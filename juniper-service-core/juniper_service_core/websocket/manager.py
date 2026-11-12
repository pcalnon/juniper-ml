"""WebSocket connection manager for real-time streaming (WS-2 / OUT-11 T2 step 2).

The de-cascored core of cascor's ``api/websocket/manager.py`` (CLEAN per design §5.6: the
broadcast / sequencing / replay-buffer / chunking infra is already model-agnostic). A
thread-safe manager that handles:

- Connection lifecycle (connect / disconnect / pending) + a bounded global and per-IP limit.
- Monotonically increasing sequence numbers on broadcasts -- every broadcast, whether or not a
  client is connected, so a gap in the numbering is a gap in what the client received.
- A bounded replay buffer for client reconnection (``replay_since``), and a resume promotion
  (``promote_to_active(..., replayed_through=...)``) that delivers whatever was broadcast while
  the replay was being sent before the socket joins the live stream.
- A thread-safe bridge for broadcasting from training threads (``broadcast_from_thread``).
- A configurable send timeout to prevent a slow client from blocking broadcast fan-out. A socket
  whose broadcast send fails or times out is dropped from the fan-out and closed **1011**, so its
  client reconnects (and can resume) instead of holding a stream nothing is sent to.
- Oversized-message chunking so a single frame never exceeds the WebSocket intermediary limit.

cascor's copy also pushed a dozen Prometheus gauges/counters via ``api.observability`` on every
connect / seq-assign / send; those emissions are **dropped** here (cascor-internal). The same
counters remain in :meth:`transport_stats` so a service can surface them through its own
``/metrics`` however it likes.

Requires ``fastapi`` -- the :mod:`juniper_service_core` top-level package keeps this whole
subpackage off the eager import path (PEP 562 lazy export).
"""

from __future__ import annotations

import asyncio
import bisect
import contextlib
import functools
import itertools
import json
import logging
import threading
import time
import uuid
from collections import deque
from concurrent.futures import CancelledError
from typing import Any

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

__all__ = ["WebSocketManager", "ws_authenticate", "ReplayOutOfRange", "DEFAULT_WS_ENDPOINTS"]

logger = logging.getLogger("juniper_service_core.websocket")

#: The close a broadcast sends to a socket it drops because a send to it failed or timed out. 1011,
#: as for this package's other server-side ends of a ``/ws/training`` socket (a heartbeat timeout,
#: an incomplete resume), and as juniper-cascor closes its copy's dropped subscribers (its
#: F-CASCOR-004, same code and reason). The reason names the cause, well under RFC 6455's 123 bytes.
_BROADCAST_DROP_CLOSE_CODE = 1011
_BROADCAST_DROP_CLOSE_REASON = "Broadcast send failed or timed out"


def _is_closed(websocket: WebSocket) -> bool:
    """Whether Starlette has marked either side of ``websocket`` closed.

    ``application_state`` turns ``DISCONNECTED`` once the app has sent its close (a heartbeat
    timeout, :meth:`WebSocketManager.close_all`, an aborted resume) or a send has met a dead
    transport; ``client_state`` once the peer's disconnect has been received. A socket without
    either attribute (a test double) reads as open.
    """
    return WebSocketState.DISCONNECTED in (getattr(websocket, "application_state", None), getattr(websocket, "client_state", None))


#: The per-endpoint connection buckets the generic base tracks: the two client-facing channels
#: (``training`` / ``control``) plus the machine-to-machine ``worker`` channel (step-3b
#: ``/ws/workers``). A service can pass a different tuple to :class:`WebSocketManager`; the worker
#: stream registers under :data:`~juniper_service_core.websocket.worker_stream.WORKER_WS_ENDPOINT`
#: (``"worker"``), so that name must be present for the per-endpoint gauge to count worker sockets.
DEFAULT_WS_ENDPOINTS: tuple[str, ...] = ("training", "control", "worker")


def _buffered_seq(message: dict) -> int:
    """The bisect key of a replay-buffer entry: its seq (0 if it has none)."""
    return message.get("seq", 0)


# N818 noqa: package exception surface; "Error"-suffix rename deferred to a
# deliberate API revision (see TrainingInterrupted in lifecycle/manager.py).
class ReplayOutOfRange(Exception):  # noqa: N818
    """Raised when the requested seq is no longer in the replay buffer."""


async def ws_authenticate(websocket: WebSocket) -> bool:
    """Authenticate a WebSocket connection via the ``X-API-Key`` header.

    Shared utility replacing inline auth boilerplate in each stream handler. ``BaseHTTPMiddleware``
    cannot intercept WebSocket upgrades, so each WS endpoint must authenticate independently.
    Reads the optional :class:`~juniper_service_core.security.APIKeyAuth` off
    ``websocket.app.state.api_key_auth``; when absent or disabled, the connection is allowed.

    Returns:
        ``True`` if authenticated (or auth disabled). ``False`` if auth failed (the connection
        is closed with code 4001).
    """
    auth = getattr(websocket.app.state, "api_key_auth", None)
    if auth is not None and getattr(auth, "enabled", False):
        api_key = websocket.headers.get("X-API-Key")
        if not auth.validate(api_key):
            await websocket.close(code=4001, reason="Authentication required")
            return False
    return True


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting.

    Provides both async and thread-safe broadcasting to support the training-thread ->
    async-WebSocket bridge pattern. Assigns monotonically increasing sequence numbers to all
    broadcast messages and maintains a bounded replay buffer for client reconnection.
    """

    def __init__(
        self,
        max_connections: int = 50,
        max_replay_buffer_size: int = 1024,
        send_timeout_seconds: float = 0.5,
        max_connections_per_ip: int = 5,
        max_message_size_bytes: int = 60_000,
        chunk_payload_size_bytes: int = 32_000,
        *,
        endpoints: tuple[str, ...] = DEFAULT_WS_ENDPOINTS,
    ):
        # Connection tracking
        self._active_connections: set[WebSocket] = set()
        self._pending_connections: set[WebSocket] = set()
        # Per-endpoint active-connection sets, used for per-endpoint accounting. Keys are the
        # closed set passed in ``endpoints``; sets are disjoint in steady state. Pending
        # (resume-handshake) connections are NOT counted -- the buckets track broadcast-eligible
        # connections only.
        self._endpoint_connections: dict[str, set[WebSocket]] = {name: set() for name in endpoints}
        # Reverse lookup: ws -> endpoint, populated at connect time and consulted at disconnect.
        self._connection_endpoint: dict[WebSocket, str] = {}
        self._max_connections = max_connections
        # Per-IP cap. Stored as ``ip -> count`` and updated under ``self._lock`` alongside the
        # connection sets. Unknown clients all share the sentinel key "unknown".
        self._max_connections_per_ip = max_connections_per_ip
        self._per_ip_counts: dict[str, int] = {}
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._connection_meta: dict[WebSocket, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        # Server identity (programmatic restart detection for the resume handshake)
        self._server_instance_id: str = str(uuid.uuid4())
        self._server_start_time: float = time.monotonic()

        # Sequencing and replay (threading.Lock: used from both async and sync contexts)
        self._next_seq: int = 1
        self._seq_lock = threading.Lock()
        self._replay_buffer: deque = deque(maxlen=max_replay_buffer_size if max_replay_buffer_size > 0 else None)
        self._replay_buffer_max_size = max_replay_buffer_size

        # Send timeout
        self._send_timeout_seconds = send_timeout_seconds
        # Closes of sockets a broadcast dropped (see _drop), one per socket, each held until it
        # finishes -- including one that outlives the broadcast's bounded wait -- because the event
        # loop keeps only a weak reference to a task. Known limit: a close that never finishes (the
        # transport never takes the frame) is held here, with its socket, until the socket is
        # disconnected after its peer has gone (disconnect() then cancels it); close_all() neither
        # awaits nor cancels it.
        self._closing: dict[WebSocket, asyncio.Task] = {}

        # Bandwidth counters. Updated under ``_seq_lock`` because the send path is invoked from
        # both the asyncio event loop and the broadcast-from-thread shim. Cumulative since
        # process start; surfaced via :meth:`transport_stats`.
        self._bytes_sent_total: int = 0
        self._messages_sent_total: int = 0
        self._messages_sent_by_type: dict[str, int] = {}
        self._bytes_sent_by_type: dict[str, int] = {}
        self._send_failures: int = 0

        # Message-size guard + chunking. Broadcasts whose serialized JSON exceeds
        # ``max_message_size_bytes`` are split into a sequence of ``chunked_message`` envelopes
        # (each payload <= ``chunk_payload_size_bytes``) so we never push a single frame over the
        # typical 64 KB WebSocket intermediary limit. Each chunk is its own broadcast (own seq,
        # own replay-buffer slot), so resume on reconnect reorders them naturally.
        self._max_message_size_bytes = max_message_size_bytes
        self._chunk_payload_size_bytes = chunk_payload_size_bytes
        self._messages_chunked_total: int = 0
        self._chunks_emitted_total: int = 0

        logger.info(
            "WebSocketManager initialized (max_connections=%d, replay_buffer=%d, send_timeout=%.1fs)",
            max_connections,
            max_replay_buffer_size,
            send_timeout_seconds,
        )

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Store the event loop reference for thread-safe broadcasting.

        Idempotent -- the stream handlers call this on connect (they run on the serving loop),
        so a service does not need a separate startup hook to enable ``broadcast_from_thread``.
        """
        self._event_loop = loop

    @property
    def server_instance_id(self) -> str:
        """UUID4 identifying this server process (resume-handshake restart detection)."""
        return self._server_instance_id

    @property
    def current_seq(self) -> int:
        """The last assigned sequence number (0 if none assigned yet)."""
        with self._seq_lock:
            return self._next_seq - 1

    @property
    def connection_count(self) -> int:
        return len(self._active_connections)

    # ------------------------------------------------------------------
    # Per-endpoint connection bookkeeping
    # ------------------------------------------------------------------

    def register_endpoint_connection(self, websocket: WebSocket, endpoint: str) -> None:
        """Add ``websocket`` to the ``endpoint`` bucket.

        Callers (each WS endpoint handler) invoke this after ``websocket.accept()`` so the
        bucket reflects the broadcast-eligible connection set, not the in-handshake set. Pair
        with :meth:`unregister_endpoint_connection` in a ``finally`` so disconnects always
        clean up, even on exception paths.
        """
        if endpoint not in self._endpoint_connections:
            # Unknown endpoint -- log once and treat as a no-op rather than silently miscount.
            logger.warning("register_endpoint_connection: unknown endpoint %r (no-op)", endpoint)
            return
        self._endpoint_connections[endpoint].add(websocket)
        self._connection_endpoint[websocket] = endpoint

    def unregister_endpoint_connection(self, websocket: WebSocket) -> None:
        """Remove ``websocket`` from its endpoint bucket (idempotent).

        Looks up the endpoint via ``_connection_endpoint`` so the caller does not need to
        re-pass it (matches the :meth:`disconnect` signature that has no endpoint argument).
        """
        endpoint = self._connection_endpoint.pop(websocket, None)
        if endpoint is None:
            return
        bucket = self._endpoint_connections.get(endpoint)
        if bucket is not None:
            bucket.discard(websocket)

    def endpoint_counts(self) -> dict[str, int]:
        """Per-endpoint broadcast-eligible connection counts (for a service's own metrics)."""
        return {name: len(bucket) for name, bucket in self._endpoint_connections.items()}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def _build_connection_established(self) -> dict:
        """Build the ``connection_established`` handshake message."""
        return {
            "type": "connection_established",
            "timestamp": time.time(),
            "data": {
                "connections": self.connection_count + len(self._pending_connections),
                "server_instance_id": self._server_instance_id,
                "server_start_time": self._server_start_time,
                "replay_buffer_capacity": self._replay_buffer_max_size,
            },
        }

    def _source_ip(self, websocket: WebSocket) -> str:
        """Best-effort source IP for per-IP accounting."""
        client = getattr(websocket, "client", None)
        if client is not None:
            try:
                return client[0] or "unknown"
            except (IndexError, TypeError):
                return "unknown"
        return "unknown"

    def _check_and_reserve_per_ip_slot(self, source_ip: str) -> bool:
        """Reserve a per-IP slot; returns ``False`` if the cap would be exceeded.

        Must be called with ``self._lock`` held. On success the caller is responsible for
        invoking :meth:`_release_per_ip_slot` on disconnect.
        """
        current = self._per_ip_counts.get(source_ip, 0)
        if current >= self._max_connections_per_ip:
            return False
        self._per_ip_counts[source_ip] = current + 1
        return True

    def _release_per_ip_slot(self, source_ip: str | None) -> None:
        """Release a per-IP slot previously reserved by :meth:`_check_and_reserve_per_ip_slot`."""
        if not source_ip:
            return
        current = self._per_ip_counts.get(source_ip, 0)
        if current <= 1:
            self._per_ip_counts.pop(source_ip, None)
        else:
            self._per_ip_counts[source_ip] = current - 1

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept and register a WebSocket connection as immediately active.

        The socket joins the broadcast fan-out, so :meth:`broadcast` closes it 1011 when a send to
        it fails or times out. A handler of the service's own that serves a socket it registered
        here must expect that close: once the app has closed, Starlette refuses a new
        ``receive_text()`` with ``RuntimeError``, not ``WebSocketDisconnect``. Such a handler reads
        with ``receive()`` until ``websocket.disconnect`` instead, as ``/ws/training``'s receive
        loop does.

        Returns:
            ``True`` if connected, ``False`` if a connection limit was reached.
        """
        async with self._lock:
            total = len(self._active_connections) + len(self._pending_connections)
            if total >= self._max_connections:
                await websocket.close(code=1013, reason="Maximum connections reached")
                logger.warning("Connection rejected: limit of %d reached", self._max_connections)
                return False

            source_ip = self._source_ip(websocket)
            if not self._check_and_reserve_per_ip_slot(source_ip):
                await websocket.close(code=1013, reason="Per-IP connection limit reached")
                logger.warning("Connection rejected: per-IP limit of %d reached for %s", self._max_connections_per_ip, source_ip)
                return False

            await websocket.accept()
            self._active_connections.add(websocket)
            self._connection_meta[websocket] = {"connected_at": time.time(), "source_ip": source_ip}
            logger.info("WebSocket connected (%d active)", self.connection_count)

        await self._send_json(websocket, self._build_connection_established())
        return True

    async def connect_pending(self, websocket: WebSocket) -> bool:
        """Accept a WebSocket in pending state (not broadcast-eligible).

        Used during the resume-handshake window. The connection receives
        ``connection_established`` but does NOT receive broadcasts until
        :meth:`promote_to_active` is called.

        Returns:
            ``True`` if accepted, ``False`` if a connection limit was reached.
        """
        async with self._lock:
            total = len(self._active_connections) + len(self._pending_connections)
            if total >= self._max_connections:
                await websocket.close(code=1013, reason="Maximum connections reached")
                logger.warning("Connection rejected: limit of %d reached", self._max_connections)
                return False

            source_ip = self._source_ip(websocket)
            if not self._check_and_reserve_per_ip_slot(source_ip):
                await websocket.close(code=1013, reason="Per-IP connection limit reached")
                logger.warning("Pending connection rejected: per-IP limit of %d reached for %s", self._max_connections_per_ip, source_ip)
                return False

            await websocket.accept()
            self._pending_connections.add(websocket)
            self._connection_meta[websocket] = {"connected_at": time.time(), "pending": True, "source_ip": source_ip}
            logger.info("WebSocket connected as pending (%d pending)", len(self._pending_connections))

        await self._send_json(websocket, self._build_connection_established())
        return True

    async def promote_to_active(self, websocket: WebSocket, *, replayed_through: int | None = None) -> bool:
        """Move a pending connection to active (broadcast-eligible).

        Must be called after the resume handshake completes.

        A socket that resumed passes ``replayed_through``: the last seq it now holds (the last
        replayed seq, or its own ``last_seq`` when nothing was replayed). A broadcast that lands
        while the replay is being sent is buffered, but its fan-out reaches only the sockets
        already active. So this first sends the socket every buffered frame above
        ``replayed_through``, in seq order and exactly as the live fan-out sent it, and repeats
        until none is left. That last check and the activation run under ``self._lock`` with no
        ``await`` between them, and :meth:`broadcast` assigns a seq and copies the active set
        with no ``await`` between them, so every seq assigned after the activation fans out to
        the socket. Every seq above ``replayed_through`` assigned before it is sent here, once
        each, in seq order, and before the first live frame.

        From then on the socket is one of the active set, with no stronger ordering than any
        other: two broadcasts that overlap (each ``broadcast_from_thread`` call is its own task)
        can interleave their sends, and a live send that fails drops the socket from the fan-out
        and closes it 1011 (:meth:`broadcast`).
        The activation waits for as long as new broadcasts keep landing during each pass's sends;
        nothing is lost meanwhile, and a socket that falls more than the buffer behind is refused
        rather than promoted over the gap. The guarantee assumes every :meth:`broadcast` runs on
        this manager's event loop; another thread must use :meth:`broadcast_from_thread`. It also
        assumes one promotion per socket: if another call activates the socket while the catch-up
        is sending, the catch-up's next check finds it active and returns ``True``, and a seq
        assigned after the catch-up last read the buffer but before that other activation reaches
        the socket by neither path.

        Returns:
            ``True`` once the socket is active. ``False`` when ``replayed_through`` was given and
            continuity cannot be kept -- a frame the client still needs was evicted from the
            replay buffer before it could be sent (or replay is disabled), a send failed, or the
            socket was disconnected or closed meanwhile. The socket is then not promoted: close
            it so the client reconnects, and :meth:`disconnect` it (if nothing has yet) to release
            its connection and per-IP slots. Without ``replayed_through`` the promotion is
            unconditional, as it always was, and returns ``True``.
        """
        if replayed_through is None:
            async with self._lock:
                self._activate(websocket)
            return True
        return await self._catch_up_and_activate(websocket, replayed_through)

    def _activate(self, websocket: WebSocket) -> None:
        """Move ``websocket`` from pending to active. Call with ``self._lock`` held."""
        self._pending_connections.discard(websocket)
        self._active_connections.add(websocket)
        meta = self._connection_meta.get(websocket, {})
        meta.pop("pending", None)
        logger.info("WebSocket promoted to active (%d active, %d pending)", self.connection_count, len(self._pending_connections))

    async def _catch_up_and_activate(self, websocket: WebSocket, replayed_through: int) -> bool:
        """Send every buffered frame above ``replayed_through``, then activate.

        See :meth:`promote_to_active`. The continuity rule is :meth:`replay_since`'s, read under
        ``self._lock``: a non-empty answer is sent outside the lock and the check repeats; an
        empty one is acted on before anything else can run on the loop. Every pass either
        sends at least one frame (the cursor strictly advances) or returns. It returns ``True``
        once it has caught up, or ``False`` once the bounded buffer has evicted a seq it had not
        yet sent; until then it is sending each broadcast, in order.
        """
        # Seqs start at 1, so a cursor below 0 holds no more than 0 does; replay_since would
        # read a negative one as older than the buffer and refuse a continuous resume.
        cursor = max(replayed_through, 0)
        while True:
            async with self._lock:
                if websocket not in self._pending_connections:
                    if websocket in self._active_connections:
                        return True  # already active: it receives every broadcast
                    # Disconnected or closed meanwhile (a shutdown, say): never resurrect it.
                    logger.info("Resume catch-up stopped after seq %s: the socket was disconnected or closed; not promoted", cursor)
                    return False
                try:
                    missed = self.replay_since(cursor)
                except ReplayOutOfRange as exc:
                    logger.warning("Resume catch-up from seq %s failed: %s; the socket is not promoted", cursor, exc)
                    return False
                if not missed:
                    self._activate(websocket)
                    return True
            for frame in missed:
                # Sent exactly as broadcast sent it live: a buffered frame was sized, and chunked if
                # it had to be, before its seq was assigned. send_personal_message would size the
                # enriched copy again and could split one near the limit into seq-less chunks.
                if not await self._send_json(websocket, frame):
                    # INFO, as the live fan-out logs a failed send: most often the client went
                    # away or a shutdown closed the socket, and _send_json has already logged a
                    # send that timed out at WARNING.
                    logger.info("Resume catch-up failed: seq %s was not delivered; the socket is not promoted", frame.get("seq"))
                    return False
                cursor = frame["seq"]

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection (from active or pending).

        Once the peer's disconnect has been received, a close that a broadcast's drop started on
        this socket and that is still pending is cancelled: the connection is gone, so the frame
        has nowhere to go. A transport that never takes it would otherwise keep that close, and
        the socket, after the connection itself has gone: under uvicorn's ``wsproto`` protocol,
        whose ``send`` waits for a writable flag that a full write buffer clears and
        ``connection_lost`` does not set, the close of a client that had stopped reading was still
        pending after that client had left. While the peer is still there, the close is left alone.
        """
        async with self._lock:
            self._active_connections.discard(websocket)
            self._pending_connections.discard(websocket)
            meta = self._connection_meta.pop(websocket, None)
            # Release the per-IP slot reserved at connect time so a clean reconnect does not
            # accrue phantom counts against the cap.
            if meta is not None:
                self._release_per_ip_slot(meta.get("source_ip"))
            logger.info("WebSocket disconnected (%d active, %d pending)", self.connection_count, len(self._pending_connections))
        closing = self._closing.get(websocket)
        if closing is not None and getattr(websocket, "client_state", None) is WebSocketState.DISCONNECTED:
            closing.cancel()

    # ------------------------------------------------------------------
    # Sequencing and replay
    # ------------------------------------------------------------------

    def _assign_seq_and_buffer(self, message: dict) -> dict:
        """Assign a monotonically increasing seq and buffer the message for replay.

        Called by :meth:`broadcast`, on the manager's event loop, before the fan-out (see
        :meth:`broadcast` for why it must be that loop). ``_seq_lock`` is a ``threading.Lock``
        (not an ``asyncio.Lock``) because the counters and the buffer are also read from
        synchronous code: :attr:`current_seq`, :meth:`replay_since`, :meth:`transport_stats`.
        Here it is held only for O(1) operations (integer increment + deque append).
        """
        with self._seq_lock:
            seq = self._next_seq
            self._next_seq += 1
            enriched = {**message, "seq": seq, "emitted_at_monotonic": time.monotonic()}
            if self._replay_buffer_max_size > 0:
                self._replay_buffer.append(enriched)
        return enriched

    def replay_since(self, last_seq: int) -> list[dict]:
        """Return buffered messages with ``seq > last_seq``, in order.

        Raises:
            ReplayOutOfRange: If ``last_seq`` is older than the oldest buffered message, or if
                the replay buffer is disabled (size 0).
        """
        with self._seq_lock:
            if self._replay_buffer_max_size <= 0:
                raise ReplayOutOfRange("Replay buffer disabled")
            if not self._replay_buffer:
                if last_seq > 0:
                    raise ReplayOutOfRange("Buffer empty, cannot verify continuity")
                return []
            oldest_seq = self._replay_buffer[0].get("seq", 0)
            if last_seq < oldest_seq - 1:
                raise ReplayOutOfRange(f"Requested seq {last_seq} older than oldest buffered seq {oldest_seq}")
            # Replay-buffer seqs are monotonically increasing (assigned under ``_seq_lock``), so
            # a bisect_right over the deque finds the cut in O(log n) probes, and only the tail
            # after it is copied. A resume catch-up reads the buffer once per pass, and copying
            # all of it every time would cost the whole buffer per pass however little is left.
            idx = bisect.bisect_right(self._replay_buffer, last_seq, key=_buffered_seq)
            tail = list(itertools.islice(reversed(self._replay_buffer), len(self._replay_buffer) - idx))
            tail.reverse()
            return tail

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _maybe_chunk_message(self, message: dict, *, quiet: bool = False) -> list[dict]:
        """Return ``[message]`` if under threshold, else a list of chunked envelopes.

        Oversized broadcasts (~64 KB) silently tear down WebSocket connections at
        intermediaries. We split here, BEFORE seq assignment, so each chunk gets its own seq +
        replay slot and resume-on-reconnect reorders chunks naturally.

        Chunking is skipped (returns ``[message]``) when:
        - ``max_message_size_bytes`` is 0 (kill-switch for tests),
        - the serialized JSON length is <= the threshold, or
        - the message is already a ``chunked_message`` envelope (no recursion).

        ``quiet`` logs the split at DEBUG instead of INFO (a broadcast with no socket active).
        """
        if self._max_message_size_bytes <= 0:
            return [message]
        if message.get("type") == "chunked_message":
            return [message]
        try:
            serialized = json.dumps(message, default=str)
        except (TypeError, ValueError):
            # If we can't serialize for sizing, let _send_json handle the error.
            return [message]
        if len(serialized) <= self._max_message_size_bytes:
            return [message]

        chunk_size = self._chunk_payload_size_bytes
        chunk_id = str(uuid.uuid4())
        original_type = str(message.get("type") or "unknown")
        payloads = [serialized[i : i + chunk_size] for i in range(0, len(serialized), chunk_size)]
        total = len(payloads)
        chunks = [
            {
                "type": "chunked_message",
                "timestamp": time.time(),
                "data": {
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                    "total_chunks": total,
                    "original_type": original_type,
                    "payload": payload,
                },
            }
            for idx, payload in enumerate(payloads)
        ]
        with self._seq_lock:
            self._messages_chunked_total += 1
            self._chunks_emitted_total += total
        logger.log(logging.DEBUG if quiet else logging.INFO, "WebSocket: chunked %s message (%d bytes) into %d chunks (chunk_id=%s)", original_type, len(serialized), total, chunk_id)
        return chunks

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(self, message: dict) -> None:
        """Assign seq, buffer for replay, and send a message to all active (non-pending) clients.

        A broadcast is sequenced and buffered whether or not any client is active. A client that
        resumes from its last seq is then replayed what was broadcast while it was away or still
        pending its handshake -- or told ``out_of_range`` once that has left the buffer -- rather
        than answered ``resume_ok`` over a gap it cannot see. With no client active the fan-out
        is simply empty (and a split is logged at DEBUG rather than INFO).

        Oversized messages are split into ``chunked_message`` envelopes before seq assignment so
        each chunk gets its own seq and replay slot.

        A socket that a send raised on or timed out for is dropped from the fan-out and closed
        1011 ``Broadcast send failed or timed out`` (:meth:`_drop`); the other sockets are
        unaffected. Its client reconnects, and a resume from its last seq replays the frame it
        missed while that is still buffered.

        Must run on the manager's event loop (the one the stream handlers serve on, which
        :meth:`set_event_loop` records); from another thread use :meth:`broadcast_from_thread`.
        A resume's continuity (:meth:`promote_to_active`) rests on a broadcast assigning its seq
        and copying the active set with nothing else running on the loop in between, and a
        broadcast running on another thread can land between the catch-up's last check and the
        activation.
        """
        for sub_message in self._maybe_chunk_message(message, quiet=not self._active_connections):
            enriched = self._assign_seq_and_buffer(sub_message)
            disconnected = []
            # No ``await`` between assigning the seq and copying the active set: the recipients
            # of each seq are exactly the sockets active when it was assigned. The resume
            # catch-up in promote_to_active relies on that.
            for ws in self._active_connections.copy():
                if not await self._send_json(ws, enriched):
                    disconnected.append(ws)
            if disconnected:
                await self._drop(disconnected, enriched["seq"])

    async def _drop(self, sockets: list[WebSocket], seq: int) -> None:
        """Drop the sockets a broadcast could not send ``seq`` to, and close each one 1011.

        :meth:`disconnect` alone only forgets a socket. Left open, the socket kept its handler's
        receive loop and heartbeat running, so the client went on answering pings on a stream that
        nothing was broadcast to, never told it was missing frames, for as long as it stayed.
        Closed, the client reconnects, and a resume from its last seq replays what it missed while
        that is still buffered.

        Known limit: the drop still releases the socket's connection and per-IP slots here, before
        the socket is gone, and ``endpoint_counts()`` counts the socket until its handler returns.
        While the close is in progress, a new socket from the same address can therefore be
        admitted past ``max_connections_per_ip``: for an instant with a peer that answers the
        close, and for as long as the ASGI server takes to give up on one that has stopped reading.
        The close bounds that excess by its own length; without it the excess lasted for as long
        as the client kept the socket open.

        Every socket is forgotten before any close starts, so an overlapping broadcast stops
        targeting them. A socket that something has already closed -- the server or the peer
        (:func:`_is_closed`) -- or that an overlapping broadcast is closing already, is not closed
        again. The closes run concurrently, and the broadcast waits for them at most one send
        timeout in all, because a peer too slow to take a frame may be as slow to take the close.
        The bound limits the wait, not the close: ``asyncio.wait`` neither cancels nor shields it,
        and a close still in flight finishes in the background (:meth:`_close_done`). The one
        thing that cancels it is :meth:`disconnect` of the same socket after its peer has gone.
        """
        for ws in sockets:
            await self.disconnect(ws)
        closes = []
        for ws in sockets:
            if ws in self._closing or _is_closed(ws):
                continue
            closing = asyncio.create_task(self._close_dropped(ws))
            self._closing[ws] = closing
            closing.add_done_callback(functools.partial(self._close_done, ws))
            closes.append(closing)
        # INFO, as a failed send is logged elsewhere: most often the client went away, and
        # _send_json has already logged a send that timed out at WARNING.
        logger.info("Broadcast of seq %s failed for %d socket(s): dropped them, and closing %d with %d", seq, len(sockets), len(closes), _BROADCAST_DROP_CLOSE_CODE)
        if closes:
            await asyncio.wait(closes, timeout=self._send_timeout_seconds)

    @staticmethod
    async def _close_dropped(websocket: WebSocket) -> None:
        """Close a socket a broadcast dropped (a coroutine, so any failure lands in its task)."""
        await websocket.close(code=_BROADCAST_DROP_CLOSE_CODE, reason=_BROADCAST_DROP_CLOSE_REASON)

    def _close_done(self, websocket: WebSocket, closing: asyncio.Task) -> None:
        """Release a finished close, and retrieve its outcome so a failure is not reported unretrieved.

        A close can fail without anything being wrong -- the transport may already be gone -- so it
        is logged at DEBUG.
        """
        self._closing.pop(websocket, None)
        if not closing.cancelled() and closing.exception() is not None:
            logger.debug("Closing a dropped WebSocket failed: %r", closing.exception())

    def broadcast_from_thread(self, message: dict) -> None:
        """Thread-safe broadcast using ``asyncio.run_coroutine_threadsafe``.

        Called from the training thread to push messages to all WebSocket clients. Adds a done
        callback to log exceptions from the coroutine. A no-op if the event loop has not been
        captured yet (of the shipped handlers only ``/ws/training`` captures it, on each
        connect) or is closed. Such a message is never sequenced.
        No client of the shipped handlers can be relying on it: they expose the
        ``server_instance_id`` a resume must present only through the manager's
        ``connection_established``, and ``/ws/training`` captures the loop before it calls
        :meth:`connect_pending`. A service accepting sockets through :meth:`connect` from its own
        handler should call :meth:`set_event_loop` first, for the same reason.
        """
        if self._event_loop is None or self._event_loop.is_closed():
            return
        coro = self.broadcast(message)
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
            future.add_done_callback(self._log_broadcast_exception)
        except Exception:
            coro.close()
            logger.debug("Cannot broadcast: event loop unavailable or closed")

    @staticmethod
    def _log_broadcast_exception(future) -> None:
        """Done callback for broadcast futures -- logs exceptions."""
        try:
            exc = future.exception()
        except CancelledError:
            return
        if exc is not None:
            logger.error("Broadcast from thread failed: %s", exc, exc_info=exc)

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> bool:
        """Send a message to a specific client (no seq assignment).

        Oversized personal messages are split into ``chunked_message`` envelopes the same way
        broadcasts are. Personal messages don't carry seq, so on reconnect a partially-delivered
        chunk group is dropped by the client (no resume), but no socket teardown.

        Returns ``True`` only if every chunk was delivered successfully. A failed send neither drops
        nor closes the socket: the caller decides (``/ws/training`` ends a resume that cannot be
        kept with its own 1011 close), and an active socket is dropped and closed by the first
        broadcast whose send to it fails.
        """
        for sub_message in self._maybe_chunk_message(message):
            if not await self._send_json(websocket, sub_message):
                return False
        return True

    async def _send_json(self, websocket: WebSocket, message: dict) -> bool:
        """Send a JSON message to a single WebSocket with a timeout.

        Applies a configurable send timeout (default 0.5s) to prevent a slow client from
        blocking broadcast fan-out. Returns ``False`` on failure or timeout.
        """
        try:
            await asyncio.wait_for(websocket.send_json(message), timeout=self._send_timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning("WebSocket send timed out after %.1fs", self._send_timeout_seconds)
            with self._seq_lock:
                self._send_failures += 1
            return False
        except Exception:
            with self._seq_lock:
                self._send_failures += 1
            return False
        # Account bytes after a successful send. We re-serialize to size the payload because
        # Starlette's send_json hides the wire bytes; the double-encode is cheap.
        try:
            byte_size = len(json.dumps(message, default=str))
        except (TypeError, ValueError):
            byte_size = 0
        self._account_send(message, byte_size)
        return True

    def _account_send(self, message: dict, byte_size: int) -> None:
        """Record a successful WS send for bandwidth telemetry."""
        msg_type = str(message.get("type") or "unknown")
        with self._seq_lock:
            self._bytes_sent_total += byte_size
            self._messages_sent_total += 1
            self._messages_sent_by_type[msg_type] = self._messages_sent_by_type.get(msg_type, 0) + 1
            self._bytes_sent_by_type[msg_type] = self._bytes_sent_by_type.get(msg_type, 0) + byte_size

    def transport_stats(self) -> dict[str, Any]:
        """Snapshot of cumulative WS transport counters (cumulative since process start).

        A service surfaces this however it likes (e.g. a ``GET /v1/metrics/transport`` route or
        a Prometheus scrape) -- the generic base keeps the counters but pushes no metrics.
        """
        with self._seq_lock:
            return {
                "bytes_sent_total": self._bytes_sent_total,
                "messages_sent_total": self._messages_sent_total,
                "send_failures": self._send_failures,
                "messages_sent_by_type": dict(self._messages_sent_by_type),
                "bytes_sent_by_type": dict(self._bytes_sent_by_type),
                "uptime_seconds": time.monotonic() - self._server_start_time,
                "active_connections": len(self._active_connections),
                "pending_connections": len(self._pending_connections),
                "current_seq": self._next_seq - 1,
                "replay_buffer_size": len(self._replay_buffer),
                "replay_buffer_capacity": self._replay_buffer_max_size,
                "messages_chunked_total": self._messages_chunked_total,
                "chunks_emitted_total": self._chunks_emitted_total,
                "max_message_size_bytes": self._max_message_size_bytes,
                "chunk_payload_size_bytes": self._chunk_payload_size_bytes,
                "endpoint_counts": self.endpoint_counts(),
            }

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def close_all(self) -> None:
        """Close all active and pending connections (used during shutdown).

        Holds ``self._lock`` around the set mutations so a concurrent ``connect()`` /
        ``disconnect()`` cannot race with shutdown and corrupt the connection set. The actual
        ``ws.close()`` calls are issued against a snapshot taken under the lock, avoiding
        deadlock risk from re-entering the lock via ``disconnect()`` on exception paths.

        A socket a broadcast has already dropped is in neither set, so it is not closed here, and
        its 1011 close, if still in flight, is neither awaited nor cancelled (:meth:`_drop`).
        """
        async with self._lock:
            snapshot = list(self._active_connections) + list(self._pending_connections)
            self._active_connections.clear()
            self._pending_connections.clear()
            self._connection_meta.clear()
            self._connection_endpoint.clear()
            for bucket in self._endpoint_connections.values():
                bucket.clear()

        for ws in snapshot:
            with contextlib.suppress(Exception):
                await ws.close(code=1001, reason="Server shutting down")
        logger.info("All WebSocket connections closed")
