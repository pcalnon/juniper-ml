# Requirements — PERF

**Area**: performance / scalability — throughput, latency, parallelization, CUDA

**Total entries**: 34

**By status**: proposed=30 | deferred=2 | superseded=2

**By priority**: P0=3 | P1=7 | P2=20 | P3=4

**By owner**: ml=23 | cas=6 | can=4 | dat=1

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

### JR-CAS-PERF-001 — Optimize tensor serialization overhead in parallel candidate training via shared memory blocks.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/OPT5_SHARED_MEMORY_PLAN.md` (lines 1-32)

**Detail**:

OPT-5 eliminates redundant tensor serialization by sharing training tensors via
named POSIX shared memory. Currently each of N candidates sends same tensors through
queue. ForkingPickler already sends handles (~340 bytes) but GET-side reconstruction
costs ~320us (same-process) to ~9ms (cross-process). For 16 candidates, ~100-145ms
overhead per round. Using multiprocessing.shared_memory.SharedMemory creates named
block, workers attach by name. Expected improvement: 5-20% total round time reduction.

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

### JR-ML-PERF-002 — C-15: Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 271-272)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-PERF-003 — C-35: Latency tests are recording-only in CI; strict assertions local-only.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 284-285)

**Notes**:

[v2 ARCH→PERF re-bucket]

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-PERF-004 — CasCor remote workers must maintain zero regression in local-only throughput and limit remote overhead to < 5% of task execution.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_CONCURRENCY_PLAN.md` (lines 361-369)

**Detail**:

PR-2: Zero regression in local-only throughput. PR-3: Remote overhead < 5% task time.

### JR-ML-PERF-005 — Cascor WebSocket send must timeout at 0.5s to prevent indefinite client stalls during backpressure.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 286-292)

**Detail**:

Wrap existing await websocket.send_json(message) in asyncio.wait_for(..., timeout=self._settings.ws_send_timeout_seconds).
Default ws_send_timeout_seconds = 0.5 in Settings (range gt=0.0, le=5.0).
On asyncio.TimeoutError / WebSocketDisconnect, log INFO and return False so caller prunes.
Quick-fix mitigation for RISK-04 in Phase A-server (Day 2, commit 3).
Phase E may upgrade to full pump-task backpressure if production telemetry shows RISK-04/11 triggering.

**Notes**:

RISK-04 quick-fix. Phase E (Day 12) full backpressure deferred per R0-03 §7.2 unless production data warrants.

### JR-ML-PERF-006 — D-6: Phase E backpressure default (D-19).

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 123-124)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-PERF-007 — D-**Browser memory leak** (RISK-10): Medium-High.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 132-133)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-PERF-008 — Fix BUG-JD-10: wrap sync storage I/O in asyncio.to_thread in juniper-data batch_update_tags.

**Status**: proposed  **Priority**: P1  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/ROADMAP_AUDIT_2026-05-05.md` (lines 79-84)

### JR-ML-PERF-009 — Issues identified through deep code analysis that impact runtime performance.

**Status**: superseded  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 607-634)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 667-696)

**Notes**:

[v2 ARCH→PERF re-bucket] [v3 brief repaired from cited content; was: '16. Performance Issues (v4 new section)'] Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

[v3 brief repaired from cited content; was: '16. Performance Issues (v4 new section)'] Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-PERF-010 — V6 Partial — Agent D: Quality, Housekeeping, Performance, Configuration.

**Status**: superseded  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_d_quality_housekeeping_perf_config.md` (lines 1-100)

**Notes**:

[v2 ARCH→PERF re-bucket] v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-CAS-PERF-002 — Add GPU/CUDA support for all tensor operations and training.

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

### JR-ML-PERF-011 — CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3923-3937)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-ML-PERF-012 — CW-08: Top-Level `import torch` — First-Task Latency.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4026-4040)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-CAN-PERF-003 — Dashboard HTTP polling ignores WebSocket relay; switch to WS for real-time metrics updates.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_4/PHASE_4_CANOPY_CASCOR_CONNECTION_ANALYSIS_d7dcbd5a-667d-48ba-8d3a-f11893105c6a.md` (lines 293-310)

**Detail**:

ISS-03 LOW. Dashboard has WebSocket relay (cascor_service_adapter.py relay loop) but does NOT consume WebSocket messages. Relies entirely on HTTP polling via dcc.Interval: fast-update-interval 1000ms, slow-update-interval 5000ms. websocket-data div defined at dashboard_manager.py:876 but zero Input("websocket-data",...) Dash callback bindings exist. Performance/UX issue, not functional blocker (ISS-01 format mismatch applies to WebSocket data anyway, and ISS-11 unnormalized field names would become active bug if this fixed).

### JR-CAS-PERF-003 — Fix _roll_sequence_number memory issue in CascadeCorrelationNetwork using same optimization as CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 456-468)

**Detail**:

Line 775: list comprehension stores all discarded values. Unlike CandidateUnit version
(fixed in CASCOR-P1-008), this version still has OOM risk. Apply same fix: simple
for-loop with MAX_ROLL_COUNT cap.

### JR-ML-PERF-013 — Implement performance optimizations from training analysis.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/TRAINING_PERFORMANCE_ANALYSIS_2026-03-20.md` (lines 1-100)

**Notes**:

Throughput and latency improvements.

### JR-ML-PERF-014 — Latency instrumentation hooks for set_params round-trip measurement.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 539-590)

**Notes**:

[v2 ARCH→PERF re-bucket]

### JR-CAN-PERF-004 — Parameter retry logic must not use blocking time.sleep().

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 171-171)

**Detail**:

Issue 3.3.4: Blocking sleep in parameter retry callback blocks event loop.
Use asyncio.sleep() or defer via callback scheduling instead.

### JR-ML-PERF-015 — PERF-CC-01: Blocking `torch.save`/`torch.load` in Async-Adjacent Code Paths.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4109-4123)

### JR-ML-PERF-016 — PERF-CC-02: `replay_since` Scans Entire Replay Buffer O(n).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4126-4140)

### JR-ML-PERF-017 — PERF-CC-03: `_broadcast_training_state` Uses `hasattr` Check.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4143-4157)

### JR-ML-PERF-018 — PERF-CN-01: 33 of 50 Dash Callbacks Missing `prevent_initial_call=True`.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4075-4089)

### JR-ML-PERF-019 — PERF-CN-02: f-string Logging in Hot Paths (71 Occurrences).

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4092-4106)

### JR-ML-PERF-020 — PERF-JD-01: Readiness Probe Does Filesystem Glob on Every Call.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4160-4182)

### JR-ML-PERF-021 — PERF-JD-02: High-Cardinality Prometheus Labels.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4185-4193)

### JR-ML-PERF-022 — Phase E: Per-client pump tasks + bounded queues + policy matrix; default drop_oldest_progress_only.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 867-921)
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 52-52)
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-98)

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

[v3 xround merge: rounds=R2-0,R3-0, n=3] Conditional phase: enters if RISK-04 (backpressure issue) observed in production. Entry: Phase 0-cascor in main.
May not ship if Phase B load testing shows slow-client impact acceptable. Exit: 5 tests green, load test (50 clients,
1 slow) → fast clients <=200ms p95, dropped counters visible. Priority P2 (default), conditional entry makes it potentially deferred. / Settled position C-15 from R3-03 table; cross-round consensus consolidation / Phase E major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-PERF-023 — `ServiceDown` suppresses `HighErrorRate*` / `HighLatency*` for the same.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md` (lines 569-574)

**Notes**:

[v3 brief repaired from cited content; was: '9.3 Inhibit rules']

### JR-CAS-PERF-004 — Create baseline performance profiles using py-spy for regression detection.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/INTEGRATION_ROADMAP-01.md` (lines 635-645)

**Detail**:

Baseline py-spy profiles for key operations enable performance regression detection.

### JR-DAT-PERF-001 — GPU acceleration (CuPy, JAX, PyTorch) deferred until >1M points or >30s generation time.

**Status**: deferred  **Priority**: P3  **Category**: PERF  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 468-490)

**Notes**:

RD-016 (DATA-019). Deferred. PyTorch no longer a dependency. CUDA not in CI.

### JR-CAS-PERF-005 — Infrastructure enhancements: GPU/CUDA support, continuous profiling (Grafana Pyroscope), large file refactoring, auto-generated API docs.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CONSOLIDATED_DEVELOPMENT_RECORD.md` (lines 253-267)

**Detail**:

P3-NEW-003: GPU/CUDA support (XL, 2-4 weeks, 🔴 NOT STARTED). P3-NEW-004: Continuous profiling with Grafana Pyroscope (🔵 DEFERRED, L effort). Large file refactoring (no file > 2000 lines, 🔴 NOT STARTED, L effort). Auto-generated API docs (MkDocs/Sphinx, 🔴 NOT STARTED, M effort). Documentation link checking in CI (🔴 NOT STARTED, S effort). Documentation search functionality (🔴 NOT STARTED, M effort). All marked future work or deferred.

**Notes**:

[v2 ARCH→PERF re-bucket] [v2 remap: AR→ARCH]

### JR-CAS-PERF-006 — Process-based async plotting to avoid blocking training.

**Status**: proposed  **Priority**: P3  **Category**: PERF  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Depends on BUG-002 verification.

