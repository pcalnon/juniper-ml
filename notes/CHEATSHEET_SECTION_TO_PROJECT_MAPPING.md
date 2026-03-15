# Cheatsheet Section-to-Project Mapping

## Reference Document for Per-Project Cheatsheet Drafting

| Meta Data         | Value                                                               |
|-------------------|---------------------------------------------------------------------|
| **Source:**        | `notes/DEVELOPER_CHEATSHEET.md` (v1.3.0, 1425 lines)              |
| **Phase:**         | 2.1 -- Section-to-Project Mapping                                  |
| **Created:**       | 2026-03-15                                                         |
| **Purpose:**       | Guide 8 parallel sub-agents drafting per-project cheatsheets       |

---

## Table of Contents

- [Section Mapping Table (Summary)](#section-mapping-table-summary)
- [Detailed Section Analysis](#detailed-section-analysis)
  - [Front Matter](#1-front-matter)
  - [Secrets](#2-secrets)
  - [API Endpoints](#3-api-endpoints)
  - [Clients](#4-clients)
  - [Services](#5-services)
  - [Testing](#6-testing)
  - [Claude Automation Script](#7-claude-automation-script)
  - [Dependencies](#8-dependencies)
  - [Configuration](#9-configuration)
  - [Logging and Observability](#10-logging-and-observability)
  - [CI/CD and Pre-commit](#11-cicd-and-pre-commit)
  - [Claude Code Session Script](#12-claude-code-session-script)
  - [Git Worktrees](#13-git-worktrees)
  - [Claude Automation Scripts (duplicate section)](#14-claude-automation-scripts-duplicate-section)
  - [Data Contract](#15-data-contract)
  - [Quick Reference Tables](#16-quick-reference-tables)
  - [Docker](#17-docker)
- [Duplicate Content Inventory](#duplicate-content-inventory)
- [Ecosystem-Level Content (juniper-ml cheatsheet)](#ecosystem-level-content-juniper-ml-cheatsheet)
- [Content to REMOVE](#content-to-remove)
- [Content to ADD (Known Gaps)](#content-to-add-known-gaps)

---

## Section Mapping Table (Summary)

| # | Section | Lines | Primary Project | Secondary Projects |
|---|---------|-------|-----------------|--------------------|
| 1 | Front Matter (header, TOC) | 1--101 | juniper-ml (ecosystem) | -- |
| 2 | Secrets | 104--194 | juniper-deploy | juniper-data, juniper-cascor, juniper-canopy, juniper-ml (ecosystem) |
| 3 | API Endpoints | 197--262 | juniper-data | juniper-cascor, juniper-cascor-client, juniper-canopy |
| 4 | Clients | 265--316 | juniper-data-client | juniper-cascor-client |
| 5 | Services | 319--427 | juniper-deploy | juniper-data, juniper-cascor, juniper-canopy |
| 6 | Testing | 430--481 | juniper-ml (ecosystem) | all repos |
| 7 | Claude Automation Script | 484--623 | juniper-ml | -- |
| 8 | Dependencies | 626--662 | juniper-ml (ecosystem) | all repos |
| 9 | Configuration | 665--695 | split: juniper-data, juniper-cascor, juniper-canopy | juniper-deploy |
| 10 | Logging and Observability | 698--857 | split: juniper-deploy (obs stack), per-service (log config) | juniper-data, juniper-cascor, juniper-canopy |
| 11 | CI/CD and Pre-commit | 860--925 | juniper-ml (ecosystem) | all repos |
| 12 | Claude Code Session Script | 928--1176 | juniper-ml | -- |
| 13 | Git Worktrees | 1179--1216 | juniper-ml (ecosystem) | all repos |
| 14 | Claude Automation Scripts (dup) | 1219--1270 | juniper-ml | -- |
| 15 | Data Contract | 1272--1306 | juniper-data | juniper-data-client |
| 16 | Quick Reference Tables | 1309--1345 | juniper-ml (ecosystem) | -- |
| 17 | Docker | 1348--1425 | juniper-deploy | juniper-data, juniper-cascor, juniper-canopy |

---

## Detailed Section Analysis

### 1. Front Matter

**Lines:** 1--101
**Headings:** `# Juniper Developer Cheatsheet`, `## Quick-Reference Procedures...`, `## Table of Contents`
**Primary target:** juniper-ml (ecosystem cheatsheet)
**Secondary:** None
**Accuracy:** Current. Version 1.3.0 matches footer. Last Updated says "March 8, 2026" in header but "March 11, 2026" in footer (line 1423) -- minor inconsistency.
**Content to ADD:** None. Each per-project cheatsheet will have its own front matter and TOC.

---

### 2. Secrets

#### 2a. View Current Secrets
**Lines:** 106--114
**Primary:** juniper-deploy
**Secondary:** juniper-ml (ecosystem)
**Accuracy:** Current. SOPS command is correct.

#### 2b. Add a New Secret
**Lines:** 116--125
**Primary:** juniper-deploy
**Secondary:** juniper-ml (ecosystem)
**Accuracy:** Current.

#### 2c. Change an Existing Secret
**Lines:** 127--131
**Primary:** juniper-deploy
**Secondary:** juniper-ml (ecosystem)
**Accuracy:** Current (delegates to "Add" procedure).

#### 2d. Remove a Secret
**Lines:** 133--142
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy (code references)
**Accuracy:** Current.

#### 2e. Enable API Key Authentication
**Lines:** 144--161
**Primary:** juniper-deploy (orchestration)
**Secondary:** juniper-data (server-side), juniper-cascor (server-side), juniper-canopy (server-side), juniper-data-client (client-side), juniper-cascor-client (client-side)
**Accuracy:** Current. Env var names are correct per AGENTS.md references.

#### 2f. Disable API Key Authentication
**Lines:** 163--171
**Primary:** juniper-deploy
**Secondary:** juniper-data
**Accuracy:** Current.

#### 2g. Add SOPS to a New Repo
**Lines:** 173--182
**Primary:** juniper-ml (ecosystem procedure)
**Secondary:** All repos
**Accuracy:** Current.

#### 2h. Rotate the SOPS Age Key
**Lines:** 184--193
**Primary:** juniper-ml (ecosystem procedure)
**Secondary:** All 8 repos
**Accuracy:** Current. Correctly notes all 8 repos need updating.

**Whole-section content to ADD:** None identified.

---

### 3. API Endpoints

#### 3a. Add an Endpoint to juniper-data
**Lines:** 199--208
**Primary:** juniper-data
**Secondary:** juniper-data-client (consumer update)
**Accuracy:** Current. Path `juniper_data/api/routes/` and registration pattern are correct.

#### 3b. Add an Endpoint to juniper-cascor
**Lines:** 210--214
**Primary:** juniper-cascor
**Secondary:** juniper-cascor-client (consumer update)
**Accuracy:** Current but thin. States "same pattern as juniper-data" without CasCor-specific route paths.
**Content to ADD:** CasCor-specific route directory path. HDF5-related endpoints if applicable.

#### 3c. Add a WebSocket Endpoint
**Lines:** 216--224
**Primary:** juniper-cascor
**Secondary:** juniper-cascor-client, juniper-canopy
**Accuracy:** Current. References `/ws/training` and `/ws/control`.
**Content to ADD:** WebSocket message schema details (known gap for juniper-cascor-client cheatsheet).

#### 3d. Change an Existing Endpoint
**Lines:** 226--235
**Primary:** juniper-ml (ecosystem -- cross-repo procedure)
**Secondary:** juniper-data, juniper-cascor, juniper-data-client, juniper-cascor-client, juniper-canopy
**Accuracy:** Current. Correctly identifies cross-repo CI dispatch events.

#### 3e. Remove an Endpoint
**Lines:** 237--245
**Primary:** juniper-ml (ecosystem)
**Secondary:** juniper-data, juniper-cascor
**Accuracy:** Current.

#### 3f. Add Request/Response Models
**Lines:** 247--251
**Primary:** juniper-data
**Secondary:** juniper-cascor, juniper-canopy
**Accuracy:** Current. Correctly distinguishes Pydantic v2 (data) vs dataclasses (cascor network config).

#### 3g. Add Middleware
**Lines:** 253--261
**Primary:** juniper-data
**Secondary:** None
**Accuracy:** Current. Middleware stack order documented.

**Whole-section content to ADD:**
- juniper-cascor: HDF5 checkpoint save/load endpoints
- juniper-cascor-client: WebSocket message schemas (metrics, state, topology, cascade_add, event)

---

### 4. Clients

#### 4a. Add a Method to juniper-data-client
**Lines:** 267--275
**Primary:** juniper-data-client
**Secondary:** None
**Accuracy:** Current. Pattern `self._session.get/post(...)` is correct.
**Content to ADD:** FakeClient test double pattern (known gap).

#### 4b. Add a Method to juniper-cascor-client
**Lines:** 277--281
**Primary:** juniper-cascor-client
**Secondary:** None
**Accuracy:** Current. References `client.py` (REST) and `ws_client.py` (WebSocket).
**Content to ADD:** WebSocket message schema details (known gap).

#### 4c. Add a WebSocket Event Handler
**Lines:** 283--291
**Primary:** juniper-cascor-client
**Secondary:** juniper-canopy (consumer)
**Accuracy:** Current. Message types listed: metrics, state, topology, cascade_add, event.

#### 4d. Change a Client Method
**Lines:** 293--300
**Primary:** juniper-data-client
**Secondary:** juniper-cascor-client
**Accuracy:** Current.

#### 4e. Remove a Client Method
**Lines:** 302--309
**Primary:** juniper-data-client
**Secondary:** juniper-cascor-client
**Accuracy:** Current.

#### 4f. Change Client Retry/Timeout Defaults
**Lines:** 311--315
**Primary:** juniper-data-client
**Secondary:** juniper-cascor-client
**Accuracy:** Current. Correctly references `requests.Session` with `urllib3.Retry`.

**Whole-section content to ADD:**
- juniper-data-client: FakeClient pattern for testing without a live server
- juniper-cascor-client: WebSocket schemas for each message type
- Both clients: Error handling / exception hierarchy

---

### 5. Services

#### 5a. Start the Full Stack (Docker)
**Lines:** 321--330
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current. `make up` and `docker compose --profile full up -d` both documented.

#### 5b. Start in Demo Mode
**Lines:** 332--341
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current.

#### 5c. Start in Dev Mode
**Lines:** 343--352
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current.

#### 5d. Add a New Docker Service
**Lines:** 354--363
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current. Profile assignment correctly documented.
**Content to ADD:** Networking configuration (known gap for juniper-deploy).

#### 5e. Change a Service Port
**Lines:** 365--374
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy (constants), juniper-ml (parent AGENTS.md)
**Accuracy:** Current. Complete checklist.

#### 5f. Add an Environment Variable to a Service
**Lines:** 376--383
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current.

#### 5g. Run a Service Natively (No Docker)
**Lines:** 385--407
**Primary:** Split across juniper-data, juniper-cascor, juniper-canopy
**Secondary:** juniper-deploy (alternative)
**Accuracy:** Current. Conda environments and commands are correct.
**Content to ADD:** juniper-cascor-worker native run command (known gap).

#### 5h. Check Service Health
**Lines:** 409--426
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current. Health endpoints `/v1/health`, `/v1/health/live`, `/v1/health/ready` documented.

**Whole-section content to ADD:**
- juniper-deploy: Docker networking configuration (bridge network, service discovery)
- juniper-deploy: Volume mounts and persistent storage
- juniper-cascor-worker: How to start the worker (native and Docker)

---

### 6. Testing

#### 6a. Run Tests per Repo
**Lines:** 432--444
**Primary:** juniper-ml (ecosystem -- aggregated cross-repo table)
**Secondary:** Each individual repo gets its own row as per-project content
**Accuracy:** Current. Commands verified against AGENTS.md references.

#### 6b. Run Tests with Coverage
**Lines:** 446--459
**Primary:** juniper-ml (ecosystem)
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Mostly current. juniper-data states "95% aggregate, 85% per-module in CI" but the generic threshold shown is 80% -- this should be clarified per project.

#### 6c. Add a Pytest Marker
**Lines:** 461--469
**Primary:** juniper-ml (ecosystem)
**Secondary:** All repos with pytest
**Accuracy:** Current.

#### 6d. Run Specific Marker Subsets
**Lines:** 471--480
**Primary:** juniper-ml (ecosystem)
**Secondary:** juniper-cascor (re: `--run-long`)
**Accuracy:** Current.

**Whole-section content to ADD:**
- Per-project: Specific marker lists for each repo
- juniper-cascor: `--run-long` flag details
- juniper-canopy: Selective test guide reference
- juniper-data-client / juniper-cascor-client: FakeClient-based test patterns (known gap)

---

### 7. Claude Automation Script

#### 7a. Validate wake_the_claude.bash usage/help flags
**Lines:** 486--498
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 7b. Enable debug mode and verify clean stderr
**Lines:** 499--507
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 7c. Troubleshoot --resume validation failures
**Lines:** 509--561
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Thorough coverage of edge cases.

#### 7d. Troubleshoot --id UUID generation fallback
**Lines:** 563--588
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Fallback chain documented correctly.

#### 7e. Verify pattern-matching hardening (no eval)
**Lines:** 590--598
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 7f. Run wake_the_claude regression tests
**Lines:** 600--622
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Coverage highlights are accurate.

**Whole-section content to ADD:** None. This section is comprehensive for juniper-ml.

---

### 8. Dependencies

#### 8a. Add a Dependency
**Lines:** 628--635
**Primary:** juniper-ml (ecosystem -- generic procedure)
**Secondary:** All repos
**Accuracy:** Current. `uv pip compile` command is correct.

#### 8b. Remove a Dependency
**Lines:** 637--644
**Primary:** juniper-ml (ecosystem)
**Secondary:** All repos
**Accuracy:** Current.

#### 8c. Regenerate Lockfile
**Lines:** 646--652
**Primary:** juniper-ml (ecosystem)
**Secondary:** All repos
**Accuracy:** Current.

#### 8d. Add an Optional Dependency Group
**Lines:** 654--661
**Primary:** juniper-ml
**Secondary:** All repos
**Accuracy:** Current. Correctly references the juniper-ml meta-package.

**Whole-section content to ADD:**
- Per-project: Specific `pyproject.toml` dependency group names
- juniper-data: ruff vs black/isort distinction for dependency tooling

---

### 9. Configuration

#### 9a. Add a Setting to juniper-data
**Lines:** 667--674
**Primary:** juniper-data
**Secondary:** juniper-deploy
**Accuracy:** Current. pydantic-settings pattern documented.

#### 9b. Add a Constant to juniper-cascor
**Lines:** 676--682
**Primary:** juniper-cascor
**Secondary:** None
**Accuracy:** Current. Extended log levels documented. Module list includes `hdf5` which validates HDF5 constants exist.

#### 9c. Add a Config Entry to juniper-canopy
**Lines:** 684--694
**Primary:** juniper-canopy
**Secondary:** None
**Accuracy:** Current. 3-level config hierarchy correctly documented.
**Content to ADD:** Cassandra/Redis config entries (known gap for juniper-canopy).

**Whole-section content to ADD:**
- juniper-cascor-worker: Worker CLI/config settings (known gap)
- juniper-canopy: Cassandra and Redis configuration (known gap)

---

### 10. Logging and Observability

#### 10a. Change Log Level at Runtime
**Lines:** 700--712
**Primary:** Split: juniper-data, juniper-cascor, juniper-canopy (each gets its own env var)
**Secondary:** juniper-deploy (env var injection)
**Accuracy:** Current.

#### 10b. Enable JSON Logging
**Lines:** 714--724
**Primary:** Split: juniper-data, juniper-cascor, juniper-canopy
**Secondary:** juniper-deploy
**Accuracy:** Current.

#### 10c. Enable Sentry Error Tracking
**Lines:** 726--736
**Primary:** Split: juniper-data, juniper-cascor, juniper-canopy
**Secondary:** juniper-deploy
**Accuracy:** Current.

#### 10d. Enable Prometheus Metrics
**Lines:** 738--758
**Primary:** juniper-deploy (stack orchestration)
**Secondary:** juniper-data, juniper-cascor, juniper-canopy (per-service enable flag)
**Accuracy:** Current. 23 namespaced metrics, `make obs` targets.

#### 10e. Start Observability Stack
**Lines:** 760--775
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current.

#### 10f. View Grafana Dashboards
**Lines:** 777--788
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current. Four dashboards documented.

#### 10g. Metric Naming Convention
**Lines:** 790--802
**Primary:** juniper-ml (ecosystem convention)
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current.

#### 10h. Add a Custom Metric to a Service
**Lines:** 804--822
**Primary:** Split: juniper-data (example shown), juniper-cascor, juniper-canopy
**Secondary:** juniper-deploy (Grafana dashboard update)
**Accuracy:** Current.

#### 10i. Add a Grafana Dashboard
**Lines:** 824--831
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current.

#### 10j. Query Prometheus Directly
**Lines:** 833--846
**Primary:** juniper-deploy
**Secondary:** None
**Accuracy:** Current.

#### 10k. Troubleshoot Missing Metrics
**Lines:** 848--856
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current.

**Whole-section content to ADD:**
- juniper-canopy: Cassandra/Redis health metrics (known gap)
- juniper-cascor: HDF5 checkpoint metrics (known gap)

---

### 11. CI/CD and Pre-commit

#### 11a. Run Pre-commit Locally
**Lines:** 862--872
**Primary:** juniper-ml (ecosystem)
**Secondary:** All repos
**Accuracy:** Current. Correctly distinguishes `ruff` (juniper-data) vs `black`+`isort`+`flake8` (others).

#### 11b. Publish a Package to PyPI
**Lines:** 874--883
**Primary:** juniper-ml
**Secondary:** juniper-data-client, juniper-cascor-client, juniper-cascor-worker (publishable packages)
**Accuracy:** Current. OIDC trusted publishing noted.

#### 11c. Add a CI Job
**Lines:** 885--894
**Primary:** juniper-ml (ecosystem -- generic pattern)
**Secondary:** All repos
**Accuracy:** Current. Pipeline stages documented.

#### 11d. Validate Documentation Links Locally
**Lines:** 896--924
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Three modes (`skip`, `check`, `warn`) documented with correct commands.

#### 11e. Troubleshoot Cross-Repo Link Checks
**Lines:** 910--924
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

**Whole-section content to ADD:** None. Each per-project cheatsheet should include its repo-specific CI job names.

---

### 12. Claude Code Session Script

#### 12a. Entry Points
**Lines:** 930--949
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 12b. Use the Default Interactive Wrapper
**Lines:** 959--988
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** **FLAG -- INCONSISTENCY.** Lines 965--966 state the wrapper "does **not** include `--dangerously-skip-permissions` unless `CLAUDE_SKIP_PERMISSIONS=1` is set", but lines 971--972 state it "currently opts into `--dangerously-skip-permissions` by default." These contradict each other. Needs resolution.

#### 12c. Launch Modes: Interactive vs Headless
**Lines:** 990--1019
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Headless logging fallback chain documented.

#### 12d. Session ID and Resume Workflow (FIRST OCCURRENCE)
**Lines:** 1021--1057
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 12e. Current Argument-Handling Pitfalls (Known) (FIRST OCCURRENCE)
**Lines:** 1059--1075
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current.

#### 12f. Session ID and Resume Workflow, Claude Code Session Script (DUPLICATE)
**Lines:** 1077--1156
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** **DUPLICATE.** This is nearly identical to 12d (lines 1021--1057) plus 12e (lines 1059--1075). See [Duplicate Content Inventory](#duplicate-content-inventory) below.

#### 12g. Troubleshoot Resume Failures
**Lines:** 1158--1175
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** Current. Failure patterns table is accurate.

**Whole-section content to ADD:** None beyond deduplication.

---

### 13. Git Worktrees

#### 13a. Create a Worktree for a New Task
**Lines:** 1181--1199
**Primary:** juniper-ml (ecosystem procedure)
**Secondary:** All repos
**Accuracy:** Current. Commands match WORKTREE_SETUP_PROCEDURE.md.

#### 13b. Merge and Clean Up a Worktree
**Lines:** 1201--1215
**Primary:** juniper-ml (ecosystem procedure)
**Secondary:** All repos
**Accuracy:** **FLAG -- STALE.** This section shows a direct `git merge` + `git push origin main` workflow, but WORKTREE_CLEANUP_PROCEDURE_V2.md (referenced in CLAUDE.md) uses a PR-based workflow (`gh pr create`). The V2 procedure explicitly avoids direct merges to main. The cheatsheet should be updated to match V2 or at minimum note the PR-based approach.

**Whole-section content to ADD:**
- Reference to `scripts/worktree_cleanup.bash` automated cleanup script
- PR-based merge workflow from V2 procedure

---

### 14. Claude Automation Scripts (duplicate section)

#### 14a. Resume a Claude Session
**Lines:** 1219--1241
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** **DUPLICATE.** Overlaps significantly with Section 12d (Session ID and Resume Workflow) and Section 7c (Troubleshoot --resume validation failures). Contains the same resume validation rules and failure messages.

#### 14b. Generate and Save a Session ID File
**Lines:** 1252--1269
**Primary:** juniper-ml
**Secondary:** None
**Accuracy:** **DUPLICATE.** Overlaps with Section 12d (Session ID and Resume Workflow) lines 1026--1032.

**Whole-section content to ADD:** None -- this entire section should be merged into Section 12 and deduplicated.

---

### 15. Data Contract

#### 15a. Add a New Generator
**Lines:** 1274--1285
**Primary:** juniper-data
**Secondary:** juniper-data-client (consumer)
**Accuracy:** Current. Generator list (`spiral`, `xor`, `gaussian`, `circles`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`) should be verified against current codebase.
**Content to ADD:** juniper-data: Storage backend configuration (known gap -- filesystem, S3, etc.).

#### 15b. Download a Dataset Artifact
**Lines:** 1287--1305
**Primary:** juniper-data-client
**Secondary:** juniper-data (server)
**Accuracy:** Current. Python example is correct.

**Whole-section content to ADD:**
- juniper-data: Storage backends for artifact persistence (known gap)
- juniper-cascor: HDF5 checkpoint format and contract (known gap)

---

### 16. Quick Reference Tables

#### 16a. Service Ports
**Lines:** 1311--1317
**Primary:** juniper-ml (ecosystem)
**Secondary:** None
**Accuracy:** Current. Matches parent AGENTS.md.

#### 16b. Conda Environments
**Lines:** 1319--1325
**Primary:** juniper-ml (ecosystem)
**Secondary:** None
**Accuracy:** Current. Python 3.14 for all three.

#### 16c. Key Auth Environment Variables
**Lines:** 1327--1335
**Primary:** juniper-ml (ecosystem)
**Secondary:** juniper-data, juniper-cascor, juniper-canopy, juniper-data-client, juniper-cascor-client
**Accuracy:** Current.

#### 16d. Docker Compose Profiles
**Lines:** 1337--1344
**Primary:** juniper-deploy
**Secondary:** juniper-ml (ecosystem)
**Accuracy:** Current. Four profiles documented.

**Whole-section content to ADD:** Per-project cheatsheets should include their own relevant subset of these tables.

---

### 17. Docker

#### 17a. Add a Package to Docker Containers
**Lines:** 1350--1371
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current.

#### 17b. Upgrade a Package Version
**Lines:** 1373--1389
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current.

#### 17c. Upgrade Python Version in Docker
**Lines:** 1391--1419
**Primary:** juniper-deploy
**Secondary:** juniper-data, juniper-cascor, juniper-canopy
**Accuracy:** Current. Multi-stage build pattern documented.

**Whole-section content to ADD:**
- juniper-deploy: Docker networking configuration (known gap)
- juniper-deploy: Health check Python snippet pattern

---

## Duplicate Content Inventory

The following content appears more than once in the cheatsheet and must be deduplicated during the per-project drafting phase.

### Duplicate 1: "Session ID and Resume Workflow"

| Occurrence | Lines | Heading |
|------------|-------|---------|
| First | 1021--1057 | `### Session ID and Resume Workflow` |
| Second | 1077--1156 | `### Session ID and Resume Workflow, Claude Code Session Script` |

**Overlap:** Resume examples, validation rules, safety constraints, and argument-handling pitfalls are repeated nearly verbatim. The second occurrence (1077--1156) also duplicates "Current Argument-Handling Pitfalls (Known)" from lines 1059--1075, restated at 1138--1156.

**Resolution:** Consolidate into a single canonical "Session ID and Resume Workflow" section in the juniper-ml cheatsheet. The second occurrence adds "Session ID Files and Safety Constraints" (lines 1102--1117) which slightly expands on the first occurrence's "Safety constraints" (lines 1053--1057) -- merge these.

### Duplicate 2: "Claude Automation Scripts" section vs earlier content

| Occurrence | Lines | Heading |
|------------|-------|---------|
| First | 928--1175 | `## Claude Code Session Script` (full section) |
| Second | 1219--1270 | `## Claude Automation Scripts` |

**Overlap:** Section 14 ("Claude Automation Scripts") at lines 1219--1270 covers "Resume a Claude Session" and "Generate and Save a Session ID File", both of which are already covered in Section 12 ("Claude Code Session Script") subsections.

**Resolution:** Merge Section 14 content into Section 12. The failure-message table at lines 1245--1250 is a useful addition that should be preserved in the merged version.

### Duplicate 3: "Current Argument-Handling Pitfalls"

| Occurrence | Lines |
|------------|-------|
| First | 1059--1075 |
| Second | 1138--1156 |

**Resolution:** Keep only one instance. Content is identical except for one trailing sentence at line 1156.

---

## Ecosystem-Level Content (juniper-ml cheatsheet)

The following content does NOT belong to any single project and should remain in the juniper-ml ecosystem cheatsheet:

| Content | Source Lines | Rationale |
|---------|-------------|-----------|
| Front matter, TOC | 1--101 | Ecosystem overview |
| Secrets: SOPS procedures (view, add, change, remove, add to new repo, rotate key) | 104--193 | Cross-repo procedure (SOPS spans all repos) |
| API Endpoints: Change/Remove (cross-repo impact) | 226--245 | Cross-repo coordination procedure |
| Testing: Run Tests per Repo table | 432--444 | Aggregated cross-repo reference |
| Testing: Pytest markers (generic) | 461--480 | Shared convention |
| Claude Automation Script (entire section) | 484--622 | juniper-ml-owned scripts |
| Dependencies: Generic procedures | 626--662 | Shared convention |
| CI/CD: Generic procedures | 860--925 | Shared convention |
| Claude Code Session Script (entire section, deduplicated) | 928--1270 | juniper-ml-owned scripts |
| Git Worktrees (entire section) | 1179--1216 | Ecosystem procedure |
| Quick Reference Tables | 1309--1345 | Ecosystem summary |
| Metric Naming Convention | 790--802 | Shared convention |

---

## Content to REMOVE

| Content | Lines | Reason |
|---------|-------|--------|
| Second "Session ID and Resume Workflow" | 1077--1156 | Duplicate of 1021--1057 plus 1059--1075 |
| "Claude Automation Scripts" section | 1219--1270 | Duplicate of content in "Claude Code Session Script" section (928--1175) |
| Duplicate "Current Argument-Handling Pitfalls" | 1138--1156 | Duplicate of 1059--1075 |
| `--dangerously-skip-permissions` contradiction | 965--972 | Contradictory statements must be resolved, not just removed -- flag for correction |

### Worktree Cleanup: Stale Procedure

The "Merge and Clean Up a Worktree" section (lines 1201--1215) shows direct `git merge` to main, which contradicts the V2 cleanup procedure that uses PRs. This should be **corrected** (not removed) to match the V2 PR-based workflow.

---

## Content to ADD (Known Gaps)

These are content gaps identified from the task specification that should be filled in the per-project cheatsheets.

### juniper-cascor cheatsheet

| Gap | Description |
|-----|-------------|
| **HDF5 checkpoint format** | Add section: HDF5 checkpoint save/load, file format, keys, versioning |
| **HDF5 endpoints** | Add procedures for HDF5-related API endpoints if they exist |
| **HDF5 constants** | Document `src/cascor_constants/hdf5.py` module (already referenced at line 678) |
| **Training lifecycle** | CasCor training phases, cascade correlation algorithm specifics |

### juniper-data cheatsheet

| Gap | Description |
|-----|-------------|
| **Storage backends** | Add section: artifact storage configuration (filesystem, S3, etc.) |
| **Generator schemas** | Per-generator parameter schemas and validation |
| **ruff configuration** | juniper-data uses ruff instead of black/isort/flake8 -- document differences |

### juniper-canopy cheatsheet

| Gap | Description |
|-----|-------------|
| **Cassandra configuration** | Add section: Cassandra connection, keyspace setup, schema management |
| **Redis configuration** | Add section: Redis connection, caching patterns, session storage |
| **Dashboard layout** | Dash component hierarchy and callback patterns |

### juniper-data-client cheatsheet

| Gap | Description |
|-----|-------------|
| **FakeClient** | Add section: Using FakeClient for testing without a live juniper-data server |
| **Error handling** | Exception hierarchy and retry behavior |

### juniper-cascor-client cheatsheet

| Gap | Description |
|-----|-------------|
| **WebSocket message schemas** | Full schema documentation for each message type (metrics, state, topology, cascade_add, event) |
| **FakeClient** | Add section: Test double patterns for cascor-client |
| **Connection lifecycle** | WebSocket connection, reconnection, and teardown patterns |

### juniper-cascor-worker cheatsheet

| Gap | Description |
|-----|-------------|
| **Worker CLI/config** | Add section: CLI arguments, configuration file format, environment variables |
| **Distributed training** | Worker registration, task distribution, result aggregation |
| **Native run command** | How to start the worker outside Docker |

### juniper-deploy cheatsheet

| Gap | Description |
|-----|-------------|
| **Docker networking** | Bridge network configuration, service discovery, DNS resolution |
| **Volume mounts** | Persistent storage configuration for data and checkpoints |
| **Health check patterns** | Python-based health check snippet used across services |
| **Makefile targets** | Full reference of available `make` targets |

### juniper-ml (ecosystem) cheatsheet

| Gap | Description |
|-----|-------------|
| **Worktree cleanup V2** | Update merge procedure to use PR-based workflow per WORKTREE_CLEANUP_PROCEDURE_V2.md |
| **`scripts/worktree_cleanup.bash`** | Document the automated cleanup script |
| **Cross-repo dependency update** | Procedure for updating a shared dependency across multiple repos |
| **Release coordination** | How to coordinate releases across interdependent packages |

---

## Per-Project Content Assignment Summary

This table shows which source sections each sub-agent should pull from, plus the new content they must add.

### juniper-data

| Source Section | Lines | Action |
|----------------|-------|--------|
| Add an Endpoint to juniper-data | 199--208 | Copy, expand |
| Add Request/Response Models | 247--251 | Copy (juniper-data portion) |
| Add Middleware | 253--261 | Copy |
| Run a Service Natively -- juniper-data block | 388--392 | Copy |
| Add a Setting to juniper-data | 667--674 | Copy |
| Change Log Level -- juniper-data | 703--704 | Copy |
| Enable JSON Logging -- juniper-data | 717 | Copy |
| Enable Sentry -- juniper-data | 731 | Copy |
| Enable Prometheus -- juniper-data | 741 | Copy |
| Add a Custom Metric | 806--822 | Copy (example uses juniper-data) |
| Add a New Generator | 1274--1285 | Copy |
| **NEW: Storage backends** | -- | Write new |
| **NEW: ruff configuration** | -- | Write new |

### juniper-cascor

| Source Section | Lines | Action |
|----------------|-------|--------|
| Add an Endpoint to juniper-cascor | 210--214 | Copy, expand |
| Add a WebSocket Endpoint | 216--224 | Copy |
| Run a Service Natively -- juniper-cascor block | 394--398 | Copy |
| Add a Constant to juniper-cascor | 676--682 | Copy |
| Change Log Level -- juniper-cascor | 706--708 | Copy |
| Enable JSON Logging -- juniper-cascor | 718 | Copy |
| Enable Sentry -- juniper-cascor | 732 | Copy |
| Enable Prometheus -- juniper-cascor | 742 | Copy |
| **NEW: HDF5 checkpoint format** | -- | Write new |
| **NEW: Training lifecycle** | -- | Write new |

### juniper-canopy

| Source Section | Lines | Action |
|----------------|-------|--------|
| Run a Service Natively -- juniper-canopy block | 400--404 | Copy |
| Add a Config Entry to juniper-canopy | 684--694 | Copy |
| Change Log Level -- juniper-canopy | 709 | Copy |
| Enable JSON Logging -- juniper-canopy | 719 | Copy |
| Enable Sentry -- juniper-canopy | 733 | Copy |
| Enable Prometheus -- juniper-canopy | 743 | Copy |
| **NEW: Cassandra configuration** | -- | Write new |
| **NEW: Redis configuration** | -- | Write new |
| **NEW: Dashboard layout** | -- | Write new |

### juniper-data-client

| Source Section | Lines | Action |
|----------------|-------|--------|
| Add a Method to juniper-data-client | 267--275 | Copy |
| Change a Client Method | 293--300 | Copy |
| Remove a Client Method | 302--309 | Copy |
| Change Client Retry/Timeout Defaults | 311--315 | Copy (data-client portion) |
| Download a Dataset Artifact | 1287--1305 | Copy |
| **NEW: FakeClient** | -- | Write new |
| **NEW: Error handling** | -- | Write new |

### juniper-cascor-client

| Source Section | Lines | Action |
|----------------|-------|--------|
| Add a Method to juniper-cascor-client | 277--281 | Copy |
| Add a WebSocket Event Handler | 283--291 | Copy |
| Change a Client Method | 293--300 | Copy |
| Remove a Client Method | 302--309 | Copy |
| Change Client Retry/Timeout Defaults | 311--315 | Copy (cascor-client portion) |
| **NEW: WebSocket message schemas** | -- | Write new |
| **NEW: FakeClient** | -- | Write new |
| **NEW: Connection lifecycle** | -- | Write new |

### juniper-cascor-worker

| Source Section | Lines | Action |
|----------------|-------|--------|
| (minimal existing content -- test command only at line 441) | 441 | Copy |
| **NEW: Worker CLI/config** | -- | Write new |
| **NEW: Distributed training** | -- | Write new |
| **NEW: Native run command** | -- | Write new |

### juniper-deploy

| Source Section | Lines | Action |
|----------------|-------|--------|
| Enable/Disable API Key Auth | 144--171 | Copy |
| Start Full Stack / Demo / Dev | 321--352 | Copy |
| Add a New Docker Service | 354--363 | Copy |
| Change a Service Port | 365--374 | Copy |
| Add an Environment Variable | 376--383 | Copy |
| Check Service Health | 409--426 | Copy |
| Enable Prometheus Metrics (stack) | 738--758 | Copy |
| Start Observability Stack | 760--775 | Copy |
| View Grafana Dashboards | 777--788 | Copy |
| Add a Grafana Dashboard | 824--831 | Copy |
| Query Prometheus Directly | 833--846 | Copy |
| Troubleshoot Missing Metrics | 848--856 | Copy |
| Docker Compose Profiles table | 1337--1344 | Copy |
| Add a Package to Docker Containers | 1350--1371 | Copy |
| Upgrade a Package Version | 1373--1389 | Copy |
| Upgrade Python Version in Docker | 1391--1419 | Copy |
| **NEW: Docker networking** | -- | Write new |
| **NEW: Volume mounts** | -- | Write new |
| **NEW: Makefile targets** | -- | Write new |

### juniper-ml (ecosystem)

| Source Section | Lines | Action |
|----------------|-------|--------|
| Secrets (all subsections) | 104--193 | Copy |
| Change/Remove an Endpoint (cross-repo) | 226--245 | Copy |
| Testing: Run Tests per Repo | 432--444 | Copy |
| Testing: Coverage, Markers | 446--480 | Copy |
| Claude Automation Script (full) | 484--622 | Copy |
| Dependencies (full) | 626--662 | Copy |
| Metric Naming Convention | 790--802 | Copy |
| CI/CD and Pre-commit (full) | 860--925 | Copy |
| Claude Code Session Script (full, **deduplicated**) | 928--1175 | Copy, deduplicate |
| Git Worktrees (**corrected for V2**) | 1179--1216 | Copy, correct |
| Quick Reference Tables | 1309--1345 | Copy |
| **NEW: Worktree cleanup V2 alignment** | -- | Correct |
| **NEW: Cross-repo dependency update** | -- | Write new |
| **NEW: Release coordination** | -- | Write new |
| **REMOVE: Duplicate sections** | 1077--1156, 1219--1270 | Delete |
