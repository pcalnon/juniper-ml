# Canopy Dashboard Display Fixes — Development Plan

- **Version**: 1.0.0
- **Date**: 2026-03-29
- **Status**: READY FOR IMPLEMENTATION
- **Scope**: juniper-canopy, juniper-cascor
- **Prerequisite**: FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md (all prior fixes applied)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Issue 1: Training Metrics Tab — Missing Progress Fields](#2-issue-1-training-metrics-tab--missing-progress-fields)
3. [Issue 2: Dataset View Tab — Empty Scatter Plot in Service Mode](#3-issue-2-dataset-view-tab--empty-scatter-plot-in-service-mode)
4. [Issue 3: Network Topology Tab — Breaks After First Hidden Unit](#4-issue-3-network-topology-tab--breaks-after-first-hidden-unit)
5. [Pre-Existing Test Failures](#5-pre-existing-test-failures)
6. [Implementation Order](#6-implementation-order)
7. [Verification Plan](#7-verification-plan)
8. [Files Requiring Modification](#8-files-requiring-modification)

---

## 1. Executive Summary

Three display issues in the juniper-canopy dashboard prevent effective real-time monitoring of
an external juniper-cascor training instance:

| # | Issue                                             | Tab              | Severity | Root Cause                                                                        |
|---|---------------------------------------------------|------------------|----------|-----------------------------------------------------------------------------------|
| 1 | Training progress fields show no sub-phase detail | Training Metrics | MODERATE | CasCor `TrainingState` fields defined but never populated during training         |
| 2 | Dataset scatter plot always empty in service mode | Dataset View     | MODERATE | CasCor `/v1/dataset` returns metadata only, no data arrays                        |
| 3 | Network topology breaks after first hidden unit   | Network Topology | HIGH     | `_transform_topology()` reads `output_weights` matrix with wrong axis orientation |

Issue 3 has already been **identified and fixed** during investigation (see §4). Issues 1 and 2
require implementation work.

---

## 2. Issue 1: Training Metrics Tab — Missing Progress Fields

### 2.1 Problem

The Training Metrics tab displays four stat cards (Current Epoch, Loss, Accuracy, Hidden Units)
and a status badge, but provides **no sub-phase detail** during the long-running training phases.
When CasCor is in candidate training (which can take minutes), the dashboard shows only
"Status: Output" (the stale phase, now fixed to show "Candidate Pool") with no indication of
progress within that phase.

### 2.2 Current State

The Canopy frontend at `metrics_panel.py:1070-1103` **already pre-wires** a progress detail
display (`_update_progress_detail_handler`) that reads the following fields from `/api/state`:

| Field                                        | UI Rendering                   | Backend State                                           |
|----------------------------------------------|--------------------------------|---------------------------------------------------------|
| `phase_detail`                               | Title-cased inline text        | In `TrainingState._STATE_FIELDS` ✅, never populated ❌ |
| `grow_iteration` / `grow_max`                | "Iteration 3/10"               | In `_STATE_FIELDS` ✅, never populated ❌               |
| `best_correlation`                           | "Best Corr: 0.8542"            | In `_STATE_FIELDS` ✅, never populated ❌               |
| `candidates_trained` / `candidates_total`    | "Candidates: 12/50"            | In `_STATE_FIELDS` ✅, never populated ❌               |
| `candidate_epoch` / `candidate_total_epochs` | "Candidate Epoch: 42/600 (7%)" | In `_STATE_FIELDS` ✅, never populated ❌               |
| `phase_started_at`                           | (not consumed in UI)           | In `_STATE_FIELDS` ✅, never populated ❌               |

The `TrainingState._STATE_FIELDS` (monitor.py:23-45) already declares all these fields.
The frontend handler already formats them. **The only missing piece is populating them during
training in CasCor's lifecycle manager.**

### 2.3 Additional Display Opportunities

Fields available from `/api/status` but not shown in the Training Metrics tab:

| Field              | Value                  | Display Suggestion                                       |
|--------------------|------------------------|----------------------------------------------------------|
| `learning_rate`    | Current LR from CasCor | Add to stat cards or progress detail                     |
| `max_hidden_units` | Configured max         | Show as `hidden_units / max_hidden_units` progress ratio |
| `max_epochs`       | Configured max epochs  | Show as context for grow_iteration                       |

### 2.4 Fix: Populate TrainingState During Training

**Repository**: juniper-cascor

**File**: `src/api/lifecycle/manager.py`

The `monitored_grow()` wrapper already has access to `state` (`TrainingState`) and the
`grow_network()` result data. The fix hooks into the grow loop to populate progress fields.

However, `monitored_grow()` wraps the **entire** `grow_network()` call as an opaque block —
it does not have access to the **per-iteration** loop variables inside `grow_network()`.
To populate `grow_iteration`, `best_correlation`, and `candidates_trained` at each iteration,
the lifecycle manager needs a hook **inside** the grow loop.

**Approach**: Two mechanisms, chosen to avoid the scoping problem (grow_network's per-iteration
variables like `best_correlation` and `candidates_trained` are local to the loop body inside
`grow_network()` and not accessible from the `monitored_validate` wrapper).

**Mechanism A — Grow iteration callback (injected attribute)**:

Inject a callback onto the network object (`self.network._grow_iteration_callback`) that
`grow_network()` can call at each iteration boundary. This callback receives the iteration
variables directly, bypassing the scope limitation.

```python
# In _install_monitoring_hooks():
def _grow_iteration_callback(iteration, max_iterations, best_correlation,
                              candidates_trained, candidates_total, phase_detail):
    state.update_state(
        grow_iteration=iteration,
        grow_max=max_iterations,
        best_correlation=best_correlation,
        candidates_trained=candidates_trained,
        candidates_total=candidates_total,
        phase_detail=phase_detail,
    )
manager_ref.network._grow_iteration_callback = _grow_iteration_callback
```

Then in `cascade_correlation.py`, `grow_network()` calls the callback (if present) at each
iteration:

```python
# Inside grow_network loop, after train_candidates returns:
if hasattr(self, '_grow_iteration_callback') and self._grow_iteration_callback:
    self._grow_iteration_callback(
        iteration=epoch + 1,
        max_iterations=max_epochs,
        best_correlation=training_results.best_correlation if training_results else None,
        candidates_trained=training_results.success_count if training_results else 0,
        candidates_total=self.candidate_pool_size,
        phase_detail="adding_candidate",
    )
```

**Mechanism B — Phase detail updates in monitored_grow()**:

`monitored_grow()` sets phase_detail at the start and end (coarse phase transitions):

```python
def monitored_grow(*args, **kwargs):
    manager_ref._extract_and_record_metrics()
    state.update_state(
        phase_detail="candidate_training",
        candidates_total=getattr(manager_ref.network, "candidate_pool_size", None),
        phase_started_at=datetime.now().isoformat(),
    )
    ...
    result = original_grow(*args, **kwargs)
    ...
    state.update_state(phase_detail="output_training")
```

**Note**: `monitored_validate()` remains focused on metrics extraction only
(`_extract_and_record_metrics()`). It is NOT the right hook for grow iteration progress because
it cannot access the loop variables from the outer `grow_network()` scope.

**Effort**: Small (1–2 hours)

### 2.5 Fix: Show Hidden Units Progress Ratio

**Repository**: juniper-canopy

**File**: `src/frontend/components/metrics_panel.py`

The "Hidden Units" stat card currently shows only the current count. Since `max_hidden_units` is
available from `/api/status`, display it as a ratio: `"3 / 1000"`.

This requires passing the `max_hidden_units` value from the status response to the stat card
update handler.

**File**: `src/frontend/dashboard_manager.py`

The status bar already shows Hidden Units as a plain number. Update to show the ratio when
`max_hidden_units > 0`.

**Effort**: Trivial (15 minutes)

---

## 3. Issue 2: Dataset View Tab — Empty Scatter Plot in Service Mode

### 3.1 Problem

The Dataset View tab always shows "No data available" when connected to an external CasCor
instance. The scatter plot requires `inputs` (feature arrays) and `targets` (class labels), but
CasCor's `/v1/dataset` endpoint returns only metadata (`loaded`, `train_samples`, `test_samples`,
`input_features`, `output_features`).

### 3.2 Root Cause

CasCor's `TrainingLifecycleManager.get_dataset()` (manager.py:504-514) returns metadata derived
from `self._train_x` and `self._train_y` tensor shapes, but does **not serialize the tensor data
itself**. The tensors are available in memory as `self._train_x` (training inputs) and
`self._train_y` (training targets / one-hot encoded).

Demo mode works because `DemoBackend.get_dataset()` (demo_backend.py:182-199) includes `inputs`
and `targets` arrays directly.

### 3.3 Fix: Add Dataset Data Endpoint to CasCor

**Approach**: Add a separate `/v1/dataset/data` endpoint that returns the actual data arrays.
This keeps the metadata-only `/v1/dataset` lightweight (it may be polled frequently) while making
the array data available on demand.

#### 3.3.1 juniper-cascor — Add endpoint and manager method

**File**: `src/api/lifecycle/manager.py`

Add a `get_dataset_data()` method:

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

**File**: `src/api/routes/dataset.py`

Add the data endpoint:

```python
@router.get("/data")
async def get_dataset_data(request: Request) -> dict:
    """Get dataset arrays for visualization."""
    lifecycle = _get_lifecycle(request)
    data = lifecycle.get_dataset_data()
    if data is None:
        raise HTTPException(status_code=404, detail="No dataset loaded")
    return success_response(data)
```

#### 3.3.2 juniper-cascor-client — Add client method

**File**: `juniper_cascor_client/client.py`

```python
def get_dataset_data(self) -> Dict[str, Any]:
    """Get dataset arrays for visualization."""
    return self._get("/dataset/data")
```

#### 3.3.3 juniper-canopy — Fetch and map dataset data

**File**: `src/backend/cascor_service_adapter.py`

Add a method to fetch dataset data arrays:

```python
def get_dataset_data(self) -> Optional[Dict[str, Any]]:
    """Fetch dataset arrays from CasCor for scatter plot visualization."""
    try:
        result = self._unwrap_response(self._client.get_dataset_data())
        if not result:
            return None
        inputs = result.get("train_x", [])
        targets_raw = result.get("train_y", [])
        # Convert targets to class indices.
        # CasCor stores train_y as 2D tensor:
        #   Binary (output_size=1): [[0.0], [1.0], ...] — threshold at 0.5
        #   Multi-class (output_size>1): [[1,0,0], [0,1,0], ...] — argmax
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

> **⚠️ Critical Design Note — Binary Classification Target Conversion**
>
> CasCor stores `train_y` as a 2D tensor with shape `(n_samples, output_size)`. For binary
> classification (`output_size=1`), each row is `[0.0]` or `[1.0]`. A naive `argmax` of a
> single-element list **always returns 0** regardless of the value, because there is only one
> index. The conversion MUST branch on `output_size`:
>
> - `output_size == 1`: threshold at 0.5 → `int(row[0] >= 0.5)`
> - `output_size > 1`: standard argmax

**File**: `src/backend/service_backend.py`

Update `get_dataset()` to merge data arrays when available:

```python
def get_dataset(self) -> Optional[Dict[str, Any]]:
    raw = self._adapter.get_dataset_info()
    if not raw:
        return None
    result = {
        "num_samples": raw.get("train_samples", 0) + raw.get("test_samples", 0),
        "num_features": raw.get("input_features", 0),
        "num_classes": raw.get("output_features", 0),
        ...
    }
    # Fetch data arrays for scatter plot (only when dataset tab is active)
    data_arrays = self._adapter.get_dataset_data()
    if data_arrays:
        result["inputs"] = data_arrays["inputs"]
        result["targets"] = data_arrays["targets"]
    return result
```

**Note**: The dataset data fetch should be guarded to avoid unnecessary large payload transfers
on every poll cycle. The dashboard already only fetches dataset data when the Dataset tab is
active (`_update_dataset_store_handler` checks `active_tab != "dataset"`).

#### 3.3.4 Payload Size Consideration

For a typical spiral dataset (200 samples × 2 features), the JSON payload is ~5-10 KB — negligible.
For larger datasets, consider adding a `max_samples` query parameter to cap the response.

**Effort**: Small–Medium (1–2 hours across 3 repos)

---

## 4. Issue 3: Network Topology Tab — Breaks After First Hidden Unit

### 4.1 Problem

The Network Topology tab renders correctly with zero hidden units but breaks (shows empty or
incomplete graph) after the first hidden unit is added during cascade correlation training.

### 4.2 Root Cause

**Bug in `_transform_topology()`** (cascor_service_adapter.py:596-610): The output weight
connection builder treats CasCor's `output_weights` matrix as **row-per-output-neuron**, but
CasCor stores it as **row-per-input-feature** (shape `(input_size + num_hidden, output_size)`).

CasCor's `output_weights` tensor (2D, shape `(input_size + num_hidden, output_size)`) serializes
via `.tolist()` as:

| Network State                 | Tensor Shape | `.tolist()`                                                  |
|-------------------------------|--------------|--------------------------------------------------------------|
| 0 hidden, 2 inputs, 1 output  | `(2, 1)`     | `[[-0.80], [-0.77]]`                                         |
| 1 hidden, 2 inputs, 1 output  | `(3, 1)`     | `[[-0.15], [0.86], [0.22]]`                                  |
| 2 hidden, 2 inputs, 2 outputs | `(4, 2)`     | `[[-0.23, 0.73], [1.22, 0.53], [0.11, -0.45], [0.88, 0.12]]` |

The bug: `output_weights[o]` was interpreted as "all weights for output neuron `o`", but it is
actually "input feature `o`'s weight to each output neuron". For the common single-output case,
`output_weights[0] = [-0.15]` (length 1), so the code could only create 1 connection instead
of `input_size + num_hidden` connections. Most input→output and hidden→output connections were
silently missing.

### 4.3 Fix Applied

The fix **transposes** the output_weights matrix before indexing by output neuron, so rows become
per-output-neuron (matching what the connection builder expects):

```python
# Transpose output_weights: row-per-input → row-per-output
raw_output_weights = raw.get("output_weights", [])
if raw_output_weights and isinstance(raw_output_weights[0], list):
    n_cols = len(raw_output_weights[0])
    output_weights_t = [
        [raw_output_weights[r][c] for r in range(len(raw_output_weights))]
        for c in range(n_cols)
    ]
else:
    output_weights_t = [raw_output_weights] if raw_output_weights else []
```

### 4.4 Status

**ALREADY FIXED** during investigation. Changes applied to:

| File                                             | Change                                                                                                                                                                                            |
|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `src/backend/cascor_service_adapter.py`          | Transposed `output_weights` matrix before building output connections                                                                                                                             |
| `src/tests/fixtures/cascor_response_fixtures.py` | Updated `real_topology()` fixture to use correct CasCor 2D format `[[0.7], [-0.2], [0.4], [0.1]]`                                                                                                 |
| `src/tests/unit/test_response_normalization.py`  | Fixed `test_transform_topology_empty_network` fixture format. Added `test_transform_topology_output_connections_with_hidden_units` and `test_transform_topology_empty_network_output_connections` |

**Test result**: 32 passed (all topology and normalization tests), 5 pre-existing failures
(unrelated — missing fixtures from prior work, see §5).

---

## 5. Pre-Existing Test Failures

Five tests in `test_response_normalization.py` fail due to missing/stale fixtures predating this
work. These should be fixed as part of this plan:

| Test                                                                    | Failure                                                                      | Root Cause                                                             |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------|
| `TestFix3CurrentMetrics::test_get_current_metrics_unwraps`              | `assert "train_loss" in result` fails — result now has nested `metrics.loss` | Stale assertion from before `_to_dashboard_metric()` was added (FIX-A) |
| `TestFix3CurrentMetrics::test_real_envelope_emits_legacy_metrics_shape` | `NameError: real_training_status_epoch_zero`                                 | Missing fixture function                                               |
| `TestGetStatus::test_epoch_zero_preserved`                              | `NameError: real_training_status_epoch_zero`                                 | Missing fixture function                                               |
| `TestGetStatus::test_hidden_units_zero_preserved`                       | `NameError: real_training_status_epoch_zero`                                 | Missing fixture function                                               |
| `TestFix4GetStatus::test_get_status_partial_nested`                     | `KeyError: 0`                                                                | Test indexes result as list but gets dict                              |

**Fix**: Update stale assertions to expect nested format. Add missing
`real_training_status_epoch_zero()` fixture. Fix `test_get_status_partial_nested` indexing.

**Effort**: Small (30 minutes)

---

## 6. Implementation Order

| Order | Item                                        | Issue  | Effort   | Repo                  | Dependencies |
|-------|---------------------------------------------|--------|----------|-----------------------|--------------|
| 1     | Fix pre-existing test failures              | §5     | 30 min   | juniper-canopy        | None         |
| 2     | Topology fix verification (already applied) | §4     | 0 (done) | juniper-canopy        | None         |
| 3     | Populate `TrainingState` progress fields    | §2.4   | 1–2 hrs  | juniper-cascor        | None         |
| 4     | Hidden units progress ratio display         | §2.5   | 15 min   | juniper-canopy        | None         |
| 5     | Add `/v1/dataset/data` endpoint             | §3.3.1 | 30 min   | juniper-cascor        | None         |
| 6     | Add `get_dataset_data()` client method      | §3.3.2 | 15 min   | juniper-cascor-client | #5           |
| 7     | Wire dataset data into Canopy               | §3.3.3 | 1 hr     | juniper-canopy        | #5, #6       |

Items 1–2 and 3–4 and 5–6 can proceed in parallel across repos.

---

## 7. Verification Plan

### 7.1 Automated Tests

```bash
# juniper-canopy
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda activate JuniperPython
pytest tests/unit/test_response_normalization.py -v  # All 37 must pass (0 failures)
pytest tests/unit/ -v -q                              # Full unit suite

# juniper-cascor
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
conda activate JuniperCascor
pytest src/tests/unit/api/ -v -q                      # All API tests must pass
```

### 7.2 New Tests Required

| Test                                                    | Validates                                                                                          |
|---------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `test_training_state_grow_fields_populated`             | `grow_iteration`, `best_correlation` populated after validate_training hook fires                  |
| `test_dataset_data_endpoint_returns_arrays`             | `/v1/dataset/data` returns `train_x`, `train_y` arrays                                             |
| `test_dataset_data_no_dataset_returns_404`              | `/v1/dataset/data` returns 404 when no dataset loaded                                              |
| `test_service_backend_get_dataset_includes_arrays`      | `ServiceBackend.get_dataset()` includes `inputs`/`targets` when available                          |
| `test_topology_transform_single_output_all_connections` | Output node connects to all inputs + all hidden units for single-output networks                   |
| `test_topology_transform_multi_output`                  | Multiple output neurons each connect to all inputs + hidden units                                  |
| `test_dataset_target_conversion_binary`                 | Binary classification (output_size=1): `[[0.0],[1.0],[0.0]]` → `[0, 1, 0]` (threshold, not argmax) |
| `test_dataset_target_conversion_multiclass`             | Multi-class (output_size=3): `[[1,0,0],[0,1,0]]` → `[0, 1]` (argmax)                               |

### 7.3 Manual Integration Verification

```bash
# Start all three services (same commands as before)
# Terminal 1: juniper-data
# Terminal 2: juniper-cascor (JUNIPER_CASCOR_PORT=8201)
# Terminal 3: juniper-canopy (CASCOR_SERVICE_URL="http://localhost:8201")

# Verify dataset data endpoint
curl -s http://localhost:8201/v1/dataset/data | python3 -m json.tool | head -5
# Expected: {"status": "success", "data": {"train_x": [[...], ...], "train_y": [[...], ...]}}

# Verify canopy dataset includes arrays
curl -s http://localhost:8050/api/dataset | python3 -m json.tool | head -5
# Expected: {"inputs": [[...], ...], "targets": [0, 1, 0, ...], ...}

# Verify training state progress fields (during active training)
curl -s http://localhost:8050/api/state | python3 -m json.tool | grep -E "phase_detail|grow_|best_corr|candidates"
# Expected: non-null values during active training

# Verify topology after hidden unit addition
curl -s http://localhost:8050/api/topology | python3 -m json.tool | grep -c '"to": "output_0"'
# Expected: input_size + num_hidden (all inputs and hidden units connect to output)
```

### 7.4 Visual Verification Checklist

- [ ] Training Metrics: progress detail text shows phase_detail during output training
- [ ] Training Metrics: progress detail shows "Iteration N/M" during grow loop
- [ ] Training Metrics: progress detail shows "Best Corr: X.XXXX" after candidate training
- [ ] Training Metrics: progress detail shows "Candidates: N/M" during candidate phase
- [ ] Training Metrics: Hidden Units stat card shows "N / max" format
- [ ] Dataset View: scatter plot renders with colored class labels in service mode
- [ ] Dataset View: scatter plot matches demo mode appearance for same dataset
- [ ] Network Topology: graph renders correctly with 0 hidden units (inputs → outputs)
- [ ] Network Topology: graph renders correctly after 1st hidden unit addition
- [ ] Network Topology: graph renders correctly after 2nd+ hidden unit (cascade connections visible)
- [ ] Network Topology: all input→output, hidden→output connections present (verify count)

---

## 8. Files Requiring Modification

### 8.1 juniper-cascor

| File                           | Changes                                                                                         |
|--------------------------------|-------------------------------------------------------------------------------------------------|
| `src/api/lifecycle/manager.py` | Populate `TrainingState` progress fields in `monitored_validate()` and `monitored_grow()` hooks |
| `src/api/routes/dataset.py`    | Add `GET /v1/dataset/data` endpoint                                                             |

### 8.2 juniper-cascor-client

| File                              | Changes                         |
|-----------------------------------|---------------------------------|
| `juniper_cascor_client/client.py` | Add `get_dataset_data()` method |

### 8.3 juniper-canopy (implementation required)

| File                                             | Changes                                                          |
|--------------------------------------------------|------------------------------------------------------------------|
| `src/backend/cascor_service_adapter.py`          | Add `get_dataset_data()` method for array fetch                  |
| `src/backend/service_backend.py`                 | Merge dataset arrays into `get_dataset()` response               |
| `src/frontend/components/metrics_panel.py`       | Show `hidden_units / max_hidden_units` in stat card              |
| `src/frontend/dashboard_manager.py`              | Show hidden units ratio in status bar                            |
| `src/tests/unit/test_response_normalization.py`  | Fix 5 pre-existing test failures; add new topology/dataset tests |
| `src/tests/fixtures/cascor_response_fixtures.py` | Add missing `real_training_status_epoch_zero()` fixture          |

### 8.4 juniper-canopy (already fixed during investigation)

| File                                             | Changes                                                          | Status     |
|--------------------------------------------------|------------------------------------------------------------------|------------|
| `src/backend/cascor_service_adapter.py`          | Transposed `output_weights` matrix in `_transform_topology()`    | ✅ Applied |
| `src/tests/fixtures/cascor_response_fixtures.py` | Fixed `real_topology()` fixture to use correct 2D format         | ✅ Applied |
| `src/tests/unit/test_response_normalization.py`  | Added output connection count tests, fixed empty network fixture | ✅ Applied |

### 8.5 Files NOT Requiring Modification

- `src/frontend/components/network_visualizer.py` — consumes transformed topology correctly; bug was in the transformer
- `src/frontend/components/dataset_plotter.py` — already handles `inputs`/`targets` correctly; just needs data
- `src/frontend/components/metrics_panel.py` `_update_progress_detail_handler` — already pre-wired for progress fields

---

*End of Canopy Dashboard Display Fixes Development Plan:*
