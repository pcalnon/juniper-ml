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
"""Round 2's correction pass on the ledger's Phase 13 and the files that land with it.

Applied to the files as frozen for round 2 (local commit ``c741351c``). Round 2's two reports are archived verbatim
in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round2.md``. Every substitution is
anchored to occur exactly once in its file. Each is credited to the lane that raised it; the orchestrator re-derived
each from the artifact or the code before applying it (the ledger's round-2 record says what). Besides the ledger
and the handoffs, the pass touches the V7 roadmap's CAN-015 row and -- new in this round -- the 2026-05-05 roadmap
audit's §5.2, which round 1 had disposed of on a reading of its ``:112`` line alone (Lanes 13-R2A and 13-R2B, MAJOR).

Usage:
    python3 util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md"
PARENT = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md"
INDEX = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md"
ROADMAP = "notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"
AUDIT = "notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"

ROADMAP_NAME = "JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"
AUDIT_NAME = "JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"

# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

LEDGER_SUBS = [
    # --- Summary: the owner's question (R2A F1, R2B F1) ---
    (
        "  the manual without any ruling. F-CANOPY-057 was still recorded as shipped by two documents the design note's\n"
        "  correction does not touch: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  (`" + ROADMAP_NAME + "`, `:15146-15160` and `:5196`) and the 2026-05-05 audit's per-repo activity table\n"
        "  (`" + AUDIT_NAME + ":112`) (round 1, Lane 13-B, MAJOR). Round 1 gave §28.1 the same dated correction; the audit\n"
        "  is a dated snapshot of commit themes and is left as history. So the first limb decides F-CANOPY-065, and\n"
        "  F-CANOPY-057 only if an audit's activity line is read as a design-plan promise; the second limb still decides\n"
        "  F-CANOPY-068's rating of record and moves no count. Item 26's second step, the CHANGELOG and the design plans\n"
        "  for every open finding, still waits on the ruling, with two leads recorded under \"Still owed\".",
        "  the manual without any ruling. F-CANOPY-057 was still recorded as shipped by two documents the design note's\n"
        "  correction does not touch: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  (`" + ROADMAP_NAME + "`, `:15146-15160` and `:5196`) (round 1, Lane 13-B, MAJOR), and the 2026-05-05 audit,\n"
        "  whose §5.2 says \"both are **shipped end-to-end** on `main`\" over the same per-PR table (`" + AUDIT_NAME + ":124`,\n"
        "  `:132`) while its own §11.4 confirmed only g-1 and g-6 of CAN-015g on cascor `main` (`:323`), and whose §5.1 line\n"
        "  reads \"CAN-015g replay V2 wired\" (`:112`) (round 1, Lane 13-B, on `:112`; round 2, Lanes 13-R2A and 13-R2B,\n"
        "  MAJOR, on §5.2). Rounds 1 and 2 gave §28.1, the CAN-015 row and §5.2 the same dated correction; the §5.1 line\n"
        "  describes canopy's consumers, which shipped, and stands. So the first limb decides F-CANOPY-065; F-CANOPY-057\n"
        "  is reached through no document this phase or its lanes read. The second limb still decides F-CANOPY-068's\n"
        "  rating of record and moves no count. Item 26's second step, the CHANGELOG and the design plans for every open\n"
        "  finding, still waits on the ruling, with two leads recorded under \"Still owed\".",
    ),
    # --- Summary: counts line ---
    (
        "  P0, **9 open P1** and **11 open P2**. By ruling on the first limb: 9 and 11 as the triage counts them, 8 and 12,\n"
        "  or 10 and 10 by the broadest reading (the audit's line; Matrix effect and counts).",
        "  P0, **9 open P1** and **11 open P2**. By ruling on the first limb: 9 and 11 as the triage counts them, or 8 and\n"
        "  12. The two recorded dissents would make it one P1 fewer (F-CANOPY-028) or one more (F-CANOPY-067); Matrix\n"
        "  effect and counts.",
    ),
    # --- Summary: F-067's dissent (R2A F5, R2B F5) ---
    (
        "  first limb. F-CANOPY-067's rating stays \"P2 pending a live drive\", its own condition; the manual documents the\n"
        "  plots it would corrupt, so the live drive is all that is left to decide it.",
        "  first limb. F-CANOPY-067's rating stays \"P2 pending a live drive\", its own condition; the manual documents the\n"
        "  plots it would corrupt, so the live drive is all that is left to decide it, and one round-1 lane would rate it\n"
        "  P1 by source today (Consensus record).",
    ),
    # --- Who, and from what: sources ---
    (
        "  compare of `main` with `dbc25277`. In this repo, after round 1: the V7 roadmap's §28.1 and CAN-015 row and the\n"
        "  2026-05-05 audit's §5.1 (named under \"The design note's correction\").",
        "  compare of `main` with `dbc25277`. In this repo, after rounds 1 and 2: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  and the 2026-05-05 audit's §5.1, §5.2 and §11.4 (named under \"The design note's correction\").",
    ),
    # --- "Reached" paragraph: the Candidate Metrics span (R2B F6) ---
    (
        "  Candidate Metrics tab's Phase and Candidate Epoch Progress (`:686-687`). Both are conditioned on the training",
        "  Candidate Metrics tab's Phase and Candidate Epoch Progress (`:686-688`). Both are conditioned on the training",
    ),
    (
        "The Phase Duration card (`:328`, \"during active phases\") and the Candidate Metrics tab's Phase and progress (`:686-687`) read the fields the entry found frozen",
        "The Phase Duration card (`:328`, \"during active phases\") and the Candidate Metrics tab's Phase and progress (`:686-688`) read the fields the entry found frozen",
    ),
    # --- The five re-ratings: F-012's residue, one-output networks (R2A F7) ---
    (
        "  semicolons row separators, so the manual's semicolon- or newline-separated floats, entered for `output_weights`,\n"
        "  become one row per value and cascor rejects the shape, loudly as before; only the comma form reaches the\n"
        "  reshape. By source two of the manual's three forms still fail for this group after the fix. It is this entry's",
        "  semicolons row separators, so the manual's semicolon- or newline-separated floats, entered for `output_weights`,\n"
        "  become one row per value, which cascor's shape check rejects wherever the network has more than one output,\n"
        "  loudly as before; only the comma form reaches the reshape. By source two of the manual's three forms still fail\n"
        "  for this group after the fix on such a network. It is this entry's",
    ),
    (
        "> newline-separated floats for `output_weights` become one row per value and cascor rejects the shape, loudly;\n"
        "> only the comma form reaches the reshape. Item 30 drives all three forms; the manual's Patch Weights sentence",
        "> newline-separated floats for `output_weights` become one row per value, which cascor's shape check rejects\n"
        "> wherever the network has more than one output, loudly; only the comma form reaches the reshape. Item 30 drives\n"
        "> all three forms; the manual's Patch Weights sentence",
    ),
    # --- F-057 status bullet (R2A F1, R2B F1) ---
    (
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13). The V7 roadmap's §28.1\n"
        "  (`" + ROADMAP_NAME + "`) carries the same correction since Phase 13's round 1; the 2026-05-05 audit's activity line\n"
        "  (`" + AUDIT_NAME + ":112`) still reads \"CAN-015g replay V2 wired\" and is left as a dated snapshot, the one document\n"
        "  through which the first limb could still reach this entry.",
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13). The V7 roadmap's §28.1 and CAN-015\n"
        "  row (`" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2 (`" + AUDIT_NAME + "`), which had said \"shipped\n"
        "  end-to-end on `main`\" while its own §11.4 confirmed only g-1 and g-6, carry the same correction since Phase 13's\n"
        "  rounds 1 and 2; the audit's §5.1 line \"CAN-015g replay V2 wired\" (`:112`) describes canopy's consumers, which\n"
        "  shipped, and stands. No document this phase or its lanes read still records the stream as shipped.",
    ),
    # --- F-065 status bullet ---
    (
        "  first limb, which after Phase 13 decides this entry, and F-CANOPY-057 only through a dated audit's activity line\n"
        "  (Phase 13, Matrix effect and counts).",
        "  first limb, which after Phase 13 decides this entry alone among the findings Phase 11 named (Phase 13, Matrix\n"
        "  effect and counts).",
    ),
    # --- The design note's correction: the audit (R2A F1, R2B F1) ---
    (
        "Two other documents recorded g-3 as shipped (round 1, Lane 13-B, MAJOR): the V7 roadmap's §28.1, \"CAN-015g +\n"
        "CAN-015h — Phase 6E deferred, shipped end-to-end\", whose g-3 row read \"cascor #190 (retarget of #187) |\n"
        "Sample-boundary weight emission | `dbc25277`\" (`" + ROADMAP_NAME + ":15146-15160`), and its CAN-015 row, which\n"
        "counts \"8 PRs for CAN-015g\" as shipped end-to-end and points to §28.1 (`:5196`); and the 2026-05-05 audit's per-repo\n"
        "commit table, \"CAN-015g replay V2 wired\" under juniper-canopy (`" + AUDIT_NAME + ":112`). Round 1 gave §28.1 the\n"
        "same dated correction, a note under its heading and the g-3 row annotated; the CAN-015 row points to §28.1 and is\n"
        "left. The audit is a dated snapshot of commit themes since 2026-04-23, not a plan's promise, and is left as\n"
        "history. Until the owner rules, the first limb reaches F-CANOPY-057 only through that audit line.",
        "Two other documents recorded g-3 as shipped (round 1, Lane 13-B, MAJOR; round 2, Lanes 13-R2A and 13-R2B, MAJOR):\n"
        "the V7 roadmap's §28.1, \"CAN-015g + CAN-015h — Phase 6E deferred, shipped end-to-end\", whose g-3 row read \"cascor\n"
        "#190 (retarget of #187) | Sample-boundary weight emission | `dbc25277`\" (`" + ROADMAP_NAME + ":15146-15160`), and\n"
        "its CAN-015 row, which counts \"8 PRs for CAN-015g\" as shipped end-to-end and points to §28.1 (`:5196`); and the\n"
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
    ),
    # --- Matrix effect: the owner's question (R2A F1, R2B F1) ---
    (
        "  - **The owner's question** (O17): the first limb decides F-CANOPY-065, and F-CANOPY-057 only if the 2026-05-05\n"
        "    audit's activity line counts as a design-plan promise: 9 open P1 and 11 open P2 if a shipped CHANGELOG or\n"
        "    design-plan promise counts as documented, as the triage counts them; 8 and 12 if not; 10 and 10 by the\n"
        "    broadest reading. The second limb decides F-CANOPY-068's rating of record and moves no count. F-CANOPY-028 is\n"
        "    the re-rating most exposed to a different reading of the manual (one round-1 lane dissents; \"The five\n"
        "    re-ratings\"), which would make each of those pairs one P1 fewer; F-CANOPY-012's counter-reading, that the\n"
        "    manual's \"lets CasCor validate the exact target shape\" makes a shape rejection the documented outcome, is\n"
        "    weaker and no lane adopted it.",
        "  - **The owner's question** (O17): the first limb decides F-CANOPY-065 alone among the findings Phase 11 named,\n"
        "    the four sites that recorded F-CANOPY-057's stream as shipped now carrying the dated correction: 9 open P1\n"
        "    and 11 open P2 if a shipped CHANGELOG or design-plan promise counts as documented, as the triage counts them;\n"
        "    8 and 12 if not. The second limb decides F-CANOPY-068's rating of record and moves no count. The two recorded\n"
        "    dissents move those pairs the other way: F-CANOPY-028, the re-rating most exposed to a different reading of\n"
        "    the manual (one round-1 lane rates it P2; \"The five re-ratings\"), one P1 fewer; F-CANOPY-067, which one\n"
        "    round-1 lane rates P1 by source today, one P1 more, 10 and 10 by that reading alone. F-CANOPY-012's\n"
        "    counter-reading, that the manual's \"lets CasCor validate the exact target shape\" makes a shape rejection the\n"
        "    documented outcome, is weaker and no lane adopted it.",
    ),
    # --- Still owed: item 26's second step (R2A F2, R2B F3; the audit) ---
    (
        "  Of the findings Phase 11 named, F-CANOPY-065 is the one the ruling moves, and F-CANOPY-057 only through the\n"
        "  2026-05-05 audit's line, the design note and the V7 roadmap's §28.1 carrying the dated correction. Two leads a\n"
        "  round-1 lane found for that step, unswept (Lane 13-B): canopy's CHANGELOG `[0.8.0]` says the producer's own\n"
        "  sentence \"survives to the modal\" (`CHANGELOG.md:1436-1437` at `571743db`), which is what F-CANOPY-060 cuts; and\n"
        "  `[0.5.0]`'s \"one tab-persistence system\" (`:2909`) for F-CANOPY-051, weaker.",
        "  Of the findings Phase 11 named, F-CANOPY-065 is the one the ruling moves; the design note, the V7 roadmap's\n"
        "  §28.1 and CAN-015 row and the 2026-05-05 audit's §5.2 carry the dated correction, so F-CANOPY-057 is reached\n"
        "  through none of them, and the step should say so for any other plan it reads. Two leads a round-1 lane found\n"
        "  for that step, unswept (Lane 13-B): canopy's CHANGELOG `[0.8.0]` says the producer's own sentence \"survives to\n"
        "  the modal\" (`CHANGELOG.md:1436-1437` at `571743db`), which is what F-CANOPY-060 cuts; and `[0.6.0]`'s \"one\n"
        "  tab-persistence system\" (`:2909`, under the `## [0.6.0]` heading at `:2171`) for F-CANOPY-051, weaker.",
    ),
    # --- Round 1's record: its own misstatements (R2A F2, F4, R2B F3, F4) ---
    (
        "    the heading and the g-3 row annotated), the audit is left as a dated snapshot, and the ruling's alternatives are\n"
        "    9/11, 8/12 or 10/10 by the broadest reading, in the Summary, \"The design note's correction\", the Matrix effect,\n"
        "    F-CANOPY-057's and F-CANOPY-065's Status bullets, \"Still owed\", the handoff, the parent's O17 and the INDEX;",
        "    the heading and the g-3 row annotated), the audit is left as a dated snapshot (reversed in round 2), and the\n"
        "    reach statement is restated in all nine of the Summary, \"The design note's correction\", the Matrix effect,\n"
        "    F-CANOPY-057's and F-CANOPY-065's Status bullets, \"Still owed\", the handoff, the parent's O17 and the INDEX, with\n"
        "    the three figures 9/11, 8/12 or 10/10 in four of them (the Summary, the Matrix effect, the handoff's Counts and\n"
        "    the parent's O17; the INDEX carries counts only);",
    ),
    (
        "  - item 26's second step records two CHANGELOG leads a lane found, unswept: `[0.8.0]`'s \"survives to the modal\"\n"
        "    for F-CANOPY-060 and `[0.5.0]`'s tab-persistence entry for F-CANOPY-051 (Lane 13-B);",
        "  - item 26's second step records two CHANGELOG leads a lane found, unswept: `[0.8.0]`'s \"survives to the modal\"\n"
        "    for F-CANOPY-060 and `[0.6.0]`'s tab-persistence entry for F-CANOPY-051 (Lane 13-B; round 1 wrote `[0.5.0]`,\n"
        "    corrected in round 2);\n"
        "  - item 18 says F-CANOPY-067's drive also settles that entry's rating under the F-CANOPY-056 standard; \"Sources\n"
        "    read\" names the roadmap and the audit; \"The design note's correction\" notes the FAQ's status note re-read at\n"
        "    `571743db`; the handoff's PR-contents sentence names the roadmap and its verification block gains the roadmap\n"
        "    grep (listed by round 2, Lanes 13-R2A and 13-R2B);",
    ),
    (
        "  - F-CANOPY-049's row and the \"Reached\" paragraph name the Phase Duration card (`:328`) and the Candidate Metrics\n"
        "    tab's Phase and progress (`:686-687`), which read the fields the entry found frozen, and say why they do not",
        "  - F-CANOPY-049's row and the \"Reached\" paragraph name the Phase Duration card (`:328`) and the Candidate Metrics\n"
        "    tab's Phase and progress (`:686-688`), which read the fields the entry found frozen, and say why they do not",
    ),
    (
        "  - the manual's `:266` (the env-var line), `:267-269`, `:328`, `:686-687` and `:285`; the matrix's `:807` (FAIL, no",
        "  - the manual's `:266` (the env-var line), `:267-269`, `:328`, `:686-688` and `:285`; the matrix's `:807` (FAIL, no",
    ),
    (
        "    F-CANOPY-056's Severity, \"re-rated P1, on plan §6.3's rule\", on source and a hand-built probe, \"not been driven\n"
        "    live\".",
        "    F-CANOPY-056's \"Re-rated P1, on plan §6.3's rule\" bullet, on source and a hand-built probe, \"has not been driven\n"
        "    live\".",
    ),
    (
        "- **Not applied.** Lane 13-B's suggestion to correct the 2026-05-05 audit as well: it is a dated snapshot of commit\n"
        "  themes, not a plan, and is recorded instead. Lanes 13-B's and 13-C's note",
        "- **Not applied.** Lane 13-B's suggestion to correct the 2026-05-05 audit as well, declined in round 1 on a reading\n"
        "  of its `:112` line alone; round 2 found that its §5.2 makes the shipping claim outright and reversed this (round\n"
        "  2's record). Lanes 13-B's and 13-C's note",
    ),
]

ROUND2_RECORD = """
- **Round 2**: two lanes on the frozen `c741351c`, briefed on round 1's corrections only, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane13R2_phase13_ledger_brief.md`. The reports, verbatim, are in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round2.md`.
  - Lane 13-R2A replayed round 1's pass on `566cb72a`: `c741351c` byte for byte on all seven files, with no hand edit,
    and re-derived every claim the pass introduced, executing canopy's two parsers on the manual's three forms.
    Lane 13-R2B was adversarial on the pass, and replayed it too.
  - Both found every count, header and disposition unchanged by the pass, the credits and the two dissents stated
    as the lanes stated them, and the triage at 79 / 56 / 1 / 2 / 20, 9 and 11.
- **Verdicts.** Both returned SOUND-WITH-FIXES, with the same MAJOR: round 1 had read the 2026-05-05 audit at its
  `:112` line alone and called it "a dated snapshot of commit themes", and its §5.2 says outright "both are shipped
  end-to-end on `main`" over the same eight-row table, while its §11.4 lists what it confirmed on cascor `main` and
  names neither #189 nor #190. That changes an action (the audit is now corrected, not left) and how O17 is put, so
  §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 3. Lane
  13-R2B also found round 1's withdrawn sentence surviving in the handoff's item 8 (MAJOR). Neither lane moved a
  count, a rating or a disposition.
- **What round 2 changed:**
  - the audit: its §5.2 now carries the same dated correction as the design note and §28.1, a note under its heading
    citing its own §11.4, and its g-3 row is annotated (`JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`); its
    §5.1 line, which describes canopy's consumers, stands. The roadmap's CAN-015 row (`:5196`) is annotated as well
    (Lane 13-R2A's NIT). With the four sites corrected, the first limb decides F-CANOPY-065 alone among the findings
    Phase 11 named, and "10 and 10 by the broadest reading" is withdrawn: 10 and 10 remains only by the F-CANOPY-067
    dissent. Stated so in the Summary, "The design note's correction", the Matrix effect, F-CANOPY-057's and
    F-CANOPY-065's Status bullets, "Still owed", the handoff, the parent's O17 and item 4, and the INDEX (Lanes
    13-R2A and 13-R2B);
  - the handoff's item 8 no longer says the first limb "now decides F-CANOPY-065 alone" on round 1's wrong ground
    (Lanes 13-R2A and 13-R2B);
  - the F-CANOPY-051 lead is `[0.6.0]`'s entry, not `[0.5.0]`'s: `:2909` sits under `## [0.6.0]` (`:2171`), `## [0.5.0]`
    starting at `:2919`; corrected in "Still owed" and in round 1's record (Lanes 13-R2A and 13-R2B);
  - round 1's record: the three figures appeared in four places and the reach statement in nine, the INDEX carrying
    counts only; its change list gains the hunks it omitted (the "Sources read" sentence, the FAQ re-read
    parenthetical, item 18's F-CANOPY-067 sentence, the handoff's PR-contents sentence and roadmap grep); the
    F-CANOPY-056 bullet is labelled "Re-rated P1" (Lanes 13-R2A and 13-R2B);
  - the F-CANOPY-012 residue: the one-value rows are rejected wherever the network has more than one output; with
    one output they are the right shape (Lane 13-R2A, from executing the parsers);
  - wording: the Candidate Metrics condition spans `:686-688` (Lane 13-R2B; Lane 13-A had cited it so); the Summary
    names F-CANOPY-067's dissent beside F-CANOPY-028's (Lanes 13-R2A and 13-R2B); the handoff's "from Phase 5's on"
    (Lane 13-R2A).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger, SUB_COUNT_HANDOFF in the handoff and SUB_COUNT_OTHER across the
    parent handoff, the INDEX, the V7 roadmap and the audit.
- **Re-derived by the orchestrator before applying:** the audit's §5.2 (`:122-134`: the sentence and the g-3 row)
  and §11.4 (`:318-323`: "#180 (g-1), #191 (g-6)"), and that the audit was last changed on 2026-07-04; the
  CHANGELOG's headings at `:2171` and `:2919`; the handoff's item 8; `_resolve_patch_values`' `len(rows) > 1` branch
  against a one-output shape; the manual's `:688`.
- **Not applied.** Nothing. Lane 13-R2B's note that cascor's validator was not fetched: "rejects the shape" is the
  shape check that rejected the flat list in segment 7, applied by source to a body of another wrong shape, and the
  residue is labelled by source.
- **Unresolved dissent.** Unchanged: F-CANOPY-028 (one lane P2) and F-CANOPY-067 (one lane P1 by source).
- **Slips.** None reported."""

# The round-2 record is appended after round 1's closing "Slips" line, which is anchored by the F-067 dissent text
# that precedes it (the same "Slips" sentence closes other phases' records).
ROUND1_TAIL = (
    "    phase's instrument, the manual, adds nothing to it; item 18's drive decides the rating under the F-CANOPY-056\n"
    "    standard.\n"
    "- **What the evidence cannot support** is unchanged from \"What this phase cannot support\", with the additions made\n"
    "  there. The instrument of this phase is a reading of one file and of the GitHub API; it could have produced a\n"
    "  different answer wherever a sentence was missed, and round 1's two independent readings of the manual (Lane 13-A's\n"
    "  twenty answers; Lane 13-B's attacks on the ten not reached) found one such place, F-CANOPY-049, recorded above.\n"
    "- **Slips.** None reported."
)

# ---------------------------------------------------------------------------
# The handoff
# ---------------------------------------------------------------------------

HANDOFF_SUBS = [
    (
        "8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb now decides F-CANOPY-065 alone).",
        "8. Then the parent's items 5 and 7, and the owner batch O1–O17 (O17's first limb decides F-CANOPY-065 alone among the\n"
        "   findings Phase 11 named, the four sites that recorded F-CANOPY-057's stream as shipped now corrected: 9/11 or 8/12).",
    ),
    (
        "    stays with the owner's first limb, which now decides it, and F-CANOPY-057 only through the 2026-05-05 audit's\n"
        "    activity line); F-CANOPY-067 \"P2 pending a live drive\", unchanged. One round-1 lane dissents on F-CANOPY-028 (P2)\n"
        "    and on F-CANOPY-067 (P1 by source); both are recorded in the ledger's consensus record.",
        "    stays with the owner's first limb, which now decides it alone among the findings Phase 11 named); F-CANOPY-067\n"
        "    \"P2 pending a live drive\", unchanged. One round-1 lane dissents on F-CANOPY-028 (P2) and on F-CANOPY-067 (P1 by\n"
        "    source); both are recorded in the ledger's consensus record.",
    ),
    (
        "    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11, 8/12, or 10/10 by the\n"
        "    broadest reading.",
        "    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11 or 8/12; the two recorded\n"
        "    dissents would make it one P1 fewer (F-CANOPY-028) or one more (F-CANOPY-067).",
    ),
    (
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's\n"
        "    §28.1 (`notes/" + ROADMAP_NAME + "`) carries the same dated correction since round 1; the 2026-05-05 audit's line\n"
        "    (`notes/" + AUDIT_NAME + ":112`) is left as a dated snapshot. canopy#535's residue is recorded in F-CANOPY-012's\n"
        "    entry: by source the manual's semicolon and newline forms for `output_weights` are read as rows and rejected.",
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's\n"
        "    §28.1 and CAN-015 row (`notes/" + ROADMAP_NAME + "`) and the 2026-05-05 audit's §5.2\n"
        "    (`notes/" + AUDIT_NAME + "`), whose own §11.4 had confirmed only g-1 and g-6 on cascor `main`, carry the same dated\n"
        "    correction (rounds 1 and 2). canopy#535's residue is recorded in F-CANOPY-012's entry: by source the manual's\n"
        "    semicolon and newline forms for `output_weights` are read as rows and rejected on any network with more than one\n"
        "    output.",
    ),
    (
        "  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no Still-owed list\n"
        "    since Phase 5's.",
        "  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no Still-owed list\n"
        "    from Phase 5's on.",
    ),
    (
        "- **This session's PR** carries the ledger, this file, the design note's and the V7 roadmap's corrections, the parent's",
        "- **This session's PR** carries the ledger, this file, the design note's, the V7 roadmap's and the audit's corrections, the parent's",
    ),
    (
        "   mechanism, of the behaviour it breaks. Of the findings Phase 11 named, F-CANOPY-065's rating is the one the ruling\n"
        "   moves, and F-CANOPY-057's only through the audit's line; leads from round 1: `CHANGELOG.md:1436-1437` for\n"
        "   F-CANOPY-060 and `:2909` for F-CANOPY-051 (ledger Phase 13, Still owed). Others may be reached by entries nobody\n"
        "   has read for them yet.",
        "   mechanism, of the behaviour it breaks. Of the findings Phase 11 named, F-CANOPY-065's rating is the one the ruling\n"
        "   moves (the four documents that recorded F-CANOPY-057's stream as shipped are corrected); leads from round 1:\n"
        "   `CHANGELOG.md:1436-1437` (`[0.8.0]`) for F-CANOPY-060 and `:2909` (`[0.6.0]`) for F-CANOPY-051 (ledger Phase 13,\n"
        "   Still owed). Others may be reached by entries nobody has read for them yet.",
    ),
    (
        "grep -c 'Correction 2026-10-19' notes/" + ROADMAP_NAME + "   # 1",
        "grep -c 'Correction 2026-10-19' notes/" + ROADMAP_NAME + "   # 1\n"
        "grep -c 'Correction 2026-10-19' notes/" + AUDIT_NAME + "   # 1",
    ),
    (
        "  - `notes/" + ROADMAP_NAME + "`: §28.1's dated correction and its g-3 row (round 1);",
        "  - `notes/" + ROADMAP_NAME + "`: §28.1's dated correction and its g-3 row (round 1); its CAN-015 row (round 2);\n"
        "  - `notes/" + AUDIT_NAME + "`: §5.2's dated correction and its g-3 row (round 2);",
    ),
]

# ---------------------------------------------------------------------------
# The parent handoff, the INDEX, the V7 roadmap, the audit
# ---------------------------------------------------------------------------

PARENT_SUBS = [
    (
        "longer promises F-CANOPY-057's stream (the V7 roadmap's §28.1 carries the same correction; the 2026-05-05 roadmap audit's\n"
        "activity line still records it, as a dated snapshot), so the first limb decides F-CANOPY-065, and F-CANOPY-057 only through that\n"
        "audit line: 9/11, 8/12, or 10/10 by the broadest reading.",
        "longer promises F-CANOPY-057's stream (the V7 roadmap's §28.1 and CAN-015 row and the 2026-05-05 roadmap audit's §5.2 carry the\n"
        "same correction), so the first limb decides F-CANOPY-065 alone among the findings Phase 11 named: 9/11 or 8/12 open P1/P2 (the\n"
        "ledger's two recorded dissents, F-CANOPY-028 and F-CANOPY-067, would move it one either way).",
    ),
    (
        "   item 30; the CAN-015g/h design note and the V7 roadmap's §28.1 are corrected. Current Lane A handoff:",
        "   item 30; the CAN-015g/h design note, the V7 roadmap's §28.1 and the 2026-05-05 roadmap audit's §5.2 are corrected.\n"
        "   Current Lane A handoff:",
    ),
]

INDEX_SUBS = [
    (
        "the CAN-015g/h design note and the V7 roadmap's §28.1 are corrected (g-3 never reached cascor `main`). Next:",
        "the CAN-015g/h design note, the V7 roadmap's §28.1 and the 2026-05-05 roadmap audit's §5.2 are corrected (g-3 never reached cascor `main`). Next:",
    ),
]

ROADMAP_SUBS = [
    (
        "8 PRs for CAN-015g (Replay V2 with per-epoch weight history)",
        "8 PRs for CAN-015g (Replay V2 with per-epoch weight history; **g-3 did not ship — see §28.1's correction of 2026-10-19**)",
    ),
]

AUDIT_SUBS = [
    (
        "### 5.2 Critical blind spot — CAN-015g and CAN-015h\n"
        "\n"
        "The roadmap (around line 5121) flags CAN-015g and CAN-015h as",
        "### 5.2 Critical blind spot — CAN-015g and CAN-015h\n"
        "\n"
        "> **Correction 2026-10-19** (the canopy E2E arc; ledger `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,\n"
        "> F-CANOPY-057 and Phase 13): **g-3 did not ship.** cascor #190, the retarget of #187, merged into\n"
        "> `feature/can-015g-2-replay-weight-cache-v2` (2026-05-03T20:05:12Z) thirteen minutes after that branch's own PR, #189,\n"
        "> had landed on `main` (19:52:10Z), so `dbc25277` is not on `main` (3 ahead, 537 behind at cascor `main` `4c26919f`,\n"
        "> 2026-10-16). This audit's own §11.4 lists what it confirmed on cascor `main`, \"#180 (g-1), #191 (g-6)\", and never\n"
        "> #189 or #190. cascor's replay frames carry no `weights` key and no replay weight has ever reached the page; canopy's\n"
        "> `docs/USER_MANUAL.md` and `notes/development/REPLAY_V2_FAQ.md` say so since canopy#684 (2026-09-24). The g-3 row\n"
        "> below is annotated. The same correction is in `JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`\n"
        "> and in §28.1 of `JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`.\n"
        "\n"
        "The roadmap (around line 5121) flags CAN-015g and CAN-015h as",
    ),
    (
        "| g-3      | cascor #190 (retarget of #187) | Sample-boundary weight emission                 |",
        "| g-3      | cascor #190 (retarget of #187) | Sample-boundary weight emission — **not on `main`**: merged into a stacked base (correction 2026-10-19; F-CANOPY-057) |",
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
        "parent": root / PARENT,
        "index": root / INDEX,
        "roadmap": root / ROADMAP,
        "audit": root / AUDIT,
    }
    texts = {k: p.read_text(encoding="utf-8") for k, p in paths.items()}

    ledger = texts["ledger"]
    if "- **Round 1**: three lanes on the frozen `566cb72a`" not in ledger or "- **Round 2**: two lanes on the frozen `c741351c`" in ledger:
        raise SystemExit("this is not the round-2 freeze (c741351c)")
    if "Correction 2026-10-19" in texts["audit"]:
        raise SystemExit("the audit already carries the 2026-10-19 correction")

    other_subs = len(PARENT_SUBS) + len(INDEX_SUBS) + len(ROADMAP_SUBS) + len(AUDIT_SUBS)
    record = (
        ROUND2_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS)))
        .replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS)))
        .replace("SUB_COUNT_OTHER", str(other_subs))
    )
    new = {}
    new["ledger"] = apply(ledger, LEDGER_SUBS, "ledger")
    if new["ledger"].count(ROUND1_TAIL) != 1:
        raise SystemExit("round-1 record tail not found exactly once")
    new["ledger"] = new["ledger"].replace(ROUND1_TAIL, ROUND1_TAIL + record)
    new["handoff"] = apply(texts["handoff"], HANDOFF_SUBS, "handoff")
    new["parent"] = apply(texts["parent"], PARENT_SUBS, "parent")
    new["index"] = apply(texts["index"], INDEX_SUBS, "index")
    new["roadmap"] = apply(texts["roadmap"], ROADMAP_SUBS, "roadmap")
    new["audit"] = apply(texts["audit"], AUDIT_SUBS, "audit")

    print(f"ledger: {len(LEDGER_SUBS)} substitutions + the round-2 record, {len(ledger)} -> {len(new['ledger'])} chars")
    print(f"handoff: {len(HANDOFF_SUBS)}; parent: {len(PARENT_SUBS)}; index: {len(INDEX_SUBS)}; roadmap: {len(ROADMAP_SUBS)}; audit: {len(AUDIT_SUBS)}")
    if args.check:
        print("--check: nothing written")
        return 0
    for k, p in paths.items():
        p.write_text(new[k], encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
