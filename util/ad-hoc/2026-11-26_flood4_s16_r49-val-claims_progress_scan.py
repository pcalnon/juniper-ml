#!/usr/bin/env python3
"""
Read the pytest progress line of test_x7_loop_responsiveness.py in juniper-canopy unit-lane job logs (cancelled jobs).

A job cancelled while pytest runs prints no failure section and no -ra summary, so a test that failed before the
cancel shows only as an `F` (or `E`) in the file's progress line ("src/tests/regression/test_x7_loop_responsiveness.py
F...  [ 98%]"; the lane runs -q with --verbose, net verbosity 0). For every unit-lane job of the chosen conclusions in
the census's unit_jobs.json, this downloads the log (one `gh api` GET) and records whether pytest reached the file and
the file's progress marks. The first mark is the health test (the file's first test). Keeps no log, only the lines.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - gh api GETs
import sys
from pathlib import Path

PROGRESS_RE = re.compile(r"src/tests/regression/test_x7_loop_responsiveness\.py ([.FEsxX]+)\s+\[")


def main() -> int:
    ap = argparse.ArgumentParser(description="scan cancelled unit-lane job logs for the X7 file's progress marks")
    ap.add_argument("--repo", default="pcalnon/juniper-canopy")
    ap.add_argument("--census", required=True, help="the census output directory (holds unit_jobs.json)")
    ap.add_argument("--conclusions", default="cancelled,timed_out")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with (Path(args.census) / "unit_jobs.json").open(encoding="utf-8") as fh:
        jobs = json.load(fh)
    wanted = set(args.conclusions.split(","))
    rows = []
    for job in jobs:
        if job["conclusion"] not in wanted or job["status"] != "completed":
            continue
        proc = subprocess.run(["gh", "api", f"repos/{args.repo}/actions/jobs/{job['id']}/logs"], capture_output=True, check=False)  # nosec B603 B607
        if proc.returncode != 0:
            rows.append({"job_id": job["id"], "run_id": job["run_id"], "error": proc.stderr.decode(errors="replace")[:200]})
            continue
        text = proc.stdout.decode("utf-8", errors="replace")
        marks = [m.group(1) for m in PROGRESS_RE.finditer(text)]
        rows.append({
            "job_id": job["id"], "run_id": job["run_id"], "attempt": job["attempt"], "name": job["name"], "branch": job["head_branch"],
            "reached_file": bool(marks), "marks": marks, "health_mark": marks[0][0] if marks else None,
            "any_fail_in_file": any(("F" in m or "E" in m) for m in marks), "pytest_started": "test session starts" in text,
        })
    summary = {
        "jobs_scanned": len(rows),
        "errors": sum(1 for r in rows if "error" in r),
        "pytest_started": sum(1 for r in rows if r.get("pytest_started")),
        "reached_x7_file": sum(1 for r in rows if r.get("reached_file")),
        "health_mark_counts": {k: sum(1 for r in rows if str(r.get("health_mark")) == k) for k in sorted({str(r.get("health_mark")) for r in rows})},
        "any_fail_in_file": [r for r in rows if r.get("any_fail_in_file")],
    }
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
