"""Canonical regression-metric math, shared by the conformance kit and the crossval layer.

Single source of truth (decision D1 / OPT-A A2 in
``notes/JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md``): both the held-out scorer
(:mod:`juniper_model_core.crossval.metrics`) and the conformance kit's reference model
(:mod:`juniper_model_core.conformance.reference`) compute regression metrics from *this* one
implementation, so the two can never drift.

This module imports ``numpy`` at runtime, so -- like :mod:`juniper_model_core.conformance` and
:mod:`juniper_model_core.crossval` -- it MUST NOT be imported by the top-level package
``__init__``. The dependency-free contract (``import juniper_model_core`` pulls no third-party
runtime dependency) is guarded by ``tests/test_dependency_free_import.py``.
"""

from __future__ import annotations

import numpy as np

__all__ = ["regression_metrics"]


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Return ``{'mse', 'rmse', 'mae', 'r2', 'loss'}`` (``loss == mse``).

    Keys are a subset of :data:`juniper_model_core.validation.REGRESSION_METRIC_KEYS`. ``r2`` is
    the coefficient of determination against the total sum of squares about the per-column mean;
    when that total is zero (a constant target) ``r2`` is defined as ``0.0`` rather than dividing
    by zero. Inputs are coerced to ``float64`` and broadcast against each other element-wise.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    err = y_pred - y_true
    mse = float(np.mean(err**2))
    mae = float(np.mean(np.abs(err)))
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y_true - y_true.mean(axis=0)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"mse": mse, "rmse": mse**0.5, "mae": mae, "r2": r2, "loss": mse}
