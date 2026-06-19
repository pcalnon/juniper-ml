"""Generic HTTP routes for Juniper model services (WS-2 / OUT-11 T2).

The model-agnostic route surface extracted from cascor's ``api/routes/`` -- training control,
metrics, dataset, and model introspection -- all operating over an injected
:class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager` (read off
``app.state.lifecycle``). Mount them via the app factory::

    from juniper_service_core import create_app
    from juniper_service_core.routes import build_routers

    app = create_app(title="my-model-service", routers=build_routers())
    app.state.lifecycle = ServiceLifecycleManager(model=my_model)

These routers bake the ``/v1`` version prefix (matching the generic health router at
``/v1/health``), so ``create_app(routers=build_routers())`` serves them at ``/v1/training``,
``/v1/metrics``, ``/v1/dataset`` and ``/v1/network``. A service layers its model-specific
routes (cascor: ``/network`` mutators, ``/decision-boundary``, snapshots, live dataset swap)
alongside.

Importing this subpackage requires ``fastapi``; the :mod:`juniper_service_core` top-level
package keeps it off the eager import path (PEP 562 lazy export).
"""

from __future__ import annotations

from fastapi import APIRouter

from juniper_service_core.routes import dataset, metrics, network, snapshots, training
from juniper_service_core.routes.dependencies import LIFECYCLE_STATE_ATTR, get_lifecycle
from juniper_service_core.routes.responses import ResponseEnvelope, error_response, success_response

__all__ = [
    "build_routers",
    "training_router",
    "metrics_router",
    "dataset_router",
    "network_router",
    "snapshots_router",
    "get_lifecycle",
    "success_response",
    "error_response",
    "ResponseEnvelope",
    "LIFECYCLE_STATE_ATTR",
]

#: The individual generic routers (each with its own ``/v1/training`` … subprefix).
training_router: APIRouter = training.router
metrics_router: APIRouter = metrics.router
dataset_router: APIRouter = dataset.router
network_router: APIRouter = network.router
snapshots_router: APIRouter = snapshots.router


def build_routers() -> list[APIRouter]:
    """Return the generic model-service routers, ready for ``create_app(routers=...)``.

    Order is stable (training, metrics, dataset, network, snapshots) for deterministic OpenAPI
    output. The snapshot routes self-report ``501`` until a service injects a model serializer.
    """
    return [training_router, metrics_router, dataset_router, network_router, snapshots_router]
