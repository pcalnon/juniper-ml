"""
In-process pytest runner with a socket.connect audit-hook census that refuses every connect to a live host port.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage (cwd = a juniper-canopy worktree; run under the JuniperCanopy1 interpreter):
    python <this file> <out.jsonl> <pytest args...>

A sys.addaudithook on "socket.connect" (raised by CPython's C-level connect AND connect_ex, so asyncio's
non-blocking connects are seen too) records every AF_INET/AF_INET6 connect with the running test's node id,
its phase, the thread, and the innermost src/ and src/tests/ frames. A connect is REFUSED (ConnectionRefusedError,
ECONNREFUSED) when its port is a Juniper service port (8050-8059, 8100, 8200-8202, 8210-8211) or any port that had
a listener on this host when the runner started, so no probe sends a byte to a live service; a test's own server on
an ephemeral port bound later is allowed. Under a guard that refuses in Python first, a guarded port recorded here
is a connect that ESCAPED the guard. Paths that never call CPython's connect (uvloop/libuv, C extensions, child
processes) are invisible to this census, as they are to the guard.
"""

from __future__ import annotations

import errno
import json
import socket
import sys
import threading
from pathlib import Path

import pytest

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


REFUSE_PORTS = frozenset(SERVICE_PORTS | _host_listening_ports())
STATE = {"nodeid": None, "phase": "outside"}
OUT: list[Path] = []
SRC_ROOT = (Path.cwd() / "src").resolve()
TESTS_ROOT = SRC_ROOT / "tests"


def _frames() -> tuple[str | None, str | None]:
    frame = sys._getframe(2)
    src_frame = test_frame = None
    while frame is not None and (src_frame is None or test_frame is None):
        name = frame.f_code.co_filename
        if test_frame is None and name.startswith(str(TESTS_ROOT)):
            test_frame = f"{Path(name).relative_to(SRC_ROOT)}:{frame.f_lineno}"
        elif src_frame is None and name.startswith(str(SRC_ROOT)) and not name.startswith(str(TESTS_ROOT)):
            src_frame = f"{Path(name).relative_to(SRC_ROOT)}:{frame.f_lineno}"
        frame = frame.f_back
    return src_frame, test_frame


def _audit(event: str, args: tuple) -> None:
    if event != "socket.connect":
        return
    sock, address = args
    try:
        family = sock.family
    except Exception:  # noqa: BLE001 - an exotic socket; record nothing
        return
    if family not in (socket.AF_INET, socket.AF_INET6) or not (isinstance(address, tuple) and len(address) >= 2):
        return
    port = address[1]
    refused = port in REFUSE_PORTS
    src_frame, test_frame = _frames()
    record = {
        "nodeid": STATE["nodeid"],
        "phase": STATE["phase"],
        "thread": threading.current_thread().name,
        "host": str(address[0]),
        "port": port,
        "refused": refused,
        "service_port": port in SERVICE_PORTS,
        "src_frame": src_frame,
        "test_frame": test_frame,
    }
    if OUT:
        with OUT[0].open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    if refused:
        raise ConnectionRefusedError(errno.ECONNREFUSED, "refused by the validator census (a live or service port)")


class CensusPlugin:
    """Tracks the running test and phase for the audit hook."""

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        STATE.update(nodeid=item.nodeid, phase="setup")
        yield
        STATE.update(phase="between")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        STATE.update(nodeid=item.nodeid, phase="call")
        yield
        STATE.update(phase="between")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item):
        STATE.update(nodeid=item.nodeid, phase="teardown")
        yield
        STATE.update(phase="between")


def main() -> int:
    OUT.append(Path(sys.argv[1]).resolve())
    OUT[0].parent.mkdir(parents=True, exist_ok=True)
    OUT[0].write_text("", encoding="utf-8")
    sys.addaudithook(_audit)
    return int(pytest.main(sys.argv[2:], plugins=[CensusPlugin()]))


if __name__ == "__main__":
    sys.exit(main())
