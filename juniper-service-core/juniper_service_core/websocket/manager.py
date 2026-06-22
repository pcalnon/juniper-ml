"""WebSocket connection manager for real-time streaming (WS-2 / OUT-11 T2 step 2).

The de-cascored core of cascor's ``api/websocket/manager.py`` (CLEAN per design §5.6: the
broadcast / sequencing / replay-buffer / chunking infra is already model-agnostic). A
thread-safe manager that handles:

- Connection lifecycle (connect / disconnect / pending) + a bounded global and per-IP limit.
- Monotonically increasing sequence numbers on broadcasts.
- A bounded replay buffer for client reconnection (``replay_since``).
- A thread-safe bridge for broadcasting from training threads (``broadcast_from_thread``).
- A configurable send timeout to prevent a slow client from blocking broadcast fan-out.
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
import json
import logging
import threading
import time
import uuid
from collections import deque
from concurrent.futures import CancelledError
from typing import Any

from fastapi import WebSocket

__all__ = ["WebSocketManager", "ws_authenticate", "ReplayOutOfRange", "DEFAULT_WS_ENDPOINTS"]

logger = logging.getLogger("juniper_service_core.websocket")

#: The per-endpoint connection buckets the generic base tracks: the two client-facing channels
#: (``training`` / ``control``) plus the machine-to-machine ``worker`` channel (step-3b
#: ``/ws/workers``). A service can pass a different tuple to :class:`WebSocketManager`; the worker
#: stream registers under :data:`~juniper_service_core.websocket.worker_stream.WORKER_WS_ENDPOINT`
#: (``"worker"``), so that name must be present for the per-endpoint gauge to count worker sockets.
DEFAULT_WS_ENDPOINTS: tuple[str, ...] = ("training", "control", "worker")


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

    async def promote_to_active(self, websocket: WebSocket) -> None:
        """Move a pending connection to active (broadcast-eligible).

        Must be called after the resume handshake completes.
        """
        async with self._lock:
            self._pending_connections.discard(websocket)
            self._active_connections.add(websocket)
            meta = self._connection_meta.get(websocket, {})
            meta.pop("pending", None)
            logger.info("WebSocket promoted to active (%d active, %d pending)", self.connection_count, len(self._pending_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection (from active or pending)."""
        async with self._lock:
            self._active_connections.discard(websocket)
            self._pending_connections.discard(websocket)
            meta = self._connection_meta.pop(websocket, None)
            # Release the per-IP slot reserved at connect time so a clean reconnect does not
            # accrue phantom counts against the cap.
            if meta is not None:
                self._release_per_ip_slot(meta.get("source_ip"))
            logger.info("WebSocket disconnected (%d active, %d pending)", self.connection_count, len(self._pending_connections))

    # ------------------------------------------------------------------
    # Sequencing and replay
    # ------------------------------------------------------------------

    def _assign_seq_and_buffer(self, message: dict) -> dict:
        """Assign a monotonically increasing seq and buffer the message for replay.

        Called on the event-loop thread before broadcast fan-out. Uses ``threading.Lock`` (not
        ``asyncio.Lock``) because it may be invoked from both sync and async contexts. The lock
        is held only for O(1) operations (integer increment + deque append).
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
            # a bisect_right gets O(log n) instead of an O(n) linear scan.
            buffered = list(self._replay_buffer)
            seqs = [msg.get("seq", 0) for msg in buffered]
            idx = bisect.bisect_right(seqs, last_seq)
            return buffered[idx:]

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _maybe_chunk_message(self, message: dict) -> list[dict]:
        """Return ``[message]`` if under threshold, else a list of chunked envelopes.

        Oversized broadcasts (~64 KB) silently tear down WebSocket connections at
        intermediaries. We split here, BEFORE seq assignment, so each chunk gets its own seq +
        replay slot and resume-on-reconnect reorders chunks naturally.

        Chunking is skipped (returns ``[message]``) when:
        - ``max_message_size_bytes`` is 0 (kill-switch for tests),
        - the serialized JSON length is <= the threshold, or
        - the message is already a ``chunked_message`` envelope (no recursion).
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
        logger.info("WebSocket: chunked %s message (%d bytes) into %d chunks (chunk_id=%s)", original_type, len(serialized), total, chunk_id)
        return chunks

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(self, message: dict) -> None:
        """Assign seq and send a message to all active (non-pending) clients.

        Oversized messages are split into ``chunked_message`` envelopes before seq assignment so
        each chunk gets its own seq and replay slot.
        """
        if not self._active_connections:
            return
        for sub_message in self._maybe_chunk_message(message):
            enriched = self._assign_seq_and_buffer(sub_message)
            disconnected = []
            for ws in self._active_connections.copy():
                if not await self._send_json(ws, enriched):
                    disconnected.append(ws)
            for ws in disconnected:
                await self.disconnect(ws)

    def broadcast_from_thread(self, message: dict) -> None:
        """Thread-safe broadcast using ``asyncio.run_coroutine_threadsafe``.

        Called from the training thread to push messages to all WebSocket clients. Adds a done
        callback to log exceptions from the coroutine. A no-op if the event loop has not been
        captured yet (no client has connected) or is closed.
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

        Returns ``True`` only if every chunk was delivered successfully.
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
