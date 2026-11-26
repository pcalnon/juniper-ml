#!/usr/bin/env python3
"""
Print validator fixes ({"id", "file", "old", "new", ...}) from one or more fixes.json files, every field, by id.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition, session 16: ruling 28's landing)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (reading two lenses' fixes for a hand merge where they touch the same text)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8;
         util/ad-hoc/2026-11-25_flood4_s14_fixpass.py (applies the fixes; reports MISSING when an earlier fix
         changed the text a later one expects)

What it does
------------
Reads each --fixes file (a JSON list, or an object with a "fixes" list) and prints, for every fix whose id is in
--ids (all fixes when --ids is omitted), the source file's basename, the id, the target file, every other field, then
the old and new texts verbatim between markers. Reads only; writes nothing.

Usage
-----
    python3 util/ad-hoc/2026-11-26_flood4_s16_show_fixes.py --fixes A.json [B.json ...] [--ids K3d C4 ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("fixes", [])
    return [fix for fix in data if isinstance(fix, dict)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--fixes", type=Path, nargs="+", required=True)
    parser.add_argument("--ids", nargs="*", default=None)
    args = parser.parse_args()
    wanted = set(args.ids) if args.ids else None
    shown = 0
    for path in args.fixes:
        for fix in _load(path):
            if wanted is not None and fix.get("id") not in wanted:
                continue
            shown += 1
            print(f"===== {path.parent.name}/{path.name} {fix.get('id')} {fix.get('file')}")
            for key, value in fix.items():
                if key in ("id", "file", "old", "new"):
                    continue
                print(f"{key}: {value}")
            print("--- OLD:")
            print(fix.get("old", ""))
            print("--- NEW:")
            print(fix.get("new", ""))
            print()
    print(f"shown: {shown}")
    return 0 if shown else 1


if __name__ == "__main__":
    sys.exit(main())
