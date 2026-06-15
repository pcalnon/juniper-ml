"""FastAPI application factory for Juniper model services.

:func:`create_app` builds a model-agnostic FastAPI app, mounts the generic health
router, then includes any service-supplied routers. It carries **no** model,
classification, or training logic -- those live in the owning service and are passed in
as ``routers``. This keeps the service-tier scaffolding reusable across every Juniper
model service (WS-2).
"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import APIRouter, FastAPI

from juniper_service_core.health import health_router


def create_app(
    *,
    title: str = "Juniper Service",
    version: str = "0.1.0",
    routers: Iterable[APIRouter] = (),
) -> FastAPI:
    """Create a FastAPI app with the generic health router plus any extra routers.

    Args:
        title: OpenAPI title for the app.
        version: OpenAPI version string for the app.
        routers: Additional service routers to mount after the health router.

    Returns:
        A configured :class:`~fastapi.FastAPI` instance. Model-agnostic by design.
    """
    app = FastAPI(title=title, version=version)
    app.include_router(health_router())
    for router in routers:
        app.include_router(router)
    return app
