#!/usr/bin/env python
"""Record the Phase 9 ledger's round-10 validation, which terminated the review (Lanes R10-A and R10-B).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-10 record)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round10.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round9_corrections.py (the pass round 10 reviewed)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Round 10 changed no
number, disposition or action: R10-A returned SOUND with no findings, and R10-B's one LOW finding was a code
comment in util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py, corrected there directly. So this pass
only records the round and the review's termination under section 4 of the consensus procedure.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round10_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

SUBS = [
    (
        "Round list: the round-10 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7,8,9}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7,8,9,10}.md`",
    ),
    (
        "Tools: round 10's record",
        """rounds 3 to 9's passes
    are `…_round{3,4,5,6,7,8,9}_corrections.py`, likewise.""",
        """rounds 3 to 10's
    passes are `…_round{3,4,5,6,7,8,9,10}_corrections.py`, likewise.""",
    ),
    (
        "Round 10's record: the review terminated",
        f"""  - **Round 9 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} calls
    for a round 10 on these corrections.
""",
        f"""  - **Round 9 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} called
    for a round 10 on these corrections.
  - **Round 10**: two lanes on the frozen `b0eb4ac1`. Lane R10-A re-derived round 9's claims from their
    artifacts and returned SOUND with no findings; its tests of `key_material` refused every one of about
    17,000 fake keys in the forms the ledger names. Lane R10-B attacked round 9's corrections and returned
    SOUND-WITH-FIXES with one LOW finding: a comment in the report archiver that round 9 had made false, which
    was corrected in the tool directly.
  - **Round 10 changed no number, disposition or action, so under §4 of {PROC} the review of this phase's
    text terminated at round 10.** This pass (`util/ad-hoc/2026-09-24_phase9_ledger_round10_corrections.py`)
    records it and changes nothing else.
""",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    text = LEDGER.read_text(encoding="utf-8")
    bad = []
    for why, old, new in SUBS:
        n = text.count(old)
        if n != 1:
            bad.append((n, why, old[:90]))
            continue
        text = text.replace(old, new)
    if bad:
        for n, why, head in bad:
            print(f"REFUSED: {n} matches for [{why}]: {head!r}", file=sys.stderr)
        return 1
    if not args.dry_run:
        LEDGER.write_text(text, encoding="utf-8")
    print(f"{'would apply' if args.dry_run else 'applied'} {len(SUBS)} substitutions to {LEDGER.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
