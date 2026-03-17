# Canopy Decision Boundary Fix Plan

**Project**: JuniperCanopy — Decision Boundary Visualization
**Created**: 2026-03-16
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Phase 2 Implementation In Progress
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor-client referenced)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Analysis Summary](#analysis-summary)
- [Root Causes](#root-causes)
- [Data Contract Analysis](#data-contract-analysis)
- [Reference Implementation Comparison](#reference-implementation-comparison)
- [Implementation Plan](#implementation-plan)
- [Testing Plan](#testing-plan)
- [Validation Checklist](#validation-checklist)
- [Files Modified](#files-modified)
- [Troubleshooting Log](#troubleshooting-log)

---

## Problem Statement

The juniper-canopy application displays a decision boundary plot that illustrates the current CasCor network's classification of the input dataset. The decision boundary **never updates during training** — it remains identical from epoch 0 through 96%+ accuracy. This affects both demo mode and service mode, though via different mechanisms.

### Observed Behavior (2026-03-17)

- Application running in **demo mode** (localhost:8050)
- Network training to 96% accuracy with 6 hidden units
- Decision boundary plot shows a near-linear gradient (0.3–0.7 range) — characteristic of initial random weights with no hidden unit contributions
- Plot does not change when training progresses, hidden units are added, or accuracy improves
- Refresh button has no visible effect (boundary data is recomputed but weights are unchanged)
- Resolution slider has no effect on boundary shape (same stale predictions at any resolution)

---

## Analysis Summary

### Architecture Overview

The decision boundary visualization follows a three-layer architecture:

```bash
Frontend (Dash)                    Backend (FastAPI)                 CasCor Service
┌──────────────────┐     GET      ┌──────────────────┐   REST     ┌───────────────────┐
│ DecisionBoundary │ ←─────────── │ /api/decision_   │ ←───────── │  /v1/decision-    │
│ component        │  every 5s    │   boundary       │            │    boundary       │
│                  │  (slow-      │                  │            │                   │
│ dashboard_       │   update-    │ DemoBackend or   │   via      │ TrainingLifecycle │
│   manager.py     │   interval)  │ ServiceBackend   │  cascor-   │    Manager        │
│                  │              │   .get_decision_ │  client    │                   │
│                  |              │    boundary()    │            │                   │
└──────────────────┘              └──────────────────┘            └───────────────────┘
```

### Current Behavior by Backend Mode

| Mode        | Backend Class    | Behavior                                                             | Result                                      |
|-------------|------------------|----------------------------------------------------------------------|---------------------------------------------|
| **Demo**    | `DemoBackend`    | Computes boundary via `MockCascorNetwork.forward()`                  | **Broken** — always returns initial weights |
| **Service** | `ServiceBackend` | Delegates to `CascorServiceAdapter` → juniper-cascor-client → CasCor | **Fixed (2026-03-17)** — returns live data  |

### Key Discoveries

**Demo Mode (primary issue):**

1. `MockCascorNetwork.forward()` ignores hidden units entirely — only uses initial `input_weights`
2. `_simulate_training_step()` never modifies network weights — only updates synthetic loss/accuracy metrics
3. `DemoBackend.get_decision_boundary()` has no thread safety when accessing the network during training
4. The combination means the decision boundary is frozen at epoch-0 random weights forever

**Service Mode (previously fixed):**

1. `ServiceBackend` now delegates to `CascorServiceAdapter` (fixed 2026-03-16)
2. `CascorServiceAdapter.get_decision_boundary()` transforms CasCor 1D format to frontend 2D format (fixed 2026-03-16)
3. Resolution slider now wired to API request (fixed 2026-03-17, PR #24)

---

## Root Causes

### Phase 1 Root Causes (Service Mode — FIXED)

#### RC-1: ServiceBackend.get_decision_boundary() Returns None ✅ FIXED

**File**: `juniper-canopy/src/backend/service_backend.py:111-112`
**Status**: Fixed — now delegates to `self._adapter.get_decision_boundary(resolution)`

#### RC-2: CascorServiceAdapter Lacks Decision Boundary Delegation ✅ FIXED

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py:261-310`
**Status**: Fixed — `get_decision_boundary()` method with full 1D→2D transform implemented

#### RC-3: Data Contract Mismatch Between CasCor Service and Frontend ✅ FIXED

**Status**: Fixed — `CascorServiceAdapter.get_decision_boundary()` performs the transform

#### RC-4: Resolution Slider Not Wired to API ✅ FIXED

**File**: `juniper-canopy/src/frontend/dashboard_manager.py:765-773, 1251-1265`
**Status**: Fixed — resolution slider value passed to API endpoint as query parameter (PR #24)

#### RC-5: Orphaned Component Interval ✅ FIXED

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py`
**Status**: Fixed — orphaned `dcc.Interval` removed

### Phase 2 Root Causes (Demo Mode — ACTIVE)

#### RC-6: MockCascorNetwork.forward() Ignores Hidden Units (CRITICAL)

**File**: `juniper-canopy/src/demo_mode.py:135-152`

```python
def forward(self, x: torch.Tensor) -> torch.Tensor:
    if len(self.hidden_units) == 0:
        output = torch.matmul(x, self.input_weights) + self.output_bias
    else:
        # Include hidden unit contributions (simplified)
        output = torch.matmul(x, self.input_weights[: x.shape[1], :]) + self.output_bias
    return torch.sigmoid(output)
```

**Impact**: Even when hidden units are added during training (via `add_hidden_unit()` at line 628), the `forward()` method **never processes data through them**. The `else` branch is misleadingly labeled "Include hidden unit contributions" but only slices `input_weights` — it never reads `hidden_units[i]["weights"]`, `hidden_units[i]["bias"]`, or `hidden_units[i]["activation_fn"]`.

**Comparison with juniper-cascor reference** (`cascade_correlation.py:1184-1225`):

```python
# CasCor's forward() properly cascades through all hidden units:
hidden_outputs = []
for unit in self.hidden_units:
    unit_input = torch.cat([x] + hidden_outputs, dim=1)
    unit_output = unit["activation_fn"](torch.sum(unit_input * unit["weights"], ...) + unit["bias"])
    hidden_outputs.append(unit_output)
output_input = torch.cat([x] + hidden_outputs, dim=1)
output = torch.matmul(output_input, self.output_weights) + self.output_bias
```

#### RC-7: _simulate_training_step() Never Updates Network Weights (CRITICAL)

**File**: `juniper-canopy/src/demo_mode.py:468-489`

```python
def _simulate_training_step(self) -> Tuple[float, float]:
    # Only updates: self.current_loss, self.current_accuracy (synthetic metrics)
    # Never touches: network.input_weights, network.output_weights, network.output_bias
    # Never touches: network.hidden_units[i]["weights"], ["bias"]
    self.current_loss = self.target_loss + (self.current_loss - self.target_loss) * (1 - decay_rate)
    self.current_accuracy = 1.0 - (self.current_loss / 2.0)
    return self.current_loss, self.current_accuracy
```

**Impact**: The network's actual prediction function is completely disconnected from the reported training metrics. Loss/accuracy values decay synthetically but the network weights that determine the decision boundary are frozen at their random initialization values.

**What the training loop does vs. what it should do:**

| Operation                  | Training Loop Does       | Effect on Boundary               |
|----------------------------|--------------------------|----------------------------------|
| Update loss/accuracy       | ✅ Yes (synthetic)       | ❌ None — metrics only           |
| Update output weights      | ❌ No                    | ❌ Boundary frozen               |
| Add hidden units           | ✅ Yes (add_hidden_unit) | ❌ None — forward() ignores them |
| Update hidden unit weights | ❌ No                    | ❌ Boundary frozen               |

#### RC-8: No Thread Safety in DemoBackend.get_decision_boundary()

**File**: `juniper-canopy/src/backend/demo_backend.py:218-221`

```python
with torch.no_grad():
    grid_tensor = torch.from_numpy(grid_points).float()
    predictions = network.forward(grid_tensor)  # NO LOCK!
    z = predictions.numpy().flatten()
```

**Impact**: The training thread modifies network state under `self._demo._lock` (lines 587-638), including reshaping `output_weights` when adding hidden units. But `DemoBackend.get_decision_boundary()` calls `network.forward()` without acquiring the lock, creating a race condition that can cause tensor shape mismatches.

**Comparison with juniper-cascor reference** (`lifecycle/manager.py:542`):

```python
# CasCor uses _topology_lock for thread safety:
with self._topology_lock, torch.no_grad():
    predictions = self.network.forward(grid_tensor)
```

#### RC-9: predict_fn Never Set on DecisionBoundary Component (Minor)

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:74`

```python
self.predict_fn: Optional[Callable] = None  # Initialized but never set
```

The `set_prediction_function()` method exists (line 415) but is never called from `DashboardManager` or any other code. This means the component's built-in client-side boundary computation is permanently disabled.

**Impact**: Minor — the backend API path is the primary update mechanism. This is a dead code path.

---

## Data Contract Analysis

### CasCor Service Response (via juniper-cascor-client)

```python
# Response from client.get_decision_boundary(resolution=50)
{
    "status": "ok",
    "data": {
        "x_grid": [-1.5, -1.44, ..., 1.5],        # 1D, length=resolution
        "y_grid": [-1.5, -1.44, ..., 1.5],        # 1D, length=resolution
        "predictions": [0.1, 0.9, ..., 0.5],      # 1D flattened, length=resolution²
        "resolution": 50,
        "x_range": [-1.5, 1.5],
        "y_range": [-1.5, 1.5],
    }
}
```

### DemoBackend Response (current format)

```python
{
    "xx": [[...], ...],     # 2D meshgrid, shape (resolution, resolution)
    "yy": [[...], ...],     # 2D meshgrid, shape (resolution, resolution)
    "Z": [[...], ...],      # 2D predictions, shape (resolution, resolution)
    "x_min": float,
    "x_max": float,
    "y_min": float,
    "y_max": float,
    "resolution": int,
}
```

### Frontend Consumption (`_create_boundary_plot`)

```python
xx = np.array(boundary_data["xx"])    # expects 2D
yy = np.array(boundary_data["yy"])    # expects 2D
Z = np.array(boundary_data["Z"])      # expects 2D

# Plotly contour uses:
x = xx[0]        # 1D x-axis values (first row of meshgrid)
y = yy[:, 0]     # 1D y-axis values (first column of meshgrid)
z = Z             # 2D prediction grid
```

---

## Reference Implementation Comparison

### juniper-cascor (Known Good)

| Aspect                 | Implementation                                                                   | File:Line                           |
|------------------------|----------------------------------------------------------------------------------|-------------------------------------|
| Forward pass           | Cascades through all hidden units sequentially                                   | `cascade_correlation.py:1184-1225`  |
| Hidden unit processing | `unit_input = torch.cat([x] + hidden_outputs, dim=1)`                            | `cascade_correlation.py:1210`       |
| Output layer           | `torch.matmul(output_input, self.output_weights) + self.output_bias`             | `cascade_correlation.py:1222`       |
| Thread safety          | `with self._topology_lock, torch.no_grad()`                                      | `lifecycle/manager.py:542`          |
| Weight updates         | Real gradient descent on output weights + correlation-based hidden unit training | Throughout `cascade_correlation.py` |
| Grid bounds            | Derived from training data: `self._train_x`                                      | `lifecycle/manager.py:543-545`      |

### juniper-canopy MockCascorNetwork (Broken)

| Aspect                 | Implementation                                                           | Issue                                                |
|------------------------|--------------------------------------------------------------------------|------------------------------------------------------|
| Forward pass           | `torch.matmul(x, self.input_weights[:x.shape[1], :]) + self.output_bias` | Hidden units ignored                                 |
| Hidden unit processing | None                                                                     | `hidden_units` list elements never read in forward() |
| Output layer           | Same as above (no separate output layer)                                 | `output_weights` never used in forward()             |
| Thread safety          | None                                                                     | No lock acquired before network.forward()            |
| Weight updates         | None                                                                     | `_simulate_training_step()` only updates metrics     |
| Grid bounds            | Correct — derived from dataset inputs                                    | OK                                                   |

### Required Fixes to Match Reference

1. **`forward()` must cascade through hidden units** — matching the cascor architecture where each hidden unit receives [inputs + all previous hidden outputs]
2. **Output layer must use `output_weights`** — the final prediction combines [inputs + all hidden outputs] × output_weights
3. **Weights must evolve during training** — simulated weight updates that progressively improve classification accuracy
4. **Thread safety** — acquire `_lock` before calling `network.forward()` in boundary computation

---

## Implementation Plan

### Phase 1: ServiceBackend Decision Boundary (RC-1, RC-2, RC-3) ✅ COMPLETE

#### Step 1.1: Add `get_decision_boundary()` to CascorServiceAdapter ✅

**Status**: Implemented in `cascor_service_adapter.py:261-310`

#### Step 1.2: Update ServiceBackend to Delegate ✅

**Status**: Implemented in `service_backend.py:111-112`

### Phase 2: Demo Mode Decision Boundary (RC-6, RC-7, RC-8)

#### Step 2.1: Fix MockCascorNetwork.forward() to Cascade Through Hidden Units

**File**: `juniper-canopy/src/demo_mode.py:135-152`

Replace the broken forward() with a proper cascade-correlation forward pass:

1. If no hidden units: `output = matmul(x, output_weights[:input_size, :].T) + output_bias`
2. If hidden units: cascade through each unit, building up `[x, h0, h1, ...]`, then apply output weights
3. Final output through sigmoid activation

The implementation must match the real CasCor forward() architecture:

- Each hidden unit receives all inputs + all previous hidden outputs
- Hidden unit output = activation_fn(sum(unit_input * weights) + bias)
- Output = sigmoid(matmul(full_features, output_weights.T) + output_bias)

#### Step 2.2: Simulate Weight Training in _simulate_training_step()

**File**: `juniper-canopy/src/demo_mode.py:468-489`

Add a lightweight weight update to make the boundary evolve during training:

1. After computing synthetic loss/accuracy, perform a simple gradient step on `output_weights`
2. Use the stored training data (`network.train_x`, `network.train_y`) to compute a mini-batch gradient
3. Apply a small learning rate update so weights improve progressively
4. This makes the decision boundary visually evolve, matching the synthetic accuracy trajectory

Alternatively, a simpler approach:

- Use `torch.optim.SGD` on `output_weights` and `output_bias` per training step
- Compute forward pass on training data, compute binary cross-entropy loss, backprop
- This gives a real (if simplified) training signal to the output layer

#### Step 2.3: Add Thread Safety to DemoBackend.get_decision_boundary()

**File**: `juniper-canopy/src/backend/demo_backend.py:218-221`

Acquire `self._demo._lock` before calling `network.forward()`:

```python
with self._demo._lock, torch.no_grad():
    grid_tensor = torch.from_numpy(grid_points).float()
    predictions = network.forward(grid_tensor)
    z = predictions.numpy().flatten()
```

### Phase 3: Resolution Slider Wiring (RC-4) ✅ COMPLETE

#### Step 3.1: Add Resolution Query Parameter to Endpoint ✅

**Status**: Already implemented in `main.py:624-637`

#### Step 3.2: Wire Frontend Resolution Slider to API ✅

**Status**: Implemented in PR #24 (`dashboard_manager.py`)

### Phase 4: Clean Up (RC-5, RC-9)

#### Step 4.1: Remove Orphaned Interval ✅ COMPLETE

#### Step 4.2: Remove Dead predict_fn Code Path (Optional)

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py`

The `set_prediction_function()` method and `self.predict_fn` attribute are dead code — never called by any consumer. Consider removing or documenting as future extension point.

---

## Testing Plan

### Existing Unit Tests (Phase 1 — All Passing) ✅

#### T-1: CascorServiceAdapter.get_decision_boundary() ✅

**File**: `src/tests/unit/backend/test_cascor_service_adapter_boundary.py`
16 tests covering transform, shapes, error handling, frontend compatibility.
Tests:

- `test_get_decision_boundary_transforms_response`: Verify 1D CasCor format → 2D frontend format
- `test_get_decision_boundary_returns_none_on_client_error`: Verify graceful error handling
- `test_get_decision_boundary_passes_resolution_to_client`: Verify resolution parameter forwarded
- `test_get_decision_boundary_meshgrid_shape`: Verify xx/yy are 2D with correct shape
- `test_get_decision_boundary_Z_shape_matches_resolution`: Verify Z is (resolution, resolution)
- `test_get_decision_boundary_returns_none_when_not_found`: Verify 404 handling (no network)

#### T-2: ServiceBackend.get_decision_boundary() ✅

**File**: `src/tests/unit/backend/test_service_backend_boundary.py`
5 tests covering delegation, resolution forwarding, None propagation.
Tests:

- `test_get_decision_boundary_delegates_to_adapter`: Verify delegation instead of `None`
- `test_get_decision_boundary_with_custom_resolution`: Verify resolution passed through
- `test_get_decision_boundary_returns_none_on_adapter_failure`: Verify None propagation

#### T-3: API Endpoint Resolution Parameter ✅

**File**: `src/tests/regression/test_topology_boundary_data_contract.py`
Tests for resolution param acceptance, clamping (5-200), default value.
Tests:

- `test_decision_boundary_default_resolution`: Verify default resolution=100
- `test_decision_boundary_custom_resolution`: Verify custom resolution accepted
- `test_decision_boundary_resolution_out_of_range`: Verify validation (5-200)

### Integration Tests

#### T-4: End-to-End Decision Boundary Flow (Service Mode) ✅

**File**: `src/tests/integration/test_decision_boundary_service_mode.py`
10 tests covering full pipeline with FakeCascorClient.
Tests:

- `test_decision_boundary_service_mode_returns_data`: Full flow with FakeCascorClient
- `test_decision_boundary_data_contract_service_mode`: Verify response matches frontend expectations
- `test_decision_boundary_periodic_refresh`: Verify data changes with network state changes

### Regression Tests

#### T-5: Data Contract Regression Tests ✅

**File**: Extend `test_topology_boundary_data_contract.py`
Tests for key names (xx/yy/Z), 2D shapes, service mode contract.
Tests:

- `test_service_backend_boundary_uses_xx_key`: Verify transformed response uses `xx` not `x_grid`
- `test_service_backend_boundary_uses_yy_key`: Verify `yy` not `y_grid`
- `test_service_backend_boundary_uses_uppercase_Z_key`: Verify `Z` not `predictions`
- `test_service_backend_boundary_xx_yy_are_2d`: Verify 2D meshgrid arrays
- `test_service_backend_boundary_Z_shape_matches_grid`: Verify Z matches resolution

### New Tests (Phase 2)

#### T-6: MockCascorNetwork.forward() Cascade Architecture

**File**: `src/tests/unit/test_mock_cascor_forward.py` (new)
Tests:

- `test_forward_no_hidden_units_produces_output`: Basic forward pass with no hidden units
- `test_forward_with_hidden_units_changes_output`: Adding hidden units changes forward() output
- `test_forward_cascade_processes_all_hidden_units`: Each hidden unit contributes to output
- `test_forward_output_shape_correct`: Output shape is (batch_size, output_size)
- `test_forward_hidden_unit_receives_all_prior_outputs`: Cascade architecture validated
- `test_forward_uses_output_weights`: Output layer uses output_weights, not input_weights
- `test_forward_different_weights_different_output`: Modifying weights changes predictions

#### T-7: Weight Training Simulation

**File**: `src/tests/unit/test_demo_weight_training.py` (new)
Tests:

- `test_training_step_modifies_output_weights`: Weights change after training step
- `test_training_reduces_loss_over_steps`: Loss decreases over multiple steps
- `test_boundary_changes_after_training`: Decision boundary data differs after training steps
- `test_boundary_evolves_with_hidden_units`: Adding hidden units changes boundary shape
- `test_training_thread_safety`: Concurrent access with lock doesn't crash

#### T-8: DemoBackend Thread Safety

**File**: `src/tests/unit/test_demo_backend_thread_safety.py` (new)
Tests:

- `test_get_decision_boundary_acquires_lock`: Verify lock is acquired during computation
- `test_concurrent_boundary_and_training`: Boundary computation during active training doesn't crash
- `test_boundary_during_hidden_unit_addition`: Boundary computation while add_hidden_unit() runs

#### T-9: Demo Mode Boundary Evolution (Integration)

**File**: `src/tests/integration/test_demo_boundary_evolution.py` (new)
Tests:

- `test_boundary_data_changes_during_training`: Run N training steps, verify boundary data at each step differs
- `test_boundary_api_returns_fresh_data`: Consecutive API calls during training return different Z values
- `test_demo_boundary_data_contract`: Verify demo mode response matches frontend expectations (xx/yy/Z format)

---

## Validation Checklist

### Phase 1 (Service Mode) ✅ COMPLETE

- [x] ServiceBackend.get_decision_boundary() returns valid data (not None)
- [x] CascorServiceAdapter correctly transforms CasCor response to frontend format
- [x] xx and yy are 2D meshgrid arrays in the response
- [x] Z is a 2D array with shape (resolution, resolution)
- [x] API endpoint accepts resolution query parameter
- [x] Error cases return None gracefully (no 500 errors)
- [x] New tests cover service mode decision boundary
- [x] Data contract regression tests cover both backend modes
- [x] Resolution slider wired to API request (PR #24)

### Phase 2 (Demo Mode) — IN PROGRESS

- [ ] MockCascorNetwork.forward() cascades through hidden units
- [ ] Hidden unit weights/biases/activations are used in forward pass
- [ ] _simulate_training_step() updates network weights
- [ ] Decision boundary data changes as training progresses
- [ ] DemoBackend.get_decision_boundary() acquires _lock
- [ ] No race conditions during concurrent training and boundary computation
- [ ] Existing DemoBackend tests continue to pass
- [ ] All existing tests continue to pass
- [ ] New tests verify boundary evolution during training
- [ ] Frontend renders correctly with evolving boundary data

---

## Files Modified

### Phase 1 (Service Mode) ✅ COMPLETE

| File                                                             | Change                                                     | Root Cause |     Status       |
|------------------------------------------------------------------|------------------------------------------------------------|------------|------------------|
| `src/backend/cascor_service_adapter.py`                          | Add `get_decision_boundary()` with format transformation   | RC-2, RC-3 | ✅ Done          |
| `src/backend/service_backend.py`                                 | Delegate to adapter instead of returning None              | RC-1       | ✅ Done          |
| `src/main.py`                                                    | Add resolution query parameter to `/api/decision_boundary` | RC-4       | ✅ Done          |
| `src/frontend/components/decision_boundary.py`                   | Remove orphaned `dcc.Interval`                             | RC-5       | ✅ Done          |
| `src/frontend/dashboard_manager.py`                              | Pass resolution to API request                             | RC-4       | ✅ Done (PR #24) |
| `src/tests/unit/backend/test_cascor_service_adapter_boundary.py` | Adapter transformation tests                               | T-1        | ✅ Done          |
| `src/tests/unit/backend/test_service_backend_boundary.py`        | Delegation tests                                           | T-2        | ✅ Done          |
| `src/tests/integration/test_decision_boundary_service_mode.py`   | End-to-end service mode tests                              | T-4        | ✅ Done          |
| `src/tests/regression/test_topology_boundary_data_contract.py`   | Service mode contract tests                                | T-5        | ✅ Done          |

### Phase 2 (Demo Mode) — IN PROGRESS

| File                                                         | Change                                               | Root Cause |
|--------------------------------------------------------------|------------------------------------------------------|------------|
| `src/demo_mode.py`                                           | Fix forward() cascade + add weight training          | RC-6, RC-7 |
| `src/backend/demo_backend.py`                                | Add thread safety (acquire _lock)                    | RC-8       |
| `src/tests/unit/test_mock_cascor_forward.py`                 | New: cascade forward tests                           | T-6        |
| `src/tests/unit/test_demo_weight_training.py`                | New: weight training simulation tests                | T-7        |
| `src/tests/unit/test_demo_backend_thread_safety.py`          | New: thread safety tests                             | T-8        |
| `src/tests/integration/test_demo_boundary_evolution.py`      | New: boundary evolution integration tests            | T-9        |

>>>>>>> 79d47ea (docs: update decision boundary fix plan with Phase 2 analysis)

### No changes required

| Repository            | Reason                                                    |
|-----------------------|-----------------------------------------------------------|
| juniper-cascor        | `/v1/decision-boundary` endpoint already exists and works |
| juniper-cascor-client | `get_decision_boundary()` method already exists           |

---


## Troubleshooting Log

### 2026-03-17: Investigation of Stale Decision Boundary in Demo Mode

**Symptom**: Decision boundary plot at 96% accuracy is identical to epoch 0. Near-linear gradient (0.3–0.7) suggesting untrained random weights.

**Investigation Process**:

1. **Screenshot analysis**: The contour plot shows values ranging 0.3–0.7 with a mostly linear gradient. This is characteristic of `sigmoid(Wx + b)` with small random weights — exactly what `MockCascorNetwork.__init__` produces with `torch.randn(...) * 0.1`.

2. **Forward pass audit**: Read `demo_mode.py:135-152`. Found that `forward()` only uses `input_weights` in a single matrix multiply, completely ignoring the `hidden_units` list. The `else` branch does `self.input_weights[:x.shape[1], :]` — a dimension slice, not cascade processing.

3. **Training step audit**: Read `demo_mode.py:468-489`. Confirmed that `_simulate_training_step()` only updates `self.current_loss` and `self.current_accuracy` via exponential decay formulas. No tensor operations on any network weight attributes.

4. **Reference comparison**: Read juniper-cascor's `cascade_correlation.py:1184-1225` and `lifecycle/manager.py:527-566`. The real CasCor properly cascades through hidden units in `forward()` and uses `_topology_lock` for thread-safe boundary computation.

5. **Thread safety audit**: Confirmed `DemoBackend.get_decision_boundary()` at line 220 calls `network.forward()` without acquiring `self._demo._lock`, while the training loop modifies network state under that lock.

**Root causes identified**: RC-6 (forward ignores hidden units), RC-7 (weights never trained), RC-8 (no thread safety).

---

## Document History

| Date       | Author                        | Change                                                                                     |
|------------|-------------------------------|--------------------------------------------------------------------------------------------|
| 2026-03-16 | Paul Calnon (via Claude Code) | Initial creation — service mode root causes (RC-1 through RC-5)                            |
| 2026-03-17 | Paul Calnon (via Claude Code) | Phase 1 marked complete. Added demo mode root causes (RC-6 through RC-9). Updated plan.    |
| 2026-03-17 | Paul Calnon (via Claude Code) | Added reference implementation comparison, troubleshooting log, Phase 2 implementation plan |

---
