"""Generic liveness/readiness health router shared by Juniper model services.

Provides a minimal, model-agnostic ``/v1/health`` (liveness) and ``/v1/health/ready``
(readiness) pair. Services that need richer dependency-probe readiness (the
``ReadinessResponse`` contract) layer that on via ``juniper-observability``; this router
is the baseline every service gets for free from the app factory.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Response body for the generic health endpoints."""

    status: str


def health_router() -> APIRouter:
    """Build the generic health :class:`~fastapi.APIRouter`.

    Returns a router exposing:

    * ``GET /v1/health`` -- liveness, returns ``{"status": "ok"}``.
    * ``GET /v1/health/ready`` -- readiness, returns ``{"status": "ready"}``.
    """
    router = APIRouter(tags=["health"])

    @router.get("/v1/health", response_model=HealthStatus)
    async def health() -> HealthStatus:
        """Liveness probe: the process is up and serving requests."""
        return HealthStatus(status="ok")

    @router.get("/v1/health/ready", response_model=HealthStatus)
    async def health_ready() -> HealthStatus:
        """Readiness probe: the service is ready to accept traffic."""
        return HealthStatus(status="ready")

    return router
