"""
In-process pytest behind a connect fence that records, per test, every connect a juniper-canopy run makes (port 8100 census).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects; adapted from util/ad-hoc/2026-11-11_flood4r2_r17-canopy-guard-r2_fenced_pytest.py
    (the census juniper-canopy#815's builder ran)

Usage (cwd = a juniper-canopy tree; run under the interpreter to test with):
    python <this file> <out prefix> <pytest args...>

One sys.addaudithook on "socket.connect", which CPython raises for every C-level connect and connect_ex (asyncio's
non-blocking connects included), sees each AF_INET/AF_INET6 connect that reaches the real socket layer and appends it
to <out prefix>.census.jsonl: the running test, its phase (setup, call, teardown, or between/outside), the thread, the
destination, and the code that opened it:
  * src_frames: canopy source frames (src/ but not src/tests/) on the connecting thread's stack, innermost first;
  * test_frames: src/tests/ frames on that stack, innermost first;
  * request / request_frames: anyio's connect_tcp dials each address in a CHILD task, so the stack of an httpx
    connect holds no canopy frame. The runner therefore wraps httpx.AsyncHTTPTransport.handle_async_request with a
    pass-through that puts the request ("METHOD URL") and the canopy frames on the stack at request time (innermost
    first; the awaiting coroutines and async generators are on that stack) into a ContextVar, which the child task
    inherits; the hook reads it back. The wrapper calls the real method and changes nothing else; it is installed
    before pytest starts, so a conftest patch of the same method wraps it.
The connect is REFUSED (ConnectionRefusedError, ECONNREFUSED), as CI's empty runner refuses it, when its port is a
Juniper service port (8050-8059, 8100, 8200-8211) or had a listener on this host when the runner started, so no run
reaches a live service. A test's own server bound later on an ephemeral port is allowed. A connect the conftest guard
refuses in Python never reaches the socket layer and so is not recorded here; instead every test report that carries
the guard's section ("unit-lane network guard") is appended to <out prefix>.guard.jsonl.

sys.path[0] (this script's directory) is replaced by the working directory, as `python -m pytest` has it.
"""

from __future__ import annotations

import contextvars
import errno
import json
import os
import socket
import sys
import threading
from pathlib import Path

SERVICE_PORTS = frozenset({*range(8050, 8060), 8100, *range(8200, 8212)})
_REQUEST = contextvars.ContextVar("r27_census_request", default=None)


def _host_listening_ports() -> set[int]:
    ports: set[int] = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(table).read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            cols = row.split()
            if len(cols) > 3 and cols[3] == "0A":
                ports.add(int(cols[1].rsplit(":", 1)[1], 16))
    return ports


class Fence:
    """The audit hook's state: what to refuse, where to write, and which test is running."""

    def __init__(self, out_prefix: Path, cwd: Path) -> None:
        self.listening_at_start = frozenset(_host_listening_ports())
        self.refuse_ports = frozenset(SERVICE_PORTS | self.listening_at_start)
        self.census = out_prefix.with_name(out_prefix.name + ".census.jsonl")
        self.guard_log = out_prefix.with_name(out_prefix.name + ".guard.jsonl")
        self.src_root = (cwd / "src").resolve()
        self.tests_root = self.src_root / "tests"
        self.nodeid: str | None = None
        self.phase = "outside"
        self.lock = threading.Lock()
        self.busy = threading.local()

    def _append(self, path: Path, record: dict) -> None:
        with self.lock, path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def _where(self, frame) -> tuple[str, bool] | None:
        """``(relative path:line:function, is a src/tests/ frame)``, or None outside src/. The path is normalized:
        a module imported through a ``tests/regression/../../`` sys.path entry carries that spelling in co_filename."""
        name = os.path.normpath(frame.f_code.co_filename)
        if not name.startswith(str(self.src_root) + os.sep):
            return None
        return f"{Path(name).relative_to(self.src_root)}:{frame.f_lineno}:{frame.f_code.co_name}", name.startswith(str(self.tests_root) + os.sep)

    def stack(self, frame) -> tuple[list[str], list[str]]:
        """Canopy source frames and src/tests/ frames from ``frame`` outward, innermost first."""
        src, tests = [], []
        while frame is not None:
            found = self._where(frame)
            if found is not None:
                (tests if found[1] else src).append(found[0])
            frame = frame.f_back
        return src, tests

    def trace_httpx(self) -> None:
        """Wrap httpx's async transport so a connect made in anyio's child task can be traced to its request."""
        import httpx

        real = httpx.AsyncHTTPTransport.handle_async_request
        fence = self

        async def traced(transport, request):
            src, tests = fence.stack(sys._getframe(1))
            token = _REQUEST.set({"request": f"{request.method} {request.url}", "src_frames": src[:8], "test_frames": tests[:4]})
            try:
                return await real(transport, request)
            finally:
                _REQUEST.reset(token)

        httpx.AsyncHTTPTransport.handle_async_request = traced

    def on_connect(self, sock, address) -> None:
        try:
            family = sock.family
        except Exception:  # noqa: BLE001 - an exotic socket; record nothing
            return
        if family not in (socket.AF_INET, socket.AF_INET6) or not (isinstance(address, tuple) and len(address) >= 2):
            return
        port = address[1]
        refused = port in self.refuse_ports
        src_frames, test_frames = self.stack(sys._getframe(3))
        traced = _REQUEST.get()
        self._append(
            self.census,
            {
                "nodeid": self.nodeid,
                "phase": self.phase,
                "thread": threading.current_thread().name,
                "host": str(address[0]),
                "port": port,
                "refused": refused,
                "service_port": port in SERVICE_PORTS,
                "src_frames": src_frames[:8],
                "test_frames": test_frames[:4],
                "request": traced["request"] if traced else None,
                "request_src_frames": traced["src_frames"] if traced else [],
                "request_test_frames": traced["test_frames"] if traced else [],
            },
        )
        if refused:
            raise ConnectionRefusedError(errno.ECONNREFUSED, "refused by the r27 census fence (a Juniper service port or a live listener)")

    def audit(self, event: str, args: tuple) -> None:
        if event != "socket.connect" or getattr(self.busy, "on", False):
            return
        self.busy.on = True
        try:
            self.on_connect(*args)
        finally:
            self.busy.on = False


def main() -> int:
    out_prefix = Path(sys.argv[1]).resolve()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    sys.path[0] = str(cwd)
    import pytest  # after sys.path[0] is the tree, as under `python -m pytest`

    fence = Fence(out_prefix, cwd)
    fence.census.write_text("", encoding="utf-8")
    fence.guard_log.write_text("", encoding="utf-8")
    out_prefix.with_name(out_prefix.name + ".listening_at_start.json").write_text(json.dumps(sorted(fence.listening_at_start)) + "\n", encoding="utf-8")

    class PhasePlugin:
        """Tells the fence which test and phase is running, and logs every report the conftest guard failed."""

        def _phase(self, item, phase: str):
            fence.nodeid, fence.phase = item.nodeid, phase
            try:
                return (yield)
            finally:
                fence.phase = "between"

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_runtest_setup(self, item):
            return (yield from self._phase(item, "setup"))

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_runtest_call(self, item):
            return (yield from self._phase(item, "call"))

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_runtest_teardown(self, item):
            return (yield from self._phase(item, "teardown"))

        def pytest_runtest_logreport(self, report):
            sections = [text for title, text in getattr(report, "sections", []) if title == "unit-lane network guard"]
            if sections:
                fence._append(fence.guard_log, {"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "message": sections[0][:400]})

    fence.trace_httpx()
    sys.addaudithook(fence.audit)
    return int(pytest.main(sys.argv[2:], plugins=[PhasePlugin()]))


if __name__ == "__main__":
    sys.exit(main())
