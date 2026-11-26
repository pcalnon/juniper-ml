#!/usr/bin/env python3
"""
Would a sibling PR's branch, with this worktree's uncommitted fix on top, merge cleanly into origin/main? Build it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout, copy 2 (juniper-data-client#273 after #274 moved main)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-26_probe_sequence_safety_screens.py (the same throwaway-index probe commit)

Fetches ``origin main`` and ``origin <branch>`` in ``--checkout``. ``--as-is`` merges the remote branch tip as it is;
otherwise a probe commit is built from the checkout's working tree (through a throwaway index under ``--work``) on
top of the remote branch tip, the way util/push_signed_commit.py would add it. Then ``git merge-tree --write-tree``
merges it with origin/main and prints the conflicts, or "clean". With ``--materialize DIR`` a clean merge becomes a
commit (parents: origin/main, the probe) checked out detached at DIR, to test exactly what would merge. No ref moves.

Exit: 0 clean, 1 conflicts, 2 setup error.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 - git with a fixed argv
import sys
from pathlib import Path


def git(checkout: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=checkout, env=env, capture_output=True, text=True, check=False)  # nosec B603 B607


def must(proc: subprocess.CompletedProcess, what: str) -> str:
    if proc.returncode != 0:
        sys.stderr.write(f"{what} failed ({proc.returncode}): {proc.stderr}{proc.stdout}")
        raise SystemExit(2)
    return proc.stdout.strip()


def remove(checkout: Path, target: Path) -> int:
    """Remove a materialized probe: only a detached, clean worktree of this repo whose tmp/ is empty (retention rule)."""
    listed = git(checkout, "worktree", "list", "--porcelain").stdout
    if f"worktree {target}\n" not in listed:
        raise SystemExit(f"refusing: {target} is not a worktree of {checkout}")
    block = listed.split(f"worktree {target}\n", 1)[1].split("\n\n", 1)[0]
    if "detached" not in block.split("\n"):
        raise SystemExit(f"refusing: {target} is on a branch, not a detached probe")
    if git(target, "status", "--porcelain").stdout.strip():
        raise SystemExit(f"refusing: {target} has changes")
    if (target / "tmp").is_dir() and any((target / "tmp").iterdir()):
        raise SystemExit(f"refusing: {target / 'tmp'} is not empty (retention rule: keep or archive it first)")
    must(git(checkout, "worktree", "remove", "--force", str(target)), "worktree remove")  # --force: the ignored, empty tmp/
    must(git(checkout, "worktree", "prune"), "worktree prune")
    print(f"removed {target}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--branch", required=False, default="")
    parser.add_argument("--work", type=Path, default=Path("."))
    parser.add_argument("--as-is", action="store_true", help="merge the remote branch tip, not the working tree")
    parser.add_argument("--materialize", type=Path, metavar="DIR", help="check a clean merge out, detached, at DIR")
    parser.add_argument("--remove", type=Path, metavar="DIR", help="instead: remove a materialized probe at DIR")
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    if args.remove:
        return remove(checkout, args.remove.resolve())
    if not args.branch:
        parser.error("--branch is required")
    args.work.mkdir(parents=True, exist_ok=True)
    must(git(checkout, "fetch", "--quiet", "origin", "main", args.branch), "git fetch")
    main_sha = must(git(checkout, "rev-parse", "origin/main"), "rev-parse origin/main")
    tip = must(git(checkout, "rev-parse", f"origin/{args.branch}"), f"rev-parse origin/{args.branch}")
    head = tip
    env = {key: value for key, value in os.environ.items() if key not in ("GIT_DIR", "GIT_WORK_TREE")}
    env.update(GIT_INDEX_FILE=str(args.work.resolve() / "merge-probe.index"), GIT_AUTHOR_NAME="probe", GIT_AUTHOR_EMAIL="probe@example.invalid", GIT_COMMITTER_NAME="probe", GIT_COMMITTER_EMAIL="probe@example.invalid")
    if not args.as_is:
        must(git(checkout, "read-tree", tip, env=env), "read-tree")
        must(git(checkout, "add", "-A", env=env), "add -A")
        tree = must(git(checkout, "write-tree", env=env), "write-tree")
        head = must(git(checkout, "commit-tree", tree, "-p", tip, "-m", "probe: the working tree on the branch tip, never pushed", env=env), "commit-tree")
        print(f"probe {head[:12]} = the working tree on origin/{args.branch} {tip[:12]}; changed vs the tip:")
        print(git(checkout, "diff", "--stat", tip, head).stdout.rstrip() or "  (nothing)")
    base = must(git(checkout, "merge-base", main_sha, head), "merge-base")
    print(f"origin/main {main_sha[:12]}  head {head[:12]}  merge base {base[:12]}")
    merged = git(checkout, "merge-tree", "--write-tree", "--name-only", main_sha, head)
    lines = merged.stdout.splitlines()
    if merged.returncode == 1:
        print("CONFLICTS:")
        print("\n".join(f"  {line}" for line in lines[1:] if line.strip()))
        return 1
    tree = must(merged, "merge-tree").splitlines()[0]
    print(f"clean: merged tree {tree[:12]}")
    if args.materialize:
        commit = must(git(checkout, "commit-tree", tree, "-p", main_sha, "-p", head, "-m", "probe: the PR merged into origin/main, never pushed", env=env), "commit-tree (merge)")
        must(git(checkout, "worktree", "add", "--detach", str(args.materialize.resolve()), commit), "worktree add")
        print(f"materialized {commit[:12]} at {args.materialize.resolve()} (detached; remove with git worktree remove)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
