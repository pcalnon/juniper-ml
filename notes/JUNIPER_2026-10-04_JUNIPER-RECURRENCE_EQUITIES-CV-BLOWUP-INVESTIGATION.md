# Juniper-Recurrence × Equities — Cross-Validation Blow-up Investigation (W0.8 replay, W0.9 matrix, P5 go/no-go)

- **Project**: Juniper — juniper-recurrence (with juniper-data, juniper-recurrence-model, juniper-model-core, juniper-ml experiment stack)
- **Author**: Paul Calnon
- **Date**: 2026-10-04 (v1.0.0); 2026-10-05 (v1.1.0)
- **Version**: 1.1.2
- **Status**: MEASURED and **consensus-reviewed, review complete** (round 1: three Lane A entry points + two Lane B briefs; round 2 on the corrections: one of each; round 3: one Lane A check of the round-2 re-derivation keys, which changed one parenthetical number and no disposition, so the process terminated — all 2026-10-05). **Verdict: GO** (§3.1) — upheld by every re-measurement; R5 may now be ruled on §3.4. The explanatory layer of v1.0.0 did not survive review and is corrected here: the audited
  2026-10-03 digits were solved on a **different artifact served under the same `dataset_id`** (§1.1), the digits of the ill-conditioned solve are reproducible (§2.4), the cause is extrapolation under drift with `ridge = 0` as the amplifier (§2.3), the note's preferred W5.8 option is a measured failure (§3.2), and the R5 band is amended (§3.4). This note is the W5.1 cause-investigation note the plan asked for and ends in an R5 recommendation (§3.4). It applies the R4 note and must be read with the consensus
  record.
- **Consensus record**: [`JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md`](JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md) — what each lane found, what the reconciler re-derived, what remains disputed
- **Plan**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md) (v1.2.0 → v1.3.0 with v1.0.0 of this note; v1.4.0 with v1.1.0), work items W0.8, W0.9, W5.1; finding F-SCI1; rulings R5, R4 note
- **Consensus record of the plan**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md) §8 ("what the evidence cannot support" — this note supplies the two measurements it named)
- **Instruments**: `util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py` (`replay` = §1, `matrix` = §2.1–2.3), `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py` (§2.4); reconciler re-derivations `util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive.py`, `..._rederive_b1.py` and `..._rederive_b1r2.py` (round 2: the cells v1.1.0 had quoted without an artifact, plus the embargoed in-era control); Lane A3's fresh-stack rerun
  `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py`
- **Evidence**: `reports/2026-10-04_recurrence-equities-cv-matrix/` — `00-dataset-create.json`, `01-recurrence-health.json`, `10-crossval-eh-rff.json`, `10-crossval-service-defaults.json`, `20-matrix-datasets.json`, `21-matrix-cells.json`, `22-matrix-table.md`, `23-linear-conditioning.json`, `scenario-a-rerun/`; the 2026-10-05 rerun and re-derivations under `reports/2026-10-05_recurrence-equities-cv-consensus/` (`laneA3-rerun/`, `reconciler-rederive.json`, `reconciler-rederive-b1.json`,
  `reconciler-rederive-b1r2.json` — keys `F10`–`F16` are cited below as "F10" etc.)

---

## 0. The question, and the instrument

The audit measured aggregate eval r² = −18,081 on `POST /v1/crossval` for the E-H dataset selector and could not isolate the cause, because the request that produced it carried no model parameters: the service defaults applied (`readout=linear`, `ridge=0.0`), not the E-H suite's own configuration (RFF readout, `ridge=1.0`, 256 features, median gamma).
Plan §3.9 therefore listed four candidates and withdrew every hypothesis of record; W0.8 was to replay the real configuration and W0.9 to widen it to a controlled matrix and issue the go/no-go for P5.

### 0.1 Stack as served

| Component | Value |
| --- | --- |
| Launch | `util/experiment_stack.bash --up --recurrence --config juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` — run `20261004T210331Z-491a`, data `127.0.0.1:8110`, recurrence `127.0.0.1:8260`; the E-H base YAML staged so the service block matches the suite (`default_d: 16`, `default_theta: null`, `default_ridge: 0.0`, rate limit off). Reproduced 2026-10-05 as run `20261005T132907Z-5493` (Lane A3), same ports, same versions. |
| juniper-data | `JuniperData` env, editable checkout `29be6d35` (`main`); `equities_seq` generator `6.0.0`; per-run storage and per-run (cold) equities cache |
| juniper-recurrence | `JuniperCascor1` env (Python 3.14.7), app 0.5.0 editable at `be081fae`; **`juniper-recurrence-model` 0.3.0 editable** (W0.1 model half applied 2026-10-04 — the audit's 0.1.5 wheel is gone); `juniper-service-core` dist 0.5.0 / module 0.4.0 (W0.1 service-core half deferred, §0.3); `juniper-model-core` 0.2.0; `juniper-data-client` 0.5.0 editable; numpy 2.5.3; OpenBLAS 0.3.34, 16 threads by default |
| Dataset | `equities_seq-6.0.0-15505731cba5b86d` — AAPL 2015-01-01 → 2022-01-01, `lookback 64`, `regression_target log_return`, `seed 20260807`, all other params at the generator's defaults (`fundamentals_fill: nan`, `normalize_features: false`); `full` view 1,698 windows (1,346 / 176 / 176 partitions), 64 × 15 features, `sum(dt)` per window 88–97 calendar days (mean 91.3, std 1.7), target mean 0.00101 / std 0.01835 |
| Folds | model-core `walk_forward_folds(1698, n_folds=5, scheme="expanding", embargo=2)` → `fold_size = 283`; train sizes 281 / 564 / 847 / 1,130 / 1,413, eval 283 each (confirmed by running the function). **Fold 3's eval holds 69 `val` rows; fold 4's eval is 107 `val` rows plus the entire 176-row `test` partition** (§2.5). |
| RFF seed | `LMURegressor(random_seed=0)` — the service's factory never passes a seed, so the HTTP route, the in-process matrix and the suite all draw the same random features. The seed was not varied in v1.0.0; §2.5 reports a sweep. |

### 0.2 Why the in-process matrix is the service's own path

The HTTP route cannot return the resolved theta, the selected ridge, the RFF gamma, or anything about the memory states (F-S7: the start log prints `theta=None`).
§2 therefore fits in-process through the same objects the route uses — `juniper_recurrence._readout.build_lmu_regressor` → `LMURegressor.fit` / `predict` with the `SequenceData.fit_kwargs()` slices, over the same `walk_forward_folds`, with `pass_eval_as_val=False` as `cross_validate` does — and reads the diagnostics off the fitted model.
Fidelity was checked, not assumed, and the consensus review sharpened the statement: on the two configurations both paths ran, the **solve** is bit-identical — per-fold `mse`, `rmse` and `mae` agree to the last bit in every fold — and only `r²` differs, at ~1e-7 relative, because the route's scorer casts `y` to float64 before `ss_tot` and the in-process scorer does not (fold 0 of the defaults cell: −93,606.24 via HTTP, −93,606.23 in-process; aggregate −20,344.64 both ways). On 2026-10-05 a fresh stack
reproduced both replays, all 24 matrix cells and all 10 conditioning rows **bitwise** (Lane A3).

### 0.3 What was not repaired

The service-core half of W0.1 (editable 0.7.0 from the juniper-ml checkout) was **deferred**: a live cascor listener on `:8202`, part of the canopy E2E stack (data `:8101`, canopy `:8051`, all up since 2026-09-22), imports `juniper_service_core` from the same env, and replacing a package under a running service is the owner's call.
It does not touch the numbers here (service-core is the FastAPI tier; crossval numerics live in the model and model-core), and the recipe with the deferral is recorded in `juniper-recurrence/AGENTS.md` (juniper-recurrence#189).

---

## 1. W0.8 — the E-H configuration, replayed on the frozen artifact

### 1.1 The artifact is Scenario A's artifact; the audited number was solved on a second mint of the same id

`POST /v1/datasets` with the E-H params resolved to **`equities_seq-6.0.0-15505731cba5b86d`**, the id the audit measured, in 2.5 s from a cold per-run cache (one ticker). Its arrays were diffed key by key against the copy the audit's **Scenario A** archived (`.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/`, minted 09:14:24Z, meta `checksum` `c02004e1…`): **all 28 keys byte-identical**, and the 2026-10-05 mint is byte-identical again (whole-file sha256 reproduced).

**v1.0.0 drew the wrong conclusion from the checksum.** The audit ran two stacks on 2026-10-03, and the −18,081 (`24-c-crossval-shadow.txt`) belongs to **Scenario B**, whose own data service minted the same id 85 s later (09:15:49Z, `.amp/in/scratch/data-store/`, checksum **`037baab7…`**). That mint differs from Scenario A's in exactly two feature columns: `dividend` (column 10) is all zero in every partition (A: 0 … 0.22; 1,367 + 180 + 178 cells), and `split_ratio` (column 11) is zero in `X_val` where A
carries the 2020-08-31 4:1 split (64 cells). The producer explains it: `equities/generator.py` zero-fills `dividend` and `split_ratio` when yfinance's response omits the action columns ("absent means none happened"), so an upstream response without the action columns is served, silently, under the same id — **cause unknown**: a transient yfinance response, a per-run cache CSV lacking the columns, or a column-flattening edge in the download path are all consistent with the evidence (§4). Re-solving `linear /
ridge 0.0` on the Scenario-B arrays reproduces **every audited digit** (fold 0 train r² 0.452957979 / eval −83,451.610; folds 1–4 −814.665 / −3.720 / −78.492 / −6,059.229; aggregate −18,081.543).

The meta `checksum` is therefore a **content** fingerprint, not a container one: `compute_checksum` is sha256 over an uncompressed `np.savez` of the arrays with sorted keys, numpy writes fixed 1980-01-01 zip timestamps, and `c02004e1…` has now been reproduced on three days. A different checksum under one id meant different arrays. v1.0.0's "first reading" — *the equities data drifted under the same id* — was right for the mint the audit measured, and the sentence that dismissed it was wrong. **F-P8 is
re-filed as a Major DATA finding** (§3.2 item 4): the `dataset_id` hashes the request, not the content, and the generator makes an incomplete upstream response indistinguishable from a complete one.

### 1.2 The E-H request body and its result

The body the suite sends (`run_experiment.py::_lmu_hyperparams` drops the YAML's `theta: null`, so the service resolves theta from the data; the suite's `dataset.params` override replaces the base YAML's params wholesale, so the body is exactly this):

```json
{"dataset": {"dataset_id": "equities_seq-6.0.0-15505731cba5b86d"}, "n_folds": 5, "scheme": "expanding", "embargo": 2,
 "d": 16, "ridge": 1.0, "readout": "rff", "rff_features": 256, "rff_gamma": "median"}
```

`POST /v1/crossval` → HTTP 200 in 11.2 s (`10-crossval-eh-rff.json`):

| fold | n_train | train r² | train RMSE | eval r² | eval RMSE | eval MAE |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 281 | +0.1843 | 0.01565 | **−0.0803** | 0.01177 | 0.00819 |
| 1 | 564 | +0.1604 | 0.01346 | **−0.0500** | 0.01380 | 0.00994 |
| 2 | 847 | +0.1392 | 0.01327 | **−0.1020** | 0.02062 | 0.01479 |
| 3 | 1,130 | +0.1262 | 0.01476 | **−0.0856** | 0.02882 | 0.02011 |
| 4 | 1,413 | +0.1239 | 0.01761 | **−0.2584** | 0.01784 | 0.01384 |
| **aggregate** | | | | **−0.1153** (std 0.0735, population) | 0.01857 | 0.01337 |

(`n_train` is not in the HTTP response; it comes from the fold construction. The aggregate is the plain mean of fold r²; `eval_std` is the population std; aggregate RMSE is the mean of per-fold RMSE.)

Per-fold eval RMSE (0.012–0.029) sits at the target's own per-fold standard deviation (0.011–0.028): the model predicts a little worse than the fold mean. Resolved internals (from the in-process reproduction, §2): theta 91.0 in every fold, gamma 0.0508 / 0.0512 / 0.0499 / 0.0499 / 0.0553, ridge 1.0 as requested, RFF seed 0.

**The E-H configuration does not blow up.** This is the number the E-H suite comment expects ("r2 ≈ 0 … NOT negative blowups"). What it does and does not mean is in §2.5.

### 1.3 The control — service defaults on the same artifact, same day

The same body with no model parameters (`readout=linear`, `ridge=0.0`, d 16, data-driven theta) → HTTP 200 in 10.9 s (`10-crossval-service-defaults.json`):

| fold | train r² | eval r² (2026-10-04, Scenario-A mint) | eval r² (audit, 2026-10-03, Scenario-B mint) | eval RMSE |
| --- | --- | --- | --- | --- |
| 0 | +0.4532 | **−93,606** | −83,452 | 3.464 |
| 1 | +0.3224 | **−798.5** | −815 | 0.381 |
| 2 | +0.2487 | **−3.70** | −3.7 | 0.043 |
| 3 | +0.1836 | **−75.6** | −78 | 0.242 |
| 4 | +0.1353 | **−7,239** | −6,059 | 1.353 |
| **aggregate** | | **−20,345** (std 36,731) | −18,081 | 1.097 |

The two columns differ by 12 % (fold 0) and 19 % (fold 4) because **two feature columns differ** between the mints (§1.1), not because of rounding. v1.0.0 said "a solve whose out-of-sample answer changes while nothing it reads has changed is being decided by rounding"; two of the fifteen columns it read had changed. Within one environment the solve is bit-identical across processes and across days (§0.2; the 2026-10-05 rerun), and OpenBLAS thread count (1 / 2 / 4 / 8 / 16) moves fold 0 by ≤ 4e-4 relative
and fold 4 by ≤ 2e-4 — three hundred times smaller than the audited gap. The audit's in-sample train r² differs too (fold 0 0.45296 vs 0.45324), which rounding of an out-of-sample extrapolation cannot explain and a different feature matrix can. The audited **class** ("catastrophic") reproduces on both mints; the audited **digits** reproduce on the mint they were solved on.

**W0.1 acceptance, in passing**: both requests returned 200 with no `PYTHONPATH` on a decision-11 artifact — the request that returned 422 `missing required key 'X_full'` in the audit. The model half of the env repair is verified.

### 1.4 The suite path records the same number (Scenario A re-run, after W0.3 / W0.4 merged)

The audit's Scenario A — `run_suite.py --suite p4/e-h-recurrence-real-data.yaml` through the launcher — was re-run on 2026-10-04 from juniper-ml `main` at `3420a1a5` (W0.3 / W0.4 merged in juniper-ml#2145) against the model-repaired env (`reports/2026-10-04_recurrence-equities-cv-matrix/scenario-a-rerun/`).
Where the audit recorded the equities cell as `succeeded` with `exit_code: 1`, `acceptance.ok: false`, `metrics: {}` and a 422'd crossval, the registry now reads: `outcome: succeeded`, `exit_code: 0`, `phases: {train: ok, predict: ok, crossval: ok, save_model: ok}`, `metrics: {train_r2: 0.1163, cv_r2: -0.1153, cv_r2_std: 0.0735, n_windows: 1346}` — where `n_windows` is the **train partition's** count from the train phase; the crossval ran on the 1,698-window `full` view and the manifest's `crossval` block
records no window count.
`REPORT.md` says `Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run.` and carries the four columns. The control cell (irregular sine) reports `cv_r2 0.975`.
The `cv_r2` equals the §1.2 aggregate **to every digit** (−0.11526096841533144) — the suite's E-H row, driven as an operator drives it, now produces the number this note measured by hand, and the four F-D1 / F-D2 symptoms are gone from the same artifact that showed them.
(From a `.claude/worktrees/` checkout the suite needs `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, because its `base_config` walks to a sibling repo; the loader documents the override. The manifest records no git SHA for any repo — `git: {}` — and the dist version of an editable install, so the checkout state that ran is a claim, not a record; a provenance gap for the driver.)

---

## 2. W0.9 — the controlled matrix

### 2.1 Design

{readout `linear` / `rff`} × {`ridge` 0.0 / 1.0 / `gcv`} × {producer `normalize_features` off / on} × {theta fold-resolved (`None`) / configured (91.0, the full-set median `sum(dt)`)} = 24 cells, 5 expanding folds each, one ticker, `d = 16`, RFF at 256 features and median gamma, `default_ridge = 0.0` as the service, RFF seed 0.
**The theta axis is degenerate by construction**: the configured value is the full-set median and every expanding train fold's median is also 91.0 (`sum(dt)` std 1.7), so each configured cell duplicates its fold-resolved twin bit for bit and the matrix has **12 distinct cells**.
The normalised artifact is `equities_seq-6.0.0-fa3aae11ac374c94` (same rows; feature columns **min-max scaled to [0, 1]** by the producer, with the scaler fitted on the pooled `train` partition — the R4 note's leakage, kept deliberately so the cell measures the producer knob as shipped).
Per fold the script records train/eval metrics, resolved theta, selected ridge and gamma, the fold's median `sum(dt)`, the eval memory block's z-range against the train fold's column statistics, the raw last-step feature z-range, and prediction vs target ranges. Wall time ≈ 32 s per cell (≈ 10 s of it fitting); total ≈ 13 min.

### 2.2 Results

Eval r² per fold (0…4) and aggregate; `train r²` fold 0 → 4; `ridge` is the resolved value (GCV writes back the selected λ). Theta resolved to **91.0 in every fold of every cell**, so the table shows the fold-resolved rows only (`22-matrix-table.md` has all 24).

| readout | ridge | normalize | eval r² per fold | **agg** | eval RMSE | train r² (f0 → f4) | ridge / gamma resolved | eval memory max abs z per fold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear | 0.0 | off | −93,606 / −798 / −3.70 / −75.6 / −7,239 | **−20,345** | 1.097 | 0.453 → 0.135 | 0 | 24 / 23 / 8 / 199 / 44 |
| linear | 1.0 | off | −6,688 / −147 / −5.56 / −121 / −3,356 | **−2,064** | 0.473 | 0.425 → 0.168 | 1 | same |
| linear | gcv | off | −218 / −2.66 / −2.04 / −36.6 / −976 | **−247** | 0.179 | 0.317 → 0.088 | 1000 / 1000 / 85.5 / 60.2 / 1000 | same |
| rff | 0.0 | off | −9,869 / −50.9 / −3.03 / −1.96 / −6.35 | **−1,986** | 0.270 | 0.959 → 0.221 | 0 / γ 0.050–0.055 | same |
| **rff** | **1.0** | **off** | **−0.08 / −0.05 / −0.10 / −0.09 / −0.26** | **−0.115** | **0.0186** | 0.184 → 0.124 | 1 / γ 0.050–0.055 | same |
| rff | gcv | off | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 | **−0.015** | 0.0177 | 0.002 → 0.001 | 1000 / 495 / 60.2 / 1000 / 1000 | same |
| linear | 0.0 | on | −2.1e13 / −8.5e6 / −22.2 / −207 / −12,319 | **−4.3e12** | 10,495 | 0.907 → 0.212 | 0 | 24 / 23 / 11 / 337 / 50 |
| linear | 1.0 | on | −0.27 / −0.09 / −0.11 / −0.13 / −22.0 | **−4.52** | 0.0306 | 0.140 → 0.085 | 1 | same |
| linear | gcv | on | −0.05 / −0.01 / −0.00 / −0.01 / −0.01 | **−0.015** | 0.0177 | 0.002 → 0.003 | 1000 × 5 | same |
| rff | 0.0 | on | −15,904 / −62.5 / −3.42 / −3.24 / −10.0 | **−3,197** | 0.337 | 0.956 → 0.229 | 0 / γ 0.048–0.061 | same |
| **rff** | **1.0** | **on** | **−0.14 / −0.06 / −0.12 / −0.11 / −0.28** | **−0.142** | **0.0188** | 0.186 → 0.119 | 1 / γ 0.048–0.061 | same |
| rff | gcv | on | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 | **−0.013** | 0.0177 | 0.002 → 0.001 | 1000 / 1000 / 495 / 1000 / 1000 | same |

Prediction scale, the quantity r² hides (eval prediction std per fold vs target std 0.011 / 0.013 / 0.020 / 0.028 / 0.016):

| cell | eval prediction std per fold | max abs prediction |
| --- | --- | --- |
| linear / 0.0 / off | 3.46 / 0.21 / 0.030 / 0.24 / 0.43 | 9.81 |
| linear / 0.0 / on | 28,000 / 22 / 0.083 / 0.40 / 0.86 | 137,000 |
| linear / 1.0 / on | 0.0049 / 0.0028 / 0.0046 / 0.0068 / 0.031 | 0.092 |
| rff / 0.0 / off | 1.05 / 0.093 / 0.033 / 0.034 / 0.037 | 4.21 |
| **rff / 1.0 / off** | 0.0043 / 0.0040 / 0.0043 / 0.0062 / 0.0076 | 0.021 |
| rff / gcv / off | 0.0002 / 0.0004 / 0.0008 / 0.0001 / 0.0002 | 0.0036 |

A daily log return has a standard deviation of about 0.018; the service-default fit predicts a log return of 9.8 (e^9.8 ≈ 18,000×, a nonsense scale) and the normalised ridge-0 fit up to 137,000. In every sane fold the RFF rung's prediction std is at most 0.51× the target's.

### 2.3 Per-candidate verdicts

- **(c) theta — refuted for the hypothesis the plan posed (a fold-to-fold theta mismatch).** `sum(dt)` over the full set is 88–97 calendar days (std 1.7) and its median is 91.0 in every expanding train fold, so the data-driven theta equals the configured one everywhere; the 12 configured cells are bit-identical to their fold-resolved twins. Theta does not differ between folds on this artifact. **No cell tried any other theta**, so nothing here says whether theta is a lever in general. F-S7 (theta never
  logged) stands as an observability defect, not as a cause.
- **(b) producer normalisation — refuted as the lever for the blow-up; the mechanism it named is real.** Producer min-max scaling does not rescue the unregularised solve (it makes it 2.1e8× worse: −20,345 → −4.3e12, because scaling raises the design's numerical rank from 113–161 to 210–226 and exposes more tiny singular values to the pseudo-inverse) and does not make linear ridge 1.0 sane (fold 4 −22). For the sane configuration the difference (−0.115 raw vs −0.142 scaled) is **below the RFF seed spread**
  (§2.5: seeds 0–5 range −0.115 … −0.252, std 0.045), so it supports no direction. Consequence for **W1.1(a)**: the documented bundle keeps `normalize_features: false` because the measurement **gives no reason to turn it on**; producer normalisation is a convenience, not a CV control (R4 note). The drift of price-level features out of the training support that candidate (b) also named is real and is part of the cause (next item).
- **(a) unregularised linear readout — confirmed as the amplifier of the audited number; the cause of record is the service-default readout applied to a chronologically drifting input, both necessary.** Every `ridge = 0.0` cell is catastrophic in both readouts and both normalisations (−20,345 / −1,986 / −4.3e12 / −3,197), and `ridge = 0` sets the magnitude. It is not *necessary*: the linear rung with `ridge = 1.0` (−2,064) or GCV (−247) on the raw memory block is still catastrophic, because that rung does
  not scale its columns (last-step feature std from 0 — `cost_basis` is constant — and 0.022 up to 7.9e11 for `volume`, `total_shares`, `market_cap`), against which any single penalty is nothing. And it is not *sufficient* in-support: an **embargoed in-era block** — eval = fold 2's 283-window block inside fold 4's training era, a 64-window embargo on both sides, 1,002 training rows, the identical design and solver — scores −1.8 at `ridge = 0`, −2.3 at `ridge = 1.0` and −0.42 at GCV, finite where the
  chronological fold with the same eval block scores −3.70 (F15); a same-pool shuffled split of fold-4 size scores −0.33 / −0.001 / −0.08 (F12), though without an embargo it also carries 61-of-64-day near-duplicates and so says "in-support", not "no drift". The 10³–10⁴ catastrophes are **folds 0 and 4**, whose eval blocks sit at era boundaries (n ≈ p at fold 0; the 2020 split entering `split_ratio` and the 2021 regime at fold 4). Every cell of this matrix is chronological, so it **does not separate the
  readout from the drift**; the drift is intrinsic to any chronological equities split, the actionable lever is the default (W5.8), and §2.4 quantifies the conditioning that turns the conjunction into −93,606. Candidate (b) stays withdrawn as a hypothesis of record: its lever is refuted, and its mechanism is this drift.
- **(d) a genuine model or `dt`-handling defect — not implicated in-support; untested under drift.** The irregular-sine control through the same route and configuration scores `cv_r2 0.975` (§1.4): it shows the route and configuration are sound on a stationary signal with a synthetic `dt` pattern, and it does not test a defect that would appear only under equities' calendar gaps or out-of-support memory states. In-support both rungs behave: on the embargoed in-era block (F15) the RFF rung scores −0.081 at
  `ridge 1.0` and −0.006 at GCV and the linear rung is finite; on the three shuffled draws (F12) rff/1.0 scores −0.148 / −0.004 / −0.052 and rff/gcv ≈ 0. v1.0.0's sentence "the only rung that standardises per fold is the one that works" is false in both directions — `rff / 0.0` standardises and scores −1,986; `linear / gcv / on` does not standardise per fold and scores −0.015 — and the RFF rung is sane because `cos(·)` **bounds** its features and the penalty shrinks them, not because it standardises: the
  linear rung given the same per-fold train-only standardisation and the same `ridge = 1.0` scores **−192**. The eval memory states do leave the train fold's support in every fold (max |z| 8–199 raw, 11–337 scaled; 28–100 % of eval rows have at least one column beyond 5 σ; raw last-step feature max |z| 10–58), i.e. the drift is real and intrinsic to price-level inputs; with bounded features and ridge ≥ 1 the RFF readout's predictions shrink toward the mean (prediction std 0.004–0.008 against a target std of
  0.011–0.028) instead of exploding. Standardisation is necessary for the linear rung and not sufficient.
- **GCV — a note, not a candidate.** On three of the four GCV configurations GCV picks a very large penalty and the fit collapses to the fold mean (train r² ≈ 0.002, eval r² −0.01): the configuration whose eval r² is nearest zero, by abstaining. **Not on `linear / gcv / off`** (−247, λ at the ceiling in three of five folds): on unscaled features a single λ cannot be large for `market_cap`'s directions and small for the price columns' at once. In **15 of 20** GCV folds the selected λ is `1000.0`, the last
  point of `_GCV_GRID` (`np.logspace(-6, 3, 60)`). The optimum is **known**, not unknown: for the RFF rung it is the null model (λ → ∞, the intercept-only fit) in folds 3 and 4 (λ = 1e12 at the extended grid's edge) and effectively in fold 0 (GCV within 4e-9 of the null value at λ ≈ 2e5), and interior (λ ≈ 398 / 63) in folds 1 and 2; for the linear rung on raw features the null model's GCV is below every finite grid point in all five folds. No grid extension changes that (§3.2 item 2).

### 2.4 Conditioning of the linear design (why ridge 0 is catastrophic under drift)

`util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py` rebuilds exactly what `LinearReadout` solves — `[ memory block (15 × 16 = 240 cols) | target_dt | 1 ]`, 242 columns, in float64 as the solve runs — per fold, and takes its SVD (`23-linear-conditioning.json`):

| artifact | fold | n_train | numerical rank (lstsq cutoff) | σ_max / σ_min | ‖coef‖₂ (min-norm) | out-of-support component along the 10 smallest directions, p99 train → p99 eval |
| --- | --- | --- | --- | --- | --- | --- |
| raw | 0 | 281 | **113** / 242 | 8.6e32 | 0.16 | 0.33 → **26,500** |
| raw | 1 | 564 | 149 | 2.4e31 | 0.10 | 10.5 → 2,540 |
| raw | 2 | 847 | 159 | 2.5e31 | 0.062 | 0.056 → 0.87 |
| raw | 3 | 1,130 | 160 | 1.3e31 | 0.047 | 6e-14 → 454 |
| raw | 4 | 1,413 | 161 | 1.5e22 | 0.026 | 2e-5 → 0.0028 |
| scaled | 0 | 281 | **210** / 242 | 1.8e24 | **6.6e6** | 6e-7 → 0.099 |
| scaled | 3 | 1,130 | 210 | 1.2e21 | 44 | 1.8e-4 → **4.5e13** |
| scaled | 4 | 1,413 | 226 | 1.1e20 | 20.6 | 7e-4 → 0.11 |

Two columns of this table are not what v1.0.0 called them. The last column is `|row · vᵢ| / σᵢ` over the **ten smallest** right-singular directions of the train design; every reported rank is ≤ 226, so all ten lie **below `lstsq`'s cutoff** and the solve discards them — the column is a drift indicator (how far eval rows leave the training row-space along numerically-null directions), not the gain the pseudo-inverse applies, and it does not track fold 4 or the scaled folds (whose blow-ups coincide with
‖coef‖₂, 6.6e6 in scaled fold 0). σ_max / σ_min is the 2-norm condition number including the rounding floor, not the amplification of the retained system. The mechanism the prose argues is still right and comes from the code, not from those columns: `lstsq(rcond=None)` keeps every σ above `eps · max(M, N) · σ_max` and multiplies the eval rows' components along the retained weak directions by 1/σ.

The "rank deficiency" is a **column-scale artefact of that relative cutoff**, not a degenerate dataset: σ_max (2.8e12 … 8.9e12) is set by the `market_cap` / `total_shares` / `volume` blocks, and under it ~130 directions carrying nearly all the price and return information are truncated. The only exactly-constant memory columns are `split_ratio`'s sixteen (zero until the 2020-08-31 split; folds 0–3). `cost_basis` is an exactly-constant **feature** — 27.3325 in every window and step, the one zero-variance raw
column (F16; Lane A3's `30-numpy-checks.json`) — whose sixteen memory columns vary only with the `dt` sequence and carry no price information; `total_shares` (coefficient of variation 0.62) is not near-constant. v1.0.0 was right about the first and wrong about the second. The same fold-0 design **column-standardised** has rank 226 / 242 and fold 4 has **full rank 242**. That is why column scaling is part of any fix and why a scalar penalty on the raw design is not one.

The min-norm solution is well behaved in-sample (small ‖coef‖, train r² 0.14–0.45) because the training rows have, by construction, no component along the discarded directions. Eval rows do — the drift of §2.3 — and the retained weak directions are extrapolated. That is the −93,606.

**The digits are reproducible.** The solve is bit-identical across the HTTP service process and the in-process script (r² differs only by scorer precision, §0.2), across two service processes, and across the 2026-10-04 and 2026-10-05 runs; thread count moves fold 0 by ≤ 4e-4 relative (Lane A3's sweep), row order by 2.4 % and a float32 round-trip of the design by 6.0 % on fold 0 — and by 5e-5 / 7e-6 on fold 4 (F14) — all far below the 12–19 % between the audit and this note, which §1.1 attributes to the two
mints. v1.0.0's "reproducible only to its order of magnitude" is withdrawn. (Fold 0 — 281 rows against 242 columns — is the one rounding-sensitive fold at the per-cent level; dropping it changes the sane aggregate −0.115 → −0.124 and the defaults aggregate −20,345 → −2,029.)

### 2.5 Fidelity and limits of the instrument

- In-process vs HTTP: the solve is bit-identical on the two configurations both paths ran; r² differs at ~1e-7 relative by scorer precision (§0.2). The in-process diagnostics read private attributes (`_memory_block`, `_readout`, `_side_channel`); a future refactor that renames them breaks the script, not the finding. The script assumes `default_ridge = 0.0` and `random_seed = 0` rather than reading them from the running service.
- **One RFF seed.** The service, the matrix and the suite all use `random_seed = 0`. Sweeping seeds 0–5 on the raw artifact gives rff/1.0 aggregates −0.115 / −0.131 / −0.126 / −0.153 / −0.156 / −0.252 (mean −0.155, std 0.045; per-fold minimum −0.558 at seed 5, fold 4). The matrix's draw is the best of six; `rff / gcv` is seed-stable over the three seeds measured (−0.013 … −0.015, F13). Any comparison between two RFF cells finer than ≈ 0.05 in aggregate is noise.
- **The CV population includes the `test` partition.** The `full` view is `train | val | test`; fold 3's eval holds 69 `val` rows and **fold 4's eval holds 107 `val` rows and the entire 176-row `test` partition** (2021-04-21 → 2021-12-29). Fold 4 is the worst fold in both rff/1.0 cells (in the three GCV cells fold 0 is worst and fold 4 best). Re-measured on train + val only (1,522 windows; F10): rff/1.0 −0.101, rff/gcv −0.006, service defaults −17,365 — class unchanged. W5.3's "`test` is touched once" is
  already void for any full-view CV run, and the population W5.2 will govern (train + val, entity-grouped) is not the one measured here.
- **Embargo 2 against a 64-step look-back**: every fold's first eval window shares 61 of its 64 days with the last train window. The target is next-day `log_return`, so there is no target leakage (train targets ≤ day t+1, eval targets ≥ day t+4); near-duplicate rows across the boundary flatter an over-fitted readout by at most ≈ 0.04, within the seed noise (F11: embargo 64 gives rff/1.0 −0.153 on the full view and −0.111 with `test` excluded; rff/gcv −0.017 / −0.009).
- **No drift-free cell** is in the matrix; the shuffled split and the embargoed in-era block in §2.3 were computed in review (F12, F15), on one block of one artifact — folds 0 and 4 have no in-era counterpart.
- One ticker (AAPL), one window (2015–2022), one dataset seed, `d = 16`. Nothing here speaks to multi-ticker folds (F-P7 / W5.2), to other `d`, to other tickers, dates or seeds, or to the MLP rung.
- "Sane" means "bounded and finite": an aggregate r² of −0.12 on next-day log returns says the model has **no demonstrated skill** at this horizon with these features — and in-support (the embargoed in-era block, F15) the RFF rung still scores −0.08, so this is not a statement about market efficiency; it is that these features with this readout carry no demonstrable next-day signal. The r² baseline is the eval fold's own mean, a stricter baseline than the bench's naive-persistence comparison. It is a
  scientific result to report, not a success to celebrate.

---

## 3. Verdict and consequences

### 3.1 Go / no-go for P5: **GO**

The E-H configuration (RFF, ridge 1.0, 256 features, median gamma, d 16, data-driven theta) produces a bounded, finite out-of-sample number on the frozen artifact (§1.2), reproduced in-process and on a fresh stack (§2.2, bitwise), and the review established it more broadly than v1.0.0 did: on both 2026-10-03 mints (−0.115 on mint A; −0.1013 on mint B, F13), across six RFF seeds (worst aggregate −0.252), with embargo 64 (−0.153, F11), with `test` excluded (−0.1014, F10 — a different measurement from mint B's
that happens to round the same), and in-support (−0.08 on the embargoed in-era block, F15); at seed 0 its predictions never exceed |0.021| against a target std of 0.018, and the instrument could have said no for the same rung (`rff / 0.0` returned −1,986). The −18,081 is a property of the **service defaults** — a linearly-extrapolating, unscaled readout on a drifting input (§2.3, §2.4) — not of theta or the `dt` handling; the data contract has its own, separate finding (§1.1, F-P8).

Under the plan's gating paragraph this makes **W5.1 a documentation-and-defaults-hardening task**, not a model/CV defect investigation ("tuning" is the wrong word: there is no in-support signal to tune toward); W5.2 (entity-grouped chronological folds) proceeds independently as planned; P5's remaining content is as written.

### 3.2 What must change regardless of the verdict (recommendations for the owner; proposed as plan items)

1. **The service default `readout=linear`, `ridge=0.0` must not be used for equities** — measured on one ticker; expected for any non-stationary real-data input by the mechanism of §2.4. It is the configuration a bare `POST /v1/crossval` or `POST /v1/train` gets, the one canopy's registry seed falls into (canopy forwards only `d` / `theta` / `ridge` and **cannot select RFF**, so for canopy the default is the only fix), and the one `juniper-recurrence train` gets without `--ridge`. The bench (constructs
   `LMURegressor` directly) and the suite's `save_model` rerun (passes `--ridge` / `--readout`) are not affected. The options v1.0.0 listed were measured in review (`reconciler-rederive.json`):

   | option | aggregate eval r² (raw artifact) | note |
   | --- | --- | --- |
   | (i) `default_ridge: 0.0 → "gcv"` alone | **−247** (grid to 1e12: −35) | GCV's null model is below every finite grid point; fails W5.8's "> −1" acceptance |
   | (ii) per-fold train-only standardisation on the linear rung alone, ridge 1.0 | **−192** | standardisation is necessary, not sufficient |
   | (i) + (ii) | −0.195 (λ at the ceiling in every fold) / −0.019 (grid extended: the null model in three folds, interior λ ≈ 1.3e5 / 6.3e3 in folds 3–4) | passes by abstaining; train r² 0.06–0.10 / ≈ 0 |
   | rff / gcv — the RFF rung's own default | **−0.015**, train r² ≈ 0.002; seed-stable over seeds 0–2 (−0.013 … −0.015, F13) | in band by abstaining; already what an RFF request without `ridge` gets |
   | (A) default readout `rff`, ridge 1.0 | **−0.115** at seed 0 (−0.155 ± 0.045 across RFF seeds 0–5), train r² 0.12–0.18 | the in-band default that retains a fit — an in-sample criterion the owner did not set; needs a `Settings.default_readout` that does not exist and changes the model class canopy is served |

   Two options pass the plan's acceptance ("aggregates above −1"), and the choice between them is the owner's, with the trade-off stated: **(B)** `default_ridge: "gcv"` **and** per-fold standardisation on the linear rung — the W5.8 row as the plan scopes it, an abstaining default whose caller sees a plausible low-signal r² with nothing that says the model abstained, so the crossval / train response must first report the selected λ and a null-model / at-ceiling flag (item 3); or **(A)** a default readout of
   `rff` with `ridge: 1.0`, filed separately as **W5.11** because it adds a setting and is a canopy-visible behaviour change — a fit that scores worse out of sample than the abstaining defaults, against an abstention that must announce itself. Constraints: (ii) must not alter the `ridge = 0` path (the bench's ratified conformance baseline — a standardised min-norm solve is a different solution, −8.8e12 on this data); `conf/experiments/irregular-sine-rff.yaml`'s `service.default_ridge: 0.0` is the E-H
   suite's `base_config` and must change in the same PR or every experiment stack keeps the old default. A pre-1.0 "Changed" entry in recurrence 0.6.0, candidate for the same ruling pattern as R8. **Proposed as W5.8** (recurrence + model), acceptance "a bare request on the E-H artifact aggregates above −1 **and** the response reports λ"; needs owner acceptance.
2. **Report a null-model / at-ceiling GCV selection**, do not extend the grid: 15 of 20 GCV folds selected the grid's last point, and the optimum beyond it is the null model for the RFF rung in three of five folds and for the raw linear rung in all five (§2.3). "Re-run off the ceiling" is unsatisfiable; what an operator needs is a WARNING in the model logger (W2.4) and a flag in the response. **Proposed as W5.9** (model); S.
3. **Return the resolved theta, gamma, selected ridge and the GCV flag per fold in the crossval response** (and log them — F-S7, W2.4's remit covers the logs only): every number in §2.3 that decided a candidate came from an in-process read the service cannot provide today, and the band in §3.4 cannot be made null-model-aware without it. **Proposed as W5.10** (recurrence); S.
4. **F-P8, re-filed as Major (DATA)**: the `dataset_id` hashes the request, so two mints of one id can differ in content, and `equities/generator.py` zero-fills `dividend` / `split_ratio` when yfinance omits the action columns, so an incomplete upstream response is served as a complete artifact with no log line (§1.1). The meta `checksum` is the content fingerprint consumers should compare. Proposed additions to **W5.7** (producer guards): record whether the action columns were present in the upstream
   response (`actions_present` in meta, or refuse the mint), log the zero-fill, and document that the id is request-addressed. The 2026-10-03 Scenario-B mint is the reproduction; why that fetch lacked the columns 85 s after a complete one is not known.
5. **Provenance in the driver's manifest** (F-D7's family, juniper-ml): `git: {}` and stale dist versions for editable installs mean the checkout that ran is unrecorded; W1.9 (launch settings) should record the checkout SHAs of the editable packages too.

### 3.3 W1.1(a) — the documented recurrence bundle

Dataset half: `fundamentals_fill: drop`, `normalize_features: false`, `regression_target: log_return`, explicit `symbols`. The `false` is this note's finding (§2.3(b)): producer normalisation gives no reason to be turned on for the recurrence path and the R4 note rules it out as a CV control.
Model half: `readout: rff`, `ridge: 1.0`, `rff_features: 256`, `rff_gamma: median`, `d: 16`. `1.0` rather than `gcv` because GCV selects the null model on this rung (§2.3) while 1.0 retains a fit (train r² 0.12–0.18); v1.0.0's "(or `gcv` once W5.9 lands)" is withdrawn — W5.9 cannot change that answer.
Two caveats a reader of the bundle needs. The measurements in this note were made at **`fundamentals_fill: nan`** (the generator default, which the E-H selector does not override), not at `drop`; because the fill is hashed into the id, following the bundle mints a different `dataset_id`. For AAPL 2015–2022 every array is finite, so `drop` has nothing to drop and the rows are expected to be identical — **untested**. And reproducing −0.1153 needs the CV and seed parameters as well: `n_folds: 5`, `scheme:
expanding`, `embargo: 2`, `lookback: 64`, dataset `seed: 20260807`, and the model's `random_seed` left at its default 0 (the route does not expose it).

### 3.4 R5 recommendation — the acceptance band for the E-H equities row

The band's purpose is to catch the two defect classes this note measured, not to assert skill:

| key | min | max | mode | why |
| --- | --- | --- | --- | --- |
| `cv_r2` | **−1.0** | **+0.5** | **`gate`** | The sane class (five configurations) sits in [−0.28, +0.00] per fold and [−0.142, −0.013] in aggregate; the nearest non-sane aggregate is −4.52 (linear / 1.0 / scaled), 4.5× below the bound, and the sane cells are 7× above it; the `ridge = 0` class is three or more orders of magnitude below. The bound survives six RFF seeds (worst −0.252), embargo 64 (−0.153), `test` excluded (−0.101) and both 2026-10-03 mints. The upper bound is a **prior**, not a measured detector: no cell approaches +0.5, and the one leak the matrix contains (pooled-train scaling) did not raise the number (−0.142 vs −0.115, within seed noise); a target-into-features leak would read ≈ 1.0 and be caught, a milder look-ahead would not. |
| `cv_r2_std` | 0.0 | **0.5** | **`gate`** | The aggregate is the plain mean of five fold r², so one catastrophic fold is diluted 5× and a single fold down to −4.6 would pass the `cv_r2` gate. The existing headline `cv_r2_std` closes that window: sane cells 0.018–0.074; linear / 1.0 / scaled (one fold at −22) 8.75; a one-outlier model gives std = 0.4·abs(x), so 0.5 fails any single fold below −1.25 with a 7× margin over the sane maximum. |

The `train_r2 ≤ 0.9` report-mode row of v1.0.0 is **withdrawn**: it keyed on the W0.4 headline `train_r2`, which is the train phase's in-sample r² at n = 1,346; the matrix's nearest proxy (fold 4, n = 1,413) puts every defective configuration's train r² at or below 0.229, so the row could never fire, and even on the n ≈ p fold 0 it misses the audited configuration (0.453). The right overfit tell, once W5.10 exists, is the per-fold train r² of fold 0.

`gate` is recommended for both keys. v1.0.0 argued it from R6; that was a category error — a `cv_r2` of −20,345 is a number the suite produced correctly, a science result in R6's own taxonomy, and R6's last clause grants permission rather than reasoning. The case is structural: the E-H configuration's predictions are bounded (prediction std ≤ 0.51× target in every sane fold; `_phi` is a cosine), and the row can breach the bound in three ways — a configuration change, a code change, or an upstream data
change served under the same id (§1.1, F-P8) — each of which a gate should surface; W5.7's `actions_present` guard is what will distinguish the third from the first two. The original R-6 made equities rows informational because of network and API-limit failures, and since W0.3 merged a cell that produces no manifest is `failed` and the suite exits non-zero on any failed / degraded cell regardless of this band. If the owner prefers to keep R-6's framing, `report` is the fallback with no change to the
numbers.
The band is **row-scoped** to the E-H equities row (the irregular-sine control's `cv_r2 0.975` would fail +0.5 under a suite-level band); W5.4's schema must carry a list of bands per row. It is measured on one ticker and one window (§2.5), on a population that includes the `test` partition; W5.4 should carry it as the E-H row's band, and W5.2's train + val, entity-grouped population gets its own measurement before it gets a band.

### 3.5 What this note changes in the plan (v1.3.0 → v1.4.0)

- F-SCI1: cause **resolved** → candidate (a) as the amplifier of extrapolation under drift; (b) refuted as the lever (its drift mechanism is real); (c) refuted for the fold-mismatch hypothesis (theta never varied); (d) not implicated, on the control and the in-support result. The −18,081 is a service-defaults artefact — and was solved on a different mint (§1.1). §3.9's "what the measurement does and does not say" is superseded by §2 here.
- W0.8, W0.9: **Done**; M0 now waits only on the P0 code merges.
- W1.1(a): `normalize_features: false`; the bundle gains its model-side half and the §3.3 caveats.
- W5.1: content fixed by the verdict (go); this note is its §1–§2; what remains of W5.1 is round 2 of the review and the R5 ruling.
- F-P8: Minor → **Major** (DATA), re-worded (§3.2 item 4); W5.7 gains the producer guard.
- New or rewritten: W5.8 (§3.2 item 1 — measured options, (B)), W5.9 (reporting, not grid extension), W5.10 (per-fold diagnostics in the response), W5.11 (default readout, the (A) option), the R5 recommendation (§3.4), and a W1.9 provenance addition.
- **Consequences the plan must carry** (round 2): (a) release placement — W5.8 / W5.10 are "Changed" entries; recurrence 0.6.0 is W1.13's P1 publication while W5.8 is P5 after M1, so one of them moves, and the model halves are a minor (0.4.0 or 0.5.0), not "0.4.x"; (b) W5.2 excludes `test` from the CV pool for every row, so the E-H row's population becomes 1,522 windows and the band is re-measured there before W5.4 encodes it (the numbers are F10); (c) W5.3's `test_r2` is not held out until W5.2 lands — a
  W5.2 → W5.3 edge; (d) the plan paragraphs that carried v1.0.0's withdrawn claims (§3.9's "resolved" paragraph, W1.1's Details, the F-P8 row, W5.9's row) are rewritten at v1.4.0.

---

## 4. What the evidence cannot support

- Any statement about multi-ticker artifacts, other `d`, the MLP rung, other tickers, other date ranges or other dataset seeds (§2.5).
- That the E-H configuration has skill: r² ≈ −0.1 is "no worse than the mean by much", not "better than the mean", in-support as well as out.
- A separation of the readout from the drift as **the** cause: no matrix cell is drift-free; the embargoed in-era block (§2.3, F15) is one block of one artifact, folds 0 and 4 have no in-era counterpart, and the shuffled split carries near-duplicate rows.
- That theta is or is not a lever: it took one value (91.0) in every cell.
- The sane number's precision beyond the RFF seed spread (≈ 0.05 in aggregate), or beyond the ≈ 0.04 the 61/64-day boundary overlap adds.
- What the `test` partition would say on its own: fold 4 is `val` + `test`, and the band was selected on that population.
- What the Scenario-B mint's upstream response looked like, or why yfinance omitted the action columns for one fetch and not for another 85 s earlier.
- That the repaired env stays repaired, or that the service-core half is harmless to apply: W0.2's preflight is the control for the former; the latter waits on the `:8202` listener (§0.3).
- The recurrence working tree's state on 2026-10-03 (the reflog places `be081fae` on `main` from 2026-10-02; the tree is clean today).

---

## Change Log

| Date | Version | Changes | Author |
| --- | --- | --- | --- |
| 2026-10-04 | 1.0.0 | W0.8 replay (§1), W0.9 matrix and conditioning (§2), GO verdict and R5 recommendation (§3); not yet consensus-reviewed | Paul Calnon |
| 2026-10-05 | 1.1.2 | Round-3 check (Lane A1-r3: 42 confirmed / 1 partial / 1 refuted over 45): the "3.8e-4" lower bound on last-step feature scale was a float32 artefact of the constant `cost_basis` column (0.0 in float64; next smallest 0.022) and is corrected; "rff/gcv seed-stable" scoped to the three seeds measured. No disposition changed; the review terminates. | Paul Calnon |
| 2026-10-05 | 1.1.1 | Round-2 consensus corrections (Lane A1-r2, Lane B1-r2; record §5): every number the fix pass had quoted without an artifact now has one (`reconciler-rederive-b1r2.json` F10–F16) and the two −0.101 values are distinguished; the cause statement becomes the conjunction with the default as the actionable lever, with an embargoed in-era control (F15) replacing the leaky shuffled split as the in-support evidence, and (b) stays withdrawn; (d) scoped to in-support / untested under drift; `cost_basis` is an exactly-constant feature (v1.1.0 had inverted the correction); W5.8's option table gains the rff/gcv row and the seed-mean, (A) is filed as W5.11; the "only way to breach" and "12 fold-stds" sentences replaced; §3.5 lists the plan consequences; minors (leak sentence, ≤ 0.04 within noise, t+4, double negative, 0.229 source, seed-0 scope of the prediction bound, fold-0 GCV "effectively null") | Paul Calnon |
| 2026-10-05 | 1.1.0 | Round-1 consensus corrections (record: `JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md`): the audited digits were solved on a second mint of the same id (§1.1, F-P8 re-filed Major); digits reproducible, rounding story withdrawn (§1.3, §2.4); cause = extrapolation under drift with ridge 0 as amplifier, (d) argued from the control, standardisation necessary not sufficient (§2.3); amplification column and rank-deficiency re-described, constant columns corrected (§2.4); RFF seed, `test`-in-fold-4, boundary overlap, 12 distinct cells (§2.1, §2.5); W5.8 options measured and re-ranked, W5.9 → reporting, W5.10 proposed (§3.2); bundle caveats (§3.3); band: `cv_r2_std` added, `train_r2` withdrawn, structural justification (§3.4); arithmetic and unit fixes (2.1e8×, e^9.8, −0.015, 0.013) | Paul Calnon |
