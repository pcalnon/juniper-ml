"""
Code lens wire probe for ruling 23's three gaps: real uvicorn on 127.0.0.1 (port 0), a raw-socket client, any ws implementation.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Which juniper_service_core runs is whatever this interpreter imports (put a tree first on PYTHONPATH); the output
records each WebSocket module's path and sha256, so every cell names the code it measured. The server binds port 0
(the kernel picks an ephemeral port), and the client is a hand-written RFC 6455 client so the probe controls exactly
which frames are sent, when, and whether the client reads at all.

Scenarios (--scenario):
  a_unsendable      /ws/training x2: broadcast n=1, a datetime, a lone surrogate, n=4; then a third client resumes
                    from last_seq 1. Records every frame each client got, every close, transport_stats().
  a_deliverable     /ws/training x1: messages main delivers (plain, NaN/inf, odd keys, unicode, an oversized one with
                    a datetime that the chunker splits). Records the raw frame text (volatile fields normalised).
  b_<site>_<late>   /ws/control: the server closes at <site> (hb = heartbeat 1011, idle = idle timeout 1000, oversize
                    = 1009, malformed = 1003), then the client sends a <late> frame (pong | command). b_hb_inflight:
                    the heartbeat closes while a command runs. b_hb_then_idle: the heartbeat closes, the client stays
                    silent, the idle timeout fires. b_auth: a refused API key (pre-accept).
  c_stall           max_connections_per_ip=1: client A stops reading, 55 kB broadcasts until A is dropped; client B
                    from the same address; A's handler is watched for --hold seconds; then client C.
  c_take_close      as c_stall, but A resumes reading after the drop and answers the close; then client B.

Usage:
  python <this file> --ws {websockets,websockets-sansio,wsproto} --scenario NAME --out OUT.json [--hold SECONDS]
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime
import hashlib
import json
import logging
import math
import os
import socket
import sys
import threading
import time
import types

from fastapi import WebSocket


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:12]


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append({"logger": record.name, "level": record.levelname, "msg": record.getMessage()[:300], "exc": bool(record.exc_info)})


class Executor:
    commands = ("start", "stop", "pause", "resume", "reset", "set_params")

    def __init__(self, start_blocks: float = 0.0) -> None:
        self.executed: list[str] = []
        self.start_blocks = start_blocks
        self.lock = threading.Lock()

    def execute(self, command: str, params):  # noqa: ARG002 - the executor contract
        with self.lock:
            self.executed.append(command)
        if command == "start" and self.start_blocks:
            time.sleep(self.start_blocks)
        return {"ok": True}


class RawWS:
    """A minimal RFC 6455 client over one TCP socket."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.frames: list[dict] = []
        self.eof = False

    async def connect(self, path: str, *, rcvbuf: int | None = None, headers: str = "") -> int:
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if rcvbuf:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
        sock.setblocking(False)
        await loop.sock_connect(sock, ("127.0.0.1", self.port))
        self.reader, self.writer = await asyncio.open_connection(sock=sock, limit=1 << 22)
        key = base64.b64encode(os.urandom(16)).decode()
        req = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n{headers}\r\n"
        self.writer.write(req.encode())
        await self.writer.drain()
        head = await asyncio.wait_for(self.reader.readuntil(b"\r\n\r\n"), 10)
        return int(head.split(b" ", 2)[1])

    def send(self, opcode: int, payload: bytes) -> None:
        assert self.writer is not None
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            hdr = bytes([0x80 | opcode, 0x80 | n])
        elif n < 65536:
            hdr = bytes([0x80 | opcode, 0x80 | 126]) + n.to_bytes(2, "big")
        else:
            hdr = bytes([0x80 | opcode, 0x80 | 127]) + n.to_bytes(8, "big")
        if n:
            key = (mask * (n // 4 + 1))[:n]
            masked = (int.from_bytes(payload, "big") ^ int.from_bytes(key, "big")).to_bytes(n, "big")
        else:
            masked = b""
        self.writer.write(hdr + mask + masked)

    def send_text(self, obj) -> None:
        self.send(0x1, (obj if isinstance(obj, str) else json.dumps(obj)).encode())

    def send_close(self, code: int = 1000, reason: str = "") -> None:
        self.send(0x8, code.to_bytes(2, "big") + reason.encode())

    async def read_frame(self, timeout: float):
        assert self.reader is not None
        try:
            h = await asyncio.wait_for(self.reader.readexactly(2), timeout)
            n = h[1] & 0x7F
            if n == 126:
                n = int.from_bytes(await self.reader.readexactly(2), "big")
            elif n == 127:
                n = int.from_bytes(await self.reader.readexactly(8), "big")
            payload = await self.reader.readexactly(n)
        except asyncio.TimeoutError:
            return None
        except (asyncio.IncompleteReadError, ConnectionError):
            self.eof = True
            return None
        opcode = h[0] & 0x0F
        rec: dict = {"t": time.monotonic(), "opcode": opcode}
        if opcode == 0x1:
            rec["text"] = payload.decode("utf-8", "replace")
        elif opcode == 0x8:
            rec["close"] = [int.from_bytes(payload[:2], "big") if len(payload) >= 2 else None, payload[2:].decode("utf-8", "replace")]
        elif opcode == 0x9:
            self.send(0xA, payload)  # answer protocol pings while reading
        self.frames.append(rec)
        return rec

    async def read_for(self, seconds: float) -> list[dict]:
        out = []
        deadline = time.monotonic() + seconds
        while not self.eof:
            left = deadline - time.monotonic()
            if left <= 0:
                break
            rec = await self.read_frame(left)
            if rec is not None:
                out.append(rec)
        return out

    async def read_until_close(self, timeout: float):
        deadline = time.monotonic() + timeout
        while not self.eof:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            rec = await self.read_frame(left)
            if rec is not None and rec["opcode"] == 0x8:
                return rec
        return None

    def abort(self) -> None:
        if self.writer is not None:
            self.writer.transport.abort()


def texts(frames: list[dict]) -> list[dict]:
    out = []
    for f in frames:
        if f.get("opcode") == 0x1:
            try:
                out.append(json.loads(f["text"]))
            except ValueError:
                out.append({"unparsed": f["text"][:80]})
    return out


def closes(frames: list[dict]) -> list:
    return [f["close"] for f in frames if f.get("opcode") == 0x8]


class Harness:
    def __init__(self, impl: str, *, mgr_kwargs: dict | None = None, settings: dict | None = None, executor: Executor | None = None, api_key: str | None = None) -> None:
        from fastapi import FastAPI

        from juniper_service_core.websocket import control_stream, manager, training_stream

        self.modules = {m.__name__: {"file": m.__file__, "sha256": _sha(m.__file__)} for m in (manager, control_stream, training_stream)}
        self.impl = impl
        self.mgr = manager.WebSocketManager(**(mgr_kwargs or {}))
        base = dict(
            disable_ws_control_endpoint=False, ws_control_allowed_origins=None, ws_control_rate_limit_per_sec=10, ws_control_cooldown_rejections=10,
            ws_control_cooldown_window_sec=60, ws_control_cooldown_block_sec=300, ws_control_idle_timeout_sec=120, ws_heartbeat_interval_sec=30,
            ws_heartbeat_pong_timeout_sec=10, ws_resume_handshake_timeout_s=5.0, ws_initial_metrics_count=0,
        )
        base.update(settings or {})
        self.executor = executor or Executor()
        app = FastAPI()
        app.state.settings = types.SimpleNamespace(**base)
        app.state.ws_manager = self.mgr
        app.state.command_executor = self.executor
        app.state.lifecycle = None
        if api_key is not None:
            from juniper_service_core.security import APIKeyAuth

            app.state.api_key_auth = APIKeyAuth([api_key])
        self.records: list[dict] = []

        def wrap(handler, name):
            async def route(websocket: WebSocket) -> None:
                rec = {"handler": name, "t0": time.monotonic(), "t1": None, "outcome": None}
                self.records.append(rec)
                try:
                    await handler(websocket)
                    rec["outcome"] = "returned"
                except BaseException as exc:
                    rec["outcome"] = f"raised {type(exc).__name__}: {exc}"
                    raise
                finally:
                    rec["t1"] = time.monotonic()

            return route

        app.add_api_websocket_route("/ws/control", wrap(control_stream.control_stream_handler, "control"))
        app.add_api_websocket_route("/ws/training", wrap(training_stream.training_stream_handler, "training"))
        self.app = app
        self.capture = Capture()
        for name in ("uvicorn.error", "juniper_service_core"):
            lg = logging.getLogger(name)
            lg.addHandler(self.capture)
            lg.setLevel(logging.DEBUG)

    async def start(self) -> int:
        import uvicorn

        config = uvicorn.Config(self.app, host="127.0.0.1", port=0, ws=self.impl, log_config=None, lifespan="off", log_level="info", timeout_graceful_shutdown=2)
        self.server = uvicorn.Server(config)
        self.task = asyncio.create_task(self.server.serve())
        deadline = time.monotonic() + 10
        while not self.server.started:
            if time.monotonic() > deadline or self.task.done():
                raise RuntimeError("uvicorn did not start")
            await asyncio.sleep(0.01)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]
        return self.port

    async def stop(self) -> None:
        self.server.should_exit = True
        try:
            await asyncio.wait_for(self.task, 10)
        except (asyncio.TimeoutError, Exception):  # noqa: BLE001 - shutdown is best effort
            self.server.force_exit = True

    def asgi_exceptions(self) -> int:
        return sum(1 for r in self.capture.records if r["logger"].startswith("uvicorn") and "Exception in ASGI application" in r["msg"])

    async def wait_handler(self, idx: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if len(self.records) > idx and self.records[idx]["t1"] is not None:
                return True
            await asyncio.sleep(0.02)
        return False

    def base_result(self) -> dict:
        return {"impl": self.impl, "port": self.port, "port_ephemeral": self.port not in range(8050, 8060) and self.port != 8100 and self.port not in range(8200, 8212), "modules": self.modules}

    def handlers(self) -> list[dict]:
        out = []
        for r in self.records:
            out.append({"handler": r["handler"], "outcome": r["outcome"], "lifetime_s": None if r["t1"] is None else round(r["t1"] - r["t0"], 3)})
        return out

    def errors(self) -> list[dict]:
        return [r for r in self.capture.records if r["level"] in ("ERROR", "CRITICAL") or r["exc"]]


WHEN = datetime.datetime(2026, 11, 25, 12, 0, 0)


async def scenario_a_unsendable(impl: str, hold: float) -> dict:  # noqa: ARG001
    h = Harness(impl, mgr_kwargs={"send_timeout_seconds": 2.0})
    await h.start()
    res = h.base_result()
    clients = [RawWS(h.port), RawWS(h.port)]
    for c in clients:
        assert await c.connect("/ws/training") == 101
        c.send_text({"type": "hello"})
    for c in clients:
        await c.read_for(0.4)
    sid = texts(clients[0].frames)[0]["data"]["server_instance_id"]
    steps = []
    for label, msg in [
        ("n1", {"type": "metrics", "data": {"n": 1}}),
        ("datetime", {"type": "metrics", "data": {"when": WHEN}}),
        ("lone_surrogate", {"type": "metrics", "data": {"name": "caf\udce9"}}),
        ("n4", {"type": "metrics", "data": {"n": 4}}),
    ]:
        await h.mgr.broadcast(msg)
        for c in clients:
            await c.read_for(0.3)
        st = h.mgr.transport_stats()
        steps.append({"after": label, "current_seq": st["current_seq"], "replay_buffer_size": st["replay_buffer_size"], "active": st["active_connections"], "send_failures": st["send_failures"], "unserializable": st.get("unserializable_messages_total"), "dropped": st.get("dropped_connections")})
    res["steps"] = steps
    res["clients"] = [{"seqs": [t.get("seq") for t in texts(c.frames) if "seq" in t], "types": [t.get("type") for t in texts(c.frames)], "closes": closes(c.frames)} for c in clients]
    r = RawWS(h.port)
    assert await r.connect("/ws/training") == 101
    r.send_text({"type": "resume", "data": {"last_seq": 1, "server_instance_id": sid}})
    await r.read_for(1.5)
    res["resume_from_1"] = {"types": [t.get("type") for t in texts(r.frames)], "seqs": [t.get("seq") for t in texts(r.frames) if "seq" in t], "closes": closes(r.frames)}
    for c in [*clients, r]:
        c.abort()
    await asyncio.sleep(0.3)
    res["handlers"] = h.handlers()
    res["error_logs"] = h.errors()
    res["asgi_exceptions"] = h.asgi_exceptions()
    await h.stop()
    return res


def _normalise(text: str) -> str:
    obj = json.loads(text)
    for key in ("emitted_at_monotonic", "timestamp"):
        if key in obj:
            obj[key] = "<t>"
    if obj.get("type") == "chunked_message":
        obj["data"]["chunk_id"] = "<id>"
    return json.dumps(obj, sort_keys=False, ensure_ascii=False)


async def scenario_a_deliverable(impl: str, hold: float) -> dict:  # noqa: ARG001
    h = Harness(impl, mgr_kwargs={"send_timeout_seconds": 2.0})
    await h.start()
    res = h.base_result()
    c = RawWS(h.port)
    assert await c.connect("/ws/training") == 101
    c.send_text({"type": "hello"})
    await c.read_for(0.4)
    start = len(c.frames)
    messages = [
        {"type": "metrics", "data": {"n": 1, "loss": 0.25}},
        {"type": "metrics", "data": {"nan": math.nan, "inf": math.inf, "ninf": -math.inf, "big": 10**30, "neg0": -0.0}},
        {"type": "metrics", "data": {"keys": {1: "a", True: "b", None: "c", 2.5: "d"}, "tuple": (1, 2), "nested": [[[]]]}},
        {"type": "metrics", "data": {"uni": "café 日本 \U0001f389", "esc": 'a"b\\c\nd ', "ctl": "\x00\x1f"}},
        {"type": "metrics", "seq": "ignored", "emitted_at_monotonic": [1, 2], "data": {"own_seq_overwritten": True}},
        {"type": "metrics", "data": {"when": WHEN, "pad": "x" * 70_000}},
        {"type": "metrics", "data": {"pad": "é" * 40_000, "when": WHEN}},
        {"type": "metrics", "data": {"n": 8}},
    ]
    for msg in messages:
        await h.mgr.broadcast(msg)
        await c.read_for(0.3)
    got = [f["text"] for f in c.frames[start:] if f.get("opcode") == 0x1]
    res["frames_normalised_sha256"] = [hashlib.sha256(_normalise(t).encode()).hexdigest()[:16] for t in got]
    res["frame_count"] = len(got)
    res["seqs"] = [json.loads(t).get("seq") for t in got]
    res["closes"] = closes(c.frames)
    chunks = [json.loads(t) for t in got if json.loads(t).get("type") == "chunked_message"]
    groups: dict = {}
    for ch in chunks:
        groups.setdefault(ch["data"]["chunk_id"], []).append(ch)
    res["chunk_groups"] = [{"n": len(g), "payload_sha256": hashlib.sha256("".join(x["data"]["payload"] for x in sorted(g, key=lambda x: x["data"]["chunk_index"])).encode()).hexdigest()[:16]} for g in groups.values()]
    st = h.mgr.transport_stats()
    res["stats"] = {k: st.get(k) for k in ("current_seq", "send_failures", "unserializable_messages_total", "messages_chunked_total", "chunks_emitted_total", "active_connections")}
    c.abort()
    await asyncio.sleep(0.3)
    res["handlers"] = h.handlers()
    res["asgi_exceptions"] = h.asgi_exceptions()
    await h.stop()
    return res


async def scenario_b(impl: str, site: str, late: str, hold: float) -> dict:  # noqa: ARG001
    settings: dict = {"ws_control_idle_timeout_sec": 30, "ws_heartbeat_interval_sec": 3600, "ws_heartbeat_pong_timeout_sec": 3600}
    executor = Executor(start_blocks=1.5 if site == "hb_inflight" else 0.0)
    api_key = None
    if site in ("hb", "hb_inflight", "hb_then_idle"):
        settings.update(ws_heartbeat_interval_sec=0.3, ws_heartbeat_pong_timeout_sec=0.3)
    if site == "hb_then_idle":
        settings.update(ws_control_idle_timeout_sec=2.0)
    if site == "idle":
        settings.update(ws_control_idle_timeout_sec=0.5)
    if site == "auth":
        api_key = "probe-key-not-a-secret"
    h = Harness(impl, settings=settings, executor=executor, api_key=api_key)
    await h.start()
    res = h.base_result()
    res["site"], res["late"] = site, late
    c = RawWS(h.port)
    status = await c.connect("/ws/control")
    res["http_status"] = status
    if status != 101:
        await asyncio.sleep(0.3)
        res["handlers"] = h.handlers()
        res["asgi_exceptions"] = h.asgi_exceptions()
        c.abort()
        await h.stop()
        return res
    await c.read_for(0.1)  # connection_established
    if site == "hb_inflight":
        c.send_text({"command": "start", "command_id": "inflight-1"})
    elif site == "oversize":
        c.send_text("x" * (65536 + 1))
    elif site == "malformed":
        c.send_text("not-json")
    close = await c.read_until_close(15)
    res["server_close"] = None if close is None else close["close"]
    t_close = time.monotonic()
    if site == "hb_then_idle":
        # stay silent (do not answer the close) until past the idle timeout
        await c.read_for(3.0)
    elif late == "pong":
        c.send_text({"type": "pong"})
    elif late == "command":
        c.send_text({"command": "stop", "command_id": "late-1"})
    after = await c.read_for(1.0)
    res["frames_after_server_close"] = [f.get("text", f.get("close")) for f in after if f.get("opcode") in (0x1, 0x8)]
    if site == "hb_inflight":
        await asyncio.sleep(1.0)
    c.send_close(1000)
    await c.read_for(3.0)
    await h.wait_handler(0, 15)
    res["handler_end_after_server_close_s"] = None if not h.records or h.records[0]["t1"] is None else round(h.records[0]["t1"] - t_close, 3)
    res["executed"] = list(executor.executed)
    res["handlers"] = h.handlers()
    res["asgi_exceptions"] = h.asgi_exceptions()
    res["error_logs"] = h.errors()
    res["info_logs"] = [r["msg"] for r in h.capture.records if r["logger"].startswith("juniper") and r["level"] == "INFO" and "Command" in r["msg"]]
    c.abort()
    await h.stop()
    return res


async def scenario_c(impl: str, take_close: bool, hold: float) -> dict:
    h = Harness(impl, mgr_kwargs={"max_connections_per_ip": 1, "send_timeout_seconds": 0.5})
    await h.start()
    res = h.base_result()
    a = RawWS(h.port)
    assert await a.connect("/ws/training", rcvbuf=4096) == 101
    a.send_text({"type": "hello"})
    await a.read_for(0.4)
    t0 = time.monotonic()
    n = 0
    while h.mgr.connection_count and n < 200:
        await h.mgr.broadcast({"type": "metrics", "data": {"i": n, "pad": "x" * 55_000}})
        n += 1
    t_drop = time.monotonic()
    st = h.mgr.transport_stats()
    res["drop"] = {"after_s": round(t_drop - t0, 3), "broadcasts": n, "active": st["active_connections"], "dropped": st.get("dropped_connections"), "per_ip": dict(h.mgr._per_ip_counts), "endpoint_training": h.mgr.endpoint_counts().get("training"), "a_handler_running": h.records[0]["t1"] is None}
    if take_close:
        close = await a.read_until_close(30)
        res["a_close"] = None if close is None else close["close"]
        a.send_close(1011)
        ended = await h.wait_handler(0, 15)
        res["a_handler_end_after_drop_s"] = round(h.records[0]["t1"] - t_drop, 3) if ended else None
    b = RawWS(h.port)
    status_b = await b.connect("/ws/training")
    res["b_status_while_a_open"] = status_b
    res["b_when_s_after_drop"] = round(time.monotonic() - t_drop, 3)
    if status_b == 101:
        b.send_text({"type": "hello"})
        await b.read_for(0.4)
        ce = [t for t in texts(b.frames) if t.get("type") == "connection_established"]
        res["b_connection_established_connections"] = ce[0]["data"]["connections"] if ce else None
    st = h.mgr.transport_stats()
    res["with_b"] = {"active": st["active_connections"], "dropped": st.get("dropped_connections"), "per_ip": dict(h.mgr._per_ip_counts), "endpoint_training": h.mgr.endpoint_counts().get("training"), "handlers_running": sum(1 for r in h.records if r["t1"] is None and r["handler"] == "training")}
    if not take_close:
        ended = await h.wait_handler(0, hold)
        res["hold_s"] = hold
        res["a_handler_end_after_drop_s"] = round(h.records[0]["t1"] - t_drop, 3) if ended else None
        cc = RawWS(h.port)
        res["c_status_after_hold"] = await cc.connect("/ws/training")
        res["c_when_s_after_drop"] = round(time.monotonic() - t_drop, 3)
        st = h.mgr.transport_stats()
        res["at_c"] = {"active": st["active_connections"], "dropped": st.get("dropped_connections"), "per_ip": dict(h.mgr._per_ip_counts), "endpoint_training": h.mgr.endpoint_counts().get("training")}
        cc.abort()
    for cl in (a, b):
        cl.abort()
    await asyncio.sleep(0.5)
    st = h.mgr.transport_stats()
    res["after_all_gone"] = {"active": st["active_connections"], "dropped": st.get("dropped_connections"), "per_ip": dict(h.mgr._per_ip_counts), "endpoint_training": h.mgr.endpoint_counts().get("training")}
    res["handlers"] = h.handlers()
    res["asgi_exceptions"] = h.asgi_exceptions()
    await h.stop()
    return res


async def run(args) -> dict:
    s = args.scenario
    if s == "a_unsendable":
        return await scenario_a_unsendable(args.ws, args.hold)
    if s == "a_deliverable":
        return await scenario_a_deliverable(args.ws, args.hold)
    if s.startswith("b_"):
        parts = s[2:].rsplit("_", 1)
        if s in ("b_hb_inflight", "b_hb_then_idle", "b_auth"):
            return await scenario_b(args.ws, s[2:], "none", args.hold)
        return await scenario_b(args.ws, parts[0], parts[1], args.hold)
    if s == "c_stall":
        return await scenario_c(args.ws, False, args.hold)
    if s == "c_take_close":
        return await scenario_c(args.ws, True, args.hold)
    raise SystemExit(f"unknown scenario {s}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--ws", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--hold", type=float, default=45.0)
    args = parser.parse_args()
    import uvicorn
    import websockets

    started = time.monotonic()
    result = asyncio.run(run(args))
    result.update({"scenario": args.scenario, "python": sys.version.split()[0], "executable": sys.executable, "base_prefix": sys.base_prefix, "uvicorn": uvicorn.__version__, "websockets": getattr(websockets, "__version__", "?"), "wall_s": round(time.monotonic() - started, 2)})
    try:
        import wsproto

        result["wsproto"] = getattr(wsproto, "__version__", "installed")
    except ImportError:
        result["wsproto"] = None
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
