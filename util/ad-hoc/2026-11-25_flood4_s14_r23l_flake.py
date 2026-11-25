"""
Run ruling 23's new and adapted lifecycle tests many times in one pytest process, to look for flakes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — one-off verification (flood-4 session 14, builder r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23);
         adapted from util/ad-hoc/2026-11-09_flood4r2_n2_stress.py (juniper-ml#2557)

Each selected test (the two new files, and the three adapted after-a-load tests of
test_lifecycle_stop_then_start.py) is passed ``--repeat`` times to one pytest run with ``--keep-duplicates``, so
every test runs that many times in one process, against ``--repo-root``'s juniper-service-core (PYTHONPATH, with its
juniper-model-core after it). With ``--switch-interval`` the pytest process first calls ``sys.setswitchinterval``.
pytest's ``--basetemp`` goes under ``--scratch`` and is removed afterwards. Prints pytest's summary line and exits
with pytest's status.

Usage: python3 <this file> --repo-root <juniper-ml checkout> --python <interpreter> --scratch <dir in a repo tmp/>
       [--repeat 50] [--switch-interval 1e-6] [--log FILE]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = "juniper-service-core"
SELECTED = (
    "tests/test_lifecycle_stop_then_load.py",
    "tests/test_lifecycle_leftover_replay_session.py",
    *(f"tests/test_lifecycle_stop_then_start.py::test_a_start_after_a_snapshot_load_is_refused_while_the_stopped_fit_is_still_running[{p}]" for p in ("resume_from_snapshot-RESUME_READY", "load_snapshot-INVESTIGATING", "start_replay-REPLAYING")),
)
_WITH_SWITCH_INTERVAL = "import sys, pytest; sys.setswitchinterval(float(sys.argv[1])); print('switch interval', sys.getswitchinterval(), flush=True); sys.exit(pytest.main(sys.argv[2:]))"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--repeat", type=int, default=50)
    parser.add_argument("--switch-interval", type=float)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    package = (args.repo_root / PACKAGE).resolve()
    args.scratch.mkdir(parents=True, exist_ok=True)
    basetemp = args.scratch.resolve() / "basetemp"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(package), str((args.repo_root / "juniper-model-core").resolve())))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    # No -q here: the package's addopts already pass -q, and a second one (-qq) drops pytest's summary line.
    pytest_args = ["-p", "no:cacheprovider", "--keep-duplicates", f"--basetemp={basetemp}", *(list(SELECTED) * args.repeat)]
    if args.switch_interval is None:
        cmd = [args.python, "-m", "pytest", *pytest_args]
    else:
        cmd = [args.python, "-c", _WITH_SWITCH_INTERVAL, repr(args.switch_interval), *pytest_args]
    try:
        result = subprocess.run(cmd, cwd=package, env=env, capture_output=True, text=True, check=False)
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
    if args.log is not None:
        with open(args.log, "w", encoding="utf-8") as fh:
            fh.write(result.stdout)
            fh.write(result.stderr)
    lines = result.stdout.splitlines()
    for line in lines[:1] if args.switch_interval is not None else []:
        print(line)
    summary = next((line for line in reversed(lines) if " in " in line and ("passed" in line or "failed" in line)), "(no summary line)")
    print(summary.strip("= "))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
