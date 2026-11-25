"""Pin that a replay session lasts only as long as the ``REPLAYING`` state it belongs to, and that a replay stop touches only a replay.

``start_replay`` opens a ``ReplaySession``, and only ``reset``, ``shutdown``, another ``start_replay``
and the replay's own stop (``replay_control("stop")``, ``stop_replay()``) ended it. ``load_snapshot``, ``resume_from_snapshot`` and
``restore_for_retrain`` move the machine out of ``REPLAYING`` and left the session open, so it
outlived its state. After a ``retrain`` or a ``resume`` a run can start, and the leftover session's
``stop`` (``replay_control("stop")``, ``POST /v1/snapshots/{id}/replay/control``) then reset the
machine to ``STOPPED`` without setting the stop while that run's ``fit`` was still running, so the
next start was accepted beside it: two ``fit`` calls on one model. Its ``seek`` and ``play`` pushed
replay frames into the live frame sink during the run. ``stop_replay()`` set ``monitor.status``
``stopped`` whatever the machine read, so it relabelled a running run, an inspection or a finished
run. Ruling 23 in section 8 of ``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``
("Lifecycle races beside N-2") gives this its fix.

Every load now ends the session it finds once the snapshot has loaded (a load that fails before that,
such as an unknown id, leaves it alone), so a session exists only while the machine reads ``REPLAYING``,
where no run can start.
``stop_replay()`` resets the machine and relabels the monitor only from ``REPLAYING``.

Eleven of the fourteen tests here fail on a ``manager.py`` that leaves the session open or relabels
outside ``REPLAYING``; the last three are controls and pass either way. Every wait is on a
``threading.Event`` with a deadline; nothing sleeps.
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainableModel, TrainResult
from juniper_model_core.serialization import ModelSerializer

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.lifecycle.snapshots import SnapshotNotFoundError
from juniper_service_core.routes import build_routers

NO_SESSION = "No replay session is active"

_PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}

# The first run completes, so a snapshot saved after it has one history row to replay.
_SNAPSHOT_RUN = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
# The run started after the load parks once it has started; a second fit call parks at its own gate.
_RUN = (("emit", "training_start"), ("gate", "run"), ("emit", "epoch_end"), ("emit", "training_end"))
_BESIDE = (("emit", "training_start"), ("gate", "beside"), ("emit", "epoch_end"))


class _GatedModel(TrainableModel):
    """A regression model whose ``fit`` call *n* follows ``scripts[n - 1]``; later calls just return.

    A step is ``("emit", event_type)``, sent through the sink, or ``("gate", name)``, which signals
    :meth:`reached` and parks until the test calls :meth:`open`. It records the thread of each call
    and the most ``fit`` calls ever running at once (``peak``). Every park is bounded.
    """

    def __init__(self, *scripts: tuple[tuple[str, str], ...]) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.fits = 0
        self.peak = 0
        self.threads: list[threading.Thread] = []
        self._running = 0
        self._scripts = scripts
        self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def _gate(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self._gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str, timeout: float = 5.0) -> bool:
        return self._gate(name)[1].wait(timeout)

    def open(self, name: str) -> None:
        self._gate(name)[0].set()

    def open_all(self) -> None:
        with self._lock:
            gates = [gate for gate, _ in self._gates.values()]
        for gate in gates:
            gate.set()

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with self._lock:
            self.fits += 1
            call = self.fits
            self.threads.append(threading.current_thread())
            self._running += 1
            self.peak = max(self.peak, self._running)
        script = self._scripts[call - 1] if call <= len(self._scripts) else ()
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(_PAYLOADS[arg]), 0))
                elif kind == "gate":
                    gate, reached = self._gate(arg)
                    reached.set()
                    gate.wait(timeout=10.0)
        finally:
            with self._lock:
                self._running -= 1
        return TrainResult(final_metrics={"mse": 0.25}, n_epochs=1)

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], 1))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.25}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "gated", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return (2,)

    @property
    def output_shape(self) -> tuple[int, ...]:
        return (1,)


class _QueueSerializer(ModelSerializer):
    """Writes no model file; each ``load`` hands back the next queued model, then fresh ones whose ``fit`` just returns."""

    def __init__(self, *models: _GatedModel) -> None:
        self._queue = list(models)

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        return self._queue.pop(0) if self._queue else _GatedModel()


def _zeros(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


@pytest.fixture
def replayed(tmp_path):
    """Build a manager that completed a run, saved a snapshot of it and is replaying that snapshot.

    The replay's load attaches a fresh model; the load after it attaches ``run_model``, whose first
    ``fit`` parks at ``run`` and whose second parks at ``beside``. Returns
    ``(manager, snapshot_id, run_model)``; everything is torn down afterwards.
    """
    built: list[tuple[ServiceLifecycleManager, list[_GatedModel]]] = []

    def build() -> tuple[ServiceLifecycleManager, str, _GatedModel]:
        first = _GatedModel(_SNAPSHOT_RUN)
        run_model = _GatedModel(_RUN, _BESIDE)
        mgr = ServiceLifecycleManager(first, serializer=_QueueSerializer(_GatedModel(), run_model), snapshot_dir=tmp_path)
        built.append((mgr, [first, run_model]))
        mgr.start_training(*_zeros())
        assert mgr.join(timeout=5.0)
        snapshot_id = mgr.save_snapshot()["id"]
        assert mgr.start_replay(snapshot_id)["state_machine"]["status"] == "REPLAYING"
        assert mgr.get_replay_state() is not None
        return mgr, snapshot_id, run_model

    yield build
    for mgr, models in built:
        for model in models:
            model.open_all()
        mgr.set_frame_sink(None)
        mgr.shutdown()
        for model in models:
            for thread in model.threads:
                thread.join(timeout=5.0)


@pytest.mark.parametrize(("load", "loaded_status"), [("load_snapshot", "INVESTIGATING"), ("resume_from_snapshot", "RESUME_READY"), ("restore_for_retrain", "STOPPED")])
def test_a_load_ends_the_replay_session_it_leaves(replayed, load: str, loaded_status: str) -> None:
    """The session ends with the ``REPLAYING`` state: its daemon stops, and no replay control finds it."""
    mgr, snapshot_id, _run_model = replayed()
    session = mgr._replay_session

    assert getattr(mgr, load)(snapshot_id)["state_machine"]["status"] == loaded_status
    # Before the fix the session survived the load, still playable and still able to stop and RESET the machine.
    assert mgr.get_replay_state() is None
    assert session.state()["stopped"] is True
    assert session.join(timeout=5.0)
    with pytest.raises(RuntimeError, match=NO_SESSION):
        mgr.replay_control("status")
    assert mgr.get_status()["state_machine"]["status"] == loaded_status


@pytest.mark.parametrize("load", ["restore_for_retrain", "resume_from_snapshot"])
def test_a_replay_stop_after_a_load_cannot_reset_a_run_started_after_it(replayed, load: str) -> None:
    """The race itself: replay, load, start, the replay's ``stop``, start again."""
    mgr, snapshot_id, run_model = replayed()
    getattr(mgr, load)(snapshot_id)
    assert mgr.start_training(*_zeros())["state_machine"]["status"] == "STARTED"
    assert run_model.reached("run")

    # Before the fix this stop was accepted: the machine read STOPPED while the run's fit kept running.
    with pytest.raises(RuntimeError, match=NO_SESSION):
        mgr.replay_control("stop")
    status = mgr.get_status()
    assert status["state_machine"]["status"] == "STARTED"
    assert status["training_active"] is True
    assert status["monitor"]["status"] == "running"
    # ...and the next start was then accepted beside that fit.
    with pytest.raises(RuntimeError, match="Training already in progress"):
        mgr.start_training(*_zeros())

    run_model.open("run")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert run_model.fits == 1
    assert run_model.peak == 1, "two fit calls ran on the model at once"


def test_a_session_left_by_a_load_pushes_no_replay_frame_into_a_run(replayed) -> None:
    """A session that outlived its state could ``seek`` (or ``play``) during a run and push replay frames to the live sink."""
    mgr, snapshot_id, run_model = replayed()
    mgr.restore_for_retrain(snapshot_id)
    mgr.start_training(*_zeros())
    assert run_model.reached("run")
    frames: list[dict[str, Any]] = []
    mgr.set_frame_sink(frames.append)

    with pytest.raises(RuntimeError, match=NO_SESSION):
        mgr.replay_control("seek", time_index=0)
    assert [frame for frame in frames if (frame.get("data") or {}).get("replay") is True] == []
    run_model.open("run")
    assert mgr.join(timeout=5.0)


@pytest.fixture
def replay_stack(tmp_path):
    """A live app + manager wired as a real service wires them, with snapshots on."""
    first = _GatedModel(_SNAPSHOT_RUN)
    run_model = _GatedModel(_RUN, _BESIDE)
    manager = ServiceLifecycleManager(first, serializer=_QueueSerializer(_GatedModel(), run_model), snapshot_dir=tmp_path)
    app = create_app(title="test-model-service", version="9.9.9", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, run_model
    first.open_all()
    run_model.open_all()
    manager.shutdown()
    for thread in first.threads + run_model.threads:
        thread.join(timeout=5.0)


def test_a_replay_stop_over_http_after_a_retrain_is_a_409_and_the_run_keeps_running(replay_stack) -> None:
    """The race's HTTP sequence: replay, retrain, start, replay stop, start."""
    client, manager, run_model = replay_stack
    X, y = _zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}
    assert client.post("/v1/training/start", json=payload).status_code == 200
    assert manager.join(timeout=5.0)
    snapshot_id = client.post("/v1/snapshots", json={}).json()["data"]["id"]
    assert client.post(f"/v1/snapshots/{snapshot_id}/replay").status_code == 200
    assert client.post(f"/v1/snapshots/{snapshot_id}/retrain").status_code == 200
    assert client.post("/v1/training/start", json=payload).status_code == 200
    assert run_model.reached("run")

    stop = client.post(f"/v1/snapshots/{snapshot_id}/replay/control", json={"action": "stop"})
    # Before the fix this was a 200 whose state_machine read STOPPED while the run's fit kept running.
    assert stop.status_code == 409, stop.text
    assert stop.json()["detail"] == NO_SESSION
    status = client.get("/v1/training/status").json()["data"]
    assert (status["state_machine"]["status"], status["training_active"]) == ("STARTED", True)
    second = client.post("/v1/training/start", json=payload)
    # ...and this second start was a 200, running a second fit beside the first.
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Training cannot be started: Training already in progress"

    run_model.open("run")
    assert manager.join(timeout=5.0)
    assert client.get("/v1/training/status").json()["data"]["state_machine"]["status"] == "COMPLETED"
    assert run_model.peak == 1


def test_stop_replay_leaves_a_running_run_alone(tmp_path) -> None:
    """``stop_replay()`` with no replay at all, while a run trains, used to set ``monitor.status`` ``stopped``."""
    model = _GatedModel(_RUN)
    mgr = ServiceLifecycleManager(model)
    try:
        mgr.start_training(*_zeros())
        assert model.reached("run")
        status = mgr.stop_replay()
        assert status["state_machine"]["status"] == "STARTED"
        assert status["monitor"]["status"] == "running"
        assert status["monitor"]["phase"] == "running"
        model.open("run")
        assert mgr.join(timeout=5.0)
        assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
        assert mgr.get_status()["monitor"]["status"] == "completed"
    finally:
        model.open_all()
        mgr.shutdown()
        for thread in model.threads:
            thread.join(timeout=5.0)


@pytest.mark.parametrize(("load", "status", "monitor"), [("load_snapshot", "INVESTIGATING", "investigating"), ("resume_from_snapshot", "RESUME_READY", "resume_ready"), (None, "COMPLETED", "completed")])
def test_stop_replay_outside_a_replay_leaves_the_machine_and_the_monitor_alone(tmp_path, load: str | None, status: str, monitor: str) -> None:
    """Outside ``REPLAYING`` there is no replay to stop, so nothing is relabelled (it used to read ``stopped``)."""
    model = _GatedModel(_SNAPSHOT_RUN)
    mgr = ServiceLifecycleManager(model, serializer=_QueueSerializer(), snapshot_dir=tmp_path)
    try:
        mgr.start_training(*_zeros())
        assert mgr.join(timeout=5.0)
        snapshot_id = mgr.save_snapshot()["id"]
        if load is not None:
            getattr(mgr, load)(snapshot_id)
        before = mgr.get_status()
        assert (before["state_machine"]["status"], before["monitor"]["status"]) == (status, monitor)
        after = mgr.stop_replay()
        assert (after["state_machine"]["status"], after["monitor"]["status"], after["monitor"]["phase"]) == (status, monitor, "idle")
    finally:
        mgr.shutdown()


def test_a_load_that_fails_leaves_the_replay_session_alone(replayed) -> None:
    """Control: a load of a snapshot that does not exist changes nothing, so the replay goes on."""
    mgr, _snapshot_id, _run_model = replayed()
    with pytest.raises(SnapshotNotFoundError):
        mgr.load_snapshot("does-not-exist")
    assert mgr.get_status()["state_machine"]["status"] == "REPLAYING"
    assert mgr.get_replay_state() is not None
    assert mgr.replay_control("stop")["state_machine"]["status"] == "STOPPED"


def test_attach_model_during_a_replay_keeps_the_session(replayed) -> None:
    """Control: ``attach_model`` does not move the machine out of ``REPLAYING``, so the session still belongs to it."""
    mgr, _snapshot_id, run_model = replayed()
    mgr.attach_model(run_model)
    assert mgr.get_status()["state_machine"]["status"] == "REPLAYING"
    assert mgr.get_replay_state() is not None
    with pytest.raises(RuntimeError, match="Cannot start training in the current state"):
        mgr.start_training(*_zeros())
    assert mgr.replay_control("stop")["state_machine"]["status"] == "STOPPED"
    assert mgr.get_replay_state() is None


def test_stop_replay_from_a_replay_still_resets_and_relabels(replayed) -> None:
    """Control: from ``REPLAYING``, ``stop_replay()`` ends the session, resets to ``STOPPED`` and reads ``stopped``."""
    mgr, _snapshot_id, _run_model = replayed()
    status = mgr.stop_replay()
    assert (status["state_machine"]["status"], status["monitor"]["status"], status["monitor"]["phase"]) == ("STOPPED", "stopped", "idle")
    assert mgr.get_replay_state() is None
