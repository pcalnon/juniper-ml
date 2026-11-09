#!/usr/bin/env python3
"""
Write the blobs of given paths at a git ref into a directory, preserving repo-relative paths.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 signed three-step update-branch)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: auto-memory reference_changelog_conflict_signed_update_branch.md (step 1 pushes main's versions verbatim)

WHY THIS EXISTS
Step 1 of the signed three-step pushes each conflicting file EXACTLY as main has it, so a server-side
update-branch merges cleanly. This extracts those blobs byte-for-byte (`git cat-file blob <ref>:<path>`)
and prints each blob id, so the push's read-back can be compared with main's tree.

Usage:
  2026-11-07_flood4_extract_ref_files.py --ref origin/main --out <dir> <path> [<path> ...]
"""

import argparse
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()
    for p in a.paths:
        blob = subprocess.run(["git", "rev-parse", "%s:%s" % (a.ref, p)], capture_output=True, text=True, check=True).stdout.strip()
        data = subprocess.run(["git", "cat-file", "blob", blob], capture_output=True, check=True).stdout
        dst = os.path.join(a.out, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(data)
        print("%s  %s (%d bytes)" % (blob, p, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
