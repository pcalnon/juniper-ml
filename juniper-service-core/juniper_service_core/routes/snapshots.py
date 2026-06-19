"""Generic snapshot routes (WS-2 / OUT-11 T2 step 1b).

The model-agnostic subset of cascor's ``api/routes/snapshots.py``: save / list / get a
snapshot, plus the three load operations -- **restore** (inspect), **retrain** (fresh run from
the loaded network), **resume** (continue training). All operate over the injected lifecycle.
Snapshot persistence is enabled only when the service constructs its ``ServiceLifecycleManager``
with a model-core ``ModelSerializer``; otherwise these routes return ``501 Not Implemented``.
Replay (``/replay`` + ``/replay/control``) and dataset-swap history stay deferred / cascor-bound.

Disk I/O runs in a threadpool (``run_in_threadpool``) so the event loop stays responsive
regardless of how heavy the injected serializer is.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from juniper_service_core.lifecycle.snapshots import SnapshotNotFoundError
from juniper_service_core.routes.dependencies import get_lifecycle
from juniper_service_core.routes.models import SnapshotCreateRequest
from juniper_service_core.routes.responses import success_response

logger = logging.getLogger("juniper_service_core.routes.snapshots")

router = APIRouter(prefix="/v1/snapshots", tags=["snapshots"])


def _require_enabled(lifecycle) -> None:
    """Raise ``501`` if the service did not configure snapshots (no serializer was injected)."""
    if not lifecycle.snapshots_enabled():
        raise HTTPException(status_code=501, detail="Snapshots are not configured for this service")


@router.post("")
async def save_snapshot(request: Request, body: SnapshotCreateRequest | None = None) -> dict:
    """Persist the current model + lifecycle state as a new snapshot."""
    lifecycle = get_lifecycle(request)
    _require_enabled(lifecycle)
    description = body.description if body is not None else ""
    try:
        result = await run_in_threadpool(lifecycle.save_snapshot, description)
        return success_response(result)
    except RuntimeError as exc:  # e.g. no model attached
        logger.debug("Save snapshot rejected: %s", exc)
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("")
async def list_snapshots(request: Request) -> dict:
    """List all stored snapshots' metadata."""
    lifecycle = get_lifecycle(request)
    _require_enabled(lifecycle)
    return success_response(await run_in_threadpool(lifecycle.list_snapshots))


@router.get("/{snapshot_id}")
async def get_snapshot(request: Request, snapshot_id: str) -> dict:
    """Return one snapshot's metadata (``404`` if absent)."""
    lifecycle = get_lifecycle(request)
    _require_enabled(lifecycle)
    meta = await run_in_threadpool(lifecycle.get_snapshot, snapshot_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")
    return success_response(meta)


async def _load_operation(request: Request, snapshot_id: str, method_name: str, operation: str) -> dict:
    """Shared body for restore / retrain / resume: 501 if disabled, 404 if absent, 409 if active."""
    lifecycle = get_lifecycle(request)
    _require_enabled(lifecycle)
    method = getattr(lifecycle, method_name)
    try:
        result = await run_in_threadpool(method, snapshot_id)
    except SnapshotNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}") from exc
    except RuntimeError as exc:  # e.g. training is active
        logger.debug("Snapshot %s rejected: %s", operation, exc)
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result["operation"] = operation
    return success_response(result)


@router.post("/{snapshot_id}/restore")
async def restore_snapshot(request: Request, snapshot_id: str) -> dict:
    """Load a snapshot for inspection (FSM -> ``INVESTIGATING``)."""
    return await _load_operation(request, snapshot_id, "load_snapshot", "restore")


@router.post("/{snapshot_id}/retrain")
async def retrain_snapshot(request: Request, snapshot_id: str) -> dict:
    """Load a snapshot's model + clear its history (FSM -> ``STOPPED``) for a fresh run."""
    return await _load_operation(request, snapshot_id, "restore_for_retrain", "retrain")


@router.post("/{snapshot_id}/resume")
async def resume_snapshot(request: Request, snapshot_id: str) -> dict:
    """Load a snapshot's model + history (FSM -> ``RESUME_READY``) to continue training."""
    return await _load_operation(request, snapshot_id, "resume_from_snapshot", "resume")
