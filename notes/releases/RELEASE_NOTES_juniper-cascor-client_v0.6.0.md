# juniper-cascor-client v0.6.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.6.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. Central-archive convention:
> [`JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`](../JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md) §11.3.
> The GitHub Release [`v0.6.0`](https://github.com/pcalnon/juniper-cascor-client/releases/tag/v0.6.0) exists
> (released 2026-07-11).

---

# juniper-cascor-client v0.6.0 Release Notes

**Release Date:** 2026-07-11
**Version:** 0.6.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-cascor-client
**Git tag:** `v0.6.0`
**PyPI:** <https://pypi.org/project/juniper-cascor-client/0.6.0/>

---

## Overview

A pure-additive minor release that gives the in-memory `FakeCascorClient` test double parity with the real
client's private `_request` escape hatch, so canopy's Start-Training flow can be exercised against the fake
without an `AttributeError` when the real `juniper-cascor-client` package is installed. No existing public
API or wire shape is touched.

---

## Added

- **`FakeCascorClient._request` — in-memory parity for the real client's private escape hatch.**
  juniper-canopy's `CascorServiceAdapter` drives the cascor dataset-staging and experimental-functions
  endpoints through `JuniperCascorClient._request` (the "public-but-private" escape hatch documented in
  cascor #242 — the client still has no first-class methods for those routes), and canopy #438 put that path
  on canopy's trivial-case Start-Training flow (`_ensure_first_start_dataset` → `get_pending_dataset()` /
  `stage_dataset()`). The fake previously did not implement `_request` at all, so any canopy test driving
  `ServiceBackend.start_training()` against `FakeCascorClient` crashed with
  `AttributeError: 'FakeCascorClient' object has no attribute '_request'` the moment the real package was
  installed. The new method mirrors the real signature (`method, path, json=None, params=None`; signature
  parity pinned by a new conformance test) and answers the five routes canopy drives, with response `data`
  shapes copied from the cascor server handlers: `POST /training/dataset` (stage), `DELETE /training/dataset`
  (clear), `GET /training/dataset/pending`, and `GET`/`POST /admin/experimental_functions`. Unknown routes
  raise `JuniperCascorNotFoundError` exactly like a real 404; closed-client and `error_prone`-scenario
  injection behave like every other fake method. `FakeCascorClient.start_training` now also **consumes** any
  staged config on a successful start, mirroring cascor #396's consume-on-start so the canopy pending banner
  clears after a start. New regression class `tests/test_fake_client.py::TestPrivateRequestEscapeHatch`
  (9 tests). Pure-additive: no existing public API or wire shape is touched.

---

## Links

- Package CHANGELOG (`[0.6.0]` section): <https://github.com/pcalnon/juniper-cascor-client/blob/main/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-cascor-client/0.6.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-cascor-client/releases/tag/v0.6.0>
