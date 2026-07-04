# Deep Audit — juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client, juniper-deploy

**Date**: 2026-04-19
**Scope**: Focused deep audit of 5 repositories (source, tests, notes, CI, cross-repo alignment)
**Type**: Read-only analysis — no code changes made
**Status**: Current — validated against live codebases
**Predecessor**: `JUNIPER_ECOSYSTEM_CODE_AUDIT.md` (2026-04-17, broad 8-repo sweep)

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [1. juniper-cascor-client](#1-juniper-cascor-client)
- [2. juniper-cascor-worker](#2-juniper-cascor-worker)
- [3. juniper-data](#3-juniper-data)
- [4. juniper-data-client](#4-juniper-data-client)
- [5. juniper-deploy](#5-juniper-deploy)
- [6. Cross-Repository Issues (Consolidated)](#6-cross-repository-issues-consolidated)
- [7. Notes/Development History Validation](#7-notesdevelopment-history-validation)
- [8. Priority Action Items](#8-priority-action-items)

---

## Executive Summary

| Repository            | Version | Coverage | Bugs           | Security   | Performance | Code Quality | Notes Status                                        |
|-----------------------|---------|----------|----------------|------------|-------------|--------------|-----------------------------------------------------|
| juniper-cascor-client | 0.4.0   | 93.52%   | 5 (0 critical) | 2 low      | 3 low       | 7            | All planned work complete                           |
| juniper-cascor-worker | 0.3.0   | 91.47%   | 4 (2 medium)   | 4 low      | 3 low       | 5            | All planned work complete                           |
| juniper-data          | 0.6.0   | ~80%+    | 5 (2 medium)   | 4 (1 high) | 4 (1 high)  | 6            | Constants refactor complete; roadmap items deferred |
| juniper-data-client   | 0.4.0   | —        | 3 (1 critical) | 1 low      | 2 low       | 5            | Constants refactor complete                         |
| juniper-deploy        | 0.2.1   | —        | —              | 7 (1 high) | —           | —            | Multiple plans partially complete                   |

**Aggregate findings across all 5 repos**:

| Severity     | Count | Key Items                                                                                                                                                               |
|--------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Critical** | 2     | Generator name `"circle"` vs `"circles"`; `"moon"` nonexistent on server                                                                                                |
| **High**     | 4     | Path traversal in LocalFS store; AlertManager missing from compose; Prometheus rules not mounted; Docker secret name mismatch                                           |
| **Medium**   | 19    | Sync generators block event loop; metadata loading O(n); JSONDecodeError unhandled in worker; coverage gate title misleading; no docker-integration CI; 503 not retried |
| **Low**      | 33    | Version header drift; typing modernization; Dockerfile defaults; idle imports                                                                                           |
| **Info**     | 12    | Design decisions, minor doc drift                                                                                                                                       |

---

## 1. juniper-cascor-client

**Version**: 0.4.0 | **Python**: ≥3.11 | **Coverage**: 93.52% (248 branch, 1171 statements)
**Dependencies**: requests≥2.28.0, urllib3≥2.0.0, websockets≥11.0

### 1.1 Bugs

| ID        | Severity   | File:Line                    | Description                                                                                                                                                                                                     |
|-----------|------------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CC-BUG-01 | **Medium** | `ws_client.py:332`           | `_recv_loop` catches bare `Exception` — swallows all errors including programming bugs. Malformed server messages kill the recv task silently, leaving pending futures to time out individually.                |
| CC-BUG-02 | **Low**    | `ws_client.py:333-335`       | `_recv_loop` calls `set_exception()` on futures that may already be done (callers clean up via `_pending.pop` in `finally`). No-op but wasteful.                                                                |
| CC-BUG-03 | **Low**    | `client.py:113-114`          | `is_alive()` catches both `JuniperCascorClientError` and builtin `ConnectionError`. The latter is dead code — `requests.ConnectionError` propagates as `JuniperCascorConnectionError` (subclass of the former). |
| CC-BUG-04 | **Low**    | `testing/fake_client.py:692` | `get_metrics` removes `correlation` field inconsistently vs history entries.                                                                                                                                    |
| CC-BUG-05 | **Low**    | `client.py:380-383`          | `_handle_response` error extraction has two branches yielding different error messages for the same status code depending on server error format.                                                               |

### 1.2 Security

| ID        | Severity | File:Line           | Description                                                                                                  |
|-----------|----------|---------------------|--------------------------------------------------------------------------------------------------------------|
| CC-SEC-01 | **Low**  | `client.py:100`     | API key in plaintext over HTTP. Default URL is `http://`. No warning when API key is set with non-HTTPS URL. |
| CC-SEC-02 | **Low**  | `client.py:368-372` | Full URL included in error messages. Currently safe (no embedded credentials), but no scrubbing.             |

### 1.3 Code Quality

| ID       | Severity   | File:Line                         | Description                                                                                                                           |
|----------|------------|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| CC-CQ-01 | **Medium** | Multiple files                    | Version mismatch: file headers say `0.3.0` or `0.2.0` or `0.1.0`, package is `0.4.0`. AGENTS.md header is `0.3.0`.                    |
| CC-CQ-02 | **Medium** | `AGENTS.md:146`                   | `set_params()` method not documented in Architecture section.                                                                         |
| CC-CQ-03 | **Low**    | `tests/test_set_params.py`        | Missing `@pytest.mark.unit` markers — tests skipped when running `pytest -m unit`.                                                    |
| CC-CQ-04 | **Low**    | `testing/fake_client.py:536-549`  | `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes are dead code. `get_training_status()` uses a local `status_map` dict instead. |
| CC-CQ-05 | **Info**   | `constants.py:32`                 | `RETRY_ALLOWED_METHODS` includes `PUT` but client has no `_put` method and cascor has no PUT endpoints.                               |
| CC-CQ-06 | **Info**   | `.pre-commit-config.yaml:133-134` | Flake8 excludes `testing/` from source linting. ~1800 lines of shipped code only gets relaxed rules.                                  |
| CC-CQ-07 | **Info**   | Multiple files                    | `typing.List`/`typing.Dict` used instead of builtin generics (Python ≥3.11 minimum).                                                  |

### 1.4 Test Coverage Gaps

| File           | Coverage | Missing                                                                                                                              |
|----------------|----------|--------------------------------------------------------------------------------------------------------------------------------------|
| `client.py`    | 82.22%   | `wait_for_ready()` polling, JSON decode errors, fallback error message path                                                          |
| `ws_client.py` | 86.26%   | Real WebSocket errors, `ConnectionClosed` in stream, `disconnect()` cancellation                                                     |
| **Structural** | —        | No integration tests against live cascor; no `FakeCascorControlStream` (XREPO-03 confirmed); no test markers on `test_set_params.py` |

### 1.5 CI/CD

| ID       | Severity | Description                                                                                                       |
|----------|----------|-------------------------------------------------------------------------------------------------------------------|
| CC-CI-01 | **Low**  | CI tests Python 3.11-3.13 but `pyproject.toml` classifies 3.14.                                                   |
| CC-CI-02 | **Low**  | Flake8 and MyPy exclude `testing/` — shipped code not fully linted/typed.                                         |
| CC-CI-03 | **Info** | No scheduled security scan workflow (only on push).                                                               |
| CC-CI-04 | **Info** | `pyproject.toml` mypy `ignore_missing_imports = false` conflicts with pre-commit `--ignore-missing-imports` flag. |

---

## 2. juniper-cascor-worker

**Version**: 0.3.0 (unreleased constants refactor on main) | **Python**: ≥3.11 | **Coverage**: 91.47%
**Dependencies**: numpy≥1.24.0, torch≥2.0.0, websockets≥11.0

### 2.1 Bugs

| ID        | Severity   | File:Line              | Description                                                                                                                                                                                                      |
|-----------|------------|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CW-BUG-01 | **Medium** | `ws_connection.py:184` | `receive_json()` doesn't catch `json.JSONDecodeError`. Malformed JSON from server during registration crashes the worker instead of reconnecting gracefully.                                                     |
| CW-BUG-02 | **Medium** | `cli.py:79`            | `task_timeout` env override logic: if user explicitly passes `--task-timeout 3600` (the default value), code falls through to env var. Can't distinguish "user passed default" from "user didn't pass anything". |
| CW-BUG-03 | **Low**    | `task_executor.py:166` | Sigmoid derivative lambda computes `torch.sigmoid(x)` twice per call. Correct but inefficient.                                                                                                                   |
| CW-BUG-04 | **Low**    | `worker.py:169-194`    | `_message_loop` doesn't catch `WorkerConnectionError` from `receive()` — propagates to `run()` which handles it. Intentional design but means any exception during task handling also breaks the loop.           |

### 2.2 Security

| ID        | Severity | File:Line                  | Description                                                                                                                           |
|-----------|----------|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| CW-SEC-01 | **Low**  | `ws_connection.py:77`      | Server URL logged — could leak credentials if URL contains them (not current pattern).                                                |
| CW-SEC-02 | **Low**  | `config.py:139-149`        | No validation that TLS cert/key/CA paths exist on disk at startup. Confusing SSL error at connect time instead of clear config error. |
| CW-SEC-03 | **Low**  | `Dockerfile:58`            | Default `CASCOR_SERVER_URL=ws://localhost:8200/...` — misconfigured container silently connects to localhost.                         |
| CW-SEC-04 | **Info** | `ws_connection.py:207-219` | No private key file permission checking (standard Python SSL behavior).                                                               |

### 2.3 Code Quality

|    ID    | Severity | File:Line               | Description                                                                                 |
|----------|----------|-------------------------|---------------------------------------------------------------------------------------------|
| CW-CQ-01 | **Low**  | `worker.py:23,61-62`    | Mixes `Optional[X]` with `X \| None` syntax. `Union` imported but only used once.           |
| CW-CQ-02 | **Low**  | `constants.py:32`       | `MSG_TYPE_TOKEN_REFRESH` defined but never referenced — dead code (forward compatibility?). |
| CW-CQ-03 | **Low**  | `worker.py:113`         | Broad `except Exception` in main run loop. Intentional resilience but could mask bugs.      |
| CW-CQ-04 | **Low**  | `cli.py:94-105,133-143` | `_run_websocket` and `_run_legacy` duplicate signal handler setup.                          |

### 2.4 Test Coverage Gaps

| File               | Coverage | Missing                                                                                   |
|--------------------|----------|-------------------------------------------------------------------------------------------|
| `cli.py`           | 90.70%   | Second SIGINT force-exit path; post-`asyncio.run` log line                                |
| `task_executor.py` | 84.51%   | `all_correlations` as Tensor/ndarray path; unknown activation fallback                    |
| `worker.py`        | 90.00%   | Generic Exception catch; result_ack/error/unknown message dispatch                        |
| `ws_connection.py` | 89.71%   | ConnectionClosed handling; TLS cert loading                                               |
| **Structural**     | —        | No integration tests (marker defined, zero tests use it); no binary frame edge case tests |

### 2.5 CI/CD & Dockerfile

| ID         | Severity   | Description                                                                                                      |
|------------|------------|------------------------------------------------------------------------------------------------------------------|
| CW-CI-01   | **Low**    | CI tests 3.11-3.13, not 3.14 (Dockerfile uses python:3.14-slim).                                                 |
| CW-CI-02   | **Medium** | `security-scan.yml` doesn't use CPU-only torch index — pulls ~4GB CUDA torch.                                    |
| CW-DOCK-01 | **Low**    | Dockerfile `ENV CASCOR_SERVER_URL` (localhost) conflicts with `CMD` (juniper-cascor service name).               |
| CW-DOCK-02 | **Medium** | `requirements.lock` includes CUDA packages (~2-4GB) even though Dockerfile installs CPU-only torch. Image bloat. |

---

## 3. juniper-data

**Version**: 0.6.0 (unreleased hardcoded-values refactor on main) | **Python**: ≥3.12
**Framework**: FastAPI + Pydantic + NumPy
**Generators**: 8 (spiral, xor, gaussian, circles, checkerboard, csv_import, mnist, arc_agi)

### 3.1 Bugs

| ID        | Severity   | File:Line                        | Description                                                                                                                  |
|-----------|------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| JD-BUG-01 | **Medium** | `api/routes/datasets.py:416-434` | `batch_export` builds entire ZIP in memory. Up to 50 datasets → OOM risk for large datasets.                                 |
| JD-BUG-02 | **Medium** | `api/routes/datasets.py:107`     | `generator.generate(params)` is synchronous inside async handler. Blocks event loop for large datasets (MNIST: 60K samples). |
| JD-BUG-03 | **Low**    | `__init__.py:77`                 | `return arc_agi.Arcade(...) or None` — `or None` is dead code (Arcade() always returns a truthy instance).                   |
| JD-BUG-04 | **Low**    | `api/models/health.py:24`        | `datetime.now().timestamp()` uses naive (non-UTC) datetime. Rest of codebase uses `datetime.now(UTC)`.                       |
| JD-BUG-05 | **Low**    | `api/routes/health.py:57`        | Readiness probe `glob("*.npz")` only counts top-level files — misses versioned/nested storage.                               |

### 3.2 Security

| ID        | Severity   | File:Line                   | Description                                                                                                                                                                    |
|-----------|------------|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| JD-SEC-01 | **Medium** | `api/security.py:59`        | API key comparison not constant-time (`api_key in self._api_keys`). Timing side-channel attack. **STILL PRESENT** from prior audit.                                            |
| JD-SEC-02 | **Medium** | `api/security.py:116`       | Rate limiter `_counters` dict grows unbounded. No eviction/TTL/max-size. DoS vector. **STILL PRESENT**.                                                                        |
| JD-SEC-03 | **High**   | `storage/local_fs.py:52-58` | `dataset_id` concatenated into filesystem paths without sanitization. Path traversal via `../../` in user-supplied `dataset_id`. Documented in RD-006 tests but **NOT FIXED**. |
| JD-SEC-04 | **Low**    | `__main__.py:64`            | `os.environ["JUNIPER_DATA_STORAGE_PATH"] = args.storage_path` — sets env var from unvalidated user input.                                                                      |

### 3.3 Performance

| ID         | Severity   | File:Line                    | Description                                                                                          |
|------------|------------|------------------------------|------------------------------------------------------------------------------------------------------|
| JD-PERF-01 | **High**   | `api/routes/datasets.py:107` | Sync dataset generation blocks async event loop. Should use `asyncio.to_thread()`.                   |
| JD-PERF-02 | **Medium** | `storage/base.py:261,317`    | `filter_datasets` and `get_stats` load ALL metadata on every call. O(n) disk reads per request.      |
| JD-PERF-03 | **Medium** | `storage/base.py:169`        | `list_versions` loads all metadata then filters in Python. No database-level filtering for Postgres. |
| JD-PERF-04 | **Low**    | `api/routes/datasets.py:307` | `batch_create_datasets` runs sequentially. Could parallelize with thread pool.                       |

### 3.4 Code Quality

| ID       | Severity   | File:Line                           | Description                                                                               |
|----------|------------|-------------------------------------|-------------------------------------------------------------------------------------------|
| JD-CQ-01 | **Medium** | `api/app.py:142`                    | `app = create_app()` at module level — app created at import time, coupling to env state. |
| JD-CQ-02 | **Medium** | `storage/postgres_store.py:125-127` | `_get_connection()` calls `psycopg2.connect()` per operation — no connection pooling.     |
| JD-CQ-03 | **Low**    | `api/settings.py:13-82`             | 40+ private constants that are each used only once as defaults. Verbose but functional.   |
| JD-CQ-04 | **Low**    | `AGENTS.md:4` vs `pyproject.toml:7` | AGENTS.md header version `0.5.0` vs actual `0.6.0`.                                       |
| JD-CQ-05 | **Low**    | `__init__.py:81-88`                 | Deprecated `get_arc_agi_api()` present but emits no deprecation warning.                  |
| JD-CQ-06 | **Low**    | `storage/kaggle_store.py:158-161`   | Uses `random.shuffle` instead of `np.random.default_rng()`. Inconsistent RNG.             |

### 3.5 Test Coverage Gaps

- No end-to-end API tests with real filesystem storage
- No concurrent access tests for version allocation atomicity
- No rate limiter memory growth test
- Postgres and Redis stores not tested in CI (require live instances)
- ARC-AGI HuggingFace fallback path untested

### 3.6 CI/CD

| ID       | Severity   | Description                                                                    |
|----------|------------|--------------------------------------------------------------------------------|
| JD-CI-01 | **Medium** | Coverage gate step titled "95%" but `COVERAGE_FAIL_UNDER` is `80`. Misleading. |
| JD-CI-02 | **Low**    | `juniper-data-client` installed from Git `@main` not PyPI in CI.               |
| JD-CI-03 | **Low**    | CI workflow and `.pre-commit-config.yaml` headers say version `0.4.0` — stale. |

---

## 4. juniper-data-client

**Version**: 0.4.0 | **Python**: ≥3.12 | **Dependencies**: numpy≥1.24, requests≥2.28, urllib3≥2.0

### 4.1 Bugs

| ID        | Severity     | File:Line                       | Description                                                                                                                                             |
|-----------|--------------|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| DC-BUG-01 | **Critical** | `constants.py:90`               | `GENERATOR_CIRCLE = "circle"` — server has `"circles"` (plural). **All client calls using this constant will fail with 400 error.**                     |
| DC-BUG-02 | **Critical** | `constants.py:91`               | `GENERATOR_MOON = "moon"` — server has **no moon generator**. Calls will fail.                                                                          |
| DC-BUG-03 | **Medium**   | `tests/test_performance.py:332` | Live test uses `"circles"` (correct server name) but is inconsistent with client's own `GENERATOR_CIRCLE` constant.                                     |
| DC-BUG-04 | **Low**      | `client.py:526-529`             | `batch_update_tags`: `if add_tags:` truthiness check means `add_tags=[]` (empty list) omits key from payload. Server may interpret absence differently. |

### 4.2 Code Quality

| ID       | Severity   | File:Line             | Description                                                                                                                                                 |
|----------|------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DC-CQ-01 | **Medium** | `constants.py`        | Client missing constants for 5 server generators: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`.                                             |
| DC-CQ-02 | **Low**    | `client.py:10`        | `typing.Dict`/`typing.List`/`typing.Optional` used instead of builtin generics (Python ≥3.12).                                                              |
| DC-CQ-03 | **Low**    | `constants.py:29`     | `RETRY_ALLOWED_METHODS` includes `POST`/`DELETE` — retrying mutations can cause duplicates. Currently safe (server is idempotent) but should be documented. |
| DC-CQ-04 | **Info**   | `tests/conftest.py:7` | Version header says `0.3.1`, project is `0.4.0`.                                                                                                            |
| DC-CQ-05 | **Info**   | `constants.py:16`     | `from typing import List, Tuple` — deprecated with Python ≥3.12.                                                                                            |

### 4.3 Test Coverage Gaps

- **Critical**: FakeDataClient accepts `"circle"` and `"moon"` — masks the server mismatch. All unit tests pass but would fail against real server.
- No tests for `wait_for_ready()` timeout path.
- No error-path tests for batch endpoints via real client (only FakeDataClient).
- Missing generators (`gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi`) not tested.

### 4.4 CI/CD

| ID       | Severity | Description                                                                 |
|----------|----------|-----------------------------------------------------------------------------|
| DC-CI-01 | **Low**  | Security scan installs `.[dev]` (full dev deps) instead of minimal runtime. |
| DC-CI-02 | **Info** | No `claude.yml` workflow (unlike juniper-ml).                               |
| DC-CI-03 | **Info** | No weekly docs-full-check workflow.                                         |

---

## 5. juniper-deploy

**Version**: 0.2.1 | **Stack**: Docker Compose + Helm + Prometheus + Grafana + AlertManager

### 5.1 Docker Compose Issues

| ID       | Severity   | Description                                                                                                                                                                                                                                                                                          |
|----------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DD-DC-01 | **High**   | **Secret name/path mismatch**: Top-level `secrets` defines `juniper_data_api_key` (singular) but service env `JUNIPER_DATA_API_KEYS_FILE` points to `/run/secrets/juniper_data_api_keys` (plural). Docker mounts at singular path; app reads plural path. **Service will fail to find secret file.** |
| DD-DC-02 | **High**   | **AlertManager service missing**: `prometheus/prometheus.yml:34` references `alertmanager:9093` but **no alertmanager service exists** in `docker-compose.yml`. Config file `alertmanager/alertmanager.yml` exists but is never mounted or used.                                                     |
| DD-DC-03 | **High**   | **Prometheus rules not mounted**: `prometheus.yml` references `recording_rules.yml` and `alert_rules.yml`, but the compose volume mount only maps `prometheus.yml`. Rules files are NOT available inside the container. Prometheus will fail to load rules.                                          |
| DD-DC-04 | **Medium** | `juniper-cascor` binds to `0.0.0.0` — externally accessible. Compare to juniper-data which correctly uses `127.0.0.1`.                                                                                                                                                                               |
| DD-DC-05 | **Medium** | `juniper-canopy` (all variants) binds to `0.0.0.0` — externally accessible.                                                                                                                                                                                                                          |
| DD-DC-06 | **Medium** | No resource limits on any service. Planned for v0.3.0, not implemented.                                                                                                                                                                                                                              |
| DD-DC-07 | **Low**    | `juniper-cascor-demo` hardcodes all env vars without `${VAR:-default}` interpolation.                                                                                                                                                                                                                |

### 5.2 Kubernetes/Helm Issues

| ID        | Severity   | File                  | Description                                                                                                                                   |
|-----------|------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| DD-K8S-01 | **Medium** | `values.yaml:306`     | Redis `auth.enabled: false` — no authentication.                                                                                              |
| DD-K8S-02 | **Medium** | `values.yaml:334`     | Grafana admin password is empty string default.                                                                                               |
| DD-K8S-03 | **Medium** | K8s canopy deployment | Missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars. Canopy deployment won't wire to backend services. |
| DD-K8S-04 | **Low**    | `.env.example:45-48`  | Cassandra env vars documented; Helm chart has Cassandra subchart dependency; Docker Compose has no Cassandra service. Vestigial.              |

### 5.3 Security

| ID        | Severity   | Description                                         |
|-----------|------------|-----------------------------------------------------|
| DD-SEC-01 | **High**   | Docker secret name/path mismatch (see DD-DC-01).    |
| DD-SEC-02 | **Medium** | Cascor port bound to 0.0.0.0 (see DD-DC-04).        |
| DD-SEC-03 | **Medium** | Canopy port bound to 0.0.0.0 (see DD-DC-05).        |
| DD-SEC-04 | **Medium** | K8s Redis with no authentication (see DD-K8S-01).   |
| DD-SEC-05 | **Medium** | K8s Grafana admin password empty (see DD-K8S-02).   |
| DD-SEC-06 | **Low**    | `secrets/` directory on disk (gitignored properly). |

### 5.4 Observability Issues

| ID        | Severity   | Description                                                                                       |
|-----------|------------|---------------------------------------------------------------------------------------------------|
| DD-OBS-01 | **High**   | AlertManager config exists but is never deployed (see DD-DC-02).                                  |
| DD-OBS-02 | **High**   | Alert rules and recording rules exist but are not mounted in Prometheus container (see DD-DC-03). |
| DD-OBS-03 | **Medium** | No integration test for observability profile (Prometheus, Grafana, AlertManager).                |

### 5.5 Test Coverage Gaps

| Gap    | Severity   | Description                                                                                                                                                                 |
|--------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TST-01 | **Medium** | No Helm chart tests in CI (`helm lint` only in pre-commit, not CI).                                                                                                         |
| TST-02 | **Medium** | **No docker-integration CI job** — compose config validated but services never built/started/tested. Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from `ci.yml`. |
| TST-03 | **Low**    | No container security scanning (Trivy/Grype). Planned for v0.5.0.                                                                                                           |
| TST-04 | **Low**    | No `promtool check config`/`check rules` in CI.                                                                                                                             |
| TST-05 | **Low**    | No test for worker service startup/connectivity.                                                                                                                            |
| TST-06 | **Low**    | `test_health.py:38-43` — `_assert_cascor_envelope()` appears to be dead code (never called).                                                                                |

### 5.6 Scripts/Automation

| ID        | Severity | Description                                                                                            |
|-----------|----------|--------------------------------------------------------------------------------------------------------|
| DD-SCR-01 | **Low**  | `test_health_enhanced.sh` uses `curl` while other scripts use python3 urllib. Inconsistent dependency. |
| DD-SCR-02 | **Low**  | `Makefile` `clean` target doesn't include all profiles in `down` command.                              |
| DD-SCR-03 | **Low**  | `Makefile` `test` target doesn't call `prepare-secrets` first, but test profile uses secrets.          |
| DD-SCR-04 | **Low**  | CI compose validation creates stub build contexts for 3 repos but not juniper-cascor-worker.           |

---

## 6. Cross-Repository Issues (Consolidated)

### 6.1 Critical: Generator Name Mismatch (XREPO-01 — confirmed STILL PRESENT)

| Client Constant    | Client Value | Server Registry Key | Status                 |
|--------------------|--------------|---------------------|------------------------|
| `GENERATOR_SPIRAL` | `"spiral"`   | `"spiral"`          | ✅ Match               |
| `GENERATOR_XOR`    | `"xor"`      | `"xor"`             | ✅ Match               |
| `GENERATOR_CIRCLE` | `"circle"`   | `"circles"`         | ❌ **MISMATCH**        |
| `GENERATOR_MOON`   | `"moon"`     | *(not registered)*  | ❌ **NONEXISTENT**     |
| *(not defined)*    | —            | `"gaussian"`        | ❌ Missing from client |
| *(not defined)*    | —            | `"checkerboard"`    | ❌ Missing from client |
| *(not defined)*    | —            | `"csv_import"`      | ❌ Missing from client |
| *(not defined)*    | —            | `"mnist"`           | ❌ Missing from client |
| *(not defined)*    | —            | `"arc_agi"`         | ❌ Missing from client |

**Impact**: `FakeDataClient` masks this — unit tests pass but real server requests fail with 400.

### 6.2 Medium: 503 Not Retried (XREPO-02 — confirmed STILL PRESENT)

**File**: `juniper-cascor-client/constants.py:31`
`RETRYABLE_STATUS_CODES = [502, 504]` — 503 (Service Unavailable) not retried. Client fails immediately during cascor startup instead of backing off.

### 6.3 Medium: No FakeCascorControlStream (XREPO-03 — confirmed STILL MISSING)

`juniper-cascor-client/testing/__init__.py` exports `FakeCascorClient` and `FakeCascorTrainingStream` only. No fake for `CascorControlStream`. Consumers testing WebSocket control (e.g., `set_params`) cannot use the testing subpackage.

### 6.4 Medium: Protocol Constants Alignment is Manual

Worker protocol constants (`MSG_TYPE_*`, `BINARY_FRAME_*`) must remain bit-identical to cascor's `MessageType(StrEnum)` in `protocol.py`. Wave 5 verified alignment, but **no automated CI check exists**. A cascor protocol change could silently break worker connectivity.

### 6.5 Low: Version Header Drift (Multiple Repos)

| Repo           | `pyproject.toml` | `AGENTS.md` header | File headers   |
|----------------|------------------|--------------------|----------------|
| cascor-client  | 0.4.0            | 0.3.0 ⚠️           | 0.1.0–0.3.0 ⚠️ |
| cascor-worker  | 0.3.0            | 0.3.0 ✅           | —              |
| juniper-data   | 0.6.0            | 0.5.0 ⚠️           | —              |
| data-client    | 0.4.0            | —                  | 0.3.1 ⚠️       |
| juniper-deploy | 0.2.1            | 0.2.1 ✅           | —              |

### 6.6 High: Docker Infrastructure Gaps (juniper-deploy)

1. **AlertManager service missing** from docker-compose.yml but referenced by Prometheus
2. **Prometheus alert/recording rules not mounted** — only `prometheus.yml` is volume-mapped
3. **Docker secret name mismatch** — `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)
4. **K8s canopy deployment missing inter-service URLs** — won't connect to cascor or data services

---

## 7. Notes/Development History Validation

### 7.1 juniper-cascor-client — All Planned Work ✅ COMPLETE

| Plan                                       | Status                                                |
|--------------------------------------------|-------------------------------------------------------|
| Hardcoded values refactor → `constants.py` | ✅ Complete (126 lines, 330 test constants)           |
| AGENTS.md rewrite (P0–P2 priorities)       | ✅ Complete (header version needs bump 0.3.0 → 0.4.0) |

### 7.2 juniper-cascor-worker — All Planned Work ✅ COMPLETE

| Plan                                                       | Status                         |
|------------------------------------------------------------|--------------------------------|
| Hardcoded values refactor → `constants.py`                 | ✅ Complete (~70 replacements) |
| AGENTS.md drift remediation (42 items)                     | ✅ Complete                    |
| Pre-commit remediation (Bandit B105, deprecation warnings) | ✅ Complete                    |
| Cross-repo bit-identity Wave 5                             | ✅ Verified (no CI automation) |

**Outstanding**: No version bump for unreleased constants refactor. Integration test marker defined but zero tests.

### 7.3 juniper-data — Constants Refactor ✅; Roadmap Items Deferred

| Plan                                                              | Status                                   |
|-------------------------------------------------------------------|------------------------------------------|
| Hardcoded values Wave 1-4 (constants modules, generator defaults) | ✅ Complete                              |
| HTTP status codes → `starlette.status`                            | ✅ Complete                              |
| AGENTS.md rewrite                                                 | ✅ Complete (version header still 0.5.0) |

**Deferred items**: RD-008 (SIM117 test fixes), RD-015 (IPC/ZeroMQ), RD-016 (GPU), RD-017 (continuous profiling).

### 7.4 juniper-data-client — Constants Refactor ✅ COMPLETE

| Plan                                                    | Status             |
|---------------------------------------------------------|--------------------|
| Hardcoded values refactor (~89 values → `constants.py`) | ✅ Complete        |
| AGENTS.md audit remediation                             | ✅ Mostly complete |

### 7.5 juniper-deploy — Multiple Plans Partially Complete

| Plan                                                          | Status                                                                   |
|---------------------------------------------------------------|--------------------------------------------------------------------------|
| Post-release roadmap: Grafana dashboards, Prometheus alerting | ✅ Done (v0.2.0)                                                         |
| Post-release roadmap: Production compose (resource limits)    | ❌ Not done (v0.3.0)                                                     |
| Post-release roadmap: TLS termination                         | ❌ Not done (v0.3.0)                                                     |
| Post-release roadmap: Worker service                          | ✅ Done (v0.4.0)                                                         |
| Post-release roadmap: Container security scanning             | ❌ Not done (v0.5.0)                                                     |
| Post-release roadmap: Scheduled integration tests             | ❌ Not done (v0.5.0)                                                     |
| Hardcoded values refactor (Phases 1-2)                        | ✅ Done                                                                  |
| Hardcoded values Phase 3 (envsubst templating)                | ❌ Deferred                                                              |
| SOPS audit: key backup, rotation, onboarding, gitleaks        | ✅ Done                                                                  |
| SOPS audit: multi-key per environment (SOPS-002)              | ❌ Deferred (Phase 5)                                                    |
| SOPS audit: CI/CD decryption integration (SOPS-013)           | ⚠️ Partial (structural validation only)                                  |
| SOPS audit: Docker secrets + SOPS integration (SOPS-014)      | ❌ Deferred (Phase 5)                                                    |
| Phase 2 systemd implementation                                | ❌ **Entirely unstarted** — no `systemd/` directory, no service units    |
| Container validation CI job                                   | ❌ Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from `ci.yml` |
| Security remediation (R1.1-R2.3)                              | ✅ All done                                                              |

---

## 8. Priority Action Items

### 8.1 Critical (Fix Immediately)

| # | Repo                | Action                                                                                        |
|---|---------------------|-----------------------------------------------------------------------------------------------|
| 1 | juniper-data-client | Rename `GENERATOR_CIRCLE` from `"circle"` to `"circles"`                                      |
| 2 | juniper-data-client | Remove `GENERATOR_MOON` or confirm server-side generator exists                               |
| 3 | juniper-data-client | Update `FakeDataClient._GENERATOR_CATALOG` to match server registry                           |
| 4 | juniper-data-client | Add missing generator constants: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi` |

### 8.2 High (Fix Soon)

| # | Repo           | Action                                                                                   |
|---|----------------|------------------------------------------------------------------------------------------|
| 5 | juniper-data   | Fix path traversal in `LocalFSDatasetStore` — validate `dataset_id` against `../`        |
| 6 | juniper-deploy | Add AlertManager service to docker-compose.yml                                           |
| 7 | juniper-deploy | Mount `alert_rules.yml` and `recording_rules.yml` into Prometheus container              |
| 8 | juniper-deploy | Fix Docker secret name: `juniper_data_api_key` → `juniper_data_api_keys` (or vice versa) |
| 9 | juniper-deploy | Add inter-service URL env vars to K8s canopy deployment                                  |

### 8.3 Medium (Address in Next Sprint)

| #  | Repo                  | Action                                                         |
|----|-----------------------|----------------------------------------------------------------|
| 10 | juniper-data          | Use `hmac.compare_digest()` for API key comparison (SEC-01)    |
| 11 | juniper-data          | Add rate limiter eviction (TTL or bounded LRU cache) (SEC-02)  |
| 12 | juniper-data          | Wrap `generator.generate()` in `asyncio.to_thread()` (PERF-01) |
| 13 | juniper-cascor-client | Add 503 to `RETRYABLE_STATUS_CODES`                            |
| 14 | juniper-cascor-client | Implement `FakeCascorControlStream`                            |
| 15 | juniper-cascor-client | Narrow `_recv_loop` exception handler from bare `Exception`    |
| 16 | juniper-cascor-worker | Handle `json.JSONDecodeError` in `receive_json()`              |
| 17 | juniper-cascor-worker | Regenerate `requirements.lock` with CPU-only torch index       |
| 18 | juniper-deploy        | Add docker-integration CI job (build + start + health check)   |
| 19 | juniper-deploy        | Add resource limits to Docker Compose services                 |
| 20 | juniper-deploy        | Bind cascor and canopy ports to `127.0.0.1`                    |

### 8.4 Low (Backlog)

| #  | Repo           | Action                                                            |
|----|----------------|-------------------------------------------------------------------|
| 21 | All 5 repos    | Bump AGENTS.md and file header versions to match `pyproject.toml` |
| 22 | All 5 repos    | Modernize `typing.Dict`/`typing.List` → builtin generics          |
| 23 | cascor-client  | Add `@pytest.mark.unit` to `test_set_params.py`                   |
| 24 | cascor-client  | Remove dead code: `_STATE_TO_FSM`, `_STATE_TO_PHASE`              |
| 25 | cascor-worker  | Remove unused `MSG_TYPE_TOKEN_REFRESH` constant                   |
| 26 | juniper-data   | Add Postgres connection pooling                                   |
| 27 | juniper-data   | Emit deprecation warning for `get_arc_agi_api()`                  |
| 28 | juniper-deploy | Add Helm lint/template validation to CI                           |
| 29 | juniper-deploy | Add `promtool check` to CI                                        |
| 30 | juniper-deploy | Implement systemd service units (Phase 2 plan exists)             |
| 31 | juniper-deploy | Add container security scanning (Trivy/Grype)                     |

---

*End of deep audit report.*
