#!/usr/bin/env python3
"""
Replicate juniper-cascor's two required Sequence Safety screens on an uncommitted working tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor .github/workflows/sequence-safety.yml (juniper-ci-tools console scripts)

Builds a DANGLING, unsigned probe commit of the working tree (tracked changes plus untracked,
non-ignored files) with a temporary index file and ``git commit-tree``: HEAD, the branch, the
real index and the working tree are never touched, and nothing is pushed. Then runs
``juniper-symbol-loss-check --scope 'src/**/*.py'`` and ``juniper-docs-additions-check`` (its
default docs cluster) from BASE to that commit, as the workflow does.

Usage:
  2026-11-09_flood4r2_r17-cascor_sequence_safety.py --tree <checkout> --base <ref> --bin <dir holding the console scripts> --index <temp index path>
Exit: 0 when both screens exit 0; 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404 -- fixed-argv git and screen runs
import sys
from pathlib import Path


def _git(tree: Path, env: dict, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(tree), *args], capture_output=True, text=True, env=env, check=True)  # nosec B603 B607 -- fixed argv
    return proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--bin", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path, help="a temporary index file path (deleted afterwards)")
    args = parser.parse_args()
    tree = args.tree.resolve()
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str(args.index.resolve())
    try:
        _git(tree, env, "read-tree", "HEAD")
        _git(tree, env, "add", "-A")
        tree_sha = _git(tree, env, "write-tree")
        head = _git(tree, env, "rev-parse", "HEAD")
        probe = _git(tree, env, "-c", "commit.gpgsign=false", "commit-tree", tree_sha, "-p", head, "-m", "probe: r17 stop-then-start (dangling, never pushed)")
        changed = _git(tree, env, "diff", "--name-status", args.base, probe)
    finally:
        if args.index.exists():
            args.index.unlink()
    print(f"probe commit {probe} (tree {tree_sha}, parent {head}); not on any branch")
    print(f"changed vs {args.base}:\n{changed}")
    plain = {k: v for k, v in os.environ.items() if k != "GIT_INDEX_FILE"}
    codes = []
    for argv in (
        [str(args.bin / "juniper-symbol-loss-check"), "--base", args.base, "--head", probe, "--repo-root", str(tree), "--scope", "src/**/*.py"],
        [str(args.bin / "juniper-docs-additions-check"), "--base", args.base, "--head", probe, "--repo-root", str(tree)],
    ):
        print(f"\n$ {' '.join(argv)}", flush=True)
        proc = subprocess.run(argv, cwd=tree, env=plain, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
        print(proc.stdout + proc.stderr)
        print(f"[exit {proc.returncode}]")
        codes.append(proc.returncode)
    return 0 if all(code == 0 for code in codes) else 1


if __name__ == "__main__":
    sys.exit(main())
