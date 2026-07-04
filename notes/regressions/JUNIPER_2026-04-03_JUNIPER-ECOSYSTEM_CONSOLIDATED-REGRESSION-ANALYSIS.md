# Juniper Project — Consolidated Regression Analysis

**Date**: 2026-04-03
**Version**: 1.0.0
**Status**: Active
**Scope**: juniper-cascor, juniper-canopy, juniper-cascor-client
**Supersedes**: REGRESSION_ANALYSIS_01 through _09 (2026-04-02)

---

## Executive Summary

The Juniper project has **36 identified issues** across juniper-cascor (11 root causes) and juniper-canopy (25 issues). The most critical is the cascor OPT-5 SharedMemory training failure introduced in commit `f603f1b`, which cascades into ~12 canopy downstream symptoms. Of the 36 issues, **10 have been resolved** through PRs #61, #74, and prior commits. **26 issues remain open**, with 6 at P0 (critical) severity.

**Key Insight**: ~60% of reported canopy symptoms are downstream effects of the cascor training failure. Fixing the cascor training pipeline resolves the majority of canopy's apparent regressions automatically.

---

## Issue Status Summary

| ID           | Description                                          | Severity | Status      | Resolution               |
|--------------|------------------------------------------------------|----------|-------------|--------------------------|
| CASCOR-RC-01 | SharedMemory premature cleanup / use-after-free race | P0       | Partial     | PR #61 (deferred unlink) |
| CASCOR-RC-02 | Walrus operator precedence bug                       | P1       | **Fixed**   | Already corrected        |
| CASCOR-RC-03 | WebSocket coroutine leak in broadcast_from_thread    | P0       | Open        | —                        |
| CASCOR-RC-04 | Exception handling in _run_training                  | P0       | Open        | —                        |
| CASCOR-RC-05 | Drain thread queue timing race                       | P0       | Open        | —                        |
| CASCOR-RC-06 | Correlation validation rejects valid results         | P1       | **Fixed**   | Clamping added           |
| CASCOR-RC-07 | Undeclared global variable (dead code)               | P3       | Open        | —                        |
| CASCOR-RC-08 | Duplicate ActivationWithDerivative class             | P3       | Open        | —                        |
| CASCOR-RC-09 | UnboundLocalError in error handler                   | P0       | **Fixed**   | Guard added              |
| CASCOR-RC-10 | HDF5 serialization failures                          | P2       | Open        | —                        |
| CASCOR-RC-11 | Weight magnitude validation too strict               | P2       | Open        | —                        |
| CAN-01       | Tab ordering incorrect                               | P1       | **Fixed**   | PR #74                   |
| CAN-02       | Tab labels (Decision Boundary, Snapshots)            | P1       | **Fixed**   | PR #74                   |
| CAN-03       | Status bar shows "Failed"                            | P1       | Downstream  | Resolves with cascor fix |
| CAN-04       | Demo mode training deadlock                          | P0       | **Fixed**   | Commit 9844f94           |
| CAN-05       | Demo mode algorithmic mismatches (5 issues)          | P0       | Open        | —                        |
| CAN-06       | Canopy-CasCor connection data contract mismatch      | P0       | Open        | —                        |
| CAN-07       | Network information shows zeros                      | P1       | Open        | —                        |
| CAN-08       | Convergence threshold shows wrong value              | P1       | Open        | —                        |
| CAN-09       | Network parameters show defaults                     | P1       | Open        | —                        |
| CAN-10       | Learning rate mismatch                               | P1       | Open        | —                        |
| CAN-11       | Candidate metrics — all data missing                 | P1       | Downstream  | Resolves with cascor fix |
| CAN-12       | Candidate loss graph dark mode                       | P2       | **Fixed**   | PR #74                   |
| CAN-13       | Network topology output node count                   | P2       | Investigate | —                        |
| CAN-14       | Decision boundary aspect ratio                       | P2       | Open        | —                        |
| CAN-15       | Decision boundary history replay                     | P2       | Open        | New feature              |
| CAN-16       | Dataset view aspect ratio                            | P2       | Open        | —                        |
| CAN-17       | Dataset dropdown not populated                       | P2       | Open        | —                        |
| CAN-18       | Dataset dropdown not pre-populated                   | P2       | Open        | —                        |
| CAN-19       | Dataset section heading hardcoded                    | P2       | Open        | —                        |
| CAN-20       | Generate dataset workflow incomplete                 | P2       | Open        | Feature gap              |
| CAN-21       | Snapshots refresh button position                    | P2       | Open        | —                        |
| CAN-22       | Cassandra tab API URL error                          | P1       | Open        | —                        |
| CAN-23       | Parameters tab dark mode                             | P3       | **Fixed**   | PR #74                   |
| CAN-24       | Tutorial tab dark mode                               | P3       | **Fixed**   | PR #74                   |
| CAN-25       | Hardcoded colors in panels                           | P2       | Open        | —                        |

---

## Section 1: juniper-cascor Root Causes

### CASCOR-RC-01: SharedMemory Premature Cleanup / Use-After-Free Race (P0)

**Description**: The OPT-5 SharedMemory optimization (commit `f603f1b`) introduced multiple interrelated defects in the parallel candidate training pipeline.

**Root Cause**: The `finally` block in `_execute_parallel_training()` calls `close_and_unlink()` on SharedMemory blocks while persistent pool workers may still be reading. When parallel training fails and falls back to sequential, sequential workers find SHM blocks already unlinked (`FileNotFoundError: /juniper_train_cbee87b2`). Additionally, zero-copy tensor views from SharedMemory are read-only; in-place operations crash with `RuntimeError`.

**Evidence**:

- `cascade_correlation.py` lines 1826–1831: SHM block creation
- `cascade_correlation.py` lines 2129–2134: Premature cleanup in finally block
- `cascade_correlation.py` lines 3134–3142: atexit handler
- Log: `FileNotFoundError: [Errno 2] No such file or directory: '/juniper_train_cbee87b2'`
- Resource tracker: "9 leaked semaphore objects", "1 leaked shared_memory objects"

**Impact**: Training crashes on first epoch. All downstream canopy monitoring fails.

**Status**: Partially fixed — PR #61 implemented deferred unlink (close without unlink, defer to next round). Tensor clone fix applied. Additional improvements needed: move cleanup scope, partial creation guards.

### CASCOR-RC-02: Walrus Operator Precedence Bug (P1) — FIXED

**Description**: Line 1708: `if snapshot_path := self.create_snapshot() is not None:` assigns boolean due to `:=` binding looser than `is not`.

**Fix**: `if (snapshot_path := self.create_snapshot()) is not None:` — already corrected in codebase.

### CASCOR-RC-03: WebSocket Coroutine Leak (P0)

**Description**: `broadcast_from_thread()` only catches `RuntimeError` when calling `asyncio.run_coroutine_threadsafe()`. Other exceptions (ValueError, TypeError) cause unawaited coroutines to accumulate.

**File**: `src/api/websocket/manager.py` lines 89–101

**Impact**: Coroutine accumulation during training broadcasts; event loop corruption; canopy never receives failure notifications.

**Fix**: Broaden to `except Exception`, always call `coro.close()`.

### CASCOR-RC-04: Exception Handling in _run_training (P0)

**Description**: Training exceptions in the background thread are logged but NOT propagated to the state machine. WebSocket clients never receive a "training_failed" event.

**File**: `src/api/lifecycle/manager.py` lines 533–538

**Impact**: State machine stays in inconsistent state. Clients see training start but never receive termination notification.

### CASCOR-RC-05: Drain Thread Queue Timing Race (P0)

**Description**: The drain thread starts polling for `_persistent_progress_queue` before `grow_network()` creates it via `_ensure_worker_pool()`.

**File**: `src/api/lifecycle/manager.py` lines 383–401

**Fix**: Add initialization guard that waits for queue creation before polling.

### CASCOR-RC-06: Correlation Validation Rejects Valid Results (P1) — FIXED

**Description**: `_validate_training_result` strictly rejects `correlation > 1.0`, but floating-point arithmetic can produce values marginally above 1.0.

**Fix**: Clamping added in `candidate_unit.py::_calculate_correlation()`.

### CASCOR-RC-07: Undeclared Global Variable (P3)

**Description**: `global shared_object_dict` at line 2923 — never defined. Dead code from earlier design.

### CASCOR-RC-08: Duplicate ActivationWithDerivative Class (P3)

**Description**: Identical class in `cascade_correlation.py:521` and `candidate_unit.py:140` with separate `ACTIVATION_MAP` dicts. Silent divergence risk in multiprocessing.

### CASCOR-RC-09: UnboundLocalError in Error Handler (P0) — FIXED

**Description**: `candidate_inputs` referenced before assignment in exception handler at line 2788. Guard `candidate_inputs = None` added.

### CASCOR-RC-10: HDF5 Serialization Failures (P2)

**Description**: Two distinct errors: (1) `TypeError: object supporting the buffer API required` during save, (2) `KeyError: Missing required group: random` during validation.

**Impact**: Snapshots cannot be saved/loaded, making training unrecoverable after interruption.

### CASCOR-RC-11: Weight Magnitude Validation Too Strict (P2)

**Description**: `_RESULT_MAX_WEIGHT_MAGNITUDE = 100.0` rejects legitimate candidates during early training when residual errors are large and weights can legitimately exceed 100.0.

**Fix**: Increase to 1000.0 and add warning log without rejection for 100–1000 range.

---

## Section 2: juniper-canopy Issues

### Downstream Symptoms (resolve when cascor training is fixed)

| ID     | Issue                         | Root Cause                           |
|--------|-------------------------------|--------------------------------------|
| CAN-03 | Status bar shows "Failed"     | Cascor training fails → FSM → FAILED |
| CAN-11 | Candidate metrics all missing | No candidate training data generated |

### Independent Bugs

**CAN-05: Demo Mode Training Algorithmic Mismatches (P0)** — 5 mismatches with CasCor reference: (1) single-step-per-epoch vs 1000-step phases, (2) wrong cascade trigger, (3) stale residual, (4) artificial loss manipulation, (5) insufficient retrain budget. File: `demo_mode.py` lines 681–872.

**CAN-06: Canopy-CasCor Connection Mismatch (P0)** — Client `is_ready()` expects `result.get("data")`, server returns `result.get("details")`. Always returns False. File: `juniper-cascor-client/client.py:76`, `canopy/src/backend/service_backend.py`.

**CAN-07: Network Information Shows Zeros (P1)** — `/api/status` doesn't include `input_size`/`output_size`. Handler defaults to 0.

**CAN-08: Convergence Threshold Wrong Value (P1)** — Callback field mapping may be incorrect. Needs investigation.

**CAN-09: Network Parameters Show Defaults (P1)** — No sync callback from backend to sidebar inputs.

**CAN-10: Learning Rate Mismatch (P1)** — Graph heading reads from API, sidebar from static default.

**CAN-13: Network Topology Output Nodes (P2)** — Cascor uses output_size=2 (2-spiral), demo uses 1. May be correct behavior. Also: output_weights setter doesn't update output_size.

**CAN-22: Cassandra API URL Error (P1)** — `_api_url()` uses Flask request context not available in Dash callbacks. Falls back to incorrect URL.

### Feature Gaps

**CAN-14/16**: Decision boundary and dataset view aspect ratio — fixed heights without ratio constraint.

**CAN-15**: Decision boundary history replay — not implemented.

**CAN-17/18**: Dataset dropdown not populated or pre-populated.

**CAN-19**: Dataset section heading hardcoded to "Spiral Dataset".

**CAN-20**: Generate dataset workflow incomplete — missing stop/compatibility/prompt logic.

**CAN-21**: Snapshots refresh button position — should be in section heading.

**CAN-25**: Hardcoded colors in HDF5/Cassandra panels — should use CSS variables.

---

## Section 3: Cross-Application Issues

**CROSS-01 (= CAN-06)**: Canopy-CasCor data contract mismatch requires coordinated changes across juniper-cascor-client (fix key lookup) and juniper-canopy (use `is_alive()` instead of `is_ready()` for connection gate).

---

## Section 4: Root Cause Dependency Map

```bash
CASCOR-RC-01 (SharedMemory) ─── PRIMARY ROOT CAUSE ──────────────────────┐
    │                                                                    │
    ├──→ Training fails after first epoch                                │
    │    ├──→ CAN-03: Status bar "Failed"                                │
    │    ├──→ CAN-07: Network info zeros (partially)                     │
    │    ├──→ CAN-09: Parameters show defaults (partially)               │
    │    ├──→ CAN-10: Learning rate mismatch (partially)                 │
    │    ├──→ CAN-11: Candidate metrics missing                          │
    │    └──→ All training graphs empty/incorrect                        │
    │                                                                    │
CASCOR-RC-03 (coroutine leak)                                            │
    └──→ Event loop corruption → WebSocket failures ─────────────────────┤
                                                                         │
CASCOR-RC-04 (exception handling)                                        │
    └──→ State machine not updated → stale status ───────────────────────┤
                                                                         │
CAN-06 (connection mismatch) ─── INDEPENDENT ──→ is_ready() always False │
    └──→ Canopy can't connect even when cascor is healthy                │
                                                                         │
INDEPENDENT ISSUES (not caused by cascor failure):                       │
    CAN-05: Demo training algorithmic mismatches                         │
    CAN-14/16: Aspect ratio issues                                       │
    CAN-15: Decision boundary replay (feature gap)                       │
    CAN-17–20: Dataset view features                                     │
    CAN-22: Cassandra API URL                                            │
    CAN-25: Hardcoded colors                                             │
```

---

## Section 5: Downstream Symptom Resolution

| Issue  | Description               |    Self-Resolves When Cascor Fixed?     |
|--------|---------------------------|:---------------------------------------:|
| CAN-03 | Status bar "Failed"       |                   Yes                   |
| CAN-07 | Network info zeros        |     Partially (also needs API fix)      |
| CAN-09 | Parameters show defaults  |  Partially (also needs sync callback)   |
| CAN-10 | Learning rate mismatch    | Partially (also needs data binding fix) |
| CAN-11 | Candidate metrics missing |                   Yes                   |

---

## Section 6: Already Resolved Issues

| Issue                  | Resolution               | Reference               | Date           |
|------------------------|--------------------------|-------------------------|----------------|
| CASCOR-RC-02           | Walrus operator fix      | Already corrected       | Pre-2026-04-02 |
| CASCOR-RC-06           | Correlation clamping     | candidate_unit.py fix   | 2026-04-02     |
| CASCOR-RC-09           | UnboundLocalError guard  | candidate_inputs = None | 2026-04-02     |
| CAN-01                 | Tab ordering fixed       | PR #74                  | 2026-04-02     |
| CAN-02                 | Tab labels corrected     | PR #74                  | 2026-04-02     |
| CAN-04                 | Demo deadlock fixed      | Commit 9844f94          | 2026-04-02     |
| CAN-12                 | Candidate loss dark mode | PR #74                  | 2026-04-02     |
| CAN-23                 | Parameters dark mode     | PR #74                  | 2026-04-02     |
| CAN-24                 | Tutorial dark mode       | PR #74                  | 2026-04-02     |
| SharedMemory lifecycle | Deferred unlink          | PR #61                  | 2026-04-02     |

---

## Section 7: Remaining Open Issues by Priority

### P0 — Critical (6 issues)

1. CASCOR-RC-01: SharedMemory cleanup improvements
2. CASCOR-RC-03: WebSocket coroutine leak
3. CASCOR-RC-04: Exception propagation in lifecycle manager
4. CASCOR-RC-05: Drain thread queue timing race
5. CAN-05: Demo mode algorithmic mismatches
6. CAN-06: Canopy-CasCor connection mismatch

### P1 — High (5 issues)

7. CAN-07: Network info zeros
8. CAN-08: Convergence threshold value
9. CAN-09: Parameter sidebar sync
10. CAN-10: Learning rate mismatch
11. CAN-22: Cassandra API URL

### P2 — Medium (12 issues)

12–23: Feature enhancements, aspect ratios, dataset view, HDF5 fixes

### P3 — Low (3 issues)

24–26: Code quality (dead code, class extraction)

---

## Appendix A: Files Affected

| File                                    | Repository    | Issues                   |
|-----------------------------------------|---------------|--------------------------|
| `cascade_correlation.py`                | cascor        | RC-01,02,06,07,08,09,11  |
| `api/websocket/manager.py`              | cascor        | RC-03                    |
| `api/lifecycle/manager.py`              | cascor        | RC-04, RC-05             |
| `snapshots/snapshot_serializer.py`      | cascor        | RC-10                    |
| `candidate_unit.py`                     | cascor        | RC-06, RC-08             |
| `frontend/dashboard_manager.py`         | canopy        | CAN-01,02,07,08,09,10,19 |
| `demo_mode.py`                          | canopy        | CAN-04, CAN-05           |
| `backend/service_backend.py`            | canopy        | CAN-06, CAN-07           |
| `components/candidate_metrics_panel.py` | canopy        | CAN-11, CAN-12           |
| `components/network_visualizer.py`      | canopy        | CAN-13                   |
| `components/decision_boundary.py`       | canopy        | CAN-14, CAN-15           |
| `components/dataset_plotter.py`         | canopy        | CAN-16,17,18,20          |
| `components/cassandra_panel.py`         | canopy        | CAN-22, CAN-25           |
| `components/hdf5_snapshots_panel.py`    | canopy        | CAN-21, CAN-25           |
| `client.py`                             | cascor-client | CAN-06/CROSS-01          |

---

## Appendix B: Source Document Cross-Reference

| Issue        | A01 | A02 | A03 | A04 | A05 | A06 | A07 | A08 | A09 |
|--------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| CASCOR-RC-01 |  ✓  |  ✓  |  ✓  |  ✓  |  ✓  |  —  |  ✓  |  ✓  |  ✓  |
| CASCOR-RC-02 |  ✓  |  ✓  |  ✓  |  ✓  |  ✓  |  —  |  —  |  —  |  —  |
| CASCOR-RC-03 |  —  |  —  |  ✓  |  ✓  |  —  |  —  |  —  |  —  |  —  |
| CASCOR-RC-04 |  —  |  —  |  ✓  |  ✓  |  —  |  —  |  —  |  —  |  —  |
| CASCOR-RC-05 |  —  |  —  |  ✓  |  ✓  |  —  |  —  |  —  |  —  |  —  |
| CASCOR-RC-06 |  ✓  |  ✓  |  —  |  —  |  ✓  |  —  |  —  |  —  |  —  |
| CAN-06       |  ✓  |  —  |  ✓  |  ✓  |  —  |  —  |  —  |  —  |  —  |
| CAN-05       |  —  |  —  |  —  |  —  |  —  |  ✓  |  —  |  —  |  —  |
| CAN-22       |  ✓  |  ✓  |  ✓  |  ✓  |  —  |  ✓  |  —  |  ✓  |  ✓  |

---

*This document consolidates and supersedes all 9 individual regression analysis documents dated 2026-04-02. All findings have been cross-validated across source documents and verified against current codebase state.*
