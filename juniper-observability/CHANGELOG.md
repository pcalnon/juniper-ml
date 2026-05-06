# Changelog

All notable changes to the `juniper-observability` package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) pre-release identifiers.

## [Unreleased]

### Added

- ``juniper_observability.prometheus_helpers`` — four idempotent
  ``prometheus_client`` collector helpers retiring the ~10 inline
  copies of the same try/except pattern that had accumulated in
  consumer repos through 2026-05-04. Public API:
  - ``register_or_reuse(factory, name, *args, **kwargs)`` —
    adopt-existing on duplicate (the default choice for almost every
    call site; samples preserved, latest call's args ignored).
  - ``register_fresh(factory, name, *args, **kwargs)`` —
    drop-and-recreate on duplicate (samples discarded, latest call's
    args take effect). Use only when test fixtures or migrations
    intentionally want different buckets/labels.
  - ``register_info_or_update(name, description, **info_labels)`` —
    sugar over ``register_or_reuse`` for the ``Info`` collector type.
  - ``lazy_register_or_reuse(factory, name, *args, **kwargs)`` —
    cached ``register_or_reuse`` for the lazy-init sentinel pattern;
    process-wide module-private cache keyed by metric name.
  All four lazy-import ``prometheus_client`` so callers without the
  optional dependency only pay the import cost on the path that
  actually needs the SDK.
- ``juniper_observability.testing`` (new sub-module) —
  ``reset_prometheus_registry`` pytest fixture replacing the file-
  scoped autouse fixtures consumer test suites had been hand-rolling.
  Function-scoped, opt-in; consumers wire it autouse in their own
  ``conftest.py``. Caused the juniper-data ``TestSEC16MetricsAppIntegration``
  failure on 2026-05-04 because the file-scoped variant only saw
  collectors registered during its own tests.

### Notes

- See
  ``notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md``
  in the juniper-ml repo for the full analysis, design rationale,
  trade-off comparison vs cascor's pre-existing ``_register_or_reuse``,
  and the phased migration plan for the 11 production call sites.

## [0.1.1] - 2026-04-29

### Changed

- **First stable promotion** (METRICS-MON R2.1.3 / seed-06). Promoted from pre-release to stable now that the first consumer (juniper-data, [pcalnon/juniper-data#60](https://github.com/pcalnon/juniper-data/pull/60)) has shipped without surfacing a wire-format regression. **No public-API changes** vs `0.1.1a` — same surface, same behavior; only the version string and trove classifier change.
- Trove classifier moved from `Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta` to reflect the 0.1.x stability commitment.
- Consumers should pin `juniper-observability>=0.1.1` going forward. Existing pins of `>=0.1.0a0` / `>=0.1.1a` continue to resolve to the latest published version, which is now `0.1.1`.

### Notes

- The previous alphas (`0.1.0a0`, `0.1.1a`) remain on PyPI for reproducibility of historical builds. Yanking is intentionally avoided; consumers can downgrade in a hotfix scenario by pinning explicitly.

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
- **Docs** — design + 5-PR migration sequence in `notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md` (parent juniper-ml repo; archived to `notes/legacy/` 2026-05-05).

### Notes

- Per-service metric definitions intentionally stay in their owning repo and use the lazy-init pattern with `prometheus_client` directly. This package only exposes cross-cutting infrastructure.

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/juniper-observability-v0.1.1...HEAD
[0.1.1]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1
[0.1.1a]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1a
