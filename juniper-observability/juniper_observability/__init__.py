"""``juniper-observability`` — shared observability primitives for Juniper services.

Single source of truth for ``DependencyStatus`` / ``ReadinessResponse``
Pydantic models, the dependency-probe utility, structured-JSON logging,
the R1.1/R1.2/R1.3 contract constants, and the Starlette middlewares
(``RequestIdMiddleware``, ``PrometheusMiddleware``) that every Juniper
server applies.

Per-service metric definitions (training-loop counters, dataset-gen
histograms, websocket gauges, etc.) intentionally stay in their owning
repo — only cross-cutting infrastructure lives here.

See ``notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md``
in juniper-ml for the design and migration plan.
"""

from juniper_observability._version import __version__
from juniper_observability.constants import (
    HEADER_X_REQUEST_ID,
    LIVENESS_STALENESS_SECONDS,
    LIVENESS_TICK_BUDGET_MS,
    READINESS_HEADER,
    UNMATCHED_ENDPOINT_LABEL,
)
from juniper_observability.health.models import DependencyStatus, ReadinessResponse
from juniper_observability.health.probe import probe_dependency
from juniper_observability.logging import (
    DEFAULT_LOG_FORMAT_PLAIN,
    LOG_FORMAT_JSON,
    JuniperJsonFormatter,
    configure_logging,
)
from juniper_observability.middleware import PrometheusMiddleware, RequestIdMiddleware, request_id_var
from juniper_observability.prometheus import get_prometheus_app, set_build_info
from juniper_observability.sentry import DEFAULT_SENTRY_TRACES_SAMPLE_RATE, configure_sentry

__all__ = [
    # Version
    "__version__",
    # Constants (R1.1/R1.2/R1.3 contract)
    "HEADER_X_REQUEST_ID",
    "LIVENESS_STALENESS_SECONDS",
    "LIVENESS_TICK_BUDGET_MS",
    "READINESS_HEADER",
    "UNMATCHED_ENDPOINT_LABEL",
    # Health
    "DependencyStatus",
    "ReadinessResponse",
    "probe_dependency",
    # Logging
    "DEFAULT_LOG_FORMAT_PLAIN",
    "JuniperJsonFormatter",
    "LOG_FORMAT_JSON",
    "configure_logging",
    # Middleware
    "PrometheusMiddleware",
    "RequestIdMiddleware",
    "request_id_var",
    # Prometheus utilities
    "get_prometheus_app",
    "set_build_info",
    # Sentry
    "DEFAULT_SENTRY_TRACES_SAMPLE_RATE",
    "configure_sentry",
]
