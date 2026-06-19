# juniper-cascor-model v0.1.0 — Release Notes (archived)

> Archived verbatim from the GitHub Release [`juniper-cascor-model-v0.1.0`](https://github.com/pcalnon/juniper-cascor/releases/tag/juniper-cascor-model-v0.1.0) (pcalnon/juniper-cascor), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

Initial release of **juniper-cascor-model** — the CW-05 candidate-training core (CandidateUnit + activation registry + utils + logging + candidate constants), extracted verbatim from `juniper-cascor/src` and shipped under the same top-level package names so consumer imports resolve unchanged.

This lets **juniper-cascor-worker** execute remote candidates via a single PyPI dependency instead of a `--cascor-path` source-tree mount, unblocking CW-05 (juniper-cascor-worker#97) and the dual-path candidate stall (#319).

**Security:** `torch>=2.10.0` floor — the minimal pin clearing every *fixable* torch CVE affecting `>=2.0`, up to CVE-2025-3001 (`lstm_cell`).

Published via OIDC trusted publishing (TestPyPI → PyPI).
