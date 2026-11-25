"""
Print two runs of the r23l-val-claims HTTP answers probe (main and the fix) side by side, field by field.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, claims lens r23l-val-claims)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_flood4_s14_r23l-val-claims_http_answers.py;
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Rows are matched by their "row" text, in the first file's order. Each field is printed once when both runs agree
("=") and twice when they differ ("main" then "fix"), so every changed answer is one "!=" line.

Usage: python3 <this file> MAIN.json FIX.json
"""

import json
import sys


def _flat(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _flat(item, f"{prefix}.{key}" if prefix else key)
    else:
        yield prefix, value


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        main_run = json.load(handle)
    with open(sys.argv[2], encoding="utf-8") as handle:
        fix_run = json.load(handle)
    print(f"main: {main_run['header']['manager_sha256'][:16]} {main_run['header']['python'].split()[0]} errors={main_run['errors']}")
    print(f"fix:  {fix_run['header']['manager_sha256'][:16]} {fix_run['header']['python'].split()[0]} errors={fix_run['errors']}")
    fix_rows = {row["row"]: row for row in fix_run["rows"]}
    changed = 0
    for row in main_run["rows"]:
        name = row["row"]
        other = fix_rows.get(name, {})
        print(f"\n== {name}")
        main_fields = dict(_flat({k: v for k, v in row.items() if k != "row"}))
        fix_fields = dict(_flat({k: v for k, v in other.items() if k != "row"}))
        for key in list(main_fields) + [k for k in fix_fields if k not in main_fields]:
            a = main_fields.get(key, "<absent>")
            b = fix_fields.get(key, "<absent>")
            if a == b:
                print(f"   =  {key}: {a!r}")
            else:
                changed += 1
                print(f"   != {key}: main {a!r}  |  fix {b!r}")
    print(f"\nfields that differ: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
