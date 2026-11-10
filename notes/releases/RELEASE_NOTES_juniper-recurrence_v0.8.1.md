# juniper-recurrence v0.8.1 Release Notes

**Release Date:** 2026-11-04
**Version:** 0.8.1
**Release Type:** PATCH
**Priority:** High for any install whose juniper-model-core is 0.2.0: on one, every `POST /v1/crossval` answers 500

---

## Overview

`juniper-recurrence` v0.8.1 raises the `juniper-model-core` floor to `>=0.3.0`. 0.8.0 calls `walk_forward_folds(groups=)` on every cross-validation request, a parameter that first shipped in model-core 0.3.0. Yet it declared `>=0.2.0`, so pip accepted model-core 0.2.0 and `pip check` stayed clean while every `POST /v1/crossval` failed with a `TypeError` (500). The defect was found on 2026-11-04 when the host env JuniperCascor1, refreshed under P12's W0.1, still held model-core 0.2.0. The fix is juniper-recurrence#229.

Upgrading moves model-core to 0.3.x (`pip install -U juniper-recurrence`). An install already on model-core 0.3.x was never affected. No API changes.

---

## What's Changed

### Changed (repository and bench only; neither ships in the wheel)

- **Temporary files go in the repo's gitignored `tmp/`, never `/tmp` (owner directive, 2026-10-26), and the owner's
  rulings on it are applied** (repo-wide, recorded here as the bench is). `/tmp/` is ignored, and `AGENTS.md` §
  Temporary files carries the rule and the rulings, retention included. `juniper-check-doc-links` passes
  `--exclude tmp` in `ci-docs.yml`, and the app image's build context (`juniper-recurrence/.dockerignore`) lists
  `tmp/`; nothing keeps pytest out of it, and counting scripts are to choose their scope as to `tmp/` deliberately
  (the owner's revised ruling).
- **The bench's equities rows pool `trainval` and cut a panel's folds on the global date per entity; a multi-ticker row `equities_seq_panel` joins the single-ticker one** (W5.2 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, the owed
  bench half; `bench/` is not part of the published distribution). `bench/run_benchmark.py` cut row-index folds
  (`walk_forward_folds(n, embargo=2)`) over the composed `full` view, so on a multi-ticker request -- an
  entity-major pool -- ticker A's 2021 landed in train beside ticker B's 2015 in eval, and the last fold
  evaluated the `test` partition the plan reserves (F-P7 / W5.3). `bench/datasets.py`'s `Dataset` now carries
  `order` (`window_end_date`), `groups` (`ticker_code`) and the row's own `embargo`; `equities_seq` loads the
  composed `trainval` view (juniper-recurrence-model 0.6.0's `derive_composed_split`; `_full` is its `"full"`
  case) with those keys and `embargo = lookback`; `run_dataset` passes `order` / `groups` / the row's embargo
  to model-core -- the seam `POST /v1/crossval` uses -- and records a `folding` block (`embargo`, `ordered`,
  `grouped`, `n_entities`, `n_folds`) that the report's per-dataset header prints. The synthetic rows are
  unchanged (row-index folds, embargo 2). The new informational row `equities_seq_panel` (`AAPL` + `MSFT`)
  sits beside `equities_seq`; Band 2b covers both. Four bench tests pin the pool, the keys, the per-entity
  embargo on the date-cut folds, the `run_dataset` seam and the registry (the generator is stubbed; no
  network). Needs juniper-recurrence-model >= 0.6.0, the app's own floor since 0.8.0. `_full`'s derivation
  moved into `_composed`, leaving an 8-line shim; the symbol-loss screen's `WEAKENED` finding on it is the
  intended shape, waived with an enumerated `Allow-Symbol-Loss: func:_full` trailer in the PR range.

### Fixed

- **`juniper-model-core` floor raised to `>=0.3.0`: with model-core 0.2.0 installed, every `POST /v1/crossval`
  answered 500.** `_folds.build_folds` (new in 0.8.0) passes `groups=` to model-core's `walk_forward_folds` on
  every request -- `groups=None` for a keyless single series -- and that keyword-only parameter first shipped in
  juniper-model-core 0.3.0 (2026-06-18). 0.2.0's signature has neither `groups` nor `**kwargs`, so the call raises
  `TypeError: walk_forward_folds() got an unexpected keyword argument 'groups'`, single-series requests included.
  0.8.0 declared `juniper-model-core[crossval]>=0.2.0,<0.4.0`, so pip resolved `juniper-recurrence==0.8.0` with
  model-core 0.2.0 and `pip check` stayed clean. Measured 2026-11-04 on `main` (`e9d0026e`) with 0.2.0 forced: the
  bench lost 4 of 41 (`bench/run_benchmark.py:70` and `bench/test_bench_smoke.py:268` / `:295` raised that
  `TypeError`, and `bench/test_app_e2e.py::test_app_e2e_trains_and_predicts_on_irregular_dt` got
  `POST /v1/crossval -> 500`), and the app suite failed 22 of 362, every one a crossval test. With 0.3.0 or 0.3.2
  swapped in, all of them pass. Now the resolver refuses 0.8.1 with model-core 0.2.0 (`ResolutionImpossible`),
  `pip check` names an existing 0.2.0 install, and `pip install -U juniper-recurrence` moves it to 0.3.x. The bench
  installs through this pin, so it is covered too; the image lock already pins 0.3.1 and does not move.
  `juniper-recurrence-model` keeps `>=0.2.0`: it never passes `groups=`, and its own suite passes on model-core
  0.2.0. `tests/test_pyproject_floors.py` now fails if the floor admits 0.1.0 or 0.2.0 again, or if the image
  lock's model-core pin leaves the range.

---

## Upgrade

```bash
pip install -U "juniper-recurrence>=0.8.1,<0.9.0"
```

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-recurrence/blob/juniper-recurrence-v0.8.1/juniper-recurrence/CHANGELOG.md)
- Fix: juniper-recurrence#229 (squash `2a467adb`)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.8.1.md` (juniper-ml)
