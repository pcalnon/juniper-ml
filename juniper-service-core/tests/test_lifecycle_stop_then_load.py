"""Pin how ``ServiceLifecycleManager`` handles a snapshot load or an attach sent right after a stop (the stop-then-load race).

A stop is cooperative: the event sink raises ``TrainingInterrupted`` at the model's next event, and
a ``fit`` that emits no events runs until it returns. ``start_training`` refuses a start while the
stopped run's ``fit`` is still running (the stop-then-start race, ruling 11 in section 8 of
``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``), but a snapshot load
(``load_snapshot``, ``resume_from_snapshot``, ``start_replay``, ``restore_for_retrain``) and
``attach_model`` checked only that the machine was inactive, so they were accepted then. That
``fit``'s thread still owns the run, and when the ``fit`` ended it settled over what was loaded:
``monitor.status`` ``stopped`` over ``investigating``, ``resume_ready`` or ``replaying``, or
``failed`` with an ``error`` when the ``fit`` raised instead of unwinding, and an event that was
already inside the sink when the stop landed was folded into the loaded history. Ruling 23 of the
same record ("Lifecycle races beside N-2") gives this its fix.

The loads and ``attach_model`` are now refused the way the start is (``RuntimeError``, the start
refusal's text; HTTP 409 on the four snapshot routes) while the previous training thread is alive
with its stop pending, before they touch anything. Once that thread has ended, the same call is
accepted and what it loads stands.

Twelve of the thirteen tests here fail on a ``manager.py`` that accepts the load or attach after a
stop, at the call that should be refused; the last is a control and passes either way. Every wait is
on a ``threading.Event`` with a deadline; nothing sleeps.
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
from juniper_service_core.lifecycle import ServiceLifecycleManager, TrainingInterrupted
from juniper_service_core.lifecycle.monitor import LifecycleMonitor
from juniper_service_core.routes import build_routers

REFUSAL = "The stopped run's fit is still running"
REFUSAL_TEXT = "The stopped run's fit is still running (a stop takes effect at its next event)"

_PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}

# Run 1 completes, so the snapshot saved after it holds one history row. Run 2 parks before its next
# event, which (were the stop not set) would land an epoch in whatever monitor is current.
_SNAPSHOT_RUN = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
_STOPPED_RUN = (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("emit", "training_end"))
_RAISING_RUN = (("emit", "training_start"), ("gate", "old"), ("raise", "boom"))

_LOADS = [
    ("load_snapshot", "INVESTIGATING", "investigating"),
    ("resume_from_snapshot", "RESUME_READY", "resume_ready"),
    ("start_replay", "REPLAYING", "replaying"),
    ("restore_for_retrain", "STOPPED", "stopped"),
]


class _GatedModel(TrainableModel):
    """A regression model whose ``fit`` call *n* follows ``scripts[n - 1]``; later calls just return.

    A step is ``("emit", event_type)``, sent through the sink; ``("gate", name)``, which signals
    :meth:`reached` and parks until the test calls :meth:`open`; or ``("raise", message)``, a ``fit``
    that fails instead of unwinding. It records the thread of each call (``threads``) and the calls the
    sink unwound (``interrupted``). Every park is bounded, so a failed assertion cannot leave a thread
    parked forever.
    """

    def __init__(self, *scripts: tuple[tuple[str, str], ...]) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.fits = 0
        self.threads: list[threading.Thread] = []
        self.interrupted: list[int] = []
        self._scripts = scripts
        self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def _gate(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self._gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str, timeout: float = 5.0) -> bool:
        """True once a ``fit`` has parked at gate ``name``, waiting up to ``timeout`` seconds."""
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
        script = self._scripts[call - 1] if call <= len(self._scripts) else ()
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(_PAYLOADS[arg]), 0))
                elif kind == "gate":
                    gate, reached = self._gate(arg)
                    reached.set()
                    gate.wait(timeout=10.0)
                elif kind == "raise":
                    raise RuntimeError(arg)
        except TrainingInterrupted:
            with self._lock:
                self.interrupted.append(call)
            raise
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


class _FreshModelSerializer(ModelSerializer):
    """Writes no model file; every ``load`` hands back a fresh model whose ``fit`` just returns."""

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        return _GatedModel()


class _HoldingMonitor(LifecycleMonitor):
    """Once armed, holds the first ``epoch_end`` inside ``on_event``, before folding it, until released.

    That is an event already inside the sink: it passed the sink's stop checks before the stop landed.
    """

    def __init__(self) -> None:
        super().__init__()
        self.armed = False
        self.inside = threading.Event()
        self.release = threading.Event()

    def on_event(self, event: TrainingEvent) -> None:
        if self.armed and event.type == "epoch_end" and not self.inside.is_set():
            self.inside.set()
            self.release.wait(timeout=10.0)
        super().on_event(event)


class _HoldsAfterSettling(ServiceLifecycleManager):
    """Holds each training thread after it has settled its run, before the thread exits."""

    def __init__(self, model: TrainableModel, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self.settled = threading.Event()
        self.exit = threading.Event()

    def _train_thread_target(self, *args: Any) -> None:
        super()._train_thread_target(*args)
        self.settled.set()
        self.exit.wait(timeout=10.0)


def _zeros(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


@pytest.fixture
def parked(tmp_path):
    """Build a manager that completed run 1, saved a snapshot of it, and has run 2's ``fit`` parked at ``old``.

    Returns ``(model, manager, snapshot_id)``; the test sends the stop (or reset) itself. Every
    manager built is torn down, its gates opened and its threads joined.
    """
    built: list[tuple[_GatedModel, ServiceLifecycleManager]] = []

    def build(second: tuple[tuple[str, str], ...] = _STOPPED_RUN, *, manager_cls: type[ServiceLifecycleManager] = ServiceLifecycleManager) -> tuple[_GatedModel, ServiceLifecycleManager, str]:
        model = _GatedModel(_SNAPSHOT_RUN, second)
        mgr = manager_cls(model, serializer=_FreshModelSerializer(), snapshot_dir=tmp_path)
        built.append((model, mgr))
        mgr.start_training(*_zeros(), dataset_name="first")
        if isinstance(mgr, _HoldsAfterSettling):
            assert mgr.settled.wait(timeout=5.0)
            mgr.exit.set()
        assert mgr.join(timeout=5.0)
        snapshot_id = mgr.save_snapshot()["id"]
        if isinstance(mgr, _HoldsAfterSettling):
            mgr.settled.clear()
            mgr.exit.clear()
        mgr.start_training(*_zeros(), dataset_name="stopped")
        if "old" in {arg for kind, arg in second if kind == "gate"}:
            assert model.reached("old")
        return model, mgr, snapshot_id

    yield build
    for model, mgr in built:
        model.open_all()
        if isinstance(mgr, _HoldsAfterSettling):
            mgr.exit.set()
        if isinstance(mgr.monitor, _HoldingMonitor):
            mgr.monitor.release.set()
        mgr.shutdown()
        for thread in model.threads:
            thread.join(timeout=5.0)


@pytest.mark.parametrize(("load", "loaded_status", "loaded_monitor"), _LOADS)
def test_a_load_while_the_stopped_runs_fit_is_still_running_is_refused(parked, load: str, loaded_status: str, loaded_monitor: str) -> None:
    """The refused load changes nothing; once the stopped ``fit`` has ended, the same load is accepted and stands."""
    model, mgr, snapshot_id = parked()
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    old_thread = model.threads[1]
    before = mgr.get_status()

    # Before the fix the load was accepted here, and the stopped fit's thread later settled over it.
    with pytest.raises(RuntimeError, match=REFUSAL):
        getattr(mgr, load)(snapshot_id)
    assert old_thread.is_alive()
    assert mgr.model is model, "a refused load attached the snapshot's model"
    assert mgr.get_status() == before
    assert mgr.get_replay_state() is None

    model.open("old")  # the stopped fit's next event finds its stop still set, and the sink unwinds it
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == [2]

    loaded = getattr(mgr, load)(snapshot_id)
    assert loaded["state_machine"]["status"] == loaded_status
    status = mgr.get_status()
    assert status["state_machine"]["status"] == loaded_status
    assert status["monitor"]["status"] == loaded_monitor
    assert "error" not in status


def test_attach_model_while_the_stopped_runs_fit_is_still_running_is_refused(parked) -> None:
    """``attach_model`` holds back the same way: the stopped run's model stays attached until its ``fit`` ends."""
    model, mgr, _snapshot_id = parked()
    mgr.stop_training()
    old_thread = model.threads[1]
    other = _GatedModel()

    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.attach_model(other)
    assert mgr.model is model
    assert mgr.get_status()["monitor"]["status"] == "stopped"

    model.open("old")
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == [2]
    mgr.attach_model(other)
    assert mgr.model is other


def test_a_load_after_a_reset_is_refused_the_same_way(parked) -> None:
    """``reset`` sets the stop as ``stop_training`` does, so a load right after it is refused too."""
    model, mgr, snapshot_id = parked()
    assert mgr.reset()["state_machine"]["status"] == "STOPPED"
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.restore_for_retrain(snapshot_id)

    model.open("old")
    model.threads[1].join(timeout=5.0)
    assert not model.threads[1].is_alive()
    assert mgr.restore_for_retrain(snapshot_id)["state_machine"]["status"] == "STOPPED"


def test_a_stopped_fit_that_raises_does_not_mark_a_load_failed(parked) -> None:
    """A ``fit`` that raises instead of unwinding settles ``failed`` with its ``error`` on its own run, not on a load.

    Before the fix the load was accepted while that ``fit`` ran, and its failure then wrote the
    ``error`` and ``monitor.status`` ``failed`` into the loaded ``INVESTIGATING`` state.
    """
    model, mgr, snapshot_id = parked(_RAISING_RUN)
    mgr.stop_training()
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.load_snapshot(snapshot_id)

    model.open("old")  # the fit raises; the machine stays STOPPED and the stopped run carries the error
    model.threads[1].join(timeout=5.0)
    assert not model.threads[1].is_alive()
    failed = mgr.get_status()
    assert (failed["state_machine"]["status"], failed["monitor"]["status"], failed.get("error")) == ("STOPPED", "failed", "boom")

    loaded = mgr.load_snapshot(snapshot_id)
    assert loaded["state_machine"]["status"] == "INVESTIGATING"
    assert loaded["monitor"]["status"] == "investigating"
    assert "error" not in loaded


def test_a_load_while_an_event_is_inside_the_sink_is_refused(tmp_path) -> None:
    """An event that passed the sink's stop checks before the stop landed is not folded into a loaded history.

    Before the fix the resume was accepted, and the held ``epoch_end`` then landed in the restored
    history: two rows where the snapshot holds one and ``resume_point_epoch`` said 1.
    """
    second = (("emit", "training_start"), ("emit", "epoch_end"), ("emit", "training_end"))
    model = _GatedModel(_SNAPSHOT_RUN, second)
    mgr = ServiceLifecycleManager(model, serializer=_FreshModelSerializer(), snapshot_dir=tmp_path)
    monitor = _HoldingMonitor()
    mgr.monitor = monitor
    try:
        mgr.start_training(*_zeros())
        assert mgr.join(timeout=5.0)
        snapshot_id = mgr.save_snapshot()["id"]
        monitor.armed = True
        mgr.start_training(*_zeros())
        assert monitor.inside.wait(timeout=5.0)  # run 2's epoch_end is inside the sink
        mgr.stop_training()

        with pytest.raises(RuntimeError, match=REFUSAL):
            mgr.resume_from_snapshot(snapshot_id)
        monitor.release.set()  # the held epoch_end lands in the stopped run's own history; its next event unwinds
        model.threads[1].join(timeout=5.0)
        assert not model.threads[1].is_alive()
        assert model.interrupted == [2]

        resumed = mgr.resume_from_snapshot(snapshot_id)
        assert resumed["resume_point_epoch"] == 1
        assert len(mgr.get_metrics_history()) == 1
    finally:
        monitor.release.set()
        mgr.shutdown()
        for thread in model.threads:
            thread.join(timeout=5.0)


@pytest.fixture
def stack(tmp_path):
    """A live app + manager wired as a real service wires them, driving a gated model with snapshots on."""
    model = _GatedModel(_SNAPSHOT_RUN, _STOPPED_RUN)
    manager = ServiceLifecycleManager(model, serializer=_FreshModelSerializer(), snapshot_dir=tmp_path)
    app = create_app(title="test-model-service", version="9.9.9", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, model
    model.open_all()
    manager.shutdown()
    for thread in model.threads:
        thread.join(timeout=5.0)


@pytest.mark.parametrize(("route", "loaded_status"), [("restore", "INVESTIGATING"), ("resume", "RESUME_READY"), ("replay", "REPLAYING"), ("retrain", "STOPPED")])
def test_a_load_over_http_after_a_stop_is_a_409_until_the_stopped_fit_has_ended(stack, route: str, loaded_status: str) -> None:
    """The race's own HTTP sequence: start, stop, load at once."""
    client, manager, model = stack
    X, y = _zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}
    assert client.post("/v1/training/start", json=payload).status_code == 200
    assert manager.join(timeout=5.0)
    snapshot_id = client.post("/v1/snapshots", json={}).json()["data"]["id"]
    assert client.post("/v1/training/start", json=payload).status_code == 200
    assert model.reached("old")
    assert client.post("/v1/training/stop").status_code == 200

    refused = client.post(f"/v1/snapshots/{snapshot_id}/{route}")
    # Before the fix this was a 200, and the stopped fit's thread later settled over the loaded state.
    assert refused.status_code == 409, refused.text
    assert refused.json()["detail"] == REFUSAL_TEXT
    # The refusal comes before the snapshot lookup, so in this window an unknown id is the same 409, not a 404.
    unknown = client.post(f"/v1/snapshots/no-such-snapshot/{route}")
    assert (unknown.status_code, unknown.json()["detail"]) == (409, REFUSAL_TEXT)
    assert client.get("/v1/training/status").json()["data"]["state_machine"]["status"] == "STOPPED"

    model.open("old")
    assert manager.join(timeout=5.0)
    assert client.post(f"/v1/snapshots/no-such-snapshot/{route}").status_code == 404
    accepted = client.post(f"/v1/snapshots/{snapshot_id}/{route}")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["data"]["state_machine"]["status"] == loaded_status
    assert client.get("/v1/training/status").json()["data"]["state_machine"]["status"] == loaded_status


def test_a_load_right_after_a_run_that_settled_itself_is_accepted_while_its_thread_exits(parked) -> None:
    """Control: only a pending stop holds a load back, so a completed run's exiting thread does not."""
    model, mgr, snapshot_id = parked((("emit", "training_start"),), manager_cls=_HoldsAfterSettling)
    assert mgr.settled.wait(timeout=5.0)
    second_thread = model.threads[1]
    assert second_thread.is_alive()  # it has settled its run but has not exited
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"

    assert mgr.load_snapshot(snapshot_id)["state_machine"]["status"] == "INVESTIGATING"
    mgr.exit.set()
    second_thread.join(timeout=5.0)
    assert not second_thread.is_alive()
    assert mgr.get_status()["monitor"]["status"] == "investigating"
