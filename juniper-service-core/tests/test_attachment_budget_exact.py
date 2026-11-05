"""Exact edges of the worker-result attachment budget (APD-SVCCORE-001).

``_handle_task_result`` refuses a declaration with ``>``, not ``>=``, on three independent caps:
how many binary frames one result may name, how large each frame may be, and how large their sum
may be. The suites that already reject an over-long list, an oversize frame, and a sum past a
monkeypatched budget never send a value that lands on the cap, so changing any ``>`` to ``>=``
still passes them and refuses a legitimate full manifest, a frame of the documented maximum, or a
submission whose bytes add up to the budget exactly.

Self-contained doubles. Does not import the coordinator or worker-stream edge suites.
"""

from __future__ import annotations

from collections import deque

import pytest

from juniper_service_core.websocket import worker_stream as worker_stream_module
from juniper_service_core.workers import ParsedResult, WorkerCoordinator, WorkerRegistry


class _RecordingProtocol:
    """Records the frame dict ``parse_result`` actually receives."""

    def __init__(self) -> None:
        self.seen: list[dict[str, bytes]] = []

    def build_assignment(self, task):
        return ({"type": "task_assign", "task_id": task.task_id, "round_id": task.round_id, "payload": task.payload}, [])

    def result_attachments(self, msg):
        return list(msg.get("attachments", []))

    def parse_result(self, worker_id, msg, frames):
        self.seen.append(dict(frames))
        if "task_id" not in msg:
            return None
        return ParsedResult(success=True, result={"task_id": msg["task_id"]}, score=None)


class _FakeSocket:
    def __init__(self, inbound: list[tuple[str, bytes]]) -> None:
        self._inbound = deque(inbound)
        self.sent: list[dict] = []

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def receive(self) -> dict:
        kind, payload = self._inbound.popleft()
        return {"text": payload} if kind == "text" else {"bytes": payload}


def _assigned() -> tuple[_RecordingProtocol, WorkerRegistry, WorkerCoordinator, str]:
    protocol = _RecordingProtocol()
    registry = WorkerRegistry()
    registry.register("node-a", {})
    coordinator = WorkerCoordinator(registry, protocol)
    (task_id,) = coordinator.submit_tasks("round-1", [{"c": 0}])
    assert coordinator.get_next_assignment("node-a") is not None
    return protocol, registry, coordinator, task_id


async def _submit(names: list[str], payloads: list[bytes]) -> tuple[_RecordingProtocol, WorkerRegistry, WorkerCoordinator, str, _FakeSocket]:
    protocol, registry, coordinator, task_id = _assigned()
    socket = _FakeSocket([("bytes", payload) for payload in payloads])
    await worker_stream_module._handle_task_result(socket, "node-a", {"task_id": task_id, "attachments": names}, coordinator)
    return protocol, registry, coordinator, task_id, socket


def _task(coordinator: WorkerCoordinator, task_id: str):
    return coordinator._pending_tasks[task_id]


@pytest.mark.asyncio
async def test_a_full_attachment_list_is_accepted() -> None:
    """Exactly ``_MAX_ATTACHMENTS`` frames are read and submitted.

    The refusal one past the cap is already pinned. This is the other side: a result that names
    the whole allowance, which is the cascor tensor-manifest maximum this constant mirrors.
    """
    count = worker_stream_module._MAX_ATTACHMENTS
    names = [f"t{i}" for i in range(count)]
    payloads = [bytes([i]) for i in range(count)]

    protocol, registry, coordinator, task_id, socket = await _submit(names, payloads)

    assert protocol.seen == [dict(zip(names, payloads, strict=True))]
    assert _task(coordinator, task_id).completed is True
    assert registry.get("node-a").idle is True
    assert socket._inbound == deque()
    assert socket.sent[-1] == {"type": "result_ack", "task_id": task_id, "status": "accepted"}


@pytest.mark.asyncio
async def test_a_frame_that_fills_the_per_frame_cap_is_delivered(monkeypatch: pytest.MonkeyPatch) -> None:
    """A frame of exactly ``_MAX_BINARY_SIZE`` is the result; one byte over is not, and frees the worker.

    The cap is lowered so the arm does not allocate the shipped 100 MiB. The total budget stays at
    its shipped value, so this arm cannot pass by way of the sum check.
    """
    monkeypatch.setattr(worker_stream_module, "_MAX_BINARY_SIZE", 8)
    exact = b"01234567"
    protocol, registry, coordinator, task_id, socket = await _submit(["blob"], [exact])

    assert protocol.seen == [{"blob": exact}]
    assert _task(coordinator, task_id).completed is True
    assert socket.sent[-1]["status"] == "accepted"
    assert registry.get("node-a").idle is True

    protocol, registry, coordinator, task_id, socket = await _submit(["blob"], [exact + b"x"])

    assert protocol.seen == []
    assert _task(coordinator, task_id).completed is False
    assert _task(coordinator, task_id).assigned_worker_id is None
    assert registry.get("node-a").idle is True
    assert socket.sent[-1]["error"] == "Binary frame too large"


@pytest.mark.asyncio
async def test_frames_that_sum_to_the_total_budget_are_delivered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Frames whose lengths add up to ``_MAX_TOTAL_BINARY_SIZE`` are delivered; one byte over is not.

    Each frame is under the per-frame cap, so a sum check written as ``>=`` is the only change that
    refuses the exact budget. The frame declared after the one that crosses the budget is left
    unread: the check returns on that frame instead of draining the rest of the list.
    """
    monkeypatch.setattr(worker_stream_module, "_MAX_BINARY_SIZE", 100)
    monkeypatch.setattr(worker_stream_module, "_MAX_TOTAL_BINARY_SIZE", 10)
    first, second = b"abcd", b"efghij"

    protocol, _registry, coordinator, task_id, socket = await _submit(["a", "b"], [first, second])

    assert protocol.seen == [{"a": first, "b": second}]
    assert _task(coordinator, task_id).completed is True
    assert socket._inbound == deque()
    assert socket.sent[-1]["status"] == "accepted"

    protocol, _registry, coordinator, task_id, socket = await _submit(["a", "b", "c"], [first, second + b"x", b"leftover"])

    assert protocol.seen == []
    assert _task(coordinator, task_id).completed is False
    assert socket._inbound == deque([("bytes", b"leftover")])
    assert socket.sent[-1]["error"] == "Binary attachments exceed total size limit"


@pytest.mark.asyncio
async def test_a_zero_total_budget_still_admits_an_empty_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """A total budget of 0 admits an empty frame and refuses the first byte.

    The per-frame cap stays above that byte, so the refusal is the sum check. ``>=`` would refuse
    the empty frame, which adds nothing.
    """
    monkeypatch.setattr(worker_stream_module, "_MAX_BINARY_SIZE", 8)
    monkeypatch.setattr(worker_stream_module, "_MAX_TOTAL_BINARY_SIZE", 0)

    protocol, _registry, coordinator, task_id, socket = await _submit(["a"], [b""])

    assert protocol.seen == [{"a": b""}]
    assert _task(coordinator, task_id).completed is True
    assert socket.sent[-1]["status"] == "accepted"

    protocol, _registry, coordinator, task_id, socket = await _submit(["a"], [b"x"])

    assert protocol.seen == []
    assert _task(coordinator, task_id).completed is False
    assert socket.sent[-1]["error"] == "Binary attachments exceed total size limit"
