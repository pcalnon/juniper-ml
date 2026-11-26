"""
Append one UTC-stamped line to a builder's PROGRESS.txt (flood-4 session 14, builder r27).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage:
    python3 <this file> <progress file> <text...>

The stamp is the current UTC time in the form `date -u +%Y-%m-%dT%H:%M:%SZ` prints. The words after the file are joined
with single spaces. Nothing else is written.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: <progress file> <text...>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {' '.join(sys.argv[2:])}\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
