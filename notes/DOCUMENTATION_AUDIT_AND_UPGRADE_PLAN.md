# Documentation Audit and Upgrade Plan

**Version**: 1.1.0
**Created**: 2026-03-14
**Author**: Paul Calnon (with Claude Code)
**Status**: Approved for Execution
**Scope**: All 8 active Juniper repositories + parent directory

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Current State Assessment](#current-state-assessment)
- [Phase 1: Prerequisites and Foundation](#phase-1-prerequisites-and-foundation)
- [Phase 2: DEVELOPER_CHEATSHEET.md Decomposition](#phase-2-developer_cheatsheetmd-decomposition)
- [Phase 3: Documentation Consistency Audit](#phase-3-documentation-consistency-audit)
- [Phase 4: Post-Release Development Roadmap Audit](#phase-4-post-release-development-roadmap-audit)
- [Phase 5: Validation and Cross-Referencing](#phase-5-validation-and-cross-referencing)
- [Dependency Graph](#dependency-graph)
- [Execution Notes](#execution-notes)

---

## Executive Summary

This plan defines a comprehensive documentation audit and upgrade across the entire Juniper ecosystem. It addresses three major work streams:

1. **DEVELOPER_CHEATSHEET.md decomposition** — Split the monolithic 1,425-line cheatsheet in `juniper-ml/notes/` into 8 per-project files, each written to the corresponding project's `docs/` directory, validated against that project's actual codebase and procedures.

2. **Documentation consistency audit** — Standardize file names, structures, layouts, and content across all 8 projects' `docs/` and `notes/` directories so documentation is comparable and navigable ecosystem-wide.

3. **Post-release development roadmap audit** — Evaluate all existing roadmap files for continued relevance, description accuracy, scope/difficulty changes, prioritization shifts, and approach refinements.

### Relationship to Prior Work

An earlier **DOCUMENTATION_AUDIT_V2_PLAN** (2026-03-02) addressed PascalCase/kebab-case conversion damage across all repos. That plan's Phase 0 blocker (reverting 501 uncommitted files) and subsequent remediation items (R-01 through R-47) are **prerequisites** for this plan. Any remaining incomplete items from that audit must be resolved or explicitly deferred before this plan's Phase 3 begins.

---

## Current State Assessment

### Documentation Inventory Summary

| Project                   | docs/ Files | notes/ Files | Has Roadmap       | Has Cheatsheet            | docs/ Structure           |
|---------------------------|-------------|--------------|-------------------|---------------------------|---------------------------|
| **juniper-ml**            | 3           | 47           | No                | Yes (master, 1,425 lines) | Flat (3 files)            |
| **juniper-cascor**        | 19          | 89           | Yes (105K lines)  | No                        | Hierarchical (6 subdirs)  |
| **juniper-data**          | 13          | 40           | Yes (787 lines)   | No                        | Mixed (3 subdirs)         |
| **juniper-canopy**        | 40          | 73           | Yes (1,044 lines) | No                        | Hierarchical (10 subdirs) |
| **juniper-data-client**   | 3           | 9            | No                | No                        | Flat (3 files)            |
| **juniper-cascor-client** | 3           | 6            | No                | No                        | Flat (3 files)            |
| **juniper-cascor-worker** | 3           | 8            | No                | No                        | Flat (3 files)            |
| **juniper-deploy**        | 7           | 7            | No                | No                        | Mixed (1 subdir)          |

### Universal Documentation (Present in All 8 Projects)

- `docs/DOCUMENTATION_OVERVIEW.md` — Navigation entry point
- `docs/QUICK_START.md` — 5-minute getting started
- `docs/REFERENCE.md` — Technical reference

### Key Inconsistencies Identified

| Issue                              | Details                                                                                   |
|------------------------------------|-------------------------------------------------------------------------------------------|
| **Subdirectory naming**            | `ci/` (juniper-cascor) vs. `ci_cd/` (juniper-data, juniper-canopy)                        |
| **File name casing**               | lowercase kebab-case (juniper-cascor) vs. UPPER_SNAKE_CASE (all others)                   |
| **Missing USER_MANUAL.md**         | juniper-cascor has no root-level user manual (content is in subdirectories)               |
| **Missing ENVIRONMENT_SETUP.md**   | juniper-cascor, juniper-ml, all client libraries lack this                                |
| **Repeated section in cheatsheet** | "Session ID and Resume Workflow" appears twice (lines 1021–1070 and 1077–1157)            |
| **Empty testing/ subdirectory**    | juniper-deploy has a `docs/testing/` directory with no files                              |
| **Duplicate ADR**                  | juniper-canopy has `ADR_001_VALID_TEST_SKIPS.md` in both `docs/` root and `docs/testing/` |

---

## Phase 1: Prerequisites and Foundation

**Priority**: CRITICAL — All subsequent phases depend on this
**Estimated Scope**: 8 projects
**Dependencies**: None
**Status**: **COMPLETE** (2026-03-14)

### 1.1 Resolve DOCUMENTATION_AUDIT_V2_PLAN Blockers

**Objective**: Ensure the codebase is in a clean, consistent state before beginning new documentation work.

#### Tasks

| ID    | Task                                      | Details                                                                                                                                                                                                                           |
|-------|-------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.1.1 | Audit V2 Phase 0 status                   | **COMPLETE.** All 8 repos clean on main. CLAUDE.md symlinks correct in all repos.                                                                                                                                                 |
| 1.1.2 | Inventory incomplete V2 remediation items | **COMPLETE.** 47 items inventoried: 7 previously complete, 3 fixed this session, 1 partial, 36 deferred. See `notes/V2_AUDIT_DISPOSITION_2026-03-14.md`.                                                                          |
| 1.1.3 | Execute remaining critical V2 items       | **COMPLETE.** R-01: deleted 1 misplaced file (scope was overstated). R-07: false positive (no fix needed). R-16: already fixed. R-17: fixed (AGENTS.md + CONSTANTS_GUIDE.md). R-18: already fixed. R-25: version bumped to 0.3.2. |
| 1.1.4 | Document V2 disposition                   | **COMPLETE.** Written to `notes/V2_AUDIT_DISPOSITION_2026-03-14.md` with full item-by-item disposition, deferral rationale, and success criteria assessment.                                                                      |

#### Phase 1.1 Success Criteria (Unblocking Gate)

Phase 2 may begin once **all** of the following are true:

- All V2 items are classified as COMPLETE, STILL REQUIRED, or DEFERRED
- No uncommitted changes remain in any of the 8 repos (Phase 0 resolved)
- V2 items R-01, R-07, R-16, R-17, R-18 are either COMPLETE or explicitly DEFERRED with documented rationale
- DEFERRED items have been assessed to confirm they do not conflict with Phases 2–5 of this plan
- If DEFERRED items would cause Phase 2–5 work to be overwritten or invalidated, they must be completed first

### 1.2 Establish Documentation Standards400 W 23RD ST

| ID    | Task                                    | Details                                                                                                                                                                                                                                 |
|-------|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.2.1 | Define documentation tier model         | **COMPLETE.** Four tiers defined: Service, Orchestration, Library, Meta-Package. See `Juniper/notes/DOCUMENTATION_STANDARDS.md`.                                                                                                        |
| 1.2.2 | Define mandatory docs per tier          | **COMPLETE.** Full mandatory file matrix defined in standards document.                                                                                                                                                                 |
| 1.2.3 | Standardize naming conventions          | **COMPLETE.** UPPER_SNAKE_CASE for files, snake_case for subdirs. **Note:** juniper-cascor kebab-case migration flagged as DECISION REQUIRED — existing `DOCUMENTATION_TEMPLATE_STANDARD.md` (v1.0.0) grandfathered the old convention. |
| 1.2.4 | Define DEVELOPER_CHEATSHEET.md template | **COMPLETE.** Template defined in standards document with header block, required sections, and rules.                                                                                                                                   |
| 1.2.5 | Document standards in ecosystem guide   | **COMPLETE.** Written to `Juniper/notes/DOCUMENTATION_STANDARDS.md`. References existing `DOCUMENTATION_TEMPLATE_STANDARD.md` for formatting/content standards.                                                                         |

### 1.3 Validate Working Environment

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 1.3.1 | Verify all 8 repos are on main and clean | **COMPLETE.** All 8 repos on `main`, working trees clean. Minor untracked: `prompts/bla` (juniper-ml), `.coverage` (juniper-deploy). |
| 1.3.2 | Verify docs/ directories exist | **COMPLETE.** All 8 projects have `docs/` directories. |
| 1.3.3 | Create worktrees for execution | **DEFERRED** to Phase 2 start. Worktrees will be created per-project as work begins. |

---

## Phase 2: DEVELOPER_CHEATSHEET.md Decomposition

**Priority**: HIGH — Core deliverable
**Estimated Scope**: 1 source file → 8 destination files + 1 ecosystem file
**Dependencies**: Phase 1 (standards and clean state)
**Status**: **COMPLETE** (2026-03-15)

### 2.1 Audit the Master Cheatsheet

**Objective**: Thoroughly audit `juniper-ml/notes/DEVELOPER_CHEATSHEET.md` (v1.3.0, 1,425 lines, last updated 2026-03-11) to identify all content by project affiliation and accuracy.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 2.1.1 | Map every section to its target project(s) | Walk through all 17 major sections and classify each subsection as belonging to one or more specific projects. Use the section analysis below as the starting map. |
| 2.1.2 | Identify duplicated content | Remove the duplicated "Session ID and Resume Workflow" section (appears at lines 1021–1070 AND 1077–1157). |
| 2.1.3 | Identify ecosystem-level content | Content that belongs to no single project (e.g., SOPS secrets management, data contract, cross-repo CI/CD patterns) should be flagged for the ecosystem-level cheatsheet in juniper-ml. |
| 2.1.4 | Verify accuracy of all commands and references | For each code block, verify the command/path/config against the actual current state of the referenced project. Flag stale or incorrect items. |
| 2.1.5 | Cross-reference with existing project docs | For each project, compare cheatsheet content with that project's `AGENTS.md`, `docs/REFERENCE.md`, and `notes/` files to identify gaps and redundancies. A "gap" is information in the project's docs/notes that the cheatsheet omits. A "redundancy" is cheatsheet content that duplicates existing project documentation verbatim. |
| 2.1.6 | Produce section mapping document | Formalize the section-to-project mapping into a structured reference document that sub-agents in Phase 2.2 can use as input. This document specifies: exact line ranges in the master cheatsheet, target project, content extraction notes, and known gaps to fill from project-specific sources. | Sub-Agent: Yes |

#### Section-to-Project Mapping (Starting Point)

| Cheatsheet Section | Primary Project(s) | Secondary Project(s) |
|--------------------|--------------------|-----------------------|
| Secrets (SOPS) | Ecosystem (juniper-ml) | juniper-data, juniper-cascor, juniper-canopy |
| API Endpoints | juniper-data, juniper-cascor | juniper-canopy |
| Clients | juniper-data-client, juniper-cascor-client | — |
| Services | juniper-data, juniper-cascor, juniper-canopy | juniper-deploy |
| Testing | All projects | — |
| Claude Automation Script | juniper-ml | — |
| Dependencies | All projects | — |
| Configuration | juniper-data, juniper-cascor, juniper-canopy | juniper-deploy |
| Logging and Observability | juniper-data, juniper-cascor, juniper-canopy | juniper-deploy |
| CI/CD and Pre-commit | All projects | — |
| Claude Code Session Script | juniper-ml | — |
| Git Worktrees | Ecosystem (juniper-ml) | All projects |
| Data Contract | juniper-data, juniper-data-client | juniper-cascor |
| Docker | juniper-deploy | juniper-data, juniper-cascor, juniper-canopy |

### 2.2 Create Per-Project Cheatsheet Files

**Objective**: Write 8 project-specific `DEVELOPER_CHEATSHEET.md` files, each in the corresponding project's `docs/` directory, plus 1 ecosystem-level file retained in `juniper-ml/docs/`.

#### Target File Locations

| Project | File Path |
|---------|-----------|
| juniper-ml | `juniper-ml/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-cascor | `juniper-cascor/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-data | `juniper-data/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-canopy | `juniper-canopy/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-data-client | `juniper-data-client/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-cascor-client | `juniper-cascor-client/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-cascor-worker | `juniper-cascor-worker/docs/DEVELOPER_CHEATSHEET.md` |
| juniper-deploy | `juniper-deploy/docs/DEVELOPER_CHEATSHEET.md` |

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 2.2.1 | Draft juniper-ml cheatsheet | Extract juniper-ml-specific content: Claude automation scripts (`wake_the_claude.bash`), session management, launcher modes, PyPI publishing, meta-package extras, and ecosystem-wide procedures (SOPS, worktrees, data contract). This file serves as both the juniper-ml project cheatsheet AND the ecosystem-level quick reference. |
| 2.2.2 | Draft juniper-cascor cheatsheet | Extract: API endpoints (REST), service startup (native + Docker), CasCor-specific configuration (`CASCOR_*` env vars), testing commands and markers, logging configuration, Prometheus metrics, dependency management, CI/CD hooks, HDF5 serialization, N-best candidate selection. |
| 2.2.3 | Draft juniper-data cheatsheet | Extract: API endpoints (generators, datasets, health), service startup, `JUNIPER_*` env vars, testing commands and markers, ruff configuration, storage backends, generator patterns, Prometheus metrics, dependency management (uv pip compile). |
| 2.2.4 | Draft juniper-canopy cheatsheet | Extract: service startup (demo + production), Dash/FastAPI configuration, `CANOPY_*` env vars, CasCor backend integration, testing commands and markers, Cassandra/Redis integration procedures, demo mode operation, Prometheus metrics. |
| 2.2.5 | Draft juniper-data-client cheatsheet | Extract: client installation and usage, session pooling, retry logic, `JuniperDataClient` API, `FakeJuniperDataClient` for testing, data contract (NPZ format), error handling. |
| 2.2.6 | Draft juniper-cascor-client cheatsheet | Extract: REST client usage, WebSocket streaming (`CascorTrainingStream`), callback patterns, `FakeCascorClient` for testing, error handling and exception types. |
| 2.2.7 | Draft juniper-cascor-worker cheatsheet | Extract: CLI usage, `WorkerConfig` configuration, environment variables, distributed training patterns, testing commands. |
| 2.2.8 | Draft juniper-deploy cheatsheet | Extract: Docker Compose profiles (full, demo, dev, observability), `make` targets, service ports and health endpoints, environment variable configuration, Prometheus/Grafana setup, container management, network architecture. |
| 2.2.9 | Add cross-references | Each per-project cheatsheet should include a "See Also" section linking to: (a) the ecosystem cheatsheet in juniper-ml, (b) the project's own `AGENTS.md`, `docs/REFERENCE.md`, and relevant `notes/` files, (c) related project cheatsheets (e.g., juniper-data-client ↔ juniper-data). |

#### Content Gaps to Address During Drafting

The master cheatsheet has known coverage gaps that each per-project cheatsheet must fill using project-specific sources (`AGENTS.md`, `docs/`, `notes/`, and codebase inspection):

| Gap | Target Project | Source for New Content |
|-----|---------------|----------------------|
| HDF5 serialization/deserialization | juniper-cascor | `docs/api/API_SCHEMAS.md`, serialization code |
| Storage backends (filesystem, DB, cloud) | juniper-data | `docs/USER_MANUAL.md`, storage module code |
| Cassandra/Redis integration procedures | juniper-canopy | `docs/cassandra/`, `docs/redis/` subdirectories |
| FakeClient testing patterns | juniper-data-client, juniper-cascor-client | `docs/REFERENCE.md` in each client library |
| Client exception hierarchy and error handling | juniper-data-client, juniper-cascor-client | Client source code, `docs/REFERENCE.md` |
| Worker CLI, WorkerConfig, distributed training | juniper-cascor-worker | `AGENTS.md`, `docs/REFERENCE.md`, CLI source code |
| Inter-service networking (Docker DNS, bridges) | juniper-deploy | `docker-compose.yml`, `docs/REFERENCE.md` |
| Cross-repo dependency version synchronization | juniper-ml (ecosystem) | Parent `CLAUDE.md` dependency graph |
| WebSocket message schemas and lifecycle | juniper-cascor-client | `docs/REFERENCE.md`, WebSocket client source |
| Canopy session state management | juniper-canopy | Dashboard source code, `docs/USER_MANUAL.md` |

### 2.3 Augment Cheatsheets with Project-Specific Content

**Objective**: Each cheatsheet should go beyond what the master cheatsheet contained. Evaluate each project's `notes/` and `docs/` directories for additional information that belongs in the cheatsheet.

#### Content Extraction Guidance

When extracting content from project `notes/` and `docs/` files for cheatsheet inclusion:

- **Summarize, don't copy**: Distill multi-page procedures into concise step-by-step quick references (5–15 lines per procedure)
- **Preserve code blocks**: Keep exact commands, paths, and code snippets — these are the primary value of a cheatsheet
- **Link to source**: Each extracted procedure should include a `> See: <source-file>` reference for the full version
- **Focus on "how to"**: Cheatsheets answer "how do I do X?" — omit background/rationale (that belongs in the source doc)
- **Target length per section**: 20–50 lines for major features, 5–15 lines for minor procedures

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 2.3.1 | Evaluate juniper-ml notes/ for additions | Review: `SOPS_USAGE_GUIDE.md`, `SOPS_IMPLEMENTATION_PLAN.md`, `SOPS_AUDIT_2026-03-02.md`, `PYPI_DEPLOYMENT_PLAN.md`, `pypi-publish-procedure.md`, `MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md`. Extract quick-reference procedures missing from the master cheatsheet. |
| 2.3.2 | Evaluate juniper-cascor notes/ for additions | Review: `ARCHITECTURE_GUIDE.md`, `FEATURES_GUIDE.md`, `API_REFERENCE.md`, `DEPENDENCY_UPDATE_WORKFLOW.md`, `CI_PIPELINE_DEVELOPMENT_PLAN.md`. Extract architecture-specific quick references, CasCor algorithm parameters, and CI pipeline specifics. |
| 2.3.3 | Evaluate juniper-data notes/ for additions | Review: `DEPENDENCY_UPDATE_WORKFLOW.md`, `PRECOMMIT_SIM108_FIX_PLAN.md`, `releases/RELEASE_NOTES_v0.4.2.md`. Extract generator-specific procedures, storage backend configuration, and ruff migration details. |
| 2.3.4 | Evaluate juniper-canopy notes/ for additions | Review: `development/IMPLEMENTATION_PLAN.md`, `development/DEVELOPMENT_ROADMAP.md`, `fixes/` directory (7 fix files), `analysis/DEMO_HANG_ANALYSIS_2026-01-03.md`. Extract dashboard-specific troubleshooting, demo mode issues, and integration testing procedures. |
| 2.3.5 | Evaluate juniper-data-client notes/ for additions | Review: `juniper-data-client_OTHER_DEPENDENCIES.md`, `POLYREPO_MIGRATION_PLAN.md`. Extract client-specific patterns and migration notes. |
| 2.3.6 | Evaluate juniper-cascor-client notes/ for additions | Review: `juniper-cascor-client_OTHER_DEPENDENCIES.md`. Extract WebSocket-specific patterns and troubleshooting. |
| 2.3.7 | Evaluate juniper-cascor-worker notes/ for additions | Review: `juniper-cascor-worker_OTHER_DEPENDENCIES.md`, `FIX_TEST_IMPORT_MOCKING_PLAN.md`. Extract worker-specific testing patterns and distributed training procedures. |
| 2.3.8 | Evaluate juniper-deploy notes/ for additions | Review: `DOCKER_PYTHON_314_MIGRATION_PLAN.md`, `CONTAINER_VALIDATION_CI_PLAN.md`, `FIX_CONFTEST_IMPORT_PLAN.md`. Extract Docker-specific procedures, container validation, and Python 3.14 migration notes. |

### 2.4 Validate Cheatsheets Against Codebases

**Objective**: Use sub-agents to perform an in-depth review of each per-project cheatsheet against the actual project architecture, codebase state, and procedures.

#### Tasks

| ID | Task | Details | Sub-Agent |
|----|------|---------|-----------|
| 2.4.1 | Validate juniper-ml cheatsheet | Verify: `wake_the_claude.bash` flags and modes match documented behavior, PyPI extras in `pyproject.toml` match documented extras, SOPS procedures match actual `.sops.yaml` configuration, test commands produce expected output. | Yes — Explore agent per project |
| 2.4.2 | Validate juniper-cascor cheatsheet | Verify: API endpoint paths match FastAPI router definitions, service startup commands work, env var names match code references, pytest markers match `conftest.py` definitions, Prometheus metric names match instrumented code, HDF5 schema matches serialization code. | Yes |
| 2.4.3 | Validate juniper-data cheatsheet | Verify: API endpoints match FastAPI routes, generator names match registered generators, storage backends match implementation, ruff config matches `pyproject.toml`, test markers match conftest. | Yes |
| 2.4.4 | Validate juniper-canopy cheatsheet | Verify: Dash layout matches documented components, CasCor integration endpoints match client usage, demo mode startup matches documented procedure, env var names match code, test markers match conftest. | Yes |
| 2.4.5 | Validate juniper-data-client cheatsheet | Verify: Client API methods match `JuniperDataClient` class definition, exception types match code, `FakeJuniperDataClient` interface matches. | Yes |
| 2.4.6 | Validate juniper-cascor-client cheatsheet | Verify: REST methods match `CascorClient` class, WebSocket stream interface matches code, exception hierarchy matches. | Yes |
| 2.4.7 | Validate juniper-cascor-worker cheatsheet | Verify: CLI options match `argparse`/`click` definitions, `WorkerConfig` fields match dataclass, env var names match code. | Yes |
| 2.4.8 | Validate juniper-deploy cheatsheet | Verify: Docker Compose profiles match `docker-compose.yml`, Makefile targets match `Makefile`, service ports match compose config, health endpoints match container healthchecks. | Yes |

### 2.5 Update and Finalize

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 2.5.0 | Consolidate sub-agent validation findings | Collect all findings from the 8 validation sub-agents (2.4.1–2.4.8) into a single corrections backlog. Prioritize corrections by risk: (1) incorrect API endpoints or commands that would cause errors, (2) stale configuration values, (3) missing cross-references, (4) formatting/style inconsistencies. |
| 2.5.1 | Apply validation corrections | Fix all issues identified by sub-agent validation (2.4.x tasks), working from the prioritized corrections backlog. |
| 2.5.2 | Update each project's DOCUMENTATION_OVERVIEW.md | Add the new `DEVELOPER_CHEATSHEET.md` to the documentation index in each project. |
| 2.5.3 | Deprecate master cheatsheet | Add a deprecation header to `juniper-ml/notes/DEVELOPER_CHEATSHEET.md` pointing to the per-project files. Move the file to `juniper-ml/notes/history/DEVELOPER_CHEATSHEET.md` once all per-project files are validated. |

---

## Phase 3: Documentation Consistency Audit

**Priority**: HIGH — Ecosystem-wide quality
**Estimated Scope**: All 8 projects' `docs/` and `notes/` directories
**Dependencies**: Phase 1 (standards), Phase 2 (cheatsheets provide additional context)
**Status**: **MOSTLY COMPLETE** (2026-03-15) — 3.1 done, 3.2.1 done, 3.3.1-3.3.2/3.3.5 done, 3.4 done. Remaining: 3.2.2-3.2.8 (content structure audits), 3.3.3-3.3.4/3.3.6-3.3.7 (stale notes classification, history org, PR docs, MCP guides)

### 3.1 Standardize docs/ Directory Structures

**Objective**: Bring all project `docs/` directories into alignment with the tier model defined in Phase 1.2.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 3.1.1 | Rename juniper-cascor `ci/` → `ci_cd/` | **COMPLETE.** Renamed 5 files, updated 16 references across 5 files. Committed `3086ea0`. |
| 3.1.2 | Rename juniper-cascor lowercase files to UPPER_SNAKE_CASE | **COMPLETE.** Renamed 22 files across 6 subdirectories. Updated 187 references across 14 files. Updated naming convention docs in DOCUMENTATION_OVERVIEW.md. Committed `aad820b`. |
| 3.1.3 | Resolve juniper-canopy duplicate ADR | **COMPLETE.** Deleted redirect stub `docs/ADR_001_VALID_TEST_SKIPS.md`, fixed broken reference in `TEST_DIRECTORY_STRUCTURE.md`. Committed `6955d40`. |
| 3.1.4 | Populate juniper-deploy `docs/testing/` | **RESOLVED.** Directory already contains `TESTING_QUICK_START.md` (115 lines). Not empty as originally assumed. |
| 3.1.5 | Add ENVIRONMENT_SETUP.md to juniper-cascor | **COMPLETE.** Created redirect stub pointing to `install/environment-setup.md`. Committed `3086ea0`. |
| 3.1.6 | Add USER_MANUAL.md to juniper-cascor | **COMPLETE.** Created redirect stub pointing to `install/user-manual.md`. Committed `3086ea0`. |

### 3.2 Audit docs/ File Content

**Objective**: Ensure documentation files across projects are comparable in structure, depth, and formatting.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 3.2.1 | Audit all DOCUMENTATION_OVERVIEW.md files | Compare structure and completeness across all 8 projects. Ensure each: lists all docs in the project, includes an "I Want To" quick-reference table, links to ecosystem context, follows consistent formatting. |
| 3.2.2 | Audit all QUICK_START.md files | Ensure each follows the same pattern: Prerequisites → Install → Run → Verify → Next Steps. Verify all commands execute correctly. |
| 3.2.3 | Audit all REFERENCE.md files | Ensure consistent structure: Configuration Reference → CLI/API Reference → Environment Variables → Project Structure → Version Compatibility. |
| 3.2.4 | Audit all ENVIRONMENT_SETUP.md files | (Service + Orchestration tiers only) Ensure consistent structure: System Prerequisites → Conda/venv Setup → Dependency Installation → Configuration → Verification. |
| 3.2.5 | Audit all USER_MANUAL.md files | (Service + Orchestration tiers only) Ensure consistent structure: Introduction → Core Concepts → Usage Patterns → Advanced Configuration → Troubleshooting. |
| 3.2.6 | Audit testing/ subdirectory docs | Compare juniper-cascor, juniper-data, juniper-canopy testing docs. Standardize file names and content structure. Ensure all include: quick start, markers reference, fixtures reference, coverage requirements. |
| 3.2.7 | Audit ci_cd/ subdirectory docs | Compare across projects. Standardize file names (`CICD_QUICK_START.md`, `CICD_MANUAL.md`, `CICD_REFERENCE.md`). Ensure all include: pipeline overview, hook configuration, workflow reference. |
| 3.2.8 | Audit api/ subdirectory docs | Compare juniper-cascor, juniper-data, juniper-canopy API docs. Standardize: endpoint reference format, schema documentation, authentication documentation, error handling documentation. |

### 3.3 Audit notes/ Directory Content

**Objective**: Evaluate all notes/ files across projects for accuracy, relevance, and proper organization.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 3.3.1 | Audit procedural docs across all projects | Verify these files are present and consistent in all 8 projects: `WORKTREE_SETUP_PROCEDURE.md`, `WORKTREE_CLEANUP_PROCEDURE.md` (or V2), `THREAD_HANDOFF_PROCEDURE.md`. Identify version drift between copies. |
| 3.3.2 | Audit dependency docs across all projects | Verify presence and accuracy of: `DEPENDENCY_UPDATE_WORKFLOW.md`, `CONDA_DEPENDENCY_FILE_HEADER.md`, `PIP_DEPENDENCY_FILE_HEADER.md`, `*_OTHER_DEPENDENCIES.md`. |
| 3.3.3 | Identify and classify stale notes | For each project, classify every file in `notes/` as: ACTIVE (current, referenced), HISTORICAL (should be in `history/`), or OBSOLETE (should be deleted). |
| 3.3.4 | Verify history/ subdirectory organization | Ensure all projects with historical docs have a `notes/history/` directory and that superseded documents have been properly moved there. |
| 3.3.5 | Verify templates/ subdirectory consistency | Compare `notes/templates/` across projects. Standardize the template set: `TEMPLATE_DEVELOPMENT_ROADMAP.md`, `TEMPLATE_ISSUE_TRACKING.md`, `TEMPLATE_PULL_REQUEST_DESCRIPTION.md`, `TEMPLATE_RELEASE_NOTES.md`, `TEMPLATE_SECURITY_RELEASE_NOTES.md`. |
| 3.3.6 | Verify pull_requests/ subdirectory organization | Ensure all PR documentation is properly filed in `notes/pull_requests/`. Check for PR docs that should exist but are missing based on git history. |
| 3.3.7 | Audit MCP/setup guides | Compare `mcp/` or `setup_config_guides/` subdirectories across projects (juniper-cascor, juniper-data, juniper-canopy). Standardize guide format and verify tool references are current. |

### 3.4 Cross-Project Documentation Alignment

**Objective**: Ensure documentation that references other projects is accurate and up-to-date.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 3.4.1 | Validate all cross-project links | Check every documentation link that references another Juniper project (e.g., `../juniper-data/notes/DEPENDENCY_UPDATE_WORKFLOW.md`). Verify the target file exists and the link path is correct. |
| 3.4.2 | Validate ecosystem references | Check that all references to service ports, conda environments, dependency relationships, and environment variables are consistent across projects. |
| 3.4.3 | Validate AGENTS.md consistency | Compare `AGENTS.md` across all 8 projects. Ensure shared sections (worktree procedures, thread handoff, naming conventions) are identical or intentionally differentiated. |
| 3.4.4 | Verify CLAUDE.md symlinks | Confirm `CLAUDE.md` is a proper symlink to `AGENTS.md` in all 8 projects (not a file copy — this was a known V2 audit issue). |

---

## Phase 4: Post-Release Development Roadmap Audit

**Priority**: MEDIUM — Strategic planning
**Estimated Scope**: 3 existing roadmaps + 4 potential new roadmaps
**Dependencies**: Phases 2–3 (leverage documentation analysis for context)
**Status**: **COMPLETE** (2026-03-15)

### 4.1 Audit Existing Roadmaps

**Objective**: Perform a full audit of the 3 existing post-release development roadmap files.

#### Roadmap Inventory

| Project | File | Size | Tasks | Last Updated | Prioritization |
|---------|------|------|-------|--------------|----------------|
| juniper-cascor | `notes/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` | 105,435 lines | 83 items | 2026-02-25 | P0–P4 (Critical → Deferred) |
| juniper-data | `notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` | 787 lines | ~30 items | 2026-02-25 | Phase 1–5 + Priority labels |
| juniper-canopy | `notes/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` | 1,044 lines | ~55 items | 2026-02-25 | Phase 0–4 (Critical → Future) |

#### Tasks

| ID | Task | Details | Sub-Agent |
|----|------|---------|-----------|
| 4.1.1 | Audit juniper-cascor roadmap | For each of the 83 items: (a) verify continued relevance by checking if the issue still exists in the codebase, (b) assess description accuracy against current code, (c) evaluate scope/difficulty changes since the roadmap was written, (d) assess prioritization shifts based on current project state, (e) identify dependency changes between items. Particular focus on P0/P1 items (11 total). | Yes — dedicated sub-agent |
| 4.1.2 | Audit juniper-data roadmap | For each of the ~30 items: same evaluation criteria as 4.1.1. Verify Phase 3 (Client Library Publication) completion status. Assess impact of v0.4.2 release on remaining items. Cross-reference with `releases/RELEASE_NOTES_v0.4.2.md`. | Yes |
| 4.1.3 | Audit juniper-canopy roadmap | For each of the ~55 items: same evaluation criteria as 4.1.1. Focus on Phase 0 (Critical Integration Gaps) — verify which items have been resolved since 2026-02-25. Cross-reference with `development/IMPLEMENTATION_PLAN.md` and `development/DEVELOPMENT_ROADMAP.md`. | Yes |
| 4.1.4 | Cross-reference roadmaps | Identify items that span multiple roadmaps (e.g., CasCor ↔ Canopy integration items). Verify consistency of scope/priority/status across roadmaps for shared work items. | Yes |

### 4.2 Evaluate Roadmap Approach Details

**Objective**: For each roadmap task, evaluate and update the documented implementation approach.

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 4.2.1 | Evaluate juniper-cascor implementation approaches | For P0–P2 items (33 total): review the documented implementation approach, assess whether the approach is still viable given codebase evolution, identify alternative approaches discovered through documentation audit work, update approach details with specific file paths and code references. |
| 4.2.2 | Evaluate juniper-data implementation approaches | For Phase 1–2 items (HIGH priority): same evaluation. Leverage knowledge of ruff migration completion, 99.40% test coverage, and 659 existing tests to refine approaches. |
| 4.2.3 | Evaluate juniper-canopy implementation approaches | For Phase 0–1 items: same evaluation. Account for Cassandra/Redis integration status, demo mode stability, and CasCor backend integration state. |

### 4.3 Determine Roadmap Needs for Remaining Projects

**Objective**: Assess whether the 4 projects without roadmaps (juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy) need post-release development roadmaps.

#### Tasks

| ID | Task | Details | Sub-Agent |
|----|------|---------|-----------|
| 4.3.1 | Assess juniper-data-client roadmap need | Evaluate: number of open issues/TODOs in codebase, feature gaps compared to juniper-data API surface, test coverage state, CI/CD maturity. Recommend: create roadmap, defer, or document that no roadmap is needed. | Yes |
| 4.3.2 | Assess juniper-cascor-client roadmap need | Same evaluation. Special attention to: WebSocket streaming completeness, REST endpoint coverage relative to juniper-cascor API surface. | Yes |
| 4.3.3 | Assess juniper-cascor-worker roadmap need | Same evaluation. Special attention to: distributed training feature completeness, integration with juniper-cascor. | Yes |
| 4.3.4 | Assess juniper-deploy roadmap need | Same evaluation. Special attention to: Docker Compose profile completeness, Python 3.14 migration plan status (`DOCKER_PYTHON_314_MIGRATION_PLAN.md`), container validation CI plan status. | Yes |
| 4.3.5 | Create roadmaps where justified | For any project where the assessment recommends a roadmap, create it using the `TEMPLATE_DEVELOPMENT_ROADMAP.md` template with findings from the assessment. |

### 4.4 Update and Finalize Roadmaps

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 4.4.1 | Apply all audit corrections to juniper-cascor roadmap | Update item statuses, descriptions, priorities, dependencies, and implementation approaches based on 4.1.1 and 4.2.1 findings. |
| 4.4.2 | Apply all audit corrections to juniper-data roadmap | Same, based on 4.1.2 and 4.2.2 findings. |
| 4.4.3 | Apply all audit corrections to juniper-canopy roadmap | Same, based on 4.1.3 and 4.2.3 findings. |
| 4.4.4 | Add document history entries | Each updated roadmap gets a new document history entry recording: date, auditor (this plan), changes made, validation method. |
| 4.4.5 | Archive superseded roadmap versions | Move pre-audit versions to `notes/history/` with date-stamped filenames. |

---

## Phase 5: Validation and Cross-Referencing

**Priority**: MEDIUM — Quality assurance
**Estimated Scope**: All deliverables from Phases 2–4
**Dependencies**: Phases 2, 3, and 4 complete

### 5.1 Final Documentation Validation

#### Tasks

| ID | Task | Details | Sub-Agent |
|----|------|---------|-----------|
| 5.1.1 | Validate all new DEVELOPER_CHEATSHEET.md files | Re-run validation (per 2.4.x) on all 8 per-project cheatsheets after corrections from Phase 2.5. | Yes — 8 parallel sub-agents |
| 5.1.2 | Validate all renamed/moved files | Verify no broken links were introduced by Phase 3.1 renames (juniper-cascor file renames, subdirectory standardization). | Yes |
| 5.1.3 | Validate all updated roadmaps | Verify roadmap item statuses against codebase (spot-check at minimum P0/P1 items for each roadmap). | Yes |
| 5.1.4 | Run link validation across all projects | Check all internal documentation links (markdown anchors, relative paths, cross-project references) for validity. | Yes |

### 5.2 Documentation Index Updates

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 5.2.1 | Update all DOCUMENTATION_OVERVIEW.md files | Ensure every project's overview reflects the final state of its `docs/` directory, including new cheatsheet files and any renames/restructures from Phase 3. |
| 5.2.2 | Update parent Juniper CLAUDE.md | If documentation standards or cross-project conventions were changed, update the parent ecosystem guide. |
| 5.2.3 | Update all AGENTS.md files | If any project's development commands, testing procedures, or conventions changed as a result of the audit, update the corresponding `AGENTS.md`. |

### 5.3 Final Report

#### Tasks

| ID | Task | Details |
|----|------|---------|
| 5.3.1 | Generate audit summary report | Create a summary document in `juniper-ml/notes/` recording: total files created, modified, moved, or deleted; key findings; remaining known issues; recommendations for ongoing documentation maintenance. |
| 5.3.2 | Update this plan with completion status | Mark each task in this plan as COMPLETE, DEFERRED, or N/A with brief notes. |
| 5.3.3 | Document recovery procedure | Record the recovery steps for Phase 3 structural changes: if renames cause widespread link breakage, revert the commit(s) in affected worktrees, re-plan the renames with corrected link updates, and re-execute. Each Phase 3 rename batch should be a separate commit to enable granular revert. |
| 5.3.4 | Establish ongoing maintenance guidance | Document in each project's `DOCUMENTATION_OVERVIEW.md`: (a) when to update the cheatsheet (any time a procedure, command, or config changes), (b) when to update the roadmap (each sprint/release cycle), (c) the documentation standards reference location (Phase 1.2.5 output). |

---

## Dependency Graph

```
Phase 1: Prerequisites and Foundation
├── 1.1 Resolve V2 Audit Blockers
├── 1.2 Establish Documentation Standards
└── 1.3 Validate Working Environment
      │
      ▼
Phase 2: DEVELOPER_CHEATSHEET.md Decomposition ──────┐
├── 2.1 Audit Master Cheatsheet                       │
├── 2.2 Create Per-Project Files                      │
├── 2.3 Augment with Project Content                  │
├── 2.4 Validate Against Codebases [sub-agents ×8]    │
└── 2.5 Update and Finalize                           │
      │                                               │
      ▼                                               ▼
Phase 3: Documentation Consistency Audit ◄────────────┘
├── 3.1 Standardize docs/ Structures
├── 3.2 Audit docs/ File Content
├── 3.3 Audit notes/ Directory Content
└── 3.4 Cross-Project Alignment
      │
      ▼
Phase 4: Roadmap Audit (can start in parallel with Phase 3.2+)
├── 4.1 Audit Existing Roadmaps [sub-agents ×3]
├── 4.2 Evaluate Approach Details
├── 4.3 Assess Remaining Projects [sub-agents ×4]
└── 4.4 Update and Finalize
      │
      ▼
Phase 5: Validation and Cross-Referencing
├── 5.1 Final Validation [sub-agents ×8+]
├── 5.2 Documentation Index Updates
└── 5.3 Final Report
```

### Critical Path

```
1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 3.1 → 3.4 → 5.1 → 5.2 → 5.3
```

### Phase 3/4 Overlap Clarification

Phase 4 (Roadmap Audit) may begin once **Phase 3.1** (structural standardization) is **planned** — the renames do not need to be fully executed. Specifically:

- **4.1.x (roadmap audits)** can start as soon as Phase 2.5 is complete, since they only read roadmap files and codebase state
- **4.3.x (roadmap-need assessments)** can start in parallel with Phase 3.2+
- **4.4.x (roadmap updates)** should wait until Phase 3.1 renames are committed, to avoid writing content with stale file references

### Parallelization Opportunities

| Parallel Group | Tasks | Notes |
|----------------|-------|-------|
| **Phase 2 drafting** | 2.2.1 through 2.2.8 | All 8 cheatsheets can be drafted concurrently |
| **Phase 2 augmentation** | 2.3.1 through 2.3.8 | All 8 project-specific evaluations run concurrently |
| **Phase 2 validation** | 2.4.1 through 2.4.8 | All 8 sub-agent validations run concurrently |
| **Phase 3 content audit** | 3.2.1 through 3.2.8 | File-type audits are independent |
| **Phase 3 + Phase 4 overlap** | 3.2.x, 3.3.x with 4.1.x | Roadmap audit can begin once Phase 3.1 structural changes are planned (not necessarily complete) |
| **Phase 4 roadmap audits** | 4.1.1 through 4.1.3 | All 3 existing roadmap audits run concurrently |
| **Phase 4 assessments** | 4.3.1 through 4.3.4 | All 4 roadmap-need assessments run concurrently |
| **Phase 5 validation** | 5.1.1 through 5.1.4 | All validation tasks run concurrently |

---

## Execution Notes

### Sub-Agent Usage Strategy

This plan leverages sub-agents extensively for parallelizable, independent work:

| Phase | Sub-Agent Count | Purpose |
|-------|----------------|---------|
| 2.4 | 8 (parallel) | Validate each cheatsheet against its project's codebase |
| 4.1 | 3 (parallel) | Audit each existing roadmap against its project's codebase |
| 4.3 | 4 (parallel) | Assess roadmap needs for projects without roadmaps |
| 5.1 | 8+ (parallel) | Final validation of all deliverables |

**Total sub-agent invocations**: ~23 (many parallelizable into ~6 rounds)

### Worktree Strategy

Each project modification should be performed in an isolated worktree per the Juniper worktree procedures. For efficiency, batch changes per project:

- **Round 1**: Create worktrees in all 8 projects
- **Round 2**: Perform all Phase 2 + 3 changes per project in its worktree
- **Round 3**: Phase 4 roadmap changes in the 3–7 affected project worktrees
- **Round 4**: Phase 5 validation and final corrections
- **Round 5**: PR creation and worktree cleanup

### Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Master cheatsheet content is stale | Phase 2.4 validation catches all inaccuracies before finalizing |
| Renames break cross-project links | Phase 3.4 + Phase 5.1.2 validate all links post-change |
| Roadmap items already completed | Phase 4.1 sub-agents verify each item against current codebase |
| Documentation drift after audit | Phase 1.2.5 establishes ongoing standards; DOCUMENTATION_OVERVIEW.md in each project serves as living index |
| V2 audit blockers unresolved | Phase 1.1 explicitly gates all subsequent work on V2 resolution |

### Estimated Task Count

| Phase | Tasks | Sub-Agent Tasks | Total |
|-------|-------|-----------------|-------|
| Phase 1 | 12 | 0 | 12 |
| Phase 2 | 26 | 9 | 35 |
| Phase 3 | 19 | 0 | 19 |
| Phase 4 | 16 | 7 | 23 |
| Phase 5 | 9 | 4+ | 13 |
| **Total** | **82** | **20** | **102** |
