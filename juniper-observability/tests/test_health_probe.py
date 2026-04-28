"""Tests for ``probe_dependency``."""

from unittest.mock import patch

from juniper_observability import probe_dependency


class TestProbeDependency:
    def test_healthy_returns_status_with_latency(self):
        with patch("juniper_observability.health.probe.urllib.request.urlopen") as mock:
            mock.return_value.__enter__ = lambda s: s
            mock.return_value.__exit__ = lambda s, *a: None
            result = probe_dependency("DataService", "http://localhost:8100/v1/health/live")
        assert result.status == "healthy"
        assert result.name == "DataService"
        assert result.latency_ms is not None and result.latency_ms >= 0
        assert result.message == "http://localhost:8100/v1/health/live"

    def test_unhealthy_on_connection_refused(self):
        with patch("juniper_observability.health.probe.urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
            result = probe_dependency("Test", "http://localhost:9999/v1/health/live", timeout=1.0)
        assert result.status == "unhealthy"
        assert result.latency_ms is not None
        assert "ConnectionRefusedError" in (result.message or "")

    def test_unhealthy_on_timeout(self):
        from urllib.error import URLError

        with patch("juniper_observability.health.probe.urllib.request.urlopen", side_effect=URLError("timeout")):
            result = probe_dependency("Slow", "http://localhost:8100/v1/health/live", timeout=0.1)
        assert result.status == "unhealthy"
        assert "URLError" in (result.message or "")

    def test_probe_swallows_arbitrary_exceptions(self):
        """Any exception type must be converted to ``unhealthy`` rather than bubbling."""
        with patch("juniper_observability.health.probe.urllib.request.urlopen", side_effect=ValueError("weird")):
            result = probe_dependency("Quirky", "http://localhost:8100/v1/health/live")
        assert result.status == "unhealthy"
        assert "ValueError" in (result.message or "")
