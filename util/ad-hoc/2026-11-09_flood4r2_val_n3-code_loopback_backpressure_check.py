"""
Does a large /ws/training replay to a NON-READING client ever block (yield) on uvicorn + websockets over loopback?

Measured 2026-11-09 (uvicorn 0.46.0, websockets 16.0, Python 3.14.7): a 1000 x 12 KB replay to a client with
max_queue=2 and SO_RCVBUF 32 KB, server-side SO_SNDBUF capped at 32 KB, made ZERO pause_writing calls and never
yielded; the resuming socket was promoted before the first 10 ms sample. Usage: python <this> <cascor src dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_val_n3-code_e2e_uvicorn.py
"""

import asyncio
import importlib
import json
import socket
import sys
import time
import types

SRC = sys.argv[1]
sys.path.insert(0, SRC)

import uvicorn  # noqa: E402
from api.websocket.manager import WebSocketManager  # noqa: E402
from api.websocket.training_stream import training_stream_handler  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402

# websockets.legacy is deprecated and often invisible to static import resolvers
# (Pylance reportMissingImports) even when present at runtime; load by name.
_wlp = importlib.import_module("websockets.legacy.protocol")

PAUSES = []
_orig_pause = _wlp.WebSocketCommonProtocol.pause_writing


def _pause(self):
    PAUSES.append((time.monotonic(), self.transport.get_write_buffer_size() if self.transport else None))
    return _orig_pause(self)


SNDBUFS = []
_orig_cm = _wlp.WebSocketCommonProtocol.connection_made


def _cm(self, transport):
    s = transport.get_extra_info('socket')
    if s is not None:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
        SNDBUFS.append(s.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    return _orig_cm(self, transport)


_wlp.WebSocketCommonProtocol.connection_made = _cm


_wlp.WebSocketCommonProtocol.pause_writing = _pause


async def main() -> None:
    app = FastAPI()
    mgr = WebSocketManager(send_timeout_seconds=5.0)
    mgr.set_event_loop(asyncio.get_running_loop())
    app.state.ws_manager = mgr
    app.state.lifecycle = None
    app.state.settings = types.SimpleNamespace(ws_resume_handshake_timeout_s=0.2, ws_initial_metrics_count=0, ws_heartbeat_interval_sec=0, ws_heartbeat_pong_timeout_sec=10)
    app.add_api_websocket_route("/ws/training", training_stream_handler)
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
    lsock.bind(("127.0.0.1", 0))
    port = lsock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, ws="websockets", lifespan="off", log_level="critical"))
    serve = asyncio.create_task(server.serve(sockets=[lsock]))
    while not server.started:
        await asyncio.sleep(0.01)
    uri = f"ws://127.0.0.1:{port}/ws/training"
    # history: 300 x 12 KB, nobody active (fix numbers them; main does not) -> use an observer to number on main too
    async with connect(uri, max_size=None) as o:
        await asyncio.sleep(0.4)  # promoted fresh
        for i in range(1000):
            await mgr.broadcast({"type": "metrics", "data": {"n": i, "pad": "x" * 12000}})
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32768)
        sock.setblocking(False)
        await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", port))
        async with connect(uri, sock=sock, max_queue=2, max_size=None) as b:
            await b.recv()
            t0 = time.monotonic()
            await b.send(json.dumps({"type": "resume", "data": {"last_seq": 0, "server_instance_id": mgr.server_instance_id}}))
            samples = []
            for _ in range(50):
                await asyncio.sleep(0.01)
                samples.append((round(time.monotonic() - t0, 3), len(mgr._pending_connections), mgr.connection_count))
            print("samples(t, pending, active):", samples[:6], "...", samples[-3:])
            got = 0
            try:
                while True:
                    await asyncio.wait_for(b.recv(), timeout=1.0)
                    got += 1
            except asyncio.TimeoutError:
                pass  # nothing more within 1 s: the stream is drained
            print("received after reading:", got)
            print("server pause_writing calls:", len(PAUSES), PAUSES[:3], "server sndbufs:", SNDBUFS, "client rcvbuf:", sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))
        # observer drained in background by library
        _ = o
    server.should_exit = True
    await serve


asyncio.run(main())
