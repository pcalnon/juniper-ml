"""Prometheus utilities (ASGI app + build-info Info metric).

These helpers wrap ``prometheus_client`` so consumers don't need to
import the SDK directly. Both functions are lazy — ``prometheus_client``
is only imported when the helper is called, so the package can be
installed without the ``[prometheus]`` extra and these helpers will
simply raise at call time.
"""

import sys


def get_prometheus_app():
    """Return the ASGI app for ``/metrics`` via ``make_asgi_app()``.

    The returned app should typically be wrapped by a service-specific
    auth middleware (e.g. juniper-data's SEC-16 ``MetricsAuthMiddleware``
    IP allowlist) before being mounted.

    Returns:
        ASGI application serving Prometheus metrics in the standard
        scrape format.
    """
    from prometheus_client import make_asgi_app

    return make_asgi_app()


def set_build_info(namespace: str, version: str) -> None:
    """Register a ``<namespace>_build`` Info metric with version + python_version.

    Idempotent against the global ``prometheus_client.REGISTRY``: a
    second call in the same process (test fixture re-creating the app,
    in-process service restart, etc.) re-fetches the existing ``Info``
    collector and updates its labels rather than raising
    ``ValueError: Duplicated timeseries``.

    Args:
        namespace: Metric namespace prefix (e.g. ``"juniper_data"``).
        version: Application version string.
    """
    from prometheus_client import REGISTRY, Info

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    metric_name = f"{namespace}_build"
    try:
        info = Info(metric_name, f"Build information for {namespace.replace('_', '-')} service")
    except ValueError:
        # Already registered — re-use the existing collector. ``Info``
        # registers under both the bare name and the ``_info`` suffixed
        # sample name; the lookup with the bare name returns the same
        # collector object.
        existing = REGISTRY._names_to_collectors.get(metric_name)
        if existing is None:
            raise
        info = existing
    info.info({"version": version, "python_version": python_version})
