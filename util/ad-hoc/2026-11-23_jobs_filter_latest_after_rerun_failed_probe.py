#!/usr/bin/env python3
# =============================================================================
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  util/ad-hoc
# File Name:    2026-11-23_jobs_filter_latest_after_rerun_failed_probe.py
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Created:      2026-11-23
# Last Updated: 2026-11-23
#
# Status: ad-hoc -- one-off (one-artifact publish sweep, Overtoad ruling 1 of 2026-11-16, session e71d3e)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
#
# Description:
#   The Overtoad ruling 1 (2026-11-16) makes the republish job refuse unless the release run's TestPyPI job(s) concluded
#   success "in the latest attempt". The proposed mechanism is GET actions/runs/{id}/jobs?filter=latest. This probe
#   answers the open question: after "Re-run failed jobs", does filter=latest still list the jobs that attempt N+1
#   CARRIED OVER from attempt N (did not re-run), with their success conclusion?
#
#   It scans recent runs (read-only GETs) for runs with run_attempt > 1, and for each compares the job list of
#   filter=latest with filter=all and with the per-attempt endpoint. A run where some job of the latest set carries a
#   run_attempt lower than the run's own attempt is a "Re-run failed jobs" run whose carried jobs filter=latest DOES list.
#   A run where filter=latest lists fewer job NAMES than filter=all is one where carried jobs are missing.
#
# Usage:
#   python3 -I util/ad-hoc/2026-11-23_jobs_filter_latest_after_rerun_failed_probe.py --repo juniper-ml [--repo ...] [--pages 3]
# =============================================================================
"""Probe whether jobs?filter=latest lists jobs carried over by "Re-run failed jobs"."""

import argparse
import json
import subprocess
import sys


def gh(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def jobs(repo: str, run_id: int, filt: str) -> list[dict]:
    got: list[dict] = []
    page = 1
    while True:
        data = gh(f"repos/pcalnon/{repo}/actions/runs/{run_id}/jobs?filter={filt}&per_page=100&page={page}")
        got.extend(data["jobs"])
        if len(got) >= data["total_count"] or not data["jobs"]:
            return got
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", required=True, help="bare repo name, e.g. juniper-ml (repeatable)")
    ap.add_argument("--pages", type=int, default=3, help="pages of 100 recent runs to scan per repo")
    ap.add_argument("--max-runs", type=int, default=12, help="stop after this many re-run runs per repo")
    ap.add_argument("--created", default="", help="only runs created on this date or range (GitHub search syntax, e.g. 2026-11-08)")
    args = ap.parse_args()
    carried_seen = missing_seen = 0
    for repo in args.repo:
        examined = 0
        for page in range(1, args.pages + 1):
            created = f"&created={args.created}" if args.created else ""
            runs = gh(f"repos/pcalnon/{repo}/actions/runs?per_page=100&page={page}{created}")["workflow_runs"]
            if not runs:
                break
            for run in runs:
                if run["run_attempt"] < 2 or run["status"] != "completed":
                    continue
                latest = jobs(repo, run["id"], "latest")
                every = jobs(repo, run["id"], "all")
                carried = [j for j in latest if j.get("run_attempt", run["run_attempt"]) < run["run_attempt"]]
                names_latest = {j["name"] for j in latest}
                names_all = {j["name"] for j in every}
                lost = sorted(names_all - names_latest)
                # A job that "Re-run failed jobs" did not re-run keeps its earlier start time in the new attempt.
                prev = {j["name"]: j for j in gh(f"repos/pcalnon/{repo}/actions/runs/{run['id']}/attempts/{run['run_attempt'] - 1}/jobs?per_page=100")["jobs"]}
                kept = [j for j in latest if prev.get(j["name"], {}).get("started_at") == j["started_at"]]
                carried_seen += bool(carried or kept)
                missing_seen += bool(lost)
                print(f"{repo} run {run['id']} '{run['name']}' attempt={run['run_attempt']} event={run['event']} "
                      f"conclusion={run['conclusion']}: latest={len(latest)} all={len(every)} "
                      f"carried_in_latest={len(carried)} same_start_as_previous_attempt={len(kept)} names_missing_from_latest={lost}")
                for j in (carried or kept)[:4]:
                    print(f"    carried: '{j['name']}' id={j['id']} run_attempt={j.get('run_attempt')} conclusion={j['conclusion']}")
                examined += 1
                if examined >= args.max_runs:
                    break
            if examined >= args.max_runs:
                break
    print(f"runs with carried jobs listed by filter=latest: {carried_seen}; runs with job names missing from it: {missing_seen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
