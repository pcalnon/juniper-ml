# Canopy-Cascor Interface: Development Roadmap

**Version**: 1.0.0
**Date**: 2026-04-08
**Author**: Claude Code (Opus 4.6)
**Owner**: Paul Calnon
**Status**: ACTIVE
**Companion Documents**:
- Analysis: `CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md`
- Plan: `CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md`

---

## 1. Executive Summary

This roadmap documents all required work to bring the Canopy-Cascor interface to production readiness. Work is organized into 4 prioritized phases with explicit dependencies, effort estimates, and success criteria.

**Total estimated effort**: 17-26 days across both repositories (reduced from 24-35 due to CR-006/CR-007/CR-008 resolution)
**Critical path**: Phase 3 (metrics granularity) is now the primary remaining work

**Key Validation Finding (2026-04-08)**: All three Tier 0 critical issues (CR-006, CR-007, CR-008) have been RESOLVED since the prior analyses. The interface is in significantly better health than previously documented.

---

## 2. Issue Priority Matrix

| ID | Severity | Impact | Effort | Risk | Phase |
|----|----------|--------|--------|------|-------|
| CR-006 | S1 | Training limits — **LARGELY RESOLVED**: verify fit() deconflation, default alignment | S (0.5-1d) | Low | 1 |
| CR-007 | S1 | State machine locks up after failure | M (1d) | Low | 1 |
| CR-008 | S2 | Missing documented WS functionality | S (0.5d) | Low | 1 |
| CR-023 | S2 | Unvalidated kwargs injection risk | S (0.5d) | Low | 2 |
| CR-024 | S2 | Body limit bypass via chunked encoding | S (0.5d) | Low | 2 |
| CR-025 | S2 | WebSocket race condition (latent) | S (0.5d) | Low | 2 |
| CR-026 | S1 | Worker impersonation via client ID | M (1d) | Medium | 2 |
| AppG-C | Arch | No metrics during output training | S-M (1-2d) | Low | 3 |
| AppG-A | Arch | No metrics during candidate training | M-L (3-5d) | Medium | 3 |
| P5-RC-18 | Systemic | No typed backend contract | L (3-5d) | Medium | 4 |
| P5-RC-14 | Low | Relay broadcasts raw metrics | S (<1d) | Low | 4 |
| P5-RC-05 | Low | Dashboard ignores WebSocket data | M (2-3d) | Medium | 4 |
| KL-1 | Known | Dataset scatter empty in service mode | L (3-5d) | Medium | 4 |

---

## 3. Phase 1: Critical Interface Fixes

**Priority**: P0 — Must be completed before release
**Estimated Duration**: 5-6 days
**Dependencies**: None

### 3.1 CR-006: Verify `max_iterations` End-to-End Implementation

**Severity**: S1 (largely resolved) | **Effort**: Small (0.5-1 day) | **Repos**: juniper-cascor, juniper-canopy

#### Status Update (2026-04-08)

**The core CR-006 issue has been SUBSTANTIALLY ADDRESSED since the prior analysis.** Verification against the current codebase shows:

- `max_iterations` now exists in `CascadeCorrelationConfig` (line 150)
- `self.max_iterations` exists on the network class (line 674)
- `fit()` now accepts `max_iterations` as a separate parameter (line 1387) and passes it independently to `grow_network()` (line 1482)
- `NetworkCreateRequest` has `max_iterations: int = Field(1000, ge=1)` (line 22)
- `TrainingParamUpdateRequest` has `max_iterations: Optional[int]` (line 58)
- `_STATE_FIELDS` includes `"max_iterations"` (line 29)
- `updatable_keys` includes `"max_iterations"` (line 712)
- `_CANOPY_TO_CASCOR_PARAM_MAP` maps `"nn_max_iterations": "max_iterations"` (line 430)

#### Remaining Verification Tasks

1. **Verify `fit()` deconflation**: Confirm that `max_epochs` goes only to `train_output_layer()` and `max_iterations` goes only to `grow_network()`
2. **Verify default alignment**: Check that defaults are consistent across the constant chain
3. **Integration test**: Verify canopy UI edit → cascor param update round-trip works for both limits
4. **Regression check**: Verify failed growth cycles still increment iteration counter

#### Recommended Fix: Option A — Full End-to-End Implementation

**Cascor Changes** (PR 1):

| Step | File | Change |
|------|------|--------|
| 1 | `cascor_constants/constants_model.py` | Add `_PROJECT_MODEL_MAX_ITERATIONS = 1000` |
| 2 | `cascor_constants/constants.py` | Add alias chain to `_CASCADE_CORRELATION_NETWORK_MAX_ITERATIONS` |
| 3 | `cascade_correlation_config.py` | Add `max_iterations: int` field (default from constant) |
| 4 | `cascade_correlation.py` | Add `self.max_iterations` attribute; use in `grow_network()` default |
| 5 | `cascade_correlation.py` | **Deconflate `fit()`**: separate `max_epochs` → `train_output_layer()`, `max_iterations` → `grow_network()` |
| 6 | `api/models/network.py` | Add `max_iterations: int = Field(1000, ge=1)` to `NetworkCreateRequest` |
| 7 | `api/models/training.py` | Add `max_iterations: Optional[int]` to `TrainingParamUpdateRequest` |
| 8 | `api/lifecycle/monitor.py` | Add `"max_iterations"` to `_STATE_FIELDS` |
| 9 | `api/lifecycle/manager.py` | Fix `create_network()` to pass both keys; add to `updatable_keys` |
| 10 | `api/lifecycle/manager.py` | Align `epochs_max` default to 1,000,000 (matching canopy) |

**Canopy Changes** (PR 2, after cascor PR merges):

| Step | File | Change |
|------|------|--------|
| 11 | `backend/cascor_service_adapter.py` | Add `"nn_max_iterations": "max_iterations"` to `_CANOPY_TO_CASCOR_PARAM_MAP` |
| 12 | `main.py` | Update `apply_params()` to forward `max_iterations` to cascor |
| 13 | `backend/training_monitor.py` | Add `__max_iterations` field to `TrainingState` |

**Tests**:
- Unit test: both values flow through `create_network()` → `TrainingState` → `get_state()`
- Unit test: `grow_network()` respects `max_iterations` independently from `max_epochs`
- Integration test: canopy UI edit → cascor param update round-trip
- Regression: failed growth cycles still increment iteration counter

**Strengths**: Correct semantics; independently controllable limits; aligned defaults
**Weaknesses**: Touches both repos; coordinated PRs needed; API version bump
**Risks**: Changing `epochs_max` default from 200/10,000 to 1,000,000 changes behavior for users relying on the old default
**Guardrails**: Semver minor bump for both repos (new API fields, default changes)

#### Alternative: Option B — Cascor-Only Fix

Fix cascor side only (steps 1-10). Leave canopy `nn_max_iterations` as dead-end until follow-up.

**Strengths**: Single-repo change; smaller blast radius
**Weaknesses**: Canopy users still can't control `max_iterations`; interim confusion

**Recommendation**: Option A. Execute as two coordinated PRs (cascor first, then canopy).

---

### 3.2 CR-007: Auto-Reset State Machine on Start

**Severity**: S1 | **Effort**: Medium (1 day) | **Repo**: juniper-cascor

#### Problem

After training fails or completes, `start_training()` bypasses the guard (only checks `is_started()`), but `handle_command(Command.START)` silently fails in terminal states. State machine becomes permanently desynchronized.

#### Recommended Fix

```python
# In TrainingLifecycleManager.start_training():
if self.state_machine.status in (TrainingStatus.FAILED, TrainingStatus.COMPLETED):
    logger.info("Auto-resetting from %s state before starting new training", self.state_machine.status)
    self.state_machine.handle_command(Command.RESET)
```

Also remove the duplicate `except` block in `_run_training` that redundantly attempts STOP from FAILED state.

**Tests**:
- Test start after FAILED transitions correctly
- Test start after COMPLETED transitions correctly
- Test auto-reset is logged
- Test duplicate error handler removal doesn't break error reporting

---

### 3.3 CR-008: Implement WebSocket `set_params`

**Severity**: S2 | **Effort**: Small (0.5 day) | **Repo**: juniper-cascor

#### Problem

Control stream docstring lists `set_params` as valid command, but `_VALID_COMMANDS` omits it.

#### Recommended Fix

```python
# In api/websocket/control_stream.py:
_VALID_COMMANDS = {"start", "stop", "pause", "resume", "reset", "set_params"}

# In _execute_command():
elif command == "set_params":
    params = message.get("params", {})
    result = await self.lifecycle.update_params(params)
    await websocket.send_json({"type": "params_updated", "data": result})
```

**Guardrails**: Validate params against same whitelist as REST endpoint.

---

### 3.4 Phase 1 Success Criteria

- [ ] `max_iterations` independently controllable from canopy dashboard
- [ ] `max_epochs` default aligned across cascor and canopy (1,000,000)
- [ ] Training restarts without reset after FAILED/COMPLETED
- [ ] `set_params` works via WebSocket control channel
- [ ] All existing tests pass in both repos
- [ ] New tests added for all changes

---

## 4. Phase 2: Security Hardening

**Priority**: P1-P2 — Required before external deployment
**Estimated Duration**: 2-3 days
**Dependencies**: None (can parallel with Phase 1)

### 4.1 CR-023: Whitelist Training Start Parameters

**Effort**: 0.5 day | **Repo**: juniper-cascor

Add parameter whitelist to `TrainingStartRequest.params`:
```python
ALLOWED_START_PARAMS = {"epochs", "learning_rate", "candidate_pool_size", ...}
# Validate in route handler before forwarding
```

### 4.2 CR-026: Server-Assigned Worker IDs

**Effort**: 1 day | **Repo**: juniper-cascor

Replace client-supplied `worker_id` with server-generated UUID:
```python
# In worker_stream_handler:
worker_id = f"worker-{uuid.uuid4().hex[:12]}"  # Server assigns
# Log mapping: client-requested name → server-assigned ID
```

### 4.3 CR-024: Chunked Encoding Body Limit

**Effort**: 0.5 day | **Repo**: juniper-cascor

1. Immediate: Configure uvicorn `--limit-max-request-size`
2. Follow-up: Implement incremental body reading in middleware

### 4.4 CR-025: WebSocket Async Lock

**Effort**: 0.5 day | **Repo**: juniper-cascor

Add `asyncio.Lock` to `WebSocketManager` for connection set mutations.

### 4.5 Phase 2 Success Criteria

- [ ] Training start only accepts whitelisted parameters
- [ ] Worker IDs are server-assigned UUIDs
- [ ] Request body limit enforced regardless of transfer encoding
- [ ] WebSocket connection management is async-safe
- [ ] All security tests pass

---

## 5. Phase 3: Metrics Granularity

**Priority**: P2 — Required for usable real-time monitoring
**Estimated Duration**: 8-12 days
**Dependencies**: Phase 1 (TrainingState field additions)

### 5.1 Define Progress Fields in TrainingState

**Effort**: 1 day | **Repo**: juniper-cascor

Add to `_STATE_FIELDS`:
- `phase_detail` (str): Sub-phase detail (e.g., "training_candidates", "retraining_output")
- `grow_iteration` (int): Current grow loop iteration
- `grow_max` (int): Maximum grow iterations
- `best_correlation` (float): Best candidate correlation
- `candidates_trained` (int): Candidates trained in current cycle
- `candidates_total` (int): Total candidates in pool
- `phase_started_at` (str): ISO timestamp of current phase start

### 5.2 Option C: Output Training Callback

**Effort**: 1-2 days | **Repo**: juniper-cascor

Add `on_epoch_callback` parameter to `train_output_layer()`:
```python
def train_output_layer(self, x, y, epochs=1000, on_epoch_callback=None):
    for epoch in range(epochs):
        # ... existing training code ...
        if on_epoch_callback and (epoch % 25 == 0 or epoch == epochs - 1):
            on_epoch_callback(epoch=epoch, loss=loss.item(), total_epochs=epochs)
```

Hook in lifecycle manager to emit metrics and update TrainingState.

### 5.3 Grow-Network State Updates

**Effort**: 1-2 days | **Repo**: juniper-cascor

Update TrainingState at each grow iteration boundary:
1. Entering candidate training (phase_detail, candidates_total)
2. Candidate training finished (best_correlation, success_count)
3. Adding best candidate
4. Entering output retraining
5. Entering validation
6. Next grow iteration (grow_iteration++)

### 5.4 Canopy Progress Indicators

**Effort**: 2 days | **Repo**: juniper-canopy

- Show `hidden_units / max_hidden_units` progress
- Show elapsed time in current phase
- Add indeterminate progress animation during candidate training
- Show last-known best correlation

### 5.5 Option A: Candidate Progress Queue

**Effort**: 3-5 days | **Repo**: juniper-cascor

Add `progress_queue` to persistent forkserver worker pool:
- Workers emit lightweight progress events via `put_nowait()`
- Main process drain thread aggregates into TrainingState
- Throttle: every 10-50 epochs per worker

**Risk**: Queue contention from 50 concurrent workers
**Mitigation**: Throttle emissions; use `put_nowait()` with silent drop on full queue

### 5.6 Phase 3 Success Criteria

- [ ] Dashboard shows per-epoch loss during output training phases
- [ ] Grow loop iteration count visible (e.g., "Growth Cycle 3/1000")
- [ ] Best correlation value displayed after each candidate cycle
- [ ] Phase sub-states visible (training_candidates, retraining_output, etc.)
- [ ] Candidate progress visible with progress bar during candidate training
- [ ] No performance regression in training throughput

---

## 6. Phase 4: Architectural Improvements

**Priority**: P3-P4 — Production architecture quality
**Estimated Duration**: 9-14 days
**Dependencies**: Phases 1-3 complete

### 6.1 P5-RC-18: Typed Backend Contract

**Effort**: 3-5 days | **Repo**: juniper-canopy

Replace `Dict[str, Any]` returns in `BackendProtocol` with TypedDicts or dataclasses:

```python
class MetricsEntry(TypedDict):
    epoch: int
    metrics: MetricsData
    network_topology: TopologyData
    phase: str
    timestamp: str

class MetricsData(TypedDict):
    loss: float
    accuracy: float
    val_loss: Optional[float]
    val_accuracy: Optional[float]

class TopologyData(TypedDict):
    input_units: int
    output_units: int
    hidden_units: int
    nodes: List[NodeData]
    connections: List[ConnectionData]
```

Integrate existing dead abstractions from `data_adapter.py` or replace them.

### 6.2 P5-RC-14 + P5-RC-05: WebSocket Consumption

**Effort**: 3-4 days | **Repo**: juniper-canopy

1. Normalize relay payloads (apply `_normalize_metric()` + `_to_dashboard_metric()`)
2. Wire WebSocket data into Dash via `clientside_callback`
3. Supplement or replace REST polling with WebSocket consumption

### 6.3 KL-1: Dataset Data in Service Mode

**Effort**: 3-5 days | **Repos**: juniper-cascor, juniper-canopy

Option A: Extend cascor's `/v1/dataset/data` endpoint to return arrays (already partially exists)
Option B: Direct juniper-data integration from canopy

### 6.4 Phase 4 Success Criteria

- [ ] BackendProtocol uses typed returns
- [ ] Demo and service backends return structurally identical data
- [ ] Contract tests enforce type compliance
- [ ] WebSocket relay normalized and consumed by dashboard
- [ ] Dataset scatter plot functional in service mode

---

## 7. Dependency Graph

```
Phase 1 (Critical)
├── 3.1 CR-006: max_iterations ───────────────────────────┐
│   ├── Cascor PR first                                   │
│   └── Canopy PR second                                  │
├── 3.2 CR-007: State machine auto-reset (independent)    │
└── 3.3 CR-008: WebSocket set_params (independent)        │
                                                           │
Phase 2 (Security) — can parallel with Phase 1            │
├── 4.1 CR-023 (independent)                              │
├── 4.2 CR-026 (independent)                              │
├── 4.3 CR-024 (independent)                              │
└── 4.4 CR-025 (independent)                              │
                                                           │
Phase 3 (Metrics Granularity) — depends on Phase 1        │
├── 5.1 Progress fields ◄─────────────────────────────────┘
│   ├── 5.2 Output training callback
│   │   └── 5.4 Canopy progress indicators
│   ├── 5.3 Grow-network state updates
│   │   └── 5.4 Canopy progress indicators
│   └── 5.5 Candidate progress queue
│       └── 5.4 Canopy progress indicators
│
Phase 4 (Architecture) — depends on Phases 1-3
├── 6.1 Typed backend contract (independent)
├── 6.2 WebSocket consumption
│   ├── P5-RC-14 normalize relay (first)
│   └── P5-RC-05 wire into Dash (second)
└── 6.3 Dataset data (independent)
```

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CR-006 default change breaks existing users | Medium | High | Document migration; add deprecation notice |
| CR-007 auto-reset surprises API clients | Low | Medium | Log auto-reset; document behavior change |
| Metrics callback overhead in hot loop | Low | Low | Throttle to every 25 epochs |
| Queue contention from 50 workers | Medium | Medium | Throttle + `put_nowait()` with silent drop |
| Typed contract refactor breaks consumers | Medium | Medium | Incremental migration; backward-compatible TypedDicts |
| Cross-repo coordination delays | Medium | Medium | PR cascor first, canopy second; use feature flags |
| Test suite instability during changes | Medium | Low | Fix and stabilize tests before feature work |

---

## 9. Milestone Timeline

| Milestone | Target | Criteria |
|-----------|--------|----------|
| **M1: Interface Stability** | End of Week 1 | CR-006, CR-007, CR-008 resolved |
| **M2: Security Ready** | End of Week 2 | CR-023, CR-024, CR-025, CR-026 resolved |
| **M3: Real-Time Monitoring** | End of Week 4 | Output + candidate metrics streaming |
| **M4: Production Architecture** | End of Week 6 | Typed contracts, WebSocket consumption |

---

*End of Development Roadmap*
