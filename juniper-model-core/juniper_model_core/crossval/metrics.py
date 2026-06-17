"""Held-out scoring for the cross-validation layer.

Scoring lives *here*, external to the model contract (decision D-CV-3): ``TrainableModel.metrics()``
reports the model's own train-time metrics, so the executor computes evaluation metrics itself from
``predict(eval.X)`` vs ``eval.y``. The regression math is the shared canonical implementation in
:mod:`juniper_model_core._metrics` (one source of truth with the conformance reference model).

v1 is regression-only (OPT-G); :func:`score` raises ``NotImplementedError`` for classification so
that branch is a purely additive drop-in later (no change to the regression path).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from juniper_model_core._metrics import regression_metrics

if TYPE_CHECKING:
    import numpy as np

    from juniper_model_core.interfaces import TaskType

__all__ = ["regression_metrics", "score"]


def score(task_type: TaskType, y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute held-out metrics for ``task_type``.

    ``regression`` -> :func:`regression_metrics`. ``classification`` -> ``NotImplementedError``
    (deferred to a later minor; OPT-G). Any other value -> ``ValueError``.
    """
    if task_type == "regression":
        return regression_metrics(y_true, y_pred)
    if task_type == "classification":
        raise NotImplementedError("crossval held-out scoring is regression-only in v1; classification is deferred (OPT-G / D-CV-3)")
    raise ValueError(f"unknown task_type: {task_type!r}")
