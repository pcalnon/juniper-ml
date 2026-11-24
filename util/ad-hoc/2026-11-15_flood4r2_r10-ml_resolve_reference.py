#!/usr/bin/env python3
"""
Resolve a docs/REFERENCE.md three-way rebuild whose one conflict is two Version History rows added after the same row.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-ml)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
A carrier that bumped docs/REFERENCE.md from main's version to the next one collides with any landing that took the
same next version first: `git merge-file -p <carrier> <base> <main>` then merges the header and footer stamps
silently (both sides wrote the same new value) and conflicts only on the two Version History rows. The rule is main's
value at the landing plus one step, header == footer, the row directly after main's highest. This takes the merge
output, requires exactly one conflict block whose two sides are one table row each, keeps main's row and puts the
carrier's row after it with --version-to, rewrites the header and footer `**Version:** --version-from` lines (exactly
two) to --version-to, and refuses anything else. It writes only --out and prints what it changed.

Usage:
    python3 <this> --merged <merge-file output> --out <file> --version-from 0.6.75 --version-to 0.6.76
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--merged", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--version-from", required=True)
    ap.add_argument("--version-to", required=True)
    args = ap.parse_args()
    lines = args.merged.read_text(encoding="utf-8").split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("<<<<<<< ")]
    if len(starts) != 1:
        raise SystemExit(f"expected exactly one conflict block, found {len(starts)}")
    start = starts[0]
    middle, end = start + 2, start + 4
    if lines[middle] != "=======" or not lines[end].startswith(">>>>>>> "):
        raise SystemExit("the conflict block is not one row against one row")
    ours, theirs = lines[start + 1], lines[middle + 1]
    old_cell = f"| {args.version_from}  |"
    if not (ours.startswith(old_cell) and theirs.startswith(old_cell)):
        raise SystemExit(f"both sides must be rows of {args.version_from}: {ours[:30]!r} / {theirs[:30]!r}")
    renumbered = f"| {args.version_to}  |" + ours[len(old_cell) :]
    lines[start : end + 1] = [theirs, renumbered]
    stamp_from, stamp_to = f"**Version:** {args.version_from}", f"**Version:** {args.version_to}"
    sites = [i for i, line in enumerate(lines) if line == stamp_from]
    if len(sites) != 2:
        raise SystemExit(f"expected the header and the footer to read {stamp_from!r}, found {len(sites)} such lines")
    for i in sites:
        lines[i] = stamp_to
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"kept main's row {theirs[:40]!r}; carrier's row renumbered to {args.version_to} after it; {stamp_from!r} -> {stamp_to!r} at lines {[i + 1 for i in sites]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
