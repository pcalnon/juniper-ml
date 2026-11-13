#!/usr/bin/env python3
"""Stop-then-start race stress repeat: run the lifecycle race tests many times in one pytest process.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- one-off verification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
             juniper-service-core/tests/test_lifecycle_stop_then_start.py and
             juniper-service-core/tests/test_lifecycle_paused_fit_return.py

Passes each test file ``--repeat`` times to one pytest run with ``--keep-duplicates``, so every
test runs that many times in one process, against the checkout's ``juniper-service-core`` and
``juniper-model-core`` (``PYTHONPATH``; pytest's rootdir insertion also puts the checkout's
``juniper-service-core`` first). With ``--switch-interval`` the pytest process first calls
``sys.setswitchinterval`` with that value (``1e-6`` switches threads about five thousand times as
often as the default 5 ms), and prints the interval in effect. pytest's ``--basetemp`` goes under
``--scratch`` and is removed afterwards; ``TMPDIR`` is left as the session set it. Prints pytest's
summary line and exits with pytest's status.

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_stress.py --python <interpreter> --scratch <a scratch dir in the repo's tmp> \\
        [--repeat 100] [--switch-interval 1e-6] [--log <file>]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "juniper-service-core/tests/test_lifecycle_stop_then_start.py",
    "juniper-service-core/tests/test_lifecycle_paused_fit_return.py",
)
# Runs pytest in a process whose interpreter switches threads every argv[1] seconds, and says so first.
_WITH_SWITCH_INTERVAL = "import sys, pytest; sys.setswitchinterval(float(sys.argv[1])); print('switch interval', sys.getswitchinterval(), flush=True); sys.exit(pytest.main(sys.argv[2:]))"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", required=True, help="an interpreter with juniper-service-core's test dependencies")
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch directory under the repo's tmp/ (never the system temp dir)")
    parser.add_argument("--repeat", type=int, default=100, help="how many times each file is passed (default 100)")
    parser.add_argument("--log", type=Path, help="write pytest's full output here")
    parser.add_argument("--switch-interval", type=float, help="run pytest with sys.setswitchinterval(<seconds>), e.g. 1e-6, so threads are switched far more often")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")

    args.scratch.mkdir(parents=True, exist_ok=True)  # pytest creates the basetemp itself, but not its parent
    basetemp = args.scratch.resolve() / "basetemp"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(REPO_ROOT / "juniper-service-core"), str(REPO_ROOT / "juniper-model-core")))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pytest_args = [*(list(FILES) * args.repeat), "--keep-duplicates", "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
    cmd = [args.python, "-m", "pytest", *pytest_args] if args.switch_interval is None else [args.python, "-c", _WITH_SWITCH_INTERVAL, str(args.switch_interval), *pytest_args]
    try:
        result = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True, check=False)
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
    if args.log is not None:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        with open(args.log, "w", encoding="utf-8") as fh:
            fh.write(result.stdout)
            fh.write(result.stderr)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    print(lines[-1] if lines else result.stderr.strip())
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
