"""
Copy the r27 change set (every modified or added file of a canopy build tree) into another tree, sha256-checked.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage:
    python3 <this file> --src <build tree> --dst <tree> --out <json> [--final <dir>]

The change set is what `git status --porcelain --untracked-files=all` lists in the build tree as modified (M) or
untracked (??), ignored files excluded. Each file is copied to the same relative path under --dst (and, with --final,
under that directory too), and the copy's sha256 is compared with the source's. The destination tree must be at the
same HEAD as the source's merge base; that HEAD is recorded. Writes <json>: {src, dst, src_head, dst_head, files:
[{path, status, sha256, copies_equal}]}. Exits 1 if any copy differs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path


def git(tree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607 - fixed argv


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def change_set(tree: Path) -> list[tuple[str, str]]:
    entries = []
    for line in git(tree, "status", "--porcelain", "--untracked-files=all").splitlines():
        code, path = line[:2], line[3:]
        if code.strip() == "M":
            entries.append((path, "modified"))
        elif code == "??":
            entries.append((path, "added"))
        else:
            raise SystemExit(f"unexpected status {code!r} for {path}")
    return sorted(entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the r27 change set into another tree, sha256-checked.")
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--dst", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--final", type=Path, default=None)
    args = parser.parse_args()
    src, dst = args.src.resolve(), args.dst.resolve()
    files, ok = [], True
    for path, status in change_set(src):
        digest = sha256(src / path)
        targets = [dst / path] + ([args.final.resolve() / path] if args.final else [])
        equal = True
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / path, target)
            equal = equal and sha256(target) == digest
        ok = ok and equal
        files.append({"path": path, "status": status, "sha256": digest, "copies_equal": equal})
    record = {"src": str(src), "dst": str(dst), "src_head": git(src, "rev-parse", "HEAD").strip(), "dst_head": git(dst, "rev-parse", "HEAD").strip(), "files": files}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
