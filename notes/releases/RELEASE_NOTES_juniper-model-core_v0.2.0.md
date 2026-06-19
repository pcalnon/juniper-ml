# juniper-model-core v0.2.0 — cross-validation / fold-executor layer — Release Notes (archived)

> Archived verbatim from the GitHub Release [`juniper-model-core-v0.2.0`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-model-core-v0.2.0) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

# juniper-model-core v0.2.0 — Cross-Validation / Fold-Executor Layer

**Release Date:** 2026-06-17
**Version:** 0.2.0
**Codename:** Fold Executor
**Release Type:** MINOR (backward-compatible)
**Tag:** `juniper-model-core-v0.2.0`

---

## Overview

`juniper-model-core` 0.2.0 adds the **cross-validation / fold-executor layer**
(`juniper_model_core.crossval`) — the model-agnostic orchestration tier *above* a single model
that the recurrence WS-4b app build explicitly deferred. It loops folds, fits a fresh model per
fold, scores held-out, and aggregates — built purely on the existing `TrainableModel` contract, so
it drives *any* conforming model (the conformance `ReferenceLinearModel`, the recurrence
`LMURegressor`, a future cascor adapter). The layer is optional (behind a new `[crossval]` extra)
and leaves the package's signature dependency-free base import intact.

> **Status:** STABLE behavior, alpha package line — additive and backward-compatible; no breaking changes.

---

## Release Summary

- **Release type:** MINOR
- **Primary focus:** New feature — cross-validation / fold-executor layer
- **Breaking changes:** NO (the `predict` ABC widening is additive / LSP-safe)
- **Dependency-free base import:** preserved (`crossval` and the new `_metrics` helper are numpy-gated and never re-exported from the top-level package)

---

## What's New

### Cross-validation / fold-executor layer (`juniper_model_core.crossval`)

A model-agnostic orchestration tier on the `TrainableModel` contract. Two contract gaps shaped the
API: the contract has no `reset()` / `clone()` (so the executor takes a **model factory**) and no
held-out `score()` (so scoring is computed **externally**), keeping the ABC lean.

**Public API (install the `[crossval]` extra — numpy):**

- `walk_forward_folds(n_samples, *, n_folds, scheme="expanding", min_train=None, embargo=0, order=None)`
  — index-based, shape-agnostic walk-forward folds (expanding / rolling; `embargo` gap to prevent
  leakage; chronological `order` key). Returns `Fold(train_idx, eval_idx)`.
- `cross_validate(model_factory, X, y, folds, *, aux=None, on_event=None, pass_eval_as_val=False, map_fn=map)`
  — fresh model per fold, held-out predict + external scoring, per-metric mean / std aggregate.
  Per-sample `aux` slicing for the 3-D Δt path (`dt` / `readout_mask` / `seq_lengths`);
  `pass_eval_as_val=False` default (held-out purity); a `map_fn` seam for a future
  parallel / distributed worker (serial by default); fold-tagged `on_event`. Returns
  `CrossValResult(task_type, folds, eval_aggregate, eval_std)`.
- `regression_metrics(y_true, y_pred)` / `score(task_type, y_true, y_pred)` — held-out scoring;
  regression implemented, classification raises `NotImplementedError` (an additive drop-in later).

### Shared metric source (`juniper_model_core._metrics`)

The canonical regression-metric math (`{mse, rmse, mae, r2, loss}`, with `loss == mse`) now lives
in one private module that both `crossval.metrics` and the conformance kit's reference model call,
so the two implementations can no longer drift.

### `TrainableModel.predict` contract widened

`predict(self, X)` → `predict(self, X, **kw)` (decision D3; additive, LSP-safe). Sequence models may
read `dt` / `readout_mask` / `seq_lengths` from `**kw`, symmetric with `fit`. Existing bare
`predict(X)` implementers and callers are unaffected.

---

## Public API Changes

| Symbol | Change | Breaking? |
| --- | --- | --- |
| `juniper_model_core.crossval.*` | New module (behind the `[crossval]` extra) | No |
| `TrainableModel.predict` | Widened `(self, X)` → `(self, X, **kw)` | No (LSP-safe) |
| `[crossval]` extra | New (`numpy>=1.24`) | No |

---

## Test Results

| Metric | Result |
| --- | --- |
| Tests passed | 94 |
| Coverage | 97.45% (gate 85%) |
| Build | `twine check` PASS; bare-wheel dependency-free import smoke PASS |

Per-module coverage of the new code: `metrics` 100%, `_metrics` 100%, `splits` 98%, `executor` 98%.
The bare-wheel smoke confirms `import juniper_model_core` pulls no numpy and `crossval` is correctly
gated behind the `[crossval]` extra.

---

## Upgrade Notes

Backward-compatible. To use the new layer:

```bash
pip install "juniper-model-core[crossval]>=0.2.0"
```

```python
from juniper_model_core.crossval import walk_forward_folds, cross_validate

folds = walk_forward_folds(len(X_full), n_folds=5, order=window_end_date)
result = cross_validate(lambda fold: MyModel(...), X_full, y_full, folds, aux={"dt": dt})
print(result.eval_aggregate, result.eval_std)
```

The base `import juniper_model_core` remains dependency-free; `crossval` is imported explicitly and
requires the `[crossval]` extra (numpy). Existing consumers pinned `>=0.1.0,<0.2.0` keep resolving
0.1.x and are unaffected until they opt into a `crossval` feature.

---

## Known Issues

- Held-out scoring is **regression-only** in v1; `score()` raises `NotImplementedError` for
  classification (deferred — additive later, no change to the regression path).
- Fold execution is **serial** in v1; the `map_fn` seam is in place for a future
  parallel / distributed worker (WS-8 / OQ-11), but no parallel backend ships here.

---

## What's Next

- **Consumers (Phase 3):** the recurrence `/v1/crossval` endpoint + a recurrence-side
  `LMURegressor`-over-CV test (the real second-implementer proof).
- Classification held-out metrics; multi-entity (ticker) embargo-aware walk-forward; optional
  server-side fold materialization in `juniper-data`.

---

## Design & Provenance

- Build roadmap (decisions D1–D5, ratified 2026-06-17): `notes/JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md`
- Ratified layer design: `notes/JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`
- Contract spec (D1–D10): `notes/JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`
- Pull request: #442 · Full changelog: `juniper-model-core/CHANGELOG.md` (`[0.2.0]`)

---

## Contributors

- Paul Calnon (@pcalnon)

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 0.2.0 | 2026-06-17 | Cross-validation / fold-executor layer; `predict(**kw)` ABC; `[crossval]` extra |
| 0.1.0 | 2026-06-14 | Initial scaffold (WS-3): `TrainableModel` / `GrowableModel` contract + conformance kit |
