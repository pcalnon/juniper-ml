# Consolidated Regression Remediation Plan

**Date**: 2026-04-03
**Version**: 1.0.0
**Status**: Active
**Author**: Claude Code (Consolidated Analysis)

**Supersedes**:

- `REGRESSION_REMEDIATION_PLAN_01_2026-04-02.md`
- `REGRESSION_REMEDIATION_PLAN_02_2026-04-02.md`
- `REGRESSION_REMEDIATION_PLAN_03_2026-04-02.md`
- `REGRESSION_REMEDIATION_PLAN_04_2026-04-02.md`
- `REGRESSION_REMEDIATION_PLAN_05_2026-04-02.md`
- `REGRESSION_REMEDIATION_PLAN_06_2026-04-02.md`

---

## Status Overview

### Already Completed

The following fixes have been applied via PR #61, PR #74, and prior commits:

| Fix                                    | Resolution                                             | Source |
|----------------------------------------|--------------------------------------------------------|--------|
| Walrus operator precedence (line 1708) | Parenthesized assignment + try/except guard            | PR #61 |
| SharedMemory deferred unlink           | `close()` deferred from worker to parent               | PR #61 |
| Tensor clone fix                       | `.clone()` on tensors before SharedMemory write        | PR #61 |
| Correlation clamping                   | `torch.clamp(-1, 1)` on correlation values             | PR #61 |
| UnboundLocalError guard                | `candidate_inputs = None` at line 2716                 | PR #61 |
| Demo deadlock fix                      | Fixed demo mode training deadlock                      | PR #61 |
| Tab ordering and labels                | Reordered tabs, renamed "HDF5 Snapshots" → "Snapshots" | PR #74 |
| Candidate loss graph dark mode         | `plotly_dark` template + dark background colors        | PR #74 |
| Parameters tab dark mode               | CSS variable-based table styling                       | PR #74 |
| Tutorial tab dark mode                 | CSS variable-based table styling                       | PR #74 |

### Remaining Work

17 items across 6 phases, organized by priority and dependency order.

---

## Phase 1: Remaining Critical Fixes (P0)

These are cascor-internal issues that affect training reliability. Phase 1 must complete before Phases 2–3 can be validated.

### 1.1 SharedMemory Cleanup Lifecycle

**Problem**: `_execute_parallel_training()` unlinks SharedMemory blocks in its `finally` block. When parallel training fails and `_execute_candidate_training()` falls back to `_execute_sequential_training()`, the sequential path cannot access the already-unlinked blocks.

**Selected Approach**: Move cleanup from `_execute_parallel_training()` to `_execute_candidate_training()` (Plan 03, Approach A).

**Rationale**: Plan 01 proposed removing `_fallback_tensors` and regenerating legacy tasks — workable but requires restructuring the sequential fallback path. Plan 04 proposed defensive try/except in `_build_candidate_inputs()` with fallback tensors — this masks the root cause and defeats OPT-5 by duplicating tensor data. Plan 03's approach directly fixes the lifecycle bug with minimal code change: the cleanup moves to the method that owns both execution paths.

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Change 1** — Remove cleanup from `_execute_parallel_training()` finally block (lines 2129–2135):

```python
# BEFORE:
finally:
    for shm_block in list(self._active_shm_blocks):
        try:
            shm_block.close_and_unlink()
            self._active_shm_blocks.remove(shm_block)
        except Exception as shm_e:
            self.logger.warning(f"...: OPT-5 SharedMemory cleanup error: {shm_e}")
    self.logger.trace("...: Parallel training round complete")

# AFTER:
finally:
    # OPT-5: Cleanup deferred to _execute_candidate_training() so sequential
    # fallback can still access SharedMemory blocks if parallel fails.
    self.logger.trace("...: Parallel training round complete")
```

**Change 2** — Add cleanup to `_execute_candidate_training()` via try/finally wrapping the method body (lines 1906–1989):

```python
def _execute_candidate_training(self, tasks: list, process_count: int) -> list:
    self.logger.info(f"...: Training {len(tasks)} candidates with {process_count} processes")
    results = []
    try:
        # ... existing parallel/sequential logic unchanged ...
    finally:
        for shm_block in list(self._active_shm_blocks):
            try:
                shm_block.close_and_unlink()
                self._active_shm_blocks.remove(shm_block)
            except Exception as shm_e:
                self.logger.warning(f"...: OPT-5 SharedMemory cleanup error: {shm_e}")

    if not results:
        results = self._get_dummy_results(len(tasks))
    return results
```

**Risk**: Low. Cleanup moves to a broader scope but the `_active_shm_blocks` tracking list ensures blocks are always eventually cleaned. SharedMemory blocks live marginally longer in the success case (negligible impact).

**Verification**:

1. `cd juniper-cascor/src/tests && bash scripts/run_tests.bash -u`
2. Start cascor, trigger training, force parallel failure (e.g., kill a worker) — verify sequential fallback succeeds
3. Monitor logs: no `FileNotFoundError` on SharedMemory reconstruction

### 1.2 WebSocket Coroutine Leak

**Problem**: `broadcast_from_thread()` creates a coroutine via `self.broadcast(message)` and passes it to `asyncio.run_coroutine_threadsafe()`. If the event loop is closed between the `is_closed()` check and the `run_coroutine_threadsafe()` call, the coroutine is never awaited or closed — it leaks.

**Selected Approach**: Catch all exceptions and close the coroutine on failure (Plan 02, Approach A).

**Rationale**: Plan 02 Approach B (explicit exception list) is more complex and risks missing new exception types. The broad except with a debug log is appropriate here because this is a best-effort broadcast — failure is expected during shutdown.

**File**: `juniper-cascor/src/api/websocket/manager.py` (lines 89–101)

```python
def broadcast_from_thread(self, message: dict) -> None:
    if self._event_loop is None or self._event_loop.is_closed():
        return
    coro = self.broadcast(message)
    try:
        asyncio.run_coroutine_threadsafe(coro, self._event_loop)
    except Exception:
        coro.close()
        logger.debug("Cannot broadcast: event loop unavailable or closed")
```

**Risk**: Low. Only affects the WebSocket broadcast path. Failure is already silent — this adds explicit cleanup.

**Verification**: Run cascor training, stop the service mid-training — verify no `RuntimeWarning: coroutine was never awaited` in logs.

### 1.3 Exception Propagation in Lifecycle Manager

**Problem**: `_run_training()` catches exceptions and logs them but does not update the training state or notify WebSocket clients. The UI shows "Training" indefinitely after a backend failure.

**Selected Approach**: Add state update and best-effort WebSocket notification (Plan 02, §1.3).

**File**: `juniper-cascor/src/api/lifecycle/manager.py` (lines 533–538)

```python
except Exception as e:
    self.logger.error(f"Training failed: {e}", exc_info=True)
    self._training_state = "failed"
    self._training_error = str(e)
    try:
        self._ws_manager.broadcast_from_thread({
            "type": "training_failed",
            "data": {"error": str(e), "phase": self._current_phase}
        })
    except Exception:
        pass
```

**Risk**: Low. Adds state update (new field `_training_error`) and best-effort notification. The inner try/except ensures broadcast failure doesn't mask the original error.

**Verification**: Inject a training failure (e.g., corrupt dataset) — verify state transitions to `"failed"` and WebSocket clients receive the event.

### 1.4 Drain Thread Queue Timing Race

**Problem**: The drain thread starts polling `network._persistent_progress_queue` immediately, but the queue may not be initialized yet. This causes an `AttributeError` or silent failure during startup.

**Selected Approach**: Add an initialization guard that waits for the queue to appear (Plan 02, §1.4).

**File**: `juniper-cascor/src/api/lifecycle/manager.py` (lines 383–401)

```python
def _drain_progress_queue(self, stop_event, network):
    queue = None
    while not stop_event.is_set():
        if queue is None:
            queue = getattr(network, '_persistent_progress_queue', None)
            if queue is None:
                stop_event.wait(timeout=0.5)
                continue
        try:
            item = queue.get_nowait()
            self._process_progress_item(item)
        except Empty:
            stop_event.wait(timeout=0.1)
```

**Risk**: Low. Adds a graceful startup delay with no behavioral change once the queue is initialized.

**Verification**: Start cascor with a cold network — verify no `AttributeError` in the drain thread during initialization.

---

## Phase 2: Canopy-CasCor Connection Fix (P0)

Required for canopy to display correct service status. Can proceed in parallel with Phase 1 since it's in different repos.

### 2.1 Client Response Key Mismatch

**Problem**: `is_ready()` in juniper-cascor-client reads `result.get("data", {}).get("network_loaded")`, but the cascor `/health/ready` endpoint returns `{"details": {"network_loaded": ...}}`.

**Selected Approach**: Fix the client to read `"details"` (Plan 02, §2.1), with a defensive fallback for both keys (Plan 01, §2.1).

**Rationale**: Plan 01's "handle both formats" approach is more resilient, but the primary fix should match the actual server contract. Combining both: fix the primary key and add a fallback.

**File**: `juniper-cascor-client/juniper_cascor_client/client.py` (line 76)

```python
# Primary key matches server contract; fallback handles legacy format
data = result.get("details") or result.get("data") or {}
return data.get("network_loaded", False)
```

**Risk**: None. Pure data contract alignment.

### 2.2 Connection Gate: `is_alive()` vs `is_ready()`

**Problem**: Canopy's `connect()` gates on `is_ready()`, which requires a network to be loaded. During startup (before training), `is_ready()` returns `False` even though the service is running.

**Selected Approach**: Gate on `is_alive()` for initial connection (Plans 01 & 02 agree).

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py` (lines 122–128)

Replace the `is_ready()` call with `is_alive()` in the connection establishment path. `is_ready()` should only be used when checking if training can start.

**Risk**: Low. `is_alive()` is less restrictive, which is correct for connection establishment.

**Verification**:

1. Start cascor without training → verify canopy connects
2. Start training → verify canopy status transitions correctly (Idle → Training → Running)

---

## Phase 3: Canopy Data Flow Fixes (P1)

These fix incorrect or missing data display in the canopy dashboard.

### 3.1 Network Information Shows Zeros

**Problem**: `input_size` and `output_size` show as 0 because cascor's `/api/status` response doesn't include network dimensions.

**Selected Approach**: Add dimensions to cascor's `get_status()` (Plan 03, §H-3).

**Rationale**: Plan 04 suggested fetching from `/api/topology` instead — this adds an extra HTTP call. Plan 03's approach adds the data at the source, which is cleaner.

**File (cascor)**: `juniper-cascor/src/api/lifecycle/manager.py` — `get_status()` (line 587)

```python
if self.network is not None:
    training_state.setdefault("input_size", self.network.input_size)
    training_state.setdefault("output_size", self.network.output_size)
```

**File (canopy)**: `juniper-canopy/src/backend/service_backend.py` (lines 134–135) — no change needed if cascor provides the data.

**Risk**: Low. `setdefault` preserves any explicitly-set values.

### 3.2 Convergence Threshold Investigation

**Problem**: The convergence threshold sidebar input may not reflect the backend's actual value.

**Selected Approach**: Audit the parameter mapping in `get_canopy_params()` (Plan 03, §H-4).

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py` — `get_canopy_params()`

Ensure `nn_growth_convergence_threshold` maps to `getattr(network, "convergence_threshold", None)`. Verify all 22 `nn_*`/`cn_*` parameter keys are mapped.

**Risk**: Low. Data plumbing audit.

### 3.3 Parameter Sidebar Sync with Backend

**Problem**: Parameters show hardcoded defaults instead of live values from cascor.

**Selected Approach**: Audit and complete the parameter mapping (Plan 03, §H-4).

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py` — `get_canopy_params()`

Verify all parameter keys map correctly. See Plan 03 §H-4 for the full required mapping table (22 keys including `nn_learning_rate`, `cn_pool_size`, `cn_candidate_epochs`, etc.).

**Risk**: Low. Missing mappings cause display-only issues.

### 3.4 Learning Rate Mismatch

**Problem**: Learning rate may display incorrectly if the mapping uses the wrong network attribute.

**Action**: Verify during §3.3 audit that `nn_learning_rate` maps to `network.learning_rate` (not `network.output_learning_rate` or similar).

### 3.5 Cassandra API URL Fix

**Problem**: `CassandraPanel._api_url()` uses Flask request context which is unavailable during Dash callbacks.

**Selected Approach**: Use settings-based URL construction (Plan 03, §M-6).

**Rationale**: Plan 04 proposed extracting to `BaseComponent` — good DRY improvement but larger scope. Plan 02's settings-based approach is simpler and immediately correct.

**File**: `juniper-canopy/src/frontend/components/cassandra_panel.py` (lines 98–113)

```python
def _api_url(self, path: str) -> str:
    base_url = self.config.get("api_base_url", "http://127.0.0.1:8050")
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
```

**Risk**: Low. URL construction change. Verify all Cassandra panel callbacks work after the change.

---

## Phase 4: UI Enhancements (P2)

Visual and interaction improvements. All plans agree on these items; differences are minor.

### 4.1 Decision Boundary Aspect Ratio + Replay

**Aspect Ratio Fix** — All plans converge on the same approach:

**File**: `juniper-canopy/src/frontend/components/decision_boundary.py` (line 150)

```python
fig.update_layout(
    yaxis=dict(scaleanchor="x", scaleratio=1),
)
```

Container style:

```python
style={"width": "100%", "aspectRatio": "1 / 1", "maxHeight": "800px"}
```

**Replay Feature** — All plans agree this is a new feature (~150–200 lines). Design:

1. Store decision boundary data at each hidden node addition in a `dcc.Store`
2. Add `dcc.Slider` with range `[0, current_hidden_units]`
3. Add play/pause controls
4. Callback updates plot based on slider position

**Recommendation**: Ship aspect ratio fix now; defer replay to a separate task/PR.

**Risk**: Low (aspect ratio), Medium (replay — new feature requiring backend changes).

### 4.2 Dataset View: Dropdown, Dynamic Fields, Generate Workflow

Three related enhancements (Plans 01–04 all agree on scope):

1. **Dropdown population**: Callback fetches generators from juniper-data via `GET /v1/generators`
2. **Dynamic sidebar**: Replace hardcoded "Spiral Dataset" heading with "Current Dataset"; show/hide fields based on selected dataset type
3. **Generate workflow**: Stop training → generate dataset → display scatter → check compatibility → prompt user if incompatible

**Files**: `dataset_plotter.py`, `dashboard_manager.py`

**Recommendation**: Defer to a separate task. This is feature work with Medium–High complexity spanning frontend and backend.

**Risk**: Medium (dropdown/dynamic), High (generate workflow — multi-step state management).

### 4.3 Snapshots Refresh Button Position

**File**: `juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py`

Move refresh button and status message from the main title area to the "Available Snapshots" section heading:

```python
dbc.CardHeader(
    dbc.Row([
        dbc.Col(html.H5("Available Snapshots"), width="auto"),
        dbc.Col([refresh_button, status_message], width="auto"),
    ], justify="between", align="center"),
),
```

**Risk**: Low. Layout change only.

### 4.4 Hardcoded Color Replacement

**Files**: `hdf5_snapshots_panel.py`, `cassandra_panel.py`

Replace hardcoded hex colors with CSS variables:

- `"#2c3e50"` → `"var(--header-color)"`
- `"#6c757d"` → `"var(--text-muted)"`
- `"#e9ecef"` → `"var(--bg-secondary)"`

**Risk**: Low. CSS-only changes.

---

## Phase 5: Code Quality (P3)

Non-functional improvements. Low priority, zero user-facing impact.

### 5.1 Dead Code Removal

| Item                              | File                     | Line | Action                       |
|-----------------------------------|--------------------------|------|------------------------------|
| `global shared_object_dict`       | `cascade_correlation.py` | 2923 | Remove undeclared global     |
| `import datetime as pd`           | `cascade_correlation.py` | 39   | Remove misleading alias      |
| Duplicate `snapshot_counter` init | `cascade_correlation.py` | 779  | Remove second initialization |

**Risk**: None. Pure dead code removal.

### 5.2 ActivationWithDerivative Class Extraction

**Selected Approach**: Extract to a shared utils module (Plan 02, Approach A).

**Rationale**: Plan 02 Approach B (import from `cascade_correlation.py`) risks circular imports. A shared `src/utils/activation.py` module with the canonical class and `ACTIVATION_MAP` is cleaner.

**File**: Create `juniper-cascor/src/utils/activation.py`, update imports in `cascade_correlation.py` and `candidate_unit.py`.

**Risk**: Medium. Touches two files and creates a new module. Requires test updates.

### 5.3 Weight Magnitude Threshold

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py` (line 2155)

**Selected Approach**: Increase `_RESULT_MAX_WEIGHT_MAGNITUDE` from `100.0` to `1000.0` and add a warning log for values between 100.0–1000.0 (Plan 01, §1.2).

**Rationale**: With learning rate 0.1 and 400 epochs, legitimate weights can exceed 100.0. A threshold of 1000.0 remains conservative against corruption while not rejecting valid training results. NaN/Inf checks (lines 2188–2190) remain as the primary corruption guard.

**Risk**: Low. Existing NaN/Inf checks provide the safety net.

---

## Phase 6: Demo Training Algorithm Fix (P1)

### 5 Algorithmic Mismatches in `canopy/src/demo_mode.py`

These affect only demo mode (not production training), but cause incorrect visual behavior when canopy runs without a live cascor backend.

| # | Mismatch                                                                       | Fix                                                                  |
|---|--------------------------------------------------------------------------------|----------------------------------------------------------------------|
| 1 | Output weight update uses full gradient descent instead of delta rule          | Align with cascor's `_train_output_weights()` delta rule             |
| 2 | Candidate correlation computed against raw targets instead of residual errors  | Compute correlation against `(y - y_predicted)`                      |
| 3 | Candidate installation doesn't freeze previous hidden unit weights             | Add `requires_grad_(False)` to existing hidden units on installation |
| 4 | Missing quickprop optimizer for candidate training                             | Implement quickprop or switch to cascor's exact optimizer            |
| 5 | Convergence check uses absolute error threshold instead of relative stagnation | Match cascor's sliding-window stagnation detection                   |

**Risk**: Medium per-fix. Demo mode is isolated from production but is the primary onboarding experience.

**Verification**: Run `./demo` in canopy, verify training converges on two-spiral within expected epoch count and decision boundary updates correctly.

---

## Risk Assessment

| Phase   | Fix                    | Risk        | Blast Radius           | Reversibility                      |
|---------|------------------------|-------------|------------------------|------------------------------------|
| 1.1     | SharedMemory lifecycle | Low         | Training pipeline      | Moderate — revert cleanup location |
| 1.2     | Coroutine leak         | Low         | WebSocket broadcast    | Easy — revert to original          |
| 1.3     | Exception propagation  | Low         | Lifecycle state        | Easy — remove state update         |
| 1.4     | Drain thread guard     | Low         | Progress monitoring    | Easy — remove guard                |
| 2.1     | Client key mismatch    | None        | Client `is_ready()`    | Trivial — single line              |
| 2.2     | Connection gate        | Low         | Service adapter        | Easy — swap `is_alive`/`is_ready`  |
| 3.1     | Network info zeros     | Low         | Status endpoint        | Easy — remove `setdefault`         |
| 3.2–3.4 | Parameter mapping      | Low         | Display only           | Easy — revert mapping              |
| 3.5     | Cassandra API URL      | Low         | Cassandra panel        | Easy — revert URL method           |
| 4.1     | Aspect ratio           | Low         | Visual only            | Trivial — revert style             |
| 4.1     | Boundary replay        | Medium      | New feature            | N/A — new code                     |
| 4.2     | Dataset enhancements   | Medium–High | Frontend + backend     | Moderate — multiple files          |
| 4.3     | Refresh button         | Low         | Layout only            | Trivial — revert layout            |
| 4.4     | CSS variables          | Low         | Dark mode styling      | Trivial — revert colors            |
| 5.1     | Dead code              | None        | No behavior change     | Trivial                            |
| 5.2     | Class extraction       | Medium      | Two files + new module | Moderate — revert imports          |
| 5.3     | Weight threshold       | Low         | Result validation      | Trivial — revert constant          |
| 6       | Demo algorithm fixes   | Medium      | Demo mode only         | Easy — isolated module             |

---

## Verification Plan

### Phase 1 Verification

```bash
# Unit tests
cd juniper-cascor/src/tests && bash scripts/run_tests.bash -u

# Integration tests
cd juniper-cascor/src/tests && bash scripts/run_tests.bash -i

# Manual: start cascor, run training for 3+ epochs, verify:
# - No FileNotFoundError in logs
# - No coroutine warnings
# - State transitions to "failed" on injected error
# - Drain thread starts cleanly on cold boot
```

### Phase 2 Verification

```bash
# Client unit tests
cd juniper-cascor-client && pytest tests/ -v

# Manual: start cascor without training
# - Verify canopy connects (is_alive gate)
# - Start training, verify status transitions
```

### Phase 3 Verification

```bash
# Canopy unit tests
cd juniper-canopy/src && pytest -m "unit and not slow" -v

# Manual: verify network info displays non-zero values
# Manual: verify parameter sidebar matches cascor config
# Manual: verify Cassandra panel loads without URL errors
```

### Phase 4 Verification

```bash
# Visual verification in both light and dark modes:
# - Decision boundary maintains 1:1 aspect ratio on resize
# - Snapshots refresh button in "Available Snapshots" header
# - No hardcoded colors visible in dark mode
```

### Phase 5 Verification

```bash
# After dead code removal:
cd juniper-cascor/src/tests && bash scripts/run_tests.bash -v -c

# After class extraction:
# Verify no circular imports: python -c "from utils.activation import ActivationWithDerivative"
```

### Phase 6 Verification

```bash
# Start canopy in demo mode
cd juniper-canopy && ./demo

# Verify: training converges on two-spiral
# Verify: decision boundary updates at each hidden node addition
# Verify: metrics graphs show expected loss curves
```

### End-to-End Integration

```bash
# Full stack verification (all services running):
# 1. Start juniper-data
# 2. Start juniper-cascor
# 3. Start juniper-canopy
# 4. Create network → start training → verify 5+ epochs complete
# 5. Verify all tabs render correctly in light and dark mode
# 6. Verify decision boundary and dataset view aspect ratios
# 7. Verify snapshot save/load cycle
```

---

## Already Completed Fixes Reference

| ID              | Description                                        | Resolution                                          | PR/Commit |
|-----------------|----------------------------------------------------|-----------------------------------------------------|-----------|
| CRIT-WALRUS     | Walrus operator precedence bug at line 1708        | Parenthesized `(snapshot_path := ...)` + try/except | PR #61    |
| CRIT-SHM-UNLINK | SharedMemory premature unlink in workers           | Deferred `close()` from worker to parent process    | PR #61    |
| CRIT-TENSOR     | Tensor mutation during SharedMemory write          | `.clone()` before write                             | PR #61    |
| CRIT-CORR       | Correlation values outside [-1, 1]                 | `torch.clamp(-1, 1)`                                | PR #61    |
| CRIT-UNBOUND    | `UnboundLocalError` in exception handler           | `candidate_inputs = None` guard at line 2716        | PR #61    |
| CRIT-DEMO-DL    | Demo mode training deadlock                        | Fixed synchronization in demo_mode.py               | PR #61    |
| UI-TABS         | Tab ordering and label normalization               | Reordered tabs, renamed labels                      | PR #74    |
| UI-CAND-DM      | Candidate loss graph white background in dark mode | `plotly_dark` template + dark bgcolor               | PR #74    |
| UI-PARAMS-DM    | Parameters tab white table in dark mode            | CSS variable-based styling                          | PR #74    |
| UI-TUTORIAL-DM  | Tutorial tab white table in dark mode              | CSS variable-based styling                          | PR #74    |

---

## Dependency Graph

```bash
Phase 1 (CasCor Critical) ──┬──> Phase 3 (Data Flow)  ──┬──> Phase 4 (UI Enhancements)
                            │                           │
Phase 2 (Connection Fix) ───┘                           └──> Phase 6 (Demo Algorithm)
                                                         │
                                                         └──> Phase 5 (Code Quality)
```

- Phases 1 and 2 can proceed in parallel (different repos)
- Phase 3 depends on Phases 1 + 2 (needs working training + connection)
- Phases 4, 5, 6 can proceed after Phase 3 (or independently for purely visual items)
