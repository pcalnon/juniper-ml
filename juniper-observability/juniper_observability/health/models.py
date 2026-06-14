"""Pydantic models for ``/v1/health/ready`` responses.

The R1.2 probe contract pins:

* ``DependencyStatus.status`` is one of {healthy, unhealthy, degraded,
  not_configured}.
* ``ReadinessResponse.status`` is one of {ready, degraded, not_ready};
  HTTP status code is 200 for ready/degraded and 503 for not_ready.
* ``ReadinessResponse.timestamp`` is a unix-epoch float **derived from
  timezone-aware UTC** (resolves the cascor naive-tz drift identified
  during R1.2 implementation; matches juniper-data's BUG-JD-06 fix).

These models are wire-compatible with the per-repo copies they replace.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    """Health status of a single dependency probed during readiness."""

    name: str
    status: Literal["healthy", "unhealthy", "degraded", "not_configured"]
    latency_ms: float | None = None
    message: str | None = None


class ReadinessResponse(BaseModel):
    """Standard ``/v1/health/ready`` response across all Juniper services."""

    status: Literal["ready", "degraded", "not_ready"]
    version: str
    service: str
    # Build provenance (juniper-ml notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md):
    # the source git SHA and ISO-8601 build timestamp baked into the image
    # at build time. ``None`` when the service runs outside a provenance-
    # stamped image (local dev / pre-rollout). Surfaced here so stale-image
    # drift is detectable straight from a readiness probe. Optional with
    # ``None`` defaults — wire-compatible with pre-0.4.0 consumers.
    git_sha: str | None = None
    build_date: str | None = None
    # METRICS-MON R1.2 / BUG-JD-06: timezone-aware UTC. Always epoch
    # seconds from a tz-aware datetime — never naive.
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())
    dependencies: dict[str, DependencyStatus] = Field(default_factory=dict)
    details: dict[str, object] = Field(default_factory=dict)
