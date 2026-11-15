#!/usr/bin/env python3
"""
Emulate ``git status`` of a dead builder's uncommitted tree from blob hashes, and compare it with its probe commits.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)

The predecessor's tree cannot be read with git from this session (its worktree is another juniper-ml worktree), so
this script computes every file's git blob id itself (``sha1(b"blob <size>\\0" + bytes)``, which is what
``git hash-object`` prints) and compares it with ``git ls-tree -r`` listings saved beforehand:

* every path of the base listing: same blob (unchanged), other blob (modified) or absent (deleted);
* every file under the tree that the base does not list (untracked), skipping ``.git``, ``tmp/``, ``__pycache__``
  and the tool caches a test run leaves;
* each named path against each probe listing given with ``--probe NAME=LISTING``.

Usage: 2026-11-14_flood4r2_ml-docs_verify_p2.py --tree <dir> --base-listing <file> [--probe NAME=LISTING ...]
       --paths <p> [<p> ...] --out <json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", "tmp", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", "node_modules", ".venv"}


def blob_id(path: Path) -> str:
    """Return the git blob id of the file at ``path`` (the value ``git hash-object`` prints)."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def sha256_of(path: Path) -> str:
    """Return the sha256 hex digest of the file at ``path``."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_listing(listing: Path) -> dict[str, str]:
    """Parse ``git ls-tree -r`` output into {path: blob id} (blobs only)."""
    entries: dict[str, str] = {}
    for line in listing.read_text(encoding="utf-8").splitlines():
        meta, _, name = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            entries[name] = parts[2]
    return entries


def walk_files(tree: Path) -> list[str]:
    """Every regular file or symlink under ``tree``, repo-relative, outside the skipped directories."""
    found: list[str] = []
    for root, dirs, files in os.walk(tree):
        rel_root = Path(root).relative_to(tree)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if rel_root.parts[:2] == (".claude", "worktrees"):
            dirs[:] = []
            continue
        for name in files:
            found.append(str(rel_root / name) if str(rel_root) != "." else name)
    return sorted(found)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--base-listing", required=True, type=Path)
    parser.add_argument("--probe", action="append", default=[], help="NAME=LISTING")
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    base = read_listing(args.base_listing)
    report: dict[str, object] = {"tree": str(args.tree), "base_listing": str(args.base_listing)}
    modified, deleted = [], []
    for name, oid in sorted(base.items()):
        path = args.tree / name
        if path.is_symlink():
            target = os.readlink(path).encode()
            current = hashlib.sha1(f"blob {len(target)}\0".encode() + target, usedforsecurity=False).hexdigest()
        elif path.is_file():
            current = blob_id(path)
        else:
            deleted.append(name)
            continue
        if current != oid:
            modified.append(name)
    untracked = [name for name in walk_files(args.tree) if name not in base]
    report["modified"] = modified
    report["deleted"] = deleted
    report["untracked"] = untracked

    probes = {}
    for spec in args.probe:
        label, _, listing = spec.partition("=")
        probes[label] = read_listing(Path(listing))
    per_path = []
    for name in args.paths:
        path = args.tree / name
        row: dict[str, object] = {"path": name, "blob": blob_id(path), "sha256": sha256_of(path), "base_blob": base.get(name)}
        for label, listing in probes.items():
            row[f"{label}_blob"] = listing.get(name)
            row[f"equals_{label}"] = listing.get(name) == row["blob"]
        per_path.append(row)
    report["paths"] = per_path
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"modified {len(modified)}, deleted {len(deleted)}, untracked {len(untracked)}")
    for name in modified:
        print(f"  M {name}")
    for name in deleted:
        print(f"  D {name}")
    for name in untracked:
        print(f"  ? {name}")
    for row in per_path:
        flags = " ".join(f"{label}={'same' if row[f'equals_{label}'] else 'DIFF'}" for label in probes)
        print(f"  {row['path']}: blob {row['blob'][:12]} sha256 {row['sha256'][:16]} {flags}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
