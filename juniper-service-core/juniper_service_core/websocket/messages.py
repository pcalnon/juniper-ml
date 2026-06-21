"""Standardized WebSocket message builders (WS-2 / OUT-11 T2 step 2).

The de-cascored core of cascor's ``api/websocket/messages.py``. cascor builds every frame
through its ``juniper_cascor_protocol.envelope`` Pydantic schemas; this generic version
constructs the **same wire format** as plain dicts so the base pulls no cascor-protocol
dependency (and stays importable without ``pydantic`` on this path). The envelope is::

    {"type": "<message_type>", "timestamp": <unix_timestamp>, "data": { ... }}

Broadcast messages additionally carry ``"seq"`` (a monotonically increasing sequence number)
and ``"emitted_at_monotonic"`` -- both assigned by
:meth:`~juniper_service_core.websocket.manager.WebSocketManager.broadcast`, not here.

Only the **model-agnostic 7 of cascor's 9 frame builders** are extracted: ``metrics`` /
``state`` / ``topology`` / ``event`` / ``chunked_message`` / ``initial_metrics`` /
``command_response``. cascor's ``cascade_add`` and ``candidate_progress`` frames are
cascade-specific and are intentionally **dropped** (a cascor subclass re-adds them on top of
the generic ``event`` frame); see the design note §5.6.

Pure stdlib -- no third-party import.
"""

from __future__ import annotations

import time
from typing import Any

__all__ = [
    "create_metrics_message",
    "create_state_message",
    "create_topology_message",
    "create_event_message",
    "create_chunked_message",
    "create_initial_metrics_message",
    "create_control_ack_message",
]


def _envelope(
    message_type: str,
    data: dict[str, Any],
    *,
    seq: int | None = None,
    emitted_at_monotonic: float | None = None,
) -> dict[str, Any]:
    """Build the canonical ``{type, timestamp, data}`` envelope, omitting unset seq fields.

    ``seq`` / ``emitted_at_monotonic`` are normally assigned by the manager at broadcast time;
    they are accepted here for parity with cascor's builder signatures (e.g. a caller that
    pre-stamps a personal message). Omitting them when ``None`` matches the pre-migration
    ``model_dump(exclude_none=True)`` wire output.
    """
    message: dict[str, Any] = {"type": message_type, "timestamp": time.time(), "data": data}
    if seq is not None:
        message["seq"] = seq
    if emitted_at_monotonic is not None:
        message["emitted_at_monotonic"] = emitted_at_monotonic
    return message


def create_metrics_message(
    data: dict[str, Any],
    *,
    seq: int | None = None,
    emitted_at_monotonic: float | None = None,
) -> dict[str, Any]:
    """Create a metrics update message."""
    return _envelope("metrics", data, seq=seq, emitted_at_monotonic=emitted_at_monotonic)


def create_state_message(
    data: dict[str, Any],
    *,
    seq: int | None = None,
    emitted_at_monotonic: float | None = None,
) -> dict[str, Any]:
    """Create a training-state update message."""
    return _envelope("state", data, seq=seq, emitted_at_monotonic=emitted_at_monotonic)


def create_topology_message(
    data: dict[str, Any],
    *,
    seq: int | None = None,
    emitted_at_monotonic: float | None = None,
) -> dict[str, Any]:
    """Create a network-topology message (the model-agnostic ``describe_topology()`` payload)."""
    return _envelope("topology", data, seq=seq, emitted_at_monotonic=emitted_at_monotonic)


def create_event_message(
    data: dict[str, Any],
    *,
    seq: int | None = None,
    emitted_at_monotonic: float | None = None,
) -> dict[str, Any]:
    """Create a generic training-event message (the model-core ``TrainingEvent`` carrier).

    A model with a richer vocabulary (cascor's ``cascade_add`` / ``candidate_progress``)
    layers its own frame types on top of this; the generic base only emits the five model-core
    event types as ``event`` payloads.
    """
    return _envelope("event", data, seq=seq, emitted_at_monotonic=emitted_at_monotonic)


def create_chunked_message(
    *,
    chunk_id: str,
    chunk_index: int,
    total_chunks: int,
    original_type: str,
    payload: str,
) -> dict[str, Any]:
    """Build one chunk of a fragmented oversized message.

    Each chunk is itself a normal envelope and gets its own ``seq`` from the manager -- chunks
    of one logical message land on consecutive seqs so the replay buffer reorders them
    naturally on resume.

    Args:
        chunk_id: UUID4 identifying the logical message all chunks belong to.
        chunk_index: 0-based position of this chunk within the message.
        total_chunks: Total number of chunks the logical message was split into.
        original_type: ``type`` field of the pre-chunked message (e.g. ``"topology"``).
        payload: A slice of the JSON-serialized original message as a string. The client
            concatenates payloads in ``chunk_index`` order and parses the result as JSON to
            reconstruct the original envelope.

    Returns:
        Envelope with type ``"chunked_message"``.
    """
    return _envelope(
        "chunked_message",
        {
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "original_type": original_type,
            "payload": payload,
        },
    )


def create_initial_metrics_message(
    metrics: list[Any],
    *,
    current_seq: int | None = None,
) -> dict[str, Any]:
    """Build the ``initial_metrics`` burst sent on a fresh WS connect.

    Carries the N most-recent metrics so a freshly-connected client can paint its time-series
    chart without an immediate REST poll. This is a personal (non-broadcast) message -- it
    carries no ``seq`` of its own, but ``data.current_seq`` reflects the last broadcast seq the
    manager had assigned at send time so the client knows where the live stream picks up.
    """
    return _envelope(
        "initial_metrics",
        {
            "metrics": metrics,
            "count": len(metrics),
            "current_seq": current_seq if current_seq is not None else 0,
        },
    )


def create_control_ack_message(
    command: str,
    status: str,
    data: dict[str, Any] | None = None,
    error: str | None = None,
    *,
    command_id: str | None = None,
    code: str | None = None,
) -> dict[str, Any]:
    """Create a control-command acknowledgment message.

    Note: ``command_response`` messages have **no** ``seq`` field -- the ``/ws/control``
    channel has no replay buffer. Optional keys (``command_id`` / ``result`` / ``error`` /
    ``code``) are included only when set, matching the cascor dict-builder.
    """
    payload: dict[str, Any] = {"command": command, "status": status}
    if command_id is not None:
        payload["command_id"] = command_id
    if data:
        payload["result"] = data
    if error:
        payload["error"] = error
    if code is not None:
        payload["code"] = code
    return _envelope("command_response", payload)
