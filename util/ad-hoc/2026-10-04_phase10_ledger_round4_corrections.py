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
"""Round 4's correction pass on the ledger's Phase 10, as exact-match edits, its Consensus record included.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` as frozen for round 4
(``b5cb675d``). Each SUB anchor must occur exactly once, and each SPAN start must be unique. Round 4's reports
are archived in ``reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round4.md``
(the Phase 10 family keeps its ``2026-10-04_`` prefix; round 4 ran on 2026-10-05). Every finding applied here
was re-derived by the orchestrator first, or is attributed to its lane.

Replaying it on ``b5cb675d``'s ledger reproduces round 5's freeze with no hand-written hunk.

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_ledger_round4_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

ROUND4_RECORD = """- **Round 4**: two lanes on the frozen `b5cb675d`, run 2026-10-05 from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane10R4_phase10_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round4.md`.
  - Lane 10-R4A re-derived every claim round 3's pass introduced. It replayed that pass on `0d3c337b` and got
    `b5cb675d` byte for byte, with no hand-written hunk, and reproduced the counts and the pixel unmixing.
  - Lane 10-R4B was adversarial on that pass.
- **Verdicts.** Lane 10-R4A returned SOUND, with no finding. Lane 10-R4B returned SOUND-WITH-FIXES, and its
  Finding 2 changes an action, so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
  requires round 5.
- **What round 4 changed:**
  - F-CANOPY-067's swap case. Round 3's reading, the orchestrator's, that after W8 step 13 a page's first fetch
    from cascor "replaces its LMU-era store" so the zeros persist "only if that fetch lands before the burst",
    was false in the usual case. A Full History page keeps cascor's history through the LMU steps unless it
    fetched after the fit landed, so its first fetch after the swap is equal and the zeros persist; where it
    did take the fit's point, they last until that fetch, up to about half a minute (Lane 10-R4B; Lane 10-R4A
    found the empty-store half as a condition of its own check);
  - item 18's restart drives. Each now confirms from canopy's log that every page reconnected before the burst,
    and repeats if not, and its Sliding Window page is read knowing that a restart strands the metrics poll for
    up to 30 s (Lane 10-R4B);
  - round 3's record. The hidden Accuracy marker rests on Lane 10-R3A's pixels, while Lane 10-R3B held that the
    capture neither shows nor excludes it, and both round-3 lanes found the mid-run case (Lane 10-R4B).
  - No number or disposition changed. The counts stay 78 findings, 53 fixed, 1 accepted, 2 withdrawn and 22
    open, with 6 open P1 and 16 open P2.
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-04_phase10_ledger_round4_corrections.py`,
    SUB_COUNT substitutions and SPAN_COUNT span rewrites.
- **Re-derived by the orchestrator before applying**, at canopy `1b2dd438`:
  - the recurrence backend's empty history before a fit lands, and the empty-fetch guard;
  - the full-history cadence canopy measured and records in its own constants;
  - the strand mechanism and its 30 s watchdog, whose comment names a canopy restart as a cause;
  - the `Client connected` log line, and that canopy's own `/ws/training` sends no `initial_metrics`.

  Not re-derived: Lane 10-R4B's model of the reconnect odds (about 0.8 within the burst's window at 4 s of
  downtime, 0.6 at 8 s and 0.4 at 12 s). Item 18 now checks the reconnect in the log instead of relying on it.
- **Slips:** none reported.

ROUND5_PENDING"""

SUBS = [
    # --- F-CANOPY-067's Severity: the swap case (Lane 10-R4B, Finding 1) ---
    (
        "    - So once a page's store holds cascor's history, the zeros stay on an idle cascor until a reload, a\n"
        "      theme or view change, or the next run. After W8 step 13, a page's first fetch from cascor replaces\n"
        "      its LMU-era store and redraws the chart, so there they persist only if that fetch lands before the\n"
        "      burst (the orchestrator's reading).",
        "    - So once a page's store holds cascor's history, the zeros stay on an idle cascor until a reload, a\n"
        "      theme or view change, or the next run.\n"
        "    - After W8 step 13 that is the usual case (round 4, Lane 10-R4B; re-derived by the orchestrator). The\n"
        "      recurrence backend answers `[]` until an LMU fit lands (`src/backend/recurrence_backend.py:312-315`),\n"
        "      and an empty fetch never replaces a non-empty store (`dashboard_manager.py:7910-7912`). So a Full\n"
        "      History page keeps cascor's history through the LMU steps unless it fetched after the fit landed,\n"
        "      and it fetches once every ~27-37 s (`canopy_constants.py:476-491`). A page that did take the fit's\n"
        "      single point is redrawn by its first fetch from cascor, usually after the burst, so there the zeros\n"
        "      last until that fetch, up to about half a minute.",
    ),
    # --- the mid-run case was both round-3 lanes' (Lane 10-R4B, Finding 3) ---
    (
        "  - **Not bounded to a few seconds by source, mid-run in the Sliding Window view** (Lane 10-R3A). The",
        "  - **Not bounded to a few seconds by source, mid-run in the Sliding Window view** (Lanes 10-R3A and 10-R3B). The",
    ),
    # --- round 3's record: the hidden marker's attribution (Lane 10-R4B, Finding 3) ---
    (
        "(Lane\n    10-R3A, by unmixing two pixels; Lane 10-R3B, by draw order). The exact-colour counts",
        "(Lane\n    10-R3A, by unmixing two pixels, re-derived by the orchestrator; Lane 10-R3B, by draw order, held that\n"
        "    the capture neither shows nor excludes it; corrected in round 4). The exact-colour counts",
    ),
    # --- item 18: the swap reason, and the restart drives (Lane 10-R4B, Findings 1 and 2) ---
    (
        "This one is the\n      orchestrator's addition: after a swap, a page's first fetch from cascor can redraw its chart after the\n      burst;",
        "This one is the\n      orchestrator's addition: after a swap, a page that took the LMU fit's point is redrawn by its first\n"
        "      fetch from cascor, usually after the burst;",
    ),
    (
        "    - the same restart mid-run, the only one of the three that reaches the mid-run case.\n",
        "    - the same restart mid-run, the only one of the three that reaches the mid-run case.\n"
        "\n"
        "    On each restart drive, confirm from canopy's log that every page's `/ws/training` connect (`Client\n"
        "    connected`, `src/communication/websocket_manager.py:399`) comes before the burst, which lands about 5 s\n"
        "    after `Cascor metrics stream connected`, and repeat the restart if it does not: pages reconnect on a\n"
        "    jittered backoff (`src/frontend/assets/websocket_client.js:162-171`), and nothing re-sends the burst. A\n"
        "    restart also strands each page's metrics poll for up to 30 s (`dashboard_manager.py:2497-2555`,\n"
        "    `canopy_constants.py:425`), so on these drives the Sliding Window page can hold the burst's rows that\n"
        "    long for a reason of its own (round 4, Lane 10-R4B; re-derived by the orchestrator).\n",
    ),
    # --- Instruments, and round 4's record ---
    (
        "Rounds 2 and 3 added `phase10_ledger_round2_corrections.py` and\n  `phase10_ledger_round3_corrections.py`.",
        "Rounds 2 to 4 added `phase10_ledger_round{2,3,4}_corrections.py`.",
    ),
    ("ROUND4_PENDING", "ROUND4_RECORD"),
]

SPANS = [
    # Round 3's record: the mid-run case was both lanes' (Lane 10-R4B, Finding 3).
    (
        "  - F-CANOPY-067's rating basis (both lanes' MAJOR). By source the zeros are not transient in two cases: on a",
        "    which the ledger's own rule makes P1 if the zeros persist;",
        "  - F-CANOPY-067's rating basis (both lanes' MAJOR). By source the zeros are not transient in two cases: on a\n"
        "    page in the Full History or Between Hidden Units view, where the ungated `extendTraces` path paints them and\n"
        "    nothing redraws while cascor is idle (Lane 10-R3B), and mid-run in the Sliding Window view, where the store\n"
        "    keeps the burst's rows while the stream is live (both lanes; this record credited Lane 10-R3A alone until\n"
        "    round 4). The rating stays P2 until the live drive, which the ledger's own rule makes P1 if the zeros\n"
        "    persist;",
    ),
]


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
    record = ROUND4_RECORD.replace("SUB_COUNT", str(len(SUBS))).replace("SPAN_COUNT", str(len(SPANS)))
    if text.count("ROUND4_RECORD") != 1:
        raise SystemExit("round-4 record placeholder not found exactly once")
    return text.replace("ROUND4_RECORD", record)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    if "ROUND4_PENDING" not in before:
        raise SystemExit("ROUND4_PENDING is absent: is this the round-4 freeze (b5cb675d)?")
    after = apply(before)
    if "ROUND5_PENDING" not in after or "ROUND4_PENDING" in after:
        raise SystemExit("placeholders not as expected after the pass")
    print(f"{len(SUBS)} substitutions, {len(SPANS)} spans; {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
