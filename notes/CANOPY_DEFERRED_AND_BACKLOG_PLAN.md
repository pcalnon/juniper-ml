# Juniper-Canopy: Deferred & Backlog Implementation Plan

**Created**: 2026-03-31
**Status**: COMPLETE — All Sprints Executed (2026-04-01)
**Prerequisite**: [CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md](CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md) (all 16 action items complete)

---

## Table of Contents

1. [Scope](#scope)
2. [Priority Framework](#priority-framework)
3. [Sprint 1: Foundation Hardening](#sprint-1-foundation-hardening)
4. [Sprint 2: Backend Integration Completion](#sprint-2-backend-integration-completion)
5. [Sprint 3: Testing & Quality Gates](#sprint-3-testing--quality-gates)
6. [Sprint 4: DevOps & Deployment](#sprint-4-devops--deployment)
7. [Sprint 5: UI Enhancements — Core](#sprint-5-ui-enhancements--core)
8. [Sprint 6: UI Enhancements — Advanced](#sprint-6-ui-enhancements--advanced)
9. [Icebox](#icebox)
10. [Pre-Existing Test Failures](#pre-existing-test-failures)
11. [Dependency Map](#dependency-map)

---

## Scope

This plan covers **all outstanding work** for juniper-canopy across three source documents:

| Source                                | Outstanding Items                                                          |
|---------------------------------------|----------------------------------------------------------------------------|
| Post-Release Development Roadmap      | 38 NOT STARTED + 9 PARTIAL + 6 DEFERRED                                    |
| Microservices Architecture Roadmap    | 9 phases (~115 tasks), all PLANNING                                        |
| Proposal 08 (UI Lock & Visualization) | 4 fixes + 3 bugs, all PROPOSED                                             |
| Audit Backlog (from previous plan)    | 4 items (MyPy strict, async tests, deprecated code, pre-existing failures) |

Items are organized into **6 sprints** by priority and dependency order, followed by an **icebox** for items requiring external changes or long-term architectural work.

---

## Priority Framework

| Priority             | Criteria                                                  | Sprint Target |
|----------------------|-----------------------------------------------------------|---------------|
| **P0 — Critical**    | Blocks core functionality; user-visible breakage          | Sprint 1      |
| **P1 — High**        | Significant quality/reliability gap; moderate user impact | Sprint 2-3    |
| **P2 — Medium**      | Code quality, test coverage, developer experience         | Sprint 3-4    |
| **P3 — Enhancement** | New features, polish, UX improvements                     | Sprint 5-6    |
| **P4 — Deferred**    | External dependencies, aspirational, low ROI              | Icebox        |

---

## Sprint 1: Foundation Hardening

Foundation Hardening — ✅ COMPLETE (2026-03-31)

**Goal**: Fix remaining partial items, resolve pre-existing test failures, clean up technical debt.
**Estimated Effort**: 1-2 days | **Actual**: ~2 hours

### Step 1.1: Fix Pre-Existing Test Failures (P0)

| Task                                                | Source | Details                                                                                                                                                             | Effort |
|-----------------------------------------------------|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| Fix `test_state_sync.py` (2 failures)               | Audit  | `test_sync_real_envelope_nested_status_fields` asserts `max_epochs==500` but gets 1000; `test_sync_real_params_filter_non_param_fields` KeyError on `learning_rate` | 30 min |
| Fix `test_demo_training_convergence.py` (1 failure) | Audit  | `test_accuracy_exceeds_chance_with_hidden_units` — timeout during training; likely needs adjusted convergence params or timeout increase                            | 30 min |
| Fix `test_phase4_implementation.py` (1 timeout)     | Audit  | `test_add_hidden_unit_calls_train_candidate_with_200_steps` — PyTorch backward pass timeout >60s; needs mock or reduced step count                                  | 30 min |

**Validation**: All unit tests pass without `--ignore` exclusions.

### Step 1.2: Vestigial Code Removal (P1)

| Task                                                 | Source      | Details                                                                                                                                                              | Effort |
|------------------------------------------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| Refactor tests away from deprecated convergence code | Audit       | 5 test files reference `_should_add_cascade_unit`, `CASCADE_COOLDOWN_EPOCHS`, `_cascade_cooldown_remaining`. tests use production code paths, delete deprecated code | 1-2 hr |
| Legacy `.pyc` cleanup                                | CAN-MED-011 | Remove stale `.pyc` files from deleted `constants.py` and any other orphaned bytecode                                                                                | 15 min |
| Documentation status inconsistencies                 | CAN-MED-013 | Fix contradictory statuses in phase3 README and IMPLEMENTATION_PLAN.md                                                                                               | 15 min |

### Step 1.3: Flake8 & Linting Configuration (P2)

| Task                                          | Source      | Details                                                                                            | Effort |
|-----------------------------------------------|-------------|----------------------------------------------------------------------------------------------------|--------|
| Consolidate Flake8 config into `.flake8` file | CAN-MED-004 | Move inline args from `.pre-commit-config.yaml` hooks into a `.flake8` config file for consistency | 20 min |
| Add `notes/` to markdown linting              | CAN-MED-003 | Expand markdownlint pre-commit hook scope to include `notes/` directory                            | 5 min  |

---

## Sprint 2: Backend Integration Completion

**Goal**: Complete all backend integration gaps for service mode.
**Estimated Effort**: 2-3 days

### Step 2.1: Decision Boundary for Service Mode (P0) — ✅ COMPLETE (pre-existing)

| Task                                               | Source       | Details                                                                                                                          | Status            |
|----------------------------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Decision boundary endpoint in juniper-cascor       | CAN-CRIT-001 | `GET /v1/decision-boundary` with server-side grid prediction (in `api/routes/decision_boundary.py` + `api/lifecycle/manager.py`) | ✅ Already exists |
| `get_decision_boundary()` in juniper-cascor-client | CAN-CRIT-001 | `client.get_decision_boundary(resolution)` wrapping the endpoint                                                                 | ✅ Already exists |
| `get_decision_boundary()` in CascorServiceAdapter  | CAN-CRIT-001 | Delegates to client, transforms `grid_x/grid_y/predictions` → `xx/yy/Z` format                                                   | ✅ Already exists |

### Step 2.2: Snapshot REST Delegation (P1) — ✅ COMPLETE (2026-03-31)

| Task                                                            | Source       | Details                                                                                                                              | Status  |
|-----------------------------------------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------|---------|
| Add `/v1/snapshots` endpoints to juniper-cascor                 | CAN-CRIT-002 | `POST /v1/snapshots` (save), `GET /v1/snapshots` (list), `GET /v1/snapshots/{id}` (detail), `POST /v1/snapshots/{id}/restore` (load) | ✅ Done |
| Add snapshot methods to juniper-cascor-client                   | CAN-CRIT-002 | `save_snapshot()`, `load_snapshot()`, `list_snapshots()`, `get_snapshot()` + FakeCascorClient support                                | ✅ Done |
| Add `save_snapshot()`/`load_snapshot()` to CascorServiceAdapter | CAN-CRIT-002 | Delegates to client methods; `load_snapshot` extracts snapshot_id from path stem                                                     | ✅ Done |
| Update HDF5 snapshots panel for service mode                    | CAN-CRIT-002 | `main.py` already checks `hasattr(backend._adapter, "save_snapshot")` — now resolves to the real methods                             | ✅ Auto |

### Step 2.3: JuniperData Error Handling (P1) — ✅ COMPLETE (2026-03-31)

| Task                                                        | Source       | Details                                                                                                                           | Status        |
|-------------------------------------------------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------|---------------|
| Map JuniperData client exceptions to user-friendly messages | CAN-HIGH-006 | `_user_friendly_data_error()` maps 6 exception types to actionable messages                                                       | ✅ Done       |
| Add JuniperData circuit breaker                             | CAN-MED-008  | N/A — JuniperData calls are one-shot (init-time dataset generation), not periodic polling; circuit breaker pattern not applicable | ✅ Not needed |
| Add structured logging for JuniperData API interactions     | CAN-MED-009  | `create_dataset` and `download_artifact_npz` log latency_ms, url, dataset_id via `extra={}`                                       | ✅ Done       |

### Step 2.4: NPZ Validation (P1) — ✅ COMPLETE (2026-03-31)

| Task                                            | Source       | Details                                                                                                  | Status  |
|-------------------------------------------------|--------------|----------------------------------------------------------------------------------------------------------|---------|
| Add dtype and shape validation for NPZ datasets | CAN-HIGH-002 | `_validate_npz_arrays()`: float32 dtype, 2D shape for X arrays, matching sample counts, numpy type check | ✅ Done |

### Step 2.5: UI Lock & Training Pipeline (P0 — UX Critical) — ✅ COMPLETE (2026-03-31)

| Task                                             | Source    | Details                                                                                                                        | Status          |
|--------------------------------------------------|-----------|--------------------------------------------------------------------------------------------------------------------------------|-----------------|
| Break lock granularity during candidate training | P08-FIX-1 | Already implemented: `_training_loop()` runs candidate training lock-free, brief lock for install, retrain per-step lock-free  | ✅ Already done |
| Emit progress during retrain                     | P08-FIX-2 | Already implemented: `OUTPUT_RETRAIN_EMIT_EVERY=50` step-based emission with time-based fallback                               | ✅ Already done |
| Fix history deque `maxlen=1000` silent eviction  | P08-BUG-2 | Increased maxlen from 1000→10000 via `TrainingConstants.METRICS_HISTORY_MAXLEN`, matching `DashboardConstants.MAX_DATA_POINTS` | ✅ Fixed        |

---

## Sprint 3: Testing & Quality Gates

Testing & Quality Gates — ✅ COMPLETE (2026-03-31)

**Goal**: Close all testing gaps, achieve coverage targets.
**Estimated Effort**: 2-3 days

### Step 3.1: Async/Sync Boundary Tests (P1) — ✅ COMPLETE (2026-03-31)

| Task                      | Source       | Details                                                                                                                                                                                | Status  |
|---------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| async/sync boundary tests | CAN-HIGH-003 | `test_async_sync_boundary.py`: 17 tests: `run_in_executor`, `run_coroutine_threadsafe`, `broadcast_sync` vs `broadcast_from_thread` behavioral difference, concurrent delivery, errors | ✅ Done |

### Step 3.2: Real Backend Path Coverage (P1) — ✅ COMPLETE (2026-03-31)

| Task                         | Source       | Details                                                                                                                                                      | Status                               |
|------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| Add gated real-backend tests | CAN-HIGH-004 | Already extensive: 15+ test files use `FakeCascorClient` for service mode paths (unit + integration). Properly gated behind `CASCOR_BACKEND_AVAILABLE=1`     | ✅ Already done (pre-existing)       |
| Main.py coverage improvement | CAN-HIGH-008 | `test_main_endpoints_coverage.py`: 35 tests covering snapshots, health, layouts CRUD, Redis/Cassandra, remote workers. Coverage 72%→86% (+110 lines)         | ✅ Done                              |

### Step 3.3: Integration Test Expansion (P1) — ✅ COMPLETE (2026-03-31)

| Task          | Source       | Details                                                                                                                                                                                        | Status               |
|---------------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| Skipped tests | CAN-HIGH-007 | gate `test_candidate_visibility` (`RUN_SERVER_TESTS=1`, `@pytest.mark.requires_server`), `test_mvp_functionality` (on error), `test_parameter_persistence`/`test_demo_endpoints` (server-gate) | ✅ Already gated     |
| E2E tests     | CAN-MED-010  | `test_juniper_data_e2e.py`: 48 tests (38 fake + 10 live) covering create → download → validate → train → verify. Gated behind `JUNIPER_DATA_E2E_TEST=1`                                        | ✅ Done (2026-04-01) |

### Step 3.4: Code Quality (P2) — ✅ COMPLETE (2026-03-31)

| Task                               | Source        | Details                                                                                                                            | Status                |
|------------------------------------|---------------|------------------------------------------------------------------------------------------------------------------------------------|-----------------------|
| Type annotation gaps               | CAN-MED-007   | `demo_mode.py` (8→0), `service_backend.py` (5→0), `demo_backend.py` (5→0) — all mypy errors resolved via type annotations + cast() | ✅ Done               |
| Test docstrings                    | CAN-MED-014   | 32 module docstrings + 16 class docstrings added across unit/integration/regression/performance test files                         | ✅ Done               |
| Enable MyPy `warn_return_any=true` | Audit Backlog | 44 `no-any-return` errors fixed across 12 files (bool() wrappers, dict() wrappers, cast(), type annotations, name-unmangle)        | ✅ Done               |
| Enable MyPy `strict_optional=true` | Audit Backlog | Enabled globally; 9 modules with pre-existing Optional errors use per-module `strict_optional=false` override pending migration    | ✅ Done (incremental) |

---

## Sprint 4: DevOps & Deployment

DevOps & Deployment — ✅ COMPLETE (2026-03-31)

**Goal**: Production-ready deployment infrastructure.
**Estimated Effort**: 3-5 days | **Actual**: Most items pre-existing; new items ~1 hour

### Step 4.1: Docker Compose Modernization (P2) — ✅ COMPLETE (pre-existing)

| Task                              | Source                | Details                                                                                                                            | Status            |
|-----------------------------------|-----------------------|------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Create Makefile in juniper-deploy | Microservices Phase 1 | Wrap Docker Compose: `up`, `down`, `restart`, `logs`, `status`, `build`, `clean`, `health`, `ps`, `shell-*`, `demo`, `dev`, `obs`  | ✅ Already exists |
| Create health check script        | Microservices Phase 1 | `scripts/health_check.sh` hitting `/v1/health/ready` for all 3 services with formatted report                                      | ✅ Already exists |
| Add Docker Compose profiles       | Microservices Phase 3 | `full`, `demo`, `dev`, `observability` profiles with network segmentation (frontend/backend/data)                                  | ✅ Already exists |
| Docker Compose demo profile       | Microservices Phase 7 | `juniper-cascor-demo` with auto-start, `demo-seed` init container, `juniper-canopy-demo` dashboard                                 | ✅ Already exists |

### Step 4.2: Health Check Consolidation (P2) — ✅ COMPLETE (2026-03-31)

| Task                      | Source                | Details                                                                                                                                                                   | Status  |
|---------------------------|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Consolidate health routes | Microservices Phase 8 | 3 canonical routes: `/v1/health`, `/v1/health/live`, `/v1/health/ready`. Legacy `/health` and `/api/health` marked `deprecated=True` with runtime deprecation warning log | ✅ Done |

### Step 4.3: Configuration Standardization (P2) — ✅ COMPLETE (pre-existing + 2026-03-31)

| Task                                               | Source                | Details                                                                                                                                       | Status          |
|----------------------------------------------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-----------------|
| Migrate env prefix `CASCOR_*` → `JUNIPER_CANOPY_*` | Microservices Phase 9 | `JUNIPER_CANOPY_*` primary via Pydantic BaseSettings; `CASCOR_*` fallback with `DeprecationWarning` in field validators for 6 legacy env vars | ✅ Already done |
| Add `.env` file support                            | Microservices Phase 9 | `.env.example` (reference), `.env.dev` (demo mode, debug logging), `.env.prod` (service mode, production defaults)                            | ✅ Done         |

### Step 4.4: Systemd Service Units (P3) — ✅ COMPLETE (2026-03-31)

| Task                                           | Source                | Details                                                                                                                                               | Status  |
|------------------------------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Define systemd user service for juniper-canopy | Microservices Phase 2 | `scripts/juniper-canopy.service` — user unit with MemoryMax=2G, CPUQuota=200%, security hardening (NoNewPrivileges, ProtectSystem=strict, PrivateTmp) | ✅ Done |
| Create `juniper-ctl` management CLI            | Microservices Phase 2 | `scripts/juniper-ctl` — start/stop/restart/status/logs/health/resources commands wrapping systemctl                                                   | ✅ Done |

---

## Sprint 5: UI Enhancements — Core

UI Enhancements — Core — ✅ COMPLETE (2026-03-31)

**Goal**: Most impactful UI improvements for everyday use.
**Estimated Effort**: 3-5 days | **Actual**: ~2 hours

### Step 5.1: Training UX Improvements (P1 — UX) — ✅ COMPLETE (2026-03-31)

| Task                             | Source    | Details                                                                               | Status                                                                  |
|----------------------------------|-----------|---------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| Meta parameter updates pause     | CAN-000   | Pause periodic backend sync when Apply Parameters is active                           | ✅ N/A — architecture already prevents overwriting (one-shot init only) |
| Decision boundary poll frequency | P08-BUG-3 | Changed boundary poll from `slow-update-interval` (5s) to `fast-update-interval` (1s) | ✅ Done                                                                 |
| Sliding window default fix       | P08-BUG-1 | Changed default from 100→500 via `DashboardConstants.DEFAULT_SLIDING_WINDOW_SIZE`     | ✅ Done                                                                 |

### Step 5.2: Tooltips & Help (P2) — ✅ COMPLETE (2026-03-31)

| Task                         | Source  | Details                                                                                                   | Status  |
|------------------------------|---------|-----------------------------------------------------------------------------------------------------------|---------|
| Add tooltips to all controls | CAN-017 | 25 `dbc.Tooltip` components for all NN/CN parameter inputs + Apply button, text in `frontend/tooltips.py` | ✅ Done |

### Step 5.3: Layout Persistence (P3) — ✅ COMPLETE (2026-03-31)

| Task                             | Source   | Details                                                                                    | Status  |
|----------------------------------|----------|--------------------------------------------------------------------------------------------|---------|
| Layout save/load to localStorage | CAN-016a | Active tab persisted via two `clientside_callback`s (save on change, restore on page load) | ✅ Done |

### Step 5.4: Dataset Management (P3) — ✅ COMPLETE (2026-03-31)

| Task                 | Source   | Details                                                                                                                                                                                    | Status  |
|----------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Generate new dataset | CAN-016b | "Generate Dataset" button + modal with samples/spirals/rotations/noise params; `POST /api/dataset/generate` endpoint; `DemoMode.regenerate_dataset()` + `DemoBackend.regenerate_dataset()` | ✅ Done |

---

## Sprint 6: UI Enhancements — Advanced

UI Enhancements — Advanced — ✅ COMPLETE (2026-03-31)

**Goal**: Advanced features for power users and research workflows.
**Estimated Effort**: 5-8 days | **Actual**: ~2 hours

### Step 6.1: Meta Parameter Tuning Tab (P3) — ✅ COMPLETE (2026-03-31)

| Task                              | Source            | Details                                                                                                                | Status                                                            |
|-----------------------------------|-------------------|------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| Create meta parameter tuning tab  | CAN-004           | Params tab, `ParametersPanel`: 3-sect dbc.Table (Network Train, Dataset, Candidate Train) current/min/max/default vals | ✅ Done                                                           |
| Pin/unpin parameters to side menu | CAN-005           | Drag-to-pin params from tuning tab to persistent side panel                                                            | ⏸ Defer — sidebar has all params; pin/unpin complex, min UX gain  |
| Individual parameter controls     | CAN-006 - CAN-013 | 22+ params tunable in sidebar (nn-*and cn-* inputs), Apply button; Params tab read-only summary                        | ✅ Already done                                                   |

### Step 6.2: Snapshot & Replay (P3) — ✅ COMPLETE (2026-03-31)

| Task                                | Source  | Details                                                                                                                                 | Status  |
|-------------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------|---------|
| Snapshot captures with tuning state | CAN-014 | Demo mode: `meta_params` dict stored on snapshot entry. HDF5: `meta_params` group with attributes. Captured from `backend.get_status()` | ✅ Done |
| Snapshot replay with tuning         | CAN-015 | Restore reads `meta_params` and applies via `backend.apply_params()`. Returns params in response for frontend sync                      | ✅ Done |

### Step 6.3: Candidate Pool History (P3) — ✅ COMPLETE (pre-existing)

| Task                           | Source  | Details                                                                                                                         | Status            |
|--------------------------------|---------|---------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Candidate pool history browser | CAN-003 | `candidate-pools-history` dcc.Store (max 20 entries), expandable `dbc.Card` per pool with epoch, top candidate, scores, metrics | ✅ Already exists |

### Step 6.4: Tutorial System (P3) — ✅ COMPLETE (2026-03-31)

| Task                        | Source  | Details                                                                                                                             | Status  |
|-----------------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------|---------|
| Tutorial reference guide    | CAN-018 | "Tutorial" tab with `TutorialPanel` — 5-section dbc.Accordion: CasCor overview, workflow guide, UI guide, parameter reference, tips | ✅ Done |
| Getting Started walkthrough | CAN-019 | Welcome modal on first visit (localStorage-gated), 4-step quick start guide with Tutorial tab link                                  | ✅ Done |

---

## Icebox

Items requiring external dependencies, major architectural work, or with low near-term ROI.

**Last reviewed**: 2026-04-01 — In-depth analysis performed for all open items. Status reclassified where research revealed existing implementations or changed blockers.

### Status Summary

| Item                         | Source                | Status                 | Verdict                                                       |
|------------------------------|-----------------------|------------------------|---------------------------------------------------------------|
| Multi-hierarchy network view | CAN-020               | BLOCKED                | Requires fundamental CasCor algorithm extension               |
| Population network view      | CAN-021               | BLOCKED                | Requires CAN-020 + population training paradigm               |
| Dataset versioning           | CAN-DEF-005           | ACTIONABLE             | 3-repo change; unblocked with phased approach                 |
| 3D network visualization     | CAN-DEF-008           | ✅ ALREADY IMPLEMENTED | Plotly 3D with 2D/3D toggle; enhancement opportunities remain |
| Network segmentation         | Microservices Phase 3 | ✅ ALREADY IMPLEMENTED | 3 networks (frontend/backend/data) with internal isolation    |
| Observability stack          | Microservices Phase 3 | ✅ ALREADY IMPLEMENTED | Prometheus + Grafana + 23 metrics + 4 dashboards              |
| Docker secrets management    | Microservices Phase 3 | ACTIONABLE             | Partial; needs `_FILE` env var pattern in services            |

### Completed Items (Cross-Repo)

| Task                                   | Source           | Notes                                                                                                                                                |
|----------------------------------------|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~~Remote worker status dashboard~~     | ~~CAN-HIGH-005~~ | ✅ COMPLETE (2026-03-31) — REST routes in cascor, client methods in cascor-client, WorkerPanel + demo endpoints in canopy                            |
| ~~Cassandra integration tests~~        | ~~CAN-DEF-002~~  | ✅ COMPLETE (2026-03-31) — Docker service in juniper-deploy, 16 real-instance integration tests gated behind CASSANDRA_INTEGRATION_TEST=1            |
| ~~Redis integration tests~~            | ~~CAN-DEF-003~~  | ✅ COMPLETE (2026-03-31) — Docker in juniper-deploy, 15 real-instance int tests gated behind REDIS_INTEGRATION_TEST=1                                |
| ~~Dataset batch operations~~           | ~~CAN-DEF-006~~  | ✅ COMPLETE (2026-03-31) — batch-create, batch-tags, batch-export endpoints in juniper-data; client wrappers + FakeDataClient in juniper-data-client |
| ~~JuniperData performance benchmarks~~ | ~~CAN-DEF-007~~  | ✅ COMPLETE (2026-04-01) — 23 benchmarks in juniper-data-client (14 fake + 9 live gated behind JUNIPER_DATA_BENCHMARK=1)                             |

---

### CAN-DEF-005: Dataset Versioning — Detailed Analysis

**Status**: ACTIONABLE (no longer blocked — phased approach unblocks canopy work)
**Source**: CANOPY_JUNIPER_DATA_INTEGRATION_PLAN.md (CAN-INT-015), juniper-data RD-CANOPY-002
**Estimated Effort**: 5-8 days across 3 repos
**Priority**: Medium — enables training reproducibility and experiment tracking

#### Current State

The juniper-data `DatasetMeta` model (`juniper_data/core/models.py`) currently has:

- **Identity**: `dataset_id` (deterministic hash from generator + version + params), `generator`, `generator_version`
- **Lifecycle**: `tags`, `ttl_seconds`, `expires_at`, `last_accessed_at`, `access_count`
- **Shape**: `n_samples`, `n_features`, `n_classes`, `n_train`, `n_test`
- **Integrity**: `checksum` (exists but set to NULL)

**What's missing**: No `dataset_name`, `dataset_version`, `parent_dataset_id`, `description`, `created_by`, or `lineage` fields. Datasets are referenced by ID only — no concept of "version 2 of the spiral-2arm dataset."

The `dataset_id` is deterministic (`{generator}-{version}-{hash[:16]}`) — identical parameters produce the same ID (caching behavior). There is no way to create multiple versions of a dataset with the same logical name.

#### Gap Analysis

| Capability      | Current                              | Required                                     |
|-----------------|--------------------------------------|----------------------------------------------|
| Version field   | Only `generator_version` (algorithm) | Explicit `dataset_version` (v1, v2, ...)     |
| Named datasets  | ID-only reference                    | Name + version lookup                        |
| Version history | None                                 | Lineage chain via `parent_dataset_id`        |
| Data integrity  | `checksum` field (unused)            | SHA256 of NPZ artifact                       |
| Provenance      | `created_at` only                    | `created_by`, `description`, derivation info |
| API endpoints   | CRUD by ID                           | List versions by name, get latest version    |
| Client methods  | ID-based only                        | Name+version reference, version listing      |

#### Implementation Plan

**Phase 1 — juniper-data model + API** (3-4 days):

| Step | Change                                                                                                   | Files                                    |
|------|----------------------------------------------------------------------------------------------------------|------------------------------------------|
| 1.1  | Add `dataset_name`, `dataset_version`, `parent_dataset_id`, `description`, `created_by` to `DatasetMeta` | `juniper_data/core/models.py`            |
| 1.2  | Extend PostgreSQL schema with versioning columns (nullable for backward compat)                          | `juniper_data/storage/postgres_store.py` |
| 1.3  | Extend all storage backends (InMemory, LocalFS, S3) with version-aware queries                           | `juniper_data/storage/*.py`              |
| 1.4  | Populate `checksum` field with SHA256 of NPZ artifact on creation                                        | `juniper_data/core/dataset_manager.py`   |
| 1.5  | Add `GET /v1/datasets/versions?name={name}` — list versions of a named dataset                           | `juniper_data/api/routes/datasets.py`    |
| 1.6  | Add `GET /v1/datasets/latest?name={name}` — get latest version                                           | `juniper_data/api/routes/datasets.py`    |
| 1.7  | Extend filter endpoint to support `name` and `version` parameters                                        | `juniper_data/api/routes/datasets.py`    |
| 1.8  | Auto-increment version when creating dataset with existing `dataset_name`                                | `juniper_data/core/dataset_manager.py`   |
| 1.9  | Tests: unit tests for model, storage queries, API endpoints                                              | `juniper_data/tests/`                    |

**Phase 2 — juniper-data-client** (1-2 days):

| Step | Change                                                     | Files                                               |
|------|------------------------------------------------------------|-----------------------------------------------------|
| 2.1  | Add `name` and `description` params to `create_dataset()`  | `juniper_data_client/client.py`                     |
| 2.2  | Add `list_versions(name)`, `get_latest(name)` methods      | `juniper_data_client/client.py`                     |
| 2.3  | Mirror in `FakeDataClient` with in-memory version tracking | `juniper_data_client/testing/fake_client.py`        |
| 2.4  | Tests: unit tests for new client methods                   | `tests/test_client.py`, `tests/test_fake_client.py` |

**Phase 3 — juniper-canopy integration** (1-2 days):

| Step | Change                                                                | Files                                             |
|------|-----------------------------------------------------------------------|---------------------------------------------------|
| 3.1  | Store `dataset_name` + `dataset_version` in training session metadata | `src/demo_mode.py`, `src/backend/data_adapter.py` |
| 3.2  | Display dataset version in dashboard status panel                     | `src/frontend/components/`                        |
| 3.3  | Add dataset version to snapshot metadata (for reproducibility)        | `src/backend/demo_backend.py`                     |
| 3.4  | Tests: E2E version-aware dataset flow                                 | `src/tests/integration/`                          |

#### Industry Best Practices Reference

| Tool          | Versioning Model                          | Key Insight                                      |
|---------------|-------------------------------------------|--------------------------------------------------|
| MLflow        | Artifact + run ID, git-tagged             | Tight coupling to experiment tracking            |
| DVC           | Content-hash in `.dvc` files, git-native  | Versioning via VCS, not API                      |
| W&B Artifacts | Name + version + alias, content-addressed | Semantic names with auto-increment               |
| Delta Lake    | Transaction log, time travel              | ACID semantics, overly complex for this use case |

**Recommended approach**: W&B-style — `dataset_name` + auto-incrementing `dataset_version` + optional alias (e.g., "production", "latest"). Content-addressed storage via `checksum` for deduplication.

#### Risks

| Risk                                            | Likelihood | Impact | Mitigation                                                         |
|-------------------------------------------------|------------|--------|--------------------------------------------------------------------|
| Breaking existing dataset ID semantics          | Medium     | High   | Make `dataset_name` optional; existing ID-only workflows unchanged |
| Storage backend migration complexity            | Low        | Medium | New columns are nullable; no migration for existing datasets       |
| Version numbering conflicts in batch operations | Low        | Low    | Auto-increment uses DB-level atomic counter                        |

---

### CAN-020: Multi-Hierarchy Network View — Detailed Analysis

**Status**: BLOCKED — Requires fundamental CasCor algorithm extension
**Source**: Canopy Roadmap Phase 3
**Dependencies**: CasCor multi-hierarchy support (does not exist)
**Estimated Effort**: 8-12 days (CasCor) + 3-5 days (canopy) when unblocked

#### Current CasCor Architecture

The `CascadeCorrelationNetwork` class (`juniper-cascor/src/cascade_correlation/cascade_correlation.py`, ~4800 lines) implements the original Fahlman & Lebiere (1990) algorithm:

- **Hidden units**: Flat list `self.hidden_units: List[Dict]` — each unit has `weights`, `bias`, `activation`
- **Cascade structure**: Each new hidden unit receives input from ALL previous layers (inputs + all prior hidden units)
- **Grow mechanism**: `grow_network()` adds one hidden unit at a time via `add_unit()`
- **Topology**: Linear cascade: Input → H0 → H1 → H2 → ... → Output (no hierarchy grouping)

**There is no concept of hierarchy levels.** The original CasCor algorithm treats all hidden units as a single growing cascade. Each unit connects to all previous units (full cascade connectivity), but they are not grouped into layers or levels.

#### What Multi-Hierarchy Would Require

"Hierarchy levels" in CasCor typically refers to **Cascade-2** or **deep cascade** extensions where hidden units are organized into groups (levels), and connectivity is restricted:

| Aspect              | Current (Flat Cascade)                         | Multi-Hierarchy                                                     |
|---------------------|------------------------------------------------|---------------------------------------------------------------------|
| Hidden unit storage | `List[Dict]` (flat)                            | `List[List[Dict]]` (nested by level)                                |
| Connectivity        | Each unit connects to ALL prior units + inputs | Level-restricted: units connect to same-level and lower-level units |
| Candidate training  | Pool trained against global residual           | Pool trained per-level against level residual                       |
| Grow logic          | Add single unit to flat list                   | Add unit to current level; create new level when saturated          |
| Topology format     | `{hidden_units: [...]}`                        | `{levels: [{units: [...]}, ...]}`                                   |
| Network size        | O(n^2) connections                             | O(n * level_size) connections per level                             |

**CasCor changes required** (juniper-cascor):

1. Refactor `hidden_units` from flat list to nested list-of-lists
2. Modify `forward()` to respect level boundaries
3. Modify `add_unit()` with level assignment logic
4. Modify `grow_network()` with level saturation detection
5. Modify candidate training to compute per-level residuals
6. Update all 16+ files that reference `hidden_units`
7. Update topology extraction, serialization, HDF5 snapshots
8. Backward compatibility for loading flat-cascade snapshots

**Canopy changes required** (when CasCor support exists):

1. Hierarchy level selector (dropdown or slider) per CAN-020 spec
2. Level-filtered topology view in network visualizer
3. Per-level metrics aggregation
4. Thumbnail preview row for level selection

#### Assessment

This is a **research-grade algorithm extension**, not a feature toggle. The original CasCor paper does not define hierarchy levels. Extensions like Cascade-2 (Baluja & Fahlman, 1994) exist in academic literature but are not widely implemented. Estimated effort for CasCor changes alone is 8-12 days with significant regression risk.

**Recommendation**: Keep BLOCKED. Revisit only if there is a specific research motivation for multi-hierarchy CasCor training. The canopy UI work (3-5 days) is straightforward once CasCor support exists.

---

### CAN-021: Population Network View — Detailed Analysis

**Status**: BLOCKED — Requires CAN-020 + population-based training
**Source**: Canopy Roadmap Phase 3
**Dependencies**: CAN-020 (hierarchy support), population-based CasCor training
**Estimated Effort**: 5-8 days (CasCor) + 3-5 days (canopy) when unblocked

#### Current State

CasCor trains **one network at a time**. There is no ensemble, evolutionary, or population-based training in `CascadeCorrelationNetwork`. The `juniper-cascor-worker` supports distributed training of **candidate pools** (multiple candidate units trained in parallel), but this is within a single network — not multiple networks.

#### What Population Training Would Require

Population-based training means running multiple CasCor networks simultaneously with different hyperparameters, architectures, or random seeds, then selecting the best-performing network(s):

**CasCor changes** (juniper-cascor):

1. Population manager: orchestrate N concurrent `CascadeCorrelationNetwork` instances
2. Selection strategy: fitness function to rank networks (loss, accuracy, complexity)
3. Crossover/mutation (evolutionary): combine hidden units from different networks
4. Shared training data with individual network state
5. Population-level metrics aggregation
6. REST API: `/v1/population/*` endpoints for management

**Canopy changes** (when CasCor support exists):

1. Network selector within a population (dropdown per CAN-021 spec)
2. Population-level dashboard (comparative metrics across networks)
3. Per-network detail view (existing visualizer per selected network)

#### Assessment

Population-based training is a **separate research direction** from core CasCor. It requires both CAN-020 (hierarchy, for meaningful population diversity) and a new orchestration layer. This is at minimum a 2-week effort with significant design decisions (evolutionary vs. random search vs. Bayesian optimization).

**Recommendation**: Keep BLOCKED. This is a long-term research feature, not a near-term engineering task.

---

### CAN-DEF-008: 3D Network Visualization — Detailed Analysis

**Status**: ✅ ALREADY IMPLEMENTED (P3-5, 2026-01-10) — Enhancement opportunities remain
**Source**: Development Roadmap P1-4 Phase 2
**Implementation**: `juniper-canopy/src/frontend/components/network_visualizer.py` (v1.7.0)

#### Current Implementation

The 3D visualization was implemented as part of P3-5 using Plotly's native 3D capabilities:

| Feature         | Implementation                                                                       |
|-----------------|--------------------------------------------------------------------------------------|
| **Rendering**   | `go.Scatter3d` traces (one per layer + edges)                                        |
| **Layout**      | `_calculate_3d_layout()`: Z-axis = network layers, Y-axis = node spread within layer |
| **Toggle**      | 2D/3D radio buttons in header controls                                               |
| **Edge colors** | Blue (negative weights), Red (positive), Gray (zero)                                 |
| **Edge width**  | Scaled by weight magnitude: `max(1, min(5, abs(w)*3+1))`                             |
| **Camera**      | Pre-configured eye position (1.5, 1.5, 0.8) with interactive rotation                |
| **Theme**       | Dark/light mode with scene background colors                                         |
| **Tests**       | 19 unit tests in `test_network_visualizer_3d.py`                                     |

#### Technology Evaluation (2026-04-01)

| Technology                     | Verdict            | Rationale                                                                  |
|--------------------------------|--------------------|----------------------------------------------------------------------------|
| **Plotly 3D** (current)        | ✅ Recommended     | Zero new deps, native Dash integration, sufficient for <500 nodes          |
| **Dash VTK**                   | ❌ Not recommended | Overkill for network graphs; designed for volumetric/mesh data; +50MB dep  |
| **Three.js (iframe)**          | ⚠️ Future option   | Full control but breaks Dash callback integration; separate build pipeline |
| **Three.js (dash-extensions)** | ⚠️ Future option   | Best advanced option but requires custom React+JS component                |

#### Enhancement Opportunities (not required, low priority)

| Enhancement                                        | Effort   | Value                                |
|----------------------------------------------------|----------|--------------------------------------|
| Force-directed 3D layout (spring physics)          | 2-3 days | Better aesthetics for large networks |
| Animation during grow_network (unit addition)      | 1-2 days | Research visualization aid           |
| Weight flow animation (data passing through edges) | 2-3 days | Educational value                    |
| WebGL performance optimization for >500 nodes      | 3-5 days | Only needed at scale                 |

**Recommendation**: Mark as COMPLETE. Current Plotly 3D implementation meets the CAN-DEF-008 requirement. Enhancements are optional polish, not blocking.

---

### Network Segmentation — Detailed Analysis

**Status**: ✅ ALREADY IMPLEMENTED — Minor enhancements possible
**Source**: Microservices Architecture Roadmap Phase 3, Section 3.5
**Implementation**: `juniper-deploy/docker-compose.yml` (lines 426-437)

#### Current Implementation

Three custom bridge networks are defined with appropriate isolation:

```bash
networks:
  frontend:   bridge (external)  — canopy, prometheus, grafana
  backend:    bridge (internal)  — cascor, canopy, redis, cassandra
  data:       bridge (internal)  — data, cascor, cascor-demo, demo-seed
```

**Service connectivity**:

- `juniper-canopy` → `frontend` + `backend` + `data` (needs access to both cascor and data)
- `juniper-cascor` → `backend` + `data` (bridges between canopy and data layer)
- `juniper-data` → `data` only (isolated data layer)
- `redis`, `cassandra` → `backend` only
- `prometheus` → `frontend` (needs cross-network scraping access — see gap below)

**Security features**:

- `internal: true` on `backend` and `data` networks blocks external access
- Port binding uses `127.0.0.1` for host-exposed services
- Service discovery via Docker DNS hostnames

#### Gap: Monitoring Network

The Phase 3 roadmap specifies a separate `monitoring` network. Currently Prometheus is on `frontend` only and relies on Docker DNS for cross-network scraping. Best practice is:

```yaml
networks:
  monitoring:
    driver: bridge
# Prometheus gets: monitoring + backend + data (for scraping)
# Grafana gets: monitoring only (queries Prometheus, not services directly)
```

**Effort**: 30 minutes — add network definition, update service assignments.

**Recommendation**: Mark base implementation as COMPLETE. The monitoring network enhancement is a minor follow-up (< 1 hour).

---

### Observability Stack (Prometheus + Grafana) — Detailed Analysis

**Status**: ✅ ALREADY IMPLEMENTED — Enhancement opportunities remain
**Source**: Microservices Architecture Roadmap Phase 3, Section 3.8
**Implementation**: `juniper-deploy/prometheus/`, `juniper-deploy/grafana/`

#### Current Implementation

| Component              | Status        | Details                                                                         |
|------------------------|---------------|---------------------------------------------------------------------------------|
| **Prometheus**         | ✅ Deployed   | `prometheus.yml` with scrape jobs for all 3 services (10s interval)             |
| **Grafana**            | ✅ Deployed   | Auto-provisioned Prometheus datasource + 4 pre-built dashboards                 |
| **Metrics middleware** | ✅ Integrated | `PrometheusMiddleware` in all 3 services, gated by `*_METRICS_ENABLED` env vars |
| **Docker profile**     | ✅ Configured | `observability` profile in docker-compose.yml; `make monitor` target            |
| **Data retention**     | ✅ Configured | 30-day TSDB retention via `--storage.tsdb.retention.time=30d`                   |

**23 total metrics across 3 services**:

- juniper-data: 6 metrics (HTTP requests/duration, dataset generations/duration, cache gauge, build info)
- juniper-cascor: 11 metrics (HTTP, training sessions/epochs/loss/accuracy/hidden-units/correlation, inference, build info)
- juniper-canopy: 6 metrics (HTTP, WebSocket connections/messages, demo mode status, build info)

**4 Grafana dashboards** (auto-provisioned via `grafana/provisioning/dashboards/`):

- Service overview, training progress, data pipeline, infrastructure

#### Enhancement Opportunities

| Enhancement                                  | Effort   | Value                                                                            | Priority |
|----------------------------------------------|----------|----------------------------------------------------------------------------------|----------|
| **Alerting rules** (Prometheus AlertManager) | 2-3 days | Production readiness: alert on service down, high error rate, training stall     | Medium   |
| **SLO/SLA dashboards**                       | 1-2 days | Track availability, latency percentiles, error budgets                           | Low      |
| **Log aggregation** (Loki + Promtail)        | 2-3 days | Centralized logs searchable via Grafana                                          | Medium   |
| **Custom CasCor dashboard**                  | 1 day    | Training-specific: loss curves, candidate pool heatmaps, network growth timeline | Low      |

**Recommendation**: Mark base implementation as COMPLETE. Alerting rules are the highest-value enhancement for production readiness.

---

### Docker Secrets Management — Detailed Analysis

**Status**: ACTIONABLE — Partial implementation, needs application-side support
**Source**: Microservices Architecture Roadmap Phase 3, Section 3.7
**Estimated Effort**: 2-3 days across 4 repos
**Priority**: Medium — security hardening for production deployments

#### Current State

| Aspect                                | Status             | Details                                                                                     |
|---------------------------------------|--------------------|---------------------------------------------------------------------------------------------|
| **`.env` files**                      | ✅ Exist           | `.env.example`, `.env.demo`, `.env.observability`, `.env.secrets.example` in juniper-deploy |
| **Compose secrets syntax**            | ❌ Not used        | No `secrets:` block in docker-compose.yml                                                   |
| **`_FILE` env var pattern**           | ❌ Not implemented | Services read secrets directly from env vars                                                |
| **`secrets.example/` directory**      | ❌ Not created     | Roadmap specifies this as documentation for required secrets                                |
| **Application `get_secret()` helper** | ❌ Not implemented | No fallback from file to env var                                                            |

#### Secrets Inventory

| Secret                        | Service(s)                   | Current Source                            | Risk                                 |
|-------------------------------|------------------------------|-------------------------------------------|--------------------------------------|
| `JUNIPER_DATA_API_KEY`        | juniper-data, juniper-cascor | Environment variable                      | Medium — visible in `docker inspect` |
| `GRAFANA_ADMIN_PASSWORD`      | grafana                      | `.env.observability` (default: `admin`)   | Low — local dev only                 |
| Database credentials (future) | juniper-data (PostgreSQL)    | Not yet needed (InMemory/LocalFS storage) | N/A                                  |

#### Implementation Plan

| Step | Change                                                            | Repos                                        | Effort  |
|------|-------------------------------------------------------------------|----------------------------------------------|---------|
| 1    | Create `get_secret(env_var, file_env_var)` utility function       | juniper-data, juniper-cascor, juniper-canopy | 2 hours |
| 2    | Replace direct `os.environ.get()` for secrets with `get_secret()` | Same 3 repos                                 | 1 hour  |
| 3    | Add `secrets:` block to docker-compose.yml                        | juniper-deploy                               | 30 min  |
| 4    | Create `secrets.example/` directory with placeholder files        | juniper-deploy                               | 15 min  |
| 5    | Add `secrets/` to `.gitignore`                                    | juniper-deploy                               | 5 min   |
| 6    | Document secret setup in README                                   | juniper-deploy                               | 30 min  |
| 7    | Tests: verify `_FILE` fallback works                              | All 3 services                               | 1 hour  |

**Application-side helper** (identical across all 3 services):

```python
def get_secret(env_var: str, file_env_var: str | None = None) -> str | None:
    """Read secret from env var, or from file at path in _FILE env var."""
    if file_env_var and (file_path := os.environ.get(file_env_var)):
        return Path(file_path).read_text().strip()
    return os.environ.get(env_var)
```

#### Risks

| Risk                                 | Likelihood | Impact | Mitigation                                                  |
|--------------------------------------|------------|--------|-------------------------------------------------------------|
| Breaking existing env var workflows  | Low        | Medium | `get_secret()` falls back to env var when `_FILE` not set   |
| Secrets files accidentally committed | Low        | High   | `.gitignore` + pre-commit hook + `secrets.example/` pattern |

---

### Remaining Long-Term Architecture Items

| Task                                          | Source                        | Status   | Notes                                                                             |
|-----------------------------------------------|-------------------------------|----------|-----------------------------------------------------------------------------------|
| WebSocket relay into Dash clientside_callback | Audit                         | DEFERRED | Requires significant Dash architecture rework; current REST polling is functional |
| Local CasCor operation within canopy          | CASCOR_DEMO_TRAINING (Step 4) | DEFERRED | Run CasCor as embedded library; complex dependency management                     |
| Kubernetes deployment via k3s                 | Microservices Phase 4         | DEFERRED | Post-Docker maturity; current Docker Compose is sufficient                        |

---

### Icebox Priority Matrix

Items sorted by actionability and impact:

| Priority | Item                             | Actionable?  | Effort     | Next Step                                       |
|----------|----------------------------------|--------------|------------|-------------------------------------------------|
| 1        | CAN-DEF-005 (Dataset versioning) | Yes          | 5-8 days   | Phase 1: extend juniper-data model + API        |
| 2        | Docker secrets management        | Yes          | 2-3 days   | Create `get_secret()` utility across services   |
| 3        | Monitoring network enhancement   | Yes          | < 1 hour   | Add `monitoring` network to docker-compose.yml  |
| 4        | Alerting rules (Prometheus)      | Yes          | 2-3 days   | Add AlertManager + rules for critical metrics   |
| —        | CAN-DEF-008 (3D visualization)   | ✅ Complete  | —          | Mark complete; enhancements are optional        |
| —        | Network segmentation             | ✅ Complete  | —          | Mark complete; minor monitoring network gap     |
| —        | Observability stack              | ✅ Complete  | —          | Mark complete; alerting is optional enhancement |
| —        | CAN-020 (Multi-hierarchy)        | Blocked      | 11-17 days | Requires CasCor algorithm research              |
| —        | CAN-021 (Population view)        | Blocked      | 8-13 days  | Requires CAN-020 + population training          |

---

## Pre-Existing Test Failures

These failures exist on `main` before any changes and should be fixed in Sprint 1.

| Test                                                                                       | Error                       | Root Cause                                                                      |
|--------------------------------------------------------------------------------------------|-----------------------------|---------------------------------------------------------------------------------|
| `test_state_sync.py::test_sync_real_envelope_nested_status_fields`                         | `assert 1000 == 500`        | `max_epochs` default changed from 500→1000 but test assertion not updated       |
| `test_state_sync.py::test_sync_real_params_filter_non_param_fields`                        | `KeyError: 'learning_rate'` | Param key name changed (likely to `nn_learning_rate`) but test not updated      |
| `test_demo_training_convergence.py::test_accuracy_exceeds_chance_with_hidden_units`        | Timeout >60s                | Training convergence too slow for test timeout; needs relaxed params or mocking |
| `test_phase4_implementation.py::test_add_hidden_unit_calls_train_candidate_with_200_steps` | Timeout >60s                | PyTorch backward pass on real tensors exceeds pytest-timeout; needs mock        |

---

## Dependency Map

```bash
Sprint 1 (Foundation) ─────────────────────┐
                                            ▼
Sprint 2 (Backend Integration) ────────► Sprint 3 (Testing)
    │                                        │
    │  CAN-CRIT-001 (decision boundary)      │
    │  CAN-CRIT-002 (snapshots)              │
    │  P08-FIX-1 (lock granularity)          │
    │                                        ▼
    └──────────────────────────────────► Sprint 4 (DevOps)
                                            │
                                            ▼
                                     Sprint 5 (UI Core)
                                            │
                                 CAN-004 (tuning tab) ──┐
                                 CAN-017 (tooltips)     │
                                 CAN-016a (layout)      │
                                            │           │
                                            ▼           ▼
                                     Sprint 6 (UI Advanced)
                                        CAN-005 (pin/unpin) ◄── CAN-004
                                        CAN-014/015 (snapshots) ◄── CAN-CRIT-002
                                        CAN-018/019 (tutorials) ◄── CAN-017
```

### Critical Path

1. **Sprint 1** must complete first (pre-existing failures block CI trust)
2. **Sprint 2 Step 2.5** (UI lock fix) is the highest-impact UX improvement
3. **Sprint 2 Steps 2.1-2.2** (decision boundary + snapshots) are cross-repo — start early
4. **Sprint 5-6** are independent of Sprint 4 (DevOps)
5. **Sprint 6** depends on Sprint 5 for CAN-004 (tuning tab) and CAN-017 (tooltips)

---

## Execution Notes

- **Cross-repo work** (Sprints 2.1, 2.2): Requires coordinated PRs in juniper-cascor, juniper-cascor-client, and juniper-canopy. Use worktree isolation per repo.
- **Testing gates**: Each sprint should end with `pytest tests/unit/ tests/regression/ --timeout=30` passing with 0 failures (no exclusions after Sprint 1).
- **Branch strategy**: One feature branch per sprint step; PR to main after step-level verification.
- **Icebox review**: Re-evaluate icebox items after Sprint 4 completion when infrastructure is mature.

---
