#!/usr/bin/env python3
"""Block until a PR merges (or is closed unmerged), then exit. One notification, no shell loop.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1973

WHY A SCRIPT AND NOT A ONE-LINER. A worktree-isolated session refuses shell STRUCTURE -- `for`,
`while`, `until`, `&&` with a heredoc -- so the usual `until gh pr view ...; do sleep; done`
background wait cannot be run at all. The ecosystem rule points the same way: any script that
produces or analyses repository state lives under `util/ad-hoc/`, never `/tmp`, because `/tmp` is
reaped when the session ends.

WHY IT EXISTS AT ALL. `util/safe_merge.py` polls for required checks and merges when they are
green, but in a CONTENDED lane the PR goes BEHIND while it waits, safe_merge re-syncs, CI restarts
on the new head, and it can exhaust its budget and exit 0 WITHOUT having merged -- which is what
happened here twice ("went BEHIND while waiting -- re-syncing", then "auto-merge net disarmed").
Native auto-merge survives that, because GitHub evaluates it after each sync rather than polling.
This script just watches for the outcome.

EXIT CODES. 0 = merged. 1 = closed without merging. 2 = timed out still open.
Prints one terminal line either way, so silence never reads as success.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time


def poll(repo: str, pr: int) -> tuple[str, str]:
    """Return (state, merge_commit_sha). Never raises on a transient gh failure."""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls/{pr}", "--jq", "{merged: .merged, state: .state, sha: .merge_commit_sha}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if out.returncode != 0:
            return "transient", ""
        data = json.loads(out.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return "transient", ""

    if data.get("merged"):
        return "merged", (data.get("sha") or "")
    if data.get("state") == "closed":
        return "closed", ""
    return "open", ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--interval", type=int, default=45, help="seconds between polls (>=30 for a remote API)")
    parser.add_argument("--timeout", type=int, default=3000, help="give up after this many seconds")
    args = parser.parse_args()

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        state, sha = poll(args.repo, args.pr)
        if state == "merged":
            print(f"MERGED {args.repo}#{args.pr} squash {sha[:8]}")
            return 0
        if state == "closed":
            print(f"CLOSED-UNMERGED {args.repo}#{args.pr} -- it did NOT merge")
            return 1
        time.sleep(args.interval)

    print(f"TIMEOUT {args.repo}#{args.pr} still open after {args.timeout}s -- NOT merged")
    return 2


if __name__ == "__main__":
    sys.exit(main())
