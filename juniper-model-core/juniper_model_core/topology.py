"""The ``describe_topology()`` schema -- the model-agnostic seam the front-end renders.

A model returns a :class:`Topology` (nodes + edges + meta) that canopy draws WITHOUT knowing
the concrete model type. ``model_type`` is an open ``str`` (decision D10), not a closed
enumeration, so adding model #20 costs no edit here -- the whole point of the template
("the cost of model #20 must equal the cost of model #2").
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = ["NodeKind", "NODE_KINDS", "TopologyNode", "TopologyEdge", "Topology"]

#: Legal node kinds -- the union of the cascor (input/hidden/output) and recurrence
#: (memory/reservoir) vocabularies. New model families reuse these where they fit.
NodeKind = Literal["input", "hidden", "output", "memory", "reservoir"]

#: Runtime tuple form of :data:`NodeKind`, for membership checks in validation.
NODE_KINDS: tuple[str, ...] = ("input", "hidden", "output", "memory", "reservoir")


class TopologyNode(TypedDict):
    """One node in the rendered graph."""

    id: str
    kind: NodeKind
    frozen: bool


class TopologyEdge(TypedDict):
    """One directed edge; ``recurrent`` flags a self/temporal feedback connection."""

    src: str
    dst: str
    recurrent: bool


class Topology(TypedDict):
    """The full model-agnostic topology description.

    ``meta`` must include at least ``task_type`` and ``n_units``; models may add extra keys
    (e.g. ``theta`` for an LMU, ``correlation`` for cascor) without changing this schema.
    """

    model_type: str
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    meta: dict[str, Any]
