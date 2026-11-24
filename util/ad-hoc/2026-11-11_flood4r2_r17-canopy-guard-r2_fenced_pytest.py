"""
In-process pytest behind a fence: no connect reaches a live host port, and no test may delete a protected directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage (cwd = a juniper-canopy tree; run under the interpreter to test with):
    python <this file> <out prefix> <pytest args...>

Adapted from util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_census_runner.py. One sys.addaudithook does two jobs.

1. "socket.connect" (raised by CPython's C-level connect and connect_ex, so asyncio's non-blocking connects are seen
   too): every AF_INET/AF_INET6 connect is appended to <out prefix>.census.jsonl with the running test, its phase,
   the thread and the innermost src/ and src/tests/ frames. It is REFUSED (ConnectionRefusedError, ECONNREFUSED)
   when its port is a Juniper service port (8050-8059, 8100, 8200-8202, 8210-8211) or had a listener on this host
   when the runner started, which is what CI's empty runner does. A test's own server on an ephemeral port bound
   later is allowed. Under the carrier's guard, which refuses in Python first, a guarded port recorded here is a
   connect that got past the guard.
2. "shutil.rmtree": a call whose target is a strict ancestor of a directory named in R2_PROTECT_DIRS (os.pathsep
   separated) is appended to <out prefix>.rmtree.jsonl with the running test and a short stack, and refused with
   PermissionError. A validator's pytest --basetemp vanished mid-run on 2026-11-09 and nobody found what removed
   it; this names an in-process remover, and keeps it from taking the scratch directory with it.

sys.path[0] (this script's directory) is replaced by the working directory, as `python -m pytest` has it.
"""

from __future__ import annotations

import errno
import json
import os
import socket
import sys
import threading
import traceback
from pathlib import Path

SERVICE_PORTS = frozenset({*range(8050, 8060), 8100, 8200, 8201, 8202, 8210, 8211})


def _host_listening_ports() -> set[int]:
    ports: set[int] = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            cols = row.split()
            if len(cols) > 3 and cols[3] == "0A":
                ports.add(int(cols[1].rsplit(":", 1)[1], 16))
    return ports


class Fence:
    """The audit hook's state: what to refuse, what to protect, where to write, and which test is running."""

    def __init__(self, out_prefix: Path, cwd: Path, protect: list[Path]) -> None:
        self.refuse_ports = frozenset(SERVICE_PORTS | _host_listening_ports())
        self.protect = protect
        self.census = out_prefix.with_name(out_prefix.name + ".census.jsonl")
        self.rmtree_log = out_prefix.with_name(out_prefix.name + ".rmtree.jsonl")
        self.src_root = (cwd / "src").resolve()
        self.tests_root = self.src_root / "tests"
        self.nodeid: str | None = None
        self.phase = "outside"
        self.lock = threading.Lock()

    def _append(self, path: Path, record: dict) -> None:
        with self.lock, path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def _frames(self) -> tuple[str | None, str | None]:
        frame = sys._getframe(3)
        src_frame = test_frame = None
        while frame is not None and (src_frame is None or test_frame is None):
            name = frame.f_code.co_filename
            if test_frame is None and name.startswith(str(self.tests_root)):
                test_frame = f"{Path(name).relative_to(self.src_root)}:{frame.f_lineno}"
            elif src_frame is None and name.startswith(str(self.src_root)) and not name.startswith(str(self.tests_root)):
                src_frame = f"{Path(name).relative_to(self.src_root)}:{frame.f_lineno}"
            frame = frame.f_back
        return src_frame, test_frame

    def on_connect(self, sock, address) -> None:
        try:
            family = sock.family
        except Exception:  # noqa: BLE001 - an exotic socket; record nothing
            return
        if family not in (socket.AF_INET, socket.AF_INET6) or not (isinstance(address, tuple) and len(address) >= 2):
            return
        port = address[1]
        refused = port in self.refuse_ports
        src_frame, test_frame = self._frames()
        self._append(self.census, {"nodeid": self.nodeid, "phase": self.phase, "thread": threading.current_thread().name, "host": str(address[0]), "port": port, "refused": refused, "service_port": port in SERVICE_PORTS, "src_frame": src_frame, "test_frame": test_frame})
        if refused:
            raise ConnectionRefusedError(errno.ECONNREFUSED, "refused by the round-2 fence (a live or service port)")

    def on_rmtree(self, target) -> None:
        if not self.protect or not isinstance(target, (str, bytes, os.PathLike)):
            return
        resolved = Path(os.fsdecode(target)).resolve()
        hit = [str(path) for path in self.protect if resolved in path.parents]
        if not hit:
            return
        self._append(self.rmtree_log, {"target": str(resolved), "would_remove": hit, "nodeid": self.nodeid, "phase": self.phase, "thread": threading.current_thread().name, "stack": traceback.format_stack(limit=14)})
        raise PermissionError(errno.EPERM, f"refused by the round-2 fence: {resolved} holds a protected directory")

    def audit(self, event: str, args: tuple) -> None:
        if event == "socket.connect":
            self.on_connect(*args)
        elif event == "shutil.rmtree":
            self.on_rmtree(args[0])


def main() -> int:
    out_prefix = Path(sys.argv[1]).resolve()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    sys.path[0] = str(cwd)
    import pytest  # after sys.path[0] is the tree, as under `python -m pytest`

    fence = Fence(out_prefix, cwd, [Path(entry).resolve() for entry in os.environ.get("R2_PROTECT_DIRS", "").split(os.pathsep) if entry])
    fence.census.write_text("", encoding="utf-8")
    fence.rmtree_log.write_text("", encoding="utf-8")

    class PhasePlugin:
        """Tells the fence which test and phase is running."""

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_setup(self, item):
            fence.nodeid, fence.phase = item.nodeid, "setup"
            try:
                return (yield)
            finally:
                fence.phase = "between"

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_call(self, item):
            fence.nodeid, fence.phase = item.nodeid, "call"
            try:
                return (yield)
            finally:
                fence.phase = "between"

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_teardown(self, item):
            fence.nodeid, fence.phase = item.nodeid, "teardown"
            try:
                return (yield)
            finally:
                fence.phase = "between"

    sys.addaudithook(fence.audit)
    return int(pytest.main(sys.argv[2:], plugins=[PhasePlugin()]))


if __name__ == "__main__":
    sys.exit(main())
