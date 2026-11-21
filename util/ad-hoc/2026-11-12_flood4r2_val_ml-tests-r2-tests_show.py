"""
Print parts of the ml-tests round-2 carrier's manifest.json for the tests-lens validator.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --manifest <path to manifest.json> --keys
    python3 <this file> --manifest <path> --section carried [--index N]
    python3 <this file> --manifest <path> --section files --brief
"""

import argparse
import json
import sys
from pathlib import Path


def _short(value, limit):
    text = json.dumps(value, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return text[:limit] + " ...(%d chars)" % len(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--keys", action="store_true")
    parser.add_argument("--section")
    parser.add_argument("--index", type=int)
    parser.add_argument("--brief", action="store_true")
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--fields", help="comma-separated keys to print per row of a list section")
    args = parser.parse_args(argv)

    with open(Path(args.manifest), encoding="utf-8") as fh:
        data = json.load(fh)

    if args.keys:
        for key, value in data.items():
            if isinstance(value, list):
                print("%s: list[%d]" % (key, len(value)))
            elif isinstance(value, dict):
                print("%s: dict[%d] keys=%s" % (key, len(value), list(value)[:12]))
            else:
                print("%s: %s" % (key, _short(value, 200)))
        return 0

    section = data[args.section]
    if args.fields and isinstance(section, list):
        names = args.fields.split(",")
        for row in section:
            print(" | ".join(str(row.get(name)) for name in names))
        return 0
    if args.index is not None:
        section = section[args.index]
        print(json.dumps(section, indent=1, ensure_ascii=False))
        return 0
    if args.brief and isinstance(section, list):
        for i, row in enumerate(section):
            print(i, _short(row, args.limit))
        return 0
    if args.brief and isinstance(section, dict):
        for key, row in section.items():
            print(key, _short(row, args.limit))
        return 0
    print(json.dumps(section, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
