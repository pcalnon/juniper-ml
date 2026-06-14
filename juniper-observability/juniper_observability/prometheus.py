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


def set_build_info(
    namespace: str,
    version: str,
    *,
    git_sha: str | None = None,
    build_date: str | None = None,
) -> None:
    """Register a ``<namespace>_build`` Info metric with build provenance.

    Always carries ``version`` + ``python_version``. When ``git_sha`` /
    ``build_date`` are supplied (the build-provenance path — see juniper-ml
    ``notes/BUILD_PROVENANCE_DESIGN_2026-06-14.md``) they are added as
    additional Info labels so the deployed source revision is visible in
    Prometheus/Grafana. They are omitted when ``None`` (e.g. local dev or
    a pre-rollout image), keeping the metric clean rather than emitting
    empty-string labels.

    Idempotent via :func:`juniper_observability.register_info_or_update`:
    a second call in the same process (test fixture re-creating the
    app, in-process service restart, etc.) re-fetches the existing
    ``Info`` collector and overwrites its labels with the latest values
    rather than raising ``ValueError: Duplicated timeseries``.

    Args:
        namespace: Metric namespace prefix (e.g. ``"juniper_data"``).
        version: Application version string.
        git_sha: Source git revision baked into the image at build time
            (keyword-only, optional).
        build_date: ISO-8601 build timestamp baked into the image at
            build time (keyword-only, optional).
    """
    from juniper_observability.prometheus_helpers import register_info_or_update

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    labels = {"version": version, "python_version": python_version}
    if git_sha is not None:
        labels["git_sha"] = git_sha
    if build_date is not None:
        labels["build_date"] = build_date
    register_info_or_update(
        f"{namespace}_build",
        f"Build information for {namespace.replace('_', '-')} service",
        **labels,
    )
