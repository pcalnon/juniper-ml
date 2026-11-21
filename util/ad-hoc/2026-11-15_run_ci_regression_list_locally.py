#!/usr/bin/env python3
"""Run every ``python3 -m unittest`` command of ci.yml's "Run Python regression tests" step, past failures.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (local pre-push check for the Python 3.15 informational-leg change)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_edits.py (the change this checks);
         memory note reference_ci_merge_mechanics_hub.md (the CI step runs under ``bash -e`` and stops at the first
         failing suite, so its red says nothing about the suites after it)

Why this exists
---------------
The CI step is ~240 ``python3 -m unittest`` commands under ``bash -e``. This reads them from the step itself (so the
list cannot drift from CI), runs each one with the interpreter you name (``python3`` in the command is replaced by
``--python``), keeps going past failures, and prints one line per failing suite plus a count.

Desktop side effect guarded: ``DBUS_SESSION_BUS_ADDRESS`` points at a socket that does not exist, so a suite that
reaches the real ``notify-send`` cannot raise a desktop alert (juniper-ml#2559 fixed the known one; this is belt and
braces).

Usage
-----
    python3 util/ad-hoc/2026-11-15_run_ci_regression_list_locally.py --python /path/to/python3.14 [--out FILE]

Exit 0 when every suite passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import yaml

STEP_NAME = "Run Python regression tests"


def suite_commands(repo: Path) -> list[list[str]]:
    doc = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    step = next(s for s in doc["jobs"]["tests"]["steps"] if s.get("name") == STEP_NAME)
    return [shlex.split(line.strip()) for line in step["run"].splitlines() if line.strip().startswith("python3 -m unittest")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python", required=True, help="interpreter that replaces python3 in each command")
    ap.add_argument("--repo", default=".", type=Path, help="checkout root (default: cwd)")
    ap.add_argument("--out", type=Path, help="also write the per-suite log here")
    args = ap.parse_args()
    repo = args.repo.resolve()
    env = dict(os.environ, DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent/no-session-bus")
    cmds = suite_commands(repo)
    failed: list[str] = []
    log_lines: list[str] = []
    start = time.monotonic()
    for argv in cmds:
        argv = [args.python, *argv[1:]]
        proc = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True)  # nosec B603
        suite = " ".join(argv[1:])
        tail = (proc.stderr.strip().splitlines() or [""])[-1]
        log_lines.append(f"rc={proc.returncode} {suite} :: {tail}")
        if proc.returncode != 0:
            failed.append(f"{suite} :: {tail}")
    summary = f"{len(cmds) - len(failed)}/{len(cmds)} suites passed in {time.monotonic() - start:.0f}s"
    if args.out:
        args.out.write_text("\n".join(log_lines + [summary, ""]), encoding="utf-8")
    for f in failed:
        print(f"FAILED {f}")
    print(summary)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
