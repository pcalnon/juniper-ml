# Lane A1 — measurement re-creation from the evidence tree only

- **Reviewer lane**: A1 (procedure `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A)
- **Artifact under review**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.0.0 (sections §0.1, §1.1–§1.4, §2.2–§2.4, §3.4, §4; the §0.2/§2.5 fidelity claim is included because the brief names it)
- **Entry point**: `reports/2026-10-04_recurrence-equities-cv-matrix/` only. No source code opened; no instrument re-run; nothing edited outside this file.
- **Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/misty-kindling-pascal` at `a0a120d5`
- **Date**: 2026-10-05
- **Method**: every number in the listed sections was parsed from the note at its printed precision and compared with the JSON/CSV/JSONL value (tolerance = half a unit of the note's last printed digit; round numbers such as `28,000` / `137,000` / `2,540` judged at their evident significant figures). Derived quantities (means, stds, ratios, sorted lists, decade gaps, pair diffs) were recomputed with `json` / `csv` / `numpy`. Script: scratchpad `verify.py` + `check2.py` (not part of the tree; not needed to reproduce — every key path is named below).

## 0. Evidence tree inventory (all 12 files the brief names are present)

| file | bytes | md5 |
| --- | --- | --- |
| `00-dataset-create.json` | 1,629 | `c5b38672157af67f0f0e2b9a06e05a66` |
| `01-recurrence-health.json` | 55 | `27f03596950b564581a4ea29cf247ea4` |
| `10-crossval-eh-rff.json` | 3,747 | `906816e2374689a2c7a12e21499b6a69` |
| `10-crossval-service-defaults.json` | 3,573 | `c3d502cd8f91f81ee1d3e9f4602091f2` |
| `20-matrix-datasets.json` | 8,037 | `f05cebd8741b918396f0b9da9381ffb6` |
| `21-matrix-cells.json` | 284,296 | `bf9268051425545f35a8669f675f03da` |
| `22-matrix-table.md` | 6,442 | `241cdbb98784e5c95abf69896685aaca` |
| `23-linear-conditioning.json` | 8,401 | `7b10e2c3f25604c55d42f2e72863ad86` |
| `scenario-a-rerun/REPORT.md` | 1,484 | `f6f56c0ec9e579c3895d8f34ed87f361` |
| `scenario-a-rerun/aggregate.csv` | 575 | `1defd4e39825b0097ec45387910db27a` |
| `scenario-a-rerun/c001-manifest.json` | 9,393 | `b809a915f7cfd3a2d5c5cfbf14bdb297` |
| `scenario-a-rerun/registry.jsonl` | 1,709 | `e796bab6e76adeffe7c0f470bd0ba4a3` |

Shape: `21-matrix-cells.json` is a list of 24 cell objects (`label, folds[5], eval_aggregate, eval_std, readout, ridge, normalize, theta, dataset_id, wall_seconds`); each fold carries `n_train, n_eval, fit_seconds, theta_resolved, sum_dt_median_train, sum_dt_median_eval, readout_kind, ridge_resolved, gamma_resolved, train_metrics, eval_metrics, memory_z_eval_vs_train, memory_z_train_self, raw_last_step_z_eval_vs_train, pred_train, target_train, pred_eval, target_eval`. `22-matrix-table.md` is a 24-row rendering of 21 (aggregate column agrees with 21 in all 24 rows, 0 mismatches). `01-recurrence-health.json` = `{"status": 200, "body": {"status": "ok"}}`.

Out-of-tree pointers the note relies on: the audit copy `.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/` does **not** exist in this worktree (it exists in the main checkout — existence checked with `ls -d` only, not opened). A sibling `reports/2026-10-03_recurrence-equities-consensus/` exists; it is outside this lane's entry point and was not opened. Grep of the tree for every 2026-10-03 digit the note quotes (`83452`, `18081`, `815`, `6059`, `037baab7`), for the SHAs (`3420a1a5`, `be081fae`, `29be6d35`), the stack run id (`20261004T210331Z-491a`), `PYTHONPATH`, `X_full`, `p4/`, `numpy`, `GCV_GRID`, feature names: **no hits** except two substring false positives inside unrelated floats (`0.32241383452526007`, `0.27018060591618376`).

## 1. Per-section tables

Verdict key: CONFIRMED / REFUTED (artifact's value given) / PARTIAL (what matches, what does not) / NO ARTIFACT. `n` = sample size behind the claim.

### §0.1 Stack as served

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 1 | stack run `20261004T210331Z-491a` | string absent from every file | NO ARTIFACT | grep | — |
| 2 | data `127.0.0.1:8110`, recurrence `127.0.0.1:8260` | `ports.data` 8110, `ports.recurrence` 8260, `service_urls` | CONFIRMED (via the 22:14 suite manifest; the two HTTP replay files carry no URL — same ports ⇒ same stack is an inference) | `scenario-a-rerun/c001-manifest.json` `ports`, `service_urls` | 1 manifest |
| 3 | E-H base YAML staged: `default_d: 16`, `default_theta: null`, `default_ridge: 0.0`, rate limit off | no config in tree | NO ARTIFACT | — | — |
| 4 | juniper-data `JuniperData` env, editable checkout `29be6d35` (`main`) | `packages.juniper-data` = editable_source `/home/pcalnon/Development/python/Juniper/juniper-data`, **version `0.14.0`**; `git` block = `{}` | PARTIAL — editable confirmed; SHA NO ARTIFACT; recorded dist version is `0.14.0` (see §4 item 6) | `c001-manifest.json` `packages.juniper-data`, `git` | 1 |
| 5 | `equities_seq` generator `6.0.0` | `meta.generator_version` "6.0.0" | CONFIRMED | `00-dataset-create.json`; also `20`, `c001-manifest.json` | 3 files |
| 6 | per-run storage, per-run cold equities cache | not recorded | NO ARTIFACT | — | — |
| 7 | `JuniperCascor1` env, Python 3.14.7 | `save_model_rerun.cmd[0]` = `/opt/miniforge3/envs/JuniperCascor1/bin/juniper-recurrence`; `environment.python` "3.14.7" | CONFIRMED | `c001-manifest.json` | 1 |
| 8 | app 0.5.0 editable at `be081fae` | `packages.juniper-recurrence` 0.5.0, editable_source set; SHA absent | PARTIAL — version + editable confirmed; SHA NO ARTIFACT | `c001-manifest.json` | 1 |
| 9 | `juniper-recurrence-model` 0.3.0 editable | 0.3.0, editable_source set | CONFIRMED | `c001-manifest.json` | 1 |
| 10 | `juniper-service-core` dist 0.5.0 / module 0.4.0 | `packages.juniper-service-core` 0.5.0 (no editable_source); module version not recorded | PARTIAL — dist confirmed; module 0.4.0 NO ARTIFACT | `c001-manifest.json` | 1 |
| 11 | `juniper-model-core` 0.2.0 | 0.2.0 | CONFIRMED | `c001-manifest.json` | 1 |
| 12 | `juniper-data-client` 0.5.0 editable | 0.5.0, editable | CONFIRMED | `c001-manifest.json` | 1 |
| 13 | numpy 2.5.3 | not recorded | NO ARTIFACT | — | — |
| 14 | dataset `equities_seq-6.0.0-15505731cba5b86d` | identical string in `00`, both `10-*`, `20`, all 12 raw cells of `21`, `23`, `c001-manifest.json` | CONFIRMED | 7 files | — |
| 15 | AAPL, 2015-01-01 → 2022-01-01, lookback 64, `log_return`, seed 20260807 | `meta.params` | CONFIRMED | `00-dataset-create.json` | 1 |
| 16 | `fundamentals_fill: nan`, `normalize_features: false` | `meta.params` | CONFIRMED | `00-dataset-create.json` | 1 |
| 17 | "all other params at the generator's defaults" | the request in `20` sends 6 params; `meta.params` echoes 19 (13 generator-filled: `purchase_date 2000-01-03`, `basis_price_field close`, `week52_window 252`, `max_symbols 14`, ratios 0.8/0.1/0.1, …) | PARTIAL — values recorded; that they are *defaults* is not | `20-matrix-datasets.json` `normalize=False.params` vs `.meta.params` | 1 |
| 18 | `full` view 1,698 windows (1,346 / 176 / 176) | `n_samples` 1698, `n_train` 1346, `n_val` 176, `n_test` 176 (sum 1698); `20`: `n_windows_full` 1698 and partitions; HTTP `response.dataset.n_windows` 1698, `split` "full" | CONFIRMED | `00`, `20`, both `10-*` | 4 files |
| 19 | 64 × 15 features | `lookback` 64, `n_features` 15 | CONFIRMED | `00`, `20`, `10-*` | — |
| 20 | `sum(dt)` 88–97 calendar days (mean 91.3, std 1.7) | `sum_dt_full` min 88.0, max 97.0, mean 91.3216, std 1.6992; `time_unit` "calendar_days" | CONFIRMED | `20` `sum_dt_full`; `00` `meta.time_unit` | 1,698 windows |
| 21 | target mean 0.00101 / std 0.01835 | 0.0010143 / 0.0183532 | CONFIRMED | `20` `target_full` | 1,698 |
| 22 | folds: `fold_size = 283`; train 281 / 564 / 847 / 1,130 / 1,413; eval 283 each; embargo 2 | `folds[k]`: n_train 281/564/847/1130/1413; n_eval 283 ×5; `eval_first_idx` = 283·(k+1); `train_last_idx` = eval_first − 3 (2-index gap); 1698 % 6 = 0; last eval index 1697 = n−1 | CONFIRMED by construction | `20` `folds` | 5 folds |
| 23 | `walk_forward_folds(1698, n_folds=5, scheme="expanding", embargo=2)` | request carries `n_folds 5, scheme expanding, embargo 2`; the function name is a source claim | PARTIAL — parameters confirmed; function identity NO ARTIFACT | `10-*` `request` | — |

§0.1 tally: CONFIRMED 14 · PARTIAL 5 · NO ARTIFACT 4.

### §0.2 / §2.5 — in-process vs HTTP fidelity ("identical to every printed digit")

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 24 | in-process service-defaults cell reproduces the HTTP control "to every printed digit (aggregate −20,344.64; fold 0 −93,606.23)" | aggregate r²: HTTP −20344.6377, in-process −20344.6354 → both print −20,344.64. Fold 0 r²: HTTP **−93606.2421**, in-process **−93606.2310** → print −93,606.**24** vs −93,606.**23**. Per-fold `mse`, `rmse`, `mae` are **bit-identical in all 5 folds, train and eval**; only `r2` differs (rel ≤ 3.4e-7), and HTTP `r2` == `1 − mse / var(target_eval, ddof=0)` to the last digit — the difference is the r² formula, not the solve | PARTIAL — aggregate yes; fold 0 differs in the second decimal and the note printed the in-process digits for both paths; the solve itself reproduced exactly | `10-crossval-service-defaults.json` `response.folds[*].{train,eval}_metrics` vs `21[0].folds[*]`; `21[0].folds[*].target_eval.std` | 5 folds × 8 metrics |
| 25 | in-process E-H cell reproduces the HTTP replay (−0.115) | −0.11526092 vs −0.11526097 (rel 4.6e-7); `mse/rmse/mae` bit-identical in all folds | CONFIRMED (to 3 dp as printed; to 7 sf) | `10-crossval-eh-rff.json` vs `21[8]` | 5 folds |

Tally: CONFIRMED 1 · PARTIAL 1.

### §1.1 The artifact is the audit's artifact

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 26 | `POST /v1/datasets` resolved to `…15505731cba5b86d` | `dataset_id`, `artifact_url` | CONFIRMED | `00-dataset-create.json` | 1 |
| 27 | "in 2.5 s from a cold per-run cache (one ticker)" | `00` has no timing field; `symbols` ["AAPL"] (one ticker ✓). The manifest's `timings.dataset_create` 2.906 s is the 22:14 suite call, a different request | NO ARTIFACT for 2.5 s | `00`; `c001-manifest.json` `timings` | — |
| 28 | "all 28 keys byte-identical" vs the audit copy | no diff record in the tree; cited audit path absent from this worktree. 9 key families × 3 partitions + `ticker_vocab` = 28 is internally consistent | NO ARTIFACT | — | — |
| 29 | meta `checksum` `c02004e1…` on 2026-10-04 | `c02004e1708e489aea48aa0a985b2eb797ee190d340080ea547dcf363bfed261` | CONFIRMED | `00` `meta.checksum`; same in `20`, `c001-manifest.json` | 3 |
| 30 | meta `checksum` `037baab7…` on 2026-10-03 | not in tree | NO ARTIFACT | — | — |
| 31 | checksum fingerprints the NPZ container (zip write timestamps), not the arrays | mechanism not demonstrable from the tree. What the tree does show: the **same** checksum was returned at `created_at` 21:06:08Z (`00`) and 22:14:49Z (manifest) under the same id, with `tags` added — `created_at`/`tags` vary per request, the checksum did not within this service instance | PARTIAL — consistent with, not evidenced by, the tree | `00` `meta` vs `c001-manifest.json` `dataset.meta` | 2 |

Tally: CONFIRMED 2 · PARTIAL 1 · NO ARTIFACT 3.

### §1.2 The E-H request body and its result

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 32 | request body (9 keys, values as printed) | identical | CONFIRMED | `10-crossval-eh-rff.json` `request` | 1 |
| 33 | `run_experiment.py::_lmu_hyperparams` drops `theta: null` | request has no `theta` key ✓; mechanism is a source claim | PARTIAL | `request` | — |
| 34 | HTTP 200 in 11.2 s | `http_status` 200, `wall_seconds` 11.203 | CONFIRMED | `10-crossval-eh-rff.json` | 1 |
| 35 | per-fold table: n_train, train r², train RMSE, eval r², eval RMSE, eval MAE (5 × 6 = 30 cells + 5 n_train) | all 30 metric cells match at printed precision (e.g. f0 train r² 0.18426 → 0.1843; f4 eval r² −0.25845 → −0.2584; f3 eval RMSE 0.028824 → 0.02882). **`n_train` is not in the HTTP response** (fold keys: `fold, train_metrics, eval_metrics, n_epochs`); the 281…1,413 column comes from `20`/`21` | CONFIRMED (provenance caveat on n_train) | `10-crossval-eh-rff.json` `response.folds[*]`; `20` `folds[*].n_train` | 5 folds |
| 36 | aggregate −0.1153 (std 0.0735), RMSE 0.01857, MAE 0.01337 | −0.11526097, 0.07353723, 0.01857014, 0.01337193. Recomputed: aggregate r² = mean of the 5 fold r² exactly; std is **population (ddof 0)** — ddof 1 would be 0.0822; aggregate RMSE = mean of per-fold RMSE (sqrt of mean mse would be 0.01951) | CONFIRMED (conventions noted) | `response.eval_aggregate`, `eval_std` | 5 folds |
| 37 | per-fold eval RMSE 0.012–0.029 "sits at" target per-fold std 0.011–0.028 | RMSE 0.01177–0.02882; `target_eval.std` 0.0113 / 0.0135 / 0.0196 / 0.0277 / 0.0159 → 0.011–0.028 | CONFIRMED | `10-eh`; `21[8].folds[*].target_eval.std` | 5 |
| 38 | resolved theta 91.0 every fold; gamma 0.0508 / 0.0512 / 0.0499 / 0.0499 / 0.0553; ridge 1.0 | `21[8]`: theta_resolved 91.0 ×5; gamma_resolved 0.05080 / 0.05120 / 0.04990 / 0.04990 / 0.05530; ridge_resolved 1.0 ×5 | CONFIRMED (in-process only; the HTTP response carries none of these, as the note states) | `21[8].folds[*]` | 5 |
| 39 | "does not blow up" / r² ≈ 0 | aggregate −0.115; folds in [−0.258, −0.050] | CONFIRMED | `10-eh` | 5 |

Tally: CONFIRMED 7 · PARTIAL 1.

### §1.3 The control — service defaults, same artifact, same day

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 40 | same body with no model parameters | `request` = `{dataset, n_folds 5, scheme expanding, embargo 2}` | CONFIRMED | `10-crossval-service-defaults.json` | 1 |
| 41 | defaults = `readout=linear`, `ridge=0.0`, d 16, data-driven theta | request carries none of these. In-process twin `21[0]` (readout_kind `linear`, ridge_resolved 0.0, theta_resolved 91.0, gamma null) reproduces the HTTP `mse` bit-for-bit in every fold | CONFIRMED by replication for readout / ridge / theta; **d: NO ARTIFACT** (no `d` key in `21` or in the HTTP request) | `21[0].folds[*]`; item 24 | 5 folds |
| 42 | HTTP 200 in 10.9 s | 200, `wall_seconds` 10.906 | CONFIRMED | `10-sd` | 1 |
| 43 | 2026-10-04 column: train r² +0.4532 / +0.3224 / +0.2487 / +0.1836 / +0.1353; eval r² −93,606 / −798.5 / −3.70 / −75.6 / −7,239; eval RMSE 3.464 / 0.381 / 0.043 / 0.242 / 1.353; aggregate −20,345 (std 36,731), RMSE 1.097 | all 17 cells match at printed precision (e.g. −93606.242, −798.467, −3.6963, −75.618, −7239.17; −20344.638, 36730.52, 1.0965). Aggregate = mean of folds; std ddof 0 (ddof 1 = 41,066) | CONFIRMED | `10-sd` `response` | 5 folds |
| 44 | "audit, 2026-10-03" column: −83,452 / −815 / −3.7 / −78 / −6,059; aggregate −18,081 | not in tree (grep hits are substrings of `0.32241383452526007` and `0.27018060591618376`) | NO ARTIFACT | — | — |
| 45 | "fold-0 moved by 12 % and fold 4 by 19 %" | with the audit value as denominator: (93,606.24 − 83,452)/83,452 = 12.17 %; (7,239.17 − 6,059)/6,059 = 19.48 %; (20,344.64 − 18,081)/18,081 = 12.5 %. With the 2026-10-04 value as denominator: 10.8 % / 16.3 % | PARTIAL — arithmetic correct; one operand of each pair is NO ARTIFACT in this tree | `10-sd` + quoted digits | 2 folds |
| 46 | "same model code (`be081fae` both days — the audit shadowed the checkout), same machine" | `git` = `{}`; platform recorded only for 2026-10-04 (`Linux-7.0.0-31-generic-x86_64-with-glibc2.43`, nproc 16) | NO ARTIFACT | `c001-manifest.json` | — |
| 47 | "a solve whose out-of-sample answer changes while nothing it reads has changed is being decided by rounding" | the tree's only cross-process replicate of this configuration (HTTP service process vs in-process script, same day) is **bit-identical in `mse`/`rmse`/`mae` for all 5 folds**; the r² delta (≤ 1.2e-7) is the scoring formula (item 24) | PARTIAL — the 12 % movement is between an in-tree and an out-of-tree number; nothing in the tree exhibits solve-level non-reproducibility | `10-sd` vs `21[0]` | 5 folds, 1 replicate pair |
| 48 | both requests returned 200 with no `PYTHONPATH` on a decision-11 artifact | both `http_status` 200 ✓; `PYTHONPATH` not recorded anywhere; the artifact's key list (absence of `X_full`) is not in the tree | PARTIAL — 200 ✓; env and key list NO ARTIFACT | both `10-*` | 2 |
| 49 | "the request that returned 422 `missing required key 'X_full'` in the audit" | not in tree | NO ARTIFACT | — | — |

Tally: CONFIRMED 3 · PARTIAL 4 · NO ARTIFACT 3.

### §1.4 Scenario A re-run

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 50 | re-run on 2026-10-04 through the launcher, suite `e-h-recurrence-real-data` | `run_id` 20261004T221425Z-ad56 (c000) and 20261004T221441Z-3835 (c001); `suite_id` `e-h-recurrence-real-data-20261004T221425Z` | CONFIRMED (the `p4/…yaml` path is not recorded) | `registry.jsonl` | 2 cells |
| 51 | from juniper-ml `main` at `3420a1a5` (W0.3/W0.4 merged in #2145) | manifest `git` = `{}`; `packages.juniper-ml` = `0.6.0` non-editable dist | NO ARTIFACT for the SHA | `c001-manifest.json` | — |
| 52 | against the model-repaired env | `juniper-recurrence-model` 0.3.0 editable | CONFIRMED | `c001-manifest.json` `packages` | 1 |
| 53 | audit's cell state: `succeeded` with `exit_code: 1`, `acceptance.ok: false`, `metrics: {}`, 422'd crossval | not in tree | NO ARTIFACT | — | — |
| 54 | registry now: `outcome: succeeded`, `exit_code: 0`, phases train/predict/crossval/save_model all `ok`, metrics `train_r2 0.1163, cv_r2 −0.1153, cv_r2_std 0.0735, n_windows 1346` | exactly: 0.11632826, −0.11526097, 0.07353723, 1346; `teardown_ok` true; `error` null | CONFIRMED | `registry.jsonl` line 2 | 1 cell |
| 55 | `REPORT.md` says "Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run." and carries the four columns | verbatim; columns `cv_r2, cv_r2_std, n_windows, train_r2` present | CONFIRMED | `REPORT.md` | 1 |
| 56 | control cell (irregular sine) `cv_r2 0.975` | 0.9749240 (n_windows 3149, train_r2 0.9795) | CONFIRMED | `registry.jsonl` line 1 | 1 |
| 57 | "`cv_r2` is the §1.2 aggregate to four decimals" | `cv_r2` == HTTP `eval_aggregate.r2` to **all 17 digits** (−0.11526096841533144); `cv_r2_std` likewise; the manifest's whole `crossval.eval_aggregate` block equals the HTTP block exactly | CONFIRMED (understated) | `registry.jsonl`, `c001-manifest.json` `crossval`, `10-eh` | 1 |
| 58 | "the four F-D1 / F-D2 symptoms are gone" | `exit_code` 0; `acceptance` `{ok: true, reasons: []}`; metrics populated; `phases.crossval.status` ok | CONFIRMED for the 2026-10-04 side (2026-10-03 side NO ARTIFACT) | `c001-manifest.json` | 1 |
| 59 | from a `.claude/worktrees/` checkout the suite needs `JUNIPER_EXP_PROJECT_DIR=…` | not recorded (`runtime_env` null) | NO ARTIFACT | — | — |
| 60 | `n_windows 1346` | recorded as 1346 — but this is the **train-split** count (`train.dataset.split` "train", `n_windows` 1346); the crossval ran on `split: full`, 1,698 windows (HTTP `response.dataset`), and the manifest's `crossval` block records no split or window count | CONFIRMED as recorded; provenance caveat | `c001-manifest.json` `train.dataset`, `crossval`; `10-eh` `response.dataset` | 1 |

Tally: CONFIRMED 8 · NO ARTIFACT 3.

### §2.2 Matrix results

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 61 | 24 cells = {linear, rff} × {0.0, 1.0, gcv} × {off, on} × {fold-resolved, configured}, 5 folds each | 24 cells, 5 folds each; labels enumerate exactly that product; `dataset_id` ∈ {…15505731cba5b86d (12 cells), …fa3aae11ac374c94 (12)} | CONFIRMED | `21` | 24 × 5 |
| 62 | normalised artifact `equities_seq-6.0.0-fa3aae11ac374c94`, "same rows" | id ✓; its `target_full`, `sum_dt_full` and `folds` dicts are bit-equal to the raw artifact's | CONFIRMED | `20` `normalize=True` | 1 |
| 63 | z-scored by the producer on the pooled `train` partition | not recorded (last-step means ≈ 0.44, stds ≈ 0.45 on the full view; one column std exactly 0.0) | NO ARTIFACT for the mechanism | `20` `normalize=True.X_last_step_*` | — |
| 64 | `d = 16`, RFF 256 features, median gamma, `default_ridge = 0.0` "as the service" (matrix) | `21` has no `d`, `rff_features` or gamma-mode field; only `gamma_resolved` ≈ 0.05 | NO ARTIFACT in `21` (d = 16 is confirmed for `23` by 242 = 15·16 + 2, and for the HTTP E-H request and the CLI `save_model_rerun` command `--d 16 --rff-features 256 --rff-gamma median`) | `21`; `23` `design_cols`; `c001-manifest.json` `save_model_rerun.cmd` | — |
| 65 | "Fit time ≈ 30 s per cell; total ≈ 13 min" | `wall_seconds` 29.04–37.6 (mean 32.1), Σ 770 s = 12.8 min ✓; Σ `fit_seconds` per cell 8.7–14.3 s (mean 10.3 s) | PARTIAL — total ✓; the 30 s is wall time, fits are ≈ 10 s/cell | `21[*].wall_seconds`, `folds[*].fit_seconds` | 24 cells |
| 66 | theta resolved to 91.0 in every fold of every cell | `theta_resolved` set = {91.0} over 120 cell-folds; `sum_dt_median_train` and `_eval` both {91.0} | CONFIRMED | `21[*].folds[*]` | 120 |
| 67 | each configured row equals its fold-resolved twin "to every printed digit" | **bit-identical** in all 249 non-timing leaves of each of the 12 pairs; only the 5 `fit_seconds` differ | CONFIRMED (stronger than claimed) | `21` pairs (0,1)…(22,23) | 12 pairs |
| 68 | `22-matrix-table.md` has all 24 | 24 rows; aggregate column agrees with `21` (0 mismatches) | CONFIRMED | `22` vs `21` | 24 |
| 69 | §2.2 table: 12 rows × (5 fold r² + agg + eval RMSE + train r² f0, f4 + 5 ridge) + 10 z cells = 166 numbers | 165 match at printed precision. One last-digit miss: **rff/gcv/off aggregate printed −0.014, artifact −0.014544 (rounds to −0.015)** | CONFIRMED 165 / PARTIAL 1 | `21[0,2,4,…,22]` | 12 cells × 5 folds |
| 70 | "same" z column (rows 2–6 = row 1; rows 8–12 = row 7) | `memory_z_eval_vs_train.max_abs_z` tuple identical across the 12 cells of each artifact (1 distinct tuple each): 24.34 / 23.11 / 7.53 / 198.63 / 43.83 and 24.34 / 23.11 / 11.20 / 336.51 / 49.63 | CONFIRMED | `21` | 12 + 12 cells |
| 71 | gamma "0.050–0.055" (off), "0.048–0.061" (on) | 0.0499–0.0553; 0.0484–0.0607; identical across the 6 rff cells of each artifact | CONFIRMED | `21[*].folds[*].gamma_resolved` | 6 + 6 |
| 72 | prediction-scale table: 6 cells × 5 pred std + 6 max |pred| | all match (linear/0.0/off 3.458 / 0.213 / 0.0300 / 0.237 / 0.433, max 9.8098; linear/0.0/on 28,031.6 ↔ "28,000", max 136,545.8 ↔ "137,000"; rff/1.0/off 0.00428 / 0.00399 / 0.00433 / 0.00625 / 0.00762, max 0.0213; …) | CONFIRMED (2–3 sf on the two round numbers) | `21[*].folds[*].pred_eval` | 6 cells × 5 |
| 73 | "target std 0.011 / 0.014 / 0.020 / 0.028 / 0.016" | `target_eval.std` 0.01132 / **0.01347** / 0.01962 / 0.02766 / 0.01590 — fold 1 prints 0.013, not 0.014; identical across all 24 cells | PARTIAL — 4 of 5; one last-digit miss | `21[*].folds[*].target_eval.std` | 5 |
| 74 | "a daily log return has a standard deviation of about 0.018" | 0.01835 | CONFIRMED | `20` `target_full.std` | 1,698 |
| 75 | "predicts values up to 9.8 (a 980 % one-day move)" | `pred_eval.max` 9.8098 (fold 0) ✓. The target is `log_return`; a log return of 9.81 is e^9.81 − 1 ≈ 18,200 (≈ 1.8 million %). "980 %" is 9.81 read as a simple return | REFUTED (unit conversion; the 9.81 itself is confirmed; the sentence's point — absurd scale — survives) | `21[0].folds[0].pred_eval.max`; `00` `params.regression_target` | 1 |
| 76 | normalised ridge-0 fit predicts "up to 137,000" | |`pred_eval.min`| 136,545.8 (fold 0) | CONFIRMED (3 sf) | `21[12].folds[0].pred_eval` | 1 |

Tally: CONFIRMED 10 · PARTIAL 3 · REFUTED 1 · NO ARTIFACT 2.

### §2.3 Per-candidate verdicts

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 77 | (c) `sum(dt)` 88–97 (std 1.7), median 91.0 in every expanding train fold | ✓ (items 20, 66) | CONFIRMED | `20`, `21` | 120 |
| 78 | (c) 12 configured cells identical to twins | bit-identical (item 67) | CONFIRMED | `21` | 12 |
| 79 | (b) producer normalisation makes the unregularised solve "four hundred million times worse (−20,345 → −4.3e12)" | 4.2894e12 / 20,344.6 = **2.11e8** (fold-0 ratio 2.29e8; RMSE ratio 9,571) | REFUTED — two hundred million, off by 2× | `21[12].eval_aggregate.r2` / `21[0].eval_aggregate.r2` | 2 cells |
| 80 | (b) linear ridge 1.0 normalised not sane: fold 4 −22 | −22.015 | CONFIRMED | `21[14].folds[4]` | 1 |
| 81 | (b) RFF ridge 1.0: −0.115 raw vs −0.142 normalised | −0.11526 / −0.14237 | CONFIRMED | `21[8]`, `21[20]` | 2 |
| 82 | (b) normalising raises numerical rank from 113–161 to 210–226 | raw 113 / 149 / 159 / 160 / 161; normalised 210 / 210 / 210 / 210 / 226 | CONFIRMED | `23` `numerical_rank_eps` | 5 + 5 |
| 83 | (a) every `ridge = 0.0` cell catastrophic: −20,345 / −1,986 / −4.3e12 / −3,197 | 8 cells (4 configs × 2 theta): −20,344.6 / −1,986.3 / −4.289e12 / −3,196.6; smallest magnitude 1,986 | CONFIRMED | `21[0,1,6,7,12,13,18,19]` | 8 |
| 84 | (a) linear ridge 1.0 on the raw block still catastrophic (−2,064) | −2,063.68 | CONFIRMED | `21[2]` | 1 |
| 85 | (a) last-step feature std from 3.8e-4 to 7.9e11 — `market_cap`, `total_shares`, `volume` | 3.815e-4 (index 9) to 7.936e11 (index 8); the three columns > 1e6 are indices 4 (6.7e7), 7 (4.4e9), 8 (7.9e11) | PARTIAL — range confirmed; feature **names** NO ARTIFACT (no name list anywhere in the tree) | `20` `X_last_step_full_per_feature_std` | 15 features |
| 86 | (a) the RFF rung standardises per fold, train-only (`readouts.py::_standardize_fit`) | source claim | NO ARTIFACT | — | — |
| 87 | (d) eval memory max |z| 8–199 raw, 11–337 normalised | 7.53–198.63; 11.20–336.51 | CONFIRMED | `21` `memory_z_eval_vs_train.max_abs_z` | 5 × 2 |
| 88 | (d) 28–100 % of eval rows have a column beyond 5σ | `frac_rows_any_gt5` min 0.2756 (raw fold 2), max 1.000 (fold 4, both artifacts); per fold raw 0.696 / 0.689 / 0.276 / 0.823 / 1.000, normalised 0.795 / 0.693 / 0.329 / 0.929 / 1.000 | CONFIRMED | `21` | 10 fold×artifact |
| 89 | (d) raw last-step feature max |z| 10–58 | 9.94–57.72 (identical for both artifacts — z-scores are affine-invariant, so this is one measurement) | CONFIRMED | `21` `raw_last_step_z_eval_vs_train.max_abs_z` | 5 |
| 90 | (d) RFF ridge ≥ 1 prediction std 0.004–0.008 vs target 0.011–0.028 | rff/1.0/off 0.00399–0.00762; rff/1.0/on 0.00388–0.00815; target 0.0113–0.0277 | CONFIRMED | `21[8]`, `21[20]` | 2 × 5 |
| 91 | GCV: "on both rungs GCV picks a very large penalty and the fit collapses to the fold mean (train r² ≈ 0.002, eval r² −0.01)" | true for rff/gcv/off, linear/gcv/on, rff/gcv/on (train r² 0.0008–0.0145; eval −0.051 … +0.0003). **False for linear/gcv/off**: train r² 0.088–0.317, eval r² −217.6 / −2.66 / −2.04 / −36.6 / −975.5, aggregate −246.9, despite λ = 1000 in 3 of its 5 folds | PARTIAL — 3 of 4 GCV configurations | `21[4]` | 4 configs × 5 |
| 92 | "in 15 of 20 GCV folds the selected λ is 1000.0" | 15 of 20 fold-resolved GCV folds (30 of 40 with twins); distinct selected values {60.209, 85.547, 495.354, 1000.0} | CONFIRMED | `21[4,10,16,22].folds[*].ridge_resolved` | 20 |
| 93 | 1000 is "the last point of the grid (`_GCV_GRID`)" | source claim; the tree shows only the four selected values | NO ARTIFACT | — | — |
| 94 | GCV is "the one configuration whose eval r² is nearest zero" | rff/gcv/on −0.01342, rff/gcv/off −0.01454, linear/gcv/on −0.01474 are the three nearest-zero aggregates | CONFIRMED (for the three collapsed GCV cells) | `21` | 24 |

Tally: CONFIRMED 13 · PARTIAL 2 · REFUTED 1 · NO ARTIFACT 2.

### §2.4 Conditioning of the linear design

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 95 | design = memory block (15 × 16 = 240) + `target_dt` + 1 = 242 columns | `design_cols` 242 in all 10 folds | CONFIRMED (d = 16 implied) | `23` | 10 |
| 96 | table: 8 rows × (n_train, rank, cond, ‖coef‖, amp p99 train → eval) = 48 numbers | 47 match (raw f0 113 / 8.620e32 / 0.1603 / 0.331 → 26,500; raw f1 2,537.7 ↔ "2,540"; raw f3 6.42e-14 → 454.3; raw f4 1.544e22 / 0.02626 / 2.14e-5 → 0.00279; norm f0 210 / 6.556e6 / 5.6e-7 → 0.0989; norm f3 4.527e13; norm f4 226 / 1.107e20 / 20.58 / 7.2e-4 → 0.109). One last-digit miss: **normalised f0 cond printed 1.7e24, artifact 1.755e24 (rounds to 1.8e24)** | CONFIRMED 47 / PARTIAL 1 | `23` `normalize=False.folds[*]`, `normalize=True.folds[0,3,4]` | 8 folds |
| — | (not a claim) normalised folds 1 and 2 are omitted from the note's table | present: f1 rank 210, cond 3.37e22, ‖coef‖ 5,896, amp 3.9e-5 → 0.0218; f2 rank 210, cond 2.15e21, ‖coef‖ 55.5, amp 1.4e-4 → 8.0e-4 | — | `23` `normalize=True.folds[1,2]` | 2 |
| 98 | amplification taken "over the ten smallest singular directions" | the JSON records no such parameter (keys: `weak_dir_amp_train_p99`, `weak_dir_amp_eval_p99`, `weak_dir_amp_eval_max`, `singular_values_log10_deciles`) | NO ARTIFACT for "ten" | `23` | — |
| 99 | "fold 4 raw blows up along directions outside the last ten" | raw f4: amp eval p99 0.00279, max 0.00962, vs its eval r² −7,239 — the metric does not track fold 4; "outside the last ten" is an inference | PARTIAL — the mismatch is in the artifact; the explanation is not | `23`, `21[0].folds[4]` | 1 |
| 100 | "rank-deficient by a third to a half" (raw) | deficiency 53.3 / 38.4 / 34.3 / 33.9 / 33.5 % | CONFIRMED | `23` | 5 |
| 101 | 2-norm condition number 1e22–1e32 | 1.54e22 – 8.62e32 | CONFIRMED (upper end is 8.6e32) | `23` `cond_2norm` | 5 |
| 102 | min-norm solution well behaved in-sample: small ‖coef‖, train r² 0.14–0.45 | ‖coef‖ 0.026–0.160; linear/0.0/off train r² 0.135–0.453 | CONFIRMED | `23`; `21[0]` | 5 |
| 103 | "That is the −93,606" | fold 0 eval r² −93,606.23 (in-process) / −93,606.24 (HTTP) | CONFIRMED | `21[0].folds[0]`, `10-sd` | 1 |
| 104 | digits moved 2026-10-03 → 2026-10-04 on identical inputs; "at cond 1e32 … reproducible only to its order of magnitude" | the tree's one cross-process replicate agrees **bit-for-bit on `mse` in every fold** (item 24); no in-tree pair differs beyond 1.2e-7, and that residue is the r² formula | PARTIAL — the 2026-10-03 operand is NO ARTIFACT; the in-tree replicate does not exhibit the claimed order-of-magnitude-only reproducibility (same machine/day; thread settings unrecorded, so the BLAS/thread mechanism is untested either way) | `10-sd` vs `21[0]`; `c001-manifest.json` `environment.thread_env` (all null) | 1 pair |
| 105 | "the audited −18,081 and today's −20,345 are the same measurement" | −20,344.64 ✓; −18,081 NO ARTIFACT | PARTIAL | `10-sd` | — |

Tally: CONFIRMED 5 · PARTIAL 4 · NO ARTIFACT 1.

### §3.4 R5 recommendation — acceptance band

All 24 aggregate eval r² from `21-matrix-cells.json`, sorted (configured twins are exact duplicates):

| aggregate eval r² | decades below −1 | cell |
| --- | --- | --- |
| −4.289e12 | 12.63 | linear / 0.0 / on (×2) |
| −20,344.64 | 4.31 | linear / 0.0 / off (×2) |
| −3,196.64 | 3.50 | rff / 0.0 / on (×2) |
| −2,063.68 | 3.31 | linear / 1.0 / off (×2) |
| −1,986.28 | 3.30 | rff / 0.0 / off (×2) |
| **−246.89** | **2.39** | linear / gcv / off (×2) |
| **−4.523** | **0.66** | linear / 1.0 / on (×2) |
| −0.14237 | — | rff / 1.0 / on (×2) |
| −0.11526 | — | rff / 1.0 / off (×2) — the E-H configuration |
| −0.01474 | — | linear / gcv / on (×2) |
| −0.01454 | — | rff / gcv / off (×2) |
| −0.01342 | — | rff / gcv / on (×2) |

Sane class (aggregate > −1): **5 configurations** (10 cells). Non-sane: 7 configurations (14 cells). Lowest sane aggregate −0.142; nearest non-sane aggregate −4.52; gap 31.8× = 1.50 decades. No cell has an aggregate in (−1, −0.142). No cell has an aggregate above +0.5 (maximum is −0.0134).

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 106 | "the sane class sits in [−0.26, +0.00] per fold" | per-fold range over the 5 sane configurations is **[−0.2765, +0.00034]**; the minimum is rff/1.0/on fold 4 (−0.2765). Excluding rff/1.0/on the minimum is −0.2584 (the E-H cell's fold 4, which prints −0.26). Maximum +0.00034 (rff/gcv fold 4) prints +0.00 ✓ | PARTIAL — −0.26 is the E-H cell's own floor; the sane class as the note itself counts it (§2.3(b), §3.1 treat rff/1.0/on as sane) reaches −0.28 | `21[8,10,16,20,22].folds[*].eval_metrics.r2` | 5 configs × 5 folds |
| 107 | "−0.115 aggregate across the four sane cells" | there are five sane configurations, not four; −0.115 is the single E-H cell's aggregate; the mean of the five sane fold-resolved aggregates is −0.060 | PARTIAL — count and referent do not match the artifact | `21` | 5 |
| 108 | "the defect class is below −1 by three or more orders of magnitude, so the lower bound separates them with no tuning" | ≥ 3 decades: linear/0.0/on (12.6), linear/0.0/off (4.3), rff/0.0/on (3.5), linear/1.0/off (3.3), rff/0.0/off (3.3). **< 3 decades: linear/gcv/off (2.39), linear/1.0/on (0.66)**. The −1 cut still separates all 24 cells (nearest non-sane −4.52, 1.5 decades from the lowest sane) | PARTIAL — true for the four `ridge = 0` configurations (the audited class) and linear/1.0/off; false for 2 of the 7 non-sane configurations; the *separation* claim holds, the *margin* claim does not | `21` | 24 cells |
| 109 | "an aggregate above +0.5 on next-day log returns would indicate leakage or a scoring error" | no matrix cell above +0.5 (max −0.0134); the irregular-sine control's 0.975 is a different dataset | NO ARTIFACT either way (analysis claim with no in-tree test) | `21`, `registry.jsonl` | 24 |
| 110 | "Train r² ≥ 0.9 marked every interpolating fold-0 fit (ridge 0, RFF: 0.959; linear normalised: 0.907)" | fold-0 train r²: rff/0.0/off **0.9586** ✓, linear/0.0/on **0.9073** ✓, rff/0.0/on **0.9557** ✓, **linear/0.0/off 0.4532** — the service-default (audited) configuration does not reach 0.9 in any fold. Conversely no non-`ridge 0` cell reaches 0.9 in any fold (max 0.4253) | PARTIAL — 3 of 4 `ridge 0` fold-0 fits; a `train_r2 ≤ 0.9` report band would not flag the configuration that produced the audited number (unless "interpolating" is read to exclude a rank-113 design on 281 rows, in which case the parenthetical "ridge 0" over-generalises) | `21[0,6,12,18].folds[0].train_metrics.r2` | 12 configs |
| 111 | "measured on one ticker and one window" | `symbols` ["AAPL"], 2015-01-01 → 2022-01-01, one seed | CONFIRMED | `00` | 1 |

Tally: CONFIRMED 1 · PARTIAL 4 · NO ARTIFACT 1.

### §4 What the evidence cannot support

| # | claim | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 112 | "15 of 20 selections sit at the grid ceiling" | 15 of 20 (item 92); "ceiling" is NO ARTIFACT (item 93) | CONFIRMED (count) | `21` | 20 |
| 113 | "the exact audited digits (−18,081, −83,452) … at condition number 1e32" | digits NO ARTIFACT; fold-0 cond 8.62e32 ✓ | PARTIAL | `23` | 1 |
| 114 | "r² ≈ −0.1 is no worse than the mean by much" | −0.115 | CONFIRMED | `10-eh` | 5 |
| 115 | nothing on multi-ticker, `test` partition, other `d`, MLP, other tickers/dates/seeds | tree holds one ticker, one window, one seed, split "full" (CV) / "train" (train phase) / predict shape [176, 1]; no MLP cells; no `d` field | CONFIRMED (absence) | `00`, `10-*`, `21`, `c001-manifest.json` | — |

Tally: CONFIRMED 3 · PARTIAL 1.

## 2. Tallies

| verdict | count |
| --- | --- |
| CONFIRMED | 67 |
| PARTIAL | 26 |
| REFUTED | 2 (item 79 "four hundred million times" → 2.1e8; item 75 "980 %" → log-return unit error) |
| NO ARTIFACT | 19 |
| **total claims scored** | **114** |

Of the 26 PARTIAL rows, 4 are last-digit rounding (items 69, 73, 96 and the 0.013-vs-0.014 target std), 9 are "value confirmed, mechanism/identity not in tree" (17, 23, 31, 33, 41, 48, 85, 99, 105), 3 concern the 2026-10-03 operands (45, 47, 104), and the remaining 10 are substantive: 24 (fold-0 fidelity digit), 65 (fit vs wall time), 91 (GCV does not collapse on linear/raw), 106–108 and 110 (the §3.4 band's stated sane range, cell count, margin and train-r² tell), 4/8/10 (versions without SHAs).

Numbers the brief singled out — one-line answers:
- dataset id, 1,698 / 1,346 / 176 / 176, fold sizes, all per-fold r²/RMSE/MAE in §1.2 and §1.3, aggregates and stds, theta/gamma/ridge, `sum(dt)` range, target mean/std, z-ranges, 28–100 %, prediction stds and maxima, ranks, condition numbers, coefficient norms, amplification figures, 15 of 20, 11.2 s / 10.9 s, "all 24 configured = fold-resolved", §1.4 Scenario-A numbers, 2 succeeded / 0 degraded, control 0.975: **CONFIRMED** (items above).
- "12 % / 19 %": arithmetic correct given the quoted digits; the 2026-10-03 digits are **NO ARTIFACT in this tree** (item 44–45).
- "all 28 keys byte-identical": **NO ARTIFACT** (item 28). "2.5 s": **NO ARTIFACT** (item 27).
- "below −1 by three or more orders of magnitude": **PARTIAL** — holds for the `ridge 0` class (min 3.30 decades) and linear/1.0/off; fails for linear/gcv/off (2.39) and linear/1.0/on (0.66); the band still separates every cell (item 108).
- configured-theta twins: **bit-identical**, not merely to printed digits (item 67).

## 3. Load-bearing statements that only the prose asserts (no artifact in this tree)

1. **Every 2026-10-03 number** — −18,081, −83,452, −815, −3.7, −78, −6,059, checksum `037baab7…`, `exit_code 1` / `acceptance.ok false` / `metrics {}` / 422 — and therefore the "12 % / 19 % movement" and the entire "digits are decided by rounding" argument of §1.3 / §2.4 / §4. The note's comparison target lives outside this tree.
2. **Artifact identity across the two days** ("all 28 keys byte-identical"). The tree proves the 2026-10-04 id and checksum; it does not carry the diff.
3. **"Same model code at `be081fae` both days", "the audit shadowed the checkout", "same machine"**: no SHA anywhere (`git: {}`), no 2026-10-03 platform record.
4. **All three SHAs** (`3420a1a5`, `be081fae`, `29be6d35`), the stack run id, the staged YAML service block, numpy 2.5.3, service-core module 0.4.0, "no `PYTHONPATH`", `JUNIPER_EXP_PROJECT_DIR`, the `p4/` suite path.
5. **Service defaults = `d 16`**, and the matrix's `d = 16` / 256 RFF features / median gamma / `default_ridge 0.0`: `21` records none of these (readout / ridge / theta are evidenced by replication; `d` only via `23`'s 242 columns and the CLI command in the manifest).
6. **Source-level mechanisms**: `_GCV_GRID` ending at 1000; `_standardize_fit` on the RFF rung; `_lmu_hyperparams` dropping theta; `walk_forward_folds`; "ten smallest singular directions"; "fold 4 blows up outside the last ten".
7. **Feature names** (`market_cap`, `total_shares`, `volume`, `cost_basis`) — the tree has only index-ordered statistics.
8. **Producer z-scoring on the pooled `train` partition** for the normalised artifact.

## 4. What the artifacts carry that the note does not say (a reader of the verdict would want these)

1. **The ill-conditioned solve reproduced exactly across processes.** Per-fold `mse`, `rmse`, `mae` are bit-identical between the HTTP service process (`10-crossval-service-defaults.json`) and the in-process script (`21[0]`) in all five folds, train and eval; the same holds for the E-H configuration. The only difference is `r2`, and the HTTP value equals `1 − mse / var(target_eval, ddof=0)` exactly — a formula difference (the in-process script scores r² differently, ~1e-7 relative). The tree therefore contains one cross-process replicate pair for the catastrophic configuration, and it is exact. This does not test thread-count or BLAS variation (both processes ran on the same host the same day; `thread_env` is all null and the service process's threads are unrecorded), but it means **nothing in the tree demonstrates the "reproducible only to its order of magnitude" behaviour**; that claim rests wholly on the out-of-tree 2026-10-03 digits.
2. **`linear / gcv / off` does not collapse.** Aggregate −246.9, folds −217.6 / −2.66 / −2.04 / −36.6 / −975.5, train r² 0.088–0.317, with λ = 1000 selected in 3 of 5 folds. §2.3's GCV paragraph ("on both rungs … collapses to the fold mean") and §3.2 option (i) ("change `default_ridge` to `gcv`; the linear rung then shrinks instead of exploding") are both contradicted on the raw artifact by the note's own table row. Under the proposed −1 gate, linear+gcv on raw equities fails.
3. **The proposed `train_r2 ≤ 0.9` tell does not fire on the audited configuration.** `linear / 0.0 / off` — the service default that produced −18,081 / −20,345 — has fold-0 train r² 0.453 (max over folds 0.453). The three `ridge 0` cells that do exceed 0.9 are the RFF and normalised ones.
4. **The sane class has five members and its floor is −0.28, not −0.26**; `rff / 1.0 / on` (the normalised E-H twin) sits at aggregate −0.142, fold 4 −0.2765; and `linear / 1.0 / on` at −4.52 is within one decade of the −1 gate.
5. **Registry `n_windows: 1346` is the train split.** The crossval ran on `split: full` (1,698 windows) per the HTTP response; the manifest's `crossval` block records no split or window count, so the suite's registry row under-states the CV sample by 352 windows.
6. **Manifest provenance gaps**: `git` is `{}` (no SHA for any repo); `packages.juniper-data.version` is `0.14.0` for an editable install that served generator `6.0.0` (a 0.14.0 dist serves equities at 3.0.0 — the recorded dist metadata is stale; the code that ran is an unrecorded checkout state); `packages.juniper-ml` is `0.6.0` non-editable; `experiment.description` for the **equities** cell reads "Irregular-Δt sine, RFF readout, walk-forward CV (DP-3 rung 2a)" (inherited from the base config).
7. **Dataset meta is not immutable under an id**: `created_at` moved from 21:06:08Z to 22:14:49Z and `tags` gained `["experiment", "e-h-recurrence-real-data-c001-0d8782ae"]` between `00` and the manifest, with the same `dataset_id` and the same checksum. Consumers keying on `created_at` would see two artifacts.
8. **A zero column in the normalised design**: index 9 has last-step std 0.0 and mean 0.0 in the normalised artifact (raw: std 3.8e-4, mean 27.3). The "near-constant column" the note describes is, after producer normalisation, exactly constant.
9. **Rank at a conventional tolerance is 48, not 113–161**: in every raw fold, 194 of 242 singular values are below 1e-8·σ_max (and below 1e-6·σ_max) — rank 48/242 (80 % deficient), identical across folds. The note quotes `numerical_rank_eps` (113–161), the permissive count. Normalised: 51 / 32 / 32 / 32 / 16 below 1e-8·σ_max.
10. **The weak-direction amplification metric is non-discriminating on the normalised artifact**: fold 0 amp p99 0.099 ↔ eval r² −2.1e13; fold 3 amp p99 4.5e13 ↔ eval r² −206.6; fold 4 0.109 ↔ −12,319. On raw it tracks folds 0–3 and misses fold 4 (0.0028 ↔ −7,239). The normalised fold-0 blow-up coincides instead with ‖coef‖ = 6.6e6 (folds 1–4: 5,896 / 55.5 / 44.0 / 20.6 — a five-decade drop the note's table, which omits folds 1–2, does not show).
11. **Train-fold self-drift**: `memory_z_train_self.max_abs_z` is 7.9 / 7.2 / 8.2 / 9.4 / **22.8** — fold 4's own training memory block already contains >20σ rows.
12. **Conventions**: `eval_std` is population std (ddof 0); `eval_aggregate.rmse` is the mean of per-fold RMSE, not √(mean mse); HTTP fold records carry only `n_epochs: 1` beyond the metrics (no n_train, theta, gamma, ridge — consistent with F-S7).
13. **Wall vs fit**: Σ `fit_seconds` ≈ 10 s per cell of the ≈ 32 s wall; "fit time ≈ 30 s" is wall time.
14. **GCV grid is invisible**: only {60.2, 85.5, 495.4, 1000} were ever selected; grid spacing and extent cannot be inferred from the tree.
15. **Raw last-step z statistics are identical for both artifacts** (affine invariance), so "raw last-step feature max |z| 10–58" is one measurement, not a raw-and-normalised pair.

## 5. Instrument adequacy (Lane A required question: could the instrument have produced a different answer?)

- **Theta axis**: `sum_dt_median_train` = 91.0 in all 120 cell-folds, so the configured (91.0) and fold-resolved arms are the same number by construction; 12 of the 24 cells are exact duplicates. The theta verdict (c) rests on a single value and could not have come out differently on this artifact — it is a null result of the instrument on this data, not a test of theta sensitivity.
- **GCV axis**: 15 of 20 folds saturate at 1000; those cells measure the grid's edge rather than GCV. The instrument cannot say what GCV would choose.
- **Conditioning instrument**: the amplification statistic separates the class on raw folds 0–3 and fails on raw fold 4 and all normalised folds (item 10 above); `coef_2norm` is the discriminating quantity on the normalised artifact.
- **Fidelity check**: same host, same day, unrecorded threads — it can show agreement (it does, bit-for-bit on the solve) but cannot probe the BLAS/thread mechanism the note invokes.
- **Scenario A**: one cell per dataset; `n_windows` reported from the train phase; `git` unrecorded; acceptance band not yet applied (`acceptance.reasons` empty) — the artifact shows the suite *runs*, not that any band would pass.

## 6. Files

- Changed: this file only — `reports/2026-10-05_recurrence-equities-cv-consensus/laneA1.md`.
- Read (evidence): the 12 files in `reports/2026-10-04_recurrence-equities-cv-matrix/` listed in §0; the note under review; `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2.
- Existence-only checks (not opened): `util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py` (18,513 B), `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py` (6,003 B); `.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/` (absent in this worktree, present in the main checkout); `reports/2026-10-03_recurrence-equities-consensus/` (sibling, not opened).
