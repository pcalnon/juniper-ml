"""
Append UTC-stamped lines to a PROGRESS.txt (one line per argument).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage:
  python -I <this file> PROGRESS_FILE "line one" ["line two" ...]
"""

from __future__ import annotations

import datetime
import pathlib
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    target = pathlib.Path(argv[1])
    with target.open("a", encoding="utf-8") as fh:
        for line in argv[2:]:
            stamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            fh.write(f"{stamp} {line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
