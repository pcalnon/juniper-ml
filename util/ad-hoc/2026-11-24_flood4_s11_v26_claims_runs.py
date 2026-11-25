#!/usr/bin/env python3
"""
List a workflow's runs, and one step's outcome in each run's jobs, through read-only gh api GETs (V26 claims).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (checks the "latent" sentences of the ruling-26 PR texts: has the lockfile
        workflow ever run in a repository, and did its commit step ever run)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
For each repository given, GETs ``repos/<owner>/<repo>/actions/workflows/<file>/runs`` (every page), prints each
run (id, created_at, event, head_branch, status, conclusion, actor), then, with ``--step``, GETs each run's jobs and
prints the conclusion of every step whose name contains that text (``skipped`` means an ``if:`` gate skipped it).
GET requests only; nothing is mutated. Writes JSON to ``--out`` when given.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_runs.py --repo juniper-cascor-client --repo juniper-data-client \
        --workflow lockfile-update.yml --step "Commit updated lockfile" --out FILE.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

OWNER = "pcalnon"


def _get(path: str) -> dict:
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} exited {proc.returncode}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _runs(repo: str, workflow: str) -> tuple[int, list[dict]]:
    runs: list[dict] = []
    total = 0
    page = 1
    while True:
        data = _get(f"repos/{OWNER}/{repo}/actions/workflows/{workflow}/runs?per_page=100&page={page}")
        total = data.get("total_count", 0)
        batch = data.get("workflow_runs", [])
        runs.extend(batch)
        if not batch or len(runs) >= total:
            break
        page += 1
    return total, runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", action="append", required=True)
    parser.add_argument("--workflow", required=True, help="workflow file name, e.g. lockfile-update.yml")
    parser.add_argument("--step", default=None, help="substring of a step name whose per-run conclusion to print")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    record: dict[str, dict] = {}
    for repo in args.repo:
        total, runs = _runs(repo, args.workflow)
        print(f"== {repo}: {args.workflow}: total_count={total}")
        rows = []
        for run in runs:
            row = {
                "id": run["id"],
                "created_at": run["created_at"],
                "event": run["event"],
                "head_branch": run["head_branch"],
                "status": run["status"],
                "conclusion": run["conclusion"],
                "actor": (run.get("actor") or {}).get("login"),
                "steps": [],
            }
            if args.step:
                jobs = _get(f"repos/{OWNER}/{repo}/actions/runs/{run['id']}/jobs?per_page=100")
                for job in jobs.get("jobs", []):
                    for step in job.get("steps") or []:
                        if args.step in step.get("name", ""):
                            row["steps"].append({"job": job.get("name"), "step": step.get("name"), "conclusion": step.get("conclusion")})
            rows.append(row)
            steps = "; ".join(f"{s['step']}={s['conclusion']}" for s in row["steps"])
            print(f"  {row['id']}  {row['created_at']}  {row['event']:<12} {row['head_branch']}  {row['status']}/{row['conclusion']}  actor={row['actor']}  {steps}")
        record[repo] = {"total_count": total, "runs": rows}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
