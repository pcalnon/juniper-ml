"""Minimal ASGI app: echo what the server's HTTP parser delivered for X-API-Key.

Reports the raw bytes uvicorn put into the ASGI scope and what Starlette's Request.headers
(latin-1 decode) yields, plus str.strip() of it and whether hmac.compare_digest accepts it.
"""

import hmac
import json

from starlette.requests import Request


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    raw = [v for k, v in scope["headers"] if k == b"x-api-key"]
    req = Request(scope)
    val = req.headers.get("X-API-Key")
    cmp = None
    if val is not None:
        try:
            hmac.compare_digest(val, val)
            cmp = "ok"
        except TypeError as exc:
            cmp = f"TypeError: {exc}"
    body = json.dumps({"raw": [r.hex() for r in raw], "starlette": None if val is None else [hex(ord(c)) for c in val], "stripped_empty": None if val is None else (val.strip() == ""), "compare_digest": cmp}).encode()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})
