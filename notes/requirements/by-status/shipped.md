# Requirements — status: shipped

**Total entries**: 99

**By priority**: P0=29 | P1=53 | P2=16 | P3=1

**By category**: TRAIN=22 | TEST=16 | API=12 | OBS=8 | SEC=7 | DOC=6 | ARCH=6 | TOOL=5 | LOCK=4 | DATA=4 | UI=4 | OPS=2 | DEP=2 | WS=1

**By owner**: cas=24 | dat=24 | ccl=14 | ml=13 | cwk=12 | can=9 | dep=2 | dcl=1

---

### JR-CAS-LOCK-001 — Add missing PyYAML, h5py, pytest-cov, psutil dependencies to conda environment.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 256-306)

### JR-DAT-DATA-001 — All 7 storage backends implemented and tested: memory, localfs, cached, redis, hf, postgres, kaggle.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-015 complete. All implementations present.

### JR-DAT-DATA-002 — All 8 generators registered in GENERATOR_REGISTRY: spiral, xor, gaussian, circles, checkerboard, csv_import, mnist, arc_agi.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP_2026-02-17.md` (lines 29-32)

**Notes**:

Status verified as shipped. All 8 confirmed in api/routes/generators.py. RD-001.

### JR-DAT-SEC-001 — API security includes APIKeyAuth authentication and RateLimiter middleware as default behaviors.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-017 complete. security.py confirmed.

### JR-DAT-TEST-001 — Code coverage 99.40% aggregate with 85% per-module minimum enforced in CI.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 165-173)

**Notes**:

RD-005 and RD-007 complete 2026-02-24. 659 tests, 51 modules all >=85%. Reverted to 80% per 2026-03-15 audit.

### JR-DAT-LOCK-001 — Dependabot configuration at .github/dependabot.yml with weekly schedule, grouped updates, PR limits.

**Status**: shipped  **Priority**: P0  **Category**: LOCK  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 242-323)

**Notes**:

RD-002 complete during migration 2026-02-21. File present, 3 dependabot PRs open.

### JR-CAS-DOC-001 — Document that CascadeCorrelationNetwork is not thread-safe.

**Status**: shipped  **Priority**: P0  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 183-198)

### JR-DCL-SEC-001 — Enable PyPI build attestations and add scheduled security scanning (Bandit + pip-audit).

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 1-33)

**Detail**:

Supply chain security improvements: enabled build attestations in publish workflow, added
.github/workflows/security-scan.yml for weekly Bandit and pip-audit scanning. Version bump: 0.3.1 → 0.3.2.
All tests passing (88 unit tests, 0 failures).

**Notes**:

Status inferred from PR marked READY_FOR_MERGE with test results. SemVer impact: PATCH (0.3.1 → 0.3.2).
No breaking changes. Medium security/privacy impact (supply chain verification via attestations).

### JR-ML-TRAIN-001 — Fix activation function mismatch: use tanh instead of sigmoid in demo mode.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 87-103)

**Detail**:

Tanh critical for CasCor algorithm: outputs ∈ {-1,+1} create binary partitions; sigmoid ∈ {0,1} can produce constant features with zero gradient. Sigmoid mean-shift also biases output layer.

**Notes**:

Root cause RC-1; doc status indicates implementation complete

### JR-CAS-TRAIN-001 — Fix candidate task parameter wiring: use correct dictionary keys (candidate_seed, candidate_epochs, candidate_learning_rate).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 235-273)

### JR-CAS-TRAIN-002 — Fix candidate training runtime errors (method name mismatch, pickling, parameter handling).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 94-122)

**Detail**:

Fix _train_candidate_worker → _train_candidate_unit method call mismatch; add __getstate__/__setstate__ to LogConfig and CascadeCorrelationConfig for multiprocessing pickling support; update CascadeCorrelationNetwork.__getstate__ to exclude log_config.

### JR-ML-TRAIN-002 — Fix drain thread race condition in cascor lifecycle manager for candidate progress monitoring.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 121-142)

**Detail**:

Progress queue drain thread checks for queue before it exists in grow_network(). Fix: deferred queue discovery in drain thread or pre-create queue before original_grow().

**Notes**:

Status marked COMPLETE (Section 1, line 7-8); Phase 1 critical fix

### JR-ML-TRAIN-003 — Fix grow progress bar denominator to use max_hidden_units instead of max_epochs.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 104-118)

**Detail**:

Demo mode passes max_epochs (10000) as progress denominator instead of max_hidden_units (10), causing 0.12% → 0% display. Fix: use max_hidden_units in Canopy progress handler, cap at 100%.

**Notes**:

Phase 1 critical fix; doc status COMPLETE

### JR-CAS-TRAIN-003 — Fix logger pickling error in multiprocessing (BUG-002).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 28-36)

**Detail**:

Enhance CascadeCorrelationNetwork and CascadeCorrelationPlotter __getstate__/__setstate__ methods for pickle support; verify CandidateUnit has pickling support.

### JR-ML-TRAIN-004 — Fix loss function: use MSE on raw output instead of BCE with sigmoid.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 104-117)

**Detail**:

BCE residuals bounded [-1,1]; MSE residuals unbounded. MSE gradient stronger; residual magnitude larger. CasCor candidate training mathematically designed around MSE residuals.

**Notes**:

Root cause RC-2; doc status indicates implementation complete

### JR-CAS-TRAIN-004 — Fix multiprocessing completion logic that can hang indefinitely due to unreliable empty()/qsize() usage.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 59-99)

**Detail**:

Replace unreliable busy-wait loop using Manager queue empty()/qsize() with bounded timeout loop. Add worker liveness checks to detect crashed workers early. Exit immediately when all workers complete.

### JR-CAS-TRAIN-005 — Fix plotting subprocess to use spawn context instead of forkserver for reliable module import in child processes.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 342-386)

### JR-CAS-TRAIN-006 — Fix save_object() method TypeError due to argument count mismatch with _save_root_attributes().

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 200-232)

### JR-CAS-TRAIN-007 — Fix test random state restoration failures (BUG-001).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 18-26)

### JR-ML-TRAIN-005 — Increase output retraining from 50 mini-batch steps to full-batch training after hidden unit installation.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 118-131)

**Detail**:

Demo: ~1,600 sample evaluations; CasCor: ~2,000,000 (1,250× difference). New hidden unit weight initialized ~0.1; needs ample optimization time. Current 50 steps insufficient (~0.125 total change).

**Notes**:

Root cause RC-3; doc status indicates implementation complete

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-DAT-DATA-003 — Lifecycle management supports tagging, TTL, expiration via DatasetMeta (tags, ttl_seconds, expires_at).

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 34-35)

**Notes**:

DATA-016 complete.

### JR-DAT-DATA-004 — NPZ contract guarantees 6 array keys with float32 dtype and one-hot label encoding.

**Status**: shipped  **Priority**: P0  **Category**: DATA  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 274-292)

**Notes**:

Foundational data contract enforced by E2E tests.

### JR-DAT-TEST-002 — Security boundary test suite includes path traversal, CSV import, input bounds, resource exhaustion, API boundaries.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 201-223)

**Notes**:

RD-006 complete 2026-02-24. 41 tests across 5 classes. Documents path traversal risks in LocalFSDatasetStore and CsvImportGenerator.

### JR-DAT-OBS-001 — Security scanning (Bandit and pip-audit) must fail on vulnerabilities, not suppress with || true or || echo.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 170-238)

**Notes**:

SEC-001 and SEC-002 CRITICAL. Status shipped per 2026-02-24 migration.

### JR-DAT-TEST-003 — TST-001: test_main.py ImportError handling must assert/skip instead of silent pass.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 329-400)

**Notes**:

TST-001 CRITICAL (P0). Status shipped per migration. Fixes provided in section 3.1.

### JR-ML-TRAIN-006 — Use Adam optimizer instead of vanilla SGD for output training.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 225-242)

**Detail**:

Adam adapts per-parameter effective learning rates using first/second moment estimates. Vanilla SGD shares same lr across all params; new hidden unit columns converge poorly.

**Notes**:

Root cause RC-9; Phase 3 investigation finding; doc status indicates implementation complete

### JR-ML-TRAIN-007 — Use full-batch training between cascade additions instead of mini-batch.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 243-258)

**Detail**:

Mini-batch between cascades (960 evals) undoes full-batch retrain (40,000 evals). High gradient variance causes random walk of carefully retrained weights. Fix: full-batch for 30 epochs instead of mini-batch.

**Notes**:

Root cause RC-10; Phase 3 finding; ~40× weaker training; doc status indicates implementation complete

### JR-CWK-SEC-001 — v0.2.0 breaking change: remove hardcoded default auth key ("juniper"), make WORKER_AUTH_KEY environment variable required at worker startup with clear error message if not set.

**Status**: shipped  **Priority**: P0  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 27-50)

**Detail**:

Breaking change for 0.1.0→0.2.0 (SemVer minor allowed pre-1.0). Rationale: hardcoded default allowed any network-accessible actor to register workers. Removed the 'juniper' default. WORKER_AUTH_KEY now REQUIRED with validation at startup (clear error if not set). Migration: set WORKER_AUTH_KEY environment variable explicitly before worker startup. For production: source from secret store (Docker secrets, K8s secrets, Vault, SOPS-encrypted env file) rather than plaintext export.

**Notes**:

Related: v0.3.0 renamed WORKER_AUTH_KEY to CASCOR_AUTH_TOKEN and the CLI flag from --api-key to --auth-token. Operators upgrading directly from v0.1.x to v0.3.0 should consult v0.3.0 release notes for mapping.

### JR-CCL-LOCK-001 — Add JUNIPER_CASCOR_API_KEY environment variable fallback for API key authentication.

**Status**: shipped  **Priority**: P1  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-CWK-DOC-001 — AGENTS.md critical fixes: update version metadata (0.1.0→0.3.0), CLI command flags, env vars defaults, and flake8 line-length to match current codebase.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 9-36)

**Detail**:

Phase 1 critical corrections (blocking): (1.1) Update header version from 0.1.0 to 0.3.0, date to 2026-04-02. (1.2) Replace legacy --host/--port command with WebSocket-mode --server-url/--auth-token as default, add --legacy mode. (1.3) Remove incorrect 'juniper' default for CASCOR_AUTHKEY, add all WebSocket env vars (CASCOR_SERVER_URL, CASCOR_AUTH_TOKEN, CASCOR_HEARTBEAT_INTERVAL, etc.), label legacy-only variables. (1.4) Change flake8 --max-line-length from 120 to 512.

### JR-CWK-DOC-002 — AGENTS.md missing core architecture sections: WebSocket mode, binary tensor protocol, TLS/mTLS support, task executor, exception hierarchy, and deprecation status.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 37-79)

**Detail**:

Phase 2 missing core architecture (high priority): (2.1) Application Architecture section (two-mode WebSocket/legacy, communication flow, worker lifecycle, module dependency graph). (2.2) WebSocket mode docs (CascorWorkerAgent async event loop, WorkerConnection class, binary tensor protocol JSON+struct, TLS/mTLS config). (2.3) Task execution pipeline (execute_training_task, CandidateUnit dynamic import from cascor, --cascor-path flag). (2.4) Public API section (all __init__.py exports, CascorWorkerAgent/CandidateTrainingWorker interfaces, WorkerConfig dataclass, exception hierarchy). (2.5) Complete CLI reference (all flags with WebSocket/Legacy/Shared labels, signal handling, --cascor-path).

### JR-CCL-TEST-001 — Align FakeCascorClient response format with real cascor ResponseEnvelope structure for consumer parity.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 65-76)

**Detail**:

Wrap all FakeCascorClient responses in _success_envelope() matching real cascor envelope format.
Ensures consumer code working against fake also works against real backend.

**Notes**:

Shipped in v0.3.0 (2026-03-30); bug fix

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

### JR-DAT-API-002 — Client package juniper-data-client published to PyPI (>=0.3.0) with Trusted Publishing OIDC.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 313-330)

**Notes**:

RD-010 complete 2026-02-20. Standalone repo pcalnon/juniper-data-client. 41 tests, 96% coverage.

### JR-CCL-OPS-001 — Configure Dependabot for automated weekly dependency updates.

**Status**: shipped  **Priority**: P1  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-TEST-002 — Configure pre-commit hooks for markdownlint, shellcheck, flake8, bandit, yamllint quality gates.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-DOC-003 — Create CODEOWNERS file for PR review routing.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-DOC-004 — Create comprehensive documentation suite including DOCUMENTATION_OVERVIEW.md, QUICK_START.md, REFERENCE.md, DEVELOPER_CHEATSHEET.md.

**Status**: shipped  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 48-57)

**Detail**:

DOCUMENTATION_OVERVIEW.md (navigation index), QUICK_START.md (installation and first-call walkthrough),
REFERENCE.md (full method and configuration reference), docs/DEVELOPER_CHEATSHEET.md (quick-reference card),
AGENTS.md (thread handoff and worktree procedures), ecosystem compatibility matrix in README, CHANGELOG.md.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-TEST-002 — Create comprehensive test suite for serialization with 6+ test cases.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 38-51)

**Detail**:

Implement test_deterministic_training_resume, test_hidden_units_preservation, test_config_roundtrip, test_activation_function_restoration, test_torch_random_state_restoration, test_history_preservation.

### JR-CAS-TEST-003 — Create GitHub Actions CI/CD workflow with pytest, coverage, mypy, and linting.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 467-507)

### JR-CAS-ARCH-003 — Create juniper-cascor-client and juniper-cascor-worker installable packages with PyPI publishing.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1034-1047)

### JR-CCL-TEST-003 — Create juniper_cascor_client.testing submodule with FakeCascorClient and FakeCascorTrainingStream for consumer testing.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 34-42)

**Detail**:

Provide in-process fake client matching real client interface. Support update_params() with scenario-aware state updates.
Consumers can switch between real and fake by importing from one or the other.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAS-ARCH-004 — Decouple Canopy from CasCor via service client; remove direct imports and sys.path manipulation.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/POLYREPO_MIGRATION_PLAN.md` (lines 1208-1220)

**Detail**:

Implement CascorServiceAdapter for two-mode activation (demo/service); remove legacy CascorIntegration (~1,601 lines); remove sys.path manipulation; update configuration to use CASCOR_SERVICE_URL (port 8200).

### JR-DEP-OBS-005 — Define and catalogue 5 user-facing and 8 internal-supporting SLO/SLI targets for the Juniper observability stack.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 1-50)

**Detail**:

The SLO catalog is the single source of truth for Juniper SLOs. User-facing SLIs
(canopy availability, canopy render latency, cascor train-job success, cascor train-epoch p95,
data POST availability) are release-blocking with tight SLO targets. Internal-supporting SLIs
(worker heartbeat freshness, cascor pending-task queue, broadcast fan-out p95, command-handler
p95, data-client request latency, data-client error rate, dataset cache-hit ratio, http 5xx rate)
are graphed but not paging.

**Notes**:

SLO targets are provisional pending 30-day soak (§2.6). Burn-rate alerting uses
Multi-Window Multi-Burn-Rate pattern. Several forward-references to R5.3/R5.4 designs.

### JR-ML-TRAIN-008 — Derive candidate_pool_phase from phase_detail in Canopy adapter.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 686-709)

**Detail**:

Adapter derives candidate_pool_status but not candidate_pool_phase. One-line fix: map phase_detail to pool phase (Training/Selecting/Idle).

**Notes**:

Phase 2 P1 fix; doc status COMPLETE; simple derivation gap

### JR-DAT-DEP-001 — Dockerfile implements multi-stage build, python:3.11-slim, non-root UID 1000, port 8100, HEALTHCHECK.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 154-181)

**Notes**:

DATA-006 complete. .dockerignore excludes development artifacts.

### JR-DAT-TEST-004 — Documentation build step validates internal markdown links in CI, fails on broken links.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 411-430)

**Notes**:

RD-014 complete 2026-02-25. scripts/check_doc_links.py in quality gate. 22 files pass validation.

### JR-DAT-TEST-005 — End-to-end integration tests verify dataset creation, NPZ download, deterministic output, and both algorithm modes.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/INTEGRATION_DEVELOPMENT_PLAN.md` (lines 210-241)

**Notes**:

DATA-008 complete. 14 E2E tests in test_e2e_workflow.py marked @pytest.mark.integration @pytest.mark.slow.

### JR-ML-TRAIN-009 — Enhance grow iteration callback with top 2 candidate ID and correlation data.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 148-167)

**Detail**:

Top candidate info never forwarded from CasCor to Canopy; TrainingResults dataclass contains data but callback does not pass it. Fix: add best_candidate_id, best_candidate_uuid, second_candidate fields to callback signature.

**Notes**:

Phase 2 P1 fix; data already available in TrainingResults; doc status COMPLETE

### JR-CAS-TRAIN-008 — Expand format validation for HDF5 snapshot files.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 73-83)

**Detail**:

Check format name/version; validate required groups and datasets; verify hidden units consistency.

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

### JR-CAS-TRAIN-009 — Implement hidden units checksums for integrity verification.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 53-61)

### JR-CCL-API-002 — Implement remote worker monitoring methods: list_workers(), get_worker(worker_id), get_worker_stats().

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 28-35)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CAS-TRAIN-010 — Implement shape validation for serialized network structure.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 63-71)

**Detail**:

Implement _validate_shapes() method; validate output layer and hidden units; call from load_network().

### JR-CCL-API-003 — Implement snapshot management methods: list_snapshots(), get_snapshot(snapshot_id), save_snapshot(), load_snapshot(snapshot_id).

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 36-44)

**Notes**:

Shipped in v0.3.0 (2026-03-30)

### JR-CCL-SEC-001 — Implement SOPS configuration (.sops.yaml) and .env.example for secrets management.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-API-004 — Implement update_params() client method for runtime training parameter updates via PATCH /v1/training/params.

**Status**: shipped  **Priority**: P1  **Category**: API  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 28-33)

**Detail**:

Add update_params() method to JuniperCascorClient with supporting _patch() helper and PATCH method in ALLOWED_METHODS.
Tests required for both real client (responses mock) and fake client.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-DAT-TOOL-001 — Line length normalized to 120 characters in [tool.ruff] as single source of truth.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 390-408)

**Notes**:

RD-013 complete 2026-02-25. 24 files reformatted. Current value 320 per 2026-03-15 audit.

### JR-DAT-TOOL-002 — Linter migrated from flake8+isort+black+pyupgrade to ruff v0.15.2.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 359-388)

**Notes**:

RD-012 complete 2026-02-25. 2 ruff hooks replace 5 pre-commit hooks. All 700 tests pass.

### JR-DEP-OBS-006 — Maintain health-readiness probe topology as a DAG with asymmetric severity policies.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 1-87)

**Detail**:

Canopy probes both cascor and data, returns 200 degraded (dashboard stays visible).
Cascor probes data (when URL set), returns 503 not_ready (gates traffic). Data probes
storage only, returns 503 not_ready. Worker probes nothing externally. Topology is
intentionally a DAG to avoid cascading false-503s. Regression tests pin both policies.
Document in repo readiness handlers.

**Notes**:

Closes METRICS-MON R2.3 seed-15. Operator runbook in §6.

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

### JR-DAT-TEST-006 — Performance test infrastructure via pytest-benchmark: 41 baselines for generators and storage.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 269-305)

**Notes**:

RD-009 complete 2026-02-25. tests/performance/ with 21+20 benchmarks. --benchmark-disable default.

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

### JR-DAT-OBS-002 — Prometheus histogram juniper_data_dataset_generation_duration_seconds buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, +inf.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 25-43)

**Notes**:

Tentative pending R5.1 SLO design. Bucket rationale documented for each boundary.

### JR-DAT-OBS-003 — Release notes document known issues, resolved issues, and What's Next with accurate status.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 89-103)

**Notes**:

RD-001 complete 2026-02-24. Only B008 warnings remain. v0.5.0 scope updated.

### JR-DAT-SEC-002 — Security hardening includes SecurityHeadersMiddleware, RequestBodyLimitMiddleware, CORS, rate limiting, metrics auth, API docs hiding.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: dat

**Sources**:
- `juniper-data/notes/pull_requests/PR_SECURITY_HARDENING_2026-03-03.md` (lines 80-85)

**Notes**:

v0.5.0 released as security hardening. Requires explicit CORS_ORIGINS env var for existing deployments.

### JR-ML-TRAIN-010 — Use Pearson correlation (normalized) instead of raw covariance in candidate training.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 259-283)

**Detail**:

Raw covariance scales with residual magnitude; after first hidden unit, residuals shrink, candidate training gradients weaken (~8× decay observed). Pearson normalized by stddev, scale-invariant.

**Notes**:

Root cause RC-11; Phase 3 finding; doc status indicates implementation complete

### JR-CWK-SEC-002 — v0.2.0 security infrastructure: add .github/workflows/security-scan.yml for weekly scheduled Bandit and pip-audit scanning, Dependabot configuration, SOPS config, and SHA-pinned GitHub Actions.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 51-77)

**Detail**:

Added .github/workflows/security-scan.yml for weekly Bandit (static security) and pip-audit (dependency CVE scanning). Added SOPS configuration (.sops.yaml) and .env.example for secrets management. Updated .gitignore to cover all .env variants. SHA-pinned all GitHub Actions to immutable commit hashes. Added cross-repo CI dispatch to juniper-cascor on push to main. Added Dependabot configuration for weekly automated dependency updates. Added CODEOWNERS file for PR review routing.

### JR-CWK-SEC-003 — v0.3.0 CVE fix: bump setuptools minimum version to >=82.0 in pyproject.toml build-system requirements to remediate source distribution CVE.

**Status**: shipped  **Priority**: P1  **Category**: SEC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 95-109)

**Detail**:

setuptools CVE affecting source distribution handling; bumped to >=82.0. Bandit pre-commit hook tuned to avoid false positives on known-safe test fixtures (B105: hardcoded_password_string suppressed for test auth_token fields). pip-audit dependency scanning runs in CI; torch +cpu local version handling fixed to enable reliable scanning of worker dependency tree.

### JR-CWK-DEP-001 — v0.3.0 deployment infrastructure: multi-stage Docker with CPU-only PyTorch, non-root user, reproducible uv pip compile lockfiles; systemd user service and management CLI.

**Status**: shipped  **Priority**: P1  **Category**: DEP  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 53-66)

**Detail**:

Docker: multi-stage Dockerfile, CPU-only PyTorch, non-root user, requirements.lock via `uv pip compile` for reproducible builds, .dockerignore. Systemd: scripts/juniper-cascor-worker.service user service unit, scripts/juniper-cascor-worker-ctl management CLI for host-level deployment.

### JR-CWK-ARCH-001 — v0.3.0 major rewrite: WebSocket-based CascorWorkerAgent replaces BaseManager-based CandidateTrainingWorker as default, with TLS/mTLS support and async event loop.

**Status**: shipped  **Priority**: P1  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 10-39)

**Detail**:

v0.3.0 (2026-04-08): WebSocket worker agent (new default) with long-lived WebSocket, work units pushed from cascor backend, binary tensor frames (struct-encoded shape/dtype/numpy data), worker capability reporting (CPU cores, GPU, versions on connect), heartbeat keepalive loop. New classes: CascorWorkerAgent (async event loop), WorkerConnection (WebSocket transport with TLS/mTLS and exponential backoff reconnection). New modules: ws_connection.py, task_executor.py (isolated training pipeline). New CLI flags: --tls-cert, --tls-key, --tls-ca for mTLS. Legacy mode (CandidateTrainingWorker) preserved behind --legacy flag with DeprecationWarning, will be removed in next major. Auth token rename: --api-key/CASCOR_API_KEY → --auth-token/CASCOR_AUTH_TOKEN (old names retained as deprecated fallbacks).

**Notes**:

Backward-compatible at deployment level via --legacy. Operators may continue legacy mode during migration window. Default mode changed; no fallback default.

### JR-CWK-TOOL-001 — Worktree cleanup procedure with CWD continuity: create new worktree before removing old one to avoid trapping Claude Code sessions in invalid paths.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (lines 1-15)

**Detail**:

The V1 procedure (see notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md) removed the worktree directory without first creating a replacement, leaving the session trapped. V2 creates a new worktree and switches CWD before removing the old one (Phase 2 must complete before Phase 4). Phases: 1 Save & Push, 2 Create New Worktree (session continuity gate), 3 Merge & Pull Request, 4 Remove Old Worktree (prerequisite: new CWD verified), 5 Verify.

**Design**:

Phase 2 is the critical gate: CWD must move to the new worktree (Step 5) before the old one is removed (Phase 4, Step 9). The procedure enforces this with explicit verification gates in Step 6.

### JR-CWK-DOC-003 — AGENTS.md missing supplementary content: directory layout, expanded key files, test details, CI/CD, pre-commit hooks, scripts, Python version requirements, and resource location guide.

**Status**: shipped  **Priority**: P2  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 80-160)

**Detail**:

Phase 3 supplementary content (medium priority): (3.1) Expand Key Files table (all Python modules, docs/, scripts/, .github/workflows/, config files). (3.2) Add directory layout tree. (3.3) Update dependencies (add websockets>=11.0). (3.4) Add CI/CD section (6-job pipeline, weekly security scan, PyPI publish, Dependabot). (3.5) Add pre-commit hooks (black, isort, flake8, mypy, bandit, shellcheck, yamllint, markdownlint, SOPS). (3.6) Add test details (6 test files, ~83 tests, fixtures, 80% coverage threshold). (3.7) Add Python version requirements (>=3.11, supported 3.11-3.14, PEP 561 py.typed). (3.8) Add docs/ section. (3.9) Add scripts/ section. Phase 4 cleanup: remove stale conf/ references, update ecosystem compatibility version. Phase 5 validation: run link checker, cross-reference CLI/env vars, test suite.

### JR-CAS-OBS-002 — Define Prometheus histogram buckets for latency metrics per observability requirements.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-50)

**Notes**:

See histogram_rationale file for bucket selection rationale.

### JR-ML-WS-121 — GAP-WS-19 close_all lock is RESOLVED on main.

**Status**: shipped  **Priority**: P2  **Category**: WS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 48-48)

**Notes**:

Settled position C-11 from R3-03 table; cross-round consensus consolidation

### JR-CAS-TRAIN-011 — Implement flexible optimizer system supporting Adam, SGD, RMSprop, AdamW.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

OptimizerConfig dataclass and _create_optimizer() method already exist in codebase.

### JR-CAS-TRAIN-012 — Implement N-best candidate selection (candidates_per_layer configuration).

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

_select_best_candidates() and add_units_as_layer() methods already exist.

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

### JR-ML-API-006 — _normalize_metric dual-format contract (flat + nested) preserved forever.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 59-59)

**Notes**:

Settled position C-22 from R3-03 table; cross-round consensus consolidation

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

### JR-CCL-LOCK-002 — Propagate V2 worktree cleanup procedure (CWD-trap bug fix) to juniper-cascor-client.

**Status**: shipped  **Priority**: P2  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CAN-UI-012 — Redefine pool training metrics around correlation statistics instead of loss/accuracy.

**Status**: shipped  **Priority**: P2  **Category**: UI  **Owner**: can

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 396-440)

**Detail**:

CasCor trains on correlation, not loss/accuracy; these metrics do not exist for candidate pool. Replace with avg_correlation, max_correlation, min_correlation, std_correlation, success_rate.

**Notes**:

Phase 3 P2 fix; doc status COMPLETE; requires UI schema change

### JR-ML-API-007 — REST endpoints preserved FOREVER: /api/metrics/history, /api/train/*, /api/v1/training/params, /api/topology.

**Status**: shipped  **Priority**: P2  **Category**: API  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 60-60)

**Notes**:

Settled position C-23 from R3-03 table; cross-round consensus consolidation

### JR-CCL-OPS-002 — Set line length to 512 for all linters (black, isort, flake8) per Juniper ecosystem standard.

**Status**: shipped  **Priority**: P2  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21); ecosystem standard convention

### JR-CWK-TOOL-002 — Thread handoff procedure: preserve context fidelity when thread compaction degrades output by proactively handing off to fresh thread before context saturation.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/THREAD_HANDOFF_PROCEDURE.md` (lines 1-35)

**Detail**:

Thread compaction introduces information loss (subtle decisions, edge cases, partial progress, reasoning get dropped). Triggers: (1) context saturation after 15+ tool calls or 5+ file edits, (2) phase boundary completion, (3) degraded recall (re-reading files), (4) multi-module transitions, (5) user request. Do NOT handoff when task is nearly complete (<2 steps) or thread is still sharp. Handoff goal structure: original task, completed items, remaining work, key discoveries, file paths.

**Design**:

Handoff protocol: (1) Checkpoint current state (task, completed, remaining, discovered, files in play), (2) Compose concise actionable goal (be specific, include paths, state decisions, mention test status, keep <500 words), (3) Present to user via handoff() tool if available (follow=true for current thread stop, follow=false rare).

### JR-CWK-TOOL-003 — Worktree setup procedure: standardized protocol for creating git worktrees when beginning a new task, centralizing worktrees in /home/pcalnon/Development/python/Juniper/worktrees/.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_SETUP_PROCEDURE.md` (lines 1-30)

**Detail**:

Prerequisites: must be in primary directory (not already in worktree), working tree clean, target branch not already checked out elsewhere. Protocol: (1) Ensure clean state, (2) Fetch and update parent branch (typically main), (3) Create working branch, (4) Compute worktree directory name using format <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>, (5) Create worktree, (6) Verify and begin work.

**Design**:

Naming convention: <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>. All worktrees in /home/pcalnon/Development/python/Juniper/worktrees/. Example: juniper-cascor-worker--feature--add-gpu-support--20260225-1430--047c3f61.

### JR-CWK-ARCH-003 — v0.3.0 deprecations: CandidateTrainingWorker (legacy), --api-key CLI flag, CASCOR_API_KEY env var; migrate to CascorWorkerAgent and --auth-token before next major release.

**Status**: shipped  **Priority**: P3  **Category**: ARCH  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 113-122)

**Detail**:

CandidateTrainingWorker (legacy): use --legacy to opt in; emits DeprecationWarning. --api-key CLI flag (old flag still parsed, deprecated). CASCOR_API_KEY env var (old var still read as fallback, deprecated). Plan migration to CascorWorkerAgent and --auth-token before next major release.

