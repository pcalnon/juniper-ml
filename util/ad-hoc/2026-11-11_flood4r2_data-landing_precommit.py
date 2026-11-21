#!/usr/bin/env python3
"""
Run a repo's pinned pre-commit hooks on explicit files of an uncommitted tree, and prove no hook rewrote a file.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (each landing stage's changed files, from the stage worktree's root)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 11; adapted from 2026-11-08_flood4r2_canopy_precommit.py

Usage:
    python3 <this> --worktree <repo worktree> --log <file> [--pre-commit <binary>] -- <repo-relative path> [...]

``--files`` is given the explicit paths, so untracked (new) files are checked too and nothing is stashed. A hook
that "fixes" a file rewrites it in the worktree and exits 1: the sha256 of every path is taken before and after, and
any difference is reported as ``rewritten``. Exit 0 only when pre-commit exits 0 and nothing was rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: the pinned pre-commit binary on explicit paths
import sys
from pathlib import Path

DEFAULT_PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"


def _shas(worktree: Path, paths: list[str]) -> dict[str, str]:
    return {p: hashlib.sha256((worktree / p).read_bytes()).hexdigest() for p in paths}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--pre-commit", default=DEFAULT_PRE_COMMIT)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    worktree = args.worktree.resolve()
    before = _shas(worktree, args.paths)
    argv = [args.pre_commit, "run", "--files", *args.paths]
    proc = subprocess.run(argv, cwd=worktree, capture_output=True, text=True, check=False)  # nosec B603
    after = _shas(worktree, args.paths)
    rewritten = sorted(p for p in args.paths if before[p] != after[p])
    verdicts = [line for line in proc.stdout.splitlines() if line.rstrip().endswith(("Passed", "Failed", "Skipped"))]
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with open(args.log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={worktree}) {' '.join(argv)}\n# exit={proc.returncode} rewritten={rewritten}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    failed = [line for line in verdicts if line.rstrip().endswith("Failed")]
    print(json.dumps({"exit": proc.returncode, "files": len(args.paths), "hooks_passed": sum(1 for v in verdicts if v.rstrip().endswith("Passed")), "hooks_skipped": sum(1 for v in verdicts if v.rstrip().endswith("Skipped")), "hooks_failed": failed, "rewritten": rewritten, "log": str(args.log)}, indent=1))
    return 0 if proc.returncode == 0 and not rewritten else 1


if __name__ == "__main__":
    sys.exit(main())
