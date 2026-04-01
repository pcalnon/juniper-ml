# Network Topology Display — Comprehensive Analysis and Fix Plan

**Date**: 2026-03-31
**Author**: Claude Code (Principal Engineer)
**Status**: ANALYSIS COMPLETE — READY FOR IMPLEMENTATION
**Scope**: juniper-canopy, juniper-cascor, juniper-cascor-client

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Document Audit — Prior Analysis Status](#2-document-audit--prior-analysis-status)
3. [Outstanding Issues — Not Yet Corrected](#3-outstanding-issues--not-yet-corrected)
4. [Issue OI-1: Topology Store Blanked on Transient Errors](#4-issue-oi-1-topology-store-blanked-on-transient-errors)
5. [Issue OI-2: WebSocket Topology Push Not Consumed by Dash](#5-issue-oi-2-websocket-topology-push-not-consumed-by-dash)
6. [Issue OI-3: Demo Backend Missing Cascade Connections](#6-issue-oi-3-demo-backend-missing-cascade-connections)
7. [Issue OI-4: Silent Exception Swallowing in extract_network_topology](#7-issue-oi-4-silent-exception-swallowing-in-extract_network_topology)
8. [Issue OI-5: Initial Sync Topology Not Pushed to Dash Store](#8-issue-oi-5-initial-sync-topology-not-pushed-to-dash-store)
9. [Issue OI-6: Narrow Exception Handling in Adapter Methods](#9-issue-oi-6-narrow-exception-handling-in-adapter-methods)
10. [Feature OF-1: Weight-Centric Topology View Toggle](#10-feature-of-1-weight-centric-topology-view-toggle)
11. [Development Plan — Phased Implementation](#11-development-plan--phased-implementation)
12. [Risk Assessment](#12-risk-assessment)
13. [Testing Strategy](#13-testing-strategy)
14. [Appendix A: Document Audit Cross-Reference](#appendix-a-document-audit-cross-reference)
15. [Appendix B: Full Data Flow Diagram](#appendix-b-full-data-flow-diagram)

---

## 1. Executive Summary

This document presents a comprehensive analysis of the network topology display subsystem in juniper-canopy, cross-referenced against 14 prior analysis documents and validated against the current codebase state (2026-03-31).

**Primary finding**: The topology display going blank after hidden units are added is caused by a **compound failure** involving:

1. The topology REST poll handler returning `{}` on error/503, which the visualizer interprets as "no topology" and renders blank (OI-1)
2. The WebSocket topology push from `cascade_add` being broadcast but never consumed by the Dash layer (OI-2)
3. Transient 503 responses during the brief window when CasCor is adding a hidden unit and reorganizing weights

**Secondary findings**: 4 additional code quality issues and 1 feature gap (weight-centric topology toggle).

### Issue Summary Table

| ID | Severity | Category | Description | Repo |
|----|----------|----------|-------------|------|
| **OI-1** | **HIGH** | Bug | Topology store returns `{}` on error, blanking display | juniper-canopy |
| **OI-2** | **HIGH** | Bug | WebSocket topology push not wired to Dash store | juniper-canopy |
| **OI-3** | MEDIUM | Bug | Demo backend omits hidden-to-hidden cascade connections | juniper-canopy |
| **OI-4** | MEDIUM | Quality | `extract_network_topology` swallows exceptions silently | juniper-canopy |
| **OI-5** | LOW | Quality | Initial sync topology never pushed to Dash store | juniper-canopy |
| **OI-6** | LOW | Quality | Several adapter methods catch only `JuniperCascorClientError` | juniper-canopy |
| **OF-1** | MEDIUM | Feature | Weight-centric topology view toggle not implemented | juniper-canopy |

### Additional Findings from CasCor Validation

1. **`create_topology_message()` is dead code in juniper-cascor** — The message builder exists in `api/websocket/messages.py` (line 35) and is exported in `__init__.py`, but no production code path ever calls it. CasCor only sends `cascade_add` event messages (with event metadata, no topology data). The Canopy adapter's `start_metrics_relay()` reacts to `cascade_add` by fetching topology via REST and broadcasting it locally — this is the only topology push path.

2. **`cascade_add` correlation is hardcoded to 0.0** — At `manager.py` line 379, the monitoring hook passes `correlation=0.0` to `on_cascade_add()` rather than the actual best candidate correlation. The real correlation is computed inside `grow_network()` but is not surfaced through the hook. This is a minor data quality issue (cosmetic) — does not affect topology display.

3. **`cascade_add` events are batch-emitted after `grow_network()` returns** — Not emitted in real-time as each unit is added. In practice `grow_network()` typically adds one unit per invocation so this is rarely observable.

---

## 2. Document Audit — Prior Analysis Status

### 2.1 Documents in `notes/development/`

| Document | Focus | Issues Identified | Current Status |
|----------|-------|-------------------|----------------|
| DATASET_DISPLAY_BUG_ANALYSIS.md | Dataset tab blank | RC-1 stale install, RC-2 FakeClient, CF-1..CF-3 | **FIXED** — `get_dataset_data()` added to client (6ed0fda), FakeClient (be17329), version bumped to 0.3.0 (09adb16), `hasattr` guard + broad exception in adapter (line 707) |
| DATASET_DISPLAY_BUG_ANALYSIS-FINAL.md | Unified dataset analysis | Same + CF-4..CF-6 | **FIXED** — same as above |
| DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md | 5-phase fix plan | Implementation detail | **PARTIALLY FIXED** — Phases 1-3 applied. Phase 5 (response.ok) partially applied. Stale worktree cleanup status unknown |
| DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN-FINAL.md | 7-phase unified plan | Implementation detail | **PARTIALLY FIXED** — same as above |
| DATASET_DISPLAY_FAILURE_ANALYSIS.md | Concise RCA | Same 3 root causes | **FIXED** |
| DATASET_DISPLAY_FIX_PLAN.md | Action-oriented plan | Same with code snippets | **PARTIALLY FIXED** |

**Residual items from dataset display bug work:**

- `_update_topology_store_handler` returns `{}` instead of `dash.no_update` on error — **NOT FIXED** (OI-1)
- Stale worktree cleanup — status unknown

### 2.2 Documents in `notes/`

| Document | Focus | Status |
|----------|-------|--------|
| CANOPY_DASHBOARD_DISPLAY_FIXES.md | 3 display issues (metrics, dataset, topology) | Issue 3 (output weights transposition): **FIXED** (committed in adapter). Issues 1-2: **FIXED** per CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md |
| DASHBOARD_AUGMENTATION_PLAN.md | Integrated augmentation (Tasks 1-3) | Task 3 (layer assignment): **FIXED** — uses 0/1/2 scheme. Tasks 1A-1E: **PARTIALLY IMPLEMENTED** |
| INTEGRATED_DASHBOARD_PLAN.md | Unified specification | Task 3 (layer values): **FIXED**. Task 4 (test failures): **FIXED** per REMAINING_ISSUES_REMEDIATION_PLAN.md |
| FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md | 20 connectivity issues | **ALL IMPLEMENTED** (P5-RC-01 through P5-RC-18) per document status |
| CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md | Training state broadcast | **ALL PHASES APPLIED** — `_broadcast_training_state()` added to CasCor, candidate pool status derived in adapter |
| CONVERGENCE_UI_FIX_PLAN.md | Convergence slider controls | **FIXED** (commits c8f2740, e11b100, PR #34) |
| CANOPY_DEFERRED_AND_BACKLOG_PLAN.md | 6-sprint backlog | Sprints 1-6: **COMPLETE** |
| REMAINING_ISSUES_REMEDIATION_PLAN.md | 5 work units post-dark-mode | All 5 work units: **COMPLETE** |

---

## 3. Outstanding Issues — Not Yet Corrected

The following issues were identified through cross-referencing all prior documents against the current codebase. Issues are ordered by severity.

---

## 4. Issue OI-1: Topology Store Blanked on Transient Errors

### Severity: HIGH

### Root Cause

`_update_topology_store_handler()` in `dashboard_manager.py` returns `{}` when the REST poll fails, instead of `dash.no_update`. This empty dict flows into the NetworkVisualizer callback where the guard `topology_data.get("input_units", 0) == 0` evaluates to `True`, rendering an empty graph.

### Evidence

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

```python
# Lines 1944-1961
def _update_topology_store_handler(self, n=None, active_tab=None):
    if active_tab != "topology":
        return dash.no_update
    try:
        url = self._api_url("/api/topology")
        response = requests.get(url, timeout=DashboardConstants.API_TIMEOUT_SECONDS)
        if not response.ok:
            self.logger.warning(f"Topology API returned {response.status_code}")
            return {}          # <-- BUG: overwrites store with empty dict
        topology = response.json()
        return topology
    except Exception as e:
        self.logger.warning(f"Failed to fetch topology from API: {type(e).__name__}: {e}")
        return {}              # <-- BUG: same issue
```

**File**: `juniper-canopy/src/frontend/components/network_visualizer.py`

```python
# Line 352
if not topology_data or topology_data.get("input_units", 0) == 0:
    empty_fig = self._create_empty_graph(theme, view_mode=view_mode)
    return empty_fig, "0", "0", "0", "0", None, None
```

### Why This Causes the Blank After Hidden Unit Addition

When CasCor adds a hidden unit via `grow_network()`, there is a brief transient window where the network state is being reorganized (output weights resized, new unit installed). If the Canopy REST poll hits `/api/topology` during this window and receives a 503 (or timeout), the handler returns `{}`, which blanks the topology display. The display stays blank until the next successful 5-second poll cycle while the topology tab is active.

**Contrast with other handlers:**

- `_update_dataset_store_handler` (line 1974): Returns `None` on error — equally problematic
- `_update_boundary_store_handler` (line 1995): Returns `None` on error — same issue
- `_update_metrics_store_handler` (line 1922): Returns `[]` on error — causes metrics to appear empty

### Fix Approaches

#### Approach A: Return `dash.no_update` on error (RECOMMENDED)

**Strengths**: Minimal change, preserves last known good state, consistent with Dash conventions
**Weaknesses**: None significant — this is the intended Dash pattern
**Risk**: Low — `dash.no_update` is a Dash-native sentinel

```python
# dashboard_manager.py — _update_topology_store_handler
def _update_topology_store_handler(self, n=None, active_tab=None):
    if active_tab != "topology":
        return dash.no_update
    try:
        url = self._api_url("/api/topology")
        response = requests.get(url, timeout=DashboardConstants.API_TIMEOUT_SECONDS)
        if not response.ok:
            self.logger.warning(f"Topology API returned {response.status_code}")
            return dash.no_update  # Preserve last known good topology
        topology = response.json()
        return topology
    except Exception as e:
        self.logger.warning(f"Failed to fetch topology from API: {type(e).__name__}: {e}")
        return dash.no_update      # Preserve last known good topology
```

**Affected files**: `juniper-canopy/src/frontend/dashboard_manager.py` (lines 1955, 1961)

#### Approach B: Apply same fix to ALL store handlers

Extend Approach A to also fix `_update_dataset_store_handler`, `_update_boundary_store_handler`, and `_update_boundary_dataset_store_handler` which have the same pattern.

**Strengths**: Comprehensive fix, prevents the same class of bug across all tabs
**Weaknesses**: Slightly larger changeset
**Risk**: Low — same reasoning as Approach A

**Affected files**:

- `dashboard_manager.py` line 1955 (`{}` → `dash.no_update`)
- `dashboard_manager.py` line 1961 (`{}` → `dash.no_update`)
- `dashboard_manager.py` line 1974 (`None` → `dash.no_update`)
- `dashboard_manager.py` line 1980 (`None` → `dash.no_update`)
- `dashboard_manager.py` line 1995 (`None` → `dash.no_update`)
- `dashboard_manager.py` line 2001 (`None` → `dash.no_update`)
- `dashboard_manager.py` line 2014 (`None` → `dash.no_update`)
- `dashboard_manager.py` line 2018 (`None` → `dash.no_update`)

**Recommendation**: **Approach B** — fix all handlers for consistency.

---

## 5. Issue OI-2: WebSocket Topology Push Not Consumed by Dash

### Severity: HIGH

### Root Cause

When `cascade_add` is received via WebSocket from CasCor, the Canopy adapter in `start_metrics_relay()` reacts by making a REST call to CasCor's `/v1/network/topology` endpoint, transforms the result via `_transform_topology()`, and broadcasts it via Canopy's internal `websocket_manager.broadcast()`. This message reaches the browser's WebSocket client, but there is no Dash clientside callback or mechanism to pipe WebSocket-pushed topology data into the `network-visualizer-topology-store` dcc.Store.

Note: CasCor itself never broadcasts topology — `create_topology_message()` in CasCor's `messages.py` is dead code. The topology push is entirely Canopy-initiated.

The Dash topology store is updated **exclusively** by the slow REST poll (5000ms interval), and **only** when the topology tab is active.

### Evidence

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

```python
# Lines 227-233 — cascade_add handler broadcasts topology
if msg_type == "cascade_add":
    try:
        topology = self.extract_network_topology()
        if topology:
            await websocket_manager.broadcast({"type": "topology", "data": topology})
    except Exception as te:
        logger.debug(f"Failed to fetch topology after cascade_add: {te}")
```

The broadcast reaches the browser but is buffered without being consumed.

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

```python
# Lines 1207-1215 — topology store only updated by REST poll
@self.app.callback(
    Output("network-visualizer-topology-store", "data"),
    Input("slow-update-interval", "n_intervals"),
    Input("visualization-tabs", "active_tab"),
)
def update_topology_store(n, active_tab):
    return self._update_topology_store_handler(n=n, active_tab=active_tab)
```

### Consequence

- Topology updates after `cascade_add` are delayed by **up to 5 seconds**
- If the user is NOT on the topology tab, the update is skipped entirely until they switch tabs
- Combined with OI-1, if the first poll after `cascade_add` hits a transient 503, the display blanks

### Fix Approaches

#### Approach A: Add WebSocket-to-Store bridge via clientside callback (RECOMMENDED)

Create a clientside callback that monitors the WebSocket message buffer for `"topology"` messages and pushes them directly into the topology store.

**Strengths**: Near-real-time topology updates, no additional REST calls, leverages existing WebSocket infrastructure
**Weaknesses**: Adds client-side JavaScript complexity, requires a new hidden dcc.Store for the WebSocket buffer
**Risk**: Medium — requires coordinating JavaScript with Dash callback graph

**Important implementation note**: The codebase already has a working WebSocket-to-Dash bridge for metrics at `dashboard_manager.py` lines 1151-1181. It uses a `clientside_callback` that creates its own WebSocket connection (`window._juniper_ws`), buffers messages to `window._juniper_ws_buffer`, and returns `window.dash_clientside.no_update`. This is separate from the `CascorWebSocket` class in `assets/websocket_client.js` (`window.cascorWS`). The topology fix should follow this established pattern.

**WARNING**: Direct DOM manipulation (`setAttribute`) on a `dcc.Store` element will NOT trigger Dash callbacks — Dash stores are React-managed components. The fix MUST use the `clientside_callback` + `window` buffer pattern.

**Implementation outline:**

1. Add a hidden `ws-topology-buffer` dcc.Store in `dashboard_manager.py` layout (following the existing `ws-metrics-buffer` pattern at line 895)
2. Extend the existing `clientside_callback` WebSocket `onmessage` handler (lines 1162-1171) to also capture `type === "topology"` messages into `window._juniper_ws_topology_buffer`
3. Add a second `clientside_callback` that pipes the topology buffer into the `ws-topology-buffer` store
4. Modify the `update_topology_store` server-side callback to merge WebSocket and REST data

```python
# dashboard_manager.py — Additional layout component (same pattern as ws-metrics-buffer)
dcc.Store(id="ws-topology-buffer", data=None),

# dashboard_manager.py — Clientside callback to drain topology buffer
self.app.clientside_callback(
    """
    function(n) {
        if (window._juniper_ws_topology_buffer && window._juniper_ws_topology_buffer.length > 0) {
            var latest = window._juniper_ws_topology_buffer[window._juniper_ws_topology_buffer.length - 1];
            window._juniper_ws_topology_buffer = [];
            return latest;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("ws-topology-buffer", "data"),
    Input("fast-update-interval", "n_intervals"),
)

# dashboard_manager.py — Extend existing WS onmessage to capture topology
# In the existing clientside_callback (lines 1162-1171), add:
#   if (msg.type === "topology" && msg.data) {
#       window._juniper_ws_topology_buffer = window._juniper_ws_topology_buffer || [];
#       window._juniper_ws_topology_buffer.push(msg.data);
#   }

# dashboard_manager.py — Merged topology callback
@self.app.callback(
    Output("network-visualizer-topology-store", "data"),
    Input("slow-update-interval", "n_intervals"),
    Input("ws-topology-buffer", "data"),
    Input("visualization-tabs", "active_tab"),
)
def update_topology_store(n, ws_topology, active_tab):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"] if ctx.triggered else ""

    if "ws-topology-buffer" in trigger and ws_topology:
        return ws_topology  # WebSocket push takes priority

    if active_tab != "topology":
        return dash.no_update

    return self._update_topology_store_handler(n=n, active_tab=active_tab)
```

**Affected files**:

- `juniper-canopy/src/frontend/dashboard_manager.py` (layout + clientside callback + server callback modification)
- `juniper-canopy/src/frontend/assets/websocket_client.js` (optional — only if extending CascorWebSocket rather than the existing clientside_callback WS)

#### Approach B: Reduce REST poll interval for topology tab

Switch topology from `slow-update-interval` (5s) to `fast-update-interval` when the topology tab is active.

**Strengths**: Simple, no JavaScript changes
**Weaknesses**: Increased API load, still not real-time, still susceptible to the tab-inactive gap
**Risk**: Low — straightforward callback change

```python
# dashboard_manager.py — Change Input from slow to fast
@self.app.callback(
    Output("network-visualizer-topology-store", "data"),
    Input("fast-update-interval", "n_intervals"),  # Changed from slow
    Input("visualization-tabs", "active_tab"),
)
```

#### Approach C: Hybrid — WebSocket push + REST fallback with `dash.no_update`

Combine Approach A (WebSocket push) with OI-1 fix (`dash.no_update` on error) for maximum resilience.

**Strengths**: Best of both worlds — real-time updates AND graceful degradation
**Weaknesses**: Largest changeset
**Risk**: Medium — same as Approach A

**Recommendation**: **Approach C** (OI-1 Approach B + OI-2 Approach A combined) — real-time WebSocket updates with graceful REST fallback.

---

## 6. Issue OI-3: Demo Backend Missing Cascade Connections

### Severity: MEDIUM

### Root Cause

`demo_backend.py:get_network_topology()` only creates input-to-hidden connections. It does not create hidden-to-hidden cascade connections that are the defining feature of CasCor architecture.

### Evidence

**File**: `juniper-canopy/src/backend/demo_backend.py`

```python
# Lines 142-148 — Only input-to-hidden connections created
for i, unit in enumerate(network.hidden_units):
    nodes.append({"id": f"hidden_{i}", "type": "hidden", "layer": 1})
    # Connections from inputs to hidden
    for j in range(network.input_size):
        weight = unit["weights"][j].item() if j < len(unit["weights"]) else 0.0
        connections.append({"from": f"input_{j}", "to": f"hidden_{i}", "weight": weight})
    # ^^^ MISSING: Cascade connections from prior hidden units
```

**Contrast with service adapter** (`cascor_service_adapter.py` lines 617-621):

```python
# Cascade connections from prior hidden units
for prior_h in range(h):
    if w_idx < len(weights):
        connections.append({"from": f"hidden_{prior_h}", "to": f"hidden_{h}", ...})
```

### Consequence

In demo mode, networks with 2+ hidden units display an **incomplete topology** — missing the signature cascade connections between hidden units. The visualization appears as a standard feedforward network rather than a cascade correlation network.

### Fix Approaches

#### Approach A: Add cascade connections to demo backend (RECOMMENDED)

**Strengths**: Fixes demo mode topology to match CasCor architecture
**Weaknesses**: Requires understanding demo network's weight structure
**Risk**: Low — additive change only

```python
# demo_backend.py — Replace lines 142-148
for i, unit in enumerate(network.hidden_units):
    nodes.append({"id": f"hidden_{i}", "type": "hidden", "layer": 1})
    weights = unit["weights"]
    w_idx = 0
    # Connections from inputs to hidden
    for j in range(network.input_size):
        weight = weights[w_idx].item() if w_idx < len(weights) else 0.0
        connections.append({"from": f"input_{j}", "to": f"hidden_{i}", "weight": weight})
        w_idx += 1
    # Cascade connections from prior hidden units
    for prior_h in range(i):
        weight = weights[w_idx].item() if w_idx < len(weights) else 0.0
        connections.append({"from": f"hidden_{prior_h}", "to": f"hidden_{i}", "weight": weight})
        w_idx += 1
```

**Affected files**: `juniper-canopy/src/backend/demo_backend.py` (lines 142-148)

#### Approach B: Refactor demo backend to use `_transform_topology`

Have the demo backend produce a weight-oriented topology dict and feed it through `_transform_topology()`, reusing the same transformation logic as the service adapter.

**Strengths**: Single source of truth for topology transformation, guaranteed consistency
**Weaknesses**: Requires demo backend to know CasCor's raw topology format; tighter coupling
**Risk**: Medium — changes the demo backend's data flow

**Recommendation**: **Approach A** — direct fix is simpler and lower risk.

---

## 7. Issue OI-4: Silent Exception Swallowing in extract_network_topology

### Severity: MEDIUM

### Root Cause

`extract_network_topology()` catches all exceptions with a bare `except Exception` and returns `None` with no logging. Any bug in `_transform_topology()` (e.g., unexpected data format from CasCor) is completely invisible.

### Evidence

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

```python
# Lines 665-676
def extract_network_topology(self) -> Optional[Dict[str, Any]]:
    try:
        raw = self._cb.call(
            lambda: self._unwrap_response(self._client.get_topology()),
            fallback=lambda: None,
        )
        if isinstance(raw, dict):
            return self._transform_topology(raw)
        result: Optional[Dict[str, Any]] = raw
        return result
    except Exception:       # <-- No logging at all
        return None
```

### Fix

Add warning-level logging to the exception handler:

```python
except Exception as e:
    logger.warning("Failed to extract network topology: %s: %s", type(e).__name__, e)
    return None
```

**Affected files**: `juniper-canopy/src/backend/cascor_service_adapter.py` (line 675)

---

## 8. Issue OI-5: Initial Sync Topology Not Pushed to Dash Store

### Severity: LOW

### Root Cause

During `CascorStateSync.sync()`, the topology is fetched and transformed correctly into `SyncedState.topology`. However, in `main.py` where the synced state is applied, only training status/epoch/params are pushed to the app state — the synced topology is never written to the Dash topology store.

### Evidence

**File**: `juniper-canopy/src/backend/state_sync.py` (lines 125-135) — correctly fetches and transforms topology.

**File**: `juniper-canopy/src/main.py` (lines 193-207) — applies synced state but omits topology.

### Consequence

On dashboard startup (or reconnection), the topology tab will show blank until the first successful REST poll (up to 5 seconds) while the topology tab is active.

### Fix

After applying synced training state, also push synced topology to the topology store's initial data or expose it via the `/api/topology` internal cache.

**Recommendation**: LOW PRIORITY — the 5-second poll will pick it up. Can be addressed as part of OI-2 (WebSocket push) which provides a more comprehensive solution.

---

## 9. Issue OI-6: Narrow Exception Handling in Adapter Methods

### Severity: LOW

### Root Cause

Several `CascorServiceAdapter` methods catch only `JuniperCascorClientError`, which would miss `AttributeError`, `TypeError`, or other unexpected exceptions. This was the original vector for the dataset display bug (RC-2).

### Evidence

Methods catching only `JuniperCascorClientError` (not yet broadened):

| Method | Lines | Risk |
|--------|-------|------|
| `create_network` | 350 | Low — hard to hit |
| `start_training_background` | 362 | Low |
| `is_training_in_progress` | 376 | Low |
| `request_training_stop` | 383 | Low |
| `pause_training` | 391 | Low |
| `resume_training` | 399 | Low |
| `reset_training` | 408 | Low |
| `get_decision_boundary` | 780 | Medium — complex data |
| `get_snapshots` | 805 | Low |
| `load_snapshot` | 821 | Low |

### Fix

The `get_dataset_data()` method (line 733) already demonstrates the correct pattern: `except Exception as e` with a warning log. Apply the same pattern to the methods listed above that handle data transformation (especially `get_decision_boundary`).

**Recommendation**: LOW PRIORITY — the `_cb.call()` circuit breaker wrapping in most methods already provides a layer of protection. Focus on `get_decision_boundary` which does data transformation.

---

## 10. Feature OF-1: Weight-Centric Topology View Toggle

### Description

The current topology visualization is exclusively **node-centric** — showing nodes and their connections as a graph. A **weight-centric** view would display the raw weight arrays from CasCor, showing the actual numerical structure of the network.

### Design

#### Toggle Control

Add a `dbc.RadioItems` or `dbc.ButtonGroup` toggle to the NetworkVisualizer's control panel:

- **Node Graph** (default): Current node-centric Plotly graph visualization
- **Weight Matrix**: Heatmap visualization showing raw weight arrays

#### Weight-Centric View Content

Display a weight heatmap grid showing:

1. **Hidden unit weights**: For each hidden unit h, a heatmap row showing its input weights (from all inputs + prior hidden units)
2. **Output weights**: A heatmap matrix showing the full output weight matrix (input_size + num_hidden × output_size)
3. **Bias values**: Sidebar annotation for each node's bias

This requires fetching the raw (pre-transformation) topology from CasCor, which includes the actual weight arrays.

### Fix Approaches

#### Approach A: Dual-store architecture (RECOMMENDED)

Maintain two topology stores:

- `network-visualizer-topology-store` (existing): Graph-oriented format for node view
- `network-visualizer-raw-topology-store` (new): Raw weight-oriented format for weight view

The REST endpoint `/api/topology` would need a `?format=raw` query parameter, or a separate `/api/topology/raw` endpoint.

**Strengths**: Clean separation of concerns, each view consumes its own data format
**Weaknesses**: Additional REST call for raw format, two stores to maintain
**Risk**: Low — Canopy-only changes (CasCor already returns raw format)

**Key insight**: CasCor's `/v1/network/topology` endpoint already returns the **raw weight-oriented format** (via `lifecycle.get_topology()`). The graph-oriented transformation happens entirely in Canopy's `_transform_topology()`. Therefore, **no CasCor changes are needed** — only a Canopy adapter method that skips transformation.

**Implementation outline:**

1. **Canopy adapter**: Add `get_raw_topology()` method that fetches from the same CasCor endpoint but returns the raw dict without calling `_transform_topology()`
2. **Canopy main.py**: Add `/api/topology/raw` endpoint that calls `backend.get_raw_topology()`
3. **Dashboard manager**: Add `network-visualizer-raw-topology-store` with same poll interval (only fetched when weight view is active)
4. **NetworkVisualizer**: Add toggle control and conditional rendering (graph or heatmap)

**Affected files**:

- `juniper-canopy/src/backend/cascor_service_adapter.py` (new `get_raw_topology()` method)
- `juniper-canopy/src/main.py` (new `/api/topology/raw` endpoint)
- `juniper-canopy/src/frontend/dashboard_manager.py` (new store + callback)
- `juniper-canopy/src/frontend/components/network_visualizer.py` (toggle + heatmap rendering)

#### Approach B: Transform graph-oriented back to weight view on the fly

Use the existing graph-oriented store and reconstruct the weight matrix view from the connections list.

**Strengths**: No new data stores or endpoints, works with existing infrastructure
**Weaknesses**: Lossy — the graph-oriented format doesn't preserve the exact raw matrix layout; reconstructed matrices may differ from actual CasCor internal state
**Risk**: Low — purely frontend change, but lower fidelity

#### Approach C: Always fetch raw topology, transform client-side

Always store the raw weight-oriented topology and transform to graph-oriented format in a clientside callback or in the visualizer callback itself.

**Strengths**: Single source of truth, both views derived from the same data
**Weaknesses**: Shifts transformation logic to the frontend, potentially slower
**Risk**: Medium — duplicates `_transform_topology()` logic (or moves it entirely)

**Recommendation**: **Approach A** — cleanest separation, highest fidelity for the weight view.

#### Weight Heatmap Rendering (all approaches)

```python
def _create_weight_heatmap(self, raw_topology: dict, theme: str) -> go.Figure:
    """Create a weight matrix heatmap from raw CasCor topology."""
    hidden_units = raw_topology.get("hidden_units", [])
    output_weights = raw_topology.get("output_weights", [])
    input_size = raw_topology.get("input_size", 0)

    fig = make_subplots(
        rows=1 + len(hidden_units), cols=1,
        subplot_titles=[f"Hidden Unit {i} Weights" for i in range(len(hidden_units))]
                       + ["Output Weights"],
        vertical_spacing=0.05,
    )

    # Hidden unit weight vectors as single-row heatmaps
    for i, unit in enumerate(hidden_units):
        weights = unit.get("weights", [])
        labels = [f"in_{j}" for j in range(input_size)] + [f"h_{j}" for j in range(i)]
        fig.add_trace(
            go.Heatmap(z=[weights], x=labels, colorscale="RdBu", zmid=0),
            row=i + 1, col=1,
        )

    # Output weight matrix as 2D heatmap
    if output_weights:
        row_labels = [f"in_{j}" for j in range(input_size)] + [f"h_{j}" for j in range(len(hidden_units))]
        fig.add_trace(
            go.Heatmap(z=output_weights, y=row_labels, colorscale="RdBu", zmid=0),
            row=len(hidden_units) + 1, col=1,
        )

    return fig
```

---

## 11. Development Plan — Phased Implementation

### Phase 1: Critical Bug Fixes (OI-1 + OI-4)

**Priority**: CRITICAL
**Effort**: ~30 minutes
**Repos**: juniper-canopy only
**Dependencies**: None

| Step | Task | File | Lines |
|------|------|------|-------|
| 1.1 | Replace `return {}` / `return None` with `dash.no_update` in all store handlers on error | `dashboard_manager.py` | 1955, 1961, 1974, 1980, 1995, 2001, 2014, 2018 |
| 1.2 | Add logging to `extract_network_topology` exception handler | `cascor_service_adapter.py` | 675 |
| 1.3 | Run unit tests: `pytest tests/unit/ -q --timeout=30` | — | — |

### Phase 2: Demo Backend Cascade Connections (OI-3)

**Priority**: HIGH
**Effort**: ~30 minutes
**Repos**: juniper-canopy only
**Dependencies**: None (can run in parallel with Phase 1)

| Step | Task | File | Lines |
|------|------|------|-------|
| 2.1 | Add hidden-to-hidden cascade connections in `get_network_topology()` | `demo_backend.py` | 142-148 |
| 2.2 | Add unit test for demo mode cascade connections with 2+ hidden units | `tests/unit/backend/test_demo_backend.py` | New |
| 2.3 | Run unit tests: `pytest tests/unit/backend/ -q --timeout=30` | — | — |

### Phase 3: WebSocket Topology Push (OI-2)

**Priority**: HIGH
**Effort**: ~2-3 hours
**Repos**: juniper-canopy only
**Dependencies**: Phase 1 (OI-1 fix must be in place for correct fallback behavior)

| Step | Task | File | Lines |
|------|------|------|-------|
| 3.1 | Add `ws-topology-buffer` dcc.Store to layout | `dashboard_manager.py` | Layout section |
| 3.2 | Add topology message handler to WebSocket client JS | `static/js/websocket_client.js` | Message handler section |
| 3.3 | Modify `update_topology_store` callback to accept WebSocket input | `dashboard_manager.py` | Lines 1207-1215 |
| 3.4 | Add integration test for WebSocket topology push path | `tests/integration/` | New |
| 3.5 | End-to-end validation: start training, observe topology update latency | — | Manual |

### Phase 4: Weight-Centric Topology Toggle (OF-1)

**Priority**: MEDIUM
**Effort**: ~4-6 hours
**Repos**: juniper-canopy only (CasCor already returns raw weight-oriented format)

| Step | Task | File | Lines |
|------|------|------|-------|
| 4.1 | Add `get_raw_topology()` method to adapter (skips `_transform_topology()`) | `cascor_service_adapter.py` | New method |
| 4.2 | Add `/api/topology/raw` proxy endpoint in Canopy | `main.py` | New endpoint |
| 4.3 | Add `network-visualizer-raw-topology-store` + callback (lazy: only when weight view active) | `dashboard_manager.py` | Layout + callback |
| 4.4 | Add view toggle control (Node Graph / Weight Matrix) | `network_visualizer.py` | `get_layout()` |
| 4.5 | Implement `_create_weight_heatmap()` method | `network_visualizer.py` | New method |
| 4.6 | Modify `update_network_graph` callback to switch between views | `network_visualizer.py` | Callback |
| 4.7 | Add unit tests for weight heatmap rendering | `tests/unit/frontend/test_network_visualizer_*.py` | New |
| 4.8 | End-to-end validation with live CasCor service | — | Manual |

### Phase 5: Quality Improvements (OI-5, OI-6)

**Priority**: LOW
**Effort**: ~1 hour
**Repos**: juniper-canopy only
**Dependencies**: Phase 3 (OI-5 is partially addressed by WebSocket push)

| Step | Task | File | Lines |
|------|------|------|-------|
| 5.1 | Apply initial synced topology to Dash store (or defer to Phase 3 WebSocket) | `main.py` | Lines 193-207 |
| 5.2 | Broaden exception handling in `get_decision_boundary` | `cascor_service_adapter.py` | Line 780 |
| 5.3 | Run full test suite: `pytest tests/ -q --timeout=30` | — | — |

---

## 12. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `dash.no_update` causes stale data to persist indefinitely | Medium | Low | Stale data is only shown until next successful poll (5s max); log warnings make it visible |
| WebSocket topology push race condition with REST poll | Low | Medium | Use timestamp comparison — only accept newer data; REST always provides authoritative fallback |
| Weight heatmap performance with large networks | Medium | Low | Lazy-load raw topology only when weight view is active; cap rendering at configurable max units |
| Demo backend weight structure differs from service mode | Low | Medium | Validate weight dimensions in test; both modes are independently correct for their use case |
| Breaking existing topology tests | High | Low | Phase 1 changes are error-path only; existing tests exercise success paths |

---

## 13. Testing Strategy

### Phase 1 Tests

```python
# test_dashboard_manager.py — New test
class TestTopologyStoreErrorHandling:
    def test_topology_handler_returns_no_update_on_http_error(self, manager, mock_requests):
        """Failed REST poll must NOT overwrite topology store."""
        mock_requests.get.return_value = Mock(ok=False, status_code=503)
        result = manager._update_topology_store_handler(n=1, active_tab="topology")
        assert result is dash.no_update

    def test_topology_handler_returns_no_update_on_exception(self, manager, mock_requests):
        """Exception during REST poll must NOT overwrite topology store."""
        mock_requests.get.side_effect = requests.Timeout("timeout")
        result = manager._update_topology_store_handler(n=1, active_tab="topology")
        assert result is dash.no_update

    def test_topology_handler_returns_data_on_success(self, manager, mock_requests):
        """Successful REST poll must update topology store."""
        mock_requests.get.return_value = Mock(ok=True, json=lambda: {"input_units": 2})
        result = manager._update_topology_store_handler(n=1, active_tab="topology")
        assert result == {"input_units": 2}
```

### Phase 2 Tests

```python
# test_demo_backend.py — New test
class TestDemoBackendCascadeConnections:
    def test_multi_hidden_unit_cascade_connections(self, demo_backend):
        """Demo backend must produce hidden-to-hidden cascade connections."""
        # Setup: create network with 2+ hidden units
        topology = demo_backend.get_network_topology()

        # hidden_1 must have connection FROM hidden_0
        h1_sources = {c["from"] for c in topology["connections"] if c["to"] == "hidden_1"}
        assert "hidden_0" in h1_sources, "Missing cascade connection hidden_0 → hidden_1"
```

### Phase 3 Tests

```python
# test_websocket_topology_push.py — New integration test
class TestWebSocketTopologyPush:
    async def test_cascade_add_triggers_topology_broadcast(self, adapter, mock_ws_manager):
        """cascade_add WebSocket message must trigger topology broadcast."""
        # Simulate cascade_add message
        await adapter._handle_ws_message({"type": "cascade_add", "data": {...}})
        mock_ws_manager.broadcast.assert_called_once()
        broadcast_msg = mock_ws_manager.broadcast.call_args[0][0]
        assert broadcast_msg["type"] == "topology"
        assert "input_units" in broadcast_msg["data"]
```

---

## Appendix A: Document Audit Cross-Reference

### Issues Previously Identified and Now Resolved

| Original Issue | Document | Resolution |
|----------------|----------|------------|
| RC-1: Stale editable install | DATASET_DISPLAY_BUG_ANALYSIS.md | Fixed: `get_dataset_data()` added to client, version bumped to 0.3.0 |
| RC-2: Narrow exception in adapter | DATASET_DISPLAY_BUG_ANALYSIS.md | Fixed: `get_dataset_data()` now catches `Exception`, has `hasattr` guard |
| RC-3: Missing in FakeCascorClient | DATASET_DISPLAY_BUG_ANALYSIS-FINAL.md | Fixed: `get_dataset_data()` added to FakeCascorClient (be17329) |
| P5-RC-01: Metrics format mismatch | FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md | Fixed: all 20 issues resolved |
| P5-RC-02: Topology format mismatch | FINAL_CANOPY_CASCOR_CONNECTION_ANALYSIS.md | Fixed: `_transform_topology()` implemented with transposition |
| Output weights transposition | CANOPY_DASHBOARD_DISPLAY_FIXES.md Issue 3 | Fixed: transpose logic at adapter lines 627-629 |
| Layer assignment (0/1/2 scheme) | DASHBOARD_AUGMENTATION_PLAN.md Task 3 | Fixed: layers 0/1/2 in adapter lines 605, 609, 635 |
| Training state not broadcast | CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md | Fixed: `_broadcast_training_state()` added to CasCor |
| Convergence UI bugs B-5.1..B-5.4 | CONVERGENCE_UI_FIX_PLAN.md | Fixed: PR #34 |
| Pre-existing test failures | INTEGRATED_DASHBOARD_PLAN.md Task 4 | Fixed: REMAINING_ISSUES_REMEDIATION_PLAN.md |

### Issues Previously Identified and Still Outstanding

| Original Issue | Document | This Document |
|----------------|----------|---------------|
| response.ok returns bad default | DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN.md Phase 3/5 | OI-1 |
| Demo backend incomplete topology | (newly identified) | OI-3 |
| Silent exception swallowing | (newly identified) | OI-4 |
| Narrow exception in other methods | DATASET_DISPLAY_BUG_ANALYSIS-FINAL.md CF-6 | OI-6 |

---

## Appendix B: Full Data Flow Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │              juniper-cascor                    │
                    │                                                │
                    │  grow_network() → add_unit()                   │
                    │       │                                        │
                    │       ├─► TrainingMonitor.on_cascade_add()     │
                    │       │       └─► WebSocket: cascade_add       │◄── Event only
                    │       │           (no topology data)            │    (correlation=0.0)
                    │       │                                        │
                    │  GET /v1/network/topology                      │
                    │       └─► get_topology() → raw dict            │◄── Weight-oriented
                    │           (create_topology_message is DEAD CODE)│
                    └──────────┬───────────────────────────┬─────────┘
                               │ WebSocket                 │ REST
                    ┌──────────▼───────────────────────────▼─────────┐
                    │           juniper-canopy backend                │
                    │                                                 │
                    │  start_metrics_relay():                         │
                    │    cascade_add received                         │
                    │      └─► REST call to CasCor /v1/network/topo  │◄── Canopy-initiated
                    │          └─► _transform_topology()             │◄── Weight→Graph
                    │          └─► ws_manager.broadcast(topology)    │
                    │               ▼                                │
                    │          [OI-2: REACHES BROWSER BUT NOT DASH]  │
                    │                                                 │
                    │  GET /api/topology:                              │
                    │    backend.get_network_topology()                │
                    │    └─► extract_network_topology()                │
                    │        └─► _transform_topology()                │
                    │    return topology or 503                       │
                    └──────────────────────┬──────────────────────────┘
                                           │ REST (5s poll)
                    ┌──────────────────────▼──────────────────────────┐
                    │          juniper-canopy frontend                 │
                    │                                                  │
                    │  _update_topology_store_handler():                │
                    │    response.ok? → topology to Store               │
                    │    error?       → {} [OI-1: BLANKS DISPLAY]      │
                    │                                                  │
                    │  network-visualizer-topology-store                │
                    │    │                                             │
                    │    ▼                                             │
                    │  NetworkVisualizer.update_network_graph():        │
                    │    input_units == 0? → empty graph                │
                    │    else → _create_network_graph()                 │
                    │            └─► Plotly Figure                      │
                    └──────────────────────────────────────────────────┘
```

---

---

## Appendix C: Validation Results

All code references, line numbers, and proposed fixes in this document were validated by independent sub-agents.

### Code Reference Validation

**Result: 20/20 CORRECT**

Every line number, code snippet, and factual claim about the codebase was verified against the current source files. No shifted, wrong, or missing references found.

### Fix Logic Validation

| Issue | Verdict | Notes |
|-------|---------|-------|
| OI-1 | **VALID** | `dash.no_update` confirmed as correct Dash sentinel; already used 26 times in `dashboard_manager.py` |
| OI-2 | **VALID** (after correction) | Original JS `setAttribute` approach replaced with established `clientside_callback` + `window` buffer pattern matching existing metrics WebSocket bridge (lines 1151-1181). File path corrected from `static/js/` to `assets/` |
| OI-3 | **VALID** | Demo network weight structure confirmed in `demo_mode.py` line 204: hidden unit h has `input_size + h` weights, cascade weights start at index `input_size` |
| OF-1 | **VALID** (after correction) | CasCor's `/v1/network/topology` already returns raw weight-oriented format — Step 4.1 (new CasCor endpoint) removed. Plotly dependencies (`go.Heatmap`, `make_subplots`) confirmed available |

### CasCor-Side Validation

| Finding | Impact |
|---------|--------|
| `create_topology_message()` is dead code in CasCor | Confirms topology push is Canopy-initiated after `cascade_add` |
| `cascade_add` correlation hardcoded to 0.0 | Cosmetic — does not affect topology display |
| `cascade_add` events batch-emitted after `grow_network()` returns | No impact — typically one unit per invocation |
| `output_weights` shape confirmed as `(input_size + num_hidden, output_size)` | Matches `_transform_topology()` transpose logic |

---

*End of analysis document.*
