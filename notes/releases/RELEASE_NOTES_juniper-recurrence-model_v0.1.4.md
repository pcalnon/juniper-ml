# juniper-recurrence-model v0.1.4 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.1.4]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-recurrence keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the record and continues the
> series past `_v0.1.2`.
> The GitHub Release [`juniper-recurrence-model-v0.1.4`](https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.4) exists.

---

# juniper-recurrence-model v0.1.4 Release Notes

**Release Date:** 2026-06-21
**Version:** 0.1.4
**Release Type:** PATCH
**Repository:** pcalnon/juniper-recurrence (path `juniper-recurrence-model/`)
**Git tag:** `juniper-recurrence-model-v0.1.4`
**PyPI:** <https://pypi.org/project/juniper-recurrence-model/0.1.4/>

---

## Overview

DP-3 readout-spectrum, **phase P2a** — the numpy **nonlinear** readout (Rung 2a). Additive and
backward-compatible (the default readout is unchanged), hence a patch release.

---

## Added

- **`RFFReadout` / `RFFReadoutSpec` (Rung 2a)** — a numpy nonlinear readout:
  `standardize(M) → random Fourier features → ridge`. `φ(M) = √(2/D)·cos(standardize(M)·W + b)` with
  `W ~ 𝒩(0, γ²I)`, `b ~ U[0, 2π)` sampled once at `fit` from the model's `random_seed` (data-independent,
  fixed across folds — cross-fold safe via the immutable spec). The design matrix is
  `[ φ(standardize(M)) | target_dt | 1 ]`: the RFF map applies to the memory block only; `target_dt` and the
  bias stay linear (D-WS4-2). Use via `LMURegressor(readout=RFFReadoutSpec(…))`. New public exports:
  `RFFReadout`, `RFFReadoutSpec`.
- **Bandwidth selection** — `γ` via the median heuristic on standardized `M` (`gamma="median"`, default;
  ridge/GCV cannot select `γ`), or a fixed float. The readout penalty is **GCV-selected by default**
  (`ridge="gcv"`); ridge is mandatory for this rung (`γ`/`D` are high-variance).
- **Mandatory per-column standardization of `M`** (train-fold-only; zero-variance columns guarded to std=1
  so predictions stay finite) — keeps the isotropic `W` from being dominated by the high-energy low-order
  Legendre columns.

## Changed

- **Serializer registry now includes `"rff"`.** `RFFReadout` persists `W`, `b`, the standardization stats,
  and the solved coefficients as float64 `readout__*` arrays + a `meta["readout"]` descriptor. Bit-exact
  lossless serialization for the `cos`-of-matmul path is **gated by an RFF conformance subclass** (in-process;
  no cross-machine claim). `D` is capped to the fold size (`p/n` guard; ridge handles the remainder).
  `model._coef` is `None` for the (nonlinear) RFF readout, as for any non-linear rung.

---

## Links

- Package CHANGELOG (`[0.1.4]` section): <https://github.com/pcalnon/juniper-recurrence/blob/main/juniper-recurrence-model/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-recurrence-model/0.1.4/>
- GitHub Release: <https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.4>
