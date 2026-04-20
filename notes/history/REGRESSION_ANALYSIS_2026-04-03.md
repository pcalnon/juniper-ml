# Juniper Project Regression Analysis

**Date**: 2026-04-03
**Scope**: juniper-cascor, juniper-canopy, juniper-cascor-client
**Author**: Claude Code (Opus 4.6)
**Status**: Active

---

## Executive Summary

Four critical regression areas have been identified across the Juniper project applications. This document provides a rigorous root-cause analysis for each, supported by specific code evidence with file paths and line numbers.

**Regression Areas**:

1. **Training Stalls** (P0 - CRITICAL): Training exits prematurely before reaching target accuracy/loss values
2. **Epoch/Iteration Semantics** (P1 - HIGH): Semantic confusion between epochs and iterations in juniper-canopy display
3. **Plot Card Heights** (P2 - MEDIUM): Data and boundary plots too small
4. **Parameter Update Flakiness** (P1 - HIGH): Unreliable parameter submission and display synchronization

---

## 1. Training Stalls (P0 - CRITICAL)

### Problem Statement

Training in juniper-cascor terminates before accuracy and loss reach target values. This renders the entire platform unusable and blocks all further development.

### Root Cause Chain

Training exits prematurely through **two independent early-exit paths** in `grow_network()`, both caused by miscalibrated thresholds.

#### RC-TRAIN-01: Correlation Threshold Too Low

**File**: `juniper-cascor/src/cascor_constants/constants_model/constants_model.py:440`
```python
_PROJECT_MODEL_CORRELATION_THRESHOLD = 0.0005  # This value was used with 100% run
```

**Evidence**: The file contains commented-out values from 0.05 (original implementation, line 421) down to 0.00001, with 0.0005 selected. A correlation threshold of 0.05% means:

- Candidates with near-zero correlation to the residual error are accepted
- Added hidden units contribute noise rather than useful features
- As the network grows and residual error shrinks, even noise candidates become impossible to find at this threshold
- The check at `cascade_correlation.py:3602` causes premature loop exit:

```python
elif training_results.best_candidate.get_correlation() < self.correlation_threshold:
    self.logger.info(f"... No candidate met correlation threshold: {self.correlation_threshold} ...")
    break  # PREMATURE EXIT PATH #1
```

**Impact**: After 3-5 hidden units are added with low-quality candidates, subsequent candidates cannot exceed even the 0.0005 bar because the residual error has been absorbed by earlier (poor) units. Training breaks out of the loop with insufficient network capacity.

#### RC-TRAIN-02: Early Stopping Patience Semantics in grow_network

**File**: `juniper-cascor/src/cascor_constants/constants_model/constants_model.py:481`
```python
_PROJECT_MODEL_PATIENCE = 50  # This value was used with 100% run
```

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3678-3680`
```python
if validate_training_results.early_stop:
    self.logger.info(f"... Early stopping triggered at epoch {epoch}.")
    break  # PREMATURE EXIT PATH #2
```

**Evidence**: The patience mechanism in `check_patience()` requires validation loss to improve by at least `convergence_threshold` (0.001) within 50 consecutive grow iterations. However:

- Each grow iteration adds a hidden unit and retrains the output layer
- After adding low-quality candidates (RC-TRAIN-01), validation loss improvement is minimal
- Patience=50 sounds generous but each "epoch" in `grow_network` is actually a **full iteration** (candidate training + output retraining), not a data pass
- With low-quality candidates producing marginal improvements, patience exhausts around iteration 10-50

The interaction between RC-TRAIN-01 and RC-TRAIN-02 creates a death spiral: low-quality candidates produce minimal loss improvement, which triggers early stopping before the network has enough capacity to achieve target accuracy.

#### RC-TRAIN-03: grow_network Loop Uses "epoch" Terminology for Iterations

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3587`
```python
for epoch in range(max_epochs):
```

**Evidence**: This loop variable is named `epoch` and bounded by `max_epochs`, but each loop iteration is actually a **growth iteration**: train candidates, add best candidate, retrain output layer. This semantic confusion has downstream effects:

- The `max_epochs` parameter (default 10,000 from constants) actually limits grow iterations, not data passes
- The callback at line 3614 passes `iteration=epoch, max_iterations=max_epochs` - correctly renaming for the callback but the source variable creates confusion
- Log messages like "Early stopping triggered at epoch {epoch}" (line 3679) are misleading - this is iteration-level early stopping, not epoch-level

### Validation

Cross-referencing with existing analysis documents:
- `juniper-canopy/notes/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` identifies 12 root causes (RC-1 through RC-12) for the demo mode. RC-3 (insufficient output retraining), RC-10 (mini-batch undoing retrain), and RC-11 (unnormalized correlation) are relevant. The main cascor code uses full-batch training (RC-10 not applicable) and MSE loss (RC-2 fixed), but the threshold calibration issues persist.
- `juniper-canopy/notes/ROOT_CAUSE_CANDIDATE_QUALITY_DEGRADATION.md` documents candidate quality degradation consistent with RC-TRAIN-01.

### Impact Assessment

| Factor | Impact |
|--------|--------|
| Severity | P0 - Blocks all development |
| Scope | All training workflows (demo + service mode) |
| User Impact | Training never reaches target accuracy |
| Data Impact | None (no data corruption) |
| Reversibility | Configuration change, fully reversible |

---

## 2. Epoch/Iteration Semantics (P1 - HIGH)

### Problem Statement

The juniper-canopy dashboard conflates "epoch" (single pass through training data) with "iteration" (complete candidate node addition + output retraining cycle). This makes the monitoring display confusing and unusable.

### Correct Definitions

- **Epoch**: A single pass through the training data during a specific phase (output training or candidate training)
- **Iteration**: One complete cycle of: candidate pool training + best candidate selection + candidate addition to network + output layer retraining. Each iteration is associated with network growth.

### Root Cause Analysis

#### RC-SEMANT-01: grow_network Loop Variable Named "epoch"

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3587`
```python
for epoch in range(max_epochs):
```

Each iteration of this loop performs a complete candidate-add-retrain cycle. The variable should be `iteration` and the bound should be `max_iterations`. The callback correctly renames it at line 3614 (`iteration=epoch`), but the source code and log messages use "epoch" throughout.

#### RC-SEMANT-02: Callback Passes max_epochs as max_iterations

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3614-3615`
```python
_grow_cb(
    iteration=epoch,          # grow iteration, but sourced from 'epoch' variable
    max_iterations=max_epochs, # max grow iterations, but sourced from 'max_epochs'
    ...
)
```

The values `max_epochs` (default 10,000) is far larger than the expected number of grow iterations (typically 5-50 hidden units). This creates a progress bar that never advances meaningfully (showing "Iteration 5/10000").

#### RC-SEMANT-03: Canopy Displays Grow Iterations Correctly but Context is Wrong

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py:1104-1107`
```python
grow_iter = state.get("grow_iteration")
grow_max = state.get("grow_max")
if grow_iter is not None and grow_max:
    parts.append(f"Iteration {grow_iter}/{grow_max}")
```

The label "Iteration" is correct, but `grow_max` is populated from `max_iterations` in the callback, which is actually `max_epochs` (10,000). The display shows "Iteration 5/10000" instead of "Iteration 5/20" (where 20 = max_hidden_units).

#### RC-SEMANT-04: demo_mode.py Epoch Counter Incremented Per Training Step

**File**: `juniper-canopy/src/demo_mode.py:1267-1270`
```python
with self._lock:
    self.current_epoch += 1
    self.current_loss = loss
    self.current_accuracy = accuracy
```

In demo mode, `current_epoch` is incremented every time metrics are emitted (after each gradient step), not after a full pass through all training data. This conflates training steps with epochs.

#### RC-SEMANT-05: Dashboard Label "Maximum Total Epochs" for Grow Iteration Limit

**File**: `juniper-canopy/src/frontend/dashboard_manager.py:589`
```python
html.P("Maximum Total Epochs:", className="mb-1 fw-bold"),
```

This parameter label controls the `max_epochs` value passed to `grow_network()`, which limits grow iterations, not epochs. The label should reflect what it actually controls.

### Impact Assessment

| Factor | Impact |
|--------|--------|
| Severity | P1 - Monitoring unusable |
| Scope | All dashboard displays showing training progress |
| User Impact | Confusing progress indication; progress bars appear stuck |
| Data Impact | None (display-only) |
| Reversibility | Label/variable changes, fully reversible |

---

## 3. Plot Card Heights (P2 - MEDIUM)

### Problem Statement

The data and boundary plot cards are too small for effective visualization. The plots need larger heights without breaking their aspect ratios.

### Current State

| Component | File | Line | Current Height | maxWidth |
|-----------|------|------|---------------|----------|
| Decision Boundary | `juniper-canopy/src/frontend/components/decision_boundary.py` | 150 | 600px | 700px |
| Dataset Scatter | `juniper-canopy/src/frontend/components/dataset_plotter.py` | 222 | 600px | 700px |
| Dataset Distribution | `juniper-canopy/src/frontend/components/dataset_plotter.py` | 228 | 25vh (200-350px) | none |

Both primary plots use `yaxis={"scaleanchor": "x", "scaleratio": 1}` to maintain 1:1 aspect ratio. The `maxWidth: 700px` with `margin: 0 auto` centers plots but constrains them.

### Root Cause

The 600px height was set as a reasonable default but is insufficient for the data visualization needs of the two-spiral and XOR classification problems. The maxWidth of 700px further constrains the effective plot area.

### Fix Requirements

- Increase height from 600px to 800px
- Increase maxWidth from 700px to 900px proportionally
- Maintain `scaleanchor`/`scaleratio` aspect ratio locks
- Ensure distribution plot scales proportionally
- Verify no CSS conflicts in `plotly_fix.css` (min-height: 300px is not restrictive)

### Impact Assessment

| Factor | Impact |
|--------|--------|
| Severity | P2 - Usability issue |
| Scope | Decision Boundary and Dataset View tabs |
| User Impact | Plots hard to read at current size |
| Data Impact | None |
| Reversibility | CSS/style change, fully reversible |

---

## 4. Parameter Update Flakiness (P1 - HIGH)

### Problem Statement

Two distinct issues:
1. Value updates are not always successful when submitted
2. Updated values are frequently not reflected in the canopy status displays

### Root Cause Analysis

#### RC-PARAM-01: WebSocket onmessage Ignores state_change Messages

**File**: `juniper-canopy/src/frontend/dashboard_manager.py:1446-1458`
```javascript
ws.onmessage = function(evt) {
    try {
        var msg = JSON.parse(evt.data);
        if (msg.type === 'metrics' && msg.data) {
            window._juniper_ws_buffer.push(msg.data);
            // ...
        }
        if (msg.type === 'topology' && msg.data) {
            window._juniper_ws_topology = msg.data;
        }
    } catch(e) {}
};
```

Only `metrics` and `topology` message types are handled. The `state_change` message broadcast by the backend after parameter updates (line 2039 of main.py) is silently discarded.

**File**: `juniper-canopy/src/main.py:2038-2039`
```python
# Broadcast state change
await websocket_manager.broadcast({"type": "state_change", "data": training_state.get_state()})
```

This means the frontend never receives real-time confirmation that parameters were applied.

#### RC-PARAM-02: Parameter Mapping Silently Drops Unmapped Keys

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py:425-447`
```python
_CANOPY_TO_CASCOR_PARAM_MAP = {
    "nn_learning_rate": "learning_rate",
    "nn_max_hidden_units": "max_hidden_units",
    "nn_max_total_epochs": "epochs_max",
    "nn_growth_convergence_threshold": "patience",  # NOTE: Wrong mapping!
    "cn_pool_size": "candidate_pool_size",
    "cn_correlation_threshold": "correlation_threshold",
    "cn_candidate_learning_rate": "candidate_learning_rate",
}
```

**Critical Bug**: `nn_growth_convergence_threshold` is mapped to `"patience"` instead of `"convergence_threshold"`. This means:
- When users update the convergence threshold, they're actually changing patience
- The actual convergence threshold is never updated

**Missing Mappings** (15+ parameters silently dropped):
- `nn_max_iterations`, `nn_patience`, `nn_multi_node_layers`, `nn_growth_trigger`, `nn_growth_preset_epochs`
- `cn_patience`, `cn_selected_candidates`, `cn_training_complete`, `cn_training_iterations`
- `cn_training_convergence_threshold`, `cn_multi_candidate`, `cn_candidate_selection`
- `cn_top_candidates`, `cn_random_candidates`
- Dataset parameters: `nn_spiral_rotations`, `nn_spiral_number`, `nn_dataset_elements`, `nn_dataset_noise`

When a user only updates unmapped parameters, `apply_params()` returns success with `"No cascor-mappable params provided"` - a silent no-op disguised as success.

#### RC-PARAM-03: Optimistic State Update Before Backend Confirmation

**File**: `juniper-canopy/src/main.py:2024-2035`
```python
# Update TrainingState with backward-compatible keys it understands
ts_updates = {}
if "nn_learning_rate" in backend_updates:
    ts_updates["learning_rate"] = float(backend_updates["nn_learning_rate"])
# ... more mappings ...
if ts_updates:
    training_state.update_state(**ts_updates)  # Updated BEFORE backend confirms!

# Forward all params to backend
backend.apply_params(**backend_updates)  # No check if this succeeded
```

`training_state` is updated **before** the backend confirms the parameters were applied. If the cascor service rejects the update, canopy's state is already wrong.

#### RC-PARAM-04: No Read-Back Confirmation After Parameter Application

**File**: `juniper-canopy/src/main.py:2035-2041`
```python
backend.apply_params(**backend_updates)  # Fire and forget
system_logger.info(f"Parameters updated: {backend_updates}")
await websocket_manager.broadcast({"type": "state_change", "data": training_state.get_state()})
return {"status": "success", "state": training_state.get_state()}
```

The endpoint doesn't check the return value of `backend.apply_params()`. Even if the backend reports `{"ok": False, "error": "..."}`, the API returns success.

#### RC-PARAM-05: ServiceBackend Does Not Propagate Errors

**File**: `juniper-canopy/src/backend/service_backend.py:197-198`
```python
def apply_params(self, **params: Any) -> Dict[str, Any]:
    return self._adapter.apply_params(**params)
```

The return value (which may contain `{"ok": False, "error": "..."}`) is returned but never inspected by the caller (main.py line 2035).

### Impact Assessment

| Factor | Impact |
|--------|--------|
| Severity | P1 - Core functionality broken |
| Scope | All parameter update workflows |
| User Impact | Parameters appear to save but don't take effect; display shows stale values |
| Data Impact | Network may train with wrong parameters |
| Reversibility | Code fix, no data migration needed |

---

## Cross-Cutting Dependencies

```
RC-TRAIN-01 (correlation threshold) ──────────────────────┐
    + RC-TRAIN-02 (early stopping) ── create death spiral │
                                                          ├──> Training stalls
RC-PARAM-02 (wrong mapping) ─────────────────────────────│
    convergence_threshold mapped to patience               │
    means runtime updates to threshold actually            │
    change patience, further destabilizing training ───────┘

RC-SEMANT-01..05 (epoch/iteration) ── affect user's ─────> User cannot diagnose
    ability to understand training progress                  training stalls

RC-PARAM-01 (WS state_change ignored) ── means ──────────> Display doesn't
RC-PARAM-03 (optimistic update) ── compounds ──────────────> reflect actual state
RC-PARAM-04 (no read-back) ── ensures ────────────────────> Silent failures
```

---

## Verification Methodology

All root causes were identified by:
1. Reading source code directly (file paths and line numbers verified)
2. Tracing execution flow from user action to backend processing
3. Cross-referencing with existing analysis documents in notes/
4. Validating against the Cascade Correlation algorithm specification (Fahlman & Lebiere, 1990)
5. Checking git history for recent changes that may have introduced or attempted to fix these issues
