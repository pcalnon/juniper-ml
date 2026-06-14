"""Dogfood: run the conformance kit against the reference regression models.

If the kit harbored a classification (argmax / accuracy) assumption it would fail here
against a pure regression model -- this is the RK-6 guard, self-applied. Running it for both
the 2-D and 3-D fixtures also proves the contract is shape-agnostic, and the growable variant
exercises the ``GrowableModel`` half of the kit.
"""

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
