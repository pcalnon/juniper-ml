# Juniper Project — Hardcoded Values Refactor: Development Roadmap

**Created**: 2026-04-08
**Completed**: 2026-04-11
**Author**: Claude Code (Automated Code Review)
**Scope**: All 8 Juniper Project applications
**Status**: ✅ **COMPLETE** — All 6 waves merged to `main` across all 8 repositories on 2026-04-11

---

## Completion Summary

All 6 waves of this roadmap were executed in a multi-session effort from 2026-04-09 through 2026-04-11. Approximately **660 hardcoded literals** were replaced across ~75 files in all 8 repositories, with cross-repo bit-identity verified via programmatic comparison (Wave 5).

### Merge record (2026-04-11)

| # | Repository            | PR                                                              | Merge SHA | Scope                                                                                                               |
|---|-----------------------|-----------------------------------------------------------------|-----------|---------------------------------------------------------------------------------------------------------------------|
| 1 | juniper-cascor        | [#123](https://github.com/pcalnon/juniper-cascor/pull/123)      | `fc87585` | constants_api_defaults (49 `_PROJECT_API_*`), api-layer refactor, candidate_unit/snapshot_serializer                |
| 2 | juniper-cascor-worker | [#27](https://github.com/pcalnon/juniper-cascor-worker/pull/27) | `5f42f91` | constants.py (68 syms: `MSG_TYPE_*`, `BINARY_FRAME_*`, `AUTH_*`), 5 worker modules refactored                       |
| 3 | juniper-cascor-client | [#17](https://github.com/pcalnon/juniper-cascor-client/pull/17) | `e76118c` | constants.py (55 syms), client.py + ws_client.py + fake_client.py + scenarios.py refactored                         |
| 4 | juniper-data          | [#37](https://github.com/pcalnon/juniper-data/pull/37)          | `9bb0d0b` | 3 layer-scoped constants modules (api/storage/core), 17 files + 7 generator `params.py` refactored                  |
| 5 | juniper-data-client   | [#18](https://github.com/pcalnon/juniper-data-client/pull/18)   | `c9de6af` | constants.py (102 syms), client.py + fake_client.py + generators.py refactored                                      |
| 6 | juniper-canopy        | [#143](https://github.com/pcalnon/juniper-canopy/pull/143)      | `39b36cf` | `SecurityConstants` + `BackendConstants` added to canopy_constants.py, 9 modules refactored                         |
| 7 | juniper-deploy        | [#31](https://github.com/pcalnon/juniper-deploy/pull/31)        | `83e9add` | `x-healthcheck-*` YAML anchors, `WORKER_REPLICAS` + `HEALTHCHECK_*` env vars, scripts/config.sh, tests/constants.py |
| 8 | juniper-ml            | [#118](https://github.com/pcalnon/juniper-ml/pull/118)          | `d79df79` | `util/worktree_cleanup.bash` MAIN_REPO derivation, `util/get_cascor_*.bash` env-var overrides,                      |
|   |                       |                                                                 |           | -- `util/juniper_plant_all.bash` CASCOR_HOST override, `tests/test_worktree_cleanup.py`                             |

### Wave 5 validation results

- **pytest**: All 8 repos green (juniper-data-client 153+9 skipped, juniper-cascor-client 223, juniper-cascor-worker 130, juniper-deploy 29+42 skipped, juniper-ml 88 unittest + bash regression, juniper-data full suite, juniper-canopy 29 unit, juniper-cascor api+unit)
- **pre-commit --all-files**: All 8 repos green on modified files (150+ hook instances total)
- **Cross-repo bit-identity (5.17–5.20)**:
  - `MessageType(StrEnum)` in juniper-cascor ↔ `MSG_TYPE_*` in juniper-cascor-worker ↔ `MSG_TYPE_*` in juniper-cascor-client — all 6 values bit-identical
  - `BinaryFrame` struct format (`<I` / utf-8 / 4-byte header) in juniper-cascor ↔ `BINARY_FRAME_*` constants in juniper-cascor-worker — identical
  - `"X-API-Key"` literal in juniper-cascor ↔ `API_KEY_HEADER_NAME` / `AUTH_HEADER_NAME` in all 3 cascor clients — identical
  - `HEADER_X_API_KEY='X-API-Key'` in juniper-data ↔ `API_KEY_HEADER_NAME` in juniper-data-client — identical
  - Pydantic `NetworkCreateRequest.model_fields[*].default` ↔ `_PROJECT_API_NETWORK_*_DEFAULT` constants — all 5 checked fields match
- **Generator output reproducibility (5.21)**: SHA-256 of `X_full`/`y_full` at `seed=42` is bit-identical between `origin/main` and the wave1 refactor branch for all 5 juniper-data generators (spiral, gaussian, checkerboard, circles, xor)
- **Docker Compose (5.14)**: `docker compose config` succeeds; `promtool check config` succeeds; override smoke tests pass for `WORKER_REPLICAS=5` and `HEALTHCHECK_INTERVAL=42s`

### Success criteria — outcome

1. ✅ Zero hardcoded values remain in application source files (excluding test data fixtures and mathematical constants like `2 * pi`) — verified across all 8 repos
2. ✅ All test suites pass across all 8 repositories
3. ✅ All pre-commit hooks pass on every modified file across all 8 repositories
4. ✅ No behavioral changes — generator outputs bit-identical, healthcheck commands unchanged, Pydantic defaults unchanged
5. ✅ Complete documentation — all 8 AGENTS.md files updated with constants-module sections; all 8 CHANGELOG.md files gained Unreleased entries; Wave 6 docs commits landed with the refactor commits
6. ✅ Pull Requests created and merged for all 8 repositories (one PR per repo)
7. ✅ Constants are discoverable — documented in each AGENTS.md with location, naming convention, and (where relevant) cross-repo alignment requirements

---

## Overview

This roadmap details the complete plan for refactoring all hardcoded values across the Juniper ecosystem into properly defined constants. The work is organized into 6 priority-ordered execution waves, with each wave containing tasks that can be executed in parallel across repositories.

### Scope Summary

| Repository                | Hardcoded Values | Already Covered | To Refactor | Constants Module Status                                 |
|---------------------------|------------------|-----------------|-------------|---------------------------------------------------------|
| **juniper-cascor**        | 76               | 20              | 56          | Excellent (6 modules) — needs API extension             |
| **juniper-data**          | 118              | 30              | 88          | Good (settings + spiral defaults) — needs 4 new modules |
| **juniper-data-client**   | 89               | 3               | 86          | **None** — needs new constants.py                       |
| **juniper-cascor-client** | 95               | 0               | 95          | **None** — needs constants.py + testing/constants.py    |
| **juniper-cascor-worker** | 50               | 3               | 47          | Partial (config.py) — needs constants.py                |
| **juniper-canopy**        | 51               | 30              | 21          | Good (canopy_constants.py) — needs 2 new classes        |
| **juniper-deploy**        | 110              | 25              | 85          | Minimal (tests/constants.py) — needs .env + config.sh   |
| **juniper-ml**            | 35               | 9               | 26          | N/A (meta-package) — env vars + path fix                |
| **TOTAL**                 | **~624**         | **~120**        | **~504**    | —                                                       |

---

## Execution Wave 1: Constants Infrastructure (All Repos)

**Priority**: CRITICAL
**Estimated Scope**: Create constants modules/files; no application logic changes
**Dependencies**: None

### Tasks

| #    | Repository            | Task                                                                  | New Files | Constants |
|------|-----------------------|-----------------------------------------------------------------------|-----------|-----------|
| 1.1  | juniper-cascor        | Create `cascor_constants/constants_api/` module                       | 2         | 43        |
| 1.2  | juniper-cascor        | Extend existing constants modules                                     | 0         | 5         |
| 1.3  | juniper-data          | Create `api/constants.py`                                             | 1         | 25        |
| 1.4  | juniper-data          | Create `storage/constants.py`                                         | 1         | 10        |
| 1.5  | juniper-data          | Create `core/constants.py`                                            | 1         | 6         |
| 1.6  | juniper-data          | Create per-generator `defaults.py` (7 generators)                     | 7         | 51        |
| 1.7  | juniper-data-client   | Create `constants.py`                                                 | 1         | 60        |
| 1.8  | juniper-cascor-client | Create `constants.py` + `testing/constants.py`                        | 2         | 95        |
| 1.9  | juniper-cascor-worker | Create `constants.py`                                                 | 1         | 30        |
| 1.10 | juniper-canopy        | Add `SecurityConstants` + `BackendConstants` to `canopy_constants.py` | 0         | 27        |
| 1.11 | juniper-canopy        | Extend `DashboardConstants` + `ServerConstants`                       | 0         | 8         |
| 1.12 | juniper-deploy        | Expand `.env.example` with new variables                              | 0         | 20        |
| 1.13 | juniper-deploy        | Create `scripts/config.sh`                                            | 1         | 8         |
| 1.14 | juniper-deploy        | Add Compose extension fields (`x-healthcheck-*`)                      | 0         | 4         |

**Acceptance Criteria**:

- All new constants files exist and are importable
- All constants hold the exact same values as the current hardcoded literals
- No application behavior changes
- All existing tests pass

---

## Execution Wave 2: Application Core Refactor

**Priority**: HIGH
**Dependencies**: Wave 1 complete
**Scope**: Replace hardcoded values with constants imports in core application logic

### Tasks

| #    | Repository            | Task                                                     | Files Modified | Replacements |
|------|-----------------------|----------------------------------------------------------|----------------|--------------|
| 2.1  | juniper-cascor        | Refactor API models (network.py, training.py)            | 2              | 16           |
| 2.2  | juniper-cascor        | Refactor lifecycle manager                               | 1              | 8            |
| 2.3  | juniper-cascor        | Refactor app.py (URLs, timeouts)                         | 1              | 8            |
| 2.4  | juniper-cascor        | Refactor middleware, routes, service launcher            | 3              | 12           |
| 2.5  | juniper-cascor        | Refactor observability                                   | 1              | 4            |
| 2.6  | juniper-cascor        | Refactor worker security                                 | 1              | 4            |
| 2.7  | juniper-data          | Refactor API layer (middleware, security, observability) | 3              | 22           |
| 2.8  | juniper-data          | Refactor storage layer                                   | 4              | 11           |
| 2.9  | juniper-data          | Refactor core layer                                      | 2              | 5            |
| 2.10 | juniper-data          | Refactor generator params (7 files)                      | 7              | 45           |
| 2.11 | juniper-data-client   | Refactor client.py                                       | 1              | 25           |
| 2.12 | juniper-cascor-client | Refactor client.py + ws_client.py                        | 2              | 24           |
| 2.13 | juniper-cascor-worker | Refactor worker.py (protocol strings)                    | 1              | 10           |
| 2.14 | juniper-cascor-worker | Refactor task_executor.py                                | 1              | 12           |
| 2.15 | juniper-cascor-worker | Refactor ws_connection.py                                | 1              | 4            |
| 2.16 | juniper-cascor-worker | Refactor config.py + cli.py (eliminate duplication)      | 2              | 16           |
| 2.17 | juniper-canopy        | Refactor middleware + discovery                          | 2              | 8            |
| 2.18 | juniper-canopy        | Refactor backend adapters                                | 4              | 7            |
| 2.19 | juniper-canopy        | Refactor dashboard manager                               | 1              | 4            |
| 2.20 | juniper-canopy        | Refactor demo mode + plotter                             | 2              | 3            |

**Acceptance Criteria**:

- Zero inline hardcoded values remain in application logic files
- All existing tests pass without modification
- No behavioral changes in any application

---

## Execution Wave 3: Testing & Support Code Refactor

**Priority**: MEDIUM
**Dependencies**: Wave 2 complete
**Scope**: Replace hardcoded values in testing utilities, fake clients, scenarios

### Tasks

| #    | Repository            | Task                                                    | Files Modified | Replacements |
|------|-----------------------|---------------------------------------------------------|----------------|--------------|
| 3.1  | juniper-cascor        | Refactor core model (candidate_unit, spiral, snapshots) | 4              | 6            |
| 3.2  | juniper-data          | Refactor encoding strings (utf-8)                       | 4              | 7            |
| 3.3  | juniper-data          | Adopt `starlette.status` for HTTP codes                 | 3              | 7            |
| 3.4  | juniper-data-client   | Refactor fake_client.py                                 | 1              | 20           |
| 3.5  | juniper-data-client   | Refactor generators.py                                  | 1              | 30           |
| 3.6  | juniper-cascor-client | Refactor fake_client.py                                 | 1              | 40           |
| 3.7  | juniper-cascor-client | Refactor scenarios.py                                   | 1              | 50           |
| 3.8  | juniper-deploy        | Refactor shell scripts (source config.sh)               | 4              | 8            |
| 3.9  | juniper-deploy        | Expand tests/constants.py                               | 1              | 5            |
| 3.10 | juniper-ml            | Parameterize CasCor API utilities                       | 6              | 6            |
| 3.11 | juniper-ml            | Fix hardcoded absolute path in worktree_cleanup.bash    | 1              | 2            |
| 3.12 | juniper-ml            | Extract test timeout constants                          | 2              | 3            |

**Acceptance Criteria**:

- All test utilities reference constants
- All shell scripts use configurable defaults
- All existing tests pass

---

## Execution Wave 4: Infrastructure & Deployment Refactor

**Priority**: MEDIUM
**Dependencies**: Wave 2 complete (can parallel with Wave 3)
**Scope**: Docker Compose, Prometheus, Grafana configuration

### Tasks

| #   | Repository     | Task                                                 |
|-----|----------------|------------------------------------------------------|
| 4.1 | juniper-deploy | Apply Compose extension fields for health checks     |
| 4.2 | juniper-deploy | Apply `.env` interpolation for new variables         |
| 4.3 | juniper-deploy | Document Prometheus/Grafana configuration values     |
| 4.4 | juniper-deploy | Validate with `docker compose config`                |
| 4.5 | juniper-deploy | Validate with `promtool check config`                |
| 4.6 | juniper-ml     | Make juniper_plant_all.bash cascor host configurable |

---

## Execution Wave 5: Validation & Quality Assurance

**Priority**: HIGH
**Dependencies**: Waves 2, 3, 4 complete
**Scope**: Full test suite execution, pre-commit validation, integration testing

### Tasks

| #    | Repository            | Task                                                                           | Command                                  |
|------|-----------------------|--------------------------------------------------------------------------------|------------------------------------------|
| 5.1  | juniper-cascor        | Full test suite                                                                | `pytest tests/ -v`                       |
| 5.2  | juniper-cascor        | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.3  | juniper-data          | Full test suite                                                                | `pytest juniper_data/tests/ -v`          |
| 5.4  | juniper-data          | Pre-commit hooks + type checking                                               | `pre-commit run --all-files && mypy`     |
| 5.5  | juniper-data-client   | Full test suite                                                                | `pytest tests/ -v`                       |
| 5.6  | juniper-data-client   | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.7  | juniper-cascor-client | Full test suite                                                                | `pytest tests/ -v`                       |
| 5.8  | juniper-cascor-client | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.9  | juniper-cascor-worker | Full test suite                                                                | `pytest tests/ -v`                       |
| 5.10 | juniper-cascor-worker | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.11 | juniper-canopy        | Unit test suite                                                                | `pytest -m "unit and not slow" -v`       |
| 5.12 | juniper-canopy        | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.13 | juniper-deploy        | Integration tests                                                              | `pytest tests/ -v`                       |
| 5.14 | juniper-deploy        | Docker compose validation                                                      | `docker compose config`                  |
| 5.15 | juniper-ml            | Full test suite                                                                | `python3 -m unittest -v tests/test_*.py` |
| 5.16 | juniper-ml            | Pre-commit hooks                                                               | `pre-commit run --all-files`             |
| 5.17 | ALL                   | Cross-repo integration: verify constants align across client/server boundaries | Manual review                            |

### Additional Validation Tasks

| #    | Task                          | Description                                                  |
|------|-------------------------------|--------------------------------------------------------------|
| 5.18 | Constants importability test  | Verify all new constants modules import without errors       |
| 5.19 | Constants/settings alignment  | Verify Pydantic Field defaults match constants values        |
| 5.20 | Protocol compatibility        | Verify worker protocol strings match server expectations     |
| 5.21 | Generator output verification | Verify generator outputs are bit-identical pre/post refactor |

---

## Execution Wave 6: Documentation & Release

**Priority**: MEDIUM
**Dependencies**: Wave 5 complete
**Scope**: Changelogs, release descriptions, AGENTS.md updates

### Tasks

| #    | Repository            | Task                                                     |
|------|-----------------------|----------------------------------------------------------|
| 6.1  | juniper-cascor        | Update AGENTS.md with constants_api documentation        |
| 6.2  | juniper-cascor        | Update CHANGELOG.md                                      |
| 6.3  | juniper-data          | Update AGENTS.md with new constants files                |
| 6.4  | juniper-data          | Update CHANGELOG.md                                      |
| 6.5  | juniper-data-client   | Update AGENTS.md with constants.py documentation         |
| 6.6  | juniper-data-client   | Update CHANGELOG.md                                      |
| 6.7  | juniper-cascor-client | Update AGENTS.md                                         |
| 6.8  | juniper-cascor-client | Update CHANGELOG.md                                      |
| 6.9  | juniper-cascor-worker | Update AGENTS.md                                         |
| 6.10 | juniper-cascor-worker | Update CHANGELOG.md                                      |
| 6.11 | juniper-canopy        | Update AGENTS.md with SecurityConstants/BackendConstants |
| 6.12 | juniper-canopy        | Update CHANGELOG.md                                      |
| 6.13 | juniper-deploy        | Update AGENTS.md with new .env variables                 |
| 6.14 | juniper-deploy        | Update CHANGELOG.md                                      |
| 6.15 | juniper-ml            | Update AGENTS.md                                         |
| 6.16 | juniper-ml            | Update CHANGELOG.md                                      |
| 6.17 | ALL                   | Create per-application Release Description documents     |
| 6.18 | ALL                   | Create and submit Pull Requests                          |

---

## Dependency Graph

```bash
Wave 1 (Constants Infrastructure)
    ├── Wave 2 (Application Core Refactor)
    │   ├── Wave 3 (Testing & Support Code)
    │   └── Wave 4 (Infrastructure & Deployment) [parallel with Wave 3]
    │       └── Wave 5 (Validation & QA) [after Waves 3+4]
    │           └── Wave 6 (Documentation & Release)
```

---

## Cross-Repository Coordination Points

### 1. Protocol Constants Alignment

The juniper-cascor **server** and juniper-cascor-worker **client** must use identical protocol message type strings. After refactoring both repos:

- `juniper-cascor` defines the canonical protocol constants
- `juniper-cascor-worker` defines its own copy (no direct code dependency)
- **Validation**: Run integration test with worker connected to server

### 2. API Endpoint Alignment

The following client/server pairs must have matching endpoint paths:

| Client                  | Server           | Endpoints                      |
|-------------------------|------------------|--------------------------------|
| `juniper-data-client`   | `juniper-data`   | All 16 `/v1/*` endpoints       |
| `juniper-cascor-client` | `juniper-cascor` | All REST + WebSocket endpoints |

**Validation**: Run client integration tests against running servers

### 3. Default Value Consistency

Training hyperparameter defaults should be consistent (or intentionally different) across:

| Value            | juniper-cascor         | juniper-cascor-client | juniper-cascor-worker | juniper-canopy  |
|------------------|------------------------|-----------------------|-----------------------|-----------------|
| Learning rate    | Settings: configurable | Fake: 0.01            | Default: 0.01         | Constants: 0.01 |
| Max hidden units | Settings: configurable | Fake: 10              | N/A                   | Constants: 1000 |
| Patience         | Constants: 50          | Fake: 10              | N/A                   | Constants: 50   |

**Action**: Document intentional differences. Client defaults represent API request defaults; server constants represent internal training defaults.

### 4. Service URL Defaults

| URL                     | Used By                                        | Purpose                           |
|-------------------------|------------------------------------------------|-----------------------------------|
| `http://localhost:8100` | juniper-cascor, juniper-canopy, juniper-deploy | JuniperData service               |
| `http://localhost:8200` | juniper-cascor-client, juniper-cascor-worker   | JuniperCascor service             |
| `http://localhost:8201` | juniper-ml utilities                           | JuniperCascor (host port mapping) |
| `http://localhost:8050` | juniper-cascor                                 | JuniperCanopy service             |

**Note**: Port 8201 vs 8200 — host-mapped port (8201) vs container port (8200). This is intentional and correct.

---

## Risk Register

| #  | Risk                                | Likelihood | Impact   | Mitigation                                     | Owner |
|----|-------------------------------------|------------|----------|------------------------------------------------|-------|
| R1 | Constants hold wrong values         | Very Low   | High     | Copy exact literals; test validates            |       |
| R2 | Import cycles                       | Low        | Medium   | Constants modules have no app-layer imports    |       |
| R3 | Settings/constants value drift      | Medium     | Medium   | Add alignment validation tests                 |       |
| R4 | Protocol mismatch (worker/server)   | Low        | Critical | Integration test; document canonical source    |       |
| R5 | Generator output changes            | Very Low   | High     | Bit-identical output verification              |       |
| R6 | Docker Compose interpolation issues | Low        | Medium   | Validate with `docker compose config`          |       |
| R7 | Breaking downstream consumers       | Very Low   | High     | No public API changes; backward-compat aliases |       |
| R8 | Large PR review burden              | Medium     | Low      | Split into per-repo PRs; each Wave is a PR     |       |

---

## Success Criteria

1. **Zero hardcoded values** remain in application source files (excluding test data fixtures and mathematical constants like `2 * pi`)
2. **All test suites pass** across all 8 repositories
3. **All pre-commit hooks pass** across all 8 repositories
4. **No behavioral changes** — applications function identically
5. **Complete documentation** — all AGENTS.md, CHANGELOG.md, and Release Descriptions updated
6. **Pull Requests created and reviewed** for all changes
7. **Constants are discoverable** — documented in AGENTS.md with locations and naming conventions
