"""
Print each draft's added lines in the five shared documents, marking whether each is in the landed tree verbatim
(claims lens, session 8). Reads <drafts>/<N>/shared_adds.json written by the drafts helper.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-claims_drafts.py
"""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the drafts' shared-document additions.")
    parser.add_argument("--drafts", required=True, type=Path)
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--width", type=int, default=170)
    parser.add_argument("--skip-path", action="append", default=[])
    parser.add_argument("prs", nargs="+", type=int)
    args = parser.parse_args()
    for number in args.prs:
        with (args.drafts / str(number) / "shared_adds.json").open() as handle:
            rows = json.load(handle)
        print(f"######## #{number}")
        for row in rows:
            if row["path"] in args.skip_path:
                continue
            landed = (args.tree / row["path"]).read_text(errors="replace").splitlines()
            landed_set = set(landed)
            print(f"  == {row['path']} (+{len(row['added'])} -{len(row['removed'])})")
            for line in row["added"]:
                mark = "SAME" if line in landed_set else "----"
                print(f"   {mark} {line[: args.width]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
