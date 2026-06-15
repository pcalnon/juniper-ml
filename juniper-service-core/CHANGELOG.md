# Changelog

All notable changes to `juniper-service-core` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-14

### Added

- Initial package scaffold for the shared service-tier library (WS-2 of the
  model/middleware refactor).
- `SettingsBase` — `pydantic-settings` base with generic `service_name` / `host` /
  `port` / `log_level` fields; subclasses set their own `env_prefix`.
- `create_app(...)` — model-agnostic FastAPI application factory that mounts the
  generic health router and any service-supplied routers.
- Generic health router (`health_router()`) exposing `GET /v1/health` (liveness) and
  `GET /v1/health/ready` (readiness), plus a `HealthStatus` model.
- Dependency-free top-level import: `import juniper_service_core` exposes only
  `__version__` eagerly; `create_app` / `SettingsBase` load lazily via PEP 562
  `__getattr__`.
- Publish (`publish-service-core.yml`) and CI (`ci-service-core.yml`) workflows.

### Notes

- Additive only: does **not** extract cascor service code yet, and does **not** depend
  on `juniper-model-core` yet (the `TrainingLifecycleBase` body is a deferred
  follow-up).

[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.1.0
