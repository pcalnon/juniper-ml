"""Tests that pin the public API surface.

Consumers import ``from juniper_observability import …``. If a symbol
is removed or renamed, this test fails first — protecting the cross-
service contract.
"""

import juniper_observability


EXPECTED_PUBLIC_SYMBOLS = {
    # Version
    "__version__",
    # Constants
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
    # Prometheus utils
    "get_prometheus_app",
    "set_build_info",
    # Prometheus collector helpers (idempotent registration patterns)
    "lazy_register_or_reuse",
    "register_fresh",
    "register_info_or_update",
    "register_or_reuse",
    # Sentry
    "DEFAULT_SENTRY_TRACES_SAMPLE_RATE",
    "configure_sentry",
}


def test_all_expected_symbols_are_exported():
    """Every consumer-facing symbol must be in ``__all__`` and importable."""
    for symbol in EXPECTED_PUBLIC_SYMBOLS:
        assert hasattr(juniper_observability, symbol), f"missing public symbol: {symbol}"


def test_no_unexpected_public_symbols():
    """``__all__`` must not silently grow without test acknowledgement."""
    declared = set(juniper_observability.__all__)
    extra = declared - EXPECTED_PUBLIC_SYMBOLS
    missing = EXPECTED_PUBLIC_SYMBOLS - declared
    assert not extra, f"juniper_observability.__all__ has undeclared symbols: {extra}"
    assert not missing, f"juniper_observability.__all__ missing expected symbols: {missing}"


def test_version_is_stable_string():
    """0.1.1 — first stable promotion after the juniper-data soak (R2.1.3).

    Released as the post-alpha stable. The previous alphas
    (``0.1.0a0`` first publish, ``0.1.1a0`` post-data-migration
    iteration) remain on PyPI for reproducibility but consumers should
    pin ``juniper-observability>=0.1.1`` going forward.
    """
    assert juniper_observability.__version__ == "0.1.1"


def test_constants_match_documented_values():
    """The R1.1/R1.2 contract values must not drift."""
    assert juniper_observability.UNMATCHED_ENDPOINT_LABEL == "_unmatched"
    assert juniper_observability.READINESS_HEADER == "X-Juniper-Readiness"
    assert juniper_observability.LIVENESS_TICK_BUDGET_MS == 250
    assert juniper_observability.LIVENESS_STALENESS_SECONDS == 30.0
    assert juniper_observability.HEADER_X_REQUEST_ID == "X-Request-ID"
