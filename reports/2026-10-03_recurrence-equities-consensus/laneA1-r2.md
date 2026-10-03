# Lane A — Round 2 measurement re-creation review

**Date:** 2026-10-03  
**Entry points:** `24-c-crossval-shadow.txt`, `21-recurrence-shadow.log`, recurrence `settings.py`; service/data-client artifacts and code named for C2; `juniper-deploy/docker-compose.yml`; recurrence training, schema, predict, snapshot, and crossval routes; frozen dataset metadata; `run_suite.py`, `run_experiment.py`, E-H/base YAML; model-core `splits.py`; `00-baseline.txt`.

## C1 — F-SCI1 rewrite

**Opened:** `24-c-crossval-shadow.txt:2-5`; `21-recurrence-shadow.log:14,16`; recurrence `settings.py:180-183`; `juniper-recurrence/conf/experiments/irregular-sine-rff.yaml`; `util/experiments/suites/p4/e-h-recurrence-real-data.yaml`; `run_experiment.py:1969-1973,1999-2009`.

The captured request body contains only the dataset selector plus `n_folds=5`, `scheme="expanding"`, and `embargo=2`; it carries no `d`, `theta`, `readout`, `ridge`, `rff_features`, or `rff_gamma`. The service log records `d=16 theta=None readout=linear`; `settings.py:183` sets `default_ridge = 0.0`. Thus the artifact supports service-default linear/unregularised operation and a null/data-driven theta request, not the E-H RFF configuration.

Exact train-fold r2 values: `0.45295797869944143`, `0.3223292113086098`, `0.24814986248864412`, `0.18370343780160026`, `0.13759590416847334`. Exact eval-fold r2 values: `-83451.6101647795`, `-814.6647303831381`, `-3.7198060564183617`, `-78.49243017276824`, `-6059.228738766733`. Aggregate eval r2: `-18081.54317403171`.

Exact train-fold RMSE values: `0.012817682670260573`, `0.012093449736157193`, `0.012397932333189862`, `0.014270733977245665`, `0.017475041341989284`. Exact eval-fold RMSE values: `3.2708042478922636`, `0.38471915840307974`, `0.042671330173562304`, `0.24665521570290905`, `1.2377474116389775`. The plan's “≈ 0.012” understates the final two train-fold values.

The response reports five folds and the request reports embargo 2. However, the crossval response descriptor says `split="full"` and `n_windows=1698`; the frozen metadata says `n_samples=1698`, `n_train=1346`. The `1,346 windows` claim describes the train partition, not the crossval population.

`irregular-sine-rff.yaml` specifies `d: 16`, `theta: null`, `ridge: 1.0`, `readout: rff`, `rff_features: 256`, and `rff_gamma: median`. The E-H suite inherits that file and overrides only the dataset to AAPL, 2015-01-01 through 2022-01-01, lookback 64, log-return target, seed 20260807. `run_experiment.py` adds the resolved train hyperparameters to its crossval body. The plan's description of the E-H configuration is correct.

**Verdict: PARTIALLY CONFIRMED.** Configuration and metric claims are supported, but the window count is wrong for the crossval run and “train-fold RMSE ≈ 0.012” is incomplete.

Discrepancy, verbatim: “Selector: AAPL 2015–2022, `log_return`, lookback 64, 1,346 windows” versus artifact `"split":"full","n_windows":1698`.

## C2 — F-S6 and F-S9

**Opened:** recurrence `data.py:60-80`; data-client `client.py:175-204` and `constants.py:193`; recurrence `settings.py:173-183`; `26-e-flat-equities.txt:1-6`; `27-f-default-nan.txt:1-6`; `23-b-train-canopy-seed.txt:1-6`; `21-recurrence-shadow.log:11-12,18-21`.

`data.py:73` constructs `JuniperDataClient(base_url=base_url, api_key=api_key)` without a timeout. `constants.py:193` defines `DEFAULT_TIMEOUT: int = 30`; `client.py:178,188,204` uses it, documents 30 seconds, and assigns it to `self.timeout`. `settings.py:174-178` exposes the data URL and API key only; the next settings are model defaults.

Request timestamps are `04:17:06.773847862` and `04:17:06.778897615`, a `0.005049753 s` separation. The second response is HTTP 409 with `TIME_TOTAL=0.003048`; the first finishes HTTP 422 after `TIME_TOTAL=0.570061`. Log lines 18-21 preserve the same 409-before-422 ordering.

The canopy-seed curl reports `TIME_TOTAL=46.503125`. The fit log reports `duration=34.463s`. Their difference is `12.040125 s` (subject to the log's millisecond rounding).

**Verdict: CONFIRMED.** The compact row's 30-second default, absent setting, lock contention timing, and canopy-seed timing are supported.

## C3 — DEPLOY

**Opened:** `juniper-deploy/docker-compose.yml:155-164,521-523,589-647,653-662,797-806,888-897`.

Pins are exactly: data `0.16.0` at lines 164 and 523; recurrence `0.5.0` at line 598; canopy `0.8.1` at lines 662, 806, and 897. The recurrence service block is lines 589-647. It contains no `volumes:` key and no `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`. Other services do have `volumes:` keys, so this is specific to recurrence rather than a file-wide absence.

**Verdict: CONFIRMED.** F-DEP1/F-DEP2 line references and recurrence-block absence claims match the Compose artifact.

## C4 — CONCURRENCY

**Opened:** recurrence `routers/training.py:37-105`; `schemas.py:162-196`; `routers/predict.py:29-74`; `routers/snapshots.py:137-215`.

`training.py:44` acquires the process-wide `train_lock`; dataset loading begins at line 49; model construction, fit, and state publication all remain inside the outer `try`; line 105 releases the lock in `finally`.

`TrainResponse` fields are `final_metrics`, `n_epochs`, optional `stopped_reason`, and `dataset`; there is no operation/model id. `StatusResponse` fields are `state`, optional `final_metrics`, optional `stopped_reason`, `events`, and optional `restored_from`; there is no operation/model id.

Predict accepts only `PredictRequest` plus injected state/settings. Snapshot save takes a description body; get/restore take a snapshot id, but no training operation/model identity. Thus “snapshots take no id” is accurate only in the finding's operation/model-id sense; snapshot resource ids do exist.

**Verdict: CONFIRMED.** F-CON1/F-CON2's identity and lock claims are supported; the snapshot wording should not be read as denying snapshot IDs.

## C5 — W0.8 / W1.0 / W5.4

**Opened:** `equities_seq-6.0.0-15505731cba5b86d.meta.json`; `run_suite.py:78-81,737-750`; `run_experiment.py:1969-2032,2052-2091`; `irregular-sine-rff.yaml`; `e-h-recurrence-real-data.yaml`; plan Phase 0, Phase 1, and Phase 5 tables/details.

The frozen metadata file exists. It identifies exactly AAPL, start `2015-01-01`, end `2022-01-01`, `regression_target="log_return"`, and `lookback=64` (plus seed 20260807 and generator 6.0.0). W0.8's E-H request/config description matches the two YAML files as detailed under C1.

`run_suite.py:78`'s accepted top-level keys do not include `acceptance`, and an `acceptance` search finds no suite-YAML facility. Lines 737-750 implement a baseline comparison explicitly documented as “REPORTING ONLY”; its verdict does not alter suite exit status. `TERMINAL_OUTCOMES` at line 81 is exactly `succeeded`, `failed`, `stalled`, `timed_out`, with no `degraded`.

`run_experiment.py` does have manifest `acceptance` blocks. For recurrence it accumulates request/phase, save-model, plot, and interruption reasons; line 2030 sets success only when `acceptance_reasons` is empty, and line 2082 writes `acceptance.ok` from `exit_code == EXIT_SUCCESS` plus those reasons. This is driver-computed run/phase/artifact success, not a configurable metric band.

The compact rows and Details bullets for W0.8, W1.0, and W5.4 are internally consistent, and every referenced work-item ID exists in its table.

**Verdict: CONFIRMED.** All requested artifact and code claims are supported.

## C6 — W5.2

**Opened:** model-core `juniper_model_core/crossval/splits.py:41-50,56-79`; recurrence `routers/crossval.py:65-88`; plan Phase 5 W5.2 row and Details bullet.

Exact signature:

```python
def walk_forward_folds(
    n_samples: int,
    *,
    n_folds: int,
    scheme: Literal["expanding", "rolling"] = "expanding",
    min_train: int | None = None,
    embargo: int = 0,
    order: np.ndarray | None = None,
    groups: np.ndarray | None = None,
) -> list[Fold]:
```

Exact route call:

```python
folds = walk_forward_folds(
    sequence.X.shape[0],
    n_folds=req.n_folds,
    scheme=req.scheme,
    embargo=req.embargo,
    min_train=req.min_train,
)
```

The existing API and omitted route arguments are confirmed. The restructuring introduced an internal W5.2 inconsistency: the table says “window embargo ≥ `lookback` + `embargo_days`,” while Details says “Embargo stays in windows and must be ≥ `lookback`” and “`embargo_days` is a separately named duration gap.” Addition across window-count and duration units is not what Details describes.

**Verdict: PARTIALLY CONFIRMED.** The code claim is confirmed; the compact row contradicts its Details bullet.

Discrepancy, verbatim: “window embargo ≥ `lookback` + `embargo_days`” versus “**Embargo stays in windows** and must be ≥ `lookback` ...; `embargo_days` is a separately named duration gap.”

## C7 — Baseline / environment claims

**Opened:** `00-baseline.txt:1-17` and searched the complete artifact for `derive_full_split`.

The JuniperCascor1 `pip check` reports installed `juniper-recurrence-model 0.1.5` against required `>=0.3.0,<0.4.0`, and service-core metadata `0.5.0` against required `>=0.6.0,<0.8.0`. The plain import probe reports model `0.1.5` and service-core module version `0.4.0`; shadowed checkouts report model `0.3.0` and service-core `0.7.0`. This supports the stale service-core metadata/module `0.5.0`/`0.4.0` pair described in W0.1 Details.

The artifact contains no `derive_full_split` import/probe and no occurrence of that symbol. It therefore does not demonstrate that `derive_full_split` is absent; version 0.1.5 alone is not a captured symbol test.

**Verdict: PARTIALLY CONFIRMED.** Version drift is supported; absence of `derive_full_split` is untraceable from `00-baseline.txt`.

Discrepancy: **UNTRACEABLE** — no primary-artifact probe of `derive_full_split` was captured.

## Tally

**CONFIRMED: 4; REFUTED: 0; PARTIALLY CONFIRMED: 3; NO ARTIFACT: 0.**

## What the evidence cannot support

- `24-c-crossval-shadow.txt` cannot support “1,346 windows” as the crossval population; it reports 1,698 full-split windows.
- The captured crossval log shows `theta=None`, not the numerical theta resolved inside each fold.
- The timing artifacts support a roughly 12.04-second curl/log gap, but do not independently partition every second of that gap or prove the Details claim that “nothing” was logged during fetch beyond the supplied service log.
- `00-baseline.txt` does not test or show the absence of `derive_full_split`.
- This review found no Details finding/work-item ID absent from its named compact table. The one restructuring inconsistency found is W5.2's dimensionally mixed compact-row embargo expression versus its Details text.
