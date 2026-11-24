"""
Print one finding (by id) of a validator's findings.json, for the tests-lens validator of the ml-tests carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --findings <findings.json> --id F6
"""

import argparse
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--findings", required=True)
    parser.add_argument("--id", required=True)
    args = parser.parse_args(argv)
    with open(args.findings, encoding="utf-8") as fh:
        data = json.load(fh)
    for finding in data.get("findings", []):
        if finding.get("id") == args.id:
            print(json.dumps(finding, indent=1, ensure_ascii=False))
            return 0
    print("no finding %s; ids: %s" % (args.id, [f.get("id") for f in data.get("findings", [])]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
