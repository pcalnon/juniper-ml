"""Regression pins: a ``resume_ok`` on ``/ws/training`` means nothing was missed before going live.

The Cursor flood-4 disposition record (juniper-ml
``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``, the
juniper-service-core ``resume_ok`` row of its defect table) found two ways a resumed client could
miss broadcasts while the server answered ``resume_ok``:

* **A broadcast made with no socket active was never numbered.** ``WebSocketManager.broadcast``
  returned before sequencing when no socket was active, so a broadcast made while nobody was
  connected -- including while a sole client was still pending its resume handshake -- got no seq
  and no replay slot. A client that resumed from its last seq was told ``resume_ok`` and had no
  gap to see.
* **A broadcast that landed during the replay reached the resuming client by neither path.** It
  was buffered, but fanned out only to the sockets already active, and the resuming socket was
  promoted only after the replay. The record's validator reproduced it with a yielding send:
  buffered seqs 1-7, the client received 3, 4, 5, 7.

Every test drives the real ``WebSocketManager`` and, where a resume is involved, the real
``training_stream_handler`` with a fake socket -- except one, which repeats the validator's own
driver and calls ``_handle_resume`` directly. A send can suspend (the shape of a send waiting on
transport back-pressure) or run a hook before its frame lands, which is how a broadcast is made to
land *during* a replay send deterministically. The resume tests assert the exact seq list the
client received: every seq after its ``last_seq``, once each, in order -- or, where continuity
cannot be kept, a gap-free prefix and a close, never a hole. The broadcasts here run one at a
time; two that overlap can still interleave their sends to any active socket, and a resume does
not change that.

Every manager is built with a send timeout no test reaches (``_NO_SEND_TIMEOUT``), so an outcome
depends on the schedule alone, never on the wall clock. The one test of the timeout path sets its
own.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import types
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.websocket import training_stream
from juniper_service_core.websocket.manager import ReplayOutOfRange, WebSocketManager
from juniper_service_core.websocket.training_stream import training_stream_handler

#: The close an aborted resume sends: the wire values a client sees, pinned literally.
RESUME_INCOMPLETE = (1011, "Resume replay incomplete")

#: A send timeout no test reaches. With the 0.5 s default, a process stall mid-send (a GC pause,
#: CPU steal on a shared runner) timed a yielding send out and changed a seeded test's outcome.
_NO_SEND_TIMEOUT = 3600.0


class FakeWS:
    """A ``/ws/training`` fake socket.

    ``receive_text`` returns the ``incoming`` frames in order (the first one only once
    ``ready_to_resume`` is set, when one is given). After them it sets ``listening`` -- the
    handler is serving its receive loop -- and blocks until :meth:`hang_up`, then raises
    ``WebSocketDisconnect``.

    ``yields`` is how many times a send suspends before its frame lands: an int, or a callable
    drawn once per send. ``on_send`` runs inside a send, before the frame lands. ``fail_on_seq``
    makes the first send of that seq raise, as a send that times out or meets a dead transport
    does. As on a real socket, a send or a second close after a close raises; ``closed`` keeps the
    first close.
    """

    def __init__(
        self,
        *,
        client: tuple[str, int] = ("1.2.3.4", 5000),
        app: types.SimpleNamespace | None = None,
        incoming: list[str] | None = None,
        ready_to_resume: asyncio.Event | None = None,
        yields: int | Callable[[], int] = 0,
        on_send: SendHook | None = None,
        fail_on_seq: int | None = None,
    ) -> None:
        self.client = client
        self.headers: dict[str, str] = {}
        self.app = app
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None
        self.listening = asyncio.Event()
        self._incoming = list(incoming or [])
        self._ready_to_resume = ready_to_resume
        self._yields = yields
        self._on_send = on_send
        self._fail_on_seq = fail_on_seq
        self._hung_up = asyncio.Event()

    async def accept(self) -> None:
        return None

    async def send_json(self, message: dict) -> None:
        if self._on_send is not None:
            await self._on_send(self, message)
        for _ in range(self._yields() if callable(self._yields) else self._yields):
            await asyncio.sleep(0)
        if self.closed is not None:
            raise RuntimeError("Cannot send once a close message has been sent")
        if self._fail_on_seq is not None and message.get("seq") == self._fail_on_seq:
            self._fail_on_seq = None
            raise RuntimeError("send failed")
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        if self.closed is not None:
            raise RuntimeError("Cannot close once a close message has been sent")
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if self._ready_to_resume is not None:
            await self._ready_to_resume.wait()
            self._ready_to_resume = None
        if self._incoming:
            return self._incoming.pop(0)
        self.listening.set()
        await self._hung_up.wait()
        raise WebSocketDisconnect(code=1000)

    def hang_up(self) -> None:
        self._hung_up.set()

    def seqs(self) -> list[int]:
        return [m["seq"] for m in self.sent if "seq" in m]

    def types(self) -> list[str]:
        return [m.get("type") for m in self.sent]

    def frame(self, frame_type: str) -> dict:
        return next(m for m in self.sent if m.get("type") == frame_type)


SendHook = Callable[[FakeWS, dict], Awaitable[None]]


class _Lifecycle:
    """Just what a fresh connect's snapshot reads: a status and a state."""

    monitor = types.SimpleNamespace(get_state=lambda: {"status": "running"})

    def get_status(self) -> dict:
        return {"status": "running"}

    def get_metrics_history(self, count: int) -> list:
        return []


def _manager(**kwargs: Any) -> WebSocketManager:
    kwargs.setdefault("send_timeout_seconds", _NO_SEND_TIMEOUT)
    return WebSocketManager(**kwargs)


def _metrics(tag: object) -> dict:
    return {"type": "metrics", "data": {"tag": tag}}


def _app(mgr: WebSocketManager, lifecycle: object | None = None) -> types.SimpleNamespace:
    """``app.state`` for the handler: this manager, no auth, quiet heartbeats.

    Every test sends its ``resume`` frame, so the handshake timeout is one no test reaches.
    """
    settings = types.SimpleNamespace(
        ws_resume_handshake_timeout_s=_NO_SEND_TIMEOUT,
        ws_initial_metrics_count=0,
        ws_heartbeat_interval_sec=3600,
        ws_heartbeat_pong_timeout_sec=3600,
    )
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=lifecycle, settings=settings))


def _resume_frame(mgr: WebSocketManager, last_seq: int) -> str:
    return json.dumps({"type": "resume", "data": {"last_seq": last_seq, "server_instance_id": mgr.server_instance_id}})


async def _observer(mgr: WebSocketManager) -> FakeWS:
    """An already-active socket, so broadcasts have somewhere to go on the old code too."""
    other = FakeWS(client=("9.9.9.9", 1))
    assert await mgr.connect(other)
    return other


def _start_resume(mgr: WebSocketManager, last_seq: int, *, lifecycle: object | None = None, **ws_kwargs: Any) -> tuple[FakeWS, asyncio.Task]:
    ws = FakeWS(app=_app(mgr, lifecycle), incoming=[_resume_frame(mgr, last_seq)], **ws_kwargs)
    return ws, asyncio.create_task(training_stream_handler(ws))


async def _settle(task: asyncio.Task, ws: FakeWS) -> None:
    """Run the loop until the handler is serving its receive loop, or has returned."""
    for _ in range(10_000):
        if task.done() or ws.listening.is_set():
            return
        await asyncio.sleep(0)
    raise AssertionError("the handler neither returned nor reached its receive loop")


async def _finish(task: asyncio.Task, ws: FakeWS) -> None:
    """Hang up if the handler is still serving, then await it (bounded, as a guard against a hang)."""
    if not task.done():
        ws.hang_up()
    await asyncio.wait_for(task, timeout=60)


# ======================================================================================
# A broadcast made with no socket active is sequenced and buffered
# ======================================================================================


@pytest.mark.asyncio
async def test_a_broadcast_with_no_socket_connected_is_sequenced_and_buffered() -> None:
    mgr = _manager()
    await mgr.broadcast(_metrics(0))
    await mgr.broadcast({"type": "state", "data": {"status": "running"}})

    assert mgr.current_seq == 2
    assert [m["seq"] for m in mgr.replay_since(0)] == [1, 2]
    stats = mgr.transport_stats()
    assert stats["replay_buffer_size"] == 2
    # Nobody to send to: sequenced and buffered, never sent.
    assert stats["messages_sent_total"] == 0
    assert stats["send_failures"] == 0


@pytest.mark.asyncio
async def test_resume_replays_what_was_broadcast_while_nobody_was_connected() -> None:
    mgr = _manager()
    first = FakeWS(client=("9.9.9.9", 1))
    assert await mgr.connect(first)
    await mgr.broadcast(_metrics(0))  # seq 1: the client holds it
    await mgr.disconnect(first)
    await mgr.broadcast(_metrics(1))  # nobody connected
    await mgr.broadcast(_metrics(2))

    ws, task = _start_resume(mgr, last_seq=1)
    await _settle(task, ws)
    await _finish(task, ws)

    assert ws.types()[:2] == ["connection_established", "resume_ok"]
    assert ws.frame("resume_ok")["data"]["replayed_count"] == 2
    assert ws.seqs() == [2, 3]


@pytest.mark.asyncio
async def test_a_broadcast_during_the_only_clients_pending_handshake_is_replayed() -> None:
    """The socket waiting to send ``resume`` is pending, so it was the case "no socket active"."""
    mgr = _manager()
    first = FakeWS(client=("9.9.9.9", 1))
    assert await mgr.connect(first)
    await mgr.broadcast(_metrics(0))  # seq 1
    await mgr.disconnect(first)

    ready = asyncio.Event()
    ws, task = _start_resume(mgr, last_seq=1, ready_to_resume=ready)
    for _ in range(10):  # let the handler accept the socket as pending and wait for the frame
        await asyncio.sleep(0)
    assert ws in mgr._pending_connections
    await mgr.broadcast(_metrics("while-pending"))  # seq 2: the only socket is pending
    ready.set()
    await _settle(task, ws)
    await _finish(task, ws)

    assert ws.frame("resume_ok")["data"]["replayed_count"] == 1
    assert ws.seqs() == [2]


@pytest.mark.asyncio
async def test_a_disabled_replay_buffer_still_sequences_but_buffers_nothing() -> None:
    mgr = _manager(max_replay_buffer_size=0)
    await mgr.broadcast(_metrics(0))

    assert mgr.current_seq == 1  # the same numbering whether or not a client is connected
    assert mgr.transport_stats()["replay_buffer_size"] == 0
    with pytest.raises(ReplayOutOfRange, match="disabled"):
        mgr.replay_since(0)


@pytest.mark.asyncio
async def test_with_nobody_connected_the_buffer_keeps_its_maxlen_and_an_evicted_resume_is_refused() -> None:
    mgr = _manager(max_replay_buffer_size=3)
    for i in range(5):  # nobody connected: seqs 1-5, the buffer keeps 3-5
        await mgr.broadcast(_metrics(i))

    assert [m["seq"] for m in mgr.replay_since(2)] == [3, 4, 5]
    assert mgr.transport_stats()["replay_buffer_size"] == 3

    # A client that last saw seq 1 missed seq 2, which has left the buffer: refused, not
    # resumed over the gap.
    ws, task = _start_resume(mgr, last_seq=1)
    await _settle(task, ws)
    await _finish(task, ws)
    assert ws.frame("resume_failed")["data"]["reason"] == "out_of_range"
    assert "resume_ok" not in ws.types()


@pytest.mark.asyncio
async def test_a_chunked_broadcast_made_while_nobody_was_connected_is_replayed_whole() -> None:
    mgr = _manager(max_message_size_bytes=200, chunk_payload_size_bytes=64)
    big = {"type": "topology", "data": {"blob": "x" * 1000}}
    await mgr.broadcast(big)
    n_chunks = mgr.current_seq
    assert n_chunks > 1  # one seq, and one replay slot, per chunk

    ws, task = _start_resume(mgr, last_seq=0)
    await _settle(task, ws)
    await _finish(task, ws)

    chunks = [m for m in ws.sent if m.get("type") == "chunked_message"]
    assert [c["seq"] for c in chunks] == list(range(1, n_chunks + 1))
    assert [c["data"]["chunk_index"] for c in chunks] == list(range(n_chunks))
    assert json.loads("".join(c["data"]["payload"] for c in chunks)) == big


@pytest.mark.asyncio
async def test_splitting_a_broadcast_nobody_receives_is_logged_at_debug_not_info(caplog: pytest.LogCaptureFixture) -> None:
    """With nobody to send to, an oversized broadcast's split is DEBUG; with a client, INFO.

    Such a broadcast used to return before it was split, so it logged nothing at all; an INFO line
    per oversized broadcast would be new noise while no dashboard is connected.
    """
    mgr = _manager(max_message_size_bytes=200, chunk_payload_size_bytes=64)
    big = {"type": "topology", "data": {"blob": "z" * 1000}}
    with caplog.at_level(logging.DEBUG, logger="juniper_service_core.websocket"):
        await mgr.broadcast(big)  # nobody connected
        await _observer(mgr)
        await mgr.broadcast(big)  # one client

    splits = [r.levelno for r in caplog.records if "chunked topology message" in r.getMessage()]
    assert splits == [logging.DEBUG, logging.INFO]


# ======================================================================================
# A broadcast landing between the replay snapshot and the activation is delivered
# ======================================================================================


@pytest.mark.asyncio
async def test_a_broadcast_that_lands_while_the_replay_is_being_sent_reaches_the_resuming_client() -> None:
    mgr = _manager()
    other = await _observer(mgr)
    for i in range(5):  # seqs 1-5
        await mgr.broadcast(_metrics(i))

    async def broadcast_mid_replay(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 3:  # the first replayed frame is in flight
            await mgr.broadcast(_metrics("during-replay"))  # seq 6

    ws, task = _start_resume(mgr, last_seq=2, on_send=broadcast_mid_replay)
    await _settle(task, ws)
    assert ws in mgr._active_connections
    await mgr.broadcast(_metrics("live"))  # seq 7
    await _finish(task, ws)

    assert ws.types()[:2] == ["connection_established", "resume_ok"]
    # replayed_count is the snapshot; seq 6 follows it, before the live stream.
    assert ws.frame("resume_ok")["data"]["replayed_count"] == 3
    assert ws.seqs() == [3, 4, 5, 6, 7]
    assert other.seqs() == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.asyncio
async def test_a_broadcast_scheduled_during_a_yielding_replay_send_is_delivered() -> None:
    """The record's validator's own driver: ``_handle_resume`` called directly, then ``promote_to_active``.

    That is the order the handler used before the fix; after it, ``_handle_resume`` has already
    promoted the socket gap-free and the second promotion changes nothing.
    """
    mgr = _manager()
    await _observer(mgr)
    for i in range(5):
        await mgr.broadcast(_metrics(i))
    resuming = FakeWS(client=("2.2.2.2", 2), yields=1)
    assert await mgr.connect_pending(resuming)

    late = asyncio.ensure_future(mgr.broadcast(_metrics("during-replay")))
    msg = {"type": "resume", "data": {"last_seq": 2, "server_instance_id": mgr.server_instance_id}}
    assert await training_stream._handle_resume(resuming, mgr, msg) is True
    await asyncio.gather(late)
    await mgr.promote_to_active(resuming)
    await mgr.broadcast(_metrics("after-promote"))

    assert [m["seq"] for m in mgr.replay_since(0)] == [1, 2, 3, 4, 5, 6, 7]
    assert resuming.seqs() == [3, 4, 5, 6, 7]


@pytest.mark.asyncio
async def test_a_broadcast_while_the_resuming_socket_waits_for_the_manager_lock_is_not_lost() -> None:
    """The last check and the activation must both come after the lock is acquired.

    The socket's last replayed frame takes ``mgr._lock`` (as a concurrent ``connect`` that is
    slow to ``accept()`` holds it), so the activation has to wait; a broadcast lands during that
    wait and the lock is then released.
    """
    mgr = _manager()
    await _observer(mgr)
    for i in range(3):  # seqs 1-3
        await mgr.broadcast(_metrics(i))

    async def broadcast_then_release() -> None:
        await mgr.broadcast(_metrics("while-waiting-for-the-lock"))  # seq 4
        mgr._lock.release()

    background: list[asyncio.Task] = []

    async def take_the_lock_on_the_last_replayed_frame(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 3:
            await mgr._lock.acquire()
            background.append(asyncio.create_task(broadcast_then_release()))

    ws, task = _start_resume(mgr, last_seq=0, on_send=take_the_lock_on_the_last_replayed_frame)
    await _settle(task, ws)
    await asyncio.gather(*background)
    await mgr.broadcast(_metrics("live"))  # seq 5
    await _finish(task, ws)

    assert ws.seqs() == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_a_chunked_broadcast_that_lands_during_the_replay_arrives_whole_and_in_order() -> None:
    mgr = _manager(max_message_size_bytes=200, chunk_payload_size_bytes=64)
    await _observer(mgr)
    for i in range(2):  # seqs 1-2, each one frame
        await mgr.broadcast(_metrics(i))
    big = {"type": "topology", "data": {"blob": "y" * 1000}}

    async def chunked_broadcast_mid_replay(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 1:
            await mgr.broadcast(big)

    ws, task = _start_resume(mgr, last_seq=0, on_send=chunked_broadcast_mid_replay)
    await _settle(task, ws)
    await _finish(task, ws)

    assert ws.seqs() == list(range(1, mgr.current_seq + 1))
    chunks = [m for m in ws.sent if m.get("type") == "chunked_message"]
    assert len(chunks) == mgr.current_seq - 2
    assert json.loads("".join(c["data"]["payload"] for c in chunks)) == big


@pytest.mark.asyncio
async def test_a_broadcast_scheduled_at_the_catch_ups_last_check_reaches_the_socket_live(monkeypatch: pytest.MonkeyPatch) -> None:
    """No ``await`` may separate the catch-up's last check from the activation.

    A broadcast is scheduled at the moment the catch-up finds nothing left to send. It runs at the
    next point the loop is free, which must be after the activation, so the socket is in its
    fan-out. With an ``await`` between the check and the activation it runs first, against an
    active set without the socket, and its seq reaches the socket by neither path.
    """
    mgr = _manager()
    other = await _observer(mgr)
    await mgr.broadcast(_metrics(0))  # seq 1
    ws = FakeWS()
    assert await mgr.connect_pending(ws)

    scheduled: list[asyncio.Future] = []
    replay_since = mgr.replay_since

    def replay_since_then_broadcast(last_seq: int) -> list[dict]:
        missed = replay_since(last_seq)
        if not missed and not scheduled:  # the catch-up's last check
            scheduled.append(asyncio.ensure_future(mgr.broadcast(_metrics("at-the-last-check"))))
        return missed

    monkeypatch.setattr(mgr, "replay_since", replay_since_then_broadcast)
    assert await mgr.promote_to_active(ws, replayed_through=1) is True
    assert scheduled
    await asyncio.gather(*scheduled)

    assert ws.seqs() == [2]
    assert other.seqs() == [1, 2]


@pytest.mark.asyncio
async def test_a_broadcast_queued_on_the_lock_behind_the_catch_ups_last_check_reaches_the_socket_live() -> None:
    """The catch-up's last check and the activation must be one hold of the lock, not two.

    A task queued on the manager's lock behind the catch-up -- as the next ``connect()`` would be --
    gets the lock as soon as the catch-up lets it go. Taking the lock again for the activation then
    waits behind that task, and a broadcast made meanwhile runs against an active set without the
    socket, so its seq reaches the socket by neither path. Two ``async with self._lock`` sections
    have no ``await`` between them, which is why the explicit-await test above cannot see a split.
    """
    mgr = _manager()
    other = await _observer(mgr)
    await mgr.broadcast(_metrics(0))  # seq 1
    ws = FakeWS()
    assert await mgr.connect_pending(ws)

    await mgr._lock.acquire()  # held, as a connect() slow to accept() holds it
    promote = asyncio.ensure_future(mgr.promote_to_active(ws, replayed_through=1))
    await asyncio.sleep(0)  # the catch-up now waits for the lock

    async def broadcast_once_it_has_the_lock() -> None:
        async with mgr._lock:  # queued behind the catch-up
            await mgr.broadcast(_metrics("queued-behind-the-catch-up"))  # seq 2

    queued = asyncio.ensure_future(broadcast_once_it_has_the_lock())
    await asyncio.sleep(0)  # now queued behind the catch-up
    mgr._lock.release()  # first come, first served: the catch-up takes the lock first
    await asyncio.gather(promote, queued)

    assert promote.result() is True
    assert ws.seqs() == [2]
    assert other.seqs() == [1, 2]


@pytest.mark.asyncio
async def test_a_seq_the_catch_up_sends_is_not_sent_to_the_socket_again_live() -> None:
    """No ``await`` may separate a broadcast's seq assignment from its copy of the active set.

    The broadcast is assigned its seq first; the catch-up then finds that seq in the buffer, sends
    it, and activates the socket. The broadcast's recipients must be the sockets active when its
    seq was assigned, which did not include this one. With an ``await`` between the assignment
    and the copy, the activation gets in first and the socket receives the seq twice.
    """
    mgr = _manager()
    other = await _observer(mgr)
    await mgr.broadcast(_metrics(0))  # seq 1
    ws = FakeWS()
    assert await mgr.connect_pending(ws)

    # Tasks start in the order they are created: the broadcast's first step runs before the
    # catch-up's.
    broadcast = asyncio.ensure_future(mgr.broadcast(_metrics("raced")))  # seq 2
    promote = asyncio.ensure_future(mgr.promote_to_active(ws, replayed_through=1))
    await asyncio.gather(broadcast, promote)

    assert promote.result() is True
    assert ws.seqs() == [2]
    assert other.seqs() == [1, 2]


@pytest.mark.asyncio
@pytest.mark.parametrize("seed", range(40))
async def test_resume_interleaved_with_broadcasts_delivers_every_seq_once_in_order(seed: int) -> None:
    """Randomised (seeded) yields on both sides; broadcasts are sequential, the resume concurrent.

    Sequential broadcasts cannot overtake one another, so any hole, duplicate or reordering in
    what the resuming socket receives comes from the resume path.
    """
    rng = random.Random(seed)
    mgr = _manager()
    other = await _observer(mgr)
    for i in range(rng.randint(0, 6)):
        await mgr.broadcast(_metrics(f"before-{i}"))
    last_seq = rng.randint(0, mgr.current_seq)
    ws, task = _start_resume(mgr, last_seq, yields=lambda: rng.randint(0, 3))

    for i in range(rng.randint(1, 12)):
        for _ in range(rng.randint(0, 3)):
            await asyncio.sleep(0)
        await mgr.broadcast(_metrics(f"during-{i}"))
    await _settle(task, ws)
    await mgr.broadcast(_metrics("live"))
    await _finish(task, ws)

    assert ws.seqs() == list(range(last_seq + 1, mgr.current_seq + 1))
    assert other.seqs() == list(range(1, mgr.current_seq + 1))


# ======================================================================================
# Continuity that cannot be kept ends the connection rather than leaving a hole
# ======================================================================================


@pytest.mark.asyncio
async def test_a_resume_whose_catch_up_was_evicted_is_closed_not_promoted_over_the_gap() -> None:
    mgr = _manager(max_replay_buffer_size=4)
    await _observer(mgr)
    for i in range(4):  # seqs 1-4
        await mgr.broadcast(_metrics(i))

    async def burst_mid_replay(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 2:  # first replayed frame in flight
            for i in range(6):  # seqs 5-10; the 4-slot buffer now holds 7-10
                await mgr.broadcast(_metrics(f"burst-{i}"))

    ws, task = _start_resume(mgr, last_seq=1, on_send=burst_mid_replay)
    await _settle(task, ws)
    if ws.listening.is_set():  # promoted: show what it receives next
        await mgr.broadcast(_metrics("live"))
    await _finish(task, ws)

    assert ws.seqs() == [2, 3, 4]  # the stream up to the gap, and nothing after it
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections
    assert ws not in mgr._pending_connections


@pytest.mark.asyncio
async def test_a_replay_frame_that_fails_to_send_ends_the_resume_instead_of_leaving_a_hole() -> None:
    mgr = _manager()
    await _observer(mgr)
    for i in range(4):  # seqs 1-4
        await mgr.broadcast(_metrics(i))

    ws, task = _start_resume(mgr, last_seq=1, fail_on_seq=3)
    await _settle(task, ws)
    if ws.listening.is_set():
        await mgr.broadcast(_metrics("live"))
    await _finish(task, ws)

    assert ws.seqs() == [2]
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections


@pytest.mark.asyncio
async def test_a_catch_up_frame_that_fails_to_send_ends_the_resume_instead_of_leaving_a_hole() -> None:
    mgr = _manager()
    await _observer(mgr)
    for i in range(4):  # seqs 1-4
        await mgr.broadcast(_metrics(i))

    async def broadcast_mid_replay(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 2:
            await mgr.broadcast(_metrics("during-replay"))  # seq 5, sent by the catch-up

    ws, task = _start_resume(mgr, last_seq=1, on_send=broadcast_mid_replay, fail_on_seq=5)
    await _settle(task, ws)
    if ws.listening.is_set():
        await mgr.broadcast(_metrics("live"))
    await _finish(task, ws)

    assert ws.seqs() == [2, 3, 4]
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections


@pytest.mark.asyncio
async def test_a_catch_up_send_that_times_out_ends_the_resume(caplog: pytest.LogCaptureFixture) -> None:
    """The one test of the send-timeout path, so its manager keeps a short timeout of its own.

    A stall can only make this send time out later, never change the outcome: the other sends
    here complete without suspending, so no timer can fire on them. The timeout is the one
    WARNING, the manager's own for a send that did not complete; the resume's end is INFO.
    """
    mgr = WebSocketManager(send_timeout_seconds=0.05)
    await _observer(mgr)
    for i in range(3):  # seqs 1-3
        await mgr.broadcast(_metrics(i))
    never = asyncio.Event()

    async def stall_the_catch_up(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 2:  # the first replayed frame is in flight
            await mgr.broadcast(_metrics("during-replay"))  # seq 4, sent by the catch-up
        elif message.get("seq") == 4:
            await never.wait()  # this send never completes; the manager's timeout ends it

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        ws, task = _start_resume(mgr, last_seq=1, on_send=stall_the_catch_up)
        listening = asyncio.ensure_future(ws.listening.wait())
        await asyncio.wait({task, listening}, timeout=60, return_when=asyncio.FIRST_COMPLETED)
        listening.cancel()
        await _finish(task, ws)

    assert ws.seqs() == [2, 3]
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections
    assert mgr.transport_stats()["send_failures"] == 1
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert [w.split(" after ")[0] for w in warnings] == ["WebSocket send timed out"]


#: Where the client of ``test_a_client_that_hangs_up_mid_resume_ends_it_at_info_not_warning`` goes away.
_HANG_UP_AT: dict[str, Callable[[dict], bool]] = {
    "resume_ok": lambda message: message.get("type") == "resume_ok",
    "replay": lambda message: message.get("seq") == 3,
    "catch_up": lambda message: message.get("seq") == 4,
}


@pytest.mark.asyncio
@pytest.mark.parametrize("hangs_up_at", ["resume_ok", "replay", "catch_up"])
async def test_a_client_that_hangs_up_mid_resume_ends_it_at_info_not_warning(hangs_up_at: str, caplog: pytest.LogCaptureFixture) -> None:
    """A send that fails because the client went away is client churn, not a server fault.

    The client goes away while ``resume_ok``, a replayed frame or a catch-up frame is in flight, and
    its transport refuses every send from then on. The resume ends as for any failed send -- not
    promoted, nothing after the gap, closed 1011 -- and nothing is logged above INFO. A send that
    times out keeps the manager's own WARNING (``test_a_catch_up_send_that_times_out_ends_the_resume``).
    """
    mgr = _manager()
    await _observer(mgr)
    for i in range(3):  # seqs 1-3
        await mgr.broadcast(_metrics(i))
    gone = False

    async def hang_up(_ws: FakeWS, message: dict) -> None:
        nonlocal gone
        if message.get("seq") == 2 and not gone:  # the first replayed frame is in flight
            await mgr.broadcast(_metrics("during-replay"))  # seq 4, sent by the catch-up
        gone = gone or _HANG_UP_AT[hangs_up_at](message)
        if gone:
            raise RuntimeError("the client has gone away")

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        ws, task = _start_resume(mgr, last_seq=1, on_send=hang_up)
        await _settle(task, ws)
        await _finish(task, ws)

    assert ws.seqs() == {"resume_ok": [], "replay": [2], "catch_up": [2, 3]}[hangs_up_at]
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections
    assert ws not in mgr._pending_connections
    assert any(r.getMessage().startswith("Resume aborted after resume_ok") for r in caplog.records)
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING] == []


class _ManagerWith071Promote(WebSocketManager):
    """A subclass that overrides ``promote_to_active`` with 0.7.1's signature (no ``replayed_through``)."""

    async def promote_to_active(self, websocket):  # type: ignore[override]
        await super().promote_to_active(websocket)


@pytest.mark.asyncio
async def test_a_manager_that_raises_after_resume_ok_closes_the_socket_instead_of_sending_a_snapshot() -> None:
    """After ``resume_ok`` an exception must end the resume, not turn it into a fresh connect.

    The 0.7.1-signature override raises TypeError on ``replayed_through``. Treated as a handshake
    error, that became a fresh connect: the socket was promoted with no catch-up, and
    ``initial_status`` followed ``resume_ok`` and the replay.
    """
    mgr = _ManagerWith071Promote(send_timeout_seconds=_NO_SEND_TIMEOUT)
    await _observer(mgr)
    for i in range(3):  # seqs 1-3
        await mgr.broadcast(_metrics(i))

    ws, task = _start_resume(mgr, last_seq=1, lifecycle=_Lifecycle())
    await _settle(task, ws)
    await _finish(task, ws)

    assert ws.types() == ["connection_established", "resume_ok", "metrics", "metrics"]
    assert ws.seqs() == [2, 3]
    assert ws.closed == RESUME_INCOMPLETE
    assert ws not in mgr._active_connections


@pytest.mark.asyncio
async def test_a_shutdown_during_the_catch_up_ends_the_resume_without_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    """``close_all`` closes the socket 1001 while the catch-up is sending: a normal shutdown.

    The resume ends, the socket is not resurrected, and nothing is logged above INFO.
    """
    mgr = _manager()
    await _observer(mgr)
    for i in range(3):  # seqs 1-3
        await mgr.broadcast(_metrics(i))

    async def shut_down_mid_catch_up(_ws: FakeWS, message: dict) -> None:
        if message.get("seq") == 2:  # the first replayed frame is in flight
            await mgr.broadcast(_metrics("during-replay"))  # seq 4, sent by the catch-up
        elif message.get("seq") == 4:  # the catch-up's frame is in flight
            await mgr.close_all()  # the socket then refuses the frame

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        ws, task = _start_resume(mgr, last_seq=1, on_send=shut_down_mid_catch_up)
        await _settle(task, ws)
        await _finish(task, ws)

    assert ws.seqs() == [2, 3]
    assert ws.closed == (1001, "Server shutting down")
    assert ws not in mgr._active_connections
    assert ws not in mgr._pending_connections
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING] == []


# ======================================================================================
# promote_to_active(replayed_through=...) -- the manager-side contract
# ======================================================================================


@pytest.mark.asyncio
async def test_promote_without_a_cursor_is_the_unconditional_promotion_it_was() -> None:
    mgr = _manager()
    ws = FakeWS()
    assert await mgr.connect_pending(ws)
    await mgr.broadcast(_metrics(0))  # seq 1, while pending: not delivered by this call

    assert await mgr.promote_to_active(ws) is True
    assert ws in mgr._active_connections
    assert ws not in mgr._pending_connections
    assert ws.seqs() == []


@pytest.mark.asyncio
async def test_promote_with_a_cursor_leaves_an_already_active_socket_alone() -> None:
    mgr = _manager()
    ws = FakeWS()
    assert await mgr.connect(ws)
    await mgr.broadcast(_metrics(0))  # seq 1, delivered live
    sent_before = list(ws.sent)

    assert await mgr.promote_to_active(ws, replayed_through=0) is True
    assert ws.sent == sent_before  # no catch-up copy of seq 1


@pytest.mark.asyncio
async def test_promote_with_a_cursor_does_not_resurrect_a_socket_disconnected_during_the_catch_up(caplog: pytest.LogCaptureFixture) -> None:
    mgr = _manager()

    async def disconnect_mid_catch_up(sock: FakeWS, message: dict) -> None:
        if message.get("seq") == 1:
            await mgr.disconnect(sock)

    ws = FakeWS(on_send=disconnect_mid_catch_up)
    assert await mgr.connect_pending(ws)
    await mgr.broadcast(_metrics(0))  # seq 1
    await mgr.broadcast(_metrics(1))  # seq 2

    with caplog.at_level(logging.INFO, logger="juniper_service_core"):
        assert await mgr.promote_to_active(ws, replayed_through=0) is False
    assert ws not in mgr._active_connections
    assert ws not in mgr._pending_connections
    # A socket that went away is not a failure of the catch-up: reported at INFO, not WARNING.
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING] == []


@pytest.mark.asyncio
async def test_promote_with_a_negative_cursor_delivers_from_the_first_seq() -> None:
    """Seqs start at 1, so a cursor below 0 holds no more than 0 does -- it is not a gap."""
    mgr = _manager()
    ws = FakeWS()
    assert await mgr.connect_pending(ws)
    await mgr.broadcast(_metrics(0))  # seq 1, while the only socket is pending

    assert await mgr.promote_to_active(ws, replayed_through=-5) is True
    assert ws in mgr._active_connections
    assert ws.seqs() == [1]


@pytest.mark.asyncio
async def test_promote_with_a_cursor_on_an_empty_buffer_activates() -> None:
    mgr = _manager()
    ws = FakeWS()
    assert await mgr.connect_pending(ws)

    assert await mgr.promote_to_active(ws, replayed_through=0) is True
    assert ws in mgr._active_connections


@pytest.mark.asyncio
async def test_the_catch_up_sends_a_buffered_frame_exactly_as_the_live_fan_out_did() -> None:
    """A broadcast at the size limit goes live as one frame, though its enriched copy is over it.

    The catch-up must send the buffered frame as the live fan-out did -- whole, with its top-level
    seq -- not size the enriched copy again and split it into chunks that carry no seq.
    """
    limit = 2_000
    mgr = _manager(max_message_size_bytes=limit, chunk_payload_size_bytes=500)
    other = await _observer(mgr)
    ws = FakeWS()
    assert await mgr.connect_pending(ws)
    at_limit: dict = {"type": "topology", "data": {"blob": ""}}
    at_limit["data"]["blob"] = "x" * (limit - len(json.dumps(at_limit)))
    assert len(json.dumps(at_limit)) == limit  # the limit is inclusive: not split
    await mgr.broadcast(at_limit)  # seq 1: one frame to the observer, and buffered

    assert await mgr.promote_to_active(ws, replayed_through=0) is True
    live = [m for m in other.sent if m.get("type") == "topology"]
    assert [m["seq"] for m in live] == [1]
    assert ws.sent[1:] == live
    assert mgr.transport_stats()["messages_chunked_total"] == 0


@pytest.mark.asyncio
async def test_replay_since_returns_exactly_the_tail_after_every_cut_point() -> None:
    """``replay_since`` copies only the tail after the cut: pinned at every cut the buffer allows."""
    mgr = _manager(max_replay_buffer_size=5)
    for i in range(8):  # seqs 1-8; the buffer keeps 4-8
        await mgr.broadcast(_metrics(i))

    for last_seq in range(3, 11):  # oldest - 1 through two past the newest
        assert [m["seq"] for m in mgr.replay_since(last_seq)] == list(range(last_seq + 1, 9)), last_seq
    with pytest.raises(ReplayOutOfRange):
        mgr.replay_since(2)
