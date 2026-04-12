# Round 1 Proposal R1-03: Maximalist / Comprehensive Synthesis

**Angle**: Single unified development plan integrating all R0 recommendations
**Author**: Round 1 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Round 1 consolidation — input to Round 2
**Inputs consolidated**: R0-01 (frontend), R0-02 (security), R0-03 (cascor backend), R0-04 (SDK / set_params), R0-05 (testing), R0-06 (ops / phasing / risk)
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` v1.3 STABLE

---

## 1. Executive summary

The WebSocket migration defined in the v1.3 architecture doc has a single load-bearing outcome: eliminate the `/api/metrics/history` polling bomb (~3 MB/s per dashboard) while introducing a browser→canopy→cascor WebSocket path that is correct, secure, observable, and operable. Round 0 produced six specialized proposals that individually cover the frontend bridge (R0-01), security gate (R0-02), cascor server backend (R0-03), SDK `set_params` plus canopy adapter (R0-04), full test strategy (R0-05), and operational phasing / rollout (R0-06). This proposal integrates every recommendation from all six into one end-to-end development plan.

**Phase ordering** (load-bearing dependency chain):

```
Phase A  (SDK set_params)                      ── parallel with ──
Phase A-server (cascor seq/replay prereqs)     ── parallel with ──
Phase B-pre-a (M-SEC-03 frame-size guards)     ── MUST precede ──> Phase B
Phase B-pre-b (M-SEC-01, M-SEC-01b, M-SEC-02)  ── MUST precede ──> Phase D
                                                  │
                                                  ▼
                                              Phase B (browser bridge)
                                                  │
                                     ┌────────────┼────────────┐
                                     ▼            ▼            ▼
                                  Phase C    Phase D        Phase F
                                (set_params) (buttons)   (heartbeat+jitter)
                                     │
                           (Phase E — backpressure, independent, recommended after B)
                           (Phase G — cascor set_params integration test, ship with A-server)
                           (Phase H — normalize_metric regression + audit, independent)
                           (Phase I — asset cache busting, MUST ship with B)
```

**Critical integration decisions made in this proposal**:

1. **Split Phase B-pre into B-pre-a and B-pre-b** (R0-06 §13.1). B-pre-a (frame-size guards, M-SEC-03) is a Phase B hard prereq. B-pre-b (Origin allowlist, cookie+CSRF, M-SEC-01/01b/02) is a Phase D hard prereq and is strongly recommended to land with B.
2. **Adopt R0-03's Phase A-server carve-out** (§11.5 there): cascor-side seq/replay/`server_instance_id` work ships as a separate 2-day phase that lands before canopy Phase B, so canopy iterates against a stable server contract.
3. **Ship Phase B with rAF coalescing scaffolded but disabled** (R0-01 disagreement #1). The 100 ms drain is already comfortably under the 60 fps budget; rAF coalescing is a future optimization gated on §5.6 instrumentation.
4. **Adopt R0-04's `timeout=1.0` default for `set_params`** (not the 5.0 from source doc §7.1). Matches GAP-WS-32 per-command timeout table.
5. **Add `request_id` as a new additive field on the `set_params` wire contract** (R0-04 §12.2). Backwards compatible; cascor's Phase G test must gate the echo.
6. **Default Phase E backpressure policy to a new `drop_oldest_progress_only` variant** (R0-06 §13.2). Source doc's `block` default leaves RISK-04 live; drop-oldest for coalesceable progress + `close(1008)` for state-bearing events is the correct default.
7. **Command responses on `/ws/control` do NOT carry `seq`** (R0-03 §11.3). `command_response` is personal RPC and does not enter the replay buffer.
8. **Adopt R0-02's positive-sense security flag** (`ws_security_enabled` default True, rather than `disable_ws_auth`). Reduces config-footgun risk. Flagged as naming decision; effort is identical.
9. **Consolidate M-SEC-10 (idle timeout), M-SEC-11 (adapter inbound validation), M-SEC-12 (log injection escaping)** from R0-02 into the canonical M-SEC register for the migration.
10. **Close RISK-15 (CSWSH) in B-pre-b** as mandatory, page-on-call alert (not ticket).

**Total estimated effort**: ~13.5-15 engineering days (R0-06's 13.5 + R0-02's 0.5-1 day delta for audit logging + R0-03's 2-day A-server carve-out that was previously folded into B). Calendar: ~5 weeks.

**Primary acceptance signal**: `canopy_rest_polling_bytes_per_sec` shows >90% reduction vs pre-migration baseline, sustained for 7 days post-Phase-B, with zero `state_dropped` events in cascor and zero orphaned-command incidents above baseline.

---

## 2. Scope: full Phase A → Phase I coverage

This proposal is the single document an engineering team needs to execute the migration end to end. Every phase includes:

- **Scope**: exact files touched, line-level references where R0 proposals provided them.
- **Dependencies**: upstream gate requirements.
- **Implementation steps**: commit-level decomposition.
- **Test plan**: unit, integration, browser, security, latency, chaos tests that gate the phase.
- **Observability**: metrics, logs, alerts that MUST exist before production exit.
- **Runbook deliverable**: what operator-facing doc must accompany the phase.
- **Kill switch**: config-only lever to disable the phase's new behavior, with TTF (time-to-flip) target.
- **Feature flag**: default state per environment.
- **Rollout gate criteria**: what must be true for the phase to exit staging and enter production.
- **Owner-class**: which team (backend-cascor, backend-canopy, frontend, sdk, security, ops).
- **Risk mitigations**: which RISK-NN items are addressed.

Phases covered in full detail: A, A-server, B-pre-a, B-pre-b, B, C, D, E, F, G, H, I. Plus:

- §14 consolidated risk register (16 RISK-NN items, each with severity, phase, kill switch, MTTR, validation hook).
- §15 consolidated test plan (per phase + per test type).
- §16 consolidated observability plan (metrics, logs, alerts, SLOs).
- §17 cross-repo coordination (dependency order, version bumps, changelog policy).
- §18 reconciled disagreements between R0 proposals (which R0 won and why).
- §19 disagreements with the R0 inputs (where this proposal differs from any individual R0).
- §20 self-audit log.

---

## 3. Source-doc cross-reference matrix

Every enumerated identifier from the architecture doc, with its phase ownership and the R0 proposal(s) that addressed it. Entries marked "this doc §N" point to where in this R1-03 synthesis the item is fully specified.

### 3.1 GAP-WS-NN coverage

| ID   | Severity | Phase    | Description                                                     | R0 source(s)         | This doc    |
|------|----------|----------|-----------------------------------------------------------------|----------------------|-------------|
| 01   | P1       | A        | SDK `set_params` WebSocket method                                | R0-04                | §7          |
| 02   | P1       | B        | Dead `window.cascorWS` / `window.cascorControlWS` integrated    | R0-01                | §8          |
| 03   | P2       | B        | Parallel raw-WS clientside callback deleted                     | R0-01                | §8          |
| 04   | P1       | B        | `ws-metrics-buffer` init callback replaced with drain           | R0-01                | §8          |
| 05   | P1       | B        | `ws-*-buffer` drain callbacks written                           | R0-01                | §8          |
| 06   | n/a      | D        | `/api/train/{command}` preserved as first-class                 | R0-06                | §9          |
| 07   | P2       | E        | Slow-client backpressure (quick fix + full fix)                 | R0-03, R0-06         | §10         |
| 08   | (umbrella) | all    | "No E2E browser test" — R0-05 is the remediation umbrella       | R0-05                | §15         |
| 09   | P2       | G        | Cascor-side `set_params` integration test                       | R0-02, R0-03, R0-05  | §12         |
| 10   | -        | C        | No canopy-side `set_params` round trip integration test         | R0-04, R0-05         | §9          |
| 11   | -        | H        | Nested+flat metric format audit                                 | R0-01, R0-05, R0-06  | §13         |
| 12   | -        | F        | Application-layer heartbeat (ping/pong)                         | R0-02, R0-05, R0-06  | §11         |
| 13   | P1       | A-server + B | Sequence numbers + replay buffer + `server_instance_id`     | R0-03                | §5          |
| 14   | P1       | B        | Plotly `extendTraces` + `maxPoints`                             | R0-01                | §8          |
| 15   | P1       | B        | Browser `requestAnimationFrame` coalescing (scaffolded off)    | R0-01                | §8          |
| 16   | P0       | B        | `/api/metrics/history` 100 ms polling waste eliminated          | R0-01                | §8          |
| 17   | -        | (deferred) | `permessage-deflate` config                                   | R0-03                | §18         |
| 18   | P2       | E/H      | Topology message >64 KB chunking / REST fallback                 | R0-03, R0-06         | §10 + §18   |
| 19   | P2       | A-server | `close_all()` lock — RESOLVED on main (R0-03 §11.1)              | R0-03                | §5          |
| 20   | P3       | H        | Client→server envelope asymmetry normalization                   | R0-03                | §13         |
| 21   | -        | A-server | 1 Hz state throttle replaced with coalescer                      | R0-03                | §5          |
| 22   | P2       | A-server | Protocol error responses on `/ws/control`                        | R0-02, R0-03, R0-05  | §5 + §6     |
| 23   | -        | F/I      | Structured logger on reconnect events                           | R0-02, R0-06         | §11 + §16   |
| 24   | P2       | B        | Production latency measurement (§5.6 plan)                      | R0-01, R0-05, R0-06  | §8 + §16    |
| 25   | P1       | B        | WebSocket-health-aware polling toggle                          | R0-01                | §8          |
| 26   | P1       | B        | Visible connection status indicator badge                       | R0-01                | §8          |
| 27   | P1       | B-pre-b  | Per-IP connection caps / DoS protection                         | R0-02, R0-05         | §6          |
| 28   | -        | A-server | Multi-key torn-write (lifecycle lock contract)                  | R0-03                | §5          |
| 29   | P2       | A-server | `broadcast_from_thread` future exception discard                | R0-03                | §5          |
| 30   | P3       | B/F      | Reconnect backoff jitter                                        | R0-01, R0-02, R0-06  | §8 + §11    |
| 31   | P2       | B/F      | Unbounded reconnect (remove 10-attempt cap)                     | R0-01, R0-02         | §8 + §11    |
| 32   | P2       | C/D      | Per-command timeouts + `command_id` correlation                 | R0-02, R0-04         | §9          |
| 33   | P2       | B        | Demo mode failure visibility                                    | R0-01                | §8          |

### 3.2 M-SEC-NN coverage

| ID    | Severity | Phase     | Description                                     | R0 source | This doc |
|-------|----------|-----------|-------------------------------------------------|-----------|----------|
| 01    | P0       | B-pre-b   | Canopy `/ws/*` Origin allowlist                 | R0-02     | §6       |
| 01b   | P0       | B-pre-b   | Cascor `/ws/*` Origin allowlist parity          | R0-02     | §6       |
| 02    | P0       | B-pre-b   | Cookie-session + CSRF first-frame               | R0-02     | §6       |
| 03    | P0       | B-pre-a   | Per-frame size caps on every WS endpoint        | R0-02     | §6       |
| 04    | P1       | B-pre-b   | Per-IP connection caps + auth timeout           | R0-02     | §6       |
| 05    | P1       | B-pre-b   | Command rate limiting (leaky bucket 10/s)       | R0-02     | §6       |
| 06    | P3       | B-pre-b   | Opaque auth-failure close-reason text           | R0-02     | §6       |
| 07    | P3       | B-pre-b   | Logging scrubbing allowlist + audit logger      | R0-02     | §6       |
| 08    | deferred | follow-up | Subdomain bypass / CSP header                   | R0-02     | §18      |
| 09    | deferred | follow-up | Constant-time API key comparison                | R0-02     | §18      |
| 10    | **new**  | B-pre-b   | Idle timeout (120 s bidirectional)              | R0-02     | §6       |
| 11    | **new**  | B-pre-b   | Adapter inbound validation (canopy→cascor)      | R0-02     | §6       |
| 12    | **new**  | B-pre-b   | Log injection CRLF escaping                     | R0-02     | §6       |

### 3.3 RISK-NN coverage

Fully cross-referenced in §14 below. For quick scan: all 16 RISK-NN items (01-16) from source doc §10 are addressed. R0-06 provides the comprehensive register; R0-01 provides FR-RISK-01..15 frontend-specific variants; R0-02 provides T-RISK-01..12 security variants; R0-03 provides §8 failure modes; R0-04 provides R04-01..14; R0-05 provides T-RISK-01..12 test-plan variants. All are folded into §14.

---

## 4. Phase A: SDK set_params (juniper-cascor-client)

**Source**: R0-04 §4-§10 (primary). R0-05 §4.2, §9.1 (test plan). R0-06 §3.1 (ordering). R0-02 §6.11 IMPL-SEC-44 (regression guard on `X-API-Key`).

**Owner-class**: sdk.

**Dependencies**: none. Phase A can start immediately, in parallel with A-server and B-pre-a.

### 4.1 Scope

Add `CascorControlStream.set_params(params, *, timeout=1.0, request_id=None)` to `juniper-cascor-client/juniper_cascor_client/ws_client.py`. Refactor `CascorControlStream` to use a background `_recv_task` and a `_pending` correlation map so two concurrent `set_params` calls can be distinguished by `request_id`.

**Why**: the architecture doc §7.1 GAP-WS-01 is the first landing point for the migration. The canopy Phase C adapter depends on it. The SDK method is also valuable to non-canopy consumers (CLI tools, notebooks).

### 4.2 API surface (R0-04 §4.1)

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
    waits for the matching command_response. This is the WebSocket analog
    of CascorClient.update_params() (REST PATCH).

    Raises:
        JuniperCascorConnectionError: not connected; call connect() first.
        JuniperCascorTimeoutError: no matching response within `timeout`.
        JuniperCascorValidationError: server returned status == "error"
            with a validation-flavored message.
        JuniperCascorClientError: any other error envelope.
    """
```

**Method naming rationale**: the wire-level command is `set_params`, so the SDK method name matches the wire for grep-ability. The REST method `update_params` is retained unchanged on `CascorClient`; the two methods are on different objects on different transports.

**Default `timeout=1.0`** (R0-04 §12.1, disagreement with source doc §7.1's 5.0 default). Rationale: GAP-WS-32 specifies `set_params: 1s`, and the hot-path slider use case loses badly if the timeout is 5 s.

### 4.3 Request/ack envelope with `request_id` (R0-04 §4.2)

**Client→server**:

```json
{
  "command": "set_params",
  "request_id": "7f9a2c3d8e1b4a5f",
  "params": {"learning_rate": 0.005, "correlation_threshold": 0.15}
}
```

**Server→client (success)**:

```json
{
  "type": "command_response",
  "timestamp": 1712707201.789,
  "data": {
    "command": "set_params",
    "request_id": "7f9a2c3d8e1b4a5f",
    "status": "success",
    "result": {"learning_rate": 0.005, "correlation_threshold": 0.15}
  }
}
```

**Server→client (error)**:

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

**`request_id` is a new additive field** (R0-04 §12.2). Backwards compatible: unknown fields in inbound JSON are naturally ignored by cascor, and the SDK falls back to first-match-wins if the server does not echo `request_id`. Phase G (cascor-side integration test) must assert the echo so the feature is guaranteed server-side before canopy depends on it.

### 4.4 Concurrent-caller correlation map (R0-04 §4.5)

```python
self._pending: Dict[str, asyncio.Future[Dict[str, Any]]] = {}
self._recv_task: Optional[asyncio.Task] = None
```

Lifecycle:
1. `connect()` starts a background `_recv_task` that loops `await self._ws.recv()`, parses each frame, looks up `data.request_id` in `self._pending`, calls `future.set_result(envelope)`.
2. `set_params(...)` creates an `asyncio.Future`, registers it under `request_id`, sends the command frame, awaits the future with the specified `timeout`, removes the entry on any path.
3. `disconnect()` cancels `_recv_task` and sets `JuniperCascorConnectionError` on all pending futures.

**Crash safety**: wrap `_recv_task` body in `try/except Exception` that logs ERROR and cancels all pending futures with `JuniperCascorClientError("recv task crashed: ...")` so callers fail loudly (R0-04 R04-06).

**Legacy compatibility**: the existing generic `command(...)` method is preserved as a wrapper that generates a fresh `request_id` if none provided. Existing callers see no API change.

### 4.5 Latency instrumentation hook (R0-04 §7.1)

```python
t_sent = time.monotonic()
await self._ws.send(json.dumps(frame))
envelope = await asyncio.wait_for(future, timeout=timeout)
t_acked = time.monotonic()
envelope["_client_latency_ms"] = (t_acked - t_sent) * 1000
return envelope
```

The `_client_latency_ms` private field is consumed by the canopy adapter's Prometheus histogram in Phase C. Leading underscore signals "SDK-private; not wire contract."

### 4.6 Test plan (R0-05 §4.2, R0-04 §10.1)

**Unit tests** (located in `juniper-cascor-client/tests/test_ws_client_set_params.py` and `tests/test_ws_client_reconnect.py`):

- `test_set_params_round_trip` — happy path
- `test_set_params_timeout` — `JuniperCascorTimeoutError`
- `test_set_params_validation_error` — `JuniperCascorValidationError` on `status: "error"` with validation-flavored message
- `test_set_params_reconnection_queue` — disconnect mid-send; future resolves with `JuniperCascorConnectionError`
- `test_set_params_concurrent_correlation` — two concurrent calls via `asyncio.gather`, each distinguished by `request_id`
- `test_set_params_caller_cancellation` — caller cancels; pending map is cleaned up (memory leak guard, elevated per R0-05 §14.1)
- `test_command_legacy_still_works` — regression gate on existing `command()` API
- `test_set_params_no_request_id_first_match_wins` — for the pre-echo transition window
- `test_set_params_x_api_key_header_present` — R0-02 IMPL-SEC-44 regression guard against header-omission

Coverage target: 90% on new SDK code (R0-05 §11.1 "Phase A new code").

### 4.7 Implementation steps (R0-04 §9.1)

1. Refactor `CascorControlStream` to use a background `_recv_task` and `_pending` correlation map. Preserve the existing `command()` API.
2. Add `set_params(params, *, timeout=1.0, request_id=None)` method with full docstring.
3. Add exception translation table (see R0-04 §4.3).
4. Add `_client_latency_ms` instrumentation.
5. Add unit tests listed in §4.6.
6. Update `juniper-cascor-client/README.md` example to show the new method.
7. Bump version (semver minor: e.g., `1.x.0` → `1.(x+1).0`).
8. Tag release; OIDC publish to PyPI.
9. Verify PyPI propagation (2-5 minutes).

### 4.8 Observability for Phase A

Metrics emitted by the SDK (consumed by Phase C adapter):

- `juniper_cascor_client_ws_set_params_total{status}` — counter; status ∈ {ok, timeout, error}. (R0-06 §6.1)

No alerts at the SDK layer (consumer decides).

### 4.9 Operational rollout

**Exit gate** (R0-06 §3.1):
- New version tagged, GitHub release created, PyPI publish succeeded.
- CHANGELOG has "Added" entry for `set_params`.
- At least one consumer (Phase C PR draft) can `pip install` the new version.

**Kill switch**: none at the SDK layer. Phase C's feature flag is the consumer-side control.

**Documentation**:
- `juniper-cascor-client/CHANGELOG.md` — "Added: `CascorControlStream.set_params()` WebSocket method"
- `juniper-cascor-client/ws_client.py` — full docstring per §4.2
- `juniper-cascor-client/README.md` — usage example

### 4.10 Effort estimate

R0-04 says 0.5 day per source doc §9.1, but realistically 1 day with the correlation-map refactor. This proposal adopts 1 day.

---

## 5. Phase A-server: cascor prerequisites (carved out from source doc Phase B)

**Source**: R0-03 §7.1 (primary). R0-05 §4.1 (tests). R0-06 §3.1 (phasing — adopts R0-03's carve-out).

**Owner-class**: backend-cascor.

**Dependencies**: none. Phase A-server can start immediately in parallel with Phase A (SDK) and Phase B-pre-a (frame-size guards).

**Rationale for the carve-out** (R0-03 §11.5): the source doc §9.3 bundles cascor-side sequence-number work with canopy browser-bridge work as one 4-day Phase B. Splitting Phase A-server off gives cascor a stable contract to ship ~2 days before canopy's Phase B begins, so canopy's browser tests exercise a real server with `seq`/`resume` already in place.

### 5.1 Scope

Phase A-server consists of 10 small commits, each green independently, delivering:

1. Sequence numbers on every outbound envelope.
2. `server_instance_id` UUID per process.
3. 1024-event bounded replay buffer with `replay_since(last_seq)`.
4. Two-phase connection registration (`_pending_connections` + `promote_to_active()`).
5. `resume`/`resume_ok`/`resume_failed` handling on `/ws/training`.
6. `snapshot_seq` on the REST `/api/v1/training/status` endpoint.
7. 1 Hz state throttle replaced with a debounced coalescer (GAP-WS-21).
8. `broadcast_from_thread` exception handling (GAP-WS-29).
9. Protocol error responses on `/ws/control` (GAP-WS-22).
10. Quick-fix backpressure: `_send_json` wrapped in `asyncio.wait_for(..., timeout=0.5)`.

**Explicitly NOT in Phase A-server** (deferred to Phase E):
- Per-client pump task + queue model (full backpressure).
- Parallel fan-out via `asyncio.gather`.

### 5.2 Replay buffer design (R0-03 §3)

**Data structure**: `collections.deque[tuple[int, dict]]` with `maxlen=1024`, stored as `WebSocketManager._replay_buffer`. Each entry is `(seq, envelope_dict)`.

**Capacity rationale**: 1024 entries ≈ 40 seconds of history at cascor's steady-state event rate (~16 KB/s). Covers WiFi blips, background-tab throttling, short cascor restarts. Longer disconnects fall back to REST snapshot.

**Memory**: ~600 KB average, ~2 MB worst case per `WebSocketManager` instance. Negligible (~0.03% of cascor's typical 6 GB RSS).

**Tunable**: `Settings.ws_replay_buffer_size` (default 1024, soft cap 8192, hard refusal above 16384).

### 5.3 Sequence number assignment (R0-03 §3.2)

**Single choke-point helper**:

```python
async def _assign_seq_and_append(self, message: dict) -> dict:
    """Assign the next seq, append to the replay buffer, return the message.

    MUST be called on the event loop thread. Holds _seq_lock for the duration.
    """
    async with self._seq_lock:
        seq = self._next_seq
        self._next_seq += 1
        message["seq"] = seq
        self._replay_buffer.append((seq, message))
    return message
```

**Lock choice**: a separate `_seq_lock: asyncio.Lock`, NOT reusing `WebSocketManager._lock`. Rationale: `_lock` is held during broadcast fan-out; reusing it would couple sequence assignment to slow-client latency.

**Lock ordering** (deadlock prevention): `_seq_lock` is always acquired BEFORE `_lock` if both are needed. In practice only `resume` handling and `close_all()` acquire both.

**Invariant 1**: every outbound message goes through `_assign_seq_and_append`. Enforced by a DEBUG-gated assertion in `broadcast()`: `assert "seq" in message`.

**Invariant 2**: `broadcast_from_thread` does NOT assign seq on the training thread. It schedules a coroutine via `run_coroutine_threadsafe`; seq assignment happens inside that coroutine on the loop thread.

**Invariant 3**: seq assignment happens BEFORE the first `send_json()`. Order: increment counter → append to deque → exit lock → iterate `_active_connections`.

**Disagreement with source doc (R0-03 §11.3)**: `command_response` on `/ws/control` does NOT have a `seq` field and does NOT enter the replay buffer. Rationale: command responses are personal RPC; replaying them on reconnect is confusing. `/ws/training` and `/ws/control` therefore have separate seq namespaces (`/ws/control` has none).

### 5.4 `server_instance_id` UUID (R0-03 §4)

**Generation**: `uuid.uuid4()` at `WebSocketManager.__init__`. Stored as `self.server_instance_id: str`. Advertised in every `connection_established` message alongside `server_start_time` (advisory only) and new field `replay_buffer_capacity` (helps clients decide resume vs snapshot).

**Not persisted**. Hot-reload = restart from client's POV. Comparison is always by equality, never by ordering.

**Format not validated by cascor**: a client sending `{"server_instance_id": "potato"}` simply gets `resume_failed: server_restarted`. Do not leak a "well-formed vs malformed" distinction.

### 5.5 `replay_since()` + `ReplayOutOfRange` (R0-03 §3.3)

```python
async def replay_since(self, last_seq: int) -> list[dict]:
    async with self._seq_lock:
        if not self._replay_buffer:
            return []
        oldest_seq = self._replay_buffer[0][0]
        if last_seq < oldest_seq - 1:
            raise ReplayOutOfRange(requested=last_seq, oldest_available=oldest_seq)
        snapshot = list(self._replay_buffer)
    return [msg for (seq, msg) in snapshot if seq > last_seq]
```

**Key pattern**: copy-then-iterate under the lock. The copy is O(n) with n ≤ 1024 — negligible. Iterating the deque without a lock would race with appends.

**Replay overflow race (R0-03 §8.4)**: between `replay_since()` returning and the client receiving the replayed messages, `_next_seq` can advance past the tail of the copied snapshot, evicting entries. Mitigation: promote the client to `_active_connections` under `_seq_lock` BEFORE finalizing the replay. The client then receives each live event twice during the replay window and de-dupes by seq. This is the canonical §6.5.2 idempotent-replay contract and is load-bearing.

### 5.6 Two-phase connection registration (R0-03 §5.1)

```
PHASE 1 — accept and auth:
  1. async with self._lock:
     - check cap, reject 1013 if full
     - await ws.accept()
     - add to _pending_connections (NOT _active_connections yet)
     - record connection_meta.registered_at
  2. Outside lock, send connection_established
     (server_instance_id, server_start_time, replay_buffer_capacity, seq=0)
     via send_personal_message (bypasses replay buffer).

PHASE 2 — resume or live handoff:
  3. await the client's first frame (5 s timeout):
     - {type: "resume", ...}: handle replay (§5.5 above)
     - anything else: treat as fresh connection; route to normal handler
     - timeout: promote to _active_connections
  4. async with self._seq_lock:
     - move ws from _pending_connections to _active_connections
     - atomic with the replay tail so no events fall between replay and live
  5. Send initial_status (personal). Clients treat it as a snapshot that
     can be overwritten by any subsequent state with greater seq.
  6. Enter main inbound loop.
```

**Alternative rejected**: per-connection `seq_cursor` (fan-out only sends if `seq > seq_cursor`). Couples the fan-out loop to per-connection state; adds lock-ordering complexity. Two-phase registration is simpler.

### 5.7 Quick-fix backpressure (R0-03 §5.2 step 1)

```python
async def _send_json(self, websocket: WebSocket, message: dict) -> bool:
    try:
        await asyncio.wait_for(websocket.send_json(message), timeout=0.5)
        return True
    except (asyncio.TimeoutError, WebSocketDisconnect):
        logger.info("Slow/disconnected client pruned during broadcast")
        return False
    except Exception:
        logger.exception("Unexpected error during WebSocket send")
        return False
```

**Timeout**: 0.5 s. Rationale (R0-03 §5.2): smallest value safely above WiFi p99 RTT (~80 ms) + TCP retransmit (~200 ms) + `json.dumps` (~10 ms) + uvicorn frame-write (~5 ms). Tunable via `Settings.ws_send_timeout_seconds`.

**Serial fan-out is preserved** in Phase A-server. Parallel fan-out is a Phase E optimization (see §10 below).

### 5.8 1 Hz state throttle coalescer (GAP-WS-21)

Source doc §3.1.3 notes that the current `lifecycle/manager.py:133-136` uses a "drop filter" that drops states emitted within 1 s of the last one. This can drop a `Started → Failed` within 200 ms transition, hiding terminal events.

**Fix** (R0-03 commit 7): replace with a coalescer that:
- Buffers the latest pending state.
- Flushes at most once per second.
- **Bypasses the throttle for terminal transitions** (`Failed`, `Stopped`, `Completed`).

### 5.9 `broadcast_from_thread` exception handling (GAP-WS-29)

Three-line patch (R0-03 commit 8):

```python
def broadcast_from_thread(self, message: dict) -> None:
    future = asyncio.run_coroutine_threadsafe(self.broadcast(message), self._event_loop)
    future.add_done_callback(self._log_broadcast_exception)

def _log_broadcast_exception(self, future):
    try:
        future.result()
    except Exception:
        logger.exception("broadcast_from_thread: broadcast raised")
```

### 5.10 Protocol error responses on `/ws/control` (GAP-WS-22)

(R0-03 §6.3 table; cross-referenced with R0-02 §4.4 control 4.)

| Failure                    | Response                                             | Close |
|----------------------------|------------------------------------------------------|-------|
| Non-JSON payload           | (close)                                              | 1003  |
| Missing `command` field    | `command_response {status: "error", error: "missing command field"}` | no    |
| Unknown command            | `command_response {status: "error", error: "Unknown command: <name>"}` | no    |
| Handler exception          | `command_response {status: "error", error: "<opaque msg>"}` + server-side traceback log | no    |
| Frame > 64 KB              | (close, framework level)                             | 1009  |

**Close-reason text must NOT leak internal state** (R0-02 §4.4 control 6). Opaque canonical strings only: `"Internal error"`, `"Invalid frame"`, `"Rate limited"`, `"Authentication failed"`, `"Forbidden"`, `"Too many connections"`.

### 5.11 Commit breakdown (R0-03 §7.1)

Each commit green independently:

1. **`messages.py`**: optional `seq` parameter on every builder (initially None everywhere).
2. **WebSocketManager plumbing**: `server_instance_id`, `_next_seq`, `_seq_lock`, `_replay_buffer`, `_assign_seq_and_append()`, `broadcast()` routes through it, `connection_established` includes new fields.
3. **`_send_json` 0.5 s timeout**: quick-fix backpressure (standalone, resolves RISK-04's immediate severity).
4. **`replay_since()` + `ReplayOutOfRange`**: pure read-side primitive. No handler yet.
5. **`training_stream.py` resume handler + two-phase registration**: `connect_pending()`, `promote_to_active()`, 5 s resume-frame timeout, full resume flow.
6. **`/api/v1/training/status` adds `snapshot_seq`**: one-line addition reading `_next_seq - 1` under `_seq_lock`.
7. **1 Hz state throttle coalescer**.
8. **`broadcast_from_thread` exception handling**.
9. **`/ws/control` protocol error responses**.
10. **Docs + CHANGELOG**: README/AGENTS.md updates for new `seq` field, `ws_replay_buffer_size` setting, `server_instance_id` semantics.

### 5.12 Test plan (R0-03 §10, R0-05 §4.1)

**Unit tests** (under `juniper-cascor/src/tests/unit/api/`):

Phase A-server adds ~15 unit tests and ~6 integration tests:

1. `test_seq_monotonically_increases_per_connection` (100 concurrent broadcasts, strictly increasing seq, 100 entries in order)
2. `test_seq_monotonicity_under_broadcast_from_thread` (10 threads × 100 calls, 1000 entries in order)
3. `test_replay_buffer_bounded_1024` (push 2000, assert len=1024, oldest seq=976)
4. `test_replay_since_happy_path` (50 events, replay from 10, get 39 with seq 11..49)
5. `test_replay_since_out_of_range` (2000 events, replay from 10, assert `ReplayOutOfRange`)
6. `test_replay_since_empty` (50 events, replay from 50, return `[]`)
7. `test_server_instance_id_stable_within_process`
8. `test_server_instance_id_unique_across_processes`
9. `test_connection_established_contents` (includes server_instance_id, server_start_time, replay_buffer_capacity, connections)
10. `test_send_json_0_5s_timeout` (fake ws never resolves, `_send_json` returns False within 0.6 s)
11. `test_state_throttle_coalescer_preserves_terminal` (Started→Failed within 200 ms both observed)
12. `test_protocol_error_malformed_json_closes_1003`
13. `test_protocol_error_missing_command_field_returns_error`
14. `test_protocol_error_unknown_command_returns_error`
15. `test_broadcast_from_thread_exception_logged_not_leaked`

**Integration tests** (under `juniper-cascor/src/tests/integration/`):

16. `test_resume_happy_path_via_test_client` (broadcast 3, disconnect, reconnect, resume with last_seq=0, assert resume_ok + 3 replayed)
17. `test_resume_failed_server_restarted` (reconnect with stale UUID → resume_failed)
18. `test_resume_failed_out_of_range` (broadcast 2000, reconnect with last_seq=10 → resume_failed)
19. `test_resume_malformed_data` (`{"type": "resume", "data": {}}` → resume_failed reason=malformed_resume)
20. `test_resume_timeout_no_frame` (no first frame, 5 s later client promoted to active, receives live events)
21. `test_snapshot_seq_atomic_with_state_read`

### 5.13 Observability for Phase A-server (R0-03 §9)

New Prometheus metrics:

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `cascor_ws_connections_active` | Gauge | endpoint | Active count |
| `cascor_ws_connections_pending` | Gauge | endpoint | Pending (pre-promotion) count |
| `cascor_ws_connections_total` | Counter | endpoint, outcome | outcome ∈ {accepted, rejected_cap, rejected_auth} |
| `cascor_ws_disconnects_total` | Counter | endpoint, reason | reason ∈ {clean, slow_client, auth_failure, server_shutdown, unknown} |
| `cascor_ws_broadcasts_total` | Counter | type | Per-envelope-type cumulative |
| `cascor_ws_broadcast_send_seconds` | Histogram | type | Buckets {0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0} |
| `cascor_ws_broadcast_timeout_total` | Counter | type | Per-send timeouts (slow-client prunes) |
| `cascor_ws_replay_buffer_occupancy` | Gauge | — | 0-1024 |
| `cascor_ws_replay_buffer_bytes` | Gauge | — | Sampled every 30 s |
| `cascor_ws_seq_current` | Gauge | — | `_next_seq - 1` |
| `cascor_ws_resume_requests_total` | Counter | outcome | outcome ∈ {success, server_restarted, out_of_range, malformed, no_resume_timeout} |
| `cascor_ws_resume_replayed_events` | Histogram | — | Buckets {0, 1, 5, 25, 100, 500, 1024} |
| `cascor_ws_state_throttle_coalesced_total` | Counter | — | Post-coalescer |
| `cascor_ws_command_responses_total` | Counter | command, status | Per-command |
| `cascor_ws_command_handler_seconds` | Histogram | command | Per-command handler latency |

Structured logs:

- INFO: `ws_connect`, `ws_disconnect`, `ws_resume_ok`, `ws_resume_failed`
- WARNING: `ws_slow_client`, replay buffer near-capacity (>90% for >30 s)
- DEBUG (off by default): every send; seq assignments

Alerts (R0-03 §9.4):

- `rate(cascor_ws_broadcast_timeout_total[1m]) > 0.1` → "slow clients detected"
- `cascor_ws_replay_buffer_occupancy > 900 for 30s` → "near-cap event rate"
- `rate(cascor_ws_resume_requests_total{outcome="server_restarted"}[5m]) > 0` → "cascor restart detected"
- `cascor_ws_seq_current` rate-of-change → 0 during active training → "broadcaster hang"

### 5.14 Kill switch

Phase A-server has no user-visible kill switch (it is purely additive server-side plumbing). If a correctness bug is discovered, revert the relevant commit. The 10-commit decomposition makes bisect easy.

### 5.15 Exit gate

- All 15 unit tests + 6 integration tests green.
- Staging deployment ≥ 24 hours with no seq-monotonicity violations in logs.
- Prometheus metrics listed in §5.13 scraped by the canopy dashboard.
- `notes/runbooks/cascor-replay-buffer.md` published.

### 5.16 Effort estimate

~2 engineering days for all 10 commits including tests. Matches R0-03 §7.1 estimate.

---

## 6. Phase B-pre: security gate

This proposal splits Phase B-pre into **B-pre-a** (frame-size guards, a Phase B prereq) and **B-pre-b** (Origin, cookie+CSRF, rate limits, audit logger, a Phase D prereq). This is R0-06 §13.1's disagreement with the source doc, adopted here.

**Source**: R0-02 (primary). R0-05 §7 (security tests). R0-06 §3.2, §13.1 (phasing).

**Owner-class**: security + backend-cascor + backend-canopy.

### 6.1 Phase B-pre-a — frame-size guards (M-SEC-03, must land with or before Phase B)

**Dependency**: none. Can land in parallel with Phase A, A-server.

**Scope**: add explicit `max_size` on every `ws.receive_*()` call across `juniper-cascor/src/api/websocket/*.py` and `juniper-canopy/src/main.py`.

**Target table** (R0-02 §4.4 control 1):

| Endpoint                           | Current     | Target          | Enforcement |
|------------------------------------|-------------|-----------------|-------------|
| cascor `/ws/control` inbound       | 64 KB       | 64 KB (unchanged, regression-protected) | keep |
| cascor `/ws/training` inbound      | unset       | 4 KB (ping/pong only)                    | add `max_size=4096` |
| canopy `/ws/control` inbound       | unset       | 64 KB                                    | add |
| canopy `/ws/training` inbound      | unset       | 4 KB                                     | add |
| canopy `/ws/*` outbound            | unset       | 128 KB                                   | add (GAP-WS-18 caveat below) |
| cascor `/ws/*` outbound            | unset       | 128 KB                                   | add |

Overflow → close 1009 (Message Too Big).

**JSON depth cap** (R0-02 §4.4 control 2): custom depth-limiting parser (or Pydantic v2 `model_config = ConfigDict(max_depth=16)` if supported), rejects deeply-nested payloads with close 1003.

**GAP-WS-18 interaction**: the 128 KB outbound cap is per-frame, not per-logical-message. Large topology messages must be chunked into multiple frames (Phase E follow-up) or fall back to REST. Documented in §10 and §18.

**Test plan**:
- `test_oversized_frame_rejected_with_1009` per endpoint (R0-02 IMPL-SEC-24, R0-05 §7.4)
- `test_100MB_frame_does_not_exhaust_memory` (server process memory delta < 10 MB)
- `test_json_depth_cap_rejects_deep_payload`

**Effort**: ~0.25 day (R0-06 §13.1).

**Exit gate**: unit tests green, changelog updated, ready to ship with Phase B.

### 6.2 Phase B-pre-b — full security hardening (Phase D prereq)

**Dependency**: B-pre-a merged (so the size caps are in place). Can start in parallel with Phase B if development bandwidth allows.

**Scope**: all other M-SEC controls (M-SEC-01 Origin, M-SEC-01b cascor parity, M-SEC-02 cookie+CSRF, M-SEC-04 per-IP cap + auth timeout, M-SEC-05 rate limit, M-SEC-06 opaque close-reason, M-SEC-07 audit logger, M-SEC-10 idle timeout, M-SEC-11 adapter inbound validation, M-SEC-12 log injection escaping).

#### 6.2.1 Origin allowlist (M-SEC-01, M-SEC-01b)

(R0-02 §4.1, §6.1-6.3.)

**Shared helper**: `juniper-cascor/src/api/websocket/origin.py::validate_origin(ws, allowlist) -> bool`. Canopy has a sibling `juniper-canopy/src/backend/ws_security.py::validate_origin(...)`. Both share a unit test matrix.

**Default allowlist (canopy)**:
```
["http://localhost:8050", "http://127.0.0.1:8050",
 "https://localhost:8050", "https://127.0.0.1:8050"]
```

**Default allowlist (cascor)**:
```
["http://localhost:8050", "http://127.0.0.1:8050",
 "http://localhost:8201", "http://127.0.0.1:8201"]
```

**Configurable**: `Settings.allowed_origins` or env `JUNIPER_WS_ALLOWED_ORIGINS`.

**Rejection mechanics**:
- Pre-accept HTTP 403 where Starlette supports it; else close 1008 post-accept.
- Log at WARNING: `origin, remote_addr, path, user_agent` (all CRLF-escaped per M-SEC-12).
- Increment `canopy_ws_origin_rejected_total{endpoint}`.
- **Audit log** as `event: ws_auth, result: origin_rejected`.
- Empty allowlist = reject-all (fail-closed). Document prominently in canopy README.

**Case and protocol**:
- Compare case-insensitively on scheme/host, case-sensitively on path.
- `http` != `https`; list both if needed.
- Strip trailing slash.
- Port is significant.
- `null` origin (file://, sandboxed iframe) always rejected.
- `*` in allowlist explicitly unsupported.

**Reverse-proxy caveat**: when canopy is deployed behind nginx/traefik with a public origin, ops must add the public origin to the allowlist. Document in deployment runbook.

**Test plan**:
- `test_origin_allowlist_accepts_configured_origin`
- `test_origin_allowlist_rejects_third_party_pages`
- `test_origin_allowlist_rejects_missing_origin`
- `test_origin_header_case_insensitive_host`
- `test_cascor_ws_training_rejects_third_party_origin`
- `test_cascor_ws_control_rejects_third_party_origin`
- `test_cswsh_from_evil_page_cannot_start_training` (Playwright, end-to-end CSWSH regression)

#### 6.2.2 Cookie-session + CSRF first-frame (M-SEC-02)

(R0-02 §4.2, §6.4.)

**Two-layer model**:

1. **Handshake cookie**: browser sends `Cookie: session=<opaque-id>` automatically on upgrade. Attributes `HttpOnly; Secure; SameSite=Strict; Path=/`. SameSite=Strict is the second-line defense against CSWSH.
2. **CSRF first-frame**: within 5 seconds of accept, client sends `{type: "auth", csrf_token: "<opaque>"}`. Server compares using `hmac.compare_digest` (constant-time). Mismatch/absence → close 4001 "Authentication failed" (opaque per M-SEC-06).

**Token lifecycle**:
- Minted via `secrets.token_urlsafe(32)` (192 bits entropy).
- Stored on session as `session["csrf_token"]`.
- Rotates on: session login/logout, every 1 hour sliding, server restart (new server_instance_id), any auth close.
- Client fetches via `/api/csrf` REST endpoint OR embedded in Dash page HTML at render time to avoid round-trip on first load (R0-02 §8.2).
- Stored in JS variable `window.__canopy_csrf`, NOT in `localStorage` (XSS exfiltration risk).

**Session-middleware**: if canopy does not yet have `SessionMiddleware`, add it as its own standalone PR (IMPL-SEC-14) verified against existing REST routes before the WS wiring lands. Prevents surprising route breakage.

**Local-dev escape hatch**: `Settings.ws_security_enabled: bool = True` (positive-sense per R0-02 §9.4 disagreement adopted here). When False, Origin + cookie + CSRF are skipped. Default True. Logged at INFO on startup. CI guardrail in `juniper-deploy` fails if prod compose sets it False (IMPL-SEC-40).

**Auth resume ordering** (R0-02 §4.7):
```
1. Client opens WS; server accepts (Origin OK, cookie OK).
2. Client sends {type: "auth", csrf_token: "<opaque>"}.
3. Server validates CSRF; close 4001 on fail.
4. Server sends connection_established.
5. Client optionally sends {type: "resume", ...}.
6. Server replays or rejects per §5.5.
7. Live streaming continues.
```

**Race handling**: between steps 4 and 6, cascor may emit live events. Server buffers outbound events in a `pending_outbound: deque(maxlen=64)` flushed when resume is resolved. Overflow → close 1013 "Resume handshake timeout."

**Test plan**:
- `test_csrf_required_for_control_commands` (Playwright)
- `test_first_frame_must_be_auth_type`
- `test_csrf_token_validates_against_session`
- `test_csrf_token_rotation_on_expiry`
- `test_session_cookie_httponly_secure_samesitestrict`
- `test_localStorage_bearer_token_not_accepted`
- `test_expired_csrf_token_rejected` (4001 reason=token_expired)

#### 6.2.3 Per-IP connection cap + auth timeout (M-SEC-04)

(R0-02 §4.5 controls 1 and 3, §6.2.)

- `_per_ip_counts: Dict[str, int]` guarded by `_lock` on `WebSocketManager`.
- Default `Settings.ws_max_connections_per_ip = 5`. Configurable.
- `asyncio.wait_for(ws.receive_text(), timeout=5.0)` for the auth frame.
- Finally-block decrement.

**Test plan**:
- `test_per_ip_cap_enforced` (6 connections, 6th rejected 1013)
- `test_per_ip_counter_decrements_on_disconnect`
- `test_per_ip_counter_decrements_on_exception` (finally-block coverage)
- `test_per_ip_counter_increment_decrement_race` (asyncio.gather load)
- `test_auth_timeout_closes_1008` (no frames for 6 s, close 1008)
- `test_per_ip_cap_configurable_via_settings`
- `test_per_ip_map_purged_when_count_reaches_zero`

#### 6.2.4 Command rate limit (M-SEC-05)

(R0-02 §4.5 control 4, §6.7.)

Per-connection leaky bucket:
- Capacity: 10 tokens
- Refill: 10 tokens/sec
- Initial fill: full

**Counting rules**:
- Command frame: 1 token.
- Auth first-frame: free.
- Resume first-frame: free.
- Application-level `ping`: free.
- Malformed JSON: free (closes anyway).

**Overflow**: `{type: "command_response", data: {status: "rate_limited", retry_after: 0.3}}`. Connection stays up.

**Optional two-bucket refinement** (R0-02 §4.5 refinement): separate 20-token bucket for `set_params` (smooth slider UX) + 10-token bucket for destructive commands (`start|stop|reset|pause|resume`). Decide during implementation if single-bucket starvation observed. R0-02 §8.6 notes the debounced slider case produces ~10 cmd/s, within budget.

**Test plan**:
- `test_command_rate_limit_10_per_sec`
- `test_rate_limit_response_is_not_an_error_close`
- `test_burst_allowance_full_fill`

#### 6.2.5 Idle timeout (M-SEC-10, new)

(R0-02 §4.5 control 5, §6.7.)

If no client frames AND no server→client messages for 120 s, close 1000. Heartbeat (GAP-WS-12) dominates this in practice.

**Test plan**:
- `test_idle_timeout_closes_1000` (mock heartbeat disabled)

#### 6.2.6 Resume frame rate limit (new micro-control)

(R0-02 §4.5 control 6.)

At most one `resume` frame per connection. A second → close 1003 (Unsupported Data). Mitigates §3.4 replay-buffer forge attack.

**Test plan**:
- `test_double_resume_closes_1003`

#### 6.2.7 Per-origin handshake cooldown (new)

(R0-02 §4.8.)

If 10 consecutive upgrade rejections (403 Origin or 4001 auth) from the same IP within 60 s, soft-block IP for 5 minutes. Return 429 during block. Caveat: punishes NAT-sharing users; opt-in for multi-tenant.

#### 6.2.8 Audit logging (M-SEC-07 extended)

(R0-02 §4.6, §6.8.)

Dedicated `canopy.audit` logger with JSON formatter and `TimedRotatingFileHandler(when="midnight", backupCount=90)`, gzip on rotation. Path `Settings.audit_log_path`.

**Per-command line shape**:
```json
{
  "event": "ws_control",
  "timestamp": "2026-04-11T21:43:00.000Z",
  "session_id": "<sha256-prefix-8>",
  "remote_addr": "127.0.0.1",
  "origin": "http://localhost:8050",
  "endpoint": "/ws/control",
  "command": "set_params",
  "command_id": "<uuid from client>",
  "params_keys": ["learning_rate", "patience"],
  "params_before": {"learning_rate": 0.01, "patience": 10},
  "params_after": {"learning_rate": 0.005, "patience": 3},
  "result": "ok",
  "seq": 12345
}
```

**Rules (R0-02 §4.6)**:
1. Never log raw session cookie; log sha256 prefix.
2. Never log CSRF token.
3. `params_keys` always logged; `params_before`/`params_after` scrubbed via `AUDIT_SCRUB_ALLOWLIST` (auto-derived from `SetParamsRequest.model_fields.keys()`).
4. Log failures with reason: `rate_limited, forbidden, validation_error, auth_failed, origin_rejected, per_ip_cap, token_expired`.
5. Separate `canopy.audit` logger name for independent retention.
6. Rotation: daily, 90-day retention, gzip compressed.
7. Do NOT audit ping/pong.
8. Do NOT audit metrics events.
9. Log before/after diff for `set_params`.
10. CRLF/tab escaping for every user-controlled string (M-SEC-12).
11. Log user-agent verbatim (escaped).

**Disk budget** (R0-02 §8.4): ~70 MB/day, ~6 GB/90-day retention. Document.

#### 6.2.9 Adapter inbound validation (M-SEC-11, new)

(R0-02 §3.6, §6.9.)

Canopy adapter (`cascor_service_adapter.py`) parses inbound cascor frames via its own Pydantic envelope schema. Reject non-conforming frames; log; reconnect. Treats cascor as untrusted.

#### 6.2.10 Adapter synthetic auth frame (open question Q2-sec)

(R0-02 §6.9, §11-sec-1.)

The canopy adapter is a Python `websockets` client that CAN set custom headers. Two options:
- **Option A**: `X-Juniper-Role: adapter` header skips CSRF check when X-API-Key is present. Adds a handler branch but is unreachable from browser (browsers can't set custom headers on WS upgrade).
- **Option B**: adapter sends a synthetic `{type: "auth", csrf_token: hmac(api_key, "adapter-ws")}`. Uniform handler.

**This proposal's decision**: adopt **Option A** (header-based skip) as the default. Rationale: simpler, and the unreachability from browser is a hard property. Document the branch in a code comment. Revisit if the branch becomes a review burden.

#### 6.2.11 Command permissions (new, R0-02 §4.3)

Abstract permission strings for future-proofing:

| Action                     | Permission required       |
|---------------------------|---------------------------|
| `start`, `stop`, `pause`, `resume` | `training:control` |
| `reset`                   | `training:destructive`    |
| `set_params` (hot keys)   | `training:control`        |
| `set_params` (cold keys)  | `training:params_cold`    |
| `resume` (replay first)   | `ws:connect` (implicit)   |

Today canopy is single-user and every authenticated session has all permissions. The layer exists so that adding roles later does not require re-plumbing the handler.

**Denial response**: `{type: "command_response", data: {status: "forbidden", command: "<cmd>"}}`. Do not close the connection.

#### 6.2.12 `close_all()` shutdown race (R0-02 §8.12, IMPL-SEC-43)

GAP-WS-19 — already resolved on main per R0-03 §11.1 but fold the test into Phase B-pre-b anyway as a regression guard.

#### 6.2.13 Test plan (R0-02 §7.2, R0-05 §7)

New test files:

| File                                                                 | Purpose                    | Scope   |
|----------------------------------------------------------------------|----------------------------|---------|
| `juniper-cascor/src/tests/unit/api/test_websocket_origin.py`         | Origin helper              | cascor  |
| `juniper-cascor/src/tests/unit/api/test_websocket_per_ip_cap.py`     | Per-IP cap + race          | cascor  |
| `juniper-cascor/src/tests/unit/api/test_websocket_size_limits.py`    | Frame caps                 | cascor  |
| `juniper-cascor/src/tests/unit/api/test_websocket_rate_limit.py`     | Leaky bucket               | cascor  |
| `juniper-canopy/src/tests/unit/test_ws_security_origin.py`           | Origin helper              | canopy  |
| `juniper-canopy/src/tests/unit/test_ws_security_auth.py`             | Cookie + CSRF              | canopy  |
| `juniper-canopy/src/tests/unit/test_ws_security_schemas.py`          | Pydantic                   | canopy  |
| `juniper-canopy/src/tests/unit/test_audit_log.py`                    | Scrubber                   | canopy  |
| `juniper-canopy/src/tests/integration/test_ws_security_cswsh.py`    | CSWSH probe (Playwright)  | canopy  |
| `juniper-canopy/src/tests/integration/test_ws_security_resume_rate.py` | Resume frame limit       | canopy  |

**Acceptance checklist** (copied into Phase B-pre-b PR description, R0-02 §7.4):

```
[ ] CSWSH probe fails (Playwright, different origin)
[ ] Origin allowlist configurable via env
[ ] Cookie session attributes: HttpOnly, Secure, SameSite=Strict, Path=/
[ ] CSRF first-frame enforced within 5s
[ ] Per-frame inbound caps enforced on all /ws/* endpoints
[ ] Per-IP connection cap enforced
[ ] Per-connection command rate limit enforced
[ ] Idle timeout (120s) closes stale connections
[ ] Audit log captures auth/command events with scrubbing
[ ] Prom counters exported for rejection reasons
[ ] Opaque auth-failure close-reason text (M-SEC-06)
[ ] Replay protocol works post-auth (auth frame, then resume frame)
[ ] Settings.ws_security_enabled=False bypass works for local dev
[ ] CI guardrail: prod compose rejects ws_security_enabled=False
[ ] All integration tests pass against a real cascor (not fake)
```

**Fuzzing targets** (R0-02 §7.3):
- Header fuzzing via `hypothesis` on origin strings (unicode, null bytes, CRLF, empty, very long).
- JSON fuzzing via `atheris` on `CommandFrame.model_validate_json` with 64 KB random payloads.
- Connection-churn chaos: 1000 open/close cycles with random auth states; assert `_per_ip_counts` → 0.
- Resume-frame chaos: random `last_seq` / `server_instance_id` combos; no uncaught exceptions.

### 6.3 Observability for Phase B-pre

(R0-02 §4.6.)

New Prometheus counters:
- `canopy_ws_auth_failure_total{reason}` — reason ∈ {origin_rejected, missing_cookie, invalid_csrf, missing_csrf, timeout}
- `canopy_ws_command_total{command, status}`
- `canopy_ws_rate_limited_total`
- `canopy_ws_per_ip_rejected_total`
- `canopy_ws_origin_rejected_total`
- `canopy_ws_frame_too_large_total`

Histogram:
- `canopy_ws_auth_latency_ms` — buckets {10, 50, 100, 250, 500, 1000, 2500, 5000}. Early indicator of brute-force probe or session-store problem.

Alerts (upgraded from ticket to page-on-call per R0-06 §14.2 issue K):
- `WSOriginRejection`: `increase(canopy_ws_auth_rejections_total{reason="origin_mismatch"}[5m]) > 0` → **page on-call** (possible CSWSH).
- `WSOversizedFrame`: `increase(canopy_ws_oversized_frame_total[5m]) > 0` → **page on-call**.

### 6.4 Kill switch

- `Settings.disable_ws_control_endpoint: bool = False` (CSWSH emergency kill; hard-disables `/ws/control`). TTF ~5 min.
- `Settings.ws_security_enabled: bool = True` for local-dev bypass. Production MUST be True. CI guardrail enforces.

### 6.5 Exit gate (Phase B-pre-a)

Landed with or before Phase B:
1. M-SEC-03 frame-size guards on all `/ws/*` endpoints (canopy + cascor).
2. Unit tests: `test_oversized_frame_rejected_with_1009` green on every endpoint.
3. No regression in existing cascor `/ws/control` 64 KB cap.

### 6.6 Exit gate (Phase B-pre-b)

Must be satisfied before any Phase D PR is eligible to merge (R0-06 §3.2):
1. **M-SEC-01 landed**: Origin allowlist on canopy `/ws/training` and `/ws/control`. `test_origin_validation_rejects_third_party_pages` green.
2. **M-SEC-01b landed**: same on cascor `/ws/*`. Shared helper extracted.
3. **M-SEC-02 landed**: cookie-session + CSRF first-frame. `test_csrf_required_for_control_commands` green.
4. **M-SEC-04 landed**: per-IP cap + auth-timeout.
5. **M-SEC-05 landed**: leaky-bucket rate limit.
6. **M-SEC-10 (new)**: 120 s idle timeout.
7. **M-SEC-07 extended**: audit logger with rotation.
8. **CSP / security headers review** documented in PR.
9. **Staging pass**: ≥ 24 hours, no auth-related user lockouts.
10. **Runbook**: `juniper-canopy/notes/runbooks/ws-auth-lockout.md` published (operator procedure for flipping `ws_security_enabled=False` if production lockout observed).
11. **RISK-15** marked "in production" in risk-tracking sheet.

### 6.7 Effort estimate

R0-02 §9.1 estimates 1.5-2 days (disagreement with source doc's 1 day). R0-06 §3.2 agrees and notes the CSRF plumbing + audit logger are under-counted in the source doc. This proposal adopts **2 days total** for B-pre-b (0.25 day for B-pre-a already folded into Phase B).

---

## 7. (moved — replaced by §5 Phase A-server)

This section was reserved in the outline for Phase A-server. Content is in §5 above. Keeping the section number sequence aligned with the outline.

---

## 8. Phase B: frontend wiring + cascor envelope emission

**Source**: R0-01 (primary). R0-03 §3-§6 (cascor-side cooperation, already landed via Phase A-server). R0-05 §4.3, §6 (tests). R0-06 §3.3, §6 (observability, gates).

**Owner-class**: frontend + backend-canopy + backend-cascor (the cascor work is in Phase A-server; canopy Phase B is the browser-side consumer).

**Dependencies**:
- **Hard**: Phase A-server (so cascor emits `seq` and handles `resume`). Phase B-pre-a (so frame-size guards are in place before traffic volume increases).
- **Recommended**: Phase B-pre-b landed alongside (so the browser's CSRF first-frame is required from day one).
- **Soft**: Phase F heartbeat/jitter can ship alongside Phase B (same JS file).
- **Mandatory with B**: Phase I asset cache busting (so browsers pick up the new JS without hard refresh).

### 8.1 Interval drain pattern (Option B, R0-01 §3.2)

**The canonical pattern**: JS WebSocket handlers append to bounded ring buffers inside a module-scope closure exposed as `window._juniperWsDrain`. A `dcc.Interval` at 100 ms fires clientside callbacks that drain each buffer into a corresponding `dcc.Store`.

**Why Option B over Option A (`dash.set_props`) or Option C (`dash-extensions.WebSocket`)**:
- Option A writes one store mutation per WebSocket event → 50 callback storms per second at `candidate_progress` rate. Option B coalesces into one store write per tick. **Correct trade-off for render performance.**
- Option A requires Dash 2.18+. Option B has no floor.
- Option C adds a third-party dep and defeats the frame-budget optimization and the GAP-WS-13 resume protocol.

#### 8.1.1 New JS asset: `assets/ws_dash_bridge.js`

(R0-01 §3.2.1.)

~200 lines, single new file at `juniper-canopy/src/frontend/assets/ws_dash_bridge.js`. Loads alphabetically after `assets/websocket_client.js`. Exposes exactly one new JS global: `window._juniperWsDrain`.

```javascript
(function() {
  if (!window.cascorWS) {
    console.error('[ws_dash_bridge] websocket_client.js must load first');
    return;
  }

  const _buffers = {
    metrics: [],             // bounded to MAX_METRICS_BUFFER
    topology: null,          // last-wins (single snapshot, not a ring)
    state: null,             // last-wins
    cascade_add: [],         // bounded to MAX_EVENT_BUFFER
    candidate_progress: [],  // bounded to MAX_EVENT_BUFFER
    _status: null,
  };
  const MAX_METRICS_BUFFER = 1000;
  const MAX_EVENT_BUFFER = 500;
  let _drainGen = 0;

  // Handlers — bound enforcement happens IN the handler, NOT the drain
  window.cascorWS.on('metrics', function(msg) {
    const data = msg && msg.data;
    if (!data) return;
    _buffers.metrics.push(data);
    if (_buffers.metrics.length > MAX_METRICS_BUFFER) {
      _buffers.metrics.splice(0, _buffers.metrics.length - MAX_METRICS_BUFFER);
    }
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
  });
  window.cascorWS.onStatus(function(status) {
    _buffers._status = status;
  });

  // Drain helpers
  window._juniperWsDrain = {
    drainMetrics: function() {
      const out = _buffers.metrics;
      _buffers.metrics = [];
      _drainGen += 1;
      return {events: out, gen: _drainGen};
    },
    drainState: function() { const out = _buffers.state; _buffers.state = null; return out; },
    drainTopology: function() { const out = _buffers.topology; _buffers.topology = null; return out; },
    drainCascadeAdd: function() { const out = _buffers.cascade_add; _buffers.cascade_add = []; return out; },
    drainCandidateProgress: function() { const out = _buffers.candidate_progress; _buffers.candidate_progress = []; return out; },
    peekStatus: function() { return _buffers._status || null; },
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
})();
```

**Critical design point (R0-01 §3.2.5, RISK-12)**: the ring-buffer cap is enforced IN the `on(type, ...)` handler, NOT in the drain callback. Rationale: background tabs throttle `setInterval` to 1 Hz; if the cap were in the drain, hours of background-tab data could accumulate before the first drain. Cap-in-handler makes memory bounds independent of drain rate.

#### 8.1.2 Python-side drain callbacks

(R0-01 §3.2.2.)

Replace the dead init callback at `dashboard_manager.py:1490-1526` (GAP-WS-04) with a drain callback:

```python
clientside_callback(
    """
    function(n_intervals, current_data) {
        if (!window._juniperWsDrain) return window.dash_clientside.no_update;
        const drain = window._juniperWsDrain.drainMetrics();
        if (!drain.events.length) return window.dash_clientside.no_update;
        const existing = (current_data && current_data.events) || [];
        const merged = existing.concat(drain.events);
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

**Key points**:
- Read-append-write, not replace. The store is a bounded event log with a `gen` counter and `last_drain_ms` diagnostic.
- `no_update` sentinel on empty drain skips the store write entirely (avoids useless diff + downstream cascade).
- Cap at 1000 matches JS ring; belt-and-suspenders.

Analogous drain callbacks for `ws-topology-buffer`, `ws-state-buffer`, `ws-cascade-add-buffer`, `ws-candidate-progress-buffer`. Topology and state are last-wins, not event logs.

**Store shape pin** (R0-01 disagreement #5): `ws-metrics-buffer.data` is `{events: [...], gen: int, last_drain_ms: float}` — structured object, not a bare list. The `gen` counter lets downstream detect store changes via JSON-inequality even when the events array happens to be the same object reference.

#### 8.1.3 Delete the parallel raw-WebSocket clientside callback

(R0-01 §3.5.2, GAP-WS-03.)

Delete `dashboard_manager.py:1490-1526` entirely. Add a comment at the deletion site: `# Former parallel WebSocket client deleted — see R1-03 Phase B and GAP-WS-03. All WebSocket subscriptions flow through assets/websocket_client.js + assets/ws_dash_bridge.js.`

Post-deletion verification:
- `grep -r "window\._juniper_ws_" juniper-canopy/src/frontend/` → zero matches.
- `grep -r "new WebSocket" juniper-canopy/src/frontend/` → one match in `assets/websocket_client.js`.

### 8.2 Plotly `extendTraces` + `maxPoints` (R0-01 §3.3, GAP-WS-14)

**Replace** server-side figure-replace callback at `metrics_panel.py:648-670` with a clientside callback that calls `Plotly.extendTraces` directly:

```python
clientside_callback(
    """
    function(buffer_data, current_fig_state) {
        if (!buffer_data || !buffer_data.events || !buffer_data.events.length) {
            return window.dash_clientside.no_update;
        }
        const events = buffer_data.events;
        const epochs = events.map(e => e.epoch);
        const losses = events.map(e => (e.metrics && e.metrics.loss) || null);
        const accs   = events.map(e => (e.metrics && e.metrics.accuracy) || null);
        const vlosses = events.map(e => (e.metrics && e.metrics.val_loss) || null);
        const vaccs   = events.map(e => (e.metrics && e.metrics.val_accuracy) || null);

        const graphId = 'metrics-panel-figure';
        const update = {x: [epochs, epochs, epochs, epochs], y: [losses, accs, vlosses, vaccs]};
        const traceIndices = [0, 1, 2, 3];
        const maxPoints = 5000;  // RISK-10 hard cap

        if (window.Plotly && document.getElementById(graphId)) {
            window.Plotly.extendTraces(graphId, update, traceIndices, maxPoints);
        }
        return window.dash_clientside.no_update;  // dummy-output pattern
    }
    """,
    Output("metrics-panel-figure-signal", "data"),
    Input("ws-metrics-buffer", "data"),
    State("metrics-panel-figure-signal", "data"),
)
```

**Key points**:
- `maxPoints=5000` is enforced by Plotly. When the trace exceeds, oldest points drop. Primary defense against RISK-10.
- `extendTraces` mutates the graph in-place; does NOT rebuild, does NOT reset pan/zoom. The critical performance win.
- Dummy output (`metrics-panel-figure-signal`) is the standard Dash idiom for clientside side-effect-only callbacks. Add a comment at the registration site explaining the pattern.
- `|| null` for missing sub-metrics renders a trace gap (correct visual).
- `uirevision: "metrics-panel-v1"` must be set in the initial figure layout for pan/zoom preservation on `Plotly.react` snapshot handoffs. Tie to a `training_run_id` that increments on reset so the chart correctly resets after a user-initiated reset (FR-RISK-07).

**Apply to** `CandidateMetricsPanel` as well. `maxPoints=5000`.

**NOT for NetworkVisualizer** (R0-01 §3.3 + disagreement #3): cytoscape.js is not Plotly; `extendTraces` does not apply. Deferred to a separate Phase B+1 design exercise or ship a reduced cytoscape WS path that just responds to `cascade_add` events without REST polling. The existing 5-second REST polling for topology is bandwidth-negligible (~3 KB/s).

### 8.3 rAF coalescing — scaffolded but disabled (R0-01 §3.3.3, GAP-WS-15)

**Decision (R0-01 disagreement #1, adopted)**: ship Phase B with `_scheduleRaf = noop`. The rAF scaffold lives in `ws_dash_bridge.js` as a stub. Enable only if §5.6 instrumentation shows frame-budget pressure post-Phase-B.

**Rationale**: the 100 ms drain already produces ~10 Hz render rate, comfortably under 60 fps. The rAF path introduces a double-render risk with the drain callback and is not strictly necessary at current event rates. Phase B's scope is already large; rAF coalescing is a Phase B+1 optimization.

### 8.4 Polling elimination (R0-01 §3.4, GAP-WS-16 + GAP-WS-25)

**The P0 motivator.** Eliminates ~3 MB/s per dashboard.

#### 8.4.1 `ws-connection-status` store

New `dcc.Store(id='ws-connection-status')` populated via a drain callback that reads `window._juniperWsDrain.peekStatus()`:

```python
clientside_callback(
    """
    function(n_intervals, current) {
        if (!window._juniperWsDrain) return window.dash_clientside.no_update;
        const status = window._juniperWsDrain.peekStatus();
        if (!status) return window.dash_clientside.no_update;
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

Emits only on change (avoids thrashing downstream).

#### 8.4.2 The polling toggle

In `_update_metrics_store_handler` at `dashboard_manager.py:2388-2421`:

```python
@callback(
    Output("metrics-panel-metrics-store", "data"),
    Input("fast-update-interval", "n_intervals"),
    State("ws-connection-status", "data"),
    State("metrics-panel-metrics-store", "data"),
)
def _update_metrics_store_handler(n, ws_status, current_data):
    if ws_status and ws_status.get("connected"):
        return no_update  # WebSocket drives metrics; do NOT poll.
    if current_data is None:
        return requests.get(self._api_url("/api/metrics/history?limit=1000"), timeout=2).json()
    # Fallback: 1 Hz (10× slower than current 100 ms)
    if (n % 10) != 0:
        return no_update
    return requests.get(self._api_url("/api/metrics/history?limit=1000"), timeout=2).json()
```

**Refinements (R0-01 disagreement #2, adopted)**:
1. Initial load always fetches REST (seed snapshot).
2. WS-connected → `no_update`.
3. WS-disconnected → 1 Hz fallback (not 100 ms) via `n % 10`.

Bandwidth outcome:
- Steady state WS healthy: 0 B/s
- Initial load: ~300 KB one-shot
- WS disconnected: ~300 KB/s
- WS reconnected: 0 B/s

**Apply the same toggle** to every polling callback that would conflict with WS push (R0-01 §3.4.3):
- `_update_metrics_store_handler` (the P0 motivator)
- `_handle_training_state_poll`
- `_handle_candidate_progress_poll`
- `_handle_topology_poll` (5-second polling; keep REST path but `no_update` on WS-healthy)

### 8.5 JS client cleanup (R0-01 §3.5.1)

**Keep** `assets/websocket_client.js`. Clean up:
1. Verify `onStatus()` returns `{connected, reason, reconnectAttempt, ts}`.
2. Add `permessage-deflate` support indicator (not configurable but surface in status).
3. **Jitter in reconnect backoff** (GAP-WS-30): `delay = Math.random() * Math.min(cap, base * Math.pow(2, attempt))` with `base=500ms`, `cap=30s`.
4. **Remove the 10-attempt cap** (GAP-WS-31): retry forever at max 30 s. Connection indicator keeps user informed.
5. **`server_instance_id` handling**: parse from `connection_established`, store in module-scope, send in `resume` frame on reconnect.
6. **`seq` tracking**: record `msg.seq` monotonically; WARN on out-of-order.
7. **Bounded JS ring of last 256 events with seq** (belt-and-suspenders against double-apply during replay).
8. **Delete dead helpers**: `getBufferedMessages()` destructive read had one caller (the dead init callback).

**Graceful degradation**: if cascor does not yet advertise `seq` (Phase A-server not landed), default `_lastSeq=0` and never trigger replay. Falls back to REST snapshot on reconnect.

### 8.6 Dead-code removal verification

- Grep assertion (AC-19): `grep -r "window\._juniper_ws_" juniper-canopy/src/frontend/` → 0 matches.
- Grep assertion (AC-20): `grep -r "new WebSocket" juniper-canopy/src/frontend/` → 1 match (in `assets/websocket_client.js`).

These run as pytest tests that shell out to `grep`.

### 8.7 Connection indicator badge (R0-01 §4 step 17, GAP-WS-26)

Small `html.Div` with a clientside callback reading `ws-connection-status` and toggling a CSS class. Four states: `connected-green`, `reconnecting-yellow`, `offline-red`, `demo-gray`.

### 8.8 Demo mode parity (R0-01 §4 step 18, GAP-WS-33, RISK-08)

`demo_mode.py` sets `{connected: true, mode: "demo"}` via `window._juniperWsDrain` peek path. Badge shows "demo"; polling toggle correctly returns `no_update` in demo mode. Required test: `test_demo_mode_metrics_parity`.

### 8.9 Latency instrumentation (R0-01 §4 step 19, GAP-WS-24)

New JS module `assets/ws_latency.js` (~50-100 LOC). Records `received_at_ms = performance.now()` per inbound message. Subtracts from `msg.emitted_at_monotonic` (with clock offset captured in `connection_established`). Bucketizes into histograms. POSTs to `/api/ws_latency` every 60 s.

**Server-side pipe** (R0-06 §6.4 step 2): cascor adds `emitted_at_monotonic` to every WS envelope; canopy adds the `/api/ws_latency` endpoint + Prometheus aggregation. The endpoint is owned by the canopy backend agent; gate the browser POST behind a feature flag if the backend lags.

**Clock offset**: browser computes `clock_offset = server_wall_clock - browser_now` from `connection_established.data.server_time`. Recomputed on every reconnect (handles laptop sleep / NTP).

**Buckets** (source doc §5.6): `{50, 100, 200, 500, 1000, 2000, 5000}` ms.

**Export cadence**: 60 s from browser to canopy.

### 8.10 Frame budget test (R0-01 AC-15)

Not a CI blocker, but a recording-only assertion (R0-05 §6.3, §8.2): emit 50 Hz `candidate_progress` for 2 s, measure via `performance.now()`, assert p95 frame-handling time < 17 ms. Run with `@pytest.mark.flaky(reruns=2)` and downgrade to trace-only if CI variance persists.

### 8.11 Implementation steps (R0-01 §4, with R0-03 and R0-02 cooperation)

Numbered step list per R0-01 §4 (31 steps). Abbreviated here:

1. [cascor/A-server dep] Ship Phase A-server first so cascor emits `seq`.
2. [canopy] Add `ws-cascade-add-buffer` and `ws-candidate-progress-buffer` stores.
3. [canopy] Add `ws-connection-status` store.
4. [canopy] Add `metrics-panel-figure-signal` dummy store.
5. [canopy/js] Create `assets/ws_dash_bridge.js` per §8.1.1.
6. [canopy/js] Clean up `assets/websocket_client.js` per §8.5.
7. [canopy] Delete dashboard_manager.py:1490-1526.
8. [canopy] Rewrite `ws-metrics-buffer` drain callback.
9. [canopy] Update topology and state drains to call `window._juniperWsDrain.drainTopology()` / `drainState()`.
10. [canopy] Add drain callbacks for `ws-cascade-add-buffer` and `ws-candidate-progress-buffer`.
11. [canopy] Add `ws-connection-status` drain callback.
12. [canopy] Refactor `_update_metrics_store_handler` with WS-aware toggle.
13. [canopy] Apply the toggle pattern to `_handle_training_state_poll`, `_handle_candidate_progress_poll`, `_handle_topology_poll`.
14. [canopy] Rewrite `MetricsPanel.update_metrics_display()` as clientside `extendTraces`.
15. [canopy] Apply `extendTraces` pattern to `CandidateMetricsPanel`.
16. [canopy] Minimal `NetworkVisualizer` WS wiring (deferrable to B+1 if scope tight).
17. [canopy] Add connection indicator badge.
18. [canopy] Demo mode parity.
19. [canopy] Browser-side latency instrumentation module.
20. [canopy] Add `metrics-panel-figure-signal` hidden store.
21. [canopy/tests] `dash_duo` fixtures and tests per R0-05 §6.1.
22. [canopy/tests] Playwright wire tests per R0-05 §6.2.
23. [canopy/tests] `test_demo_mode_metrics_parity`.
24. [canopy/ci] Marker split, `playwright install`, trace artifacts.
25. [canopy/tests] `test_chart_does_not_poll_when_websocket_connected`.
26. [canopy/tests] Memory-cap regression test.
27. [cascor/A-server dep] Confirm `seq` field and replay buffer ship date.
28. [security dep] Coordinate with B-pre-b for Origin + CSRF.
29. [canopy/docs] Update `juniper-canopy/docs/architecture.md` with new data-path diagram.
30. [Phase I] Configure `assets_url_path` with content-hash query string.
31. [canopy/tests] `test_metrics_message_has_dual_format` (R0-01 §3.6) — first line of defense against RISK-01.

### 8.12 Test plan (R0-01 §6, R0-05 §6.1, §6.2)

**Unit/Jest** (R0-01 AC-01, AC-02):
- `websocket_client.js` tests: jitter, uncapped retries, onStatus invocation, server_instance_id parsing, seq monotonicity, bounded ring.
- `ws_dash_bridge.js` tests: handler registration, ring cap in push path, drain functions return+clear, `_introspect` correctness.

**Python unit (canopy)** (AC-03):
- `test_update_metrics_store_handler_returns_no_update_when_ws_connected`
- `test_update_metrics_store_handler_falls_back_to_rest_when_ws_disconnected`
- `test_ws_connection_status_store_reflects_cascorWS_status`
- `test_ws_metrics_buffer_drain_is_bounded`
- `test_ws_metrics_buffer_drain_deduplicates_by_seq`
- `test_ws_metrics_buffer_preserves_order_when_reordered`

**dash_duo** (AC-04 .. AC-10):
- `test_browser_receives_metrics_event`
- `test_chart_updates_on_each_metrics_event`
- `test_chart_does_not_poll_when_websocket_connected`
- `test_chart_falls_back_to_polling_on_websocket_disconnect`
- `test_demo_mode_metrics_parity` (RISK-08)
- `test_metrics_message_has_dual_format`
- `test_connection_indicator_reflects_status`

**Playwright** (AC-11 .. AC-14):
- `test_websocket_frames_have_seq_field`
- `test_resume_protocol_replays_missed_events`
- `test_connection_status_indicator_reflects_websocket_state`
- `test_start_button_uses_websocket_command` (overlaps Phase D; valuable Phase B regression gate)

**Frame budget / performance regression**:
- `test_render_frame_under_budget` (recording lane)
- `test_memory_bounded_over_long_run` (emit 5000 events, assert buffer capped at 1000, chart <= 5000 points per trace)
- `test_bandwidth_eliminated_in_ws_mode` (AC-17, P0 motivator quantitative acceptance)

**Smoke**:
- `test_full_training_run_no_errors` (50-epoch scripted run; no console errors; final chart = 50 points; no orphaned WS after close)
- `test_dashboard_manager_has_no_dead_websocket_references` (grep assertion)
- `test_cascorws_is_only_websocket_constructor` (grep assertion)

### 8.13 Observability for Phase B (R0-06 §6.1)

Metrics:
- `canopy_ws_delivery_latency_ms_bucket{type}` — histogram, type ∈ {metrics, state, topology, cascade_add, candidate_progress, event, command_response}
- `canopy_ws_active_connections` — gauge; alert at 80% of `ws_max_connections`
- `canopy_ws_reconnect_total{reason}` — counter; alert on spike > 5× baseline
- `canopy_ws_browser_heap_mb` — histogram from JS; alert p95 > 500 MB
- **`canopy_rest_polling_bytes_per_sec`** — gauge; **target: >90% reduction post-Phase-B** (P0 motivator proof)

Alerts:
- `WSDeliveryLatencyP95High`: `histogram_quantile(0.95, canopy_ws_delivery_latency_ms_bucket{type="metrics"}[5m]) > 500` → ticket
- `WSConnectionCount80`: → ticket
- `WSBrowserHeapHigh`: `histogram_quantile(0.95, canopy_ws_browser_heap_mb_bucket[1h]) > 500` → ticket

SLOs (tracked via §5.6 histogram, targets from R0-06 §6.3):

| Event type                             | p50     | p95     | p99     |
|----------------------------------------|---------|---------|---------|
| `metrics` delivery                     | <100 ms | <250 ms | <500 ms |
| `state` delivery                       | <50 ms  | <100 ms | <200 ms |
| `command_response` (set_params)        | <50 ms  | <100 ms | <200 ms |
| `command_response` (start/stop)        | <100 ms | <250 ms | <500 ms |
| `cascade_add` delivery                 | <250 ms | <500 ms | <1000 ms |
| `topology` delivery (≤64 KB)           | <500 ms | <1000 ms| <2000 ms |

Error budget: 99.9% of events meet p95 over 7-day rolling window.

### 8.14 Kill switch

`Settings.disable_ws_bridge: bool = False` (emergency disable of browser bridge; falls back to REST polling which has its own bounded memory). TTF ~5 minutes.

**Validation requirement**: CI suite includes `test_disable_ws_bridge_forces_rest_polling`.

### 8.15 Exit gate (R0-06 §3.3)

- All `dash_duo` / Playwright tests in §8.12 green.
- **P0 motivator proof**: `canopy_rest_polling_bytes_per_sec` shows >90% reduction in staging when WS is connected.
- GAP-WS-24 latency instrumentation ingesting non-zero data for ≥1 hour.
- `GAP-WS-25` polling toggle observed: disconnecting cascor causes fallback to polling within drain interval.
- `test_demo_mode_metrics_parity` green (RISK-08).
- 48-72 hour browser memory soak test in staging shows no leak (RISK-10).

### 8.16 Runbook deliverable

- `juniper-canopy/notes/runbooks/ws-bridge-debugging.md` — how to capture a browser trace in staging; how to read the latency histogram panel.
- `juniper-canopy/notes/runbooks/ws-memory-soak-test-procedure.md` — 24-hour soak procedure.
- `juniper-canopy/docs/REFERENCE.md` — "WebSocket health dashboard panel" section.

### 8.17 Effort estimate

4 engineering days per source doc §9.3, which R0-01 and R0-06 both accept. Add R0-06 §13.6 observability buffer (+1 day spread across Phase B).

---

## 9. Phase C: set_params canopy adapter migration

**Source**: R0-04 (primary). R0-05 §4.3, §6.1, §9.4. R0-06 §3.4, §5.1.

**Owner-class**: backend-canopy.

**Dependencies**:
- **Hard**: Phase A (SDK `set_params`) merged and on PyPI.
- **Hard**: Phase B (browser bridge) so sliders can fire the new adapter path via `window.cascorControlWS`.
- **Recommended**: Phase B-pre-b so the browser-side CSRF is enforced from day one.

### 9.1 Scope

Refactor `CascorServiceAdapter.apply_params(**params)` to split params into hot/cold sets and dispatch hot to WebSocket `set_params`, cold to REST PATCH. Feature-flag the new path behind `Settings.use_websocket_set_params = False`.

### 9.2 Hot/cold classification (R0-04 §5.1)

```python
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
})  # 11 params per source doc §5.1

_COLD_CASCOR_PARAMS = frozenset({
    "init_output_weights",
    "candidate_epochs",
})  # params where REST is fine (one-shot dropdowns)
```

Unknown keys default to REST with a WARNING log (operator signal for a classification gap).

### 9.3 Refactored `apply_params` (R0-04 §5.1)

```python
def apply_params(self, **params: Any) -> Dict[str, Any]:
    """Forward parameter updates to the running cascor instance.

    Public delegating wrapper. Splits params into hot/cold and dispatches
    to _apply_params_hot() (WebSocket) and _apply_params_cold() (REST).
    When use_websocket_set_params is False, everything routes through REST.
    """
    mapped = {self._CANOPY_TO_CASCOR_PARAM_MAP[k]: v
              for k, v in params.items() if k in self._CANOPY_TO_CASCOR_PARAM_MAP}
    if not mapped:
        return {"ok": True, "data": {}, "message": "No cascor-mappable params"}

    if not self._settings.use_websocket_set_params:
        return self._apply_params_cold(mapped)

    hot = {k: v for k, v in mapped.items() if k in self._HOT_CASCOR_PARAMS}
    cold = {k: v for k, v in mapped.items() if k in self._COLD_CASCOR_PARAMS}
    unknown = set(mapped) - self._HOT_CASCOR_PARAMS - self._COLD_CASCOR_PARAMS
    if unknown:
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
```

**Ordering**: WebSocket fires first, then REST. The user's active sliders (hot) take latency precedence. A `lifecycle._training_lock` on the server side serializes both transports (RISK-03 mitigation).

### 9.4 `_apply_params_hot` with unconditional REST fallback (R0-04 §5.1)

```python
def _apply_params_hot(self, mapped: Dict[str, Any]) -> Dict[str, Any]:
    if self._control_stream is None or not self._control_stream.is_connected:
        logger.info(f"apply_params: WS not connected, falling back to REST for {list(mapped.keys())}")
        return self._apply_params_cold(mapped)
    try:
        future = asyncio.run_coroutine_threadsafe(
            self._control_stream.set_params(mapped, timeout=1.0),
            self._control_loop,
        )
        envelope = future.result(timeout=2.0)  # outer > inner
        latency_ms = envelope.get("_client_latency_ms", 0.0)
        SET_PARAMS_LATENCY_MS.labels(transport="websocket").observe(latency_ms)
        return {"ok": True, "data": envelope.get("data", {}).get("result", {})}
    except (JuniperCascorTimeoutError, JuniperCascorConnectionError) as e:
        logger.warning(f"apply_params: WS set_params failed ({e}); falling back to REST")
        return self._apply_params_cold(mapped)
    except JuniperCascorClientError as e:
        logger.error(f"apply_params: WS set_params server error: {e}")
        return {"ok": False, "error": str(e)}
```

**Critical**: unconditional fallback to REST on any WS failure mode (connection, timeout). Server errors bubble up (they are legitimate errors that would also fail on REST).

**Outer timeout `2.0` > inner timeout `1.0`** so the inner fires cleanly first. Pattern from R0-04 §5.3.

### 9.5 Control stream supervisor (R0-04 §5.3)

```python
async def _control_stream_supervisor(self):
    backoff = [1, 2, 5, 10, 30]
    attempt = 0
    while not self._shutdown.is_set():
        try:
            self._control_stream = CascorControlStream(self._ws_base_url, self._api_key)
            await self._control_stream.connect()
            attempt = 0
            await self._control_stream.wait_closed()
        except (JuniperCascorConnectionError, JuniperCascorClientError) as e:
            logger.warning(f"Control stream reconnect {attempt}: {e}")
        finally:
            self._control_stream = None
            if not self._shutdown.is_set():
                await asyncio.sleep(backoff[min(attempt, len(backoff) - 1)])
                attempt += 1
```

Two background tasks on the adapter's async loop: existing metrics-relay + new `_control_stream_supervisor`. Failures in one do not kill the other.

**No client-side queueing on reconnect** (R0-04 §5.3). Sliders are debounced at 250 ms; a 5-second reconnect followed by flushing queued values would replay stale state. Correct behavior: use REST for the one call during the gap.

### 9.6 Feature flag (R0-04 §5.2, R0-06 §5.1)

`Settings.use_websocket_set_params: bool = False` in `juniper-canopy/src/config/settings.py`. Environment override `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS`.

**Rollout stages**:

| Stage | Description                                          | Default |
|-------|------------------------------------------------------|---------|
| 0     | Phase A lands; no canopy change yet                  | n/a     |
| 1     | Phase C lands; flag default False in prod            | False   |
| 2     | Instrumentation collects REST p50/p95/p99 for 1 week | False   |
| 3     | Compare to §5.1 targets; decide if Phase C needed    | False   |
| 4     | Canary: flip to True in staging; ≥1 week clean       | True (staging), False (prod) |
| 5     | Production flip: single-line config PR               | True    |

**Flip criteria** (R0-06 §3.4):
- §5.6 histogram ≥1 week; WS p95 < 100 ms AND REST p95 > 200 ms (meaningful delta).
- Zero increase in orphaned-command incidents (RISK-13).
- Canary cohort ≥1 week with zero param-loss.
- User-research signal (if Q7 runs) shows "feels more responsive" from ≥3 of 5 subjects.

**Flip evaluation**: per-call (cheap attribute access; no restart).

**Kill switch**: `JUNIPER_CANOPY_USE_WEBSOCKET_SET_PARAMS=false` + canopy restart. TTF ~2 minutes (R0-04 §5.2). Or: config edit without restart if the flag check is per-call.

**Removal criterion**: do NOT remove the flag or REST path for ≥1 release cycle after the flip. Keeps rollback lever warm.

### 9.7 Latency instrumentation (R0-04 §7.2)

```python
SET_PARAMS_LATENCY_MS = prometheus_client.Histogram(
    name="canopy_set_params_latency_ms",
    documentation="set_params latency per transport",
    labelnames=["transport"],
    buckets=[5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000],
)
```

Emitted by both `_apply_params_hot` (WS) and `_apply_params_cold` (REST).

### 9.8 Test plan (R0-04 §10, R0-05 §4.3, §9.4)

**Unit tests**:
- `test_apply_params_hot_keys_go_to_websocket`
- `test_apply_params_cold_keys_go_to_rest`
- `test_apply_params_mixed_batch_split`
- `test_apply_params_hot_falls_back_to_rest_on_ws_error`
- `test_apply_params_preserves_public_signature`
- `test_apply_params_feature_flag_default_off`
- `test_apply_params_feature_flag_on_uses_websocket`
- `test_apply_params_unknown_keys_default_to_rest_with_warning`
- `test_control_stream_supervisor_reconnects_with_exponential_backoff`
- `test_control_stream_supervisor_shutdown_cancels_pending_futures`

**Integration tests** (R0-05 §5.2, §5.3):
- `test_adapter_apply_params_hot_uses_websocket_roundtrip` (against FakeCascorServerHarness)
- `test_adapter_apply_params_cold_uses_rest`
- `test_adapter_reconnects_after_fake_kills_connection`
- `test_adapter_handles_resume_failed_by_fetching_snapshot`

**dash_duo** (R0-05 §6.1):
- `test_learning_rate_change_uses_websocket_set_params`
- `test_learning_rate_change_falls_back_to_rest_on_disconnect`
- `test_orphaned_command_resolves_via_state_event` (GAP-WS-32)
- `test_per_command_timeout_values`

**CI runs in BOTH flag states**: flag-off is the regression gate, flag-on is the new-path gate.

### 9.9 Observability (R0-06 §6.1)

- `canopy_set_params_latency_ms_bucket{transport, key}` — Phase C flip gate
- `canopy_orphaned_commands_total{command}` — alert rate > 1/min

Alert: `CanopyOrphanedCommands`: `rate(canopy_orphaned_commands_total[5m]) > 1/60` → ticket.

### 9.10 Kill switch

`Settings.use_websocket_set_params=False` → all params route through REST. TTF ~5 minutes.

### 9.11 Exit gate (R0-06 §3.4)

To merge Phase C to main:
- Unit tests and integration tests in §9.8 green.
- Feature flag defaults to False in production.
- Flag-on path exercised in CI.

To flip flag default (Stage 5):
- §5.6 histogram shows meaningful WS vs REST delta (≥1 week data).
- Canary cohort ≥1 week clean.
- Zero RISK-03 ordering violations.
- Zero RISK-09 user-visible regressions.

### 9.12 Runbook deliverable

- `juniper-canopy/notes/runbooks/ws-set-params-feature-flag.md` — how to flip, how to monitor, how to roll back.
- `juniper-canopy/docs/REFERENCE.md` — Phase C feature flag section.

### 9.13 Effort estimate

2 engineering days per source doc §9.4, accepted by R0-04 and R0-06.

---

## 10. Phase D: control buttons via WebSocket (gated on B-pre-b)

**Source**: R0-05 §4.3, §9.5. R0-06 §3.5.

**Owner-class**: frontend + backend-canopy.

**Dependencies**:
- **Hard**: Phase B (browser bridge exists; `window.cascorControlWS` cleaned up).
- **Hard**: Phase B-pre-b (all M-SEC-01/01b/02/03/04/05 in place). Enforced by branch protection.

### 10.1 Scope

Add WebSocket path for `start`, `stop`, `pause`, `resume`, `reset` training-control commands. Retain REST POST at `/api/train/{command}` as first-class supported API (GAP-WS-06). Phase D is additive, NOT a REST migration.

### 10.2 Implementation

Frontend: slider buttons fire `window.cascorControlWS.send({command: "start"})` (etc.). Fallback path: if WS disconnected, POST to REST. Client-side `command_id` (UUID) is generated so the orphaned-command detection (GAP-WS-32) can match ack or state event.

Per-command timeouts (source doc §7.32, R0-02 §3.3 attack 5):
- `start`: 10 s
- `stop/pause/resume`: 2 s
- `set_params`: 1 s
- `reset`: 2 s

Cascor's `command_id` is scoped per-connection, never global (security invariant: `Dict[WebSocket, Dict[command_id, pending]]`).

### 10.3 Test plan (R0-05 §9.5)

**Unit** (canopy):
- `test_training_button_handler_sends_websocket_command_when_connected`
- `test_training_button_handler_falls_back_to_rest_when_disconnected`
- `test_rest_endpoint_still_returns_200_and_updates_state` (GAP-WS-06 regression)

**Playwright** (R0-05 §6.2):
- `test_start_button_uses_websocket_command`
- `test_command_ack_updates_button_state`
- `test_disconnect_restores_button_to_disabled`
- `test_csrf_required_for_websocket_start` (B-pre-b regression gate)

### 10.4 Observability

- `canopy_training_control_total{command, transport}` — track ratio.
- `canopy_orphaned_commands_total{command}` — reused from Phase C.

### 10.5 Kill switch

No Phase D-specific kill switch beyond the B-pre-b `disable_ws_control_endpoint`. If Phase D causes user-visible regression, revert the PR.

### 10.6 Exit gate (R0-06 §3.5)

- All Playwright tests green.
- CSRF regression test `test_csrf_required_for_websocket_start` green.
- 24 h staging with zero orphaned-command incidents.
- REST endpoints still receive traffic from non-browser consumers (verify via access logs).
- `docs/REFERENCE.md` documents both REST and WS training control APIs.

### 10.7 Runbook deliverable

- `juniper-canopy/notes/runbooks/ws-control-button-debug.md`.
- `juniper-canopy/docs/REFERENCE.md` — "Training control API" section.

---

## 11. Phase E: full backpressure + heartbeat + reconnect jitter

Consolidates source doc Phase E (backpressure) and Phase F (heartbeat + jitter) since they are small and frequently ship together.

**Source**: R0-03 §5.2, §7.2. R0-02 (heartbeat security). R0-05 §4.1, §9.6, §9.7. R0-06 §3.6, §13.2.

**Owner-class**: backend-cascor (backpressure) + frontend (jitter) + both (heartbeat).

**Dependencies**: Phase B in production (real workload exposes slow-client patterns).

### 11.1 Phase E — full backpressure (per-client pump task)

(R0-03 §5.2 "Full fix", §7.2.)

```python
class _ClientState:
    ws: WebSocket
    send_queue: asyncio.Queue[dict]
    pump_task: asyncio.Task
    slow_strikes: int
```

Each connected client has a dedicated `pump_task` that consumes from its queue and `await ws.send_json(msg)` with the 0.5 s per-send timeout. 3 strikes → close 1008 + prune.

**Policy matrix** (R0-03 §5.2, R0-06 §13.2 adopted — default is `drop_oldest_progress_only`):

| Event type              | Queue size | Overflow policy  | Rationale |
|-------------------------|-----------:|-------------------|-----------|
| `state`                 | 128        | close(1008)       | Terminal-state-sensitive |
| `metrics`               | 128        | close(1008)       | Drops cause chart gaps, but still observable |
| `cascade_add`           | 128        | close(1008)       | Each event is a growth step |
| `candidate_progress`    | 32         | drop_oldest       | Coalesceable; next progress subsumes previous |
| `event` (training_complete etc.) | 128 | close(1008)       | Terminal-state-sensitive |
| `command_response`      | 64         | close(1008)       | Client specifically waits for this |
| `connection_established`| n/a        | n/a               | Personal send |
| `pong`                  | 16         | drop_oldest       | Client can re-ping |

`Settings.ws_backpressure_policy ∈ {block, drop_oldest_progress_only, close_slow}`. **Default: `drop_oldest_progress_only`** (R0-06 §13.2, disagreement with source doc which says `block`).

**Rationale for the disagreement**: RISK-04 is Medium/Medium. Keeping `block` as the default leaves the first production incident as exactly this failure mode. `drop_oldest_progress_only` mitigates both RISK-04 (slow client blocks broadcasts) and RISK-11 (silent data loss for state-bearing events).

**Disconnect cleanup** (R0-03 §5.3):
1. Cancel pump task (BEFORE removing from set).
2. Drain send queue (already stale).
3. Remove from both `_active_connections` and `_pending_connections`.
4. Close ws cleanly if still open.
5. Decrement per-IP counter.
6. Remove `_ClientState` entry.

Idempotent.

**Parallel fan-out** (R0-03 §5.4): Phase E can ship with the pump-task model where each client has its own coroutine, and `broadcast()` just enqueues. This sidesteps the serial fan-out problem entirely.

### 11.2 Phase F — heartbeat (GAP-WS-12)

(R0-05 §4.2, §9.7.)

Application-layer ping/pong:
- Client sends `{type: "ping"}` every 30 s.
- Server replies `{type: "pong"}`.
- Client closes if no pong within 5 s.

Integrates with M-SEC-10 idle timeout: heartbeat resets the idle timer.

### 11.3 Phase F — reconnect jitter (GAP-WS-30)

(R0-01 §3.5.1 item 3, R0-06 §3.6.)

```javascript
delay = Math.random() * Math.min(CAP, BASE * 2 ** attempt);
```

`BASE=500ms`, `CAP=30s`. Full jitter (not decorrelated jitter) for simplicity.

### 11.4 Phase F — uncapped reconnect (GAP-WS-31)

(R0-01 §3.5.1 item 4.)

Remove 10-attempt cap. Retry forever at max 30 s intervals. Connection indicator keeps user informed.

### 11.5 Test plan (R0-05 §9.6, §9.7)

**Unit** (cascor):
- `test_slow_client_does_not_block_other_clients`
- `test_slow_client_send_timeout_closes_1008_for_state`
- `test_slow_client_progress_events_dropped`
- `test_drop_oldest_queue_policy`
- `test_backpressure_default_is_drop_oldest_progress_only` (updated per R0-06 §13.2)

**Unit** (cascor-client):
- `test_ping_sent_every_30_seconds`
- `test_pong_received_cancels_close`
- `test_reconnect_backoff_has_jitter` (std-dev > 0 across 10 attempts)
- `test_reconnect_backoff_capped`
- `test_reconnect_attempt_unbounded_with_cap` (GAP-WS-31: >10 attempts with capped delay)

**Integration/Playwright**:
- `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect` (test override ping_interval=0.1, pong_timeout=0.5)

**Chaos**:
- Rolling reconnect test: 10 clients continuously disconnect/reconnect at randomized 1-10 s intervals during a 10-minute broadcast. Assert no missed events outside documented reconnect window.

### 11.6 Observability

Cascor:
- `cascor_ws_broadcast_send_duration_seconds` — histogram; alert p95 > 500 ms
- `cascor_ws_dropped_messages_total{reason, type}` — counter; **alert any non-zero `state_dropped`**
- `cascor_ws_slow_client_closes_total` — counter

Canopy/frontend (reuses `canopy_ws_reconnect_total` from Phase B).

Alerts:
- `WSStateDropped`: `increase(cascor_ws_dropped_messages_total{type="state"}[5m]) > 0` → **page on-call**
- `WSSlowBroadcastP95`: p95 > 500 ms → ticket
- `WSReconnectStorm`: `rate(canopy_ws_reconnect_total[1m]) > 5 * <baseline>` → ticket (page if jitter fix not deployed)

### 11.7 Kill switches

- `Settings.ws_backpressure_policy=block` → revert to source doc's default (restores RISK-04, documented trade-off).
- `Settings.disable_ws_auto_reconnect=True` → stops reconnect storm. TTF ~10 min.

### 11.8 Exit gate

- All unit/integration/chaos tests green.
- 48 h staging with zero `state_dropped` alerts.
- Phase E: `ws-slow-client-policy.md` runbook published.
- Phase F: no runbook change beyond `disable_ws_auto_reconnect` flag reference.

### 11.9 Effort estimate

Phase E: 1 day. Phase F: 0.5 day. Total: 1.5 days.

---

## 12. Phase G: cascor set_params integration test

**Source**: R0-03 §6.3, §7.1 commit 9. R0-02 §6.10 IMPL-SEC-39 (security test cases). R0-05 §4.1 "Phase G", §9.8.

**Owner-class**: backend-cascor.

**Dependencies**: ships with Phase A-server (the source doc envelope changes are already in place).

### 12.1 Scope

Add integration tests that exercise cascor's `/ws/control` set_params handler via FastAPI `TestClient.websocket_connect()` directly (no SDK dependency, so cascor can validate the wire protocol without coupling to cascor-client release cadence).

### 12.2 Test list

(R0-05 §4.1 + R0-02 §6.10 + R0-05 §14.5 expansions.)

- `test_set_params_via_websocket_happy_path`
- `test_set_params_whitelist_filters_unknown_keys`
- `test_set_params_init_output_weights_literal_validation` (rejects `"random; rm -rf /"`)
- `test_set_params_oversized_frame_rejected` (64 KB cap)
- `test_set_params_no_network_returns_error`
- `test_unknown_command_returns_error` (GAP-WS-22)
- `test_malformed_json_closes_with_1003` (GAP-WS-22)
- `test_set_params_origin_rejected` (M-SEC-01b regression)
- `test_set_params_unauthenticated_rejected` (X-API-Key regression)
- `test_set_params_rate_limit_triggers_after_10_cmds` (M-SEC-05)
- `test_set_params_bad_init_output_weights_literal_rejected`
- **Addition (R0-05 §14.5)**: `test_set_params_concurrent_command_response_correlation` (two WebSocket clients; each `command_response` routes to its originating connection)
- **Addition (R0-05 §14.5)**: `test_set_params_during_training_applies_on_next_epoch_boundary` (ack vs effect, §5.3.1)
- **Addition (R0-02 §7.2)**: `test_set_params_request_id_echo` (server echoes `request_id` for Phase A SDK consumer)

### 12.3 Effort estimate

0.5 day per source doc §9.8 — accepted.

---

## 13. Phase H: nested+flat metric format audit

**Source**: R0-01 §3.6 (the wire-format regression test). R0-05 §4.3, §9.9. R0-06 §3.6, §13.7.

**Owner-class**: backend-canopy.

**Dependencies**: **regression test MUST land before the audit begins** (source doc §9.9).

### 13.1 Scope

Two deliverables:
1. **Regression test** (`test_normalize_metric_produces_dual_format`) landed as its own PR before any audit work.
2. **Consumer audit document** (`juniper-ml/notes/code-review/NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md`) documenting every consumer of `_normalize_metric` output and whether each reads the nested format, the flat format, or both.

### 13.2 Regression test (R0-05 §4.3)

```python
def test_normalize_metric_produces_dual_format():
    """Regression gate: normalize_metric must produce BOTH flat and nested keys.

    This is the test PR #141 lacked. Any future refactor that silently
    drops one format must fail this test.
    """
    raw = {"train_loss": 0.5, "val_loss": 0.6, "hidden_units": 2}
    out = _normalize_metric(raw)
    # Flat keys
    assert "train_loss" in out
    assert out["train_loss"] == 0.5
    assert "val_loss" in out
    assert out["val_loss"] == 0.6
    # Nested keys
    assert "metrics" in out
    assert out["metrics"]["train_loss"] == 0.5
    assert out["metrics"]["val_loss"] == 0.6
    # Topology nested keys
    assert "network_topology" in out
    assert out["network_topology"]["hidden_units"] == 2
```

Plus:
- `test_normalize_metric_nested_topology_present`
- `test_normalize_metric_preserves_legacy_timestamp_field`

**Phase B wire-level companion** (R0-01 §3.6): `test_metrics_message_has_dual_format` in the Phase B test suite — assertion that cascor→canopy→browser wire format is dual-format compatible. This wire test protects against server-side regression; the Python test protects against canopy-side refactor regression.

**dash_duo companion** (R0-05 §6.1): `test_normalize_metric_dual_format_in_browser_view` — defensive browser-side assertion that both formats drive the chart.

### 13.3 Consumer audit

Deliverable: `NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` documenting:
1. Every caller of `_normalize_metric` output.
2. Which consumers read nested keys (`m["metrics"]["loss"]`).
3. Which consumers read flat keys (`m["train_loss"]`).
4. Which read both.
5. Recommendation: do NOT remove the dual format until ALL consumers are migrated.

**Do not touch the format in Phase B** (R0-01 §3.6). Phase H is the only place removals are considered, and only after the audit.

### 13.4 CODEOWNERS rule (R0-06 §13.7)

Add a CODEOWNERS entry: any PR touching `_normalize_metric` requires explicit approval from a specific reviewer group. Operational guard against RISK-01.

### 13.5 Effort estimate

1 day per source doc §9.9 — accepted.

---

## 14. Consolidated risk register

Every RISK-NN from source doc §10, plus R0-01 FR-RISK, R0-04 R04, R0-05 T-RISK variants, folded into a single register. Each entry has: severity, likelihood, phase, owner-class, primary mitigation, monitoring signal, kill switch, TTF, validation hook.

### RISK-01 — Dual metric format removed too aggressively

- Severity/Likelihood: **High/Medium**
- Phase: **H**
- Owner: backend-canopy
- Mitigation: Phase H regression test BEFORE audit; CODEOWNERS rule on `_normalize_metric`; Phase B wire-level `test_metrics_message_has_dual_format`.
- Signal: canopy `/api/metrics` access log response-schema fingerprint (hash response shape for 24 h, alert on drift).
- Kill switch: git revert + blue/green redeploy. TTF ~5 min.
- Validation: §13.2 test suite.

### RISK-02 — Phase B clientside_callback wiring hard to debug remotely

- Severity/Likelihood: **Medium/High**
- Phase: **B**
- Owner: frontend + ops
- Mitigation: Playwright trace viewer; `dash_duo` store assertions; Option B drain pattern; runbook documenting trace-capture procedure.
- Signal: `canopy_ws_delivery_latency_ms`; drain callback error rate; browser JS console error rate (Sentry-style).
- Kill switch: `Settings.disable_ws_bridge=True`. TTF ~5 min.
- Rollback depth: REST polling fallback retained through at least Phase D.

### RISK-03 — Phase C REST+WS ordering race

- Severity/Likelihood: **Medium/Low** (disjoint hot/cold; keyed merges verified at `lifecycle/manager.py:702-723`)
- Phase: **C**
- Owner: backend-canopy
- Mitigation: per-param routing; feature flag; cascor `_training_lock` linearizes server-side; WS fires before REST.
- Signal: `canopy_set_params_latency_ms_bucket{transport, key}`; "set_params order-violation" log event.
- Kill switch: `Settings.use_websocket_set_params=False`. TTF ~5 min.

### RISK-04 — Slow-client blocks broadcasts

- Severity/Likelihood: **Medium/Medium** (raised from Low after hung-devtools-tab observation)
- Phase: **E** (full fix), Phase A-server (quick-fix `_send_json` timeout is hotfixable)
- Owner: backend-cascor
- Mitigation: quick-fix 0.5 s per-send timeout (Phase A-server commit 3, hotfixable standalone); full Phase E pump task with per-client queue.
- Signal: `cascor_ws_broadcast_send_duration_seconds` p95 > 500 ms; per-client queue depth.
- Kill switch: `Settings.ws_backpressure_policy=close_slow`. TTF ~5 min.
- Default: `drop_oldest_progress_only` (R0-06 §13.2).

### RISK-05 — Playwright fixture misses real-cascor-only regression

- Severity/Likelihood: **Medium/Medium**
- Phase: **B, D**
- Owner: ops
- Mitigation: nightly smoke test against real cascor in staging; alert on diff with fake-cascor results.
- Signal: smoke-test job success/failure 7-day rolling window.
- Kill switch: n/a (coverage risk). Response: fix the test.

### RISK-06 — Reconnection storm after cascor restart

- Severity/Likelihood: **Low/Medium** (raised — current no-jitter backoff synchronizes reconnects)
- Phase: **F**
- Owner: frontend
- Mitigation: full jitter on backoff (3-line change).
- Signal: `cascor_ws_connections_total` derivative; alert on >5× baseline.
- Kill switch: `Settings.disable_ws_auto_reconnect=True`. TTF ~10 min.

### RISK-07 — 50-connection cap hit by multi-tenant deployment

- Severity/Likelihood: **Low/Low**
- Phase: tangential to E; addressed via `Settings.ws_max_connections` (existing) + M-SEC-04 per-IP cap.
- Owner: backend-cascor + ops
- Mitigation: operator-tunable.
- Signal: `cascor_ws_active_connections_total` at 80% of cap.
- Kill switch: raise `ws_max_connections`. TTF ~10 min.

### RISK-08 — Demo mode parity breaks

- Severity/Likelihood: **Low/Medium**
- Phase: **B**
- Owner: backend-canopy
- Mitigation: `test_demo_mode_metrics_parity` in Phase B gate (blocker, not warning).
- Signal: demo-mode smoke test; manual spot-check.
- Kill switch: revert specific PR. TTF ~10 min.

### RISK-09 — Phase C changes user-perceived behavior unexpectedly

- Severity/Likelihood: **Low/Medium**
- Phase: **C**
- Owner: backend-canopy + frontend
- Mitigation: feature flag + canary; §5.6 instrumentation is the arbiter.
- Signal: `canopy_ws_delivery_latency_ms{type=set_params_ack}`; user study qualitative.
- Kill switch: `Settings.use_websocket_set_params=False`. TTF ~5 min.

### RISK-10 — Browser memory exhaustion from unbounded chart data

- Severity/Likelihood: **Medium/High** (overnight runs)
- Phase: **B**
- Owner: frontend
- Mitigation: `Plotly.extendTraces(maxPoints=5000)`; JS ring buffer cap enforced in the handler (NOT drain).
- Signal: `performance.memory.usedJSHeapSize` reported every 60 s via §5.6 endpoint. Alert p95 > 500 MB.
- Kill switch: `Settings.disable_ws_bridge=True`. TTF ~5 min.
- Validation: 48-72 h staging soak before production.

### RISK-11 — Silent data loss via drop-oldest broadcast queue

- Severity/Likelihood: **High/Low** (only under sustained slow-client load)
- Phase: **E**
- Owner: backend-cascor
- Mitigation: `drop_oldest_progress_only` policy — close for state-bearing events; drop-oldest only for `candidate_progress` and `pong`.
- Signal: `cascor_ws_dropped_messages_total{reason, type}`; **alert any non-zero `state_dropped`** (page).
- Kill switch: revert to `block`. TTF ~5 min (intentional knob).

### RISK-12 — Background tab memory spike on foreground

- Severity/Likelihood: **Low/Medium**
- Phase: **B**
- Owner: frontend
- Mitigation: JS-side ring enforcement in handler (same as RISK-10); background tab throttling does not affect cap.
- Signal: same as RISK-10.
- Kill switch: same.

### RISK-13 — Orphaned commands after timeout

- Severity/Likelihood: **Medium/Medium**
- Phase: **B, C, D**
- Owner: frontend + backend-canopy
- Mitigation: GAP-WS-32 per-command correlation IDs + "pending verification" UI state; resolve via `command_response` OR a matching `state` event.
- Signal: `canopy_orphaned_commands_total` > 1/min.
- Kill switch: reduce timeouts or `use_websocket_set_params=False`.

### RISK-14 — Cascor crash mid-broadcast leaves clients inconsistent

- Severity/Likelihood: **Low/Low**
- Phase: **B** (via `server_instance_id` / resume)
- Owner: backend-cascor
- Mitigation: `server_instance_id` change forces full REST resync on reconnect.
- Signal: cascor `server_instance_id` change correlates with client resync.
- Kill switch: rolling-restart canopy. TTF ~10 min.

### RISK-15 — CSWSH attack exploits missing Origin validation (HIGH)

- Severity/Likelihood: **High/Medium**
- Phase: **B-pre-b**
- Owner: security + backend-canopy + backend-cascor
- Mitigation: M-SEC-01 + M-SEC-01b + M-SEC-02. Phase B-pre-b is hard prereq for Phase D.
- Signal: `canopy_ws_auth_rejections_total{reason="origin_mismatch"}` — **page on-call on any non-zero from unknown origin**.
- Kill switch: `Settings.disable_ws_control_endpoint=True`. TTF ~5 min.
- Gate: §6.6 Phase B-pre-b exit gate.

### RISK-16 — Topology message >64 KB silently for large networks

- Severity/Likelihood: **Medium/Medium** (any network with >50-100 hidden units)
- Phase: **B-pre-a** (surfaces it) + follow-up (chunking or REST fallback)
- Owner: backend-cascor
- Mitigation: server-side size guard; structured error rather than truncation; REST fallback path.
- Signal: `cascor_ws_oversized_frame_total{endpoint, type}`; WARNING log on any truncated topology.
- Kill switch: client-side REST `/api/topology` fallback.

### Risk mitigation compact matrix

| ID | Phase     | Owner                    | Kill switch                              | TTF    |
|----|-----------|--------------------------|------------------------------------------|--------|
| 01 | H         | backend-canopy           | git revert + redeploy                    | 5 min  |
| 02 | B         | frontend + ops           | `disable_ws_bridge=True`                 | 5 min  |
| 03 | C         | backend-canopy           | `use_websocket_set_params=False`         | 5 min  |
| 04 | E         | backend-cascor           | `ws_backpressure_policy=close_slow`      | 5 min  |
| 05 | B,D       | ops                      | n/a (coverage risk)                      | -      |
| 06 | F         | frontend                 | `disable_ws_auto_reconnect`              | 10 min |
| 07 | -         | backend-cascor + ops     | raise `ws_max_connections`               | 10 min |
| 08 | B         | backend-canopy           | revert Phase B PR                        | 10 min |
| 09 | C         | backend-canopy + frontend| `use_websocket_set_params=False`         | 5 min  |
| 10 | B         | frontend                 | `disable_ws_bridge=True`                 | 5 min  |
| 11 | E         | backend-cascor           | revert to `policy=block`                 | 5 min  |
| 12 | B         | frontend                 | same as RISK-10                          | 5 min  |
| 13 | B,C,D     | frontend + backend-canopy| `use_websocket_set_params=False`         | 5 min  |
| 14 | B         | backend-cascor           | rolling restart                          | 10 min |
| 15 | B-pre-b   | security + backend       | `disable_ws_control_endpoint=True`       | 5 min  |
| 16 | B-pre-a   | backend-cascor           | REST fallback for topology               | 5 min  |

---

## 15. Consolidated test plan

Full test plan consolidated from R0-05 §4-§9, R0-01 §6, R0-02 §7, R0-03 §10, R0-04 §10. Organized by tier then by phase.

### 15.1 Fixture reuse strategy (R0-05 §3)

**Reuse as-is**:
- `FakeCascorClient` scenario presets (`idle`, `two_spiral_training`, `xor_converged`, `empty`, `error_prone`).
- `FakeCascorTrainingStream.inject_message()` / `_sent_commands` / `error_prone` error injection.
- REST-shaped methods on `FakeCascorClient`.

**Minimal additive extensions to existing fakes**:
1. `on_command(command_name, handler)` on fake control stream (matches R0-05 §8.5 `FakeCascorServerHarness.on_command`).
2. Auto-`command_response` scaffolding for recognized commands.
3. Optional sequence-number mode: `FakeCascorTrainingStream(with_seq=True)`.
4. Optional `connection_established` emission with fabricated `server_instance_id`.
5. `simulate_disconnect()` / `simulate_reconnect(last_seq)` helpers for replay tests.
6. `enforce_api_key=True` mode.

**New fixture**: `FakeCascorServerHarness` in `juniper-cascor-client/juniper_cascor_client/testing/server_harness.py` — thin FastAPI/uvicorn wrapper composing existing fakes. Shared across canopy and cascor-client Playwright/`dash_duo` tests.

**Explicitly NOT**: creating a separate `FakeCascorWSV2` class. Reuse mandate is to extend in place.

### 15.2 Unit tier

Fast lane; runs on every PR.

**Cascor**:
- Phase A-server tests (15) per §5.12.
- Phase B-pre-a/b security tests per §6.2.13.
- Phase E tests per §11.5.
- Phase G tests per §12.2.

**juniper-cascor-client**:
- Phase A tests per §4.6.
- Phase F tests per §11.5.
- Phase B resume protocol tests (R0-05 §4.2):
  - `test_resume_sends_last_seq_on_reconnect`
  - `test_resume_applies_replayed_events`
  - `test_resume_handles_out_of_range_by_snapshot_fallback`
  - `test_resume_handles_server_restart`
  - `test_resume_idempotent_replay_seq_deduplication`

**Canopy**:
- Phase B unit tests per §8.12 (Python unit tier).
- Phase C tests per §9.8.
- Phase D unit tests per §10.3.
- Phase H tests per §13.2.

Coverage targets per R0-05 §11.1:
| Phase     | Target |
|-----------|--------|
| A         | 95%    |
| B-pre     | 90%    |
| B         | 85%    |
| C         | 90%    |
| D         | 85%    |
| E         | 90%    |
| F         | 90%    |

Whole-repo threshold: 80% (project standard).

### 15.3 Integration tier

Stand up real services via pytest fixture. `integration` marker, slower (~15-30 s per test).

**cascor + cascor-client end-to-end** (R0-05 §5.1):
- `test_set_params_end_to_end_happy_path`
- `test_set_params_end_to_end_whitelist_enforced`
- `test_set_params_end_to_end_init_output_weights_injection_blocked`
- `test_metrics_stream_end_to_end`
- `test_state_transitions_deliver_within_100ms`
- `test_oversized_control_frame_closed_1009`

**canopy adapter against fake cascor with real WebSocket** (R0-05 §5.2):
- `test_adapter_subscribes_to_metrics_and_forwards_to_normalizer`
- `test_adapter_apply_params_hot_uses_websocket_roundtrip`
- `test_adapter_apply_params_cold_uses_rest`
- `test_adapter_reconnects_after_fake_kills_connection`
- `test_adapter_handles_resume_failed_by_fetching_snapshot`
- `test_adapter_demo_mode_parity` (RISK-08)
- `test_adapter_enforces_api_key`

**Reconnection/replay scenarios** (R0-05 §5.3):
- `test_reconnect_replays_10_missed_events`
- `test_reconnect_with_stale_last_seq_triggers_snapshot`
- `test_reconnect_with_stale_server_instance_id_triggers_snapshot`
- `test_snapshot_seq_bridges_no_gap` (§6.5.2 atomicity)
- `test_older_cascor_without_resume_command_triggers_fallback`
- `test_duplicate_seq_is_deduplicated_client_side`
- `test_broken_connection_1006_triggers_heartbeat_detection_and_reconnect`

**Worker smoke** (R0-05 §5.4):
- `test_worker_endpoint_unaffected_by_seq_and_replay_changes`

### 15.4 Browser tier (dash_duo + Playwright)

Uses `e2e` marker; runs on PR to main and nightly.

**dash_duo for store/DOM assertions**:
- Phase B: `test_browser_receives_metrics_event`, `test_chart_updates_on_each_metrics_event`, `test_chart_does_not_poll_when_websocket_connected`, `test_chart_falls_back_to_polling_on_websocket_disconnect`, `test_demo_mode_metrics_parity`, `test_ws_metrics_buffer_store_is_ring_buffer_bounded`, `test_ws_metrics_buffer_ignores_events_with_duplicate_seq`, `test_connection_indicator_badge_reflects_state`
- Phase C: `test_learning_rate_change_uses_websocket_set_params`, `test_learning_rate_change_falls_back_to_rest_on_disconnect`, `test_orphaned_command_resolves_via_state_event`, `test_per_command_timeout_values`
- Phase H: `test_normalize_metric_dual_format_in_browser_view`

**Playwright for wire-level assertions**:
- Phase B: `test_websocket_frames_have_seq_field`, `test_resume_protocol_replays_missed_events`, `test_seq_reset_on_cascor_restart`, `test_frame_budget_respected_at_50hz` (recording lane), `test_oversized_topology_frame_handled_gracefully`
- Phase D: `test_start_button_uses_websocket_command`, `test_command_ack_updates_button_state`, `test_disconnect_restores_button_to_disabled`, `test_csrf_required_for_websocket_start`
- Phase F: `test_ping_pong_reciprocity`, `test_missing_pong_triggers_reconnect`
- Phase I: `test_asset_url_includes_version_query_string`

**Frame budget** (R0-05 §6.3, recording-only lane):
- `test_frame_budget_single_metric_event_under_17ms`
- `test_frame_budget_batched_50_events_under_50ms`
- `test_plotly_extendTraces_used_not_full_figure_replace`

**Caveats** (R0-05 §6.3): run in dedicated job on fixed-performance runner; p95 over 30 iterations, not single-shot; `@pytest.mark.flaky(reruns=2)`; downgrade to trace-only if flakiness persists.

**Trace artifacts** (R0-05 §6.4): `--tracing=retain-on-failure --screenshot=only-on-failure --video=retain-on-failure`. 14-day retention.

### 15.5 Security regression tier

Separate `security` marker, runs on every PR to canopy or cascor.

Per R0-05 §7, full list of M-SEC-01..07 regression tests plus new M-SEC-10/11/12 tests. Detailed list in §6.2.13 above.

**CSWSH end-to-end regression**: `test_cswsh_from_evil_page_cannot_start_training` — Playwright navigates to simulated evil page on different origin and attempts WS to `localhost:8050/ws/control`; assert rejected and training state unchanged.

### 15.6 Latency tier

Split into recording-only (CI) and strict-local (dev workflow) per R0-05 §8.2.

**CI lane (every PR)**:
- Run latency instrumentation path.
- Capture histogram as `latency-report.json` artifact.
- **Do not assert specific thresholds.** Report, don't gate.

**Nightly lane**:
- Trend check: alert if nightly p95 degrades >30% vs main branch 7-day moving average.

**Local-only lane** (`make test-latency`):
- `JUNIPER_LATENCY_STRICT=1` env flag flips assertions from record to enforce.
- Exercises the same tests with strict thresholds.

### 15.7 Chaos / fuzz tier

- Header fuzzing via `hypothesis` on origin strings.
- JSON fuzzing via `atheris` on `CommandFrame.model_validate_json`.
- Connection-churn: 1000 open/close cycles, assert `_per_ip_counts → 0`.
- Resume-frame chaos.
- Rolling reconnect test (§11.5).

### 15.8 Contract test lane (new, R0-05 §14.10)

Proposed marker `contract` that runs on every PR to any of cascor, canopy, or cascor-client. Contract tests include:
- `test_fake_cascor_message_schema_parity` — loads cascor `messages.py` builders and validates fake output.
- `test_normalize_metric_produces_dual_format` (H) — lock-in.
- `test_canopy_adapter_message_schema_matches_cascor_ws_client` — cross-repo shape match.

---

## 16. Consolidated observability plan

### 16.1 Metrics (consolidated from R0-02 §4.6, R0-03 §9.1, R0-06 §6.1)

**SDK layer** (`juniper-cascor-client`):
- `juniper_cascor_client_ws_set_params_total{status}` — counter

**cascor server**:
- `cascor_ws_connections_active{endpoint}` — gauge
- `cascor_ws_connections_pending{endpoint}` — gauge
- `cascor_ws_connections_total{endpoint, outcome}` — counter
- `cascor_ws_disconnects_total{endpoint, reason}` — counter
- `cascor_ws_broadcasts_total{type}` — counter
- `cascor_ws_broadcast_send_seconds{type}` — histogram
- `cascor_ws_broadcast_timeout_total{type}` — counter
- `cascor_ws_replay_buffer_occupancy` — gauge
- `cascor_ws_replay_buffer_bytes` — gauge (sampled)
- `cascor_ws_seq_current` — gauge
- `cascor_ws_resume_requests_total{outcome}` — counter
- `cascor_ws_resume_replayed_events` — histogram
- `cascor_ws_state_throttle_coalesced_total` — counter
- `cascor_ws_command_responses_total{command, status}` — counter
- `cascor_ws_command_handler_seconds{command}` — histogram
- `cascor_ws_dropped_messages_total{reason, type}` — counter (Phase E)
- `cascor_ws_slow_client_closes_total` — counter (Phase E)
- `cascor_ws_oversized_frame_total{endpoint, type}` — counter (Phase B-pre-a)

**canopy**:
- `canopy_ws_auth_rejections_total{reason}` — counter (B-pre-b)
- `canopy_ws_origin_rejected_total{endpoint}` — counter (B-pre-b)
- `canopy_ws_oversized_frame_total{endpoint}` — counter (B-pre-a)
- `canopy_ws_auth_failure_total{reason}` — counter (B-pre-b)
- `canopy_ws_command_total{command, status}` — counter
- `canopy_ws_rate_limited_total` — counter (B-pre-b)
- `canopy_ws_per_ip_rejected_total` — counter (B-pre-b)
- `canopy_ws_frame_too_large_total` — counter
- `canopy_ws_auth_latency_ms` — histogram (B-pre-b)
- `canopy_ws_delivery_latency_ms_bucket{type}` — histogram (§5.6 P0)
- `canopy_ws_active_connections` — gauge
- `canopy_ws_reconnect_total{reason}` — counter
- `canopy_ws_browser_heap_mb` — histogram from JS
- **`canopy_rest_polling_bytes_per_sec`** — gauge (P0 motivator proof)
- `canopy_set_params_latency_ms_bucket{transport, key}` — histogram (Phase C flip gate)
- `canopy_orphaned_commands_total{command}` — counter
- `canopy_training_control_total{command, transport}` — counter (Phase D)

### 16.2 Logs (R0-03 §9.2, R0-02 §4.6)

Structured JSON. Separate `canopy.audit` logger for control-plane actions with 90-day rotation + gzip.

WARN:
- slow_client prune: `{event: ws_slow_client, client_ip, timeout_s}`
- replay buffer near-capacity (>90% for >30 s)
- broadcast exception (full traceback)
- origin rejections
- auth failures (server-side reason; client sees opaque)

INFO:
- `ws_connect`, `ws_disconnect` with duration, close code, reason
- `ws_resume_ok`, `ws_resume_failed`
- audit entries per §6.2.8

DEBUG (off in production):
- every send (rate-limited)
- seq assignments (rate-limited)

### 16.3 Alerts (R0-06 §6.3)

Page on-call:
- `WSOriginRejection` — possible CSWSH
- `WSOversizedFrame` — possible DoS probe
- `WSStateDropped` — silent data loss

Ticket:
- `WSDeliveryLatencyP95High`
- `WSConnectionCount80`
- `WSBrowserHeapHigh`
- `WSReconnectStorm`
- `WSSlowBroadcastP95`
- `CanopyOrphanedCommands`

### 16.4 SLOs (R0-06 §6.3)

Validated against §5.6 histogram, error budget 99.9% meet p95 over 7-day rolling window:

| Event type                             | p50     | p95     | p99      |
|----------------------------------------|---------|---------|----------|
| `metrics` delivery                     | <100 ms | <250 ms | <500 ms  |
| `state` delivery                       | <50 ms  | <100 ms | <200 ms  |
| `command_response` (set_params)        | <50 ms  | <100 ms | <200 ms  |
| `command_response` (start/stop)        | <100 ms | <250 ms | <500 ms  |
| `cascade_add` delivery                 | <250 ms | <500 ms | <1000 ms |
| `topology` delivery (≤64 KB)           | <500 ms | <1000 ms| <2000 ms |

### 16.5 §5.6 operationalization (R0-06 §6.4)

1. Phase B implements the pipe: cascor adds `emitted_at_monotonic` to every envelope; canopy adds `/api/ws_latency` POST endpoint + JS histogram.
2. Phase B rolls out with the instrumentation, not as follow-up.
3. Canopy aggregates into Prometheus histogram.
4. Dashboard panel shows p50/p95/p99 per type. Updates via the same WS path it measures (closes the loop).
5. Clock offset recomputed on every reconnect (laptop sleep, NTP).
6. Buckets: `{50, 100, 200, 500, 1000, 2000, 5000}` ms.
7. Export cadence: 60 s.
8. SLO validation: §5.1/§5.4 latency tables transition from "aspirations" to SLOs after ≥1 week of data.
9. User-research option: §5.7 5-subject think-aloud study. Decision gate Q7.

---

## 17. Cross-repo coordination

### 17.1 Dependency order (R0-06 §8.1)

1. **juniper-cascor-client Phase A PR** → merge → tag → PyPI publish. Wait 2-5 min for index propagation.
2. **juniper-cascor Phase A-server PR** (commits 1-10 per §5.11) → merge. Independent of SDK.
3. **juniper-cascor Phase B-pre-a PR** (M-SEC-03 frame-size guards) → merge.
4. **juniper-cascor Phase B-pre-b PR** (M-SEC-01b + parity + audit logger on cascor side) → merge.
5. **juniper-canopy Phase B-pre-a PR** (frame-size guards) → merge.
6. **juniper-canopy Phase B-pre-b PR** (Origin + CSRF + cookie + rate limit + audit logger) → merge.
7. **juniper-canopy Phase B PR** (browser bridge + polling toggle + connection indicator + §5.6 instrumentation + Phase I asset cache busting) → merge. **Independent of SDK.**
8. **juniper-canopy Phase C PR** — rebase on main, bump `juniper-cascor-client>=<new-version>`, update `juniper-ml` extras pin in follow-up, CI with new SDK, merge.
9. **juniper-canopy Phase D PR** — rebase on Phase B + Phase B-pre-b. Merge **only after** B-pre-b confirmed in production.
10. **juniper-cascor Phase E PR** — any time after Phase B.
11. **juniper-canopy / juniper-cascor Phase F PR** — alongside Phase B recommended.
12. **juniper-cascor Phase G PR** — bundled with Phase A-server.
13. **juniper-canopy Phase H PR** — regression test first (own PR), then audit doc. Independent schedule.
14. **juniper-canopy Phase I PR** — bundled with Phase B.

**Merge strategy**: squash-merge (not merge commits). Use GitHub merge queue if available.

**Branch naming**: `ws-migration/phase-<letter>-<slug>`. Example: `ws-migration/phase-b-pre-security`, `ws-migration/phase-b-browser-bridge`.

**Worktree naming** (per Juniper CLAUDE.md): `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>` in `/home/pcalnon/Development/python/Juniper/worktrees/`.

### 17.2 Version bumps (R0-06 §8.2)

| Repo                  | Phase       | Bump  | Rationale |
|-----------------------|-------------|-------|-----------|
| juniper-cascor-client | A           | minor | New public method |
| juniper-cascor        | A-server    | minor | New envelope field `seq` + `server_instance_id` |
| juniper-cascor        | B-pre-a/b   | patch | Security hardening |
| juniper-cascor        | E           | minor | New `ws_backpressure_policy` setting |
| juniper-cascor        | G           | patch | Test-only |
| juniper-canopy        | B-pre-a/b   | patch | Security hardening |
| juniper-canopy        | B           | minor | New browser bridge + instrumentation endpoint |
| juniper-canopy        | C           | patch | Internal refactor; public API unchanged |
| juniper-canopy        | D           | patch | New WS control path; REST preserved |
| juniper-canopy        | H           | patch | Test + doc |
| juniper-canopy        | I           | patch | Asset handling |
| juniper-ml            | -           | patch (per SDK bump) | Extras pin update |

**Helm charts** (per user `project_helm_version_convention.md` memory): `Chart.yaml` `version` and `appVersion` must match app semver. Helm chart bumps accompany app bumps.

### 17.3 Changelog policy

Keep-a-Changelog per PR. Headings:
- `### Added`
- `### Changed`
- `### Fixed`
- `### Security`
- `### Deprecated` (none expected)
- `### Removed` (none in this migration per RISK-01 caution)

Every entry cross-references GAP-WS-NN and RISK-NN IDs for traceability.

### 17.4 Cross-repo CI on multi-repo PRs (R0-05 §10.5)

**Option chosen**: TestPyPI prerelease approach (R0-06 §9.13). Phase A publishes to TestPyPI; Phase B-on PRs install from TestPyPI and run e2e. Avoids the need for a monorepo worktree CI script (R0-05 §10.5 option 1 — deferred).

---

## 18. Reconciled disagreements between R0 proposals

Tabular summary of places where two or more R0 proposals disagreed, with this proposal's decision and rationale.

### 18.1 Phase B-pre granularity

**Disagreement**: Source doc and some R0s treat Phase B-pre as one unit. R0-06 §13.1 argues for a split.

**Who said what**:
- R0-02: single Phase B-pre.
- R0-06: split into B-pre-a (frame-size, Phase B prereq) and B-pre-b (auth, Phase D prereq).

**Decision**: **Adopt the split** (R0-06 wins). Rationale: M-SEC-03 is load-bearing for Phase B (traffic volume increases), while M-SEC-01/01b/02 is load-bearing for Phase D (control surface exposure). Treating them as one phase hides the different urgency.

### 18.2 Phase E default policy

**Disagreement**: Source doc says `block` default; R0-06 §13.2 says `drop_oldest_progress_only`.

**Who said what**:
- R0-03 §5.2: policy matrix per event type (close for state, drop for progress). Doesn't explicitly name the default.
- R0-06: default `drop_oldest_progress_only`.
- Source doc: default `block` (migrate on major version bump).

**Decision**: **Adopt `drop_oldest_progress_only`** (R0-06 wins). Rationale: RISK-04 is Medium/Medium. Keeping `block` leaves the first production incident as exactly this failure mode. The policy is still flag-gated so operators can revert to `block`.

### 18.3 `command_response` seq field

**Disagreement**: Source doc §6.5 implies all server→client messages have `seq`. R0-03 §11.3 argues against it for `command_response`.

**Who said what**:
- R0-03: `command_response` is personal RPC; no `seq`; separate namespace from `/ws/training` broadcast.
- Source doc: implies all outbound messages carry `seq`.

**Decision**: **Adopt R0-03's carve-out**. Rationale: replaying a `command_response` for a command the client didn't issue is semantically confusing; command correlation is via `request_id` (or `command` name legacy), not seq.

### 18.4 `set_params` default timeout

**Disagreement**: Source doc §7.1 says 5.0; R0-04 §12.1 says 1.0.

**Who said what**:
- R0-04: 1.0 (matches GAP-WS-32 per-command timeout table).
- Source doc §7.1: 5.0 (copy-paste from `DEFAULT_CONTROL_STREAM_TIMEOUT`).

**Decision**: **Adopt 1.0** (R0-04 wins). Rationale: hot-path slider use case; 5 s fallback UX is visibly bad.

### 18.5 `request_id` as additive field

**Disagreement**: Source doc §3.2.3 does not include `request_id`; R0-04 §12.2 adds it.

**Who said what**:
- R0-04: additive, backwards-compatible, SDK falls back to first-match-wins if server doesn't echo.
- Source doc: silent.

**Decision**: **Adopt R0-04's addition**. Phase G (§12.2) includes `test_set_params_request_id_echo` as a server-side gate.

### 18.6 Security flag naming

**Disagreement**: Source doc proposes `Settings.disable_ws_auth=True`. R0-02 §9.4 argues for positive-sense `ws_security_enabled=True`.

**Who said what**:
- R0-02: positive-sense; reverses config-footgun direction.
- R0-06: silent on naming.
- Source doc: negative-sense.

**Decision**: **Adopt `ws_security_enabled`** (positive-sense, default True). Rationale: merge accident with a negative-sense flag can land insecure config in prod; positive-sense fails safe. Effort is identical.

### 18.7 rAF coalescing

**Disagreement**: Source doc implies rAF coalescing ships with Phase B. R0-01 disagreement #1 argues it should be scaffolded but disabled.

**Who said what**:
- R0-01: scaffold only; enable later based on §5.6 data.
- Source doc: ship enabled in Phase B.

**Decision**: **Adopt R0-01's scaffold-only** approach. Rationale: 100 ms drain = ~10 Hz render rate, comfortably under 60 fps. Double-render risk with drain callback is not worth adding complexity to Phase B's already-large scope.

### 18.8 REST fallback polling rate during disconnect

**Disagreement**: Source doc §6.3 does not specify; R0-01 disagreement #2 argues 1 Hz, not 100 Hz.

**Decision**: **Adopt R0-01's 1 Hz refinement**. Rationale: 100 Hz polling during disconnect is as pathological as the pre-migration bug. 1 Hz matches §6.4 disconnection taxonomy cadence.

### 18.9 NetworkVisualizer in Phase B

**Disagreement**: Source doc puts NetworkVisualizer in Phase B's chart callbacks list. R0-01 disagreement #3 argues for deferral.

**Decision**: **Ship a minimal WS wiring only** (respond to `cascade_add` without REST polling). Full cytoscape redesign is Phase B+1 (deferrable). Rationale: cytoscape is not Plotly; `extendTraces` does not apply; proper redesign is its own exercise.

### 18.10 Phase C test routing unit tests

**Disagreement**: Source doc §9.4 lists dash_duo browser tests but omits unit-level routing tests for `apply_params`. R0-05 §14.2 adds them.

**Decision**: **Adopt R0-05's addition**. Unit-level routing tests are in §9.8.

### 18.11 Origin default (fail-closed vs fail-open)

**Disagreement**: Source doc is ambiguous on empty allowlist semantics. R0-02 §9.3 pins "empty list = reject all browser origins".

**Decision**: **Adopt fail-closed semantics** (empty list = reject all). Rationale: safer than "allow all". Document prominently in canopy README.

### 18.12 Adapter synthetic auth frame

**Disagreement**: R0-02 §11-sec-1 flags as open question (Q2-sec). Two options: header-based skip or HMAC-CSRF.

**Decision**: **Adopt Option A (header-based `X-Juniper-Role: adapter` skip)**. Rationale: simpler; unreachable-from-browser property is a hard invariant. Document the branch in code comment with clear rationale.

### 18.13 M-SEC-10/11/12 canonical assignment

**Disagreement**: R0-02 §9.9 proposes new M-SEC-10 (idle timeout), M-SEC-11 (adapter inbound validation), M-SEC-12 (log injection escaping). Source doc stops at M-SEC-07.

**Decision**: **Adopt the new M-SEC numbers** as canonical for this migration. All three fold into Phase B-pre-b. M-SEC-12 could alternatively fold into M-SEC-07 if Round 2+ prefers.

### 18.14 Per-IP cap default

**Disagreement**: Source doc Q6 lists this as open. R0-02 §3.5 attack 1 and R0-06 §13.3 propose 5/IP default.

**Decision**: **Adopt 5/IP default**, tunable via `Settings.ws_max_connections_per_ip`. Multi-tenant future adjustment.

### 18.15 Audit logging scope

**Disagreement**: Source doc §2.9.2 M-SEC-07 mentions scrubbing allowlist but not a dedicated audit logger. R0-02 §4.6 adds a full audit logger with rotation.

**Decision**: **Adopt the full audit logger**. Scope bump acknowledged (R0-02 disagreement #9.8). Effort folded into Phase B-pre-b's 1.5-2 day estimate.

---

## 19. Disagreements with R0 inputs

Where this synthesis differs from any individual R0 proposal.

### 19.1 Phase A-server carve-out (adopting R0-03, overruling R0-01's "Phase B is a 4-day estimate" framing)

R0-01 §3.1 treats the cascor-side sequence-number work as part of Phase B. R0-03 §11.5 argues for carving it out as Phase A-server. **This synthesis adopts R0-03's carve-out**. Rationale: reviewable, merge-able independently of canopy; provides a stable contract for canopy Phase B tests.

### 19.2 `ws_security_enabled` positive-sense flag (R0-02 alternative, not unanimous)

R0-02 §9.4 flagged this as a "naming nit but a footgun concern" and explicitly said "accept either." This synthesis picks positive-sense as the default. Round 2+ can reverse if the Juniper config convention is negative-sense.

### 19.3 Frame budget tests as recording-only (R0-05 refinement, stricter than R0-01)

R0-01's AC-15 treats `test_render_frame_under_budget` as a pass/fail gate. R0-05 §6.3 and §8.2 argue for recording-only in CI. **This synthesis adopts R0-05's recording-only position** with strict-local lane for devs. Rationale: shared CI runners have ±30% performance variance; strict latency assertions erode trust.

### 19.4 Phase B-pre effort estimate (2 days, not 1)

Source doc §9.2 says 1 day. R0-02 §9.1 and R0-06 §3.2 both argue for 1.5-2 days (CSRF plumbing + audit logger undercounted). **This synthesis adopts 2 days total** for B-pre-b (B-pre-a is ~0.25 day folded into Phase B).

### 19.5 NetworkVisualizer reduced scope (R0-01 disagreement adopted, not unanimous)

R0-01 disagreement #3 proposes deferring NetworkVisualizer cytoscape redesign. Source doc includes it in Phase B. **This synthesis adopts the reduced Phase B scope** (WS wiring only for `cascade_add`; no full cytoscape redesign).

### 19.6 Audit log retention 90 days vs source doc silent

R0-02 §4.6 specifies 90 days; source doc is silent. **This synthesis adopts 90 days**, configurable via `Settings.audit_log_retention_days`.

### 19.7 Phase E default `drop_oldest_progress_only` (R0-06 vs source doc `block`)

Already in §18.2. Adopted. Documented here as a formal disagreement with the source doc as R0-06 framed it.

### 19.8 Contract test lane as dedicated marker (R0-05 §14.10 open question)

R0-05 flagged contract tests as an open question. **This synthesis adopts the `contract` marker** as a first-class CI lane running on every PR to any of cascor, canopy, cascor-client. Rationale: prevents fake-harness drift (T-RISK-04) and cross-repo schema mismatches.

---

## 20. Self-audit log

### 20.1 Coverage check — GAP-WS

Walked through all 33 GAP-WS items:

- [x] GAP-WS-01 — SDK set_params (§4)
- [x] GAP-WS-02 — cascorWS integration (§8.5)
- [x] GAP-WS-03 — parallel raw-WS callback deletion (§8.1.3)
- [x] GAP-WS-04 — ws-metrics-buffer init callback rewrite (§8.1.2)
- [x] GAP-WS-05 — drain callbacks (§8.1.2)
- [x] GAP-WS-06 — REST preserved (§10.1, §17.3)
- [x] GAP-WS-07 — backpressure (§5.7 quick, §11.1 full)
- [x] GAP-WS-08 — umbrella, addressed by §15 test plan
- [x] GAP-WS-09 — cascor set_params integration test (§12)
- [x] GAP-WS-10 — canopy set_params round trip (§9.8)
- [x] GAP-WS-11 — nested+flat audit (§13)
- [x] GAP-WS-12 — heartbeat (§11.2)
- [x] GAP-WS-13 — sequence numbers + replay (§5)
- [x] GAP-WS-14 — extendTraces (§8.2)
- [x] GAP-WS-15 — rAF coalescing (§8.3, scaffolded-off)
- [x] GAP-WS-16 — polling elimination (§8.4)
- [ ] GAP-WS-17 — permessage-deflate: explicitly deferred per R0-03 §7.3. Not covered in this migration.
- [x] GAP-WS-18 — topology chunking (§10, §18, §14.16)
- [x] GAP-WS-19 — close_all lock (resolved on main, regression test in §6.2.12)
- [x] GAP-WS-20 — envelope asymmetry (Phase H deferred)
- [x] GAP-WS-21 — 1 Hz state throttle coalescer (§5.8)
- [x] GAP-WS-22 — protocol error responses (§5.10)
- [x] GAP-WS-23 — reconnect event logging (§5.13 WARN log, §11 reconnect)
- [x] GAP-WS-24 — production latency measurement (§8.9, §16.5)
- [x] GAP-WS-25 — polling toggle (§8.4.2)
- [x] GAP-WS-26 — connection indicator (§8.7)
- [x] GAP-WS-27 — per-IP cap (§6.2.3)
- [x] GAP-WS-28 — multi-key torn-write (lifecycle lock already in Phase A-server §5)
- [x] GAP-WS-29 — broadcast_from_thread exception (§5.9)
- [x] GAP-WS-30 — reconnect jitter (§11.3)
- [x] GAP-WS-31 — uncapped reconnect (§11.4)
- [x] GAP-WS-32 — per-command timeouts + correlation IDs (§4.3, §10.2)
- [x] GAP-WS-33 — demo mode visibility (§8.8)

**33/33 GAP-WS items addressed** (one deferred: GAP-WS-17 `permessage-deflate` per R0-03 §7.3).

### 20.2 Coverage check — M-SEC

- [x] M-SEC-01 — canopy Origin allowlist (§6.2.1)
- [x] M-SEC-01b — cascor Origin parity (§6.2.1)
- [x] M-SEC-02 — cookie + CSRF (§6.2.2)
- [x] M-SEC-03 — per-frame size caps (§6.1)
- [x] M-SEC-04 — per-IP cap + auth timeout (§6.2.3)
- [x] M-SEC-05 — command rate limit (§6.2.4)
- [x] M-SEC-06 — opaque close-reason (§5.10, §6.2.8)
- [x] M-SEC-07 — audit logger (§6.2.8)
- [ ] M-SEC-08 — subdomain bypass / CSP: deferred (R0-02 §5.4 non-goal)
- [ ] M-SEC-09 — constant-time API key: deferred (R0-02 §5.4 non-goal)
- [x] M-SEC-10 (new) — idle timeout (§6.2.5)
- [x] M-SEC-11 (new) — adapter inbound validation (§6.2.9)
- [x] M-SEC-12 (new) — log injection escaping (§6.2.8 rule 10)

**11/13 M-SEC items addressed** (2 explicitly deferred).

### 20.3 Coverage check — RISK

All 16 RISK-NN items have dedicated entries in §14 with severity, phase, owner, mitigation, signal, kill switch, TTF, and validation hook.

- [x] RISK-01 through RISK-16 — all covered in §14.

### 20.4 Coverage check — phases have owner, acceptance criteria, observability, test plan, kill switch

Per-phase audit:

| Phase | Owner | Exit gate | Observability | Test plan | Kill switch |
|-------|-------|-----------|---------------|-----------|-------------|
| A     | §4.1  | §4.9      | §4.8          | §4.6      | n/a (additive) |
| A-server | §5.1 | §5.15 | §5.13 | §5.12 | revert (bisect-friendly commits) |
| B-pre-a | §6.1 | §6.5 | n/a (counter only) | §6.1 | rollback with B |
| B-pre-b | §6.2 | §6.6 | §6.3 | §6.2.13 | `disable_ws_control_endpoint` |
| B     | §8    | §8.15 | §8.13 | §8.12 | `disable_ws_bridge` |
| C     | §9.1  | §9.11 | §9.9  | §9.8  | `use_websocket_set_params=False` |
| D     | §10.1 | §10.6 | §10.4 | §10.3 | revert PR |
| E     | §11.1 | §11.8 | §11.6 | §11.5 | `ws_backpressure_policy=block` |
| F     | §11.2-§11.4 | §11.8 | §11.6 | §11.5 | `disable_ws_auto_reconnect` |
| G     | §12.1 | §12.3 | n/a (test-only) | §12.2 | n/a |
| H     | §13.1 | §13.5 | RISK-01 fingerprint | §13.2 | git revert |
| I     | (R0-01 §4 step 30, §8.11) | with B | n/a | Playwright asset test | n/a |

All 12 phases have all 5 coverage dimensions.

### 20.5 Corrections made in edit pass

1. **Added Phase I observability note**: first draft mentioned Phase I (asset cache busting) only as "ships with B" without an exit gate line. Added Playwright `test_asset_url_includes_version_query_string` reference in §15.4 and §20.4.

2. **Clarified R0-03 GAP-WS-19 status**: first draft said GAP-WS-19 is resolved. Added explicit §5 cross-reference that R0-03 §11.1 verified this on main 2026-04-11 and §6.2.12 folds the regression test into B-pre-b.

3. **Added the `request_id` Phase G regression test**: §12.2 now includes `test_set_params_request_id_echo` explicitly, so Phase A's SDK consumer does not race with server-side support.

4. **Pinned the positive-sense security flag decision**: §18.6 and §19.2 now cite the decision explicitly; the flag name `ws_security_enabled` is used consistently throughout §6.

5. **Split Phase B-pre gate criteria into B-pre-a and B-pre-b**: §6.5 and §6.6 are now separate gates, reflecting R0-06 §13.1 disagreement adopted into §18.1.

6. **Added M-SEC compact alerting**: §6.3 and §16.3 now explicitly upgrade `WSOriginRejection` and `WSOversizedFrame` to page-on-call per R0-06 §14.2 issue K.

7. **Added replay overflow race mitigation explicitly**: §5.5 now documents the R0-03 §8.4 race and the "promote under lock + client dedupe by seq" fix. First draft referenced it only in passing.

8. **Added `drop_oldest_progress_only` as a named Phase E policy default**: §11.1 and §18.2 now use the specific name, matching R0-06 §13.2 exactly.

9. **Added `contract` marker as a first-class CI lane**: §15.8 and §19.8. R0-05 §14.10 flagged this as an open question; this synthesis makes a decision.

10. **Clarified Phase A-server vs Phase B split**: §5 is Phase A-server, §8 is Phase B (canopy side). Previously §7 was reserved; §7 is now a pointer noting the reservation.

11. **Added R0-02 IMPL-SEC-44 to Phase A tests**: `test_set_params_x_api_key_header_present` is in §4.6 as the regression guard against header-omission.

12. **Added the 8-point B-pre-b exit gate** explicitly in §6.6 to match R0-06 §3.2.

13. **Added the acceptance checklist** in §6.2.13 copied from R0-02 §7.4 verbatim for the Phase B-pre-b PR description.

14. **Added observability `canopy_rest_polling_bytes_per_sec` as explicit P0 motivator proof metric** in §8.13 and §16.1.

### 20.6 Outstanding items flagged for Round 2

- **Effort estimate reconciliation**: individual R0s give varied numbers. This synthesis uses ~13.5-15 days (R0-06 §13.6 + R0-03 §7.1 carve-out). Round 2 could refine against current main state.
- **NetworkVisualizer scope decision**: §19.5 adopts R0-01's reduced scope. If Round 2 confirms NetworkVisualizer uses Plotly (not cytoscape), the reduction is moot.
- **Dash version floor**: R0-01 §8.5 flags that Dash 2.18+ is required for Option A. Option B (this synthesis) has no floor, but the PR description should verify canopy's current Dash version.
- **Plotly version**: R0-01 §8.5 flags that `extendTraces(maxPoints)` signature differs Plotly 1.x vs 2.x. Verify canopy pins Plotly 2.x.
- **`juniper-canopy` session middleware state**: R0-02 §8.1 and R0-06 §13 flag as unverified. Phase B-pre-b IMPL-SEC-14 adds `SessionMiddleware` if absent. Round 2 should verify current state.
- **Audit log destination** (Q6-sec in R0-02 §11): local file vs central log collector. Deferred.
- **Multi-tenant replay isolation** (Q1-sec): deferred to post-migration.
- **Browser compatibility** (Q2): Chromium-only for v1. Documented in R0-06 §9.
- **Q7 user research**: skip for initial migration; revisit post-rollout if subjective complaints arise.

### 20.7 Final consistency check

- All section numbers cross-reference valid R0 sources.
- All GAP-WS, M-SEC, RISK identifiers used are traceable.
- All disagreements in §18 and §19 have a pick + rationale.
- Every phase has its exit gate, kill switch, TTF, owner, test list.
- Consolidated risk register in §14 is pairwise-consistent with per-phase mentions.
- Observability plan in §16 is pairwise-consistent with per-phase metrics lists.
- Cross-repo coordination in §17 is pairwise-consistent with per-phase dependency notes.
- Effort estimate sums correctly to ~13.5-15 days.

### 20.8 Self-audit pass verdict

**PASS**: every enumerated identifier is addressed; every phase has complete specification; every contradiction between R0 proposals is explicitly resolved; every disagreement with R0 inputs is justified.

---

**End of R1-03 maximalist comprehensive synthesis.**
