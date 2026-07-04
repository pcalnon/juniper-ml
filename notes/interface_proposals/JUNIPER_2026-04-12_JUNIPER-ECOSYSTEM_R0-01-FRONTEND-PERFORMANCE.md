# Round 0 Proposal R0-01: Frontend / Browser Performance

**Specialization**: Browser-side performance, Dash clientside, Plotly.js
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope

This proposal covers the browser-side data path and render loop only. It focuses on completing the Phase A / Phase B frontend work enumerated in the architecture doc: wiring `ws-metrics-buffer` the way `ws-topology-buffer` and `ws-state-buffer` are already wired (Option B Interval drain, per §1.3), migrating Plotly rendering from full-figure replace to `Plotly.extendTraces()` with `maxPoints` (GAP-WS-14), adding requestAnimationFrame coalescing to absorb the 10-50 Hz burst rate of `candidate_progress` events (GAP-WS-15), eliminating the ~3 MB/s `/api/metrics/history` polling waste via the connection-status-aware polling toggle (GAP-WS-16 / GAP-WS-25), removing the dead second JS WebSocket client at `dashboard_manager.py:1490-1526` (GAP-WS-03), integrating the existing but unused `window.cascorWS` from `assets/websocket_client.js` (GAP-WS-02), wiring the connection indicator badge (GAP-WS-26), adding demo-mode failure visibility (GAP-WS-33), and validating the resulting path with `dash_duo` + Playwright tests per §8. Security (Phase B-pre, CSWSH, Origin validation), cascor server-side broadcaster / replay buffer, and SDK `set_params` are explicitly out of scope for this proposal and are covered by parallel sub-agents.

---

## 2. Source-doc cross-references

This proposal addresses the following enumerated items from the architecture doc:

**Phase assignments**:
- Phase B (browser WebSocket → Dash store bridge) — primary phase for this proposal
- Phase I (frontend asset cache busting) — tangentially addressed via the client-version-pinning recommendation
- Phase B-pre is acknowledged as a hard precondition but NOT owned by this proposal (security agent)

**GAP-WS identifiers addressed**:
- **GAP-WS-02** (P1) — `assets/websocket_client.js` `window.cascorWS` / `window.cascorControlWS` are dead code. Decision: integrate, do not delete.
- **GAP-WS-03** (P2) — parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490-1526`. Delete it in favor of `window.cascorWS`.
- **GAP-WS-04** (P1) — `ws-metrics-buffer` `dcc.Store` never populated (init callback returns `no_update`).
- **GAP-WS-05** (P1) — no clientside callback drains `ws-*-buffer` stores into chart inputs.
- **GAP-WS-14** (P1) — chart updates must use `Plotly.extendTraces()` with `maxPoints`, not figure replacement.
- **GAP-WS-15** (P1) — browser-side `requestAnimationFrame` coalescing for high-frequency events.
- **GAP-WS-16** (P0) — `/api/metrics/history` polling at 100 ms × ~300 KB/response ≈ 3 MB/s waste per dashboard.
- **GAP-WS-24** (P2) — production WebSocket latency instrumentation (browser-side histogram module; the `/api/ws_latency` backend is server-agent territory, but the browser emitter lives here).
- **GAP-WS-25** (P1) — WebSocket-health-aware polling toggle.
- **GAP-WS-26** (P1) — visible connection status indicator wired to `window.cascorWS.onStatus()`.
- **GAP-WS-30** (P3) — reconnect backoff jitter (cosmetic; ships with the JS refactor).
- **GAP-WS-31** (P2) — unbounded reconnect attempts (currently capped at 10).
- **GAP-WS-33** (P2) — demo mode failure visibility.

**Risks (§10)**:
- **RISK-02** — Phase B clientside_callback wiring is hard to debug remotely. Mitigation: Option B drain pattern + Playwright traces + `dash_duo` store assertions.
- **RISK-08** — demo mode parity breaks when canopy migrates to WebSocket-driven UI. Mitigation: `test_demo_mode_metrics_parity`.
- **RISK-10** — browser-side memory exhaustion from unbounded chart data. Mitigation: `Plotly.extendTraces(maxPoints=5000)` + `ws-metrics-buffer` bounded ring (last 1000 events).
- **RISK-12** — background tab memory spike when foregrounded. Mitigation: JS-side ring buffer bounding in the event handler (not in the drain callback, which is throttled when the tab is backgrounded).

**Caveats (§1.3, §5.3.1, §5.5)**:
- §1.3 — Dash clientside_callbacks are pure functions triggered by declared `Input`s; they cannot "subscribe" to JS events. **Option B (Interval drain)** is the recommended primary path. This proposal adopts Option B exclusively.
- §5.3.1 — control feedback latency (<16 ms) is already met by the local DOM; the ack-latency budget only applies to the set_params dispatch; effect observation is dominated by training step time. My recommendations optimize the dcc.Interval-driven batching, not the unachievable parts.
- §5.5 — 60 fps = 16.67 ms/frame budget. Full figure replace at 10k points = 80-200 ms. This is the single strongest reason for `extendTraces` + rAF coalescing.

---

## 3. Recommended approach

### 3.1 Phase A prerequisites

Phase A (SDK `set_params`) is owned by the SDK agent, not this proposal. However, Phase B depends on Phase A being merged and released to PyPI before the canopy adapter can switch. For the browser-side work in this proposal, Phase A is a non-blocker: the browser never imports `juniper-cascor-client`. The browser talks to canopy, and canopy talks to cascor. Phase B can proceed in parallel with Phase A — the only place they intersect is the eventual adapter refactor in Phase C, which is also owned by a different agent.

What this proposal DOES depend on being available before Phase B ships:
1. **Phase B-pre security (M-SEC-01, M-SEC-02, M-SEC-03)** — the browser cannot connect without the Origin allowlist, cookie-session auth, and CSRF-in-first-frame being implemented on canopy `/ws/training` and `/ws/control`. The security agent owns this. If Phase B-pre slips, Phase B can still implement and land the JS + Python wiring behind a feature flag (`Settings.enable_browser_ws=False` by default), but the Playwright tests that need a real WebSocket handshake must skip until Phase B-pre lands.
2. **Cascor `seq` field in envelope (GAP-WS-13)** — for lossless reconnect. The browser reconnect handler in `ws_dash_bridge.js` must know whether the server advertises `seq`; if not, it gracefully falls back to full snapshot refresh on reconnect (§6.5.2 pattern). The cascor server agent owns the `seq` implementation. The browser code should degrade gracefully when `seq` is absent.
3. **Canopy `/ws/training` relay already working** — it is. Per §2.5-§2.6 the canopy adapter's `start_metrics_relay()` and the canopy server's `/ws/training` endpoint both exist and broadcast correctly. The only reason this data is not on the dashboard is that the browser side dead-ends in JS globals — which is exactly what this proposal fixes.

### 3.2 Phase B Interval drain wiring (the canonical Option B pattern)

**The Option B pattern codified, with file-level structure.** The architecture doc's §1.3 says: "JS handler appends to `window._buffer`; a `clientside_callback` fires on `dcc.Interval.n_intervals` (e.g., 250 ms) and drains the buffer into the store." That is the pattern for every inbound event type. This section specifies how to make that pattern consistent and debuggable across metrics, topology, state, and candidate_progress.

#### 3.2.1 File-level structure

Create one new JS asset file:

```
juniper-canopy/src/frontend/assets/ws_dash_bridge.js   (new, ~200 lines)
```

Keep the existing `assets/websocket_client.js` but clean it up in-place (see §3.5).

The new `ws_dash_bridge.js`:

- Depends on `window.cascorWS` being defined (load order: Dash loads `assets/` files alphabetically by default, so a file named `ws_dash_bridge.js` loads AFTER `websocket_client.js`. Confirm the ordering by adding a guard at the top of the bridge file: `if (!window.cascorWS) { console.error('[ws_dash_bridge] websocket_client.js must load first'); return; }`).
- Registers exactly five `on(type, ...)` handlers on `window.cascorWS` and one `onStatus(...)` handler.
- Each handler pushes to a typed JS-side ring buffer with a hard upper bound (see §3.2.5 — the ring is enforced in the handler, NOT in the drain callback, because background tab throttling can delay the drain).
- Exposes exactly ONE new JS global (`window._juniperWsDrain`) that provides the drain helpers and a `_introspect` helper for tests. All other state lives in a module-scope closure to avoid namespace pollution. The single drain namespace is deliberate — it replaces the three legacy `window._juniper_ws_*` globals with one discoverable surface.

The module-scope closure also exposes the drain / introspection helpers for tests and the Python-side clientside_callbacks:

```javascript
// ws_dash_bridge.js (skeleton)
(function() {
  if (!window.cascorWS) {
    console.error('[ws_dash_bridge] websocket_client.js must load first');
    return;
  }

  // JS-side ring buffers. Bounded in the append path, drained by dcc.Interval.
  const _buffers = {
    metrics: [],            // bounded to MAX_METRICS_BUFFER
    topology: null,         // last-wins (single snapshot, not a ring)
    state: null,             // last-wins
    cascade_add: [],        // bounded to MAX_EVENT_BUFFER
    candidate_progress: [], // bounded to MAX_EVENT_BUFFER
  };
  const MAX_METRICS_BUFFER = 1000;  // matches the ws-metrics-buffer store cap
  const MAX_EVENT_BUFFER = 500;

  // Monotonic drain gen used to validate that drain callbacks are not stale
  let _drainGen = 0;

  // rAF scheduling for chart renders (see §3.3).
  let _rafHandle = null;
  const _rafQueue = { metrics: [], candidate_progress: [] };

  // Event handlers
  window.cascorWS.on('metrics', function(msg) {
    const data = msg && msg.data;
    if (!data) return;
    _buffers.metrics.push(data);
    if (_buffers.metrics.length > MAX_METRICS_BUFFER) {
      // drop oldest — this is the memory cap; background tabs don't lose data
      // because the cap is on the buffer, not the drain rate.
      _buffers.metrics.splice(0, _buffers.metrics.length - MAX_METRICS_BUFFER);
    }
    _scheduleRaf('metrics', data);  // feeds the extendTraces path
  });

  window.cascorWS.on('state', function(msg) {
    if (msg && msg.data) _buffers.state = msg.data;
  });

  window.cascorWS.on('topology', function(msg) {
    if (msg && msg.data) _buffers.topology = msg.data;
  });

  window.cascorWS.on('cascade_add', function(msg) {
    const data = msg && msg.data;
    if (!data) return;
    _buffers.cascade_add.push(data);
    if (_buffers.cascade_add.length > MAX_EVENT_BUFFER) {
      _buffers.cascade_add.splice(0, _buffers.cascade_add.length - MAX_EVENT_BUFFER);
    }
  });

  window.cascorWS.on('candidate_progress', function(msg) {
    const data = msg && msg.data;
    if (!data) return;
    _buffers.candidate_progress.push(data);
    if (_buffers.candidate_progress.length > MAX_EVENT_BUFFER) {
      _buffers.candidate_progress.splice(0, _buffers.candidate_progress.length - MAX_EVENT_BUFFER);
    }
    _scheduleRaf('candidate_progress', data);
  });

  // Status handler for connection indicator (GAP-WS-26) and polling toggle (GAP-WS-25)
  window.cascorWS.onStatus(function(status) {
    // Published via set_props in the status drain callback below
    _buffers._status = status;
  });

  // Expose drain functions (called by clientside callbacks)
  window._juniperWsDrain = {
    drainMetrics: function() {
      const out = _buffers.metrics;
      _buffers.metrics = [];
      _drainGen += 1;
      return {events: out, gen: _drainGen};
    },
    drainState: function() {
      const out = _buffers.state;
      _buffers.state = null;
      return out;
    },
    drainTopology: function() {
      const out = _buffers.topology;
      _buffers.topology = null;
      return out;
    },
    drainCascadeAdd: function() {
      const out = _buffers.cascade_add;
      _buffers.cascade_add = [];
      return out;
    },
    drainCandidateProgress: function() {
      const out = _buffers.candidate_progress;
      _buffers.candidate_progress = [];
      return out;
    },
    peekStatus: function() {
      return _buffers._status || null;
    },
    _introspect: function() {
      return {
        metricsSize: _buffers.metrics.length,
        topology: _buffers.topology,
        state: _buffers.state,
        cascadeAddSize: _buffers.cascade_add.length,
        candidateProgressSize: _buffers.candidate_progress.length,
      };
    },
  };

  // rAF scheduler (see §3.3)
  function _scheduleRaf(type, data) { /* ... */ }
})();
```

The `_introspect` helper is what `dash_duo` tests use via `page.evaluate("window._juniperWsDrain._introspect()")` to assert the buffer state without touching the Dash store graph. It is explicitly namespaced with `_introspect` so an accidental production use stands out in code review.

#### 3.2.2 Python-side: drain callbacks in `dashboard_manager.py`

The existing drain callbacks for `ws-topology-buffer` and `ws-state-buffer` at `dashboard_manager.py:1531-1564` already use the dcc.Interval drain pattern. Phase B adds a matching drain callback for `ws-metrics-buffer` and wires each drain to call into `window._juniperWsDrain` instead of reading `window._juniper_ws_*` globals directly.

**Delete** (GAP-WS-03): `dashboard_manager.py:1490-1526` — the parallel raw-WebSocket clientside callback. Replace with a placeholder comment referencing this proposal so future readers understand the history.

**Rewrite** (GAP-WS-04): the `ws-metrics-buffer` init callback is replaced with the drain callback below. The old callback's `Output("ws-metrics-buffer", "data")` is preserved; the new callback is the only writer.

**Rewrite** (GAP-WS-05): the topology and state drain callbacks are updated to call `window._juniperWsDrain.drainTopology()` / `drainState()` instead of reading `window._juniper_ws_topology` / `window._juniper_ws_state`. This unifies the contract.

Concrete callback registrations (pseudo-Python inside `dashboard_manager.py` where it builds clientside callbacks):

```python
# Replaces dashboard_manager.py:1490-1526 (the dead init callback)
# Drains metrics from the JS-side ring into the ws-metrics-buffer store.
# Fires on fast-update-interval (100 ms) matching the existing drain cadence.
clientside_callback(
    """
    function(n_intervals, current_data) {
        if (!window._juniperWsDrain) {
            return window.dash_clientside.no_update;
        }
        const drain = window._juniperWsDrain.drainMetrics();
        if (!drain.events.length) {
            return window.dash_clientside.no_update;
        }
        const existing = (current_data && current_data.events) || [];
        const merged = existing.concat(drain.events);
        // Cap at 1000 to match the JS-side ring buffer
        const capped = merged.length > 1000 ? merged.slice(-1000) : merged;
        return {events: capped, gen: drain.gen, last_drain_ms: performance.now()};
    }
    """,
    Output("ws-metrics-buffer", "data"),
    Input("fast-update-interval", "n_intervals"),
    State("ws-metrics-buffer", "data"),
    prevent_initial_call=False,
)
```

Notes on this callback:

1. **Read-append-write pattern, not replace**: the drain appends to the existing store data. This means the store becomes a bounded event log, not a snapshot. Consumers read `data.events` and treat it as a live feed with a `gen` counter for change detection.
2. **`no_update` when empty**: Dash's `no_update` sentinel skips the store write entirely, which avoids a useless server-side diff and keeps downstream callbacks from firing. This is the key optimization for idle dashboards.
3. **Cap at 1000**: matches the JS-side ring buffer. The JS ring is the primary line of defense (enforced on every push, works even when the tab is backgrounded); the Python-side cap is a belt-and-suspenders second line of defense.
4. **`last_drain_ms` diagnostic**: useful in the latency instrumentation module (GAP-WS-24) to measure drain-to-render latency.
5. **`prevent_initial_call=False`**: ensures the drain runs on page load so any early metrics are not lost.

Analogous drain callbacks for `ws-topology-buffer`, `ws-state-buffer`, `ws-cascade-add-buffer`, and `ws-candidate-progress-buffer` follow the same pattern (most are simpler because topology/state are last-wins, not event logs).

#### 3.2.3 Why Option B and not Option A (`dash.set_props`)

The architecture doc's §1.3 lists three options. Option A (`dash.set_props()`, Dash 2.18+) is more idiomatic — the JS handler can call `window.dash_clientside.set_props("ws-metrics-buffer", {data: newBuffer})` directly from inside the `on('metrics', ...)` callback. Per-event writes from an inline callback bypass the Output system entirely.

This proposal nevertheless recommends Option B as the primary path, matching the architecture doc's recommendation. Reasons:

1. **Event coalescing**: Option A writes one store mutation per WebSocket event. At 50 Hz `candidate_progress` burst rate, that is 50 callback storms per second. Option B coalesces into one store write per `fast-update-interval` tick. **This is the correct trade-off for render performance**, even though Option A is newer and prettier.
2. **Existing precedent**: `ws-topology-buffer` and `ws-state-buffer` already use drain callbacks (just broken). Matching the existing pattern keeps the mental model consistent and reduces code-review surface.
3. **Dash-version floor**: Option A requires Dash 2.18+. Confirming the canopy repo's Dash version and bumping if necessary is additional work that Option B avoids. Check `juniper-canopy/pyproject.toml` for the current Dash version before assuming; Option B has no such floor.
4. **`dash_duo` testability**: `dash_duo` understands store mutations natively. A drain callback that writes to `ws-metrics-buffer.data` is straightforward to assert via `dash_duo.wait_for_element_by_id('ws-metrics-buffer')` followed by JS evaluation. Option A store mutations happen outside the callback graph and need different test assertions.

**When to reconsider Option A**: if, in Phase C or beyond, the 100 ms drain latency on `fast-update-interval` becomes a user-observable bottleneck. Per §5.3.1 this is unlikely — the effect observation loop is dominated by training step time (100 ms - 10 s), which dwarfs the 100 ms drain. This proposal does not recommend revisiting Option A unless §5.6 instrumentation shows a specific bottleneck.

#### 3.2.4 Why Option C (`dash-extensions.WebSocket`) is the runner-up

Option C uses a third-party Dash component that exposes a `message` prop as a legitimate callback Input. It would replace the entire `window.cascorWS` + `ws_dash_bridge.js` + drain-callback stack with a single `dcc.WebSocket(id="ws", url="/ws/training")` component.

Reasons not to ship Option C in Phase B:

1. **Third-party dependency**: `dash-extensions` adds another upstream to track. Security review + pinning + CI coverage. The Juniper ecosystem currently has zero `dash-extensions` usage.
2. **Loses fine-grained control**: the component triggers a Dash callback per-message, not per-frame batched. That defeats the frame-budget optimization in §5.5.
3. **Reconnection semantics are the component's, not ours**: the GAP-WS-13 resume protocol (server_instance_id + last_seq replay) requires custom reconnect logic. The component does not provide hooks for "emit this first frame on reconnect." Patching around it would re-introduce most of the complexity we're trying to avoid.

**When to reconsider Option C**: if Phase B's custom wiring becomes a maintenance liability after 6 months, revisit. For now, Option B is simpler and more controllable.

#### 3.2.5 Ring buffer enforcement in the handler, not the drain callback (RISK-12)

This is the single most important design subtlety in the drain pattern: **the bound on `ws-metrics-buffer` must be enforced in the JS `on('metrics', ...)` handler, not in the Python drain callback**. Reason:

- Background tabs in modern browsers (Chromium, Firefox) throttle `setInterval`/`requestAnimationFrame` to ~1 Hz. Dash's `dcc.Interval` is a `setInterval` underneath.
- If a user leaves a dashboard in a background tab during a long training run, `fast-update-interval` fires only once per second. Meanwhile, the WebSocket handler continues to receive events at whatever rate the server emits.
- If the bound is enforced only in the drain callback (which runs at the throttled rate), the JS-side ring can grow unboundedly for minutes — up to hundreds of thousands of events — before the first drain fires and trims it back. That is the memory-exhaustion risk RISK-12 describes.
- Enforcing the bound in the handler (every push) makes the memory cap independent of drain rate. The cap is the cap, period.

The bounded-in-handler pattern is shown in §3.2.1's `_buffers.metrics.push(...)` + `splice` code. **Every `on(type, ...)` callback that pushes to an event-log buffer must include this splice-to-cap logic.** Topology and state are exceptions because they are last-wins (single snapshot, not a log).

### 3.3 Plotly `extendTraces` + rAF coalescing

The single biggest per-frame optimization. Per §5.5, full figure replacement with 10k points costs 80-200 ms per update. `extendTraces` with `maxPoints` is O(1) per event and preserves pan/zoom state. This section specifies how to migrate `metrics_panel.py` and `candidate_metrics_panel.py`, and how to wire the rAF scheduler so at most one Plotly call runs per animation frame.

#### 3.3.1 Current path (to be replaced)

Current `MetricsPanel.update_metrics_display()` callback at `metrics_panel.py:648-670`:

```
Input: metrics-panel-metrics-store.data   (full metrics history list)
Output: metrics-panel-figure.figure        (full Plotly figure object)
```

On every update, it constructs a new `go.Figure(...)` with the entire history as the trace data. Dash then diffs the figure JSON against the previous value and sends the entire new figure over the WebSocket to the browser, which replaces the plot.

Problems:
1. The figure object can be 100-500 KB for a 10k-point run, serialized per update.
2. Plotly.js must rebuild SVG/WebGL data on every replacement.
3. Pan/zoom state is lost unless explicitly preserved in `uirevision`.
4. The Dash diff runs server-side on every update, consuming CPU.

#### 3.3.2 Target path (`extendTraces` via clientside_callback)

Replace the server-side figure-replace callback with a clientside_callback that calls `Plotly.extendTraces` directly:

```python
# metrics_panel.py (illustrative — the real implementation merges with the existing component wiring)
clientside_callback(
    """
    function(buffer_data, current_fig_state) {
        if (!buffer_data || !buffer_data.events || !buffer_data.events.length) {
            return window.dash_clientside.no_update;
        }
        const events = buffer_data.events;
        // Extract xs/ys per trace from the event batch
        const epochs = events.map(e => e.epoch);
        const losses = events.map(e => (e.metrics && e.metrics.loss) || null);
        const accs   = events.map(e => (e.metrics && e.metrics.accuracy) || null);
        const vlosses = events.map(e => (e.metrics && e.metrics.val_loss) || null);
        const vaccs   = events.map(e => (e.metrics && e.metrics.val_accuracy) || null);

        // Plotly.extendTraces mutates the graph div in-place
        // trace indices match the figure construction order in the initial layout
        const graphId = 'metrics-panel-figure';
        const update = {
            x: [epochs, epochs, epochs, epochs],
            y: [losses, accs, vlosses, vaccs]
        };
        const traceIndices = [0, 1, 2, 3];
        const maxPoints = 5000;  // RISK-10 — hard cap on in-memory points

        if (window.Plotly && document.getElementById(graphId)) {
            window.Plotly.extendTraces(graphId, update, traceIndices, maxPoints);
        }
        // No figure replacement; the callback has no Output for the figure
        return window.dash_clientside.no_update;
    }
    """,
    Output("metrics-panel-figure-signal", "data"),  # dummy output (see §3.3.4)
    Input("ws-metrics-buffer", "data"),
    State("metrics-panel-figure-signal", "data"),
)
```

Key points:

1. **The Input is `ws-metrics-buffer.data`**, not a polling interval. The callback fires only when the store actually updates — which is driven by the drain callback in §3.2, which is driven by `fast-update-interval` ticks that have new data to deliver.
2. **`maxPoints=5000`**: enforced by Plotly itself. When the trace exceeds 5000 points, the oldest points are dropped. This is the primary defense against RISK-10 unbounded chart memory.
3. **`window.Plotly.extendTraces` mutates the graph in-place**: does NOT reconstruct the figure, does NOT replace the DOM, does NOT reset pan/zoom. This is the critical performance win.
4. **Dummy output (`metrics-panel-figure-signal`)**: Dash clientside callbacks must declare an Output even if they do nothing useful with it. A hidden `dcc.Store(id='metrics-panel-figure-signal')` component receives dummy values so the callback graph is satisfied without actually triggering a figure diff. This pattern is slightly ugly but it is the standard Dash idiom for "clientside side-effect-only" callbacks.
5. **`null` handling for missing sub-metrics**: val_loss / val_accuracy may be absent during the candidate phase. The `|| null` coercion sends `null` to Plotly, which renders a gap in the trace — the correct visual behavior.

#### 3.3.3 requestAnimationFrame coalescing (GAP-WS-15)

At 50 Hz `candidate_progress` burst rates, even the drain pattern (at 100 ms tick) sends 5 events per tick. Each tick fires the chart callback once, which calls `Plotly.extendTraces` once. That is fine — the drain already coalesces to 10 Hz.

The rAF coalescer is a second-order optimization that only matters if:
1. The drain interval is tightened from 100 ms to < 16.67 ms (unlikely — 100 ms is sufficient).
2. Multiple chart types are simultaneously updating and their combined cost exceeds the 16.67 ms frame budget.
3. The underlying browser is slow and the rAF scheduler is the only way to avoid jank.

For Phase B, I recommend the rAF coalescer be **implemented in `ws_dash_bridge.js` but kept simple**: events accumulated inside the same rAF frame are batched into a single `Plotly.extendTraces` call via the `_scheduleRaf` helper sketched in §3.2.1. The Python-side drain callback remains unchanged.

Pseudo-code:

```javascript
function _scheduleRaf(type, data) {
  _rafQueue[type].push(data);
  if (_rafHandle === null) {
    _rafHandle = window.requestAnimationFrame(function() {
      _rafHandle = null;
      // Directly call Plotly.extendTraces for each type that has pending events
      // NOTE: this is an OPTIMIZATION — the drain callback also renders; the rAF path
      // is a shortcut for sub-frame bursts. It is safe to double-render because
      // extendTraces with maxPoints is idempotent w.r.t. the bound.
      const metricsBatch = _rafQueue.metrics;
      _rafQueue.metrics = [];
      if (metricsBatch.length) {
        _applyPlotlyExtendForBatch('metrics-panel-figure', metricsBatch);
      }
      const candBatch = _rafQueue.candidate_progress;
      _rafQueue.candidate_progress = [];
      if (candBatch.length) {
        _applyPlotlyExtendForBatch('candidate-metrics-panel-figure', candBatch);
      }
    });
  }
}
```

**Important caveat**: the rAF path and the drain-callback path will both try to render the chart. This is safe only if:
- `extendTraces` is idempotent w.r.t. the bound (it is; the oldest points drop at the cap).
- The rAF path pulls from the same JS-side ring buffer that the drain callback pulls from — and both mutate that buffer by removing drained items.

Actually, reviewing this again: the rAF path consuming events directly creates a double-render risk. **Simplification: for Phase B, ship WITHOUT the rAF path** and use only the drain callback. The 100 ms drain interval produces ~10 Hz render rate, which is comfortably under the 60 Hz budget. Phase B's scope is already large; rAF coalescing is a Phase B+1 optimization if instrumentation shows it is needed.

I will flag this as a deviation from GAP-WS-15 in §7 (Disagreements). Summary: **implement rAF coalescing as a scaffold in the JS bridge but leave it disabled (feature-flagged) in Phase B**; enable only if §5.6 latency instrumentation shows render jank.

#### 3.3.4 The dummy-output pattern and its alternatives

The `metrics-panel-figure-signal` dummy Output is required because Dash clientside callbacks need at least one declared Output. Alternatives considered:

- **Output to `metrics-panel-figure.figure`**: would work but then Dash thinks the callback wrote a new figure, which re-triggers server-side diff logic. Defeats the purpose.
- **Pattern-matching Output with `ALL`**: overkill for a single graph.
- **Store with `clear_data` flag**: works but introduces additional store churn.

The dummy-output pattern is explicitly documented in the Dash clientside callback docs and is the idiomatic solution. Add a brief comment at the callback registration site citing this proposal so future readers understand why the output is ignored.

#### 3.3.5 `uirevision` preservation

When the chart does need to be fully replaced (e.g., after a reconnect that triggers the §6.5.2 snapshot handoff using `Plotly.react`), the layout must include `layout.uirevision` set to a stable value. This preserves pan/zoom across the `Plotly.react` call. Without it the view resets to the default x/y range on every replace.

Set `uirevision` to a constant (e.g., `"metrics-panel-v1"`) in the initial figure construction in `metrics_panel.py`. This is a 1-line change that should ship with Phase B even though `Plotly.react` is only called on snapshot handoff.

### 3.4 Eliminating `/api/metrics/history` polling (GAP-WS-16 + GAP-WS-25)

This is the P0 motivator — ~3 MB/s of pure REST waste per dashboard. The fix has two parts: (a) the polling callback must check WebSocket status and `no_update` out when connected, and (b) the polling interval must be relaxed when polling is the secondary path.

#### 3.4.1 Connection-status store (`ws-connection-status`)

A new `dcc.Store(id='ws-connection-status')` is added to the dashboard layout. It is populated via an Option B drain from `window._juniperWsDrain.peekStatus()`:

```python
# dashboard_manager.py — new callback, registered alongside the other drains
clientside_callback(
    """
    function(n_intervals, current) {
        if (!window._juniperWsDrain) {
            return window.dash_clientside.no_update;
        }
        const status = window._juniperWsDrain.peekStatus();
        if (!status) return window.dash_clientside.no_update;
        // Only emit if something meaningful changed
        const curConnected = current && current.connected === true;
        const newConnected = status.connected === true;
        const curReason = (current && current.reason) || null;
        const newReason = status.reason || null;
        if (curConnected === newConnected && curReason === newReason) {
            return window.dash_clientside.no_update;
        }
        return {
            connected: newConnected,
            last_change_ms: status.ts || performance.now(),
            reason: newReason,
            reconnect_attempt: status.reconnectAttempt || 0,
        };
    }
    """,
    Output("ws-connection-status", "data"),
    Input("fast-update-interval", "n_intervals"),
    State("ws-connection-status", "data"),
)
```

The callback fires every 100 ms but only emits an update when the peek returns non-null AND at least one of `connected` / `reason` has actually changed versus the current store state. In the common steady-state where the connection is healthy and nothing has changed, the callback returns `no_update` and the store is not rewritten — which in turn means downstream consumers (the polling toggle and the indicator badge) do not re-fire either.

Note: the cascorWS `onStatus()` handler in `ws_dash_bridge.js` writes `_buffers._status = status` on every status callback from the underlying WebSocket. The drain's comparison against the current store state is what prevents thrashing. In practice the status changes rarely — only on connect/disconnect/reconnect transitions — so the peek-and-compare pattern is a no-op on the vast majority of ticks.

#### 3.4.2 The polling toggle in `_update_metrics_store_handler`

Per §6.3 the pattern is:

```python
@callback(
    Output("metrics-panel-metrics-store", "data"),
    Input("fast-update-interval", "n_intervals"),
    State("ws-connection-status", "data"),
    State("metrics-panel-metrics-store", "data"),
)
def _update_metrics_store_handler(n, ws_status, current_data):
    if ws_status and ws_status.get("connected"):
        # WebSocket is driving metrics. Do NOT poll.
        return no_update
    # Fallback / initial-load path
    if current_data is None or _should_fetch_history(n, current_data):
        return requests.get(
            self._api_url("/api/metrics/history?limit=1000"),
            timeout=2
        ).json()
    return no_update
```

Two refinements beyond what the architecture doc shows:

1. **The REST fallback interval is relaxed from 100 ms to ~1 Hz** when `current_data` is already populated. In the fallback case the dashboard has lost the WebSocket and is waiting for reconnect; polling at 100 ms is still wasteful, but polling at 1 Hz (matching the §6.4 disconnection taxonomy's 1 Hz fallback cadence) is 10× better. Implementation: check `(n % 10) != 0` in the handler and return `no_update` on non-matching ticks. This keeps the `fast-update-interval` component unchanged (avoiding a cascade of other callback changes) while effectively slowing the polling.
2. **Initial load is always REST** — the first time the handler runs, `current_data is None` and it must seed the store with history regardless of WebSocket status. This is the §6.3 "REST for initial snapshot; WebSocket for live merge" pattern.

The combination of (1) WebSocket-connected → `no_update`, (2) WebSocket-disconnected but data present → 1 Hz fallback, (3) initial load → REST GET gives us:

| State | Behavior | Bandwidth |
|---|---|---|
| Steady state, WebSocket healthy | `no_update`, no REST | 0 B/s (from this endpoint) |
| Initial load | 1 REST GET | ~300 KB one-shot |
| WebSocket disconnected, waiting for reconnect | 1 REST GET per second | ~300 KB/s |
| WebSocket reconnected | reverts to `no_update` | 0 B/s |

**Bandwidth elimination**: ~3 MB/s → ~0 B/s in the common case. This is the P0 win.

#### 3.4.3 Applying the same pattern to other polling handlers

The same toggle must be added to every polling callback that would conflict with a WebSocket-driven path. The known ones (per §2.8 and a grep of `dashboard_manager.py`):

- `_update_metrics_store_handler` (`dashboard_manager.py:2388-2421`) — the P0 motivator
- `_handle_training_state_poll` — the state-polling callback that feeds the status badge and epoch counter
- `_handle_candidate_progress_poll` — candidate metrics panel
- `_handle_topology_poll` — NetworkVisualizer's 5-second polling callback (keep the REST path, but reduce to `no_update` on WS-healthy state; WS push drives it)

The architecture doc does not enumerate these — it gives the pattern and leaves the enumeration to the implementation PR. This proposal makes the enumeration explicit so the Phase B PR description can list each callback rather than discovering them iteratively.

### 3.5 Removing dead JS WebSocket clients

There are two JS WebSocket client implementations per §2.7. This section specifies exactly what happens to each.

#### 3.5.1 `assets/websocket_client.js` — KEEP and clean up

Per GAP-WS-02, this file's `window.cascorWS` / `window.cascorControlWS` classes have the right API shape and are the integration target. **Do not delete.** Clean-up tasks within Phase B:

1. **Verify `onStatus()` is exposed and correct**. The status callback must receive an object with at least `{connected: bool, reason: str, reconnectAttempt: int, ts: number}`. If the current implementation only exposes a boolean, extend it.
2. **Add `permessage-deflate` support indicator**: not configurable from the client side, but surface it in the status object so instrumentation can correlate bandwidth with compression state.
3. **Jitter in reconnect backoff (GAP-WS-30)**: three-line change. Replace the deterministic `[500, 1000, 2000, 5000]` schedule with `delay = Math.random() * Math.min(cap, base * Math.pow(2, attempt))`.
4. **Remove the 10-attempt cap (GAP-WS-31)**: retry forever at max 30 s intervals. The connection indicator (GAP-WS-26) keeps the user informed.
5. **Add `server_instance_id` handling**: parse it from the `connection_established` message's data; store in a module-scope variable for the next reconnect. On reconnect, emit `{type: "resume", data: {last_seq: ..., server_instance_id: ...}}` as the first frame. If cascor does not support resume (or returns `resume_failed`), fall back to full REST snapshot refresh per §6.5.2.
6. **Add `seq` tracking**: on every inbound message, record `msg.seq` in a module-scope `_lastSeq` variable. Monotonically check that `msg.seq > _lastSeq` and log a WARN if out-of-order (indicates a server bug or a reordering middlebox — should never happen on a well-behaved WebSocket).
7. **Add the bounded JS ring (unused by current callers but required by GAP-WS-13 replay)**: a small FIFO of the last ~256 events with their `seq` numbers. On a full disconnect followed by resume, the client compares its last acknowledged `seq` against the server's replay — the ring is mostly belt-and-suspenders but protects against double-apply.
8. **Delete dead helpers** that are not referenced post-integration. The `getBufferedMessages()` destructive read method is one such; its only caller was the dead drain callback. Keep the documented API methods (`on`, `onStatus`, `send`) and delete internal helpers with no callers.

The file should end up at ~200-250 lines post-cleanup (currently ~230).

#### 3.5.2 `dashboard_manager.py:1490-1526` clientside callback — DELETE

This is the parallel raw-WebSocket client. Its removal is straightforward:

- Delete lines 1490-1526 entirely.
- Delete the `ws-metrics-buffer` init callback (the broken one returning `no_update`) — it is replaced by the new drain callback in §3.2.2.
- Delete references to `window._juniper_ws_buffer`, `window._juniper_ws_topology`, `window._juniper_ws_state` globals anywhere else in `dashboard_manager.py`. The topology and state drain callbacks (currently at `dashboard_manager.py:1531-1564`) must be updated to call `window._juniperWsDrain.drainTopology()` / `drainState()` instead.
- Add a brief comment at the deletion site: `# Former parallel WebSocket client deleted in Phase B — see R0-01_frontend_performance.md and GAP-WS-03. All WebSocket subscriptions now flow through assets/websocket_client.js + assets/ws_dash_bridge.js.`

Post-deletion verification: `grep -r "_juniper_ws_" juniper-canopy/src/frontend/` returns zero matches. `grep -r "new WebSocket" juniper-canopy/src/frontend/` returns zero matches in any Python or JS file (the only `new WebSocket(...)` call should be inside `assets/websocket_client.js` itself).

#### 3.5.3 Dead-code in tests

Check `juniper-canopy/src/tests/` for any existing tests that exercise the dead clientside callback or the `_juniper_ws_*` globals. If any exist, update them to match the new wiring. If they are asserting things about the broken behavior (e.g., "the store is never written to"), delete them.

### 3.6 Nested-vs-flat metric format cleanup strategy

Per §4, the dual format is NOT dead code — `MetricsPanel` reads `m["metrics"]["loss"]` style nested accessors. **Do not touch the format in Phase B.** GAP-WS-11 is explicitly Phase H territory.

What Phase B needs to know about the format:

1. **The drain-callback → chart-render path must read the nested keys**. The clientside callback in §3.3.2 reads `e.metrics.loss`, `e.metrics.accuracy`, `e.metrics.val_loss`, `e.metrics.val_accuracy`. These are the nested accessors that `MetricsPanel` already uses. Using the flat keys (`e.train_loss`, etc.) would work too and the values would be identical, but the nested accessors match the existing chart code's pattern and any future audit of the flat keys will not break the clientside callback if the two paths agree.
2. **`ws-metrics-buffer.events` preserves the full dict**. The JS-side handler does not strip either format; it pushes the entire `msg.data` dict into the ring. Consumers can read whichever shape they prefer.
3. **Regression test**: the Phase H plan (§9.9) says "Add `test_normalize_metric_produces_dual_format` BEFORE the audit." Phase B should also pin the wire-level assertion: "after the browser receives a `metrics` message via WebSocket, `ws-metrics-buffer.data.events[-1]` contains BOTH the nested and flat keys." This is a Playwright wire test that protects against a future refactor silently dropping one format.

Add this single Playwright wire test to the Phase B test suite:

```python
def test_metrics_message_has_dual_format(page, fake_cascor_server):
    fake_cascor_server.script({
        "type": "metrics",
        "timestamp": time.time(),
        "data": {
            "epoch": 1,
            "metrics": {"loss": 0.5, "accuracy": 0.9, "val_loss": 0.6, "val_accuracy": 0.85},
            "network_topology": {"hidden_units": 2},
            "train_loss": 0.5,
            "train_accuracy": 0.9,
            "val_loss": 0.6,
            "val_accuracy": 0.85,
            "hidden_units": 2,
            "phase": "output",
            "timestamp": "2026-04-11T00:00:00Z",
        }
    })
    page.goto(canopy_url)
    page.wait_for_function("() => window._juniperWsDrain._introspect().metricsSize > 0")
    buf_state = page.evaluate("() => window._juniperWsDrain._introspect()")
    # Assertion runs against the event buffer AFTER drain completes
    last = page.evaluate("""() => {
        const store = document.querySelector('#ws-metrics-buffer');
        // Read Dash store data via the dash_clientside API
        return window.dash_clientside && window.dash_clientside.callback_context;
    }""")
    # More concretely, use dash_duo's wait_for_* helpers in a dash_duo test
    # rather than Playwright for this store-state assertion
```

The above is pseudocode; in practice this assertion belongs in a `dash_duo` test because `dash_duo` natively reads store state. The Playwright version demonstrates the event shape by intercepting the WebSocket frame before it reaches the drain. Both approaches have a place in the test suite:

- **Playwright wire test**: asserts the cascor→canopy→browser wire format is dual-format-compatible. Catches server-side regressions.
- **`dash_duo` store test**: asserts the drain callback preserves both keys in the store. Catches client-side regressions.

---

## 4. Implementation steps

Each step below has a file-level target, approximate line references (against `origin/main` as of 2026-04-10), dependency notes, and verification hooks. Steps are ordered to minimize churn on partially-merged intermediate states.

1. **[cascor / out of scope, dependency only]** Confirm cascor `seq` field work is in progress or landed. If not, Phase B can still ship — the client handles missing `seq` by defaulting to 0 and never triggering replay. Flag as a soft dependency in the PR description.

2. **[canopy]** Add the `ws-cascade-add-buffer` and `ws-candidate-progress-buffer` `dcc.Store` declarations to the dashboard layout alongside the existing `ws-metrics-buffer`, `ws-topology-buffer`, and `ws-state-buffer`. Locate the existing store declarations in `dashboard_manager.py` (search for `ws-metrics-buffer`) and add the new ones in the same block. **File**: `juniper-canopy/src/frontend/dashboard_manager.py` (store declarations are near the top of the layout construction, likely around line 1200-1300).

3. **[canopy]** Add the `ws-connection-status` store declaration. Same location. Initial value `{connected: false}`.

4. **[canopy]** Add the `metrics-panel-figure-signal` dummy store (see §3.3.4) to the metrics panel layout. **File**: `juniper-canopy/src/frontend/components/metrics_panel.py`.

5. **[canopy / js]** Create `juniper-canopy/src/frontend/assets/ws_dash_bridge.js` per the skeleton in §3.2.1. ~200 lines. Alphabetical load order after `websocket_client.js` (verified by file naming).

6. **[canopy / js]** Clean up `juniper-canopy/src/frontend/assets/websocket_client.js` per §3.5.1. Add `onStatus` enrichment, jitter, uncapped reconnect, `server_instance_id` tracking, `seq` tracking, and delete `getBufferedMessages()`. **Pin the behavior with Jest/Vitest unit tests** (§8 recommends this tier for JS-only logic).

7. **[canopy]** Delete the parallel raw-WebSocket clientside callback at `dashboard_manager.py:1490-1526`. Add the deletion comment.

8. **[canopy]** Rewrite the `ws-metrics-buffer` drain callback to read from `window._juniperWsDrain.drainMetrics()` per §3.2.2. **File**: `dashboard_manager.py` — near the former init callback site.

9. **[canopy]** Update the topology and state drain callbacks at `dashboard_manager.py:1531-1564` to read from `window._juniperWsDrain.drainTopology()` / `drainState()`. Remove all references to `window._juniper_ws_topology` / `window._juniper_ws_state`.

10. **[canopy]** Add new drain callbacks for `ws-cascade-add-buffer` and `ws-candidate-progress-buffer`. Pattern matches the metrics drain.

11. **[canopy]** Add the `ws-connection-status` drain callback per §3.4.1.

12. **[canopy]** Refactor `_update_metrics_store_handler` at `dashboard_manager.py:2388-2421` to (a) read `ws-connection-status` via State, (b) return `no_update` when connected, (c) slow the fallback polling to 1 Hz by checking `n % 10 == 0`. Preserve the initial-load REST GET path.

13. **[canopy]** Apply the same toggle pattern to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, and any other polling callback that would conflict with WS push. Enumerate these in the PR description.

14. **[canopy]** Rewrite `MetricsPanel.update_metrics_display()` at `metrics_panel.py:648-670` as a clientside_callback calling `Plotly.extendTraces` per §3.3.2. Preserve the existing initial figure construction (for page-load snapshot rendering). Add `uirevision: "metrics-panel-v1"` to the figure layout.

15. **[canopy]** Apply the same `extendTraces` pattern to `CandidateMetricsPanel` in `candidate_metrics_panel.py`. `maxPoints=5000`.

16. **[canopy]** For `NetworkVisualizer` (cytoscape graph), do NOT use `extendTraces` (cytoscape is not Plotly). Instead, the callback takes `ws-topology-buffer` and `ws-cascade-add-buffer` as Inputs and performs a cytoscape element mutation. This is lower priority and can defer to Phase B+1 if scope is tight. Minimum: wire the WS path so the graph updates on cascade_add events without polling.

17. **[canopy]** Add the connection indicator badge component (GAP-WS-26). A small `html.Div` with a clientside callback that reads `ws-connection-status` and toggles a CSS class. Four states: connected (green), reconnecting (yellow), offline (red), demo (gray).

18. **[canopy]** Demo mode parity (GAP-WS-33 + RISK-08): ensure `demo_mode.py` sets the connection status to `{connected: true, mode: "demo"}` via the same `window._juniperWsDrain` peek path (or directly via a `set_props` on `ws-connection-status`). The badge shows "demo" and the polling toggle correctly returns `no_update` in demo mode too.

19. **[canopy]** Add the browser-side latency instrumentation JS module per §5.6 / GAP-WS-24. ~50-100 LOC in `assets/ws_latency.js`. Records `received_at_ms = performance.now()` per inbound message, subtracts from `msg.emitted_at_monotonic` (accounting for clock offset captured in `connection_established`), bucketizes into histograms, POSTs to `/api/ws_latency` every 60 s. The server-side `/api/ws_latency` endpoint is the cascor/backend agent's responsibility, not this proposal's — but the browser emitter is in scope here and should land together.

20. **[canopy]** Add the `metrics-panel-figure-signal` hidden store for the clientside callback's dummy output.

21. **[canopy / tests]** Write the `dash_duo` fixtures and test files per §8.4. This is ~1.5 days of fixture setup + ~1 day of actual test coverage. Use `FakeCascorServerHarness` from §8.5 via `pytest.importorskip("juniper_cascor_client.testing")`.

22. **[canopy / tests]** Write the Playwright wire tests per §8.4. Focus on three things only: (a) WebSocket frame has `seq` field, (b) resume protocol replays missed events, (c) connection status indicator reflects state. Leave the store-state assertions to `dash_duo`.

23. **[canopy / tests]** Add the `test_demo_mode_metrics_parity` test (RISK-08).

24. **[canopy / ci]** Update CI per §8.5.1 — marker split, `playwright install` step, trace artifact upload on failure.

25. **[canopy / tests]** Regression test: `test_chart_does_not_poll_when_websocket_connected`. Assert that the `requests.get` call count for `/api/metrics/history` is 1 (initial load) over a 5-second test run with WebSocket connected. Use `unittest.mock.patch` or Playwright network interception.

26. **[canopy / tests]** Memory cap regression test: drive the fake cascor server to emit 5000 metrics events. Assert `ws-metrics-buffer.data.events.length === 1000` (the store cap). Assert `Plotly.extendTraces` was called with `maxPoints=5000` and the chart trace has `<=5000` points.

27. **[cascor / out of scope]** Coordinate with the cascor agent on the `seq` field and replay buffer ship date. Phase B's reconnect test depends on the server supporting resume.

28. **[cascor / out of scope]** Coordinate with the security agent on Phase B-pre Origin allowlist + cookie-session auth + CSRF-in-first-frame. Phase B's JS can be pre-wired to send the CSRF token on the first frame; disable this behind a feature flag if Phase B-pre slips.

29. **[canopy / docs]** Update `juniper-canopy/docs/architecture.md` (or equivalent) with a brief diagram showing the new data path: cascor → canopy adapter → canopy `/ws/training` → browser `websocket_client.js` → `ws_dash_bridge.js` → `_juniperWsDrain` → dcc.Interval drain → `ws-*-buffer` stores → chart clientside callbacks → Plotly.extendTraces. One diagram is worth 500 words of prose here.

30. **[phase I / asset cache busting]** Configure `assets_url_path` with a content-hash query string per §9.10. Trivial 0.5-day change. Ship in the same PR as Phase B so browsers pick up the new JS without hard refresh.

31. **[canopy / tests]** Add the wire-format regression test `test_metrics_message_has_dual_format` from §3.6 as the first line of defense against RISK-01 (dual format removal).

---

## 5. Risks and mitigations (frontend-specific)

| ID | Risk | Mitigation |
|---|---|---|
| FR-RISK-01 | Background tab throttling delays the drain callback, allowing `_buffers.metrics` to grow unboundedly | JS-side ring enforced in the `on('metrics', ...)` handler, NOT in the drain callback (see §3.2.5). Cap is independent of drain rate. |
| FR-RISK-02 | `Plotly.extendTraces` called before the graph div exists (race with Dash's graph mount) | Guard with `document.getElementById(graphId)` check; if absent, skip the call. The next drain will populate the chart once the div mounts. |
| FR-RISK-03 | `Plotly.extendTraces(maxPoints)` behavior differs across Plotly.js versions | Pin `plotly` to a known version in `juniper-canopy/pyproject.toml` and confirm the `extendTraces` signature. Current Plotly (2.x+) supports the 4th arg; older versions (1.x) do not. |
| FR-RISK-04 | Clientside callback fires before `window.cascorWS` exists (load-order race) | Alphabetical load order ensures `websocket_client.js` loads before `ws_dash_bridge.js`. Add defensive guard in `ws_dash_bridge.js`: `if (!window.cascorWS) return;` and retry in a `DOMContentLoaded` handler. |
| FR-RISK-05 | Dash `dcc.Store` mutation triggers unintended cascading callbacks on other components | Audit the callback graph: enumerate every `Input("ws-metrics-buffer", "data")` and verify each is intentional. Use `prevent_initial_call=True` on any cascading callback. |
| FR-RISK-06 | The `metrics-panel-figure-signal` dummy output is confusing to future readers | Add a comment block above the clientside callback registration explaining the pattern and linking to this proposal. |
| FR-RISK-07 | `uirevision` prevents the chart from resetting after a training reset (user clicks "Reset") | Tie `uirevision` to a training-run ID that increments on reset, e.g., `f"metrics-panel-v1-{training_run_id}"`. When the user resets, the reset handler writes a new `training_run_id` to a store; the chart layout callback picks it up and flips `uirevision`. |
| FR-RISK-08 | Drain callback's `State("ws-metrics-buffer", "data")` causes it to be rewritten on every tick even when nothing changes | The `no_update` sentinel in the drain body (when the JS-side ring is empty) prevents the rewrite. Verify with `dash_duo` that the store's timestamp does not change during idle intervals. |
| FR-RISK-09 | Memory leak from `window._juniperWsDrain` closure holding references to detached DOM graph divs | No DOM references are held in the closure — only primitives and plain object literals. Plotly's `extendTraces` is called with the graph ID string, not a DOM reference. Risk is low. |
| FR-RISK-10 | Clientside callback throws an uncaught exception that silently kills the Dash callback graph | Wrap the body in `try { ... } catch (e) { console.error('[ws_dash_bridge] drain failure', e); return window.dash_clientside.no_update; }`. Add a Sentry (or equivalent) error-reporting hook. |
| FR-RISK-11 | `requests.get("/api/metrics/history")` in `_update_metrics_store_handler` still fires during the initial-load window, creating a brief mix of WS push + REST polling | The initial load happens before `ws-connection-status` is populated (the handler sees `ws_status = None`). Accept this 1-tick overlap; the merge logic in the chart's clientside callback is idempotent w.r.t. `epoch`-keyed deduplication. |
| FR-RISK-12 | `extendTraces` append-only path produces duplicate points if the drain happens twice for the same event batch | Drain function mutates the JS-side ring (`_buffers.metrics = []`), so a second drain returns an empty array. Idempotent. |
| FR-RISK-13 | `dash_duo` tests fail in CI due to ChromeDriver version mismatch | Use `playwright install chromium` for Playwright tests; `dash_duo` still requires ChromeDriver but is handled by the `dash[testing]` extra. Pin both versions in the CI workflow file. |
| FR-RISK-14 | Clientside callback's `eval`-executed JS string hides syntax errors until runtime | Dash emits a warning on registration if the string is malformed, but does not catch logic errors. Mitigation: extract non-trivial clientside callbacks to `assets/*.js` files with named functions, and reference them from `clientside_callback(ClientsideFunction("namespace", "fn_name"), ...)`. This is the Dash idiom for non-trivial clientside logic. |
| FR-RISK-15 | The rAF coalescer double-renders with the drain callback, producing visible jank | Phase B ships with rAF coalescer DISABLED (feature-flagged `_scheduleRaf = noop`). Enable only if instrumentation shows a bottleneck. |

---

## 6. Verification / acceptance criteria

Each bullet below is a concrete check that must pass before Phase B is considered complete.

### 6.1 Unit-level (Jest/Vitest for JS, pytest for Python)

- **AC-01**: `assets/websocket_client.js` unit tests cover: jitter in reconnect schedule, uncapped retries, `onStatus` callback invocation on connect/disconnect/error, `server_instance_id` parsing from `connection_established`, `seq` monotonicity check, bounded ring buffer.
- **AC-02**: `assets/ws_dash_bridge.js` unit tests cover: handler registration on `window.cascorWS`, ring buffer cap enforcement in the handler (push 1001 events, assert `_buffers.metrics.length === 1000`), drain functions return and clear, `_introspect` returns correct state.
- **AC-03**: `_update_metrics_store_handler` Python unit test: mock `requests.get`, assert it is called on initial load, NOT called when `ws_status["connected"]` is True, called at 1 Hz when `ws_status["connected"]` is False and `current_data` exists.

### 6.2 `dash_duo` store-level

- **AC-04**: `test_browser_receives_metrics_event` — fake cascor server emits a `metrics` message; `dash_duo` waits for `ws-metrics-buffer.data.events.length === 1` via a JS `page.evaluate` helper; asserts the event shape matches the input.
- **AC-05**: `test_chart_updates_on_each_metrics_event` — emit 10 metrics events; assert the chart's trace 0 has `>=10` points via `page.evaluate("() => document.getElementById('metrics-panel-figure').data[0].y.length")`.
- **AC-06**: `test_chart_does_not_poll_when_websocket_connected` — register a network-request interceptor for `/api/metrics/history`; emit metrics via WebSocket for 5 seconds; assert interceptor captured 1 request (initial load only), not 50.
- **AC-07**: `test_chart_falls_back_to_polling_on_websocket_disconnect` — close the WebSocket mid-test; assert interceptor starts seeing `/api/metrics/history` requests within 1 second.
- **AC-08**: `test_demo_mode_metrics_parity` — run dashboard in demo mode; emit demo metrics; assert the same store wiring works and the chart updates without a real cascor backend.
- **AC-09**: `test_metrics_message_has_dual_format` — emit a metrics message with both nested and flat keys; assert `ws-metrics-buffer.data.events[-1]` contains BOTH `metrics.loss` AND `train_loss`.
- **AC-10**: `test_connection_indicator_reflects_status` — assert the connection indicator CSS class is `connected-green` when healthy, `offline-red` when disconnected, `demo-gray` in demo mode.

### 6.3 Playwright wire-level

- **AC-11**: `test_websocket_frames_have_seq_field` — intercept the canopy `/ws/training` WebSocket using Playwright's `page.on('websocket')` + `ws.on('framereceived')`; emit a metric; assert the received frame's JSON contains a `seq` field.
- **AC-12**: `test_resume_protocol_replays_missed_events` — connect, send a few events, disconnect the WebSocket server, reconnect, assert the client sends `{type: "resume", data: {last_seq: ..., server_instance_id: ...}}` as its first frame; the fake server replies with the missed events.
- **AC-13**: `test_connection_status_indicator_reflects_websocket_state` — drive the state via fake server close/reopen; assert the indicator CSS class transitions happen within 1 second.
- **AC-14**: `test_start_button_uses_websocket_command` — click start; assert the outbound WebSocket frame contains `{command: "start"}`, NOT a REST POST. (This overlaps with Phase D but the wire test is valuable as a Phase B regression gate.)

### 6.4 Frame budget / performance regression

- **AC-15**: `test_render_frame_under_budget` — emit 50 Hz `candidate_progress` for 2 seconds (100 events); measure the max frame duration via `performance.now()` instrumentation; assert `max_frame_ms < 16.67` (or at worst `< 33.33` for 30 fps). This is the only quantitative frame-budget check in the suite and protects against future regressions in the chart render path.
- **AC-16**: `test_memory_bounded_over_long_run` — emit 5000 metrics events; assert `ws-metrics-buffer.data.events.length === 1000` (the cap); assert Plotly chart data length `<= 5000` per trace.
- **AC-17**: `test_bandwidth_eliminated_in_ws_mode` — run dashboard in WebSocket mode for 10 seconds; measure total bytes fetched from `/api/metrics/history` via network interception; assert `bytes_fetched < 400_000` (initial snapshot only, ~300 KB + headers). The target is "<1 MB total for the whole run" vs the current ~30 MB for the same 10-second window.

### 6.5 Smoke / integration

- **AC-18**: `test_full_training_run_no_errors` — drive the fake cascor server through a scripted 50-epoch training run; assert no console errors in the browser; assert the final chart shows 50 points; assert no orphaned WebSocket connections remain after dashboard close.
- **AC-19**: `test_dashboard_manager_has_no_dead_websocket_references` — grep-based assertion: `grep -r "window\._juniper_ws_" juniper-canopy/src/frontend/` returns zero matches.
- **AC-20**: `test_cascorws_is_only_websocket_constructor` — grep-based assertion: `grep -r "new WebSocket" juniper-canopy/src/frontend/` returns one match, and it is in `assets/websocket_client.js`.

The grep-based assertions (AC-19, AC-20) are cheap and catch accidental regression from a partial revert or merge conflict. They run in CI as a `pytest` test that shells out to `grep`.

---

## 7. Disagreements with the source doc

1. **GAP-WS-15 rAF coalescing should be scaffolded but DISABLED in Phase B** (vs. the source doc's implication that it ships with Phase B). Reasoning: the 100 ms drain interval already produces ~10 Hz render rate, well under the 60 fps budget. rAF coalescing is a Phase B+1 optimization that should be enabled only after §5.6 instrumentation shows frame-budget pressure. **Justification**: the source doc itself notes (RISK-02) that clientside callback wiring is finicky to debug; shipping fewer moving parts in Phase B is strictly safer. The rAF code can live in the bridge file as a no-op (`_scheduleRaf = noop`) without affecting correctness.

2. **The `_update_metrics_store_handler` REST fallback should be slowed to 1 Hz**, not just toggled off when WS is connected. The source doc §6.3 only specifies the WS-connected case; it does not say what the fallback cadence should be during reconnect. 100 ms polling during reconnect is the same pathological rate as the current implementation; 1 Hz matches the §6.4 disconnection taxonomy's fallback cadence. **Justification**: minimizes bandwidth during disconnect windows, which are typically short but can be long during cascor restarts. This is additive to the source doc, not contradictory.

3. **Phase B should ship WITHOUT `NetworkVisualizer` cytoscape migration if scope pressure is high**. The source doc lumps NetworkVisualizer into Phase B's "chart/panel callbacks" list but NetworkVisualizer uses cytoscape.js, not Plotly, and `extendTraces` does not apply. A proper cytoscape migration is a separate design exercise. **Justification**: Phase B is already a 4-day estimate that could slip. Deferring NetworkVisualizer to Phase B+1 does not block the P0 motivator (which is the metrics chart polling elimination). The existing 5-second REST polling for topology is bandwidth-negligible (~3 KB/s, 1000× smaller than the metrics bomb).

4. **The §5.5 frame budget line "MUST use extendTraces, not figure replace"** is too strong. Specifically, the snapshot replacement path (§6.5.2 after reconnect) correctly uses `Plotly.react(...)`, NOT `extendTraces`. This is a nuance the source doc itself acknowledges in §6.5.2, but the §5.5 unqualified "MUST use extendTraces" could be misread as applying everywhere. **Recommendation**: the implementation must use `extendTraces` for LIVE updates and `Plotly.react` for SNAPSHOT replacement. I am not disagreeing with the source doc's intent; I am disagreeing with a literal reading of the §5.5 frame-budget table that omits the snapshot case. This proposal explicitly codifies both paths.

5. **The `ws-metrics-buffer` store should be an EVENT LOG with bounded ring, not a last-wins snapshot**. The source doc GAP-WS-04 says "The store should be a bounded ring buffer (e.g., last 1000 metrics) to avoid unbounded memory growth" which agrees with this proposal. But the GAP-WS-04 target-state text also says "push into the metrics store" without specifying the shape. This proposal pins the shape as `{events: [...], gen: int, last_drain_ms: float}` — a structured object, not a bare list — so downstream consumers can detect store changes via `gen` even when the `events` array happens to be the same object reference. **Justification**: avoids a subtle Dash gotcha where Input-firing depends on JSON-serialized equality.

6. **GAP-WS-24 (latency instrumentation) — only the browser emitter is in scope here**. The server-side histogram endpoint, Prometheus export, and dashboard panel belong to a backend agent. This proposal ships the browser-side module (`assets/ws_latency.js` + POST to `/api/ws_latency`) but the backend endpoint is a coordination dependency. If the backend agent is not shipping in the same PR cycle, gate the browser-side POST behind a feature flag so the 60-second POST loop does not produce 404s in the console.

None of these are contradictions with the source doc's intent; they are refinements driven by implementation considerations. The source doc's design is correct at the architecture level; this proposal's disagreements are all at the "how exactly does this line of code behave in production" level.

---

## 8. Self-audit log

### 8.1 Pass 1 verification (what was checked)

- Read §0.1, §0.2, §1.1-§1.5 (executive summary and caveats) — confirmed the P0 motivator is `/api/metrics/history` at ~3 MB/s.
- Read §2.5-§2.8 — confirmed the broken dual-JS-client architecture at `dashboard_manager.py:1490` and `assets/websocket_client.js`.
- Read §3.1-§3.4 — confirmed message shapes for `metrics`, `state`, `topology`, `cascade_add`, `candidate_progress`, and the envelope asymmetry.
- Read §4 — confirmed the dual nested+flat format is NOT dead code; `MetricsPanel` reads nested accessors directly.
- Read §5.1-§5.7 — confirmed 100 ms / 200 ms / 500 ms latency tiers and the §5.3.1 ack-vs-effect distinction.
- Read §5.5 — confirmed the 16.67 ms frame budget and the `extendTraces` requirement.
- Read §5.6 — confirmed the latency instrumentation pattern (server-side `emitted_at_monotonic` + browser-side histogram).
- Read §6.3-§6.5 — confirmed the Option B drain pattern, connection-status-aware polling toggle, disconnection taxonomy, and reconnect resume protocol (including §6.5.2 snapshot handoff atomicity and the `Plotly.react` vs `extendTraces` distinction).
- Read §7 GAP-WS-01 through GAP-WS-33 — mapped every GAP in the browser-side scope to this proposal's sections.
- Read §8 — confirmed the `dash_duo` + Playwright dual-tool strategy and the `FakeCascorServerHarness` fixture pattern.
- Read §9.3 (Phase B) and §9.10 (Phase I asset cache busting) — confirmed scope and file touches.
- Read §10 RISK-02, RISK-08, RISK-10, RISK-12 — mapped to FR-RISK-01 through FR-RISK-15.

### 8.2 Pass 2 corrections made

After the initial draft, I re-read it and made the following corrections:

1. **Added §3.2.5 on ring buffer enforcement in the handler vs drain callback**. The first draft implied the cap could live in either place. RISK-12 (background tab throttling) makes this a real correctness issue, not a style preference. The cap MUST be in the handler.

2. **Clarified the dummy output pattern in §3.3.4**. The first draft showed the clientside callback with `Output("metrics-panel-figure-signal", "data")` without explaining why. Future readers would be confused.

3. **Added §3.3.5 on `uirevision`**. The first draft did not mention this. It is a one-line fix but a real correctness issue for the snapshot-replacement path.

4. **Rewrote §3.3.3 rAF coalescing**. The first draft said rAF coalescing ships with Phase B. Second pass surfaced that it introduces a double-render risk with the drain callback and is not strictly necessary at the 100 ms drain rate. Moved to "scaffold disabled" in §3.3.3 and added as disagreement #1 in §7.

5. **Expanded §3.4.2 with the 1 Hz fallback polling rate**. First draft just toggled polling off; second pass noticed that during disconnect windows 100 Hz polling is still pathological. Added as disagreement #2 in §7.

6. **Deferred NetworkVisualizer to Phase B+1 optionally**. First draft had it in scope; second pass noted it uses cytoscape, not Plotly, and `extendTraces` does not apply. Added as disagreement #3 in §7 and as step 16 in §4 with "lower priority" marker.

7. **Added §3.6 on the dual format wire test**. First draft did not mention this. RISK-01 (dual format removal) is a documented risk and having a Phase B wire-level regression test (not just the Phase H Python test) protects against the whole stack.

8. **Added AC-17 on bandwidth measurement**. First draft's acceptance criteria focused on correctness; I realized the P0 motivator (~3 MB/s elimination) should have a quantitative acceptance criterion, not just a correctness one. Added AC-17 measuring bytes fetched.

9. **Added AC-19 and AC-20 grep-based assertions**. Cheap belt-and-suspenders checks that protect against accidental regression from a partial revert or merge conflict. These are the kind of tests that catch "we deleted the dead code, then a rebase brought it back."

10. **Flagged latency instrumentation (GAP-WS-24) as having a server-side dependency**. First draft put the whole GAP-WS-24 in scope; second pass noted the `/api/ws_latency` endpoint belongs to a backend agent. Clarified in disagreement #6.

11. **Added the `seq` monotonicity check to `assets/websocket_client.js` cleanup (§3.5.1 item 6)**. First draft had the `seq` tracking for replay but not the monotonicity check. Second pass realized out-of-order `seq` is a latent server bug and should be logged.

12. **Fixed internal inconsistency between §3.2.1 JS skeleton and §3.2 narrative**. The first draft said "Exposes no new JS globals" but then exposed `window._juniperWsDrain` in the skeleton. Rewritten to explicitly acknowledge the single intentional global, with rationale.

13. **Fixed the §3.4.1 connection-status drain callback**. First draft's JS body returned the status on every non-null peek, contradicting the surrounding prose which claimed it emitted only on change. Rewrote the callback body to compare against `State("ws-connection-status", "data")` and `no_update` when neither `connected` nor `reason` has changed. This is the only place the first draft's code and prose directly contradicted each other.

### 8.3 Uncertainties and open items

- **Current Dash version in canopy**: I did not verify whether `juniper-canopy` pins Dash >= 2.18 (required for Option A `set_props`). Option B does not require it, so this is not blocking, but the PR description should check and note it.
- **Current Plotly.js version**: `extendTraces(maxPoints)` signature differs between Plotly 1.x and 2.x. I am assuming Plotly 2.x. The PR should verify by grepping `juniper-canopy` for `plotly` in requirements files.
- **Whether `NetworkVisualizer` uses cytoscape or Plotly**: I stated cytoscape based on my reading of §5.2 ("NetworkVisualizer (cytoscape graph)"). If it actually uses Plotly, my disagreement #3 is wrong and NetworkVisualizer does belong in Phase B.
- **Load-order guarantees for `assets/*.js`**: I stated Dash loads `assets/` files alphabetically. This is documented but versioned; for Dash 3.x the behavior may differ. The PR should test load order explicitly.
- **Whether the `server_instance_id` field has landed in cascor**: GAP-WS-13 is server-agent territory. This proposal's §3.5.1 item 5 assumes it exists. If it slips, the browser-side resume protocol must gracefully no-op when the field is absent (and falls back to full snapshot refresh). The JS client handles this via `if (!serverInstanceId) fallbackToSnapshot()`.
- **Whether the canopy `/ws/training` endpoint already forwards the `seq` field**: the canopy adapter's `start_metrics_relay()` at `cascor_service_adapter.py:199` normalizes messages; I am not sure whether it preserves unknown envelope fields. If not, Phase B must either preserve them (trivial `dict` copy) or add them in the canopy adapter.
- **The `fast-update-interval` cadence**: I am assuming 100 ms based on §1.1. If the actual value is different, the drain callback math needs adjustment. Check `dashboard_manager.py:1197`.

### 8.4 Items I chose not to cover despite being in the "browser performance" lane

- **Service Workers** for offline dashboard resilience. Out of scope; the architecture doc does not mention them and they would add significant complexity.
- **WebAssembly Plotly backend**: Plotly's WASM-accelerated renderer. Possibly faster for very large traces, but adds deployment complexity and is not mentioned in the source doc.
- **Shared Web Workers for the WebSocket client**: multiple dashboard tabs could share a single underlying WebSocket via `SharedWorker`, halving the cascor connection count. Interesting but out of scope; architecture doc does not call for it and GAP-WS-07 (backpressure) is a different fix for the same underlying concern.
- **IndexedDB or localStorage-backed metrics history**: would allow resuming a dashboard session across browser restarts. Out of scope; the §6.5 `localStorage` usage is only for `last_seq` and `server_instance_id` tracking, not for metrics history.
- **Tabular virtualization in candidate list views**: not a chart, not in the primary hot path, not mentioned in §5.

### 8.5 Self-confidence assessment

- **High confidence** in §3.2 (Option B drain pattern), §3.3 (`extendTraces`), §3.4 (polling toggle), §3.5 (dead code removal). These are direct applications of the source doc's recommendations with file-level specifics.
- **Medium confidence** in §3.3.3 (rAF coalescing scaffold). I reversed course during self-audit; the final recommendation to ship disabled is defensible but the source doc implies it should ship enabled. Disagreement #1.
- **Medium confidence** in the `metrics-panel-figure-signal` dummy output pattern. This is a standard Dash idiom but I have not verified it compiles against canopy's current Dash version.
- **Lower confidence** in the exact file-line references. Line numbers against `origin/main` at 2026-04-10 are likely stale by the time this proposal is consolidated; the PR should re-ground against current main.
- **Lower confidence** in the `FakeCascorServerHarness` fixture migration path. The source doc §8.5 says "the existing fake is in-process — extend it to a real FastAPI server harness" but the details of how the existing `FakeCascorTrainingStream` maps to a FastAPI route are not spelled out. Phase B's test fixture work will need to figure this out during implementation.

### 8.6 Items to coordinate with other sub-agents

- **Security agent (Phase B-pre)**: the browser-side JS must know whether CSRF-in-first-frame is required. My cleanup of `assets/websocket_client.js` (§3.5.1) adds `server_instance_id` tracking; the security agent's work adds CSRF token tracking. Both should land in the same PR if possible, or coordinate the merge order.
- **Cascor server agent (GAP-WS-13 seq)**: the browser's `seq` monotonicity check and the `_lastSeq` ring depend on cascor emitting `seq`. If cascor lags, my JS client handles it gracefully (assumes `seq=0`) but the reconnect test will be a partial skip.
- **SDK agent (Phase A)**: no direct dependency. The browser never imports `juniper-cascor-client`.
- **Adapter/Phase C agent**: Phase C uses the browser-side WebSocket wiring from Phase B to drive `set_params` slider handlers. The slider click handler needs to call `window.cascorControlWS.send({command: "set_params", params: ...})`. That JS wiring is trivial once Phase B's `cascorControlWS` cleanup is done; the adapter agent can consume it directly.
- **Frame budget / latency instrumentation**: my browser-side emitter POSTs to `/api/ws_latency`. The backend owner of that endpoint must be confirmed. If no one owns it, gate the POST behind a feature flag so Phase B can ship without waiting.

### 8.7 Final line count target

This proposal targets 600-1500 lines. Current estimate after the pass-2 revisions: ~1000-1200 lines including self-audit. Within the target envelope.
