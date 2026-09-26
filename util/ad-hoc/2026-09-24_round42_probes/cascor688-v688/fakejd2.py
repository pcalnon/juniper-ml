"""A real-HTTP fake of juniper-data for probing cascor#686 (scratch only). Extends v678's fakejd with artifact shapes."""

from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

import numpy as np

LISTING: List[Dict[str, Any]] = [
    {"name": "spiral", "schema": {"type": "object", "properties": {"n_spirals": {"type": "integer"}}}},
    {"name": "csv_import", "schema": {"type": "object", "properties": {"allow_truncation": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}}}},
    {"name": "equities", "schema": {"type": "object", "properties": {"allow_truncation": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}}}},
]
PARTIAL_META: Dict[str, Any] = {"truncation": {"unit": "symbols", "cap": 14, "requested": 503, "imported": 14}}


def npz_bytes(mode: str, seed: int) -> bytes:
    """mode: three | train_val | train_test | train_only. 2 features, 2 outputs, so no padding ever replaces a tensor."""
    rng = np.random.default_rng(seed)
    arrays = {"X_train": rng.standard_normal((20, 2)).astype("float32"), "y_train": rng.standard_normal((20, 2)).astype("float32")}
    if mode in ("three", "train_val"):
        arrays["X_val"], arrays["y_val"] = rng.standard_normal((6, 2)).astype("float32"), rng.standard_normal((6, 2)).astype("float32")
    if mode in ("three", "train_test"):
        arrays["X_test"], arrays["y_test"] = rng.standard_normal((4, 2)).astype("float32"), rng.standard_normal((4, 2)).astype("float32")
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


class FakeJD:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.gen_mode = "ok"  # ok | 500
        self.create_mode = "ok"  # ok | 422
        self.meta: Dict[str, Any] = dict(PARTIAL_META)
        self.artifact_mode = "three"
        self.posts: List[Dict[str, Any]] = []
        self.gen_calls = 0
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:
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
                    if fake.gen_mode == "500":
                        return self._send(500, b'{"detail":"boom"}')
                    return self._send(200, json.dumps(LISTING).encode())
                if self.path.endswith("/artifact"):
                    return self._send(200, npz_bytes(fake.artifact_mode, len(fake.posts)), "application/octet-stream")
                return self._send(404, b'{"detail":"nope"}')

            def do_POST(self) -> None:  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                with fake.lock:
                    fake.posts.append(body)
                if fake.create_mode == "422":
                    return self._send(422, json.dumps({"detail": "Shares outstanding could not be resolved. Re-submit with allow_truncation=true"}).encode())
                return self._send(201, json.dumps({"dataset_id": "ds-%d" % len(fake.posts), "generator": body.get("generator"), "meta": fake.meta, "artifact_url": "/x"}).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
