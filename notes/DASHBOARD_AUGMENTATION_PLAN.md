# Canopy Dashboard Augmentation Plan (Integrated)

**Date:** 2026-03-29
**Version:** 2.0.0
**Status:** PARTIALLY COMPLETE — Phase 1 items done, Phase 2-4 remaining
**Scope:** juniper-canopy (primary), juniper-cascor + juniper-cascor-client (dataset endpoint)
**Prerequisite:** FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md Appendix G (Tiers 0-2 all merged)
**Synthesized From:**

- `juniper-ml/notes/CANOPY_DASHBOARD_DISPLAY_FIXES.md` v1.0.0
- `juniper-ml/notes/DEPENDENCY_UPDATE_WORKFLOW.md` v1.0.0
- Claude Code plan exploration (2026-03-29)

---

## Table of Contents

1. [Context](#1-context)
2. [Task 1: Training Metrics Tab — Display Additional Fields](#2-task-1-training-metrics-tab)
3. [Task 2: Dataset View Tab — Fix Plot Display](#3-task-2-dataset-view-tab)
4. [Task 3: Network Topology Tab — Fix Display After Hidden Units](#4-task-3-network-topology-tab)
5. [Pre-Existing Test Failures](#5-pre-existing-test-failures)
6. [Implementation Sequencing](#6-implementation-sequencing)
7. [Cross-Repo Dependency Workflow](#7-cross-repo-dependency-workflow)
8. [Verification Plan](#8-verification-plan)
9. [Files Requiring Modification](#9-files-requiring-modification)
10. [Validation Results](#10-validation-results)

---

## 1. Context

Following the Appendix G metrics emission granularity work (Tiers 0-2), the canopy dashboard now
has 29 TrainingState fields and normalized metrics flowing through both REST and WebSocket
channels. The cascor lifecycle manager now populates all progress fields (`phase_detail`,
`grow_iteration`, `grow_max`, `best_correlation`, `candidates_trained`, `candidates_total`,
`candidate_epoch`, `candidate_total_epochs`, `phase_started_at`) during training via injected
callbacks and a drain thread. Three dashboard display issues remain:

| # | Issue                                                                | Tab              | Severity | Root Cause                                                                                 |
|---|----------------------------------------------------------------------|------------------|----------|--------------------------------------------------------------------------------------------|
| 1 | Progress fields shown only as text, no charts for validation metrics | Training Metrics | MODERATE | UI doesn't plot val_loss/val_accuracy; no progress bars or extra metric cards              |
| 2 | Dataset scatter plot always empty in service mode                    | Dataset View     | MODERATE | CasCor `/v1/dataset` returns metadata only, no data arrays                                 |
| 3 | Network topology layer data contract broken after first hidden unit  | Network Topology | HIGH     | `_transform_topology()` assigns incrementing layer numbers instead of fixed 3-layer scheme |

**Note:** The output_weights matrix transposition bug (identified in CANOPY_DASHBOARD_DISPLAY_FIXES.md
section 4) has already been fixed and merged. The remaining topology issue (Task 3 below) is the
layer field assignment, which is a separate data contract bug.

---

## 2. Task 1: Training Metrics Tab

### 2.1 Current State (Post-Appendix G)

The Appendix G work (now merged) completed:

- **Cascor side (DONE)**: TrainingState fields populated via `_grow_iteration_callback` and
  `_output_training_callback` in `manager.py`; drain thread reads candidate progress from
  worker pool's `progress_queue`
- **Canopy side (DONE)**: `_update_progress_detail_handler` displays progress text; relay
  forwards all new fields; TrainingState mirrors all 29 fields

**Still missing on the canopy UI side:**

| Enhancement                                             | Type                 | Complexity |
|---------------------------------------------------------|----------------------|------------|
| 2A. Validation loss/accuracy overlay traces             | New chart overlay    | Medium     |
| 2B. Training progress summary cards (dbc.Progress bars) | New UI section       | Medium     |
| 2C. Learning rate metric card                           | New stat card        | Low        |
| 2D. Phase duration display                              | New text element     | Low        |
| 2E. Hidden units progress ratio                         | Modify existing card | Trivial    |

### 2A. Validation Loss/Accuracy Overlay Traces

**File:** `src/frontend/components/metrics_panel.py`

The backend already normalizes `val_loss` and `val_accuracy` into `metrics.val_loss` /
`metrics.val_accuracy` via `_normalize_metric()` (cascor_service_adapter.py:482-500), but
`_create_loss_plot()` and `_create_accuracy_plot()` don't read them.

- Add helper `_add_validation_overlay(fig, metrics_data, field_name, trace_name, color)` that
  extracts `metrics.{field_name}` from each entry, filters Nones, adds dashed Scatter trace
- Call from `_create_loss_plot()` — overlay `val_loss` as dashed purple (`#9467bd`)
- Call from `_create_accuracy_plot()` — overlay `val_accuracy` as dashed brown (`#8c564b`)
- Plot validation data across all phases (not just output)

### 2B. Training Progress Summary Cards

**File:** `src/frontend/components/metrics_panel.py`

- Insert `html.Div` row between metric cards (line ~431) and plots (line ~433)
- Contains: phase badge, `dbc.Progress` for grow iteration, `dbc.Progress` for candidate epoch
- IDs: `{cid}-phase-badge`, `{cid}-grow-progress`, `{cid}-candidate-epoch-progress`
- New callback from `training-state-store` -> `_update_training_progress_handler()` with
  visibility toggling (hide bars when idle/stopped)
- Note: `dbc.Progress` is not yet used in canopy (first usage), but `dbc` is imported at line 47

### 2C. Learning Rate Metric Card

**File:** `src/frontend/components/metrics_panel.py`

- Add 5th metric card after "Hidden Units" — color `#6f42c1`, ID `{cid}-current-lr`
- **Use a separate small callback** from `training-state-store` (NOT expand the existing
  8-element return tuple from `_update_metrics_display_handler`)
- Format: `f"{lr:.6f}"`

### 2D. Phase Duration Display

**File:** `src/frontend/components/metrics_panel.py`

- Add `html.Span` ID `{cid}-phase-duration` next to phase badge in progress section
- Compute elapsed from `phase_started_at` (ISO 8601) vs `datetime.now()`
- Display "Phase Duration: Xm Ys" when active, empty when idle/stopped

### 2E. Hidden Units Progress Ratio

**File:** `src/frontend/components/metrics_panel.py`, `src/frontend/dashboard_manager.py`

- Change "Hidden Units" card from plain count to `"N / max"` format
- `max_hidden_units` is available from `/api/state` (already in TrainingState)
- Update status bar display similarly

---

## 3. Task 2: Dataset View Tab

### 3.1 Root Cause

`ServiceBackend.get_dataset()` (service_backend.py:155-168) returns metadata only. The
`DatasetPlotter._create_scatter_plot()` triggers "No data available" at line 308 when
`len(inputs) == 0`. DemoBackend works because `demo_backend.py:193-198` includes arrays.

CasCor has the training tensors in memory (`_train_x`, `_train_y`) but its `/v1/dataset`
endpoint only serializes shape metadata, not the tensor data itself.

### 3.2 Fix — Phase 1: Canopy Graceful Degradation (canopy-only)

**File:** `src/frontend/components/dataset_plotter.py`

In `_process_dataset_update()`, add metadata-only branch:

- Check `"inputs" in dataset and dataset["inputs"]`
- When metadata-only: show stats with informational placeholder plot
- When full data: existing logic unchanged

**File:** `src/backend/service_backend.py`

In `get_dataset()`, pass through `inputs`/`targets` if present in raw response (future-proofing).

### 3.3 Fix — Phase 2: Cross-Repo Dataset Data Endpoint

**Repository: juniper-cascor:**

Add `get_dataset_data()` method to `src/api/lifecycle/manager.py`:

```python
def get_dataset_data(self) -> Optional[Dict[str, Any]]:
    if self._train_x is None:
        return None
    result = {"train_x": self._train_x.detach().cpu().tolist(),
              "train_y": self._train_y.detach().cpu().tolist()}
    if self._val_x is not None:
        result["val_x"] = self._val_x.detach().cpu().tolist()
        result["val_y"] = self._val_y.detach().cpu().tolist()
    return result
```

Add `GET /v1/dataset/data` endpoint in `src/api/routes/dataset.py`.

**Repository: juniper-cascor-client:**

Add `get_dataset_data()` to `juniper_cascor_client/client.py`.

**Repository: juniper-canopy:**

Add `get_dataset_data()` to `cascor_service_adapter.py` with target conversion:

- Binary (output_size=1): threshold at 0.5 (`int(row[0] >= 0.5)`) — NOT argmax
- Multi-class (output_size>1): standard argmax

Update `service_backend.get_dataset()` to merge arrays when available.

**Payload**: ~5-10 KB for typical spiral dataset (200 samples x 2 features). The dashboard
already only fetches when the Dataset tab is active.

### 3.4 Dependency Update When Adding Client Method

Per `DEPENDENCY_UPDATE_WORKFLOW.md`, after adding `get_dataset_data()` to juniper-cascor-client:

1. Publish new client version (or use git dependency during development)
2. Update canopy's `pyproject.toml` to require the new minimum client version
3. Regenerate lockfile: `uv pip compile pyproject.toml --extra juniper-data --extra juniper-cascor -o requirements.lock`
4. Commit both `pyproject.toml` and `requirements.lock` together

---

## 4. Task 3: Network Topology Tab

### 4.1 Root Cause

**Output weights transposition bug**: ALREADY FIXED (merged). `_transform_topology()` now
transposes the output_weights matrix before building connections.

**Layer field assignment bug** (remaining): `_transform_topology()` line 582 assigns
`"layer": h + 1` to hidden nodes (hidden_0=1, hidden_1=2, ...) and line 611 assigns
`"layer": num_hidden + 1` to output nodes. DemoBackend correctly uses `"layer": 1` for all
hidden and `"layer": 2` for all output.

This breaks the integration test at `test_main_coverage.py:548` which asserts
`node["layer"] in [0, 1, 2]`, and violates the 3-layer data contract.

### 4.2 Fix

**File:** `src/backend/cascor_service_adapter.py`

- Line 582: `"layer": h + 1` -> `"layer": 1`
- Line 611: `"layer": num_hidden + 1` -> `"layer": 2`

**No changes needed to:**

- `network_visualizer.py` — uses count-based positioning via `topology["hidden_units"]`, not
  the numeric `layer` field
- `_calculate_hidden_node_position_offsets()` — handles n_hidden > 1 with staggered layout
- Output weight connection loop — correctly handles all inputs + hidden -> each output

---

## 5. Pre-Existing Test Failures

Five tests in `test_response_normalization.py` fail due to stale fixtures predating the
Appendix G work:

| Test                                            | Root Cause                                                             |
|-------------------------------------------------|------------------------------------------------------------------------|
| `test_get_current_metrics_unwraps`              | Stale assertion (expects flat `train_loss`, now nested `metrics.loss`) |
| `test_real_envelope_emits_legacy_metrics_shape` | Missing `real_training_status_epoch_zero` fixture                      |
| `test_epoch_zero_preserved`                     | Missing `real_training_status_epoch_zero` fixture                      |
| `test_hidden_units_zero_preserved`              | Missing `real_training_status_epoch_zero` fixture                      |
| `test_get_status_partial_nested`                | Indexes result as list but gets dict                                   |

**Fix:** Update assertions for nested format. Add missing fixture. Fix indexing.

---

## 6. Implementation Sequencing

| Phase | Item                                             | Complexity | Risk   | Repo                          |
|-------|--------------------------------------------------|------------|--------|-------------------------------|
| 1     | Fix pre-existing test failures (section 5)       | Low        | Low    | canopy                        |
| 1     | Task 3: Fix topology layer assignments (2 lines) | Low        | Low    | canopy                        |
| 1     | Task 2 Phase 1: Metadata-only graceful handling  | Low        | Low    | canopy                        |
| 2     | Task 1A: Validation loss/accuracy overlays       | Medium     | Low    | canopy                        |
| 2     | Task 1C: Learning rate card                      | Low        | Low    | canopy                        |
| 2     | Task 1D: Phase duration display                  | Low        | Low    | canopy                        |
| 2     | Task 1E: Hidden units ratio                      | Trivial    | Low    | canopy                        |
| 3     | Task 1B: Training progress bars (dbc.Progress)   | Medium     | Low    | canopy                        |
| 4     | Task 2 Phase 2: Dataset data endpoint            | Medium     | Medium | cascor, cascor-client, canopy |

Phase 1 items are canopy-only and can ship independently. Phase 4 requires cross-repo
coordination and a dependency version bump per the workflow in section 7.

---

## 7. Cross-Repo Dependency Workflow

When Task 2 Phase 2 adds `get_dataset_data()` to juniper-cascor-client, follow this process
(from `DEPENDENCY_UPDATE_WORKFLOW.md`):

1. Implement and publish new cascor-client version with `get_dataset_data()`
2. In canopy's `pyproject.toml`, bump `juniper-cascor-client>=X.Y.Z`
3. Regenerate lockfile:

   ```bash
   uv pip compile pyproject.toml \
     --extra juniper-data \
     --extra juniper-cascor \
     -o requirements.lock
   ```

4. Commit `pyproject.toml` + `requirements.lock` together
5. CI lockfile-check job verifies consistency automatically

If using Dependabot for the version bump, the `lockfile-update.yml` workflow auto-regenerates
the lockfile (first CI run fails on stale lock, concurrency group cancels it, second run passes).

---

## 8. Verification Plan

### 8.1 Automated Tests

```bash
# juniper-canopy
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
pytest tests/unit/test_response_normalization.py -v       # All must pass (0 failures)
pytest tests/unit/frontend/ -q --timeout=30               # Metrics panel tests
pytest tests/unit/test_dataset_plotter.py -q              # Dataset plotter tests
pytest tests/unit/ -q --timeout=30                        # Full unit suite
```

### 8.2 New Tests Required

| Test                                                | Validates                                                  |
|-----------------------------------------------------|------------------------------------------------------------|
| `test_transform_topology_correct_layer_assignments` | All hidden nodes get layer=1, outputs get layer=2          |
| `test_process_dataset_update_metadata_only`         | Metadata-only dict renders stats without crash             |
| `test_process_dataset_update_with_arrays`           | Full dataset with inputs/targets renders scatter           |
| `test_add_validation_overlay_with_data`             | val_loss/val_accuracy traces added to plot                 |
| `test_add_validation_overlay_no_data`               | No trace added when validation data all None               |
| `test_dataset_target_conversion_binary`             | Binary: `[[0.0],[1.0]]` -> `[0,1]` (threshold, not argmax) |
| `test_dataset_target_conversion_multiclass`         | Multi-class: `[[1,0,0],[0,1,0]]` -> `[0,1]` (argmax)       |

### 8.3 Visual Verification Checklist

- [ ] Training Metrics: progress bars show grow iteration and candidate epoch during training
- [ ] Training Metrics: validation loss/accuracy overlay appears on plots when available
- [ ] Training Metrics: learning rate card displays current value
- [ ] Training Metrics: phase duration shows elapsed time
- [ ] Training Metrics: hidden units shows "N / max" format
- [ ] Dataset View: service mode shows metadata stats (Phase 1) or scatter plot (Phase 2)
- [ ] Network Topology: renders correctly with 0, 1, 2+ hidden units
- [ ] Network Topology: all input->output and hidden->output connections present

---

## 9. Files Requiring Modification

### 9.1 juniper-canopy (all phases)

| File                                             | Changes                                                               | Phase |
|--------------------------------------------------|-----------------------------------------------------------------------|-------|
| `src/backend/cascor_service_adapter.py`          | Fix layer assignments (Task 3); add `get_dataset_data()` (Task 2 Ph2) | 1, 4  |
| `src/backend/service_backend.py`                 | Pass-through inputs/targets (Task 2)                                  | 1, 4  |
| `src/frontend/components/metrics_panel.py`       | Tasks 1A-1E (overlays, progress bars, cards, ratio)                   | 2-3   |
| `src/frontend/components/dataset_plotter.py`     | Metadata-only graceful handling (Task 2 Ph1)                          | 1     |
| `src/frontend/dashboard_manager.py`              | Hidden units ratio in status bar (Task 1E)                            | 2     |
| `src/tests/unit/test_response_normalization.py`  | Fix 5 pre-existing failures; add layer assertions                     | 1     |
| `src/tests/fixtures/cascor_response_fixtures.py` | Add missing `real_training_status_epoch_zero` fixture                 | 1     |

### 9.2 juniper-cascor (Phase 4 only)

| File                           | Changes                             |
|--------------------------------|-------------------------------------|
| `src/api/lifecycle/manager.py` | Add `get_dataset_data()` method     |
| `src/api/routes/dataset.py`    | Add `GET /v1/dataset/data` endpoint |

### 9.3 juniper-cascor-client (Phase 4 only)

| File                              | Changes                         |
|-----------------------------------|---------------------------------|
| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

### 9.4 Files NOT Requiring Modification

- `network_visualizer.py` — uses count-based positioning, not numeric `layer` field
- `metrics_panel.py` `_update_progress_detail_handler` — already pre-wired for progress fields
- `monitor.py` (cascor) — TrainingState fields already populated by Appendix G callbacks

---

## 10. Validation Results

All three tasks validated by specialized sub-agents (2026-03-29):

### Task 3 (Topology)

- Exact lines confirmed: 582 and 611 in cascor_service_adapter.py
- DemoBackend uses layer 1/2 (confirmed lines 143/151 of demo_backend.py)
- NetworkVisualizer does NOT use numeric layer field (confirmed lines 577-591)
- Integration test `test_main_coverage.py:548` asserts `[0,1,2]` — will pass after fix
- `_calculate_hidden_node_position_offsets()` handles n_hidden > 1 correctly

### Task 2 (Dataset)

- ServiceBackend returns metadata only (confirmed lines 155-168)
- `_create_scatter_plot()` line 308 triggers empty plot on `len(inputs) == 0`
- DemoBackend includes arrays (confirmed lines 193-198)
- Existing tests don't cover metadata-only scenario

### Task 1 (Metrics)

- val_loss/val_accuracy available in backend (lines 482-500) but not parsed by plot methods
- Card pattern: `html.Div([html.H5(), html.H2(id=...)])` with flex layout (lines 393-428)
- Handler return tuple: 8 elements — use separate callbacks for new outputs
- dbc.Progress available (dbc imported) but never used (first usage)

---

## 11. Implementation Status (2026-04-01)

| Phase | Item | Status |
|-------|------|--------|
| 1 | Fix pre-existing test failures (section 5) | ✅ COMPLETE — Fixed in Backlog Sprint 1 |
| 1 | Task 3: Fix topology layer assignments | ✅ COMPLETE — output_weights transposition fixed |
| 1 | Task 2 Phase 1: Metadata-only graceful handling | ❌ NOT STARTED |
| 2 | Task 1A: Validation loss/accuracy overlays | ❌ NOT STARTED |
| 2 | Task 1B: Training progress bars (dbc.Progress) | ✅ COMPLETE — Candidate training display fixes plan delivered progress bars |
| 2 | Task 1C: Learning rate metric card | ❌ NOT STARTED |
| 2 | Task 1D: Phase duration display | ❌ NOT STARTED |
| 2 | Task 1E: Hidden units progress ratio | ✅ COMPLETE — commit 18e39cf (max_hidden_units denominator) |
| 4 | Task 2 Phase 2: Dataset data endpoint | ❌ NOT STARTED — requires cross-repo work |

### Additional Work Completed (not in original plan)

| Feature | Commit | Description |
|---------|--------|-------------|
| Weight matrix heatmap (OF-1) | b55ff46 | New display mode for network visualizer with raw topology endpoint |
| Correlation statistics | 37c885d | Replace pool metrics with correlation stats, forward all_correlations |
| WebSocket topology buffer | 04db7e6 | Real-time topology updates via WebSocket |
| CasCor state mapping | 8d6b858 | Top candidate field mapping, candidate_pool_phase derivation |
| GIL contention test fix | 04db7e6 | Rewrote flaky training loop tests to use thread.join instead of polling |

---

*Synthesized from CANOPY_DASHBOARD_DISPLAY_FIXES.md v1.0.0, DEPENDENCY_UPDATE_WORKFLOW.md v1.0.0,
and Claude Code plan exploration. Supersedes the individual source documents for implementation.*
