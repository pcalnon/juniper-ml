# A-N2 (item 18): generate → stage → train → render through canopy, once per §12-seeded generator

**Date**: 2026-09-23. The stack was up 19:27–19:58Z and the runs were 19:30–19:55Z.
**Item**: 18 (A-N2) of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md`.
**Requirement**: §12.4 of `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`, which asks for "generate → stage → train → render, observed once" per newly seeded generator.
**Stack recipe**: `notes/JUNIPER_2026-07-21_JUNIPER-ECOSYSTEM_ISOLATED-STACK-E2E-CHECKLIST.md` (via `util/isolated_stack.bash`).

§12.6 of the selection-reachability design (`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`) fitted
`LMURegressor` directly. §12.7 of the same design went `generate → NPZ → CascadeCorrelationNetwork.fit`. Neither
touched canopy. This run drives every step through **canopy's HTTP API**: the routes the dashboard's callbacks and
buttons use. It adds a dashboard screenshot per generator as the literal "render".

## Verdict

**7 of the 8 §12 seeds complete the loop through canopy's Start button. `equities` does not whenever the live CasCor
network is narrower than its 15 features.** In that case canopy's Start returns **409** (F1 below). It completes through
the restart modal's **Start fresh** route. Both controls pass.

The `train` column is measured from `POST /api/train/start` to the first terminal poll of `GET /api/train/status`. The
LMU's own fit duration, from the recurrence log, is in brackets. Final metrics come from canopy's `GET /api/metrics`.

| # | generator (canopy value) | model | generate | stage | train | render | train wall | final metric |
|---|---|---|---|---|---|---|---|---|
| 01 | `spirals`, **pre-§12 control** | CasCor | PASS: `spiral-3.0.0-16e3f162cf258238`, 1000/400/300, 2 features | PASS: 200, `source: pending` | PASS: COMPLETED (early_stopped), 10 units | PASS: history 0→4422 rows, `/api/dataset` 2 features, dashboard "Completed — early stopped" | 152.1 s (cascor defaults, see Parameters) | val acc 0.9725, test F1 0.950, loss 0.0474 |
| 02 | `gaussian` | CasCor | PASS: `gaussian-3.0.0-cc2b5b8f05c7b9d9`, 100/40/30, 2 features | PASS: 200 | PASS: COMPLETED (early_stopped), 10→11 units | PASS: history +10 rows, `current_dataset=gaussian`, dashboard "Completed — early stopped" | 5.8 s | val acc 1.000, test F1 1.000, loss 0.0029 |
| 03 | `checkerboard` | CasCor | PASS: `checkerboard-3.0.0-01064f5fe366ae03`, 200/80/60, 2 features | PASS: 200 | PASS: COMPLETED (max_iterations), 11→19 units | PASS: history +45 rows, `current_dataset=checkerboard`, dashboard "Completed — max iterations" | 12.5 s | val acc 0.4875 (chance), test F1 0.663, loss 0.2479 |
| 04 | `equities`, via **Start** | CasCor | PASS: `equities-5.0.0-efb9b8316674e4ce`, 15881/1986/1983, 15 features, seed params intact | PASS: 200 (seed reached cascor as `params`) | **FAIL**: `POST /api/train/start` → **409** "`_pad_dataset_for_network: dataset (15, 2) exceeds network capacity (2, 2); resize the network first`" | N/A: no run. The routes keep serving checkerboard's results under an `equities` label (F1) | — (start refused after 15.6 s of generation) | — |
| 04b | `equities`, via **restart, Start fresh** | CasCor | PASS: the same id re-served (`POST /v1/datasets` 201, artifact GET 200) | PASS: 200 | PASS: COMPLETED (below_threshold), vanilla 15×2 network, 1 unit | PASS: history reset to 804 rows (start_fresh), `/api/dataset` 15 features, dashboard "Completed — converged", Input Nodes 15 | 33.3 s (cascor **defaults**: caps discarded, F2) | val acc 0.534, test F1 0.488, loss 0.2489 |
| 05 | `multi_sine` | Recurrence | PASS: `multi_sine-3.0.0-8dfa94a78568d243`, 1574/197/197 windows, 1 feature | PASS: 200, `dataset_ref` echoed | PASS: trained (converged) | PASS: `/api/metrics` + 1-row history; `/api/dataset` names the same id; dashboard LMU panel R² 1.0000 | 0.42 s (fit 0.237 s) | R² 1.0000, MSE 1.7e-15 |
| 06 | `mackey_glass` | Recurrence | PASS: `mackey_glass-3.0.0-f3f55d08e42c7141`, 1574/197/197, 1 feature | PASS: 200 | PASS: trained (converged) | PASS: `/api/dataset` names the id; dashboard R² 0.9999 | 0.21 s (fit 0.124 s) | R² 0.9999, MSE 6.0e-06 |
| 07 | `irregular_sine` | Recurrence | PASS: `irregular_sine-3.0.0-4a5904b53d15aa7d`, 1574/197/197, 1 feature | PASS: 200 | PASS: trained (converged) | PASS: `/api/dataset` names the id; dashboard page text R² 0.9918 (in the PNG the welcome modal covers that tile; status bar at mount default at 45 s, O1) | 0.21 s (fit 0.146 s) | R² 0.9918, MSE 0.0162 |
| 08 | `ar_p` | Recurrence | PASS: `ar_p-3.0.0-623a212735964d0a`, 1574/197/197, 1 feature | PASS: 200 | PASS: trained (converged) | PASS: `/api/dataset` names the id; dashboard page text R² 0.0429 (welcome modal open in the PNG) | 0.42 s (fit 0.165 s) | R² 0.0429, MSE 0.0122 |
| 09 | `delay_product` | Recurrence | PASS: `delay_product-3.0.0-10ae313fa6bdef23`, 1574/197/197, 1 feature | PASS: 200 | PASS: trained (converged) | PASS: `/api/dataset` names the id; dashboard R² 0.0053 (status bar at mount default at 45 s, O1) | 0.21 s (fit 0.151 s) | R² 0.0053, MSE 2.48 |
| 10 | `equities_seq`, **LMU control** | Recurrence | PASS: `equities_seq-5.0.0-c7916412c2344e07`, 15561/1986/1983 windows, 15 features | PASS: 200 | PASS: trained (converged) | PASS: `/api/dataset` names the id; dashboard R² 0.0084 | 75.4 s (fit 67.9 s) | R² 0.0084, MSE 4.4e-04 |

**What §12.4 asks for.** A generator that cannot complete the sequence should be seeded disabled with a reason.
**`equities` is the only candidate.** It generates, stages and trains; what fails is canopy's **Start** on a live
CasCor model built for a narrower dataset. That is a property of the Start path, and of any dataset wider than the live
network. It is not a property of the `equities` generator. So the remedy is more likely a Start-path fix, or a
"use Start fresh" affordance, than disabling the seed. That is the owner's call.

**Ordering.** For CasCor, "generate" happens **inside Start**: cascor's `_reload_dataset` calls juniper-data when it
consumes the staged config. For the LMU, it happens inside the recurrence service's `POST /v1/train`. The literal order
is therefore stage → Start (generate, then train) → render. Generation is evidenced from the isolated juniper-data leg,
read-only: its dataset list before and after each case, the new id's metadata, and its access log.

## What ran, and proof of what each leg imported

| leg | port / pid | code (sha, version) | `/v1/health` `git_sha` |
|---|---|---|---|
| juniper-data | 8111 / 3802524 | worktree `ce4368190a11f40d93e1bccd1a2fee2ea20632a0` (origin/main), 0.15.0 | = HEAD (**stamped** by the wrapper, note 1) |
| juniper-cascor | 8212 / 3803758 | worktree `f7a6d57347dad86d830bbf80b735ba6e54bb3868` (origin/main), 0.11.0 | = HEAD |
| juniper-canopy | 8061 / 3805344 | worktree `480746530fbe9062a6a3eaad5cab165c85b72ce8` (origin/main), 0.8.1 | = HEAD |
| juniper-recurrence | 8221 / 3804962 | PRIMARY checkout `9b240253589c241004409bdef3f5b211909b9805`, 0.5.0 (note 4) | not reported |

All three worktree `git_sha` verdicts were **MATCH**. A stamp is only as honest as what was imported, so each leg also
has an import proof:

1. **juniper-data** ran from a dedicated venv with extras `api,mnist,equities` (yfinance 1.7.0, datasets 5.0.1,
   pandas 3.0.6). The venv's `juniper_data.__file__` is in the worktree, and `pip show` reports an editable install
   whose project location is the synthetic root's symlink to the worktree. `isolated_stack.bash` does not stamp data's
   `git_sha`, so the wrapper stamps it from the worktree HEAD.
2. **juniper-cascor** ran in `JuniperCascor1` (Python 3.14.7, torch 2.11.0) with process cwd = worktree `src`.
   - Since the process started it compiled 47 worktree modules, including the server-only
     `src/api/lifecycle/__pycache__/manager.cpython-314.pyc`.
   - A same-interpreter, same-cwd probe resolves `api` and `cascade_correlation` to the worktree. The env's editable
     install of the primary checkout does not win.
3. **juniper-canopy** ran in `JuniperCanopy1` (Python 3.13) with cwd = worktree `src`.
   - It compiled 60 worktree modules, including `frontend/dashboard_manager`, `backend/service_backend` and
     `backend/cascor_service_adapter`, all tagged `cpython-313` (canopy's interpreter).
   - The probe resolves `model_registry`, `backend` and `frontend` to the worktree.
4. **juniper-recurrence** is the `juniper-recurrence` console script in `JuniperCascor1`, an installed package this run
   did not choose.
   - Its 0.5.0 is an **editable install of the PRIMARY checkout** `/home/pcalnon/Development/python/Juniper/juniper-recurrence`,
     clean and equal to its local `origin/main`.
   - **juniper-recurrence-model 0.1.5** is a site-packages install; the released line is 0.3.x (O8).
   - juniper-recurrence-client 0.3.0 and juniper-data-client 0.5.0 are editable installs of the primary checkouts.
   - Proof: an import probe with the service's interpreter and cwd, plus `pip show`.

All three worktrees are clean: `git status` shows only ignored `__pycache__/`, `logs/` and `*.egg-info/`. Details are
in `00_stack/provenance.json`. The worktree paths are listed at the end of this file.

**Isolation.** The legs ran on 8111 / 8212 / 8061 / 8221, from a synthetic ecosystem root of symlinks under the
session scratchpad (`a-n2-eco/`), with run dir `a-n2-run/`. Every bring-up and teardown went through
`util/ad-hoc/2026-09-23_a_n2_stack.bash`. That wrapper hard-sets every override and refuses a default port. It also
refuses `--up` on an occupied port, and refuses `--down` unless each listener is a pid this run recorded. Snapshots
went to the run dir (`JUNIPER_CASCOR_SNAPSHOTS_DIR` and `JUNIPER_E2E_CANOPY_SNAPSHOT_DIR`), never to a checkout.

The other session's stack was recorded before bring-up (`00_stack/protected_stack_before.txt`) and after teardown
(`99_postflight/postflight.json`): pids 2856834 / 2857489 / 2858037 were still alive and listening on
8101 / 8202 / 8051, unchanged. The :8055 and :8056 canopy instances changed pid between 19:14Z and 19:25Z, before this
run started anything. Some other session restarted them; this run did not touch them.

## How canopy was driven

Each call below is the dashboard's own call, reproduced over HTTP against :8061 by
`util/ad-hoc/2026-09-23_a_n2_drive.py`:

| step | route | the dashboard's origin of the call |
|---|---|---|
| select | `POST /api/model/select {"nn_model"}` | `_select_model_handler` |
| caps (CasCor) | `POST /api/set_params {nn_model, nn_*/cn_*}` | the params panel's Apply |
| stage | `POST /api/stage_dataset` | `_apply_dataset_handler` at canopy `48074653`. Spirals send the four typed fields, taken from the sidebar's service-mode values (`/api/state`). Everything else sends `{"nn_dataset_type", "nn_dataset_params": dataset_default_params(value) (omitted when empty), "nn_model"}` |
| start | `POST /api/train/start`. Recurrence sends the one-shot body `{"dataset": {"generator", "params"?}}` | the Start button's REST transport (`restFallback()`) and `_resolve_oneshot_start_body_handler` |
| restart | `POST /api/train/restart {"start_fresh": true, "reset": true}` | the restart modal. Used only for 04b |
| poll | `GET /api/train/status` every 0.2 s, then every 2 s after 15 s | — |
| render | `GET /api/metrics`, `/api/metrics/history?limit=0`, `/api/dataset`, `/api/state`, `/api/status`, `/api/selection`, `/api/topology`, `/api/network/stats`, `/api/decision_boundary` | the Training Metrics store poll, status bar, network info, dataset view, topology and decision-boundary panels |

Every request carried a same-origin dashboard's credentials: the session cookie, `Origin: http://127.0.0.1:8061`, and an
`X-CSRF-Token` from `GET /api/csrf`. **canopy ran OPEN**: no `CANOPY_API_KEY`, and it logged "running OPEN" at start.
So `require_browser_control_auth` would have admitted the requests without those headers too.

The **"render" screenshots** come from `util/ad-hoc/2026-09-23_a_n2_screenshot.py`: Playwright 1.59.0 headless Chromium
from `JuniperCanopy1`, one fresh browser context per capture. Its only input is closing the first-visit welcome modal.
It saves `dashboard.png`, the page text, the console log, and the status bar sampled at fixed times after load.

## Parameters set

- **CasCor caps**, through `/api/set_params` before every CasCor case after the control: `nn_max_iterations=8`,
  `nn_output_epochs=60`, `nn_max_total_epochs=60`, `cn_training_iterations=40` and `nn_max_hidden_units=32`. These
  mirror the probe behind §12.7 of the selection-reachability design (`util/ad-hoc/2026-09-10_rank2_cascor_fit.py`).
  - **Max-epochs hazard**: both the max-epochs-style field and the output-epochs field went at 60. cascor reports
    `epochs_max` as derived and read-only since C2b. Canopy's Start sends no `max_epochs`, and cascor's `fit()` then
    reads `output_epochs` for the initial pass too, so 60 governs every output pass.
  - **Landed**: `/api/state` read the live cascor values back as 8 / 60 / 40 / 32, with derived
    `nn_max_total_epochs=860`.
  - **Why 32 hidden units, not 8**: canopy's Start continues the current model by default, and the control left 10
    units. A lower total cap would forbid growth, so growth per run is bounded by the 8 iterations instead.
- **Control (01) ran at cascor's engine defaults**: max_hidden_units 10, output_epochs 10000, candidate_epochs 400,
  max_iterations 1,000,000, patience 50. On a fresh cascor no network exists until the first Start, so
  `/api/set_params` returned **502** "Backend rejected parameters: No network created". That is expected on a fresh
  service. It is recorded in `01_spirals_control/03_set_params_caps.json`.
- **04b ran at engine defaults as well**: `start_fresh` discarded the caps (F2).
- **LMU**: the service's effective defaults. Canopy's `/api/set_params` has no `d` / `theta` / `ridge` fields, and the
  one-shot body carried none. The registry seeds are the only dataset params: `{}` for the five synthetics, and
  `{"symbols": [5 names], "regression_target": "return", "fundamentals_fill": "drop"}` for `equities_seq`.
- **`equities` seed**: `{"symbols": ["AAPL","MSFT","GOOGL","AMZN","NVDA"], "fundamentals_fill": "drop", "normalize_features": true}`.
  It reached juniper-data intact: the dataset metadata's `params` echo all three, with the deployment's
  `max_symbols=14` bound server-side. So the §12.8 defaults channel works end to end through canopy → cascor → data.

## Findings

### F1: `equities` Start is refused whenever the live CasCor network is narrower than the dataset (the only FAIL)

- **Step**: `POST /api/train/start`. Response **409**:
  `{"detail": "Training could not be started: Training cannot be started: _pad_dataset_for_network: dataset (15, 2) exceeds network capacity (2, 2); resize the network first"}`.
  The request took 15.6 s: cascor generated and loaded the dataset inside Start, then refused.
- **Logs** (in `04_equities/logs/`):
  - cascor: `Reloaded dataset 'equities' (15881 train samples)`, then
    `WARNING - Start training failed: _pad_dataset_for_network: dataset (15, 2) exceeds network capacity (2, 2)…`, then
    `"POST /v1/training/start HTTP/1.1" 409 Conflict`.
  - canopy: `[ERROR] …cascor_service_adapter: Failed to start training: …`, then
    `[WARNING] system: Training start rejected: …`.
- **Cause**: canopy's Start continues the current model (`start_fresh=False`). cascor's `start_training` then pads a
  *smaller* dataset up to the network, but refuses a *larger* one: "only `swap_dataset_live` owns the grow path"
  (`juniper-cascor` `src/api/lifecycle/manager.py`, `_pad_dataset_for_network` and the comment above its call in
  `start_training`). After `spirals`, `gaussian` and `checkerboard`, all of them 2-feature, the live network was
  (2, 2). Every CasCor seed except `equities` (15) and `mnist` (784) is 2-feature. So in practice `equities` fails
  Start unless it is the first thing a cascor process trains, or the operator picks **Start fresh**.
  - `mnist` should hit the same refusal. That is inferred from the code and was not run: `mnist` is not a §12 seed.
- **Aftermath**, from `04_equities/1*_render_*.json` and `04_equities/dashboard_after_refused_start.png`:
  - cascor consumed the staged config before refusing: `pending_dataset: null`, `current_dataset: equities`, and
    `/api/selection` reports `{"value": "equities", "source": "loaded"}`.
  - The network, status and metrics are still checkerboard's: COMPLETED (max_iterations), 19 units, Input Nodes 2,
    val acc 0.4875.
  - A freshly loaded dashboard shows checkerboard's results under "Current Dataset — Equities (tabular)", with the
    status bar reading "Completed — max iterations". The refusal is visible only as the transient alert in the tab
    that pressed Start.
  - `/api/decision_boundary` → 503 (cascor 500: "Failed to compute decision boundary").
  - A retry of Start would refuse identically, because the dataset stays loaded. That is inferred from the code and was
    not re-run.
- **Remedy path (04b)**: `POST /api/train/restart {"start_fresh": true}`, the restart modal's route, completes. cascor
  logs `start_fresh: discarded model…` and then `start_training: no network — creating 15x2 from dataset dims`.

### F2 (adjacent to A-N2): Start fresh discards the params applied just before it through `/api/set_params`

- **Sequence** (04b): `/api/set_params` caps, then `/api/stage_dataset`, then `/api/train/restart {"start_fresh": true}`.
- **Before the restart**, `/api/state` read 8 / 60 / 40 / 32 (`04_equities__restart-fresh/04_state_before.json`).
- **After it**, `/api/state` read `nn_max_iterations=1000000`, `nn_output_epochs=10000`, `cn_training_iterations=400`
  and `nn_max_hidden_units=10`: the engine defaults (`15_render_api_state.json`). The dashboard shows
  "Hidden Units 1 / 10" and "Iteration 0 / 1000000" (`04_equities__restart-fresh/dashboard.png`).
- **Mechanism**: `_start_fresh_reset_locked` sets `model = None`, and create-on-start builds
  `create_simple_config(input_size, output_size)`.
- **Why it matters**: the restart modal applies edited params *before* the restart (`_execute_restart_handler`: re-stage,
  then apply params, then restart). With **Start fresh** on, the operator's edits are therefore silently dropped.
- **Scope**: this was observed through the same two routes the modal calls. The modal itself was not clicked.

### Observations (not A-N2 failures)

- **O1: the status bar lags on a fresh page load.** The top status bar is fed by `/api/status` on `fast-update-interval`.
  All 12 timed captures (`*/dashboard*_timeline.json`) show its mount default, "Stopped | Idle | Step 0 | Hidden Units
  0", at the first sample, 13–16 s after load. `/api/status` had said COMPLETED or trained throughout.
  - The 6 CasCor captures switched to the run's state by 22–30 s.
  - 4 of the 6 LMU captures switched by 45–50 s.
  - `07_irregular_sine` and `09_delay_product` were **still** at the default at 45 s, while the LMU results panel beside
    it already showed the run's R².
  - Network Information, which is sampled, already showed the run's values at the first sample. The metric tiles and
    the LMU panel were not sampled, but they show the run's values at capture time (`dashboard_text.txt`).
- **O2: the Classification Metrics chart reads as empty for every CasCor case, including the control.**
  - Both metric charts plot `metric["epoch"]` as x (`frontend/components/metrics_panel.py` `_parse_metrics` /
    `_create_accuracy_plot`). That field is a per-phase counter, not a common axis: output rows run 1, 26, 51, … and
    end on the step counter (11, 13, 22), while candidate rows reach 9551–10000.
  - The axis spans about 10k. Accuracy is drawn on output rows only, so it lands in a sliver at x ≤ 51.
  - The loss chart shares the axis and mixes the two counters too.
  - Not investigated further. It may already be on the canopy E2E findings register.
- **O3: `/api/set_params`'s `applied` list under-reports.** It returned `{"applied": ["cn_training_iterations"]}` only.
  canopy logged `Cascor params updated via WS: ['max_iterations', 'epochs_max', 'max_hidden_units', 'output_epochs']`
  and `via REST: ['candidate_epochs']`. The keys routed over `/ws/control` are missing from the C2a partition, and so
  is `epochs_max`'s `not-updatable` skip. The values did land (`/api/state`).
- **O4: canopy's `/v1/health` `version` says 0.6.0 while the source is 0.8.1.** `APP_VERSION` comes from installed
  metadata, and `JuniperCanopy1`'s editable install of the primary is 0.6.0. `git_sha` is the reliable field.
- **O5: 80 `WARNING … Network stats API returned 503`** while a dashboard was open under the recurrence backend. The
  network-info details poll hits `/api/network/stats`, and that route has no recurrence branch. Log noise at slow-tick
  cadence.
- **O6: `gaussian` and `checkerboard` trained on a continued model.** Canopy's Start default carried the control's
  10-unit spirals network into both runs, adding 1 and then 8 units. Their loops pass, but their metrics are not clean
  single-dataset fits. `checkerboard` at chance matches §12.7 of the selection-reachability design: "at its own
  default of 200 samples … sits at chance".
- **O7: `equities_seq` fit took 67.9 s**, against 39.6 s in the selection-reachability design's §12.6 (at generator
  3.0.0). Host-dependent, and well inside the 300 s one-shot timeout.
- **O8: the recurrence leg is not what a `pip install juniper-ml[recurrence]` user gets.** It runs the primary
  checkout of juniper-recurrence and juniper-recurrence-model **0.1.5**. The meta-package's `recurrence` extra pins
  `>=0.3.0,<0.4.0`.

## Against the recorded numbers (§12.6 to §12.8 of the selection-reachability design)

| generator | recorded | this run (through canopy) |
|---|---|---|
| `multi_sine` | (1574, 32, 1), fit 0.10 s, R² 1.000 | 1574 train windows, 1 feature, fit 0.237 s, R² 1.0000 |
| `mackey_glass` | fit 0.11 s, R² 0.9999 | fit 0.124 s, R² 0.9999 |
| `irregular_sine` | fit 0.11 s, R² 0.9918 | fit 0.146 s, R² 0.9918 |
| `ar_p` | fit 0.10 s, R² 0.043 | fit 0.165 s, R² 0.0429 |
| `delay_product` | fit 0.10 s, R² 0.004 | fit 0.151 s, R² 0.0053 |
| `equities_seq` | 5.0.0 re-generation: 15,557 train windows × 15 features; fit 39.6 s, R² −0.004 (at 3.0.0) | 15,561 windows × 15, fit 67.9 s, R² 0.0084 |
| `gaussian` | X_train (100, 2), 1 unit, top-1 1.000, 0.4 s | 100 train, +1 unit on a continued model, acc 1.000, 5.8 s |
| `checkerboard` | (200, 2), 1 unit, top-1 0.515 | 200 train, +8 units on a continued model, acc 0.500 / val 0.4875 |
| `equities` | (15877, 15) at 5.0.0 on 09-22, 4 units, loss 0.2498 → 0.2482 (4,000-row subsample) | 15881 train (the calendar moved); via Start fresh: 1 unit, loss 0.2489, val acc 0.534 |

## Deviations, ambiguities, and what was skipped

- **Payload shape.** The brief named `DashboardManager._dataset_stage_payload`. That builder is not on canopy
  `origin/main` (`48074653`); it is on the unmerged live-swap mirror branch. The body used is
  `_apply_dataset_handler`'s at `48074653`, which has the same keys.
  - The untouched form's rendered schema-default values were not added. For example, `equities`' form shows
    `max_symbols` 14 and `start_date` 2000-01-01. juniper-data fills the same defaults for an omitted key, as the
    dataset metadata confirms.
- **Start transport.** Only the Start button's REST transport was exercised. Its `/ws/control` transport, the one it
  prefers when the socket is open, was not.
- **Aborted first control attempt.** It made one `/api/model/select`, a no-op on cascor, and one `/api/set_params`,
  which returned 502 because no network existed. It then crashed in the driver's own juniper-data listing (`limit`
  above the route's 1000 cap) before staging. Its partial evidence was deleted and the case was re-run from scratch.
  No stage or start came from it.
- **Welcome modal.** The first-visit modal's header "x" was clicked only in `09_delay_product`. In the other 10 of the
  11 captures that tried, no modal was visible within the 10 s wait.
  - The modal is **open** in `07_irregular_sine/dashboard.png` and `08_ar_p/dashboard.png`, and in the control's first
    two captures (`01_spirals_control/dashboard.png` and `dashboard_settle60.png`). There it covers part of the
    Training Metrics panel. In 07 it covers the R² tile.
  - Every capture's `dashboard_text.txt` still carries the rendered values: R² 0.9918 for 07, 0.0429 for 08.
  - The control's `dashboard_final.png` has no modal.
- **Not run**: `mnist` and the other incumbents. They are not §12 seeds, and only `spirals` and `equities_seq` were
  asked for as controls.
- **Secrets**: the shell environment carries tokens that the stack legs inherit. Only a named allow-list of environment
  keys was ever read from `/proc/<pid>/environ`. Saved logs were passed through a token redactor, and a final grep of
  this directory found no token-shaped strings.
- **Slimming**: after `verdicts.json` was computed from the full captures, `slim` truncated bulky captures in place.
  - The capture was 63 MB and is 6.9 MB after slimming.
  - Metrics-history lists now keep their first 3 and last 20 rows plus the count.
  - `/api/dataset`'s echoed `inputs` / `targets` arrays and the decision-boundary grids now keep their shape and first
    rows.
  - cascor's per-candidate-epoch `[candidate_unit.py:…] INFO` lines were dropped, with the count noted at the top of
    each log.
  - Every cut carries `_truncated_by_a_n2_slim`.

## Evidence layout

- `00_stack/`
  - `stack_up.log`, `stack_down.log`: the wrapper's output.
  - `protected_stack_before.txt`.
  - `provenance.json`: health, pids, cwd, compiled-module lists, import probes, `pip show`.
  - `logs/`: the four full service logs, redacted. cascor's is slimmed.
  - `batch_*.log`: the batch runner's console.
- `NN_<case>[__<tag>]/`
  - `NN_<step>.json`: every HTTP exchange, with request body, status, response and elapsed time.
  - `poll_timeline.json`: each status change during training.
  - `data_new_datasets.json`: the juniper-data ids created and their metadata.
  - `logs/{data,cascor,canopy,recurrence}.{slice,excerpt}.log`: the byte-offset slice of each service log for the case,
    plus the lines matching errors, refusals and dataset calls.
  - `dashboard*.png`, `dashboard*_text.txt`, `dashboard*_console.txt`, `dashboard*_timeline.json`.
  - `summary.json`, `index.json`.
- `verdicts.json`: the per-stage PASS/FAIL/N/A above, computed from the saved evidence by `… summarize`.
- `99_postflight/postflight.json`.

## Scripts (all in `util/ad-hoc/`)

- `2026-09-23_a_n2_stack.bash`: the guarded wrapper around `util/isolated_stack.bash`.
- `2026-09-23_a_n2_drive.py`: `provenance`, `run <case>`, `summarize`, `archive-logs`, `slim`, `postflight`, `list`.
- `2026-09-23_a_n2_screenshot.py`: the dashboard capture. Run it with `JuniperCanopy1`'s Python.
- `2026-09-23_a_n2_run_batch.bash`: runs cases in order, taking a screenshot after each.

Reproduce, from the juniper-ml worktree, with the worktrees below still present:

```bash
bash util/ad-hoc/2026-09-23_a_n2_stack.bash --dry-run --up --with-recurrence
bash util/ad-hoc/2026-09-23_a_n2_stack.bash --up --with-recurrence
python3 util/ad-hoc/2026-09-23_a_n2_drive.py provenance
python3 util/ad-hoc/2026-09-23_a_n2_drive.py run 01_spirals_control --timeout 1200 --stop-on-timeout
bash util/ad-hoc/2026-09-23_a_n2_run_batch.bash 900 02_gaussian 03_checkerboard 04_equities
python3 util/ad-hoc/2026-09-23_a_n2_drive.py run 04_equities --tag restart-fresh --start-route restart-fresh --timeout 1800
bash util/ad-hoc/2026-09-23_a_n2_run_batch.bash 360 05_multi_sine 06_mackey_glass 07_irregular_sine 08_ar_p 09_delay_product 10_equities_seq_control
python3 util/ad-hoc/2026-09-23_a_n2_drive.py summarize
python3 util/ad-hoc/2026-09-23_a_n2_drive.py archive-logs
bash util/ad-hoc/2026-09-23_a_n2_stack.bash --down
python3 util/ad-hoc/2026-09-23_a_n2_drive.py postflight
python3 util/ad-hoc/2026-09-23_a_n2_drive.py slim
```

## Worktrees created (left in place: cleanup is owner-gated)

- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--verify--a-n2-loop--20260923-1415--ce436819`
  (detached at `ce436819`)
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--verify--a-n2-loop--20260923-1415--f7a6d573`
  (detached at `f7a6d573`). Holds 142 MB of ignored `logs/` from the service.
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--verify--a-n2-loop--20260923-1415--48074653`
  (detached at `48074653`)
