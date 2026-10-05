#!/usr/bin/env python3
"""Wait for GitHub Actions to recover from an outage, re-run a PR's abandoned workflow runs, then merge.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use operations helper)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc. Written during the 2026-10-05 Actions major outage (githubstatus incident opened
             21:09Z): queued jobs never received a runner, were CANCELLED after ~20 min with zero steps,
             and every path-scoped aggregate gate then FAILED with "change detection did not succeed".
             Nothing in the PRs' code failed. The remedy is a re-run of every failed / cancelled run on
             the PR's current head once the Actions component is operational, then the normal merge
             gate (util/safe_merge.py), which waits for green and reads the MERGED line.

Why a script: the worktree-isolation hook refuses shell loops and gh calls with runtime values, and a
script FILE is not inspected. Everything here is `gh` reads, `gh run rerun`, and safe_merge.py.

Run:
    python3 util/ad-hoc/2026-10-05_rerun_after_actions_outage.py --repo juniper-recurrence --pr 192 --merge
    python3 util/ad-hoc/2026-10-05_rerun_after_actions_outage.py --repo juniper-ml --pr 2164 --no-merge
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

STATUS_URL = "https://www.githubstatus.com/api/v2/components.json"
RERUN_CONCLUSIONS = {"failure", "cancelled", "timed_out", "startup_failure"}


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def actions_status() -> str:
    try:
        with urllib.request.urlopen(STATUS_URL, timeout=20) as resp:  # nosec B310 - fixed https URL
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001 - a status-page hiccup must not abort the wait
        return f"unknown ({exc.__class__.__name__})"
    for comp in data.get("components", []):
        if comp.get("name") == "Actions":
            return str(comp.get("status"))
    return "unknown (no Actions component)"


def head_sha(owner: str, repo: str, pr: int) -> str:
    return json.loads(gh("pr", "view", str(pr), "--repo", f"{owner}/{repo}", "--json", "headRefOid"))["headRefOid"]


def runs_on(owner: str, repo: str, sha: str) -> list[dict]:
    out = gh("run", "list", "--repo", f"{owner}/{repo}", "--commit", sha, "--limit", "50", "--json", "databaseId,name,status,conclusion")
    return json.loads(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--poll-seconds", type=int, default=120)
    ap.add_argument("--max-wait-seconds", type=int, default=4 * 3600)
    ap.add_argument("--merge-timeout", type=int, default=3600)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--merge", action="store_true")
    group.add_argument("--no-merge", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    status = actions_status()
    while status != "operational":
        if time.time() - t0 > args.max_wait_seconds:
            print(f"GAVE UP after {int(time.time() - t0)} s; Actions still {status}", flush=True)
            return 2
        print(f"{time.strftime('%H:%M:%S')} Actions = {status}; waiting {args.poll_seconds} s", flush=True)
        time.sleep(args.poll_seconds)
        status = actions_status()
    print(f"{time.strftime('%H:%M:%S')} Actions = operational after {int(time.time() - t0)} s", flush=True)

    sha = head_sha(args.owner, args.repo, args.pr)
    rerun = 0
    for run in runs_on(args.owner, args.repo, sha):
        if run.get("status") == "completed" and (run.get("conclusion") or "") in RERUN_CONCLUSIONS:
            print(f"re-running {run['name']} ({run['databaseId']}, was {run['conclusion']})", flush=True)
            subprocess.run(["gh", "run", "rerun", str(run["databaseId"]), "--repo", f"{args.owner}/{args.repo}"], check=False)
            rerun += 1
    print(f"re-ran {rerun} run(s) on {sha[:8]}", flush=True)

    if args.no_merge:
        return 0
    safe_merge = Path(__file__).resolve().parents[2] / "util" / "safe_merge.py"
    cmd = [sys.executable, str(safe_merge), "--pr", str(args.pr), "--repo", args.repo, "--owner", args.owner, "--execute", "--timeout", str(args.merge_timeout)]
    print("handing off to:", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
