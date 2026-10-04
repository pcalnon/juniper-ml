# Juniper-Recurrence × Equities — Cross-Validation Blow-up Investigation (W0.8 replay, W0.9 matrix, P5 go/no-go)

- **Project**: Juniper — juniper-recurrence (with juniper-data, juniper-recurrence-model, juniper-model-core, juniper-ml experiment stack)
- **Author**: Paul Calnon
- **Date**: 2026-10-04
- **Version**: 1.0.0
- **Status**: MEASURED — §1 (W0.8) and §2 (W0.9) complete; **verdict: GO** (§3). This note is the W5.1 cause-investigation note the plan asked for and ends in an R5 recommendation (§3.4). It has **not yet been reviewed under the consensus procedure**, which the plan requires before R5 is ruled.
- **Plan**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md) (v1.2.0 → v1.3.0 with this note), work items W0.8, W0.9, W5.1; finding F-SCI1; rulings R5, R4 note
- **Consensus record of the plan**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md) §8 ("what the evidence cannot support" — this note supplies the two measurements it named)
- **Instruments**: `util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py` (`replay` = §1, `matrix` = §2.1–2.3), `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py` (§2.4)
- **Evidence**: `reports/2026-10-04_recurrence-equities-cv-matrix/` — `00-dataset-create.json`, `01-recurrence-health.json`, `10-crossval-eh-rff.json`, `10-crossval-service-defaults.json`, `20-matrix-datasets.json`, `21-matrix-cells.json`, `22-matrix-table.md`, `23-linear-conditioning.json`

---

## 0. The question, and the instrument

The audit measured aggregate eval r² = −18,081 on `POST /v1/crossval` for the E-H dataset selector and could not isolate the cause, because the request that produced it carried no model parameters: the service defaults applied (`readout=linear`, `ridge=0.0`), not the E-H suite's own configuration (RFF readout, `ridge=1.0`, 256 features, median gamma).
Plan §3.9 therefore listed four candidates and withdrew every hypothesis of record; W0.8 was to replay the real configuration and W0.9 to widen it to a controlled matrix and issue the go/no-go for P5.

### 0.1 Stack as served

| Component | Value |
| --- | --- |
| Launch | `util/experiment_stack.bash --up --recurrence --config juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` — run `20261004T210331Z-491a`, data `127.0.0.1:8110`, recurrence `127.0.0.1:8260`; the E-H base YAML staged so the service block matches the suite (`default_d: 16`, `default_theta: null`, `default_ridge: 0.0`, rate limit off) |
| juniper-data | `JuniperData` env, editable checkout `29be6d35` (`main`); `equities_seq` generator `6.0.0`; per-run storage and per-run (cold) equities cache |
| juniper-recurrence | `JuniperCascor1` env (Python 3.14.7), app 0.5.0 editable at `be081fae`; **`juniper-recurrence-model` 0.3.0 editable** (W0.1 model half applied 2026-10-04 — the audit's 0.1.5 wheel is gone); `juniper-service-core` dist 0.5.0 / module 0.4.0 (W0.1 service-core half deferred, §0.3); `juniper-model-core` 0.2.0; `juniper-data-client` 0.5.0 editable; numpy 2.5.3 |
| Dataset | `equities_seq-6.0.0-15505731cba5b86d` — AAPL 2015-01-01 → 2022-01-01, `lookback 64`, `regression_target log_return`, `seed 20260807`, all other params at the generator's defaults (`fundamentals_fill: nan`, `normalize_features: false`); `full` view 1,698 windows (1,346 / 176 / 176 partitions), 64 × 15 features, `sum(dt)` per window 88–97 calendar days (mean 91.3, std 1.7), target mean 0.00101 / std 0.01835 |
| Folds | model-core `walk_forward_folds(1698, n_folds=5, scheme="expanding", embargo=2)` → `fold_size = 283`; train sizes 281 / 564 / 847 / 1,130 / 1,413, eval 283 each (the plan's derived 281–1,413 is confirmed by construction) |

### 0.2 Why the in-process matrix is the service's own path

The HTTP route cannot return the resolved theta, the selected ridge, the RFF gamma, or anything about the memory states (F-S7: the start log prints `theta=None`).
§2 therefore fits in-process through the same objects the route uses — `juniper_recurrence._readout.build_lmu_regressor` → `LMURegressor.fit` / `predict` with the `SequenceData.fit_kwargs()` slices, over the same `walk_forward_folds`, with `pass_eval_as_val=False` as `cross_validate` does — and reads the diagnostics off the fitted model.
Fidelity was checked, not assumed: the in-process cell matching the service defaults reproduces the HTTP control to every printed digit (aggregate −20,344.64; fold 0 −93,606.23), and the in-process E-H cell reproduces the HTTP replay (−0.115).

### 0.3 What was not repaired

The service-core half of W0.1 (editable 0.7.0 from the juniper-ml checkout) was **deferred**: a live cascor listener on `:8202`, part of the canopy E2E stack (data `:8101`, canopy `:8051`, all up since 2026-09-22), imports `juniper_service_core` from the same env, and replacing a package under a running service is the owner's call.
It does not touch the numbers here (service-core is the FastAPI tier; crossval numerics live in the model and model-core), and the recipe with the deferral is recorded in `juniper-recurrence/AGENTS.md` (juniper-recurrence#189).

---

## 1. W0.8 — the E-H configuration, replayed on the frozen artifact

### 1.1 The artifact is the audit's artifact

`POST /v1/datasets` with the E-H params resolved to **`equities_seq-6.0.0-15505731cba5b86d`**, the id the audit measured, in 2.5 s from a cold per-run cache (one ticker). Its arrays were diffed key by key against the copy the audit archived (`.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/`): **all 28 keys byte-identical** (`X_*`, `y_*`, `y_reg_*`, `dt_*`, `date_*`, `target_dt_*`, `window_end_date_*`, `ticker_code_*`, `observed_mask_*`, `ticker_vocab`).

The meta `checksum` nevertheless differs (`037baab7…` on 2026-10-03, `c02004e1…` on 2026-10-04): it fingerprints the NPZ container, whose zip entries carry write timestamps, not the arrays. Recorded in the plan as **F-P8** (Minor). The first reading of that difference — "the equities data drifted under the same id" — was wrong, and it would have mis-explained §1.3.

### 1.2 The E-H request body and its result

The body the suite sends (`run_experiment.py::_lmu_hyperparams` drops the YAML's `theta: null`, so the service resolves theta from the data):

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
| **aggregate** | | | | **−0.1153** (std 0.0735) | 0.01857 | 0.01337 |

Per-fold eval RMSE (0.012–0.029) sits at the target's own per-fold standard deviation (0.011–0.028): the model predicts a little worse than the fold mean, which is what "r² ≈ 0 at the efficient-market ceiling" looks like. Resolved internals (from the in-process reproduction, §2): theta 91.0 in every fold, gamma 0.0508 / 0.0512 / 0.0499 / 0.0499 / 0.0553, ridge 1.0 as requested.

**The E-H configuration does not blow up.** This is the number the E-H suite comment expects ("r2 ≈ 0 … NOT negative blowups").

### 1.3 The control — service defaults on the same artifact, same day

The same body with no model parameters (`readout=linear`, `ridge=0.0`, d 16, data-driven theta) → HTTP 200 in 10.9 s (`10-crossval-service-defaults.json`):

| fold | train r² | eval r² (2026-10-04) | eval r² (audit, 2026-10-03) | eval RMSE |
| --- | --- | --- | --- | --- |
| 0 | +0.4532 | **−93,606** | −83,452 | 3.464 |
| 1 | +0.3224 | **−798.5** | −815 | 0.381 |
| 2 | +0.2487 | **−3.70** | −3.7 | 0.043 |
| 3 | +0.1836 | **−75.6** | −78 | 0.242 |
| 4 | +0.1353 | **−7,239** | −6,059 | 1.353 |
| **aggregate** | | **−20,345** (std 36,731) | −18,081 | 1.097 |

Same arrays (§1.1), same model code (`juniper-recurrence-model` at `be081fae` both days — the audit shadowed the checkout), same machine — and the fold-0 number moved by 12 % and fold 4 by 19 %. A solve whose out-of-sample answer changes while nothing it reads has changed is being decided by rounding; §2.4 measures why. The audited class ("catastrophic") reproduces; the audited digits do not, and should not be quoted as if they were a property of the data.

**W0.1 acceptance, in passing**: both requests returned 200 with no `PYTHONPATH` on a decision-11 artifact — the request that returned 422 `missing required key 'X_full'` in the audit. The model half of the env repair is verified.

### 1.4 The suite path records the same number (Scenario A re-run, after W0.3 / W0.4 merged)

The audit's Scenario A — `run_suite.py --suite p4/e-h-recurrence-real-data.yaml` through the launcher — was re-run on 2026-10-04 from juniper-ml `main` at `3420a1a5` (W0.3 / W0.4 merged in juniper-ml#2145) against the model-repaired env (`reports/2026-10-04_recurrence-equities-cv-matrix/scenario-a-rerun/`).
Where the audit recorded the equities cell as `succeeded` with `exit_code: 1`, `acceptance.ok: false`, `metrics: {}` and a 422'd crossval, the registry now reads: `outcome: succeeded`, `exit_code: 0`, `phases: {train: ok, predict: ok, crossval: ok, save_model: ok}`, `metrics: {train_r2: 0.1163, cv_r2: -0.1153, cv_r2_std: 0.0735, n_windows: 1346}`.
`REPORT.md` says `Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run.` and carries the four columns. The control cell (irregular sine) reports `cv_r2 0.975`.
The `cv_r2` is the §1.2 aggregate to four decimals — the suite's E-H row, driven as an operator drives it, now produces the sane number this note measured by hand, and the four F-D1 / F-D2 symptoms are gone from the same artifact that showed them.
(From a `.claude/worktrees/` checkout the suite needs `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`, because its `base_config` walks to a sibling repo; the loader documents the override.)

---

## 2. W0.9 — the controlled matrix

### 2.1 Design

{readout `linear` / `rff`} × {`ridge` 0.0 / 1.0 / `gcv`} × {producer `normalize_features` off / on} × {theta fold-resolved (`None`) / configured (91.0, the full-set median `sum(dt)`)} = 24 cells, 5 expanding folds each, one ticker, `d = 16`, RFF at 256 features and median gamma, `default_ridge = 0.0` as the service.
The normalised artifact is `equities_seq-6.0.0-fa3aae11ac374c94` (same rows; feature columns z-scored by the producer on the pooled `train` partition — the R4 note's leakage, kept deliberately so the cell measures the producer knob as shipped).
Per fold the script records train/eval metrics, resolved theta, selected ridge and gamma, the fold's median `sum(dt)`, the eval memory block's z-range against the train fold's column statistics, the raw last-step feature z-range, and prediction vs target ranges. Fit time ≈ 30 s per cell; total ≈ 13 min.

### 2.2 Results

Eval r² per fold (0…4) and aggregate; `train r²` fold 0 → 4; `ridge` is the resolved value (GCV writes back the selected λ). Theta resolved to **91.0 in every fold of every cell**, so each configured row equals its fold-resolved twin and the table shows the fold-resolved rows only (`22-matrix-table.md` has all 24).

| readout | ridge | normalize | eval r² per fold | **agg** | eval RMSE | train r² (f0 → f4) | ridge / gamma resolved | eval memory max abs z per fold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear | 0.0 | off | −93,606 / −798 / −3.70 / −75.6 / −7,239 | **−20,345** | 1.097 | 0.453 → 0.135 | 0 | 24 / 23 / 8 / 199 / 44 |
| linear | 1.0 | off | −6,688 / −147 / −5.56 / −121 / −3,356 | **−2,064** | 0.473 | 0.425 → 0.168 | 1 | same |
| linear | gcv | off | −218 / −2.66 / −2.04 / −36.6 / −976 | **−247** | 0.179 | 0.317 → 0.088 | 1000 / 1000 / 85.5 / 60.2 / 1000 | same |
| rff | 0.0 | off | −9,869 / −50.9 / −3.03 / −1.96 / −6.35 | **−1,986** | 0.270 | 0.959 → 0.221 | 0 / γ 0.050–0.055 | same |
| **rff** | **1.0** | **off** | **−0.08 / −0.05 / −0.10 / −0.09 / −0.26** | **−0.115** | **0.0186** | 0.184 → 0.124 | 1 / γ 0.050–0.055 | same |
| rff | gcv | off | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 | **−0.014** | 0.0177 | 0.002 → 0.001 | 1000 / 495 / 60.2 / 1000 / 1000 | same |
| linear | 0.0 | on | −2.1e13 / −8.5e6 / −22.2 / −207 / −12,319 | **−4.3e12** | 10,495 | 0.907 → 0.212 | 0 | 24 / 23 / 11 / 337 / 50 |
| linear | 1.0 | on | −0.27 / −0.09 / −0.11 / −0.13 / −22.0 | **−4.52** | 0.0306 | 0.140 → 0.085 | 1 | same |
| linear | gcv | on | −0.05 / −0.01 / −0.00 / −0.01 / −0.01 | **−0.015** | 0.0177 | 0.002 → 0.003 | 1000 × 5 | same |
| rff | 0.0 | on | −15,904 / −62.5 / −3.42 / −3.24 / −10.0 | **−3,197** | 0.337 | 0.956 → 0.229 | 0 / γ 0.048–0.061 | same |
| **rff** | **1.0** | **on** | **−0.14 / −0.06 / −0.12 / −0.11 / −0.28** | **−0.142** | **0.0188** | 0.186 → 0.119 | 1 / γ 0.048–0.061 | same |
| rff | gcv | on | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 | **−0.013** | 0.0177 | 0.002 → 0.001 | 1000 / 1000 / 495 / 1000 / 1000 | same |

Prediction scale, the quantity r² hides (eval prediction std per fold vs target std 0.011 / 0.014 / 0.020 / 0.028 / 0.016):

| cell | eval prediction std per fold | max abs prediction |
| --- | --- | --- |
| linear / 0.0 / off | 3.46 / 0.21 / 0.030 / 0.24 / 0.43 | 9.81 |
| linear / 0.0 / on | 28,000 / 22 / 0.083 / 0.40 / 0.86 | 137,000 |
| linear / 1.0 / on | 0.0049 / 0.0028 / 0.0046 / 0.0068 / 0.031 | 0.092 |
| rff / 0.0 / off | 1.05 / 0.093 / 0.033 / 0.034 / 0.037 | 4.21 |
| **rff / 1.0 / off** | 0.0043 / 0.0040 / 0.0043 / 0.0062 / 0.0076 | 0.021 |
| rff / gcv / off | 0.0002 / 0.0004 / 0.0008 / 0.0001 / 0.0002 | 0.0036 |

A daily log return has a standard deviation of about 0.018; the service-default fit predicts values up to 9.8 (a 980 % one-day move) and the normalised ridge-0 fit up to 137,000.

### 2.3 Per-candidate verdicts

- **(c) theta — refuted.** `sum(dt)` over the full set is 88–97 calendar days (std 1.7) and its median is 91.0 in every expanding train fold, so the data-driven theta equals the configured one everywhere; the 12 configured cells are identical to their fold-resolved twins to every printed digit. Theta is not a lever on this artifact. F-S7 (theta never logged) stands as an observability defect, not as a cause.
- **(b) unnormalised features — refuted as the lever.** Producer normalisation does not rescue the unregularised solve (it makes it four hundred million times worse: −20,345 → −4.3e12), does not make linear ridge 1.0 sane (fold 4 −22), and is not needed by the sane configuration (RFF ridge 1.0: −0.115 raw vs −0.142 normalised).
  The mechanism is in §2.4: normalising raises the design's numerical rank from 113–161 to 210–226, which exposes more tiny-but-nonzero singular values to the pseudo-inverse. Consequence for **W1.1(a)**: the documented recurrence bundle keeps `normalize_features: false`; producer normalisation is a convenience, not a CV control (R4 note), and this measurement gives no reason to turn it on.
- **(a) unregularised linear readout extrapolating — confirmed as the cause of the audited number.** Every `ridge = 0.0` cell is catastrophic in both readouts and both normalisations (−20,345 / −1,986 / −4.3e12 / −3,197).
  The linear rung with `ridge = 1.0` on the raw memory block is still catastrophic (−2,064) because that rung does not standardise: the memory columns inherit the raw feature scales (last-step feature std from 3.8e-4 to 7.9e11 — `market_cap`, `total_shares`, `volume`), against which a penalty of 1.0 is nothing.
  The RFF rung standardises the memory block per fold, train-only (`readouts.py::_standardize_fit`), so its `ridge = 1.0` acts on unit-scale features and the cos features are bounded; it is sane. §2.4 quantifies the conditioning that turns "unregularised" into "catastrophic".
- **(d) per-fold standardisation on a non-stationary memory — not implicated.** The only rung that standardises per fold is the one that works.
  The eval memory states do leave the train fold's support in every fold (max |z| 8–199 raw, 11–337 normalised; 28–100 % of eval rows have at least one column beyond 5σ; raw last-step feature max |z| 10–58), i.e. the drift is real and intrinsic to price-level inputs — but with ridge ≥ 1 on standardised features the RFF readout's bounded features saturate and its predictions shrink toward the mean (prediction std 0.004–0.008 against a target std of 0.011–0.028) instead of exploding.
  Standardisation is part of the remedy, not the defect.
- **GCV — a note, not a candidate.** On both rungs GCV picks a very large penalty and the fit collapses to the fold mean (train r² ≈ 0.002, eval r² −0.01): the honest "no linear signal at this horizon" answer, and the one configuration whose eval r² is nearest zero. But in **15 of 20** GCV folds the selected λ is `1000.0`, the last point of the grid (`_GCV_GRID` in `juniper_recurrence_model/readouts.py`), so the GCV-optimal penalty is unknown — it lies at or beyond the grid's edge.

### 2.4 Conditioning of the linear design (why ridge 0 is catastrophic, and why the digits are not reproducible)

`util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py` rebuilds exactly what `LinearReadout` solves — `[ memory block (15 × 16 = 240 cols) | target_dt | 1 ]`, 242 columns — per fold, and takes its SVD (`23-linear-conditioning.json`):

| artifact | fold | n_train | numerical rank (eps) | σ_max / σ_min | ‖coef‖₂ (min-norm) | weak-direction amplification, p99 train → p99 eval |
| --- | --- | --- | --- | --- | --- | --- |
| raw | 0 | 281 | **113** / 242 | 8.6e32 | 0.16 | 0.33 → **26,500** |
| raw | 1 | 564 | 149 | 2.4e31 | 0.10 | 10.5 → 2,540 |
| raw | 2 | 847 | 159 | 2.5e31 | 0.062 | 0.056 → 0.87 |
| raw | 3 | 1,130 | 160 | 1.3e31 | 0.047 | 6e-14 → 454 |
| raw | 4 | 1,413 | 161 | 1.5e22 | 0.026 | 2e-5 → 0.0028 |
| normalised | 0 | 281 | **210** / 242 | 1.7e24 | **6.6e6** | 6e-7 → 0.099 |
| normalised | 3 | 1,130 | 210 | 1.2e21 | 44 | 1.8e-4 → **4.5e13** |
| normalised | 4 | 1,413 | 226 | 1.1e20 | 20.6 | 7e-4 → 0.11 |

("weak-direction amplification" = |row · vᵢ| / σᵢ over the ten smallest singular directions of the train design — what the min-norm solution does to a row's component along them. It is a partial view: fold 4 raw blows up along directions outside the last ten, and the table's job is to show the class, not to rank folds.)

The design is **rank-deficient by a third to a half** on the raw artifact (near-constant columns — `cost_basis`, `total_shares` for a single ticker — plus the Legendre memory of slowly varying price levels) and the 2-norm condition number is 1e22–1e32. The min-norm `lstsq` solution is well behaved in-sample (small ‖coef‖, train r² 0.14–0.45) because the training rows have, by construction, no component along the null directions.
Eval rows do — the drift of §2.3(d) — and the pseudo-inverse multiplies those components by 1/σ for every σ just above the rank cutoff. That is the −93,606. It is also why the digits moved between 2026-10-03 and 2026-10-04 on identical inputs: at cond 1e32 the solution in the near-null subspace is determined by floating-point rounding (BLAS reduction order, thread count), so the number is reproducible only to its order of magnitude.
The audited −18,081 and today's −20,345 are the same measurement.

### 2.5 Fidelity and limits of the instrument

- In-process vs HTTP: identical to every printed digit on the two configurations both paths ran (§0.2). The in-process diagnostics read private attributes (`_memory_block`, `_readout`, `_side_channel`); a future refactor that renames them breaks the script, not the finding.
- One ticker (AAPL), one window (2015–2022), one seed, five expanding folds, `d = 16`. Nothing here speaks to multi-ticker folds (F-P7 / W5.2), to the `test` partition (W5.3), to other `d`, or to the MLP rung.
- "Sane" means "not a defect": an aggregate r² of −0.12 on next-day log returns says the model has **no demonstrated skill** at this horizon with these features. That is the efficient-market ceiling the suite comment anticipates, and it is a scientific result to report, not a success to celebrate.

---

## 3. Verdict and consequences

### 3.1 Go / no-go for P5: **GO**

The E-H configuration (RFF, ridge 1.0, 256 features, median gamma, d 16, data-driven theta) produces a sane out-of-sample number on the frozen artifact (§1.2), reproduced in-process (§2.2), stable across producer normalisation (−0.115 / −0.142). The −18,081 is a property of the **service defaults** — an unregularised linear readout on a rank-deficient, unstandardised memory design (§2.4) — not of the model, the data contract, theta or the `dt` handling.

Under the plan's gating paragraph this makes **W5.1 a tuning-and-documentation task**, not a model/CV defect investigation; W5.2 (entity-grouped chronological folds) proceeds independently as planned; P5's remaining content is as written.

### 3.2 What must change regardless of the verdict (recommendations for the owner; proposed as plan items)

1. **The service default `readout=linear`, `ridge=0.0` must not be used for equities, or for any non-stationary real-data input.** It is the configuration a bare `POST /v1/crossval` or `POST /v1/train` gets, and it is the one canopy's registry seed and any hand-written request fall into.
   Options, in order of preference: (i) change `Settings.default_ridge` from `0.0` to `"gcv"` (the linear rung then shrinks instead of exploding; the irregular-sine YAML pins `0.0` explicitly, so the reference experiment is unaffected); (ii) give the linear rung the per-fold standardisation the RFF rung already has, so a float ridge means the same thing on both rungs; (iii) at minimum, document the hazard on the route and in the registry seed.
   (i) is a behaviour change for callers that relied on the default — a pre-1.0 "Changed" entry in recurrence 0.6.0, candidate for the same ruling pattern as R8. **Proposed as W5.8** (recurrence + model); needs owner acceptance.
2. **Extend `_GCV_GRID` above 1000** or make the ceiling a logged warning: 15 of 20 GCV folds selected the grid's last point, so "GCV-selected" currently means "the largest value we allowed". **Proposed as W5.9** (model); S.
3. **Log the resolved theta, gamma and ridge per fold** (F-S7, already W2.4's remit): every number in §2.3 that decided a candidate came from an in-process read the service cannot provide today.
4. **The meta `checksum` is not a content fingerprint** (F-P8): consumers that want to prove two artifacts are the same must compare arrays. juniper-data may hash the arrays instead, or document the field.

### 3.3 W1.1(a) — the documented recurrence bundle

`normalize_features: false`. The measurement gives no reason to turn producer normalisation on for the recurrence path (−0.115 raw vs −0.142 normalised with the sane configuration; harmful with the unsafe one), and the R4 note already rules it out as a CV control.
The bundle's other values are unchanged from the plan: `fundamentals_fill: drop`, `regression_target: log_return`, explicit `symbols`, plus — **new, from this note** — the model side of the bundle must name the rung: `readout: rff`, `ridge: 1.0` (or `gcv` once W5.9 lands), `rff_features: 256`, `rff_gamma: median`.

### 3.4 R5 recommendation — the acceptance band for the E-H equities row

The band's purpose is to catch the two defect classes this note measured, not to assert skill:

| key | min | max | mode | why |
| --- | --- | --- | --- | --- |
| `cv_r2` | **−1.0** | **+0.5** | **`gate`** | The sane class sits in [−0.26, +0.00] per fold and −0.115 aggregate across the four sane cells; the defect class is below −1 by three or more orders of magnitude, so the lower bound separates them with no tuning. An aggregate above +0.5 on next-day log returns would indicate leakage or a scoring error, not skill, so the upper bound is a defect detector too. |
| `train_r2` | 0.0 | 0.9 | `report` | Train r² ≥ 0.9 marked every interpolating fold-0 fit (ridge 0, RFF: 0.959; linear normalised: 0.907) — a cheap overfit tell worth flagging, not failing. |

`gate` is recommended for `cv_r2` despite the earlier R-6 "equities rows are informational": the band encodes no scientific claim, only the two failure classes, and R6's reasoning (a defect in the suite's own output should fail the suite) applies to them. If the owner prefers to keep R-6's framing, `report` is the fallback with no change to the numbers.
The band is measured on one ticker and one window (§2.5); W5.4 should carry it as the E-H row's band and W5.2's multi-ticker row gets its own measurement before it gets a band.

### 3.5 What this note changes in the plan (v1.3.0)

- F-SCI1: cause **resolved** → candidate (a), with (b) and (c) refuted and (d) not implicated; the −18,081 is a service-defaults artefact. §3.9's "what the measurement does and does not say" is superseded by §2 here.
- W0.8, W0.9: **Done**; M0 now waits only on the P0 code merges.
- W1.1(a): `normalize_features: false`; the bundle gains its model-side half (§3.3).
- W5.1: content fixed by the verdict (go); this note is its §1–§2; what remains of W5.1 is the consensus review and the R5 ruling.
- New: F-P8 (Minor, DATA), proposed W5.8 and W5.9 (P5), R5 recommendation (§3.4).

---

## 4. What the evidence cannot support

- Any statement about multi-ticker artifacts, the `test` partition, other `d`, the MLP rung, other tickers, other date ranges or other seeds (§2.5).
- That the E-H configuration has skill: r² ≈ −0.1 is "no worse than the mean by much", not "better than the mean".
- That GCV's collapse to the mean is the GCV optimum: 15 of 20 selections sit at the grid ceiling.
- The exact audited digits (−18,081, −83,452): at condition number 1e32 they are rounding artefacts of an ill-posed solve and were not expected to reproduce (§2.4). The class reproduces.
- That the repaired env stays repaired, or that the service-core half is harmless to apply: W0.2's preflight is the control for the former; the latter waits on the `:8202` listener (§0.3).

---

## Change Log

| Date | Version | Changes | Author |
| --- | --- | --- | --- |
| 2026-10-04 | 1.0.0 | W0.8 replay (§1), W0.9 matrix and conditioning (§2), GO verdict and R5 recommendation (§3); not yet consensus-reviewed | Paul Calnon |
