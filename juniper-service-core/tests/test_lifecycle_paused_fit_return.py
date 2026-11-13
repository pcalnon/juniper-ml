"""Pin how ``ServiceLifecycleManager`` settles a ``fit`` that returns while the run is PAUSED.

Pause is cooperative: the event sink blocks in ``_pause_event.wait()`` at the next event the
model emits. A pause that arrives after the model's last event (or during a ``fit`` that emits
none) never reaches that wait, so ``fit`` returns while the lifecycle is still PAUSED. The run is
over at that point: the pause has nothing left to hold.

Before this fix the training thread called ``mark_completed()``, which accepts only STARTED (the
cascor-mirrored machine), ignored its refusal, and wrote ``monitor.status`` ``completed``. The
machine stayed PAUSED with no thread behind it, a resume then moved it to STARTED (still no
thread), and every start with data was refused (HTTP 409 ``Training cannot be started: Training
already in progress``; one without data is a 400) until a stop or reset. This is the "paused-fit
wedge" in §4 of ``notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md``.

The run now settles COMPLETED, exactly as if the pause had not been requested: the machine is not
active, no pause is left pending, a resume is refused because nothing is paused, and a start runs
a fresh ``fit``. A stop that races the completion still settles STOPPED, and a resume that lands
before ``fit`` returns still continues the same run. A ``fit`` that raises while paused settles
FAILED and releases the pause as well.

The training thread settles only a run it still owns. ``start_training`` now refuses a start while
a stopped run's ``fit`` is still running (the stop-then-start race, pinned by
``tests/test_lifecycle_stop_then_start.py``), so a newer run can no longer become current first.
Before that refusal, a start issued right after a stop made a newer run current while the stopped
run's ``fit`` was still running: before that ``fit`` reached an event (the start cleared the stop,
so the ``fit`` kept running), or while it was still unwinding from the stop. The
``test_a_stopped_runs_*`` tests rebuild that interleaving by clearing the stop before the start
(``_start_beside_the_stopped_fit``), and pin that the ownership check, now a second line of
defence, still keeps the stale thread's settle off the newer run. On 0.7.2 and earlier the stale
thread completed a newer run that was still training (a third start was then accepted beside it),
failed it, or wrote its monitor context ``stopped``; and the paused-completion branch, unguarded,
would also have resumed a newer paused run and completed it mid-``fit``. The run's result is
recorded under the same guard, so a ``fit`` whose run was stopped records none, superseded or
not: no start can clear its stop while it is still running, because ``start_training`` refuses
first (also from ``INVESTIGATING`` and ``REPLAYING``, where the stop used to be cleared before the
state machine refused the start).
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainableModel, TrainResult

from juniper_service_core.app import create_app
from juniper_service_core.lifecycle import ServiceLifecycleManager, TrainingInterrupted
from juniper_service_core.routes import build_routers


class _TailGatedModel(TrainableModel):
    """A regression model whose ``fit`` parks after its last event, then returns.

    With ``emit_events`` it emits ``training_start``, a ``phase_change`` into ``candidate``, one
    ``epoch_end`` and ``training_end``; without it, it emits nothing (a black-box ``fit``). Either
    way nothing is emitted after the tail gate, so a pause requested while ``fit`` is parked there
    cannot be honoured: ``fit`` returns while the lifecycle is PAUSED.
    """

    def __init__(self, *, emit_events: bool = True) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.emit_events = emit_events
        self._in: tuple[int, ...] = (1,)
        self._out: tuple[int, ...] = (1,)
        self.fits = 0
        self.at_tail = threading.Event()  # set once fit has emitted its last event and parked
        self.release = threading.Event()  # the test sets this to let fit return

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        self.fits += 1
        self._in = tuple(X.shape[1:])
        self._out = tuple(y.shape[1:])
        if self.emit_events and on_event is not None:
            on_event(TrainingEvent("training_start", {}, 0))
            on_event(TrainingEvent("phase_change", {"phase": "candidate"}, 0))
            on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 0.5}}, 0))
            on_event(TrainingEvent("training_end", {"metrics": {"mse": 0.5}}, 0))
        self.at_tail.set()
        # Bounded, so a failed assertion in the test cannot leave this thread parked forever.
        self.release.wait(timeout=10.0)
        return TrainResult(final_metrics={"mse": 0.5}, n_epochs=1)

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], *self._out))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.5}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "tail_gated", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return self._in

    @property
    def output_shape(self) -> tuple[int, ...]:
        return self._out


_PAYLOADS: dict[str, dict[str, Any]] = {
    "training_start": {},
    "epoch_end": {"epoch": 0, "metrics": {"mse": 0.5}},
}


class _ScriptedModel(TrainableModel):
    """A regression model whose ``fit`` call *n* follows ``scripts[n - 1]``; later calls just return.

    A step is ``("emit", event_type)``, sent through the sink; ``("gate", name)``, which signals
    :meth:`reached` and parks until the test calls :meth:`open`; or ``("raise", message)``.
    ``unwind_gate``, when given, parks a ``fit`` that the sink is unwinding with
    ``TrainingInterrupted`` before it re-raises: a model that cleans up after a stop. Every park is
    bounded, so a failed assertion cannot leave a thread parked forever.
    """

    def __init__(self, *scripts: tuple[tuple[str, str], ...], unwind_gate: str | None = None) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self.fits = 0
        self.threads: list[threading.Thread] = []  # the thread of each fit call, in call order
        self.results: dict[int, TrainResult] = {}  # fit call number -> what that call returned
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
        try:
            for kind, arg in script:
                if kind == "emit" and on_event is not None:
                    on_event(TrainingEvent(arg, dict(_PAYLOADS[arg]), 0))
                elif kind == "gate":
                    self._park(arg)
                elif kind == "raise":
                    raise RuntimeError(arg)
        except TrainingInterrupted:
            if self._unwind_gate is not None:
                self._park(self._unwind_gate)
            raise
        result = TrainResult(final_metrics={"mse": 0.5}, n_epochs=1)
        with self._lock:
            self.results[call] = result
        return result

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], 1))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.5}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "scripted", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return (2,)

    @property
    def output_shape(self) -> tuple[int, ...]:
        return (1,)


def _zeros() -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32)


def _wait_at_tail(model: _TailGatedModel) -> None:
    assert model.at_tail.wait(timeout=5.0), "training thread never reached the tail gate"
    model.at_tail.clear()


def _pause_after_last_event(mgr: ServiceLifecycleManager, model: _TailGatedModel) -> None:
    """Start a run, pause it once ``fit`` has emitted its last event, then let ``fit`` return."""
    X, y = _zeros()
    mgr.start_training(X, y)
    _wait_at_tail(model)
    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    model.release.set()  # fit returns: no further event, so the sink's pause wait never runs
    assert mgr.join(timeout=5.0), "the training thread did not exit after fit returned"


def _direct_run_returns(mgr: ServiceLifecycleManager) -> bool:
    """Drive ``mgr.run()``, the public synchronous body, on a helper thread; True if it returned.

    ``run`` sends the model's events through the manager's event sink, so a pause gate left closed
    holds it at the model's first event. On a timeout ``stop_training`` opens the gate and unwinds
    the held run, so the helper thread does not outlive the test.
    """
    X, y = _zeros()
    returned = threading.Event()

    def body() -> None:
        try:
            mgr.run(X, y)
        except TrainingInterrupted:
            return
        returned.set()

    helper = threading.Thread(target=body, name="direct-run", daemon=True)
    helper.start()
    ok = returned.wait(timeout=5.0)
    if not ok:
        mgr.stop_training()
    helper.join(timeout=5.0)
    return ok


@pytest.mark.parametrize("emit_events", [True, False], ids=["after-last-event", "eventless-fit"])
def test_fit_that_returns_while_paused_settles_completed(emit_events: bool) -> None:
    model = _TailGatedModel(emit_events=emit_events)
    mgr = ServiceLifecycleManager(model)
    _pause_after_last_event(mgr, model)

    status = mgr.get_status()
    # Before the fix: {"status": "PAUSED", "phase": <the paused phase>, "paused_phase": <same>}.
    assert status["state_machine"] == {"status": "COMPLETED", "phase": "idle", "paused_phase": None}
    assert status["training_active"] is False
    assert status["monitor"]["status"] == "completed"
    assert status["monitor"]["phase"] == "idle"
    # No pause is left pending: the public synchronous body runs straight through. Its fit must
    # emit, or a pause gate left closed would never be reached.
    model.emit_events = True
    assert _direct_run_returns(mgr), "run() blocked at its first event: the paused completion left the pause gate closed"

    # A start (no resume) runs a fresh fit, exactly as after any completed run.
    X, y = _zeros()
    assert mgr.start_training(X, y)["state_machine"]["status"] == "STARTED"
    assert mgr.join(timeout=5.0)
    assert model.fits == 3  # the paused run, the direct run(), the new run
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"


@pytest.fixture
def stack():
    """A live app + manager wired as a real service wires them, driving a tail-gated model."""
    model = _TailGatedModel()
    manager = ServiceLifecycleManager(model)
    app = create_app(title="test-model-service", version="9.9.9", routers=build_routers())
    app.state.lifecycle = manager
    with TestClient(app) as client:
        yield client, manager, model
    model.release.set()
    manager.shutdown()


def test_resume_then_start_after_a_paused_fit_returned_over_http(stack) -> None:
    """The defect's own sequence: pause, let ``fit`` return, resume, then start."""
    client, manager, model = stack
    X, y = _zeros()
    payload = {"inline_data": {"train_x": X.tolist(), "train_y": y.tolist()}}

    assert client.post("/v1/training/start", json=payload).status_code == 200
    _wait_at_tail(model)
    paused = client.post("/v1/training/pause")
    assert paused.status_code == 200, paused.text
    assert paused.json()["data"]["state_machine"]["status"] == "PAUSED"
    model.release.set()
    assert manager.join(timeout=5.0)

    resume = client.post("/v1/training/resume")
    start = client.post("/v1/training/start", json=payload)
    # Before the fix the resume answered 200 (STARTED, with no thread behind it) and this start
    # was a 409, "Training cannot be started: Training already in progress".
    assert start.status_code == 200, start.text
    assert resume.status_code == 409, resume.text
    assert resume.json()["detail"] == "Training cannot be resumed in the current state"

    assert manager.join(timeout=5.0)
    status = client.get("/v1/training/status").json()["data"]
    assert status["state_machine"]["status"] == "COMPLETED"
    assert status["training_active"] is False
    assert model.fits == 2


def test_stop_that_races_a_paused_completion_still_settles_stopped() -> None:
    """Control: a stop requested during the pause wins over the completion, as before."""
    model = _TailGatedModel()
    mgr = ServiceLifecycleManager(model)
    X, y = _zeros()
    mgr.start_training(X, y)
    _wait_at_tail(model)
    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    model.release.set()
    assert mgr.join(timeout=5.0)

    status = mgr.get_status()
    assert status["state_machine"] == {"status": "STOPPED", "phase": "idle", "paused_phase": None}
    assert status["training_active"] is False
    assert status["monitor"]["status"] == "stopped"


def test_resume_before_fit_returns_still_completes_the_same_run() -> None:
    """Control: a resume that lands while the thread is alive continues that run to COMPLETED."""
    model = _TailGatedModel()
    mgr = ServiceLifecycleManager(model)
    X, y = _zeros()
    mgr.start_training(X, y)
    _wait_at_tail(model)
    assert mgr.pause_training()["state_machine"]["paused_phase"] == "candidate"
    resumed = mgr.resume_training()["state_machine"]
    assert resumed == {"status": "STARTED", "phase": "candidate", "paused_phase": None}
    model.release.set()
    assert mgr.join(timeout=5.0)

    assert mgr.get_status()["state_machine"] == {"status": "COMPLETED", "phase": "idle", "paused_phase": None}
    assert model.fits == 1


@pytest.fixture
def scripted():
    """Build ``(model, manager)`` pairs around a :class:`_ScriptedModel`, and tear each one down."""
    built: list[tuple[_ScriptedModel, ServiceLifecycleManager]] = []

    def build(*scripts: tuple[tuple[str, str], ...], unwind_gate: str | None = None) -> tuple[_ScriptedModel, ServiceLifecycleManager]:
        model = _ScriptedModel(*scripts, unwind_gate=unwind_gate)
        mgr = ServiceLifecycleManager(model)
        built.append((model, mgr))
        return model, mgr

    yield build
    for model, mgr in built:
        model.open_all()
        mgr.shutdown()
        for thread in model.threads:
            if thread is not threading.current_thread():
                thread.join(timeout=5.0)


def test_fit_that_raises_while_paused_settles_failed_and_releases_the_pause(scripted) -> None:
    """A ``fit`` that raises after the pause settles FAILED and leaves no pause pending."""
    model, mgr = scripted((("emit", "training_start"), ("emit", "epoch_end"), ("gate", "tail"), ("raise", "boom")), (("emit", "training_start"),))
    X, y = _zeros()
    mgr.start_training(X, y)
    assert model.reached("tail")
    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    model.open("tail")  # fit raises: no further event, so the sink's pause wait never runs
    assert mgr.join(timeout=5.0)

    status = mgr.get_status()
    assert status["state_machine"] == {"status": "FAILED", "phase": "idle", "paused_phase": None}
    assert status["error"] == "boom"
    assert status["training_active"] is False
    assert status["monitor"]["status"] == "failed"
    assert _direct_run_returns(mgr), "run() blocked at its first event: the failure left the pause gate closed"


_OLD_RETURNS = (("emit", "training_start"), ("gate", "old"))
_OLD_RAISES = (("emit", "training_start"), ("gate", "old"), ("raise", "old-boom"))
_NEW_RUNS = (("emit", "training_start"), ("gate", "new"))
_NEW_PAUSES = (*_NEW_RUNS, ("emit", "epoch_end"), ("gate", "new-tail"))


def _start_beside_the_stopped_fit(mgr: ServiceLifecycleManager, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """Start a newer run while the stopped run's ``fit`` is still running, as a start once could.

    ``start_training`` refuses that start while the stop is pending (the stop-then-start race;
    ``tests/test_lifecycle_stop_then_start.py``). Clearing the stop first, as the start itself
    used to, rebuilds the interleaving the refusal now prevents, so the tests below still pin the
    ownership check behind it.
    """
    mgr._stop_event.clear()
    return mgr.start_training(X, y)


def _stop_then_start_at_once(mgr: ServiceLifecycleManager, model: _ScriptedModel) -> threading.Thread:
    """Park run 1 before its next event, stop it, and start run 2 beside it; return run 1's thread.

    The start lands with the stop cleared before run 1's ``fit`` reaches an event, so that ``fit``
    never sees it and keeps running beside run 2, which parks at its ``new`` gate. Run 1's thread
    is no longer the manager's.
    """
    X, y = _zeros()
    mgr.start_training(X, y)
    assert model.reached("old")
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    assert _start_beside_the_stopped_fit(mgr, X, y)["state_machine"]["status"] == "STARTED"
    assert model.reached("new")
    return model.threads[0]


def _pause_the_new_run(mgr: ServiceLifecycleManager, model: _ScriptedModel) -> None:
    """Pause run 2 while it is parked, then let it go: its next event waits in the sink's pause wait."""
    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    model.open("new")


def _assert_the_new_run_is_still_paused_and_held(mgr: ServiceLifecycleManager, model: _ScriptedModel) -> None:
    status = mgr.get_status()
    assert status["state_machine"] == {"status": "PAUSED", "phase": "running", "paused_phase": "running"}
    assert status["training_active"] is True
    assert status["monitor"]["status"] == "paused"
    assert "error" not in status
    # Run 2 is still held by its pause (bounded, since this is a negative check) ...
    assert not model.reached("new-tail", timeout=0.5), "run 2 got past its pause: the stale thread opened the pause gate"
    # ... and the machine still refuses a third, concurrent run.
    with pytest.raises(RuntimeError, match="Training already in progress"):
        mgr.start_training(*_zeros())


def _resume_and_finish_the_new_run(mgr: ServiceLifecycleManager, model: _ScriptedModel) -> None:
    assert mgr.resume_training()["state_machine"]["status"] == "STARTED"
    assert model.reached("new-tail")
    model.open("new-tail")
    assert mgr.join(timeout=5.0)
    status = mgr.get_status()
    assert status["state_machine"] == {"status": "COMPLETED", "phase": "idle", "paused_phase": None}
    assert "error" not in status
    assert model.fits == 2


def test_a_stopped_runs_fit_that_returns_leaves_a_newer_running_run_alone(scripted) -> None:
    """A stale return must not complete a newer run that is still training."""
    model, mgr = scripted(_OLD_RETURNS, _NEW_RUNS)
    old_thread = _stop_then_start_at_once(mgr, model)
    model.open("old")  # run 1's fit returns while run 2's fit is still running
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()

    # Without the ownership guard (as on 0.7.2), run 1's thread marked run 2 COMPLETED while its fit
    # was still running, and a third start was then accepted beside it.
    status = mgr.get_status()
    assert status["state_machine"]["status"] == "STARTED"
    assert status["training_active"] is True
    assert status["monitor"]["status"] == "running"
    with pytest.raises(RuntimeError, match="Training already in progress"):
        mgr.start_training(*_zeros())

    model.open("new")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert model.fits == 2


def test_a_stopped_runs_fit_that_returns_leaves_a_newer_paused_run_alone(scripted) -> None:
    """A stale return must not resume, release or complete the newer, paused run."""
    model, mgr = scripted(_OLD_RETURNS, _NEW_PAUSES)
    old_thread = _stop_then_start_at_once(mgr, model)
    _pause_the_new_run(mgr, model)
    model.open("old")  # run 1's fit returns, with no event in between
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()

    # Without the ownership guard, run 1's thread issued RESUME on run 2, opened the pause gate and
    # marked run 2 COMPLETED while its fit was still running.
    _assert_the_new_run_is_still_paused_and_held(mgr, model)
    _resume_and_finish_the_new_run(mgr, model)


def test_a_stopped_runs_fit_that_raises_leaves_a_newer_paused_run_alone(scripted) -> None:
    """A stale failure must not mark the newer, paused run FAILED or release its pause."""
    model, mgr = scripted(_OLD_RAISES, _NEW_PAUSES)
    old_thread = _stop_then_start_at_once(mgr, model)
    _pause_the_new_run(mgr, model)
    model.open("old")  # run 1's fit raises, with no event in between
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()

    # Without the ownership guard, run 1's error marked run 2 FAILED ("old-boom").
    _assert_the_new_run_is_still_paused_and_held(mgr, model)
    _resume_and_finish_the_new_run(mgr, model)


def test_a_stopped_runs_interrupt_leaves_a_newer_runs_monitor_alone(scripted) -> None:
    """A stale thread that finishes unwinding a stop after a newer start must not mark it stopped."""
    model, mgr = scripted(
        (("emit", "training_start"), ("gate", "old"), ("emit", "epoch_end")),
        (("emit", "training_start"), ("gate", "new")),
        unwind_gate="old-unwind",
    )
    X, y = _zeros()
    mgr.start_training(X, y)
    assert model.reached("old")
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    model.open("old")  # run 1's next event sees the stop, and the sink raises TrainingInterrupted
    assert model.reached("old-unwind")  # run 1's fit is still cleaning up when run 2 starts
    assert _start_beside_the_stopped_fit(mgr, X, y)["state_machine"]["status"] == "STARTED"
    assert model.reached("new")
    old_thread = model.threads[0]
    model.open("old-unwind")
    old_thread.join(timeout=5.0)
    assert not old_thread.is_alive()

    status = mgr.get_status()
    # Without the ownership guard, run 1's thread wrote monitor stopped / idle over run 2's context
    # while the machine said STARTED.
    assert status["monitor"]["status"] == "running"
    assert status["monitor"]["phase"] == "running"
    assert status["state_machine"]["status"] == "STARTED"
    assert status["training_active"] is True

    model.open("new")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert model.fits == 2


def test_only_the_run_that_completes_records_its_result(scripted) -> None:
    """A stopped run's ``fit`` returns a result that is not recorded; the completed run's is.

    ``_last_result`` is written under the same guard as the completion. Nothing reads it yet, so
    no other test sees it. On 0.7.2 and earlier every return was recorded: a stopped run's, and a
    superseded run's over the newer run.
    """
    model, mgr = scripted(
        (("emit", "training_start"), ("gate", "a")),
        (("emit", "training_start"), ("gate", "b")),
        (("emit", "training_start"), ("gate", "c")),
    )
    X, y = _zeros()

    # Run 1 is stopped while its fit is parked; that fit then returns with the stop still set.
    mgr.start_training(X, y)
    assert model.reached("a")
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    model.open("a")
    assert mgr.join(timeout=5.0)
    assert 1 in model.results  # fit 1 returned a result ...
    assert mgr._last_result is None  # ... and it was not recorded

    # Run 2 is stopped and run 3 started beside it; run 2's fit then returns, its run superseded.
    mgr.start_training(X, y)
    assert model.reached("b")
    assert mgr.stop_training()["state_machine"]["status"] == "STOPPED"
    assert _start_beside_the_stopped_fit(mgr, X, y)["state_machine"]["status"] == "STARTED"
    assert model.reached("c")
    stale_thread = model.threads[1]
    model.open("b")
    stale_thread.join(timeout=5.0)
    assert not stale_thread.is_alive()
    assert 2 in model.results
    assert mgr._last_result is None

    # Run 3 completes and records its own result.
    model.open("c")
    assert mgr.join(timeout=5.0)
    assert mgr.get_status()["state_machine"]["status"] == "COMPLETED"
    assert mgr._last_result is model.results[3]
