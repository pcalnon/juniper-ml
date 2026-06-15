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
- Generic service-infra extraction from `juniper-cascor` (de-cascored, zero cascor
  coupling): `security` (`APIKeyAuth`, `RateLimiter`, `api_key_header`, plus the
  config-injected `build_api_key_auth` / `build_rate_limiter` factories replacing
  cascor's global-settings singletons), `secrets` (`get_secret` Docker file-secret
  reader), and `middleware` (`SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware`,
  `SecurityMiddleware`, `EXEMPT_PATHS`) — with cascor's `cascor_constants` body-size /
  status-code imports replaced by local module constants. All exported lazily via the
  PEP 562 `__getattr__` so the dependency-free top-level import still holds.
- Publish (`publish-service-core.yml`) and CI (`ci-service-core.yml`) workflows.

### Notes

- Additive only: extracts the first slice of cascor's generic service infra (security /
  secrets / middleware, above); the websocket / worker / generic-route helpers are not
  extracted yet, and this package does **not** depend on `juniper-model-core` yet (the
  `TrainingLifecycleBase` body is a deferred follow-up).

[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.1.0
