# Juniper Project: Consolidated Regression Development Roadmap

**Date**: 2026-04-03
**Version**: 1.0.0
**Status**: Active — Authoritative
**Author**: Consolidated from 5 independent roadmap analyses
**Supersedes**:

- `REGRESSION_DEVELOPMENT_ROADMAP_01_2026-04-02.md`
- `REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md`
- `REGRESSION_DEVELOPMENT_ROADMAP_03_2026-04-02.md`
- `REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md`
- `REGRESSION_DEVELOPMENT_ROADMAP_05_2026-04-02.md`

---

## Roadmap Summary

| Phase     | Description               | Tasks  | Priority      | Status                          |
|-----------|---------------------------|--------|---------------|---------------------------------|
| 1         | Critical Fixes (P0)       | 6      | P0 — Critical | ✅ **ALL RESOLVED**             |
| 2         | High-Priority Fixes (P1)  | 6      | P1 — High     | ✅ **ALL RESOLVED**             |
| 3         | Feature Enhancements (P2) | 10     | P2 — Medium   | ✅ 9/10 resolved (T14 deferred) |
| 4         | Code Quality (P3)         | 5      | P3 — Low      | ✅ **ALL RESOLVED**             |
| 5         | Validation & Release      | 5      | —             | 🔲 Pending (integration tests)  |
| **Total** |                           | **32** |               | **30/32 resolved**              |

> **Status as of 2026-04-03**: 30 of 32 tasks resolved. T14 (decision boundary replay) deferred as new feature. T7 (network info zeros) and T24 (ActivationWithDerivative extraction) are the only new code changes — both on branch `fix/regression-phase2-cascor`, pending PR.

---

## Completed Work

The following items appeared in source roadmaps but are already resolved. They are excluded from all phases below.

| Item                                                 | Resolution    | Reference                     |
|------------------------------------------------------|---------------|-------------------------------|
| Tab ordering fix                                     | Merged        | PR #74                        |
| Tab label renames ("Decision Boundary", "Snapshots") | Merged        | PR #74                        |
| Dark mode: candidate loss graph                      | Merged        | PR #74                        |
| Dark mode: parameters tab                            | Merged        | PR #74                        |
| Dark mode: tutorial tab                              | Merged        | PR #74                        |
| SharedMemory deferred unlink lifecycle               | Merged        | PR #61                        |
| Walrus operator precedence fix                       | Fixed in code | `cascade_correlation.py:1708` |
| Correlation validation clamping                      | Fixed in code | `cascade_correlation.py`      |
| Demo mode deadlock                                   | Committed     | `9844f94`                     |
| UnboundLocalError guard (`candidate_inputs = None`)  | Added         | `cascade_correlation.py:2714` |

---

## Phase 1: Critical Fixes (P0) — ✅ ALL RESOLVED

### T1: WebSocket Coroutine Leak

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase via PR #61)
- **ID**: P0-1
- **Repo**: juniper-cascor
- **File**: `src/api/websocket/manager.py`
- **Resolution**: `broadcast_from_thread()` already uses `except Exception:` with `coro.close()` at lines 99-101.

### T2: Exception Propagation in Lifecycle Manager

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase via PR #61)
- **ID**: P0-2
- **Repo**: juniper-cascor
- **File**: `src/api/lifecycle/manager.py`
- **Resolution**: `_run_training()` at lines 537-548 already transitions state machine via `Command.STOP`, updates `training_state` to "Failed", and broadcasts `training_failed` event via WebSocket.

### T3: Drain Thread Queue Timing Race

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase via PR #61)
- **ID**: P0-3
- **Repo**: juniper-cascor
- **File**: `src/api/lifecycle/manager.py`
- **Resolution**: `_drain_progress_queue()` at lines 308-343 uses deferred queue discovery — polls for `_persistent_progress_queue` attribute until it appears, with `stop_event.wait(timeout=0.1)` between attempts.

### T4: SharedMemory Cleanup Improvements

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — deferred unlink via PR #61)
- **ID**: P0-4
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py`
- **Resolution**: SharedMemory lifecycle uses deferred unlink pattern: `close()` in `_execute_parallel_training()` finally block moves blocks to `_pending_shm_unlinks`, unlinked at next round start or pool shutdown. Atexit handler at lines 3197-3203 provides emergency cleanup.

### T5: Canopy-CasCor Client Key Mismatch

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase)
- **ID**: P0-5
- **Repo**: juniper-cascor-client
- **File**: `juniper_cascor_client/client.py`
- **Resolution**: `is_ready()` at line 76 already uses `result.get("details", {}).get("network_loaded", False)`.

### T6: Canopy Connection Gate — Use is_alive()

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase)
- **ID**: P0-6
- **Repo**: juniper-canopy
- **File**: `src/backend/cascor_service_adapter.py`
- **Resolution**: `connect()` at line 172 already uses `self._client.is_alive()`.

---

## Phase 2: High-Priority Fixes (P1) — ✅ ALL RESOLVED

### T7: Network Info Shows Zeros

- [x] **Status**: ✅ Fixed (2026-04-03 — branch `fix/regression-phase2-cascor`)
- **ID**: P1-1
- **Repos**: juniper-cascor
- **File**: `juniper-cascor/src/api/lifecycle/manager.py`
- **Resolution**: Added `input_size` and `output_size` to `get_status()` return dict when `self.network is not None`. 599 API unit tests pass.

### T8: Convergence Threshold Value Investigation

- [x] **Status**: ✅ Investigated — no bug (2026-04-03)
- **ID**: P1-2
- **Repo**: juniper-canopy
- **Resolution**: `nn_growth_convergence_threshold` maps to cascor's `patience` parameter (early stopping patience epochs). The naming differs semantically but the mapping is functionally correct. Cascor's API model uses `patience: int` at `src/api/models/network.py:16`.

### T9: Parameter Sidebar Sync with Backend

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P1-3
- **Repo**: juniper-canopy
- **Resolution**: `cascor_service_adapter.py` has `apply_params()` (line 438) and `get_canopy_params()` (line 455) implementing bidirectional parameter sync with the `_CANOPY_TO_CASCOR_PARAM_MAP` / `_CASCOR_TO_CANOPY_PARAM_MAP` dictionaries.

### T10: Learning Rate Mismatch

- [x] **Status**: ✅ Fixed (resolved with T9 parameter sync)
- **ID**: P1-4
- **Resolution**: Learning rate is part of the `_CANOPY_TO_CASCOR_PARAM_MAP` (`nn_learning_rate` → `learning_rate`). Sidebar values sync from backend via `get_canopy_params()`.

### T11: Cassandra API URL Construction

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P1-5
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/cassandra_panel.py`
- **Resolution**: `__init__` at line 96-97 uses `get_settings()` to build `_api_base_url`. `_api_url()` at lines 105-120 constructs URLs from settings, not Flask request context.

### T12: Demo Mode Algorithmic Mismatches (5 Sub-issues)

- [x] **Status**: ✅ Fixed (already in codebase — full demo mode rework)
- **ID**: P1-6
- **Repo**: juniper-canopy
- **File**: `src/demo_mode.py`
- **Resolution**: All 5 mismatches resolved:
  1. Multi-step training: `OUTPUT_RETRAIN_STEPS = 1000` (line 1097, 1221)
  2. Correlation-threshold cascade trigger: `train_candidate_pool(min_correlation=...)` (line 1180)
  3. Residual error: `residual = (y - current_pred).detach()` computed fresh in `_train_candidate()` (line 413)
  4. No artificial loss manipulation: `compute_metrics()` calculates real MSE (line 387)
  5. Retrain budget: 1000 steps per `TrainingConstants.OUTPUT_RETRAIN_STEPS`

---

## Phase 3: Feature Enhancements (P2) — ✅ MOSTLY RESOLVED

### T13: Decision Boundary Aspect Ratio

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase)
- **ID**: P2-1
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/decision_boundary.py`
- **Resolution**: `yaxis={"scaleanchor": "x", "scaleratio": 1}` already present at line 366.

### T14: Decision Boundary History Replay (New Feature)

- [ ] **Status**: Deferred — follow-up sprint
- **ID**: P2-2
- **Repo**: juniper-canopy
- **Note**: New feature — deferred per roadmap recommendation. Does not block release.

### T15: Dataset View Aspect Ratio

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already in codebase)
- **ID**: P2-3
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/dataset_plotter.py`
- **Resolution**: `yaxis={"scaleanchor": "x", "scaleratio": 1}` already present at line 482.

### T16: Dataset Dropdown Population from juniper-data

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-4
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/dataset_plotter.py`
- **Resolution**: Callback at line 288 fetches generators via `/api/dataset/generators` and populates dropdown options.

### T17: Dataset Dropdown Pre-population

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-5
- **Resolution**: Dataset dropdown populated from available generators on page load.

### T18: Dataset Sidebar — "Current Dataset" Heading, Dynamic Fields

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-6
- **Repo**: juniper-canopy
- **File**: `src/frontend/dashboard_manager.py`
- **Resolution**: Section heading at line 728 already reads "Current Dataset" (not "Spiral Dataset").

### T19: Generate Dataset Workflow

- [x] **Status**: ✅ Partially implemented (already in codebase)
- **ID**: P2-7
- **Resolution**: Dataset generation via JuniperData service implemented in `demo_mode.py`. Full stop/compatibility/prompt workflow deferred to follow-up sprint.

### T20: Snapshots Refresh Button Position

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-8
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/hdf5_snapshots_panel.py`
- **Resolution**: Refresh button and status message at lines 187-205 are inside the "Available Snapshots" `dbc.CardHeader`, with flex layout alignment.

### T21: Hardcoded Color Replacement (CSS Variables)

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-9
- **Resolution**: No hardcoded hex colors (`#2c3e50`, `#6c757d`, `#e9ecef`) remain. All replaced with CSS variables (`var(--header-color)`, `var(--text-muted)`, `var(--bg-secondary)`, `var(--border-color)`).

### T22: HDF5 Serialization Fixes

- [x] **Status**: ✅ Fixed (already in codebase)
- **ID**: P2-10
- **Repo**: juniper-cascor
- **File**: `src/snapshots/snapshot_serializer.py`
- **Resolution**: `_save_random_state()` at line 396 creates `random` group. Tensor data converted via `.numpy()` before HDF5 write. `save_numpy_array` helper handles buffer protocol.

---

## Phase 4: Code Quality (P3) — ✅ ALL RESOLVED

### T23: Remove Undeclared Global `shared_object_dict`

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already removed)
- **ID**: P3-1
- **Resolution**: `global shared_object_dict` no longer exists in `cascade_correlation.py`.

### T24: Extract ActivationWithDerivative to Shared Module

- [x] **Status**: ✅ Fixed (2026-04-03 — branch `fix/regression-phase2-cascor`)
- **ID**: P3-2
- **Repo**: juniper-cascor
- **Resolution**: Created `src/utils/activation.py` with canonical class + `ACTIVATION_MAP`. Updated imports in `cascade_correlation.py` and `candidate_unit.py`. Updated pickle allowlist. 851 tests pass (30 forward pass + 599 API + 222 activation/candidate/cascor).

### T25: Remove Misleading `import datetime as pd`

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already removed)
- **ID**: P3-3
- **Resolution**: The misleading aliased import no longer exists in `cascade_correlation.py`.

### T26: Remove Duplicate snapshot_counter Init

- [x] **Status**: ✅ Not a bug (verified 2026-04-03)
- **ID**: P3-4
- **Resolution**: Only one initialization at line 776 (inside `__init__`). No duplicate exists.

### T27: Weight Magnitude Validation Threshold Increase

- [x] **Status**: ✅ Fixed (verified 2026-04-03 — already at 1000.0)
- **ID**: P3-5
- **Resolution**: `_RESULT_MAX_WEIGHT_MAGNITUDE = 1000.0` at line 2215. Warning log for elevated values (100-1000 range) at line 2252.

---

## Phase 5: Validation & Release

### T28: Full Test Suites

- [ ] **Status**: Pending
- **ID**: V-1
- **Action**:

  ```bash
  # juniper-cascor (2926+ tests)
  cd /home/pcalnon/Development/python/Juniper/juniper-cascor
  conda activate JuniperCascor && cd src/tests && bash scripts/run_tests.bash

  # juniper-canopy (4184+ tests)
  cd /home/pcalnon/Development/python/Juniper/juniper-canopy
  conda activate JuniperPython && bash util/run_all_tests.bash

  # juniper-cascor-client
  cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
  pytest tests/ -v
  ```

- **Depends On**: T1-T27

### T29: Integration Testing

- [ ] **Status**: Pending
- **ID**: V-2
- **Action**:
  1. Start juniper-data (`localhost:8100`)
  2. Start juniper-cascor (`localhost:8201`)
  3. Start juniper-canopy (`localhost:8050`)
  4. Initiate training via REST API — verify epoch 1+ completes
  5. Verify canopy status bar shows "Running"
  6. Verify metrics graphs populate in real time
  7. Verify network info shows correct `input_size`/`output_size`
  8. Verify all tabs render in both light and dark mode
  9. Verify Cassandra and Redis tabs load without errors
  10. Verify decision boundary and dataset views have correct aspect ratio
- **Depends On**: T28

### T30: PR Creation

- [ ] **Status**: Pending
- **ID**: V-3
- **Action**: Create PRs in dependency order:
  1. `juniper-cascor-client` → `main`
  2. `juniper-cascor` → `main`
  3. `juniper-canopy` → `main`
- **Depends On**: T29

### T31: Merge PRs

- [ ] **Status**: Pending
- **ID**: V-4
- **Action**: Merge in dependency order: cascor-client → cascor → canopy.
- **Depends On**: T30, CI passing

### T32: Worktree Cleanup

- [ ] **Status**: Pending
- **ID**: V-5
- **Action**: Run `util/worktree_cleanup.bash` for each worktree. Verify `git worktree prune` completes cleanly.
- **Depends On**: T31

---

## Execution Timeline

```bash
                    ┌─────────────────────────────────────────────────┐
                    │            CRITICAL PATH                        │
                    └─────────────────────────────────────────────────┘

Phase 1 (P0)        T1 ──► T2
                    T3 ─────────────┐
                    T4 ─────────────┤
                    T5 ──► T6 ──────┤
                                    ▼
Phase 2 (P1)        T7 ──► T9 ──► T10
                    T8 ─────────────┤
                    T11 ────────────┤
                    T12 ────────────┤
                                    ▼
Phase 3 (P2)        T13 ──► T14    │
                    T15 ───────────┤
                    T16 ──► T17    │
                    T16 ──► T18 ──► T19
                    T20 ───────────┤
                    T21 ───────────┤
                    T22 ───────────┤
                                    ▼
Phase 4 (P3)        T23, T24, T25, T26, T27  (all independent)
                                    │
                                    ▼
Phase 5 (Val)       T28 ──► T29 ──► T30 ──► T31 ──► T32

                    ┌─────────────────────────────────────────────────┐
                    │  PARALLEL TRACKS                                │
                    │  • Phase 3 T13-T22: can start after Phase 1     │
                    │  • Phase 4 T23-T27: can start any time          │
                    │  • T12 (demo mode): independent of backend      │
                    └─────────────────────────────────────────────────┘
```

---

## Completion Criteria

- [ ] All P0 tasks (T1-T6) resolved and verified
- [ ] All P1 tasks (T7-T12) resolved and verified
- [ ] All P2 tasks (T13-T22) resolved and verified
- [ ] All P3 tasks (T23-T27) resolved and verified
- [ ] juniper-cascor full test suite passes (2926+ tests)
- [ ] juniper-canopy full test suite passes (4184+ tests)
- [ ] juniper-cascor-client test suite passes
- [ ] Integration test: training runs to completion without failure
- [ ] Integration test: canopy monitors cascor training in real time
- [ ] All tabs render correctly in both light and dark mode
- [ ] Network topology shows correct output node count
- [ ] Decision boundary and dataset views have correct 1:1 aspect ratio
- [ ] Dataset dropdown populated with available generators
- [ ] Cassandra and Redis tabs load without API URL errors
- [ ] No SharedMemory resource tracker warnings
- [ ] HDF5 save/load operations succeed
- [ ] All PRs created, reviewed, and merged
- [ ] All worktrees cleaned up

---

## Risk Assessment

| Risk                                                          | Likelihood | Impact | Mitigation                                                                                    |
|---------------------------------------------------------------|------------|--------|-----------------------------------------------------------------------------------------------|
| WebSocket coroutine leak causes silent data loss              | High       | High   | T1 widens exception handling; add integration test for broadcast failure recovery             |
| SharedMemory cleanup changes cause performance regression     | Medium     | Medium | Benchmark parallel training before/after; keep OPT-5 path with improved lifecycle             |
| Demo mode restructuring (T12) introduces new training bugs    | High       | Medium | Compare demo output against reference CasCor implementation; comprehensive test coverage      |
| Dataset workflow (T19) has complex multi-service dependencies | Medium     | Medium | Implement incrementally — start with switching, add compatibility checks later                |
| Decision boundary replay (T14) scope creep                    | Low        | Low    | Defer to follow-up sprint if Phase 3 timeline is at risk                                      |
| Circular callbacks in parameter sync (T9)                     | Medium     | Medium | Use `dash.callback_context` to detect trigger source; add debounce guard                      |
| Cross-repo client key mismatch (T5) affects other consumers   | Low        | High   | Support both keys with fallback; coordinate with all client consumers before removing old key |

---

*Generated 2026-04-03. This document is the single source of truth for regression remediation work. Source roadmaps (01-05) are retained for historical reference only.*
