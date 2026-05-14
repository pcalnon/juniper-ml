# Requirements — juniper-data-client (dcl)

**Total entries**: 16

**By status**: proposed=15 | shipped=1

**By priority**: P0=3 | P1=4 | P2=8 | P3=1

**By category**: DOC=10 | ARCH=3 | SEC=1 | DATA=1 | TEST=1

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

### JR-DCL-DATA-001 — Refactor testing/generators.py to import from constants.py (~30 replacements).

**Status**: proposed  **Priority**: P2  **Category**: DATA  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 46-49)

**Detail**:

testing/generators.py contains ~30 hardcoded values (math constants, dataset defaults) for spiral, xor,
circle, and moon generators that must be migrated to constants.py. Depends on dcl-010.

**Notes**:

[v2 ARCH→DATA re-bucket]

### JR-DCL-TEST-001 — Run full test suite and pre-commit hooks after constants refactor to validate no behavioral changes.

**Status**: proposed  **Priority**: P2  **Category**: TEST  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/HARDCODED_VALUES_REFACTOR_PLAN.md` (lines 52-69)

**Detail**:

After completing constants refactor (dcl-010 through dcl-013), must run: (1) Full test suite with
pytest tests/ -v, (2) Pre-commit hooks with pre-commit run --all-files, (3) Verify each generator
(spiral, xor, circle, moon) with default parameters to ensure outputs match pre-refactor results.

### JR-DCL-DOC-010 — Update AGENTS.md Last Updated date and document utility scripts.

**Status**: proposed  **Priority**: P3  **Category**: DOC  **Owner**: dcl

**Sources**:
- `juniper-data-client/notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md` (lines 160-163)

**Detail**:

Low-priority metadata and polish tasks: (1) Update header Last Updated from 2026-02-20 to current date,
(2) Document utility scripts (scripts/check_doc_links.py, scripts/generate_dep_docs.sh, util/run_all_tests.bash),
(3) Add environment variables section documenting JUNIPER_DATA_API_KEY, JUNIPER_DATA_URL, .env.example reference.

**Notes**:

Also in AGENTS_MD_UPDATE_ROADMAP (Tasks 4.1, 4.2, 4.3) and AGENTS_MD_UPDATE_PLAN (Steps 4.1, 4.2, 4.3).

