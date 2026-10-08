#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. Read-only git inspection of fleet PR branches in a sibling repo:
# own commits, merge-base, behind count, and what landing the PR head on origin/main
# would actually change (git merge-tree --write-tree, never a merge-base diff).
# It never writes refs, never commits, never touches GitHub.
"""Per-PR true-delta report for fleet PR branches in one repo.

Usage:
    2026-10-08_flood3_clients_eval_git.py <repo-path> <ref> [<ref> ...]

Each <ref> is a commit-ish (e.g. origin/cursor/foo). For each it prints the commits
not on origin/main, the merge-base, how far main has moved past that base, the
merge-tree verdict (clean / conflicted paths), and the --stat of origin/main -> merged tree.
"""
import subprocess
import sys


def git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    repo = argv[1]
    main_sha = git(repo, "rev-parse", "origin/main").stdout.strip()
    print(f"origin/main = {main_sha[:10]}")
    for ref in argv[2:]:
        print(f"\n===== {ref}")
        head = git(repo, "rev-parse", ref).stdout.strip()
        print(f"head        = {head[:10]}")
        own = git(repo, "log", "--format=%h %G? %s", f"origin/main..{head}").stdout.strip()
        print("own commits (not on origin/main):")
        print("  " + own.replace("\n", "\n  ") if own else "  (none)")
        base = git(repo, "merge-base", "origin/main", head).stdout.strip()
        behind = git(repo, "rev-list", "--count", f"{base}..origin/main").stdout.strip()
        print(f"merge-base  = {base[:10]}  (main is {behind} commit(s) past it)")
        mt = git(repo, "merge-tree", "--write-tree", "--name-only", "origin/main", head, check=False)
        lines = mt.stdout.strip().splitlines()
        tree = lines[0] if lines else ""
        if mt.returncode == 0:
            print(f"merge-tree  = CLEAN (tree {tree[:10]})")
        elif mt.returncode == 1:
            conflicted = [ln for ln in lines[1:] if ln and not ln.startswith("Auto-merging") and not ln.startswith("CONFLICT")]
            print(f"merge-tree  = CONFLICTED (tree {tree[:10]}); paths: {sorted(set(conflicted))}")
            for ln in lines[1:]:
                if ln.startswith("CONFLICT"):
                    print(f"  {ln}")
        else:
            print(f"merge-tree  = ERROR rc={mt.returncode}: {mt.stderr.strip()}")
            continue
        stat = git(repo, "diff", "--stat=200", "origin/main", tree).stdout.rstrip()
        print("landing would change (origin/main -> merged tree):")
        print("  " + stat.replace("\n", "\n  ") if stat else "  (nothing)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
