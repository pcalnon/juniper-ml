# juniper-service-core v0.1.0 — initial scaffold (T1 service infra) — Release Notes

> Archived per the release-notes convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).
> **Backfill:** `0.1.0` was published to PyPI on **2026-06-16** via a *tag-only* push (tag
> `juniper-service-core-v0.1.0`), before the publish workflow's GitHub-Release gate existed — so no
> Release was cut at the time. This file is the body of the **backfilled** GitHub Release for that
> existing tag, authored after the fact for the historical record. The substantial **T2** surface
> ships in [`v0.2.0`](RELEASE_NOTES_juniper-service-core_v0.2.0.md).

---

# juniper-service-core v0.1.0 — Initial Scaffold (T1 Service Infrastructure)

**Release Date:** 2026-06-16 (PyPI publish; scaffold dated 2026-06-14)
**Version:** 0.1.0
**Release Type:** Initial release (first PyPI publish)
**Tag:** `juniper-service-core-v0.1.0`

---

## Overview

First release of the shared **service-tier** library for the Juniper ML platform (WS-2 of the
model/middleware refactor). `0.1.0` is the **T1** layer — the model-agnostic FastAPI service
infrastructure extracted and **de-cascored** from `juniper-cascor`, with zero cascor coupling. The
T2 surface (lifecycle orchestrator, generic routes, snapshots, replay, websocket, and the worker
subsystem) ships in `0.2.0`.

The package's signature property — a **dependency-free top-level import** (`import
juniper_service_core` pulls no third-party runtime dependency; the rest resolves lazily via PEP 562
`__getattr__`) — is established here.

---

## What's in it (T1)

- **`create_app(...)`** — model-agnostic FastAPI application factory; **`SettingsBase`** — a
  `pydantic-settings` base; the generic **`/v1/health[/ready]`** router.
- **`security`** — `APIKeyAuth`, `RateLimiter`, `api_key_header`, plus the config-injected
  `build_api_key_auth` / `build_rate_limiter` factories (replacing cascor's global-settings
  singletons).
- **`secrets`** — `get_secret` Docker file-secret reader.
- **`middleware`** — `SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware`, `SecurityMiddleware`,
  `EXEMPT_PATHS`.
- **`launcher`** — `ManagedService`, `start_service`, `wait_for_health` (subprocess companion-service
  runner with `atexit` cleanup).
- **`lifecycle`** — the **synchronous** `TrainingLifecycle` body (drives a `juniper-model-core`
  `TrainableModel`'s `fit()` to completion + an `EventCollector` ordered sink).
- CI (`ci-service-core.yml`) and publish (`publish-service-core.yml`) workflows.

---

## Dependencies

`fastapi>=0.110`, `pydantic>=2.0`, `pydantic-settings>=2.0`, **`juniper-model-core>=0.1.0`**
(publish-first; the lifecycle body drives the model contract). No `numpy` yet — that arrives in
`0.2.0` with the generic routes.

---

## What's Next

- **`0.2.0`** — the full T2 surface (threaded lifecycle orchestrator + FSM + monitor, generic HTTP
  routes, snapshot persistence + replay, the websocket subsystem, and the remote-worker subsystem).

---

## Design & Provenance

- Refactor plan (WS-2): `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`
- Pull requests: scaffold #417 · T1 security #419 · launcher #420 · synchronous lifecycle #422
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.1.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.1.0 | 2026-06-16 | Initial scaffold — T1 service infrastructure (app factory / settings / health / security / secrets / middleware / launcher / synchronous lifecycle), de-cascored from juniper-cascor |
