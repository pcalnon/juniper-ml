#!/usr/bin/env python3
"""Lane A round 2: does uvicorn's h11 parser refuse the ~26.7 KB deep-cursor request "before the app sees it", as
the probe's new comment says? Serve a trivial ASGI app on 127.0.0.1 (ephemeral port) with http="h11" (and
"httptools" if importable), send the request (a) in one write, (b) in 1 KB writes with small pauses, and report
whether the app saw it. Run with JuniperCanopy1's python (uvicorn 0.49.0). The server is stopped at the end."""
import asyncio
import base64

import uvicorn

deep = base64.urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode("ascii").rstrip("=")
REQ = f"GET /v1/datasets?cursor={deep} HTTP/1.1\r\nHost: t\r\nConnection: close\r\n\r\n".encode("ascii")


async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    body = f"app saw query of {len(scope['query_string'])} bytes".encode()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": body})


async def client(port, chunk, pause):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    sent = 0
    try:
        if chunk is None:
            w.write(REQ)
            await w.drain()
            sent = len(REQ)
        else:
            for i in range(0, len(REQ), chunk):
                w.write(REQ[i:i + chunk])
                await w.drain()
                sent = min(len(REQ), i + chunk)
                await asyncio.sleep(pause)
    except (ConnectionResetError, BrokenPipeError) as e:
        pass
    try:
        data = await asyncio.wait_for(r.read(), timeout=10)
    except (ConnectionResetError, BrokenPipeError) as e:
        data = f"<{type(e).__name__} after sending {sent} bytes>".encode()
    w.close()
    head, _, body = data.partition(b"\r\n\r\n")
    first = head.split(b"\r\n", 1)[0].decode(errors="replace")
    return f"{first} | body: {body[:70]!r} (sent {sent} of {len(REQ)})"


async def main(http):
    cfg = uvicorn.Config(app, host="127.0.0.1", port=0, http=http, log_level="critical", lifespan="off")
    server = uvicorn.Server(cfg)
    task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        print(f"[{http}] one write      :", await client(port, None, 0))
        print(f"[{http}] 1 KB writes    :", await client(port, 1024, 0.01))
        print(f"[{http}] 8 KB writes    :", await client(port, 8192, 0.02))
    finally:
        server.should_exit = True
        await task


print("uvicorn", uvicorn.__version__, "request bytes", len(REQ))
asyncio.run(main("h11"))
try:
    import httptools  # noqa: F401
    asyncio.run(main("httptools"))
except ImportError:
    print("httptools not importable in this env")
