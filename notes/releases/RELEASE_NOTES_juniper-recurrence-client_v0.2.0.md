# juniper-recurrence-client v0.2.0 — Release Notes (archived)

> **Retroactive backfill** — authored 2026-07-12 for the PyPI release-train **Phase 0.3** central-archive
> backfill ([`JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`](../JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md) §12 step 0.3; drift findings F-2/F-3).
> Content is sourced from the package `CHANGELOG.md` `[0.2.0]` section plus the git tag date; it is **not** a
> verbatim copy of the GitHub Release body. juniper-recurrence keeps a local `notes/releases/` copy; per plan
> §10.2 the central `juniper-ml` archive is canonical, so this file centralizes the current client release
> (no earlier recurrence-client archive existed centrally).
> The GitHub Release [`juniper-recurrence-client-v0.2.0`](https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-client-v0.2.0) exists.

---

# juniper-recurrence-client v0.2.0 Release Notes

**Release Date:** 2026-06-24
**Version:** 0.2.0
**Release Type:** MINOR
**Repository:** pcalnon/juniper-recurrence (path `juniper-recurrence-client/`)
**Git tag:** `juniper-recurrence-client-v0.2.0`
**PyPI:** <https://pypi.org/project/juniper-recurrence-client/0.2.0/>

---

## Overview

The client forwards the DP-3 readout-spectrum selectors added to the recurrence service in 0.2.0. `train()`
and `crossval()` gain the `readout` selector (`"linear" | "rff" | "mlp"`), the RFF/MLP knobs, and
`ridge="gcv"`, each forwarded verbatim in the request body. Backward compatible — all parameters are optional;
unset means an unchanged request body.

---

## Added

- **`readout` selection forwarded by `train()` / `crossval()` (DP-3 P2c).** Both methods gain
  `readout: Optional[Literal["linear", "rff"]]`, `rff_features: Optional[int]`, and `rff_gamma:
  Optional[Union[float, Literal["median"]]]`, forwarded verbatim so callers can select the service's
  nonlinear RFF readout (Rung 2a). Backward compatible — all optional; unset ⇒ an unchanged request body.
- **`readout="mlp"` + MLP knobs forwarded by `train()` / `crossval()` (DP-3 P3).** Both methods widen
  `readout` to `Optional[Literal["linear", "rff", "mlp"]]` and gain `mlp_hidden` / `mlp_weight_decay` /
  `mlp_lr` / `mlp_max_epochs` / `mlp_patience` (all `Optional`), forwarded verbatim so callers can select the
  service's torch MLP readout (Rung 2b). (The service needs its own `[torch]` extra to fulfil `readout="mlp"`.)
- **`ridge="gcv"` accepted by `train()` / `crossval()` (DP-3 P1).** The `ridge` parameter widens from
  `Optional[float]` to `Optional[Union[float, Literal["gcv"]]]`, forwarded verbatim (no client-side
  validation change).

---

## Links

- Package CHANGELOG (`[0.2.0]` section): <https://github.com/pcalnon/juniper-recurrence/blob/main/juniper-recurrence-client/CHANGELOG.md>
- PyPI: <https://pypi.org/project/juniper-recurrence-client/0.2.0/>
- GitHub Release: <https://github.com/pcalnon/juniper-recurrence/releases/tag/juniper-recurrence-client-v0.2.0>
