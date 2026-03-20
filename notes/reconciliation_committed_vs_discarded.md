# Reconciliation: Committed vs. Discarded Implementations

**Date**: 2026-03-19
**Thread**: `imperative-meandering-steele` (branch conversation)
**Input**: `notes/thread_implementation_delta_analysis.md`

---

## Changes Applied

### Critical #1: RestrictedUnpickler Allowlist Expansion

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Problem**: The committed allowlist only included 3 activation types (Tanh, Sigmoid, ReLU). The system supports 13 activation types via `_PROJECT_MODEL_ACTIVATION_FUNCTIONS_DICT`. Deserializing a `CandidateUnit` with any other activation (Identity, LeakyReLU, ELU, SELU, GELU, Softmax, Softplus, Hardtanh, Softshrink, Tanhshrink) through `RestrictedUnpickler` would raise `UnpicklingError`.

**Fix**: Added all 13 activation type entries to `ALLOWED_CLASSES`:

- `torch.nn.modules.linear.Identity`
- `torch.nn.modules.activation.{Tanh, Sigmoid, ReLU, LeakyReLU, ELU, SELU, GELU, Softmax, Softplus, Hardtanh, Softshrink, Tanhshrink}`
- `numpy._core.multiarray._reconstruct` (Python 3.14+ internal rename compatibility)

**Verified**: All 13 activation types round-trip through `RestrictedUnpickler.loads()` successfully. Dangerous classes (`eval`, `os.system`) remain blocked.

### Critical #3: Weight Magnitude Validation

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Problem**: The committed `_validate_training_result()` method checked correlation bounds and tensor NaN/Inf, but did not check candidate weight/bias magnitudes. The plan's V-4 threat model (training poisoning) requires magnitude bounds to detect adversarial parameter injection.

**Fix**: Added weight magnitude validation to `_validate_training_result()`:

- New class attribute: `_RESULT_MAX_WEIGHT_MAGNITUDE = 100.0` (matches `_MAX_WEIGHT_MAGNITUDE` in protocol.py)
- Checks `weights` and `bias` attributes on `CandidateUnit` for NaN, Inf, and magnitude exceeding the limit
- Logs detailed warning messages identifying which parameter and what its magnitude was

**Verified**: Rejects weights with magnitude > 100.0, NaN weights, and Inf bias. Accepts weights at boundary (99.0).

### Minor #8: Queue Maxsize Named Constant

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Problem**: Queue maxsize used literal `1000` in 4 locations with no named constant.

**Fix**:

- Introduced `_QUEUE_MAXSIZE = 1024` named constant
- Replaced all 4 occurrences of `Queue(maxsize=1000)` / `mp.Queue(maxsize=1000)` with `_QUEUE_MAXSIZE`
- Updated 2 tests in `test_cascade_correlation_security.py` to assert against `_QUEUE_MAXSIZE` instead of literal `1000`

### Minor #9: Max Dimensions

**Status**: No change needed. Already `10` in committed code (`protocol.py:99`).

### Minor #10: Settings Naming

**Files**: `juniper-cascor/src/api/settings.py`, `juniper-cascor/src/api/app.py`, `juniper-cascor/src/tests/unit/api/test_api_settings.py`

**Problem**: Settings used `worker_*` prefix; should use `remote_workers_*` for clarity that these are remote worker settings (not local multiprocessing worker settings).

**Fix**: Renamed across all files:

- `worker_heartbeat_timeout` -> `remote_workers_heartbeat_timeout`
- `worker_task_reassignment_timeout` -> `remote_workers_task_reassignment_timeout`
- Module-level constants renamed accordingly
- Environment variable prefix changes from `JUNIPER_CASCOR_WORKER_*` to `JUNIPER_CASCOR_REMOTE_WORKERS_*`
- Test assertions and env var names updated

### Minor #11: Env Var Naming (cascor-worker)

**Files**: `juniper-cascor-worker` worktree (branch `feature/phase-2-websocket-worker`, PR #10)

**Problem**: PR #10 uses `CASCOR_API_KEY` environment variable and `api_key` field name. Should be `CASCOR_AUTH_TOKEN` / `auth_token` to distinguish from the server-side API key concept and match the user-facing naming convention.

**Fix**: Renamed across config.py, cli.py, worker.py, and test files:

- Field: `api_key` -> `auth_token` (in `WorkerConfig` dataclass)
- Env var: `CASCOR_API_KEY` -> `CASCOR_AUTH_TOKEN`
- CLI arg: `--api-key` -> `--auth-token`
- Internal parameter in `ws_connection.py` kept as `api_key` (internal API, maps via `worker.py` call site)
- All test assertions updated

---

## Architectural Analysis

### Difference #4: Protocol Organization

**Committed**: Class-based with `BinaryFrame` (encode/decode static methods) and `WorkerProtocol` (build_*and validate_* static methods).

**Discarded**: Standalone dataclasses (`TaskAssignment`, `TaskResult`, `WorkerCapabilities`, `TensorManifestEntry`) with module-level functions (`create_*`, `parse_*`, `encode_tensor_frame`, `decode_tensor_frame`).

#### Strengths of Committed (class-based)

| Strength                         | Detail                                                                                                                                                                         |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Namespace organization**       | `BinaryFrame.encode()` and `WorkerProtocol.build_register()` self-documenting via class context. obvious which functions belong together.                                      |
| **Discoverability**              | IDE autocomplete on `WorkerProtocol.` reveals all available operations. Standalone functions require knowing the naming convention.                                            |
| **Validation co-location**       | `validate_task_result()`, `validate_tensors()`, `validate_register()` w/ validated builders. Discarded ver, `parse_task_result()` parses & partial validation. less composable |
| **Forward-compatible msg types** | `TOKEN_REFRESH` and `ERROR` already defined, ready for Phase 4. Discarded used ad-hoc types (`REGISTER_ACK`, `NO_TASKS`, `DISCONNECT`) to be added later.                      |
| **Single authority constants**   | `_MAX_FRAME_SIZE`, `_MAX_CORRELATION`, `_MAX_WEIGHT_MAGNITUDE` are module-level but used only by the protocol classes, keeping bounds checking centralized.                    |

#### Weaknesses of Committed (class-based)

| Weakness                       | Detail                                                                                                                                                                               |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **No typed data structures**   | The committed version passes `dict[str, Any]` everywhere. The discarded version's dataclasses (`TaskAssignment`, `TaskResult`) provide type safety and IDE support for field access. |
| **Verbose static methods**     | `WorkerProtocol.build_task_assign(task_id=..., round_id=..., ...)` requires remembering all parameter names. A `TaskAssignment` dataclass can be constructed piecemeal.              |
| **No explicit ACK/NACK types** | The discarded version explicitly models `REGISTER_ACK`, `HEARTBEAT_ACK`, `NO_TASKS` as enum members. The committed version uses ad-hoc dicts for these, which is less type-safe.     |

#### Risks and Guardrails

| Risk                        | Guardrail                                                                                                                                            |
|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Dict key typos**          | `validate_task_result()` checks required fields — runtime validation compensates for lack of static types.                                           |
| **Message format drift**    | Both implementations duplicate frame encoding in the worker. The committed version's `BinaryFrame` is at least a named class that can be referenced. |
| **Overly permissive dicts** | Tests (`test_worker_protocol.py`) cover all builders and validators, providing regression protection.                                                |

**Recommendation**: The committed approach is adequate. If type safety becomes a concern, typed message dataclasses could be added later as wrappers around the dict builders without breaking the wire format.

---

### Difference #5: Registry WebSocket Storage

**Committed**: `WorkerRegistration` is a pure data record (no WebSocket reference). WebSocket management is external — the handler maintains the mapping.

**Discarded**: `WorkerRegistration` stores the `WebSocket` object directly. The registry owns both data and connection lifecycle.

#### Strengths of Committed (pure data)

| Strength                         | Detail                                                                                                                                                    |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Thread-safety simplification** | `WorkerRegistration` contains only serializable, thread-safe data. No async WebSocket objects cross thread boundaries inside the lock-protected registry. |
| **Testability**                  | Registry can be tested without mocking WebSocket objects. Pure data operations (register, heartbeat, assign_task) are trivially unit-testable.            |
| **Separation of concerns**       | The registry answers "who is connected?" The handler answers "how do I reach them?" This prevents the registry from becoming a god object.                |
| **Garbage collection**           | No risk of the registry holding references to closed WebSocket objects. The handler closes the connection; the registry just records deregistration.      |
| **Serializable status**          | `get_all_workers()` returns data that can be serialized to JSON for monitoring endpoints without stripping WebSocket references.                          |

#### Weaknesses of Committed (pure data)

| Weakness                        | Detail                                                                                                                                                                               |
|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Indirection for dispatch**    | To send a message to a worker, the coordinator needs a callback or lookup mechanism separate from the registry. The committed code uses `register_send_callback()` — an extra layer. |
| **Consistency gap**             | The registry might say a worker is registered, but its WebSocket could have already closed. The handler must deregister on disconnect promptly.                                      |
| **No atomic "assign-and-send"** | Assigning a task (registry) and sending it (handler) are two separate operations. A failure between them leaves the task assigned but unsent.                                        |

#### Strengths of Discarded (WebSocket in registry)

| Strength                 | Detail                                                                                                                        |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| **Atomic dispatch**      | `coordinator.try_assign_task()` can mark the task assigned AND send it in one operation since it has the WebSocket reference. |
| **Simpler mental model** | "The registry knows everything about a worker" — one place to look up both identity and communication channel.                |

#### Weaknesses of Discarded (WebSocket in registry)

| Weakness                            | Detail                                                                                                                                                                            |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Thread/async boundary violation** | FastAPI WS's are async & Sync train threads access Registry. Call `await websocket.send_json()` from sync context. needs `asyncio.run_coroutine_threadsafe()`, complex, deadlock. |
| **Leaked references**               | If a WebSocket disconnects but the registry isn't updated, the stored reference becomes a dead object. Sending to it raises exceptions that must be caught everywhere.            |
| **Testing complexity**              | Every registry test needs WebSocket mocks with async capabilities, increasing test surface area and fragility.                                                                    |

#### Risks and Guardrails

| Risk                            | Guardrail                                                                                                                             |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **Stale callback** (committed)  | The coordinator's health monitor thread detects stale workers via heartbeat timeout and removes both the callback and registry entry. |
| **Assign-send gap** (committed) | If sending fails, the callback catches the exception and the coordinator unassigns the task for reassignment.                         |
| **Dead WebSocket** (discarded)  | Would require a health-check wrapper around every send operation, duplicating the heartbeat logic.                                    |

**Recommendation**: The committed approach (pure data registry) is the correct design for this architecture. The async/sync boundary between the training thread and WebSocket handlers makes it dangerous to store async objects in a lock-protected data structure. The callback pattern adds one layer of indirection but eliminates an entire class of concurrency bugs.

---

## Test Results

| Suite                                       | Result                                                    |
|---------------------------------------------|-----------------------------------------------------------|
| juniper-cascor unit tests                   | **2250 passed**, 15 skipped, 0 failures                   |
| juniper-cascor-worker tests (PR #10 branch) | **97 passed**, 0 failures (deprecation warnings expected) |

---

## Files Modified

### juniper-cascor (main branch)

| File                                                  | Changes                                                                                                                                                               |
|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `src/cascade_correlation/cascade_correlation.py`      | Expanded RestrictedUnpickler allowlist (+13 entries), added weight magnitude validation to `_validate_training_result()`, introduced `_QUEUE_MAXSIZE = 1024` constant |
| `src/api/settings.py`                                 | Renamed `worker_*` fields to `remote_workers_*`                                                                                                                       |
| `src/api/app.py`                                      | Updated references to renamed settings fields                                                                                                                         |
| `src/tests/unit/api/test_api_settings.py`             | Updated assertions and env var names for renamed fields                                                                                                               |
| `src/tests/unit/test_cascade_correlation_security.py` | Updated queue maxsize assertions to use `_QUEUE_MAXSIZE`                                                                                                              |

### juniper-cascor-worker (feature/phase-2-websocket-worker branch, PR #10)

| File                              | Changes                                                                    |
|-----------------------------------|----------------------------------------------------------------------------|
| `juniper_cascor_worker/config.py` | Renamed `api_key` -> `auth_token`, `CASCOR_API_KEY` -> `CASCOR_AUTH_TOKEN` |
| `juniper_cascor_worker/cli.py`    | Renamed `--api-key` -> `--auth-token`, env var reference                   |
| `juniper_cascor_worker/worker.py` | Updated config field reference at call site                                |
| `tests/test_config.py`            | Updated field and env var assertions                                       |
| `tests/test_cli.py`               | Updated mock arg name and assertion                                        |
| `tests/test_worker_agent.py`      | Updated config fixture field name                                          |
