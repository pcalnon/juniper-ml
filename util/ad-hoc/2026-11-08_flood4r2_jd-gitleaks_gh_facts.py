#!/usr/bin/env python3
"""
Read (GET only) the GitHub facts behind the juniper-data Gitleaks fix's wording about #370, #157 and the eight PRs #370 consolidated.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (round 2 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
The fix's texts must say what gitleaks-action's --first-parent walk cut from juniper-data's pull-request scans,
and must not claim the commits it cut were covered elsewhere when the covering scans ran with zero rules (before
2026-10-25). This gathers, read-only, each cited pull request's dates and state, #370's commit graph, the second
parent of #157's diverged merge, the Gitleaks lines of #370's last Security Scans job log, and each of the eight
consolidated pull requests' Security Scans check run. Every call is an explicit `gh api --method GET`.

Usage:
    python3 <this> --out <json>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: gh api --method GET
import sys
from pathlib import Path

REPO = "repos/pcalnon/juniper-data"
PRS = [370, 157, 337, 338, 341, 344, 346, 352, 356, 360]
CONSOLIDATED = [337, 338, 341, 344, 346, 352, 356, 360]
JOB_370 = 101319597180
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def get(path: str, jq: str | None = None) -> str:
    argv = ["gh", "api", "--method", "GET", path]
    if jq:
        argv += ["--jq", jq]
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"GET {path} failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
    return proc.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out: dict = {"prs": {}}
    for n in PRS:
        out["prs"][n] = json.loads(get(f"{REPO}/pulls/{n}", '{number, title, created_at, closed_at, merged_at, commits, base: .base.ref, head: .head.sha, merge_commit_sha}'))
    commits = json.loads(get(f"{REPO}/pulls/370/commits?per_page=100", "[.[] | {sha: .sha[0:8], parents: [.parents[].sha[0:8]], date: .commit.committer.date, subject: (.commit.message | split(\"\\n\")[0])}]"))
    out["pr370_commits"] = commits
    out["pr370_counts"] = {"commits": len(commits), "merges": sum(1 for c in commits if len(c["parents"]) > 1), "non_merge": sum(1 for c in commits if len(c["parents"]) == 1)}
    out["pr157_second_parent_f7ff9148"] = json.loads(get(f"{REPO}/commits/f7ff9148", '{sha: .sha[0:8], parents: [.parents[].sha[0:8]], subject: (.commit.message | split("\\n")[0])}'))
    log = ANSI.sub("", get(f"{REPO}/actions/jobs/{JOB_370}/logs"))
    out["pr370_job_log_lines"] = [line.split(" ", 1)[1] if line[:4].isdigit() else line for line in log.splitlines() if "gitleaks cmd" in line or "commits scanned" in line]
    out["consolidated_security_scans"] = {}
    for n in CONSOLIDATED:
        head = out["prs"][n]["head"]
        runs = json.loads(get(f"{REPO}/commits/{head}/check-runs?per_page=100", '[.check_runs[] | select(.name == "Security Scans") | {conclusion, started_at, id}]'))
        out["consolidated_security_scans"][n] = runs
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: out[k] for k in ("pr370_counts", "pr157_second_parent_f7ff9148", "pr370_job_log_lines")}, indent=1))
    for n in PRS:
        p = out["prs"][n]
        print(f"#{n} created={p['created_at']} closed={p['closed_at']} merged={p['merged_at']} commits={p['commits']} base={p['base']}")
    for n, runs in out["consolidated_security_scans"].items():
        print(f"#{n} Security Scans: {[(r['conclusion'], r['started_at']) for r in runs]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
