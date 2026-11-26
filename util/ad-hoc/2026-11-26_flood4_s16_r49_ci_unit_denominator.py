"""
Count juniper-canopy's unit-lane jobs that actually ran (success or failure) per event class and Python leg, over every
completed ci.yml run attempt in a census listing: the denominator for the health test's CI failure rate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; input runs_all.json from
    util/ad-hoc/2026-11-26_flood4_s16_r49_ci_census.py

Usage:
    python3 -I <this file> --repo pcalnon/juniper-canopy --census-dir <dir with runs_all.json>
One GET (`gh api .../runs/<id>/attempts/<n>/jobs`) per attempt of every run whose conclusion is success or failure.
Writes <census-dir>/unit_denominator.json: unit-lane jobs by (main|pr) x leg x job conclusion, and by day.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess  # nosec B404 - fixed gh argv lists, no shell
import sys
from pathlib import Path

UNIT_JOB_PREFIX = "Unit Tests + Coverage"


def gh_jobs(repo: str, run_id: int, attempt: int) -> list[dict]:
    argv = ["gh", "api", "--paginate", "-H", "Accept: application/vnd.github+json", f"repos/{repo}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100"]
    cp = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    if cp.returncode != 0:
        raise RuntimeError(f"gh api jobs {run_id}/{attempt} failed: {cp.stderr.strip()[:300]}")
    decoder = json.JSONDecoder()
    text, index, jobs = cp.stdout.strip(), 0, []
    while index < len(text):
        obj, end = decoder.raw_decode(text, index)
        jobs.extend(obj.get("jobs", []))
        index = end
        while index < len(text) and text[index].isspace():
            index += 1
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--census-dir", required=True)
    args = parser.parse_args()
    root = Path(args.census_dir)
    runs = [r for r in json.loads((root / "runs_all.json").read_text(encoding="utf-8")) if r["conclusion"] in ("success", "failure")]
    by_class = collections.Counter()
    by_day = collections.defaultdict(collections.Counter)
    for run in runs:
        klass = "main" if run["head_branch"] == "main" else "pr"
        for attempt in range(1, (run["run_attempt"] or 1) + 1):
            for job in gh_jobs(args.repo, run["id"], attempt):
                name = job.get("name") or ""
                if not name.startswith(UNIT_JOB_PREFIX) or job.get("conclusion") not in ("success", "failure"):
                    continue
                leg = name[len(UNIT_JOB_PREFIX) :].strip(" ()")
                by_class[f"{klass}|{leg}|{job['conclusion']}"] += 1
                by_day[run["created_at"][:10]][klass] += 1
    totals = collections.Counter()
    for key, count in by_class.items():
        totals[key.split("|")[0]] += count
    result = {"runs_read": len(runs), "unit_jobs_ran_by_class": dict(totals), "unit_jobs_by_class_leg_conclusion": dict(sorted(by_class.items())), "unit_jobs_ran_by_day": {d: dict(c) for d, c in sorted(by_day.items())}}
    (root / "unit_denominator.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({"runs_read": len(runs), "unit_jobs_ran_by_class": dict(totals)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
