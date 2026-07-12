# juniper-recurrence-model v0.1.5 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.1.5]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-recurrence keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the current model release.
> The GitHub Release [`juniper-recurrence-model-v0.1.5`](https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.5) exists.

---

# juniper-recurrence-model v0.1.5 Release Notes

**Release Date:** 2026-06-24 (git tag / PyPI upload; the package CHANGELOG heads this section 2026-06-23)
**Version:** 0.1.5
**Release Type:** PATCH
**Repository:** pcalnon/juniper-recurrence (path `juniper-recurrence-model/`)
**Git tag:** `juniper-recurrence-model-v0.1.5`
**PyPI:** <https://pypi.org/project/juniper-recurrence-model/0.1.5/>

---

## Overview

DP-3 readout-spectrum, **phase P3** — the optional **torch MLP readout (Rung 2b)** plus the `LMURegressor`
validation plumbing that feeds it. Additive and backward compatible (the default readout and the closed-form
rungs are unchanged), hence a patch release. Ratified GO 2026-06-23
(`notes/JUNIPER_DECISIONS_RATIFIED_2026-06-23.md` D5, in juniper-ml) as capability insurance for future
complex / hybrid datasets — the current dataset catalog does not itself require it.

---

## Added

- **`MLPReadout` / `MLPReadoutSpec` (Rung 2b)** — an optional torch MLP readout behind a new `[torch]` extra
  (`torch>=2.10.0`, the ecosystem CVE-2025-3001 security floor; ships cp314 wheels). Architecture:
  `standardize(M) → GELU trunk (h→h) → linear head over [trunk | extra]`, with internal target
  standardization. Training is **CPU-only, single-threaded, float32, `use_deterministic_algorithms(True)`**,
  so an in-process save→load→predict round-trip is bit-exact within a machine (no cross-machine claim). State
  persists as **named numpy arrays** (never `torch.save`; the serializer loads with `allow_pickle=False`).
  `torch` is imported **lazily**, so the base package stays numpy-only and torch-free. New public exports:
  `MLPReadout`, `MLPReadoutSpec`. Use via `LMURegressor(readout=MLPReadoutSpec(…))`.
- **`Readout.fit` validation arguments** — the `Readout` protocol's `fit` gained optional `M_val` /
  `extra_val` / `y_val` keywords. The closed-form linear and RFF rungs accept and ignore them; the MLP rung
  uses them for **validation-driven early stopping** (relative `min_delta`, `patience`), keeping the
  best-validation weights.

## Changed

- **`LMURegressor.fit` plumbs `X_val` / `y_val` through to the readout.** When validation data is supplied
  (directly, or by the crossval / conformance harness), `fit` builds a held-out feature block and passes it
  to `readout.fit`. Optional `*_val` timing kwargs make the val block Δt-faithful; absent (the conformance /
  crossval convention) it falls back to the uniform-grid construction.
- **`TrainResult` reports the readout's true training diagnostics.** `n_epochs` reflects the readout's
  trained-epoch count and `stopped_reason` reflects how it stopped (`"early_stopping"` / `"max_epochs"` for
  the MLP). Closed-form readouts read as the canonical single-solve `1` / `"converged"` — preserving the
  crossval `n_epochs == 1` invariant.
- **Serializer registry now includes `"mlp"`** (lazily registered, so the base import never pulls in torch).
  The MLP persists its layer weights/biases + standardization stats as float32 `readout__*` arrays + a
  `meta["readout"]` descriptor; bit-exact lossless serialization is gated by an `MLPReadout` conformance
  subclass. `model._coef` is `None` for the (nonlinear) MLP readout.

---

## Links

- Package CHANGELOG (`[0.1.5]` section): <https://github.com/pcalnon/juniper-recurrence/blob/main/juniper-recurrence-model/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-recurrence-model/0.1.5/>
- GitHub Release: <https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-model-v0.1.5>
