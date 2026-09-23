"""Where do the bytes go when a /ws/training subscriber stops reading? Kernel queues + loop yields."""

import asyncio
import fcntl
import json
import socket
import struct
import sys
import termios
import time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
N = int(sys.argv[2])
PAD = int(sys.argv[3])
sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402

from api.app import create_app  # noqa: E402
from api.settings import Settings  # noqa: E402

SIOCOUTQ = termios.TIOCOUTQ
SIOCINQ = termios.FIONREAD


def q(sock, req):
    try:
        return struct.unpack("I", fcntl.ioctl(sock.fileno(), req, b"\0\0\0\0"))[0]
    except Exception as e:
        return f"err:{e}"


async def main() -> None:
    app = create_app(Settings(auto_start=False, ws_resume_handshake_timeout_s=0.1, ws_initial_metrics_count=0))
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(("127.0.0.1", 0))
    port = lsock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", lifespan="on"))
    serve_task = asyncio.create_task(server.serve(sockets=[lsock]))
    while not server.started:
        await asyncio.sleep(0.02)
    mgr = app.state.ws_manager
    a = await connect(f"ws://127.0.0.1:{port}/ws/training")
    for want in ("connection_established", "initial_status", "state"):
        while json.loads(await a.recv()).get("type") != want:
            pass
    while mgr.connection_count < 1:
        await asyncio.sleep(0.02)
    a_port = a.local_address[1]
    proto = next(p for p in server.server_state.connections if getattr(p, "client", None) and p.client[1] == a_port)
    srv_sock = proto.transport.get_extra_info("socket")
    cli_sock = a.transport.get_extra_info("socket")
    ticks = 0

    async def ticker():
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0)

    tk = asyncio.create_task(ticker())
    await asyncio.sleep(0.05)
    import os; pad = os.urandom(PAD // 2).hex()
    t0 = time.monotonic()
    for i in range(N):
        tb = time.monotonic()
        await mgr.broadcast({"type": "metrics", "data": {"epoch": i, "pad": os.urandom(PAD // 2).hex()}})
        dt = time.monotonic() - tb
        if i % max(1, N // 10) == 0 or dt > 0.1 or mgr.connection_count == 0:
            print(f"i={i} bcast={dt*1000:.1f}ms ticks={ticks} srv_wbuf={proto.transport.get_write_buffer_size()} srv_kernel_outq={q(srv_sock, SIOCOUTQ)} cli_kernel_inq={q(cli_sock, SIOCINQ)} active={mgr.connection_count} send_failures={mgr.transport_stats()['send_failures']}", flush=True)
        if mgr.connection_count == 0:
            break
    print(f"elapsed {time.monotonic()-t0:.2f}s ticks={ticks} srv_sndbuf={srv_sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)} cli_rcvbuf={cli_sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)}")
    tk.cancel()
    a.transport.abort()
    server.should_exit = True
    await asyncio.wait_for(serve_task, 15)


asyncio.run(main())
