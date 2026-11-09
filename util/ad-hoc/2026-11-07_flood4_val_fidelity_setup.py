"""
Flood-4 validation (fidelity lens): prove the carrier's on-disk files equal its staged tree, then copy them in.

Usage: python3 <this> <out.json> <carrier_worktree>

Reads the builder's carrier worktree READ-ONLY (plain file reads, never git there). For every path the
staged tree ddfae11e holds, hashes the target's on-disk file as a git blob and compares it to the tree's
blob; lists on-disk files the tree does not hold (outside tmp/, .git and caches); then copies every
changed non-util/ad-hoc path into THIS worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
SKIP_DIRS = {".git", "tmp", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist", ".venv", "node_modules"}


def run(*args: str) -> str:
    return subprocess.run(list(args), cwd=HERE, check=True, capture_output=True, text=True).stdout


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main() -> int:
    out = Path(sys.argv[1])
    target = Path(sys.argv[2])  # the builder's carrier worktree, read-only
    tree_entries: dict[str, tuple[str, str]] = {}
    for line in run("git", "ls-tree", "-r", "-z", TREE).split("\0"):
        if not line:
            continue
        meta, path = line.split("\t", 1)
        mode, _type, sha = meta.split()
        tree_entries[path] = (mode, sha)
    mismatches = []
    missing = []
    for path, (mode, sha) in sorted(tree_entries.items()):
        p = target / path
        if mode == "120000":
            if not p.is_symlink() or blob_sha(os.readlink(p).encode()) != sha:
                mismatches.append(path)
            continue
        if not p.exists():
            missing.append(path)
            continue
        if blob_sha(p.read_bytes()) != sha:
            mismatches.append(path)
    extra = []
    for root, dirs, files in os.walk(target):
        rel_root = Path(root).relative_to(target)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (rel_root == Path(".") and d == ".claude") and not d.endswith(".egg-info")]
        for f in files:
            rel = str((rel_root / f)) if str(rel_root) != "." else f
            if rel not in tree_entries and not f.endswith(".pyc"):
                extra.append(rel)
    changed = [line.split("\t") for line in run("git", "diff", "--name-status", "--no-renames", BASE, TREE).splitlines()]
    copied = []
    for status, path in changed:
        if path.startswith("util/ad-hoc/"):
            continue
        src = target / path
        dst = HERE / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append((status, path))
    report = {
        "tree_paths": len(tree_entries),
        "on_disk_vs_tree_mismatches": mismatches,
        "missing_on_disk": missing,
        "on_disk_not_in_tree": sorted(extra),
        "changed_vs_base": changed,
        "copied_into_validator_worktree": copied,
    }
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"tree paths {len(tree_entries)}; mismatches {len(mismatches)}; missing {len(missing)}; extra {len(extra)}; changed {len(changed)}; copied {len(copied)}")
    print("mismatches:", mismatches[:20])
    print("extra:", sorted(extra)[:40])
    return 0


if __name__ == "__main__":
    sys.exit(main())
