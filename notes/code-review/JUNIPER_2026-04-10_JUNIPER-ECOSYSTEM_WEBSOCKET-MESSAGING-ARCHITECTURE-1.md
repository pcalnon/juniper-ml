# Canopy ↔ Cascor WebSocket & Messaging Architecture Analysis

**Date created**: 2026-04-10
**Author**: Claude Code (Opus 4.6, 1M context) on behalf of Paul Calnon
**Status**: v1.3 (post round-1 + round-2 + round-3 subagent integration) — STABLE
**Scope**: end-to-end messaging architecture between juniper-canopy, juniper-cascor-client, and juniper-cascor; WebSocket vs REST transport split per UI element; latency tolerance matrix; implementation plan for the gaps.
**Supersedes**: the premature deferral language in `CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` §6.0 (P5-RC-05 marked DEFERRED) and §3.5 (canopy `set_params` integration test marked WONT-DO). Both items are critical functionality, not won't-do work.

**Action required**: update `CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` §3.5 and §6.0 to reference this document and remove the WONT-DO/DEFERRED markings. PR #116 covers this.

**Primary audience**: engineer implementing Phases A-H. **Secondary**: future-Claude resuming the work after a thread handoff. **Tertiary**: PMs and stakeholders evaluating scope (read §0.1 TL;DR and §1 only).

---

## 0.1 TL;DR

The canopy ↔ cascor WebSocket pipeline is built on both sides but the dashboard ignores the WebSocket data and polls REST endpoints instead.
This is invisible at low training rates and breaks at production rates.
The P0 motivator is `/api/metrics/history` polling at 100 ms × ~300 KB/response = ~3 MB/s of pure waste per dashboard.
Fix is roughly 8.5 engineering days across three repos (cascor, canopy, juniper-cascor-client) with a phased plan in §9; calendar time including PR review and CI iteration is ~3 weeks.
The `set_params` WebSocket control path (canopy → cascor) is genuinely missing and is critical functionality, not won't-do work.
Browser-side verification uses Playwright (§8) plus the official Dash `dash_duo` test fixture, both feasible from a headless environment.

---

## 0.2 Table of Contents

- [§0 Document Conventions](#0-document-conventions)
- [§0.1 TL;DR](#01-tldr)
- [§0.2 Table of Contents](#02-table-of-contents)
- [§1 Executive Summary](#1-executive-summary)
- [§2 WebSocket Surface Inventory](#2-websocket-surface-inventory)
  - [§2.9 Security Model (REQUIRED before Phase D)](#29-security-model-required-before-phase-d)
- [§3 Bidirectional Message Contract](#3-bidirectional-message-contract)
- [§4 Nested vs Flat Data Structure Analysis](#4-nested-vs-flat-data-structure-analysis)
- [§5 Latency Tolerance Matrix](#5-latency-tolerance-matrix)
  - [§5.5 End-to-end Frame Budget](#55-end-to-end-frame-budget)
  - [§5.6 Production Latency Measurement Plan](#56-production-latency-measurement-plan)
- [§6 Transport Split Design](#6-transport-split-design)
  - [§6.4 Disconnection Taxonomy & Recovery](#64-disconnection-taxonomy--recovery)
  - [§6.5 Reconnection Protocol (sequence numbers + replay)](#65-reconnection-protocol-sequence-numbers--replay)
- [§7 Missing / Broken Pieces (Enumerated)](#7-missing--broken-pieces-enumerated)
- [§8 Browser-Side Verification Strategy](#8-browser-side-verification-strategy)
- [§9 Phased Implementation Plan](#9-phased-implementation-plan)
- [§10 Risk Register](#10-risk-register)
- [§11 Open Questions for Human Review](#11-open-questions-for-human-review)
- [§12 References](#12-references)

---

## 0. Document Conventions

- **Repos in scope**:
  - `juniper-cascor` — cascor server (FastAPI, async)
  - `juniper-cascor-client` — Python SDK that canopy uses to call cascor
  - `juniper-canopy` — dashboard application (FastAPI + Dash)
- **File:line references** are against `origin/main` HEAD as of 2026-04-10.
- **Verdict labels**:
  - **PRESENT** — feature exists and works as intended
  - **PARTIAL** — feature is partially implemented; some paths work, others don't
  - **MISSING** — feature does not exist
  - **BROKEN** — feature exists but does not function (dead code, broken wiring)
- **Severity labels (gaps in §7)**:
  - **P0** — blocks core canopy functionality OR is a security vulnerability
  - **P1** — blocks usability at production training speeds OR causes silent data loss
  - **P2** — required for complete contract; not blocking
  - **P3** — quality / hardening
- **Risk severity (§10)**: High / Medium / Low (qualitative; orthogonal to gap severity)
- **GAP-WS-NN** — enumerated gaps in the WebSocket pipeline; see §7. Each gap has a unique ID, severity, location, current state, target state, and remediation hook.
- **Identifier prefixes from prior reviews**:
  - **P5-RC-NN** — issues from `FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` (2026-03-28)
  - **CR-NNN** — issues from `CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md`
  - **NEW-NN** — issues surfaced during the 2026-04-09 Phase 1 verification pass
- **Latency budgets**: see §5 — distinguishes *control feedback latency* (slider→DOM, must be <16 ms, achieved by Dash clientside), *ack latency* (slider→backend ack, target by parameter class), and *effect observation latency* (slider→training-effect→chart-update, dominated by training step time).
- **Roles** (used consistently throughout):
  - **cascor server** — the FastAPI service in `juniper-cascor/`
  - **canopy adapter** — the Python code in `juniper-canopy/src/backend/cascor_service_adapter.py` that acts as a *client* of cascor
  - **canopy server** — the FastAPI/Dash application in `juniper-canopy/src/main.py` that acts as a *server* to the browser
  - **browser** — the Dash dashboard in the user's web browser, a *client* of canopy server

---

## 1. Executive Summary

### 1.1 Five primary findings

1. **The WebSocket infrastructure is ~60% built and largely unused.** All three layers exist:
   - Cascor server emits structured WebSocket messages (`/ws/training`, `/ws/control`)
   - Canopy adapter consumes them, normalizes them, re-broadcasts to canopy's own `/ws/training`
   - The browser opens WebSocket connections and receives messages
   ...but the dashboard's chart and panel components do not actually consume any of this data. They poll REST endpoints on a `dcc.Interval` timer instead. The result is that the dashboard works correctly at small training speeds but cannot keep up with production training rates because it has no real-time push path.

2. **There are TWO independent browser-side WebSocket clients, both dead-end.**
    - `juniper-canopy/src/frontend/assets/websocket_client.js` defines `window.cascorWS` and `window.cascorControlWS` that are auto-loaded by Dash but never referenced by any callback.
    - A separate clientside callback at `dashboard_manager.py:1490` opens its own duplicate WebSocket connection and writes to `window._juniper_ws_*` JS globals.
    - Two drain callbacks then write to `ws-topology-buffer` / `ws-state-buffer` `dcc.Store`s — but no chart component uses those stores as Input.
    - `ws-metrics-buffer` is even more broken: the init callback returns `no_update` so the store is never populated. See §2.7.

3. **There is no canopy → cascor WebSocket parameter control path.** `juniper-cascor-client` exposes `update_params(params)` over REST PATCH but has no equivalent WebSocket method.
    - Canopy's `cascor_service_adapter.apply_params()` therefore uses REST.
    - Per-keystroke or per-slider parameter changes hit a comparatively slow REST round-trip.
    - This is the canopy `set_params` integration gap that was incorrectly marked WONT-DO in §3.5 of the roadmap.

4. **The `_normalize_metric` nested+flat dual format is NOT dead code.**
    - A prior survey concluded the nested keys (`metrics: {...}`, `network_topology: {...}`) were unused because they were rebuilt downstream by `_to_dashboard_metric`.
    - That conclusion was wrong: dashboard chart components read directly from the nested keys via `m.get("metrics", {}).get("loss")` style accessors.
    - Removing them (closed PR #141) would have silently broken metrics rendering.
    - The flat keys are also not strictly dead — they are retained "for API/client compatibility" in the function's docstring, and an audit of every consumer is required before either format can be removed.
    - The reversion was correct.

5. **The P0 motivator is the `/api/metrics/history` REST polling bandwidth bomb.**
    - `_update_metrics_store_handler` (`dashboard_manager.py:2388-2421`) issues a `GET /api/metrics/history?limit=N` every 100 ms via `fast-update-interval`.
    - At `limit=1000` × ~300 B/entry ≈ 300 KB per response × 10 Hz polling = **~3 MB/s per dashboard** of pure REST waste.
    - WebSocket push at ~16 KB/s steady-state is ~200× more efficient.
    - This is the strongest concrete reason for the migration and was previously buried in §2.8.

### 1.2 The architectural problem in one sentence

> **WebSocket messages reach the browser but dead-end in JS globals that no Dash callback reads, while charts poll REST at 100 ms wasting ~3 MB/s per dashboard.**

### 1.3 Critical caveats discovered during validation
<!-- Note: this was originally a duplicate heading; second §1.3 ("What this document delivers") was renumbered to §1.5 below. -->

**(P0 design caveat)** Phase B's "wire `window.cascorWS.on('metrics', ...)` into a Dash callback" pattern as originally drafted is technically impossible: Dash `clientside_callback`s are pure functions evaluated when their declared `Input(...)` triggers — they do not subscribe to arbitrary JS events. The correct patterns are:

- **Option A — `dash.set_props()` (Dash 2.18+)**: a JS event handler can call `window.dash_clientside.set_props("ws-metrics-buffer", {data: newBuffer})` directly from inside the `on('metrics', ...)` callback, bypassing the Output system entirely. This is the idiomatic modern solution.
- **Option B — JS buffer + Interval drain**: the JS handler appends to `window._buffer`; a `clientside_callback` fires on `dcc.Interval.n_intervals` (e.g., 250 ms) and drains the buffer into the store. This is what the existing (broken) drain callbacks at `dashboard_manager.py:1531-1564` already do for topology/state.
- **Option C — `dash-extensions.WebSocket`**: a third-party Dash component that provides a `dcc.WebSocket`-style component whose `message` prop becomes a legitimate callback Input. Eliminates most of the custom wiring.

**Recommendation**: **Option B (Interval drain)** is the correct primary path because:

1. It coalesces high-frequency events into render-rate batches (one store update per drain interval, not per event), avoiding callback storms.
2. It already exists for `ws-topology-buffer` and `ws-state-buffer` — Phase B completes the pattern by wiring the metrics buffer the same way and adding drain callbacks for chart inputs.
3. It does not require Dash 2.18+ (Option A) or a third-party dependency (Option C).
4. It is testable via `dash[testing]`'s `dash_duo` fixture, which understands store mutations natively.

Option C (`dash-extensions.WebSocket`) is the runner-up; evaluate after Phase B if Option B's complexity becomes excessive.

**(P0 security caveat)** The canopy server's `/ws/training` and `/ws/control` endpoints currently accept any same-origin browser connection with no authentication and **no `Origin` validation**. This is a Cross-Site WebSocket Hijacking (CSWSH) vulnerability — any web page the user visits can open a WebSocket to `http://localhost:8050/ws/control` and issue `start`/`stop`/`reset`/`set_params`. §2.9 below mandates the security model that must be in place BEFORE Phase D (control buttons over WebSocket) is shipped.

### 1.4 Key findings (full list)

- **§2.7**: Two independent browser-side WebSocket clients exist; both dead-end. (Architecture)
- **§3**: The bidirectional message envelope is asymmetric — server→client uses `{type, timestamp, data}`; client→server commands use `{command, params}` with no envelope. (Protocol)
- **§3.1.3**: The 1 Hz state throttle is a "drop filter," not a coalescer. It can drop terminal `Failed`/`Stopped` transitions in fast sequences. (Correctness bug)
- **§2.2**: CR-025 (`close_all()` connection lock) is **partially fixed** — copy-then-iterate provides iterator safety but the method does NOT acquire `_lock`. A concurrent `connect()` during shutdown can leak an orphaned connection. (Concurrency bug)
- **§5**: 11 of 17 editable parameters benefit from WebSocket transport per the latency tolerance matrix; 6 are fine on REST. But see §5.3 caveat: latency thresholds are conventionally engineering aspirations, not validated user requirements; Phase C may downgrade from P1 to P2 pending §5.6 instrumentation.
- **§6.5**: There is no event sequence number / replay protocol; events emitted during a brief disconnect are lost and the dashboard cannot detect that drift has occurred.
- **§7**: 33 enumerated gaps (GAP-WS-01 through GAP-WS-33), ranging from P0 (security, auth, replay protocol, REST polling bandwidth) to P3 (close-reason text, envelope normalization).
- **§8**: Browser-side verification via Playwright + `dash[testing]` `dash_duo` is feasible from a headless dev environment; the existing `juniper-cascor-client/juniper_cascor_client/testing/FakeCascorClient` and `FakeCascorTrainingStream` should be reused as the in-process fake.
- **§9**: ~8.5 engineering days across 3 repos; ~3 weeks calendar including PR review and CI iteration.

### 1.5 What this document delivers

| Section | Deliverable                                                                                                             |
|---------|-------------------------------------------------------------------------------------------------------------------------|
| §2      | Inventory of every WebSocket endpoint, client class, broadcast method, and message handler in scope                     |
| §3      | Bidirectional message contract with full payload schemas in both directions                                             |
| §4      | Nested vs flat data structure analysis with consumer enumeration and retention recommendation                           |
| §5      | Latency tolerance matrix for every editable canopy UI element                                                           |
| §6      | Transport split design — which operations belong on WebSocket vs REST                                                   |
| §7      | Enumerated missing/broken pieces with severity and remediation hooks                                                    |
| §8      | Browser-side verification strategy that addresses the "I cannot test in a real browser from this environment" objection |
| §9      | Phased implementation plan with risk assessment                                                                         |
| §10     | Risk register                                                                                                           |
| §11     | Open questions for human review                                                                                         |
| §12     | References                                                                                                              |

---

## 2. WebSocket Surface Inventory

### 2.1 Cascor server endpoints

Cascor exposes three WebSocket endpoints, all mounted in `app.py` and authenticated via the `X-API-Key` header.

| # | Path             | File:line                           | Auth                                     | Handler                     | Backing manager                        |
|---|------------------|-------------------------------------|------------------------------------------|-----------------------------|----------------------------------------|
| 1 | `/ws/training`   | `juniper-cascor/src/api/app.py:338` | `X-API-Key`                              | `training_stream_handler()` | `WebSocketManager` (async)             |
| 2 | `/ws/control`    | `juniper-cascor/src/api/app.py:339` | `X-API-Key`                              | `control_stream_handler()`  | (no manager — RPC pattern)             |
| 3 | `/ws/v1/workers` | `juniper-cascor/src/api/app.py:340` | `X-API-Key` + rate limit + Origin reject | `worker_stream_handler()`   | `WorkerCoordinator` + `WorkerRegistry` |

Authentication is centralized in `juniper-cascor/src/api/websocket/manager.py:21-38` (`ws_authenticate()` checks the header via `APIKeyAuth.validate()` and closes with code `4001` on failure).

The worker endpoint is out of scope for this analysis — it is the cascor → distributed-worker channel, not the canopy → cascor channel.

### 2.2 Cascor `WebSocketManager`

**File**: `juniper-cascor/src/api/websocket/manager.py:41-146`

| Concern             | Detail                                                                                                                                                            |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Connection set      | `_active_connections: Set[WebSocket]` (line 49)                                                                                                                   |
| Connection metadata | `_connection_meta: Dict[WebSocket, Dict]` (line 52)                                                                                                               |
| Connection cap      | `_max_connections: int = 50` (line 50; configurable via `Settings.ws_max_connections`); rejects with code `1013` when full (line 71-74)                           |
| Concurrency lock    | `_lock: asyncio.Lock()` (line 53) — protects `connect()` (70), `disconnect()` (96), and broadcast iteration (106)                                                 |
| Sync→async bridge   | `broadcast_from_thread(message)` (line 112-124) uses `asyncio.run_coroutine_threadsafe()` to schedule a coroutine on the event loop from a sync background thread |
| Fan-out broadcast   | `broadcast(message)` (line 101-110) iterates active connections, sends, and prunes failed sockets                                                                 |
| Per-client send     | `send_personal_message(websocket, message)` (line 126-128)                                                                                                        |
| Shutdown            | `close_all()` (line 138-145) — copies the set first, then iterates and closes with code `1001` ("Server shutting down")                                           |

**Lock-type contract (IMPORTANT — must remain documented at the lock definition site)**: cascor uses TWO distinct lock types in different layers, and they have different rules:

- **`WebSocketManager._lock`** is `asyncio.Lock` (manager.py:53). Acquired by `async with`. Safe to await arbitrary coroutines (including `ws.close()`) inside the critical section. Lives on the event loop thread.
- **`TrainingLifecycleManager._training_lock`** is `threading.Lock` (manager.py:42).
  - Acquired by `with`, **MUST NOT be held across any `await`**, and critical sections must remain O(microseconds) — at most a dict copy or a small attribute swap.
  - Any future contributor adding a long-running critical section (a disk write, a network call, an `await` by accident) will deadlock the event loop because `broadcast_from_thread` schedules onto the same loop that the REST handlers run on.
  - Both training threads and async REST handlers acquire this lock; mixing them with a long critical section is a latent deadlock.
- **`TrainingState._lock`** is `threading.Lock` (monitor.py:54). Same rules as `_training_lock` above.

**Cross-lock-type rule**: never hold an `asyncio.Lock` while waiting on a `threading.Lock` (or vice versa). The two lock types live in different worlds and a holder of one cannot safely block on the other without risking deadlock or event-loop starvation.

**CR-025 status — verified PARTIAL** (verified against `juniper-cascor/src/api/websocket/manager.py:138-145` on 2026-04-10):

```python
async def close_all(self) -> None:
    for ws in self._active_connections.copy():  # ← copy but NO lock
        with contextlib.suppress(Exception):
            await ws.close(code=1001, reason="Server shutting down")
    self._active_connections.clear()
    self._connection_meta.clear()
```

The method does **not** acquire `self._lock` before copying, iterating, or clearing.
The copy-then-iterate provides Python iterator safety (no `RuntimeError: Set changed size during iteration`), but a concurrent `connect()` during shutdown can leak an orphaned connection: a client connecting during the iteration window will be added to `_active_connections` after the copy but before the `clear()`, then silently dropped from the set without ever receiving its `ws.close()` frame.
The connection remains open client-side until the server's TCP socket closes, with no clean shutdown signal.

Severity: P2 (degraded shutdown UX, not a memory or correctness bug).
Tracked as **GAP-WS-19** in §7.
Fix is to wrap the entire method body in `async with self._lock:` — the iteration awaits `ws.close()` which is safe under an `asyncio.Lock` (not a `threading.Lock`).

### 2.3 Cascor server message envelope

All cascor WebSocket messages follow this canonical envelope:

```json
{
  "type": "<message_type>",
  "timestamp": <unix_float_seconds>,
  "data": { ... }
}
```

This is enforced by the message builder functions in `juniper-cascor/src/api/websocket/messages.py` and is consistent across all three endpoints' outbound messages.

### 2.4 `juniper-cascor-client` SDK WebSocket classes

**Repo**: `/home/pcalnon/Development/python/Juniper/juniper-cascor-client/juniper_cascor_client/`

| Class                  | File:line          | URL path       | Send methods                                               | Receive methods                                | Callbacks                                                                       |
|------------------------|--------------------|----------------|------------------------------------------------------------|------------------------------------------------|---------------------------------------------------------------------------------|
| `CascorTrainingStream` | `ws_client.py:18`  | `/ws/training` | `send_command(cmd, params)` (generic)                      | `stream()` (async iter), `listen()` (blocking) | `on_metrics()`, `on_state()`, `on_topology()`, `on_cascade_add()`, `on_event()` |
| `CascorControlStream`  | `ws_client.py:149` | `/ws/control`  | `command(cmd, params)` (RPC; waits for `command_response`) | (request/response only)                        | (none)                                                                          |

**Critical gap (P1, MISSING)**: neither class exposes a dedicated `send_set_params(params)` / `set_params(params)` / `update_params_ws(params)` method. The `CascorTrainingStream.send_command()` method is generic and could in principle be used to issue a `set_params` message, but:

1. It is undocumented for that purpose.
2. There is no mechanism to await an acknowledgement (it is fire-and-forget).
3. The `CascorControlStream.command()` method does support request/response but is designed for control verbs (`start`, `stop`, etc.) and has no per-command schema validation for `set_params`.

The natural place to add the missing functionality is `CascorControlStream.set_params(params, timeout=5.0)` returning the parsed `command_response` payload, plus an asynchronous variant.

### 2.5 Canopy `CascorServiceAdapter` WebSocket usage

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

| Concern           | Method                                  | Line(s) |
|-------------------|-----------------------------------------|---------|
| Open relay        | `start_metrics_relay()`                 | 199     |
| Stream loop       | (inside relay)                          | 213-225 |
| Cleanup           | `stop_metrics_relay()`                  | 328     |
| Reconnect backoff | exponential `[1, 2, 5, 10, 30]` seconds | 208     |

`start_metrics_relay()` opens a `CascorTrainingStream` connection to cascor's `/ws/training`, then dispatches incoming messages by `type`:

| Inbound type                | Handling                                                                                                                                                            | Line    |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| `metrics`                   | Pipe through `_normalize_metric() → _to_dashboard_metric()`, then forward via canopy's `websocket_manager.broadcast()`                                              | 221-224 |
| `state`                     | Map field-name bridge (`best_candidate_id` → `top_candidate_id`, etc.), then forward to local `_state_update_callback` which updates canopy's local `TrainingState` | 236-288 |
| `cascade_add`               | Trigger a fresh `extract_network_topology()` REST call, then broadcast a `topology` message                                                                         | 227-233 |
| `candidate_progress`        | Forward `epoch`, `total_epochs`, `correlation` to local `_state_update_callback`                                                                                    | 291-301 |
| `event` (training_complete) | Map to `{status: "Completed", phase: "Idle"}` and update local state                                                                                                | 304-311 |

**Note**: `apply_params()` (line 450) does NOT use the WebSocket. It maps canopy's `nn_*`/`cn_*` parameter namespace to cascor API names (`_CANOPY_TO_CASCOR_PARAM_MAP`, line 432-448) and calls `self._client.update_params(mapped)` — the REST PATCH `/training/params` endpoint. This is the canopy-side anchor of the missing WebSocket `set_params` path.

### 2.6 Canopy server WebSocket endpoints

**File**: `juniper-canopy/src/main.py`

| Path           | Line | Inbound types                               | Outbound types                                                 | Purpose                                   |
|----------------|------|---------------------------------------------|----------------------------------------------------------------|-------------------------------------------|
| `/ws/training` | 355  | `ping`                                      | `state`, `metrics`, `topology`, `cascade_add`, `event`, `pong` | Real-time relay from cascor → browser     |
| `/ws/control`  | 417  | `start`, `stop`, `pause`, `resume`, `reset` | `control_ack`                                                  | Browser → canopy → cascor command path    |
| `/ws` (legacy) | 1925 | (legacy)                                    | (legacy)                                                       | Older fallback endpoint, currently unused |

The canopy `WebSocketManager` lives at `juniper-canopy/src/communication/websocket_manager.py`. It exposes `broadcast()` (async), `broadcast_sync()` and `broadcast_from_thread()` (for sync→async bridging from training callbacks and the cascor relay), and `broadcast_state_change()` (which wraps a state dict in the standard `{type, timestamp, data}` envelope).

### 2.7 Browser-side WebSocket clients (TWO of them, both broken)

This is the biggest finding. The canopy dashboard contains **two separate browser-side WebSocket implementations**, neither of which is wired to chart or panel components.

#### 2.7.1 `assets/websocket_client.js` — exported, never used

**File**: `juniper-canopy/src/frontend/assets/websocket_client.js` (≈230 lines)

| Symbol                   | Type                       | Description                |
|--------------------------|----------------------------|----------------------------|
| `window.cascorWS`        | `CascorWebSocket` instance | Connects to `/ws/training` |
| `window.cascorControlWS` | `CascorWebSocket` instance | Connects to `/ws/control`  |

The `CascorWebSocket` class implements:

- `on(type, handler)` — register type-specific callback
- `onStatus(handler)` — register status observer
- `send(message)` — send command and await `control_ack` (5 s timeout, command-name correlation)
- `getBufferedMessages()` — destructive read of internal buffer (max 100 messages, FIFO)
- Exponential backoff reconnect (500 ms → 5 s, max 10 attempts)
- No heartbeat / ping-pong frame implementation

**`assets/` is auto-loaded by Dash**, so the file is shipped to every browser session. The two global instances are constructed at page load (lines 219, 223). However, **no Dash callback, clientside callback, or component code references `window.cascorWS` or `window.cascorControlWS`**. A grep across `src/frontend/*.py` and `src/frontend/components/*.py` returns zero matches.

**Verdict: BROKEN (dead code).**

#### 2.7.2 In-line clientside callback at `dashboard_manager.py:1490` — the parallel implementation

A separate clientside callback at `juniper-canopy/src/frontend/dashboard_manager.py:1490-1526` constructs its own raw WebSocket to `/ws/training`. Its handler stores incoming messages in three module-scope JS globals:

```javascript
window._juniper_ws_buffer    // metrics
window._juniper_ws_topology  // topology snapshot
window._juniper_ws_state     // state changes
```

This callback's declared `Output` is `ws-metrics-buffer.data`, but the function returns `no_update` for that store, so the metrics buffer store is **never written to**. The other two stores (`ws-topology-buffer`, `ws-state-buffer`) are populated by separate drain callbacks (lines 1531-1545 and 1550-1564 respectively) that run on the `fast-update-interval` (every ~100 ms) and pull from the JS globals.

| Store                | Populated?                                     | Consumed by?                                       |
|----------------------|------------------------------------------------|----------------------------------------------------|
| `ws-metrics-buffer`  | **No** — the init callback returns `no_update` | (would be irrelevant; no consumer)                 |
| `ws-topology-buffer` | Yes (every 100 ms)                             | **Nothing** — no callback uses this store as Input |
| `ws-state-buffer`    | Yes (every 100 ms)                             | **Nothing** — no callback uses this store as Input |

**Verdict: BROKEN.** The infrastructure is half-built. Messages flow from cascor → canopy → browser → JS globals → two stores, but the stores are dead ends.

### 2.8 Where the dashboard actually reads its data from

To understand what data is actually rendered, the audit traced backwards from `MetricsPanel` (the main loss/accuracy chart):

1. `MetricsPanel.update_metrics_display()` callback (`metrics_panel.py:648-670`) takes input `metrics-panel-metrics-store.data`.
2. That store is fed by an Interval-driven callback (`dashboard_manager.py:1589-1600`) bound to `fast-update-interval`.
3. The handler `_update_metrics_store_handler()` (`dashboard_manager.py:2388-2421`) issues a `requests.get()` to the canopy REST endpoint `/api/metrics/history?limit=...`.
4. The REST endpoint in turn calls `backend.get_metrics_history()` → `cascor_service_adapter.training_monitor.get_recent_metrics()` (REST GET to cascor).

So the actual production data path for metrics is:

```bash
cascor REST endpoint → cascor_service_adapter (REST GET)
                    → canopy backend.get_metrics_history()
                    → REST handler /api/metrics/history
                    → Dash callback on fast-update-interval (100 ms polling)
                    → metrics-panel-metrics-store
                    → MetricsPanel chart
```

The WebSocket path that *should* be:

```bash
cascor WS event → cascor_service_adapter._normalize_metric()
               → canopy websocket_manager.broadcast()
               → canopy /ws/training endpoint
               → browser WebSocket onmessage
               → ws-metrics-buffer (or equivalent store)
               → MetricsPanel chart
```

...is built end-to-end from the cascor side through the browser receive handler, but **the bridge from the JS handler into the Dash store is broken**, so the WebSocket data has no impact on what the user sees.

Training control buttons (start/stop/pause/resume/reset) follow the same pattern: their click handler (`dashboard_manager.py:1725-1754`, implemented at `:2522-2575`) issues `requests.post(self._api_url("/api/train/{command}"))` — REST POST, not the available `cascorControlWS.send()` method.

### 2.9 Security Model (REQUIRED before Phase D)

The original draft of this document treated authentication and CSRF as §11 open question #3 ("Should canopy's `/ws/training` endpoint be authenticated?"). That framing is wrong: routing `set_params` and training control over a WebSocket without an auth model is a P0 security defect, not an open question. This section enumerates the required security posture before any of Phase B/C/D ships.

#### 2.9.1 Threat model

| Threat                                       | Attack vector                                                              | Severity | Current status                                                               |
|----------------------------------------------|----------------------------------------------------------------------------|----------|------------------------------------------------------------------------------|
| Cross-Site WebSocket Hijacking (CSWSH)       | Malicious page opens `ws://localhost:8050/ws/control` and                  | **P0**   | **VULNERABLE** -- no Origin validation on canopy `/ws*`                      |
|                                              | -- issues `start`/`stop`/`reset`/`set_params`                              |          |                                                                              |
|                                              | -- while the user has the canopy dashboard authenticated in another tab    |          |                                                                              |
| Credentialed CSRF over WebSocket             | Same as above but with cookie credentials forwarded                        | **P0**   | **VULNERABLE** — no CSRF token in WS frames                                  |
| Per-IP DoS (slot exhaustion)                 | Single attacker opens 50 connections from one host, starves legit users    | P1       | Cascor's 50-connection cap is global, not per-IP                             |
| Auth-bypass via header omission              | Tests using a fake server that doesn't enforce `X-API-Key`                 | P2       | Test fixtures (§8.5) need to enforce auth                                    |
|                                              | -- mask regressions where canopy stops sending the header                  |          |                                                                              |
| Param-injection via `init_output_weights`    | String value passed to `setattr` or `getattr` without validation;          | P2       | Validated as `Literal["zero", "random"]`                                     |
|                                              | -- could inject arbitrary code                                             |          | -- (`juniper-cascor/src/api/models/network.py:23`)                           |
| Information disclosure via close-reason text | "Invalid API key" vs "Missing API key" lets attackers enumerate auth state | P3       | All auth failures should use a single, opaque "Authentication failed" reason |
| Sensitive data in logs                       | Future `set_params` payloads with credentials would leak via plain logs    | P3       | No PII in current params; document as forward concern                        |

#### 2.9.2 Required mitigations (before Phase D ships)

**M-SEC-01 (P0): Origin validation on canopy `/ws/*` endpoints**

Add an `Origin` allowlist to canopy's WebSocket route handlers, modeled after the worker endpoint's existing pattern (`juniper-cascor/src/api/websocket/worker_stream.py:41-44`). Default allowlist: `http://localhost:8050`, `http://127.0.0.1:8050`. Configurable via `Settings.allowed_origins`. Reject with HTTP 403 before WebSocket upgrade for non-matching origins.

**M-SEC-02 (P0): Authentication model for canopy `/ws/*` endpoints**

Browsers cannot send custom headers on WebSocket upgrade (the JS WebSocket API forbids it), so the cascor `X-API-Key` pattern cannot be reused. The recommended approach:

1. **Cookie-session auth**: canopy's existing session cookie (if any) is sent automatically on the WebSocket handshake. The handler validates the cookie against the session store.
2. **CSRF token in first message**: after the handshake, the server expects the client's first frame to be `{"type": "auth", "csrf_token": "<token>"}`, where `csrf_token` is fetched from a previously-loaded `/api/csrf` REST endpoint and embedded in the page. Closes with code 4001 if absent or invalid.
3. **Per-command HMAC** (advanced, optional): each control command carries a HMAC computed over `{command, params, timestamp}` using a session-derived key. Prevents replay even within an authenticated session.

For local-development deployments (single user, no network exposure), all three can be configured-off with a `Settings.disable_ws_auth=True` flag — but the flag must default to **enabled** in production.

**M-SEC-03 (P0): Per-frame size limits on every WebSocket endpoint**:

`juniper-cascor/src/api/websocket/control_stream.py:23` enforces a 64 KB cap on `/ws/control` inbound. Verify the same cap applies to:

- `juniper-cascor/src/api/websocket/training_stream.py` — training stream inbound (currently `ping`/`pong` only, but the framework allows arbitrary messages)
- `juniper-canopy/src/main.py:355,417` — canopy server `/ws/training` and `/ws/control`

Without this, a 100 MB inbound frame can exhaust server memory before parsing even begins.

**M-SEC-04 (P1): Per-IP connection caps + auth timeout**:

Enhance `juniper-cascor/src/api/websocket/manager.py` to track per-IP connection counts. Default cap: 5 connections per IP (configurable via `Settings.ws_max_connections_per_ip`). Add a connect-time auth timeout: if the client does not complete auth within 5 seconds, close with code 1008 (Policy Violation) and log the IP for rate-limiting.

**Concurrency contract**: the per-IP count map is a `Dict[str, int]` field on `WebSocketManager` (`_per_ip_counts: Dict[str, int] = {}`). It MUST be mutated only inside `async with self._lock:` (the same lock guarding `_active_connections`). The decrement happens in the WebSocket route handler's `finally` block (NOT only in `disconnect()`, because exception paths can skip `disconnect()`):

```python
@app.websocket("/ws/training")
async def training_ws(ws: WebSocket):
    client_ip = ws.client.host
    async with manager._lock:
        if manager._per_ip_counts.get(client_ip, 0) >= settings.ws_max_connections_per_ip:
            await ws.close(code=1013, reason="Per-IP connection cap")
            return
        manager._per_ip_counts[client_ip] = manager._per_ip_counts.get(client_ip, 0) + 1
    try:
        # ... handler ...
    finally:
        async with manager._lock:
            count = manager._per_ip_counts.get(client_ip, 0) - 1
            if count <= 0:
                del manager._per_ip_counts[client_ip]  # prevent unbounded growth
            else:
                manager._per_ip_counts[client_ip] = count
```

**Cookie attributes (refinement to M-SEC-02)**: the canopy session cookie must be set `HttpOnly; Secure; SameSite=Strict; Path=/`. Bearer tokens in `localStorage` are explicitly rejected as XSS-exfiltratable. **CSRF token rotation**: tokens expire after 1 hour of inactivity or on session invalidation; the client re-fetches on `close code 4001 reason=token_expired`.

**M-SEC-01b (P0): Cascor `/ws/*` Origin validation parity**: M-SEC-01 covers canopy's `/ws/*`. Cascor's `/ws/training` and `/ws/control` are also reachable from the browser in demo-mode / direct-connect topologies and must enforce the same Origin allowlist. The pattern already exists at `juniper-cascor/src/api/websocket/worker_stream.py:41-44` and should be extracted into a shared `validate_origin()` helper.

**M-SEC-05 (P1): Command rate limiting**:

Add a per-connection command-frequency cap on `/ws/control`: e.g., 10 commands per second. Excess commands respond with `{type: "command_response", data: {status: "rate_limited"}}` and do not execute. Tracked via the `slowapi` library or a homegrown leaky bucket.

**M-SEC-06 (P3): Opaque auth-failure reason**:

Change all WebSocket close-reason strings on auth failure (cascor and canopy) from descriptive ("Invalid API key", "Missing API key", "Expired key") to a single opaque "Authentication failed". Log the actual reason server-side for operational debugging.

**M-SEC-07 (P3): Logging scrubbing allowlist**:

Add a documented allowlist of `set_params` keys that may be logged in cleartext. All other keys are logged as `<redacted>`. Apply now even though current params are non-sensitive — prevents future regressions.

#### 2.9.3 Phase ordering implication

Phase D (control buttons over WebSocket) **MUST NOT ship** until M-SEC-01, M-SEC-02, and M-SEC-03 are in place. The implementation plan in §9 has been updated to insert a new **Phase B-pre: Security hardening** before Phase D (see §9.2).

---

## 3. Bidirectional Message Contract

This section documents every message type that crosses each repo boundary. **Asterisks (*) mark fields that are required**; all others are optional.

### 3.0 Envelope asymmetry

**Server → client** messages use the canonical envelope `{type: str, timestamp: float, data: dict}`. This applies to all outbound messages on `/ws/training`, `/ws/control`, and `/ws/v1/workers`.

**Client → server** command messages use a different shape: `{command: str, params: dict}`. There is **no `type` field, no `timestamp`, no `data` wrapper**. This asymmetry is undocumented in the cascor source and was discovered by reading `juniper-cascor/src/api/websocket/control_stream.py:97-100`.

This is a real wire-format inconsistency that should be normalized in a future release. For now, clients (canopy adapter, browser JS, juniper-cascor-client) MUST send the bare `{command, params}` shape and parse the wrapped `{type, timestamp, data}` shape. **GAP-WS-20 (P3)**: normalize bidirectional envelope to use `{type, timestamp, data}` everywhere. Tracked in §7.

### 3.1 cascor → canopy (cascor server → canopy adapter, via `/ws/training` and `/ws/control`)

#### 3.1.1 `connection_established`

```json
{
  "type": "connection_established",
  "timestamp": 1712707200.123,
  "data": {
    "connections": 3
  }
}
```

- **Trigger**: client connects successfully and passes auth
- **Frequency**: once per connection
- **Source**: `juniper-cascor/src/api/websocket/manager.py:84-91`

#### 3.1.2 `initial_status`

Full payload of `lifecycle.get_status()` wrapped in the envelope. Sent once per `/ws/training` connect.

- **Source**: `juniper-cascor/src/api/websocket/training_stream.py:42-44`

#### 3.1.3 `state`

Payload is the full output of `lifecycle.training_state.get_state()`:

```json
{
  "type": "state",
  "timestamp": 1712707201.456,
  "data": {
    "status": "Started",
    "phase": "Output",
    "phase_detail": "training_output",
    "current_epoch": 42,
    "current_step": 42,
    "max_epochs": 100000000000,
    "max_iterations": 1000000,
    "max_hidden_units": 10000,
    "learning_rate": 0.01,
    "candidate_learning_rate": 0.005,
    "patience": 5,
    "candidate_pool_size": 8,
    "correlation_threshold": 0.1,
    "candidate_epochs": 50,
    "output_epochs": 25,
    "init_output_weights": "zero",
    "grow_iteration": 3,
    "grow_max": 1000000,
    "candidates_trained": 5,
    "candidates_total": 8,
    "best_correlation": 0.873,
    "candidate_epoch": 0,
    "candidate_total_epochs": 50,
    "phase_started_at": "2026-04-10T05:00:00.000000",
    "best_candidate_id": 5,
    "best_candidate_uuid": "a1b2c3d4-...",
    "second_candidate_id": 3,
    "second_candidate_correlation": 0.812,
    "all_correlations": [0.873, 0.812, 0.799, ...]
  }
}
```

- **Trigger**: any `state.update_state()` call followed by `_broadcast_training_state()`
- **Frequency**: limited to **1 Hz** by a monotonic timer in `lifecycle/manager.py:133-136`.
  - **WARNING: this is a "drop filter," not a coalescer.** The implementation is `if now - self._last_state_broadcast_time < 1.0: return` — events arriving within the 1-second window are silently dropped, never delivered.
  - **This can drop terminal state transitions** (e.g., a fast `Started → Failed → Stopped` sequence within 1 second leaves the dashboard showing `Started` forever).
    - The throttle should be replaced with a debounced coalescer that flushes the most-recent state at the interval boundary, with terminal states (`Failed`, `Stopped`, `Completed`) bypassing the throttle entirely.
    - Tracked as **GAP-WS-21 (P1)** in §7.
- **Multi-thread race**: `_last_state_broadcast_time` is read/written from multiple threads (drain thread, training thread, REST handler) without locking.
  - CPython attribute assignment is atomic at bytecode level, but two simultaneous broadcasts can squeak through.
  - Low severity but worth noting.
- **Builder**: `juniper-cascor/src/api/websocket/messages.py:26-32`

#### 3.1.4 `metrics`

```json
{
  "type": "metrics",
  "timestamp": 1712707201.789,
  "data": {
    "epoch": 42,
    "loss": 0.234,
    "accuracy": 0.917,
    "validation_loss": 0.245,
    "validation_accuracy": 0.901,
    "learning_rate": 0.01,
    "hidden_units": 3,
    "phase": "output"
  }
}
```

- **Trigger**: per-epoch callback during output training (`train_output_layer(on_epoch_callback=...)`); throttled to every 25 epochs + final epoch (`cascade_correlation.py:~1680`)
- **Frequency**: bursts of 1 message per 25 epochs during output phase; quiet during candidate phase (replaced by `candidate_progress`)
- **Builder**: `juniper-cascor/src/api/websocket/messages.py:17-23`

**Schema note**: cascor uses `loss`/`accuracy`/`validation_loss`/`validation_accuracy` (no `train_` prefix); canopy's adapter normalizes to `train_loss`/`train_accuracy`/`val_loss`/`val_accuracy` flat keys plus the nested `metrics: {...}` shape — see §4.

#### 3.1.5 `cascade_add`

```json
{
  "type": "cascade_add",
  "timestamp": 1712707202.012,
  "data": {
    "hidden_unit_index": 3,
    "correlation": 0.873
  }
}
```

- **Trigger**: cascor adds a hidden unit (`grow_network` install hook in `manager.py:354-368`)
- **Frequency**: per cascade event (low — bounded by `max_iterations`)
- **Builder**: `juniper-cascor/src/api/websocket/messages.py:53-59`

#### 3.1.6 `candidate_progress`

```json
{
  "type": "candidate_progress",
  "timestamp": 1712707202.123,
  "data": {
    "candidate_id": 5,
    "candidate_uuid": "a1b2c3d4-...",
    "epoch": 30,
    "total_epochs": 50,
    "correlation": 0.873
  }
}
```

- **Trigger**: candidate worker progress emission (`CandidateUnit.train_detailed:614-622`); throttled to every 50 epochs + final epoch *per candidate* and aggregated through the persistent worker pool's `_persistent_progress_queue` (drained by `manager._drain_progress_queue()` in `lifecycle/manager.py:309-344`)
- **Frequency**: high during candidate phase — up to (pool_size × epochs/50) events per cycle
- **Builder**: `juniper-cascor/src/api/websocket/messages.py:62-68`

#### 3.1.7 `event` (training lifecycle)

```json
{
  "type": "event",
  "timestamp": 1712707203.456,
  "data": {
    "event": "training_complete"
  }
}
```

- Other event values include `training_failed`, `training_started`, `training_stopped`
- **Source**: lifecycle manager broadcasts at phase boundaries

#### 3.1.8 `topology`

```json
{
  "type": "topology",
  "timestamp": 1712707204.789,
  "data": {
    "input_size": 2,
    "output_size": 1,
    "hidden_units": [
      {"weights": [...], "bias": 0.123, "activation": "tanh"},
      ...
    ],
    "output_weights": [[...], ...],
    "output_bias": [0.0]
  }
}
```

- **Trigger**: not directly emitted by cascor's WebSocket today; canopy adapter triggers a fresh REST `extract_network_topology()` on every `cascade_add` and re-broadcasts the result on canopy's own `/ws/training` (see §3.3.4)

#### 3.1.9 `command_response`

The response format for any command sent on `/ws/control`. See §3.2.

### 3.2 canopy → cascor (canopy adapter → cascor server, via `/ws/control`)

#### 3.2.1 `start`

```json
{
  "command": "start",
  "params": {
    "epochs_max": 100000000000,
    "max_iterations": 1000000
  }
}
```

- **Whitelist check**: `_VALID_COMMANDS = {"start", "stop", "pause", "resume", "reset", "set_params"}` (`control_stream.py:22`)
- **Handler**: `lifecycle.start_training(**params)`
- **Response**: `command_response` with `status: "success"` or `status: "error"`

#### 3.2.2 `stop` / `pause` / `resume` / `reset`

Same envelope, different `command` value, no required `params`.

#### 3.2.3 `set_params`

```json
{
  "command": "set_params",
  "params": {
    "learning_rate": 0.005,
    "max_hidden_units": 10000,
    "patience": 10
  }
}
```

- **Whitelist of allowed params** (`lifecycle/manager.py:684-723`):
  - `learning_rate`, `candidate_learning_rate`, `correlation_threshold`, `candidate_pool_size`, `max_hidden_units`, `epochs_max`, `max_iterations`, `patience`, `convergence_threshold`, `candidate_convergence_threshold`, `candidate_patience`, `candidate_epochs`, `init_output_weights`
- **Handler**: `lifecycle.update_params(params)` — same handler used by REST PATCH `/v1/training/params`
- **Response on success**:

  ```json
  {
    "type": "command_response",
    "timestamp": ...,
    "data": {
      "command": "set_params",
      "status": "success",
      "result": { /* updated params dict */ }
    }
  }
  ```

- **Response on failure** (e.g., no network):

  ```json
  {
    "type": "command_response",
    "timestamp": ...,
    "data": {
      "command": "set_params",
      "status": "error",
      "error": "No network exists — create a network first"
    }
  }
  ```

**Status**: server-side **PRESENT** (cascor accepts and handles the command); client-side **MISSING** (juniper-cascor-client has no method to issue it; canopy adapter does not call it).

#### 3.2.4 Protocol error responses

The original draft did not document failure modes for malformed input on `/ws/control`. The required behavior is:

| Failure mode                               | Cascor response                                                                 | Close code (if any)     | Spec'd?                                                                    |
|--------------------------------------------|---------------------------------------------------------------------------------|-------------------------|----------------------------------------------------------------------------|
| Non-JSON payload                           | (immediate close)                                                               | 1003 (Unsupported Data) | **Recommended; not currently implemented**                                 |
| JSON with no `command` field               | `command_response`, `status: "error", error: "missing command field"`           | (no close)              | **Recommended; not currently implemented**                                 |
| Unknown command (not in `_VALID_COMMANDS`) | `command_response`, `status: "error", error: "Unknown command: <name>"`         | (no close)              | error returns `control_stream.py:55-59`,                                   |
|                                            |                                                                                 |                         | -- early-return `create_control_ack_message(command, "error", error=...)`. |
|                                            |                                                                                 |                         | -- Behavior Correct; Documents Contract for New commands.                  |
| Handler exception                          | `command_response`, `status: "error", error: "<exception message>"` + traceback | (no close)              | Partial — exceptions caught but no traceback logging                       |
| Frame > 64 KB                              | (immediate close)                                                               | 1009 (Message Too Big)  | Currently raises in framework before handler runs                          |

Tracked as **GAP-WS-22 (P2)** in §7.

### 3.3 canopy server → browser (canopy `/ws/training`, broadcast to all dashboard clients)

The canopy server does not invent new types — it forwards the cascor envelope after normalization. The shapes are:

#### 3.3.1 `metrics` (normalized by adapter)

```json
{
  "type": "metrics",
  "timestamp": ...,
  "data": {
    "epoch": 42,
    "metrics": {
      "loss": 0.234,
      "accuracy": 0.917,
      "val_loss": 0.245,
      "val_accuracy": 0.901
    },
    "network_topology": {
      "hidden_units": 3
    },
    "train_loss": 0.234,
    "train_accuracy": 0.917,
    "val_loss": 0.245,
    "val_accuracy": 0.901,
    "hidden_units": 3,
    "phase": "output",
    "timestamp": "2026-04-10T05:00:01.789000"
  }
}
```

This is the **dual nested+flat shape** that §4 discusses in detail. The nested keys (`metrics: {...}`, `network_topology: {...}`) are what `MetricsPanel` reads; the flat keys are retained for SDK / API client compatibility.

#### 3.3.2 `state` — same shape as cascor `state`, with field-name bridge

The canopy adapter applies a small mapping at lines 251-285:

- `best_candidate_id` → `top_candidate_id` (NEW-02 bridge)
- additional canopy-specific phase / epoch normalization

#### 3.3.3 `cascade_add`

Forwarded as-is from cascor.

#### 3.3.4 `topology`

Re-fetched from cascor's REST endpoint on every `cascade_add` event (adapter line 227-233), then broadcast on the canopy `/ws/training` endpoint.

#### 3.3.5 `pong`

```json
{ "type": "pong", "timestamp": ... }
```

Reply to browser-initiated `ping` keep-alive. Currently the browser does not send `ping` — the canopy server has no heartbeat reciprocity built in.

### 3.4 browser → canopy server (canopy `/ws/control`)

#### 3.4.1 `start` / `stop` / `pause` / `resume` / `reset`

Same envelope as §3.2 but routed through canopy's `/ws/control` handler (`main.py:417`). The handler forwards to the active backend (demo or service); for service mode the call eventually issues a REST POST to cascor's `/api/v1/training/{command}` endpoint **OR** a WebSocket `command` to cascor's `/ws/control` (currently the canopy adapter only uses REST for these).

#### 3.4.2 `ping`

Browser keep-alive heartbeat — currently **not implemented**.

---

## 4. Nested vs Flat Data Structure Analysis

### 4.1 The dual format

`juniper-canopy/src/backend/cascor_service_adapter.py:516-561` defines `_normalize_metric()`. It accepts a raw metric dict from cascor and returns a dict containing both:

| Key set                                                                                                   | Format | Purpose                                                                            |
|-----------------------------------------------------------------------------------------------------------|--------|------------------------------------------------------------------------------------|
| `epoch`, `train_loss`, `train_accuracy`, `val_loss`, `val_accuracy`, `hidden_units`, `phase`, `timestamp` | flat   | "Canonical normalized names retained for API/client compatibility" (per docstring) |
| `metrics: {loss, accuracy, val_loss, val_accuracy}`, `network_topology: {hidden_units}`                   | nested | "Legacy dashboard shape used by metrics panel rendering" (per docstring)           |

Every caller of `_normalize_metric` then pipes the result through `_to_dashboard_metric()` (line 564-585), which **discards everything except the nested format and the four scalar fields** (`epoch`, `phase`, `timestamp`, plus the rebuilt nested `metrics`/`network_topology` from the flat keys).

### 4.2 Consumer enumeration

A grep across `juniper-canopy/src/` and `juniper-cascor-client/` for the seven flat keys (`train_loss`, `train_accuracy`, `val_loss`, `val_accuracy`, `hidden_units`, `phase`, `timestamp`) and the two nested keys (`metrics`, `network_topology`) gives:

| Consumer                                                           | Reads which keys                                                                           | Source                                                                  |
|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `MetricsPanel` chart callback                                      | `m["metrics"]["loss"]`, `m["metrics"]["accuracy"]`, `m["metrics"]["val_loss"]`,            | `frontend/components/metrics_panel.py`                                  |
|                                                                    | -- `m["metrics"]["val_accuracy"]`, `m["network_topology"]["hidden_units"]`                 |                                                                         |
| `_to_dashboard_metric`                                             | `flat["train_loss"]`, `flat["train_accuracy"]`, `flat["val_loss"]`,                        | `cascor_service_adapter.py:564-585`                                     |
|                                                                    | -- `flat["val_accuracy"]`, `flat["hidden_units"]`, `flat["epoch"]`,                        |                                                                         |
|                                                                    | -- `flat["phase"]`, `flat["timestamp"]`                                                    |                                                                         |
| `state_sync.py:150`                                                | calls the pipeline `_to_dashboard_metric(_normalize_metric(m))` for each historical metric | `backend/state_sync.py`                                                 |
| `test_response_normalization.py::test_metrics_loss_zero_preserved` | `normalized["train_loss"]`, `normalized["train_accuracy"]`,                                | (test only)                                                             |
|                                                                    | -- `dashboard["metrics"]["loss"]`, `dashboard["metrics"]["accuracy"]`                      |                                                                         |
| `test_response_normalization.py::TestDashboardMetricsContract`     | asserts the FINAL output of `get_recent_metrics`/`get_current_metrics`                     | (test only)                                                             |
|                                                                    | -- does NOT contain flat keys at top level (i.e., the post-pipeline shape is nested-only)  |                                                                         |
| `juniper-cascor-client`                                            | Reads cascor's native `loss`/`accuracy`/`validation_loss`/`validation_accuracy`            | `juniper-cascor-client/juniper_cascor_client/training_monitor.py`, etc. |
|                                                                    | -- from the cascor REST/WS responses, NOT canopy's normalized format                       |                                                                         |
| External SDK consumers (potential)                                 | Unknown — the docstring claim "API/client compatibility" is unverified                     | (unknown)                                                               |
|                                                                    | -- beyond the in-tree juniper-cascor-client (which doesn't use these keys)                 |                                                                         |

### 4.3 Findings

1. **The nested keys are NOT dead code.** `MetricsPanel` directly reads `m["metrics"]["loss"]` style accessors. PR #141, which removed them, would have silently broken the chart.

2. **The flat keys ARE intermediate-only inside `_normalize_metric`.** Their only consumer in the canopy repo is `_to_dashboard_metric`, which collapses them back into the nested format. The "API/client compatibility" rationale in the docstring is not backed by an in-tree consumer.

3. **HOWEVER**, the flat keys are the *natural* shape for consumers outside this dashboard — for example, an external script consuming canopy's REST `/api/metrics` endpoint would expect flat scalar fields, not a nested shape. The nested shape is a Plotly-friendly convention.

4. **The current dual return is pragmatically correct but architecturally muddled**: `_normalize_metric` is doing two jobs (normalizing names AND building the dashboard shape) when its name implies only the first.

### 4.4 Recommendation

**Do not remove either format until a follow-up audit verifies external consumers.** Specifically:

- **Phase 0** (this document): document the contract as-is. Both nested and flat keys are part of the canopy `/api/metrics`-shaped envelope.
- **Phase 1**: split `_normalize_metric` into two clearly-named helpers:
  - `_normalize_field_names(entry)` — bridges cascor names to canopy flat names; returns flat-only
  - `_to_dashboard_metric(flat)` — wraps a flat dict in the nested dashboard shape (already exists)
- **Phase 2**: audit canopy's REST endpoints to determine whether external clients receive the flat keys, the nested keys, or both.
  - Document the result here.
- **Phase 3**: if external clients only consume the nested shape, the flat keys can be removed from the eventual broadcast payload (but keep them inside the helpers for clarity).
  - If they consume the flat shape, keep both formats with a clearer reason in the docstring than "API/client compatibility".

The reverted PR #141 was correct in being reverted. A future change should follow the phased approach above.

### 4.5 Type contract implications

`juniper-canopy/src/backend/protocol.py:72-87` declares `MetricsResult` as a `TypedDict, total=False` containing both nested-style fields (`epoch: int`, `loss: float`, `accuracy: float`, etc.) and flat-style fields (`train_loss: float`, `train_accuracy: float`, etc.).
This permissive declaration accommodates both formats but hides the actual contract from consumers. Phase 1 of the typed contract work (PR #140) added the broader typed envelope but did not tighten this particular TypedDict.

**Recommendation**: replace `MetricsResult` with a discriminated union of `FlatMetricsResult` and `NestedMetricsResult`, OR keep `total=False` but document the per-call expected shape in each method's docstring.

---

## 5. Latency Tolerance Matrix

This section tabulates every editable canopy UI element with its latency requirements and the recommended transport.

**Latency budget definitions**:

- **p50**: median wall-clock from user action (or backend event) to UI reflection
- **p99**: 99th percentile, used for "feels broken" threshold
- **acceptable**: maximum tolerable p50 before users perceive UI as laggy

### 5.1 Editable UI elements (parameter inputs)

| Component ID                              | Parameter                           | Edit semantics      | Current path                | p50 (est.) | Target p50† | Recommended                | Notes                                                 |
|-------------------------------------------|-------------------------------------|---------------------|-----------------------------|------------|-------------|----------------------------|-------------------------------------------------------|
| `nn-learning-rate-input`                  | `nn_learning_rate`                  | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 100 ms      | **WebSocket `set_params`** | Users tweak and want immediate feedback in loss curve |
| `nn-max-hidden-units-input`               | `nn_max_hidden_units`               | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     | Affects when training stops; medium urgency           |
| `nn-max-total-epochs-input`               | `nn_max_total_epochs`               | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     | Same as above                                         |
| `nn-max-iterations-input`                 | `nn_max_iterations`                 | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     | Same as above                                         |
| `nn-patience-input`                       | `nn_patience`                       | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     | Same as above                                         |
| `nn-growth-convergence-threshold-input`   | `nn_growth_convergence_threshold`   | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 100 ms      | **WebSocket `set_params`** | Affects when growth triggers; tight feedback loop     |
| `nn-growth-trigger-radio`                 | `nn_growth_trigger`                 | discrete (radio)    | REST POST `/api/set_params` | 100-300 ms | 500 ms      | REST OK                    | One-shot toggle, low urgency                          |
| `nn-init-output-weights-dropdown`         | `nn_init_output_weights`            | discrete (dropdown) | REST POST `/api/set_params` | 100-300 ms | 500 ms      | REST OK                    | One-shot toggle                                       |
| `nn-spiral-rotations-input`               | `nn_spiral_rotations`               | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 500 ms      | REST OK                    | Dataset regen — slow operation anyway                 |
| `nn-dataset-elements-input`               | `nn_dataset_elements`               | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 500 ms      | REST OK                    | Dataset regen                                         |
| `nn-dataset-noise-input`                  | `nn_dataset_noise`                  | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 500 ms      | REST OK                    | Dataset regen                                         |
| `cn-pool-size-input`                      | `cn_pool_size`                      | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     | Affects next candidate cycle                          |
| `cn-correlation-threshold-input`          | `cn_correlation_threshold`          | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 100 ms      | **WebSocket `set_params`** | Tight loop with candidate progress display            |
| `cn-training-iterations-input`            | `cn_training_iterations`            | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     |                                                       |
| `cn-training-convergence-threshold-input` | `cn_training_convergence_threshold` | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     |                                                       |
| `cn-patience-input`                       | `cn_patience`                       | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 200 ms      | WebSocket `set_params`     |                                                       |
| `cn-candidate-learning-rate-input`        | `cn_candidate_learning_rate`        | live (debounced)    | REST POST `/api/set_params` | 100-300 ms | 100 ms      | **WebSocket `set_params`** | Same urgency as nn_learning_rate                      |

**Summary**: 11 of 17 editable parameters benefit from WebSocket transport; 6 are acceptable on REST.

**† Footnote on the "Target p50" column**: these are engineering targets, not validated user requirements.
Per §5.7, validation requires a 5-subject think-aloud study.
Until that runs, treat the urgency tier (hot/warm/cold) as a hypothesis.
**Sliders specifically**: the slider handle motion is always <16 ms (clientside DOM, no round-trip needed); the target column applies only to the `set_params` dispatch at debounce-fire, not to the perceived responsiveness of the slider itself.
See §5.3.1 for the ack-vs-effect distinction.

### 5.2 Real-time output / observation elements

| Component                                  | Updates from                       | Update rate                            | Current path                        | p99 latency | Recommended transport            | Notes                                        |
|--------------------------------------------|------------------------------------|----------------------------------------|-------------------------------------|-------------|----------------------------------|----------------------------------------------|
| `MetricsPanel` (loss chart)                | cascor `metrics` events            | up to 1 / 25 epochs (i.e., 1-10 Hz)    | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | Polling at 100ms waste bandwidth + lags push |
| `CandidateMetricsPanel` (cand corr)        | cascor `candidate_progress` events | up to (pool_size × 1/50 epoch)         | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | High burst rate during candidate phase       |
|                                            |                                    | -- per cycle (10-50 Hz burst)          |                                     |             |                                  |                                              |
| `NetworkVisualizer` (cytoscape graph)      | cascor `cascade_add` events        | bursty, low (one per growth iteration) | REST polling at 5000 ms + on-demand | 500 ms      | **WebSocket push**               | Currently misses events between polls        |
| `DecisionBoundary` (contour plot)          | cascor `topology` updates          | low (one per growth iteration)         | REST polling at 5000 ms             | 1 s         | REST OK                          | Low frequency, large payload — REST is fine  |
| `DatasetPlotter` (scatter)                 | dataset regen events               | one-shot                               | REST one-shot on training start     | 1 s         | REST OK                          | One-shot                                     |
| Training status badge                      | `state` events (status trans)      | low (every status change)              | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | Reflect status changes immediately           |
| `phase_detail` indicator                   | `state` events (phase trans)       | low                                    | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | Same as above                                |
| `grow_iteration` / `grow_max` progress bar | `state` events                     | per-iteration                          | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | Same as above                                |
| `best_correlation` display                 | `state` events (per cand)          | per-candidate cycle                    | REST polling at 100 ms              | 200 ms      | **WebSocket push**               | Same as above                                |
| `phase_started_at` / phase duration        | `state` events + client timer      | clientside ticking                     | REST polling for phase changes      | 200 ms      | **WebSocket push** phase change; | Hybrid correct                               |
|                                            |                                    |                                        |                                     |             | -- client JS- sec-cnt            |                                              |

**Summary**: 8 of 10 observation elements need WebSocket push; 2 are fine on REST.

### 5.3 Latency budget rationale

Why **100 ms** for the most urgent elements:

- Below 100 ms is generally perceived as "instant" (Nielsen Norman Group, 1968 / Card-Robertson-Mackinlay 1991, replicated many times)
- Above 100 ms users start to perceive the system as "responding" rather than "instant"
- Above 300 ms users perceive lag
- Above 1 s users may switch tasks or repeat their action

The `learning_rate`, `correlation_threshold`, and `convergence_threshold` parameters are tight-feedback-loop knobs — users tweak and immediately watch the loss curve to see the effect. A 300 ms REST round-trip + a 100 ms polling delay = 400 ms total, well into the laggy zone.

Why **200 ms** for the broader parameter set:

- Acceptable for non-critical-loop parameters like `max_hidden_units` where the user adjusts and waits to observe the effect over many seconds.

Why **REST is OK for some parameters**:

- Discrete radio/dropdown changes happen rarely (one click) and don't benefit from sub-100ms latency.
- Parameters that trigger expensive backend operations (dataset regeneration) are bottlenecked elsewhere and the transport is not the limiting factor.

### 5.3.1 Critical caveat: ack latency vs. effect observation latency

**The §5.1 latency thresholds apply to ack latency, not effect-observation latency.** For a `learning_rate` slider whose feedback signal is the *loss chart*, the user's perceived-latency loop is:

```bash
slider release → debounce (250 ms) → set_params dispatch → cascor receives →
  next epoch boundary (typically 100-1000 ms) → metrics emit → WS broadcast →
  browser receives → store update → Plotly extendTraces → user sees the curve bend
```

The transport hop (`set_params dispatch → cascor receives`) is one of ~7 stages, and on a real training run the *next-epoch* stage alone can exceed the entire 100 ms budget. **The 100 ms target is for control feedback (slider handle responds locally) and ack latency (the dispatch round-trip), not for the full effect loop.** Slider handle motion is always <16 ms (clientside DOM, no round-trip needed).

Three distinct latency concepts the document distinguishes:

| Concept                        | Definition                                   | Target                                                 | Achieved by                         |
|--------------------------------|----------------------------------------------|--------------------------------------------------------|-------------------------------------|
| **Control feedback latency**   | Slider/input → DOM updates locally           | <16 ms                                                 | Dash clientside (no network)        |
| **Ack latency**                | Slider/input → backend confirmation          | <100 ms (hot params) / <200 ms (warm) / <500 ms (cold) | WebSocket (hot/warm) or REST (cold) |
| **Effect observation latency** | Slider/input → user observes result on chart | dominated by training step time (100 ms - 10 s)        | not affected by transport choice    |

**Implication for Phase C urgency**: Phase C (canopy → cascor `set_params` over WebSocket) optimizes ack latency, which is invisible inside the much-larger effect observation loop for actively-training networks. **Phase C should be re-prioritized from P1 to P2** pending §5.6 production measurement showing whether ack latency is actually a user pain point. The §5.1 matrix's "WebSocket required" column should be relabeled "WebSocket preferred."

### 5.4 Backend event latency budgets

For the *cascor → browser* direction:

| Event class                 | Typical rate                 | p99 latency budget | Justification                                        |
|-----------------------------|------------------------------|--------------------|------------------------------------------------------|
| `metrics` (per-epoch loss)  | 1-10 Hz                      | 100 ms             | Should appear "live" on the loss chart               |
| `candidate_progress`        | 10-50 Hz burst               | 200 ms             | Burst rate is high; some coalescing is acceptable    |
| `state`                     | 1 Hz throttled               | 200 ms             | Status changes should feel immediate                 |
| `cascade_add`               | <1 Hz (per growth iteration) | 100 ms             | Visual events that the user is actively watching for |
| `topology` (full)           | <0.1 Hz                      | 500 ms             | Rare and expensive                                   |
| `event` (training_complete) | one-shot                     | 200 ms             | User waits for completion notification               |

### 5.5 End-to-end frame budget

A 60 fps target gives the browser **16.67 ms per frame**. Every WebSocket event whose result must appear on a chart consumes some of that budget. The decomposition (estimated, to be verified by §5.6 instrumentation):

| Stage                                                                  | Estimated cost | Optimization                                  |
|------------------------------------------------------------------------|----------------|-----------------------------------------------|
| WebSocket frame parse (JSON)                                           | <1 ms          | Use `JSON.parse` (browser native)             |
| `requestAnimationFrame` coalesce (batch events arriving in same frame) | <1 ms          | rAF scheduler                                 |
| `dcc.Store` write via `dash.set_props` or drain callback               | ~2 ms          | Single store update per frame, not per event  |
| Dash callback graph walk (server-side or clientside)                   | ~3 ms          | Minimize Input fan-out per chart              |
| Plotly chart update via `Plotly.extendTraces()` (incremental)          | ~5 ms          | **MUST use extendTraces, not figure replace** |
| Browser paint                                                          | ~5 ms          | (browser-controlled)                          |
| **Total budget**                                                       | **~17 ms**     | **fits within one frame at 60 fps**           |

**Without these optimizations** (current architecture using full figure replace via Dash callback Output):

| Stage                                   | Estimated cost            |
|-----------------------------------------|---------------------------|
| Plotly full figure rebuild (10k points) | ~80-200 ms                |
| Dash diff + roundtrip                   | ~10-30 ms                 |
| Total                                   | **~90-230 ms per update** |

At 100-200 ms per update, the dashboard cannot sustain >5 Hz refresh — and at 50 Hz candidate progress event rates the chart enters main-thread starvation. **Phase B is therefore not just "wire WebSocket data into the store"; it must also include `Plotly.extendTraces()` migration AND rAF-based coalescing**, or it will ship and feel *worse* than the current 100 ms REST polling.

Tracked as **GAP-WS-23 (P1)** in §7: clientside chart updates must use `Plotly.extendTraces()` with `maxPoints` parameter, not full figure replacement.

### 5.6 Production latency measurement plan

Latency budgets without instrumentation are wishes. Phase B+ must include:

1. **Server-side timestamp**: every cascor WebSocket message embeds `emitted_at_monotonic` (cascor's `time.monotonic()`).
2. **Browser-side receive time**: clientside callback records `received_at = performance.now() + clock_offset` where `clock_offset` is the difference between server's wall-clock (sent in `connection_established`) and the browser's `Date.now()`.
3. **Histogram aggregation**: a clientside JS module bucketizes per-event-type latencies into Prometheus-style buckets `{50, 100, 200, 500, 1000, 2000, 5000} ms`.
4. **Periodic export**: every 60 s, the JS module POSTs the histogram to a new canopy `/api/ws_latency` REST endpoint.
5. **Canopy backend**: aggregates submissions into a process-wide Prometheus histogram metric `canopy_ws_delivery_latency_ms_bucket{type=...}`.
6. **Dashboard panel**: a small "WebSocket health" panel in the canopy dashboard displays p50/p95/p99 latency per event type, updated via the same WebSocket path it measures (closing the loop).

The §5.1 / §5.4 budget tables become **SLOs verified against the histogram**, not aspirations.

Tracked as **GAP-WS-24 (P2)** in §7. Phase B includes the instrumentation; Phase C+ uses the data to validate (or invalidate) the latency thresholds.

### 5.7 User research validation plan

The §5.1 / §5.4 thresholds are engineering aspirations, not validated user requirements. To convert them into requirements:

1. Recruit 3-5 ML researchers who actively use the canopy dashboard.
2. Record screen + think-aloud during 5 real training runs each.
3. Mark timestamps where the subject expresses impatience ("why isn't that updating?", "is it stuck?", clicking the same button twice).
4. Correlate with measured latency from §5.6.
5. Revise the §5.1 matrix with empirical thresholds.

Until this research runs, label the §5.1 "Acceptable p50" column "Target p50 (unvalidated)" and treat the urgency tier (hot/warm/cold) as a hypothesis.

---

## 6. Transport Split Design

Given the latency tolerance matrix, here is the recommended transport for every operation in scope.

### 6.1 Per-operation transport recommendation

| Operation                                         | Direction                 | Recommended transport                          | Endpoint                    | Rationale                                    |
|---------------------------------------------------|---------------------------|------------------------------------------------|-----------------------------|----------------------------------------------|
| Real-time metrics emission                        | cascor → browser          | **WebSocket**                                  | `/ws/training`              | Push-based, low latency, no polling waste    |
| Real-time candidate progress                      | cascor → browser          | **WebSocket**                                  | `/ws/training`              | High burst rate; polling cannot keep up      |
| Real-time state updates                           | cascor → browser          | **WebSocket**                                  | `/ws/training`              | Status changes need immediate UI reflection  |
| Cascade-add events                                | cascor → browser          | **WebSocket**                                  | `/ws/training`              | Bursty, visual; polling misses events        |
| Topology snapshots (after cascade_add)            | cascor → browser          | **WebSocket** (re-fetched via REST internally) | `/ws/training`              | Adapter already re-fetches; broadcast result |
| Training control (start/stop/pause/resume/reset)  | browser → canopy → cascor | **WebSocket**                                  | `/ws/control` (both ends)   | RPC pattern with command_response acks       |
| Hot parameter updates (learning rate, thresholds) | browser → canopy → cascor | **WebSocket `set_params`**                     | `/ws/control` (both ends)   | Sub-100ms latency budget                     |
| Cold parameter updates (radio/dropdown one-shots) | browser → canopy → cascor | **REST PATCH**                                 | `/api/v1/training/params`   | Existing REST path is fine                   |
| Initial state hydration                           | browser → canopy → cascor | **REST GET**                                   | `/api/v1/training/status`   | One-shot on page load                        |
| Historical metrics fetch                          | browser → canopy → cascor | **REST GET**                                   | `/api/v1/metrics/history`   | Bulk, one-shot per page load (or pagination) |
| Decision boundary                                 | browser → canopy → cascor | **REST GET**                                   | `/api/v1/decision-boundary` | Slow, large, infrequent                      |
| Dataset arrays                                    | browser → canopy → cascor | **REST GET**                                   | `/api/v1/dataset/data`      | Slow, large, infrequent                      |
| Network statistics (full topology dump)           | browser → canopy → cascor | **REST GET**                                   | `/api/v1/network/topology`  | Slow, large, infrequent                      |

### 6.2 Why this split is correct

**Principle**: WebSocket carries events; REST carries documents. The dashboard's job is to render an initial document (REST snapshot at page load) and then merge live events into it (WebSocket push). This is the pattern every modern real-time dashboard uses (Grafana, Datadog, etc.).

The current REST-only design fails on three axes that matter:

1. **Floor latency** equal to the polling interval, regardless of tuning. At 100 ms polling the user-perceived latency is bounded below by 100 ms even when the underlying event happened 99 ms before the poll. WebSocket push has zero floor latency (events arrive when they occur).
2. **Event loss** for any event frequency above the Nyquist limit of the poll rate. At 10 Hz polling, a 50 Hz `candidate_progress` burst loses 80% of events — the dashboard sees only one in five updates. The lost events cannot be recovered without sequence numbers and a replay protocol (GAP-WS-13).
3. **Wasted CPU** on both ends processing no-op polls. Most polls return data the dashboard already has. Server-side this scales linearly with the number of dashboards; client-side it scales linearly with the polling rate. WebSocket has zero no-op work.

Bandwidth is *not* the primary concern at typical payload sizes (10 Hz × 2 KB = 20 KB/s is negligible). The exception is the `/api/metrics/history` polling endpoint specifically, which returns ~300 KB per request × 10 Hz = ~3 MB/s of waste — see GAP-WS-16. That single endpoint is the concrete P0 motivator for the migration.

### 6.3 Hybrid pattern: page load + live merge

The recommended pattern for every panel:

1. **Page load**: REST GET to fetch the initial snapshot (state, metrics history, topology, params).
2. **Subscribe**: open WebSocket to canopy `/ws/training`. Browser receives all subsequent events.
3. **Live merge**: each WebSocket event mutates the local state in the appropriate `dcc.Store`.
4. **Reconnection**: on WebSocket disconnect, fall back to REST polling at **1 Hz** (well below the previous 100 ms rate; matches the `state` broadcast cadence) until the WebSocket is restored. On reconnect, follow the §6.5 resume protocol.

**Polling toggle (P1, GAP-WS-25)**: when WebSocket is connected, REST polling MUST be disabled (or reduced to a 5-10 s liveness probe).
Concurrent WebSocket push + 100 ms REST polling produces duplicate points and off-by-one bugs in merge logic.
The mechanism: a `ws-connection-status` `dcc.Store` is populated via the same Option B Interval drain pattern as `ws-metrics-buffer` (NOT written directly from JS — that's the impossibility called out in §1.3).
Concretely: `window.cascorWS.onStatus(handler)` writes `{connected: bool, ...}` to a `window._juniper_ws_status` JS global; a `clientside_callback` fires on `dcc.Interval(id="status-poll", interval=500, n_intervals)` and drains the global into `ws-connection-status.data`.
The polling callback's first action is then to read the (server-side) status store and `return no_update` if connected:

```python
@callback(
    Output("metrics-panel-metrics-store", "data"),
    Input("fast-update-interval", "n_intervals"),
    State("ws-connection-status", "data"),
)
def _update_metrics_store_handler(_, ws_status):
    if ws_status and ws_status.get("connected"):
        return no_update  # WebSocket is driving; do not duplicate
    return requests.get(self._api_url("/api/metrics/history?limit=1000"), timeout=2).json()
```

This is the pattern used by every modern real-time dashboard (Grafana, Datadog, etc.) and is what the canopy infrastructure was *intended* to support but does not currently wire up.

### 6.4 Disconnection Taxonomy & Recovery

| Scenario                                                  | Close code                                                           | Cause                                  | Browser response                                                                         |
|-----------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------|------------------------------------------------------------------------------------------|
| Browser tab closed                                        | 1001                                                                 | User action                            | (no recovery needed; connection cleaned up server-side via §2.2 `disconnect()`)          |
| Server graceful shutdown                                  | 1001                                                                 | `close_all()` during cascor restart    | Backoff reconnect, on success run §6.5 resume protocol                                   |
| Network partition (WiFi drop, TCP half-open)              | 1006 (abnormal) — detect after 2nd timeout, not detect w/o heartbeat | OS-level connection loss               | Heartbeat (GAP-WS-12) detect in `<heartbeat_interval × 3>`sec; backoff reconnect         |
| Slow client kicked (Phase E)                              | 1008 (Policy Violation)                                              | Server's send queue overflow           | Backoff reconnect, run §6.5 resume protocol; user-visible "lost real-time updates" badge |
| Auth failure on connect                                   | 4001 (application)                                                   | Invalid `X-API-Key` or expired session | **Do NOT reconnect-loop**; show "authentication required" UI and stop                    |
| Auth failure mid-session (key rotated)                    | currently impossible — auth is connect-only                          | (future)                               | Fail loud, do not retry                                                                  |
| Max connections hit                                       | 1013 (Try Again Later)                                               | Cascor's 50-connection cap             | Backoff reconnect with extra jitter (different schedule from regular reconnects)         |
| Frame > 64 KB on `/ws/control`                            | 1009 (Message Too Big)                                               | Client bug                             | Log error, do NOT reconnect — fix the client                                             |
| Frame > 64 KB on `/ws/training` outbound (e.g., topology) | (undefined behavior, likely framework-level close connection)        | Server bug                             | See §3.1.8 — topology must be chunked or sent via REST                                   |

**Heartbeat (GAP-WS-12, promoted to P1)**: without an application-layer ping/pong, network partitions are silently undetectable except by the cascor server's TCP send timeout (which can be minutes). Implementation:

- Browser sends `{"type": "ping", "timestamp": <iso8601>}` every 30 seconds on `/ws/training`.
- Server replies with `{"type": "pong", "timestamp": <iso8601>}` (already builder-defined, see §3.3.5).
- If the browser does not receive a `pong` within 5 seconds of sending `ping`, it closes the connection with code 1001 and triggers reconnect.

Note: protocol-layer `ping`/`pong` (RFC 6455 §5.5.2/5.5.3) is handled transparently by uvicorn's `websockets` library and never reaches application code. Chromium sends those automatically at ~60s intervals; Safari and Firefox do not. Application-layer JSON `ping`/`pong` is the only cross-browser way to detect silent connection loss.

### 6.5 Reconnection Protocol (sequence numbers + replay)

**The current architecture loses events emitted during the reconnect window.** A `cascade_add` that fired during a 5-second WiFi blip is permanently lost to any consumer that needed the event itself (animation, toast notification). Metrics history is retrievable via `/api/metrics/history`, but the envelope has no sequence number, so the client cannot tell "did I miss any events?"

**GAP-WS-13 (P1) — Lossless reconnect via sequence numbers and replay buffer.** Required components:

1. **Sequence number on every server→client message**: cascor `WebSocketManager` maintains a monotonic `_next_seq: int` (resets on cascor process start). Every outbound message envelope gains a `seq` field:

   ```json
   {"type": "metrics", "timestamp": ..., "seq": 12345, "data": {...}}
   ```

2. **Server instance identity in `connection_established`**: the initial message advertises BOTH `server_instance_id` (a UUID4 generated at cascor process startup) AND `server_start_time` (a Unix timestamp, advisory only — for human operators reading logs). Clients compare instance IDs by EQUALITY, not ordering. The UUID-based identity is immune to clock skew, NTP rewind, and process-restart timestamp collisions:

   ```json
   {"type": "connection_established", "timestamp": ..., "data": {"connections": 3, "server_instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "server_start_time": 1712707000.0}}
   ```

3. **Replay buffer**: cascor `WebSocketManager` maintains a bounded ring buffer of the last 1024 events with their `seq` numbers. Bounded so memory is constant.
4. **Resume request on reconnect**: after a successful reconnect, the browser sends `{"type": "resume", "data": {"last_seq": N, "server_instance_id": "<uuid>"}}` as its first frame.
5. **Server resume handling**:
   - If `server_instance_id != current_server_instance_id`: the cascor process restarted (or this is a different cascor instance entirely). Reply with `{"type": "resume_failed", "data": {"reason": "server_restarted"}}`. Browser fetches a full REST snapshot.
   - If `last_seq < (current_seq - 1024)`: requested resume point is outside the replay buffer. Reply with `resume_failed` reason `out_of_range`. Browser fetches a full REST snapshot.
   - Otherwise: replay every event with `seq > last_seq` from the ring buffer, then resume normal live streaming.
6. **Client merge**: when replaying, the browser increments `seq` and applies events normally. If the live stream resumes mid-replay, events are processed in `seq` order via a small reorder buffer.

This protocol guarantees **no event loss** on reconnect within the 1024-event replay window, and **detected drift** outside it (forcing a snapshot refresh).

#### 6.5.1 Thread-safety contract for `_next_seq` and the replay buffer

All `_next_seq` increments AND ring buffer appends MUST happen on the event loop thread under a lock. Two implementation options:

**Option 1 — Reuse `WebSocketManager._lock`**: simpler but contends with the broadcast fan-out loop (which holds the lock during `broadcast()` iteration per GAP-WS-07). A slow client holding the lock during `broadcast()` blocks every subsequent seq assignment. **This option is acceptable ONLY if Phase E (GAP-WS-07 backpressure with per-send timeout) lands before or together with Phase B (GAP-WS-13 sequence numbers).**

**Option 2 — Add a separate `_seq_lock: asyncio.Lock()`**: finer-grained lock that protects only the seq counter and the replay buffer. Doesn't contend with the broadcast iteration. Order of acquisition: `_seq_lock` BEFORE `_lock` if both are needed (consistent ordering prevents deadlock). **Recommended** to decouple the seq assignment from the slow-client risk.

**The training thread MUST route through `broadcast_from_thread` → `run_coroutine_threadsafe`** so that the seq number is assigned and the ring append happens on the loop thread, not on the training thread. Without this, two writers race and the resume protocol's `seq > last_seq` invariant breaks silently.

**All outbound paths funnel through a single `_assign_seq_and_append(msg)` helper on the loop thread.** This includes both `broadcast()` (loop-thread direct callers like REST handlers) and `broadcast_from_thread()` (sync-thread callers like training callbacks). No caller may write directly to `_active_connections` — verified against `manager.py:41-146` on 2026-04-10.

**Resume replay must copy the ring buffer under the lock** before iterating, then iterate the copy outside the lock (same copy-then-iterate pattern as `close_all()`, but with the lock actually held during the copy).

**Shutdown race**: if `broadcast_from_thread` is called during loop shutdown, `run_coroutine_threadsafe` raises and NO seq is consumed. The ring buffer and `_next_seq` remain consistent. See GAP-WS-29 for the exception-handling path.

The replay buffer is a `collections.deque(maxlen=1024)` of `(seq, message)` tuples. **Memory cost**: ~600 KB per `WebSocketManager` instance for the average case (1024 events × ~600 B/event average). **Worst case** (buffer dominated by ~1 KB `state` events and ~600 B dual-format `metrics` events): up to ~2 MB per instance. Documented for operators. Documented for operators in §10 RISK note.

#### 6.5.2 Snapshot → live handoff atomicity

When a client falls back to a REST snapshot (after `out_of_range` or `server_restarted`), the snapshot fetch and live stream attach must be coordinated to avoid an event-loss gap:

1. Client closes the WebSocket explicitly (don't reuse the broken connection).
2. Client fetches the REST snapshot.
    - **The snapshot endpoint MUST read both the state payload and `snapshot_seq` atomically** under the same lock that serializes ring-buffer appends — i.e., `async with manager._lock: snapshot = build_snapshot(); snapshot_seq = manager._next_seq`.
    - Without this atomicity, a torn read is possible: the snapshot includes events through state-seq=N but `snapshot_seq` returns N-1 because the seq counter hasn't been incremented yet — causing event N to be replayed AND already-applied, breaking idempotency for any non-keyed merge.
3. Client renders the snapshot data to its store.
    - **Chart redraw uses `Plotly.react(graphId, newData, layout)`** (NOT `extendTraces`) so the chart cleanly replaces its data with the snapshot, preserving pan/zoom state.
    - Existing displayed points are discarded; the user sees a brief flash (<100 ms) rather than overlapping stale and fresh data.
4. Client opens a new WebSocket and immediately sends `{type: "resume", data: {last_seq: snapshot_seq, server_instance_id: "<uuid>"}}` as its first frame.
5. Server replays any events with `seq > snapshot_seq` from the ring buffer (most likely 0-2 events between snapshot and reconnect), then resumes live streaming.
6. Client continues with `extendTraces` for subsequent live events.

**Idempotent replay contract**: clients MUST treat replay as idempotent. Events with `seq <= snapshot_seq` received during the resume window (e.g., late-arriving messages from a stale connection) are discarded by the client based on `seq` check. This is the second-line defense against any §6.5.2 atomicity bug.

This guarantees no events are missed in the gap between snapshot read and WebSocket attach.

**Snapshot fetch retry policy**: client retries snapshot fetch with exponential backoff (1 s, 2 s, 4 s, 8 s, 16 s, 30 s, cap at 30 s), up to 10 attempts.
While retrying, connection indicator shows "Restoring data…".
If all 10 attempts fail, indicator shows "Unable to restore data — click to retry manually", and the chart displays its stale pre-restart data with a red 'stale' overlay.
The WebSocket is NOT reopened until a snapshot succeeds (otherwise live events would be applied on top of stale baseline).
On 500/4xx/schema-invalid responses, treat as retryable failure; on 3 consecutive schema-invalid responses (not network errors), escalate to "cascor version incompatible" red banner and stop retrying.

#### 6.5.3 Edge cases

- **Client localStorage cleared mid-session**: if the browser cannot find a saved `last_seq`, the client treats this as `out_of_range` and falls back to a full REST snapshot.
- **Browser tab close grace period**: cascor's `disconnect()` cleans up immediately on receiving close code 1001.
  - To allow fast reopen-resume, the replay buffer entries are NOT purged on disconnect — they remain for any future client that reconnects with a matching `server_start_time` and a `last_seq` within the window.
- **Older cascor servers without GAP-WS-13**: a server that doesn't recognize the `resume` command will respond with `command_response` containing `status: "error", error: "Unknown command: resume"`
  - (verified against `juniper-cascor/src/api/websocket/control_stream.py:55-59` — the early-return path actually sends a `create_control_ack_message` error response, NOT a silent drop).
  - The client should match on `status: "error"` with the resume command name AND fall back to the full REST snapshot.
  - Optimization: cache the "server supports resume" fact in `localStorage` keyed by `server_instance_id` so subsequent reconnects to the same server instance skip the probe.

#### 6.5.4 Backwards-compat: new envelope fields

The `seq` field on every message and the `server_instance_id` on `connection_established` are **additive fields** (not replacing existing fields).
Any client performing strict-key (closed-schema) validation must be updated.
The juniper-cascor-client SDK parses messages as plain dicts via `json.loads()` (verified at `juniper-cascor-client/juniper_cascor_client/ws_client.py:73,181,210`) — there are no Pydantic models or other strict schema validators in the SDK, so unknown envelope fields are naturally ignored by any consumer that uses `.get()` / indexed access.
Document the additive change in the cascor `messages.py` CHANGELOG.

**Subprotocol implication**: this is technically a v1.1 envelope (additive fields).
Per §7.34, an additive change does NOT warrant a `Sec-WebSocket-Protocol` subprotocol bump because dict-based consumers are forward-compatible by construction.
If a future change is non-additive (renamed or removed fields), introduce `juniper-cascor.v2` at that time.

---

## 7. Missing / Broken Pieces (Enumerated)

Each item below has: a unique ID, severity (P0-P3), location, current state, target state, and a remediation hook.

### 7.1 GAP-WS-01 — `juniper-cascor-client` lacks WebSocket `set_params`

- **Severity**: P1
- **Location**: `juniper-cascor-client/juniper_cascor_client/ws_client.py`
- **Current state**: `CascorTrainingStream.send_command()` (line 87) is generic; `CascorControlStream.command()` (line 193) supports control verbs but not `set_params`.
- **Target state**: a dedicated `CascorControlStream.set_params(params, timeout=5.0) -> dict` method that:
  1. validates params against the same whitelist as cascor server
  2. sends `{command: "set_params", params: ...}` over the control WS
  3. waits up to `timeout` seconds for a `command_response` with matching `command` field
  4. raises `CascorParamError` on validation failure or `CascorTimeoutError` on timeout
  5. returns the `result` dict on success
- **Remediation hook**: this is the first piece to land. Adding it does not require changes to cascor server (already supports it) or canopy (will use it after Phase B).

### 7.2 GAP-WS-02 — Browser-side `cascorWS` / `cascorControlWS` are dead code

- **Severity**: **P1** (raised from P2 — this is the foundation of the entire browser-side WebSocket layer; without it Phase B has no anchor)
- **Location**: `juniper-canopy/src/frontend/assets/websocket_client.js` (`window.cascorWS`, `window.cascorControlWS`)
- **Current state**: file is auto-loaded by Dash; constructor runs and opens WebSocket connections; no callback or component code references the global instances.
- **Target state**: integrate them into the dashboard. **Decision: do NOT delete.** The class has the right API surface (`on()`, `send()`, buffered reconnect, status callbacks) and §7.3/§7.4/§7.5 remediation hooks depend on `window.cascorWS` existing. A future deletion would force re-implementation. This decision is final to avoid churn.
- **Remediation hook**: the integration is the foundation for §7.4 and §7.5. See §1.3 for the discussion of the three options (`dash.set_props` / Interval drain / `dash-extensions.WebSocket`); Option B (Interval drain) is the recommended primary path.

### 7.3 GAP-WS-03 — Parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490`

- **Severity**: P2
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py:1490-1526`
- **Current state**: clientside callback opens its own WebSocket to `/ws/training`, populates three `window._juniper_ws_*` JS globals, and (in the case of `ws-metrics-buffer`) returns `no_update` so the corresponding store is never written to.
- **Target state**: delete this callback in favor of using `assets/websocket_client.js`'s `window.cascorWS` (after §7.2 integration).
- **Remediation hook**: delete and replace with a clientside_callback that wraps `window.cascorWS.on('metrics', handler)` to push into the metrics store.

### 7.4 GAP-WS-04 — `ws-metrics-buffer` store never populated

- **Severity**: P1
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py:1490` (declared input/output) plus the body which returns `no_update`
- **Current state**: store declared, callback declares it as Output, body returns `no_update` so the store always has the empty initial value.
- **Target state**: a clientside_callback (preferably driven by `window.cascorWS.on('metrics', ...)`) that appends to the store on each WebSocket event. The store should be a bounded ring buffer (e.g., last 1000 metrics) to avoid unbounded memory growth.
- **Remediation hook**: combined with §7.5 below.

### 7.5 GAP-WS-05 — No clientside callback drains WS stores into chart inputs

- **Severity**: P1
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py` (no callback exists)
- **Current state**: even after `ws-topology-buffer` and `ws-state-buffer` are populated by their drain callbacks, no chart or panel callback uses them as Input. Charts read from `metrics-panel-metrics-store` which is fed by REST polling.
- **Target state**: each chart/panel callback should accept the relevant `ws-*-buffer` store as an additional Input, merging it with the REST-fetched snapshot. The pattern is:

  ```python
  @callback(Output("metrics-panel-figure", "figure"),
            Input("ws-metrics-buffer", "data"),
            Input("metrics-panel-metrics-store", "data"))
  def render_metrics(ws_events, snapshot): ...
  ```

- **Remediation hook**: depends on §7.4.

### 7.6 GAP-WS-06 — Training control buttons use REST POST instead of WebSocket

- **Severity**: P2
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py:2522-2575` (`_handle_training_buttons_handler()`)
- **Current state**: button handler calls `requests.post(self._api_url("/api/train/{command}"), timeout=2)`.
- **Target state**: a clientside_callback that calls `window.cascorControlWS.send({command: ...})` and listens for the `control_ack`. Falls back to REST POST on WebSocket disconnect.
- **Remediation hook**: requires §7.2 integration first.

### 7.7 GAP-WS-07 — No backpressure / slow client handling in cascor `WebSocketManager`

- **Severity**: **P2** (raised from P3 — slow client serially blocks all broadcasts because `broadcast()` iterates connections synchronously, and there is no per-send timeout. Even in single-canopy deployments a hung dev-tools tab can degrade the dashboard for everyone.)
- **Location**: `juniper-cascor/src/api/websocket/manager.py:101-110` (`broadcast()` loop)
- **Current state**: `broadcast()` iterates active connections and calls `websocket.send_json()` synchronously per client. **No per-send timeout** — a client in TCP half-open state can block the loop for the full TCP timeout (seconds to minutes). Disconnected clients are pruned only after a send failure.
- **Target state**: two-step fix:
  1. **Quick fix**: wrap each `send_json` in `asyncio.wait_for(send_json, timeout=0.5)`; on timeout, close the client with code 1008 and remove from the active set. This is a one-line patch and addresses the worst slow-client case.
  2. **Full fix**: per-client send queue with bounded depth. Recommended `maxsize=128` (raised from the original draft's 64; at peak event rate ~20/s a 128-deep queue absorbs ~6 seconds of stall). **Policy: close slow client (code 1008) for state-bearing events; drop-oldest for coalesceable progress events** (`candidate_progress` with `maxsize=32` per-type queue). Drop-oldest causes silent stream-ordering corruption for state events but is acceptable for coalesceable progress.
- **Remediation hook**: deferred to Phase E. The quick fix can land independently as a hotfix.

### 7.8 GAP-WS-08 — No end-to-end browser test for the WebSocket path

- **Severity**: P1
- **Location**: `juniper-canopy/src/tests/integration/` (no such test exists)
- **Current state**: there is `tests/integration/test_websocket_control.py` but it tests the canopy server WebSocket endpoints in isolation using a `TestClient`. It does not exercise the browser-side JS or the JS↔Dash store bridge.
- **Target state**: a Playwright (or pytest-playwright) integration test that:
  1. starts a fake cascor server fixture
  2. starts the canopy app pointed at the fake server
  3. opens a real browser
  4. asserts that WebSocket events from the fake cascor server cause the loss chart to update without polling
  5. asserts that clicking the start button issues a WebSocket command (not REST POST) and receives the ack
- **Remediation hook**: see §8 (browser-side verification strategy).

### 7.9 GAP-WS-09 — No cascor-side integration test for `set_params` on `/ws/control`

- **Severity**: P2
- **Location**: `juniper-cascor/src/tests/unit/api/test_websocket_control.py`
- **Current state**: tests cover `start`/`stop`/`pause`/`resume`/`reset` but not `set_params`.
  - The set_params handler exists at `control_stream.py:97-100` but is exercised only by the Phase 1 unit tests added to `test_websocket_control.py` for the routing layer, not the param-update validation layer.
- **Target state**: integration test that opens a `/ws/control` WebSocket, sends `{command: "set_params", params: {learning_rate: 0.005}}`, and asserts the `command_response` reflects the updated value AND that the underlying `lifecycle.network.learning_rate` attribute was actually mutated.
  - Also: negative-path tests for whitelist bypass (`{evil_key: ...}` filtered, no exception), malformed enum (`init_output_weights: "random; rm -rf /"` rejected by Pydantic Literal validator), and per-frame size limit (>64 KB rejected with 1009).
- **Remediation hook**: **Use FastAPI's `TestClient.websocket_connect()` directly** (same pattern as `test_websocket_control.py:71-78`), NOT the SDK.
  - Cascor has no runtime dependency on `juniper-cascor-client` and tests should validate the wire protocol on the server side, not the SDK's interpretation of it.
  - The SDK is only used in Phase G's *canopy*-side tests.

### 7.10 GAP-WS-10 — No canopy-side integration test for `set_params` round-trip

- **Severity**: P2
- **Location**: `juniper-canopy/src/tests/integration/` (no such test exists)
- **Current state**: there is `test_param_apply_roundtrip.py` but it tests the REST PATCH path; nothing exercises the WebSocket path because that path doesn't exist yet.
- **Target state**: integration test that uses a fake cascor WebSocket fixture and asserts that `cascor_service_adapter.apply_params()` (after refactor) issues a `set_params` command on the WebSocket and parses the `command_response`.
- **Remediation hook**: depends on GAP-WS-01 and the subsequent canopy-side adapter refactor.

### 7.11 GAP-WS-11 — Canopy `_normalize_metric` dual format is undocumented for external consumers

- **Severity**: P3
- **Location**: `juniper-canopy/src/backend/cascor_service_adapter.py:516-561`
- **Current state**: see §4. The flat keys are retained "for API/client compatibility" but no in-tree consumer reads them.
- **Target state**: see §4.4. Phased: document as-is, then split helpers, then audit external consumers, then optionally remove.
- **Remediation hook**: do NOT touch in this round; tracked here for completeness.

### 7.12 GAP-WS-12 — No WebSocket heartbeat / ping-pong reciprocity

- **Severity**: **P1** (raised from P3 — without application-layer heartbeat, network partition is undetectable in Safari/Firefox; only Chromium auto-sends protocol-layer pings, creating cross-browser inconsistency)
- **Location**: both cascor and canopy WebSocket layers
- **Current state**: no application-layer `ping`/`pong` frame handling. Canopy server has a `pong` reply type defined but the browser never sends `ping`. Reconnection is triggered only by socket close, which only fires on TCP-level errors (not silent partition).
- **Target state**: browser sends `{type: "ping", timestamp: ...}` every 30 s; server responds with `{type: "pong", timestamp: ...}`; browser closes and reconnects if no `pong` is received within 5 s. See §6.4 disconnection taxonomy for details.
- **Remediation hook**: Phase F. Required before Phase D ships if multi-browser support is a requirement.

### 7.13 GAP-WS-13 — Lossless reconnect via sequence numbers and replay buffer

- **Severity**: **P1**
- **Location**: `juniper-cascor/src/api/websocket/manager.py`, `juniper-cascor/src/api/websocket/messages.py`, `juniper-canopy/src/frontend/assets/websocket_client.js`
- **Current state**: no sequence numbers in the envelope; no replay buffer; no resume protocol. Events emitted during a brief disconnect are silently lost.
- **Target state**: see §6.5 for the full protocol design. Add monotonic `seq: int` to every envelope; cascor maintains a 1024-event ring buffer; clients send `{type: "resume", data: {last_seq, server_start_time}}` on reconnect.
- **Remediation hook**: Phase B-pre (security hardening) or Phase B (browser bridge). Should ship together with the heartbeat (GAP-WS-12) so disconnection detection and recovery are coherent.

### 7.14 GAP-WS-14 — Plotly chart updates must use `extendTraces` with `maxPoints`

- **Severity**: **P1**
- **Location**: `juniper-canopy/src/frontend/components/metrics_panel.py`, `candidate_metrics_panel.py`
- **Current state**: chart updates use Dash callback Output → Plotly figure replace, which rebuilds the entire trace array on every update. For 10k-point charts this costs 80-200 ms per update on mid-range hardware.
- **Target state**: switch chart updates to a clientside callback that calls `Plotly.extendTraces(graphId, {x: [[newX]], y: [[newY]]}, [traceIdx], maxPoints=5000)`. This is O(1) per event regardless of history length AND preserves pan/zoom state. The `maxPoints` argument bounds memory growth (drops the oldest point when the cap is hit).
- **Remediation hook**: Phase B (essential — without this Phase B will ship and feel worse than the current REST polling). See §5.5 frame budget.

### 7.15 GAP-WS-15 — Browser-side rAF coalescing for high-frequency events

- **Severity**: **P1**
- **Location**: `juniper-canopy/src/frontend/assets/websocket_client.js` and the Phase B Interval drain callback
- **Current state**: each WebSocket event triggers a separate Dash store update which triggers a separate chart re-render. At 50 Hz `candidate_progress` burst rates, this exceeds the browser's 60 fps frame budget and causes main-thread starvation.
- **Target state**: events arriving in the same animation frame are batched in a JS-side ring buffer; a `requestAnimationFrame`-driven flush commits at most one store update per frame. Combined with GAP-WS-14 (`extendTraces`), this keeps the per-frame cost under 17 ms.
- **Remediation hook**: Phase B. Implement as a small JS module loaded alongside `websocket_client.js`.

### 7.16 GAP-WS-16 — `/api/metrics/history` polling is the bandwidth bomb (P0 motivator)

- **Severity**: **P0** (this is the strongest concrete reason for the entire migration)
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py:2388-2421` (`_update_metrics_store_handler`)
- **Current state**: every `fast-update-interval` tick (100 ms) issues `requests.get(self._api_url(f"/api/metrics/history?limit={limit}"))`. At `limit=1000` × ~300 B/entry = ~300 KB per response × 10 Hz polling = **~3 MB/s per dashboard** of pure REST waste. With multiple browser tabs open this scales linearly.
- **Target state**: WebSocket push replaces the polling for live metrics; REST `/api/metrics/history` is called ONLY on initial page load and on reconnect snapshot recovery (§6.3 / §6.5). Polling-disabled-when-WS-connected wired via GAP-WS-25 (polling toggle).
- **Remediation hook**: Phase B (browser bridge) + GAP-WS-25 polling toggle.

### 7.17 GAP-WS-17 — `permessage-deflate` compression not configured

- **Severity**: P2
- **Location**: cascor `juniper-cascor/src/api/websocket/manager.py` + uvicorn config
- **Current state**: uvicorn's `websockets` library supports `permessage-deflate` (RFC 7692) but defaults vary by protocol (`wsproto` vs `websockets`). Compression is not explicitly enabled. JSON metrics with repetitive keys typically compress 4-8×, so the 16 KB/s steady-state would drop to ~2-4 KB/s.
- **Target state**: explicitly enable `permessage-deflate` in cascor uvicorn config; verify with a packet capture that the negotiation succeeds.
- **Remediation hook**: low-effort; can land independently in cascor.

### 7.18 GAP-WS-18 — Topology message can exceed 64 KB silently

- **Severity**: **P1** (silent data loss for large networks)
- **Location**: `juniper-cascor/src/api/websocket/messages.py:35-41` (`topology_message` builder)
- **Current state**: topology JSON for a network with H=100 hidden units and input_size=50 ≈ 120-150 KB. The 64 KB inbound cap on `/ws/control` does not apply to outbound messages, but the receiving `juniper-cascor-client` and the browser may have their own receive limits. The doc framework will tear down the connection if the limit is hit.
- **Target state**: chunk topology into `topology_partial: {chunk_index, total_chunks, data}` messages, OR fall back to REST GET `/api/v1/network/topology` for any topology > 32 KB (with WebSocket emitting a `topology_changed` notification only).
- **Remediation hook**: Phase E or Phase H. Can be deferred until a real network exceeds the cap; document the threshold now.

### 7.19 GAP-WS-19 — `close_all()` does not hold `_lock` (CR-025 partial)

- **Severity**: P2
- **Location**: `juniper-cascor/src/api/websocket/manager.py:138-145`
- **Current state**: see §2.2. Copy-then-iterate provides iterator safety but allows orphaned connections during shutdown/connect race.
- **Target state**: wrap the entire `close_all()` body in `async with self._lock:`. Iteration awaits `ws.close()` which is safe under an `asyncio.Lock`.
- **Remediation hook**: low-effort fix; can land independently in cascor.

### 7.20 GAP-WS-20 — Bidirectional envelope asymmetry

- **Severity**: P3
- **Location**: §3.0 above
- **Current state**: server→client uses `{type, timestamp, data}`; client→server commands use `{command, params}` with no envelope.
- **Target state**: normalize to `{type, timestamp, data}` everywhere. New shape for client commands: `{type: "command", timestamp: ..., data: {command: "set_params", params: {...}}}`. Backward-compatible by accepting both shapes during a deprecation window.
- **Remediation hook**: deferred; not blocking any functional work.

### 7.21 GAP-WS-21 — 1 Hz state throttle drops terminal transitions

- **Severity**: **P1** (correctness bug; can leave dashboard in stale terminal state)
- **Location**: `juniper-cascor/src/api/lifecycle/manager.py:133-136`
- **Current state**: simple "drop if `last_broadcast < 1 s ago`" filter. A fast `Started → Failed → Stopped` sequence within 1 s leaves the dashboard showing `Started` forever.
- **Target state**: replace with a debounced coalescer:
  1. Buffer the latest pending state.
  2. Flush at most once per second AND within ~50 ms of the most-recent update.
  3. Bypass the throttle entirely for terminal transitions (`Failed`, `Stopped`, `Completed`).
- **Remediation hook**: cascor PR; can ship independently of the canopy work.

### 7.22 GAP-WS-22 — Protocol error responses not specified

- **Severity**: P2
- **Location**: §3.2.4 above
- **Current state**: malformed JSON, missing `command` field, unknown commands, and handler exceptions are handled inconsistently — some are silently ignored, some return ad-hoc error messages.
- **Target state**: see §3.2.4 table. Standardize close codes (1003, 1009) and `command_response.status: "error"` payloads.
- **Remediation hook**: cascor PR; ships with GAP-WS-09 integration tests that exercise the failure modes.

### 7.23 GAP-WS-23 — `Plotly.extendTraces` with `maxPoints` (alias of GAP-WS-14)

- **Severity**: see GAP-WS-14
- **Note**: this entry was originally enumerated separately but is folded into GAP-WS-14 above. Kept here for reference link integrity.

### 7.24 GAP-WS-24 — Production WebSocket latency instrumentation

- **Severity**: P2
- **Location**: §5.6 above
- **Current state**: no per-message latency measurement; the §5.1 / §5.4 budgets are aspirations, not SLOs.
- **Target state**: see §5.6. Server-side `emitted_at_monotonic` timestamp + browser-side histogram aggregation + canopy `/api/ws_latency` endpoint + Prometheus export.
- **Remediation hook**: Phase B includes the instrumentation; Phase C+ uses the data.

### 7.25 GAP-WS-25 — WebSocket-health-aware polling toggle

- **Severity**: **P1**
- **Location**: `juniper-canopy/src/frontend/dashboard_manager.py:2388-2421` (and similar for other panels)
- **Current state**: REST polling on `fast-update-interval` runs whether or not the WebSocket is connected. After Phase B both paths will be active simultaneously, causing duplicate data and merge bugs.
- **Target state**: a `ws-connection-status` `dcc.Store` written by `window.cascorWS.onStatus()` callback. Each polling callback's first action is to read the status store and `return no_update` if connected. See §6.3 for the code pattern.
- **Remediation hook**: Phase B (essential for the migration to be clean).

### 7.26 GAP-WS-26 — Visible connection status indicator

- **Severity**: **P1**
- **Location**: canopy dashboard header (new component)
- **Current state**: if cascor restarts or the WebSocket disconnects, the dashboard shows a frozen chart with no visible error. The user assumes training stalled.
- **Target state**: a small badge in the dashboard header: green=connected, yellow=reconnecting, red=offline, gray=demo mode. Wired to `window.cascorWS.onStatus()` (which §2.7.1 notes exists but is unused).
- **Remediation hook**: Phase B.

### 7.27 GAP-WS-27 — Per-IP connection caps and DoS protection

- **Severity**: P1 (security hardening)
- **Location**: `juniper-cascor/src/api/websocket/manager.py`
- **Current state**: 50-connection cap is global, not per-IP. Single attacker can starve all slots.
- **Target state**: per-IP cap (e.g., 5), auth-timeout on connect (close in <5 s if no valid auth), command rate limit (e.g., 10 commands/sec per connection).
- **Remediation hook**: M-SEC-04 / M-SEC-05 in §2.9.

### 7.28 GAP-WS-28 — Multi-key `update_params` torn-write race

- **Severity**: P2
- **Location**: `juniper-cascor/src/api/lifecycle/manager.py:702-723` (`update_params`)
- **Current state**: param mutations under `_training_lock` are atomic from the writer's POV, but the training thread reads attributes (e.g., `network.learning_rate`) without acquiring `_training_lock`. CPython single-attribute reads are atomic, but a multi-key update (e.g., changing `learning_rate` AND `patience` together) is observable as a torn read by the training step.
- **Target state**: training thread should snapshot params at the start of each epoch under `_training_lock`, not read them per-step. Document the contract.
- **Remediation hook**: cascor PR; needs careful review.

### 7.29 GAP-WS-29 — `broadcast_from_thread` discards future exceptions

- **Severity**: P3
- **Location**: `juniper-cascor/src/api/websocket/manager.py:112-124`
- **Current state**: the `Future` returned by `run_coroutine_threadsafe` is discarded. If `broadcast()` raises, the exception is silently swallowed. Also: on the shutdown race path, if the loop is closing and `run_coroutine_threadsafe` raises, the coroutine is closed only in the except branch — partial scheduling can leak.
- **Target state**: add `.add_done_callback(lambda f: log_error_if_failed(f))`; wrap in a `try/finally` that calls `coro.close()` on any error path.
- **Remediation hook**: cascor PR; minor but improves debuggability.

### 7.30 GAP-WS-30 — Reconnect backoff has no jitter (thundering herd risk)

- **Severity**: P3
- **Location**: `juniper-canopy/src/frontend/assets/websocket_client.js` reconnect schedule
- **Current state**: exponential backoff `500 ms → 5 s` with no jitter. After a cascor restart, all dashboards reconnect on identical schedules, synchronizing reconnect attempts at t=500 ms, t=1 s, t=2 s, ... — a textbook thundering herd.
- **Target state**: add full jitter: `delay = random.uniform(0, min(cap, base * 2**attempt))`. Three-line change.
- **Remediation hook**: Phase F or earlier; can land independently.

### 7.31 GAP-WS-31 — Unbounded reconnect attempts cap (currently capped at 10)

- **Severity**: P2
- **Location**: `juniper-canopy/src/frontend/assets/websocket_client.js`
- **Current state**: cap at 10 reconnect attempts (~50 s of backoff). Dashboards left open during a long cascor restart will give up reconnecting permanently.
- **Target state**: remove the cap or replace with a ceiling (retry forever at max 30 s intervals). Dashboards should never give up reconnecting; the connection indicator (GAP-WS-26) keeps the user informed.
- **Remediation hook**: Phase F.

### 7.32 GAP-WS-32 — Per-command timeouts and orphaned-command resolution

- **Severity**: P2
- **Location**: `juniper-canopy/src/frontend/assets/websocket_client.js` and the canopy adapter
- **Current state**: 5 s timeout for all `cascorControlWS.send()` calls. If `start` legitimately takes longer (dataset load, network init), the browser shows error while training is actually running.
- **Target state**: per-command timeouts (e.g., `start`: 10 s, `stop`/`pause`/`resume`: 2 s, `set_params`: 1 s). Every command carries a client-generated `command_id` (UUID); cascor echoes it in `command_response`; on timeout the client marks the command "pending verification" and waits for a matching `state` event before declaring failure.
- **Remediation hook**: Phase D. Required for `start` UX correctness.

### 7.33 GAP-WS-33 — Demo mode failure visibility

- **Severity**: P2
- **Location**: `juniper-canopy/src/demo_mode.py` and the connection indicator
- **Current state**: if demo mode's background thread crashes, the dashboard shows a frozen chart with no indication.
- **Target state**: demo mode sets `window.cascorWS.status = "demo"` via a clientside init. On thread crash, status transitions to `"demo-error"` with a visible UI badge (tied to GAP-WS-26).
- **Remediation hook**: Phase B (parity with the connection indicator).

### 7.34 Considered and explicitly deferred (not GAPs)

The following improvements were considered during the round 1 / round 2 validation passes but are intentionally NOT tracked as gaps in this document, with the reasons noted:

- **State diffing (`state_delta` message type)**: would reduce state-broadcast bandwidth ~80-90%. **Deferred** because state events are already 1 Hz throttled — total bandwidth (~1 KB/s for state messages) is not a hotspot. Revisit if the throttle is removed (per GAP-WS-21 debouncer rewrite) AND state event rate goes >5 Hz.
- **JSON float precision trimming (~17 digits → 6)**: would reduce metric payload size ~30-50%. **Deferred** because (a) `permessage-deflate` (GAP-WS-17) will claim most of that savings via repetition compression, (b) a custom JSON encoder adds maintenance burden, (c) the steady-state ~16 KB/s is well within bandwidth budgets. Revisit if compression negotiation fails on a target deployment.
- **Binary encoding (MessagePack/CBOR)**: would reduce both payload size and float overhead. **Deferred** because the entire ecosystem currently uses JSON; switching is a multi-component coordinated change with no operational driver yet.
- **Subprotocol versioning (`Sec-WebSocket-Protocol: juniper-cascor.v1`)**: would enable graceful version migration. **Deferred** until a v2 envelope is needed (currently no breaking schema change is planned).
- **`_normalize_metric` dual format wire-size cost**: the dual format adds ~2× the metric payload size on the wire (~600 B vs ~320 B). **Documented here for completeness**, not tracked as a gap because §4 explicitly says do NOT remove either format until external consumers are audited (GAP-WS-11 Phase H).

---

## 8. Browser-Side Verification Strategy

### 8.1 The objection

The premature deferral of P5-RC-05 in §6.0 of the roadmap was justified with: *"Wiring this requires browser-side JS that I cannot manually verify in a browser from this environment. Getting it wrong silently breaks live metrics."* This is a real constraint but is **not a reason to skip the work** — it is a reason to design verification that does not depend on a manual browser session.

### 8.2 Verification approaches by feasibility

| Approach                               | Feasibility from headless dev environment                       | Coverage                                                           | Recommended                                                          |
|----------------------------------------|-----------------------------------------------------------------|--------------------------------------------------------------------|----------------------------------------------------------------------|
| Manual browser test                    | None (no browser)                                               | Full                                                               | No (not feasible)                                                    |
| Selenium with Chromium headless        | Possible if Chromium available                                  | Full                                                               | Superseded                                                           |
| **Playwright (pytest-playwright)**     | **Possible — bundles its own browser via `playwright install`** | **Full, with raw WebSocket frame introspection**                   | **Yes — for assertions about wire-level WebSocket behavior**         |
| **`dash[testing]` `dash_duo` fixture** | **Possible — uses ChromeDriver via Selenium**                   | **Native understanding of Dash component IDs and store mutations** | **Yes — for assertions about Dash store state and component output** |
| pyppeteer (Chromium control)           | Possible — similar to Playwright                                | Full                                                               | Superseded                                                           |
| JS unit tests via Jest or Vitest       | Always                                                          | JS-only logic (event dispatch, backoff, parsing)                   | Complementary                                                        |
| Mock-based pytest                      | Always                                                          | Low (no real browser)                                              | Complementary                                                        |

**Use both Playwright and `dash_duo`, not just one.** The tools have complementary strengths:

- **`dash_duo`** is the official Dash testing harness. It understands Dash component IDs, waits for clientside callbacks, and resolves store mutations natively. Phase B's entire premise is "clientside_callback writes into `dcc.Store`" — exactly what `dash_duo.wait_for_text_to_equal()` / `wait_for_style_to_equal()` validates. Use it for assertions about *what's in the store* and *what's rendered*.
- **Playwright** has no notion of a Dash store; assertions must reach through `page.evaluate("window.dash_clientside...")`, which is brittle. But Playwright has excellent network introspection — it can intercept WebSocket frames, assert message contents, simulate slow connections, drop frames. Use it for assertions about *the wire protocol*.

The right split is: `dash_duo` tests assert "after sending these messages to the fake cascor server, the loss chart shows these data points" (store-state assertions). Playwright tests assert "clicking the start button issues a WebSocket frame with `{command: 'start'}`" (wire assertions).

### 8.3 Recommended verification stack

The Playwright / pytest-playwright approach is the right primary tool because:

1. **Self-contained**: `playwright install chromium` downloads a portable browser into the Python environment. No system Chrome required.
2. **Headless or headed**: defaults to headless, suitable for CI.
3. **Excellent network introspection**: Playwright can intercept WebSocket frames, assert message contents, simulate slow connections, drop frames, etc.
4. **Native Python integration**: `pytest-playwright` provides fixtures (`page`, `browser`, `context`) and asserts in idiomatic pytest style.
5. **Reliable selectors**: `page.get_by_test_id()`, `page.get_by_role()`, `page.get_by_label()` — no fragile XPath/CSS.
6. **Auto-waiting**: built-in retries with timeout — no flaky `time.sleep` calls.
7. **Trace viewer**: failures produce a full timeline with screenshots, network frames, and DOM snapshots — easy to debug remotely.

### 8.4 Test fixture architecture

```bash
canopy_e2e_tests/
├── conftest.py
│   ├── @pytest.fixture(scope="session") def fake_cascor_server()
│   │   # asyncio HTTP+WebSocket server that mimics cascor's /ws/training and /ws/control
│   │   # injectable: predefined message scripts, latency simulation, drop policy
│   ├── @pytest.fixture(scope="session") def canopy_app(fake_cascor_server)
│   │   # boots canopy uvicorn pointed at the fake cascor URL
│   ├── @pytest.fixture def browser_page(canopy_app, page)
│       # Playwright page fixture, navigated to canopy URL
├── test_metrics_panel_websocket.py
│   ├── test_browser_receives_metrics_event
│   ├── test_chart_updates_on_each_metrics_event
│   ├── test_chart_does_not_poll_when_websocket_connected
│   └── test_chart_falls_back_to_polling_on_websocket_disconnect
├── test_set_params_websocket.py
│   ├── test_learning_rate_change_uses_websocket_set_params
│   ├── test_learning_rate_change_falls_back_to_rest_on_disconnect
│   └── test_set_params_validation_error_displays_in_ui
├── test_training_control_websocket.py
│   ├── test_start_button_uses_websocket_command
│   ├── test_command_ack_updates_button_state
│   └── test_disconnect_restores_button_to_disabled
└── test_dashboard_smoke.py
    └── test_full_training_run_no_errors
```

### 8.5 The fake-cascor-server fixture

**Use the existing in-tree fake**, not a new aiohttp implementation.

`juniper-cascor-client/juniper_cascor_client/testing/fake_client.py` (992 lines) and `fake_ws_client.py` (222 lines) already define `FakeCascorClient`, `FakeCascorTrainingStream`, and `FakeCascorControlStream`. They support:

- `inject_message(msg)` — push a message into the simulated stream
- per-type callback registration matching the real `CascorTrainingStream` API (`on_metrics`, `on_state`, `on_topology`, `on_cascade_add`, `on_event`)
- scripted scenarios (`scenario="two_spiral_training"`)

These are already used by `juniper-canopy/src/tests/integration/test_param_apply_roundtrip.py:10-29` via `pytest.importorskip("juniper_cascor_client.testing")`.

#### What's missing from the existing fake (and what to add)

The existing fake is **in-process** — it injects messages programmatically into the SDK. Phase B's Playwright and `dash_duo` tests need a **real HTTP/WebSocket server** the browser can connect to. The right approach is to wrap the existing fake in a thin FastAPI/uvicorn harness that lives in `juniper-cascor-client[testing]`:

```python
# juniper_cascor_client/testing/server_harness.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

class FakeCascorServerHarness:
    """Wraps FakeCascorClient state in a real FastAPI server.

    Use FastAPI/uvicorn (NOT aiohttp) to match cascor's actual stack —
    this catches subtle behavior differences in header parsing,
    WebSocketDisconnect semantics, and X-API-Key validation.
    """

    def __init__(self, api_key: str = "test-key"):
        self.api_key = api_key
        self.received_commands: list[dict] = []
        self._app = FastAPI()
        self._app.websocket("/ws/training")(self._training_handler)
        self._app.websocket("/ws/control")(self._control_handler)
        self._scripted: list[dict] = []
        self._on_command_handlers: dict[str, callable] = {}

    async def _validate_auth(self, ws: WebSocket) -> bool:
        if ws.headers.get("X-API-Key") != self.api_key:
            await ws.close(code=4001, reason="Authentication failed")
            return False
        return True

    async def _training_handler(self, ws: WebSocket):
        await ws.accept()
        if not await self._validate_auth(ws):
            return
        try:
            for msg in self._scripted:
                await ws.send_json(msg)
                await asyncio.sleep(0.01)
            while True:
                await ws.receive_text()  # consume client pings
        except WebSocketDisconnect:
            pass

    async def _control_handler(self, ws: WebSocket):
        await ws.accept()
        if not await self._validate_auth(ws):
            return
        try:
            while True:
                msg = await ws.receive_json()
                self.received_commands.append(msg)
                command = msg.get("command")
                # Allow tests to script per-command responses
                if command in self._on_command_handlers:
                    await self._on_command_handlers[command](msg, ws)
                else:
                    await ws.send_json({
                        "type": "command_response",
                        "timestamp": time.time(),
                        "data": {"command": command, "status": "success", "result": {}}
                    })
        except WebSocketDisconnect:
            pass

    def script(self, *messages):
        self._scripted.extend(messages)

    def on_command(self, command_name: str, handler):
        """Register an interactive handler that runs when the named command arrives.

        handler signature: async def(msg: dict, ws: WebSocket) -> None
        """
        self._on_command_handlers[command_name] = handler

    def expect_command(self, command_name: str) -> dict:
        return next(c for c in self.received_commands if c.get("command") == command_name)
```

Three improvements over the original draft:

1. **FastAPI, not aiohttp** — matches cascor's actual stack so subtle behavior differences (headers, disconnect semantics) cannot mask bugs.
2. **Auth enforcement** — the fake validates `X-API-Key` and closes with 4001 on failure, so tests fail loud if the canopy adapter stops sending the header.
3. **`on_command` interactive handlers** — supports the "after the client sends `set_params`, emit a `state` event reflecting the change" pattern that the original sketch could not.

Tests use:

```python
@pytest.fixture(scope="session")
def fake_cascor_server():
    harness = FakeCascorServerHarness()
    server_thread = threading.Thread(target=lambda: uvicorn.run(harness._app, host="127.0.0.1", port=0), daemon=True)
    server_thread.start()
    # Wait for server to be ready, capture port
    yield harness
    # Daemon thread exits with the test process
```

### 8.5.1 CI runtime, marker split, and trace artifact policy

**Marker split**: define two pytest markers to separate fast unit/integration tests from slow Playwright end-to-end tests:

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "fast: unit and TestClient-based integration tests (<30s total)",
    "e2e: Playwright + dash_duo end-to-end tests (~3-5 min total)",
]
```

Run on every push: `pytest -m "fast or not e2e"`. Run on PR-to-main: `pytest -m e2e` as a separate job. Nightly: full suite.

**Realistic timing**:

- `playwright install --with-deps chromium` first run: ~60 s; cached: ~5 s
- Per Playwright test: ~8-15 s (canopy boot 3-5s + browser launch 1-2s + WebSocket handshake + scripted messages 1-2s + teardown)
- Verification matrix in §8.8 has ~16 e2e tests → **~2-4 min total** with `pytest -n auto` for parallelism

**Trace artifact policy**: Playwright traces with DOM/network/screenshots are 2-15 MB per test, 30-150 MB per failing run. GitHub Actions artifact storage is billed beyond 500 MB free tier. Configure:

```yaml
- name: Upload Playwright traces
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-traces
    path: test-results/
    retention-days: 14
```

Plus `--screenshot=only-on-failure --video=retain-on-failure` for cheaper fallback artifacts when traces are too large.

### 8.6 CI integration

```yaml
# .github/workflows/ci.yml — additional job
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test,e2e]"
      - run: playwright install --with-deps chromium
      - run: pytest tests/e2e/ -v --tracing=retain-on-failure
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-traces
          path: test-results/
```

The trace artifact is critical: it lets a remote developer (or LLM) inspect the exact timeline of a failure including network frames and DOM state, eliminating the "I can't see what the browser was doing" gap.

### 8.7 What this strategy DOES NOT cover

- **Visual regression** — pixel-level rendering correctness. Out of scope for this work; Plotly figures don't need pixel testing.
- **Real-cascor performance** — the fake server provides no real training; performance benchmarks need a separate harness with a real cascor instance.
- **Multi-browser compatibility** — Playwright defaults to Chromium. Firefox/WebKit support is one config flag away if/when needed.

### 8.8 Verification matrix (per remediation phase)

| Remediation phase                                     | Verification                                                                                            |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Phase A: SDK gap (GAP-WS-01)                          | Cascor unit tests + new SDK unit tests + cascor `/ws/control` integration test (GAP-WS-09)              |
| Phase B: Browser bridge (GAP-WS-02 through GAP-WS-05) | Playwright e2e: `test_browser_receives_metrics_event`, `test_chart_updates_on_each_metrics_event`       |
| Phase C: Set_params adapter wiring (GAP-WS-10)        | Canopy unit test for the adapter; Playwright e2e: `test_learning_rate_change_uses_websocket_set_params` |
| Phase D: Control button rewiring (GAP-WS-06)          | Playwright e2e: `test_start_button_uses_websocket_command`                                              |
| Phase E: Backpressure (GAP-WS-07)                     | Cascor unit test simulating a slow client; Playwright e2e for the dashboard's reconnection behavior     |

---

## 9. Phased Implementation Plan

Each phase has: scope, dependencies, risk, test plan, and estimated effort. **Effort is "engineering working days for one engineer with full context"**, not calendar time. Calendar time including PR review cycles, CI iteration, and integration is roughly 2.5-3× the engineering days.

### 9.1 Phase A — `juniper-cascor-client` adds WebSocket `set_params`

- **Scope**: GAP-WS-01
- **Touches**: `juniper-cascor-client/juniper_cascor_client/ws_client.py` + `tests/unit/test_ws_client.py`
- **Dependencies**: none
- **Risk**: very low (additive change to a Python SDK; cannot break existing callers; verified that `set_params` does not already exist on the class)
- **Test plan**:
  - `test_set_params_round_trip` — fake WebSocket server, send + receive ack
  - `test_set_params_timeout` — server never replies, raise `CascorTimeoutError`
  - `test_set_params_validation_error` — server replies with `status: "error"`, raise `CascorParamError`
  - `test_set_params_reconnection_queue` — verify behavior when client disconnects mid-send
  - `test_set_params_concurrent_correlation` — two `set_params` in flight, verify each `command_response` is delivered to the correct caller (requires per-command correlation IDs)
  - `test_set_params_caller_cancellation` — caller cancels the `await` before server replies; verify no resource leak
- **Effort**: 0.5 day
- **Deliverable**: a new release of `juniper-cascor-client` (semver minor bump). Document the addition under "Added" in the SDK CHANGELOG.

### 9.2 Phase B-pre — Security hardening (REQUIRED before Phase D)

- **Scope**: M-SEC-01, M-SEC-02, M-SEC-03 from §2.9
- **Touches**:
  - `juniper-canopy/src/main.py` — Origin allowlist on `/ws/training` and `/ws/control`
  - `juniper-canopy/src/main.py` — cookie-session auth + CSRF token validation on first WebSocket frame
  - `juniper-canopy/src/main.py` and `juniper-cascor/src/api/websocket/*.py` — explicit `max_size` on every `receive_*()` call
- **Dependencies**: none (security-only)
- **Risk**: medium — auth changes can lock out legitimate users; staging environment validation required
- **Test plan**:
  - Playwright: `test_csrf_required_for_control_commands`
  - Playwright: `test_origin_validation_rejects_third_party_pages`
  - Cascor unit: `test_oversized_frame_rejected_with_1009`
- **Effort**: 1 day
- **Deliverable**: canopy + cascor PRs. Must merge before Phase D ships.

### 9.3 Phase B — Browser WebSocket → Dash store bridge

- **Scope**: GAP-WS-02, GAP-WS-03, GAP-WS-04, GAP-WS-05, GAP-WS-13 (sequence numbers + replay), GAP-WS-14 (Plotly extendTraces), GAP-WS-15 (rAF coalescing), GAP-WS-16 (REST polling reduction), GAP-WS-24 (latency instrumentation), GAP-WS-25 (polling toggle), GAP-WS-26 (connection indicator), GAP-WS-33 (demo mode failure visibility)
- **Touches**:
  - `juniper-canopy/src/frontend/assets/websocket_client.js` — cleanup; ensure `onStatus` callback is exposed
  - `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` (new) — JS module that drains `window.cascorWS` events into Dash stores via the Interval drain pattern (Option B from §1.3)
  - `juniper-canopy/src/frontend/dashboard_manager.py` — delete the duplicate raw-WS clientside callback at line 1490; add the connection-status-aware polling toggle to `_update_metrics_store_handler` and similar callbacks; add the connection indicator badge component
  - `juniper-canopy/src/frontend/components/metrics_panel.py` (and other panels) — add `Input("ws-metrics-buffer", "data")` to chart callbacks via clientside that calls `Plotly.extendTraces()` instead of returning a full figure
  - `juniper-cascor/src/api/websocket/messages.py` — add `seq` field to envelope
  - `juniper-cascor/src/api/websocket/manager.py` — maintain replay buffer; handle `resume` request
- **Dependencies**: Phase B-pre (security must be in place); independent of Phase A
- **Risk**: **HIGH** — clientside_callback debugging is finicky; the merge logic between snapshot and live events needs care; the §1.3 architectural correction (Option B Interval drain) is the right pattern but requires careful Plotly extendTraces wiring
- **Test plan**:
  - `dash_duo`: `test_browser_receives_metrics_event` (asserts via `wait_for_text_to_equal` that the chart store updates after fake-server emits a metric)
  - `dash_duo`: `test_chart_updates_on_each_metrics_event`
  - `dash_duo`: `test_chart_does_not_poll_when_websocket_connected` — asserts `_update_metrics_store_handler` returns `no_update` when `ws-connection-status.connected` is True
  - `dash_duo`: `test_chart_falls_back_to_polling_on_websocket_disconnect`
  - `dash_duo`: `test_demo_mode_metrics_parity` — runs the dashboard in demo backend mode and asserts the same clientside store wiring works without a cascor backend (RISK-08)
  - Playwright: `test_websocket_frames_have_seq_field` (raw frame inspection)
  - Playwright: `test_resume_protocol_replays_missed_events`
  - Playwright: `test_connection_status_indicator_reflects_websocket_state`
  - Jest/Vitest unit: `cascorWS.on('metrics', handler)` fires; reconnect backoff schedule with jitter; URL construction with `wss://` under HTTPS; bounded ring buffer behavior
- **Effort**: **4 days** (raised from 2 — the architectural correction in §1.3 means redesigning the bridge before coding; the rAF coalescing + extendTraces work is non-trivial; Playwright + dash_duo fixture setup from scratch is ~1.5 days; reconnect/resume protocol coding + tests is ~1 day)
- **Deliverable**: canopy + cascor PRs with the wiring + Playwright/dash_duo test fixtures + initial test files

### 9.4 Phase C — Canopy `apply_params` switches to WebSocket for hot params

- **Priority**: **P2** (relabeled from P1 — see §5.3.1 ack-vs-effect-latency analysis. The `set_params` ack latency is invisible inside the much-larger effect-observation loop for actively-training networks. Phase C ships behind the feature flag below; the §5.6 instrumentation determines whether enabling actually improves UX before the default flips.)
- **Scope**: GAP-WS-10 + the canopy adapter refactor + GAP-WS-32 (per-command timeouts)
- **Touches**:
  - `juniper-canopy/src/backend/cascor_service_adapter.py` — `apply_params(params)` is **retained as a public delegating wrapper** that inspects each param against the hot/cold whitelist from §5 and dispatches to `_apply_params_hot()` (WebSocket) / `_apply_params_cold()` (REST). The split methods are private (`_` prefix). External callers see no signature change. **No deprecation needed.**
  - `juniper-canopy/src/frontend/dashboard_manager.py` — sliders for hot params use a clientside_callback that calls `window.cascorControlWS.send({command: "set_params", params: ...})` with per-command correlation IDs
- **Dependencies**: Phase A (SDK must expose `set_params` first); Phase B (browser bridge must be in place)
- **Risk**: **medium** — racing REST and WebSocket calls for the same param could cause confusion. The mitigation: hot/cold sets are disjoint AND `update_params()` uses keyed merges (not full replacement, verified at `lifecycle/manager.py:702-723`), so two successive calls with disjoint keys are safe under the shared `_training_lock`.
  - **Caveat**: per the §5.3.1 ack-vs-effect-latency analysis, Phase C may turn out to be unnecessary — the `set_params` ack latency is invisible inside the much-larger effect-observation loop. **Decision: ship Phase C behind a feature flag (`Settings.use_websocket_set_params=False` by default) and use the §5.6 instrumentation to verify whether enabling it actually improves user-perceived latency before flipping the default.**
- **Test plan**:
  - Canopy unit test for `cascor_service_adapter._apply_params_hot()` against `FakeCascorTrainingStream` (`AsyncMock` is sufficient for the call-site itself)
  - Canopy unit test for the routing in `apply_params()` — asserts hot params go to `_hot`, cold to `_cold`, mixed batches are split
  - `dash_duo`: `test_learning_rate_change_uses_websocket_set_params`
  - `dash_duo`: `test_learning_rate_change_falls_back_to_rest_on_disconnect`
  - **`dash_duo`: `test_orphaned_command_resolves_via_state_event`** (GAP-WS-32) — fake server delays `command_response` past the per-command timeout but emits a `state` event reflecting the change; assert the UI correctly transitions from "pending verification" to "applied"
  - **`dash_duo`: `test_per_command_timeout_values`** — verify `start: 10s`, `stop/pause/resume: 2s`, `set_params: 1s` are correctly enforced
- **Effort**: **2 days** (unchanged — the routing logic is contained, and the delegating wrapper preserves backwards compat)
- **Deliverable**: canopy PR with adapter refactor + dashboard wiring + tests + feature flag

### 9.5 Phase D — Training control buttons use WebSocket

- **Scope**: GAP-WS-06
- **Touches**:
  - `juniper-canopy/src/frontend/dashboard_manager.py` — replace the REST POST handler with a clientside_callback using `window.cascorControlWS.send()`; fall back to REST POST on disconnect. **The `/api/train/{command}` REST endpoint is explicitly preserved as a first-class supported API**, not merely a fallback. External consumers (curl scripts, CI jobs, monitoring probes) continue to work without modification. Document in canopy `docs/REFERENCE.md` under "Training control API."
- **Dependencies**: Phase B (browser bridge must be in place); Phase B-pre (security model must be in place because the WebSocket control path is the primary CSWSH attack surface)
- **Risk**: low — the REST POST handler stays as a documented public API
- **Test plan**:
  - Playwright: `test_start_button_uses_websocket_command`
  - Playwright: `test_command_ack_updates_button_state`
  - Playwright: `test_disconnect_restores_button_to_disabled`
  - Playwright: `test_csrf_required_for_websocket_start` (security regression)
- **Effort**: 1 day

### 9.6 Phase E — Cascor backpressure / slow client handling

- **Scope**: GAP-WS-07
- **Touches**: `juniper-cascor/src/api/websocket/manager.py`
- **Dependencies**: none (independent of canopy phases)
- **Risk**: medium — concurrency code; needs careful review
- **Test plan**:
  - Cascor unit test: simulate a slow client by holding a TCP-level read pause (using `asyncio.Queue(maxsize=0)` as the consumer); assert `broadcast()` does not block other clients
  - Cascor unit test: client whose per-client send queue is full; assert state-bearing events trigger `close(1008)` and progress events are dropped per policy
- **Effort**: 1 day
- **Deliverable**: cascor PR. **Quick fix** (per-send `asyncio.wait_for(send_json, timeout=0.5)`) can land independently as a hotfix before the full Phase E.
- **Migration path**: ship Phase E behind `Settings.ws_backpressure_policy ∈ {block, drop_oldest, close_slow}` with default `block` to preserve current behavior; flip the default only at the next major version.

### 9.7 Phase F — Heartbeat / ping-pong reciprocity + reconnect jitter

- **Scope**: GAP-WS-12, GAP-WS-30, GAP-WS-31
- **Touches**: `juniper-canopy/src/frontend/assets/websocket_client.js` (heartbeat + jitter + uncapped retries) + `juniper-canopy/src/main.py` (server-side `pong` handler) + cascor `messages.py` (already has `pong` builder)
- **Effort**: 0.5 day
- **Deliverable**: canopy + cascor (both ends need to support `ping`/`pong`)

### 9.8 Phase G — Cascor WS `set_params` integration test

- **Scope**: GAP-WS-09, GAP-WS-22 (protocol error responses)
- **Touches**: `juniper-cascor/src/tests/unit/api/test_websocket_control.py`
- **Dependencies**: none — **uses FastAPI's `TestClient.websocket_connect()` directly**, NOT the SDK. Cascor has no runtime dependency on `juniper-cascor-client` and tests should validate the wire protocol on the server side, not the SDK's interpretation of it. (The original draft incorrectly suggested using the SDK; this contradicts cascor's dependency graph.)
- **Test plan**:
  - `test_set_params_via_websocket_happy_path` — open `/ws/control`, send `set_params`, assert `command_response.data.result.learning_rate == 0.005` AND `lifecycle.network.learning_rate == 0.005`
  - `test_set_params_whitelist_filters_unknown_keys` — send `{evil_key: ...}`, assert it is silently filtered without raising
  - `test_set_params_init_output_weights_literal_validation` — send `{init_output_weights: "random; rm -rf /"}`, assert it is rejected by Pydantic Literal validator with `command_response.status: "error"`
  - `test_set_params_oversized_frame_rejected` — send a frame > 64 KB, assert close code 1009
  - `test_set_params_no_network_returns_error` — send before `create_network`, assert error response (per the existing handler logic at `lifecycle/manager.py:684-723`)
  - `test_unknown_command_returns_error` (GAP-WS-22) — assert structured error response, not silent ignore
  - `test_malformed_json_closes_with_1003` (GAP-WS-22) — assert close code
- **Effort**: 0.5 day

### 9.9 Phase H — Documentation / `_normalize_metric` audit

- **Scope**: GAP-WS-11 + §4.4 phased plan
- **Touches**: `juniper-canopy/src/tests/unit/test_response_normalization.py` (regression test) + a new `juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` document
- **Dependencies**: none
- **Test plan**:
  - **Add `test_normalize_metric_produces_dual_format` BEFORE the audit** — locks in the contract that `_normalize_metric` returns BOTH the flat AND the nested keys in a single dict; this is the regression gate for any future refactor (and the regression test that PR #141 lacked)
  - Audit deliverable: an enumerated list of every external consumer of the canopy `/api/metrics` REST endpoint (operators, scripts, exporters), with shape requirements for each
- **Effort**: 1 day audit + follow-up PRs as separate work
- **Deliverable**: regression test PR + audit document

### 9.10 Phase I — Frontend asset cache busting

- **Scope**: ensure browser clients pick up new JS without manual hard-refresh after Phase B ships
- **Touches**: `juniper-canopy/src/main.py` Dash app construction
- **Dependencies**: independent; can ship in the same PR as Phase B
- **Background**: Dash auto-loads `assets/*.js` files, but the default cache headers do NOT include cache-busting query strings. After Phase B ships, browsers with cached `assets/websocket_client.js` (v1.1) receiving a `seq`-bearing envelope (v1.2) may either (a) silently ignore the new fields (forward-compat by accident) or (b) crash if their JSON parser is strict. Either way the user must hard-refresh to get the new client.
- **Target state**: configure `assets_url_path` with a content-hash query string (`?v=<hash>`) per Dash's asset management documentation. Dash 2.x supports `assets_url_path` and Dash 3.x supports content-fingerprinting via `--assets-url-path` plus webpack-style hashing.
- **Test plan**: Playwright `test_asset_url_includes_version_query_string`
- **Effort**: 0.5 day

### 9.11 Total estimated effort

| Phase                      | Effort  | Cumulative |
|----------------------------|---------|------------|
| A (SDK set_params)         | 0.5 day | 0.5 day    |
| B-pre (security)           | 1 day   | 1.5 days   |
| B (browser bridge)         | 4 days  | 5.5 days   |
| C (set_params adapter)     | 2 days  | 7.5 days   |
| D (control buttons)        | 1 day   | 8.5 days   |
| E (backpressure)           | 1 day   | 9.5 days   |
| F (heartbeat + jitter)     | 0.5 day | 10 days    |
| G (cascor set_params test) | 0.5 day | 10.5 days  |
| H (normalize_metric audit) | 1 day   | 11.5 days  |
| I (asset cache busting)    | 0.5 day | 12 days    |

**Total: ~12 engineering working days** for the full WebSocket overhaul (raised from the original 8.5 estimate after the validation rounds surfaced the architectural caveat in §1.3, the security gap in §2.9, the rAF/extendTraces requirement in §5.5, and the asset cache-busting gap in §9.X). **Calendar time including PR review and CI iteration: ~4 weeks** across three repos.

The Phase 4 estimate of 9-14 days for "P5-RC-05 frontend WebSocket consumption" was the right ballpark for Phases B + D combined; the additional 6-7 days are for security (B-pre), the SDK gap (A), backpressure (E), and the set_params adapter (C).

### 9.12 Phase ordering rationale

The dependency chain forces:

1. **Phase A** (SDK) first, in parallel with Phase B-pre (security)
2. **Phase B-pre** before Phase B (security must precede the browser bridge so the new attack surface is not exposed)
3. **Phase B** before Phase C (browser bridge must exist before adapter can wire to it)
4. **Phase B** before Phase D (control buttons depend on browser bridge)
5. **Phases E, F, G, H** are independent of the critical path and can be picked up in any order

Critical-path: **A | B-pre → B → C | D**, with E/F/G/H as parallel work.

### 9.13 Release coordination

For CI/CD across three repos:

1. **Phase A PR** (`juniper-cascor-client`) merges to main, triggers a tagged GitHub release, OIDC publishes to PyPI.
2. **Wait** for PyPI index propagation (~2-5 minutes).
3. **Phase B-pre PR** (canopy + cascor security) merges independently — no SDK dep bump needed.
4. **Phase B PR** (canopy browser bridge + cascor sequence numbers) merges independently — no SDK dep bump needed.
5. **Phase C PR** (canopy adapter) rebases on latest main, bumps `juniper-cascor-client>=<new-version>` in `pyproject.toml` and `juniper-ml` extras, runs CI with the new SDK, merges.
6. **Phase D PR** rebases on Phase B and Phase B-pre.

Use squash-merge for each PR (not merge commits) for a linear history. Use GitHub's "merge queue" if available to serialize.

---

## 10. Risk Register

| ID      | Risk                                                                                                       | Severity | Likelihood                                                                                                         | Mitigation                                                                                                                                                                                                    |
|---------|------------------------------------------------------------------------------------------------------------|----------|--------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RISK-01 | The dual nested+flat metric format is removed too aggressively, breaking external consumers                | High     | Medium                                                                                                             | §4.4 phased plan; do NOT remove either format until external audit complete; lock-in regression test `test_normalize_metric_produces_dual_format` in Phase H                                                  |
| RISK-02 | Phase B's clientside_callback wiring is hard to debug remotely                                             | Medium   | High                                                                                                               | Playwright trace viewer + dash_duo store assertions + the verification matrix in §8.8; the §1.3 architectural correction (Option B Interval drain) is the foundation that prevents the most common debug-trap |
| RISK-03 | Phase C race condition: REST PATCH and WebSocket set_params for the same param land out of order           | Medium   | Low (hot and cold sets disjoint AND `update_params` uses keyed merges, verified at `lifecycle/manager.py:702-723`) | Per-param routing in `apply_params()` delegating wrapper; ship Phase C behind feature flag                                                                                                                    |
| RISK-04 | Cascor server's slow-client blocking (GAP-WS-07) manifests in normal dev workflows                         | Medium   | **Medium** (raised from Low — a hung dev-tools tab serially blocks all broadcasts)                                 | Phase E backpressure with quick-fix `wait_for(send_json, timeout=0.5)` available as a hotfix                                                                                                                  |
| RISK-05 | The Playwright fixture doesn't catch a regression that only manifests in real cascor (not the fake server) | Medium   | Medium                                                                                                             | Add a periodic smoke test against a real cascor instance, separate from the fast E2E suite                                                                                                                    |
| RISK-06 | Browser WebSocket reconnection storm after cascor restart                                                  | Low      | **Medium** (raised — current backoff has no jitter, causes synchronized reconnect waves)                           | Phase F adds full jitter to reconnect backoff (3-line change)                                                                                                                                                 |
| RISK-07 | The 50-connection cap in cascor WebSocketManager is hit by a multi-tenant deployment                       | Low      | Low                                                                                                                | Configurable via `Settings.ws_max_connections`; per-IP cap in M-SEC-04                                                                                                                                        |
| RISK-08 | Demo mode parity breaks when canopy migrates to WebSocket-driven UI                                        | Low      | Medium                                                                                                             | Demo mode uses the same `websocket_manager` module; **explicit `test_demo_mode_metrics_parity` test required in Phase B test plan** (added to §9.3)                                                           |
| RISK-09 | The canopy `set_params` integration changes user-perceived behavior in unexpected ways                     | Low      | Medium                                                                                                             | **Phase C ships behind `Settings.use_websocket_set_params=False` feature flag**; §5.6 instrumentation determines if enabling improves UX before flipping default                                              |
| RISK-10 | Browser-side memory exhaustion from unbounded chart data                                                   | Medium   | High (overnight runs accumulate millions of points)                                                                | GAP-WS-14 mandates `Plotly.extendTraces(maxPoints=5000)`; ring buffer in `ws-metrics-buffer` (last 1000 events); JS handler enforces buffer cap (not drain callback, which is throttled in background tabs)   |
| RISK-11 | Silent data loss via drop-oldest broadcast queue                                                           | High     | Low (only manifests under sustained slow-client load)                                                              | Phase E policy: **close slow client (1008) for state-bearing events**; drop-oldest only for coalesceable progress events with separate per-type queue                                                         |
| RISK-12 | Background tab memory spike when foregrounded                                                              | Low      | Medium                                                                                                             | JS-side ring buffer enforcement (not drain-callback enforcement); see GAP-WS-04 note about background tab throttling                                                                                          |
| RISK-13 | Orphaned commands after timeout (browser declares failure but server completes)                            | Medium   | Medium                                                                                                             | GAP-WS-32 per-command correlation IDs + `pending verification` state pending matching `command_response`/`state` event                                                                                        |
| RISK-14 | Cascor crash mid-broadcast leaves clients inconsistent                                                     | Low      | Low                                                                                                                | Resolved by GAP-WS-13 reconnect+replay protocol — `server_start_time` change forces all clients to do a full REST resync on reconnect                                                                         |
| RISK-15 | CSWSH attack exploits missing Origin validation on canopy `/ws/control`                                    | **High** | **Medium** (any web page the user visits during a canopy session)                                                  | M-SEC-01 + M-SEC-02 in §2.9; Phase B-pre is a hard prerequisite for Phase D                                                                                                                                   |
| RISK-16 | Topology message exceeds 64 KB silently for large networks                                                 | Medium   | **Medium** (any network with >50-100 hidden units)                                                                 | GAP-WS-18 chunking or REST fallback; document the threshold; add a server-side size guard                                                                                                                     |

---

## 11. Open Questions for Human Review

The original draft had 8 open questions; several have been resolved into recommendations during integration. Remaining genuinely-open questions:

1. **What is the target deployment topology?** Single canopy + single cascor + N browser dashboards is the assumed default. Multi-tenant cascor deployments would require revisiting GAP-WS-07 (backpressure) sooner. **Decision needed before Phase E.**

2. **Is there a hard requirement on browser compatibility?** Playwright defaults to Chromium; if Firefox or Safari support is required, additional Playwright fixtures and `BrowserType.firefox` / `BrowserType.webkit` configuration are needed. **Decision needed before Phase B test plan finalization.**

3. **Should `set_params` updates be journaled?** A historical record of parameter changes is useful for debugging and reproducing experiments. This is out of scope of this document but worth considering for a future change. **Defer until after Phase C.**

4. **Are there any in-flight refactors of `dashboard_manager.py` that would conflict with this work?** Coordinate timing with the release prep work referenced in `CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` §6.0. **Coordinate before Phase B kickoff.**

5. **Should cascor and canopy adopt a versioned subprotocol (`juniper-cascor.v1`)?** §11.2 of the protocol review (Reviewer 1) raised this. Adding `Sec-WebSocket-Protocol` would enable graceful version migration when the envelope changes (e.g., when GAP-WS-13 sequence numbers land). Currently there is no mechanism to reject an outdated client. **Defer; revisit if/when a v2 envelope is needed.**

6. **What is the right per-IP connection cap for the canopy deployment?** §2.9 M-SEC-04 proposes 5/IP. Validate against deployment patterns. **Decision needed before Phase B-pre.**

7. **Should the §5 latency thresholds be re-validated with user research before Phase C ships?** §5.7 proposes a 5-subject think-aloud study. This would convert engineering aspirations into user requirements but adds 1-2 weeks of calendar time. **Decision needed before Phase C scoping freeze.**

### 11.1 Resolved during integration (no longer open questions)

- ~~Q1: nested vs flat metric keys~~ → Resolved: do NOT remove either format; see §4.4 phased plan and the lock-in test in Phase H.
- ~~Q3: should canopy `/ws/training` be authenticated~~ → Resolved: yes; see §2.9 M-SEC-01/M-SEC-02. This is a P0 not an open question.
- ~~Q5: 1 Hz state throttle~~ → Resolved: replace with a debounced coalescer that bypasses throttle for terminal transitions. See GAP-WS-21.
- ~~Q7: `_juniper_ws_buffer` global usage~~ → Investigation closed: no other references found in `src/frontend/`. The drain callbacks at `dashboard_manager.py:1531-1564` are its only consumers, and Phase B deletes both. Tracked under GAP-WS-03.

---

## 12. References

### Internal documents

- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` — original Phase 1-4 roadmap
- `juniper-ml/notes/code-review/CANOPY_CASCOR_INTERFACE_ANALYSIS_2026-04-08.md` — interface analysis
- `juniper-ml/notes/FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md` — historical 20-issue registry (P5-RC-01 through P5-RC-18 + KL-1)
- `juniper-ml/notes/code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md` — cascor code review (CR-006 through CR-076)

### Pull requests referenced

- juniper-cascor PR #119 (Phase 1 test gaps + NEW-03/NEW-04/max_hidden_units, merged)
- juniper-cascor PR #120 (Phase 2 security hardening, merged)
- juniper-cascor PR #121 (epochs_max alignment, merged)
- juniper-cascor PR #122 (constants raise to 100B/1M/10K, open)
- juniper-canopy PR #137 (Phase 1-5 code review remediation, merged)
- juniper-canopy PR #138 (Phase 1 verification, merged)
- juniper-canopy PR #139 (Phase 3 demo backend, merged)
- juniper-canopy PR #140 (Phase 4 typed contract, merged)
- juniper-canopy PR #141 (NEW-01 nested format removal, **closed without merging**)
- juniper-canopy PR #142 (constants raise, open)
- juniper-ml PR #113 (Phase 3 docs, merged)
- juniper-ml PR #114 (Phase 4 docs, merged)
- juniper-ml PR #115 (Phase 1 deferred items doc resolution, merged)
- juniper-ml PR #116 (premature resolution claims revert, open)

### Source files (key file:line references)

- `juniper-cascor/src/api/websocket/manager.py` — `WebSocketManager` class (line 41), `connect()` (70), `disconnect()` (96), `broadcast()` (101), `broadcast_from_thread()` (112), `close_all()` (138)
- `juniper-cascor/src/api/websocket/control_stream.py` — `_VALID_COMMANDS` (22), max-size (23), `set_params` handler (97)
- `juniper-cascor/src/api/websocket/training_stream.py` — training stream handler
- `juniper-cascor/src/api/websocket/messages.py` — message builders (`metrics_message` 17, `state_message` 26, `topology_message` 35, `event_message` 44, `cascade_add_message` 53, `candidate_progress_message` 62, `command_response` 71)
- `juniper-cascor/src/api/lifecycle/manager.py` — `update_params()` whitelist (705-718), 1Hz state throttle (133-136), drain thread (309-344)
- `juniper-cascor/src/cascade_correlation/cascade_correlation.py` — output epoch callback throttle (~1646), persistent worker pool (3049-3081)
- `juniper-cascor/src/candidate_unit/candidate_unit.py:614-622` — candidate progress emission
- `juniper-cascor-client/juniper_cascor_client/ws_client.py` — `CascorTrainingStream` (18), `CascorControlStream` (149)
- `juniper-cascor-client/juniper_cascor_client/testing/fake_ws_client.py` — `FakeCascorTrainingStream` and `FakeCascorControlStream`
- `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py` — `FakeCascorClient`
- `juniper-canopy/src/backend/cascor_service_adapter.py` — `start_metrics_relay` (199), `apply_params` (450), `_normalize_metric` (516), `_to_dashboard_metric` (564)
- `juniper-canopy/src/backend/protocol.py` — `BackendProtocol` (118), `MetricsResult` (72)
- `juniper-canopy/src/communication/websocket_manager.py` — canopy `WebSocketManager`
- `juniper-canopy/src/main.py:355,417` — `/ws/training` and `/ws/control` route definitions
- `juniper-canopy/src/frontend/dashboard_manager.py` — `fast-update-interval` (1197), `ws-metrics-buffer` (1202), broken init callback (1490), drain callbacks (1531-1564), metrics REST handler (2388), training button handler (2522)
- `juniper-canopy/src/frontend/components/metrics_panel.py` — `MetricsPanel` chart callback (648-670)
- `juniper-canopy/src/frontend/assets/websocket_client.js` — `CascorWebSocket` class, `cascorWS` (219), `cascorControlWS` (223)

### External standards and tools

- RFC 6455 — The WebSocket Protocol (<https://www.rfc-editor.org/rfc/rfc6455>)
- RFC 7692 — Compression Extensions for WebSocket (`permessage-deflate`)
- Playwright Python documentation: <https://playwright.dev/python/>
- pytest-playwright: <https://playwright.dev/python/docs/test-runners>
- Dash testing (`dash[testing]`, `dash_duo`): <https://dash.plotly.com/testing>
- Dash `clientside_callback` documentation: <https://dash.plotly.com/clientside-callbacks>
- Dash `dcc.Store` documentation: <https://dash.plotly.com/dash-core-components/store>
- Dash `dash.set_props` (Dash 2.18+): <https://dash.plotly.com/advanced-callbacks>
- `dash-extensions` (third-party): <https://www.dash-extensions.com/>

### Latency perception research

- Miller, R. B. (1968). "Response time in man-computer conversational transactions." AFIPS '68 — original 100 ms / 1 s / 10 s thresholds
- Card, S. K., Robertson, G. G., & Mackinlay, J. D. (1991). "The Information Visualizer, an Information Workspace." CHI '91 — replication and refinement
- Nielsen Norman Group, "Response Times: The 3 Important Limits" (1993, updated 2014). <https://www.nngroup.com/articles/response-times-3-important-limits/>

### Validation history

This document was developed with rigorous subagent validation:

- **Round 1 (2026-04-10)**: 12 subagents in parallel, each reviewing from a distinct expertise angle:
  1. WebSocket protocol correctness (RFC 6455, envelope, framing)
  2. Plotly Dash frontend architecture (clientside_callback, dcc.Store, asset loading)
  3. Browser performance and perceived latency
  4. Data serialization and bandwidth
  5. Cascor backend instrumentation and concurrency
  6. Test coverage and verification approaches
  7. Security (auth, CSWSH, DoS, validation)
  8. Concurrency and threading (sync↔async bridge, locks, races)
  9. Latency tolerance UX
  10. Backwards compatibility
  11. Failure modes and resilience
  12. Documentation quality

- The round 1 findings drove substantive corrections including: the §1.3 architectural caveat (Dash clientside_callback subscribe pattern is impossible), the §2.9 security model section (CSWSH P0), the §5.3.1 ack-vs-effect-latency clarification, the §5.5 frame budget, the §6.4 disconnection taxonomy, the §6.5 reconnect+replay protocol, 21 additional GAP-WS entries (13-33), and the §9 phase reordering with new Phase B-pre.

- **Round 2 (2026-04-10)**: 10 focused subagents validated the round-1 integration.
  - Confirmed ~85% of round-1 issues were addressed;
  - surfaced ~18 additional P1/P2 issues including:
    - **duplicate §1.3** heading (renumbered to `§1.5`),
    - **§1.4 "18 enumerated gaps"** off-by-15 (corrected to 33),
    - **§5.1 table header** relabeled to "Target p50 (unvalidated)†",
    - **§6.2 framing inverted** from "wastes bandwidth" to "floor latency / event loss", `§6.3` `ws-connection-status` store population mechanism clarified (Option B drain), `§6.5.1`/`§6.5.2`/`§6.5.3` thread-safety + atomicity + edge cases added, M-SEC-04 per-IP map locking code sample added, M-SEC-01b cascor Origin parity, M-SEC-02 cookie attributes + CSRF rotation,
    - **§2.2 lock-type contract**, Phase G/H test plans,
    - **§9.10 Phase I** (asset cache busting),
    - **§7.34 deferred-items** rationale,
    - **§8.5.1 CI** runtime/marker split.
  - All 18 round-2 items integrated.

- **Round 3 (2026-04-10)**: 10 focused subagents validated the round-2 integration. Confirmed all 16 round-2 critical fixes landed; surfaced ~25 round-3 issues, of which ~10 were substantive and integrated:
  - **§6.5.4 fabricated "verified" Pydantic claim** (the SDK uses plain `json.loads`, not Pydantic — verified by reviewer 9 against `juniper-cascor-client/juniper_cascor_client/ws_client.py:73,181,210`)
  - **§6.5.3 wrong about "silent drop"** (older cascor responds with `command_response` error per `control_stream.py:55-59`; doc's own §3.2.4 also contradicted itself)
  - **§2.9.3 broken cross-ref** (`§9.X` → `§9.2`)
  - **§6.5 clock skew on `server_start_time`** — switched to `server_instance_id` UUID for cascor restart detection
  - **§6.5.1 lock-widening contention** — documented two implementation options (reuse `_lock` only after Phase E, OR add `_seq_lock`); recommended Option 2
  - **§6.5.2 snapshot atomicity** — clarified that snapshot endpoint MUST read state + `snapshot_seq` atomically under the lock; added idempotent replay contract; added snapshot fetch retry policy
  - **§9.10 Phase I numbering** (was Roman `§9.X`, renumbered to `§9.10` with §9.11/9.12/9.13 cascade)
  - **Plotly.react vs extendTraces** for snapshot replacement (vs live updates) clarified in §6.5.2
  - Status header updated from "v1.1 pending round-2" to "v1.3 STABLE"

  - Round-3 issues NOT integrated (judged out of scope or already adequately covered):
    - Subdomain bypass / CSP header (M-SEC-08): security hardening beyond CSWSH; deferred to a follow-up security pass
    - Constant-time API key comparison (M-SEC-09): valid concern but a cascor-side hardening separable from this analysis
    - Performance / load test plan (50 concurrent dashboards × 50 Hz): out of scope for analysis document; tracked as future Phase J
    - Per-message wire-size column in §3.1: nice-to-have, not load-bearing
    - TLS overhead acknowledgment in §6.2: minor

- **Document declared STABLE** after round 3 (~25 lines added/changed in round 3 vs ~140 in round 2 vs ~685 in round 1 — convergence achieved).
Round 4 not run; remaining nitpicks would add cosmetic value but no substantive design changes.
