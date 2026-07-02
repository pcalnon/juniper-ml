"""Edge-path coverage for :class:`WebSocketManager` (C-4a).

Complements ``test_t2_websocket.py`` (which covers the happy sequencing / replay / broadcast
surface) by driving the endpoint-bookkeeping no-ops, the per-IP accounting corner cases, the
pending-connection limits, the chunking / send-failure / byte-accounting error paths, the
thread-safe broadcast bridge (success + schedule-failure), and ``close_all``.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future

import pytest

from juniper_service_core.websocket.manager import ReplayOutOfRange, WebSocketManager


class FakeWS:
    """A minimal async WebSocket stand-in (accept / send_json / close)."""

    def __init__(self, client: tuple[str, int] | None = ("1.2.3.4", 5000)) -> None:
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


class FailingSendWS(FakeWS):
    """A socket whose ``send_json`` raises -- exercises the generic send-failure branch."""

    async def send_json(self, message: dict) -> None:
        raise RuntimeError("socket gone")


class HangingSendWS(FakeWS):
    """A socket whose ``send_json`` never returns -- exercises the send-timeout branch."""

    def __init__(self, client: tuple[str, int] | None = ("1.2.3.4", 5000)) -> None:
        super().__init__(client)
        self._never = asyncio.Event()

    async def send_json(self, message: dict) -> None:
        await self._never.wait()


class CloseRaisingWS(FakeWS):
    """A socket whose ``close`` raises -- exercises the ``close_all`` suppression branch."""

    async def close(self, code: int = 1000, reason: str = "") -> None:
        raise RuntimeError("close failed")


# ----------------------------------------------------------------------------------------
# Per-endpoint bookkeeping
# ----------------------------------------------------------------------------------------


def test_register_endpoint_unknown_is_noop() -> None:
    mgr = WebSocketManager()
    ws = FakeWS()
    mgr.register_endpoint_connection(ws, "not-a-real-endpoint")
    assert all(ws not in bucket for bucket in mgr._endpoint_connections.values())


def test_unregister_endpoint_unregistered_is_noop() -> None:
    mgr = WebSocketManager()
    mgr.unregister_endpoint_connection(FakeWS())  # never registered -> early return


def test_endpoint_counts_reflect_registration() -> None:
    mgr = WebSocketManager()
    ws = FakeWS()
    mgr.register_endpoint_connection(ws, "training")
    counts = mgr.endpoint_counts()
    assert counts["training"] == 1
    assert counts["control"] == 0


# ----------------------------------------------------------------------------------------
# Per-IP accounting corner cases
# ----------------------------------------------------------------------------------------


def test_source_ip_handles_empty_client_tuple() -> None:
    mgr = WebSocketManager()
    assert mgr._source_ip(FakeWS(client=())) == "unknown"


def test_source_ip_handles_missing_client() -> None:
    mgr = WebSocketManager()
    assert mgr._source_ip(FakeWS(client=None)) == "unknown"


def test_release_per_ip_slot_ignores_falsy_ip() -> None:
    mgr = WebSocketManager()
    mgr._release_per_ip_slot(None)
    mgr._release_per_ip_slot("")


# ----------------------------------------------------------------------------------------
# Pending-connection limits
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_pending_rejects_at_global_limit() -> None:
    mgr = WebSocketManager(max_connections=1)
    assert await mgr.connect(FakeWS(client=("1.1.1.1", 1)))
    late = FakeWS(client=("2.2.2.2", 2))
    assert await mgr.connect_pending(late) is False
    assert late.closed is not None and late.closed[0] == 1013


@pytest.mark.asyncio
async def test_connect_pending_rejects_at_per_ip_limit() -> None:
    mgr = WebSocketManager(max_connections_per_ip=1)
    assert await mgr.connect_pending(FakeWS(client=("9.9.9.9", 1)))
    late = FakeWS(client=("9.9.9.9", 2))
    assert await mgr.connect_pending(late) is False
    assert late.closed is not None and late.closed[0] == 1013


# ----------------------------------------------------------------------------------------
# Replay + chunking edge cases
# ----------------------------------------------------------------------------------------


def test_replay_since_empty_buffer_nonzero_seq_raises() -> None:
    mgr = WebSocketManager()
    with pytest.raises(ReplayOutOfRange):
        mgr.replay_since(5)


def test_maybe_chunk_passes_through_chunked_envelope() -> None:
    mgr = WebSocketManager()
    chunk = {"type": "chunked_message", "data": {"chunk_index": 0}}
    assert mgr._maybe_chunk_message(chunk) == [chunk]


def test_maybe_chunk_unserializable_returns_single() -> None:
    mgr = WebSocketManager()
    circular: dict = {"type": "metrics"}
    circular["self"] = circular
    assert mgr._maybe_chunk_message(circular) == [circular]


# ----------------------------------------------------------------------------------------
# Broadcast / send-path failure handling
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_broadcast_drops_failed_connection() -> None:
    mgr = WebSocketManager()
    good = FakeWS(client=("1.1.1.1", 1))
    bad = FailingSendWS(client=("2.2.2.2", 2))
    assert await mgr.connect(good)
    assert await mgr.connect(bad)
    await mgr.broadcast({"type": "metrics", "data": {"mse": 0.1}})
    assert good in mgr._active_connections
    assert bad not in mgr._active_connections


@pytest.mark.asyncio
async def test_broadcast_without_connections_is_noop() -> None:
    mgr = WebSocketManager()
    await mgr.broadcast({"type": "metrics", "data": {}})  # no active clients -> early return
    assert mgr.current_seq == 0  # no seq assigned


@pytest.mark.asyncio
async def test_send_json_timeout_counts_failure() -> None:
    mgr = WebSocketManager(send_timeout_seconds=0.01)
    assert await mgr._send_json(HangingSendWS(), {"type": "metrics", "data": {}}) is False
    assert mgr.transport_stats()["send_failures"] >= 1


@pytest.mark.asyncio
async def test_send_json_unserializable_payload_accounts_zero_bytes() -> None:
    mgr = WebSocketManager()
    circular: dict = {"type": "metrics"}
    circular["self"] = circular
    assert await mgr._send_json(FakeWS(), circular) is True
    stats = mgr.transport_stats()
    assert stats["messages_sent_total"] == 1
    assert stats["bytes_sent_total"] == 0


@pytest.mark.asyncio
async def test_send_personal_message_returns_false_on_failure() -> None:
    mgr = WebSocketManager()
    assert await mgr.send_personal_message(FailingSendWS(), {"type": "metrics", "data": {}}) is False


# ----------------------------------------------------------------------------------------
# Thread-safe broadcast bridge
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_broadcast_from_thread_schedules_on_loop() -> None:
    mgr = WebSocketManager()
    ws = FakeWS(client=("1.1.1.1", 1))
    assert await mgr.connect(ws)
    mgr.set_event_loop(asyncio.get_running_loop())
    mgr.broadcast_from_thread({"type": "metrics", "data": {"mse": 1.0}})
    await asyncio.sleep(0)
    pending = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if pending:
        await asyncio.gather(*pending)
    assert any(m.get("type") == "metrics" for m in ws.sent)


@pytest.mark.asyncio
async def test_broadcast_from_thread_handles_schedule_failure() -> None:
    mgr = WebSocketManager()

    class _BadLoop:
        def is_closed(self) -> bool:
            return False

    mgr._event_loop = _BadLoop()  # type: ignore[assignment]
    # run_coroutine_threadsafe raises against a non-loop; the coro is closed + logged, no re-raise.
    mgr.broadcast_from_thread({"type": "metrics", "data": {}})


def test_log_broadcast_exception_variants() -> None:
    err = Future()
    err.set_exception(ValueError("boom"))
    WebSocketManager._log_broadcast_exception(err)  # exception present -> logged

    ok = Future()
    ok.set_result(None)
    WebSocketManager._log_broadcast_exception(ok)  # no exception -> quiet

    cancelled = Future()
    cancelled.cancel()
    WebSocketManager._log_broadcast_exception(cancelled)  # CancelledError swallowed


# ----------------------------------------------------------------------------------------
# Shutdown
# ----------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_close_all_closes_active_and_pending() -> None:
    mgr = WebSocketManager()
    active = FakeWS(client=("1.1.1.1", 1))
    pending = FakeWS(client=("2.2.2.2", 2))
    assert await mgr.connect(active)
    assert await mgr.connect_pending(pending)
    await mgr.close_all()
    assert active.closed is not None and active.closed[0] == 1001
    assert pending.closed is not None and pending.closed[0] == 1001
    assert mgr.connection_count == 0


@pytest.mark.asyncio
async def test_close_all_suppresses_close_errors() -> None:
    mgr = WebSocketManager()
    ws = CloseRaisingWS(client=("3.3.3.3", 1))
    assert await mgr.connect(ws)
    await mgr.close_all()  # ws.close raises -> suppressed
    assert mgr.connection_count == 0
