"""
Append one UTC-stamped checkpoint line to the validator's PROGRESS.txt (the session-5 addendum's checkpoint rule).

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_checkpoint.py "<what finished, and where its evidence is>"

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

SCRATCH = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "r10-data-client-s5"


def main() -> int:
    message = " ".join(sys.argv[1:]).strip()
    if not message:
        print(__doc__)
        return 2
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(SCRATCH / "PROGRESS.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {message}\n")
    print(f"{stamp} {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
