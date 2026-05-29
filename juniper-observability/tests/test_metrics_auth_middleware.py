"""Tests for ``MetricsAuthMiddleware`` (SEC-16 promotion to shared lib).

Promoted to ``juniper-observability`` 0.3.0 from the inline copies that
shipped in juniper-data #157 and juniper-cascor #313. This suite is the
canonical contract; the consumer-side tests in those repos exist only
to pin the re-export shape after migration.

Tests drive the middleware directly via raw ASGI scopes (no FastAPI /
Starlette TestClient) so the package keeps its stdlib-only runtime
posture — ``juniper-observability`` does not depend on starlette at
runtime, and importing it must not pull starlette into ``sys.modules``.
"""

from __future__ import annotations

from typing import Any

import pytest

from juniper_observability import (
    METRICS_DEFAULT_TRUSTED_IPS,
    MetricsAuthMiddleware,
    normalize_client_ip,
    parse_trusted_networks,
)


# ---------------------------------------------------------------------------
# Helpers — minimal ASGI driver
# ---------------------------------------------------------------------------


async def _stub_app(scope, receive, send) -> None:
    """ASGI stub that responds 200 with body ``b"ok"``."""
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": b"ok"})


class _Captured:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


async def _empty_receive() -> dict[str, Any]:  # pragma: no cover — /metrics never reads body
    return {"type": "http.disconnect"}


def _scope(client_ip: str | None = "127.0.0.1") -> dict[str, Any]:
    return {
        "type": "http",
        "method": "GET",
        "path": "/metrics",
        "headers": [],
        "client": (client_ip, 12345) if client_ip is not None else None,
    }


async def _drive(middleware, scope) -> _Captured:
    captured = _Captured()
    await middleware(scope, _empty_receive, captured.send)
    return captured


def _status_of(captured: _Captured) -> int:
    start = next(m for m in captured.messages if m["type"] == "http.response.start")
    return int(start["status"])


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def test_default_constant_is_loopback_only() -> None:
    assert METRICS_DEFAULT_TRUSTED_IPS == ("127.0.0.1", "::1")


def test_parse_trusted_networks_widens_bare_ipv4_to_host_network() -> None:
    nets = parse_trusted_networks(["127.0.0.1"])
    assert len(nets) == 1
    assert nets[0].prefixlen == 32


def test_parse_trusted_networks_widens_bare_ipv6_to_host_network() -> None:
    nets = parse_trusted_networks(["::1"])
    assert len(nets) == 1
    assert nets[0].prefixlen == 128


def test_parse_trusted_networks_accepts_mixed_cidr_and_bare() -> None:
    nets = parse_trusted_networks(["172.18.0.0/16", "127.0.0.1", "fd00::/8"])
    assert len(nets) == 3


def test_parse_trusted_networks_fails_loud_on_invalid_cidr() -> None:
    with pytest.raises(ValueError, match=r"172\.18\.0\.0/164"):
        parse_trusted_networks(["172.18.0.0/164"])


def test_normalize_client_ip_strips_ipv6_zone_id() -> None:
    addr = normalize_client_ip("fe80::1%eth0")
    assert str(addr) == "fe80::1"


def test_normalize_client_ip_unwraps_ipv4_mapped_ipv6() -> None:
    addr = normalize_client_ip("::ffff:172.18.0.5")
    assert str(addr) == "172.18.0.5"


def test_normalize_client_ip_returns_plain_ipv4_unchanged() -> None:
    addr = normalize_client_ip("172.18.0.5")
    assert str(addr) == "172.18.0.5"


# ---------------------------------------------------------------------------
# Middleware — IP allowlist behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestMetricsAuthMiddleware:
    async def test_default_loopback_allows_127_0_0_1(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app)
        captured = await _drive(middleware, _scope("127.0.0.1"))
        assert _status_of(captured) == 200

    async def test_default_loopback_rejects_other(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app)
        captured = await _drive(middleware, _scope("172.18.0.5"))
        assert _status_of(captured) == 403

    async def test_cidr_v4_match_allows(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["172.18.0.0/16"])
        captured = await _drive(middleware, _scope("172.18.0.5"))
        assert _status_of(captured) == 200

    async def test_cidr_v4_miss_rejects(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["172.18.0.0/16"])
        captured = await _drive(middleware, _scope("10.0.0.5"))
        assert _status_of(captured) == 403

    async def test_mixed_cidr_and_literal_entries_allowed(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["172.18.0.0/16", "10.0.0.99"])
        captured = await _drive(middleware, _scope("10.0.0.99"))
        assert _status_of(captured) == 200

    async def test_cidr_v6_match_allows(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["fd00::/8"])
        captured = await _drive(middleware, _scope("fd12::1"))
        assert _status_of(captured) == 200

    async def test_ipv4_mapped_ipv6_against_ipv4_cidr(self) -> None:
        """Docker-bridge regression: ``::ffff:172.18.0.5`` must unwrap to
        ``172.18.0.5`` before CIDR membership."""
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["172.18.0.0/16"])
        captured = await _drive(middleware, _scope("::ffff:172.18.0.5"))
        assert _status_of(captured) == 200

    async def test_ipv6_zone_id_is_stripped(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["fe80::/10"])
        captured = await _drive(middleware, _scope("fe80::1%eth0"))
        assert _status_of(captured) == 200

    async def test_malformed_client_address_rejects(self) -> None:
        """``"testclient"`` (Starlette TestClient default) cannot match any
        CIDR — the ``except ValueError`` keeps ``allowed = False``."""
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["0.0.0.0/0"])
        captured = await _drive(middleware, _scope("not-an-ip"))
        assert _status_of(captured) == 403

    async def test_missing_client_in_scope_rejects(self) -> None:
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["127.0.0.1"])
        captured = await _drive(middleware, _scope(None))
        assert _status_of(captured) == 403

    async def test_invalid_cidr_raises_at_init(self) -> None:
        with pytest.raises(ValueError, match=r"172\.18\.0\.0/164"):
            MetricsAuthMiddleware(_stub_app, trusted_ips=["172.18.0.0/164"])

    async def test_non_http_scope_passes_through(self) -> None:
        """WebSocket / lifespan scopes must not 403 — the middleware only
        guards HTTP."""
        ws_called = False

        async def _ws_app(scope, receive, send):
            nonlocal ws_called
            ws_called = True

        middleware = MetricsAuthMiddleware(_ws_app, trusted_ips=["127.0.0.1"])
        scope = {"type": "websocket", "path": "/ws", "client": ("untrusted-host", 12345)}
        await middleware(scope, _empty_receive, _Captured().send)
        assert ws_called, "non-HTTP scope must fall through to wrapped app"

    async def test_passes_response_through_unmodified(self) -> None:
        """When allowed, the wrapped app's response start + body messages
        flow through verbatim."""
        middleware = MetricsAuthMiddleware(_stub_app, trusted_ips=["127.0.0.1"])
        captured = await _drive(middleware, _scope("127.0.0.1"))
        assert _status_of(captured) == 200
        body_msg = next(m for m in captured.messages if m["type"] == "http.response.body")
        assert body_msg["body"] == b"ok"


# ---------------------------------------------------------------------------
# Module-shape invariant — ``MetricsAuthMiddleware`` is plain-ASGI
# ---------------------------------------------------------------------------


def test_metrics_auth_module_does_not_import_starlette_directly() -> None:
    """``MetricsAuthMiddleware`` is a plain-ASGI middleware (it does not
    subclass ``starlette.middleware.base.BaseHTTPMiddleware``). The source
    file itself must not import starlette — even though the package as a
    whole depends on starlette via ``PrometheusMiddleware`` and
    ``RequestIdMiddleware``, keeping this module starlette-free lets
    future consumers strip the dep if they only want the metrics
    allowlist surface.
    """
    import inspect

    from juniper_observability.middleware import metrics_auth as metrics_auth_module

    source = inspect.getsource(metrics_auth_module)
    assert "import starlette" not in source
    assert "from starlette" not in source
