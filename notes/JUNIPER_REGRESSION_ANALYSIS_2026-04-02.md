# Juniper Project Regression Analysis

**Date**: 2026-04-02
**Affected Applications**: juniper-cascor, juniper-canopy
**Severity**: CRITICAL (training pipeline blocked)
**Author**: Claude Code (Opus 4.6)

---

## Executive Summary

The Juniper project has experienced critical regressions across its two primary applications:

1. **juniper-cascor**: Training fails catastrophically shortly after the first epoch begins, caused by a SharedMemory race condition introduced in OPT-5 (shared memory training tensors), compounded by an UnboundLocalError in the error handler.
2. **juniper-canopy**: Multiple UI regressions including stalled progress indicators, incorrect parameter values, dark mode styling gaps, and missing feature implementations.

The cascor training failure is the root cause of many canopy display issues — when training fails, the backend reports "Failed" status, metrics stop updating, and network information returns zeros.

---

## SECTION 1: CRITICAL — juniper-cascor Training Failure

### 1.1 Symptom

A running juniper-cascor instance fails shortly after beginning the first epoch of `grow_network()`. The canopy dashboard status bar shows "Failed".

### 1.2 Root Cause: OPT-5 SharedMemory Premature Cleanup + UnboundLocalError

**Two interacting defects produce the failure:**

#### Defect 1: SharedMemory Premature Cleanup (PRIMARY)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: `_execute_parallel_training()` lines 2129-2135

The `finally` block in `_execute_parallel_training()` unconditionally unlinks SharedMemory blocks:

```python
# Line 2129-2135
finally:
    for shm_block in list(self._active_shm_blocks):
        try:
            shm_block.close_and_unlink()
            self._active_shm_blocks.remove(shm_block)
        except Exception as shm_e:
            ...
```

When parallel training fails and the system falls back to sequential training (line 1977 in `_execute_candidate_training()`), the sequential workers attempt to reconstruct tensors from SharedMemory blocks that have already been unlinked:

```python
# Line 2854 in _build_candidate_inputs()
tensors, shm_handle = SharedTrainingMemory.reconstruct_tensors(training_inputs)
```

This produces: `FileNotFoundError: [Errno 2] No such file or directory: '/juniper_train_cbee87b2'`

#### Defect 2: UnboundLocalError in Error Handler (SECONDARY)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: `train_candidate_worker()` lines 2785-2801

When the FileNotFoundError propagates from `_build_candidate_inputs()`, the exception handler at line 2790 references `candidate_inputs`. A guard was added at line 2716 (`candidate_inputs = None`), but **the deployed code generating the log errors did NOT have this guard**. The guard was added after the error was observed.

**Log evidence** (lines 27738-27740):
```
FileNotFoundError: [Errno 2] No such file or directory: '/juniper_train_cbee87b2'

[cascade_correlation.py: _execute_sequential_training:2149] [ERROR]
Task error: cannot access local variable 'candidate_inputs' where it is not associated with a value
```

#### Even with the guard fix, Defect 1 persists

With `candidate_inputs = None`, the error handler returns `CandidateTrainingResult(success=False, ...)` instead of crashing. But ALL sequential candidates still fail because the SharedMemory blocks are gone. Result: no viable candidates → training loop breaks → FSM transitions to FAILED → canopy shows "Failed".

### 1.3 Complete Failure Chain

```
1. fit() → grow_network() → _get_training_results() → train_candidates()
2. train_candidates() → _execute_candidate_training()
3. _execute_candidate_training() tries distributed training via TaskDistributor
4. _execute_parallel_training() is called → workers process tasks
5. Result collection times out or returns 0 results (line 27683-27684 in logs)
6. _execute_parallel_training()'s FINALLY block unlinks SharedMemory blocks
7. _execute_candidate_training() catches RuntimeError, falls back to sequential
8. _execute_sequential_training() calls train_candidate_worker() for each task
9. train_candidate_worker() → _build_candidate_inputs() → SharedMemory.reconstruct_tensors()
10. SharedMemory block '/juniper_train_cbee87b2' is already unlinked → FileNotFoundError
11. _fallback_tensors not populated → re-raises FileNotFoundError
12. Error handler triggers UnboundLocalError (or returns dummy result with guard)
13. ALL sequential candidates fail → no viable candidate found
14. grow_network() breaks → training terminates → FSM → FAILED state
```

### 1.4 Triggering Conditions

The failure occurs when:
- Parallel training via TaskDistributor returns zero results (timeout, worker crash, etc.)
- The system attempts its sequential fallback path
- OPT-5 SharedMemory is active (which is always the case in current code)

### 1.5 Commit That Introduced the Regression

**Commit**: `f603f1b` — `feat: implement OPT-5 for shared memory training tensors`

This commit introduced:
- `SharedTrainingMemory` class (lines 217-358)
- SharedMemory metadata dicts in `_generate_candidate_tasks()`
- SharedMemory cleanup in `_execute_parallel_training()` finally block
- SharedMemory reconstruction in `_build_candidate_inputs()`

The partial fix was in:
**Commit**: `db2f1a6` — `fix: resolve resource tracker KeyErrors and test warnings (#58)`
- Added `candidate_inputs = None` guard (line 2716)
- Changed SharedMemory to `track=False` to avoid resource tracker warnings
- **Did NOT fix the premature cleanup issue**

### 1.6 Log Evidence

**File**: `juniper-cascor/logs/juniper_cascor.log`

| Log Line | Timestamp | Level | Message |
|----------|-----------|-------|---------|
| 27683 | 08:57:24 | WARNING | `_collect_training_results: Result queue empty, continuing` |
| 27684 | 08:57:24 | WARNING | `TaskDistributor returned no results, falling back to sequential` |
| 27685 | 08:57:24 | ERROR | `TaskDistributor failed to return results` |
| 27691 | 08:57:24 | WARNING | `Parallel training failed, falling back to sequential training` |
| 27700 | 08:57:24 | ERROR | `[Errno 2] No such file or directory: '/juniper_train_cbee87b2'` |
| 27740 | 08:57:24 | ERROR | `Task error: cannot access local variable 'candidate_inputs'` |
| 27832 | 08:57:24 | ERROR | Same error — repeated for each pool candidate |
| 27883 | 08:57:24 | ERROR | Same error — repeated for each pool candidate |
| 27931 | 08:57:25 | ERROR | Same error — repeated for each pool candidate |
| 27975 | 08:57:25 | ERROR | Same error — repeated for each pool candidate |

---

## SECTION 2: juniper-canopy UI Regressions

### 2.1 Tab Ordering

**Current order** (dashboard_manager.py lines 1075-1134):
Training Metrics → Candidate Metrics → Network Topology → Decision Boundary → Dataset View → Workers → Parameters → Snapshots → Redis → Cassandra → Tutorial → About

**Expected order**:
Training Metrics → Candidate Metrics → Network Topology → Decision Boundary → Dataset View → Workers → Parameters → HDF5 Snapshots → Redis → Cassandra → Tutorial → About

**Status**: Tab order in current source code MATCHES expected order. The label "Snapshots" (line 1112) is already the renamed version. **No code change needed** — verify deployed version matches source.

### 2.2 Status Bar Shows "Failed"

**Root Cause**: Cascor training failure (Section 1) → FSM state = "FAILED" → `service_backend.py` line 118: `"failed": status_upper == "FAILED"` → canopy status bar logic (line 2126): `if is_failed: status = "Failed"`.

**Fix**: Resolve the cascor training failure. The status bar correctly reports backend state.

### 2.3 Training Metrics Tab Issues

#### 2.3.1 Progress Bar Stalls

**Root Cause**: Training failure → no more epochs → no progress updates via WebSocket or REST polling.

#### 2.3.2 Left Menu Network Parameters Show Incorrect Values

**Root Cause**: When in `service` mode, `_init_params_from_backend_handler()` (line 2725) reads from `/api/state`. The `/api/state` endpoint (main.py line 600-632) populates `nn_*`/`cn_*` keys using `setdefault()` with `TrainingConstants` defaults. If cascor does not populate these keys in its training state, canopy falls back to constants.

**File**: `juniper-canopy/src/main.py` lines 605-627
**Issue**: `state.setdefault("nn_max_iterations", TrainingConstants.DEFAULT_MAX_ITERATIONS)` etc. These defaults are only overridden if cascor exposes matching keys via `backend._adapter.get_canopy_params()` (line 630-631). If the adapter doesn't map cascor parameters correctly, defaults persist.

#### 2.3.3 Convergence Threshold Shows Number of Epochs Value

**Root Cause**: The callback Output ordering was verified correct (Output #6 = preset_epochs, Output #7 = convergence_threshold, matching return indices). The issue is therefore in the **backend data source**: when cascor's training state doesn't expose `nn_growth_convergence_threshold`, canopy falls back to `TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD`. If the default convergence threshold constant happens to have the same value as the epochs default, or if `get_canopy_params()` maps the wrong cascor attribute to `nn_growth_convergence_threshold`, the wrong value appears.

**Investigation needed**: Audit `CascorServiceAdapter.get_canopy_params()` to verify the mapping for `nn_growth_convergence_threshold` and `nn_growth_preset_epochs` keys.

#### 2.3.4 Network Information Shows Zeros (Input/Output Nodes)

**Root Cause**: `_update_network_info_handler()` (line 2183) reads `input_size` and `output_size` from `/api/status`. The `service_backend.py` line 134-135 reads these from `training_state`: `ts.get("input_size", 0)`. If the training state doesn't contain these keys (which depends on cascor's state machine broadcasting them), defaults to 0.

**Secondary cause**: When training fails immediately, the network may never populate these fields in its training state broadcast.

#### 2.3.5 Training Loss Graph Incorrect / Training Accuracy Graph Empty

**Root Cause**: Training failure → no/minimal metrics produced → `get_metrics_history()` returns empty or incomplete data → graphs show nothing or stale data.

#### 2.3.6 Learning Rate Mismatch

**Root Cause**: The graph heading area reads learning rate from metrics data, while the left menu reads it from `/api/state` parameter initialization. If these two sources provide different values (metrics from network attribute vs. state from defaults), they'll mismatch.

### 2.4 Candidate Metrics Tab Issues

#### 2.4.1 Progress Bar Stalled

**Root Cause**: Training failure → candidate training never completes → no candidate epoch updates.

#### 2.4.2 No Top Candidate Information

**Root Cause**: Training failure → no candidates trained successfully → `top_candidate_id`, `top_candidate_score` not populated in state.

#### 2.4.3 Pool Training Metrics All Zeros

**Root Cause**: Training failure → `pool_metrics` dict not populated → all values default to 0.0.

#### 2.4.4 Candidate Training Loss Graph Not Populated

**Root Cause**: No successful candidate training → no loss data.

#### 2.4.5 Candidate Loss Graph White Background in Dark Mode

**File**: `juniper-canopy/src/frontend/components/candidate_metrics_panel.py` lines 567-573

```python
fig.update_layout(
    ...
    template="plotly",
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="#ffffff",  # HARDCODED LIGHT COLOR
    ...
)
```

**Root Cause**: `_create_candidate_loss_figure()` does not accept or respond to a theme parameter. Colors are hardcoded to light mode values. The `_create_empty_plot()` method (line 582) correctly accepts a `theme` parameter but the main figure method does not.

### 2.5 Network Topology — Two Output Nodes

**Root Cause**: The default spiral problem uses `_SPIRAL_PROBLEM_NUM_SPIRALS = 2`, which sets `_CASCOR_OUTPUT_SIZE = 2` (one-hot encoding: 2 classes → 2 output nodes). This is **architecturally correct** for the default 2-spiral configuration.

If settings indicate 1 output node, either:
- The user's custom settings aren't being applied to the network
- Or the cascor backend is creating the network with default spiral constants regardless of user settings

**File**: `juniper-cascor/src/cascor_constants/constants_problem/constants_problem.py` line 862:
`_SPIRAL_PROBLEM_OUTPUT_SIZE = _SPIRAL_PROBLEM_NUM_SPIRALS` (= 2)

### 2.6 Decision Boundary Tab

#### 2.6.1 Aspect Ratio

**Current**: `style={"height": "70vh", "maxHeight": "800px", "minHeight": "400px"}` (line 150)
**Issue**: Fixed viewport-relative height doesn't preserve the scatter plot's native aspect ratio. The width stretches to fill the container while height is fixed, causing distortion.
**Enhancement needed**: Use `aspectratio` in Plotly layout or use `scaleanchor`/`scaleratio` on axes.

#### 2.6.2 Historical Visualization / Replay

**Status**: Not implemented. The decision boundary component (`decision_boundary.py`, 452 lines) has no:
- Hidden node slider/selector for viewing boundaries at previous hidden unit counts
- Replay/animation mechanism
- Historical boundary storage

**Enhancement needed**: New feature implementation required.

### 2.7 Dataset View Tab

#### 2.7.1 Aspect Ratio

Similar to Decision Boundary — fixed height doesn't preserve scatter plot aspect ratio.

#### 2.7.2 Dataset Dropdown Not Populated

**File**: `dataset_plotter.py` line 103-104:
```python
options=[],  # Populated dynamically
value=None,
```

The dropdown is initialized empty and should be populated with available dataset generators from juniper-data via a callback. Need to verify if the population callback exists and works correctly.

#### 2.7.3 Dropdown Not Pre-populated with Current Dataset

The `value=None` at line 105 means no default selection. Should be populated with the currently active dataset.

#### 2.7.4 Left Menu Dataset Parameters Section

**Issue**: The sidebar section is labeled "Spiral Dataset" specifically. It should:
- Have a generic heading: "Current Dataset"
- Dynamically show fields appropriate for the selected dataset type
- Update when dataset selection changes

#### 2.7.5 Generate Dataset Workflow

**Issue**: The full workflow (stop training → display new dataset → update distributions → handle compatibility) may not be fully implemented. Requires verification of:
- Stop training on new dataset generation
- Dataset compatibility checking with current network
- User prompting for incompatible datasets

### 2.8 HDF5 Snapshots Tab

#### 2.8.1 Tab Label Rename

**Current**: Label is already "Snapshots" (line 1112 in dashboard_manager.py).
**Status**: Already renamed. **No code change needed.**

#### 2.8.2 Refresh Button Repositioning

**Issue**: Refresh button and status message should be moved to the "Available Snapshots" section heading rather than at the top of the tab.

### 2.9 Cassandra Tab — API URL Error

**File**: `juniper-canopy/src/frontend/components/cassandra_panel.py`

The Cassandra panel makes requests to `/api/v1/cassandra/status` (line 389) and `/api/v1/cassandra/metrics` (line 448). These endpoints exist in `main.py` (lines 1705 and 1725).

The `_api_url()` method (line 99-120) constructs URLs using Flask request context:
```python
from flask import request
origin = f"{request.scheme}://{request.host}"
return urljoin(f"{origin}/", path.lstrip("/"))
```

**Potential Issues**:
1. **Flask vs Dash context**: Cassandra panel uses `flask.request` but the app runs on Dash (which wraps Flask). The request context may not be available during callback execution.
2. **Port mismatch**: If canopy runs on port 8050 but the Cassandra status endpoint is actually proxied through a different service, the URL will be wrong.
3. **Callback context**: During Dash callbacks (which are AJAX requests), `flask.request` may reference the callback endpoint itself rather than the original page URL.

### 2.10 Parameters Tab — Dark Mode

**Issue**: Meta Parameters tables show white background in dark mode.

**Root Cause**: The `parameters_panel.py` component likely renders HTML tables without CSS variable support for dark mode. The `dark_mode.css` may not target the specific table classes used in the parameters panel.

### 2.11 Tutorial Tab — Dark Mode

**Issue**: Dashboard Components and Parameters Reference tables show white background in dark mode.

**Root Cause**: Same as Parameters tab — HTML tables rendered without dark mode CSS class application.

---

## SECTION 3: Issue Classification and Priority

### Priority 1 — CRITICAL (Blocks All Training)

| ID | Issue | Application | Root Cause |
|----|-------|-------------|------------|
| C-1 | SharedMemory premature cleanup | cascor | OPT-5 finally block cleanup timing |
| C-2 | UnboundLocalError in error handler | cascor | Missing variable initialization (partially fixed) |

### Priority 2 — HIGH (Significantly Degrades Monitoring)

| ID | Issue | Application | Root Cause |
|----|-------|-------------|------------|
| H-1 | Status bar shows "Failed" | canopy | Downstream of C-1 |
| H-2 | All progress bars stalled | canopy | Downstream of C-1 |
| H-3 | Network info shows zeros | canopy | Training state not populated |
| H-4 | Parameters show defaults | canopy | Service adapter mapping gap |
| H-5 | Convergence threshold value swap | canopy | Callback output ordering |

### Priority 3 — MEDIUM (UI Polish / Dark Mode)

| ID | Issue | Application | Root Cause |
|----|-------|-------------|------------|
| M-1 | Candidate loss graph white bg in dark mode | canopy | Hardcoded colors |
| M-2 | Parameters tab white bg in dark mode | canopy | Missing CSS targeting |
| M-3 | Tutorial tab white bg in dark mode | canopy | Missing CSS targeting |
| M-4 | Decision boundary aspect ratio | canopy | Fixed height, no aspect lock |
| M-5 | Dataset view aspect ratio | canopy | Fixed height, no aspect lock |
| M-6 | Cassandra API URL error | canopy | Flask context issue |
| M-7 | Snapshots refresh button position | canopy | Layout structure |

### Priority 4 — LOW (Feature Enhancements)

| ID | Issue | Application | Root Cause |
|----|-------|-------------|------------|
| L-1 | Decision boundary history/replay | canopy | Not implemented |
| L-2 | Dataset dropdown population | canopy | Missing juniper-data integration |
| L-3 | Dataset section dynamic fields | canopy | Static "Spiral" heading |
| L-4 | Generate dataset full workflow | canopy | Incomplete workflow logic |
| L-5 | Network topology output nodes | canopy/cascor | Correct behavior (2-spiral default) |

---

## SECTION 4: Dependency Map

```
C-1 (SharedMemory cleanup) ──fixes──> C-2 (error handler)
C-1 ──fixes──> H-1 (Failed status)
C-1 ──fixes──> H-2 (stalled progress)
C-1 ──partially fixes──> H-3 (network info zeros)
C-1 ──partially fixes──> H-4 (parameters defaults)

H-3, H-4 ──require──> Service adapter parameter mapping audit
H-5 ──requires──> Callback output ordering verification

M-1, M-2, M-3 ──independent──> CSS/theme fixes
M-4, M-5 ──independent──> Layout fixes
M-6 ──independent──> API URL construction fix
M-7 ──independent──> Layout restructure

L-1, L-2, L-3, L-4 ──independent──> New feature work
```

---

## SECTION 5: Verification Recommendations

1. **After C-1 fix**: Run cascor training end-to-end; verify training completes first epoch and continues through multiple hidden unit additions
2. **After C-1 fix**: Verify canopy status bar shows "Running" during training
3. **After H-3/H-4 fix**: Verify network info shows correct input/output sizes
4. **After H-5 fix**: Verify convergence threshold field shows the correct value
5. **After M-1/M-2/M-3 fix**: Toggle dark mode and verify all tables and graphs use dark theme
6. **After L-1 implementation**: Verify decision boundary replay with slider control
7. **Full regression test**: Run both application test suites (`pytest` for both repos)
