#!/usr/bin/env python3
"""
Append one clock-stamped line to the validator's PROGRESS.txt (the stamp is read from the clock, never typed).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/BRIEF_S7_ADDENDUM.txt (section 3: stamp every PROGRESS.txt line from the clock)

Usage: 2026-11-12_flood4r2_val_d2-data_progress.py <PROGRESS.txt> <message words...>
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    target, words = Path(sys.argv[1]), sys.argv[2:]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {' '.join(words)}\n")
    print(stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
