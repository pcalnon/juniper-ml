# Juniper-Recurrence — Prometheus `/metrics` Endpoint: Design

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; build lands in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.1.0 (as-built; aligned with the implementation PR)
**Last Updated**: 2026-06-18

---

> **What this is.** The design for the `juniper-recurrence` application's Prometheus `/metrics`
> endpoint — the deferred "fast-follow" the WS-4b app-build plan (§6 / §14) and the app's own
> `[observability]` extra anticipated. It mirrors the canonical juniper-data / juniper-cascor pattern,
> is built on `juniper-observability`, and is enabled by `juniper-service-core`'s existing `/metrics`
> security exemption. Implementation lands as a single PR in `pcalnon/juniper-recurrence`.

---

## 1. Scope and motivation

The `juniper-recurrence` app (shipped `0.1.0`, on PyPI) exposes train / predict / model / dataset
routes but **no operational telemetry**. Every other Juniper FastAPI service (data, cascor, canopy)
exposes a Prometheus `/metrics` surface gated by an IP allowlist. The app already **declares** the
`[observability]` extra and its pyproject comment flags `/metrics` as a deferred fast-follow; this
design closes that gap.

**In scope:** the `/metrics` endpoint, IP-allowlist auth, HTTP-request metrics, build-info, settings,
graceful-optional behavior when the extra is absent, tests, CI.

**Out of scope:** app-specific domain metrics beyond HTTP + build-info (deferred — §9); a Grafana
dashboard; alert rules.

## 2. The canonical pattern (juniper-data / cascor, via juniper-observability)

`juniper-observability` (`>=0.4.0`) provides the building blocks; juniper-data's `api/app.py` is the
reference wiring:

- `get_prometheus_app()` — the Prometheus exposition ASGI app (`prometheus_client.make_asgi_app()`).
- `MetricsAuthMiddleware(asgi_app, trusted_ips=…)` — wraps that ASGI app with an IP allowlist
  (literals + CIDRs; IPv4-mapped-IPv6 aware; unparseable entries raise at construction).
- `PrometheusMiddleware(app, service_name=…, namespace="juniper")` — records
  `juniper_http_requests_total` + `juniper_http_request_duration_seconds` for every request.
- `set_build_info(service, version, …)` — a build-info `Info` metric (version, python; optional git
  SHA / build date).
- `register_or_reuse(...)` — the idempotent collector helper, for any future app-specific metrics.

Reference wiring (juniper-data, `api/app.py`):

```python
if settings.metrics_enabled:
    app.mount("/metrics", MetricsAuthMiddleware(get_prometheus_app(), settings.metrics_trusted_ips))
```

This composes with the security stack because `/metrics` is in `juniper_service_core`'s
`EXEMPT_PATHS` (SEC-16): `SecurityMiddleware` skips API-key auth for `/metrics`, and
`MetricsAuthMiddleware` IP-gates it instead.

## 3. Design decisions

### 3.1 Endpoint path — `/metrics`, not `/v1/metrics`

`juniper_service_core.middleware.EXEMPT_PATHS` already contains exactly `/metrics` and `/metrics/`
(SEC-16, mirroring juniper-data). Mounting at `/metrics` therefore inherits the API-key exemption for
free and matches the cross-service Prometheus convention (data / cascor / canopy all use `/metrics`).
The WS-4b plan's loose "/v1/metrics" wording is **superseded** by `/metrics` for this reason. The
app's functional routes remain under `/v1/*`; `/metrics` is the conventional, deliberately-unversioned
scrape path.

### 3.2 Auth model — `MetricsAuthMiddleware` IP allowlist

Two composing layers, identical to juniper-data:

1. `SecurityMiddleware` (API-key auth + rate limit) **skips** `/metrics` (service-core `EXEMPT_PATHS`).
2. `MetricsAuthMiddleware` gates `/metrics` by an **IP allowlist** (`metrics_trusted_ips`).

Prometheus scrapers authenticate by network position, not API keys. The default allowlist is
**loopback only** (`["127.0.0.1", "::1"]`, mirroring juniper-data); Docker / compose deployments
extend it via `JUNIPER_RECURRENCE_METRICS_TRUSTED_IPS` to include the compose-network CIDR.

### 3.3 Metrics emitted

- **HTTP** — `PrometheusMiddleware(service_name="juniper-recurrence")` →
  `juniper_http_requests_total{method,path,status}` + `juniper_http_request_duration_seconds`. **No
  router edits required** — the middleware captures every request.
- **Build-info** — `set_build_info("juniper_recurrence", __version__)` → `juniper_recurrence_build_info`
  Info metric (version + python; git SHA / build date if available). The namespace is the underscored
  service name — Prometheus metric names disallow hyphens.
- **Default process / GC metrics** from `prometheus_client`'s default registry.

App-specific domain counters (train / predict counts, last-training metrics) are deferred (§9); the
HTTP + build-info surface is the meaningful v1, and `register_or_reuse` is the sanctioned path when
they land.

### 3.4 Settings (`Settings`, env prefix `JUNIPER_RECURRENCE_`)

| Field | Type | Default | Notes |
|---|---|---|---|
| `metrics_enabled` | `bool` | `True` | Mounts `/metrics` when true (and observability importable) |
| `metrics_trusted_ips` | `list[str]` | `["127.0.0.1", "::1"]` | IP literals / CIDRs; a field-validator rejects unparseable entries early (mirrors juniper-data) |

Env examples: `JUNIPER_RECURRENCE_METRICS_ENABLED=false`;
`JUNIPER_RECURRENCE_METRICS_TRUSTED_IPS='["127.0.0.1","::1","172.18.0.0/16"]'`.

### 3.5 Graceful-optional observability + pin bump

`[observability]` stays an **optional** extra. `app.py` guards the import: if `juniper_observability`
is absent, the app still builds and runs and `/metrics` is simply not mounted (a warning is logged
when `metrics_enabled` is true, so the misconfiguration is visible). The extra is bumped
**`juniper-observability>=0.3.1` → `juniper-observability[prometheus]>=0.4.0`** — `>=0.4.0` is the
floor that provides `set_build_info`, and the `[prometheus]` marker pulls `prometheus-client` (which
`juniper-observability` keeps optional, so the bare package would `ModuleNotFoundError` at scrape time).

## 4. Architecture / wiring (`app.py`)

The metrics wiring is added inside `build_app()` **between `SecurityHeadersMiddleware` and
`SecurityMiddleware`** (so `SecurityMiddleware` is still added last and stays the outermost handler):

```python
# After RequestBodyLimit + SecurityHeaders, before SecurityMiddleware:
if settings.metrics_enabled:
    try:
        from juniper_observability import (
            MetricsAuthMiddleware,
            PrometheusMiddleware,
            get_prometheus_app,
            set_build_info,
        )
    except ImportError:
        logger.warning(
            "metrics_enabled but juniper-observability is not installed; "
            "/metrics will not be mounted (install the [observability] extra)."
        )
    else:
        application.add_middleware(PrometheusMiddleware, service_name=settings.service_name)
        # underscored namespace -> metric name juniper_recurrence_build_info
        set_build_info(settings.service_name.replace("-", "_"), __version__)
        application.mount(
            "/metrics",
            MetricsAuthMiddleware(get_prometheus_app(), trusted_ips=settings.metrics_trusted_ips),
        )
```

**Middleware ordering.** `PrometheusMiddleware` is added **before** `SecurityMiddleware`, so under
Starlette's LIFO execution `SecurityMiddleware` remains the outermost handler — the canonical
cascor / canopy / data invariant, asserted by `test_app_smoke`. Consequently unauthenticated or
rate-limited requests are rejected by `SecurityMiddleware` **before** `PrometheusMiddleware` runs, so
they add no metric cardinality (the more secure choice). `PrometheusMiddleware` records requests that
pass the security gate (200s plus app-level 4xx/5xx); the `/metrics` mount is reached only for
trusted IPs.

## 5. Test matrix

`tests/test_metrics.py`, guarded by `pytest.importorskip("juniper_observability")` and using
`juniper_observability.testing.reset_prometheus_registry` to avoid cross-test collector collisions:

| Test | Asserts |
|---|---|
| trusted-IP scrape | `GET /metrics` from `127.0.0.1` → `200`, Prometheus content-type, body contains `juniper_recurrence_build_info` |
| untrusted-IP | app built with `metrics_trusted_ips=["10.0.0.0/8"]` → `GET /metrics` → `403` |
| API-key exempt | `GET /metrics` with no `X-API-Key` → **not** `401` (the service-core exemption holds) |
| disabled | `metrics_enabled=False` → `GET /metrics` → `404` (not mounted) |
| HTTP counter | after a request, `juniper_http_requests_total` is present in the scrape |
| graceful-optional | import-guard path (monkeypatch the import to raise) → app builds, `/metrics` `404`, warning logged |

## 6. CI changes

`ci-recurrence-app.yml` installs `.[test,observability]` (currently `.[test]`) so the metrics tests
execute on the 3.12 / 3.13 / 3.14 matrix. `importorskip` keeps them green for contributors without
the extra installed.

## 7. Risks and guardrails

| Risk | Guardrail |
|---|---|
| Prometheus collector double-registration across app rebuilds / tests | `register_or_reuse` / observability's idempotent helpers; `reset_prometheus_registry` in test fixtures |
| `/metrics` accidentally requiring an API key | service-core `EXEMPT_PATHS` already exempts it; a test asserts no-key → not `401` |
| Over-permissive default allowlist | default loopback-only; Docker extends explicitly via env |
| Unparseable CIDR silently accepted | settings field-validator **and** `MetricsAuthMiddleware` both reject at construction |
| RK-6 (classification leak) | metrics are operational only; no model-output / `argmax` assumptions |
| observability extra absent at runtime | guarded import; app still serves; warning logged |

## 8. Out of scope / future

- App-specific domain metrics (train / predict counters, last-training `mse` / `r2` gauges) via
  `register_or_reuse` — a fast-follow once the operational surface is in.
- Grafana dashboard + alert rules (juniper-deploy).
- A `/metrics` surface for the model package — N/A; it is a library, not a service.

## 9. Implementation plan (one PR, `pcalnon/juniper-recurrence`)

1. `pyproject.toml` — bump the `[observability]` extra to `juniper-observability[prometheus]>=0.4.0`.
2. `juniper_recurrence/settings.py` — add `metrics_enabled`, `metrics_trusted_ips` + validator.
3. `juniper_recurrence/app.py` — guarded metrics wiring (§4).
4. `tests/test_metrics.py` — the §5 matrix.
5. `.github/workflows/ci-recurrence-app.yml` — install `.[test,observability]`.

Worktree off `juniper-recurrence` `main`; PR; no merge without Paul's explicit signal.

## 10. Cross-references

- WS-4b app build plan (§6 endpoint surface, §14 deferred `/metrics`): [`JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md)
- Canonical recurrence roadmap: [`JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md)
- Idempotent collector helpers: [`observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`](observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md)
- Reference wiring (cross-repo): `juniper-data/juniper_data/api/app.py`; `juniper-observability/juniper_observability/{prometheus.py, middleware/metrics_auth.py, middleware/prometheus.py}`
