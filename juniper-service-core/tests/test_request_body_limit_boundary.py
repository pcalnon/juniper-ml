"""The request-body cap admits a payload that fills it and rejects the next byte.

``RequestBodyLimitMiddleware`` compares with ``>`` in two places: the
``Content-Length`` early reject, and the cumulative stream read (CR-024).
The neighboring suites drive 5 bytes at a cap of 100 and 50 bytes at a cap
of 10, so either comparison can flip to ``>=`` and those suites stay green
while a body that exactly fills the cap starts returning 413.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI, Request

from juniper_service_core.middleware import RequestBodyLimitMiddleware

CAP = 10


def _app(max_bytes: int = CAP) -> tuple[FastAPI, list[bytes]]:
    app = FastAPI()
    seen: list[bytes] = []

    @app.post("/v1/echo")
    async def echo(request: Request) -> dict[str, int]:
        body = await request.body()
        seen.append(body)
        return {"n": len(body)}

    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=max_bytes)
    return app, seen


async def _drive(app: FastAPI, *, headers: list[tuple[bytes, bytes]] | None = None, chunks: list[bytes]) -> tuple[int, bytes]:
    sent: list[dict] = []
    pending = list(chunks)
    index = 0

    async def receive() -> dict:
        nonlocal index
        if index < len(pending):
            body = pending[index]
            index += 1
            return {"type": "http.request", "body": body, "more_body": index < len(pending)}
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/echo",
        "raw_path": b"/v1/echo",
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    await app(scope, receive, send)
    start = next(message for message in sent if message["type"] == "http.response.start")
    payload = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return start["status"], payload


def _post(max_bytes: int = CAP, *, headers: list[tuple[bytes, bytes]] | None = None, chunks: list[bytes]) -> tuple[list[bytes], int, dict]:
    app, seen = _app(max_bytes)
    status, payload = asyncio.run(_drive(app, headers=headers, chunks=chunks))
    return seen, status, json.loads(payload)


def test_a_body_that_fills_the_cap_is_delivered() -> None:
    body = b"x" * CAP
    seen, status, payload = _post(chunks=[body])
    assert status == 200
    assert seen == [body]
    assert payload == {"n": CAP}


def test_one_byte_over_the_cap_is_rejected_and_the_route_is_not_called() -> None:
    seen, status, payload = _post(chunks=[b"x" * (CAP + 1)])
    assert status == 413
    assert payload == {"detail": "Request body too large"}
    assert seen == []


def test_content_length_equal_to_the_cap_is_admitted() -> None:
    body = b"y" * CAP
    seen, status, payload = _post(headers=[(b"content-length", str(CAP).encode())], chunks=[body])
    assert status == 200
    assert seen == [body]
    assert payload == {"n": CAP}


def test_content_length_one_byte_over_the_cap_is_rejected_before_the_route() -> None:
    seen, status, payload = _post(headers=[(b"content-length", str(CAP + 1).encode())], chunks=[b""])
    assert status == 413
    assert payload == {"detail": "Request body too large"}
    assert seen == []


def test_a_content_length_at_the_cap_still_rejects_one_extra_byte() -> None:
    seen, status, payload = _post(headers=[(b"content-length", str(CAP).encode())], chunks=[b"x" * (CAP + 1)])
    assert status == 413
    assert payload == {"detail": "Request body too large"}
    assert seen == []


def test_chunks_that_sum_to_the_cap_are_delivered_whole() -> None:
    first, second = b"abcdef", b"ghij"
    assert len(first) + len(second) == CAP
    seen, status, payload = _post(chunks=[first, second])
    assert status == 200
    assert seen == [first + second]
    assert payload == {"n": CAP}


def test_the_chunk_that_crosses_the_cap_is_rejected() -> None:
    seen, status, payload = _post(chunks=[b"abcdef", b"ghijk"])
    assert status == 413
    assert payload == {"detail": "Request body too large"}
    assert seen == []


def test_an_empty_body_is_admitted_when_the_cap_is_zero() -> None:
    seen, status, payload = _post(max_bytes=0, chunks=[b""])
    assert status == 200
    assert seen == [b""]
    assert payload == {"n": 0}
    seen, status, payload = _post(max_bytes=0, chunks=[b"x"])
    assert status == 413
    assert payload == {"detail": "Request body too large"}
    assert seen == []
