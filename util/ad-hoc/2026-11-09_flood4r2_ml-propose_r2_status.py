#!/usr/bin/env python3
"""List what the ml-propose carrier's worktree changes against its base, without running git inside that worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (the Cursor flood-4 round-2 "ml-propose" carrier, second build after validation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; util/ad-hoc/2026-11-08_flood4r2_ml-propose_manifest.py (reads the name_status.txt this writes)

The session that builds this carrier is isolated in another worktree, which refuses ``git`` aimed at the carrier's.
So this reads the base tree from ``--ls-tree`` (``git ls-tree -r --full-tree <base>``, run in any worktree of the
repository) and compares the carrier's files with it in Python:

* a tracked file whose bytes hash (git's blob sha1: ``blob <size>\\0<bytes>``) differs from the base blob is ``M``;
  a tracked file that is missing is ``D``. Paths an LFS filter rewrites (``.gitattributes``: images) are skipped,
  since their checkout bytes are a smudged copy of the blob, never the blob itself;
* an untracked file is ``??``. Only the directories a carrier can touch are walked (``SCAN_ROOTS`` and the root's
  own files), skipping the repository's ignored trees (``tmp/``, caches, ``*.egg-info``, ``.git``).

Writes ``git status --porcelain``-shaped lines (``" M path"``, ``"?? path"``) to ``--out``, sorted, with LC_ALL=C order.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-propose_r2_status.py --worktree <carrier root> --ls-tree <file> --out <file>
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

SCAN_ROOTS = ("util", "tests", "docs", "notes", "scripts", "conf", "prompts", "reports", ".github", "juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core")
SKIP_DIRS = {"tmp", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "node_modules", ".git", "build", "dist", ".venv", "logs"}
LFS_SUFFIXES = {".xcf", ".jpg", ".png", ".ico", ".jpeg", ".bmp", ".svg", ".JPG", ".gif", ".tiff", ".webp"}


def _blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--ls-tree", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = Path(args.worktree).resolve()
    tracked: dict = {}
    symlinks: set = set()
    with open(args.ls_tree, encoding="utf-8") as fh:
        for line in fh:
            meta, _, path = line.rstrip("\n").partition("\t")
            mode, kind, sha = meta.split()
            if kind == "blob" and mode == "120000":
                symlinks.add(path)  # tracked, but its blob is the link text: not compared
            elif kind == "blob":
                tracked[path] = sha
    lines = []
    skipped_lfs = 0
    for path, sha in tracked.items():
        if Path(path).suffix in LFS_SUFFIXES:
            skipped_lfs += 1
            continue
        target = root / path
        if not target.is_file():
            lines.append(f" D {path}")
        elif _blob_sha1(target.read_bytes()) != sha:
            lines.append(f" M {path}")
    tracked_set = set(tracked) | symlinks
    candidates = [p for p in root.iterdir() if p.is_file()]
    for top in SCAN_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
            candidates.extend(Path(dirpath) / name for name in filenames)
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        if rel not in tracked_set and not path.name.endswith((".pyc", ".pyo")) and path.name != ".git":
            lines.append(f"?? {rel}")
    lines.sort(key=lambda ln: ln[3:].encode())
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("".join(f"{ln}\n" for ln in lines))
    print(f"{len(tracked)} tracked paths compared ({skipped_lfs} LFS paths skipped); {len(lines)} changes written to {args.out}")
    for ln in lines:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
