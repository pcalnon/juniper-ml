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
"""Round 1's correction pass on the ledger's Phase 13 and the files that landed with it.

Applied to the files as frozen for round 1 (local commit ``566cb72a``). Round 1's three reports are archived
verbatim in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round1.md``. Every
substitution is anchored to occur exactly once in its file. Each is credited to the lane that raised it; the
orchestrator re-derived each from the artifact or the code before applying it (the ledger's round-1 record says
what). Besides the ledger, the pass touches the new handoff, the parent consolidated handoff, the INDEX, the Phase 12
handoff's banner, the apply script's header, and -- new in this round -- the V7 roadmap's §28.1, which still recorded
g-3 as shipped (Lane 13-B, MAJOR).

Usage:
    python3 util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py [--check] [--root DIR]
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
PHASE12_HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase12-recorded-pacer-shipped-in-0-9-0-items-25-26-next.md"
APPLY_SCRIPT = "util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py"
ROADMAP = "notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"

ROADMAP_NAME = "JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md"
AUDIT_NAME = "JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md"

# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

LEDGER_SUBS = [
    # --- Summary: the owner's question (B1, MAJOR) ---
    (
        "- **The owner's question narrows.** Of the four findings Phase 11 placed within the first limb's reach, three\n"
        "  (F-CANOPY-012, -013, -018) are P1 by the manual without any ruling, and the fourth (F-CANOPY-057) is no longer\n"
        "  promised by the design note once corrected. The first limb now decides F-CANOPY-065 alone, as Phase 10 first put\n"
        "  it; the second limb still decides F-CANOPY-068's rating of record and moves no count. Item 26's second step, the\n"
        "  CHANGELOG and the design plans for every open finding, still waits on the ruling.",
        "- **The owner's question narrows.** Of the three findings Phase 11 placed within the first limb's reach\n"
        "  (F-CANOPY-057, -018, -012) and F-CANOPY-013, which it left unsettled, three (F-CANOPY-012, -013, -018) are P1 by\n"
        "  the manual without any ruling. F-CANOPY-057 was still recorded as shipped by two documents the design note's\n"
        "  correction does not touch: the V7 roadmap's §28.1 and CAN-015 row\n"
        "  (`" + ROADMAP_NAME + "`, `:15146-15160` and `:5196`) and the 2026-05-05 audit's per-repo activity table\n"
        "  (`" + AUDIT_NAME + ":112`) (round 1, Lane 13-B, MAJOR). Round 1 gave §28.1 the same dated correction; the audit\n"
        "  is a dated snapshot of commit themes and is left as history. So the first limb decides F-CANOPY-065, and\n"
        "  F-CANOPY-057 only if an audit's activity line is read as a design-plan promise; the second limb still decides\n"
        "  F-CANOPY-068's rating of record and moves no count. Item 26's second step, the CHANGELOG and the design plans\n"
        "  for every open finding, still waits on the ruling, with two leads recorded under \"Still owed\".",
    ),
    # --- Summary: counts line ---
    (
        "  P0, **9 open P1** and **11 open P2**. By ruling on the first limb alone: 9 and 11 as the triage counts them, or\n"
        "  8 and 12.",
        "  P0, **9 open P1** and **11 open P2**. By ruling on the first limb: 9 and 11 as the triage counts them, 8 and 12,\n"
        "  or 10 and 10 by the broadest reading (the audit's line; Matrix effect and counts).",
    ),
    # --- Summary: the CHANGELOG's #532 and the history (A4, B8, C3) ---
    (
        "  the four findings (its one `#532` is the 0.9.0 entry for F-CANOPY-059). Their entries stay OPEN, as Phase 4\n"
        "  ruled, until each row is re-driven live; that re-drive fell out of the numbered list when Phase 9 renumbered it,\n"
        "  and is restored here as **item 30**.",
        "  the four findings (its only `#532` mentions, three, are in the 0.9.0 entry for F-CANOPY-059). Their entries stay\n"
        "  OPEN, as Phase 4 ruled, until each row is re-driven live; that re-drive was last listed in Phase 4's own prose,\n"
        "  no Still-owed list from Phase 5's (2026-08-28) on carried it, and it is restored here as **item 30**.",
    ),
    # --- Summary: the five re-ratings' counter-readings (B dissent) ---
    (
        "  they are set against and the counter-readings are under \"The five re-ratings\". F-CANOPY-028's is the narrowest,\n"
        "  and is recorded as such.",
        "  they are set against and the counter-readings are under \"The five re-ratings\". F-CANOPY-028's is the narrowest,\n"
        "  and one round-1 lane dissents from it; F-CANOPY-012 carries a weaker counter-reading; both are recorded.",
    ),
    # --- Who, and from what: sources ---
    (
        "  `main` `4c26919f` (2026-10-16T09:33:36Z; `src/api/lifecycle/manager.py`); cascor PRs 187, 189 and 190 and the\n"
        "  compare of `main` with `dbc25277`.",
        "  `main` `4c26919f` (2026-10-16T09:33:36Z; `src/api/lifecycle/manager.py`); cascor PRs 187, 189 and 190 and the\n"
        "  compare of `main` with `dbc25277`. In this repo, after round 1: the V7 roadmap's §28.1 and CAN-015 row and the\n"
        "  2026-05-05 audit's §5.1 (named under \"The design note's correction\").",
    ),
    # --- Who, and from what: "Reached" and F-049 (A3, B4) ---
    (
        "  otherwise. A sentence that only names a surface the finding touches does not reach it: the manual names the\n"
        "  Training Metrics store's one-second updates, and F-CANOPY-049's relay defect does not stop them. A finding fixed\n"
        "  in code is rated on the behaviour it measured, as the ledger has always done; the disposition token changes on\n"
        "  the live re-drive, the rating on the evidence.",
        "  otherwise. A sentence that only names a surface the finding touches does not reach it: the manual names the\n"
        "  Training Metrics store's one-second updates, and F-CANOPY-049's relay defect does not stop them. The manual also\n"
        "  documents two surfaces fed by the fields F-CANOPY-049's measurement found frozen through a live candidate phase,\n"
        "  the Phase Duration card (\"Shows elapsed time from `phase_started_at` during active phases\", `:328`) and the\n"
        "  Candidate Metrics tab's Phase and Candidate Epoch Progress (`:686-687`). Both are conditioned on the training\n"
        "  state carrying the fields, the entry measured neither surface, and the fault that froze them, cascor forgetting\n"
        "  a socket (F-CASCOR-004), is FIXED by cascor#674; F-CANOPY-049 is the relay's failure to notice, which no sentence\n"
        "  addresses, so it is not reached. A reader who takes the other view would count 10 open P1 and 10 open P2 (round 1,\n"
        "  Lanes 13-A and 13-B). A finding fixed in code is rated on the behaviour it measured, as the ledger has always\n"
        "  done; the disposition token changes on the live re-drive, the rating on the evidence.",
    ),
    # --- the sweep table: line cites (A1) and the F-049 row (A3, B4) ---
    (
        "| F-CANOPY-018 | P2 | § Configuration Parameters: \"Edits are staged until you click **Apply** — the button enables only when a value differs from the last applied set\" (`:266-268`) |",
        "| F-CANOPY-018 | P2 | § Configuration Parameters: \"Edits are staged until you click **Apply** — the button enables only when a value differs from the last applied set\" (`:267-268`) |",
    ),
    (
        "| F-CANOPY-065 | P1 if a shipped CHANGELOG or design-plan promise counts | § Configuration Parameters says only that edits are staged until Apply and that the Parameters tab shows the applied values (`:266-269`);",
        "| F-CANOPY-065 | P1 if a shipped CHANGELOG or design-plan promise counts | § Configuration Parameters says only that edits are staged until Apply and that the Parameters tab shows the applied values (`:267-269`);",
    ),
    (
        "| F-CANOPY-049 | P2 | § Status Indicators (`:155-171`) and § Update Intervals (`:173-176`) describe the browser's connection count and the one-second metrics updates; Troubleshooting 5 (`:1144`) is the browser's socket. None describes the canopy-to-cascor relay or `/api/state`'s freshness | no | P2 |",
        "| F-CANOPY-049 | P2 | § Status Indicators (`:155-171`) and § Update Intervals (`:173-176`) describe the browser's connection count and the one-second metrics updates; Troubleshooting 5 (`:1144`) is the browser's socket. The Phase Duration card (`:328`, \"during active phases\") and the Candidate Metrics tab's Phase and progress (`:686-687`) read the fields the entry found frozen, conditioned on the state carrying them. None describes the canopy-to-cascor relay, `/api/state`'s freshness, or recovery from an upstream drop | no, with the counter-reading under \"Who, and from what\" (round 1, Lanes 13-A and 13-B) | P2 |",
    ),
    # --- The five re-ratings: F-012's residue (B3) ---
    (
        "  flat list reshaped `(I+H, output_size)` from the panel's topology store, and names what to type when it cannot.\n"
        "  A note, not a finding: the manual's Patch Weights text does not describe that row idiom; every form it names\n"
        "  still parses.",
        "  flat list reshaped `(I+H, output_size)` from the panel's topology store, and names what to type when it cannot.\n"
        "  A residue, dispositioned and not filed (round 1, Lane 13-B): `_parse_float_rows` (`:437-456`) makes newlines and\n"
        "  semicolons row separators, so the manual's semicolon- or newline-separated floats, entered for `output_weights`,\n"
        "  become one row per value and cascor rejects the shape, loudly as before; only the comma form reaches the\n"
        "  reshape. By source two of the manual's three forms still fail for this group after the fix. It is this entry's\n"
        "  own surface and row, so it gets no new id: item 30 drives the three forms, and the manual's Patch Weights\n"
        "  sentence then needs the row idiom, or the parser a single-width rule.",
    ),
    (
        "> on a leg serving that code (item 30). A note, not a finding: the manual's Patch Weights text does not describe\n"
        "> the row idiom #535 added; every form it names still parses.",
        "> on a leg serving that code (item 30). A residue, dispositioned and not filed (Phase 13, round 1, Lane 13-B):\n"
        "> `_parse_float_rows` (`:437-456`) makes newlines and semicolons row separators, so the manual's semicolon- or\n"
        "> newline-separated floats for `output_weights` become one row per value and cascor rejects the shape, loudly;\n"
        "> only the comma form reaches the reshape. Item 30 drives all three forms; the manual's Patch Weights sentence\n"
        "> then needs the row idiom, or the parser a single-width rule.",
    ),
    # --- The five re-ratings: F-028's dissent (B dissent) ---
    (
        "  the narrowest of the five, and a validator who takes the other reading moves the P1 count from 9 to 8. **In\n"
        "  code:** canopy#533's `_merge_pinned_params` writes only what it can observe.",
        "  the narrowest of the five, and a validator who takes the other reading moves the P1 count from 9 to 8: in\n"
        "  round 1 Lane 13-B took it and rates this finding P2, Lane 13-A rated it P1, narrowly, and the orchestrator keeps\n"
        "  P1 and records the dissent (Consensus record). **In code:** canopy#533's `_merge_pinned_params` writes only what\n"
        "  it can observe.",
    ),
    # --- The five re-ratings: F-032's two inductions (B5) ---
    (
        "  fails\". Segment 16 measured it absent for 60 s under each of two inductions while canopy's own API carried the\n"
        "  error. Phase 4's correction to the entry stands:",
        "  fails\". Segment 16 measured it absent for 60 s under each of two inductions, with canopy's own API carrying the\n"
        "  error under the cascor-down one. Phase 4's correction to the entry stands:",
    ),
    (
        "> (dismissable)\" (`docs/USER_MANUAL.md:732` at canopy `main` `571743db`). Segment 16 measured the alert absent for\n"
        "> 60 s under each of two inductions while canopy's own API reported the error. The correction above stands: the\n",
        "> (dismissable)\" (`docs/USER_MANUAL.md:732` at canopy `main` `571743db`). Segment 16 measured the alert absent for\n"
        "> 60 s under each of two inductions, with canopy's own API carrying the error under the cascor-down one. The\n"
        "> correction above stands: the\n",
    ),
    # --- F-018 blockquote line cite (A1) ---
    (
        "> set\" (`docs/USER_MANUAL.md:266-268` at canopy `main` `571743db`). Segment 12 measured the opposite after a",
        "> set\" (`docs/USER_MANUAL.md:267-268` at canopy `main` `571743db`). Segment 12 measured the opposite after a",
    ),
    # --- F-065 status bullet line cite (A1) ---
    (
        "  (`docs/USER_MANUAL.md:266-269`); no sentence describes what the toast reports. The rating stays with the owner's\n"
        "  first limb, which after Phase 13 decides this entry alone (Phase 13, Matrix effect and counts).",
        "  (`docs/USER_MANUAL.md:267-269`); no sentence describes what the toast reports. The rating stays with the owner's\n"
        "  first limb, which after Phase 13 decides this entry, and F-CANOPY-057 only through a dated audit's activity line\n"
        "  (Phase 13, Matrix effect and counts).",
    ),
    # --- F-057 status bullet (B1) ---
    (
        "  correction item 26 required: g-3 never reached `main`. With that it no longer records the stream as shipped, and\n"
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13).",
        "  correction item 26 required: g-3 never reached `main`. With that it no longer records the stream as shipped, and\n"
        "  the owner's first limb (O17) does not reach this entry through it (Phase 13). The V7 roadmap's §28.1\n"
        "  (`" + ROADMAP_NAME + "`) carries the same correction since Phase 13's round 1; the 2026-05-05 audit's activity line\n"
        "  (`" + AUDIT_NAME + ":112`) still reads \"CAN-015g replay V2 wired\" and is left as a dated snapshot, the one document\n"
        "  through which the first limb could still reach this entry.",
    ),
    # --- The design note's correction: the roadmap and the audit (B1) ---
    (
        "in the note was re-verified; the correction is scoped to g-3 and to the \"decision-boundary animation with\n"
        "per-unit weight evolution\" its summary describes, which has not shipped. With that, the note no longer records\n"
        "the weight stream as implemented, and F-CANOPY-057 is not within reach of the owner's first limb through it; its\n"
        "P2 rests on the manual's and the FAQ's current text, as since Phase 10.",
        "in the note was re-verified; the correction is scoped to g-3 and to the \"decision-boundary animation with\n"
        "per-unit weight evolution\" its summary describes, which has not shipped. With that, the note no longer records\n"
        "the weight stream as implemented, and F-CANOPY-057 is not within reach of the owner's first limb through it; its\n"
        "P2 rests on the manual's and the FAQ's current text, as since Phase 10 (the FAQ's status note of 2026-09-24 was\n"
        "re-read at `571743db` in round 1, Lane 13-B).\n"
        "\n"
        "Two other documents recorded g-3 as shipped (round 1, Lane 13-B, MAJOR): the V7 roadmap's §28.1, \"CAN-015g +\n"
        "CAN-015h — Phase 6E deferred, shipped end-to-end\", whose g-3 row read \"cascor #190 (retarget of #187) |\n"
        "Sample-boundary weight emission | `dbc25277`\" (`" + ROADMAP_NAME + ":15146-15160`), and its CAN-015 row, which\n"
        "counts \"8 PRs for CAN-015g\" as shipped end-to-end and points to §28.1 (`:5196`); and the 2026-05-05 audit's per-repo\n"
        "commit table, \"CAN-015g replay V2 wired\" under juniper-canopy (`" + AUDIT_NAME + ":112`). Round 1 gave §28.1 the\n"
        "same dated correction, a note under its heading and the g-3 row annotated; the CAN-015 row points to §28.1 and is\n"
        "left. The audit is a dated snapshot of commit themes since 2026-04-23, not a plan's promise, and is left as\n"
        "history. Until the owner rules, the first limb reaches F-CANOPY-057 only through that audit line.",
    ),
    # --- What this phase cannot support (B3, B dissent) ---
    (
        "- Whether the four fixes work on a live page is not known to this ledger. Phase 4 brought up no stack, and no\n"
        "  later phase drove their rows. Their re-drive is item 30.",
        "- Whether the four fixes work on a live page is not known to this ledger. Phase 4 brought up no stack, and no\n"
        "  later phase drove their rows. Their re-drive is item 30. The F-CANOPY-012 residue, two of the manual's forms read\n"
        "  as rows, is by source; no page has sent one.\n"
        "- The two CHANGELOG leads under \"Still owed\" are a lane's reading of two entries, not ratings; the second step\n"
        "  was not done.",
    ),
    # --- Matrix effect: the rows (A2) ---
    (
        "- No matrix row changes: this phase drove no row. The rows whose FAIL halves carry the five re-rated findings are\n"
        "  C2.9-05 (F-CANOPY-018), M-WORKERS-02 (F-CANOPY-032), M-NETWORK-EDITOR-09 and -13 (F-CANOPY-013) and\n"
        "  M-NETWORK-EDITOR-17 (F-CANOPY-012); F-CANOPY-028's rows, M-PARAMETERS-04/-05/-06, read PASS with the pin value\n"
        "  \"pending an Apply\", and Phase 4 named them for its re-drive.",
        "- No matrix row changes: this phase drove no row. The rows whose FAIL, or FAIL half, rests on the five re-rated\n"
        "  findings are C2.9-05 (FAIL, F-CANOPY-018), M-WORKERS-02 (FAIL; the row names no id, and the F-CANOPY-032 entry\n"
        "  names the row), M-NETWORK-EDITOR-09 and -13 (FAIL half, F-CANOPY-013) and M-NETWORK-EDITOR-17 (FAIL half,\n"
        "  F-CANOPY-012); F-CANOPY-028's rows, M-PARAMETERS-04/-05/-06, read PASS, -05 with its value \"pending an Apply\",\n"
        "  and Phase 4 named them for its re-drive.",
    ),
    # --- Matrix effect: the owner's question (B1, B dissent) ---
    (
        "  - **The owner's question** (O17): the first limb now decides F-CANOPY-065 alone: 9 open P1 and 11 open P2 if a\n"
        "    shipped CHANGELOG or design-plan promise counts as documented, as the triage counts them, else 8 and 12. The\n"
        "    second limb decides F-CANOPY-068's rating of record and moves no count. F-CANOPY-028 is the one re-rating a\n"
        "    different reading of the manual would reverse (above), which would make those 8 and 12, or 7 and 13.",
        "  - **The owner's question** (O17): the first limb decides F-CANOPY-065, and F-CANOPY-057 only if the 2026-05-05\n"
        "    audit's activity line counts as a design-plan promise: 9 open P1 and 11 open P2 if a shipped CHANGELOG or\n"
        "    design-plan promise counts as documented, as the triage counts them; 8 and 12 if not; 10 and 10 by the\n"
        "    broadest reading. The second limb decides F-CANOPY-068's rating of record and moves no count. F-CANOPY-028 is\n"
        "    the re-rating most exposed to a different reading of the manual (one round-1 lane dissents; \"The five\n"
        "    re-ratings\"), which would make each of those pairs one P1 fewer; F-CANOPY-012's counter-reading, that the\n"
        "    manual's \"lets CasCor validate the exact target shape\" makes a shape rejection the documented outcome, is\n"
        "    weaker and no lane adopted it.",
    ),
    # --- Still owed: item 26's second step (B1, B dissent leads, C2) ---
    (
        "- **Item 26's first step is DONE**: every open finding has been checked against canopy's manual. Its second step\n"
        "  stays, and narrows: once the owner rules, check each open finding not yet rated on canopy's CHANGELOG and the\n"
        "  design plans for a promise, or, if the ruling counts it, a description of an internal mechanism, of the\n"
        "  behaviour it breaks; of the four findings Phase 11 named, F-CANOPY-065 is the only one the ruling can still\n"
        "  move, and the CAN-015g/h design note's correction is applied.\n"
        "- **Item 18** is unchanged; F-CANOPY-064's P1 stands.",
        "- **Item 26's first step is DONE**: every open finding has been checked against canopy's manual. Its second step\n"
        "  stays: once the owner rules, check each open finding not yet rated on canopy's CHANGELOG and the design plans\n"
        "  for a promise, or, if the ruling counts it, a description of an internal mechanism, of the behaviour it breaks.\n"
        "  Of the findings Phase 11 named, F-CANOPY-065 is the one the ruling moves, and F-CANOPY-057 only through the\n"
        "  2026-05-05 audit's line, the design note and the V7 roadmap's §28.1 carrying the dated correction. Two leads a\n"
        "  round-1 lane found for that step, unswept (Lane 13-B): canopy's CHANGELOG `[0.8.0]` says the producer's own\n"
        "  sentence \"survives to the modal\" (`CHANGELOG.md:1436-1437` at `571743db`), which is what F-CANOPY-060 cuts; and\n"
        "  `[0.5.0]`'s \"one tab-persistence system\" (`:2909`) for F-CANOPY-051, weaker.\n"
        "- **Item 18** is unchanged; F-CANOPY-064's P1 stands. Its F-CANOPY-067 drive also settles that entry's rating\n"
        "  under the F-CANOPY-056 standard: P1 if a page shows the zeros persisting, as source says (one round-1 lane would\n"
        "  rate it P1 by source today; Consensus record).",
    ),
    # --- Still owed: item 30 (A4, B3, B6, B7, C3) ---
    (
        "30. **The Phase 4 fix wave's live re-drive**, owed since 2026-08-28 (Phase 4, \"Still owed (unchanged, plus)\") and\n"
        "    carried by no numbered item since Phase 9 renumbered the list; now owed at P1 for four of its findings. On a\n"
        "    leg serving canopy 0.9.0 or later (every release from 0.7.0 carries the fixes), drive:\n"
        "    - **M-NETWORK-EDITOR-17** for F-CANOPY-012 (all four targets; `output_weights` as rows and as a flat list,\n"
        "      and a wrong-count flat list for the new message) and **M-NETWORK-EDITOR-09 and -13** for F-CANOPY-013 (the\n"
        "      alert's index and count on a successful append and remove): a service leg whose cascor can be restored into\n"
        "      `Investigating`, so a writable cascor, never the trio;\n"
        "    - **C2.9-05** for F-CANOPY-018 (Apply disabled and `params-status` clean after a successful apply; the toast's\n"
        "      ~900 ms life, which the fix was not written for, read as it is) and **M-PARAMETERS-04/-05/-06** for\n"
        "      F-CANOPY-028 (pin, reload, pin again; the first set must survive): the controls are canopy-side and the\n"
        "      manual says they work in both modes, so a demo leg is expected to reach them, to be confirmed on the drive;",
        "30. **The Phase 4 fix wave's live re-drive**, owed since 2026-08-28 (Phase 4, \"Still owed (unchanged, plus)\"), last\n"
        "    listed there and carried by no Still-owed list from Phase 5's on; now owed at P1 for four of its findings. On a\n"
        "    leg serving canopy 0.9.0 or later (every release from 0.7.0 carries the fixes), drive:\n"
        "    - **M-NETWORK-EDITOR-17** for F-CANOPY-012 (all four targets; `output_weights` in each of the manual's three\n"
        "      forms, comma-, semicolon- and newline-separated, as rows, and as a wrong-count flat list for the new message;\n"
        "      by source the semicolon and newline forms become one row per value and are rejected) and\n"
        "      **M-NETWORK-EDITOR-09 and -13** for F-CANOPY-013 (the alert's index and count on a successful append and\n"
        "      remove): a service leg whose cascor can be restored into `Investigating`, so a writable cascor, never the trio;\n"
        "    - **C2.9-05** for F-CANOPY-018 (the row's own expectation, the toast; and, as an added expectation scored\n"
        "      separately, Apply disabled and `params-status` clean after a successful apply; the toast's ~900 ms life, which\n"
        "      the fix was not written for, read as it is) and **M-PARAMETERS-04/-05/-06** for F-CANOPY-028 (pin, reload, pin\n"
        "      again; the first set must survive): the sidebar's Apply controls work in both modes by the manual (`:285`),\n"
        "      and the pins and the dirty tracker are canopy-side by source, so a demo leg is expected to reach them, to be\n"
        "      confirmed on the drive;",
    ),
    (
        "    Each entry's header token changes only on its own row's result. F-CANOPY-032's result either closes the entry\n"
        "    or re-diagnoses it. The F-CANOPY-012 drive should also say whether the manual's Patch Weights sentence needs\n"
        "    the row idiom.",
        "    Each entry's header token changes only on its own row's result. F-CANOPY-032's result either closes the entry\n"
        "    or re-diagnoses it. The F-CANOPY-012 drive also settles the residue above: whether the manual's Patch Weights\n"
        "    sentence gets the row idiom, or the parser a single-width rule.",
    ),
]

ROUND1_RECORD = """- **Round 1**: three lanes on the frozen `566cb72a`, briefed separately with different entry points. Briefs are in
  `reports/e2e-canopy-2026-09-02/drafts/lane13{A,B,C}_phase13_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round1.md`.
  - Lane 13-A rated the twenty open findings from the manual first, with the entries read at `main` `ad6013f4` so
    the phase's ratings could not leak, then compared, then re-derived every manual, GitHub, source, triage, matrix
    and ledger fact. Its twenty ratings equal the phase's, and every fact held.
  - Lane 13-B was adversarial on the re-ratings: each of the five, the ten not reached, the owner's question, the
    counts, item 30, and what was stated that was inferred.
  - Lane 13-C replayed the apply pass from `ad6013f4` (all six files byte-identical, no hand edit), checked the seven
    files against each other, the rest of the ledger, the matrix, the repo's tests and conventions and GitHub, and
    ran the handoff's verification commands.
  - The lanes' own probes are in their scratch directories and were not archived: each was a reading of the manual,
    a `gh` query or a run of the repo's own tools, and none produced a figure the ledger rests on that those do not
    reproduce.
- **Verdicts.** All three returned SOUND-WITH-FIXES. Lane 13-B's MAJOR changes an action and the ruling's alternative
  counts (two other documents still recorded g-3 as shipped, so "the first limb now decides F-CANOPY-065 alone" did
  not hold), its finding on canopy#535's row parser changes item 30, and a handoff verification command expected the
  wrong number (Lanes 13-B and 13-C), so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
  requires round 2. No lane refuted a re-rating, the triage's counts or any entry's disposition; one lane dissents
  on F-CANOPY-028 and on F-CANOPY-067 (below).
- **What round 1 changed:**
  - the owner's question: the V7 roadmap's §28.1 and CAN-015 row and the 2026-05-05 audit's activity line still
    recorded g-3 as shipped (Lane 13-B, MAJOR). §28.1 now carries the same dated correction as the design note
    (`JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`: a note under
    the heading and the g-3 row annotated), the audit is left as a dated snapshot, and the ruling's alternatives are
    9/11, 8/12 or 10/10 by the broadest reading, in the Summary, "The design note's correction", the Matrix effect,
    F-CANOPY-057's and F-CANOPY-065's Status bullets, "Still owed", the handoff, the parent's O17 and the INDEX;
  - the F-CANOPY-012 residue: `_parse_float_rows` makes newlines and semicolons row separators, so two of the
    manual's three forms are read as one row per value and rejected by source; "every form it names still parses"
    is withdrawn, the residue is dispositioned in the entry and under "The five re-ratings", not filed, and item 30
    drives all three forms (Lane 13-B);
  - the handoff's `grep -c 'P1 '` expected 9 and prints 10, the triage's summary line matching too; it is now
    anchored to the row prefix (Lanes 13-B and 13-C);
  - F-CANOPY-049's row and the "Reached" paragraph name the Phase Duration card (`:328`) and the Candidate Metrics
    tab's Phase and progress (`:686-687`), which read the fields the entry found frozen, and say why they do not
    reach it: both are conditioned on the state carrying the fields, neither surface was measured, and the trigger,
    F-CASCOR-004, is FIXED; the other reading would count 10 and 10 (Lanes 13-A and 13-B);
  - "the four findings Phase 11 placed within the first limb's reach" now reads as Phase 11 wrote it: three within
    reach and F-CANOPY-013 unsettled (Lane 13-C);
  - the fix wave's re-drive was last listed in Phase 4's prose and carried by no Still-owed list from Phase 5's on,
    not "since Phase 9 renumbered"; the Summary, item 30 and the handoff say so (Lanes 13-A and 13-C);
  - item 26's second step records two CHANGELOG leads a lane found, unswept: `[0.8.0]`'s "survives to the modal"
    for F-CANOPY-060 and `[0.5.0]`'s tab-persistence entry for F-CANOPY-051 (Lane 13-B);
  - item 30: C2.9-05's own expectation is the toast, and the Apply-disabled check is an added expectation scored
    separately; the demo-leg expectation rests on the manual for the Apply controls and on source for the pins
    (Lane 13-B);
  - wording: the manual's Apply sentence starts at `:267` (Lane 13-A); only M-PARAMETERS-05 carries "pending an
    Apply", M-WORKERS-02 and C2.9-05 are whole-row FAILs and M-WORKERS-02's row names no id (Lane 13-A); the
    CHANGELOG's `#532` appears three times in one entry (Lane 13-B); F-CANOPY-032's two inductions, the API carrying
    the error under the cascor-down one (Lane 13-B); F-CANOPY-012's weaker counter-reading, recorded beside
    F-CANOPY-028's (Lane 13-B); the plan, the matrix and the ledger named by filename in the handoff and the banner,
    and the banner's "item 3's first half" (Lanes 13-B and 13-C); the apply script's header gains the `Retire when:`
    and `Related:` lines `util/ad-hoc/README.md` asks for (Lane 13-C).
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py`,
    SUB_COUNT_LEDGER substitutions in the ledger, SUB_COUNT_HANDOFF in the handoff and SUB_COUNT_OTHER across the
    parent handoff, the INDEX, the Phase 12 handoff's banner, the apply script and the V7 roadmap.
- **Re-derived by the orchestrator before applying:**
  - the V7 roadmap's §28.1 heading, g-3 row (`:15156`) and CAN-015 row (`:5196`), the audit's line (`:112`), and
    that the roadmap was last changed on 2026-07-04;
  - `_parse_float_rows` (`network_editor_panel.py:437-456` at `571743db`): `text.replace(";", "\\n").split("\\n")`,
    one row per line, and `_resolve_patch_values`' `len(rows) > 1` branch returning the rows unchanged;
  - the manual's `:266` (the env-var line), `:267-269`, `:328`, `:686-687` and `:285`; the matrix's `:807` (FAIL, no
    id) and `:822-824`; Phase 5's Still owed (F-039, F-037, F-038, F-036 and F-026 only); Phase 11's "three open
    P2s are already known to be within reach" and "F-CANOPY-013 … unsettled";
  - the `grep -c` figures, 10 and 9; F-CASCOR-004's header, FIXED by cascor#674; the CHANGELOG's `#532` at `:534`,
    `:535` and `:541` and the two lead entries at `:1436-1437` and `:2909`; `util/ad-hoc/README.md:17-31`;
    F-CANOPY-056's Severity, "re-rated P1, on plan §6.3's rule", on source and a hand-built probe, "not been driven
    live".
- **Not applied.** Lane 13-B's suggestion to correct the 2026-05-05 audit as well: it is a dated snapshot of commit
  themes, not a plan, and is recorded instead. Lanes 13-B's and 13-C's note that the handoff describes the landed
  state (a PR, signed commits, archived reports) before it exists: checked at landing, as Phase 12 did. Lane 13-C's
  note that the five headers name a second severity in prose: F-CANOPY-057's header is the precedent, and the triage
  reads the first token.
- **Unresolved dissent.**
  - **F-CANOPY-028**: Lane 13-B rates it P2 (the manual's sentence promises survival of a reload, which the store did;
    the discard is a writer defect no sentence describes; the ledger read the manual literally for F-CANOPY-057).
    Lane 13-A rates it P1, narrowly. The orchestrator keeps P1, on what a user following the manual sees, and
    records the dissent; by Lane 13-B's reading the counts are 8 and 12.
  - **F-CANOPY-067**: Lane 13-B holds that "unchanged" applies a stricter standard than F-CANOPY-056's, which was
    rated P1 on source and a hand-built probe before any live drive, so by that precedent F-CANOPY-067 is P1 by
    source today (10 and 10), the live drive deciding the disposition. The orchestrator keeps Phase 10's "P2
    pending a live drive": that condition was set after five rounds on whether a page shows the zeros, and this
    phase's instrument, the manual, adds nothing to it; item 18's drive decides the rating under the F-CANOPY-056
    standard.
- **What the evidence cannot support** is unchanged from "What this phase cannot support", with the additions made
  there. The instrument of this phase is a reading of one file and of the GitHub API; it could have produced a
  different answer wherever a sentence was missed, and round 1's two independent readings of the manual (Lane 13-A's
  twenty answers; Lane 13-B's attacks on the ten not reached) found one such place, F-CANOPY-049, recorded above.
- **Slips.** None reported."""

# ---------------------------------------------------------------------------
# The handoff
# ---------------------------------------------------------------------------

HANDOFF_SUBS = [
    (
        "python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c 'P1 '   # 9",
        "python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 9",
    ),
    (
        "grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md   # 2",
        "grep -c 'Correction 2026-10-19' notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md   # 2\n"
        "grep -c 'Correction 2026-10-19' notes/" + ROADMAP_NAME + "   # 1",
    ),
    (
        "  `main` `571743db` (2026-10-17, the head after the v0.9.0 release), under plan §6.3's rule (P1 = \"breaks a documented\n"
        "  behaviour\") and the ledger's own precedents (F-CANOPY-056, F-CANOPY-057, F-CANOPY-064).",
        "  `main` `571743db` (2026-10-17, the head after the v0.9.0 release), under §6.3 of\n"
        "  `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (P1 = \"breaks a documented behaviour\")\n"
        "  and the ledger's own precedents (F-CANOPY-056, F-CANOPY-057, F-CANOPY-064).",
    ),
    (
        "    F-ML-002); F-CASCOR-001/-002 P1 already; F-CANOPY-064 P1 on the manual already; F-CANOPY-065 not reached (its rating\n"
        "    stays with the owner's first limb, which now decides it alone); F-CANOPY-067 \"P2 pending a live drive\", unchanged.",
        "    F-ML-002); F-CASCOR-001/-002 P1 already; F-CANOPY-064 P1 on the manual already; F-CANOPY-065 not reached (its rating\n"
        "    stays with the owner's first limb, which now decides it, and F-CANOPY-057 only through the 2026-05-05 audit's\n"
        "    activity line); F-CANOPY-067 \"P2 pending a live drive\", unchanged. One round-1 lane dissents on F-CANOPY-028 (P2)\n"
        "    and on F-CANOPY-067 (P1 by source); both are recorded in the ledger's consensus record.",
    ),
    (
        "  - **Counts**: 79 findings, 56 fixed, 1 accepted, 2 withdrawn, **20 open**: 0 P0, **9 P1** (F-CANOPY-012, -013, -018,\n"
        "    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11 or 8/12.",
        "  - **Counts**: 79 findings, 56 fixed, 1 accepted, 2 withdrawn, **20 open**: 0 P0, **9 P1** (F-CANOPY-012, -013, -018,\n"
        "    -028, -032, -064, -065, F-CASCOR-001, -002), **11 P2**. By the first limb's ruling: 9/11, 8/12, or 10/10 by the\n"
        "    broadest reading.",
    ),
    (
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s.",
        "    `dbc25277` 3 ahead / 537 behind `4c26919f`). F-CANOPY-057 re-confirmed at both current `main`s. The V7 roadmap's\n"
        "    §28.1 (`notes/" + ROADMAP_NAME + "`) carries the same dated correction since round 1; the 2026-05-05 audit's line\n"
        "    (`notes/" + AUDIT_NAME + ":112`) is left as a dated snapshot. canopy#535's residue is recorded in F-CANOPY-012's\n"
        "    entry: by source the manual's semicolon and newline forms for `output_weights` are read as rows and rejected.",
    ),
    (
        "  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no numbered item since\n"
        "    Phase 9's renumbering.",
        "  - **New item 30**: the Phase 4 fix wave's live re-drive, owed since 2026-08-28 and carried by no Still-owed list\n"
        "    since Phase 5's.",
    ),
    (
        "- **This session's PR** carries the ledger, this file, the design note's correction, the parent's item 4 and O17, the\n"
        "  INDEX's P2 row, the SUPERSEDED banner on the Phase 12 handoff, Phase 13's consensus records (briefs, verbatim\n"
        "  reports, replayable passes) and the apply script `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`. Find it\n"
        "  with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all`.",
        "- **This session's PR** carries the ledger, this file, the design note's and the V7 roadmap's corrections, the parent's\n"
        "  item 4 and O17, the INDEX's P2 row, the SUPERSEDED banner on the Phase 12 handoff, Phase 13's consensus records\n"
        "  (briefs, verbatim reports, replayable passes) and the apply script `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`.\n"
        "  Find it with `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase13 --state all`.",
    ),
    (
        "   - M-NETWORK-EDITOR-17 (F-CANOPY-012: all four targets; `output_weights` as rows, as a flat list, and a wrong-count\n"
        "     flat list) and M-NETWORK-EDITOR-09/-13 (F-CANOPY-013: the alert's index and count on a successful append and\n"
        "     remove) need a service leg whose cascor can be restored into `Investigating`: a writable cascor, never the trio.\n"
        "   - C2.9-05 (F-CANOPY-018: Apply disabled and `params-status` clean after a successful apply) and M-PARAMETERS-04/-05/-06\n"
        "     (F-CANOPY-028: pin, reload, pin again) are canopy-side; a demo leg is expected to reach them.",
        "   - M-NETWORK-EDITOR-17 (F-CANOPY-012: all four targets; `output_weights` in the manual's three forms, as rows, and as\n"
        "     a wrong-count flat list; by source the semicolon and newline forms are read as rows and rejected) and\n"
        "     M-NETWORK-EDITOR-09/-13 (F-CANOPY-013: the alert's index and count on a successful append and remove) need a\n"
        "     service leg whose cascor can be restored into `Investigating`: a writable cascor, never the trio.\n"
        "   - C2.9-05 (F-CANOPY-018: the toast, and as an added expectation scored separately, Apply disabled and `params-status`\n"
        "     clean after a successful apply) and M-PARAMETERS-04/-05/-06 (F-CANOPY-028: pin, reload, pin again): the Apply\n"
        "     controls work in both modes by the manual, the pins by source; a demo leg is expected to reach them.",
    ),
    (
        "   - At P2: C2.1-01/02 (F-CANOPY-001); M-METRICS-03 (F-CANOPY-026's row, still FAIL in the matrix). F-CANOPY-034 has no row.",
        "   - At P2: C2.1-01/02 (F-CANOPY-001); M-METRICS-03 (F-CANOPY-026's row, still FAIL in\n"
        "     `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`). F-CANOPY-034 has no row.",
    ),
    (
        "   mechanism, of the behaviour it breaks. Only F-CANOPY-065's rating can still move among the four Phase 11 named;\n"
        "   the others may be reached by entries nobody has read for them yet.",
        "   mechanism, of the behaviour it breaks. Of the findings Phase 11 named, F-CANOPY-065's rating is the one the ruling\n"
        "   moves, and F-CANOPY-057's only through the audit's line; leads from round 1: `CHANGELOG.md:1436-1437` for\n"
        "   F-CANOPY-060 and `:2909` for F-CANOPY-051 (ledger Phase 13, Still owed). Others may be reached by entries nobody\n"
        "   has read for them yet.",
    ),
    (
        "- **canopy's CHANGELOG does not name the Phase 4 fix wave.** canopy#532/#533/#535 are in v0.7.0 (the `compare` API\n"
        "  says `behind`, 0 ahead) but no entry names them or their findings; do not infer \"unshipped\" from the CHANGELOG.",
        "- **canopy's CHANGELOG does not name the Phase 4 fix wave.** canopy#532/#533/#535 are in v0.7.0 (the `compare` API\n"
        "  says `behind`, 0 ahead) but no fix entry names them or their findings (canopy#532 appears only inside the 0.9.0\n"
        "  entry for F-CANOPY-059); do not infer \"unshipped\" from the CHANGELOG.",
    ),
    (
        "  - `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`: the header's Status and\n"
        "    Last updated, the dated correction under the status block, the two g-3 rows;",
        "  - `notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`: the header's Status and\n"
        "    Last updated, the dated correction under the status block, the two g-3 rows;\n"
        "  - `notes/" + ROADMAP_NAME + "`: §28.1's dated correction and its g-3 row (round 1);",
    ),
]

# ---------------------------------------------------------------------------
# The parent handoff, the INDEX, the Phase 12 handoff's banner, the apply script
# ---------------------------------------------------------------------------

PARENT_SUBS = [
    (
        "longer promises F-CANOPY-057's stream, so the first limb decides F-CANOPY-065 alone: 9/11 or 8/12 open P1/P2.",
        "longer promises F-CANOPY-057's stream (the V7 roadmap's §28.1 carries the same correction; the 2026-05-05 roadmap audit's\n"
        "activity line still records it, as a dated snapshot), so the first limb decides F-CANOPY-065, and F-CANOPY-057 only through that\n"
        "audit line: 9/11, 8/12, or 10/10 by the broadest reading.",
    ),
    (
        "   item 30; the CAN-015g/h design note is corrected. Current Lane A handoff:",
        "   item 30; the CAN-015g/h design note and the V7 roadmap's §28.1 are corrected. Current Lane A handoff:",
    ),
]

INDEX_SUBS = [
    (
        "owed their live re-drive (new item 30); the CAN-015g/h design note is corrected. Next:",
        "owed their live re-drive (new item 30); the CAN-015g/h design note and the V7 roadmap's §28.1 are corrected (g-3 never reached cascor `main`). Next:",
    ),
]

PHASE12_SUBS = [
    (
        "> Its item 1 (juniper-ml#2263 merged 2026-10-19T08:49:20Z) and item 3 (item 26's first step, the manual sweep, recorded as\n"
        "> the ledger's Phase 13) are done; items 2, 4, 5, 6 and 7 carry there, with a new item 30 (the Phase 4 fix wave's live\n"
        "> re-drive, four of its findings now P1).",
        "> Its item 1 (juniper-ml#2263 merged 2026-10-19T08:49:20Z) and item 3's first half (item 26's first step, the manual\n"
        "> sweep, and the CAN-015g/h design note's correction, recorded as Phase 13 of\n"
        "> `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) are done; item 3's second half (the CHANGELOG\n"
        "> and the design plans, after the ruling) and items 2, 4, 5, 6 and 7 carry there, with a new item 30 (the Phase 4 fix\n"
        "> wave's live re-drive, four of its findings now P1).",
    ),
]

APPLY_SCRIPT_SUBS = [
    (
        "# Status      : ad-hoc — one-off apply pass; RETAINED as provenance (owner policy 2026-08-25)\n"
        "# ---------------------------------------------------------------------------\n",
        "# Status      : ad-hoc — one-off apply pass; RETAINED as provenance (owner policy 2026-08-25)\n"
        "# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)\n"
        "# Related     : ledger Phase 13 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);\n"
        "#               HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md\n"
        "# ---------------------------------------------------------------------------\n",
    ),
]

ROADMAP_SUBS = [
    (
        "### 28.1 CAN-015g + CAN-015h — Phase 6E deferred, shipped end-to-end\n"
        "\n"
        "The original v7.0.0 roadmap (line ~5121, since updated to `✅ Shipped`) flagged these as **deferred to dedicated post-Phase-6E sprints**. Both shipped in full between 2026-05-03 and 2026-05-05.\n",
        "### 28.1 CAN-015g + CAN-015h — Phase 6E deferred, shipped end-to-end\n"
        "\n"
        "> **Correction 2026-10-19** (the canopy E2E arc; ledger `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,\n"
        "> F-CANOPY-057 and Phase 13): **g-3 did not ship.** cascor #190, the retarget of #187, merged into\n"
        "> `feature/can-015g-2-replay-weight-cache-v2` (2026-05-03T20:05:12Z) thirteen minutes after that branch's own PR, #189,\n"
        "> had landed on `main` (19:52:10Z), so `dbc25277` is not on `main` (3 ahead, 537 behind at cascor `main` `4c26919f`,\n"
        "> 2026-10-16). cascor's replay frames carry no `weights` key (`src/api/lifecycle/manager.py`, `_emit_frame`), canopy's\n"
        "> relay would drop one (`src/backend/cascor_service_adapter.py`, `_to_dashboard_metric`), and no replay weight has ever\n"
        "> reached the page; canopy's `docs/USER_MANUAL.md` and `notes/development/REPLAY_V2_FAQ.md` have said so since\n"
        "> canopy#684 (2026-09-24). The g-3 row below is annotated. CAN-015g's write side shipped (g-1, g-2, g-6); its replay\n"
        "> side did not (g-3), and the canopy consumers g-4 and g-7 shipped with no live input. The same correction is in\n"
        "> `JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`.\n"
        "\n"
        "The original v7.0.0 roadmap (line ~5121, since updated to `✅ Shipped`) flagged these as **deferred to dedicated post-Phase-6E sprints**. Both shipped in full between 2026-05-03 and 2026-05-05.\n",
    ),
    (
        "| g-3 | [cascor #190](https://github.com/pcalnon/juniper-cascor/pull/190) (retarget of #187) | Sample-boundary weight emission | `dbc25277` |",
        "| g-3 | [cascor #190](https://github.com/pcalnon/juniper-cascor/pull/190) (retarget of #187) | Sample-boundary weight emission — **not on `main`**: merged into a stacked base (correction 2026-10-19; F-CANOPY-057) | `dbc25277` (not an ancestor of `main`) |",
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
        "phase12": root / PHASE12_HANDOFF,
        "apply_script": root / APPLY_SCRIPT,
        "roadmap": root / ROADMAP,
    }
    texts = {k: p.read_text(encoding="utf-8") for k, p in paths.items()}

    ledger = texts["ledger"]
    if "CONSENSUS_RECORD_PENDING" not in ledger or "- **Round 1**: three lanes on the frozen `566cb72a`" in ledger:
        raise SystemExit("this is not the round-1 freeze (566cb72a)")
    if "Correction 2026-10-19" in texts["roadmap"]:
        raise SystemExit("the V7 roadmap already carries the 2026-10-19 correction")

    other_subs = len(PARENT_SUBS) + len(INDEX_SUBS) + len(PHASE12_SUBS) + len(APPLY_SCRIPT_SUBS) + len(ROADMAP_SUBS)
    record = (
        ROUND1_RECORD.replace("SUB_COUNT_LEDGER", str(len(LEDGER_SUBS)))
        .replace("SUB_COUNT_HANDOFF", str(len(HANDOFF_SUBS)))
        .replace("SUB_COUNT_OTHER", str(other_subs))
    )
    new = {}
    new["ledger"] = apply(ledger, LEDGER_SUBS, "ledger")
    if new["ledger"].count("CONSENSUS_RECORD_PENDING") != 1:
        raise SystemExit("consensus placeholder not found exactly once")
    new["ledger"] = new["ledger"].replace("CONSENSUS_RECORD_PENDING", record)
    new["handoff"] = apply(texts["handoff"], HANDOFF_SUBS, "handoff")
    new["parent"] = apply(texts["parent"], PARENT_SUBS, "parent")
    new["index"] = apply(texts["index"], INDEX_SUBS, "index")
    new["phase12"] = apply(texts["phase12"], PHASE12_SUBS, "phase12 handoff")
    new["apply_script"] = apply(texts["apply_script"], APPLY_SCRIPT_SUBS, "apply script")
    new["roadmap"] = apply(texts["roadmap"], ROADMAP_SUBS, "roadmap")

    print(f"ledger: {len(LEDGER_SUBS)} substitutions + the round-1 record, {len(ledger)} -> {len(new['ledger'])} chars")
    print(f"handoff: {len(HANDOFF_SUBS)}; parent: {len(PARENT_SUBS)}; index: {len(INDEX_SUBS)}; phase12: {len(PHASE12_SUBS)}; "
          f"apply script: {len(APPLY_SCRIPT_SUBS)}; roadmap: {len(ROADMAP_SUBS)}")
    if args.check:
        print("--check: nothing written")
        return 0
    for k, p in paths.items():
        p.write_text(new[k], encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
