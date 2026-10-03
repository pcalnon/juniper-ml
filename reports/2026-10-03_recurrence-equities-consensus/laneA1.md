# Lane A agent A1 — artifact re-derivation

- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A and §7
- **Target**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`
- **Entry point**: `.amp/in/artifacts/recurrence-equities-audit/`
- **Date**: 2026-10-03
- **Brief**: Re-derive artifact-backed claims without reading repository source code.

## 0. Instrument, and whether it could have produced a different answer

<!-- markdownlint-disable MD013 -->
| Instrument | Could it produce a different answer? | Sample size | What was NOT done |
| --- | --- | --- | --- |
| Direct `cat`, `rg`, and `jq` over the archived evidence | Yes. The paired plain/shadow crossval artifacts produce 422 and 200; paired test logs produce both green and failing results. JSON queries expose null, absent, and populated fields distinctly. | One 103-file archive; every artifact named in the 14-point brief was inspected, including 2 manifests, 2 stats files, 10 package test logs, 2 service logs, and the inventory | No source code was read; no service was started; no tests or network requests were run; no artifact was modified. |
<!-- markdownlint-enable MD013 -->

The instrument cannot prove facts absent from the archive, runtime causality beyond the captured outputs, or values that the cited artifact does not record. Verdict units below are atomic claims, not numbered sections.

## 1. Baseline environment

### Versions — VERIFIED / CONTRADICTED

`00-baseline.txt` supports the app and model versions:

> `juniper-recurrence 0.5.0 has requirement ... but you have juniper-recurrence-model 0.1.5.`

It does **not** consistently support the plan's `juniper-service-core 0.5.0`. The `pip check` transcript says:

> `juniper-recurrence 0.5.0 has requirement juniper-service-core<0.8.0,>=0.6.0, but you have juniper-service-core 0.5.0.`

but the same artifact's explicit plain-version probe says:

> `0.4.0 /opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/juniper_service_core/__init__.py`

**CONTRADICTED** for the asserted measured value: the explicit import probe reports **0.4.0**, while `pip check` reports 0.5.0. The artifact is internally inconsistent and cannot establish one installed service-core version.

### `pip check` — VERIFIED

The CasCor environment reports four broken requirements and `exit=1`: two CUDA mismatches, recurrence-model 0.1.5 below the app's `>=0.3.0`, and service-core reported by pip as 0.5.0 below `>=0.6.0`. The JuniperData check says:

> `No broken requirements found.`
>
> `exit=0`

### `derive_full_split` import — NO ARTIFACT

`00-baseline.txt` contains no `derive_full_split` command or import result. The ImportError appears later in `tests-bench-env.log`, but the plan specifically attributes it to `00-baseline.txt`.

## 2. Plain versus shadowed crossval

### HTTP status, detail, and fold metrics — VERIFIED

`31-c-crossval-plain.txt` records:

> `{"detail":"invalid dataset: NPZ artifact is missing required key 'X_full'"}`
>
> `HTTP_STATUS=422`

`24-c-crossval-shadow.txt` records `HTTP_STATUS=200`. In response fold order 0–4, exact train r2 values are:

> `0.45295797869944143`, `0.3223292113086098`, `0.24814986248864412`, `0.18370343780160026`, `0.13759590416847334`

Exact eval r2 values are:

> `-83451.6101647795`, `-814.6647303831381`, `-3.7198060564183617`, `-78.49243017276824`, `-6059.228738766733`

The aggregate is `r2: -18081.54317403171`. The maximum fold eval RMSE is fold 0's `3.2708042478922636`. The plan's rounded numbers and order are correct.

### F-SCI1 readout configuration — CONTRADICTED

The plan calls this shadowed crossval an RFF run with 256 features and median gamma. The matching start line in `21-recurrence-shadow.log` says instead:

> `cross-validation start: dataset=equities_seq-6.0.0-15505731cba5b86d folds=5 scheme=expanding d=16 theta=None readout=linear`

`24-c-crossval-shadow.txt`'s POST body contains no readout override. Correct captured value: **linear**, not RFF. The fold metrics remain accurately transcribed.

### Target standard deviation — NO ARTIFACT

`24-c-crossval-shadow.txt` contains no target distribution or target standard deviation. Its `eval_std` is the standard deviation of fold metrics, not the target: `rmse: 1.1890319141779127`, `r2: 32762.308611429213`. The cited artifact does not support `target std ≈ 0.017`.

## 3. Scenario A suite registry and process exit

### Registry cell — VERIFIED

For equities cell `c001-0d8782ae`, `scenario-a-suite/registry.jsonl` records:

> `"outcome": "succeeded"`
>
> `"exit_code": 1`
>
> `"metrics": {}`

The cell's manifest and stats record acceptance as:

> `"ok": false`
>
> `"crossval failed: HTTP 422: invalid dataset: NPZ artifact is missing required key 'X_full'"`

### Suite exit and printed disposition — VERIFIED

`11-scenario-a-suite.exit` is exactly `0`. `11-scenario-a-suite.txt` prints:

> `[suite] c001-0d8782ae: succeeded`

## 4. Manifests and stats schema

### Train metric nesting — VERIFIED

The equities stats file nests the exact train result at `recurrence.final_metrics.r2`:

> `"r2": 0.11632826498677562`

The rounded plan value `0.116` and W0.4's `0.1163` are supported.

### Crossval aggregate nesting — NO ARTIFACT

Both archived stats files contain `"crossval": null`; neither demonstrates a populated `recurrence.crossval.eval_aggregate.r2`. That proposed path may be intended, but these artifacts do not establish it.

### Crossval failure, acceptance, and completion reason — VERIFIED

Both manifests have `crossval: null`, `acceptance.ok: false`, and the full detail:

> `crossval failed: HTTP 422: invalid dataset: NPZ artifact is missing required key 'X_full'`

Both have:

> `"completion_reason": null`

### HTTP-detail truncation — NO ARTIFACT

The captured detail is shorter than the claimed 500-character bound and appears complete. No archived case exceeds the bound, so these artifacts cannot demonstrate truncation at 500 characters.

## 5. Train responses

### AAPL train — VERIFIED

`22-a-train-aapl.txt` records status 200, `r2: 0.128816878514036`, `TIME_TOTAL=3.255929`, and `n_windows: 1346`.

### Five-symbol canopy seed — VERIFIED

`23-b-train-canopy-seed.txt` records status 200 and:

> `"r2":0.008372555513041502`
>
> `"n_windows":15592`
>
> `TIME_TOTAL=46.503125`

The plan's 0.008, 46.5 seconds, and 15,592 windows are correct.

### Out-of-sample metric — VERIFIED absence

Both train responses contain only `final_metrics` for the requested `split: train`; neither labels or reports a validation/test/OOS metric.

## 6. Predict response

### Metrics in predict — VERIFIED absence

`25-d-predict.txt` returns only `predictions` and `shape: [176,1]`, with status 200. No metrics field appears.

## 7. Flat equities refusal

### First attempt (`26-e-flat-equities.txt`) — CONTRADICTED

The plan cites this file for the 422 sequence-rank refusal, but it actually records:

> `{"detail":"a training run is already in progress"}`
>
> `HTTP_STATUS=409`

### Retry (`28-e-flat-equities-retry.txt`) — VERIFIED

The retry records status 422 and the exact detail:

> `invalid dataset: X_train must be 3-D (W, L, F) for a sequence artifact; got 2-D`

Thus the substantive control is reproduced, but the F-S4 evidence citation to file 26 is wrong unless file 28 is included.

## 8. Bare-default NaN refusal

### Exact detail — VERIFIED

`27-f-default-nan.txt` records status 422 and:

> `invalid dataset: X_train has non-finite values (NaN/Inf)`

## 9. CLI parameter support

### `--params` and exit code — VERIFIED

Both `32-g-cli-params-no-out.txt` and `33-g-cli-params-with-out.txt` say:

> `juniper-recurrence: error: unrecognized arguments: --params ...`

Both corresponding `.exit` files contain `2`. `34-g-cli-help.txt` lists `--generator` and `--out` but no `--params` or `--params-file`.

## 10. NPZ inventory

### Keys, shapes, dtypes, finiteness, and absences — VERIFIED

`42-npz-inventory.json` records, per sequence split: `X` float32 `(W,64,15)`; `y` float32 `(W,2)`; `y_reg` float32 `(W,1)`; `date` int32 `(W,64)`; `dt` float32 `(W,64)`; `target_dt` float32 `(W,)`; `window_end_date` int32 `(W,)`; `ticker_code` int32 `(W,)`; `observed_mask` uint8 `(W,64)`; and `ticker_vocab` `<U4` `(1,)`. Every numeric key has `finite_fraction: 1.0`.

The complete key list contains no `seq_lengths_*`, `t_*`, `padding_mask_*`, or `*_full`. Flat equities has `X_train (15912,15)`, `X_val (1989,15)`, and `X_test (1987,15)`, all float32, plus `y`, `y_reg`, ticker/date provenance keys, and `<U5` ticker vocabulary.

### `observed_mask` is all ones — NO ARTIFACT

The inventory establishes uint8 shape and 100% finiteness, not values. It cannot distinguish all ones from all zeros or another finite mask.

## 11. Package test counts

### Counts — VERIFIED

The ten logs report exactly:

- app shadowed `234 passed`; env `1 failed, 233 passed`, failing `test_docs_require_auth_when_enabled` because `assert 200 == 401`;
- model shadowed/env `141 passed` each;
- client shadowed/env `75 passed` each;
- bench shadowed `37 passed`; env `14 failed, 23 passed`;
- root shadowed/env `57 passed, 7 subtests passed` each.

These artifacts do not cover the plan's additional canopy, juniper-data, or 524/1/4 juniper-ml counts; those are outside the named `tests-*-{env,shadowed}.log` set.

## 12. Service logs

### Log-content claims — VERIFIED

`21-recurrence-shadow.log` contains the observed 409:

> `POST /v1/train rejected: a training run is already in progress`
>
> `"POST /v1/train HTTP/1.1" 409 Conflict`

Neither `21-recurrence-shadow.log` nor `30-recurrence-plain.log` contains `RequestId`, `request_id`, or `X-Request-ID`. Neither contains an ERROR-level record or traceback. Neither logs generator parameter bodies or an artifact key/shape/dtype inventory. Start lines do show unresolved theta, for example:

> `training start: dataset=equities_seq-6.0.0-15505731cba5b86d split=train windows=1346 d=16 theta=None readout=linear`

## 13. Served generator metadata

### Versions and task types — VERIFIED

`40-seq-meta-http.txt` records `generator_version: "6.0.0"`, `task_type: "regression"`, `n_classes: null`, status 200. `41-flat-meta-http.txt` records `generator_version: "5.0.0"`, `task_type: "classification"`, `n_classes: 2`, status 200.

## 14. Final listeners

### Audit ports down — VERIFIED

`99-final-listeners.txt` contains only the socket header and `--- experiment ranges ---`; no listener row follows. The artifact supports that nothing was listening in the checked experiment ranges at capture time.

## Material items in the evidence the plan omits

1. `00-baseline.txt` is internally inconsistent about plain `juniper-service-core`: `pip check` says 0.5.0 while the explicit import/version probe says 0.4.0. The plan presents 0.5.0 as settled.
2. The supposedly flat-equities 422 capture first hit a real concurrency race: `26-e-flat-equities.txt` is a 409. Only retry file 28 proves the 422. This is material evidence for the plan's lock/concurrency discussion.
3. Both suite cells, not only equities, are registered `outcome: succeeded` with `exit_code: 1`, `metrics: {}`, and failed acceptance. The defect is therefore not equities-specific in this suite run.
4. Both scenario manifests record package versions substantially older than several current repository versions (`juniper-data 0.14.0`, `juniper-ml 0.6.0`, `juniper-canopy 0.5.0`). That provenance should accompany any generalisation from the scenario.
5. The F-SCI1 configuration mismatch is easy to miss because the response contains metrics but no echoed hyperparameters; only the matching service log exposes `readout=linear`.

## Final tally

| Verdict | Count |
| --- | ---: |
| VERIFIED | 19 |
| CONTRADICTED | 3 |
| NO ARTIFACT | 5 |
| **Total** | **27** |

The artifact archive strongly supports the central observed failures, suite truthfulness defect, response metrics, test counts, inventory shapes, and metadata. It does not support five specifically attributed details, and it contradicts three: the settled service-core version, the claim that the first flat-equities transcript is the 422 refusal, and F-SCI1's RFF attribution.
The scientific metric values are accurately transcribed, but the cited crossval transcript does not contain the claimed target standard deviation and the service log identifies that manual run as `readout=linear`.
