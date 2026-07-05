# Juniper Project Regression Analysis - 2026-04-03

**Author**: Claude Code (Principal Engineer Analysis)
**Date**: 2026-04-03
**Scope**: juniper-cascor, juniper-canopy
**Status**: Active

---

## Executive Summary

Four critical regressions have been identified across the Juniper project. This analysis traces each issue to specific root causes with line-level evidence in the codebase.

| # | Issue | Severity | Application(s) | Root Cause Status |
|---|-------|----------|-----------------|-------------------|
| 1 | Training stalls before reaching targets | P0 Critical | juniper-cascor | Identified, partially fixed |
| 2 | Epoch/Iteration semantic confusion | P1 High | juniper-canopy | Identified, unfixed |
| 3 | Data/boundary plot cards too small | P2 Medium | juniper-canopy | Identified, unfixed |
| 4 | Parameter update flakiness | P1 High | juniper-canopy, juniper-cascor | Identified, partially fixed |

---

## Issue 1: Training Stalls Before Reaching Target Accuracy/Loss

### Symptom

The CasCor training process terminates prematurely -- the network stops growing before training accuracy reaches the target value (default 0.999) or before training loss converges to an acceptable level. This renders the entire project non-functional.

### Root Cause Analysis

**Multiple compounding causes identified:**

#### RC-1A: Missing Convergence Threshold in Patience Check (FIXED in uncommitted changes)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:4446`
**Committed code**:
```python
if value_loss < best_value_loss:    # ANY improvement resets patience
    best_value_loss = value_loss
    patience_counter = 0
```

**Problem**: Without a minimum improvement threshold, patience resets on floating-point noise improvements. This is not the stalling cause but interacts with RC-1B -- when loss plateaus at a non-converged value, even tiny oscillations can delay the patience mechanism from triggering, creating a "zombie training" state where the system runs indefinitely without progress rather than cleanly exiting and letting the cascade grow.

**Fix (in uncommitted changes)**: Added `self.convergence_threshold` (default 0.001):
```python
if value_loss < best_value_loss - self.convergence_threshold:
```

#### RC-1B: Candidate Training Convergence Threshold Missing (FIXED in uncommitted changes)

**File**: `juniper-cascor/src/candidate_unit/candidate_unit.py:599`
**Committed code**:
```python
if current_abs_correlation > abs(best_correlation_so_far):
```

**Problem**: Without a convergence threshold, candidate early stopping patience resets on any improvement. Combined with the default patience of 30 and 400 max epochs, candidates may train for excessively long or terminate with suboptimal correlations.

**Fix (in uncommitted changes)**: Added convergence threshold:
```python
if current_abs_correlation > abs(best_correlation_so_far) + self.convergence_threshold:
```

#### RC-1C: Correlation Threshold Causes Premature Cascade Exit (UNFIXED)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3611`
```python
elif training_results.best_candidate.get_correlation() < self.correlation_threshold:
    self.logger.info(f"No candidate met correlation threshold: {self.correlation_threshold}...")
    break
```

**Problem**: The correlation threshold (default 0.0005) is checked as an absolute floor. When the residual error becomes small (as training progresses), candidates naturally achieve lower correlations because there's less signal to correlate with. The threshold does not adapt to the magnitude of the residual error, causing premature cascade termination in the late stages of training.

**Evidence**: This is the most common training termination pathway when the network has 10+ hidden units and loss is in the 0.01-0.1 range but accuracy hasn't reached 0.999.

**Proposed Fix**: Add an adaptive threshold or significantly lower the static threshold. Alternatively, use the ratio of best_correlation to residual_error magnitude as the stopping criterion.

#### RC-1D: OPT-5 SharedMemory Failures Cause Silent Training Abort (PARTIALLY FIXED)

**Files**:
- `juniper-cascor/src/cascade_correlation/cascade_correlation.py:1741-1771` (SHM creation)
- `juniper-cascor/src/cascade_correlation/cascade_correlation.py:1877-1920` (execution fallback)

**Problem**: SharedMemory creation failures in OPT-5 fall through to a sequential fallback path. If the fallback also fails or produces degraded results, `train_candidates()` returns None, causing the grow_network loop to break at line 3606.

**Status**: PRs #60 and #61 fixed the most critical SharedMemory lifecycle issues (deferred unlink, resource tracker errors, tensor clone). However, the fallback path's resilience needs verification.

#### RC-1E: Output Layer Retraining Uses Fixed Epoch Count (OBSERVATION)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3646`
```python
train_loss = self.train_output_layer(x_train, y_train, self.output_epochs)
```

**Observation**: `output_epochs` defaults to 10,000, which is the maximum -- not a target. The output training uses its own early stopping. However, if the output layer's early stopping triggers prematurely (e.g., patience exhausted due to plateau), the post-cascade-add retraining may be insufficient, leaving higher loss than necessary for the next iteration's residual error calculation.

### Impact

- **Immediate**: Training cannot complete. The network grows partially but stops before achieving target accuracy.
- **Downstream**: All juniper-canopy monitoring displays show stalled/incomplete training state.
- **Development**: Blocks all further feature development.

---

## Issue 2: Epoch/Iteration Semantic Confusion

### Correct Definitions (per project specification)

| Term | Definition |
|------|-----------|
| **Epoch** | A single pass through the training data |
| **Iteration** | One complete candidate node addition + one complete network output retraining. Each iteration is associated with network growth. |

### Current Display (Incorrect)

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`

| Display Element | Label | Source Data | Correct Label |
|----------------|-------|-------------|---------------|
| Line 406 | "Current Epoch" | `metrics_data[-1]["epoch"]` = grow_network loop counter | **"Current Iteration"** |
| Line 457 | "Grow Iteration" | `grow_iteration/grow_max` | **"Cascade Iteration"** |
| Line 472 | "Candidate Epoch" | `candidate_epoch/candidate_total_epochs` | **"Candidate Epoch"** (correct) |
| Line 1107 | "Iteration {n}/{m}" (detail text) | grow_iteration/grow_max | **"Cascade Iteration {n}/{m}"** |
| Line 1122 | "Candidate Epoch: {n}/{m}" (detail text) | candidate_epoch/candidate_total_epochs | Correct |

### Root Cause

The `grow_network()` loop (cascade_correlation.py:3596) uses a variable named `epoch` but it represents an **iteration** of the cascade growth process. Each loop iteration:
1. Trains a pool of candidates (multiple epochs of candidate training)
2. Selects the best candidate
3. Adds it to the network (network growth event)
4. Retrains the output layer (multiple epochs of output training)

This is definitionally an **iteration**, not an epoch. The metrics pipeline propagates this naming confusion from the backend through WebSocket messages to the canopy display.

### Affected Components

1. **Metrics Panel Cards** (metrics_panel.py:406): "Current Epoch" heading
2. **Progress Bars** (metrics_panel.py:457): "Grow Iteration" label
3. **Progress Detail Text** (metrics_panel.py:1107): "Iteration {n}/{m}" format string
4. **Plot X-Axis Labels** (metrics_panel.py): Various plot x-axis labels using "Epoch"

### Impact

- Users cannot correctly interpret training progress
- Monitoring data is semantically misleading
- The relationship between iterations and network growth is obscured

---

## Issue 3: Data and Boundary Plot Card Heights Too Small

### Current Dimensions

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:150`
```python
style={"height": "600px", "maxWidth": "700px", "margin": "0 auto"}
```

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:222`
```python
style={"height": "600px", "maxWidth": "700px", "margin": "0 auto"}
```

### Problem

The 600px x 700px plot dimensions are too small for effective visualization of:
- Decision boundary contours (fine detail lost at current resolution)
- Dataset scatter plots (point density not visible at current scale)
- The card container constrains these plots further with padding

### Proposed Fix

Increase both plot dimensions while maintaining aspect ratio:
- **Height**: 600px -> 800px
- **Max Width**: 700px -> 900px
- **Distribution Plot**: min 200px -> 250px, max 350px -> 450px

This maintains the approximately 7:6 width-to-height ratio while providing ~33% more visualization area.

### Impact

- Improved readability of decision boundary contours
- Better visibility of dataset point distributions
- No breaking changes to layout (cards scale within their containers)

---

## Issue 4: Parameter Update Flakiness

### Symptom

1. Parameter value updates submitted via the canopy sidebar are not always successfully applied to the cascor backend.
2. Updated values are not reflected in the canopy status displays after submission.

### Root Cause Analysis

#### RC-4A: Incorrect Parameter Mapping (FIXED in uncommitted changes)

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py:430`
**Committed code**:
```python
_CANOPY_TO_CASCOR_PARAM_MAP = {
    ...
    "nn_growth_convergence_threshold": "patience",   # WRONG: maps convergence_threshold to patience
    ...
}
```

**Problem**: The canopy UI's "Growth Convergence Threshold" field was being mapped to the cascor backend's `patience` parameter instead of `convergence_threshold`. This means:
- Submitting a convergence threshold value (e.g., 0.01) would set patience to 0 (truncated float → int)
- Patience was not independently controllable from the UI
- The convergence threshold was never actually applied to the backend

**Fix (in uncommitted changes)**: Corrected the mapping and added separate patience controls:
```python
_CANOPY_TO_CASCOR_PARAM_MAP = {
    ...
    "nn_growth_convergence_threshold": "convergence_threshold",  # CORRECT
    "nn_patience": "patience",                                    # NEW
    "cn_patience": "candidate_patience",                          # NEW
    "cn_training_convergence_threshold": "candidate_convergence_threshold",  # NEW
    ...
}
```

#### RC-4B: Missing Patience UI Controls (FIXED in uncommitted changes)

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

**Problem**: The sidebar had no input controls for `nn_patience` or `cn_patience`. Users could not set patience values directly. The only way patience was affected was through the incorrect convergence_threshold mapping.

**Fix (in uncommitted changes)**: Added `nn-patience-input` and `cn-patience-input` controls with appropriate min/max/default values.

#### RC-4C: Missing Backend Updatable Keys (FIXED in uncommitted changes)

**File**: `juniper-cascor/src/api/lifecycle/manager.py:717`

**Problem**: The `updatable_keys` set in `update_params()` did not include `convergence_threshold`, `candidate_patience`, or `candidate_convergence_threshold`. Even with correct mapping, these values would be silently ignored.

**Fix (in uncommitted changes)**: Added the three missing keys to the updatable set.

#### RC-4D: Missing API Model Fields (FIXED in uncommitted changes)

**File**: `juniper-cascor/src/api/models/training.py:52`

**Problem**: The `TrainingParamUpdateRequest` Pydantic model lacked fields for the three new parameters, causing them to be stripped during validation.

**Fix (in uncommitted changes)**: Added `convergence_threshold`, `candidate_patience`, and `candidate_convergence_threshold` fields with appropriate validation.

### Impact

- Users setting convergence thresholds were unknowingly corrupting patience settings
- Patience was not user-controllable, preventing tuning of early stopping behavior
- Parameter updates that appeared successful in the UI were silently rejected by the backend

---

## Cross-Cutting Concerns

### Uncommitted Changes Status

Both `juniper-cascor` and `juniper-canopy` have significant uncommitted changes on `main` that address Issues 1 and 4 partially:

**juniper-cascor** (8 files, +50/-2 lines):
- Convergence threshold infrastructure throughout constants, config, network, candidate unit
- API lifecycle manager and model updates for new parameters

**juniper-canopy** (13 files, +301/-37 lines):
- Parameter mapping corrections
- New patience UI controls
- Updated tests for new parameter count (23 -> 25 outputs)

These changes need to be committed on feature branches, combined with fixes for Issues 2 and 3, and validated through testing.

### Interaction Between Issues

```
Issue 1 (Training Stall)
    ├── RC-1A (Patience threshold) ← Fixed by Issue 4's convergence_threshold plumbing
    ├── RC-1B (Candidate threshold) ← Fixed by Issue 4's candidate params
    ├── RC-1C (Correlation threshold) ← UNFIXED, needs adaptive threshold
    └── RC-1D (OPT-5 failures) ← Previously fixed in PRs #60, #61

Issue 4 (Parameter Flakiness)
    ├── RC-4A (Wrong mapping) ← Enabled RC-1A/1B fixes to reach backend
    ├── RC-4B (Missing UI) ← Made RC-1A/1B fixes user-tunable
    ├── RC-4C (Missing keys) ← Backend acceptance of new params
    └── RC-4D (Missing model) ← API validation of new params
```

Issues 2 and 3 are independent UI concerns.
