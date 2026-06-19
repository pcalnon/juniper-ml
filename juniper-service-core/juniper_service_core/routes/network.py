"""Generic model-introspection routes (WS-2 / OUT-11 T2).

The read-only, model-agnostic subset of cascor's ``api/routes/network.py``: model info and
the topology graph. ``GET /network/topology`` delegates straight to
``model.describe_topology()`` -- the model-core seam the front-end renders without knowing the
concrete model type. The mutating surface (create / delete / weight-patch / manual
hidden-unit add+remove) and ``/network/stats`` are cascade-specific (they assume an indexed,
mutable cascade) and stay in the cascor subclass.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from juniper_service_core.routes.dependencies import get_lifecycle
from juniper_service_core.routes.responses import success_response

router = APIRouter(prefix="/v1/network", tags=["network"])


@router.get("")
async def get_network(request: Request) -> dict:
    """Return model-agnostic model info (type, task, shapes, unit count). Empty if no model."""
    return success_response(get_lifecycle(request).get_network_info())


@router.get("/topology")
async def get_topology(request: Request) -> dict:
    """Return the model's :class:`~juniper_model_core.topology.Topology` graph (404 if no model)."""
    topology = get_lifecycle(request).get_topology()
    if topology is None:
        raise HTTPException(status_code=404, detail="No model attached")
    return success_response(topology)
