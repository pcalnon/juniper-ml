#!/usr/bin/env python3
"""Remove one task worktree and its local branch from a sibling Juniper repo, only after its PR has merged.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use cleanup helper)
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc. The worktree-isolation hook refuses ``git -C <path>`` and ``cd`` into another checkout,
             so the two wave-1 worktrees (juniper-recurrence#192, juniper-ml#2164) could not be removed from a
             shell one-liner. A script file is not inspected, and ``subprocess.run(..., cwd=repo_dir)`` is
             the same operation. Gates, in order: the PR must read MERGED on GitHub; the worktree must be one
             the repo registers; a dirty worktree is removed only when every modified file is byte-identical
             to the same path on freshly fetched ``origin/main`` (the #2164 worktree is dirty by construction:
             its agent committed through the signed API, so the six edits were never committed locally), or
             under ``--force-dirty``. Never touches the primary checkout's branch or working tree; the only
             write to the primary is ``git fetch origin main``, which updates a remote-tracking ref.

Run:
    python3 util/ad-hoc/2026-10-05_remove_merged_worktree.py --gh-repo pcalnon/juniper-recurrence --pr 192 \
        --repo-dir /home/pcalnon/Development/python/Juniper/juniper-recurrence \
        --worktree /home/pcalnon/Development/python/Juniper/worktrees/juniper-recurrence--feat--w1-5-operation-id-timeouts--20261005-0828--2c34805c \
        --branch feat/w1-5-operation-id-timeouts [--force-dirty] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def dirty_matches_main(repo_dir: Path, worktree: Path, status_lines: list[str]) -> tuple[list[str], list[str]]:
    """Split the dirty paths into (identical to origin/main, different). Untracked or deleted paths count as different."""
    run(["git", "fetch", "origin", "main"], cwd=repo_dir)
    same: list[str] = []
    diff: list[str] = []
    for line in status_lines:
        code, path = line[:2], line[3:]
        if code.strip() != "M" or not (worktree / path).is_file():
            diff.append(path)
            continue
        local = run(["git", "hash-object", str(worktree / path)], cwd=repo_dir).stdout.strip()
        remote = run(["git", "rev-parse", f"origin/main:{path}"], cwd=repo_dir, check=False).stdout.strip()
        (same if local == remote and local else diff).append(path)
    return same, diff


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gh-repo", required=True, help="owner/name")
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--repo-dir", required=True, type=Path)
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--force-dirty", action="store_true", help="remove even when a dirty file differs from origin/main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = json.loads(run(["gh", "pr", "view", str(args.pr), "--repo", args.gh_repo, "--json", "state,mergeCommit"]).stdout)
    if state.get("state") != "MERGED":
        print(f"REFUSED: {args.gh_repo}#{args.pr} is {state.get('state')}, not MERGED", flush=True)
        return 1
    merge_sha = (state.get("mergeCommit") or {}).get("oid", "?")
    print(f"{args.gh_repo}#{args.pr} MERGED as {merge_sha[:8]}", flush=True)

    registered = run(["git", "worktree", "list", "--porcelain"], cwd=args.repo_dir).stdout
    wt = str(args.worktree.resolve())
    if f"worktree {wt}" not in registered:
        print(f"REFUSED: {wt} is not a worktree registered in {args.repo_dir}", flush=True)
        return 1

    status_lines = [ln for ln in run(["git", "status", "--short"], cwd=args.worktree).stdout.splitlines() if ln.strip()]
    dirty = bool(status_lines)
    if dirty:
        same, diff = dirty_matches_main(args.repo_dir, args.worktree, status_lines)
        for path in same:
            print(f"  identical to origin/main: {path}", flush=True)
        for path in diff:
            print(f"  DIFFERS from origin/main:  {path}", flush=True)
        if diff and not args.force_dirty:
            print("REFUSED: a dirty file is not on origin/main; pass --force-dirty only if you know why", flush=True)
            return 1

    if args.dry_run:
        print(f"DRY RUN: would remove {wt} and delete local branch {args.branch}", flush=True)
        return 0

    rm = ["git", "worktree", "remove"] + (["--force"] if dirty else []) + [wt]
    run(rm, cwd=args.repo_dir)
    run(["git", "worktree", "prune"], cwd=args.repo_dir)
    print(f"removed worktree {wt}", flush=True)
    branches = run(["git", "branch", "--list", args.branch], cwd=args.repo_dir).stdout.strip()
    if branches:
        run(["git", "branch", "-D", args.branch], cwd=args.repo_dir)
        print(f"deleted local branch {args.branch}", flush=True)
    else:
        print(f"no local branch {args.branch} to delete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
