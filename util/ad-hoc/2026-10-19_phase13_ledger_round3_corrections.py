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
"""Round 3's correction pass on the ledger's Phase 13 and the files that land with it.

Applied to the files as frozen for round 3 (local commit ``10194b8c``). Round 3's two reports are archived verbatim
in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round3.md``. Every substitution is
anchored to occur exactly once in its file. Each is credited to the lane that raised it; the orchestrator re-derived
each from the artifact before applying it (the ledger's round-3 record says what). The pass touches the ledger, the
new handoff, the Phase 12 handoff's banner and the 2026-05-05 roadmap audit (pointers on three rows that restate
the §5.2 claim round 2 corrected).

Usage:
    python3 util/ad-hoc/2026-10-19_phase13_ledger_round3_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md"
PHASE12_HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md"
AUDIT = "notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"

AUDIT_NAME = "JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"
ROADMAP_NAME = "JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"

LEDGER_SUBS = [
    # --- Summary: the audit cites are c741351c's; the CAN-015 row is a pointer; the absolute sentence (R3A F3/F4, R3B F1/F8/F9) ---
    (
        "  whose §5.2 says \"both are **shipped end-to-end** on `main`\" over the same per-PR table (`" + AUDIT_NAME + ":124`,\n"
        "  `:132`) while its own §11.4 confirmed only g-1 and g-6 of CAN-015g on cascor `main` (`:323`), and whose §5.1 line\n"
        "  reads \"CAN-015g replay V2 wired\" (`:112`) (round 1, Lane 13-B, on `:112`; round 2, Lanes 13-R2A and 13-R2B,\n"
        "  MAJOR, on §5.2). Rounds 1 and 2 gave §28.1, the CAN-015 row and §5.2 the same dated correction; the §5.1 line\n"
        "  describes canopy's consumers, which shipped, and stands. So the first limb decides F-CANOPY-065; F-CANOPY-057\n"
        "  is reached through no document this phase or its lanes read. The second limb still decides F-CANOPY-068's\n",
        "  whose §5.2 says \"both are **shipped end-to-end** on `main`\" over the same per-PR table (`" + AUDIT_NAME + ":124`\n"
        "  and `:132` at `c741351c`, before its correction) while its own §11.4 confirmed only g-1 and g-6 of CAN-015g on\n"
        "  cascor `main` (`:323` there), and whose §5.1 line reads \"CAN-015g replay V2 wired\" (`:112`) (round 1, Lane 13-B,\n"
        "  on `:112`; round 2, Lanes 13-R2A and 13-R2B, MAJOR, on §5.2). Rounds 1 and 2 gave §28.1 and §5.2 the same dated\n"
        "  correction and pointed the roadmap's CAN-015 row at it; round 3 pointed the audit's three restatements of its\n"
        "  claim (its §5.2 Status delta, its §8.1 row and its §11.7 row) at §5.2's note (Lane 13-R3B); the §5.1 line\n"
        "  describes canopy's consumers, which shipped, and stands. So the first limb decides F-CANOPY-065; F-CANOPY-057\n"
        "  is reached through no document this phase or its lanes read, every site that recorded the stream as shipped\n"
        "  now carrying the dated correction or a pointer to it. The second limb still decides F-CANOPY-068's\n",
    ),
    # --- F-057 Status bullet ---
    (
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13). The V7 roadmap's §28.1 and CAN-015\n"
        "  row (`" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2 (`" + AUDIT_NAME + "`), which had said \"shipped\n"
        "  end-to-end on `main`\" while its own §11.4 confirmed only g-1 and g-6, carry the same correction since Phase 13's\n"
        "  rounds 1 and 2; the audit's §5.1 line \"CAN-015g replay V2 wired\" (`:112`) describes canopy's consumers, which\n"
        "  shipped, and stands. No document this phase or its lanes read still records the stream as shipped.",
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13). The V7 roadmap's §28.1\n"
        "  (`" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2 (`" + AUDIT_NAME + "`), which had said \"shipped end-to-end\n"
        "  on `main`\" while its own §11.4 confirmed only g-1 and g-6, carry the same correction since Phase 13's rounds 1\n"
        "  and 2, and the roadmap's CAN-015 row and the audit's three restatements (its §5.2 Status delta, §8.1 and §11.7\n"
        "  rows) point at it since rounds 2 and 3; the audit's §5.1 line \"CAN-015g replay V2 wired\" (`:112`) describes\n"
        "  canopy's consumers, which shipped, and stands. No document this phase or its lanes read still records the stream\n"
        "  as shipped without the correction, or a pointer to it, beside the claim.",
    ),
    # --- The design note's correction: cites, the CAN-015 pointer, round 3's pointers (R3A F3/F4, R3B F1/F8) ---
    (
        "2026-05-05 audit, whose §5.2, \"Critical blind spot — CAN-015g and CAN-015h\", says \"As of 2026-05-05 both are\n"
        "**shipped end-to-end** on `main`\" over the same eight-row table, g-3 row included (`" + AUDIT_NAME + ":122-134`),\n"
        "while its own §11.4, \"CAN-015g/h shipping verification\", lists what it confirmed on cascor `main`, \"#180 (g-1),\n"
        "#191 (g-6)\", and never #189 or #190 (`:318-323`); its §5.1 per-repo table's \"CAN-015g replay V2 wired\" (`:112`)\n"
        "describes canopy's consumers (g-4, g-7), which shipped, and stands. Round 1 gave §28.1 the same dated correction,\n"
        "a note under its heading and the g-3 row annotated, having read the audit at `:112` alone and called it a\n"
        "snapshot of commit themes; round 2 read §5.2, annotated the CAN-015 row, and gave §5.2 the same note, citing\n"
        "§11.4, with its g-3 row annotated. With the four sites corrected, no document this phase or its lanes read records\n"
        "the stream as shipped, and the first limb reaches F-CANOPY-057 through none of them; a plan none of them read may\n"
        "still, which item 26's second step would find.",
        "2026-05-05 audit, whose §5.2, \"Critical blind spot — CAN-015g and CAN-015h\", says \"As of 2026-05-05 both are\n"
        "**shipped end-to-end** on `main`\" over the same eight-row table, g-3 row included (`" + AUDIT_NAME + ":122-137` at\n"
        "`c741351c`, before its correction), while its own §11.4, \"CAN-015g/h shipping verification\", lists what it\n"
        "confirmed on cascor `main`, \"#180 (g-1), #191 (g-6)\", and never #189 or #190 (`:318-323` there); its §5.1\n"
        "per-repo table's \"CAN-015g replay V2 wired\" (`:112`) describes canopy's consumers (g-4, g-7), which shipped, and\n"
        "stands. Round 1 gave §28.1 the same dated correction, a note under its heading and the g-3 row annotated, having\n"
        "read the audit at `:112` alone and called it a snapshot of commit themes; round 2 read §5.2, pointed the CAN-015\n"
        "row at §28.1's note, and gave §5.2 the same note, citing §11.4, with its g-3 row annotated; round 3 pointed the\n"
        "audit's three restatements of the claim, its §5.2 Status delta and its §8.1 and §11.7 rows, at §5.2's note (Lane\n"
        "13-R3B). With the four sites in three documents corrected or pointed at the correction, no document this phase\n"
        "or its lanes read records the stream as shipped without it, and the first limb reaches F-CANOPY-057 through none\n"
        "of them; a plan none of them read may still, which item 26's second step would find.",
    ),
    # --- Matrix effect (R3A F4) ---
    (
        "  - **The owner's question** (O17): the first limb decides F-CANOPY-065 alone among the findings Phase 11 named,\n"
        "    the four sites that recorded F-CANOPY-057's stream as shipped now carrying the dated correction: 9 open P1\n",
        "  - **The owner's question** (O17): the first limb decides F-CANOPY-065 alone among the findings Phase 11 named,\n"
        "    the four sites in three documents that recorded F-CANOPY-057's stream as shipped now corrected or pointed at\n"
        "    the correction: 9 open P1\n",
    ),
    # --- Still owed, item 30: the F-012 qualifier (R3B F5) ---
    (
        "      by source the semicolon and newline forms become one row per value and are rejected) and\n",
        "      by source the semicolon and newline forms become one row per value and are rejected on a network with more\n"
        "      than one output) and\n",
    ),
    # --- Round 1's amended record: eight places, not nine (R3A F1, R3B F3) ---
    (
        "    reach statement is restated in all nine of the Summary, \"The design note's correction\", the Matrix effect,\n"
        "    F-CANOPY-057's and F-CANOPY-065's Status bullets, \"Still owed\", the handoff, the parent's O17 and the INDEX, with\n"
        "    the three figures 9/11, 8/12 or 10/10 in four of them (the Summary, the Matrix effect, the handoff's Counts and\n"
        "    the parent's O17; the INDEX carries counts only);",
        "    reach statement is restated in all eight of the Summary, \"The design note's correction\", the Matrix effect,\n"
        "    F-CANOPY-057's and F-CANOPY-065's Status bullets, \"Still owed\", the handoff and the parent's O17, with the three\n"
        "    figures 9/11, 8/12 or 10/10 in four of them (the Summary, the Matrix effect, the handoff's Counts and the\n"
        "    parent's O17); the INDEX and the parent's item 4 name the corrected documents and the counts only (round 1\n"
        "    wrote \"nine\" and \"the INDEX\"; corrected in round 3);",
    ),
    # --- Round 2's record: its own misstatements (R3A F1/F2, R3B F2/F3/F4) ---
    (
        "    Phase 11 named, and \"10 and 10 by the broadest reading\" is withdrawn: 10 and 10 remains only by the F-CANOPY-067\n"
        "    dissent. Stated so in the Summary, \"The design note's correction\", the Matrix effect, F-CANOPY-057's and\n"
        "    F-CANOPY-065's Status bullets, \"Still owed\", the handoff, the parent's O17 and item 4, and the INDEX (Lanes\n"
        "    13-R2A and 13-R2B);",
        "    Phase 11 named, and \"10 and 10 by the broadest reading\" is withdrawn: 10 and 10 remains by the F-CANOPY-067\n"
        "    dissent and by the F-CANOPY-049 counter-reading. Stated so in the Summary, \"The design note's correction\", the\n"
        "    Matrix effect, F-CANOPY-057's and F-CANOPY-065's Status bullets, \"Still owed\", the handoff and the parent's O17,\n"
        "    and, as the list of corrected documents, in the parent's item 4 and the INDEX (Lanes 13-R2A and 13-R2B; round 2\n"
        "    wrote \"only by the F-CANOPY-067 dissent\" and listed item 4 and the INDEX with the rest, corrected in round 3);",
    ),
    (
        "  - round 1's record: the three figures appeared in four places and the reach statement in nine, the INDEX carrying\n"
        "    counts only; its change list gains the hunks it omitted (the \"Sources read\" sentence, the FAQ re-read\n"
        "    parenthetical, item 18's F-CANOPY-067 sentence, the handoff's PR-contents sentence and roadmap grep); the\n"
        "    F-CANOPY-056 bullet is labelled \"Re-rated P1\" (Lanes 13-R2A and 13-R2B);",
        "  - round 1's record: the three figures appeared in four places and the reach statement in eight, the INDEX and the\n"
        "    parent's item 4 carrying the corrected-document list and counts only; its change list gains the hunks it\n"
        "    omitted (the \"Sources read\" sentence, the FAQ re-read parenthetical, item 18's F-CANOPY-067 sentence, the\n"
        "    handoff's PR-contents sentence and roadmap grep); the F-CANOPY-056 bullet is labelled \"Re-rated P1\" (Lanes\n"
        "    13-R2A and 13-R2B);",
    ),
    (
        "  - wording: the Candidate Metrics condition spans `:686-688` (Lane 13-R2B; Lane 13-A had cited it so); the Summary\n"
        "    names F-CANOPY-067's dissent beside F-CANOPY-028's (Lanes 13-R2A and 13-R2B); the handoff's \"from Phase 5's on\"\n"
        "    (Lane 13-R2A).\n",
        "  - wording: the Candidate Metrics condition spans `:686-688` (Lane 13-R2B; Lane 13-A had cited it so); the Summary\n"
        "    names F-CANOPY-067's dissent beside F-CANOPY-028's (Lanes 13-R2A and 13-R2B); the handoff's \"from Phase 5's on\"\n"
        "    (Lane 13-R2A); and, listed by round 3 (Lanes 13-R3A and 13-R3B): the \"Sources read\" sentence (rounds 1 and 2;\n"
        "    §5.1, §5.2 and §11.4), round 1's \"Not applied\" bullet rewritten and its \"(reversed in round 2)\", the handoff's\n"
        "    PR-contents sentence, its audit grep, its two \"Changed by this session\" lines and item 4's `[0.8.0]` and\n"
        "    `[0.6.0]` tags.\n",
    ),
]

ROUND3_RECORD = """
- **Round 3**: two lanes on the frozen `10194b8c`, briefed on round 2's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane13R3_phase13_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round3.md`.
  - Lane 13-R3A replayed round 2's pass on `c741351c`: `10194b8c` byte for byte on all six files, with no hand edit,
    and re-derived every claim the pass introduced, the parsers executed again against one- and two-output shapes.
    Lane 13-R3B was adversarial on the pass, and replayed it too.
  - Both found every count, header, rating and disposition unchanged, the reach statement consistent where round 2
    rewrote it, the credits and the two dissents as the lanes stated them, and the triage at 79 / 56 / 1 / 2 / 20,
    9 and 11.
- **Verdicts.** Both returned SOUND-WITH-FIXES. Neither moved a count, a rating or a disposition. Two findings change
  an action: the audit restates its §5.2 claim in three rows round 2 did not touch (its §5.2 Status delta, its §8.1
  row and its §11.7 row), so round 2's absolute "no document … still records the stream as shipped" overstated (Lane
  13-R3B); and the handoff's landing trap named the apply script alone where the three correction passes must follow
  it (Lane 13-R3B). So §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires
  round 4. The rest is the records' description of themselves and wording.
- **What round 3 changed:**
  - the audit's three restatements now point at §5.2's note (`JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`,
    the Status delta under §5.2, the §8.1 row and the §11.7 row); the Summary, F-CANOPY-057's Status bullet, "The
    design note's correction" and the Matrix effect say "corrected or pointed at the correction", "four sites in three
    documents", and that the CAN-015 row carries a pointer, not the note (Lanes 13-R3A and 13-R3B);
  - the handoff's landing trap names the apply script and the three correction passes, in that order (Lane 13-R3B);
  - the F-CANOPY-012 qualifier, "on a network with more than one output", reaches item 30 and the handoff's item 2
    (Lane 13-R3B);
  - round 1's and round 2's records: the reach statement is in eight places, the INDEX and the parent's item 4 naming
    the corrected documents and the counts only; 10 and 10 remains by the F-CANOPY-067 dissent and by the F-CANOPY-049
    counter-reading; round 2's change list gains the hunks it omitted (the "Sources read" sentence, round 1's
    rewritten "Not applied" and its parenthetical, the handoff's PR-contents sentence, audit grep and two "Changed by
    this session" lines, item 4's release tags) (Lanes 13-R3A and 13-R3B);
  - the audit's line cites in the Summary and "The design note's correction" are pinned to `c741351c`, before the
    ten-line note moved them, and the table span is `:122-137` (Lanes 13-R3A and 13-R3B);
  - the Phase 12 handoff's SUPERSEDED banner names the roadmap's and the audit's corrections beside the design note's
    (Lane 13-R3B's note on the corrected-site lists);
  - the handoff's item 4 says "four sites in three documents" (Lanes 13-R3A and 13-R3B).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase13_ledger_round3_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger, SUB_COUNT_HANDOFF in the handoff, SUB_COUNT_P12 in the Phase 12
    handoff's banner and SUB_COUNT_AUDIT in the audit.
- **Re-derived by the orchestrator before applying:** the audit's rows at `10194b8c` (`:168` "Status delta", `:225`
  "CAN-015g/h shipped end-to-end without any roadmap delta", `:360` "§5 CAN-015g/h shipping claim | CONFIRMED"), and
  that its §5.2 sentence, g-3 row and §11.4 now sit at `:134`, `:142` and `:328-333`; the INDEX's row and the parent's
  item 4 carry no reach statement (0 hits for "first limb"); the handoff's trap sentence.
- **Not applied.** Lane 13-R3B's note that the corrected-site list differs by file beyond the banner: the parent's
  item 4 and the INDEX name documents, the ledger counts sites; both are true.
- **Unresolved dissent.** Unchanged: F-CANOPY-028 (one lane P2) and F-CANOPY-067 (one lane P1 by source).
- **Slips.** None reported."""

ROUND2_TAIL = (
    "- **Unresolved dissent.** Unchanged: F-CANOPY-028 (one lane P2) and F-CANOPY-067 (one lane P1 by source).\n"
    "- **Slips.** None reported."
)

HANDOFF_SUBS = [
    (
        "   moves (the four documents that recorded F-CANOPY-057's stream as shipped are corrected); leads from round 1:",
        "   moves (the four sites in three documents that recorded F-CANOPY-057's stream as shipped are corrected or point at\n"
        "   the correction); leads from round 1:",
    ),
    (
        "     a wrong-count flat list; by source the semicolon and newline forms are read as rows and rejected) and\n",
        "     a wrong-count flat list; by source the semicolon and newline forms are read as rows and rejected on a network\n"
        "     with more than one output) and\n",
    ),
    (
        "- **Shared files land as whole-file uploads.** Build each from a fresh `origin/main` copy at upload time and re-apply\n"
        "  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`; re-check `origin/main` an hour after the merge.",
        "- **Shared files land as whole-file uploads.** Build each from a fresh `origin/main` copy at upload time and re-apply\n"
        "  with `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py --root <copy>`, then the round-1, round-2 and round-3\n"
        "  correction passes (`util/ad-hoc/2026-10-19_phase13_ledger_round{1,2,3}_corrections.py --root <copy>`), in that\n"
        "  order; re-check `origin/main` an hour after the merge.",
    ),
    (
        "  - `notes/" + AUDIT_NAME + "`: §5.2's dated correction and its g-3 row (round 2);",
        "  - `notes/" + AUDIT_NAME + "`: §5.2's dated correction and its g-3 row (round 2); pointers on its §5.2 Status delta and\n"
        "    its §8.1 and §11.7 rows (round 3);",
    ),
]

PHASE12_SUBS = [
    (
        "> sweep, and the CAN-015g/h design note's correction, recorded as Phase 13 of\n",
        "> sweep, and the CAN-015g/h design note's correction, carried also into the V7 roadmap and the 2026-05-05 roadmap\n"
        "> audit, recorded as Phase 13 of\n",
    ),
]

AUDIT_SUBS = [
    (
        "**Status delta**: roadmap says \"future deferred\", code says \"shipped, hardened, integration-tested\".",
        "**Status delta**: roadmap says \"future deferred\", code says \"shipped, hardened, integration-tested\" (g-3 excepted: see the correction of 2026-10-19 above).",
    ),
    (
        "| **Major delivery sprints don't trigger a roadmap revision** | CAN-015g/h shipped end-to-end without any roadmap delta                                   | All 15 sub-tasks                    |",
        "| **Major delivery sprints don't trigger a roadmap revision** | CAN-015g/h shipped end-to-end without any roadmap delta (g-3 excepted: see §5.2's correction of 2026-10-19) | All 15 sub-tasks                    |",
    ),
    (
        "| §5 CAN-015g/h shipping claim           | CONFIRMED via git log + roadmap line 5121 quote                                              |",
        "| §5 CAN-015g/h shipping claim           | CONFIRMED via git log + roadmap line 5121 quote (g-3 excepted: §11.4's list never named #190; see §5.2's correction of 2026-10-19) |",
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

    paths = {
        "ledger": root / LEDGER,
        "handoff": root / HANDOFF,
        "phase12": root / PHASE12_HANDOFF,
        "audit": root / AUDIT,
    }
    texts = {k: p.read_text(encoding="utf-8") for k, p in paths.items()}

    ledger = texts["ledger"]
    if "- **Round 2**: two lanes on the frozen `c741351c`" not in ledger or "- **Round 3**: two lanes on the frozen `10194b8c`" in ledger:
        raise SystemExit("this is not the round-3 freeze (10194b8c)")
    if "g-3 excepted" in texts["audit"]:
        raise SystemExit("the audit already carries round 3's pointers")

    record = (
        ROUND3_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS)))
        .replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS)))
        .replace("SUB_COUNT_P12", str(len(PHASE12_SUBS)))
        .replace("SUB_COUNT_AUDIT", str(len(AUDIT_SUBS)))
    )
    new = {}
    new["ledger"] = apply(ledger, LEDGER_SUBS, "ledger")
    if new["ledger"].count(ROUND2_TAIL) != 1:
        raise SystemExit("round-2 record tail not found exactly once")
    new["ledger"] = new["ledger"].replace(ROUND2_TAIL, ROUND2_TAIL + record)
    new["handoff"] = apply(texts["handoff"], HANDOFF_SUBS, "handoff")
    new["phase12"] = apply(texts["phase12"], PHASE12_SUBS, "phase12 handoff")
    new["audit"] = apply(texts["audit"], AUDIT_SUBS, "audit")

    print(f"ledger: {len(LEDGER_SUBS)} substitutions + the round-3 record, {len(ledger)} -> {len(new['ledger'])} chars")
    print(f"handoff: {len(HANDOFF_SUBS)}; phase12: {len(PHASE12_SUBS)}; audit: {len(AUDIT_SUBS)}")
    if args.check:
        print("--check: nothing written")
        return 0
    for k, p in paths.items():
        p.write_text(new[k], encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
