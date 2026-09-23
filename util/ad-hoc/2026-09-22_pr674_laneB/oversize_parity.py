"""main vs PR #674: an OVERSIZED broadcast (> ws_max_message_size_bytes) carrying a NumPy scalar or a
lone surrogate. Real uvicorn server + real websockets client; counts what the subscriber receives."""

import asyncio
import json
import socket
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import uvicorn  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402

from api.app import create_app  # noqa: E402
from api.settings import Settings  # noqa: E402


async def main() -> None:
    app = create_app(Settings(auto_start=False, ws_resume_handshake_timeout_s=0.1, ws_initial_metrics_count=0))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", lifespan="on"))
    serve_task = asyncio.create_task(server.serve(sockets=[sock]))
    while not server.started:
        await asyncio.sleep(0.02)
    mgr = app.state.ws_manager
    c = await connect(f"ws://127.0.0.1:{sock.getsockname()[1]}/ws/training")
    for want in ("connection_established", "initial_status", "state"):
        while json.loads(await c.recv()).get("type") != want:
            pass
    while mgr.connection_count < 1:
        await asyncio.sleep(0.02)
    big = [float(i) for i in range(12000)]  # ~90 KB of JSON: above the 60_000 chunk threshold
    cases = {
        "oversize+np.float32": {"type": "topology", "data": {"hidden_units": big, "scale": np.float32(0.5)}},
        "oversize+lone-surrogate": {"type": "topology", "data": {"hidden_units": big, "name": "run-\udcff"}},
        "small+np.float32": {"type": "metrics", "data": {"loss": np.float32(0.5)}},
    }
    for label, msg in cases.items():
        before = mgr.transport_stats()
        await mgr.broadcast(msg)
        await mgr.broadcast({"type": "metrics", "data": {"marker": label}})
        got = []
        while True:
            try:
                f = json.loads(await asyncio.wait_for(c.recv(), 2))
            except Exception as e:
                got.append(f"<{type(e).__name__}>")
                break
            got.append(f.get("type") if f.get("type") != "chunked_message" else f"chunk{f['data']['chunk_index']}")
            if f.get("type") == "metrics" and f["data"].get("marker") == label:
                break
        after = mgr.transport_stats()
        print(f"{label:26s} received={got} chunked_total+={after['messages_chunked_total'] - before['messages_chunked_total']} unserializable+={after.get('unserializable_messages_total', 0) - before.get('unserializable_messages_total', 0)} active={after['active_connections']}")
        if mgr.connection_count == 0:
            print("  subscriber was dropped; stopping")
            break
    c.transport.abort()
    server.should_exit = True
    await asyncio.wait_for(serve_task, 15)


asyncio.run(main())
