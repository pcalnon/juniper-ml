"""
Check that every fixes.json entry's "old" text occurs exactly once in the carrier's file, and optionally write the
carrier files with all fixes applied (in order) to a directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code

Usage:
    python <this file> --fixes <fixes.json> --final <carrier final/ dir> [--write <dir>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixes", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--write", default="")
    parser.add_argument("--only-index", default="", help="comma-separated fixes.json indexes to apply (default: all)")
    args = parser.parse_args()
    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    if args.only_index:
        keep = {int(x) for x in args.only_index.split(",")}
        fixes = [fix for index, fix in enumerate(fixes) if index in keep]
    texts: dict[str, str] = {}
    ok = True
    for index, fix in enumerate(fixes):
        rel = fix["file"]
        original = (Path(args.final) / rel).read_text(encoding="utf-8")
        count = original.count(fix["old"])
        current = texts.setdefault(rel, original)
        applied = current.count(fix["old"]) == 1
        if applied:
            texts[rel] = current.replace(fix["old"], fix["new"])
        ok = ok and count == 1 and applied
        print(json.dumps({"index": index, "id": fix["id"], "file": rel, "old_count_in_carrier": count, "applied_in_sequence": applied}))
    if args.write:
        for rel, text in texts.items():
            dest = Path(args.write) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            print(json.dumps({"wrote": str(dest)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
