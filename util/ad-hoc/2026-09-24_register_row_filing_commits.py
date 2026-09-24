#!/usr/bin/env python3
"""
Name the commit that FILED each post-primer defect-register row, for a provenance count.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- read-only
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Section 4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` counts the post-primer
rows whose provenance differs from the round-37 handoff validation, and several rows state no
provenance of their own. Two validation lanes of juniper-ml#2074 disagreed about which rows the count
misses. This settles it from history: for each id it finds the oldest commit on the given ref whose
register first contains the id's table row (`| <id> `), via `git log -S`, and prints its date and
subject.

Usage: python3 util/ad-hoc/2026-09-24_register_row_filing_commits.py [--ref origin/main] ID...
"""

from __future__ import annotations

import argparse
import subprocess

REGISTER = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("ids", nargs="+")
    args = ap.parse_args()
    for ident in args.ids:
        out = subprocess.run(["git", "log", "--reverse", "--format=%h %cI %s", "-S", f"| {ident} ", args.ref, "--", REGISTER], check=True, capture_output=True, text=True).stdout.split("\n")
        print(f"{ident:15} {out[0][:150] if out and out[0] else '(no commit adds its row)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
