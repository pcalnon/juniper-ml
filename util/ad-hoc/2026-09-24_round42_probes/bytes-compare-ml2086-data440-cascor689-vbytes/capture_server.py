"""A local Sentry-envelope sink: records each POST's item types to a JSONL file. 127.0.0.1 only.

python capture_server.py <port> <out.jsonl>
"""

import gzip
import http.server
import json
import sys
import zlib

port, out = int(sys.argv[1]), sys.argv[2]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        enc = (self.headers.get("Content-Encoding") or "").lower()
        try:
            if enc == "gzip":
                raw = gzip.decompress(raw)
            elif enc == "deflate":
                raw = zlib.decompress(raw)
            elif enc == "br":
                import brotli

                raw = brotli.decompress(raw)
        except Exception:  # noqa: BLE001
            pass
        types = []
        details = []
        for line in raw.split(b"\n"):
            if line.startswith(b"{") and (b'"exception"' in line or b'"logentry"' in line):
                try:
                    ev = json.loads(line)
                    exc = (ev.get("exception") or {}).get("values") or [{}]
                    details.append({"exc": f"{exc[-1].get('type')}: {str(exc[-1].get('value'))[:80]}", "logger": ev.get("logger"), "msg": str((ev.get("logentry") or {}).get("message"))[:80]})
                except Exception:  # noqa: BLE001
                    pass
            if line.startswith(b'{"type"') or b'"type":' in line[:40]:
                try:
                    obj = json.loads(line)
                    if "type" in obj and "length" in obj or "type" in obj and len(obj) <= 4:
                        types.append(obj["type"])
                except Exception:  # noqa: BLE001
                    pass
        with open(out, "a") as fh:
            fh.write(json.dumps({"path": self.path, "types": types, "details": details, "bytes": len(raw), "ua": self.headers.get("User-Agent")}) + "\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
