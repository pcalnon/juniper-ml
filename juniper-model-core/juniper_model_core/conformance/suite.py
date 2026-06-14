"""The parametrized conformance assertions.

Subclass :class:`TrainableModelConformance` in a consumer's test module, implement the three
factory hooks, and pytest runs every contract check against the supplied model. The base
classes are deliberately *not* named ``Test*`` so pytest does not collect them directly --
only the consumer's concrete ``Test*`` subclass is collected.

Example::

    from juniper_model_core.conformance import TrainableModelConformance, tiny_regression_3d

    class TestLMUConformance(TrainableModelConformance):
        def make_model(self):      return LMUModel(d=16, theta=30.0, task_type="regression")
        def make_dataset(self):    return tiny_regression_3d()
        def make_serializer(self): return LMUSerializer()
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from juniper_model_core.conformance.fixtures import ConformanceDataset
from juniper_model_core.interfaces import GrowableModel, TrainableModel
from juniper_model_core.serialization import ModelSerializer
from juniper_model_core.validation import legal_event_order, validate_metrics, validate_topology

__all__ = ["TrainableModelConformance", "GrowableModelConformance"]


class TrainableModelConformance:
    """Contract assertions every ``TrainableModel`` must satisfy.

    Concrete subclasses override :meth:`make_model` and :meth:`make_dataset` (and optionally
    :meth:`make_serializer`, which defaults to ``None`` to skip the serialization check).
    """

    # ----- consumer-supplied factories ------------------------------------------------
    def make_model(self) -> TrainableModel:
        raise NotImplementedError("conformance subclass must implement make_model()")

    def make_dataset(self) -> ConformanceDataset:
        raise NotImplementedError("conformance subclass must implement make_dataset()")

    def make_serializer(self) -> ModelSerializer | None:
        return None

    # ----- shared helper --------------------------------------------------------------
    def _fit(self, model: TrainableModel, dataset: ConformanceDataset, events: list) -> object:
        return model.fit(dataset.X, dataset.y, X_val=dataset.X_val, y_val=dataset.y_val, on_event=events.append, **dataset.fit_kwargs)

    # ----- contract checks ------------------------------------------------------------
    def test_isinstance(self) -> None:
        assert isinstance(self.make_model(), TrainableModel)

    def test_declares_task_type(self) -> None:
        assert self.make_model().task_type in ("classification", "regression")

    def test_fit_returns_train_result(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        result = self._fit(model, dataset, [])
        assert result.n_epochs >= 1
        assert isinstance(result.final_metrics, dict) and result.final_metrics

    def test_fit_predict_metrics_roundtrip(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        preds = np.asarray(model.predict(dataset.X_val))
        assert preds.shape[0] == dataset.X_val.shape[0]
        validate_metrics(model.task_type, model.metrics())

    def test_predict_output_shape(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        preds = np.asarray(model.predict(dataset.X_val))
        assert tuple(preds.shape[1:]) == tuple(model.output_shape)

    def test_metrics_keys_match_task_type(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        validate_metrics(model.task_type, model.metrics())

    def test_no_classification_assumptions_for_regression(self) -> None:
        # RK-6: a regression model must traverse the generic path with no accuracy key.
        model = self.make_model()
        if model.task_type != "regression":
            return
        dataset = self.make_dataset()
        self._fit(model, dataset, [])
        assert "accuracy" not in model.metrics()

    def test_describe_topology_renderable(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        topology = model.describe_topology()
        validate_topology(topology)
        assert topology["meta"]["task_type"] == model.task_type

    def test_event_ordering(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        events: list = []
        self._fit(model, dataset, events)
        assert legal_event_order(events)

    def test_serialization_roundtrip_lossless(self) -> None:
        serializer = self.make_serializer()
        if serializer is None:
            return
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        before = np.asarray(model.predict(dataset.X_val))
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "model")
            serializer.save(model, path)
            restored = serializer.load(path)
        after = np.asarray(restored.predict(dataset.X_val))
        assert np.array_equal(before, after), "predictions differ after save/load -- serialization is not lossless"


class GrowableModelConformance(TrainableModelConformance):
    """Additional assertions for ``GrowableModel`` implementers."""

    def test_is_growable(self) -> None:
        assert isinstance(self.make_model(), GrowableModel)

    def test_grow_step_increments_n_units(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        before = model.n_units
        outcome = model.grow_step()
        if outcome.added:
            assert model.n_units == before + 1
            assert outcome.n_units == model.n_units

    def test_freeze_stops_growth(self) -> None:
        model, dataset = self.make_model(), self.make_dataset()
        self._fit(model, dataset, [])
        model.freeze()
        before = model.n_units
        outcome = model.grow_step()
        assert not outcome.added
        assert model.n_units == before
