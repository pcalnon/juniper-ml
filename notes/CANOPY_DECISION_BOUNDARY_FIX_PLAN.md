# Canopy Decision Boundary Fix Plan

**Project**: JuniperCanopy — Decision Boundary Visualization
**Created**: 2026-03-16
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Implementation In Progress
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor-client referenced)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Analysis Summary](#analysis-summary)
- [Root Causes](#root-causes)
- [Data Contract Analysis](#data-contract-analysis)
- [Implementation Plan](#implementation-plan)
- [Testing Plan](#testing-plan)
- [Validation Checklist](#validation-checklist)
- [Files Modified](#files-modified)

---

## Problem Statement

The juniper-canopy application displays a decision boundary plot that illustrates the current CasCor network's classification of the input dataset. Currently, this calculation is either not being performed, or is only being performed once when the application is launched.

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
│ dashboard_       │   update-    │ ServiceBackend   │   via      │ TrainingLifecycle │
│   manager.py     │   interval)  │   .get_decision_ │  cascor-   │    Manager        │
│                  │              │    boundary()    │  client    │                   │
└──────────────────┘              └──────────────────┘            └───────────────────┘
```

### Current Behavior by Backend Mode

| Mode        | Backend Class    | Behavior                                             | Result                          |
|-------------|------------------|------------------------------------------------------|---------------------------------|
| **Demo**    | `DemoBackend`    | Computes boundary in-process via `network.forward()` | Works — updated every 5 seconds |
| **Service** | `ServiceBackend` | Returns `None` (hardcoded)                           | **Broken** — always returns 503 |

### Key Discovery

The entire pipeline for service mode decision boundary computation already exists but is disconnected:

1. **juniper-cascor** serves `GET /v1/decision-boundary` with full grid predictions
2. **juniper-cascor-client** has `get_decision_boundary(resolution)` method
3. **CascorServiceAdapter** in juniper-canopy has access to the client
4. **ServiceBackend** simply returns `None` instead of using the adapter

---

## Root Causes

### RC-1: ServiceBackend.get_decision_boundary() Returns None (CRITICAL)

**File**: `juniper-canopy/src/backend/service_backend.py:111-114`

```python
def get_decision_boundary(self, resolution: int = 50) -> Optional[Dict[str, Any]]:
    # Decision boundary computation requires in-process network access.
    # Not available over REST — returns None.
    return None
```

**Impact**: In production mode (connected to a real CasCor service), the decision boundary is never computed. The `/api/decision_boundary` endpoint always returns 503.

**Root Issue**: The comment states "not available over REST" — but it IS available. The `juniper-cascor` service has a `/v1/decision-boundary` endpoint, and `juniper-cascor-client` exposes `get_decision_boundary()`. This was likely written before the CasCor endpoint existed.

### RC-2: CascorServiceAdapter Lacks Decision Boundary Delegation

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Impact**: Even if `ServiceBackend` tried to delegate, there's no method on `CascorServiceAdapter` to call the client's `get_decision_boundary()`. The adapter currently only has `get_prediction_function() -> None`.

### RC-3: Data Contract Mismatch Between CasCor Service and Frontend

The CasCor service returns a different data format than what the frontend expects:

| Field         | CasCor Service                                   | Frontend Expected                           |
|---------------|--------------------------------------------------|---------------------------------------------|
| X coordinates | `x_grid` (1D array, length=resolution)           | `xx` (2D meshgrid, resolution × resolution) |
| Y coordinates | `y_grid` (1D array, length=resolution)           | `yy` (2D meshgrid, resolution × resolution) |
| Predictions   | `predictions` (1D flattened, length=resolution²) | `Z` (2D array, resolution × resolution)     |
| X bounds      | `x_range` ([min, max])                           | `x_min`, `x_max` (separate keys)            |
| Y bounds      | `y_range` ([min, max])                           | `y_min`, `y_max` (separate keys)            |

The ServiceBackend must transform the CasCor response into the frontend format.

### RC-4: API Resolution Hardcoded

**File**: `juniper-canopy/src/main.py:631`

```python
boundary = backend.get_decision_boundary(100)
```

The resolution is hardcoded to 100, ignoring the frontend's resolution slider. While the slider currently only affects local computation (when `predict_fn` is used), the API should accept resolution as a query parameter to allow the frontend to request different resolutions.

### RC-5: Orphaned Component Interval (Minor)

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:156`

```python
dcc.Interval(id=f"{self.component_id}-update-interval", interval=2000, n_intervals=0)
```

This 2-second interval is defined but never connected to any callback. It creates confusion about the update mechanism. The actual updates come from `slow-update-interval` (5 seconds) in `dashboard_manager.py`.

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

### DemoBackend Response (current working format)

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

### Required Transformation

```python
# CasCor response → Frontend format
import numpy as np

x_grid = np.array(data["x_grid"])                    # 1D
y_grid = np.array(data["y_grid"])                    # 1D
predictions = np.array(data["predictions"])           # 1D flattened
resolution = data["resolution"]

xx, yy = np.meshgrid(x_grid, y_grid)                # → 2D meshgrids
Z = predictions.reshape(resolution, resolution)       # → 2D grid

result = {
    "xx": xx.tolist(),
    "yy": yy.tolist(),
    "Z": Z.tolist(),
    "x_min": data["x_range"][0],
    "x_max": data["x_range"][1],
    "y_min": data["y_range"][0],
    "y_max": data["y_range"][1],
    "resolution": resolution,
}
```

---

## Implementation Plan

### Phase 1: ServiceBackend Decision Boundary (RC-1, RC-2, RC-3)

#### Step 1.1: Add `get_decision_boundary()` to CascorServiceAdapter

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

Add a new method that:

1. Calls `self._client.get_decision_boundary(resolution)`
2. Transforms the CasCor response format to the frontend format (1D → 2D meshgrid)
3. Handles errors gracefully (returns `None` on failure)

#### Step 1.2: Update ServiceBackend to Delegate

**File**: `juniper-canopy/src/backend/service_backend.py:111-114`

Replace the hardcoded `return None` with delegation to `self._adapter.get_decision_boundary(resolution)`.

### Phase 2: API Resolution Parameter (RC-4)

#### Step 2.1: Add Resolution Query Parameter to Endpoint

**File**: `juniper-canopy/src/main.py`

Change the `/api/decision_boundary` endpoint to accept an optional `resolution` query parameter (default: 100, range: 5-200).

#### Step 2.2: Wire Frontend Resolution Slider to API

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

Update `_update_boundary_store_handler` to pass the current resolution value from the slider to the API request URL as a query parameter.

### Phase 3: Clean Up Orphaned Interval (RC-5)

#### Step 3.1: Remove Orphaned Interval

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py:156`

Remove the orphaned `dcc.Interval` component. Updates are managed by `dashboard_manager.py`'s `slow-update-interval`.

---

## Testing Plan

### Unit Tests

#### T-1: CascorServiceAdapter.get_decision_boundary()

**File**: New test or extend existing adapter tests

Tests:

- `test_get_decision_boundary_transforms_response`: Verify 1D CasCor format → 2D frontend format
- `test_get_decision_boundary_returns_none_on_client_error`: Verify graceful error handling
- `test_get_decision_boundary_passes_resolution_to_client`: Verify resolution parameter forwarded
- `test_get_decision_boundary_meshgrid_shape`: Verify xx/yy are 2D with correct shape
- `test_get_decision_boundary_Z_shape_matches_resolution`: Verify Z is (resolution, resolution)
- `test_get_decision_boundary_returns_none_when_not_found`: Verify 404 handling (no network)

#### T-2: ServiceBackend.get_decision_boundary()

**File**: Extend existing service backend tests

Tests:

- `test_get_decision_boundary_delegates_to_adapter`: Verify delegation instead of `None`
- `test_get_decision_boundary_with_custom_resolution`: Verify resolution passed through
- `test_get_decision_boundary_returns_none_on_adapter_failure`: Verify None propagation

#### T-3: API Endpoint Resolution Parameter

**File**: Extend existing endpoint tests

Tests:

- `test_decision_boundary_default_resolution`: Verify default resolution=100
- `test_decision_boundary_custom_resolution`: Verify custom resolution accepted
- `test_decision_boundary_resolution_out_of_range`: Verify validation (5-200)

### Integration Tests

#### T-4: End-to-End Decision Boundary Flow (Service Mode)

Tests:

- `test_decision_boundary_service_mode_returns_data`: Full flow with FakeCascorClient
- `test_decision_boundary_data_contract_service_mode`: Verify response matches frontend expectations
- `test_decision_boundary_periodic_refresh`: Verify data changes with network state changes

### Regression Tests

#### T-5: Data Contract Consistency

**File**: Extend `test_topology_boundary_data_contract.py`

Tests:

- `test_service_backend_boundary_uses_xx_key`: Verify transformed response uses `xx` not `x_grid`
- `test_service_backend_boundary_uses_yy_key`: Verify `yy` not `y_grid`
- `test_service_backend_boundary_uses_uppercase_Z_key`: Verify `Z` not `predictions`
- `test_service_backend_boundary_xx_yy_are_2d`: Verify 2D meshgrid arrays
- `test_service_backend_boundary_Z_shape_matches_grid`: Verify Z matches resolution

---

## Validation Checklist

- [ ] ServiceBackend.get_decision_boundary() returns valid data (not None)
- [ ] CascorServiceAdapter correctly transforms CasCor response to frontend format
- [ ] xx and yy are 2D meshgrid arrays in the response
- [ ] Z is a 2D array with shape (resolution, resolution)
- [ ] API endpoint accepts resolution query parameter
- [ ] Error cases return None gracefully (no 500 errors)
- [ ] Existing DemoBackend behavior unchanged (no regressions)
- [ ] All existing tests continue to pass
- [ ] New tests cover service mode decision boundary
- [ ] Data contract regression tests cover both backend modes
- [ ] Frontend renders correctly with service mode data

---

## Files Modified

### juniper-canopy (primary changes)

| File                                                             | Change                                                     | Root Cause |
|------------------------------------------------------------------|------------------------------------------------------------|------------|
| `src/backend/cascor_service_adapter.py`                          | Add `get_decision_boundary()` with format transformation   | RC-2, RC-3 |
| `src/backend/service_backend.py`                                 | Delegate to adapter instead of returning None              | RC-1       |
| `src/main.py`                                                    | Add resolution query parameter to `/api/decision_boundary` | RC-4       |
| `src/frontend/components/decision_boundary.py`                   | Remove orphaned `dcc.Interval`                             | RC-5       |
| `src/frontend/dashboard_manager.py`                              | Pass resolution to API request                             | RC-4       |
| `src/tests/unit/backend/test_cascor_service_adapter_boundary.py` | New: adapter transformation tests                          | T-1        |
| `src/tests/unit/backend/test_service_backend_boundary.py`        | New: delegation tests                                      | T-2        |
| `src/tests/integration/test_decision_boundary_service_mode.py`   | New: end-to-end service mode tests                         | T-4        |
| `src/tests/regression/test_topology_boundary_data_contract.py`   | Extend: service mode contract tests                        | T-5        |

### No changes required

| Repository            | Reason                                                    |
|-----------------------|-----------------------------------------------------------|
| juniper-cascor        | `/v1/decision-boundary` endpoint already exists and works |
| juniper-cascor-client | `get_decision_boundary()` method already exists           |

---

## Document History

| Date       | Author                        | Change           |
|------------|-------------------------------|------------------|
| 2026-03-16 | Paul Calnon (via Claude Code) | Initial creation |
