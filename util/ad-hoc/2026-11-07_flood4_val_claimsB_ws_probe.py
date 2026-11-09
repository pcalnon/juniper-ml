"""
Probe the flood-4 docs carrier's #2462 / #2444 claims (WS frame caps, training resume, connection caps) against main's juniper-service-core.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (Claude Code validator, flood-4 claims lens slice B, ws fork)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier validation; drafts juniper-ml#2462, #2444 (tests #2458, #2441)

Run with PYTHONPATH=<this worktree>/juniper-service-core and an interpreter that has fastapi,
uvicorn and websockets. Part A reads a downloaded uvicorn wheel as a zip (never imported). Part E
starts a real uvicorn server on an ephemeral 127.0.0.1 port, in-process, and stops it.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import socket
import sys
import threading
import time
import types
import zipfile
from collections import deque

from fastapi import WebSocketDisconnect


def part_a(wheel: str) -> None:
    print("== A: uvicorn wheel static read:", wheel)
    names = [
        "uvicorn/config.py",
        "uvicorn/protocols/websockets/auto.py",
        "uvicorn/protocols/websockets/websockets_impl.py",
        "uvicorn/protocols/websockets/websockets_sansio_impl.py",
        "uvicorn/protocols/websockets/wsproto_impl.py",
    ]
    needles = ("ws_max_size: int", "403", "FORBIDDEN", "AutoWebSocketsProtocol =", "import websockets", "import wsproto", "max_size=self.config")
    with zipfile.ZipFile(wheel) as z:
        for name in names:
            try:
                text = z.read(name).decode("utf-8")
            except KeyError:
                print(f"  {name}: ABSENT")
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if any(n in line for n in needles):
                    print(f"  {name}:{i}: {line.strip()}")


def _exact_json(fields: dict, size: int, pad_char: str = "a", ensure_ascii: bool = True) -> str:
    skeleton = {**fields, "pad": ""}
    base = json.dumps(skeleton, separators=(",", ":"), ensure_ascii=ensure_ascii)
    skeleton["pad"] = pad_char * (size - len(base))
    raw = json.dumps(skeleton, separators=(",", ":"), ensure_ascii=ensure_ascii)
    assert len(raw) == size, (len(raw), size)
    return raw


class _TextWS:
    def __init__(self, incoming: list[str]) -> None:
        self._incoming = deque(incoming)
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def send_bytes(self, data: bytes) -> None:
        self.sent.append({"bytes": len(data)})

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(1000)
        return self._incoming.popleft()

    async def receive(self) -> dict:
        if not self._incoming:
            raise WebSocketDisconnect(1000)
        item = self._incoming.popleft()
        return item if isinstance(item, dict) else {"text": item}


class _Exec:
    commands = ("start",)

    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(self, command, params):
        self.calls.append(command)
        return {"ok": True}


async def part_b_control() -> None:
    from juniper_service_core.websocket import control_stream as cs
    from juniper_service_core.websocket.control_security import LeakyBucket

    print("== B1: /ws/control text cap (65536 characters)")
    for label, size, pad, ascii_ in (("ascii-65536", 65536, "a", True), ("e-acute-65536", 65536, "é", False), ("ascii-65537", 65537, "a", True)):
        raw = _exact_json({"command": "start"}, size, pad, ascii_)
        ex = _Exec()
        bucket = LeakyBucket()
        before = bucket._tokens
        ws = _TextWS([raw, json.dumps({"command": "start"})])
        try:
            await cs._control_recv_loop(ws, ex, {"start"}, bucket, asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")
            ended = "returned"
        except WebSocketDisconnect:
            ended = "WebSocketDisconnect (queue drained)"
        print(f"  {label}: chars={len(raw)} utf8_bytes={len(raw.encode('utf-8'))} calls={ex.calls} closed={ws.closed} ended={ended} tokens_before={before} tokens_after={round(bucket._tokens, 3)} remaining_unread={len(ws._incoming)}")
        print(f"    sent={[ (m.get('type'), m.get('data', {}).get('status'), m.get('data', {}).get('error')) for m in ws.sent]}")
    for label, size in (("pong-65536", 65536), ("pong-65537", 65537)):
        raw = _exact_json({"type": "pong"}, size)
        ev = asyncio.Event()
        bucket = LeakyBucket()
        ws = _TextWS([raw])
        try:
            await cs._control_recv_loop(ws, None, {"start"}, bucket, ev, idle_timeout=0, client_ip="1.2.3.4")
            ended = "returned"
        except WebSocketDisconnect:
            ended = "WebSocketDisconnect (queue drained)"
        print(f"  {label}: pong_event_set={ev.is_set()} closed={ws.closed} ended={ended} tokens={round(bucket._tokens, 3)} sent={[m.get('data', {}).get('error') for m in ws.sent]}")


async def part_b_worker() -> None:
    from juniper_service_core.websocket import worker_stream as wsm
    from juniper_service_core.workers import JsonTaskProtocol, WorkerCoordinator, WorkerRegistry

    print("== B2: /ws/workers registration + message loop (65536 characters)")
    for size in (65536, 65537):
        reg = WorkerRegistry()
        raw = _exact_json({"type": "register", "worker_id": "w1", "capabilities": {}}, size)
        ws = _TextWS([raw])
        wid = await wsm._handle_registration(ws, reg)
        print(f"  register-{size}: wid={wid} closed={ws.closed} sent={[ (m.get('type'), m.get('error')) for m in ws.sent]}")
    for size in (65536, 65537):
        reg = WorkerRegistry()
        coord = WorkerCoordinator(reg, JsonTaskProtocol())
        ws = _TextWS([json.dumps({"type": "register", "worker_id": "w1", "capabilities": {}}), _exact_json({"type": "heartbeat"}, size), json.dumps({"type": "heartbeat"})])
        wid = await wsm._handle_registration(ws, reg)
        ws.sent.clear()
        try:
            await wsm._message_loop(ws, wid, reg, coord)
        except WebSocketDisconnect:
            pass  # the scripted queue drained: the expected end of this arm
        print(f"  loop-heartbeat-{size}: closed={ws.closed} sent={[ (m.get('type'), m.get('error')) for m in ws.sent]}")
    reg = WorkerRegistry()
    coord = WorkerCoordinator(reg, JsonTaskProtocol())
    ws = _TextWS([json.dumps({"type": "register", "worker_id": "w1", "capabilities": {}}), "[1, 2]"])
    wid = await wsm._handle_registration(ws, reg)
    try:
        await wsm._message_loop(ws, wid, reg, coord)
        print("  loop-json-array: returned")
    except WebSocketDisconnect:
        print("  loop-json-array: WebSocketDisconnect")
    except Exception as exc:  # noqa: BLE001 - the probe records what escapes
        print(f"  loop-json-array: escapes {type(exc).__name__}: {exc}")

    print("== B3: binary attachment caps (constants patched to 10 bytes for the boundary arms)")
    saved = (wsm._MAX_BINARY_SIZE, wsm._MAX_TOTAL_BINARY_SIZE)
    print(f"  shipped: _MAX_BINARY_SIZE={wsm._MAX_BINARY_SIZE} _MAX_TOTAL_BINARY_SIZE={wsm._MAX_TOTAL_BINARY_SIZE} _MAX_ATTACHMENTS={wsm._MAX_ATTACHMENTS} 100MiB={100 * 1024 * 1024} 7x16MiB={7 * 16 * 1024 * 1024} 6x16MiB={6 * 16 * 1024 * 1024}")
    wsm._MAX_BINARY_SIZE = 10
    wsm._MAX_TOTAL_BINARY_SIZE = 10
    try:
        for label, sizes in (("one-frame-10", [10]), ("one-frame-11", [11]), ("total-6+4", [6, 4]), ("total-6+5", [6, 5])):
            reg = WorkerRegistry()
            proto = JsonTaskProtocol()
            names = [f"a{i}" for i in range(len(sizes))]
            proto.result_attachments = lambda msg, _n=names: list(_n)
            coord = WorkerCoordinator(reg, proto)
            reg.register("worker-x", {}, client_name="w")
            (tid,) = coord.submit_tasks("r1", [{"p": 1}])
            assert coord.get_next_assignment("worker-x") is not None
            ws = _TextWS([{"bytes": b"x" * s} for s in sizes])
            await wsm._handle_task_result(ws, "worker-x", {"type": "task_result", "task_id": tid}, coord)
            task = coord._pending_tasks[tid]
            print(f"  {label}: sent={[ (m.get('type'), m.get('error') or m.get('status')) for m in ws.sent]} assigned_worker_id={task.assigned_worker_id} completed={task.completed} active_task_id={reg.get('worker-x').active_task_id}")
    finally:
        wsm._MAX_BINARY_SIZE, wsm._MAX_TOTAL_BINARY_SIZE = saved
    for n in (32, 33):
        reg = WorkerRegistry()
        proto = JsonTaskProtocol()
        names = [f"a{i}" for i in range(n)]
        proto.result_attachments = lambda msg, _n=names: list(_n)
        coord = WorkerCoordinator(reg, proto)
        reg.register("worker-x", {}, client_name="w")
        (tid,) = coord.submit_tasks("r1", [{"p": 1}])
        coord.get_next_assignment("worker-x")
        ws = _TextWS([{"bytes": b"x"} for _ in range(n)])
        await wsm._handle_task_result(ws, "worker-x", {"type": "task_result", "task_id": tid}, coord)
        print(f"  attachments-{n}: frames_left_unread={len(ws._incoming)} sent={[ (m.get('type'), m.get('error') or m.get('status')) for m in ws.sent]}")


class _ConnWS:
    def __init__(self, client=("1.2.3.4", 5000)) -> None:
        self.client = client
        self.sent: list[dict] = []
        self.accepted = False
        self.closed = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(f"{record.name} {record.levelname} {record.getMessage()}")


async def part_c_manager() -> None:
    from juniper_service_core.websocket.manager import ReplayOutOfRange, WebSocketManager

    print("== C1: WebSocketManager defaults")
    sig = inspect.signature(WebSocketManager.__init__)
    print("  ", {k: v.default for k, v in sig.parameters.items() if k != "self"})

    print("== C2: replay_since")
    m = WebSocketManager()
    print(f"  first seq on a fresh manager: {m._assign_seq_and_buffer({'type': 'x'})['seq']}")
    for label, mgr, seqs, asks in (
        ("empty", WebSocketManager(), 0, [0, -1, 1]),
        ("disabled", WebSocketManager(max_replay_buffer_size=0), 3, [0, 3]),
        ("size2-after-5", WebSocketManager(max_replay_buffer_size=2), 5, [2, 3, 4, 5, 99]),
    ):
        for _ in range(seqs):
            mgr._assign_seq_and_buffer({"type": "metrics"})
        for ask in asks:
            try:
                out = [e["seq"] for e in mgr.replay_since(ask)]
            except ReplayOutOfRange as exc:
                out = f"ReplayOutOfRange({exc})"
            print(f"  {label} replay_since({ask}) -> {out}")

    print("== C3: chunking at the defaults")
    mgr = WebSocketManager()
    overhead = len(json.dumps({"type": "metrics", "data": {"blob": ""}}, default=str))
    for target in (60000, 60001):
        msg = {"type": "metrics", "data": {"blob": "x" * (target - overhead)}}
        out = mgr._maybe_chunk_message(msg)
        print(f"  json.dumps len={len(json.dumps(msg, default=str))} -> {len(out)} frame(s); payload lens={[len(c['data']['payload']) for c in out if c.get('type') == 'chunked_message']}; rejoin_ok={''.join(c['data']['payload'] for c in out if c.get('type') == 'chunked_message') == json.dumps(msg, default=str) if len(out) > 1 else 'n/a'}")
    big_chunk = {"type": "chunked_message", "data": {"payload": "y" * 70000}}
    print(f"  already chunked_message, 70000-char payload -> {len(mgr._maybe_chunk_message(big_chunk))} frame(s)")
    off = WebSocketManager(max_message_size_bytes=0)
    print(f"  max_message_size_bytes=0, 200000-char blob -> {len(off._maybe_chunk_message({'type': 'm', 'blob': 'z' * 200000}))} frame(s)")
    neg = WebSocketManager(max_message_size_bytes=-1)
    print(f"  max_message_size_bytes=-1, 200000-char blob -> {len(neg._maybe_chunk_message({'type': 'm', 'blob': 'z' * 200000}))} frame(s)")
    nonser = {"type": "metrics", "data": {"obj": {1, 2}}}
    print(f"  non-JSON value measured via default=str: {mgr._maybe_chunk_message(nonser) == [nonser]}")

    print("== C4: connection caps + _source_ip")
    h = _ListHandler()
    lg = logging.getLogger("juniper_service_core.websocket")
    lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    try:
        mgr = WebSocketManager(max_connections=2)
        a, p = _ConnWS(("1.1.1.1", 1)), _ConnWS(("2.2.2.2", 2))
        await mgr.connect(a)
        await mgr.connect_pending(p)
        blocked = _ConnWS(("3.3.3.3", 3))
        r = await mgr.connect_pending(blocked)
        print(f"  global cap with 1 active + 1 pending: connect_pending -> {r} accepted={blocked.accepted} closed={blocked.closed} endpoint_counts={mgr.endpoint_counts()}")
        await mgr.disconnect(p)
        r2 = await mgr.connect_pending(blocked)
        print(f"  after disconnect(pending): connect_pending -> {r2}")
        mgr = WebSocketManager()
        results = []
        for client in (None, (), ("", 1), None, (), ("", 2)):
            w = _ConnWS(client)
            results.append((repr(client), await mgr.connect_pending(w), w.closed))
        named = _ConnWS(("9.9.9.9", 1))
        results.append(("named", await mgr.connect_pending(named), named.closed))
        print(f"  six address-less sockets + one named at defaults: {results}")
        print(f"  per-ip counts: {mgr._per_ip_counts}")
        for client in (None, (), ("", 1), 5, ("h", 1)):
            w = _ConnWS(client)
            print(f"  _source_ip({client!r}) -> {mgr._source_ip(w)!r}")
    finally:
        lg.removeHandler(h)
    print("  log records:")
    for line in h.records:
        if "rejected" in line:
            print("   ", line)


class _AppState(types.SimpleNamespace):
    pass


class _HandlerWS:
    def __init__(self, app, incoming: list[str], client=("5.5.5.5", 1)) -> None:
        self.app = app
        self.client = client
        self.headers: dict = {}
        self._incoming = deque(incoming)
        self.sent: list[dict] = []
        self.accepted = False
        self.closed = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(1000)
        return self._incoming.popleft()


class _Monitor:
    def get_state(self):
        return {"status": "idle"}


class _Lifecycle:
    monitor = _Monitor()

    def get_status(self):
        return {"status": "STOPPED"}

    def get_metrics_history(self, count=100):
        return [{"epoch": 1}]


async def part_d_training_handler() -> None:
    from juniper_service_core.websocket.manager import WebSocketManager
    from juniper_service_core.websocket.training_stream import training_stream_handler

    print("== D: training_stream_handler resume flows")
    cases = {
        "out_of_range(empty buffer, last_seq 5)": lambda sid: json.dumps({"type": "resume", "data": {"last_seq": 5, "server_instance_id": sid}}),
        "ok(empty buffer, last_seq 0)": lambda sid: json.dumps({"type": "resume", "data": {"last_seq": 0, "server_instance_id": sid}}),
        "malformed(no server_instance_id)": lambda sid: json.dumps({"type": "resume", "data": {"last_seq": 0}}),
        "restarted(wrong id)": lambda sid: json.dumps({"type": "resume", "data": {"last_seq": 0, "server_instance_id": "other"}}),
        "non-json": lambda sid: "not json",
        "data-not-object": lambda sid: json.dumps({"type": "resume", "data": 7}),
    }
    for label, build in cases.items():
        mgr = WebSocketManager()
        app = types.SimpleNamespace(state=_AppState(ws_manager=mgr, lifecycle=_Lifecycle(), settings=None))
        ws = _HandlerWS(app, [build(mgr.server_instance_id)])
        await training_stream_handler(ws)
        types_sent = [(m.get("type"), (m.get("data") or {}).get("reason") if m.get("type") == "resume_failed" else None) for m in ws.sent]
        print(f"  {label}: closed={ws.closed} sent={types_sent} per_ip_after={mgr._per_ip_counts} active={len(mgr._active_connections)} pending={len(mgr._pending_connections)}")


async def part_f_no_active_client() -> None:
    from juniper_service_core.websocket.manager import WebSocketManager

    print("== F: broadcasts while no socket is active (sole-client reconnect)")
    mgr = WebSocketManager()
    client = _ConnWS(("7.7.7.7", 1))
    await mgr.connect(client)
    for i in range(3):
        await mgr.broadcast({"type": "metrics", "data": {"i": i}})
    last_seen = max(m.get("seq", 0) for m in client.sent)
    await mgr.disconnect(client)
    for i in range(3, 5):
        await mgr.broadcast({"type": "metrics", "data": {"i": i}})
    again = _ConnWS(("7.7.7.7", 2))
    await mgr.connect_pending(again)
    await mgr.broadcast({"type": "metrics", "data": {"i": 5}})
    replay = mgr.replay_since(last_seen)
    print(f"  client saw seqs up to {last_seen}; 3 broadcasts made while it was gone or pending; current_seq={mgr.current_seq}; replay_since({last_seen}) -> {len(replay)} messages (resume_ok, replayed_count {len(replay)})")


def part_e_live(port_hint: int, ws_impl: str = "auto") -> None:
    import uvicorn
    import websockets
    from fastapi import FastAPI
    from websockets.asyncio.client import connect

    from juniper_service_core.websocket.manager import WebSocketManager
    from juniper_service_core.websocket.router import build_websocket_router, build_worker_router
    from juniper_service_core.websocket.worker_stream import attach_worker_pool
    from juniper_service_core.workers import JsonTaskProtocol, WorkerCoordinator, WorkerRegistry

    print(f"== E: live uvicorn {uvicorn.__version__} + websockets {websockets.__version__}")
    app = FastAPI()
    app.include_router(build_websocket_router())
    app.include_router(build_worker_router())
    settings = types.SimpleNamespace(disable_ws_control_endpoint=True)
    app.state.settings = settings
    app.state.ws_manager = WebSocketManager(max_connections=0)
    registry = WorkerRegistry()
    attach_worker_pool(app, registry=registry, coordinator=WorkerCoordinator(registry, JsonTaskProtocol()))

    h = _ListHandler()
    for name in ("uvicorn.error", "uvicorn.access", "juniper_service_core"):
        lg = logging.getLogger(name)
        lg.addHandler(h)
        lg.setLevel(logging.INFO)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", port_hint))
    port = sock.getsockname()[1]
    config = uvicorn.Config(app, log_config=None, lifespan="off", ws=ws_impl)
    print(f"  Config.ws={config.ws!r} Config.ws_max_size={config.ws_max_size}")
    server = uvicorn.Server(config)
    t = threading.Thread(target=lambda: asyncio.run(server.serve(sockets=[sock])), daemon=True)
    t.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)

    async def client() -> None:
        base = f"ws://127.0.0.1:{port}"
        for path in ("/ws/control", "/ws/training"):
            mark = len(h.records)
            try:
                async with connect(base + path):
                    print(f"  {path}: CONNECTED (unexpected)")
            except Exception as exc:  # noqa: BLE001 - record the handshake failure shape
                status = getattr(getattr(exc, "response", None), "status_code", None)
                print(f"  {path}: {type(exc).__name__} status={status}")
            await asyncio.sleep(0.2)
            for line in h.records[mark:]:
                print(f"    log: {line}")
        settings.disable_ws_control_endpoint = False
        mark = len(h.records)
        async with connect(base + "/ws/control", max_size=None) as ws:
            first = json.loads(await ws.recv())
            await ws.send("a" * (16 * 1024 * 1024 + 1))
            frames = []
            try:
                while True:
                    frames.append(await asyncio.wait_for(ws.recv(), timeout=5))
            except Exception as exc:  # noqa: BLE001
                print(f"  /ws/control 16MiB+1 text: first={first.get('type')} later_frames={frames} -> {type(exc).__name__} close_code={ws.close_code} reason={ws.close_reason!r}")
        await asyncio.sleep(0.2)
        for line in h.records[mark:]:
            print(f"    log: {line}")
        mark = len(h.records)
        async with connect(base + "/ws/workers", max_size=None) as ws:
            await ws.recv()
            await ws.send(json.dumps({"type": "register", "worker_id": "w1", "capabilities": {}}))
            ack = json.loads(await ws.recv())
            print(f"  /ws/workers registered: {ack.get('type')} workers={registry.worker_count}")
            await ws.send(b"\x00" * (16 * 1024 * 1024 + 1))
            frames = []
            try:
                while True:
                    frames.append(await asyncio.wait_for(ws.recv(), timeout=5))
            except Exception as exc:  # noqa: BLE001
                print(f"  /ws/workers 16MiB+1 binary: later_frames={frames} -> {type(exc).__name__} close_code={ws.close_code} reason={ws.close_reason!r}")
        await asyncio.sleep(0.3)
        print(f"  /ws/workers after: workers={registry.worker_count}")
        for line in h.records[mark:]:
            print(f"    log: {line}")

    try:
        asyncio.run(client())
    finally:
        server.should_exit = True
        t.join(timeout=10)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wheel", required=True)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--live-only", action="store_true")
    ap.add_argument("--ws-impl", default="auto")
    args = ap.parse_args()
    if not args.live_only:
        part_a(args.wheel)
        asyncio.run(part_b_control())
        asyncio.run(part_b_worker())
        asyncio.run(part_c_manager())
        asyncio.run(part_d_training_handler())
        asyncio.run(part_f_no_active_client())
    if args.live or args.live_only:
        part_e_live(0, args.ws_impl)
    print("== done", sys.version.split()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
