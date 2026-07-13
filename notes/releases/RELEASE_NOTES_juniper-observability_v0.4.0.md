# juniper-observability v0.4.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.4.0]` section plus the git tag date; it is **not** a
> verbatim copy of a GitHub Release body. Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> **No GitHub Release exists for tag `juniper-observability-v0.4.0`** (published tag-only — audit F-1); this
> file is the durable in-repo record.

---

# juniper-observability v0.4.0 Release Notes

**Release Date:** 2026-06-14
**Version:** 0.4.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-ml (path `juniper-observability/`)
**Git tag:** `juniper-observability-v0.4.0` (tag-only; no GitHub Release — audit F-1)
**PyPI:** <https://pypi.org/project/juniper-observability/0.4.0/>

---

## Overview

The foundation release for the ecosystem build-provenance / stale-image-detection effort. It teaches the
shared build-info helper and the readiness response to carry the deployed source revision (git SHA + build
date) so a running service's provenance is visible in Prometheus/Grafana and on `/v1/health/ready`. Both
changes are additive and backward-compatible — no public-symbol change.

---

## Added

- **Build provenance.** `set_build_info(namespace, version, *, git_sha=None, build_date=None)` now accepts
  keyword-only `git_sha` and `build_date` and, when provided, emits them as additional labels on the
  `<namespace>_build` Info metric so the deployed source revision is visible in Prometheus/Grafana. They are
  omitted (not blank) when `None`.
- `ReadinessResponse` gains optional `git_sha` / `build_date` fields (default `None`) so
  `/v1/health/ready` can carry the same provenance.

Both changes are additive and backward-compatible: existing two-argument `set_build_info` callers and
pre-0.4.0 `ReadinessResponse` consumers are unaffected (no public-symbol change). This is the foundation
release for the ecosystem build-provenance / stale-image-detection effort — see juniper-ml
`notes/JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md`. Consumers wanting the provenance
labels should pin `juniper-observability>=0.4.0`.

---

## Links

- Package CHANGELOG (`[0.4.0]` section): <https://github.com/pcalnon/juniper-ml/blob/main/juniper-observability/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-observability/0.4.0/>
- Git tag: <https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.4.0>
