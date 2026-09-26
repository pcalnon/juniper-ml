"""Drive a REAL uvicorn server with raw-socket non-ASCII X-API-Key requests (HTTP and WS).

Optionally initialise the REAL Sentry SDK through the service's own configure path, with a
capturing transport injected (no network), and report whether any envelope carries the secret.

python svc_probe.py --service sc|data|cascor --parser h11|httptools [--sentry] [--path P ...]
"""

import argparse
import json
import logging
import os
import socket
import sys
import tempfile
import threading
import time

p = argparse.ArgumentParser()
p.add_argument("--service", required=True, choices=["sc", "data", "cascor"])
p.add_argument("--parser", default="h11", choices=["h11", "httptools"])
p.add_argument("--sentry", action="store_true")
p.add_argument("--path", nargs="*", default=[])
p.add_argument("--scratch", default=os.path.dirname(os.path.abspath(__file__)))
args = p.parse_args()
for entry in reversed(args.path):
    sys.path.insert(0, entry)

SECRET = "-".join(("real", "configured", "key", "LEAKMARK", "9c1e"))
SECRET2 = "-".join(("second", "configured", "key", "LEAKMARK", "4b2d"))
DSN = "http://public@127.0.0.1:9/1"  # never contacted: the transport is replaced

envelopes = []
init_kwargs = []
if args.sentry:
    import sentry_sdk
    from sentry_sdk.transport import Transport

    class Capturing(Transport):
        def __init__(self):
            super().__init__()

        def capture_envelope(self, envelope):
            envelopes.append(envelope)

    _real_init = sentry_sdk.init

    def _init(*a, **kw):
        assert kw.get("dsn", DSN).startswith("http://public@127.0.0.1:"), "refusing a non-local DSN"
        kw["transport"] = Capturing()
        init_kwargs.append(sorted(k for k in kw if k not in ("transport",)))
        return _real_init(*a, **kw)

    sentry_sdk.init = _init

if args.service == "sc":
    from fastapi import FastAPI, WebSocket
    from juniper_service_core.middleware import SecurityMiddleware
    from juniper_service_core.security import APIKeyAuth, RateLimiter
    from juniper_service_core.websocket.manager import ws_authenticate

    app = FastAPI()

    @app.get("/v1/data")
    def _data():
        return {"ok": True}

    @app.websocket("/ws/training")
    async def _ws(websocket: WebSocket):
        if not await ws_authenticate(websocket):
            return
        await websocket.accept()
        await websocket.close()

    auth = APIKeyAuth([SECRET, SECRET2])
    app.add_middleware(SecurityMiddleware, api_key_auth=auth, rate_limiter=RateLimiter(enabled=False))
    app.state.api_key_auth = auth
    if args.sentry:
        from juniper_observability import configure_sentry

        configure_sentry(DSN, "probe-sc", "0")
    http_path, ws_path = "/v1/data", "/ws/training"
    import juniper_service_core.security as sec_mod
elif args.service == "data":
    from juniper_data.api.app import create_app
    from juniper_data.api.settings import Settings

    tmp = tempfile.mkdtemp(dir=args.scratch, prefix="data-store-")
    settings = Settings(storage_path=tmp, api_keys=[SECRET, SECRET2], sentry_dsn=DSN if args.sentry else None)
    app = create_app(settings=settings)
    http_path, ws_path = "/v1/generators", None
    import juniper_data.api.security as sec_mod
else:
    from api.app import create_app
    from api.settings import Settings

    settings = Settings(api_keys=[SECRET, SECRET2], sentry_dsn=DSN if args.sentry else None, host="127.0.0.1")
    app = create_app(settings=settings)
    http_path, ws_path = "/v1/workers", "/ws/training"
    import api.security as sec_mod

import juniper_observability  # noqa: E402

print(f"security module: {sec_mod.__file__}")
print(f"observability:   {juniper_observability.__file__}")
if args.sentry:
    print(f"sentry-sdk {sentry_sdk.VERSION}")

import uvicorn  # noqa: E402

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 0))
port = sock.getsockname()[1]
config = uvicorn.Config(app, http=args.parser, ws="websockets", lifespan="on", log_level="warning")
server = uvicorn.Server(config)
thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
thread.start()
deadline = time.time() + 60
while not server.started and time.time() < deadline:
    time.sleep(0.05)
assert server.started, "uvicorn did not start"

exc_records = []


class _Grab(logging.Handler):
    def emit(self, record):
        if record.exc_info:
            exc_records.append(f"{record.name}: {record.getMessage()} [{record.exc_info[0].__name__}]")


for name in ("uvicorn.error", "uvicorn", ""):
    logging.getLogger(name).addHandler(_Grab())


_src_counter = [0]


def raw(request: bytes, stop_at_head: bool = False) -> bytes:
    # A fresh loopback SOURCE address per request (all of 127/8 is loopback on Linux), so the
    # services' FailedAuthThrottle -- left at its production default -- never masks a status.
    n = _src_counter[0]
    _src_counter[0] += 1
    src = f"127.1.{n // 250}.{n % 250 + 1}"
    s = socket.create_connection(("127.0.0.1", port), timeout=5, source_address=(src, 0))
    s.sendall(request)
    data = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            if stop_at_head and b"\r\n\r\n" in data:
                break
    except socket.timeout:
        pass
    finally:
        s.close()
    return data


def status_of(resp: bytes):
    line = resp.split(b"\r\n", 1)[0]
    if line.startswith(b"HTTP/"):
        return int(line.split()[1])
    return f"no-status({resp[:40]!r})"


def http(headers: list[bytes]) -> object:
    req = b"GET " + http_path.encode() + b" HTTP/1.1\r\nHost: 127.0.0.1\r\n" + b"".join(h + b"\r\n" for h in headers) + b"Connection: close\r\n\r\n"
    return status_of(raw(req))


def ws(headers: list[bytes]) -> object:
    req = b"GET " + ws_path.encode() + b" HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n" + b"".join(h + b"\r\n" for h in headers) + b"\r\n"
    return status_of(raw(req, stop_at_head=True))


results = {}
# every single byte as the whole key (CR and LF end the line, so they are not a value)
for b in range(256):
    if b in (0x0A, 0x0D):
        continue
    results[f"byte 0x{b:02x}"] = http([b"X-API-Key: " + bytes([b])])
specials = {
    "guess+\\xa0": [b"X-API-Key: guess-key\xa0"],
    "utf8 e-acute": [b"X-API-Key: \xc3\xa9"],
    "8000 x \\xff": [b"X-API-Key: " + b"\xff" * 8000],
    "dup: \\xa0 then valid": [b"X-API-Key: \xa0", b"X-API-Key: " + SECRET.encode()],
    "dup: valid then \\xa0": [b"X-API-Key: " + SECRET.encode(), b"X-API-Key: \xa0"],
    "valid": [b"X-API-Key: " + SECRET.encode()],
    "missing": [],
    "empty": [b"X-API-Key: "],
    "nbsp-padded valid": [b"X-API-Key: \xa0" + SECRET.encode() + b"\xa0"],
}
for label, hdrs in specials.items():
    results[label] = http(hdrs)
ws_results = {}
if ws_path:
    for label, hdrs in {"\\xa0": [b"X-API-Key: \xa0"], "\\x85": [b"X-API-Key: \x85"], "guess+\\xa0": [b"X-API-Key: guess-key\xa0"], "8000 x \\xff": [b"X-API-Key: " + b"\xff" * 8000], "missing": [], "valid": [b"X-API-Key: " + SECRET.encode()]}.items():
        ws_results[label] = ws(hdrs)

time.sleep(0.3)
if args.sentry:
    sentry_sdk.flush(timeout=5)
server.should_exit = True
thread.join(timeout=20)
if args.sentry:
    sentry_sdk.flush(timeout=5)

by_status = {}
for label, st in results.items():
    by_status.setdefault(str(st), []).append(label)
print(f"[{args.service}/{args.parser}] HTTP status histogram:")
for st, labels in sorted(by_status.items()):
    shown = ", ".join(labels[:6]) + (f", ... (+{len(labels) - 6})" if len(labels) > 6 else "")
    print(f"   {st}: {len(labels)} cases  [{shown}]")
if ws_results:
    print(f"[{args.service}/{args.parser}] WS handshake: {ws_results}")
print(f"[{args.service}/{args.parser}] exception log records: {len(exc_records)} {exc_records[:2]}")

if args.sentry:
    wire = b"\n".join(e.serialize() for e in envelopes)
    item_types = {}
    error_events = 0
    frames_with_vars = 0
    for e in envelopes:
        for item in e.items:
            item_types[item.type] = item_types.get(item.type, 0) + 1
        ev = e.get_event()
        if ev and ev.get("exception"):
            error_events += 1
            for value in ev["exception"].get("values", []):
                for fr in (value.get("stacktrace") or {}).get("frames", []):
                    if "vars" in fr:
                        frames_with_vars += 1
    print(f"[{args.service}/{args.parser}] sentry init kwargs: {init_kwargs}")
    print(f"[{args.service}/{args.parser}] envelopes={len(envelopes)} items={item_types} error_events={error_events} frames_with_vars={frames_with_vars}")
    for name, sec in (("SECRET", SECRET), ("SECRET2", SECRET2)):
        n = wire.count(sec.encode())
        print(f"[{args.service}/{args.parser}] {name} ON THE WIRE: {n > 0} (occurrences: {n})")
        if n:
            i = wire.find(sec.encode())
            print("   context:", wire[max(0, i - 160): i + 40].decode("utf-8", "replace").replace("\n", " "))
