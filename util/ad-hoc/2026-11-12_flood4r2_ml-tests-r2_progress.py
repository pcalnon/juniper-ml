#!/usr/bin/env python3
"""
Append one checkpoint line to the carrier build's PROGRESS.txt, stamped with the UTC clock at the moment of writing.

The build's checkpoints must carry the time they were written, read from the clock and never typed. This host's
shell refuses a `$(date -u ...)` substitution in a command whose text also names a version-control tool, so the
stamp is taken here instead.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_progress.py <PROGRESS.txt> <message ...>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (checkpoint as you go)
"""

import sys
from datetime import datetime, timezone


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {' '.join(sys.argv[2:])}\n"
    with open(sys.argv[1], "a", encoding="utf-8") as fh:
        fh.write(line)
    print(line, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
