"""
For each draft, compare its docs/REFERENCE.md description line for a suite with the landed tree's line for the
same suite, word by word (claims lens, session 8). Reads <drafts>/<N>/shared_adds.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-claims_drafts.py
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ENTRY = re.compile(r"^\s*- `(tests/[^`]+\.py)`")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare REFERENCE description lines draft vs landed.")
    parser.add_argument("--drafts", required=True, type=Path)
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--path", default="docs/REFERENCE.md")
    parser.add_argument("prs", nargs="+", type=int)
    args = parser.parse_args()
    landed = (args.tree / args.path).read_text(errors="replace").splitlines()
    for number in args.prs:
        with (args.drafts / str(number) / "shared_adds.json").open() as handle:
            rows = json.load(handle)
        for row in rows:
            if row["path"] != args.path:
                continue
            for line in row["added"]:
                match = ENTRY.match(line)
                if not match:
                    if not line.startswith("python3 -m unittest"):
                        print(f"#{number} NON-ENTRY ADD: {line[:300]}")
                    continue
                suite = match.group(1)
                candidates = [text for text in landed if ENTRY.match(text) and ENTRY.match(text).group(1) == suite]
                print(f"#{number} {suite}: landed entries {len(candidates)}")
                for text in candidates:
                    if text == line:
                        print("   identical")
                        continue
                    words = list(difflib.ndiff(line.split(" "), text.split(" ")))
                    changed = [w for w in words if w[:1] in "+-"]
                    print("   draft->landed word changes:", " ".join(changed)[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
