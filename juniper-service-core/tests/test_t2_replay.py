"""Tests for the WS-2 / OUT-11 T2 step-1c snapshot replay.

Deterministic coverage of the generic replay engine: the synchronous control surface
(seek/speed/range/pause/play/stop) and ``step()`` are exercised directly (no timing
dependence), and the background daemon is verified by playing to the end behind an event
signal with a generous timeout. Manager + route tests confirm the ``REPLAYING`` FSM state and
the start-rejected-while-replaying guard.
"""

from __future__ import annotations

import threading

import pytest
from fastapi.testclient import TestClient
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceLinearModel, ReferenceLinearSerializer

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ReplaySession, ServiceLifecycleManager
from juniper_service_core.routes import build_routers


def _history(n: int) -> list[dict]:
    return [{"epoch": i, "metrics": {"mse": 1.0 / (i + 1)}, "seq": i} for i in range(n)]


# --------------------------------------------------------------------------------------
# ReplaySession (unit) -- synchronous control surface + step()
# --------------------------------------------------------------------------------------


def test_replay_starts_paused_at_zero() -> None:
    session = ReplaySession("s", _history(5))
    state = session.start()
    try:
        assert state["paused"] is True
        assert state["time_index"] == 0
        assert state["length"] == 5
        assert state["frame"]["epoch"] == 0
    finally:
        session.stop()
        assert session.join(timeout=2.0)


def test_replay_controls_are_synchronous() -> None:
    # Exercise the synchronous control surface WITHOUT start(): control() / step() / state()
    # all mutate under the session lock and need no daemon. Starting the daemon here would let
    # its _run loop call step() concurrently with the explicit step() below -- both advance
    # _time_index, so the deterministic index assertion ("== 2") would intermittently see the
    # daemon's extra step ("== 3"). Not starting the daemon makes this test deterministic and
    # is the honest scope for a test named "controls_are_synchronous".
    session = ReplaySession("s", _history(5))
    assert session.control("seek", time_index=3)["time_index"] == 3
    assert session.control("speed", value=2.0)["speed"] == 2.0
    assert session.control("range", start=1, end=4)["range"] == {"start": 1, "end": 4}
    # seek clamps into the active range [1, 4) -> max index 3
    assert session.control("seek", time_index=10)["time_index"] == 3
    # step() advances by sign(speed) once playing
    session.control("seek", time_index=1)
    session.control("play")
    assert session.step() is True
    assert session.state()["time_index"] == 2


def test_replay_step_auto_pauses_at_boundary() -> None:
    session = ReplaySession("s", _history(3))
    session.start()
    try:
        session.control("play")
        session.control("seek", time_index=2)  # last valid index (length 3 -> range [0,3))
        assert session.step() is False  # 2 -> 3 is out of range, auto-pause
        assert session.state()["paused"] is True
    finally:
        session.stop()
        assert session.join(timeout=2.0)


def test_replay_unknown_action_raises() -> None:
    session = ReplaySession("s", _history(2))
    with pytest.raises(ValueError):
        session.control("frobnicate")
    session.stop()


def test_replay_daemon_plays_to_end() -> None:
    seen: list[int] = []
    reached_end = threading.Event()

    def on_frame(frame: dict) -> None:
        seen.append(frame["time_index"])
        if frame["time_index"] >= 4:
            reached_end.set()

    session = ReplaySession("s", _history(5), on_frame=on_frame)
    session.start()  # paused at 0, emits frame 0
    session.control("speed", value=10.0)
    session.control("play")
    try:
        assert reached_end.wait(timeout=3.0), f"replay did not reach the end; saw {seen}"
        # advancing past the last index auto-pauses at the boundary
        assert session.state()["time_index"] == 4
    finally:
        session.stop()
        assert session.join(timeout=2.0)


# --------------------------------------------------------------------------------------
# ServiceLifecycleManager replay
# --------------------------------------------------------------------------------------


@pytest.fixture
def replay_manager(tmp_path):
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)
    snapshot_id = manager.save_snapshot()["id"]
    yield manager, snapshot_id
    manager.shutdown()


def test_manager_start_replay_enters_replaying(replay_manager) -> None:
    manager, snapshot_id = replay_manager
    result = manager.start_replay(snapshot_id)
    assert result["state_machine"]["status"] == "REPLAYING"
    assert result["replay"]["snapshot_id"] == snapshot_id
    assert result["replay"]["paused"] is True
    assert manager.get_replay_state() is not None


def test_manager_replay_control_and_stop(replay_manager) -> None:
    manager, snapshot_id = replay_manager
    manager.start_replay(snapshot_id)
    assert manager.replay_control("seek", time_index=0)["replay"]["time_index"] == 0
    stopped = manager.replay_control("stop")
    assert stopped["state_machine"]["status"] == "STOPPED"
    assert manager.get_replay_state() is None


def test_manager_start_rejected_while_replaying(replay_manager) -> None:
    manager, snapshot_id = replay_manager
    manager.start_replay(snapshot_id)
    ds = tiny_regression_2d()
    with pytest.raises(RuntimeError):
        manager.start_training(ds.X, ds.y)  # START is rejected from REPLAYING


def test_manager_replay_control_without_session_raises(replay_manager) -> None:
    manager, _snapshot_id = replay_manager
    with pytest.raises(RuntimeError):
        manager.replay_control("pause")


# --------------------------------------------------------------------------------------
# /v1/snapshots/{id}/replay routes
# --------------------------------------------------------------------------------------


@pytest.fixture
def replay_client(tmp_path):
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    app = create_app(routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, ds
    manager.shutdown()


def _data(response) -> dict:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    return body["data"]


def test_routes_replay_flow(replay_client) -> None:
    client, manager, ds = replay_client
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)
    snapshot_id = _data(client.post("/v1/snapshots", json={}))["id"]

    started = _data(client.post(f"/v1/snapshots/{snapshot_id}/replay"))
    assert started["state_machine"]["status"] == "REPLAYING"
    assert started["replay"]["paused"] is True

    seeked = _data(client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "seek", "time_index": 0}))
    assert seeked["replay"]["time_index"] == 0

    stopped = _data(client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "stop"}))
    assert stopped["state_machine"]["status"] == "STOPPED"


def test_routes_replay_control_without_session_is_409(replay_client) -> None:
    client, manager, ds = replay_client
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)
    snapshot_id = _data(client.post("/v1/snapshots", json={}))["id"]
    assert client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "pause"}).status_code == 409


def test_routes_replay_bad_action_is_422(replay_client) -> None:
    client, manager, ds = replay_client
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)
    snapshot_id = _data(client.post("/v1/snapshots", json={}))["id"]
    client.post(f"/v1/snapshots/{snapshot_id}/replay")
    assert client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "nope"}).status_code == 422


def test_routes_replay_501_when_disabled() -> None:
    manager = ServiceLifecycleManager(ReferenceLinearModel())  # no serializer
    app = create_app(routers=build_routers())
    app.state.lifecycle = manager
    client = TestClient(app)
    assert client.post("/v1/snapshots/x/replay").status_code == 501
