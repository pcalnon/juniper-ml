# juniper-ml v0.6.0 — extras floor-bump — Release Notes (archived)

> Archived verbatim from the GitHub Release [`v0.6.0`](https://github.com/pcalnon/juniper-ml/releases/tag/v0.6.0) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

**Floor-bumps `[clients]`, `[worker]`, and `[servers]` minimums to the versions shipped to PyPI on 2026-05-23 alongside the broader ecosystem release wave (`juniper-cascor` 0.5.0, `juniper-canopy` 0.5.0, `juniper-cascor-worker` 0.4.0, `juniper-cascor-client` 0.4.0, `juniper-data-client` 0.4.1). Semver minor — existing callers pinning `juniper-ml>=0.5.0` are transparently upgraded to the new floor minimums.**

Merged via [#322](https://github.com/pcalnon/juniper-ml/pull/322).

## Pin changes

| Extra      | Before                                                            | After                                                                  |
|------------|-------------------------------------------------------------------|------------------------------------------------------------------------|
| `clients`  | `juniper-data-client>=0.4.0`, `juniper-cascor-client>=0.3.0`      | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.4.0`           |
| `worker`   | `juniper-cascor-worker>=0.3.0`                                    | `juniper-cascor-worker>=0.4.0`                                         |
| `servers`  | `juniper-canopy>=0.3.0`, `juniper-cascor>=0.3.17`, `juniper-data>=0.6.0` | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0` |
| `tools`    | unchanged                                                         | unchanged                                                              |
| `doc-tools`| unchanged                                                         | unchanged                                                              |

The matching lint contract in `tests/test_pyproject_extras.py::EXPECTED_EXTRAS` updates in lockstep.

## Doc surfaces brought into agreement

5 docs now declare the same pin set: `README.md`, `AGENTS.md`, `docs/REFERENCE.md`, `docs/DOCUMENTATION_OVERVIEW.md`, and `docs/QUICK_START.md`.

**Drive-by fix:** the `juniper-config-tools` member of `[tools]` (added via CFG-06 / juniper-ml#320 on 2026-05-22) is now visible in those four extras tables, closing pre-existing doc drift between pyproject and the human-readable references.

## Compatibility notes

- Installing `pip install juniper-ml==0.6.0` (no extras) is unchanged — base dependencies remain `[]`.
- Installing any extra resolves to the new floor minimums, e.g. `pip install juniper-ml[clients]==0.6.0` now installs `juniper-cascor-client>=0.4.0` instead of `>=0.3.0`.
- TestPyPI publish-time install verification exercises both `[clients]` and `[tools]` against the published metadata (extended to `[tools]` in this release; see CHANGELOG).

See the full CHANGELOG section below for context.

---## [0.6.0] - 2026-05-23

### Changed

- **Extras floor-bump to today's ecosystem release wave.**
  `[clients]`, `[worker]`, and `[servers]` now require the versions that
  shipped to PyPI on 2026-05-23 alongside the broader
  `juniper-cascor` 0.5.0 / `juniper-canopy` 0.5.0 /
  `juniper-cascor-worker` 0.4.0 / `juniper-cascor-client` 0.4.0 /
  `juniper-data-client` 0.4.1 release wave. Specifically:
  - `[clients]`: `juniper-data-client>=0.4.0` → `>=0.4.1`;
    `juniper-cascor-client>=0.3.0` → `>=0.4.0`.
  - `[worker]`: `juniper-cascor-worker>=0.3.0` → `>=0.4.0`.
  - `[servers]`: `juniper-canopy>=0.3.0` → `>=0.5.0`;
    `juniper-cascor>=0.3.17` → `>=0.5.0`; `juniper-data>=0.6.0` (unchanged).
  - `[tools]` and `[doc-tools]` unchanged at this release. The matching
    lint contract in `tests/test_pyproject_extras.py` updates in lockstep.
  Resolved doc surfaces brought into agreement: `README.md`,
  `AGENTS.md`, `docs/REFERENCE.md`, `docs/DOCUMENTATION_OVERVIEW.md`,
  and `docs/QUICK_START.md` all now declare the same pin set.
  Drive-by fix: the `juniper-config-tools` member of `[tools]` (added
  via CFG-06 / juniper-ml#320) is now visible in the README, AGENTS.md,
  REFERENCE.md, and QUICK_START.md tables, closing pre-existing doc
  drift between pyproject and human-readable extras references.
  Version bumped 0.5.0 → 0.6.0 (semver minor: existing callers pinning
  to `juniper-ml>=0.5.0` will be transparently upgraded to the new
  floor minimums).

- **TestPyPI extras-resolution verification extended to `[tools]`.**
  `.github/workflows/publish.yml` now runs a third `pip install` step
  after the bare-package install and the `[clients]` install: it also
  installs `juniper-ml[tools]==${VERSION}` from TestPyPI and imports
  the three `[tools]` packages (`juniper-ci-tools`,
  `juniper-doc-tools`, `juniper-observability`). Both light extras
  (`[clients]` + `[tools]`) are now exercised at publish time, closing
  the gap documented in the v0.5.0 release runbook §7 (which
  previously called out `[tools]` as caught only by the schema lint,
  not at publish time). `[servers]` and `[worker]` remain
  schema-lint-only because their dependency trees are too heavy to
  resolve in every release run. Matching runbook §7 update so the
  documented behavior matches reality.

- **`juniper-ml[all]` install-size advisory corrected** in
  `docs/QUICK_START.md`, `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`,
  and `notes/META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`. The
  original v0.5.0 estimate of "roughly 2 GB" understated the resolved
  on-disk footprint by ~2.5x: the actual figure measured against PyPI
  on 2026-05-21 (Python 3.13, Linux x86_64) was **5 GB on disk after
  install**. The advisory also now gives concrete per-extra footprints
  (`[clients]`, `[tools]`, `[doc-tools]` < 50 MB each; `[servers]`
  < 200 MB). Pure documentation correction; no code or pin changes.
