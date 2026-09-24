#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-9 validation corrections (Lanes R9-A and R9-B).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-9 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round9.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round8_corrections.py (the pass this corrects)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the report archiver's key_material() and the shape check were edited
directly. Labels: A = R9-A, B = R9-B.

Round 9's one action was a tool fix: round 8 had REPLACED round 7's PEM form instead of adding to it, so a
header, whitespace and a 20-39-character body passed; round 9 keeps both.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round9_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

SUBS = [
    # --- Instruments ---------------------------------------------------------------------------------------------
    (
        "Round list: the round-9 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7,8}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7,8,9}.md`",
    ),
    (
        "Tools: round 9's pass",
        """rounds 3 to 8's passes
    are `…_round{3,4,5,6,7,8}_corrections.py`, likewise.""",
        """rounds 3 to 9's passes
    are `…_round{3,4,5,6,7,8,9}_corrections.py`, likewise.""",
    ),
    (
        "A2, B1: what round 7 refused, and round 9 keeping it",
        """    also have passed a whole key). Round 8 widened that refusal, which had caught only a header, whitespace and
    base64 (Lanes R8-A and R8-B passed fake keys through it in six other forms): it now refuses any PEM END line,
    any base64 run of 40 or more characters within 400 characters after a PEM header, and any age identity
    with a body.""",
        """    also have passed a whole key). That refusal caught a PEM header followed by whitespace and 20 or more base64
    characters, and a whole classic age key; Lanes R8-A and R8-B passed fake keys through it in six other forms.
    Round 8 replaced it rather than adding to it, which let a header followed by a 20-39-character body pass, so
    round 9 kept round 7's form as well (Lane R9-B). It now refuses any PEM END line; a PEM header followed by
    whitespace and 20 or more base64 characters; any base64 run of 40 or more characters within 400 characters
    after a PEM header; and any age identity with a body.""",
    ),
    # --- Consensus record ----------------------------------------------------------------------------------------
    (
        "A1, B2: round 7's count, measured with the check as round 7 left it",
        """      prefix in its plainest form (round 8 widened that). `2026-09-24_secret_shape_check.py` gained the cases that
      see both, and fails 14 times on round 6's tools;""",
        """      prefix in its plainest form (rounds 8 and 9 widened that). `2026-09-24_secret_shape_check.py` gained the
      cases that see both and, as round 7 left it, fails 14 times on round 6's tools;""",
    ),
    (
        "B1: round 8's record, what it dropped and hid",
        """      identity with a body. `2026-09-24_secret_shape_check.py` gained a case for each form, plus an END line
      alone, and fails those 7 on round 7's archiver;""",
        """      identity with a body. `2026-09-24_secret_shape_check.py` gained a case for each form, plus an END line
      alone, and fails those 7 on round 7's archiver. Round 8 also dropped round 7's own PEM form and lengthened
      the check's case for it from a 39- to a 48-character body, which hid the drop; round 9 restored both;""",
    ),
    (
        "Round 9's record",
        f"""  - **Round 8 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} calls
    for a round 9 on these corrections.
""",
        f"""  - **Round 8 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} called
    for a round 9 on these corrections.
  - **Round 9**: two lanes on the frozen `04db8614`. Lane R9-A re-derived round 8's claims from their
    artifacts; Lane R9-B attacked round 8's corrections. Both returned SOUND-WITH-FIXES. The replay of round 8's
    script is exact; every tool's `sk-` floor history, every form `key_material` names (R9-A tested 21 fakes,
    R9-B more), the check's "fails those 7", the three reports' regeneration and the key-material sweep all
    held.
  - **What round 9 changed:**
    - the report archiver, an action: round 8's `key_material` had replaced round 7's PEM form, so a header, whitespace
      and a 20-39-character body passed with the header allowed (Lane R9-B); it now keeps that form beside
      round 8's, and `2026-09-24_secret_shape_check.py` has a 39-character case again, which fails on round 8's
      archiver;
    - wording: round 7's "fails 14 times" (measured with the check as round 7 left it), and what round 7's
      refusal caught (a classic age key too);
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round9_corrections.py`, with no hand
      edit to the ledger.
  - **Re-derived before applying (round 9):** the dropped form, by the 39-character case, which fails once on
    round 8's archiver and passes on round 9's; round 7's own check passes on round 9's tools. After the fix,
    round 6's, 7's and 8's reports regenerate byte-identical under their scoped allows, and no file under
    `reports/e2e-canopy-2026-09-02/`, and no script in `util/ad-hoc/`, holds key material.
  - **Round 9 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} calls
    for a round 10 on these corrections.
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
