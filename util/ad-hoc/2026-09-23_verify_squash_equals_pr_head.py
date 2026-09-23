#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# File Name:     2026-09-23_verify_squash_equals_pr_head.py
# Description:   For each merged PR, confirm the squash commit's TREE equals the PR
#                head's tree -- i.e. nothing was dropped or added at merge time.
#                Under a strict ruleset the head must be up to date with main when it
#                merges, so the two trees must be identical; a non-empty diff means
#                the squash shipped something the reviewed head did not carry.
#
# Usage:         python3 2026-09-23_verify_squash_equals_pr_head.py \
#                    --repo pcalnon/juniper-canopy --clone <local clone> 668 669 667
#
# Exit:          0 all equal, 1 any differs / unmerged / unfetchable.
# -----------------------------------------------------------------------------
import argparse
import json
import subprocess
import sys


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--clone", required=True, help="local clone of --repo (fetch-only use)")
    ap.add_argument("prs", nargs="+", type=int)
    a = ap.parse_args()

    run(["git", "fetch", "origin", "--quiet"], cwd=a.clone)
    bad = 0
    for n in a.prs:
        meta = json.loads(run(["gh", "pr", "view", str(n), "--repo", a.repo, "--json", "state,headRefOid,mergeCommit,mergedAt"]).stdout)
        head = meta["headRefOid"]
        squash = (meta.get("mergeCommit") or {}).get("oid")
        if meta["state"] != "MERGED" or not squash:
            print(f"#{n}: NOT MERGED (state={meta['state']})")
            bad += 1
            continue
        if run(["git", "cat-file", "-e", head], cwd=a.clone, check=False).returncode != 0:
            run(["git", "fetch", "origin", head, "--quiet"], cwd=a.clone, check=False)
        if run(["git", "cat-file", "-e", head], cwd=a.clone, check=False).returncode != 0:
            print(f"#{n}: head {head[:8]} NOT FETCHABLE")
            bad += 1
            continue
        stat = run(["git", "diff", "--stat", head, squash], cwd=a.clone).stdout.strip()
        tree_h = run(["git", "rev-parse", f"{head}^{{tree}}"], cwd=a.clone).stdout.strip()
        tree_s = run(["git", "rev-parse", f"{squash}^{{tree}}"], cwd=a.clone).stdout.strip()
        verdict = "EQUAL" if tree_h == tree_s else "DIFFERS"
        if verdict != "EQUAL":
            bad += 1
        print(f"#{n}: head={head[:8]} squash={squash[:8]} merged={meta['mergedAt']} tree {verdict}")
        if stat:
            print("    " + stat.replace("\n", "\n    "))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
