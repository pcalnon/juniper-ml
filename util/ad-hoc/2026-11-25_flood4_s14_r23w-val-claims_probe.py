#!/usr/bin/env python3
"""
Claims-lens probe for ruling 23's "WebSocket gaps beside N-4": what a client sees, in process and on real uvicorn.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14 claims lens r23w-val-claims, run in session 15 on 2026-11-26 UTC)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Which juniper_service_core runs is whatever this interpreter imports (a venv with main's tree or the fixed tree
installed editable); the JSON records each WebSocket module's path and sha256, so a run names the code it measured.

testclient   In process, with Starlette's TestClient (one portal loop for every session; the probe runs the manager's
             broadcast on that loop with portal.call, so each step has finished when the call returns):
             a_*  /ws/training: an unsendable broadcast (a datetime; separately a lone surrogate) between two good
                  ones; every frame and close each client got, transport_stats() around it, the log lines, a resume
                  across it.
             c_*  /ws/training: a socket whose broadcast send raises is dropped (its server-side send_json is made to
                  raise); a second socket from the same address (TestClient's "testclient") under three caps:
                  per-IP 1, global 1, and the defaults (5 / 50); its admission answer and connection_established's
                  data.connections; the counts while the dropped socket is open and after it has gone.
             b_*  /ws/control: the heartbeat closes the socket 1011, then a late command arrives; and a command still
                  running when the heartbeat closes. What was executed, what was sent after the close, the log lines,
                  and whether the handler raised.
wire         Real uvicorn on 127.0.0.1, port 0 (the kernel picks it), one --ws implementation, a raw RFC 6455 client.
             Client A completes its handshake and never reads again (SO_RCVBUF 4096); 55 kB broadcasts until A is
             dropped; then client B from the same address: its HTTP status line (101 or 403) and, if admitted, its
             connection_established data.connections. With --hold S, A's state and a client C's status after S s.

Usage
-----
    python <this file> testclient --out OUT.json
    python <this file> wire --ws {websockets,websockets-sansio,wsproto} --cap N [--max-connections M] [--hold S] --out OUT.json
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
import struct
import sys
import threading
import time
import types
from typing import Any

import anyio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from juniper_service_core.websocket import control_stream as _cs
from juniper_service_core.websocket import manager as _mgr
from juniper_service_core.websocket import training_stream as _ts
from juniper_service_core.websocket.commands import DEFAULT_COMMANDS
from juniper_service_core.websocket.manager import WebSocketManager
from juniper_service_core.websocket.router import build_websocket_router

_WHEN = datetime.datetime(2026, 11, 25, 12, 0, 0)
_SURROGATE = "\udc80"


def _modules() -> dict:
    out = {}
    for mod in (_mgr, _cs, _ts):
        with open(mod.__file__, "rb") as fh:
            out[mod.__name__] = {"path": mod.__file__, "sha256": hashlib.sha256(fh.read()).hexdigest()}
    return out


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append({"logger": record.name, "level": record.levelname, "msg": record.getMessage()})


def _capture() -> Capture:
    cap = Capture()
    for name in ("juniper_service_core", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.setLevel(logging.DEBUG)
        lg.addHandler(cap)
    return cap


def _app(mgr: WebSocketManager, *, settings: Any = None, executor: Any = None) -> FastAPI:
    app = FastAPI()
    app.include_router(build_websocket_router())
    app.state.ws_manager = mgr
    if settings is not None:
        app.state.settings = settings
    if executor is not None:
        app.state.command_executor = executor
    return app


def _frame(msg: dict) -> dict:
    if msg["type"] == "websocket.close":
        return {"close": [msg.get("code"), msg.get("reason")]}
    if msg["type"] != "websocket.send":
        return {"other": msg["type"]}
    text = msg.get("text")
    try:
        data = json.loads(text)
    except Exception:  # noqa: BLE001 - a frame that is not JSON is recorded raw
        return {"raw": (text or "")[:120]}
    inner = data.get("data") if isinstance(data.get("data"), dict) else {}
    keep = {k: inner[k] for k in ("connections", "status", "error", "command", "result", "n") if k in inner}
    return {"type": data.get("type"), "seq": data.get("seq"), **({"data": keep} if keep else {}), **({"command": data.get("command")} if "command" in data else {})}


def _drain(session: Any) -> list[dict]:
    out = []
    while True:
        try:
            msg = session.portal.call(session._send_rx.receive_nowait)
        except anyio.WouldBlock:
            return out
        except Exception as exc:  # noqa: BLE001 - a closed stream ends the drain
            out.append({"drain_ended": type(exc).__name__})
            return out
        out.append(_frame(msg))


def _until(predicate: Any, limit: float = 10.0, step: float = 0.01) -> bool:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return bool(predicate())


def _open(client: TestClient, path: str) -> tuple[Any, dict]:
    session = client.websocket_connect(path)
    try:
        session.__enter__()
    except WebSocketDisconnect as exc:
        return None, {"refused": [exc.code, exc.reason]}
    return session, {"accepted": True}


def _close(session: Any, settle: Any = None) -> dict:
    """Hang up as a client does, let the handler see it (``settle``, or the inbox emptied), then end the session.

    TestClient's own exit cancels the app's scope right after it sends the disconnect, which could cut a handler's
    ``finally`` short; so the disconnect is sent first and the handler given its turn before the exit.
    """
    if session is None:
        return {"closed": "not open"}
    try:
        session.send({"type": "websocket.disconnect", "code": 1000})
    except Exception as exc:  # noqa: BLE001 - the app may have ended already (on main, by raising)
        pass
    if settle is not None:
        settled = _until(settle, limit=5.0)
    else:
        settled = _until(lambda: session.portal.call(lambda: session._receive_tx.statistics().current_buffer_used) == 0, limit=5.0)
        time.sleep(0.2)  # an observation window for the handler to return once it has read the disconnect
    try:
        session.__exit__(None, None, None)
    except Exception as exc:  # noqa: BLE001 - the handler's own exception is what is measured
        return {"settled": settled, "handler_raised": f"{type(exc).__name__}: {exc}"}
    return {"settled": settled, "handler_raised": None}


def _stats(client: TestClient, mgr: WebSocketManager) -> dict:
    def snap() -> dict:
        st = mgr.transport_stats()
        keys = ("send_failures", "unserializable_messages_total", "active_connections", "pending_connections", "dropped_connections", "current_seq", "replay_buffer_size")
        return {
            "transport_stats": {k: st.get(k, "<absent>") for k in keys},
            "connection_count": mgr.connection_count,
            "per_ip": dict(mgr._per_ip_counts),
            "endpoint_counts": mgr.endpoint_counts(),
            "has_key_unserializable": "unserializable_messages_total" in st,
            "has_key_dropped": "dropped_connections" in st,
        }

    return client.portal.call(snap)


def _fresh(client: TestClient, mgr: WebSocketManager, want_active: int) -> tuple[Any, dict]:
    session, answer = _open(client, "/ws/training")
    if session is None:
        return None, answer
    session.send_json({"type": "hello"})
    _until(lambda: client.portal.call(lambda: mgr.transport_stats()["active_connections"]) >= want_active)
    answer["first_frames"] = _drain(session)
    return session, answer


# ----------------------------------------------------------------------------------------------------------- (a)
def scenario_a(cap: Capture) -> dict:
    out: dict = {}
    mgr = WebSocketManager(send_timeout_seconds=0.5)
    with TestClient(_app(mgr)) as client:
        s1, a1 = _fresh(client, mgr, 1)
        s2, a2 = _fresh(client, mgr, 2)
        sid = next((f.get("data", {}) for f in a1["first_frames"] if f.get("type") == "connection_established"), {})
        server_instance_id = mgr._server_instance_id
        out["connect"] = [a1, a2]
        client.portal.call(mgr.broadcast, {"type": "metrics", "data": {"n": 1}})
        out["after_seq1"] = {"s1": _drain(s1), "s2": _drain(s2), "stats": _stats(client, mgr)}
        n_logs = len(cap.records)
        client.portal.call(mgr.broadcast, {"type": "metrics", "data": {"when": _WHEN}})
        out["after_datetime"] = {"s1": _drain(s1), "s2": _drain(s2), "stats": _stats(client, mgr), "logs": [r for r in cap.records[n_logs:] if r["level"] in ("ERROR", "WARNING", "INFO")]}
        client.portal.call(mgr.broadcast, {"type": "metrics", "data": {"n": 2}})
        out["after_n2"] = {"s1": _drain(s1), "s2": _drain(s2), "stats": _stats(client, mgr)}
        s3, a3 = _open(client, "/ws/training")
        out["resume"] = {"open": a3}
        if s3 is not None:
            s3.send_json({"type": "resume", "data": {"last_seq": 1, "server_instance_id": server_instance_id}})
            got: list[dict] = []

            def settled() -> bool:
                got.extend(_drain(s3))
                return any("close" in f for f in got) or any(f.get("type") == "metrics" and f.get("seq") == 3 for f in got) or any(f.get("type") == "metrics" and f.get("seq") == 2 and (f.get("data") or {}).get("n") == 2 for f in got)

            out["resume"]["settled"] = _until(settled, limit=5.0)
            out["resume"]["frames"] = got
        out["unused_sid"] = sid
        out["close"] = {"s1": _close(s1), "s2": _close(s2), "s3": _close(s3)}
    # A lone surrogate on its own (TestClient's transport does not encode text as UTF-8; a real server does).
    mgr = WebSocketManager(send_timeout_seconds=0.5)
    with TestClient(_app(mgr)) as client:
        s1, _ = _fresh(client, mgr, 1)
        n_logs = len(cap.records)
        client.portal.call(mgr.broadcast, {"type": "metrics", "data": {"s": _SURROGATE}})
        out["lone_surrogate"] = {"s1": _drain(s1), "stats": _stats(client, mgr), "logs": [r for r in cap.records[n_logs:] if r["level"] in ("ERROR", "WARNING")]}
        out["lone_surrogate"]["close"] = _close(s1)
    # The frame's ``type`` is printed by the ERROR line: a lone surrogate in ``type`` itself.
    mgr = WebSocketManager(send_timeout_seconds=0.5)
    with TestClient(_app(mgr)) as client:
        s1, _ = _fresh(client, mgr, 1)
        n_logs = len(cap.records)
        client.portal.call(mgr.broadcast, {"type": "m" + _SURROGATE, "data": {}})
        logs = [r for r in cap.records[n_logs:] if r["level"] == "ERROR"]
        out["surrogate_in_type"] = {"s1": _drain(s1), "logs": [{**r, "msg_ascii": ascii(r["msg"])} for r in logs]}
        out["surrogate_in_type"]["close"] = _close(s1)
    return out


# ----------------------------------------------------------------------------------------------------------- (c)
def scenario_c(cap: Capture, max_per_ip: int, max_total: int) -> dict:
    out: dict = {"max_connections_per_ip": max_per_ip, "max_connections": max_total}
    mgr = WebSocketManager(send_timeout_seconds=0.5, max_connections_per_ip=max_per_ip, max_connections=max_total)
    with TestClient(_app(mgr)) as client:
        sa, aa = _fresh(client, mgr, 1)
        out["a_connect"] = aa
        server_a = client.portal.call(lambda: next(iter(mgr._active_connections)))

        async def refuse(data: Any, mode: str = "text") -> None:
            raise RuntimeError("the transport refused the frame (probe)")

        server_a.send_json = refuse  # this socket's next broadcast send fails; its close still goes through send()
        client.portal.call(mgr.broadcast, {"type": "metrics", "data": {"n": 1}})
        out["a_after_drop"] = _drain(sa)
        out["stats_at_drop"] = _stats(client, mgr)
        n_logs = len(cap.records)
        sb, ab = _open(client, "/ws/training")
        out["b_answer"] = ab
        if sb is not None:
            sb.send_json({"type": "hello"})
            _until(lambda: client.portal.call(lambda: mgr.transport_stats()["active_connections"]) >= 1, limit=5.0)
            out["b_first_frames"] = _drain(sb)
        out["b_logs"] = [r for r in cap.records[n_logs:] if r["level"] in ("WARNING", "ERROR")]
        out["stats_with_b"] = _stats(client, mgr)
        out["a_close"] = _close(sa, settle=lambda: _stats(client, mgr)["endpoint_counts"].get("training", 0) == (1 if sb is not None else 0))
        out["stats_after_a_gone"] = _stats(client, mgr)
        sc, ac = _open(client, "/ws/training")
        out["c_answer_after_a_gone"] = ac
        out["b_close"] = _close(sb)
        out["c_close"] = _close(sc)
    return out


# ----------------------------------------------------------------------------------------------------------- (b)
class Executor:
    commands = tuple(DEFAULT_COMMANDS)

    def __init__(self, block: str | None = None) -> None:
        self.executed: list[str] = []
        self.block = block
        self.started = threading.Event()
        self.gate = threading.Event()
        self.done = threading.Event()

    def execute(self, command: str, params: dict | None) -> dict:
        self.executed.append(command)
        if command == self.block:
            self.started.set()
            self.gate.wait(30)
        self.done.set()
        return {"ok": True, "command": command}


def _control_settings() -> types.SimpleNamespace:
    return types.SimpleNamespace(ws_heartbeat_interval_sec=0.05, ws_heartbeat_pong_timeout_sec=0.1, ws_control_idle_timeout_sec=0, ws_control_allowed_origins=[])


def _wait_close(session: Any, got: list[dict], limit: float = 10.0) -> bool:
    def closed() -> bool:
        got.extend(_drain(session))
        return any("close" in f for f in got)

    return _until(closed, limit=limit)


def _after_close(frames: list[dict]) -> list[dict]:
    out, closed = [], False
    for f in frames:
        if "close" in f:
            closed = True
        elif closed:
            out.append(f)
    return out


def scenario_b_late(cap: Capture) -> dict:
    out: dict = {}
    ex = Executor()
    mgr = WebSocketManager()
    with TestClient(_app(mgr, settings=_control_settings(), executor=ex)) as client:
        s, a = _open(client, "/ws/control")
        out["open"] = a
        got: list[dict] = []
        out["heartbeat_closed"] = _wait_close(s, got)
        n_logs = len(cap.records)
        s.send_text(json.dumps({"command": "stop", "command_id": "late-1"}))
        out["late_frame_consumed"] = _until(lambda: s.portal.call(lambda: s._receive_tx.statistics().current_buffer_used) == 0, limit=5.0)
        _until(lambda: bool(ex.executed), limit=1.0)  # an observation window: on main the dispatch runs at once
        got.extend(_drain(s))
        out["frames"] = got
        out["sent_after_the_close"] = _after_close(got)
        out["executed"] = list(ex.executed)
        out["close"] = _close(s)
        out["logs"] = [r for r in cap.records[n_logs:] if r["logger"].startswith("juniper_service_core") and r["level"] in ("INFO", "WARNING", "ERROR")]
    return out


def scenario_b_inflight(cap: Capture) -> dict:
    out: dict = {}
    ex = Executor(block="start")
    mgr = WebSocketManager()
    with TestClient(_app(mgr, settings=_control_settings(), executor=ex)) as client:
        s, a = _open(client, "/ws/control")
        out["open"] = a
        got: list[dict] = _drain(s)
        n_logs = len(cap.records)
        s.send_text(json.dumps({"command": "start", "command_id": "c-1"}))
        out["started"] = ex.started.wait(10)
        out["heartbeat_closed"] = _wait_close(s, got)
        ex.gate.set()
        out["executor_done"] = ex.done.wait(10)
        _until(lambda: any("not acknowledged" in r["msg"] or "Cannot call" in r["msg"] for r in cap.records[n_logs:]), limit=3.0)
        got.extend(_drain(s))
        out["frames"] = got
        out["sent_after_the_close"] = _after_close(got)
        out["executed"] = list(ex.executed)
        out["close"] = _close(s)
        out["logs"] = [r for r in cap.records[n_logs:] if r["logger"].startswith("juniper_service_core") and r["level"] in ("INFO", "WARNING", "ERROR")]
    return out


def run_testclient(args: argparse.Namespace) -> dict:
    cap = _capture()
    result = {"mode": "testclient", "python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "modules": _modules()}
    result["a_unsendable"] = scenario_a(cap)
    result["c_per_ip_1"] = scenario_c(cap, 1, 50)
    result["c_global_1"] = scenario_c(cap, 5, 1)
    result["c_defaults"] = scenario_c(cap, 5, 50)
    result["b_late_command"] = scenario_b_late(cap)
    result["b_inflight_command"] = scenario_b_inflight(cap)
    return result


# ----------------------------------------------------------------------------------------------------------- wire
def _handshake(port: int, path: str, *, rcvbuf: int | None = None) -> tuple[socket.socket, str, bytes]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if rcvbuf is not None:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
    sock.settimeout(10)
    sock.connect(("127.0.0.1", port))
    key = base64.b64encode(os.urandom(16)).decode()
    req = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    sock.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(1)
        if not chunk:
            break
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].decode(errors="replace")
    return sock, status, rest


def _send_text(sock: socket.socket, text: str) -> None:
    payload = text.encode()
    mask = os.urandom(4)
    header = bytes([0x81])
    n = len(payload)
    if n < 126:
        header += bytes([0x80 | n])
    elif n < 65536:
        header += bytes([0x80 | 126]) + struct.pack("!H", n)
    else:
        header += bytes([0x80 | 127]) + struct.pack("!Q", n)
    sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))


def _read_frame(sock: socket.socket) -> tuple[int, bytes]:
    def exact(n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("closed")
            data += chunk
        return data

    b0, b1 = exact(2)
    n = b1 & 0x7F
    if n == 126:
        n = struct.unpack("!H", exact(2))[0]
    elif n == 127:
        n = struct.unpack("!Q", exact(8))[0]
    return b0 & 0x0F, exact(n)


def run_wire(args: argparse.Namespace) -> dict:
    import uvicorn

    cap = _capture()
    result: dict = {"mode": "wire", "ws": args.ws, "cap": args.cap, "max_connections": args.max_connections, "hold": args.hold, "python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "modules": _modules(), "uvicorn": uvicorn.__version__}
    mgr = WebSocketManager(send_timeout_seconds=0.5, max_connections_per_ip=args.cap, max_connections=args.max_connections)
    app = _app(mgr)
    config = uvicorn.Config(app, host="127.0.0.1", port=0, ws=args.ws, log_config=None, lifespan="off")
    server = uvicorn.Server(config)
    holder: dict = {}

    def serve() -> None:
        loop = asyncio.new_event_loop()
        holder["loop"] = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    if not _until(lambda: server.started, limit=15.0):
        result["error"] = "server did not start"
        return result
    port = server.servers[0].sockets[0].getsockname()[1]
    result["port_ephemeral"] = port
    loop = holder["loop"]

    def stats() -> dict:
        st = mgr.transport_stats()
        return {"active": st.get("active_connections"), "pending": st.get("pending_connections"), "dropped": st.get("dropped_connections", "<absent>"), "send_failures": st.get("send_failures"), "per_ip": dict(mgr._per_ip_counts), "endpoint_counts": mgr.endpoint_counts(), "connection_count": mgr.connection_count}

    sock_a, status_a, _ = _handshake(port, "/ws/training", rcvbuf=4096)
    result["a_status"] = status_a
    _send_text(sock_a, json.dumps({"type": "hello"}))
    _until(lambda: mgr.transport_stats()["active_connections"] >= 1, limit=10.0)
    blob = "x" * 55000
    t0 = time.monotonic()
    sent = 0
    for _ in range(400):
        asyncio.run_coroutine_threadsafe(mgr.broadcast({"type": "metrics", "data": {"blob": blob}}), loop).result(timeout=15)
        sent += 1
        st = mgr.transport_stats()
        if st["active_connections"] == 0:
            break
    t_drop = time.monotonic()
    result["drop"] = {"broadcasts": sent, "seconds": round(t_drop - t0, 3), "stats": stats()}
    sock_b, status_b, rest_b = _handshake(port, "/ws/training")
    result["b_status"] = status_b
    if " 101 " in status_b + " ":
        try:
            sock_b.settimeout(5)
            op, payload = _read_frame(sock_b) if not rest_b else (1, rest_b)
            frame = json.loads(payload.decode()) if op == 1 else {}
            result["b_connection_established"] = {"type": frame.get("type"), "connections": (frame.get("data") or {}).get("connections")}
        except Exception as exc:  # noqa: BLE001 - recorded
            result["b_connection_established"] = {"error": f"{type(exc).__name__}: {exc}"}
    result["stats_with_b"] = stats()
    if args.hold:
        marks = []
        t_end = t_drop + args.hold
        while time.monotonic() < t_end:
            time.sleep(min(5.0, max(0.0, t_end - time.monotonic())))
            marks.append({"t_after_drop": round(time.monotonic() - t_drop, 1), **stats()})
        result["hold_marks"] = marks
        sock_c, status_c, _ = _handshake(port, "/ws/training")
        result["c_status_after_hold"] = status_c
        sock_c.close()
    result["asgi_exceptions"] = sum(1 for r in cap.records if r["logger"] == "uvicorn.error" and "Exception in ASGI application" in r["msg"])
    for s in (sock_b, sock_a):
        try:
            s.close()
        except OSError:  # a socket the server has already closed needs no close here
            pass
    _until(lambda: mgr.transport_stats().get("dropped_connections", 0) == 0 and not mgr._per_ip_counts, limit=10.0)
    result["stats_after_clients_gone"] = stats()
    server.should_exit = True
    thread.join(timeout=15)
    result["server_thread_alive"] = thread.is_alive()
    result["warnings"] = [r["msg"] for r in cap.records if r["logger"].startswith("juniper_service_core") and r["level"] == "WARNING"][:10]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    p_tc = sub.add_parser("testclient")
    p_tc.add_argument("--out", required=True)
    p_w = sub.add_parser("wire")
    p_w.add_argument("--ws", required=True, choices=["websockets", "websockets-sansio", "wsproto"])
    p_w.add_argument("--cap", type=int, required=True)
    p_w.add_argument("--max-connections", type=int, default=50)
    p_w.add_argument("--hold", type=float, default=0.0)
    p_w.add_argument("--out", required=True)
    args = parser.parse_args()
    result = run_testclient(args) if args.mode == "testclient" else run_wire(args)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=True, default=str)
        fh.write("\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
