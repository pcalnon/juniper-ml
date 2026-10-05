# Lane B2 — adversarial analysis review of `JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.0.0

- **Lens**: actionability, decision consequences, self-serving framing (procedure `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B — prompt to refute).
- **Scope**: the note's §2.2–§2.5, §3, §4; the plan `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.3.0 rows R5/R6 (:752-753), W5.4 (:476, :495-497), W5.8 (:480, :485-487), W5.9 (:481), W1.1 (:388, :405-408), W1.14 (:401), W2.4 (:429), F-P8 (:168); the R-6 origin (`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md:1241`); `util/experiments/suites/p4/e-h-recurrence-real-data.yaml`; `juniper_recurrence_model/readouts.py`; `juniper_recurrence/settings.py`, `_readout.py`, `routers/crossval.py`, `main.py`; canopy `src/main.py`, `src/model_registry.py`; `bench/run_benchmark.py`; `conf/experiments/irregular-sine-rff.yaml`; `util/experiments/run_suite.py`, `run_experiment.py`.
- **Raw measurements accepted as given.** Every number below is either read from `reports/2026-10-04_recurrence-equities-cv-matrix/*.json` or computed from the note's own frozen artifact (`juniper-ml/.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz`, which §1.1 certifies byte-identical to the matrix's input) in the `JuniperCascor1` interpreter through the same objects the instrument uses (`build_lmu_regressor` → `LMURegressor.fit` / `_memory_block` / `_side_channel`, model-core `walk_forward_folds`, `_regression_metrics`). **Fidelity of my harness**: rff/1.0/raw reproduces the note's five folds to four decimals (−0.0803 / −0.0500 / −0.1020 / −0.0856 / −0.2584) and linear/gcv/raw to the printed digits (−217.6 / −2.659 / −2.042 / −36.59 / −975.5). Reproduction code is in Appendix A (embedded rather than filed under `util/ad-hoc/` because this review is read-only outside this file).
- **Nothing was edited** except this file. No git commands were run.

## 0. Steelman of GO (accepted)

The E-H configuration's number is reproduced by three independent paths to four decimals (HTTP replay `10-crossval-eh-rff.json`, in-process `21-matrix-cells.json` cell 8, the Scenario-A suite re-run `scenario-a-rerun/registry.jsonl` `cv_r2 −0.11526`). The RFF rung is *structurally* bounded: in every sane fold its eval prediction std is ≤ 0.51× the target std (`folds[].pred_eval.std / target_eval.std`, max 0.512), and for near-uncorrelated predictions r² ≈ −(ratio)², so a fold below −1 would need predictions as wide as the target — twice anything measured. The audited catastrophe is fully explained by the conditioning table (§2.4) plus min-norm extrapolation, theta is provably not a lever, and nothing in 24 cells points at a model or `dt` defect. **GO is earned; so is the −1.0 lower bound.** What follows attacks the actions built on top of them.

## 1. Findings

Severity is about the *recommendation* the sentence carries. Every computation's output is quoted; anything I could not test is marked UNTESTED.

### F1 — FATAL — W5.8 option (i) is refuted by the note's own table and fails W5.8's acceptance

Quote (§3.2 item 1, note:195): *"Options, in order of preference: (i) change `Settings.default_ridge` from `0.0` to `"gcv"` (the linear rung then shrinks instead of exploding; …)"*

Evidence:
- The note's own row (§2.2, note:118; `21-matrix-cells.json` cell 4): **linear / gcv / off = −246.9** (folds −217.6 / −2.66 / −2.04 / −36.6 / −975.5). "Shrinks instead of exploding" is false on the raw artifact — the artifact the W1.1 bundle (`normalize_features: false`, note:203) and canopy's seed (`model_registry.py:332-336`, no `normalize_features`) both produce.
- The plan's W5.8 acceptance (plan:480): *"a bare `/v1/crossval` on the E-H artifact aggregates above −1"*. Option (i) yields −247 on exactly that artifact.
- Mechanism (code): `LinearReadout.fit` hands `_gcv_select` the **unscaled** `[M | target_dt]` (`readouts.py:186-187`); `_gcv_select` centres but never scales (`readouts.py:131-134`). With last-step feature stds from 3.8e-4 to 7.9e11 (`20-matrix-datasets.json` `X_last_step_full_per_feature_std`), a single λ cannot be "large" for `market_cap`'s directions and "small" for `cost_basis`'s at once.
- **Extending the grid does not rescue it** (my computation, Appendix A, "GCV curve beyond the 1000 ceiling: linear/raw"): with λ ∈ logspace(−6, 12) the argmin moves to 1.6e4 / 2.5e5 / 4.0e5 / 4.0e7 / 1e12 and the eval r² at the GCV-optimal λ is **−45.6 / −0.29 / −0.34 / −18.4 / −111.1 (mean ≈ −35)**. In all five folds GCV(λ→∞, null model) = 3.02e-4 … 3.55e-4 is *below* GCV at every finite grid point (min/null − 1 = +18 %, +7 %, +3 %, +4 %, +2 %): GCV's global optimum on unscaled features is the null model, unreachable by any grid short of λ ≫ σ_max² ≈ 1e23.

Change: (i) cannot be listed as a stand-alone option, let alone the preferred one. See F2 for what the measurement supports.

### F2 — FATAL — W5.8 option (ii) is unmeasured by the note, and when measured it also fails; the §2.3(d) attribution it rests on is wrong

Quotes: §3.2 item 1 (note:195): *"(ii) give the linear rung the per-fold standardisation the RFF rung already has, so a float ridge means the same thing on both rungs"*; §2.3(d) (note:150-152): *"The only rung that standardises per fold is the one that works. … Standardisation is part of the remedy, not the defect."*

Evidence: no cell in the matrix has a standardised linear rung; the closest proxy, producer-normalised linear/1.0, is −4.52 with fold 4 at −22.0 (cell 14). I measured option (ii) as written — `_standardize_fit` on the train-fold memory block, applied to eval, then the rung's own solvers (Appendix A, "W5.8 option (ii)"):

| standardised linear rung | eval r² per fold | agg | train r² | λ |
| --- | --- | --- | --- | --- |
| ridge 0 (min-norm) | −4.4e13 / −1.0e7 / −23.9 / −250 / −19,159 | **−8.8e12** | 0.93 → 0.24 | 0 |
| ridge 1.0 | −33.9 / −11.7 / −3.9 / −60.9 / −849 | **−191.9** | 0.40 → 0.18 | 1 |
| gcv, grid capped at 1000 | −0.24 / −0.20 / −0.06 / −0.20 / −0.28 | **−0.195** | 0.10 → 0.08 | 1000 ×5 (all at ceiling) |
| gcv, grid to 1e12 | −0.05 / −0.01 / −0.00 / −0.01 / −0.02 | **−0.019** | 0.00 / 0.00 / 0.00 / 0.004 / 0.038 | 1e12 / 1e12 / 1e12 / 1.3e5 / 6.3e3 |

So "a float ridge means the same thing on both rungs" is not what standardisation buys: the RFF rung is sane at ridge 1.0 because `cos(·)` **bounds** its features to ±√(2/256) (`readouts.py:298-303`), not because it standardises. The linear rung with the identical standardisation and the identical penalty is −192. The §2.3(d) inference from "the rung that standardises works" to "standardisation is the remedy" is a correlation across two rungs that differ in three things (scaling, boundedness, random projection), and the note did not separate them although its instrument could.

Consequences for W5.8: (i) alone −247, (ii) alone −192, **only (i)+(ii) together passes the plan's "> −1" acceptance — at −0.195 with λ pinned to the ceiling in all five folds, or −0.019 as the null model once the grid is extended.** The "and/or" in plan:480 must become "and", and the owner must be told that the only safe *linear* default the measurement supports is one that (nearly) abstains. The configuration that passes *and retains fit* is rff/1.0 (train r² 0.12–0.18) — i.e. the evidence supports changing the default **readout**, which the note never lists.

Change: rewrite §3.2(1) as — "(A) default readout `rff` with ridge 1.0 (measured −0.115, retains fit), or (B) `default_ridge="gcv"` **and** per-fold standardisation on the linear rung (measured −0.195 capped / −0.019 extended, a null-model default), with the selected λ and an at-ceiling/null-model flag returned in the response before either ships (see M7). (i) and (ii) alone are measured failures." Correct §2.3(d) to "not separable from boundedness on this matrix".

### F3 — MAJOR — the `train_r2 ≤ 0.9` report band can never fire on the key it names

Quote (§3.4, note:213): *"Train r² ≥ 0.9 marked every interpolating fold-0 fit (ridge 0, RFF: 0.959; linear normalised: 0.907) — a cheap overfit tell worth flagging, not failing."*

Evidence: the band keys on the W0.4 headline `train_r2`, which is `final_metrics.r2` of the **train phase** on the 1,346-window train partition (plan:358; `scenario-a-rerun/registry.jsonl`: `train_r2 0.1163, n_windows 1346`). The 0.959 / 0.907 are **fold-0 CV train fits at n = 281 against 242 design columns** — interpolation that exists only because n ≈ p. At the train phase's size, the matrix's nearest proxy is fold 4 (n = 1,413): over the seven defective configurations the train r² is 0.135 / 0.168 / 0.088 / 0.221 / 0.212 / 0.085 / 0.229 (`folds[4].train_metrics.r2`, cells 0/2/4/6/12/14/18) — **max 0.229**. Sensitivity on the headline key: 0 of 7. Even on fold 0 it is 3 of 7 (rff/0.0 ×2, linear/0.0/on) and misses the headline defect itself (linear/0.0/off: 0.453). The lower bound 0.0 is equally inert: the minimum train r² over all 120 fold-fits is 0.00075 (an unpenalised intercept makes a negative train r² essentially unreachable).

Change: drop the `train_r2` band. If an overfit tell is wanted, it has to key on a per-fold CV quantity W0.4 does not surface (`cv_train_r2_max`) and would still be a 43 % detector; not worth carrying.

### M1 — MAJOR — "three or more orders of magnitude" is false, and the aggregate band leaves a single-fold window open that an existing key would close

Quote (§3.4, note:212): *"the defect class is below −1 by three or more orders of magnitude, so the lower bound separates them with no tuning."*

Evidence (`21-matrix-cells.json`, all 24 cells; theta twins are identical so 12 distinct):

| aggregate | log10(−agg) | cells |
| --- | --- | --- |
| −4.29e12 | 12.6 | linear/0.0/on |
| −20,345 | 4.3 | linear/0.0/off |
| −3,197 / −2,064 / −1,986 | 3.3–3.5 | rff/0.0/on, linear/1.0/off, rff/0.0/off |
| −246.9 | **2.4** | linear/gcv/off |
| **−4.52** | **0.66** | linear/1.0/on (folds −0.27 / −0.09 / −0.11 / −0.13 / **−22.0**) |
| −0.142 / −0.115 / −0.0147 / −0.0145 / −0.0134 | in band | rff/1.0/on, rff/1.0/off, linear/gcv/on, rff/gcv/off, rff/gcv/on |

The nearest defect sits 4.5× below the bound and the nearest sane cell 7× above it. Two of six defective aggregates are not "three orders" below −1 (0.66 and 2.4). The band separates every measured cell — that conclusion stands — but by a factor of 4.5, and the sentence overstates the margin by ~2.5 orders.

The aggregate is the plain mean of fold r² (verified: `mean(folds) == eval_aggregate.r2` to 6 digits), so one catastrophic fold is diluted 5×. With the four other folds at the sane cells' measured values, **a single fold down to −4.6 passes the aggregate gate** (rff/1.0/off: other four sum −0.318 → threshold −4.68). linear/1.0/on fails only because its fold 4 is −22.

What closes it without touching W0.4: the existing headline `cv_r2_std`. Sane cells: 0.0179–0.0735; linear/1.0/on: **8.75**; one-outlier model (four folds ≈ 0, one at x): std = 0.4|x|, so `cv_r2_std ≤ 0.5` fails any single fold below −1.25 while keeping a 7× margin over the sane maximum. A per-fold minimum would need a new headline key (`cv_r2_min`); a prediction-scale bound (`pred_std/target_std ≤ 1`, sane max 0.51, nearest defect 1.93) is sharper still but the headline keys do not carry it.

Change: correct the sentence ("the nearest defect is 4.5× below the bound; the sane cells are 7× above it"); add `cv_r2_std ≤ 0.5` (gate or report) as the second band; replace "[−0.26, +0.00] per fold" with the measured [−0.2765, +0.0003] and delete "−0.115 aggregate across the four sane cells" (the four have four different aggregates, and there are five in-band cells — linear/gcv/on is omitted from the count).

### M2 — MAJOR — the argument for `mode: gate` is a category error; the right argument exists and is not made

Quote (§3.4, note:215): *"`gate` is recommended … despite the earlier R-6 "equities rows are informational": the band encodes no scientific claim, only the two failure classes, and R6's reasoning (a defect in the suite's own output should fail the suite) applies to them."*

Evidence:
- R6 (plan:753) draws its line between *"a phase that was asked for did not run — that is a suite defect, not a science result"* and `flagged` (report). A `cv_r2` of −20,345 is a number the suite produced correctly; in R6's own taxonomy it is a science result. R6's last clause — *"`gate` mode is the row's explicit opt-in to fail"* — grants permission, it does not recommend. The note cites permission as if it were reasoning.
- "Encodes no scientific claim" is false: "a configuration whose CV r² is below −1 is numerically unsound" is a claim about the model on the data. It is a *weak* claim, well supported here, and that is the honest way to say it.
- The original R-6 (experimentation plan:1241) made equities rows informational because *"Equities experiments fail or throttle on network/API limits"* — a data-availability risk. That risk is already outside the band's reach: a cell that produces no manifest is `failed` (`run_suite.py:745`, `:773-782`) and the suite exits 1 on any failed / degraded / not-run cell (`run_suite.py:29`). "Informational, never gating" has not described the exit code since W0.3 merged. The note does not say this, and it is the strongest fact in favour of its own recommendation.
- The defensible case for gate is the structural one in §0 above: the E-H configuration's predictions are bounded (pred std ≤ 0.51× target in every fold; `_phi` is a cosine), its aggregate sits 12 fold-stds above −1.0 (`(agg+1)/eval_std.r2` = 12.0), and the only way the row can breach −1 is a configuration or code change. False-fail risk from data restatement under this configuration: negligible by that bound (UNTESTED on other windows). W5.2's multi-ticker row is correctly deferred (note:216).

Change: replace the R6 paragraph with the structural argument and the run_suite exit-code fact; state the claim the band does encode.

### M3 — MAJOR — W5.9's acceptance is unsatisfiable; the "unknown" optimum was computable

Quotes: §3.2 item 2 (note:197): *"Extend `_GCV_GRID` above 1000 or make the ceiling a logged warning: 15 of 20 GCV folds selected the grid's last point, so "GCV-selected" currently means "the largest value we allowed"."*; §2.3 (note:153): *"the GCV-optimal penalty is unknown — it lies at or beyond the grid's edge"*; §4 (note:232); plan W5.9 acceptance (plan:481): *"the E-H GCV cells re-run off the ceiling"*.

Evidence (Appendix A, "GCV curve beyond the 1000 ceiling: rff/raw", φ taken from the fitted rff/1.0 model so W, b and the fold statistics are the matrix's):

| fold | capped selection | extended argmin (λ ≤ 1e12) | GCV@argmin vs GCV(null) | eval r² at optimum | train r² |
| --- | --- | --- | --- | --- | --- |
| 0 | 1000 | 2.0e5 | −4e-9 (numerically the null model) | −0.051 | 0.0000 |
| 1 | 495 | **398** (interior) | −5.6e-4 | −0.005 | 0.0044 |
| 2 | 60.2 | **63** (interior) | −1.3e-3 | −0.012 | 0.0141 |
| 3 | 1000 | 1e12 (edge) | +1e-12 (null model) | −0.007 | 0.0000 |
| 4 | 1000 | 1e12 (edge) | +7e-13 (null model) | −0.001 | 0.0000 |

In three of five RFF folds the GCV optimum **is** λ = ∞ — the intercept-only model — and no finite ceiling makes the selection interior; the two folds that were already interior (495, 60) stay interior (398, 63). The linear/raw rung is worse (F1): GCV(null) is below every finite grid point in all five folds. So "re-run off the ceiling" cannot be met for folds 0/3/4, extending the grid changes nothing measurable for the E-H row (agg −0.015 either way), and the "unknown" optimum is a one-SVD closed form (`_gcv_select` already has the SVD; the curve past the grid is the same formula).

Change: W5.9 becomes "detect and report a null-model / edge selection" — a WARNING in the model logger (W2.4) **and** a flag in the crossval/train response — with acceptance "a fold whose GCV optimum is the null model is reported as such; the E-H GCV cells report it in folds 0/3/4". Drop the grid extension. Rewrite note:153 and note:232: the optimum is known; it is the null model.

### M4 — MAJOR — the bundle's "(or `gcv` once W5.9 lands)" is wrong, and the choice of `ridge: 1.0` is unargued

Quote (§3.3, note:204): *"`readout: rff`, `ridge: 1.0` (or `gcv` once W5.9 lands), `rff_features: 256`, `rff_gamma: median`."* (same text in plan:407.)

Evidence: M3 — `gcv` on this rung selects the null model in three folds regardless of the ceiling (train r² 0.0000; `rff/gcv` cells: train r² 0.001–0.015, agg −0.014). "Once W5.9 lands" implies W5.9 changes the answer; it cannot. The matrix's best aggregate is rff/gcv (−0.014) and the note picks rff/1.0 (−0.115) without saying why. The defensible reason is in the data: rff/1.0 is the only in-band configuration that **retains any fit** (train r² 0.124–0.184; `folds[].train_metrics.r2`, cells 8/20) — sane by modelling rather than by abstention. "Sane" is not a selection criterion between sane cells; "sane and non-null" is, and it is what the note silently used.

Change: delete the parenthetical; add the sentence "`1.0` rather than `gcv` because GCV selects the null model on this rung (§2.3, M3) and 1.0 retains a fit (train r² 0.12–0.18)".

### M5 — MAJOR — the documented bundle is not the measured configuration

Quote (§3.3, note:204): *"The bundle's other values are unchanged from the plan: `fundamentals_fill: drop`, `regression_target: log_return`, explicit `symbols`"*; versus §0.1 (note:27): *"all other params at the generator's defaults (`fundamentals_fill: nan`, …)"*.

Evidence: `00-dataset-create.json` `meta.params.fundamentals_fill == "nan"`; `20-matrix-datasets.json` request params carry no `fundamentals_fill`. Every number in the note was measured at `nan`; the bundle tells the reader to use `drop`. Because `fundamentals_fill` is hashed into the id, a reader following the bundle gets a **different `dataset_id`** and cannot cross-check against `15505731cba5b86d`. Row equivalence: all 28 arrays of the archived artifact are finite (my check: `X_train/X_val/X_test`, `y_reg_*` — 0 non-finite), so `drop` has nothing to drop for AAPL 2015–2022 and the rows are *probably* identical — **UNTESTED** (minting the `drop` artifact needs a data service). The bundle also omits `d: 16`, `n_folds: 5`, `scheme: expanding`, `embargo: 2`, `lookback: 64` and the seeds (dataset `20260807`; model `random_seed` defaults to 0, `model.py:89`, and the route does not expose it — a Python-API reader with `random_seed=None` will not reproduce −0.1153).

Change: either measure the bundle as documented (one cell) or state in §3.3 that the measurement was at `fundamentals_fill: nan` and why `drop` is expected to be row-identical here; list the CV and seed parameters a reader needs.

### M6 — MAJOR — "who is affected" by W5.8 is incomplete, and option (ii) is not free for the model

Quote (§3.2 item 1, note:194): *"It is the configuration a bare `POST /v1/crossval` or `POST /v1/train` gets, and it is the one canopy's registry seed and any hand-written request fall into."* and (note:195) *"the irregular-sine YAML pins `0.0` explicitly, so the reference experiment is unaffected"*.

Evidence (code):
- `default_ridge` reaches only the linear rung (`_readout.py:101-103`); the RFF rung already defaults to `"gcv"` (`_readout.py:40, :105`).
- **Canopy forwards only `d`, `theta`, `ridge`** (`src/main.py:932`) — it has no `readout` field, so canopy's recurrence path can never select RFF; its `equities_seq` seed sends neither `ridge` nor `normalize_features` (`model_registry.py:332-336`; target `return`, five tickers). Under (i) it moves from the −20,345 class to the −247 class on the one-ticker proxy; five tickers UNTESTED. The "use rff/1.0" remedy is unavailable to canopy's users; the note should say the default is their *only* fix and that (i) alone does not fix it.
- The recurrence CLI `train` without `--ridge` (`main.py:56`) is affected; the suite's `save_model` rerun is not (it passes `--ridge`/`--readout`, `run_experiment.py:1872-1896`).
- The bench is **not** affected by `Settings.default_ridge` (it constructs `LMURegressor` directly, `run_benchmark.py:83, :100`), but option (ii) changes `LinearReadout` itself, and the bench's *ratified* primary bands are the model's `ridge=0` *"juniper-model-core conformance setting ("overfit-tiny exactly")"* that are *"deliberately left untouched"* (`run_benchmark.py:37-41`). A standardised min-norm solve is a different solution (my measurement: −8.8e12 vs −20,345 raw) — so (ii) alters the conformance baseline unless it is gated to ridge > 0 or behind a flag. The plan's W5.8 owner line "recurrence + model" does not name this.
- The reference YAML's `service.default_ridge: 0.0` (`irregular-sine-rff.yaml:20`) is the **E-H suite's `base_config`** (`e-h-recurrence-real-data.yaml:9`). "Unaffected" is true of the reference experiment (its `train:` block pins `ridge: 1.0`, `readout: rff`, YAML:40-41) and false of the stacks launched from it: every experiment-stack service inherits the explicit 0.0, so a bare request to such a service bypasses W5.8 unless the YAML is changed in the same PR.

Change: add the four consumers and the two non-consumers by name; add "update `conf/experiments/irregular-sine-rff.yaml` `service.default_ridge`" to W5.8; state that (ii) must not change the ridge=0 path (conformance kit) and must be measured against the bench before merge.

### M7 — MAJOR — "predict the mean silently" is the actual consequence of the preferred remedy, and the note frames it as "honest"

Quotes: §2.3 (note:153): *"the honest "no linear signal at this horizon" answer"*; §3.2 (note:195): *"the linear rung then shrinks instead of exploding"*.

Evidence: the only linear default that passes the band ((i)+(ii), F2) returns train r² 0.06–0.10 with λ at the ceiling in every fold, or 0.00 as the null model. The route cannot return the selected λ (F-S7, note:32), so a caller sees a plausible "low signal" r² and nothing that says the model abstained. The exploding default at least announces itself (−93,606 is not mistaken for a result). "Honest" describes what GCV *computed*; whether the service *tells* the caller is the design question, and the note resolves it by default rather than by instrument.

Change: order the work — selected λ / null-model flag in the response (W2.4 + a response-schema item, see M8) **before** the default changes; and name the alternative that keeps a fit: default readout rff/1.0.

### M8 — MAJOR — item 3 of §3.2 points at a work item that does not cover it

Quote (§3.2 item 3, note:198): *"Log the resolved theta, gamma and ridge per fold (F-S7, already W2.4's remit)"*.

Evidence: W2.4 (plan:429) is the model's INFO fit summary and *"Route start log prints the resolved theta"*. Per-fold λ / γ / θ **in the crossval response** — the thing a suite, canopy, or a band could read — is in no item (W5.3 adds OOS metrics to `/v1/predict`, not fold diagnostics to `/v1/crossval`).

Change: name it: extend W2.4 (or add W5.10) with "crossval response carries per-fold `theta`, `ridge_selected`, `gamma`, `gcv_at_edge`".

### m1 — MINOR — the +0.5 upper bound is a prior presented as a measured defect detector

Quote (§3.4, note:212): *"An aggregate above +0.5 on next-day log returns would indicate leakage or a scoring error, not skill, so the upper bound is a defect detector too."*

Evidence: max aggregate anywhere −0.0134; max fold r² +0.0003. The one leak the matrix contains — producer normalisation fitted on the pooled train partition (R4 note; the `on` cells) — **lowered** the sane aggregate (−0.115 → −0.142). The data say nothing about +0.5; a target-into-features leak would read ≈ 1.0 and be caught, a milder look-ahead would not. Keep it, label it a prior.

### m2 — MINOR — W5.4 as specified carries one band per row; the note proposes two, and the control row is unaddressed

Evidence: plan:476/495 — *"per-row schema `acceptance: {metric, min, max, mode: gate / report}`"* (singular). The note's §3.4 table has two rows (`cv_r2`, `train_r2`), M1 adds a third. The suite's base cell (irregular sine, `name: null`, `cv_r2 0.975`) would fail +0.5 under any suite-level band. Say the schema becomes a list, that the band is row-scoped to `equities-seq-aapl`, and what the control row carries.

### m3 — MINOR — §3.2 item 4 (F-P8) is a fork, not an action

Quote (note:199): *"juniper-data may hash the arrays instead, or document the field."* No owner question, no work item, and changing `checksum` semantics affects every consumer that stores and compares it — which consumers: UNTESTED. Make it a ruling (R9) or a doc-only item.

### m4 — MINOR — one ticker generalised to a class

Quote (§3.2 item 1, note:194): *"must not be used for equities, or for any non-stationary real-data input."* The mechanism (near-constant single-ticker columns, price-level Legendre memory, §2.4) makes the class claim *expected*; the measurement establishes it for one ticker, one window. Multi-ticker: UNTESTED (and F-P7's non-chronological folds make it a different question). State it as expected, not established. Same for §3.5 "F-SCI1: cause resolved" — resolved for the audited number; fine as written if the ticker scope is restated there.

### m5 — MINOR — "W5.1 a tuning-and-documentation task" under-sells what the note itself proposes

Quote (§3.1, note:190). The measurement shows *every* linear-rung default is either catastrophic or the null model — a default-selection defect at the model's edge (W5.8 is a behaviour change with a CHANGELOG "Changed" entry, note:196). "Tuning" is the wrong label for a recommendation to change what a bare request does.

### m6 — MINOR — the skill baseline is an oracle

`_regression_metrics` scores r² against the **eval fold's own mean** (`model.py:54`), a baseline no model trained on the past can attain; "no demonstrated skill" (note:180) is therefore stricter than the bench's naive-persistence / linear-ridge comparison that the suite comment's "efficient-market ceiling" refers to. Not self-serving (it understates the model); say which baseline.

### Framing census (item 7 of the brief)

| Steer | Earned? |
| --- | --- |
| Bold on the rff/1.0 rows only (note:120, :126, :137) — the configuration the author's suite already uses — while rff/gcv and linear/gcv/on have aggregates nearer zero | Partly: rff/1.0 is the only in-band cell that retains fit (M4), but the note never says so; as printed it reads as "the candidate we had was right" |
| "sane" (note:180 defines it as "not a defect") | Earned as defined; misapplied in §3.4 ("four sane cells", one aggregate) — M1 |
| "defect class … three or more orders of magnitude" | Not earned — M1 |
| "the honest … answer" for GCV's collapse (note:153) | Earned as a statement about GCV; unearned as a service behaviour — M7 |
| "confirmed as the cause of the audited number" (note:147) | Earned |
| "(d) … not implicated. The only rung that standardises per fold is the one that works." (note:150) | Not earned — F2; this is the load-bearing step for option (ii) |
| "the GCV-optimal penalty is unknown" (note:153, :232) | Not earned — M3; it keeps W5.9 alive as a grid extension |
| "a scientific result to report, not a success to celebrate"; "no demonstrated skill" (note:180, :231) | Earned, and against interest — credit |
| "R6's reasoning … applies" (note:215) | Not earned — M2 |
| §3.5 "F-SCI1: cause resolved"; "W1.1(a): … the bundle gains its model-side half" | Resolved for the audited number (fine); the model-side half carries M4/M5 |

The note confirms the plan's candidate (a), which its author proposed. The confirmation itself is sound (every ridge-0 cell is catastrophic; the mechanism is measured). The steering is in what is built on it: each of the three code recommendations (W5.8(i), W5.8(ii), W5.9) is favourable to the narrative "we know the fix" and each is contradicted by a computation the note's instrument could have run.

### Actionability (item 8 of the brief)

| Item | Can an engineer act without a further decision? | Missing |
| --- | --- | --- |
| §3.2(1) W5.8 | No — three options, owner must choose; the preferred one fails the acceptance | the joint requirement (F2); the YAML service block and conformance-kit constraint (M6); a measured acceptance ("bare request on `15505731…` aggregates above −1 **and** the response reports λ") |
| §3.2(2) W5.9 | Half — the warning half is actionable; the extension half is unsatisfiable (M3) | the null-model condition and where it is surfaced; drop "extend" |
| §3.2(3) | Yes for logs (W2.4); no for the response (M8) | the item that adds per-fold diagnostics to the crossval response |
| §3.2(4) F-P8 | No — a fork with no ruling and no item (m3) | ruling or item; consumer census |
| §3.4 R5 band | Mostly — numbers are given; `gate` with a `report` fallback still asks the owner; one of the two bands is vacuous (F3) | `cv_r2_std ≤ 0.5` (M1); schema plurality and the control row (m2); the structural justification (M2) |

## 2. (a) The case that the recommendations must not go to the owner unchanged

Accepting every raw measurement, the two code changes the note proposes are refuted by its own table and by one computation on its own frozen artifact: `default_ridge="gcv"` alone gives −247 on the raw single-ticker artifact (the note's row 118) and ≈ −35 with the grid extended, so it fails the acceptance the plan wrote for it; per-fold standardisation alone gives −192, because the RFF rung is sane for its bounded cosine features and not for its standardisation, which is the step §2.3(d) gets wrong and option (ii) is built on; only the two together pass, by producing a model that predicts the mean with λ pinned to the ceiling in every fold — and the route cannot tell the caller that happened. W5.9's acceptance ("re-run off the ceiling") cannot be met, because GCV's optimum for the RFF rung is λ = ∞ in three of five folds; the "unknown" optimum is a closed form the instrument already computes. The `train_r2 ≤ 0.9` band keys on the train-phase r² at n = 1,346, where no measured defect exceeds 0.229 — it can never fire. The `cv_r2` band's stated separation of "three or more orders of magnitude" is 0.66 orders for the nearest defect, and a single-fold blow-up to −4.6 passes it, a window the existing `cv_r2_std` key closes at ≤ 0.5. The bundle tells the reader `fundamentals_fill: drop` when every number was measured at `nan`, and promises `gcv` "once W5.9 lands" when `gcv` is the null model regardless. An owner ruling R5 and accepting W5.8/W5.9 from this text would approve one vacuous gate, one unsatisfiable acceptance, and a default change whose preferred form does not do what the sentence says.

## 3. (b) Verdict

- **GO: stands.** (a) confirmed, (c) refuted, (b) refuted as the lever — all survive. The structural bound on the RFF rung makes the GO robust beyond the five folds measured.
- **R5: accept `cv_r2 ∈ [−1.0, +0.5]`, `mode: gate`, with amendments** — replace the R6 argument with the structural one and the run_suite exit-code fact (M2); add `cv_r2_std ≤ 0.5` (M1); drop the `train_r2` band (F3); label +0.5 a prior (m1); row-scope it and settle the control row (m2).
- **W5.8: return to the author.** Rewrite as "(A) default readout rff/1.0, or (B) `gcv` **and** standardisation, both with λ / null-model reported in the response first"; name canopy's readout gap, the CLI, the YAML service block, and the conformance-kit constraint on the ridge=0 path (F1, F2, M6, M7).
- **W5.9: return to the author.** Null-model / edge *reporting*, not a grid extension; acceptance rewritten (M3).
- **W1.1(a): return to the author.** Delete "(or `gcv` once W5.9 lands)"; state the `fundamentals_fill` mismatch; add the CV/seed parameters; say why 1.0 (M4, M5).
- **§2.3(d) and §3.2 item 3**: correct the standardisation attribution; name the response-side work item (F2, M8).
- Recommend a v1.1.0 of the note before R5 is ruled; the plan's v1.3.0 rows W5.8, W5.9, the W1.1 details and the §3.9 "resolved" paragraph inherit the same corrections.

## 4. (c) Tallies

- **FATAL 2** (F1, F2 — both W5.8 as written), **MAJOR 9** (F3, M1–M8), **MINOR 6** (m1–m6).
- By target: R5 band — F3, M1, M2, m1, m2; W5.8 — F1, F2, M6, M7, m4, m5; W5.9 — M3; W1.1(a) — M4, M5; §3.2 item 3 — M8; F-P8 — m3; framing — m6.
- Survives unchanged: GO; the (a)/(b)/(c) verdicts and the (d) *conclusion* (not its argument); the −1.0 lower bound; `gate` (with a different justification); F-P8 as a finding; W0.1/W0.3/W0.4 acceptance-in-passing; §2.4 conditioning; §2.5's against-interest framing.
- UNTESTED: five-ticker behaviour of any default; `drop` vs `nan` row equivalence; other windows/seeds; `checksum` consumers; whether W5.4's eventual schema can carry two bands.

## Appendix A — reproduction (run in `/opt/miniforge3/envs/JuniperCascor1/bin/python`, read-only; outputs quoted above verbatim)

```python
import numpy as np
from juniper_recurrence_model import sequence_data_from_arrays
from juniper_recurrence_model.model import _regression_metrics
from juniper_recurrence_model.readouts import _GCV_GRID, _standardize_fit, _ridge_solve
from juniper_model_core.crossval import walk_forward_folds
from juniper_recurrence._readout import build_lmu_regressor

NPZ = ".amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz"  # under juniper-ml/
arrays = {k: v for k, v in np.load(NPZ, allow_pickle=False).items()}
# finiteness: every X_*/y_reg_* array has 0 non-finite cells (M5)
seq = sequence_data_from_arrays(arrays, "full"); n = seq.X.shape[0]
folds = walk_forward_folds(n, n_folds=5, scheme="expanding", embargo=2); aux_all = seq.fit_kwargs()

def gcv_curve(F, y, grid):               # same algebra as readouts._gcv_select, any grid; plus the lambda->inf limit
    n = F.shape[0]; fc = F - F.mean(0); yc = y - y.mean(0)
    u, s, vt = np.linalg.svd(fc, full_matrices=False); g = u.T @ yc; s2 = s**2
    e = float((yc**2).sum()); perp = e - float((g**2).sum()); out = []
    for lam in grid:
        trh = 1.0 + float((s2/(s2+lam)).sum()); rss = float((((lam/(s2+lam))**2)[:, None]*g**2).sum()) + perp
        d = (n - trh)**2; out.append(n*rss/d if d > 0 else np.inf)
    return np.array(out), n*e/(n-1.0)**2, s
def gcv_fit(F, y, lam):
    fm = F.mean(0); ym = y.mean(0); u, s, vt = np.linalg.svd(F-fm, full_matrices=False); g = u.T @ (y-ym)
    coef = vt.T @ ((s/(s**2+lam))[:, None]*g); return np.concatenate([coef, (ym - fm @ coef)[None, :]], 0)
ext = np.logspace(-6, 12, 181); cache = {}
for i, f in enumerate(folds):                      # fidelity + memory blocks from the matrix's own rff/1.0 fit
    tr, ev = f.train_idx, f.eval_idx; atr = {k: v[tr] for k, v in aux_all.items()}; aev = {k: v[ev] for k, v in aux_all.items()}
    m = build_lmu_regressor(d=16, theta=None, readout="rff", ridge=1.0, rff_features=256, rff_gamma="median", default_ridge=0.0)
    m.fit(seq.X[tr], seq.y[tr], **atr); print(i, _regression_metrics(seq.y[ev], m.predict(seq.X[ev], **aev))["r2"])  # -0.0803 ... -0.2584
    Mtr = m._memory_block(np.asarray(seq.X[tr], float), atr.get("dt"), None, atr.get("seq_lengths")); Mev = m._memory_block(np.asarray(seq.X[ev], float), aev.get("dt"), None, aev.get("seq_lengths"))
    ytr = np.asarray(seq.y[tr], float).reshape(len(tr), -1); yev = np.asarray(seq.y[ev], float).reshape(len(ev), -1)
    cache[i] = dict(Mtr=Mtr, Mev=Mev, str=m._side_channel(atr.get("target_dt"), len(tr)), sev=m._side_channel(aev.get("target_dt"), len(ev)), ptr=m._readout._phi(Mtr), pev=m._readout._phi(Mev), ytr=ytr, yev=yev)
for i, c in cache.items():                         # (5) GCV past the ceiling, linear/raw and rff/raw
    for name, F, Fe in (("linear", np.c_[c["Mtr"], c["str"]], np.c_[c["Mev"], c["sev"]]), ("rff", np.c_[c["ptr"], c["str"]], np.c_[c["pev"], c["sev"]])):
        g, null, s = gcv_curve(F, c["ytr"], ext); j = int(np.argmin(g)); coef = gcv_fit(F, c["ytr"], float(ext[j]))
        print(name, i, "argmin", ext[j], "edge", j == len(ext)-1, "min/null-1", g[j]/null-1, "eval r2", _regression_metrics(c["yev"], np.c_[Fe, np.ones(len(Fe))] @ coef)["r2"])
for mode in ("ridge0", "ridge1", "gcv_capped", "gcv_ext"):   # W5.8 option (ii): standardised linear rung
    ev = []
    for i, c in cache.items():
        mu, sd = _standardize_fit(c["Mtr"]); F = np.c_[(c["Mtr"]-mu)/sd, c["str"]]; Fe = np.c_[(c["Mev"]-mu)/sd, c["sev"]]
        D = np.c_[F, np.ones(len(F))]; De = np.c_[Fe, np.ones(len(Fe))]
        if mode == "ridge0": coef = np.linalg.lstsq(D, c["ytr"], rcond=None)[0]
        elif mode == "ridge1": coef = _ridge_solve(D, c["ytr"], 1.0)
        else:
            grid = _GCV_GRID if mode == "gcv_capped" else ext; g, _, _ = gcv_curve(F, c["ytr"], grid); coef = gcv_fit(F, c["ytr"], float(grid[int(np.argmin(g))]))
        ev.append(_regression_metrics(c["yev"], De @ coef)["r2"])
    print(mode, [round(x, 3) for x in ev], np.mean(ev))   # ridge0 -8.8e12; ridge1 -191.9; gcv_capped -0.195; gcv_ext -0.019
```

Band / sensitivity / dilution numbers in M1, F3 and §0 are plain reads of `reports/2026-10-04_recurrence-equities-cv-matrix/21-matrix-cells.json` (`eval_aggregate.r2`, `eval_std.r2`, `folds[].eval_metrics.r2`, `folds[].train_metrics.r2`, `folds[].pred_eval.std`, `folds[].target_eval.std`, `folds[].ridge_resolved`).
