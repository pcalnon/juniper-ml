"""Tests for ``PrometheusMiddleware`` (R1.1 cardinality contract)."""

from unittest.mock import MagicMock, patch

import pytest

from juniper_observability import UNMATCHED_ENDPOINT_LABEL, PrometheusMiddleware

pytest.importorskip("prometheus_client")


class TestPrometheusMiddleware:
    """METRICS-MON R1.1 / seed-01: bounded label cardinality."""

    @staticmethod
    def _build_request(*, method: str, url_path: str, route_template: str | None) -> MagicMock:
        request = MagicMock()
        request.url.path = url_path
        request.method = method
        if route_template is None:
            request.scope = {}
        else:
            route = MagicMock()
            route.path = route_template
            request.scope = {"route": route}
        return request

    @pytest.mark.asyncio
    async def test_matched_route_uses_template(self):
        with patch("prometheus_client.Counter") as MockCounter, patch("prometheus_client.Histogram") as MockHistogram:
            request_count = MagicMock()
            unmatched_count = MagicMock()
            MockCounter.side_effect = [request_count, unmatched_count]
            mock_histogram = MagicMock()
            MockHistogram.return_value = mock_histogram

            mw = PrometheusMiddleware(app=MagicMock(), service_name="test", namespace="juniper_data")

            response = MagicMock()
            response.status_code = 200

            async def call_next(_):
                return response

            request = self._build_request(method="GET", url_path="/v1/datasets/abc", route_template="/v1/datasets/{dataset_id}")
            await mw.dispatch(request, call_next)

            request_count.labels.assert_called_once_with(method="GET", endpoint="/v1/datasets/{dataset_id}", status="200")
            unmatched_count.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_unmatched_route_collapses_to_label(self):
        with patch("prometheus_client.Counter") as MockCounter, patch("prometheus_client.Histogram") as MockHistogram:
            request_count = MagicMock()
            unmatched_count = MagicMock()
            MockCounter.side_effect = [request_count, unmatched_count]
            MockHistogram.return_value = MagicMock()

            mw = PrometheusMiddleware(app=MagicMock(), service_name="test", namespace="juniper_data")

            response = MagicMock()
            response.status_code = 404

            async def call_next(_):
                return response

            request = self._build_request(method="GET", url_path="/totally/unknown", route_template=None)
            await mw.dispatch(request, call_next)

            request_count.labels.assert_called_once_with(method="GET", endpoint=UNMATCHED_ENDPOINT_LABEL, status="404")
            unmatched_count.labels.assert_called_once_with(method="GET")

    @pytest.mark.asyncio
    async def test_cardinality_bounded_under_high_entropy_paths(self):
        """Stress test: 50 distinct unmatched URLs produce exactly 1 endpoint label value."""
        with patch("prometheus_client.Counter") as MockCounter, patch("prometheus_client.Histogram") as MockHistogram:
            request_count = MagicMock()
            unmatched_count = MagicMock()
            MockCounter.side_effect = [request_count, unmatched_count]
            MockHistogram.return_value = MagicMock()

            mw = PrometheusMiddleware(app=MagicMock(), service_name="test", namespace="juniper_data")

            response = MagicMock()
            response.status_code = 404

            async def call_next(_):
                return response

            for i in range(50):
                request = self._build_request(method="GET", url_path=f"/attacker/{i}/abc", route_template=None)
                await mw.dispatch(request, call_next)

            distinct_endpoints = {call.kwargs["endpoint"] for call in request_count.labels.call_args_list}
            assert distinct_endpoints == {UNMATCHED_ENDPOINT_LABEL}
            assert unmatched_count.labels.call_count == 50

    @pytest.mark.asyncio
    async def test_namespace_prefix_applied_to_all_metric_names(self):
        with patch("prometheus_client.Counter") as MockCounter, patch("prometheus_client.Histogram") as MockHistogram:
            MockCounter.return_value = MagicMock()
            MockHistogram.return_value = MagicMock()

            PrometheusMiddleware(app=MagicMock(), service_name="test", namespace="juniper_data")

            counter_names = [call.args[0] for call in MockCounter.call_args_list]
            assert "juniper_data_http_requests_total" in counter_names
            assert "juniper_data_http_unmatched_requests_total" in counter_names
            histogram_names = [call.args[0] for call in MockHistogram.call_args_list]
            assert "juniper_data_http_request_duration_seconds" in histogram_names

    @pytest.mark.asyncio
    async def test_empty_namespace_produces_unprefixed_names(self):
        with patch("prometheus_client.Counter") as MockCounter, patch("prometheus_client.Histogram") as MockHistogram:
            MockCounter.return_value = MagicMock()
            MockHistogram.return_value = MagicMock()

            PrometheusMiddleware(app=MagicMock(), service_name="test", namespace="")

            counter_names = [call.args[0] for call in MockCounter.call_args_list]
            assert "http_requests_total" in counter_names
            assert "http_unmatched_requests_total" in counter_names
