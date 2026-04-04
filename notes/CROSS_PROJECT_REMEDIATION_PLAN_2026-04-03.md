# Cross-Project Remediation Plan and Development Roadmap

**Date**: 2026-04-03
**Author**: Claude Code (Principal Engineer Role)
**Reference**: `CROSS_PROJECT_REGRESSION_ANALYSIS_2026-04-03.md`
**Status**: Active

---

## Phase 1: Training Stalling Fix (CRITICAL -- Blocks All Other Work)

### Priority: P0 -- Must fix first

### Step 1.1: Propagate Validation State in grow_network()

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: After line 3677 (the debug log after validate_training())

**Fix**: Add two lines to update loop state variables from validation results:

```python
# After the debug log on line 3677, before the early_stop check:
patience_counter = validate_training_results.patience_counter
best_value_loss = validate_training_results.best_value_loss
```

**Also**: Remove the TODO comment at line 3581 since the bug will be fixed.

#### Approach Analysis

| Aspect | Assessment |
|--------|------------|
| **Strength** | Minimal change, directly addresses root cause |
| **Weakness** | None -- this is the intended behavior per the API contract |
| **Risk** | Low -- the validate_training() method already computes correct values |
| **Guardrail** | Existing test suite validates early stopping behavior |

**Recommendation**: IMPLEMENT -- this is the only correct approach.

### Step 1.2: Add Regression Test for Patience Propagation

**File**: New test in `juniper-cascor/src/tests/unit/` or existing test file

**Test**: Verify that `patience_counter` and `best_value_loss` are updated across epochs in `grow_network()`. Specifically:
- Train with validation data where loss plateaus
- Assert that early stopping triggers after `patience` epochs of no improvement
- Assert that `best_value_loss` tracks the actual minimum validation loss

---

## Phase 2: Epoch/Iteration Semantic Correction (HIGH)

### Priority: P1

### Step 2.1: Rename grow_network() Loop Variable (juniper-cascor)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Changes**:
1. Line 3587: Rename `epoch` to `growth_iteration` in the for loop
2. Lines 3594, 3602-3605, 3614-3615, 3646-3647, 3650-3651, 3677, 3679, 3681-3682: Update all references to the renamed variable
3. Line 3614: Already passes as `iteration=` -- value now correctly named
4. Line 3615: `max_iterations=max_epochs` -- this is semantically correct since `max_epochs` parameter to `grow_network()` actually represents max growth iterations

**Note**: The `grow_network()` parameter `max_epochs` should ideally be renamed to `max_growth_iterations`, but this would require changes to `fit()` and all callers. This is deferred to avoid scope creep.

#### Approach Analysis

| Aspect | Assessment |
|--------|------------|
| **Strength** | Clarifies code intent, prevents future confusion |
| **Weakness** | Parameter name `max_epochs` still misleading at function signature level |
| **Risk** | Low -- purely a rename of a local variable |
| **Guardrail** | All existing tests continue to pass (behavioral equivalence) |

### Step 2.2: Update Canopy Parameter Names and Labels

**File**: `juniper-canopy/src/main.py`, `canopy_constants.py`, frontend components

**Changes**:
1. Rename `DEFAULT_MAX_ITERATIONS` to `DEFAULT_MAX_GROWTH_ITERATIONS` in `canopy_constants.py`
2. Update display labels in `metrics_panel.py` to distinguish:
   - "Growth Iteration: X/Y" (for network growth progress)
   - "Output Epoch: X/Y" (for output layer training)
   - "Candidate Epoch: X/Y" (for candidate training)
3. Update tooltips and parameter descriptions to use correct terminology
4. Update parameter panel labels for clarity

**Note**: The `nn_max_iterations`, `nn_max_total_epochs`, `cn_training_iterations` parameter keys are part of the API contract between canopy and cascor. Renaming them would require coordinated changes across both apps and the client library. The recommended approach is to:
- Keep internal API keys unchanged for backward compatibility
- Update only **display labels** and **tooltips** in the frontend
- Add clarifying comments in the code

#### Approach Analysis

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| A: Rename API keys everywhere | Full semantic clarity | High risk, multi-repo change, breaks API | NOT RECOMMENDED |
| B: Rename display labels only | Low risk, user-facing improvement | Internal code still confusing | RECOMMENDED |
| C: Add a mapping layer | Clean separation | Over-engineering for the scope | DEFERRED |

**Recommendation**: Approach B -- rename display labels and add clarifying comments.

---

## Phase 3: Plot Card Height Increase (MEDIUM)

### Priority: P2

### Step 3.1: Increase Scatter and Boundary Plot Heights

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py`
**Line 222**: Change scatter plot height from `600px` to `800px`

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py`
**Line 150**: Change boundary plot height from `600px` to `800px`

**Also increase max width** from `700px` to `900px` to maintain aspect ratio within the `width=9` container (~900px at desktop).

### Step 3.2: Increase Distribution Plot Height

**File**: `juniper-canopy/src/frontend/components/dataset_plotter.py`
**Line 228**: Change from `25vh` / max `350px` to `30vh` / max `450px`
**Line 535**: Change figure layout height from `300px` to `400px`

#### Approach Analysis

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| A: Fixed pixel increase | Simple, predictable | Not responsive | RECOMMENDED |
| B: Viewport-relative (vh) | Responsive | Behavior varies by screen | DEFERRED |
| C: Container-percentage | Fills available space | May distort on wide screens | NOT RECOMMENDED |

**Recommendation**: Approach A -- increase fixed pixel values. The existing Plotly `scaleanchor` setting preserves aspect ratios automatically.

---

## Phase 4: Parameter Update Flakiness Fix (CRITICAL)

### Priority: P1

### Step 4.1: Fix Async/Sync Boundary

**File**: `juniper-canopy/src/main.py`, line 2042

**Change**: Wrap synchronous `backend.apply_params()` in `asyncio.to_thread()`:

```python
# Before:
backend.apply_params(**backend_updates)

# After:
result = await asyncio.to_thread(backend.apply_params, **backend_updates)
```

This ensures the backend call completes before broadcasting and returning.

### Step 4.2: Expand TrainingState Synchronization

**File**: `juniper-canopy/src/main.py`, lines 2038-2046

**Change**: Sync all applied parameters to TrainingState, not just 3:

```python
# Expand the ts_updates mapping to include all parameter keys
param_to_state_map = {
    "nn_learning_rate": "learning_rate",
    "nn_max_hidden_units": "max_hidden_units",
    "nn_max_total_epochs": "max_epochs",
    "nn_max_iterations": "max_iterations",
    "cn_pool_size": "candidate_pool_size",
    "cn_correlation_threshold": "correlation_threshold",
    "cn_training_iterations": "candidate_training_epochs",
    "nn_patience": "patience",
    # ... additional mappings
}
```

### Step 4.3: Include Full Parameter State in WebSocket Broadcast

**File**: `juniper-canopy/src/main.py`, line 2046

**Change**: Include applied parameters in broadcast:

```python
broadcast_data = {
    **training_state.get_state(),
    "applied_params": backend_updates,
}
await websocket_manager.broadcast({"type": "params_updated", "data": broadcast_data})
```

### Step 4.4: Fix CasCor Client Key Path Mismatch

**File**: `juniper-cascor-client/juniper_cascor_client/client.py`, line 76

**Change**: Fix key path from `data` to `details`:

```python
# Before:
return result.get("data", {}).get("network_loaded", False)

# After:
return result.get("details", {}).get("network_loaded", False)
```

### Step 4.5: Fix Connection Gate in CasCor Service Adapter

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

**Change**: Use `is_alive()` instead of `is_ready()` for initial connection. Check `is_ready()` only when operations require a loaded network.

### Step 4.6: Add Error Propagation for Failed Parameter Updates

**File**: `juniper-canopy/src/main.py`, around line 2042

**Change**: Check the return value of `apply_params()` and return appropriate error:

```python
result = await asyncio.to_thread(backend.apply_params, **backend_updates)
if isinstance(result, dict) and not result.get("ok", True):
    return JSONResponse(
        status_code=502,
        content={"status": "error", "message": result.get("error", "Failed to apply params to backend")}
    )
```

#### Approach Analysis

| Step | Risk | Impact | Recommendation |
|------|------|--------|----------------|
| 4.1 async fix | Low | High -- fixes timing | IMPLEMENT |
| 4.2 state sync | Low | Medium -- fixes display | IMPLEMENT |
| 4.3 broadcast | Low | Medium -- real-time updates | IMPLEMENT |
| 4.4 key path | Low | Critical -- fixes service mode | IMPLEMENT |
| 4.5 connection gate | Medium | High -- fixes service connection | IMPLEMENT |
| 4.6 error propagation | Low | Medium -- user feedback | IMPLEMENT |

---

## Phase 5: Testing and Validation

### Step 5.1: Run Existing Test Suites

```bash
# juniper-cascor
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
pytest src/tests/ -v --timeout=60

# juniper-canopy
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
pytest src/tests/ -v --timeout=60

# juniper-cascor-client
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
pytest tests/ -v --timeout=30
```

### Step 5.2: Add New Regression Tests

1. **Patience propagation test** (juniper-cascor): Verify patience_counter increments across growth iterations
2. **Parameter roundtrip test** (juniper-canopy): Verify all params survive submit -> apply -> broadcast -> display
3. **Key path test** (juniper-cascor-client): Verify `is_ready()` parses `details.network_loaded`

---

## Phase 6: Deployment

### Step 6.1: Create Working Branches

Per worktree conventions, create feature branches in each affected repo:
- `juniper-cascor`: `fix/training-convergence-patience`
- `juniper-canopy`: `fix/regression-display-params`
- `juniper-cascor-client`: `fix/readiness-key-path`

### Step 6.2: Push and Create Pull Requests

Push branches and create PRs targeting `main` in each repo.

---

## Priority Matrix

| Phase | Priority | Blocking? | Estimated Complexity |
|-------|----------|-----------|---------------------|
| 1: Training stalling | P0 | Yes -- blocks all | Low (2 lines + test) |
| 2: Epoch/iteration | P1 | No | Medium (multi-file rename) |
| 3: Plot heights | P2 | No | Low (style changes) |
| 4: Param updates | P1 | No | Medium (6 sub-steps) |
| 5: Testing | P0 | Yes -- validates all | Medium |
| 6: Deployment | P0 | Yes -- delivers fixes | Low |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Patience fix changes training behavior | Medium | High | Run full test suite, compare training curves |
| Renaming breaks API contract | Low | High | Only rename display labels, not API keys |
| Height changes break responsive layout | Low | Medium | Test at multiple viewport sizes |
| Async fix introduces new race condition | Low | Medium | Use `asyncio.to_thread()` for proper blocking |
| Key path fix breaks other clients | Low | Low | Only juniper-canopy uses this client |
