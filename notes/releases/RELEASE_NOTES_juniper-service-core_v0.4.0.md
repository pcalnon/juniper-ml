# juniper-service-core v0.4.0 — E-8 boot-time dependency-floor self-check — Release Notes

> Authored from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](../templates/TEMPLATE_RELEASE_NOTES.md)
> and archived per the release-notes convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).
> Used as the body of the GitHub Release [`juniper-service-core-v0.4.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.4.0).

---

# juniper-service-core v0.4.0 — Boot-time dependency-floor self-check

**Release Date:** 2026-07-01
**Version:** 0.4.0
**Release Type:** MINOR (additive over 0.3.0)
**Tag:** `juniper-service-core-v0.4.0`

---

## Overview

`juniper-service-core` 0.4.0 adds a new **`dependency_floors`** module — a **boot-time
dependency-floor self-check** (enhancement **E-8**). A service calls `enforce_dependency_floors(...)`
at startup, **before it binds**; if any installed `juniper-*` wheel is below the service's declared
floor, the call raises `DependencyFloorError` (naming `dep + floor + installed`) so the server's
startup **fails loud** instead of the service limping along on a stale wheel.

This is the automatic **prevention** companion to the E-2 env-floor-drift **detector** (juniper-ml's
`util/env_floor_drift_check.py` + the `juniper-env-drift-check` CI console script): those detect a
below-floor wheel out of band; this stops a service from serving on top of one. It would have caught
the canopy **"green tests / dead app"** incident — a client wheel below its `pyproject` floor that
passed unit tests but broke the live app — at first start, with zero human action.

> **Status:** STABLE, additive — no breaking changes vs 0.3.0. The dependency-free
> `import juniper_service_core` guarantee is preserved (the module is stdlib-first; `packaging` is an
> optional import with a numeric-tuple fallback).

---

## Release Summary

- **Release type:** MINOR (additive)
- **Primary focus:** `enforce_dependency_floors(...)` — a fail-loud boot-time `juniper-*` floor check
- **Breaking changes:** NO
- **New runtime dependency:** none (stdlib `importlib.metadata` / `tomllib`; `packaging` optional)

---

## What's New (over 0.3.0)

### `dependency_floors` — boot-time floor enforcement

- **`enforce_dependency_floors(...)`** — resolves the service's `juniper-*` floors from an explicit
  `{dist: min_version}` mapping, the caller's installed **Requires-Dist metadata** (`distribution=` —
  the robust runtime path that works for wheel *or* editable installs), or a source `pyproject.toml`
  (`pyproject_path=`), then raises `DependencyFloorError` if any installed wheel is below floor.
  Conditional / extra-gated deps (environment markers) are skipped — only unconditional floors are
  enforced, so an optional dep can't false-positive.
- **`DependencyFloorError`** — the raised exception; and **`check_dependency_floors(floors)`**, the
  pure, side-effect-free core (returns the list of violations) for callers that want to inspect.
- **Escape hatch** — `JUNIPER_SKIP_DEP_FLOOR_CHECK` (truthy) bypasses the check, logged loudly, so a
  false positive can never permanently block a legitimate start.
- Version comparison is numeric-aware (`0.9.0 < 0.10.0`), via `packaging` when available with a
  stdlib numeric-tuple fallback.

Exposed lazily from the top level (`from juniper_service_core import enforce_dependency_floors,
DependencyFloorError`) via the existing PEP-562 surface, so the dependency-free base import is
unaffected.

---

## Public API Changes

| Surface | Change | Breaking? |
| --- | --- | --- |
| `enforce_dependency_floors(floors=None, *, distribution=None, pyproject_path=None, prefix="juniper-", skip_env_var="JUNIPER_SKIP_DEP_FLOOR_CHECK", logger=None)` | New — fail-loud boot-time floor check | No (additive) |
| `DependencyFloorError(RuntimeError)` | New exception | No (additive) |
| `check_dependency_floors(floors)` | New pure checker returning violations | No (additive) |

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests passed | 207 (full `juniper-service-core` suite; +20 new for `dependency_floors`) |
| Coverage | 83% (≥80% gate); `dependency_floors.py` fully covered |
| Lint | `ruff check` + `ruff format --check` clean |
| Build | `python -m build` + `twine check` PASS (sdist + wheel) |
| Dependency-free import | preserved (base `import juniper_service_core` stays `fastapi`-free) |

---

## Upgrade / Install Notes

```bash
pip install "juniper-service-core>=0.4.0"   # adds the dependency_floors boot-time self-check
pip install "juniper-ml[tools]"             # bundled with the other shared tools (pin widened to >=0.2.0,<0.5.0)
```

- Additive over 0.3.0 — no code changes required for existing consumers.
- A service that wants the boot-time check must require `>=0.4.0` and call
  `enforce_dependency_floors(distribution="<its-dist-name>")` at startup (e.g. in its FastAPI
  `lifespan`), before binding.

---

## Known Issues / By-Design Deferrals

None. The **canopy adoption** (canopy calling `enforce_dependency_floors` at the top of its
`lifespan`) is a downstream follow-up gated on this release; it is not part of this package release.

---

## What's Next

- **juniper-canopy** adopts the check: add `juniper-service-core>=0.4.0` and call
  `enforce_dependency_floors(distribution="juniper-canopy")` at the top of its `lifespan`
  (`src/main.py`), before `create_backend` / binding, plus a canopy-side test. This is the downstream
  half of E-8 and the direct fix for the canopy incident class.
- Other services (cascor, data) can adopt the same one-liner as they take up `juniper-service-core`.

---

## Design & Provenance

- Plan: `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md` §6.11 (E-8, the
  app-startup self-check / the primary E-1 Plan-B and E-2 prevention companion)
- Pull request: E-8 boot-time dependency-floor self-check + 0.4.0 bump #596
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.4.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.4.0 | 2026-07-01 | `dependency_floors` — boot-time `juniper-*` floor self-check (E-8); fail loud before binding |
| 0.3.0 | 2026-06-25 | `create_app(lifespan=...)` — optional FastAPI lifespan hook in the app factory |
| 0.2.0 | 2026-06-21 | T2 surface — lifecycle orchestrator / generic routes / snapshots / replay / websocket / worker subsystem |
| 0.1.0 | 2026-06-16 | Initial scaffold — T1 service infrastructure |
