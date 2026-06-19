"""Generic dataset routes (WS-2 / OUT-11 T2).

The de-cascored core of cascor's ``api/routes/dataset.py`` -- dataset metadata (shapes /
counts) and the raw arrays for visualization. Fully model-agnostic: the lifecycle returns
shapes and nested-list arrays without any cascade assumption.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from juniper_service_core.routes.dependencies import get_lifecycle
from juniper_service_core.routes.responses import success_response

router = APIRouter(prefix="/v1/dataset", tags=["dataset"])


@router.get("")
async def get_dataset(request: Request) -> dict:
    """Return dataset metadata (presence, name, sample counts, shapes)."""
    return success_response(get_lifecycle(request).get_dataset())


@router.get("/data")
async def get_dataset_data(request: Request) -> dict:
    """Return the dataset arrays as nested lists for visualization (``data`` is null if none)."""
    return success_response(get_lifecycle(request).get_dataset_data())
