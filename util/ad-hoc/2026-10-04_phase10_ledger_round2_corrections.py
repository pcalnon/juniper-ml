#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Round 2's correction pass on the ledger's Phase 10 (and F-CANOPY-057's owed re-rating), as exact-match edits.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` at the round-2 freeze
(``2134ca2a``). Each anchor must occur exactly once. The lanes' reports are archived in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round2.md``; every finding applied
here was re-derived by the orchestrator first.

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_ledger_round2_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

SUBS = [
    # --- F-CANOPY-057 (Phase 9): the re-rating its own entry said was owed with canopy#684 ---
    (
        "no replay weight reaches the page (P1 while canopy's manual and FAQ promise the stream, re-rated 2026-09-24; canopy + cascor; found 2026-09-23 by the cuts' round-1 adversarial lane; OPEN).**\n",
        "no replay weight reaches the page (P2 since canopy#684, merged 2026-09-24 as `f2147403`, corrected the manual and FAQ that promised the stream, re-rated 2026-10-04; P1 before that, from 2026-09-24; canopy + cascor; found 2026-09-23 by the cuts' round-1 adversarial lane; OPEN).**\n"
        "\n"
        "- **Status 2026-10-04: re-rated P2** (round 2 of Phase 10's validation, Lanes 10-R2A and 10-R2B; re-derived by\n"
        "  the orchestrator). canopy#684, from branch `fix/idle-cuts-round3-wording`, merged at 2026-09-24T11:10:28Z as\n"
        "  `f2147403`, an ancestor of canopy `1b2dd438`, and it changed both files the P1 rested on.\n"
        "  `docs/USER_MANUAL.md:764-766` now says \"Today no weight sample reaches the page\", and\n"
        "  `notes/development/REPLAY_V2_FAQ.md` opens with a status note that no replay weight reaches the page. That is\n"
        "  the re-rating the Severity bullet below said was owed with the merge. The defect itself stands.\n",
    ),
    # --- Summary ---
    (
        "- **Two declined:** the selection arc's O4 (an environment artifact) and O9 (a design question, the owner's).",
        "- **Two declined:** the selection arc's O4 (an environment artifact) and O9 (a design question, the owner's).\n"
        "- **F-CANOPY-057 re-rated P2.** canopy#684 corrected the manual and FAQ that its P1 rested on, the re-rating\n"
        "  its entry said was owed with that merge (found in round 2).",
    ),
    (
        "  P0, **7 open P1** and 15 open P2.",
        "  P0, **6 open P1** and 16 open P2.",
    ),
    # --- F-CANOPY-060 ---
    (
        "    seed's 5 symbols (`src/model_registry.py:267-277`), so from the page the refusal needs a custom list of\n"
        "    more than 14 symbols, `max_symbols` set below the list's length, or a deployment ceiling below the list's\n"
        "    length (round 1, Lanes 10-B1 and 10-B2).",
        "    seed's 5 symbols (`src/model_registry.py:267-277`). The form renders no array field, so `symbols` travels\n"
        "    only as that seed (`:234-238`), and from the page the refusal needs `max_symbols`, or a deployment\n"
        "    ceiling, below 5. The 503-symbol case needs the API or a YAML (round 1, Lane 10-B1; round 2, Lane\n"
        "    10-R2B).",
    ),
    (
        "  `29be6d35`). So both import at most the first 14 symbols, and the choice then decides, as for a shortfall,",
        "  `29be6d35`). So both import at most the first N symbols, N being the effective cap (14 at juniper-data's\n"
        "  default), and the choice then decides, as for a shortfall,",
    ),
    (
        "    says what accepting imports: the first 14 symbols.",
        "    says what accepting imports: the first N symbols.",
    ),
    # --- F-CANOPY-063 ---
    ("real one nests the partition). A claim-text grep finds only the first two kinds.", "real one nests the partition). A claim-text grep finds only the first."),
    # --- F-CANOPY-064 ---
    (
        "(one point after the run, in both archived captures, beside Accuracy tiles of 98.75% and 96.30%)",
        "(one Accuracy point after the run in the A-N2 capture, and in Phase 1's only scalar-series markers, beside Accuracy tiles of 96.30% and 98.75%)",
    ),
    (
        "  Then drive it live: mid-pass for the tile, after a run for the chart, and across a relay reconnect.",
        "  Then drive it live: mid-pass for the tile, after a run for the chart, and W8 step 13 after a CasCor run with a\n"
        "  page open, which is F-CANOPY-067's trigger (a cascor restart's burst is empty).",
    ),
    # --- F-CANOPY-065 ---
    ("(P1, canopy repo; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O3; re-rated P1 in round 1 of this phase's validation; OPEN).**", "(P1 if a shipped CHANGELOG promise counts as documented, else P2, the owner's question; canopy repo; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O3; re-rated P1 in round 1 of this phase's validation; OPEN).**"),
    ("(`src/tests/integration/test_n5_apply_params_ux.py:308`)", "(`src/tests/integration/test_n5_apply_params_ux.py:309`)"),
    (
        "    with the same result, and unwrapping the ack in `_apply_params_hot` alone recovered all four WS keys and\n"
        "    the skip.",
        "    with the same result, and unwrapping the ack in `_apply_params_hot` alone recovered the three WS keys the\n"
        "    network took, the fourth's not-updatable skip, and the REST key.",
    ),
    (
        "  example never appears. This ledger already treats a promise outside the manual as documented: F-CANOPY-057\n"
        "  is P1 on the manual and a FAQ. The values themselves land.",
        "  example never appears. No manual or REFERENCE text makes this promise, so the P1 holds only if a shipped\n"
        "  CHANGELOG or design-plan promise counts as documented under plan §6.3, the owner's question (Consensus\n"
        "  record); if not, F-CANOPY-065 is P2. Round 1 also cited F-CANOPY-057 as a precedent. Round 2 withdrew that:\n"
        "  F-CANOPY-057's P1 rested on the manual, and has lapsed (its status). The values themselves land.",
    ),
    # --- Consensus record, round 1's own text ---
    (
        "  showed all three instruments adequate.",
        "  showed `f060` and `o2` adequate. `o3` copies `apply_params`' merge, so it cannot verify F-CANOPY-065's fix\n"
        "  until it drives the real one (Lane 10-A2's Finding 3; Still owed, item 20; corrected in round 2).",
    ),
    (
        "  - F-CANOPY-064's mechanism. Accuracy keyed on `phase` is now the main cause; the \"sliver\" sentence is\n"
        "    withdrawn; the A-N2 run's budgets are cascor's defaults, not canopy's (Lanes 10-A2 and 10-B2); and its\n"
        "    \"every path\" claim is corrected (Lanes 10-A1, 10-A2 and 10-B2);",
        "  - F-CANOPY-064's mechanism. Accuracy keyed on `phase` is now the main cause (Lanes 10-B1 and 10-B2); the\n"
        "    \"sliver\" sentence is withdrawn (Lane 10-B2); the A-N2 run's budgets are cascor's defaults, not canopy's\n"
        "    (Lane 10-A2); and its \"every path\" claim is corrected (Lanes 10-A1, 10-A2 and 10-B2);",
    ),
    (
        "  §6.3. Lane 10-B1 read it so, as this ledger did for F-CANOPY-057. If it does not, F-CANOPY-065 and\n"
        "  F-CANOPY-057 both return to P2.",
        "  §6.3. Lane 10-B1 read it so. If it does not, F-CANOPY-065 returns to P2. Round 1 also named F-CANOPY-057\n"
        "  here; round 2 removed it, because its P1 rested on the manual and has lapsed.",
    ),
    # --- Matrix effect and counts ---
    (
        "  FAIL on F-CANOPY-064 (its entry has the evidence). The run's `statuses.tsv` is left as recorded.",
        "  FAIL on F-CANOPY-064 (its entry has the evidence). The run's `statuses.tsv` is left as recorded.\n"
        "- M-METRICS-32's PASS (re-validated at `04f06ff`) covers its append callback only. Its row also claims a\n"
        "  clientside `extendTraces` path, which was never driven and fails by source (F-CANOPY-064; Still owed, item\n"
        "  18; round 2, Lane 10-R2B).",
    ),
    (
        "  - **7 open P1:** F-CANOPY-055, F-CANOPY-057, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CASCOR-001 and\n"
        "    F-CASCOR-002.",
        "  - **6 open P1:** F-CANOPY-055, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CASCOR-001 and F-CASCOR-002.",
    ),
    (
        "  - 15 open P2.",
        "  - 16 open P2. F-CANOPY-057 returned to P2 in round 2 (its status).",
    ),
    # --- Still owed ---
    (
        "- **Item 16** is DONE (2026-10-04), except its fixture sweep, which moves to item 19.",
        "- **Item 16** is DONE (2026-10-04), except its fixture sweep, which moves to item 19.\n"
        "- **Item 13**'s canopy follow-up merged as canopy#684 (`f2147403`, 2026-09-24), and F-CANOPY-057's re-rating\n"
        "  that it owed is applied (that entry's status).",
    ),
    (
        "    Then drive it live: mid-pass, after a run, and across a relay reconnect with a page open, which also\n"
        "    settles F-CANOPY-067's rating.",
        "    Then drive it live: mid-pass, after a run, and W8 step 13 after a CasCor run with a page open (not a\n"
        "    cascor restart, whose burst is empty), which also settles F-CANOPY-067's rating.",
    ),
    (
        "    the N5 fake, the extractor's \"WS-flat\" docstring and the \"default off\" comment. Test with a mixed Apply.",
        "    the N5 fake, the extractor's \"WS-flat\" docstring and the \"default off\" comment. Test with a mixed Apply\n"
        "    through the real `apply_params`, and make the `o3` instrument drive it too, since it copies the merge.",
    ),
]

SPANS = [
    (
        "  `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png`, shows the same chart",
        "  Step 11.",
        "  `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png`, shows the same chart: the 0–10k axis and, at\n"
        "  x ≈ 11 under \"+Unit #10\", a marker cluster that is the Recall and ROC-AUC series, not Accuracy. The cluster\n"
        "  holds no pixel of Accuracy's colour against 11 of Recall's and 8 of ROC-AUC's (round 2, Lane 10-R2B,\n"
        "  reproduced by the orchestrator). It sits beside Accuracy 98.75% and Training Step 11.",
    ),
    (
        "  - By the same source only a growth run's last step row, drained at `:2150` after the return to `output`,",
        "both captures show one point.",
        "  - By the same source only a growth run's last step row, drained at `:2150` after the return to `output`,\n"
        "    carries `output` (Lane 10-B2). So, from the store, one growth run's Accuracy trace has no point during\n"
        "    growth and one after it, at any budget. Earlier runs that a plain Start retains each add one point (a\n"
        "    plain Start keeps cascor's history, `manager.py:2931`), and F-CANOPY-067's burst can add zero-valued points.\n"
        "    The chart's F1, Precision, Recall and ROC-AUC series are not phase-filtered (`metrics_panel.py:2032-2072`),\n"
        "    so they gain points during growth (round 2, Lane 10-R2B).",
    ),
    (
        "canopy's metrics relay forwards cascor's `initial_metrics` burst without normalizing it, so after a relay reconnect while a page is open, up to 100 flat rows can enter the metrics store, where the panel reads their loss and accuracy as 0 (P2 until observed live,",
        "(P2 until observed live,",
        "canopy's metrics relay forwards cascor's `initial_metrics` burst without normalizing it, so after the relay (re)connects while a page is open, up to 100 flat rows can enter the metrics store, where the panel reads their loss and accuracy as 0 (P2 while the zeros are transient,",
    ),
    (
        "- **When it fires.** The relay connects at canopy's startup",
        "  measured.",
        "- **When it fires** (round 2, Lanes 10-R2A and 10-R2B; re-derived by the orchestrator). cascor sends the burst\n"
        "  about 5 s after the relay (re)connects, once its resume handshake times out (`training_stream.py:60-79`), and\n"
        "  canopy broadcasts it to every page open then. The relay (re)connects:\n"
        "  - on a switch back to CasCor from the LMU model, W8 step 13, clicked on the open page. `/api/model/select`\n"
        "    runs `_swap_backend`, which awaits the new backend's `initialize()` (`src/main.py:4100-4101`), and that\n"
        "    starts a fresh relay (`src/backend/service_backend.py:460`). cascor still holds its monitor rows, since a\n"
        "    plain Start retains them;\n"
        "  - at canopy's startup. In the A-N2 log the relay connected at 14:27:30.768, 43 ms after \"Application startup\n"
        "    complete\", and cascor's initial-state frames, the burst among them, arrived at 14:27:35.770\n"
        "    (`reports/2026-09-23_canopy-a-n2-generate-stage-train-render/00_stack/logs/juniper-canopy.log:34-37`). A tab\n"
        "    that reconnects across a canopy restart within those 5 s can receive it;\n"
        "  - after a socket loss while cascor stays up.\n"
        "\n"
        "  A cascor restart sends an empty burst, since the new process holds no rows, and F-CANOPY-049 and\n"
        "  F-CASCOR-004 describe drops the relay does not reconnect from. How long the rows stay was not measured.",
    ),
    (
        "- **Severity: P2 until observed live.**",
        "(Still owed, item 18).",
        "- **Severity: P2, because the zeros are transient by source** (round 2, Lane 10-R2B). The burst stamps the\n"
        "  liveness clock (`ws_dash_bridge.js:273`); after 5 s of quiet the REST poll replaces the store\n"
        "  (`dashboard_manager.py:7877`, `:7941`), and during a run the next relayed frame replaces the tiles. A live\n"
        "  drive of W8 step 13 decides it: P1 if the zeros persist beyond a few seconds (Still owed, item 18).",
    ),
    (
        "  (F-CANOPY-064), or drop the burst; include a relay reconnect in item 18's live drive.",
        "  (F-CANOPY-064), or drop the burst; include a relay reconnect in item 18's live drive.",
        "  (F-CANOPY-064), or drop the burst. Drive W8 step 13 after a CasCor run, with a page open, in item 18's live\n"
        "  drive; a cascor restart will not do, because its burst is empty.",
    ),
]

ROUND2 = "ROUND2_PENDING"


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
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    after = apply(before)
    if ROUND2 not in after:
        raise SystemExit("round-2 placeholder missing")
    print(f"{len(SUBS)} substitutions, {len(SPANS)} spans; {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
