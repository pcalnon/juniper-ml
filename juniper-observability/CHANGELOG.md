# Changelog

All notable changes to the `juniper-observability` package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) pre-release identifiers.

## [Unreleased]

## [0.1.1a] - 2026-04-28

### Changed

- First publishable alpha. Republishes the `0.1.0a*` source tree under a clean PEP 440 alpha version (`0.1.1a`) following pending-publisher reconfiguration on TestPyPI / PyPI. No source changes from `0.1.0a2`; the bump is required to obtain a fresh, never-uploaded version after the earlier publish attempts under `0.1.0a0` / `0.1.0a2` failed at the trusted-publisher handshake.

### Notes

- `juniper-observability` is not yet wired into the `juniper-ml[all]` extras. It will be added once the alpha graduates and downstream services start importing from it as part of the METRICS-MON R2.1 migration.

## [0.1.0a0] - 2026-04-28 (unpublished)

Initial source drop, never released to PyPI / TestPyPI.

### Added

- **Health models** — Pydantic `DependencyStatus` and `ReadinessResponse` for the standard `/v1/health/ready` response shape used by every Juniper server.
- **`probe_dependency`** — synchronous HTTP health-check helper that returns a populated `DependencyStatus`.
- **Structured logging** — `JuniperJsonFormatter` plus the `configure_logging` helper, with `request_id` propagation across log records.
- **Middleware**
  - `RequestIdMiddleware` — assigns / forwards the `X-Request-ID` header and binds it to the logging context.
  - `PrometheusMiddleware` — request-count + latency middleware with bounded label cardinality per the R1.1 cross-service contract (`UNMATCHED_ENDPOINT_LABEL`).
- **Cross-service constants** — `UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS` (pinned from the R1.1 / R1.2 / R1.3 contracts).
- **Prometheus utilities** — `get_prometheus_app` (mountable ASGI app) and `set_build_info` (for setting the `*_build_info` gauge from `pyproject.toml` metadata).
- **Sentry init** — `configure_sentry` with the SEC-10 `before_send` hook always installed.
- **Package extras** — `[prometheus]`, `[sentry]`, `[all]`.
- **Docs** — design + 5-PR migration sequence in `notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (parent juniper-ml repo).

### Notes

- Per-service metric definitions intentionally stay in their owning repo and use the lazy-init pattern with `prometheus_client` directly. This package only exposes cross-cutting infrastructure.

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/juniper-observability-v0.1.1a...HEAD
[0.1.1a]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1a
