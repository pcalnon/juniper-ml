# juniper-model-core v0.3.0 — multi-entity walk-forward folds — Release Notes

> Canonical release notes for the GitHub Release [`juniper-model-core-v0.3.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-model-core-v0.3.0) (pcalnon/juniper-ml), authored 2026-06-19
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)). This file is the canonical source for the Release body.

---

# juniper-model-core v0.3.0 — Multi-Entity Walk-Forward Folds

**Release Date:** 2026-06-19
**Version:** 0.3.0
**Codename:** Panel Folds
**Release Type:** MINOR (backward-compatible)
**Tag:** `juniper-model-core-v0.3.0`

---

## Overview

`juniper-model-core` 0.3.0 generalizes the cross-validation splitter from a single time series to
**multi-entity ("panel") data** — multiple tickers, sensors, or subjects in one dataset. It adds a
single additive, keyword-only parameter, `walk_forward_folds(..., groups=)`, that keeps folds pooled
and date-ordered while applying the leakage **`embargo` purge per entity** rather than globally. This
closes a subtle look-back leak that a single global-rank embargo leaves open on a panel, and it is
fully backward-compatible: `groups=None` (the default) is byte-identical to the prior single-series
behavior.

> **Status:** STABLE behavior, alpha package line — additive and backward-compatible; no breaking changes.

---

## Release Summary

- **Release type:** MINOR
- **Primary focus:** New feature — multi-entity ("panel") embargo-aware walk-forward folds
- **Breaking changes:** NO (`groups` is keyword-only with a `None` default; the `None` path is byte-identical to 0.2.0)
- **Dependency-free base import:** preserved (`crossval` remains numpy-gated and is never re-exported from the top-level package)

---

## What's New

### Multi-entity ("panel") walk-forward folds (`walk_forward_folds(..., groups=)`)

`walk_forward_folds` gains an optional `groups: np.ndarray | None = None` parameter — a per-sample
entity id (e.g. `ticker_code`) of length `n_samples`. When supplied, the splitter treats the data as
a panel:

- **Folds stay pooled and date-ordered.** Train = all entities' windows before each cut; eval = the
  next block across all entities. The fold boundaries are driven by the shared chronological `order`,
  exactly as in the single-series case.
- **The `embargo` purge is applied per group.** From each fold's train side, the last `embargo`
  windows *of each entity* (by that entity's own `order`) are dropped. On a panel this is the correct
  leakage guard: a single global-rank gap of `embargo` rows mostly drops *other* entities' windows,
  leaving the cut entity's own most-recent windows adjacent to its eval block. The per-group purge
  removes exactly the windows that could overlap a per-window-step look-back for the entity being
  evaluated.

Set `embargo` to at least the look-back length (expressed in windows) to fully purge a
per-window-step look-back for every entity.

`groups=None` (default) is byte-identical to the 0.2.0 single-series behavior (parity-tested against
the un-`groups`ed path), so existing callers are unaffected.

```python
from juniper_model_core.crossval import walk_forward_folds, cross_validate

# X_full: (n, T, F) windows pooled across tickers; ticker_code/window_end_date are per-window 1-D keys.
folds = walk_forward_folds(
    len(X_full), n_folds=5, embargo=20, order=window_end_date, groups=ticker_code
)
result = cross_validate(lambda fold: MyModel(...), X_full, y_full, folds, aux={"dt": dt})
```

`cross_validate` is unchanged: it consumes the `folds` list, so multi-entity support is entirely a
property of how the folds were generated.

---

## Public API Changes

| Symbol | Change | Breaking? |
| --- | --- | --- |
| `walk_forward_folds` | New keyword-only param `groups: np.ndarray \| None = None` (per-group embargo on a pooled date-ordered split) | No (`None` default == 0.2.0 behavior) |
| `walk_forward_folds` | New `ValueError` when `groups` length != `n_samples` | No (input validation; mirrors the existing `order` check) |

No other symbols changed. `cross_validate`, `Fold`, `FoldResult`, `CrossValResult`,
`regression_metrics`, `score`, and the `TrainableModel` contract are unchanged from 0.2.0.

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests passed | 103 |
| Coverage | 97.54% (gate 95%) |
| Build | `twine check` PASS; bare-wheel dependency-free import smoke PASS |

The splitter module (`crossval/splits.py`) is at 98% line coverage; the new `groups` branch is fully
exercised (parity vs. the single-series path, pooled eval blocks, per-group embargo purge, per-group
leakage guard, length validation, determinism, and both fold-skip guards). The bare-wheel smoke
confirms `import juniper_model_core` still pulls no numpy and `crossval` stays behind the `[crossval]`
extra.

---

## Upgrade Notes

Backward-compatible. To use multi-entity folds:

```bash
pip install "juniper-model-core[crossval]>=0.3.0"
```

Pass a per-sample `groups` array (entity ids) alongside the chronological `order` key. Existing
single-series callers need no change — omit `groups` (or pass `None`) and behavior is identical to
0.2.0. Consumers pinned `>=0.2.0,<0.3.0` keep resolving 0.2.x and are unaffected until they opt into
the `groups` parameter and widen their pin.

---

## Known Issues

- Held-out scoring remains **regression-only**; `score()` raises `NotImplementedError` for
  classification (deferred — additive later).
- Fold execution remains **serial**; the `map_fn` seam is in place for a future
  parallel / distributed worker (WS-8 / OQ-11), but no parallel backend ships here.
- The per-group embargo is expressed in **windows**, not wall-clock time; for irregular sampling,
  size `embargo` to the maximum look-back window count.

---

## What's Next

- A first real multi-entity consumer (e.g. an equities panel over `cross_validate`), proving the
  per-group embargo end-to-end on a non-synthetic dataset.
- Classification held-out metrics; optional server-side fold materialization in `juniper-data`; a
  parallel `map_fn` backend (WS-8 / OQ-11).
- The cascor model-core conformance adapter (WS-6) and any canopy-side surfacing of cross-validation
  (WS-5) consume this layer unchanged.

---

## Design & Provenance

- Phase 4 evaluation (multi-ticker recommendation, Option B): `notes/JUNIPER_MODEL_CORE_CROSSVAL_PHASE4_EVALUATION_2026-06-18.md`
- Build roadmap (decisions D1–D5, ratified 2026-06-17): `notes/JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md`
- Ratified layer design: `notes/JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`
- Pull request: #472 (merge `38f40ce`) · Full changelog: `juniper-model-core/CHANGELOG.md` (`[0.3.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.3.0 | 2026-06-19 | Multi-entity ("panel") walk-forward folds: `walk_forward_folds(..., groups=)` with per-group embargo |
| 0.2.0 | 2026-06-17 | Cross-validation / fold-executor layer; `predict(**kw)` ABC; `[crossval]` extra |
| 0.1.0 | 2026-06-14 | Initial scaffold (WS-3): `TrainableModel` / `GrowableModel` contract + conformance kit |
