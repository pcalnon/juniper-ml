# Requirements — API

**Area**: API contracts — schemas, versioning, compatibility, migrations

**Total entries**: 56

**By status**: proposed=44 | shipped=12

**By priority**: P0=3 | P1=29 | P2=24

**By owner**: ml=26 | can=16 | dat=6 | cas=4 | ccl=4

---

### JR-CAN-API-001 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

### JR-CAN-API-002 — Fix metrics format mismatch: flatten nested dashboard metrics contract (metrics.loss, metrics.accuracy) to match service mode output.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Dashboard reads nested metrics (metrics.loss, metrics.accuracy); service-mode adapter emits flat structure. Critical display blocker for metrics charts.

**Notes**:

P5-RC-01; critical display blocker; part of final synthesis

### JR-CAN-API-003 — Phase 1 Release-Critical Quality (15 tasks across API, config, frontend).

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 64-101)

**Detail**:

Step 1.1 (7 tasks): Fix /ws exception loop, enforce max_connections, stop 
broadcast() mutation, remove duplicate cn_patience, define set_params Pydantic model, 
handle malformed Content-Length, restrict CORS.
Step 1.2 (5 tasks): Centralize version, update app_config.yaml/pyproject.toml headers,
use get_settings() in get_rate_limiter(), fix CORS YAML syntax.
Step 1.3 (3 tasks): Replace _api_url() with settings-based, fix screenshot timestamp,
deduplicate accuracy plot logic.

### JR-DAT-API-001 — All consumers (juniper-cascor, JuniperCanopy) reference juniper-data-client from PyPI (>=0.3.0), not vendored copies.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 333-349)

**Notes**:

RD-011 complete 2026-02-21. Vendored copies removed from all consumers.

### JR-CAS-API-001 — Build FastAPI service layer for CasCor with REST endpoints and WebSocket streaming.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 728-735)

**Detail**:

Add 19 REST endpoints across 6 route files; WebSocket endpoints for real-time training streaming (/ws/training, /ws/control); TrainingLifecycleManager with thread-safe state machine and ThreadPoolExecutor; service entry point (server.py) alongside existing CLI (main.py).

### JR-DAT-API-002 — Client package juniper-data-client published to PyPI (>=0.3.0) with Trusted Publishing OIDC.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 313-330)

**Notes**:

RD-010 complete 2026-02-20. Standalone repo pcalnon/juniper-data-client. 41 tests, 96% coverage.

### JR-DAT-API-003 — Health check endpoints distinguish liveness (/v1/health/live) and readiness (/v1/health/ready).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 186-207)

**Notes**:

DATA-007 complete. 4 integration tests added.

### JR-CCL-API-001 — Implement dataset retrieval method: get_dataset_data() via GET /v1/dataset/data.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 45-48)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-002 — Implement remote worker monitoring methods: list_workers(), get_worker(worker_id), get_worker_stats().

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 28-35)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-003 — Implement snapshot management methods: list_snapshots(), get_snapshot(snapshot_id), save_snapshot(), load_snapshot(snapshot_id).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 36-44)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-API-004 — Implement update_params() client method for runtime training parameter updates via PATCH /v1/training/params.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 28-33)

**Detail**:

Add update_params() method to JuniperCascorClient with supporting _patch() helper and PATCH method in ALLOWED_METHODS.
Tests required for both real client (responses mock) and fake client.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-DAT-API-004 — NPZ artifact schema documented with 6 keys (X_train, y_train, X_test, y_test, X_full, y_full) as float32 one-hot.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

DATA-010 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-DAT-API-005 — Parameter validation parity with consumer projects via AliasChoices and Pydantic.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 295-300)

**Notes**:

DATA-011 complete.

### JR-ML-API-001 — /api/v1/training/status returns snapshot_seq + server_instance_id atomically.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 117-117)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-API-002 — All WebSocket message envelopes must include optional seq field and preserve backward compatibility.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 194-240)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 262-282)

**Detail**:

Message builders add optional seq: int | None = None parameter.
seq serializes as top-level field when present; omitted when None (backward compat).
Every message type (state, metrics, topology, etc.) flows through _assign_seq_and_append.
Cascade client that does not understand seq field must still function (field is optional in parsers).

**Notes**:

Phase A-server (Day 2). Backward compatibility non-negotiable. Unknown fields must be ignored per schema.

### JR-CAN-API-004 — Canopy must enforce max_connections limit in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 74-74)

**Detail**:

Issue 1.1.2: Currently no enforcement of max_connections. Must track active
connection count and reject new clients when limit reached.

### JR-CAS-API-002 — CasCor backend must expose prediction method accepting arbitrary input grids for visualization.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 687-691)

**Notes**:

Required for JuniperCanopy decision boundary visualization.

### JR-CAS-API-003 — CasCor service must expose REST endpoints for snapshot save/load with full training state.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 701-705)

**Detail**:

REST endpoints must capture network weights, optimizer state, and training metadata via PyTorch state_dict() or equivalent.

### JR-CAN-API-005 — CORS configuration YAML syntax must be valid and documented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 87-87)

**Detail**:

Issue 1.2.5: app_config.yaml CORS section has syntax errors. Validate and
document expected format. File: conf/app_config.yaml

### JR-CAN-API-006 — DashboardManager must construct API URLs via settings, not ad-hoc _api_url().

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 91-91)

**Detail**:

Issue 1.3.1: _api_url() helper is error-prone and inconsistent. Replace all
callsites with settings-based URL construction. File: src/frontend/dashboard_manager.py

### JR-CAN-API-007 — Define Pydantic model for set_params endpoint request body.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 77-77)

**Detail**:

Issue 1.1.5: set_params endpoint lacks formal request schema. Add Pydantic
model for validation. File: src/main.py. Updates OpenAPI documentation.

### JR-CAN-API-008 — Fix CascorStateSync to read from correct response fields (data.state_machine, data.monitor).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

Sync reads data.state, data.epoch; real cascor has data.state_machine, data.monitor. Causes initial state hydration to fail.

**Notes**:

FIX-5; initial sync reads wrong keys

### JR-CAN-API-009 — Implement CascorIntegration.get_network_data() method to return network statistics.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 120-140)

**Detail**:

Method does not exist on CascorIntegration class; callers will receive AttributeError at runtime. Must return dict with keys: input_weights, hidden_weights, output_weights, hidden_biases, output_biases, threshold_function, optimizer.

**Notes**:

Network statistics tab fails when connected to real CasCor backend; blocking P1

### JR-CAN-API-010 — Implement real backend control for Canopy WebSocket endpoint when connected to live CasCor backend.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 55-85)

**Detail**:

The /ws/control endpoint currently rejects all commands when cascor_integration is active with a hardcoded error. Must implement command routing to CascorIntegration methods (start, stop, pause, resume, reset) and add state broadcasting after each command execution.

**Notes**:

Part of Phase 1 critical integration blockers; blocking all real-backend WebSocket control

### JR-CAN-API-011 — Implement save_snapshot() and load_snapshot() methods on CascorIntegration class.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 146-166)

**Detail**:

Methods do not exist; code falls through to minimal HDF5 fallback that only stores metadata, not network state. Must delegate to CasCor's CascadeHDF5Serializer.

**Notes**:

Snapshot save/load in real backend mode produces incomplete snapshots

### JR-CAN-API-012 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

### JR-CAN-API-013 — Normalize case-sensitivity for status and phase fields: ensure consistent handling of uppercase values from backends.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 102-116)

**Detail**:

Relay path at cascor_service_adapter.py:222 lacks .lower(); sync path at state_sync.py:70 has it. Asymmetric protection. FakeCascorClient uses uppercase, triggering bug in tests. Future backends may pass uppercase.

**Notes**:

P5-RC-03; retained as HIGH latent bug; defensive measure for future backends

### JR-CAN-API-014 — Normalize ServiceTrainingMonitor to use unwrapped response format for real cascor integration.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

_ServiceTrainingMonitor reads raw JuniperCascorClient responses without calling _unwrap_response(). Must normalize via single boundary in CascorServiceAdapter. Fixes FIX-1,2,3.

**Notes**:

Systemic root cause; affects metrics, is_training flag, response shape

### JR-ML-API-003 — Reconnect protocol must handle resume frames within 5s timeout and emit resume_ok or resume_failed response.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 420-490)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 389-412)

**Detail**:

training_stream handler: await asyncio.wait_for(ws.receive_json(), timeout=5.0) for optional first frame.
If type=="resume": check server_instance_id, call replay_since(), emit resume_ok + replayed OR resume_failed.
Failure reasons: server_restarted (instance mismatch), out_of_range (seq too old), malformed_resume (missing fields).
If first frame is not resume or timeout: treat as fresh client, route through normal handler.
Promote to active only after resume handling completes.

**Notes**:

Phase A-server (Day 3). R0-03 §6.1 "initial_status race" documented in code comment. Scenarios in §8.

### JR-CAN-API-015 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

### JR-ML-API-004 — Server must advertise server_instance_id (UUID) in connection_established and snapshot_seq in status endpoint.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R1-03_maximalist_comprehensive.md` (lines 392-410)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 283-299)

**Detail**:

connection_established frame (sent via send_personal_message, bypassing replay buffer) includes server_instance_id, server_start_time, replay_buffer_capacity.
/api/v1/training/status endpoint adds atomic snapshot under _seq_lock: payload["snapshot_seq"] = manager._next_seq - 1.
Also advertise server_instance_id in status endpoint.
Client uses server_instance_id to detect server restarts and reject out-of-date resume attempts.

**Notes**:

Phase A-server (Days 2-3). Atomicity of snapshot_seq with state read is load-bearing (Day 3 commit 6).

### JR-ML-API-005 — SetParamsResponse wire model with extra=allow.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 224-224)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-ML-API-006 — _normalize_metric dual-format contract (flat + nested) preserved forever.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 59-59)

**Notes**:

Settled position C-22 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-007 — REST endpoints preserved FOREVER: /api/metrics/history, /api/train/*, /api/v1/training/params, /api/topology.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 60-60)

**Notes**:

Settled position C-23 from R3-03 table; cross-round consensus consolidation

### JR-ML-API-008 — 10. Phase 7: Validation and Finalization.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 232-233)

### JR-ML-API-009 — 2. Plan Overview.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 21-22)

### JR-ML-API-010 — 3. Phase 0: Prior Art Assessment.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 60-61)

### JR-ML-API-011 — 4. Phase 1: Codebase Exploration and Discovery.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 85-86)

### JR-ML-API-012 — 5. Phase 2: Deep-Dive API and Model Analysis.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 116-117)

### JR-ML-API-013 — 6. Phase 3: Interface Contract Mapping.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 133-134)

### JR-ML-API-014 — 7. Phase 4: Discrepancy Identification.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 150-151)

### JR-ML-API-015 — 8. Phase 5: Comprehensive Documentation.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 177-178)

### JR-ML-API-016 — 9. Phase 6: Remediation Planning.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_REVIEW_PLAN_2026-04-08.md` (lines 206-207)

### JR-DAT-API-006 — API versioning strategy defines version increment, backward-incompatibility, deprecation policy (2 minor versions notice, 6 months support).

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 245-265)

**Notes**:

DATA-009 complete. Documented in docs/api/JUNIPER_DATA_API.md.

### JR-ML-API-017 — API-01: Health `status` Value Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5133-5148)

### JR-ML-API-018 — API-02: Health Response Schema Diverges.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5151-5165)

### JR-ML-API-019 — API-03: Canopy FSM Lacks Auto-Reset from FAILED/COMPLETED on START.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5168-5182)

### JR-ML-API-020 — API-04: FakeClient State Constants Different Vocabulary.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5185-5189)

### JR-ML-API-021 — API-05: Error Response Format Inconsistent.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5192-5207)

### JR-ML-API-022 — API-06: `candidate_progress` WS Message Not in Client Constants.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5210-5214)

### JR-ML-API-023 — API-07: Client Missing Methods for 4 Server Endpoints.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5217-5221)

### JR-ML-API-024 — API-08: `set_params` Includes Extraneous `type:command` Field.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5224-5232)

### JR-ML-API-025 — API-09: HTTPException Errors Bypass ResponseEnvelope.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 5235-5249)

### JR-CAS-API-004 — CasCor service API must support separate network_epochs and candidate_epochs parameters.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 562-566)

**Notes**:

Requires API contract extension; juniper-cascor-client start_training() method update.

### JR-CAN-API-016 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-ML-API-026 — Wire-format rollout is strictly additive; no field renamed/retyped/removed.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 77-77)

**Notes**:

Settled position C-40 from R3-03 table; cross-round consensus consolidation

