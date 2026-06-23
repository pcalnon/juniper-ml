# Thread Handoff — juniper-canopy A1-iv (model picker + runtime backend swap) & A1-deploy

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Subject repo**: pcalnon/juniper-canopy (doc home: pcalnon/juniper-ml)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-23
**Purpose**: Continue the **canopy model-selection A1 enabler**, picking up where
[`HANDOFF_2026-06-21_canopy-a1-recurrence-training-integration.md`](HANDOFF_2026-06-21_canopy-a1-recurrence-training-integration.md)
left off. That handoff started the build; this thread shipped **A1-i, A1-ii, A1-iii-a,
A1-iii-b1, and A1-iii-b2** — the recurrence/LMU model is now end-to-end integrated into the
dashboard *backend + rendering*, but is **not yet user-selectable live**. What remains is
**A1-iv** (the model picker UI + the runtime backend swap) and **A1-deploy** (Paul-gated).
Use this file as the opening prompt for a fresh thread, per the mandatory thread-handoff policy.

---

## 0. FIRST — verify live state before any work (repos advance same-day; multiple sessions run)

1. **Read the running record (source of truth)** — full PR-by-PR history + every gotcha:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_canopy_a1_recurrence_integration_2026-06-22.md"
   ```

2. **Confirm A1-iii-b2 (#389) merged, then sweep its worktree.** When this handoff was written,
   **#389 was OPEN, green, MERGEABLE (not merged)** — A1-i/A1-ii/A1-iii-a/A1-iii-b1 (PRs
   #383/#384, #385, #386, #388) are already on `main`; b2 is the only one in flight.

   ```bash
   for pr in 383 384 385 386 388 389; do gh pr view "$pr" -R pcalnon/juniper-canopy --json state --jq "\"#$pr: \(.state)\""; done
   ```

   Worktree to remove once **#389** shows `MERGED` (2-gate cleanup: Paul says merged AND `gh`
   confirms): `…/Juniper/worktrees/juniper-canopy--feat--canopy-recurrence-metrics--*`
   (`git -C <canopy> worktree remove --force <dir>; git branch -D feat/canopy-recurrence-metrics;
   git push origin --delete feat/canopy-recurrence-metrics; git worktree prune`). Also this
   handoff's own worktree `juniper-ml--docs--handoff-canopy-a1-iv-deploy--*` once its PR merges.

3. **Read the design-of-record docs (in juniper-ml `notes/`):**
   - [`JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md`](../../notes/JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md)
     — **the A1 selection-UI design (A1-iv's spec).** Paul chose a **DEDICATED full-width
     model-surface table** (not a sidebar dropdown) for 10–20+ models+variants; multi-axis
     capability predicate (ndim + temporal; task_type inert); label-suffix reasons on greyed
     options; swappable conflict policy; inline ✕; status-enum registry.
   - [`JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md`](../../notes/JUNIPER_CANOPY_A1_III_DASHBOARD_INTEGRATION_SCOPE_2026-06-23.md)
     — the A1-iii scope; its "Boundary" section defines exactly what was deferred to A1-iv.
   - [`JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md`](../../notes/JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md)
     — decisions D1-A/D5/D6 (the execution-paradigm bridge already built).

4. **Collision-check + create your worktree off FRESH `origin/main`** (never trust the local
   tree or this doc's line numbers — re-grep). `gh pr list -R pcalnon/juniper-canopy --state open`
   first (a concurrent session may be touching canopy).

---

## 1. DONE this thread (all CI-green; #389 pending merge)

| Slice | PR(s) | Delivered (all on `main` except b2) |
|---|---|---|
| **A1-i** adapter + settings | #383 (+ #384 fix) | `RecurrenceServiceAdapter` (`src/backend/recurrence_service_adapter.py`) — sync httpx client, `train()`+`training_status()`, `X-API-Key`, typed errors. `Settings.recurrence_service_url` + `recurrence_api_key` (prefixed > shared, `_FILE`). |
| **A1-ii** routing | #385 | `RecurrenceBackend` (`src/backend/recurrence_backend.py`) — `BackendProtocol` one-shot wrapper, daemon-thread fit, binary status, stubs. `create_backend(nn_model=…)` provider routing (`src/backend/__init__.py`); `model_registry.get_model_spec()` + `RECURRENCE_PROVIDER`. |
| **A1-iii-a** routes + plumbing | #386 | Fixed 5 `main.py` `backend_type` mis-buckets (snapshots/workers/lifespan); **`/api/train/start` optional body + `/ws/control` start** forward a dataset-ref + `d/theta/ridge` via `_recurrence_start_kwargs` (recurrence-gated; cascor/demo unchanged). |
| **A1-iii-b1** suppression | #388 | The **execution flag**: `ModelSpec.execution` + `BackendProtocol.execution` property on all 3 backends → `/api/train/status` returns `execution`. `model-class-store` (`dcc.Store`) hydrated on mount → hides 5 cascade `dbc.Tab`s + the status-bar Iteration segment for one-shot. |
| **A1-iii-b2** result view | **#389 (OPEN-green)** | `metrics_panel.py` `render_model_class_metrics` callback hides the classification cards/plots and shows a **regression result card** (R²/RMSE/MSE/MAE/Loss + spinner) for one-shot; `MetricsResult` += `r2/mse/rmse/mae`. **Dedicated card (D-iii-3), not in-place** — sidesteps the flat-vs-nested metrics-envelope mismatch (no backend get_metrics shape change). |

**Net:** a recurrence backend is constructible, routable, route-correct, fit-runnable, and
renders its regression result + suppresses cascade panels. **It is NOT reachable from the live
dashboard** — the global `backend` is a startup-fixed singleton and there is no model picker.

---

## 2. Remaining work

### A1-iv — model picker UI + runtime backend swap (PRIMARY; this is the big one)

Three coupled pieces (consider sub-splitting; Paul approves splits — propose a cadence first,
like the b1/b2 split this thread):

1. **The model-selection surface** — the dedicated full-width model table from
   `JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` (A1): a row per model
   (`model_registry.MODELS`), capability predicate gating (recurrence needs `input_ndim={3}`
   + `requires_dt` 3-D datasets; greyed with a label-suffix reason when incompatible with the
   selected dataset), `status`-enum presentation (`live`/`coming_soon`/…), inline ✕, the
   `nn_model` selection mirrored to a store. **May sub-split A1a (sidebar gate + summary +
   minimal picker) → A1b (full facet table)** per the design.

2. **The runtime backend swap (the `nn_model` mirror).** Today `backend` is a process-global
   singleton (`src/main.py:171` `global backend`; set ONCE in lifespan at `main.py:189`
   `create_backend(service_url=…)` / `:217` `create_backend(demo_mode=True)`). `create_backend`
   ALREADY accepts `nn_model=` and routes a recurrence model → `RecurrenceBackend` (A1-ii), but
   **nothing calls it with `nn_model` outside tests**. A1-iv must add a mechanism to **re-create
   the global backend** when the user selects a model (shut down the old, `create_backend(
   nn_model=<selected>)`, `await initialize()`, re-seed `training_state`). The lifespan already
   has a `recurrence` `training_state` branch (A1-iii-a, `main.py:~237`). **Decide: full
   re-create vs a multiplexing backend** (the enabler doc D5 says no multiplexer needed for two
   models — favour re-create).

3. **Wire the dataset-ref from the UI into `start_training`.** A1-iii-a built the *route-side*
   plumbing (the `/api/train/start` body + `/ws/control` forwarding); A1-iv must **supply the
   ref**. The recurrence-compatible dataset choice lives on the viz surface
   (`dataset-plotter-dataset-selector` generator + `dataset-plotter-split-selector`,
   `src/frontend/components/dataset_plotter.py`), currently **unwired to training**. Read those
   as callback `State`s and POST `{dataset:{generator,params,split}, d, theta, ridge}` to
   `/api/train/start` for a one-shot model.

4. **Flip `recurrence.status` `coming_soon` → `live`** in `model_registry.py` once the model is
   genuinely selectable+trainable (enabler doc Phase 2). Gate on A1-deploy being up for the live
   path, OR ship selectable-against-a-configured-`recurrence_service_url`.

### A1-deploy — juniper-deploy recurrence service (PAUL-GATED; the live e2e gate)

Standard service add (enabler doc §3.2): in `juniper-deploy/docker-compose.yml` clone the
`juniper-cascor` block — `build.context: ../juniper-recurrence/juniper-recurrence` (the
Dockerfile is DONE, recurrence #21), `ports: 8211:8210`, `JUNIPER_RECURRENCE_*` env, outbound
`JUNIPER_DATA_URL`, new secret `juniper_recurrence_api_keys` (+ `./secrets/` + `./secrets.example/`
+ `make prepare-secrets`), `/v1/health` healthcheck, prometheus scrape job, `.env.example` vars.
**Deploy approvals are Paul's** — drive to the gate, then hand off. Can land independently/parallel.

### Follow-ups (separate PRs; not blocking A1-iv)

- **Over-broad v1-prefix guard** — `src/tests/unit/backend/test_cascor_service_adapter_v1_prefix_regression.py`
  flags ANY `_request`/`_get`/… under `src/backend/` with a `/v1/`-prefixed path; it's
  cascor-client-specific but bites any raw-httpx adapter (cost A1-i a CI cycle; worked around by
  naming the recurrence adapter helper `_call`). Scope it to cascor-client-based adapters.
- **Flaky `test_train_after_reset`** (`src/tests/ui/`) — a demo-timing race (clicks Start then
  polls `is_running=True` via `/api/status`; the demo completes before it's caught on fast CI
  runners). Unrelated to recurrence; make it robust (accept `is_running OR completed`).
- **Predict / cross-val surface (A1-v, deferred)** — `/v1/predict` + `/v1/crossval` were left out
  of the A1 first cut (enabler OQ-2: train+status only). LMU's value is forecasting, so a
  predict-from-dashboard view is a plausible next ask.

---

## 3. Key architecture & file anchors (re-grep — line numbers drift)

- **Backend factory / swap point:** `src/backend/__init__.py` `create_backend(*, service_url,
  demo_mode, nn_model)` — `nn_model` → `_try_create_recurrence_backend` → `RecurrenceBackend`.
  Global singleton: `src/main.py:171` / `:189` / `:217` / `:386`.
- **The execution flag (b1):** `model_registry.ModelSpec.execution` (`"live"|"one_shot"`),
  `backend.execution` property (all 3 backends), `GET /api/train/status` returns it; frontend
  `model-class-store` (`dcc.Store` in `dashboard_manager.py`) hydrated from it on mount
  (`params-init-interval`). A1-iv's picker writes the selected model; the swap re-hydrates.
- **Registry:** `src/model_registry.py` — `MODELS` (cascor `in-process`/`live`; recurrence
  `juniper-recurrence`/`coming_soon`/`input_ndim={3}`/`requires_dt`/`execution="one_shot"`),
  `get_model_spec(key)`, `RECURRENCE_PROVIDER`, `dataset_type_options()`, `DATASET_TYPES`.
- **Dataset choice (unwired to training):** `src/frontend/components/dataset_plotter.py`
  (`dataset-plotter-dataset-selector`, `dataset-plotter-split-selector`).
- **Tabs:** `dashboard_manager._all_visualization_tabs()` + `_visible_tabs()` (b1).

---

## 4. CI / test gotchas (HARD-WON this thread — read before pushing)

- **The UI / Playwright suite is a SEPARATE CI job**, NOT in the `unit + regression` coverage
  scope. The full local `pytest src/tests/unit src/tests/regression` does **not** run it.
  **Run it locally** (chromium is installed): `pytest src/tests/ui --override-ini=addopts=`
  (~6 min). b1 went red 3× partly because this wasn't run up front; b2 was first-try green after
  running it locally.
- **Control-graph lint** (`src/tests/unit/test_control_graph_lint.py`) — flags any **ACTIONABLE**
  control (Button / Dropdown / Select / Input / RadioItems / Checklist / Switch / Slider / Upload)
  left unreachable by every callback. **A1-iv's picker IS actionable → it MUST be wired to a
  callback Input (or added to `KNOWN_ORPHANS` with cause).** `dcc.Store`/`dbc.Tab`/`Span`/`Div`
  are ignored. This is THE gate for A1-iv.
- **L2 behavioral manifest** (`src/tests/ui_contract/control_manifest.py`) — only for controls
  with a backend round-trip (a POST). The picker→backend-swap likely needs an entry.
- **Panel snapshot** (`src/tests/regression/test_panel_layout_snapshots.py`) hashes only
  `metrics_panel` + `dataset_plotter` `get_layout()`. If A1-iv edits either, regen:
  `rm src/tests/regression/snapshots/<panel>.txt && pytest …test_panel_layout_snapshots.py -m regression`
  (writes baseline + skips) → commit.
- **`test_sidebar_width._parse_tab_labels`** GREPS `dashboard_manager.py` source for
  `label="X",\n  tab_id="y"` on SEPARATE lines → keep `dbc.Tab`s multi-line (a one-liner
  refactor broke it this thread).
- **`active_tab` invariant** (`test_single_mount_time_active_tab_restore`): exactly **2**
  `Output("visualization-tabs", "active_tab")` writers (Store-restore + tutorial). Don't add a 3rd.
- **Black** on `dashboard_manager.py` fails the LOCAL pre-commit safety-check (py3.12 can't parse
  the file's py3.14 syntax) — it's a one-time reformat, stable on re-run; CI (py3.14) passes.
- **CodeQL findings are real** (not infra) — the `CodeQL` check (separate from `Analyze (python)`)
  fails fast on error-level alerts. `try/except ImportError: pytest.skip` → use
  `pytest.importorskip` (caught this thread). 4s "fail" ≠ infra; check the alerts.
- **Coverage gate 80%** in the unit+regression job. Put TestClient route tests in
  `src/tests/regression/` so they count toward coverage. Construct `DashboardManager({})` (cheap)
  to unit-test panel methods; route tests use a module-scoped `with TestClient(main.app)` +
  function-scoped `monkeypatch.setattr(main, "backend", RecurrenceBackend(fake))`.

---

## 5. Conventions

- **Tests** run under the **JuniperCanopy1** conda env (Python 3.13). Per canopy PR: control-graph
  lint green; snapshot regen if a hashed panel's `get_layout()` changes; run the UI suite locally.
- **Pre-commit**: black / isort / flake8 / mypy / bandit / async-route audit / doc-links (line 512).
- **Worktrees**: centralized `…/Juniper/worktrees/`, off fresh `origin/main`. **2-gate cleanup**:
  only remove after Paul says THAT PR is merged AND `gh pr view` shows `MERGED`.
- **One clean commit per PR** (squash-merge ships the first commit only). Cadence: one PR per
  sub-slice, await Paul's merge between slices.
- **Run the full `unit + regression` scope WITH `--cov` before committing**, AND the UI suite —
  both CI-gap lessons of this thread.

---

## 6. Git status at handoff

- canopy `main`: A1-i/A1-ii/A1-iii-a/A1-iii-b1 merged (HEAD around #388 `451b822`); **#389 (b2)
  OPEN-green-MERGEABLE** — merge it first, then sweep its worktree
  `feat/canopy-recurrence-metrics`.
- No other canopy work in flight from this thread; no uncommitted edits.
- This handoff lands on its own juniper-ml `docs/handoff-canopy-a1-iv-deploy` branch (open PR).
