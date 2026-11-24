"""
Count how often each proposed text fix's OLD string occurs in its target file, and that the NEW string is not there yet.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

The spec is a JSON list of {finding, file, old, new[, expected_count]}; `file` starts with COPY/ (the validator's
copy of the repo) or DELIVERABLES/ (the builder's text files). Reads only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--deliverables", required=True, type=Path)
    args = parser.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    roots = {"COPY": args.copy, "DELIVERABLES": args.deliverables}
    bad = 0
    for item in spec:
        root, _, rel = item["file"].partition("/")
        text = (roots[root] / rel).read_text(encoding="utf-8")
        expected = item.get("expected_count", 1)
        old_count = text.count(item["old"])
        new_count = text.count(item["new"])
        ok = old_count == expected and new_count == 0
        bad += 0 if ok else 1
        print(f"{'ok ' if ok else 'BAD'} {item['finding'][:40]:40} {item['file']:48} old x{old_count} (want {expected}), new x{new_count}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
