"""Tests for the synchronous ``TrainingLifecycle`` body (WS-2).

Drives juniper-model-core's conformance *reference* models through the lifecycle and
asserts the model's TrainingEvents are forwarded in a legal order with a monotonic,
lifecycle-stamped ``seq``.
"""

from __future__ import annotations

import numpy as np
from juniper_model_core.conformance.fixtures import tiny_regression_2d
from juniper_model_core.conformance.reference import ReferenceGrowableModel, ReferenceLinearModel
from juniper_model_core.events import TrainingEvent
from juniper_model_core.interfaces import TrainResult

from juniper_service_core.lifecycle import EventCollector, TrainingLifecycle


def test_run_drives_fit_and_returns_trainresult() -> None:
    ds = tiny_regression_2d()
    result = TrainingLifecycle(ReferenceLinearModel()).run(ds.X, ds.y, X_val=ds.X_val, y_val=ds.y_val)
    assert isinstance(result, TrainResult)
    assert isinstance(result.final_metrics, dict) and result.final_metrics


def test_events_forwarded_in_legal_order_with_monotonic_seq() -> None:
    ds = tiny_regression_2d()
    collector = EventCollector()
    TrainingLifecycle(ReferenceLinearModel(), on_event=collector).run(ds.X, ds.y)
    assert collector.types[0] == "training_start"
    assert collector.types[-1] == "training_end"
    assert "epoch_end" in collector.types
    # The lifecycle owns run-level ordering: a contiguous monotonic seq from 0.
    assert [e.seq for e in collector.events] == list(range(len(collector.events)))


def test_lifecycle_seq_is_authoritative_over_model_seq() -> None:
    """A model emitting a constant (wrong) seq still yields a monotonic stream."""

    class BadSeqModel(ReferenceLinearModel):
        def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
            if on_event is not None:
                on_event(TrainingEvent("training_start", {}, 99))
                on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {}}, 99))
                on_event(TrainingEvent("training_end", {}, 99))
            return TrainResult(final_metrics={"mse": 0.0}, n_epochs=1)

    collector = EventCollector()
    TrainingLifecycle(BadSeqModel(), on_event=collector).run(
        np.zeros((2, 2), np.float32), np.zeros((2, 1), np.float32)
    )
    assert [e.seq for e in collector.events] == [0, 1, 2]


def test_rerun_resets_seq() -> None:
    ds = tiny_regression_2d()
    collector = EventCollector()
    lifecycle = TrainingLifecycle(ReferenceLinearModel(), on_event=collector)
    lifecycle.run(ds.X, ds.y)
    n_first = len(collector.events)
    lifecycle.run(ds.X, ds.y)
    second = collector.events[n_first:]
    assert [e.seq for e in second] == list(range(len(second)))


def test_drives_growable_model() -> None:
    ds = tiny_regression_2d()
    collector = EventCollector()
    result = TrainingLifecycle(ReferenceGrowableModel(), on_event=collector).run(ds.X, ds.y)
    assert isinstance(result, TrainResult)
    assert collector.types[0] == "training_start"
    assert collector.types[-1] == "training_end"


def test_no_event_sink_is_safe() -> None:
    ds = tiny_regression_2d()
    # No on_event sink: emit() is a no-op; run must still complete.
    result = TrainingLifecycle(ReferenceLinearModel()).run(ds.X, ds.y)
    assert isinstance(result, TrainResult)
