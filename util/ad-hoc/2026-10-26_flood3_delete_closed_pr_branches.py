#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_flood3_delete_closed_pr_branches.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Deletes the leftover `cursor/*` head branches of CLOSED Cursor flood-3 PRs
#   (owner ruling 2026-10-26: "Delete flood-3's only"). The PR set is
#   util/ad-hoc/2026-10-08_fleet_flood3_disposition.json (116 PRs). A branch is
#   deleted only when every guard holds:
#     - the PR is closed and was NOT merged (a merged PR's branch is reported, not touched);
#     - its head lives in the same repository (not a fork) and is named `cursor/*`;
#     - the branch still exists and its tip equals the PR's final head SHA
#       (a branch that moved after the close carries something the PR never had);
#     - no OPEN PR uses that branch as its head.
#   Every deletion is appended to a TSV (repo, pr, branch, sha) so a branch can be
#   restored: GitHub's "Restore branch" on the PR page, or
#   `gh api -X POST repos/pcalnon/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<sha>`.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-26_flood3_delete_closed_pr_branches.py \
#       --disposition util/ad-hoc/2026-10-08_fleet_flood3_disposition.json \
#       --log <tsv> [--execute]
#   Without --execute it only reports what it would delete.
#
# Exit codes: 0 done; 1 a guard refused some branch (reported); 2 usage/API error.
# -----------------------------------------------------------------------------
"""Delete the leftover cursor/* head branches of closed, unmerged flood-3 PRs, behind guards."""

import argparse
import json
import subprocess
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

OWNER = "pcalnon"


def gh_json(path: str, method: str = "GET"):
    """Call the GitHub API through gh; return (status_ok, parsed JSON or None)."""
    proc = subprocess.run(["gh", "api", "-X", method, path], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, (json.loads(proc.stdout) if proc.stdout.strip() else None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--disposition", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True, help="TSV of deleted refs (appended)")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    prs = json.loads(args.disposition.read_text())["prs"]
    tally: Counter = Counter()
    refused = 0
    for row in prs:
        repo, n = row["repo"], row["pr"]
        ok, pr = gh_json(f"repos/{OWNER}/{repo}/pulls/{n}")
        if not ok:
            print(f"ERROR   {repo}#{n}: {pr}")
            return 2
        ref, sha = pr["head"]["ref"], pr["head"]["sha"]
        head_repo = (pr["head"].get("repo") or {}).get("full_name")
        if pr["state"] != "closed":
            tally["open-pr"] += 1
            print(f"SKIP    {repo}#{n} {ref}: PR is {pr['state']}")
            continue
        if not ref.startswith("cursor/") or head_repo != f"{OWNER}/{repo}":
            tally["not-cursor-or-fork"] += 1
            continue
        quoted = urllib.parse.quote(ref, safe="/")
        ok, live = gh_json(f"repos/{OWNER}/{repo}/git/ref/heads/{quoted}")
        if not ok:
            tally["already-gone"] += 1
            continue
        if pr.get("merged_at"):
            tally["merged-branch-left"] += 1
            print(f"REPORT  {repo}#{n} {ref}: merged PR, branch still exists (not touched)")
            continue
        tip = live["object"]["sha"]
        if tip != sha:
            refused += 1
            tally["moved-after-close"] += 1
            print(f"REFUSE  {repo}#{n} {ref}: tip {tip[:8]} != PR head {sha[:8]}")
            continue
        ok, users = gh_json(f"repos/{OWNER}/{repo}/pulls?state=open&head={OWNER}:{urllib.parse.quote(ref, safe='')}")
        if not ok or users:
            refused += 1
            tally["open-pr-uses-branch"] += 1
            print(f"REFUSE  {repo}#{n} {ref}: an open PR uses this branch, or the check failed")
            continue
        if not args.execute:
            tally["would-delete"] += 1
            print(f"WOULD   {repo}#{n} {ref} @ {tip[:8]}")
            continue
        ok, err = gh_json(f"repos/{OWNER}/{repo}/git/refs/heads/{quoted}", method="DELETE")
        if not ok:
            refused += 1
            tally["delete-failed"] += 1
            print(f"FAILED  {repo}#{n} {ref}: {err}")
            continue
        with args.log.open("a", encoding="utf-8") as fh:
            fh.write(f"{repo}\t{n}\t{ref}\t{tip}\n")
        tally[f"deleted:{repo}"] += 1
        tally["deleted"] += 1
        print(f"DELETED {repo}#{n} {ref} @ {tip[:8]}")
    print("TALLY", dict(sorted(tally.items())))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
