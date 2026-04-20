# Phase B Implementation Plan — P0 Win (Polling Elimination)

**Status**: READY FOR IMPLEMENTATION
**Date**: 2026-04-12
**Author**: Claude Code (Opus 4.6, 1M context) on behalf of Paul Calnon
**Canonical Plan Reference**: R5-01 §S7
**Prerequisites**: P1 (Phase 0-cascor), P2 (Phase A-SDK), P3+P4 (Phase B-pre-a) — ALL MERGED

---

## Context

Phase B eliminates ~3 MB/s REST polling by wiring the browser to drain `/ws/training` into Dash stores. Ships behind two flags: `enable_browser_ws_bridge` (dev flip) + `disable_ws_bridge` (permanent kill switch). P1-P4 are merged. Per canonical plan §S7.

Three PRs: P5 (cascor, small), P6 (canopy, large), P7 (one-line flag flip).

---

## PR P5: `phase-b-cascor-audit-prom-counters` (juniper-cascor)

Small PR — wire the Phase B-pre-a security metrics into actual code paths and add the audit event Prometheus counter hookup.

**Skipping for now** — the security metrics from B-pre-a are already defined in observability.py. The actual counter increments will be added when the code paths are exercised. P5 is not blocking P6. Moving directly to P6.

---

## PR P6: `phase-b-canopy-drain-wiring` (juniper-canopy) — THE P0 WIN

### Worktree

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git fetch origin && git checkout main && git pull origin main
BRANCH="phase-b-canopy-drain-wiring"
git branch "$BRANCH" main
WT="/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--feat--${BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WT" "$BRANCH"
```

### Implementation (ordered by dependency)

#### 1. Settings — two-flag design + 4 new fields

**File:** `src/settings.py`

Add to `Settings` class:

```python
enable_browser_ws_bridge: bool = False   # D-17: dev flip (off by default)
disable_ws_bridge: bool = False          # D-18: permanent kill switch
enable_raf_coalescer: bool = False       # D-04: scaffolded disabled
enable_ws_latency_beacon: bool = True    # Latency beacon enabled
```

Runtime check: `ws_enabled = settings.enable_browser_ws_bridge and not settings.disable_ws_bridge`

#### 2. `websocket_client.js` — seq tracking, resume, jitter improvement

**File:** `src/frontend/assets/websocket_client.js` (existing, ~7KB)

Modify the existing `CascorWebSocket` class:

- **Jitter backoff** (GAP-WS-30): `delay = Math.random() * Math.min(30000, 500 * Math.pow(2, attempt))`
- **Remove 10-attempt cap** (GAP-WS-31): retry forever, max 30s
- **Capture `server_instance_id`** from `connection_established` message
- **`seq` tracking**: Store `_lastSeq`, WARN on gap (console.warn), increment tracking
- **Resume on reconnect**: Send `{type: "resume", data: {last_seq, server_instance_id}}` on reconnect; fallback to REST on `resume_failed`
- **Expose connection status**: `this.connected`, `this.reconnecting` flags

#### 3. `ws_dash_bridge.js` — NEW (~200 LOC)

**File:** `src/frontend/assets/ws_dash_bridge.js` (new)

Bridge between `window.cascorWS` and Dash clientside callbacks:

```javascript
window._juniperWsDrain = {
    // Bounded ring buffers (ring bound enforced IN the handler per C-19)
    _metricsBuffer: [],     // max 1000
    _stateBuffer: null,     // latest only (single object)
    _topologyBuffer: null,  // latest only
    _cascadeAddBuffer: [],  // max 500
    _candidateProgressBuffer: [], // max 500
    _connectionStatus: {connected: false, reconnecting: false, mode: "live"},
    _gen: 0,  // drain generation counter

    // Drain methods (called by Dash clientside callbacks)
    drainMetrics() { ... },    // returns + clears _metricsBuffer
    drainState() { ... },      // returns + clears _stateBuffer
    drainTopology() { ... },
    drainCascadeAdd() { ... },
    drainCandidateProgress() { ... },
    peekConnectionStatus() { ... }, // peek, not drain (emit on change)
};
```

Register handlers on `window.cascorWS`:

```javascript
window.cascorWS.on("metrics", function(msg) {
    if (window._juniperWsDrain._metricsBuffer.length >= 1000) {
        window._juniperWsDrain._metricsBuffer.shift(); // drop oldest
    }
    window._juniperWsDrain._metricsBuffer.push(msg.data);
});
// Similar for state, topology, cascade_add, candidate_progress
```

rAF scaffold: `_scheduleRaf = function() {}` (noop per D-04).

#### 4. `dashboard_manager.py` — stores + drain callbacks + polling toggle

**File:** `src/frontend/dashboard_manager.py` (the largest change)

**a) Add new dcc.Stores** (in layout section):

- `dcc.Store(id='ws-metrics-buffer')` — structured `{events: [], gen: int, last_drain_ms: float}`
- `dcc.Store(id='ws-cascade-add-buffer')`
- `dcc.Store(id='ws-candidate-progress-buffer')`
- `dcc.Store(id='ws-connection-status')` — `{connected: bool, reconnecting: bool, mode: str}`
- Keep existing `ws-topology-buffer`, `ws-state-buffer`

**b) Replace lines 1490-1527** (old raw-WS clientside callback):
Remove the old `window._juniper_ws` global creation. Replace with a comment noting the bridge is now in `ws_dash_bridge.js`.

**c) Replace lines 1532-1565** (old drain callbacks):
Replace with new drain callbacks that read from `window._juniperWsDrain`:

```python
app.clientside_callback(
    """function(n) {
        if (!window._juniperWsDrain) return window.dash_clientside.no_update;
        var events = window._juniperWsDrain.drainMetrics();
        if (!events || events.length === 0) return window.dash_clientside.no_update;
        window._juniperWsDrain._gen++;
        return {events: events, gen: window._juniperWsDrain._gen, last_drain_ms: Date.now()};
    }""",
    Output("ws-metrics-buffer", "data"),
    Input("fast-update-interval", "n_intervals"),
)
```

Similar for topology, state, cascade_add, candidate_progress.

**d) Modify `_update_metrics_store_handler`** (lines 2388-2422):
Add polling toggle: when `ws-connection-status.connected === true`, return `no_update` (skip REST poll). Keep REST path for:

- Initial page load (first call always fetches)
- Fallback to 1 Hz when WS disconnected (D-05): `if n % 10 != 0: return no_update`

**e) Apply polling-toggle to other handlers:**

- `_handle_training_state_poll` — return no_update when ws-state-buffer has data
- `_handle_candidate_progress_poll` — similar
- `_handle_topology_poll` — similar
- **Keep all REST paths** (D-54)

#### 5. Backend endpoints

**File:** `src/main.py`

Add:

- `POST /api/ws_latency` — accepts latency submissions, feeds Prometheus histogram
- `POST /api/ws_browser_errors` — accepts error reports, feeds counter

These are simple POST endpoints that just increment metrics.

#### 6. Connection indicator

**File:** `src/frontend/components/connection_indicator.py` (new, small)

4-state badge component: connected-green, reconnecting-yellow, offline-red, demo-gray.
Wire into the dashboard layout, update via `ws-connection-status` store.

#### 7. Demo mode parity (RISK-08)

**File:** `src/frontend/dashboard_manager.py`

In demo mode, set `ws-connection-status = {connected: true, mode: "demo"}` so the polling toggle doesn't try to use WS (which doesn't exist in demo mode).

### Tests (focused on P0 gates)

**Python unit** (new file: `src/tests/unit/test_phase_b_bridge.py`):

- `test_both_flags_interact_correctly` — ws_enabled logic
- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_ws_metrics_buffer_store_is_structured_object`

### Verification

1. All existing tests green
2. New tests green
3. With `enable_browser_ws_bridge=False` (default): behavior unchanged, all REST polling continues
4. PR: `feat(ws): browser drain wiring, polling toggle, two-flag design` → main

### Critical files

1. `src/settings.py` — two-flag settings
2. `src/frontend/assets/websocket_client.js` — seq, resume, jitter
3. `src/frontend/assets/ws_dash_bridge.js` — new bridge
4. `src/frontend/dashboard_manager.py` — stores, drains, polling toggle
5. `src/main.py` — backend endpoints
6. `src/tests/unit/test_phase_b_bridge.py` — new tests

---

## PR P7: `phase-b-canopy-flag-flip` (one-line PR)

After P6 is merged and staging soak passes:

- Change `enable_browser_ws_bridge: bool = True` in settings.py
- Requires project-lead review
- Mid-week deploy only (D-61)

---

## Architectural decisions (settled, from §S2)

- Two flags: `enable_browser_ws_bridge` + `disable_ws_bridge` (D-17+D-18)
- REST endpoints preserved FOREVER (D-21/D-54/D-56)
- Ring-bound enforced IN the handler, not drain callback (C-19)
- `ws-metrics-buffer` store shape = `{events, gen, last_drain_ms}` (D-07)
- REST fallback cadence = 1 Hz during disconnect (D-05)
- rAF coalescer scaffolded but DISABLED (D-04)
- Debounce lives in Dash clientside callback, 250ms (C-29)

## Key existing code references

- `websocket_client.js`: `CascorWebSocket` class at `/src/frontend/assets/websocket_client.js`
- Old WS globals: `window._juniper_ws`, `window._juniper_ws_buffer`, `window._juniper_ws_topology`, `window._juniper_ws_state` (lines 1490-1527 of dashboard_manager.py)
- Old drain callbacks: lines 1532-1565 of dashboard_manager.py
- Metrics store handler: lines 2388-2422 of dashboard_manager.py
- Status indicator: lines 398-420 of dashboard_manager.py
- Metrics panel chart rendering: lines 648-670 of metrics_panel.py
