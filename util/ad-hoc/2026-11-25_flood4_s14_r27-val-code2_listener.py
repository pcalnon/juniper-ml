"""
A stand-in "live juniper-data" for the r27-val-code2 bypass probe: binds 127.0.0.1 on an EPHEMERAL port (never a Juniper
port), answers every GET with 200 {"status": "alive"}, logs each request line, and exits after a fixed lifetime.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2

Usage:
    python <this file> <port file> <request log> <lifetime seconds>
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def main() -> int:
    port_file, log_file, lifetime = sys.argv[1], sys.argv[2], float(sys.argv[3])

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - http.server's name
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"method": "GET", "path": self.path, "host_header": self.headers.get("Host")}) + "\n")
            body = b'{"status": "alive"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    with open(port_file, "w", encoding="utf-8") as handle:
        handle.write(str(server.server_address[1]))
    timer = threading.Timer(lifetime, server.shutdown)
    timer.start()
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
