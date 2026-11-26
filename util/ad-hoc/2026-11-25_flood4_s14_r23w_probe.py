"""
Reproduce ruling 23's three "WebSocket gaps beside N-4" in juniper-service-core: in process, and on real uvicorn.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23w: re-verify and fix ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Which juniper_service_core runs is whatever the interpreter imports (put a tree on PYTHONPATH to pick main or the
fix); the JSON records the imported module paths and their sha256, so a cell names the code it measured.

Usage:
  python <this file> inproc --out OUT.json
      (a) an unserialisable broadcast, and an oversized one with the same value; (b) /ws/control after its
      heartbeat's close, with a late pong and a late command; (c) the per-IP slot of a dropped socket.
      Real Starlette WebSocket objects over an in-memory ASGI peer.
  python <this file> uvicorn --ws {websockets,websockets-sansio,wsproto} --scenario {late_pong,late_command,stall} --out OUT.json
      Real uvicorn on 127.0.0.1, an ephemeral port (port 0), and a raw-socket client.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime
import hashlib
import json
import logging
import os
import socket
import sys
import time
import types
from pathlib import Path
from typing import Any

import juniper_service_core.websocket.control_stream as control_stream
import juniper_service_core.websocket.manager as manager_mod
import juniper_service_core.websocket.training_stream as training_stream
from fastapi import WebSocket
from juniper_service_core.websocket.control_stream import control_stream_handler
from juniper_service_core.websocket.manager import WebSocketManager
from juniper_service_core.websocket.training_stream import training_stream_handler


def _code_identity() -> dict:
    out = {}
    for mod in (manager_mod, control_stream, training_stream):
        path = Path(mod.__file__)
        out[mod.__name__] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return out


def _env() -> dict:
    import fastapi
    import starlette

    info = {"python": sys.version.split()[0], "executable": sys.executable, "fastapi": fastapi.__version__, "starlette": starlette.__version__}
    try:
        import uvicorn
        import websockets

        info["uvicorn"] = uvicorn.__version__
        info["websockets"] = websockets.__version__
    except ImportError:
        info["uvicorn"] = info["websockets"] = None  # the in-process cells need neither
    try:
        import wsproto

        info["wsproto"] = getattr(wsproto, "__version__", "installed")
    except ImportError:
        info["wsproto"] = None
    return info


# ------------------------------------------------------------------------------------------------
# In process: an in-memory ASGI peer under Starlette's own WebSocket
# ------------------------------------------------------------------------------------------------


class Peer:
    """The ASGI server's side of one socket: an inbox the app reads, a record of what it sends."""

    def __init__(self, *, fail_sends: bool = False) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.inbox.put_nowait({"type": "websocket.connect"})
        self.messages: list[dict] = []
        self.fail_sends = fail_sends

    async def receive(self) -> dict:
        return await self.inbox.get()

    async def send(self, message: dict) -> None:
        if message["type"] == "websocket.send" and self.fail_sends:
            raise RuntimeError("transport refused the frame")
        self.messages.append(message)

    def push(self, frame: dict) -> None:
        self.inbox.put_nowait({"type": "websocket.receive", "text": json.dumps(frame)})

    def hang_up(self, code: int = 1000) -> None:
        self.inbox.put_nowait({"type": "websocket.disconnect", "code": code})

    def frames(self) -> list[dict]:
        return [json.loads(m["text"]) for m in self.messages if m["type"] == "websocket.send"]

    def closes(self) -> list[list]:
        return [[m.get("code"), m.get("reason")] for m in self.messages if m["type"] == "websocket.close"]


def _socket(peer: Peer, app: Any, ip: str = "10.0.0.1", path: str = "/ws/training") -> WebSocket:
    scope = {"type": "websocket", "path": path, "headers": [], "query_string": b"", "client": (ip, 5000), "app": app}
    return WebSocket(scope, peer.receive, peer.send)


def _training_app(mgr: WebSocketManager) -> Any:
    settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=30, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600)
    return types.SimpleNamespace(state=types.SimpleNamespace(ws_manager=mgr, lifecycle=None, settings=settings))


async def _settle(n: int = 200) -> None:
    for _ in range(n):
        await asyncio.sleep(0)


async def _wait(pred, limit: float = 10.0) -> bool:
    loop = asyncio.get_running_loop()
    end = loop.time() + limit
    while not pred():
        if loop.time() > end:
            return False
        await asyncio.sleep(0.001)
    return True


async def _serve_training(mgr: WebSocketManager, peer: Peer, first: dict, ip: str = "10.0.0.1") -> tuple[WebSocket, asyncio.Task]:
    peer.push(first)
    ws = _socket(peer, _training_app(mgr), ip)
    task = asyncio.create_task(training_stream_handler(ws))
    await _wait(lambda: ws in mgr._active_connections or task.done())
    await _settle()
    return ws, task


def _outcome(task: asyncio.Task) -> str:
    if not task.done():
        return "running"
    if task.cancelled():
        return "cancelled"
    exc = task.exception()
    return "returned" if exc is None else f"RAISED {type(exc).__name__}: {exc}"


async def inproc_unserialisable() -> dict:
    """(a): one broadcast holding a datetime; then a resume across it; then an oversized one with the same value."""
    mgr = WebSocketManager(send_timeout_seconds=5)
    peers = [Peer(), Peer()]
    tasks = []
    for i, peer in enumerate(peers):
        _, task = await _serve_training(mgr, peer, {"type": "hello"}, ip=f"10.0.0.{i + 1}")
        tasks.append(task)
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # seq 1: delivered
    seq_before = mgr.current_seq
    failures_before = mgr.transport_stats()["send_failures"]
    raised = None
    try:
        await mgr.broadcast({"type": "metrics", "data": {"when": datetime.datetime(2026, 11, 25, 12, 0, 0)}})
    except Exception as exc:  # recorded, not swallowed silently
        raised = f"{type(exc).__name__}: {exc}"
    await _settle()
    stats = mgr.transport_stats()
    result = {
        "broadcast_raised": raised,
        "seq_before": seq_before,
        "seq_after": mgr.current_seq,
        "replay_buffer_size": stats["replay_buffer_size"],
        "send_failures_added": stats["send_failures"] - failures_before,
        "unserializable_messages_total": stats.get("unserializable_messages_total", "(no such key)"),
        "closes_per_socket": [p.closes() for p in peers],
        "active_after": mgr.connection_count,
    }
    # The next broadcast: who still receives it?
    await mgr.broadcast({"type": "metrics", "data": {"n": 3}})
    await _settle()
    result["next_broadcast_seq"] = mgr.current_seq
    result["next_broadcast_received_by"] = [[f.get("seq") for f in p.frames() if f.get("type") == "metrics"] for p in peers]
    for peer in peers:
        peer.hang_up(1000)
    await asyncio.wait(tasks, timeout=10)
    result["handlers"] = [_outcome(t) for t in tasks]
    # A resume from seq 1, across the frame that took seq 2 on main.
    peer = Peer()
    _, task = await _serve_training(mgr, peer, {"type": "resume", "data": {"last_seq": 1, "server_instance_id": mgr.server_instance_id}}, ip="10.0.0.9")
    await _settle()
    result["resume_from_seq_1"] = {"frames": [f.get("type") + (f"#{f['seq']}" if "seq" in f else "") for f in peer.frames()], "closes": peer.closes()}
    peer.hang_up(1000)
    await asyncio.wait({task}, timeout=10)
    # An oversized message with the same value: delivered as chunks today (the chunker sizes with default=str).
    mgr2 = WebSocketManager(send_timeout_seconds=5, max_message_size_bytes=200, chunk_payload_size_bytes=100)
    peer2 = Peer()
    _, task2 = await _serve_training(mgr2, peer2, {"type": "hello"})
    big = {"type": "metrics", "data": {"when": datetime.datetime(2026, 11, 25, 12, 0, 0), "pad": "x" * 300}}
    await mgr2.broadcast(big)
    await _settle()
    chunk_texts = [m["text"] for m in peer2.messages if m["type"] == "websocket.send" and json.loads(m["text"]).get("type") == "chunked_message"]
    payload = "".join(json.loads(t)["data"]["payload"] for t in chunk_texts)
    result["oversized_same_value"] = {
        "chunks_delivered": len(chunk_texts),
        "closes": peer2.closes(),
        "reassembled_equals_default_str_dump": payload == json.dumps(big, default=str),
        "chunk_payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
    }
    peer2.hang_up(1000)
    await asyncio.wait({task2}, timeout=10)
    return result


class RecordingExecutor:
    commands = ("start", "stop", "pause", "resume", "reset", "set_params")

    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, command: str, params: dict | None) -> dict:
        self.executed.append(command)
        return {"ok": True}


def _control_app(executor: RecordingExecutor | None, hb: float) -> Any:
    settings = types.SimpleNamespace(
        disable_ws_control_endpoint=False,
        ws_control_cooldown_rejections=10,
        ws_control_cooldown_window_sec=60,
        ws_control_cooldown_block_sec=300,
        ws_control_allowed_origins=None,
        ws_control_rate_limit_per_sec=10,
        ws_control_idle_timeout_sec=3600,
        ws_heartbeat_interval_sec=hb,
        ws_heartbeat_pong_timeout_sec=hb,
    )
    return types.SimpleNamespace(state=types.SimpleNamespace(settings=settings, command_executor=executor, ws_manager=None))


async def inproc_control_late(frame: dict) -> dict:
    """(b): the heartbeat closes /ws/control 1011; then ``frame`` arrives (completing the receive in flight), then another."""
    executor = RecordingExecutor()
    peer = Peer()
    ws = _socket(peer, _control_app(executor, hb=0.01), path="/ws/control")
    task = asyncio.create_task(control_stream_handler(ws))
    closed = await _wait(lambda: bool(peer.closes()))
    peer.push(frame)
    peer.push(frame)
    await _settle()
    await asyncio.sleep(0.05)
    await _settle()
    before_hangup = _outcome(task)
    peer.hang_up(1011)
    await asyncio.wait({task}, timeout=10)
    sends_after_close = []
    seen_close = False
    for m in peer.messages:
        if m["type"] == "websocket.close":
            seen_close = True
        elif seen_close and m["type"] == "websocket.send":
            sends_after_close.append(json.loads(m["text"]).get("type"))
    return {"server_closed": closed, "closes": peer.closes(), "outcome_before_disconnect": before_hangup, "outcome": _outcome(task), "executed": executor.executed, "sends_after_close": sends_after_close}


async def inproc_per_ip() -> dict:
    """(c): cap 1 per IP; a socket whose broadcast send fails is dropped; is a second socket from its address admitted while the first is open?"""
    mgr = WebSocketManager(send_timeout_seconds=5, max_connections_per_ip=1, max_connections=1)
    a = Peer(fail_sends=False)
    _, task_a = await _serve_training(mgr, a, {"type": "hello"})
    a.fail_sends = True
    await mgr.broadcast({"type": "metrics", "data": {"n": 1}})  # A's send fails: dropped, closed 1011
    await _settle()
    at_drop = {"a_closes": a.closes(), "a_handler": _outcome(task_a), "connection_count": mgr.connection_count, "endpoint_counts": mgr.endpoint_counts(), "per_ip": dict(mgr._per_ip_counts)}
    b = Peer()
    _, task_b = await _serve_training(mgr, b, {"type": "hello"})  # same address, while A's handler still runs (its peer has not answered the close)
    second = {
        "b_admitted": any(f.get("type") == "connection_established" for f in b.frames()),
        "b_closes": b.closes(),
        "a_handler_when_b_tried": _outcome(task_a),
        "connection_count": mgr.connection_count,
        "endpoint_counts": mgr.endpoint_counts(),
        "per_ip": dict(mgr._per_ip_counts),
    }
    a.hang_up(1011)  # A's peer answers the close
    await asyncio.wait({task_a}, timeout=10)
    await _settle()
    after_a = {"a_handler": _outcome(task_a), "connection_count": mgr.connection_count, "endpoint_counts": mgr.endpoint_counts(), "per_ip": dict(mgr._per_ip_counts)}
    c = Peer()
    _, task_c = await _serve_training(mgr, c, {"type": "hello"})
    after_a["c_admitted_after_a_returned"] = any(f.get("type") == "connection_established" for f in c.frames())
    for p in (b, c):
        p.hang_up(1000)
    await asyncio.wait({task_b, task_c}, timeout=10)
    return {"at_drop": at_drop, "second_socket_same_ip": second, "after_a_returned": after_a, "end": {"connection_count": mgr.connection_count, "endpoint_counts": mgr.endpoint_counts(), "per_ip": dict(mgr._per_ip_counts)}}


async def run_inproc() -> dict:
    return {
        "a_unserialisable_broadcast": await inproc_unserialisable(),
        "b_control_late_pong": await inproc_control_late({"type": "pong"}),
        "b_control_late_command": await inproc_control_late({"command": "stop", "command_id": "late-1"}),
        "c_per_ip_slot": await inproc_per_ip(),
    }


# ------------------------------------------------------------------------------------------------
# Real uvicorn, raw-socket client
# ------------------------------------------------------------------------------------------------


def _frame(opcode: int, payload: bytes) -> bytes:
    key = os.urandom(4)
    n = len(payload)
    if n < 126:
        head = bytes([0x80 | opcode, 0x80 | n])
    elif n < 65536:
        head = bytes([0x80 | opcode, 0x80 | 126]) + n.to_bytes(2, "big")
    else:
        head = bytes([0x80 | opcode, 0x80 | 127]) + n.to_bytes(8, "big")
    return head + key + bytes(b ^ key[i % 4] for i, b in enumerate(payload))


async def _read_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    b1, b2 = await reader.readexactly(2)
    n = b2 & 0x7F
    if n == 126:
        n = int.from_bytes(await reader.readexactly(2), "big")
    elif n == 127:
        n = int.from_bytes(await reader.readexactly(8), "big")
    return b1 & 0x0F, await reader.readexactly(n)


async def _client(port: int, path: str, *, rcvbuf: int | None = None) -> tuple[int, asyncio.StreamReader | None, asyncio.StreamWriter | None]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if rcvbuf:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.setblocking(False)
    await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", port))
    reader, writer = await asyncio.open_connection(sock=sock)
    key = base64.b64encode(os.urandom(16)).decode()
    writer.write(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
    await writer.drain()
    status = int((await asyncio.wait_for(reader.readline(), 10)).split()[1])
    while (await asyncio.wait_for(reader.readline(), 10)) not in (b"\r\n", b""):
        pass
    if status != 101:
        writer.close()
        return status, None, None
    return status, reader, writer


def _send_text(writer: asyncio.StreamWriter, obj: dict) -> None:
    writer.write(_frame(0x1, json.dumps(obj).encode()))


class _Captured(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record.getMessage())


async def _start_server(app: Any, ws_impl: str):
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=0, ws=ws_impl, lifespan="off", log_config=None, log_level="info")
    server = uvicorn.Server(config)
    serving = asyncio.create_task(server.serve())
    assert await _wait(lambda: server.started or serving.done(), limit=20), "uvicorn did not start"
    port = server.servers[0].sockets[0].getsockname()[1]
    return server, serving, port


async def _stop_server(server, serving) -> None:
    server.should_exit = True
    await asyncio.wait({serving}, timeout=20)


def _wrapped(handler, record: dict):
    async def endpoint(websocket: WebSocket) -> None:
        record["started"] = time.monotonic()
        try:
            await handler(websocket)
        except BaseException as exc:
            record["outcome"] = f"RAISED {type(exc).__name__}: {exc}"
            record["ended"] = time.monotonic()
            raise
        record["outcome"] = "returned"
        record["ended"] = time.monotonic()

    return endpoint


async def run_uvicorn_late(ws_impl: str, late: dict) -> dict:
    """(b) on the wire: no pong, so the heartbeat closes 1011; the client then sends ``late`` twice, then its close."""
    from fastapi import FastAPI

    captured = _Captured()
    logging.getLogger("uvicorn.error").addHandler(captured)
    logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
    executor = RecordingExecutor()
    record: dict = {}
    app = FastAPI()
    app.state.settings = _control_app(executor, hb=0.2).state.settings
    app.state.command_executor = executor
    app.add_api_websocket_route("/ws/control", _wrapped(control_stream_handler, record))
    server, serving, port = await _start_server(app, ws_impl)
    result: dict = {"port_ephemeral": port}
    try:
        status, reader, writer = await _client(port, "/ws/control")
        result["handshake"] = status
        frames: list[Any] = []
        close_seen = None
        t_close = None
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            opcode, payload = await asyncio.wait_for(_read_frame(reader), timeout=15)
            if opcode == 0x8:
                close_seen = [int.from_bytes(payload[:2], "big"), payload[2:].decode()]
                t_close = time.monotonic()
                break
            frames.append(json.loads(payload).get("type") if opcode == 0x1 else f"opcode{opcode}")
        result["frames_before_close"] = frames
        result["server_close"] = close_seen
        _send_text(writer, late)  # after the server's close: a late frame
        _send_text(writer, late)
        await writer.drain()
        after: list[Any] = []
        try:
            while True:
                opcode, payload = await asyncio.wait_for(_read_frame(reader), timeout=1.0)
                after.append(json.loads(payload).get("type") if opcode == 0x1 else f"opcode{opcode}")
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError) as exc:
            result["read_after_server_close_ended_by"] = type(exc).__name__  # a quiet second, or the server's EOF
        result["frames_after_server_close"] = after
        result["handler_outcome_before_client_close"] = record.get("outcome", "running")
        try:
            writer.write(_frame(0x8, (1000).to_bytes(2, "big")))
            await writer.drain()
        except ConnectionError as exc:
            result["client_close_failed"] = type(exc).__name__  # the server dropped the transport first
        await _wait(lambda: "outcome" in record, limit=15)
        writer.close()
        result["handler_outcome"] = record.get("outcome", "running")
        result["handler_seconds_after_server_close"] = round(record["ended"] - t_close, 3) if "ended" in record and t_close else None
        result["executed"] = executor.executed
        result["asgi_exceptions_logged"] = sum(1 for m in captured.records if "Exception in ASGI application" in m)
    finally:
        await _stop_server(server, serving)
        logging.getLogger("uvicorn.error").removeHandler(captured)
    return result


async def run_uvicorn_stall(ws_impl: str) -> dict:
    """(c) on the wire: cap 1 per IP; client A stops reading; 55 kB broadcasts until A is dropped; then B from the same address."""
    from fastapi import FastAPI

    mgr = WebSocketManager(send_timeout_seconds=0.5, max_connections_per_ip=1)
    records: list[dict] = []

    def endpoint_factory():
        rec: dict = {}
        records.append(rec)
        return _wrapped(training_stream_handler, rec)

    app = FastAPI()
    app.state.ws_manager = mgr
    app.state.lifecycle = None
    app.state.settings = _training_app(mgr).state.settings

    async def endpoint(websocket: WebSocket) -> None:
        await endpoint_factory()(websocket)

    app.add_api_websocket_route("/ws/training", endpoint)
    server, serving, port = await _start_server(app, ws_impl)
    result: dict = {"port_ephemeral": port}
    writers = []
    try:
        status, _, writer_a = await _client(port, "/ws/training", rcvbuf=4096)  # A never reads again
        writers.append(writer_a)
        result["a_handshake"] = status
        _send_text(writer_a, {"type": "hello"})
        await writer_a.drain()
        assert await _wait(lambda: len(mgr._active_connections) == 1, limit=10)
        a_ws = next(iter(mgr._active_connections))
        blob = {"type": "metrics", "data": {"blob": "x" * 55_000}}
        t0 = time.monotonic()
        sent = 0
        while a_ws in mgr._active_connections and time.monotonic() - t0 < 60:
            await mgr.broadcast(blob)
            sent += 1
        t_drop = time.monotonic()
        result["broadcasts_until_drop"] = sent
        result["dropped"] = a_ws not in mgr._active_connections
        result["seconds_to_drop"] = round(t_drop - t0, 3)
        result["at_drop"] = {"a_handler": records[0].get("outcome", "running"), "connection_count": mgr.connection_count, "endpoint_counts": mgr.endpoint_counts(), "per_ip": dict(mgr._per_ip_counts)}
        status_b, _, writer_b = await _client(port, "/ws/training")
        result["b_handshake"] = status_b
        if writer_b is not None:
            writers.append(writer_b)
            _send_text(writer_b, {"type": "hello"})
            await writer_b.drain()
            await _wait(lambda: len(records) >= 2 and mgr.endpoint_counts()["training"] >= 1 and len(mgr._active_connections) >= 1, limit=5)
        result["when_b_tried"] = {
            "a_handler": records[0].get("outcome", "running"),
            "sockets_open_from_one_ip_with_cap_1": sum(1 for r in records if "started" in r and "outcome" not in r),
            "connection_count": mgr.connection_count,
            "endpoint_counts": mgr.endpoint_counts(),
            "per_ip": dict(mgr._per_ip_counts),
        }
        # How long does A's handler outlive the drop? (bounded observation)
        await _wait(lambda: "outcome" in records[0], limit=45)
        result["a_handler_outcome"] = records[0].get("outcome", "running")
        result["a_handler_outlived_drop_seconds"] = round(records[0]["ended"] - t_drop, 3) if "ended" in records[0] else None
        if writer_b is None:
            status_c, _, writer_c = await _client(port, "/ws/training")
            result["c_handshake_after_a_ended"] = status_c
            if writer_c is not None:
                writers.append(writer_c)
        result["end_counts"] = {"connection_count": mgr.connection_count, "endpoint_counts": mgr.endpoint_counts(), "per_ip": dict(mgr._per_ip_counts)}
    finally:
        for w in writers:
            try:
                w.close()
            except OSError as exc:
                result.setdefault("client_close_errors", []).append(type(exc).__name__)  # already closed by the server
        await _stop_server(server, serving)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="mode", required=True)
    p_in = sub.add_parser("inproc")
    p_in.add_argument("--out", required=True)
    p_uv = sub.add_parser("uvicorn")
    p_uv.add_argument("--ws", required=True, choices=["websockets", "websockets-sansio", "wsproto"])
    p_uv.add_argument("--scenario", required=True, choices=["late_pong", "late_command", "stall"])
    p_uv.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out: dict[str, Any] = {"env": _env(), "code": _code_identity(), "started_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if args.mode == "inproc":
        out["mode"] = "inproc"
        out["results"] = asyncio.run(run_inproc())
    else:
        out["mode"] = f"uvicorn ws={args.ws} scenario={args.scenario}"
        if args.scenario == "stall":
            out["results"] = asyncio.run(run_uvicorn_stall(args.ws))
        else:
            late = {"type": "pong"} if args.scenario == "late_pong" else {"command": "stop", "command_id": "late-1"}
            out["results"] = asyncio.run(run_uvicorn_late(args.ws, late))
    Path(args.out).write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(out["results"], indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
