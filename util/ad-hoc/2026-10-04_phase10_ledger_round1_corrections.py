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
"""Round 1's correction pass on the ledger's Phase 10, as replayable exact-match edits.

Applied to ``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`` at the round-1 freeze
(``0737d573``). Every edit asserts that its anchor occurs exactly once, so a replay onto a moved file stops
instead of guessing. The lanes' reports are archived in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md``; every finding
applied here was re-derived by the orchestrator first (the Consensus record says how).

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_ledger_round1_corrections.py [--check]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

# (old, new): plain substitutions, each old unique.
SUBS = [
    # --- heading and Summary ---
    (
        "## Phase 10 — 2026-10-04: the peer arcs' hand-overs filed — F-CANOPY-060 to -066, one of them P1; two declined",
        "## Phase 10 — 2026-10-04: the peer arcs' hand-overs filed — F-CANOPY-060 to -067, two of them P1; two declined; a Phase 1 PASS corrected",
    ),
    (
        "  Where a function could be lifted out, it was also executed (Instruments, below).",
        "  For F-CANOPY-060, F-CANOPY-064's tile and F-CANOPY-065's extractor the functions were also executed\n"
        "  (Instruments, below). The rest was read in source, and round 1 of this phase's validation executed more of\n"
        "  it.",
    ),
    ("- **Seven filed:**", "- **Eight filed:**"),
    (
        "  - F-CANOPY-060 (P2, OPEN): the shortfall prompt cuts juniper-data's cap refusal short, and its options\n"
        "    describe a shortfall.",
        "  - F-CANOPY-060 (P2, OPEN): the shortfall prompt cuts juniper-data's cap refusal short, and never mentions\n"
        "    the cap.",
    ),
    (
        "  - **F-CANOPY-064 (P1, OPEN):** the Training Metrics charts plot two numberings on one axis, and canopy's\n"
        "    relay drops the key that tells them apart.",
        "  - **F-CANOPY-064 (P1, OPEN):** the Training Metrics charts keep accuracy only on rows labelled `output` and\n"
        "    plot two numberings on one axis, and canopy's normalizing paths drop the key that tells them apart.\n"
        "    Phase 1's own capture showed it on 2026-08-10, and that run's W1-09 PASS is corrected to FAIL.",
    ),
    (
        "  - F-CANOPY-065 (P2, OPEN): `/api/set_params`'s `applied` list omits every key sent over `/ws/control`.",
        "  - **F-CANOPY-065 (P1, OPEN):** `/api/set_params`'s `applied` list omits every key sent over `/ws/control`,\n"
        "    so the toast canopy 0.6.0 promised never reports a key cascor declines there.",
    ),
    (
        "  - F-CANOPY-066 (P2, OPEN): under the recurrence backend, `/api/network/stats` answers 503 on every slow tick.",
        "  - F-CANOPY-066 (P2, OPEN): under the recurrence backend, `/api/network/stats` answers 503 on every slow tick.\n"
        "  - F-CANOPY-067 (P2, OPEN): the relay forwards cascor's `initial_metrics` burst unnormalized, so those rows\n"
        "    paint loss and accuracy as 0. Found by round 1 of this phase's validation, not handed over.",
    ),
    (
        "- **Counts** (`e2e_finding_triage.py`): 77 findings, 53 fixed, 1 accepted, 2 withdrawn, **21 open**; no open\n"
        "  P0, **6 open P1** and 15 open P2.",
        "- **Counts** (`e2e_finding_triage.py`): 78 findings, 53 fixed, 1 accepted, 2 withdrawn, **22 open**; no open\n"
        "  P0, **7 open P1** and 15 open P2.",
    ),
    (
        "| O3 | the same | the same | filed as F-CANOPY-065, P2, OPEN |",
        "| O3 | the same | the same | filed as F-CANOPY-065, P1 (re-rated in round 1), OPEN |",
    ),
    (
        "The A-N2 run's O1 is F-CANOPY-055. Its O6, O7 and O8 were not handed over.",
        "The A-N2 run's O1 is F-CANOPY-055. Its O6, O7 and O8 were not handed over. F-CANOPY-067 was not handed over\n"
        "either: round 1 of this phase's validation found it (Consensus record, below).",
    ),
    # --- F-CANOPY-060 ---
    (
        "and the prompt's accept and drop options describe broken rows and placeholder values that a cap refusal does not have (P2, canopy repo, pre-existing;",
        "and the prompt's options never mention the cap (P2, canopy repo, pre-existing;",
    ),
    (
        "  - A request without a symbols list asks for all 503 bundled constituents, so it is refused unless an opt-in\n"
        "    is sent. canopy's CHANGELOG records that refusal for the restart modal's old re-stage.",
        "  - At juniper-data's defaults a request whose symbols outnumber the cap is refused unless it opts in. A\n"
        "    request with no symbols list asks for all 503 bundled constituents; canopy's CHANGELOG records that\n"
        "    refusal for the restart modal's old re-stage, since fixed. Today every canopy staging path sends the\n"
        "    seed's 5 symbols (`src/model_registry.py:267-277`), so from the page the refusal needs a custom list of\n"
        "    more than 14 symbols, `max_symbols` set below the list's length, or a deployment ceiling below the list's\n"
        "    length (round 1, Lanes 10-B1 and 10-B2).",
    ),
    ("`src/tests/unit/frontend/test_dataset_shortfall_prompt.py:36-45`", "`src/tests/unit/frontend/test_dataset_shortfall_prompt.py:37-46`"),
    (
        "  workflow completes, and the producer's remedy is on screen. What is missing is the permanence notice and an\n"
        "  accurate description of the options.",
        "  workflow completes, and the producer's remedy is on screen. What is missing is juniper-data's dataset-level\n"
        "  permanence sentence, and any mention of the cap.",
    ),
    (
        "- **Fix direction:** cut only at `\" To accept it,\"`. Word the options for both refusal classes, or key the\n"
        "  copy on the class: juniper-data's cap sentence names the cap.",
        "- **Fix direction:** cut only at `\" To accept it,\"`. Word each option for both cases, the cap and then accept\n"
        "  or drop, without keying the accept/drop choice away for a cap refusal.",
    ),
    # --- F-CANOPY-061 / -062: the exemption from the live-re-drive rule ---
    (
        "  to everyone (`src/canopy_constants.py:668-674`). A docs switch computed apart from authentication is the\n"
        "  drift that comment guards against.",
        "  to everyone (`src/canopy_constants.py:668-674`). A docs switch computed apart from authentication is the\n"
        "  drift that comment guards against.\n"
        "- **FIXED without a live re-drive** (round 1, Lane 10-B1). This ledger's usual rule keeps a merged fix OPEN\n"
        "  until one (Phase 4's status correction). Neither F-CANOPY-061 nor F-CANOPY-062 is observable through the\n"
        "  page, neither has a matrix row, and each is verified by canopy#685's diff and by tests that assert the\n"
        "  behaviour both ways: `src/tests/regression/test_outbound_secret_leaks_boot.py:420` and `:429` for this\n"
        "  one, and `test_security.py:700` for F-CANOPY-062.",
    ),
    (
        "  here. Neither was re-derived as a canopy E2E finding.",
        "  here. Neither was re-derived as a canopy E2E finding.\n"
        "- FIXED without a live re-drive, for the reasons under F-CANOPY-061.",
    ),
    # --- F-CANOPY-063 ---
    (
        "  - This phase found two more: this one, and F-CANOPY-060's fixture. F-CANOPY-064's N6 fixture is a third,\n"
        "    which builds a key that the live relay never delivers.",
        "  - This phase found four: this one, F-CANOPY-060's fixture, F-CANOPY-064's N6 fixture (rows in the dashboard\n"
        "    shape carrying `kind`, a shape no path delivers) and F-CANOPY-065's N5 fake (a flat WS ack, where the\n"
        "    real one nests the partition). A claim-text grep finds only the first two kinds.",
    ),
    # --- F-CANOPY-064 ---
    (
        "**F-CANOPY-064 — the Training Metrics charts plot cascor's `epoch` field on one x-axis, though cascor writes two numberings into it and tells them apart with a `kind` key that canopy's relay drops: the Classification Metrics chart reads as empty for a CasCor run (the archived control capture shows no accuracy line beside a 96.30% Accuracy tile), and in service mode the Training Step tile's `kind` filter cannot work, so mid-pass it would show an inner output epoch (P1, canopy repo, with a cascor labelling question; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O2, widened 2026-10-04; OPEN).**",
        "**F-CANOPY-064 — the Training Metrics charts keep accuracy only on rows labelled `output` and plot cascor's `epoch` field on one x-axis, though cascor labels the growth loop's rows `candidate`, writes two numberings into `epoch` and tells them apart with a `kind` key that canopy's normalizing paths drop: the Classification Metrics chart shows no accuracy line for a CasCor run that grows (one point after the run, in both archived captures, beside Accuracy tiles of 98.75% and 96.30%), and in service mode the Training Step tile's `kind` filter cannot work, so mid-pass it would show an inner output epoch (P1, canopy repo, with a cascor labelling question; present in Phase 1's own capture of 2026-08-10 and missed there; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O2; widened 2026-10-04; OPEN).**",
    ),
    (
        "  Accuracy therefore sits at x = 1…N, the steps, on an axis that runs to the inner-epoch budget.",
        "  Whatever accuracy reaches the chart sits at x ≤ N, the step count, on an axis that runs to the inner-epoch\n"
        "  budget (round 1, Lane 10-B2).",
    ),
    (
        "    step row. The archived tiles read 11, 13 and 22, which are correct.",
        "    step row. The archived tiles read 11, 13, 22 and 2, which are correct.",
    ),
    (
        "  - N6's test cannot see this. `test_n6_counter_semantics.py:51` builds its `output_epoch` rows with a `kind`\n"
        "    key that the relay never delivers.",
        "  - N6's test cannot see this. `test_n6_counter_semantics.py:51` builds its `output_epoch` rows in the\n"
        "    dashboard shape with `kind`, a shape no path delivers.",
    ),
    (
        "    run with canopy's default budgets, the accuracy curve cannot be read.",
        "    run that grows, the chart shows no accuracy curve at all, whatever the budget.",
    ),
    # --- F-CANOPY-065 ---
    (
        "**F-CANOPY-065 — `/api/set_params`'s `applied` list, and the toast built from it, omits every key sent over `/ws/control`, and with them any key cascor declined there: canopy's partition extractor never looks where cascor's WS ack carries the partition (P2, canopy repo; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O3; OPEN).**",
        "**F-CANOPY-065 — `/api/set_params`'s `applied` list omits every key sent over `/ws/control`, so the apply toast canopy 0.6.0 promised never reports a key cascor declines there: canopy's partition extractor never looks where cascor's WS ack carries the partition (P1, canopy repo; observed 2026-09-23 by the canopy selection arc's A-N2 run as its O3; re-rated P1 in round 1 of this phase's validation; OPEN).**",
    ),
    (
        "  - a mutation that also scans `data.result` recovers the three WS keys and `epochs_max`'s `not-updatable`\n"
        "    skip.",
        "  - a mutation that also scans `data.result` recovers the three WS keys and `epochs_max`'s `not-updatable`\n"
        "    skip on the WS-only arm. On the mixed arm it does not, because the REST envelope's `data` replaces the WS\n"
        "    frame's first. The script writes its own copy of `apply_params`' merge; Lane 10-A2 drove the real one\n"
        "    with the same result, and unwrapping the ack in `_apply_params_hot` alone recovered all four WS keys and\n"
        "    the skip.",
    ),
    (
        "- **What a user loses.** The toast lists only REST-routed keys as applied, and a key that cascor declines on\n"
        "  the WS leg is not reported as declined.",
        "- **What a user loses.** The apply toast lists no keys. It reads \"Parameters applied\" unless a skip partition\n"
        "  reaches it (`_compose_apply_toast`, `dashboard_manager.py:9091-9145`), and A-N2's answer gives it none. So a\n"
        "  key cascor declines on the WS leg is never reported, and when the REST leg reports a skip, the applied count\n"
        "  leaves out the WS keys. Executed on A-N2's archived answer, the toast reads \"Parameters applied\"; with the\n"
        "  partition the WS ack carried, \"Applied 4 parameter(s); 1 skipped: nn_max_total_epochs (not-updatable)\"\n"
        "  (round 1, Lane 10-B2; the function re-read by the orchestrator).",
    ),
    (
        "- **Severity: P2**, drift. The values land, and the manual documents no applied or skipped list.",
        "- **Why the tests missed it.** The N5 test fakes the WS ack as flat, `{\"applied\": [\"learning_rate\"]}`\n"
        "  (`src/tests/integration/test_n5_apply_params_ux.py:308`), and the extractor's docstring says \"the WS ack\n"
        "  carries it flat\" (`cascor_service_adapter.py:1429-1430`). The real frame nests the partition at\n"
        "  `data.result` (round 1, Lane 10-B1).\n"
        "- **Severity: P1**, re-rated in round 1 (Lane 10-B1; re-derived by the orchestrator). canopy's CHANGELOG\n"
        "  shipped the promise under 0.6.0: \"the toast shows what the live network took vs. declined with the reason\n"
        "  (e.g. `epochs_max (not-updatable)`)\", with \"REST-nested and WS-flat shapes both handled\" (canopy\n"
        "  `CHANGELOG.md:1975-1980`). The defects plan says canopy renders both sets\n"
        "  (`JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md:311`). On the default WS leg that\n"
        "  example never appears. This ledger already treats a promise outside the manual as documented: F-CANOPY-057\n"
        "  is P1 on the manual and a FAQ. The values themselves land.",
    ),
    (
        "- **Fix direction:** read the partition from `data.result`, or unwrap the ack in `_apply_params_hot`. Keep the\n"
        "  two legs' partitions apart instead of `update`-merging their dicts. Correct the comment.",
        "- **Fix direction:** unwrap the ack in `_apply_params_hot`, and keep the two legs' partitions apart instead of\n"
        "  `update`-merging their dicts; reading `data.result` alone does not fix a mixed Apply (above). Correct the N5\n"
        "  fake, the docstring and the \"default off\" comment, and test with a mixed Apply through the real\n"
        "  `apply_params`.",
    ),
    # --- Matrix effect and counts ---
    (
        "- No matrix row changes, because nothing was driven.",
        "- No matrix-table row changes. One workflow verdict is corrected from archived evidence: W1-09's PASS in run\n"
        "  `20260810T002233Z` (`statuses.tsv:81`, within `W1-01..11`) is refuted by that run's own capture, so W1-09 is\n"
        "  FAIL on F-CANOPY-064 (its entry has the evidence). The run's `statuses.tsv` is left as recorded.",
    ),
    (
        "- **Counts**, from `e2e_finding_triage.py`: **77 findings**, 53 fixed, 1 accepted, 2 withdrawn, **21 open**.",
        "- **Counts**, from `e2e_finding_triage.py`: **78 findings**, 53 fixed, 1 accepted, 2 withdrawn, **22 open**.",
    ),
    (
        "  - **6 open P1:** F-CANOPY-055, F-CANOPY-057, F-CANOPY-058, F-CANOPY-064, F-CASCOR-001 and F-CASCOR-002.",
        "  - **7 open P1:** F-CANOPY-055, F-CANOPY-057, F-CANOPY-058, F-CANOPY-064, F-CANOPY-065, F-CASCOR-001 and\n"
        "    F-CASCOR-002.",
    ),
    # --- Still owed ---
    (
        "- **Item 16** is DONE (2026-10-04).",
        "- **Item 16** is DONE (2026-10-04), except its fixture sweep, which moves to item 19.",
    ),
    (
        "18. **F-CANOPY-064 (P1).** Carry `kind`, fix the axis, key accuracy on `kind`, and correct N6's fixture. Then\n"
        "    drive it live, mid-pass and after a run. Settle from an unslimmed history how many of a run's step rows\n"
        "    cascor labels `output`.",
        "18. **F-CANOPY-064 (P1) and F-CANOPY-067.** Carry `kind`, fix the axis, key accuracy on `kind`, correct N6's\n"
        "    fixture, normalize or drop the `initial_metrics` burst, and align `extendTraces` with the relay's rows.\n"
        "    Then drive it live: mid-pass, after a run, and across a relay reconnect with a page open, which also\n"
        "    settles F-CANOPY-067's rating. Confirm from an unslimmed history that only a run's last step row is\n"
        "    labelled `output`.",
    ),
    (
        "19. **F-CANOPY-060 and F-CANOPY-063.** canopy's wording and fixtures, and the rest of item 16's fixture sweep.",
        "19. **F-CANOPY-060 and F-CANOPY-063**, and item 16's fixture sweep. Do the sweep by comparing each fixture\n"
        "    with the shape its live path delivers, not by a grep. It covers N6's fixture (item 18), N5's WS-ack fake\n"
        "    (item 20), F-CANOPY-060's fixture and F-CANOPY-063's quote.",
    ),
    (
        "20. **F-CANOPY-065.** Read the WS leg's partition, and correct the \"default off\" comment.",
        "20. **F-CANOPY-065 (P1).** Unwrap the ack in `_apply_params_hot` and keep the legs' partitions apart. Correct\n"
        "    the N5 fake, the extractor's \"WS-flat\" docstring and the \"default off\" comment. Test with a mixed Apply.",
    ),
]

# (start, end, new): replace the text from `start` through `end` inclusive; each marker unique.
SPANS = [
    (
        "- **The options.** Accept and drop both re-stage with `allow_truncation=true`",
        "is the only text that says what accepting does.",
        "- **The options.** Accept and drop both re-stage with `allow_truncation=true`, adding `incomplete_rows` accept\n"
        "  or drop (`_restage_payload_with_policy`; `_resolve_dataset_shortfall_handler`). juniper-data applies the\n"
        "  cap first and then its incomplete-rows policy to the symbols it kept (`generator.py:314`, then `:338`, at\n"
        "  `29be6d35`). So both import at most the first 14 symbols, and the choice then decides, as for a shortfall,\n"
        "  whether any of those it cannot resolve are kept with placeholder values or dropped (round 1, Lane 10-B2;\n"
        "  re-derived by the orchestrator).\n"
        "  - The options' words, \"Accept broken rows and continue\" and \"Drop broken rows and continue\"\n"
        "    (`dashboard_manager.py:8442-8443`; the buttons are at `:2365-2366`), are right about that choice. They\n"
        "    never mention the cap. The producer's own sentence, which the prompt does show, is the only text that\n"
        "    says what accepting imports: the first 14 symbols.",
    ),
    (
        "- **Fix direction:** re-sync the quoted sentence.",
        "and\n  each needs its own check.",
        "- **Fix direction:** re-sync the quoted sentence. Pin it to cascor's text with a check that fails when cascor\n"
        "  moves, or quote only the marker and claim nothing about the rest. Finish item 16's sweep (item 19), as a\n"
        "  comparison of each fixture with the shape its live path delivers: a grep cannot find a wrong shape that\n"
        "  claims nothing. For the record, a case-insensitive grep of canopy's tests for \"verbatim from\", \"measured\n"
        "  on/off the\" and \"exact shape\" finds eleven lines. Two quote #532's retracted label; the other nine are\n"
        "  claim-bearing: `test_availability_unknown_state.py:87`, `test_f035_candidate_loss_from_history.py:139`,\n"
        "  `test_f054_replay_block_clientside.py:99`, `test_poller_budget.py:149`, `test_stage2_global_lane.py:114`\n"
        "  and `:339`, `test_start_fresh_refusal_and_modal_text.py:41`, and `test_dashboard_manager.py:612` and\n"
        "  `:732` (round 1, Lanes 10-A1 and 10-B2).",
    ),
    (
        "- **canopy's relay drops `kind`.**",
        "No consumer downstream can tell the numberings apart.",
        "- **canopy's normalizing paths drop `kind`.** `_normalize_metric` (`src/backend/cascor_service_adapter.py:1885`)\n"
        "  and `_to_dashboard_metric` (`:1960`) rebuild each row from fixed key sets without it. They serve\n"
        "  `get_current_metrics` and `get_recent_metrics` (`:457-482`), the relay of cascor's `metrics` frames\n"
        "  (`:778`), and the state sync at boot and on a model swap (`CascorStateSync.sync`,\n"
        "  `src/backend/state_sync.py:150`).\n"
        "  - Two paths do not normalize (round 1, Lanes 10-A1, 10-A2 and 10-B2; re-derived by the orchestrator in\n"
        "    source). The relay forwards every other frame type as it came (`:774-780`), cascor's `initial_metrics`\n"
        "    burst included; those rows keep `kind` but are flat, which F-CANOPY-067 records. And the clientside\n"
        "    `extendTraces` path (`src/frontend/components/metrics_panel.py:1015`) reads flat `e.loss` / `e.accuracy`\n"
        "    (`:1032-1037`), so it extends nothing from a relayed `metrics` frame, whose rows are nested. It acts on\n"
        "    the burst's flat rows only, plotting both numberings on trace 0 and a missing accuracy as 0 (Lane 10-B2,\n"
        "    executed in node).\n"
        "  - So no path delivers a row in the dashboard shape that carries `kind`, which is the shape N6's fixture\n"
        "    builds.",
    ),
    (
        "  - Executed (`util/ad-hoc/2026-10-04_phase10_o2_rederive.py`). Rows built as cascor's monitor builds them",
        "The same rows with `kind` kept read `3`.",
        "  - Executed (`util/ad-hoc/2026-10-04_phase10_o2_rederive.py`). Rows with cascor's keys and numbering, all\n"
        "    labelled `output` (three steps, then a pass cut at inner epoch 2501), went through canopy's two\n"
        "    normalizers and its real panel. The tile read `2501`; the same rows with `kind` kept read `3`. The chart\n"
        "    extents the script prints are artefacts of its all-`output` labelling (Lane 10-B2). Round 1 reproduced\n"
        "    the tile with rows from cascor's real `TrainingMonitor`: `441` and `1776` mid-pass against `5` and `2`\n"
        "    with `kind` kept (Lane 10-A2), and `2501` (Lane 10-B2).",
    ),
    (
        "  - The run used canopy's defaults, because its parameter caps were refused",
        "so it narrows as the budget grows.",
        "  - The run used cascor's engine defaults, because its parameter caps were refused (`03_set_params_caps.json`,\n"
        "    HTTP 502): Output Epochs (per pass) 10000. canopy's own default is 25 (`src/canopy_constants.py:75`;\n"
        "    Lane 10-A2). The chart held canopy's default Sliding Window of 500 rows. Each pass contributes 401 rows\n"
        "    (4,422 = 11 × 401 + 11), so the window held only steps 10 and 11, and a zoomed crop shows one accuracy\n"
        "    point, at x = 11 (Lanes 10-A2 and 10-B2).\n"
        "- **Present since at least 2026-08-10, and missed** (round 1, Lane 10-B1; the capture re-read by the\n"
        "  orchestrator). Phase 1's capture of run `20260810T002233Z`,\n"
        "  `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png`, shows the same chart: the 0–10k axis, one\n"
        "  marker cluster at x ≈ 11 under \"+Unit #10\" and no accuracy line, beside Accuracy 98.75% and Training\n"
        "  Step 11.\n"
        "  - That run scored `W1-01..11 PASS` (`statuses.tsv:81`). The range includes W1 step 9, \"loss and accuracy\n"
        "    plots accumulate points\" (the matrix's §4, W1). Its own capture refutes the accuracy half, so W1-09 is\n"
        "    FAIL on F-CANOPY-064 (Matrix effect, below). No later run re-scored it.\n"
        "  - M-METRICS-30's PASS in the same run rests on a trace count (\"accuracy plot 6 traces\", `statuses.tsv:75`).\n"
        "    That row tests zoom and pan, which this does not refute, so it stands.",
    ),
    (
        "- **A cascor labelling question, source-derived and not executed.** cascor labels each row with the monitor's",
        "  phase.",
        "- **A cascor labelling question**, source-derived and reproduced in round 1 with cascor's real\n"
        "  `TrainingMonitor` (Lanes 10-A2, 10-B1 and 10-B2). cascor labels each row with the monitor's phase.",
    ),
    (
        "  - How many of a run's step rows carry `output` is not established",
        "because the archive is slimmed.",
        "  - By the same source only a growth run's last step row, drained at `:2150` after the return to `output`,\n"
        "    carries `output` (Lane 10-B2). So the accuracy chart shows no point during growth and at most one after\n"
        "    a run, at any budget. The slimmed archive cannot confirm the count, and both captures show one point.",
    ),
    (
        "- **Fix direction.** Carry `kind` through `_normalize_metric` and `_to_dashboard_metric`.",
        "mid-pass for the tile and once after a run for the chart.",
        "- **Fix direction.** Carry `kind` through `_normalize_metric` and `_to_dashboard_metric`, normalize or drop the\n"
        "  relay's `initial_metrics` burst (F-CANOPY-067), and align the `extendTraces` path with the relay's row\n"
        "  shape. Plot each chart on one numbering: the step index for step rows, and within-pass samples on their\n"
        "  own axis or not at all. Key accuracy on `kind`, not on `phase`. Correct N6's fixture to the relay's shape.\n"
        "  Then drive it live: mid-pass for the tile, after a run for the chart, and across a relay reconnect.",
    ),
]

F067 = """
**F-CANOPY-067 — canopy's metrics relay forwards cascor's `initial_metrics` burst without normalizing it, so after a relay reconnect while a page is open, up to 100 flat rows can enter the metrics store, where the panel reads their loss and accuracy as 0 (P2 until observed live, canopy repo; found 2026-10-04 by round 1 of Phase 10's validation, Lanes 10-A1, 10-A2 and 10-B2; OPEN).**

- **The path** (re-derived by the orchestrator in source, at canopy `1b2dd438` and cascor `95cdc562`):
  - On a connect that is not a resume, cascor's `/ws/training` sends a `state` frame and then an
    `initial_metrics` burst of recent monitor rows (`src/api/websocket/training_stream.py:281-300`; 100 by
    default, `ws_initial_metrics_count`, `src/api/settings.py:382`). The rows are cascor's flat monitor rows:
    `loss` and `accuracy` at the top level, and `kind`.
  - canopy's relay normalizes only `metrics` frames and broadcasts every other type as it came
    (`src/backend/cascor_service_adapter.py:774-780`).
  - The browser bridge pushes each burst row into the metrics buffer (`src/frontend/assets/ws_dash_bridge.js:261-270`),
    and `_append_ws_metrics_store_handler` appends those rows unchanged to `metrics-panel-metrics-store`
    (`src/frontend/dashboard_manager.py:7813-7834`).
  - The panel reads `metric["metrics"]["loss"]` and `["accuracy"]` with a default of 0
    (`src/frontend/components/metrics_panel.py:1671-1672`, and the plots at `:1952` and `:2260`).
- **Executed, not observed.** Lane 10-A2 drove a frame from cascor's real `create_initial_metrics_message`
  through canopy's real relay loop and then its real panel: loss and accuracy plotted as 0, and the tiles read
  Loss 0.0000 and Accuracy 0.00%. Lane 10-B2 drove canopy's real relay loop against a fake stream: the burst
  rows kept `kind`, arrived flat, and with them in the store the loss values read `[0,0,0,0]`. Its node run of
  canopy's real `websocket_client.js` and `ws_dash_bridge.js` showed the burst rows extending the clientside
  traces with both numberings (F-CANOPY-064).
- **When it fires.** The relay connects at canopy's startup, before any page is open, so that burst reaches no
  page. It reaches pages on a relay reconnect, after a cascor restart or a dropped socket (F-CANOPY-049,
  F-CASCOR-004). How often that happens with a page open, and how long the rows stay in the store, were not
  measured.
- **Severity: P2 until observed live.** If a live check shows the tiles reading 0, it breaks the manual's
  "Real-time Updates" of loss and accuracy and becomes P1 (Still owed, item 18).
- **Fix direction:** normalize the burst's rows in the relay as `metrics` frames are, carrying `kind`
  (F-CANOPY-064), or drop the burst; include a relay reconnect in item 18's live drive.
"""

CONSENSUS = "CONSENSUS_RECORD_PENDING"


def apply(text: str) -> str:
    for old, new in SUBS:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"SUB anchor found {n} times: {old[:90]!r}")
        text = text.replace(old, new)
    for start, end, new in SPANS:
        i = text.find(start)
        if i < 0 or text.find(start, i + 1) >= 0:
            raise SystemExit(f"SPAN start not unique: {start[:90]!r}")
        j = text.find(end, i)
        if j < 0:
            raise SystemExit(f"SPAN end not found after start: {end[:90]!r}")
        text = text[:i] + new + text[j + len(end):]
    anchor = "\n### Declined\n"
    if text.count(anchor) != 1:
        raise SystemExit("Declined anchor not unique")
    text = text.replace(anchor, F067 + anchor)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only and report")
    args = ap.parse_args()
    before = LEDGER.read_text(encoding="utf-8")
    after = apply(before)
    if CONSENSUS not in after:
        raise SystemExit("consensus placeholder missing")
    print(f"{len(SUBS)} substitutions, {len(SPANS)} spans, F-CANOPY-067 inserted; {len(before)} -> {len(after)} chars")
    if not args.check:
        LEDGER.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
