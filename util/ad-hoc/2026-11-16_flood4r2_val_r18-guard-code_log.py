"""
Append one UTC-stamped line to the r18-guard code lens's PROGRESS.txt (validator JL1).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py

Usage: python3 <this file> <progress file> <message ...>   (or "-" as the message to read it from stdin)
"""

import datetime
import sys
from pathlib import Path


def main(argv: list) -> int:
    path = Path(argv[0])
    message = sys.stdin.read().strip() if argv[1:] == ["-"] else " ".join(argv[1:])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a") as handle:
        handle.write("%s %s\n" % (stamp, message))
    print("%s logged %d chars" % (stamp, len(message)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
