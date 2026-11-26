"""
Run a juniper-canopy pytest lane behind a C-level socket.connect audit hook that records, and fences, every connect.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r27 (juniper-canopy unit-lane :8100 connects). Written independently of
    the builder's census tooling, to re-measure its numbers.

Usage (run with the interpreter of the venv under test):
    python -I <this file> --tree <canopy checkout> --out <output dir> [--timeout S] -- <pytest arguments>

The launcher builds a clean environment for the child: every JUNIPER_*, CASCOR_* and CANOPY_* variable dropped (one
whose name contains SENTRY is kept, set empty), LD_LIBRARY_PATH dropped, LIBTORCH set empty, and the CI unit step's
three variables set (CASCOR_BACKEND_AVAILABLE=0, RUN_SERVER_TESTS=0, ENABLE_SLOW_TESTS=0). The child, in the tree,
installs sys.addaudithook for "socket.connect" (raised by the C implementation of socket.connect and connect_ex, so it
sees what a Python-level patch lets through) and runs pytest.main in-process.

The fence: an AF_INET/AF_INET6 connect to 8050-8059, 8100 or 8200-8211, or to any TCP port listening when the run
starts (read from /proc/net/tcp and tcp6), is refused with ECONNREFUSED before it leaves the process, as an empty CI
runner refuses it. No test can reach a live local service.

Attribution: httpx.AsyncHTTPTransport.handle_async_request is wrapped (pass-through) to put the request and the app
frames that sent it into a ContextVar, which anyio's connect tasks inherit; the hook records it with the test node id,
the phase (setup / call / teardown) and the thread. Outputs in --out: connects.jsonl, reports.jsonl (one line per
test report: node id, phase, outcome, whether the conftest network guard flagged it), listening_at_start.json,
pytest_exit.json.
"""

from __future__ import annotations

import argparse
import contextvars
import errno
import json
import os
import socket
import subprocess  # nosec B404 - runs this same file as the child, with a list argv
import sys
import threading
import traceback
from pathlib import Path

JUNIPER_PORTS = frozenset({*range(8050, 8060), 8100, *range(8200, 8212)})
CI_STEP_VARIABLES = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"}
DROPPED_PREFIXES = ("JUNIPER_", "CASCOR_", "CANOPY_")


def _listening_ports() -> list[int]:
    ports: set[int] = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            lines = Path(table).read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 3 and fields[3] == "0A":  # TCP_LISTEN
                ports.add(int(fields[1].rsplit(":", 1)[1], 16))
    return sorted(ports)


def _clean_environment() -> dict[str, str]:
    env = {}
    for key, value in os.environ.items():
        if key == "LD_LIBRARY_PATH":
            continue
        if key.startswith(DROPPED_PREFIXES):
            if "SENTRY" in key:
                env[key] = ""
            continue
        env[key] = value
    env["LIBTORCH"] = ""
    env.update(CI_STEP_VARIABLES)
    return env


def launch(args: argparse.Namespace, pytest_args: list[str]) -> int:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, "-I", str(Path(__file__).resolve()), "--child", "--tree", str(Path(args.tree).resolve()), "--out", str(out), "--", *pytest_args]
    try:
        completed = subprocess.run(argv, cwd=str(Path(args.tree).resolve()), env=_clean_environment(), timeout=args.timeout, check=False)  # nosec B603 - fixed argv, this interpreter
        code = completed.returncode
    except subprocess.TimeoutExpired:
        code = -999
    (out / "launcher_exit.json").write_text(json.dumps({"child_exit": code}) + "\n", encoding="utf-8")
    return 0 if code in (0, 1) else 2


def child(args: argparse.Namespace, pytest_args: list[str]) -> int:
    tree = Path(args.tree).resolve()
    out = Path(args.out).resolve()
    src = tree / "src"
    tests = src / "tests"
    listening = frozenset(_listening_ports())
    (out / "listening_at_start.json").write_text(json.dumps(sorted(listening)) + "\n", encoding="utf-8")

    state = {"nodeid": None, "phase": None}
    connects: list[dict] = []
    reports: list[dict] = []
    request_context: contextvars.ContextVar = contextvars.ContextVar("r27_val_claims_request", default=None)

    def _frames(stack) -> tuple[list[str], list[str]]:
        app, test = [], []
        for frame in stack:
            path = Path(frame.filename)
            try:
                relative = path.resolve().relative_to(src)
            except (ValueError, OSError):
                continue
            label = f"{relative.as_posix()}:{frame.lineno} {frame.name}"
            (test if path.resolve().is_relative_to(tests) else app).append(label)
        return app, test

    def _hook(event: str, hook_args) -> None:
        if event != "socket.connect":
            return
        sock, address = hook_args
        family = getattr(sock, "family", None)
        if family not in (socket.AF_INET, socket.AF_INET6) or not (isinstance(address, tuple) and len(address) >= 2):
            return
        port = address[1]
        refused = port in JUNIPER_PORTS or port in listening
        app, test = _frames(traceback.extract_stack()[:-1])
        thread = threading.current_thread()
        connects.append(
            {
                "nodeid": state["nodeid"],
                "phase": state["phase"],
                "host": address[0],
                "port": port,
                "refused_by_fence": refused,
                "thread": None if thread is threading.main_thread() else thread.name,
                "request": request_context.get(),
                "app_frames": app[-6:],
                "test_frames": test[-3:],
            }
        )
        if refused:
            raise ConnectionRefusedError(errno.ECONNREFUSED, "refused by the r27-val-claims census fence")

    sys.path.insert(0, str(tree))  # as `python -m pytest` run from the tree puts the working directory first
    import httpx
    import pytest

    real_handle = httpx.AsyncHTTPTransport.handle_async_request

    async def _traced(transport, request):
        app, test = _frames(traceback.extract_stack()[:-1])
        token = request_context.set({"request": f"{request.method} {request.url}", "app_frames": app[-6:], "test_frames": test[-3:]})
        try:
            return await real_handle(transport, request)
        finally:
            request_context.reset(token)

    httpx.AsyncHTTPTransport.handle_async_request = _traced
    sys.addaudithook(_hook)

    class CensusPlugin:
        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_logstart(self, nodeid, location):
            state["nodeid"] = nodeid

        @pytest.hookimpl(trylast=True)
        def pytest_runtest_logfinish(self, nodeid, location):
            state["nodeid"] = None

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_setup(self, item):
            state["phase"] = "setup"
            try:
                return (yield)
            finally:
                state["phase"] = None

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_call(self, item):
            state["phase"] = "call"
            try:
                return (yield)
            finally:
                state["phase"] = None

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_teardown(self, item, nextitem):
            state["phase"] = "teardown"
            try:
                return (yield)
            finally:
                state["phase"] = None

        def pytest_runtest_logreport(self, report):
            guard = [text for name, text in report.sections if name == "unit-lane network guard"]
            reports.append(
                {
                    "nodeid": report.nodeid,
                    "when": report.when,
                    "outcome": report.outcome,
                    "wasxfail": hasattr(report, "wasxfail"),
                    "duration": round(report.duration, 3),
                    "guard": guard[0][:300] if guard else None,
                    "longrepr": None if report.passed else str(report.longrepr)[-600:],
                }
            )

    try:
        code = pytest.main(pytest_args, plugins=[CensusPlugin()])
    finally:
        with (out / "connects.jsonl").open("w", encoding="utf-8") as handle:
            for record in connects:
                handle.write(json.dumps(record) + "\n")
        with (out / "reports.jsonl").open("w", encoding="utf-8") as handle:
            for record in reports:
                handle.write(json.dumps(record) + "\n")
    (out / "pytest_exit.json").write_text(json.dumps({"pytest_exit": int(code)}) + "\n", encoding="utf-8")
    return int(code)


def main() -> int:
    argv = sys.argv[1:]
    pytest_args: list[str] = []
    if "--" in argv:
        split = argv.index("--")
        argv, pytest_args = argv[:split], argv[split + 1 :]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=5400)
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args(argv)
    return child(args, pytest_args) if args.child else launch(args, pytest_args)


if __name__ == "__main__":
    sys.exit(main())
