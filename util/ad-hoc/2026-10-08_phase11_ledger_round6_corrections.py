#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 6's correction pass on the ledger's Phase 11: the final wording pass, which ends its review.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` as frozen for round 6
(``da08f639``, round 5's pass applied to ``684d70bc``). Round 6's reports are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md``. Neither lane found
anything that changes a number, a disposition or an action, so under §4 of
``notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`` the review ends at round 6,
and this pass corrects the records only. Every substitution is anchored to occur exactly once.

Usage:
    python3 util/ad-hoc/2026-10-08_phase11_ledger_round6_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

ROUND6_RECORD = """

- **Round 6**: two lanes on the frozen `da08f639`, briefed on round 5's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane11R6_phase11_ledger_brief.md`. It also kept them from assessing any
  rating against canopy's manual, which is item 26's work. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md`.
  - Lane 11-R6A re-derived the pass's claims and replayed it on `684d70bc`: `da08f639` byte for byte, with no hand
    edit. Lane 11-R6B was adversarial on the pass, and replayed it too.
  - Both found item 26 and the Matrix in agreement, one rating each for F-CANOPY-065 and F-CANOPY-068 under every
    ruling, the counts and the triage unchanged, and the CodeQL pass's third run changing nothing a probe computes.
  - Their own probes are archived as `util/ad-hoc/2026-10-08_phase11_r6_{a,b}_*.py` (17 files) by
    `util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py --round 6`. The prescreen predicts no alert on them.
- **Verdicts.** Both returned SOUND-WITH-FIXES, with the same three NITs, each a misstatement in these records.
  Neither found anything that changes a number, a disposition or an action, so under §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` **the review ends at round 6.**
- **What round 6 changed**, in the records only:
  - round 3's record no longer says that round 4 restored Phase 10's own wording;
  - round 5's record credits F-CANOPY-013's reason, changed in the Matrix, to Lanes 11-R5A and 11-R5B, and the
    "condition" wording to Lane 11-R5B alone;
  - round 4's Slips: Lane 11-R4B's runs wrote all three bytecode files, the release trace's cache included, and
    Lane 11-R4A's wrote none. Round 5 had taken Lane 11-R4A's own attribution without re-deriving it.
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-08_phase11_ledger_round6_corrections.py`,
    SUB_COUNT substitutions in the ledger.
- **Re-derived by the orchestrator before applying:** the only bytecode files written in the worktree during round
  4, their modification times (10:51:23.39Z, and 10:59:24.05Z for two), against the round-4 lanes' command times,
  Lane 11-R4B's run of the rederive script at 10:51:23.28Z and its probe run at 10:59:23.95Z.
- **Slips.** Neither lane reported one."""

SUBS = [
    # --- round 3's record: round 4 restored Phase 10's question in F-CANOPY-065's words (R6A F1, R6B F1) ---
    (
        "(round 4 restored Phase 10's wording)",
        "(round 4 restored Phase 10's question in F-CANOPY-065's wording, \"shipped\" included; round 5 Phase 10's own\n"
        "    words, in the Unresolved bullet)",
    ),
    # --- round 4's Slips: Lane 11-R4B wrote all three bytecode files (R6A F3, R6B F3) ---
    (
        "- **Slips.** Lane 11-R4A ran the repo's rederive script once without `-B`, which wrote one git-ignored bytecode\n"
        "  file into the worktree; no tracked file changed. Lane 11-R4B ran one canopy `git log` whose format printed author\n"
        "  dates, with no name or e-mail, and one probe without `-B`, which wrote two git-ignored bytecode files into the\n"
        "  worktree (Lane 11-R5A). Neither printed a secret or an address.",
        "- **Slips.** Lane 11-R4B ran its Python without `-B`, and two of its runs wrote three git-ignored bytecode files\n"
        "  into the worktree: the release trace's cache, by its run of the rederive script at 10:51:23Z, and two by one\n"
        "  probe at 10:59:24Z. Lane 11-R4A also ran Python without `-B` but wrote none: its report took the release trace's\n"
        "  cache for its own, and round 5 copied that without re-deriving it (round 6, Lanes 11-R6A and 11-R6B). No tracked\n"
        "  file changed. Lane 11-R4B also ran one canopy `git log` whose format printed author dates, with no name or\n"
        "  e-mail. Neither printed a secret or an address.",
    ),
    # --- round 5's record: where the F-CANOPY-013 credit changed, and who raised "condition" (R6A F2, R6B F2) ---
    (
        "    first, and the Matrix's F-CANOPY-013 bullet names the manual's step 6 and canopy#532 (Lanes 11-R5A and\n"
        "    11-R5B);",
        "    first, and the Matrix's F-CANOPY-013 bullet names the manual's step 6 and canopy#532, and credits the note's\n"
        "    reason to Lane 11-R4A (Lanes 11-R5A and 11-R5B);",
    ),
    (
        "  - round 4's record: its first-limb bullet no longer calls the shipped wording Phase 10's, and calls the second\n"
        "    limb a condition, not an exception (Lanes 11-R5A and 11-R5B); its Verdicts give Lane 11-R4B's first-limb claim;\n"
        "    its credits for T-mode's unrecorded effect and for F-CANOPY-013's reason now name the lanes that raised them;\n"
        "    and its Slips record Lane 11-R4B's two bytecode files (Lane 11-R5A);",
        "  - round 4's record: its first-limb bullet no longer calls the shipped wording Phase 10's (Lanes 11-R5A and\n"
        "    11-R5B), and calls the second limb a condition, not an exception (Lane 11-R5B); its Verdicts give Lane 11-R4B's\n"
        "    first-limb claim; its credit for T-mode's unrecorded effect names the lane that raised it; and its Slips record\n"
        "    Lane 11-R4B's bytecode files (Lane 11-R5A; round 6 corrected the count and the attribution);",
    ),
    # --- the round-6 record, after round 5's ---
    (
        "  - canopy#532, merged on 2026-08-28 as `359e1bf7`.\n- **Slips.** Neither lane reported one.",
        "  - canopy#532, merged on 2026-08-28 as `359e1bf7`.\n- **Slips.** Neither lane reported one.ROUND6_RECORD",
    ),
]


def apply(text: str, subs: list) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"SUB anchor found {n} times: {old[:100]!r}")
        text = text.replace(old, new)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    if "- **Round 5**: two lanes on the frozen `684d70bc`" not in before or "- **Round 6**: two lanes on the frozen `da08f639`" in before:
        raise SystemExit("this is not the round-6 freeze (da08f639)")
    after = apply(before, SUBS)
    record = ROUND6_RECORD.replace("SUB_COUNT", str(len(SUBS)))
    if after.count("ROUND6_RECORD") != 1:
        raise SystemExit("round-6 record placeholder not found exactly once")
    after = after.replace("ROUND6_RECORD", record)
    print(f"ledger: {len(SUBS)} substitutions, {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
