"""Synchronous dependency-probe helper used by readiness handlers.

The probe is a one-shot HTTP GET against a peer service's
``/v1/health/live`` endpoint. ``probe_dependency`` swallows every
exception and converts it into a ``DependencyStatus`` with status
``unhealthy``; this is intentional — a probe failure must never bubble
out of the readiness handler and crash the request.

R4.2 will introduce an async variant that does not block the event
loop. Until then, callers running inside async handlers should be aware
that ``probe_dependency`` is sync and best invoked via
``asyncio.to_thread`` if probe latency is non-trivial.
"""

import time
import urllib.request

from juniper_observability.health.models import DependencyStatus


def probe_dependency(name: str, url: str, timeout: float = 5.0) -> DependencyStatus:
    """Probe a dependency health endpoint. Returns status with latency.

    Args:
        name: Human-readable name of the dependency for logs/dashboards.
        url: Health endpoint URL to probe (typically ``/v1/health/live``).
        timeout: Connection timeout in seconds.

    Returns:
        ``DependencyStatus`` with:
        - ``status="healthy"`` when the GET returns without raising.
        - ``status="unhealthy"`` for any exception (connection refused,
          timeout, non-2xx via ``HTTPError``); the exception type and
          message are encoded into the ``message`` field.
        - ``latency_ms`` always populated from a monotonic clock.
    """
    start = time.monotonic()
    try:
        urllib.request.urlopen(url, timeout=timeout)  # nosec B310 — internal health probe
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name=name, status="healthy", latency_ms=round(latency, 1), message=url)
    except Exception as e:  # noqa: BLE001 — probe surfaces every failure mode
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(
            name=name,
            status="unhealthy",
            latency_ms=round(latency, 1),
            message=f"{url} — {type(e).__name__}: {e}",
        )
