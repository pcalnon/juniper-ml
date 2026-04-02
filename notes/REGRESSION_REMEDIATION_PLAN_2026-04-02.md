# Juniper Project: Regression Remediation Plan

**Date**: 2026-04-02
**Reference**: `REGRESSION_ANALYSIS_2026-04-02.md`
**Author**: Claude Code (Principal Engineer Analysis)

---

## Phase 1: Critical Training Failure Fix (CASCOR-001)

### Fix 1A: UnboundLocalError Guard (Immediate — Required)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Lines**: 2714-2715

**Change**: Initialize `candidate_inputs = None` before the `try` block.

```python
# BEFORE (line 2714):
shm_handle = None  # OPT-5: track SharedMemory handle for deferred close
try:

# AFTER:
shm_handle = None  # OPT-5: track SharedMemory handle for deferred close
candidate_inputs = None  # Guard: prevent UnboundLocalError in except handler
try:
```

**Strengths**:
- Single-line fix, zero risk of regression
- The existing handler at line 2788 already checks `if candidate_inputs` — it will now correctly evaluate to `None` → `False` and use the fallback `-1`
- No behavioral change for the success path

**Weaknesses**: None. This is a pure bug fix.

**Risk**: Minimal. The fix only affects the error-handling path.

**Recommendation**: **Apply immediately.**

---

### Fix 1B: SharedMemory Lifecycle Fix (Required — Addresses Root Cause)

The primary exception is `FileNotFoundError` when a worker process tries to attach to a shared memory block that no longer exists.

#### Approach A: Defensive SharedMemory Reconstruction (Recommended)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Lines**: 2846-2864 (`_build_candidate_inputs`)

**Change**: Wrap SharedMemory reconstruction in a try-except that falls back to the legacy tuple-based path.

```python
# In _build_candidate_inputs, lines 2848-2855:
if isinstance(training_inputs, dict):
    try:
        logger.debug(f"... OPT-5 reconstructing tensors from SharedMemory: {training_inputs.get('shm_name')}")
        tensors, shm_handle = SharedTrainingMemory.reconstruct_tensors(training_inputs)
        candidate_input, y, residual_error = tensors
        candidate_epochs = training_inputs["candidate_epochs"]
        candidate_learning_rate = training_inputs["candidate_learning_rate"]
        candidate_display_frequency = training_inputs["candidate_display_frequency"]
    except (FileNotFoundError, OSError) as shm_err:
        logger.warning(f"... OPT-5 SharedMemory unavailable ({shm_err}), falling back to serialized tensors")
        # Fall back to legacy serialized path if SharedMemory is unavailable
        fallback = training_inputs.get("_fallback_tensors")
        if fallback is None:
            raise  # No fallback available, re-raise
        candidate_input, candidate_epochs, y, residual_error, candidate_learning_rate, candidate_display_frequency = fallback
else:
    # Legacy tuple path (unchanged)
    ...
```

**Additionally**: Modify `_generate_candidate_tasks()` to include `_fallback_tensors` as a tuple in the training_inputs dict, providing a serialized fallback.

**Strengths**:
- Graceful degradation: training continues even if SharedMemory fails
- No data loss — falls back to pre-OPT-5 behavior
- Captures the failure scenario and logs it for diagnosis

**Weaknesses**:
- Slightly increases task payload size (carries both SharedMemory metadata and fallback tensors)
- Masks the underlying SharedMemory issue (but logs a warning)

**Risk**: Low. The fallback path is the pre-OPT-5 code path that worked reliably.

#### Approach B: Fix SharedMemory Lifecycle Directly

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: SharedTrainingMemory class and `_execute_candidate_training()`

**Change**: Ensure the SharedMemory block is not cleaned up until all workers have completed. Currently, the `atexit` handler or early cleanup may destroy the block before workers attach.

- Move `SharedTrainingMemory.cleanup()` to after `_collect_results()` completes
- Add reference counting to SharedTrainingMemory
- Use a `try-finally` to guarantee cleanup happens after worker completion

**Strengths**:
- Fixes the root cause directly
- No performance overhead from carrying fallback data

**Weaknesses**:
- Higher complexity; requires understanding the full multiprocessing lifecycle
- Risk of shared memory leaks if cleanup doesn't execute (process killed)
- May not cover all edge cases (e.g., worker crash before attach)

**Risk**: Medium. Multiprocessing shared memory lifecycle is subtle.

#### Approach C: Disable OPT-5 Temporarily

**Change**: Set a flag to bypass SharedMemory and always use the legacy tuple path.

**Strengths**: Fastest fix, guaranteed to work.
**Weaknesses**: Loses OPT-5 performance gains (zero-copy tensor sharing).
**Risk**: None, but sacrifices optimization.

**Recommendation**: **Apply Approach A (defensive fallback) combined with Fix 1A.** This provides immediate resilience while preserving OPT-5 when SharedMemory works. Approach B should be pursued as a follow-up to properly fix the SharedMemory lifecycle.

---

## Phase 2: Canopy UI Fixes

### Fix 2.1: Tab Ordering (CANOPY-001)

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`
**Lines**: 1075-1135

**Change**: Reorder the `dbc.Tab()` entries and update labels:

```
1. Training Metrics    (tab_id="metrics")
2. Candidate Metrics   (tab_id="candidates")
3. Network Topology    (tab_id="topology")
4. Decision Boundary   (tab_id="boundaries")     ← label changed from "Decision Boundaries"
5. Dataset View        (tab_id="dataset")
6. Workers             (tab_id="workers")         ← moved from position 9
7. Parameters          (tab_id="parameters")      ← moved from position 11
8. Snapshots           (tab_id="snapshots")        ← label changed from "HDF5 Snapshots"
9. Redis               (tab_id="redis")
10. Cassandra          (tab_id="cassandra")
11. Tutorial           (tab_id="tutorial")         ← moved from position 12
12. About              (tab_id="about")            ← moved from position 10
```

**Also update** `TAB_SIDEBAR_CONFIG` if tab_id ordering affects sidebar visibility.

**Risk**: Low. Pure layout change. Must update any tests that assert tab order.

---

### Fix 2.2: Cassandra Panel API URL (CANOPY-016)

**File**: `juniper-canopy/src/frontend/components/cassandra_panel.py`
**Lines**: 98-113

**Change**: Replace the broken `_api_url` with one that builds absolute URLs using Flask request context, matching `dashboard_manager.py`'s approach:

```python
def _api_url(self, path: str) -> str:
    from flask import request
    from urllib.parse import urljoin
    origin = f"{request.scheme}://{request.host}"
    return urljoin(f"{origin}/", path.lstrip("/"))
```

**Apply same fix to**: `redis_panel.py`, `worker_panel.py`, `candidate_metrics_panel.py`

**Alternative**: Extract `_api_url` to `BaseComponent` so all components inherit it consistently.

**Recommendation**: Extract to `BaseComponent` for DRY principle. All component panels should use the same URL construction logic.

**Risk**: Low. Straightforward URL fix.

---

### Fix 2.3: Snapshots Tab Naming (CANOPY-015)

**Files**:
- `src/frontend/dashboard_manager.py` line 1102: Change `label="HDF5 Snapshots"` → `label="Snapshots"`
- `src/frontend/components/hdf5_snapshots_panel.py` line 110: Change `"HDF5 Snapshots"` → `"Snapshots"`

**Additionally**: Move Refresh button and status message to "Available Snapshots" section heading.

**Risk**: Low. Label/layout changes only.

---

### Fix 2.4: Network Information Data Binding (CANOPY-005, CANOPY-006)

**File**: `src/frontend/dashboard_manager.py`
**Lines**: 2183-2256

**Issue**: `/api/status` doesn't return `input_size` and `output_size`.

**Approach A (Recommended)**: Add `input_size` and `output_size` to the `/api/status` response in `main.py`. These values come from the network topology and should be included in status.

**Approach B**: Fetch from `/api/topology` in the network info handler instead of `/api/status`.

**Risk**: Low. Data plumbing change.

---

### Fix 2.5: Dataset Sidebar Dynamic Fields (CANOPY-013)

**File**: `src/frontend/dashboard_manager.py`
**Lines**: 721-790

**Change**:
1. Rename heading from "Spiral Dataset" → "Current Dataset"
2. Use a dynamic container (e.g., `html.Div(id="dataset-params-container")`) instead of hardcoded spiral fields
3. Add callback to populate fields based on selected dataset type

**Risk**: Medium. Requires new callback logic and potentially new component patterns. Must ensure existing spiral parameter IDs are preserved for backward compatibility.

---

### Fix 2.6: Dataset Dropdown Population (CANOPY-012)

**File**: `src/frontend/components/dataset_plotter.py`
**Lines**: 102-108

**Change**: Add a callback that fetches available generators from the juniper-data service (or demo backend) and populates the dropdown options.

```python
@app.callback(
    Output(f"{self.component_id}-dataset-selector", "options"),
    Output(f"{self.component_id}-dataset-selector", "value"),
    Input("fast-update-interval", "n_intervals"),  # or on initial load
)
def populate_dataset_dropdown(n):
    generators = data_client.list_generators()
    options = [{"label": g["name"].title(), "value": g["name"]} for g in generators]
    current = current_dataset_name or (options[0]["value"] if options else None)
    return options, current
```

**Risk**: Medium. Requires integration with juniper-data-client.

---

### Fix 2.7: Dark Mode Card/Table Styling (CANOPY-017, CANOPY-018, CANOPY-019)

**File**: `src/frontend/assets/dark_mode.css`

**Change**: Add explicit dark mode rules for Bootstrap card components:

```css
/* Card dark mode */
.dark-mode .card {
    background-color: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
}

.dark-mode .card-header {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
}

.dark-mode .card-body {
    background-color: var(--bg-card) !important;
    color: var(--text-color) !important;
}
```

**For Plotly graphs** (candidate loss empty state): Apply `plotly_dark` template or set `paper_bgcolor` and `plot_bgcolor` to dark mode values when theme is dark.

**Risk**: Low. CSS-only changes. Must verify no unintended style overrides.

---

### Fix 2.8: Decision Boundary / Dataset View Aspect Ratio (CANOPY-010, CANOPY-011)

**Files**:
- `src/frontend/components/decision_boundary.py` line 150
- `src/frontend/components/dataset_plotter.py` lines 218-229

**Change**: Use `aspectRatio` constraints or responsive sizing:

```python
style={"height": "70vh", "maxHeight": "800px", "minHeight": "400px"}
```

Or use Plotly's `autosize=True` with layout constraints:
```python
fig.update_layout(
    autosize=True,
    height=None,  # Let container determine
    yaxis=dict(scaleanchor="x", scaleratio=1),  # 1:1 aspect ratio
)
```

**Risk**: Low. Visual change only.

---

### Fix 2.9: Network Topology Output Nodes (CANOPY-009)

**File**: `src/frontend/components/network_visualizer.py` line 614

**Root Cause Diagnosis Needed**: Verify what `output_units` value the backend returns. For the two-spiral binary classification problem:
- If using sigmoid output: 1 output node is correct
- If using softmax output: 2 output nodes is correct

**Action**: Verify cascor network configuration and ensure canopy correctly reads the actual output dimension rather than a mismatched default.

**Risk**: Low, but requires backend verification.

---

### Fix 2.10: Decision Boundary Historical Replay (CANOPY-010 Enhancement)

**Change**: Add a slider or stepper control that allows viewing the decision boundary at each hidden node addition step. Requires:
1. Backend to store/return decision boundary history per hidden unit count
2. Frontend slider/stepper component
3. Callback to update boundary plot on slider change

**Risk**: Medium. New feature, not a bug fix. Requires backend API changes.

---

### Fix 2.11: Generate Dataset Workflow (CANOPY-014)

**Change**: Implement the full dataset generation workflow:
1. Stop training when new dataset is requested
2. Call juniper-data-client to generate dataset
3. Display new dataset in scatter plot
4. Update Feature Distributions
5. Check neural network compatibility (input dimensions match)
6. If compatible: allow training restart
7. If incompatible: show modal prompting user to fix or start new training

**Risk**: High. Multi-step workflow spanning frontend and backend. Requires careful state management.

---

## Phase 3: Validation

All fixes must be validated through:
1. Unit test execution for affected modules
2. Integration test execution for API endpoints
3. Manual visual verification for UI/dark mode changes
4. Full regression test suite pass for both applications

---

## Risk Assessment Summary

| Fix | Risk | Complexity | Dependencies |
|-----|------|-----------|-------------|
| 1A: UnboundLocalError guard | Minimal | Trivial | None |
| 1B-A: SharedMemory fallback | Low | Low | Fix 1A |
| 2.1: Tab ordering | Low | Low | None |
| 2.2: Cassandra API URL | Low | Low | None |
| 2.3: Snapshots naming | Low | Trivial | Fix 2.1 |
| 2.4: Network info data | Low | Low | Backend API |
| 2.5: Dataset sidebar dynamic | Medium | Medium | Fix 2.6 |
| 2.6: Dataset dropdown | Medium | Medium | juniper-data-client |
| 2.7: Dark mode CSS | Low | Low | None |
| 2.8: Aspect ratio | Low | Low | None |
| 2.9: Output nodes | Low | Low | Backend verification |
| 2.10: Boundary replay | Medium | High | Backend API changes |
| 2.11: Generate dataset workflow | High | High | Fixes 2.5, 2.6 |
