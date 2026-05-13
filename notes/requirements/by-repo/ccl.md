# Requirements — juniper-cascor-client (ccl)

**Total entries**: 33

**By status**: proposed=19 | shipped=14

**By priority**: P0=2 | P1=22 | P2=9

**By category**: DOC=13 | ARCH=6 | TEST=4 | API=4 | LOCK=2 | OPS=2 | SEC=2

---

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

### JR-CCL-LOCK-001 — Add JUNIPER_CASCOR_API_KEY environment variable fallback for API key authentication.

**Status**: shipped  **Priority**: P1  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 43-46)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-TEST-001 — Align FakeCascorClient response format with real cascor ResponseEnvelope structure for consumer parity.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.3.0.md` (lines 65-76)

**Detail**:

Wrap all FakeCascorClient responses in _success_envelope() matching real cascor envelope format.
Ensures consumer code working against fake also works against real backend.

**Notes**:

Shipped in v0.3.0 (2026-03-30); bug fix

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

### JR-CCL-TEST-003 — Create juniper_cascor_client.testing submodule with FakeCascorClient and FakeCascorTrainingStream for consumer testing.

**Status**: shipped  **Priority**: P1  **Category**: TEST  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 34-42)

**Detail**:

Provide in-process fake client matching real client interface. Support update_params() with scenario-aware state updates.
Consumers can switch between real and fake by importing from one or the other.

**Notes**:

Shipped in v0.2.0 (2026-03-21)

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

### JR-CCL-LOCK-002 — Propagate V2 worktree cleanup procedure (CWD-trap bug fix) to juniper-cascor-client.

**Status**: shipped  **Priority**: P2  **Category**: LOCK  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21)

### JR-CCL-OPS-002 — Set line length to 512 for all linters (black, isort, flake8) per Juniper ecosystem standard.

**Status**: shipped  **Priority**: P2  **Category**: OPS  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/releases/RELEASE_NOTES_v0.2.0.md` (lines 90-96)

**Notes**:

Shipped in v0.2.0 (2026-03-21); ecosystem standard convention

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

### JR-CCL-SEC-002 — Add Security section to AGENTS.md documenting SOPS encryption, Gitleaks, Bandit, pip-audit.

**Status**: proposed  **Priority**: P2  **Category**: SEC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 123-124)
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 75-76)

**Notes**:

Medium severity: documents security tooling

### JR-CCL-DOC-012 — Add Test Organization section to AGENTS.md documenting test structure, markers, fixtures, 80% coverage requirement.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md`
- `juniper-cascor-client/notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md` (lines 66-69)

**Notes**:

Medium severity: helps agents understand test conventions

### JR-CCL-DOC-013 — Update AGENTS.md and CHANGELOG.md documentation after hardcoded-values refactor completion.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: ccl

**Sources**:
- `juniper-cascor-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 76-79)

**Notes**:

Documentation & release phase (MEDIUM priority)

