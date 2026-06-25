# juniper-service-core v0.3.0 — create_app(lifespan=) — Release Notes

> Authored from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](../templates/TEMPLATE_RELEASE_NOTES.md)
> and archived per the release-notes convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).
> Used as the body of the GitHub Release [`juniper-service-core-v0.3.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.3.0).

---

# juniper-service-core v0.3.0 — App-factory lifespan hook

**Release Date:** 2026-06-25
**Version:** 0.3.0
**Release Type:** MINOR (additive over 0.2.0)
**Tag:** `juniper-service-core-v0.3.0`

---

## Overview

`juniper-service-core` 0.3.0 adds an optional **`lifespan`** parameter to the `create_app` factory,
forwarded to `FastAPI(lifespan=...)`. A consuming service can now run startup/shutdown hooks —
logging configuration, build-info, resource setup/teardown — in a **FastAPI lifespan** rather than at
import time or in its CLI entrypoint, matching the lifespan pattern the older Juniper services
(data / cascor / canopy) already use.

This unblocks the **juniper-recurrence audit H1 follow-up**: the recurrence app currently configures
logging at its CLI `serve` entry *because* `create_app` exposed no lifespan hook. With 0.3.0 it can
move that into a lifespan (which also covers a direct `uvicorn juniper_recurrence.app:app`).

> **Status:** STABLE behavior, additive — no breaking changes vs 0.2.0. Omitting `lifespan` is exactly
> the previous behavior.

---

## Release Summary

- **Release type:** MINOR (additive)
- **Primary focus:** `create_app(lifespan=...)` — an optional FastAPI lifespan hook in the app factory
- **Breaking changes:** NO
- **New runtime dependency:** none

---

## What's New (over 0.2.0)

### `create_app(lifespan=...)`

`create_app` accepts an optional `lifespan` (a FastAPI lifespan context manager) and forwards it to
`FastAPI(lifespan=lifespan)`. Consumers that need startup/shutdown orchestration construct a lifespan
and pass it in; the generic health router and any supplied routers are mounted as before. Omitting
`lifespan` keeps the prior no-lifespan behavior.

---

## Public API Changes

| Surface | Change | Breaking? |
| --- | --- | --- |
| `create_app(*, title, version, routers, lifespan=None)` | New optional `lifespan` keyword, forwarded to `FastAPI(lifespan=...)` | No (additive; default `None` = prior behavior) |

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests passed | 187 (full `juniper-service-core` suite) |
| Lint | `ruff check` + `ruff format --check` clean; `app.py` mypy-clean |
| Build | `python -m build` + `twine check` PASS (sdist + wheel) |
| Dependency-free import | preserved (the base `import juniper_service_core` stays `fastapi`-free) |

---

## Upgrade / Install Notes

```bash
pip install "juniper-service-core>=0.3.0"   # adds the create_app(lifespan=) hook
pip install "juniper-ml[tools]"             # bundled with the other shared tools (pin widened to >=0.2.0,<0.4.0)
```

- Additive over 0.2.0 — no code changes required for existing consumers.
- Consumers that want to pass a `lifespan` to `create_app` must require `>=0.3.0`.

---

## Known Issues / By-Design Deferrals

None.

---

## What's Next

- **juniper-recurrence** adopts `create_app(lifespan=...)` to move its logging configuration (and
  `set_build_info`) into a FastAPI lifespan (audit H1 follow-up), bumping its `juniper-service-core`
  pin to `>=0.3.0`.

---

## Design & Provenance

- Motivation: `notes/JUNIPER_RECURRENCE_FULL_AUDIT_2026-06-24.md` (H1 follow-up)
- Pull request: `create_app(lifespan=)` + 0.3.0 bump #550
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.3.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.3.0 | 2026-06-25 | `create_app(lifespan=...)` — optional FastAPI lifespan hook in the app factory |
| 0.2.0 | 2026-06-21 | T2 surface — lifecycle orchestrator / generic routes / snapshots / replay / websocket / worker subsystem |
| 0.1.0 | 2026-06-16 | Initial scaffold — T1 service infrastructure |
