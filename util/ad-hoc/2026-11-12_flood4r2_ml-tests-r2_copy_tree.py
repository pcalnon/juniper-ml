#!/usr/bin/env python3
"""
Copy this carrier's uncommitted tree onto a scratch worktree of the same base, or verify such a copy byte for byte.

The whole regression list takes long, and the mutation check rewrites source files in the carrier's worktree
while it runs, so the list runs in a byte-identical copy. Every path the carrier changes goes over: the modified
and the new files, helper scripts included, since some suites walk util/ (path-literal baselines, script
inventories). Round 1's copier took the 23 carrier paths and left the helpers behind.

  default   copy every changed or untracked (not ignored) path of this worktree to --dest;
  --verify  hash both sides (sha256) and compare the destination's own change list with this one's: any path
            that differs, is missing, or is changed there but not here is reported.

Both worktrees must have the same HEAD. Writes <out> (JSON) when --out is given.

Usage (from the carrier worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_copy_tree.py --dest <scratch worktree> [--verify] [--out F]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_copy_tree.py (round 1's)
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=str(cwd), capture_output=True, text=True, check=True).stdout


def _changed(root: Path) -> list:
    """Paths `git status` reports in ``root``: modified, intent-to-add and untracked (not ignored)."""
    out = _git(root, "status", "--porcelain", "--untracked-files=all", "-z")
    return sorted(entry[3:] for entry in out.split("\0") if entry)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "absent"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    here, dest = Path.cwd(), Path(args.dest)
    heads = (_git(here, "rev-parse", "HEAD").strip(), _git(dest, "rev-parse", "HEAD").strip())
    if heads[0] != heads[1]:
        raise SystemExit(f"different HEADs: {heads[0]} here, {heads[1]} in --dest")
    paths = _changed(here)
    if not args.verify:
        for path in paths:
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(here / path, target)
        print(f"copied {len(paths)} paths to {dest}")
    rows = [{"path": path, "here": _sha(here / path), "dest": _sha(dest / path)} for path in paths]
    differing = [row["path"] for row in rows if row["here"] != row["dest"]]
    extra = [path for path in _changed(dest) if path not in paths]
    report = {"head": heads[0], "here": str(here), "dest": str(dest), "paths": len(paths), "differing": differing, "changed_in_dest_only": extra, "rows": rows}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    identical = not differing and not extra
    print(f"{len(paths)} paths; differing: {differing or 'none'}; changed in --dest only: {extra or 'none'} -> {'identical' if identical else 'DIFFERENT'}")
    return 0 if identical else 1


if __name__ == "__main__":
    sys.exit(main())
