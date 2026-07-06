"""Coverage-lift tests for the generic route error / edge branches (work-unit C-4b).

Targets the error and coercion branches the both-stacks-green contract suites
(``test_t2_routes_contract.py`` / ``test_t2_snapshots.py``) do not drive:

* ``routes/responses.py`` -- numpy-scalar coercion (the success ``.item()`` path, the
  defensive passthrough when ``.item()`` raises) and the ``error_response`` envelope
  builder.
* ``routes/snapshots.py`` -- the 409 rejection branches (save with no model attached; a
  load/replay refused because training is active) and the replay 404 branch.
* ``routes/training.py`` -- the param + ``epochs`` merge and the 409 "cannot be started"
  branch.

Every test is deterministic: real :class:`ServiceLifecycleManager` instances driven through a
FastAPI ``TestClient`` (mirroring the existing suite's fixtures), plus a tiny
snapshots-enabled fake for the "training active" rejection paths a real manager can only
reach through a background-thread race. No sleeps, no async fixtures.
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import (
    ReferenceGrowableModel,
    ReferenceLinearModel,
    ReferenceLinearSerializer,
)

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.routes import build_routers
from juniper_service_core.routes.responses import (
    coerce_native_scalars,
    error_response,
    success_response,
)

# ==========================================================================================
# routes/responses.py -- scalar coercion + envelope builders
# ==========================================================================================


def test_coerce_native_scalars_collapses_numpy_in_containers() -> None:
    """numpy scalars nested in dicts / lists / tuples become JSON-clean Python natives."""
    coerced = coerce_native_scalars({"i": np.int64(7), "row": [np.float64(1.5), 2], "tup": (np.int32(3),)})
    assert coerced == {"i": 7, "row": [1.5, 2], "tup": (3,)}
    assert isinstance(coerced["i"], int) and not isinstance(coerced["i"], np.integer)
    assert isinstance(coerced["row"][0], float) and not isinstance(coerced["row"][0], np.floating)
    assert isinstance(coerced["tup"], tuple)


def test_success_response_coerces_numpy_scalar_payload() -> None:
    """``success_response`` runs the payload through the coercer before the envelope serializes."""
    envelope = success_response({"score": np.float64(0.25)})
    assert envelope["status"] == "success"
    assert envelope["data"]["score"] == 0.25
    assert not isinstance(envelope["data"]["score"], np.floating)
    assert "version" in envelope["meta"]


class _RaisingItem:
    """A non-numpy object whose ``.item()`` raises -- exercises the defensive passthrough."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def item(self) -> object:
        raise self._exc


@pytest.mark.parametrize("exc", [ValueError("not a scalar"), TypeError("item takes args")])
def test_coerce_native_scalars_passthrough_when_item_raises(exc: Exception) -> None:
    """An object exposing a raising ``.item()`` falls through untouched (returned as-is)."""
    sentinel = _RaisingItem(exc)
    assert coerce_native_scalars(sentinel) is sentinel


def test_error_response_builds_error_envelope() -> None:
    """``error_response`` yields the shared error envelope with a fully populated detail block."""
    err = error_response("BAD_INPUT", "it broke", "at row 3")
    assert err["status"] == "error"
    assert err["error"] == {"code": "BAD_INPUT", "message": "it broke", "detail": "at row 3"}
    assert "version" in err["meta"]


def test_error_response_detail_defaults_to_none() -> None:
    """The optional ``detail`` argument defaults to ``None`` in the built envelope."""
    err = error_response("NOPE", "missing")
    assert err["error"]["code"] == "NOPE"
    assert err["error"]["detail"] is None


# ==========================================================================================
# routes/training.py -- param / epoch merge + start rejection
# ==========================================================================================


@pytest.fixture
def growable_client():
    """A live app + growable-model manager, wired exactly as a real service would wire them."""
    dataset = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    app = create_app(title="c4b-training", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, dataset
    manager.shutdown()


def test_start_training_merges_params_and_epochs(growable_client) -> None:
    """``params`` merge + ``epochs`` -> ``params['max_epochs']`` before the run starts (200)."""
    client, manager, ds = growable_client
    payload = {
        "inline_data": {"train_x": ds.X.tolist(), "train_y": ds.y.tolist()},
        "params": {"learning_rate": 0.5},
        "epochs": 3,
    }
    response = client.post("/v1/training/start", json=payload)
    assert response.status_code == 200, response.text
    assert manager.join(timeout=5.0)
    params = client.get("/v1/training/params").json()["data"]
    assert params["learning_rate"] == 0.5
    assert params["max_epochs"] == 3


def test_start_training_409_when_no_model() -> None:
    """Starting with inline data but no model attached surfaces the reason as 409 (not 500)."""
    manager = ServiceLifecycleManager()  # no model attached
    app = create_app(routers=build_routers())
    app.state.lifecycle = manager
    client = TestClient(app)
    payload = {"inline_data": {"train_x": [[0.0, 0.0]], "train_y": [[0.0]]}}
    response = client.post("/v1/training/start", json=payload)
    assert response.status_code == 409, response.text
    assert "cannot be started" in response.json()["detail"].lower()


# ==========================================================================================
# routes/snapshots.py -- 409 save/load rejections + replay 404/409
# ==========================================================================================


@pytest.fixture
def serializer_client(tmp_path):
    """A live app + serializer-injected manager (snapshots enabled) over a temp bundle dir."""
    dataset = tiny_regression_2d()
    manager = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    app = create_app(title="c4b-snapshots", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, dataset
    manager.shutdown()


def test_save_snapshot_409_when_no_model(tmp_path) -> None:
    """Snapshots enabled (serializer injected) but no model -> save raises -> 409 (not 501/500)."""
    manager = ServiceLifecycleManager(None, serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    app = create_app(routers=build_routers())
    app.state.lifecycle = manager
    client = TestClient(app)
    response = client.post("/v1/snapshots", json={"description": "no-model"})
    assert response.status_code == 409, response.text
    assert "model" in response.json()["detail"].lower()


def test_start_replay_404_for_missing_snapshot(serializer_client) -> None:
    """Replaying a snapshot id that has no bundle is a 404 (SnapshotNotFoundError branch)."""
    client, _manager, _ds = serializer_client
    response = client.post("/v1/snapshots/does-not-exist/replay")
    assert response.status_code == 404, response.text
    assert "not found" in response.json()["detail"].lower()


class _TrainingActiveLifecycle:
    """A snapshots-enabled fake whose load / replay operations reject with ``RuntimeError``.

    Mirrors the manager's "Cannot load a snapshot while training is active" rejection so the
    route-level 409 branches are covered deterministically -- a real manager reaches this
    state only via a live background training thread (a race we must not depend on).
    """

    def snapshots_enabled(self) -> bool:
        return True

    def load_snapshot(self, snapshot_id: str) -> dict:
        raise RuntimeError("Cannot load a snapshot while training is active")

    def restore_for_retrain(self, snapshot_id: str) -> dict:
        raise RuntimeError("Cannot load a snapshot while training is active")

    def resume_from_snapshot(self, snapshot_id: str) -> dict:
        raise RuntimeError("Cannot load a snapshot while training is active")

    def start_replay(self, snapshot_id: str) -> dict:
        raise RuntimeError("Cannot start replay while training is active")


def _fake_lifecycle_client(lifecycle: object) -> TestClient:
    """Mount ``lifecycle`` (a duck-typed fake) onto a real app and return a TestClient."""
    app = create_app(routers=build_routers())
    app.state.lifecycle = lifecycle
    return TestClient(app)


@pytest.mark.parametrize("operation", ["restore", "retrain", "resume"])
def test_load_operation_409_when_training_active(operation: str) -> None:
    """restore / retrain / resume all funnel a RuntimeError from the manager into a 409."""
    client = _fake_lifecycle_client(_TrainingActiveLifecycle())
    response = client.post(f"/v1/snapshots/any/{operation}")
    assert response.status_code == 409, response.text
    assert "active" in response.json()["detail"].lower()


def test_start_replay_409_when_training_active() -> None:
    """A replay refused because training is active surfaces as a 409 (RuntimeError branch)."""
    client = _fake_lifecycle_client(_TrainingActiveLifecycle())
    response = client.post("/v1/snapshots/any/replay")
    assert response.status_code == 409, response.text
    assert "active" in response.json()["detail"].lower()
