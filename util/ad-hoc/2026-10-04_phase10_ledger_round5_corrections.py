#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 5's wording pass on the ledger's Phase 10, its Consensus record included; the review ends here.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` as frozen for round 5
(``b2375a51``). No finding of round 5 changed a number, disposition or action, so under §4 of
``JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`` the review ends, and this pass
is not itself reviewed. Round 5's reports are archived in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round5.md``.

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_ledger_round5_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

ROUND5_RECORD = """- **Round 5**: two lanes on the frozen `b2375a51`, run 2026-10-05 from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane10R5_phase10_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round5.md`.
  - Lane 10-R5A re-derived every claim round 4's pass introduced. It replayed that pass on `b5cb675d` and got
    `b2375a51` byte for byte, with no hand-written hunk, and reproduced the counts.
  - Lane 10-R5B was adversarial on that pass, and replayed it too.
- **Verdicts.** Lane 10-R5A returned SOUND and Lane 10-R5B SOUND-WITH-FIXES. No finding of either changes a
  number, disposition or action, so under §4 **the review ends at round 5**, and this round's wording pass was
  not itself reviewed. Lane 10-R5B also offered an optional action change: start W8 a full-fetch cycle after
  the run ends. It is not taken, because the drive decides the rating without it: in every branch the zeros
  last at least until the first fetch from cascor, up to about half a minute.
- **What round 5 changed, all wording:**
  - the swap case's "the usual case", narrowed to the branch it holds in, with the branch where the page's
    store missed the run's last rows added (Lane 10-R5B);
  - the restart strand, "about 30 s" rather than "up to 30 s", because the watchdog counts its 30 s from a 5 s
    slow tick (Lane 10-R5A);
  - the log line to look for, `Client connected: training-client-…`, because `/ws/control` logs the same
    words (Lane 10-R5B);
  - round 4's record: canopy derives the ~27-37 s full-history cadence from its measured tick; it did not
    measure it (both lanes).
  - The counts stay 78 findings, 53 fixed, 1 accepted, 2 withdrawn and 22 open, with 6 open P1 and 16 open P2.
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-04_phase10_ledger_round5_corrections.py`,
    SUB_COUNT substitutions and SPAN_COUNT span rewrites.
- **Re-derived by the orchestrator before applying**, at canopy `1b2dd438`: the watchdog's clock, which starts
  at the first slow tick that sees the poll disabled and fires at a later tick 30 s on
  (`dashboard_manager.py:2536-2545`); the Full History poll's fetch on every 5th tick, during a run as well
  (`:7877`, `:7883`); and the two socket labels, `training-client-` and `control-client-` (`src/main.py:850`,
  `:985`).
- **Slips:** none reported."""

SUBS = [
    # --- F-CANOPY-067's swap case: "the usual case" narrowed (Lane 10-R5B, Finding 1) ---
    (
        "    - After W8 step 13 that is the usual case (round 4, Lane 10-R4B; re-derived by the orchestrator). The\n"
        "      recurrence backend answers `[]` until an LMU fit lands (`src/backend/recurrence_backend.py:312-315`),\n"
        "      and an empty fetch never replaces a non-empty store (`dashboard_manager.py:7910-7912`). So a Full\n"
        "      History page keeps cascor's history through the LMU steps unless it fetched after the fit landed,\n"
        "      and it fetches once every ~27-37 s (`canopy_constants.py:476-491`). A page that did take the fit's\n"
        "      single point is redrawn by its first fetch from cascor, usually after the burst, so there the zeros\n"
        "      last until that fetch, up to about half a minute.",
        "    - After W8 step 13 that holds when the page fetched after the run ended and not after the fit landed\n"
        "      (round 4, Lane 10-R4B; narrowed in round 5, Lane 10-R5B; re-derived by the orchestrator). The\n"
        "      recurrence backend answers `[]` until an LMU fit lands (`src/backend/recurrence_backend.py:312-315`),\n"
        "      and an empty fetch never replaces a non-empty store (`dashboard_manager.py:7910-7912`). A Full History\n"
        "      page fetches once every ~27-37 s (`canopy_constants.py:476-491`), during a run as well, so its store\n"
        "      can miss the run's last rows if W8 starts within that cycle. A page that took the fit's single point,\n"
        "      or whose store missed the run's last rows, is redrawn by its first fetch from cascor, usually after\n"
        "      the burst, so there the zeros last until that fetch, up to about half a minute.",
    ),
    # --- item 18: the log line, and the strand's length (Lane 10-R5B, Finding 3; Lane 10-R5A, Finding 1) ---
    (
        "(`Client\n    connected`, `src/communication/websocket_manager.py:399`)",
        "(`Client\n    connected: training-client-…`, `src/communication/websocket_manager.py:399`)",
    ),
    (
        "    restart also strands each page's metrics poll for up to 30 s (`dashboard_manager.py:2497-2555`,\n"
        "    `canopy_constants.py:425`), so on these drives",
        "    restart can also strand a page's metrics poll for about 30 s (the watchdog's 30 s, counted from a 5 s\n"
        "    slow tick; `dashboard_manager.py:2497-2555`, `canopy_constants.py:425`), so on these drives",
    ),
    # --- round 4's record: the swap case's wording, the strand, the cadence (both round-5 lanes) ---
    (
        "    was false in the usual case. A Full History page keeps cascor's history through the LMU steps unless it\n"
        "    fetched after the fit landed, so its first fetch after the swap is equal and the zeros persist; where it\n"
        "    did take the fit's point,",
        "    was false in a likely case (Lane 10-R4B's words; this record said \"the usual case\" until round 5). A Full\n"
        "    History page keeps cascor's history through the LMU steps unless it fetched after the fit landed or\n"
        "    missed the run's last rows (round 5, Lane 10-R5B), so its first fetch after the swap is equal and the\n"
        "    zeros persist; where it did take the fit's point,",
    ),
    (
        "a restart strands the metrics poll for\n    up to 30 s (Lane 10-R4B);",
        "a restart can strand the metrics poll for\n    about 30 s (Lane 10-R4B; \"up to 30 s\" until round 5);",
    ),
    (
        "  - the full-history cadence canopy measured and records in its own constants;",
        "  - the full-history cadence canopy derives in its own constants from its measured tick (\"measured\" until\n"
        "    round 5);",
    ),
    # --- Instruments, and round 5's record ---
    ("Rounds 2 to 4 added `phase10_ledger_round{2,3,4}_corrections.py`.", "Rounds 2 to 5 added `phase10_ledger_round{2,3,4,5}_corrections.py`."),
    ("ROUND5_PENDING", "ROUND5_RECORD"),
]

SPANS: list = []


def apply(text: str) -> str:
    for old, new in SUBS:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"SUB anchor found {n} times: {old[:100]!r}")
        text = text.replace(old, new)
    for start, end, new in SPANS:
        i = text.find(start)
        if i < 0 or text.find(start, i + 1) >= 0:
            raise SystemExit(f"SPAN start not unique: {start[:100]!r}")
        j = text.find(end, i)
        if j < 0:
            raise SystemExit(f"SPAN end not found after start: {end[:100]!r}")
        text = text[:i] + new + text[j + len(end):]
    # The record names the pass's own size, so it is filled in last.
    record = ROUND5_RECORD.replace("SUB_COUNT", str(len(SUBS))).replace("SPAN_COUNT", str(len(SPANS)))
    if text.count("ROUND5_RECORD") != 1:
        raise SystemExit("round-5 record placeholder not found exactly once")
    return text.replace("ROUND5_RECORD", record)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    if "ROUND5_PENDING" not in before:
        raise SystemExit("ROUND5_PENDING is absent: is this the round-5 freeze (b2375a51)?")
    after = apply(before)
    if "_PENDING" in after.split("## Phase 10 —", 1)[1]:
        raise SystemExit("a placeholder remains in Phase 10 after the pass")
    print(f"{len(SUBS)} substitutions, {len(SPANS)} spans; {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
