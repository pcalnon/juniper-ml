# Juniper-Canopy: Deferred & Backlog Implementation Plan

**Created**: 2026-03-31
**Status**: PLAN — Ready for Execution
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

### Step 2.2: Snapshot REST Delegation (P1) — ⏳ BLOCKED (cross-repo)

| Task                                                            | Source       | Details                                                       | Status                          |
|-----------------------------------------------------------------|--------------|---------------------------------------------------------------|---------------------------------|
| Add `/v1/snapshots` endpoints to juniper-cascor                 | CAN-CRIT-002 | Save/load/list snapshot REST endpoints                        | ❌ Not started (juniper-cascor) |
| Add `save_snapshot()`/`load_snapshot()` to CascorServiceAdapter | CAN-CRIT-002 | Thin REST delegation to CasCor `/v1/snapshots` endpoints      | ❌ Blocked on cascor endpoints  |
| Update HDF5 snapshots panel for service mode                    | CAN-CRIT-002 | Wire panel to use adapter methods instead of local file paths | ❌ Blocked on adapter           |

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

**Goal**: Close all testing gaps, achieve coverage targets.
**Estimated Effort**: 2-3 days

### Step 3.1: Async/Sync Boundary Tests (P1) — ✅ COMPLETE (2026-03-31)

| Task                                         | Source       | Details                                                                                                                                                                                          | Status  |
|----------------------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Add dedicated async/sync boundary test suite | CAN-HIGH-003 | `test_async_sync_boundary.py`: 17 tests covering `run_in_executor`, `run_coroutine_threadsafe`, `broadcast_sync` vs `broadcast_from_thread` behavioral difference, concurrent delivery, errors | ✅ Done |

### Step 3.2: Real Backend Path Coverage (P1) — ✅ COMPLETE (2026-03-31)

| Task                         | Source       | Details                                                                                                                                                      | Status                               |
|------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| Add gated real-backend tests | CAN-HIGH-004 | Already extensive: 15+ test files use `FakeCascorClient` for service mode paths (unit + integration). Properly gated behind `CASCOR_BACKEND_AVAILABLE=1`     | ✅ Already done (pre-existing)       |
| Main.py coverage improvement | CAN-HIGH-008 | `test_main_endpoints_coverage.py`: 35 tests covering snapshots, health, layouts CRUD, Redis/Cassandra, remote workers. Coverage 72%→86% (+110 lines)         | ✅ Done                              |

### Step 3.3: Integration Test Expansion (P1) — ✅ COMPLETE (2026-03-31)

| Task                            | Source       | Details                                                                                                                                                                                                             | Status        |
|---------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| Convert remaining skipped tests | CAN-HIGH-007 | Already properly gated: `test_candidate_visibility` (`RUN_SERVER_TESTS=1` + `@pytest.mark.requires_server`), `test_mvp_functionality` (skip on connection error), `test_parameter_persistence`/`test_demo_endpoints` (server-gated) | ✅ Already gated |
| E2E JuniperData path tests      | CAN-MED-010  | Full import → train → retrieve path, gated behind env vars                                                                                                                                                           | Not started   |

### Step 3.4: Code Quality (P2) — ⏳ IN PROGRESS

| Task                               | Source        | Details                                                                                                                         | Status           |
|------------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------|------------------|
| Type annotation gaps               | CAN-MED-007   | `demo_mode.py`: all mypy errors resolved (8→0). Remaining: `service_backend.py`, `demo_backend.py` TypedDict return mismatches | ✅ Partial        |
| Test docstrings                    | CAN-MED-014   | Add descriptive docstrings to tests lacking them (bulk operation)                                                                | Not started      |
| Enable MyPy `warn_return_any=true` | Audit Backlog | Fix resulting type errors (~100+); do incrementally per module                                                                   | Not started      |
| Enable MyPy `strict_optional=true` | Audit Backlog | Fix resulting Optional-related errors (~100+); do incrementally                                                                  | Not started      |

---

## Sprint 4: DevOps & Deployment

**Goal**: Production-ready deployment infrastructure.
**Estimated Effort**: 3-5 days

### Step 4.1: Docker Compose Modernization (P2)

| Task                              | Source                | Details                                                                                                                     | Effort |
|-----------------------------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------|--------|
| Create Makefile in juniper-deploy | Microservices Phase 1 | Wrap Docker Compose: `up`, `down`, `restart`, `logs`, `status`, `build`, `clean`, `health`, `ps`, `shell-*`                 | 2-3 hr |
| Create health check script        | Microservices Phase 1 | `scripts/health_check.sh` hitting `/v1/health/ready` for all 3 services                                                     | 30 min |
| Add Docker Compose profiles       | Microservices Phase 3 | `dev`, `demo`, `full`, `test`, `monitor` profiles; `juniper-canopy-dev` (demo) and `juniper-canopy-demo` (service) variants | 2-3 hr |
| Docker Compose demo profile       | Microservices Phase 7 | Real CasCor with auto-start (`CASCOR_AUTO_TRAIN=true`, `CASCOR_DEMO_DATASET=two_spiral`)                                    | 1-2 hr |

### Step 4.2: Health Check Consolidation (P2)

| Task                      | Source                | Details                                                                                                                                                                  | Effort |
|---------------------------|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| Consolidate health routes | Microservices Phase 8 | Consolidate 5 health routes (`/health`, `/api/health`, `/v1/health`, `/v1/health/ready`, `/v1/health/live`) to 3 canonical routes; deprecate legacy routes with warnings | 1-2 hr |

### Step 4.3: Configuration Standardization (P2)

| Task                                               | Source                | Details                                                                                                                                              | Effort |
|----------------------------------------------------|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| Migrate env prefix `CASCOR_*` → `JUNIPER_CANOPY_*` | Microservices Phase 9 | Add `JUNIPER_CANOPY_*` as primary with `CASCOR_*` backward compat and deprecation warnings; already partially done in `settings.py` field validators | 2-3 hr |
| Add `.env` file support                            | Microservices Phase 9 | `.env.example`, `.env.dev`, `.env.prod` with documentation                                                                                           | 1 hr   |

### Step 4.4: Systemd Service Units (P3)

| Task                                           | Source                | Details                                                                                    | Effort |
|------------------------------------------------|-----------------------|--------------------------------------------------------------------------------------------|--------|
| Define systemd user service for juniper-canopy | Microservices Phase 2 | Unit file with dependency ordering, resource limits (2G RAM, 200% CPU), security hardening | 1-2 hr |
| Create `juniper-ctl` management CLI            | Microservices Phase 2 | start/stop/restart/status/logs/health/resources commands                                   | 3-4 hr |

---

## Sprint 5: UI Enhancements — Core

**Goal**: Most impactful UI improvements for everyday use.
**Estimated Effort**: 3-5 days

### Step 5.1: Training UX Improvements (P1 — UX)

| Task                             | Source    | Details                                                                         | Effort |
|----------------------------------|-----------|---------------------------------------------------------------------------------|--------|
| Meta parameter updates pause     | CAN-000   | Pause periodic backend sync when Apply Parameters is active                     | 30 min |
| Decision boundary poll frequency | P08-BUG-3 | Reduce boundary poll from 5s to 1-2s; or wire to WebSocket events for real-time | 1 hr   |
| Sliding window default fix       | P08-BUG-1 | Change default window or auto-adjust based on training activity density         | 30 min |

### Step 5.2: Tooltips & Help (P2)

| Task                         | Source  | Details                                                                     | Effort |
|------------------------------|---------|-----------------------------------------------------------------------------|--------|
| Add tooltips to all controls | CAN-017 | Use `dbc.Tooltip` on each control; define text in a constants/config module | 2-3 hr |

### Step 5.3: Layout Persistence (P3)

| Task                             | Source   | Details                                                                                    | Effort |
|----------------------------------|----------|--------------------------------------------------------------------------------------------|--------|
| Layout save/load to localStorage | CAN-016a | Serialize dashboard state (selected tab, chart zoom, window sizes) via clientside_callback | 3-4 hr |

### Step 5.4: Dataset Management (P3)

| Task                        | Source   | Details                                                                                   | Effort |
|-----------------------------|----------|-------------------------------------------------------------------------------------------|--------|
| Import/generate new dataset | CAN-016b | "New Dataset" button: import from file, URL, or JuniperData; generate spirals/XOR locally | 3-5 hr |

---

## Sprint 6: UI Enhancements — Advanced

**Goal**: Advanced features for power users and research workflows.
**Estimated Effort**: 5-8 days

### Step 6.1: Meta Parameter Tuning Tab (P3)

| Task                              | Source                  | Details                                                                                                                                                               | Effort |
|-----------------------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| Create meta parameter tuning tab  | CAN-004                 | New dashboard tab with all exposed meta params in organized sections                                                                                                  | 4-6 hr |
| Pin/unpin parameters to side menu | CAN-005                 | Drag-to-pin params from tuning tab to persistent side panel                                                                                                           | 2-3 hr |
| Individual parameter controls     | CAN-006 through CAN-013 | Network train epochs, candidate pool epochs, pool size, correlation threshold, optimizer, activation, selection count, integration mode — all tunable during training | 4-6 hr |

### Step 6.2: Snapshot & Replay (P3)

| Task                                | Source  | Details                                                                    | Effort |
|-------------------------------------|---------|----------------------------------------------------------------------------|--------|
| Snapshot captures with tuning state | CAN-014 | Record meta param values at each snapshot; store alongside network weights | 3-4 hr |
| Snapshot replay with tuning         | CAN-015 | Load snapshot and allow meta param modification during replay              | 3-5 hr |

### Step 6.3: Candidate Pool History (P3)

| Task                           | Source  | Details                                                                                 | Effort |
|--------------------------------|---------|-----------------------------------------------------------------------------------------|--------|
| Candidate pool history browser | CAN-003 | Retain candidate pool data for each cascade addition; expandable "Previous Pools" panel | 3-4 hr |

### Step 6.4: Tutorial System (P3)

| Task                        | Source  | Details                                                                            | Effort |
|-----------------------------|---------|------------------------------------------------------------------------------------|--------|
| Tutorial text (right-click) | CAN-018 | Right-click context menu with detailed descriptions and doc links                  | 3-4 hr |
| Guided walkthrough          | CAN-019 | Step-by-step highlighted tutorial using a tour library (dash-extensions or custom) | 5-8 hr |

---

## Icebox

Items requiring external dependencies, major architectural work, or with low near-term ROI.

### Requires External Changes (Cross-Repo)

| Task                           | Source       | Blocked By                             | Notes                                              |
|--------------------------------|--------------|----------------------------------------|----------------------------------------------------|
| Multi-hierarchy network view   | CAN-020      | Multi-hierarchy CasCor implementation  | CasCor doesn't support hierarchy yet               |
| Population network view        | CAN-021      | Population-based CasCor implementation | CasCor doesn't support populations yet             |
| Remote worker status dashboard | CAN-HIGH-005 | RemoteWorkerClient in CasCor           | Worker monitoring belongs in juniper-cascor-worker |
| Cassandra integration tests    | CAN-DEF-002  | Cassandra instance                     | Needs infrastructure provisioning                  |
| Redis integration tests        | CAN-DEF-003  | Redis instance                         | Needs infrastructure provisioning                  |
| Dataset versioning             | CAN-DEF-005  | JuniperData API versioning support     | Requires juniper-data feature                      |
| Dataset batch operations       | CAN-DEF-006  | JuniperData batch API                  | Requires juniper-data feature                      |

### Long-Term Architecture

| Task                                          | Source                        | Notes                                                                          |
|-----------------------------------------------|-------------------------------|--------------------------------------------------------------------------------|
| 3D network visualization                      | CAN-DEF-008                   | Research-grade; evaluate Dash VTK or three.js                                  |
| WebSocket relay into Dash clientside_callback | Audit                         | Replace/supplement REST polling; requires significant Dash architecture rework |
| Local CasCor operation within canopy          | CASCOR_DEMO_TRAINING (Step 4) | Run CasCor as embedded library; needs careful dependency management            |
| Kubernetes deployment via k3s                 | Microservices Phase 4         | Post-Docker maturity                                                           |
| Network segmentation                          | Microservices Phase 3         | Docker network isolation (backend/frontend/monitoring)                         |
| Observability stack (Prometheus + Grafana)    | Microservices Phase 3         | Needs Docker monitoring profile                                                |
| JuniperData performance benchmarks            | CAN-DEF-007                   | Useful but low urgency                                                         |
| Docker secrets management                     | Microservices Phase 3         | `secrets.example/` directory, `_FILE` env var pattern                          |

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
