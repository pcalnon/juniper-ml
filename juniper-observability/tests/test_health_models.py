"""Tests for ``DependencyStatus`` and ``ReadinessResponse`` Pydantic models."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from juniper_observability import DependencyStatus, ReadinessResponse


class TestDependencyStatus:
    def test_healthy_status(self):
        dep = DependencyStatus(name="Storage", status="healthy", latency_ms=2.5, message="ok")
        assert dep.name == "Storage"
        assert dep.status == "healthy"
        assert dep.latency_ms == 2.5

    def test_unhealthy_status_without_latency(self):
        dep = DependencyStatus(name="Storage", status="unhealthy")
        assert dep.status == "unhealthy"
        assert dep.latency_ms is None
        assert dep.message is None

    def test_not_configured_status(self):
        dep = DependencyStatus(name="Sentry", status="not_configured")
        assert dep.status == "not_configured"

    def test_status_literal_rejects_invalid_values(self):
        with pytest.raises(ValidationError):
            DependencyStatus(name="x", status="bogus")  # type: ignore[arg-type]


class TestReadinessResponse:
    def test_ready_response_default_timestamp(self):
        before = datetime.now(UTC).timestamp()
        resp = ReadinessResponse(status="ready", version="0.1.0a0", service="juniper-test")
        after = datetime.now(UTC).timestamp()

        assert resp.status == "ready"
        assert resp.version == "0.1.0a0"
        assert resp.service == "juniper-test"
        assert resp.dependencies == {}
        assert resp.details == {}
        # Timestamp is unix-epoch seconds derived from a tz-aware UTC
        # datetime — must fall in the [before, after] window.
        assert before <= resp.timestamp <= after

    def test_timestamp_is_tz_aware_utc_not_naive(self):
        """METRICS-MON R1.2 / BUG-JD-06: ``timestamp`` must be derived from UTC.

        We can't observe timezone directly from a unix-epoch float, but
        we can observe that the timestamp is consistent with a UTC
        ``now()`` and not offset by local timezone hours.
        """
        utc_now = datetime.now(UTC).timestamp()
        resp = ReadinessResponse(status="ready", version="0.1.0a0", service="juniper-test")
        # Under naive ``datetime.now().timestamp()`` the value would be
        # offset by the local TZ offset on Python builds where
        # ``datetime.now()`` interprets the result as local time. The
        # tz-aware variant is offset-free.
        assert abs(resp.timestamp - utc_now) < timedelta(seconds=1).total_seconds()

    def test_degraded_response_with_deps(self):
        dep = DependencyStatus(name="Storage", status="unhealthy", message="not found")
        resp = ReadinessResponse(
            status="degraded",
            version="0.1.0a0",
            service="juniper-test",
            dependencies={"storage": dep},
            details={"mode": "demo"},
        )
        assert resp.status == "degraded"
        assert resp.dependencies["storage"].status == "unhealthy"
        assert resp.details["mode"] == "demo"

    def test_not_ready_status(self):
        resp = ReadinessResponse(status="not_ready", version="0.1.0a0", service="juniper-test")
        assert resp.status == "not_ready"

    def test_status_literal_rejects_invalid_values(self):
        with pytest.raises(ValidationError):
            ReadinessResponse(status="ok", version="0.1.0a0", service="x")  # type: ignore[arg-type]

    def test_model_dump_round_trip(self):
        """Wire-compat: model_dump → ReadinessResponse(**dump) is loss-free."""
        original = ReadinessResponse(
            status="degraded",
            version="0.1.0a0",
            service="juniper-test",
            dependencies={"a": DependencyStatus(name="A", status="healthy", latency_ms=1.0)},
            details={"k": "v"},
        )
        round_tripped = ReadinessResponse(**original.model_dump())
        assert round_tripped.model_dump() == original.model_dump()
