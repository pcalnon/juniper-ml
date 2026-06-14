"""Training-lifecycle seam (declared in WS-3, body designed in WS-2).

:class:`TrainingLifecycleBase` is the de-cascored manager that drives a model through
training while emitting :class:`TrainingEvent`s -- operating *only* against the
:class:`TrainableModel` / :class:`GrowableModel` interfaces, never a concrete model.

**Scope note (decision D8).** This module declares the seam -- the constructor shape and the
abstract :meth:`run` entry point -- so consumers can see exactly where the lifecycle plugs
in. Its substantive body (threading, the training finite-state machine, dataset management,
worker coordination) is intentionally deferred to WS-2, where it is co-designed with
juniper-service-core and the worker-parallelism question (OQ-11). Do not build on internals
until then.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult

__all__ = ["TrainingLifecycleBase"]


class TrainingLifecycleBase(ABC):
    """Drives a :class:`TrainableModel` through its training lifecycle.

    The model and an optional event sink are injected at construction; concrete lifecycles
    (a cascade lifecycle, a recurrence lifecycle) implement :meth:`run`.
    """

    def __init__(self, model: TrainableModel, on_event: Callable[[TrainingEvent], None] | None = None) -> None:
        self.model = model
        self.on_event = on_event

    def emit(self, event: TrainingEvent) -> None:
        """Forward ``event`` to the injected sink, if any.

        The single, inspectable path by which a lifecycle surfaces progress -- no
        monkey-patching of the model (D4).
        """
        if self.on_event is not None:
            self.on_event(event)

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> TrainResult:
        """Execute the training lifecycle. **Body deferred to WS-2** (see module docstring)."""
