#!/usr/bin/env python3
"""Count every informational Python 3.15 leg run since a cutoff, across all branches: how many passed, how many warned.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-16
Status:      ad-hoc -- investigation (Python 3.15 migration arc, phase 3 go/no-go: is 3.15 green on every run, or only the latest?)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_py315_leg_survey.py (reads only the LATEST main run per workflow),
             util/ad-hoc/2026-11-15_py315_informational_green_legs.py (the report step whose annotation this reads)

Why this exists
---------------
The leg survey reads one run per workflow: the newest on `main`. That is a single sample, and it cannot tell a
steady pass from a flaky one. Phase 3 makes these legs block merges, so the question it has to answer is how
often a 3.15 leg has warned over every run, PR runs included, since the last phase-2 fix landed. An informational
leg's check always concludes green; its `Report the informational Python 3.15 result` step's annotation is the
result: a `notice` ("every step passed on Python 3.15") or a `warning` naming the failed steps.

A PR run's warning may be the PR's own defect rather than a 3.15 problem: each warning is listed with its event,
branch and run so it can be read, not just counted.

Read-only: GET requests through `gh api`. Writes nothing.

Usage
-----
    python3 util/ad-hoc/2026-11-16_py315_leg_warning_history.py --since 2026-11-15T13:00:00Z [--repo <bare-name> ...]

Exit 0 when every request succeeded; 1 when any failed (each failure is printed, the rest still run).
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys
from collections import Counter

OWNER = "pcalnon"
REPOS = [
    "juniper-ml", "juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence", "juniper-deploy",
    "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-harcot",
]


def gh(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def runs_since(repo: str, since: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = gh(f"repos/{OWNER}/{repo}/actions/runs?created=>={since}&status=completed&per_page=100&page={page}")["workflow_runs"]
        out.extend(batch)
        if len(batch) < 100:
            return out
        page += 1


def classify(repo: str, job: dict) -> tuple[str, str]:
    # A cancelled job is classified FIRST: the report step runs under `if: always()`, sees the cancelled test
    # step's outcome `cancelled`, and posts a "step(s) failed" WARNING although nothing failed (measured on
    # juniper-ml run 43771172510, 2026-11-15T22:46Z: all four Regression Tests legs cancelled, the 3.15 one warned).
    if job.get("conclusion") in ("cancelled", "skipped"):
        return job["conclusion"], ""
    notes = gh(f"repos/{OWNER}/{repo}/check-runs/{job['id']}/annotations")
    for a in notes:
        title = a.get("title") or ""
        if "informational" in title and "3.15" in title:
            return a["annotation_level"], a.get("message", "")[:220]
    return "no-annotation", f"job conclusion {job.get('conclusion')}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", required=True, help="ISO-8601 UTC cutoff on the run's created_at, e.g. 2026-11-15T13:00:00Z")
    ap.add_argument("--repo", action="append", help="limit to these bare repo names")
    args = ap.parse_args()
    failed = False
    grand: Counter = Counter()
    for repo in args.repo or REPOS:
        try:
            runs = runs_since(repo, args.since)
        except RuntimeError as exc:
            print(f"!! {repo}: {exc}")
            failed = True
            continue
        tally: Counter = Counter()
        flagged: list[str] = []
        for run in runs:
            try:
                jobs = gh(f"repos/{OWNER}/{repo}/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
            except RuntimeError as exc:
                print(f"!! {repo} run {run['id']}: {exc}")
                failed = True
                continue
            for job in (j for j in jobs if "3.15" in j["name"]):
                try:
                    level, msg = classify(repo, job)
                except RuntimeError as exc:
                    print(f"!! {repo} job {job['id']}: {exc}")
                    failed = True
                    continue
                tally[level] += 1
                if level not in ("notice", "cancelled", "skipped"):
                    flagged.append(f"    {level}: run {run['id']} {run['created_at']} {run['event']} {run['head_branch']} {run['head_sha'][:8]} | {job['name'][:60]} | {msg}")
        grand.update(tally)
        print(f"=== {repo}: {len(runs)} completed runs since {args.since}; 3.15 jobs: {dict(tally) or 'none'}")
        for line in flagged:
            print(line)
    print(f"=== ALL: {dict(grand)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
