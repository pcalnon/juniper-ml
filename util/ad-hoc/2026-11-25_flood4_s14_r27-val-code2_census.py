"""
Connect census and fence for juniper-canopy's unit lane, in the pytest process AND every child Python process.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14, replacement code lens r27-val-code2 (validation of carrier r27, canopy :8100 unit-lane connects).
    Written independently of the stopped lens's fence (util/ad-hoc/2026-11-25_flood4_s14_r27-val-code_fence.py), whose
    _wrap_fake probed every sys.modules entry and crashed on torch.ops on main.

How it is loaded (the runner util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py arranges both, as two
symlinks to this one file):
    * a generated ``sitecustomize.py`` on PYTHONPATH imports it as ``r27v2_census`` (the fence; no pytest import) in
      EVERY Python process that inherits the environment, so a child interpreter a test spawns is fenced and counted
      too (not one started with -I or -S, which skip sitecustomize);
    * pytest loads it as ``-p r27v2_plugin``, which adds the test/phase attribution, the guard-report log and the
      carrier fake's answer log, sharing the fence's state.

Environment:
    R27V2_OUT     output prefix (required, else the module does nothing): <prefix>.connects.jsonl (all processes,
                  O_APPEND lines), <prefix>.fake.jsonl, <prefix>.guard.jsonl, <prefix>.summary.json (pytest process)
    R27V2_LISTEN  comma-separated ports that were LISTENING when the run started (computed once by the runner)
    R27V2_ALLOW   optional comma-separated ports never refused (a probe's own server)
    R27V2_TREE    the canopy tree under test (to find its src/tests/conftest.py)

The fence: a sys.addaudithook on "socket.connect" (raised by CPython's C-level connect/connect_ex, asyncio's
non-blocking connects included, and below any monkeypatch of socket.socket.connect). It REFUSES, with
ConnectionRefusedError(ECONNREFUSED) -- what an empty CI runner gives -- every connect to a Juniper service port
(8050-8059, 8100, 8200-8211) on any address, and every connect to a local address on a port listening at the start,
so no run can drive a live local service. It records every AF_INET/AF_INET6 connect. Header values are never recorded.
"""

from __future__ import annotations

import errno
import ipaddress
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

OUT = os.environ.get("R27V2_OUT")
JUNIPER_PORTS = frozenset({*range(8050, 8060), 8100, *range(8200, 8212)})
LISTEN = frozenset(int(p) for p in os.environ.get("R27V2_LISTEN", "").split(",") if p.strip())
ALLOW = frozenset(int(p) for p in os.environ.get("R27V2_ALLOW", "").split(",") if p.strip())
TREE = Path(os.environ.get("R27V2_TREE", os.getcwd())).resolve()
STATE = {"nodeid": None, "phase": "outside", "started": time.time(), "is_pytest": False, "fake_module": None}
COUNTS = {"connects": 0, "connects_8100": 0, "refused_juniper": 0, "refused_listening": 0, "fake_answers": 0, "guard_reports": 0}
_LOCK = threading.Lock()
_FD: dict[str, int] = {}


def _append(kind: str, record: dict) -> None:
    if not OUT:
        return
    line = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
    with _LOCK:
        fd = _FD.get(kind)
        if fd is None:
            fd = os.open(f"{OUT}.{kind}.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            _FD[kind] = fd
        os.write(fd, line)


def _is_local(host: str) -> bool:
    if host in ("localhost", ""):
        return True
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return host.endswith(".localhost")
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_unspecified or ip.is_private or ip.is_link_local


def _canopy_frames() -> list[str]:
    """Up to 8 innermost frames of the calling thread that are canopy application code (src/, not src/tests/)."""
    frames = []
    src, tests = str(TREE / "src"), str(TREE / "src" / "tests")
    frame = sys._getframe(2)
    while frame is not None and len(frames) < 8:
        name = frame.f_code.co_filename
        if name.startswith(src) and not name.startswith(tests):
            frames.append(f"{os.path.relpath(name, src)}:{frame.f_lineno}:{frame.f_code.co_name}")
        frame = frame.f_back
    return frames


def _audit(event, args):
    if event != "socket.connect":
        return
    sock, address = args[0], args[1]
    family = getattr(sock, "family", None)
    if family not in (socket.AF_INET, socket.AF_INET6) or not isinstance(address, tuple) or len(address) < 2:
        return
    host, port = str(address[0]), address[1]
    refuse = None
    if port in JUNIPER_PORTS:
        refuse = "juniper"
    elif port in LISTEN and port not in ALLOW and _is_local(host):
        refuse = "listening"
    thread = threading.current_thread()
    record = {
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "process": "pytest" if STATE["is_pytest"] else "child " + " ".join(sys.argv[:3])[:160],
        "nodeid": STATE["nodeid"],
        "phase": STATE["phase"],
        "thread": thread.name,
        "main_thread": thread is threading.main_thread(),
        "family": "AF_INET6" if family == socket.AF_INET6 else "AF_INET",
        "host": host,
        "port": port,
        "refused": refuse,
    }
    if port in JUNIPER_PORTS:
        try:
            record["canopy_frames"] = _canopy_frames()
        except Exception as exc:  # noqa: BLE001 - attribution is best effort and must never change the connect
            record["canopy_frames_error"] = repr(exc)
    with _LOCK:
        COUNTS["connects"] += 1
        if port == 8100:
            COUNTS["connects_8100"] += 1
        if refuse:
            COUNTS[f"refused_{refuse}"] += 1
    _append("connects", record)
    if refuse:
        raise ConnectionRefusedError(errno.ECONNREFUSED, "Connection refused")


if OUT and __name__ == "r27v2_census" and not getattr(sys, "_r27v2_census_installed", False):
    sys._r27v2_census_installed = True
    sys.addaudithook(_audit)


# ---------------------------------------------------------------------------------------------------------------------
# pytest plugin half (only active when pytest loads this module with -p r27v2_census)
# ---------------------------------------------------------------------------------------------------------------------


def _find_fake_class():
    """The carrier's JuniperDataFake class in THIS tree's src/tests/conftest.py, or None (main has none)."""
    target = (TREE / "src" / "tests" / "conftest.py").resolve()
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        try:
            if Path(path).resolve() != target:
                continue
        except (OSError, ValueError):
            continue
        cls = module.__dict__.get("JuniperDataFake")
        return (cls, path) if isinstance(cls, type) else (None, path)
    return None, None


def _wrap_fake() -> None:
    cls, path = _find_fake_class()
    STATE["fake_module"] = {"conftest": path, "has_fake": cls is not None}
    if cls is None or cls.__dict__.get("_r27v2_wrapped"):
        return
    original = cls.respond

    def respond(self, request, _original=original):
        timeout = request.extensions.get("timeout")
        _append(
            "fake",
            {
                "nodeid": STATE["nodeid"],
                "phase": STATE["phase"],
                "thread": threading.current_thread().name,
                "method": request.method,
                "url": str(request.url),
                "port": request.url.port,
                "answer": "refuse" if self.response is None else f"answer {self.response[0]}",
                "timeout": timeout,
                "header_names": sorted(k.lower() for k in request.headers.keys()),
            },
        )
        with _LOCK:
            COUNTS["fake_answers"] += 1
        return _original(self, request)

    cls.respond = respond
    cls._r27v2_wrapped = True


if __name__ == "r27v2_plugin":
    # The pytest half. Loaded ONLY by pytest's -p r27v2_plugin (a second name for this file), so a child process,
    # which loads the fence as r27v2_census through sitecustomize, never imports pytest. It shares the fence's one
    # state: the module globals below are rebound to the r27v2_census instance's objects.
    import pytest
    import r27v2_census as _fence

    STATE, COUNTS, _LOCK, _append = _fence.STATE, _fence.COUNTS, _fence._LOCK, _fence._append

    def pytest_configure(config):
        STATE["is_pytest"] = True

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_protocol(item, nextitem):
        if STATE["fake_module"] is None:
            _wrap_fake()
        STATE["nodeid"] = item.nodeid
        try:
            return (yield)
        finally:
            STATE["nodeid"] = None
            STATE["phase"] = "between"

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_setup(item):
        STATE["phase"] = "setup"
        try:
            return (yield)
        finally:
            STATE["phase"] = "after-setup"

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(item):
        STATE["phase"] = "call"
        try:
            return (yield)
        finally:
            STATE["phase"] = "after-call"

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_teardown(item, nextitem):
        STATE["phase"] = "teardown"
        try:
            return (yield)
        finally:
            STATE["phase"] = "after-teardown"

    def pytest_runtest_logreport(report):
        for title, text in getattr(report, "sections", []):
            if title == "unit-lane network guard":
                with _LOCK:
                    COUNTS["guard_reports"] += 1
                _append("guard", {"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "message": text[:400]})

    def pytest_sessionfinish(session, exitstatus):
        if not OUT or not STATE["is_pytest"]:
            return
        modules = {}
        for name in ("main", "health", "settings", "httpx", "httpcore", "anyio", "pytest", "torch"):
            module = sys.modules.get(name)
            modules[name] = getattr(module, "__file__", None)
            version = getattr(module, "__version__", None)
            if isinstance(version, str):
                modules[f"{name}_version"] = version
        summary = {
            "python": sys.version,
            "executable": sys.executable,
            "base_prefix": sys.base_prefix,
            "cwd": os.getcwd(),
            "tree": str(TREE),
            "exitstatus": int(exitstatus),
            "counts_pytest_process": COUNTS,
            "listen_ports_at_start": sorted(LISTEN),
            "allow_ports": sorted(ALLOW),
            "fake_module": STATE["fake_module"],
            "modules": modules,
            "seconds": round(time.time() - STATE["started"], 1),
        }
        with open(f"{OUT}.summary.json", "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=1, sort_keys=True)
