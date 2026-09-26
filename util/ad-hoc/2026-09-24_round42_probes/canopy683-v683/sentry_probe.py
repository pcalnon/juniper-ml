"""Which secrets reach Sentry? Fake DSN -> local envelope sink; real uvicorn boot of <tree>/src; inspect every envelope.

Scenario: canopy auth ENABLED with a real key (REALKEY_MARK inside it), demo mode, a padded JUNIPER_DATA_API_KEY
(LEAKME inside it) and a juniper-data URL nothing listens on. After startup, ONE anonymous raw-socket request presents
``X-API-Key: \\xa0`` (a byte both uvicorn parsers pass): hmac.compare_digest raises TypeError on non-ASCII text.

usage: python sentry_probe.py <python-exe> <tree-dir> [h11|httptools]
"""

import gzip
import http.server
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY, TREE = sys.argv[1], Path(sys.argv[2]).resolve()
LOOP = sys.argv[3] if len(sys.argv) > 3 else "httptools"
REAL_KEY = "real-canopy-key-REALKEYMARK-7f3a"
captured: list[bytes] = []


class Sink(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        enc = (self.headers.get("Content-Encoding") or "").lower()
        try:
            if enc == "gzip":
                body = gzip.decompress(body)
            elif enc == "deflate":
                body = zlib.decompress(body)
            elif enc == "br":
                import brotli  # type: ignore

                body = brotli.decompress(body)
        except Exception as exc:  # noqa: BLE001
            body = f"<undecodable {enc}: {exc}>".encode()
        captured.append(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


sink_port = free_port()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", sink_port), Sink)
threading.Thread(target=srv.serve_forever, daemon=True).start()
work = Path(tempfile.mkdtemp(prefix="sentry-", dir=str(HERE / "work")))
(work / "conf").mkdir()
shutil.copy(TREE / "conf" / "logging_config.yaml", work / "conf" / "logging_config.yaml")
port = free_port()
env = {k: v for k, v in os.environ.items() if not k.startswith(("CANOPY_", "JUNIPER_", "SENTRY", "CASCOR_"))}
env.update(
    CANOPY_API_KEY=REAL_KEY,
    JUNIPER_DATA_API_KEY=" LEAKME-data-key-S1",
    JUNIPER_DATA_URL=f"http://127.0.0.1:{free_port()}",
    JUNIPER_CANOPY_SENTRY_DSN=f"http://publickey@127.0.0.1:{sink_port}/42",
    JUNIPER_CANOPY_DEMO_MODE="1",
    JUNIPER_CANOPY_SERVER__PORT=str(port),
    JUNIPER_SKIP_DEP_FLOOR_CHECK="1",
    PYTHONDONTWRITEBYTECODE="1",
    PYTHONPATH=str(TREE / "src"),
    LIBTORCH="",
    LD_LIBRARY_PATH="",
)
log = open(work / "uvicorn.log", "wb")
proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--app-dir", str(TREE / "src"), "--host", "127.0.0.1", "--port", str(port), "--http", LOOP], cwd=str(work), env=env, stdout=log, stderr=subprocess.STDOUT)
up = False
for _ in range(120):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health/live", timeout=1)
        up = True
        break
    except Exception:  # noqa: BLE001
        time.sleep(0.5)
print("server up:", up, "parser:", LOOP)
with socket.create_connection(("127.0.0.1", port)) as s:
    s.sendall(b"GET /api/status HTTP/1.1\r\nHost: 127.0.0.1\r\nX-API-Key: \xa0\r\nConnection: close\r\n\r\n")
    resp = b""
    s.settimeout(10)
    try:
        while chunk := s.recv(65536):
            resp += chunk
    except OSError:
        pass
print("anonymous non-ASCII-key request ->", resp.split(b"\r\n", 1)[0])
time.sleep(12)  # the logs batcher's flush interval
proc.terminate()
proc.wait(20)
time.sleep(1)
srv.shutdown()
blob = b"\n".join(captured)
print(f"envelopes captured: {len(captured)}")
for label, mark in (("real CANOPY_API_KEY", b"REALKEYMARK"), ("padded JUNIPER_DATA_API_KEY", b"LEAKME-data-key-S1")):
    n = sum(1 for b in captured if mark in b)
    print(f"  envelopes carrying the {label}: {n}")
    for b in captured:
        i = b.find(mark)
        if i >= 0:
            print("    ...", b[max(0, i - 220): i + 60].decode("utf-8", "replace").replace("\n", " "), "...")
            break
text = (work / "uvicorn.log").read_bytes()
print("uvicorn console lines carrying the real key:", sum(1 for ln in text.splitlines() if b"REALKEYMARK" in ln))
