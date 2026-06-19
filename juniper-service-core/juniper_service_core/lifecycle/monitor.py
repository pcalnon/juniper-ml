"""Model-agnostic training monitor (WS-2 / OUT-11 T2).

The de-cascored core of cascor's ``api/lifecycle/monitor.py``. cascor's monitor predates
:mod:`juniper_model_core` and carries a bespoke callback surface
(``on_epoch_end(epoch, loss, accuracy, learning_rate, hidden_units, …)``) plus cascade-only
state (``best_correlation`` / ``candidates_trained`` / ``all_correlations`` / …). This
generic monitor instead consumes the **one model-agnostic event vocabulary** --
:class:`juniper_model_core.events.TrainingEvent` (``training_start`` / ``epoch_end`` /
``unit_added`` / ``phase_change`` / ``training_end``) -- so it works for any
:class:`~juniper_model_core.interfaces.TrainableModel` without classification assumptions
(``metrics`` is an open dict: ``{mse, rmse, r2}`` for a regressor, ``{loss, accuracy}`` for a
classifier). This is the "extract onto the model-core interfaces" mandate done at the seam.

Thread-safe: the orchestrator drives ``on_event`` from a background training thread while
HTTP routes read the snapshot accessors on the request thread, so all access is guarded by a
single lock. ``TrainingEvent`` is referenced structurally (``.type`` / ``.payload`` / ``.seq``)
and only under :data:`typing.TYPE_CHECKING`, so importing this module pulls no third-party
runtime dependency.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from juniper_model_core.events import TrainingEvent

__all__ = ["LifecycleMonitor", "DEFAULT_HISTORY_LIMIT"]

#: Default cap on the retained per-epoch metric history (a ring buffer; oldest dropped).
DEFAULT_HISTORY_LIMIT = 10_000


class LifecycleMonitor:
    """Thread-safe accumulator of live training state + a bounded metric history.

    Fed one :class:`~juniper_model_core.events.TrainingEvent` at a time via :meth:`on_event`
    (the single, inspectable progress path -- no monkey-patching of the model, model-core
    decision D4). Exposes JSON-ready snapshots for the ``/training/status``, ``/metrics`` and
    ``/metrics/history`` routes.

    Generic fields only -- ``status`` / ``phase`` / ``current_epoch`` / ``latest_metrics`` /
    ``n_units`` / dataset+model metadata. Cascade-specific telemetry (correlation curves,
    candidate-pool progress) is carried as opaque ``TrainingEvent.payload`` entries in the
    history, not promoted to first-class monitor state.
    """

    def __init__(self, history_limit: int = DEFAULT_HISTORY_LIMIT) -> None:
        self._lock = threading.Lock()
        self._history: deque[dict[str, Any]] = deque(maxlen=history_limit)
        self._status: str = "stopped"
        self._phase: str = "idle"
        self._current_epoch: int = 0
        self._latest_metrics: dict[str, float] = {}
        self._n_units: int = 0
        self._model_type: str | None = None
        self._dataset_name: str | None = None
        self._max_epochs: int | None = None
        self._started_at: float | None = None
        self._updated_at: float | None = None

    # -- ingestion -------------------------------------------------------------------------

    def on_event(self, event: TrainingEvent) -> None:
        """Fold one training event into the accumulated state (thread-safe).

        Handles the five model-core event types; an unknown type is recorded in the history
        but otherwise ignored, so a model that emits a richer vocabulary never breaks the
        monitor.
        """
        now = time.time()
        payload = dict(event.payload)
        with self._lock:
            self._updated_at = now
            if event.type == "training_start":
                self._status = "running"
                self._phase = "running"
                self._current_epoch = 0
                self._latest_metrics = {}
                self._n_units = 0
                self._started_at = now
                self._history.clear()
            elif event.type == "epoch_end":
                epoch = int(payload.get("epoch", self._current_epoch))
                metrics = {key: float(value) for key, value in dict(payload.get("metrics", {})).items()}
                self._current_epoch = epoch
                if metrics:
                    self._latest_metrics = metrics
                self._history.append(
                    {
                        "seq": int(event.seq),
                        "epoch": epoch,
                        "metrics": metrics,
                        "n_units": self._n_units,
                        "timestamp": now,
                    }
                )
            elif event.type == "unit_added":
                self._n_units = int(payload.get("n_units", self._n_units + 1))
            elif event.type == "phase_change":
                phase = payload.get("phase")
                if isinstance(phase, str):
                    self._phase = phase
            elif event.type == "training_end":
                metrics = {key: float(value) for key, value in dict(payload.get("metrics", {})).items()}
                if metrics:
                    self._latest_metrics = metrics
                self._status = "ended"

    def set_run_context(
        self,
        *,
        status: str | None = None,
        phase: str | None = None,
        model_type: str | None = None,
        dataset_name: str | None = None,
        max_epochs: int | None = None,
    ) -> None:
        """Set generic run metadata the orchestrator knows but the events don't carry.

        Only non-``None`` arguments are applied (so callers can update one field at a time).
        """
        with self._lock:
            if status is not None:
                self._status = status
            if phase is not None:
                self._phase = phase
            if model_type is not None:
                self._model_type = model_type
            if dataset_name is not None:
                self._dataset_name = dataset_name
            if max_epochs is not None:
                self._max_epochs = max_epochs

    def reset(self) -> None:
        """Clear all accumulated state back to the pre-run baseline."""
        with self._lock:
            self._history.clear()
            self._status = "stopped"
            self._phase = "idle"
            self._current_epoch = 0
            self._latest_metrics = {}
            self._n_units = 0
            self._started_at = None
            self._updated_at = None

    # -- snapshots (read by HTTP routes) ---------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """An atomic snapshot of the live training state (drives ``/training/status``)."""
        with self._lock:
            return {
                "status": self._status,
                "phase": self._phase,
                "current_epoch": self._current_epoch,
                "n_units": self._n_units,
                "model_type": self._model_type,
                "dataset_name": self._dataset_name,
                "max_epochs": self._max_epochs,
                "latest_metrics": dict(self._latest_metrics),
                "started_at": self._started_at,
                "updated_at": self._updated_at,
            }

    def get_metrics(self) -> dict[str, Any]:
        """The current metric snapshot (drives ``/metrics``).

        ``metrics`` is the model's own open dict -- never coerced to a classification shape.
        """
        with self._lock:
            return {
                "epoch": self._current_epoch,
                "n_units": self._n_units,
                "metrics": dict(self._latest_metrics),
                "timestamp": self._updated_at,
            }

    def get_history(self, count: int | None = None) -> list[dict[str, Any]]:
        """The retained per-epoch metric history (drives ``/metrics/history``).

        ``count`` returns the most-recent ``count`` entries; ``None`` returns all retained.
        """
        with self._lock:
            entries = list(self._history)
        if count is not None and count >= 0:
            return entries[-count:]
        return entries
