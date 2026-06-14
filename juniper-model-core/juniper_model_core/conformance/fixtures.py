"""Tiny in-memory datasets for the conformance kit.

Deliberately built around a **regression** problem (both 2-D tabular and 3-D sequence) so the
kit drives a regression model through every route -- the RK-6 guard against classification
assumptions (argmax / accuracy) leaking into "generic" code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = ["ConformanceDataset", "tiny_regression_2d", "tiny_regression_3d"]


@dataclass(frozen=True)
class ConformanceDataset:
    """A small train/val split plus any model-specific ``fit`` keyword arrays.

    ``fit_kwargs`` carries auxiliary sequence arrays (``dt`` / ``readout_mask`` /
    ``seq_lengths``) for 3-D models; it is empty for 2-D models (D3). The kit calls
    ``model.fit(X, y, X_val=X_val, y_val=y_val, on_event=..., **fit_kwargs)``.
    """

    X: np.ndarray
    y: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    task_type: str = "regression"
    fit_kwargs: dict[str, Any] = field(default_factory=dict)


def tiny_regression_2d(seed: int = 0) -> ConformanceDataset:
    """A small tabular regression problem: ``y = X @ W + b`` plus light noise."""
    rng = np.random.default_rng(seed)
    n_features, n_targets = 5, 2
    weight = rng.normal(size=(n_features, n_targets))
    bias = rng.normal(size=(n_targets,))

    def _make(m: int) -> tuple[np.ndarray, np.ndarray]:
        features = rng.normal(size=(m, n_features)).astype(np.float64)
        targets = (features @ weight + bias + 0.01 * rng.normal(size=(m, n_targets))).astype(np.float64)
        return features, targets

    X, y = _make(64)
    X_val, y_val = _make(16)
    return ConformanceDataset(X=X, y=y, X_val=X_val, y_val=y_val, task_type="regression")


def tiny_regression_3d(seed: int = 0) -> ConformanceDataset:
    """A small sequence regression problem with irregular per-step gaps ``dt``.

    Mirrors the additive 3-D NPZ contract: ``X`` is ``(n, T, F)``, ``dt`` is ``(n, T)`` with
    ``dt[:, 0] == 0`` and strictly-positive later gaps, and ``readout_mask`` marks the steps
    where targets apply. One target per window (the equities_seq shape).
    """
    rng = np.random.default_rng(seed)
    timesteps, n_features, n_targets = 6, 3, 1
    weight = rng.normal(size=(timesteps * n_features, n_targets))

    def _make(m: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        features = rng.normal(size=(m, timesteps, n_features)).astype(np.float64)
        targets = (features.reshape(m, -1) @ weight + 0.01 * rng.normal(size=(m, n_targets))).astype(np.float64)
        dt = np.zeros((m, timesteps), dtype=np.float64)
        dt[:, 1:] = rng.integers(1, 4, size=(m, timesteps - 1)).astype(np.float64)  # irregular positive gaps
        readout_mask = np.ones((m, timesteps), dtype=bool)
        return features, targets, dt, readout_mask

    X, y, dt, mask = _make(48)
    X_val, y_val, dt_val, mask_val = _make(12)
    return ConformanceDataset(
        X=X,
        y=y,
        X_val=X_val,
        y_val=y_val,
        task_type="regression",
        fit_kwargs={"dt": dt, "readout_mask": mask},
    )
