# Juniper Project — Outstanding Development Items

**Date**: 2026-04-21
**Version**: 5.0.0
**Status**: Current — Validated via 10-agent audit (5 repo-focused + 5 cross-cutting concern agents) across all 8 repositories
**Scope**: All incomplete development work across the Juniper ecosystem
**Sources**: v4.0.0 document + 5-agent cross-cutting concern audit (concurrency, error handling, testing/CI, configuration, API contracts)

---

## Table of Contents

- [1. Purpose and Methodology](#1-purpose-and-methodology)
- [2. Validation Summary](#2-validation-summary)
- [3. Items Previously Incomplete — Now Fixed](#3-items-previously-incomplete--now-fixed)
- [4. Security Issues](#4-security-issues)
- [5. Active Bugs (Confirmed Still Present)](#5-active-bugs-confirmed-still-present)
- [6. Code Quality and Cleanup](#6-code-quality-and-cleanup)
- [7. Dashboard Enhancements](#7-dashboard-enhancements)
- [8. WebSocket Migration (R5-01 Remaining Phases)](#8-websocket-migration-r5-01-remaining-phases)
- [9. Microservices and Infrastructure](#9-microservices-and-infrastructure)
- [10. CasCor Algorithm and Feature Enhancements](#10-cascor-algorithm-and-feature-enhancements)
- [11. Cross-Repository Alignment Issues](#11-cross-repository-alignment-issues)
- [12. Housekeeping and Broken References](#12-housekeeping-and-broken-references)
- [13. juniper-deploy Outstanding Items](#13-juniper-deploy-outstanding-items)
- [14. juniper-data Outstanding Items](#14-juniper-data-outstanding-items)
- [15. Client Library Outstanding Items](#15-client-library-outstanding-items)
- [16. Performance Issues](#16-performance-issues-v4-new-section)
- [17. Source Document Lineage](#17-source-document-lineage)
- [18. Concurrency and Thread Safety Issues](#18-concurrency-and-thread-safety-issues-v5-new)
- [19. Error Handling and Robustness](#19-error-handling-and-robustness-v5-new)
- [20. Testing and CI/CD Gaps](#20-testing-and-cicd-gaps-v5-new)
- [21. Configuration and Dependency Issues](#21-configuration-and-dependency-issues-v5-new)
- [22. API Contract and Protocol Issues](#22-api-contract-and-protocol-issues-v5-new)
- [23. Validation Methodology (v5.0.0)](#23-validation-methodology-v500)

---

## 1. Purpose and Methodology

This document consolidates all **currently incomplete** development work across the Juniper ecosystem. It extends v3.0.0 (34-document cross-reference) with a **live codebase audit** performed by 5 specialized agents that independently scanned all source files, configuration, and infrastructure across all 8 active repositories.

**Validation method (v4.0.0)**: Five specialized audit agents independently performed deep code analysis of the live codebases, using file reads, grep pattern searches, and structural analysis. Each agent verified existing v3 items and identified new issues. Findings were deduplicated and cross-validated before integration.

**Validation method (v5.0.0)**: Five additional specialized agents audited **cross-cutting concerns** across all 8 repositories simultaneously: concurrency/threading, error handling/robustness, test coverage/CI, configuration/dependencies, and API contracts/protocol correctness. This complementary approach identified ~70 new items that per-repo audits missed. See [Section 23](#23-validation-methodology-v500) for details.

**Status legend**:

| Symbol | Meaning                                         |
|--------|-------------------------------------------------|
| ✅     | Fixed since last consolidation (newly resolved) |
| 🔴     | Still open — confirmed not implemented          |
| ⚠️     | Partially fixed — some elements still missing   |
| 🐛     | Bug confirmed still present                     |
| 🔵     | Deferred — explicitly decided to defer          |

---

## 2. Validation Summary

| Category                      | v4 Open | v5 Fixed | v5 Still Open | v5 New (v5) | Running Total |
|-------------------------------|---------|----------|---------------|-------------|---------------|
| Security                      | 16      | 0        | 16            | +0          | 16            |
| Active Bugs (cascor)          | 15      | 0        | 15            | +3          | 18            |
| Active Bugs (canopy)          | 10      | 0        | 10            | +2          | 12            |
| Active Bugs (data)            | 9       | 0        | 9             | +2          | 11            |
| Active Bugs (data/clients)    | 7       | 0        | 7             | +0          | 7             |
| Dashboard Augmentation        | 5       | 0        | 5             | +0          | 5             |
| WebSocket Migration           | 16      | 0        | 16            | +0          | 16            |
| Infrastructure                | 7       | 0        | 7             | +0          | 7             |
| Deploy Infrastructure         | 26      | 0        | 26            | +3          | 29            |
| Cross-Repo Alignment          | 14      | 0        | 14            | +5          | 19            |
| Housekeeping                  | 24      | 0        | 24            | +0          | 24            |
| CasCor Enhancements           | 9       | 0        | 9             | +0          | 9             |
| Code Quality                  | 30      | 0        | 30            | +0          | 30            |
| Client Libraries              | 29      | 0        | 29            | +0          | 29            |
| Performance                   | 7       | 0        | 7             | +0          | 7             |
| Concurrency (v5 new)          | —       | —        | —             | +9          | 9             |
| Error Handling (v5 new)       | —       | —        | —             | +10         | 10            |
| Testing/CI (v5 new)           | —       | —        | —             | +17         | 17            |
| Configuration/Deps (v5 new)   | —       | —        | —             | +16         | 16            |
| API/Protocol (v5 new)         | —       | —        | —             | +10         | 10            |
| **Grand total (v5)**          | **~230**| **0**    | **~230**      | **+~70**    | **~300**      |

---

## 3. Items Previously Incomplete — Now Fixed

### Fixed in v1–v3 (carried forward)

| Item                                            | Source                                 | Repo   | Evidence                                                                                                                |
|-------------------------------------------------|----------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------|
| **Task 2 Ph1**: Metadata-only graceful handling | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `dataset_plotter.py:361-364` — renders `"Dataset loaded (metadata only)"` empty plot                                    |
| **Task 1A**: Validation loss/accuracy overlays  | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:1449` — `_add_validation_overlay()` for val_loss (L1378) and val_accuracy (L1623)                     |
| **Task 1C**: Learning rate metric card          | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:441` — LR card with `_update_learning_rate_handler()` at L1041                                        |
| **Task 1D**: Phase duration display             | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `metrics_panel.py:157` — `phase-duration` ID; `_update_phase_duration_handler()` at L1082                               |
| **Phase C**: WebSocket `set_params`             | juniper-ml R5-01                       | canopy | `settings.py:182` — `use_websocket_set_params: bool = True`; `cascor_service_adapter.py:454,642` routes via WS          |
| **Phase D**: WS control buttons                 | juniper-ml R5-01                       | canopy | `settings.py:186` — `enable_ws_control_buttons: bool = True`; `dashboard_manager.py:1898` registers clientside callback |
| **Task 2 Ph2**: Dataset data endpoint           | juniper-ml DASHBOARD_AUGMENTATION_PLAN | canopy | `cascor_service_adapter.py:989` — `get_dataset_data()` delegates to client                                              |
| **Per-IP connection cap (canopy)**              | juniper-ml R5-01                       | canopy | `settings.py:99` — `max_connections_per_ip: int = 5`; `websocket_manager.py:269-291` enforces                           |
| **OPT-3**: Persistent output layer              | juniper-cascor dev record              | cascor | `cascade_correlation.py:1603-1607` — intentional fresh nn.Linear per call (documented design decision)                  |

### Newly confirmed fixed in v4

| Item                                    | v3 ID  | Repo   | Evidence                                                                                                                                                               |
|-----------------------------------------|--------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Request body limit for chunked encoding | SEC-08 | cascor | `src/api/middleware.py:58-89` — `RequestBodyLimitMiddleware` now stream-reads POST/PUT/PATCH bodies when Content-Length absent; caps at `_MAX_REQUEST_BODY_BYTES`      |
| Worker `worker_id` server-generated     | SEC-09 | cascor | `src/api/websocket/worker_stream.py:159-164` — server generates `worker_id = f"worker-{uuid.uuid4().hex[:12]}"`. Client-supplied value is stored as `client_name` only |

---

## 4. Security Issues

### 4.1 Original items (v3) — status updated

| ID     | Severity   | Repository     | Description                                                   | File                                      | Status (v4)                                                                                                                 |
|--------|------------|----------------|---------------------------------------------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| SEC-01 | **HIGH**   | juniper-data   | API key comparison not constant-time — timing side-channel    | `juniper_data/api/security.py:59`         | 🔴 Confirmed — `api_key in self._api_keys` (set membership)                                                                 |
| SEC-02 | **MEDIUM** | juniper-data   | Rate limiter memory unbounded — DoS vector                    | `juniper_data/api/security.py`            | 🔴 Confirmed — no eviction, TTL, or max-size                                                                                |
| SEC-03 | **MEDIUM** | juniper-cascor | No per-IP WebSocket connection limiting                       | `src/api/settings.py`                     | 🔴 Confirmed — only `ws_max_connections: 50` (global)                                                                       |
| SEC-04 | **LOW**    | juniper-data   | Sync dataset generation blocks event loop                     | `juniper_data/api/routes/datasets.py:107` | 🔴 Confirmed                                                                                                                |
| SEC-05 | **HIGH**   | juniper-canopy | Cross-Site WebSocket Hijacking (CSWSH) — no Origin validation | `/ws/training`, `/ws/control`             | 🔴 Confirmed                                                                                                                |
| SEC-06 | **MEDIUM** | juniper-canopy | No auth on canopy WS endpoints                                | WebSocket endpoints                       | 🔴 Confirmed                                                                                                                |
| SEC-07 | **MEDIUM** | juniper-cascor | Unvalidated `params` dict in `TrainingStartRequest`           | `TrainingStartRequest`                    | ⚠️ Partial fix — `_ALLOWED_TRAINING_PARAMS` whitelist filters key names at `training.py:36-52`, values are `Dict[str, Any]` |
| SEC-08 | ~~MEDIUM~~ | juniper-cascor | ~~Request body limit bypassed by chunked encoding~~           | `src/api/middleware.py:58-89`             | ✅ Fixed — `RequestBodyLimitMiddleware` now caps chunked bodies (see note below)                                            |
| SEC-09 | ~~MEDIUM~~ | juniper-cascor | ~~Worker `worker_id` client-supplied without validation~~     | `src/api/websocket/worker_stream.py:159`  | ✅ Fixed — server generates `worker_id`, client value stored as `client_name`                                               |
| SEC-10 | **LOW**    | juniper-data   | Sentry `send_default_pii=True`                                | Sentry configuration                      | 🔴 Confirmed                                                                                                                |

> **SEC-08 partial reopening**: While the middleware caps body size, it uses `await request.body()` (line 86) which reads the *full* body into memory before checking size. A malicious chunked body larger than RAM but smaller than OS socket buffer could cause memory exhaustion. See BUG-CC-15 below.

### 4.2 New security issues (v4)

| ID     | Severity   | Repository     | Description                                                   | File(s)                                           | Evidence                                                                                                          |
|--------|------------|----------------|---------------------------------------------------------------|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| SEC-11 | **HIGH**   | juniper-cascor | `pickle.loads` HDF5 snapshot data w/o `RestrictedUnpickler`   | `src/snapshots/snapshot_serializer.py:828`        | `pickle.loads(python_state_bytes)`: arbitrary code exec, crafted snapshots; `# trunk-ignore(bandit/B301)` comment |
| SEC-12 | **HIGH**   | juniper-canopy | `/ws` generic endpoint: no Origin validation, per-IP limit    | `src/main.py:2109-2127`                           | API key auth, miss `validate_origin()`, `check_per_ip_limit()` implemented by: `/ws/training`, `/ws/control`      |
| SEC-13 | **HIGH**   | juniper-canopy | Auth secrets exposed: query params via `/api/remote/connect`  | `src/main.py:2392`                                | `authkey` accepted query parameter: logged by web servers, saved browser history/referrer                         |
| SEC-14 | **MEDIUM** | juniper-canopy | Internal exception messages leaked to clients via `str(e)`    | `src/main.py:996, 2055, 2076, 2371, 2411`         | 5 endpoints return `str(e)` in JSON responses — may expose paths, library versions, connect strings               |
| SEC-15 | **MEDIUM** | juniper-cascor | Cascor sentry `send_default_pii=True` (same as SEC-10)        | `src/api/observability.py:176`, `src/main.py:129` | Both init sites set `send_default_pii=True` — API keys leak in headers to Sentry                                  |
| SEC-16 | **MEDIUM** | juniper-data   | `/metrics` Prometheus endpoint bypasses auth middleware       | `juniper_data/api/app.py:121`                     | Mounted ASGI sub-app: `SecurityMiddleware` for router-dispatched requests, not mounts                             |
| SEC-17 | **MEDIUM** | juniper-cascor | Snapshot `snapshot_id` path param, unchecked traversal chars  | `src/api/lifecycle/manager.py:883-904`,           | No regex rejecting `../`, special characters; glob-then-filter limits exposure, violates defense-in-depth         |
|        |            |                |                                                               | `src/api/routes/snapshots.py:48-64`               |                                                                                                                   |
| SEC-18 | **MEDIUM** | cascor-worker  | `_decode_binary_frame` no bounds check, malformed binary data | `juniper_cascor_worker/worker.py:330-343`         | Trusts header-encoded `ndim`, `shape`, `dtype_len`, no bounds check: crafted frame, cause OOM via `np.frombuffer` |

---

## 5. Active Bugs (Confirmed Still Present)

### 5.1 juniper-cascor

| ID        | Severity   | Description                                                            | File(s)                                                            | Evidence                                                                                                      |
|-----------|------------|------------------------------------------------------------------------|--------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| BUG-CC-01 | **MEDIUM** | `create_topology_message()` not fully implemented:                     | `src/api/websocket/messages.py:72`                                 | Defined and exported but zero production callers                                                              |
|           |            | -- topology changes never broadcast via WS                             |                                                                    |                                                                                                               |
| BUG-CC-02 | **MEDIUM** | `cascade_add` correlation hardcoded to `0.0`                           | `src/api/lifecycle/manager.py:427-430`                             | `monitor.on_cascade_add(hidden_unit_index=i, correlation=0.0)` — actual correlation is lost                   |
| BUG-CC-03 | **MEDIUM** | `or` fallback bugs for falsy values in spiral_problem.py               | `src/spiral_problem/spiral_problem.py:600-608,1250-1262,1411-1419` | `self.clockwise = clockwise or self.clockwise or DEFAULT` — falsy `False`/`0` silently overridden             |
| BUG-CC-04 | **LOW**    | Version strings inconsistent across file headers                       | `src/main.py` (0.3.1), `cascade_correlation.py` (0.3.2),           | All three disagree                                                                                            |
|           |            |                                                                        | -- `pyproject.toml` (0.4.0)                                        |                                                                                                               |
| BUG-CC-05 | **LOW**    | `remote_client_0.py` has hardcoded old monorepo path                   | `src/remote_client/remote_client_0.py:16`                          | `sys.path.append("/home/pcalnon/Development/python/Juniper/src/prototypes/cascor/src")`                       |
| BUG-CC-06 | **LOW**    | 32 test files have hardcoded `sys.path.append` to old monorepo         | `src/tests/` (32 files)                                            | Stale path references from pre-polyrepo era                                                                   |
| BUG-CC-07 | **MEDIUM** | `TrainingMonitor.current_phase` never updated by state machine         | `src/api/lifecycle/monitor.py:157`, `manager.py:272,395$,433`      | Manually set as str$ing, not managed by `TrainingStateMachine.phase` — can drift                              |
| BUG-CC-08 | **MEDIUM** | Undeclared global `shared_object_dict`                                 | Shared memory module                                               | Fails static analysis, fragile — relies on implicit global state                                              |
| BUG-CC-09 | **MEDIUM** | `validate_training_results` uninitialized variable when `max_epochs=0` | Training validation                                                | Causes crash when `max_epochs=0` — variable referenced before assignment                                      |
| BUG-CC-10 | **MEDIUM** | `validate_training`: `value_output`/`value_loss`/`value_accuracy`      | `src/cascade_correlation/cascade_correlation.py:4444`              | Variables only assigned inside `if x_val is not None` branch;                                                 |
|           |            | -- not initialized for no-validation-data path                         |                                                                    | -- verbose log at L4444 references them on else path — `UnboundLocalError` at VERBOSE log level               |
| BUG-CC-11 | **MEDIUM** | `_init_content_list` walrus operator precedence bug in `utils.py`      | `src/utils/utils.py:208`                                           | `content := _init_content_list(...) is not None` assigns `True`/`False` to `content`,                         |
|           |            |                                                                        |                                                                    | -- not the list — subsequent `.append()` raises `AttributeError`                                              |
| BUG-CC-12 | **MEDIUM** | `load_dataset` uses `yaml.safe_load` instead of `torch.load`           | `src/utils/utils.py:90-92`                                         | Changed from `torch.load` to `yaml.safe_load` but expects torch tensor keys:                                  |
|           |            |                                                                        |                                                                    | -- function is broken. Dead code (no callers)                                                                 |
| BUG-CC-13 | **MEDIUM** | `RateLimiter._counters` never pruned — unbounded memory growth         | `src/api/security.py:107`                                          | No expired entries cleaned; `ConnectionRateLimiter` has `_maybe_cleanup`, `RateLimiter` does not              |
| BUG-CC-14 | **LOW**    | `HandshakeCooldown._rejections` never pruned for non-blocked IPs       | `src/api/websocket/control_security.py:88,108-114`                 | Entries persist forever if IPs fail & never reach block threshold: minor mem leak                             |
| BUG-CC-15 | **MEDIUM** | `RequestBodyLimitMiddleware` reads full body before size check         | `src/api/middleware.py:86`                                         | `body = await request.body()`: body in mem before check `len(body) > self._max_bytes`: SEC-08 partial         |
| BUG-CC-16 | **MEDIUM** | `_last_state_broadcast_time` unprotected cross-thread R/W              | `src/api/lifecycle/manager.py:151-155`                             | Two concurrent callers can both pass throttle check and broadcast simultaneously (v5 new)                     |
| BUG-CC-17 | **MEDIUM** | `_extract_and_record_metrics()` split-lock — duplicate metric emission | `src/api/lifecycle/manager.py:453-495`                             | Lock released between reading and writing high-water-mark; duplicate metrics possible (v5 new)                |
| BUG-CC-18 | **HIGH**   | Dummy candidate results on double training failure — silent corruption | `src/cascade_correlation/cascade_correlation.py:1930-1962`         | When parallel AND sequential fallback both fail, dummy zero-correlation candidate installed silently (v5 new) |

### 5.2 juniper-canopy

| ID        | Severity   | Description                                             | File(s)                                                      | Evidence                                                                                                                      |
|-----------|------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| BUG-CN-01 | **HIGH**   | `_stop.clear()` race: `_perform_reset()` w/o lock       | `src/demo_mode.py:1614-1618`                                 | `_stop.clear()` at L1617 and `_pause.clear()` at L1618 outside lock block (lock covers L1615-1616)                            |
| BUG-CN-02 | **HIGH**   | DashboardManager god class (3,232 lines)                | `src/frontend/dashboard_manager.py`                          | 3,232 lines, 81 `def` functions — still growing                                                                               |
| BUG-CN-03 | **MEDIUM** | 226 `hasattr` guards, tests skip test logic             | `src/tests/` (226 occurrences)                               | Verified exact count: 226                                                                                                     |
| BUG-CN-04 | **MEDIUM** | `_api_base_url` hardcoded to `127.0.0.1`                | `cascor_service_adapter.py`                                  | Breaks in Docker/remote deployments                                                                                           |
| BUG-CN-05 | **MEDIUM** | Service populate param values w/ int defaults           | Parameter UI                                                 | UI shows incorrect values for params cascor doesn't expose                                                                    |
| BUG-CN-06 | **MEDIUM** | 1 Hz state throttle drops terminal transitions          | State update handling                                        | Fast Started→Failed→Stopped leaves dashboard showing Started forever                                                          |
| BUG-CN-07 | **LOW**    | Duplicate `APP_VERSION` assignment in module            | `src/main.py:90-93` and `src/main.py:110-113`                | Two identical `try/except` blocks for version extraction — copy-paste error                                                   |
| BUG-CN-08 | **MEDIUM** | `_demo_snapshots` list grows unbounded: demo mode       | `src/main.py:1345, 1444`                                     | `insert(0, snapshot)` with no cap or eviction — memory leak proportional to snapshot frequency                                |
| BUG-CN-09 | **MEDIUM** | `WebSocketManager.active_connections` not thread safe   | `src/communication/websocket_manager.py:178,239,304-310,446` | `broadcast_from_thread()` reads bg threads, `connect()`/`disconnect()` mod: `RuntimeError: Set changed size during iteration` |
| BUG-CN-10 | **LOW**    | `message_count` increment not atomic                    | `src/communication/websocket_manager.py:375`                 | `self.message_count += 1` not thread-safe — inaccurate statistics under concurrent broadcasts                                 |
| BUG-CN-11 | **MEDIUM** | `regenerate_dataset` mutates state without lock         | `src/demo_mode.py:1660-1676`                                 | train_x, train_y, epoch, loss mutated without `_lock` — training thread sees partial state (v5 new)                           |
| BUG-CN-12 | **LOW**    | `config_manager._load_config()` returns {} on any error | `src/config_manager.py:147-149`                              | Catches all exceptions including programming errors, returns empty config silently (v5 new)                                   |

### 5.3 juniper-data

| ID        | Severity   | Description                                                        | File(s)                          | Evidence                                                                                                                     |
|-----------|------------|--------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| BUG-JD-01 | **MEDIUM** | `batch_export` builds entire ZIP in memory — OOM risk              | `api/routes/datasets.py:416-434` | Large dataset exports accumulate entire ZIP in memory before sending response                                                |
| BUG-JD-02 | **MEDIUM** | `delete()` TOCTOU race condition — non-atomic check-then-unlink    | `storage/local_fs.py`            | Time-of-check to time-of-use race between existence check and file deletion                                                  |
| BUG-JD-03 | **MEDIUM** | `update_meta` writes without temp file — partial data exposure     | `storage/local_fs.py:221-226`    | Confirmed: `meta_path.write_text(...)` directly, while `save()` uses atomic temp-file-replace at L80-101                     |
| BUG-JD-04 | **MEDIUM** | Deterministic IDs with `seed=None` → stale cache returns           | `core/dataset_id.py`             | When seed is None, generated dataset ID is deterministic causing stale cache hits                                            |
| BUG-JD-05 | **LOW**    | `_version_lock` is class variable — won't work across workers      | `storage/base.py:23`             | Confirmed: `_version_lock = threading.Lock()` at class level — per-process, not per-cluster                                  |
| BUG-JD-06 | **LOW**    | `ReadinessResponse.timestamp` uses naive `datetime.now()`          | `api/models/health.py:24`        | All other timestamps use `datetime.now(UTC)`; this one produces local-time timestamps                                        |
| BUG-JD-07 | **MEDIUM** | `record_dataset_generation()` defined but never called             | `api/observability.py:218-229`   | Prometheus metrics `dataset_generations_total` and `generation_duration_seconds` never recorded from route handlers          |
| BUG-JD-08 | **LOW**    | `record_access()` defined but never called from API layer          | `storage/base.py:125-135`        | `access_count` and `last_accessed_at` fields never populated; TTL-based expiration by access won't work                      |
| BUG-JD-09 | **MEDIUM** | High-cardinality Prometheus labels from parameterized routes       | `api/observability.py:98`        | `endpoint = request.url.path` captures full path with dataset IDs — unbounded label cardinality; Prometheus OOM risk         |
| BUG-JD-10 | **HIGH**   | ALL storage operations block async event loop (extends JD-PERF-01) | `api/routes/datasets.py:98-424`  | get_meta, save, batch_export, batch_update_tags — all synchronous in async handlers; blocks ALL concurrent requests (v5 new) |
| BUG-JD-11 | **LOW**    | `record_access` TOCTOU race on access_count increment              | `storage/base.py:125-135`        | Two concurrent requests read same count, both increment, one lost (v5 new)                                                   |

---

## 6. Code Quality and Cleanup

### 6.1 juniper-cascor — Stale Code Removal

| ID        | Priority | Description                                                                                      | File(s)                                                                      | Effort      |
|-----------|----------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|-------------|
| CLN-CC-01 | **P2**   | Delete legacy `remote_client/` directory (3 files) — superseded by juniper-cascor-worker         | `src/remote_client/`                                                         | 10 min      |
| CLN-CC-02 | **P2**   | Delete stale `check.py` duplicate (600 lines) — copy of spiral_problem.py                        | `src/spiral_problem/check.py`                                                | 10 min      |
| CLN-CC-03 | **P2**   | Remove 9 local `import traceback` in cascade_correlation.py — uncomment line 64 top-level import | `cascade_correlation.py:64,2270,2804,3775,3840` + other files                | 30 min      |
| CLN-CC-04 | **P2**   | Enable mypy strict mode                                                                          | `pyproject.toml`                                                             | M           |
| CLN-CC-05 | **P2**   | Legacy spiral code — ~20 trivial getter/setter methods, no `@deprecated` markers                 | `src/spiral_problem/spiral_problem.py` (53 methods)                          | M           |
| CLN-CC-06 | **P3**   | Remove "Roll" concept in CandidateUnit                                                           | candidate_unit.py                                                            | 🔵 Deferred |
| CLN-CC-07 | **P3**   | Candidate factory refactor — all creation through `_create_candidate_unit()`                     | cascade_correlation.py                                                       | 🔵 Deferred |
| CLN-CC-08 | **P3**   | Remove commented-out code blocks                                                                 | Multiple files                                                               | 🔵 Deferred |
| CLN-CC-09 | **P3**   | Line length reduction to 120 characters                                                          | Multiple files                                                               | 🔵 Deferred |
| CLN-CC-10 | **P2**   | `utils.py:238` — fix broken `check_object_pickleability` function (uses `dill` not in deps)      | `src/utils/utils.py:238`                                                     | S           |
| CLN-CC-11 | **P2**   | `snapshot_serializer.py:~756` — extend optimizer support (per in-code TODO)                      | `snapshot_serializer.py`                                                     | M           |
| CLN-CC-12 | **P2**   | `.ipynb_checkpoints` directories committed to repository                                         | `src/cascade_correlation/.ipynb_checkpoints/`, `src/candidate_unit/`, `src/` | 10 min      |
| CLN-CC-13 | **P2**   | `sys.path.append` at module level in `cascade_correlation.py:69`                                 | `src/cascade_correlation/cascade_correlation.py:69`                          | S           |
| CLN-CC-14 | **P3**   | Empty `# TODO :` headers in 18+ files (boilerplate noise)                                        | Multiple file headers                                                        | S           |
| CLN-CC-15 | **P3**   | `_object_attributes_to_table` return type annotation wrong (`str` but returns `list`/`None`)     | `src/utils/utils.py:197`                                                     | S           |

### 6.2 juniper-canopy — Code Quality

| ID        | Priority | Description                                                                     | Evidence                                                                          | Effort |
|-----------|----------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|--------|
| CLN-CN-01 | **P2**   | `theme-table` CSS class never implemented                                       | No `.theme-table` in any CSS file                                                 | S      |
| CLN-CN-02 | **P2**   | NPZ validation only in DemoMode, not ServiceBackend                             | `_validate_npz_arrays()` exists only in `demo_mode.py:767`                        | S      |
| CLN-CN-03 | **P2**   | Performance test suite minimal — only 1 test file                               | `src/tests/performance/test_button_responsiveness.py` only                        | M      |
| CLN-CN-04 | **P2**   | JuniperData-specific error handling missing                                     | Only cascor-client errors caught; no juniper-data-client error classes            | M      |
| CLN-CN-05 | **P3**   | DashboardManager extraction (3,232 → component classes)                         | Blocked by R5-01 Phase B stability                                                | L      |
| CLN-CN-06 | **P2**   | Re-enable remaining MyPy disabled codes (7 codes)                               | 7 MyPy error codes currently suppressed                                           | M      |
| CLN-CN-07 | **P2**   | Real backend path test coverage                                                 | No tests exercise real CasCor paths — all use fakes/mocks                         | M      |
| CLN-CN-08 | **P2**   | Convert skipped integration tests (4 files with `requires_server`)              | 4 test files with `requires_server` skip marker                                   | M      |
| CLN-CN-09 | **P2**   | main.py coverage gap (84% vs 95% target)                                        | `main.py` at 84% coverage                                                         | S      |
| CLN-CN-10 | **P2**   | `main.py` is 2,543 lines — second god file                                      | 65 functions/methods; 30+ route handlers in a single file                         | L      |
| CLN-CN-11 | **P2**   | `metrics_panel.py` is 1,790 lines — third god file                              | 18 `@app.callback` decorators in single file                                      | L      |
| CLN-CN-12 | **P2**   | `network_visualizer.py:1512` — active TODO indicating logging error bug         | `# TODO: this is throwing a logging error` on `_create_new_node_highlight_traces` | S      |
| CLN-CN-13 | **P3**   | `demo_mode.py:938` — deprecated `_generate_spiral_dataset_local()` still called | `@deprecated` but called as fallback at L554 and L1667                            | S      |
| CLN-CN-14 | **P3**   | `np.random.seed(42)` sets global numpy seed in `demo_mode.py:960`               | Mutates global RNG state; affects all concurrent `np.random` users                | S      |

### 6.3 juniper-data — Code Quality (v4 new)

| ID        | Priority | Description                                                            | Evidence                                                                   | Effort |
|-----------|----------|------------------------------------------------------------------------|----------------------------------------------------------------------------|--------|
| CLN-JD-01 | **P2**   | `python-dotenv` is hard dependency for optional ARC-AGI feature        | `pyproject.toml` requires it; only used in `__init__.py:get_arc_agi_env()` | S      |
| CLN-JD-02 | **P2**   | `FakeDataClient.close()` destroys data, unlike real client             | `testing/fake_client.py:762-766` — clears `_datasets` on close             | S      |
| CLN-JD-03 | **P3**   | Module-level `create_app()` at `app.py:142` — import-time side effects | Reads env vars and creates middleware at import time                       | M      |

---

## 7. Dashboard Enhancements

### 7.0 Critical and High-Priority Enhancements (v3.0.0)

| ID           | Severity     | Description                                                                        | Status                                                                   |
|--------------|--------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| CAN-CRIT-001 | **CRITICAL** | Decision boundary non-functional in production/service mode                        | ⚠️ Partially resolved — core logic present but not wired in service mode |
| CAN-CRIT-002 | **CRITICAL** | Save/Load snapshot in adapter — prevents training session recovery in service mode | ⚠️ Scope reduced — blocked on `/v1/snapshots/*` API                      |
| CAN-HIGH-005 | **MEDIUM**   | Remote worker status dashboard                                                     | 🔴 NOT STARTED                                                           |
| KL-1         | **MEDIUM**   | Dataset scatter plot empty in service mode (known limitation)                      | 🔴 Known limitation                                                      |
| CAN-DEF-008  | **LOW**      | Advanced 3D node interactions                                                      | 🔵 Deferred                                                              |

### 7.1 Canopy Enhancement Backlog (CAN-000 through CAN-021)

All items 🔴 NOT STARTED unless otherwise noted. (Full table unchanged from v3 — see CAN-000 through CAN-021.)

| ID       | Module            | Description                                                               | Priority |
|----------|-------------------|---------------------------------------------------------------------------|----------|
| CAN-000  | Meta Param Menu   | Periodic updates pause when Apply Parameters button active                | P2       |
| CAN-001  | Training Metrics  | Training Loss time window toggle/dropdown                                 | P3       |
| CAN-002  | Training Metrics  | Custom rolling time window for Training Loss graph                        | P3       |
| CAN-003  | Training Metrics  | Retain candidate pool data per node addition; expandable "Previous Pools" | P3       |
| CAN-004  | Meta Param Tuning | New Tab for all exposed meta parameters                                   | P3       |
| CAN-005  | Meta Param Tuning | Pin/Unpin meta params from Tuning Tab to left side menu                   | P3       |
| CAN-006  | Meta Param Tuning | Network train epoch count parameter                                       | P3       |
| CAN-007  | Meta Param Tuning | Candidate pool training epoch count parameter                             | P3       |
| CAN-008  | Meta Param Tuning | Candidate pool node count parameter                                       | P3       |
| CAN-009  | Meta Param Tuning | Correlation threshold parameter                                           | P3       |
| CAN-010  | Meta Param Tuning | Optimizer type meta parameter                                             | P3       |
| CAN-011  | Meta Param Tuning | Activation function meta parameter                                        | P3       |
| CAN-012  | Meta Param Tuning | Number of top candidate nodes to select                                   | P3       |
| CAN-013  | Meta Param Tuning | Candidate node integration mode                                           | P3       |
| CAN-014  | Training Metrics  | Snapshot captures tuning values throughout training                       | P3       |
| CAN-015  | Training Metrics  | Snapshot replay with live tuning → new training session                   | P3       |
| CAN-016a | All               | Save/Load dashboard layout state                                          | P3       |
| CAN-016b | Dataset           | Import/Generate new dataset (file, URL, REST)                             | P3       |
| CAN-017  | All               | Tooltips on all dashboard controls                                        | P3       |
| CAN-018  | All               | Right-click tutorial descriptions with doc links                          | P4       |
| CAN-019  | All               | Walk-through style tutorial with highlighted steps                        | P4       |
| CAN-020  | All               | Show network at specific hierarchy level                                  | P4       |
| CAN-021  | All               | Show network in population (ensemble view)                                | P4       |

---

## 8. WebSocket Migration (R5-01 Remaining Phases)

### 8.1 Phases Now Complete

(Unchanged from v3 — Phases 0-cascor, A-SDK, B-pre-a, B, C, D all ✅ Complete.)

### 8.2 Phases Still Incomplete

| Phase | Goal                                           | Status                                         | Priority | Effort |
|-------|------------------------------------------------|------------------------------------------------|----------|--------|
| E     | Backpressure pump tasks                        | 🔴 NOT STARTED — conditional on telemetry data | P3       | M      |
| F     | Heartbeat jitter                               | 🔴 NOT STARTED                                 | P3       | S      |
| G     | Integration tests (cascor `set_params` via WS) | 🔴 NOT STARTED                                 | P2       | M      |
| H     | `_normalize_metric` audit                      | 🔴 NOT STARTED                                 | P3       | S      |

### 8.3 Critical Individual Gaps (from WebSocket Architecture Review)

(All 12 items unchanged from v3 — GAP-WS-16 through GAP-WS-32 + Phase B-pre-b. All 🔴 NOT STARTED.)

| ID            | Priority | Description                                                                                  | Status         |
|---------------|----------|----------------------------------------------------------------------------------------------|----------------|
| GAP-WS-16     | **P0**   | `/api/metrics/history` polling bandwidth bomb (~3 MB/s per dashboard tab)                    | 🔴 NOT STARTED |
| GAP-WS-14     | **P1**   | Plotly must use `extendTraces` with `maxPoints` — full figure rebuild is 80-200ms            | 🔴 NOT STARTED |
| GAP-WS-15     | **P1**   | Browser-side rAF coalescing needed for 50Hz candidate events                                 | 🔴 NOT STARTED |
| GAP-WS-13     | **P1**   | Lossless reconnect via sequence numbers and replay buffer — events lost during disconnect    | 🔴 NOT STARTED |
| GAP-WS-25     | **P1**   | WebSocket-health-aware polling toggle — both WS+REST run simultaneously causing duplicates   | 🔴 NOT STARTED |
| GAP-WS-26     | **P1**   | Visible connection status indicator (green/yellow/red badge)                                 | 🔴 NOT STARTED |
| GAP-WS-18     | **P1**   | Topology message can exceed 64 KB silently causing connection teardown                       | 🔴 NOT STARTED |
| GAP-WS-21     | **P1**   | 1 Hz state throttle drops terminal transitions (correctness bug)                             | 🔴 NOT STARTED |
| GAP-WS-28     | **P2**   | Multi-key `update_params` torn-write race                                                    | 🔴 NOT STARTED |
| GAP-WS-31     | **P2**   | Unbounded reconnect cap — stops after 10, dashboards left open permanently stop reconnecting | 🔴 NOT STARTED |
| GAP-WS-32     | **P2**   | Per-command timeouts and orphaned-command resolution                                         | 🔴 NOT STARTED |
| Phase B-pre-b | **P1**   | CSWSH/CSRF on `/ws/control` — NOT STARTED (required before Phase D default-on)               | 🔴 NOT STARTED |

---

## 9. Microservices and Infrastructure

(Sections 9.1, 9.2, 9.3 unchanged from v3 — carried forward.)

### 9.1 Completed Phases

| Phase   | Description                                          | Status      |
|---------|------------------------------------------------------|-------------|
| Phase 1 | Critical startup/shutdown fixes (plant/chop scripts) | ✅ Complete |
| Phase 2 | systemd service units + ctl scripts (all 4 services) | ✅ Complete |
| Phase 3 | Worker Dockerfile, docker-compose, systemd           | ✅ Complete |
| Phase 4 | Kubernetes Helm chart (23 templates)                 | ✅ Complete |

### 9.2 Phase 5: Observability & Hardening — INCOMPLETE

| Step | Task                                             | Status               | Evidence                                                          |
|------|--------------------------------------------------|----------------------|-------------------------------------------------------------------|
| 5.1  | Configure AlertManager receivers (Slack/email)   | 🔴 Placeholders only | `alertmanager.yml` has empty receiver stubs, no real integrations |
| 5.2  | Define alert rules for service availability      | ✅ Complete          | `alert_rules.yml` has 6 rule groups, 12 real alerts               |
| 5.3  | Standardize health endpoints across all services | 🔴 NOT STARTED       | Health endpoint formats differ across services                    |
| 5.4  | Volume backup/restore documentation              | 🔴 NOT STARTED       | No backup docs exist                                              |
| 5.5  | Startup validation test suite                    | 🔴 NOT STARTED       | No startup script tests in juniper-ml                             |

### 9.3 Microservices Architecture Roadmap (Phases 5–9)

| Phase | Description                                           | Status                                               |
|-------|-------------------------------------------------------|------------------------------------------------------|
| 5     | BackendProtocol Interface Refactor                    | ✅ Complete (`protocol.py`)                          |
| 6     | Client Library Fakes                                  | ✅ Complete (FakeCascorClient, FakeDataClient)       |
| 7     | Docker Compose Demo Profile                           | ✅ Complete (demo profile in juniper-deploy)         |
| 8     | Enhanced Health Checks with Dependency Status         | ⚠️ Partial — some services have dependency reporting |
| 9     | Configuration Standardization (Pydantic BaseSettings) | ✅ Complete for cascor and data; canopy migrated     |

---

## 10. CasCor Algorithm and Feature Enhancements

(All items unchanged from v3 — all 🔴 NOT STARTED.)

### Training Control

| ID      | Description                                                | Priority |
|---------|------------------------------------------------------------|----------|
| CAS-002 | Separate epoch limits for full network and candidate nodes | P3       |
| CAS-003 | Max train session iterations meta parameter                | P3       |
| CAS-006 | Auto-snap best network when new best accuracy achieved     | P3       |

### Algorithm Enhancements

| ID      | Description                                           | Priority |
|---------|-------------------------------------------------------|----------|
| ENH-006 | Flexible optimizer system (Adam, SGD, RMSprop, AdamW) | P3       |
| ENH-007 | N-best candidate layer selection                      | P3       |

### Network Architecture

| ID      | Description                                              | Priority |
|---------|----------------------------------------------------------|----------|
| CAS-008 | Network hierarchy management (multi-hierarchical CasCor) | P4       |
| CAS-009 | Network population management (ensemble approaches)      | P4       |

### Serialization & Validation

| ID      | Description                                                              | Priority |
|---------|--------------------------------------------------------------------------|----------|
| ENH-001 | Comprehensive serialization test suite (7 remaining tests)               | P2       |
| ENH-002 | Hidden units checksum validation (SHA256)                                | P2       |
| ENH-003 | Tensor shape validation during load                                      | P2       |
| ENH-004 | Enhanced format validation (`_validate_format()`)                        | P2       |
| ENH-005 | Refactor candidate unit instantiation (factory method)                   | P2       |
| ENH-008 | Worker cleanup improvements (SIGKILL fallback)                           | P2       |

### Storage & Infrastructure

| ID         | Description                                                          | Priority       |
|------------|----------------------------------------------------------------------|----------------|
| CAS-005    | Extract common dependencies to modules (cascor + worker shared code) | P3             |
| CAS-010    | Snapshot vector DB storage (indexed by UUID)                         | P4             |
| —          | Shared memory startup sweep for stale `juniper_train_*` blocks       | P3             |
| —          | `/v1/snapshots/*` API endpoints (4) — deferred, blocks CAN-CRIT-002  | P2             |
| P3-NEW-003 | GPU/CUDA support for training                                        | P4 (XL effort) |
| —          | Large file refactoring (no file > 2000 lines)                        | P3             |
| —          | Auto-generated API docs (MkDocs/Sphinx)                              | P3             |

---

## 11. Cross-Repository Alignment Issues

### 11.1 Original items (v3)

| ID        | Severity     | Repositories           | Description                                                                                                    | Evidence                                                              |
|-----------|--------------|------------------------|----------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| XREPO-01  | **CRITICAL** | data-client ↔ data     | Generator name `"circle"` vs server's `"circles"` — client requests will fail with 400                         | `juniper_data_client/constants.py:90` — `GENERATOR_CIRCLE = "circle"` |
| XREPO-01b | **CRITICAL** | data-client ↔ data     | `GENERATOR_MOON = "moon"` — server has **no moon generator** at all                                            | `juniper_data_client/constants.py:91`                                 |
| XREPO-01c | **MEDIUM**   | data-client ↔ data     | Client missing constants for 5 server generators: `gaussian`, `checkerboard`, `csv_import`, `mnist`, `arc_agi` | Only `spiral`, `xor`, `circle`, `moon` defined                        |
| XREPO-02  | **MEDIUM**   | cascor-client          | 503 not in `RETRYABLE_STATUS_CODES` — transient unavailability not retried                                     | `constants.py:31` — `RETRYABLE_STATUS_CODES = [502, 504]`             |
| XREPO-03  | **MEDIUM**   | cascor-client          | No `FakeCascorControlStream` — testing gap for WS control                                                      | `testing/` has FakeClient and FakeTrainingStream only                 |
| XREPO-04  | **MEDIUM**   | cascor-worker ↔ cascor | Protocol constants alignment is manual — no CI automation for bit-identity verification                        | Wave 5 verified, but cascor change could silently break worker        |
| XREPO-05  | **MEDIUM**   | cascor ↔ canopy        | State name inconsistency — UPPERCASE vs title-case vs FSM constants                                            | Different repos use different casing for same training states         |
| XREPO-06  | **MEDIUM**   | cascor ↔ canopy        | `epochs_max` default discrepancy — cascor 10,000 vs API 200 vs canopy 1,000,000                                | Three different defaults for the same parameter across the stack      |
| XREPO-07  | **MEDIUM**   | cascor-client          | `command()` vs `set_params()` message format inconsistency — `command()` never sends `type` field              | Wire protocol mismatch between the two methods                        |

### 11.2 New cross-repo issues (v4)

| ID       | Severity   | Repositories           | Description                                                                                            | Evidence                                                                                         |
|----------|------------|------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| XREPO-08 | **MEDIUM** | cascor-client          | Three distinct WS message formats: `send_command()`, `command()`, and `set_params()` all differ        | `ws_client.py:99` (no type), `:232` (no type), `:280-285` (has `type: "command"`) — inconsistent |
| XREPO-09 | **MEDIUM** | data-client ↔ data     | Client `create_dataset()` missing `tags` and `ttl_seconds` parameters from server API                  | Server `CreateDatasetRequest` has 8 fields; client only sends 6 — `tags`/`ttl_seconds` dropped   |
| XREPO-10 | **MEDIUM** | data-client            | `FakeDataClient` metadata schema diverges from real server response structure                          | Fake uses `"n_full"` key, flat meta structure; real returns full `DatasetMeta` Pydantic model    |
| XREPO-11 | **MEDIUM** | data-client            | Client retries non-idempotent mutations (POST, DELETE)                                                 | `RETRY_ALLOWED_METHODS = ["HEAD", "GET", "POST", "PATCH", "DELETE"]` — can create duplicates     |
| XREPO-12 | **MEDIUM** | cascor-worker          | `y` tensor received from server but never used in training task                                        | `task_executor.py:35` documents key `y` but L74-75 only use `candidate_input`/`residual_error`   |
| XREPO-13 | **MEDIUM** | cascor ↔ data ↔ canopy | Health endpoint `status` value inconsistency: cascor/data return `"ok"`, canopy returns `"healthy"`    | `cascor/health.py:27`, `canopy/main.py:694-705` (v5 new)                                         |
| XREPO-14 | **MEDIUM** | cascor-client ↔ cascor | FakeClient state consts use different vocab: `"idle"`/`"training"` vs server's `"STOPPED"`/`"STARTED"` | `testing/constants.py:39-43` vs server `state_machine.py:21-29` (v5 new)                         |
| XREPO-15 | **MEDIUM** | all services           | Error response format inconsistent — three different JSON error shapes across services                 | cascor: `{"status":"error","error":{}}` + `{"detail":""}`, data: `{"detail":""}`,                |
|          |            |                        |                                                                                                        | -- canopy: `{"error":"","detail":"","status_code":500}` (v5 new)                                 |
| XREPO-16 | **MEDIUM** | data ↔ data-client     | Client missing methods for 4 server endpoints: filter, stats, cleanup-expired, individual tags         | Server has routes; client has no corresponding methods (v5 new)                                  |
| XREPO-17 | **LOW**    | cascor ↔ cascor-client | `candidate_progress` WS message broadcast by server but not in client constants, no callback           | `messages.py:102-109` — server sends it; client has no handler (v5 new)                          |

---

## 12. Housekeeping and Broken References

### 12.1 Original items (v3)

| ID     | Repository     | Description                                                                         | Priority |
|--------|----------------|-------------------------------------------------------------------------------------|----------|
| HSK-01 | juniper-canopy | 3 broken symlinks in `notes/development/` pointing to deleted juniper-ml files      | P3       |
| HSK-02 | juniper-cascor | `src/remote_client/` directory still exists (3 files) — superseded by cascor-worker | P2       |
| HSK-03 | juniper-cascor | `src/spiral_problem/check.py` — 600-line stale duplicate                            | P2       |
| HSK-04 | juniper-cascor | 32 test files with hardcoded `sys.path.append` to old monorepo paths                | P2       |
| HSK-05 | cascor-client  | AGENTS.md header version 0.3.0, package is 0.4.0                                    | P3       |
| HSK-06 | juniper-data   | AGENTS.md header version 0.5.0, package is 0.6.0                                    | P3       |
| HSK-07 | cascor-client  | File headers (constants.py, testing/*) show versions 0.1.0–0.3.0 (should be 0.4.0)  | P3       |
| HSK-08 | data-client    | `tests/conftest.py` version header says 0.3.1, project is 0.4.0                     | P3       |
| HSK-09 | cascor-client  | Dead code: `_STATE_TO_FSM` and `_STATE_TO_PHASE` class attributes never referenced  | P3       |
| HSK-10 | juniper-ml     | `scripts/test.bash` outdated/non-functional — references removed `nohup.out`        | P3       |
| HSK-11 | juniper-ml     | `wake_the_claude.bash` `DEBUG="${TRUE}"` hardcoded ON — noisy output                | P2       |
| HSK-12 | juniper-ml     | `NOHUP_STATUS=$?` captures fork status (always 0) — dead error check                | P3       |
| HSK-13 | juniper-canopy | 169 hardcoded ThemeColors remain — MED-026 rollout deferred                         | P3       |

### 12.2 New housekeeping items (v4)

| ID     | Repository    | Description                                                                                                              | Priority |
|--------|---------------|--------------------------------------------------------------------------------------------------------------------------|----------|
| HSK-14 | juniper-ml    | `resume_session.bash` contains hardcoded session UUID — one-time-use script committed as permanent                       | P3       |
| HSK-15 | juniper-ml    | `util/global_text_replace.bash` is a no-op — search==replace identical strings; misspelled `KIBAB`                       | P3       |
| HSK-16 | juniper-ml    | `util/kill_all_pythons.bash` uses `sudo kill -9` on ALL Python processes indiscriminately                                | P2       |
| HSK-17 | juniper-ml    | `util/worktree_new.bash` hardcodes branch/repo names and conda env; has stray `}` in error msg                           | P3       |
| HSK-18 | juniper-ml    | `util/worktree_close.bash` hardcodes default identifier — not reusable without args                                      | P3       |
| HSK-19 | juniper-ml    | Stale files in repo root: `bla`, `juniper_cascor.log`, `juniper-project-pids.txt`, `JuniperProject.pid`, `.mcp.json.swp` | P3       |
| HSK-20 | juniper-ml    | `claude_interactive.bash:17` `DEBUG="${TRUE}"` hardcoded — forces `--dangerously-skip-permissions`                       | P2       |
| HSK-21 | juniper-ml    | `wake_the_claude.bash:53` stale TODO comment — `debug_log` already writes to stderr                                      | P3       |
| HSK-22 | juniper-ml    | `wake_the_claude.bash:547` TODO — model parameter accepted but never validated                                           | P3       |
| HSK-23 | juniper-ml    | `scripts/juniper-all-ctl:38` cascor port defaults to 8200 (container port) vs host port 8201                             | P3       |
| HSK-24 | cascor-client | Dead constants: `ERROR_PRONE_INITIAL_HIDDEN_UNITS` / `ERROR_PRONE_INITIAL_EPOCH` never used                              | P3       |

---

## 13. juniper-deploy Outstanding Items

### 13.1 Infrastructure Bugs (Confirmed Still Present)

| ID        | Severity   | Description                                                                                                                      | Evidence                                                    |
|-----------|------------|----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| DEPLOY-01 | **HIGH**   | Docker secret name/path mismatch: `juniper_data_api_key` (singular) vs app expects `juniper_data_api_keys` (plural)              | `docker-compose.yml:110` vs `:99`                           |
| DEPLOY-02 | **HIGH**   | AlertManager service missing from docker-compose.yml — `prometheus.yml:34` references `alertmanager:9093` but no service defined | `alertmanager/alertmanager.yml` exists but never used       |
| DEPLOY-03 | **HIGH**   | Prometheus alert/recording rules not mounted — only `prometheus.yml` is volume-mapped, rules files unreachable inside container  | `docker-compose.yml:422` — single file mount, not directory |
| DEPLOY-04 | **MEDIUM** | K8s canopy deployment missing `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` env vars                 | Helm templates                                              |
| DEPLOY-05 | **MEDIUM** | K8s Redis `auth.enabled: false` — no authentication                                                                              | `values.yaml:306`                                           |
| DEPLOY-06 | **MEDIUM** | K8s Grafana admin password is empty string default                                                                               | `values.yaml:334`                                           |
| DEPLOY-07 | **MEDIUM** | No resource limits on any Docker Compose service                                                                                 | Planned for v0.3.0, not implemented                         |
| DEPLOY-08 | **MEDIUM** | Cascor and canopy ports bound to `0.0.0.0` (externally accessible)                                                               | `docker-compose.yml:128-129,297-298`                        |
| DEPLOY-09 | **MEDIUM** | Worker auth token not via Docker secrets                                                                                         | Worker authentication token passed as plain env var         |
| DEPLOY-10 | **MEDIUM** | Demo variants lack security hardening                                                                                            | Demo compose profiles use relaxed security settings         |
| DEPLOY-11 | **LOW**    | `JUNIPER_DATA_API_KEYS` defaults to empty — auth disabled by default                                                             | Empty default means API key auth is effectively off         |
| DEPLOY-12 | **LOW**    | `wait_for_services.sh` uses hardcoded ports instead of env vars                                                                  | Port numbers hardcoded in health check script               |

### 13.2 New infrastructure issues (v4)

| ID        | Severity   | Description                                                                                                       | Evidence                                                                                      |
|-----------|------------|-------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| DEPLOY-13 | **HIGH**   | `canopy-dev` network isolation prevents data access — on `frontend` only, but juniper-data on `backend`+`data`    | `docker-compose.yml:391-392` — dev profile is broken, canopy-dev cannot reach juniper-data    |
| DEPLOY-14 | **MEDIUM** | Prometheus rule files not mounted into container (extends DEPLOY-03 with specific fix)                            | Only `prometheus.yml` file is volume-mounted; needs `./prometheus:/etc/prometheus:ro`         |
| DEPLOY-15 | **MEDIUM** | Helm chart default values use `latest` image tags for all 4 services                                              | `values.yaml:27,86,163,227` — non-reproducible deployments                                    |
| DEPLOY-16 | **MEDIUM** | `kube-prometheus-stack.grafana.adminPassword` empty in values.yaml                                                | `values.yaml:334` — if kube-prometheus-stack enabled, Grafana installs with empty password    |
| DEPLOY-17 | **LOW**    | CI compose validation missing worker build context stubs                                                          | `.github/workflows/ci.yml:163-170` — only 3 of 4 Dockerfiles stubbed, 3 of 7 secrets          |
| DEPLOY-18 | **LOW**    | Prometheus container has no healthcheck                                                                           | `docker-compose.yml:410-428` — Grafana may start before Prometheus is ready                   |
| DEPLOY-19 | **LOW**    | Grafana container has no healthcheck                                                                              | `docker-compose.yml:433-453`                                                                  |
| DEPLOY-20 | **LOW**    | Redis has no persistence volume — data lost on restart                                                            | `docker-compose.yml:458-467` — acceptable for cache, should be documented                     |
| DEPLOY-21 | **LOW**    | `canopy-demo` and `canopy-dev` missing Redis dependency                                                           | Full canopy depends on Redis; demo/dev profiles don't include it                              |
| DEPLOY-22 | **LOW**    | `Dockerfile.test` uses unpinned `python:3.12-slim`                                                                | No digest or patch version pin — non-reproducible test builds                                 |
| DEPLOY-23 | **LOW**    | No Helm chart linting in CI                                                                                       | CI validates Docker Compose but doesn't run `helm lint` or `helm template`                    |
| DEPLOY-24 | **HIGH**   | Helm values.yaml missing `JUNIPER_DATA_URL` and `CASCOR_SERVICE_URL` for canopy — K8s canopy can't reach services | `values.yaml` canopy env section — only SERVER, RATE_LIMIT, LOG, SENTRY, METRICS set (v5 new) |
| DEPLOY-25 | **HIGH**   | Helm values.yaml missing `CASCOR_SERVER_URL` for worker — worker fails to start in K8s                            | `values.yaml` worker env — only `CASCOR_HEARTBEAT_INTERVAL` set (v5 new)                      |
| DEPLOY-26 | **MEDIUM** | Helm values.yaml missing `JUNIPER_DATA_URL` for cascor — cascor can't locate data service in K8s                  | `values.yaml` cascor env — `main.py` treats missing `JUNIPER_DATA_URL` as fatal (v5 new)      |

### 13.3 Unimplemented Roadmap Items (carried from v3)

| ID           | Planned Version | Description                                              | Status                                                             |
|--------------|-----------------|----------------------------------------------------------|--------------------------------------------------------------------|
| DEPLOY-RD-01 | 0.3.0           | Production compose profile with resource limits          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-02 | 0.3.0           | TLS termination via reverse proxy                        | 🔴 NOT DONE                                                        |
| DEPLOY-RD-03 | 0.5.0           | Scheduled weekly integration tests                       | 🔴 NOT DONE                                                        |
| DEPLOY-RD-04 | 0.5.0           | Container image security scanning (Trivy/Grype)          | 🔴 NOT DONE                                                        |
| DEPLOY-RD-05 | —               | Phase 2 systemd service units                            | 🔴 ENTIRELY UNSTARTED — no `systemd/` directory                    |
| DEPLOY-RD-06 | —               | Docker integration CI job (build + start + health check) | 🔴 Planned in `CONTAINER_VALIDATION_CI_PLAN.md` but absent from CI |
| DEPLOY-RD-07 | —               | SOPS multi-key per environment (SOPS-002)                | 🔴 Deferred to Phase 5                                             |
| DEPLOY-RD-08 | —               | Docker secrets + SOPS integration (SOPS-014)             | 🔴 Deferred to Phase 5                                             |

---

## 14. juniper-data Outstanding Items

### 14.1 Security Issues (Confirmed Still Present)

| ID        | Severity   | File                        | Description                                                                                                                                                         |
|-----------|------------|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| JD-SEC-01 | **HIGH**   | `storage/local_fs.py:52-58` | Path traversal: `dataset_id` concatenated into filesystem paths without `../` sanitization. User-supplied IDs in delete/get endpoints can escape storage directory. |
| JD-SEC-02 | **MEDIUM** | `api/security.py:59`        | API key comparison not constant-time — timing side-channel (SEC-01 from prior audit, still present)                                                                 |
| JD-SEC-03 | **MEDIUM** | `api/security.py:116`       | Rate limiter memory unbounded — no eviction/TTL (SEC-02 from prior audit, still present)                                                                            |

### 14.2 Performance Issues

| ID         | Severity   | File                                | Description                                                                                                                              |
|------------|------------|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| JD-PERF-01 | **HIGH**   | `api/routes/datasets.py:107`        | Sync `generator.generate()` blocks async event loop. Needs `asyncio.to_thread()`.                                                        |
| JD-PERF-02 | **MEDIUM** | `storage/base.py:261,317`           | `filter_datasets`/`get_stats` load ALL metadata on every call — O(n) disk reads.                                                         |
| JD-PERF-03 | **MEDIUM** | `storage/base.py:169`               | `list_versions` loads all metadata then filters in Python. No DB-level filtering for Postgres.                                           |
| JD-PERF-04 | **MEDIUM** | `storage/postgres_store.py:125-127` | No connection pooling — `psycopg2.connect()` called per operation. Confirmed: `close()` is a no-op for "connection-per-request pattern". |
| JD-PERF-05 | **MEDIUM** | `api/routes/health.py:57`           | Readiness probe does filesystem glob on every call — `len(list(storage_path.glob("*.npz")))` is O(n) per probe (v4 new)                  |

### 14.3 Deferred Roadmap Items

| ID     | Description                             | Status      |
|--------|-----------------------------------------|-------------|
| RD-008 | Fix SIM117 test code violations         | 🔵 DEFERRED |
| RD-015 | IPC Architecture (ZeroMQ/shared-memory) | 🔵 DEFERRED |
| RD-016 | GPU Acceleration for large datasets     | 🔵 DEFERRED |
| RD-017 | Continuous Profiling infrastructure     | 🔵 DEFERRED |

---

## 15. Client Library Outstanding Items

### 15.1 juniper-cascor-client

| ID    | Severity   | Description                                                                                                 | Status             |
|-------|------------|-------------------------------------------------------------------------------------------------------------|--------------------|
| CC-01 | **MEDIUM** | `_recv_loop` catches bare `Exception` — swallows programming errors, pending futures time out               | 🔴 Open            |
| CC-02 | **MEDIUM** | 503 not in `RETRYABLE_STATUS_CODES`                                                                         | 🔴 Open (XREPO-02) |
| CC-03 | **MEDIUM** | No `FakeCascorControlStream`                                                                                | 🔴 Open (XREPO-03) |
| CC-04 | **LOW**    | `set_params()` method not documented in AGENTS.md Architecture                                              | 🔴 Open            |
| CC-05 | **LOW**    | CI doesn't test Python 3.14 (classified in pyproject.toml)                                                  | 🔴 Open            |
| CC-06 | **MEDIUM** | `command()` never sends `type` field — wire protocol inconsistency with `set_params()`                      | 🔴 Open (XREPO-07) |
| CC-07 | **MEDIUM** | NpzFile resource leak in data-client — `np.load(BytesIO())` never closed                                    | 🔴 Open            |
| CC-08 | **LOW**    | WebSocket auto-reconnection not implemented — long training runs silently lose WS                           | 🔴 Open            |
| CC-09 | **MEDIUM** | `CascorTrainingStream.stream()` no `json.JSONDecodeError` handling — malformed JSON crashes stream          | 🔴 Open (v4 new)   |
| CC-10 | **MEDIUM** | `CascorControlStream.connect()` no `json.JSONDecodeError` handling — leaks untyped error                    | 🔴 Open (v4 new)   |
| CC-11 | **MEDIUM** | `CascorControlStream.command()` direct path — no `json.JSONDecodeError` handling                            | 🔴 Open (v4 new)   |
| CC-12 | **MEDIUM** | `CascorControlStream._recv_loop()` no `json.JSONDecodeError` — single bad message fails ALL pending futures | 🔴 Open (v4 new)   |
| CC-13 | **LOW**    | `_recv_loop` silently drops non-correlated server messages (state changes, errors, heartbeats)              | 🔴 Open (v4 new)   |
| CC-14 | **LOW**    | `_handle_response()` calls `response.json()` unconditionally — fails on non-JSON 2xx bodies                 | 🔴 Open (v4 new)   |
| CC-15 | **MEDIUM** | No TLS/SSL configuration support on WS streams (unlike worker which has full mTLS support)                  | 🔴 Open (v4 new)   |
| CC-16 | **LOW**    | `FakeCascorClient.wait_for_ready()` returns `True` immediately — no timeout testing possible                | 🔴 Open (v4 new)   |
| CC-17 | **LOW**    | `FakeCascorClient.wait_for_ready()` missing `self._lock` — thread safety gap                                | 🔴 Open (v4 new)   |

### 15.2 juniper-data-client

| ID    | Severity     | Description                                                                                    | Status              |
|-------|--------------|------------------------------------------------------------------------------------------------|---------------------|
| DC-01 | **CRITICAL** | `GENERATOR_CIRCLE = "circle"` — server has `"circles"` (plural)                                | 🔴 Open (XREPO-01)  |
| DC-02 | **CRITICAL** | `GENERATOR_MOON = "moon"` — server has no moon generator                                       | 🔴 Open (XREPO-01b) |
| DC-03 | **MEDIUM**   | Missing constants for 5 server generators                                                      | 🔴 Open (XREPO-01c) |
| DC-04 | **MEDIUM**   | `FakeDataClient` masks generator name bugs — accepts invalid names                             | 🔴 Open             |
| DC-05 | **MEDIUM**   | `FakeDataClient` missing lifecycle methods (`filter_datasets`, `get_stats`, `cleanup_expired`) | 🔴 Open (v4 new)    |

### 15.3 juniper-cascor-worker

| ID    | Severity   | Description                                                                                          | Status                                                |
|-------|------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| CW-01 | **MEDIUM** | `receive_json()` doesn't catch `json.JSONDecodeError` — malformed server message crashes worker      | ⚠️ Partially fixed — `_parse_json()` catches but      |
|       |            |                                                                                                      | -- `receive_json()` at `ws_connection.py:184` doesn't |
| CW-02 | **MEDIUM** | `requirements.lock` includes CUDA packages (~2-4GB image bloat)                                      | 🔴 Open                                               |
| CW-03 | **LOW**    | No integration tests (marker defined, zero tests use it)                                             | 🔴 Open                                               |
| CW-04 | **MEDIUM** | Timeout error sends `candidate_uuid: ""` instead of actual UUID                                      | 🔴 Open                                               |
| CW-05 | **MEDIUM** | Dynamic import `from candidate_unit.candidate_unit import CandidateUnit` — fragile, no version check | 🔴 Open                                               |
| CW-06 | **MEDIUM** | `receive_json()` in `ws_connection.py:184` — no `json.JSONDecodeError` catch (registration crash)    | 🔴 Open (v4 new)                                      |
| CW-07 | **MEDIUM** | No validation of `tensor_manifest` keys against received binary frames — deadlock risk               | 🔴 Open (v4 new)                                      |
| CW-08 | **MEDIUM** | `task_executor.py:12` top-level `import torch` — first-task latency from deferred torch import       | 🔴 Open (v4 new)                                      |

---

## 16. Performance Issues (v4 new section)

Issues identified through deep code analysis that impact runtime performance.

### 16.1 juniper-canopy

| ID         | Severity   | Description                                                        | File(s)                                                              | Evidence                                                                  |
|------------|------------|--------------------------------------------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------------|
| PERF-CN-01 | **MEDIUM** | 33 of 50 Dash callbacks missing `prevent_initial_call=True`        | `metrics_panel.py` (14), `candidate_metrics_panel.py` (7), 12 others | 33 unnecessary callback executions on every dashboard load                |
| PERF-CN-02 | **LOW**    | f-string logging in hot paths (71 occurrences in demo_mode + main) | `src/demo_mode.py` (20), `src/main.py` (51)                          | String interpolation evaluated even when log level suppresses the message |

### 16.2 juniper-cascor

| ID         | Severity   | Description                                                             | File(s)                                | Evidence                                                                                                  |
|------------|------------|-------------------------------------------------------------------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------|
| PERF-CC-01 | **MEDIUM** | Blocking `torch.save`/`torch.load` in async-adjacent code paths         | `src/api/lifecycle/manager.py:870,894` | Synchronous HDF5 I/O called from async REST handlers — blocks all concurrent requests during snapshot ops |
| PERF-CC-02 | **LOW**    | `replay_since` scans entire replay buffer O(n) on every resume request  | `src/api/websocket/manager.py:248`     | Linear scan of 1024-entry deque; binary search would be O(log n)                                          |
| PERF-CC-03 | **LOW**    | `_broadcast_training_state` uses `hasattr` check instead of proper init | `src/api/lifecycle/manager.py:153`     | `hasattr(self, "_last_state_broadcast_time")` on every call                                               |

### 16.3 juniper-data

| ID         | Severity   | Description                                                  | File(s)                   | Evidence                                                               |
|------------|------------|--------------------------------------------------------------|---------------------------|------------------------------------------------------------------------|
| PERF-JD-01 | **MEDIUM** | Readiness probe does filesystem glob on every call           | `api/routes/health.py:57` | `len(list(storage_path.glob("*.npz")))` is O(n) per probe              |
| PERF-JD-02 | **MEDIUM** | High-cardinality Prometheus labels from parameterized routes | `api/observability.py:98` | `endpoint = request.url.path` with dataset IDs — unbounded cardinality |

---

## 17. Source Document Lineage

This document was produced by cross-referencing:

### v1.0.0–v3.0.0 Sources (34 documents)

(Full table unchanged from v3 — see v3 Section 16 for the complete list of 34 cross-referenced source documents.)

### v4.0.0 Sources

| Source                               | Method                                    | Scope                                              |
|--------------------------------------|-------------------------------------------|----------------------------------------------------|
| Live codebase: juniper-cascor        | File reads, grep, structural analysis     | All `src/` files, `pyproject.toml`, tests          |
| Live codebase: juniper-canopy        | File reads, grep, structural analysis     | All `src/` files, `pyproject.toml`, tests          |
| Live codebase: juniper-data          | File reads, grep, structural analysis     | All `juniper_data/` files, `pyproject.toml`, tests |
| Live codebase: juniper-data-client   | File reads, grep, structural analysis     | All `juniper_data_client/` files, tests            |
| Live codebase: juniper-cascor-client | File reads, grep, structural analysis     | All `juniper_cascor_client/` files, tests          |
| Live codebase: juniper-cascor-worker | File reads, grep, structural analysis     | All `juniper_cascor_worker/` files, tests          |
| Live codebase: juniper-deploy        | File reads, compose analysis, Helm review | All compose files, Dockerfiles, Helm chart, CI     |
| Live codebase: juniper-ml            | File reads, shellcheck, CI analysis       | All scripts, utilities, workflows, tests           |

---

## 18. Concurrency and Thread Safety Issues (v5 new)

Issues identified through cross-cutting concurrency analysis across all repositories.

| ID      | Severity   | Repository     | Description                                                                           | File(s)                                | Evidence                                                           |
|---------|------------|----------------|---------------------------------------------------------------------------------------|----------------------------------------|--------------------------------------------------------------------|
| CONC-01 | **HIGH**   | juniper-canopy | `_per_ip_counts` check-then-act race in WebSocketManager — no lock on check+decrement | `websocket_manager.py:278-282,289-292` | Concurrent connect/disconnect can corrupt per-IP tracking          |
| CONC-02 | **MEDIUM** | juniper-cascor | `_last_state_broadcast_time` unprotected cross-thread R/W                             | `manager.py:151-155`                   | Two callers can both pass throttle check simultaneously            |
| CONC-03 | **MEDIUM** | juniper-cascor | `_extract_and_record_metrics` split-lock — duplicate emissions                        | `manager.py:453-495`                   | Lock released between read and write of high-water-mark            |
| CONC-04 | **HIGH**   | juniper-data   | ALL storage operations block async event loop (extends JD-PERF-01)                    | `datasets.py:98-154,259,277,377-424`   | get_meta, save, batch ops are synchronous in async handlers        |
| CONC-07 | **MEDIUM** | juniper-canopy | `regenerate_dataset` mutates state without lock                                       | `demo_mode.py:1660-1676`               | Training thread sees partially updated dataset                     |
| CONC-08 | **LOW**    | juniper-canopy | `is_running` reads/writes inconsistently locked                                       | `demo_mode.py:1151,1293,1398,1478`     | Boolean check-then-act not atomic                                  |
| CONC-09 | **MEDIUM** | juniper-cascor | Fire-and-forget `asyncio.create_task` without stored reference                        | `app.py:137,142`                       | Startup tasks silently swallowed on exception; GC'd references     |
| CONC-10 | **LOW**    | juniper-cascor | Health monitor deregister/assign race window                                          | `coordinator.py:379-408`               | Task assigned to worker about to be deregistered — 120s delay risk |
| CONC-12 | **LOW**    | juniper-data   | `record_access` TOCTOU on access_count increment                                      | `base.py:125-135`                      | Concurrent access increments can lose counts                       |

---

## 19. Error Handling and Robustness (v5 new)

Issues identified through cross-cutting error handling analysis across all repositories.

| ID        | Severity   | Repository            | Description                                                                                        | File(s)                                                 |
|-----------|------------|-----------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| ERR-01    | **MEDIUM** | juniper-data-client   | `response.json()` unguarded against JSONDecodeError on all 13 public methods                       | `client.py:215-531`                                     |
| ERR-02    | **MEDIUM** | juniper-cascor-client | `response.json()` unguarded in `_request()` — ValueError escapes                                   | `client.py:366`                                         |
| ERR-06    | **LOW**    | juniper-cascor        | `raise HTTPException` without `from e` — loses exception context (6 locations)                     | `routes/network.py:31,52`, `training.py:89,109,121,170` |
| ERR-07    | **LOW**    | juniper-data          | `raise HTTPException` without `from e` — broad except masks programming errors as 400              | `datasets.py:90`                                        |
| ERR-08    | **LOW**    | juniper-data          | `str(e)` in batch create error response — information disclosure                                   | `datasets.py:342-348`                                   |
| ERR-09    | **MEDIUM** | juniper-cascor        | `remote_client_0.process_tasks()` catches all exceptions, only prints — silent failure             | `remote_client_0.py:73-74`                              |
| ERR-12    | **LOW**    | juniper-canopy        | `config_manager._load_config()` silently returns {} on any exception                               | `config_manager.py:147-149`                             |
| ERR-13    | **LOW**    | juniper-data          | `arc_agi` generator silently falls back on any exception — masks auth/network errors               | `generator.py:95-98`                                    |
| ERR-14    | **MEDIUM** | juniper-cascor-client | `CascorMetricsStream.stream()` swallows ConnectionClosed — caller can't detect disconnect          | `ws_client.py:79-80`                                    |
| ROBUST-01 | **HIGH**   | juniper-cascor        | Dummy candidate results on double training failure — zero-correlation candidate installed silently | `cascade_correlation.py:1930-1962`                      |

---

## 20. Testing and CI/CD Gaps (v5 new)

Issues identified through cross-cutting test coverage and CI analysis across all repositories.

| ID        | Severity   | Category     | Repository     | Description                                                                         |
|-----------|------------|--------------|----------------|-------------------------------------------------------------------------------------|
| CI-01     | **HIGH**   | CI/CD        | cascor-client  | CI doesn't test Python 3.14 — consumers (cascor, canopy) run on 3.14                |
| CI-02     | **HIGH**   | CI/CD        | cascor-worker  | CI doesn't test Python 3.14 — cascor (consumer) runs on 3.14                        |
| CI-03     | **HIGH**   | CI/CD        | juniper-deploy | 1,177 lines of tests exist but CI runs ZERO of them                                 |
| CI-04     | **MEDIUM** | CI/CD        | cascor-client  | Missing dedicated weekly security-scan.yml — vulnerability detection gap            |
| CI-05     | **MEDIUM** | CI/CD        | cascor-client  | Missing lockfile-update.yml workflow — stale dependencies accumulate                |
| CI-06     | **MEDIUM** | CI/CD        | juniper-deploy | No coverage configuration at all — tests exist but coverage never measured          |
| CI-07     | **LOW**    | CI/CD        | cascor, worker | Inconsistent GitHub Actions artifact upload/cache versions across repos             |
| COV-01    | **MEDIUM** | Coverage     | juniper-deploy | Tests exist but zero coverage infrastructure (no `[tool.coverage]`, no `--cov`)     |
| COV-02    | **MEDIUM** | Coverage     | juniper-canopy | No per-module coverage gate (juniper-data enforces 85% per-module)                  |
| COV-04    | **LOW**    | Coverage     | juniper-data   | Coverage gate mismatch — CI comment says 95%, actual `COVERAGE_FAIL_UNDER` is 80%   |
| TQ-01     | **MEDIUM** | Test Quality | juniper-cascor | 10+ tests with no assertions — fire-and-forget test methods inflate counts          |
| TQ-02     | **MEDIUM** | Test Quality | juniper-canopy | 149 `time.sleep` calls in tests — excessive hard-coded waits, flakiness risk        |
| TQ-03     | **MEDIUM** | Test Quality | cascor-worker  | Config validation tests have no assertions — pass as long as no exception           |
| TQ-04     | **LOW**    | Test Quality | juniper-cascor | 139 `hasattr` guards in tests (similar to canopy's 226 tracked in BUG-CN-03)        |
| TQ-05     | **LOW**    | Test Quality | juniper-canopy | 10 unit tests import httpx — actually integration-level tests                       |
| CI-SEC-01 | **HIGH**   | Security CI  | cascor-client  | No weekly security scan — supply chain vulnerability window for widely-consumed lib |
| CI-SEC-02 | **LOW**    | Security CI  | juniper-deploy | No security scanning at all (shell scripts, Python helpers unaudited)               |

### Cross-Repo CI Feature Matrix

| Feature              | cascor | canopy | data | data-client | cascor-client | cascor-worker | deploy | juniper-ml |
|----------------------|--------|--------|------|-------------|---------------|---------------|--------|------------|
| Pre-commit           | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | ✅     | ✅         |
| Unit Tests in CI     | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | ❌     | ✅         |
| Coverage Gate        | 80%    | 80%    | 80%+ | 80%         | 80%           | 80%           | ❌     | —          |
| Per-Module Coverage  | —      | ❌     | ✅   | —           | —             | —             | —      | —          |
| Python 3.14 CI       | ✅     | ✅     | ✅   | ✅          | ❌            | ❌            | —      | —          |
| Gitleaks             | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| Bandit SAST          | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| pip-audit            | ✅     | ✅     | ✅   | ✅          | ✅            | ✅            | —      | —          |
| Weekly security-scan | ✅     | ✅     | ✅   | ✅          | ❌            | ✅            | —      | ✅         |
| Docker smoke test    | ✅     | ✅     | ✅   | —           | —             | —             | —      | —          |

---

## 21. Configuration and Dependency Issues (v5 new)

Issues identified through cross-cutting configuration and dependency analysis across all repositories.

| ID     | Severity   | Category              | Repository     | Description                                                                                         | Evidence                                                        |
|--------|------------|-----------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| CFG-01 | **HIGH**   | Missing Dependency    | juniper-canopy | `torch` imported unconditionally but missing from dependencies — demo mode crashes on install       | `demo_backend.py:45` imports torch; not in pyproject.toml       |
| CFG-02 | **MEDIUM** | Unnecessary Dep       | juniper-cascor | `sentry-sdk` in core deps but only used when `SENTRY_SDK_DSN` is set                                | Should be in optional `observability` extra                     |
| CFG-03 | **MEDIUM** | Env Var Inconsistency | juniper-cascor | `SENTRY_SDK_DSN` (main.py) vs `JUNIPER_CASCOR_SENTRY_DSN` (Settings) — two env vars for one feature | `main.py:58` vs `settings.py:189`                               |
| CFG-04 | **MEDIUM** | Config Bypass         | juniper-cascor | `JUNIPER_DATA_URL` read via raw `os.getenv`, bypasses Settings class — no validation                | `app.py:121,185,253`, `health.py:56`                            |
| CFG-05 | **MEDIUM** | Env Var Conflict      | juniper-cascor | `CASCOR_LOG_LEVEL` vs `JUNIPER_CASCOR_LOG_LEVEL` — both needed for full log level control           | `constants.py:580` vs `settings.py:116`                         |
| CFG-06 | **LOW**    | Naming                | cascor-worker  | `CASCOR_*` env prefix inconsistent with ecosystem `JUNIPER_*` convention                            | `constants.py:126-138` — 13 env vars use bare `CASCOR_*`        |
| CFG-07 | **MEDIUM** | Port Inconsistency    | Cross-repo     | Port 8200 vs 8201 confusion — cascor binds 8200, Docker maps to 8201, clients default to 8200       | cascor-client, canopy default to 8200; Docker host port is 8201 |
| CFG-08 | **LOW**    | Config Inconsistency  | Cross-repo     | Rate limiting defaults differ — data enabled, cascor/canopy disabled by default                     | Local dev has no rate limits; production does — behavioral gap  |
| CFG-09 | **MEDIUM** | Unsafe Default        | juniper-canopy | `audit_log_path` defaults to `/var/log/canopy/audit.log` — requires root, crashes non-root deploys  | `settings.py:172` — `audit_log_enabled: True` default           |
| CFG-12 | **LOW**    | Build Config          | cascor-worker  | `setuptools>=82.0` vs `>=61.0` everywhere else — unnecessary constraint                             | `pyproject.toml:2`                                              |
| CFG-13 | **LOW**    | Unnecessary Dep       | juniper-canopy | `python-dotenv` in core deps but never imported — pydantic-settings handles `.env`                  | No `import dotenv` in canopy `src/`                             |
| CFG-14 | **LOW**    | Stale Constraint      | juniper-canopy | `juniper-cascor-client>=0.1.0` allows outdated incompatible versions (current is 0.4.0)             | juniper-ml requires `>=0.3.0`                                   |
| CFG-16 | **LOW**    | Config Bypass         | juniper-canopy | `CASCOR_DEMO_MODE` read directly, bypasses Settings deprecation validator                           | `backend/__init__.py:66`                                        |

---

## 22. API Contract and Protocol Issues (v5 new)

Issues identified through cross-cutting API contract and protocol correctness analysis.

| ID       | Severity   | Category        | Repositories          | Description                                                                                                             |
|----------|------------|-----------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------|
| API-01   | **MEDIUM** | Health Endpoint | cascor, data, canopy  | Health `status` value inconsistent: cascor/data return `"ok"`, canopy returns `"healthy"`                               |
| API-02   | **LOW**    | Health Endpoint | cascor, data, canopy  | Health response schema diverges — canopy returns 7 fields, cascor/data return 2                                         |
| API-03   | **HIGH**   | State Machine   | cascor, canopy        | Canopy FSM lacks auto-reset from FAILED/COMPLETED on START — training unrestartable in demo mode without explicit RESET |
| API-04   | **MEDIUM** | Testing         | cascor-client, cascor | FakeClient state constants use different vocabulary: `"idle"` vs `"STOPPED"`, `"training"` vs `"STARTED"`               |
| API-05   | **MEDIUM** | Error Handling  | all services          | Error response format inconsistent — three different JSON error shapes across services                                  |
| API-06   | **LOW**    | Protocol        | cascor, cascor-client | `candidate_progress` WS message broadcast by server, not in client constants, no callback handler                       |
| API-07   | **MEDIUM** | API Coverage    | data, data-client     | Client missing methods for 4 server endpoints: filter, stats, cleanup-expired, individual tags                          |
| API-08   | **LOW**    | Protocol        | cascor-client, cascor | `set_params` includes extraneous `type:command` field; `command()` does not — asymmetric envelopes                      |
| API-09   | **MEDIUM** | API Contract    | juniper-cascor        | HTTPException errors bypass ResponseEnvelope — dual error format in same API                                            |
| PROTO-01 | **LOW**    | Protocol        | canopy, cascor        | Canopy `/ws/control` accepts `reset` parameter not in cascor's control protocol                                         |

---

## 23. Validation Methodology (v5.0.0)

### Process

Version 5.0.0 extends the v4.0.0 per-repository audit with a second wave of **cross-cutting concern agents** — 5 agents that each audited ALL 8 repositories through a specific analytical lens. This complementary approach catches issues that span repository boundaries and require understanding of system-wide patterns.

### v4.0.0 Agents (per-repository focus)

| Agent   | Focus Area                          | Repositories                                 | Findings |
|---------|-------------------------------------|----------------------------------------------|----------|
| Agent 1 | Backend server security & bugs      | juniper-cascor                               | 18       |
| Agent 2 | Dashboard UI, performance, security | juniper-canopy                               | 15       |
| Agent 3 | Data service & client library       | juniper-data, juniper-data-client            | 19       |
| Agent 4 | Client SDK & distributed worker     | juniper-cascor-client, juniper-cascor-worker | 17       |
| Agent 5 | Infrastructure, scripts, CI/CD      | juniper-deploy, juniper-ml                   | 25       |

### v5.0.0 Agents (cross-cutting concerns)

| Agent    | Focus Area                                         | Repositories | New Findings |
|----------|----------------------------------------------------|--------------|--------------|
| Agent 6  | Concurrency, threading, async correctness          | All 8        | 9            |
| Agent 7  | Error handling, exception safety, robustness       | All 8        | 10           |
| Agent 8  | Test coverage, test quality, CI/CD completeness    | All 8        | 17           |
| Agent 9  | Configuration, dependencies, environment variables | All 8        | 13           |
| Agent 10 | API contracts, protocol correctness, integration   | All 8        | 10           |

### Key Changes from v4.0.0

| Change Type              | Count   | Details                                                                                                    |
|--------------------------|---------|------------------------------------------------------------------------------------------------------------|
| Items confirmed FIXED    | 0       | No additional items resolved between v4 and v5                                                             |
| New bugs                 | 8       | BUG-CC-16–18, BUG-CN-11–12, BUG-JD-10–11                                                                   |
| New deploy issues        | 3       | DEPLOY-24–26 (Helm missing critical env vars for K8s)                                                      |
| New cross-repo issues    | 5       | XREPO-13–17 (health status, FakeClient vocabulary, error shapes, missing methods, candidate_progress)      |
| New concurrency issues   | 9       | CONC-01–12 (per-IP race, throttle race, split-lock, async blocking, state mutation, fire-and-forget tasks) |
| New error handling       | 10      | ERR-01–14, ROBUST-01 (JSONDecodeError gaps, silent failures, dummy training results)                       |
| New testing/CI gaps      | 17      | CI-01–07, COV-01–04, TQ-01–05, CI-SEC-01–02                                                                |
| New configuration issues | 13      | CFG-01–16 (torch missing dep, Sentry dual env, port confusion, audit log root crash)                       |
| New API/protocol issues  | 10      | API-01–09, PROTO-01 (FSM auto-reset, health inconsistency, error format, missing client methods)           |
| **Total new items (v5)** | **~70** | Deduplicated across 5 cross-cutting agents                                                                 |

### Cumulative Audit Statistics

| Version | Method                      | Agents | New Items Found | Cumulative Total |
|---------|-----------------------------|--------|-----------------|------------------|
| v1–v2   | Document cross-reference    | 3      | 69              | 69               |
| v3      | 34-document cross-reference | 5      | ~85             | ~145             |
| v4      | Per-repo codebase audit     | 5      | ~83             | ~230             |
| v5      | Cross-cutting concern audit | 5      | ~70             | **~300**         |

### Severity Distribution (v5 new items only)

| Severity | Count | Highlights                                                                                                                            |
|----------|-------|---------------------------------------------------------------------------------------------------------------------------------------|
| HIGH     | 8     | ROBUST-01 (dummy training results), API-03 (FSM auto-reset), CFG-01 (torch missing), BUG-CC-18, CONC-01/04, CI-01/02/03, DEPLOY-24/25 |
| MEDIUM   | 35    | Config env var conflicts, port confusion, JSONDecodeError gaps, race conditions, test quality, error formats                          |
| LOW      | 27    | Config bypass, naming inconsistencies, missing assertions, minor protocol asymmetries                                                 |

---

*End of outstanding development items document (v5.0.0 — validated via 10-agent audit: 5 repo-focused + 5 cross-cutting concern agents across 8 repositories).*
