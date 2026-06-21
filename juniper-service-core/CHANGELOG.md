# Changelog

All notable changes to `juniper-service-core` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_Nothing yet._

## [0.1.0] - 2026-06-21

Initial public release of the shared service-tier library (WS-2 of the model/middleware
refactor). Ships the full **T1** (service infra) and **T2** (lifecycle, routes, snapshots, replay,
websocket, and worker subsystem) surface extracted and de-cascored from `juniper-cascor`, with zero
cascor coupling. Additive only — cascor is untouched; its adoption of these bases is WS-6's A-phase.
The cascade-bound parts (correlation reduction, the `Task`/`TaskResult` envelope, cascade frames,
dataset-swap history) stay cascor-side per the OUT-11 design audit.

### Added

#### Package + service infra (T1)

- `SettingsBase` — `pydantic-settings` base with generic `service_name` / `host` / `port` /
  `log_level` fields; subclasses set their own `env_prefix`.
- `create_app(...)` — model-agnostic FastAPI application factory that mounts the generic health
  router and any service-supplied routers.
- Generic health router (`health_router()`) exposing `GET /v1/health` (liveness) and
  `GET /v1/health/ready` (readiness), plus a `HealthStatus` model.
- **Dependency-free top-level import:** `import juniper_service_core` exposes only `__version__`
  eagerly; the rest of the public surface loads lazily via PEP 562 `__getattr__`, so the TestPyPI
  publish-verify can run a clean `--no-deps` import check.
- Generic service-infra extraction from `juniper-cascor` (de-cascored): `security` (`APIKeyAuth`,
  `RateLimiter`, `api_key_header`, plus the config-injected `build_api_key_auth` /
  `build_rate_limiter` factories replacing cascor's global-settings singletons), `secrets`
  (`get_secret` Docker file-secret reader), and `middleware` (`SecurityHeadersMiddleware`,
  `RequestBodyLimitMiddleware`, `SecurityMiddleware`, `EXEMPT_PATHS`) — cascor's `cascor_constants`
  imports replaced by local module constants.
- `launcher` — generic subprocess-managed companion-service runner: `ManagedService`,
  `wait_for_health`, `start_service`, plus `atexit` cleanup of the active-services registry. Log-dir
  resolution is generic (`JUNIPER_SERVICE_LOG_DIR`, else `./logs`).

#### Training lifecycle + generic routes (T2 step 1)

- `lifecycle` — the **synchronous** `TrainingLifecycle` body drives a `juniper-model-core`
  `TrainableModel`'s `fit()` to completion and forwards its `TrainingEvent`s to the injected sink,
  stamping a monotonic run-scoped `seq`; plus an `EventCollector` ordered sink. One body drives both
  fixed-topology and growable models (growth happens inside `fit()`, per the model-core contract).
- `ServiceLifecycleManager` — the model-agnostic, **background-threaded** lifecycle body that
  model-core's `TrainingLifecycleBase` deferred to WS-2: drives an injected `TrainableModel` through
  `fit()` on a worker thread, tracks a `LifecycleStateMachine`
  (`STOPPED → STARTED → {PAUSED, COMPLETED, FAILED}`, phase = open `str`), folds `TrainingEvent`s into
  a thread-safe `LifecycleMonitor` (live-state snapshot + bounded metric history), and honors
  cooperative pause/stop at event boundaries.
- **Generic HTTP routes** (`juniper_service_core.routes`) — model-agnostic training-control
  (`/v1/training/{start,stop,pause,resume,reset,status,params}`), metrics (`/v1/metrics`,
  `/v1/metrics/history`), dataset (`/v1/dataset`, `/v1/dataset/data`), and read-only
  model-introspection (`/v1/network`, `/v1/network/topology`) routes over the injected lifecycle
  (`app.state.lifecycle`), plus the shared `ResponseEnvelope` / `success_response` (with numpy-scalar
  coercion). Mount via `create_app(routers=build_routers())`.

#### Snapshot persistence + replay (T2 steps 1b / 1c)

- **Snapshot persistence** — a serializer-injected `SnapshotStore` (one bundle directory per
  snapshot: the model written by an injected `juniper-model-core` `ModelSerializer` + a JSON sidecar
  of lifecycle state) plus the `ServiceLifecycleManager` methods `save_snapshot` / `list_snapshots` /
  `get_snapshot` / `load_snapshot` (→ `INVESTIGATING`) / `restore_for_retrain` (→ `STOPPED`) /
  `resume_from_snapshot` (→ `RESUME_READY`), and the `/v1/snapshots` routes (disk I/O off the event
  loop). Enabled only when a service injects a `ModelSerializer` (otherwise the routes return `501`).
- **Snapshot replay** — `ReplaySession` plays a snapshot's stored metric history back as timed frames
  on a background daemon (play / pause / seek / speed / range / stop / status; an injectable
  `on_frame` sink), plus `start_replay` (→ `REPLAYING`) / `replay_control` / `stop_replay` /
  `get_replay_state` and the `POST /v1/snapshots/{id}/replay[/control]` routes.

#### WebSocket subsystem (T2 step 2)

- `juniper_service_core.websocket` — the model-agnostic websocket surface: `WebSocketManager`
  (monotonic sequencing, bounded replay buffer, oversized-message chunking, thread-safe broadcast,
  per-endpoint connection accounting) + the generic message builders (the 7 model-agnostic frames) +
  control-path security (`validate_control_origin` / `LeakyBucket` / `HandshakeCooldown`) + the
  `/ws/training` (metrics stream) and `/ws/control` (command channel) handlers + `build_websocket_router`.
- **Injectable `CommandExecutor`** (default `LifecycleCommandExecutor`) — the control-channel dispatch
  adapter, so a service maps the wire commands onto its own orchestration without the base hard-coding
  any verb semantics.
- `attach_websocket` lifecycle→broadcast bridge — live-training **and** replay frames push to
  `/ws/training` clients via the manager's additive `frame_sink` (wired into `ReplaySession.on_frame`).

#### Worker subsystem (T2 step 3)

- **Worker-pool foundations** (`juniper_service_core.workers`) — `WorkerRegistry` /
  `WorkerRegistration` / `WorkerRegistryFullError` (registration, heartbeat, health-score, idle/stale
  queries, capacity cap) + security primitives (`TLSConfig` mTLS, `ConnectionRateLimiter` token-bucket,
  `AnomalyDetector` over a generic bounded quality `score`) + audit (`AuditLogger` / `WorkerMetrics` /
  `AuditEventType`) + `WorkerRegistryCollector` (a `prometheus_client` bridge; configurable
  `metric_prefix`, pending-tasks via an injected callable).
- **`WorkerCoordinator`** — generic task dispatch / collect / timeout / retry with a worker-liveness
  early-exit and a background health monitor, over an injectable `WorkerTaskProtocol` seam
  (`build_assignment` + `parse_result` + `result_attachments`; the `CommandExecutor` analogue). Result
  reduction stays consumer-side (`collect_results` returns the raw list).
- **`/ws/workers` stream** (`worker_stream_handler`) — the machine-to-machine worker channel
  (origin-reject, `X-API-Key` auth, per-source rate-limit, registration handshake with a
  server-assigned id, heartbeat + enriched-field forwarding, dispatch + binary-frame transport), plus
  `attach_worker_pool` app-wiring and `build_worker_router`.

#### CI / publish workflows

- `ci-service-core.yml` (test matrix + build, PR-to-`main` path-scoped) and `publish-service-core.yml`
  (TestPyPI → PyPI via OIDC trusted publishing, tag `juniper-service-core-v*`, gated on a GitHub
  Release per the release convention).

### Notes

- **Cascade-bound parts stay cascor-side** per the OUT-11 design audit (OQ-11): correlation-based
  result reduction, the `Task`/`TaskResult` envelope (`candidate_data` / `correlation` / …), the
  `cascade_add` / `candidate_progress` frames, topology/per-sample-weight replay, and dataset-swap
  history. cascor adopts the generic bases in WS-6 (deferred follow-ups FW-1..4 in the design doc).
- **`juniper-model-core` dependency (publish-first).** The lifecycle body depends on the model
  contract; model-core must be on PyPI before this package is published. The dependency loads lazily,
  so the dependency-free top-level import is preserved.
- Adds a `numpy>=1.24` runtime dependency (the generic routes marshal inline request arrays at the
  model boundary). It loads lazily with `.routes`, so the dependency-free top-level import holds.
- Every generic surface is proven by a both-stacks-green contract test that drives it with
  model-core's **regression** reference models (the RK-6 guard against classification/cascade
  assumptions leaking into "generic" code).

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/juniper-service-core-v0.1.0...HEAD
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.1.0
