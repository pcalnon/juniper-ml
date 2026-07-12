# juniper-data-client v0.4.2 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.4.2]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-data-client keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the record.
> The GitHub Release [`v0.4.2`](https://github.com/pcalnon/juniper-data-client/releases/tag/v0.4.2) exists.

---

# juniper-data-client v0.4.2 Release Notes

**Release Date:** 2026-06-17
**Version:** 0.4.2
**Release Type:** PATCH
**Repository:** pcalnon/juniper-data-client
**Git tag:** `v0.4.2`
**PyPI:** <https://pypi.org/project/juniper-data-client/0.4.2/>

---

## Overview

A patch release that publishes the `validate_npz_contract` NPZ data-contract validator (present in the source
tree since the WS-1 data foundation but absent from the published 0.4.1 wheel), adds a
`JUNIPER_DATA_API_KEY_FILE` Docker-secret indirection to the client, and moves the CI lints onto the shared
`juniper-ci-tools` console scripts.

---

## Added

- **`validate_npz_contract` NPZ data-contract validator** — public helper
  (`from juniper_data_client import validate_npz_contract`) that classifies an artifact's array bundle as
  `"tabular"` (2-D `X`) or `"sequence"` (3-D `X` with the WS-1 irregular-Δt keys) and validates the contract
  invariants (`dt >= 0`, `dt[:, 0] == 0`, mask/shape consistency) with a configurable `dt_atol`. Lets
  consumers (e.g. the juniper-recurrence app) gate 3-D Δt artifacts up front. Shipped in the source tree since
  the WS-1 data foundation but **absent from the published 0.4.1 wheel**; 12 unit tests in
  `tests/test_contract.py`.
- **`JUNIPER_DATA_API_KEY_FILE` Docker-secret indirection** (defense-in-depth follow-up to cascor#331):
  `JuniperDataClient` now resolves its API key from a `JUNIPER_DATA_API_KEY_FILE` env var (a path to a file
  whose stripped contents are the key) before falling back to the plain `JUNIPER_DATA_API_KEY` env var. An
  explicit `api_key=` constructor argument still wins over both. New `API_KEY_FILE_ENV_VAR` constant and a
  module-private `_resolve_api_key_from_env()` helper; 3 unit tests pin the precedence chain.
- **CI lints now run via the `juniper-ci-tools` PyPI package** — the AGENTS.md version-drift lint and the
  workflow script-path lint run from the shared `juniper-ci-tools>=0.2.0` console scripts; the former inline
  `util/` copies were removed (includes the one-line `AGENTS.md` bump 0.3.2 → 0.4.1 clearing the drift).
- **AGENTS.md header-schema lint + auto-bump workflow** — adopts `juniper-ci-tools` v0.4.0's AGENTS.md
  header-schema lint plus the companion `agents-md-touch-up` workflow that auto-refreshes the `Last Updated`
  field on PRs touching `AGENTS.md`.

## Changed

- **README compatibility matrix sync** — refreshed the README compatibility matrix for the cascor / canopy
  `0.5.0` and cascor-worker `0.4.0` releases.

---

## Links

- Package CHANGELOG (`[0.4.2]` section): <https://github.com/pcalnon/juniper-data-client/blob/main/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-data-client/0.4.2/>
- GitHub Release: <https://github.com/pcalnon/juniper-data-client/releases/tag/v0.4.2>
