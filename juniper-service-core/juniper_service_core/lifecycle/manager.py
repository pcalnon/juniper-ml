"""Model-agnostic training-lifecycle orchestrator (WS-2 / OUT-11 T2).

:class:`ServiceLifecycleManager` is the generic base extracted from cascor's 3k-line,
cascade-bound ``api/lifecycle/manager.py`` -- the "extract base, keep cascor subclass"
refactor. It is the **substantive body** that model-core's
:class:`juniper_model_core.lifecycle.TrainingLifecycleBase` deferred to WS-2: it drives an
injected :class:`~juniper_model_core.interfaces.TrainableModel` through ``fit`` on a
background thread, tracks status via a :class:`~juniper_service_core.lifecycle.state_machine.LifecycleStateMachine`,
folds the model's :class:`~juniper_model_core.events.TrainingEvent`s into a
:class:`~juniper_service_core.lifecycle.monitor.LifecycleMonitor`, and exposes the JSON-ready
query surface the generic HTTP routes call (``get_status`` / ``get_metrics`` /
``get_metrics_history`` / ``get_dataset`` / ``get_topology`` / ``get_network_info``).

What stays in a service subclass (cascor): model construction (``create_network`` building a
``CascadeCorrelationNetwork``), snapshot/replay persistence, live dataset swap, manual
weight/unit surgery, decision-boundary rendering, and the worker coordinator. The base owns
*only* the model-agnostic orchestration; it force-generalizes nothing cascade-specific
(RK-4 guardrail).

**Cooperative interrupt.** ``fit`` is a black box, so pause/stop are honored at event
boundaries: the per-event sink (which the model calls as it emits ``TrainingEvent``s) blocks
while paused and raises :class:`TrainingInterrupted` on stop. A model that emits events
during ``fit`` (the model-core contract encourages exactly this) is therefore interruptible
with no model-specific hook.
"""

from __future__ import annotations

import datetime
import logging
import os
import threading
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from juniper_model_core.lifecycle import TrainingLifecycleBase

from juniper_service_core.lifecycle.monitor import DEFAULT_HISTORY_LIMIT, LifecycleMonitor
from juniper_service_core.lifecycle.replay import ReplaySession
from juniper_service_core.lifecycle.snapshots import SnapshotStore
from juniper_service_core.lifecycle.state_machine import LifecycleCommand, LifecycleStateMachine

if TYPE_CHECKING:
    import numpy as np

    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult
    from juniper_model_core.serialization import ModelSerializer

__all__ = ["ServiceLifecycleManager", "TrainingInterrupted"]

logger = logging.getLogger("juniper_service_core.lifecycle.manager")


class TrainingInterrupted(Exception):
    """Raised inside the event sink to unwind ``model.fit`` on a stop/reset request.

    Internal control-flow signal -- never surfaced to an HTTP caller; the orchestrator
    catches it and settles the state machine in ``STOPPED``.
    """


class ServiceLifecycleManager(TrainingLifecycleBase):
    """Generic background-threaded training orchestrator for a model-core model.

    Construct with a model (or attach one later via :meth:`attach_model`), then drive it with
    :meth:`start_training` / :meth:`stop_training` / :meth:`pause_training` /
    :meth:`resume_training` / :meth:`reset`. HTTP routes read :meth:`get_status` and friends.

    A service that builds its own model from request parameters (cascor's ``create_network``)
    subclasses this and adds that surface; the generic base requires only that a model
    implementing the :class:`~juniper_model_core.interfaces.TrainableModel` contract be
    attached before training starts.
    """

    def __init__(
        self,
        model: TrainableModel | None = None,
        *,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
        serializer: ModelSerializer | None = None,
        snapshot_dir: str | os.PathLike[str] | None = None,
    ) -> None:
        super().__init__(model, on_event=None)
        self.state_machine = LifecycleStateMachine()
        self.monitor = LifecycleMonitor(history_limit=history_limit)
        # Snapshots are enabled iff a model serializer is injected. The dir defaults to
        # JUNIPER_SERVICE_SNAPSHOT_DIR (else ``./snapshots``); cascor/etc. pass an explicit path.
        self._snapshot_store: SnapshotStore | None = None
        if serializer is not None:
            resolved_dir = snapshot_dir if snapshot_dir is not None else os.environ.get("JUNIPER_SERVICE_SNAPSHOT_DIR", "snapshots")
            self._snapshot_store = SnapshotStore(serializer, resolved_dir)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # set == "not paused"
        self._thread: threading.Thread | None = None
        self._seq = 0
        self._train_x: np.ndarray | None = None
        self._train_y: np.ndarray | None = None
        self._val_x: np.ndarray | None = None
        self._val_y: np.ndarray | None = None
        self._dataset_name: str | None = None
        self._params: dict[str, Any] = {}
        self._last_result: TrainResult | None = None
        self._last_error: str | None = None
        self._replay_session: ReplaySession | None = None

    # -- model attachment ------------------------------------------------------------------

    def attach_model(self, model: TrainableModel) -> None:
        """Attach (or replace) the model this manager drives. Rejected while a run is active."""
        with self._lock:
            if self.state_machine.is_active():
                raise RuntimeError("Cannot attach a model while training is active")
            self.model = model
            self._last_result = None
            self._last_error = None
            self.monitor.reset()
            self.monitor.set_run_context(model_type=self._safe_model_type())

    def has_model(self) -> bool:
        """True once a model is attached."""
        return self.model is not None

    # -- training control ------------------------------------------------------------------

    def start_training(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        *,
        dataset_name: str | None = None,
        **fit_kwargs: Any,
    ) -> dict[str, Any]:
        """Begin a training run on a background thread.

        ``fit_kwargs`` is forwarded verbatim to ``model.fit`` (e.g. sequence auxiliaries
        ``dt`` / ``readout_mask``). Returns the post-transition status dict. Raises
        ``RuntimeError`` if no model is attached or a run is already active.
        """
        with self._lock:
            if self.model is None:
                raise RuntimeError("No model attached")
            if self.state_machine.is_active():
                raise RuntimeError("Training already in progress")
            self._train_x, self._train_y = X, y
            self._val_x, self._val_y = X_val, y_val
            self._dataset_name = dataset_name
            self._stop_event.clear()
            self._pause_event.set()
            self.monitor.set_run_context(
                status="running",
                phase="running",
                model_type=self._safe_model_type(),
                dataset_name=dataset_name,
                max_epochs=fit_kwargs.get("max_epochs"),
            )
            if not self.state_machine.handle_command(LifecycleCommand.START):  # pragma: no cover - guarded above
                raise RuntimeError("Cannot start training in the current state")
            self._last_error = None
            self._thread = threading.Thread(
                target=self._train_thread_target,
                args=(X, y, X_val, y_val, dict(fit_kwargs)),
                name="service-lifecycle-train",
                daemon=True,
            )
            self._thread.start()
            return self._status_dict()

    def stop_training(self) -> dict[str, Any]:
        """Request a stop (idempotent). Signals the running thread to unwind cooperatively."""
        with self._lock:
            self._stop_event.set()
            self._pause_event.set()  # release a paused run so it can observe the stop
            self.state_machine.handle_command(LifecycleCommand.STOP)
            self.monitor.set_run_context(status="stopped", phase="idle")
            return self._status_dict()

    def pause_training(self) -> dict[str, Any]:
        """Pause an active run at its next event boundary. Raises ``RuntimeError`` if not started."""
        with self._lock:
            if not self.state_machine.is_started():
                raise RuntimeError("Training is not running")
            self.state_machine.handle_command(LifecycleCommand.PAUSE)
            self._pause_event.clear()
            self.monitor.set_run_context(status="paused", phase="paused")
            return self._status_dict()

    def resume_training(self) -> dict[str, Any]:
        """Resume a paused run. Raises ``RuntimeError`` if not paused."""
        with self._lock:
            if not self.state_machine.is_paused():
                raise RuntimeError("Training is not paused")
            self.state_machine.handle_command(LifecycleCommand.RESUME)
            self._pause_event.set()
            self.monitor.set_run_context(status="running", phase="running")
            return self._status_dict()

    def reset(self) -> dict[str, Any]:
        """Stop any run and clear all training state back to the idle baseline."""
        with self._lock:
            self._stop_event.set()
            self._pause_event.set()
            self._teardown_replay()
            self.state_machine.handle_command(LifecycleCommand.RESET)
            self._train_x = self._train_y = self._val_x = self._val_y = None
            self._dataset_name = None
            self._last_result = None
            self._last_error = None
            self.monitor.reset()
            self.monitor.set_run_context(model_type=self._safe_model_type())
            return self._status_dict()

    def join(self, timeout: float | None = None) -> bool:
        """Block until the current training thread finishes. Returns ``True`` if it is idle.

        Test/shutdown convenience -- lets callers wait for a run deterministically instead of
        polling :meth:`get_status` with sleeps.
        """
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def shutdown(self) -> None:
        """Signal any run / replay to stop and join its thread (best-effort)."""
        with self._lock:
            self._stop_event.set()
            self._pause_event.set()
            self._teardown_replay()
        self.join(timeout=5.0)

    # -- the synchronous body (model-core TrainingLifecycleBase.run) -----------------------

    def run(self, X: np.ndarray, y: np.ndarray, *, X_val: np.ndarray | None = None, y_val: np.ndarray | None = None, **fit_kwargs: Any) -> TrainResult:
        """Drive ``model.fit`` to completion on the *calling* thread, routing events to the
        monitor with a run-scoped monotonic ``seq``.

        This is the reusable synchronous primitive (model-core's deferred WS-2 body);
        :meth:`start_training` runs it on a background thread and wraps it with the
        state-machine lifecycle. ``fit`` may raise :class:`TrainingInterrupted` via the sink
        when a stop is requested mid-run.
        """
        if self.model is None:
            raise RuntimeError("No model attached")
        self._seq = 0
        return self.model.fit(X, y, X_val=X_val, y_val=y_val, on_event=self._handle_event, **fit_kwargs)

    def _train_thread_target(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray | None, y_val: np.ndarray | None, fit_kwargs: dict[str, Any]) -> None:
        """Background thread entry: run the body, then settle the state machine."""
        try:
            result = self.run(X, y, X_val=X_val, y_val=y_val, **fit_kwargs)
        except TrainingInterrupted:
            logger.info("Training interrupted by stop request")
            with self._lock:
                self.monitor.set_run_context(status="stopped", phase="idle")
        except Exception as exc:  # noqa: BLE001 - any model failure must settle the FSM in FAILED
            logger.exception("Training failed")
            with self._lock:
                self.state_machine.mark_failed(str(exc))
                self._last_error = str(exc)
                self.monitor.set_run_context(status="failed", phase="idle")
        else:
            with self._lock:
                # A stop racing with normal completion already moved the FSM to STOPPED;
                # don't override it with COMPLETED.
                if not self._stop_event.is_set():
                    self.state_machine.mark_completed()
                    self.monitor.set_run_context(status="completed", phase="idle")
                self._last_result = result

    def _handle_event(self, event: TrainingEvent) -> None:
        """Per-event sink passed to ``model.fit`` (runs on the training thread).

        Order: observe stop/pause, stamp a run-scoped ``seq``, fold into the monitor, then
        reflect a ``phase_change`` onto the state machine. The pause wait is held *outside*
        the manager lock so a concurrent :meth:`stop_training` can release it.
        """
        if self._stop_event.is_set():
            raise TrainingInterrupted
        self._pause_event.wait()
        if self._stop_event.is_set():
            raise TrainingInterrupted
        stamped = replace(event, seq=self._seq)
        self._seq += 1
        self.monitor.on_event(stamped)
        if stamped.type == "phase_change":
            phase = stamped.payload.get("phase")
            if isinstance(phase, str):
                with self._lock:
                    self.state_machine.set_phase(phase)

    # -- query surface (read by HTTP routes) -----------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """The full lifecycle status (drives ``/training/status``)."""
        with self._lock:
            return self._status_dict()

    def get_metrics(self) -> dict[str, Any]:
        """The current metric snapshot (drives ``/metrics``)."""
        return self.monitor.get_metrics()

    def get_metrics_history(self, count: int | None = None) -> list[dict[str, Any]]:
        """The retained per-epoch metric history (drives ``/metrics/history``)."""
        return self.monitor.get_history(count)

    def get_dataset(self) -> dict[str, Any]:
        """Dataset metadata (shapes / counts / name) -- drives ``/dataset``."""
        with self._lock:
            if self._train_x is None:
                return {"has_data": False}
            return {
                "has_data": True,
                "name": self._dataset_name,
                "n_train": int(self._train_x.shape[0]),
                "n_val": int(self._val_x.shape[0]) if self._val_x is not None else 0,
                "input_shape": list(self._train_x.shape[1:]),
                "output_shape": list(self._train_y.shape[1:]) if self._train_y is not None else [],
            }

    def get_dataset_data(self) -> dict[str, Any] | None:
        """The dataset arrays as nested lists for visualization -- drives ``/dataset/data``."""
        with self._lock:
            if self._train_x is None or self._train_y is None:
                return None
            data: dict[str, Any] = {
                "train_x": self._train_x.tolist(),
                "train_y": self._train_y.tolist(),
            }
            if self._val_x is not None and self._val_y is not None:
                data["val_x"] = self._val_x.tolist()
                data["val_y"] = self._val_y.tolist()
            return data

    def get_network_info(self) -> dict[str, Any]:
        """Model-agnostic model info (drives ``GET /network``). Empty dict when no model."""
        model = self.model
        if model is None:
            return {}
        info: dict[str, Any] = {
            "model_type": self._safe_model_type(),
            "task_type": getattr(model, "task_type", None),
            "input_shape": list(getattr(model, "input_shape", ()) or ()),
            "output_shape": list(getattr(model, "output_shape", ()) or ()),
        }
        n_units = getattr(model, "n_units", None)
        if n_units is not None:
            info["n_units"] = int(n_units)
        return info

    def get_topology(self) -> dict[str, Any] | None:
        """The model's model-agnostic topology (drives ``GET /network/topology``).

        Delegates straight to ``model.describe_topology()`` -- the model-core seam the
        front-end renders without knowing the concrete model type.
        """
        model = self.model
        if model is None:
            return None
        return dict(model.describe_topology())

    def get_training_params(self) -> dict[str, Any]:
        """The current generic training-parameter store (drives ``GET /training/params``)."""
        with self._lock:
            return dict(self._params)

    def update_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Merge runtime parameter updates (PATCH semantics) and return the new store.

        The generic base stores parameters opaquely; a service subclass overrides this to
        validate against its model (e.g. cascor's candidate-pool rules) and to apply live.
        """
        with self._lock:
            self._params.update(params)
            return dict(self._params)

    # -- snapshots (OUT-11 T2 step 1b; enabled when a ModelSerializer is injected) ----------

    def snapshots_enabled(self) -> bool:
        """True if this manager was built with a model serializer (snapshots are configured)."""
        return self._snapshot_store is not None

    def save_snapshot(self, description: str = "") -> dict[str, Any]:
        """Persist the current model + lifecycle state as a new snapshot; return its metadata.

        Raises ``RuntimeError`` if snapshots are not configured or no model is attached.
        """
        with self._lock:
            store = self._require_snapshots()
            if self.model is None:
                raise RuntimeError("No model attached")
            sidecar = {
                "description": description,
                "status": self.state_machine.status.name,
                "model_type": self._safe_model_type(),
                "dataset_name": self._dataset_name,
                "params": dict(self._params),
                "state": self.monitor.get_state(),
                "history": self.monitor.get_history(),
            }
            return store.save(self.model, self._new_snapshot_id(), sidecar)

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List all stored snapshots' metadata (drives ``GET /snapshots``)."""
        return self._require_snapshots().list()

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """Return one snapshot's metadata, or ``None`` if absent (drives ``GET /snapshots/{id}``)."""
        return self._require_snapshots().get(snapshot_id)

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        """Restore a snapshot for **inspection** -> ``INVESTIGATING`` (training rejected until a
        retrain/resume promotes it). Returns the post-load status. Raises
        :class:`~juniper_service_core.lifecycle.snapshots.SnapshotNotFoundError` if absent.
        """
        with self._lock:
            sidecar = self._load_snapshot_model(snapshot_id)
            self.monitor.restore(sidecar.get("history", []), status="investigating", phase="idle")
            self.state_machine.mark_investigating()
            return self._status_dict()

    def restore_for_retrain(self, snapshot_id: str) -> dict[str, Any]:
        """Restore a snapshot's model but **clear** its history -> ``STOPPED`` (a fresh run from
        this network). Returns the post-load status."""
        with self._lock:
            self._load_snapshot_model(snapshot_id)
            self.monitor.reset()
            self.monitor.set_run_context(model_type=self._safe_model_type())
            self.state_machine.handle_command(LifecycleCommand.RESET)
            return self._status_dict()

    def resume_from_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        """Restore a snapshot's model **and** history -> ``RESUME_READY`` (the next ``start``
        continues). Returns the post-load status with ``resume_point_epoch``."""
        with self._lock:
            sidecar = self._load_snapshot_model(snapshot_id)
            history = sidecar.get("history", [])
            self.monitor.restore(history, status="resume_ready", phase="idle")
            self.state_machine.mark_resume_ready()
            result = self._status_dict()
            result["resume_point_epoch"] = len(history)
            return result

    def _require_snapshots(self) -> SnapshotStore:
        if self._snapshot_store is None:
            raise RuntimeError("Snapshots are not configured (no model serializer was provided)")
        return self._snapshot_store

    def _new_snapshot_id(self) -> str:
        """A unique, sortable, UTC-timestamp snapshot id (collision-suffixed ``_2`` … ``_1000``)."""
        base = "snapshot_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        store = self._snapshot_store
        if store is None or not store.exists(base):
            return base
        for suffix in range(2, 1001):
            candidate = f"{base}_{suffix}"
            if not store.exists(candidate):
                return candidate
        return base  # pragma: no cover - 1000 same-second snapshots is not a real scenario

    def _load_snapshot_model(self, snapshot_id: str) -> dict[str, Any]:
        """Shared restore core: reject-if-active, deserialize model + sidecar, attach. Caller holds the lock."""
        store = self._require_snapshots()
        if self.state_machine.is_active():
            raise RuntimeError("Cannot load a snapshot while training is active")
        model, sidecar = store.load(snapshot_id)  # raises SnapshotNotFoundError if absent
        self.model = model
        self._last_result = None
        self._last_error = None
        self.monitor.set_run_context(model_type=self._safe_model_type())
        return sidecar

    # -- replay (OUT-11 T2 step 1c; plays a snapshot's stored history back as timed frames) --

    def start_replay(self, snapshot_id: str) -> dict[str, Any]:
        """Load a snapshot and begin replaying its metric history -> ``REPLAYING`` (paused at
        frame 0). Returns the status with a ``replay`` block. Raises ``SnapshotNotFoundError`` /
        ``RuntimeError`` (training active)."""
        with self._lock:
            sidecar = self._load_snapshot_model(snapshot_id)
            self._teardown_replay()
            self._replay_session = ReplaySession(snapshot_id, sidecar.get("history", []))
            self.state_machine.mark_replaying()
            self.monitor.set_run_context(status="replaying", phase="replay")
            started = self._replay_session.start()
            result = self._status_dict()
            result["replay"] = started
            return result

    def replay_control(self, action: str, **params: Any) -> dict[str, Any]:
        """Control the active replay (play/pause/seek/speed/range/stop/status). ``stop`` exits to
        ``STOPPED``. Raises ``RuntimeError`` if no replay is active, ``ValueError`` on a bad action."""
        with self._lock:
            if self._replay_session is None:
                raise RuntimeError("No replay session is active")
            replay_state = self._replay_session.control(action, **params)
            if action == "stop":
                self._teardown_replay()
                self.state_machine.handle_command(LifecycleCommand.RESET)
                self.monitor.set_run_context(status="stopped", phase="idle")
            result = self._status_dict()
            result["replay"] = replay_state
            return result

    def stop_replay(self) -> dict[str, Any]:
        """Stop the active replay -> ``STOPPED`` (idempotent)."""
        with self._lock:
            self._teardown_replay()
            if self.state_machine.is_replaying():
                self.state_machine.handle_command(LifecycleCommand.RESET)
            self.monitor.set_run_context(status="stopped", phase="idle")
            return self._status_dict()

    def get_replay_state(self) -> dict[str, Any] | None:
        """The active replay session's state, or ``None`` if no replay is active."""
        session = self._replay_session
        return session.state() if session is not None else None

    def _teardown_replay(self) -> None:
        """Stop and drop the replay session, if any. Caller holds the lock."""
        if self._replay_session is not None:
            self._replay_session.stop()
            self._replay_session = None

    def is_alive(self, stale_after_seconds: float = 30.0) -> bool:
        """Basic liveness: an idle service is alive; an active run is alive while its monitor
        ticked within ``stale_after_seconds``.

        The richer heartbeat daemon (cascor METRICS-MON) is intentionally out of scope for
        this generic base; this is the minimal model-agnostic check the readiness route needs.
        """
        if not self.state_machine.is_active():
            return True
        updated = self.monitor.get_state().get("updated_at")
        if updated is None:
            return True
        return (time.time() - float(updated)) < stale_after_seconds

    # -- internals -------------------------------------------------------------------------

    def _status_dict(self) -> dict[str, Any]:
        """Assemble the status payload. Caller must hold ``self._lock``."""
        status: dict[str, Any] = {
            "state_machine": self.state_machine.get_state_summary(),
            "monitor": self.monitor.get_state(),
            "training_active": self.state_machine.is_active(),
            "has_model": self.has_model(),
        }
        if self._last_error is not None:
            status["error"] = self._last_error
        return status

    def _safe_model_type(self) -> str | None:
        """Best-effort model-type label for monitor/status, robust to an unfitted model."""
        model = self.model
        if model is None:
            return None
        try:
            return str(model.describe_topology().get("model_type"))
        except Exception:  # noqa: BLE001 - topology may be unavailable pre-fit; label is cosmetic
            return type(model).__name__
