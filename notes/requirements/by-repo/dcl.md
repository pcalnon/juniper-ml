# Requirements — juniper-data-client (dcl)

**Total entries**: 11

**By status**: proposed=10 | shipped=1

**By priority**: P0=3 | P1=3 | P2=4 | P3=1

**By category**: DOC=8 | SEC=1 | ARCH=1 | TEST=1

---

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

### JR-DCL-DOC-006 — Add CI/CD documentation section to AGENTS.md covering 3 GitHub Actions workflows.

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

### JR-DCL-DOC-007 — Document JuniperDataClient exception hierarchy with HTTP status code mapping in AGENTS.md.

**Status**: proposed  **Priority**: P2  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 112-116)

**Detail**:

Exception hierarchy is mentioned only in Key Files, not fully documented. Must show full exception tree
(JuniperDataClientError parent with 5 specific exceptions) and HTTP status code -> exception type mapping.
Essential context for agents working on error handling and debugging.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Task 3.3) and AGENTS_MD_UPDATE_PLAN (Step 3.3).

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-DCL-DOC-008 — Update AGENTS.md Last Updated date and document utility scripts.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 160-163)

**Detail**:

Low-priority metadata and polish tasks: (1) Update header Last Updated from 2026-02-20 to current date,
(2) Document utility scripts (scripts/check_doc_links.py, scripts/generate_dep_docs.sh, util/run_all_tests.bash),
(3) Add environment variables section documenting JUNIPER_DATA_API_KEY, JUNIPER_DATA_URL, .env.example reference.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Tasks 4.1, 4.2, 4.3) and AGENTS_MD_UPDATE_PLAN (Steps 4.1, 4.2, 4.3).

