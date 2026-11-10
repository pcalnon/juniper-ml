#!/usr/bin/env python3
"""
Round-5 validator: check that every round-4 fix entry (the builder's JSON) landed exactly once in the frozen files and
that its old text is gone; print each new text's line number.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 5 (findings: tmp/flood4/ml-docs/val-round5/)

Usage: python3 -I 2026-11-07_flood4_val_round5_fix_presence.py <fixes.json> <frozen_dir>
"""

from __future__ import annotations

import json
import os
import sys


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        fixes = json.load(fh)
    bad = 0
    for n, fx in enumerate(fixes, 1):
        with open(os.path.join(argv[2], fx["path"]), encoding="utf-8") as fh:
            text = fh.read()
        new_count, old_count = text.count(fx["new"]), text.count(fx["old"])
        line = text[: text.find(fx["new"])].count("\n") + 1 if new_count else None
        ok = new_count == 1 and (old_count == 0 or fx["old"] in fx["new"])
        bad += not ok
        print(f"{n:2d} pr={fx['pr']} {fx['path']}:{line} new={new_count} old={old_count} {'OK' if ok else 'PROBLEM'}")
    print(f"{len(fixes)} entries, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
