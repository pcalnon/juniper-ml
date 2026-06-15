"""Generic training-lifecycle bodies (WS-2).

Concrete :class:`juniper_model_core.lifecycle.TrainingLifecycleBase` implementations that
drive a model-core :class:`~juniper_model_core.interfaces.TrainableModel` through training
and forward the model's :class:`~juniper_model_core.events.TrainingEvent`s to the injected
sink. This is the **synchronous foundation**; the threaded / finite-state-machine /
dataset-hot-swap / worker-coordinated bodies -- and the worker-parallelism question
(OQ-11) -- are deferred follow-ups (model-core ``lifecycle.py`` decision D8).

Importing this module requires ``juniper-model-core`` (the model contract); it is therefore
NOT imported at the top level of :mod:`juniper_service_core` (it is exposed lazily) so the
dependency-free top-level import is preserved.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from juniper_model_core.lifecycle import TrainingLifecycleBase

if TYPE_CHECKING:
    import numpy as np
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult

__all__ = ["TrainingLifecycle", "EventCollector"]


class EventCollector:
    """A simple, ordered event sink -- for tests, inspection, and replay.

    Use it as the ``on_event`` sink of a lifecycle; it records every emitted event in order.
    """

    def __init__(self) -> None:
        self.events: list[TrainingEvent] = []

    def __call__(self, event: TrainingEvent) -> None:
        self.events.append(event)

    @property
    def types(self) -> list[str]:
        """The event ``type`` strings, in emission order."""
        return [event.type for event in self.events]


class TrainingLifecycle(TrainingLifecycleBase):
    """Synchronous lifecycle: drives ``model.fit`` to completion on the calling thread.

    :meth:`run` wires the model's ``on_event`` to this lifecycle's :meth:`emit`, so the
    model's progress events flow to the injected sink. The lifecycle owns **run-level
    ordering**: it stamps a monotonic ``seq`` on each event as it passes through, so the
    sink sees a legally-ordered stream regardless of what ``seq`` the model emits.

    Growth (``unit_added``) for a :class:`~juniper_model_core.interfaces.GrowableModel`
    happens *inside* its ``fit`` (the model-core contract), so this single synchronous body
    drives both fixed-topology and growable models. The threaded / FSM / dataset-hot-swap /
    worker-coordinated bodies are deferred (D8; worker parallelism is OQ-11).
    """

    def __init__(self, model: TrainableModel, on_event: Callable[[TrainingEvent], None] | None = None) -> None:
        super().__init__(model, on_event)
        self._seq = 0

    def emit(self, event: TrainingEvent) -> None:
        """Forward ``event`` to the sink with a monotonic, run-scoped ``seq`` stamped."""
        super().emit(replace(event, seq=self._seq))
        self._seq += 1

    def run(self, X: np.ndarray, y: np.ndarray, **kw: Any) -> TrainResult:
        """Drive the model's full ``fit`` synchronously, routing its events through the
        lifecycle.

        ``**kw`` (e.g. ``X_val`` / ``y_val``, or sequence auxiliaries like ``dt``) is
        forwarded to ``fit``. Do **not** pass ``on_event`` -- the lifecycle owns the sink.
        """
        self._seq = 0
        return self.model.fit(X, y, on_event=self.emit, **kw)
