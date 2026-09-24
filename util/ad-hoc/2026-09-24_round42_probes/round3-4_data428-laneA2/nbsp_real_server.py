"""The NBSP-wrapped '*' over a REAL server: uvicorn (h11) in a thread on 127.0.0.1, raw socket requests."""

import http.client
import json
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

L = Path(__file__).resolve().parent
sys.path.insert(0, str(L / "trees" / "3a76a4c"))

import uvicorn  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

storage = Path(tempfile.mkdtemp(dir=str(L / "tmp"))) / "s"
storage.mkdir()
store = LocalFSDatasetStore(storage)
app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, http="h11", log_level="warning", lifespan="off"))
datasets.set_store(store)
thread = threading.Thread(target=server.run, daemon=True)
thread.start()
for _ in range(100):
    if server.started:
        break
    time.sleep(0.05)

conn = http.client.HTTPConnection("127.0.0.1", port)
conn.request("POST", "/v1/datasets", body=json.dumps({"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 4}, "persist": True}), headers={"Content-Type": "application/json"})
dsid = json.loads(conn.getresponse().read())["dataset_id"]
conn.close()


def raw(method: str, path: str, header: bytes, body: bytes = b"") -> str:
    req = f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n".encode() + header + b"\r\n"
    if body:
        req += b"Content-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\n"
    req += b"\r\n" + body
    with socket.create_connection(("127.0.0.1", port)) as sock:
        sock.sendall(req)
        data = b""
        while chunk := sock.recv(65536):
            data += chunk
    return data.split(b"\r\n", 1)[0].decode()


print("uvicorn", uvicorn.__version__, "h11 on port", port)
for label, hdr in (("If-None-Match: \\xa0*", b"If-None-Match: \xa0*"), ("If-Match: \\xa0*", b"If-Match: \xa0*"), ("control If-Match: garbage", b"If-Match: garbage")):
    print(f"GET /{{id}} {label:28s} -> {raw('GET', f'/v1/datasets/{dsid}', hdr)}")
print(f"PATCH tags If-Match: \\xa0*        -> {raw('PATCH', f'/v1/datasets/{dsid}/tags', b'If-Match: \xa0*', json.dumps({'add_tags': ['nbsp-real']}).encode())}; tags now {store.get_meta(dsid).tags}")
server.should_exit = True
thread.join(timeout=10)
