"""
Validator n3's own pytest cases for juniper-cascor's resume-loss fix; copied into a scratch cascor worktree as
src/tests/unit/api/test_n3_validator_extra.py to judge whether a mutant that survives the builder's suite is
equivalent or merely untested.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-cascor fix/ws-resume-losses
"""

import asyncio
import json
import random
import types
from collections.abc import Callable
from typing import List

import pytest
from api.websocket.manager import WebSocketManager
from api.websocket.training_stream import training_stream_handler
from fastapi import WebSocketDisconnect


class Sock:
    _n = 0

    def __init__(self, *, app=None, frames=(), yields: Callable[[], int] = lambda: 0, hook=None):
        Sock._n += 1
        self.name = f"s{Sock._n}"
        self.client = (f"10.{Sock._n // 250}.{Sock._n % 250}.1", 4000 + Sock._n)
        self.headers: dict = {}
        self.app = app
        self.out: List[dict] = []
        self.closes: List[tuple] = []
        self._q: asyncio.Queue = asyncio.Queue()
        for f in frames:
            self._q.put_nowait(f)
        self._yields = yields
        self._hook = hook
        self.serving = asyncio.Event()

    async def accept(self) -> None:
        return None

    async def send_json(self, message: dict) -> None:
        if self._hook is not None:
            await self._hook(self, message)
        for _ in range(self._yields()):
            await asyncio.sleep(0)
        self.out.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closes.append((code, reason))

    async def receive_text(self) -> str:
        if self._q.empty():
            self.serving.set()
        item = await self._q.get()
        if item is None:
            raise WebSocketDisconnect(code=1000)
        return item

    def hang_up(self) -> None:
        self._q.put_nowait(None)

    def seqs(self) -> List[int]:
        return [m["seq"] for m in self.out if "seq" in m]

    def types(self) -> List[str]:
        return [m.get("type") for m in self.out]


def _mgr(**kw) -> WebSocketManager:
    kw.setdefault("send_timeout_seconds", 60.0)
    return WebSocketManager(**kw)


def _app(mgr):
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=60.0, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=0, ws_heartbeat_pong_timeout_sec=60.0)
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, settings=settings, lifecycle=None))


def _resume(mgr, last_seq) -> str:
    return json.dumps({"type": "resume", "data": {"last_seq": last_seq, "server_instance_id": mgr.server_instance_id}})


def _m(tag) -> dict:
    return {"type": "metrics", "data": {"tag": tag}}


async def _serving_or_done(sock: Sock, task) -> None:
    waiter = asyncio.ensure_future(sock.serving.wait())
    try:
        await asyncio.wait({task, waiter}, timeout=30.0, return_when=asyncio.FIRST_COMPLETED)
    finally:
        waiter.cancel()


async def _end(sock: Sock, task) -> None:
    if not task.done():
        sock.hang_up()
    await asyncio.wait_for(task, timeout=30.0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_n3_final_check_with_a_task_queued_on_the_lock_loses_nothing() -> None:
    """A second lock waiter at the final check: releasing and re-taking the lock there would yield."""
    mgr = _mgr()
    obs = Sock()
    assert await mgr.connect(obs)
    s = Sock()
    assert await mgr.connect_pending(s)
    for i in range(3):
        await mgr.broadcast(_m(i))
    for ev in mgr.replay_since(0):
        assert await mgr.send_personal_message(s, ev)
    await mgr._lock.acquire()
    promote = asyncio.create_task(mgr.promote_to_active(s, replayed_through=3))
    await asyncio.sleep(0)
    contender = asyncio.create_task(mgr.connect_pending(Sock()))
    await asyncio.sleep(0)
    mgr._lock.release()
    late = asyncio.create_task(mgr.broadcast(_m("late")))
    assert await promote is True
    await late
    await contender
    assert s.seqs() == [1, 2, 3, 4]


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("seed", range(60))
async def test_n3_concurrent_resumes_with_lock_churn_each_get_every_seq(seed: int) -> None:
    rng = random.Random(seed)
    mgr = _mgr(max_connections=500, max_connections_per_ip=500, max_connections_global=500)
    obs = Sock()
    assert await mgr.connect(obs)
    for i in range(rng.randint(0, 6)):
        await mgr.broadcast(_m(f"pre{i}"))
    resumers = []
    for _ in range(3):
        last = rng.randint(0, mgr.current_seq)
        s = Sock(app=_app(mgr), frames=[_resume(mgr, last)], yields=lambda: rng.randint(0, 3))
        resumers.append((s, last, asyncio.create_task(training_stream_handler(s))))

    async def broadcaster() -> None:
        for i in range(rng.randint(5, 25)):
            for _ in range(rng.randint(0, 3)):
                await asyncio.sleep(0)
            await mgr.broadcast(_m(f"b{i}"))

    async def churn() -> None:
        for _ in range(rng.randint(2, 12)):
            x = Sock()
            for _ in range(rng.randint(0, 2)):
                await asyncio.sleep(0)
            await mgr.connect_pending(x)
            for _ in range(rng.randint(0, 2)):
                await asyncio.sleep(0)
            await mgr.disconnect(x)

    await asyncio.gather(broadcaster(), churn())
    for s, _, task in resumers:
        await _serving_or_done(s, task)
    await mgr.broadcast(_m("final"))
    for s, _, task in resumers:
        await _end(s, task)
    for s, last, _ in resumers:
        assert s.types()[:2] == ["connection_established", "resume_ok"]
        assert s.closes == []
        assert s.seqs() == list(range(last + 1, mgr.current_seq + 1))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_n3_an_eviction_during_a_later_catch_up_pass_closes_without_a_hole() -> None:
    mgr = _mgr(max_replay_buffer_size=4)
    obs = Sock()
    assert await mgr.connect(obs)
    for i in range(2):
        await mgr.broadcast(_m(i))  # seqs 1-2
    phase = {"n": 0}

    async def hook(_s: Sock, msg: dict) -> None:
        if msg.get("seq") == 2 and phase["n"] == 0:  # the replay: makes a catch-up pass necessary
            phase["n"] = 1
            await mgr.broadcast(_m("c1"))  # seq 3
        elif msg.get("seq") == 3 and phase["n"] == 1:  # first catch-up pass: burst past the buffer
            phase["n"] = 2
            for i in range(6):
                await mgr.broadcast(_m(f"burst{i}"))  # seqs 4-9; 4-5 evicted

    s = Sock(app=_app(mgr), frames=[_resume(mgr, 1)], hook=hook)
    task = asyncio.create_task(training_stream_handler(s))
    await _serving_or_done(s, task)
    if not task.done():
        await mgr.broadcast(_m("live"))
    await _end(s, task)
    assert s.seqs() == [2, 3]
    assert s.closes == [(1011, "Resume replay incomplete")]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_n3_nothing_to_replay_but_a_broadcast_during_resume_ok_still_arrives() -> None:
    mgr = _mgr()
    obs = Sock()
    assert await mgr.connect(obs)
    for i in range(3):
        await mgr.broadcast(_m(i))  # seqs 1-3: the client holds all of them

    async def hook(_s: Sock, msg: dict) -> None:
        if msg.get("type") == "resume_ok":
            await mgr.broadcast(_m("during-resume-ok"))  # seq 4, while the socket is pending

    s = Sock(app=_app(mgr), frames=[_resume(mgr, 3)], hook=hook)
    task = asyncio.create_task(training_stream_handler(s))
    await _serving_or_done(s, task)
    await mgr.broadcast(_m("live"))  # seq 5
    await _end(s, task)
    assert s.seqs() == [4, 5]
