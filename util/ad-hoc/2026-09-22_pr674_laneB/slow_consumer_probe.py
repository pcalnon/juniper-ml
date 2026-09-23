"""Lane B adversarial experiment for juniper-cascor PR #674 (F-CASCOR-004).

A REAL slow consumer over TCP loopback -- the case the PR body lists as "not proven".
Client A stops reading after the handshake; client B keeps reading. The server
broadcasts until A's send times out (GAP-WS-07, 0.5 s), then we watch what the
PR's close does, under whichever uvicorn/websockets stack PYTHONPATH selects.

Args: <tree root> <stall_seconds_after_drop or -1 for never> <msg_pad_bytes> <observe_seconds>
"""

import asyncio
import json
import socket
import sys
import time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
STALL = float(sys.argv[2])
PAD = int(sys.argv[3])
OBSERVE = float(sys.argv[4])
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402
import websockets  # noqa: E402
from uvicorn.protocols.websockets.auto import AutoWebSocketsProtocol  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402
from websockets.exceptions import ConnectionClosed  # noqa: E402

from api.app import create_app  # noqa: E402
from api.settings import Settings  # noqa: E402

T0 = time.monotonic()


def ts() -> str:
    return f"{time.monotonic() - T0:7.2f}s"


async def handshake(conn) -> None:
    for want in ("connection_established", "initial_status", "state"):
        while True:
            frame = json.loads(await asyncio.wait_for(conn.recv(), 5))
            if frame.get("type") == want:
                break


async def main() -> None:
    print(f"uvicorn {uvicorn.__version__} websockets {websockets.__version__} auto={AutoWebSocketsProtocol.__name__}")
    app = create_app(Settings(auto_start=False, ws_resume_handshake_timeout_s=0.1, ws_initial_metrics_count=0))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", lifespan="on"))
    serve_task = asyncio.create_task(server.serve(sockets=[sock]))
    while not server.started:
        await asyncio.sleep(0.02)
    mgr = app.state.ws_manager
    url = f"ws://127.0.0.1:{port}/ws/training"
    has_pending = hasattr(mgr, "_pending_closes")

    a = await connect(url)
    await handshake(a)
    b = await connect(url)
    await handshake(b)
    while mgr.connection_count < 2:
        await asyncio.sleep(0.02)
    a_port = a.local_address[1]
    srv_a = next(ws for ws in mgr._active_connections if ws.client.port == a_port)
    proto_a = getattr(srv_a._send, "__self__", None)
    transport_a = getattr(proto_a, "transport", None)

    b_frames = 0

    async def read_b() -> None:
        nonlocal b_frames
        try:
            async for _ in b:
                b_frames += 1
        except ConnectionClosed:
            pass

    b_task = asyncio.create_task(read_b())

    # A stops reading here. Broadcast until A is dropped.
    import os; pad = os.urandom(PAD // 2).hex()
    sent = 0
    t_first = time.monotonic()
    while mgr.connection_count == 2 and sent < 20000:
        await mgr.broadcast({"type": "metrics", "data": {"epoch": sent, "pad": os.urandom(PAD // 2).hex()}})
        sent += 1
    t_drop = time.monotonic()
    stats = mgr.transport_stats()
    wbuf = transport_a.get_write_buffer_size() if transport_a is not None else None
    print(f"{ts()} A dropped after {sent} broadcasts (~{sent * (PAD + 80) / 1024:.0f} KiB) in {t_drop - t_first:.2f}s; send_failures={stats['send_failures']} active={stats['active_connections']} server-side write buffer for A={wbuf}")
    print(f"{ts()} application_state(A)={srv_a.application_state.name} pending_closes={len(mgr._pending_closes) if has_pending else 'n/a'} training_bucket={len(mgr._endpoint_connections['training'])}")

    a_result = {}

    async def drain_a() -> None:
        n = 0
        try:
            async for _ in a:
                n += 1
        except ConnectionClosed:
            pass
        a_result.update(frames=n, code=a.close_code, reason=a.close_reason, at=ts())

    a_task = None
    deadline = time.monotonic() + OBSERVE
    next_report = time.monotonic()
    while time.monotonic() < deadline:
        if STALL >= 0 and a_task is None and time.monotonic() - t_drop >= STALL:
            print(f"{ts()} A resumes reading")
            a_task = asyncio.create_task(drain_a())
        if STALL == -3 and not a_result.get("ponged") and time.monotonic() - t_drop >= 1.0:
            print(f"{ts()} A (still not reading) sends an app-level pong, as cascor-client's auto-pong would")
            await a.send(json.dumps({"type": "pong"}))
            a_result["ponged"] = True
        if STALL == -3 and a_task is None and time.monotonic() - t_drop >= 3.0:
            print(f"{ts()} A resumes reading; training_bucket={len(mgr._endpoint_connections['training'])} pending_closes={len(mgr._pending_closes)}")
            a_task = asyncio.create_task(drain_a())
        if STALL == -2 and not a_result.get("aborted") and time.monotonic() - t_drop >= 3.0:
            print(f"{ts()} A's socket is RESET by the peer (slow relay killed / restarted)")
            a.transport.abort()
            a_result["aborted"] = True
        if time.monotonic() >= next_report:
            closing = getattr(transport_a, "is_closing", lambda: None)()
            print(f"{ts()} pending_closes={len(mgr._pending_closes) if has_pending else 'n/a'} training_bucket={len(mgr._endpoint_connections['training'])} global_slots={mgr._global_ws_count} A.transport.is_closing={closing} A.wbuf={transport_a.get_write_buffer_size() if transport_a else None} B.frames={b_frames}")
            next_report = time.monotonic() + 2.0
        if "code" in a_result or a_result.get("aborted"):
            pass
        else:
            await asyncio.sleep(0.05)
            continue
        if (not has_pending or not mgr._pending_closes) and len(mgr._endpoint_connections["training"]) == 1:
            await asyncio.sleep(0.5)  # let any exception-handler log flush
            break
        await asyncio.sleep(0.05)
    print(f"{ts()} A outcome: {a_result or 'no close observed (A never resumed or close never arrived)'}")
    print(f"{ts()} final: pending_closes={len(mgr._pending_closes) if has_pending else 'n/a'} training_bucket={len(mgr._endpoint_connections['training'])} B.frames={b_frames} B.open={b.state.name}")

    for t in (a_task, b_task):
        if t is not None:
            t.cancel()
    for c in (a, b):
        try:
            c.transport.abort()
        except Exception:
            pass
    server.should_exit = True
    try:
        await asyncio.wait_for(serve_task, 15)
    except asyncio.TimeoutError:
        print(f"{ts()} uvicorn shutdown did not finish in 15s")


asyncio.run(main())
