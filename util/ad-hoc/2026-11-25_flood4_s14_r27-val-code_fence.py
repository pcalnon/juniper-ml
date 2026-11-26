"""
pytest plugin (load with -p): a connect fence and census for juniper-canopy's unit lane, plus a log of every request the carrier's juniper-data fake answers.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r27-val-code (independent validation of carrier r27, juniper-canopy :8100 unit-lane connects)

Environment (read at import):
    R27V_OUT          output prefix (required): writes <prefix>.connects.jsonl, <prefix>.fake.jsonl, <prefix>.guard.jsonl,
                      <prefix>.summary.json
    R27V_ALLOW_PORTS  optional comma-separated ports the fence lets through even if listening at start (a probe's own server)

What it does:
    * sys.addaudithook on "socket.connect" (CPython raises it for every C-level connect/connect_ex, asyncio's non-blocking
      connects included). Every AF_INET/AF_INET6 connect that reaches the real socket layer is recorded with the running
      test, its phase, the thread, the destination and -- for a connect made on an event-loop thread -- the canopy source
      frames (src/, not src/tests/) of every asyncio task whose await chain runs through src/health.py (the probe).
    * It REFUSES (ConnectionRefusedError, ECONNREFUSED -- what CI's empty runner gives) a connect to a Juniper service port
      (8050-8059, 8100, 8200-8211) on any address, and a connect to a LOCAL address on a port that was listening when the
      plugin was imported, so no run can drive a live local service.
    * It wraps the carrier's JuniperDataFake.respond (when the conftest defines it) with a pass-through that logs each
      request the fake answers (test, phase, method, URL, host, port, the answer kind). Behaviour is unchanged.
    * It logs every report that carries the canopy guard's "unit-lane network guard" section.
"""

from __future__ import annotations

import asyncio
import errno
import ipaddress
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

OUT = os.environ.get("R27V_OUT")
if not OUT:
    raise RuntimeError("R27V_OUT must name an output prefix")
ALLOW = {int(p) for p in os.environ.get("R27V_ALLOW_PORTS", "").split(",") if p.strip()}
JUNIPER_PORTS = frozenset({*range(8050, 8060), 8100, *range(8200, 8212)})
SRC = (Path.cwd() / "src").resolve()
TESTS = SRC / "tests"


def _listening() -> tuple[set[int], set[str]]:
    """Ports in LISTEN state at import, and the local addresses they listen on (from /proc/net/tcp and tcp6)."""
    ports: set[int] = set()
    addresses: set[str] = set()
    for name, width in (("/proc/net/tcp", 8), ("/proc/net/tcp6", 32)):
        try:
            with open(name, encoding="ascii") as handle:
                lines = handle.readlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) < 4 or fields[3] != "0A":
                continue
            local_hex, port_hex = fields[1].split(":")
            ports.add(int(port_hex, 16))
            raw = bytes.fromhex(local_hex)
            if width == 8:
                addresses.add(str(ipaddress.IPv4Address(raw[::-1])))
            else:
                words = b"".join(raw[i : i + 4][::-1] for i in range(0, 16, 4))
                addresses.add(str(ipaddress.IPv6Address(words)))
    return ports, addresses


LISTEN_PORTS, LISTEN_ADDRESSES = _listening()
STATE = {"nodeid": None, "phase": "outside", "started": time.time()}
_LOCK = threading.Lock()
_KINDS = ("connects", "fake", "guard")
for _kind in _KINDS:
    with open(f"{OUT}.{_kind}.jsonl", "w", encoding="utf-8"):
        pass  # truncate: each record is appended below
COUNTS = {"connects": 0, "refused_juniper": 0, "refused_listening": 0, "fake_answers": 0, "guard_reports": 0}


def _write(kind: str, record: dict) -> None:
    with _LOCK:
        with open(f"{OUT}.{kind}.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _is_local(host: str) -> bool:
    if host in ("localhost", ""):
        return True
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError:
            return False
        return any(_is_local(info[4][0]) for info in infos)
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_unspecified or str(ip) in LISTEN_ADDRESSES


def _chain(coro) -> list[tuple[str, int, str]]:
    frames = []
    for _ in range(300):
        if coro is None:
            break
        frame = getattr(coro, "cr_frame", None) or getattr(coro, "gi_frame", None) or getattr(coro, "ag_frame", None)
        if frame is not None:
            frames.append((frame.f_code.co_filename, frame.f_lineno, frame.f_code.co_name))
        nxt = getattr(coro, "cr_await", None)
        if nxt is None:
            nxt = getattr(coro, "gi_yieldfrom", None)
        if nxt is None:
            nxt = getattr(coro, "ag_await", None)
        coro = nxt
    return frames


def _probe_sites() -> list[list[str]]:
    """For a connect on an event-loop thread: the canopy (non-test) frames of each task whose chain includes src/health.py."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return []
    sites = []
    for task in list(asyncio.all_tasks(loop)):
        frames = _chain(task.get_coro())
        canopy = [f"{Path(fn).relative_to(SRC)}:{line}:{name}" for fn, line, name in frames if fn.startswith(str(SRC)) and not fn.startswith(str(TESTS))]
        if any(site.startswith("health.py:") for site in canopy):
            sites.append(canopy)
    return sites


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
    elif port in LISTEN_PORTS and port not in ALLOW and _is_local(host):
        refuse = "listening"
    thread = threading.current_thread()
    record = {
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
            record["probe_sites"] = _probe_sites()
        except Exception as exc:  # noqa: BLE001 - attribution is best-effort and must never change the connect
            record["probe_sites_error"] = repr(exc)
    COUNTS["connects"] += 1
    if refuse:
        COUNTS[f"refused_{refuse}"] += 1
    _write("connects", record)
    if refuse:
        raise ConnectionRefusedError(errno.ECONNREFUSED, "Connection refused")


sys.addaudithook(_audit)


def _wrap_fake() -> str:
    """Wrap the conftest's JuniperDataFake.respond with a logging pass-through, if the conftest defines one."""
    for module in list(sys.modules.values()):
        cls = getattr(module, "JuniperDataFake", None)
        if cls is None or getattr(cls, "_r27v_wrapped", False):
            continue
        original = cls.respond

        def respond(self, request, _original=original):
            kind = "refuse" if self.response is None else f"answer {self.response[0]}"
            _write(
                "fake",
                {
                    "nodeid": STATE["nodeid"],
                    "phase": STATE["phase"],
                    "thread": threading.current_thread().name,
                    "method": request.method,
                    "url": str(request.url),
                    "host": request.url.host,
                    "port": request.url.port,
                    "answer": kind,
                    "timeout": request.extensions.get("timeout"),
                },
            )
            COUNTS["fake_answers"] += 1
            return _original(self, request)

        cls.respond = respond
        cls._r27v_wrapped = True
        return getattr(module, "__file__", "?")
    return ""


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    if "fake_module" not in STATE:
        STATE["fake_module"] = _wrap_fake()
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
            COUNTS["guard_reports"] += 1
            _write("guard", {"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "message": text[:400]})


def pytest_sessionfinish(session, exitstatus):
    modules = {}
    for name in ("main", "health", "settings", "httpx", "anyio", "httpcore", "pytest"):
        module = sys.modules.get(name)
        modules[name] = getattr(module, "__file__", None)
        if hasattr(module, "__version__"):
            modules[f"{name}_version"] = module.__version__
    summary = {
        "python": sys.version,
        "executable": sys.executable,
        "base_prefix": sys.base_prefix,
        "cwd": str(Path.cwd()),
        "exitstatus": int(exitstatus),
        "counts": COUNTS,
        "listen_ports_at_start": sorted(LISTEN_PORTS),
        "allow_ports": sorted(ALLOW),
        "fake_module": STATE.get("fake_module"),
        "modules": modules,
        "seconds": round(time.time() - STATE["started"], 1),
    }
    with open(f"{OUT}.summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1, sort_keys=True)
