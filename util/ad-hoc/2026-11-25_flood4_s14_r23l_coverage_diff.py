"""
Compare two coverage.py JSON reports file by file and print every file whose numbers differ.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23l: main's suite vs this change's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage: python3 <this file> A.json B.json
Prints, per differing file: statements, missing, branches, partial branches, the missing lines and the
missing branch arcs of A and of B.
"""

import json
import sys

FIELDS = ("num_statements", "missing_lines", "num_branches", "num_partial_branches", "percent_covered")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    a, b = _load(argv[1]), _load(argv[2])
    names = sorted(set(a["files"]) | set(b["files"]))
    differing = 0
    for name in names:
        sa = a["files"].get(name, {}).get("summary", {})
        sb = b["files"].get(name, {}).get("summary", {})
        if all(sa.get(f) == sb.get(f) for f in FIELDS):
            continue
        differing += 1
        print(f"== {name}")
        for f in FIELDS:
            print(f"   {f}: {sa.get(f)} -> {sb.get(f)}")
        for label, doc in (("A", a), ("B", b)):
            entry = doc["files"].get(name, {})
            print(f"   {label} missing lines: {entry.get('missing_lines')}")
            print(f"   {label} missing branches: {entry.get('missing_branches')}")
    print(f"files differing: {differing}")
    print(f"totals A: {a['totals'].get('percent_covered_display')}% partial {a['totals'].get('num_partial_branches')}; B: {b['totals'].get('percent_covered_display')}% partial {b['totals'].get('num_partial_branches')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
