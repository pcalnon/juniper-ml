# Integrated Canopy Dashboard Development Plan

- **Version**: 1.0.0
- **Date**: 2026-03-29
- **Status**: VALIDATED — READY FOR IMPLEMENTATION
- **Scope**: juniper-canopy (primary), juniper-cascor, juniper-cascor-client
- **Supersedes**:
  - `CANOPY_DASHBOARD_DISPLAY_FIXES.md` v1.0.0
  - `DASHBOARD_AUGMENTATION_PLAN.md` v2.0.0
- **Prerequisites**:
  - FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md — all Appendix E fixes (MERGED ✅)
  - FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md — Appendix F phase display fix (MERGED ✅)
  - FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md — Appendix G Tiers 0-2 (MERGED ✅)
  - Output weights transposition fix for `_transform_topology()` (APPLIED ✅, uncommitted)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Codebase State Validation](#2-codebase-state-validation)
3. [Task 1: Training Metrics Tab Enhancements](#3-task-1-training-metrics-tab-enhancements)
4. [Task 2: Dataset View Tab Fix](#4-task-2-dataset-view-tab-fix)
5. [Task 3: Network Topology Layer Consistency](#5-task-3-network-topology-layer-consistency)
6. [Task 4: Pre-Existing Test Failures](#6-task-4-pre-existing-test-failures)
7. [Implementation Sequencing](#7-implementation-sequencing)
8. [Cross-Repo Dependency Workflow](#8-cross-repo-dependency-workflow)
9. [Verification Plan](#9-verification-plan)
10. [Files Requiring Modification](#10-files-requiring-modification)
11. [Source Document Reconciliation](#11-source-document-reconciliation)

---

## 1. Executive Summary

This plan integrates and reconciles two prior development plans into a single validated
specification. It addresses three dashboard display issues plus pre-existing test debt.

| # | Task                                                                      | Tab              | Severity | Status |
|---|---------------------------------------------------------------------------|------------------|----------|--------|
| 1 | Add validation overlays, progress bars, LR card, phase duration, HU ratio | Training Metrics | MODERATE | Ready  |
| 2 | Fix empty scatter plot in service mode                                    | Dataset View     | MODERATE | Ready  |
| 3 | Fix topology layer value inconsistency between service and demo modes     | Network Topology | LOW      | Ready  |
| 4 | Fix 5 pre-existing test failures                                          | Tests            | LOW      | Ready  |

**Key validation findings that differ from the source documents:**

- The DASHBOARD_AUGMENTATION_PLAN correctly identifies Appendix G work as merged — **confirmed**
- The topology layer issue is a **data-model consistency concern**, not a rendering bug — the
  visualizer ignores the numeric `layer` field entirely
- Task 1E (hidden units ratio): `max_hidden_units` IS already in the `/api/status` response
  (service_backend.py line 134) — no data plumbing needed, only display format changes
- The output_weights transposition fix (from CANOPY_DASHBOARD_DISPLAY_FIXES.md §4) is applied
  in the working tree but **not yet committed**

---

## 2. Codebase State Validation

The following Appendix G items were verified as **PRESENT and MERGED** in the current codebase:

| Item                            | File                              | Evidence                                             |
|---------------------------------|-----------------------------------|------------------------------------------------------|
| `_grow_iteration_callback`      | juniper-cascor manager.py:285     | Defined, assigned at line 325                        |
| `_output_training_callback`     | juniper-cascor manager.py:218     | Defined, assigned at line 239                        |
| `_drain_progress_queue` thread  | juniper-cascor manager.py:295     | Thread started at line 333                           |
| `TrainingState` progress fields | juniper-cascor monitor.py:36-44   | All 8 Appendix G fields present                      |
| `grow_network()` callback       | cascade_correlation.py:3323       | `on_grow_iteration_callback` param, resolved at 3383 |
| `train_output_layer()` callback | cascade_correlation.py:1455       | `on_epoch_callback` param, resolved at 1534          |
| Canopy progress detail handler  | metrics_panel.py:1070-1103        | Reads all progress fields                            |
| Output weights transposition    | cascor_service_adapter.py:599-608 | Applied, uncommitted                                 |

---

## 3. Task 1: Training Metrics Tab Enhancements

### 3A. Validation Loss/Accuracy Overlay Traces

**Status**: Backend data available, frontend not consuming it.

The backend normalizes `val_loss` and `val_accuracy` into `metrics.val_loss` / `metrics.val_accuracy`
(cascor_service_adapter.py:499-500, 506-507). The plot methods `_create_loss_plot()` (line 1346)
and `_create_accuracy_plot()` (line 1535) only extract `metrics.loss` and `metrics.accuracy`.

**Fix**: Add helper `_add_validation_overlay(fig, metrics_data, field_name, trace_name, color)`
that extracts `metrics.{field_name}`, filters `None` values, and adds a dashed Scatter trace.
Call from both plot methods.

**Effort**: Small (30 minutes)

### 3B. Training Progress Summary (dbc.Progress bars)

**Status**: `dbc` is imported (line 47) but `dbc.Progress` is not yet used anywhere.

**Fix**: Insert a row between the stat cards (line ~431) and the plots (line ~433) containing:

- Phase badge: `{cid}-phase-badge`
- Grow iteration progress bar: `{cid}-grow-progress` (e.g., "Iteration 3/10")
- Candidate epoch progress bar: `{cid}-candidate-epoch-progress`

Add a new callback from `training-state-store` → `_update_training_progress_handler()` with
visibility toggling (hide bars when idle/stopped).

**Note**: Use a **separate callback** — do NOT expand the existing 8-element return tuple from
`_update_metrics_display_handler`.

**Effort**: Medium (1–2 hours)

### 3C. Learning Rate Metric Card

**Status**: `learning_rate` is in `TrainingState` (monitor.py:308) and flows through `/api/state`.

**Fix**: Add 5th stat card after "Hidden Units" — color `#6f42c1` (purple), ID `{cid}-current-lr`.
Use a separate small callback from `training-state-store`. Format: `f"{lr:.6f}"`.

**Effort**: Low (15 minutes)

### 3D. Phase Duration Display

**Status**: `phase_started_at` is in `TrainingState` and populated (manager.py:245).

**Fix**: Add `html.Span` ID `{cid}-phase-duration` in the progress summary section. Compute
elapsed from `phase_started_at` (ISO 8601) vs `datetime.now()`. Display "Phase Duration: Xm Ys"
when active, empty when idle/stopped.

**Effort**: Low (15 minutes)

### 3E. Hidden Units Progress Ratio

**Status**: `max_hidden_units` is already present in both `/api/status` (service_backend.py
line 134) and `/api/state`. No data plumbing changes needed — display format changes only.

**Fix — Metrics panel card**: Change "Hidden Units" card from plain count to `"N / max"` format.

**Fix — Status bar**: Update `_build_unified_status_bar_content` to read `max_hidden_units` from
the status response (already present) and display as `"N / max"`.

**Effort**: Trivial (15 minutes)

---

## 4. Task 2: Dataset View Tab Fix

### 4.1 Root Cause

`ServiceBackend.get_dataset()` (service_backend.py:155-168) returns metadata only. The
`DatasetPlotter._create_scatter_plot()` shows "No data available" when `len(inputs) == 0`
(line 307). CasCor has the actual tensors (`_train_x`, `_train_y`) in memory but does not
expose them via any endpoint.

### 4.2 Phase 1: Graceful Degradation (canopy-only)

**File**: `src/frontend/components/dataset_plotter.py`

When `inputs` is empty but metadata is present, show an informational stats card instead of
the generic "No data available" message. Display `num_samples`, `num_features`, `num_classes`.

**File**: `src/backend/service_backend.py`

Pass through `inputs`/`targets` from the raw response if present (future-proofing for Phase 2).

**Effort**: Low (30 minutes)

### 4.3 Phase 2: Cross-Repo Dataset Data Endpoint

#### 4.3.1 juniper-cascor

**File**: `src/api/lifecycle/manager.py` — add `get_dataset_data()`:

```python
def get_dataset_data(self) -> Optional[Dict[str, Any]]:
    """Return dataset arrays for visualization."""
    if self._train_x is None:
        return None
    result = {
        "train_x": self._train_x.detach().cpu().tolist(),
        "train_y": self._train_y.detach().cpu().tolist(),
    }
    if self._val_x is not None:
        result["val_x"] = self._val_x.detach().cpu().tolist()
        result["val_y"] = self._val_y.detach().cpu().tolist()
    return result
```

**File**: `src/api/routes/dataset.py` — add `GET /v1/dataset/data` endpoint.

#### 4.3.2 juniper-cascor-client

**File**: `juniper_cascor_client/client.py` — add `get_dataset_data()` method.

#### 4.3.3 juniper-canopy

**File**: `src/backend/cascor_service_adapter.py` — add `get_dataset_data()` with target
conversion:

```python
def get_dataset_data(self) -> Optional[Dict[str, Any]]:
    """Fetch dataset arrays from CasCor for scatter plot visualization."""
    try:
        result = self._unwrap_response(self._client.get_dataset_data())
        if not result:
            return None
        inputs = result.get("train_x", [])
        targets_raw = result.get("train_y", [])
        # Binary (output_size=1): threshold at 0.5 — NOT argmax
        # Argmax of single-element list [1.0] returns 0, not 1
        if targets_raw and len(targets_raw[0]) == 1:
            targets = [int(row[0] >= 0.5) for row in targets_raw]
        elif targets_raw:
            targets = [max(range(len(row)), key=lambda i: row[i]) for row in targets_raw]
        else:
            targets = []
        return {"inputs": inputs, "targets": targets}
    except JuniperCascorClientError:
        return None
```

> **⚠️ Binary Classification Target Conversion**: CasCor stores `train_y` as 2D tensor with
> shape `(n_samples, output_size)`. For binary classification (`output_size=1`), each row is
> `[0.0]` or `[1.0]`. `argmax` of a single-element list always returns 0. Must use threshold.

**File**: `src/backend/service_backend.py` — merge arrays into `get_dataset()` response.

**Effort**: Small–Medium (1–2 hours across 3 repos)

---

## 5. Task 3: Network Topology Layer Consistency

### 5.1 Current State

The output_weights transposition bug is **already fixed** (applied in working tree, uncommitted).
A separate issue remains: layer value assignment inconsistency.

| Source                                  | Input layer | Hidden layer(s)                     | Output layer     |
|-----------------------------------------|-------------|-------------------------------------|------------------|
| Service adapter (`_transform_topology`) | 0           | `h + 1` (incremental: 1, 2, 3, ...) | `num_hidden + 1` |
| Demo backend                            | 0           | 1 (all hidden on same layer)        | 2                |

### 5.2 Analysis

**The visualizer does NOT use the numeric `layer` field.** The `NetworkVisualizer` (lines 583-591)
builds its own networkx graph using string layer labels (`"input"`, `"hidden"`, `"output"`) and
computes layout from `n_input`, `n_hidden`, `n_output` counts. The numeric `layer` field is
**ignored for rendering**.

**Impact**: The inconsistency affects:

- Integration test `test_main_coverage.py:548` which asserts `node["layer"] in [0, 1, 2]` — this
  would **FAIL with ≥3 hidden units** in service mode (hidden_2 gets layer=3)
- API consumers that inspect the raw topology JSON and expect consistent layer semantics

**Architectural note**: The service adapter's incrementing scheme (`h + 1`) is technically correct
for CasCor — each cascade hidden unit IS on a different layer in the cascade architecture. The
demo backend's fixed scheme (all hidden = 1) is a simplification.

### 5.3 Fix

Normalize to the demo backend's 3-layer scheme (`0/1/2`) for API consistency, since:

1. The visualizer already handles multi-hidden-unit positioning independently
2. The integration test expects `[0, 1, 2]`
3. Consistent layer semantics across modes prevents consumer confusion

**File**: `src/backend/cascor_service_adapter.py`

- Line 582: `"layer": h + 1` → `"layer": 1`
- Line 611: `"layer": num_hidden + 1` → `"layer": 2`

**Effort**: Trivial (2 lines)

---

## 6. Task 4: Pre-Existing Test Failures

Five tests in `test_response_normalization.py` fail due to stale fixtures:

| Test                                            | Root Cause                                           | Fix              |
|-------------------------------------------------|------------------------------------------------------|------------------|
| `test_get_current_metrics_unwraps`              | Expects flat `train_loss`, now nested `metrics.loss` | Update assertion |
| `test_real_envelope_emits_legacy_metrics_shape` | Missing `real_training_status_epoch_zero` fixture    | Add fixture      |
| `test_epoch_zero_preserved`                     | Missing `real_training_status_epoch_zero` fixture    | Add fixture      |
| `test_hidden_units_zero_preserved`              | Missing `real_training_status_epoch_zero` fixture    | Add fixture      |
| `test_get_status_partial_nested`                | Indexes result as list but gets dict                 | Fix indexing     |

**Effort**: Small (30 minutes)

---

## 7. Implementation Sequencing

| Phase | Items                                                          | Complexity | Repo                          | Dependencies |
|-------|----------------------------------------------------------------|------------|-------------------------------|--------------|
| **1** | Task 4: Fix pre-existing test failures                         | Low        | canopy                        | None         |
| **1** | Task 3: Fix layer assignments (2 lines)                        | Trivial    | canopy                        | None         |
| **1** | Task 2 Phase 1: Metadata-only graceful handling                | Low        | canopy                        | None         |
| **1** | Commit output_weights transposition fix                        | N/A        | canopy                        | None         |
| **2** | Task 1A: Validation overlay traces                             | Low        | canopy                        | None         |
| **2** | Task 1C: Learning rate card                                    | Low        | canopy                        | None         |
| **2** | Task 1D: Phase duration display                                | Low        | canopy                        | None         |
| **2** | Task 1E: Hidden units ratio (card + status endpoint)           | Trivial    | canopy                        | None         |
| **3** | Task 1B: Training progress bars (dbc.Progress)                 | Medium     | canopy                        | None         |
| **4** | Task 2 Phase 2: Dataset data endpoint + client + canopy wiring | Medium     | cascor, cascor-client, canopy | Cross-repo   |

Phase 1 is all canopy-only, low-risk, and can ship immediately.
Phase 2 items are independent and can be done in parallel.
Phase 3 introduces first `dbc.Progress` usage — slightly higher complexity.
Phase 4 requires cross-repo coordination per §8.

---

## 8. Cross-Repo Dependency Workflow

Task 2 Phase 2 adds `get_dataset_data()` to juniper-cascor-client. Follow this process:

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
5. CI lockfile-check job verifies consistency

---

## 9. Verification Plan

### 9.1 Automated Tests

```bash
# juniper-canopy
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda activate JuniperPython
pytest tests/unit/test_response_normalization.py -v  # 0 failures
pytest tests/unit/ -q --timeout=30                    # Full unit suite

# juniper-cascor (Phase 4 only)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
conda activate JuniperCascor
pytest src/tests/unit/api/ -q                         # All API tests pass
```

### 9.2 New Tests Required

| Test                                                | Validates                                       | Phase |
|-----------------------------------------------------|-------------------------------------------------|-------|
| `test_transform_topology_correct_layer_assignments` | All hidden = layer 1, outputs = layer 2         | 1     |
| `test_process_dataset_update_metadata_only`         | Metadata-only renders stats without crash       | 1     |
| `test_add_validation_overlay_with_data`             | val_loss/val_accuracy traces added to plot      | 2     |
| `test_add_validation_overlay_no_data`               | No trace when all validation values are None    | 2     |
| `test_dataset_data_endpoint_returns_arrays`         | `/v1/dataset/data` returns train_x, train_y     | 4     |
| `test_dataset_data_no_dataset_returns_404`          | 404 when no dataset loaded                      | 4     |
| `test_service_backend_get_dataset_includes_arrays`  | Includes `inputs`/`targets` when available      | 4     |
| `test_dataset_target_conversion_binary`             | `[[0.0],[1.0],[0.0]]` → `[0, 1, 0]` (threshold) | 4     |
| `test_dataset_target_conversion_multiclass`         | `[[1,0,0],[0,1,0]]` → `[0, 1]` (argmax)         | 4     |

### 9.3 Visual Verification Checklist

- [ ] Training Metrics: validation loss overlay appears as dashed line on loss plot
- [ ] Training Metrics: validation accuracy overlay appears on accuracy plot
- [ ] Training Metrics: progress bars show grow iteration and candidate epoch
- [ ] Training Metrics: learning rate card displays current value
- [ ] Training Metrics: phase duration shows elapsed time during active training
- [ ] Training Metrics: hidden units shows "N / max" format
- [ ] Dataset View: service mode shows metadata stats (Phase 1)
- [ ] Dataset View: service mode shows scatter plot with class colors (Phase 2)
- [ ] Network Topology: renders correctly with 0, 1, 2+ hidden units
- [ ] Network Topology: all input→output and hidden→output connections present

---

## 10. Files Requiring Modification

### 10.1 juniper-canopy — Phase 1 (canopy-only, low-risk)

| File                                             | Changes                                         |
|--------------------------------------------------|-------------------------------------------------|
| `src/backend/cascor_service_adapter.py`          | Fix layer assignments (2 lines: 582, 611)       |
| `src/backend/service_backend.py`                 | Pass-through inputs/targets in `get_dataset()`  |
| `src/frontend/components/dataset_plotter.py`     | Metadata-only graceful handling                 |
| `src/tests/unit/test_response_normalization.py`  | Fix 5 pre-existing failures; add layer test     |
| `src/tests/fixtures/cascor_response_fixtures.py` | Add `real_training_status_epoch_zero()` fixture |

### 10.2 juniper-canopy — Phase 2-3 (UI enhancements)

| File                                       | Changes                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------|
| `src/frontend/components/metrics_panel.py` | Tasks 1A-1E: overlays, progress bars, LR card, phase duration, HU ratio |
| `src/frontend/dashboard_manager.py`        | Task 1E: hidden units ratio in status bar                               |

### 10.3 juniper-canopy — Phase 4 (cross-repo)

| File                                    | Changes                                                    |
|-----------------------------------------|------------------------------------------------------------|
| `src/backend/cascor_service_adapter.py` | Add `get_dataset_data()` with binary/multiclass conversion |
| `src/backend/service_backend.py`        | Merge dataset arrays into `get_dataset()`                  |

### 10.4 juniper-cascor — Phase 4

| File                           | Changes                             |
|--------------------------------|-------------------------------------|
| `src/api/lifecycle/manager.py` | Add `get_dataset_data()` method     |
| `src/api/routes/dataset.py`    | Add `GET /v1/dataset/data` endpoint |

### 10.5 juniper-cascor-client — Phase 4

| File                              | Changes                         |
|-----------------------------------|---------------------------------|
| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

### 10.6 Already Applied (uncommitted)

| File                                             | Changes                                                 | Status     |
|--------------------------------------------------|---------------------------------------------------------|------------|
| `src/backend/cascor_service_adapter.py`          | Output weights transposition in `_transform_topology()` | ✅ Applied |
| `src/tests/fixtures/cascor_response_fixtures.py` | Fixed `real_topology()` to use 2D format                | ✅ Applied |
| `src/tests/unit/test_response_normalization.py`  | Added output connection count tests                     | ✅ Applied |

### 10.7 Files NOT Requiring Modification

- `network_visualizer.py` — uses count-based positioning, ignores numeric `layer` field
- `dataset_plotter.py` (Phase 2+) — already handles `inputs`/`targets` correctly; needs data
- `metrics_panel.py` `_update_progress_detail_handler` — already wired for all progress fields
- `monitor.py` (cascor) — `TrainingState` fields already populated by merged Appendix G work

---

## 11. Source Document Reconciliation

This plan reconciles the following discrepancies between the source documents:

| Issue                          | CANOPY_DASHBOARD_DISPLAY_FIXES.md                 | DASHBOARD_AUGMENTATION_PLAN.md           | Resolution                                                    |
|--------------------------------|---------------------------------------------------|------------------------------------------|---------------------------------------------------------------|
| Appendix G state               | Assumed not yet implemented                       | Correctly assumes merged                 | **Merged confirmed** ✅                                       |
| Topology issue                 | Output weights transposition only                 | Transposition + layer assignment         | **Both issues real**, transposition fixed, layer fix included |
| Task 1 scope                   | Only hidden units ratio (§2.5)                    | Full 1A-1E enhancement suite             | **Adopted broader scope** from augmentation plan              |
| TrainingState hooks            | Proposed `monitored_validate()` for grow progress | Correctly identifies injected callback   | **Callback approach confirmed** ✅                            |
| Dataset graceful degradation   | Not included                                      | Phase 1 metadata-only handling           | **Adopted** — good UX even without cross-repo work            |
| Binary target conversion       | Correctly identified argmax bug                   | Also correctly identifies threshold fix  | **Both agree** — threshold for output_size=1                  |
| Task 1E status bar data source | Assumes `max_hidden_units` available              | Doesn't address data source gap          | **Identified gap** — need to add to `/api/status`             |
| Cross-repo dependency workflow | Not included                                      | Includes version bump + lockfile process | **Adopted** from augmentation plan                            |

---

*End of Integrated Canopy Dashboard Development Plan:*
