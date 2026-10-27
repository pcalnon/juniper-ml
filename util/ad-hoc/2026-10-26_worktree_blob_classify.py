#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_worktree_blob_classify.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Classifies a worktree's files against its base tree and main WITHOUT running
#   git inside it. Built for the 2026-10-26 flood-3 cleanup: the worktree-isolated
#   session could not cd into .claude/worktrees/agent-* to run a status there, and
#   an mtime test was useless, since a checkout writes every file after its pointer
#   file. The inputs are tree listings (`ls-tree -r <ref>`) and the object list of
#   main's history (`rev-list --objects <ref>`), both made in any worktree of the
#   same repository. Each file's blob id is computed the way git computes it, then:
#     MODIFIED   in the base tree with another blob
#     UNTRACKED  not in the base tree
#     DELETED    in the base tree, missing on disk
#   and each MODIFIED / UNTRACKED file is compared with main: SAME (identical blob
#   on main), DIFF (main has another blob there) or ABSENT (not on main). Given the
#   object list, DIFF/ABSENT gain /HIST (the blob existed somewhere in main's
#   history, so git can recover it) or /UNIQUE (it never did: preserve it before
#   `worktree remove --force`, with 2026-10-26_worktree_preserve_unique.py).
#   Cache directories and LFS-tracked binaries (smudged on disk, pointers in the
#   tree) are skipped. Ignored files are NOT filtered: review UNTRACKED rows.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-26_worktree_blob_classify.py \
#       <worktree> <base listing> <main listing> [<main object list>]
# -----------------------------------------------------------------------------
"""Classify a worktree's files against its base tree and main without running git in it."""

import hashlib
import os
import sys
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".git", "node_modules", ".venv", "venv"}
LFS_EXT = {".xcf", ".jpg", ".png", ".ico", ".jpeg", ".gif", ".svg", ".bmp", ".tif", ".tiff", ".webp", ".pdf"}
POINTER = ".git"  # a linked worktree's pointer file, not content


def listing(path: str) -> dict:
    """Parse `ls-tree -r` output into {path: blob id}."""
    out = {}
    for line in Path(path).read_text().splitlines():
        meta, name = line.split("\t", 1)
        _mode, kind, sha = meta.split()
        if kind == "blob":
            out[name] = sha
    return out


def blob_id(p: Path) -> str:
    """The git blob id of a file (a symlink hashes its target text)."""
    data = os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec B324 -- git's object id, not security


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    wt, base, main_ = Path(sys.argv[1]), listing(sys.argv[2]), listing(sys.argv[3])
    history: set = set()
    if len(sys.argv) > 4:  # every object reachable from main
        history = {line.split()[0] for line in Path(sys.argv[4]).read_text().splitlines() if line}
    seen, rows = set(), []
    for dirpath, dirnames, filenames in os.walk(wt):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for f in filenames:
            p = Path(dirpath) / f
            rel = str(p.relative_to(wt))
            if rel == POINTER or p.suffix.lower() in LFS_EXT:
                continue
            seen.add(rel)
            try:
                bid = blob_id(p)
            except OSError as exc:
                rows.append(("UNREADABLE", rel, str(exc)))
                continue
            if rel in base:
                if base[rel] == bid:
                    continue
                state = "MODIFIED"
            else:
                state = "UNTRACKED"
            vs_main = "SAME" if main_.get(rel) == bid else ("DIFF" if rel in main_ else "ABSENT")
            if vs_main != "SAME" and history:
                vs_main += "/HIST" if bid in history else "/UNIQUE"
            rows.append((state, rel, vs_main))
    for rel in base:
        if rel not in seen and Path(rel).suffix.lower() not in LFS_EXT and not (wt / rel).exists():
            rows.append(("DELETED", rel, "-"))
    for state, rel, vs_main in sorted(rows):
        print(f"{state:10} {vs_main:14} {rel}")
    print(f"TOTAL {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
