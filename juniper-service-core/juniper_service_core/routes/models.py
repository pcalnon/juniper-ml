"""Request models for the generic routes (WS-2 / OUT-11 T2).

The model-agnostic subset of cascor's ``api/models/training.py``. cascor's ``TrainingParams``
hard-codes 24 cascade-specific fields (``candidate_pool_size`` / ``correlation_threshold`` /
…) and its ``TrainingStartRequest`` carries a ``dataset`` block with a hard-wired two-spiral
generator -- both stay in the cascor adapter. The generic surface keeps only what any model
service needs: inline training arrays and an **open** parameter dict (a service validates and
applies its own parameters by overriding ``ServiceLifecycleManager.update_params``).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["InlineData", "TrainingStartRequest", "SnapshotCreateRequest", "ReplayControlRequest"]


class InlineData(BaseModel):
    """Training arrays supplied directly in the request body.

    Row-major nested lists; the route converts them to ``float32`` numpy arrays at the
    boundary (numpy at the interface, model-core D2). ``val_x`` / ``val_y`` are optional.
    Shapes are model-defined: ``(n, F)`` for tabular models. (Sequence ``(n, T, F)`` inputs
    plus their auxiliary arrays -- ``dt`` / ``readout_mask`` -- are a documented follow-up;
    the generic inline path covers the 2-D case the conformance stub exercises.)
    """

    train_x: list
    train_y: list
    val_x: list | None = None
    val_y: list | None = None


class TrainingStartRequest(BaseModel):
    """Optional body for ``POST /training/start``.

    ``inline_data`` supplies the dataset; ``params`` is an open dict merged into the
    lifecycle's parameter store (a service interprets it); ``epochs`` is a convenience that is
    recorded under ``params["max_epochs"]``. A service that builds datasets from a generator
    spec (cascor's spiral) adds that field in its own request subclass.
    """

    model_config = ConfigDict(extra="forbid")

    inline_data: InlineData | None = None
    params: dict | None = None
    epochs: int | None = None


class SnapshotCreateRequest(BaseModel):
    """Optional body for ``POST /snapshots`` -- a human-readable label for the snapshot."""

    model_config = ConfigDict(extra="forbid")

    description: str = ""


class ReplayControlRequest(BaseModel):
    """Body for ``POST /snapshots/{id}/replay/control``.

    ``action`` is one of play / pause / seek / speed / range / stop / status; the other fields
    are the action's parameters (``seek`` uses ``time_index``; ``speed`` uses ``value``;
    ``range`` uses ``start`` + ``end``) and are forwarded only when set.
    """

    model_config = ConfigDict(extra="forbid")

    action: str
    time_index: int | None = None
    value: float | None = None
    start: int | None = None
    end: int | None = None
