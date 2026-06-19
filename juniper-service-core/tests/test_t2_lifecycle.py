"""Unit tests for the WS-2 / OUT-11 T2 lifecycle base (FSM, monitor, orchestrator).

Drives juniper-model-core's *regression* reference models through the generic orchestrator,
so the RK-6 guard (no argmax / accuracy in "generic" code) is exercised by construction. A
small steppable stub gives deterministic, sleep-free coverage of the cooperative pause/stop
path (interrupting an in-flight ``fit`` at an event boundary).
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceGrowableModel, ReferenceLinearModel
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainableModel, TrainResult

from juniper_service_core.lifecycle import (
    LifecycleCommand,
    LifecycleMonitor,
    LifecycleStateMachine,
    LifecycleStatus,
    ServiceLifecycleManager,
)


# --------------------------------------------------------------------------------------
# state machine
# --------------------------------------------------------------------------------------


def test_fsm_start_stop_cycle() -> None:
    sm = LifecycleStateMachine()
    assert sm.is_stopped()
    assert sm.handle_command(LifecycleCommand.START) is True
    assert sm.is_started() and sm.phase == "running"
    assert sm.handle_command(LifecycleCommand.STOP) is True
    assert sm.is_stopped() and sm.phase == "idle"


def test_fsm_pause_resume_restores_phase() -> None:
    sm = LifecycleStateMachine()
    sm.handle_command(LifecycleCommand.START)
    sm.set_phase("warmup")
    assert sm.handle_command(LifecycleCommand.PAUSE) is True
    assert sm.is_paused() and sm.paused_phase == "warmup"
    assert sm.handle_command(LifecycleCommand.RESUME) is True
    assert sm.is_started() and sm.phase == "warmup"


def test_fsm_double_start_rejected() -> None:
    sm = LifecycleStateMachine()
    sm.handle_command(LifecycleCommand.START)
    assert sm.handle_command(LifecycleCommand.START) is False


def test_fsm_mark_completed_only_from_started_then_start_auto_resets() -> None:
    sm = LifecycleStateMachine()
    assert sm.mark_completed() is False  # not from STOPPED
    sm.handle_command(LifecycleCommand.START)
    assert sm.mark_completed() is True
    assert sm.status is LifecycleStatus.COMPLETED
    # START from a terminal state auto-resets then starts.
    assert sm.handle_command(LifecycleCommand.START) is True
    assert sm.is_started()


def test_fsm_reset_always_valid_from_failed() -> None:
    sm = LifecycleStateMachine()
    sm.handle_command(LifecycleCommand.START)
    assert sm.mark_failed("boom") is True
    assert sm.is_failed()
    assert sm.handle_command(LifecycleCommand.RESET) is True
    assert sm.is_stopped()


def test_fsm_set_phase_ignored_when_not_started() -> None:
    sm = LifecycleStateMachine()
    sm.set_phase("nope")
    assert sm.phase == "idle"


def test_fsm_pause_rejected_when_stopped() -> None:
    sm = LifecycleStateMachine()
    assert sm.handle_command(LifecycleCommand.PAUSE) is False


# --------------------------------------------------------------------------------------
# monitor
# --------------------------------------------------------------------------------------


def test_monitor_folds_event_stream() -> None:
    mon = LifecycleMonitor()
    mon.on_event(TrainingEvent("training_start", {"n_samples": 10}, 0))
    mon.on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 0.5}}, 1))
    mon.on_event(TrainingEvent("epoch_end", {"epoch": 1, "metrics": {"mse": 0.2}}, 2))
    mon.on_event(TrainingEvent("unit_added", {"n_units": 1, "unit_id": "u1"}, 3))
    mon.on_event(TrainingEvent("training_end", {"metrics": {"mse": 0.2}}, 4))

    state = mon.get_state()
    assert state["current_epoch"] == 1
    assert state["n_units"] == 1
    assert state["latest_metrics"] == {"mse": 0.2}
    assert mon.get_metrics()["metrics"] == {"mse": 0.2}

    history = mon.get_history()
    assert len(history) == 2
    assert mon.get_history(count=1)[0]["epoch"] == 1


def test_monitor_training_start_clears_history() -> None:
    mon = LifecycleMonitor()
    mon.on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 1.0}}, 0))
    mon.on_event(TrainingEvent("training_start", {}, 0))
    assert mon.get_history() == []


def test_monitor_phase_change_updates_phase() -> None:
    mon = LifecycleMonitor()
    mon.on_event(TrainingEvent("phase_change", {"phase": "candidate"}, 0))
    assert mon.get_state()["phase"] == "candidate"


def test_monitor_history_is_bounded() -> None:
    mon = LifecycleMonitor(history_limit=3)
    for epoch in range(10):
        mon.on_event(TrainingEvent("epoch_end", {"epoch": epoch, "metrics": {"mse": 1.0}}, epoch))
    history = mon.get_history()
    assert len(history) == 3
    assert [entry["epoch"] for entry in history] == [7, 8, 9]


# --------------------------------------------------------------------------------------
# orchestrator -- full run with the regression reference model
# --------------------------------------------------------------------------------------


def test_manager_drives_full_training_to_completed() -> None:
    ds = tiny_regression_2d()
    mgr = ServiceLifecycleManager(ReferenceGrowableModel())
    assert mgr.has_model()
    mgr.start_training(ds.X, ds.y, ds.X_val, ds.y_val)
    assert mgr.join(timeout=5.0)

    status = mgr.get_status()
    assert status["state_machine"]["status"] == "COMPLETED"
    assert status["training_active"] is False

    metrics = mgr.get_metrics()["metrics"]
    assert metrics  # non-empty
    assert "accuracy" not in metrics  # RK-6: a regression model never reports accuracy
    assert all(isinstance(value, float) for value in metrics.values())
    assert len(mgr.get_metrics_history()) >= 1


def test_manager_start_without_model_raises() -> None:
    mgr = ServiceLifecycleManager()
    with pytest.raises(RuntimeError):
        mgr.start_training(np.zeros((2, 2), np.float32), np.zeros((2, 1), np.float32))


def test_manager_reset_clears_dataset_and_state() -> None:
    ds = tiny_regression_2d()
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr.start_training(ds.X, ds.y)
    assert mgr.join(timeout=5.0)
    assert mgr.get_dataset()["has_data"] is True

    mgr.reset()
    assert mgr.get_status()["state_machine"]["status"] == "STOPPED"
    assert mgr.get_dataset()["has_data"] is False


def test_manager_get_topology_delegates_to_model() -> None:
    mgr = ServiceLifecycleManager(ReferenceGrowableModel())
    topo = mgr.get_topology()
    assert topo is not None
    assert topo["model_type"] == "reference_growable"
    assert "n_units" in topo["meta"]


def test_manager_get_topology_none_without_model() -> None:
    assert ServiceLifecycleManager().get_topology() is None


# --------------------------------------------------------------------------------------
# orchestrator -- deterministic cooperative pause / stop via a steppable stub
# --------------------------------------------------------------------------------------


class _SteppableModel(TrainableModel):
    """A regression model whose ``fit`` blocks before each epoch's event, so a test can step
    it deterministically and interrupt it mid-run at an event boundary."""

    def __init__(self, n_epochs: int = 4) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self._n_epochs = n_epochs
        self._in: tuple[int, ...] = (1,)
        self._out: tuple[int, ...] = (1,)
        self.at_gate = threading.Event()  # set while parked, waiting to emit the next epoch
        self.step_gate = threading.Event()  # the test sets this to release one epoch

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        self._in = tuple(X.shape[1:])
        self._out = tuple(y.shape[1:])
        if on_event is not None:
            on_event(TrainingEvent("training_start", {}, 0))
        for epoch in range(self._n_epochs):
            self.at_gate.set()
            self.step_gate.wait()
            self.step_gate.clear()
            if on_event is not None:
                # If the orchestrator requested a stop, this call raises and unwinds fit.
                on_event(TrainingEvent("epoch_end", {"epoch": epoch, "metrics": {"mse": 1.0 / (epoch + 1)}}, 0))
        if on_event is not None:
            on_event(TrainingEvent("training_end", {}, 0))
        return TrainResult(final_metrics={"mse": 0.1}, n_epochs=self._n_epochs)

    def predict(self, X, **kw) -> np.ndarray:
        return np.zeros((X.shape[0], *self._out))

    def metrics(self) -> dict[str, float]:
        return {"mse": 0.1}

    def describe_topology(self) -> dict[str, Any]:
        return {"model_type": "steppable", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

    @property
    def input_shape(self) -> tuple[int, ...]:
        return self._in

    @property
    def output_shape(self) -> tuple[int, ...]:
        return self._out


def _wait_at_gate(model: _SteppableModel) -> None:
    assert model.at_gate.wait(timeout=2.0), "training thread never reached the epoch gate"
    model.at_gate.clear()


def test_manager_cooperative_stop_unwinds_fit() -> None:
    model = _SteppableModel(n_epochs=5)
    mgr = ServiceLifecycleManager(model)
    mgr.start_training(np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32))

    _wait_at_gate(model)  # parked before emitting epoch 0
    assert mgr.get_status()["state_machine"]["status"] == "STARTED"

    mgr.stop_training()  # sets the stop flag + FSM -> STOPPED
    model.step_gate.set()  # release: the epoch-0 emit hits the sink, which raises and unwinds

    assert mgr.join(timeout=2.0)
    status = mgr.get_status()
    assert status["state_machine"]["status"] == "STOPPED"
    assert status["training_active"] is False


def test_manager_pause_resume_around_an_active_run() -> None:
    model = _SteppableModel(n_epochs=5)
    mgr = ServiceLifecycleManager(model)
    mgr.start_training(np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32))

    _wait_at_gate(model)
    assert mgr.get_status()["state_machine"]["status"] == "STARTED"

    assert mgr.pause_training()["state_machine"]["status"] == "PAUSED"
    assert mgr.resume_training()["state_machine"]["status"] == "STARTED"

    # Clean up: stop and let the parked thread observe it.
    mgr.stop_training()
    model.step_gate.set()
    assert mgr.join(timeout=2.0)
    assert mgr.get_status()["state_machine"]["status"] == "STOPPED"


def test_manager_pause_rejected_when_not_running() -> None:
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    with pytest.raises(RuntimeError):
        mgr.pause_training()
