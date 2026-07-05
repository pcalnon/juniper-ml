"""``juniper-model-core`` -- the shared model-contract template for the Juniper ML platform.

A genuinely-shared abstraction (the ``-core`` suffix): the minimal interface the Juniper
service layer needs from *any* learning model, plus a reusable conformance kit that proves a
model is pluggable. The contract is derived from **two** real implementers -- the
Cascade-Correlation network (a growable 2-D classifier) and the Delta-t-native Legendre
Memory Unit (a fixed-order time-series regressor) -- never from cascor alone (refactor plan
risk RK-4).

Importing this top-level package pulls **no** third-party runtime dependency: the contract
references ``numpy`` only in type annotations. The conformance kit
(:mod:`juniper_model_core.conformance`) *does* use numpy at runtime -- install the
``[conformance]`` extra to run it.

See ``notes/JUNIPER_2026-06-14_JUNIPER-ML_MODEL-CORE-INTERFACE-DESIGN.md`` (in the juniper-ml repo) for
the full design rationale and the ratified decision ledger (D1-D10).
"""

from __future__ import annotations

from juniper_model_core._version import __version__
from juniper_model_core.events import TRAINING_EVENT_TYPES, TrainingEvent, TrainingEventType
from juniper_model_core.interfaces import GrowableModel, GrowthOutcome, TaskType, TrainableModel, TrainResult
from juniper_model_core.lifecycle import TrainingLifecycleBase
from juniper_model_core.serialization import ModelSerializer
from juniper_model_core.topology import NODE_KINDS, NodeKind, Topology, TopologyEdge, TopologyNode
from juniper_model_core.validation import (
    CLASSIFICATION_METRIC_KEYS,
    REGRESSION_METRIC_KEYS,
    legal_event_order,
    validate_metrics,
    validate_topology,
)

__all__ = [
    "__version__",
    # interfaces
    "TaskType",
    "TrainResult",
    "GrowthOutcome",
    "TrainableModel",
    "GrowableModel",
    # events
    "TrainingEvent",
    "TrainingEventType",
    "TRAINING_EVENT_TYPES",
    # topology
    "NodeKind",
    "NODE_KINDS",
    "TopologyNode",
    "TopologyEdge",
    "Topology",
    # serialization
    "ModelSerializer",
    # validation (shared behavior, as inspectable free functions -- never base-class magic)
    "validate_metrics",
    "validate_topology",
    "legal_event_order",
    "REGRESSION_METRIC_KEYS",
    "CLASSIFICATION_METRIC_KEYS",
    # lifecycle seam (body deferred to WS-2)
    "TrainingLifecycleBase",
]
