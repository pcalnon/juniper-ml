# Thread Handoff — juniper-canopy A1b-1 (model-selection modal surface)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Subject repo**: pcalnon/juniper-canopy (doc home: pcalnon/juniper-ml)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-25
**Type**: Thread-handoff prompt (continue in a fresh thread)
**Origin**: Completion of **A1-iv-3c** (one-shot Start dataset-ref → `start_training`; canopy
#395 MERGED, which completes **A1a** end-to-end) + ratification of the **A1b** design (the OQ-1 /
OQ-4 spike decisions). This hands off **A1b-1**, the first of two A1b slices.
**Supersedes**: [`HANDOFF_2026-06-23_canopy-a1-iv-picker-and-deploy.md`](HANDOFF_2026-06-23_canopy-a1-iv-picker-and-deploy.md)
(#522) — iv-3c is now done; A1a is complete.

---

## 0. FIRST — verify live state before any work (repos advance same-day; multiple sessions run)

1. **Confirm iv-3c merged + canopy `main`.** When written, canopy `main` = `f464272` (#395 squash).

   ```bash
   gh pr view 395 -R pcalnon/juniper-canopy --json state --jq .state          # MERGED
   MAIN=/home/pcalnon/Development/python/Juniper/juniper-canopy
   git -C "$MAIN" fetch origin && git -C "$MAIN" rev-parse --short origin/main # f464272
   gh pr list -R pcalnon/juniper-canopy --state open                          # concurrent sessions?
   ```

2. **Read the running record (source of truth)** — the **"A1b DESIGN RATIFIED 2026-06-25"** block
   has every decision, the insulation insight, and the `model_reason` note:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_canopy_a1_recurrence_integration_2026-06-22.md"
   ```

3. **The A1b-1 worktree already exists, off `f464272`, with NO edits** — do NOT recreate it:
   `…/Juniper/worktrees/juniper-canopy--feat--canopy-model-table--20260625-0027--f4642729`
   (branch `feat/canopy-model-table`). Re-grep every line number below — they drift.

4. **Design-of-record** (binding; do not relitigate):
   [`notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`](../../notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md)
   — §5 surfaces, D7 (dedicated full-width surface), D8 (lifecycle), §5.2 (the model table),
   §5.3 (the bidirectional gate), §5.7 (gated models), §5.8 (degenerate states).

---

## 1. DONE — leading into this handoff

- **A1a COMPLETE** (model → backend swap → gated dataset → one-shot fit, end-to-end): iv-1 / iv-2 /
  iv-3a / iv-3b (canopy #390–394) + **iv-3c (#395 MERGED)**. iv-3c forwards `{"dataset":{generator,
  params}}` on the one-shot Start; params come from the registry's `DatasetTypeSpec.default_params`
  (`equities_seq` = `{max_symbols:5, regression_target:"return"}` — bounded + stationary).
- **A1b design RATIFIED 2026-06-25** (OQ-1 / OQ-4 spike + scope):

  | Decision | Ratified |
  |---|---|
  | **Surface (OQ-1)** | **Modal** — `dbc.Modal(size="xl", scrollable=True, centered=True)`. Chosen over a Models-tab because the tab bar caps `visualization-tabs.active_tab` writers at exactly 2 (mount-race guard `test_single_mount_time_active_tab_restore`) **and** is rebuilt by the one_shot suppression (`_visible_tabs`); a modal's `is_open` toggle sidesteps both. dbc 2.0.4 = Bootstrap 5: `size` caps width (xl = 1140px); height auto-grows to the viewport, then `scrollable` scrolls the body — so it scales to many models with no manual sizing. |
  | **Table (OQ-4)** | **Custom `dbc.Table`** (NOT `dash_table.DataTable`) — A1b's cells are rich: a status badge, a compatibility-reason cell, and a per-row Select button disabled for incompatible models; DataTable renders those as conditional cell *styling*, not real components, and there is no virtualization payoff at 2–5 rows. |
  | **Scope** | **Split A1b-1 → A1b-2** (mirrors iv-3a / iv-3b). |
  | **Lifecycle (option a)** | `coming_soon` (recurrence) stays FULLY selectable (consistent with the shipped iv-3a picker); D8 Train-gating is deferred to **iv-5** (flip-to-live). |

---

## 2. Remaining work

### A1b-1 — the model-selection modal surface (THIS slice; PRIMARY)

The dedicated full-width surface (D7) + the sidebar handoff to it. Concretely:

1. **Modal** — `dbc.Modal(size="xl", scrollable=True, centered=True, id="model-selection-modal")`
   near the other modals (`dashboard_manager.py`: welcome-modal @~1708, live-switch-modal @~1750 /
   1789; insert after ~1816). Header "Select a Model"; body = a container
   (`model-selection-table-container`) the open-callback fills with the custom `dbc.Table`; footer =
   a Close button (`model-selection-modal-close`).
2. **Sidebar** — REPLACE `nn-model-dropdown` (@~1068-1075, inside the `sidebar-nn-model` div
   @~1064-1079) with the kept `nn-model-summary` (@~1076) + a new **"▸ change"** button
   (`nn-model-change-button`) that opens the modal. (`model_options()` may become an unused import —
   check.)
3. **Table builder** — `_build_model_selection_table(dataset_value, selected_model)`: rows = `MODELS`;
   columns = Model / Category / Status badge (`live` / `coming_soon` / …) / Compatibility (✓ or
   `model_reason` vs the current dataset) / Select. Select =
   `dbc.Button(id={"type":"model-select-btn","index":model.key}, disabled=<not compatible>)`.
   Highlight the active row. **Option (a): coming_soon is NOT disabled — only *incompatible* is.**
4. **Callbacks** (in `_setup_model_selection_callbacks` @~2077):
   - `toggle_model_modal` — `nn-model-change-button` opens (and rebuilds the table vs the current
     `nn-dataset-type-dropdown` value via `State`), `model-selection-modal-close` closes. Outputs
     `model-selection-modal.is_open` + `model-selection-table-container.children`; branch on
     `ctx.triggered_id`.
   - **REWIRE** `select_model` (@~2086-2094): from `Input("nn-model-dropdown","value")` →
     `Input({"type":"model-select-btn","index":ALL},"n_clicks")`; resolve the clicked `model_key`
     via `ctx.triggered_id["index"]` (guard the no-click initial fire); reuse `_select_model_handler`;
     ALSO close the modal (`Output("model-selection-modal","is_open", allow_duplicate=True)` → False).
     Pattern-matching idiom already in the file: `dash.ALL` @~3107.
   - **KEEP** `gate_dataset_options` (@~2096) and `resolve_oneshot_start_body` (@~2109) UNCHANGED.
5. **Registry** — add `model_reason(model, dataset) -> str | None` (the model-perspective inverse of
   the existing `dataset_reason`; e.g. "needs 3-D data") for the compatibility cell. `compatible` /
   `MODELS` / `DATASET_TYPES` / `get_model_spec` already exist; unit-test the new helper.

> **The insulation insight (why A1b-1 is well-bounded):** the downstream gates key off the **stores**,
> not the dropdown — iv-3b `gate_dataset_options` reads `model-selection-store`; iv-3c
> `resolve_oneshot_start_body` and the iii one_shot suppression read `model-class-store`. So A1b-1
> swaps only the **input** side: the table's Select button writes those same stores via
> `_select_model_handler`, and every downstream gate follows for free.

After A1b-1: model selection happens on the dedicated surface; the sidebar is a compact summary +
"▸ change".

### A1b-2 — reactive reverse gate + degenerate states (NEXT slice)

The bidirectional gate made reactive (§5.3): selecting a **dataset** live-greys the incompatible
**models** in the table (pre-filtered on open) and annotates the sidebar summary ("3-D models only");
degenerate states (§5.8: empty compatible-set message + recovery); an optional search box
(label + family + category + tags, §5.2).

### iv-5 — flip `recurrence` `coming_soon` → `live`

One-line `model_registry.py` edit, gated on the recurrence service being deployed/reachable (or
selectable against a configured `recurrence_service_url`). Update the registry tests asserting
`coming_soon`. This is where D8 Train-gating (the deferred half of option (a)) lands.

### defect #7 (separate PR; non-blocking)

Scope the over-broad `/v1`-prefix guard test
(`src/tests/unit/backend/test_cascor_service_adapter_v1_prefix_regression.py`) to cascor-client-based
adapters.

---

## 3. Key anchors (re-grep — line numbers drift; captured 2026-06-25 off `f464272`)

- **Sidebar picker** (`dashboard_manager.py`): the `sidebar-nn-model` div @~1064-1079 (dropdown
  @~1068-1075, summary @~1076).
- **Modals**: welcome-modal @~1708, live-switch-modal @~1750 / 1789 (insertion point after ~1816).
- **Model-selection callbacks**: `_setup_model_selection_callbacks` @~2077; `select_model` @~2086;
  `gate_dataset_options` @~2096; `resolve_oneshot_start_body` @~2109; `_resolve_oneshot_start_body_handler`
  @~2118; `_select_model_handler` + `_model_summary_text` just below (the iv-3a handlers to reuse).
- **Tab machinery — do NOT entangle**: `_all_visualization_tabs` @~1870, `_visible_tabs` @~1960,
  `suppress_cascade_tabs` @~2058; the "exactly two `active_tab` writers" guard (comment @~1965).
- **Pattern-matching idiom**: `dash.ALL` (param-pin) @~3107.
- **Registry** (`src/model_registry.py`): `MODELS`, `DATASET_TYPES`, `compatible`, `dataset_reason`,
  `gated_dataset_options`, `model_options`, `dataset_default_params`, `get_model_spec`.

---

## 4. CI / test gotchas (hard-won on iv-3c)

- **Control-graph lint** (`src/tests/unit/test_control_graph_lint.py`): every ACTIONABLE control
  (Button / Dropdown / Input) must be reachable by a callback `Input` or listed in `KNOWN_ORPHANS`.
  The new `nn-model-change-button` + `model-selection-modal-close` are actionable → wire them.
  **Verify the pattern-matching Select buttons don't trip it** (it may not understand dict IDs).
  Removing `nn-model-dropdown` may need a lint / L2-manifest update.
- **Update the iv-3a tests**: `src/tests/regression/test_model_picker.py` + `test_model_select.py`
  reference `nn-model-dropdown` and assert the dropdown select flow — rewrite for the table. Add a
  new `src/tests/regression/test_model_table.py` (modal open/close; table rows = registry;
  compatibility/status cells; Select → store + `/api/model/select` + close). Behavioral tests go in
  `src/tests/regression/` (the coverage-gated scope).
- **`DashboardManager({})` construction** in a regression test validates the new modal + callbacks
  register cleanly (catches `allow_duplicate` duplicate-output conflicts up front). Delegate callback
  bodies to testable `_*_handler` methods.
- **Run gates under `conda activate JuniperCanopy1`** (Py3.13) — the **bare interpreter skips the
  LIBTORCH-strip activate hook**, so `import torch` dies (`undefined symbol …`). Run pytest from the
  **worktree ROOT**, not `src/` (the coverage `omit` patterns are cwd-relative; running from `src/`
  tanks the total to ~58%).
  - coverage (≥80): `pytest -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ --cov=src --cov-report=term-missing --cov-fail-under=80`
  - lint: `pre-commit run --files <changed>` (black / isort / flake8 ×2 / mypy / bandit / async-route).
  - UI suite SEPARATELY (never concurrent with the coverage gate): `pytest src/tests/ui --override-ini=addopts= -p no:cacheprovider` (~6 min; chromium installed).
- **Black** parses the file's py3.14 syntax fine on JuniperCanopy1 (py3.13) — no local black-parse failure (verified on iv-3c).

---

## 5. Conventions

- **One PR per slice; Paul merges between.** 2-gate worktree sweep: Paul says merged AND
  `gh pr view` shows `MERGED`. Sweep the A1b-1 worktree only after its PR merges; create the A1b-2
  worktree off fresh `origin/main` **before** removing the old one (CWD-safe V2).
- Tests under **JuniperCanopy1** (Py3.13). Pre-commit + CI span py3.12 / 3.13 / 3.14.
- Commit messages end with the `Co-Authored-By` + `Claude-Session` trailers; PR bodies end with the
  Generated-with-Claude-Code footer.
- Worktrees centralized in `…/Juniper/worktrees/`, off fresh `origin/main`.

---

## 6. Git status at handoff

- canopy `main` = `f464272` (#395 merged; the iv-3c worktree was swept + its branch deleted).
- **A1b-1 worktree exists, no edits** (see §0.3) — the starting point: `feat/canopy-model-table` off
  `f464272`.
- juniper-ml: this doc lands on its own `docs/handoff-canopy-a1b-1-model-table` branch (open PR);
  juniper-ml `main` advanced via concurrent agent-suite sessions.
- No uncommitted work elsewhere; no lingering background tasks. The running-record memory holds the
  full A1b design.
