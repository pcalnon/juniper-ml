#!/usr/bin/env python3
# =============================================================================
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  util/ad-hoc
# File Name:    2026-11-23_one_artifact_carry_scripts_verified.py
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Created:      2026-11-23
# Last Updated: 2026-11-23
#
# Status: ad-hoc -- one-off (one-artifact publish arc, session e71d3e)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
#
# Description:
#   Carry the one-artifact arc's 26 uncommitted util/ad-hoc scripts from a sibling worktree into this one,
#   proving each file against the sha256 manifests the arc recorded on 2026-11-15/16 (carried_scripts.sha256,
#   copied_tools_writers.sha256).
#
#   Between 2026-11-20 and 11-22 a blind "owner" -> "Overtoad" text substitution (the Overtoad's
#   task/owner-is-the-overtoad PRs) also rewrote files on disk in sibling worktrees, these scripts among them.
#   A file whose bytes miss the manifest is therefore tried once more with the inverse substitution
#   ("Overtoad" -> "owner"), and is written here ONLY if that inverse reproduces the recorded sha256 exactly.
#   Nothing is written for a file that matches neither way; the run then exits 1 and names it.
#
#   Read-only on the source worktree. Writes only under this worktree's util/ad-hoc/.
#
# Usage:
#   python3 -I util/ad-hoc/2026-11-23_one_artifact_carry_scripts_verified.py --source <sibling worktree> \
#       --carried <carried_scripts.sha256> --copied <copied_tools_writers.sha256> [--dry-run]
# =============================================================================
"""Carry the arc's uncommitted scripts into this worktree, proven byte-for-byte against the recorded sha256."""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]


def read_manifest(path: Path, prefix: str) -> dict[str, str]:
    """Map a path relative to util/ad-hoc/ to its recorded sha256."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.strip()
        if prefix and name.startswith(prefix):
            name = name[len(prefix):]
        out[name] = digest
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path, help="sibling worktree root holding the untracked scripts")
    ap.add_argument("--carried", required=True, type=Path, help="carried_scripts.sha256 (names relative to util/ad-hoc/)")
    ap.add_argument("--copied", required=True, type=Path, help="copied_tools_writers.sha256 (names prefixed util/ad-hoc/)")
    ap.add_argument("--dry-run", action="store_true", help="verify and report; write nothing")
    args = ap.parse_args()

    wanted = read_manifest(args.carried, "")
    wanted.update(read_manifest(args.copied, "util/ad-hoc/"))
    src_root = args.source.resolve() / "util" / "ad-hoc"
    dst_root = HERE / "util" / "ad-hoc"
    print(f"manifest entries: {len(wanted)} (expect 26)")

    failures: list[str] = []
    counts = {"verbatim": 0, "inverse": 0}
    for name in sorted(wanted):
        src = src_root / name
        data = src.read_bytes()
        how = "verbatim"
        if hashlib.sha256(data).hexdigest() != wanted[name]:
            restored = data.replace(b"Overtoad", b"owner")
            if hashlib.sha256(restored).hexdigest() != wanted[name]:
                failures.append(name)
                print(f"FAIL     {name}: neither the bytes on disk nor the inverse substitution match")
                continue
            data, how = restored, "inverse"
        counts[how] += 1
        dst = dst_root / name
        if dst.exists() and dst.read_bytes() != data:
            failures.append(name)
            print(f"REFUSE   {name}: a DIFFERENT file already exists here")
            continue
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            dst.chmod(src.stat().st_mode & 0o777)
        print(f"OK {how:8s} {name}")
    print(f"verbatim={counts['verbatim']} inverse={counts['inverse']} failed={len(failures)} dry_run={args.dry_run}")
    return 1 if failures or len(wanted) != 26 else 0


if __name__ == "__main__":
    sys.exit(main())
