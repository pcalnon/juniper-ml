"""Prometheus middleware for Juniper services.

METRICS-MON R1.1 / seed-01 contract:

- ``endpoint`` label is set to the resolved Starlette route template
  (e.g. ``/v1/datasets/{dataset_id}``) — never to the raw URL path.
- Requests that do not match any registered route template collapse
  into ``UNMATCHED_ENDPOINT_LABEL`` and increment a separate counter
  ``<namespace>_http_unmatched_requests_total{method}``.
- This bounds Prometheus label cardinality under attacker-controlled
  paths or path-parameter routes; per-repo dashboards relying on the
  unbounded raw-URL fallback have been migrated.

The middleware is service-specific only by virtue of its ``namespace``
prefix — ``juniper_data_*``, ``juniper_cascor_*``, ``juniper_canopy_*``.
Consumers pass their identity at construction time.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from juniper_observability.constants import UNMATCHED_ENDPOINT_LABEL


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP request counts and durations with bounded cardinality.

    Lazily imports ``prometheus_client`` so the broader package can be
    used without the ``[prometheus]`` extra installed.
    """

    def __init__(self, app: object, service_name: str = "juniper-service", namespace: str = "juniper") -> None:
        super().__init__(app)
        from prometheus_client import REGISTRY, Counter, Histogram

        prefix = f"{namespace}_" if namespace else ""

        # Idempotent metric registration. ``Counter`` / ``Histogram``
        # construction registers the collector with the global
        # ``REGISTRY`` and raises ``ValueError`` if the timeseries name
        # is already present. That happens whenever ``PrometheusMiddleware``
        # is instantiated more than once in the same Python process —
        # most commonly during pytest sessions that build multiple
        # ``TestClient(app)`` instances (each ``build_middleware_stack``
        # constructs a fresh middleware), but also after any in-process
        # restart of a service. On the duplicate, re-fetch the existing
        # collector instead of crashing the whole app startup.
        #
        # Same shape as the canopy fix in
        # ``juniper-canopy/src/observability.py:_ensure_canopy_metrics``
        # (cascor PR #205 / canopy V34a). The lookup uses the name as
        # passed to the factory; ``prometheus_client`` registers under
        # both the bare name and the suffixed sample names (``_total``,
        # ``_created``, ``_bucket``, ``_sum``, ``_count``), all pointing
        # at the same collector object.
        def _get_or_create(factory, name, *args, **kwargs):
            try:
                return factory(name, *args, **kwargs)
            except ValueError:
                existing = REGISTRY._names_to_collectors.get(name)
                if existing is None:
                    raise
                return existing

        self._request_count = _get_or_create(
            Counter,
            f"{prefix}http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        self._request_duration = _get_or_create(
            Histogram,
            f"{prefix}http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        )
        self._unmatched_count = _get_or_create(
            Counter,
            f"{prefix}http_unmatched_requests_total",
            "HTTP requests not matching any registered route template",
            ["method"],
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        route = request.scope.get("route")
        template = getattr(route, "path", None) if route is not None else None
        method = request.method
        if template:
            endpoint = template
        else:
            endpoint = UNMATCHED_ENDPOINT_LABEL
            self._unmatched_count.labels(method=method).inc()

        status = str(response.status_code)
        self._request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self._request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        return response
