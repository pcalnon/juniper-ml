#!/usr/bin/env python3
"""
Show where each ruling-26 CHANGELOG entry sits in its repository's [Unreleased] section, and that section's style (V26).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (checks the CHANGELOG placement and category claims of the six PR texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
For each repository: reads main's ``CHANGELOG.md`` (from ``--clones``) and the frozen one (``--r26``/<repo>/final/),
finds the lines the frozen file adds, and prints: the ``## [...]`` release heading and ``### ...`` category heading
the added block sits under; the headings of the ``[Unreleased]`` section in order, with the number of top-level
entries under each; the first line of the top-level entry immediately before and after the added block; and how the
other top-level entries of that category open (bold lead sentence or not, sub-bullets or not), so the new entry's
style can be compared. Read-only.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_changelog.py --r26 DIR --clones DIR
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

REPOS = ["juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy"]


def _heading_at(lines: list[str], index: int, prefix: str) -> tuple[int, str]:
    for i in range(index, -1, -1):
        if lines[i].startswith(prefix) and not lines[i].startswith(prefix + "#"):
            return i, lines[i]
    return -1, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--r26", type=Path, required=True)
    parser.add_argument("--clones", type=Path, required=True)
    args = parser.parse_args()

    for repo in REPOS:
        old = (args.clones / repo / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        new = (args.r26 / repo / "final" / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
        inserts = [(j1, j2) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
        print(f"==================== {repo}")
        if len(inserts) != 1:
            print(f"  {len(inserts)} changed regions: {inserts}")
        j1, j2 = inserts[0]
        rel_i, release = _heading_at(new, j1, "## ")
        cat_i, category = _heading_at(new, j1, "### ")
        print(f"  added lines {j1 + 1}-{j2} under {release!r} (line {rel_i + 1}) / {category!r} (line {cat_i + 1})")
        # the [Unreleased] section's headings
        unrel = next((i for i, line in enumerate(new) if line.startswith("## [Unreleased]")), None)
        nxt = next((i for i in range(unrel + 1, len(new)) if new[i].startswith("## ")), len(new)) if unrel is not None else None
        if unrel is not None:
            print(f"  [Unreleased] spans lines {unrel + 1}-{nxt}; its headings:")
            current = None
            counts: dict[str, int] = {}
            order: list[str] = []
            for i in range(unrel + 1, nxt):
                if new[i].startswith("### "):
                    current = new[i]
                    order.append(current)
                    counts[current] = 0
                elif current and new[i].startswith("- "):
                    counts[current] += 1
            for heading in order:
                print(f"    {heading}  ({counts[heading]} top-level entries, the new one included if here)")
        # neighbours
        before = next((i for i in range(j1 - 1, -1, -1) if new[i].startswith("- ") or new[i].startswith("#")), None)
        after = next((i for i in range(j2, len(new)) if new[i].startswith("- ") or new[i].startswith("#")), None)
        if before is not None:
            print(f"  entry/heading before (line {before + 1}): {new[before][:170]}")
        if after is not None:
            print(f"  entry/heading after  (line {after + 1}): {new[after][:170]}")
        # style of the category's other entries
        if cat_i >= 0:
            end = next((i for i in range(cat_i + 1, len(new)) if new[i].startswith("#")), len(new))
            entries = [i for i in range(cat_i + 1, end) if new[i].startswith("- ") and not (j1 <= i < j2)]
            bold = sum(1 for i in entries if new[i].startswith("- **"))
            subs = 0
            for k, i in enumerate(entries):
                stop = entries[k + 1] if k + 1 < len(entries) else end
                if any(new[x].startswith("  - ") for x in range(i + 1, stop)):
                    subs += 1
            print(f"  other entries in this category: {len(entries)}; bold lead: {bold}; with sub-bullets: {subs}")
        print("  --- the added block:")
        for i in range(j1, j2):
            print(f"  | {new[i]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
