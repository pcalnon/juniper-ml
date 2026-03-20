# Juniper CasCor Concurrency Architecture Plan

**Project**: Juniper Cascade Correlation Neural Network Platform
**Author**: Claude Code (Opus 4.6) + Paul Calnon
**Created**: 2026-03-18
**Status**: Draft (Validated 2026-03-18)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Analysis](#2-current-architecture-analysis)
3. [Legacy Architecture](#3-legacy-architecture)
4. [Requirements](#4-requirements)
5. [Proposed Approaches](#5-proposed-approaches)
6. [Security Analysis](#6-security-analysis)
7. [Comparative Analysis](#7-comparative-analysis)
8. [Recommendations](#8-recommendations)
9. [Implementation Plan](#9-implementation-plan)
10. [Testing Strategy](#10-testing-strategy)
11. [Risks and Guardrails](#11-risks-and-guardrails)

---

## 1. Executive Summary

The Juniper CasCor platform uses a hybrid concurrency architecture for parallel candidate neural network training. The current implementation has evolved through four release candidate fixes (RC-1 through RC-4) documented in `juniper-cascor/notes/PARALLEL_CANDIDATE_TRAINING_FIX_PLAN.md`. While local parallelism is well-optimized, the remote/distributed worker system has fundamental limitations that prevent reliable deployment across heterogeneous environments.

This plan analyzes the current state, evaluates three architectural approaches, and recommends a phased implementation strategy to achieve reliable, secure, high-performance distributed training.

### Key Findings

- **Local parallelism** (multiprocessing persistent worker pool) is mature and well-optimized
- **Remote worker support** requires the full cascor codebase installed on every worker machine
- **No transport encryption** exists for distributed training
- **No dynamic worker management** -- workers cannot join/leave during training
- **No reconnection logic** for intermittent connections
- **Python 3.14 free-threading** is not currently feasible (standard GIL-enabled build, no PyTorch support)
- **RC-2 broke the existing remote worker path** -- `BaseManager`-proxied queues replaced with direct `mp.Queue`
- **Critical security vulnerabilities** exist in the pickle-based serialization protocol

---

## 2. Current Architecture Analysis

### 2.1 Overview

The juniper-cascor application uses three distinct concurrency models that work together:

| Layer                         | Technology                                 | Purpose                          |
|-------------------------------|--------------------------------------------|----------------------------------|
| **Process-based parallelism** | `multiprocessing` (persistent worker pool) | CPU-intensive candidate training |
| **Thread-based parallelism**  | `threading` + `ThreadPoolExecutor`         | Training lifecycle coordination  |
| **Async I/O**                 | `asyncio` + FastAPI/Uvicorn                | HTTP/WebSocket API serving       |

### 2.2 Process-Based Parallelism (Candidate Training)

**Primary file**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

#### CandidateTrainingManager (lines 212-250)

A custom `BaseManager` subclass that registers two queue factories for inter-process communication:

```python
class CandidateTrainingManager(BaseManager):
    """Custom manager for handling candidate training queues."""

CandidateTrainingManager.register("get_task_queue", callable=_create_task_queue)
CandidateTrainingManager.register("get_result_queue", callable=_create_result_queue)
```

Global module-level queues (`_task_queue`, `_result_queue`) are managed via factory functions (lines 184-208). The manager supports configurable start methods: `fork`, `spawn`, `forkserver`.

#### Persistent Worker Pool (RC-4, lines 2461-2562)

The `_ensure_worker_pool()` static method manages a reusable pool of worker processes:

- **Health checking**: Verifies all workers are alive before reuse
- **Lazy initialization**: Pool created on first use
- **Daemon processes**: Auto-terminate when parent exits
- **Worker naming**: `CandidateWorker-{i}` for debugging

Shutdown uses a three-phase escalation strategy:

1. Send `None` sentinels for graceful shutdown
2. `terminate()` with 1-5 second timeout
3. `SIGKILL` as final resort

#### Worker Loop (lines 2565-2705)

The `_worker_loop()` static method runs in each worker process:

- **Thread pinning** (RC-1): Sets `torch.set_num_threads()`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS` to prevent CPU oversubscription
- **Stand-by mode**: Sleeps 0.1s when no tasks available
- **Sentinel shutdown**: `None` task triggers clean exit
- **Error recovery**: Failed tasks produce a `CandidateTrainingResult` with `success=False`
- **Shared data optimization** (RC-3): Lightweight task format with shared training inputs passed via process args

#### Execution Flow

`_execute_parallel_training()` orchestrates the training round:

1. Get/create persistent worker pool via `_ensure_worker_pool()`
2. Send task tuples to `task_queue`
3. Collect results from `result_queue` with timeout and worker liveness checks
4. Return list of `CandidateTrainingResult` objects

#### Pickling Solutions

- **`ActivationWithDerivative`** (lines 292-401): Picklable wrapper for activation functions using name-based serialization/deserialization
- **`__getstate__`/`__setstate__`** (lines 1976-1991): Excludes non-picklable objects (queues, manager, worker pool state) from serialization

### 2.3 Thread-Based Parallelism (Training Lifecycle)

**Primary file**: `juniper-cascor/src/api/lifecycle/manager.py`

#### TrainingLifecycleManager

Wraps `CascadeCorrelationNetwork` training in a background thread via `ThreadPoolExecutor`:

**Synchronization primitives**:

| Primitive                 | Purpose                   |
|---------------------------|---------------------------|
| `_training_lock` (Lock)   | Serializes network access |
| `_metrics_lock` (Lock)    | Protects metrics history  |
| `_topology_lock` (Lock)   | Protects network topology |
| `_stop_requested` (Event) | Graceful stop signal      |
| `_pause_event` (Event)    | Pause/resume control      |

**Key design**: Training runs in a background thread (`cascor-train`), while the FastAPI event loop handles HTTP/WebSocket requests. The `_pause_event` and `_stop_requested` events bridge the two contexts.

#### TrainingState and TrainingMonitor

**File**: `juniper-cascor/src/api/lifecycle/monitor.py`

- **TrainingState** (lines 18-92): Thread-safe state container with atomic updates via `threading.Lock`
- **TrainingMonitor** (lines 95-225): Collects real-time metrics using `deque(maxlen=10000)` buffer and `queue.Queue` for async polling. Callback system dispatches events to registered handlers.

#### Thread-Safe Broadcasting Bridge

**File**: `juniper-cascor/src/api/websocket/manager.py`

The `WebSocketManager.broadcast_from_thread()` method bridges the training thread and async event loop:

```python
def broadcast_from_thread(self, message: dict) -> None:
    asyncio.run_coroutine_threadsafe(self.broadcast(message), self._event_loop)
```

This is the critical integration point between the synchronous training thread and the asynchronous WebSocket infrastructure.

### 2.4 Async I/O (FastAPI/Uvicorn)

**Files**: `src/api/app.py`, `src/server.py`, `src/api/websocket/`

- **Uvicorn**: Single-process async event loop
- **WebSocket endpoints**:
  - `/ws/training` -- Read-only metrics stream (server pushes via broadcast)
  - `/ws/control` -- Bidirectional command channel (client sends commands, server acknowledges)
- **Lifespan management**: Event loop reference stored for `run_coroutine_threadsafe()` calls
- **Connection limits**: Max 50 WebSocket connections

#### Rate Limiter

**File**: `src/api/security.py`

Thread-safe fixed-window rate limiter using `threading.Lock` for counter updates. Provides per-key tracking with configurable requests-per-minute and window size.

### 2.5 Remote Worker Support

#### RemoteWorkerClient (juniper-cascor)

**File**: `juniper-cascor/src/remote_client/remote_client.py`

Connects to `CandidateTrainingManager` server, obtains proxy queues, and spawns local worker processes running `CascadeCorrelationNetwork._worker_loop()`:

- Uses `forkserver` multiprocessing context
- Daemon worker processes
- Sentinel-based graceful shutdown
- **Requires full cascor codebase installed**

#### CandidateTrainingWorker (juniper-cascor-worker)

**File**: `juniper-cascor-worker/juniper_cascor_worker/worker.py`

Standalone PyPI package providing CLI-based distributed worker:

- **Configuration**: `WorkerConfig` dataclass with env var support
- **CLI**: `juniper-cascor-worker --manager-host HOST --manager-port PORT --authkey KEY --workers N`
- **Signal handling**: Two-tap SIGINT/SIGTERM shutdown
- **Process management**: Configurable multiprocessing context (`forkserver`, `spawn`, `fork`)
- **Dependencies**: `numpy>=1.24.0`, `torch>=2.0.0`
- **Critical limitation**: Imports `CascadeCorrelationNetwork` for both `CandidateTrainingManager` (class registration) and `_worker_loop` (target function)

### 2.6 Client Library (juniper-cascor-client)

**Directory**: `juniper-cascor-client/juniper_cascor_client/`

Hybrid sync/async client library:

| Component              | Pattern     | Technology             | Thread-Safe?                   |
|------------------------|-------------|------------------------|--------------------------------|
| `JuniperCascorClient`  | Synchronous | `requests` + `urllib3` | No (`Session` not thread-safe) |
| `CascorTrainingStream` | Async       | `websockets`           | Yes (pure async)               |
| `CascorControlStream`  | Async       | `websockets`           | Yes (pure async)               |

**Key features**:

- HTTP retry strategy (3 attempts, 0.5 backoff, retry on 502/504)
- Connection pooling (pool_maxsize=10)
- Callback-based WebSocket message dispatch
- No built-in WebSocket reconnection logic
- Comprehensive fake client testing framework with thread-safe `FakeCascorClient`

### 2.7 Python 3.14 Free-Threading Status

**Current status**: No free-threading code exists in the codebase.

- No `sys._is_gil_enabled()` checks
- No `PYTHON_GIL=0` configuration
- No free-threading annotations or guards
- Architecture implicitly depends on GIL for some thread safety
- Multiprocessing is used specifically to bypass GIL for CPU-intensive candidate training

### 2.8 Thread Safety Warning

From `CascadeCorrelationNetwork` docstring:

> **NOT THREAD-SAFE**: Do not share CascadeCorrelationNetwork instances between threads without proper synchronization. For concurrent training scenarios, create separate network instances per thread.

The `TrainingLifecycleManager` properly isolates the network in a single background thread.

---

## 3. Legacy Architecture

**Directory**: `juniper-legacy/JuniperLegacy/src/prototypes/juniper_cascor/`

### 3.1 Original Multiprocessing Design

The legacy implementation used the same `BaseManager` pattern but with key differences:

- **Lambda functions** for activation functions -- caused pickling failures
- **Per-round pool creation** -- no persistent pool, processes recreated each training round
- **Dynamic worker count**: `max(1, min(candidate_pool_size, cpu_affinity_count, cpu_count) - 1)`
- **Module preloading** required for forkserver: `['logging', 'torch', 'multiprocessing.managers.BaseManager', 'uuid', ...]`

### 3.2 Evolution Through RC Fixes

| Phase | Fix                                            | Problem Solved                                           |
|-------|------------------------------------------------|----------------------------------------------------------|
| RC-1  | PyTorch thread pinning                         | CPU oversubscription from uncontrolled BLAS thread pools |
| RC-2  | Direct `mp.Queue` (bypass BaseManager proxies) | Queue proxy overhead and serialization bottleneck        |
| RC-3  | Shared training inputs via process args        | Redundant serialization of identical training data       |
| RC-4  | Persistent worker pool                         | Per-round process creation overhead                      |

### 3.3 Legacy Threaded Plot

**File**: `juniper-legacy/JuniperLegacy/src/prototypes/threaded_plot/src/threaded_plot.py`

Producer-consumer pattern with thread queues for matplotlib thread safety. Uses a `@ript` ("Run In Plotting Thread") decorator and global send/return queues.

---

## 4. Requirements

### 4.1 Functional Requirements

| ID   | Requirement                                              | Priority |
|------|----------------------------------------------------------|----------|
| FR-1 | Remote workers connect before OR after training starts   | Must     |
| FR-2 | Support heterogeneous hardware and OS environments       | Must     |
| FR-3 | Tolerate intermittent worker connections                 | Must     |
| FR-4 | Lightweight remote worker code                           | Should   |
| FR-5 | Python-based, avoid non-standard libraries unless needed | Should   |
| FR-6 | Dynamic worker joining/leaving during training rounds    | Must     |
| FR-7 | Automatic task redistribution on worker failure          | Must     |
| FR-8 | Preserve existing local parallelism performance          | Must     |

### 4.2 Performance Requirements

| ID   | Requirement                                        | Priority |
|------|----------------------------------------------------|----------|
| PR-1 | High performance is critical                       | Must     |
| PR-2 | Zero regression in local-only training throughput  | Must     |
| PR-3 | Remote worker overhead < 5% of task execution time | Should   |
| PR-4 | Support 1-50+ concurrent remote workers            | Should   |

### 4.3 Security Requirements

| ID   | Requirement                                         | Priority |
|------|-----------------------------------------------------|----------|
| SR-1 | Protect distributed network from external threats   | Must     |
| SR-2 | Protect individual workers from malicious workers   | Must     |
| SR-3 | Protect primary workstation from all remote workers | Must     |
| SR-4 | Protect primary workstation from external threats   | Must     |
| SR-5 | Encrypt all data in transit                         | Must     |
| SR-6 | Authenticate all worker connections                 | Must     |
| SR-7 | Validate all data received from workers             | Must     |

### 4.4 Platform Requirements

| ID     | Requirement                               |
|--------|-------------------------------------------|
| PLAT-1 | All machines run Python 3.14+             |
| PLAT-2 | Worker code should be installable via pip |
| PLAT-3 | Support Linux, macOS, and Windows workers |

---

## 5. Proposed Approaches

### 5.1 Approach A: WebSocket-Based Distributed Workers

#### Overview

Replace `BaseManager` protocol with WebSocket Secure (WSS) for all remote worker communication. Workers connect to a new FastAPI WebSocket endpoint (`/ws/v1/workers`) on the existing cascor server.

#### Architecture

```bash
                    JUNIPER CASCOR SERVER (Primary Workstation)
 ┌─────────────────────────────────────────────────────────────────┐
 │  FastAPI Application                                            │
 │  ┌────────────────┐   ┌──────────────────────────────────────┐  │
 │  │ /ws/training   │   │ /ws/v1/workers                       │  │
 │  │ /ws/control    │   │  - JWT authentication                │  │
 │  └────────────────┘   │  - Binary frame dispatch             │  │
 │                       │  - Heartbeat management              │  │
 │                       └────────┬─────────────────────────────┘  │
 │                                │                                │
 │  ┌─────────────────────────────┴──────────────────────────────┐ │
 │  │              WorkerCoordinator                             │ │
 │  │  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐   │ │
 │  │  │WorkerRegistry│  │TaskDistributor │  │ResultCollector│   │ │
 │  │  └──────────────┘  └────────────────┘  └───────────────┘   │ │
 │  └────────────────────────────────────────────────────────────┘ │
 └─────────────────────────────────────────────────────────────────┘
                        │ WSS (TLS 1.3)
          ┌─────────────┼─────────────┐
     ┌────┴────┐   ┌────┴────┐   ┌────┴─────┐
     │Worker A │   │Worker B │   │Worker C  │
     │(Linux)  │   │(macOS)  │   │(Windows) │
     └─────────┘   └─────────┘   └──────────┘
```

#### Server-Side Design

**WorkerRegistry**: Thread-safe registry tracking connected workers with:

- Worker ID, capabilities (CPU cores, GPU, memory, Python/PyTorch versions)
- Connection timestamp, last heartbeat, health score
- Active task tracking

**TaskDistributor**: Assigns tasks to workers based on:

- Round-robin among idle workers (weighted by capacity)
- Health score priority (healthier workers get tasks first)
- Capability matching (future: GPU-aware routing)

**ResultCollector**: Validates and aggregates results:

- Schema validation (type, bounds, task correlation)
- Server-side correlation cross-verification for top candidates
- Timeout-based task reassignment

**Worker Mid-Training Join**: New workers register and immediately receive tasks from the current round's unassigned pool. If all tasks are dispatched, the new worker waits for the next round.

**Worker Disconnection Handling**: Active tasks from disconnected workers are marked as timed-out after `heartbeat_timeout * 3` and reassigned to available workers.

#### Client-Side (Worker) Design

Minimal worker agent with dependencies: `websockets`, `numpy`, `torch` only.

```python
class CascorWorkerAgent:
    """Lightweight WebSocket-based training worker."""

    async def connect(self, url, token):
        self._ws = await websockets.connect(url, extra_headers={"Authorization": f"Bearer {token}"})

    async def run(self):
        async for message in self._ws:
            msg = decode_message(message)  # JSON envelope + binary tensor payload
            if msg["type"] == "task_assign":
                result = self._execute_task(msg)
                await self._ws.send(encode_result(result))
            elif msg["type"] == "heartbeat_request":
                await self._ws.send(encode_heartbeat())
```

**Reconnection strategy**: Exponential backoff (1s base, 60s max, jitter). On reconnect, worker re-authenticates and re-registers. In-flight tasks at disconnection are handled by server-side timeout.

**Heartbeat**: Worker sends heartbeat every 10 seconds. Server marks worker stale after 30 seconds without heartbeat.

#### Serialization Protocol

- **Control messages**: JSON envelope (`{"type": "...", "task_id": "...", ...}`)
- **Tensor data**: Binary WebSocket frames with msgpack-encoded numpy arrays
- **Compression**: Optional zstd compression for large tensors (configurable threshold)
- **Candidate training function**: Serialized via `cloudpickle` and cached per training round (sent once, not per task)

#### Strengths

1. **Native TLS** via WSS -- no socket monkey-patching
2. **Firewall-friendly** -- single HTTPS port
3. **Reuses existing infrastructure** -- FastAPI WebSocket patterns already in codebase
4. **Language-agnostic potential** -- WebSocket is a standard protocol (future: non-Python workers)
5. **Built-in connection management** -- WebSocket protocol handles ping/pong, close frames
6. **No pickle dependency for remote path** -- eliminates arbitrary code execution vector if using structured serialization
7. **Dynamic worker management** -- natural fit for WebSocket connection/disconnection events

#### Weaknesses

1. **WebSocket overhead** -- JSON parsing, frame encoding add ~1-5ms per message vs ~0.1ms for direct queue
2. **Serialization cost** -- Tensors must be serialized/deserialized for network transport
3. **New infrastructure** -- Requires implementing a new WebSocket endpoint, worker protocol, and task distribution layer
4. **Complexity** -- More moving parts than enhanced multiprocessing
5. **Event loop integration** -- Must bridge async WebSocket handler with synchronous training thread
6. **No shared memory** -- Remote workers cannot share memory with the server

### 5.2 Approach B: Enhanced Multiprocessing with Decoupled Workers

#### Overview

Evolve the existing `BaseManager` approach to address remote limitations while preserving local performance. Key innovation: self-contained task payloads via `cloudpickle` that eliminate the cascor import dependency.

#### Architecture

```bash
 ┌─────────────────────────────────────────────────────────┐
 │  CascadeCorrelationNetwork                              │
 │    │                                                    │
 │    +── LOCAL PATH (unchanged): _ensure_worker_pool()    │
 │    │   direct mp.Queue + persistent mp.Process pool     │
 │    │                                                    │
 │    +── REMOTE PATH: EnhancedTrainingManager             │
 │          +── TLS-wrapped BaseManager server             │
 │          +── WorkerRegistry (heartbeats, health)        │
 │          +── TaskRedistributor (failure recovery)       │
 │          +── Self-contained task payloads (cloudpickle) │
 └─────────────────────────────────────────────────────────┘
            │ TLS + Certificate Auth
            v
 ┌──────────────────────────────────────────────────────┐
 │  REMOTE WORKER (Python 3.14+, numpy, torch)          │
 │  DecoupledWorkerAgent                                │
 │    +── ResilientConnection (exponential backoff)     │
 │    +── GenericTaskRunner (no cascor imports)         │
 │    +── HeartbeatThread (background liveness)         │
 └──────────────────────────────────────────────────────┘
```

#### Key Innovation: Self-Contained Task Payloads

Instead of workers importing `CascadeCorrelationNetwork.train_candidate_worker`, the server serializes the entire computation as a `TaskPayload`:

```python
@dataclass
class TaskPayload:
    task_id: str
    candidate_index: int
    candidate_data: dict
    training_inputs: bytes     # cloudpickle-serialized tensors
    train_function: bytes      # cloudpickle-serialized callable
    candidate_class: bytes     # cloudpickle-serialized CandidateUnit class
```

Workers use `GenericTaskRunner` to unpack and execute payloads without any cascor imports. The training function and `CandidateUnit` class arrive in the payload itself.

#### Server-Side Enhancements

- **EnhancedTrainingManager**: `BaseManager` subclass with TLS and control queue for worker registration/heartbeats
- **WorkerRegistry**: Thread-safe registry with health scoring
- **RemoteWorkerCoordinator**: Background thread monitoring heartbeats and redistributing tasks from failed workers
- **Dual-path dispatch**: Local workers use direct `mp.Queue`; remote workers use enhanced manager queue with serialized payloads

#### Connection Management

- **ResilientConnection**: Wraps BaseManager connection with exponential backoff retry (1s base, 60s max)
- **HeartbeatThread**: Background thread sending heartbeats every 10 seconds via control queue
- **Health scoring**: Success +0.05, failure -0.2, stale heartbeat = removal

#### Strengths

1. **Minimal disruption** -- Local path completely unchanged (RC-4 persistent pool intact)
2. **Leverages existing infrastructure** -- `BaseManager` already used and debugged
3. **Python stdlib foundation** -- Only `cloudpickle` added as new dependency
4. **Incremental adoption** -- Remote workers optional, local-only default
5. **Task granularity is ideal** -- 8-32 independent tasks per round, each seconds to minutes
6. **Preserves existing tests** -- All current tests continue working

#### Weaknesses

1. **cloudpickle security risk** -- Deserializing payloads is equivalent to arbitrary code execution
2. **BaseManager scalability ceiling** -- Single-threaded server process; bottleneck above ~50 remote workers
3. **No work stealing** -- Push-based distribution; idle workers wait
4. **Version sensitivity** -- cloudpickle serialized bytecode is Python-version-specific
5. **TLS wrapping complexity** -- `BaseManager` not designed for TLS; requires socket monkey-patching or external tunnel
6. **No GPU-aware routing** -- All tasks treated equally

### 5.3 Approach C: Hybrid Free-Threading + WebSocket

#### Overview

Two-tier architecture: Python 3.14 free-threading (no-GIL) for local workers (zero-copy shared memory) + WebSocket for remote workers. Graceful fallback to multiprocessing if GIL is enabled.

#### Architecture

```bash
                    ┌─────────────────────────────────────┐
                    │       TaskDistributor (unified)     │
                    │              │                      │
                    │     ┌────────┴────────┐             │
                    │     │                 │             │
                    │   LOCAL TIER      REMOTE TIER       │
                    │  (free-threaded)  (WebSocket)       │
                    │                                     │
                    │   ThreadPool ───┐  WSS Server ──┐   │
                    │   Thread 0      │  Worker A     │   │
                    │   Thread 1      │  Worker B     │   │
                    │   ...           │  Worker C     │   │
                    │   (shared mem)  │  (serialized) │   │
                    └─────────────────────────────────────┘
```

#### Local Tier: Free-Threading

**GIL detection**:

```python
def detect_free_threading() -> bool:
    if not hasattr(sys, '_is_gil_enabled'):
        return False
    return not sys._is_gil_enabled()
```

**Thread pool**: Replaces `multiprocessing.Process` pool with `threading.Thread` pool:

- Threads share memory directly -- no serialization overhead
- `queue.Queue` for task/result communication (internally synchronized)
- Training inputs passed by reference (zero-copy)

**Thread safety without GIL**:

- Each candidate task creates its own `CandidateUnit` -- no shared mutable state during training
- Shared training inputs are read-only during candidate training -- safe without locks
- `queue.Queue` is thread-safe by design
- `torch.set_num_threads(1)` must be set globally (not per-thread) to prevent BLAS oversubscription
- `torch.Generator` per-thread instead of global RNG for reproducibility

**Fallback**: If `sys._is_gil_enabled()` returns `True`, automatically uses existing multiprocessing path. Configuration option `CASCOR_FORCE_MULTIPROCESSING=1` to disable free-threading even when available.

#### Performance Expectations (Local Tier)

| Metric                | Multiprocessing (Current)          | Free-Threading (Proposed) |
|-----------------------|------------------------------------|---------------------------|
| Worker creation       | ~200-500ms per process             | ~0.1ms per thread         |
| Task serialization    | Pickle per task (~50-100us/tensor) | Zero-copy reference       |
| Result serialization  | Pickle per result (~200-500us)     | Zero-copy reference       |
| Memory per worker     | 100-300MB (full process)           | ~1MB stack per thread     |
| Communication latency | OS pipe IPC per message            | In-process mutex (~1-5us) |

**Estimated savings**: ~500-1000ms per full training run + ~1.5GB memory reduction for 8-worker pool.

#### Remote Tier: WebSocket

Same as Approach A's remote worker design. Workers connect via WSS, receive serialized tasks, return results.

#### Strengths

1. **Best-of-both-worlds** -- Zero-overhead local + flexible remote
2. **Massive memory savings** -- ~1-2GB less for typical 8-worker pool
3. **Backward compatible** -- Multiprocessing fallback is existing RC-4 code, unchanged
4. **Unified API** -- `TaskDistributor` abstracts execution tier from caller
5. **Dynamic remote workers** -- WebSocket supports connect-at-any-time
6. **Ecosystem alignment** -- Leverages existing FastAPI WebSocket infrastructure

#### Weaknesses

1. **Experimental dependency** -- Free-threading in Python 3.14 is experimental
2. **Two execution models to maintain** -- Thread pool + multiprocessing fallback doubles test surface
3. **Thread safety audit required** -- Existing code assumes GIL protection
4. **PyTorch compatibility uncertain** -- PyTorch free-threaded builds may not be stable
5. **BLAS thread contention** -- Shared BLAS pool in free-threaded mode requires careful thread count management
6. **Debugging complexity** -- Thread-based data races harder to diagnose than process-based issues
7. **Dual-protocol testing** -- 2x2 matrix: free-threading on/off x remote workers on/off

---

## 6. Security Analysis

### 6.1 Current Vulnerabilities

| ID  | Vulnerability                                     | Severity | Location                                              |
|-----|---------------------------------------------------|----------|-------------------------------------------------------|
| V-1 | Hardcoded authkey in source code                  | CRITICAL | `constants_model.py:47`                               |
| V-2 | No transport encryption                           | HIGH     | `BaseManager` uses raw TCP                            |
| V-3 | Pickle deserialization = arbitrary code execution | CRITICAL | `result_queue.get()` at `cascade_correlation.py:1720` |
| V-4 | No result validation                              | HIGH     | Results directly appended without checks              |
| V-5 | Shared queue namespace                            | MEDIUM   | All workers access same task/result queues            |
| V-6 | No connection tracking                            | MEDIUM   | `CandidateTrainingManager` has no worker registry     |

### 6.2 Threat Model

#### External Network Threats

| Threat                                            | Risk   | Mitigation                                               |
|---------------------------------------------------|--------|----------------------------------------------------------|
| Unauthorized connection (using hardcoded authkey) | HIGH   | Generate random authkey at deployment; never use default |
| Man-in-the-middle on training data                | HIGH   | Mandatory TLS (WSS or TLS-wrapped sockets)               |
| DoS against primary workstation                   | MEDIUM | Connection rate limiting, queue size limits              |
| Port scanning / fingerprinting                    | LOW    | Non-standard ports, TLS wrapping                         |

#### Malicious Worker Threats

| Threat                                 | Risk     | Mitigation                                               |
|----------------------------------------|----------|----------------------------------------------------------|
| Training poisoning via crafted results | CRITICAL | Result schema validation, correlation cross-verification |
| Arbitrary code execution via pickle    | CRITICAL | Restricted unpickler or structured serialization         |
| Task theft / cross-worker interference | MEDIUM   | Per-worker task assignment, task tracking                |
| Training data exfiltration             | HIGH     | Network egress control, worker machine hardening         |
| Resource exhaustion                    | MEDIUM   | Queue size limits, payload size limits, rate limiting    |

#### Primary Workstation Protection

| Threat                                | Risk     | Mitigation                                                             |
|---------------------------------------|----------|------------------------------------------------------------------------|
| Server compromise via deserialization | CRITICAL | Restricted unpickler, process isolation, sandboxed deserialization     |
| Worker-originated filesystem access   | MEDIUM   | Workers never access cascor codebase directly (with decoupled workers) |
| Model state exfiltration              | MEDIUM   | Training data necessarily shared; use trusted infrastructure           |

#### Worker-to-Worker Isolation

| Threat                         | Risk   | Mitigation                                      |
|--------------------------------|--------|-------------------------------------------------|
| Direct worker communication    | LOW    | Network segmentation, host-based firewalls      |
| Worker impersonation           | MEDIUM | Mutual TLS with per-worker certificates         |
| Cross-worker task interference | MEDIUM | Per-worker task assignment with server tracking |

### 6.3 Recommended Security Architecture

#### Layer 1: Transport Security (TLS 1.3)

- **WebSocket approach**: Native WSS (TLS built into WebSocket standard)
- **Multiprocessing approach**: TLS proxy (stunnel/socat) or SSH tunnel as pragmatic first step; native TLS socket wrapping as stretch goal

#### Layer 2: Authentication

- **Mutual TLS (mTLS)**: Each worker gets a unique X.509 client certificate signed by a project CA
- **JWT tokens**: For WebSocket approach, issue time-limited JWT tokens after mTLS handshake
- **Certificate hierarchy**: Project Root CA -> Server Certificate + Per-Worker Certificates

#### Layer 3: Input Validation

**Restricted Unpickler** for multiprocessing path:

```python
ALLOWED_CLASSES = {
    ('candidate_unit.candidate_unit', 'CandidateTrainingResult'),
    ('candidate_unit.candidate_unit', 'CandidateUnit'),
    ('torch._utils', '_rebuild_tensor_v2'),
    ('torch', 'Tensor'),
    ('numpy', 'ndarray'),
    # ... standard types
}

class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in ALLOWED_CLASSES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Blocked: {module}.{name}")
```

**Result validation**: Type checking, bounds validation (`0 <= correlation <= 1`), task tracking, candidate unit architecture verification.

#### Layer 4: Monitoring and Audit

Security event logging integrated with Juniper's extended logging system:

- `SECURITY_CONNECT/DISCONNECT`: Worker lifecycle events
- `SECURITY_AUTH_FAIL`: Failed authentication attempts
- `SECURITY_VALIDATION_FAIL`: Result validation failures
- `SECURITY_ANOMALY`: Statistical anomalies in training results

### 6.4 Certificate Management

```bash
# Generate CA (once, store offline)
openssl genpkey -algorithm ED25519 -out ca.key
openssl req -new -x509 -key ca.key -out ca.crt -days 3650 \
  -subj "/CN=Juniper CasCor CA/O=Juniper"

# Generate server cert
openssl genpkey -algorithm ED25519 -out server.key
openssl req -new -key server.key -out server.csr -subj "/CN=cascor-manager"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365

# Generate per-worker cert
openssl genpkey -algorithm ED25519 -out worker-alpha.key
openssl req -new -key worker-alpha.key -out worker-alpha.csr \
  -subj "/CN=worker-alpha"
openssl x509 -req -in worker-alpha.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out worker-alpha.crt -days 365
```

**Storage**: CA key offline/HSM; server/worker keys at `/etc/juniper/tls/` with mode 0600.

### 6.5 Security Implementation Priority

| Phase                          | Items                                                                                               |
|--------------------------------|-----------------------------------------------------------------------------------------------------|
| **Phase 1 (Critical)**         | Replace hardcoded authkey, add restricted unpickler, add result validation, add queue size limits   |
| **Phase 2 (High)**             | Add TLS transport, mTLS client certificates, connection rate limiting, audit logging                |
| **Phase 3 (Defense in Depth)** | Task assignment tracking, correlation cross-verification, per-worker metrics, cert rotation         |
| **Phase 4 (Architecture)**     | WebSocket-based transport (eliminates pickle), safetensors serialization, sandboxed deserialization |

---

## 7. Comparative Analysis

### 7.1 Approach Comparison Matrix

| Criterion                    | A: WebSocket                             | B: Enhanced MP                         | C: Hybrid FT+WS                      |
|------------------------------|------------------------------------------|----------------------------------------|--------------------------------------|
| **Local performance**        | No change (keep MP)                      | No change (keep MP)                    | Better (zero-copy threads)           |
| **Remote performance**       | Good (WS overhead ~1-5ms/msg)            | Good (MP proxy overhead ~0.1ms)        | Good (same as A for remote)          |
| **Memory efficiency**        | Same as current                          | Same as current                        | Much better (~1.5GB savings)         |
| **Security**                 | Excellent (native TLS, no pickle)        | Moderate (TLS wrapping complex)        | Excellent (same as A for remote)     |
| **Complexity**               | Moderate (new WS endpoint)               | Low (evolves existing code)            | High (two tiers + fallback)          |
| **Dynamic workers**          | Excellent (WS connect/disconnect)        | Good (via control queue)               | Excellent (same as A for remote)     |
| **Intermittent connections** | Excellent (WS reconnect natural)         | Moderate (MP reconnect complex)        | Excellent (same as A for remote)     |
| **Worker code weight**       | Lightweight (websockets + numpy + torch) | Moderate (cloudpickle + numpy + torch) | Lightweight (same as A)              |
| **Maturity risk**            | Low (WebSocket is stable)                | Low (BaseManager is stable)            | HIGH (free-threading experimental)   |
| **Migration effort**         | Medium (new endpoint + protocol)         | Low (extends existing)                 | High (thread safety audit + WS)      |
| **Scalability**              | High (async WS can handle many conns)    | Moderate (BaseManager single-threaded) | High (same as A for remote)          |
| **Cross-platform**           | Excellent (WebSocket is universal)       | Good (MP context varies by OS)         | Excellent for remote, Good for local |

### 7.2 Decision Factors

**Strongest case for Approach A (WebSocket)**:

- Security (eliminates pickle vector entirely if using structured serialization)
- Cross-platform compatibility (WebSocket is universal)
- Dynamic worker management (natural fit for WebSocket lifecycle)
- Scalability (async can handle many connections)
- Existing infrastructure (FastAPI already has WebSocket patterns)

**Strongest case for Approach B (Enhanced MP)**:

- Minimal disruption (local path unchanged, small delta)
- Lowest migration effort (extends existing code)
- Python stdlib foundation (only adds cloudpickle)
- Proven technology (BaseManager is well-understood)

**Strongest case for Approach C (Hybrid)**:

- Best local performance (zero-copy, zero-serialization)
- Memory efficiency (~1.5GB savings for 8-worker pool)
- Future-forward (positions for Python 3.14+ ecosystem)
- Best of both worlds when free-threading is stable

### 7.3 Risk Assessment

| Risk                          | A                      | B                           | C                           |
|-------------------------------|------------------------|-----------------------------|-----------------------------|
| Free-threading instability    | N/A                    | N/A                         | HIGH                        |
| PyTorch compatibility         | N/A                    | N/A                         | HIGH                        |
| Pickle code execution         | LOW (can avoid pickle) | HIGH (cloudpickle required) | LOW (can avoid pickle)      |
| BaseManager scalability       | N/A                    | MEDIUM                      | N/A                         |
| TLS implementation complexity | LOW (native WSS)       | HIGH (socket wrapping)      | LOW (native WSS for remote) |
| Test matrix size              | MODERATE               | LOW                         | HIGH (2x2 matrix)           |

---

## 8. Recommendations

### 8.1 Primary Recommendation: Approach A (WebSocket) with Phased Rollout

> **NOTE**: This recommendation was revised during validation. See Section 12.4 for details.

**Rationale**: Approach A delivers the highest-value improvement (reliable remote workers) with proven technology (WebSocket is stable, well-supported, and already used in the codebase). The existing multiprocessing local path (RC-4 persistent pool) is already well-optimized and should not be changed.

**Why not C (Hybrid)**: Free-threading is not currently feasible -- the installed Python 3.14 is a standard GIL-enabled build, and PyTorch has no official free-threading support. The free-threading local tier is deferred to a future iteration when the ecosystem matures.

**Why not B (Enhanced MP)**: Approach B's TLS wrapping of BaseManager is fragile (requires socket monkey-patching or external tunneling) and `cloudpickle` introduces the same arbitrary code execution risk it tries to solve. Furthermore, RC-2 already broke the BaseManager remote path by switching to direct `mp.Queue`, so the existing remote infrastructure needs replacement regardless.

**Why A**: WebSocket provides native TLS, standard authentication patterns, firewall-friendly single-port access, and reuses the existing FastAPI WebSocket infrastructure. The serialization protocol uses structured JSON + binary tensors (no pickle), eliminating the primary security attack vector.

### 8.2 Implementation Strategy: Five Phases

> **NOTE**: Phase structure revised during validation. See Section 12.5 for details.

#### Phase 1a: Security Fixes (Critical, Days of Work)

**Scope**: Fix critical security vulnerabilities in the existing multiprocessing path.

**Deliverables**:

- Replace hardcoded authkey with runtime-generated secrets
- Add restricted unpickler for result queue deserialization (empirically validated allowlist)
- Add result validation in `_collect_training_results()` (type, bounds, NaN/Inf, shape, magnitude)
- Fix timing-attack-vulnerable API key comparison with `hmac.compare_digest()`
- Add queue size limits (`maxsize` parameter)

#### Phase 1b: WebSocket Remote Worker Infrastructure

**Scope**: Implement Approach A's WebSocket remote worker system.

**Deliverables**:

- Implement `/ws/v1/workers` WebSocket endpoint on cascor server
- Implement `WorkerRegistry`, `WorkerCoordinator`
- Implement structured serialization protocol (JSON + binary tensor frames, no pickle)
- Add API key header authentication (matching existing WS patterns)
- Add Host header validation, Origin rejection
- Add heartbeat protocol and worker health tracking
- Add 100MB max WebSocket frame size limit
- Add tensor shape/dtype validation against expected dimensions

#### Phase 2: Remote Worker Agent

**Scope**: Rewrite `juniper-cascor-worker` as a WebSocket-based worker.

**Deliverables**:

- `CascorWorkerAgent` class using WebSocket (no cascor imports for connection)
- Built-in `CandidateUnit` training function (shipped with package, not serialized)
- WebSocket connection management with exponential backoff reconnection
- Cross-platform CLI (use `threading.Event.wait()` instead of `signal.pause()`)
- Worker registration with capability reporting
- Per-worker connection deduplication (one WebSocket per `worker_id`)
- `--legacy` flag for backward compatibility

#### Phase 3: Unified Task Distribution + Testing

**Scope**: Integrate local multiprocessing and remote WebSocket workers through a unified interface.

**Deliverables**:

- `TaskDistributor` abstracting local/remote execution
- Local-first scheduling (local workers get priority, remote gets overflow)
- Task timeout and reassignment (failed remote tasks fall back to local)
- Mixed-tier result collection via `multiprocessing.Queue`
- Performance benchmarking (local-only vs local+remote)
- Cross-platform CI matrix (Linux, macOS, Windows)
- Graceful degradation test (remote enabled, no workers connected)

#### Phase 4: Security Hardening + Production Readiness

**Scope**: Production security and operational readiness.

**Deliverables**:

- JWT token lifecycle (issuance CLI, rotation, in-band refresh, revocation)
- Mutual TLS with per-worker certificates (optional enhancement)
- Certificate generation tooling (ED25519, 365-day worker certs)
- Correlation cross-verification for top-K candidates
- Per-worker metrics and anomaly detection
- Result provenance tracking (which worker produced which cascade layer)
- Comprehensive audit logging
- Documentation for distributed deployment

#### Future: Free-Threading Local Tier

**Scope**: When PyTorch officially supports free-threaded Python.

**Deliverables**:

- `detect_free_threading()` utility
- `LocalThreadPool` class
- Thread safety audit of cascor codebase
- Automatic fallback to multiprocessing

### 8.3 Reasoning Behind Selection

1. **Phased approach minimizes risk**: Phase 1 delivers a working distributed system using proven technology (WebSocket). Phase 2 adds the experimental benefit (free-threading) with automatic fallback.

2. **Each phase is independently valuable**: Phase 1 alone solves the distributed worker requirements. Phase 2 alone improves local performance. They compose well but don't depend on each other.

3. **Security first**: Phase 1 includes all critical security fixes. Remote workers are never exposed without TLS and authentication.

4. **Existing code preserved**: The RC-4 persistent worker pool is the fallback path for both "no remote workers" and "GIL enabled" scenarios. It is never modified, only wrapped.

5. **Future-forward**: The architecture positions for a world where free-threaded Python is stable, while not betting on it.

---

## 9. Implementation Plan

### 9.1 Phase 1: Security Foundations + WebSocket Remote Tier

#### 9.1.1 Security Fixes (juniper-cascor)

**File**: `src/cascor_constants/constants_model/constants_model.py`

- Remove hardcoded `_PROJECT_MODEL_AUTHKEY` default
- Add validation requiring explicit authkey configuration

**File**: `src/cascade_correlation/cascade_correlation.py`

- Add `RestrictedUnpickler` for result queue deserialization
- Add `_validate_result()` method for `CandidateTrainingResult` verification
- Add `maxsize` parameter to queue creation factories
- Add result bounds checking in `_collect_training_results()`

#### 9.1.2 WebSocket Worker Endpoint (juniper-cascor)

**New file**: `src/api/websocket/worker_stream.py`

- WebSocket handler for `/ws/v1/workers`
- JWT authentication on connection
- Binary message frame handling
- Task assignment and result collection

**New file**: `src/api/workers/registry.py`

- `WorkerRegistry` class: thread-safe worker tracking
- `WorkerRegistration` dataclass: ID, capabilities, heartbeat, health score
- Registration/deregistration with lifecycle events

**New file**: `src/api/workers/coordinator.py`

- `WorkerCoordinator` class: task distribution and result aggregation
- Health monitoring thread
- Task timeout and reassignment logic

**New file**: `src/api/workers/protocol.py`

- Message format definitions (task assignment, result submission, heartbeat)
- Tensor serialization/deserialization helpers (numpy arrays to/from bytes)
- Protocol version negotiation

**Modified file**: `src/cascade_correlation/cascade_correlation.py`

- Add `_init_remote_workers()` method
- Modify `_execute_parallel_training()` to support dual-path dispatch (local + remote)
- Add `_collect_from_both_sources()` method for unified result collection

**Modified file**: `src/cascade_correlation/cascade_correlation_config/cascade_correlation_config.py`

- Add remote worker configuration fields:
  - `enable_remote_workers: bool = False`
  - `ws_worker_port: int = 8200` (reuses existing FastAPI port)
  - `ws_worker_token_secret: str = ""` (required if remote workers enabled)
  - `heartbeat_timeout: float = 30.0`
  - `task_reassignment_timeout: float = 120.0`

#### 9.1.3 Remote Worker Agent (juniper-cascor-worker)

**Rewritten file**: `juniper_cascor_worker/worker.py`

- `CascorWorkerAgent` class using WebSocket
- No cascor imports required
- Automatic reconnection with exponential backoff
- Heartbeat thread
- Task execution via deserialized training function

**New file**: `juniper_cascor_worker/ws_connection.py`

- WebSocket connection management
- TLS configuration
- Reconnection logic

**New file**: `juniper_cascor_worker/task_executor.py`

- Generic task execution engine
- Tensor deserialization
- Result serialization

**Modified file**: `juniper_cascor_worker/config.py`

- Add WebSocket configuration fields:
  - `server_url: str` (replaces `manager_host`/`manager_port`)
  - `auth_token: str`
  - `tls_cert: str | None`
  - `tls_key: str | None`
  - `tls_ca: str | None`
  - `heartbeat_interval: float = 10.0`
  - `reconnect_backoff_base: float = 1.0`
  - `reconnect_backoff_max: float = 60.0`

**Modified file**: `juniper_cascor_worker/cli.py`

- Add `--server-url`, `--auth-token`, `--tls-cert`, `--tls-key`, `--tls-ca` arguments
- Keep `--legacy` flag for backward compatibility with BaseManager path

### 9.2 Phase 2: Free-Threading Local Tier

#### 9.2.1 Free-Threading Detection (juniper-cascor)

**New file**: `src/parallelism/__init__.py`

- `detect_free_threading()` function
- `FREE_THREADING_AVAILABLE` module constant

**New file**: `src/parallelism/local_thread_pool.py`

- `LocalThreadPool` class
- Thread-based worker loop (mirrors `_worker_loop` but with shared memory)
- Shutdown via `threading.Event` + sentinels

#### 9.2.2 Integration (juniper-cascor)

**Modified file**: `src/cascade_correlation/cascade_correlation.py`

- Refactor `_init_multiprocessing()` to `_init_parallelism()`
- Add `_init_thread_pool()` method
- Add `_ensure_thread_pool()` method
- Modify `_ensure_worker_pool()` to dispatch to thread or process pool

#### 9.2.3 Thread Safety Audit (juniper-cascor)

**Files to audit**:

- `src/cascade_correlation/cascade_correlation.py` -- module-level mutable globals
- `src/candidate_unit/candidate_unit.py` -- `shared_object_dict`, global RNG usage
- `src/cascade_correlation/activation_with_derivative.py` -- `ACTIVATION_MAP` (read-only, safe)

**Required changes**:

- Replace `random.randint()` with per-task seed generation in main thread
- Replace `torch.manual_seed()` in `CandidateUnit` with `torch.Generator` instances
- Protect or eliminate `shared_object_dict` mutable global
- Set `torch.set_num_threads(1)` globally before creating thread pool

### 9.3 Phase 3: Unified Task Distribution

**New file**: `src/parallelism/task_distributor.py`

- `TaskDistributor` class
- Local-first scheduling
- Cross-tier result collection
- Task timeout and reassignment

**Modified file**: `src/cascade_correlation/cascade_correlation.py`

- Replace direct pool usage with `TaskDistributor` interface
- Add capacity-aware task distribution
- Add mixed-tier result collection

### 9.4 Phase 4: Security Hardening

**New directory**: `scripts/tls/`

- Certificate generation scripts
- CA management tooling

**New file**: `src/api/workers/security.py`

- mTLS integration
- Token rotation
- Connection rate limiting
- Anomaly detection

**New file**: `src/api/workers/audit.py`

- Security event logging
- Per-worker metrics tracking

---

## 10. Testing Strategy

### 10.1 Unit Tests

#### Phase 1 Tests

| Test                        | Description                                            |
|-----------------------------|--------------------------------------------------------|
| `test_restricted_unpickler` | Verify allowed classes pass, blocked classes raise     |
| `test_result_validation`    | Verify bounds checking, type checking, task tracking   |
| `test_worker_registry`      | Register, heartbeat, unregister, stale detection       |
| `test_worker_coordinator`   | Task assignment, timeout, reassignment                 |
| `test_ws_protocol`          | Message encoding/decoding, binary frames               |
| `test_ws_worker_agent`      | Connection, task execution, result submission          |
| `test_reconnection`         | Exponential backoff, max retries, successful reconnect |
| `test_heartbeat`            | Regular heartbeat, missed heartbeat detection          |

#### Phase 2 Tests

| Test                             | Description                                                 |
|----------------------------------|-------------------------------------------------------------|
| `test_detect_free_threading`     | GIL detection on various Python builds                      |
| `test_local_thread_pool`         | Pool creation, task submission, result collection, shutdown |
| `test_thread_safety_queue`       | Concurrent put/get from multiple threads                    |
| `test_thread_pool_fallback`      | Automatic fallback to multiprocessing when GIL enabled      |
| `test_torch_generator_isolation` | Per-thread RNG produces different sequences                 |
| `test_shared_tensor_read_only`   | Multiple threads reading same tensor concurrently           |

#### Phase 3 Tests

| Test                               | Description                                          |
|------------------------------------|------------------------------------------------------|
| `test_task_distributor_local_only` | All tasks to local pool when no remote workers       |
| `test_task_distributor_mixed`      | Tasks split between local and remote                 |
| `test_task_redistribution`         | Tasks from failed remote workers reassigned to local |
| `test_local_first_scheduling`      | Local workers always get priority                    |
| `test_unified_result_collection`   | Results from both tiers collected correctly          |

#### Phase 4 Tests

| Test                       | Description                                      |
|----------------------------|--------------------------------------------------|
| `test_mtls_authentication` | Valid certs accepted, invalid rejected           |
| `test_token_rotation`      | Expired tokens rejected, renewed tokens accepted |
| `test_rate_limiting`       | Connection flood rejected                        |
| `test_anomaly_detection`   | Suspicious correlation patterns flagged          |
| `test_audit_logging`       | Security events properly logged                  |

### 10.2 Integration Tests

| Test                                      | Description                                              | Scope      |
|-------------------------------------------|----------------------------------------------------------|------------|
| `test_local_training_unchanged`           | Existing local training produces identical results       | Regression |
| `test_remote_worker_training`             | Remote worker completes candidate training via WebSocket | Phase 1    |
| `test_mixed_local_remote`                 | Tasks distributed across local and remote workers        | Phase 3    |
| `test_worker_join_mid_training`           | Worker joins during active training round                | Phase 1    |
| `test_worker_disconnect_mid_task`         | Worker disconnects; task reassigned and completed        | Phase 1    |
| `test_intermittent_connection`            | Worker reconnects after network disruption               | Phase 1    |
| `test_free_threaded_training_correctness` | Thread pool produces same results as multiprocessing     | Phase 2    |
| `test_cross_platform_worker`              | Workers on different OS produce valid results            | Phase 1    |

### 10.3 Performance Tests

| Test                               | Description                                       | Metric              |
|------------------------------------|---------------------------------------------------|---------------------|
| `benchmark_local_mp_vs_threads`    | Compare multiprocessing vs thread pool throughput | Tasks/second        |
| `benchmark_serialization_overhead` | Measure WebSocket serialization cost              | ms/task             |
| `benchmark_memory_usage`           | Compare memory usage: MP vs threads               | MB                  |
| `benchmark_worker_scalability`     | Throughput vs number of remote workers            | Tasks/second/worker |
| `benchmark_reconnection_latency`   | Time from disconnect to reconnect                 | ms                  |

### 10.4 Security Tests

| Test                                         | Description                                  |
|----------------------------------------------|----------------------------------------------|
| `test_unauthorized_connection_rejected`      | Connection without valid token/cert rejected |
| `test_malformed_result_rejected`             | Crafted results with invalid schema rejected |
| `test_oversized_payload_rejected`            | Payloads exceeding size limit rejected       |
| `test_replay_attack_prevented`               | Replayed authentication tokens rejected      |
| `test_restricted_unpickler_blocks_os_system` | Pickle payload with `os.system` blocked      |

### 10.5 Regression Tests

| Test                                | Description                                            |
|-------------------------------------|--------------------------------------------------------|
| `test_existing_local_training_path` | All existing tests pass with no modification           |
| `test_sequential_fallback`          | Sequential training still works when parallel disabled |
| `test_cascor_worker_legacy_mode`    | Legacy `--cascor-path` mode still works                |
| `test_client_library_unchanged`     | juniper-cascor-client tests pass without modification  |

---

## 11. Risks and Guardrails

### 11.1 Technical Risks

| Risk                                              | Probability | Impact   | Mitigation                                                           |
|---------------------------------------------------|-------------|----------|----------------------------------------------------------------------|
| Free-threading causes subtle data corruption      | Medium      | Critical | Automatic fallback to MP; extensive correctness testing              |
| PyTorch not stable on free-threaded Python        | High        | High     | Runtime detection; `CASCOR_FORCE_MULTIPROCESSING` override           |
| WebSocket overhead reduces training throughput    | Low         | Medium   | Measure overhead vs task time; only use remote for overflow          |
| BaseManager TLS wrapping breaks on Python updates | Medium      | Medium   | Use WSS instead of wrapping MP sockets                               |
| cloudpickle version mismatch across machines      | Medium      | High     | Standardize Python version; use structured serialization for WS path |

### 11.2 Operational Risks

| Risk                                | Probability | Impact | Mitigation                                                  |
|-------------------------------------|-------------|--------|-------------------------------------------------------------|
| Certificate management complexity   | Medium      | Medium | Automated cert generation scripts; 365-day worker certs     |
| Remote worker deployment complexity | Medium      | Medium | pip-installable worker package; single CLI command to start |
| Increased monitoring burden         | Low         | Low    | Structured audit logging; dashboard integration             |

### 11.3 Guardrails

#### Performance Guardrails

- **Regression gate**: CI benchmark comparing local training throughput against baseline. Fail build if regression exceeds 5%.
- **Task overhead cap**: Log warning if per-task overhead exceeds 1% of task execution time.
- **Memory budget**: Log warning if thread pool memory exceeds expected bounds.

#### Stability Guardrails

- **Automatic fallback**: Free-threading disabled if `detect_free_threading()` returns `False` or if PyTorch raises RuntimeError during initialization.
- **Worker health threshold**: Workers with health score < 0.3 are disconnected and their tasks reassigned.
- **Training round timeout**: If a training round exceeds `3x` the expected duration, abandon remote results and complete with local workers only.

#### Security Guardrails

- **No default authkey**: Application refuses to start if authkey is the hardcoded default.
- **TLS required for remote**: Remote workers rejected if TLS is not configured.
- **Result validation mandatory**: All results validated before incorporation into training state.
- **Rate limiting**: Connection rate limit of 10 connections/minute/IP.

---

## Appendix A: File Impact Summary

### juniper-cascor (Modified Files)

| File                                                                               | Changes                                                     |
|------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `src/cascade_correlation/cascade_correlation.py`                                   | Dual-path dispatch, result validation, restricted unpickler |
| `src/cascade_correlation/cascade_correlation_config/cascade_correlation_config.py` | Remote worker config fields                                 |
| `src/cascor_constants/constants_model/constants_model.py`                          | Remove hardcoded authkey                                    |
| `src/api/app.py`                                                                   | Mount worker WebSocket endpoint                             |
| `src/candidate_unit/candidate_unit.py`                                             | Thread-safe RNG (Phase 2)                                   |

### juniper-cascor (New Files)

| File                                   | Purpose                              |
|----------------------------------------|--------------------------------------|
| `src/api/websocket/worker_stream.py`   | Worker WebSocket handler             |
| `src/api/workers/__init__.py`          | Workers package                      |
| `src/api/workers/registry.py`          | Worker registry                      |
| `src/api/workers/coordinator.py`       | Task distribution and lifecycle      |
| `src/api/workers/protocol.py`          | Message format and serialization     |
| `src/api/workers/security.py`          | Authentication, validation (Phase 4) |
| `src/api/workers/audit.py`             | Security audit logging (Phase 4)     |
| `src/parallelism/__init__.py`          | Free-threading detection (Phase 2)   |
| `src/parallelism/local_thread_pool.py` | Thread pool (Phase 2)                |
| `src/parallelism/task_distributor.py`  | Unified distribution (Phase 3)       |

### juniper-cascor-worker (Modified Files)

| File                              | Changes                           |
|-----------------------------------|-----------------------------------|
| `juniper_cascor_worker/worker.py` | Rewrite as WebSocket worker agent |
| `juniper_cascor_worker/config.py` | WebSocket config fields           |
| `juniper_cascor_worker/cli.py`    | New CLI arguments, legacy mode    |
| `pyproject.toml`                  | Add `websockets` dependency       |

### juniper-cascor-worker (New Files)

| File                                     | Purpose                         |
|------------------------------------------|---------------------------------|
| `juniper_cascor_worker/ws_connection.py` | WebSocket connection management |
| `juniper_cascor_worker/task_executor.py` | Generic task execution engine   |

### juniper-ml (This Repository)

| File                               | Purpose            |
|------------------------------------|--------------------|
| `notes/CASCOR_CONCURRENCY_PLAN.md` | This plan document |

---

## Appendix B: Dependency Changes

### juniper-cascor

```toml
# pyproject.toml additions
[project.optional-dependencies]
remote = ["PyJWT>=2.0.0"]  # JWT token generation for worker auth
```

### juniper-cascor-worker

```toml
# pyproject.toml changes
dependencies = [
    "numpy>=1.24.0",
    "torch>=2.0.0",
    "websockets>=11.0",   # NEW: WebSocket client
]
```

Note: `cloudpickle` is NOT required in the recommended approach (Approach C). The WebSocket path uses structured serialization (numpy arrays to bytes + JSON envelope) instead of pickle-based serialization.

---

## Appendix C: Configuration Reference

### Server-Side (juniper-cascor)

| Setting                     | Type  | Default    | Description                                                |
|-----------------------------|-------|------------|------------------------------------------------------------|
| `enable_remote_workers`     | bool  | `False`    | Enable WebSocket worker endpoint                           |
| `ws_worker_token_secret`    | str   | *required* | JWT signing secret (must be set if remote workers enabled) |
| `heartbeat_timeout`         | float | `30.0`     | Seconds before marking worker stale                        |
| `task_reassignment_timeout` | float | `120.0`    | Seconds before reassigning unfinished remote task          |
| `max_remote_workers`        | int   | `50`       | Maximum simultaneous remote worker connections             |
| `parallelism_mode`          | str   | `"auto"`   | `"auto"`, `"multiprocessing"`, `"threading"`               |

### Worker-Side (juniper-cascor-worker)

| Setting                  | Type  | Default    | Description                                     |
|--------------------------|-------|------------|-------------------------------------------------|
| `server_url`             | str   | *required* | WSS URL (e.g., `wss://host:8200/ws/v1/workers`) |
| `auth_token`             | str   | *required* | JWT authentication token                        |
| `num_workers`            | int   | `1`        | Number of local worker threads/processes        |
| `heartbeat_interval`     | float | `10.0`     | Seconds between heartbeat messages              |
| `reconnect_backoff_base` | float | `1.0`      | Initial reconnection delay                      |
| `reconnect_backoff_max`  | float | `60.0`     | Maximum reconnection delay                      |
| `tls_cert`               | str   | `None`     | Client certificate path (for mTLS)              |
| `tls_key`                | str   | `None`     | Client key path                                 |
| `tls_ca`                 | str   | `None`     | CA certificate path                             |

---

## 12. Validation Findings and Plan Revisions

This section documents findings from independent validation of the plan by three specialized review agents (architecture, completeness, security). All critical findings have been addressed with plan revisions.

### 12.1 Critical Findings

#### FINDING 1: Free-Threading is Not Currently Feasible (FATAL)

**Source**: Architecture validation

The installed Python 3.14.3 (conda-forge) is a **standard GIL-enabled build**, not a free-threaded build:

- `sysconfig.get_config_var('Py_GIL_DISABLED')` returns `0`
- `sys._is_gil_enabled()` returns `True`
- `sys.flags.nogil` attribute is not present

Furthermore, **PyTorch has no official support for free-threaded Python**. PyTorch's C++ extensions use thread-local state and assume GIL protection. Running PyTorch under a no-GIL interpreter would produce crashes or data corruption.

**REVISION**: Approach C's free-threading local tier is **deferred** to a future plan iteration. The recommended approach is revised to:

- **Phase 1-3**: Implement Approach A (WebSocket remote workers) with existing multiprocessing for local workers
- **Phase 4 (future)**: Re-evaluate free-threading when PyTorch and numpy officially support it

The `detect_free_threading()` utility function is kept as a readiness check but no thread pool implementation is included in this plan's scope.

#### FINDING 2: RC-2 Broke the Existing Remote Worker Path

**Source**: Architecture validation

The RC-2 fix replaced `BaseManager`-proxied queues with direct `multiprocessing.Queue` objects (`self._mp_ctx.Queue()`). Direct `multiprocessing.Queue` objects use OS pipes and **cannot be shared over the network**. The existing `RemoteWorkerClient` and `CandidateTrainingWorker` both call `self.manager.get_task_queue()` to obtain proxied queue references, but the current production code path bypasses the manager entirely.

**Implication**: The existing `juniper-cascor-worker` package is **already non-functional** for remote workers. The `CandidateTrainingManager(BaseManager)` class is still defined but is not used in the current hot path.

**REVISION**: The plan explicitly positions the WebSocket architecture as a **replacement** for the broken BaseManager remote path, not a parallel addition. The legacy `CandidateTrainingManager`, `RemoteWorkerClient`, and BaseManager-based `CandidateTrainingWorker` are deprecated.

#### FINDING 3: Pickle Contradiction in WebSocket Path

**Source**: Security validation

The plan simultaneously states:

- "No pickle dependency for remote path -- eliminates arbitrary code execution vector" (Section 5.1)
- "Candidate training function: Serialized via cloudpickle" (Section 5.1)

These are contradictory. If `cloudpickle` serializes the training function, pickle is not eliminated.

**REVISION**: The WebSocket path uses **structured serialization only** -- no pickle, no cloudpickle. The approach:

1. **Server sends task data as JSON + binary tensors** (candidate config, hyperparameters, training inputs as numpy arrays)
2. **Worker executes a built-in training function** (shipped with the `juniper-cascor-worker` package) rather than receiving serialized code
3. **Worker returns results as JSON + binary tensors** (correlation, weights, bias, metrics)
4. **Server reconstructs `CandidateTrainingResult`** from the structured response

This means the worker **does** need the `CandidateUnit` training logic shipped as part of its package. The training function is **code** distributed via pip, not **data** serialized via pickle. This is a middle ground: the worker needs `juniper-cascor-worker` installed (which includes the training function), but does NOT need the full cascor codebase.

#### FINDING 4: RestrictedUnpickler Allowlist Incomplete

**Source**: Security validation

The allowlist for the existing multiprocessing path must include ~25+ types used by `CandidateTrainingResult` and `CandidateUnit` serialization. The empirically correct allowlist includes:

```python
ALLOWED_CLASSES = {
    # Application types
    ('candidate_unit.candidate_unit', 'CandidateTrainingResult'),
    ('candidate_unit.candidate_unit', 'CandidateUnit'),
    ('candidate_unit.candidate_unit', 'ActivationWithDerivative'),
    # Python builtins
    ('builtins', 'list'), ('builtins', 'dict'), ('builtins', 'set'),
    ('builtins', 'tuple'), ('builtins', 'float'), ('builtins', 'int'),
    ('builtins', 'bool'), ('builtins', 'str'), ('builtins', 'bytes'),
    # PyTorch tensor reconstruction
    ('torch._utils', '_rebuild_tensor_v2'),
    ('torch', 'Tensor'), ('torch', 'Size'),
    ('torch.storage', 'TypedStorage'), ('torch.storage', 'UntypedStorage'),
    ('torch', 'float32'), ('torch', 'float64'), ('torch', 'int64'),
    # Collections and codecs
    ('collections', 'OrderedDict'),
    ('_codecs', 'encode'),
    # Numpy
    ('numpy', 'ndarray'), ('numpy', 'dtype'),
    ('numpy.core.multiarray', '_reconstruct'),
}
```

**REVISION**: The allowlist must be **empirically validated** by pickling a real `CandidateTrainingResult` through `pickletools.dis()` and adding a regression test.

#### FINDING 5: JWT Authentication Must Use Headers, Not Query Params

**Source**: Architecture + Security validation

JWT in query parameters exposes tokens in server access logs, proxy logs, browser history. For machine-to-machine worker connections, use the `Authorization: Bearer <token>` header in the WebSocket upgrade request.

**REVISION**: The plan mandates API key header authentication (matching the existing `/ws/training` and `/ws/control` patterns) for Phase 1, with mTLS as an optional enhancement for production deployments.

### 12.2 High-Severity Findings

#### FINDING 6: Missing JWT Lifecycle

The plan does not specify token issuance, rotation, expiry-during-connection, or revocation.

**REVISION**: JWT lifecycle defined as:

- **Issuance**: CLI command generates time-limited tokens (24h dev, 1h prod) signed with `ws_worker_token_secret`
- **Claims**: `worker_id`, `iat`, `exp`, `jti` (unique ID for revocation)
- **Refresh**: Server sends `token_refresh` message at 80% lifetime. Worker must acknowledge.
- **Revocation**: In-memory set of revoked `jti` values checked on each message receipt
- **Expiry during connection**: Server checks on each heartbeat cycle. Expired tokens trigger disconnect with code 4002.

#### FINDING 7: Missing Wire Protocol for CandidateTrainingResult

The plan's "numpy arrays + JSON envelopes" approach does not address the complexity of returning a full `CandidateUnit` object.

**REVISION**: The wire protocol explicitly decomposes results:

```json
// Worker -> Server: Task result
{
    "type": "task_result",
    "task_id": "uuid",
    "candidate_id": 3,
    "correlation": 0.847,
    "success": true,
    "epochs_completed": 200,
    "activation_name": "sigmoid",
    "all_correlations": [0.1, 0.3, 0.5, 0.847],
    "numerator": 1.234,
    "denominator": 5.678,
    "error_message": null
}
// Followed by binary frames:
// Frame 1: weights tensor (numpy array bytes, shape + dtype header)
// Frame 2: bias tensor
// Frame 3: norm_output tensor (optional)
// Frame 4: norm_error tensor (optional)
```

The server reconstructs `CandidateTrainingResult` (with a `CandidateUnit`) from these structured primitives. **No pickle involved.**

#### FINDING 8: Missing Mid-Training Worker Join Mechanism

The plan says workers can "join mid-training" but doesn't explain the signaling mechanism from the async WebSocket handler to the synchronous training thread.

**REVISION**: The `WorkerCoordinator` maintains a thread-safe `available_workers` counter. The `TaskDistributor` checks this counter before each task assignment. When a new worker joins (via WebSocket handler), the coordinator increments the counter. The training thread does not need to be signaled -- it simply finds more workers available when distributing the next batch of tasks. Workers that join mid-round wait for the next round (no task rebalancing within a round).

#### FINDING 9: Phase 1 Should Be Split

Security fixes (restricted unpickler, result validation, authkey fix) are simpler and higher-priority than the full WebSocket implementation.

**REVISION**: Phase 1 split into:

- **Phase 1a**: Security fixes for existing multiprocessing path (days of work)
- **Phase 1b**: WebSocket remote worker system (weeks of work)

#### FINDING 10: Existing API Key Comparison is Timing-Attack Vulnerable

The current `api_key in self._api_keys` uses Python's `in` operator on a `set`, which is NOT constant-time.

**REVISION**: Fix API key validation to use `hmac.compare_digest()`:

```python
import hmac
def validate(self, api_key: str | None) -> bool:
    if not self._enabled:
        return True
    if api_key is None:
        return False
    return any(hmac.compare_digest(api_key, k) for k in self._api_keys)
```

### 12.3 Medium-Severity Findings

| Finding                                                        | Resolution                                                                             |
|----------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `signal.pause()` crashes on Windows                            | Worker CLI rewrite uses `threading.Event.wait()` instead                               |
| Missing msgpack/zstd from dependency lists                     | Removed from protocol; use raw numpy `.tobytes()` + JSON envelope                      |
| Python version contradiction (3.11 vs 3.14)                    | Worker `requires-python` updated to `>=3.14`                                           |
| No memory exhaustion protection for binary frames              | Add 100MB max WebSocket frame size; validate tensor shapes against expected dimensions |
| No worker connection deduplication                             | One active WebSocket per `worker_id`; new connections close older ones                 |
| No per-worker result rate limiting                             | Max 1 result per dispatched task; reject undispatched task IDs                         |
| No Origin header validation on worker endpoint                 | Reject connections carrying `Origin` header (workers are machine-to-machine)           |
| No Host header validation                                      | Validate `Host` against configured allowlist                                           |
| Missing `sequential` option in `parallelism_mode`              | Added to config options                                                                |
| No graceful degradation test (remote enabled, no workers)      | Added to test strategy                                                                 |
| No cross-platform CI description                               | Added note for CI matrix (Linux, macOS, Windows)                                       |
| Missing backward compatibility strategy for `remote_client.py` | Deprecated in favor of WebSocket path; retained with deprecation warning               |

### 12.4 Revised Recommendation

**Primary Recommendation: Approach A (WebSocket-Based Distributed Workers) with phased rollout.**

The original recommendation of Approach C (Hybrid) is revised because:

1. Free-threading is not feasible with current Python 3.14 builds and PyTorch
2. The multiprocessing local path (RC-4 persistent pool) is already well-optimized
3. The primary value of this plan is enabling **remote workers**, not improving local performance

The revised approach:

- **Local workers**: Keep existing multiprocessing persistent pool (RC-4), unchanged
- **Remote workers**: New WebSocket-based system (Approach A)
- **Future**: Free-threading local tier when PyTorch supports it (Approach C, Phase 2)

### 12.5 Revised Phase Structure

| Phase      | Scope                                                                                                                  | Effort |
|------------|------------------------------------------------------------------------------------------------------------------------|--------|
| **1a**     | Security fixes for existing MP path (restricted unpickler, result validation, authkey, timing-safe API key comparison) | Days   |
| **1b**     | WebSocket worker endpoint, registry, coordinator, protocol                                                             | Weeks  |
| **2**      | Remote worker agent (juniper-cascor-worker rewrite with WebSocket)                                                     | Weeks  |
| **3**      | Unified TaskDistributor (local MP + remote WS), testing, benchmarking                                                  | Weeks  |
| **4**      | Security hardening (mTLS, cert management, audit logging, anomaly detection)                                           | Weeks  |
| **Future** | Free-threading local tier (when PyTorch supports it)                                                                   | TBD    |

### 12.6 Serialization Protocol Specification

The WebSocket wire protocol uses JSON control messages and binary WebSocket frames for tensor data.

#### Message Types (JSON)

**Server -> Worker: Task Assignment:**

```json
{
    "type": "task_assign",
    "task_id": "uuid",
    "round_id": "uuid",
    "candidate_index": 0,
    "candidate_data": {
        "input_size": 4,
        "activation_name": "sigmoid",
        "random_value_scale": 1.0,
        "candidate_uuid": "uuid",
        "candidate_seed": 42,
        "random_max_value": 1.0,
        "sequence_max_value": 1.0
    },
    "training_params": {
        "epochs": 200,
        "learning_rate": 0.01,
        "display_frequency": 100
    },
    "tensor_manifest": {
        "candidate_input": {"shape": [1000, 4], "dtype": "float32"},
        "y": {"shape": [1000, 1], "dtype": "float32"},
        "residual_error": {"shape": [1000, 1], "dtype": "float32"}
    }
}
```

Followed by binary frames (one per tensor in manifest order).

**Worker -> Server: Task Result:**

```json
{
    "type": "task_result",
    "task_id": "uuid",
    "candidate_id": 0,
    "candidate_uuid": "uuid",
    "correlation": 0.847,
    "success": true,
    "epochs_completed": 200,
    "activation_name": "sigmoid",
    "all_correlations": [0.1, 0.3, 0.847],
    "numerator": 1.234,
    "denominator": 5.678,
    "best_corr_idx": 199,
    "error_message": null,
    "tensor_manifest": {
        "weights": {"shape": [4], "dtype": "float32"},
        "bias": {"shape": [1], "dtype": "float32"},
        "norm_output": {"shape": [1000], "dtype": "float32"},
        "norm_error": {"shape": [1000], "dtype": "float32"}
    }
}
```

Followed by binary frames (one per tensor in manifest order).

**Heartbeat** (bidirectional)

```json
{"type": "heartbeat", "worker_id": "uuid", "timestamp": 1711000000.0}
```

**Worker Registration** (worker -> server, first message after connect)

```json
{
    "type": "register",
    "worker_id": "uuid",
    "capabilities": {
        "cpu_cores": 8,
        "gpu": false,
        "python_version": "3.14.3",
        "torch_version": "2.9.0",
        "numpy_version": "2.2.0",
        "os": "Linux"
    }
}
```

#### Binary Frame Format

Each binary frame is a raw numpy array in C-contiguous byte order:

```bash
[4 bytes: shape dimension count (uint32)]
[N * 4 bytes: shape values (uint32 each)]
[4 bytes: dtype string length (uint32)]
[M bytes: dtype string (utf-8)]
[remaining bytes: raw array data]
```

This is a simple, efficient format that avoids pickle entirely and can be decoded with only `numpy` and `struct`.

### 12.7 Result Validation Specification

All results from remote workers must pass these validation checks before acceptance:

1. **Schema validation**: JSON envelope has all required fields with correct types
2. **Task tracking**: `task_id` matches a dispatched, uncompleted task
3. **Bounds checking**: `0.0 <= correlation <= 1.0`
4. **Tensor shape validation**: Shapes match expected dimensions from the task's tensor manifest
5. **Tensor dtype validation**: All tensors are `float32`
6. **NaN/Inf checking**: No `NaN` or `Inf` values in any tensor
7. **Weight magnitude**: `max(abs(weights)) < 100.0` (configurable)
8. **Duplicate detection**: Same `task_id` not accepted twice
9. **Cross-verification (Phase 4)**: Server recomputes correlation for top-K candidates using own data
