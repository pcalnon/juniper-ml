#!/usr/bin/env python3
"""
Apply a validation lens's exact old/new fixes (fixes.json) to working copies, reporting each as applied, missing or ambiguous.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 7 cleanup script, session 13: merging the code and claims lenses' fixes)
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- one-off (the ruling 7 script's fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_flood4_r7_cleanup.py; tmp/flood4/session13/val_code/fixes.json and
         tmp/flood4/session13/val_claims/fixes.json (the two lenses' outputs)

What it does
------------
Each fix is {"id", "file", "old", "new", ...}. The fix's file is located by its basename under --work (copies made
there first with --init FROM_DIR). A fix applies only when its old text occurs exactly once in the file as it stands
at its turn; otherwise it is reported MISSING (0) or AMBIGUOUS (>1) and left for a hand merge. --skip drops fixes by
id, or by ID@LINE for one fix of several sharing an id; --order is "list" (the file's order) or "bottom-up" (descending line, as a lens that built its fixes against the
original file applies them). Writes nothing outside --work; prints one line per fix and a summary.

Usage
-----
    python3 util/ad-hoc/2026-11-25_flood4_s13_r7_fixpass.py --work DIR [--init FROM_DIR --names A B ...] \
        --fixes FIXES.json [--order list|bottom-up] [--skip ID ...]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--init", type=Path, default=None, help="copy --names from this directory into --work first")
    parser.add_argument("--names", nargs="*", default=[])
    parser.add_argument("--fixes", type=Path, required=True)
    parser.add_argument("--order", choices=("list", "bottom-up"), default="list")
    parser.add_argument("--skip", nargs="*", default=[])
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.init:
        for name in args.names:
            shutil.copy2(args.init / name, args.work / name)
    with args.fixes.open(encoding="utf-8") as fh:
        fixes = json.load(fh)
    if args.order == "bottom-up":
        fixes = sorted(fixes, key=lambda f: -int(f.get("line") or 0))
    counts = {"APPLIED": 0, "MISSING": 0, "AMBIGUOUS": 0, "SKIPPED": 0}
    for fix in fixes:
        target = args.work / Path(fix["file"]).name
        if fix["id"] in args.skip or f"{fix['id']}@{fix.get('line')}" in args.skip:
            verdict = "SKIPPED"
        else:
            text = target.read_text(encoding="utf-8")
            n = text.count(fix["old"])
            if n == 1:
                target.write_text(text.replace(fix["old"], fix["new"], 1), encoding="utf-8")
                verdict = "APPLIED"
            else:
                verdict = "MISSING" if n == 0 else "AMBIGUOUS"
        counts[verdict] += 1
        print(f"{verdict:<9} {fix['id']:<6} {target.name}:{fix.get('line')}  {fix.get('why', '')[:90]}")
    print("summary: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return 0 if counts["MISSING"] == 0 and counts["AMBIGUOUS"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
