"""The model-agnostic training-event vocabulary.

A single, small set of event types that *subsumes* every Juniper model's native events, so
the monitoring / service layer consumes one vocabulary and each model maps its own events
onto it (refactor plan section 2.3). For example cascor maps ``cascade_add -> unit_added``
and ``candidate_progress -> phase_change``; the fixed-order LMU emits only
``training_start`` / ``epoch_end`` / ``training_end``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = ["TrainingEventType", "TrainingEvent", "TRAINING_EVENT_TYPES"]

#: The closed set of generic event types. Each model maps its native events onto these.
TrainingEventType = Literal[
    "training_start",
    "training_end",
    "epoch_end",
    "unit_added",
    "phase_change",
]

#: Tuple form of :data:`TrainingEventType`, for runtime membership checks.
TRAINING_EVENT_TYPES: tuple[str, ...] = (
    "training_start",
    "training_end",
    "epoch_end",
    "unit_added",
    "phase_change",
)


@dataclass(frozen=True, slots=True)
class TrainingEvent:
    """One training-lifecycle event.

    ``payload`` carries event-specific detail; documented conventions:

    * ``epoch_end``    -> ``{"epoch": int, "metrics": dict[str, float]}``
    * ``unit_added``   -> ``{"n_units": int, "unit_id": str, "score": float | None}``
    * ``phase_change`` -> ``{"phase": str, "detail": ...}``

    ``seq`` is a per-run, monotonically non-decreasing counter, used by the conformance kit
    to assert a legal ordering independent of wall-clock timing.
    """

    type: TrainingEventType
    payload: dict[str, Any] = field(default_factory=dict)
    seq: int = 0
