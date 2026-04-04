# Juniper Project Regression Development Roadmap

**Date**: 2026-04-03
**Author**: Claude Code (Opus 4.6)
**Companion Documents**: REGRESSION_ANALYSIS_2026-04-03.md, REGRESSION_REMEDIATION_PLAN_2026-04-03.md

---

## Roadmap Overview

| Phase | Priority | Description | Tasks | Status |
|-------|----------|-------------|-------|--------|
| 1 | P0 CRITICAL | Fix training stall in juniper-cascor | T01-T03 | Pending |
| 2 | P1 HIGH | Fix epoch/iteration semantics | T04-T07 | Pending |
| 3 | P2 MEDIUM | Increase plot card heights | T08-T10 | Pending |
| 4 | P1 HIGH | Fix parameter update flakiness | T11-T15 | Pending |
| 5 | -- | Validation and testing | T16-T18 | Pending |

---

## Phase 1: Fix Training Stall (P0 CRITICAL)

### T01: Raise correlation threshold default

- **File**: `juniper-cascor/src/cascor_constants/constants_model/constants_model.py:440`
- **Change**: `_PROJECT_MODEL_CORRELATION_THRESHOLD = 0.0005` -> `0.01`
- **Root Cause**: RC-TRAIN-01

### T02: Rename grow_network loop variable and fix callback max_iterations

- **File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
- **Changes**:
  - Line 3587: `for epoch in range(max_epochs)` -> `for iteration in range(max_epochs)`
  - Line 3615: `max_iterations=max_epochs` -> `max_iterations=self.max_hidden_units`
  - All log messages in grow_network: replace "epoch" with "iteration" where referring to grow cycles
- **Root Cause**: RC-TRAIN-02, RC-TRAIN-03, RC-SEMANT-01, RC-SEMANT-02

### T03: Validate training completes on standard datasets

- **Method**: Review unit tests for training completion assertions
- **Acceptance**: Existing test suite passes with new threshold

---

## Phase 2: Fix Epoch/Iteration Semantics (P1 HIGH)

### T04: Update dashboard parameter label

- **File**: `juniper-canopy/src/frontend/dashboard_manager.py:589`
- **Change**: "Maximum Total Epochs:" -> "Maximum Grow Iterations:"
- **Root Cause**: RC-SEMANT-05

### T05: Fix demo_mode epoch tracking

- **File**: `juniper-canopy/src/demo_mode.py`
- **Change**: Ensure `current_epoch` reflects actual data passes, not per-step increments
- **Root Cause**: RC-SEMANT-04

### T06: Verify metrics_panel displays iteration progress correctly

- **File**: `juniper-canopy/src/frontend/components/metrics_panel.py`
- **Verification**: With T02 fix, grow_max should be max_hidden_units, making the display correct
- **Root Cause**: RC-SEMANT-03

### T07: Update canopy patience label for grow phase

- **File**: `juniper-canopy/src/frontend/dashboard_manager.py`
- **Change**: "Patience (epochs):" -> "Patience (iterations):" in grow-phase context
- **Root Cause**: RC-SEMANT-05

---

## Phase 3: Increase Plot Card Heights (P2 MEDIUM)

### T08: Increase decision boundary plot dimensions

- **File**: `juniper-canopy/src/frontend/components/decision_boundary.py:150`
- **Change**: height 600px -> 800px, maxWidth 700px -> 900px

### T09: Increase dataset scatter plot dimensions

- **File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:222`
- **Change**: height 600px -> 800px, maxWidth 700px -> 900px

### T10: Increase distribution plot dimensions proportionally

- **File**: `juniper-canopy/src/frontend/components/dataset_plotter.py:228`
- **Change**: height 25vh -> 30vh, maxHeight 350px -> 450px, minHeight 200px -> 250px

---

## Phase 4: Fix Parameter Update Flakiness (P1 HIGH)

### T11: Add state_change handler to WebSocket client

- **File**: `juniper-canopy/src/frontend/dashboard_manager.py:1446-1458`
- **Change**: Add `state_change` message type to onmessage handler, add clientside callback to drain state buffer

### T12: Fix parameter mapping bug (convergence_threshold -> patience)

- **File**: `juniper-canopy/src/backend/cascor_service_adapter.py:430`
- **Change**: `"nn_growth_convergence_threshold": "patience"` -> `"nn_growth_convergence_threshold": "convergence_threshold"`

### T13: Add missing parameter mappings

- **File**: `juniper-canopy/src/backend/cascor_service_adapter.py:425-434`
- **Add**: `nn_patience -> patience`, `cn_patience -> candidate_patience`, `cn_training_convergence_threshold -> candidate_convergence_threshold`

### T14: Fix optimistic state update ordering

- **File**: `juniper-canopy/src/main.py:2024-2041`
- **Change**: Check `backend.apply_params()` result before updating TrainingState; return error if backend rejects

### T15: Add parameter update confirmation test

- **File**: New test in `juniper-canopy/src/tests/`
- **Test**: Verify parameter mapping sends correct keys to cascor

---

## Phase 5: Validation and Testing

### T16: Run juniper-cascor full test suite

- **Command**: `cd juniper-cascor && conda run -n JuniperCascor pytest src/tests/ -v`
- **Acceptance**: All tests pass, no tests removed

### T17: Run juniper-canopy full test suite

- **Command**: `cd juniper-canopy && conda run -n JuniperPython pytest src/tests/ -m "unit and not slow" -v`
- **Acceptance**: All tests pass, no tests removed

### T18: Run juniper-cascor-client test suite

- **Command**: `cd juniper-cascor-client && pytest tests/ -v`
- **Acceptance**: All tests pass

---

## Dependency Graph

```
T01 (threshold) ──────┐
T02 (loop rename) ────┤──> T03 (validate training)
                      │
T04 (label) ──────────┤
T05 (demo epoch) ─────┤──> T06 (verify display)
T07 (patience label) ─┘

T08 (boundary height) ─┐
T09 (scatter height) ──┤──> Independent (no dependencies)
T10 (distrib height) ──┘

T11 (WS handler) ─────┐
T12 (mapping bug) ─────┤
T13 (missing maps) ────┤──> T15 (param test)
T14 (state ordering) ──┘

T03, T06, T15 ────────────> T16, T17, T18 (test suites)
```
