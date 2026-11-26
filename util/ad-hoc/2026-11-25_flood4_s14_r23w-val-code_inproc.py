"""
Code lens in-process probe for ruling 23's fix: paths the wire cells do not reach, run against main or the fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Which juniper_service_core runs is whatever this interpreter imports (PYTHONPATH picks the tree); the JSON records
each module's path and sha256. A real Starlette WebSocket over an in-memory ASGI peer that encodes text as UTF-8.

Cases:
  ctl_error_ack_after_close_<kind>  /ws/control: the heartbeat closes while a command runs, and the command then
                                    raises ValueError / times out / raises an unexpected error: does the handler raise?
  drop_then_handler_raises          /ws/training: a dropped socket's handler ends with an exception: are the slots freed?
  overlapping_drops                 two broadcasts in flight both fail on one socket: slots held once, released once?
  close_all_per_ip                  close_all() with one active and one dropped socket, then both handlers return: what
                                    is left in the per-IP map, and is a new socket from those addresses admitted?
  connect_handler_never_disconnects a socket registered with connect() is dropped and nobody calls disconnect(): slots?

Usage:
  python <this file> --out OUT.json
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import threading
import time
import types


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:12]


class Peer:
    def __init__(self) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.inbox.put_nowait({"type": "websocket.connect"})
        self.messages: list[dict] = []
        self.fail_sends = False
        self.hold_sends: asyncio.Event | None = None
        self.sending = asyncio.Event()

    async def receive(self) -> dict:
        return await self.inbox.get()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send":
            if self.hold_sends is not None and json.loads(message["text"]).get("type") == "metrics":
                self.sending.set()
                await self.hold_sends.wait()
            if self.fail_sends:
                raise RuntimeError("the transport refused the frame")
            message["text"].encode("utf-8")
        self.messages.append(message)

    def push(self, obj) -> None:
        self.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps(obj)})

    def hang_up(self, code: int = 1000) -> None:
        self.inbox.put_nowait({"type": "websocket.disconnect", "code": code})

    def closes(self) -> list:
        return [(m.get("code"), m.get("reason")) for m in self.messages if m["type"] == "websocket.close"]

    def sent_after_close(self) -> list:
        out, closed = [], False
        for m in self.messages:
            if m["type"] == "websocket.close":
                closed = True
            elif closed:
                out.append(m.get("text"))
        return out


def socket_for(peer: Peer, app, ip: str, path: str):
    from fastapi import WebSocket

    scope = {"type": "websocket", "path": path, "headers": [], "query_string": b"", "client": (ip, 5000), "app": app}
    return WebSocket(scope, peer.receive, peer.send)


async def until(pred, limit: float = 20.0) -> bool:
    deadline = time.monotonic() + limit
    while not pred():
        if time.monotonic() > deadline:
            return False
        await asyncio.sleep(0.002)
    return True


def outcome(task: asyncio.Task) -> str:
    if not task.done():
        return "running"
    if task.cancelled():
        return "cancelled"
    exc = task.exception()
    return "returned" if exc is None else f"raised {type(exc).__name__}: {exc}"


class Exec:
    commands = ("start", "stop", "pause", "resume", "reset", "set_params")

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.started = threading.Event()
        self.gate = threading.Event()
        self.executed: list[str] = []

    def execute(self, command, params):  # noqa: ARG002 - the executor contract
        self.executed.append(command)
        self.started.set()
        self.gate.wait(20)
        if self.kind == "value_error":
            raise ValueError("invalid state transition")
        if self.kind == "unexpected":
            raise KeyError("boom")
        if self.kind == "timeout":
            time.sleep(0.6)
        return {"ok": True}


async def ctl_error_ack_after_close(kind: str) -> dict:
    from juniper_service_core.websocket import control_stream

    saved = dict(control_stream._COMMAND_TIMEOUTS)
    control_stream._COMMAND_TIMEOUTS["start"] = 0.4 if kind == "timeout" else 10.0
    try:
        executor = Exec(kind)
        settings = types.SimpleNamespace(disable_ws_control_endpoint=False, ws_control_cooldown_rejections=10, ws_control_cooldown_window_sec=60, ws_control_cooldown_block_sec=300, ws_control_allowed_origins=None, ws_control_rate_limit_per_sec=10, ws_control_idle_timeout_sec=3600, ws_heartbeat_interval_sec=0.02, ws_heartbeat_pong_timeout_sec=0.02)
        app = types.SimpleNamespace(state=types.SimpleNamespace(settings=settings, command_executor=executor, ws_manager=None))
        peer = Peer()
        peer.push({"command": "start", "command_id": "c-1"})
        task = asyncio.create_task(control_stream.control_stream_handler(socket_for(peer, app, "10.0.0.9", "/ws/control")))
        await until(executor.started.is_set)
        await until(lambda: bool(peer.closes()))
        executor.gate.set()
        await until(lambda: task.done(), 3.0)
        early = outcome(task)
        peer.hang_up(1011)
        await asyncio.wait({task}, timeout=10)
        return {"case": f"ctl_error_ack_after_close_{kind}", "closes": peer.closes(), "outcome_before_hangup": early, "final_outcome": outcome(task), "sent_after_close": peer.sent_after_close(), "executed": executor.executed}
    finally:
        control_stream._COMMAND_TIMEOUTS.clear()
        control_stream._COMMAND_TIMEOUTS.update(saved)


def training_app(mgr):
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=3600, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))


def counts(mgr) -> dict:
    st = mgr.transport_stats()
    return {"active": st["active_connections"], "pending": st["pending_connections"], "dropped": st.get("dropped_connections"), "per_ip": dict(mgr._per_ip_counts), "endpoint_training": mgr.endpoint_counts().get("training"), "meta": len(mgr._connection_meta)}


async def serve(mgr, peer, ip):
    from juniper_service_core.websocket import training_stream

    peer.push({"type": "hello"})
    ws = socket_for(peer, training_app(mgr), ip, "/ws/training")
    task = asyncio.create_task(training_stream.training_stream_handler(ws))
    await until(lambda: task.done() or ws in mgr._connection_endpoint)
    return ws, task


async def drop_then_handler_raises() -> dict:
    from juniper_service_core.websocket import manager, training_stream

    mgr = manager.WebSocketManager(send_timeout_seconds=3600, max_connections_per_ip=1, max_connections=1)
    original = training_stream._recv_pong_loop
    boom = asyncio.Event()

    async def raising_loop(websocket, pong_received, **kwargs):  # noqa: ARG001 - the replaced signature
        await boom.wait()
        raise RuntimeError("handler failure after the drop")

    training_stream._recv_pong_loop = raising_loop
    try:
        peer = Peer()
        task = (await serve(mgr, peer, "10.0.0.1"))[1]
        peer.fail_sends = True
        await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
        at_drop = counts(mgr)
        boom.set()
        await asyncio.wait({task}, timeout=10)
        after = counts(mgr)
        peer2 = Peer()
        task2 = (await serve(mgr, peer2, "10.0.0.1"))[1]
        admitted = not task2.done() and not peer2.closes()
        peer2.hang_up()
        await asyncio.wait({task2}, timeout=10)
        return {"case": "drop_then_handler_raises", "closes": peer.closes(), "at_drop": at_drop, "handler": outcome(task), "after_handler": after, "next_socket_admitted": admitted}
    finally:
        training_stream._recv_pong_loop = original


async def overlapping_drops() -> dict:
    from juniper_service_core.websocket import manager

    mgr = manager.WebSocketManager(send_timeout_seconds=3600, max_connections_per_ip=2)
    pa, pb = Peer(), Peer()
    ta = (await serve(mgr, pa, "10.0.0.1"))[1]
    tb = (await serve(mgr, pb, "10.0.0.1"))[1]
    pa.hold_sends = asyncio.Event()
    pa.fail_sends = True
    b1 = asyncio.create_task(mgr.broadcast({"type": "metrics", "data": {"n": 1}}))
    await until(pa.sending.is_set)
    pa.sending.clear()
    b2 = asyncio.create_task(mgr.broadcast({"type": "metrics", "data": {"n": 2}}))
    await asyncio.sleep(0.01)
    pa.hold_sends.set()
    await asyncio.wait({b1, b2}, timeout=10)
    mid = counts(mgr)
    pa.hang_up(1011)
    await asyncio.wait({ta}, timeout=10)
    after_a = counts(mgr)
    pb.hang_up()
    await asyncio.wait({tb}, timeout=10)
    return {"case": "overlapping_drops", "a_closes": pa.closes(), "b_closes": pb.closes(), "while_a_dropped": mid, "after_a_returns": after_a, "after_all": counts(mgr), "handlers": [outcome(ta), outcome(tb)]}


async def close_all_per_ip() -> dict:
    from juniper_service_core.websocket import manager

    mgr = manager.WebSocketManager(send_timeout_seconds=3600, max_connections_per_ip=1)
    pa, pb = Peer(), Peer()
    ta = (await serve(mgr, pa, "10.0.0.1"))[1]
    tb = (await serve(mgr, pb, "10.0.0.2"))[1]
    pa.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
    before = counts(mgr)
    await mgr.close_all()
    pa.hang_up(1011)
    pb.hang_up(1001)
    await asyncio.wait({ta, tb}, timeout=10)
    after = counts(mgr)
    admitted = {}
    for ip in ("10.0.0.1", "10.0.0.2"):
        p = Peer()
        t = (await serve(mgr, p, ip))[1]
        admitted[ip] = (not t.done()) and not p.closes()
        p.hang_up()
        await asyncio.wait({t}, timeout=10)
    return {"case": "close_all_per_ip", "before_close_all": before, "after_handlers_returned": after, "new_socket_admitted_after": admitted, "a_closes": pa.closes(), "b_closes": pb.closes()}


async def connect_handler_never_disconnects() -> dict:
    from juniper_service_core.websocket import manager

    mgr = manager.WebSocketManager(send_timeout_seconds=3600, max_connections_per_ip=1, max_connections=1)
    pa = Peer()
    wa = socket_for(pa, None, "10.0.0.1", "/custom")
    await mgr.connect(wa)
    pa.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})
    pa.hang_up(1011)  # the peer leaves; a handler of the service's own that relied on the drop never calls disconnect()
    await asyncio.sleep(0.05)
    pb = Peer()
    ok = await mgr.connect(socket_for(pb, None, "10.0.0.2", "/custom"))
    return {"case": "connect_handler_never_disconnects", "closes": pa.closes(), "counts": counts(mgr), "new_socket_admitted": ok, "b_closes": pb.closes()}


async def main_async() -> dict:
    from juniper_service_core.websocket import control_stream, manager, training_stream

    result = {"modules": {m.__name__: {"file": m.__file__, "sha256": _sha(m.__file__)} for m in (manager, control_stream, training_stream)}, "python": sys.version.split()[0], "executable": sys.executable, "base_prefix": sys.base_prefix, "cases": []}
    for kind in ("value_error", "timeout", "unexpected", "success"):
        result["cases"].append(await ctl_error_ack_after_close(kind))
    for coro in (drop_then_handler_raises, overlapping_drops, close_all_per_ip, connect_handler_never_disconnects):
        result["cases"].append(await coro())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = asyncio.run(main_async())
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, default=str)
    for case in result["cases"]:
        print(json.dumps(case, default=str)[:700])
    return 0


if __name__ == "__main__":
    sys.exit(main())
