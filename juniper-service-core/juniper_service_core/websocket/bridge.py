"""Lifecycle -> WebSocket broadcast bridge (WS-2 / OUT-11 T2 step 2; resolves FW-3).

Wires a :class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager`'s live frames
onto a :class:`~juniper_service_core.websocket.manager.WebSocketManager` so the ``/ws/training``
channel pushes updates in real time. The push source is exactly what steps 1a/1c built:

* **Live training.** The manager's per-event sink emits a ``{"type": "metrics"|"state", ...}``
  frame on each model-core ``TrainingEvent`` (epoch_end -> metrics, the rest -> state). The
  manager's ``frame_sink`` runs on the training thread; this bridge routes it through
  ``broadcast_from_thread`` (the thread-safe asyncio bridge).
* **Replay.** The manager passes its ``frame_sink`` to ``ReplaySession.on_frame`` (the hook 1c
  added "for exactly this"), so replay frames push live too -- closing design follow-up **FW-3**.

:func:`attach_websocket` is the one-stop wiring a service calls during app construction:
``app.state.ws_manager`` + (optional) ``app.state.command_executor`` + the frame-sink hook. The
stream handlers capture the serving event loop themselves on connect, so no startup hook is
needed for ``broadcast_from_thread`` to work.

Requires ``fastapi``; kept off the eager import path (PEP 562 lazy export).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from juniper_service_core.websocket.manager import WebSocketManager
from juniper_service_core.websocket.messages import create_event_message, create_metrics_message, create_state_message

if TYPE_CHECKING:
    from fastapi import FastAPI

    from juniper_service_core.lifecycle.manager import ServiceLifecycleManager
    from juniper_service_core.websocket.commands import CommandExecutor

__all__ = ["build_frame_sink", "attach_websocket"]

#: Frame ``type`` -> message-envelope builder. The manager emits ``metrics`` / ``state`` frames;
#: an unknown type degrades to the generic ``event`` envelope rather than dropping the frame.
_FRAME_BUILDERS = {
    "metrics": create_metrics_message,
    "state": create_state_message,
    "event": create_event_message,
}


def build_frame_sink(ws_manager: WebSocketManager):
    """Return a ``frame_sink`` that converts manager frames to envelopes and broadcasts them.

    The returned callable takes a ``{"type": ..., "data": {...}}`` frame (as the manager emits),
    wraps it in the matching message envelope, and hands it to
    :meth:`~juniper_service_core.websocket.manager.WebSocketManager.broadcast_from_thread`
    (thread-safe; a no-op until a client connects and the serving loop is captured).
    """

    def _sink(frame: dict) -> None:
        builder = _FRAME_BUILDERS.get(frame.get("type", "event"), create_event_message)
        ws_manager.broadcast_from_thread(builder(frame.get("data", {})))

    return _sink


def attach_websocket(
    app: FastAPI,
    *,
    manager: ServiceLifecycleManager,
    ws_manager: WebSocketManager | None = None,
    command_executor: CommandExecutor | None = None,
) -> WebSocketManager:
    """Wire a manager + websocket manager onto an app and connect the live-broadcast bridge.

    Sets ``app.state.lifecycle`` / ``app.state.ws_manager`` (and ``app.state.command_executor`` if
    given), then installs the manager's ``frame_sink`` so live-training and replay frames push to
    connected ``/ws/training`` clients. Idempotent on ``app.state``. The websocket **router** is
    mounted separately via :func:`~juniper_service_core.websocket.router.build_websocket_router`
    (so a service controls route ordering through ``create_app``).

    Args:
        app: The FastAPI app to wire.
        manager: The lifecycle orchestrator (also mounted as ``app.state.lifecycle``).
        ws_manager: The websocket connection manager; a default is constructed if omitted.
        command_executor: Optional control-channel executor for ``/ws/control``.

    Returns:
        The :class:`WebSocketManager` in use (the passed one, or the freshly constructed default).
    """
    if ws_manager is None:
        ws_manager = WebSocketManager()
    app.state.lifecycle = manager
    app.state.ws_manager = ws_manager
    if command_executor is not None:
        app.state.command_executor = command_executor
    manager.set_frame_sink(build_frame_sink(ws_manager))
    return ws_manager
