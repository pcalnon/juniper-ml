#!/usr/bin/env python3
"""
Append one clock-stamped line to a scratch PROGRESS.txt (the time is read from the clock, never typed).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)

Usage: 2026-11-14_flood4r2_ml-docs_log.py <progress file> <message words ...>
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {' '.join(argv[1:])}\n"
    with Path(argv[0]).open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
