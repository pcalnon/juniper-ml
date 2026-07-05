# Juniper Ecosystem — Comprehensive Code Audit

**Date**: 2026-04-17
**Scope**: All 8 active Juniper repositories
**Type**: Read-only analysis — no code changes made
**Status**: Current

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [1. Critical Findings](#1-critical-findings)
  - [1.1 WebSocket Topology Broadcast Gap](#11-websocket-topology-broadcast-gap)
  - [1.2 Network Topology Visualization Issues](#12-network-topology-visualization-issues)
  - [1.3 Metaparameter Wiring Gaps](#13-metaparameter-wiring-gaps)
  - [1.4 Shared Memory and Multiprocessing Issues](#14-shared-memory-and-multiprocessing-issues)
  - [1.5 Security Concerns](#15-security-concerns)
- [2. Per-Repository Findings](#2-per-repository-findings)
  - [2.1 juniper-cascor](#21-juniper-cascor)
  - [2.2 juniper-canopy](#22-juniper-canopy)
  - [2.3 juniper-cascor-client](#23-juniper-cascor-client)
  - [2.4 juniper-cascor-worker](#24-juniper-cascor-worker)
  - [2.5 juniper-data](#25-juniper-data)
  - [2.6 juniper-data-client](#26-juniper-data-client)
  - [2.7 juniper-deploy](#27-juniper-deploy)
  - [2.8 juniper-ml](#28-juniper-ml)
- [3. Cross-Repository Issues](#3-cross-repository-issues)
- [4. Performance Analysis](#4-performance-analysis)
- [5. Architectural Assessment](#5-architectural-assessment)
- [6. Risk Assessment and Guardrails](#6-risk-assessment-and-guardrails)
- [7. Recommendations](#7-recommendations)

---

## Executive Summary

This audit examines the entire Juniper ecosystem across 8 active repositories. The codebase demonstrates strong engineering fundamentals — consistent CI/CD pipelines, comprehensive test coverage, well-structured AGENTS.md files, and a clear architectural vision. The core cascade correlation implementation is sound and includes thoughtful optimizations (shared memory, pre-allocated buffers, hoisted computations).

However, several significant issues were identified, primarily in the integration layer between juniper-cascor and juniper-canopy:

| Category             | Critical | High  | Medium | Low    | Info  |
|----------------------|----------|-------|--------|--------|-------|
| WebSocket/Topology   | 1        | 2     | 3      | 2      | 2     |
| Metaparameter Wiring | 0        | 1     | 3      | 1      | 0     |
| Shared Memory/MP     | 0        | 0     | 3      | 2      | 1     |
| Security             | 0        | 1     | 4      | 2      | 0     |
| Performance          | 0        | 0     | 4      | 3      | 1     |
| Code Quality         | 0        | 0     | 5      | 8      | 3     |
| Cross-Repo Alignment | 0        | 1     | 3      | 2      | 0     |
| **Total**            | **1**    | **5** | **25** | **20** | **7** |

---

## 1. Critical Findings

### 1.1 WebSocket Topology Broadcast Gap

**Severity**: CRITICAL
**Repositories**: juniper-cascor, juniper-canopy
**Files**: `juniper-cascor/src/api/websocket/messages.py`, `juniper-cascor/src/api/lifecycle/manager.py`, `juniper-cascor/src/api/lifecycle/monitor.py`

#### The Problem

The `create_topology_message()` builder exists in `messages.py` (L72–79) but is **never called anywhere in the codebase**. The `TrainingMonitor.callbacks` dictionary includes a `"topology_change"` key (L165 of `monitor.py`) but **no callback is ever registered for it**. The `TrainingLifecycleManager._install_monitoring_hooks()` registers callbacks for `epoch_end`, `cascade_add`, `training_start`, `training_end`, and `candidate_progress` — but **not** for `topology_change`.

#### Impact

When the cascade correlation network adds a hidden unit, no WebSocket message is broadcast to connected clients. The `cascade_add` message (which IS broadcast) includes `hidden_unit_index`, `correlation`, and `total_hidden_units` — but NOT the full topology data (nodes, connections, weights). Clients must poll `GET /v1/network/topology` to discover structural changes.

#### Supporting Code

```python
# messages.py L72-79 — Builder exists but is never called
def create_topology_message(topology_data: dict, seq: int | None = None) -> dict:
    return _build_envelope("topology", topology_data, seq=seq)

# monitor.py L165 — Callback slot exists but is never populated
self.callbacks = {
    "epoch_end": [], "cascade_add": [], "topology_change": [],  # ← dead slot
    "training_start": [], "training_end": [], "candidate_progress": [],
}

# manager.py L236-270 — _install_monitoring_hooks registers everything EXCEPT topology_change
```

#### Canopy Workaround

Canopy compensates by polling `/api/topology` on a 5-second interval (`SLOW_UPDATE_INTERVAL_MS = 5000` in `dashboard_manager.py`). The WS bridge can receive topology pushes if they were sent, but since cascor never sends them, canopy always falls back to REST polling. This creates a 0–5 second lag when hidden units are added.

---

### 1.2 Network Topology Visualization Issues

**Severity**: HIGH
**Repositories**: juniper-cascor, juniper-canopy

#### 1.2.1 Initial Output Node Count

**Status**: ✅ CORRECT — Not a bug

The initial network correctly shows a single output node.
In canopy's `DemoBackend.get_network_topology()` (demo_backend.py L140–188), output nodes are created using `network.output_size` which defaults to 1 for the two-spiral problem.
In service mode, the cascor REST response includes `output_size` from the live network.
The concern about "two output nodes" may stem from the `output_weights` matrix shape — for a network with `input_size=2` and 0 hidden units, `output_weights` has shape `(2, 1)`, where the `2` represents input-to-output connections (one weight per input), not two output nodes.

**Root Cause of Confusion**:
The `output_weights` array in the topology REST response has shape `(input_size + n_hidden, output_size)`.
If a client renders one node per row of this matrix, it would incorrectly show `input_size` "output" nodes.
The matrix should be interpreted as weights FROM each source node TO each output node.

#### 1.2.2 Topology Not Updating After Hidden Node Addition

**Status**: ⚠️ PARTIALLY WORKING — Works via polling, not push

As described in §1.1, topology changes are not broadcast via WebSocket.
Canopy's topology visualization DOES update, but only when the polling interval (5s) triggers a REST fetch.
The `NetworkVisualizer.update_network_graph()` callback (L298–477 of `dashboard_manager.py`) detects hidden unit count changes between consecutive metrics snapshots and triggers a redraw with a pulsing highlight animation.

**Gap**: During rapid cascade additions (e.g., 2+ hidden units in < 5 seconds), intermediate states may be missed. The topology will jump from N hidden units to N+2 without showing the N+1 state.

#### 1.2.3 Weight Changes Not Displayed During Training

**Status**: ⚠️ ARCHITECTURAL LIMITATION

The topology visualization has a hash-based skip mechanism (network_visualizer.py L391–398) that uses only structural counts (`input_units`, `hidden_units`, `output_units`, `len(connections)`) — NOT weight values. This means **weight changes during training do not trigger a graph redraw**. The weights are available in the topology data (each connection has a `weight` field), and the "Show Weights" checkbox enables weight labels on edges, but the graph only redraws when the structure changes.

Additionally, the 3D topology view (L1186–1354) ignores the `show_weights` parameter entirely — weight labels are only supported in 2D mode.

**Supporting Code**:

```python
# network_visualizer.py L391-398 — hash ignores weight values
def _topology_hash(self, topology_data):
    return hash((
        topology_data.get("input_units", 0),
        topology_data.get("hidden_units", 0),
        topology_data.get("output_units", 0),
        len(topology_data.get("connections", [])),
    ))
    # Weight values are NOT in the hash — weight-only changes don't trigger redraw
```

---

### 1.3 Metaparameter Wiring Gaps

**Severity**: HIGH
**Repositories**: juniper-canopy, juniper-cascor

#### 1.3.1 End-to-End Flow

The metaparameter update flow works through these stages:

```bash
UI Sidebar Input → track_param_changes callback (dirty detection)
  → Apply Button click → apply_parameters callback
    → REST POST /api/train/set_params  OR  WS /ws/control set_params command
      → main.py → backend.apply_params()
        → Demo: DemoMode.apply_params() sets attributes directly
        → Service: CascorServiceAdapter → cascor REST PATCH /v1/training/params
          → TrainingLifecycleManager.update_params()
            → setattr(self.network, key, value) under _training_lock
```

**What works end-to-end**: `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `epochs_max`, `max_iterations`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`, `candidate_epochs`

**What is broken/missing**:

| Parameter                    | Issue                                                                                                                                                                                                                                                        |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `init_output_weights`        | Defined in REST model but **no corresponding UI control** exists in canopy sidebar                                                                                                                                                                           |
| `modifiable_during_training` | Flag defined in `TrainingParamConfig` (settings.py L53) but **never checked** — all params can be changed mid-training without validation                                                                                                                    |
| Service mode defaults        | In service mode, canopy populates parameter values with **internal defaults** first, only overwriting with values from `get_canopy_params()`. If cascor doesn't expose a parameter, canopy shows the default — **the UI lies about the actual cascor state** |

#### 1.3.2 Message Format Inconsistency (cascor-client)

The `CascorControlStream.command()` method (ws_client.py L231–240) has an inconsistency with `set_params()`:

- `set_params()` sends: `{"type": "command", "command": "set_params", "command_id": "...", "params": {...}}`
- `command()` without recv task sends: `{"command": "start", "params": {...}}` — **no `type` field**
- `command()` with recv task sends: `{"command": "start", "command_id": "...", "params": {...}}` — **no `type` field**

If the cascor server's control stream handler dispatches by `message["type"]`, commands sent via `command()` will fail silently.

---

### 1.4 Shared Memory and Multiprocessing Issues

**Severity**: MEDIUM
**Repository**: juniper-cascor

#### 1.4.1 Shared Memory Block Leaks

`SharedTrainingMemory` (cascade_correlation.py L227–388) creates named POSIX shared memory blocks in `/dev/shm` with names like `juniper_train_{uuid}`. The `track=False` parameter (L326) disables Python's resource tracker to prevent double-unlink, but this means:

- If the creator process crashes without calling `unlink()`, the block persists in `/dev/shm` until system reboot or manual cleanup
- The `atexit` handler (L762) provides cleanup on normal exit, but is not called on SIGKILL or OOM-kill
- Orphaned blocks from crashed training sessions accumulate over time

**Recommendation**: Add a startup sweep that removes stale `juniper_train_*` blocks from `/dev/shm`.

#### 1.4.2 SharedMemory `FileExistsError`

`SharedMemory(create=True)` at L277 will raise `FileExistsError` if a block with the same name already exists. The UUID suffix mitigates collisions between concurrent sessions, but does not protect against orphaned blocks from previous crashed sessions that happened to generate the same UUID (extremely unlikely but theoretically possible).

#### 1.4.3 Worker Pool Busy-Wait

`_collect_worker_results` (L2018) uses a `while` loop with `time.sleep(sleepytime)` to poll the result queue. This is a CPU-consuming busy-wait pattern. `queue.qsize()` is used for early exit, but `qsize()` raises `NotImplementedError` on macOS.

#### 1.4.4 BLAS Thread Contention

`torch.set_num_threads(parent_thread_count)` in `_init_multiprocessing` (L782) is a **global** setting affecting all PyTorch operations in the process, including the API server's forward passes for decision boundary computation. If multiprocessing reduces this, decision boundary requests become slower.

---

### 1.5 Security Concerns

**Severity**: HIGH (aggregate)
**Repositories**: juniper-data, juniper-deploy

#### 1.5.1 Non-Constant-Time API Key Comparison

`juniper-data/juniper_data/api/security.py` L59:

```python
api_key in self._api_keys
```

This uses Python's standard `in` operator on a set, which is NOT constant-time for string comparison. An attacker can use timing side-channel attacks to determine API keys character by character. Should use `hmac.compare_digest()`.

#### 1.5.2 Unbounded Rate Limiter Memory

`juniper-data/juniper_data/api/security.py` L116–117: The `_counters` dictionary (`defaultdict`) grows without bound as new client IPs connect. No eviction or size limit exists. Under sustained traffic from many unique IPs (or IP spoofing), this is a memory leak and DoS vector.

#### 1.5.3 Docker Port Binding

`juniper-deploy/docker-compose.yml`: juniper-cascor (L129) and all juniper-canopy variants (L298, L349, L386) bind ports to `0.0.0.0` (all interfaces) instead of `127.0.0.1`. Compare to juniper-data (L89) which correctly uses `127.0.0.1:`. This exposes cascor and canopy services to the entire network.

```yaml
# CURRENT (insecure)
- "${CASCOR_HOST_PORT:-8201}:${CASCOR_PORT:-8200}"   # binds to 0.0.0.0

# CORRECT (loopback only)
- "127.0.0.1:${CASCOR_HOST_PORT:-8201}:${CASCOR_PORT:-8200}"
```

#### 1.5.4 Body Size Limit Bypass

`juniper-data/juniper_data/api/middleware.py` L81: `RequestBodyLimitMiddleware` checks only the `Content-Length` header. A malicious client can omit this header and stream an arbitrarily large body.

---

## 2. Per-Repository Findings

### 2.1 juniper-cascor

| ID    | Severity     | File                              | Line(s) | Finding                                                                                                                   |
|-------|--------------|-----------------------------------|---------|---------------------------------------------------------------------------------------------------------------------------|
| CC-01 | **Critical** | `api/websocket/messages.py`       | 72–79   | `create_topology_message()` exists but is never called — topology changes not broadcast via WS                            |
| CC-02 | **High**     | `api/lifecycle/manager.py`        | 757–782 | `get_topology()` returns no `connections` field — clients must infer cascade connectivity from weight dimensions          |
| CC-03 | **High**     | `api/lifecycle/manager.py`        | 767     | `output_weights` matrix returned without explicit node-to-weight mapping — clients must reconstruct                       |
| CC-04 | **Medium**   | `api/lifecycle/manager.py`        | 776     | `unit.get("activation_fn", torch.sigmoid).__name__` returns `"ActivationWithDerivative"` not the underlying function name |
| CC-05 | **Medium**   | `api/lifecycle/manager.py`        | 427–429 | After `grow_network`, `on_cascade_add` broadcasts `correlation=0.0` — actual candidate correlation is lost                |
| CC-06 | **Medium**   | `api/lifecycle/state_machine.py`  | 216–234 | State names inconsistent: state machine returns UPPERCASE, `TrainingState` returns title-case                             |
| CC-07 | **Medium**   | `api/websocket/worker_stream.py`  | 193     | Worker message loop has no heartbeat timeout — dead worker connections block indefinitely                                 |
| CC-08 | **Medium**   | `api/websocket/worker_stream.py`  | 241–259 | Binary frame collection has no frame sequence validation — out-of-order frames silently corrupt                           |
| CC-09 | **Medium**   | `cascade_correlation.py`          | 277     | `SharedMemory(create=True)` raises `FileExistsError` on orphaned blocks from previous crashes                             |
| CC-10 | **Medium**   | `cascade_correlation.py`          | 2018    | `_collect_worker_results` uses busy-wait polling pattern                                                                  |
| CC-11 | **Medium**   | `cascade_correlation.py`          | 782–783 | `torch.set_num_threads()` is global — affects API server's forward passes                                                 |
| CC-12 | **Medium**   | `api/routes/training.py`          | 140–141 | Route accesses private `ws_manager._seq_lock` and `ws_manager._next_seq`                                                  |
| CC-13 | **Low**      | `api/websocket/manager.py`        | 304–314 | `_send_json` catches all exceptions silently; 0.5s timeout may be too aggressive for large topology messages              |
| CC-14 | **Low**      | `api/lifecycle/monitor.py`        | 159     | `"topology_change"` callback slot exists but is never triggered — dead code                                               |
| CC-15 | **Low**      | `cascade_correlation.py`          | 326     | `SharedMemory(track=False)` means orphaned blocks require manual cleanup or reboot                                        |
| CC-16 | **Low**      | `cascade_correlation.py`          | 3722    | `candidates_per_layer` attribute accessed via `getattr` with default — hidden undocumented feature                        |
| CC-17 | **Low**      | `candidate_unit.py`               | 388     | `os.environ["PYTHONHASHSEED"]` modified process-wide — affects API server if called from main process                     |
| CC-18 | **Low**      | `candidate_unit.py`               | 179     | 20+ verbose log calls in `CandidateUnit.__init__` — generates 160+ log calls per grow iteration at pool_size=8            |
| CC-19 | **Low**      | `parallelism/task_distributor.py` | 50      | Directly accesses private `_coordinator._registry` attribute — tight coupling                                             |
| CC-20 | **Low**      | `parallelism/task_distributor.py` | 103–106 | Local and remote task execution is sequential, not parallel                                                               |
| CC-21 | **Info**     | `api/websocket/control_stream.py` | 180     | Heartbeat timeout closes with code 1006 (abnormal) instead of 1000 (normal)                                               |
| CC-22 | **Info**     | `api/lifecycle/manager.py`        | 649     | Inconsistent timestamp formats: `datetime.now().isoformat()` vs `time.time()`                                             |

### 2.2 juniper-canopy

| ID    | Severity   | File                    | Line(s)        | Finding                                                                                                                           |
|-------|------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------|
| CN-01 | **Medium** | `dashboard_manager.py`  | 346–349        | `_api_base_url` hardcoded to `127.0.0.1` — Dash REST callbacks break in Docker/remote deployments                                 |
| CN-02 | **Medium** | `main.py`               | 806–841        | Service mode populates parameter values with internal defaults first — UI shows incorrect values for params cascor doesn't expose |
| CN-03 | **Medium** | `network_visualizer.py` | 1186–1354      | 3D topology view ignores `show_weights` parameter — no weight labels on 3D edges                                                  |
| CN-04 | **Medium** | `network_visualizer.py` | 391–398        | Topology hash ignores weight values — graph doesn't redraw for weight-only updates during training                                |
| CN-05 | **Low**    | `settings.py`           | 53             | `modifiable_during_training` flag defined in `TrainingParamConfig` but never checked — all params changeable mid-training         |
| CN-06 | **Low**    | `websocket_manager.py`  | 186            | `heartbeat_interval` configured but no heartbeat ping/pong loop exists                                                            |
| CN-07 | **Low**    | `main.py`               | 90–93, 110–113 | Duplicate `APP_VERSION` assignment — dead code                                                                                    |
| CN-08 | **Low**    | `dashboard_manager.py`  | 2346+          | 3–5 self-directed REST requests/second per browser tab — no request coalescing                                                    |
| CN-09 | **Low**    | Decision boundary       | —              | Resolution=200 → 40K forward passes per update on 1s interval; no throttling or caching                                           |
| CN-10 | **Info**   | `training_metrics.py`   | 45–49          | `TrainingMetricsComponent` deprecated but still present                                                                           |

### 2.3 juniper-cascor-client

| ID    | Severity   | File                        | Line(s)  | Finding                                                                                               |
|-------|------------|-----------------------------|----------|-------------------------------------------------------------------------------------------------------|
| CL-01 | **Medium** | `ws_client.py`              | 231–240  | `command()` vs `set_params()` message format inconsistency — `command()` never sends `"type"` field   |
| CL-02 | **Medium** | `client.py`                 | 378–385  | Error parsing silently loses `{"error": "string"}` format messages — falls through to `response.text` |
| CL-03 | **Medium** | `client.py`                 | 366      | `response.json()` can raise `ValueError`/`JSONDecodeError` on non-JSON success responses (e.g., 204)  |
| CL-04 | **Medium** | `constants.py`              | 31       | 503 not in `RETRYABLE_STATUS_CODES` — transient service unavailability not retried                    |
| CL-05 | **Low**    | `ws_client.py`              | 322–336  | `_recv_loop` silently drops non-`command_response` messages on control stream                         |
| CL-06 | **Low**    | `ws_client.py`              | 332      | Bare `Exception` catch in `_recv_loop` — too broad, could catch `SystemExit`/`KeyboardInterrupt`      |
| CL-07 | **Low**    | `ws_client.py`              | 90–102   | `send_command()` on training stream is fire-and-forget — confusing API surface                        |
| CL-08 | **Low**    | `constants.py`              | 14       | Version in header comment (0.3.0) stale vs package version (0.4.0)                                    |
| CL-09 | **Low**    | `testing/fake_client.py`    | 100–105  | `STATE_TRANSITIONS` dict declared but never used — dead code                                          |
| CL-10 | **Low**    | `testing/fake_client.py`    | 536, 574 | Duplicate/dead state maps (`_STATE_TO_FSM`, `_STATE_TO_PHASE`)                                        |
| CL-11 | **Info**   | `testing/fake_ws_client.py` | —        | No `FakeCascorControlStream` exists — testing gap for `set_params` via WS                             |

### 2.4 juniper-cascor-worker

| ID    | Severity   | File               | Line(s) | Finding                                                                                              |
|-------|------------|--------------------|---------|------------------------------------------------------------------------------------------------------|
| CW-01 | **Medium** | `worker.py`        | 225     | Timeout error sends `candidate_uuid: ""` instead of actual UUID from `candidate_data`                |
| CW-02 | **Medium** | `worker.py`        | 410     | Legacy worker calls private `CascadeCorrelationNetwork._worker_loop` — tight coupling                |
| CW-03 | **Medium** | `task_executor.py` | 46–48   | Dynamic import `from candidate_unit.candidate_unit import CandidateUnit` — fragile, no version check |
| CW-04 | **Low**    | `task_executor.py` | 165–168 | Activation derivatives recompute forward pass (double sigmoid/tanh)                                  |
| CW-05 | **Low**    | `task_executor.py` | 100–106 | Heavy `hasattr` usage on training result — loose return type contract                                |
| CW-06 | **Low**    | `worker.py`        | 280–281 | `_build_capabilities` unconditionally imports `torch` — no graceful error if missing                 |
| CW-07 | **Low**    | `cli.py`           | 97–102  | Signal handler race window before event loop starts                                                  |
| CW-08 | **Info**   | `ws_connection.py` | —       | No explicit WebSocket ping/pong timeout configuration (relies on library defaults)                   |

### 2.5 juniper-data

| ID    | Severity   | File                     | Line(s) | Finding                                                                                      |
|-------|------------|--------------------------|---------|----------------------------------------------------------------------------------------------|
| JD-01 | **High**   | `api/security.py`        | 59      | Non-constant-time API key comparison — timing side-channel attack vector                     |
| JD-02 | **Medium** | `api/security.py`        | 116–117 | Rate limiter `_counters` grow unbounded — memory leak / DoS vector                           |
| JD-03 | **Medium** | `api/routes/datasets.py` | 107     | Synchronous dataset generation blocks async event loop                                       |
| JD-04 | **Medium** | `api/routes/datasets.py` | 414–424 | `batch_export` builds entire ZIP in memory — no size limit                                   |
| JD-05 | **Medium** | `api/routes/datasets.py` | 89–90   | Pydantic validation errors returned raw to client — information leak                         |
| JD-06 | **Medium** | `api/routes/health.py`   | 57      | `glob("*.npz")` on every readiness probe — expensive with many datasets                      |
| JD-07 | **Medium** | `storage/local_fs.py`    | 176–183 | `delete()` has TOCTOU race condition — non-atomic check-then-unlink                          |
| JD-08 | **Medium** | `storage/local_fs.py`    | 226     | `update_meta` writes directly without temp file — concurrent reads see partial data          |
| JD-09 | **Medium** | `storage/base.py`        | 261     | `filter_datasets` reads ALL metadata from disk per call — no caching or indexing             |
| JD-10 | **Medium** | `core/dataset_id.py`     | 30–36   | Deterministic IDs with `seed=None` → same ID for different random data → stale cache returns |
| JD-11 | **Medium** | `api/app.py`             | 142     | `app = create_app()` at module level — settings frozen at import time                        |
| JD-12 | **Medium** | `__main__.py`            | 62–64   | CLI storage path override via `os.environ` after `Settings()` — fragile order dependency     |
| JD-13 | **Low**    | `api/middleware.py`      | 81      | Body size limit checks `Content-Length` header only — can be omitted by attacker             |
| JD-14 | **Low**    | `storage/base.py`        | 23      | `_version_lock` is a class variable — won't work across multiple uvicorn workers             |
| JD-15 | **Low**    | `pyproject.toml`         | 205     | mypy `python_version = "3.14"` while `requires-python = ">=3.12"`                            |
| JD-16 | **Low**    | `__main__.py`            | 59      | Custom log levels (`TRACE`/`VERBOSE`) passed to uvicorn which doesn't support them           |

### 2.6 juniper-data-client

| ID    | Severity   | File                     | Line(s) | Finding                                                                                                |
|-------|------------|--------------------------|---------|--------------------------------------------------------------------------------------------------------|
| DC-01 | **High**   | `constants.py`           | 91–92   | Generator names `"circle"`/`"moon"` don't match server's `"circles"` — no `"moon"` generator on server |
| DC-02 | **Medium** | `constants.py`           | 29      | `RETRY_ALLOWED_METHODS` includes `POST`/`DELETE` — retrying `create_dataset` can cause duplicates      |
| DC-03 | **Medium** | `client.py`              | 409     | `np.load(io.BytesIO(content))` — `NpzFile` object never closed (resource leak)                         |
| DC-04 | **Medium** | `testing/fake_client.py` | 112–137 | `_GENERATOR_CATALOG` lists `"circle"`/`"moon"` not present on real server — FakeClient masks bugs      |
| DC-05 | **Medium** | `testing/generators.py`  | —       | Spiral generator formula differs from server's `SpiralGenerator` — different data geometry             |
| DC-06 | **Low**    | `testing/fake_client.py` | 762–766 | `close()` clears `_datasets` — real client only closes HTTP session                                    |

### 2.7 juniper-deploy

| ID    | Severity | File                           | Line(s)            | Finding                                                                                                          |
|-------|----------|--------------------------------|--------------------|------------------------------------------------------------------------------------------------------------------|
| DD-01 | **High** | `docker-compose.yml`           | 129, 298, 349, 386 | Cascor and canopy ports bound to `0.0.0.0` — exposed to network (data correctly uses `127.0.0.1`)                |
| DD-02 | **Low**  | `docker-compose.yml`           | 98                 | `JUNIPER_DATA_API_KEYS` defaults to empty — auth disabled by default in Docker                                   |
| DD-03 | **Low**  | `docker-compose.yml`           | 109–110            | Secret name `juniper_data_api_key` (singular) vs env var `juniper_data_api_keys` (plural) — naming inconsistency |
| DD-04 | **Low**  | `prometheus/prometheus.yml`    | 36–38              | References `recording_rules.yml` and `alert_rules.yml` that don't exist                                          |
| DD-05 | **Low**  | `scripts/wait_for_services.sh` | 39–41              | Data and canopy URLs use hardcoded ports instead of env vars                                                     |

### 2.8 juniper-ml

| ID    | Severity   | File                           | Line(s) | Finding                                                                                        |
|-------|------------|--------------------------------|---------|------------------------------------------------------------------------------------------------|
| ML-01 | **Medium** | `scripts/wake_the_claude.bash` | 37      | `DEBUG="${TRUE}"` hardcoded ON in production — all invocations emit debug output               |
| ML-02 | **Medium** | `scripts/wake_the_claude.bash` | 652–655 | `NOHUP_STATUS=$?` captures fork status (always 0), not process exit — error check is dead code |
| ML-03 | **Low**    | `pyproject.toml`               | 30–31   | No upper bounds on dependency versions — major bumps could break consumers                     |

---

## 3. Cross-Repository Issues

### 3.1 Generator Name Mismatch

**Repositories**: juniper-data, juniper-data-client
**Severity**: HIGH

The client library defines generators `"circle"` and `"moon"` (in `constants.py` and `testing/fake_client.py`), but the server has `"circles"` (plural) and no `"moon"` generator at all. The `FakeDataClient` masks this mismatch — tests pass against the fake but would fail against the real server.

### 3.2 Wire Protocol Alignment

**Repositories**: juniper-cascor, juniper-cascor-client, juniper-cascor-worker
**Status**: ✅ Well-maintained

The Wave 5 cross-repo verification established bit-identical alignment for:

- `MSG_TYPE_*` values match `MessageType(StrEnum)` in `protocol.py`
- `BINARY_FRAME_*` constants match server's struct format
- `API_KEY_HEADER_NAME` matches `"X-API-Key"`
- All `ENDPOINT_*` paths match server routes

The constants in all three packages include explicit documentation of the alignment requirement.

### 3.3 State Name Inconsistency

**Repositories**: juniper-cascor, juniper-cascor-client
**Severity**: MEDIUM

The cascor state machine returns UPPERCASE state names (`"STOPPED"`, `"STARTED"`), while `TrainingState.get_state()` returns title-case strings (`"Stopped"`, `"Started"`). Client code must normalize case. The `FakeCascorClient` uses yet another mapping (`STATE_IDLE` → `FSM_STATUS_IDLE` vs `FSM_STATUS_STOPPED`), adding confusion.

### 3.4 Port Mapping Inconsistency

**Repositories**: juniper-cascor, juniper-deploy
**Severity**: LOW

Cascor listens on container port 8200 but is mapped to host port 8201 in Docker. The client default `base_url` is `http://localhost:8200` which is correct for local development (no Docker) but wrong for Docker deployments where the host port is 8201. The `.env.example` documents this, but it's a common source of confusion.

---

## 4. Performance Analysis

### 4.1 juniper-cascor Performance

| Area                    | Status           | Detail                                                                           |
|-------------------------|------------------|----------------------------------------------------------------------------------|
| **Forward pass**        | ✅ Optimized     | Pre-allocated buffer (OPT-1) eliminates N `torch.cat()` calls                    |
| **Hidden output cache** | ✅ Optimized     | Forward pass cache (OPT-4) keyed by `data_ptr()` prevents stale cache            |
| **Output training**     | ✅ Optimized     | Hidden output computation hoisted above epoch loop (CR-060)                      |
| **Shared memory**       | ✅ Well-designed | Zero-copy tensor sharing via POSIX shared memory (OPT-5)                         |
| **Worker pool**         | ⚠️ Concern       | Busy-wait polling for worker results; `qsize()` unreliable on macOS              |
| **Candidate logging**   | ⚠️ Concern       | 20+ log calls per `CandidateUnit.__init__` × pool_size = 160+ per grow iteration |
| **BLAS threads**        | ⚠️ Concern       | `torch.set_num_threads()` is global — MP config affects API server               |
| **Task distribution**   | ⚠️ Concern       | Local and remote execution is sequential, not parallel                           |

### 4.2 juniper-canopy Performance

| Area                  | Status           | Detail                                                                       |
|-----------------------|------------------|------------------------------------------------------------------------------|
| **Polling frequency** | ⚠️ Concern       | 3–5 self-directed REST requests/second per browser tab                       |
| **Decision boundary** | ⚠️ Concern       | Resolution=200 → 40K forward passes per second with no throttling            |
| **Topology hash**     | ⚠️ Design choice | Hash ignores weights — prevents unnecessary redraws but masks weight changes |
| **Metrics history**   | ✅ Good          | `deque(maxlen=10000)` bounds memory                                          |

### 4.3 juniper-data Performance

| Area                   | Status     | Detail                                                            |
|------------------------|------------|-------------------------------------------------------------------|
| **Sync generation**    | ⚠️ Concern | `generator.generate(params)` blocks event loop in async endpoint  |
| **Readiness probe**    | ⚠️ Concern | `glob("*.npz")` scans entire data directory on every health check |
| **Metadata filtering** | ⚠️ Concern | `filter_datasets` reads ALL metadata from disk per request        |
| **Batch export**       | ⚠️ Concern | ZIP built entirely in memory — no streaming                       |

---

## 5. Architectural Assessment

### 5.1 Strengths

1. **Clean separation of concerns**: Each repository has a single, well-defined responsibility
2. **Client library pattern**: Published PyPI packages (`juniper-data-client`, `juniper-cascor-client`) with testing utilities enable consumer testing without live services
3. **Wire protocol documentation**: Constants alignment is explicitly tracked and verified
4. **CI/CD maturity**: Comprehensive pre-commit hooks, multi-version test matrices, security scanning, trusted publishing
5. **CasCor implementation quality**: The core algorithm implementation is well-documented, correctly handles cascade connectivity, and includes thoughtful optimizations
6. **Observability infrastructure**: Prometheus, Grafana dashboards, Sentry integration, request ID tracking

### 5.2 Weaknesses

1. **Push vs. poll architecture**: The WebSocket infrastructure exists but key events (topology changes) still require REST polling. This creates unnecessary latency and server load.
2. **Dual-path complexity**: Both REST and WebSocket paths exist for parameter updates, with subtle format differences. This increases the surface area for bugs.
3. **State representation inconsistency**: State names differ between the state machine, training state, client fakes, and REST responses. No canonical normalization layer.
4. **Dynamic imports**: The worker's dependency on cascor's internal module structure (`candidate_unit.candidate_unit.CandidateUnit`) is fragile and version-unaware.
5. **FakeClient fidelity**: Testing fakes in `juniper-data-client` and `juniper-cascor-client` have behavioral divergences from real services (generator names, data geometry, state mapping).

### 5.3 Architecture Diagram: WebSocket Message Flow

```bash
juniper-cascor                    juniper-canopy
┌──────────────────┐              ┌───────────────────┐
│ Training Thread  │              │ Dash Callbacks    │
│   epoch_end ─────┼── broadcast ─┤── metrics_store   │
│   cascade_add ───┼── broadcast ─┤── topology hint   │  ← count only, not full topology
│   candidate_prog ┼── broadcast ─┤── progress_store  │
│   training_end ──┼── broadcast ─┤── event_store     │
│                  │              │                   │
│ ❌ topology_chg  │  (not wired) │                   │
│                  │              │ ⏱ REST poll/ 5s ─┼─ full topology (GET /topology)
└──────────────────┘              └───────────────────┘
```

---

## 6. Risk Assessment and Guardrails

### 6.1 Risks

| Risk                                                         | Likelihood | Impact | Mitigation                                                            |
|--------------------------------------------------------------|------------|--------|-----------------------------------------------------------------------|
| **Topology visualization stale during training**             | High       | Medium | REST polling at 5s provides eventual consistency                      |
| **Metaparameter apply showing wrong values in service mode** | High       | Medium | Demo mode works correctly; service mode needs cascor param sync       |
| **Shared memory leak on crash**                              | Medium     | Low    | `atexit` handler covers normal exits; `/dev/shm` blocks are small     |
| **API key timing attack**                                    | Low        | High   | Requires network access and many requests; mitigated by rate limiting |
| **Docker port exposure**                                     | Medium     | High   | Only affects Docker deployments; local dev is unaffected              |
| **Generator name mismatch causing client errors**            | High       | Medium | FakeClient masks this; will surface when testing against real server  |
| **Busy-wait CPU consumption in worker pool**                 | Medium     | Low    | Only affects during active parallel training                          |
| **Non-idempotent POST retry**                                | Low        | Medium | May create duplicate datasets on transient failures                   |

### 6.2 Guardrails

| Guardrail                      | Status     | Notes                                                                       |
|--------------------------------|------------|-----------------------------------------------------------------------------|
| **Pre-commit hooks**           | ✅ Strong  | Flake8/Ruff, Bandit, ShellCheck, MyPy, Markdownlint across all repos        |
| **CI/CD pipelines**            | ✅ Strong  | Multi-version test matrices, security scanning, coverage gates              |
| **Wire protocol verification** | ✅ Strong  | Wave 5 cross-repo bit-identity checks documented                            |
| **Type checking**              | ✅ Strong  | MyPy strict mode in client libraries; basic mode in applications            |
| **Test coverage**              | ✅ Good    | 80% minimum enforced; per-module 85% in juniper-data                        |
| **Secrets management**         | ✅ Good    | SOPS encryption, Docker secrets, pre-commit blocks unencrypted `.env`       |
| **Resource cleanup**           | ⚠️ Partial | `atexit` for shared memory; no stale block sweep                            |
| **Rate limiting**              | ⚠️ Partial | Exists but memory-unbounded                                                 |
| **Thread safety**              | ✅ Good    | Locks in lifecycle manager; `_topology_lock` for safe reads during training |

---

## 7. Recommendations

### 7.1 Immediate (Critical/High)

1. **Wire up topology broadcast**: Register a `topology_change` callback in `TrainingLifecycleManager._install_monitoring_hooks()` that calls `create_topology_message()` and broadcasts via the `WebSocketManager`. Trigger it after `add_unit()` completes and after each output training epoch.

2. **Fix generator name alignment**: Change `juniper-data-client/constants.py` from `"circle"` to `"circles"` and remove `"moon"`. Update `FakeDataClient._GENERATOR_CATALOG` to match the real server's generator registry.

3. **Fix Docker port bindings**: Add `127.0.0.1:` prefix to cascor and canopy port mappings in `docker-compose.yml`.

4. **Use constant-time API key comparison**: Replace `api_key in self._api_keys` with `any(hmac.compare_digest(api_key, k) for k in self._api_keys)` in `juniper-data/api/security.py`.

### 7.2 Short-Term (Medium)

5. **Add topology hash based on weights**: Include a hash or generation counter for weight values in the topology hash function so the network visualization redraws when weights change during training.

6. **Add rate limiter eviction**: Implement a TTL-based eviction for the `_counters` dictionary in `RateLimiter`, or use a bounded LRU cache.

7. **Run dataset generation in executor**: Wrap `generator.generate(params)` in `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the event loop.

8. **Fix `NpzFile` resource leak**: Use `with np.load(...) as npz:` context manager in `juniper-data-client/client.py`.

9. **Add `FakeCascorControlStream`**: Create a testing fake for the WebSocket control stream in `juniper-cascor-client/testing/`.

10. **Fix canopy `_api_base_url`**: Use the server's configured host/port instead of hardcoding `127.0.0.1`.

11. **Normalize state names**: Establish a canonical set of state name constants (lowercase) and use them consistently across cascor state machine, training state, client libraries, and fakes.

### 7.3 Long-Term (Low/Architectural)

12. **Add shared memory startup sweep**: On cascor server startup, remove stale `juniper_train_*` blocks from `/dev/shm`.

13. **Parallelize local+remote task execution**: In `TaskDistributor`, run local and remote task execution concurrently rather than sequentially.

14. **Reduce polling in canopy**: With topology broadcasts working (recommendation #1), reduce or eliminate the 5s REST polling for topology data. Rely on WS push with REST as fallback.

15. **Version-check cascor imports in worker**: Add a version compatibility check when the worker dynamically imports from the cascor codebase.

16. **Add message `type` field to all control commands**: Ensure `CascorControlStream.command()` includes `"type": "command"` in all messages, matching `set_params()` format.

17. **Add atomic writes to `update_meta`**: Use the same temp-file-then-rename pattern as `save()` in `juniper-data/storage/local_fs.py`.

---

*End of audit report.*
