"""Pin how ``ServiceLifecycleManager`` handles a start sent right after a stop (the stop-then-start race).

A stop is cooperative: the event sink raises ``TrainingInterrupted`` at the model's next event, and
a ``fit`` that emits no events runs until it returns. ``start_training`` used to clear the stop
event, so a start sent before the stopped run's ``fit`` reached its next event cancelled the stop:
that ``fit`` never saw it, kept running beside the new run on the same model, and sent its events
through the shared sink into the new run's monitor (a ``phase_change`` set the new run's phase, an
``epoch_end`` landed in its history, a ``training_end`` set ``monitor.status`` ``ended``). The pause
gate is shared too: when that ``fit`` reached its next event while the new run was paused, it
waited at the new run's gate, and the new run's paused completion released it with no command,
after which a third start was accepted beside it. This is the second of the four defects of §8,
ruling 11 of ``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`` ("Fix all
four now").

A start is now refused (``RuntimeError``; HTTP 409) while the previous run's thread is still
alive with its stop pending, before the start touches anything. The stop stays set, so the
stopped ``fit`` unwinds at its next event and none of its later events lands anywhere; once its
thread has ended, a start is accepted and runs alone. The refusal is decided under the manager
lock, and it does not depend on the machine reading ``STOPPED``: a snapshot load is accepted
after a stop, and a start from the state it leaves is refused the same way. A start after a run
that settled itself (``COMPLETED`` or ``FAILED``) is not held back while that thread exits, and a
thread that died without settling blocks nothing.

Eleven of the thirteen tests here fail on a ``manager.py`` without the refusal, at the refused
start (there it was accepted, or refused only after it had cleared the stop); the last two are
controls and pass either way. Every wait is on a ``threading.Event`` with a deadline; nothing
sleeps.
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
from juniper_service_core.routes import build_routers

REFUSAL = "The stopped run's fit is still running"
REFUSAL_DETAIL = "Training cannot be started: The stopped run's fit is still running (a stop takes effect at its next event)"

_PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "phase_change": {"phase": "candidate"},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.25}},
    "training_end": {"metrics": {"mse": 0.25}},
}


class _GatedModel(TrainableModel):
    """A regression model whose ``fit`` call *n* follows ``scripts[n - 1]``; later calls just return.

    A step is ``("emit", event_type)``, sent through the sink; ``("gate", name)``, which signals
    :meth:`reached` and parks until the test calls :meth:`open`; or ``("exit", "")``, which raises
    ``SystemExit`` (an exception the training thread does not catch). ``unwind_gate``, when given,
    parks a ``fit`` that the sink is unwinding before it re-raises: a model that cleans up after a
    stop. It records the events the sink let through, per call (``delivered``), the calls the sink
    unwound (``interrupted``), and the most ``fit`` calls ever running at once (``peak``). Every park
    is bounded, so a failed assertion cannot leave a thread parked forever.
    """

    def __init__(self, *scripts: tuple[tuple[str, str], ...], unwind_gate: str | None = None) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.fits = 0
        self.peak = 0
        self.threads: list[threading.Thread] = []  # the thread of each fit call, in call order
        self.delivered: dict[int, list[str]] = {}
        self.interrupted: list[int] = []
        self._running = 0
        self._scripts = scripts
        self._unwind_gate = unwind_gate
        self._gates: dict[str, tuple[threading.Event, threading.Event]] = {}
        self._lock = threading.Lock()

    def _gate(self, name: str) -> tuple[threading.Event, threading.Event]:
        with self._lock:
            return self._gates.setdefault(name, (threading.Event(), threading.Event()))

    def reached(self, name: str, timeout: float = 5.0) -> bool:
        """True once a ``fit`` has parked at gate ``name``, waiting up to ``timeout`` seconds."""
        return self._gate(name)[1].wait(timeout)

    def was_reached(self, name: str) -> bool:
        """True if a ``fit`` has parked at gate ``name`` (no wait)."""
        return self._gate(name)[1].is_set()

    def open(self, name: str) -> None:
        self._gate(name)[0].set()

    def open_all(self) -> None:
        with self._lock:
            gates = [gate for gate, _ in self._gates.values()]
        for gate in gates:
            gate.set()

    def _park(self, name: str) -> None:
        gate, reached = self._gate(name)
        reached.set()
        gate.wait(timeout=10.0)

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        with self._lock:
            self.fits += 1
            call = self.fits
            script = self._scripts[call - 1] if call <= len(self._scripts) else ()
            self.threads.append(threading.current_thread())
            self.delivered[call] = []
            self._running += 1
            self.peak = max(self.peak, self._running)
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(_PAYLOADS[arg]), 0))
                    with self._lock:
                        self.delivered[call].append(arg)
                elif kind == "gate":
                    self._park(arg)
                elif kind == "exit":
                    raise SystemExit(arg)
        except TrainingInterrupted:
            with self._lock:
                self.interrupted.append(call)
            if self._unwind_gate is not None:
                self._park(self._unwind_gate)
            raise
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


class _HoldsAfterSettling(ServiceLifecycleManager):
    """Holds each training thread after it has settled its run, before the thread exits."""

    def __init__(self, model: TrainableModel) -> None:
        super().__init__(model)
        self.settled = threading.Event()
        self.exit = threading.Event()

    def _train_thread_target(self, *args: Any) -> None:
        super()._train_thread_target(*args)
        self.settled.set()
        self.exit.wait(timeout=10.0)


class _FreshModelSerializer(ModelSerializer):
    """Writes no model file; every ``load`` hands back a fresh model whose ``fit`` just returns.

    The snapshot store keeps its own sidecar, which is all a load needs to find the snapshot.
    """

    def save(self, model: TrainableModel, path: Any) -> None:
        """Nothing to write."""

    def load(self, path: Any) -> TrainableModel:
        return _GatedModel()


class _AnnouncingLock:
    """Stands in for the manager's lock, and says when one given thread is about to wait for it."""

    def __init__(self, lock: Any, watched: threading.Thread) -> None:
        self._lock = lock
        self._watched = watched
        self.wanted = threading.Event()

    def __enter__(self) -> Any:
        if threading.current_thread() is self._watched:
            self.wanted.set()
        return self._lock.__enter__()

    def __exit__(self, *exc_info: Any) -> Any:
        return self._lock.__exit__(*exc_info)


def _zeros(rows: int = 4) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((rows, 2), np.float32), np.zeros((rows, 1), np.float32)


@pytest.fixture
def gated():
    """Build ``(model, manager)`` pairs around a :class:`_GatedModel`, and tear each one down."""
    built: list[tuple[_GatedModel, ServiceLifecycleManager]] = []

    def build(*scripts: tuple[tuple[str, str], ...], unwind_gate: str | None = None, manager_cls: type[ServiceLifecycleManager] = ServiceLifecycleManager, **manager_kwargs: Any) -> tuple[_GatedModel, ServiceLifecycleManager]:
        model = _GatedModel(*scripts, unwind_gate=unwind_gate)
        mgr = manager_cls(model, **manager_kwargs)
        built.append((model, mgr))
        return model, mgr

    yield build
    for model, mgr in built:
        model.open_all()
        if isinstance(mgr, _HoldsAfterSettling):
            mgr.exit.set()
        mgr.shutdown()
        for thread in model.threads:
            thread.join(timeout=5.0)


# Run 1 parks before its next event; every event after the gate would reach the sink if its stop
# were cleared. Run 2 parks once it has started.
_STOPPED_RUN = (("emit", "training_start"), ("gate", "old"), ("emit", "phase_change"), ("emit", "epoch_end"), ("emit", "training_end"), ("gate", "old-after"))
_NEXT_RUN = (("emit", "training_start"), ("gate", "new"))


def _stop_while_parked(mgr: ServiceLifecycleManager, model: _GatedModel) -> threading.Thread:
    """Start run 1 and stop it while its ``fit`` is parked before its next event; return its thread."""
    X, y = _zeros()
    mgr.start_training(X, y, dataset_name="first")
    assert model.reached("old")
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    return model.threads[0]


def _start_and_finish_alone(mgr: ServiceLifecycleManager, model: _GatedModel, gate: str = "new") -> None:
    """A start is accepted, its ``fit`` runs alone to ``COMPLETED``."""
    assert mgr.start_training(*_zeros())["state_machine"]["status"] == "STARTED"
    assert model.reached(gate)
    model.open(gate)
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert model.peak == 1, "two fit calls ran on the model at once"


def test_a_start_while_the_stopped_runs_fit_is_still_running_is_refused(gated) -> None:
    """The refused start changes nothing: no second ``fit``, the stopped run's state and dataset stay."""
    model, mgr = gated(_STOPPED_RUN, _NEXT_RUN)
    old_thread = _stop_while_parked(mgr, model)

    # Before the fix this start was accepted, cleared the stop, and started a second fit beside the first.
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros(rows=6), dataset_name="second")
    assert old_thread.is_alive()
    assert model.fits == 1
    status = mgr.get_status()
    assert status["state_machine"] == {"status": "STOPPED", "phase": "idle", "paused_phase": None}
    assert status["training_active"] is False
    assert status["monitor"]["status"] == "stopped"
    dataset = mgr.get_dataset()
    assert (dataset["name"], dataset["n_train"]) == ("first", 4)


def test_the_stopped_fit_still_sees_its_stop_and_none_of_its_later_events_lands(gated) -> None:
    """After the refused start, the stopped ``fit`` unwinds at its next event; then a start runs alone."""
    model, mgr = gated(_STOPPED_RUN, _NEXT_RUN)
    old_thread = _stop_while_parked(mgr, model)
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())

    model.open("old")  # run 1's fit reaches its next event; its stop is still set, so the sink unwinds it
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == [1]
    # Before the fix its phase_change, epoch_end and training_end went through the sink into the new run.
    assert model.delivered[1] == ["training_start"]
    assert not model.was_reached("old-after")
    status = mgr.get_status()
    assert status["state_machine"] == {"status": "STOPPED", "phase": "idle", "paused_phase": None}
    assert status["monitor"]["status"] == "stopped"
    assert mgr.get_metrics_history() == []

    _start_and_finish_alone(mgr, model)
    assert model.fits == 2


@pytest.fixture
def stack():
    """A live app + manager wired as a real service wires them, driving a gated model."""
    model = _GatedModel(_STOPPED_RUN, _NEXT_RUN)
    manager = ServiceLifecycleManager(model)
    app = create_app(title="test-model-service", version="9.9.9", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, model
    model.open_all()
    manager.shutdown()
    for thread in model.threads:
        thread.join(timeout=5.0)


def test_stop_then_start_over_http_is_a_409_until_the_stopped_fit_has_ended(stack) -> None:
    """The race's own HTTP sequence: start, stop, start at once."""
    client, manager, model = stack
    X, y = _zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}

    assert client.post("/v1/training/start", json=payload).status_code == 200
    assert model.reached("old")
    assert client.post("/v1/training/stop").status_code == 200
    refused = client.post("/v1/training/start", json=payload)
    # Before the fix this was a 200, with two fit calls running on the model.
    assert refused.status_code == 409, refused.text
    assert refused.json()["detail"] == REFUSAL_DETAIL
    assert client.get("/v1/training/status").json()["data"]["state_machine"]["status"] == "STOPPED"

    model.open("old")
    assert manager.join(timeout=5.0)
    started = client.post("/v1/training/start", json=payload)
    assert started.status_code == 200, started.text
    assert model.reached("new")
    model.open("new")
    assert manager.join(timeout=5.0)
    assert client.get("/v1/training/status").json()["data"]["state_machine"]["status"] == "COMPLETED"
    assert model.fits == 2
    assert model.peak == 1


def test_a_stopped_fit_cannot_be_released_by_a_later_paused_completion(gated) -> None:
    """The shared pause gate: stop run 1, start run 2, pause it, run 1 reaches its next event, run 2's fit returns.

    Before the fix the start was accepted, run 1's next event waited at run 2's pause gate, and run
    2's paused completion released it with no command: its events landed in the completed run's
    monitor, and a third start was accepted beside it.
    """
    model, mgr = gated(
        (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end"), ("gate", "old-after")),
        (("emit", "training_start"), ("gate", "new")),
        (("emit", "training_start"), ("gate", "third")),
    )
    old_thread = _stop_while_parked(mgr, model)
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())
    model.open("old")  # run 1's next event sees its stop and unwinds: it never waits at a pause gate
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == [1]

    # Run 2 starts alone, is paused, and its fit returns while paused: the paused completion opens
    # the gate with no stale fit behind it.
    assert mgr.start_training(*_zeros())["state_machine"]["status"] == "STARTED"
    assert model.reached("new")
    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    model.open("new")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert mgr.get_metrics_history() == []  # run 1's epoch_end never reached a monitor
    assert not model.was_reached("old-after")

    _start_and_finish_alone(mgr, model, gate="third")
    assert model.fits == 3


def test_a_start_while_the_stopped_fit_is_still_unwinding_is_refused(gated) -> None:
    """A ``fit`` that has seen the stop and is still cleaning up holds the start back too."""
    model, mgr = gated((("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end")), _NEXT_RUN, unwind_gate="old-unwind")
    old_thread = _stop_while_parked(mgr, model)
    model.open("old")  # the next event sees the stop: the sink raises TrainingInterrupted
    assert model.reached("old-unwind")  # run 1's fit is still unwinding

    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())
    model.open("old-unwind")
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert mgr.get_status()["monitor"]["status"] == "stopped"

    _start_and_finish_alone(mgr, model)


def test_a_stopped_eventless_fit_holds_a_start_back_until_it_returns(gated) -> None:
    """A ``fit`` that emits no events never sees the stop; a start waits for it to return."""
    model, mgr = gated((("gate", "old"),), _NEXT_RUN)
    old_thread = _stop_while_parked(mgr, model)
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())

    model.open("old")  # the fit returns; the stop is still set, so the run stays STOPPED
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == []
    status = mgr.get_status()
    assert status["state_machine"]["status"] == "STOPPED"
    assert status["monitor"]["status"] == "stopped"

    _start_and_finish_alone(mgr, model)


def test_a_reset_then_start_is_refused_the_same_way(gated) -> None:
    """``reset`` sets the stop as ``stop_training`` does, so a start right after it is refused too."""
    model, mgr = gated(_STOPPED_RUN, _NEXT_RUN)
    mgr.start_training(*_zeros())
    assert model.reached("old")
    assert mgr.reset()["state_machine"]["status"] == "STOPPED"
    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())

    model.open("old")
    model.threads[0].join(timeout=5.0)
    assert not model.threads[0].is_alive()
    assert model.interrupted == [1]
    _start_and_finish_alone(mgr, model)


@pytest.mark.parametrize(
    ("load", "loaded_status"),
    [("resume_from_snapshot", "RESUME_READY"), ("load_snapshot", "INVESTIGATING"), ("start_replay", "REPLAYING")],
)
def test_a_start_after_a_snapshot_load_is_refused_while_the_stopped_fit_is_still_running(gated, tmp_path, load: str, loaded_status: str) -> None:
    """The refusal does not depend on the machine reading ``STOPPED``.

    After a stop, a snapshot load is accepted while the stopped run's ``fit`` is still running, and
    it leaves the machine ``RESUME_READY``, ``INVESTIGATING`` or ``REPLAYING``. Before the fix a
    start from ``RESUME_READY`` was accepted, cleared the stop and ran beside that ``fit``; from
    the other two the state machine refused it, but only after the start had cleared the stop. The
    refusal comes first in all three, so the stop stays set and the stopped ``fit`` unwinds.
    """
    model, mgr = gated(_STOPPED_RUN, serializer=_FreshModelSerializer(), snapshot_dir=tmp_path)
    snapshot_id = mgr.save_snapshot()["id"]
    old_thread = _stop_while_parked(mgr, model)
    assert getattr(mgr, load)(snapshot_id)["state_machine"]["status"] == loaded_status

    with pytest.raises(RuntimeError, match=REFUSAL):
        mgr.start_training(*_zeros())
    assert old_thread.is_alive()
    assert mgr.get_status()["state_machine"]["status"] == loaded_status
    assert model.fits == 1

    model.open("old")  # the stopped fit's next event still finds its stop set, and the sink unwinds it
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()
    assert model.interrupted == [1]
    assert model.delivered[1] == ["training_start"]
    assert not model.was_reached("old-after")


def test_a_stop_that_lands_while_a_start_waits_for_the_lock_still_refuses_that_start(gated) -> None:
    """The refusal is decided under the manager lock, after any stop that took the lock first.

    A start that read "no stop pending" before it took the lock, and then waited for the lock while
    a stop landed, would clear that stop and run beside the stopped ``fit``. The test holds the
    lock, lets a second thread's start reach it, stops the run, and only then lets the start in.
    """
    model, mgr = gated(_STOPPED_RUN, _NEXT_RUN)
    mgr.start_training(*_zeros(), dataset_name="first")
    assert model.reached("old")
    outcome: list[str] = []

    def start() -> None:
        try:
            outcome.append(mgr.start_training(*_zeros(rows=6), dataset_name="second")["state_machine"]["status"])
        except RuntimeError as exc:
            outcome.append(str(exc))

    starter = threading.Thread(target=start, name="second-start", daemon=True)
    lock = _AnnouncingLock(mgr._lock, starter)
    mgr._lock = lock
    with lock:
        starter.start()
        assert lock.wanted.wait(timeout=5.0)  # the start has reached the lock and is waiting for it
        assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    starter.join(timeout=5.0)
    assert not starter.is_alive()

    # With the check made before the lock was taken, this start was accepted beside run 1's fit.
    assert outcome == ["The stopped run's fit is still running (a stop takes effect at its next event)"]
    assert model.fits == 1
    dataset = mgr.get_dataset()
    assert (dataset["name"], dataset["n_train"]) == ("first", 4)

    model.open("old")
    model.threads[0].join(timeout=5.0)
    assert not model.threads[0].is_alive()
    assert model.interrupted == [1]
    _start_and_finish_alone(mgr, model)


def test_a_start_right_after_a_run_settled_itself_is_accepted_while_its_thread_exits(gated) -> None:
    """Only a pending stop holds a start back: a completed run's thread may still be exiting."""
    model, mgr = gated((("emit", "training_start"),), _NEXT_RUN, manager_cls=_HoldsAfterSettling)
    mgr.start_training(*_zeros())
    assert mgr.settled.wait(timeout=5.0)
    first_thread = model.threads[0]
    assert first_thread.is_alive()  # it has settled its run but has not exited
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"

    assert mgr.start_training(*_zeros())["state_machine"]["status"] == "STARTED"
    mgr.exit.set()
    first_thread.join(timeout=5.0)
    assert model.reached("new")
    model.open("new")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert model.fits == 2


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_a_thread_that_died_without_settling_does_not_hold_a_start_back(gated) -> None:
    """Control: the refusal reads the thread's liveness, so a dead thread cannot wedge the manager.

    ``SystemExit`` is not an ``Exception``, so the training thread ends without settling: the machine
    still reads ``STARTED``, as before the fix. A stop clears it, and the next start is accepted.
    """
    model, mgr = gated((("emit", "training_start"), ("exit", "")), _NEXT_RUN)
    mgr.start_training(*_zeros())
    assert mgr.join(timeout=5.0), "the training thread did not end"
    assert model.fits == 1
    assert mgr.get_status()["state_machine"]["status"] == "STARTED"
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"

    _start_and_finish_alone(mgr, model)
