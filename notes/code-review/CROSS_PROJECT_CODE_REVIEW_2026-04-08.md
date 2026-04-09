# Cross-Project Code Review & Release Audit

**Date**: 2026-04-08
**Scope**: juniper-ml, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-deploy
**Reviewer**: Claude Code (Principal Engineer audit)
**Purpose**: Release readiness assessment for all 6 Juniper ecosystem applications

---

## Executive Summary

All 6 applications were subjected to comprehensive code review including full codebase audit, changelog validation against git history, test suite execution, pre-commit hook verification, and release blocker identification.

### Aggregate Results

| Application           | Version | Tests            | Coverage   | Pre-commit   | Critical | High   | Medium | Low    |
|-----------------------|---------|------------------|------------|--------------|----------|--------|--------|--------|
| juniper-ml            | 0.3.0   | 88 pass          | N/A (meta) | 16/16 pass   | 1        | 4      | 3      | 8      |
| juniper-data          | 0.5.0*  | 847 pass         | 98.66%     | 19/19 pass   | 2        | 3      | 2      | 3      |
| juniper-data-client   | 0.3.2*  | 136 pass, 9 skip | 90.36%     | 22/22 pass   | 3        | 2      | 3      | 5      |
| juniper-cascor-client | 0.3.0   | 208 pass         | 84.48%     | 22/22 pass   | 0        | 3      | 5      | 7      |
| juniper-cascor-worker | 0.3.0   | 101 pass         | 80.13%     | 22/22 pass   | 3        | 2      | 3      | 4      |
| juniper-deploy        | 0.2.0   | 14 pass          | N/A        | 9/9 pass     | 1        | 4      | 5      | 4      |
| **Totals**            |         | **1394 pass**    |            | **All pass** | **10**   | **18** | **21** | **31** |

*Version marked with asterisk indicates version mismatch detected across files.

### Cross-Cutting Themes

1. **Changelog debt is universal**: Every application has significant undocumented changes. This is the single most common blocker.
2. **Git tags are missing**: 4 of 6 applications reference versions in changelogs that have no corresponding git tag.
3. **Version inconsistencies**: juniper-data has version mismatches across 4 files; juniper-data-client has features beyond its declared version.
4. **Test coverage is strong**: All applications meet or exceed the 80% threshold. juniper-data leads at 98.66%.
5. **Pre-commit compliance is excellent**: All applications pass all configured hooks with zero issues.
6. **Documentation drift**: README and reference docs lag behind actual API surfaces in multiple projects.

---

## 1. juniper-ml (Meta-Package)

### Overview

- **Version**: 0.3.0 (pyproject.toml)
- **Tests**: 88 passed (60 + 11 + 17 Python) + 1 bash regression
- **Pre-commit**: 16/16 hooks pass
- **Build**: Successful; twine check passes

### Critical Issues

**C-ML-1: Missing git tags for v0.2.1 and v0.3.0**
CHANGELOG declares v0.2.1 (2026-03-06) and v0.3.0 (2026-03-12) as released, but no git tags exist. The publish workflow triggers on GitHub release events, so these versions were either never published or published without proper tagging. CHANGELOG footer comparison links produce 404 errors on GitHub.

### High Issues

**H-ML-1: CI dependency-docs job references wrong path** (`ci.yml:244`)
`bash scripts/generate_dep_docs.sh` fails because the file is at `util/generate_dep_docs.sh`. This CI job has been broken since the scripts-to-util directory rename.

**H-ML-2: juniper_chop_all.bash PID file parsing bug** (`util/juniper_chop_all.bash:275-325`)
`read -d '' -r -a JUNIPER_PIDS` splits on whitespace, not newlines. PID file lines like `juniper-data:           12345` are split into separate array elements. The `%%:*` and `#*:` operations fail to parse correctly. Additionally, the C-style for loop has contradictory stdin redirection. This script cannot correctly stop services.

**H-ML-3: Empty [Unreleased] section despite 100+ post-v0.3.0 commits**
Substantial features (systemd support, worker integration, startup/shutdown scripts, worktree cleanup v2) are completely undocumented in the changelog.

**H-ML-4: `scripts/test.bash` is outdated and non-functional**
References `nohup.out` (removed in security hardening), relies on `sleep 12` timing. Will not produce reliable results.

### Medium Issues

**M-ML-1: `test_worktree_cleanup.py` not run in CI** (`ci.yml:109-110`)
17 tests exist but are not executed in the pipeline.

**M-ML-2: `juniper_chop_all.bash` hardcoded defaults override env vars** (lines 69-71)
`KILL_WORKERS` hardcoded to `"1"`, then `${KILL_WORKERS:-0}` is a no-op. Documentation says default is `0`.

**M-ML-3: Overly broad worker search term** (`util/juniper_chop_all.bash:84`)
`WORKER_SEARCH_TERM="cascor"` matches any process with "cascor" including the cascor backend itself.

### Low Issues

- `--slient` typo in `wake_the_claude.bash:108` (should be `--silent`)
- `specfied` typo in `wake_the_claude.bash:343`
- Hardcoded paths in `worktree_cleanup.bash:38-39` and `worktree_new.bash:4`
- `global_text_replace.bash` replaces a string with itself (no-op)
- `worktree_new.bash:16` has extra closing brace in error message
- `resume_session.bash` contains hardcoded session UUID
- Stale TODO comment in `wake_the_claude.bash:53`
- `kill_all_pythons.bash` uses `sudo kill -9` on ALL Python processes indiscriminately

### Security Concerns

- `kill_all_pythons.bash`: Dangerous — kills all Python processes system-wide with `sudo kill -9`
- `claude_interactive.bash`: Auto-enables `--dangerously-skip-permissions` when DEBUG is TRUE (and DEBUG defaults to TRUE)
- `cleanup_open_worktrees.bash`: Runs `git add --all` and `git push` without confirmation

### Remediation Summary

1. Create retroactive git tags for v0.2.1 and v0.3.0
2. Fix CI path: `scripts/generate_dep_docs.sh` → `util/generate_dep_docs.sh`
3. Fix PID parsing: use `mapfile -t` instead of `read -d '' -r -a`
4. Populate [Unreleased] changelog section
5. Add `test_worktree_cleanup.py` to CI pipeline
6. Fix `KILL_WORKERS` default and worker search term

---

## 2. juniper-data (Dataset Generation REST Service)

### Overview

- **Version**: 0.5.0 (pyproject.toml) / 0.4.2 (**init**.py) / 0.4.0 (Dockerfile)
- **Tests**: 847 passed, 98.66% coverage
- **Pre-commit**: 19/19 hooks pass
- **Stack**: FastAPI, Pydantic v2, NumPy, 8 generators, 7 storage backends

### Critical Issues

**C-JD-1: Version mismatch across 4 files**

| Location | Version |
|----------|---------|
| `pyproject.toml [project].version` | 0.5.0 |
| `juniper_data/__init__.py __version__` | 0.4.2 |
| `Dockerfile` label | 0.4.0 |
| `pyproject.toml` header comment | 0.4.0 |

The health endpoint, Prometheus build_info metrics, and TestPyPI verification all report 0.4.2. Any PyPI publish would fail verification.

**C-JD-2: CSV import path traversal vulnerability** (`csv_import/generator.py:80-87`)
The `file_path` parameter from `CsvImportParams` is used directly via `Path(params.file_path)` without sanitization. An authenticated API user can read arbitrary server files. The code contains an explicit TODO acknowledging this vulnerability.

### High Issues

**H-JD-1: 60+ commits since v0.5.0 not in CHANGELOG**
Major features (dataset versioning CAN-DEF-005, batch endpoints CAN-DEF-006, Docker secrets, systemd support, Postgres concurrency fixes) are completely absent from changelog.

**H-JD-2: `params.n_spirals` fallback bug** (`datasets.py:114`)
`n_classes = arrays["y_train"].shape[1] if n_train > 0 else params.n_spirals` — uses a spiral-specific attribute as a generic fallback. Any non-spiral generator producing an empty training set raises `AttributeError`.

**H-JD-3: Stale Dockerfile image version label** (`Dockerfile:36`)
`org.opencontainers.image.version="0.4.0"` — three versions behind.

### Medium Issues

**M-JD-1: Sentry PII enabled by default** (`observability.py:139`)
`send_default_pii=True` sends IP addresses and PII to Sentry without explicit opt-in.

**M-JD-2: Line-length configuration inconsistency**
Ruff `line-length = 320` but ecosystem convention (parent CLAUDE.md) specifies 512.

### Low Issues

- Rate limiter `_counters` dict grows unbounded with unique IPs (no TTL eviction)
- `traces_sample_rate=1.0` sends all Sentry traces
- Deprecated `get_arc_agi_api()` has no `warnings.warn()` call

### Remediation Summary

1. Synchronize all version references to target release (0.6.0 recommended given post-0.5.0 features)
2. Implement path traversal protection: configurable `JUNIPER_DATA_IMPORT_DIR` base directory with traversal rejection
3. Write 0.6.0 changelog section covering all post-0.5.0 work
4. Fix `n_spirals` fallback with generic derivation
5. Update Dockerfile label
6. Make Sentry PII configurable (default False)

---

## 3. juniper-data-client (HTTP Client Library)

### Overview

- **Version**: 0.3.2 (code) — but no git tag exists for v0.3.2
- **Tests**: 136 passed, 9 skipped (live benchmarks), 90.36% coverage
- **Pre-commit**: 22/22 hooks pass
- **API Surface**: 20 public methods across 6 categories

### Critical Issues

**C-JDC-1: Version doesn't reflect API changes**
6 new public methods (`batch_delete`, `batch_create`, `batch_update_tags`, `batch_export`, `list_versions`, `get_latest`) and new `create_dataset` parameters were added after the 0.3.2 changelog entry. Per SemVer, new API surface requires a MINOR bump to 0.4.0.

**C-JDC-2: No git tag for v0.3.2**
CHANGELOG documents v0.3.2 but no git tag exists. Only `v0.3.0` and `v0.3.1-beta` tags exist. Publishing requires a GitHub release which requires a tag.

**C-JDC-3: CHANGELOG missing all post-0.3.2 features**
Three feature commits (batch operations, versioning, performance benchmarks) are absent from CHANGELOG.md.

### High Issues

**H-JDC-1: Real client HTTP tests missing for 6 methods**
`client.py` is at 75.68% coverage. All batch operations and versioning methods have zero HTTP-level test coverage via `@responses.activate`. They are only tested through `FakeDataClient`. URL construction, parameter serialization, or HTTP method errors would not be caught.

**H-JDC-2: PATCH excluded from retry allowed_methods** (`client.py:101`)
`batch_update_tags()` uses PATCH, but retry strategy only allows HEAD, GET, POST, DELETE. PATCH requests encountering transient errors fail immediately without retry.

### Medium Issues

**M-JDC-1: docs/REFERENCE.md stale** — version header says 0.3.1, missing batch and versioning documentation
**M-JDC-2: docs/QUICK_START.md references `FakeJuniperDataClient`** — should be `FakeDataClient`
**M-JDC-3: README API table incomplete** — missing 6 new methods

### Low Issues

- File header version drift (testing modules say 0.3.1)
- `FakeDataClient.close()` doesn't prevent subsequent operations
- Live performance test uses wrong generator names ("circles", "gaussian")
- Thread safety undocumented
- No `__repr__` on client class

### Remediation Summary

1. Bump version to 0.4.0 (new public API surface)
2. Write 0.4.0 changelog entry
3. Add PATCH to retry `allowed_methods`
4. Add HTTP-level tests for batch and versioning methods
5. Update README, REFERENCE.md, QUICK_START.md

---

## 4. juniper-cascor-client (HTTP/WebSocket Client Library)

### Overview

- **Version**: 0.3.0
- **Tests**: 208 passed, 84.48% coverage
- **Pre-commit**: 22/22 hooks pass
- **API Surface**: 42+ REST methods + 2 WebSocket stream classes

### High Issues

**H-JCC-1: CHANGELOG missing v0.2.0 and v0.3.0 entries**
Package is at v0.3.0 but CHANGELOG only documents v0.1.0. Only `v0.1.0` git tag exists.

**H-JCC-2: No git tags for v0.2.0 or v0.3.0**
GitHub releases cannot be created; PyPI publish cannot be triggered.

**H-JCC-3: No WebSocket automatic reconnection**
Neither `CascorTrainingStream` nor `CascorControlStream` implements reconnection. For training runs lasting hours, a network hiccup silently terminates the stream with no recovery. Consumers must implement their own reconnection.

### Medium Issues

**M-JCC-1: `wait_for_ready()` calls `is_alive()` instead of `is_ready()`** (`client.py:86`)
Semantic bug — method name promises readiness but only checks liveness. A service can be alive without a network loaded.

**M-JCC-2: `CascorControlStream.command()` has no timeout** (`ws_client.py:204`)
`await self._ws.recv()` blocks indefinitely if the server stops responding.

**M-JCC-3: Handshake not validated in `CascorControlStream.connect()`** (`ws_client.py:178`)
Connection_established message consumed but not validated; error responses silently discarded.

**M-JCC-4: README API reference missing 9 methods**
Methods added in v0.2.0 and v0.3.0 (update_params, snapshots, workers, dataset_data) not in README.

**M-JCC-5: Snapshot/dataset_data FakeCascorClient methods have 0% test coverage**

### Low Issues

- Duplicate `_success_envelope` definition (dead code)
- No HTTP 401/403 exception mapping
- `response.json()` not protected against non-JSON 200 responses
- Retry strategy includes mutating HTTP methods
- `wait_for_ready` in FakeCascorClient doesn't acquire lock
- `get_metrics()` redundant `setdefault`
- Testing submodule bypasses flake8 linting

### Remediation Summary

1. Write CHANGELOG entries for v0.2.0 and v0.3.0
2. Create git tags
3. Fix `wait_for_ready()` to call `is_ready()`
4. Add timeout to `CascorControlStream.command()`
5. Validate handshake message
6. Update README API table
7. Add tests for uncovered fake client methods
8. Document WebSocket reconnection gap prominently

---

## 5. juniper-cascor-worker (Distributed Training Worker)

### Overview

- **Version**: 0.3.0
- **Tests**: 101 passed, 80.13% coverage (barely meets threshold)
- **Pre-commit**: 22/22 hooks pass
- **Architecture**: WebSocket-based async worker (default) + legacy multiprocessing mode (deprecated)

### Critical Issues

**C-JCW-1: CHANGELOG missing v0.3.0 entry**
The entire WebSocket worker rewrite, auth_token rename, setuptools security fix, and 30+ commits since v0.2.0 are undocumented. The `[Unreleased]` section is empty.

**C-JCW-2: Missing git tags for v0.2.0 and v0.3.0**
Only `v0.1.0` and `v0.1.1` tags exist. CHANGELOG comparison links reference non-existent `v0.2.0` tag.

**C-JCW-3: v0.1.1 tag undocumented**
Tag exists in git but has no CHANGELOG entry.

### High Issues

**H-JCW-1: `worker.py` at 68.23% coverage**
Core async control flows (`run()`, `_heartbeat_loop()`, `_message_loop()`) are entirely untested. These are the most critical production code paths. Overall coverage passes at 80.13% only because other modules compensate.

**H-JCW-2: Thread-unsafe `asyncio.Event.set()` from signal handler**
(`worker.py:121` called from `cli.py:95`) — `asyncio.Event` is documented as not thread-safe. The signal handler runs on the main thread while the event loop may be on another. Should use `loop.call_soon_threadsafe()`.

### Medium Issues

**M-JCW-1: No task execution timeout** (`worker.py:201`)
`asyncio.to_thread(_execute_task, ...)` has no timeout. A hung training task blocks indefinitely.

**M-JCW-2: No WebSocket receive timeout** (`ws_connection.py:134`)
`await self._ws.recv()` blocks indefinitely on silent server failure.

**M-JCW-3: `connect_with_retry` doesn't check stop event**
When `max_retries=None` (default), retry loop runs indefinitely. Shutdown response delayed up to 60 seconds.

### Low Issues

- `from_env()` doesn't wrap ValueError for invalid env vars
- `reconnect_backoff_max` not validated against `reconnect_backoff_base`
- No explicit BaseManager connection close
- Sigmoid derivative evaluates `torch.sigmoid` twice per call

### Concurrency Assessment

**WebSocket Mode**: Well-designed single-threaded asyncio with `asyncio.to_thread` for CPU-bound training. No shared mutable state between async loop and training thread. Primary concern is the thread-unsafe signal handler.

**Legacy Mode**: Standard multiprocessing with sentinel-based shutdown. Sentinel ordering not guaranteed but acceptable. Daemon processes prevent orphaning.

### Remediation Summary

1. Write CHANGELOG v0.3.0 entry (WebSocket rewrite, auth_token rename, TLS support, etc.)
2. Create git tags (and document v0.1.1)
3. Fix signal handler thread safety
4. Add tests for `run()`, `_heartbeat_loop()`, `_message_loop()` (target: worker.py > 80%)
5. Add task execution timeout
6. Add receive timeout parameter

---

## 6. juniper-deploy (Docker Compose Orchestration)

### Overview

- **Version**: 0.2.0 (documented in AGENTS.md; no formal release)
- **Tests**: 14/14 passed (security/availability unit tests)
- **Pre-commit**: 9/9 hooks pass
- **Scope**: 12 services across 5 profiles + Kubernetes Helm chart (v0.1.0)

### Critical Issues

**C-JDP-1: Network isolation not implemented as documented**
AGENTS.md states `backend` and `data` networks are "internal (no external access)" but neither has `internal: true` set in `docker-compose.yml` (lines 494-503). All networks allow external connectivity, contradicting the documented security model.

### High Issues

**H-JDP-1: Makefile `prepare-secrets` uses undefined variables** (`Makefile:70-72`)
`$(SECRETS_DIR)` and `$(SECRETS_FILES)` are never defined. `make up`, `make demo`, `make dev` all depend on this target. `mkdir -p ""` succeeds silently but creates nothing.

**H-JDP-2: Dockerfile.test copies non-existent file** (`Dockerfile.test:30`)
`COPY conftest.py .` fails because `conftest.py` is at `tests/conftest.py`, not repo root. The `test` profile cannot build.

**H-JDP-3: AGENTS.md documentation inconsistencies**

- Cassandra documented in `full` profile but absent from `docker-compose.yml`
- Redis documented in `demo` profile but only in `full` and `test`
- Redis documented with port binding but has none
- `make obs`/`make obs-demo` referenced but only `make monitor` exists

**H-JDP-4: CHANGELOG references outdated image versions**
Security section mentions "Prometheus v3.2.1, Grafana 11.5.2" but actuals are v3.10.0 and 12.4.0.

### Medium Issues

**M-JDP-1: `redis:7-alpine` floating minor version tag**
Should be pinned (e.g., `redis:7.4.2-alpine`) for reproducible builds.

**M-JDP-2: Worker auth token not managed via Docker secrets**
`juniper-cascor-worker` uses `CASCOR_AUTH_TOKEN` env var while all other services use Docker secret files.

**M-JDP-3: `.env.observability` contains misleading `GRAFANA_ADMIN_PASSWORD=admin`**
Not consumed by compose file (uses `__FILE` variant) but confusing.

**M-JDP-4: Demo variants lack security hardening**
`juniper-canopy-demo` and `juniper-cascor-demo` have no secret mounts, rate limiting, or observability configuration.

**M-JDP-5: Version alignment**
AGENTS.md says `0.2.0`, Helm chart appVersion is `0.4.0`, no pyproject.toml version field.

### Low Issues

- Duplicate pytest configuration in `pyproject.toml` and `pytest.ini`
- `demo-seed` network placement suboptimal (backend instead of data)
- `test-runner` not on `data` network
- Grafana `depends_on` lacks health check condition

### Remediation Summary

1. Add `internal: true` to `backend` and `data` networks
2. Define `SECRETS_DIR` and `SECRETS_FILES` in Makefile
3. Fix Dockerfile.test: remove `COPY conftest.py .`
4. Correct AGENTS.md documentation to match actual compose config
5. Update CHANGELOG with current image versions
6. Pin Redis image version
7. Add Docker secrets for worker auth token

---

## Cross-Project Issue Summary

### By Severity

| Severity | Count | Applications Affected |
|----------|-------|-----------------------|
| CRITICAL | 10 | All 6 |
| HIGH | 18 | All 6 |
| MEDIUM | 21 | All 6 |
| LOW | 31 | All 6 |
| **Total** | **80** | |

### By Category

| Category | Count | Description |
|----------|-------|-------------|
| Changelog gaps | 12 | Missing entries, wrong versions, empty sections |
| Missing git tags | 8 | CHANGELOG references versions without tags |
| Version mismatches | 5 | Different versions across files in same project |
| Test coverage gaps | 6 | Untested critical code paths |
| Security issues | 5 | Path traversal, PII exposure, network isolation |
| Documentation drift | 9 | README/docs don't match actual API |
| Code bugs | 8 | PID parsing, fallback bugs, thread safety |
| CI/CD issues | 4 | Wrong paths, missing tests in pipeline |
| Infrastructure | 7 | Floating tags, undefined vars, broken Dockerfiles |
| Code quality | 16 | Typos, dead code, hardcoded paths |

### Ecosystem-Wide Patterns

1. **No application has all git tags**: This is a systemic process gap. Releases are documented in changelogs but tags are not created, meaning GitHub releases and PyPI publishes may not have occurred.

2. **Changelog maintenance is deferred**: All 6 applications have significant undocumented work. This suggests changelog updates are not part of the PR/merge workflow.

3. **Version synchronization is manual**: juniper-data demonstrates the failure mode — 4 different version strings across the codebase.

4. **Documentation lags API changes**: Multiple applications have README API tables, reference docs, and quick-start guides that don't reflect the current API surface.
