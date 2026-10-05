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
"""Round 3's correction pass on the ledger's Phase 10 (and F-CANOPY-057's tense), as exact-match edits.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` as frozen for round 3
(``0d3c337b``; the two handoff commits after it touch no ledger line). Each SUB anchor must occur exactly once,
and each SPAN start must be unique. The lanes' reports are archived in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round3.md``; every finding applied
here was re-derived by the orchestrator first, or is attributed to its lane.

Unlike rounds 1 and 2, this pass also writes the round's Consensus record and the Instruments sentence, so
replaying it on ``0d3c337b``'s ledger reproduces round 4's freeze with no hand-written hunk.

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_ledger_round3_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

ROUND3_RECORD = """- **Round 3**: two lanes on the frozen `0d3c337b`, from one brief,
  `reports/e2e-canopy-2026-09-02/drafts/lane10R3_phase10_ledger_brief.md`, and the reports, verbatim, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round3.md`.
  - Lane 10-R3A re-derived every claim round 2's pass introduced, artifact-first. It replayed that pass on
    `2134ca2a` and got `0d3c337b` exactly, outside the two hand-written parts, and reproduced the counts.
  - Lane 10-R3B was adversarial on that pass.
- **Verdicts.** Both returned SOUND-WITH-FIXES, each with a MAJOR finding that changes an action, so §4 of
  `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` requires round 4.
- **What round 3 changed:**
  - F-CANOPY-067's rating basis (both lanes' MAJOR). By source the zeros are not transient in two cases: on a
    page in the Full History or Between Hidden Units view, where the ungated `extendTraces` path paints them and
    nothing redraws while cascor is idle (Lane 10-R3B), and mid-run in the Sliding Window view, where the store
    keeps the burst's rows while the stream is live (Lane 10-R3A). The rating stays P2 until the live drive,
    which the ledger's own rule makes P1 if the zeros persist;
  - item 18's deciding drive. It runs on unfixed `main`, before the fix (Lane 10-R3B), with the recurrence leg
    up, without which W8 step 13 is a no-op (Lane 10-R3B), with a page held in Full History (Lane 10-R3B), and
    with a mid-run burst (Lane 10-R3A). F-CANOPY-064's and F-CANOPY-067's fix directions now point at it;
  - F-CANOPY-064's reading of Phase 1's capture. The cluster covers a mostly hidden Accuracy marker (Lane
    10-R3A, by unmixing two pixels; Lane 10-R3B, by draw order). The exact-colour counts, 0, 7 and 7, are Lane
    10-R2B's, and the 11 and 8 were the orchestrator's (both lanes). W1-09 stays FAIL;
  - F-CANOPY-057's Severity bullet, no longer in the present tense (both lanes), and Phase 9's items 15 (Lane
    10-R3B) and 7 (the orchestrator), which still called it P1;
  - F-CANOPY-065's condition, carried into the heading, the Summary, the provenance table and item 20 (Lane
    10-R3B);
  - round 2's record. Its "could not have failed" was Lane 10-R2B's alone, and Lane 10-R2A's contrary reading is
    now recorded (both lanes).
  - No number or disposition changed. The counts stay 78 findings, 53 fixed, 1 accepted, 2 withdrawn and 22
    open, with 6 open P1 and 16 open P2.
  - The pass is replayable, this record included: `util/ad-hoc/2026-10-04_phase10_ledger_round3_corrections.py`,
    SUB_COUNT substitutions and SPAN_COUNT span rewrites.
- **Re-derived by the orchestrator before applying**, in source at canopy `1b2dd438` or in the archive:
  - `extendTraces`' one Input, its missing view check, its 0 for a missing accuracy and its trace-0 target;
  - the store's two writers, the WS append's opt-out in the history views and its 500-row window, the REST
    poll's skip while the stream is live and its `no_update` for an equal fetch, and the history route's live,
    uncached read of cascor (round 2 left the REST takeover as Lane 10-R2B's reading);
  - the figure callback's Inputs;
  - the swap's no-op branch when `recurrence_service_url` is unset, at `src/main.py:4087-4090` (Lane 10-R3B
    cited `:4086-4089`), and its refusal while training;
  - the clicking page's tab-bar rebuild, with a fresh metrics panel in its default view;
  - the two pixels' colours in Phase 1's capture, on the light plot background, and their unmixing to about
    70% Accuracy green.

  Not re-derived: the y-axis reading that puts those pixels at about 98.6% (Lane 10-R3A). The orchestrator's
  own reading from source, that after a swap the page's first fetch from cascor can redraw the chart after the
  burst, is new in this pass, and item 18's idle restart was added for it.
- **Slips:** none reported.

ROUND4_PENDING"""

SUBS = [
    # --- F-CANOPY-065's condition, carried into every place that states its rating (Lane 10-R3B) ---
    (
        "## Phase 10 — 2026-10-04: the peer arcs' hand-overs filed — F-CANOPY-060 to -067, two of them P1; two declined; a Phase 1 PASS corrected",
        "## Phase 10 — 2026-10-04: the peer arcs' hand-overs filed — F-CANOPY-060 to -067, two of them P1, one conditionally; two declined; a Phase 1 PASS corrected",
    ),
    ("  - **F-CANOPY-065 (P1, OPEN):** `/api/set_params`'s", "  - **F-CANOPY-065 (P1, conditionally; OPEN):** `/api/set_params`'s"),
    (
        "| O3 | the same | the same | filed as F-CANOPY-065, P1 (re-rated in round 1), OPEN |",
        "| O3 | the same | the same | filed as F-CANOPY-065, P1 if the owner's question goes that way (re-rated in round 1), OPEN |",
    ),
    ("20. **F-CANOPY-065 (P1).**", "20. **F-CANOPY-065 (P1, conditionally).**"),
    # --- F-CANOPY-067 in the Summary (both lanes' MAJOR) ---
    (
        "  - F-CANOPY-067 (P2, OPEN): the relay forwards cascor's `initial_metrics` burst unnormalized, so those rows\n"
        "    paint loss and accuracy as 0. Found by round 1 of this phase's validation, not handed over.",
        "  - F-CANOPY-067 (P2 pending a live drive, OPEN): the relay forwards cascor's `initial_metrics` burst\n"
        "    unnormalized, so those rows paint loss and accuracy as 0. By source the zeros can persist, which would\n"
        "    make it P1 (Still owed, item 18). Found by round 1 of this phase's validation, not handed over.",
    ),
    # --- F-CANOPY-057, no longer P1 in the present tense (Lanes 10-R3A and 10-R3B) ---
    (
        "- **Severity: P1**, re-rated in round 2 of the ledger's validation (Lanes R2-F and R2-B). canopy `main` still\n"
        "  promises the stream (`docs/USER_MANUAL.md:764`",
        "- **Severity: P1 until canopy#684** (status above), re-rated in round 2 of the ledger's validation (Lanes R2-F\n"
        "  and R2-B). canopy `main` then promised the stream (`docs/USER_MANUAL.md:764`",
    ),
    ("     - F-CANOPY-057 stays open.", "     - F-CANOPY-057 stays open, and is P2 since canopy#684 (its status)."),
    (
        "- **Item 7** is now F-CANOPY-057 alone. F-CANOPY-056 and F-CANOPY-059 are FIXED and verified live.",
        "- **Item 7** is now F-CANOPY-057 alone, P2 since round 2. F-CANOPY-056 and F-CANOPY-059 are FIXED and verified\n  live.",
    ),
    (
        "- **Item 13**'s canopy follow-up merged as canopy#684 (`f2147403`, 2026-09-24), and F-CANOPY-057's re-rating\n"
        "  that it owed is applied (that entry's status).",
        "- **Item 13**'s canopy follow-up merged as canopy#684 (`f2147403`, 2026-09-24), and F-CANOPY-057's re-rating\n"
        "  that it owed is applied (that entry's status).\n"
        "- **Item 15**'s ratings question is narrower now: F-CANOPY-059 (P0) and F-CANOPY-056 (P1) are FIXED, and\n"
        "  F-CANOPY-057 is P2 (carried here in round 3, Lane 10-R3B).",
    ),
    # --- F-CANOPY-064 (Lanes 10-R3A and 10-R3B) ---
    (
        "(one Accuracy point after the run in the A-N2 capture, and in Phase 1's only scalar-series markers, beside Accuracy tiles of 96.30% and 98.75%)",
        "(one Accuracy point after the run in the A-N2 capture and one mostly hidden in Phase 1's, beside Accuracy tiles of 96.30% and 98.75%)",
    ),
    (
        "Its own capture refutes the accuracy half, so W1-09 is\n    FAIL on F-CANOPY-064 (Matrix effect, below).",
        "Its own capture refutes the accuracy half, since one\n    point, mostly hidden, does not accumulate, so W1-09 is FAIL on F-CANOPY-064 (Matrix effect, below).",
    ),
    (
        "  Then drive it live: mid-pass for the tile, after a run for the chart, and W8 step 13 after a CasCor run with a\n"
        "  page open, which is F-CANOPY-067's trigger (a cascor restart's burst is empty).",
        "  Then drive it live: mid-pass for the tile and after a run for the chart. F-CANOPY-067's rating drive comes\n"
        "  first, on unfixed `main` (Still owed, item 18).",
    ),
    # --- F-CANOPY-067 (both lanes' MAJOR) ---
    (
        "up to 100 flat rows can enter the metrics store, where the panel reads their loss and accuracy as 0 (P2 while the zeros are transient, canopy repo;",
        "up to 100 flat rows can enter the metrics store, where the panel reads their loss and accuracy as 0, or reach the charts through `extendTraces`, which plots a missing accuracy as 0 (P2 pending a live drive, though by source the zeros can persist, which would make it P1; canopy repo;",
    ),
    (
        "  (F-CANOPY-064), or drop the burst. Drive W8 step 13 after a CasCor run, with a page open, in item 18's live\n"
        "  drive; a cascor restart will not do, because its burst is empty.",
        "  (F-CANOPY-064), or drop the burst. Decide the rating first, on unfixed `main`, with Still owed item 18's\n"
        "  drives, and repeat them after the fix.",
    ),
    # --- Consensus record: round 2's text, corrected ---
    (
        "  - F-CANOPY-067's triggers. A switch back to CasCor (W8 step 13) fires it every time, while a cascor\n"
        "    restart's burst is empty, so the planned live check could not have failed (both lanes). Its rating basis\n"
        "    is now the zeros' transience (Lane 10-R2B);",
        "  - F-CANOPY-067's triggers. A switch back to CasCor (W8 step 13) fires it (both lanes; round 3 added: only\n"
        "    when the swap is real). A cascor restart's burst is empty, so a check induced that way could not have\n"
        "    failed (Lane 10-R2B; Lane 10-R2A judged item 18 as written still exercised the path; this record said\n"
        "    \"both lanes\" until round 3). Its rating basis became the zeros' transience (Lane 10-R2B), which round 3\n"
        "    found false in part;",
    ),
    (
        "  - F-CANOPY-064's accuracy count and header. Phase 1's marker cluster is the Recall and ROC-AUC series, not\n"
        "    Accuracy; retained runs add points, and the scalar series are not phase-filtered (Lane 10-R2B);",
        "  - F-CANOPY-064's accuracy count and header. Phase 1's marker cluster shows only the Recall and ROC-AUC\n"
        "    colours (round 3 found a mostly hidden Accuracy marker beneath them); retained runs add points, and the\n"
        "    scalar series are not phase-filtered (Lane 10-R2B);",
    ),
    (
        "  - Phase 1's capture, by a pixel count of the series' colours in the cluster: 0 Accuracy, 11 Recall and 8\n"
        "    ROC-AUC.",
        "  - Phase 1's capture, by a pixel count of the series' colours in the cluster, within a colour tolerance: 0\n"
        "    Accuracy, 11 Recall and 8 ROC-AUC (exact matches give 0, 7 and 7; round 3).",
    ),
    # --- Instruments, and round 3's record ---
    (
        "tmpfs, `phase10_r1_{a2,b1,b2}_*`. Round 2 added `phase10_ledger_round2_corrections.py`.",
        "tmpfs, `phase10_r1_{a2,b1,b2}_*`. Rounds 2 and 3 added `phase10_ledger_round2_corrections.py` and\n"
        "  `phase10_ledger_round3_corrections.py`.",
    ),
    ("ROUND3_PENDING", "ROUND3_RECORD"),
]

SPANS = [
    # F-CANOPY-067's W8 trigger: the recurrence leg, and the clicking page's re-mount (Lane 10-R3B).
    (
        "    starts a fresh relay (`src/backend/service_backend.py:460`). cascor still holds its monitor rows, since a",
        "    plain Start retains them;",
        "    starts a fresh relay (`src/backend/service_backend.py:460`). cascor still holds its monitor rows, since a\n"
        "    plain Start retains them. The swap is real only with the recurrence leg up: with `recurrence_service_url`\n"
        "    unset, its default (`src/settings.py:262`), no selection targets the recurrence backend\n"
        "    (`src/main.py:3980`), both selects take the no-op branch (`:4087-4090`), and no relay starts (round 3,\n"
        "    Lane 10-R3B). The clicking page's tab bar is then rebuilt with a fresh metrics panel\n"
        "    (`src/frontend/dashboard_manager.py:2747-2754`), whose view starts in Sliding Window\n"
        "    (`metrics_panel.py:642`), so the persistent case below can show only on the other open pages (Lane\n"
        "    10-R3B; re-derived by the orchestrator);",
    ),
    # F-CANOPY-067's Severity (both lanes' MAJOR).
    (
        "- **Severity: P2, because the zeros are transient by source** (round 2, Lane 10-R2B).",
        "(Still owed, item 18).",
        "- **Severity: P2 pending a live drive** (round 3). Round 2 rested P2 on the zeros being transient; round 3\n"
        "  found that basis false in part (Lanes 10-R3A and 10-R3B; re-derived by the orchestrator in source at canopy\n"
        "  `1b2dd438`).\n"
        "  - **Transient by source:** the tiles, which read the newest row (`metrics_panel.py:1671-1672`), and the\n"
        "    charts on an idle page in the Sliding Window view. The burst stamps the liveness clock\n"
        "    (`ws_dash_bridge.js:273`), and after 5 s of quiet the REST poll replaces the store\n"
        "    (`dashboard_manager.py:7877`, `:7941`).\n"
        "  - **Persistent by source in the Full History and Between Hidden Units views** (Lane 10-R3B). The\n"
        "    clientside `extendTraces` callback's only Input is `ws-metrics-buffer`, and it has no view check\n"
        "    (`metrics_panel.py:1015-1142`). It plots a missing accuracy as 0 (`:1037`) straight onto the Accuracy\n"
        "    trace (`:1095`).\n"
        "    - The store has two writers: the WS append, which opts out in these views\n"
        "      (`dashboard_manager.py:7827-7828`), and the REST poll, which answers `no_update` to a fetch equal to\n"
        "      the store (`:7941`). The history route reads cascor live, through no cache\n"
        "      (`src/backend/service_backend.py:335-336`).\n"
        "    - The figure callback's Inputs are the store, the theme and the view (`metrics_panel.py:970-972`).\n"
        "    - So once a page's store holds cascor's history, the zeros stay on an idle cascor until a reload, a\n"
        "      theme or view change, or the next run. After W8 step 13, a page's first fetch from cascor replaces\n"
        "      its LMU-era store and redraws the chart, so there they persist only if that fetch lands before the\n"
        "      burst (the orchestrator's reading).\n"
        "  - **Not bounded to a few seconds by source, mid-run in the Sliding Window view** (Lane 10-R3A). The\n"
        "    stream stays live, so the poll is skipped (`:7877`), and the WS append keeps the burst's rows\n"
        "    (`:7832-7834`) until a 5 s gap in `metrics` frames or 500 newer rows (the view's default window,\n"
        "    `metrics_panel.py:642`, `canopy_constants.py:511`). How long that is in a run was not measured. W8 step\n"
        "    13 cannot reach this case, because canopy refuses a model switch while training\n"
        "    (`src/main.py:4092-4097`).\n"
        "  - So this ledger's own rule, P1 if the zeros persist beyond a few seconds, predicts P1 by source. The\n"
        "    drives in Still owed item 18 decide it, on unfixed `main`.",
    ),
    # F-CANOPY-064, Phase 1's capture (Lanes 10-R3A and 10-R3B).
    (
        "  `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png`, shows the same chart: the 0–10k axis and, at",
        "  reproduced by the orchestrator). It sits beside Accuracy 98.75% and Training Step 11.",
        "  `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png`, shows the same chart: the 0–10k axis and, at\n"
        "  x ≈ 11 under \"+Unit #10\", a marker cluster beside Accuracy 98.75% and Training Step 11, in which the Recall\n"
        "  and ROC-AUC markers cover a mostly hidden Accuracy marker.\n"
        "  - Accuracy is trace 0, drawn beneath the scalar series (`metrics_panel.py:2271-2290`; round 3, Lane\n"
        "    10-R3B).\n"
        "  - No pixel in the cluster matches Accuracy's colour exactly, against 7 of Recall's and 7 of ROC-AUC's\n"
        "    (Lane 10-R2B; 11 and 8 within a colour tolerance, the orchestrator's count).\n"
        "  - Two pixels where the ROC-AUC and Recall markers meet, `#5d9c64` and `#598c5b`, unmix to about 70%\n"
        "    Accuracy green (round 3, Lane 10-R3A; the unmixing re-derived by the orchestrator). On that lane's\n"
        "    reading of the axis they sit at about 98.6%, against the tile's 98.75%.",
    ),
    # Item 18: the rating drive first, on unfixed main, built to be able to show persistence (both lanes).
    (
        "18. **F-CANOPY-064 (P1) and F-CANOPY-067.**",
        "    labelled `output`.",
        "18. **F-CANOPY-064 (P1) and F-CANOPY-067.** First, on unfixed `main`, decide F-CANOPY-067's rating, holding\n"
        "    one page in Sliding Window and a second in Full History through each drive (round 3, Lanes 10-R3A and\n"
        "    10-R3B):\n"
        "    - W8 step 13 after a CasCor run, with the recurrence leg up (`--with-recurrence`), without which both\n"
        "      selects are no-ops and no burst is sent;\n"
        "    - a canopy restart on an idle cascor, the pages reconnecting within the burst's 5 s. This one is the\n"
        "      orchestrator's addition: after a swap, a page's first fetch from cascor can redraw its chart after the\n"
        "      burst;\n"
        "    - the same restart mid-run, the only one of the three that reaches the mid-run case.\n"
        "\n"
        "    A cascor restart will not do, because its burst is empty. Then carry `kind`, fix the axis, key accuracy\n"
        "    on `kind`, correct N6's fixture, normalize or drop the `initial_metrics` burst, and align `extendTraces`\n"
        "    with the relay's rows. Then drive it live: mid-pass, after a run, and the same three drives as\n"
        "    verification. Confirm from an unslimmed history that only a run's last step row is labelled `output`.",
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
    record = ROUND3_RECORD.replace("SUB_COUNT", str(len(SUBS))).replace("SPAN_COUNT", str(len(SPANS)))
    if text.count("ROUND3_RECORD") != 1:
        raise SystemExit("round-3 record placeholder not found exactly once")
    return text.replace("ROUND3_RECORD", record)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    if "ROUND3_PENDING" not in before:
        raise SystemExit("ROUND3_PENDING is absent: is this the round-3 freeze (0d3c337b)?")
    after = apply(before)
    if "ROUND4_PENDING" not in after or "ROUND3_PENDING" in after:
        raise SystemExit("placeholders not as expected after the pass")
    print(f"{len(SUBS)} substitutions, {len(SPANS)} spans; {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
