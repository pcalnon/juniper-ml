#!/usr/bin/env python3
"""
Check that every path in a list carries, on a git ref, exactly the blob of a local copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (the PRs it verifies);
         util/push_signed_commit.py (which reads back each commit's blobs; this reads the MERGED result)

Why this exists
---------------
A squash merge of a multi-commit PR is expected to carry every commit's files, and a merge that raced a push has
shipped less than its PR before (a later commit's diff missing from `main`). The signed-commit tools read back each
commit as it lands; this reads the ref the PR was merged into, so "merged" is checked against what was sent. It
computes each local file's git blob id itself (``blob <size>\\0`` + bytes, SHA-1) and compares it with
``git ls-tree -r <ref>``. It prints counts and the paths that differ or are missing, never file content.

Usage
-----
    git fetch origin main   # first
    python3 -B util/ad-hoc/2026-10-10_verify_blobs_on_ref.py --ref origin/main --list <paths.txt> --root <copies>

Exit 0 when every listed path is on the ref with the local blob, 1 otherwise, 2 on a usage error.
"""
import argparse
import hashlib
import subprocess  # nosec B404 -- fixed argv, never a shell
import sys
from pathlib import Path


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data, usedforsecurity=False).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--list", required=True)
    ap.add_argument("--root", required=True, help="directory holding the local copies, at their repository paths")
    args = ap.parse_args()
    paths = [line.strip() for line in Path(args.list).read_text(encoding="utf-8").splitlines() if line.strip()]
    root = Path(args.root)
    if not paths or not root.is_dir():
        print("refused: an empty list or a missing --root", file=sys.stderr)
        return 2
    out = subprocess.run(["git", "ls-tree", "-r", args.ref], capture_output=True, text=True, check=False)  # nosec B603 B607
    if out.returncode != 0:
        print(f"refused: git ls-tree {args.ref} failed", file=sys.stderr)
        return 2
    on_ref = {}
    for row in out.stdout.splitlines():
        meta, _, path = row.partition("\t")
        on_ref[path] = meta.split()[2]
    same, differ, missing, unreadable = 0, [], [], []
    for path in paths:
        local = root / path
        if not local.is_file():
            unreadable.append(path)
        elif path not in on_ref:
            missing.append(path)
        elif on_ref[path] != blob_id(local.read_bytes()):
            differ.append(path)
        else:
            same += 1
    print(f"{args.ref}: {same} of {len(paths)} path(s) carry the local blob; {len(differ)} differ; {len(missing)} missing; {len(unreadable)} without a local copy")
    for label, rows in (("DIFFERS", differ), ("MISSING", missing), ("NO LOCAL COPY", unreadable)):
        for path in rows:
            print(f"  {label} {path}")
    return 0 if same == len(paths) else 1


if __name__ == "__main__":
    sys.exit(main())
