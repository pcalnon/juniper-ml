# Round 0 Proposal R0-04: SDK & set_params Control Path (Phase C)

**Specialization**: juniper-cascor-client SDK design, set_params WS contract, canopy adapter migration
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope

This proposal covers the **client-side** of the canopy to cascor parameter-control path:

1. A new WebSocket `set_params(params)` method on `juniper-cascor-client`, added to `CascorControlStream` (the class that already implements the `/ws/control` RPC pattern).
2. The request/ack wire contract for `set_params` as issued by the SDK, including request envelope, correlation ID handling, ack-timeout semantics, and mapped Python exceptions.
3. How the new SDK method coexists with the existing REST `update_params(params)` method on the synchronous `CascorClient` (they are different objects on different transports; neither replaces the other).
4. The canopy-side migration of `CascorServiceAdapter.apply_params(**params)` from a single-transport REST call to a per-key hot/cold splitter that dispatches hot params over WebSocket and cold params over REST.
5. The feature flag that gates the new behavior (`Settings.use_websocket_set_params=False`, default off) per Phase C's P2 rollout decision.
6. The fallback story for the three classes of adverse conditions: WebSocket disconnected, WebSocket reconnecting, WebSocket returning a server error.
7. Idempotency, duplicate suppression, and debouncing as they relate to the SDK surface.
8. Per-message latency instrumentation hooks required by §5.6 (Production Latency Measurement Plan).
9. Type-safety and validation on the SDK side before sending to cascor.
10. Acceptance criteria for Phase A (SDK) and Phase C (canopy adapter).

**Explicitly out of scope**:

- The cascor SERVER side: `_VALID_COMMANDS` whitelist, `control_stream.py:97-100` handler, broadcaster lock policy, replay buffer, `server_instance_id`, sequence numbers on broadcast. These belong to a sibling agent.
- Browser-side Plotly wiring, clientside callbacks, `window.cascorControlWS`, or `dcc.Store` plumbing. These also belong to a sibling agent.
- Security controls (M-SEC-01, M-SEC-02, M-SEC-03, M-SEC-04, M-SEC-05, M-SEC-06, M-SEC-07). This proposal **references Phase B-pre as a strict prerequisite** for any dashboard-triggered `set_params` path but does not design the controls themselves.
- Plans for moving the existing REST `/api/v1/training/params` endpoint. Per §9.5 Phase D discussion for control endpoints and §9.4 Phase C for params, the REST path remains a first-class public API.

The proposal assumes Phase A (SDK addition) and Phase C (canopy adapter wiring) are the two pieces in the author's lane. Phase B (browser bridge) is a **hard dependency** of Phase C because the browser-side clientside callback is what ultimately fires the new adapter path; without it, the adapter refactor has no consumer.

---

## 2. Source-doc cross-references

| Section | Content relevant to this proposal |
|---|---|
| §1.4 finding #3 | "There is no canopy → cascor WebSocket parameter control path." |
| §2.4 | `CascorTrainingStream` / `CascorControlStream` surface; the critical-gap note that neither class exposes `set_params`. Recommends `CascorControlStream.set_params(params, timeout=5.0)` as the landing site. |
| §2.5 | `apply_params()` at `cascor_service_adapter.py:450` currently calls `self._client.update_params(mapped)` (REST PATCH). The canopy-side anchor of the gap. |
| §3.0 | Envelope asymmetry: server→client uses `{type, timestamp, data}`; client→server uses bare `{command, params}`. |
| §3.2.3 | The `set_params` message contract: whitelist keys, success/error `command_response` shape. |
| §3.2.4 | Protocol error-response contract (malformed JSON, unknown command, handler exception, oversized frame). GAP-WS-22. |
| §5.1 | 11 of 17 editable parameters benefit from WebSocket transport. The hot/cold split this proposal uses for per-key routing. |
| §5.3.1 | **Critical caveat**: ack latency vs. effect-observation latency. The reason Phase C is P2, not P1, and why the feature flag matters. |
| §5.6 | Production latency measurement plan; the SDK must embed `emitted_at_monotonic` hooks so Phase C has data to decide whether to flip the default. |
| §6.1 | Transport split table showing "Hot parameter updates" routed to WebSocket and "Cold parameter updates" routed to REST. |
| §6.4 | Disconnection taxonomy — close codes relevant for fallback decisions. |
| §6.5 | Reconnection protocol (seq/replay). The SDK's reconnection story is *not* about applying replayed events to a chart; it is about how an in-flight `set_params` future is resolved across a reconnect. |
| §7.1 GAP-WS-01 | The SDK gap this proposal closes, with remediation hook "the first piece to land." |
| §7.10 GAP-WS-10 | No canopy-side integration test for `set_params` round-trip. Depends on GAP-WS-01. |
| §7.32 GAP-WS-32 | Per-command timeouts and orphaned-command resolution. Per-command timeouts proposed: `start: 10s`, `stop/pause/resume: 2s`, **`set_params: 1s`**. |
| §9.1 Phase A | SDK test plan: `test_set_params_round_trip`, `test_set_params_timeout`, `test_set_params_validation_error`, `test_set_params_reconnection_queue`, `test_set_params_concurrent_correlation`, `test_set_params_caller_cancellation`. |
| §9.4 Phase C | Canopy adapter test plan and the `Settings.use_websocket_set_params=False` feature flag. |
| §9.13 | Release coordination: Phase A PR must ship through PyPI before Phase C PR bumps the dep pin. |
| §10 RISK-03 | "Phase C race condition: REST PATCH and WebSocket set_params for the same param land out of order." Mitigated by per-param routing and disjoint hot/cold sets. |
| §10 RISK-09 | "Canopy `set_params` integration changes user-perceived behavior in unexpected ways." Mitigated by feature flag + §5.6 instrumentation. |
| §10 RISK-13 | "Orphaned commands after timeout (browser declares failure but server completes)." Mitigated via GAP-WS-32 per-command correlation IDs and `pending verification` UI state. This proposal ports the same pattern to the SDK layer. |

---

## 3. Why Phase C is P2 (ack latency invisible inside effect-observation loop)

Per §5.3.1, the user's perceived-latency loop when dragging a `learning_rate` slider is:

```
slider release → debounce (~250 ms) → set_params dispatch → cascor receives →
  next epoch boundary (100-1000 ms) → metrics emit → WS broadcast →
  browser receives → store update → Plotly extendTraces → user sees the curve bend
```

The transport hop (`set_params dispatch → cascor receives`) is one of ~7 stages. The **next-epoch** stage alone can exceed the entire 100 ms budget. So:

- Phase C optimizes **ack latency** (slider-release → backend confirmation).
- Ack latency is a sub-component of **effect-observation latency** (slider-release → chart bends).
- For actively-training networks, effect-observation latency is dominated by the next-epoch stage.
- Optimizing ack latency therefore delivers a measurable win only when epoch time is small relative to the REST round-trip — i.e., when training is fast (small datasets, low per-epoch cost). For most real workloads, the RTT difference between REST PATCH and WebSocket `set_params` is invisible inside effect-observation latency.

This is why the source doc **relabels Phase C from P1 to P2** (§5.3.1 and §9.4) and says it ships behind a flag. The §5.6 instrumentation is the gate: once real-world p50/p95 numbers exist for both transports, the decision to flip `use_websocket_set_params=True` by default becomes data-driven.

**Implication for this proposal**: the SDK method is written and shipped (Phase A, §9.1) with full test coverage regardless of the Phase C decision. The canopy adapter wires the method behind a flag. The two phases are decoupled: Phase A delivers value to any SDK consumer (not just canopy) by closing GAP-WS-01, and Phase C delivers value to canopy users only after the flag is flipped based on §5.6 data.

**This proposal explicitly does NOT argue against the P2 downgrade.** The downgrade is correct. The proposal scopes Phase C as "ship the plumbing so the decision can be made" rather than "ship user-visible latency improvements."

---

## 4. SDK API surface

### 4.1 New WebSocket set_params method signature

Add to `juniper_cascor_client/ws_client.py` on `CascorControlStream` (line 150):

```python
async def set_params(
    self,
    params: Dict[str, Any],
    *,
    timeout: float = 1.0,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update runtime-modifiable training parameters via WebSocket.

    Sends a `set_params` command to cascor's /ws/control endpoint and
    waits for the matching command_response. This is the WebSocket
    analog of CascorClient.update_params() (REST PATCH).

    Args:
        params: Dict of parameter names and new values. Keys must be
            members of the cascor whitelist (see §3.2.3 of the WebSocket
            messaging architecture doc, v1.3 STABLE). Values are passed
            through json.dumps without re-validation beyond JSON-
            serializability; cascor performs the authoritative type
            check.
        timeout: Seconds to wait for the command_response. Default 1.0
            per GAP-WS-32 per-command timeout table. Use 0 to disable
            (the method will block indefinitely on the server's reply).
        request_id: Optional client-supplied correlation ID. If None,
            one is auto-generated (uuid.uuid4().hex). Returned in the
            command_response for matching.

    Returns:
        The parsed command_response envelope, a dict of shape
        {"type": "command_response", "timestamp": float,
         "data": {"command": "set_params", "status": "success",
                  "result": {...updated params...}}}.

    Raises:
        JuniperCascorConnectionError: not connected; call connect() first.
        JuniperCascorTimeoutError: no matching response within `timeout`.
        JuniperCascorValidationError: the server returned
            command_response.status == "error" with a validation-flavored
            message (e.g., "Unknown parameter", "Invalid value").
        JuniperCascorClientError: any other error envelope (e.g.,
            "No network exists — create a network first").

    Notes:
        This method is safe to call concurrently on the same stream
        instance as long as each caller uses a distinct request_id.
        The internal correlation map routes each response to the
        waiting caller; see §4.5 for the contract.

        Unlike REST update_params() on CascorClient, this method does
        NOT retry on network errors. The caller is expected to handle
        reconnection explicitly (see §6).
    """
```

**Why `set_params` and not `update_params`**: the cascor wire-level command is literally `set_params` (verified at `juniper-cascor/src/api/websocket/control_stream.py` handler and §3.2.3 of the source doc). Naming the SDK method after the wire command makes the wire contract grep-able from the SDK callsite. The REST method name (`update_params`) is a legacy of the REST PATCH endpoint naming and is not changed.

**Why `timeout: float = 1.0`**: GAP-WS-32 specifies `set_params: 1s` as the per-command timeout. The source doc also specifies `start: 10s`, `stop/pause/resume: 2s`. The default for the generic `command()` method is `DEFAULT_CONTROL_STREAM_TIMEOUT` (5s); this is overridden per-method.

**Why `request_id` is a caller-suppliable kwarg**: for canopy's Phase C wiring, the correlation ID comes from the browser (clientside callback generates it so that the frontend can match `command_response` or a fallback `state` event to the originating slider). The SDK must pass it through, not generate its own when one is supplied.

### 4.2 Request/ack envelope

**Client→server frame** (bare `{command, params}` per §3.0 envelope asymmetry, with the added `request_id` from GAP-WS-32):

```json
{
  "command": "set_params",
  "request_id": "7f9a2c3d8e1b4a5f",
  "params": {
    "learning_rate": 0.005,
    "correlation_threshold": 0.15
  }
}
```

**Server→client frame** (wrapped `{type, timestamp, data}` per §3.0, plus `request_id` echo per GAP-WS-32):

```json
{
  "type": "command_response",
  "timestamp": 1712707201.789,
  "data": {
    "command": "set_params",
    "request_id": "7f9a2c3d8e1b4a5f",
    "status": "success",
    "result": {
      "learning_rate": 0.005,
      "correlation_threshold": 0.15
    }
  }
}
```

**Error case**:

```json
{
  "type": "command_response",
  "timestamp": 1712707201.789,
  "data": {
    "command": "set_params",
    "request_id": "7f9a2c3d8e1b4a5f",
    "status": "error",
    "error": "No network exists — create a network first"
  }
}
```

**Note on `request_id`**: the source doc at §3.2.3 does NOT currently specify a `request_id` field in either direction (only `command`, `status`, `result`/`error`). Adding it is a **new proposal from this document**, derived from GAP-WS-32's "client-generated `command_id` (UUID); cascor echoes it in `command_response`" language. See §11 for the disagreement note — this is an additive, backward-compatible extension to the `set_params` contract and should ship with Phase A on the SDK side and with the Phase G cascor integration test on the server side.

**Fallback if cascor does not echo `request_id`**: the SDK's correlation layer falls back to first-match-wins on `command == "set_params"`. This is racy if two `set_params` are in flight, but the canopy slider use case (debounced per slider, one in flight at a time) is not affected. Phase G (GAP-WS-09) server-side tests MUST include a `request_id` echo assertion so that server-side support lands before any `juniper-cascor-client` consumer depends on it. If the server lag forces SDK release first, the SDK defaults to first-match-wins and accepts the race.

### 4.3 Error and timeout semantics

**Exception mapping**:

| Wire / runtime condition | Python exception raised |
|---|---|
| Not connected (called before `connect()` or after `disconnect()`) | `JuniperCascorConnectionError` |
| `asyncio.wait_for` timeout before any response arrives | `JuniperCascorTimeoutError` with message `"set_params ack not received within {timeout}s"` |
| `command_response.status == "error"` with message matching validation patterns ("unknown param", "invalid value", "out of range") | `JuniperCascorValidationError` |
| `command_response.status == "error"` with any other message | `JuniperCascorClientError` |
| `ConnectionClosed` raised during `recv()` | `JuniperCascorConnectionError` with `__cause__` = the original `ConnectionClosed`, message includes close code |
| JSON parse error on the response frame | `JuniperCascorClientError` with message `"malformed command_response envelope: {json_err}"` |

**Timeout semantics**:

- The `timeout` kwarg bounds the time from `await self._ws.send(...)` to the receipt of a matching `command_response`. It does NOT include the time spent awaiting a lock in the correlation map, which is effectively zero under normal load.
- On timeout, the correlation entry for this `request_id` is **removed from the pending map** so a late-arriving response does not leak to a subsequent caller. The late response is logged at DEBUG and dropped.
- On timeout, the underlying WebSocket connection is **NOT closed**. The caller is expected to decide whether to retry, fall back to REST, or surface the error to the user. This matches the existing `CascorControlStream.command()` behavior.

**No retries**: `set_params` is not automatically retried on timeout or connection error. Retries at this layer would compose badly with the canopy adapter's fallback-to-REST logic (§5.3). The canopy adapter is the single decision point for retry.

### 4.4 Coexistence with existing REST update_params

The current SDK exposes:

- **`CascorClient.update_params(params)`** — synchronous, REST PATCH to `/api/v1/training/params`. Located in `client.py:224-238`. Used by `juniper-canopy/src/backend/cascor_service_adapter.py:465`.
- **`CascorControlStream.command("set_params", params)`** — async, generic WebSocket RPC. Could be hand-called but has no timeout tuning, no correlation ID, no exception translation.

The proposal is **strictly additive**:

- Add `CascorControlStream.set_params(...)` as a new async method. This is the WebSocket path.
- **Do NOT** remove or deprecate `CascorClient.update_params()`. It remains the REST path, used by:
  - Cold parameters in the canopy adapter (per §6.1 transport split).
  - Any external consumer of the SDK that does not want to open a WebSocket (scripts, notebooks, CLI tools).
  - The fallback path in the canopy adapter when WebSocket is disconnected or the feature flag is off.
- The two methods target **different objects** (`CascorClient` vs `CascorControlStream`) on **different transports** (HTTPS vs WSS), so there is no name collision.

**Naming alignment**: the source doc §7.1 GAP-WS-01 remediation says `CascorControlStream.set_params(params, timeout=5.0)`. This proposal changes the default timeout from `5.0` to `1.0` to match GAP-WS-32's per-command timeout table. Disagreement logged in §11.

**Is there a case for a unified high-level facade?** One could imagine a `CascorClient.set_params_smart(params)` that picks REST or WebSocket based on some policy. **Rejected**: the SDK should remain a thin wrapper over the wire. The "smart" routing belongs in canopy's `CascorServiceAdapter` because the hot/cold split is a canopy-specific decision informed by canopy's UI element mapping. Pushing it into the SDK would require the SDK to know about canopy's `nn_*`/`cn_*` namespace (wrong layering) or maintain its own hot/cold whitelist (duplication).

### 4.5 Concurrent-caller correlation map

The current `CascorControlStream.command()` is single-caller: it sends a message and awaits the next `recv()`. With `set_params` potentially being called from multiple sliders in parallel (or from the same slider twice before the first ack arrives), the one-in-flight assumption breaks.

**Required addition** to `CascorControlStream`:

```python
self._pending: Dict[str, asyncio.Future[Dict[str, Any]]] = {}
self._recv_task: Optional[asyncio.Task] = None
```

Lifecycle:

1. `connect()` starts a background `_recv_task` that loops `await self._ws.recv()`, parses each frame, looks up `data.request_id` in `self._pending`, and calls `future.set_result(envelope)`.
2. `set_params(...)` creates a new `asyncio.Future`, registers it under `request_id` in `_pending`, sends the command frame, `await asyncio.wait_for(future, timeout)`, removes the entry on any path, and returns the parsed envelope.
3. `disconnect()` cancels `_recv_task` and `set_exception(JuniperCascorConnectionError(...))` on all pending futures so waiting callers see a clean failure.

**Why a single background recv task**: `websockets.ClientConnection.recv()` is a single-reader abstraction. Multiple concurrent callers each calling `recv()` would deadlock or interleave messages unsafely. The single-reader background task is the canonical pattern.

**What about the generic `command()` method?** It continues to work but internally routes through the same correlation map. Callers of `command("start", ...)` get a request_id generated for them; the existing first-match-wins behavior is preserved as a legacy compatibility shim (no `request_id` on the frame, first response with matching `command` name wins).

**Back-compat**: the `_recv_task` lifecycle is internal; callers of the existing `CascorControlStream.command()` method see no API change. The refactor ships as part of Phase A (§9.1).

---

## 5. canopy adapter migration

### 5.1 apply_params() refactor

Current shape (`juniper-canopy/src/backend/cascor_service_adapter.py:451-470`):

```python
def apply_params(self, **params: Any) -> Dict[str, Any]:
    mapped = {self._CANOPY_TO_CASCOR_PARAM_MAP[k]: v
              for k, v in params.items() if k in self._CANOPY_TO_CASCOR_PARAM_MAP}
    # ... skipped-key logging ...
    result = self._client.update_params(mapped)  # REST PATCH
    # ... error handling ...
```

Refactored shape (Phase C):

```python
# New constant (hot = §5.1 "WebSocket preferred" set; cold = REST OK set)
_HOT_CASCOR_PARAMS = frozenset({
    "learning_rate",
    "candidate_learning_rate",
    "correlation_threshold",
    "candidate_pool_size",
    "max_hidden_units",
    "epochs_max",
    "max_iterations",
    "patience",
    "convergence_threshold",
    "candidate_convergence_threshold",
    "candidate_patience",
    # 11 params total per §5.1 summary
})
_COLD_CASCOR_PARAMS = frozenset({
    "init_output_weights",
    "candidate_epochs",
    # 2 params that cascor accepts but §5.1 says REST is OK
    # (one-shot dropdowns; no tight feedback loop)
})

def apply_params(self, **params: Any) -> Dict[str, Any]:
    """Forward parameter updates to the running cascor instance.

    Public delegating wrapper. Splits params into hot/cold sets and
    dispatches to _apply_params_hot() (WebSocket) and _apply_params_cold()
    (REST). When Settings.use_websocket_set_params is False, all params
    route through the REST path for backwards-compat behavior.
    """
    mapped = {self._CANOPY_TO_CASCOR_PARAM_MAP[k]: v
              for k, v in params.items() if k in self._CANOPY_TO_CASCOR_PARAM_MAP}
    # ... skipped-key logging (unchanged) ...
    if not mapped:
        return {"ok": True, "data": {}, "message": "No cascor-mappable params provided"}

    if not self._settings.use_websocket_set_params:
        # Feature flag off: preserve original REST behavior
        return self._apply_params_cold(mapped)

    hot = {k: v for k, v in mapped.items() if k in self._HOT_CASCOR_PARAMS}
    cold = {k: v for k, v in mapped.items() if k in self._COLD_CASCOR_PARAMS}
    unknown = set(mapped) - self._HOT_CASCOR_PARAMS - self._COLD_CASCOR_PARAMS
    if unknown:
        # New param that cascor accepts but this adapter doesn't yet classify.
        # Default to REST for safety; log a WARNING so operators notice the gap.
        logger.warning(f"apply_params: unclassified keys, defaulting to REST: {unknown}")
        cold.update({k: mapped[k] for k in unknown})

    results: Dict[str, Any] = {"ok": True, "data": {}}
    if hot:
        hot_result = self._apply_params_hot(hot)
        results["data"].update(hot_result.get("data", {}))
        results["ok"] = results["ok"] and hot_result["ok"]
    if cold:
        cold_result = self._apply_params_cold(cold)
        results["data"].update(cold_result.get("data", {}))
        results["ok"] = results["ok"] and cold_result["ok"]
    return results


def _apply_params_hot(self, mapped: Dict[str, Any]) -> Dict[str, Any]:
    """WebSocket fast-path for hot params.

    Uses a module-level or adapter-scoped CascorControlStream that is
    kept open for the lifetime of the adapter (see §6 for connection
    lifecycle). Falls back to REST on any of:
    - WebSocket not connected
    - WebSocket in reconnecting state
    - JuniperCascorTimeoutError from set_params()
    - JuniperCascorConnectionError from set_params()
    - JuniperCascorClientError from set_params() (preserve original REST behavior on server errors)
    """
    if self._control_stream is None or not self._control_stream.is_connected:
        logger.info(f"apply_params: WS not connected, falling back to REST for {list(mapped.keys())}")
        return self._apply_params_cold(mapped)
    try:
        future = asyncio.run_coroutine_threadsafe(
            self._control_stream.set_params(mapped, timeout=1.0),
            self._control_loop,
        )
        envelope = future.result(timeout=2.0)  # outer timeout > inner timeout
        return {"ok": True, "data": envelope.get("data", {}).get("result", {})}
    except (JuniperCascorTimeoutError, JuniperCascorConnectionError) as e:
        logger.warning(f"apply_params: WS set_params failed ({e}); falling back to REST")
        return self._apply_params_cold(mapped)
    except JuniperCascorClientError as e:
        logger.error(f"apply_params: WS set_params server error: {e}")
        return {"ok": False, "error": str(e)}


def _apply_params_cold(self, mapped: Dict[str, Any]) -> Dict[str, Any]:
    """REST slow-path (original behavior, extracted as private method)."""
    try:
        result = self._client.update_params(mapped)
        logger.info(f"Cascor params updated (REST): {list(mapped.keys())}")
        return {"ok": True, "data": result}
    except JuniperCascorClientError as e:
        logger.error(f"Failed to update cascor params: {e}")
        return {"ok": False, "error": str(e)}
```

**Backwards compatibility**: the public signature `apply_params(**params)` is unchanged. External callers see the same `{"ok": bool, "data": dict}` return shape. Per §9.4, "External callers see no signature change. No deprecation needed."

**Per-key split preserves atomicity inside each transport**: the hot and cold sets are disjoint (hot contains `learning_rate`, cold contains `init_output_weights`). Within each set, the single-call semantics of cascor's `lifecycle.update_params()` are preserved — cascor uses keyed merges (verified in §10 RISK-03), so two back-to-back calls with disjoint keys do not race each other. **A single `apply_params()` call can fire both a WebSocket set_params AND a REST PATCH**, in either order, against the same cascor instance; the `lifecycle._training_lock` serializes them on the server side.

**Ordering guarantee**: the WebSocket path fires first, then REST. Rationale: the hot params are the ones the user is actively dragging, so they should take precedence on latency. If the REST call fails but the WebSocket call succeeded, the user still got the hot-param update.

### 5.2 Feature flag and rollback

Add to `juniper-canopy/src/config/settings.py`:

```python
use_websocket_set_params: bool = Field(
    default=False,
    description=(
        "When True, canopy's apply_params() routes hot params through "
        "CascorControlStream.set_params() over WebSocket. When False, all "
        "params go through REST PATCH (legacy behavior). See Phase C of the "
        "WebSocket messaging architecture doc (v1.3 STABLE). Default False "
        "pending §5.6 production latency measurement (GAP-WS-24)."
    ),
)
```

Environment variable: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=true|false`. Read via the existing `Settings` singleton.

**Rollout stages**:

1. **Stage 0 (Phase A lands)**: SDK exposes `set_params`; canopy is unchanged. No flag exists yet. No user-visible change.
2. **Stage 1 (Phase C lands, flag default False)**: canopy adapter has both paths; tests pass on both with flag True in CI; production default is False. No user-visible change. Instrumentation (§5.6) starts collecting REST-path p50/p95/p99 for `apply_params`.
3. **Stage 2 (instrumentation complete, ~1 week after Phase C lands)**: compare REST latency histogram to the §5.1 thresholds. If REST p99 for hot params is already under the §5.1 target (e.g., <200 ms), Phase C is unnecessary and the flag stays False forever. Otherwise proceed.
4. **Stage 3 (opt-in enable)**: flip flag to True in a staging canopy instance; run a week of real usage; collect WS-path latency histograms. Compare to REST histograms.
5. **Stage 4 (production default flip)**: if WS-path p99 is meaningfully lower than REST-path p99 AND there are no regressions in RISK-03 / RISK-09 alerting, flip the production default to True via a canopy config change. This is a single-line PR; no code churn.
6. **Stage 5 (REST PATCH deprecation)**: **not planned**. The REST path remains as the documented public API and as the fallback for disconnected clients.

**Rollback**: flipping the flag back to False is a single-line config change; no code redeploy needed if it's an env var. This is the primary rollback path.

**Kill switch**: if a critical bug is discovered in the WS path (e.g., correlation-map leak, slider lag), operators set `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` and restart the canopy process. Total MTTR: <2 minutes.

### 5.3 Fallback to REST during WS reconnect

The WebSocket connection can be in one of four states:

| State | `_apply_params_hot` behavior |
|---|---|
| **Connected** | Send via WS; on success return; on timeout/error fall back to REST |
| **Reconnecting** (backoff pending, no active connection) | Skip WS, go directly to REST. Do NOT queue. |
| **Disconnected** (connect never succeeded; no reconnect task running) | Skip WS, go directly to REST. Attempt reconnect in background. |
| **Shutting down** (adapter is being torn down) | Fall through to REST. Log at INFO. |

**Why no queueing on reconnect**: queueing `set_params` calls during a reconnect window would compose badly with the slider's debounce semantics. The user is dragging a slider at human timescales (100 ms to 10 s); a 5-second reconnect gap followed by "flush all queued set_params" would replay stale values on top of the current one. The slider's own debounce logic already guarantees that only the most recent value per slider is in flight at any time — so the correct fallback is "use REST for this one call and carry on."

**Connection lifecycle ownership**: the `CascorServiceAdapter` owns a single long-lived `CascorControlStream` instance, opened during adapter initialization (after the existing `CascorTrainingStream` relay is up per §2.5) and closed during `stop_metrics_relay()`. The reconnect logic uses the same exponential backoff schedule as the training relay: `[1, 2, 5, 10, 30]` seconds.

**Reconnect task**:

```python
async def _control_stream_supervisor(self):
    """Background task that keeps CascorControlStream alive."""
    backoff = [1, 2, 5, 10, 30]
    attempt = 0
    while not self._shutdown.is_set():
        try:
            self._control_stream = CascorControlStream(self._ws_base_url, self._api_key)
            await self._control_stream.connect()
            attempt = 0  # reset on successful connect
            await self._control_stream.wait_closed()  # blocks until disconnect
        except (JuniperCascorConnectionError, JuniperCascorClientError) as e:
            logger.warning(f"Control stream reconnect {attempt}: {e}")
        finally:
            self._control_stream = None
            if not self._shutdown.is_set():
                await asyncio.sleep(backoff[min(attempt, len(backoff) - 1)])
                attempt += 1
```

Two tasks run in parallel in the adapter's background event loop: the existing metrics-relay task (`CascorTrainingStream` consumer) and the new `_control_stream_supervisor`. They are independent — a failure in one does not kill the other.

**Thread bridging**: canopy's `CascorServiceAdapter` is called from a synchronous Dash callback thread. The control stream lives in the adapter's async loop (same loop as the existing training relay). The bridge is `asyncio.run_coroutine_threadsafe(...).result(timeout=...)`, already used elsewhere in canopy. The outer `.result(timeout=2.0)` is intentionally >= the inner `timeout=1.0` passed to `set_params()` so that the inner timeout fires cleanly before the outer one.

### 5.4 What happens if the flag is on but Phase B is not done yet?

The Phase C refactor lands **after** Phase B per the §9.12 phase ordering. If Phase C lands first by mistake (merge order error), the feature flag defaults to False, so nothing breaks — the adapter still uses REST. When someone flips the flag to True in a test environment, the adapter attempts to open a control stream; if Phase B's security mitigations (Phase B-pre) are not in place, the control stream connect may be rejected by cascor's auth check, the fallback triggers, and everything still works via REST. A warning log tells operators the WS path is not usable.

So: **ordering errors are self-healing** because the fallback is unconditional. This is a strong argument for keeping the fallback permanently rather than removing it once the WS path is proven.

---

## 6. Idempotency and reconnection behavior

### 6.1 Idempotency of set_params at the cascor layer

Cascor's `lifecycle.update_params(params)` is a **keyed merge** (verified per the source doc §10 RISK-03 referencing `lifecycle/manager.py:684-723`). Sending `{learning_rate: 0.005}` twice back-to-back produces the same final state as sending it once. The operation is naturally idempotent at the server.

This means **the SDK does not need to deduplicate**. A replayed or retried `set_params` with the same payload does not corrupt state. The worst case is wasted bandwidth.

### 6.2 Duplicate suppression on reconnect

**Scenario**: the WebSocket disconnects mid-send. The send may or may not have been received by cascor; `send()` doesn't wait for ack.

**Proposed behavior**: the `set_params()` future that was in flight at disconnect is **resolved with `JuniperCascorConnectionError`**. The caller (canopy adapter) catches it and falls back to REST. The REST call re-applies the same params. If the original WebSocket send was received by cascor, the REST call is a no-op (keyed merge with identical values). If it was not received, the REST call applies the values.

**No replay buffer on the client side**: the SDK does not maintain a pending-send buffer for `set_params`. §6.5 of the source doc describes a **server-side** replay buffer for server→client events, not for client→server commands. Client commands are not reliably delivered across disconnects; the recovery strategy is "the caller decides what to do" (retry, fall back, give up).

**Why this is safe for the slider use case**: the slider's debounce (250 ms) is smaller than any reasonable reconnect interval (1 s minimum). So by the time a reconnect completes, the slider has almost certainly fired its next debounced update, which will apply the latest value. The user sees at most a 1-second stutter in ack latency; the final state converges.

### 6.3 In-flight futures on adapter shutdown

When `stop_metrics_relay()` (or its control-stream counterpart) is called, any pending `set_params` futures must be resolved. Options:

| Option | Behavior | Chosen? |
|---|---|---|
| Cancel futures | `future.cancel()` raises `CancelledError` in caller | Yes, when shutting down adapter |
| Exception | `future.set_exception(JuniperCascorConnectionError("shutting down"))` | Yes, equivalent outcome, cleaner semantics |
| Wait for completion | Block shutdown until all futures complete | No — shutdown must not hang on a stuck server |

**Decision**: `set_exception(JuniperCascorConnectionError("shutting down"))`. This is clean: the caller already handles `JuniperCascorConnectionError` as "fall back to REST," so shutdown during an in-flight call degrades gracefully.

### 6.4 Caller cancellation (§9.1 test plan)

Test `test_set_params_caller_cancellation` (§9.1): the caller `await`s `set_params(...)` and then cancels the task before the server replies. The SDK must:

1. Propagate the `CancelledError` to the caller.
2. Remove the `request_id` entry from `_pending` so a late-arriving response is not leaked to a future caller.
3. NOT close the WebSocket connection (other callers may be actively using it).

The implementation is:

```python
try:
    return await asyncio.wait_for(future, timeout=timeout)
except asyncio.CancelledError:
    self._pending.pop(request_id, None)
    raise
except asyncio.TimeoutError:
    self._pending.pop(request_id, None)
    raise JuniperCascorTimeoutError(f"set_params ack not received within {timeout}s")
```

---

## 7. Latency instrumentation (§5.6 hooks)

Phase C's go/no-go decision hinges on §5.6 data. The SDK must emit the right hooks so the canopy adapter can aggregate per-request latency.

### 7.1 Client-side hooks

Add to `CascorControlStream.set_params()`:

```python
import time
t_sent = time.monotonic()
await self._ws.send(json.dumps(frame))
envelope = await asyncio.wait_for(future, timeout=timeout)
t_acked = time.monotonic()
latency_ms = (t_acked - t_sent) * 1000
# Stash into envelope for caller inspection (optional but cheap)
envelope["_client_latency_ms"] = latency_ms
return envelope
```

The `_client_latency_ms` key is a **private SDK-only field** not part of the wire contract (leading underscore per Python convention). Callers that want it can read it; callers that don't are unaffected. The canopy adapter reads it and emits a Prometheus histogram observation.

**Why monotonic and not wall-clock**: wall clock can jump backwards on NTP sync. Monotonic is guaranteed non-decreasing within a process. Latency measurements over real-time traffic need monotonic.

### 7.2 Canopy adapter aggregation

In `_apply_params_hot()`, after a successful send:

```python
try:
    envelope = future.result(timeout=2.0)
    latency_ms = envelope.get("_client_latency_ms", 0.0)
    SET_PARAMS_LATENCY_MS.labels(transport="websocket").observe(latency_ms)
    return {"ok": True, "data": envelope.get("data", {}).get("result", {})}
except ...
```

And in `_apply_params_cold()`:

```python
t_sent = time.monotonic()
try:
    result = self._client.update_params(mapped)
    latency_ms = (time.monotonic() - t_sent) * 1000
    SET_PARAMS_LATENCY_MS.labels(transport="rest").observe(latency_ms)
    return {"ok": True, "data": result}
```

where `SET_PARAMS_LATENCY_MS` is a `prometheus_client.Histogram(name="canopy_set_params_latency_ms", ...)` with buckets `{5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000}` ms.

This gives a direct comparison: `canopy_set_params_latency_ms_bucket{transport="websocket"}` vs `canopy_set_params_latency_ms_bucket{transport="rest"}` per §5.6 item #5.

### 7.3 What §5.6 adds beyond this

§5.6 goes further and proposes server-side `emitted_at_monotonic` stamps for incoming events — but that is for **cascor → browser** latency, not for **`set_params` request/ack latency**. The `set_params` case is entirely single-sided (client measures round-trip), so no server-side cooperation is needed beyond the existing `command_response` frame.

**GAP-WS-24** covers the full §5.6 plan (server stamps, browser histograms, `/api/ws_latency` endpoint, Prometheus export). This proposal is a **subset** of GAP-WS-24 specifically for the `set_params` case. It can ship before the full GAP-WS-24 because it does not require server-side changes.

---

## 8. Per-keystroke vs per-slider-release strategy

The SDK is **transport-neutral on debouncing**. It does not debounce. Rationale:

1. Debouncing is a UI concern (how often the user's input generates a "fire" event). It belongs in the Dash clientside callback, not the SDK.
2. Canopy already debounces sliders in the existing REST path (per the `fast-update-interval` and per-slider debounce docstring conventions). Phase C inherits the same debounce.
3. Putting debouncing in the SDK would couple it to a UI tempo, which varies by consumer. A future non-canopy consumer (CLI tool, notebook) would want immediate dispatch, not 250 ms debounce.

**Recommendation for canopy sliders**: keep the existing 250 ms debounce on slider-release (or keystroke for text inputs). Fire one `apply_params()` per debounced event. The SDK's `set_params` will see at most one call per 250 ms per slider — well within the timeout budget.

**What if the user drags a slider continuously across a range**: intermediate values are discarded by the debounce; only the final release fires. The `set_params` call sees the single final value. This is the desired UX: the user is saying "set learning rate to this value I ended on," not "apply every value I passed through."

**What if multiple sliders move at once**: the Phase C adapter refactor accepts `**params`, so a single call can carry multiple keys. The slider-group callback batches them into one `apply_params(nn_learning_rate=..., cn_correlation_threshold=...)` call per debounce tick. The adapter then splits hot/cold and sends at most one WebSocket frame and at most one REST request. This is more efficient than one frame per slider.

---

## 9. Implementation steps

### 9.1 Phase A: SDK set_params (0.5 day per §9.1, but realistically 1 day with correlation-map refactor)

**Touched files**:
- `juniper-cascor-client/juniper_cascor_client/ws_client.py`
- `juniper-cascor-client/juniper_cascor_client/constants.py` (add `WS_MSG_TYPE_COMMAND_RESPONSE`)
- `juniper-cascor-client/juniper_cascor_client/exceptions.py` (no change; existing exceptions are sufficient)
- `juniper-cascor-client/tests/unit/test_ws_client.py` (add test cases listed in §9.1 of source doc)
- `juniper-cascor-client/CHANGELOG.md` (added under "Added")

**Order of operations**:
1. Refactor `CascorControlStream` to use a background `_recv_task` and a `_pending` correlation map. Preserve the existing `command()` API as a wrapper that generates a fresh `request_id` if none is provided.
2. Add `set_params(params, *, timeout=1.0, request_id=None)` method.
3. Add unit tests in `test_ws_client.py`.
4. Update README.md example to show the new method.
5. Bump version (semver minor: e.g., `1.x.0` → `1.(x+1).0`). Tag, release.

**Test matrix** (per §9.1):
- `test_set_params_round_trip` — happy path, success envelope returned
- `test_set_params_timeout` — no server reply, `JuniperCascorTimeoutError` raised
- `test_set_params_validation_error` — server replies with `status: "error"`, appropriate exception raised
- `test_set_params_reconnection_queue` — client disconnects mid-send; verify pending future resolves with `JuniperCascorConnectionError`
- `test_set_params_concurrent_correlation` — two concurrent calls with distinct `request_id`s; each resolves to its matching response
- `test_set_params_caller_cancellation` — caller cancels before reply; pending map is cleaned; no leak
- `test_command_legacy_still_works` — existing `command("start")` call path still succeeds (backwards-compat regression gate)
- `test_set_params_no_request_id_first_match_wins` — for the server-not-yet-echoing-request_id transition window

### 9.2 Phase C: canopy adapter wiring (2 days per §9.4)

**Touched files**:
- `juniper-canopy/src/backend/cascor_service_adapter.py` — refactor `apply_params()`; add `_apply_params_hot()`, `_apply_params_cold()`, `_HOT_CASCOR_PARAMS`, `_COLD_CASCOR_PARAMS`, `_control_stream_supervisor` task
- `juniper-canopy/src/config/settings.py` — add `use_websocket_set_params: bool = False` setting
- `juniper-canopy/pyproject.toml` — bump `juniper-cascor-client>={Phase_A_version}`
- `juniper-ml/pyproject.toml` — bump the same pin in the meta-package extras
- `juniper-canopy/src/tests/unit/test_cascor_service_adapter.py` — add routing tests
- `juniper-canopy/src/tests/integration/test_param_apply_roundtrip_ws.py` (new) — WebSocket roundtrip test against `FakeCascorServerHarness`
- `juniper-canopy/docs/REFERENCE.md` — document the feature flag

**Order of operations**:
1. Wait for Phase A PyPI release (§9.13 item 2: 2-5 minutes propagation).
2. Bump dep pin; run CI; green light.
3. Land the flag setting + the hot/cold classification + the refactored `apply_params()`.
4. Land the `_control_stream_supervisor` task (borrow structure from the existing metrics-relay task).
5. Land the unit tests and the new integration test.
6. Merge. Default flag is False; no user-visible change.
7. Coordinate with the sibling frontend agent for Phase B to wire the slider clientside callback to route hot params through the adapter's now-WebSocket-aware `apply_params()`.

### 9.3 Sequencing against Phase B

Phase B (browser bridge) is Phase C's hard dependency because the dashboard sliders are the primary consumer of the adapter refactor. **However**, Phase C can land with the flag off **without** Phase B landing first. The REST path is preserved and is exactly equivalent to pre-refactor behavior when the flag is False.

This gives the project team scheduling flexibility:
- Phase A → Phase C (flag off) can land and be stable before Phase B is merged.
- Phase B lands; operators can flip the flag to True in staging.
- §5.6 instrumentation data drives the default-flip decision.

---

## 10. Verification / acceptance criteria

### 10.1 Phase A (SDK) acceptance

| # | Criterion | How verified |
|---|---|---|
| A1 | `CascorControlStream.set_params(params)` exists and is an async method | Importable; `inspect.iscoroutinefunction` returns True |
| A2 | Round-trip against a fake server returns the parsed `command_response` envelope | `test_set_params_round_trip` |
| A3 | Timeout raises `JuniperCascorTimeoutError` | `test_set_params_timeout` |
| A4 | Server error raises appropriate exception class | `test_set_params_validation_error` |
| A5 | Two concurrent calls correlate correctly via `request_id` | `test_set_params_concurrent_correlation` |
| A6 | Cancellation cleans up pending map | `test_set_params_caller_cancellation` |
| A7 | Disconnect mid-call resolves in-flight futures with `JuniperCascorConnectionError` | `test_set_params_reconnection_queue` |
| A8 | Existing `command()` method still works (regression) | `test_command_legacy_still_works` |
| A9 | Package version bumped, CHANGELOG updated, release published to PyPI | CI release workflow |

### 10.2 Phase C (canopy adapter) acceptance

| # | Criterion | How verified |
|---|---|---|
| C1 | `Settings.use_websocket_set_params` exists with default False | Config test |
| C2 | `apply_params(**params)` public signature unchanged | Callers compile; existing REST tests pass |
| C3 | With flag False, all params route through REST | Unit test with mock REST client; no WS traffic |
| C4 | With flag True, hot params route through WS, cold through REST | Unit test with both mocked |
| C5 | With flag True, WS disconnect triggers REST fallback | Unit test |
| C6 | With flag True, WS timeout triggers REST fallback | Unit test with slow fake server |
| C7 | With flag True, WS server error is surfaced (not fallback) | Unit test |
| C8 | With flag True, mixed hot/cold batch fires both transports | Unit test |
| C9 | Unclassified keys default to REST with warning log | Unit test |
| C10 | Integration test against `FakeCascorServerHarness` asserts the WS frame is well-formed `{command: "set_params", params: ...}` | `test_param_apply_roundtrip_ws.py` |
| C11 | Latency histogram labels are emitted for both transports | Unit test reads Prometheus registry |
| C12 | Control-stream supervisor reconnects with exponential backoff | Integration test forces disconnect |
| C13 | Control-stream supervisor shutdown cancels pending futures | Unit test |

### 10.3 Stage 2/3 flag-flip acceptance (operational, not code)

| # | Criterion | How verified |
|---|---|---|
| O1 | One week of REST-path p50/p95/p99 collected in Prometheus | Grafana dashboard |
| O2 | Flag flipped True in staging; no alerting regressions for 1 week | ops review |
| O3 | WS-path p99 under §5.1 target (200 ms for broad params, 100 ms for tight-loop params) | histogram comparison |
| O4 | No RISK-03 (ordering race) alerts | alert query |
| O5 | No RISK-09 (unexpected behavior) user reports | issue tracker review |
| O6 | Production flag flip PR authored, reviewed, merged | GitHub |

---

## 11. Risks and mitigations

| ID | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R04-01 | SDK `_pending` correlation map leaks entries on partial failures | Medium | Medium | Always `pop` in `finally`; add a test that measures `len(_pending)` after various failure modes |
| R04-02 | Adding `request_id` as a new field breaks older cascor servers that do not know about it | Low | Low | The field is additive on the client→server side; cascor's `_VALID_COMMANDS` is unchanged and unknown fields in the inbound JSON are naturally ignored. Verified by the same §6.5.4 additive-envelope argument. |
| R04-03 | RISK-03 (REST+WS ordering race) manifests when hot/cold sets overlap due to a future param addition | Medium | Low | Explicit whitelist classification; WARNING log on unknown keys; `lifecycle._training_lock` serializes both paths server-side |
| R04-04 | RISK-09 (unexpected behavior) — a slider that used to "always work" breaks when the WS path is enabled | Low | Medium | Feature flag; REST fallback on any WS error is unconditional; ship with default False |
| R04-05 | Background control stream is never opened because Phase B-pre auth fails silently | Low | Medium | `_control_stream_supervisor` logs each connect attempt at WARNING; operators notice; fallback protects users in the meantime |
| R04-06 | `_recv_task` crashes with an unhandled exception and the correlation map stops draining | Medium | Low | Wrap the recv loop in `try/except Exception` that logs at ERROR and cancels all pending futures with `JuniperCascorClientError("recv task crashed: ...")` so callers fail loudly |
| R04-07 | Canopy adapter's background loop is shared with the metrics relay; a blocking call in `_control_stream_supervisor` could starve it | Low | Low | All calls are `await`; no synchronous blocking; the supervisor's backoff is `asyncio.sleep`, not `time.sleep` |
| R04-08 | Caller passes a numpy scalar (e.g., `np.float32(0.005)`) and `json.dumps` raises | Low | Medium | Convert to Python primitives in `apply_params` before passing down; unit test covers numpy scalar inputs. Already handled by the existing REST path; preserve the behavior. |
| R04-09 | The `_client_latency_ms` private SDK field leaks into a caller that mutates it | Low | Low | Document the leading-underscore convention; return a fresh dict from `set_params()` so caller mutation does not affect the SDK |
| R04-10 | The canopy adapter is torn down while a `set_params` request is in the uvicorn request queue | Low | Low | `asyncio.run_coroutine_threadsafe` raises `RuntimeError` if the loop is closed; catch and fall through to REST |
| R04-11 | The `request_id` echo is not yet supported by cascor when SDK is released; concurrent calls correlate incorrectly via first-match-wins | Medium | Medium | Phase G (cascor server test) gates the `request_id` echo; SDK default is first-match-wins if `request_id` is absent; canopy sliders are debounced so concurrent `set_params` is rare. Document clearly in the SDK CHANGELOG. |
| R04-12 | Two adapter instances in the same canopy process open two control streams, doubling server-side connections | Low | Low | Adapter is a module-level singleton in canopy (verified in existing code); only one control stream per process |
| R04-13 | The `_control_stream_supervisor` task leaks after adapter shutdown because the cancel() is missed | Low | Low | Track the task handle in the adapter; `stop_metrics_relay()` awaits both task cancellations before returning |
| R04-14 | Flag flip in production causes a thundering herd of control-stream connects from many canopy replicas | Low | Low | Canopy is typically a single replica; multi-replica deployments should add jitter to the supervisor's backoff (same mechanism as GAP-WS-30 but on the client side) |

**All risks are mitigated by the unconditional REST fallback.** This is the load-bearing property of the Phase C design: if any part of the WS path fails, the existing REST path is the rollback, and the user experience degrades at most to pre-refactor latency.

---

## 12. Disagreements with the source doc

### 12.1 Default `timeout` for `set_params`

**Source doc**: §7.1 GAP-WS-01 remediation recommends `CascorControlStream.set_params(params, timeout=5.0)`.

**This proposal**: default `timeout=1.0`.

**Rationale**: the source doc itself at §7.32 GAP-WS-32 specifies `set_params: 1s` as the per-command timeout. The 5.0 default in §7.1 appears to be a carry-over from the generic `DEFAULT_CONTROL_STREAM_TIMEOUT=5.0` (`constants.py`). The 1 second value is more aligned with the hot-path use case (slider updates) and matches the §5.1 urgency tiers (100-200 ms ack budget plus headroom).

**Impact if unresolved**: if the default is 5s, a slider hang caused by a stuck server takes 5 seconds to fall back to REST, which is a visibly bad UX. 1 second is tight but acceptable given the 200 ms §5.1 target. Callers that need more can pass `timeout=5.0` explicitly.

### 12.2 `request_id` as a new additive field

**Source doc**: §3.2.3 does not include `request_id` in the `set_params` contract. §7.32 GAP-WS-32 mentions `command_id` as a client-supplied field that cascor "echoes in `command_response`," but this is not wired into the §3.2 contract.

**This proposal**: add `request_id` as an additive field in both directions, documented here and (eventually) promoted to §3.2.3.

**Rationale**: correlation is required for concurrent `set_params` calls. Without it, the first-match-wins fallback is racy. Adding the field is cheap and backwards-compatible on the wire (cascor's existing handler would ignore unknown fields in the inbound JSON; the SDK would fall back to first-match-wins if cascor's response does not echo it).

**Action**: flag this in §11 "Open questions" for human review to formalize in §3.2.3. The Phase G cascor server test (GAP-WS-09) should assert that cascor echoes `request_id` back when present.

### 12.3 SDK fallback semantics

**Source doc**: does not specify what `set_params` should do on reconnect beyond "raise a connection error."

**This proposal**: `set_params` always raises on connect failure / disconnect / timeout; the **canopy adapter** is the single decision point for fallback-to-REST. No SDK-level retry.

**Rationale**: layering. SDK-level retries compose badly with application-level policies. Canopy might want different fallback behavior than, e.g., a future CLI tool. Each caller picks its own policy.

### 12.4 Keeping REST `update_params` forever

**Source doc**: §9.4 and §9.5 both mention that existing REST paths stay as "first-class supported APIs" (e.g., `/api/train/{command}` at §9.5). The source doc is silent on the specific case of REST `/api/v1/training/params` (the cascor endpoint backing `CascorClient.update_params()`).

**This proposal**: explicitly keep REST `update_params()` forever. The canopy adapter's REST fallback is the primary reason, but the SDK should also keep it for non-canopy consumers.

**Rationale**: no deprecation plan, no end-of-life, no migration path. The REST path is stable and used; the WS path is additive. The symmetry with §9.5's explicit preservation of `/api/train/{command}` is deliberate.

### 12.5 Per-slider debounce belongs in Dash, not in the SDK

**Source doc**: silent on debounce location.

**This proposal**: the SDK does not debounce; canopy's clientside callback does.

**Rationale**: cleanly layered. Same as §12.3.

---

## 13. Self-audit log

### 13.1 First pass findings (after initial draft)

1. **Missing per-command correlation ID story**. First draft treated `set_params` as a single-caller method like the existing `command()`. Added §4.5 concurrent-caller correlation map section, added GAP-WS-32 cross-reference, added `request_id` to the wire contract, updated exception semantics to describe pending-map cleanup.

2. **Missing caller-cancellation test case**. Source doc §9.1 lists `test_set_params_caller_cancellation` explicitly. First draft had no discussion of cancellation. Added §6.4 and §10.1 A6.

3. **No discussion of `_recv_task` crash recovery**. If the background recv loop dies from an unexpected exception, pending futures would hang forever. Added R04-06 mitigation.

4. **Thread-bridging detail missing**. The adapter's `apply_params()` is called from a synchronous Dash thread but the SDK method is async. Added §5.3 thread-bridging discussion with `asyncio.run_coroutine_threadsafe` pattern.

5. **Missing REST fallback kill switch / MTTR story**. Added Stage 4/5 rollback discussion in §5.2 and explicit 2-minute MTTR for the env-var flip.

6. **Feature flag scope creep**. First draft had the flag gating both Phase C and its instrumentation. Clarified in §5.2 that instrumentation runs in both modes (False and True) so the Stage 2/3 comparison is feasible.

7. **Timeout default mismatch with source doc**. Source doc §7.1 says 5.0 but §7.32 says 1.0. First draft copied 5.0 uncritically. Added §12.1 disagreement; resolved to 1.0.

8. **Missing concurrent-slider optimization**. Two sliders moving at once should fire one frame not two. First draft was silent. Added §8 last paragraph.

9. **Idempotency discussion was superficial**. Added §6.1 and §6.2 with concrete "keyed merge" reasoning and the no-client-side-replay-buffer decision.

10. **Hot/cold split was partial**. First draft listed only the §5.1 "tight-loop" params. Expanded to the full 11-hot-of-17 split per the §5.1 matrix summary and added `_HOT_CASCOR_PARAMS` and `_COLD_CASCOR_PARAMS` constants with the full enumeration in §5.1 of the proposal.

11. **Missing "unclassified key" defensive logging**. A future cascor param that canopy doesn't know about would fall through silently. Added the `unknown` set handling in `apply_params()` with a WARNING log.

12. **Missing Stage 0 in the rollout stages**. First draft jumped from "Phase A lands" to "Phase C lands." Added Stage 0 to make the sequence explicit and self-documenting.

### 13.2 Second pass findings (after first self-review)

13. **§5.6 scope conflict**. The source doc's §5.6 is broader than this proposal's hooks. Clarified in §7.3 that this is a subset, not a replacement, and does not require server-side changes for `set_params` specifically.

14. **Missing ordering guarantee between hot and cold in a mixed batch**. The adapter fires WebSocket first then REST; this was implicit. Added explicit "Ordering guarantee" paragraph in §5.1.

15. **Ambiguous behavior when flag is True but Phase B is not deployed**. Added §5.4 "What happens if the flag is on but Phase B is not done yet?" section. Self-healing because the fallback is unconditional.

16. **Missing test for the legacy `command()` method regression**. Added test A8 in §10.1 to gate the correlation-map refactor against a regression in the existing generic `command()` API.

17. **Missing operational acceptance criteria**. §10.1 and §10.2 are code/test criteria only. Added §10.3 for the stage-2/3 flag-flip operational criteria.

18. **Disagreement section was missing a disagreement**. First draft had 3 disagreements; added §12.4 (REST path preservation) and §12.5 (debounce location) for completeness.

19. **Risk table was thin**. Expanded from 8 risks to 14 with distinct scenarios: correlation-map leak, numpy scalar, private field leak, shutdown race, multi-replica thundering herd, etc.

20. **Missing explicit "do not cover" list at the top**. Added "Explicitly out of scope" paragraph in §1 Scope to keep the lane discipline clear.

### 13.3 Third pass findings (after second self-review)

21. **§4.1 method signature docstring was too terse for the public API**. Expanded to explain args, returns, raises, and notes. This is library-facing documentation and will ship in the SDK release.

22. **§4.3 timeout semantics missed a subtlety**. The outer timeout in `future.result(timeout=2.0)` must be >= the inner `set_params(..., timeout=1.0)`. Otherwise the outer fires first and the inner is orphaned. Added the explicit >= relationship in §5.3.

23. **§5.1 unknown-key fallback was written as REST but never explained why REST and not raise**. Added rationale: safe default; WARNING log surfaces the classification gap to operators; raising would break the adapter for a param that cascor accepts.

24. **§6.2 "no retries" could be misread as "SDK silently drops failed sends"**. Clarified: the SDK always raises on any failure; it is the application layer that decides not to retry. "No retries" is a statement about the SDK's behavior, not about the overall system behavior (which does retry via the fallback).

25. **§11 did not reference all the source-doc RISK IDs**. Cross-referenced RISK-03, RISK-09, RISK-13 explicitly in the R04 table and in prose.

26. **§9.1 sequencing step missing the coordination hand-off**. The Phase C implementation requires coordination with the sibling frontend agent to wire sliders. Added step 7 in §9.2.

27. **Missing note on who reads `_client_latency_ms`**. Added §7.1 explanation that canopy reads it and emits a Prometheus observation.

28. **RISK-11 (`request_id` unsupported by server) was missing**. Added R04-11 with explicit guidance about the release-ordering window.

29. **Missing verification criterion for R04-12 (adapter singleton)**. Not directly testable; documented as an invariant in the prose of §5.3.

30. **§4.4 coexistence section missed the rationale for `set_params` vs `update_params` naming**. Added the "wire command name" argument explicitly in §4.1.

### 13.4 Final consistency check

- All §-references are to sections that exist in the source doc (§1.4, §2.4, §2.5, §3.0, §3.2.3, §3.2.4, §5.1, §5.3.1, §5.6, §6.1, §6.4, §6.5, §9.1, §9.4, §9.12, §9.13, §10, §11).
- All GAP-WS references are to items that exist (GAP-WS-01, -09, -10, -22, -24, -30, -32).
- All RISK references exist (RISK-03, RISK-09, RISK-13).
- All M-SEC references are introductory (M-SEC-01, -02, -03) — referenced only as Phase B-pre prerequisite.
- Scope discipline: the proposal does not cover broadcaster locks, replay buffers, server_instance_id, Plotly wiring, dcc.Store wiring, Origin validation, CSRF, or authentication. Each is either out of scope (sibling agent) or referenced as a Phase B-pre prerequisite.
- Phase-C-is-P2 framing is consistent with §5.3.1 and §9.4.
- The proposal does not argue against the P2 downgrade; it ships the plumbing so the decision can be data-driven.
- The REST path is explicitly preserved as a first-class API per §9.5 symmetry.
- Feature flag is `Settings.use_websocket_set_params=False` default per §9.4.
- Rollback story is a single env-var flip with <2 minute MTTR.

No further corrections identified on the final pass.

---

**End of R0-04 proposal.**
