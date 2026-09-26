#!/usr/bin/env python3
"""Lane A: `*` wrapped in single bytes, sent as RAW bytes to a live uvicorn (h11, then httptools).

Starts uvicorn in-process on a FREE loopback port (never 8100), creates one dataset, then sends
GET /v1/datasets/{id}/artifact with ``If-None-Match: <b>*<b>`` for each byte b and records the
status: 304 = read as ``*``; 200 = passed through and judged malformed (full body); 400 = the
server's parser refused the byte. The server is stopped before the next parser starts.
"""

import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

import juniper_data

assert Path(juniper_data.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_TREE"]).resolve())
import httpx  # noqa: E402
import uvicorn  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

BYTES = [0x09, 0x20, 0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x1F, 0x85, 0xA0, 0x01, 0x7F]
PORTS = {"h11": int(sys.argv[1]), "httptools": int(sys.argv[2])}


def port_free(port: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def raw_get(port: int, path: str, header_value: bytes) -> int:
    request = b"GET " + path.encode() + b" HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\nIf-None-Match: " + header_value + b"\r\n\r\n"
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.sendall(request)
        data = b""
        while b"\r\n" not in data:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    return int(data.split(b" ", 2)[1])


print("uvicorn", uvicorn.__version__)
for parser, port in PORTS.items():
    assert port != 8100 and port_free(port), f"port {port} is not free"
    storage = Path(tempfile.mkdtemp(prefix=f"ows-{parser}-"))
    app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, http=parser, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    try:
        created = httpx.post(f"http://127.0.0.1:{port}/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 3}, "persist": True}, timeout=30)
        dataset_id = created.json()["dataset_id"]
        path = f"/v1/datasets/{dataset_id}/artifact"
        row = []
        for b in BYTES:
            status = raw_get(port, path, bytes([b]) + b"*" + bytes([b]))
            row.append(f"0x{b:02X}:{status}")
        print(f"{parser:9} (port {port}) If-None-Match: <b>*<b> ->", " ".join(row))
        print(f"{parser:9} control: '*' alone -> {raw_get(port, path, b'*')}, '\"nomatch\"' -> {raw_get(port, path, b'\"nomatch\"')}")
    finally:
        server.should_exit = True
        thread.join(15)
        print(f"{parser:9} server stopped: {not thread.is_alive()}; port free again: {port_free(port)}")
