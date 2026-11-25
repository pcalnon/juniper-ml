#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_land_d14_pair.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-11-23
# Last Modified: 2026-11-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     Flood-4 session 10 (owner's merge approval of 2026-11-23 for this arc). Land the D-14 pair in order:
#     juniper-cascor#776, then juniper-ml#2618. For each PR: wait until CodeQL has analysed the CURRENT head of
#     refs/pull/N/merge; resolve an unresolved github-advanced-security review thread ONLY when its alert's instance on
#     that ref reads "fixed" (resolving before the fix is confirmed would be dishonest; CodeQL never resolves its own
#     thread); stop if any such thread's alert is still open; then run util/safe_merge.py --execute and require its
#     "MERGED #N" line. #2618 is marked ready only after #776 has merged. Prints one line per event, UTC-stamped.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_land_d14_pair.py [--poll 60] [--max-wait 3600]
#####################################################################################################################################################################################################
"""Land juniper-cascor#776 then juniper-ml#2618, resolving only CodeQL threads whose alert is fixed."""

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import time

OWNER = "pcalnon"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAFE_MERGE = os.path.join(ROOT, "util", "safe_merge.py")
ALERT_RE = re.compile(r"/security/code-scanning/(\d+)")


def log(msg):
    print(f"[{_dt.datetime.now(_dt.timezone.utc).strftime('%H:%M:%SZ')}] {msg}", flush=True)


def gh_json(*args):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)[:120]} failed: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def head_sha(repo, number):
    return gh_json("api", f"repos/{OWNER}/{repo}/pulls/{number}")["head"]["sha"]


def codeql_done(repo, sha):
    runs = gh_json("api", f"repos/{OWNER}/{repo}/commits/{sha}/check-runs?per_page=100")["check_runs"]
    codeql = [r for r in runs if r["name"].lower().startswith(("analyze", "codeql"))]
    return bool(codeql) and all(r["status"] == "completed" for r in codeql), [(r["name"], r["status"], r["conclusion"]) for r in codeql]


def threads(repo, number):
    query = "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{id isResolved comments(first:1){nodes{author{login} body path}}}}}}}"
    data = gh_json("api", "graphql", "-f", f"query={query}", "-F", f"o={OWNER}", "-F", f"r={repo}", "-F", f"n={number}")
    return data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]


def alert_state_on_pr(repo, alert, number):
    instances = gh_json("api", f"repos/{OWNER}/{repo}/code-scanning/alerts/{alert}/instances?ref=refs/pull/{number}/merge")
    return instances[0]["state"] if instances else "no-instance"


def settle_threads(repo, number):
    """Resolve fixed CodeQL threads; return False if an unresolved thread is not a fixed CodeQL alert."""
    clean = True
    for node in threads(repo, number):
        if node["isResolved"]:
            continue
        first = node["comments"]["nodes"][0]
        author, body = first["author"]["login"], first["body"]
        match = ALERT_RE.search(body)
        if not author.startswith("github-advanced-security") or not match:
            log(f"{repo}#{number}: unresolved thread by {author} on {first.get('path')} is not a CodeQL alert -> STOP")
            clean = False
            continue
        state = alert_state_on_pr(repo, match.group(1), number)
        if state != "fixed":
            log(f"{repo}#{number}: CodeQL alert {match.group(1)} on {first.get('path')} is '{state}' on the PR ref -> STOP (not resolving)")
            clean = False
            continue
        gh_json("api", "graphql", "-f", "query=mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}", "-F", f"t={node['id']}")
        log(f"{repo}#{number}: alert {match.group(1)} reads 'fixed' on refs/pull/{number}/merge -> thread resolved")
    return clean


def wait_codeql(repo, number, poll, max_wait):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        sha = head_sha(repo, number)
        done, runs = codeql_done(repo, sha)
        if done:
            log(f"{repo}#{number}: CodeQL complete on head {sha[:8]}: {runs}")
            return True
        time.sleep(poll)
    log(f"{repo}#{number}: CodeQL not complete within {max_wait}s -> STOP")
    return False


def merge(repo, number):
    proc = subprocess.run([sys.executable, SAFE_MERGE, "--repo", repo, "--pr", str(number), "--merge-method", "squash", "--execute"], capture_output=True, text=True, check=False)
    out = (proc.stdout + proc.stderr).strip().splitlines()
    for line in out[-6:]:
        log(f"  safe_merge: {line[:200]}")
    return any(line.startswith(f"MERGED #{number}") for line in out)


def land(repo, number, poll, max_wait):
    if not wait_codeql(repo, number, poll, max_wait):
        return False
    time.sleep(30)  # let the code-scanning results settle onto the alert instances
    if not settle_threads(repo, number):
        return False
    if not merge(repo, number):
        log(f"{repo}#{number}: NOT merged (see safe_merge lines) -> STOP")
        return False
    pr = gh_json("api", f"repos/{OWNER}/{repo}/pulls/{number}")
    log(f"{repo}#{number}: MERGED as {pr['merge_commit_sha']}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll", type=int, default=60)
    parser.add_argument("--max-wait", type=int, default=3600)
    args = parser.parse_args(argv)
    if not land("juniper-cascor", 776, args.poll, args.max_wait):
        return 1
    subprocess.run(["gh", "pr", "ready", "2618", "--repo", f"{OWNER}/juniper-ml"], check=False)
    log("juniper-ml#2618: marked ready")
    time.sleep(60)
    return 0 if land("juniper-ml", 2618, args.poll, args.max_wait) else 1


if __name__ == "__main__":
    sys.exit(main())
