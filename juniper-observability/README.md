# juniper-observability

Shared observability primitives for the Juniper ML platform.

## What's in here

- **Health models** (`DependencyStatus`, `ReadinessResponse`) — Pydantic models for the standard `/v1/health/ready` response shape used by every Juniper server.
- **Probe utility** (`probe_dependency`) — synchronous HTTP health-check helper.
- **Logging** (`JuniperJsonFormatter`, `configure_logging`) — structured-JSON logging with `request_id` propagation.
- **Middleware** (`RequestIdMiddleware`, `PrometheusMiddleware`) — Starlette middlewares applied by every Juniper server. The Prometheus middleware bounds label cardinality per the R1.1 contract.
- **Constants** (`UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS`) — pinned values from the R1.1, R1.2, and R1.3 cross-service contracts.
- **Prometheus utilities** (`get_prometheus_app`, `set_build_info`).
- **Sentry init** (`configure_sentry`) — with the SEC-10 `before_send` hook always installed.

## Install

```bash
pip install juniper-observability                          # core only
pip install "juniper-observability[prometheus]"            # + Prometheus middleware/utilities
pip install "juniper-observability[sentry]"                # + Sentry init
pip install "juniper-observability[all]"                   # everything
```

## Per-service metrics stay in each repo

This package intentionally exposes only **cross-cutting** observability infrastructure. Service-specific metric definitions (training-loop counters, dataset-gen histograms, websocket gauges, etc.) live in their owning repo and use the lazy-init pattern with `prometheus_client` directly.

## Design + migration

See [`notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](../notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) in the parent juniper-ml repo for the full design and the 5-PR migration sequence.

## License

MIT — see [LICENSE](../LICENSE).
