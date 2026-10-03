# Thread Handoff — juniper-canopy A1-iv (iv-3c dataset-ref → start_training, then A1b table + flip-live)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Subject repo**: pcalnon/juniper-canopy (doc home: pcalnon/juniper-ml)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-24
**Purpose**: Continue the **canopy model-selection A1-iv enabler**, picking up where
[`HANDOFF_2026-06-23_canopy-a1-iv-picker-and-deploy.md`](HANDOFF_2026-06-23_canopy-a1-iv-picker-and-deploy.md)
left off. That handoff scoped A1-iv (picker + runtime backend swap) + A1-deploy; **this thread
shipped iv-1, iv-2, A1-deploy GAP-B, defect #8, iv-3a, and iv-3b — six merged PRs** — so the
recurrence/LMU model is now selectable, the backend swaps at runtime, and the sidebar dataset gate
greys incompatible datasets. What remains is **iv-3c** (the last A1a sub-slice: dataset-ref →
start_training), then **iv-4** (A1b facet table), **iv-5** (flip recurrence→live), and **defect
#7**. Use this file as the opening prompt for a fresh thread, per the mandatory thread-handoff
policy.

---

## 0. FIRST — verify live state before any work (repos advance same-day; multiple sessions run)

1. **Read the running record (source of truth)** — full PR-by-PR history + every gotcha:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_canopy_a1_recurrence_integration_2026-06-22.md"
   ```

2. **Confirm canopy `main` + the merged PRs.** When written, canopy `main` = `2122a7d` (#394).

   ```bash
   for pr in 390 391 392 393 394; do gh pr view "$pr" -R pcalnon/juniper-canopy --json state --jq "\"#$pr: \(.state)\""; done
   gh pr view 132 -R pcalnon/juniper-deploy --json state --jq '"deploy #132: \(.state)"'
   ```

3. **The iv-3c worktree already exists, off `2122a7d`, with NO edits** — do NOT re-create it:
   `…/Juniper/worktrees/juniper-canopy--feat--canopy-train-dataset-ref--20260624-1751--2122a7d6`
   (branch `feat/canopy-train-dataset-ref`). Run `gh pr list -R pcalnon/juniper-canopy --state open`
   first (a concurrent session may touch canopy). Re-grep every line number below — they drift.

4. **Design-of-record** (juniper-ml `notes/`):
   - [`JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](../../notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
     — the A1 selection-UI design (§5 surface; D2/D4/D7/D8; A1b/iv-4 = the faceted table).
   - [`JUNIPER_2026-06-23_JUNIPER-CANOPY_A1-III-DASHBOARD-INTEGRATION-SCOPE.md`](../../notes/JUNIPER_2026-06-23_JUNIPER-CANOPY_A1-III-DASHBOARD-INTEGRATION-SCOPE.md)
     — A1-iii (the route-side dataset-ref plumbing iv-3c consumes).

---

## 1. DONE — this thread (6 merged PRs; canopy `main` `2122a7d`)

| Slice | PR | Delivered |
|---|---|---|
| **iv-1** | canopy #390 | Compatibility engine in `model_registry.py` — `compatible()`/`temporal_ok()` predicate + `compatible_models()`/`compatible_datasets()` resolvers (design §4; the D5 correctness guarantee). |
| **A1-deploy GAP-B** | deploy #132 | `RECURRENCE_SERVICE_URL` + canopy `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` wiring (full + demo). The recurrence compose service already existed (WS-7/OUT-4); this closed the consumer-wiring gap. |
| **iv-2** | canopy #391 | Runtime backend swap — `_swap_backend()` + `POST /api/model/select` (`main.py`); shared `_seed_training_state()`; `current_nn_model` / `_resolved_service_url` globals. Re-create, not multiplex (D5). |
| **defect #8** | canopy #392 | De-flaked `test_train_after_reset` (break-on-completion within the two-boolean contract). |
| **iv-3a** | canopy #393 | Sidebar model picker (`nn-model-dropdown` + `model-selection-store` + summary) → POSTs `/api/model/select` + mirrors `execution` into `model-class-store`. `model_options()` / `DEFAULT_MODEL_KEY`. |
| **iv-3b** | canopy #394 | 3-D `equities_seq` `DatasetTypeSpec` seed (so `compatible_datasets(recurrence)` is non-empty) + `dataset_reason()` / `gated_dataset_options()` + the sidebar dataset-gate callback (disable-with-reason + conflict-snap, D5). `model-selection-store` reconciled to hold the model key. |

**Net:** recurrence is selectable (picker → backend swap), and the dataset dropdown greys
incompatible datasets per the selected model. **It is not yet trainable from the UI** — the start
button never forwards the dataset-ref. That is iv-3c.

---

## 2. Remaining work

### iv-3c — dataset-ref → start_training (the LAST A1a sub-slice; PRIMARY)

**Route-side is DONE** (A1-iii-a): both REST `/api/train/start` (`main.py` `_TrainStartBody`
@~2850, `_recurrence_start_kwargs` @639, applied @2878) and WS `/ws/control` start (@755) accept
`{dataset:{generator/name/dataset_id, params, split}, d, theta, ridge}` and forward it to
recurrence `start_training`. **The frontend must SUPPLY the body.**

**Start flow = Phase-D dual-transport** (`dashboard_manager.py`):

- clientside WS JS `PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS` @~109 (when
  `settings.enable_ws_control_buttons` — **NON-default**) → `window.cascorControlWS.send()` → WS
  `/ws/control`.
- server-side `_handle_training_buttons_handler` @~4986 (**DEFAULT**) → `training-control-action`
  store → dispatch callback (`Input("training-control-action", "data")` @~3338) → REST
  `/api/train/start`.

**iv-3c — Paul's decision: wire BOTH transports:**

- When `model-class-store == "one_shot"`, read the `nn-dataset-type-dropdown` value (the generator,
  e.g. `equities_seq`) + dataset params (`nn-dataset-elements-input`, `nn-dataset-noise-input`) as
  callback `State`, and include the dataset-ref body on the start POST (REST path).
- Thread the same ref into the **clientside WS JS** so the WS-control transport carries it in the
  `/ws/control` start message.
- **No LMU hyperparameter UI inputs** (d/theta/ridge) exist → omit them; the recurrence service
  defaults them. (Adding `d`/`theta`/`ridge` inputs is optional polish.)
- Gates: control-graph lint (no new actionable control, but verify); the **L2 behavioral manifest**
  likely needs an entry (the start now has a recurrence backend round-trip carrying a body). Put
  TestClient / handler tests in `src/tests/regression/`.

After iv-3c, **A1a is COMPLETE** (model → gated dataset → one-shot fit, end-to-end).

### iv-4 — A1b: the dedicated faceted model-table surface

The full-width searchable/faceted model table (design D7/§5.2; OQ-1 lean = a **Models tab**; OQ-4 =
`dash_table.DataTable` vs custom). Row-per-model with facets (category / status / tags / task-fit),
search across label + family + category + tags, lifecycle-status presentation (D8), compatibility
reason cells. **Upgrades / replaces the iv-3a minimal sidebar picker** (keep the sidebar
"Model: X ▸ change" summary that opens the surface). The reverse gate (dataset → models greying)
belongs here.

### iv-5 — flip recurrence.status coming_soon → live

One-line `model_registry.py` edit once recurrence is genuinely selectable + trainable. **Gate on the
recurrence service being up** (A1-deploy stack, Paul-driven) **OR** ship selectable against a
configured `recurrence_service_url`. Update the registry tests that assert `coming_soon`.

### Defect #7 (separate PR; non-blocking)

Scope the over-broad `/v1`-prefix guard test
(`src/tests/unit/backend/test_cascor_service_adapter_v1_prefix_regression.py`) to cascor-client-based
adapters — it flags ANY `_request` / `_get` / … under `src/backend/` with a `/v1/`-prefixed path
(it bit A1-i; worked around by naming the recurrence adapter helper `_call`).

---

## 3. Key anchors (re-grep — line numbers drift)

- **iv-3c start flow** (`dashboard_manager.py`): `_setup_button_action_callbacks` @~3223; the
  WS-vs-server branch @~3231; clientside JS `PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS` @~109; server
  handler `_handle_training_buttons_handler` @~4986; `training-control-action` dispatch @~3338; the
  cold-swap REST `/api/train/start` @~3834 (a DIFFERENT flow — the live-dataset-swap restart banner).
  Dataset `State`: `nn-dataset-type-dropdown` value (@~1140 layout, now gated), `nn-dataset-elements-input`,
  `nn-dataset-noise-input`. `model-class-store` (the one_shot flag) hydrated by
  `_setup_model_class_callbacks` @~1989.
- **route-side** (`main.py`): `_TrainStartBody` @~2850; `_recurrence_start_kwargs` @639 (used at WS
  `/ws/control` @755 + REST `/api/train/start` @2878).
- **registry** (`model_registry.py`): `MODELS` (cascor `live` / recurrence `coming_soon`),
  `DATASET_TYPES` (5×2-D + `equities_seq` 3-D), `compatible` / `compatible_datasets` /
  `gated_dataset_options` / `dataset_reason` / `model_options` / `DEFAULT_MODEL_KEY`.

---

## 4. CI / test gotchas (hard-won this thread)

- **Run the UI suite SEQUENTIALLY — never concurrent with the coverage gate.** Running both at once
  flakes/hangs `test_train_after_reset` (a demo-timing race under load); this cost several cycles.
  CI's isolated UI Sub-suite job passes. Local UI:
  `pytest src/tests/ui --override-ini=addopts= -p no:cacheprovider` (~6 min; chromium installed).
- **Control-graph lint** (`test_control_graph_lint.py`): every ACTIONABLE control
  (Dropdown / Button / Input / …) must be reachable by a callback Input (or `KNOWN_ORPHANS`).
- **`DashboardManager({})` construction** (in a regression test) validates that the new layout +
  callbacks register cleanly — it catches `allow_duplicate` duplicate-output conflicts up front.
  Delegate callback bodies to testable `_*_handler` methods (e.g. `_select_model_handler`,
  `_gate_dataset_options_handler`) and unit-test those.
- **Coverage ≥80%** (unit+regression job):
  `pytest -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ --cov=src --cov-report=term-missing --cov-fail-under=80`.
  The default `addopts` has NO `--cov`; add it explicitly.
- **Black local-fails on py3.12** for `dashboard_manager.py` (it parses py3.14 syntax) — a benign
  one-time reformat, stable on re-run; CI (py3.14) passes.
- **Touching `main.py` triggers a full mypy re-check** → can surface PRE-EXISTING false-positives
  (e.g. `list(dict.get())` `call-overload`); a targeted `# type: ignore[...]` is the
  scope-respecting fix — do not refactor unrelated lines.
- Panel-snapshot (`test_panel_layout_snapshots.py`) hashes only `metrics_panel` + `dataset_plotter`
  `get_layout()` — sidebar edits don't trip it. `test_sidebar_width` greps `dashboard_manager.py`
  for multi-line `dbc.Tab`s.

---

## 5. Conventions

- **One PR per slice; Paul merges between.** 2-gate worktree sweep: Paul says merged AND
  `gh pr view` shows `MERGED`. Sweep the iv-3c worktree only after its PR merges.
- Tests under the **JuniperCanopy1** conda env (Python 3.13). Pre-commit:
  black / isort / flake8 ×2 / mypy / bandit / async-route-audit / doc-links (line length 512).
- Commit messages end with the `Co-Authored-By` + `Claude-Session` trailers; PR bodies end with the
  Generated-with-Claude-Code footer.
- Worktrees centralized in `…/Juniper/worktrees/`, off fresh `origin/main`.

---

## 6. Git status at handoff

- canopy `main` = `2122a7d` (#394); all 6 PRs merged, their worktrees swept.
- **iv-3c worktree exists, no edits** (see §0.3) — the starting point.
- juniper-ml `main` ≈ `54e5d83` (advanced by a concurrent session, #530). This handoff doc lands on
  its own juniper-ml `docs/handoff-canopy-a1-iv-3c` branch (open PR).
- No uncommitted work elsewhere; no lingering background tasks.
