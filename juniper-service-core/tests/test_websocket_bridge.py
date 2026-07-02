"""Coverage for the lifecycle -> WebSocket broadcast bridge default-construction path (C-4a).

``test_t2_websocket.py`` always passes an explicit ``ws_manager`` to ``attach_websocket``; this
pins the omitted-``ws_manager`` default-construction branch.
"""

from __future__ import annotations

from fastapi import FastAPI
from juniper_model_core.conformance.reference import ReferenceGrowableModel

from juniper_service_core.lifecycle import ServiceLifecycleManager
from juniper_service_core.websocket import WebSocketManager, attach_websocket


def test_attach_websocket_constructs_default_manager() -> None:
    app = FastAPI()
    manager = ServiceLifecycleManager(ReferenceGrowableModel())
    try:
        ws_manager = attach_websocket(app, manager=manager)  # no ws_manager -> default constructed
        assert isinstance(ws_manager, WebSocketManager)
        assert app.state.ws_manager is ws_manager
        assert app.state.lifecycle is manager
    finally:
        manager.shutdown()
