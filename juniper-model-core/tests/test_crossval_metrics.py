"""Tests for the held-out scoring helpers (`juniper_model_core.crossval.metrics`).

Covers the known-answer regression math, the `loss == mse` / key-subset invariants, the
single-source-of-truth delegation (the crossval scorer, the shared `_metrics`, and the conformance
reference model all return identical values), and the `score(task_type, ...)` dispatch branches.
"""

import numpy as np
import pytest

from juniper_model_core._metrics import regression_metrics as canonical_metrics
from juniper_model_core.conformance.reference import _regression_metrics as reference_metrics
from juniper_model_core.crossval import regression_metrics, score
from juniper_model_core.validation import REGRESSION_METRIC_KEYS


def test_regression_metrics_known_answer():
    y_true = np.array([[1.0], [2.0], [3.0]])
    y_pred = np.array([[1.0], [2.0], [4.0]])  # only the last sample is wrong, by 1.0
    m = regression_metrics(y_true, y_pred)
    assert m["mse"] == pytest.approx(1.0 / 3.0)
    assert m["mae"] == pytest.approx(1.0 / 3.0)
    assert m["rmse"] == pytest.approx((1.0 / 3.0) ** 0.5)
    assert m["loss"] == m["mse"]
    # ss_res = 1, ss_tot = (1-2)^2 + 0 + (3-2)^2 = 2  ->  r2 = 1 - 1/2 = 0.5
    assert m["r2"] == pytest.approx(0.5)


def test_keys_are_subset_of_canonical_regression_keys():
    m = regression_metrics(np.zeros((4, 1)), np.ones((4, 1)))
    assert set(m) <= REGRESSION_METRIC_KEYS
    assert set(m) == {"mse", "rmse", "mae", "r2", "loss"}


def test_constant_target_r2_is_zero_not_nan():
    y = np.array([[5.0], [5.0], [5.0]])
    m = regression_metrics(y, y)
    assert m["r2"] == 0.0
    assert m["mse"] == 0.0


def test_single_source_of_truth_delegation():
    rng = np.random.default_rng(0)
    y_true = rng.normal(size=(10, 2))
    y_pred = rng.normal(size=(10, 2))
    out = regression_metrics(y_true, y_pred)
    # All three call sites must agree exactly (A2: one shared implementation, no drift).
    assert out == canonical_metrics(y_true, y_pred)
    assert out == reference_metrics(y_true, y_pred)


def test_score_dispatch_regression():
    y_true = np.array([[1.0], [2.0]])
    y_pred = np.array([[1.0], [2.0]])
    out = score("regression", y_true, y_pred)
    assert out["mse"] == 0.0
    assert out == regression_metrics(y_true, y_pred)


def test_score_classification_is_not_implemented():
    with pytest.raises(NotImplementedError):
        score("classification", np.array([0, 1]), np.array([0, 1]))


def test_score_unknown_task_type_raises():
    with pytest.raises(ValueError, match="unknown task_type"):
        score("bogus", np.array([0]), np.array([0]))
