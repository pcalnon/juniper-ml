# juniper-recurrence v0.2.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.2.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-recurrence keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the record.
> The GitHub Release [`juniper-recurrence-v0.2.0`](https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-v0.2.0) exists.

---

# juniper-recurrence v0.2.0 Release Notes

**Release Date:** 2026-06-24
**Version:** 0.2.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-recurrence (path `juniper-recurrence/`)
**Git tag:** `juniper-recurrence-v0.2.0`
**PyPI:** <https://pypi.org/project/juniper-recurrence/0.2.0/>

---

## Overview

Surfaces the DP-3 readout spectrum at the HTTP + CLI edge: `POST /v1/train` and `POST /v1/crossval` (and the
`train` CLI) now select `readout: "linear" | "rff" | "mlp"` and `ridge="gcv"`, matched to the
`juniper-recurrence-model` 0.1.5 readouts. Ships the container image (OUT-4 / WS-7) that makes the app
deployable.

---

## Fixed

- **CLI `--rff-features` / `--rff-gamma` are now rejected without `--readout rff`** (P2c follow-up). The rule
  was enforced at the HTTP edge (422) but the `train` CLI silently dropped the RFF-only knobs on the linear
  readout. The check now lives in the shared `build_lmu_regressor`, so the CLI and HTTP behave identically
  (the CLI exits 2 with an error message).

## Added

- **HTTP readout enum — select the DP-3 readout over `/v1/train` and `/v1/crossval` (P2c).** The train +
  crossval request bodies (and the `train` CLI) accept `readout: "linear" | "rff"` plus the RFF params
  `rff_features` / `rff_gamma`; the service constructs the matching immutable readout spec and passes it to
  `LMURegressor`. `readout` defaults to the back-compat linear readout; `"rff"` selects the numpy nonlinear
  random-Fourier-feature readout (Rung 2a). Floor-bumps the model pin to `juniper-recurrence-model>=0.1.4`.
- **HTTP readout enum — `readout="mlp"`, the torch MLP readout (DP-3 P3).** Extends the `readout` enum on
  `POST /v1/train`, `POST /v1/crossval`, and the `train` CLI with `"mlp"` (Rung 2b) plus the optional MLP
  hyperparameters. The MLP needs torch **at runtime**, kept optional via a new **`[torch]` extra**; a
  deployment without it still starts and rejects `readout="mlp"` with a clear **503**. Floor-bumps the model
  pin to `juniper-recurrence-model>=0.1.5`.
- **Container image — `Dockerfile` + `.dockerignore` (OUT-4 / WS-7).** A multi-stage, slim (~77 MB) image.
  The LMU stack is numpy-only (no torch). Runs as a non-root `juniper` user; `ENTRYPOINT ["juniper-recurrence"]`
  / `CMD ["serve"]` launches uvicorn on container port 8210. A new `Docker Build & Smoke Test` CI job builds
  the image and asserts `/v1/health` → 200.
- **`ridge="gcv"` at the API + CLI edge (DP-3 P1).** `POST /v1/train` / `POST /v1/crossval` (and
  `juniper-recurrence train --ridge gcv`) now accept `ridge="gcv"` in addition to a non-negative float.

## Changed

- **`juniper-recurrence-model` pin floor → `>=0.1.5`** (was `>=0.1.2`; ceiling unchanged at `<0.2.0`). 0.1.5
  ships the full DP-3 readout spectrum. Publish-first: 0.1.5 must reach PyPI before this app change installs.
- **`[bench]` extra now pins `juniper-data>=0.9.0`** (was `>=0.6.0`) for the `delay_product` capacity
  generator the DP-3 nonlinear-readout benchmark requires.
- **Benchmark `equities_seq` re-bench — stationary target + regularized-readout LMU.** Finding: the published
  r²≈−50 equities failure was dominantly an unregularized-readout artifact (ridge=0), not target
  non-stationarity; with a regularized readout on the stationary log-return target the Δt-LMU reaches the
  efficient-market predictability ceiling (r²≈0) and beats linear ridge. See juniper-recurrence#28.

---

## Links

- Package CHANGELOG (`[0.2.0]` section): <https://github.com/pcalnon/juniper-recurrence/blob/main/juniper-recurrence/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-recurrence/0.2.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-v0.2.0>
