"""Unit tests for the value types, ABC abstractness, and the lifecycle seam."""

from dataclasses import FrozenInstanceError

import pytest

from juniper_model_core import (
    GrowableModel,
    GrowthOutcome,
    ModelSerializer,
    TrainableModel,
    TrainingEvent,
    TrainingLifecycleBase,
    TrainResult,
    __version__,
)


def test_version_is_nonempty_string():
    assert isinstance(__version__, str) and __version__


def test_train_result_is_frozen():
    result = TrainResult(final_metrics={"mse": 0.1}, n_epochs=2)
    assert result.history is None and result.stopped_reason is None
    with pytest.raises(FrozenInstanceError):
        result.n_epochs = 3  # frozen dataclass


def test_growth_outcome_defaults():
    outcome = GrowthOutcome(added=True, n_units=1)
    assert outcome.unit_id is None and outcome.score is None


def test_training_event_default_payload_and_seq():
    event = TrainingEvent("epoch_end")
    assert event.payload == {} and event.seq == 0


def test_abstract_classes_cannot_instantiate():
    for abstract in (TrainableModel, GrowableModel, ModelSerializer):
        with pytest.raises(TypeError):
            abstract()  # type: ignore[abstract]


class _DummyModel(TrainableModel):
    task_type = "regression"

    def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw):
        return TrainResult(final_metrics={"mse": 0.0}, n_epochs=1)

    def predict(self, X):
        return X

    def metrics(self):
        return {"mse": 0.0}

    def describe_topology(self):
        return {"model_type": "dummy", "nodes": [{"id": "i", "kind": "input", "frozen": True}], "edges": [], "meta": {"task_type": "regression"}}

    @property
    def input_shape(self):
        return (1,)

    @property
    def output_shape(self):
        return (1,)


def test_concrete_model_instantiates():
    model = _DummyModel()
    assert isinstance(model, TrainableModel)
    assert model.metrics() == {"mse": 0.0}


def test_lifecycle_seam_emit_and_run():
    captured: list = []

    class _Lifecycle(TrainingLifecycleBase):
        def run(self, *args, **kwargs):
            self.emit(TrainingEvent("training_start", {}, 0))
            self.emit(TrainingEvent("training_end", {}, 1))
            return TrainResult(final_metrics={"mse": 0.0}, n_epochs=1)

    lifecycle = _Lifecycle(_DummyModel(), on_event=captured.append)
    result = lifecycle.run()
    assert result.n_epochs == 1
    assert [event.type for event in captured] == ["training_start", "training_end"]


def test_lifecycle_emit_without_sink_is_noop():
    class _Lifecycle(TrainingLifecycleBase):
        def run(self, *args, **kwargs):
            return TrainResult(final_metrics={}, n_epochs=0)

    lifecycle = _Lifecycle(_DummyModel())  # no on_event
    lifecycle.emit(TrainingEvent("epoch_end", {}, 0))  # must not raise


def test_lifecycle_base_is_abstract():
    with pytest.raises(TypeError):
        TrainingLifecycleBase(_DummyModel())  # type: ignore[abstract]
