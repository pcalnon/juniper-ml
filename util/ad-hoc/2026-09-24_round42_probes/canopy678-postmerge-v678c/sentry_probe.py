"""Does the blank-key WARNING reach Sentry? Fake DSN -> local envelope sink; boot canopy; inspect.

Usage: python sentry_probe.py <tree-dir>
"""

import gzip
import http.server
import os
import socket
import subprocess
import sys
import threading
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, sys.argv[1])
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
captured = []


class Sink(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        enc = (self.headers.get("Content-Encoding") or "").lower()
        try:
            if enc == "gzip":
                body = gzip.decompress(body)
            elif enc == "br":
                import brotli  # type: ignore

                body = brotli.decompress(body)
            elif enc == "deflate":
                body = zlib.decompress(body)
        except Exception as exc:  # noqa: BLE001
            body = f"<undecodable {enc}: {exc}>".encode()
        captured.append((self.path, body))
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

port = free_port()
env = {k: v for k, v in os.environ.items() if not k.startswith(("CANOPY_", "JUNIPER_", "SENTRY"))}
env.update(CANOPY_API_KEY=" \t ", JUNIPER_CANOPY_SENTRY_DSN=f"http://publickey@127.0.0.1:{sink_port}/42", JUNIPER_CANOPY_DEMO_MODE="1", JUNIPER_SKIP_DEP_FLOOR_CHECK="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{TREE}/src:{TREE}", LIBTORCH="", LD_LIBRARY_PATH="")
log = open(os.path.join(HERE, f"sentry-{sys.argv[1]}.log"), "wb")
proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)], cwd=f"{TREE}/src", env=env, stdout=log, stderr=subprocess.STDOUT)
time.sleep(20)  # startup (~7 s) + the logs batcher's flush interval
proc.terminate()
proc.wait(15)
time.sleep(1)
srv.shutdown()
hits = [(p, b) for p, b in captured if b"set but blank" in b]
print(f"envelopes captured: {len(captured)}; containing the blank-key WARNING: {len(hits)}")
for p, b in hits[:1]:
    i = b.find(b"set but blank")
    print(p, b[max(0, i - 300): i + 80])
print("item types seen:", sorted({seg.split(b'"type":"')[1].split(b'"')[0].decode() for _, b in captured for seg in b.split(b"\n") if b'"type":"' in seg}))
