"""cascor's direct-CLI bootstrap ``sentry_sdk.init`` (src/main.py): does a secret local reach the wire?

The REAL init runs (import main with a DSN in the environment) and the REAL HttpTransport posts to
a capture server on 127.0.0.1 -- nothing leaves the host.

python cascor_cli_sentry_probe.py <cascor src dir>
"""

import gzip
import http.server
import logging
import os
import sys
import threading
import zlib

src = sys.argv[1]
SECRET = "-".join(("cli", "bootstrap", "secret", "LEAKMARK", "d00d"))
bodies = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        enc = (self.headers.get("Content-Encoding") or "").lower()
        if enc == "gzip":
            raw = gzip.decompress(raw)
        elif enc == "deflate":
            raw = zlib.decompress(raw)
        elif enc == "br":
            import brotli

            raw = brotli.decompress(raw)
        bodies.append((self.path, raw))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
dsn = f"http://public@127.0.0.1:{server.server_address[1]}/1"
os.environ["JUNIPER_CASCOR_SENTRY_DSN"] = dsn
os.environ["SENTRY_SDK_DSN"] = dsn  # same value: no CFG-03 drift warning, and dotenv cannot override either

sys.path.insert(0, src)
os.chdir(src)
import main  # noqa: E402,F401  -- runs the bootstrap sentry_sdk.init
import sentry_sdk  # noqa: E402

client = sentry_sdk.get_client()
print("main.py:", main.__file__)
print("sentry-sdk", sentry_sdk.VERSION, "| client active:", client.is_active(), "| include_local_variables:", client.options.get("include_local_variables"), "| dsn is local:", str(client.options.get("dsn", "")).startswith("http://public@127.0.0.1:"))


def holder():
    candidate = SECRET  # noqa: F841
    raise TypeError("comparing strings with non-ASCII characters is not supported")


try:
    holder()
except TypeError:
    sentry_sdk.capture_exception()
try:
    holder()
except TypeError:
    logging.getLogger("juniper_cascor.api").exception("Unhandled exception")
sentry_sdk.flush(timeout=10)
server.shutdown()
wire = b"\n".join(b for _p, b in bodies)
print(f"posts received: {len(bodies)} | paths: {sorted({p for p, _b in bodies})}")
print(f"SECRET ON THE WIRE: {SECRET.encode() in wire} (occurrences: {wire.count(SECRET.encode())}); frames with vars: {wire.count(b'\"vars\":')}")
