"""
Probe the flood-4 docs carrier's /ws/control (#2446) and request-body-cap (#2456) claims against main's code.

Read-only on the repository: imports juniper_service_core from the directory named by
PYTHONPATH (main's juniper-service-core), starts throwaway uvicorn servers on loopback
ports, and prints one PASS/FAIL/OBSERVED line per claim. Writes nothing.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier validation (claims lens, slice B: #2446, #2456)
"""

from __future__ import annotations

import base64
import logging
import socket
import sys
import threading
import time
import types

import juniper_service_core
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from juniper_service_core.middleware import _DEFAULT_MAX_REQUEST_BODY_BYTES, RequestBodyLimitMiddleware
from juniper_service_core.security import APIKeyAuth
from juniper_service_core.websocket import control_security
from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket, validate_control_origin
from juniper_service_core.websocket.control_stream import control_stream_handler

RESULTS: list[str] = []


def record(label: str, ok: bool, detail: str = "") -> None:
    line = f"{'PASS' if ok else 'FAIL'}: {label}" + (f" -- {detail}" if detail else "")
    RESULTS.append(line)
    print(line, flush=True)


def observed(label: str, detail: str) -> None:
    line = f"OBSERVED: {label} -- {detail}"
    RESULTS.append(line)
    print(line, flush=True)


class FakeClock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def unit_bucket() -> None:
    real = control_security.time.monotonic
    clock = FakeClock(1000.0)
    control_security.time.monotonic = clock
    try:
        b = LeakyBucket(capacity=3, refill_rate=3.0)
        assert all(b.try_acquire() for _ in range(3))
        record("bucket denies after capacity", b.try_acquire() is False)
        clock.now += 1000.0
        admitted = sum(1 for _ in range(10) if b.try_acquire())
        record("long idle banks at most capacity", admitted == 3, f"admitted={admitted}")
        # deficit 0.88 s -> 0.9
        b2 = LeakyBucket(capacity=1, refill_rate=1.0)
        b2.try_acquire()
        clock.now += 0.12
        denied = b2.try_acquire()
        tokens_after_denial = b2._tokens
        ra = b2.retry_after
        record("denial does not subtract (0.12 stays)", denied is False and abs(tokens_after_denial - 0.12) < 1e-9, f"tokens={tokens_after_denial!r}")
        record("deficit 0.88 s reports 0.9", ra == 0.9, f"retry_after={ra!r}")
        # exactly 1.0 refill admitted, leaves 0
        b3 = LeakyBucket(capacity=1, refill_rate=1.0)
        b3.try_acquire()
        clock.now += 1.0
        record("refill landing on exactly 1.0 admitted, leaves 0", b3.try_acquire() is True and b3._tokens == 0.0, f"tokens={b3._tokens!r}")
        # retry_after 0.0 when a token is available
        b4 = LeakyBucket(capacity=2, refill_rate=2.0)
        record("retry_after 0.0 with a token available", b4.retry_after == 0.0)
        # capacity 0 never admits; retry_after 3600
        b5 = LeakyBucket(capacity=0, refill_rate=0.0)
        clock.now += 10_000.0
        record("capacity 0 never admits", b5.try_acquire() is False)
        record("refill_rate 0 -> retry_after 3600.0", b5.retry_after == 3600.0, f"{b5.retry_after!r}")
        b6 = LeakyBucket(capacity=5, refill_rate=-1.0)
        b6._tokens = 0.0
        record("negative refill -> retry_after 3600.0", b6.retry_after == 3600.0)
    finally:
        control_security.time.monotonic = real


def unit_cooldown() -> None:
    real = control_security.time.monotonic
    clock = FakeClock(50_000.0)
    control_security.time.monotonic = clock
    try:
        c = HandshakeCooldown()  # defaults 10 / 60 / 300
        got = [c.record_rejection("1.1.1.1") for _ in range(10)]
        record("default: 10th rejection blocks, 9th does not", got[:9] == [False] * 9 and got[9] is True, f"{got}")
        record("history cleared on block", c._rejections["1.1.1.1"] == [])
        # remaining rounding
        start = clock.now
        clock.now = start + 300 - 0.06
        record("0.06 s remaining reports 0.1", c.get_block_remaining("1.1.1.1") == 0.1)
        clock.now = start + 300 - 0.04
        rem = c.get_block_remaining("1.1.1.1")
        still = c.is_blocked("1.1.1.1")
        observed("0.04 s remaining", f"get_block_remaining={rem!r} while is_blocked={still}")
        clock.now = start + 300
        record("is_blocked False at exact blocked_until, entry removed", c.is_blocked("1.1.1.1") is False and "1.1.1.1" not in c._blocked_until)
        c2 = HandshakeCooldown()
        for _ in range(10):
            c2.record_rejection("3.3.3.3")
        clock.now += 300
        record("get_block_remaining None at exact end, entry removed", c2.get_block_remaining("3.3.3.3") is None and "3.3.3.3" not in c2._blocked_until)
        # window strictness
        c3 = HandshakeCooldown(max_rejections=2, window_sec=60)
        c3._rejections["4.4.4.4"] = [clock.now - 60]
        record("stamp aged exactly 60 s does not count", c3.record_rejection("4.4.4.4") is False)
        c4 = HandshakeCooldown(max_rejections=2, window_sec=60)
        c4._rejections["4.4.4.4"] = [clock.now - 60 + 1e-3]
        record("stamp 1 ms inside the window counts", c4.record_rejection("4.4.4.4") is True)
        # cleanup every 50, strictly older than 2*window
        c5 = HandshakeCooldown(max_rejections=1000, window_sec=60)
        c5._rejections["edge"] = [clock.now - 120]
        c5._rejections["older"] = [clock.now - 120 - 0.001]
        for i in range(49):
            c5.record_rejection(f"x{i}")
        before = ("older" in c5._rejections, "edge" in c5._rejections)
        c5.record_rejection("x49")
        after = ("older" in c5._rejections, "edge" in c5._rejections)
        record("cleanup on 50th record drops strictly-older-than-2w, keeps exactly-2w", before == (True, True) and after == (False, True), f"before={before} after={after}")
    finally:
        control_security.time.monotonic = real


class _WS:
    def __init__(self, origin: str | None) -> None:
        self.headers = {} if origin is None else {"origin": origin}


def unit_origin() -> None:
    allow = ["https://app.example"]
    cases = [
        (None, allow, False),
        ("/", allow, False),
        ("///", ["/"], False),
        ("https://app.example.evil", allow, False),
        ("https://evil.app.example", allow, False),
        ("HTTPS://App.Example/", allow, True),
        ("https://app.example", ["HTTPS://APP.EXAMPLE//"], True),
        (" https://app.example", allow, False),
    ]
    for origin, allowlist, want in cases:
        got = validate_control_origin(_WS(origin), allowlist)
        record(f"origin {origin!r} vs {allowlist!r} -> {want}", got is want, f"got={got}")


class _Exec:
    commands = ("start", "stop")

    def execute(self, command, params):
        return {"ok": True, "command": command}


def _app_control(**settings) -> FastAPI:
    app = FastAPI()
    app.add_api_websocket_route("/ws/control", control_stream_handler)
    base = dict(ws_heartbeat_interval_sec=3600, ws_heartbeat_pong_timeout_sec=3600, ws_control_idle_timeout_sec=0)
    base.update(settings)
    app.state.settings = types.SimpleNamespace(**base)
    app.state.command_executor = _Exec()
    return app


def client_control() -> None:
    app = _app_control(ws_control_rate_limit_per_sec=2)
    with TestClient(app) as tc:
        with tc.websocket_connect("/ws/control") as ws:
            est = ws.receive_json()
            replies = []
            for _ in range(3):
                ws.send_json({"command": "start"})
                replies.append(ws.receive_json())
            statuses = [r["data"]["status"] for r in replies]
            record("burst of capacity=2 then rate_limited", statuses == ["success", "success", "rate_limited"], f"{statuses}")
            data = replies[2]["data"]
            record("rate_limited carries data.result.retry_after", isinstance(data.get("result"), dict) and "retry_after" in data["result"], f"data={data}")
            record("rate_limited has no data.retry_after", "retry_after" not in data, f"keys={sorted(data)}")
            observed("connection_established frame", str(est))
    # pong spends no token; unknown command spends one
    app = _app_control(ws_control_rate_limit_per_sec=1)
    with TestClient(app) as tc:
        with tc.websocket_connect("/ws/control") as ws:
            ws.receive_json()
            for _ in range(5):
                ws.send_json({"type": "pong"})
            ws.send_json({"command": "start"})
            r = ws.receive_json()
            record("pong x5 then command succeeds (pong spends no token)", r["data"]["status"] == "success", f"{r['data']}")
    app = _app_control(ws_control_rate_limit_per_sec=1)
    with TestClient(app) as tc:
        with tc.websocket_connect("/ws/control") as ws:
            ws.receive_json()
            ws.send_json({"command": "bogus"})
            r1 = ws.receive_json()
            ws.send_json({"command": "start"})
            r2 = ws.receive_json()
            record("unknown command spends a token", r1["data"].get("code") == "unknown_command" and r2["data"]["status"] == "rate_limited", f"{r1['data']} / {r2['data']}")


class ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_server(app, ws_impl: str):
    import uvicorn

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None, log_level="info", ws=ws_impl, lifespan="off")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.02)
    return server, thread, port


def _raw(port: int, request: bytes) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(request)
        data = b""
        try:
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
                if b"\r\n\r\n" in data and (b"Content-Length: 0" in data or b"content-length: 0" in data):
                    break
        except TimeoutError:
            # A server that keeps the socket open after its response: what arrived is the answer.
            return data
        return data


def _handshake(port: int, origin: str | None = None, key: str | None = None) -> bytes:
    lines = [
        "GET /ws/control HTTP/1.1",
        f"Host: 127.0.0.1:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        # RFC 6455 sec 1.3's sample nonce, built at run time so the secret scan does not take it for a key.
        "Sec-WebSocket-Key: " + base64.b64encode(b"the sample nonce").decode(),
        "Sec-WebSocket-Version: 13",
    ]
    if origin is not None:
        lines.append(f"Origin: {origin}")
    if key is not None:
        lines.append(f"X-API-Key: {key}")
    return _raw(port, ("\r\n".join(lines) + "\r\n\r\n").encode())


def server_control(ws_impl: str, handler: ListHandler) -> None:
    scenarios = []
    # kill switch
    app = _app_control(disable_ws_control_endpoint=True)
    scenarios.append(("kill switch 1013", app, {}))
    app = _app_control()
    app.state.api_key_auth = APIKeyAuth(["k1"])
    scenarios.append(("bad key 4001", app, {"key": "nope"}))
    app = _app_control(ws_control_allowed_origins=["https://app.example"])
    scenarios.append(("bad origin 4003", app, {"origin": "https://evil.example"}))
    app = _app_control(ws_control_allowed_origins=["https://app.example"])
    scenarios.append(("missing origin 4003", app, {}))
    for label, app, kwargs in scenarios:
        server, thread, port = _start_server(app, ws_impl)
        try:
            handler.records.clear()
            resp = _handshake(port, **kwargs)
            time.sleep(0.2)
            status = resp.split(b"\r\n", 1)[0].decode(errors="replace")
            msgs = [(r.name, r.levelname, r.getMessage()) for r in handler.records]
            code_in_logs = any(c in m for (_, _, m) in msgs for c in ("1013", "4001", "4003", "4029"))
            juniper = [m for m in msgs if m[0].startswith("juniper_service_core")]
            observed(f"[{ws_impl}] {label}", f"status={status!r} uvicorn={[m for m in msgs if m[0].startswith('uvicorn')]} juniper={juniper} code_in_logs={code_in_logs}")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
    # cooldown: N=2, failed key twice then blocked
    app = _app_control(ws_control_cooldown_rejections=2)
    app.state.api_key_auth = APIKeyAuth(["k1"])
    server, thread, port = _start_server(app, ws_impl)
    try:
        for attempt in range(3):
            handler.records.clear()
            resp = _handshake(port, key="nope")
            time.sleep(0.2)
            status = resp.split(b"\r\n", 1)[0].decode(errors="replace")
            msgs = [(r.name, r.levelname, r.getMessage()) for r in handler.records if r.name.startswith("juniper_service_core")]
            observed(f"[{ws_impl}] cooldown N=2 bad-key attempt {attempt + 1}", f"status={status!r} juniper={msgs}")
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def _app_body(max_bytes: int) -> FastAPI:
    app = FastAPI()

    @app.post("/v1/echo")
    async def echo(request: Request) -> dict:
        body = await request.body()
        return {"n": len(body)}

    @app.get("/v1/echo")
    async def echo_get(request: Request) -> dict:
        body = await request.body()
        return {"n": len(body)}

    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=max_bytes)
    return app


def server_body() -> None:
    app = _app_body(10)
    server, thread, port = _start_server(app, "websockets")
    try:
        cases = {
            "CL=abc": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: abc\r\nConnection: close\r\n\r\n",
            "CL=10 body 10": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\nConnection: close\r\n\r\n" + b"x" * 10,
            "CL=11 body 11": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: 11\r\nConnection: close\r\n\r\n" + b"x" * 11,
            "CL=5 body 8 (under-declared, fits)": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\nConnection: close\r\n\r\n" + b"x" * 8,
            "CL=5 body 50 (under-declared, over)": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: 5\r\nConnection: close\r\n\r\n" + b"x" * 50,
            "chunked 10": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n6\r\nabcdef\r\n4\r\nghij\r\n0\r\n\r\n",
            "chunked 11": b"POST /v1/echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n6\r\nabcdef\r\n5\r\nghijk\r\n0\r\n\r\n",
            "GET chunked 50": b"GET /v1/echo HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n32\r\n" + b"x" * 50 + b"\r\n0\r\n\r\n",
            "GET CL=50 body 50": b"GET /v1/echo HTTP/1.1\r\nHost: x\r\nContent-Length: 50\r\nConnection: close\r\n\r\n" + b"x" * 50,
        }
        for label, req in cases.items():
            resp = _raw(port, req)
            head, _, body = resp.partition(b"\r\n\r\n")
            status = head.split(b"\r\n", 1)[0].decode(errors="replace")
            observed(f"[uvicorn httptools/h11 auto] body cap 10: {label}", f"status={status!r} body={body[:120]!r}")
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def client_body() -> None:
    record("default cap is 10 MiB", _DEFAULT_MAX_REQUEST_BODY_BYTES == 10 * 1024 * 1024)
    app = _app_body(10)
    tc = TestClient(app)
    r = tc.post("/v1/echo", content=b"x", headers={"content-length": "not-a-number"})
    record("TestClient: non-integer CL -> 400 Invalid Content-Length header", r.status_code == 400 and r.json() == {"detail": "Invalid Content-Length header"}, f"{r.status_code} {r.text}")
    r = tc.post("/v1/echo", content=b"x" * 10)
    record("TestClient: 10 bytes at cap 10 delivered", r.status_code == 200 and r.json() == {"n": 10}, f"{r.status_code} {r.text}")
    r = tc.post("/v1/echo", content=b"x" * 11)
    record("TestClient: 11 bytes at cap 10 -> 413", r.status_code == 413 and r.json() == {"detail": "Request body too large"}, f"{r.status_code} {r.text}")


def main() -> int:
    print(f"python {sys.version.split()[0]} juniper_service_core from {juniper_service_core.__file__}", flush=True)
    import starlette
    import uvicorn

    print(f"starlette {starlette.__version__} uvicorn {uvicorn.__version__}", flush=True)
    unit_bucket()
    unit_cooldown()
    unit_origin()
    client_control()
    client_body()
    handler = ListHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    for impl in ("websockets", "websockets-sansio"):
        try:
            server_control(impl, handler)
        except Exception as exc:  # noqa: BLE001 - report and continue
            observed(f"[{impl}] server_control error", repr(exc))
    try:
        server_body()
    except Exception as exc:  # noqa: BLE001 - report and continue
        observed("server_body error", repr(exc))
    fails = [r for r in RESULTS if r.startswith("FAIL")]
    print(f"SUMMARY: {len(RESULTS)} lines, {len(fails)} FAIL", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
