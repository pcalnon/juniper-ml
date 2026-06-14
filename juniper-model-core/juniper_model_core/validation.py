"""Inspectable validation helpers -- the shared *behavior* the interface ABCs exclude.

C1 (first-principles / no black-box base classes) is honored by keeping the ABCs
interface-only and putting every piece of shared behavior here, as pure functions over plain
Python data (dicts, lists, strings). Nothing here is third-party-dependent at runtime, and
nothing is inherited base-class machinery: implementers and the conformance kit call these
explicitly.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from juniper_model_core.events import TRAINING_EVENT_TYPES
from juniper_model_core.topology import NODE_KINDS

if TYPE_CHECKING:
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TaskType
    from juniper_model_core.topology import Topology

__all__ = [
    "REGRESSION_METRIC_KEYS",
    "CLASSIFICATION_METRIC_KEYS",
    "validate_metrics",
    "validate_topology",
    "legal_event_order",
]

#: Canonical metric keys per task type. Extra keys are permitted (cost of model #20), with
#: one hard rule enforced by :func:`validate_metrics`: a regression model must never report a
#: classification-only key such as ``accuracy`` (the RK-6 guard against classification
#: assumptions leaking into generic code).
REGRESSION_METRIC_KEYS: frozenset[str] = frozenset({"mse", "rmse", "mae", "r2", "loss"})
CLASSIFICATION_METRIC_KEYS: frozenset[str] = frozenset({"accuracy", "loss", "cross_entropy", "f1", "precision", "recall"})

#: Keys that may never appear in a regression model's metrics.
_CLASSIFICATION_ONLY: frozenset[str] = CLASSIFICATION_METRIC_KEYS - REGRESSION_METRIC_KEYS


def validate_metrics(task_type: TaskType, metrics: dict[str, float]) -> None:
    """Raise ``ValueError`` if ``metrics`` is inconsistent with ``task_type``.

    Rules: every value is a real number (``bool`` rejected); a ``regression`` model reports
    at least one canonical regression key and *no* classification-only key (RK-6); a
    ``classification`` model reports at least one canonical classification key.
    """
    for key, value in metrics.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"metric {key!r} is not a real number: {value!r}")
    keys = set(metrics)
    if task_type == "regression":
        leaked = keys & _CLASSIFICATION_ONLY
        if leaked:
            raise ValueError(f"regression model reports classification-only metric(s): {sorted(leaked)} (RK-6)")
        if not keys & REGRESSION_METRIC_KEYS:
            raise ValueError(f"regression model reports no canonical regression metric; got {sorted(keys)}")
    elif task_type == "classification":
        if not keys & CLASSIFICATION_METRIC_KEYS:
            raise ValueError(f"classification model reports no canonical classification metric; got {sorted(keys)}")
    else:
        raise ValueError(f"unknown task_type: {task_type!r}")


def validate_topology(topology: Topology) -> None:
    """Raise ``ValueError`` if ``topology`` is not a well-formed, renderable graph.

    Checks: all required keys present; ``model_type`` is a non-empty string; at least one
    node; node ids unique and non-empty; node ``kind`` legal; every edge endpoint references
    an existing node; ``meta`` includes ``task_type``.
    """
    for key in ("model_type", "nodes", "edges", "meta"):
        if key not in topology:
            raise ValueError(f"topology missing required key {key!r}")
    if not isinstance(topology["model_type"], str) or not topology["model_type"]:
        raise ValueError("topology.model_type must be a non-empty string")
    nodes = topology["nodes"]
    if not nodes:
        raise ValueError("topology must declare at least one node")
    ids: set[str] = set()
    for node in nodes:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(f"topology node has an invalid id: {node!r}")
        if node_id in ids:
            raise ValueError(f"duplicate topology node id: {node_id!r}")
        ids.add(node_id)
        if node.get("kind") not in NODE_KINDS:
            raise ValueError(f"topology node {node_id!r} has illegal kind {node.get('kind')!r}; legal kinds are {NODE_KINDS}")
    for edge in topology["edges"]:
        for endpoint in ("src", "dst"):
            ref = edge.get(endpoint)
            if ref not in ids:
                raise ValueError(f"topology edge {endpoint} {ref!r} references an unknown node")
    if "task_type" not in topology["meta"]:
        raise ValueError("topology.meta must include 'task_type'")


def legal_event_order(events: Sequence[TrainingEvent]) -> bool:
    """Return ``True`` iff ``events`` form a legal training sequence.

    Legal means: non-empty; the first event is ``training_start`` and the last is
    ``training_end``, each appearing exactly once; every type is a known
    :data:`TrainingEventType`; and ``seq`` is non-decreasing across the sequence.
    """
    if not events:
        return False
    types = [event.type for event in events]
    if types[0] != "training_start" or types[-1] != "training_end":
        return False
    if types.count("training_start") != 1 or types.count("training_end") != 1:
        return False
    if any(event_type not in TRAINING_EVENT_TYPES for event_type in types):
        return False
    seqs = [event.seq for event in events]
    return all(earlier <= later for earlier, later in zip(seqs, seqs[1:]))
