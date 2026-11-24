#!/usr/bin/env python3
"""
Sample an experiment run's process trees from /proc at 1 s and write cpu-seconds per wall-second per role — the occupancy of one Juniper run, in cores.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc — investigation (perf lane P2 item 4.1 residue: the PF-8 occupancy probe, step 1 of §1.3 of the 2026-09-08 re-scope note)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md

WHY THIS EXISTS

§8.4 of the 2026-09-02 instrument-resolution note locates the contention knee in SYNTHETIC-WORKER
units (one worker = one saturated core), and §1.3 of the 2026-09-08 re-scope note says PF-8's
marginal value is finding where one Juniper run sits on that axis. Nothing records it: the driver's
manifest carries nproc and the thread env, not what the run actually consumed, and `ps %CPU` is a
lifetime average (cputime / elapsed) — useless for a 60 s window. This reads `/proc/<pid>/stat`
utime+stime for every process in the run's trees once a second and writes the deltas, so the mean
over the training window is the run's core occupancy; reading that as sweep workers is an
assumption, stated below.

WHAT IT SAMPLES

It watches the run root for run directories created after it started (the launcher writes
`ports.json` at `--up`, then `juniper-data.pid` / `juniper-cascor.pid` once each service has
answered health) and, for each, walks the process table:

    cascor_uvicorn     the recorded cascor listener pid
    cascor_forkserver  its child whose cmdline names the multiprocessing forkserver
    cascor_workers     every descendant of the forkserver (the candidate pool)
    cascor_other       any other descendant of the listener
    cascor_tree        the sum of the four above  <- the figure §1.3 asks for
    data               the juniper-data listener and its descendants
    driver             run_experiment.py for this run dir, and its descendants
    total              cascor_tree + data + driver
    host_busy_cores    (busy / total) jiffies from /proc/stat x nproc — the WHOLE host, ours and
                       everyone else's; ambient occupancy = host_busy_cores - total / wall_dt

Every cpu column is cpu-seconds spent in the interval; divide by `wall_dt` for occupancy in CORES.
Equating one core with one sweep worker is an assumption §8.4 of the sweep note disclaims (the
knee is located in worker count, not cores). A pid born inside an interval is counted from birth (`starttime` against the
previous tick's uptime); a pid that exits inside one loses its final partial second, which
`vanished` counts so the loss can be bounded. Rows with `run_id -` are host-only ticks between
cells and give the ambient trace.

Run it in the background BEFORE launching the suite and stop it by the pid `--pid-file` records —
never `kill $!` after `setsid nohup` (that is the wrapper), and never `pkill -f` on a pattern your
own shell's command line matches:

    python3 util/ad-hoc/2026-09-10_pf8_occupancy_sampler.py --out SUITE_DIR/occupancy.tsv --pid-file PATH.pid &
    ...
    kill "$(cat PATH.pid)"          # or: touch the --stop-file

Reduce with util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py.
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CLK_TCK = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
DEFAULT_RUN_ROOT = Path(os.environ.get("JUNIPER_EXP_RUN_ROOT", str(Path.home() / ".local" / "state" / "juniper-experiments")))
RUN_ID_RE = re.compile(r"^(\d{8}T\d{6})Z-[0-9a-f]{4}$")
ROLES = ("cascor_uvicorn", "cascor_forkserver", "cascor_workers", "cascor_other", "data", "driver")
CASCOR_ROLES = ("cascor_uvicorn", "cascor_forkserver", "cascor_workers", "cascor_other")
COLUMNS = ("utc_iso", "epoch_s", "run_id", "wall_dt", *ROLES, "cascor_tree", "total", "n_workers", "n_pids", "vanished", "host_busy_cores", "load_1m")
#: Consecutive ticks with no live tracked pid (after the run had some) before the run is detached.
DETACH_AFTER_IDLE_TICKS = 5

_STOP = False


def _stop(signum, frame):  # noqa: ARG001 - signal handler signature
    global _STOP
    _STOP = True


@dataclass(frozen=True)
class ProcStat:
    pid: int
    comm: str
    ppid: int
    cpu_ticks: int  # utime + stime, clock ticks
    start_ticks: int  # starttime, clock ticks since boot


def parse_stat(text: str) -> "ProcStat | None":
    """Parse one ``/proc/<pid>/stat`` line.

    ``comm`` may contain spaces and parentheses, so the fields are split around the LAST ``)``.
    After it, ``rest[i]`` is field ``i + 3`` of proc(5): ppid = 4, utime = 14, stime = 15,
    starttime = 22.
    """
    try:
        lparen = text.index("(")
        rparen = text.rindex(")")
        pid = int(text[:lparen].strip())
        comm = text[lparen + 1 : rparen]
        rest = text[rparen + 1 :].split()
        return ProcStat(pid, comm, int(rest[1]), int(rest[11]) + int(rest[12]), int(rest[19]))
    except (ValueError, IndexError):
        return None


def snapshot_procs(proc: Path = Path("/proc")) -> "dict[int, ProcStat]":
    out: "dict[int, ProcStat]" = {}
    for entry in os.listdir(proc):
        if not entry.isdigit():
            continue
        try:
            text = (proc / entry / "stat").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue  # exited between listdir and read
        st = parse_stat(text)
        if st is not None:
            out[st.pid] = st
    return out


def read_cmdline(pid: int, proc: Path = Path("/proc")) -> str:
    try:
        return (proc / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:
        return ""


def children_map(procs: "dict[int, ProcStat]") -> "dict[int, list[int]]":
    kids: "dict[int, list[int]]" = defaultdict(list)
    for st in procs.values():
        kids[st.ppid].append(st.pid)
    return kids


def descendants(root: int, kids: "dict[int, list[int]]") -> "set[int]":
    seen: "set[int]" = set()
    stack = [root]
    while stack:
        parent = stack.pop()
        for child in kids.get(parent, ()):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def classify_roles(cascor_pid: "int | None", data_pid: "int | None", driver_pid: "int | None", procs: "dict[int, ProcStat]", cmdline_of) -> "dict[str, set[int]]":
    """Assign every live pid of the run's three trees to one role. Pure: ``cmdline_of(pid) -> str``."""
    roles: "dict[str, set[int]]" = {role: set() for role in ROLES}
    kids = children_map(procs)
    if cascor_pid is not None and cascor_pid in procs:
        roles["cascor_uvicorn"].add(cascor_pid)
        for child in kids.get(cascor_pid, ()):
            if "forkserver" in cmdline_of(child):
                roles["cascor_forkserver"].add(child)
                roles["cascor_workers"] |= descendants(child, kids)
            else:
                roles["cascor_other"].add(child)
                roles["cascor_other"] |= descendants(child, kids)
    if data_pid is not None and data_pid in procs:
        roles["data"] = {data_pid} | descendants(data_pid, kids)
    if driver_pid is not None and driver_pid in procs:
        roles["driver"] = {driver_pid} | descendants(driver_pid, kids)
    return roles


def account(prev_ticks: "dict[int, int]", prev_uptime_ticks: "float | None", procs: "dict[int, ProcStat]", roles: "dict[str, set[int]]", clk_tck: int = CLK_TCK) -> "tuple[dict[str, float], int]":
    """cpu-seconds per role since the previous tick, and how many previously tracked pids are gone.

    A pid absent from ``prev_ticks`` counts from birth when its ``starttime`` is at or after the
    previous tick's uptime (it was born inside the interval); otherwise it is a baseline sample
    that contributes nothing this tick (we just attached, and its history is not ours to claim).
    A pid that exited inside the interval takes its final partial second with it — reported in
    the vanished count, never invented.
    """
    seconds: "dict[str, float]" = {}
    for role, pids in roles.items():
        ticks = 0
        for pid in pids:
            st = procs[pid]
            if pid in prev_ticks:
                ticks += max(0, st.cpu_ticks - prev_ticks[pid])
            elif prev_uptime_ticks is not None and st.start_ticks >= prev_uptime_ticks:
                ticks += st.cpu_ticks
        seconds[role] = ticks / clk_tck
    vanished = sum(1 for pid in prev_ticks if pid not in procs)
    return seconds, vanished


def read_cpu_jiffies(path: Path = Path("/proc/stat")) -> "tuple[int, int]":
    """``(busy, total)`` jiffies from the aggregate ``cpu`` line: idle = idle + iowait."""
    line = path.read_text(encoding="utf-8").splitlines()[0]
    vals = [int(v) for v in line.split()[1:]]
    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
    total = sum(vals[:8])
    return total - idle, total


def host_busy_cores(prev: "tuple[int, int]", cur: "tuple[int, int]", nproc: int) -> float:
    busy = cur[0] - prev[0]
    total = cur[1] - prev[1]
    return (busy / total) * nproc if total > 0 else 0.0


def uptime_ticks(path: Path = Path("/proc/uptime"), clk_tck: int = CLK_TCK) -> float:
    return float(path.read_text(encoding="utf-8").split()[0]) * clk_tck


def load_1m(path: Path = Path("/proc/loadavg")) -> str:
    return path.read_text(encoding="utf-8").split()[0]


@dataclass
class RunHandle:
    run_id: str
    run_dir: Path
    cascor_pid: "int | None" = None
    data_pid: "int | None" = None
    driver_pid: "int | None" = None
    prev_ticks: "dict[int, int]" = field(default_factory=dict)
    seen_pids: bool = False
    idle_ticks: int = 0


def _pid_from(path: Path) -> "int | None":
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def discover_runs(run_root: Path, since_utc: datetime, known: "dict[str, RunHandle]", done: "set[str]") -> None:
    """Attach every run dir whose id timestamp is at or after ``since_utc`` and is not already known or finished."""
    try:
        entries = list(os.scandir(run_root))
    except OSError:
        return
    for entry in entries:
        match = RUN_ID_RE.match(entry.name)
        if not match or not entry.is_dir() or entry.name in known or entry.name in done:
            continue
        stamp = datetime.strptime(match.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        if stamp < since_utc:
            continue
        known[entry.name] = RunHandle(entry.name, Path(entry.path))


class CmdlineCache:
    """One tick's memo of ``/proc/<pid>/cmdline`` reads, so a pid is read at most once per tick."""

    def __init__(self, proc: Path = Path("/proc")) -> None:
        self._proc = proc
        self._cache: "dict[int, str]" = {}

    def __call__(self, pid: int) -> str:
        if pid not in self._cache:
            self._cache[pid] = read_cmdline(pid, self._proc)
        return self._cache[pid]


def find_driver_pid(run_dir: Path, procs: "dict[int, ProcStat]", cmdline_of) -> "int | None":
    """The driver is invoked as ``python run_experiment.py --config … --run-dir RUN_DIR`` by run_suite."""
    needle = str(run_dir)
    for pid in procs:
        cmd = cmdline_of(pid)
        if "run_experiment.py" in cmd and needle in cmd:
            return pid
    return None


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="TSV to append to (header written when the file is new)")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--since-seconds", type=float, default=60.0, help="attach run dirs whose id timestamp is at most this many seconds before the sampler started")
    parser.add_argument("--max-seconds", type=float, default=7200.0, help="hard stop, so an un-killed sampler cannot outlive its purpose by a day")
    parser.add_argument("--pid-file", type=Path, default=None, help="write the sampler's own pid here (the pid to kill)")
    parser.add_argument("--stop-file", type=Path, default=None, help="stop when this path appears")
    args = parser.parse_args(argv)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    if args.pid_file is not None:
        args.pid_file.parent.mkdir(parents=True, exist_ok=True)
        args.pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")

    nproc = os.cpu_count() or 1
    started = time.time()
    since_utc = datetime.fromtimestamp(started - args.since_seconds, timezone.utc)
    known: "dict[str, RunHandle]" = {}
    done: "set[str]" = set()
    prev_cpu = read_cpu_jiffies()
    prev_uptime: "float | None" = None
    prev_time = started

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fresh = not args.out.exists()
    with args.out.open("a", encoding="utf-8") as out:
        if fresh:
            out.write("\t".join(COLUMNS) + "\n")
        while not _STOP and time.time() - started < args.max_seconds and not (args.stop_file is not None and args.stop_file.exists()):
            time.sleep(args.interval)
            now = time.time()
            wall_dt = now - prev_time
            procs = snapshot_procs()
            uptime = uptime_ticks()
            cur_cpu = read_cpu_jiffies()
            busy_cores = host_busy_cores(prev_cpu, cur_cpu, nproc)
            load = load_1m()
            iso = datetime.fromtimestamp(now, timezone.utc).isoformat(timespec="seconds")
            discover_runs(args.run_root, since_utc, known, done)
            cmdline_of = CmdlineCache()
            wrote = 0
            for run in list(known.values()):
                if run.cascor_pid is None:
                    run.cascor_pid = _pid_from(run.run_dir / "juniper-cascor.pid")
                if run.data_pid is None:
                    run.data_pid = _pid_from(run.run_dir / "juniper-data.pid")
                if run.driver_pid is None or run.driver_pid not in procs:
                    run.driver_pid = find_driver_pid(run.run_dir, procs, cmdline_of)
                roles = classify_roles(run.cascor_pid, run.data_pid, run.driver_pid, procs, cmdline_of)
                tracked = set().union(*roles.values())
                seconds, vanished = account(run.prev_ticks, prev_uptime, procs, roles)
                run.prev_ticks = {pid: procs[pid].cpu_ticks for pid in tracked}
                if tracked:
                    run.seen_pids = True
                    run.idle_ticks = 0
                elif run.seen_pids:
                    run.idle_ticks += 1
                tree = sum(seconds[r] for r in CASCOR_ROLES)
                total = tree + seconds["data"] + seconds["driver"]
                cells = [iso, f"{now:.3f}", run.run_id, f"{wall_dt:.3f}", *(f"{seconds[r]:.3f}" for r in ROLES), f"{tree:.3f}", f"{total:.3f}", str(len(roles["cascor_workers"])), str(len(tracked)), str(vanished), f"{busy_cores:.3f}", load]
                out.write("\t".join(cells) + "\n")
                wrote += 1
                if run.seen_pids and run.idle_ticks >= DETACH_AFTER_IDLE_TICKS:
                    done.add(run.run_id)
                    del known[run.run_id]
            if wrote == 0:
                cells = [iso, f"{now:.3f}", "-", f"{wall_dt:.3f}", *("0.000" for _ in ROLES), "0.000", "0.000", "0", "0", "0", f"{busy_cores:.3f}", load]
                out.write("\t".join(cells) + "\n")
            out.flush()
            prev_cpu, prev_uptime, prev_time = cur_cpu, uptime, now
    if args.pid_file is not None:
        try:
            args.pid_file.unlink()
        except OSError:
            pass  # best-effort: the pid file is advisory and may already be gone
    return 0


if __name__ == "__main__":
    sys.exit(main())
