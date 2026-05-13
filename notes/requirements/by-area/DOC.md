# Requirements — DOC

**Area**: documentation / process — link validation, conventions, file headers

**Total entries**: 42

**By status**: proposed=36 | shipped=6

**By priority**: P0=5 | P1=15 | P2=18 | P3=4

**By owner**: ccl=13 | dcl=10 | can=7 | ml=5 | cwk=3 | cas=2 | dat=2

---

### JR-CAS-DOC-001 — Document that CascadeCorrelationNetwork is not thread-safe.

**Status**: shipped  **Priority**: P0  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 183-198)

### JR-DCL-DOC-001 — Fix flake8 line-length command in AGENTS.md from 120 to 512.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 37-45)

**Detail**:

AGENTS.md commands section specifies --max-line-length=120, but the project standard is 512.
This discrepancy causes agents to produce false positives against actual project linting rules.
The parent CLAUDE.md explicitly states line-length 512 for all linters (ecosystem standard).
Fix: Update AGENTS.md Quick Reference > Essential Commands section.

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.2) and AGENTS_MD_UPDATE_PLAN (Step 1.2).

### JR-DCL-DOC-002 — Fix __version__ in juniper_data_client/__init__.py from 0.3.1 to 0.3.2 to match pyproject.toml.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 24-32)

**Detail**:

The __init__.py __version__ string (0.3.1) is out of sync with pyproject.toml (0.3.2).
This is a code bug affecting any code or consumer that reads juniper_data_client.__version__.
Fix: Update juniper_data_client/__init__.py line 10 to __version__ = "0.3.2"

**Notes**:

Also appears in AGENTS_MD_UPDATE_ROADMAP (Task 1.1) and AGENTS_MD_UPDATE_PLAN (Step 1.1).

### JR-CCL-DOC-001 — Update AGENTS.md version from 0.1.0 to 0.3.0 to match current package state.

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 20-28)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 11-13)

**Detail**:

AGENTS.md declares version 0.1.0 but actual package version is 0.3.0. Misleads agents about
codebase maturity and feature set (missing testing submodule, worker API, snapshot API, dataset API).

**Notes**:

Critical severity: marked P0 as blocking (misleads agents about codebase state)

### JR-CCL-DOC-002 — Update AGENTS.md: correct flake8 line length from 120 to 512 (blocker — agents produce incorrect output).

**Status**: proposed  **Priority**: P0  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 46-46)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 16-17)

**Detail**:

The AGENTS.md file incorrectly specifies flake8 --max-line-length=120, while pyproject.toml and
.pre-commit-config.yaml both specify 512 per Juniper ecosystem standard. This causes agents to
produce false-positive linting failures.

**Notes**:

Critical severity: marked P0 as blocking (agents produce incorrect output)

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

### JR-CCL-DOC-005 — Add Architecture section to AGENTS.md documenting class hierarchy, API categories, exception hierarchy, design patterns.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 51-56)

**Detail**:

Document class hierarchy (JuniperCascorClient, CascorTrainingStream, CascorControlStream),
API method categories (health, network, training, metrics, data, snapshots, workers),
exception hierarchy (7 exception classes), design patterns (context manager, callback/observer, retry, envelope).

**Notes**:

High severity: agents have no guidance on codebase structure

### JR-CCL-DOC-006 — Add Directory Layout section to AGENTS.md documenting complete directory tree with annotations.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 152-154)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 48-49)

**Notes**:

High severity: required by directives for agent codebase orientation

### JR-DCL-DOC-003 — Add directory structure section to AGENTS.md showing full repository layout.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-56)

**Detail**:

AGENTS.md lacks any description of the directory structure. Must document complex layout including:
juniper_data_client/, juniper_data_client/testing/, tests/, docs/, notes/, scripts/, util/,
.github/workflows/, conf/ with annotations for each directory's purpose.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.1) and AGENTS_MD_UPDATE_PLAN (Step 2.1).

### JR-CAN-DOC-001 — Application version must be centralized via importlib.metadata.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 83-83)

**Detail**:

Issue 1.2.1: Version string currently duplicated across health, status, and
config endpoints. Use importlib.metadata as single source of truth.
File: src/main.py

### JR-ML-DOC-001 — CHANGELOG.md + docs/websocket_protocol.md additive field contract section.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 121-121)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-CAN-DOC-002 — Configuration must have no version string mismatches (app_config.yaml, pyproject.toml).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 84-86)

**Detail**:

Issues 1.2.2, 1.2.3: Update app_config.yaml version to 0.4.0 and pyproject.toml
header version comment to match. Should be single source via importlib.metadata.

### JR-DCL-DOC-004 — Document complete JuniperDataClient public API (20+ methods) in AGENTS.md, replacing minimal 3-method snippet.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 79-108)

**Detail**:

Public API section currently shows only 3 methods (health_check, create_spiral_dataset, download_artifact_npz).
Client has grown to 20+ public methods across 9 categories: Health & Readiness (3), Generator Discovery (2),
Dataset Creation (2), Dataset Versioning (2), Dataset Operations (3), Artifact Download (2), Preview (1),
Batch Operations (4), Resource Management (2). Must replace snippet with full categorized reference.

**Notes**:

New API added since last AGENTS.md update (2026-02-20): batch_delete, batch_create, batch_update_tags,
batch_export, list_versions, get_latest, list_generators, get_generator_schema, get_preview, is_ready,
wait_for_ready. Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.3) and AGENTS_MD_UPDATE_PLAN (Step 2.3).

### JR-DCL-DOC-005 — Document juniper_data_client.testing submodule in AGENTS.md (FakeDataClient, generators).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-57)

**Detail**:

Testing submodule (juniper_data_client/testing/) contains FakeDataClient (715 lines) and 4 synthetic
generators (generate_spiral, generate_xor, generate_circle, generate_moon) in generators.py (284 lines).
This is a critical public API surface that ships with the library and is used by consumers (juniper-cascor,
juniper-canopy). Must add "Testing Utilities" section documenting import paths and usage patterns.

**Notes**:

The omission of this submodule from AGENTS.md means agents are unaware of this significant API.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.4) and AGENTS_MD_UPDATE_PLAN (Step 2.4).

### JR-DCL-DOC-006 — Expand AGENTS.md Key Files table from 4 entries to ~20 entries covering all significant files.

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 50-76)

**Detail**:

The Key Files table is severely incomplete. Must document: juniper_data_client/testing/ submodule
(fake_client.py, generators.py), docs/ directory (4 files), scripts/ (check_doc_links.py, generate_dep_docs.sh),
util/ (run_all_tests.bash), CI/CD workflows (.github/workflows/ci.yml, publish.yml, security-scan.yml),
configuration files (.pre-commit-config.yaml, .sops.yaml, .env.example, conf/), and project meta files
(CHANGELOG.md, py.typed, README.md, LICENSE).

**Notes**:

Severity: High. Testing submodule is critical public API (ships with library, used by juniper-cascor
and juniper-canopy). Agents working on this codebase are unaware of its existence when omitted from AGENTS.md.
Also in AGENTS_MD_UPDATE_ROADMAP (Task 2.2) and AGENTS_MD_UPDATE_PLAN (Step 2.2).

### JR-CCL-DOC-007 — Expand AGENTS.md Key Files table with 15+ missing entries (testing submodule, py.typed, CHANGELOG.md, docs/, scripts/, notes/, CI/CD files).

**Status**: proposed  **Priority**: P1  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 58-77)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 23-28)

**Detail**:

Missing files include: juniper_cascor_client/testing/ (1,807 LOC), py.typed (PEP 561),
CHANGELOG.md, docs/ (4 files), scripts/ (2 files), notes/, .env.example, .pre-commit-config.yaml,
.github/workflows/ci.yml, publish.yml, CODEOWNERS, dependabot.yml, .sops.yaml, conf/, tests/conftest.py.

**Notes**:

High severity: agents cannot orient themselves or find major code components

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

### JR-CWK-DOC-003 — AGENTS.md missing supplementary content: directory layout, expanded key files, test details, CI/CD, pre-commit hooks, scripts, Python version requirements, and resource location guide.

**Status**: shipped  **Priority**: P2  **Category**: DOC  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/AGENTS_MD_REMEDIATION_PLAN_2026-04-02.md` (lines 80-160)

**Detail**:

Phase 3 supplementary content (medium priority): (3.1) Expand Key Files table (all Python modules, docs/, scripts/, .github/workflows/, config files). (3.2) Add directory layout tree. (3.3) Update dependencies (add websockets>=11.0). (3.4) Add CI/CD section (6-job pipeline, weekly security scan, PyPI publish, Dependabot). (3.5) Add pre-commit hooks (black, isort, flake8, mypy, bandit, shellcheck, yamllint, markdownlint, SOPS). (3.6) Add test details (6 test files, ~83 tests, fixtures, 80% coverage threshold). (3.7) Add Python version requirements (>=3.11, supported 3.11-3.14, PEP 561 py.typed). (3.8) Add docs/ section. (3.9) Add scripts/ section. Phase 4 cleanup: remove stale conf/ references, update ecosystem compatibility version. Phase 5 validation: run link checker, cross-reference CLI/env vars, test suite.

### JR-DCL-DOC-007 — Add Architecture & Design Patterns section to AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-118)

**Detail**:

AGENTS.md lacks architecture/design patterns section. For agents working on this codebase, understanding
the following patterns is essential: connection management (requests.Session with HTTPAdapter), retry
strategy (exponential backoff, retries on 429/5xx), URL normalization (scheme addition, trailing slash
removal, /v1 suffix handling), error mapping (HTTP status codes -> specific exception types), API key
handling (constructor param or JUNIPER_DATA_API_KEY env var), context manager pattern.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.1) and AGENTS_MD_UPDATE_PLAN (Step 3.1).

### JR-DCL-DOC-008 — Add CI/CD documentation section to AGENTS.md covering 3 GitHub Actions workflows.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-134)

**Detail**:

AGENTS.md has no CI/CD documentation. Agents making changes should know: ci.yml runs multi-version
tests (Python 3.12, 3.13, 3.14), pre-commit hooks, coverage checks (80% threshold), security scanning;
publish.yml handles PyPI publishing with trusted publishing (OIDC) and build attestations;
security-scan.yml runs weekly Bandit + pip-audit scanning.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.2) and AGENTS_MD_UPDATE_PLAN (Step 3.2).

### JR-CCL-DOC-008 — Add CI/CD Pipeline section to AGENTS.md documenting GitHub Actions workflow structure, quality gates, downstream dispatch.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 57-60)

**Notes**:

Medium severity: improves agent understanding of CI workflows

### JR-CCL-DOC-009 — Add Environment Variables section to AGENTS.md documenting JUNIPER_CASCOR_API_KEY and CASCOR_SERVICE_URL.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 71-73)

**Notes**:

Medium severity: documents runtime configuration

### JR-CCL-DOC-010 — Add Linting & Formatting section to AGENTS.md documenting line length (512), tool versions, complexity limits, pre-commit hooks.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 62-64)

**Notes**:

Medium severity: supports local quality enforcement

### JR-CCL-DOC-011 — Add Python Version Support note to AGENTS.md documenting >=3.11, tested on 3.11-3.14.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md`
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 78-79)

**Notes**:

Medium severity: clarifies compatibility constraints

### JR-CCL-DOC-012 — Add Test Organization section to AGENTS.md documenting test structure, markers, fixtures, 80% coverage requirement.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md`
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 66-69)

**Notes**:

Medium severity: helps agents understand test conventions

### JR-DCL-DOC-009 — Document JuniperDataClient exception hierarchy with HTTP status code mapping in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-116)

**Detail**:

Exception hierarchy is mentioned only in Key Files, not fully documented. Must show full exception tree
(JuniperDataClientError parent with 5 specific exceptions) and HTTP status code -> exception type mapping.
Essential context for agents working on error handling and debugging.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.3) and AGENTS_MD_UPDATE_PLAN (Step 3.3).

### JR-ML-DOC-002 — Fix 17 broken markdown links in DEVELOPER_CHEATSHEET.md - 12 self-referencing and 5 missing intra-repo files.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 207-244)

**Detail**:

Category B (12 links): self-referencing cross-repo links should be direct relative:
- ../juniper-ml/notes/SOPS_USAGE_GUIDE.md → SOPS_USAGE_GUIDE.md
- ../juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md → SOPS_IMPLEMENTATION_PLAN.md
- ../juniper-ml/notes/SOPS_AUDIT_2026-03-02.md → SOPS_AUDIT_2026-03-02.md
- ../juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md → SECRETS_MANAGEMENT_ANALYSIS.md
- ../juniper-ml/notes/pypi-publish-procedure.md → pypi-publish-procedure.md
- ../juniper-ml/AGENTS.md → ../AGENTS.md (5 instances)

Category C (5 links): missing files never created, should be removed or redirected:
- Line 491: plan_7.5_7.6_dependency_management.md (remove)
- Line 575: STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md (remove)
- Line 720: PYPI_PUBLISH_PROCEDURE.md → pypi-publish-procedure.md (rename fix)
- Line 720: PYPI_PUBLISH_PLAN_3_PACKAGES.md (remove)
- Line 755: WORKTREE_IMPLEMENTATION_PLAN.md (remove or redirect to WORKTREE_SETUP_PROCEDURE.md)

### JR-CAS-DOC-002 — Fix import alias mistake: datetime import uses pd instead of dt.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 362-366)

**Detail**:

Line 38 of cascade_correlation.py: 'import datetime as pd' should be 'import datetime as dt'. pd is conventionally pandas; using for datetime misleads developers.

### JR-ML-DOC-003 — Fix semantic error in SECURITY_AUDIT_PLAN.md line 845 - correct deep relative path to ../CLAUDE.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 246-264)

**Detail**:

Category D false-negative: ../../../CLAUDE.md resolves to wrong document via repo-root fallback.
Should be ../CLAUDE.md to reference repo's own CLAUDE.md (symlink to AGENTS.md) containing the same #worktree-procedures-mandatory--task-isolation section.

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

### JR-ML-DOC-004 — Phase H: `_normalize_metric` dual-format regression test + consumer audit + CODEOWNERS hard gate.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 1032-1077)

**Detail**:

Phase does NOT refactor `_normalize_metric`; locks in dual-format contract (flat keys + nested keys) with regression gate.
Tests in `juniper-canopy/src/tests/unit/test_normalize_metric.py`.
Regression: `test_normalize_metric_produces_dual_format` asserts BOTH nested (`{training: {loss: 0.5}}`) AND flat (`{training.loss: 0.5}`) on output.
Additional tests: nested format unchanged since Phase H, flat format unchanged since Phase H.
Consumer audit document: `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` enumerates every consumer:
frontend MetricsPanel, CandidateMetricsPanel, Prometheus `/api/metrics`, WebSocket drain, debug logger, test fixtures.
CODEOWNERS: `juniper-canopy/src/backend/normalize_metric.py @<project-lead>` + `juniper-canopy/src/frontend/components/metrics_panel.py @<project-lead>`.
`.github/CODEOWNERS` branch protection enforces owner review.

**Design**:

Single PR (P16). Test-only phase; refactoring deferred to follow-up (gated on audit findings).

**Notes**:

Entry: Phase B in main. Exit: regression tests pass, CODEOWNERS enforced (test via PR without owner review → must block),
consumer audit reviewed + merged. Rollback: revert P16 (10 min TTF); CODEOWNERS rule disappears.
Note: Phase H is NOT a behavior-change gate; it's a documentation + regression-gate phase.

### JR-DAT-DOC-001 — Production startup must use create_app() factory: uvicorn juniper_data.api.app:create_app --factory or python -m juniper_data.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 239-250)

**Notes**:

D-050 MEDIUM priority. Current docs show direct app reference.

### JR-CAN-DOC-005 — Remove commented-out imports across codebase.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 164-164)

**Detail**:

Issue 3.2.5: Commented imports clutter code. Remove or restore with rationale.

### JR-ML-DOC-005 — Stabilize CI documentation link validation by implementing cross-repo link classification and worktree directory exclusion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/CROSS_REPO_LINK_RESOLUTION_PROPOSAL.md` (lines 70-175)

**Detail**:

DEVELOPER_CHEATSHEET.md has 124 broken cross-repo links in CI:
- 107 Category A: cross-repo relative links (../juniper-data/..., etc)
- 12 Category B: self-referencing cross-repo (../juniper-ml/...)
- 5 Category C: missing intra-repo files
- 1 Category D: false-negative deep link

Phase 1: Implement --cross-repo flag with skip/warn/check modes; exclude .claude/worktrees from scanning.

**Design**:

Approach 1A: Add --cross-repo flag with three modes:
- skip (default in CI): skip cross-repo links, log count
- warn: report as warnings (non-blocking)
- check: validate as normal (for local with all repos)

_ECOSYSTEM_REPOS hardcoded set with 8 known repos.
_CROSS_REPO_PATTERN regex matches patterns.

**PRs**: juniper-ml PR

**Notes**:

Recommend Phase 1: CI stabilization with --cross-repo skip.
Phase 2: ecosystem-root discovery with fallback.
Phase 3: documentation content cleanup (Approach 2A hybrid links).

### JR-CCL-DOC-013 — Update AGENTS.md and CHANGELOG.md documentation after hardcoded-values refactor completion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 76-79)

**Notes**:

Documentation & release phase (MEDIUM priority)

### JR-CAN-DOC-006 — Add deprecation warnings to remaining legacy env validators.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 227-227)

**Detail**:

Issue 5.1.1: Legacy env var validators need deprecation warnings.
Use warnings.warn() to alert users of upcoming removal.

### JR-DAT-DOC-002 — AGENTS.md must document current project structure, components, security, dependencies (15+ entries for components).

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dat

**Sources**:
- `juniper-data/notes/AGENTS_MD_DRIFT_ANALYSIS.md` (lines 45-64)

**Notes**:

D-001 through D-050 catalogued. 5 CRITICAL issues (version, security, line length, directory, middleware).

### JR-CAN-DOC-007 — Codecov build count assumption must be documented.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 254-254)

**Detail**:

Issue 5.4.4: Codecov configuration makes implicit assumptions about build
frequency. Document in README or config comments what build count limit is
set to and why.

### JR-DCL-DOC-010 — Update AGENTS.md Last Updated date and document utility scripts.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 160-164)

**Detail**:

Low-priority metadata and polish tasks: (1) Update header Last Updated from 2026-02-20 to current date,
(2) Document utility scripts (scripts/check_doc_links.py, scripts/generate_dep_docs.sh, util/run_all_tests.bash),
(3) Add environment variables section documenting JUNIPER_DATA_API_KEY, JUNIPER_DATA_URL, .env.example reference.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Tasks 4.1, 4.2, 4.3) and AGENTS_MD_UPDATE_PLAN (Steps 4.1, 4.2, 4.3).

