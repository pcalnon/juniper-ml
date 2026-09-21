#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Block until a PR leaves OPEN, then print its terminal state and merge commit.

WHY: `util/safe_merge.py` arms a server-side auto-merge net and then waits. When the waiting
PROCESS is killed -- a timeout, a dropped session -- the net survives and GitHub still completes
the merge, but nothing is left watching to confirm it. This is the missing observer.

It reports the merge COMMIT, not the exit code. `safe_merge.py` can exit 0 without merging in
several shapes, so a receipt is the only acceptable evidence (see
memory/reference_safe_merge_exits_zero_without_merging.md).

It also prints CLOSED-without-merge distinctly, because a force-reset to base closes a PR and
that failure mode is easy to misread as success.

Usage: python3 2026-09-21_await_pr_merge.py <repo> <pr> [--timeout SECONDS] [--interval SECONDS]
"""

from __future__ import annotations

import json
import subprocess
import sys
import time


def view(repo: str, pr: str) -> dict:
    p = subprocess.run(
        ["gh", "pr", "view", pr, "--repo", f"pcalnon/{repo}",
         "--json", "state,mergedAt,mergeCommit,mergeStateStatus,autoMergeRequest"],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        return {}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    repo, pr = sys.argv[1], sys.argv[2]
    timeout = int(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 1500
    interval = int(sys.argv[sys.argv.index("--interval") + 1]) if "--interval" in sys.argv else 25

    deadline = time.time() + timeout
    while time.time() < deadline:
        d = view(repo, pr)
        state = d.get("state")
        if state and state != "OPEN":
            commit = (d.get("mergeCommit") or {}).get("oid", "")
            if state == "MERGED":
                print(f"MERGED {repo}#{pr} at {commit[:8]} ({d.get('mergedAt')})")
                return 0
            print(f"{state} {repo}#{pr} WITHOUT merging -- investigate, do not read as success")
            return 1
        time.sleep(interval)

    d = view(repo, pr)
    net = "ARMED" if d.get("autoMergeRequest") else "NONE"
    print(f"TIMEOUT after {timeout}s: {repo}#{pr} still OPEN "
          f"({d.get('mergeStateStatus')}), auto-merge net {net}")
    print("  net ARMED means GitHub will still merge on green; net NONE means nothing will.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
