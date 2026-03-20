# Thread Implementation Delta Analysis

**Date**: 2026-03-19
**Thread**: `imperative-meandering-steele`
**Purpose**: Detailed comparison of changes made (then discarded) during this thread versus the previously committed changes from prior threads.

---

## Context

During this thread, I re-implemented Phase 1a, Phase 1b, and Phase 2 of the CasCor Concurrency Architecture without awareness that prior threads had already committed and pushed identical work as merged PRs. Upon discovering the prior work (via `gh pr list`), all local changes were discarded and the repos were updated to the merged state.

This document catalogs every difference between the discarded implementation and the committed implementation.

---

## Phase 1a: Security Fixes for Multiprocessing Path

**Prior commit**: `27cce13` (PR #29, merged into juniper-cascor)
**Files affected**: `security.py`, `constants_model.py`, `cascade_correlation_config.py`, `cascade_correlation.py`

### 1. Timing-safe API key comparison (`security.py`)

| Aspect         | Discarded (this thread)                                        | Committed (PR #29)                                             |
|----------------|----------------------------------------------------------------|----------------------------------------------------------------|
| Import         | `import hmac`                                                  | `import hmac`                                                  |
| Implementation | `any(hmac.compare_digest(api_key, k) for k in self._api_keys)` | `any(hmac.compare_digest(api_key, k) for k in self._api_keys)` |

**Verdict**: Identical. No delta.

### 2. Hardcoded authkey removal (`constants_model.py`)

| Aspect          | Discarded (this thread)                                      | Committed (PR #29)                                                       |
|-----------------|--------------------------------------------------------------|--------------------------------------------------------------------------|
| Approach        | Generate at module-import time using `secrets.token_hex(32)` | Set to `None`; defer generation to `CascadeCorrelationConfig.__init__()` |
| Value           | `_PROJECT_MODEL_AUTHKEY = _secrets.token_hex(32)`            | `_PROJECT_MODEL_AUTHKEY = None`                                          |
| Import          | `import secrets as _secrets` at module scope                 | No import in constants_model.py                                          |
| Generation site | `constants_model.py` line 47                                 | `cascade_correlation_config.py` line 218-219                             |

**Verdict**: **Significant architectural difference.**

- **Discarded**: Authkey generated once per Python process at import time. Every `CascadeCorrelationConfig` instance in the same process shares the same key.
- **Committed**: Authkey is `None` by default; each `CascadeCorrelationConfig` instance generates its own unique key via `secrets.token_hex(32)` in `__init__()`. This is more flexible — users can still pass an explicit authkey, and each network instance gets its own key.
- **Committed is better**: The deferred generation pattern is more Pythonic, allows per-instance keys, and avoids side effects at module import time.

### 3. Config authkey handling (`cascade_correlation_config.py`)

| Aspect       | Discarded (this thread)                        | Committed (PR #29)                                                              |
|--------------|------------------------------------------------|---------------------------------------------------------------------------------|
| Changes      | None (not modified)                            | Type annotation changed to `str \| None`, auto-generation added                 |
| Default type | `str` (receives the hex string from constants) | `str                            \| None` (receives `None`, generates on demand) |

**Verdict**: **Delta — discarded version missed this file entirely.** The committed version modifies the config class to accept `None` and auto-generate, while the discarded version relied on the constant being pre-generated. The committed approach is cleaner.

### 4. RestrictedUnpickler (`cascade_correlation.py`)

| Aspect                 | Discarded (this thread)                                                                                                           | Committed (PR #29)                                          |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Class name             | `RestrictedUnpickler`                                                                                                             | `RestrictedUnpickler`                                       |
| Allowlist location     | Module-level `_RESTRICTED_UNPICKLER_ALLOWED_CLASSES` set                                                                          | Class attribute `RestrictedUnpickler.ALLOWED_CLASSES` set   |
| Allowlist entries      | 43 entries (more comprehensive)                                                                                                   | 26 entries (more conservative)                              |
| `loads()` method       | Module-level `restricted_loads()` function                                                                                        | `@classmethod RestrictedUnpickler.loads()`                  |
| Additional activations | All 13 activation types listed                                                                                                    | Only Tanh, Sigmoid, ReLU                                    |
| Extra entries          | `complex`, `frozenset`, `torch.int32`, `torch.bool`, `torch.float64`, `torch.nn.modules.linear.Identity`                          | Only 3 activations, no `complex`/`frozenset`, no `Identity` |
|                        | all 13 activation types, `numpy._core.multiarry._reconstruct`, `cascade_correlation.cascade_correlation.ActivationWithDerivative` |                                                             |

**Detailed allowlist comparison:**

Entries in **discarded only** (not in committed):

- `("builtins", "complex")`
- `("builtins", "frozenset")`
- `("_codecs", "encode")` — committed has this
- `("torch", "int32")`
- `("torch", "bool")`
- `("torch", "float64")`
- `("torch.nn.modules.linear", "Identity")`
- `("torch.nn.modules.activation", "LeakyReLU")`
- `("torch.nn.modules.activation", "ELU")`
- `("torch.nn.modules.activation", "SELU")`
- `("torch.nn.modules.activation", "GELU")`
- `("torch.nn.modules.activation", "Softmax")`
- `("torch.nn.modules.activation", "Softplus")`
- `("torch.nn.modules.activation", "Hardtanh")`
- `("torch.nn.modules.activation", "Softshrink")`
- `("torch.nn.modules.activation", "Tanhshrink")`
- `("numpy._core.multiarray", "_reconstruct")` (Python 3.14+ compat)
- `("cascade_correlation.cascade_correlation", "ActivationWithDerivative")`

Entries in **committed only** (not in discarded):

- None — committed is a strict subset

**Verdict**: **Meaningful difference.**
The discarded version has a larger allowlist (43 vs 26 entries).
The committed version is more conservative — it only allows the 3 most common activation functions.
However, the discarded version was empirically validated to support all activation types available in the system.
The committed version would **fail at runtime** if a `CandidateUnit` uses `Identity`, `LeakyReLU`, `ELU`, `SELU`, `GELU`, `Softmax`, `Softplus`, `Hardtanh`, `Softshrink`, or `Tanhshrink` activation functions.
This is a **potential bug in the committed code** if the `RestrictedUnpickler` is ever used for those activations.

**Note:**
As the committed code's own docstring acknowledges, `multiprocessing.Queue` uses its own internal unpickler that cannot be overridden, so `RestrictedUnpickler` is only used for manual deserialization paths.
The practical impact depends on whether those paths handle non-standard activations.

### 5. Result validation (`cascade_correlation.py`)

| Aspect                          | Discarded (this thread)                                                              | Committed (PR #29)                                       |
|---------------------------------|--------------------------------------------------------------------------------------|----------------------------------------------------------|
| Function scope                  | Module-level `_validate_training_result(result)`                                     | Instance method `self._validate_training_result(result)` |
| Return type                     | `tuple[bool, str]` (is_valid, error_message)                                         | `bool` (True/False, logs internally)                     |
| Correlation bounds check        | Yes (0.0 to 1.0)                                                                     | Yes (0.0 to 1.0)                                         |
| Candidate type check            | Yes (`isinstance(result.candidate, CandidateUnit)`)                                  | Yes (`isinstance(result.candidate, CandidateUnit)`)      |
| Tensor NaN/Inf check            | Yes (norm_output, norm_error)                                                        | Yes (norm_output, norm_error)                            |
| Weight magnitude check          | Yes (`_RESULT_MAX_WEIGHT_MAGNITUDE = 100.0`, checks `weights` and `bias` attributes) | No                                                       |
| Numerator/denominator NaN check | Yes                                                                                  | No                                                       |
| `math` module import            | Yes (for `math.isnan`, `math.isinf`)                                                 | No (uses `torch.isnan`, `torch.isinf`)                   |
| Logging                         | Returns error message string for caller to log                                       | Logs directly via `self.logger.error/warning`            |

**Verdict**: **Moderate difference.**
The discarded version is more thorough — it checks weight magnitude, numerator/denominator fields, and uses the `math` module for scalar checks.
The committed version is simpler but omits weight magnitude validation (a concern from the plan's V-4 threat).
The discarded version's module-level function is arguably cleaner for testability; the committed version's instance method has direct logger access.

### 6. Queue size limits (`cascade_correlation.py`)

| Aspect                | Discarded (this thread)                      | Committed (PR #29)                 |
|-----------------------|----------------------------------------------|------------------------------------|
| Constant name         | `_QUEUE_MAXSIZE = 1024`                      | (literal `1000` used inline)       |
| Queue factory maxsize | `Queue(maxsize=_QUEUE_MAXSIZE)`              | `Queue(maxsize=1000)`              |
| Direct queue maxsize  | `self._mp_ctx.Queue(maxsize=_QUEUE_MAXSIZE)` | `self._mp_ctx.Queue(maxsize=1000)` |

**Verdict**: **Minor difference.** The discarded version uses a named constant (`1024`), the committed version uses a literal (`1000`). The discarded approach is marginally cleaner for maintainability, but functionally equivalent.

### 7. Test coverage

| Aspect                | Discarded (this thread) | Committed (PR #29)                                           |
|-----------------------|-------------------------|--------------------------------------------------------------|
| New test file         | None created            | `test_cascade_correlation_security.py` (329 lines, 27 tests) |
| Existing test updates | None                    | 18 lines added to `test_api_security.py`                     |

**Verdict**: **Significant gap.**
The discarded version created no tests; the committed version adds 27 dedicated security tests covering the RestrictedUnpickler, result validation, and queue limits.

---

## Phase 1b: WebSocket Worker Endpoint Infrastructure

**Prior commit**: `8cde48f` (PR #30, merged into juniper-cascor)
**Files affected**: 8 new files, 8 modified files

### 1. Protocol module (`api/workers/protocol.py`)

| Aspect                   | Discarded (this thread)                                                                                                       | Committed (PR #30)                                                                           |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Lines                    | ~230                                                                                                                          | ~330                                                                                         |
| MessageType class        | `str, Enum` (standard Enum)                                                                                                   | `StrEnum` (Python 3.11+)                                                                     |
| Additional message types | `REGISTER_ACK`, `HEARTBEAT_ACK`, `NO_TASKS`, `DISCONNECT`                                                                     | `TOKEN_REFRESH`, `ERROR`                                                                     |
| Architecture             | Dataclasses (`TaskAssignment`, `TaskResult`, `WorkerCapabilities`, `TensorManifestEntry`) + Functions (`create_*`, `parse_*`) | Single `WorkerProtocol` class with static builder methods (`build\_*`) + `BinaryFrame` class |
| Binary encoding          | `encode_tensor_frame()` / `decode_tensor_frame()` as module functions                                                         | `BinaryFrame.encode()` / `BinaryFrame.decode()` as static methods                            |
| Validation               | `parse_task_result()` raises ValueError                                                                                       | `WorkerProtocol.validate_task_result()` returns list of error strings                        |
| Tensor validation        | Not in protocol                                                                                                               | `WorkerProtocol.validate_tensors()` — checks shape, dtype, NaN, Inf, magnitude               |
| Registration validation  | Not in protocol                                                                                                               | `WorkerProtocol.validate_register()`                                                         |
| Frame constants          | `MAX_FRAME_SIZE = 100MB`                                                                                                      | `_MAX_FRAME_SIZE = 100MB` (same value, private naming)                                       |
| Max dimensions           | 8                                                                                                                             | 10                                                                                           |

**Verdict**: **Significantly different architecture.** Both implement the same wire protocol, but:

- Committed uses class-based organization (`BinaryFrame`, `WorkerProtocol`) vs. discarded's standalone functions and dataclasses.
- Committed includes `TOKEN_REFRESH` and `ERROR` message types (forward-looking for Phase 4).
- Committed includes comprehensive validation methods (`validate_tensors`, `validate_register`) that the discarded version lacks.
- Discarded includes `REGISTER_ACK`, `HEARTBEAT_ACK`, `NO_TASKS`, `DISCONNECT` message types that the committed version omits (these are handled as ad-hoc JSON in the committed version).

### 2. Registry module (`api/workers/registry.py`)

| Aspect                  | Discarded (this thread)                                    | Committed (PR #30)                                                    |
|-------------------------|------------------------------------------------------------|-----------------------------------------------------------------------|
| Lines                   | ~150                                                       | ~192                                                                  |
| `WorkerRegistration`    | Dataclass with `websocket` field, mutable `health_score`   | Dataclass without `websocket` field, computed `health_score` property |
| Health scoring          | Mutable float adjusted by +0.05 (success) / -0.2 (failure) | Computed as `tasks_completed / total`                                 |
| `max_workers` limit     | Constructor parameter, enforced in `register()`            | Not present — no hard cap                                             |
| `register()` return     | `bool` (False if full or duplicate)                        | `WorkerRegistration` (always succeeds, replaces duplicates)           |
| `register()` parameters | `worker_id, websocket, capabilities`                       | `worker_id, capabilities` (no websocket)                              |
| WebSocket reference     | Stored in `WorkerRegistration.websocket`                   | Not stored in registry (managed externally)                           |
| `deregister` naming     | `unregister()`                                             | `deregister()`                                                        |
| `get_status()` method   | Yes (returns full status dict)                             | No                                                                    |
| `clear()` method        | No                                                         | Yes                                                                   |
| `is_alive()` method     | On `WorkerRegistry.get_stale_workers()`                    | On `WorkerRegistration.is_alive(timeout)`                             |

**Verdict**: **Significantly different design.** Key architectural difference: the discarded version stores WebSocket references in the registry, while the committed version keeps the registry as pure data (WebSocket management is external). The committed approach is cleaner — it avoids mixing async WebSocket objects with thread-safe registry state. The committed version's computed health score is simpler than the discarded version's manually adjusted score.

### 3. Coordinator module (`api/workers/coordinator.py`)

| Aspect               | Discarded (this thread)                                   | Committed (PR #30)                                                  |
|----------------------|-----------------------------------------------------------|---------------------------------------------------------------------|
| Lines                | ~310                                                      | ~402                                                                |
| `PendingTask` fields | `task_tuple` (raw tuple stored)                           | `candidate_data`, `training_params`, `tensors` (parsed)             |
| Task dispatch        | `try_assign_task()` sends directly via websocket          | Uses `_send_callbacks` dict for async dispatch from training thread |
| Result collection    | `receive_result()` called from handler                    | `submit_result()` called from handler                               |
| Round management     | `begin_round()` / `end_round()`                           | `submit_tasks()` / `collect_results()` / `clear_round()`            |
| Health monitoring    | Background thread with `_monitor_loop()`                  | Background thread with `_health_monitor_loop()`                     |
| Tensor handling      | Builds frames inside coordinator (`_build_tensor_frames`) | Delegates to `BinaryFrame.encode()` at dispatch time                |
| Blocking collection  | `end_round()` returns results immediately                 | `collect_results()` blocks with timeout using `Event.wait()`        |

**Verdict**: **Substantially different architecture.** The committed version uses a callback-based dispatch pattern (`register_send_callback`/`_send_callbacks`) for cross-thread async communication, which is more sophisticated than the discarded version's direct WebSocket access. The committed `collect_results()` with `Event.wait()` provides proper synchronous blocking from the training thread, while the discarded version requires external coordination.

### 4. WebSocket handler (`api/websocket/worker_stream.py`)

| Aspect                   | Discarded (this thread)                                                | Committed (PR #30)                                                          |
|--------------------------|------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| Lines                    | ~170                                                                   | ~273                                                                        |
| Origin check order       | After auth check                                                       | Before auth check (first thing)                                             |
| Auth pattern             | Same as existing handlers                                              | Same as existing handlers                                                   |
| Registration             | Registers with `registry.register(worker_id, websocket, capabilities)` | Registers with `registry.register(worker_id, capabilities)` (no websocket)  |
| Task dispatch on connect | `coordinator.try_assign_task(worker_id)`                               | `coordinator.register_send_callback(worker_id, send_fn)` + initial dispatch |
| Binary frame handling    | Manual `websocket.receive()` after task_result                         | `_receive_binary_frames()` helper with validation                           |
| Error handling           | Basic try/except                                                       | Detailed per-message error handling with protocol error messages            |
| Message loop             | Generic `websocket.receive()`                                          | Structured `websocket.receive_text()` / `websocket.receive_bytes()`         |

**Verdict**: **Moderate structural differences.** The committed version has more detailed error handling, a helper function for binary frame reception, and uses the callback pattern for async dispatch. The Origin check ordering difference (before vs. after auth) is a minor security consideration — checking Origin first (committed) avoids wasting effort on auth for browser-originated requests.

### 5. Settings (`api/settings.py`)

| Aspect        | Discarded (this thread)                                                                                                        | Committed (PR #30)                                             |
|---------------|--------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| New fields    | `remote_workers_enabled`, `remote_workers_max`, `remote_workers_heartbeat_timeout`, `remote_workers_task_reassignment_timeout` | `worker_heartbeat_timeout`, `worker_task_reassignment_timeout` |
| Enable toggle | Explicit `remote_workers_enabled: bool`                                                                                        | No explicit toggle (presence of workers implies enabled)       |
| Max workers   | `remote_workers_max: int = 50`                                                                                                 | Not in settings (handled in coordinator)                       |
| Field naming  | `remote_workers_*` prefix                                                                                                      | `worker_*` prefix                                              |

**Verdict**: **Minor naming/approach difference.** The discarded version has an explicit enable toggle; the committed version is simpler.

### 6. App integration (`api/app.py`)

| Aspect                | Discarded (this thread)                          | Committed (PR #30)                               |
|-----------------------|--------------------------------------------------|--------------------------------------------------|
| Initialization        | Conditional on `settings.remote_workers_enabled` | Always initializes (conditional imports avoided) |
| Lifecycle integration | None (coordinator is standalone)                 | Coordinator injected into lifecycle manager      |
| WebSocket route       | `/ws/v1/workers`                                 | `/ws/v1/workers`                                 |
| Shutdown              | Stop coordinator monitoring                      | Stop coordinator monitoring                      |

**Verdict**: **Moderate difference.** The committed version integrates the coordinator with the lifecycle manager, which is needed for the training thread to dispatch tasks. The discarded version would require additional glue code.

### 7. Additional files in committed but not discarded

| File                                       | Lines      | Purpose                                      |
|--------------------------------------------|------------|----------------------------------------------|
| `api/lifecycle/manager.py` (modified)      | +19 lines  | Coordinator injection into lifecycle manager |
| `cascade_correlation.py` (modified)        | +172 lines | Dual-path dispatch (local MP + remote WS)    |
| `cascade_correlation_config.py` (modified) | +11 lines  | Remote worker config fields                  |
| `test_worker_protocol.py`                  | 317 lines  | Protocol unit tests                          |
| `test_worker_registry.py`                  | 186 lines  | Registry unit tests                          |
| `test_worker_coordinator.py`               | 285 lines  | Coordinator unit tests                       |
| `test_worker_stream.py`                    | 228 lines  | WebSocket handler tests                      |
| `test_api_settings.py` (modified)          | +19 lines  | Settings field tests                         |
| `test_lifecycle_manager.py` (modified)     | +37 lines  | Lifecycle coordinator tests                  |

**Verdict**: **Major gap.** The committed version includes 120 new tests across 4 test files plus updates to 2 existing test files. The discarded version created zero tests. The committed version also integrates dual-path dispatch directly into `cascade_correlation.py` and the lifecycle manager — work that the discarded version deferred entirely.

---

## Phase 2: WebSocket Worker Agent (juniper-cascor-worker)

**Prior commit**: `9fa4cef` (PR #10, open on juniper-cascor-worker)
**Files affected**: 6 new/modified files + 6 test files

### 1. Config (`config.py`)

| Aspect                | Discarded (this thread)                 | Committed (PR #10)                                               |
|-----------------------|-----------------------------------------|------------------------------------------------------------------|
| WebSocket field names | `server_url`, `auth_token`, `worker_id` | `server_url`, `api_key`, no `worker_id`                          |
| TLS fields            | None                                    | `tls_cert`, `tls_key`, `tls_ca` (Phase 4 forward-compat)         |
| Mode selection        | `legacy_mode: bool` field on dataclass  | `legacy: bool` parameter on `validate()`                         |
| URL validation        | Checks `server_url` is non-empty        | Checks `server_url` starts with `ws://` or `wss://`              |
| Heartbeat validation  | None                                    | Checks `heartbeat_interval > 0` and `reconnect_backoff_base > 0` |
| Env var naming        | `CASCOR_AUTH_TOKEN`                     | `CASCOR_API_KEY`                                                 |

**Verdict**: **Moderate differences.** The committed version is more thorough — it includes TLS placeholder fields for Phase 4, validates URL scheme, and validates numeric bounds. The naming difference (`auth_token` vs `api_key`) is important for consistency with the cascor API which uses `X-API-Key`.

### 2. Worker agent (`ws_worker.py` vs `worker.py`)

| Aspect               | Discarded (this thread)                                             | Committed (PR #10)                                               |
|----------------------|---------------------------------------------------------------------|------------------------------------------------------------------|
| Agent class location | New file `ws_worker.py`                                             | Appended to existing `worker.py`                                 |
| Class name           | `CascorWorkerAgent`                                                 | `CascorWorkerAgent`                                              |
| Connection class     | `WSConnection` (separate file)                                      | `WSConnection` (separate file)                                   |
| Architecture         | Separate `_handle_task()`, `_send_result()`, `_send_error_result()` | Similar structure with `_handle_task_assign()`, `_send_result()` |
| Training execution   | `asyncio.to_thread(execute_training_task, ...)`                     | `asyncio.to_thread(self._execute_task, ...)`                     |
| Heartbeat            | `asyncio.create_task(self._heartbeat_loop())`                       | `asyncio.create_task(self._heartbeat_loop())`                    |
| Message parsing      | Manual `json.loads()`                                               | Manual `json.loads()`                                            |

**Verdict**: **Similar architecture, different file organization.**
The committed version puts the new agent class in the same `worker.py` file (alongside `CandidateTrainingWorker`), while the discarded version creates a separate file.
The committed approach is simpler for a single file but makes `worker.py` much larger (335 lines).

### 3. Task executor (`task_executor.py`)

Both versions create a self-contained candidate training function. Key differences:

| Aspect             | Discarded (this thread)                                          | Committed (PR #10)                                             |
|--------------------|------------------------------------------------------------------|----------------------------------------------------------------|
| Function name      | `execute_training_task()`                                        | `execute_training_task()`                                      |
| Import of cascor   | Tries to import `CandidateUnit` from cascor if available         | Same approach — isolated import                                |
| BinaryFrame        | Duplicates `encode_tensor_frame` / `decode_tensor_frame` locally | Duplicates `BinaryFrame.encode` / `BinaryFrame.decode` locally |
| Activation mapping | `_ACTIVATIONS` dict with all 16 variants                         | Similar dict with fewer variants                               |
| Training algorithm | Custom SGD-based correlation maximization                        | Custom SGD-based correlation maximization                      |

**Verdict**: **Similar implementations.**
Both duplicate the binary frame encoding (necessary since the worker shouldn't depend on the server package).
The training algorithms are equivalent.

### 4. CLI (`cli.py`)

| Aspect           | Discarded (this thread)                          | Committed (PR #10) |
|------------------|--------------------------------------------------|--------------------|
| Legacy flag      | `--legacy`                                       | `--legacy`         |
| Signal handling  | Uses `threading.Event` for cross-platform compat | Same approach      |
| Default mode     | WebSocket                                        | WebSocket          |
| `signal.pause()` | Replaced with `Event.wait(timeout=1.0)`          | Same approach      |

**Verdict**: **Essentially identical approach.** Both replace `signal.pause()` with `Event.wait()` for cross-platform compatibility.

### 5. Test coverage

| Aspect          | Discarded (this thread) | Committed (PR #10)                                                                                           |
|-----------------|-------------------------|--------------------------------------------------------------------------------------------------------------|
| New test files  | None                    | `test_task_executor.py` (188 lines), `test_worker_agent.py` (237 lines), `test_ws_connection.py` (215 lines) |
| Updated tests   | None                    | `test_cli.py` (updated for dual-mode), `test_config.py` (100+ new lines)                                     |
| Total new tests | 0                       | 35                                                                                                           |

**Verdict**: **Major gap.**
The committed version includes comprehensive test coverage; the discarded version created no tests.

---

## Summary of All Differences

### Critical Differences (could affect correctness or security)

1. **RestrictedUnpickler allowlist**: Discarded version supports all 13 activation types; committed only supports 3. Committed version may fail for non-standard activations if `RestrictedUnpickler` is used on that path.

2. **Authkey generation site**: Discarded generates at import time (per-process); committed generates at config instantiation time (per-instance). Committed is architecturally superior.

3. **Weight magnitude validation**: Discarded checks candidate weight magnitudes in result validation; committed omits this check.

### Architectural Differences (design choices, not bugs)

4. **Protocol organization**: Discarded uses standalone dataclasses + functions; committed uses class-based `BinaryFrame` + `WorkerProtocol` with static methods.

5. **Registry WebSocket storage**: Discarded stores WebSocket refs in registry; committed keeps registry as pure data.

6. **Coordinator dispatch**: Discarded sends directly via WebSocket; committed uses callback pattern for async/sync bridge.

7. **Worker agent file location**: Discarded creates `ws_worker.py`; committed extends `worker.py`.

### Minor Differences (cosmetic, naming, values)

8. **Queue maxsize**: 1024 vs 1000 (named constant vs literal).
9. **Max dimensions**: 8 vs 10.
10. **Settings naming**: `remote_workers_*` vs `worker_*`.
11. **Env var**: `CASCOR_AUTH_TOKEN` vs `CASCOR_API_KEY`.

### Coverage Gaps (discarded had zero tests)

12. **Phase 1a**: Committed adds 27 security tests; discarded adds 0.
13. **Phase 1b**: Committed adds 120 tests across 4 files; discarded adds 0.
14. **Phase 2**: Committed adds 35 tests across 3 new files; discarded adds 0.
15. **Total**: Committed adds ~182 new tests; discarded adds 0.

### Missing Integration Work (in discarded)

16. Discarded did not modify `cascade_correlation.py` for dual-path dispatch (Phase 1b).
17. Discarded did not modify `lifecycle/manager.py` for coordinator injection.
18. Discarded did not modify `cascade_correlation_config.py` for remote worker config fields (Phase 1b).

---

## Recommendations

1. **RestrictedUnpickler allowlist** (Item 1): The committed version should be evaluated for completeness. If the `RestrictedUnpickler` is ever used on a path that deserializes `CandidateUnit` objects with non-standard activations (Identity, LeakyReLU, ELU, SELU, GELU, Softmax, Softplus, Hardtanh, Softshrink, Tanhshrink), it will fail. Consider expanding the allowlist or documenting the limitation.

2. **Weight magnitude validation** (Item 3): The committed result validation should be considered for enhancement with weight magnitude checks, matching the plan's V-4 threat model.

3. **No action needed for most items**: The committed implementations are generally equal or superior to the discarded versions in architecture and test coverage.
