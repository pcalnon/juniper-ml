#!/usr/bin/env python3
"""
List every API-key-check implementation on each Juniper repository's origin/main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (flood-4 docs carrier: is the list of APIKeyAuth copies complete?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round-6 finding R6-F1)

WHY THIS EXISTS
The docs carrier lists which packages carry their own copy of the API-key check (and the first release of
each with the byte compare). Round 6 found a copy the list missed (juniper-canopy). A list that claims to be
complete must be checked against the code, not against the previous round's list: this greps every repo's
origin/main (fetched first) for an APIKeyAuth class and for compare_digest call sites.

Usage: 2026-11-07_flood4_api_key_copies_census.py [--root ~/Development/python/Juniper]
"""

import argparse
import os
import subprocess
import sys

REPOS = ["juniper-ml", "juniper-cascor", "juniper-data", "juniper-canopy", "juniper-recurrence",
         "juniper-cascor-worker", "juniper-cascor-client", "juniper-data-client", "juniper-deploy"]
PATTERN = r"class [A-Za-z]*APIKey[A-Za-z]*|compare_digest\("


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/Development/python/Juniper"))
    a = ap.parse_args()
    for repo in REPOS:
        path = os.path.join(a.root, repo)
        if not os.path.isdir(path):
            print("== %s: (no checkout)" % repo)
            continue
        subprocess.run(["git", "-C", path, "fetch", "-q", "origin"], capture_output=True)
        head = subprocess.run(["git", "-C", path, "rev-parse", "--short=8", "origin/main"], capture_output=True, text=True).stdout.strip()
        p = subprocess.run(["git", "-C", path, "grep", "-n", "-E", PATTERN, "origin/main", "--", "*.py", ":!*tests*", ":!*test_*"], capture_output=True, text=True)
        lines = [ln.replace("origin/main:", "", 1) for ln in p.stdout.splitlines()]
        print("== %s @ %s: %d hit(s)" % (repo, head, len(lines)))
        for ln in lines:
            print("   " + ln[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
