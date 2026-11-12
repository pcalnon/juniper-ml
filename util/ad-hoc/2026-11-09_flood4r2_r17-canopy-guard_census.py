"""
Census of the network connects a juniper-canopy pytest run makes, recorded per test by a C-level audit hook.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"): canopy's unit lane made unmocked connects
to 127.0.0.1:8050 (a live canopy listener on this host) and to :8100 (juniper-data's port). This runs pytest
in-process in a canopy worktree with ``sys.addaudithook`` watching the ``socket.connect`` event, which CPython
raises for every ``socket.connect`` / ``connect_ex`` (asyncio's non-blocking connects included), and records each
AF_INET / AF_INET6 attempt with the test, the phase (setup / call / teardown) and thread that made it, and the
innermost worktree frames.

A connect is ALLOWED only when its destination is loopback and the listening socket belongs to this process or
one of its descendants (a test's own server, port 0 included). Every other connect -- a live service on this
host, an empty port, a non-loopback host -- is REFUSED with ECONNREFUSED, which is what CI's empty runner does,
so the census never sends a byte to a live service. ``connect_ex`` is wrapped to return the errno instead of
raising, keeping its contract. ``subprocess.Popen`` and non-numeric ``socket.getaddrinfo`` events are recorded
too, so a test whose child process connects is at least named.

``--inject`` is the lane-wide MUTANT: at the start of every test's call phase it makes a deliberate, unmocked
connect to 127.0.0.1:8050 and swallows the refusal, so a run with the guard installed must fail every guarded
test that reaches its call, and the census records the connects that got past the guard (only unguarded tests).

``--probe-guard`` proves, test by test, that the conftest guard is ARMED without changing any outcome: at the
start of each call it makes the same swallowed connect, checks the ``service_port_guard`` fixture's guard
refused and recorded exactly that address, then withdraws that one record, so the test's own outcome is still
measured. Tests whose probe the guard refused land in "armed"; a test the guard is not armed for gets no probe
and lands in "not_armed".

Usage (run with -I so neither this directory nor the user site is on sys.path):
  /opt/miniforge3/envs/JuniperCanopy1/bin/python -I <this file> --wt <canopy worktree> --out <json> [--inject | --probe-guard] -- <pytest args>

Writes <json>: {"exit", "collected", "outcomes", "failed", "connects", "by_port", "by_test", "popen",
"getaddrinfo", "import_origins", "imported_outside_wt"}. Exits with pytest's exit status.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import errno
import ipaddress
import json
import os
import socket
import sys
import threading
import traceback
from collections import Counter, defaultdict
from pathlib import Path

import pytest

# CI's unit step environment (ci.yml "Run Unit Tests with Coverage Gate"), plus the empty LIBTORCH /
# LD_LIBRARY_PATH the canopy verify note prescribes for this host (precedent: the round-2 validator's fence).
CI_ENV = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0", "LIBTORCH": "", "LD_LIBRARY_PATH": ""}
INJECT_TARGET = ("127.0.0.1", 8050)
LISTEN_STATE = "0A"
PROC_TABLES = ("/proc/self/net/tcp", "/proc/self/net/tcp6")
ORIGIN_MODULES = ("main", "settings", "demo_mode", "backend.cascor_service_adapter", "frontend.dashboard_manager")


def _socket_inodes(pid: str) -> set[str]:
    """Return the socket inodes pid holds open."""
    inodes: set[str] = set()
    fd_dir = f"/proc/{pid}/fd"
    try:
        names = os.listdir(fd_dir)
    except OSError:
        return inodes
    for name in names:
        try:
            target = os.readlink(f"{fd_dir}/{name}")
        except OSError:
            continue
        if target.startswith("socket:["):
            inodes.add(target[len("socket:[") : -1])
    return inodes


def _descendants(root: int) -> list[str]:
    """Return the pids (as strings) of root's descendant processes."""
    children: dict[int, list[int]] = defaultdict(list)
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/stat", encoding="utf-8") as fh:
                stat = fh.read()
        except OSError:
            continue
        children[int(stat.rsplit(")", 1)[1].split()[1])].append(int(name))
    found: list[str] = []
    stack = [root]
    while stack:
        for child in children.get(stack.pop(), []):
            found.append(str(child))
            stack.append(child)
    return found


def _listener_inodes(port: int) -> set[str]:
    """Return the inodes of LISTEN sockets on port (any process in this network namespace)."""
    inodes: set[str] = set()
    for table in PROC_TABLES:
        try:
            with open(table, encoding="utf-8") as fh:
                rows = fh.read().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            parts = row.split()
            if len(parts) > 9 and parts[3] == LISTEN_STATE and int(parts[1].rsplit(":", 1)[1], 16) == port:
                inodes.add(parts[9])
    return inodes


def _is_loopback(host: object) -> bool:
    if host in ("localhost", "", "0.0.0.0", "::"):  # nosec B104 - matched, never bound: an unspecified destination is this host
        return True
    try:
        return ipaddress.ip_address(str(host).split("%", 1)[0]).is_loopback
    except ValueError:
        return False


class Census:
    """A pytest plugin object plus the audit hook it drives."""

    def __init__(self, wt: Path, inject: bool = False, probe_guard: bool = False) -> None:
        self.wt = str(wt.resolve())
        self.inject = inject
        self.probe_guard = probe_guard
        self.injected = 0
        self.armed: list[str] = []
        self.not_armed: list[str] = []
        self.nodeid = "<collection>"
        self.phase = "collect"
        self.connects: list[dict] = []
        self.popen: list[dict] = []
        self.getaddrinfo: Counter = Counter()
        self.markers: dict[str, list[str]] = {}
        self.outcomes: dict[str, str] = {}
        self.collected = 0
        self._busy = threading.local()
        self._orig_connect_ex = socket.socket.connect_ex
        census = self

        def connect_ex(sock, address):
            if sock.family in (socket.AF_INET, socket.AF_INET6) and isinstance(address, tuple) and len(address) >= 2:
                verdict = census.verdict(address)
                if verdict != "allowed-own-listener":
                    census.record(address, verdict, "connect_ex")
                    return errno.ECONNREFUSED
            return census._orig_connect_ex(sock, address)

        socket.socket.connect_ex = connect_ex
        sys.addaudithook(self.audit)

    # --- policy -------------------------------------------------------------------------------------------
    def verdict(self, address: tuple) -> str:
        host, port = address[0], address[1]
        if not _is_loopback(host):
            return "refused-non-loopback"
        listeners = _listener_inodes(int(port))
        if not listeners:
            return "refused-no-listener"
        owned = _socket_inodes("self")
        for pid in _descendants(os.getpid()):
            owned |= _socket_inodes(pid)
        return "allowed-own-listener" if listeners & owned else "refused-foreign-listener"

    def record(self, address: tuple, verdict: str, call: str) -> None:
        frames = []
        for frame in traceback.extract_stack()[:-3]:
            if frame.filename.startswith(self.wt):
                frames.append(f"{os.path.relpath(frame.filename, self.wt)}:{frame.lineno}:{frame.name}")
        self.connects.append(
            {
                "test": self.nodeid,
                "phase": self.phase,
                "thread": threading.current_thread().name,
                "host": str(address[0]),
                "port": int(address[1]),
                "verdict": verdict,
                "call": call,
                "frames": frames[-8:],
            }
        )

    def audit(self, event: str, args: tuple) -> None:
        if event not in ("socket.connect", "subprocess.Popen", "socket.getaddrinfo"):
            return
        if getattr(self._busy, "on", False):
            return
        self._busy.on = True
        try:
            self._audit(event, args)
        finally:
            self._busy.on = False

    def _audit(self, event: str, args: tuple) -> None:
        if event == "subprocess.Popen":
            argv = args[1] if isinstance(args[1], (list, tuple)) else [args[1]]
            self.popen.append({"test": self.nodeid, "phase": self.phase, "argv": [str(a) for a in argv][:6]})
            return
        if event == "socket.getaddrinfo":
            host = args[0]
            if isinstance(host, bytes):
                host = host.decode("ascii", "replace")
            if host and not _is_loopback(host) and not str(host).replace(".", "").isdigit():
                self.getaddrinfo[f"{self.nodeid} -> {host}:{args[1]}"] += 1
            return
        sock, address = args
        if sock.family not in (socket.AF_INET, socket.AF_INET6) or not (isinstance(address, tuple) and len(address) >= 2):
            return
        verdict = self.verdict(address)
        self.record(address, verdict, "connect")
        if verdict != "allowed-own-listener":
            raise ConnectionRefusedError(errno.ECONNREFUSED, f"refused by the r17 census fence ({verdict})")

    # --- pytest hooks -------------------------------------------------------------------------------------
    def pytest_collection_modifyitems(self, items):
        self.collected = len(items)
        for item in items:
            self.markers[item.nodeid] = sorted({m.name for m in item.iter_markers()})

    def _phase(self, item, phase: str):
        self.nodeid, self.phase = item.nodeid, phase
        try:
            return (yield)
        finally:
            self.phase = "between"

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_setup(self, item):
        return (yield from self._phase(item, "setup"))

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_call(self, item):
        if self.inject or self.probe_guard:
            self.nodeid, self.phase = item.nodeid, "call"
        if self.inject:
            self._inject_connect()
        elif self.probe_guard:
            self._probe_guard(item)
        return (yield from self._phase(item, "call"))

    def _probe_guard(self, item) -> None:
        """Make the mutant's connect, confirm the guard refused and recorded it, and withdraw that record."""
        guard = item.funcargs.get("service_port_guard")
        if guard is None or guard.armed_for != item.nodeid:
            # Not armed: no probe, so a test that swaps the guard's pass-through for a recorder
            # (test_unit_lane_network_guard.py's no_real_connect) does not record the probe too.
            self.not_armed.append(item.nodeid)
            return
        before = len(guard.refused)
        self._inject_connect()
        added = guard.refused[before:]
        if added == [f"{INJECT_TARGET[0]}:{INJECT_TARGET[1]}"]:
            del guard.refused[before:]
            self.armed.append(item.nodeid)
        else:
            self.not_armed.append(item.nodeid)

    def _inject_connect(self) -> None:
        """The mutant: an unmocked connect to canopy's port whose refusal the 'code' swallows."""
        self.injected += 1
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(INJECT_TARGET)
            except OSError:
                return

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item, nextitem):
        return (yield from self._phase(item, "teardown"))

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed") or (report.when == "teardown" and report.outcome == "failed"):
            previous = self.outcomes.get(report.nodeid)
            if previous in (None, "passed"):
                self.outcomes[report.nodeid] = report.outcome if report.when == "call" else f"{report.when}-{report.outcome}"

    # --- summary ------------------------------------------------------------------------------------------
    def summary(self) -> dict:
        by_port: dict[str, dict] = {}
        by_test: dict[str, dict] = {}
        for event in self.connects:
            port = by_port.setdefault(str(event["port"]), {"connects": 0, "tests": set(), "verdicts": Counter(), "hosts": Counter()})
            port["connects"] += 1
            port["tests"].add(event["test"])
            port["verdicts"][event["verdict"]] += 1
            port["hosts"][event["host"]] += 1
            entry = by_test.setdefault(
                event["test"],
                {"markers": self.markers.get(event["test"], []), "outcome": self.outcomes.get(event["test"]), "ports": Counter(), "phases": Counter(), "threads": Counter(), "first_frames": event["frames"]},
            )
            entry["ports"][f"{event['host']}:{event['port']}:{event['verdict']}"] += 1
            entry["phases"][event["phase"]] += 1
            entry["threads"][event["thread"]] += 1
        for port in by_port.values():
            port["tests"] = sorted(port["tests"])
            port["n_tests"] = len(port["tests"])
        return {"by_port": by_port, "by_test": by_test}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--wt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--inject", action="store_true", help="the lane-wide mutant: a swallowed connect to 127.0.0.1:8050 at the start of every test's call")
    parser.add_argument("--probe-guard", action="store_true", help="the same connect, withdrawn from the guard's record once refused: proves arming per test")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    pytest_args = args.pytest_args[1:] if args.pytest_args[:1] == ["--"] else args.pytest_args

    os.environ.update(CI_ENV)
    for name in ("GITHUB_ACTIONS", "GITHUB_STEP_SUMMARY"):
        os.environ.pop(name, None)
    os.chdir(args.wt)

    census = Census(args.wt, inject=args.inject, probe_guard=args.probe_guard)
    code = int(pytest.main(pytest_args, plugins=[census]))
    origins = {}
    for name in ORIGIN_MODULES:
        module = sys.modules.get(name)
        origins[name] = getattr(module, "__file__", None) if module is not None else None
    wt = str(args.wt.resolve())
    outside = {name: path for name, path in origins.items() if path is not None and not str(Path(path).resolve()).startswith(wt + os.sep)}
    outcome_counts = Counter(census.outcomes.values())
    record = {
        "exit": code,
        "wt": wt,
        "args": pytest_args,
        "python": sys.version.split()[0],
        "collected": census.collected,
        "injected": census.injected,
        "armed": census.armed,
        "not_armed": census.not_armed,
        "markers": census.markers,
        "outcomes": dict(outcome_counts),
        "outcome_by_test": census.outcomes,
        "failed": sorted(nodeid for nodeid, outcome in census.outcomes.items() if outcome not in ("passed", "skipped")),
        "n_connects": len(census.connects),
        **census.summary(),
        "connects": census.connects,
        "popen": census.popen,
        "getaddrinfo": dict(census.getaddrinfo),
        "import_origins": origins,
        "imported_outside_wt": outside,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, default=lambda value: dict(value) if isinstance(value, Counter) else sorted(value))
    ports = {port: (entry["connects"], entry["n_tests"]) for port, entry in record["by_port"].items()}
    print(f"[r17-census] exit={code} collected={census.collected} outcomes={dict(outcome_counts)} connects={len(census.connects)} by_port(connects,tests)={ports} popen={len(census.popen)} outside_wt={outside}")
    return code


if __name__ == "__main__":
    sys.exit(main())
