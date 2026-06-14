"""The reusable interface-conformance test kit (ships in juniper-model-core).

A single, parametrized suite any ``TrainableModel`` / ``GrowableModel`` must pass. A consumer
subclasses :class:`TrainableModelConformance` (or :class:`GrowableModelConformance`),
supplying ``make_model`` / ``make_dataset`` / ``make_serializer`` factories; pytest then runs
every contract assertion against that model. This is OQ-12's "installable kit + thin per-repo
wrapper" resolution -- the kit is importable code, not a pytest-plugin entry point.

Unlike the top-level package, this subpackage imports ``numpy`` at runtime -- install
``juniper-model-core[conformance]`` to use it.
"""

from __future__ import annotations

from juniper_model_core.conformance.fixtures import ConformanceDataset, tiny_regression_2d, tiny_regression_3d
from juniper_model_core.conformance.reference import ReferenceGrowableModel, ReferenceLinearModel, ReferenceLinearSerializer
from juniper_model_core.conformance.suite import GrowableModelConformance, TrainableModelConformance

__all__ = [
    "ConformanceDataset",
    "tiny_regression_2d",
    "tiny_regression_3d",
    "TrainableModelConformance",
    "GrowableModelConformance",
    "ReferenceLinearModel",
    "ReferenceGrowableModel",
    "ReferenceLinearSerializer",
]
