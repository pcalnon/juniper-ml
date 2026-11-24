#!/usr/bin/env python3
"""
Three-way a carrier's shared documents against a sibling pull request's head and report the version stamps that result.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the carrier's stamps.json ("trap": a clean three-way keeps one bump for two changes);
         tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (rebuild with ``git merge-file -p``)

For each ``--file`` the script takes the carrier's copy (``--carrier`` checkout, working tree), the base
blob (``--base`` ref) and the sibling's blob (``--sibling`` ref, read from ``--repo``), writes all three and
the merged result under ``--out``, and prints the conflict count ``git merge-file`` returned with every
line of each side that carries a version or date stamp. Read-only on the repository and the carrier.

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_three_way.py --repo <checkout> --carrier <checkout> --base <ref>
      --sibling <ref> --out <dir> --file <path> [--file <path> ...]
Exit: 0 (it reports; it does not judge).
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed-argv read-only git calls
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Document Version|Last Updated|Version covered|Compiled)\*\*")


def _show(repo: Path, ref: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607 -- fixed argv


def _stamps(text: str) -> list[str]:
    return [f"{number}: {line.strip()}" for number, line in enumerate(text.splitlines(), start=1) if STAMP.match(line)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--sibling", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--file", action="append", required=True)
    args = parser.parse_args()
    for path in args.file:
        target = args.out / path.replace("/", "__")
        target.mkdir(parents=True, exist_ok=True)
        carrier = (args.carrier / path).read_text(encoding="utf-8")
        base = _show(args.repo, args.base, path)
        sibling = _show(args.repo, args.sibling, path)
        (target / "carrier").write_text(carrier, encoding="utf-8")
        (target / "base").write_text(base, encoding="utf-8")
        (target / "sibling").write_text(sibling, encoding="utf-8")
        merged = subprocess.run(["git", "merge-file", "-p", str(target / "carrier"), str(target / "base"), str(target / "sibling")], capture_output=True, text=True, check=False)  # nosec B603 B607 -- fixed argv
        (target / "merged").write_text(merged.stdout, encoding="utf-8")
        print(f"\n== {path}: git merge-file exit {merged.returncode} (the number of conflicts; negative on error)")
        for label, text in (("base", base), ("carrier", carrier), ("sibling", sibling), ("merged", merged.stdout)):
            print(f"  {label:8s} {len(text.splitlines()):5d} lines; stamps: {_stamps(text)}")
        print(f"  conflict markers in merged: {merged.stdout.count('<<<<<<<')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
