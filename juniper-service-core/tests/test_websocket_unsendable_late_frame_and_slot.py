"""Regression pins: the three WebSocket gaps beside the broadcast drop-and-close.

The Cursor flood-4 disposition record (juniper-ml
``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``, section 8, ruling 23, "WebSocket
gaps beside N-4") left three defects next to the fix that closes a socket a broadcast drops (juniper-ml#2547):

- **An unsendable broadcast.** A message the transport cannot serialise (a ``datetime``, a lone surrogate, a
  circular reference) took a seq and a replay slot, failed on every socket, and so closed every socket 1011;
  every resume across it was then closed 1011 ``Resume replay incomplete``. It is now refused before it takes
  a seq: nothing is sent, no socket is closed, and it is counted and logged without its value. An oversized
  message with the same value is still delivered, as chunks, exactly as before.
- **``/ws/control`` after the server's close.** A frame arriving after the heartbeat's 1011 close ended
  ``control_stream_handler`` with Starlette's ``RuntimeError``, and a command arriving then was executed and
  could not be acknowledged. Now nothing is executed or sent after the close, and the handler drains until
  the disconnect, as ``/ws/training``'s receive loop does.
- **The per-IP slot.** The drop released the socket's connection and per-IP slots at once, while the socket
  was still open, so a second socket from the same address was admitted past ``max_connections_per_ip`` (and
  past ``max_connections``). The slots are now released when the socket's handler disconnects it.

Every test drives the real ``WebSocketManager`` and, where a client's view matters, the real handlers, over a
real Starlette ``WebSocket`` bound to an in-memory ASGI peer whose sends encode text as UTF-8, as a real ASGI
server does. Outcomes depend on the schedule alone: the tests that need a timer (the heartbeat, the idle
timeout) wait for its effect, never for a duration. Tests marked "Control" pin behaviour that must not change
and pass before the fix too.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import threading
import types
from typing import Any

import pytest
from fastapi import WebSocket

from juniper_service_core.websocket.control_stream import control_stream_handler
from juniper_service_core.websocket.manager import WebSocketManager
from juniper_service_core.websocket.training_stream import training_stream_handler

#: The close a broadcast sends to a socket it drops.
DROP_CLOSE = (1011, "Broadcast send failed or timed out")
#: The admission refusals (pre-accept closes; uvicorn answers HTTP 403 for them).
PER_IP_REFUSAL = (1013, "Per-IP connection limit reached")
GLOBAL_REFUSAL = (1013, "Maximum connections reached")

_NO_TIMEOUT = 3600.0
_FRESH = {"type": "hello"}  # any first frame but ``resume``: a fresh connect, with no handshake wait
_WHEN = datetime.datetime(2026, 11, 25, 12, 0, 0)


class AsgiPeer:
    """The ASGI server's side of one WebSocket: an inbox the app reads, and a record of what the app sends.

    A text frame is encoded as UTF-8 before it is recorded, as a real ASGI server does, so a lone surrogate
    fails the send. ``fail_sends`` makes every send raise. ``hold_error`` holds the send of the control ack
    whose error text it names until ``release`` is set (``held`` is set when it is held).
    """

    def __init__(self, *, hold_error: str | None = None) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.inbox.put_nowait({"type": "websocket.connect"})
        self.messages: list[dict] = []
        self.fail_sends = False
        self.receive_calls = 0
        self.hold_error = hold_error
        self.held = asyncio.Event()
        self.release = asyncio.Event()

    async def receive(self) -> dict:
        self.receive_calls += 1
        return await self.inbox.get()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send":
            if self.fail_sends:
                raise RuntimeError("the transport refused the frame")
            message["text"].encode("utf-8")
            if self.hold_error is not None and json.loads(message["text"]).get("data", {}).get("error") == self.hold_error:
                self.held.set()
                await self.release.wait()
        self.messages.append(message)

    def push(self, frame: Any) -> None:
        self.inbox.put_nowait({"type": "websocket.receive", "text": frame if isinstance(frame, str) else json.dumps(frame)})

    def hang_up(self, code: int = 1000) -> None:
        self.inbox.put_nowait({"type": "websocket.disconnect", "code": code})

    def frames(self) -> list[dict]:
        return [json.loads(m["text"]) for m in self.messages if m["type"] == "websocket.send"]

    def seqs(self) -> list[int]:
        return [f["seq"] for f in self.frames() if "seq" in f]

    def closes(self) -> list[tuple[int, str]]:
        return [(m.get("code"), m.get("reason")) for m in self.messages if m["type"] == "websocket.close"]

    def sent_after_the_close(self) -> list[dict]:
        out, closed = [], False
        for m in self.messages:
            if m["type"] == "websocket.close":
                closed = True
            elif closed:
                out.append(json.loads(m["text"]))
        return out


def _socket(peer: AsgiPeer, app: Any = None, ip: str = "10.0.0.1", path: str = "/ws/training") -> WebSocket:
    scope = {"type": "websocket", "path": path, "headers": [], "query_string": b"", "client": (ip, 5000), "app": app}
    return WebSocket(scope, peer.receive, peer.send)


async def _until(predicate: Any, limit: float = 30.0) -> bool:
    """Poll ``predicate`` until it holds (bounded, as a guard against a hang)."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + limit
    while not predicate():
        if loop.time() > deadline:
            return False
        await asyncio.sleep(0.001)
    return True


async def _settle(rounds: int = 100) -> None:
    for _ in range(rounds):
        await asyncio.sleep(0)


def _ended_cleanly(task: asyncio.Task) -> bool:
    return task.done() and not task.cancelled() and task.exception() is None


# ======================================================================================
# (a) A broadcast that no socket could be sent is refused before it takes a seq
# ======================================================================================


def _cyclic() -> dict:
    data: dict = {}
    data["self"] = data
    return data


_UNSENDABLE = [
    pytest.param({"when": _WHEN}, "TypeError", id="datetime"),
    pytest.param({"name": "caf\udce9"}, "UnicodeEncodeError", id="lone-surrogate"),
    pytest.param(_cyclic(), "ValueError", id="circular"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(("data", "error"), _UNSENDABLE)
async def test_an_unsendable_broadcast_is_refused_before_it_takes_a_seq_and_closes_no_socket(data: dict, error: str) -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    peers = [AsgiPeer(), AsgiPeer()]
    sockets = [_socket(p, ip=f"10.0.0.{i}") for i, p in enumerate(peers)]
    for ws in sockets:
        assert await mgr.connect(ws)
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})

    await mgr.broadcast({"type": "metrics", "data": data})

    stats = mgr.transport_stats()
    assert mgr.current_seq == 1  # no seq taken
    assert stats["replay_buffer_size"] == 1  # nothing buffered
    assert stats["unserializable_messages_total"] == 1
    assert stats["send_failures"] == 0  # nothing was attempted on any socket
    assert [p.closes() for p in peers] == [[], []]
    assert all(ws in mgr._active_connections for ws in sockets)
    await mgr.broadcast({"type": "metrics", "data": {"n": 2}})
    assert [p.seqs() for p in peers] == [[1, 2], [1, 2]]  # the stream continues without a gap


@pytest.mark.asyncio
async def test_a_refused_broadcast_is_logged_at_error_without_its_value(caplog: pytest.LogCaptureFixture) -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    with caplog.at_level(logging.DEBUG, logger="juniper_service_core"):
        await mgr.broadcast({"type": "metrics", "data": {"when": _WHEN, "secret": "hunter2"}})

    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert errors == ["Broadcast refused: a 'metrics' message cannot be serialised as the transport sends it (TypeError); it took no seq, and no socket was sent it or closed"]
    logged = "\n".join(r.getMessage() for r in caplog.records)
    for value in ("2026", "hunter2", "datetime"):
        assert value not in logged


@pytest.mark.asyncio
async def test_a_resume_across_a_refused_broadcast_is_continuous() -> None:
    """Before the refusal, the frame was in the replay and every resume across it was closed 1011."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=_NO_TIMEOUT, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # seq 1, buffered with nobody connected
    await mgr.broadcast({"type": "metrics", "data": {"when": _WHEN}})  # refused
    await mgr.broadcast({"type": "metrics", "data": {"n": 2}})  # seq 2

    peer = AsgiPeer()
    peer.push({"type": "resume", "data": {"last_seq": 1, "server_instance_id": mgr.server_instance_id}})
    task = asyncio.create_task(training_stream_handler(_socket(peer, app)))
    assert await _until(lambda: mgr.endpoint_counts()["training"] == 1 or task.done())
    peer.hang_up()
    await asyncio.wait({task}, timeout=30)

    assert _ended_cleanly(task)
    assert [f["type"] for f in peer.frames()][:2] == ["connection_established", "resume_ok"]
    assert peer.seqs() == [2]
    assert peer.closes() == []


@pytest.mark.asyncio
async def test_an_oversized_message_with_the_same_value_is_still_delivered_byte_for_byte() -> None:
    """Control. The chunker serialises with ``default=str``, so its chunks are sendable: this is not refused."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_message_size_bytes=200, chunk_payload_size_bytes=100)
    peer = AsgiPeer()
    assert await mgr.connect(_socket(peer))
    message = {"type": "metrics", "data": {"when": _WHEN, "pad": "x" * 300}}

    await mgr.broadcast(message)

    chunks = [f for f in peer.frames() if f["type"] == "chunked_message"]
    assert len(chunks) == 4
    assert [c["seq"] for c in chunks] == [1, 2, 3, 4]
    assert "".join(c["data"]["payload"] for c in chunks) == json.dumps(message, default=str)
    assert peer.closes() == []
    assert mgr.transport_stats().get("unserializable_messages_total", 0) == 0  # a control: the key is new


@pytest.mark.asyncio
async def test_a_message_whose_own_seq_field_the_broadcast_overwrites_is_still_delivered() -> None:
    """Control. The broadcast replaces ``seq`` (and ``emitted_at_monotonic``) before it sends, so their old values never reach the wire."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    peer = AsgiPeer()
    assert await mgr.connect(_socket(peer))

    await mgr.broadcast({"type": "metrics", "seq": _WHEN, "emitted_at_monotonic": _WHEN, "data": {"n": 1}})

    assert peer.seqs() == [1]
    assert peer.closes() == []


# ======================================================================================
# (b) /ws/control executes and sends nothing after the server's close, and never raises
# ======================================================================================


class RecordingExecutor:
    """Records each command; ``start`` blocks on ``gate`` (set ``started`` first) until the test releases it."""

    commands = ("start", "stop", "pause", "resume", "reset", "set_params")

    def __init__(self) -> None:
        self.executed: list[str] = []
        self.started = threading.Event()
        self.gate = threading.Event()

    def execute(self, command: str, params: dict | None) -> dict:
        self.executed.append(command)
        if command == "start":
            self.started.set()
            self.gate.wait(30)
        return {"ok": True}


def _control_app(executor: RecordingExecutor, *, heartbeat: float, idle_timeout: float = _NO_TIMEOUT) -> types.SimpleNamespace:
    settings = types.SimpleNamespace(
        disable_ws_control_endpoint=False,
        ws_control_cooldown_rejections=10,
        ws_control_cooldown_window_sec=60,
        ws_control_cooldown_block_sec=300,
        ws_control_allowed_origins=None,
        ws_control_rate_limit_per_sec=10,
        ws_control_idle_timeout_sec=idle_timeout,
        ws_heartbeat_interval_sec=heartbeat,
        ws_heartbeat_pong_timeout_sec=heartbeat,
    )
    return types.SimpleNamespace(state=types.SimpleNamespace(settings=settings, command_executor=executor, ws_manager=None))


async def _control(peer: AsgiPeer, executor: RecordingExecutor, **kwargs: Any) -> asyncio.Task:
    return asyncio.create_task(control_stream_handler(_socket(peer, _control_app(executor, **kwargs), path="/ws/control")))


def _heartbeat_closed(peer: AsgiPeer) -> bool:
    return bool(peer.closes()) and peer.closes()[0][0] == 1011


@pytest.mark.asyncio
async def test_a_late_pong_after_the_heartbeat_close_does_not_end_the_control_handler_with_an_error() -> None:
    peer, executor = AsgiPeer(), RecordingExecutor()
    task = await _control(peer, executor, heartbeat=0.01)
    assert await _until(lambda: _heartbeat_closed(peer))

    peer.push({"type": "pong"})  # completes the receive in progress when the server closed
    peer.push({"type": "pong"})
    await _settle()
    assert not task.done()  # draining: no receive_text() after the close, so no RuntimeError

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert _ended_cleanly(task)


@pytest.mark.asyncio
async def test_a_late_command_after_the_heartbeat_close_is_neither_executed_nor_acknowledged() -> None:
    peer, executor = AsgiPeer(), RecordingExecutor()
    task = await _control(peer, executor, heartbeat=0.01)
    assert await _until(lambda: _heartbeat_closed(peer))

    peer.push({"command": "stop", "command_id": "late-1"})
    peer.push({"command": "reset", "command_id": "late-2"})
    await _settle()
    assert not task.done()

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert _ended_cleanly(task)
    assert executor.executed == []
    assert peer.sent_after_the_close() == []


@pytest.mark.asyncio
async def test_a_command_still_running_when_the_heartbeat_closes_is_not_acknowledged() -> None:
    """The command was received before the close, so it runs to completion; its ack would follow the close."""
    peer, executor = AsgiPeer(), RecordingExecutor()
    peer.push({"command": "start", "command_id": "c-1"})
    task = await _control(peer, executor, heartbeat=0.01)
    try:
        assert await _until(executor.started.is_set)
        assert await _until(lambda: _heartbeat_closed(peer))  # the heartbeat closes while start runs
    finally:
        executor.gate.set()
    await _settle()
    assert await _until(lambda: task.done() or peer.receive_calls >= 3)  # connect, the command, then the drain
    assert not task.done()

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert _ended_cleanly(task)
    assert executor.executed == ["start"]
    assert peer.sent_after_the_close() == []


class EndingExecutor(RecordingExecutor):
    """``start`` blocks on ``gate`` (see :class:`RecordingExecutor`), then ends the way ``kind`` names."""

    def __init__(self, kind: str) -> None:
        super().__init__()
        self.kind = kind

    def execute(self, command: str, params: dict | None) -> dict:
        result = super().execute(command, params)
        if self.kind == "rejected":
            raise ValueError("invalid state transition")
        if self.kind == "failed":
            raise KeyError("boom")
        return result


_ENDINGS = [
    pytest.param("success", "Command 'start' completed after the server closed the socket; it was not acknowledged", id="success"),
    pytest.param("rejected", "Command 'start' rejected: invalid state transition", id="rejected"),
    pytest.param("failed", "Command 'start' failed: 'boom'", id="failed"),
    pytest.param("timeout", "Command 'start' timed out after 0.2s", id="timeout"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(("kind", "logged"), _ENDINGS)
async def test_a_command_running_at_the_heartbeat_close_is_not_acknowledged_however_it_ends(kind: str, logged: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """Each of the four acknowledgments after a command runs -- its result, a rejection, an unexpected error, its timeout -- crosses the close."""
    from juniper_service_core.websocket import control_stream

    monkeypatch.setitem(control_stream._COMMAND_TIMEOUTS, "start", 0.2 if kind == "timeout" else 10.0)
    peer, executor = AsgiPeer(), EndingExecutor(kind)
    peer.push({"command": "start", "command_id": "c-1"})
    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        task = await _control(peer, executor, heartbeat=0.01)
        try:
            assert await _until(executor.started.is_set)
            assert await _until(lambda: _heartbeat_closed(peer))  # the heartbeat closes while start runs
            if kind != "timeout":
                executor.gate.set()  # a timeout is the command still running when its wait gives up
            assert await _until(lambda: task.done() or peer.receive_calls >= 3)  # connect, the command, then the drain
            assert not task.done()
        finally:
            executor.gate.set()
        peer.hang_up(1011)
        await asyncio.wait({task}, timeout=30)

    assert _ended_cleanly(task)
    assert peer.sent_after_the_close() == []
    messages = [r.getMessage() for r in caplog.records]
    assert logged in messages
    assert not any("Cannot call" in m for m in messages)


@pytest.mark.asyncio
async def test_the_idle_timeout_after_a_heartbeat_close_does_not_close_again() -> None:
    """The idle timeout fires on a socket the heartbeat has closed: no second close (Starlette would refuse it)."""
    peer, executor = AsgiPeer(), RecordingExecutor()
    task = await _control(peer, executor, heartbeat=0.01, idle_timeout=0.5)
    assert await _until(lambda: _heartbeat_closed(peer))
    receives_at_close = peer.receive_calls

    assert await _until(lambda: task.done() or peer.receive_calls > receives_at_close)  # the timeout fired; the drain reads
    assert not task.done()
    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert _ended_cleanly(task)
    assert len(peer.closes()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("frame", "error"),
    [
        pytest.param("x" * (65536 + 1), "Message too large", id="oversize"),
        pytest.param("not-json", "Invalid JSON", id="malformed-json"),
        pytest.param("[1, 2]", "Invalid control message", id="non-object"),
    ],
)
async def test_a_rejected_frame_whose_ack_crosses_the_heartbeat_close_is_not_closed_twice(frame: str, error: str) -> None:
    """The heartbeat closes while the reject's error ack is on its way: the loop's own close must not follow."""
    peer, executor = AsgiPeer(hold_error=error), RecordingExecutor()
    peer.push(frame)
    task = await _control(peer, executor, heartbeat=0.01)
    try:
        assert await _until(peer.held.is_set)
        assert await _until(lambda: _heartbeat_closed(peer))
    finally:
        peer.release.set()
    await _settle()
    assert not task.done()

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert _ended_cleanly(task)
    assert len(peer.closes()) == 1 and peer.closes()[0][0] == 1011


@pytest.mark.asyncio
async def test_the_control_drain_returns_at_once_when_the_disconnect_was_already_received() -> None:
    """Starlette refuses ``receive()`` once the disconnect has been received, so the drain must not call it then."""
    from juniper_service_core.websocket import control_stream

    drain = control_stream._drain_until_disconnect
    peer = AsgiPeer()
    ws = _socket(peer, path="/ws/control")
    await ws.accept()
    peer.hang_up()
    assert (await ws.receive())["type"] == "websocket.disconnect"
    calls = peer.receive_calls

    await asyncio.wait_for(drain(ws), timeout=30)

    assert peer.receive_calls == calls


@pytest.mark.asyncio
async def test_the_loops_own_close_is_unchanged_when_the_heartbeat_has_not_closed() -> None:
    """Control. An oversize frame on an open socket: the error ack, then the loop's own 1009 close."""
    peer, executor = AsgiPeer(), RecordingExecutor()
    peer.push("x" * (65536 + 1))
    task = await _control(peer, executor, heartbeat=_NO_TIMEOUT)
    await asyncio.wait({task}, timeout=30)

    assert _ended_cleanly(task)
    assert peer.closes() == [(1009, "Message too large")]
    assert peer.frames()[-1]["data"]["error"] == "Message too large"


# ======================================================================================
# (c) A dropped socket keeps its connection and per-IP slots until its handler returns
# ======================================================================================


def _training_app(mgr: WebSocketManager) -> types.SimpleNamespace:
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=_NO_TIMEOUT, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))


async def _serve(mgr: WebSocketManager, peer: AsgiPeer, ip: str) -> asyncio.Task:
    """Run the real ``/ws/training`` handler on a fresh connect; return once it is registered, or has returned (refused)."""
    peer.push(_FRESH)
    ws = _socket(peer, _training_app(mgr), ip)
    task = asyncio.create_task(training_stream_handler(ws))
    assert await _until(lambda: task.done() or ws in mgr._connection_endpoint)
    return task


async def _drop_first(mgr: WebSocketManager, ip: str = "10.0.0.1") -> tuple[AsgiPeer, asyncio.Task]:
    """A socket whose next broadcast send fails: dropped and closed 1011, its handler draining (its peer has not answered)."""
    peer = AsgiPeer()
    task = await _serve(mgr, peer, ip)
    peer.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
    assert peer.closes() == [DROP_CLOSE]
    assert not task.done()
    return peer, task


@pytest.mark.asyncio
async def test_a_dropped_socket_keeps_its_per_ip_slot_until_its_handler_returns() -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections_per_ip=1)
    peer_a, task_a = await _drop_first(mgr)

    peer_b = AsgiPeer()
    task_b = await _serve(mgr, peer_b, "10.0.0.1")  # the same address, while the dropped socket is still open
    assert peer_b.closes() == [PER_IP_REFUSAL]
    assert _ended_cleanly(task_b)
    assert mgr._per_ip_counts == {"10.0.0.1": 1}

    peer_a.hang_up(1011)  # the client answers the close: the old socket is gone
    await asyncio.wait({task_a}, timeout=30)
    assert _ended_cleanly(task_a)
    assert mgr._per_ip_counts == {}

    peer_c = AsgiPeer()
    task_c = await _serve(mgr, peer_c, "10.0.0.1")  # the reconnect is admitted once the old socket is gone
    assert not task_c.done() and peer_c.closes() == []
    peer_c.hang_up()
    await asyncio.wait({task_c}, timeout=30)
    assert _ended_cleanly(task_c)


@pytest.mark.asyncio
async def test_a_dropped_socket_keeps_its_connection_slot_until_its_handler_returns() -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections=1)
    peer_a, task_a = await _drop_first(mgr)

    peer_b = AsgiPeer()
    task_b = await _serve(mgr, peer_b, "10.0.0.2")  # another address: the global cap is full while A is open
    assert peer_b.closes() == [GLOBAL_REFUSAL]
    assert _ended_cleanly(task_b)

    peer_a.hang_up(1011)
    await asyncio.wait({task_a}, timeout=30)
    peer_c = AsgiPeer()
    task_c = await _serve(mgr, peer_c, "10.0.0.2")
    assert not task_c.done() and peer_c.closes() == []
    peer_c.hang_up()
    await asyncio.wait({task_c}, timeout=30)
    assert _ended_cleanly(task_c)


@pytest.mark.asyncio
async def test_a_dropped_socket_registered_with_connect_keeps_its_connection_slot_until_disconnected() -> None:
    """A service's own handler (``connect()``): the slot is released by its ``disconnect()``, not by the drop."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections=1)
    peer_a = AsgiPeer()
    ws_a = _socket(peer_a, ip="10.0.0.1")
    assert await mgr.connect(ws_a)
    peer_a.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
    assert peer_a.closes() == [DROP_CLOSE]

    peer_b = AsgiPeer()
    assert await mgr.connect(_socket(peer_b, ip="10.0.0.2")) is False
    assert peer_b.closes() == [GLOBAL_REFUSAL]

    await mgr.disconnect(ws_a)
    assert await mgr.connect(_socket(AsgiPeer(), ip="10.0.0.2")) is True


@pytest.mark.asyncio
async def test_every_count_agrees_with_what_is_open_while_a_dropped_socket_closes() -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    peer_a, task_a = await _drop_first(mgr)

    stats = mgr.transport_stats()
    assert (stats["active_connections"], stats["pending_connections"], stats["dropped_connections"]) == (0, 0, 1)
    assert mgr.endpoint_counts()["training"] == 1
    assert mgr._per_ip_counts == {"10.0.0.1": 1}
    peer_b = AsgiPeer()
    task_b = await _serve(mgr, peer_b, "10.0.0.2")
    assert peer_b.frames()[0]["data"]["connections"] == 2  # A is still open, and B

    peer_a.hang_up(1011)
    await asyncio.wait({task_a}, timeout=30)
    stats = mgr.transport_stats()
    assert (stats["active_connections"], stats["pending_connections"], stats["dropped_connections"]) == (1, 0, 0)
    assert mgr.endpoint_counts()["training"] == 1
    assert mgr._per_ip_counts == {"10.0.0.2": 1}
    peer_b.hang_up()
    await asyncio.wait({task_b}, timeout=30)
    assert mgr.transport_stats()["dropped_connections"] == 0 and mgr._per_ip_counts == {} and mgr.endpoint_counts()["training"] == 0


@pytest.mark.asyncio
async def test_a_socket_disconnected_before_its_drop_is_not_held() -> None:
    """Control. Its handler disconnected it while the failing send was in flight: the drop must not hold it again."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    sending, proceed = asyncio.Event(), asyncio.Event()

    class GatedFailingPeer(AsgiPeer):
        async def send(self, message: dict) -> None:
            if message["type"] == "websocket.send" and json.loads(message["text"]).get("type") == "metrics":
                sending.set()
                await proceed.wait()
                raise RuntimeError("the transport refused the frame")
            await super().send(message)

    peer = GatedFailingPeer()
    ws = _socket(peer)
    assert await mgr.connect(ws)
    broadcast = asyncio.create_task(mgr.broadcast({"type": "metrics", "data": {"n": 1}}))
    try:
        assert await _until(sending.is_set)
        await mgr.disconnect(ws)  # its handler's disconnect, while the failing send is still in flight
    finally:
        proceed.set()
    await asyncio.wait({broadcast}, timeout=30)

    assert mgr.transport_stats().get("dropped_connections", 0) == 0  # a control: the key is new
    assert mgr._per_ip_counts == {}
    assert mgr.connection_count == 0


@pytest.mark.asyncio
async def test_a_dropped_socket_releases_its_slots_once_however_often_it_is_disconnected() -> None:
    """Control. ``disconnect()`` is idempotent: a second call for the dropped socket must not take the other socket's slot."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections_per_ip=2)
    peer_a, peer_b = AsgiPeer(), AsgiPeer()
    ws_a, ws_b = _socket(peer_a), _socket(peer_b)
    assert await mgr.connect(ws_a) and await mgr.connect(ws_b)
    peer_a.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
    assert peer_a.closes() == [DROP_CLOSE] and peer_b.closes() == []

    await mgr.disconnect(ws_a)
    await mgr.disconnect(ws_a)

    assert mgr._per_ip_counts == {"10.0.0.1": 1}  # ws_b still holds its slot
    assert ws_a not in mgr._connection_meta


@pytest.mark.asyncio
async def test_close_all_forgets_a_dropped_socket() -> None:
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT)
    peer_a, task_a = await _drop_first(mgr)
    assert mgr.transport_stats()["dropped_connections"] == 1

    await mgr.close_all()

    assert mgr.transport_stats()["dropped_connections"] == 0
    assert peer_a.closes() == [DROP_CLOSE]  # not closed a second time
    peer_a.hang_up(1011)
    await asyncio.wait({task_a}, timeout=30)
    assert _ended_cleanly(task_a)


@pytest.mark.asyncio
async def test_close_all_leaves_no_address_charged() -> None:
    """close_all() forgets every socket, so their handlers' disconnect() finds no record to release: no address may stay charged."""
    mgr = WebSocketManager(send_timeout_seconds=_NO_TIMEOUT, max_connections_per_ip=1)
    peer_a, task_a = await _drop_first(mgr, "10.0.0.1")
    peer_b = AsgiPeer()
    task_b = await _serve(mgr, peer_b, "10.0.0.2")

    await mgr.close_all()
    peer_a.hang_up(1011)
    peer_b.hang_up(1001)
    await asyncio.wait({task_a, task_b}, timeout=30)

    assert mgr._per_ip_counts == {}
    for ip in ("10.0.0.1", "10.0.0.2"):
        peer = AsgiPeer()
        task = await _serve(mgr, peer, ip)
        assert not task.done() and peer.closes() == []
        peer.hang_up()
        await asyncio.wait({task}, timeout=30)
