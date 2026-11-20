#!/usr/bin/env python3
"""List every workflow job whose JOB-level ``continue-on-error`` is exactly ``${{ matrix.experimental == true }}``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (found the target jobs for juniper-data-client#262, juniper-cascor-client#197 and
        juniper-deploy#275)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_py315_informational_green_legs.py (juniper-ml#2578; it edits the jobs this finds);
         tmp/py315/GREEN_LEGS_BRIEF.md ("Target jobs ... Find them by parsing every workflow; don't trust memory")

Why this exists
---------------
The green-legs edit applies to every job that carries phase 1's job-level informational expression, and to no
other job. This parses every ``.github/workflows/*.yml`` / ``*.yaml`` of each repo given and prints each such job
with its name, matrix and steps, flagging any step that already sets ``id``, ``if`` or its own
``continue-on-error`` (a step-level ``continue-on-error`` makes the edit script refuse, so it must be combined by
hand). Any other job with a job-level ``continue-on-error`` or a matrix mentioning 3.15 is listed as a NOTE.
Read-only.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_green_legs_survey.py <repo-worktree> [<repo-worktree> ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

EXPR = "${{ matrix.experimental == true }}"


def main() -> int:
    for root in sys.argv[1:]:
        wf_dir = Path(root) / ".github" / "workflows"
        print(f"=== {root}")
        files = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")))
        print(f"    {len(files)} workflow files")
        for wf in files:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
            jobs = (doc or {}).get("jobs") or {}
            for jid, job in jobs.items():
                if not isinstance(job, dict):
                    continue
                coe = job.get("continue-on-error")
                matrix = ((job.get("strategy") or {}).get("matrix")) or {}
                mentions_315 = "3.15" in yaml.safe_dump(matrix) if matrix else False
                if coe == EXPR:
                    steps = job.get("steps") or []
                    print(f"  TARGET {wf.name} :: {jid}  name={job.get('name')!r}  steps={len(steps)}")
                    print(f"         matrix={matrix}")
                    for i, s in enumerate(steps):
                        label = s.get("name") or s.get("uses")
                        flags = []
                        if "id" in s:
                            flags.append(f"id={s['id']}")
                        if "continue-on-error" in s:
                            flags.append(f"STEP-COE={s['continue-on-error']!r}")
                        if "if" in s:
                            flags.append(f"if={s['if']!r}")
                        print(f"           [{i}] {label!r} {' '.join(flags)}")
                elif coe is not None or mentions_315:
                    print(f"  NOTE   {wf.name} :: {jid}  job-coe={coe!r}  matrix-mentions-3.15={mentions_315}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
