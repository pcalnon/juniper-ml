#!/usr/bin/env python3
"""
Hash every file of the ml-docs carrier against its manifest and list the carrier tree's changes against a main commit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check A)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/ (the validator's deliverables)

The carrier is an uncommitted worktree that a validator may not run git in, so its status is emulated: every file on
disk (outside .git and tmp/) gets its git blob id, computed here, and is compared with ``git ls-tree -r`` of the base
commit, which this script reads through ``--repo`` (any checkout that shares the object store). LFS-filtered
paths (``filter=lfs`` in .gitattributes) hold smudged bytes on disk and a pointer blob in the tree, so they are
listed apart, not as edits.

Usage:
  2026-11-14_flood4r2_val_ml-docs_hashcheck.py --carrier <dir> --manifest <manifest.json> --base <sha>
      --repo <a checkout sharing the object store> --out <report.json>
"""

import argparse
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path

SKIP_DIRS = {".git", "tmp", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}


def blob_id(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode() + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def lfs_patterns(carrier: Path) -> list[str]:
    attrs = carrier / ".gitattributes"
    if not attrs.is_file():
        return []
    patterns = []
    for line in attrs.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and "filter=lfs" in parts[1:]:
            patterns.append(parts[0])
    return patterns


def is_lfs(rel: str, patterns: list[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(rel, p) for p in patterns)


def skipped(parts: tuple[str, ...]) -> bool:
    return any(part in SKIP_DIRS for part in parts[:-1]) or parts[0] in SKIP_DIRS


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    carrier = Path(args.carrier)
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    hashes = []
    for entry in manifest["files"]:
        path = carrier / entry["path"]
        got = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        hashes.append({"path": entry["path"], "status": entry["status"], "manifest": entry["sha256"], "disk": got, "match": got == entry["sha256"]})
    listing = subprocess.run(["git", "ls-tree", "-r", "-z", args.base], cwd=args.repo, capture_output=True, check=True).stdout.decode("utf-8")
    tree = {}
    for rec in listing.split("\0"):
        if not rec:
            continue
        meta, rel = rec.split("\t", 1)
        _mode, kind, sha = meta.split()
        if kind == "blob":
            tree[rel] = sha
    patterns = lfs_patterns(carrier)
    on_disk = {}
    for path in carrier.rglob("*"):
        parts = path.relative_to(carrier).parts
        if skipped(parts):
            continue
        if path.is_symlink():
            on_disk["/".join(parts)] = blob_id(str(path.readlink()).encode())
        elif path.is_file():
            on_disk["/".join(parts)] = blob_id(path.read_bytes())
    modified, added, deleted, lfs = [], [], [], []
    for rel, sha in sorted(on_disk.items()):
        if rel not in tree:
            added.append(rel)
        elif tree[rel] != sha:
            (lfs if is_lfs(rel, patterns) else modified).append(rel)
    for rel in sorted(tree):
        if rel not in on_disk and not skipped(tuple(rel.split("/"))):
            deleted.append(rel)
    report = {
        "carrier": str(carrier),
        "base": args.base,
        "manifest_hashes": hashes,
        "manifest_all_match": all(h["match"] for h in hashes),
        "modified": modified,
        "added": added,
        "deleted": deleted,
        "lfs_smudged_not_edits": len(lfs),
    }
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("manifest_all_match", "modified", "added", "deleted", "lfs_smudged_not_edits")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
