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

| Phase     | Description               | Tasks  | Priority      | Dependencies      | Est. Effort   |
|-----------|---------------------------|--------|---------------|-------------------|---------------|
| 1         | Critical Fixes (P0)       | 6      | P0 — Critical | None              | 2-3 days      |
| 2         | High-Priority Fixes (P1)  | 6      | P1 — High     | Phase 1 (partial) | 2-3 days      |
| 3         | Feature Enhancements (P2) | 10     | P2 — Medium   | Phase 2 (partial) | 3-5 days      |
| 4         | Code Quality (P3)         | 5      | P3 — Low      | Phase 1           | 0.5 day       |
| 5         | Validation & Release      | 5      | —             | Phases 1-4        | 1-2 days      |
| **Total** |                           | **32** |               |                   | **9-14 days** |

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

## Phase 1: Critical Fixes (P0) — BLOCKS RELEASES

### T1: WebSocket Coroutine Leak

- [ ] **Status**: Pending
- **ID**: P0-1
- **Repo**: juniper-cascor
- **File**: `src/api/websocket/manager.py`
- **Action**: In `broadcast_from_thread()`, widen `except RuntimeError` to `except Exception`. Add `coroutine.close()` call in the exception handler to prevent leaked unawaited coroutines.
- **Depends On**: None
- **Verification**: `grep -n 'except Exception' src/api/websocket/manager.py`

### T2: Exception Propagation in Lifecycle Manager

- [ ] **Status**: Pending
- **ID**: P0-2
- **Repo**: juniper-cascor
- **File**: `src/api/lifecycle/manager.py`
- **Action**: In `_run_training()` exception handler: (1) transition state machine to `"failed"`, (2) broadcast `"training_failed"` event via WebSocket.
- **Depends On**: T1
- **Verification**: Integration test — trigger training exception, verify state is `"failed"` and WebSocket receives failure event.

### T3: Drain Thread Queue Timing Race

- [ ] **Status**: Pending
- **ID**: P0-3
- **Repo**: juniper-cascor
- **File**: `src/api/lifecycle/manager.py`
- **Action**: Add initialization guard to drain thread's queue polling. Implement graceful wait with configurable timeout for queue availability before first poll.
- **Depends On**: None (parallel with T1-T2)
- **Verification**: Unit test with delayed queue creation; no `AttributeError` on startup.

### T4: SharedMemory Cleanup Improvements

- [ ] **Status**: Pending
- **ID**: P0-4
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py`
- **Action**: (1) Add try/finally cleanup guard for partially-created SharedMemory blocks. (2) Ensure `_active_shm_blocks` list stays consistent on exception. (3) Add `atexit` handler for emergency SharedMemory cleanup on process exit.
- **Depends On**: None
- **Verification**: Unit test for SharedMemory cleanup on creation failure; no resource tracker warnings with `CASCOR_LOG_LEVEL=DEBUG`.

### T5: Canopy-CasCor Client Key Mismatch

- [ ] **Status**: Pending
- **ID**: P0-5
- **Repo**: juniper-cascor-client
- **File**: `juniper_cascor_client/client.py`
- **Action**: In `is_ready()`, handle both `"data"` and `"details"` response keys:

  ```python
  data = result.get("data") or result.get("details") or {}
  return data.get("network_loaded", False)
  ```

  Update `testing/fake_client.py` `health_ready()` to match real server response format.
- **Depends On**: None
- **Verification**: `cd juniper-cascor-client && pytest tests/ -v`

### T6: Canopy Connection Gate — Use is_alive()

- [ ] **Status**: Pending
- **ID**: P0-6
- **Repo**: juniper-canopy
- **File**: `src/backend/cascor_service_adapter.py` (or `service_backend.py`)
- **Action**: Change `connect()` gate from `is_ready()` to `is_alive()`. A service that is alive but not yet ready (no network loaded) should still accept a connection.
- **Depends On**: T5
- **Verification**: `cd juniper-canopy && pytest src/tests/ -v -k service_adapter`

---

## Phase 2: High-Priority Fixes (P1)

### T7: Network Info Shows Zeros

- [ ] **Status**: Pending
- **ID**: P1-1
- **Repos**: juniper-cascor, juniper-canopy
- **Files**: `juniper-cascor/src/api/lifecycle/manager.py` (`get_status()` ~line 587), `juniper-canopy/src/backend/service_backend.py`
- **Action**: (1) In cascor `get_status()`, add `input_size` and `output_size` to training state when network exists. (2) In canopy `service_backend.py`, use `_first_defined()` pattern to extract dimensions from `ts`, `monitor`, or `raw` dicts.
- **Depends On**: None
- **Verification**: `curl localhost:8201/v1/training/status | jq '.input_size, .output_size'`

### T8: Convergence Threshold Value Investigation

- [ ] **Status**: Pending
- **ID**: P1-2
- **Repo**: juniper-canopy
- **File**: `src/frontend/dashboard_manager.py`, `src/backend/cascor_service_adapter.py`
- **Action**: Audit `get_canopy_params()` — ensure `nn_growth_convergence_threshold` maps to `network.convergence_threshold` and `nn_growth_preset_epochs` maps to `network.growth_preset_epochs`. Fix any swapped mappings.
- **Depends On**: None
- **Verification**: Start training, verify sidebar threshold matches backend value.

### T9: Parameter Sidebar Sync with Backend

- [ ] **Status**: Pending
- **ID**: P1-3
- **Repo**: juniper-canopy
- **File**: `src/frontend/dashboard_manager.py`, `src/backend/cascor_service_adapter.py`
- **Action**: Add callback to fetch actual runtime parameters from cascor backend and update all 22 `nn_*`/`cn_*` sidebar input fields. Guard against circular callback triggers.
- **Depends On**: T7 (status API must expose params)
- **Verification**: Start training, verify sidebar values update from backend state.

### T10: Learning Rate Mismatch

- [ ] **Status**: Pending
- **ID**: P1-4
- **Repo**: juniper-canopy
- **Files**: `src/frontend/components/training_metrics.py`, `src/frontend/dashboard_manager.py`
- **Action**: Ensure learning rate in metrics graph heading and sidebar value both reflect the actual runtime value from the backend, not a stale default.
- **Depends On**: T9
- **Verification**: Visual — graph heading LR matches sidebar LR matches backend LR.

### T11: Cassandra API URL Construction

- [ ] **Status**: Pending
- **ID**: P1-5
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/cassandra_panel.py` (~lines 99-113)
- **Action**: Replace broken Flask request-context `_api_url()` with config-based URL construction. Consider extracting to `BaseComponent` if pattern is shared with `redis_panel.py`, `worker_panel.py`.
- **Depends On**: None
- **Verification**: Navigate to Cassandra tab — no API URL error in console.

### T12: Demo Mode Algorithmic Mismatches (5 Sub-issues)

- [ ] **Status**: Pending
- **ID**: P1-6
- **Repo**: juniper-canopy
- **File**: `src/demo_mode.py`
- **Action**:
  1. Replace single-step-per-epoch with configurable `OUTPUT_STEPS_PER_EPOCH` (50)
  2. Replace loss-stagnation cascade trigger with correlation-threshold-based trigger
  3. Compute residual error AFTER output convergence, not before retrain
  4. Remove artificial loss manipulation (~lines 871-872)
  5. Increase output retrain budget from 500 to 1000 steps
- **Depends On**: None (demo mode is independent of cascor backend)
- **Verification**: Run demo mode — loss decreases, cascades spaced 20+ epochs apart, >90% accuracy within 300 epochs.

---

## Phase 3: Feature Enhancements (P2)

### T13: Decision Boundary Aspect Ratio

- [ ] **Status**: Pending
- **ID**: P2-1
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/decision_boundary.py` (~line 149)
- **Action**: Add `yaxis=dict(scaleanchor="x", scaleratio=1)` to figure layout. Adjust container CSS for responsive aspect ratio.
- **Depends On**: None
- **Verification**: Visual — boundary plot is square, not stretched.

### T14: Decision Boundary History Replay (New Feature)

- [ ] **Status**: Pending
- **ID**: P2-2
- **Repo**: juniper-canopy
- **Files**: `src/frontend/components/decision_boundary.py`, backend API
- **Action**: (1) Store decision boundary snapshot at each hidden node addition. (2) Add `dcc.Store` for boundary history. (3) Add slider/stepper control for navigating boundary evolution. (4) Add play/pause replay animation.
- **Depends On**: T13
- **Verification**: Add 3+ hidden nodes, use slider to view boundary at each stage.
- **Note**: Can be deferred to follow-up sprint without blocking release.

### T15: Dataset View Aspect Ratio

- [ ] **Status**: Pending
- **ID**: P2-3
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/dataset_plotter.py` (~line 222)
- **Action**: Same approach as T13 — add `scaleanchor`/`scaleratio` to scatter plot layout.
- **Depends On**: None
- **Verification**: Visual — dataset scatter plot is square.

### T16: Dataset Dropdown Population from juniper-data

- [ ] **Status**: Pending
- **ID**: P2-4
- **Repo**: juniper-canopy
- **Files**: `src/frontend/components/dataset_plotter.py`, `src/frontend/dashboard_manager.py`
- **Action**: Add callback to fetch available generators via `juniper-data-client` `list_generators()` API and populate dropdown options. Add error handling for unavailable service.
- **Depends On**: None
- **Verification**: Dropdown shows generators from juniper-data `/v1/generators`.

### T17: Dataset Dropdown Pre-population

- [ ] **Status**: Pending
- **ID**: P2-5
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/dataset_plotter.py`
- **Action**: Pre-select the currently active training dataset in the dropdown on page load.
- **Depends On**: T16
- **Verification**: On load, dropdown shows current dataset name as selected.

### T18: Dataset Sidebar — "Current Dataset" Heading, Dynamic Fields

- [ ] **Status**: Pending
- **ID**: P2-6
- **Repo**: juniper-canopy
- **File**: `src/frontend/dashboard_manager.py`
- **Action**: (1) Rename "Spiral Dataset" section header to "Current Dataset". (2) Replace hardcoded spiral parameter fields with dynamic container that updates visibility/labels based on selected generator type.
- **Depends On**: T16
- **Verification**: Select different dataset type — sidebar fields update accordingly.

### T19: Generate Dataset Workflow

- [ ] **Status**: Pending
- **ID**: P2-7
- **Repo**: juniper-canopy
- **Files**: `src/frontend/dashboard_manager.py`, `src/frontend/components/dataset_plotter.py`, `src/backend/data_adapter.py`
- **Action**: Implement full workflow: (1) stop training on button click, (2) generate new dataset via juniper-data, (3) update scatter plot, (4) update feature distributions, (5) check network compatibility, (6) prompt user if incompatible.
- **Depends On**: T16, T18
- **Verification**: Click Generate → training stops → new data appears → compatibility check fires.

### T20: Snapshots Refresh Button Position

- [ ] **Status**: Pending
- **ID**: P2-8
- **Repo**: juniper-canopy
- **File**: `src/frontend/components/hdf5_snapshots_panel.py` (~lines 113-124)
- **Action**: Move refresh button and status message from main panel header to "Available Snapshots" section heading. Use `dbc.Row` with `justify="between"`.
- **Depends On**: None
- **Verification**: Visual — refresh button is inside Available Snapshots card, not in main header.

### T21: Hardcoded Color Replacement (CSS Variables)

- [ ] **Status**: Pending
- **ID**: P2-9
- **Repo**: juniper-canopy
- **Files**: `src/frontend/components/hdf5_snapshots_panel.py` (lines 111, 123, 216), `src/frontend/components/cassandra_panel.py` (line 200)
- **Action**: Replace hardcoded hex colors with CSS variables: `#2c3e50` → `var(--header-color)`, `#6c757d` → `var(--text-muted)`, `#e9ecef` → `var(--bg-secondary)`.
- **Depends On**: None
- **Verification**: Toggle dark mode — HDF5 and Cassandra panels use theme colors.

### T22: HDF5 Serialization Fixes

- [ ] **Status**: Pending
- **ID**: P2-10
- **Repo**: juniper-cascor
- **File**: `src/snapshots/snapshot_serializer.py`
- **Action**: (1) Ensure all objects passed to HDF5 writer support buffer protocol. (2) Add `random` group to HDF5 serialization format.
- **Depends On**: None
- **Verification**: Save and load snapshot without `BufferError`; `random` group present in HDF5 file.

---

## Phase 4: Code Quality (P3)

### T23: Remove Undeclared Global `shared_object_dict`

- [ ] **Status**: Pending
- **ID**: P3-1
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py` (line 2923)
- **Action**: Delete `global shared_object_dict` — variable is never declared at module scope.
- **Depends On**: None
- **Verification**: `grep -n 'shared_object_dict' src/cascade_correlation/cascade_correlation.py` — no results.

### T24: Extract ActivationWithDerivative to Shared Module

- [ ] **Status**: Pending
- **ID**: P3-2
- **Repo**: juniper-cascor
- **Files**: `src/utils/activation.py` (new), `src/cascade_correlation/cascade_correlation.py`, `src/candidate_unit/candidate_unit.py`
- **Action**: Create canonical `ActivationWithDerivative` class in `src/utils/activation.py`. Update both consumers to import from the shared module. Verify `ACTIVATION_MAP` is consistent.
- **Depends On**: None
- **Verification**: `python -c "from src.utils.activation import ActivationWithDerivative"` succeeds; full test suite passes.

### T25: Remove Misleading `import datetime as pd`

- [ ] **Status**: Pending
- **ID**: P3-3
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py` (line 39)
- **Action**: Delete the misleading aliased import. If `pd` is referenced elsewhere in the file, replace with correct `datetime` usage.
- **Depends On**: None
- **Verification**: `grep -n 'import datetime as pd' src/cascade_correlation/cascade_correlation.py` — no results; no `NameError` at runtime.

### T26: Remove Duplicate snapshot_counter Init

- [ ] **Status**: Pending
- **ID**: P3-4
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py` (line 779)
- **Action**: Remove the duplicate `self.snapshot_counter = 0` if it is already initialized in `__init__`.
- **Depends On**: None
- **Verification**: `grep -n 'snapshot_counter = 0' src/cascade_correlation/cascade_correlation.py` — single occurrence.

### T27: Weight Magnitude Validation Threshold Increase

- [ ] **Status**: Pending
- **ID**: P3-5
- **Repo**: juniper-cascor
- **File**: `src/cascade_correlation/cascade_correlation.py` (line 2155)
- **Action**: Change `_RESULT_MAX_WEIGHT_MAGNITUDE = 100.0` to `1000.0`. Add warning log (without rejection) for values in the 100.0–1000.0 range.
- **Depends On**: None
- **Verification**: `grep -n '_RESULT_MAX_WEIGHT_MAGNITUDE' src/cascade_correlation/cascade_correlation.py` shows `1000.0`.

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
