"""A tiny real-HTTP fake of juniper-data for probing cascor#678 (scratch only)."""

from __future__ import annotations

import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

import numpy as np

REAL_LIKE_LISTING: List[Dict[str, Any]] = [
    {"name": "spiral", "version": "3.0.0", "description": "s", "available": True, "install_hint": None, "schema": {"type": "object", "properties": {"n_spirals": {"type": "integer"}}}},
    {"name": "csv_import", "version": "3.0.0", "description": "c", "available": True, "install_hint": None, "schema": {"type": "object", "properties": {"allow_truncation": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}}}},
    {"name": "equities", "version": "5.0.0", "description": "e", "available": True, "install_hint": None, "schema": {"type": "object", "properties": {"allow_truncation": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}}}},
]


def npz_bytes(rows: int = 20) -> bytes:
    rng = np.random.default_rng(7)
    buf = io.BytesIO()
    np.savez(
        buf,
        X_train=rng.standard_normal((rows, 2)).astype("float32"),
        y_train=rng.standard_normal((rows, 2)).astype("float32"),
        X_val=rng.standard_normal((6, 2)).astype("float32"),
        y_val=rng.standard_normal((6, 2)).astype("float32"),
        X_test=rng.standard_normal((4, 2)).astype("float32"),
        y_test=rng.standard_normal((4, 2)).astype("float32"),
    )
    return buf.getvalue()


class FakeJD:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.gen_mode = "ok"  # ok | delay | 500 | badjson | empty | partial | noschema | dict
        self.gen_delay = 0.0
        self.gen_calls = 0
        self.create_mode = "422"  # 422 | ok
        self.meta: Dict[str, Any] = {"truncation": {"unit": "symbols", "cap": 14, "requested": 503, "imported": 14}}
        self.posts: List[Dict[str, Any]] = []
        self.listing = REAL_LIKE_LISTING
        self.artifact_mode = "three"  # three | train_only
        self.rows = 20
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:  # silence
                pass

            def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path.startswith("/v1/health/ready"):
                    return self._send(200, b'{"status":"ready"}')
                if self.path.startswith("/v1/health"):
                    return self._send(200, b'{"status":"ok"}')
                if self.path == "/v1/generators":
                    with fake.lock:
                        fake.gen_calls += 1
                        mode, delay = fake.gen_mode, fake.gen_delay
                    if mode == "delay":
                        time.sleep(delay)
                        return self._send(200, json.dumps(fake.listing).encode())
                    if mode == "500":
                        return self._send(500, b'{"detail":"boom"}')
                    if mode == "badjson":
                        return self._send(200, b"<html>not json</html>", "text/html")
                    if mode == "empty":
                        return self._send(200, b"[]")
                    if mode == "dict":
                        return self._send(200, json.dumps({"generators": fake.listing}).encode())
                    if mode == "noschema":
                        return self._send(200, json.dumps([{"name": e["name"], "parameters": ["x"]} for e in fake.listing]).encode())
                    if mode == "partial":
                        # equities' entry lost its schema; the others kept theirs
                        lst = [dict(e) for e in fake.listing]
                        for e in lst:
                            if e["name"] == "equities":
                                e.pop("schema")
                        return self._send(200, json.dumps(lst).encode())
                    return self._send(200, json.dumps(fake.listing).encode())
                if self.path.endswith("/artifact"):
                    if fake.artifact_mode == "train_only":
                        buf = io.BytesIO()
                        np.savez(buf, X_train=np.zeros((5, 2), dtype="float32"), y_train=np.zeros((5, 2), dtype="float32"))
                        return self._send(200, buf.getvalue(), "application/octet-stream")
                    return self._send(200, npz_bytes(fake.rows), "application/octet-stream")
                return self._send(404, b'{"detail":"nope"}')

            def do_POST(self) -> None:  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                with fake.lock:
                    fake.posts.append(body)
                if fake.create_mode == "422":
                    return self._send(422, json.dumps({"detail": "Shares outstanding could not be resolved. Re-submit with allow_truncation=true"}).encode())
                if fake.create_mode == "422_validation":
                    return self._send(422, json.dumps({"detail": [{"loc": ["params", "n_spirals"], "msg": "Input should be greater than or equal to 2", "type": "greater_than_equal"}]}).encode())
                return self._send(201, json.dumps({"dataset_id": "ds-%d" % len(fake.posts), "generator": body.get("generator"), "meta": fake.meta, "artifact_url": "/x"}).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
