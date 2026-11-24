"""Tests for the FastAPI app factory and generic health router."""

from __future__ import annotations

from contextlib import asynccontextmanager

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


def test_lifespan_is_forwarded():
    events: list[str] = []

    @asynccontextmanager
    async def lifespan(app):
        events.append("startup")
        yield
        events.append("shutdown")

    app = create_app(lifespan=lifespan)
    # Entering/exiting the TestClient context drives the app's lifespan.
    with TestClient(app) as client:
        assert events == ["startup"]
        assert client.get("/v1/health").json() == {"status": "ok"}
    assert events == ["startup", "shutdown"]


def test_no_lifespan_by_default():
    # The factory works with no lifespan (previous behaviour); startup/shutdown is a no-op.
    with TestClient(create_app()) as client:
        assert client.get("/v1/health").status_code == 200


def test_fastapi_native_telemetry_is_off_on_every_fastapi(monkeypatch):
    """The factory passes FastAPI the telemetry opt-out, whatever its version, so this test never skips.

    From FastAPI 0.142 the merged config is ``app._telemetry``; before that ``telemetry=`` is not a parameter and
    FastAPI keeps it, as given, in ``app.extra``. From 0.143 an omitted ``auto_configure`` takes its default from
    ``FASTAPI_OTEL_AUTO_CONFIGURE`` when the app is built, so the variable is set to ``true`` first: an
    ``auto_configure`` dropped from the factory's ``telemetry=`` then reads ``True``, as the other four switches do
    by default.
    """
    monkeypatch.setenv("FASTAPI_OTEL_AUTO_CONFIGURE", "true")
    app = create_app()
    config = getattr(app, "_telemetry", None)
    if config is None:
        config = app.extra.get("telemetry", {})
    for switch in ("tracing", "metrics", "logs", "operation_spans", "auto_configure"):
        assert config.get(switch) is False, switch
