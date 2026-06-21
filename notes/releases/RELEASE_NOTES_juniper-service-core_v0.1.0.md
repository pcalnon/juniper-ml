# juniper-service-core v0.1.0 — shared service-tier scaffolding — Release Notes

> Authored from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](../templates/TEMPLATE_RELEASE_NOTES.md)
> and archived per the release-notes convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).
> Used verbatim as the body of the GitHub Release [`juniper-service-core-v0.1.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.1.0).

---

# juniper-service-core v0.1.0 — Shared Service-Tier Scaffolding

**Release Date:** 2026-06-21
**Version:** 0.1.0
**Release Type:** Initial release (first PyPI publish)
**Tag:** `juniper-service-core-v0.1.0`

---

## Overview

`juniper-service-core` is the shared **service-tier** library for the Juniper ML platform (WS-2 of
the model/middleware refactor) — the minimal, model-agnostic FastAPI plumbing every Juniper model
service needs. This first release ships the complete **T1** (service infra) and **T2** (training
lifecycle, generic routes, snapshots, replay, websocket, and the remote-worker subsystem) surface,
extracted and **de-cascored** from `juniper-cascor` with zero cascor coupling.

The package is designed around two load-bearing properties:

1. **Dependency-free top-level import.** `import juniper_service_core` pulls **no** third-party
   runtime dependency — only `__version__` is eager; the rest of the surface (`create_app`, the
   lifecycle/routes/websocket/worker subsystems) resolves lazily via PEP 562 `__getattr__`. This is
   what lets the TestPyPI publish-verify run a clean `--no-deps` import check.
2. **Extract base, keep cascor subclass.** Every generic surface is proven by a both-stacks-green
   contract test driven by `juniper-model-core`'s **regression** reference models (the RK-6 guard
   against classification/cascade assumptions leaking into "generic" code). cascor is untouched; it
   adopts these bases in WS-6.

> **Status:** STABLE behavior, `0.1.0` package line — additive, no consumers broken (there are none
> yet; the cascor cutover is WS-6).

---

## Release Summary

- **Release type:** Initial (first publish)
- **Primary focus:** The shared service-tier surface — T1 infra + T2 lifecycle/routes/snapshots/replay/websocket/workers
- **Breaking changes:** N/A (first release)
- **Dependency-free base import:** preserved and test-enforced (subprocess blocks `fastapi`/`pydantic_settings`)

---

## What's New

### T1 — service infrastructure

`SettingsBase` (pydantic-settings base), `create_app(...)` (FastAPI app factory), the generic
`/v1/health[/ready]` router, API-key auth + rate limiting + security/body-limit middleware
(config-injected factories replacing cascor's global-settings singletons), the Docker file-secret
reader, and a subprocess-managed companion-service `launcher`.

### T2 — training lifecycle + generic routes

The **synchronous** `TrainingLifecycle` body and the **background-threaded** `ServiceLifecycleManager`
(both drive a `juniper-model-core` `TrainableModel` through `fit()`), a `LifecycleStateMachine`
(open-string phase), a `TrainingEvent`-folding `LifecycleMonitor`, and the generic
`/v1/{training,metrics,dataset,network}` routes over an injected lifecycle (`app.state.lifecycle`).

### T2 — snapshots + replay

A serializer-injected `SnapshotStore` (model + JSON sidecar) with save / list / get / load /
restore-for-retrain / resume, the `/v1/snapshots` routes, and a `ReplaySession` that plays a
snapshot's metric history back as timed frames (play/pause/seek/speed/range/stop) with an injectable
`on_frame` sink.

### T2 — websocket subsystem

`WebSocketManager` (sequencing / bounded replay buffer / oversized-message chunking / thread-safe
broadcast / per-endpoint accounting), the generic message builders, control-path security, the
`/ws/training` + `/ws/control` handlers, an **injectable `CommandExecutor`** (control-dispatch
adapter), and the `attach_websocket` lifecycle→broadcast bridge (live + replay frames).

### T2 — remote-worker subsystem

The generic worker-pool foundations (`WorkerRegistry`, mTLS / rate-limit / anomaly security, audit +
per-worker metrics, a `prometheus_client` collector), the generic **`WorkerCoordinator`** (dispatch /
collect / timeout / retry over an injectable `WorkerTaskProtocol` seam), and the machine-to-machine
**`/ws/workers`** stream with `attach_worker_pool` wiring.

---

## Public API (highlights)

| Surface | Names |
| --- | --- |
| App / settings / health | `create_app`, `SettingsBase`, `health_router` |
| Security / secrets / middleware | `APIKeyAuth`, `RateLimiter`, `build_api_key_auth`, `build_rate_limiter`, `get_secret`, `SecurityMiddleware`, … |
| Launcher | `ManagedService`, `start_service`, `wait_for_health` |
| Lifecycle | `TrainingLifecycle`, `ServiceLifecycleManager`, `LifecycleStateMachine`, `LifecycleMonitor`, `SnapshotStore`, `ReplaySession` |
| Routes | `build_routers`, `get_lifecycle`, `ResponseEnvelope`, `success_response`, `error_response` |
| WebSocket | `WebSocketManager`, `CommandExecutor`, `LifecycleCommandExecutor`, `build_websocket_router`, `attach_websocket`, `build_worker_router`, `attach_worker_pool`, `worker_stream_handler` |
| Workers | `WorkerRegistry`, `WorkerCoordinator`, `WorkerTaskProtocol`, `ParsedResult`, `AnomalyDetector`, `AuditLogger`, `WorkerMetrics`, `WorkerRegistryCollector`, `TLSConfig`, `ConnectionRateLimiter` |

Everything beyond `__version__` is lazily exported (PEP 562), so the top-level import stays
dependency-free.

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests passed | 185 |
| Coverage | ≥ 80% gate held (CI matrix Python 3.12 / 3.13) |
| Build | `python -m build` + `twine check` PASS (sdist + wheel) |
| Dependency-free import | verified in a subprocess that blocks `fastapi` / `pydantic_settings` |

---

## Upgrade / Install Notes

```bash
pip install juniper-service-core            # the shared service-tier library
pip install "juniper-ml[tools]"             # bundled with the other Juniper shared tools
```

- **Publish-first dependency:** `juniper-model-core` (the model contract) must be resolvable from
  PyPI — it is published independently and pinned `>=0.1.0,<0.4.0`.
- The base `import juniper_service_core` is dependency-free; `fastapi` / `pydantic-settings` /
  `numpy` load only when the corresponding lazy surface (routes / websocket / workers / settings) is
  accessed.

---

## Known Issues / By-Design Deferrals

None blocking. The following stay **cascor-side / deferred** by design (OUT-11 OQ-11, not bugs):

- Correlation-based **result reduction** and the cascade `Task`/`TaskResult` envelope (the
  `WorkerCoordinator` dispatches over opaque payloads + an injected codec; reduction is the
  consumer's job — WS-8).
- The `cascade_add` / `candidate_progress` websocket frames, topology / per-sample-weight replay,
  and **dataset-swap history** (cascor's P2 live-swap feature) — generalized only when a second
  consumer needs them (design-doc FW-1..4).

---

## What's Next

- **WS-6 — cascor adoption.** cascor repoints its service tier at these generic bases (subclassing
  `ServiceLifecycleManager`, injecting its `WorkerTaskProtocol` / `CommandExecutor`), now that
  service-core is published and the OUT-11 gate is cleared.
- Optional later modules noted in the design audit (`log_config` / `profiling` / `utils`).

---

## Design & Provenance

- Design, gate-audit & build plan: `notes/JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md`
- Refactor plan (WS-2): `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`
- Pull requests: scaffold #417 · T1 security #419 · launcher #420 · sync lifecycle #422 · T2 routes/lifecycle #473 · snapshots #476 · replay #478 · websocket #484 · worker foundations #492 · worker coordinator + `/ws/workers` #496
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.1.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.1.0 | 2026-06-21 | Initial release — shared service-tier surface (T1 infra + T2 lifecycle / routes / snapshots / replay / websocket / worker subsystem), de-cascored from juniper-cascor |
