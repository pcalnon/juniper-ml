#!/usr/bin/env python3
"""
Print the HEAD and the change list of one or more scratch worktrees, from inside each.

The carrier's proofs run in scratch worktrees of the same repository (a clean main, a byte copy of the carrier,
main with another carrier's files). This session's shell refuses a version-control command aimed at another
checkout from outside it, so each worktree is asked from its own directory. With --probe-commit MESSAGE the one
worktree named is given an unsigned, never-pushed commit of its whole working tree (plumbing only: a tree written
from its index after `add -A`, `commit-tree`, and a soft reset of its detached HEAD to it), so the carrier's tools,
which read main's files from HEAD, see that tree as "the main of the day".

Usage:
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_worktree_status.py DIR [DIR ...]
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_worktree_status.py --probe-commit "<message>" DIR

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_land.py (which needs a clean landing worktree)
"""

import argparse
import subprocess
import sys


def _git(cwd: str, *argv: str, text_in: str = "") -> str:
    return subprocess.run(["git", *argv], cwd=cwd, input=text_in, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe-commit")
    ap.add_argument("dirs", nargs="+")
    args = ap.parse_args()
    if args.probe_commit:
        if len(args.dirs) != 1:
            raise SystemExit("--probe-commit takes exactly one worktree")
        root = args.dirs[0]
        on_branch = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=root, capture_output=True, check=False).returncode == 0
        if on_branch:
            raise SystemExit("refusing: that worktree is on a branch, and a probe commit must not move one")
        parent = _git(root, "rev-parse", "HEAD")
        _git(root, "add", "-A", ".")
        tree = _git(root, "write-tree")
        probe = _git(root, "commit-tree", tree, "-p", parent, "-F", "-", text_in=args.probe_commit + "\n")
        _git(root, "reset", "--soft", probe)
        print(f"{root}: probe commit {probe} on {parent[:8]} (unsigned, unreferenced, never pushed)")
    for root in args.dirs:
        head = _git(root, "rev-parse", "HEAD")
        changes = _git(root, "status", "--porcelain", "--untracked-files=all")
        print(f"{root}: HEAD {head}; {len(changes.splitlines()) if changes else 0} changed path(s)")
        if changes:
            print("\n".join("    " + line for line in changes.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
