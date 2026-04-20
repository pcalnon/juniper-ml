# Cross-Project Regression Analysis

**Date**: 2026-04-03
**Author**: Claude Code (Principal Engineer Role)
**Scope**: juniper-cascor, juniper-canopy, juniper-cascor-client
**Status**: Active Investigation

---

## Executive Summary

Four critical regressions have been identified across the Juniper ecosystem. The most severe is a training convergence failure in juniper-cascor caused by a bug in the `grow_network()` loop that prevents early stopping state from propagating between epochs. The remaining three regressions are in juniper-canopy: semantic confusion between epochs and iterations, undersized plot cards, and flaky parameter updates.

---

## Regression 1: Training Stalling Before Target Accuracy/Loss (CRITICAL)

### Symptom

Training runs fail to converge to target accuracy and loss values. The cascade correlation network grows indefinitely or terminates on correlation threshold rather than on validation-based early stopping.

### Root Cause

**File**: `/juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: `grow_network()` method, lines 3576-3696

The `patience_counter` and `best_value_loss` loop state variables are **never updated** with the values returned from `validate_training()`. A TODO comment at line 3581 explicitly acknowledges this as a known bug:

```python
# TODO: validate_training_results bug: needs to be fixed
```

#### Detailed Evidence

1. **Initialization** (line 3544-3545): `patience_counter=0`, `best_value_loss=float("inf")` are passed into `grow_network()` as parameters.

2. **Loop body** (lines 3650-3662): Each epoch creates `ValidateTrainingInputs` using the **same unchanged** `patience_counter` and `best_value_loss` values.

3. **Validation call** (line 3667): `validate_training()` correctly computes updated patience and best loss values via `evaluate_early_stopping()` -> `check_patience()`.

4. **Missing update** (after line 3677): The code logs the results and checks `early_stop`, but **never assigns**:
   ```python
   # MISSING:
   patience_counter = validate_training_results.patience_counter
   best_value_loss = validate_training_results.best_value_loss
   ```

5. **Consequence**: Every epoch, `check_patience()` receives `patience_counter=0` and `best_value_loss=inf`. The patience counter resets every iteration, making patience-based early stopping impossible.

#### Why Training Still Terminates (Eventually)

Training does eventually stop via one of these non-patience mechanisms:
- **Correlation threshold** (line 3602): `training_results.best_candidate.get_correlation() < self.correlation_threshold` -- but with threshold at 0.0005, almost all candidates pass.
- **Max hidden units** (checked in `evaluate_early_stopping()`): `len(self.hidden_units) >= max_hidden_units`.
- **Target accuracy** (checked in `evaluate_early_stopping()`): `train_accuracy >= 0.999`.
- **Null training results** (line 3597-3598): If candidate training returns None.

None of these are as effective as patience-based early stopping for detecting convergence stalls where loss stops improving but accuracy hasn't reached the target.

### Impact

- **Severity**: CRITICAL -- blocks all further development
- Training runs that should converge in 20-50 growth iterations instead run to the max hidden units limit
- Wastes compute time and produces suboptimal network architectures
- The network overfits by adding unnecessary hidden units

### Configuration Context

Default values in `constants_model.py`:
| Parameter | Default | Effect |
|-----------|---------|--------|
| `_PROJECT_MODEL_EPOCHS_MAX` | 10000 | Very high growth iteration limit |
| `_PROJECT_MODEL_OUTPUT_EPOCHS` | 10000 | High per-output retraining epoch count |
| `_PROJECT_MODEL_CORRELATION_THRESHOLD` | 0.0005 | Extremely permissive -- nearly all candidates pass |
| `_PROJECT_MODEL_PATIENCE` | 50 | Never enforced due to bug |
| `_PROJECT_MODEL_CONVERGENCE_THRESHOLD` | 0.001 | Tiny improvement threshold -- never checked |

---

## Regression 2: Epoch/Iteration Semantic Confusion (HIGH)

### Symptom

The juniper-canopy monitoring dashboard misrepresents training progress. Users cannot distinguish between:
- **Epoch**: A single pass through the training data
- **Iteration**: One complete candidate node addition + one complete network output training (associated with network growth)

### Root Causes

#### RC-1: Wrong Values Passed to Growth Callback (juniper-cascor)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`, lines 3613-3615

```python
_grow_cb(
    iteration=epoch,           # BUG: 'epoch' is the loop variable for growth iterations
    max_iterations=max_epochs, # BUG: 'max_epochs' is the max growth iterations param
    ...
)
```

The `grow_network()` loop variable is named `epoch` (line 3587: `for epoch in range(max_epochs):`), but it actually represents **growth iterations** (each loop body adds a hidden unit). The parameter `max_epochs` passed to `grow_network()` from `fit()` actually represents the maximum number of growth iterations, not data epochs.

This mislabeling propagates through:
- `manager.py:353-356` -- `_grow_iteration_callback()` receives incorrect values
- `monitor.py:67,98` -- TrainingState stores as `grow_iteration` and `grow_max`
- WebSocket messages to juniper-canopy

#### RC-2: Inconsistent Parameter Naming (juniper-canopy)

**File**: `juniper-canopy/src/main.py`, lines 573-626

| Parameter Name | Actual Meaning | Confusion |
|----------------|----------------|-----------|
| `nn_max_iterations` | Max growth iterations | "iterations" is ambiguous |
| `nn_max_total_epochs` | Max output training epochs | Not "total" epochs of anything |
| `cn_training_iterations` | Candidate training epochs | Should be "epochs" not "iterations" |
| `nn_growth_preset_epochs` | Growth epoch threshold | Ambiguous relationship to growth |

#### RC-3: Display Labels (juniper-canopy)

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`, line 1122

```python
parts.append(f"Candidate Epoch: {cand_epoch}/{cand_total_epochs} ({pct}%)")
```

While "Candidate Epoch" is technically correct (it's counting data passes during candidate training), the surrounding context uses "epoch" and "iteration" interchangeably, causing confusion.

#### RC-4: Constants Naming (juniper-canopy)

**File**: `juniper-canopy/src/canopy_constants.py`, line 47

```python
DEFAULT_MAX_ITERATIONS: Final[int] = 1000
```

Vague -- should specify this means max growth iterations.

### Impact

- **Severity**: HIGH -- renders monitoring dashboard unusable for understanding training progress
- Users cannot determine whether the network is growing (adding units) or simply training existing weights
- Progress metrics are misleading

---

## Regression 3: Plot Card Heights Too Small (MEDIUM)

### Symptom

Data distribution plots and decision boundary plots are too small to effectively visualize training data and network decision regions.

### Current State

| Component | Element | Current Height | File:Line |
|-----------|---------|---------------|-----------|
| Dataset Plotter | Scatter plot | 600px | `dataset_plotter.py:222` |
| Dataset Plotter | Distribution plot | 25vh (max 350px) | `dataset_plotter.py:228` |
| Dataset Plotter | Figure layout | 300px | `dataset_plotter.py:535` |
| Decision Boundary | Boundary plot | 600px | `decision_boundary.py:150` |
| CSS Global | Plotly min-height | 300px | `plotly_fix.css:16` |
| CSS Global | Tab pane min-height | 400px | `plotly_fix.css:66` |

### Analysis

Both scatter and decision boundary plots use fixed `600px` height with `maxWidth: 700px`. Aspect ratio is maintained via Plotly's `yaxis={"scaleanchor": "x", "scaleratio": 1}`.

The plots occupy a `dbc.Col(width=9)` container (75% of page width, ~900px at desktop). The fixed 600px height with 700px max width creates an undersized visualization area that makes it difficult to distinguish overlapping data points and decision regions in complex datasets like two-spiral.

### Impact

- **Severity**: MEDIUM -- affects usability of monitoring but not training correctness
- Small plot sizes make it difficult to visually assess decision boundary quality
- Data point clusters overlap and become indistinguishable

---

## Regression 4: Parameter Update Flakiness (CRITICAL)

### Symptom

Two distinct failures:
1. Parameter value updates are not always successful when submitted
2. Updated parameter values are frequently not reflected in status displays

### Root Causes

#### RC-1: Synchronous Backend Call in Async Context

**File**: `juniper-canopy/src/main.py`, line 2042

```python
# Inside async function api_set_params():
backend.apply_params(**backend_updates)  # SYNC call -- no await
await websocket_manager.broadcast(...)   # Broadcast runs before apply completes
return {"status": "success", ...}        # Returns success prematurely
```

`backend.apply_params()` is synchronous. In an async context, this doesn't block the event loop, so the WebSocket broadcast and HTTP response can execute before the parameter application completes. When `apply_params()` is slow (e.g., making an HTTP call to juniper-cascor), the frontend shows success while the backend is still processing.

#### RC-2: Incomplete State Synchronization

**File**: `juniper-canopy/src/main.py`, lines 2038-2046

Only 3 of 22+ parameters are synced to `TrainingState`:
- `learning_rate`
- `max_hidden_units`
- `max_epochs`

The WebSocket broadcast (line 2046) sends only `training_state.get_state()`, which excludes the other 19+ parameters (`cn_pool_size`, `cn_correlation_threshold`, `nn_max_iterations`, etc.). These never appear in real-time status updates.

#### RC-3: CasCor Service Connection Failure

**File**: `juniper-cascor-client/juniper_cascor_client/client.py`, line 76

```python
# WRONG key path:
return result.get("data", {}).get("network_loaded", False)

# Server actually returns:
ReadinessResponse(details={"network_loaded": ...})  # "details" not "data"
```

`is_ready()` checks for `data.network_loaded` but the server returns `details.network_loaded`. This means `is_ready()` always returns False, and the CasCor service adapter in juniper-canopy cannot establish a connection. Only demo mode works.

Additionally, `connect()` in the CasCor service adapter gates on `is_ready()` (which requires `network_loaded=True`) instead of `is_alive()` (which only requires the server to respond). This creates a timing race where canopy starts before cascor finishes auto-training setup.

#### RC-4: Silent Error Swallowing

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`, lines 441-456

```python
except JuniperCascorClientError as e:
    logger.error(f"Failed to update cascor params: {e}")
    return {"ok": False, "error": str(e)}  # Returned but never checked
```

The error return is never checked by callers (`main.py:2042`, `service_backend.py:197-198`). The frontend shows success regardless.

#### RC-5: Incomplete Parameter Mapping

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`, lines 426-437

Only 10 parameters are mapped in `_CANOPY_TO_CASCOR_PARAM_MAP`. The remaining 12+ parameters (including `cn_training_iterations`, `nn_max_iterations`, `cn_selected_candidates`, etc.) are silently dropped with no warning when forwarding to the CasCor backend.

#### RC-6: WebSocket Broadcast Missing Full Parameter State

**File**: `juniper-canopy/src/main.py`, line 2046

```python
await websocket_manager.broadcast({"type": "state_change", "data": training_state.get_state()})
```

The broadcast includes only `TrainingState` fields (3 params), not the full set of applied parameters. Frontend stores that depend on WebSocket updates never receive the complete parameter state.

### Impact

- **Severity**: CRITICAL -- destroys user trust, leaves network in ambiguous state
- Users cannot reliably update training parameters during a run
- Status displays show stale parameter values
- When connected to real CasCor service (not demo), parameter updates silently fail
- No feedback mechanism to inform users of failed updates

---

## Cross-Cutting Observations

### Interaction Between Regressions

1. **Training stalling + parameter flakiness**: Users try to adjust parameters (learning rate, patience) to fix stalling, but updates don't take effect, compounding the problem.
2. **Epoch/iteration confusion + training stalling**: Users misread progress as "epoch 50 of 10000" when it should read "growth iteration 50" -- they don't realize the network is growing too many units rather than training effectively.
3. **Plot sizes + training stalling**: Small plots make it harder to visually confirm that training is actually converging or stalling.

### Shared Architectural Concerns

- **Async/sync boundary**: Multiple async functions call synchronous methods without `await asyncio.to_thread()`, creating potential ordering issues beyond just parameter updates.
- **State consistency**: `TrainingState` is a partial view of the actual state, leading to information loss in WebSocket broadcasts.
- **Error propagation**: Multiple layers silently swallow errors (adapter, backend, main), making debugging difficult.

---

## Verification Status

| Finding | Verified Via | Confidence |
|---------|-------------|------------|
| Patience counter bug | Code read, TODO comment | CONFIRMED |
| Epoch/iteration mislabeling | Code read, callback chain | CONFIRMED |
| Plot heights | Code read, style values | CONFIRMED |
| Sync-in-async issue | Code read, function signatures | CONFIRMED |
| State sync gap | Code read, field comparison | CONFIRMED |
| Key path mismatch | Code read, API contract comparison | CONFIRMED |
| Silent error swallowing | Code read, caller analysis | CONFIRMED |
| Incomplete param mapping | Code read, map vs input comparison | CONFIRMED |
