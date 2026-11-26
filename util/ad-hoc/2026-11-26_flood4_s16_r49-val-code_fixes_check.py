"""
Check a lens's fixes.json against the carrier: every "old" occurs exactly once in its file under the carrier's final/
tree, and the fixes apply in order; optionally write the patched files under an output tree for a test run.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26), a follow-up of ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16, code lens
    r49-val-code (its fixes.json)

Usage: python <this file> --fixes <fixes.json> --final <carrier final/ dir> [--write-into <tree>]
Prints one JSON line per fix (occurrences before it applies) and exits 1 when any fix does not occur exactly once.
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
    parser.add_argument("--write-into")
    args = parser.parse_args()
    with open(args.fixes, encoding="utf-8") as handle:
        fixes = json.load(handle)
    texts: dict[str, str] = {}
    ok = True
    for fix in fixes:
        path = fix["file"]
        if path not in texts:
            texts[path] = (Path(args.final) / path).read_text(encoding="utf-8")
        count = texts[path].count(fix["old"])
        print(json.dumps({"id": fix["id"], "file": path, "occurrences": count}))
        if count != 1:
            ok = False
            continue
        texts[path] = texts[path].replace(fix["old"], fix["new"], 1)
    if ok and args.write_into:
        for path, text in texts.items():
            target = Path(args.write_into) / path
            target.write_text(text, encoding="utf-8")
            print(json.dumps({"wrote": str(target)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
