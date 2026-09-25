#!/usr/bin/env python3
"""Candidate 5(a): does a FastAPI 422 that echoes a lone-surrogate input become a 500?

Two apps, in-process via Starlette's TestClient (raise_server_exceptions=False):
  default  -- FastAPI's built-in RequestValidationError handler;
  copy     -- a handler written exactly like juniper-data's app.py:187-212 at main
              (JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})).
Body: {"n": "<lone surrogate>"} against a model whose n is an int. The surrogate is built
with chr() and sent as a JSON escape, never typed.
"""
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel


class Body(BaseModel):
    n: int


def make(copy: bool) -> FastAPI:
    app = FastAPI()
    if copy:
        @app.exception_handler(RequestValidationError)
        async def h(request: Request, exc: RequestValidationError) -> JSONResponse:
            return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": jsonable_encoder(exc.errors())})

    @app.post("/x")
    async def x(body: Body) -> dict:
        return {"n": body.n}

    return app


BS = chr(92)
payload = ('{"n": "' + BS + "ud800" + '"}').encode("ascii")
control = b'{"n": "abc"}'
for name, copy in (("default", False), ("data-style copy", True)):
    client = TestClient(make(copy), raise_server_exceptions=False)
    r1 = client.post("/x", content=control, headers={"Content-Type": "application/json"})
    r2 = client.post("/x", content=payload, headers={"Content-Type": "application/json"})
    print(f"{name:16s} control(non-int str): {r1.status_code} {r1.headers.get('content-type')} | lone surrogate: {r2.status_code} {r2.headers.get('content-type')}")
