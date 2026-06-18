"""Dogfood: run the conformance kit against the reference regression models.

If the kit harbored a classification (argmax / accuracy) assumption it would fail here
against a pure regression model -- this is the RK-6 guard, self-applied. Running it for both
the 2-D and 3-D fixtures also proves the contract is shape-agnostic, and the growable variant
exercises the ``GrowableModel`` half of the kit.
"""

import numpy as np

from juniper_model_core.conformance import (
    GrowableModelConformance,
    ReferenceGrowableModel,
    ReferenceLinearModel,
    ReferenceLinearSerializer,
    TrainableModelConformance,
    tiny_regression_2d,
    tiny_regression_3d,
)


class TestReferenceConformance2D(TrainableModelConformance):
    def make_model(self):
        return ReferenceLinearModel(task_type="regression")

    def make_dataset(self):
        return tiny_regression_2d()

    def make_serializer(self):
        return ReferenceLinearSerializer()


class TestReferenceConformance3D(TrainableModelConformance):
    def make_model(self):
        return ReferenceLinearModel(task_type="regression")

    def make_dataset(self):
        return tiny_regression_3d()

    def make_serializer(self):
        return ReferenceLinearSerializer()


class TestReferenceGrowableConformance(GrowableModelConformance):
    def make_model(self):
        return ReferenceGrowableModel()

    def make_dataset(self):
        return tiny_regression_2d()

    def make_serializer(self):
        return None


def test_reference_predict_accepts_and_ignores_kwargs():
    """D-CV-7: a 2-D model's ``predict`` accepts auxiliary ``**kw`` and ignores them, so the fold
    executor can call ``predict(X, **aux)`` uniformly across 2-D and 3-D models without a TypeError."""
    data = tiny_regression_2d()
    model = ReferenceLinearModel(task_type="regression")
    model.fit(data.X, data.y)
    baseline = model.predict(data.X)
    with_kw = model.predict(data.X, dt=np.ones(data.X.shape[0]), readout_mask=None, seq_lengths=None)
    assert np.array_equal(baseline, with_kw)
