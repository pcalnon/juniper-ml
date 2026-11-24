"""
Check the validator's text_fixes.json: every ``old`` occurs exactly once in the file it names, and differs from ``new``.

"COPY/<repo path>" is read from the carrier worktree (the validator's copy holds the same bytes) and
"DELIVERABLES/<name>" from the carrier's tmp/flood4-fix/r10-gitleaks-port/. Nothing is written or edited.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_check_text_fixes.py <text_fixes.json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-data-client--ci--gitleaks-pr-commit-scan--20261111-1914--3cd855d1"
DELIVERABLES = CARRIER / "tmp" / "flood4-fix" / "r10-gitleaks-port"


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as fh:
        fixes = json.load(fh)
    bad = 0
    for index, fix in enumerate(fixes):
        kind, _, rel = fix["file"].partition("/")
        path = (CARRIER if kind == "COPY" else DELIVERABLES) / rel
        if kind not in ("COPY", "DELIVERABLES") or not path.is_file():
            print(f"[{index}] {fix['file']}: no such file")
            bad += 1
            continue
        count = path.read_text(encoding="utf-8").count(fix["old"])
        verdict = "ok" if count == 1 and fix["old"] != fix["new"] else "BAD"
        bad += verdict != "ok"
        print(f"[{index}] {verdict} {fix['finding']} {fix['file']}: old occurs {count} time(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
