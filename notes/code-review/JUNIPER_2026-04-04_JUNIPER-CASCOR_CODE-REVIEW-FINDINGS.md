# juniper-cascor Comprehensive Code Review — Phases 2-7 Findings

**Status:** COMPLETE
**Reviewer:** Claude Code (automated deep review)
**Owner:** Paul Calnon
**Review date:** 2026-04-04
**Repository:** `juniper-cascor` (path: `/home/pcalnon/Development/python/Juniper/juniper-cascor`)
**Baseline commit:** `2ca3729fb8af0d96aad6be7594d4ae8477245317`
**Baseline branch:** `fix/ci-duplicate-params-and-imports`
**Companion document:** `CASCOR_COMPREHENSIVE_CODE_REVIEW_PLAN_2026-04-04.md` (Phase 0-1, CR-001 through CR-005)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Phase 2 — Architecture and Module Boundaries](#2-phase-2--architecture-and-module-boundaries)
3. [Phase 3 — Security, Reliability, Concurrency](#3-phase-3--security-reliability-concurrency)
4. [Phase 4 — Correctness and Numerical Behavior](#4-phase-4--correctness-and-numerical-behavior)
5. [Phase 5 — Performance and Scalability](#5-phase-5--performance-and-scalability)
6. [Phase 6 — Test Suite Quality](#6-phase-6--test-suite-quality)
7. [Phase 7 — Synthesis and Remediation Roadmap](#7-phase-7--synthesis-and-remediation-roadmap)

---

## 1. Executive Summary

This document contains **38 validated findings** (CR-006 through CR-076) across Phases 2-6, extending the baseline Phase 0-1 findings (CR-001 through CR-005) from the companion plan document.

### Severity Distribution

| Severity | Count | Findings                                                                                                                                                                               |
|----------|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **S0**   | 0     | —                                                                                                                                                                                      |
| **S1**   | 6     | CR-006, CR-007, CR-026, CR-040, CR-042, CR-071                                                                                                                                         |
| **S2**   | 23    | CR-008, CR-009, CR-010, CR-022, CR-023, CR-024, CR-025, CR-028, CR-029, CR-041, CR-043, CR-044, CR-045, CR-046, CR-048, CR-060, CR-062, CR-064, CR-065, CR-070, CR-072, CR-073, CR-074 |
| **S3**   | 9     | CR-021, CR-027, CR-047, CR-049, CR-050, CR-061, CR-063, CR-075, CR-076                                                                                                                 |

### Critical Path

The most impactful clusters are **core ML correctness** (CR-040, CR-042, CR-043, CR-045, CR-046, CR-048) and the **training limits data flow** (CR-006).
Early stopping is effectively non-functional, several optimizer types crash, snapshot round-trips can lose activation function identity, and new hidden unit weight initialization deviates from the standard algorithm.
Additionally, `max_epochs` and `max_iterations` are conflated in `fit()`, `max_iterations` has no persistent state in cascor, and canopy's growth iteration limit UI is a dead-end that never reaches cascor.
These should be addressed before any production training runs.

### Positive Observations (Clean Areas)

- **Dependency direction**: All imports flow correctly from `api/` toward core modules; no reverse dependencies.
- **Route layering**: All route handlers delegate exclusively to `TrainingLifecycleManager`; no direct ML state manipulation from routes.
- **API key comparison**: Uses `hmac.compare_digest()` (timing-safe).
- **Wire protocol**: Avoids pickle; uses struct-based numpy serialization with shape/dtype/NaN/magnitude validation.
- **Worker coordinator**: Uses proper `threading.Lock` for core state, with duplicate result detection.
- **Security headers**: CSP, X-Frame-Options, HSTS present via middleware.
- **Docker secrets**: `get_secret()` follows best practices.

---

## 2. Phase 2 — Architecture and Module Boundaries

### CR-006: Incomplete implementation of `max_epochs` and `max_iterations` as separate training limits — broken data flow across cascor and canopy

| Field                | Value                                                                                                                                                                                                                                                               |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Architectural / Logical                                                                                                                                                                                                                                             |
| **Secondary tags**   | data-flow, state-management, cross-project, API-contract                                                                                                                                                                                                            |
| **Severity**         | S1                                                                                                                                                                                                                                                                  |
| **Likelihood**       | High                                                                                                                                                                                                                                                                |
| **Effort**           | L                                                                                                                                                                                                                                                                   |
| **Validation**       | G2: juniper-cascor <-> juniper-canopy data flow: 1. `TrainingState.update_state()` drops `max_iterations`, 2. `fit()` combines epochs & iterations, 3. both limit edits in canopy, `nn_max_iterations` not sent to cascor, 4. defaults differ across constant chain |
| **Location**         | Multi-file, cross-project (see Data Flow Trace below)                                                                                                                                                                                                               |

**Observation:** `max_epochs` and `max_iterations` are semantically distinct training limits that have been partially implemented as separate concepts but are broken at multiple points in the data flow.

**Definitions:**

- **epoch** — a single pass through the entire training dataset
- **iteration** — one complete cycle through candidate training, network growth, and output retraining. Partially or unsuccessfully completed steps (e.g., candidate training fails to produce a valid candidate and the network does not grow) should still count as a completed iteration.

Both fields are needed. Both should meet the following requirements:

- Should be tracked by juniper-cascor
- Passed to juniper-canopy on network initialization
- Updated in juniper-canopy as part of the ongoing, training state messages
  - These messages are passed from juniper-cascor to juniper-canopy
  - These messages update the juniper-canopy display in (near) realtime
  - These messages are received via API and/or Web Socket
- Their upper limits should be editable in juniper-canopy
  - Updated values passed back to juniper-cascor
  - Integrated in juniper-cascor training

**Analysis — Data Flow Trace:**

The following table traces each field through the entire path from constants to canopy and back. Each row is a touchpoint; rows marked with a defect describe the specific breakage.

**`max_epochs` (upper limit on total dataset passes):**

| Component                 | File                                                | Field Name                                           | Default                                     | Status                                                                              |
|---------------------------|-----------------------------------------------------|------------------------------------------------------|---------------------------------------------|-------------------------------------------------------------------------------------|
| Constant (cascor)         | `cascor_constants/constants_model.py:205`           | `_PROJECT_MODEL_EPOCHS_MAX`                          | 10,000                                      | Exists                                                                              |
| Alias chain (cascor)      | `cascor_constants/constants.py:568→665→787`         | `_CASCOR_EPOCHS_MAX`                                 | 10,000                                      | Exists                                                                              |
|                           |                                                     | → `_SPIRAL_PROBLEM_EPOCHS_MAX`                       |                                             |                                                                                     |
|                           |                                                     | → `_CASCADE_CORRELATION_NETWORK_EPOCHS_MAX`          |                                             |                                                                                     |
| Config (cascor)           | `cascade_correlation_config.py:125`                 | `epochs_max`                                         | 10,000                                      | Exists                                                                              |
| Network instance          | `cascade_correlation.py:666`                        | `self.epochs_max`                                    | 10,000                                      | Exists                                                                              |
| `fit()` method            | `cascade_correlation.py:1428`                       | `max_epochs` parameter                               | Falls back to `self.output_epochs` (10,000) | **DEFECT: `max_epochs` is conflated with `max_iterations`                           |
|                           |                                                     |                                                      |                                             | -- Same value passed to `train_o$utput_layer()` as e$poch count                     |
|                           |                                                     |                                                      |                                             | -- AND to `grow_network()` as iteration count at line 1458**                        |
| API model (create)        | `api/models/network.py:19`                          | `NetworkCreateRequest.epochs_max`                    | **200**                                     | **DEFECT: Default 200 is inconsistent with:**                                       |
|                           |                                                     |                                                      |                                             | -- **constant default 10,000 and canopy default 1,000,000**                         |
| API model (update)        | `api/models/training.py:53`                         | `TrainingParamUpdateRequest.epochs_max`              | None (optional)                             | Exists                                                                              |
| Lifecycle manager         | `api/lifecycle/manager.py:176`                      | `max_iterations=kwargs.get("epochs_max", 200)`       | 200                                         | **DEFECT: Passes `epochs_max` using wrong key: `max_iterations`**                   |
|                           |                                                     |                                                      |                                             | -- **to `update_state()`, so it is silently dropped**                               |
| TrainingState             | `api/lifecycle/monitor.py:28,58`                    | `_STATE_FIELDS` contains `"max_epochs"`, default 200 | 200                                         | **DEFECT: Value not updated from network config, manager key is wrong; always 200** |
| WebSocket broadcast       | `api/websocket/messages.py`                         | `max_epochs` in state dict                           | 200 (stale)                                 | Consequence of above defect                                                         |
| Canopy protocol           | `canopy: backend/protocol.py:69`                    | `max_epochs: int`                                    | —                                           | Exists                                                                              |
| Canopy state sync         | `canopy: backend/state_sync.py:25,82-85`            | `SyncedState.max_epochs`                             | 0                                           | Exists, with fallback chain                                                         |
| Canopy TrainingState      | `canopy: backend/training_monitor.py:235,271`       | `__max_epochs`                                       | 200                                         | Exists                                                                              |
| Canopy UI                 | `canopy: frontend/dashboard_manager.py:598`         | `nn-max-total-epochs-input`                          | 1,000,000                                   | Exists                                                                              |
| Canopy → cascor param map | `canopy: backend/cascor_service_adapter.py:426-438` | `"nn_max_total_epochs": "epochs_max"`                | —                                           | Exists — correctly maps back to cascor                                              |
| Canopy set_params         | `canopy: main.py:2039`                              | `ts_updates["max_epochs"] = int(...)`                | —                                           | Exists — updates local TrainingState                                                |

**`max_iterations` (upper limit on cascade growth cycles):**

| Component                  | File                                        | Field Name                               | Default                              | Status                                                                                 |
|----------------------------|---------------------------------------------|------------------------------------------|--------------------------------------|----------------------------------------------------------------------------------------|
| Constant (cascor)          | —                                           | —                                        | —                                    | **MISSING: No dedicated constant for max growth iterations**                           |
| Config (cascor)            | `cascade_correlation_config.py`             | —                                        | —                                    | **MISSING: No `max_iterations` field in CascadeCorrelationConfig**                     |
| Network instance           | `cascade_correlation.py`                    | —                                        | —                                    | **MISSING: No `self.max_iterations` attribute**                                        |
| `grow_network()` parameter | `cascade_correlation.py:3596`               | `max_iterations`                         | 1,000 (hardcoded standalone default) | Exists as parameter only, not as persistent network state                              |
| `fit()` → `grow_network()` | `cascade_correlation.py:1458`               | `max_iterations=max_epochs`              | Same as max_epochs                   | **DEFECT: Passes `max_epochs` value as `max_iterations`, conflating the two concepts** |
| API model (create)         | `api/models/network.py`                     | —                                        | —                                    | **MISSING: No `max_iterations` field on `NetworkCreateRequest`**                       |
| API model (update)         | `api/models/training.py`                    | —                                        | —                                    | **MISSING: No `max_iterations` field on `TrainingParamUpdateRequest`**                 |
| TrainingState              | `api/lifecycle/monitor.py`                  | —                                        | —                                    | **MISSING: `max_iterations` not in `_STATE_FIELDS`**                                   |
| WebSocket broadcast        | —                                           | —                                        | —                                    | **MISSING: `max_iterations` not in state broadcast**                                   |
| Canopy constants           | `canopy: canopy_constants.py:47-49`         | `DEFAULT_MAX_GROWTH_ITERATIONS`          | 1,000                                | Exists                                                                                 |
| Canopy settings            | `canopy: settings.py:71`                    | `max_iterations: TrainingParamConfig`    | min=1, max=100,000, default=1,000    | Exists                                                                                 |
| Canopy UI                  | `canopy: frontend/dashboard_manager.py:578` | `nn-max-iterations-input`                | 1,000                                | Exists                                                                                 |
| Canopy → cascor param map  | `canopy: backend/cascor_service_adapter.py` | —                                        | —                                    | **MISSING: `nn_max_iterations` has no entry in `_CANOPY_TO_CASCOR_PARAM_MAP`:**        |
|                            |                                             |                                          |                                      | -- **logged as "Canopy-only params (no cascor mapping)" and dropped**                  |
| Canopy set_params          | `canopy: main.py:1989-1990`                 | `nn_max_iterations` recognized as nn_key | —                                    | **DEFECT: Stored locally via `setattr` but never forwarded to cascor**                 |

**Summary of defects:**

1. **`fit()` conflates epochs and iterations** (cascor `cascade_correlation.py:1458`): `max_iterations=max_epochs` passes one value for two fundamentally different limits
2. **`max_iterations` silently dropped by `TrainingState`** (cascor `manager.py:176`): Wrong key name passed to `update_state()`
3. **`max_iterations` has no cascor-side persistent state**: No constant, no config field, no network attribute, no API model field, no TrainingState field, no WebSocket broadcast
4. **Canopy `nn_max_iterations` is a dead-end**: UI control exists, user can edit it, but the value is never forwarded to cascor — it is logged and dropped
5. **Default values are inconsistent**: `epochs_max` defaults to 10,000 (constants), 200 (API model), 200 (auto-train settings), 1,000,000 (canopy UI)

#### Remediation options

**Option A — Full end-to-end implementation of both fields (recommended)**:

Implement `max_iterations` as a first-class field parallel to `max_epochs` across the entire data path:

1. **Constants** (cascor): Add `_PROJECT_MODEL_MAX_ITERATIONS = 1000` and alias chain through `constants.py` to `_CASCADE_CORRELATION_NETWORK_MAX_ITERATIONS`
2. **Config** (cascor): Add `max_iterations: int = _CASCADE_CORRELATION_NETWORK_MAX_ITERATIONS` to `CascadeCorrelationConfig`
3. **Network** (cascor): Add `self.max_iterations` attribute initialized from config; use it as the default in `grow_network()`
4. **`fit()`** (cascor): Deconflate — pass `max_epochs` to `train_output_layer()` for epoch limit and `self.max_iterations` (or a separate `max_iterations` parameter) to `grow_network()` for iteration limit
5. **API models** (cascor): Add `max_iterations: int = Field(1000, ge=1)` to `NetworkCreateRequest` and `TrainingParamUpdateRequest`
6. **TrainingState** (cascor): Add `"max_iterations"` to `_STATE_FIELDS`; add `_max_iterations` attribute; include in `get_state()` serialization
7. **Lifecycle manager** (cascor): Fix `create_network()` to pass both `max_epochs=...` and `max_iterations=...` to `update_state()` with correct keys; add `max_iterations` to `update_params()` updatable keys
8. **Canopy param map**: Add `"nn_max_iterations": "max_iterations"` to `_CANOPY_TO_CASCOR_PARAM_MAP`
9. **Canopy set_params**: Update `apply_params()` to forward `max_iterations` to cascor and update local TrainingState
10. **Defaults**: Align defaults — `max_epochs` should default to ~1,000,000 (matching canopy's `DEFAULT_TRAINING_EPOCHS`), `max_iterations` should default to ~1,000 (matching canopy's `DEFAULT_MAX_GROWTH_ITERATIONS` and `grow_network()`'s standalone default)

- **Strengths:** Correct semantics; consistent data flow; both limits independently controllable from canopy; aligned defaults across the stack
- **Weaknesses:** Touches both repos (cascor + canopy); requires coordinated PRs; API model change may require version bump
- **Risks:** Clients sending `max_iterations` to older cascor versions will have the field ignored (but this is no worse than today). Changing `epochs_max` default from 200/10,000 to 1,000,000 changes behavior for users relying on the old default as a training stop condition.
- **Guardrails:** (1) Add unit tests asserting both values flow through `create_network()` → `TrainingState` → `get_state()`. (2) Add integration test asserting canopy UI edit → cascor param update round-trip. (3) Verify `grow_network()` respects `max_iterations` independently from `max_epochs`. (4) Test that incomplete/failed growth cycles still increment the iteration counter. (5) Semver: minor version bump for both repos (new API fields, default changes).

**Option B — Cascor-only fix (partial)**:

Fix the cascor side only: add `max_iterations` to constants, config, network, TrainingState, and API models. Do not modify canopy. Canopy's `nn_max_iterations` UI would remain a dead-end until a follow-up PR wires it.

- **Strengths:** Single-repo change; smaller blast radius
- **Weaknesses:** Canopy users still can't control `max_iterations` until the follow-up
- **Risks:** Interim period where the field exists in cascor but canopy can't set it; could cause confusion if users see `max_iterations` in the status response but can't change it from the dashboard

**Recommendation:** Option A, executed as two coordinated PRs (cascor first, then canopy). The canopy side is primarily wiring an existing UI control to an existing param map — the UI already exists and the user already expects it to work. The cascor side is the larger change but follows established patterns for existing fields like `epochs_max`.

Both repos should be updated in the same development cycle to avoid a window where the field exists in cascor but canopy can't drive it.

---

### CR-007: State machine enters irrecoverable terminal state after FAILED or COMPLETED without enforced reset

| Field                | Value                                                                                                                                                                                                                            |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Logical                                                                                                                                                                                                                          |
| **Secondary tags**   | state-machine, lifecycle                                                                                                                                                                                                         |
| **Severity**         | S1                                                                                                                                                                                                                               |
| **Likelihood**       | Medium                                                                                                                                                                                                                           |
| **Effort**           | M                                                                                                                                                                                                                                |
| **Validation**       | G2 — Traced state transitions: `_handle_start` accepts only STOPPED/PAUSED; `start_training` checks only `is_started()` which returns False for FAILED/COMPLETED; `monitored_fit` START command silently fails from FAILED state |
| **Location**         | `src/api/lifecycle/manager.py:510` — `start_training` guard / `src/api/lifecycle/state_machine.py:113-124` — `_handle_start`                                                                                                     |

**Observation:** After training fails or completes, the state machine enters a terminal state. `start_training` bypasses the guard (it only checks `is_started()`), submits new work to the executor, but inside `monitored_fit`, `sm.handle_command(Command.START)` silently fails. The state machine becomes permanently desynchronized from actual training state.

**Analysis:** Manifests when: (1) training fails then user retries via POST `/v1/training/start`, or (2) training completes then user starts another session without calling reset. The state machine reports stale data while training actually executes. The error handler in `_run_training` also attempts `STOP` from FAILED state, producing spurious "Invalid transition" warnings.

#### Remediation options

**Option A — Auto-reset on start (recommended)**:

- If state is FAILED or COMPLETED, call `handle_command(Command.RESET)` before proceeding
- **Strengths:** Self-healing, backward-compatible, matches user intent
- **Weaknesses:** Implicit reset may surprise callers expecting explicit reset
- **Guardrails:** Log the auto-reset at INFO level; add regression test

**Option B — Enforce explicit reset**:

- Raise `RuntimeError` if state is FAILED or COMPLETED
- **Strengths:** Explicit, forces callers to acknowledge terminal state
- **Weaknesses:** Breaking change for clients that retry without resetting

**Option C — Remove duplicate error handler in `_run_training`**

- Remove the `except` block that redundantly attempts STOP after `monitored_fit` already handled failure
- **Strengths:** Eliminates spurious warning logs
- **Weaknesses:** Doesn't fix the root desynchronization

**Recommendation:** Option A combined with Option C.

---

### CR-008: WebSocket control stream documents `set_params` command but does not implement it

| Field                | Value                                                                                                                      |
|----------------------|----------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Architectural                                                                                                              |
| **Secondary tags**   | API-contract, websocket                                                                                                    |
| **Severity**         | S2                                                                                                                         |
| **Likelihood**       | Medium                                                                                                                     |
| **Effort**           | S                                                                                                                          |
| **Validation**       | G3 — Module docstring (line 5) lists `set_params`; `_VALID_COMMANDS` (line 21) omits it; `_execute_command` has no handler |
| **Location**         | `src/api/websocket/control_stream.py:5,21,80-102`                                                                          |

**Observation:** Docstring states the endpoint accepts `"set_params"` as a valid command. `_VALID_COMMANDS` only contains `{"start", "stop", "pause", "resume", "reset"}`. Clients sending `set_params` receive "Unknown command" error.

**Analysis:** Contract violation. The PATCH `/v1/training/params` REST endpoint exists as an alternative, but the WebSocket channel advertises capability it does not provide.

#### Remediation options

**Option A — Implement set_params (recommended)**:

- Add to `_VALID_COMMANDS` and `_execute_command`; call `lifecycle.update_params(params)`
- **Strengths:** Fulfills documented contract and meets application requirements
- **Guardrails:** Validate params against same whitelist as REST endpoint

**Option B — Remove from docstring**:

- **Strengths:** Zero risk, accurate documentation
- **Weaknesses:** Fails to meet application requirements and user expectations

**Recommendation:** Option A Immediately. This is critical functionality expected by users and a requirement for juniper-cascor and juniper-canopy.

---

### CR-009: Worker security modules (mTLS, anomaly detection, rate limiting, audit) are not integrated into runtime

| Field                | Value                                                                                                                                                                                                                                                    |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Architectural                                                                                                                                                                                                                                            |
| **Secondary tags**   | security, dead-code                                                                                                                                                                                                                                      |
| **Severity**         | S2                                                                                                                                                                                                                                                       |
| **Likelihood**       | Low                                                                                                                                                                                                                                                      |
| **Effort**           | L                                                                                                                                                                                                                                                        |
| **Validation**       | G4 — `TLSConfig`, `ConnectionRateLimiter`, `AnomalyDetector` (security.py) and `AuditLogger`, `WorkerMetrics` (audit.py) are defined and tested but never imported or instantiated in any runtime module. Grep confirms zero imports outside test files. |
| **Location**         | `src/api/workers/security.py` — `TLSConfig`, `ConnectionRateLimiter`, `AnomalyDetector` / `src/api/workers/audit.py` — `AuditLogger`, `WorkerMetrics`                                                                                                    |

**Observation:** Five security-related classes for the worker subsystem exist with full implementations and test coverage but have no integration point in production code. Docstrings indicate "Phase 4 components" implemented ahead of integration.

**Analysis:** Workers are currently authenticated by API key only. No mTLS, no connection-level rate limiting, no anomaly detection on training results, no audit trail. Mitigated by worker feature being relatively new and likely deployed in trusted networks.

#### Remediation options

**Option A — Wire into runtime (recommended)**:

- Feature-flag each component via `Settings` for gradual rollout
- **Strengths:** Completes security posture for distributed workers, fully meets application requirements
- **Weaknesses:** Significant integration work

**Option B — Document as intentionally deferred**:

- Add clear `# TODO: Phase 4 integration` markers
- **Strengths:** No code risk; clarifies intent
- **Weaknesses:** Fails to meet application requirments and security standards

**Recommendation:** Begin Option A using feature flags to accomplish an incremental roll-out.

---

### CR-010: Dual auth mechanisms — WebSocket endpoints lack middleware-level enforcement and rate limiting

| Field                | Value                                                                                                                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Architectural                                                                                                                                                                                    |
| **Secondary tags**   | security, consistency                                                                                                                                                                            |
| **Severity**         | S2                                                                                                                                                                                               |
| **Likelihood**       | Medium                                                                                                                                                                                           |
| **Effort**           | M                                                                                                                                                                                                |
| **Validation**       | G4 — `SecurityMiddleware` (middleware.py:67) uses `BaseHTTPMiddleware` which cannot intercept WebSocket upgrades. Each WS handler re-implements auth inline. No rate limiting on WS connections. |
| **Location**         | `src/api/middleware.py:67-73` / `src/api/websocket/training_stream.py:23-28` / `control_stream.py:28-33` / `worker_stream.py:46-51`                                                              |

**Observation:** REST routes are protected by centralized `SecurityMiddleware` (API key + rate limiting). WebSocket endpoints each perform inline auth checks (consistent but fragile). No rate limiting on WebSocket connections — a client can open connections at arbitrary rates up to `ws_max_connections=50`.

**Analysis:** Auth is functionally correct today. The rate limiting gap means an attacker with a valid API key (or in open-access mode) can consume all 50 WebSocket slots. Adding new WS endpoints requires remembering to copy auth boilerplate.

#### Remediation options

**Option A — Extract WebSocket auth into shared utility (recommended)**:

- Create `ws_authenticate(websocket)` helper; DRY, ensures consistency
- **Strengths:** Quick win, reduces boilerplate
- **Risks:** Minimal

**Option B — Add WebSocket connection rate limiting**:

- Wire `ConnectionRateLimiter` from `api/workers/security.py`
- **Strengths:** Closes the rate limiting gap
- **Weaknesses:** Requires instantiation and injection pattern

**Recommendation:** Option A as quick win; Option B as part of CR-009 integration.

---

## 3. Phase 3 — Security, Reliability, Concurrency

### CR-021: Global singleton initialization race in `get_api_key_auth()` and `get_rate_limiter()`

| Field                | Value                                                                                                                                                                     |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Concurrency                                                                                                                                                               |
| **Secondary tags**   | race-condition, dead-code                                                                                                                                                 |
| **Severity**         | S3                                                                                                                                                                        |
| **Likelihood**       | Low                                                                                                                                                                       |
| **Effort**           | S                                                                                                                                                                         |
| **Validation**       | G4 — Classic check-then-act race on module-level globals without lock. Functions are currently unused by the application (app creates instances directly in `app.state`). |
| **Location**         | `src/api/security.py:211-232` — `get_api_key_auth()`, `get_rate_limiter()`                                                                                                |

**Observation:** Both functions use check-then-set on module globals without locks. The application does not use these singletons — `create_app()` creates its own instances directly.

**Analysis:** Currently this is dead code with a latent race condition. The consequence would be benign duplication (two equivalent instances), not security bypass.

#### Remediation options

**Option A — Remove the unused singletons entirely**:

- **Strengths:** Dead code removal, eliminates confusion about authoritative auth instance
- **Weaknesses:** Removes critical functionality needed for other authentication and security enhancements. Blocks code changes needed to meet application requirements.
- **Guardrails:** Grep for all callers; verify only tests reference them

**Option B — Add a module-level Lock (recommended)**:

- **Strengths:** Correct because singletons are needed as part of the ongoing authentication and security updates.  Will be required by CR-009 and CR-010

**Recommendation:** Option B.

---

### CR-022: Prometheus metrics unbounded label cardinality on `endpoint` label

| Field                | Value                                                                                   |
|----------------------|-----------------------------------------------------------------------------------------|
| **Primary category** | Reliability                                                                             |
| **Secondary tags**   | observability, DoS, prometheus                                                          |
| **Severity**         | S2                                                                                      |
| **Likelihood**       | Medium                                                                                  |
| **Effort**           | S                                                                                       |
| **Validation**       | G4 — Well-documented Prometheus anti-pattern; `request.url.path` used directly as label |
| **Location**         | `src/api/observability.py:90-95` — `PrometheusMiddleware.dispatch()`                    |

**Observation:** `PrometheusMiddleware` uses `request.url.path` directly as the `endpoint` label. Routes with path parameters (`/v1/snapshots/{snapshot_id}`, `/v1/workers/{worker_id}`) produce unique time series per distinct value. 404s to arbitrary paths also create unique series.

**Analysis:** Unbounded cardinality growth can cause memory exhaustion and Prometheus scrape timeout. Only active when `metrics_enabled=True` (disabled by default).

#### Remediation options

**Option A — Normalize paths using FastAPI route resolution (recommended)**:

- Use `request.scope.get("route").path` (the template string) instead of actual path
- Fall back to `"unmatched"` for 404s
- **Strengths:** Correct cardinality
- **Guardrails:** Test with parameterized routes and 404s

**Option B — Path allowlist with "other" bucket**:

- **Weaknesses:** Requires maintaining allowlist when routes change

**Recommendation:** Option A.

---

### CR-023: Unvalidated `params` dict in `TrainingStartRequest` passed as `**kwargs` to `network.fit()`

| Field                | Value                                                                                                                                         |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Input validation                                                                                                                              |
| **Secondary tags**   | injection, API-contract                                                                                                                       |
| **Severity**         | S2                                                                                                                                            |
| **Likelihood**       | Low                                                                                                                                           |
| **Effort**           | M                                                                                                                                             |
| **Validation**       | G3 — `params: Optional[Dict[str, Any]]` with no validation; forwarded through `lifecycle.start_training(**kwargs)` to `network.fit(**kwargs)` |
| **Location**         | `src/api/routes/training.py:55-56` / `src/api/models/training.py:32`                                                                          |

**Observation:** API clients can pass arbitrary keyword arguments to `fit()`. Unexpected kwargs cause `TypeError` caught as training failure, but error messages may leak internal function signatures. The `update_params` endpoint correctly whitelists updatable keys; the `start_training` endpoint does not.

**Analysis:** JSON serialization limits injection to primitive types, so remote code execution is not possible. The risk is information disclosure (leaked parameter names) and unexpected behavior from overriding internal parameters.

#### Remediation options

**Option A — Whitelist allowed params keys (recommended)**:

- Match the `update_params` pattern
- **Strengths:** Consistent, prevents unexpected kwargs

**Option B — Replace with typed Pydantic model**:

- **Strengths:** Full validation, self-documenting contract
- **Weaknesses:** Breaking change for non-standard params

**Recommendation:** Option A as quick fix, Option B as required follow-up.

---

### CR-024: `RequestBodyLimitMiddleware` relies solely on `Content-Length` header — bypassable with chunked encoding

| Field                | Value                                                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Security                                                                                                                        |
| **Secondary tags**   | DoS, middleware, input-validation                                                                                               |
| **Severity**         | S2                                                                                                                              |
| **Likelihood**       | Medium                                                                                                                          |
| **Effort**           | S                                                                                                                               |
| **Validation**       | G3 — HTTP/1.1 spec allows `Transfer-Encoding: chunked` without `Content-Length`; middleware only checks `content-length` header |
| **Location**         | `src/api/middleware.py:60-64` — `RequestBodyLimitMiddleware.dispatch()`                                                         |

**Observation:** Middleware only checks `Content-Length` header. Chunked transfer encoding has no `Content-Length`, so the 10MB limit check is skipped entirely. Arbitrarily large bodies are fully buffered by FastAPI before Pydantic validation.

**Analysis:** Partially mitigated by uvicorn defaults, but not explicitly configured.

#### Remediation options

**Option A — Read and measure body incrementally**:

- **Strengths:** Catches all large bodies regardless of encoding
- **Weaknesses:** More complex middleware

**Option B — Configure uvicorn `--limit-max-request-size` (recommended for immediate mitigation)**

- **Strengths:** Simple operational fix
- **Weaknesses:** Requires infrastructure-level configuration

**Recommendation:** Option B immediately, Option A as defense-in-depth follow-up.

---

### CR-025: `WebSocketManager` `_active_connections` set lacks explicit async synchronization

| Field                | Value                                                                                                                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Concurrency                                                                                                                                                                           |
| **Secondary tags**   | race-condition, websocket                                                                                                                                                             |
| **Severity**         | S2                                                                                                                                                                                    |
| **Likelihood**       | Medium                                                                                                                                                                                |
| **Effort**           | M                                                                                                                                                                                     |
| **Validation**       | G2 — `broadcast_from_thread()` schedules coroutines on event loop; `connect()`/`disconnect()` mutate set from same loop; `_connection_meta` dict mutated without `.copy()` protection |
| **Location**         | `src/api/websocket/manager.py:29-30` — `_active_connections`; line 89-101 — `broadcast_from_thread()`                                                                                 |

**Observation:** Connections stored in a plain `set`. `broadcast()` uses `.copy()` for iteration (good), but `_connection_meta` dict is mutated without copy protection. Currently safe under CPython's single-threaded asyncio model, but correctness depends on implementation details.

**Analysis:** Fragile — a future event loop change or bug fix could break the implicit safety guarantee.

#### Remediation options

**Option A — Add `asyncio.Lock` (recommended)**

- **Strengths:** Correct regardless of event loop implementation; future-proof
- **Weaknesses:** Minor added complexity

**Option B — Document the single-event-loop assumption**:

- **Weaknesses:** Does not protect against future changes

**Recommendation:** Option A.

---

### CR-026: Worker `worker_id` is client-supplied with no server-side validation or uniqueness enforcement

| Field                | Value                                                                                                                                                        |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Security                                                                                                                                                     |
| **Secondary tags**   | authentication, impersonation                                                                                                                                |
| **Severity**         | S1                                                                                                                                                           |
| **Likelihood**       | Medium                                                                                                                                                       |
| **Effort**           | M                                                                                                                                                            |
| **Validation**       | G2 — Traced registration path: `worker_stream.py:128` reads `worker_id` from client message; `registry.py:88-93` replaces existing registration with same ID |
| **Location**         | `src/api/websocket/worker_stream.py:128` / `src/api/workers/registry.py:88-93`                                                                               |

**Observation:** Workers choose their own `worker_id`. The registry explicitly replaces existing registrations with the same ID. All workers share the same API key — no per-worker identity.

**Analysis:** A malicious worker can impersonate another worker, hijack task assignments, displace legitimate workers (orphaning their connections), and steal task results. `WorkerProtocol.validate_register()` only checks field existence, not format or authorization.

#### Remediation options

**Option A — Server-assigned worker IDs (recommended for simplicity)**:

- Workers receive assigned ID in `registration_ack`
- **Strengths:** Eliminates impersonation entirely
- **Weaknesses:** Workers can't reconnect with persistent identity

**Option B — Worker ID allowlist or registration token**:

- **Strengths:** Per-worker auth; maintains worker-chosen IDs and meets worker reconnect requirement.
- **Weaknesses:** Requires token distribution infrastructure

**Recommendation:** Add format validation (alphanumeric + hyphens, max 64 chars) immediately.  Then implement Option B since worker reconnection is required.

---

### CR-027: `AuditLogger` and `WorkerMetrics` counters lack thread-safety

| Field                | Value                                                                                                                                                            |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Concurrency                                                                                                                                                      |
| **Secondary tags**   | race-condition, audit                                                                                                                                            |
| **Severity**         | S3                                                                                                                                                               |
| **Likelihood**       | Low                                                                                                                                                              |
| **Effort**           | S                                                                                                                                                                |
| **Validation**       | G4 — Read-modify-write pattern on plain dict without lock; other worker subsystem classes (`WorkerRegistry`, `WorkerCoordinator`) correctly use `threading.Lock` |
| **Location**         | `src/api/workers/audit.py:65,97-101`                                                                                                                             |

**Observation:** `AuditLogger._counter` and `WorkerMetrics._workers` use compound read-modify-write without locks. Practical impact is inaccurate counts, not security bypass.

**Recommendation:** Add `threading.Lock` to both, matching the pattern used throughout the workers subsystem.

---

### CR-028: TOCTOU gap in `_check_stale_workers` between snapshot and deregistration

| Field                | Value                                                                                                                                                  |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Concurrency                                                                                                                                            |
| **Secondary tags**   | TOCTOU, worker-lifecycle                                                                                                                               |
| **Severity**         | S2                                                                                                                                                     |
| **Likelihood**       | Low                                                                                                                                                    |
| **Effort**           | M                                                                                                                                                      |
| **Validation**       | G4 — Two separate lock acquisitions: `get_stale_workers()` (registry lock) then `deregister()` (registry lock); worker could heartbeat between the two |
| **Location**         | `src/api/workers/coordinator.py:367-381` — `_check_stale_workers()`                                                                                    |

**Observation:** Between `get_stale_workers()` snapshot and `deregister()`, a worker could send a heartbeat, making it no longer stale. The coordinator would deregister a live worker. The window is small (health check every 10s, heartbeat timeout 30s) but possible.

**Analysis:** Consequence is disconnecting a live worker and orphaning its WebSocket connection. Duplicate result detection prevents data corruption.

#### Remediation options

**Option A — Hold coordinator lock across entire loop body**:

- **Weaknesses:** Longer lock hold time

**Option B — Re-check staleness before deregistering (recommended)**:

- **Strengths:** Minimal lock contention; catches the race

**Recommendation:** Option B.

---

### CR-029: `InlineDataset` allows unbounded array sizes in training start request

| Field                | Value                                                                                                                             |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Input validation                                                                                                                  |
| **Secondary tags**   | DoS, memory                                                                                                                       |
| **Severity**         | S2                                                                                                                                |
| **Likelihood**       | Medium                                                                                                                            |
| **Effort**           | S                                                                                                                                 |
| **Validation**       | G3 — `train_x: List[List[float]]` with no size constraints; Pydantic deserialization + `torch.tensor()` allocate arbitrary memory |
| **Location**         | `src/api/models/training.py:17-23` / `src/api/routes/training.py:44-48`                                                           |

**Observation:** No constraints on list lengths. Even the 10MB body limit (with its chunked bypass per CR-024) allows ~300K floats which expand significantly in Python list form before tensor conversion.

**Recommendation:** Add `max_length` to outer list (e.g., 100000) and inner lists (e.g., 1000). Inline data is for small ad-hoc datasets; large datasets should use juniper-data service.

---

## 4. Phase 4 — Correctness and Numerical Behavior

### CR-040: Early stopping patience state not propagated between `grow_network` iterations

| Field                | Value                                                                                                                                                                                                                                   |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — algorithmic                                                                                                                                                                                                               |
| **Secondary tags**   | early-stopping, convergence                                                                                                                                                                                                             |
| **Severity**         | S1                                                                                                                                                                                                                                      |
| **Likelihood**       | High                                                                                                                                                                                                                                    |
| **Effort**           | S                                                                                                                                                                                                                                       |
| **Validation**       | G2 — `patience_counter` and `best_value_loss` are local variables in `grow_network` that are never updated from `validate_training_results` between iterations. Lines 3750-3751 show this was previously done but is now commented out. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:3722-3764` — `grow_network`                                                                                                                                                             |

**Observation:** In `grow_network`, `patience_counter` is always 0 and `best_value_loss` is always `float("inf")` on every iteration because the results from `validate_training` are never read back into the local variables.

**Analysis:** Patience-based early stopping can never trigger (except with `patience=0`, which is not the default of 50). The only working early stopping mechanisms are `check_hidden_units_max()` and `check_training_accuracy()`. The network will grow to `max_hidden_units` or `max_iterations`, wasting computation and risking overfitting.

#### Remediation options

**Option A — Restore the two-line update (recommended)**:

```python
patience_counter = validate_training_results.patience_counter
best_value_loss = validate_training_results.best_value_loss
```

- **Strengths:** Two-line fix; restores previously-working behavior (commented code proves intent)
- **Guardrails:** Regression test for early stopping

**Option B — Promote to instance variables**:

- **Strengths:** Eliminates fragile local-variable hand-off
- **Weaknesses:** Slightly more invasive

**Recommendation:** Option A immediatley. Add option B to long-term plan, with note to re-evaluate benefits later.

---

### CR-041: `CascadeCorrelationNetwork._roll_sequence_number` stores all discarded values in a list

| Field                | Value                                                                                                                                                                                         |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — resource consumption                                                                                                                                                            |
| **Secondary tags**   | memory, OOM                                                                                                                                                                                   |
| **Severity**         | S2                                                                                                                                                                                            |
| **Likelihood**       | Medium                                                                                                                                                                                        |
| **Effort**           | S                                                                                                                                                                                             |
| **Validation**       | G1 — `CandidateUnit._roll_sequence_number` already fixed (CASCOR-P1-008: capped loop, no list), but `CascadeCorrelationNetwork._roll_sequence_number` at line 1074 still uses the old pattern |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:1074`                                                                                                                                         |

**Observation:** The CandidateUnit version was fixed to avoid OOM but the identical method in CascadeCorrelationNetwork was not updated. Uses list comprehension: `discard = [generator(0, max_value) for _ in range(sequence)]`.

**Analysis:** Default `sequence_max_value` is 10, so in practice the list is tiny. But the fix should be mirrored for consistency and defense against configuration changes.

**Recommendation:** Mirror the CASCOR-P1-008 fix: replace list comprehension with capped for-loop.  Increase the `sequence_max_value` to 100.

---

### CR-042: `_create_optimizer` references undefined `OptimizerConfig` attributes — crashes on non-default optimizer types

| Field          | Value                                                                                                                                                                                                                                                         |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Pri cat**    | Correctness — crash                                                                                                                                                                                                                                           |
| **Sec tags**   | config, optimizer                                                                                                                                                                                                                                             |
| **Severity**   | S1                                                                                                                                                                                                                                                            |
| **Likelihood** | Low (default is Adam)                                                                                                                                                                                                                                         |
| **Effort**     | M                                                                                                                                                                                                                                                             |
| **Validation** | G3:`OptimizerConfig` flds:`optimizer_type`,`learning_rate`,`momentum`,`beta1`,`beta2`,`weight_decay`,`epsilon`.`_create_optimizer` refs:`config.rho`,`config.lr_decay`,`config.lambd`,`config.alpha`,`config.t0`,`config.max_iter`,etc. OptimizerConfig=>none |
| **Location**   | `src/cascade_correlation/cascade_correlation.py:2583-2684` — `_create_optimizer`                                                                                                                                                                              |

**Observation:** The optimizer factory handles Adadelta, Adafactor, Adagrad, ASGD, LBFGS, Muon, Rprop, etc. Each references config attributes that don't exist on `OptimizerConfig`. Selecting any non-default optimizer (anything other than Adam/SGD/RMSprop/AdamW) causes immediate `AttributeError`.

**Analysis:** Default path (Adam) works. The API and configuration layer allow setting arbitrary optimizer types. These optimizer entries exist in the factory as if they are supported.

#### Remediation options

**Option A — Add all required attributes to OptimizerConfig with sensible defaults (recommended)**:

- **Strengths:** Completes the contract

**Option B — Remove unsupported optimizer entries**:

- Keep only Adam, SGD, RMSprop, AdamW

**Option C — Add validation with clear error message**:

**Recommendation:** Option A because these optimizers are required to work to meet application requirements.

---

### CR-043: `validate_training` has no early stopping path when validation data is absent

| Field                | Value                                                                                                                                                                       |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — algorithmic                                                                                                                                                   |
| **Secondary tags**   | early-stopping                                                                                                                                                              |
| **Severity**         | S2                                                                                                                                                                          |
| **Likelihood**       | Medium                                                                                                                                                                      |
| **Effort**           | S                                                                                                                                                                           |
| **Validation**       | G2 — `validate_training` only enters early stopping logic inside `if x_val is not None and y_val is not None:`. The else-block (lines 4402-4423) is entirely commented out. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:4313-4435`                                                                                                                  |

**Observation:** Without validation data, `validate_training` returns `early_stop=False` unconditionally. The commented-out else-block previously provided training-loss-based early stopping.

**Analysis:** Combined with CR-040 (patience not propagated), early stopping is effectively broken in all modes. With validation data: patience never accumulates. Without validation data: not even attempted.

**Recommendation:** Uncomment the else-block that uses training loss for early stopping. Combine with CR-040 fix.

---

### CR-044: Hidden unit activation function not wrapped in `ActivationWithDerivative` after HDF5 deserialization

| Field                | Value                                                                                                                                                                       |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — snapshot round-trip                                                                                                                                           |
| **Secondary tags**   | serialization                                                                                                                                                               |
| **Severity**         | S2                                                                                                                                                                          |
| **Likelihood**       | Medium                                                                                                                                                                      |
| **Effort**           | S                                                                                                                                                                           |
| **Validation**       | G2 — `_load_hidden_units` at line 788-791 assigns from `activation_functions_dict` (raw PyTorch module, not wrapped). Runtime-created units use `ActivationWithDerivative`. |
| **Location**         | `src/snapshots/snapshot_serializer.py:786-792`                                                                                                                              |

**Observation:** Loaded hidden units get bare activation functions (e.g., `torch.nn.Tanh()`), while runtime units get `ActivationWithDerivative` wrappers. Forward pass works (both callable), but the type inconsistency means loaded units fail if the derivative path is needed.

**Recommendation:** Wrap resolved activation in `ActivationWithDerivative` during load.

---

### CR-045: `add_unit` initializes new hidden unit output weights with random values instead of zero

| Field                | Value                                                                                                                                                                                                                      |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — algorithmic                                                                                                                                                                                                  |
| **Secondary tags**   | weight-initialization                                                                                                                                                                                                      |
| **Severity**         | S2                                                                                                                                                                                                                         |
| **Likelihood**       | High                                                                                                                                                                                                                       |
| **Effort**           | S                                                                                                                                                                                                                          |
| **Validation**       | G2 — `add_unit` at line 3457 allocates with `torch.randn * 0.1`, then copies old weights at line 3468. New row retains random initialization. Standard CasCor algorithm (Fahlman & Lebiere 1990) uses zero initialization. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:3457-3471`                                                                                                                                                                 |

**Observation:** New hidden unit's output weights initialized with `torch.randn * 0.1` instead of zero. The output layer is retrained after each unit addition, but must first "unlearn" the random initialization before converging to useful weights.

**Analysis:** Introduces unnecessary variance. With limited `output_epochs`, may produce suboptimal output weights. Same pattern in `add_units_as_layer`.
    Note: Zero initialization is standard for CasCor and eliminates variance from the retraining starting point.
    However, the ability to experiment with non-standard output weight initialization methods is a key requirement for the hierarchical network architectures enhancement.

**Recommendation:** Add an `init_output_weights` flag with enumerated values including, but not necessarily limited to, the following: zero and random.
    The flag should be used to determine output node initialization behavior: using `torch.zeros` for the new row(s) vs `toch.randn * 0.1`.
    The flag should have defaults defined in appropriate constants class and local config files.
    Flag default should be accessed by juniper-cascor durring all network initialization locations in the code.
    The flag value should be stored in the cascor network object
    The flag should be exposed as an editable parameter in juniper-canopy, with values selectable from a dropdown list populated from the valid enumerated values list.
    Changes to the flag should be passed back to the cascor network and integrated into its settins.

---

### CR-046: `ActivationWithDerivative.__setstate__` silently falls back to ReLU for unrecognized activation names

| Field                | Value                                                                                                           |
|----------------------|-----------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — silent data corruption                                                                            |
| **Secondary tags**   | serialization, multiprocessing                                                                                  |
| **Severity**         | S2                                                                                                              |
| **Likelihood**       | Low                                                                                                             |
| **Effort**           | S                                                                                                               |
| **Validation**       | G3 — `__setstate__` at line 137 defaults to `torch.nn.ReLU()` if name lookup fails. No warning or error raised. |
| **Location**         | `src/utils/activation.py:129-137`                                                                               |

**Observation:** When unpickled via multiprocessing, if the activation name doesn't match any key in `ACTIVATION_MAP`, the function silently becomes ReLU. No diagnostic trail.

**Analysis:** Could produce incorrect training results if a custom activation's name changes or PyTorch renames an internal function.

**Recommendation:** Raise `ValueError` instead of silently falling back. A visible error is always better than silent behavior change.

---

### CR-047: `SharedTrainingMemory` shape descriptor only supports tensors up to 2D

| Field                | Value                                                                             |
|----------------------|-----------------------------------------------------------------------------------|
| **Primary category** | Correctness — data integrity                                                      |
| **Secondary tags**   | shared-memory                                                                     |
| **Severity**         | S3                                                                                |
| **Likelihood**       | Low                                                                               |
| **Effort**           | M                                                                                 |
| **Validation**       | G2 — Struct format stores only `shape_0` and `shape_1`. Current usage is 2D only. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:225-349`                          |

**Observation:** Latent defect — not an active bug. The descriptor format stores only two shape dimensions. 3D+ tensors would be silently truncated.

**Recommendation:** Immedidately, add validation check rejecting `ndim > 2` with a clear error message.
    - The capacity to allow `ndim > 2` should be documented as an enhancement and added to the development plan.  This feature is required for using some alternate datasets and for the hierarchical network enhancement.

---

### CR-048: `_save_hidden_units` reads activation function name incorrectly from `ActivationWithDerivative` wrapper

| Field                | Value                                                                                                                                                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — snapshot round-trip                                                                                                                                                                     |
| **Secondary tags**   | serialization, data-loss                                                                                                                                                                              |
| **Severity**         | S2                                                                                                                                                                                                    |
| **Likelihood**       | Medium                                                                                                                                                                                                |
| **Effort**           | S                                                                                                                                                                                                     |
| **Validation**       | G2 — Uses `getattr(unit["activation_fn"], "__name__", ...)` but `ActivationWithDerivative` has no `__name__`; name is stored as `_activation_name`. Falls back to `network.activation_function_name`. |
| **Location**         | `src/snapshots/snapshot_serializer.py:385-386`                                                                                                                                                        |

**Observation:** For the common case (all units same activation), the fallback produces the correct result. For heterogeneous activations per unit (supported by CasCor), per-unit activation is silently lost on save, replaced by the network default.

**Recommendation:** Change to `getattr(unit["activation_fn"], "_activation_name", network.activation_function_name)`.

---

### CR-049: `_accuracy` assumes one-hot encoded targets — broken for `output_size=1`

| Field                | Value                                                                        |
|----------------------|------------------------------------------------------------------------------|
| **Primary category** | Correctness — algorithmic                                                    |
| **Secondary tags**   | accuracy, metrics                                                            |
| **Severity**         | S3                                                                           |
| **Likelihood**       | Low                                                                          |
| **Effort**           | S                                                                            |
| **Validation**       | G2 — `argmax(dim=1)` on [N,1] tensor always returns 0, giving 100% accuracy. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:4683-4733`                   |

**Observation:** For binary classification with `output_size=1`, accuracy is always reported as 100%. The target accuracy check could trigger premature early stopping.

**Recommendation:** Add threshold-based accuracy for `output_size == 1`.

---

### CR-050: Duplicate forward-pass logic in `train_output_layer` vs `forward()`

| Field                | Value                                                                                                                                                                    |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Correctness — consistency                                                                                                                                                |
| **Secondary tags**   | code-duplication                                                                                                                                                         |
| **Severity**         | S3                                                                                                                                                                       |
| **Likelihood**       | High                                                                                                                                                                     |
| **Effort**           | M                                                                                                                                                                        |
| **Validation**       | G2 — `train_output_layer` uses `torch.cat` accumulation; `forward()` uses OPT-1 pre-allocated buffer. Both must produce identical results but are maintained separately. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:1580-1591`                                                                                                               |

**Observation:** Two separate implementations of hidden-unit output computation. A bug fix to one may not be applied to the other, causing silent training/inference divergence.

**Recommendation:** Extract shared `_compute_hidden_outputs(x)` method used by both.

---

## 5. Phase 5 — Performance and Scalability

### CR-060: Hidden unit forward pass recomputed redundantly every output training epoch

| Field                | Value                                                                                                                                                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Performance                                                                                                                                                                                                                     |
| **Secondary tags**   | hot-path, redundant-computation                                                                                                                                                                                                 |
| **Severity**         | S2                                                                                                                                                                                                                              |
| **Likelihood**       | High                                                                                                                                                                                                                            |
| **Effort**           | M                                                                                                                                                                                                                               |
| **Validation**       | G2 — `train_output_layer` inner loop recomputes hidden outputs every epoch; hidden weights are frozen so outputs are constant. Same loop duplicated in `add_unit`, `add_units_as_layer`, `forward`, `_prepare_candidate_input`. |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:1580-1591`                                                                                                                                                                      |

**Observation:** With N hidden units and E output epochs: N*E hidden-unit forward passes instead of N. Five independent copies of the hidden-output loop exist with subtle differences.

**Recommendation:** Extract `_compute_hidden_outputs(x)` using OPT-1 buffer pattern; hoist above epoch loop in `train_output_layer`.

---

### CR-061: Optimizer and `nn.Linear` recreated on every `train_output_layer` call

| Field                | Value                                                                   |
|----------------------|-------------------------------------------------------------------------|
| **Primary category** | Performance                                                             |
| **Secondary tags**   | object-allocation                                                       |
| **Severity**         | S3                                                                      |
| **Likelihood**       | High                                                                    |
| **Effort**           | S                                                                       |
| **Validation**       | G2 — Lines 1564-1574: `nn.Linear` and optimizer created unconditionally |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:1564-1574`              |

**Observation:** Adam momentum/velocity state is discarded each call. For CasCor, this may be intentional since the parameter space changes when hidden units are added.

**Recommendation:** Document as intentional. Add comment explaining optimizer reset is by design when architecture changes.

---

### CR-062: Excessive f-string tensor interpolation logging in hot paths

| Field                | Value                                                                                                                                                                                                                      |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Performance                                                                                                                                                                                                                |
| **Secondary tags**   | hot-path, logging                                                                                                                                                                                                          |
| **Severity**         | S2                                                                                                                                                                                                                         |
| **Likelihood**       | High                                                                                                                                                                                                                       |
| **Effort**           | M                                                                                                                                                                                                                          |
| **Validation**       | G1 — `conftest.py` lines 538-578 document this exact issue: `_NoOpLogger` created specifically because "f-string argument evaluation in filtered log calls: ~0.9s per fit() call from 1000+ tensor.**repr**() evaluations" |
| **Location**         | `src/candidate_unit/candidate_unit.py:560-634` — `train_detailed` inner loop                                                                                                                                               |

**Observation:** ~30 logger calls per epoch in candidate training, many with f-string tensor interpolations. Even at WARNING level, f-strings are evaluated before level check. For 16 candidates * 200 epochs = 96,000 string interpolations per training round.

**Recommendation:** Move constant-value logging (shapes, dtypes) before the loop. Convert per-epoch logging to lazy `%s` formatting.

---

### CR-063: `add_units_as_layer` stores numpy copies of weights in history

| Field                | Value                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------------|
| **Primary category** | Performance                                                                                      |
| **Secondary tags**   | memory-growth                                                                                    |
| **Severity**         | S3                                                                                               |
| **Likelihood**       | Medium                                                                                           |
| **Effort**           | S                                                                                                |
| **Validation**       | G2 — `.clone().detach().numpy()` per hidden unit; duplicates data already in `self.hidden_units` |
| **Location**         | `src/cascade_correlation/cascade_correlation.py:3569-3575`                                       |

**Observation:** Every hidden unit's weights stored as numpy arrays in history, duplicating data already in `self.hidden_units`.

**Recommendation:** Store only metadata (shape, correlation, index) in history.

---

### CR-064: Decision boundary computation runs synchronously in async handler, blocking event loop

| Field                | Value                                                                                                                                            |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Performance                                                                                                                                      |
| **Secondary tags**   | API, blocking                                                                                                                                    |
| **Severity**         | S2                                                                                                                                               |
| **Likelihood**       | Medium                                                                                                                                           |
| **Effort**           | S                                                                                                                                                |
| **Validation**       | G2 — `get_decision_boundary` creates meshgrid up to 200x200=40K points, runs forward pass, converts to lists, all while holding `_topology_lock` |
| **Location**         | `src/api/routes/decision_boundary.py:17-35` + `src/api/lifecycle/manager.py:786-825`                                                             |

**Observation:** At resolution=200: 40K-sample forward pass with numpy-to-tensor conversion + `.tolist()` conversion, all blocking the async event loop and holding `_topology_lock`.

**Recommendation:** Wrap in `asyncio.get_event_loop().run_in_executor(None, ...)`.

---

### CR-065: `TaskDistributor` dual-path execution is serial, not concurrent

| Field                | Value                                                                                           |
|----------------------|-------------------------------------------------------------------------------------------------|
| **Primary category** | Performance                                                                                     |
| **Secondary tags**   | parallelism                                                                                     |
| **Severity**         | S2                                                                                              |
| **Likelihood**       | Low                                                                                             |
| **Effort**           | M                                                                                               |
| **Validation**       | G2 — `distribute_and_collect()` at line 104-106: `local_fn` and `remote_fn` called sequentially |
| **Location**         | `src/parallelism/task_distributor.py:103-106`                                                   |

**Observation:** In dual-path mode (local + remote), total time is `local_time + remote_time` instead of `max(local_time, remote_time)`. Defeats the architectural purpose of dual-path distribution.

**Recommendation:** Use `concurrent.futures.ThreadPoolExecutor` to run both callables in parallel.

---

## 6. Phase 6 — Test Suite Quality

### CR-070: Integration tests rely on fixed `time.sleep()` for async training synchronization

| Field                | Value                                                                          |
|----------------------|--------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                   |
| **Secondary tags**   | flaky-tests                                                                    |
| **Severity**         | S2                                                                             |
| **Likelihood**       | High                                                                           |
| **Effort**           | M                                                                              |
| **Validation**       | G2 — `test_api_full_lifecycle.py` contains 15 `time.sleep()` calls (0.2s-1.0s) |
| **Location**         | `src/tests/integration/api/test_api_full_lifecycle.py:77-208`                  |

**Observation:** Tests will be flaky under CI load. The polling pattern in `test_create_train_wait_for_completion` is the right approach but not generalized.

**Recommendation:** Create `wait_for_state(client, expected_states, timeout=5.0, poll_interval=0.1)` helper.

---

### CR-071: Coverage tests bypass actual `fit()` method to avoid timeouts — false coverage confidence

| Field                | Value                                                                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                                                                          |
| **Secondary tags**   | false-confidence, coverage-gap                                                                                                        |
| **Severity**         | S1                                                                                                                                    |
| **Likelihood**       | High                                                                                                                                  |
| **Effort**           | M                                                                                                                                     |
| **Validation**       | G2 — Multiple tests nominally testing fit/grow_network actually call `train_output_layer` instead; comments confirm deliberate bypass |
| **Location**         | `src/tests/unit/test_cascade_correlation_coverage.py:130-228` / `src/tests/unit/test_training_workflow.py:44-57`                      |

**Observation:** Tests contributing to coverage metrics but not exercising the actual training flow: `fit() -> grow_network() -> train_candidates() -> _execute_candidate_training() -> _process_training_results()`.
    The `@pytest.mark.timeout(10)` decorators confirm deliberate simplification
    The core algorithm is only tested in integration tests marked `@pytest.mark.slow` (skipped by default).

**Analysis:** The most critical code path in the application has no unit-level coverage in standard CI runs.

#### Remediation options

**Option A — Create "fast fit" test (recommended)**:

- Use ultra-minimal parameters: `pool_size=1, candidate_epochs=1, output_epochs=1, max_hidden_units=1`
- **Strengths:** Full path coverage in seconds

**Option B — Use `--fast-slow` infrastructure from conftest.py**

**Recommendation:** Both Option A and Option B.
    Option A will allow accurate, critical code path coverage checks with non-limiting runtimes.
    Option B will allow the more rigorous checks needed for this application critical code path.

---

### CR-072: `force_sequential_training` autouse fixture masks all multiprocessing bugs

| Field                | Value                                                                                                                                          |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                                                                                   |
| **Secondary tags**   | coverage-gap                                                                                                                                   |
| **Severity**         | S2                                                                                                                                             |
| **Likelihood**       | Medium                                                                                                                                         |
| **Effort**           | M                                                                                                                                              |
| **Validation**       | G2 — `autouse=True` fixture monkeypatches `_calculate_optimal_process_count` to always return 1. Parallel training path never exercised in CI. |
| **Location**         | `src/tests/conftest.py:510-528`                                                                                                                |

**Observation:** The entire parallel training path (`_execute_parallel_training`, `_ensure_worker_pool`, `_collect_worker_results`, `_drain_stale_results`, SharedTrainingMemory OPT-5, task distributor) is never tested in standard runs.
    Comment explains "parallel path spawns multiprocessing.Process workers that fail with BrokenPipeError in test environments."

**Recommendation:** Create `test_parallel_training.py` with `@pytest.mark.slow` that overrides the fixture.
    Also add unit tests that mock multiprocessing primitives for fast CI coverage.

---

### CR-073: `_NoOpLogger` session fixture masks logging-related bugs in production code

| Field                | Value                                                                                 |
|----------------------|---------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                          |
| **Secondary tags**   | test-infra                                                                            |
| **Severity**         | S2                                                                                    |
| **Likelihood**       | Low                                                                                   |
| **Effort**           | S                                                                                     |
| **Validation**       | G2 — Session-scoped `autouse=True` fixture replaces entire logging system with no-ops |
| **Location**         | `src/tests/conftest.py:538-674`                                                       |

**Observation:** No test exercises actual logging initialization or verifies log message correctness. If a production log call references a nonexistent attribute, no test catches it.

**Recommendation:** Add a single smoke test running `fit()` with real logger at WARNING level.

---

### CR-074: Tests named for `grow_network` testing actually bypass it entirely

| Field                | Value                                                                                                                  |
|----------------------|------------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                                                           |
| **Secondary tags**   | misleading-tests                                                                                                       |
| **Severity**         | S2                                                                                                                     |
| **Likelihood**       | High                                                                                                                   |
| **Effort**           | S                                                                                                                      |
| **Validation**       | G4 — `test_grow_network_adds_hidden_unit` manually appends a dict to `hidden_units` list; never calls `grow_network()` |
| **Location**         | `src/tests/unit/test_cascade_correlation_coverage.py:136-158`                                                          |

**Observation:** Tests verify that Python `list.append()` works, not that `grow_network()` correctly trains candidates, selects the best, adds it, and retrains.

**Recommendation:** Rewrite to actually call `grow_network()` with ultra-minimal parameters.

---

### CR-075: Performance test baselines record data but never assert against regression thresholds

| Field                | Value                                                                                                            |
|----------------------|------------------------------------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                                                     |
| **Secondary tags**   | missing-assertions                                                                                               |
| **Severity**         | S3                                                                                                               |
| **Likelihood**       | Medium                                                                                                           |
| **Effort**           | M                                                                                                                |
| **Validation**       | G2 — Memory tests record RSS delta but have no assertions. `save_baseline()` appends to JSON with no comparison. |
| **Location**         | `src/tests/performance/test_baselines.py:277-324`                                                                |

**Observation:** Performance test infrastructure is well-designed but needs assertions to be actionable.

**Recommendation:** Add threshold assertions to memory tests; use pytest-benchmark `--benchmark-compare` in CI.

---

### CR-076: Triple random seeding in `conftest.py` creates confusing test infrastructure

| Field                | Value                                                                                       |
|----------------------|---------------------------------------------------------------------------------------------|
| **Primary category** | Test quality                                                                                |
| **Secondary tags**   | test-infra                                                                                  |
| **Severity**         | S3                                                                                          |
| **Likelihood**       | Low                                                                                         |
| **Effort**           | S                                                                                           |
| **Validation**       | G2 — Seeds set in `pytest_configure`, per-fixture, and `reset_random_seeds` autouse fixture |
| **Location**         | `src/tests/conftest.py:108-109,229,720-724`                                                 |

**Observation:** Three seeding mechanisms makes it hard to reason about determinism. Functionally correct but confusing.

**Recommendation:** Remove per-fixture `torch.manual_seed(42)` calls; keep `reset_random_seeds` as single source of truth.

---

## 7. Phase 7 — Synthesis and Remediation Roadmap

### 7.1 Group Recommendations

| Group                                     | Issues                         | Recommended Sequencing                                                                                                                                                                                     |
|-------------------------------------------|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Core correct (CRIT)**                   | CR-040,042,043,046,048,049     | Fix before prod training. CR-040(2-line fix) + CR-043(uncomment) fix early stopping. CR-046(raise not fallback) is small. CR-042 + CR-048 finish optimizer/serializer contracts.                           |
| **Output weight init (cross-project)**    | CR-045                         | Add configurable `init_output_weights` flag with enumerated values (zero, random, etc.). Expose in canopy as dropdown. Requires constants, config, network, canopy UI, and canopy→cascor param flow.       |
| **Snap rnd-trip fidelity**                | CR-044,048,046                 | Bundle into single PR. All affect save/load correctness. Test with round-trip assertion.                                                                                                                   |
| **Training limits (CRIT, cross-project)** | CR-006                         | Implement `max_epochs` and `max_iterations`, e2e as separate first-class fields. Coord PRs:                                                                                                                |
|                                           |                                | -- 1. cascor (constants, config, network, API, TrainingState, lifecycle)                                                                                                                                   |
|                                           |                                | -- 2. canopy (param map, set_params forwarding). Large effort — dedicated work item.                                                                                                                       |
| **WS control channel**                    | CR-008                         | Implement `set_params` command immediately. Critical functionality expected by users; required for juniper-canopy integration.                                                                             |
| **Lifecycle state mach**                  | CR-007                         | Auto-reset from terminal states. Affects downstream consumers (juniper-canopy).                                                                                                                            |
| **API sec hardening**                     | CR-010,023,024,026,029         | Prioritize CR-026 (worker ID format validation + registration tokens, S1). Then CR-023 (param whitelist) + CR-029 (inline data bounds) + CR-024 (chunked bypass). CR-010 (shared WS auth) DRY improvement. |
| **Wrkr subsys complete**                  | CR-009,021,027,028             | Begin CR-009 (incremental integration Phase 4 sec mod via feature flags). CR-021 (add Lock to singletons, required by CR-009/CR-010). CR-027 (add locks) and CR-028 (re-check staleness) are small fixes.  |
| **Observability**                         | CR-022                         | Quick fix: normalize Prometheus labels.                                                                                                                                                                    |
| **Performance**                           | CR-060,062,064,065             | CR-060 (shared hidden-output method) and CR-062 (lazy logging) have the highest impact. CR-064 (async decision boundary) is a quick fix. CR-065 (parallel task distributor) is lower priority.             |
| **Test qual foundation**                  | CR-071,072,073,074,070         | CR-071 (fast fit test, both Options A and B) is the highest-value single change: adds real coverage for the critical path. CR-074 (rewrite misleading tests) and CR-072 (parallel training tests) follow.  |
| **Tool align** (PH1)                      | CR-001,002,003                 | Fix before large refactors to improve signal from mypy/flake8.                                                                                                                                             |
| **Low-pri cleanup**                       | CR-041,047,050,061,063,075,076 | Address opportunistically or bundle with related work. CR-041 includes increasing `sequence_max_value` to 100. CR-047 includes documenting ndim > 2 as a planned enhancement.                              |

### 7.2 Recommended Priority Order

**Tier 1 — Fix before next production training run:**

| # | Finding | Fix Size          | Impact                                                                                                                                                                                   |
|---|---------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | CR-040  | 2 lines           | Restores early stopping                                                                                                                                                                  |
| 2 | CR-043  | Uncomment block   | Enables early stopping without validation data                                                                                                                                           |
| 3 | CR-045  | M (cross-project) | Add configurable `init_output_weights` flag (zero, random, etc.) with canopy dropdown; default zero per CasCor algorithm                                                                 |
| 4 | CR-046  | ~3 lines          | Raise instead of silent ReLU fallback                                                                                                                                                    |
| 5 | CR-007  | ~15 lines         | Auto-reset prevents state machine desynchronization                                                                                                                                      |
| 6 | CR-006  | L (cross-project) | Implement `max_epochs` and `max_iterations` as separate first-class fields end-to-end (cascor constants → config → network → API → TrainingState → canopy param map → canopy set_params) |

**Tier 2 — Fix before next release:**

| #  | Finding | Fix Size | Impact                                                                        |
|----|---------|----------|-------------------------------------------------------------------------------|
| 7  | CR-008  | S        | Implement `set_params` in WS control stream — critical canopy functionality   |
| 8  | CR-042  | M        | Complete OptimizerConfig for all registered optimizer types                   |
| 9  | CR-048  | 1 line   | Correct activation name extraction for snapshots                              |
| 10 | CR-044  | ~3 lines | Wrap activation after HDF5 load                                               |
| 11 | CR-026  | M        | Worker ID format validation + registration tokens for reconnection            |
| 12 | CR-071  | M        | Fast fit test (Option A) + fast-slow infrastructure (Option B) for core path  |
| 13 | CR-023  | S        | Whitelist training start params (quick fix); typed Pydantic model (follow-up) |
| 14 | CR-029  | S        | Bound inline dataset arrays                                                   |

**Tier 3 — Address in upcoming sprints:**

| #  | Finding | Fix Size | Impact                                                                          |
|----|---------|----------|---------------------------------------------------------------------------------|
| 15 | CR-009  | L        | Begin incremental integration of worker security modules via feature flags      |
| 16 | CR-021  | S        | Add thread-safe locking to global auth singletons (prerequisite for CR-009/010) |
| 17 | CR-060  | M        | Extract shared hidden-output computation                                        |
| 18 | CR-062  | M        | Lazy logging in hot paths                                                       |
| 19 | CR-064  | S        | Async decision boundary                                                         |
| 20 | CR-010  | M        | Shared WS auth utility                                                          |
| 21 | CR-022  | S        | Prometheus label normalization                                                  |
| 22 | CR-024  | S        | Chunked encoding body limit                                                     |
| 23 | CR-025  | S        | Async lock for WebSocketManager                                                 |
| 24 | CR-072  | M        | Parallel training test coverage                                                 |
| 25 | CR-070  | M        | Polling-based integration tests                                                 |

**Tier 4 — Opportunistic / low-priority:**

CR-027, CR-028, CR-041, CR-047, CR-049, CR-050, CR-061, CR-063, CR-073, CR-074, CR-075, CR-076

### 7.3 Traceability Matrix

| ID     | Phase | Theme            | Severity | Suggested PR Title                                                                                  | Release Note                     |
|--------|-------|------------------|----------|-----------------------------------------------------------------------------------------------------|----------------------------------|
| CR-006 | 2     | Training limits  | S1       | Implement max_epochs and max_iterations as separate first-class fields end-to-end (cascor + canopy) | Bugfix / Feature (cross-project) |
| CR-007 | 2     | Lifecycle        | S1       | Auto-reset state machine from terminal states on training start                                     | Bugfix                           |
| CR-008 | 2     | API contract     | S2       | Implement set_params command in WebSocket control stream                                            | Feature (critical canopy req)    |
| CR-009 | 2     | Security         | S2       | Incrementally integrate worker security modules via feature flags                                   | Security                         |
| CR-010 | 2     | Security         | S2       | Extract shared WebSocket auth utility                                                               | Security                         |
| CR-021 | 3     | Concurrency      | S3       | Add thread-safe locking to global auth singletons (required by CR-009/CR-010)                       | Reliability                      |
| CR-022 | 3     | Observability    | S2       | Normalize Prometheus endpoint labels to route templates                                             | Bugfix                           |
| CR-023 | 3     | Input validation | S2       | Whitelist allowed params in training start request                                                  | Security                         |
| CR-024 | 3     | Security         | S2       | Add chunked-encoding-aware body size limiting                                                       | Security                         |
| CR-025 | 3     | Concurrency      | S2       | Add asyncio.Lock to WebSocketManager connection state                                               | Reliability                      |
| CR-026 | 3     | Security         | S1       | Worker ID format validation + registration tokens for reconnection                                  | Security                         |
| CR-027 | 3     | Concurrency      | S3       | Add threading.Lock to AuditLogger and WorkerMetrics                                                 | Reliability                      |
| CR-028 | 3     | Concurrency      | S2       | Re-check worker staleness before deregistration                                                     | Reliability                      |
| CR-029 | 3     | Input validation | S2       | Add max_length constraints to InlineDataset arrays                                                  | Security                         |
| CR-040 | 4     | Core ML          | S1       | Restore early stopping patience propagation in grow_network                                         | Bugfix (critical)                |
| CR-041 | 4     | Core ML          | S2       | Mirror CASCOR-P1-008 roll_sequence fix in network class; increase sequence_max_value to 100         | Bugfix                           |
| CR-042 | 4     | Core ML          | S1       | Complete OptimizerConfig for all registered optimizer types                                         | Bugfix                           |
| CR-043 | 4     | Core ML          | S2       | Restore training-loss early stopping when no validation data                                        | Bugfix                           |
| CR-044 | 4     | Snapshots        | S2       | Wrap activation in ActivationWithDerivative after HDF5 load                                         | Bugfix                           |
| CR-045 | 4     | Core ML          | S2       | Add configurable `init_output_weights` flag (zero, random, etc.) with canopy dropdown               | Feature (cross-project)          |
| CR-046 | 4     | Core ML          | S2       | Raise ValueError on unrecognized activation deserialization                                         | Bugfix                           |
| CR-047 | 4     | Core ML          | S3       | Validate SharedTrainingMemory rejects ndim > 2; document ndim > 2 support as planned enhancement    | Reliability / Enhancement        |
| CR-048 | 4     | Snapshots        | S2       | Fix activation name extraction in _save_hidden_units                                                | Bugfix                           |
| CR-049 | 4     | Core ML          | S3       | Support output_size=1 in accuracy computation                                                       | Enhancement                      |
| CR-050 | 4     | Core ML          | S3       | Extract shared hidden-output computation method                                                     | Refactor                         |
| CR-060 | 5     | Performance      | S2       | Hoist hidden-output computation above output training loop                                          | Performance                      |
| CR-061 | 5     | Performance      | S3       | Document intentional optimizer reset in train_output_layer                                          | Docs                             |
| CR-062 | 5     | Performance      | S2       | Convert hot-path logging to lazy evaluation                                                         | Performance                      |
| CR-063 | 5     | Performance      | S3       | Store metadata only (not weight copies) in unit history                                             | Performance                      |
| CR-064 | 5     | Performance      | S2       | Run decision boundary computation in thread pool executor                                           | Performance                      |
| CR-065 | 5     | Performance      | S2       | Parallelize local/remote task execution in TaskDistributor                                          | Performance                      |
| CR-070 | 6     | Tests            | S2       | Replace time.sleep with polling helper in integration tests                                         | Tests                            |
| CR-071 | 6     | Tests            | S1       | Add fast-fit unit test (Option A) + fast-slow infrastructure (Option B) for full training pipeline  | Tests                            |
| CR-072 | 6     | Tests            | S2       | Add multiprocessing integration tests with slow marker                                              | Tests                            |
| CR-073 | 6     | Tests            | S2       | Add smoke test with real logger for production logging paths                                        | Tests                            |
| CR-074 | 6     | Tests            | S2       | Rewrite grow_network tests to call actual grow_network                                              | Tests                            |
| CR-075 | 6     | Tests            | S3       | Add regression assertions to performance baselines                                                  | Tests                            |
| CR-076 | 6     | Tests            | S3       | Consolidate random seeding to single autouse fixture                                                | Tests                            |

### 7.4 Cross-cutting Guardrails

- Any change touching `snapshots/` or wire protocol requires **juniper-cascor-client** and **juniper-canopy** smoke tests per ecosystem AGENTS.md
- Core ML fixes (CR-040, CR-043, CR-045) should be validated against the two-spiral benchmark to confirm training still converges correctly
- Security fixes (CR-026, CR-023, CR-029) should be tested with the existing WebSocket and worker test suites
- The Phase 1 tooling fixes (CR-001 mypy, CR-002 flake8) should be completed before the larger refactors (CR-050, CR-060) to ensure linting signal is accurate

### 7.5 Program Exit Criteria

| # | Criterion                                                                   | Status                                       |
|---|-----------------------------------------------------------------------------|----------------------------------------------|
| 1 | Each taxonomy dimension has validated exemplar or "none found after search" | **Met** — exemplars across all 6 dimensions  |
| 2 | Every accepted finding has Issue Record with options                        | **Met** — 38 findings, CR-006 through CR-076 |
| 3 | Prioritized backlog exists                                                  | **Met** — §7.1-§7.3                          |
| 4 | CI baseline green or waived                                                 | **Green** — unit test run passed at baseline |
| 5 | Group recommendations documented                                            | **Met** — §7.1                               |
| 6 | Traceability matrix complete                                                | **Met** — §7.3                               |

**Sign-off:** Phases 2-7 complete.
The 6 S1 findings (CR-006, CR-007, CR-026, CR-040, CR-042, CR-071) should be prioritized for immediate remediation.
The core ML cluster (CR-040, CR-042, CR-043, CR-045, CR-046, CR-048) and the training limits data flow (CR-006) are the highest-impact groups — early stopping is effectively non-functional, snapshot fidelity has gaps, and the max_epochs/max_iterations data path is broken across cascor and canopy.

---

## Document History

| Date       | Change                                                                                                                              |
|------------|-------------------------------------------------------------------------------------------------------------------------------------|
| 2026-04-04 | Initial Phase 0-1 findings (CR-001 through CR-005) in companion plan document                                                       |
| 2026-04-04 | Phases 2-7 complete: 38 findings (CR-006 through CR-076), group recommendations, traceability matrix, exit criteria                 |
| 2026-04-04 | Owner rev: CR-006 (training limits data flow, S2→S1), CR-008 (implement set_params), CR-009 (begin integration),                    |
|            | CR-021 (add Lock), CR-026 (registration tokens), CR-041 (increase seq max), CR-045 (configurable init flag),                        |
|            | CR-047 (ndim enhancement plan), CR-071 (both options). Fixed finding cnt (33→38), sev cnts, and propagated changes: summary section |
