"""Shared FastAPI dependencies for the generic routes (WS-2 / OUT-11 T2).

The de-cascored ``_get_lifecycle`` pattern every cascor route repeated inline: read the
lifecycle orchestrator off ``request.app.state`` and 503 if the service has not wired it yet.
A service mounts its :class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager`
(or a subclass) onto ``app.state.lifecycle`` during startup; every generic route reads it
through :func:`get_lifecycle`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

if TYPE_CHECKING:
    from juniper_service_core.lifecycle.manager import ServiceLifecycleManager

__all__ = ["LIFECYCLE_STATE_ATTR", "get_lifecycle"]

#: The ``app.state`` attribute the generic routes read the lifecycle orchestrator from.
LIFECYCLE_STATE_ATTR = "lifecycle"


def get_lifecycle(request: Request) -> ServiceLifecycleManager:
    """Return the lifecycle orchestrator from ``app.state``, or raise ``503`` if unset.

    The 503 mirrors cascor: a service that has not finished wiring its lifecycle (or has torn
    it down) reports "not ready" rather than a 500 ``AttributeError``.
    """
    lifecycle = getattr(request.app.state, LIFECYCLE_STATE_ATTR, None)
    if lifecycle is None:
        raise HTTPException(status_code=503, detail="Lifecycle manager not initialized")
    return lifecycle
