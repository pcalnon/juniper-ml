"""Both-stacks-green contract test for the WS-2 / OUT-11 T2 step-2 websocket subsystem.

Drives EVERY generic websocket channel with model-core's regression stubs -- the RK-6 guard:
because the driver is a *regression* model, no classification assumption (argmax / accuracy) or
cascade assumption (candidate / correlation) can hide in "generic" code, and the base is proven
independently of cascor (cascor is untouched by this PR).

Coverage:

* ``WebSocketManager`` -- sequencing, replay buffer (+ out-of-range), oversized-message chunking,
  global + per-IP connection limits, and broadcast fan-out (with a lightweight fake socket).
* ``ws_authenticate`` -- allow-when-unconfigured + the enabled valid/invalid arms.
* The lifecycle -> broadcast **bridge** -- live training frames (metrics / state) and replay
  frames (FW-3) reach a recording websocket manager.
* ``/ws/training`` -- the connect handshake, fresh-connect initial burst, and the resume path
  (success + server-restart rejection), via ``TestClient.websocket_connect``.
* ``/ws/control`` -- the executor-driven command channel: start / set_params / reset acks, the
  invalid-state and unknown-command error arms, and the leaky-bucket rate limit.
"""

from __future__ import annotations

import types

import pytest
from fastapi.testclient import TestClient
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceGrowableModel, ReferenceLinearModel, ReferenceLinearSerializer

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.routes import build_routers
from juniper_service_core.security import build_api_key_auth
from juniper_service_core.websocket import (
    LifecycleCommandExecutor,
    ReplayOutOfRange,
    WebSocketManager,
    attach_websocket,
    build_frame_sink,
    build_websocket_router,
    ws_authenticate,
)

# ======================================================================================
# Test doubles
# ======================================================================================


class FakeWebSocket:
    """A minimal async WebSocket stand-in for ``WebSocketManager`` unit tests."""

    def __init__(self, client=("1.2.3.4", 5000), headers: dict | None = None, app=None):
        self.client = client
        self.headers = headers or {}
        self.app = app
        self.sent: list[dict] = []
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.closed = (code, reason)


class RecordingWsManager:
    """Captures ``broadcast_from_thread`` calls so the bridge can be asserted synchronously."""

    def __init__(self) -> None:
        self.broadcasts: list[dict] = []

    def broadcast_from_thread(self, message: dict) -> None:
        self.broadcasts.append(message)


def _fast_ws_settings(**overrides) -> types.SimpleNamespace:
    """Settings stub that makes the handlers run fast + deterministic under TestClient.

    A short resume timeout avoids a multi-second handshake wait; the heartbeat + idle timeouts
    are pushed far out so neither the ping loop nor an idle close interleaves with the messages
    a test asserts on.
    """
    base = dict(
        ws_resume_handshake_timeout_s=0.2,
        ws_initial_metrics_count=50,
        ws_heartbeat_interval_sec=3600,
        ws_heartbeat_pong_timeout_sec=3600,
        ws_control_idle_timeout_sec=3600,
        ws_control_rate_limit_per_sec=10,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


# ======================================================================================
# WebSocketManager -- sequencing + replay (synchronous surface)
# ======================================================================================


def test_assign_seq_is_monotonic_and_buffered() -> None:
    mgr = WebSocketManager(max_replay_buffer_size=10)
    e1 = mgr._assign_seq_and_buffer({"type": "metrics", "data": {"mse": 1.0}})
    e2 = mgr._assign_seq_and_buffer({"type": "metrics", "data": {"mse": 0.5}})
    assert e1["seq"] == 1
    assert e2["seq"] == 2
    assert "emitted_at_monotonic" in e1
    assert mgr.current_seq == 2


def test_replay_since_returns_tail() -> None:
    mgr = WebSocketManager(max_replay_buffer_size=10)
    for i in range(3):
        mgr._assign_seq_and_buffer({"type": "metrics", "data": {"i": i}})
    assert [m["seq"] for m in mgr.replay_since(0)] == [1, 2, 3]
    assert [m["seq"] for m in mgr.replay_since(2)] == [3]
    assert mgr.replay_since(3) == []


def test_replay_since_out_of_range_raises() -> None:
    mgr = WebSocketManager(max_replay_buffer_size=2)
    for i in range(5):  # overflow the 2-slot buffer (oldest evicted)
        mgr._assign_seq_and_buffer({"type": "metrics", "data": {"i": i}})
    # Oldest buffered seq is 4; requesting seq 1 is no longer continuity-verifiable.
    with pytest.raises(ReplayOutOfRange):
        mgr.replay_since(1)


def test_replay_buffer_disabled_raises() -> None:
    mgr = WebSocketManager(max_replay_buffer_size=0)
    with pytest.raises(ReplayOutOfRange):
        mgr.replay_since(0)


# ======================================================================================
# WebSocketManager -- chunking
# ======================================================================================


def test_small_message_is_not_chunked() -> None:
    mgr = WebSocketManager()
    msg = {"type": "metrics", "data": {"mse": 0.1}}
    assert mgr._maybe_chunk_message(msg) == [msg]


def test_oversized_message_is_chunked() -> None:
    mgr = WebSocketManager(max_message_size_bytes=200, chunk_payload_size_bytes=64)
    big = {"type": "topology", "data": {"blob": "x" * 1000}}
    chunks = mgr._maybe_chunk_message(big)
    assert len(chunks) > 1
    assert all(c["type"] == "chunked_message" for c in chunks)
    # Reassembling the payloads in order reconstructs the original serialized JSON.
    assert {c["data"]["chunk_index"] for c in chunks} == set(range(len(chunks)))
    assert chunks[0]["data"]["original_type"] == "topology"


def test_chunking_killswitch_passes_through() -> None:
    mgr = WebSocketManager(max_message_size_bytes=0)
    big = {"type": "topology", "data": {"blob": "x" * 5000}}
    assert mgr._maybe_chunk_message(big) == [big]


# ======================================================================================
# WebSocketManager -- connection lifecycle + broadcast (async)
# ======================================================================================


@pytest.mark.asyncio
async def test_broadcast_assigns_seq_and_fans_out() -> None:
    mgr = WebSocketManager()
    ws1 = FakeWebSocket(client=("1.1.1.1", 1))
    ws2 = FakeWebSocket(client=("2.2.2.2", 2))
    assert await mgr.connect(ws1)
    assert await mgr.connect(ws2)
    # connect sent each a connection_established frame.
    assert ws1.sent[0]["type"] == "connection_established"

    await mgr.broadcast({"type": "metrics", "data": {"mse": 0.25}})
    assert ws1.sent[-1]["type"] == "metrics"
    assert ws1.sent[-1]["seq"] == 1
    assert ws2.sent[-1]["seq"] == 1  # same broadcast seq to every client


@pytest.mark.asyncio
async def test_global_connection_limit() -> None:
    mgr = WebSocketManager(max_connections=1)
    a = FakeWebSocket(client=("1.1.1.1", 1))
    b = FakeWebSocket(client=("2.2.2.2", 2))
    assert await mgr.connect(a)
    assert not await mgr.connect(b)
    assert b.closed is not None and b.closed[0] == 1013


@pytest.mark.asyncio
async def test_per_ip_connection_limit() -> None:
    mgr = WebSocketManager(max_connections_per_ip=2)
    conns = [FakeWebSocket(client=("9.9.9.9", i)) for i in range(3)]
    assert await mgr.connect(conns[0])
    assert await mgr.connect(conns[1])
    assert not await mgr.connect(conns[2])  # third from the same IP is rejected
    assert conns[2].closed is not None and conns[2].closed[0] == 1013
    # A disconnect releases the slot so a later connect from that IP succeeds.
    await mgr.disconnect(conns[0])
    assert await mgr.connect(conns[2])


@pytest.mark.asyncio
async def test_broadcast_from_thread_is_noop_without_loop() -> None:
    mgr = WebSocketManager()
    # No event loop captured -> a thread broadcast is a safe no-op (does not raise).
    mgr.broadcast_from_thread({"type": "metrics", "data": {}})


# ======================================================================================
# ws_authenticate
# ======================================================================================


@pytest.mark.asyncio
async def test_ws_authenticate_allows_when_unconfigured() -> None:
    ws = FakeWebSocket(app=types.SimpleNamespace(state=types.SimpleNamespace()))
    assert await ws_authenticate(ws) is True


@pytest.mark.asyncio
async def test_ws_authenticate_enabled_valid_and_invalid() -> None:
    auth = build_api_key_auth(["s3cret"])
    app = types.SimpleNamespace(state=types.SimpleNamespace(api_key_auth=auth))
    ok = FakeWebSocket(headers={"X-API-Key": "s3cret"}, app=app)
    bad = FakeWebSocket(headers={"X-API-Key": "nope"}, app=app)
    assert await ws_authenticate(ok) is True
    assert await ws_authenticate(bad) is False
    assert bad.closed is not None and bad.closed[0] == 4001


# ======================================================================================
# Lifecycle -> broadcast bridge (live training frames + replay frames / FW-3)
# ======================================================================================


def test_bridge_pushes_live_training_frames() -> None:
    ds = tiny_regression_2d()
    recording = RecordingWsManager()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    manager.set_frame_sink(build_frame_sink(recording))
    try:
        manager.start_training(ds.X, ds.y)
        assert manager.join(timeout=5.0)
    finally:
        manager.shutdown()

    types_seen = {b["type"] for b in recording.broadcasts}
    assert "state" in types_seen  # training_start / training_end emit state frames
    assert "metrics" in types_seen  # epoch_end emits metrics frames
    # RK-6: a regression model never reports accuracy, even through the live stream.
    metric_frames = [b for b in recording.broadcasts if b["type"] == "metrics"]
    assert all("accuracy" not in (b["data"].get("metrics") or {}) for b in metric_frames)


def test_bridge_pushes_replay_frames(tmp_path) -> None:
    ds = tiny_regression_2d()
    recording = RecordingWsManager()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    try:
        manager.start_training(ds.X, ds.y)
        assert manager.join(timeout=5.0)
        snapshot_id = manager.save_snapshot()["id"]
        # Wire the sink only now, so the only frames recorded are replay frames.
        manager.set_frame_sink(build_frame_sink(recording))
        manager.start_replay(snapshot_id)  # ReplaySession.start() emits the initial frame
    finally:
        manager.shutdown()

    assert recording.broadcasts, "replay did not push any frame through the sink (FW-3)"
    first = recording.broadcasts[0]
    assert first["type"] == "metrics"
    assert first["data"]["replay"] is True
    assert first["data"]["snapshot_id"] == snapshot_id


def test_frame_sink_unset_is_silent() -> None:
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())  # no frame_sink
    try:
        manager.start_training(ds.X, ds.y)
        assert manager.join(timeout=5.0)
        # No sink wired -> training completes normally and history is still recorded.
        assert manager.get_metrics_history()
    finally:
        manager.shutdown()


# ======================================================================================
# /ws/training channel (TestClient.websocket_connect)
# ======================================================================================


@pytest.fixture
def training_client():
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    app = create_app(routers=[*build_routers(), build_websocket_router()])
    app.state.settings = _fast_ws_settings()
    attach_websocket(app, manager=manager, ws_manager=WebSocketManager())
    with TestClient(app) as client:
        yield client, manager, ds
    manager.shutdown()


def test_training_fresh_connect_sends_initial_burst(training_client) -> None:
    client, _manager, _ds = training_client
    with client.websocket_connect("/ws/training") as ws:
        established = ws.receive_json()
        assert established["type"] == "connection_established"
        assert "server_instance_id" in established["data"]
        # Send a non-resume frame to short-circuit the resume-handshake wait.
        ws.send_json({"type": "noop"})
        assert ws.receive_json()["type"] == "initial_status"
        assert ws.receive_json()["type"] == "state"
        assert ws.receive_json()["type"] == "initial_metrics"


def test_training_resume_success_replays_zero(training_client) -> None:
    client, _manager, _ds = training_client
    with client.websocket_connect("/ws/training") as ws:
        established = ws.receive_json()
        server_id = established["data"]["server_instance_id"]
        ws.send_json({"type": "resume", "data": {"last_seq": 0, "server_instance_id": server_id}})
        resumed = ws.receive_json()
        assert resumed["type"] == "resume_ok"
        assert resumed["data"]["replayed_count"] == 0


def test_training_resume_rejects_restarted_server(training_client) -> None:
    client, _manager, _ds = training_client
    with client.websocket_connect("/ws/training") as ws:
        ws.receive_json()  # connection_established
        ws.send_json({"type": "resume", "data": {"last_seq": 5, "server_instance_id": "stale-uuid"}})
        failed = ws.receive_json()
        assert failed["type"] == "resume_failed"
        assert failed["data"]["reason"] == "server_restarted"


# ======================================================================================
# /ws/control channel (TestClient.websocket_connect)
# ======================================================================================


def _control_app(rate_limit: int = 10):
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    executor = LifecycleCommandExecutor(manager, start=lambda params: manager.start_training(ds.X, ds.y))
    app = create_app(routers=[*build_routers(), build_websocket_router()])
    app.state.settings = _fast_ws_settings(ws_control_rate_limit_per_sec=rate_limit)
    attach_websocket(app, manager=manager, ws_manager=WebSocketManager(), command_executor=executor)
    return app, manager


@pytest.fixture
def control_client():
    app, manager = _control_app()
    with TestClient(app) as client:
        yield client, manager
    manager.shutdown()


def test_control_connection_established(control_client) -> None:
    client, _manager = control_client
    with client.websocket_connect("/ws/control") as ws:
        established = ws.receive_json()
        assert established["type"] == "connection_established"
        assert established["data"]["channel"] == "control"


def test_control_start_and_reset_acks(control_client) -> None:
    client, manager = control_client
    with client.websocket_connect("/ws/control") as ws:
        ws.receive_json()  # connection_established
        ws.send_json({"command": "start", "command_id": "c1"})
        ack = ws.receive_json()
        assert ack["type"] == "command_response"
        assert ack["data"]["status"] == "success"
        assert ack["data"]["command_id"] == "c1"
        assert manager.join(timeout=5.0)  # let the started run settle

        ws.send_json({"command": "reset"})
        assert ws.receive_json()["data"]["status"] == "success"


def test_control_set_params_ack(control_client) -> None:
    client, _manager = control_client
    with client.websocket_connect("/ws/control") as ws:
        ws.receive_json()
        ws.send_json({"command": "set_params", "params": {"max_epochs": 5}})
        ack = ws.receive_json()
        assert ack["data"]["status"] == "success"
        assert ack["data"]["result"]["max_epochs"] == 5


def test_control_invalid_state_surfaces_error(control_client) -> None:
    client, _manager = control_client
    with client.websocket_connect("/ws/control") as ws:
        ws.receive_json()
        # pause is invalid from STOPPED -> the manager raises RuntimeError, surfaced as an error ack.
        ws.send_json({"command": "pause"})
        ack = ws.receive_json()
        assert ack["data"]["status"] == "error"
        assert "running" in ack["data"]["error"].lower()


def test_control_unknown_command(control_client) -> None:
    client, _manager = control_client
    with client.websocket_connect("/ws/control") as ws:
        ws.receive_json()
        ws.send_json({"command": "frobnicate"})
        ack = ws.receive_json()
        assert ack["data"]["status"] == "error"
        assert ack["data"]["code"] == "unknown_command"


def test_control_rate_limit() -> None:
    app, manager = _control_app(rate_limit=1)  # 1 token, ~1/s refill
    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws/control") as ws:
                ws.receive_json()  # connection_established
                ws.send_json({"command": "set_params", "params": {"a": 1}})
                first = ws.receive_json()
                ws.send_json({"command": "set_params", "params": {"b": 2}})
                second = ws.receive_json()
                statuses = {first["data"]["status"], second["data"]["status"]}
                assert "rate_limited" in statuses
    finally:
        manager.shutdown()
