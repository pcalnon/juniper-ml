#!/usr/bin/env python3
"""Keep an ARMED auto-merge PR current with a busy ``main`` until it merges (strict ruleset).

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc merge-lane helper
Author:      Paul Calnon
Created:     2026-09-23
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-ml#2040, the 0.10.0 CHANGELOG fold)

Why this exists
---------------
Under a ``strict: true`` ruleset an armed auto-merge on a BEHIND PR waits forever, and every
``update-branch`` restarts CI (~10-15 min on a contended runner pool). juniper-ml#2040 went
green-but-BEHIND three times in a row on 2026-09-23 as ~20 concurrent sessions merged into
``main``. Waiting for each doomed run to finish before updating wastes its remaining minutes. This
watcher updates the branch the moment it goes BEHIND, so every CI minute is spent on a head that
can still merge.

It never merges, never arms, never re-arms: auto-merge stays the owner-granted mechanism. It exits
0 on MERGED; 2 closed; 3 auto-merge disarmed (a failed ``gh pr merge`` disarms it silently -- say so
rather than re-arm); 4 conflict (DIRTY -- a human must look); 1 timeout.

Usage
-----
    python3 util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py --pr 2040 [--repo juniper-ml] [--timeout 5400]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - gh CLI only, fixed argv
import time

_QUERY = "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){state mergeStateStatus headRefOid autoMergeRequest{enabledAt}}}}"


def _state(owner: str, repo: str, pr: int) -> dict:
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={_QUERY}", "-F", f"o={owner}", "-F", f"r={repo}", "-F", f"n={pr}"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607
    return json.loads(out)["data"]["repository"]["pullRequest"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--repo", default="juniper-ml")
    ap.add_argument("--owner", default="pcalnon")
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--interval", type=int, default=30)
    args = ap.parse_args()

    deadline = time.monotonic() + args.timeout
    updates = 0
    while time.monotonic() < deadline:
        try:
            pr = _state(args.owner, args.repo, args.pr)
        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as exc:
            print(f"transient read failure ({exc.__class__.__name__}); retrying", flush=True)
            time.sleep(args.interval)
            continue
        state, merge_state, head = pr["state"], pr["mergeStateStatus"], pr["headRefOid"]
        if state == "MERGED":
            print(f"MERGED after {updates} update-branch call(s)", flush=True)
            return 0
        if state == "CLOSED":
            print("CLOSED without merging", flush=True)
            return 2
        if pr["autoMergeRequest"] is None:
            print("auto-merge is DISARMED -- not re-arming; a human decides", flush=True)
            return 3
        if merge_state == "DIRTY":
            print("merge conflict (DIRTY) -- a human must resolve it", flush=True)
            return 4
        if merge_state == "BEHIND":
            res = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{args.owner}/{args.repo}/pulls/{args.pr}/update-branch", "-f", f"expected_head_sha={head}"], capture_output=True, text=True)  # nosec B603 B607
            updates += 1
            print(f"BEHIND at {head[:8]} -> update-branch #{updates}: {(res.stdout or res.stderr).strip()[:120]}", flush=True)
        time.sleep(args.interval)
    print(f"TIMEOUT after {args.timeout}s and {updates} update-branch call(s)", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
