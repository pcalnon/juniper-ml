#!/usr/bin/env python3
"""Survey every Juniper repo's latest Python 3.15 legs on `main`: which pass every step, which warn, and why.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-15
Status:      ad-hoc -- investigation (Python 3.15 migration arc, phase 2: what is left)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_py315_informational_green_legs.py (the report step whose annotations this reads)

Why this exists
---------------
Every informational 3.15 leg ends with a `Report the informational Python 3.15 result` step that posts a
`::notice` ("every step passed on Python 3.15") or a `::warning` naming the failed steps. A leg's check-run always
concludes green, so the conclusion says nothing; the annotation is the result. This reads, per repo and per
workflow, the latest `main` run that has a 3.15 job, and prints that job's annotation. Path-filtered workflows
(e.g. cascor's `ci-cascor-model.yml`) may have no run on `main`'s head, so it walks each workflow's own history.
Read-only: GET requests through `gh api`.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_leg_survey.py [--repo <bare-name> ...]

Exit 0 always (it reports); 1 only when a request fails.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys

OWNER = "pcalnon"
REPOS = [
    "juniper-ml", "juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence", "juniper-deploy",
    "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-harcot",
]


def gh(path: str) -> object:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", action="append", help="limit to these bare repo names")
    args = ap.parse_args()
    failed = False
    for repo in args.repo or REPOS:
        try:
            workflows = gh(f"repos/{OWNER}/{repo}/actions/workflows?per_page=100")["workflows"]
        except RuntimeError as exc:
            print(f"!! {repo}: {exc}")
            failed = True
            continue
        for wf in workflows:
            if wf.get("state") != "active":
                continue
            try:
                runs = gh(f"repos/{OWNER}/{repo}/actions/workflows/{wf['id']}/runs?branch=main&per_page=5&status=completed")["workflow_runs"]
            except RuntimeError:
                continue
            for run in runs:
                jobs = gh(f"repos/{OWNER}/{repo}/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
                legs = [j for j in jobs if "3.15" in j["name"]]
                if not legs:
                    continue
                for job in legs:
                    notes = gh(f"repos/{OWNER}/{repo}/check-runs/{job['id']}/annotations")
                    text = [f"{a['annotation_level']}: {a['message'][:150]}" for a in notes if "3.15" in a.get("message", "") or "Python 3" in a.get("title", "")]
                    print(f"{repo:22s} {wf['name'][:34]:34s} run {run['id']} ({run['head_sha'][:8]}, {run['created_at'][:10]} {run['event']}) {job['name'][:50]}")
                    print(f"      {job['conclusion']}: {' | '.join(text) if text else 'no 3.15 annotation'}")
                break
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
