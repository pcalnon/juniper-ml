"""Tests for the fold executor (`juniper_model_core.crossval.executor`).

Covers the dogfood against the conformance ``ReferenceLinearModel`` (high held-out r2), aggregate
correctness, determinism, fold-tagged event forwarding, the ``map_fn`` parallelism seam (parity +
re-sort), the ``pass_eval_as_val`` policy, the per-sample ``aux`` guard, and a second implementer:
an in-repo 3-D ``TrainableModel`` stub driven with ``aux={dt, readout_mask}`` that proves the layer
is genuinely model-agnostic and slices auxiliary arrays correctly (never importing a real model).
"""

import numpy as np
import pytest

from juniper_model_core import TrainableModel, TrainingEvent, TrainResult
from juniper_model_core.conformance import ReferenceLinearModel
from juniper_model_core.crossval import cross_validate, regression_metrics, walk_forward_folds
from juniper_model_core.validation import legal_event_order


def _linear_data(n=120, n_features=4, seed=0):
    rng = np.random.default_rng(seed)
    weight = rng.normal(size=(n_features, 1))
    X = rng.normal(size=(n, n_features))
    y = X @ weight + 0.01 * rng.normal(size=(n, 1))
    return X, y


# --------------------------------------------------------------------------------------------------
# Dogfood + aggregate + determinism
# --------------------------------------------------------------------------------------------------
def test_dogfood_reference_linear_high_r2():
    X, y = _linear_data()
    folds = walk_forward_folds(X.shape[0], n_folds=4)
    result = cross_validate(lambda i: ReferenceLinearModel(random_seed=0), X, y, folds)
    assert result.task_type == "regression"
    assert len(result.folds) == 4
    assert [fr.fold for fr in result.folds] == [0, 1, 2, 3]
    assert result.eval_aggregate["r2"] > 0.95  # linear data, low noise
    for fr in result.folds:
        assert set(fr.eval_metrics) == {"mse", "rmse", "mae", "r2", "loss"}
        assert fr.n_epochs >= 1
        assert set(fr.train_metrics)  # non-empty train-time metrics


def test_aggregate_is_mean_and_std_of_folds():
    X, y = _linear_data()
    folds = walk_forward_folds(X.shape[0], n_folds=3)
    result = cross_validate(lambda i: ReferenceLinearModel(), X, y, folds)
    for key in result.eval_aggregate:
        values = np.asarray([fr.eval_metrics[key] for fr in result.folds], dtype=np.float64)
        assert result.eval_aggregate[key] == pytest.approx(float(values.mean()))
        assert result.eval_std[key] == pytest.approx(float(values.std()))


def test_determinism_same_inputs_same_result():
    X, y = _linear_data()
    folds = walk_forward_folds(X.shape[0], n_folds=4)
    first = cross_validate(lambda i: ReferenceLinearModel(random_seed=0), X, y, folds)
    second = cross_validate(lambda i: ReferenceLinearModel(random_seed=0), X, y, folds)
    assert [fr.eval_metrics for fr in first.folds] == [fr.eval_metrics for fr in second.folds]
    assert first.eval_aggregate == second.eval_aggregate
    assert first.eval_std == second.eval_std


# --------------------------------------------------------------------------------------------------
# Event forwarding (fold-tagged, legal order per fold)
# --------------------------------------------------------------------------------------------------
def test_event_forwarding_is_fold_tagged_and_legal():
    X, y = _linear_data()
    folds = walk_forward_folds(X.shape[0], n_folds=3)
    by_fold: dict[int, list] = {}

    def on_event(fold_idx, event):
        by_fold.setdefault(fold_idx, []).append(event)

    cross_validate(lambda i: ReferenceLinearModel(), X, y, folds, on_event=on_event)
    assert set(by_fold) == {0, 1, 2}
    for events in by_fold.values():
        assert legal_event_order(events)


# --------------------------------------------------------------------------------------------------
# map_fn seam (OPT-F F2): parity with serial + re-sort of out-of-order results
# --------------------------------------------------------------------------------------------------
def test_map_fn_seam_parity_and_resort():
    X, y = _linear_data(100)
    folds = walk_forward_folds(X.shape[0], n_folds=4)
    serial = cross_validate(lambda i: ReferenceLinearModel(), X, y, folds)

    def list_map(fn, items):
        return [fn(item) for item in items]

    parity = cross_validate(lambda i: ReferenceLinearModel(), X, y, folds, map_fn=list_map)
    assert parity.eval_aggregate == serial.eval_aggregate
    assert [fr.eval_metrics for fr in parity.folds] == [fr.eval_metrics for fr in serial.folds]

    def reversed_map(fn, items):
        return [fn(item) for item in reversed(list(items))]

    reordered = cross_validate(lambda i: ReferenceLinearModel(), X, y, folds, map_fn=reversed_map)
    assert [fr.fold for fr in reordered.folds] == [0, 1, 2, 3]  # re-sorted by fold index
    assert reordered.eval_aggregate == serial.eval_aggregate


# --------------------------------------------------------------------------------------------------
# pass_eval_as_val policy (OPT-B B3): default keeps the eval set out of fit
# --------------------------------------------------------------------------------------------------
class _ValRecorder(ReferenceLinearModel):
    def __init__(self):
        super().__init__()
        self.val_rows = "unset"

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw):
        self.val_rows = None if X_val is None else int(X_val.shape[0])
        return super().fit(X, y, X_val=X_val, y_val=y_val, on_event=on_event, **kw)


def test_pass_eval_as_val_default_is_false():
    X, y = _linear_data(60)
    folds = walk_forward_folds(X.shape[0], n_folds=3)
    models: dict[int, _ValRecorder] = {}

    def factory(i):
        models[i] = _ValRecorder()
        return models[i]

    cross_validate(factory, X, y, folds)
    assert all(m.val_rows is None for m in models.values())


def test_pass_eval_as_val_true_forwards_eval_slice():
    X, y = _linear_data(60)
    folds = walk_forward_folds(X.shape[0], n_folds=3)
    models: dict[int, _ValRecorder] = {}

    def factory(i):
        models[i] = _ValRecorder()
        return models[i]

    cross_validate(factory, X, y, folds, pass_eval_as_val=True)
    for fold_idx, model in models.items():
        assert model.val_rows == len(folds[fold_idx].eval_idx)


# --------------------------------------------------------------------------------------------------
# Error paths
# --------------------------------------------------------------------------------------------------
def test_aux_must_be_per_sample():
    X, y = _linear_data(40)
    folds = walk_forward_folds(X.shape[0], n_folds=2)
    with pytest.raises(ValueError, match="not per-sample"):
        cross_validate(lambda i: ReferenceLinearModel(), X, y, folds, aux={"dt": np.zeros(7)})


def test_x_y_sample_mismatch_raises():
    folds = walk_forward_folds(10, n_folds=2)
    with pytest.raises(ValueError, match="samples"):
        cross_validate(lambda i: ReferenceLinearModel(), np.zeros((10, 3)), np.zeros((9, 1)), folds)


def test_empty_folds_raises():
    with pytest.raises(ValueError, match="folds is empty"):
        cross_validate(lambda i: ReferenceLinearModel(), np.zeros((10, 2)), np.zeros((10, 1)), [])


# --------------------------------------------------------------------------------------------------
# Second implementer: in-repo 3-D TrainableModel stub driven with aux (model-agnostic proof)
# --------------------------------------------------------------------------------------------------
class _Recording3DModel(TrainableModel):
    """A minimal 3-D regressor that *requires* a per-sample ``dt`` in ``**kw``.

    It asserts on every call that the ``dt`` it receives has exactly as many rows as ``X`` -- so if
    the executor mis-sliced ``aux`` the test would fail. This is the in-repo stand-in for a real
    sequence model (the recurrence ``LMURegressor``), kept here to avoid a model-core -> recurrence
    dependency cycle (F-REFINE-6 / OPT-C C1).
    """

    def __init__(self):
        self.task_type = "regression"
        self.random_seed = 0
        self._coef = None
        self._in_shape: tuple[int, ...] = ()
        self._out_shape: tuple[int, ...] = ()
        self._metrics: dict[str, float] = {}

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        dt = kw.get("dt")
        assert dt is not None, "stub requires dt in **kw"
        assert dt.shape[0] == X.shape[0], f"dt rows {dt.shape[0]} != X rows {X.shape[0]} (aux mis-sliced)"
        self._in_shape = tuple(X.shape[1:])
        self._out_shape = tuple(y.shape[1:])
        design = np.concatenate([X.reshape(X.shape[0], -1), np.ones((X.shape[0], 1))], axis=1)
        coef, *_ = np.linalg.lstsq(design, y.reshape(y.shape[0], -1), rcond=None)
        self._coef = coef
        preds = (design @ coef).reshape(y.shape)
        self._metrics = regression_metrics(y, preds)
        seq = 0
        if on_event is not None:
            on_event(TrainingEvent("training_start", {}, seq))
            seq += 1
            on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": dict(self._metrics)}, seq))
            seq += 1
            on_event(TrainingEvent("training_end", {}, seq))
        return TrainResult(final_metrics=dict(self._metrics), n_epochs=1, history=None, stopped_reason="converged")

    def predict(self, X, **kw):
        X = np.asarray(X, dtype=np.float64)
        dt = kw.get("dt")
        assert dt is not None, "stub requires dt in predict(**kw)"
        assert dt.shape[0] == X.shape[0], f"dt rows {dt.shape[0]} != X rows {X.shape[0]} (aux mis-sliced)"
        design = np.concatenate([X.reshape(X.shape[0], -1), np.ones((X.shape[0], 1))], axis=1)
        return (design @ self._coef).reshape((X.shape[0], *self._out_shape))

    def metrics(self):
        return dict(self._metrics)

    def describe_topology(self):
        return {
            "model_type": "stub_3d",
            "nodes": [{"id": "input", "kind": "input", "frozen": True}, {"id": "output", "kind": "output", "frozen": False}],
            "edges": [{"src": "input", "dst": "output", "recurrent": False}],
            "meta": {"n_units": 0, "task_type": self.task_type},
        }

    @property
    def input_shape(self):
        return self._in_shape

    @property
    def output_shape(self):
        return self._out_shape


def test_second_implementer_3d_with_aux_runs_and_slices():
    rng = np.random.default_rng(0)
    n, timesteps, n_features = 60, 5, 2
    X = rng.normal(size=(n, timesteps, n_features))
    weight = rng.normal(size=(timesteps * n_features, 1))
    y = X.reshape(n, -1) @ weight + 0.01 * rng.normal(size=(n, 1))
    dt = np.abs(rng.normal(size=(n, timesteps))) + 0.1
    readout_mask = np.ones((n, timesteps), dtype=bool)
    folds = walk_forward_folds(n, n_folds=3)

    result = cross_validate(lambda i: _Recording3DModel(), X, y, folds, aux={"dt": dt, "readout_mask": readout_mask})

    assert result.task_type == "regression"
    assert len(result.folds) == 3
    assert result.eval_aggregate["r2"] > 0.9  # the Delta-t path ran end-to-end on a linear-over-window synthetic
    assert set(result.eval_aggregate) == {"mse", "rmse", "mae", "r2", "loss"}


def test_reference_linear_still_conforms_to_widened_predict():
    # A bare predict(self, X) implementer still satisfies the widened ABC and runs without aux.
    model = ReferenceLinearModel()
    assert isinstance(model, TrainableModel)
    X, y = _linear_data(30, n_features=3)
    folds = walk_forward_folds(X.shape[0], n_folds=2)
    result = cross_validate(lambda i: ReferenceLinearModel(), X, y, folds)
    assert result.eval_aggregate["r2"] > 0.9
