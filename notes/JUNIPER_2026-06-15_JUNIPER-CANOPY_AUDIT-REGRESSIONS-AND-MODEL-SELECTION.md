# Juniper-Canopy — Regression Audit, Model-Selection Design & UI Regression Harness — DELIVERABLE

**Project**: juniper-canopy (subject of audit) / juniper-ml (doc home)
**Author**: Paul Calnon
**License**: MIT License
**Status**: Empirically-validated deliverable (supersedes the working plan `JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md`)
**Last Updated**: 2026-06-16

> **⚠️ STATUS UPDATE (2026-06-17): §3 and §7 are now stale.** Canopy `#366` (merged
> 2026-06-16, *after* this doc) wired **all three** orphan controls — including
> `nn-init-output-weights-dropdown` and `dataset-plotter-dataset-selector`, which
> §3.2/§3.3 mark "deferred"; `KNOWN_ORPHANS` is now empty. The model-selection design
> (§4) and accessibility analysis remain the design of record. Current state +
> go-forward roadmap:
> [`JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md).
>
> This is the evidence-backed deliverable produced after the empirical phase. It
> supersedes the approved working plan
> [`JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md`](JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md).
> Every internal claim carries a `file:line` reference against juniper-canopy
> `test/ui-regression-harness` (base `c07dab8`); every external citation is
> retrieved into [`../papers/`](../papers/) with a specific URL + accessed-date.
> Verification commands and the exact test runs that back each claim are in §6.

---

## 1. Context & motivation

`juniper-canopy` is the Dash/FastAPI research dashboard (v0.5.0) and web front-end
for the Juniper platform. Two pressures converge:

1. **Enhancement (forward-looking).** A new `juniper-recurrence` model (LMU,
   irregular-Δt time-series) is being built (see the `JUNIPER_RECURRENCE_*`
   corpus in `notes/`). It must be selectable from canopy. Today canopy lets the
   user pick a **dataset** but offers **no way to pick a model**, and has **zero
   `task_type` awareness**. Some dataset×model combinations are intrinsically
   incompatible (a time-series dataset cannot train feed-forward CasCor; a 2-D
   classification dataset cannot train the recurrence model). Model selection
   needs **bidirectional compatibility gating**.

2. **Regressions (highest-priority blocker).** Canopy has persistent, fix-resistant,
   user-facing **dead-control** regressions clustered around dataset
   configuration/modification/selection. The team already named this the
   **"dead button" class**
   (`notes/CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md`). There
   was no automated net catching them, so they kept recurring.

**Outcome delivered:** (a) a deterministic automated harness that exercises every
canopy control and auto-extends to future controls; (b) a verified fix for the one
trivially-scoped proven dead control; (c) this audit/design document.

---

## 2. Current-state audit

### 2.1 Architecture

- **App entry** `src/main.py` — FastAPI app hosting the Dash dashboard; training
  control endpoints `POST /api/train/{start,stop,pause,resume,reset}`
  (`src/main.py:2748-2818`), `POST /api/set_params` (`src/main.py:2878`),
  `POST /api/stage_dataset` (`src/main.py:3041`),
  `DELETE /api/cancel_pending_dataset` (`src/main.py:3064`), `GET /api/state`
  (`src/main.py:916`), `GET /api/status`.
- **Orchestrator** `src/frontend/dashboard_manager.py` builds the layout and
  registers callbacks. The dataset stage/cancel/banner callbacks live in one block
  (`dashboard_manager.py:3507-3640`).
- **Backends** are pluggable behind `BackendProtocol`. Demo mode uses
  `DemoBackend` (`src/backend/demo_backend.py`) wrapping the `DemoMode` simulator
  (`src/demo_mode.py`). Demo mode is the deterministic, torch-free target for the
  harness.

### 2.2 Control-surface inventory (selected, `file:line`)

| Control id | Kind | Where | Wiring |
|---|---|---|---|
| `start/pause/stop/resume/reset-button` | Button | `dashboard_manager.py:786…` | Phase D clientside `buttonMap` (`dashboard_manager.py:120-124`) + REST fallback |
| `apply-params-button` | Button | `dashboard_manager.py:1433` | server callback → `POST /api/set_params` |
| `apply-dataset-button` | Button | dataset section | `apply_dataset` → `POST /api/stage_dataset` (`dashboard_manager.py:3522`) |
| `cancel-pending-dataset-button` | Button | banner | `cancel_pending_dataset` → `DELETE /api/cancel_pending_dataset` (`dashboard_manager.py:3564`) |
| `restart-with-new-dataset-button` | Button | banner (`dashboard_manager.py:1409`) | **was orphan; fixed this iteration** (§3.1) |
| `pending-dataset-banner` | Alert | `dashboard_manager.py:1424` | `is_open` driven by 4 callbacks incl. `reconcile_pending_dataset_banner` (base `:3588` / post-fix `:3621`) |
| `nn-dataset-type-dropdown` | Dropdown | `dashboard_manager.py:1113` | State-only by design (read on apply-dataset click) — **not** an orphan |
| `nn-init-output-weights-dropdown` | Dropdown | `dashboard_manager.py:880` | **orphan; deferred** (§3.2) |
| `nn-learning-rate-input` | Input(number) | `dashboard_manager.py:904` | `debounce=350` (`canopy_constants.py:267`); apply roundtrip |
| `{dataset_plotter}-dataset-selector` | Dropdown | `dataset_plotter.py:106` | **orphan; deferred** (§3.3) |

\* Line numbers in `dashboard_manager.py` ≥ 3583 shift by +33 on the fix branch
because the fix inserts the `restart_with_new_dataset` callback there; the table
cites post-fix lines where relevant.

This table is a **selected** sample, not the full surface: `util/ui_control_graph.py`
enumerates *every* actionable control programmatically by walking the realized
layout tree, so the orphan analysis in §3 is exhaustive even though this table is
illustrative.

### 2.3 The "dead button" taxonomy

A control is **actionable** if a user can act on it (Button/Upload/Dropdown/
Select/Input/Switch/Checklist/RadioItems/Slider — see `util/ui_control_graph.py:55`).
An actionable control is an **orphan** when no callback can ever observe it:

- **Trigger controls** (Button, Upload): useless unless read as a callback
  **Input** — a button read only as `State`, or not at all, can never fire
  (`ui_control_graph.py:75`).
- **Value-carriers** (everything else): their value must reach a callback **Input
  or State**, else it never enters the app
  (`ui_control_graph.py:162-169`).

This taxonomy is the empirical discovery engine in §3; it is encoded in the L1
lint (§5.1).

### 2.4 Docker-image caveat

The running `canopy:8050` / `cascor:8201` are the juniper-deploy Docker stack and
may be a stale image (cf. project memory "juniper-cascor image 2 months stale").
**All findings below were reproduced against a local demo instance**, not the
Docker stack — the harness boots `src/main.py` in demo mode on a free port
(`src/tests/ui/conftest.py:33-71`) or instantiates the app in-process. The Docker
stack is for cross-checking only.

---

## 3. Empirically-validated regression catalog

Discovery method: the L1 control-graph lint (§5.1) instantiates the Dash app in
demo mode and enumerates **every** actionable control vs. **every** callback
Input/State binding. Pre-fix it reported exactly **three** orphans (reproduced —
`python util/ui_control_graph.py` exits 1 listing all three). Each is triaged
below with root cause, severity, and fix-now-vs-defer.

### 3.1 `restart-with-new-dataset-button` — FIXED this iteration

- **Symptom:** Clicking "Stop & Restart with new dataset" in the pending-dataset
  banner did nothing.
- **Root cause:** the button (`dashboard_manager.py:1409`) appeared in **no**
  callback `Input`/`State`/`Output` — a textbook trigger-orphan.
- **Severity:** High — it defeats the documented cold-swap restart path
  (`FRONTEND_ISSUES_PLAN_2026-05-09.md §3` designed the cold swap but left this
  button unwired).
- **Fix (trivially scoped → done):**
  1. **Callback** (`dashboard_manager.py:3583` decorator / `:3588` def, fix branch):
     new server-side `restart_with_new_dataset` mirrors `cancel_pending_dataset` — on `n_clicks`
     it `POST /api/train/start?reset=true` and returns `False` to close the
     banner.
  2. **Demo parity** (`demo_mode.py:1475`, inside `DemoMode.start`'s `if reset:`
     block at `:1466`): `DemoMode.start(reset=True)` now clears `self._pending_dataset_config`. The real cascor backend clears its
     `pending_dataset` on `start_training(reset=True)` — the assumption baked
     into `reconcile_pending_dataset_banner`'s docstring
     (`dashboard_manager.py:3589-3595`). Demo mode did **not** mirror that, so the
     reconcile poll (`/api/status.pending_dataset`, surfaced at
     `demo_backend.py:119`) would re-open the banner on the next tick. This was
     the subtle second half of the bug.
  3. **Lint baseline** trimmed: `restart-with-new-dataset-button` removed from
     `KNOWN_ORPHANS` (`tests/unit/test_control_graph_lint.py`). The anti-rot test
     `test_known_orphans_not_stale` *forces* this once the control is wired.
- **Regression artifact (TDD, runnable):**
  `tests/integration/test_restart_with_new_dataset.py` — stage a dataset
  (`/api/stage_dataset`), assert `/api/status.pending_dataset` is set, then
  `POST /api/train/start?reset=true`, then assert `pending_dataset` is `None`
  (the exact signal that closes the banner). **Verified red→green** (§6).
- **PR:** stacked `fix/orphan-dataset-restart-button` off `test/ui-regression-harness`.

### 3.2 `nn-init-output-weights-dropdown` — DEFERRED (double break)

- **Symptom:** the "Init Output Weights" selector (`dashboard_manager.py:880`) has
  no effect on training.
- **Root cause — two independent breaks:**
  1. **Frontend:** the dropdown is read by no callback `Input`/`State`, so its
     value never reaches the Apply callback and is never POSTed.
  2. **Backend model:** even if it were POSTed, `nn_init_output_weights` is **not
     a declared field on `SetParamsRequest`** (`main.py:2831-2876`), so the value is
     silently discarded at request parsing (Pydantic's default `extra="ignore"`),
     before `model_dump(exclude_none=True)` (`main.py:2889`) ever runs — despite the
     handler's `nn_keys` list being ready for it (`main.py:2909`) and `/api/state`
     already round-tripping it (`main.py:938`, `:974`). (Verified: the outcome is a
     silent drop; the cause is parse-time `extra` handling, not `model_dump`.)
- **Severity:** Medium — silent no-op of a real hyperparameter.
- **Disposition:** **Deferred to its own PR.** Non-trivial: needs the frontend
  callback wiring **and** the `SetParamsRequest` field **and** a demo mirror.
  Retained in `KNOWN_ORPHANS` with this reason so L1 keeps it visible until fixed.

### 3.3 `{dataset_plotter}-dataset-selector` — DEFERRED (incomplete feature)

- **Symptom:** the Dataset-Visualization dataset picker
  (`dataset_plotter.py:106`, dynamic id `f"{component_id}-dataset-selector"`)
  selects nothing useful.
- **Root cause:** a `populate_dataset_selector` callback **writes** its `options`
  and `value` (`dataset_plotter.py:380-386`), but the user's **selected value is
  read by no callback `Input`/`State`** — the selection has nowhere to go. (It is
  an Output target but never an Input/State, which is precisely the value-carrier
  orphan condition.)
- **Severity:** Low — incomplete/unsurfaced feature, not a regression of working
  behavior.
- **Disposition:** **Deferred to its own PR.** Retained in `KNOWN_ORPHANS`.

---

## 4. Enhancement design — model selection + bidirectional compatibility gating

**Design only this iteration; implementation is a follow-up PR.** This section is
the design of record.

### 4.1 Registry (single source of truth)

`src/model_registry.py` (new):

- `ModelSpec{key, label, supported_task_types, input_ndim, is_live, gated_reason}`
- `DatasetTypeSpec{value, label, task_type, ndim}`
- `models_for_dataset(dataset_value) -> list[ModelSpec]`
- `dataset_values_for_model(model_key) -> list[str]`

Seed:

| key | live? | input_ndim | task_types | note |
|---|---|---|---|---|
| `cascor` | yes | {2} | {classification, regression} | current backend |
| `recurrence` | **gated** | {3} | {time_series, irregular_dt} | "coming soon" |

**Compatibility matrix** (the bidirectional gate, derived from `task_type` ∩
`input_ndim`). Every dataset canopy ships today is 2-D classification, so all are
cascor-compatible and recurrence-incompatible; the matrix becomes interesting once
juniper-data's 3-D irregular-Δt time-series generators land (WS-1):

| dataset (task_type, ndim) | `cascor` | `recurrence` |
|---|---|---|
| spirals / xor / circles / moons (classification, 2-D) | ✓ | ✗ hard-disable (ndim/task mismatch) |
| mnist (classification, 2-D) | ✓ | ✗ hard-disable |
| *future* time-series (time_series, 3-D) | ✗ hard-disable | soft-gate ("coming soon") |
| *future* irregular-Δt (irregular_dt, 3-D) | ✗ hard-disable | soft-gate |

"✓" = trainable now; "✗ hard-disable" = genuine incompatibility (`aria-disabled` +
tooltip, §4.3); "soft-gate" = compatible-but-not-yet-live (selectable + toast +
revert, so users discover it).

The registry also becomes the single source for the **dataset-type options
currently hardcoded inline** at `dashboard_manager.py:1115-1119`
(Spirals/XOR/MNIST/Circles/Moons), removing that duplication. It ties into the
juniper-data `task_type` + 3-D irregular-Δt NPZ contract (WS-1, `notes/`).

### 4.2 Dash mechanics

- **Selector:** `dcc.Dropdown id="nn-model-dropdown"` inserted above the
  dataset-type dropdown (`dashboard_manager.py:1111`), wrapped in
  `html.Div(id="nn-model-wrapper")`.
- **Bidirectional gating:** two callbacks recompute `options` (flipping per-option
  availability): model→dataset and dataset→model, intersecting with `is_live`. On a
  gating that invalidates the current selection, also `Output(..., "value")` to snap
  to the first compatible option.
- **Violation feedback:** a `dbc.Alert(duration=…, dismissable=True)` toast in a
  fixed Div at `top:13rem` (clears the existing outcome surfaces at 5rem/9rem).

### 4.3 Accessibility — why soft-gate + `aria-disabled`, not native `disabled`

This is the crux, and it is backed by retrieved primary sources (§8):

- A natively **`disabled`** control is **removed from the tab order** and fires
  **neither hover nor focus**, so a tooltip explaining *why* an option is
  unavailable can never appear. W3C APG: *"Browsers remove HTML input elements with
  the `disabled` attribute from the tab sequence"*
  ([`w3c-aria-tooltip-and-disabled.md`](../papers/w3c-aria-tooltip-and-disabled.md),
  Source 2). MDN: HTML `disabled` *"suppress[es] all functionality"* and removes
  focusability (Source 4).
- **`aria-disabled="true"`** keeps the element **focusable** while signaling
  unavailability to assistive tech: W3C APG endorses exactly this case — *"it is
  useful for an element to convey a disabled state while remaining focusable …
  accomplished by applying the state `aria-disabled="true"`"* (Source 2). NN/g
  concurs: disabled buttons *"should also have the ARIA-disabled: true attribute …
  allow the button to still receive tab focus"*
  ([`nngroup-disabled-buttons.md`](../papers/nngroup-disabled-buttons.md), Source 1).
  **Caveat (MDN, Source 4):** `aria-disabled` is *semantic only* — canopy must
  **manually suppress** activation of the gated option in callback logic.
- **Tooltip:** wrapper-targeted `dbc.Tooltip` (recomputed text). Because the gated
  item stays focusable, wire `aria-describedby` from the trigger to a
  `role="tooltip"` element so the "incompatible because…" explanation shows on
  **both hover and keyboard focus** — NN/g: *"Tooltips that appear only on mouse
  hover are inaccessible for users that rely on keyboards"* (Source 2). (`dcc.Dropdown`
  supports per-option `disabled` but **not** `title`; `dbc.Select` supports both —
  see versions in §6.)
- **Soft-gate vs hard-disable:** NN/g — disabled controls *"should [be used]
  sparingly, ensure they're accessible, and clearly explain why"* (Source 3). So:
  **soft-gate** the not-yet-available `recurrence` model (selectable + toast +
  revert value) so users *discover* it; **hard-disable** (with `aria-disabled` +
  tooltip) only genuine task-type incompatibilities.

### 4.4 Backend mirror (mandatory)

Add `nn_model` to `StageDatasetRequest` (`main.py:3025-3038`) and `SetParamsRequest`
(`main.py:2831`), thread through `demo_mode.py` + `demo_backend.py`, and reject
`recurrence` with a clean error until the service exists. (Note the §3.2 lesson:
a field absent from the request model is silently dropped — the mirror is not
optional.)

---

## 5. Automated regression-detection harness

Three complementary layers. **L1 + L2 are the deterministic, zero-browser,
auto-extending core (~90% of the value); L3 is a thin real-browser proof.**

### 5.1 L1 — static control-graph lint (no browser, default suite)

- `util/ui_control_graph.py`: instantiates `DashboardManager({}).app` in demo mode,
  walks the realized layout tree for ided actionable controls
  (`enumerate_controls`), walks `app.callback_map` for Input/State ids
  (`enumerate_bindings`), and reports orphans (`lint`). Pattern-matching dict ids
  are normalized by `type` (`id_key`, `:95`).
- Gate `tests/unit/test_control_graph_lint.py`: `test_no_new_orphan_controls`
  fails CI when any actionable control becomes unreachable;
  `test_known_orphans_not_stale` forces an entry out of `KNOWN_ORPHANS` once wired
  (baseline may only **shrink**). **This catches the entire dead-button class
  deterministically** — it would have caught `restart-with-new-dataset-button`
  instantly.

### 5.2 L2 — API/callback behavioral coverage (in-process `TestClient`, default suite)

- `src/tests/ui_contract/control_manifest.py`: declarative `ControlContract` rows
  (control_id, method, endpoint, body, expected response/state).
- `src/tests/integration/test_control_manifest_behavioral.py` parametrizes over the
  manifest, calls each endpoint via `TestClient(app)` (demo mode), and asserts the
  declared post-condition (response key and/or `/api/state` roundtrip).
- **Future-proofing:** adding one `ControlContract` row enrolls a control in L2; the
  L1 lint independently guarantees it is wired. Adding a control = add a row.

### 5.3 L3 — real-browser proof, and the empirical POC outcome

- **POC #2 (Playwright native-value-setter) — RUN, FAILED.** The corrected,
  literature-backed approach (native `HTMLInputElement.prototype.value` setter +
  **bubbling** `input`+`change` + blur + 350 ms debounce wait — the canonical
  workaround in [`react-controlled-input-onchange.md`](../papers/react-controlled-input-onchange.md))
  was implemented and run against `nn-learning-rate-input`. **Result: the Apply
  roundtrip pushed the *default* `0.01`, not the set `0.0123`.** `dbc.Input`
  (dash-bootstrap-components) has its own value-tracking that swallows the synthetic
  event, exactly as it swallows `el.value = x`. This **confirms the prior team's
  finding** (`test_apply_button_flow.py` history) with the canonical incantation, so
  it is now a settled negative result, not an untried idea. It is committed as a
  reproducible **strict-xfail** artifact, `src/tests/ui/test_l3_native_setter_poc.py`
  (it flips to XPASS if a future Dash release fixes the synthetic-event path — a
  canary for taking the un-xfail), and the `test_apply_button_flow.py` xfail record
  was upgraded to cite this evidence (commits `1cea5d9`, `c7b5dbc`).
- **POC #1 (dash_duo) — the working path, DEFERRED.** Dash's official
  `dash.testing`/`dash_duo` drives inputs via Selenium **`send_keys`** (real
  keystroke events that fire React's `onChange` natively) —
  [`dash-testing-dash-duo.md`](../papers/dash-testing-dash-duo.md). It requires
  `selenium` + `multiprocess` + `chromedriver` (none currently in `JuniperCanopy1`)
  and a dedicated `make test-ui-dash` job. **Deferred** as a scoped follow-up: it
  adds CI weight + flake surface for a deliberately thin layer, and —
  decisively — **the Apply→`/api/set_params`→`/api/state` contract this xfail
  targets is already proven deterministically by L2** (`apply-params-button` row),
  so the browser leg is redundancy, not a coverage gap.
- **Net L3 position:** keep `test_apply_button_flow.py` as a strict-xfail that
  documents the harness wall; the un-xfail is a clean, well-understood follow-up.

### 5.4 CI wiring

L1 + L2 ride the existing `unit-tests` / `integration` jobs — **no new
dependencies**, gating every PR (`.github/workflows/ci.yml`). L3 stays in the
existing `ui-tests` job (Playwright). selenium/Chrome are added only if/when the
dash_duo follow-up is taken.

---

## 6. Validation methodology + evidence appendix

Every claim above was produced empirically, not asserted. Reproduction (env
`JuniperCanopy1`; `source /opt/miniforge3/etc/profile.d/conda.sh && conda activate
JuniperCanopy1`):

| Claim | Command | Observed |
|---|---|---|
| 3 orphans pre-fix | `cd src && python ../util/ui_control_graph.py` | exit 1, lists the 3 of §3 |
| Bug is real (demo parity) | regression test applied to **base** *without* the `demo_mode.start` clear | **FAILED** — `pending_dataset` not cleared after restart |
| Fix works | regression test on **fix** branch | **PASSED** |
| 2 orphans post-fix | `python ../util/ui_control_graph.py` (fix branch) | exit 1, lists only §3.2 + §3.3 |
| L1 gate + L2 + regression (run on **fix** branch, which stacks both) | `pytest tests/unit/test_control_graph_lint.py tests/integration/test_control_manifest_behavioral.py tests/integration/test_restart_with_new_dataset.py -q` | **11 passed** (the harness branch alone yields 10; +1 is the fix's regression test) |
| No new regressions | `pytest -m "unit or integration" -q` | only a **pre-existing** `test_security` rate-limiter ordering flake (fails identically on base — confirmed) |
| L3 POC #2 fails (committed artifact) | `pytest src/tests/ui/test_l3_native_setter_poc.py --override-ini=addopts= -q` | `1 xfailed` — native-setter pushed default `0.01`, not `0.0123` |
| xfail intact | `pytest src/tests/ui/test_apply_button_flow.py --override-ini=addopts= -q` | `1 xfailed` |
| Lint/format | `flake8` + `black --check` + pre-commit on changed files | clean / all hooks pass |

**Independent validation (planned, §7 task):** independent sub-agents re-open every
`file:line` cited here, re-run every POC, and re-resolve every external URL; a
completeness critic hunts unverified/contradicted claims. Findings feed a fix list
applied to this doc.

**Anti-hallucination note:** reconnaissance initially mis-stated that the
`nn-init-output-weights-dropdown` was wired; the L1 lint contradicted that, and
§3.2 reflects the verified double break.

---

## 7. Execution plan / PR breakdown

**Landed / in-flight (this iteration):**

1. **canopy `test/ui-regression-harness`** — L1 lint + gate, L2 manifest + driver,
   L3 POC outcome documented on `test_apply_button_flow.py` (commits incl.
   `4fc6b68`, `1cea5d9`).
2. **canopy `fix/orphan-dataset-restart-button`** (stacked on #1) — §3.1 fix +
   regression test (`1a4cad6`).
3. **juniper-ml `docs/canopy-audit-recurrence-integration`** — this doc + the 4
   retrieved papers.

**Deferred (own PRs):**

- Model-selection feature implementation (§4) — registry, selector, gating,
  accessibility wiring, backend mirror.
- `nn-init-output-weights-dropdown` double-break fix (§3.2).
- `{dataset_plotter}-dataset-selector` wiring (§3.3).
- L3 dash_duo numeric-input proof (§5.3) — adds selenium+chromedriver + a CI job.
- `requirements.lock` reconcile (dash 4.2.0→4.1.0 installed, plotly, starlette).

**Sequencing:** canopy harness (#1) lands first; the fix (#2) stacks on it; the ml
doc (#3) references both. Merge upstream-first.

---

## 8. References

**External literature (retrieved into [`../papers/`](../papers/), 2026-06-16):**

- [`nngroup-disabled-buttons.md`](../papers/nngroup-disabled-buttons.md) — Nielsen
  Norman Group: button states, `aria-disabled`, tooltip guidelines, "disable
  sparingly + explain why". (nngroup.com)
- [`w3c-aria-tooltip-and-disabled.md`](../papers/w3c-aria-tooltip-and-disabled.md) —
  W3C WAI-ARIA APG Tooltip pattern + `aria-disabled` vs HTML `disabled`
  focusability; MDN corroboration. (w3.org / MDN)
- [`dash-testing-dash-duo.md`](../papers/dash-testing-dash-duo.md) — Plotly Dash
  testing docs: `dash_duo`/`dash.testing`, Selenium `send_keys` input driving.
  (dash.plotly.com)
- [`react-controlled-input-onchange.md`](../papers/react-controlled-input-onchange.md) —
  React controlled-input `onChange` semantics + native-setter + bubbling-event
  workaround. (react.dev / MDN, + secondary)

**Internal cross-links (not re-retrieved):**

- `JUNIPER_2026-06-15_JUNIPER-CANOPY_AUDIT-AND-HARNESS-PLAN.md` — the approved working plan
  this supersedes.
- `notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (Issues #1–#6),
  `notes/CANOPY_TRAINING_CONTROL_ERROR_SURFACING_DESIGN_2026-06-14.md` — the
  dead-button class taxonomy this audit extends.
- The `JUNIPER_RECURRENCE_*` / LMU / `task_type` / WS-1 corpus in `notes/` and
  `papers/` — the model-selection enhancement's upstream.
