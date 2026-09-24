#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-8 validation corrections (Lanes R8-A and R8-B).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-8 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round8.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round7_corrections.py (the pass this corrects)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the report archiver's key-material refusal and the shape check were
edited directly. Labels: A = R8-A, B = R8-B.

Round 8's one action was a tool fix: both lanes passed fake keys through the archiver's refusal with the header
allowed. The ledger's other findings were wording.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round8_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

SUBS = [
    # --- Instruments ---------------------------------------------------------------------------------------------
    (
        "Round list: the round-8 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7,8}.md`",
    ),
    (
        "Tools: round 8's pass",
        """rounds 3 to 7's passes
    are `…_round{3,4,5,6,7}_corrections.py`, likewise.""",
        """rounds 3 to 8's passes
    are `…_round{3,4,5,6,7,8}_corrections.py`, likewise.""",
    ),
    (
        "A1, B2: the sk- floor's history",
        """round 7 restored the bare `sk-` floor
    that round 6 had raised to 32 characters (Lane R7-B).""",
        """round 7 set the bare `sk-` floor to
    20 characters in all four shape-bearing tools (round 6 had raised the extractor's from 20 to 32, and the
    other three had used 32 since they were written; Lanes R7-B, R8-A and R8-B).""",
    ),
    (
        "A2, B1: the archiver's refusal, widened",
        """(Lane R7-B found that an allowed PEM header would
    also have passed a whole key).
""",
        """(Lane R7-B found that an allowed PEM header would
    also have passed a whole key). Round 8 widened that refusal, which had caught only a header, whitespace and
    base64 (Lanes R8-A and R8-B passed fake keys through it in six other forms): it now refuses any PEM END line,
    any base64 run of 40 or more characters within 400 characters after a PEM header, and any age identity
    with a body.
""",
    ),
    # --- Consensus record ----------------------------------------------------------------------------------------
    (
        "B3: round 6's check numbers, with the check as round 6 left it",
        "seven and three of the shapes `2026-09-24_secret_shape_check.py` tests (`sk-ant-…` keys among them).",
        """seven and three of the shapes `2026-09-24_secret_shape_check.py` tested as round 6 left it (`sk-ant-…`
      keys among them).""",
    ),
    (
        "B3: round 6's re-derivation, the same qualifier",
        """the widened secret shapes (`2026-09-24_secret_shape_check.py` fails 17 times on round
    5's tools and passes on these)""",
        """the widened secret shapes (`2026-09-24_secret_shape_check.py`, as round 6 left it, fails 17
    times on round 5's tools and passes on round 6's)""",
    ),
    (
        "A1, B2: round 7's record, the floor's history",
        """    - two tools, an action: the bare `sk-` floor round 6 had raised to 32 characters is back at 20 in all four
      shape-bearing tools, and the report archiver's `--allow-shape` is scoped to one agent's report and
      refuses key material after an allowed prefix.""",
        """    - two tools, an action: the bare `sk-` floor is now 20 in all four shape-bearing tools (round 6 had raised
      only the extractor's to 32; the other three had used 32 since they were written), and the report
      archiver's `--allow-shape` is scoped to one agent's report and refuses key material after an allowed
      prefix in its plainest form (round 8 widened that).""",
    ),
    (
        "B3: round 7's re-derivation, stated as it was done",
        "  - **Re-derived before applying (round 7):** both tool findings, by that check;",
        """  - **Re-derived before applying (round 7):** finding 4 by that check's 24-character case, and finding 5 by
    reading the pattern (its PEM and age alternatives match only a prefix), not by a run;""",
    ),
    (
        "Round 8's record",
        f"""  - **Round 7 changed actions, two tool fixes, and no number or disposition**, so §4 of {PROC} calls for a
    round 8 on these corrections.
""",
        f"""  - **Round 7 changed actions, two tool fixes, and no number or disposition**, so §4 of {PROC} called for a
    round 8 on these corrections.
  - **Round 8**: two lanes on the frozen `3297131f`. Lane R8-A re-derived round 7's claims from their
    artifacts; Lane R8-B attacked round 7's corrections. Both returned SOUND-WITH-FIXES. The replay of round 7's
    script is exact, cascor#678's events and the counts held, both scan windows regenerate byte-identical, and
    the scoped allow fails closed for another agent's allow, an unscoped allow and no allow.
  - **What round 8 changed:**
    - the report archiver's key-material refusal, an action: both lanes passed fake keys through it with the
      header allowed, in six forms besides round 7's (a JSON-escaped body, a blockquote, numbered lines, a
      backticked header, an encrypted PEM's header lines, a post-quantum age identity). It now refuses any PEM
      END line, any base64 run of 40 or more characters within 400 characters after a PEM header, and any age
      identity with a body. `2026-09-24_secret_shape_check.py` gained a case for each form, plus an END line
      alone, and fails those 7 on round 7's archiver;
    - wording: the `sk-` floor's history (round 6 raised only the extractor's), and round 6's numbers for the
      check, which were measured with the check as round 6 left it;
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round8_corrections.py`, with no hand
      edit to the ledger.
  - **Re-derived before applying (round 8):** each tool's first `sk-` floor, from git; the refusal's gaps, by the
    new cases. After the fix, round 6's and round 7's reports regenerate byte-identical under their scoped
    allows, and no file under `reports/e2e-canopy-2026-09-02/`, and no script in `util/ad-hoc/`, holds key
    material.
  - **Round 8 changed an action, a tool fix, and no number or disposition in the ledger**, so §4 of {PROC} calls
    for a round 9 on these corrections.
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
