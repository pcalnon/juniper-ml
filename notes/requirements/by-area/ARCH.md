# Requirements — ARCH

**Area**: architecture / cross-cutting design — microservices, polyrepo, interface proposals

**Total entries**: 436

**By status**: proposed=343 | designed=57 | shipped=6 | deferred=2 | superseded=28

**By priority**: P0=5 | P1=267 | P2=155 | P3=9

**By owner**: ml=402 | can=13 | cas=6 | ccl=6 | cwk=4 | dcl=4 | dat=1

---

### JR-ML-ARCH-001 — Day-1 verification procedure: 5 greps + baseline measurement before any Phase B deploy.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-02_executive_ready_deliverable.md` (lines 28-66)

**Detail**:

Pre-flight checks (must complete before Phase B PR): (1) Confirm ecosystem clean across 3 repos (git status);
(2) Verify GAP-WS-19 resolved at manager.py:138-156; (3) Record 5 scope-determining greps:
  - SessionMiddleware presence (B-pre-b budget);
  - NetworkVisualizer render tech (cytoscape vs Plotly, Phase B scope);
  - Dash version floor;
  - run_coroutine_threadsafe usage (Phase C supervisor);
  - command_id vs request_id in cascor control (Phase G contract).
(4) Measure 1-hour baseline canopy_rest_polling_bytes_per_sec in staging (denominator for >90% reduction acceptance gate).
(5) Create worktrees per Juniper convention (/home/pcalnon/Development/python/Juniper/worktrees/ format <repo>--<branch>--<YYYYMMDD-HHMM>--<shorthash>).
(6) Open Phase 0-cascor + A-SDK worktrees in parallel (no cross-repo dep until Phase G).
(7) Begin with PR-1 (phase-a-sdk-set-params on cascor-client).

**Notes**:

Gate on Phase B entry. Dedup with R4-02, R3-03.

### JR-ML-ARCH-002 — **P0: polling eliminated**.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-003 — Phase 1:.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 25-97)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 24-96)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 10-46)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 51-100)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-004 — Phase 2:.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 100-127)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 99-126)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 49-65)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 103-153)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-005 — WebSocket bridge replaces ~3 MB/s REST polling for metrics; achieves >=90% bandwidth reduction.

**Status**: proposed  **Priority**: P0  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 33-40)
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 130-135)

**Detail**:

Cascor's `/ws/training` broadcast stream emits monotonically-increasing `seq` on every outbound envelope, 
advertises `server_instance_id` + `replay_buffer_capacity` on `connection_established`, supports a 1024-entry 
replay buffer with `resume` handler, exposes `snapshot_seq` atomically on REST. Browser drains `/ws/training` 
into bounded Dash store, renders via Plotly.extendTraces, **stops polling `/api/metrics/history`** when healthy.
Polling kept forever as fallback kill-switch.

**Design**:

Two-phase WebSocket pipeline: Phase 0-cascor (cascor server prerequisites) + Phase B (browser bridge drain).
Phase 0-cascor: sequence numbers, replay buffer, resume protocol, state coalescer fix.
Phase B: ws_dash_bridge.js drain module, Plotly extendTraces for metrics panel, connection-status store,
fallback toggle via `enable_browser_ws_bridge` (default False until staging soak) + `disable_ws_bridge` (permanent kill switch).

**Notes**:

P0 motivator. Metric: `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Dedup candidate with R3-03.

### JR-CAS-ARCH-001 — CasCor must expose REST API for training lifecycle operations (19 endpoints).

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-735)

**Detail**:

FastAPI service layer with REST endpoints for all training lifecycle operations; WebSocket endpoints for real-time streaming (/ws/training, /ws/control); ThreadPoolExecutor for blocking training.

### JR-CAS-ARCH-002 — CasCor service API must serialize training access via lock or dedicated thread.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 672-674)

**Detail**:

CascadeCorrelationNetwork is NOT thread-safe. API layer must serialize access via a lock or run training in dedicated thread with message-passing interface.

### JR-CAS-ARCH-003 — Create juniper-cascor-client and juniper-cascor-worker installable packages with PyPI publishing.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1034-1047)

### JR-CAS-ARCH-004 — Decouple Canopy from CasCor via service client; remove direct imports and sys.path manipulation.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1208-1220)

**Detail**:

Implement CascorServiceAdapter for two-mode activation (demo/service); remove legacy CascorIntegration (~1,601 lines); remove sys.path manipulation; update configuration to use CASCOR_SERVICE_URL (port 8200).

### JR-CWK-ARCH-001 — v0.3.0 major rewrite: WebSocket-based CascorWorkerAgent replaces BaseManager-based CandidateTrainingWorker as default, with TLS/mTLS support and async event loop.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 10-39)

**Detail**:

v0.3.0 (2026-04-08): WebSocket worker agent (new default) with long-lived WebSocket, work units pushed from cascor backend, binary tensor frames (struct-encoded shape/dtype/numpy data), worker capability reporting (CPU cores, GPU, versions on connect), heartbeat keepalive loop. New classes: CascorWorkerAgent (async event loop), WorkerConnection (WebSocket transport with TLS/mTLS and exponential backoff reconnection). New modules: ws_connection.py, task_executor.py (isolated training pipeline). New CLI flags: --tls-cert, --tls-key, --tls-ca for mTLS. Legacy mode (CandidateTrainingWorker) preserved behind --legacy flag with DeprecationWarning, will be removed in next major. Auth token rename: --api-key/CASCOR_API_KEY → --auth-token/CASCOR_AUTH_TOKEN (old names retained as deprecated fallbacks).

**Notes**:

Backward-compatible at deployment level via --legacy. Operators may continue legacy mode during migration window. Default mode changed; no fallback default.

### JR-ML-ARCH-006 — 1. Executive Summary.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 49-50)

### JR-ML-ARCH-007 — 1.1 Primary Finding.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 51-60)

### JR-ML-ARCH-008 — 1.2 Final Synthesis Outcome.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 61-82)

### JR-ML-ARCH-009 — 1.3 Two Critical Display Blockers.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 83-95)

### JR-ML-ARCH-010 — 1.4 Final Resolution of the Main Divergence.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 96-118)

### JR-ML-ARCH-011 — 10. Verified Working Paths.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1290-1306)

### JR-ML-ARCH-012 — 11. Consolidated Fix Recommendations.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1307-1357)

### JR-ML-ARCH-013 — 12. Implementation Priority and Ordering.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1409-1464)

### JR-ML-ARCH-014 — 13. Risk Assessment.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1465-1483)

### JR-ML-ARCH-015 — 14. Verification Plan.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1484-1485)

### JR-ML-ARCH-016 — 14.1 Automated Tests.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1486-1504)

### JR-ML-ARCH-017 — 14.2 New Contract Tests (FIX-K).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1505-1554)

### JR-ML-ARCH-018 — 14.3 Manual Integration Test.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1555-1593)

### JR-ML-ARCH-019 — 14.4 Visual Verification Checklist.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1594-1615)

### JR-ML-ARCH-020 — 15. Files Requiring Modification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1616-1617)

### JR-ML-ARCH-021 — 15.1 juniper-canopy — Required.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1618-1628)

### JR-ML-ARCH-022 — 15.2 juniper-cascor — Required (cross-repo).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1629-1635)

### JR-ML-ARCH-023 — 15.3 Optional / Recommended Cleanup.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1636-1642)

### JR-ML-ARCH-024 — 15.4 Files NOT Requiring Modification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1643-1653)

### JR-ML-ARCH-025 — 16. Post-Synthesis Validation Notes.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1654-1655)

### JR-ML-ARCH-026 — 16.1 Code Validation Results.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1656-1673)

### JR-ML-ARCH-027 — 16.2 Key Reconciliation Decisions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1674-1682)

### JR-ML-ARCH-028 — 16.3 Completeness Assessment.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1683-1733)

### JR-ML-ARCH-029 — 2. Synthesis Methodology and Governing Resolutions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 119-120)

### JR-ML-ARCH-030 — 2.1 Methodology.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 121-133)

### JR-ML-ARCH-031 — 2.2 Canonical Numbering.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 134-141)

### JR-ML-ARCH-032 — 2.3 Proposal Attribution Legend.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 142-155)

### JR-ML-ARCH-033 — 2.4 Repositories Examined.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 156-165)

### JR-ML-ARCH-034 — 3. Phase 1 / Phase 2 Assessment and Unanimous Findings.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 166-167)

### JR-ML-ARCH-035 — 3.1 Phase 1: Correctly Implemented but Incompletely Validated.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 168-195)

### JR-ML-ARCH-036 — 3.2 Phase 2: Correct but Too Narrow.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 196-207)

### JR-ML-ARCH-037 — 3.3 Unanimous Findings Preserved in Final Document.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 208-221)

### JR-ML-ARCH-038 — 4. Unified Issue Registry.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 222-223)

### JR-ML-ARCH-039 — 4.1 Final Registry.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 224-248)

### JR-ML-ARCH-040 — 4.2 Final Classification Notes.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 249-257)

### JR-ML-ARCH-041 — 5. Detailed Issue Analysis.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 258-308)

### JR-ML-ARCH-042 — 6. Cross-Proposal Agreement Matrices.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1016-1017)

### JR-ML-ARCH-043 — 6.1 Phase 5 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1018-1042)

### JR-ML-ARCH-044 — 6.2 Phase 4 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1043-1067)

### JR-ML-ARCH-045 — 6.3 Phase 3 Proposal Agreement Matrix.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1068-1096)

### JR-ML-ARCH-046 — 7. Disagreements and Final Resolutions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1097-1098)

### JR-ML-ARCH-047 — 7.1 Uppercase Status Gap: Removed vs Retained.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1099-1109)

### JR-ML-ARCH-048 — 7.10 State Sync Metrics Severity.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1183-1188)

### JR-ML-ARCH-049 — 7.2 Topology Severity: CRITICAL vs MODERATE.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1110-1118)

### JR-ML-ARCH-050 — 7.3 CasCor Phase Bug Severity.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1119-1128)

### JR-ML-ARCH-051 — 7.4 Hardcoded URL Count: 2 vs 6.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1129-1137)

### JR-ML-ARCH-052 — 7.5 Hardcoded URLs Severity: MODERATE vs LOW.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1138-1146)

### JR-ML-ARCH-053 — 7.6 `/api/metrics` Snapshot: Separate Issue vs Subsumed.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1147-1155)

### JR-ML-ARCH-054 — 7.7 Dataset Scatter: Active Bug vs Known Limitation.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1156-1164)

### JR-ML-ARCH-055 — 7.8 `candidate_epochs` Mapping Classification.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1165-1173)

### JR-ML-ARCH-056 — 7.9 Relay Raw Metrics Severity: MODERATE vs LOW.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1174-1182)

### JR-ML-ARCH-057 — 8. Architectural Root Cause Analysis and Dependency Graph.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1189-1190)

### JR-ML-ARCH-058 — 8.1 The Fundamental Problem (Consensus Across All Proposals).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1191-1205)

### JR-ML-ARCH-059 — 8.2 Why the Status Bar Works (All Proposals Agree).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1206-1209)

### JR-ML-ARCH-060 — 8.3 How the Problem Compounds (Best Articulated by P4-D).

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1210-1219)

### JR-ML-ARCH-061 — 8.4 Root Cause Dependency Graph.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1220-1258)

### JR-ML-ARCH-062 — 9. False Positives and Retractions.

**Status**: designed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 1259-1289)

### JR-ML-ARCH-063 — 0-cascor: `git revert` P1.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 342-343)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-064 — 0-cascor: `JUNIPER_WS_REPLAY_BUFFER_SIZE=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 339-340)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-065 — 0-cascor: `JUNIPER_WS_SEND_TIMEOUT_SECONDS=0.01`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 340-341)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-066 — 0-cascor: Rolling cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 341-342)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-067 — 01: Dual metric format removed aggressively.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 375-376)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-068 — 02: Phase B clientside_callback hard to debug.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 376-377)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-069 — 03: Phase C REST+WS ordering race.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 377-378)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-070 — 04: Slow-client blocks broadcasts.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 378-379)

### JR-ML-ARCH-071 — 05: Playwright misses real-cascor regression.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 379-380)

### JR-ML-ARCH-072 — 06: Reconnection storm after cascor restart.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 380-381)

### JR-ML-ARCH-073 — 07: 50-conn cap hit (multi-tenant).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 381-382)

### JR-ML-ARCH-074 — 08: Demo mode parity breaks.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 382-383)

### JR-ML-ARCH-075 — 09: Phase C unexpected behavior.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 383-384)

### JR-ML-ARCH-076 — 10: Browser memory exhaustion.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 384-385)

### JR-ML-ARCH-077 — 11: Silent data loss via drop-oldest.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 385-386)

### JR-ML-ARCH-078 — 12: Background tab memory spike.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 386-387)

### JR-ML-ARCH-079 — 13: Orphaned commands after timeout.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 387-388)

### JR-ML-ARCH-080 — 14: Cascor crash mid-broadcast.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 388-389)

### JR-ML-ARCH-081 — 15: **CSWSH attack**.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 389-390)

### JR-ML-ARCH-082 — --: Mid-week deploys for behavior-changing flag flips only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 300-301)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-083 — --: Minimum-viable carveout ~7 days (P0 only).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 301-302)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-084 — --: Phase 0-cascor staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 295-296)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-085 — --: Phase B staging soak = 72 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 296-297)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-086 — --: Phase B-pre-b staging soak = 48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 297-298)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-087 — --: Phase C flag-flip canary >= 7 days production data.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 299-300)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-088 — --: Phase D entry gate = B-pre-b in production >=48 h.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 298-299)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-089 — A-SDK: Downgrade cascor-client pin.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 343-344)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-090 — A-SDK: PyPI yank.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 344-345)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-091 — `audit_log_enabled`: B-pre-a.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 315-316)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-092 — B-pre-a: `JUNIPER_AUDIT_LOG_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 349-350)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-093 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS='*'`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 347-348)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-094 — B-pre-a: `JUNIPER_WS_ALLOWED_ORIGINS=<broader>`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 346-347)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-095 — B-pre-a: `JUNIPER_WS_IDLE_TIMEOUT_SECONDS=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 348-349)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-096 — B-pre-a: `JUNIPER_WS_MAX_CONNECTIONS_PER_IP=99999`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 345-346)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-097 — B-pre-b: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 351-352)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-098 — B-pre-b: `JUNIPER_WS_RATE_LIMIT_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 352-353)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-099 — B-pre-b: `JUNIPER_WS_SECURITY_ENABLED=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 350-351)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-100 — B: Hardcoded ring-cap reduction.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 355-356)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-101 — B: `JUNIPER_DISABLE_WS_BRIDGE=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 354-355)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-102 — B: `JUNIPER_ENABLE_BROWSER_WS_BRIDGE=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 353-354)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-103 — B: URL `?ws=off` diagnostic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 356-357)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-104 — BUG-CC-01: `create_topology_message()` Not Fully Implemented.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 536-561)

### JR-ML-ARCH-105 — BUG-CC-02: `cascade_add` Correlation Hardcoded to `0.0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 564-578)

### JR-ML-ARCH-106 — BUG-CC-03: `or` Fallback Bugs for Falsy Values in spiral_problem.py.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 581-595)

### JR-ML-ARCH-107 — BUG-CC-04: Version Strings Inconsistent Across File Headers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 598-612)

### JR-ML-ARCH-108 — BUG-CC-05: `remote_client_0.py` Hardcoded Old Monorepo Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 615-641)

### JR-ML-ARCH-109 — BUG-CC-06: 32 Test Files Have Hardcoded `sys.path.append` to Old Monorepo.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 644-658)

### JR-ML-ARCH-110 — BUG-CC-07: `TrainingMonitor.current_phase` Never Updated by State Machine.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 661-675)

### JR-ML-ARCH-111 — BUG-CC-08: Undeclared Global `shared_object_dict`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 678-692)

### JR-ML-ARCH-112 — BUG-CC-09: `validate_training_results` Uninitialized Variable When `max_epochs=0`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 695-709)

### JR-ML-ARCH-113 — BUG-CC-10: `validate_training` Validation Variables Not Initialized for No-Validation-Data Path.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 712-726)

### JR-ML-ARCH-114 — BUG-CC-11: Walrus Operator Precedence Bug in `utils.py`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 729-743)

### JR-ML-ARCH-115 — BUG-CC-12: `load_dataset` Uses `yaml.safe_load` Instead of `torch.load`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 746-779)

### JR-ML-ARCH-116 — BUG-CC-13: `RateLimiter._counters` Never Pruned — Unbounded Memory Growth.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 782-796)

### JR-ML-ARCH-117 — BUG-CC-14: `HandshakeCooldown._rejections` Never Pruned for Non-Blocked IPs.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 799-813)

### JR-ML-ARCH-118 — BUG-CC-15: `RequestBodyLimitMiddleware` Reads Full Body Before Size Check.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 816-830)

### JR-ML-ARCH-119 — BUG-CC-16: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 833-841)

### JR-ML-ARCH-120 — BUG-CC-17: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 844-852)

### JR-ML-ARCH-121 — BUG-CC-18: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 855-863)

### JR-ML-ARCH-122 — BUG-CN-01: `_stop.clear()` Race — `_perform_reset()` Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 868-882)

### JR-ML-ARCH-123 — BUG-CN-02: DashboardManager God Class (3,232 Lines).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 885-907)

### JR-ML-ARCH-124 — BUG-CN-03: 226 `hasattr` Guards in Tests Skip Test Logic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 910-924)

### JR-ML-ARCH-125 — BUG-CN-04: `_api_base_url` Hardcoded to `127.0.0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 927-941)

### JR-ML-ARCH-126 — BUG-CN-05: Service Populate Param Values with Int Defaults.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 944-958)

### JR-ML-ARCH-127 — BUG-CN-06: 1 Hz State Throttle Drops Terminal Transitions.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 961-976)

### JR-ML-ARCH-128 — BUG-CN-07: Duplicate `APP_VERSION` Assignment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 979-993)

### JR-ML-ARCH-129 — BUG-CN-08: `_demo_snapshots` List Grows Unbounded in Demo Mode.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 996-1010)

### JR-ML-ARCH-130 — BUG-CN-09: `WebSocketManager.active_connections` Not Thread Safe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1013-1027)

### JR-ML-ARCH-131 — BUG-CN-10: `message_count` Increment Not Atomic.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1030-1044)

### JR-ML-ARCH-132 — BUG-CN-11: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1047-1055)

### JR-ML-ARCH-133 — BUG-CN-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1058-1066)

### JR-ML-ARCH-134 — BUG-JD-01: `batch_export` Builds Entire ZIP in Memory — OOM Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1071-1093)

### JR-ML-ARCH-135 — BUG-JD-02: `delete()` TOCTOU Race Condition.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1096-1110)

### JR-ML-ARCH-136 — BUG-JD-03: `update_meta` Writes Without Temp File — Partial Data Exposure.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1113-1127)

### JR-ML-ARCH-137 — BUG-JD-04: Deterministic IDs with `seed=None` → Stale Cache Returns.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1130-1144)

### JR-ML-ARCH-138 — BUG-JD-05: `_version_lock` Is Class Variable — Won't Work Across Workers.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1147-1169)

### JR-ML-ARCH-139 — BUG-JD-06: `ReadinessResponse.timestamp` Uses Naive `datetime.now()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1172-1186)

### JR-ML-ARCH-140 — BUG-JD-07: `record_dataset_generation()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1189-1203)

### JR-ML-ARCH-141 — BUG-JD-08: `record_access()` Defined but Never Called.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1206-1220)

### JR-ML-ARCH-142 — BUG-JD-09: High-Cardinality Prometheus Labels from Parameterized Routes.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1223-1237)

### JR-ML-ARCH-143 — BUG-JD-10: ALL Storage Operations Block Async Event Loop.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1240-1248)

### JR-ML-ARCH-144 — BUG-JD-11: `record_access` TOCTOU Race on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1251-1259)

### JR-ML-ARCH-145 — C-01: Correlation field is `command_id`, NOT `request_id` -- every repo, every test.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 228-229)

### JR-ML-ARCH-146 — C-02: `command_response` has NO `seq` field; `/ws/control` has no replay buffer.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 229-230)

### JR-ML-ARCH-147 — C-03: `set_params` default timeout = 1.0 s (not 5.0 s).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 230-231)

### JR-ML-ARCH-148 — C-04: SDK fails fast on disconnect; no reconnect queue; no SDK-level retries.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 242-243)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-149 — C-05: Replay buffer = 1024 entries, env-configurable via `JUNIPER_WS_REPLAY_BUFFER_SIZE`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 243-244)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-150 — C-06: `server_instance_id` = programmatic key; `server_start_time` = advisory only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 231-232)

### JR-ML-ARCH-151 — C-07: `replay_buffer_capacity` added to `connection_established`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 232-233)

### JR-ML-ARCH-152 — C-08: Two-phase registration via `_pending_connections` set.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 233-234)

### JR-ML-ARCH-153 — C-09: Cascor `SetParamsRequest` has `extra="forbid"`; canopy adapter routes unclassified keys to REST with.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 234-235)

### JR-ML-ARCH-154 — C-10: Adapter->cascor auth = HMAC first-frame (NOT `X-Juniper-Role` header).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 256-257)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-155 — C-11: GAP-WS-19 `close_all` lock is RESOLVED on main; regression test only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 257-258)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-156 — C-12: Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 268-269)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-157 — C-13: Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 269-270)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-158 — C-14: Phase B ships behind two flags: `enable_browser_ws_bridge` (False->True post-soak) + `disable_ws_bri.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 270-271)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-159 — C-15: Phase E default backpressure = `drop_oldest_progress_only` (overrides source doc `block`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 271-272)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-160 — C-16: rAF coalescer scaffolded but DISABLED (`enable_raf_coalescer=False`).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 272-273)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-161 — C-17: REST fallback cadence during disconnect = 1 Hz (NOT 100 ms).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 244-245)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-162 — C-18: `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (NOT bare array).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 245-246)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-163 — C-19: Ring-bound enforced in the handler (NOT the drain callback); AST lint enforces.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 246-247)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-164 — C-20: GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy `/api/ws_latency` + histogram), both in.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 273-274)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-165 — C-21: NetworkVisualizer: minimum WS wiring in Phase B; deep migration deferred if cytoscape.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 274-275)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-166 — C-22: `_normalize_metric` dual-format contract preserved forever; CODEOWNERS hard gate in Phase H.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 275-276)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-167 — C-23: REST endpoints preserved FOREVER -- no deprecation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 247-248)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-168 — C-24: Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 258-259)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-169 — C-25: One-resume-per-connection rule (second resume -> close 1003).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 248-249)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-170 — C-26: Per-IP connection cap = 5 default; single-bucket rate limit = 10 cmd/s.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 259-260)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-171 — C-27: **`ws_security_enabled=True` (positive sense)**, NOT `disable_ws_auth`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 260-261)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-172 — C-28: Phase C flag `use_websocket_set_params=False` default; 6 hard flip gates.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 276-277)

*Merged from 4 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-173 — C-29: Debounce lives in Dash clientside callback (NOT SDK), 250 ms.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 249-250)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-174 — C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` is REFUSED by the parser (non-switch).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 250-251)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-175 — C-31: Shadow traffic: rejected.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 261-262)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-176 — C-32: Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 282-283)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-177 — C-33: Per-command HMAC deferred indefinitely.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 262-263)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-178 — C-34: Contract-test pytest marker `contract` runs on every PR in all 3 repos.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 283-284)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-179 — C-35: Latency tests are recording-only in CI; strict assertions local-only.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 284-285)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-180 — C-36: Total effort: 13.5 target / 15.75 planning buffer / ~4.5 weeks calendar.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 294-295)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-181 — C-37: P0 success metric = `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}` reduced >90.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 285-286)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-182 — C-38: Observability-before-behavior rule: metrics + panels + alerts before the behavior change.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 286-287)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-183 — C-39: Kill switch MTTR <=5 min, CI-tested, staging-drilled; untested switch is not a switch.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 287-288)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-184 — C-40: Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 235-236)

### JR-ML-ARCH-185 — C-41: `emitted_at_monotonic: float` on every `/ws/training` broadcast envelope.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 236-237)

### JR-ML-ARCH-186 — C-42: Error-budget burn-rate rule operationally binding (if 99.9% budget burns in <1 day, freeze non-relia.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 288-289)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-187 — C: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 357-358)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-188 — C: `JUNIPER_WS_SET_PARAMS_TIMEOUT=0.1`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 358-359)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-189 — Canonical settings table: 25+ configuration variables across cascor/canopy with env vars, types, defaults, validation.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 212-242)

**Detail**:

Settings with Pydantic Field(..., description=...). Cascor: ws_replay_buffer_size (int, 1024, env JUNIPER_WS_REPLAY_BUFFER_SIZE, validation >=0),
ws_send_timeout_seconds (float, 0.5, JUNIPER_WS_SEND_TIMEOUT_SECONDS, >0), ws_state_throttle_coalesce_ms (int, 1000, JUNIPER_WS_STATE_THROTTLE_COALESCE_MS, >0),
ws_resume_handshake_timeout_s (float, 5.0, JUNIPER_WS_RESUME_HANDSHAKE_TIMEOUT_S, >0), ws_pending_max_duration_s (float, 10.0, JUNIPER_WS_PENDING_MAX_DURATION_S, >0),
ws_max_connections_per_ip (int, 5, JUNIPER_WS_MAX_CONNECTIONS_PER_IP, >=1), ws_allowed_origins (list[str], [], JUNIPER_WS_ALLOWED_ORIGINS, no '*'),
ws_idle_timeout_seconds (int, 120, JUNIPER_WS_IDLE_TIMEOUT_SECONDS, >=0), ws_backpressure_policy (Literal, drop_oldest_progress_only, JUNIPER_WS_BACKPRESSURE_POLICY, enum).
Canopy: ws_security_enabled (bool, True, JUNIPER_WS_SECURITY_ENABLED, bool; CI refuses False in prod), ws_max_connections_per_ip (int, 5, JUNIPER_CANOPY_WS_MAX_CONNECTIONS_PER_IP, >=1),
ws_allowed_origins (list[str], localhost defaults, JUNIPER_CANOPY_WS_ALLOWED_ORIGINS, no '*'), ws_rate_limit_enabled (bool, True, JUNIPER_WS_RATE_LIMIT_ENABLED, bool),
ws_rate_limit_cps (int, 10, JUNIPER_WS_RATE_LIMIT_CPS, >=1), audit_log_enabled (bool, True, JUNIPER_AUDIT_LOG_ENABLED, bool),
audit_log_path (str, /var/log/canopy/audit.log, JUNIPER_AUDIT_LOG_PATH, path), audit_log_retention_days (int, 90, JUNIPER_AUDIT_LOG_RETENTION_DAYS, >=1),
disable_ws_control_endpoint (bool, False, JUNIPER_DISABLE_WS_CONTROL_ENDPOINT, bool), enable_browser_ws_bridge (bool, False→True, JUNIPER_ENABLE_BROWSER_WS_BRIDGE, bool),
disable_ws_bridge (bool, False, JUNIPER_DISABLE_WS_BRIDGE, bool), enable_raf_coalescer (bool, False, JUNIPER_ENABLE_RAF_COALESCER, bool),
enable_ws_latency_beacon (bool, True, JUNIPER_ENABLE_WS_LATENCY_BEACON, bool), use_websocket_set_params (bool, False, JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS, bool),
ws_set_params_timeout (float, 1.0, JUNIPER_WS_SET_PARAMS_TIMEOUT, >0), enable_ws_control_buttons (bool, False, JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS, bool),
disable_ws_auto_reconnect (bool, False, JUNIPER_DISABLE_WS_AUTO_RECONNECT, bool).
CI assert: every setting documented, every env var round-trips.

**Design**:

Pydantic BaseModel with Field(..., description=...) for documentation. Type-safe validation on load.
env var naming: JUNIPER_<SETTING_UPPER> for cascor, JUNIPER_CANOPY_<SETTING_UPPER> or JUNIPER_<SETTING_UPPER> for canopy (varies by context).

**Notes**:

Central to Phase execution. All settings present before merge. CI lint enforces documentation + round-trip.

### JR-ML-ARCH-190 — CCC-01: Wire-format schema evolution — strictly additive, no field rename/retype/remove; rollout state matrix.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 59-146)

**Detail**:

Wire format is additive-only. Every field added in Phase 0-cascor (seq, emitted_at_monotonic, replay_buffer_capacity, server_instance_id)
is present but may be ignored by older clients. No field is renamed, retyped, or removed.
Rollout state matrix documents per-phase per-endpoint compatibility: which fields are present,
which are optional, which old clients tolerate.
Acceptance criteria: rollout doc completed, PR contains state matrix, no surprises in cross-repo CI.

**Notes**:

Cross-cutting. Applies to all phases touching wire. Dedup with R3-03.

### JR-ML-ARCH-191 — CCC-03: Kill-switch architecture — every phase has config-only reversal, MTTR <=5 min, CI-tested, staging-drilled.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 261-340)

**Detail**:

Every behavior change has a kill switch: feature flag (boolean), config enum, or env var.
MTTR (mean time to recovery) <=5 min: flip flag + restart, no code revert needed.
Every switch CI-tested: PR includes test that toggles switch, asserts behavior changes.
Every switch staging-drilled: canary in staging verifies toggle works before production deploy.
Examples: `enable_browser_ws_bridge` (5 min toggle), `use_websocket_set_params` (2 min toggle), `ws_backpressure_policy` (env var),
`ws_allowed_origins` (env list), `disable_ws_bridge` (permanent kill, always available).
Acceptance: if kill switch fails to produce expected metric delta within 60 s, migration halts for re-planning.

**Notes**:

Cross-cutting. Principle from R1-02 principle 2. Dedup with R3-03.

### JR-ML-ARCH-192 — CONC-01: `_per_ip_counts` Check-Then-Act Race in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4216-4231)

### JR-ML-ARCH-193 — CONC-02: `_last_state_broadcast_time` Unprotected Cross-Thread R/W.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4234-4249)

### JR-ML-ARCH-194 — CONC-03: `_extract_and_record_metrics()` Split-Lock — Duplicate Metric Emission.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4252-4275)

### JR-ML-ARCH-195 — CONC-04: ALL Storage Operations Block Async Event Loop (juniper-data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4278-4301)

### JR-ML-ARCH-196 — CONC-07: `regenerate_dataset` Mutates State Without Lock.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4304-4319)

### JR-ML-ARCH-197 — CONC-08: `is_running` Reads/Writes Inconsistently Locked.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4322-4336)

### JR-ML-ARCH-198 — CONC-09: Fire-and-Forget `asyncio.create_task` Without Stored Reference.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4339-4353)

### JR-ML-ARCH-199 — CONC-10: Health Monitor Deregister/Assign Race Window.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4356-4370)

### JR-ML-ARCH-200 — CONC-12: `record_access` TOCTOU on access_count Increment.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4373-4388)

### JR-ML-ARCH-201 — Constitution: 42+ settled positions on wire format, protocol behavior, security, phase order, observability, effort.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 112-242)

**Detail**:

C-01: Correlation field `command_id`, NOT `request_id`. C-02: `command_response` NO seq; `/ws/control` no replay buffer.
C-03: `set_params` default timeout 1.0 s (not 5.0 s). C-04: SDK fails fast on disconnect, no reconnect queue, no retries.
C-05: Replay buffer 1024 entries, env-configurable. C-06: `server_instance_id` programmatic key, `server_start_time` advisory.
C-07: `replay_buffer_capacity` on `connection_established`. C-08: Two-phase registration via `_pending_connections`.
C-09: Cascor `SetParamsRequest` `extra="forbid"`; canopy routes unclassified keys to REST with WARN.
C-10: Adapter→cascor HMAC first-frame (NOT `X-Juniper-Role` header). C-11: GAP-WS-19 resolved on main, regression test only.
C-12/C-13: Phase 0-cascor carve-out from Phase B; Phase B-pre splits 0-cascor + B-pre-b.
C-14: Phase B two-flag design (`enable_browser_ws_bridge` + `disable_ws_bridge`). C-15: Phase E default `drop_oldest_progress_only`.
C-16: rAF coalescer scaffolded disabled. C-17: REST fallback 1 Hz during disconnect. C-18: `ws-metrics-buffer` = `{events, gen, last_drain_ms}`.
C-19: Ring bound in handler, not drain callback. C-20: GAP-WS-24 splits 24a (browser) + 24b (canopy endpoint).
C-21: NetworkVisualizer minimum wire Phase B, deep deferred if cytoscape. C-22: `_normalize_metric` dual format preserved, CODEOWNERS Phase H.
C-23: REST endpoints preserved FOREVER, no deprecation. C-24: Per-IP cap 5, single-bucket rate limit 10 cmd/s.
C-25: One-resume-per-connection rule. C-26: Per-command HMAC deferred. C-27: `ws_security_enabled=True` (positive sense).
C-28: Phase C flag `use_websocket_set_params=False` default, 6 hard flip gates.
C-29: Debounce in Dash callback (250 ms), not SDK. C-30: `JUNIPER_WS_ALLOWED_ORIGINS='*'` REFUSED (non-switch).
C-31: Multi-tenant isolation deferred. C-32: Chromium-only Playwright v1. C-33: Per-command HMAC deferred.
C-34: Contract-test pytest marker. C-35: Latency tests recording-only CI, strict local-only. C-36: Total 15.75 eng days / ~4.5 weeks.
C-37: P0 metric = canopy_rest_polling_bytes_per_sec >=90% reduction. C-38: Observability-before-behavior. C-39: Kill-switch MTTR <=5 min, CI-tested.
C-40: Wire format strictly additive. C-41: `emitted_at_monotonic` on every `/ws/training` broadcast.
C-42: Error-budget burn-rate operationally binding.
Plus D-NN decision mapping, effort table, feature flag inventory.

**Notes**:

Source of truth. All items settled; re-litigation via formal decision change only. Used by Phase 0-cascor through Phase I.

### JR-ML-ARCH-202 — Correctness: no seq gaps.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-203 — Correctness: no state loss.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-CCL-ARCH-001 — Create production constants module juniper_cascor_client/constants.py with ~30 constants (URLs, timeouts, retries, status codes).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 12-22)

**Detail**:

Sections: Service Configuration (base URLs), HTTP Configuration (timeout, retries, backoff, pool size),
HTTP Status Codes (400, 404, 409, 422, 503), Decision Boundary (resolution default/min/max),
Authentication (header name).

**Design**:

Create juniper_cascor_client/constants.py with logical sections organizing ~30 production constants.
Alternative: split into constants.py (production) and testing/constants.py (test fixtures).

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-002 — Create testing constants module juniper_cascor_client/testing/constants.py with ~65 constants (hyperparams, scenario params, topology, worker sim).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 23-37)

**Detail**:

Sections: Fake Client Configuration (URL, version, error rate, uptime), Training Hyperparameters
(learning rate, epochs, hidden units, patience), Loss/Accuracy Curve Parameters (per scenario),
Network Topology Generation (bias, weight scales), Decision Boundary Generation, Worker Simulation Data,
Dataset Configuration.

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-ML-ARCH-204 — D-1: Correlation field name (D-02).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 118-119)

### JR-ML-ARCH-205 — D-2: Phase 0-cascor carve-out (D-11).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 119-120)

### JR-ML-ARCH-206 — D-3: Two-flag browser bridge (D-17 + D-18).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 120-121)

### JR-ML-ARCH-207 — D-4: REST paths preserved forever (D-21, D-54, D-56).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 121-122)

### JR-ML-ARCH-208 — D-5: Positive-sense security flag (D-10).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 122-123)

### JR-ML-ARCH-209 — D-6: Phase E backpressure default (D-19).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 123-124)

### JR-ML-ARCH-210 — D-7: Phase C flag-flip criteria (D-48).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 124-125)

### JR-ML-ARCH-211 — D-8: Kill-switch MTTR tested (D-53).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 125-126)

### JR-ML-ARCH-212 — D-**Browser memory leak** (RISK-10): Medium-High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 132-133)

### JR-ML-ARCH-213 — D-**Cascor crash mid-broadcast** (RISK-14): Low.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 135-136)

### JR-ML-ARCH-214 — D-Correctness: no seq gaps: `cascor_ws_seq_gap_detected_total`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-215 — D-Correctness: no state loss: `cascor_ws_dropped_messages_total{type="state"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-ML-ARCH-216 — D-Criterion: Metric.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

### JR-ML-ARCH-217 — D-**CSWSH attack** (RISK-15): High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 131-132)

### JR-ML-ARCH-218 — D-**Dual metric format breakage** (RISK-01): High.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 134-135)

### JR-ML-ARCH-219 — D-Observability: full pipe: All canonical metrics present on `/metrics`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-220 — D-**P0: polling eliminated**: `canopy_rest_polling_bytes_per_sec{endpoint="/api/metrics/history"}`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-221 — D-Recovery: kill switches work: Every switch flipped in staging.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-ARCH-222 — D-Risk: Severity.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 129-130)

### JR-ML-ARCH-223 — D-Security: CSWSH closed: `canopy_ws_origin_rejected_total` page alert functional.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-ARCH-224 — D-**Silent data loss** (RISK-11): High (low likelihood).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 133-134)

### JR-ML-ARCH-225 — D: `JUNIPER_CANOPY_ENABLE_WS_CONTROL_BUTTONS=false`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 359-360)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-226 — D: `JUNIPER_DISABLE_WS_CONTROL_ENDPOINT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 360-361)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-227 — `disable_ws_auto_reconnect`: F.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 317-318)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-228 — `disable_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 308-309)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-229 — `disable_ws_control_endpoint`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 313-314)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-230 — E: `JUNIPER_WS_BACKPRESSURE_POLICY=block`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 361-362)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-231 — Effort bounds and calendar: 15.75 expected eng days (~4.5 weeks calendar) with soak windows.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R4-01_comprehensive_master_plan.md` (lines 76-94)

**Detail**:

Effort table (optimistic/expected/pessimistic): Phase 0-cascor 1.5/2.0/3.0, A-SDK 0.5/1.0/1.5, B-pre-a 0.5/1.0/1.5,
B 3.0/4.0/5.0, B-pre-b 1.0/1.5/2.0, C 1.5/2.0/3.0, D 0.75/1.0/1.5, E 0.75/1.0/1.5, F 0.25/0.5/1.0,
G 0.25/0.5/0.75, H 0.5/1.0/1.5, I 0.1/0.25/0.5. Total 10.6/15.75/22.25 eng days.
Calendar translation: 15.75 days × single-dev lane = ~3 weeks one-person, or ~4.5 weeks with 48-72 h soak windows.
Minimum-viable carveout (P0 only): ~7 days (Phase A-SDK + 0-cascor + B-pre-a + B + I).
Soak windows: 0-cascor 72 h, Phase B 72 h, B-pre-b 48 h, Phase C canary >=7 days.
Phase dependency graph: A-SDK || 0-cascor || B-pre-a → B || B-pre-b → D; C parallel with B/D; E/F/G/H follow.

**Notes**:

Risks: 0-cascor async race (+risk), A-SDK correlation map iteration (+risk), B-pre-a audit logger name collision (+risk),
B NetworkVisualizer Plotly (+1 day), B-pre-b session middleware absent (+0.5 day), C concurrent-correlation bugs (+risk),
D orphaned-command UI state (+risk), E queue tuning (+risk), F reconnect-cap lift debated.

### JR-ML-ARCH-232 — `enable_browser_ws_bridge`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 307-308)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-233 — `enable_raf_coalescer`: B.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 309-310)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-234 — `enable_ws_control_buttons`: D.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 311-312)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-235 — ERR-01: `response.json()` Unguarded Against JSONDecodeError (data-client).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4412-4426)

### JR-ML-ARCH-236 — ERR-02: `response.json()` Unguarded in cascor-client `_request()`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4429-4443)

### JR-ML-ARCH-237 — ERR-06: `raise HTTPException` Without `from e` — Lost Exception Context (cascor).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4446-4460)

### JR-ML-ARCH-238 — ERR-07: `raise HTTPException` Without `from e` — Broad Except Masks Programming Errors (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4463-4477)

### JR-ML-ARCH-239 — ERR-08: `str(e)` in Batch Create Error Response — Information Disclosure (data).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4480-4494)

### JR-ML-ARCH-240 — ERR-09: `remote_client_0.process_tasks()` Catches All Exceptions, Only Prints.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4497-4511)

### JR-ML-ARCH-241 — ERR-12: `config_manager._load_config()` Returns {} on Any Error.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4514-4529)

### JR-ML-ARCH-242 — ERR-13: `arc_agi` Generator Silent Fallback on Any Exception.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4532-4546)

### JR-ML-ARCH-243 — ERR-14: `CascorMetricsStream.stream()` Swallows ConnectionClosed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4549-4571)

### JR-ML-ARCH-244 — F: `JUNIPER_DISABLE_WS_AUTO_RECONNECT=true`.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 362-363)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-245 — Flag: Phase.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 305-306)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-CAN-ARCH-001 — get_rate_limiter() must use get_settings() instead of direct access.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 86-86)

**Detail**:

Issue 1.2.4: Inconsistent settings access pattern. Use get_settings() function
for uniform configuration retrieval. File: src/security.py

### JR-ML-ARCH-246 — H: `git revert` P16.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 363-364)

*Merged from 3 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-247 — I: `git revert` cache-bust commit.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 364-365)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-248 — ID: Risk.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 373-374)

*Merged from 2 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-249 — Observability: full pipe.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-CAN-ARCH-002 — Phase 1 Addendum—6 backend fixes (KeyError guards, thread safety, connection leaks).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 262-270)

**Detail**:

1.4.1: Guard get_dataset against KeyError on partial data (MED-036).
1.4.2: Fix prepare_dataset_for_visualization None crash (MED-038).
1.4.3: Thread-safe locking for Cassandra singleton (MED-039).
1.4.4: Thread-safe locking for Redis singleton (MED-041).
1.4.5: Fix Redis exception aliases to use sentinel class (MED-042).
1.4.6: Fix Redis force_new=True connection leak (MED-043).

### JR-ML-ARCH-250 — Phase 3:.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 130-203)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 129-202)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 68-104)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 156-230)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-CAN-ARCH-003 — Phase 3 Addendum—5 backend quality improvements (circuit breaker, lazy imports, API exposure).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 271-277)

**Detail**:

3.5.1: Cache network property or wrap in circuit breaker (MED-034).
3.5.2: Narrow relay loop exception handling (MED-035).
3.5.3: Lazy-import torch in data_adapter.py (MED-037).
3.5.4: Expose public API on CascorServiceAdapter (MED-046).
3.5.5: Don't store Cassandra credentials as plain attributes (MED-040).

### JR-ML-ARCH-251 — Phase H: Normalize_metric audit + regression gate; CODEOWNERS hard gate; pre-commit hook.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-101)

**Notes**:

Phase H major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-ML-ARCH-252 — Phase: Switch (env var).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 337-338)

*Merged from 5 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-253 — Recovery: kill switches work.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-CCL-ARCH-003 — Refactor client.py to use constants module (~20 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-44)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-004 — Refactor testing/fake_client.py to use testing constants (~40 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 50-52)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-005 — Refactor testing/scenarios.py to use testing constants (~50 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 54-56)

**Detail**:

Largest refactor: loss curve parameters, accuracy curve parameters, network topology generation,
decision boundary generation constants.

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-CCL-ARCH-006 — Refactor ws_client.py to use constants module (~4 replacements of hardcoded values).

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-48)

**Notes**:

Part of hardcoded-values refactor (HIGH priority)

### JR-ML-ARCH-254 — Security: CSWSH closed.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-ARCH-255 — `use_websocket_set_params`: C.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 310-311)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-256 — `ws_backpressure_policy`: E.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 316-317)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-257 — `ws_rate_limit_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 314-315)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-258 — `ws_security_enabled`: B-pre-b.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 312-313)

*Merged from 6 extraction candidates (slices: ml-C).*

### JR-ML-ARCH-259 — Single-tenant v1; multi-tenant replay isolation deferred.

**Status**: deferred  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 61-61)

**Notes**:

Settled position C-24 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-260 — 1. Purpose and Methodology.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 34-51)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 39-64)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-261 — 10. CasCor Algorithm and Feature Enhancements.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 360-410)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 398-450)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-262 — 11. Cross-Repository Alignment Issues.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 411-438)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 451-486)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-263 — 12. Housekeeping and Broken References.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 439-476)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 487-526)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-264 — 13. juniper-deploy Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 477-526)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 527-581)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-265 — 14. juniper-data Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 527-557)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 582-614)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-266 — 15. Client Library Outstanding Items.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 558-606)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 615-666)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-267 — 16. Performance Issues (v4 new section).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 607-634)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 667-696)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-268 — 17. Concurrency and Thread Safety Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 697-716)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-269 — 17. Source Document Lineage.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 635-657)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-270 — 18. Error Handling and Robustness (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 717-737)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-271 — 18. Validation Methodology (v4.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 658-698)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-272 — 19. Testing and CI/CD Gaps (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 738-780)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-273 — 2. Validation Summary.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 52-75)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 65-92)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-274 — 20. Configuration and Dependency Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 781-804)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-275 — 21. API Contract and Protocol Issues (v5 new).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 805-825)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-276 — 22. Source Document Lineage (v5.0.0 - v1.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 826-900)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-277 — 23. Validation Methodology (v5.0.0 - v1.0.0).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 901-941)

**Notes**:

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

### JR-ML-ARCH-278 — 3. Items Previously Incomplete — Now Fixed.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 76-100)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 93-119)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-279 — 4. Security Issues.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 101-135)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 120-156)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-280 — 5. Active Bugs (Confirmed Still Present).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 136-193)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 157-223)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-281 — 6. Code Quality and Cleanup.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 194-244)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 224-276)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-282 — 7. Dashboard Enhancements.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 245-288)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 277-322)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-283 — 8. WebSocket Migration (R5-01 Remaining Phases).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 289-324)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 323-360)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-284 — 9. Microservices and Infrastructure.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 325-359)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 361-397)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-285 — Table of Contents.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V4_VALIDATED.md` (lines 11-33)
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V5_VALIDATED.md` (lines 11-38)

**Notes**:

Superseded: V4 VALIDATED snapshot; check v6/v7 remediation entries

---

Superseded: V5 VALIDATED snapshot; check v6/v7 remediation entries

*Merged from 2 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-286 — V6 Partial — Agent B: Active Bugs (CasCor, Canopy, Data).

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_b_active_bugs.md` (lines 1-100)

**Notes**:

v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-ML-ARCH-287 — V6 Partial — Agent D: Quality, Housekeeping, Performance, Configuration.

**Status**: superseded  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/partials/v6_partial_agent_d_quality_housekeeping_perf_config.md` (lines 1-100)

**Notes**:

v6 partial agent output; pre-dates V6_REMEDIATION_ANALYSIS — likely subsumed by V6/V7 entries already captured by ml-C

### JR-ML-ARCH-288 — CAS-006: Auto-Snap Best Network.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2446-2450)

### JR-ML-ARCH-289 — CC-01: `_recv_loop` Catches Bare `Exception`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3656-3670)

### JR-ML-ARCH-290 — CC-04: `set_params()` Method Not Documented in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3673-3687)

### JR-ML-ARCH-291 — CC-05: CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3690-3698)

### JR-ML-ARCH-292 — CC-06: `command()` Never Sends `type` Field.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3701-3708)

### JR-ML-ARCH-293 — CC-07: NpzFile Resource Leak in data-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3711-3725)

### JR-ML-ARCH-294 — CC-08: WebSocket Auto-Reconnection Not Implemented.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3728-3742)

### JR-ML-ARCH-295 — CC-13: `_recv_loop` Silently Drops Non-Correlated Server Messages.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3762-3776)

### JR-ML-ARCH-296 — CC-14: `_handle_response()` Calls `response.json()` Unconditionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3779-3793)

### JR-ML-ARCH-297 — CC-15: No TLS/SSL Configuration Support on WS Streams.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3796-3810)

### JR-ML-ARCH-298 — CC-16: `FakeCascorClient.wait_for_ready()` Returns True Immediately.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3813-3827)

### JR-ML-ARCH-299 — CC-17: `FakeCascorClient.wait_for_ready()` Missing `self._lock`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3830-3844)

### JR-ML-ARCH-300 — CFG-01: `torch` Imported but Missing from canopy Dependencies.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4883-4897)

### JR-ML-ARCH-301 — CFG-02: `sentry-sdk` in Core Dependencies but Only Used Optionally.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4900-4914)

### JR-ML-ARCH-302 — CFG-03: `SENTRY_SDK_DSN` vs `JUNIPER_CASCOR_SENTRY_DSN` — Dual Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4917-4931)

### JR-ML-ARCH-303 — CFG-04: `JUNIPER_DATA_URL` Read via Raw `os.getenv`, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4934-4948)

### JR-ML-ARCH-304 — CFG-05: `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — Both Needed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4951-4965)

### JR-ML-ARCH-305 — CFG-06: `CASCOR_*` Env Prefix Inconsistent with `JUNIPER_*` Convention.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4968-4982)

### JR-ML-ARCH-306 — CFG-07: Port 8200 vs 8201 Confusion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4985-4999)

### JR-ML-ARCH-307 — CFG-08: Rate Limiting Defaults Differ Across Services.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5002-5016)

### JR-ML-ARCH-308 — CFG-09: `audit_log_path` Defaults to `/var/log/` — Requires Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5019-5041)

### JR-ML-ARCH-309 — CFG-12: `setuptools>=82.0` vs `>=61.0` Elsewhere.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5044-5058)

### JR-ML-ARCH-310 — CFG-13: `python-dotenv` in canopy Core Deps but Never Imported.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5061-5075)

### JR-ML-ARCH-311 — CFG-14: `juniper-cascor-client>=0.1.0` Allows Outdated Incompatible Versions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5078-5092)

### JR-ML-ARCH-312 — CFG-16: `CASCOR_DEMO_MODE` Read Directly, Bypasses Settings.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5095-5109)

### JR-ML-ARCH-313 — CI-01: cascor-client CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4643-4657)

### JR-ML-ARCH-314 — CI-02: cascor-worker CI Doesn't Test Python 3.14.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4660-4664)

### JR-ML-ARCH-315 — CI-03: juniper-deploy CI Runs ZERO Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4667-4681)

### JR-ML-ARCH-316 — CI-04: Missing Weekly security-scan.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4684-4695)

### JR-ML-ARCH-317 — CI-05: Missing lockfile-update.yml for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4698-4709)

### JR-ML-ARCH-318 — CI-06: juniper-deploy No Coverage Configuration.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4712-4723)

### JR-ML-ARCH-319 — CI-07: Inconsistent GitHub Actions Versions Across Repos.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4726-4737)

### JR-ML-ARCH-320 — CI-SEC-01: No Weekly Security Scan for cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4838-4842)

### JR-ML-ARCH-321 — CI-SEC-02: No Security Scanning in juniper-deploy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4845-4856)

### JR-ML-ARCH-322 — COV-01: Deploy Tests Exist but Zero Coverage.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4740-4744)

### JR-ML-ARCH-323 — COV-02: Canopy No Per-Module Coverage Gate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4747-4758)

### JR-ML-ARCH-324 — COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4761-4772)

### JR-DCL-ARCH-001 — Create juniper_data_client/constants.py module to centralize ~60 hardcoded values across codebase.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 130-145)

**Detail**:

Codebase contains ~89 hardcoded values across 6 files with no centralized constants module.
Only 3 values are defined as class-level constants on JuniperDataClient (DEFAULT_TIMEOUT, DEFAULT_RETRIES,
DEFAULT_BACKOFF_FACTOR); remaining values (16 API endpoints, connection pool sizes, HTTP status codes,
generator defaults) are inline literals. Create single constants.py organized into 7 sections:
(1) HTTP Configuration, (2) API Endpoints, (3) Timeouts & Polling, (4) Authentication,
(5) Generator Defaults, (6) Generator Mathematics, (7) Data Types.

**Design**:

Recommended structure: single juniper_data_client/constants.py (~60 constants).
Maintain backward compatibility by keeping class-level constants as aliases referencing module constants.
Validate all generator outputs match current behavior with integration tests.
Keep mathematical constants clearly separated from configuration constants.

### JR-ML-ARCH-325 — CW-01: `receive_json()` Doesn't Catch JSONDecodeError.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3906-3920)

### JR-ML-ARCH-326 — CW-02: `requirements.lock` Includes CUDA Packages (~2-4GB Bloat).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3923-3937)

### JR-ML-ARCH-327 — CW-03: No Integration Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3940-3954)

### JR-ML-ARCH-328 — CW-04: Timeout Error Sends `candidate_uuid: ""` Instead of Actual UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3957-3971)

### JR-ML-ARCH-329 — CW-05: Dynamic Import `from candidate_unit.candidate_unit import CandidateUnit`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3974-3996)

### JR-ML-ARCH-330 — CW-06: `receive_json()` in Registration Path — No JSONDecodeError Catch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3999-4006)

### JR-ML-ARCH-331 — CW-07: No Validation of `tensor_manifest` Keys Against Received Binary Frames.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4009-4023)

### JR-ML-ARCH-332 — CW-08: Top-Level `import torch` — First-Task Latency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4026-4040)

### JR-CAN-ARCH-004 — DashboardManager must be refactored for extract to <2000 lines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 177-177)

**Detail**:

Issue 3.4.2: DashboardManager is monolithic. Begin extraction of sidebar,
controls, stores, and theme logic into separate modules. Post-refactor target: <2000 lines.

### JR-ML-ARCH-333 — DC-01: GENERATOR_CIRCLE = "circle" — Server Has "circles".

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3849-3853)

### JR-ML-ARCH-334 — DC-02: GENERATOR_MOON = "moon" — No Server Generator.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3856-3860)

### JR-ML-ARCH-335 — DC-03: Missing Constants for 5 Server Generators.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3863-3867)

### JR-ML-ARCH-336 — DC-04: `FakeDataClient` Masks Generator Name Bugs.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3870-3884)

### JR-ML-ARCH-337 — DC-05: `FakeDataClient` Missing Lifecycle Methods.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3887-3901)

### JR-ML-ARCH-338 — DEPLOY-01: Docker Secret Name/Path Mismatch.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3335-3349)

### JR-ML-ARCH-339 — DEPLOY-02: AlertManager Service Missing from docker-compose.yml.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3352-3366)

### JR-ML-ARCH-340 — DEPLOY-04: K8s Canopy Missing Service URL Env Vars.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3386-3397)

### JR-CAN-ARCH-005 — Extract create_empty_plot() as shared utility across metric panels.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 162-162)

**Detail**:

Issue 3.2.3: create_empty_plot logic duplicated in multiple components.
Extract to plot_utils.py or equivalent shared module.

### JR-CWK-ARCH-002 — Hardcoded values refactoring: create juniper_cascor_worker/constants.py to consolidate ~50 hardcoded values (protocol messages, activation functions, training defaults, WebSocket config, validation bounds).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 1-50)

**Detail**:

~50 hardcoded values across 7 source files. Existing infrastructure: config.py WorkerConfig dataclass (8 field defaults, partial coverage). Gaps: protocol message type strings (7), activation function names (3), training hyperparameters (6 — epochs, learning rate, display frequency, value scales), WebSocket config (4), config duplicates across config.py/cli.py/env defaults (6), validation constants (2), error handling (2). Coverage summary: ~3 covered (partial), ~47 not covered. Proposed solution: create constants.py with sections for protocol types, activation functions, training defaults, WebSocket, config defaults, validation, error handling. Update config.py, cli.py, worker.py, task_executor.py, ws_connection.py to import from constants.py. Key benefit: eliminates 3-way duplication between config.py, cli.py, env var defaults.

### JR-ML-ARCH-341 — HSK-01: 3 Broken Symlinks in canopy `notes/development/`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2881-2895)

### JR-ML-ARCH-342 — HSK-02: `src/remote_client/` Directory Still Exists.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2898-2902)

### JR-ML-ARCH-343 — HSK-03: `src/spiral_problem/check.py` — 600-Line Stale Duplicate.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2905-2909)

### JR-ML-ARCH-344 — HSK-04: 32 Test Files with Hardcoded `sys.path.append`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2912-2916)

### JR-ML-ARCH-345 — HSK-05: cascor-client AGENTS.md Header Version 0.3.0 vs Package 0.4.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2919-2933)

### JR-ML-ARCH-346 — HSK-06: juniper-data AGENTS.md Header Version 0.5.0 vs Package 0.6.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2936-2940)

### JR-ML-ARCH-347 — HSK-07: cascor-client File Headers Show Versions 0.1.0–0.3.0.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2943-2947)

### JR-ML-ARCH-348 — HSK-08: data-client `tests/conftest.py` Version Header Says 0.3.1.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2950-2954)

### JR-ML-ARCH-349 — HSK-09: Dead Code `_STATE_TO_FSM` and `_STATE_TO_PHASE` in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2957-2982)

### JR-ML-ARCH-350 — HSK-10: `scripts/test.bash` Outdated/Non-Functional.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2985-3010)

### JR-ML-ARCH-351 — HSK-11: `wake_the_claude.bash` `DEBUG="${TRUE}"` Hardcoded ON.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3013-3028)

### JR-ML-ARCH-352 — HSK-12: `NOHUP_STATUS=$?` Captures Fork Status (Always 0).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3031-3045)

### JR-ML-ARCH-353 — HSK-13: 169 Hardcoded ThemeColors Remain in canopy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3048-3062)

### JR-ML-ARCH-354 — HSK-14: `resume_session.bash` Contains Hardcoded Session UUID.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3065-3087)

### JR-ML-ARCH-355 — HSK-15: `util/global_text_replace.bash` Is a No-Op.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3090-3112)

### JR-ML-ARCH-356 — HSK-16: `util/kill_all_pythons.bash` Uses `sudo kill -9` on ALL Python Processes.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3115-3129)

### JR-ML-ARCH-357 — HSK-17: `util/worktree_new.bash` Hardcodes Branch/Repo Names.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3132-3146)

### JR-ML-ARCH-358 — HSK-18: `util/worktree_close.bash` Hardcodes Default Identifier.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3149-3163)

### JR-ML-ARCH-359 — HSK-19: Stale Files in Repo Root.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3166-3180)

### JR-ML-ARCH-360 — HSK-20: `claude_interactive.bash:17` `DEBUG="${TRUE}"` Hardcoded.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3183-3198)

### JR-ML-ARCH-361 — HSK-21: `wake_the_claude.bash:53` Stale TODO Comment.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3201-3215)

### JR-ML-ARCH-362 — HSK-22: `wake_the_claude.bash:547` TODO — Model Parameter Never Validated.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3218-3232)

### JR-ML-ARCH-363 — HSK-23: `scripts/juniper-all-ctl:38` Cascor Port Defaults to 8200 (Container) vs Host 8201.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3235-3249)

### JR-ML-ARCH-364 — HSK-24: Unused Constants in cascor-client.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 3252-3277)

### JR-CAN-ARCH-006 — NetworkVisualizer callback is overloaded and must be split.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 172-172)

**Detail**:

Issue 3.3.5: Single callback handles too many inputs. Split into separate
callbacks for layout changes, theme changes, and data updates.

### JR-ML-ARCH-365 — Phase 0-cascor is a carve-out from Phase B.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 49-49)

**Notes**:

Settled position C-12 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-366 — Phase 4:.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 206-239)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 205-238)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 107-162)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 233-265)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-367 — Phase B-pre splits into B-pre-a (gates B) + B-pre-b (gates D).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 50-50)

**Notes**:

Settled position C-13 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-368 — Phase C flag use_websocket_set_params=False default; 6 hard flip gates.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 65-65)

**Notes**:

Settled position C-28 from R3-03 table; cross-round consensus consolidation

### JR-ML-ARCH-369 — PROTO-01: Canopy `/ws/control` Accepts `reset` Parameter Not in Cascor Protocol.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5252-5266)

### JR-DCL-ARCH-002 — Refactor client.py to import from constants.py module (~25 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 38-41)

**Detail**:

client.py contains ~25 hardcoded values (base URL, endpoints, pool config, status codes) that must be
migrated to constants.py. This refactor depends on dcl-010 (creation of constants.py).

### JR-DCL-ARCH-003 — Refactor testing/fake_client.py to import from constants.py (~20 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 42-45)

**Detail**:

testing/fake_client.py contains ~20 hardcoded values (URLs, training defaults, worker data) that must be
migrated to constants.py. Depends on dcl-010.

### JR-DCL-ARCH-004 — Refactor testing/generators.py to import from constants.py (~30 replacements).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-49)

**Detail**:

testing/generators.py contains ~30 hardcoded values (math constants, dataset defaults) for spiral, xor,
circle, and moon generators that must be migrated to constants.py. Depends on dcl-010.

### JR-CAN-ARCH-007 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

### JR-CAS-ARCH-005 — Remove direct absolute path hardcoding that breaks on non-development machines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 142-146)

**Notes**:

Use relative paths or environment-relative configuration.

### JR-ML-ARCH-370 — Remove module-level sys.path.append in cascade_correlation.py:69.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3600-3610)

**Detail**:

CLN-CC-13: sys.path manipulation at module level in cascade_correlation.py:69
is an anti-pattern. Refactor to use proper imports or package structure.

### JR-CAN-ARCH-008 — Remove or deprecate legacy TrainingMetricsComponent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 163-163)

**Detail**:

Issue 3.2.4: TrainingMetricsComponent appears unused. Verify no references
and remove, or document deprecation plan and mark with DeprecationWarning.

### JR-CAN-ARCH-009 — Remove orphaned candidate callbacks from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 161-161)

**Detail**:

Issue 3.2.2: Callbacks in MetricsPanel that reference removed candidate display.
Remove or reconnect to active candidate pool UI.

### JR-CAS-ARCH-006 — Replace Path truthiness checks with explicit None checks.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 394-398)

**Detail**:

Path objects are always truthy even for empty strings. Use 'if x is None' instead of 'or' fallback patterns (lines 3015, 3096, 471).

### JR-ML-ARCH-371 — RISK: Correctness: no seq gaps.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 147-148)

### JR-ML-ARCH-372 — RISK: Correctness: no state loss.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 148-149)

### JR-ML-ARCH-373 — RISK: Criterion.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 143-144)

### JR-ML-ARCH-374 — RISK: Observability: full pipe.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 149-150)

### JR-ML-ARCH-375 — RISK: **P0: polling eliminated**.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 145-146)

### JR-ML-ARCH-376 — RISK: Recovery: kill switches work.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 150-151)

### JR-ML-ARCH-377 — RISK: Security: CSWSH closed.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/R5-01_canonical_development_plan.md` (lines 146-147)

### JR-ML-ARCH-378 — ROBUST-01: Dummy Candidate Results on Double Training Failure — Silent Corruption.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4574-4597)

### JR-ML-ARCH-379 — TQ-01: 10+ Tests with No Assertions (cascor).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4775-4786)

### JR-ML-ARCH-380 — TQ-02: 149 `time.sleep` Calls in canopy Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4789-4800)

### JR-ML-ARCH-381 — TQ-03: Worker Config Validation Tests with No Assertions.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4803-4814)

### JR-ML-ARCH-382 — TQ-04: 139 `hasattr` Guards in cascor Tests.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4817-4821)

### JR-ML-ARCH-383 — TQ-05: 10 Unit Tests Import httpx (Integration-Level).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 4824-4835)

### JR-ML-ARCH-384 — XREPO-01: Generator Name `"circle"` vs Server's `"circles"`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2509-2524)

### JR-ML-ARCH-385 — XREPO-02: 503 Not in `RETRYABLE_STATUS_CODES`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2571-2586)

### JR-ML-ARCH-386 — XREPO-03: No `FakeCascorControlStream` — Testing Gap for WS Control.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2589-2604)

### JR-ML-ARCH-387 — XREPO-04: Protocol Constants Alignment Is Manual.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2607-2629)

### JR-ML-ARCH-388 — XREPO-05: State Name Inconsistency — UPPERCASE vs Title-Case vs FSM Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2632-2646)

### JR-ML-ARCH-389 — XREPO-06: `epochs_max` Default Discrepancy.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2649-2663)

### JR-ML-ARCH-390 — XREPO-07: `command()` vs `set_params()` Message Format Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2666-2681)

### JR-ML-ARCH-391 — XREPO-08: Three Distinct WS Message Formats.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2684-2692)

### JR-ML-ARCH-392 — XREPO-09: Client `create_dataset()` Missing `tags` and `ttl_seconds`.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2695-2709)

### JR-ML-ARCH-393 — XREPO-10: `FakeDataClient` Metadata Schema Diverges from Real Server.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2712-2726)

### JR-ML-ARCH-394 — XREPO-11: Client Retries Non-Idempotent Mutations (POST, DELETE).

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2729-2743)

### JR-ML-ARCH-395 — XREPO-12: `y` Tensor Received but Never Used in Worker.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2746-2760)

### JR-ML-ARCH-396 — XREPO-13: Health Endpoint `status` Value Inconsistency.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2763-2771)

### JR-ML-ARCH-397 — XREPO-14: FakeClient State Constants Use Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2774-2789)

### JR-ML-ARCH-398 — XREPO-15: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2792-2800)

### JR-ML-ARCH-399 — XREPO-16: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2803-2818)

### JR-ML-ARCH-400 — XREPO-17: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 2821-2836)

### JR-CWK-ARCH-003 — v0.3.0 deprecations: CandidateTrainingWorker (legacy), --api-key CLI flag, CASCOR_API_KEY env var; migrate to CascorWorkerAgent and --auth-token before next major release.

**Status**: shipped  **Priority**: P3  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 113-122)

**Detail**:

CandidateTrainingWorker (legacy): use --legacy to opt in; emits DeprecationWarning. --api-key CLI flag (old flag still parsed, deprecated). CASCOR_API_KEY env var (old var still read as fallback, deprecated). Plan migration to CascorWorkerAgent and --auth-token before next major release.

### JR-DAT-ARCH-001 — IPC architecture (gRPC, message queue, shared memory, WebSocket) deferred until REST bottleneck or >100MB datasets.

**Status**: deferred  **Priority**: P3  **Category**: ARCH  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 438-465)

**Notes**:

RD-015 (DATA-018). Deferred. REST migration success reduced urgency.

### JR-CAN-ARCH-010 — Defer true IPC architecture (Cascor-Canopy process separation) to future when triggering conditions are met.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 407-433)

**Detail**:

Current architecture embeds CasCor within Canopy process. Deferral justified by RemoteWorkerClient and async training providing sufficient capability. Revisit if hard cancellation, multiple concurrent jobs, or remote clusters needed.

**Notes**:

Phase 4 deferred; has explicit trigger conditions

### JR-CAN-ARCH-011 — Environment variable parsing must fix boolean/integer precedence bug.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 228-228)

**Detail**:

Issue 5.1.2: _convert_type checks boolean before integer, causing "0"
to parse as False instead of 0. Reorder checks: int/float before bool.

### JR-CWK-ARCH-004 — Hardcoded values refactor implementation plan: Phase 1 create constants module, Phase 2 refactor source files, Phase 3 validate test suite and pre-commit, Phase 4 documentation update.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 1-80)

**Detail**:

Phase 1 (HIGH priority): Create constants.py (~30 constants in 7 sections), eliminate config duplication. Phase 2 (HIGH priority): Refactor worker.py (10 protocol strings), task_executor.py (12 training defaults/activation names), ws_connection.py (4 WebSocket strings), config.py (8 dataclass field defaults + 8 env var defaults), cli.py (4 argparse defaults). Phase 3 (HIGH priority): Run full pytest suite, run pre-commit hooks, verify protocol message type strings match cascor server. Phase 4 (MEDIUM priority): Update AGENTS.md, update CHANGELOG.md, create release description. Risk: protocol string mismatch with server (very low, mitigated by constants matching exact current strings + integration test); training defaults change behavior (very low, constants preserve exact values); config duplication elimination error (low, mitigated by unit test); import cycle (very low, constants.py has no imports from other worker modules).

### JR-CAN-ARCH-012 — Layout type sprint must forward positional/keyword parameters correctly.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 245-245)

**Detail**:

Issue 5.3.4: _layout_type_sprint helper loses parameters. Use *args, **kwargs
or explicit forwarding to preserve full signature.

### JR-ML-ARCH-401 — Phase 5:.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md` (lines 242-263)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md` (lines 241-262)
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 165-187)
- `juniper-ml/notes/regressions/CONSOLIDATED_DEVELOPMENT_ROADMAP.md` (lines 268-323)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_06_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_02_2026-04-02.md

---

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

---

From CONSOLIDATED_DEVELOPMENT_ROADMAP.md

*Merged from 4 extraction candidates (slices: 3b-3).*

### JR-ML-ARCH-402 — Phase 6:.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: ml

**Sources**:
- `juniper-ml/notes/regressions/REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md` (lines 190-220)

**Notes**:

From REGRESSION_DEVELOPMENT_ROADMAP_04_2026-04-02.md

### JR-CAN-ARCH-013 — Settings access must guard against KeyError or use default.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 242-242)

**Detail**:

Issue 5.3.1: config.key access can raise AttributeError. Use get() or
try/except to provide sensible defaults.

