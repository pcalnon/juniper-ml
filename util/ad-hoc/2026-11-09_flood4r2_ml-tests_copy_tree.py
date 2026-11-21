#!/usr/bin/env python3
"""
Copy the carrier's changed files into a scratch worktree of the same base, or verify that one matches.

The whole-regression run takes most of an hour; running it in a byte-identical copy of the carrier lets the
mutation runs (which edit the code under test in place) proceed in the carrier worktree meanwhile. The copy is
made from `git diff --name-only HEAD` plus untracked files (util/ad-hoc/ excluded), and --verify re-reads both
trees and reports any path whose sha256 differs, so the copy's results can be credited to the final carrier.

Usage (from the carrier worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_copy_tree.py --dest <scratch worktree> [--verify]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_run_suites.py
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def _paths() -> list:
    changed = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, check=True).stdout.split()
    return sorted(p for p in set(changed) | set(untracked) if not p.startswith("util/ad-hoc/"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    dest = Path(args.dest)
    differ = []
    for path in _paths():
        if args.verify:
            if not (dest / path).is_file() or _sha(Path(path)) != _sha(dest / path):
                differ.append(path)
            continue
        (dest / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest / path)
    if args.verify:
        print("identical" if not differ else "DIFFER: " + ", ".join(differ))
        return 1 if differ else 0
    print(f"copied {len(_paths())} paths")
    return 0


if __name__ == "__main__":
    sys.exit(main())
