"""Optional cross-validation / fold-executor layer (model-agnostic; numpy).

The orchestration tier *above* a single model: loop folds -> fit a fresh model per fold ->
score held-out -> aggregate. It is built purely on the :class:`~juniper_model_core.TrainableModel`
contract, so it drives *any* conforming model (the conformance kit's ``ReferenceLinearModel``, the
recurrence ``LMURegressor``, a future cascor adapter) without knowing the concrete type.

Two contract gaps shape the API (see the design note):

* there is no ``reset()`` / ``clone()`` on the contract, so the executor takes a **model factory**
  ``Callable[[int], TrainableModel]`` (fold index -> fresh model), never a model instance;
* there is no held-out ``score()`` on the contract, so scoring is computed **here** from
  ``predict(eval.X)`` vs ``eval.y`` (decision D-CV-3, kept external to keep the ABC lean).

Install the ``[crossval]`` extra (numpy). This subpackage is **not** re-exported from the
top-level ``juniper_model_core`` package, preserving the dependency-free core import
(``tests/test_dependency_free_import.py``); import it explicitly::

    from juniper_model_core.crossval import cross_validate, walk_forward_folds
"""

from __future__ import annotations

from juniper_model_core.crossval.executor import CrossValResult, FoldResult, cross_validate
from juniper_model_core.crossval.metrics import regression_metrics, score
from juniper_model_core.crossval.splits import Fold, walk_forward_folds

__all__ = [
    "Fold",
    "walk_forward_folds",
    "FoldResult",
    "CrossValResult",
    "cross_validate",
    "regression_metrics",
    "score",
]
