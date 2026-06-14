"""Tests for the FastAPI app factory and generic health router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient

from juniper_service_core.app import create_app


def test_health_liveness_endpoint():
    client = TestClient(create_app())
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_readiness_endpoint():
    client = TestClient(create_app())
    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_app_metadata_is_configurable():
    app = create_app(title="My Service", version="9.9.9")
    assert app.title == "My Service"
    assert app.version == "9.9.9"


def test_extra_routers_are_mounted():
    extra = APIRouter()

    @extra.get("/v1/custom")
    async def custom():
        return {"hello": "world"}

    client = TestClient(create_app(routers=[extra]))
    # Provided router is mounted...
    assert client.get("/v1/custom").json() == {"hello": "world"}
    # ...and the generic health router is still present.
    assert client.get("/v1/health").json() == {"status": "ok"}
