# juniper-service-core v0.5.0 — SEC-F01 boot-time auth-posture self-check — Release Notes

> Authored from [`notes/templates/TEMPLATE_RELEASE_NOTES.md`](../templates/TEMPLATE_RELEASE_NOTES.md)
> and archived per the release-notes convention (see [`notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` §11](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md)).
> Used as the body of the GitHub Release [`juniper-service-core-v0.5.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-service-core-v0.5.0).

---

# juniper-service-core v0.5.0 — Boot-time auth-posture self-check

**Release Date:** 2026-07-18
**Version:** 0.5.0
**Release Type:** MINOR (additive over 0.4.0)
**Tag:** `juniper-service-core-v0.5.0`

---

## Overview

`juniper-service-core` 0.5.0 adds a new **`auth_posture`** module — a **boot-time auth-posture
self-check** (**SEC-F01**), the security companion to 0.4.0's E-8 `enforce_dependency_floors` check.
A service calls `enforce_auth_posture(...)` at startup, **before it binds**, passing its resolved API
keys and whether auth is required in this deployment (`require_auth`); the call **fails loud** (logs
`CRITICAL` and raises `AuthPostureError`) when `require_auth=True` but no real key is configured, so
the server refuses to start rather than silently serving open.

This closes the failure mode confirmed in the containerized-stack security audit (**HO-2**): every
juniper HTTP service computes `enabled = len(api_keys) > 0`, so an empty or placeholder secret
silently disables `APIKeyAuth` and the service serves protected routes unauthenticated — with no
startup error and a `healthy` health check. A blank/whitespace key (what an empty secret file
resolves to) counts as unset.

> **Status:** STABLE, additive — no breaking changes vs 0.4.0. The dependency-free
> `import juniper_service_core` guarantee is preserved (the module is stdlib-only).

---

## Release Summary

- **Release type:** MINOR (additive)
- **Primary focus:** `enforce_auth_posture(...)` — a fail-loud boot-time auth-posture check (SEC-F01)
- **Breaking changes:** NO
- **New runtime dependency:** none (stdlib-only; lazy PEP-562 export preserved)

---

## What's New (over 0.4.0)

### `auth_posture` — boot-time auth-posture enforcement (SEC-F01)

- **`enforce_auth_posture(api_keys, *, require_auth, service_name="service", skip_env_var=..., logger=None)`**
  — three outcomes: a real key configured → `INFO` (secured); no real key + `require_auth=False` →
  loud `WARNING` (running OPEN, visible in logs); no real key + `require_auth=True` → `CRITICAL` +
  raise `AuthPostureError` (startup refused).
- **`auth_is_configured(api_keys)`** / **`real_keys(api_keys)`** — the pure, side-effect-free core:
  blank/whitespace-only keys are not real auth, mirroring exactly what makes `APIKeyAuth` *enabled*.
- **Escape hatch** — `JUNIPER_SKIP_AUTH_POSTURE_CHECK` (truthy) bypasses the check, logged loudly, so
  a false positive can never permanently block a legitimate start.
- Exported lazily from the top level (`from juniper_service_core import enforce_auth_posture,
  auth_is_configured, AuthPostureError`) — the dependency-free base import is unaffected.

### Fixed

- **`[test]` extra now includes `prometheus-client>=0.20.0`** — the `workers/metrics` tests exercise
  `WorkerRegistryCollector` (a `prometheus_client` bridge) but the dependency was absent from the
  `test` extra, so those tests silently **skipped** in CI. Test-only surface — no runtime dependency.

### Changed

- **Test coverage lifted** for the `workers/`, `lifecycle/`, `routes/`, and top-level sub-modules
  (work-unit **C-4** of the per-file coverage rollout,
  `notes/JUNIPER_2026-06-30_JUNIPER-ECOSYSTEM_PER-FILE-COVERAGE-ROLLOUT-SCOPING.md`): each named
  source file ≥90% statement coverage, each sub-module ≥95% pooled — real tests only, and the
  **blocking per-file coverage gate** (C-4c) is now wired in CI.

---

## Public API Changes

| Surface | Change | Breaking? |
| --- | --- | --- |
| `enforce_auth_posture(api_keys, *, require_auth, service_name="service", skip_env_var="JUNIPER_SKIP_AUTH_POSTURE_CHECK", logger=None)` | New — fail-loud boot-time auth-posture check | No (additive) |
| `AuthPostureError(RuntimeError)` | New exception | No (additive) |
| `auth_is_configured(api_keys)` / `real_keys(api_keys)` | New pure checkers | No (additive) |

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests | Full `juniper-service-core` suite green on Python 3.12/3.13 in the release PR CI (juniper-ml#657) |
| Coverage | Blocking per-file gate (C-4c, juniper-ml#611) enforcing ≥90% per named file / ≥95% pooled per lifted sub-module |
| Build | `python -m build` + `twine check` PASS (sdist + wheel) on the release PR |
| Dependency-free import | preserved (base `import juniper_service_core` stays `fastapi`-free; `auth_posture` is stdlib-only) |

---

## Upgrade / Install Notes

```bash
pip install "juniper-service-core>=0.5.0"   # adds the auth_posture boot-time self-check
pip install "juniper-ml[tools]"             # bundled with the other shared tools (pin widened to >=0.2.0,<0.6.0)
```

- Additive over 0.4.0 — no code changes required for existing consumers.
- A service that wants the boot-time check must require `>=0.5.0` and call
  `enforce_auth_posture(api_keys, require_auth=...)` at startup (e.g. in its FastAPI `lifespan`,
  mirroring the E-8 `enforce_dependency_floors` adoption), before binding — and set
  `require_auth=True` outside an explicit dev/open profile.

---

## Known Issues / By-Design Deferrals

None in the package itself. **Consumer adoption is downstream**: each service (canopy, cascor, data,
recurrence) adopting `enforce_auth_posture` at lifespan is a per-service follow-up gated on this
release. The recurrence app's dependency ceiling bump to admit 0.5.0 is open as juniper-recurrence#85.

---

## What's Next

- Per-service SEC-F01 adoption: call `enforce_auth_posture(...)` at the top of each service's
  `lifespan` with `require_auth=True` outside dev/open profiles.
- **juniper-recurrence** merges its ceiling bump (juniper-recurrence#85, `<0.5.0` → `<0.6.0`) and can
  then adopt 0.5.0.

---

## Design & Provenance

- Finding: SEC-F01 from the stack interactive-UX + security audit (SP2′ arc; HO-2 live confirmation)
- Implementation: `enforce_auth_posture()` boot check — juniper-ml#610
- Coverage lift + gate: C-4 (juniper-ml#609) + C-4c blocking gate (juniper-ml#611)
- Release proposal (release-train propose mode) + RK-11 pin lockstep fix: juniper-ml#657
- Full changelog: `juniper-service-core/CHANGELOG.md` (`[0.5.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.5.0 | 2026-07-18 | `auth_posture` — boot-time auth-posture self-check (SEC-F01); fail loud when auth required but unconfigured |
| 0.4.0 | 2026-07-01 | `dependency_floors` — boot-time `juniper-*` floor self-check (E-8); fail loud before binding |
| 0.3.0 | 2026-06-25 | `create_app(lifespan=...)` — optional FastAPI lifespan hook in the app factory |
| 0.2.0 | 2026-06-21 | T2 surface — lifecycle orchestrator / generic routes / snapshots / replay / websocket / worker subsystem |
| 0.1.0 | 2026-06-16 | Initial scaffold — T1 service infrastructure |
