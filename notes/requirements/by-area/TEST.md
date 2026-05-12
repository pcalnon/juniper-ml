# Requirements — TEST

**Area**: testing-and-ci — pytest, fixtures, CI workflows, regression analysis

**Total entries**: 59

**By status**: proposed=42 | shipped=16 | deferred=1

**By priority**: P0=4 | P1=32 | P2=20 | P3=3

**By owner**: can=24 | dat=11 | cas=8 | ml=6 | ccl=4 | cwk=3 | dep=2 | dcl=1

---

### JR-DAT-TEST-001 — Code coverage 99.40% aggregate with 85% per-module minimum enforced in CI.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 165-173)

**Notes**:

RD-005 and RD-007 complete 2026-02-24. 659 tests, 51 modules all >=85%. Reverted to 80% per 2026-03-15 audit.

### JR-CAS-TEST-001 — Increase serialization test coverage to ≥80% for snapshot_serializer.py.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 102-147)

### JR-DAT-TEST-002 — Security boundary test suite includes path traversal, CSV import, input bounds, resource exhaustion, API boundaries.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 201-223)

**Notes**:

RD-006 complete 2026-02-24. 41 tests across 5 classes. Documents path traversal risks in LocalFSDatasetStore and CsvImportGenerator.

### JR-DAT-TEST-003 — TST-001: test_main.py ImportError handling must assert/skip instead of silent pass.

**Status**: shipped  **Priority**: P0  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 329-400)

**Notes**:

TST-001 CRITICAL (P0). Status shipped per migration. Fixes provided in section 3.1.

### JR-CCL-TEST-001 — Align FakeCascorClient response format with real cascor ResponseEnvelope structure for consumer parity.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 65-76)

**Detail**:

Wrap all FakeCascorClient responses in _success_envelope() matching real cascor envelope format.
Ensures consumer code working against fake also works against real backend.

**Notes**:

Shipped in v0.3.0 (2026-03-30); bug fix

### JR-CCL-TEST-002 — Configure pre-commit hooks for markdownlint, shellcheck, flake8, bandit, yamllint quality gates.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 58-63)

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

### JR-CCL-TEST-003 — Create juniper_cascor_client.testing submodule with FakeCascorClient and FakeCascorTrainingStream for consumer testing.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 34-42)

**Detail**:

Provide in-process fake client matching real client interface. Support update_params() with scenario-aware state updates.
Consumers can switch between real and fake by importing from one or the other.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

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

### JR-CAN-TEST-009 — CI must upload coverage reports to Codecov.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 117-117)

**Detail**:

Issue 2.1.5: .github/workflows/ci.yml missing Codecov step. Add upload
after test run for coverage tracking and status badges.

### JR-CAS-TEST-004 — Establish automated CI/CD pipeline with pytest, coverage, type checking, and linting.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 569-599)

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

### JR-CAN-TEST-012 — MyPy strict_optional setting conflict must be resolved.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 123-123)

**Detail**:

Issue 2.2.3: MyPy configuration has conflicting strict_optional directives
in different sections. Consolidate to single authoritative setting.

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

### JR-ML-TEST-001 — Phase G: Cascor set_params integration tests via FastAPI TestClient.websocket_connect().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 89-100)

**Notes**:

Phase G major milestone from R3-03 Phase index (§2); orchestrates implementation effort

### JR-CAN-TEST-015 — pip-audit in CI must scan full dependency tree, not just top-level.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 115-115)

**Detail**:

Issue 2.1.3: pip-audit command in .github/workflows/ci.yml is incomplete.
Must specify report file and scan transitive dependencies.

### JR-CAN-TEST-016 — Replace 8 always-passing assert True tests with real assertions using pytest.raises().

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 86-98)

**Detail**:

Tests in performance and integration suites use assert True in both success and exception branches. Provides false confidence; regressions undetectable.

**Notes**:

Category A: 8 critical test issues; Phase 1 critical

### JR-CCL-TEST-004 — Run full test suite validation after constants refactor to ensure scenario outputs and behaviors unchanged.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 62-71)

**Detail**:

Execute: pytest tests/ -v
Verify scenario generation for two_spiral, xor_converged, and empty scenarios.
Validate metric curves, topology, and decision boundary data match pre-refactor.

**Notes**:

Validation phase of refactor (HIGH priority)

### JR-CAS-TEST-005 — Set and enforce minimum coverage thresholds: 70% overall, 80% for core snapshots module.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 632-647)

### JR-DAT-TEST-007 — Test code quality: tests must not be excluded from flake8, mypy, or pytest checks.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 58-76)

**Detail**:

TST-002: Tests excluded from Flake8 (HIGH).
TST-003: Tests excluded from MyPy (HIGH).
TST-004: Pytest warnings suppressed (HIGH).
CFG-001: Excessive Flake8 ignores E722, F401 (HIGH).
33+ flake8 violations hidden (F401 7, F541 5, SIM117 21).

**Notes**:

P1 HIGH issues. 34 total violations currently undetected.

### JR-CWK-TEST-001 — Test import mocking fix: add patch.dict(sys.modules, {"cascade_correlation": None, ...}) to test_connect_without_cascor_raises and test_start_without_cascor_raises to force ImportError regardless of JuniperCascor environment.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/history/FIX_TEST_IMPORT_MOCKING_PLAN.md` (lines 1-50)

**Detail**:

Two tests fail when run in JuniperCascor conda environment where cascade_correlation package is installed: (1) test_connect_without_cascor_raises expects ImportError handler but import succeeds, code attempts real TCP connection to manager (127.0.0.1:50000), gets ConnectionRefusedError wrapped as WorkerConnectionError, regex match fails. (2) test_start_without_cascor_raises bypasses "Not connected" guard, import succeeds, code spawns real forkserver processes, returns normally without raising. Fix: wrap both tests' calls to worker.connect()/start() in patch.dict(sys.modules, {"cascade_correlation": None, "cascade_correlation.cascade_correlation": None}), forcing ImportError on import statement. Matches existing pattern in 6 other tests (lines 87, 115, 134, 161, 186, 307). Setting sys.modules key to None causes Python's import machinery to raise ImportError: import of <module> halted; None in sys.modules.

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

### JR-ML-TEST-002 — testing/fake_ws_client.py: on_command(name, handler) auto-scaffold command_response reply.

**Status**: proposed  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 225-225)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAS-TEST-006 — Defer test optimization: reduce 45-minute test suite to ≤5 minutes.

**Status**: deferred  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 37-39)

**Detail**:

Test suite runs in 45+ minutes; target ≤5 minutes. This is a deferred medium-priority optimization (MED-014) per document status.

**Notes**:

Deferred optimization; developer productivity; noted in doc status

### JR-CAN-TEST-018 — Add integration tests for async/sync boundary with WebSocket responsiveness during training.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/INTEGRATION_ROADMAP-01.md` (lines 168-189)

**Detail**:

No integration tests verify WebSocket responsiveness during active training; schedule_broadcast() uses run_coroutine_threadsafe but has no tests.

**Notes**:

Phase 2 high priority; training callbacks are registered but untested in integration context

### JR-DEP-TEST-001 — Add scheduled weekly integration tests to detect upstream breakage.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 184-195)

**Detail**:

Phase 4 (v0.5.0) CI enhancement. Add schedule: cron: '0 6 * * 1' trigger to
.github/workflows/ci.yml or dedicated workflow. Run full Docker integration suite
weekly against main to detect upstream breakage. Notify on failure via GitHub Actions.

### JR-CAS-TEST-007 — Backward compatibility testing with old serialized snapshots.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

### JR-CWK-TEST-002 — Bandit B105 pre-commit false positives in test files: suppress B105 (hardcoded_password_string) in test Bandit hook, targeting known-safe test fixture credential values.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 99-106)

**Detail**:

Root cause: auth_token field matches Bandit regex (RE_WORDS includes "token") introduced in WebSocket Phase 2 refactoring after pre-commit config finalized. Original api_key didn't trigger B105 ("key" not in word list). 11 B105 false positives across 3 test files (test_cli.py:4, test_config.py:6, test_worker_agent.py:1) — all test fixtures using dummy credentials. Solution: Add B105 to --skip in .pre-commit-config.yaml test Bandit hook (line 195), maintaining numerical order (--skip=B101,B104,B105,B108,B110,B311). Source Bandit hook unaffected; detect-private-key hook catches real secrets.

### JR-ML-TEST-003 — Chromium-only Playwright for v1.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 69-69)

**Notes**:

Settled position C-32 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TEST-019 — Consolidate duplicate conftest.py fixtures into single configuration file.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 122-128)

**Detail**:

Two conftest.py files (445 + 224 lines) contain overlapping fixtures. Consolidate to avoid duplication and maintenance burden.

**Notes**:

Category D: Duplicate fixtures; DRY principle violation

### JR-ML-TEST-004 — Contract-test pytest marker contract runs on every PR, NOT nightly.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 71-71)

**Notes**:

Settled position C-34 from R3-03 table; cross-round consensus consolidation

### JR-DEP-TEST-002 — Extend compose validation to cover observability and production profiles.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 205-211)

**Detail**:

Phase 4. validate-compose job in ci.yml already validates full, demo, dev profiles.
Extend to validate observability and production profiles as added. Add JSON schema
validation for Grafana dashboard files (Phase 1 output).

### JR-DAT-TEST-008 — Fix 21 SIM117 violations (nested with statements) by combining where Python 3.11+ allows.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 247-266)

**Notes**:

RD-008 LOW priority deferred. Currently in ruff ignore list in pyproject.toml.

### JR-CAS-TEST-008 — Increase code coverage from ~15-78% baseline to 90% target via additional unit tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 543-589)

### JR-ML-TEST-005 — Latency tests are recording-only in CI (latency_recording marker); strict assertions local-only.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 72-72)

**Notes**:

Settled position C-35 from R3-03 table; cross-round consensus consolidation

### JR-CAN-TEST-020 — Move 5 non-test files (scripts, manual verifiers) out of test directory to util/.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 99-108)

**Detail**:

Files like test_yaml.py, test_dashboard_init.py are print-based scripts with no assertions. Should be moved to util/ for clarity.

**Notes**:

Category B: 5 files; Phase 1 high priority

### JR-CAN-TEST-021 — Phase 4 Test Coverage Expansion (14 tasks).

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 189-214)

**Detail**:

Step 4.1 (4 gap fills): Test discovery, observability (Prometheus/Sentry),
secrets_util (SOPS paths), middleware edge cases (malformed headers).
Step 4.2 (4 new types): Security tests (auth, injection, CORS), WebSocket load,
circuit breaker resilience, API contract validation.

### JR-ML-TEST-006 — Phase G (integration tests): 15 cascor `/ws/control` set_params tests via FastAPI TestClient + contract lane.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 976-1029)

**Detail**:

Tests in `juniper-cascor/src/tests/integration/api/test_ws_control_set_params.py`.
15 entries: happy path, whitelist filters unknown keys, init_output_weights literal validation (rejects injection),
oversized frame 64 KB rejected (4 KB per B-pre-a), network error returns error, unknown command error,
malformed JSON closes 1003, origin rejected, unauthenticated rejected, rate limit after 10 cmds,
bad init_output_weights rejected, concurrent command correlation (2 clients, echo routing correct),
set_params during training applies on next epoch (ack vs effect), echoes command_id, command_response no seq.
Contract-lane test: `test_fake_cascor_message_schema_parity` (runs in both cascor + canopy `contract` lane).
No design sketch needed (test-only phase).

**Notes**:

Entry: Phase 0-cascor + Phase B-pre-b in main. Tests via FastAPI TestClient (no SDK dependency).
Exit: all 15 pass, `pytest -m contract` lane green in cascor + canopy. Rollback: n/a (test-only).
Dedup candidate with R3-03.

### JR-CAN-TEST-022 — Re-enable MyPy error codes currently disabled (15 codes); fix underlying type issues.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 160-165)

**Detail**:

.pre-commit-config.yaml disables 15 MyPy error codes, reducing type checking effectiveness. Phase 2 work to fix underlying issues, then re-enable codes.

**Notes**:

Category H: 15 codes disabled; type safety issue

### JR-CAN-TEST-023 — Remove || true suppression from Bandit security scan in CI pipeline.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN_AMP.md` (lines 150-155)

**Detail**:

ci.yml line 412: bandit || true suppresses security issues silently. Security should not fail silently.

**Notes**:

Category G: Security scan gap; best practices violation

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-DAT-TEST-009 — Slow test job must be scheduled separately for integration and performance tests.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 69-70)

**Notes**:

INF-003 MEDIUM (P2).

### JR-CWK-TEST-003 — Test warning elimination: suppress DeprecationWarnings in test_worker.py (expected legacy API tests), RuntimeWarnings for unawaited CascorWorkerAgent coroutines, enforce warnings-as-errors baseline in pyproject.toml.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/PRE_COMMIT_REMEDIATION_PLAN.md` (lines 107-144)

**Detail**:

DeprecationWarnings (23): CandidateTrainingWorker.__init__() emits at worker.py:326; test_worker.py exercises deprecated legacy API. Solution: module-level pytestmark filterwarnings in test_worker.py. RuntimeWarnings (3): unawaited CascorWorkerAgent.run() coroutines during mock-based test cleanup. Solution: targeted filterwarnings in pyproject.toml for coroutine pattern. Baseline: filterwarnings = ["error", ...] in pytest config treats all warnings as errors by default with explicit exceptions for known, intentional warnings. Prevents silent warning accumulation; new unexpected warnings cause test failures.

### JR-DAT-TEST-010 — Pre-commit hooks should include pyupgrade for syntax modernization.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 72-73)

**Notes**:

L-01 LOW (P3).

### JR-DAT-TEST-011 — Pre-commit hooks should include shellcheck for shell script validation.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 73-74)

**Notes**:

L-02 LOW (P3).

### JR-CAN-TEST-024 — Shellcheck severity level should align with ecosystem convention.

**Status**: proposed  **Priority**: P3  **Category**: TEST  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 252-252)

**Detail**:

Issue 5.4.2: Current shellcheck invocation uses non-standard severity flag.
Align to standard shellcheck options.

