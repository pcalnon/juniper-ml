#!/usr/bin/env python3
"""
Move one CHANGELOG entry below the entry that follows it, byte for byte, so a new entry sits under an existing one of its subsection.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (round 2 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
A new entry at the very top of a subsection collides with every concurrent pull request that also adds one there.
The orchestrator's rule is that the new entry sits BELOW at least one existing entry of its subsection. This swaps
the entry that starts with --entry with the entry right after it (which starts with --next and ends at the blank line
before the next "## [" heading), refuses unless both start lines occur exactly once and the entries are adjacent,
and proves the file holds exactly the same lines afterwards, only reordered.

Usage:
    python3 <this> --file <CHANGELOG.md> --entry <first line prefix> --next <first line prefix> [--apply]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--entry", required=True)
    ap.add_argument("--next", dest="nxt", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    with open(args.file, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith(args.entry)]
    nexts = [i for i, line in enumerate(lines) if line.startswith(args.nxt)]
    if len(starts) != 1 or len(nexts) != 1:
        raise SystemExit(f"refused: --entry matches {len(starts)} lines and --next {len(nexts)}; each must match one")
    start, nxt = starts[0], nexts[0]
    block = lines[start:nxt]
    if not block or any(line.startswith(("- **", "## ", "### ")) for line in block[1:]):
        raise SystemExit("refused: the two entries are not adjacent")
    end = next(i for i in range(nxt + 1, len(lines)) if lines[i].startswith(("## ", "### ", "- **")))
    while lines[end - 1] == "":
        end -= 1
    moved = lines[:start] + lines[nxt:end] + block + lines[end:]
    if Counter(moved) != Counter(lines) or len(moved) != len(lines):
        raise SystemExit("refused: the reordered file does not hold the same lines")
    print(f"entry: lines {start + 1}-{nxt} ({len(block)} lines); the entry after it: lines {nxt + 1}-{end} ({end - nxt} lines)")
    print(f"after the move the entry starts at line {start + 1 + (end - nxt)}")
    if args.apply:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write("\n".join(moved))
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
