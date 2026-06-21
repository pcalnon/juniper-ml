"""WebSocket subsystem (WS-2 / OUT-11 T2 step 2).

The model-agnostic websocket surface extracted from cascor's ``api/websocket/`` -- a thread-safe
connection :class:`~juniper_service_core.websocket.manager.WebSocketManager` (sequencing, replay
buffer, oversized-message chunking, thread-safe broadcast), the generic message builders, the
control-path security primitives, and the two stream handlers (``/ws/training`` metrics stream +
``/ws/control`` command channel). Command dispatch is decoupled behind an injectable
:class:`~juniper_service_core.websocket.commands.CommandExecutor`, and live frames reach connected
clients through :func:`~juniper_service_core.websocket.bridge.attach_websocket`.

Wire it into a service like the HTTP routes::

    from juniper_service_core import create_app
    from juniper_service_core.lifecycle import ServiceLifecycleManager
    from juniper_service_core.routes import build_routers
    from juniper_service_core.websocket import (
        LifecycleCommandExecutor, attach_websocket, build_websocket_router,
    )

    manager = ServiceLifecycleManager(my_model)
    app = create_app(routers=[*build_routers(), build_websocket_router()])
    attach_websocket(
        app,
        manager=manager,
        command_executor=LifecycleCommandExecutor(manager, start=my_start_handler),
    )

cascor's worker stream and its ``cascade_add`` / ``candidate_progress`` frames are intentionally
out of scope (worker subsystem = step 3; cascade frames stay cascor-side -- design §5.6).

Importing this subpackage requires ``fastapi``; the :mod:`juniper_service_core` top-level package
keeps every name here off the eager import path (PEP 562 lazy export) so ``import
juniper_service_core`` stays dependency-free.
"""

from __future__ import annotations

from juniper_service_core.websocket.bridge import attach_websocket, build_frame_sink
from juniper_service_core.websocket.commands import DEFAULT_COMMANDS, CommandExecutor, LifecycleCommandExecutor
from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket, validate_control_origin
from juniper_service_core.websocket.control_stream import control_stream_handler
from juniper_service_core.websocket.manager import DEFAULT_WS_ENDPOINTS, ReplayOutOfRange, WebSocketManager, ws_authenticate
from juniper_service_core.websocket.messages import (
    create_chunked_message,
    create_control_ack_message,
    create_event_message,
    create_initial_metrics_message,
    create_metrics_message,
    create_state_message,
    create_topology_message,
)
from juniper_service_core.websocket.router import build_websocket_router, build_worker_router
from juniper_service_core.websocket.training_stream import training_stream_handler
from juniper_service_core.websocket.worker_stream import attach_worker_pool, worker_stream_handler

__all__ = [
    # Connection manager + auth
    "WebSocketManager",
    "ws_authenticate",
    "ReplayOutOfRange",
    "DEFAULT_WS_ENDPOINTS",
    # Command dispatch (the adapter seam)
    "CommandExecutor",
    "LifecycleCommandExecutor",
    "DEFAULT_COMMANDS",
    # Control-path security
    "validate_control_origin",
    "LeakyBucket",
    "HandshakeCooldown",
    # Stream handlers + router
    "training_stream_handler",
    "control_stream_handler",
    "build_websocket_router",
    # Worker channel (step 3b -- /ws/workers)
    "worker_stream_handler",
    "build_worker_router",
    "attach_worker_pool",
    # Broadcast bridge
    "attach_websocket",
    "build_frame_sink",
    # Message builders
    "create_metrics_message",
    "create_state_message",
    "create_topology_message",
    "create_event_message",
    "create_chunked_message",
    "create_initial_metrics_message",
    "create_control_ack_message",
]
