"""Minimal but genuine reference implementations of the model contract.

:class:`ReferenceLinearModel` is a closed-form least-squares regressor over flattened inputs.
It exists for one reason: to be the kit's own RK-6 canary. The conformance suite is run
against it in juniper-model-core's own tests, so the kit *cannot* harbor a hidden ``argmax``
/ accuracy assumption without its own CI failing. :class:`ReferenceGrowableModel` extends it
with a trivial growth counter to exercise the ``GrowableModel`` half of the kit. Neither is
meant for real use; together they double as the smallest worked example of how to implement
the interface (numpy at the boundary, events via ``on_event``, a lossless serializer).
"""

from __future__ import annotations

import json
import os

import numpy as np

from juniper_model_core._metrics import regression_metrics as _regression_metrics
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import GrowableModel, GrowthOutcome, TaskType, TrainableModel, TrainResult
from juniper_model_core.serialization import ModelSerializer
from juniper_model_core.topology import Topology

__all__ = ["ReferenceLinearModel", "ReferenceGrowableModel", "ReferenceLinearSerializer"]


def _flatten(X: np.ndarray) -> np.ndarray:
    """Collapse all non-batch axes: ``(n, *shape) -> (n, prod(shape))``."""
    return np.asarray(X, dtype=np.float64).reshape(X.shape[0], -1)


def _design(flat: np.ndarray) -> np.ndarray:
    """Append a bias column to a flattened design matrix."""
    return np.concatenate([flat, np.ones((flat.shape[0], 1))], axis=1)


class ReferenceLinearModel(TrainableModel):
    """Closed-form least-squares regressor over flattened inputs (reference only)."""

    def __init__(self, task_type: TaskType = "regression", random_seed: int | None = 0) -> None:
        if task_type != "regression":
            raise ValueError("ReferenceLinearModel only implements task_type='regression'")
        self.task_type: TaskType = task_type
        self.random_seed = random_seed
        self._coef: np.ndarray | None = None
        self._in_shape: tuple[int, ...] = ()
        self._out_shape: tuple[int, ...] = ()
        self._metrics: dict[str, float] = {}

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        self._in_shape = tuple(X.shape[1:])
        self._out_shape = tuple(y.shape[1:])
        seq = 0
        if on_event is not None:
            on_event(TrainingEvent("training_start", {"n_samples": int(X.shape[0])}, seq))
            seq += 1
        design = _design(_flatten(X))
        target = y.reshape(y.shape[0], -1)
        coef, *_ = np.linalg.lstsq(design, target, rcond=None)
        self._coef = coef
        preds = (design @ coef).reshape(y.shape)
        self._metrics = _regression_metrics(y, preds)
        if on_event is not None:
            on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": dict(self._metrics)}, seq))
            seq += 1
            on_event(TrainingEvent("training_end", {"metrics": dict(self._metrics)}, seq))
        return TrainResult(final_metrics=dict(self._metrics), n_epochs=1, history=[dict(self._metrics)], stopped_reason="converged")

    def predict(self, X) -> np.ndarray:
        if self._coef is None:
            raise RuntimeError("model is not fitted")
        X = np.asarray(X, dtype=np.float64)
        out = _design(_flatten(X)) @ self._coef
        return out.reshape((X.shape[0], *self._out_shape))

    def metrics(self) -> dict[str, float]:
        return dict(self._metrics)

    def describe_topology(self) -> Topology:
        n_in = int(np.prod(self._in_shape)) if self._in_shape else 0
        n_out = int(np.prod(self._out_shape)) if self._out_shape else 0
        return {
            "model_type": "reference_linear",
            "nodes": [
                {"id": "input", "kind": "input", "frozen": True},
                {"id": "output", "kind": "output", "frozen": False},
            ],
            "edges": [{"src": "input", "dst": "output", "recurrent": False}],
            "meta": {"n_units": 0, "task_type": self.task_type, "n_in": n_in, "n_out": n_out},
        }

    @property
    def input_shape(self) -> tuple[int, ...]:
        return self._in_shape

    @property
    def output_shape(self) -> tuple[int, ...]:
        return self._out_shape


class ReferenceGrowableModel(ReferenceLinearModel, GrowableModel):
    """A trivially-growable reference regressor -- exercises the ``GrowableModel`` kit.

    Growth here is a bookkeeping counter (no effect on the linear fit); it exists only to
    drive :meth:`grow_step` / :attr:`n_units` / :meth:`freeze` through the conformance suite.
    """

    def __init__(self, task_type: TaskType = "regression", random_seed: int | None = 0, max_units: int = 3) -> None:
        super().__init__(task_type=task_type, random_seed=random_seed)
        self._n_units = 0
        self._frozen = False
        self._max_units = max_units

    @property
    def n_units(self) -> int:
        return self._n_units

    def grow_step(self, **kw) -> GrowthOutcome:
        if self._frozen or self._n_units >= self._max_units:
            return GrowthOutcome(added=False, n_units=self._n_units)
        self._n_units += 1
        return GrowthOutcome(added=True, n_units=self._n_units, unit_id=f"u{self._n_units}", score=1.0 / self._n_units)

    def freeze(self) -> None:
        self._frozen = True

    def describe_topology(self) -> Topology:
        topo = super().describe_topology()
        topo["model_type"] = "reference_growable"
        topo["meta"]["n_units"] = self._n_units
        for index in range(1, self._n_units + 1):
            topo["nodes"].append({"id": f"u{index}", "kind": "hidden", "frozen": True})
        return topo


class ReferenceLinearSerializer(ModelSerializer):
    """Lossless ``.npz`` + JSON serializer for :class:`ReferenceLinearModel`."""

    def save(self, model, path) -> None:
        if not isinstance(model, ReferenceLinearModel):
            raise TypeError("ReferenceLinearSerializer only serializes ReferenceLinearModel")
        if model._coef is None:
            raise RuntimeError("cannot serialize an unfitted model")
        meta = {
            "task_type": model.task_type,
            "random_seed": model.random_seed,
            "in_shape": list(model._in_shape),
            "out_shape": list(model._out_shape),
            "metrics": model._metrics,
        }
        np.savez(os.fspath(path), coef=model._coef, meta=json.dumps(meta))

    def load(self, path) -> ReferenceLinearModel:
        resolved = os.fspath(path)
        if not resolved.endswith(".npz"):
            resolved = resolved + ".npz"
        with np.load(resolved, allow_pickle=False) as data:
            coef = data["coef"]
            meta = json.loads(str(data["meta"]))
        model = ReferenceLinearModel(task_type=meta["task_type"], random_seed=meta["random_seed"])
        model._coef = coef
        model._in_shape = tuple(meta["in_shape"])
        model._out_shape = tuple(meta["out_shape"])
        model._metrics = {key: float(value) for key, value in meta["metrics"].items()}
        return model
