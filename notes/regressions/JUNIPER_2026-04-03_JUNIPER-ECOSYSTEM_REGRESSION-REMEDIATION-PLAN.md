# Juniper Project Regression Remediation Plan - 2026-04-03

**Author**: Claude Code (Principal Engineer)
**Date**: 2026-04-03
**Companion Document**: `REGRESSION_ANALYSIS_2026-04-03.md`
**Status**: Active

---

## Remediation Strategy

### Priority Order

1. **P0**: Training stall fix (RC-1C: adaptive correlation threshold)
2. **P1**: Parameter update completeness (commit and validate uncommitted fixes)
3. **P1**: Epoch/iteration semantic correction
4. **P2**: Plot card height increase

### Approach: Single Feature Branch Per Repository

All fixes for each repository will be consolidated on a single feature branch to minimize merge complexity:
- `juniper-cascor`: `fix/regression-phase3-2026-04-03`
- `juniper-canopy`: `fix/regression-phase3-2026-04-03`

---

## Fix 1: Training Stall - Adaptive Correlation Threshold (RC-1C)

### Problem

The correlation threshold (0.0005) is static. As training progresses and residual errors shrink, candidate correlations naturally decrease. A static floor causes premature cascade exit.

### Approach A: Adaptive Threshold Based on Residual Magnitude (RECOMMENDED)

**Rationale**: Scale the correlation threshold relative to the residual error magnitude. When residuals are large (early training), maintain a meaningful threshold. When residuals are small (late training), lower the threshold proportionally.

**Implementation**:
```python
# cascade_correlation.py, grow_network() around line 3611
residual_magnitude = residual_error.abs().mean().item()
adaptive_threshold = min(self.correlation_threshold, residual_magnitude * 0.01)
if training_results.best_candidate.get_correlation() < adaptive_threshold:
    ...
```

**Strengths**:
- Automatically adapts to training progress
- Prevents premature exit while maintaining quality control
- No new hyperparameters needed

**Weaknesses**:
- Residual magnitude scale depends on problem and encoding
- Factor (0.01) may need tuning per dataset

**Risk**: Low - falls back to original threshold when residual is large

### Approach B: Minimum Iteration Count Before Threshold Check

**Rationale**: Require a minimum number of cascade iterations before applying the correlation threshold.

**Implementation**:
```python
min_iterations = max(5, self.max_hidden_units // 4)
if epoch >= min_iterations and training_results.best_candidate.get_correlation() < self.correlation_threshold:
    ...
```

**Strengths**: Simple, predictable
**Weaknesses**: Arbitrary minimum, doesn't adapt to problem difficulty
**Risk**: Low

### Approach C: Correlation Decay Warning (Instead of Hard Stop)

**Rationale**: Log a warning and continue for a configurable number of iterations when correlation drops below threshold, only stopping if it persists.

**Implementation**: Track consecutive low-correlation iterations, stop after N consecutive failures.

**Strengths**: Resilient to transient correlation dips
**Weaknesses**: More complex state management
**Risk**: Medium

### Recommended Approach

**Approach A (Adaptive threshold)** with a fallback floor:
```python
adaptive_threshold = max(1e-6, min(self.correlation_threshold, residual_magnitude * 0.01))
```

The `max(1e-6, ...)` floor prevents the threshold from becoming so small that noise-level correlations pass.

---

## Fix 2: Commit and Validate Uncommitted Parameter Fixes

### Already Implemented (Uncommitted on Main)

The following fixes exist as uncommitted changes and need to be committed on feature branches:

**juniper-cascor**:
- `convergence_threshold` constant and propagation (constants → config → network → API)
- `candidate_patience` and `candidate_convergence_threshold` parameters
- `check_patience()` convergence threshold check
- `CandidateUnit.train()` convergence threshold check
- API lifecycle manager updatable keys and model fields

**juniper-canopy**:
- Fixed `nn_growth_convergence_threshold` → `convergence_threshold` mapping
- Added `nn_patience` and `cn_patience` UI controls and callbacks
- Added parameter mapping for new params
- Updated tests for 25-output parameter count

### Validation Required

1. All existing tests pass with these changes
2. New parameters are correctly propagated from UI → adapter → client → cascor API → network
3. Status endpoint returns updated parameter values after PATCH

---

## Fix 3: Epoch/Iteration Semantic Correction

### Changes Required

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`

| Line | Current | Corrected |
|------|---------|-----------|
| 406 | `html.H5("Current Epoch")` | `html.H5("Current Iteration")` |
| 457 | `html.Small("Grow Iteration", ...)` | `html.Small("Cascade Iteration", ...)` |
| 1107 | `f"Iteration {grow_iter}/{grow_max}"` | `f"Cascade Iteration {grow_iter}/{grow_max}"` |

**Metrics plots**: The x-axis on loss and accuracy plots currently shows "Epoch" numbers. These should show "Iteration" to maintain consistency.

### Approach: Display-Only Changes

Only change the display labels in juniper-canopy. Do NOT rename the backend data fields (`epoch`, `grow_iteration`) as this would break WebSocket protocol compatibility and require cascor-client updates.

**Strengths**: Minimal blast radius, no backend changes
**Weaknesses**: Backend/frontend terminology diverges (backend says "epoch", frontend shows "iteration")
**Risk**: None - display-only change

---

## Fix 4: Plot Card Height Increase

### Changes Required

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:150`
```python
# Before:
style={"height": "600px", "maxWidth": "700px", "margin": "0 auto"}
# After:
style={"height": "800px", "maxWidth": "900px", "margin": "0 auto"}
```

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:222`
```python
# Before:
style={"height": "600px", "maxWidth": "700px", "margin": "0 auto"}
# After:
style={"height": "800px", "maxWidth": "900px", "margin": "0 auto"}
```

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:228`
```python
# Before:
style={"height": "25vh", "maxHeight": "350px", "minHeight": "200px"}
# After:
style={"height": "30vh", "maxHeight": "450px", "minHeight": "250px"}
```

### Aspect Ratio Preservation

The current 600:700 (height:width) ratio ~ 0.857.
The proposed 800:900 ratio ~ 0.889.
This is a minor ratio change that slightly increases the relative height, making plots more square-like. The `scaleanchor` attribute on the plot's y-axis (already set via line 366 in decision_boundary.py) ensures the data aspect ratio is preserved regardless of container dimensions.

**Risk**: None - the Plotly `scaleanchor` handles data aspect ratio; container changes only affect surrounding whitespace.

---

## Risk Assessment Summary

| Fix | Complexity | Risk | Test Impact |
|-----|-----------|------|-------------|
| Fix 1 (Adaptive threshold) | Low | Low | Needs new unit tests |
| Fix 2 (Parameter plumbing) | Medium | Low | Tests already updated |
| Fix 3 (Epoch→Iteration labels) | Low | None | Test label assertions may need update |
| Fix 4 (Plot heights) | Trivial | None | No test impact |

---

## Testing Plan

### juniper-cascor

1. Run full test suite: `cd src && python -m pytest tests/ -x -v` (2695+ tests)
2. Add unit test for adaptive correlation threshold behavior
3. Verify convergence_threshold propagation from config to check_patience()

### juniper-canopy

1. Run full test suite: `cd src && pytest tests/ -v` (3066+ tests)
2. Verify label changes don't break existing test assertions
3. Verify parameter count matches new 25-output expectation
4. Integration test: parameter round-trip UI → backend → UI
