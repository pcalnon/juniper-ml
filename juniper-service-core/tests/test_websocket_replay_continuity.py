"""Boundary pins for WebSocket replay continuity and connection accounting.

Existing replay tests ask for a seq far older than the buffer, or for a tail that was never
evicted. They stay green if the continuity check moves by one (`last_seq < oldest - 1`
becomes `<=` or `< oldest - 2`), which either forces a full resync on a client that still
has the message just before the window, or replays across a gap as if nothing was missed.

The same file pins three neighbouring limits the coarser tests do not separate:

* a serialized body whose length equals ``max_message_size_bytes`` is one frame; one byte
  over is chunked, and no chunk payload exceeds ``chunk_payload_size_bytes``;
* a pending resume handshake consumes a global slot, and disconnecting it gives the slot back;
* sockets with no client address share the ``"unknown"`` per-IP bucket, so a hidden address
  is not its own budget.
"""

from __future__ import annotations

import json

import pytest

from juniper_service_core.websocket.manager import ReplayOutOfRange, WebSocketManager


class FakeWS:
    """Minimal socket: accept / send_json / close, with an optional client address."""

    def __init__(self, client: tuple[str, int] | tuple[()] | None = ("1.2.3.4", 5000)) -> None:
        self.client = client
        self.sent: list[dict] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)


def test_empty_replay_buffer_accepts_only_a_client_that_has_seen_nothing() -> None:
    mgr = WebSocketManager()
    assert mgr.replay_since(0) == []
    with pytest.raises(ReplayOutOfRange, match="Buffer empty"):
        mgr.replay_since(1)


def test_replay_at_the_evicted_edge_is_continuous_and_one_before_is_a_gap() -> None:
    mgr = WebSocketManager(max_replay_buffer_size=2)
    for i in range(5):
        mgr._assign_seq_and_buffer({"type": "metrics", "data": {"i": i}})
    # Seqs 1..5 were assigned; the 2-slot buffer retained 4 and 5.
    oldest = 4
    assert [m["seq"] for m in mgr.replay_since(oldest - 1)] == [4, 5]
    assert [m["seq"] for m in mgr.replay_since(oldest)] == [5]
    assert mgr.replay_since(oldest + 1) == []
    with pytest.raises(ReplayOutOfRange, match="older than oldest"):
        mgr.replay_since(oldest - 2)


def test_message_exactly_at_the_size_limit_is_one_frame_and_one_byte_over_is_chunked() -> None:
    limit = 80
    chunk_size = 30
    overhead = len(json.dumps({"type": "metrics", "data": {"blob": ""}}))
    exact = {"type": "metrics", "data": {"blob": "x" * (limit - overhead)}}
    assert len(json.dumps(exact)) == limit
    mgr = WebSocketManager(max_message_size_bytes=limit, chunk_payload_size_bytes=chunk_size)
    assert mgr._maybe_chunk_message(exact) == [exact]

    over = {"type": "metrics", "data": {"blob": "x" * (limit - overhead + 1)}}
    serialized = json.dumps(over)
    assert len(serialized) == limit + 1
    chunks = mgr._maybe_chunk_message(over)
    assert len(chunks) > 1
    assert [c["data"]["chunk_index"] for c in chunks] == list(range(len(chunks)))
    payloads = [c["data"]["payload"] for c in chunks]
    assert all(len(payload) <= chunk_size for payload in payloads)
    assert any(len(payload) == chunk_size for payload in payloads)
    assert "".join(payloads) == serialized
    assert all(c["data"]["original_type"] == "metrics" for c in chunks)


@pytest.mark.asyncio
async def test_pending_handshake_consumes_and_releases_a_global_slot() -> None:
    mgr = WebSocketManager(max_connections=2)
    active = FakeWS(client=("1.1.1.1", 1))
    pending = FakeWS(client=("2.2.2.2", 2))
    assert await mgr.connect(active) is True
    assert await mgr.connect_pending(pending) is True

    blocked = FakeWS(client=("3.3.3.3", 3))
    assert await mgr.connect(blocked) is False
    assert blocked.accepted is False
    assert blocked.closed == (1013, "Maximum connections reached")

    await mgr.disconnect(pending)
    assert await mgr.connect(blocked) is True
    assert blocked.accepted is True


@pytest.mark.asyncio
async def test_sockets_with_no_client_address_share_one_per_ip_bucket() -> None:
    mgr = WebSocketManager(max_connections_per_ip=1, max_connections=10)
    hidden = FakeWS(client=None)
    also_hidden = FakeWS(client=())
    named = FakeWS(client=("8.8.8.8", 9))
    assert await mgr.connect(hidden) is True
    assert await mgr.connect(also_hidden) is False
    assert also_hidden.accepted is False
    assert also_hidden.closed is not None and also_hidden.closed[0] == 1013
    assert await mgr.connect(named) is True
