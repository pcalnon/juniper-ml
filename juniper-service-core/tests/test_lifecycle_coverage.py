"""Deterministic statement-coverage tests for the ``lifecycle/`` subsystem (C-4b).

Targets the residual gaps in ``manager.py`` (the background-threaded orchestrator),
``replay.py`` and ``state_machine.py`` -- guard clauses, terminal / illegal transitions,
snapshot + replay control edges, the cooperative stop-after-pause interrupt, and the
best-effort frame-sink error swallowing. Every threaded path is driven exactly the way
``tests/test_t2_lifecycle.py`` drives the manager: a steppable model gated by
:class:`threading.Event`s and the manager's own ``join`` / status APIs -- no sleep polling.
The replay control surface is exercised synchronously (no daemon started) for determinism,
mirroring ``tests/test_t2_replay.py``.
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import (
    ReferenceGrowableModel,
    ReferenceLinearModel,
    ReferenceLinearSerializer,
)
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainableModel, TrainResult

from juniper_service_core.lifecycle import (
    LifecycleCommand,
    LifecycleMonitor,
    LifecycleStateMachine,
    ReplaySession,
    ServiceLifecycleManager,
    SnapshotStore,
    TrainingInterrupted,
)

# --------------------------------------------------------------------------------------
# fakes -- minimal model-core TrainableModel implementations for deterministic drive
# --------------------------------------------------------------------------------------


class _SteppableModel(TrainableModel):
    """A model whose ``fit`` parks before each epoch's event, so a test steps it and can
    interrupt it mid-run at an event boundary (mirrors ``tests/test_t2_lifecycle.py``)."""

    def __init__(self, n_epochs: int = 5) -> None:
        self.task_type = "regression"
        self.random_seed = 0
        self._n_epochs = n_epochs
        self._in: tuple[int, ...] = (1,)
        self._out: tuple[int, ...] = (1,)
        self.at_gate = threading.Event()
        self.step_gate = threading.Event()

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


class _RaisingFitModel(ReferenceLinearModel):
    """``fit`` emits one event then raises a normal exception (settles the FSM in FAILED)."""

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        if on_event is not None:
            on_event(TrainingEvent("training_start", {}, 0))
        raise ValueError("boom")


class _RaisingTopoModel(ReferenceLinearModel):
    """``describe_topology`` raises -- forces ``_safe_model_type``'s fallback branch."""

    def describe_topology(self) -> dict[str, Any]:
        raise RuntimeError("no topology available pre-fit")


def _zeros() -> tuple[np.ndarray, np.ndarray]:
    return np.zeros((4, 2), np.float32), np.zeros((4, 1), np.float32)


def _wait_at_gate(model: _SteppableModel) -> None:
    assert model.at_gate.wait(timeout=2.0), "training thread never reached the epoch gate"
    model.at_gate.clear()


def _drain(mgr: ServiceLifecycleManager, model: _SteppableModel) -> None:
    """Stop the active steppable run and join its thread deterministically."""
    mgr.stop_training()
    model.step_gate.set()
    assert mgr.join(timeout=2.0)


# --------------------------------------------------------------------------------------
# state_machine.py -- predicates + illegal/terminal transitions
# --------------------------------------------------------------------------------------


def test_state_machine_status_predicates() -> None:
    sm = LifecycleStateMachine()
    assert not sm.is_completed()
    assert not sm.is_investigating()
    assert not sm.is_resume_ready()
    assert not sm.is_replaying()

    sm.handle_command(LifecycleCommand.START)
    assert sm.mark_completed() is True
    assert sm.is_completed() is True

    inv = LifecycleStateMachine()
    assert inv.mark_investigating() is True and inv.is_investigating() is True
    res = LifecycleStateMachine()
    assert res.mark_resume_ready() is True and res.is_resume_ready() is True
    rep = LifecycleStateMachine()
    assert rep.mark_replaying() is True and rep.is_replaying() is True


def test_state_machine_start_from_paused_restores_phase() -> None:
    sm = LifecycleStateMachine()
    sm.handle_command(LifecycleCommand.START)
    sm.set_phase("warmup")
    assert sm.handle_command(LifecycleCommand.PAUSE) is True
    # START (not RESUME) from PAUSED restores the remembered phase.
    assert sm.handle_command(LifecycleCommand.START) is True
    assert sm.is_started() and sm.phase == "warmup"


def test_state_machine_resume_rejected_when_not_paused() -> None:
    sm = LifecycleStateMachine()
    assert sm.handle_command(LifecycleCommand.RESUME) is False
    assert sm.is_stopped()


def test_state_machine_mark_failed_rejected_when_not_active() -> None:
    sm = LifecycleStateMachine()
    assert sm.mark_failed("nope") is False  # from STOPPED
    assert sm.is_stopped()


def test_state_machine_snapshot_marks_rejected_while_active() -> None:
    sm = LifecycleStateMachine()
    sm.handle_command(LifecycleCommand.START)
    assert sm.mark_investigating() is False
    assert sm.mark_resume_ready() is False
    assert sm.mark_replaying() is False
    assert sm.is_started()  # unchanged


# --------------------------------------------------------------------------------------
# replay.py -- synchronous control surface (no daemon started)
# --------------------------------------------------------------------------------------


def _history(n: int) -> list[dict[str, Any]]:
    return [{"epoch": i, "metrics": {"mse": 1.0 / (i + 1)}, "seq": i} for i in range(n)]


def test_replay_pause_action_sets_paused() -> None:
    session = ReplaySession("s", _history(4))
    session.control("play")
    assert session.control("pause")["paused"] is True


def test_replay_step_returns_false_when_paused() -> None:
    session = ReplaySession("s", _history(4))  # starts paused
    assert session.step() is False


def test_replay_stop_fires_on_complete_once() -> None:
    calls: list[int] = []
    session = ReplaySession("s", _history(3), on_complete=lambda: calls.append(1))
    session.stop()
    session.stop()  # already stopped -> hook not fired again
    assert calls == [1]


def test_replay_stop_swallows_on_complete_error() -> None:
    def boom() -> None:
        raise RuntimeError("hook down")

    session = ReplaySession("s", _history(2), on_complete=boom)
    session.stop()  # must not propagate
    assert session.state()["stopped"] is True


def test_replay_join_true_when_never_started() -> None:
    session = ReplaySession("s", _history(2))
    assert session.join(timeout=0.1) is True


def test_replay_frame_none_for_empty_history() -> None:
    session = ReplaySession("s", [])
    state = session.state()
    assert state["length"] == 0
    assert state["frame"] is None


def test_replay_emit_frame_swallows_sink_error() -> None:
    def boom(_frame: dict[str, Any]) -> None:
        raise RuntimeError("sink down")

    session = ReplaySession("s", _history(4), on_frame=boom)
    # seek emits a frame synchronously through the sink; the error must be swallowed.
    result = session.control("seek", time_index=1)
    assert result["time_index"] == 1


# --------------------------------------------------------------------------------------
# monitor.py + snapshots.py -- small residual nudges (pooled margin)
# --------------------------------------------------------------------------------------


def test_monitor_set_run_context_max_epochs() -> None:
    mon = LifecycleMonitor()
    mon.set_run_context(max_epochs=7)
    assert mon.get_state()["max_epochs"] == 7


def test_monitor_restore_with_explicit_scalars() -> None:
    mon = LifecycleMonitor()
    mon.restore(
        [{"epoch": 3, "metrics": {"mse": 0.2}, "n_units": 9}],
        n_units=5,
        status="investigating",
        phase="idle",
    )
    state = mon.get_state()
    assert state["n_units"] == 5
    assert state["status"] == "investigating"
    assert state["phase"] == "idle"


def test_monitor_restore_infers_n_units_from_last_entry() -> None:
    mon = LifecycleMonitor()
    mon.restore([{"epoch": 1, "metrics": {"mse": 0.5}, "n_units": 4}])
    assert mon.get_state()["n_units"] == 4


def test_snapshot_store_list_empty_when_base_absent(tmp_path) -> None:
    store = SnapshotStore(ReferenceLinearSerializer(), tmp_path / "does-not-exist")
    assert store.list() == []


# --------------------------------------------------------------------------------------
# manager.py -- unit-level query/guard surface (no threads)
# --------------------------------------------------------------------------------------


def test_attach_model_resets_state_and_context() -> None:
    mgr = ServiceLifecycleManager()
    assert mgr.has_model() is False
    mgr.attach_model(ReferenceLinearModel())
    assert mgr.has_model() is True
    assert mgr.monitor.get_state()["model_type"] is not None


def test_run_without_model_raises() -> None:
    mgr = ServiceLifecycleManager()
    with pytest.raises(RuntimeError):
        mgr.run(np.zeros((2, 2), np.float32), np.zeros((2, 1), np.float32))


def test_get_dataset_data_none_without_data() -> None:
    assert ServiceLifecycleManager().get_dataset_data() is None


def test_get_dataset_data_includes_val_split() -> None:
    mgr = ServiceLifecycleManager()
    mgr._train_x = np.zeros((3, 2), np.float32)
    mgr._train_y = np.zeros((3, 1), np.float32)
    mgr._val_x = np.zeros((1, 2), np.float32)
    mgr._val_y = np.zeros((1, 1), np.float32)
    data = mgr.get_dataset_data()
    assert data is not None
    assert "train_x" in data and "val_x" in data and "val_y" in data


def test_get_network_info_empty_without_model() -> None:
    assert ServiceLifecycleManager().get_network_info() == {}


def test_get_network_info_includes_n_units_for_growable() -> None:
    info = ServiceLifecycleManager(ReferenceGrowableModel()).get_network_info()
    assert info["model_type"] == "reference_growable"
    assert "n_units" in info


def test_safe_model_type_none_without_model() -> None:
    assert ServiceLifecycleManager()._safe_model_type() is None


def test_safe_model_type_falls_back_on_topology_error() -> None:
    mgr = ServiceLifecycleManager()
    mgr.model = _RaisingTopoModel()
    assert mgr._safe_model_type() == "_RaisingTopoModel"


def test_save_snapshot_without_model_raises(tmp_path) -> None:
    mgr = ServiceLifecycleManager(serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    with pytest.raises(RuntimeError):
        mgr.save_snapshot()


def test_new_snapshot_id_collision_appends_suffix(tmp_path) -> None:
    mgr = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)

    class _CountingStore:
        def __init__(self) -> None:
            self.checked: list[str] = []

        def exists(self, snapshot_id: str) -> bool:
            self.checked.append(snapshot_id)
            # The base id ends in the UTC 'Z' suffix; collision candidates end in '_<n>'.
            return snapshot_id.endswith("Z")

    stub = _CountingStore()
    mgr._snapshot_store = stub  # type: ignore[assignment]
    snapshot_id = mgr._new_snapshot_id()
    assert snapshot_id.endswith("_2")
    assert stub.checked[0].endswith("Z")  # probed the base first
    assert stub.checked[1] == snapshot_id  # then the first suffixed candidate


def test_is_alive_true_when_idle() -> None:
    assert ServiceLifecycleManager(ReferenceLinearModel()).is_alive() is True


def test_is_alive_true_when_active_without_monitor_update() -> None:
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr.state_machine.handle_command(LifecycleCommand.START)  # active, monitor never ticked
    assert mgr.is_alive() is True


def test_is_alive_reflects_monitor_freshness_when_active() -> None:
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr.state_machine.handle_command(LifecycleCommand.START)
    mgr.monitor.on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 1.0}}, 0))
    assert mgr.is_alive() is True
    # A zero staleness window makes any elapsed time count as stale.
    assert mgr.is_alive(stale_after_seconds=0.0) is False


# --------------------------------------------------------------------------------------
# manager.py -- frame-sink error swallowing (best-effort transport)
# --------------------------------------------------------------------------------------


def test_frame_sink_receives_live_frames_during_run() -> None:
    frames: list[dict[str, Any]] = []
    mgr = ServiceLifecycleManager(ReferenceLinearModel(), frame_sink=frames.append)
    ds = tiny_regression_2d()
    mgr.start_training(ds.X, ds.y)
    assert mgr.join(timeout=5.0)
    assert any(frame["type"] == "metrics" for frame in frames)


def test_emit_live_frame_swallows_sink_errors() -> None:
    def boom(_frame: dict[str, Any]) -> None:
        raise RuntimeError("sink down")

    mgr = ServiceLifecycleManager(ReferenceLinearModel(), frame_sink=boom)
    mgr._emit_live_frame("epoch_end")  # metrics-frame path
    mgr._emit_live_frame("other")  # state-frame path


def test_emit_live_frame_noop_without_sink() -> None:
    ServiceLifecycleManager(ReferenceLinearModel())._emit_live_frame("epoch_end")


def test_emit_replay_frame_swallows_sink_errors() -> None:
    def boom(_frame: dict[str, Any]) -> None:
        raise RuntimeError("sink down")

    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr.set_frame_sink(boom)
    mgr._emit_replay_frame({"time_index": 0, "metrics": {"mse": 0.1}})


def test_emit_replay_frame_noop_without_sink() -> None:
    ServiceLifecycleManager(ReferenceLinearModel())._emit_replay_frame({"time_index": 0})


# --------------------------------------------------------------------------------------
# manager.py -- FAILED settlement + phase-change reflection
# --------------------------------------------------------------------------------------


def test_fit_exception_settles_failed_and_reports_error() -> None:
    mgr = ServiceLifecycleManager(_RaisingFitModel())
    X, y = _zeros()
    mgr.start_training(X, y)
    assert mgr.join(timeout=5.0)
    status = mgr.get_status()
    assert status["state_machine"]["status"] == "FAILED"
    assert "error" in status and "boom" in status["error"]
    assert status["training_active"] is False


def test_handle_event_phase_change_reflects_onto_state_machine() -> None:
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr.state_machine.handle_command(LifecycleCommand.START)  # STARTED so set_phase applies
    mgr._handle_event(TrainingEvent("phase_change", {"phase": "candidate"}, 0))
    assert mgr.state_machine.phase == "candidate"


def test_handle_event_stop_after_pause_raises_interrupted() -> None:
    """Cooperative stop observed at the *second* stop-check, after the pause wait releases."""
    mgr = ServiceLifecycleManager(ReferenceLinearModel())
    mgr._seq = 0
    mgr._stop_event.clear()
    real_pause = mgr._pause_event
    real_pause.clear()  # paused: the sink will block in pause_event.wait()

    at_wait = threading.Event()

    class _GatedPause:
        def wait(self, timeout: float | None = None) -> bool:
            at_wait.set()  # signal we passed the first stop-check and are entering the wait
            return real_pause.wait(timeout)

        def is_set(self) -> bool:
            return real_pause.is_set()

        def set(self) -> None:
            real_pause.set()

        def clear(self) -> None:
            real_pause.clear()

    mgr._pause_event = _GatedPause()  # type: ignore[assignment]
    outcome: dict[str, str] = {}

    def worker() -> None:
        try:
            mgr._handle_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 1.0}}, 0))
            outcome["result"] = "returned"
        except TrainingInterrupted:
            outcome["result"] = "interrupted"

    thread = threading.Thread(target=worker, name="gated-handle-event")
    thread.start()
    assert at_wait.wait(timeout=2.0)  # worker is parked inside the pause wait
    mgr._stop_event.set()
    real_pause.set()  # release the wait -> the second stop-check fires
    thread.join(timeout=2.0)
    assert thread.is_alive() is False
    assert outcome["result"] == "interrupted"


# --------------------------------------------------------------------------------------
# manager.py -- active-run guard clauses (deterministic threaded drive)
# --------------------------------------------------------------------------------------


def test_start_and_attach_rejected_while_active() -> None:
    model = _SteppableModel(n_epochs=5)
    mgr = ServiceLifecycleManager(model)
    X, y = _zeros()
    mgr.start_training(X, y)
    _wait_at_gate(model)
    try:
        assert mgr.get_status()["state_machine"]["status"] == "STARTED"
        with pytest.raises(RuntimeError):
            mgr.start_training(X, y)  # already in progress
        with pytest.raises(RuntimeError):
            mgr.attach_model(ReferenceLinearModel())  # cannot attach while active
    finally:
        _drain(mgr, model)
    assert mgr.get_status()["state_machine"]["status"] == "STOPPED"


def test_load_snapshot_rejected_while_active(tmp_path) -> None:
    model = _SteppableModel(n_epochs=5)
    mgr = ServiceLifecycleManager(model, serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    X, y = _zeros()
    mgr.start_training(X, y)
    _wait_at_gate(model)
    try:
        with pytest.raises(RuntimeError):
            mgr.load_snapshot("anything")  # snapshots enabled, but a run is active
    finally:
        _drain(mgr, model)


# --------------------------------------------------------------------------------------
# manager.py -- stop_replay + replay frame push (snapshot-backed)
# --------------------------------------------------------------------------------------


@pytest.fixture
def snap_manager(tmp_path):
    ds = tiny_regression_2d()
    mgr = ServiceLifecycleManager(ReferenceLinearModel(), serializer=ReferenceLinearSerializer(), snapshot_dir=tmp_path)
    mgr.start_training(ds.X, ds.y)
    assert mgr.join(timeout=5.0)
    snapshot_id = mgr.save_snapshot("for-replay")["id"]
    yield mgr, snapshot_id
    mgr.shutdown()


def test_stop_replay_from_replaying_resets(snap_manager) -> None:
    mgr, snapshot_id = snap_manager
    mgr.start_replay(snapshot_id)
    assert mgr.get_replay_state() is not None
    status = mgr.stop_replay()
    assert status["state_machine"]["status"] == "STOPPED"
    assert mgr.get_replay_state() is None


def test_stop_replay_without_active_replay_is_safe(snap_manager) -> None:
    mgr, _snapshot_id = snap_manager
    status = mgr.stop_replay()  # no session, not REPLAYING -> idempotent no-op
    assert "state_machine" in status
    assert mgr.get_replay_state() is None


def test_start_replay_pushes_initial_frame_to_sink(snap_manager) -> None:
    mgr, snapshot_id = snap_manager
    frames: list[dict[str, Any]] = []
    mgr.set_frame_sink(frames.append)
    mgr.start_replay(snapshot_id)  # start() emits frame 0 synchronously via the sink adapter
    try:
        assert any(frame.get("type") == "metrics" for frame in frames)
    finally:
        mgr.stop_replay()
