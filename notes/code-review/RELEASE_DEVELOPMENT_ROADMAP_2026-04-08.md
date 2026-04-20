# Juniper Ecosystem Release Development Roadmap

**Date**: 2026-04-08
**Companion documents**:

- `CROSS_PROJECT_CODE_REVIEW_2026-04-08.md` — Full findings with file:line references
- `RELEASE_PREPARATION_PLAN_2026-04-08.md` — Phased execution plan with fix details

---

## Overview

This roadmap organizes all required work from the cross-project code review into a prioritized, dependency-aware execution plan. Work is structured as phases with explicit entry/exit criteria.

---

## Phase 1: Critical Fixes (Blocking — No Release Without These)

**Entry criteria**: Code review complete
**Exit criteria**: All critical issues resolved, tests passing, pre-commit clean

| #    | Application           | Task                                           | Severity | Files                                           | Est. Complexity |
|------|-----------------------|------------------------------------------------|----------|-------------------------------------------------|-----------------|
| 1.1  | juniper-data          | Synchronize version to 0.6.0 across 4 files    | CRITICAL | `__init__.py`, `pyproject.toml`, `Dockerfile`   | Trivial         |
| 1.2  | juniper-data          | Implement CSV import path traversal protection | CRITICAL | `csv_import/generator.py`, `settings.py`        | Medium          |
| 1.3  | juniper-data-client   | Bump version to 0.4.0 across all files         | CRITICAL | `pyproject.toml`, `__init__.py`, `testing/*.py` | Trivial         |
| 1.4  | juniper-deploy        | Add `internal: true` to backend/data networks  | CRITICAL | `docker-compose.yml`                            | Trivial         |
| 1.5  | juniper-cascor-worker | Write CHANGELOG v0.3.0 entry                   | CRITICAL | `CHANGELOG.md`                                  | Medium          |
| 1.6  | juniper-cascor-worker | Create git tags v0.2.0, v0.3.0                 | CRITICAL | N/A (git ops)                                   | Trivial         |
| 1.7  | juniper-cascor-worker | Document v0.1.1 in CHANGELOG                   | CRITICAL | `CHANGELOG.md`                                  | Trivial         |
| 1.8  | juniper-ml            | Create git tags v0.2.1, v0.3.0                 | CRITICAL | N/A (git ops)                                   | Trivial         |
| 1.9  | juniper-data-client   | Write CHANGELOG v0.4.0 entry                   | CRITICAL | `CHANGELOG.md`                                  | Medium          |
| 1.10 | juniper-data-client   | Create git tag v0.3.2                          | CRITICAL | N/A (git ops)                                   | Trivial         |

### Task 1.2 Detail: CSV Import Path Traversal

**Approaches**:

| Approach                | Description                                                                            | Strengths                                               | Weaknesses                             | Risk     |
|-------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------|----------------------------------------|----------|
| A. Base dir restriction | Add `JUNIPER_DATA_IMPORT_DIR` setting; resolve paths relative to it; reject traversals | Preserves functionality; standard pattern; configurable | New setting required; migration needed | Low      |
| B. API disablement      | Remove csv_import from API registry; keep for Python-only use                          | Zero attack surface; simplest change                    | Reduces API functionality              | Very Low |
| C. Path validation only | Validate resolved path doesn't contain `..` components                                 | Simple implementation                                   | Incomplete (symlink bypass possible)   | Medium   |

**Recommendation**: Approach A — provides the strongest security posture while preserving functionality.

**Implementation outline**:

```python
# settings.py
import_dir: str = Field(default="/data/imports", env="JUNIPER_DATA_IMPORT_DIR")

# csv_import/generator.py
import_base = Path(settings.import_dir).resolve()
resolved = (import_base / params.file_path).resolve()
if not resolved.is_relative_to(import_base):
    raise ValidationError("Path traversal detected")
```

---

## Phase 2: High-Priority Fixes (Should Fix Before Release)

**Entry criteria**: Phase 1 complete
**Exit criteria**: All high-severity issues resolved, tests passing

| #    | Application           | Task                                | Severity | Files                                | Est. Complexity |
|------|-----------------------|-------------------------------------|----------|--------------------------------------|-----------------|
| 2.1  | juniper-ml            | Fix CI dependency-docs path         | HIGH     | `.github/workflows/ci.yml:244`       | Trivial         |
| 2.2  | juniper-ml            | Fix PID file parsing in chop_all    | HIGH     | `util/juniper_chop_all.bash:275-325` | Medium          |
| 2.3  | juniper-ml            | Populate [Unreleased] changelog     | HIGH     | `CHANGELOG.md`                       | Medium          |
| 2.4  | juniper-ml            | Add test_worktree_cleanup.py to CI  | HIGH     | `.github/workflows/ci.yml:109-110`   | Trivial         |
| 2.5  | juniper-data          | Write CHANGELOG 0.6.0 section       | HIGH     | `CHANGELOG.md`                       | Medium          |
| 2.6  | juniper-data          | Fix n_spirals fallback              | HIGH     | `datasets.py:114`                    | Trivial         |
| 2.7  | juniper-data          | Update Dockerfile label             | HIGH     | `Dockerfile:36`                      | Trivial         |
| 2.8  | juniper-data-client   | Add PATCH to retry methods          | HIGH     | `client.py:101`                      | Trivial         |
| 2.9  | juniper-data-client   | Add HTTP tests for 6 methods        | HIGH     | `tests/test_client.py`               | Medium          |
| 2.10 | juniper-cascor-client | Write CHANGELOG v0.2.0 + v0.3.0     | HIGH     | `CHANGELOG.md`                       | Medium          |
| 2.11 | juniper-cascor-client | Create git tags                     | HIGH     | N/A (git ops)                        | Trivial         |
| 2.12 | juniper-cascor-client | Document WebSocket reconnection gap | HIGH     | `README.md`                          | Low             |
| 2.13 | juniper-cascor-worker | Fix signal handler thread safety    | HIGH     | `worker.py:58,119-121`, `cli.py:95`  | Medium          |
| 2.14 | juniper-cascor-worker | Add core control flow tests         | HIGH     | `tests/` (new test file/class)       | High            |
| 2.15 | juniper-deploy        | Fix Makefile variables              | HIGH     | `Makefile:70-72`                     | Trivial         |
| 2.16 | juniper-deploy        | Fix Dockerfile.test COPY            | HIGH     | `Dockerfile.test:30`                 | Trivial         |
| 2.17 | juniper-deploy        | Correct AGENTS.md documentation     | HIGH     | `AGENTS.md`                          | Medium          |
| 2.18 | juniper-deploy        | Fix CHANGELOG image versions        | HIGH     | `CHANGELOG.md`                       | Trivial         |

### Task 2.2 Detail: PID File Parsing

**Approaches**:

| Approach           | Description                                                      | Strengths                                 | Weaknesses                                                   |
|--------------------|------------------------------------------------------------------|-------------------------------------------|--------------------------------------------------------------|
| A. `mapfile -t`    | Replace `read -d '' -r -a` with `mapfile -t JUNIPER_PIDS < file` | Minimal diff; retains array indexing      | Requires removing contradictory stdin redirect from for loop |
| B. while-read loop | Replace array + for-loop with `while IFS= read -r line`          | More explicit parsing; handles edge cases | Larger diff; different iteration pattern                     |

**Recommendation**: Approach A — minimal change, fixes the root cause.

### Task 2.13 Detail: Signal Handler Thread Safety

**Approaches**:

| Approach                  | Description                                                            | Strengths                           | Weaknesses                              |
|---------------------------|------------------------------------------------------------------------|-------------------------------------|-----------------------------------------|
| A. `call_soon_threadsafe` | Store event loop reference; use `loop.call_soon_threadsafe(event.set)` | Idiomatic asyncio; minimal change   | Loop may be None if stop() before run() |
| B. `threading.Event`      | Replace `asyncio.Event` with `threading.Event`; poll in async loop     | Eliminates all cross-thread asyncio | Requires polling logic; less clean      |

**Recommendation**: Approach A with None guard.

### Task 2.14 Detail: Worker Control Flow Tests

**Target**: Raise `worker.py` coverage from 68.23% to >80%

**Test cases needed**:

1. `run()` — normal startup, message processing, clean shutdown
2. `_heartbeat_loop()` — periodic heartbeat sending
3. `_message_loop()` — message dispatch to handler methods
4. `_handle_task_assign()` — task execution and result reporting
5. Connection loss and reconnection behavior
6. Stop event during reconnection backoff

**Approach**: Use `unittest.mock.AsyncMock` for WebSocket connection, inject messages via mock's `recv` side effects, verify sent messages via mock's `send` assertions.

---

## Phase 3: Medium-Priority Improvements (Should Fix)

**Entry criteria**: Phase 2 complete
**Exit criteria**: All medium issues addressed or explicitly deferred with rationale

| #    | Application           | Task                                   | Severity | Files                                    |
|------|-----------------------|----------------------------------------|----------|------------------------------------------|
| 3.1  | juniper-ml            | Fix chop_all defaults and search term  | MEDIUM   | `util/juniper_chop_all.bash:69-71,82,84` |
| 3.2  | juniper-data          | Make Sentry PII configurable           | MEDIUM   | `observability.py:139`                   |
| 3.3  | juniper-data          | Align line-length with ecosystem (512) | MEDIUM   | `pyproject.toml` ruff config             |
| 3.4  | juniper-data-client   | Update REFERENCE.md                    | MEDIUM   | `docs/REFERENCE.md`                      |
| 3.5  | juniper-data-client   | Fix QUICK_START.md class name          | MEDIUM   | `docs/QUICK_START.md:138`                |
| 3.6  | juniper-data-client   | Update README API table                | MEDIUM   | `README.md`                              |
| 3.7  | juniper-cascor-client | Fix wait_for_ready semantic bug        | MEDIUM   | `client.py:86`                           |
| 3.8  | juniper-cascor-client | Add command() timeout                  | MEDIUM   | `ws_client.py:204`                       |
| 3.9  | juniper-cascor-client | Validate handshake message             | MEDIUM   | `ws_client.py:178`                       |
| 3.10 | juniper-cascor-client | Update README API table (+9 methods)   | MEDIUM   | `README.md`                              |
| 3.11 | juniper-cascor-client | Add tests for snapshot/dataset methods | MEDIUM   | `tests/test_fake_client.py`              |
| 3.12 | juniper-cascor-worker | Add task execution timeout             | MEDIUM   | `worker.py:201`                          |
| 3.13 | juniper-cascor-worker | Add WebSocket receive timeout          | MEDIUM   | `ws_connection.py:134`                   |
| 3.14 | juniper-cascor-worker | Check stop event in connect_with_retry | MEDIUM   | `ws_connection.py`                       |
| 3.15 | juniper-deploy        | Pin Redis image version                | MEDIUM   | `docker-compose.yml`                     |
| 3.16 | juniper-deploy        | Add Docker secrets for worker auth     | MEDIUM   | `docker-compose.yml`                     |
| 3.17 | juniper-deploy        | Remove misleading Grafana password     | MEDIUM   | `.env.observability:20`                  |
| 3.18 | juniper-deploy        | Document demo variant limitations      | MEDIUM   | `AGENTS.md` or `README.md`               |
| 3.19 | juniper-deploy        | Align version numbers                  | MEDIUM   | `AGENTS.md`, Helm `Chart.yaml`           |

---

## Phase 4: Documentation & Changelog Finalization

**Entry criteria**: Phases 1-3 complete
**Exit criteria**: All changelogs current, all docs accurate, release descriptions ready

| #   | Application           | Task                                                                      |
|-----|-----------------------|---------------------------------------------------------------------------|
| 4.1 | All 6                 | Final CHANGELOG review — ensure all changes since last tag are documented |
| 4.2 | All 6                 | Verify version consistency across all files                               |
| 4.3 | All 6                 | Draft release descriptions (use templates from code review)               |
| 4.4 | juniper-data-client   | Update REFERENCE.md version and content                                   |
| 4.5 | juniper-cascor-client | Update README with full API reference                                     |
| 4.6 | juniper-deploy        | Reconcile AGENTS.md with actual compose configuration                     |

---

## Phase 5: Pre-Release Validation

**Entry criteria**: Phase 4 complete
**Exit criteria**: All validation checks pass for all applications

### Per-Application Validation Matrix

| Check              | ML                | Data              | Data-Client       | CasCor-Client     | CasCor-Worker     | Deploy                  |
|--------------------|-------------------|-------------------|-------------------|-------------------|-------------------|-------------------------|
| Tests pass         | `unittest`        | `pytest`          | `pytest`          | `pytest`          | `pytest`          | `pytest`                |
| Coverage ≥80%      | N/A               | ≥80%              | ≥80%              | ≥80%              | ≥80%              | N/A                     |
| Pre-commit clean   | Yes               | Yes               | Yes               | Yes               | Yes               | Yes                     |
| CHANGELOG complete | Yes               | Yes               | Yes               | Yes               | Yes               | Yes                     |
| Version consistent | Yes               | Yes               | Yes               | Yes               | Yes               | Yes                     |
| Docs current       | Yes               | Yes               | Yes               | Yes               | Yes               | Yes                     |
| Build succeeds     | `python -m build` | `python -m build` | `python -m build` | `python -m build` | `python -m build` | `docker compose config` |
| Package valid      | `twine check`     | `twine check`     | `twine check`     | `twine check`     | `twine check`     | N/A                     |

---

## Phase 6: Release Execution

**Entry criteria**: Phase 5 validation passes for all applications
**Exit criteria**: All applications released and verified

### Release Order (Dependency-Aware)

```bash
Step 1: juniper-data v0.6.0          (no Juniper deps)
Step 2: juniper-data-client v0.4.0   (depends on juniper-data API)
Step 3: juniper-cascor-client v0.3.0 (depends on juniper-cascor API)
Step 4: juniper-cascor-worker v0.3.0 (depends on juniper-cascor)
Step 5: juniper-ml v0.4.0            (meta-package, depends on clients)
Step 6: juniper-deploy v0.2.0        (orchestration, depends on images)
```

### Per-Step Actions

For each step:

1. Ensure working branch is pushed to remote
2. Create PR to main (if not already merged)
3. Merge PR after CI passes
4. Create annotated git tag: `git tag -a v<VERSION> -m "Release v<VERSION>"`
5. Push tag: `git push origin v<VERSION>`
6. Create GitHub release with release description
7. Verify CI publish workflow succeeds (PyPI packages)
8. Verify installation: `pip install <package>==<VERSION>`
9. Update downstream dependency pins if needed

---

## Low-Priority / Post-Release Work

These items were identified during the code review but are not release blockers. They should be tracked as issues for future sprints.

| #    | Application           | Task                                             | Severity     |
|------|-----------------------|--------------------------------------------------|--------------|
| P.1  | juniper-ml            | Fix typos in wake_the_claude.bash                | LOW          |
| P.2  | juniper-ml            | Remove hardcoded paths from utility scripts      | LOW          |
| P.3  | juniper-ml            | Remove/rewrite kill_all_pythons.bash             | LOW          |
| P.4  | juniper-ml            | Fix global_text_replace.bash no-op               | LOW          |
| P.5  | juniper-data          | Add rate limiter TTL eviction                    | LOW          |
| P.6  | juniper-data          | Make traces_sample_rate configurable             | LOW          |
| P.7  | juniper-data          | Add deprecation warning to get_arc_agi_api()     | LOW          |
| P.8  | juniper-data-client   | Fix live perf test generator names               | LOW          |
| P.9  | juniper-data-client   | Add FakeDataClient close() guard                 | LOW          |
| P.10 | juniper-data-client   | Document thread safety                           | LOW          |
| P.11 | juniper-cascor-client | Remove duplicate _success_envelope               | LOW          |
| P.12 | juniper-cascor-client | Add HTTP 401/403 exception mapping               | LOW          |
| P.13 | juniper-cascor-client | Add flake8 hook for testing submodule            | LOW          |
| P.14 | juniper-cascor-client | Implement WebSocket auto-reconnection            | LOW (future) |
| P.15 | juniper-cascor-worker | Wrap ValueError in WorkerConfigError             | LOW          |
| P.16 | juniper-cascor-worker | Validate backoff_max >= backoff_base             | LOW          |
| P.17 | juniper-cascor-worker | Explicit BaseManager close in disconnect()       | LOW          |
| P.18 | juniper-deploy        | Remove duplicate pytest.ini                      | LOW          |
| P.19 | juniper-deploy        | Fix network placement for demo-seed/test-runner  | LOW          |
| P.20 | juniper-deploy        | Add health check condition to Grafana depends_on | LOW          |

---

## Effort Estimates

| Phase                    | Tasks        | Estimated Effort | Parallelizable                |
|--------------------------|--------------|------------------|-------------------------------|
| Phase 1: Critical Fixes  | 10           | 4-6 hours        | Yes (per application)         |
| Phase 2: High-Priority   | 18           | 8-12 hours       | Yes (per application)         |
| Phase 3: Medium-Priority | 19           | 6-8 hours        | Yes (per application)         |
| Phase 4: Documentation   | 6            | 3-4 hours        | Yes (per application)         |
| Phase 5: Validation      | 6 apps       | 2-3 hours        | Partially                     |
| Phase 6: Release         | 6 releases   | 2-3 hours        | Sequential (dependency order) |
| **Total**                | **65 tasks** | **25-36 hours**  |                               |

Work within each phase is highly parallelizable across applications. The primary constraint is the sequential release execution in Phase 6 (dependency order).

---

## Success Criteria

The release preparation is complete when:

1. All 10 critical issues are resolved
2. All 18 high-priority issues are resolved
3. All medium-priority issues are resolved or explicitly deferred
4. All test suites pass (1394+ tests across 6 applications)
5. All pre-commit hooks pass for all 6 applications
6. All changelogs are complete and follow Keep a Changelog format
7. All versions are consistent across files within each application
8. All git tags exist for declared versions
9. All README and reference documentation reflect current API surfaces
10. All 6 applications are successfully published/deployed
