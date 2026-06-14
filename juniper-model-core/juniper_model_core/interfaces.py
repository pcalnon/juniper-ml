"""Core model-contract interfaces.

These ABCs define the *minimal* contract the Juniper service layer needs from any learning
model. The surface is deliberately shaped by **two** real implementers -- cascor's
``CascadeCorrelationNetwork`` (a growable 2-D classifier) and the recurrence LMU (a
fixed-order time-series regressor) -- so the abstraction reflects plurality, not cascor
alone (RK-4).

Ratified design stance (2026-06-14, decisions D1-D10):

* **ABCs, not Protocols** (D1) -- nominal typing gives the conformance kit a reliable
  ``isinstance`` check and fits the "subclass + inject" mechanism.
* **numpy at the boundary** (D2) -- arrays cross the interface as ``numpy.ndarray``;
  framework-native tensors stay inside each model. numpy appears here only in type
  annotations, so importing this module pulls no third-party runtime dependency.
* **Auxiliary sequence arrays via keyword** (D3) -- 3-D sequence models read ``dt`` /
  ``readout_mask`` / ``seq_lengths`` from ``**kw``; 2-D models ignore them. This keeps the
  contract additive and 2-D-safe, mirroring the additive 3-D NPZ data contract.
* **Interface-only ABCs** (C1) -- these classes declare the contract and nothing else.
  Shared *behavior* lives in :mod:`juniper_model_core.validation` as inspectable free
  functions, never as inherited base-class machinery.

``GrowableModel`` is intentionally minimal and provisional: cascor is its only current
implementer, so its surface stays loose until RCC becomes the second implementer in WS-4.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import numpy as np

    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.topology import Topology

__all__ = [
    "TaskType",
    "TrainResult",
    "GrowthOutcome",
    "TrainableModel",
    "GrowableModel",
]

#: What kind of learning problem a model solves; drives how generic consumers interpret
#: :meth:`TrainableModel.predict` and :meth:`TrainableModel.metrics`.
TaskType = Literal["classification", "regression"]


@dataclass(frozen=True, slots=True)
class TrainResult:
    """Summary returned by :meth:`TrainableModel.fit`.

    Deliberately lean: per-step detail belongs in emitted :class:`TrainingEvent`s and
    on-demand metrics belong in :meth:`TrainableModel.metrics`. This is the post-training
    summary the service/lifecycle layer reports.
    """

    final_metrics: dict[str, float]
    n_epochs: int
    history: list[dict[str, float]] | None = None
    stopped_reason: str | None = None


@dataclass(frozen=True, slots=True)
class GrowthOutcome:
    """Result of a single :meth:`GrowableModel.grow_step`."""

    added: bool
    n_units: int
    unit_id: str | None = None
    score: float | None = None


class TrainableModel(ABC):
    """The minimal contract every Juniper model satisfies.

    Implementers set :attr:`task_type` and :attr:`random_seed` (determinism is testable --
    the conformance kit may assert reproducibility). All array arguments and returns are
    ``numpy.ndarray`` with the *sample/batch* axis first; :attr:`input_shape` /
    :attr:`output_shape` describe the per-sample shape, excluding that axis.
    """

    task_type: TaskType
    random_seed: int | None = None

    @abstractmethod
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        *,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        on_event: Callable[[TrainingEvent], None] | None = None,
        **kw: Any,
    ) -> TrainResult:
        """Train on ``X`` / ``y``.

        ``X`` is ``(n_samples, *input_shape)`` -- i.e. ``(n, F)`` for tabular models or
        ``(n, T, F)`` for sequence models. Sequence models read their auxiliary arrays
        (``dt``, ``readout_mask``, ``seq_lengths``) from ``**kw``; tabular models ignore
        them (D3). If ``on_event`` is supplied, the model SHOULD emit :class:`TrainingEvent`s
        through it in a legal order (``training_start`` first, ``training_end`` last) -- the
        single, inspectable progress path, with no monkey-patching (D4).
        """

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return model outputs for ``X``.

        Continuous values for ``regression``; class scores (logits / probabilities) for
        ``classification``. NEVER an ``argmax`` -- collapsing scores to labels is a
        classification-only concern and must not live in the generic contract (RK-6).
        """

    @abstractmethod
    def metrics(self) -> dict[str, float]:
        """Latest scalar metrics.

        Keys must be valid for :attr:`task_type` (see
        :data:`juniper_model_core.validation.REGRESSION_METRIC_KEYS` /
        ``CLASSIFICATION_METRIC_KEYS``). A regression model must never report ``accuracy``.
        """

    @abstractmethod
    def describe_topology(self) -> Topology:
        """Return the model-agnostic node/edge graph the front-end renders without knowing
        the concrete model type (see :mod:`juniper_model_core.topology`)."""

    @property
    @abstractmethod
    def input_shape(self) -> tuple[int, ...]:
        """Per-sample input shape, excluding the batch axis: ``(F,)`` or ``(T, F)``."""

    @property
    @abstractmethod
    def output_shape(self) -> tuple[int, ...]:
        """Per-sample output shape, excluding the batch axis."""


class GrowableModel(TrainableModel, ABC):
    """A :class:`TrainableModel` that constructs its own topology incrementally
    (Cascade-Correlation today; future RCC / Growing-ESN).

    **Provisional surface (RK-4).** cascor is the only current implementer; this contract
    stays deliberately minimal until RCC is the second implementer (WS-4), at which point
    the :meth:`grow_step` signature is revisited against both. We intentionally do *not* bake
    cascor-specific arguments (such as a residual-error tensor) into the signature here.
    """

    @property
    @abstractmethod
    def n_units(self) -> int:
        """Current count of grown units."""

    @abstractmethod
    def grow_step(self, **kw: Any) -> GrowthOutcome:
        """Add (and freeze) at most one unit.

        On success :attr:`n_units` increments and -- when growth happens inside a
        :meth:`fit` that was given an ``on_event`` sink -- a ``unit_added``
        :class:`TrainingEvent` is emitted.
        """

    @abstractmethod
    def freeze(self) -> None:
        """Finalize the topology so further :meth:`grow_step` calls are no-ops."""
