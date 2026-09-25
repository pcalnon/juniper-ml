"""canopy main's own SecurityMiddleware + APIKeyAuth + RateLimiter under REAL uvicorn (no Sentry, no network)."""
import socket
import sys
import threading
import time

sys.path.insert(0, sys.argv[1])
from fastapi import FastAPI  # noqa: E402

import middleware  # noqa: E402  canopy src/middleware.py
import security  # noqa: E402  canopy src/security.py

app = FastAPI()


@app.get("/api/status")
def status():
    return {"ok": True}


@app.get("/api/csrf")
def csrf():
    return {"ok": True}


auth = security.APIKeyAuth(["canopy-real-key"])
app.add_middleware(middleware.SecurityMiddleware, api_key_auth=auth, rate_limiter=security.RateLimiter(requests_per_minute=1000, enabled=True))

import uvicorn  # noqa: E402

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 0))
port = sock.getsockname()[1]
server = uvicorn.Server(uvicorn.Config(app, http=sys.argv[2], lifespan="off", log_level="critical"))
threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True).start()
while not server.started:
    time.sleep(0.05)


def get(path, hdrs):
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    s.sendall(b"GET " + path + b" HTTP/1.1\r\nHost: x\r\n" + b"".join(h + b"\r\n" for h in hdrs) + b"Connection: close\r\n\r\n")
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return data.split(b"\r\n", 1)[0].decode()


print(f"[canopy main / {sys.argv[2]}]")
print("  /api/status  X-API-Key: \\xa0            ->", get(b"/api/status", [b"X-API-Key: \xa0"]))
print("  /api/status  X-API-Key: wrong-ascii      ->", get(b"/api/status", [b"X-API-Key: wrong-ascii"]))
print("  /api/csrf    X-Canopy-Internal: \\xa0    ->", get(b"/api/csrf", [b"X-Canopy-Internal: \xa0"]), "(key-exempt path, anonymous)")
server.should_exit = True
