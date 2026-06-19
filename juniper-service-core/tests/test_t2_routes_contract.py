"""Both-stacks-green contract test for the WS-2 / OUT-11 T2 generic routes.

The headline RK-6 guard: drive EVERY generic route with model-core's ``ReferenceGrowableModel``
(a *regression* stub) through a real FastAPI app assembled from
``create_app(routers=build_routers())``. Because the driver is a regression model, no
classification assumption (argmax / accuracy) can hide in "generic" code -- and the base is
proven independently of cascor (cascor is untouched by this PR).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceGrowableModel

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.routes import build_routers


@pytest.fixture
def stack():
    """A live app + manager + dataset, wired exactly as a real service would wire them."""
    dataset = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    app = create_app(title="test-model-service", version="9.9.9", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, dataset
    manager.shutdown()


def _data(response) -> dict:
    """Assert the shared envelope shape and return the ``data`` payload."""
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert "data" in body
    assert "meta" in body and "version" in body["meta"]
    return body["data"]


def _start_payload(dataset) -> dict:
    return {
        "inline_data": {
            "train_x": dataset.X.tolist(),
            "train_y": dataset.y.tolist(),
            "val_x": dataset.X_val.tolist(),
            "val_y": dataset.y_val.tolist(),
        }
    }


def test_status_before_training(stack) -> None:
    client, _manager, _ds = stack
    data = _data(client.get("/v1/training/status"))
    assert data["state_machine"]["status"] == "STOPPED"
    assert data["training_active"] is False
    assert data["has_model"] is True


def test_full_training_flow_drives_every_route(stack) -> None:
    client, manager, ds = stack

    # Start -> background run.
    start = _data(client.post("/v1/training/start", json=_start_payload(ds)))
    assert start["state_machine"]["status"] in ("STARTED", "COMPLETED")

    # Wait for the run to finish deterministically, then assert terminal status.
    assert manager.join(timeout=5.0)
    status = _data(client.get("/v1/training/status"))
    assert status["state_machine"]["status"] == "COMPLETED"

    # Metrics: a regression model reports regression metrics, never accuracy (RK-6).
    metrics = _data(client.get("/v1/metrics"))["metrics"]
    assert metrics
    assert "accuracy" not in metrics

    history = _data(client.get("/v1/metrics/history"))
    assert len(history) >= 1

    # Dataset metadata + arrays.
    dataset = _data(client.get("/v1/dataset"))
    assert dataset["has_data"] is True
    assert dataset["n_train"] == ds.X.shape[0]
    assert dataset["input_shape"] == list(ds.X.shape[1:])

    dataset_data = _data(client.get("/v1/dataset/data"))
    assert len(dataset_data["train_x"]) == ds.X.shape[0]

    # Model introspection + topology (delegates to model.describe_topology()).
    network = _data(client.get("/v1/network"))
    assert network["model_type"] == "reference_growable"
    assert network["task_type"] == "regression"

    topology = _data(client.get("/v1/network/topology"))
    assert topology["model_type"] == "reference_growable"
    assert "n_units" in topology["meta"]


def test_params_get_and_patch(stack) -> None:
    client, _manager, _ds = stack
    assert _data(client.get("/v1/training/params")) == {}
    patched = _data(client.patch("/v1/training/params", json={"max_epochs": 7}))
    assert patched["max_epochs"] == 7
    assert _data(client.get("/v1/training/params"))["max_epochs"] == 7


def test_lifecycle_control_state_codes(stack) -> None:
    client, manager, _ds = stack
    # Pause/resume are invalid from STOPPED -> 409.
    assert client.post("/v1/training/pause").status_code == 409
    assert client.post("/v1/training/resume").status_code == 409
    # Stop and reset are idempotent -> 200.
    assert client.post("/v1/training/stop").status_code == 200
    assert client.post("/v1/training/reset").status_code == 200


def test_start_requires_inline_data(stack) -> None:
    client, _manager, _ds = stack
    assert client.post("/v1/training/start", json={}).status_code == 400


def test_503_when_lifecycle_not_wired() -> None:
    app = create_app(routers=build_routers())  # no app.state.lifecycle
    client = TestClient(app)
    assert client.get("/v1/training/status").status_code == 503


def test_topology_404_when_no_model() -> None:
    app = create_app(routers=build_routers())
    app.state.lifecycle = ServiceLifecycleManager()  # no model attached
    client = TestClient(app)
    assert client.get("/v1/network/topology").status_code == 404


def test_generic_health_router_still_present(stack) -> None:
    client, _manager, _ds = stack
    # The app factory's generic health router coexists with the T2 routes.
    assert client.get("/v1/health").json() == {"status": "ok"}
