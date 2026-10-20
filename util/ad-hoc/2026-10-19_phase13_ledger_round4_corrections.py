#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-19
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md
# ---------------------------------------------------------------------------
"""Round 4's correction pass on the ledger's Phase 13 and the files that land with it: wording and the records only.

Applied to the files as frozen for round 4 (local commit ``369863cf``). Round 4's two reports are archived verbatim
in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round4.md``. Neither lane found
anything that changes a number, a disposition or an action, so the review ended at round 4; this pass applies their
wording fixes, appends the round-4 record and fills the handoff's ``**Consensus**`` line. Every substitution is
anchored to occur exactly once in its file.

Usage:
    python3 util/ad-hoc/2026-10-19_phase13_ledger_round4_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md"
PARENT = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md"

ROADMAP_NAME = "JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"
AUDIT_NAME = "JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"

LEDGER_SUBS = [
    # --- The design note's correction: the site count and the theme lines (R4A F1/F6, R4B F1/F6) ---
    (
        "13-R3B). With the four sites in three documents corrected or pointed at the correction, no document this phase\n"
        "or its lanes read records the stream as shipped without it, and the first limb reaches F-CANOPY-057 through none\n"
        "of them; a plan none of them read may still, which item 26's second step would find.",
        "13-R3B). With every site that recorded the stream as shipped corrected or pointed at the correction, three\n"
        "sections corrected (the design note's status block, the roadmap's §28.1, the audit's §5.2) and four restatements\n"
        "pointed at them (the roadmap's CAN-015 row; the audit's §5.2 Status delta, §8.1 and §11.7 rows), no document this\n"
        "phase or its lanes read records the stream as shipped without it, and the first limb reaches F-CANOPY-057\n"
        "through none of them; the audit's theme lines (`:13`, `:21`, `:248`, `:353`), which name no sub-task, stand with\n"
        "its §5.1 line (round 4, Lanes 13-R4A and 13-R4B). A plan none of them read may still, which item 26's second step\n"
        "would find.",
    ),
    # --- Matrix effect (R4A F1, R4B F1) ---
    (
        "    the four sites in three documents that recorded F-CANOPY-057's stream as shipped now corrected or pointed at\n"
        "    the correction: 9 open P1\n",
        "    every site that recorded F-CANOPY-057's stream as shipped now corrected or pointed at the correction (three\n"
        "    sections corrected, four restatements pointed): 9 open P1\n",
    ),
    # --- Still owed (R4A F2, R4B F2) ---
    (
        "  Of the findings Phase 11 named, F-CANOPY-065 is the one the ruling moves; the design note, the V7 roadmap's\n"
        "  §28.1 and CAN-015 row and the 2026-05-05 audit's §5.2 carry the dated correction, so F-CANOPY-057 is reached\n"
        "  through none of them, and the step should say so for any other plan it reads.",
        "  Of the findings Phase 11 named, F-CANOPY-065 is the one the ruling moves; the design note, the V7 roadmap's\n"
        "  §28.1 and the 2026-05-05 audit's §5.2 carry the dated correction, and the roadmap's CAN-015 row and the audit's\n"
        "  three restatements point at it, so F-CANOPY-057 is reached through none of them, and the step should say so for\n"
        "  any other plan it reads.",
    ),
    # --- Sources read (R4A F5) ---
    (
        "  compare of `main` with `dbc25277`. In this repo, after rounds 1 and 2: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  and the 2026-05-05 audit's §5.1, §5.2 and §11.4 (named under \"The design note's correction\").",
        "  compare of `main` with `dbc25277`. In this repo, after rounds 1 to 3: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  and the 2026-05-05 audit's §5.1, §5.2, §8.1, §11.4 and §11.7 (named under \"The design note's correction\").",
    ),
    # --- Round 3's record: what each place says, the omitted hunk, the credits (R4A F3/F4, R4B F4/F5) ---
    (
        "    the Status delta under §5.2, the §8.1 row and the §11.7 row); the Summary, F-CANOPY-057's Status bullet, \"The\n"
        "    design note's correction\" and the Matrix effect say \"corrected or pointed at the correction\", \"four sites in three\n"
        "    documents\", and that the CAN-015 row carries a pointer, not the note (Lanes 13-R3A and 13-R3B);\n"
        "  - the handoff's landing trap names the apply script and the three correction passes, in that order (Lane 13-R3B);\n",
        "    the Status delta under §5.2, the §8.1 row and the §11.7 row) (Lane 13-R3B); the Summary and F-CANOPY-057's\n"
        "    Status bullet say that every site carries the correction or a pointer to it and that the CAN-015 row is pointed\n"
        "    at it, and \"The design note's correction\" and the Matrix effect said \"four sites in three documents corrected\n"
        "    or pointed at the correction\" (Lanes 13-R3A and 13-R3B; round 4 recounted the sites);\n"
        "  - the handoff's landing trap names the apply script and the three correction passes, in that order, and its\n"
        "    \"Changed by this session\" audit line names round 3's pointers (Lane 13-R3B);\n",
    ),
    (
        "    the corrected documents and the counts only; 10 and 10 remains by the F-CANOPY-067 dissent and by the F-CANOPY-049\n"
        "    counter-reading; round 2's change list gains the hunks it omitted (the \"Sources read\" sentence, round 1's\n"
        "    rewritten \"Not applied\" and its parenthetical, the handoff's PR-contents sentence, audit grep and two \"Changed by\n"
        "    this session\" lines, item 4's release tags) (Lanes 13-R3A and 13-R3B);",
        "    the corrected documents and the counts only; 10 and 10 remains by the F-CANOPY-067 dissent and by the F-CANOPY-049\n"
        "    counter-reading (Lane 13-R3B); round 2's change list gains the hunks it omitted (the \"Sources read\" sentence,\n"
        "    round 1's rewritten \"Not applied\" and its parenthetical, the handoff's PR-contents sentence, audit grep and two\n"
        "    \"Changed by this session\" lines, item 4's release tags) (Lanes 13-R3A and 13-R3B);",
    ),
]

ROUND4_RECORD = """
- **Round 4**: two lanes on the frozen `369863cf`, briefed on round 3's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane13R4_phase13_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round4.md`.
  - Lane 13-R4A replayed round 3's pass on `10194b8c`: `369863cf` byte for byte on all four files, with no hand edit,
    and re-derived every claim the pass introduced, reading every `shipped`, `CAN-015g`, `g-3` and `#190` line of the
    audit. Lane 13-R4B was adversarial on the pass, and replayed it too.
  - Both found every count, header, rating and disposition unchanged, the dissents as the lanes stated them, and
    the triage at 79 / 56 / 1 / 2 / 20, 9 and 11.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Neither found anything that changes a number, a disposition or an
  action, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` **the
  review ends at round 4.**
- **What round 4 changed**, wording and the records only:
  - the site count: round 3 had written "four sites in three documents" after finding three more restatements in
    the audit; the phase now counts three sections corrected (the design note's status block, the roadmap's §28.1,
    the audit's §5.2) and four restatements pointed at them (the roadmap's CAN-015 row; the audit's §5.2 Status
    delta, §8.1 and §11.7 rows), in "The design note's correction", the Matrix effect and the handoff's items 4 and 8
    (Lanes 13-R4A and 13-R4B);
  - the CAN-015 row "carries the correction" no longer in "Still owed", the handoff's Completed bullet and the
    parent's O17, where round 3 had not reached; it points at it (Lanes 13-R4A and 13-R4B);
  - the handoff's item 8 reads as its item 4 (Lane 13-R4B);
  - "Sources read" names the audit's §8.1 and §11.7 and rounds 1 to 3 (Lane 13-R4A);
  - the audit's theme lines (`:13`, `:21`, `:248`, `:353`), which name no sub-task, are recorded as standing with its
    §5.1 line (Lanes 13-R4A and 13-R4B);
  - round 3's record: its first bullet says what each of the four places says in its own words, its handoff bullet
    gains the "Changed by this session" audit line it omitted, and the F-CANOPY-049 counter-reading is credited to
    Lane 13-R3B alone (Lanes 13-R4A and 13-R4B);
  - the handoff's landing trap names this round's pass too, and that each pass needs a whole-tree copy under
    `--root` (Lane 13-R4B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase13_ledger_round4_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger, SUB_COUNT_HANDOFF in the handoff and SUB_COUNT_PARENT in the parent
    handoff. It also fills the handoff's `**Consensus**` line.
- **Re-derived by the orchestrator before applying:** the roadmap's `:5196` (a pointer clause); the three places that
  still said "carry"; the audit's four theme lines; the handoff's items 4 and 8.
- **Not applied.** Lane 13-R4A's note that the audit's `:353` could take the same pointer: it names no sub-task and
  holds with g-3 excepted.
- **Unresolved dissent.** Unchanged: F-CANOPY-028 (one lane P2) and F-CANOPY-067 (one lane P1 by source).
- **What the evidence cannot support** is unchanged from "What this phase cannot support" and round 1's record. The
  instrument of this phase is a reading of one file and of the GitHub API; across four rounds its two independent
  readings of the manual agreed with the phase's twenty ratings, and the rounds' corrections were to what the phase
  said about other documents (the roadmap, the audit) and about itself.
- **Slips.** None reported."""

ROUND3_TAIL = (
    "- **Not applied.** Lane 13-R3B's note that the corrected-site list differs by file beyond the banner: the parent's\n"
    "  item 4 and the INDEX name documents, the ledger counts sites; both are true.\n"
    "- **Unresolved dissent.** Unchanged: F-CANOPY-028 (one lane P2) and F-CANOPY-067 (one lane P1 by source).\n"
    "- **Slips.** None reported."
)

HANDOFF_SUBS = [
    (
        "**Consensus**: CONSENSUS_SUMMARY_PENDING",
        "**Consensus**: four rounds on 2026-10-19 (three lanes, then two on each correction pass); round 4 changed no number,\n"
        "disposition or action, so the review ended there (ledger Phase 13, Consensus record).",
    ),
    (
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's\n"
        "    §28.1 and CAN-015 row (`notes/" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2\n"
        "    (`notes/" + AUDIT_NAME + "`), whose own §11.4 had confirmed only g-1 and g-6 on cascor `main`, carry the same dated\n"
        "    correction (rounds 1 and 2). canopy#535's residue",
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's\n"
        "    §28.1 (`notes/" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2\n"
        "    (`notes/" + AUDIT_NAME + "`), whose own §11.4 had confirmed only g-1 and g-6 on cascor `main`, carry the same dated\n"
        "    correction (rounds 1 and 2), and the roadmap's CAN-015 row and the audit's §5.2 Status delta, §8.1 and §11.7\n"
        "    rows point at it (rounds 2 and 3). canopy#535's residue",
    ),
    (
        "   moves (the four sites in three documents that recorded F-CANOPY-057's stream as shipped are corrected or point at\n"
        "   the correction); leads from round 1:",
        "   moves (every site that recorded F-CANOPY-057's stream as shipped is corrected or points at the correction); leads\n"
        "   from round 1:",
    ),
    (
        "8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb decides F-CANOPY-065 alone among the\n"
        "   findings Phase 11 named, the four sites that recorded F-CANOPY-057's stream as shipped now corrected: 9/11 or 8/12).",
        "8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb decides F-CANOPY-065 alone among the\n"
        "   findings Phase 11 named, every site that recorded F-CANOPY-057's stream as shipped corrected or pointed at the\n"
        "   correction: 9/11 or 8/12).",
    ),
    (
        "  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`, then the round-1, round-2 and round-3\n"
        "  correction passes (`util/ad-hoc/2026-10-19_phase13_ledger_round{1,2,3}_corrections.py --root <copy>`), in that\n"
        "  order; re-check `origin/main` an hour after the merge.",
        "  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`, then the four correction passes\n"
        "  (`util/ad-hoc/2026-10-19_phase13_ledger_round{1,2,3,4}_corrections.py --root <copy>`), in that order, on a\n"
        "  whole-tree copy (each pass reads several files under `--root`); re-check `origin/main` an hour after the merge.",
    ),
]

PARENT_SUBS = [
    (
        "longer promises F-CANOPY-057's stream (the V7 roadmap's §28.1 and CAN-015 row and the 2026-05-05 roadmap audit's §5.2 carry the\n"
        "same correction), so the first limb decides F-CANOPY-065 alone among the findings Phase 11 named: 9/11 or 8/12 open P1/P2 (the\n"
        "ledger's two recorded dissents, F-CANOPY-028 and F-CANOPY-067, would move it one either way).",
        "longer promises F-CANOPY-057's stream (the V7 roadmap's §28.1 and the 2026-05-05 roadmap audit's §5.2 carry the same correction,\n"
        "and the roadmap's CAN-015 row and the audit's three restatements point at it), so the first limb decides F-CANOPY-065 alone among\n"
        "the findings Phase 11 named: 9/11 or 8/12 open P1/P2 (the ledger's two recorded dissents, F-CANOPY-028 and F-CANOPY-067, would\n"
        "move it one either way).",
    ),
]


def apply(text: str, subs: list, label: str) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label}: SUB anchor found {n} times: {old[:90]!r}")
        text = text.replace(old, new)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="repo root (default: this script's repo)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    paths = {"ledger": root / LEDGER, "handoff": root / HANDOFF, "parent": root / PARENT}
    texts = {k: p.read_text(encoding="utf-8") for k, p in paths.items()}

    ledger = texts["ledger"]
    if "- **Round 3**: two lanes on the frozen `10194b8c`" not in ledger or "- **Round 4**: two lanes on the frozen `369863cf`" in ledger:
        raise SystemExit("this is not the round-4 freeze (369863cf)")

    record = (
        ROUND4_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS)))
        .replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS)))
        .replace("SUB_COUNT_PARENT", str(len(PARENT_SUBS)))
    )
    new = {}
    new["ledger"] = apply(ledger, LEDGER_SUBS, "ledger")
    if new["ledger"].count(ROUND3_TAIL) != 1:
        raise SystemExit("round-3 record tail not found exactly once")
    new["ledger"] = new["ledger"].replace(ROUND3_TAIL, ROUND3_TAIL + record)
    new["handoff"] = apply(texts["handoff"], HANDOFF_SUBS, "handoff")
    new["parent"] = apply(texts["parent"], PARENT_SUBS, "parent")

    print(f"ledger: {len(LEDGER_SUBS)} substitutions + the round-4 record, {len(ledger)} -> {len(new['ledger'])} chars")
    print(f"handoff: {len(HANDOFF_SUBS)}; parent: {len(PARENT_SUBS)}")
    if args.check:
        print("--check: nothing written")
        return 0
    for k, p in paths.items():
        p.write_text(new[k], encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
