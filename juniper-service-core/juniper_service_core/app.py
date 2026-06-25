"""FastAPI application factory for Juniper model services.

:func:`create_app` builds a model-agnostic FastAPI app, mounts the generic health
router, then includes any service-supplied routers. It carries **no** model,
classification, or training logic -- those live in the owning service and are passed in
as ``routers``. This keeps the service-tier scaffolding reusable across every Juniper
model service (WS-2).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from fastapi import APIRouter, FastAPI

from juniper_service_core.health import health_router

if TYPE_CHECKING:
    from starlette.types import Lifespan


def create_app(
    *,
    title: str = "Juniper Service",
    version: str = "0.1.0",
    routers: Iterable[APIRouter] = (),
    lifespan: Lifespan[FastAPI] | None = None,
) -> FastAPI:
    """Create a FastAPI app with the generic health router plus any extra routers.

    Args:
        title: OpenAPI title for the app.
        version: OpenAPI version string for the app.
        routers: Additional service routers to mount after the health router.
        lifespan: Optional FastAPI lifespan context manager, forwarded to
            ``FastAPI(lifespan=...)``. Lets a consuming service run startup/shutdown
            hooks (logging configuration, build-info, resource setup/teardown) in a
            lifespan instead of at import time or in its CLI entrypoint. Omit for the
            previous behaviour (no lifespan).

    Returns:
        A configured :class:`~fastapi.FastAPI` instance. Model-agnostic by design.
    """
    app = FastAPI(title=title, version=version, lifespan=lifespan)
    app.include_router(health_router())
    for router in routers:
        app.include_router(router)
    return app
