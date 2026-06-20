"""WebSocket router factory for Juniper model services (WS-2 / OUT-11 T2 step 2).

:func:`build_websocket_router` returns an :class:`~fastapi.APIRouter` carrying the generic
``/ws/training`` (server-to-client metrics stream) and ``/ws/control`` (client-to-server command)
endpoints, mountable through the app factory exactly like the HTTP routers::

    from juniper_service_core import create_app
    from juniper_service_core.routes import build_routers
    from juniper_service_core.websocket import build_websocket_router

    app = create_app(routers=[*build_routers(), build_websocket_router()])

The paths match cascor's existing ``/ws/training`` / ``/ws/control`` (no ``/v1`` prefix) so WS-6's
A-phase adoption is a drop-in. A service still wires ``app.state.ws_manager`` /
``app.state.command_executor`` (and the live-broadcast bridge) -- see
:func:`~juniper_service_core.websocket.bridge.attach_websocket`.

Requires ``fastapi``; kept off the eager import path (PEP 562 lazy export).
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

from juniper_service_core.websocket.control_stream import control_stream_handler
from juniper_service_core.websocket.training_stream import training_stream_handler

__all__ = ["build_websocket_router"]


def build_websocket_router(*, training: bool = True, control: bool = True) -> APIRouter:
    """Return an APIRouter with the generic websocket endpoints.

    Args:
        training: Mount ``/ws/training`` (the metrics stream). Default ``True``.
        control: Mount ``/ws/control`` (the command channel). Default ``True``.

    Returns:
        An :class:`~fastapi.APIRouter` ready for ``create_app(routers=[...])``.
    """
    router = APIRouter()

    if training:

        @router.websocket("/ws/training")
        async def _training(websocket: WebSocket) -> None:
            await training_stream_handler(websocket)

    if control:

        @router.websocket("/ws/control")
        async def _control(websocket: WebSocket) -> None:
            await control_stream_handler(websocket)

    return router
