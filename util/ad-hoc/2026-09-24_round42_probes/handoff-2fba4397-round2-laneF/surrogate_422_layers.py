#!/usr/bin/env python3
"""In-process probe (no ports): what does a lone-surrogate 422 echo become when the app ALSO registers
ValueError and Exception handlers, as juniper-data's app.py does (:187, :214, :238)?

Arms:
  A  FastAPI default 422 handler only
  B  data-style: copied RequestValidationError handler only
  C  data-style: copied 422 handler + ValueError handler (JSON 400) + Exception handler (JSON 500)
  D  C without the ValueError handler (Exception handler only)
Run with the primer venv (fastapi 0.141.1, starlette 1.6.0).
"""
import asyncio
import json

import fastapi
import httpx
import starlette
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class Body(BaseModel):
    n: int


def build(copy_422: bool, value_error: bool, exception: bool) -> FastAPI:
    app = FastAPI()

    if copy_422:
        @app.exception_handler(RequestValidationError)
        async def rve(request: Request, exc: RequestValidationError) -> JSONResponse:
            return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})

    if value_error:
        @app.exception_handler(ValueError)
        async def ve(request: Request, exc: ValueError) -> JSONResponse:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid request parameters"})

    if exception:
        @app.exception_handler(Exception)
        async def ge(request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.post("/x")
    async def x(body: Body) -> dict:
        return {"n": body.n}

    return app


async def hit(app: FastAPI, raw: bytes):
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.post("/x", content=raw, headers={"content-type": "application/json"})
        return r.status_code, r.headers.get("content-type"), r.text[:80]


async def main():
    surrogate = b'{"n": "\\ud800"}'  # JSON escape of a lone high surrogate
    control = b'{"n": "abc"}'
    arms = {
        "A default only": (False, False, False),
        "B copy only": (True, False, False),
        "C copy+ValueError+Exception": (True, True, True),
        "D copy+Exception": (True, False, True),
    }
    print("fastapi", fastapi.__version__, "starlette", starlette.__version__)
    for name, flags in arms.items():
        app = build(*flags)
        print(f"{name:30} control={await hit(app, control)}")
        print(f"{'':30} surrogate={await hit(app, surrogate)}")


asyncio.run(main())
