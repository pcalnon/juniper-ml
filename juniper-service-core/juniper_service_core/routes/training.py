"""Generic training-control routes (WS-2 / OUT-11 T2).

The model-agnostic subset of cascor's ``api/routes/training.py`` -- start/stop/pause/resume/
reset/status plus the parameter get/patch. The cascor-coupled bits stay in the cascor adapter:
the hard-wired two-spiral generator (``_generate_spiral_data``), the candidate-pool / live
dataset-swap endpoints, and the cascade-specific param validation. Every handler reads the
lifecycle off ``app.state`` (:func:`~juniper_service_core.routes.dependencies.get_lifecycle`)
and wraps its result in the shared :func:`~juniper_service_core.routes.responses.success_response`
envelope.
"""

from __future__ import annotations

import logging

import numpy as np
from fastapi import APIRouter, HTTPException, Request

from juniper_service_core.routes.dependencies import get_lifecycle
from juniper_service_core.routes.models import TrainingStartRequest
from juniper_service_core.routes.responses import success_response

logger = logging.getLogger("juniper_service_core.routes.training")

router = APIRouter(prefix="/v1/training", tags=["training"])


def _to_array(values: list) -> np.ndarray:
    """Convert request-body nested lists to a ``float32`` array (numpy at the boundary, D2)."""
    return np.asarray(values, dtype=np.float32)


@router.post("/start")
async def start_training(request: Request, body: TrainingStartRequest | None = None) -> dict:
    """Start a training run from inline data.

    ``params`` (if present) is merged into the lifecycle's parameter store before the run;
    ``epochs`` is recorded as ``params["max_epochs"]``. Returns the post-transition status.
    """
    lifecycle = get_lifecycle(request)
    if body is None or body.inline_data is None:
        raise HTTPException(status_code=400, detail="No training data provided (inline_data is required)")
    inline = body.inline_data
    X = _to_array(inline.train_x)
    y = _to_array(inline.train_y)
    X_val = _to_array(inline.val_x) if inline.val_x is not None else None
    y_val = _to_array(inline.val_y) if inline.val_y is not None else None

    params = dict(body.params or {})
    if body.epochs is not None:
        params["max_epochs"] = body.epochs
    if params:
        lifecycle.update_params(params)

    try:
        result = lifecycle.start_training(X, y, X_val, y_val, dataset_name="inline")
        return success_response(result)
    except RuntimeError as exc:
        # No model attached / a run already active -- surface the reason (409) rather than 500.
        logger.debug("Start training rejected: %s", exc)
        raise HTTPException(status_code=409, detail=f"Training cannot be started: {exc}") from exc


@router.post("/stop")
async def stop_training(request: Request) -> dict:
    """Stop the current run (idempotent)."""
    return success_response(get_lifecycle(request).stop_training())


@router.post("/pause")
async def pause_training(request: Request) -> dict:
    """Pause an active run at its next event boundary."""
    lifecycle = get_lifecycle(request)
    try:
        return success_response(lifecycle.pause_training())
    except RuntimeError as exc:
        logger.debug("Pause rejected: %s", exc)
        raise HTTPException(status_code=409, detail="Training cannot be paused in the current state") from exc


@router.post("/resume")
async def resume_training(request: Request) -> dict:
    """Resume a paused run."""
    lifecycle = get_lifecycle(request)
    try:
        return success_response(lifecycle.resume_training())
    except RuntimeError as exc:
        logger.debug("Resume rejected: %s", exc)
        raise HTTPException(status_code=409, detail="Training cannot be resumed in the current state") from exc


@router.post("/reset")
async def reset_training(request: Request) -> dict:
    """Reset all training state to the idle baseline."""
    return success_response(get_lifecycle(request).reset())


@router.get("/status")
async def get_status(request: Request) -> dict:
    """Return the full lifecycle status (state machine + monitor snapshot)."""
    return success_response(get_lifecycle(request).get_status())


@router.get("/params")
async def get_params(request: Request) -> dict:
    """Return the current training-parameter store."""
    return success_response(get_lifecycle(request).get_training_params())


@router.patch("/params")
async def update_params(request: Request, body: dict) -> dict:
    """Merge runtime parameter updates (PATCH semantics) and return the new store."""
    return success_response(get_lifecycle(request).update_params(body))
