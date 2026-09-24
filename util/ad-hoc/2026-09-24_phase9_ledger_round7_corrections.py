#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-7 validation corrections (Lanes R7-A and R7-B).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-7 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round7.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round6_corrections.py (the pass this corrects)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the four tools' secret shapes, the report archiver's --allow-shape and
the shape check were edited directly. Labels: A = R7-A, B = R7-B.

Round 7's ledger findings were wording only; its two actions were tool fixes (B4, B5).

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round7_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

SUBS = [
    # --- "Who" ---------------------------------------------------------------------------------------------------
    (
        "B3: cascor#678 was never a draft either, and its arm was on 09-23",
        """It added that cascor#678 was
      armed the same way that morning, and asked whether that sweeper was the owner's.""",
        """It added that cascor#678 was
      armed the same way earlier (its only arm was at 13:32:10Z on 09-23, and it too was never a draft), and
      asked whether that sweeper was the owner's.""",
    ),
    # --- Instruments ---------------------------------------------------------------------------------------------
    (
        "Round list: the round-7 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6,7}.md`",
    ),
    (
        "B4, B5: the tools round 7 fixed",
        """    used it for the owner's answer ("Who", above). Round 6 widened its secret shapes, and the launch scan's and
    the archive tool's, after Lane R6-B found `sk-ant-…` keys passing it; `2026-09-24_secret_shape_check.py`
    tests all three against constructed fake values, both ways.
""",
        """    used it for the owner's answer ("Who", above). Round 6 widened its secret shapes, and the launch scan's and
    the archive tool's, after Lane R6-B found `sk-ant-…` keys passing it; round 7 restored the bare `sk-` floor
    that round 6 had raised to 32 characters (Lane R7-B). `2026-09-24_secret_shape_check.py` tests all three,
    and the report archiver, against constructed fake values, both ways.
  - `2026-09-23_archive_consensus_reports_by_round.py`, which archives the lanes' reports verbatim: round 6 gave
    it `--allow-shape` for a reviewed literal, and round 7 scoped each allow to one agent's report, refused key
    material after an allowed prefix, and widened its shapes (Lane R7-B found that an allowed PEM header would
    also have passed a whole key).
""",
    ),
    (
        "Tools: round 7's pass",
        """rounds 3 to 6's passes
    are `…_round{3,4,5,6}_corrections.py`, likewise.""",
        """rounds 3 to 7's passes
    are `…_round{3,4,5,6,7}_corrections.py`, likewise.""",
    ),
    # --- Consensus record ----------------------------------------------------------------------------------------
    (
        "B1: round 6's record, two numbers did change",
        "count, time and source line round 5 added held, including the signing key of the 03:00Z commits.",
        """count, time and source line round 5 added held except two, the question's time and the count of drafts
    (R6-A's finding 1, R6-B's finding 2); the signing key of the 03:00Z commits held too.""",
    ),
    (
        "A1, B2: round 6's record, without the unsupported 'only'",
        """    - "whatever cascor reports": F-CANOPY-055 freezes the bar only on a page slower than its tick, and the bar
      reads Stopped during a replay through its own `else` either way;""",
        """    - "whatever cascor reports": F-CANOPY-055 freezes the bar on some pages, not on every page (whether only on
      pages slower than its tick is unmeasured), and the bar reads Stopped during a replay through its own
      `else` either way;""",
    ),
    (
        "Round 7's record",
        f"""  - **Round 6 changed a disposition, numbers and an action**, so §4 of {PROC} calls for a round 7 on these
    corrections.
""",
        f"""  - **Round 6 changed a disposition, numbers and an action**, so §4 of {PROC} called for a round 7 on these
    corrections.
  - **Round 7**: two lanes on the frozen `129f4880`. Lane R7-A re-derived round 6's claims from their
    artifacts; Lane R7-B attacked round 6's corrections. Both returned SOUND-WITH-FIXES. The replay of round 6's
    script is exact, the answer's scope and every ready and arm time re-derive from the transcript and the
    timelines, and the follow-up's rebase, the shape check and both scan windows reproduce.
  - **What round 7 changed:**
    - in the ledger, wording only: round 6's record said every round-5 number held and that F-CANOPY-055 freezes
      the bar only on slow pages, and "Who" said cascor#678 was armed "the same way that morning" (it too was
      never a draft, and its arm was on 09-23);
    - two tools, an action: the bare `sk-` floor round 6 had raised to 32 characters is back at 20 in all four
      shape-bearing tools, and the report archiver's `--allow-shape` is scoped to one agent's report and
      refuses key material after an allowed prefix. `2026-09-24_secret_shape_check.py` gained the cases that
      see both, and fails 14 times on round 6's tools;
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round7_corrections.py`, with no hand
      edit to the ledger.
  - **Re-derived before applying (round 7):** both tool findings, by that check; cascor#678's events (no draft
    or ready event, one arm at 13:32:10Z on 09-23). After the fixes, both scan windows regenerate
    byte-identical, all 36 archived tmpfs files pass, round 6's report regenerates byte-identical under the
    scoped allow, and every secret shape in the archived reports and briefs is a reviewed quote (round 6's PEM
    header, round 7's age-key prefix).
  - **Round 7 changed actions, two tool fixes, and no number or disposition**, so §4 of {PROC} calls for a
    round 8 on these corrections.
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
