"""Tests for ``get_prometheus_app`` and ``set_build_info``."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from juniper_observability import get_prometheus_app, set_build_info

pytest.importorskip("prometheus_client")


class TestGetPrometheusApp:
    def test_returns_asgi_app(self):
        app = get_prometheus_app()
        assert callable(app)


class TestSetBuildInfo:
    def test_creates_info_metric_with_namespace_prefix(self):
        with patch("prometheus_client.Info") as MockInfo:
            mock_info = MagicMock()
            MockInfo.return_value = mock_info
            set_build_info("juniper_test", "1.2.3")
        MockInfo.assert_called_once()
        name = MockInfo.call_args.args[0]
        description = MockInfo.call_args.args[1]
        assert name == "juniper_test_build"
        assert "juniper-test" in description

    def test_info_payload_includes_version_and_python_version(self):
        with patch("prometheus_client.Info") as MockInfo:
            mock_info = MagicMock()
            MockInfo.return_value = mock_info
            set_build_info("juniper_test", "1.2.3")
        info_payload = mock_info.info.call_args.args[0]
        assert info_payload["version"] == "1.2.3"
        expected_py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert info_payload["python_version"] == expected_py
