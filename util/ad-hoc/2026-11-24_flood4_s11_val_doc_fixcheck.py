#!/usr/bin/env python3
"""
Check a validator's exact old -> new fixes against the drafted flood-4 record and changelog entry, then apply them to copies.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V2: document lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (proves every proposed fix applies once and in any order; edits only copies)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; util/ad-hoc/2026-11-24_flood4_s11_val_doc_checks.py

What it does
------------
Reads --fixes, a JSON list of {"id", "target": "record" | "changelog", "old", "new"}. For each target it:

  1. counts every fix's old string in the UNEDITED file (each must occur exactly once);
  2. applies the fixes in the listed order, re-checking at each step that the old string still occurs once
     (so no fix consumes or duplicates another's anchor);
  3. applies them again in REVERSE order and compares, so a reader can apply them in any order;
  4. writes the forward result to --out-dir as <basename of the input>.fixed.

It prints a per-fix line and a summary; it never edits its inputs. Exit 0 when every fix applies cleanly and both
orders agree, 1 otherwise, 2 on a usage error.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_doc_fixcheck.py --fixes fixes.json --record R.md \
        --changelog changelog_entry.md --out-dir DIR
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def apply_all(text: str, fixes: list[dict]) -> tuple[str, list[str]]:
    problems: list[str] = []
    for fx in fixes:
        n = text.count(fx["old"])
        if n != 1:
            problems.append(f"{fx['id']}: old string occurs {n} times at its turn")
            continue
        text = text.replace(fx["old"], fx["new"], 1)
    return text, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixes", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--changelog", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    with open(args.fixes, encoding="utf-8") as fh:
        fixes = json.load(fh)
    paths = {"record": Path(args.record), "changelog": Path(args.changelog)}
    ok = True
    for target, path in paths.items():
        original = path.read_text(encoding="utf-8")
        mine = [fx for fx in fixes if fx["target"] == target]
        print(f"== {target}: {path} ({len(mine)} fixes)")
        for fx in mine:
            n = original.count(fx["old"])
            ok &= n == 1
            print(f"  {fx['id']:5} occurrences in the unedited file: {n} {'OK' if n == 1 else 'NOT UNIQUE'}")
        forward, p_fwd = apply_all(original, mine)
        reverse, p_rev = apply_all(original, list(reversed(mine)))
        for p in p_fwd + p_rev:
            print(f"  PROBLEM {p}")
        same = forward == reverse
        ok &= not p_fwd and not p_rev and same
        out = Path(args.out_dir) / (path.name + ".fixed")
        out.write_text(forward, encoding="utf-8")
        print(f"  forward and reverse orders give the same text: {same}; lines {original.count(chr(10))} -> {forward.count(chr(10))}; wrote {out}")
    print("ALL FIXES APPLY ONCE, IN ANY ORDER" if ok else "SOME FIXES FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
