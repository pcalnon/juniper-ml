"""Starlette / ASGI middleware shared across Juniper services."""

from juniper_observability.middleware.metrics_auth import (
    METRICS_DEFAULT_TRUSTED_IPS,
    MetricsAuthMiddleware,
    TrustedNetwork,
    normalize_client_ip,
    parse_trusted_networks,
)
from juniper_observability.middleware.prometheus import PrometheusMiddleware
from juniper_observability.middleware.request_id import RequestIdMiddleware, request_id_var

__all__ = [
    "METRICS_DEFAULT_TRUSTED_IPS",
    "MetricsAuthMiddleware",
    "PrometheusMiddleware",
    "RequestIdMiddleware",
    "TrustedNetwork",
    "normalize_client_ip",
    "parse_trusted_networks",
    "request_id_var",
]
