"""Generic metrics routes (WS-2 / OUT-11 T2).

The de-cascored core of cascor's ``api/routes/metrics.py`` -- the current metric snapshot and
the per-epoch history. ``metrics`` is the model's own open dict (``{mse, rmse, r2}`` for a
regressor, ``{loss, accuracy}`` for a classifier); no classification shape is assumed. The
``/metrics/transport`` counters (WebSocket diagnostics) belong with the websocket subsystem
(step 2) and are not part of this surface.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from juniper_service_core.routes.dependencies import get_lifecycle
from juniper_service_core.routes.responses import success_response

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(request: Request) -> dict:
    """Return the current metric snapshot (epoch, n_units, latest metrics)."""
    return success_response(get_lifecycle(request).get_metrics())


@router.get("/history")
async def get_metrics_history(request: Request, count: int | None = Query(default=None, ge=1)) -> dict:
    """Return the per-epoch metric history (most-recent ``count`` entries, or all)."""
    return success_response(get_lifecycle(request).get_metrics_history(count))
