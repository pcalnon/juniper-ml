#!/usr/bin/env python3
"""
Report whether every uncommitted file in this checkout is byte-identical to a commit's copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (rehoming a worktree whose changes landed through signed API commits)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629 (the local test runner), whose files were uploaded with util/push_signed_commit.py

A change uploaded with ``createCommitOnBranch`` never becomes a local commit, so the worktree that wrote it still
shows it as modified or untracked after the squash lands. Before such a worktree is reset onto ``main``, this
proves nothing would be lost: each path ``git status --porcelain`` lists must equal the commit's blob.

Usage: ``python3 util/ad-hoc/2026-11-24_worktree_matches_commit.py COMMIT``. Exit 0 when every listed path is the
same, 1 when any differs or is absent from the commit. This script's own path is skipped.
"""

from __future__ import annotations

import subprocess  # nosec B404 - runs git with fixed argv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()


def changed_paths() -> list[str]:
    """Every modified, added or untracked path, from ``git status --porcelain=v1 -z`` (renames give the new path)."""
    out = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT, capture_output=True, check=True).stdout  # nosec B603 B607
    fields = out.decode("utf-8", "surrogateescape").split("\0")
    paths: list[str] = []
    skip_next = False
    for field in fields:
        if skip_next:
            skip_next = False
            continue
        if not field:
            continue
        status, path = field[:2], field[3:]
        if status[0] in "RC":
            skip_next = True  # the rename's source path follows; the new path is the one that holds the content
        paths.append(path)
    return sorted(p for p in paths if p != SELF)


def blob(commit: str, path: str) -> bytes | None:
    """The commit's copy of the path, or None when the commit has no such file."""
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=False)  # nosec B603 B607
    return proc.stdout if proc.returncode == 0 else None


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: 2026-11-24_worktree_matches_commit.py COMMIT", file=sys.stderr)
        return 2
    commit = argv[0]
    paths = changed_paths()
    if not paths:
        print("no uncommitted path")
        return 0
    bad = 0
    for path in paths:
        theirs = blob(commit, path)
        if theirs is None:
            verdict = "ABSENT from the commit"
        elif theirs == (ROOT / path).read_bytes():
            verdict = "same"
        else:
            verdict = "DIFFERS"
        bad += verdict != "same"
        print(f"{verdict:<22}  {path}")
    print(f"{len(paths) - bad} of {len(paths)} uncommitted path(s) equal {commit}'s copy")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
