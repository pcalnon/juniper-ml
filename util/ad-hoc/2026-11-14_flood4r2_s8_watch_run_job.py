#!/usr/bin/env python3
"""
Wait for one GitHub Actions run to complete, then save the log of each named job and print the lines matching the
given patterns (the "what the live run must show" reads of the flood-4 landings).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: post-merge reads of the ruling 10 ports and ruling 33)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

Why: a job's log is readable through the jobs API as soon as that job completes, but `gh run view --log` refuses
until the whole run has; and the evidence to read is a fixed list of lines per job. One read-only call replaces a
poll loop plus a grep per job, which this host's shell guard refuses as one command line.

Usage:
  2026-11-14_flood4r2_s8_watch_run_job.py --repo pcalnon/<repo> --run <run id> --job "<job name>" [--job ...]
      --pattern '<regex>' [--pattern ...] --out <dir> [--poll 30] [--timeout 3000]

Read-only: GET requests through `gh api` only. Exit 0 = the run completed and every job was found; 1 = a job was
not found or the wait timed out.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def gh_json(path: str) -> dict:
    done = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)  # nosec B603 B607 -- fixed argv, read-only GET
    return json.loads(done.stdout)


def gh_text(path: str) -> str:
    done = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)  # nosec B603 B607 -- fixed argv, read-only GET
    return done.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--job", action="append", required=True)
    parser.add_argument("--pattern", action="append", default=[])
    parser.add_argument("--out", required=True)
    parser.add_argument("--poll", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=3000)
    parser.add_argument("--jobs-only", action="store_true", help="stop waiting once every named job has completed, even if the run has not")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.timeout
    while True:
        run = gh_json(f"repos/{args.repo}/actions/runs/{args.run}")
        if run.get("status") == "completed":
            break
        if args.jobs_only:
            listed = gh_json(f"repos/{args.repo}/actions/runs/{args.run}/jobs?per_page=100").get("jobs", [])
            named = [j for j in listed if j.get("name") in args.job]
            if len(named) == len(args.job) and all(j.get("status") == "completed" for j in named):
                break
        if time.monotonic() > deadline:
            print(f"TIMEOUT: run {args.run} status={run.get('status')}")
            return 1
        time.sleep(args.poll)
    print(f"run {args.run}: {run.get('event')} {run.get('head_sha', '')[:8]} {run.get('name')} -> {run.get('status')} {run.get('conclusion')}")

    jobs = gh_json(f"repos/{args.repo}/actions/runs/{args.run}/jobs?per_page=100").get("jobs", [])
    patterns = [re.compile(p) for p in args.pattern]
    missing = 0
    for name in args.job:
        job = next((j for j in jobs if j.get("name") == name), None)
        if job is None:
            print(f"JOB NOT FOUND: {name!r}")
            missing += 1
            continue
        print(f"job {job['id']} {name!r}: {job.get('conclusion')}")
        for step in job.get("steps", []):
            print(f"   step {step.get('number')} {step.get('conclusion')} {step.get('name')}")
        text = gh_text(f"repos/{args.repo}/actions/jobs/{job['id']}/logs")
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
        (out / f"job_{job['id']}_{safe}.log").write_text(text, encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if any(p.search(line) for p in patterns):
                print(f"   l.{number}: {line[:220]}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
