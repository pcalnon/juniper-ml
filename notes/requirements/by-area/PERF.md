# Requirements — PERF

**Area**: performance / scalability — throughput, latency, parallelization, CUDA

**Total entries**: 18

**By status**: proposed=17 | deferred=1

**By priority**: P0=2 | P1=2 | P2=12 | P3=2

**By owner**: ml=12 | can=3 | cas=2 | dat=1

---

### JR-ML-PERF-001 — JS ring buffers must cap at bound on every push (not in drain callback) to enforce memory invariant.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-01_frontend_performance.md` (lines 550-600)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 976-982)

**Detail**:

ws_dash_bridge.js: bound-in-handler invariant—every push does splice-to-cap (MAX_METRICS_BUFFER=1000, etc).
Load-bearing for RISK-12: DO NOT move the cap into the drain callback.
Ensures memory is bounded even if drain callback is never called or crashes.

**Notes**:

R0-01 §3.2.5 load-bearing. Non-negotiable. Phase B (Day 8). Memory safety for long-running dashboards.

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

### JR-ML-PERF-002 — Cascor WebSocket send must timeout at 0.5s to prevent indefinite client stalls during backpressure.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-03_replay_buffer_design.md` (lines 1-100)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 286-292)

**Detail**:

Wrap existing await websocket.send_json(message) in asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds).
Default ws_send_timeout_seconds = 0.5 in Settings (range gt=0.0, le=5.0).
On asyncio.TimeoutError / WebSocketDisconnect, log INFO and return False so caller prunes.
Quick-fix mitigation for RISK-04 in Phase A-server (Day 2, commit 3).
Phase E may upgrade to full pump-task backpressure if production telemetry shows RISK-04/11 triggering.

**Notes**:

RISK-04 quick-fix. Phase E (Day 12) full backpressure deferred per R0-03 §7.2 unless production data warrants.

### JR-ML-PERF-003 — Phase E: Per-client pump tasks + bounded queues + policy matrix; default drop_oldest_progress_only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-98)

**Notes**:

Phase E major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-CAS-PERF-001 — Add GPU/CUDA support for all tensor operations and training.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 885-912)

### JR-CAN-PERF-002 — API timeout must be reduced for fast-interval callbacks.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 176-176)

**Detail**:

Issue 3.4.1: Default API timeout too long for frequently-polled endpoints.
Set shorter timeout (2-5s) for metrics/state endpoints, keep longer (10s) for
heavy operations like dataset upload.

### JR-CAN-PERF-003 — Parameter retry logic must not use blocking time.sleep().

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 171-171)

**Detail**:

Issue 3.3.4: Blocking sleep in parameter retry callback blocks event loop.
Use asyncio.sleep() or defer via callback scheduling instead.

### JR-ML-PERF-004 — PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4109-4123)

### JR-ML-PERF-005 — PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4126-4140)

### JR-ML-PERF-006 — PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4143-4157)

### JR-ML-PERF-007 — PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4075-4089)

### JR-ML-PERF-008 — PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4092-4106)

### JR-ML-PERF-009 — PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4160-4182)

### JR-ML-PERF-010 — PERF-JD-02: High-Cardinality Prometheus Labels.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4185-4193)

### JR-ML-PERF-011 — Phase E (conditional): Per-client pump tasks + bounded queues + backpressure policy matrix.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 867-921)

**Detail**:

Replace serial fan-out in `WebSocketManager.broadcast()` with per-client pump tasks + bounded queues.
Per-client `asyncio.Queue` bounded at 256 (configurable via `Settings.ws_per_client_queue_size`).
Per-client `_pump_task` created on connect, cancelled on disconnect.
Policy dispatch: `drop_oldest_progress_only` (default) drops oldest progress events (metrics, candidate_progress);
closes 1013 for state-bearing events (state, topology, cascade_add, connection_established).
`block` (legacy): synchronously blocks broadcast until queue drains.
`close_slow`: closes 1008 if queue full >5s.
Setting: `ws_backpressure_policy = "drop_oldest_progress_only"` (env: `JUNIPER_WS_BACKPRESSURE_POLICY`).
Tests: 5 entries. Default drops oldest for progress, block policy works when opted-in, close_slow closes stalled,
slow client doesn't block fast clients, terminal state events not dropped.
Observability: `cascor_ws_dropped_messages_total{policy, reason}`, `cascor_ws_per_client_queue_depth_histogram`.

**Design**:

Single PR (P13). Overrides source-doc default (`block`) with production-safer `drop_oldest_progress_only`.
Progress events droppable, state events flow or close (prevent silent loss).

**Notes**:

Conditional phase: enters if RISK-04 (backpressure issue) observed in production. Entry: Phase 0-cascor in main.
May not ship if Phase B load testing shows slow-client impact acceptable. Exit: 5 tests green, load test (50 clients,
1 slow) → fast clients <=200ms p95, dropped counters visible. Priority P2 (default), conditional entry makes it potentially deferred.

### JR-ML-PERF-012 — Phase E default backpressure = drop_oldest_progress_only.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 52-52)

**Notes**:

Settled position C-15 from R3-03 table; cross-round consensus consolidation

### JR-DAT-PERF-001 — GPU acceleration (CuPy, JAX, PyTorch) deferred until >1M points or >30s generation time.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 468-490)

**Notes**:

RD-016 (DATA-019). Deferred. PyTorch no longer a dependency. CUDA not in CI.

### JR-CAS-PERF-002 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

