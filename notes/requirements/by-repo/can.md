# Requirements — juniper-canopy (can)

**Total entries**: 114

**By status**: proposed=105 | shipped=9

**By priority**: P0=15 | P1=51 | P2=27 | P3=21

**By category**: TEST=24 | UI=20 | API=16 | ARCH=13 | OBS=11 | SEC=8 | DOC=7 | DEP=5 | LOCK=5 | PERF=3 | TRAIN=1 | WS=1

---

### JR-CAN-SEC-001 — API key validation must use hmac.compare_digest() to prevent timing attacks.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 43-43)

**Detail**:

Issue 0.1.2: Replace string 'in' operator with constant-time comparison.
File: src/security.py

### JR-CAN-SEC-002 — CallbackContextAdapter must be thread-safe via contextvars.ContextVar.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 50-50)

**Detail**:

Issue 0.2.1: Replace instance attributes with contextvars.ContextVar to ensure
thread isolation. File: src/frontend/callback_context.py

### JR-CAN-UI-001 — Canopy should not mutate incoming broadcast messages in websocket_manager.broadcast().

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 75-75)

**Detail**:

Issue 1.1.3: broadcast() currently mutates message dicts in-place. 
Must pass immutable copy or deep clone before modification.

### JR-CAN-UI-002 — Dataset-tab edits don't persist—Phase 1 cold-swap with Cancel button, Phase 2 live in-flight swap.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 38-42)

**Detail**:

Phase 1: add Cancel button, cold-swap via canopy adapter + cascor endpoint. 
Phase 2 (separate doc): live dataset swap behind experimental-functions gate, 
two-step warning modal, History/Snapshots/Replay persistence.

**PRs**: PR-7 (Phase 1, Issue, PR-series P2-1 to P2-7 (Phase 2 live swap, documented separately)

**Notes**:

See ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md for full Phase 2 spec.
Shares root cause with Issue #1.

### JR-CAN-SEC-003 — Exception handler must suppress internal details; log full stack server-side only.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 45-45)

**Detail**:

Issue 0.1.3: Return generic message to client, preserve full exception in
server-side logs only. Prevents information disclosure.

### JR-CAN-API-001 — Fix /ws exception handling infinite loop in main.py.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 73-73)

**Detail**:

Issue 1.1.1: WebSocket route exception handling loop. Must exit cleanly
on expected errors (client disconnect) without retry loop.
File: src/main.py

### JR-CAN-UI-003 — Fix metaparameter edits that silently drop 14 of 29 keys without reaching cascor backend.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Root causes: incomplete adapter mapping, no roundtrip verification. 
Three sub-parts: (C1) surface drops to user, (C2) extend cascor PATCH endpoints, 
(C3) roundtrip verification. Includes candidate-pool invariants atomic validation.

**PRs**: PR-1 (Phase 6A series, Issue

**Notes**:

Blocks Issue

### JR-CAN-API-002 — Fix metrics format mismatch: flatten nested dashboard metrics contract (metrics.loss, metrics.accuracy) to match service mode output.

**Status**: proposed  **Priority**: P0  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Dashboard reads nested metrics (metrics.loss, metrics.accuracy); service-mode adapter emits flat structure. Critical display blocker for metrics charts.

**Notes**:

P5-RC-01; critical display blocker; part of final synthesis

### JR-CAN-UI-004 — Fix network topology format mismatch: convert weight-oriented CasCor structure to graph-oriented visualizer contract.

**Status**: proposed  **Priority**: P0  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/development/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (lines 85-95)

**Detail**:

Service-mode emits weight-oriented topology (input_size, hidden_units: [...]) while visualizer expects graph-oriented structure (input_units, connections). Critical display blocker.

**Notes**:

P5-RC-02; critical display blocker; part of final synthesis

### JR-CAN-SEC-004 — Phase 0 Addendum—Add threading.Lock to TrainingStateMachine.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 258-260)

**Detail**:

HIGH-015: Thread-safe locking required in backend training state machine.
File: src/backend/training_state_machine.py

### JR-CAN-SEC-005 — Phase 0 Pre-Release Security Blockers (6 vulnerabilities).

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 30-61)

**Detail**:

0.1.1: Fix path traversal in snapshot endpoints via regex + resolve() check.
0.1.2: Fix timing attack in API key validation via hmac.compare_digest().
0.1.3: Suppress internal exception details; log server-side, return generic message.
0.1.4: Fix rate limiter memory leak with periodic eviction + size cap (10k entries).
0.2.1: Fix thread-unsafe CallbackContextAdapter via contextvars.ContextVar.
0.2.2: Fix threading.Event replacement race with clear() instead of reassign.

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

### JR-CAN-PERF-001 — Rate limiter must evict expired entries periodically to prevent memory leak.

**Status**: proposed  **Priority**: P0  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 47-49)

**Detail**:

Issue 0.1.4: Add _evict_expired() method with periodic cleanup.
Emergency size cap: 10,000 entries. File: src/security.py

### JR-CAN-TRAIN-001 — Single-iteration auto-pause after stop+reset due to cleared _pause_event.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 42-42)

**Detail**:

cascor lifecycle manager leaves _pause_event cleared after reset(). 
Fix: one-line change to clear+set instead of reassign.

**PRs**: PR-5 (cascor fix, ordered first in remediation)

### JR-CAN-SEC-006 — Threading.Event replacement race must use clear() instead of reassignment.

**Status**: proposed  **Priority**: P0  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 52-53)

**Detail**:

Issue 0.2.2: In demo_mode.py, use _stop.clear() instead of _stop = Event()
to avoid TOCTOU race. File: src/demo_mode.py

### JR-CAN-TEST-001 — Phase 1 Complete—Eliminated 9 false-positive assert True tests.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 18-24)

**Detail**:

Epic 1.1: Removed all assert True patterns from test_button_responsiveness.py,
test_button_state.py, and others. Epic 1.2: Moved 5 non-test files (test_yaml.py,
test_dashboard_init.py, etc.) to util/verify_*.py. Epic 1.3: Fixed security scan
suppression (removed || true from bandit, updated pip-audit to strict mode).

### JR-CAN-TEST-002 — Phase 2 Complete—Consolidated fixtures and enabled MyPy/linting on tests.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 25-30)

**Detail**:

Epic 2.1: Single source of truth for test fixtures. Epic 2.2: Re-enabled critical
MyPy error codes (arg-type, return-value, assignment). Epic 2.3: Enabled flake8
linting on test files with relaxed configuration.

### JR-CAN-TEST-003 — Phase 3 Complete—Fixed weak tests, unconditional skips, exception suppression.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 31-39)

**Detail**:

Epic 3.1: Reduced in [200, 503] permissive patterns from 21 to 5. Epic 3.2: Converted
9 unconditional skips to conditional with documentation (ADR-001). Epic 3.3: Fixed
5 exception suppression patterns. Epic 3.4: Re-enabled B905, F401, B008. Epic 3.5:
Removed duplicate test classes. Epic 3.6: Converted bug-documenting tests to xfail.

### JR-CAN-TEST-004 — Phase 4 Complete—Config standardization, docs, MyPy improvements, suppress review.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 40-45)

**Detail**:

Epic 4.1: Standardized coverage fail_under to 80%, re-enabled pytest warnings.
Epic 4.2: Enabled markdown linting, created TEST_DIRECTORY_STRUCTURE.md, fixed
docstrings. Epic 4.3: Re-enabled 9 MyPy codes (call-arg, override, no-redef, etc),
reduced disabled codes from 15 to 7. Epic 4.4: Reviewed contextlib.suppress patterns,
added clarifying comments.

### JR-CAN-UI-005 — Accuracy plot phase band logic must be deduplicated.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 93-93)

**Detail**:

Issue 1.3.3: Repeated phase-band visualization logic in metrics_panel.py.
Extract to shared helper. File: src/frontend/components/metrics_panel.py

### JR-CAN-TEST-005 — Add browser-automation UI test sub-suite with dedicated CI lane.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 45-46)

**Detail**:

No browser automation harness exists. Create pytest sub-suite with ≤5 min 
wall-clock budget via parallel jobs, caching, and slow marker. Skeleton 
in Phase 4 step 1, full coverage in Phase 4 step 2.

**PRs**: PR-4.1 (skeleton with basic page loads), {'PR-4.2 (full coverage': 'param Apply, dataset swap, snapshot restore)'}

### JR-CAN-TEST-006 — Add integration test suite for real CasCor backend code paths with mocked CascorIntegration.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 191-207)

**Detail**:

conftest.py forces CASCOR_DEMO_MODE=1 for all tests; no test exercises cascor_integration paths. Would have caught INT-CRIT-001/002/003.

**Notes**:

Phase 2 high priority; must test control, topology, metrics, statistics, decision boundary, snapshots

### JR-CAN-DOC-001 — Application version must be centralized via importlib.metadata.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 83-83)

**Detail**:

Issue 1.2.1: Version string currently duplicated across health, status, and
config endpoints. Use importlib.metadata as single source of truth.
File: src/main.py

### JR-CAN-TEST-007 — Bandit configuration must be consolidated to single file.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 121-121)

**Detail**:

Issue 2.2.1: Multiple bandit config files (.bandit, .pre-commit hook, CI).
Consolidate to .bandit and reference from all invocation points.

### JR-CAN-TEST-008 — Bandit invocations across all CI workflows must be consistent.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 122-122)

**Detail**:

Issue 2.2.2: bandit runs in pre-commit, CI, and manual invocations with
varying flags. Standardize command and flags across all paths.

### JR-CAN-API-004 — Canopy must enforce max_connections limit in WebSocketManager.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 74-74)

**Detail**:

Issue 1.1.2: Currently no enforcement of max_connections. Must track active
connection count and reject new clients when limit reached.

### JR-CAN-TEST-009 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

### JR-CAN-OBS-001 — ColoredFormatter must not mutate LogRecord during formatting.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 151-151)

**Detail**:

Issue 3.1.1: ColoredFormatter adds ANSI codes to LogRecord.msg in-place,
affecting file output. Clone record before mutation or use format string.

### JR-CAN-DOC-002 — Configuration must have no version string mismatches (app_config.yaml, pyproject.toml).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 84-86)

**Detail**:

Issues 1.2.2, 1.2.3: Update app_config.yaml version to 0.4.0 and pyproject.toml
header version comment to match. Should be single source via importlib.metadata.

### JR-CAN-API-005 — CORS configuration YAML syntax must be valid and documented.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 87-87)

**Detail**:

Issue 1.2.5: app_config.yaml CORS section has syntax errors. Validate and
document expected format. File: conf/app_config.yaml

### JR-CAN-SEC-007 — CORS must be restricted to used methods and headers only.

**Status**: proposed  **Priority**: P1  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 79-79)

**Detail**:

Issue 1.1.7: Currently allows all methods and headers. Restrict to
actual API usage (GET, POST, OPTIONS; only necessary headers). File: src/main.py

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

### JR-CAN-DEP-001 — Docker dependencies must be pinned via lockfile, not floating versions.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 128-128)

**Detail**:

Issue 2.3.2: Dockerfile uses floating versions (python:3.11, etc). Pin via
Dockerfile ARG or multi-stage from pinned base images.

### JR-CAN-DEP-002 — Docker log file handler must use append mode, not write mode.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 130-130)

**Detail**:

Issue 2.3.4: Log file handler configured with 'w' (write) instead of 'a'
(append). Causes log truncation on app restart. Use 'a' mode.

### JR-CAN-DEP-003 — Docker must have production configuration or documented env var overrides.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.1: Dockerfile currently dev-centric. Create Dockerfile.prod or
document production override env vars (API_BASE, CASCOR_HOST, etc).

### JR-CAN-DEP-004 — Docker service URLs must have correct defaults for health checks.

**Status**: proposed  **Priority**: P1  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 129-129)

**Detail**:

Issue 2.3.3: HEALTHCHECK instruction uses http://localhost:8000/health
but app may be configured differently. Use env vars or expose-port-agnostic probe.

### JR-CAN-API-008 — Fix CascorStateSync to read from correct response fields (data.state_machine, data.monitor).

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase_2/PHASE_2_UNIFIED_EXTERNAL_CASCOR_DEVELOPMENT_PLAN_v2.md` (lines 62-80)

**Detail**:

Sync reads data.state, data.epoch; real cascor has data.state_machine, data.monitor. Causes initial state hydration to fail.

**Notes**:

FIX-5; initial sync reads wrong keys

### JR-CAN-ARCH-001 — get_rate_limiter() must use get_settings() instead of direct access.

**Status**: proposed  **Priority**: P1  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 86-86)

**Detail**:

Issue 1.2.4: Inconsistent settings access pattern. Use get_settings() function
for uniform configuration retrieval. File: src/security.py

### JR-CAN-TEST-010 — GitHub Actions workflow must fix lockfile extras mismatch.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 113-113)

**Detail**:

Issue 2.1.1: .github/workflows/lockfile-update.yml extras specification
conflicts with pyproject.toml. Align definitions.

### JR-CAN-TEST-011 — GitHub publish workflow must add contents:read permission.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 114-114)

**Detail**:

Issue 2.1.2: .github/workflows/publish.yml missing minimal required
permissions. Add contents:read for artifact access.

### JR-CAN-OBS-002 — Health checks must use async probes instead of blocking network calls.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 155-155)

**Detail**:

Issue 3.1.5: Health endpoints currently block on cascor connectivity checks.
Use async probes or timeout guards to prevent cascor slowness from blocking
health endpoint response.

### JR-CAN-API-009 — Implement CascorIntegration.get_network_data() method to return network statistics.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 120-140)

**Detail**:

Method does not exist on CascorIntegration class; callers will receive AttributeError at runtime. Must return dict with keys: input_weights, hidden_weights, output_weights, hidden_biases, output_biases, threshold_function, optimizer.

**Notes**:

Network statistics tab fails when connected to real CasCor backend; blocking P1

### JR-CAN-UI-006 — Implement decision boundary visualization for real CasCor backend in Canopy dashboard.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 88-118)

**Detail**:

The /api/decision_boundary endpoint retrieves prediction function from cascor_integration but never computes the grid. Must implement grid computation mirroring demo mode logic.

**Notes**:

Dataset/Decision Boundary tab shows "No data available" when connected to real CasCor backend

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

### JR-CAN-OBS-003 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-CAN-API-012 — Middleware must handle malformed Content-Length header gracefully.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 78-78)

**Detail**:

Issue 1.1.6: Non-numeric or negative Content-Length can crash request parsing.
Add bounds check and return 400 Bad Request. File: src/middleware.py

### JR-CAN-TEST-012 — MyPy strict_optional setting conflict must be resolved.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 123-123)

**Detail**:

Issue 2.2.3: MyPy configuration has conflicting strict_optional directives
in different sections. Consolidate to single authoritative setting.

### JR-CAN-UI-007 — Network visualizer screenshot timestamp must not be static.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 92-92)

**Detail**:

Issue 1.3.2: Screenshot PNG contains hardcoded timestamp instead of actual
capture time. Must update on every screenshot. File: src/frontend/components/network_visualizer.py

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

### JR-CAN-TEST-013 — Phase 2 CI/CD Infrastructure Reliability (12 tasks).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 104-138)

**Detail**:

Step 2.1 (5 CI tasks): Fix lockfile extras, add permissions, fix pip-audit, 
define dev extra, add Codecov upload.
Step 2.2 (3 security tasks): Consolidate bandit config, standardize invocations,
fix mypy strict_optional conflict.
Step 2.3 (4 Docker tasks): Create prod config, pin deps via lockfile,
fix service URLs, change log handler to append mode.

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

### JR-CAN-DOC-003 — Phase 3 Code Quality & Observability (18 tasks).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 141-186)

**Detail**:

Step 3.1 (6 logging): Fix ColoredFormatter mutation, cache logger wrappers,
make Sentry sample rate configurable, normalize Prometheus labels, use async 
health checks, set production log levels.
Step 3.2 (5 dead code): Remove unused candidate pool display, orphaned callbacks,
extract create_empty_plot(), deprecate legacy TrainingMetricsComponent.
Step 3.3 (5 frontend): Extract colors to theme_constants, fix modulo toggle,
fix doc links, remove blocking time.sleep(), split NetworkVisualizer callback.
Step 3.4 (2 perf): Reduce API timeout, begin DashboardManager extraction.

### JR-CAN-TEST-014 — Phase 4 Addendum—6 test quality fixes (context suppression, schema tests, coverage gaps).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 279-287)

**Detail**:

4.3.1: Remove contextlib.suppress(Exception) from assertions (HIGH-016).
4.3.2: Add pytest.fail() guards to WebSocket schema tests (HIGH-017).
4.3.3: Remove hasattr guards from unit tests (HIGH-018).
4.3.4: Rewrite performance test without exception suppression (HIGH-019).
4.3.5: Add dedicated tests for parameters_panel.py (55.3% gap).
4.3.6: Expand candidate_metrics_panel.py callback tests (65.6% gap).

### JR-CAN-TEST-015 — pip-audit in CI must scan full dependency tree, not just top-level.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 115-115)

**Detail**:

Issue 2.1.3: pip-audit command in .github/workflows/ci.yml is incomplete.
Must specify report file and scan transitive dependencies.

### JR-CAN-OBS-004 — Production default log levels must prevent debug spam in production.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 156-156)

**Detail**:

Issue 3.1.6: Default log level may be too verbose in production. Set
production-safe default (INFO/WARNING) independent of dev config.

### JR-CAN-OBS-005 — Prometheus endpoint labels must be normalized to prevent cardinality explosion.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 154-154)

**Detail**:

Issue 3.1.4: Endpoint labels may include query params, causing unbounded cardinality.
Normalize to path template (e.g. /api/v1/params/{id} not /api/v1/params/123).

### JR-CAN-LOCK-001 — pyproject.toml must define 'dev' extra for dependency management.

**Status**: proposed  **Priority**: P1  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 116-116)

**Detail**:

Issue 2.1.4: Missing dev extra for development dependencies. Define
[project.optional-dependencies] with 'dev' key including test/lint tools.

### JR-CAN-API-015 — Remove duplicate cn_patience configuration parameter.

**Status**: proposed  **Priority**: P1  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 76-76)

**Detail**:

Issue 1.1.4: cn_patience appears twice in configuration. Consolidate to single
canonical definition. File: src/main.py

### JR-CAN-TEST-016 — Replace 8 always-passing assert True tests with real assertions using pytest.raises().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 86-98)

**Detail**:

Tests in performance and integration suites use assert True in both success and exception branches. Provides false confidence; regressions undetectable.

**Notes**:

Category A: 8 critical test issues; Phase 1 critical

### JR-CAN-UI-008 — Replace debounce=True with 350ms on numeric inputs to fix perceived typing lag.

**Status**: proposed  **Priority**: P1  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 365-499)

**Detail**:

Issue: spinner changes commit immediately but typed values require blur. 
Solution: use debounce=350ms for live feedback without callback churn. 
Also adds clientside blur-on-Apply and validation styling (invalid=True border).

**PRs**: PR-2 (Phase 6B, Issue

### JR-CAN-OBS-006 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

### JR-CAN-TEST-017 — Test Suite & CI/CD Enhancements (16 epics, 145 total hours).

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md`

**Detail**:

Phase 1 (21h): Eliminate false-positive tests (9 assert True), move non-test files,
fix security scan suppression.
Phase 2 (39h): Consolidate conftest.py, re-enable MyPy codes, enable linting on tests.
Phase 3 (50h): Fix weak tests, address unconditional skips, fix exception suppression,
re-enable flake8 checks, remove duplicate test classes, fix bug-documenting tests.
Phase 4 (35h): Configuration standardization, docs, future MyPy, extended suppress review.

### JR-CAN-UI-009 — Must support zero-copy metadata parameter updates between Canopy and Cascor.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 56-162)

**Detail**:

Candidate-pool invariants form a constrained triple (selected_candidates, 
top_candidates, random_candidates) that must be validated atomically in cascor.
Post-merge validation required for multi-key PATCH (e.g. {S: 6, T: 4, R: 2}).
Validation helper _validate_candidate_pool_triple() enforces 6 invariants.

**Notes**:

Shipped as part of Phase 6A remediation (Issue #1 / can-001 implementation).
Candidate-pool semantics confirmed 2026-05-09.

### JR-CAN-UI-010 — Phase 3 Wave 1—HDF5 snapshot capabilities (create, restore, history).

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 75-211)

**Detail**:

P3-1: Create new snapshot endpoint (POST /api/v1/snapshots) with auto-generated 
timestamp names and demo mode support. P3-2: Restore endpoint with training state 
validation and WebSocket broadcast. P3-3: History tracking (append-only JSONL log).
Status: all complete as of 2026-01-10.

### JR-CAN-UI-011 — Phase 3 Wave 2—Training Metrics Save/Load layouts and 3D topology visualization.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 402-599)

**Detail**:

P3-4: Save/load metric panel configuration as named presets (GET/POST/DELETE 
/api/v1/metrics/layouts endpoints). P3-5: Toggle 2D/3D network topology view 
with layer-based z-axis, circular layout for >4 hidden nodes, weight-based edge coloring.

**PRs**: {'PR-series': 'Wave 2 (37 new tests, coverage maintained 93%+)'}

### JR-CAN-OBS-007 — Phase 3 Wave 3—Redis and Cassandra cluster monitoring tabs.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 604-897)

**Detail**:

P3-6: Redis monitoring (health badge, memory/ops/hit-rate metrics, auto-refresh). 
P3-7: Cassandra cluster overview (contact points, hosts table, keyspace/table metrics). 
Both integrate new backend clients (redis_client.py, cassandra_client.py), 
optional integration with soft-fail on missing libraries.

**PRs**: {'PR-series': 'Wave 3 (93 new tests, 640+ total for Phase 3)'}

### JR-CAN-UI-012 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-CAN-UI-013 — About panel documentation links must be validated and repaired.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 170-170)

**Detail**:

Issue 3.3.3: Broken or outdated documentation links in About panel.
Audit all links and update URLs or remove invalid references.

### JR-CAN-TEST-018 — Add integration tests for async/sync boundary with WebSocket responsiveness during training.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 168-189)

**Detail**:

No integration tests verify WebSocket responsiveness during active training; schedule_broadcast() uses run_coroutine_threadsafe but has no tests.

**Notes**:

Phase 2 high priority; training callbacks are registered but untested in integration context

### JR-CAN-PERF-002 — API timeout must be reduced for fast-interval callbacks.

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 176-176)

**Detail**:

Issue 3.4.1: Default API timeout too long for frequently-polled endpoints.
Set shorter timeout (2-5s) for metrics/state endpoints, keep longer (10s) for
heavy operations like dataset upload.

### JR-CAN-UI-014 — Canopy must use explicit blur-on-Apply to force pending debounced values to commit.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 456-475)

**Detail**:

Clientside callback that blurs active element on Apply button click.
Removes entire class of apply-with-stale-value races where fast typists
submit before debounce commits value. ~10 lines of JS.

**Notes**:

Part of Issue

### JR-CAN-API-016 — Configure JuniperData client integration with JUNIPER_DATA_URL and docker-compose entry.

**Status**: proposed  **Priority**: P2  **Category**: API  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 209-232)

**Detail**:

JUNIPER_DATA_URL not in app_config.yaml; no docker-compose entry; no E2E test with live JuniperData service.

**Notes**:

Phase 2 high priority; client exists in Phase 4 deliverable but is not actively integrated

### JR-CAN-TEST-019 — Consolidate duplicate conftest.py fixtures into single configuration file.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 122-128)

**Detail**:

Two conftest.py files (445 + 224 lines) contain overlapping fixtures. Consolidate to avoid duplication and maintenance burden.

**Notes**:

Category D: Duplicate fixtures; DRY principle violation

### JR-CAN-ARCH-004 — DashboardManager must be refactored for extract to <2000 lines.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 177-177)

**Detail**:

Issue 3.4.2: DashboardManager is monolithic. Begin extraction of sidebar,
controls, stores, and theme logic into separate modules. Post-refactor target: <2000 lines.

### JR-CAN-ARCH-005 — Extract create_empty_plot() as shared utility across metric panels.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 162-162)

**Detail**:

Issue 3.2.3: create_empty_plot logic duplicated in multiple components.
Extract to plot_utils.py or equivalent shared module.

### JR-CAN-UI-015 — Hardcoded colors must be extracted to theme_constants.py for DRY.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 168-168)

**Detail**:

Issue 3.3.1: Color strings repeated across components. Extract to
theme_constants.py for centralized management and dark/light theme support.

### JR-CAN-UI-016 — Modulo toggle for theme switching must use Dash State, not module-level flag.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 169-169)

**Detail**:

Issue 3.3.2: Theme toggle using module-level variable instead of callback State.
Can cause race conditions in multi-user scenarios. Use dcc.Store for theme state.

### JR-CAN-TEST-020 — Move 5 non-test files (scripts, manual verifiers) out of test directory to util/.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 99-108)

**Detail**:

Files like test_yaml.py, test_dashboard_init.py are print-based scripts with no assertions. Should be moved to util/ for clarity.

**Notes**:

Category B: 5 files; Phase 1 high priority

### JR-CAN-ARCH-006 — NetworkVisualizer callback is overloaded and must be split.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 172-172)

**Detail**:

Issue 3.3.5: Single callback handles too many inputs. Split into separate
callbacks for layout changes, theme changes, and data updates.

### JR-CAN-UI-017 — Numeric inputs must use validation styling (red border) for out-of-range values.

**Status**: proposed  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 478-499)

**Detail**:

dbc.Input invalid=True property shows red border. Add pattern-matching callback
that watches min/max bounds and sets invalid flag on value change. Provides
immediate feedback without requiring Apply-button interaction.

**Notes**:

Part of Issue

### JR-CAN-PERF-003 — Parameter retry logic must not use blocking time.sleep().

**Status**: proposed  **Priority**: P2  **Category**: PERF  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 171-171)

**Detail**:

Issue 3.3.4: Blocking sleep in parameter retry callback blocks event loop.
Use asyncio.sleep() or defer via callback scheduling instead.

### JR-CAN-TEST-021 — Phase 4 Test Coverage Expansion (14 tasks).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 189-214)

**Detail**:

Step 4.1 (4 gap fills): Test discovery, observability (Prometheus/Sentry),
secrets_util (SOPS paths), middleware edge cases (malformed headers).
Step 4.2 (4 new types): Security tests (auth, injection, CORS), WebSocket load,
circuit breaker resilience, API contract validation.

### JR-CAN-DOC-004 — Phase 5 Housekeeping (19 low-priority tasks across config, logging, CI/CD).

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 218-255)

**Detail**:

5.1 (5 config): Deprecation warnings, boolean/int precedence, env var migration,
Black target-version, CPU-only conda env.
5.2 (4 logging): Capture call site, timezone-aware timestamps, replace print(),
resolve FATAL_LEVEL conflict.
5.3 (6 code): AttributeError fix, message size check, exception type narrowing,
parameter forwarding, hit_rate format verification, theme-aware colors.
5.4 (4 CI/CD): Docker health check, shellcheck severity, pre-commit autoupdate,
codecov docs.

### JR-CAN-TEST-022 — Re-enable MyPy error codes currently disabled (15 codes); fix underlying type issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 160-165)

**Detail**:

.pre-commit-config.yaml disables 15 MyPy error codes, reducing type checking effectiveness. Phase 2 work to fix underlying issues, then re-enable codes.

**Notes**:

Category H: 15 codes disabled; type safety issue

### JR-CAN-DOC-005 — Remove commented-out imports across codebase.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 164-164)

**Detail**:

Issue 3.2.5: Commented imports clutter code. Remove or restore with rationale.

### JR-CAN-ARCH-007 — Remove dead _create_candidate_pool_display from MetricsPanel.

**Status**: proposed  **Priority**: P2  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 160-160)

**Detail**:

Issue 3.2.1: Dead code left in MetricsPanel. Remove or document why retained.
File: src/frontend/components/metrics_panel.py

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

### JR-CAN-TEST-023 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

### JR-CAN-DOC-006 — Add deprecation warnings to remaining legacy env validators.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 227-227)

**Detail**:

Issue 5.1.1: Legacy env var validators need deprecation warnings.
Use warnings.warn() to alert users of upcoming removal.

### JR-CAN-OBS-008 — All print() statements must be replaced with logger.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 237-237)

**Detail**:

Issue 5.2.3: print() bypasses logging config. Replace with appropriate
logger.info/debug/warning calls throughout codebase.

### JR-CAN-LOCK-002 — Black code formatter must have py314 in target-version.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 230-230)

**Detail**:

Issue 5.1.4: pyproject.toml Black config needs py314 for Python 3.14 compatibility.
Add to target-version list.

### JR-CAN-LOCK-003 — CASCOR_SNAPSHOT_DIR env var must be migrated to JUNIPER_CANOPY_SNAPSHOT_DIR.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 229-229)

**Detail**:

Issue 5.1.3: Old env var still referenced. Support both for compatibility
but document migration path and plan removal date.

### JR-CAN-DOC-007 — Codecov build count assumption must be documented.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 254-254)

**Detail**:

Issue 5.4.4: Codecov configuration makes implicit assumptions about build
frequency. Document in README or config comments what build count limit is
set to and why.

### JR-CAN-LOCK-004 — CPU-only conda environment must be created for deployment without CUDA.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 231-231)

**Detail**:

Issue 5.1.5: Current environment assumes CUDA. Create environment-cpu.yml
with PyTorch CPU variant and document usage.

### JR-CAN-ARCH-010 — Defer true IPC architecture (Cascor-Canopy process separation) to future when triggering conditions are met.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 407-433)

**Detail**:

Current architecture embeds CasCor within Canopy process. Deferral justified by RemoteWorkerClient and async training providing sufficient capability. Revisit if hard cancellation, multiple concurrent jobs, or remote clusters needed.

**Notes**:

Phase 4 deferred; has explicit trigger conditions

### JR-CAN-DEP-005 — Docker health check should consider curl-based approach.

**Status**: proposed  **Priority**: P3  **Category**: DEP  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 251-251)

**Detail**:

Issue 5.4.1: Current health check may not be reliable. Consider switch to
curl-based probe (add curl to base image) for more flexible checks.

### JR-CAN-ARCH-011 — Environment variable parsing must fix boolean/integer precedence bug.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 228-228)

**Detail**:

Issue 5.1.2: _convert_type checks boolean before integer, causing "0"
to parse as False instead of 0. Reorder checks: int/float before bool.

### JR-CAN-SEC-008 — Exception handling in callback_context must narrow exception types.

**Status**: proposed  **Priority**: P3  **Category**: SEC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 244-244)

**Detail**:

Issue 5.3.3: Bare except: clause catches SystemExit/KeyboardInterrupt.
Narrow to (ValueError, AttributeError, ...); let system signals propagate.

### JR-CAN-OBS-009 — FATAL_LEVEL constant conflict must be resolved.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 238-238)

**Detail**:

Issue 5.2.4: FATAL_LEVEL defined in multiple modules with different values.
Consolidate to single definition in logging module.

### JR-CAN-UI-018 — Header title color must be theme-aware (not hardcoded).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 247-247)

**Detail**:

Issue 5.3.6: Header title color hardcoded to light theme. Use theme-aware
color from theme_constants.py for dark/light mode support.

### JR-CAN-UI-019 — Hit rate formatter must verify percentage contract (0.0-1.0 range).

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 246-246)

**Detail**:

Issue 5.3.5: _format_hit_rate may receive values outside [0, 1]. Add bounds
check and either clamp or raise error depending on usage context.

### JR-CAN-ARCH-012 — Layout type sprint must forward positional/keyword parameters correctly.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 245-245)

**Detail**:

Issue 5.3.4: _layout_type_sprint helper loses parameters. Use *args, **kwargs
or explicit forwarding to preserve full signature.

### JR-CAN-UI-020 — Left sidebar too wide on Training Metrics tab—use per-tab width from ui_standards.

**Status**: proposed  **Priority**: P3  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 46-46)

**Detail**:

Hardcoded dbc.Col(width=3) for all tabs. Move to per-tab config via 
ui_standards.py. Seeds UI_STANDARDS.md documentation.

**PRs**: PR-6 (cosmetic sidebar width), PR-6.5 (UI_STANDARDS doc + Training-Metrics narrowing experiment)

### JR-CAN-OBS-010 — Log timestamps must be timezone-aware (UTC).

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 236-236)

**Detail**:

Issue 5.2.2: Naive timestamps can cause ambiguity in distributed logs.
Use datetime.now(timezone.utc) or equivalent.

### JR-CAN-OBS-011 — Logger must capture real call site instead of logger.py:line-N.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 235-235)

**Detail**:

Issue 5.2.1: _log_with_context wrapper causes all logs to appear from
logger.py instead of actual call site. Use inspect.stack() to get caller.

### JR-CAN-LOCK-005 — Pre-commit hook suite must be auto-updated.

**Status**: proposed  **Priority**: P3  **Category**: LOCK  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 253-253)

**Detail**:

Issue 5.4.3: pre-commit hooks may be outdated. Run `pre-commit autoupdate`
to refresh all hook versions and update .pre-commit-config.yaml.

### JR-CAN-ARCH-013 — Settings access must guard against KeyError or use default.

**Status**: proposed  **Priority**: P3  **Category**: ARCH  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 242-242)

**Detail**:

Issue 5.3.1: config.key access can raise AttributeError. Use get() or
try/except to provide sensible defaults.

### JR-CAN-TEST-024 — Shellcheck severity level should align with ecosystem convention.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 252-252)

**Detail**:

Issue 5.4.2: Current shellcheck invocation uses non-standard severity flag.
Align to standard shellcheck options.

### JR-CAN-WS-001 — Training WebSocket must validate message size to prevent DoS.

**Status**: proposed  **Priority**: P3  **Category**: WS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 243-243)

**Detail**:

Issue 5.3.2: WebSocket message handler does not check message size.
Add check: reject messages > 1MB with log and graceful disconnect.

