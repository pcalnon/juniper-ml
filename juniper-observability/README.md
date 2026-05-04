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

## Release workflow

`juniper-observability` publishes independently from the root `juniper-ml` meta-package.

1. Update `juniper-observability/pyproject.toml` and `juniper-observability/CHANGELOG.md` for the new package version.
2. Push a tag named `juniper-observability-vX.Y.Z` to run `.github/workflows/publish-observability.yml`.
3. The workflow builds the sdist and wheel from this subdirectory, validates them with `twine check`, and uploads the `juniper-observability-dist` artifact for seven days.
4. The TestPyPI job downloads that artifact, publishes with OIDC trusted publishing, retries installation while the TestPyPI index catches up, and imports `juniper_observability` to verify the release.
5. The PyPI job downloads the same artifact and publishes it to PyPI after the TestPyPI verification job succeeds.

Use `workflow_dispatch` on `publish-observability.yml` only to re-fire an existing tag. The workflow uses GitHub-hosted `ubuntu-latest` runners and SHA-pinned actions; if it is moved to self-hosted runners, verify runner compatibility with the pinned `actions/upload-artifact` and `actions/download-artifact` versions before releasing.

## License

MIT — see [LICENSE](../LICENSE).
