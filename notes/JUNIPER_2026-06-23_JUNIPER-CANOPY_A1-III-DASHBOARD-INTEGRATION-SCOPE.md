# Juniper-Canopy — A1-iii Dashboard-Integration Scope (one-shot execution path)

**Project**: juniper-canopy (subject) / juniper-ml (doc home)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-23
**Status**: Scoping / sub-split ratified (design-first; pre-implementation)

> Scopes **A1-iii** — wiring the recurrence (LMU) one-shot model into canopy's live
> dashboard. Builds on **A1-i** (`RecurrenceServiceAdapter`, canopy #383/#384) and **A1-ii**
> (`RecurrenceBackend` + `create_backend(nn_model=…)` routing, canopy #385). Design-of-record
> for the execution-paradigm bridge:
> [`JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md`](JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md)
> (decisions **D1-A / D5 / D6**) and the selection UI
> [`JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`](JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md).
> Grounded by a three-track read of `main.py`, the frontend panels, and the training-trigger
> flow (2026-06-23); key `file:line` anchors throughout.

---

## 1. Where A1 stands

| Slice | State |
|---|---|
| A1-i — `RecurrenceServiceAdapter` (sync httpx; `train` + `training_status`) + settings | **DONE** (canopy #383 + #384 fix; on `main`) |
| A1-ii — `RecurrenceBackend` (one-shot `BackendProtocol` wrapper) + `create_backend(nn_model=)` routing + `get_model_spec`/`RECURRENCE_PROVIDER` | **DONE** (canopy #385; on `main`) |
| **A1-iii — dashboard integration (this doc)** | **scoped here** |
| A1-iv — model-selection UI + runtime backend swap (`nn_model` mirror) | later |
| A1-deploy — juniper-deploy recurrence service | Paul-gated, parallel |

The backend is built and routable. The gap is entirely **dashboard-side**: the live route
layer mis-buckets a third `backend_type`, no model-class panel-visibility mechanism exists,
and the training trigger never forwards a dataset reference.

---

## 2. The three findings

### 2.1 Routes are mostly fenced, but five sites mis-bucket `"recurrence"`

`RecurrenceBackend.backend_type == "recurrence"` is a **third** value (`main.py` only knew
`"demo"` / `"service"`). It stores `self._adapter` (a `RecurrenceServiceAdapter`, **not** a
`CascorServiceAdapter`) and has **no** `self._demo`. Of ~20 `backend_type` sites:

- The cascade-only routes (remote-workers connect/start/stop, replay/resume/retrain via
  `_require_service_adapter`, network mutation) are **correctly fenced** by `== "service"`
  guards → clean **501/503** for recurrence. No work.
- `RecurrenceBackend` already returns `None` for `get_network_topology` / `get_raw_topology`
  / `get_decision_boundary`, so `/api/topology`, `/api/topology/raw`, `/api/decision_boundary`
  **503 cleanly** (verified — not a crash). No work beyond a regression test.
- The **problems** are `!= "service"` / bare-`hasattr(_adapter)` mis-buckets:

| Line | Site | Bug for recurrence | Fix |
|---|---|---|---|
| **1537** | `/api/v1/snapshots` | `(… or not snapshots) and backend_type != "service"` → recurrence serves **fabricated demo-mock snapshots** ("Demo mode: showing simulated snapshots") | Gate the mock path on `== "demo"`, not `!= "service"` |
| **1813**, **2024** | snapshot create / restore | bare `hasattr(backend, "_adapter")` (no type check) → recurrence's adapter slips to an h5py fallback that writes a meaningless cascade-shaped snapshot; if the recurrence adapter ever grows a like-named `save_snapshot`/`load_snapshot` it'd be invoked with cascor semantics | Gate the adapter call on `backend_type == "service"` (or 501 for recurrence) |
| **2639**, **2672** | `/api/v1/workers/stats` , `/workers/list` | `else` branch fabricates **synthetic demo workers** (2 fake workers w/ health scores) for any non-service backend | Explicit recurrence branch → empty (`total: 0` / `workers: []`) |
| **237** | lifespan state sync | only `elif backend_type == "service":` seeds `training_state` + registers `set_state_update_callback` → recurrence boots with **no state sync**, so `idle→training→trained` transitions + regression metrics never propagate to `training_state`/WS clients | Add a `recurrence` branch that seeds regression-shaped state (and decides on a state-update path) |

A sixth, softer item: the `/ws/control` dispatch (`main.py:680-701`, `757-798`) blindly calls
`pause_training` / `resume_training`; `RecurrenceBackend` returns `{ok: False, message: …}`
(clean rejection, not a crash), but the **frontend should hide pause/resume** for a one-shot
model (A1-iii-b).

### 2.2 No model-class panel-visibility mechanism exists — it must be built

The right-side viz area is a single `dbc.Tabs` (`id="visualization-tabs"`,
`dashboard_manager.py:1559-1639`); the only existing visibility driver is `active_tab`. The
**five cascade-only tabs** must be suppressed for a one-shot model:

| Cascade tab | `dbc.Tab` (dashboard_manager.py) | inner-Div id? |
|---|---|---|
| Candidate Metrics | 1566-1570 | none |
| Network Topology | 1571-1575 | none |
| Network Evolution | 1576-1580 | none |
| Decision Boundary | 1581-1585 | none |
| Workers | 1591-1595 | none |

Because the inner Divs have no `id`, suppression happens at the **`dbc.Tab` level** (add `id`s
to those five tabs + a callback toggling `style`/membership, driven by a model-class flag).
The same flag suppresses the status-bar **hidden-units** segment
(`_build_unified_status_bar_content`, `dashboard_manager.py:4449-4516`) and the metrics panel's
cascade cards (Hidden Units / Learning Rate / progress bars).

The **metrics panel is hard-coded for classification** (`metrics_panel.py`): accuracy card
value (`:1285`) / format `:.2%` (`:1291`) / label "Accuracy" (`:419`); `_create_accuracy_plot`
(`:1684-1760`) with yaxis range `[0, 1.0]` (`:1751`) and val-overlay (`:1724`). `RecurrenceBackend`
already emits `r2/mse/rmse/mae/loss` via `get_metrics`, but the panel never reads them, and
`MetricsResult` (`backend/protocol.py:76-92`) declares **no regression keys**. The per-epoch
curve degenerates to a single point for a one-shot fit (`get_metrics_history` returns one
terminal entry).

Transport already in place: `GET /api/train/status` (`main.py:2846`) returns
`{"backend": backend.backend_type, **get_status()}`, and `get_status` emits
`phase ∈ {idle, fitting, complete, error}` — enough to drive a flag + a spinner without new
infrastructure.

### 2.3 The training trigger never forwards a dataset reference

`start-button` (`dashboard_manager.py:785`) → WS `/ws/control` `start` (`main.py:687-688`) or
REST `/api/train/start` (`main.py:2766-2780`) → `backend.start_training(reset=<bool>)` —
**only `reset`**. But `RecurrenceBackend.start_training` *requires* a dataset ref
(`generator`/`name`/`dataset_id` + `params`/`split`) + `d/theta/ridge` and returns
`ok=False, error="no dataset reference…"` otherwise. Today the dataset is staged out-of-band
(`apply-dataset-button` → `/api/stage_dataset` → cascor `stage_dataset`, consumed on the next
`start_training(reset=True)`); `RecurrenceBackend` has no `stage_dataset`. The recurrence-
compatible dataset choice currently lives on the **viz surface** (`dataset-plotter-dataset-selector`
generator + `dataset-plotter-split-selector`), unwired to training.

⇒ A recurrence fit through today's button fails immediately. A1-iii must **forward a
dataset-ref + hyperparameters to `start_training`**.

---

## 3. Ratified sub-split (two PRs)

### A1-iii-a — route correctness + dataset-ref plumbing (backend/route; no UI)

1. **Route mis-bucket fixes** (§2.1): L1537 (mock-snapshot gate → `== "demo"`),
   L1813/L2024 (adapter snapshot calls gated on `== "service"`), L2639/L2672 (recurrence →
   empty worker data), L237 (seed recurrence `training_state` + state-update path).
2. **Dataset-ref plumbing**: widen `/api/train/start` (and the `/ws/control` `start` branch) to
   accept an optional **request body** carrying a dataset ref (`generator`/`name`/`dataset_id`,
   `params`, `split`) + `d`/`theta`/`ridge`, and forward it as `start_training(**kwargs)`.
   **Backward-compatible** — cascor's `start_training` ignores the extra kwargs; recurrence
   requires them.
3. **Regression test** asserting topology / raw-topology / decision-boundary 503 cleanly for a
   recurrence backend (lock in the "returns None" contract).

Testable headless via route/integration tests with an **injected** recurrence backend — no UI,
no live picker. Makes a recurrence backend *safe and runnable* in the app.

### A1-iii-b — one-shot UI rendering (the D1-A / D6 core)

1. **`ModelSpec.execution` field** (`"live" | "one_shot"`) — `cascor` → `live`, `recurrence` →
   `one_shot`. The canonical driver (per D1-A); surfaced to the frontend as a `dcc.Store` flag
   sourced from `/api/train/status` (`backend_type`) + the registry.
2. **Cascade-panel suppression**: hide the five cascade `dbc.Tab`s (add `id`s) + the status-bar
   hidden-units segment + the metrics panel's cascade cards, via the flag. Hide pause/resume
   controls for one-shot.
3. **Metrics accuracy → regression switch**: parametrize the metrics card + `_create_accuracy_plot`
   (label / value / format / yaxis range / val-overlay) on the metric set; add `r2`/`mse`/`rmse`/
   `mae` keys to `MetricsResult`.
4. **Minimal one-shot result view**: submit → spinner (poll `/api/train/status` `phase`) → final
   **regression-metrics** card. Per the D1-A guardrail: minimal metrics view first, enrich later.

Per-canopy-PR gates: L1 control-graph lint + the L2 behavioral manifest (controls with a backend
round-trip) + panel-snapshot regen if `get_layout()` changes.

### Boundary — what stays in A1-iv (not A1-iii)

The **model-selection surface** (the dedicated picker) and the **runtime backend swap** (the
`nn_model` mirror that re-creates the startup-fixed global `backend` when the user selects a
model) are **A1-iv**. A1-iii is built + tested by *injecting/forcing* a recurrence backend; A1-iv
makes it user-reachable. (The global `backend` is a process singleton set once in the lifespan,
`main.py:189/217`; runtime swap is new A1-iv infrastructure.)

---

## 4. Design decisions

- **D-iii-1 — drive suppression from a new `ModelSpec.execution` field**, not by overloading
  `category` / `backend_type`. `category` (`feedforward`/`ts_established`/`ts_growth`) and the
  runtime `backend_type` could both work, but a dedicated `execution = "live" | "one_shot"` axis
  is the D1-A design-of-record, is model-class-agnostic (future one-shot models inherit it), and
  keeps `status="live"` (trainability) cleanly separate from execution paradigm.
- **D-iii-2 — carry the dataset ref as a request body** on `/api/train/start` (+ the WS `start`
  branch), not via the cascor `stage_dataset` pending-dataset pattern. The recurrence service
  fetches the dataset itself, so the ref is small (`generator`/`name`/`dataset_id` + `params` +
  `split`); a one-shot fit shouldn't borrow cascor's two-step stage-then-consume flow.
- **D-iii-3 — minimal result view first.** A regression-metrics card (r2 / mse / rmse / mae +
  loss) driven by the spinner→complete phase; defer richer forecasting/plots.
- **D-iii-4 — A1-iii-a is headless.** No UI changes; everything is route-layer + tested by
  injecting a recurrence backend, so the risky live-route edits land and bake before the UI slice.

---

## 5. Key anchors

- **main.py route audit** (full table in the scoping thread): fixes at `main.py:237`, `1537`,
  `1813`, `2024`, `2639`, `2672`; correctly-fenced `== "service"` guards elsewhere; training
  trigger `main.py:687-688` (WS) / `2766-2780` (REST) → `start_training(reset=…)`.
- **panels**: `dashboard_manager.py:1559-1639` (`visualization-tabs`); cascade tabs `1566-1595`;
  status bar `4449-4516`. **metrics**: `metrics_panel.py:419, 1285, 1291, 1684-1760, 1724`;
  `backend/protocol.py:76-92` (`MetricsResult`).
- **trigger / selection / dataset**: `dashboard_manager.py:785` (`start-button`), `3030`
  (button callbacks), `3549-3596` (`apply_dataset`); `dataset_plotter.py` (`dataset-plotter-*`
  generator/split/load); `model_registry.py` (`ModelSpec`, `get_model_spec`, `RECURRENCE_PROVIDER`);
  `backend/recurrence_backend.py:94-95, 125-151` (`start_training` keys).

**Cross-links**: [`JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md`](JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md)
(D1-A/D5/D6); [`JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`](JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md)
(A0/A1 UI). canopy #368 (model-selection tracker); #383/#384/#385 (A1-i/A1-ii).
