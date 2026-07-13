# juniper-recurrence-model v0.1.3 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.1.3]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-recurrence keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the record and continues the
> series past `_v0.1.2`.
> The GitHub Release [`juniper-recurrence-model-v0.1.3`](https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.3) exists.

---

# juniper-recurrence-model v0.1.3 Release Notes

**Release Date:** 2026-06-21 (git tag / PyPI upload; the package CHANGELOG heads this section 2026-06-20)
**Version:** 0.1.3
**Release Type:** PATCH
**Repository:** pcalnon/juniper-recurrence (path `juniper-recurrence-model/`)
**Git tag:** `juniper-recurrence-model-v0.1.3`
**PyPI:** <https://pypi.org/project/juniper-recurrence-model/0.1.3/>

---

## Overview

DP-3 readout-spectrum, **phase P1**. Makes the LMU regressor's only trained surface — its *readout* — a
configurable spectrum, and ships the cheap data-ranked lever (a GCV-selected regularised linear readout).
Fully backward compatible: an additive, optional API — hence a patch release (stays inside every existing
`<0.2.0` consumer pin).

---

## Added

- **Readout-spec API** (`juniper_recurrence_model.readouts`): the `Readout` / `ReadoutSpec` protocols,
  `LinearReadout`, and the immutable `LinearReadoutSpec(ridge=…)`. `LMURegressor` now accepts an explicit
  `readout=<spec>` (a *spec*, not a live object — so a spec shared across cross-validation folds can never
  leak one fold's fitted weights into another). New public exports: `Readout`, `ReadoutSpec`,
  `LinearReadout`, `LinearReadoutSpec`, `RidgeParam`.
- **GCV ridge selection** (`ridge="gcv"`): closed-form generalised-cross-validation choice of the readout L2
  penalty at `fit` — one SVD of the (centred) design matrix + a 1-D log-grid search, no held-out split and no
  inner-CV refit. The selected λ is written back to `model.ridge` and persisted in the serialized metadata.
  Resolves juniper-recurrence#28.

## Changed

- **`LMURegressor` delegates its readout** to the spec (the fixed Δt LMU memory rollout is unchanged).
  `LMURegressor(d, theta, ridge=…)` remains **byte-identical** to the pre-DP-3 model (the default
  `LinearReadoutSpec(ridge=0.0)`); `ridge` widened to `float | Literal["gcv"]`. The readout receives the
  memory block `M` only; `LMURegressor` keeps owning `target_dt` (a linear side-channel appended after any
  nonlinearity) and the bias column (preserves D-WS4-2). `model._coef` is now a read-only forwarding property
  to the linear readout's coefficients.
- **Serializer schema 2.** `LMUSerializer` now persists the readout's own state as namespaced `readout__*`
  arrays + a nested `meta["readout"]` descriptor (with a `kind` tag), reconstructed via a readout registry on
  load. **Pre-DP-3 `.npz` files still load** (a top-level `coef` + no `meta["readout"]` falls back to a
  linear readout from `meta["ridge"]`). The LMU envelope keys (esp. `meta["d"]` = memory order) stay frozen.

---

## Links

- Package CHANGELOG (`[0.1.3]` section): <https://github.com/pcalnon/juniper-recurrence/blob/main/juniper-recurrence-model/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-recurrence-model/0.1.3/>
- GitHub Release: <https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.3>
