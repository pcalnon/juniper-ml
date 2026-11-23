"""
Append one clock-stamped line to one or more PROGRESS.txt files (the D-14 fix-up's checkpoint log).

The line is stamped from the UTC clock (``%Y-%m-%dT%H:%M:%SZ``), never from memory, and written to every file named
before ``--``, so the two carriers' logs carry the same milestone at the same second.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_progress.py <PROGRESS.txt> [<PROGRESS.txt> ...] -- <message words ...>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import datetime
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print("usage: progress.py <file> [<file> ...] -- <message>", file=sys.stderr)
        return 2
    cut = argv.index("--")
    files = [Path(name) for name in argv[:cut]]
    message = " ".join(argv[cut + 1 :]).strip()
    if not files or not message:
        print("usage: progress.py <file> [<file> ...] -- <message>", file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {message}\n"
    for path in files:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    print(line, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
