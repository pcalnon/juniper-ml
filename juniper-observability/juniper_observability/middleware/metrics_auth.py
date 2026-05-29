"""``MetricsAuthMiddleware`` — IP-allowlist ASGI wrapper for ``/metrics``.

Promoted to ``juniper-observability`` in 0.3.0 from the inline copies
that shipped in juniper-data #157 and juniper-cascor #313. Both
consumer repos imported and adapted the same shape; the promotion
collapses the two duplicates into a single source of truth so the
fail-loud CIDR + IPv6 normalisation contract drifts in lockstep
across the Juniper services.

The middleware is intentionally ASGI-level (not FastAPI) because:

- ``/metrics`` is mounted as an ASGI sub-app by every Juniper service
  (``app.mount("/metrics", get_prometheus_app())``), so the ASGI wrapper
  applies before the wrapped Prometheus app sees the request.
- ASGI-level inspection of ``scope["client"]`` is the canonical way
  to read the real client address without depending on
  ``starlette.requests.Request`` (which itself depends on FastAPI).

Per-service settings (the ``metrics_trusted_ips: list[str]`` Pydantic
field, the ``JUNIPER_<SERVICE>_METRICS_TRUSTED_IPS`` env var, and the
fail-loud validator) intentionally stay in each service's settings
module — only the cross-cutting middleware lives here.

See ``notes/poc/POC_REMEDIATION_PLAN_2026-05-27.md`` in juniper-deploy
§§2.2/3.1 for the rationale and validator-driven design history.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from typing import Awaitable, Callable, MutableMapping, Union

__all__ = [
    "METRICS_DEFAULT_TRUSTED_IPS",
    "MetricsAuthMiddleware",
    "TrustedNetwork",
    "normalize_client_ip",
    "parse_trusted_networks",
]


# Default allowlist consumed when no ``trusted_ips`` arg is passed. Matches
# the per-service ``Settings.metrics_trusted_ips`` defaults across data,
# cascor, and (soon) canopy: loopback only.
METRICS_DEFAULT_TRUSTED_IPS: tuple[str, ...] = ("127.0.0.1", "::1")

#: Type alias for the compiled-network tuple — ``ipaddress.ip_network``
#: returns either an IPv4 or IPv6 network object depending on input.
TrustedNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]

# ASGI type aliases — kept here so the middleware module doesn't pull
# starlette into its import graph (juniper-observability stays a thin
# stdlib + ipaddress shim).
_Scope = MutableMapping[str, object]
_Message = MutableMapping[str, object]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]


def parse_trusted_networks(raw: Iterable[str]) -> tuple[TrustedNetwork, ...]:
    """Compile CIDR strings / bare IP literals into ``ip_network`` objects.

    Bare-IP entries are widened to host networks (``/32`` or ``/128``) by
    ``ip_network(..., strict=False)``. Unparseable entries fail loud at
    init time — operator typos must not silently 403 every scrape. The
    per-service fail-loud Pydantic ``field_validator`` calls this same
    function so the error surfaces at ``Settings()`` construction.

    Raises:
        ValueError: when any ``raw`` entry is neither a valid IP nor a
            valid CIDR. Message names the offending entry.
    """
    nets: list[TrustedNetwork] = []
    for entry in raw:
        try:
            nets.append(ipaddress.ip_network(entry, strict=False))
        except ValueError as exc:
            raise ValueError(f"trusted IP/CIDR entry {entry!r} is not a valid IP or CIDR: {exc}") from exc
    return tuple(nets)


def normalize_client_ip(client_ip: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
    """Strip IPv6 zone-id and unwrap IPv4-mapped IPv6 to its IPv4 form.

    - ``fe80::1%eth0`` → ``fe80::1`` (zone-id rejected by ``ip_address``).
    - ``::ffff:172.18.0.5`` → ``172.18.0.5`` (membership in an IPv4 CIDR
      otherwise returns ``False`` despite the underlying address being
      IPv4 — the exact regression Docker bridges hit when an inbound
      connection is mapped to the host's IPv6 socket).
    """
    if "%" in client_ip:
        client_ip = client_ip.split("%", 1)[0]
    addr = ipaddress.ip_address(client_ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        addr = addr.ipv4_mapped
    return addr


class MetricsAuthMiddleware:
    """ASGI wrapper that restricts a sub-app to a trusted IP allowlist.

    Accepts bare IP literals, CIDR ranges, and a mix of both. IPv6 zone
    identifiers are stripped from the client address; IPv4-mapped IPv6
    addresses are unwrapped before membership check so a Docker
    container appearing as ``::ffff:172.18.0.5`` matches an IPv4
    ``172.18.0.0/16`` range. Unparseable allowlist entries raise at
    init time (fail-loud — operator typos must not silently 403).

    Typical use:

    .. code-block:: python

        from juniper_observability import (
            MetricsAuthMiddleware,
            get_prometheus_app,
        )

        # ``settings.metrics_trusted_ips`` is a per-service Pydantic
        # field (e.g. ``["127.0.0.1", "::1", "172.18.0.0/16"]``).
        app.mount(
            "/metrics",
            MetricsAuthMiddleware(
                get_prometheus_app(),
                trusted_ips=settings.metrics_trusted_ips,
            ),
        )

    Args:
        app: The downstream ASGI app to wrap (typically the prometheus
            ASGI mount). Called only when the client IP matches.
        trusted_ips: Iterable of IP literals and/or CIDR strings.
            ``None`` (the default) uses
            :data:`METRICS_DEFAULT_TRUSTED_IPS` (loopback only).
    """

    def __init__(
        self,
        app: _ASGIApp,
        trusted_ips: Iterable[str] | None = None,
    ) -> None:
        self.app = app
        raw = trusted_ips if trusted_ips is not None else METRICS_DEFAULT_TRUSTED_IPS
        self.networks: tuple[TrustedNetwork, ...] = parse_trusted_networks(raw)

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] == "http":
            allowed = False
            client = scope.get("client")
            client_ip = client[0] if client else None
            if client_ip:
                try:
                    addr = normalize_client_ip(client_ip)
                    allowed = any(addr in net for net in self.networks)
                except ValueError:
                    # Malformed client address (e.g. ``"testclient"``
                    # from Starlette's TestClient default host) — never
                    # match. Tests must spoof a real IP via
                    # ``TestClient(app, client=("127.0.0.1", 12345))``.
                    pass
            if not allowed:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [(b"content-type", b"text/plain; charset=utf-8")],
                    }
                )
                await send({"type": "http.response.body", "body": b"Forbidden"})
                return
        await self.app(scope, receive, send)
