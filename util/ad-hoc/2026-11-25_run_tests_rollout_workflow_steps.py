#!/usr/bin/env python3
"""
Print a checkout's workflow jobs and steps compactly (no comments): the survey input for porting util/run_tests.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- the run_tests rollout (the 2026-11-24 handoff's section 1)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_run_tests_rollout_survey.py (reads the primaries; this reads any checkout, such as a
         worktree at a repo's origin/main)

For each workflow (all of them, or those named with ``--workflow``), each job: its name, ``needs``, ``if``,
``continue-on-error``, matrix and default working directory; then each step: name, ``if``, ``working-directory``,
``env`` keys, ``uses``, and the ``run`` script with comment-only lines dropped. ``--jobs`` limits the jobs shown
(fnmatch patterns). Read-only. Takes the checkout as an argument so no shell line has to name the workflow directory.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path

import yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--workflow", action="append", default=[], help="file name or glob (repeatable); default: all")
    parser.add_argument("--jobs", action="append", default=[], help="job id glob (repeatable); default: all")
    args = parser.parse_args(argv)
    wf_dir = Path(args.checkout) / ".github" / "workflows"
    files = sorted(wf_dir.glob("*.y*ml"))
    if args.workflow:
        files = [path for path in files if any(fnmatch.fnmatch(path.name, pattern) for pattern in args.workflow)]
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        on = data.get(True, data.get("on"))
        print(f"=== {path.name}   name={data.get('name')!r}   on={list(on) if isinstance(on, dict) else on}")
        for job_id, job in (data.get("jobs") or {}).items():
            if args.jobs and not any(fnmatch.fnmatch(job_id, pattern) for pattern in args.jobs):
                continue
            if not isinstance(job, dict):
                continue
            wd = ((job.get("defaults") or {}).get("run") or {}).get("working-directory")
            matrix = ((job.get("strategy") or {}).get("matrix")) or None
            print(f"--- job {job_id}  name={job.get('name')!r}  needs={job.get('needs')}  if={job.get('if')!r}  coe={job.get('continue-on-error')!r}  wd={wd!r}")
            if matrix:
                print(f"    matrix={matrix}")
            if job.get("env"):
                print(f"    job env={job.get('env')}")
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                bits = [f"name={step.get('name')!r}"]
                for key in ("id", "if", "working-directory", "uses", "shell"):
                    if step.get(key) is not None:
                        bits.append(f"{key}={step.get(key)!r}")
                if step.get("env"):
                    bits.append(f"env={sorted(step['env'])}")
                print("    * " + "  ".join(bits))
                for line in str(step.get("run") or "").splitlines():
                    if line.strip() and not line.strip().startswith("#"):
                        print(f"        | {line.rstrip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
