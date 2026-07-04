# juniper-service-core v0.2.0 — T2 surface (lifecycle / routes / snapshots / replay / websocket / workers) — Release Notes

> Authored from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](../templates/TEMPLATE_RELEASE_NOTES.md)
> and archived per the release-notes convention (see [`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)).
> Used as the body of the GitHub Release [`juniper-service-core-v0.2.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.2.0).

---

# juniper-service-core v0.2.0 — Service-Tier T2 Surface

**Release Date:** 2026-06-21
**Version:** 0.2.0
**Release Type:** MINOR (additive over 0.1.0)
**Tag:** `juniper-service-core-v0.2.0`

---

## Overview

`juniper-service-core` 0.2.0 adds the **T2 surface** of the OUT-11 service-tier extraction on top of
0.1.0's T1 infrastructure: the full **training-lifecycle orchestrator**, the **generic HTTP routes**,
**snapshot persistence + replay**, the **websocket subsystem**, and the **remote-worker subsystem** —
all extracted and **de-cascored** from `juniper-cascor` with zero cascor coupling. This is the last
prerequisite for the **WS-6 cascor cutover** (cascor repoints its service tier at these generic bases).

The package keeps its two load-bearing properties: a **dependency-free top-level import** (everything
beyond `__version__` resolves lazily via PEP 562, test-enforced with `fastapi`/`pydantic_settings`
blocked in a subprocess), and **"extract base, keep cascor subclass"** — every generic surface is
proven by a both-stacks-green contract test driven by `juniper-model-core`'s **regression** reference
models (the RK-6 guard against classification/cascade assumptions). cascor is untouched.

> **Status:** STABLE behavior, additive — no breaking changes vs 0.1.0.

---

## Release Summary

- **Release type:** MINOR (additive)
- **Primary focus:** the T2 service surface — lifecycle / routes / snapshots / replay / websocket / workers
- **Breaking changes:** NO
- **New runtime dependency:** `numpy>=1.24` (lazy, gated behind `.routes`; the dependency-free base import is preserved)

---

## What's New (over 0.1.0's T1 base)

### Training lifecycle (threaded) + generic routes

The background-threaded **`ServiceLifecycleManager`** (drives a `juniper-model-core` `TrainableModel`
through `fit()` on a worker thread; `LifecycleStateMachine` with an open-string phase; a
`TrainingEvent`-folding `LifecycleMonitor`; cooperative pause/stop at event boundaries), plus the
generic **`/v1/{training,metrics,dataset,network}`** routes over an injected lifecycle and the shared
`ResponseEnvelope`.

### Snapshot persistence + replay

A serializer-injected **`SnapshotStore`** (model + JSON sidecar) with save / list / get / load /
restore-for-retrain / resume and the `/v1/snapshots` routes, and a **`ReplaySession`** that plays a
snapshot's metric history back as timed frames (play/pause/seek/speed/range/stop) with an injectable
`on_frame` sink.

### WebSocket subsystem

**`WebSocketManager`** (sequencing / bounded replay buffer / oversized-message chunking / thread-safe
broadcast / per-endpoint accounting), the generic message builders, control-path security, the
`/ws/training` + `/ws/control` handlers, an **injectable `CommandExecutor`** (control-dispatch
adapter), and the `attach_websocket` lifecycle→broadcast bridge (live + replay frames).

### Remote-worker subsystem

The generic worker-pool foundations (**`WorkerRegistry`**, mTLS / rate-limit / anomaly security,
audit + per-worker metrics, a `prometheus_client` collector), the generic **`WorkerCoordinator`**
(dispatch / collect / timeout / retry over an injectable **`WorkerTaskProtocol`** seam —
`build_assignment` + `parse_result`, the `CommandExecutor` analogue; result reduction stays
consumer-side), and the machine-to-machine **`/ws/workers`** stream with `attach_worker_pool` wiring.

---

## Public API Changes

| Surface | Change | Breaking? |
| --- | --- | --- |
| `juniper_service_core.routes` | New (generic HTTP routes; requires `fastapi`) | No (additive) |
| `ServiceLifecycleManager`, `LifecycleStateMachine`, `LifecycleMonitor`, `SnapshotStore`, `ReplaySession` | New (lazy) | No |
| `juniper_service_core.websocket` | New (`WebSocketManager`, `CommandExecutor`, `build_websocket_router`, `attach_websocket`, `build_worker_router`, `attach_worker_pool`, `worker_stream_handler`) | No |
| `juniper_service_core.workers` | New (`WorkerRegistry`, `WorkerCoordinator`, `WorkerTaskProtocol`, `ParsedResult`, security / audit / metrics) | No |
| `numpy>=1.24` runtime dep | New (lazy, gated behind `.routes`) | No |

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
pip install "juniper-service-core>=0.2.0"   # the full service-tier surface
pip install "juniper-ml[tools]"             # bundled with the other Juniper shared tools (pin widened to >=0.2.0,<0.3.0)
```

- Additive over 0.1.0 — no code changes required for existing T1 consumers.
- **`0.1.0` shipped only the T1 layer** (app factory / settings / health / security / secrets /
  middleware / synchronous lifecycle); the lifecycle orchestrator, routes, snapshots, replay,
  websocket, and worker subsystems are **new in `0.2.0`**. Consumers that need them must require
  `>=0.2.0`.
- The base `import juniper_service_core` stays dependency-free; `fastapi` / `numpy` load only when the
  corresponding lazy surface is accessed.

---

## Known Issues / By-Design Deferrals

None blocking. The following stay **cascor-side / deferred** by design (OUT-11 OQ-11, not bugs):
correlation-based **result reduction** and the cascade `Task`/`TaskResult` envelope (the
`WorkerCoordinator` dispatches over opaque payloads + an injected codec); the `cascade_add` /
`candidate_progress` frames, topology / per-sample-weight replay, and **dataset-swap history**.

---

## What's Next

- **WS-6 — cascor adoption.** cascor subclasses `ServiceLifecycleManager` and injects its
  `WorkerTaskProtocol` / `CommandExecutor`, repointing its service tier at these generic bases now
  that 0.2.0 is published.
- Optional later modules noted in the design audit (`log_config` / `profiling` / `utils`).

---

## Design & Provenance

- Design, gate-audit & build plan: `notes/JUNIPER_2026-06-19_JUNIPER-ML_SERVICE-CORE-T2-SURFACE-DESIGN-AND-AUDIT.md`
- Pull requests: T2 routes/lifecycle #473 · snapshots #476 · replay #478 · websocket #484 · worker foundations #492 · worker coordinator + `/ws/workers` #496
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.2.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.2.0 | 2026-06-21 | T2 surface — lifecycle orchestrator / generic routes / snapshots / replay / websocket / worker subsystem |
| 0.1.0 | 2026-06-16 | Initial scaffold — T1 service infrastructure |
