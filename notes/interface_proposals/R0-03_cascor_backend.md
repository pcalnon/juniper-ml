# Round 0 Proposal R0-03: Cascor Server Backend

**Specialization**: FastAPI WebSocket broadcaster, replay buffer, server_instance_id, reconnection
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE)

---

## 1. Scope

This proposal covers the cascor-server side of the WebSocket messaging pipeline. It is
Round 0 (initial), one of six parallel specialty angles. The goal is to define — at a
level specific enough that an implementer could land a PR without revisiting the
architecture doc — how the cascor server should evolve to support:

1. A bounded replay buffer for lossless reconnect (GAP-WS-13).
2. A `server_instance_id` UUID for clock-skew-immune restart detection (§6.5 step 2).
3. Monotonic per-server sequence numbers on every outbound envelope.
4. A broadcaster that cannot be stalled by a single slow client (GAP-WS-07 quick fix
   and full fix).
5. Clean endpoint contracts for `/ws/training` and `/ws/control` with resume-aware
   behavior on the training stream.
6. The set of prerequisites (call them "Phase A-server") that must land in
   `juniper-cascor` before the canopy-side Phase B browser-bridge work can begin.

**Explicit non-goals**:

- Security / auth / Origin validation / CSWSH (M-SEC-01..07). Another R0 agent owns
  that lane.
- The SDK-side `set_params` method in `juniper-cascor-client` (GAP-WS-01). Another R0
  agent.
- Canopy browser bridge, Plotly extendTraces, dcc.Store drain callbacks (GAP-WS-02..05,
  14, 15, 25, 26). Another R0 agent.
- Dashboard-level latency measurement histogram and latency SLO work (GAP-WS-24).
  Touches cascor server-side timestamps only in the minimal form described in §9.2.

**In scope but touched lightly (integration surfaces only)**:

- Training-thread → broadcaster handoff (`broadcast_from_thread`) — cascor-internal.
- Cascor lifecycle-manager's 1 Hz state throttle (GAP-WS-21) — this is upstream of the
  broadcaster and is in-scope because a fix here changes what the broadcaster sees.
- Protocol error responses on `/ws/control` (GAP-WS-22) — cascor server owns the
  contract.

---

## 2. Source-doc cross-references

The following sections of `WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3) are
the authoritative inputs. Every design choice below is anchored to at least one of
these.

| Area | Source anchor |
|---|---|
| Cascor WebSocket surface | §2.1, §2.2, §2.3 |
| Server→client message envelope | §2.3, §3.0, §3.1.x |
| Client→server envelope asymmetry | §3.0, §3.2.x |
| 1 Hz state throttle "drop filter" bug | §3.1.3, GAP-WS-21 |
| CR-025 `close_all()` lock status | §2.2, GAP-WS-19 |
| Disconnection taxonomy and close codes | §6.4 |
| Reconnection protocol + sequence numbers | §6.5 (and its 6.5.1-6.5.4 subsections) |
| Replay buffer contract | §6.5 step 3, §6.5.1 |
| Snapshot↔live handoff atomicity | §6.5.2 |
| Backpressure / slow-client handling | GAP-WS-07, §9.6 (Phase E) |
| Topology message 64 KB overflow | GAP-WS-18 |
| Per-IP caps (touches manager.py but is M-SEC-04) | §2.9.2 (out of scope here) |
| `broadcast_from_thread` future exception discard | GAP-WS-29 |
| Protocol error responses on `/ws/control` | §3.2.4, GAP-WS-22 |
| Phased implementation plan | §9 (especially §9.3 Phase B server-side items) |
| Risk register entries relevant to server backend | RISK-04, RISK-11, RISK-14, RISK-16 |

Note on version drift: the source doc was captured 2026-04-10. By 2026-04-11 the
cascor-side `close_all()` has been updated to hold `self._lock` properly (verified in
§11 disagreements below). GAP-WS-19 is effectively resolved on main.

---

## 3. Replay buffer design

### 3.1 Data structure and capacity

**Chosen data structure**: `collections.deque[tuple[int, dict]]` with `maxlen=1024`,
stored as an instance attribute on `WebSocketManager`. Each entry is
`(seq, envelope_dict)`.

Why deque:

- O(1) append + O(1) `popleft` on overflow (automatic eviction via `maxlen`).
- Python memory footprint is predictable — the deque is a doubly-linked list of
  64-slot blocks, so fixed overhead is small and dominated by the stored message
  dicts.
- Zero third-party deps, matches the style of the existing `manager.py`.
- Lookup by seq is O(n) in the worst case but n is bounded at 1024 and the common
  replay request walks from an index near the tail, so the amortized cost is a
  tight linear scan. Binary search is *not* worth the complexity because the deque
  is strictly monotonic in seq and 1024 is small.

**Why not alternatives considered**:

- `list[dict]` + manual slice eviction — O(n) eviction on every append; dropped.
- `dict[int, dict]` keyed by seq — needs a second structure for eviction order;
  dropped for complexity.
- `numpy.ndarray(dtype=object)` ring — no memory win for dict payloads; dropped.
- Write-behind to Redis — way out of scope for "bounded local ring" semantics and
  adds a failure mode that does not exist today.

**Capacity rationale (1024)**:

At cascor's steady-state event rate (~16 KB/s, derived in §1 of the source doc from
`~600 B/event × ~25 events/s` during an active candidate phase with metrics
interleaved), 1024 entries is approximately **40 seconds of history**. This comfortably
covers:

- The typical 5-second WiFi blip mentioned in §6.5 of the source doc.
- A browser tab backgrounded for ~30 seconds (Chromium throttles timers to 1 Hz in
  background, slowing the drain callback but not stopping it).
- A cascor graceful restart that completes in under ~20 seconds.

It does **not** cover:

- An overnight dashboard-left-open scenario across a cascor restart (server_instance_id
  will change — §4.2 — and the client falls back to a REST snapshot; the replay buffer
  is not the recovery path).
- A sustained >60 s disconnect during high-rate candidate-phase training (would exceed
  1024 events; client falls back to snapshot).

The 1024 number is an *operational parameter*, not a hard contract. It should live as
`Settings.ws_replay_buffer_size` (default 1024) so operators can tune it. The client's
`out_of_range` handling (snapshot fallback) is the correctness guarantee; the buffer
size is a latency/bandwidth tradeoff.

### 3.2 Sequence number assignment

**Contract**: every server→client message envelope emitted on `/ws/training`,
`/ws/control`, and any future canopy-aware endpoint carries a strictly monotonic
`seq: int` field. The sequence counter resets to 0 on cascor process start. It is
paired with `server_instance_id` so that a client comparing `seq` values across a
server restart cannot get false continuity.

**Assignment site**: sequence assignment MUST happen on the event-loop thread in a
single choke-point helper. Pseudocode for the new helper on `WebSocketManager`:

```python
async def _assign_seq_and_append(self, message: dict) -> dict:
    """Assign the next seq, append the (seq, msg) to the replay buffer, return the
    in-place-mutated message.

    MUST be called on the event loop thread. Holds self._seq_lock for the duration
    of counter increment + deque append so that broadcast ordering equals seq order.
    """
    async with self._seq_lock:
        seq = self._next_seq
        self._next_seq += 1
        message["seq"] = seq
        # deque.append is thread-safe but we hold the lock for the whole tuple op
        # so that a concurrent resume iteration sees a consistent snapshot.
        self._replay_buffer.append((seq, message))
    return message
```

The crucial invariants:

1. **No caller may write to `_active_connections` without funneling through `broadcast()`
   or `broadcast_from_thread()`**, which in turn funnel through `_assign_seq_and_append`.
   Verified against `manager.py:41-146` on 2026-04-10 per source-doc §6.5.1. This is
   not currently enforced — a future PR could plausibly violate it. I recommend
   adding an assertion in `broadcast()`:

   ```python
   assert "seq" in message, "broadcast() messages must go through _assign_seq_and_append"
   ```

   That assertion lives behind a DEBUG-level flag so it doesn't fire in production hot
   paths, or runs only in `pytest` via a conftest override.

2. **`broadcast_from_thread` must not assign the seq on the training thread.** It
   schedules a coroutine onto the loop via `run_coroutine_threadsafe`, and the seq is
   assigned inside that coroutine on the loop thread. Two writers from two different
   training threads cannot race because `_assign_seq_and_append` holds `_seq_lock`.

3. **Seq assignment must happen BEFORE the first `send_json()`.** If a client receives
   the message before it is in the replay buffer, a racing reconnect could request a
   resume from `last_seq=N` where N was already sent but not yet buffered. The order
   inside the helper is: increment counter → append to deque → exit lock → then
   iterate over `_active_connections`.

**Lock choice — `_seq_lock` vs `_lock`**: per §6.5.1 of the source doc, I recommend a
separate `_seq_lock: asyncio.Lock` **instead of** reusing `WebSocketManager._lock`. The
latter is held during broadcast fan-out iteration today, so reusing it would couple
sequence-counter increment to the slow-client broadcast timeout discussed in §5.2
below. With a separate `_seq_lock`, a stalled broadcast to one client does not delay
seq assignment for the next event.

**Lock ordering** (to prevent deadlock): `_seq_lock` is always acquired BEFORE `_lock`
if both are needed. In practice only `resume` handling and `close_all()` acquire both;
normal `broadcast()` acquires only `_seq_lock` via `_assign_seq_and_append` then
iterates connections under `_lock`.

### 3.3 Lookup and replay-from-cursor

**Contract**: given a client-supplied `last_seq`, return all entries `(seq, msg)` with
`seq > last_seq`, in ascending seq order.

**Algorithm**:

```python
async def replay_since(self, last_seq: int) -> list[dict]:
    """Return all buffered messages with seq > last_seq.

    Returns an empty list if last_seq is at or past the tail.
    Raises OutOfRangeError if last_seq is older than the oldest buffered entry.
    """
    async with self._seq_lock:
        if not self._replay_buffer:
            return []
        oldest_seq = self._replay_buffer[0][0]
        if last_seq < oldest_seq - 1:
            # client asks for something we've already evicted
            raise ReplayOutOfRange(
                requested=last_seq, oldest_available=oldest_seq
            )
        # Copy under the lock; iterate outside.
        snapshot = list(self._replay_buffer)
    return [msg for (seq, msg) in snapshot if seq > last_seq]
```

Key points:

- **Copy-then-iterate under lock** — same pattern as the updated `close_all()` on main
  (see §11). The copy is O(n) with n ≤ 1024 so cost is negligible; iterating the deque
  without a lock would race with appends.
- **`ReplayOutOfRange` exception** is caught by the `resume` handler in
  `control_stream.py` (or `training_stream.py`, whichever owns the handler — see §6),
  which then sends `{"type": "resume_failed", "data": {"reason": "out_of_range",
  "oldest_available_seq": <N>, "newest_available_seq": <M>}}`. The `oldest_available_seq`
  is advisory; a well-behaved client uses it only for logging.
- **`last_seq == oldest_seq - 1`** is the boundary case: the client's last-seen event
  is exactly the one right before the oldest buffered, meaning no events were lost.
  Returns the full buffer.
- **`last_seq >= newest_seq`** returns `[]` — no events to replay; client is already
  caught up.

### 3.4 Memory accounting

Estimate per-entry cost:

| Component | Bytes |
|---|---|
| Python dict overhead (8 slots min) | ~240 B |
| Envelope keys (`type`, `timestamp`, `seq`, `data`) | ~80 B |
| Interned string values for `type` | ~0 B (interned) |
| Float timestamp | ~24 B |
| Int seq | ~28 B |
| Nested `data` dict (varies by type) | 200-1500 B |
| Tuple `(seq, msg)` overhead | ~56 B |
| **Average entry** | **~600 B** |
| **Worst case entry** (dual-format metrics or full `state`) | **~2 KB** |

Total for 1024 entries:

- **Average**: ~600 KB per `WebSocketManager` instance.
- **Worst case**: ~2 MB per instance (buffer dominated by large state payloads).

Cascor runs one `WebSocketManager` per process. Total memory budget for the replay
buffer is therefore bounded at ~2 MB. This is ~0.03% of the RSS of a typical cascor
process (~6 GB during candidate training). **Not a concern.**

Document this in `manager.py` as a docstring note so that a future contributor who
bumps `ws_replay_buffer_size` understands the scaling. I recommend a soft cap of 8192
and a hard refusal above 16384 in the `Settings` validator — the client's fallback path
(snapshot refetch) is correct and cheap, so there is no strong reason to grow the
buffer beyond tens of seconds of history.

**Observability hook**: expose `WebSocketManager.replay_buffer_bytes` as a computed
property that walks the deque and `sys.getsizeof()`s each entry. Called only by the
Prometheus exporter on a 30 s cadence, not in the broadcast hot path. See §9.

---

## 4. `server_instance_id` UUID

### 4.1 Generation and lifetime

**Generation**: a single `uuid.uuid4()` call at `WebSocketManager.__init__`. Exposed
as `self.server_instance_id: str` (stringified UUID).

```python
def __init__(self, max_connections: int = 50, replay_buffer_size: int = 1024):
    self._active_connections: Set[WebSocket] = set()
    self._max_connections = max_connections
    self._event_loop: Optional[asyncio.AbstractEventLoop] = None
    self._connection_meta: Dict[WebSocket, Dict[str, Any]] = {}
    self._lock = asyncio.Lock()
    self._seq_lock = asyncio.Lock()
    self._next_seq: int = 0
    self._replay_buffer: deque[tuple[int, dict]] = deque(maxlen=replay_buffer_size)
    self.server_instance_id: str = str(uuid.uuid4())
    self.server_start_time: float = time.time()
    logger.info(
        "WebSocketManager initialized "
        f"(max_connections={max_connections}, "
        f"replay_buffer_size={replay_buffer_size}, "
        f"server_instance_id={self.server_instance_id})"
    )
```

**Lifetime**: for the life of the `WebSocketManager` instance, which is the life of
the cascor process. The UUID is **not persisted** across restarts. The entire point is
that it changes on every restart so clients can detect the restart.

**Not persisted** — this is deliberate:

- If cascor writes the UUID to disk and reloads it on restart, clients think they are
  connected to the same instance and will submit `resume` with stale `last_seq`. The
  replay buffer is empty at restart, so the only honest response is `out_of_range`
  anyway, but now we have to pretend the old instance was OK with an empty buffer.
  Simpler to just change the UUID.
- If cascor wants a persistent "cascor deployment identity" for logs/metrics, that
  belongs in a separate field (e.g., `deployment_id` read from env) — NOT in
  `server_instance_id`. Do not conflate the two.

**What triggers a new UUID**:

- Process start (normal case).
- That's the complete list. No runtime regeneration.

**Hot reload note**: if cascor ever supports hot config reload that tears down and
re-instantiates `WebSocketManager`, the UUID changes and clients see a restart event.
This is correct — the replay buffer IS actually gone. Do not add a "preserve UUID
across hot reloads" special case; that hides a real discontinuity.

### 4.2 Restart detection semantics

**The core rule**: clients compare `server_instance_id` by **equality**, never by
ordering. UUIDs have no natural ordering and any ordering logic would be a bug.

On every `connection_established` message, cascor includes:

```json
{
  "type": "connection_established",
  "timestamp": 1712707200.123,
  "seq": 0,
  "data": {
    "connections": 3,
    "server_instance_id": "a1b2c3d4-e5f6-4890-abcd-ef1234567890",
    "server_start_time": 1712707000.0,
    "replay_buffer_capacity": 1024
  }
}
```

- `server_start_time` is **advisory only**. Per §6.5 source-doc it exists for human
  operators reading logs who want to correlate "when did cascor restart" with server
  logs. Clients MUST NOT use it for restart detection — clock skew, NTP rewind, and
  time-travel during DST transitions all corrupt timestamp comparisons. Use
  `server_instance_id` equality.
- `replay_buffer_capacity` is a new field I propose (not in source doc). It tells the
  client how much history is available, so the client can decide whether to even
  attempt a resume vs. going straight to a snapshot refetch after a long disconnect.
  Purely an optimization.
- `seq: 0` — the `connection_established` message consumes seq 0 from each client's
  POV (but see §4.3 below — this is not the same as the server's `_next_seq`).

**Clock skew immunity check**: the only comparison on `server_instance_id` is `==` /
`!=`. No sort, no max, no "newer" logic. Verified mentally against every code path in
§6.5.

### 4.3 Client-side handling (summary — details belong to the canopy-frontend agent)

From the server backend perspective, here's what cascor must send and what it must
accept:

1. **On connect**: cascor sends `connection_established` with `server_instance_id`,
   `server_start_time`, `replay_buffer_capacity`.
2. **Client persists** `server_instance_id` and `last_seq` to localStorage. (Client
   concern; noted for contract completeness.)
3. **On reconnect**: client sends `{"type": "resume", "data": {"last_seq": N,
   "server_instance_id": "<uuid>"}}` as its **first frame** after `accept()`. Cascor
   MUST NOT send anything other than `connection_established` before receiving this
   frame — otherwise the first live event arrives before the client has decided
   whether to replay or snapshot. See §6 for the handler ordering.
4. **Cascor handles resume**:
   - `server_instance_id != self.server_instance_id` → send `{"type": "resume_failed",
     "data": {"reason": "server_restarted", "new_server_instance_id":
     "<uuid>"}}`. Do NOT close the connection. Client then fetches snapshot and sends
     a new `resume` with `last_seq = snapshot_seq` (see §6.5.2 of source doc).
   - `replay_since(last_seq)` raises `ReplayOutOfRange` → send `{"type":
     "resume_failed", "data": {"reason": "out_of_range", "oldest_available_seq": N}}`.
     Same follow-up as above.
   - Otherwise → send each replayed message via `send_personal_message`, in seq
     order, THEN mark the connection as "live" (eligible for broadcast fan-out). See
     §5 for the registration two-phase.
5. **Client omitted `resume`**: if the first non-`resume` frame is a live
   subscription or a command, treat as a fresh connection (no replay).

A subtle edge case the source doc §6.5.2 calls out: "torn snapshot" during the
snapshot→live handoff. Cascor's role is to provide an atomic snapshot endpoint that
returns `(state_payload, snapshot_seq)` under the same `_seq_lock` that guards the
replay buffer. I cover this in §6.3 below.

---

## 5. Broadcaster lifecycle

### 5.1 Connection registration

Today's `connect()` does: acquire `_lock` → check cap → `ws.accept()` → add to set →
log → send `connection_established`. Post-GAP-WS-13, it must do:

**Two-phase registration**:

```
PHASE 1 — accept and auth (existing):
  1. async with self._lock:
     - check cap, reject with 1013 if full
     - await ws.accept()
     - add to a NEW set self._pending_connections (not _active_connections yet)
     - record connection_meta with registered_at timestamp
  2. Outside the lock, send connection_established with server_instance_id, seq=0
     (personal message, not broadcast, so it bypasses the replay buffer).

PHASE 2 — resume or live handoff:
  3. Await the client's first frame with a 5 s timeout:
     - if it's {type: "resume", ...}: handle replay (see §6.1)
     - if it's anything else: treat as fresh connection; drop and re-queue the frame
       to the normal handler; promote to _active_connections
     - if it times out: promote to _active_connections (fresh client; client is
       expected to send resume only if it has a saved last_seq)
  4. async with self._lock:
     - move ws from _pending_connections to _active_connections
  5. From this point onward the client receives broadcast fan-out.
```

**Why two phases**: without the pending set, the normal `broadcast()` loop would fan
messages out to a client that is mid-replay, interleaving live messages with replayed
ones. With the pending set, the client is atomically absent from fan-out until replay
completes.

**Alternative considered — single-phase with a per-connection "seq_cursor"**: instead
of a pending set, each connection carries `seq_cursor: int` (initialized to "max seq
at connect time"). `broadcast()` only sends to a connection if `seq > seq_cursor`.
Replay sets `seq_cursor = last_seq` temporarily. **Rejected** because it couples the
fan-out loop to per-connection state and complicates the lock-ordering discussion.
The pending set is simpler.

**`connection_established` does NOT enter the replay buffer**: it is
connection-specific (contains `connections: 3` which differs per-connection anyway)
and a fresh reconnect cannot meaningfully "replay" an old `connection_established`.
Sent via `send_personal_message`, not `broadcast()`. This bypass is important.

### 5.2 Backpressure handling

The source doc specifies a two-step fix (§7.7, GAP-WS-07):

1. **Quick fix** — wrap each `send_json` in `asyncio.wait_for(..., timeout=0.5)`.
   On timeout: close the client with code 1008 and remove from `_active_connections`.
2. **Full fix** — per-client bounded send queue with backpressure policy.

I endorse both, with the following cascor-server-specific details:

**Quick fix, implementation sketch** (drop-in replacement for `_send_json`):

```python
async def _send_json(self, websocket: WebSocket, message: dict) -> bool:
    """Send JSON message to a single WebSocket. Returns False on failure.

    Wraps the send in a 0.5 s timeout so a slow client cannot stall the
    broadcast loop. On timeout or error, returns False so the caller
    prunes the connection.
    """
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

**Timeout rationale**: 0.5 s is the smallest value that is safely above the WiFi p99
RTT (~80 ms over residential connections) + TCP retransmit (~200 ms) + `json.dumps`
work (~10 ms) + uvicorn's frame-write path (~5 ms). Below 0.5 s we would prune
healthy clients under normal packet loss. Above 0.5 s the broadcast loop stalls enough
to affect other clients. Tunable via `Settings.ws_send_timeout_seconds`.

**Full fix — per-client send queue**:

```python
class _ClientState:
    ws: WebSocket
    send_queue: asyncio.Queue[dict]  # maxsize from Settings
    pump_task: asyncio.Task
    slow_strikes: int  # counter for slow-client kick policy

# In broadcast():
for client in self._clients:
    try:
        client.send_queue.put_nowait(message)
    except asyncio.QueueFull:
        # Policy: close for state events, drop-oldest for progress events
        if message["type"] in {"state", "cascade_add", "event", "command_response"}:
            await client.ws.close(code=1008, reason="Slow client")
            self._active_connections.discard(client.ws)
        else:
            # Drop oldest for coalesceable progress; drop at most once per second
            with contextlib.suppress(asyncio.QueueEmpty):
                client.send_queue.get_nowait()
            client.send_queue.put_nowait(message)
```

A dedicated `pump_task` per client reads from its queue and `await ws.send_json(msg)`
with the 0.5 s per-send timeout. On persistent failure (3 strikes) the pump closes
the ws with 1008 and removes the client.

**Queue size**: the source doc recommends `maxsize=128` with a rationale of "~6 seconds
of stall at peak event rate 20/s". I endorse 128 as the default for `state`, `metrics`,
and `event` streams. For `candidate_progress` — which can burst at 50 Hz per the §5.4
budget table — I recommend a **separate per-type sub-queue with `maxsize=32`** and
drop-oldest policy. The rationale is in RISK-11: state-bearing events must not be
silently dropped, but coalesceable progress events can be.

**Policy matrix** (my recommended default, overridable via
`Settings.ws_backpressure_policy`):

| Event type | Queue size | Overflow policy | Rationale |
|---|---|---|---|
| `state` | 128 | close(1008) | State is terminal-state-sensitive |
| `metrics` | 128 | close(1008) | Drops cause chart gaps, not chart errors, but still observable |
| `cascade_add` | 128 | close(1008) | Each event represents a growth step — missing one corrupts topology |
| `candidate_progress` | 32 | drop_oldest | Coalesceable; next progress subsumes previous |
| `event` (training_complete etc.) | 128 | close(1008) | Terminal-state-sensitive |
| `command_response` | 64 | close(1008) | Client is specifically waiting for this |
| `connection_established` | n/a | n/a | Sent once via `send_personal_message` |
| `pong` | 16 | drop_oldest | Heartbeat; client can re-ping |

**Replay interaction**: slow-client kick happens only on the **live** fan-out path,
not during replay. Replay is a separate phase (§5.1) where the manager awaits each
`send_personal_message` serially; the same 0.5 s per-send timeout applies, and a
slow-replay-target is closed with 1008 before promotion to `_active_connections`.

**RISK-04 mitigation**: the source doc raises RISK-04 to Medium likelihood after
observing that a hung devtools tab can block broadcasts. The quick fix alone resolves
this because the timeout path prunes the hung client within 0.5 s.

### 5.3 Disconnect cleanup

Today's `disconnect()`:

```python
async def disconnect(self, websocket: WebSocket) -> None:
    async with self._lock:
        self._active_connections.discard(websocket)
        self._connection_meta.pop(websocket, None)
```

Post-backpressure, this needs to:

1. Cancel the pump task.
2. Drain the send queue (messages dropped — they are already stale).
3. Remove from both `_active_connections` AND `_pending_connections` (in case the
   disconnect fires during the two-phase registration).
4. Close the WebSocket cleanly if still open.
5. Decrement the per-IP counter (see M-SEC-04 in the security agent's lane).
6. Remove the per-client `_ClientState` entry.

**Task cancellation ordering**: cancel the pump task BEFORE removing from the set. If
we remove first, a racing `broadcast()` cannot enqueue into the soon-to-be-cancelled
pump, but a send that was already in flight could still succeed. Not a correctness
bug but awkward to reason about. Cancel first, cleanup second.

**Idempotent**: `disconnect()` must be safe to call multiple times on the same `ws`.
The current `discard()` is already idempotent; the new cleanup steps all use `pop(...,
None)` or equivalent.

**Exception path**: `disconnect()` is called from multiple paths — the `training_ws`
route handler's `finally` block, the slow-client kick, `close_all()`, and the resume
handler on `out_of_range`. All paths must route through this single method so the
cleanup set is consistent.

### 5.4 Fanout efficiency

Current `broadcast()`:

```python
async def broadcast(self, message: dict) -> None:
    if not self._active_connections:
        return
    disconnected = []
    for ws in self._active_connections.copy():
        if not await self._send_json(ws, message):
            disconnected.append(ws)
    for ws in disconnected:
        await self.disconnect(ws)
```

Observations:

- **Serial await**: each client's `send_json` awaits before the next. At N=50 connected
  clients × 10 ms per send = 500 ms serial latency for the last client. Acceptable at
  current scale but bounds scalability.
- **Post-GAP-WS-13** this becomes: `_assign_seq_and_append(message)` → serial
  fan-out.

**Recommended parallel fan-out** (post-Phase E):

```python
async def broadcast(self, message: dict) -> None:
    tagged = await self._assign_seq_and_append(message)
    if not self._active_connections:
        return
    # Parallel fan-out with per-send timeout.
    clients = list(self._active_connections)
    results = await asyncio.gather(
        *[self._send_json(ws, tagged) for ws in clients],
        return_exceptions=True,
    )
    for ws, ok in zip(clients, results):
        if ok is not True:  # False or exception
            await self.disconnect(ws)
```

**Concerns with parallel fan-out**:

- Per-client ordering: `asyncio.gather` does not reorder sends to the same client, so
  seq monotonicity per-client is preserved. Verified: each `_send_json` is its own
  coroutine on its own client.
- Memory: 50 concurrent sends hold 50 × 600 B = 30 KB of duplicated envelope
  references. Negligible.
- Lock contention: no additional lock acquisition vs serial; `_assign_seq_and_append`
  is held once.

**Skip the full parallelism for MVP**. Phase B-server ships with the serial fan-out
+ 0.5 s per-send timeout (quick fix). Parallel fan-out is a Phase E optimization once
the pump-task design lands, because the pump-task model sidesteps the question
entirely — each client has its own coroutine, and broadcast just enqueues.

---

## 6. Endpoint contracts

### 6.1 `/ws/training`

**File**: `juniper-cascor/src/api/websocket/training_stream.py`

**Inbound messages** (client → server):

| Type | Meaning | Handler response |
|---|---|---|
| `ping` | Application-layer heartbeat | Reply with `pong` (existing `messages.py` builder) |
| `resume` (NEW) | Lossless reconnect request | See §6.2 below |
| (anything else) | Protocol violation | Respond with `{"type": "error", "data": {"error": "unexpected message"}}`; do NOT close |

**Outbound** (via manager broadcast or personal send):

- `connection_established` (personal, on connect)
- `initial_status` (personal, on connect after resume decision)
- `state`, `metrics`, `cascade_add`, `candidate_progress`, `event`, `topology`
  (broadcast, assigned seq)
- `resume_failed` (personal, in response to `resume`)
- `resume_ok` (NEW, personal, in response to successful `resume` — advisory, tells
  client how many events will be replayed)
- `pong` (personal, in response to `ping`)

**Resume handler wiring** — this is the new code. Placed in the training_stream
handler because the `/ws/control` endpoint is RPC and replay semantics don't apply
there:

```python
async def training_stream_handler(ws: WebSocket, manager: WebSocketManager, ...):
    if not await ws_authenticate(ws):
        return
    if not await manager.connect_pending(ws):  # new method — adds to _pending
        return
    try:
        # Wait up to 5 s for an initial resume frame.
        try:
            first_frame = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        except asyncio.TimeoutError:
            first_frame = None

        if first_frame and first_frame.get("type") == "resume":
            data = first_frame.get("data", {})
            client_instance_id = data.get("server_instance_id")
            last_seq = data.get("last_seq")
            if client_instance_id != manager.server_instance_id:
                await manager.send_personal_message(ws, {
                    "type": "resume_failed",
                    "timestamp": time.time(),
                    "data": {
                        "reason": "server_restarted",
                        "new_server_instance_id": manager.server_instance_id,
                    },
                })
            else:
                try:
                    replay = await manager.replay_since(last_seq)
                except ReplayOutOfRange as exc:
                    await manager.send_personal_message(ws, {
                        "type": "resume_failed",
                        "timestamp": time.time(),
                        "data": {
                            "reason": "out_of_range",
                            "oldest_available_seq": exc.oldest_available,
                        },
                    })
                else:
                    await manager.send_personal_message(ws, {
                        "type": "resume_ok",
                        "timestamp": time.time(),
                        "data": {"replayed_count": len(replay)},
                    })
                    for msg in replay:
                        await manager.send_personal_message(ws, msg)
        elif first_frame is not None:
            # Non-resume first frame — route through the normal inbound handler
            # as if it had arrived in the main loop.
            await handle_training_inbound(ws, first_frame, ...)

        # Promote from pending to active (main broadcast loop now feeds this ws).
        await manager.promote_to_active(ws)

        # Send initial_status snapshot personal message.
        initial_status = build_initial_status(lifecycle)
        await manager.send_personal_message(ws, initial_status)

        # Main inbound loop.
        while True:
            msg = await ws.receive_json()
            await handle_training_inbound(ws, msg, ...)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
```

The `handle_training_inbound` helper dispatches on `msg["type"]` for `ping` (reply
`pong`) and any future inbound types. It explicitly **rejects** unknown types with an
error reply rather than silently ignoring — this matches the recommendation in
GAP-WS-22 for `/ws/control` and extends the same policy to `/ws/training`.

**Initial_status race**: note that `initial_status` is sent AFTER promotion to active,
which means a live `state` event could theoretically arrive before `initial_status`
due to broadcast interleaving. Clients must treat `initial_status` as a snapshot that
can be overwritten by any subsequent `state` message with equal-or-greater `seq`.
Document this in the client contract.

### 6.2 Resume contract details

**Request**:

```json
{
  "type": "resume",
  "data": {
    "last_seq": 12345,
    "server_instance_id": "a1b2c3d4-e5f6-4890-abcd-ef1234567890"
  }
}
```

**Response paths**:

1. **Resume success**:
   - `resume_ok` personal message with `replayed_count: N`
   - N personal messages, each a replayed envelope with its original `seq`
   - Then promotion to `_active_connections`; the next broadcast message is live
2. **Server restarted** (`server_instance_id` mismatch):
   - `resume_failed` with reason `server_restarted`
   - Promotion to `_active_connections` (client continues on live stream after
     its snapshot fetch)
3. **Out of range** (`last_seq` older than oldest buffered):
   - `resume_failed` with reason `out_of_range` and `oldest_available_seq` advisory
   - Promotion to `_active_connections`
4. **Missing `data.last_seq`** or missing `data.server_instance_id`:
   - `resume_failed` with reason `malformed_resume`
   - Promotion to `_active_connections` (treat as a fresh client)
5. **Frame arrived but not JSON**:
   - Close with 1003 (same as control stream protocol errors — GAP-WS-22)

**Idempotency**: the client should treat replay as idempotent. Cascor does not
de-duplicate across concurrent reconnects from the same client — see §8.3 for that
failure mode.

**Atomic snapshot read for §6.5.2**: the source doc §6.5.2 requires that the REST
snapshot endpoint read `(snapshot_payload, snapshot_seq)` atomically under the same
lock that serializes ring-buffer appends. Translation for cascor: the
`/api/v1/training/status` handler (which clients use as the snapshot) must include
`snapshot_seq` in its response, computed under `manager._seq_lock`:

```python
@router.get("/api/v1/training/status")
async def get_status(manager: WebSocketManager = Depends(...)):
    payload = lifecycle.get_status()
    async with manager._seq_lock:
        snapshot_seq = manager._next_seq - 1  # last-assigned seq
    payload["snapshot_seq"] = snapshot_seq
    payload["server_instance_id"] = manager.server_instance_id
    return payload
```

The invariant is: any message with `seq > snapshot_seq` was emitted strictly after the
snapshot was captured, so a client that resumes from `snapshot_seq` is guaranteed to
see exactly the events emitted since the snapshot (modulo replay buffer capacity).

**Torn-read risk if this lock is omitted**: a metrics event with seq=N could be
broadcast to all live clients before `_next_seq` is incremented past N — meaning the
REST snapshot captures state that reflects event N's data but returns
`snapshot_seq = N - 1`. The client then resumes from N-1, cascor replays event N, and
the client sees N applied twice. The `snapshot_seq` being assigned under the same lock
as the seq counter increment prevents this.

**Alternative**: assign seq BEFORE broadcast, so `_next_seq - 1` always reflects the
last-committed seq. This is what §3.2 mandates. The status endpoint relies on that
ordering; document it in both places.

### 6.3 `/ws/control`

**File**: `juniper-cascor/src/api/websocket/control_stream.py`

**Inbound**:

```json
{
  "command": "set_params",
  "params": {"learning_rate": 0.005}
}
```

**No `type` field** — per §3.0 the client→server envelope is asymmetric. Source doc
GAP-WS-20 tracks normalization as P3 deferred. Cascor server must accept the current
shape indefinitely; a future normalized shape would be accepted in parallel.

**Allowed commands**: `_VALID_COMMANDS = {"start", "stop", "pause", "resume", "reset",
"set_params"}` per `control_stream.py:22`.

**Command handling ordering change for Phase B-server**:

Today `/ws/control` is RPC-only (request → response, no broadcast side effects). With
sequence numbers added, command responses also need a `seq`:

```json
{
  "type": "command_response",
  "timestamp": 1712707300.0,
  "seq": 12346,
  "data": {"command": "set_params", "status": "success", "result": {...}}
}
```

**But `command_response` is personal, not broadcast**. Should it enter the replay
buffer? Two options:

1. **Yes, enters the replay buffer.** Every outbound message has a seq so clients
   have a single monotonic ordering to reason about. Replay of a command_response on
   reconnect is weird (the command isn't re-issued) but it's benign — the client
   ignores command_responses for commands it doesn't remember sending.
2. **No, command_response is personal and does not consume a seq.** The replay
   buffer only contains broadcast events. Command responses have no `seq` field (or
   a `seq: null`).

**I recommend Option 2**. Rationale:

- Replaying a command_response for a command the client didn't issue is semantically
  confusing.
- A command is connection-scoped (the `/ws/control` connection that issued it). If
  the client reconnects, the pending command should be retried from the client side
  via the GAP-WS-32 per-command correlation ID mechanism, not resurrected from
  cascor's replay buffer.
- `/ws/control` is a separate connection from `/ws/training`. The training stream's
  replay buffer has no relationship to the control stream's command responses.

**Implication**: the two WebSocket endpoints have separate seq namespaces. To keep
this simple, I recommend:

- `/ws/training` broadcast envelope: `seq` field present, drawn from
  `manager._next_seq`.
- `/ws/control` `command_response` envelope: no `seq` field. Client matches responses
  to commands by `command` value (today) or by `command_id` UUID (after GAP-WS-32
  lands).

**Per-command correlation ID** (GAP-WS-32 hook): cascor accepts and echoes a
client-supplied `command_id` when present. The new inbound shape would be:

```json
{
  "command": "set_params",
  "command_id": "f1e2d3c4-...",
  "params": {"learning_rate": 0.005}
}
```

And the response:

```json
{
  "type": "command_response",
  "timestamp": ...,
  "data": {
    "command": "set_params",
    "command_id": "f1e2d3c4-...",
    "status": "success",
    "result": {...}
  }
}
```

Cascor MUST NOT validate the command_id format (any string is accepted). Its only
responsibility is to echo it back in the matching response. If the field is absent,
the response omits it.

**Protocol error responses (GAP-WS-22)**: normalized per source doc §3.2.4 table:

| Failure | Response | Close | New? |
|---|---|---|---|
| Non-JSON payload | (close) | 1003 | NEW — implement with try/except on `receive_json` |
| Missing `command` field | `command_response` with `status: "error", error: "missing command field"` | no close | NEW |
| Unknown command | `command_response` with `status: "error", error: "Unknown command: <name>"` | no close | exists (`control_stream.py:55-59`) |
| Handler exception | `command_response` with `status: "error", error: "<msg>"`; log traceback server-side | no close | exists (partial — add traceback log) |
| Frame > 64 KB | (close) | 1009 | exists (framework-level) |

These ship with the Phase G integration tests (§9.8 source doc). I include them here
because the cascor-server side of the contract is mine to define.

---

## 7. Implementation steps (Phase A-server focus)

The source doc's Phase A is SDK-side (GAP-WS-01 in `juniper-cascor-client`). Phase B
is the big browser-bridge work and includes cascor-side sequence numbers and replay
buffer (see §9.3 of source doc). I propose carving out a smaller **Phase A-server**
that lands the cascor-side prerequisites BEFORE the canopy-side Phase B work starts,
so that canopy can iterate against a server that already emits `seq` and handles
`resume`.

### 7.1 Phase A-server: cascor prerequisites

**Scope**: GAP-WS-13 (sequence numbers + replay buffer) + GAP-WS-21 (state throttle
coalescer) + GAP-WS-22 (protocol error responses) + GAP-WS-29
(`broadcast_from_thread` exception handling) + the quick-fix portion of GAP-WS-07
(per-send timeout).

**Order of commits** (each commit green independently):

1. **Commit 1 — `messages.py`**: add optional `seq` parameter to every builder. At
   this point seq is `None` on every message; no consumers depend on it yet.
   Tests: existing message builder tests still pass; new test asserts `seq=None`
   serializes cleanly.

2. **Commit 2 — `WebSocketManager` plumbing**: add `server_instance_id`,
   `server_start_time`, `_next_seq`, `_seq_lock`, `_replay_buffer`. Add
   `_assign_seq_and_append()` helper. `broadcast()` and `broadcast_from_thread()` now
   route through it. `connect()` includes `server_instance_id` and
   `replay_buffer_capacity` in `connection_established`.
   Tests: unit tests on the manager verify seq monotonicity, buffer bounded-ness,
   and connection_established envelope contents. No training_stream changes yet.

3. **Commit 3 — `_send_json` 0.5 s timeout (quick-fix backpressure)**: wraps the
   send in `asyncio.wait_for`. Standalone — resolves RISK-04's immediate severity
   without waiting for the full pump-task model.
   Tests: unit test with a `asyncio.Future`-backed fake ws that never resolves;
   asserts `_send_json` returns False within ~0.5 s and doesn't raise.

4. **Commit 4 — `replay_since()` + `ReplayOutOfRange` exception**: pure read-side
   method on the manager. No resume handler yet — just the primitive.
   Tests: unit tests for empty buffer, partial replay, full replay, out-of-range,
   `last_seq == newest_seq` (returns empty), `last_seq == oldest_seq - 1`
   (returns full buffer).

5. **Commit 5 — `training_stream.py` resume handler + two-phase registration**:
   `_pending_connections` set, `connect_pending()`, `promote_to_active()`,
   the 5-second resume-frame timeout, the full `resume`/`resume_failed`/`resume_ok`
   flow.
   Tests: integration test via FastAPI `TestClient.websocket_connect()` for each
   resume outcome: happy path with 3 replayed events, server_restarted mismatch,
   out_of_range, missing fields, non-resume first frame.

6. **Commit 6 — `/api/v1/training/status` adds `snapshot_seq`**: one-line addition
   to the existing endpoint, reading `_next_seq` under `_seq_lock`.
   Tests: unit test asserts `snapshot_seq` is present and monotonically
   increasing across successive calls interleaved with broadcasts.

7. **Commit 7 — 1 Hz state throttle → debounced coalescer (GAP-WS-21)**: replace
   the drop filter in `lifecycle/manager.py:133-136` with a coalescer that:
   - Buffers the latest pending state.
   - Flushes at most once per second.
   - Bypasses the throttle entirely for terminal transitions (`Failed`, `Stopped`,
     `Completed`).
   - Schedules the flush via an asyncio call_later or an equivalent thread-safe
     bridge.
   Tests: unit test that fires `Started → Failed → Stopped` within 200 ms; asserts
   all three transitions are observed by a fake WebSocketManager.

8. **Commit 8 — `broadcast_from_thread` exception handling (GAP-WS-29)**: attach a
   done callback that logs errors; wrap in try/finally that closes the coroutine on
   any failure path. Three-line patch.
   Tests: unit test that triggers an exception inside the scheduled coroutine;
   asserts the log line fires and no coroutine warning appears at exit.

9. **Commit 9 — `/ws/control` protocol error responses (GAP-WS-22)**: the
   table in §6.3 above. Mostly unit-test coverage; code changes are small.

10. **Commit 10 — docs and CHANGELOG**: update cascor README / AGENTS.md /
    `messages.py` docstring with the new `seq` field, document the
    `ws_replay_buffer_size` setting, document the `server_instance_id` semantics.
    No code.

**Effort estimate**: ~2 engineering days for all 10 commits, tests included. The
source doc's Phase B estimate of 4 days includes both the cascor-side and canopy-side
work; I think the cascor-side is about 2 of those days. Carving Phase A-server off
lets canopy Phase B begin with a stable server contract.

### 7.2 Phase E-server: full backpressure (pump task)

**Deferred**: the per-client pump task + queue model is a bigger change. Not required
for correctness once the 0.5 s `_send_json` timeout is in place, so Phase A-server can
ship with the quick fix only. Phase E-server lands later with:

- `_ClientState` dataclass.
- Per-client `asyncio.Queue(maxsize=...)`.
- Pump task per client, cancelled on disconnect.
- Policy matrix from §5.2 wired via `Settings.ws_backpressure_policy`.

**Effort**: ~1 engineering day.

### 7.3 What is explicitly NOT in Phase A-server

- The `/ws/control` `command_id` correlation field (GAP-WS-32). Deferred with Phase D
  of source doc §9.5; cascor adds the echo then.
- Topology chunking (GAP-WS-18 / RISK-16). Deferred to Phase E/H of source doc; cascor
  adds a size guard and a REST fallback.
- `permessage-deflate` config (GAP-WS-17). Small standalone cascor PR; not blocking.
- `close_all()` lock fix (GAP-WS-19). Already fixed on main per §11.

---

## 8. Failure modes and recovery

This section enumerates every server-side failure mode I can think of and describes
the cascor-server's behavior. Some are already covered above; I repeat them here with
explicit mitigation.

### 8.1 Server restart mid-training

**Scenario**: cascor process dies or is restarted while training is active with N
connected canopy clients.

**What happens**:
1. FastAPI's lifespan shutdown fires. `close_all()` runs (already-fixed version on
   main, per §11). All client connections receive a clean close with code 1001.
2. Replay buffer is discarded (in-memory only).
3. `_next_seq` resets to 0 on restart.
4. `server_instance_id` is a fresh UUID4.
5. Clients reconnect, send `resume` with their saved `last_seq` and the OLD
   `server_instance_id`.
6. Cascor compares: `client_instance_id != self.server_instance_id` → `resume_failed
   reason=server_restarted`.
7. Clients fetch REST snapshot, re-issue `resume` with `last_seq = snapshot_seq`
   against the NEW instance. Snapshot_seq is near 0 (no events buffered yet);
   replay returns empty; client continues on live stream.

**Correctness check**: no events are applied twice; no events are lost IF the
client's snapshot refetch succeeds. If it fails, the client displays a stale-data
badge (source doc §6.5.2 retry policy).

**Cascor responsibility**: ensure `close_all()` runs during shutdown so clients get a
clean 1001 and can start backoff-reconnect immediately. Already implemented on main.

### 8.2 Client gone but broadcast queue full

**Scenario**: a client's TCP half-open state means sends time out. Before the 0.5 s
timeout, the pump queue fills up during a candidate-progress burst.

**What happens (post-Phase E-server)**:
1. Queue reaches `maxsize`. Policy from §5.2 applies:
   - For `candidate_progress` (drop_oldest): oldest enqueued event is dropped; new
     event is enqueued. User sees a gap in the progress update stream but no
     correctness violation (correlation values are monotonic approximations).
   - For `state` (close): the slow client is closed with code 1008 and pruned.
2. The slow-client's broadcasts no longer back up in cascor's memory.
3. Other clients continue receiving broadcasts uninterrupted.

**Pre-Phase E-server (quick fix only)**: each send has a 0.5 s timeout. A broadcast
that encounters a slow client waits up to 0.5 s for that client, then prunes it. Fan-out
for other clients is serially behind, so worst-case tail latency at 50 clients is
~25 s — unacceptable for production, acceptable as an interim while Phase E is in
flight.

**Observability**: metric `cascor_ws_broadcast_timeout_total{type}` increments per
prune. Alerts fire if rate > 1/s sustained.

### 8.3 Concurrent reconnects from the same client

**Scenario**: a client's initial reconnect succeeds but its backoff logic races with
itself and opens a second connection before the first is fully established. Both send
`resume` with the same `last_seq`.

**What happens**: cascor treats both as independent connections. Each gets its own
replay. Each is promoted to `_active_connections`. The client now receives every
broadcast event twice, once per socket.

**Mitigation**: client-side responsibility to avoid this — the reconnect logic should
close any existing socket before opening a new one. Not cascor's problem. However,
cascor can add a best-effort "same-IP same-UA quick dedupe": on `connect()`, check if
an existing active connection shares the same `client_ip` and `User-Agent` AND was
connected less than 5 seconds ago; if so, close the newer one with 1008
"duplicate_connection".

**I recommend NOT implementing the same-IP dedupe in Phase A-server.** The heuristic
is unreliable (multiple dashboards on one workstation is legitimate), the false-positive
cost is a user-visible disconnect, and the correct fix lives in the client. Document
in the client contract that "a well-behaved client closes any existing socket before
reconnecting."

### 8.4 Replay buffer overflow during a live reconnect

**Scenario**: a client requests `resume` with `last_seq = N`. While cascor is iterating
the deque snapshot to build the replay list, `_next_seq` advances past N + 1024,
evicting the entries that were about to be replayed.

**What happens (with the §3.3 algorithm)**:
1. `replay_since(N)` copies the deque under `_seq_lock`.
2. The snapshot is a list of 1024 tuples that were present at lock-acquisition time.
3. Subsequent `broadcast()` calls append to the deque after the lock is released,
   which may evict oldest entries — but the snapshot list is independent and
   unaffected.
4. The replay iterates the snapshot and sends each message. The client's `seq_cursor`
   advances to the max seq in the replay.
5. When promotion happens, the client starts receiving live events. The first live
   event has a seq that may be substantially larger than the max-replayed seq (gap
   of up to 1024 events), and the client may never see those middle events.

**This is a correctness bug.** The client thinks it resumed cleanly but missed
intermediate events.

**Mitigation**: promote the client to `_active_connections` BEFORE finalizing the
replay, then de-duplicate on the client side by tracking the max-seen seq. Concretely:

1. Copy the deque under `_seq_lock` to get `snapshot = list(deque)`.
2. `newest_replayed_seq = snapshot[-1][0]` (or `last_seq` if empty).
3. **Promote to `_active_connections` under `_seq_lock`** (same critical section).
   Broadcasts after this point will fan out to the client AND are in the replay
   snapshot (at their original seq).
4. Release the lock. Send the replay messages.
5. During replay, live broadcasts are also hitting the client — the client sees each
   live event twice (once in replay, once live). It de-dupes by `seq`.

**Key trick**: inside the lock, we `append_to_active_connections_atomic(ws)`. Outside
the lock we send the replay. Any message broadcast after the promotion hits both the
deque (still going) AND `_active_connections` (ws is now in it). Since the client
de-dupes by seq, no correctness issue.

**Client contract**: clients MUST de-duplicate replayed events by seq. This is
already §6.5.2 of the source doc ("idempotent replay contract"). I am reinforcing that
it is load-bearing for this specific race.

**Alternative**: hold `_seq_lock` for the entire replay send. Rejected — blocks
broadcasts for seconds if replay is large or network is slow.

### 8.5 Cascor event loop hang during broadcast

**Scenario**: a broadcast triggers some path that deadlocks (e.g., a `threading.Lock`
acquired from inside a coroutine — a legitimate concern per the source doc §2.2
lock-type-contract note).

**What happens**: the event loop is stalled. All WebSocket endpoints stop responding.
New connects fail (the `accept()` handler is also on the loop). Health checks time out.

**Mitigation**:
- The source doc's lock-type-contract note at §2.2 is the primary defense. Document
  it at the lock definition sites.
- Add a watchdog task that runs on the loop and logs a warning if its own sleep
  takes longer than 5 seconds: `asyncio.sleep(1.0)` in a loop, `await_time -
  expected_time > 5.0` triggers the warning. Not a production-hardening tool but
  helps detect regressions early.
- Add a lint rule (if possible) that flags any `threading.Lock` acquisition inside
  an `async def`. Flake8 doesn't have this built-in; a custom AST check in
  `juniper-cascor/.pre-commit` would work.

### 8.6 Resume request with non-UUID `server_instance_id`

**Scenario**: a malicious or buggy client sends `{"type": "resume", "data":
{"last_seq": 0, "server_instance_id": "potato"}}`.

**Cascor behavior**: string equality comparison with `self.server_instance_id` fails
→ `resume_failed reason=server_restarted`. No correctness issue; cascor does not
parse or validate the UUID format.

**Should cascor validate?** No. The source doc doesn't require UUID format validation,
and validating would leak information (a "well-formed but wrong" vs "malformed"
distinction). Treat all mismatches identically.

---

## 9. Observability and metrics

The source doc §5.6 talks about end-to-end latency histograms as a canopy-side
instrumentation concern. This section covers cascor-server-side metrics only.

### 9.1 Prometheus metrics (new)

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `cascor_ws_connections_active` | Gauge | endpoint | Active connection count per endpoint |
| `cascor_ws_connections_pending` | Gauge | endpoint | Connections in the pending (pre-promotion) state |
| `cascor_ws_connections_total` | Counter | endpoint, outcome | Cumulative connect attempts; outcome=`{accepted, rejected_cap, rejected_auth}` |
| `cascor_ws_disconnects_total` | Counter | endpoint, reason | reason=`{clean, slow_client, auth_failure, server_shutdown, unknown}` |
| `cascor_ws_broadcasts_total` | Counter | type | Cumulative broadcasts, by envelope type |
| `cascor_ws_broadcast_send_seconds` | Histogram | type | Per-send latency; buckets `{0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0}` |
| `cascor_ws_broadcast_timeout_total` | Counter | type | Per-send timeouts (slow clients pruned) |
| `cascor_ws_replay_buffer_occupancy` | Gauge | — | Current entry count (0-1024) |
| `cascor_ws_replay_buffer_bytes` | Gauge | — | Approximate byte size (sampled, see §3.4) |
| `cascor_ws_seq_current` | Gauge | — | Current `_next_seq - 1`, useful for monitoring event rate |
| `cascor_ws_resume_requests_total` | Counter | outcome | outcome=`{success, server_restarted, out_of_range, malformed, no_resume_timeout}` |
| `cascor_ws_resume_replayed_events` | Histogram | — | Events replayed per successful resume; buckets `{0, 1, 5, 25, 100, 500, 1024}` |
| `cascor_ws_state_throttle_dropped_total` | Counter | — | State events dropped by the 1 Hz throttle (pre-Phase A-server commit 7; drops to 0 after coalescer lands) |
| `cascor_ws_state_throttle_coalesced_total` | Counter | — | State events coalesced into a later flush (post-coalescer) |
| `cascor_ws_command_responses_total` | Counter | command, status | Per-command success/error counter |
| `cascor_ws_command_handler_seconds` | Histogram | command | Per-command handler latency |

All metrics live behind the existing prometheus-client or OpenTelemetry exporter that
cascor already uses. If no exporter exists, add a minimal `/metrics` endpoint.

### 9.2 Structured logs (new)

Log at `INFO` level:

- connection_established: `{event: ws_connect, endpoint, client_ip, connection_count}`
- disconnect: `{event: ws_disconnect, endpoint, client_ip, reason, duration_s}`
- resume success: `{event: ws_resume_ok, client_ip, last_seq, replayed_count, oldest_buffered_seq, newest_buffered_seq}`
- resume failure: `{event: ws_resume_failed, client_ip, reason, last_seq}`

Log at `WARNING`:

- slow_client prune: `{event: ws_slow_client, client_ip, timeout_s}`
- replay buffer near-capacity (>90% full for >30 s): once per occurrence, with dedupe
- broadcast exception: full traceback

Log at `DEBUG`:

- every send (rate-limited by existing logging config; do NOT enable in production)
- seq assignments (rate-limited)

### 9.3 Internal assertions (dev mode)

Behind a `CASCOR_DEV_ASSERTIONS=1` env var:

- Every envelope passed to `broadcast()` has `seq` set (asserts that
  `_assign_seq_and_append` was called).
- Every envelope in `_replay_buffer` has monotonically increasing seq.
- `_next_seq > len(_replay_buffer)` always (cannot have more buffered than total
  emitted).
- `_pending_connections.isdisjoint(_active_connections)` always.

These are `assert` statements inside the manager methods, gated by env var so they
don't fire in production hot paths.

### 9.4 Alerts (recommended SLOs — not cascor's to configure)

Proposed for the operator running cascor:

- `rate(cascor_ws_broadcast_timeout_total[1m]) > 0.1` → "slow clients detected"
- `cascor_ws_replay_buffer_occupancy > 900 for 30s` → "replay buffer near cap; event
  rate may exceed buffer scale"
- `rate(cascor_ws_resume_requests_total{outcome="server_restarted"}[5m]) > 0` → "cascor
  restart; check for crash loop"
- `cascor_ws_seq_current` rate-of-change dropping to 0 during active training →
  "broadcaster not emitting; check for event loop hang"

---

## 10. Verification / acceptance criteria

For Phase A-server (§7.1) to be considered done:

### 10.1 Unit tests (cascor)

Pass under `pytest juniper-cascor/src/tests/unit/api/`:

1. **WebSocketManager seq monotonicity**: 100 concurrent `broadcast()` calls from a
   single loop; assert all broadcasted messages have strictly increasing seq and
   that `_replay_buffer` contains exactly 100 entries in order.
2. **WebSocketManager seq monotonicity under `broadcast_from_thread`**: 10 threads
   × 100 calls each; assert all 1000 messages in the deque have strictly increasing
   seq.
3. **Replay buffer eviction**: broadcast 2000 messages; assert `len(_replay_buffer)
   == 1024` and the oldest entry has seq = 976.
4. **Replay from cursor (happy path)**: broadcast 50 messages, call `replay_since(10)`,
   assert return length 39 with seq 11..49.
5. **Replay from cursor (out of range)**: broadcast 2000 messages (causes eviction),
   call `replay_since(10)`, assert `ReplayOutOfRange` raised with
   `oldest_available >= 976`.
6. **Replay from cursor (empty)**: broadcast 50, call `replay_since(50)`, assert
   return `[]`.
7. **server_instance_id stability**: call manager methods, assert
   `server_instance_id` does not change across calls.
8. **server_instance_id uniqueness**: create two managers, assert their
   `server_instance_id` differ.
9. **connection_established contents**: connect a fake ws, assert the first message
   contains `server_instance_id`, `server_start_time`, `replay_buffer_capacity`,
   `connections`.
10. **Slow client 0.5 s timeout**: fake ws whose `send_json` never resolves; call
    `_send_json`, assert returns False within 0.6 s.
11. **State throttle coalescer (post-commit 7)**: fire `Started → Running → Failed`
    within 200 ms on a fake lifecycle; assert all 3 states are observed by the
    broadcaster, AND the throttle deferred the middle `Running` until ~1 s later (or
    dropped it if terminal `Failed` bypassed).
12. **Protocol error: malformed JSON on /ws/control**: send non-JSON, assert close
    code 1003.
13. **Protocol error: missing command field**: send `{"params": {}}`, assert
    `command_response` with `status: "error"`.
14. **Protocol error: unknown command**: send `{"command": "nope"}`, assert
    `command_response` with `status: "error", error: "Unknown command: nope"`.
15. **broadcast_from_thread exception handling**: trigger a raise inside the scheduled
    coroutine; assert a log line fires and no "coroutine was never awaited" warning
    appears.

### 10.2 Integration tests (cascor, via TestClient)

Pass under `pytest juniper-cascor/src/tests/integration/`:

16. **Resume happy path**: connect to `/ws/training`, broadcast 3 events, disconnect,
    reconnect, send `resume` with `last_seq = 0`, assert `resume_ok replayed_count=3`
    followed by 3 replayed messages in seq order, followed by live events.
17. **Resume after server_instance_id mismatch**: connect, disconnect, reinstantiate
    manager (simulates restart), reconnect, send `resume` with OLD
    `server_instance_id`, assert `resume_failed reason=server_restarted`.
18. **Resume after out_of_range**: connect, broadcast 2000 events, disconnect,
    reconnect, send `resume` with `last_seq = 10`, assert `resume_failed
    reason=out_of_range`.
19. **Resume with malformed data**: send `{"type": "resume", "data": {}}`, assert
    `resume_failed reason=malformed_resume`.
20. **Resume timeout (no initial frame)**: connect but never send any frame; assert
    after 5 s the client is promoted to active and receives live events normally.
21. **Atomic snapshot_seq**: GET `/api/v1/training/status` while broadcasts are in
    flight; assert `snapshot_seq == _next_seq - 1` at the moment of response
    generation (tested by asserting that `resume_since(snapshot_seq)` returns events
    with seq > snapshot_seq and no duplicates of snapshot-included events).

### 10.3 End-to-end tests (deferred to Phase B canopy work)

Items 22-25 below are NOT in Phase A-server acceptance; they are Phase B's job to
verify that a real browser flows through the cascor server correctly. I note them for
completeness because they exercise the same server code.

22. Playwright: `test_websocket_frames_have_seq_field`.
23. Playwright: `test_resume_protocol_replays_missed_events` (Phase B test).
24. dash_duo: `test_snapshot_to_live_handoff_no_duplicate_points`.
25. Playwright: `test_server_restart_triggers_snapshot_refetch`.

### 10.4 Load / soak tests (recommended but optional)

26. **Broadcast at 100 Hz for 60 s with 10 connected clients** (requires a small
    harness). Assert: no deque overflow beyond 1024, no send timeouts, seq
    monotonicity holds, memory usage stable within ±10%.
27. **Rolling reconnect test**: 10 clients continuously disconnect/reconnect at
    randomized intervals (1-10 s) during a 10-minute broadcast run. Assert no missed
    events (every client's seq-sequence has no gaps outside the documented
    reconnect window).

These are Phase E-server scope; not required for Phase A-server signoff.

### 10.5 Manual verification

For a reviewer of the Phase A-server PR:

1. `grep -r "seq" juniper-cascor/src/api/websocket/` — every outbound envelope builder
   mentions `seq`.
2. `grep -r "server_instance_id" juniper-cascor/src/api/websocket/` — appears in
   `connection_established`, `resume_failed`, and `WebSocketManager.__init__`.
3. `grep -r "_assign_seq_and_append" juniper-cascor/src/api/websocket/` — single
   definition in manager.py; called from `broadcast()` and `broadcast_from_thread()`
   paths only.
4. Read `manager.py` and verify there are NO other callers that write to
   `_active_connections` outside `connect_pending() / promote_to_active() / disconnect()
   / close_all()`.
5. Read the resume handler in `training_stream.py`; verify it is the ONLY place that
   calls `replay_since()`.

---

## 11. Disagreements with the source doc

### 11.1 GAP-WS-19 is already resolved on main as of 2026-04-11

**Source doc says**: `close_all()` does NOT acquire `_lock`, allowing an orphaned
connection race. Severity P2. Fix is to wrap the body in `async with self._lock:`.

**Actual state**: verified by reading `juniper-cascor/src/api/websocket/manager.py`
lines 138-156 on 2026-04-11. The method NOW does:

```python
async def close_all(self) -> None:
    async with self._lock:
        snapshot = list(self._active_connections)
        self._active_connections.clear()
        self._connection_meta.clear()
    for ws in snapshot:
        with contextlib.suppress(Exception):
            await ws.close(code=1001, reason="Server shutting down")
```

This is the exact fix the source doc prescribes, with the additional refinement that
the `ws.close()` loop is OUTSIDE the lock to avoid re-entering `disconnect()` on
exception paths. **GAP-WS-19 should be marked RESOLVED in the next source doc revision.**

**Consequence for this proposal**: I do not include a GAP-WS-19 fix in Phase A-server.
The source doc's v1.3 snapshot was captured on 2026-04-10; a fix landed between that
snapshot and 2026-04-11. This is concrete evidence that the source doc has drift risk
against main; Round 1 consolidation should do a fresh verification of all
`manager.py`-referencing GAPs.

### 11.2 Replay buffer should live on the WebSocketManager, not a separate object

**Source doc §6.5.1**: "The replay buffer is a `collections.deque(maxlen=1024)` of
`(seq, message)` tuples." Implied placement: on the manager. The source doc does not
explicitly address whether the buffer is a separate class or an attribute.

**My recommendation**: make it a plain attribute on `WebSocketManager`, not a
separate `ReplayBuffer` class. Rationale:

- Every lock interaction is on the manager's locks; splitting into a class adds
  indirection without decoupling.
- The buffer is always per-manager; there is no multi-buffer scenario.
- A named class would force naming discussions ("ReplayBuffer" vs "EventLog" vs
  "EventRing") that add no value.

**If later a canopy-side replay buffer is needed** (canopy forwarding cascor events
to its own /ws/training), that would be a separate `canopy.WebSocketManager` instance
with its own deque attribute. No shared abstraction needed.

### 11.3 `command_response` should NOT have a seq field

**Source doc §6.5 implies** that every server→client message has a `seq` field. It
doesn't explicitly carve out `command_response`.

**My position** (§6.3 above): command responses on `/ws/control` do not enter the
replay buffer and do not have a `seq` field. Rationale repeated: they are personal
RPC responses; replaying them on reconnect is semantically confusing; they are
matched by command/command_id, not by seq.

**Disagreement severity**: mild. The source doc doesn't explicitly claim
command_response needs a seq, but the natural reading is "all outbound messages". I
am asking Round 1 to formalize the carve-out.

### 11.4 Two-phase registration is new vocabulary not in the source doc

**Source doc §6.5** specifies the resume protocol but doesn't explicitly say how the
cascor server atomically transitions a connection from "under replay" to "live
broadcast-eligible". §5.1 above introduces `_pending_connections` / `promote_to_active()`
as the vehicle. This is my design choice; Round 1 consolidation should confirm it is
compatible with the canopy-side expectation. (The alternative — per-connection
seq_cursor — is also compatible but I argue is worse.)

### 11.5 Phase A-server should exist as a carved-out phase

**Source doc §9.3** (Phase B) bundles cascor-side sequence-number work with canopy
browser-bridge work as a 4-day phase. **I propose carving out Phase A-server** as a
~2-day prerequisite that cascor can ship independently, so canopy iterates against a
stable server.

**Benefit**: cascor-side work can be reviewed, merged, and deployed to the staging
cluster before any canopy-side code changes. Canopy's Playwright tests can then
exercise a real cascor instance with the seq+replay contract already in place.

**Risk**: cascor main carries `seq`-bearing envelopes for ~1 week while canopy Phase B
is in flight. This is fine because the field is additive — existing consumers
(juniper-cascor-client SDK, old canopy) ignore the new field via `dict.get()`. Source
doc §6.5.4 explicitly confirms this.

### 11.6 Minor — the source doc uses "server_start_time" and "server_instance_id" inconsistently

**Source doc §6.5 step 2** shows both fields in `connection_established`. Step 4's
`resume` request shape shows `server_start_time` alone ("... `{last_seq: N,
server_start_time: <float>}`"), then step 5 compares by `server_instance_id`. The
older terminology `server_start_time` from an earlier draft appears to have survived
in some spots.

**My proposal**: standardize on `server_instance_id` for the comparison key
throughout. `server_start_time` is advisory-only and included alongside for human
log correlation but never compared. I believe the source doc *intends* this per its
step 5 and its "UUID-based identity is immune to clock skew" language; the
step-4-vs-step-5 inconsistency is a source doc stale-text artifact. Flag for Round 1
cleanup.

---

## 12. Self-audit log

This section records the changes made during the re-read / edit pass after the
initial draft.

### 12.1 Self-audit pass

I re-read the draft looking for:

- Unclear data structures → resolved one ("pump task per client" was under-specified
  re: lifecycle; added explicit "cancelled on disconnect" and "3-strike" semantics).
- Missing failure modes → added §8.4 "Replay buffer overflow during a live reconnect"
  which I had not initially covered. This is a real correctness concern that deserved
  its own section.
- Weak observability → expanded §9.1 metric list from 8 to 15 metrics. Added explicit
  labels on the resume outcome counter because operational alerting needs to
  distinguish "server restarted" from "out of range".
- Section 6.3 ambiguity on whether `command_response` has a seq → made the position
  explicit (§6.3 and §11.3).
- §3.3 replay algorithm was missing the "copy-then-iterate under lock" discussion;
  added it explicitly.
- §7 originally had 6 commits; expanded to 10 to break the manager plumbing into
  smaller reviewable commits. Each commit green independently.
- §10 verification criteria was initially ~8 items; expanded to 27 items across
  unit/integration/E2E/load/manual.

### 12.2 Changes made in the edit pass

1. Added §8.4 (replay buffer overflow during live reconnect) — this is the race
   between `replay_since` iteration and ongoing `broadcast()` evictions.
2. Tightened §5.2 policy matrix with a per-type table.
3. Added §6.2's atomic snapshot-read discussion with a concrete code snippet for the
   REST `/api/v1/training/status` change.
4. Split §7.1 into 10 smaller commits rather than 6.
5. Added §11.1 (GAP-WS-19 already resolved) after verifying the current `manager.py`
   against the source doc's claim.
6. Added §11.6 (stale `server_start_time` vs `server_instance_id` in source doc).
7. Expanded §9 from a bare metrics table to labels, thresholds, and alert rules.
8. Added §3.2 assertion about `broadcast()` callers funneling through
   `_assign_seq_and_append` — this is a real invariant that belongs in the contract.
9. Added §4.1's `replay_buffer_capacity` field on `connection_established` — not in
   source doc but a minor extension that helps clients optimize.
10. Added §6.3's explicit carve-out that `/ws/control` `command_response` has no
    `seq` and separate discussion at §11.3.

### 12.3 Items I considered and did not include

- **Subprotocol negotiation (`Sec-WebSocket-Protocol: juniper-cascor.v1.1`)**: source
  doc §7.34 explicitly defers this. I agree — the `seq` field is additive, so
  forward-compat is maintained.
- **Compression / `permessage-deflate` (GAP-WS-17)**: out of my lane for Phase
  A-server; it's an independent cascor PR with no dependency on sequence numbers or
  replay.
- **Topology chunking (GAP-WS-18 / RISK-16)**: touches `messages.py` and the training
  loop emission code, but is a separate piece of work that can land parallel to Phase
  A-server. I mention it in §7.3 as explicitly NOT in scope for Phase A-server.
- **REST snapshot endpoint rework**: only the `snapshot_seq` field addition is in
  Phase A-server (§6.2). A deeper restructuring of `/api/v1/training/status` is not
  needed.
- **Per-IP caps (M-SEC-04)**: security lane. I reference it (§5.3 disconnect cleanup)
  only to note that the decrement must live in the same cleanup path, not to design
  it.
- **Metric/candidate-progress payload optimization (source doc §7.34 deferred items)**:
  bandwidth is not a cascor-side concern for Phase A-server; the source doc's
  16 KB/s budget is comfortable.

### 12.4 Confidence self-assessment

- **High confidence**:
  - Replay buffer structure (deque) and capacity rationale.
  - `server_instance_id` generation / lifetime / semantics.
  - Seq assignment lock ordering.
  - Phase A-server commit breakdown.
- **Medium confidence**:
  - Two-phase registration design (§5.1). An alternative per-connection seq_cursor
    might be simpler; Round 1 should weigh both.
  - Backpressure policy matrix (§5.2). The close-vs-drop split between state and
    progress events is defensible but there are other reasonable choices.
  - The §8.4 race mitigation via "promote under lock, de-dup on client". The client
    contract load-bearing-ness of de-dup deserves explicit Round 1 confirmation.
- **Lower confidence**:
  - Exact `_send_json` timeout value of 0.5 s. It's a reasonable starting point but
    should be measured against real RTT distributions.
  - Whether `command_response` should or should not have a `seq` (§11.3). I have a
    reasoned position but it's a judgment call.
  - Whether Phase A-server carve-out (§11.5) is operationally better than one big
    Phase B PR. Depends on release-coordination preferences.

### 12.5 Open questions I would like Round 1 to answer

1. **Is Phase A-server accepted as a carved-out phase, or does it fold back into Phase
   B?** My argument is in §11.5.
2. **Does `command_response` carry `seq`?** My position is no (§11.3). Round 1 should
   formalize.
3. **Are the Phase E-server backpressure policies acceptable defaults?** I propose
   close-for-state / drop-oldest-for-progress. Alternative is always-close.
4. **Do we want a compatibility-probe mechanism** for older clients that don't
   understand `resume`? Source doc §6.5.3 says "older clients get an Unknown command
   error on resume and fall back to snapshot." Verify this is the consolidation
   position.
5. **Is `replay_buffer_capacity` on `connection_established` acceptable as an
   additive field?** I added it; source doc does not require it. Harmless if
   rejected.
6. **Should cascor emit a `server_instance_id`-changed event if the manager is hot-
   reloaded mid-process?** My §4.1 says no (hot reload IS a restart from the client's
   POV). Round 1 should confirm.

---

**End of R0-03 Cascor Server Backend proposal.**
