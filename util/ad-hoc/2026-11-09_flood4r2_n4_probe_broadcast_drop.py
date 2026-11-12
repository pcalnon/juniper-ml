#!/usr/bin/env python3
"""
Probe: what juniper-service-core's ``/ws/training`` does to a socket whose broadcast send fails.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (re-derives defect N-4 on a given tree, and shows the fix's effect)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11:
         "juniper-service-core's broadcast drops a socket whose send fails without closing it");
         juniper-service-core/juniper_service_core/websocket/manager.py,
         juniper-service-core/juniper_service_core/websocket/training_stream.py

Each scenario runs the real ``training_stream_handler`` and ``WebSocketManager`` of the tree named by
``--service-core`` over a real Starlette ``WebSocket`` bound to an in-memory ASGI peer, so Starlette's
own state machine decides what a send or a close does after the server has closed. Nothing touches
the network or the checkout. Usage::

    python3 <this file> --service-core <dir holding juniper_service_core> --model-core <dir holding juniper_model_core>

Prints one JSON object: per scenario, what the client saw and what the manager believes.

Round 2 (2026-11-11). The round-1 key ``second_socket_same_ip_accepted_while_first_open`` was false by
construction on a fixed tree: it stopped counting the first socket as open the moment a close frame was sent to
it. It is replaced by ``second_socket_same_ip_admitted_while_first_handler_running``, which is what the scenario
measures, and ``endpoint_counts`` and the per-IP count are read while both handlers run. Three scenarios were
added for limits the texts state: the frame that completes a receive already in flight when the server closes, a
service's own handler on a socket it registered with ``connect()``, and a close that never completes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import types
from pathlib import Path


class AsgiPeer:
    """The ASGI server's side of one WebSocket: what the app receives, and what it sends."""

    def __init__(self, *, auto_pong: bool = False, hold_close: bool = False) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.inbox.put_nowait({"type": "websocket.connect"})
        self.messages: list[dict] = []
        self.blocked = asyncio.Event()
        self.blocked.set()  # set = sends complete; cleared = a send waits (back-pressure)
        self.close_gate = asyncio.Event()  # cleared = a close never completes until released
        if not hold_close:
            self.close_gate.set()
        self.auto_pong = auto_pong

    async def receive(self) -> dict:
        return await self.inbox.get()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send":
            await self.blocked.wait()
        elif message["type"] == "websocket.close":
            await self.close_gate.wait()
        self.messages.append(message)
        if self.auto_pong and message["type"] == "websocket.send" and json.loads(message["text"]).get("type") == "ping":
            self.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps({"type": "pong"})})

    def frames(self) -> list[dict]:
        return [json.loads(m["text"]) for m in self.messages if m["type"] == "websocket.send"]

    def closes(self) -> list[list]:
        return [[m.get("code"), m.get("reason")] for m in self.messages if m["type"] == "websocket.close"]


def _scope(app: types.SimpleNamespace, ip: str) -> dict:
    return {"type": "websocket", "path": "/ws/training", "headers": [], "client": (ip, 5000), "app": app, "query_string": b""}


async def _wait_for(predicate, limit: float = 5.0) -> bool:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + limit
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.005)
    return predicate()


async def _connect_fresh(app, handler, websocket_cls, ip: str, *, auto_pong: bool = False):
    peer = AsgiPeer(auto_pong=auto_pong)
    peer.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps({"type": "hello"})})  # not a resume: a fresh connect
    ws = websocket_cls(_scope(app, ip), peer.receive, peer.send)
    task = asyncio.create_task(handler(ws))
    return peer, ws, task


async def _slow_client(mod) -> dict:
    """A client too slow for one broadcast: the send times out, and what then?"""
    mgr = mod.WebSocketManager(send_timeout_seconds=0.05, max_connections_per_ip=1)
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=5.0, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=0.05, ws_heartbeat_pong_timeout_sec=1.0)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))
    peer, ws, task = await _connect_fresh(app, mod.training_stream_handler, mod.WebSocket, "10.0.0.1", auto_pong=True)
    await _wait_for(lambda: ws in mgr._active_connections)
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # seq 1: delivered
    peer.blocked.clear()
    await mgr.broadcast({"type": "metrics", "data": {"n": 2}})  # seq 2: the send times out
    peer.blocked.set()
    await asyncio.sleep(0.3)  # several heartbeat intervals
    await mgr.broadcast({"type": "metrics", "data": {"n": 3}})  # seq 3
    pings_after_drop = sum(1 for f in peer.frames() if f.get("type") == "ping")
    # A second socket from the same IP, with a per-IP cap of 1, while the first's handler still runs? The peer never
    # answers a close here, so on a fixed tree the first handler is draining; on main it was never closed at all.
    peer2, ws2, task2 = await _connect_fresh(app, mod.training_stream_handler, mod.WebSocket, "10.0.0.1")
    await _wait_for(lambda: ws2 in mgr._active_connections or task2.done() or bool(peer2.closes()), 1.0)
    result = {
        "seqs_received": [f["seq"] for f in peer.frames() if "seq" in f],
        "close_frames_sent": peer.closes(),
        "handler_still_running": not task.done(),
        "pings_received_meanwhile": pings_after_drop,
        "in_active_set": ws in mgr._active_connections,
        "connection_count": mgr.connection_count,
        "endpoint_counts_training": mgr.endpoint_counts().get("training"),
        "per_ip_count_for_10.0.0.1": mgr._per_ip_counts.get("10.0.0.1", 0),
        "second_socket_same_ip_admitted_while_first_handler_running": (ws2 in mgr._active_connections) and not task.done(),
        "handlers_running_from_one_ip_with_cap_1": sum(1 for t in (task, task2) if not t.done()),
        "second_socket_close_frames": peer2.closes(),
        "send_failures": mgr.transport_stats()["send_failures"],
    }
    # Let the first client acknowledge any close, then end everything.
    peer.inbox.put_nowait({"type": "websocket.disconnect", "code": 1000})
    peer2.inbox.put_nowait({"type": "websocket.disconnect", "code": 1000})
    done, _ = await asyncio.wait({task, task2}, timeout=5)
    result["handler_outcomes"] = [("raised " + type(t.exception()).__name__) if t.exception() else "returned" for t in done]
    return result


async def _late_frame_after_close(mod) -> dict:
    """The server closes a slow socket; a frame the peer already had in flight arrives before its close reply."""
    mgr = mod.WebSocketManager(send_timeout_seconds=0.05)
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=5.0, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))
    peer, ws, task = await _connect_fresh(app, mod.training_stream_handler, mod.WebSocket, "10.0.0.2")
    await _wait_for(lambda: ws in mgr._active_connections)
    peer.blocked.clear()
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # times out
    peer.blocked.set()
    closed = await _wait_for(lambda: bool(peer.closes()), 1.0)
    peer.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps({"type": "pong"})})  # in flight
    await asyncio.sleep(0.05)
    returned_before_disconnect = task.done()
    peer.inbox.put_nowait({"type": "websocket.disconnect", "code": 1011})
    done, _ = await asyncio.wait({task}, timeout=5)
    outcome = ("raised " + type(task.exception()).__name__ + ": " + str(task.exception())) if task in done and task.exception() else ("returned" if task in done else "still running")
    return {"server_closed": closed, "close_frames_sent": peer.closes(), "returned_before_the_disconnect": returned_before_disconnect, "handler_outcome": outcome}


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


def _outcome(task: asyncio.Task) -> str:
    if not task.done():
        return "still running"
    if task.exception() is not None:
        return "raised " + type(task.exception()).__name__ + ": " + str(task.exception())
    return "returned"


async def _frame_in_flight_when_the_server_closes(mod) -> dict:
    """The server closes a slow socket while the handler waits in a receive: is the frame that completes it dispatched?"""
    mgr = mod.WebSocketManager(send_timeout_seconds=0.05)
    lifecycle = _Lifecycle()
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=5.0, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    app = types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=lifecycle, settings=settings))
    peer, ws, task = await _connect_fresh(app, mod.training_stream_handler, mod.WebSocket, "10.0.0.3")
    await _wait_for(lambda: ws in mgr._active_connections)
    await asyncio.sleep(0.05)  # let the handler reach its receive loop
    failures_before = mgr.transport_stats()["send_failures"]
    peer.blocked.clear()
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # times out: dropped (and, on a fixed tree, closed)
    peer.blocked.set()
    closed = await _wait_for(lambda: bool(peer.closes()), 1.0)
    subscribe = {"type": "websocket.receive", "text": json.dumps({"type": "subscribe_metrics", "data": {"max_count": 5}})}
    peer.inbox.put_nowait(subscribe)  # completes the receive already in flight
    await asyncio.sleep(0.05)
    reads_after_first = lifecycle.history_reads
    peer.inbox.put_nowait(subscribe)  # a later frame
    await asyncio.sleep(0.05)
    result = {
        "server_closed": closed,
        "history_reads_after_the_frame_in_flight": reads_after_first,
        "history_reads_after_a_later_frame": lifecycle.history_reads,
        "send_failures_added": mgr.transport_stats()["send_failures"] - failures_before,
        "handler_before_the_disconnect": _outcome(task),
    }
    peer.inbox.put_nowait({"type": "websocket.disconnect", "code": 1011})
    await asyncio.wait({task}, timeout=5)
    result["handler_outcome"] = _outcome(task)
    return result


async def _own_handler_on_a_connect_socket(mod) -> dict:
    """A service's own handler: ``connect()``, then a ``receive_text()`` loop that catches ``WebSocketDisconnect``."""
    mgr = mod.WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer()
    ws = mod.WebSocket(_scope(types.SimpleNamespace(state=types.SimpleNamespace()), "10.0.0.4"), peer.receive, peer.send)

    async def own_handler() -> int:
        received = 0
        await mgr.connect(ws)
        try:
            while True:
                await ws.receive_text()
                received += 1
        except mod.WebSocketDisconnect:
            return received
        finally:
            await mgr.disconnect(ws)

    task = asyncio.create_task(own_handler())
    await _wait_for(lambda: ws in mgr._active_connections)
    await asyncio.sleep(0.05)  # the handler is now waiting in receive_text()
    peer.blocked.clear()
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # times out
    peer.blocked.set()
    closed = await _wait_for(lambda: bool(peer.closes()), 1.0)
    peer.inbox.put_nowait({"type": "websocket.receive", "text": "late"})  # completes the receive in flight
    await asyncio.sleep(0.05)
    after_late_frame = _outcome(task)
    peer.inbox.put_nowait({"type": "websocket.disconnect", "code": 1011})
    await asyncio.wait({task}, timeout=5)
    return {"server_closed": closed, "close_frames_sent": peer.closes(), "handler_after_one_late_frame": after_late_frame, "handler_outcome": _outcome(task)}


async def _a_close_that_never_completes(mod) -> dict:
    """The transport never takes the close: what holds it, and what does ``close_all()`` do about it?"""
    mgr = mod.WebSocketManager(send_timeout_seconds=0.05)
    peer = AsgiPeer(hold_close=True)
    ws = mod.WebSocket(_scope(types.SimpleNamespace(state=types.SimpleNamespace()), "10.0.0.5"), peer.receive, peer.send)
    await mgr.connect(ws)
    peer.blocked.clear()
    loop = asyncio.get_running_loop()
    started = loop.time()
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # the send times out, then the close hangs
    first = round(loop.time() - started, 3)
    started = loop.time()
    await mgr.broadcast({"type": "metrics", "data": {"n": 2}})  # nothing active now
    second = round(loop.time() - started, 3)
    record = getattr(mgr, "_closing", None)
    result = {
        "first_broadcast_seconds_at_a_0.05s_send_timeout": first,
        "next_broadcast_seconds": second,
        "closing_record_after_the_broadcast": None if record is None else len(record),
    }
    await mgr.close_all()
    result["closing_record_after_close_all"] = None if record is None else len(record)
    result["pending_close_tasks_after_close_all"] = None if record is None else sum(1 for t in record.values() if not t.done())
    peer.close_gate.set()
    await asyncio.sleep(0.05)
    result["closing_record_after_the_transport_takes_the_close"] = None if record is None else len(record)
    result["close_frames_sent"] = peer.closes()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--service-core", required=True, type=Path)
    parser.add_argument("--model-core", required=True, type=Path)
    args = parser.parse_args()
    sys.path[:0] = [str(args.service_core.resolve()), str(args.model_core.resolve())]
    from fastapi import WebSocket, WebSocketDisconnect

    from juniper_service_core.websocket import manager as manager_mod
    from juniper_service_core.websocket import training_stream as stream_mod

    mod = types.SimpleNamespace(WebSocketManager=manager_mod.WebSocketManager, training_stream_handler=stream_mod.training_stream_handler, WebSocket=WebSocket, WebSocketDisconnect=WebSocketDisconnect)

    async def run_all() -> dict:
        return {
            "manager_file": manager_mod.__file__,
            "slow_client": await _slow_client(mod),
            "late_frame_after_close": await _late_frame_after_close(mod),
            "frame_in_flight_when_the_server_closes": await _frame_in_flight_when_the_server_closes(mod),
            "own_handler_on_a_connect_socket": await _own_handler_on_a_connect_socket(mod),
            "a_close_that_never_completes": await _a_close_that_never_completes(mod),
        }

    print(json.dumps(asyncio.run(run_all()), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
