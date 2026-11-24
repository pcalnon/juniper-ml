"""
Append clock-stamped lines to the D-14 code-lens validator's PROGRESS.txt.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> "<line>" ["<line>" ...]
Each argument becomes one line, stamped with the current UTC time (YYYY-MM-DDTHH:MM:SSZ).
"""

import datetime
import sys
from pathlib import Path

PROGRESS = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "d14-code-lens" / "PROGRESS.txt"


def main() -> int:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(PROGRESS, "a", encoding="utf-8") as handle:
        for line in sys.argv[1:]:
            handle.write(f"{stamp} {line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
