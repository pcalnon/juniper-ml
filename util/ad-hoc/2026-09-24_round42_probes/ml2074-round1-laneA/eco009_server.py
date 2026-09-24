#!/usr/bin/env python3
"""Lane A: a minimal app behind canopy's own RequestBodyLimitMiddleware (origin/main copy), cap 32 bytes.
usage: eco009_server.py <port> <h11|httptools>"""
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, f"{S}/src/juniper-canopy/src")

import uvicorn  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402

import middleware  # noqa: E402  canopy's src/middleware.py


async def echo(request: Request):
    body = await request.body()
    return JSONResponse({"received": len(body)})


app = Starlette(routes=[Route("/echo", echo, methods=["POST"])])
app.add_middleware(middleware.RequestBodyLimitMiddleware, max_bytes=32)
print("middleware from", middleware.__file__, flush=True)
uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]), http=sys.argv[2], log_level="warning")
