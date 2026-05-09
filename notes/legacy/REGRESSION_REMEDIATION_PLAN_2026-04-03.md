# Juniper Project Regression Remediation Plan

**Date**: 2026-04-03
**Scope**: juniper-cascor, juniper-canopy
**Author**: Claude Code (Opus 4.6)
**Status**: Active
**Companion Document**: REGRESSION_ANALYSIS_2026-04-03.md

---

## Phase 1: Training Stall Fix (P0 - CRITICAL)

### 1.1 Raise Correlation Threshold

**Root Cause**: RC-TRAIN-01
**File**: `juniper-cascor/src/cascor_constants/constants_model/constants_model.py:440`

**Change**: `0.0005` -> `0.01`

**Rationale**: The original implementation default was 0.05 (line 421 comment). A value of 0.01 is conservative enough to accept meaningful candidates while filtering noise. Values below 0.005 produce candidates with effectively zero contribution.

**Approach A (Recommended)**: Static threshold increase
- Change default to 0.01
- Simple, predictable, matches literature defaults
- Risk: May reject candidates too aggressively for some datasets
- Guardrail: Value is runtime-configurable via API

**Approach B**: Adaptive threshold based on network size
- Formula: `threshold = max(0.005, initial_threshold / (1 + 0.1 * num_hidden_units))`
- Adapts as residual error shrinks
- Risk: More complex, harder to debug
- Not recommended for initial fix

**Recommendation**: Approach A. Simple static increase to 0.01 addresses the immediate training stall. Adaptive thresholding can be added later as an enhancement.

### 1.2 Fix grow_network Loop Semantics

**Root Cause**: RC-TRAIN-02, RC-TRAIN-03
**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3587-3615`

**Changes**:
1. Rename loop variable `epoch` -> `iteration` (line 3587)
2. Rename parameter `max_epochs` -> `max_iterations` in grow_network signature (line 3542)
3. Update callback to pass `max_iterations=self.max_hidden_units` instead of `max_iterations=max_epochs` (line 3615)
4. Update all log messages in grow_network to use "iteration" terminology
5. Update ValidateTrainingInputs construction to pass correct semantics

**Approach A (Recommended)**: Use `max_hidden_units` as the iteration bound
- The grow_network loop should iterate at most `max_hidden_units` times, not `max_epochs`
- `max_epochs` remains the parameter name for the API but is interpreted as max iterations
- The callback passes `max_iterations=self.max_hidden_units` for accurate progress display

**Approach B**: Keep `max_epochs` as the loop bound, fix display only
- Less disruptive but leaves the semantic confusion in place
- Not recommended: the confusion is a root cause of the training stall

**Recommendation**: Approach A. Fixing the loop bound to `max_hidden_units` also implicitly fixes the early stopping issue since the patience counter now operates over a meaningful iteration count.

### 1.3 Verify Early Stopping Behavior Post-Fix

After fixes 1.1 and 1.2, early stopping should behave correctly:
- Higher-quality candidates (correlation > 0.01) produce meaningful loss improvements
- Patience of 50 over `max_hidden_units` iterations (typically 20-50) is appropriate
- Convergence threshold of 0.001 per iteration is reasonable with quality candidates

**No code change required** - the early stopping mechanism itself is correct; the inputs were wrong.

---

## Phase 2: Epoch/Iteration Semantics Fix (P1 - HIGH)

### 2.1 Fix grow_network Callback Parameters

**Root Cause**: RC-SEMANT-01, RC-SEMANT-02
**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py:3614-3615`

**Change**: Pass `max_iterations=self.max_hidden_units` instead of `max_iterations=max_epochs`

This is the same change as Phase 1.2, included here for completeness.

### 2.2 Fix Canopy Metrics Display Labels

**Root Cause**: RC-SEMANT-03
**File**: `juniper-canopy/src/frontend/components/metrics_panel.py:1107`

**Current**: `parts.append(f"Iteration {grow_iter}/{grow_max}")`
**Correct**: Already uses "Iteration" label (correct). The fix is in the data source (Phase 2.1).

### 2.3 Fix Dashboard Parameter Labels

**Root Cause**: RC-SEMANT-05
**File**: `juniper-canopy/src/frontend/dashboard_manager.py:589`

**Change**: "Maximum Total Epochs:" -> "Maximum Grow Iterations:"

This label controls the `nn_max_total_epochs` parameter which becomes `max_epochs` in grow_network, which is actually the grow iteration limit. The label should reflect the actual behavior.

### 2.4 Fix Demo Mode Epoch Tracking

**Root Cause**: RC-SEMANT-04
**File**: `juniper-canopy/src/demo_mode.py:1267`

**Analysis**: In demo mode, `current_epoch` is incremented per metrics emission (per gradient step). This should be incremented per full pass through training data.

**Approach**: Track actual epochs separately from training steps. Emit metrics with step count and epoch count as distinct fields.

**Risk**: May affect existing callbacks that rely on `current_epoch` as a step counter.

---

## Phase 3: Plot Card Heights (P2 - MEDIUM)

### 3.1 Increase Decision Boundary Plot Height

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:150`

**Change**: `"height": "600px", "maxWidth": "700px"` -> `"height": "800px", "maxWidth": "900px"`

### 3.2 Increase Dataset Scatter Plot Height

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:222`

**Change**: `"height": "600px", "maxWidth": "700px"` -> `"height": "800px", "maxWidth": "900px"`

### 3.3 Increase Distribution Plot Height Proportionally

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:228`

**Change**: `"height": "25vh", "maxHeight": "350px", "minHeight": "200px"` -> `"height": "30vh", "maxHeight": "450px", "minHeight": "250px"`

### Risk Assessment

- Aspect ratio locks (`scaleanchor`/`scaleratio`) are preserved automatically
- The 9-column Bootstrap grid provides ~75% viewport width, accommodating 900px maxWidth on standard displays
- No CSS conflicts (plotly_fix.css min-height of 300px is not restrictive)
- Responsive behavior maintained via centered layout

---

## Phase 4: Parameter Update Flakiness (P1 - HIGH)

### 4.1 Add state_change Handler to WebSocket Client

**Root Cause**: RC-PARAM-01
**File**: `juniper-canopy/src/frontend/dashboard_manager.py:1446-1458`

**Change**: Add `state_change` message type handling to the WebSocket onmessage handler:

```javascript
if (msg.type === 'state_change' && msg.data) {
    window._juniper_ws_state = msg.data;
}
```

Add a new clientside callback to drain the state buffer into a Dash store, similar to the existing topology buffer pattern.

### 4.2 Fix Parameter Mapping Bug

**Root Cause**: RC-PARAM-02
**File**: `juniper-canopy/src/backend/cascor_service_adapter.py:425-434`

**Changes**:
1. Fix wrong mapping: `"nn_growth_convergence_threshold": "patience"` -> `"nn_growth_convergence_threshold": "convergence_threshold"`
2. Add missing mappings for runtime-updatable cascor parameters:
   - `"nn_patience": "patience"`
   - `"cn_patience": "candidate_patience"`
   - `"cn_training_convergence_threshold": "candidate_convergence_threshold"`
   - `"nn_max_iterations": "epochs_max"` (if this should map to max grow iterations)

**Note**: Parameters that are canopy-only (spiral, dataset, UI-only flags) are correctly silently skipped. But core training parameters must be mapped.

### 4.3 Fix Optimistic State Update

**Root Cause**: RC-PARAM-03, RC-PARAM-04, RC-PARAM-05
**File**: `juniper-canopy/src/main.py:2024-2041`

**Change**: Check `backend.apply_params()` return value before updating TrainingState:

```python
result = backend.apply_params(**backend_updates)
if isinstance(result, dict) and result.get("ok") is False:
    return JSONResponse({"error": result.get("error", "Backend rejected parameters")}, status_code=502)

# Only update TrainingState AFTER confirmed success
if ts_updates:
    training_state.update_state(**ts_updates)
```

### Risk Assessment

| Fix | Risk | Mitigation |
|-----|------|-----------|
| 4.1 WS handler | Low - additive change | Existing metrics/topology handlers unaffected |
| 4.2 Mapping fix | Medium - changes parameter routing | Test with both demo and service mode |
| 4.3 State ordering | Medium - changes success/failure flow | Error responses need frontend handling |

---

## Validation Plan

### Per-Phase Validation

| Phase | Test | Method |
|-------|------|--------|
| 1 (Training) | Training reaches target accuracy on XOR | Run training to completion |
| 1 (Training) | Training reaches target on two-spiral | Run training to completion |
| 2 (Semantics) | Iteration display shows N/max_hidden_units | Visual inspection of canopy UI |
| 2 (Semantics) | Progress bar advances meaningfully | Visual inspection |
| 3 (Plots) | Plot cards are 800px tall | Browser dev tools inspection |
| 3 (Plots) | Aspect ratio preserved | Visual inspection |
| 4 (Params) | Parameter update confirmed via read-back | Apply params, verify API response |
| 4 (Params) | State display updates after param change | Apply params, check canopy display |

### Test Suite Requirements

- All existing tests must pass (no removals or disabling)
- New tests for parameter mapping validation
- New tests for WebSocket state_change handling
- Existing 2,695 cascor tests, 3,066+ canopy tests, 208 client tests
