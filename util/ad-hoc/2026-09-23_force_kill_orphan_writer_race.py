"""
Measure how each ``_force_kill`` strategy fares against a stub that is still publishing its markers.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2046 (red ``main`` run 35864791786: ``OSError: [Errno 39] Directory not empty: '…/markers'``)

``tests/test_isolated_stack_script.py`` kills its launch stubs in a ``finally`` that runs INSIDE the
``TemporaryDirectory`` block, so whatever the kill leaves running races ``rmtree``. This drives the
exact production shape -- a ``/bin/bash -c`` harness started by ``subprocess.run`` (no new session)
that ``nohup``-launches a stub and echoes ``$!``; the stub publishes two markers through
``printf > X.partial`` + ``mv -f`` children, then ``exec sleep 60`` -- and kills it after a random
0-``--max-delay-ms`` delay, so the kill lands anywhere in the publishing window.

Per strategy it counts:

- ``stub_survived``  -- the stub pid still in ``/proc`` after the helper returned;
- ``writer_survived`` -- any process still referencing the iteration's marker dir after the helper
  returned (an orphaned ``mv`` mid-rename is the one that matters);
- ``enotempty``      -- ``TemporaryDirectory`` cleanup raising ``OSError`` errno 39, the CI symptom.

Strategies: ``current`` is the helper as it stood on ``main`` at 7fb40892 (three identical copies);
``minimal`` is the fix #2046 suggests (fall through to ``os.kill`` on ``ProcessLookupError``);
``shipped`` imports ``force_kill`` from ``tests/process_cleanup.py``, so the retained script measures
the code that actually runs in CI rather than a transcription of it.

The delay distribution is chosen to hit the window, so these counts say whether a race EXISTS under
each strategy, not how often CI would lose it. Every surviving process is SIGKILLed after it is
counted, so a run leaves nothing behind.

``--slow-writer-ms N`` is the CONSTRUCTED shape: each ``mv`` runs as ``sh -c 'sleep N; exec mv …'``,
standing in for a writer child descheduled under CPU contention -- the condition every earlier flake
in this suite needed. At natural timing the helper's own 50 ms poll outlasts an orphaned ``mv``, so
``minimal`` and ``shipped`` score the same; only a writer that outlives the poll separates a helper
that kills the stub from one that kills what the stub has in flight.

Usage (from the repo root)::

    python3 util/ad-hoc/2026-09-23_force_kill_orphan_writer_race.py --iterations 300
    python3 util/ad-hoc/2026-09-23_force_kill_orphan_writer_race.py --iterations 100 --slow-writer-ms 300
"""

from __future__ import annotations

import argparse
import errno
import os
import random
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def current(pid: int) -> None:
    """The helper as it stood on ``main`` at 7fb40892 (``:994``, ``:1514``, ``:1885``)."""
    for kill_target in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
        try:
            kill_target()
            break
        except ProcessLookupError:
            return
        except PermissionError:
            continue
    for _ in range(20):
        if not Path(f"/proc/{pid}").exists():
            return
        time.sleep(0.05)


def minimal(pid: int) -> None:
    """The fix #2046 suggests: a ``killpg`` miss falls through to ``os.kill``."""
    for kill in (os.killpg, os.kill):
        try:
            kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue
    for _ in range(20):
        if not Path(f"/proc/{pid}").exists():
            return
        time.sleep(0.05)


def _shipped():
    sys.path.insert(0, str(REPO_ROOT))
    from tests.process_cleanup import force_kill

    return force_kill


def _referencing(marker_dir: Path) -> "list[int]":
    """Pids whose cmdline names ``marker_dir`` -- an orphaned ``mv`` carries both paths in argv."""
    needle = str(marker_dir).encode()
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if needle in (entry / "cmdline").read_bytes():
                found.append(int(entry.name))
        except OSError:
            continue
    return found


def _write_stub(stub: Path, marker_dir: Path, slow_writer_ms: float) -> None:
    """The ``bin/python`` stub from ``TestDataUpLive._write_python314_stub``, verbatim unless slowed."""
    if slow_writer_ms > 0:
        mv = f"sh -c 'sleep {slow_writer_ms / 1000:.3f}; exec mv -f \"$0\" \"$1\"'"
    else:
        mv = "mv -f"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "PYTHON_GIL=%s\\n" "${{PYTHON_GIL-}}" >"{marker_dir}/python.env.partial"\n'
        f'{mv} "{marker_dir}/python.env.partial" "{marker_dir}/python.env"\n'
        f'printf "%s\\n" "$@" >"{marker_dir}/python.args.partial"\n'
        f'{mv} "{marker_dir}/python.args.partial" "{marker_dir}/python.args"\n'
        "exec sleep 60\n"
    )
    stub.chmod(0o755)


def run_one(helper, max_delay_ms: float, slow_writer_ms: float) -> "dict[str, bool]":
    outcome = {"stub_survived": False, "writer_survived": False, "enotempty": False}
    leftovers: "list[int]" = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker_dir = root / "markers"
            marker_dir.mkdir()
            stub = root / "python"
            _write_stub(stub, marker_dir, slow_writer_ms)
            launched = subprocess.run(
                ["/bin/bash", "-c", f'nohup "{stub}" -m juniper_data --port 65301 >/dev/null 2>&1 & echo "$!"'],
                capture_output=True,
                text=True,
                timeout=10,
            )
            pid = int(launched.stdout.strip())
            time.sleep(random.uniform(0, max_delay_ms) / 1000)
            helper(pid)
            if Path(f"/proc/{pid}").exists():
                outcome["stub_survived"] = True
                leftovers.append(pid)
            writers = [p for p in _referencing(marker_dir) if p != pid]
            if writers:
                outcome["writer_survived"] = True
                leftovers.extend(writers)
    except OSError as exc:
        if exc.errno != errno.ENOTEMPTY:
            raise
        outcome["enotempty"] = True
    finally:
        for stray in leftovers:
            try:
                os.kill(stray, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                # Exited between being counted and being reaped: already what we want.
                pass
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--max-delay-ms", type=float, default=15.0)
    parser.add_argument("--slow-writer-ms", type=float, default=0.0)
    parser.add_argument("--strategies", default="current,minimal,shipped")
    parser.add_argument("--seed", type=int, default=2046)
    args = parser.parse_args()

    random.seed(args.seed)
    helpers = {"current": current, "minimal": minimal}
    if "shipped" in args.strategies.split(","):
        helpers["shipped"] = _shipped()
    print(f"runner pid={os.getpid()} pgid={os.getpgid(0)} iterations={args.iterations} max_delay_ms={args.max_delay_ms} slow_writer_ms={args.slow_writer_ms} seed={args.seed}")
    worst = 0
    for name in args.strategies.split(","):
        counts = {"stub_survived": 0, "writer_survived": 0, "enotempty": 0}
        started = time.monotonic()
        for _ in range(args.iterations):
            for key, hit in run_one(helpers[name], args.max_delay_ms, args.slow_writer_ms).items():
                counts[key] += hit
        elapsed = time.monotonic() - started
        print(f"{name:8s} stub_survived={counts['stub_survived']:4d}  writer_survived={counts['writer_survived']:4d}  enotempty={counts['enotempty']:4d}  ({elapsed:.1f}s)")
        if name == "shipped":
            worst = sum(counts.values())
    # Exit status reflects only the shipped helper: the other two are the controls.
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main())
