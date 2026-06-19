# v0.4.1 — juniper-observability companion + publish workflow — Release Notes (archived)

> Archived verbatim from the GitHub Release [`v0.4.1`](https://github.com/pcalnon/juniper-ml/releases/tag/v0.4.1) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

## Summary

Companion release that ships the new **`juniper-observability`** sibling
package (alpha) under `juniper-observability/`, plus the workflows that
publish it independently of the meta-package.

This is a docs / metadata release for `juniper-ml` itself — no runtime
code in the meta-package changed. The headline is the new sibling.

## Highlights

- **`juniper-observability` (alpha `0.1.1a`)** — shared observability
  primitives (health models, structured logging, request-id +
  Prometheus middleware, cross-service constants, Sentry init with
  SEC-10 `before_send`). Shipped as its own PyPI distribution; not yet
  wired into `juniper-ml[all]`.
- **`.github/workflows/ci-observability.yml`** — dedicated CI for the
  observability package.
- **`.github/workflows/publish-observability.yml`** — OIDC trusted
  publishing (TestPyPI → install verification → PyPI) keyed off the
  `juniper-observability-v*` tag namespace, with `verbose: true` on
  both upload steps so 4xx failures surface the underlying response
  body.
- Hardcoded-values refactor (Wave 3 + 4): `worktree_cleanup.bash`
  derives `MAIN_REPO` from `${BASH_SOURCE[0]}`; all 6
  `util/get_cascor_*.bash` REST utilities + `juniper_plant_all.bash`
  read `JUNIPER_CASCOR_HOST` / `JUNIPER_CASCOR_PORT` from the
  environment.
- New `tests/test_worktree_cleanup.py` regression suite.
- METRICS-MON roadmap and R2.1 shared-observability design notes under
  `notes/code-review/`.

See [CHANGELOG.md](CHANGELOG.md) for the full list.

## Verifying installation

```bash
pip install --upgrade juniper-ml==0.4.1
python -c "import importlib.metadata; print(importlib.metadata.version('juniper-ml'))"
```
