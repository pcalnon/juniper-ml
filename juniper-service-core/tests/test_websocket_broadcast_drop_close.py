"""Regression pins: a socket a broadcast drops is closed 1011, not left open on a dead stream.

The Cursor flood-4 disposition record (juniper-ml
``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``, section 8, ruling 11)
found that ``WebSocketManager.broadcast`` dropped a socket whose send raised or timed out without
closing it. The socket left the fan-out, but the ``/ws/training`` handler's receive loop and
heartbeat kept it open: the client went on answering pings on a stream nothing was broadcast to,
never told it was missing frames, and the per-IP slot the drop released had a live socket behind
it, so the per-IP cap no longer bounded that client's open sockets. juniper-cascor had fixed its
own copy (its F-CASCOR-004); this is the same fix for the shared implementation.

Every test drives the real ``WebSocketManager`` -- and, where a client's view matters, the real
``training_stream_handler`` -- over a real Starlette ``WebSocket`` bound to an in-memory ASGI peer,
so Starlette's own state machine decides what a send or a close does after a close. The peer can
refuse a send (``RuntimeError``, as a transport refusing the frame; ``OSError``, as a dead one, which
Starlette marks closed), hold sends (back-pressure, so the manager's send timeout fires), and hold
or fail a close. Outcomes depend on the schedule alone; the few tests that need a timer to fire
(the send timeout, the heartbeat) wait for its effect, never for a duration. The bound on the
broadcast's wait for its closes is read off the one ``asyncio.wait`` call the drop makes
(``_record_waits``), not timed.
"""

from __future__ import annotations

import asyncio
import gc
import json
import logging
import types
from typing import Any

import pytest
from fastapi import WebSocket

from juniper_service_core.websocket.manager import WebSocketManager
from juniper_service_core.websocket.training_stream import training_stream_handler

#: The close a broadcast sends to a socket it drops: the wire values a client sees, pinned literally.
DROP_CLOSE = (1011, "Broadcast send failed or timed out")

#: A send timeout no test reaches unless it means to.
_NO_SEND_TIMEOUT = 3600.0


class AsgiPeer:
    """The ASGI server's side of one WebSocket: what the app receives, and what it sends.

    ``fail_with`` is raised by every ``websocket.send`` (only the one carrying ``fail_on_seq`` when
    that is given), after one yield when ``yield_before_failing``. Clearing ``send_gate`` holds every
    send. A close waits on ``close_gate`` (set unless ``gated_close``), then raises ``close_error`` if
    one is given. ``listening`` is set once the app waits on an empty inbox.
    """

    def __init__(
        self,
        *,
        fail_with: BaseException | None = None,
        fail_on_seq: int | None = None,
        yield_before_failing: bool = False,
        gated_close: bool = False,
        close_error: BaseException | None = None,
    ) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.inbox.put_nowait({"type": "websocket.connect"})
        self.messages: list[dict] = []
        self.send_gate = asyncio.Event()
        self.send_gate.set()
        self.close_gate = asyncio.Event()
        if not gated_close:
            self.close_gate.set()
        self.close_started = asyncio.Event()
        self.listening = asyncio.Event()
        self.on_close: Any = None
        self._fail_with = fail_with
        self._fail_on_seq = fail_on_seq
        self._yield_before_failing = yield_before_failing
        self._close_error = close_error

    async def receive(self) -> dict:
        if self.inbox.empty():
            self.listening.set()
        return await self.inbox.get()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send":
            await self.send_gate.wait()
            if self._fail_with is not None and (self._fail_on_seq is None or json.loads(message["text"]).get("seq") == self._fail_on_seq):
                if self._yield_before_failing:
                    await asyncio.sleep(0)
                raise self._fail_with
        elif message["type"] == "websocket.close":
            self.close_started.set()
            if self.on_close is not None:
                self.on_close()
            await self.close_gate.wait()
            if self._close_error is not None:
                raise self._close_error
        self.messages.append(message)

    def push(self, frame: dict) -> None:
        self.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps(frame)})

    def hang_up(self, code: int = 1000) -> None:
        self.inbox.put_nowait({"type": "websocket.disconnect", "code": code})

    def frames(self) -> list[dict]:
        return [json.loads(m["text"]) for m in self.messages if m["type"] == "websocket.send"]

    def seqs(self) -> list[int]:
        return [f["seq"] for f in self.frames() if "seq" in f]

    def closes(self) -> list[tuple[int, str]]:
        return [(m.get("code"), m.get("reason")) for m in self.messages if m["type"] == "websocket.close"]


class SnapshotHoldingPeer(AsgiPeer):
    """An ``AsgiPeer`` whose transport holds the handler's ``initial_status`` frame until released."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.snapshot_started = asyncio.Event()
        self.snapshot_gate = asyncio.Event()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send" and json.loads(message["text"]).get("type") == "initial_status":
            self.snapshot_started.set()
            await self.snapshot_gate.wait()
        await super().send(message)


class CountingWebSocket(WebSocket):
    """Starlette's ``WebSocket``, counting every close attempted on it (one that raises included)."""

    def __init__(self, scope: dict, receive: Any, send: Any) -> None:
        super().__init__(scope, receive, send)
        self.close_calls = 0

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.close_calls += 1
        await super().close(code=code, reason=reason)


class _Lifecycle:
    """What a fresh connect's snapshot and a ``subscribe_metrics`` read, counting history reads."""

    def __init__(self) -> None:
        self.monitor = types.SimpleNamespace(get_state=lambda: {"status": "running"})
        self.history_reads = 0

    def get_status(self) -> dict:
        return {"status": "running"}

    def get_metrics_history(self, count: int) -> list:
        self.history_reads += 1
        return []


def _manager(**kwargs: Any) -> WebSocketManager:
    kwargs.setdefault("send_timeout_seconds", _NO_SEND_TIMEOUT)
    return WebSocketManager(**kwargs)


def _metrics(tag: object) -> dict:
    return {"type": "metrics", "data": {"tag": tag}}


def _app(mgr: WebSocketManager, lifecycle: object | None = None, **settings: Any) -> types.SimpleNamespace:
    values = {"ws_resume_handshake_timeout_s": _NO_SEND_TIMEOUT, "ws_initial_metrics_count": 0, "ws_heartbeat_interval_sec": 3600, "ws_heartbeat_pong_timeout_sec": 3600}
    values.update(settings)
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=lifecycle, settings=types.SimpleNamespace(**values)))


def _open(peer: AsgiPeer, app: types.SimpleNamespace | None = None, ip: str = "10.0.0.1") -> CountingWebSocket:
    scope = {"type": "websocket", "path": "/ws/training", "headers": [], "query_string": b"", "client": (ip, 5000), "app": app}
    return CountingWebSocket(scope, peer.receive, peer.send)


async def _serve(app: types.SimpleNamespace, peer: AsgiPeer, first_frame: dict, ip: str = "10.0.0.1") -> tuple[CountingWebSocket, asyncio.Task]:
    """Run the real handler on a socket whose first frame is ``first_frame``; return once it listens."""
    peer.push(first_frame)
    ws = _open(peer, app, ip)
    task = asyncio.create_task(training_stream_handler(ws))
    listening = asyncio.ensure_future(peer.listening.wait())
    await asyncio.wait({task, listening}, timeout=30, return_when=asyncio.FIRST_COMPLETED)
    listening.cancel()
    assert not task.done(), "the handler returned before reaching its receive loop"
    return ws, task


def _untracked(mgr: WebSocketManager) -> bool:
    """No connection, endpoint-bucket or per-IP accounting is left for any socket."""
    return mgr.connection_count == 0 and mgr.endpoint_counts()["training"] == 0 and mgr._per_ip_counts == {}


_FRESH = {"type": "hello"}  # any frame but ``resume``: a fresh connect, with no wait for the handshake timeout


async def _until(predicate: Any, limit: float = 30.0) -> bool:
    """Poll ``predicate`` until it holds (bounded, as a guard against a hang)."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + limit
    while not predicate():
        if loop.time() > deadline:
            return False
        await asyncio.sleep(0.001)
    return True


def _record_waits(patch: pytest.MonkeyPatch) -> list[tuple[int, float | None, str]]:
    """Record each ``asyncio.wait`` call made while ``patch`` holds: (how many awaited, timeout, return_when)."""
    waits: list[tuple[int, float | None, str]] = []
    real_wait = asyncio.wait

    async def recording_wait(fs: Any, *, timeout: float | None = None, return_when: str = asyncio.ALL_COMPLETED) -> Any:
        waits.append((len(fs), timeout, return_when))
        return await real_wait(fs, timeout=timeout, return_when=return_when)

    patch.setattr(asyncio, "wait", recording_wait)
    return waits


# ======================================================================================
# The manager: a socket a broadcast drops is closed
# ======================================================================================


@pytest.mark.asyncio
async def test_a_socket_whose_broadcast_send_raises_is_closed_1011_and_the_others_are_untouched() -> None:
    mgr = _manager()
    good, bad = AsgiPeer(), AsgiPeer(fail_with=RuntimeError("the transport refused the frame"))
    good_ws, bad_ws = _open(good, ip="10.0.0.1"), _open(bad, ip="10.0.0.2")
    assert await mgr.connect(good_ws)
    assert await mgr.connect(bad_ws)
    active_at_close: list[bool] = []
    bad.on_close = lambda: active_at_close.append(bad_ws in mgr._active_connections)

    await mgr.broadcast(_metrics(0))

    assert bad.closes() == [DROP_CLOSE]
    assert active_at_close == [False]  # forgotten before it was closed
    assert bad_ws not in mgr._active_connections
    assert good.closes() == []
    assert good.seqs() == [1]
    assert good_ws in mgr._active_connections
    assert mgr._closing == {}  # the finished close is released


@pytest.mark.asyncio
async def test_a_socket_whose_broadcast_send_times_out_is_closed_1011(caplog: pytest.LogCaptureFixture) -> None:
    """A slow client: the send times out (the manager's own WARNING), then the socket is closed."""
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer()
    ws = _open(peer)
    assert await mgr.connect(ws)
    peer.send_gate.clear()  # every frame now waits on the transport

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        await asyncio.wait_for(mgr.broadcast(_metrics(0)), timeout=30)

    assert peer.closes() == [DROP_CLOSE]
    assert ws not in mgr._active_connections
    assert mgr.transport_stats()["send_failures"] == 1
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert [w.split(" after ")[0] for w in warnings] == ["WebSocket send timed out"]


@pytest.mark.asyncio
async def test_a_dropped_socket_is_logged_at_info_not_warning(caplog: pytest.LogCaptureFixture) -> None:
    """A send that raised is most often a client gone away: client churn, not a server fault."""
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the client has gone away"))
    assert await mgr.connect(_open(peer))

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        await mgr.broadcast(_metrics(0))

    assert any(r.getMessage() == "Broadcast of seq 1 failed for 1 socket(s): dropped them, and closing 1 with 1011" and r.levelno == logging.INFO for r in caplog.records)
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING] == []


@pytest.mark.asyncio
async def test_a_socket_whose_transport_is_gone_is_dropped_without_a_close_attempt() -> None:
    """Starlette marks a socket closed when a send meets a dead transport (``OSError``): nothing to close."""
    mgr = _manager()
    peer = AsgiPeer(fail_with=ConnectionResetError("connection reset by peer"))
    ws = _open(peer)
    assert await mgr.connect(ws)

    await mgr.broadcast(_metrics(0))

    assert ws not in mgr._active_connections
    assert ws.close_calls == 0
    assert peer.closes() == []


@pytest.mark.asyncio
async def test_a_socket_the_server_already_closed_is_not_closed_again() -> None:
    """Another path closed it first (here, as the heartbeat does); the broadcast only forgets it."""
    mgr = _manager()
    peer = AsgiPeer()
    ws = _open(peer)
    assert await mgr.connect(ws)
    await ws.close(code=1011, reason="Heartbeat timeout: no pong or traffic within 10s")

    await mgr.broadcast(_metrics(0))  # Starlette refuses the send: a close was already sent

    assert ws not in mgr._active_connections
    assert ws.close_calls == 1
    assert peer.closes() == [(1011, "Heartbeat timeout: no pong or traffic within 10s")]


@pytest.mark.asyncio
async def test_a_socket_whose_peer_has_disconnected_is_not_closed() -> None:
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"))
    ws = _open(peer)
    assert await mgr.connect(ws)
    peer.hang_up()
    assert (await ws.receive())["type"] == "websocket.disconnect"  # the peer's disconnect is received

    await mgr.broadcast(_metrics(0))

    assert ws not in mgr._active_connections
    assert ws.close_calls == 0


@pytest.mark.asyncio
async def test_overlapping_broadcasts_that_both_drop_a_socket_close_it_once() -> None:
    """The second drop lands before the first close has run, so only the manager's record stops it."""
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), yield_before_failing=True)
    ws = _open(peer)
    assert await mgr.connect(ws)

    await asyncio.gather(mgr.broadcast(_metrics("a")), mgr.broadcast(_metrics("b")))

    assert ws.close_calls == 1
    assert peer.closes() == [DROP_CLOSE]


@pytest.mark.asyncio
async def test_no_socket_is_closed_before_the_broadcast_has_forgotten_it() -> None:
    """While the drop waits for the manager's lock to forget the socket, its close must not start."""
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"))
    ws = _open(peer)
    assert await mgr.connect(ws)

    await mgr._lock.acquire()
    try:
        task = asyncio.create_task(mgr.broadcast(_metrics(0)))
        for _ in range(100):
            await asyncio.sleep(0)
        assert not task.done()  # the drop waits for the lock
        assert ws in mgr._active_connections
        assert not peer.close_started.is_set()
    finally:
        mgr._lock.release()
    await asyncio.wait({task}, timeout=30)

    assert task.done()
    assert ws not in mgr._active_connections
    assert peer.closes() == [DROP_CLOSE]


@pytest.mark.asyncio
async def test_a_slow_close_holds_the_broadcast_at_most_the_send_timeout_and_is_not_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    """The broadcast's one wait for the close is bounded by exactly the send timeout; the close outlives it."""
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), gated_close=True)
    ws = _open(peer)
    assert await mgr.connect(ws)

    with monkeypatch.context() as patch:
        waits = _record_waits(patch)
        await asyncio.wait_for(mgr.broadcast(_metrics(0)), timeout=30)  # returns with the close in flight

    assert waits == [(1, 0.05, asyncio.ALL_COMPLETED)]  # the bound: one wait, of the send timeout
    assert peer.close_started.is_set()
    assert peer.closes() == []
    closing = mgr._closing[ws]
    assert not closing.done()
    peer.close_gate.set()
    await asyncio.wait({closing}, timeout=30)
    assert closing.done() and not closing.cancelled()
    assert peer.closes() == [DROP_CLOSE]
    assert mgr._closing == {}


@pytest.mark.asyncio
async def test_a_disconnect_while_the_peer_is_still_there_leaves_the_close_in_flight() -> None:
    """Only a peer that has gone makes a pending close pointless; any other disconnect leaves it alone."""
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), gated_close=True)
    ws = _open(peer)
    assert await mgr.connect(ws)
    await asyncio.wait_for(mgr.broadcast(_metrics(0)), timeout=30)  # returns with the close in flight
    closing = mgr._closing[ws]

    await mgr.disconnect(ws)  # the broadcast forgot it already; the peer has not disconnected
    for _ in range(100):
        await asyncio.sleep(0)
    assert not closing.done()

    peer.close_gate.set()
    await asyncio.wait({closing}, timeout=30)
    assert closing.done() and not closing.cancelled()
    assert peer.closes() == [DROP_CLOSE]
    assert mgr._closing == {}


@pytest.mark.asyncio
async def test_a_close_still_pending_when_the_peer_has_gone_is_cancelled_and_released() -> None:
    """A transport that never takes the close frame must not keep the close, and its socket, for good.

    Under uvicorn's ``wsproto`` protocol the close of a client that had stopped reading was still
    pending after that client had left (measured: its ``send`` waits for a writable flag that a full
    write buffer clears). Once the handler has seen the disconnect and disconnects the socket, the
    manager cancels that close.
    """
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), gated_close=True)
    ws, task = await _serve(_app(mgr), peer, _FRESH)
    await asyncio.wait_for(mgr.broadcast(_metrics(0)), timeout=30)  # returns with the close in flight
    closing = mgr._closing[ws]
    assert not closing.done()

    peer.hang_up(1006)  # the connection is lost; the transport never took the close frame
    await asyncio.wait({task}, timeout=30)
    assert task.done() and task.exception() is None
    await asyncio.wait({closing}, timeout=30)

    assert closing.cancelled()
    assert mgr._closing == {}
    assert peer.closes() == []
    assert _untracked(mgr)


@pytest.mark.asyncio
async def test_the_closes_of_one_broadcast_run_concurrently() -> None:
    """Three slow closes: all start before the broadcast's (bounded) wait, not one per wait."""
    mgr = _manager()
    peers = [AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), gated_close=True) for _ in range(3)]
    for i, peer in enumerate(peers):
        assert await mgr.connect(_open(peer, ip=f"10.0.1.{i}"))

    task = asyncio.create_task(mgr.broadcast(_metrics(0)))
    try:
        assert await _until(lambda: all(p.close_started.is_set() for p in peers), limit=5)
        assert not task.done()
    finally:
        for peer in peers:
            peer.close_gate.set()
    await asyncio.wait({task}, timeout=30)

    assert task.done()
    assert [p.closes() for p in peers] == [[DROP_CLOSE]] * 3


@pytest.mark.asyncio
async def test_the_broadcast_waits_once_for_all_its_closes_for_one_send_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Three slow closes: one wait, for all three, bounded by exactly the send timeout (not one per socket)."""
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    peers = [AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), gated_close=True) for _ in range(3)]
    for i, peer in enumerate(peers):
        assert await mgr.connect(_open(peer, ip=f"10.0.1.{i}"))

    with monkeypatch.context() as patch:
        waits = _record_waits(patch)
        await asyncio.wait_for(mgr.broadcast(_metrics(0)), timeout=30)

    assert waits == [(3, 0.05, asyncio.ALL_COMPLETED)]
    assert all(p.close_started.is_set() for p in peers)
    closing = list(mgr._closing.values())
    assert len(closing) == 3
    for peer in peers:
        peer.close_gate.set()
    await asyncio.wait(closing, timeout=30)
    assert [p.closes() for p in peers] == [[DROP_CLOSE]] * 3
    assert mgr._closing == {}


@pytest.mark.asyncio
async def test_a_dropped_sockets_per_ip_slot_is_released_once() -> None:
    """Forgotten by the broadcast, then disconnected again by its own handler: one release, not two.

    Only end states are asserted, so this does not fix *when* the slot is released (at the drop, today).
    """
    mgr = _manager(max_connections_per_ip=2)
    app = _app(mgr)
    bad, good = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), fail_on_seq=1), AsgiPeer()
    _, bad_task = await _serve(app, bad, _FRESH)
    _, good_task = await _serve(app, good, _FRESH)
    assert mgr._per_ip_counts == {"10.0.0.1": 2}

    await mgr.broadcast(_metrics(0))  # seq 1 fails for one of the two sockets from this address
    assert bad.closes() == [DROP_CLOSE]
    bad.hang_up(1011)
    await asyncio.wait({bad_task}, timeout=30)
    assert bad_task.done() and bad_task.exception() is None

    assert mgr._per_ip_counts == {"10.0.0.1": 1}  # the other socket still holds its slot
    good.hang_up()
    await asyncio.wait({good_task}, timeout=30)
    assert good_task.done() and good_task.exception() is None
    assert mgr._per_ip_counts == {}


@pytest.mark.asyncio
async def test_a_close_that_fails_is_retrieved_and_logged_at_debug(caplog: pytest.LogCaptureFixture) -> None:
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), close_error=RuntimeError("the transport refused the close"))
    assert await mgr.connect(_open(peer))

    with caplog.at_level(logging.DEBUG):
        await mgr.broadcast(_metrics(0))
        assert mgr._closing == {}
        gc.collect()  # an unretrieved task exception is reported when the task is collected

    messages = [r.getMessage() for r in caplog.records]
    assert any(m.startswith("Closing a dropped WebSocket failed") for m in messages)
    assert not any("never retrieved" in m for m in messages)


@pytest.mark.asyncio
async def test_a_failed_personal_send_neither_drops_nor_closes_the_socket() -> None:
    """The caller decides; ``/ws/training`` ends a resume that cannot be kept with its own 1011 close."""
    mgr = _manager()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"))
    ws = _open(peer)
    assert await mgr.connect(ws)

    assert await mgr.send_personal_message(ws, _metrics(0)) is False

    assert ws in mgr._active_connections
    assert ws.close_calls == 0


# ======================================================================================
# The handler: the client is told, reconnects and resumes; the handler leaves cleanly
# ======================================================================================


@pytest.mark.asyncio
async def test_a_dropped_client_is_closed_and_a_resume_replays_the_frame_it_missed() -> None:
    mgr = _manager()
    app = _app(mgr)
    peer_a = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"), fail_on_seq=2)
    _, task_a = await _serve(app, peer_a, _FRESH)
    await mgr.broadcast(_metrics(1))  # seq 1: delivered
    await mgr.broadcast(_metrics(2))  # seq 2: the send fails, so the socket is dropped and closed

    assert peer_a.closes() == [DROP_CLOSE]
    peer_a.hang_up(1011)  # the client acknowledges the close
    await asyncio.wait({task_a}, timeout=30)
    assert task_a.done() and task_a.exception() is None

    # The client reconnects and resumes from the last seq it holds.
    peer_b = AsgiPeer()
    _, task_b = await _serve(app, peer_b, {"type": "resume", "data": {"last_seq": 1, "server_instance_id": mgr.server_instance_id}}, ip="10.0.0.1")
    await mgr.broadcast(_metrics(3))
    peer_b.hang_up()
    await asyncio.wait({task_b}, timeout=30)

    assert peer_a.seqs() == [1]
    assert [f.get("type") for f in peer_b.frames()][:2] == ["connection_established", "resume_ok"]
    assert peer_b.seqs() == [2, 3]  # the missed frame, replayed, then the live stream
    assert task_b.exception() is None


@pytest.mark.asyncio
async def test_after_the_managers_close_the_receive_loop_drains_until_the_disconnect() -> None:
    """Frames the peer had in flight are not dispatched, and the handler waits for the disconnect.

    The first frame completes the receive already in progress when the server closed (a pong:
    harmless). Calling ``receive_text()`` again would raise Starlette's ``RuntimeError``; returning
    on the next frame would let the ASGI server drop the transport before the close frame left.
    """
    mgr = _manager()
    lifecycle = _Lifecycle()
    peer = AsgiPeer(fail_with=RuntimeError("the transport refused the frame"))
    _, task = await _serve(_app(mgr, lifecycle), peer, _FRESH)
    await mgr.broadcast(_metrics(0))
    assert peer.closes() == [DROP_CLOSE]

    peer.push({"type": "pong"})
    peer.push({"type": "subscribe_metrics", "data": {"max_count": 5}})
    for _ in range(100):
        await asyncio.sleep(0)
    assert not task.done()  # still draining: the disconnect has not arrived
    assert lifecycle.history_reads == 0  # the subscribe_metrics was drained, not dispatched

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert task.done() and task.exception() is None
    assert _untracked(mgr)


@pytest.mark.asyncio
async def test_a_socket_closed_before_the_receive_loop_starts_is_drained_not_read() -> None:
    """A broadcast fails on the socket while the handler is still sending its initial snapshot.

    No receive is in progress when the server closes, so the loop's first step must be the drain: a
    ``receive_text()`` there would raise Starlette's ``RuntimeError`` and end the handler with it.
    """
    mgr = _manager()
    peer = SnapshotHoldingPeer(fail_with=RuntimeError("the transport refused the frame"), fail_on_seq=1)
    peer.push(_FRESH)
    task = asyncio.create_task(training_stream_handler(_open(peer, _app(mgr, _Lifecycle()))))
    await asyncio.wait_for(peer.snapshot_started.wait(), timeout=30)

    await mgr.broadcast(_metrics(0))  # seq 1 fails: the socket is dropped and closed mid-snapshot
    assert peer.closes() == [DROP_CLOSE]

    peer.snapshot_gate.set()
    for _ in range(100):
        await asyncio.sleep(0)
    assert not task.done()  # draining: it did not call receive_text() on a socket the server closed

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert task.done() and task.exception() is None
    assert _untracked(mgr)


@pytest.mark.asyncio
async def test_a_late_pong_after_the_heartbeat_close_does_not_end_the_handler_with_an_error() -> None:
    """The same drain covers the server's other close: a pong that arrives just after the timeout."""
    mgr = _manager()
    peer = AsgiPeer()
    _, task = await _serve(_app(mgr, ws_heartbeat_interval_sec=0.01, ws_heartbeat_pong_timeout_sec=0.01), peer, _FRESH)
    assert await _until(lambda: bool(peer.closes()))
    assert peer.closes()[0][0] == 1011

    peer.push({"type": "pong"})  # too late: it completes the receive in progress
    peer.push({"type": "pong"})
    for _ in range(100):
        await asyncio.sleep(0)
    assert not task.done()

    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=30)
    assert task.done() and task.exception() is None
