"""Both-stacks-green tests for the WS-2 / OUT-11 T2 step-1b snapshot seam.

Exercises the generic snapshot persistence -- the ``SnapshotStore``, the serializer-injected
``ServiceLifecycleManager`` methods (save/list/get/load/restore/retrain/resume), and the
``/v1/snapshots`` routes -- driven entirely by model-core's reference **regression** model +
``ReferenceLinearSerializer`` (no cascor, no HDF5). The model serializer is the injected seam,
so the same generic code path serves cascor's HDF5 serializer in WS-6.
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceLinearModel, ReferenceLinearSerializer

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager, SnapshotNotFoundError, SnapshotStore
from juniper_service_core.routes import build_routers


# --------------------------------------------------------------------------------------
# SnapshotStore (unit) -- the on-disk bundle + injected serializer
# --------------------------------------------------------------------------------------


def test_snapshot_store_roundtrip(tmp_path) -> None:
    ds = tiny_regression_2d()
    model = ReferenceLinearModel()
    model.fit(ds.X, ds.y)  # the serializer requires a fitted model

    store = SnapshotStore(ReferenceLinearSerializer(), tmp_path)
    meta = store.save(model, "snap_1", {"description": "first", "history": [{"epoch": 0, "metrics": {"mse": 0.1}}]})
    assert meta["id"] == "snap_1"
    assert store.exists("snap_1")
    assert [entry["id"] for entry in store.list()] == ["snap_1"]
    assert store.get("snap_1")["description"] == "first"

    loaded_model, sidecar = store.load("snap_1")
    assert sidecar["history"][0]["epoch"] == 0
    # The model-core serializer contract: save -> load is a lossless prediction round-trip.
    np.testing.assert_allclose(loaded_model.predict(ds.X), model.predict(ds.X))


def test_snapshot_store_missing(tmp_path) -> None:
    store = SnapshotStore(ReferenceLinearSerializer(), tmp_path)
    with pytest.raises(SnapshotNotFoundError):
        store.load("does-not-exist")
    assert store.get("does-not-exist") is None
    assert store.list() == []


# --------------------------------------------------------------------------------------
# ServiceLifecycleManager snapshot methods
# --------------------------------------------------------------------------------------


@pytest.fixture
def trained_manager(tmp_path):
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    manager.start_training(ds.X, ds.y, ds.X_val, ds.y_val)
    assert manager.join(timeout=5.0)
    return manager, ds


def test_manager_snapshots_enabled_only_with_serializer(tmp_path) -> None:
    assert ServiceLifecycleManager(ReferenceLinearModel()).snapshots_enabled() is False
    enabled = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    assert enabled.snapshots_enabled() is True


def test_manager_save_list_get(trained_manager) -> None:
    manager, _ = trained_manager
    meta = manager.save_snapshot("after training")
    snapshot_id = meta["id"]
    assert meta["description"] == "after training"
    assert any(entry["id"] == snapshot_id for entry in manager.list_snapshots())
    assert manager.get_snapshot(snapshot_id)["id"] == snapshot_id
    assert manager.get_snapshot("missing") is None


def test_manager_restore_is_investigating_and_keeps_history(trained_manager) -> None:
    manager, _ = trained_manager
    snapshot_id = manager.save_snapshot()["id"]
    status = manager.load_snapshot(snapshot_id)
    assert status["state_machine"]["status"] == "INVESTIGATING"
    assert len(manager.get_metrics_history()) >= 1


def test_manager_retrain_clears_history_to_stopped(trained_manager) -> None:
    manager, _ = trained_manager
    snapshot_id = manager.save_snapshot()["id"]
    status = manager.restore_for_retrain(snapshot_id)
    assert status["state_machine"]["status"] == "STOPPED"
    assert manager.get_metrics_history() == []


def test_manager_resume_keeps_history_and_start_resumes(trained_manager) -> None:
    manager, ds = trained_manager
    snapshot_id = manager.save_snapshot()["id"]
    result = manager.resume_from_snapshot(snapshot_id)
    assert result["state_machine"]["status"] == "RESUME_READY"
    assert result["resume_point_epoch"] >= 1
    assert len(manager.get_metrics_history()) >= 1
    # The new FSM edge: START is legal from RESUME_READY and runs to completion.
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)
    assert manager.get_status()["state_machine"]["status"] == "COMPLETED"


def test_manager_save_without_serializer_raises() -> None:
    manager = ServiceLifecycleManager(ReferenceLinearModel())
    with pytest.raises(RuntimeError):
        manager.save_snapshot()


def test_manager_missing_snapshot_raises(trained_manager) -> None:
    manager, _ = trained_manager
    with pytest.raises(SnapshotNotFoundError):
        manager.load_snapshot("does-not-exist")


# --------------------------------------------------------------------------------------
# /v1/snapshots routes
# --------------------------------------------------------------------------------------


@pytest.fixture
def snapshot_client(tmp_path):
    ds = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    app = create_app(title="test-model-service", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, ds
    manager.shutdown()


def _data(response) -> dict:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    return body["data"]


def test_routes_full_snapshot_flow(snapshot_client) -> None:
    client, manager, ds = snapshot_client
    manager.start_training(ds.X, ds.y)
    assert manager.join(timeout=5.0)

    saved = _data(client.post("/v1/snapshots", json={"description": "v1"}))
    snapshot_id = saved["id"]
    assert any(entry["id"] == snapshot_id for entry in _data(client.get("/v1/snapshots")))
    assert _data(client.get(f"/v1/snapshots/{snapshot_id}"))["description"] == "v1"

    restored = _data(client.post(f"/v1/snapshots/{snapshot_id}/restore"))
    assert restored["operation"] == "restore"
    assert restored["state_machine"]["status"] == "INVESTIGATING"

    resumed = _data(client.post(f"/v1/snapshots/{snapshot_id}/resume"))
    assert resumed["operation"] == "resume"
    assert resumed["state_machine"]["status"] == "RESUME_READY"
    assert resumed["resume_point_epoch"] >= 1

    retrained = _data(client.post(f"/v1/snapshots/{snapshot_id}/retrain"))
    assert retrained["operation"] == "retrain"
    assert retrained["state_machine"]["status"] == "STOPPED"


def test_routes_404_for_missing_snapshot(snapshot_client) -> None:
    client, _manager, _ds = snapshot_client
    assert client.get("/v1/snapshots/nope").status_code == 404
    assert client.post("/v1/snapshots/nope/restore").status_code == 404
    assert client.post("/v1/snapshots/nope/resume").status_code == 404


def test_routes_501_when_snapshots_not_configured() -> None:
    manager = ServiceLifecycleManager(ReferenceLinearModel())  # no serializer -> disabled
    app = create_app(routers=build_routers())
    app.state.lifecycle = manager
    client = TestClient(app)
    assert client.post("/v1/snapshots").status_code == 501
    assert client.get("/v1/snapshots").status_code == 501
    assert client.post("/v1/snapshots/any/restore").status_code == 501
