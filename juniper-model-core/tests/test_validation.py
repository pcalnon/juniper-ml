"""Unit tests for the shared validation free functions (the C1 'behavior' surface)."""

import pytest

from juniper_model_core import (
    CLASSIFICATION_METRIC_KEYS,
    REGRESSION_METRIC_KEYS,
    TrainingEvent,
    legal_event_order,
    validate_metrics,
    validate_topology,
)


def test_validate_metrics_accepts_regression():
    validate_metrics("regression", {"mse": 0.1, "r2": 0.9})


def test_validate_metrics_rejects_accuracy_for_regression():
    with pytest.raises(ValueError):
        validate_metrics("regression", {"mse": 0.1, "accuracy": 0.9})


def test_validate_metrics_requires_canonical_regression_key():
    with pytest.raises(ValueError):
        validate_metrics("regression", {"weird": 1.0})


def test_validate_metrics_accepts_classification():
    validate_metrics("classification", {"accuracy": 0.9, "loss": 0.2})


def test_validate_metrics_classification_requires_canonical_key():
    with pytest.raises(ValueError):
        validate_metrics("classification", {"mse": 0.1})


def test_validate_metrics_rejects_non_numeric():
    with pytest.raises(ValueError):
        validate_metrics("regression", {"mse": "nope"})


def test_validate_metrics_rejects_bool():
    with pytest.raises(ValueError):
        validate_metrics("regression", {"mse": True})


def test_validate_metrics_unknown_task_type():
    with pytest.raises(ValueError):
        validate_metrics("clustering", {"x": 1.0})  # type: ignore[arg-type]


def test_metric_key_sets_partition_accuracy():
    assert "accuracy" in CLASSIFICATION_METRIC_KEYS
    assert "accuracy" not in REGRESSION_METRIC_KEYS
    assert "loss" in REGRESSION_METRIC_KEYS and "loss" in CLASSIFICATION_METRIC_KEYS


def _topology(**overrides):
    base = {
        "model_type": "x",
        "nodes": [
            {"id": "a", "kind": "input", "frozen": True},
            {"id": "b", "kind": "output", "frozen": False},
        ],
        "edges": [{"src": "a", "dst": "b", "recurrent": False}],
        "meta": {"task_type": "regression"},
    }
    base.update(overrides)
    return base


def test_validate_topology_ok():
    validate_topology(_topology())


def test_validate_topology_missing_key():
    with pytest.raises(ValueError):
        validate_topology({"nodes": [], "edges": [], "meta": {}})  # type: ignore[arg-type]


def test_validate_topology_empty_nodes():
    with pytest.raises(ValueError):
        validate_topology(_topology(nodes=[]))


def test_validate_topology_bad_model_type():
    with pytest.raises(ValueError):
        validate_topology(_topology(model_type=""))


def test_validate_topology_duplicate_id():
    with pytest.raises(ValueError):
        validate_topology(_topology(nodes=[{"id": "a", "kind": "input", "frozen": True}, {"id": "a", "kind": "output", "frozen": False}]))


def test_validate_topology_bad_kind():
    with pytest.raises(ValueError):
        validate_topology(_topology(nodes=[{"id": "a", "kind": "banana", "frozen": True}], edges=[]))


def test_validate_topology_dangling_edge():
    with pytest.raises(ValueError):
        validate_topology(_topology(edges=[{"src": "a", "dst": "ghost", "recurrent": False}]))


def test_validate_topology_meta_without_task_type():
    with pytest.raises(ValueError):
        validate_topology(_topology(meta={}))


def test_legal_event_order_ok():
    events = [TrainingEvent("training_start", {}, 0), TrainingEvent("epoch_end", {}, 1), TrainingEvent("training_end", {}, 2)]
    assert legal_event_order(events)


def test_legal_event_order_empty():
    assert not legal_event_order([])


def test_legal_event_order_bad_start():
    assert not legal_event_order([TrainingEvent("epoch_end", {}, 0), TrainingEvent("training_end", {}, 1)])


def test_legal_event_order_missing_end():
    assert not legal_event_order([TrainingEvent("training_start", {}, 0), TrainingEvent("epoch_end", {}, 1)])


def test_legal_event_order_duplicate_start():
    events = [TrainingEvent("training_start", {}, 0), TrainingEvent("training_start", {}, 1), TrainingEvent("training_end", {}, 2)]
    assert not legal_event_order(events)


def test_legal_event_order_decreasing_seq():
    assert not legal_event_order([TrainingEvent("training_start", {}, 5), TrainingEvent("training_end", {}, 1)])
