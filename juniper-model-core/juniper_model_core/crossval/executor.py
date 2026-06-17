"""The fold executor: drive the per-fold ``fit -> predict -> score`` step and aggregate.

Model-agnostic and built on the :class:`~juniper_model_core.TrainableModel` contract. Per fold the
executor constructs a *fresh* model from the supplied factory (the contract has no ``reset()`` /
``clone()``), fits it on the training slice, predicts on the held-out eval slice, and scores that
prediction externally (the contract has no held-out ``score()``); per-fold eval metrics are then
aggregated to mean / std.

Auxiliary per-sample arrays (``dt`` / ``target_dt`` / ``readout_mask`` / ``seq_lengths`` for the 3-D
sequence path) are passed through ``aux`` and sliced on axis 0 by the fold indices exactly like
``X`` / ``y``; a guard rejects any ``aux`` entry that is not per-sample (decision D-CV-4 / F-REFINE-4).
Execution is serial by default; an optional ``map_fn`` seam lets a later parallel/distributed worker
(WS-8 / OQ-11) inject a parallel map with no API change (D-CV-5 / OPT-F F2).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

import numpy as np

from juniper_model_core.crossval.metrics import score as _score

if TYPE_CHECKING:
    from juniper_model_core.crossval.splits import Fold
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TaskType, TrainableModel

__all__ = ["FoldResult", "CrossValResult", "cross_validate"]


@dataclass(frozen=True)
class FoldResult:
    """Outcome of one fold."""

    fold: int
    train_metrics: dict[str, float]  # the model's own final_metrics (train-time)
    eval_metrics: dict[str, float]  # held-out score on the eval slice
    n_epochs: int


@dataclass(frozen=True)
class CrossValResult:
    """The full cross-validation result: per-fold detail plus per-metric mean / std aggregates."""

    task_type: TaskType
    folds: list[FoldResult]
    eval_aggregate: dict[str, float]  # per-metric mean across folds
    eval_std: dict[str, float]  # per-metric population std across folds


def _aggregate(per_fold: list[dict[str, float]]) -> tuple[dict[str, float], dict[str, float]]:
    """Per-metric mean and population std across folds (keys taken from the first fold)."""
    if not per_fold:
        return {}, {}
    keys = list(per_fold[0])
    mean: dict[str, float] = {}
    std: dict[str, float] = {}
    for key in keys:
        values = np.asarray([fold_metrics[key] for fold_metrics in per_fold], dtype=np.float64)
        mean[key] = float(values.mean())
        std[key] = float(values.std())
    return mean, std


def cross_validate(
    model_factory: Callable[[int], TrainableModel],
    X: np.ndarray,
    y: np.ndarray,
    folds: Sequence[Fold],
    *,
    aux: Mapping[str, np.ndarray] | None = None,
    on_event: Callable[[int, TrainingEvent], None] | None = None,
    pass_eval_as_val: bool = False,
    map_fn: Callable[[Callable[[Any], Any], Sequence[Any]], Any] = map,
) -> CrossValResult:
    """Run cross-validation: fit a fresh model per fold, score held-out, aggregate.

    Args:
        model_factory: ``fold_index -> fresh TrainableModel``. Called once per fold; never reused.
        X: ordered full feature array, ``(n_samples, *input_shape)``.
        y: ordered full target array, sample axis first.
        folds: the :class:`~juniper_model_core.crossval.splits.Fold` sequence (index-based).
        aux: optional per-sample auxiliary arrays (e.g. ``{"dt": ..., "readout_mask": ...}``); each
            is sliced on axis 0 by the fold indices and forwarded to ``fit`` / ``predict`` as keyword
            arguments. Every entry must have ``shape[0] == n_samples``.
        on_event: optional ``(fold_index, TrainingEvent) -> None`` sink; the per-fold event stream is
            forwarded with the fold index attached (the model's own ``on_event`` takes one argument).
        pass_eval_as_val: when ``True``, the eval slice is also passed as ``X_val`` / ``y_val`` to
            ``fit``; default ``False`` keeps the held-out eval set out of the fit (decision OPT-B B3 --
            avoids eval-fold leakage for models that early-stop on the validation set).
        map_fn: the mapping primitive used to run folds; defaults to the builtin serial ``map``. A
            parallel/distributed worker may inject an order-preserving parallel map with no other API
            change (OPT-F F2). Must return one result per fold (order need not be preserved -- results
            are re-sorted by fold index).

    Returns:
        A :class:`CrossValResult` with per-fold results and per-metric mean / std aggregates.

    Raises:
        ValueError: if ``folds`` is empty, ``X`` / ``y`` sample counts disagree, or any ``aux`` entry
            is not per-sample (``shape[0] != n_samples``).
    """
    X = np.asarray(X)
    y = np.asarray(y)
    n_samples = X.shape[0]
    if y.shape[0] != n_samples:
        raise ValueError(f"X has {n_samples} samples but y has {y.shape[0]}")
    if not folds:
        raise ValueError("folds is empty; nothing to cross-validate")

    aux_arrays: dict[str, np.ndarray] = {}
    for key, value in (aux or {}).items():
        arr = np.asarray(value)
        if arr.shape[0] != n_samples:
            raise ValueError(f"aux[{key!r}] is not per-sample: shape[0]={arr.shape[0]} != n_samples={n_samples}")
        aux_arrays[key] = arr

    def _run_fold(item: tuple[int, Fold]) -> tuple[FoldResult, TaskType]:
        fold_index, fold = item
        train_idx = np.asarray(fold.train_idx)
        eval_idx = np.asarray(fold.eval_idx)
        model = model_factory(fold_index)

        fit_aux = {key: arr[train_idx] for key, arr in aux_arrays.items()}
        eval_aux = {key: arr[eval_idx] for key, arr in aux_arrays.items()}
        sink = partial(on_event, fold_index) if on_event is not None else None

        X_val = X[eval_idx] if pass_eval_as_val else None
        y_val = y[eval_idx] if pass_eval_as_val else None
        train_result = model.fit(X[train_idx], y[train_idx], X_val=X_val, y_val=y_val, on_event=sink, **fit_aux)

        y_pred = model.predict(X[eval_idx], **eval_aux) if eval_aux else model.predict(X[eval_idx])
        eval_metrics = _score(model.task_type, y[eval_idx], np.asarray(y_pred))

        result = FoldResult(
            fold=fold_index,
            train_metrics=dict(train_result.final_metrics),
            eval_metrics=eval_metrics,
            n_epochs=int(train_result.n_epochs),
        )
        return result, model.task_type

    outcomes: list[tuple[FoldResult, TaskType]] = list(map_fn(_run_fold, list(enumerate(folds))))
    outcomes.sort(key=lambda outcome: outcome[0].fold)
    fold_results = [outcome[0] for outcome in outcomes]
    task_type = outcomes[0][1]

    aggregate, std = _aggregate([fold_result.eval_metrics for fold_result in fold_results])
    return CrossValResult(task_type=task_type, folds=fold_results, eval_aggregate=aggregate, eval_std=std)
