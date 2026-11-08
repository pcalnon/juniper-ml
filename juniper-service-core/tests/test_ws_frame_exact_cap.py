"""A WebSocket text frame that fills the 64KB cap is still a frame.

Both channels reject with a strict ``>`` against 65536 characters
(``control_stream._MAX_MESSAGE_SIZE``, ``worker_stream._MAX_JSON_SIZE``).
The suites that already exist send 65537 characters on the control channel
and never send a frame of this length on the worker channel, so changing
``>`` to ``>=`` would drop a command, a keepalive, a registration, and a
heartbeat that fill the cap and still pass those suites.

The control channel closes (1009) one byte over the cap. Registration closes
(4005) one byte over it. The worker message loop reports the oversize frame
and keeps reading, so the next legal heartbeat is still acknowledged.
"""

from __future__ import annotations

import asyncio
import json
from collections import deque

import pytest
from fastapi import WebSocketDisconnect

from juniper_service_core.websocket import control_stream, worker_stream
from juniper_service_core.websocket.control_security import LeakyBucket
from juniper_service_core.websocket.control_stream import _control_recv_loop
from juniper_service_core.websocket.worker_stream import _handle_registration, _message_loop
from juniper_service_core.workers import JsonTaskProtocol, WorkerCoordinator, WorkerRegistry

_CAP = 65536


def _exact_json(fields: dict, size: int) -> str:
    """Compact JSON object of exactly ``size`` characters. The pad is only ``a``."""
    skeleton = {**fields, "pad": ""}
    base = json.dumps(skeleton, separators=(",", ":"))
    extra = size - len(base)
    assert extra >= 0, f"skeleton is already {len(base)} characters"
    skeleton["pad"] = "a" * extra
    raw = json.dumps(skeleton, separators=(",", ":"))
    assert len(raw) == size
    assert "\\" not in raw
    return raw


class _ControlWS:
    def __init__(self, incoming: list[str]) -> None:
        self._incoming = deque(incoming)
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(code=1000)
        return self._incoming.popleft()


class _RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(self, command: str, params: dict | None) -> dict:
        self.calls.append(command)
        return {"ok": True}


class _WorkerWS:
    def __init__(self, incoming: list[str]) -> None:
        self._incoming = deque(incoming)
        self.sent: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def send_bytes(self, data: bytes) -> None:
        self.sent.append({"bytes": len(data)})

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)

    async def receive_text(self) -> str:
        if not self._incoming:
            raise WebSocketDisconnect(1000)
        return self._incoming.popleft()

    async def receive(self) -> dict:
        if not self._incoming:
            raise WebSocketDisconnect(1000)
        return {"text": self._incoming.popleft()}


def test_both_channels_share_the_documented_64kb_cap() -> None:
    assert control_stream._MAX_MESSAGE_SIZE == _CAP
    assert worker_stream._MAX_JSON_SIZE == _CAP


@pytest.mark.asyncio
async def test_control_command_that_fills_the_cap_is_executed() -> None:
    raw = _exact_json({"command": "start"}, control_stream._MAX_MESSAGE_SIZE)
    executor = _RecordingExecutor()
    ws = _ControlWS([raw])

    with pytest.raises(WebSocketDisconnect):
        await _control_recv_loop(ws, executor, {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")

    assert executor.calls == ["start"]
    assert ws.closed is None
    assert any(m.get("type") == "command_response" and m["data"]["command"] == "start" and m["data"]["status"] == "success" for m in ws.sent)


@pytest.mark.asyncio
async def test_control_command_one_byte_over_the_cap_closes() -> None:
    raw = _exact_json({"command": "start"}, control_stream._MAX_MESSAGE_SIZE + 1)
    executor = _RecordingExecutor()
    ws = _ControlWS([raw, _exact_json({"command": "start"}, 32)])

    await _control_recv_loop(ws, executor, {"start"}, LeakyBucket(), asyncio.Event(), idle_timeout=0, client_ip="1.2.3.4")

    assert executor.calls == []
    assert ws.closed == (1009, "Message too large")
    assert ws.sent[-1]["data"]["error"] == "Message too large"


@pytest.mark.asyncio
async def test_control_pong_that_fills_the_cap_is_keepalive() -> None:
    raw = _exact_json({"type": "pong"}, control_stream._MAX_MESSAGE_SIZE)
    pong = asyncio.Event()
    ws = _ControlWS([raw])

    with pytest.raises(WebSocketDisconnect):
        await _control_recv_loop(ws, None, {"start"}, LeakyBucket(), pong, idle_timeout=0, client_ip="1.2.3.4")

    assert pong.is_set()
    assert ws.closed is None
    assert ws.sent == []


@pytest.mark.asyncio
async def test_worker_registration_that_fills_the_cap_registers() -> None:
    raw = _exact_json({"type": "register", "worker_id": "w1", "capabilities": {}}, worker_stream._MAX_JSON_SIZE)
    registry = WorkerRegistry()
    ws = _WorkerWS([raw])

    worker_id = await _handle_registration(ws, registry)

    assert worker_id is not None and worker_id.startswith("worker-")
    assert registry.worker_count == 1
    assert ws.closed is None
    assert any(m.get("type") == "registration_ack" and m.get("worker_id") == worker_id for m in ws.sent)


@pytest.mark.asyncio
async def test_worker_registration_one_byte_over_the_cap_closes() -> None:
    raw = _exact_json({"type": "register", "worker_id": "w1", "capabilities": {}}, worker_stream._MAX_JSON_SIZE + 1)
    registry = WorkerRegistry()
    ws = _WorkerWS([raw])

    worker_id = await _handle_registration(ws, registry)

    assert worker_id is None
    assert registry.worker_count == 0
    assert ws.closed == (4005, "Message too large")
    assert any(m.get("error") == "Registration message too large" for m in ws.sent)


@pytest.mark.asyncio
async def test_worker_heartbeat_that_fills_the_cap_is_acked() -> None:
    register = json.dumps({"type": "register", "worker_id": "w1", "capabilities": {}})
    heartbeat = _exact_json({"type": "heartbeat"}, worker_stream._MAX_JSON_SIZE)
    registry = WorkerRegistry()
    coordinator = WorkerCoordinator(registry, JsonTaskProtocol())
    ws = _WorkerWS([register, heartbeat])
    worker_id = await _handle_registration(ws, registry)
    assert worker_id is not None
    ws.sent.clear()

    with pytest.raises(WebSocketDisconnect):
        await _message_loop(ws, worker_id, registry, coordinator)

    assert ws.closed is None
    assert [m.get("type") for m in ws.sent] == ["heartbeat"]
    assert ws.sent[0]["worker_id"] == worker_id
    assert not any(m.get("error") == "Message too large" for m in ws.sent)


@pytest.mark.asyncio
async def test_worker_heartbeat_one_byte_over_keeps_the_connection() -> None:
    register = json.dumps({"type": "register", "worker_id": "w1", "capabilities": {}})
    over = _exact_json({"type": "heartbeat"}, worker_stream._MAX_JSON_SIZE + 1)
    follow = json.dumps({"type": "heartbeat"})
    registry = WorkerRegistry()
    coordinator = WorkerCoordinator(registry, JsonTaskProtocol())
    ws = _WorkerWS([register, over, follow])
    worker_id = await _handle_registration(ws, registry)
    assert worker_id is not None
    ws.sent.clear()

    with pytest.raises(WebSocketDisconnect):
        await _message_loop(ws, worker_id, registry, coordinator)

    assert ws.closed is None
    assert [m.get("error") for m in ws.sent if m.get("type") == "error"] == ["Message too large"]
    acks = [m for m in ws.sent if m.get("type") == "heartbeat"]
    assert len(acks) == 1 and acks[0]["worker_id"] == worker_id
