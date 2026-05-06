# Canopy Decision Boundary Fix Plan — V2

**Project**: JuniperCanopy — Decision Boundary Visualization
**Created**: 2026-03-17
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Implementation In Progress
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor-client secondary, juniper-cascor read-only reference)
**Supersedes**: `CANOPY_DECISION_BOUNDARY_FIX_PLAN.md` (V1, 2026-03-16)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Audit Summary](#audit-summary)
- [Root Cause Inventory](#root-cause-inventory)
- [Data Contract Analysis](#data-contract-analysis)
- [Implementation Plan](#implementation-plan)
- [Testing Plan](#testing-plan)
- [Validation Checklist](#validation-checklist)
- [Files Modified](#files-modified)

---

## Problem Statement

The juniper-canopy decision boundary visualization is broken in **both** operating modes:

- **Demo mode**: Displays diagonal color stripes that never change during training, despite the dashboard reporting >96% accuracy with 12 hidden units. The boundary reflects an untrained network regardless of actual training progress.
- **Service mode**: The `CascorServiceAdapter` silently fails due to an API key name mismatch (`x_grid`/`y_grid` vs `grid_x`/`grid_y`), resulting in either an empty plot or no boundary data. This bug was masked because all tests use the `FakeCascorClient`, which has different key names and data formats than the real cascor service.

### Screenshot Analysis (2026-03-17)

The screenshot shows:
- **Status**: Running, Phase: Output Training, Epoch: 377, Hidden Units: 12
- **Decision Boundary**: Multi-colored diagonal stripe bands (red → yellow → blue), characteristic of `sigmoid(w1*x + w2*y + b)` with random weights
- **Data Points**: Correctly positioned on the plot but not correlating with the colored regions
- **Root Cause**: Random hidden unit weights (never trained via candidate phase) produce linear-in-random-feature predictions. The continuous sigmoid output (0-1) renders as smooth gradient bands rather than discrete class regions.

---

## Audit Summary

Six independent audit sub-agents analyzed the decision boundary pipeline. Their findings are consolidated below.

### Audit 1: API Data Contract Mismatch (Service Mode)

The CascorServiceAdapter was written and tested against the `FakeCascorClient`, which uses different key names and data formats than the real cascor API. Seven specific mismatches were identified:

| # | Field             | Real API (manager.py)          | FakeCascorClient (scenarios.py) | Adapter Expects   |
|---|-------------------|--------------------------------|---------------------------------|-------------------|
| 1 | Grid X key        | `grid_x`                       | `x_grid`                        | `x_grid`          |
| 2 | Grid Y key        | `grid_y`                       | `y_grid`                        | `y_grid`          |
| 3 | Grid shape        | 2D meshgrid `(res, res)`       | 1D linspace `(res,)`            | 1D (re-meshgrids) |
| 4 | Predictions shape | 2D `(res, res)`                | 1D flat `(res²,)`               | 1D (reshapes)     |
| 5 | Prediction values | Integer class indices (argmax) | Continuous sigmoid (0-1)        | Numeric           |
| 6 | Envelope status   | `"success"`                    | `"ok"`                          | Not checked       |
| 7 | Envelope meta     | Present                        | Absent                          | Not consumed      |

### Audit 2: Demo Mode Forward Pass and Training

- `MockCascorNetwork.forward()` has been fixed to cascade through hidden units (current code is correct)
- Hidden unit weights are random and never trained (no candidate training phase)
- Training is deferred: `_simulate_training_step()` only increments a counter; actual weight updates happen lazily in `get_decision_boundary()` with a cap of 20 steps
- Displayed accuracy is a synthetic exponential decay curve disconnected from actual network performance
- `DemoBackend` returns raw sigmoid outputs (continuous 0-1) instead of argmax class indices

### Audit 3: Grid and Coordinate Handling

- Grid generation math is correct in all paths (meshgrid ordering, ravel order, Plotly z[i,j] convention)
- The double-meshgrid bug (passing 2D arrays to `np.meshgrid()`) would produce `(res², res²)` output if key names were fixed without also fixing dimensionality handling
- Demo mode data flow from meshgrid → component → Plotly is correct

### Audit 4: Visualization Rendering

- Integer class labels produce sharp two-color regions (correct behavior)
- Continuous sigmoid values produce smooth multi-color gradient bands (the observed diagonal stripes)
- The diagonal orientation comes from the random weight vector direction in `sigmoid(w . x + b)`
- Missing `argmax` in demo mode is the primary visual difference from the reference implementation

### Audit 5: Training Fidelity

- With intermittent boundary tab viewing, 55-65% of training steps are permanently lost
- Hidden units with random weights achieve ~55-70% actual accuracy on spiral data (vs displayed 96-98%)
- Each cascade add reinitializes output weights for the new column, disrupting learning
- The deferred training mechanism (counter + lazy flush with cap) is architecturally flawed

### Audit 6: End-to-End Pipeline

- Service mode: KeyError at adapter line 283 → None → 503 error → error dict stored in dcc.Store → empty plot
- Demo mode: Data flows correctly but predictions are wrong (random hidden weights, continuous output)
- HTTP 503 errors are not detected by dashboard manager (no status code check)
- Dataset endpoint in service mode returns metadata only (no inputs/targets), so data point overlay never displays
- `_pending_train_steps` counter has a minor race condition (increment outside lock)

---

## Root Cause Inventory

### Service Mode Root Causes

#### RC-S1: Key Name Mismatch Between Real API and Adapter (CRITICAL)

**Status**: OPEN — previously marked as fixed, but fix was tested only against FakeCascorClient

- **File**: `juniper-canopy/src/backend/cascor_service_adapter.py:283-284`
- **Issue**: Adapter reads `data["x_grid"]` and `data["y_grid"]`; real cascor API returns `grid_x` and `grid_y`
- **Impact**: KeyError caught silently → returns None → 503 error → empty boundary plot

#### RC-S2: Data Dimensionality Mismatch (CRITICAL)

**Status**: OPEN

- **File**: `juniper-canopy/src/backend/cascor_service_adapter.py:289`
- **Issue**: Adapter calls `np.meshgrid(x_grid, y_grid)` assuming 1D input. Real API returns 2D meshgrid arrays. Passing 2D arrays to `np.meshgrid()` produces `(res², res²)` output — catastrophically wrong.
- **Impact**: Even fixing key names alone would produce corrupt grid coordinates

#### RC-S3: FakeCascorClient Divergence from Real API (HIGH)

**Status**: OPEN — must be fixed in juniper-cascor-client repo

- **File**: `juniper-cascor-client/juniper_cascor_client/testing/scenarios.py:441-448`
- **Issue**: `generate_decision_boundary()` returns `x_grid`/`y_grid` (1D) with continuous sigmoid predictions. Real API returns `grid_x`/`grid_y` (2D) with integer argmax predictions.
- **Impact**: All adapter tests pass against the fake but fail against the real service. Tests provide false confidence.

#### RC-S4: HTTP Error Responses Not Detected (MEDIUM)

**Status**: OPEN

- **File**: `juniper-canopy/src/frontend/dashboard_manager.py:1262-1263`
- **Issue**: `requests.get()` does not raise for HTTP 503. Error JSON `{"error": "..."}` is stored as boundary data. The error dict is truthy, so the component treats it as data (falls through to empty arrays).
- **Impact**: Misleading UX — no indication that the backend has data but the adapter failed

#### RC-S5: No Dataset Overlay in Service Mode (MEDIUM)

**Status**: OPEN

- **Issue**: The cascor `/v1/dataset` endpoint returns metadata only (sample counts, feature counts) — no `inputs` or `targets` arrays. The decision boundary component expects `inputs` and `targets` for scatter overlay.
- **Impact**: No data points displayed on the boundary plot in service mode

### Demo Mode Root Causes

#### RC-D1: Hidden Unit Weights Never Trained (CRITICAL)

**Status**: OPEN — the primary cause of the diagonal stripe pattern

- **File**: `juniper-canopy/src/demo_mode.py:113-133`
- **Issue**: `add_hidden_unit()` creates units with `torch.randn(...) * 0.1` weights that are never updated. Real CasCor trains hidden units via candidate correlation maximization. Without trained hidden units, the network is effectively a linear classifier augmented with random noise features.
- **Impact**: Decision boundary is near-linear regardless of training progress

#### RC-D2: Deferred Training Loses Steps (HIGH)

**Status**: OPEN

- **File**: `juniper-canopy/src/backend/demo_backend.py:211-216`
- **Issue**: `min(pending, 20)` cap applies at most 20 training steps per boundary request, but clears ALL accumulated pending steps. When the user is on other tabs, hundreds of steps accumulate but only 20 execute.
- **Impact**: 55-65% of training steps permanently lost under typical usage

#### RC-D3: Synthetic Metrics Disconnected from Network (HIGH)

**Status**: OPEN

- **File**: `juniper-canopy/src/demo_mode.py:537-569`
- **Issue**: Displayed loss/accuracy follows a synthetic exponential decay curve: `loss = target + (loss_prev - target) * 0.95`. This always converges to ~96-98% accuracy regardless of actual network performance.
- **Impact**: User sees high accuracy but boundary looks untrained — confusing and misleading

#### RC-D4: Missing Argmax — Continuous Values Instead of Class Labels (MEDIUM)

**Status**: OPEN

- **File**: `juniper-canopy/src/backend/demo_backend.py:229-230`
- **Issue**: `z = predictions.numpy().flatten()` uses raw sigmoid outputs (0-1 continuous). Real CasCor uses `predictions.argmax(dim=1)` for discrete class indices (0, 1).
- **Impact**: Contour plot shows smooth gradient bands instead of sharp class regions

#### RC-D5: Output Weight Reinitialization on Cascade Add (MEDIUM)

**Status**: OPEN

- **File**: `juniper-canopy/src/demo_mode.py:128-133`
- **Issue**: When a hidden unit is added, the new output weight column is random (`torch.randn * 0.1`). Combined with deferred training (only 20 steps applied), the output layer barely adapts before the next cascade disruption.
- **Impact**: Output weights are perpetually playing catch-up, never converging

### Previously Fixed (Verified by Audit)

| RC | Description | Status |
|----|-------------|--------|
| RC-6 (V1) | `MockCascorNetwork.forward()` ignores hidden units | **FIXED** — forward pass now cascades correctly |
| RC-8 (V1) | No thread safety in `DemoBackend.get_decision_boundary()` | **FIXED** — acquires `self._demo._lock` |
| RC-4 (V1) | Resolution slider not wired to API | **FIXED** |
| RC-5 (V1) | Orphaned component interval | **FIXED** |

---

## Data Contract Analysis

### What the Real CasCor API Returns

```python
# GET /v1/decision-boundary?resolution=50
# Response: success_response(boundary) → {"status": "success", "data": {...}, "meta": {...}}
{
    "data": {
        "x_range": [x_min, x_max],           # [float, float]
        "y_range": [y_min, y_max],           # [float, float]
        "resolution": 50,                     # int
        "grid_x": [[...], ...],              # 2D meshgrid, shape (res, res)
        "grid_y": [[...], ...],              # 2D meshgrid, shape (res, res)
        "predictions": [[0, 1, ...], ...],   # 2D array, shape (res, res), INTEGER class indices
    }
}
```

### What the FakeCascorClient Returns (DIVERGENT)

```python
{
    "data": {
        "x_grid": [-1.5, ..., 1.5],         # 1D array, length=res
        "y_grid": [-1.5, ..., 1.5],         # 1D array, length=res
        "predictions": [0.1, 0.9, ...],     # 1D flat, length=res², CONTINUOUS sigmoid
        "resolution": 50,
        "x_range": [-1.5, 1.5],
        "y_range": [-1.5, 1.5],
    }
}
```

### What the Frontend Component Expects

```python
# boundary_data dict:
{
    "xx": [[...], ...],    # 2D meshgrid, shape (res, res) — xx[0] = 1D x-axis
    "yy": [[...], ...],    # 2D meshgrid, shape (res, res) — yy[:, 0] = 1D y-axis
    "Z": [[...], ...],     # 2D array, shape (res, res) — predictions
    "x_min": float,
    "x_max": float,
    "y_min": float,
    "y_max": float,
    "resolution": int,
}
```

### Required Fix: Canonical Response Format

Both backends (DemoBackend and ServiceBackend) must produce the same format. The adapter must correctly transform the real API response to this format.

**Option chosen**: Fix the adapter to handle the real API's key names and 2D data format directly (no re-meshgrid needed since the API already returns meshgrids).

---

## Implementation Plan

### Phase 1: Fix Service Mode Data Contract (RC-S1, RC-S2, RC-S3)

**Target repos**: juniper-canopy, juniper-cascor-client

#### Step 1.1: Fix CascorServiceAdapter Key Names and Dimensionality

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py:261-310`

Replace the current transformation logic:

```python
# CURRENT (broken):
x_grid = np.array(data["x_grid"])        # KeyError with real API
y_grid = np.array(data["y_grid"])        # KeyError with real API
xx, yy = np.meshgrid(x_grid, y_grid)    # Re-meshgrids (wrong for 2D input)
Z = predictions.reshape(res, res)

# FIXED:
grid_x = np.array(data["grid_x"])       # Match real API key name
grid_y = np.array(data["grid_y"])       # Match real API key name
predictions = np.array(data["predictions"])
# Data is already 2D meshgrid from the API — use directly
xx = grid_x                              # Already (res, res) meshgrid
yy = grid_y                              # Already (res, res) meshgrid
Z = predictions                          # Already (res, res) reshaped
```

#### Step 1.2: Update FakeCascorClient to Match Real API Format

**File**: `juniper-cascor-client/juniper_cascor_client/testing/scenarios.py:392-448`

Change `generate_decision_boundary()` to return:
- Key names: `grid_x`, `grid_y` (matching real API)
- Grid arrays: 2D meshgrid arrays (matching real API)
- Predictions: 2D array of integer class indices (matching real API)

**File**: `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py:596-627`

Update wrapper to match real API response structure.

#### Step 1.3: Add HTTP Error Detection in Dashboard Manager

**File**: `juniper-canopy/src/frontend/dashboard_manager.py:1258-1268`

Add `response.raise_for_status()` or check `response.status_code` before storing boundary data. On error, return `None` instead of the error JSON.

### Phase 2: Fix Demo Mode Decision Boundary (RC-D1, RC-D2, RC-D3, RC-D4, RC-D5)

**Target repo**: juniper-canopy

#### Step 2.1: Implement Simplified Candidate Training for Hidden Units (RC-D1)

**File**: `juniper-canopy/src/demo_mode.py` — `MockCascorNetwork`

Add a `train_candidate()` method that trains the hidden unit weights before installation:

1. Compute residual error: `residual = train_y - forward(train_x)`
2. For N steps (e.g., 50-100): adjust unit weights to maximize correlation with residual
3. Use the correlation-maximization gradient: `d_correlation / d_weights`
4. After training, freeze the unit weights (which happens naturally since only output weights are trained thereafter)

This is a simplified but functional version of the real CasCor candidate training phase. It gives hidden units meaningful feature detectors instead of random projections.

Update `add_hidden_unit()` to call `train_candidate()` before appending the unit.

#### Step 2.2: Remove Deferred Training — Train Inline (RC-D2)

**File**: `juniper-canopy/src/demo_mode.py` — `_simulate_training_step()`
**File**: `juniper-canopy/src/backend/demo_backend.py` — `get_decision_boundary()`

Replace the deferred training mechanism:

- In `_simulate_training_step()`: call `network.train_output_step()` directly (under `_lock`)
- In `get_decision_boundary()`: remove the pending step flush logic (no longer needed)
- Remove `_pending_train_steps` counter entirely

This ensures every simulated epoch results in an actual weight update, eliminating step loss.

#### Step 2.3: Compute Real Metrics from Network (RC-D3)

**File**: `juniper-canopy/src/demo_mode.py` — `_simulate_training_step()`

After performing the actual training step, compute real metrics:

```python
with torch.no_grad():
    predictions = network.forward(network.train_x)
    # Binary classification with single sigmoid output
    pred_classes = (predictions > 0.5).float()
    accuracy = (pred_classes == network.train_y).float().mean().item()
    loss = F.binary_cross_entropy(predictions, network.train_y).item()
```

Use these real values for `self.current_loss` and `self.current_accuracy` instead of the synthetic decay curve. Keep a smoothing average if desired to reduce noise.

#### Step 2.4: Apply Argmax for Binary Classification (RC-D4)

**File**: `juniper-canopy/src/backend/demo_backend.py:229-235`

Change boundary prediction post-processing to produce class labels:

```python
# CURRENT:
z = predictions.numpy().flatten()                    # continuous 0-1
return {"Z": z.reshape(resolution, resolution).tolist(), ...}

# FIXED:
z = (predictions > 0.5).int().numpy().flatten()     # binary class labels 0/1
return {"Z": z.reshape(resolution, resolution).tolist(), ...}
```

Alternatively, keep the continuous output and offer both modes: discrete class labels for "Decision Boundary" view, continuous values for "Confidence" view. The `show_confidence` checkbox already exists in the component UI.

**Chosen approach**: Return continuous sigmoid values but also include class labels. The frontend component already has a "Show Confidence" toggle — use it:
- Show Confidence OFF: threshold at 0.5 for discrete class regions
- Show Confidence ON: show continuous probability heatmap

#### Step 2.5: Fix Output Weight Reinitialization (RC-D5)

**File**: `juniper-canopy/src/demo_mode.py:128-133`

After adding a hidden unit, immediately retrain output weights for several steps to adapt to the new unit:

```python
def add_hidden_unit(self):
    # ... existing unit creation and weight expansion ...
    # Retrain output weights to accommodate new hidden unit
    for _ in range(50):
        self.train_output_step()
```

### Phase 3: Error Handling and UX Improvements

#### Step 3.1: Improve Error Propagation in Dashboard Manager (RC-S4)

**File**: `juniper-canopy/src/frontend/dashboard_manager.py:1258-1268`

Check HTTP status code before storing boundary data.

#### Step 3.2: Add Error State to Decision Boundary Component

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:197-199`

Distinguish between "no data" (None) and "error" (dict with "error" key) responses.

### Phase 4: Cross-Repo Test Alignment

#### Step 4.1: Add Integration Test Against Real API Format

**File**: `juniper-canopy/src/tests/integration/test_decision_boundary_service_mode.py`

Add tests that verify the adapter handles the REAL cascor API format (key names `grid_x`/`grid_y`, 2D arrays, integer predictions).

#### Step 4.2: Add Contract Test in juniper-cascor-client

**File**: `juniper-cascor-client/tests/test_scenarios.py` (or similar)

Add a test that verifies `generate_decision_boundary()` output matches the real API's field names and data shapes.

---

## Testing Plan

### Existing Tests to Update

#### T-1: CascorServiceAdapter Boundary Tests (UPDATE)

**File**: `juniper-canopy/src/tests/unit/backend/test_cascor_service_adapter_boundary.py`

Update to use `grid_x`/`grid_y` key names and 2D array inputs. Add tests for:
- Real API format with 2D meshgrid input
- Real API format with integer predictions
- Backward compatibility with FakeCascorClient format (if retained)

#### T-2: Service Mode Integration Tests (UPDATE)

**File**: `juniper-canopy/src/tests/integration/test_decision_boundary_service_mode.py`

Update FakeCascorClient usage to match real API format after scenarios.py is fixed.

### New Tests

#### T-N1: Adapter Handles Real API Format

Test that `CascorServiceAdapter.get_decision_boundary()` correctly transforms the real cascor API response (2D meshgrids, `grid_x`/`grid_y` keys, integer predictions).

#### T-N2: Mock Network Candidate Training

Test that after `add_hidden_unit()`, the hidden unit's weights are trained (not random) and improve correlation with residual error.

#### T-N3: Inline Training — No Step Loss

Test that every call to `_simulate_training_step()` results in an actual weight change in the network.

#### T-N4: Real Metrics Computation

Test that `current_loss` and `current_accuracy` reflect actual network predictions, not synthetic values.

#### T-N5: Decision Boundary Evolution

Test that the decision boundary data changes meaningfully as training progresses (not just noise but structural improvement).

#### T-N6: Argmax vs Confidence Toggle

Test that boundary data contains appropriate values:
- Class labels (0, 1) for discrete mode
- Continuous probabilities (0.0-1.0) for confidence mode

#### T-N7: HTTP Error Handling in Dashboard Manager

Test that 503 responses do not get stored as boundary data.

#### T-N8: Regression — No Service Mode KeyError

Test that the adapter does not raise KeyError when receiving real API key names (`grid_x`, `grid_y`).

---

## Validation Checklist

### Service Mode

- [ ] CascorServiceAdapter reads `grid_x`/`grid_y` keys (matching real API)
- [ ] Adapter handles 2D meshgrid arrays without re-meshgridding
- [ ] Adapter produces `xx`, `yy`, `Z` in correct 2D format for frontend
- [ ] FakeCascorClient updated to match real API format
- [ ] All existing adapter tests pass with updated format
- [ ] HTTP 503 errors detected and handled gracefully
- [ ] Dashboard manager does not store error JSON as boundary data

### Demo Mode

- [ ] Hidden units have trained weights (not random) after `add_hidden_unit()`
- [ ] `_simulate_training_step()` performs actual weight update (no deferred counter)
- [ ] Displayed accuracy matches actual network prediction accuracy
- [ ] Decision boundary data changes structurally as training progresses
- [ ] Boundary reflects spiral pattern at high accuracy (not linear stripes)
- [ ] Thread safety maintained during concurrent training and boundary computation
- [ ] Cascade adds are followed by output weight retraining

### Cross-Cutting

- [ ] All existing tests pass
- [ ] New tests cover each root cause
- [ ] No regressions in demo mode startup
- [ ] No regressions in service mode connectivity
- [ ] Frontend renders correctly in both modes

---

## Files Modified

### juniper-canopy

| File | Change | Root Cause |
|------|--------|------------|
| `src/backend/cascor_service_adapter.py` | Fix key names (`grid_x`/`grid_y`), handle 2D arrays | RC-S1, RC-S2 |
| `src/demo_mode.py` | Add candidate training, inline weight updates, real metrics | RC-D1, RC-D2, RC-D3 |
| `src/backend/demo_backend.py` | Remove deferred flush, add argmax/confidence toggle | RC-D2, RC-D4 |
| `src/frontend/dashboard_manager.py` | Add HTTP error detection | RC-S4 |
| `src/frontend/components/decision_boundary.py` | Handle error responses, confidence toggle | RC-S4 |
| `src/tests/unit/backend/test_cascor_service_adapter_boundary.py` | Update for real API format | T-1 |
| `src/tests/integration/test_decision_boundary_service_mode.py` | Update for real API format | T-2 |
| `src/tests/unit/test_mock_cascor_forward.py` | Tests for candidate training | T-N2 |
| `src/tests/unit/test_demo_weight_training.py` | Tests for inline training, real metrics | T-N3, T-N4 |
| `src/tests/integration/test_demo_boundary_evolution.py` | Tests for boundary evolution | T-N5 |

### juniper-cascor-client

| File | Change | Root Cause |
|------|--------|------------|
| `juniper_cascor_client/testing/scenarios.py` | Fix key names, 2D format, integer predictions | RC-S3 |
| `juniper_cascor_client/testing/fake_client.py` | Update wrapper to match | RC-S3 |

### No Changes Required

| Repository | Reason |
|------------|--------|
| juniper-cascor | Real API is the source of truth — no changes needed |

---

## Implementation Order

1. **Phase 1.2 first**: Fix FakeCascorClient in juniper-cascor-client (upstream dependency)
2. **Phase 1.1**: Fix CascorServiceAdapter in juniper-canopy
3. **Phase 2.1**: Add candidate training to MockCascorNetwork
4. **Phase 2.2**: Remove deferred training
5. **Phase 2.3**: Compute real metrics
6. **Phase 2.4**: Add argmax/confidence toggle
7. **Phase 2.5**: Fix output weight reinitialization
8. **Phase 3**: Error handling improvements
9. **Phase 4**: Cross-repo test alignment
10. **Final**: Run all tests, commit, create PR(s)

---

## Validation Results

Three independent validation agents reviewed this plan against the source code.

| Area | Verdict | Key Findings |
|------|---------|-------------|
| Service Mode | **VALIDATED** | All 5 claims confirmed. Key name mismatch, 2D data, HTTP 503 — all verified in source. |
| Demo Mode | **VALIDATED** | All claims confirmed. Forward pass cascade works, hidden weights random, deferred training confirmed. Minor: lock acquisition location for inline training needs explicit handling; `_reset_state_and_history()` doesn't reset output weights. |
| Test Coverage | **PARTIAL** | Solid coverage of primary root causes. Gaps: (1) No contract test T-number for Step 4.2; (2) No concurrent cascade-add + boundary test; (3) No test for RC-S5 (missing dataset overlay); (4) Plan omits `test_fake_client.py` and `test_main_api_coverage.py` from files-to-modify list; (5) T-N4/T-N5 need concrete assertions. |

### Adjustments Made from Validation

1. **Step 2.1**: Candidate training learning rate set to 0.1 (higher than output LR of 0.01). Use full training set (not mini-batch) for correlation computation.
2. **Step 2.2**: Lock acquisition added explicitly inside `_simulate_training_step()` around the `train_output_step()` call.
3. **Step 2.5**: Note that 50 `train_output_step()` calls under lock blocks boundary requests for ~10-50ms. Acceptable for demo mode.
4. **Added T-N9**: Contract test for FakeCascorClient matching real API schema (Step 4.2).
5. **Added T-N10**: Concurrent cascade-add + boundary computation thread safety test.
6. **Files Modified table updated**: Added `test_fake_client.py` (juniper-cascor-client) and `test_main_api_coverage.py` (juniper-canopy).

---

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2026-03-17 | Paul Calnon (via Claude Code) | V2 created from comprehensive 6-agent audit. Identifies service mode as still broken. Adds RC-S1 through RC-S5 and RC-D1 through RC-D5. Supersedes V1. |
| 2026-03-17 | Paul Calnon (via Claude Code) | Added validation results from 3 validation agents. Updated plan with gaps found. Status changed to Implementation In Progress. |
