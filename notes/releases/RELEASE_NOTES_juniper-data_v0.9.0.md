# juniper-data v0.9.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.9.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-data keeps a local `notes/releases/` copy; per plan §10.2
> the central `juniper-ml` archive is canonical, so this file centralizes the record.
> The GitHub Release [`v0.9.0`](https://github.com/pcalnon/juniper-data/releases/tag/v0.9.0) exists.

---

# juniper-data v0.9.0 Release Notes

**Release Date:** 2026-06-22
**Version:** 0.9.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-data
**Git tag:** `v0.9.0`
**PyPI:** <https://pypi.org/project/juniper-data/0.9.0/>

---

## Overview

A minor release adding the `delay_product` synthetic time-series generator — the DP-3 capacity instrument
whose regression target is a bilinear product of two delayed in-window values, provably unfittable by a
linear readout but fittable by a non-linear one. It is the capacity-demonstrating dataset that exposes a
clear nonlinear ≫ linear r² gap for the recurrence readout-spectrum work.

---

## Added

- **New `delay_product` synthetic time-series generator (DP-3 capacity instrument).** An irregularly-sampled
  sinusoid superposition (the same non-uniform Δt sampling as `irregular_sine`) whose regression target is
  the **bilinear product of two delayed in-window values**, `y = x(t−τ₁)·x(t−τ₂)`, with `lag1` / `lag2`
  step-delays kept strictly inside the lookback. The product is a quadratic form in the (linear) LMU memory
  state, so a **linear readout provably cannot fit it** (r² bounded below 1) while a **non-linear
  (random-Fourier-feature) readout can** — making it the capacity-demonstrating dataset that exposes a clear
  nonlinear ≫ linear r² gap, complementing the near-linear synthetics where the linear readout is already at
  its ceiling. Emits the standard additive 3-D NPZ contract
  (`{X, y, dt, target_dt, observed_mask}_{train,test,full}`, `task_type="regression"`, `time_unit="steps"`)
  and reuses the leakage-safe `window_timed_series` windowing. Registered as `delay_product`; numpy-only, no
  extra. See juniper-ml `notes/JUNIPER_RECURRENCE_DP3_READOUT_SPECTRUM_DESIGN_2026-06-20.md` §8a.

---

## Links

- Package CHANGELOG (`[0.9.0]` section): <https://github.com/pcalnon/juniper-data/blob/main/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-data/0.9.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-data/releases/tag/v0.9.0>
