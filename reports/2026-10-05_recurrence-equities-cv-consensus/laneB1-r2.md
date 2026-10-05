# Lane B1-r2 — adversarial review of the v1.1.0 corrections (round 2)

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.1.0 (working tree; `git diff` against committed v1.0.0 = 100 insertions / 75 deletions)
- **Brief**: REFUTE the corrections. Lenses: correctness of the new text, internal consistency, sequencing/gating consequences, self-serving framing, re-opened closed questions.
- **Entry points used**: the diff first, then v1.1.0 whole, the plan v1.3.0 (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`), the plan's consensus record (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`), `reports/2026-10-04_recurrence-equities-cv-matrix/*.json`, `reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive*.json` and `laneA3-rerun/*`, the three 2026-10-05 ad-hoc scripts, source under `juniper-recurrence/`, `juniper-data/juniper_data/generators/equities/generator.py` + `core/artifacts.py` (to test the F-P8 code claims), `juniper-ml/juniper-model-core` (scorer), `juniper-canopy/src/backend/recurrence_*` (the "cannot select RFF" claim), and the two 2026-10-03 mints under `juniper-ml/.amp/in/` (meta `created_at`, arrays). **Not opened**: `lane*.md` round-1 reports, the consensus-record note.
- **Computations**: four scratchpad scripts (`check_a.py`–`check_d.py`, scratchpad only; results are reproduced inline below so nothing depends on them surviving). No file in the repo was written except this report.

Line numbers below are v1.1.0's (`N:` = note line) unless prefixed `plan:`.

---

## 1. Findings

### F1 — MAJOR — a universal in the new §2.5 is false on the note's own table

> N:184 "Fold 4 is the worst fold in every sane cell."

Evidence (`21-matrix-cells.json`, fold-resolved rows, argmin of per-fold eval r²): rff/1.0/off → worst fold 4 ✓; rff/1.0/on → worst fold 4 ✓; **rff/gcv/off → fold 4 is the BEST fold (+0.00034), worst is fold 0**; **rff/gcv/on → fold 4 is the BEST (+0.00031)**; **linear/gcv/on → worst is fold 0 (−0.047), fold 4 = −0.006**. True for 2 of the 5 sane cells. The sentence motivates the `test`-partition concern as a general degradation; it is a property of the ridge-1.0 RFF cells only.

Change: "Fold 4 is the worst fold in both rff/1.0 cells; in the three GCV cells it is the best or second-best — the `test` era is not harder for an abstaining model."

### F2 — MAJOR — numbers in the new text have no instrument or artifact in the note's declared Instruments / Evidence lists

Quoted new sentences and the number each carries:

- N:184 "Re-measured on train + val only (1,522 windows): rff/1.0 −0.101, rff/gcv −0.006, service defaults −17,365"
- N:185 "(embargo 64: rff/1.0 −0.153 full, −0.111 with `test` excluded; rff/gcv −0.017 / −0.009)"
- N:154, N:188, N:196 "in-support (the shuffled split) the RFF rung is bounded (≈ −0.05)" / "the RFF rung still scores ≈ −0.05"
- N:196, N:229 "on both 2026-10-03 mints (−0.115 / −0.101)" / "and both 2026-10-03 mints"
- N:178 "row order ≤ 2.5 %, a float32 round-trip of the design 6 %"
- N:183 "`rff / gcv` is seed-stable (−0.013 … −0.015)"
- N:174 "`total_shares` has a coefficient of variation of 0.63"

Evidence: `grep -rn "1522|17365|17,365|embargo=64|embargo 64|shuffle"` over `reports/2026-10-04_…/`, `laneA3-rerun/*.log|*.md|*.json`, both reconciler JSONs and the three 2026-10-05 scripts returns **nothing** for the first two bullets. `reconciler-rederive-b1.json` has F1 (mint diff + linear/ridge0 on mint B only — no rff/1.0 on B), F2 (`fold4_shuffled_eval_r2_3_draws` via `linear_fit_eval` only — no RFF draw), F5, F7, F9 (seeds for rff/1.0 only — no rff/gcv per seed). `laneA3-rerun/30-numpy-checks.json` holds float32 column stds, not a design round-trip. The CV 0.63 is derivable (from the NPZ, last-step `total_shares` std/mean = 0.629) but is not in any listed artifact. **The same value −0.101 is quoted for two different conditions** (mint B at N:196; `test` excluded at N:184/N:196/N:229) — a probable copy error that no artifact can arbitrate.

Consequence: §3.1's "the review established it more broadly than v1.0.0 did" and §3.4's "The bound survives … embargo 64 (−0.153), `test` excluded (−0.101) and both 2026-10-03 mints" rest on numbers a reader cannot re-derive; the Lane A principle the note otherwise follows ("artifact over prose") is broken by the fix pass.

Change: extend `2026-10-05_recurrence_equities_consensus_rederive_b1.py` with F10 (train+val-only, three cells), F11 (embargo 64, full and test-excluded), F12 (RFF rung on the three shuffled draws), F13 (rff/1.0 and rff/gcv on mint B; rff/gcv per seed), F14 (row-order permutation; float32 round-trip), write them to the JSON, and cite the keys; or strike the numbers and the two sentences that lean on them. Resolve the −0.101 collision either way.

### F3 — MAJOR — the F-SCI1 re-attribution re-opens the withdrawn hypothesis and misaligns cause with remedy

> N:153 "**(a) unregularised linear readout — confirmed as the amplifier; the cause is extrapolation under drift.**"
> N:239 "F-SCI1: cause **resolved** → candidate (a) as the amplifier of extrapolation under drift; (b) refuted as the lever (its drift mechanism is real)"
> N:152 "The drift of price-level features out of the training support that candidate (b) also named is real and is part of the cause"

Evidence: the plan's consensus record §4.1 closed "the normalisation hypothesis is withdrawn as a hypothesis-of-record; it survives only as candidate (b)" (plan:255–258 carry that text). v1.1.0 re-elevates (b)'s mechanism — drift of unnormalised price-level inputs — into *the cause* while demoting the measured lever to "amplifier"; yet every remedy proposed (§3.2 items 1–3: readout / ridge / standardisation defaults, λ reporting) acts on (a), and nothing proposed acts on drift (which is intrinsic to every chronological equities split and not removable). §4 (N:252) itself concedes "A separation of candidate (a) from the drift: no matrix cell is drift-free" — so "cause **resolved**" overreaches: the data support a necessary conjunction, not a cause/amplifier ordering. This is the round-1-fix-restores-a-closed-question pattern §4 of the procedure warns about, in the finding's own severity row.

Change: F-SCI1 cause of record = "the service-default readout (linear, ridge 0, unscaled 242-column design) applied to a chronologically drifting input; both are necessary (§2.3, F2 of the b1 re-derivation); the actionable lever is the default (W5.8)". Keep (b) withdrawn as a hypothesis-of-record; do not write "the cause is drift" into the plan's §3.9.

### F4 — MAJOR — the shuffled-split inference conflates "in-era" with "near-duplicate of a training row"

> N:153 "a same-pool **shuffled** split of fold-4 size with the identical design and solver — eval rows drawn from inside the training era, so no drift — scores −0.33 / −0.001 / −0.08 instead of −7,239"

Evidence: `rederive_b1.py:196–206` — three full permutations of the pool, no embargo. By the note's own N:185, adjacent windows share 61 of 64 days, so every shuffled eval window is a near-copy of several training windows. The control therefore removes drift **and** inserts maximal near-duplicate leakage; numerically, a near-copy of training rows has ~no component along the discarded directions, which is the mechanism of §2.4 — so the result is *consistent* with the mechanism but cannot say "drift" as opposed to "any row outside the training row-space". It is also one fold size, three draws, the linear rung only. What else the result could mean: that the 2021 eval block specifically (the 4:1 split entering `split_ratio`'s memory columns only in fold 4's train; `market_cap`/`total_shares` level jumps) is the problem — not drift in general. "ridge = 0 is neither sufficient nor necessary" is still supported: *not necessary* by linear/1.0 (−2,064) and linear/gcv (−247) (sourced); *not sufficient* only by this leaky control.

Change: run a block-held-out in-era control (eval = one contiguous 283-window block inside the training era, with a ≥ 64-window embargo on both sides, train = the rest) for both rungs; replace "so no drift" with "in-support (and overlapping)" until it exists.

### F5 — MAJOR — (d) is re-based on a non-discriminating control plus an unsourced number

> N:154 "The evidence is the control and the in-support result, not the rung comparison v1.0.0 made: the irregular-sine control through the same route and configuration scores `cv_r2 0.975` (§1.4), and in-support (the shuffled split) the RFF rung is bounded (≈ −0.05) and the linear rung is finite."

Evidence: the irregular-sine control is stationary and uses a synthetic `dt` pattern; a model or `dt`-handling defect that only manifests on equities' calendar gaps or on out-of-support memory states is untouched by it (it establishes that the route + configuration are sound on a stationary signal — nothing about (d) under drift). The RFF in-support number has no artifact (F2 above: `linear_fit_eval` only). What survives, sourced: F2's three linear in-support draws are finite (−0.33 / −0.001 / −0.08). The withdrawal of v1.0.0's "the only rung that standardises per fold is the one that works" is correct (rff/0.0 standardises and scores −1,986; linear/gcv/on does not and scores −0.015 — both in `21-matrix-cells.json`), and "−192" for the standardised linear rung at ridge 1.0 is sourced (`C_std_linear_ridge1_eval_r2` aggregate −191.90).

Change: "(d) not implicated **for the linear rung in-support** (F2); the RFF rung in-support is UNMEASURED; the sine control shows the route and configuration are sound on a stationary signal and does not test a drift-conditioned defect." Add the RFF in-support cell (F4's control) before writing "(d) not implicated" into plan §3.9.

### F6 — MAJOR — §3.2's option ranking rests on a criterion the owner did not set, applied to the best of six seeds

> N:209 "| (A) default readout `rff`, ridge 1.0 | **−0.115**, train r² 0.12–0.18 | the only in-band default that retains a fit |"
> N:211 "Recommendation, in order: **(A)** a default readout of `rff` with `ridge: 1.0`, or **(B)** …"
> N:208 "| (i) + (ii) | −0.195 (λ at the ceiling in every fold) / −0.019 (grid extended; the null model) | passes by abstaining; train r² 0.06–0.10 / ≈ 0 |"

Evidence: (1) "retains a fit" is in-sample train r² — the quantity §3.4 (N:232) withdraws as a tell and §3.1 (N:198) says has no in-support counterpart ("there is no in-support signal to tune toward"). By the out-of-sample criterion the plan's W5.8 acceptance actually names (plan:480 "aggregates above −1"), the abstaining defaults (−0.015 / −0.019) score *better* than (A) (−0.115). (2) −0.115 is seed 0 = "the best of six" (N:183); the seed mean is −0.155 ± 0.045, worst −0.252 (`F9`). The table quotes the best draw without the caveat two sections earlier. (3) The RFF rung's **own** designed default ridge is GCV (`readouts.py:272` `ridge: RidgeParam = "gcv"`; `_readout.py:77–78` "``None`` ⇒ the rung default (``default_ridge`` for linear, GCV for RFF)"), scores −0.015, is in band, and is absent from the table — (A) as written overrides two defaults, not one. (4) "(grid extended; the null model)" — `C_std_linear_gcv_ext_lambda` = 1e12, 1e12, 1e12, **125,892, 6,309** with train r² 0.004 / 0.038 in folds 3–4: the null model in three folds of five. (5) No measured number in the table disagrees with §2.2/§2.3 ((i) −247 = linear/gcv/off; (A) −0.115 = rff/1.0/off; (ii) −192 and −8.8e12 match `C_*`).

Change: rank by the owner's criterion (in band) plus the abstention-transparency requirement the note's own item 3 imposes; quote (A) as "−0.155 ± 0.045 across seeds (seed-0 route value −0.115)"; add the `rff / gcv` row; present (A) vs (B) as the owner's choice with the trade-off stated ("a fit that scores worse out of sample vs an abstention that must be flagged"); fix "the null model" to "the null model in three folds (λ → ∞), interior in folds 3–4".

### F7 — MAJOR — option (A) exceeds W5.8 as the plan words it and needs a setting that does not exist

> N:211 "**(A)** a default readout of `rff` with `ridge: 1.0`"
> N:202 "(canopy forwards only `d` / `theta` / `ridge` and **cannot select RFF**, so for canopy the default is the only fix)"

Evidence: plan:480 W5.8 Change column: "`default_ridge` → `"gcv"`, and/or per-fold standardisation on the linear rung; at minimum document the hazard" — no readout change. `settings.py:181–183` has `default_d`, `default_theta`, `default_ridge` only; `readout: None ⇒ linear` is fixed in `schemas.py:39–44` and `_readout.py:75`. (A) therefore adds a `Settings` field, changes the resolved default of `/v1/train` and `/v1/crossval`, and changes the model class canopy is served without any canopy change (`recurrence_backend.py:96` `_HYPERPARAM_KEYS = ("d", "theta", "ridge")` — the "cannot select RFF" claim is **verified** at the adapter). That is a canopy-visible behaviour change owned by "recurrence + model". (Checked and *not* a problem: neither the service schemas/routers nor canopy's backend/adapter expose `coef`, so RFF's `coef = None` breaks no surface.) Also verified: `conf/experiments/irregular-sine-rff.yaml` is the E-H suite's `base_config` (`util/experiments/suites/p4/e-h-recurrence-real-data.yaml:9`) and pins `default_ridge: 0.0` (yaml:20), so the "same PR" constraint at N:211 is right.

Change: either widen the W5.8 row (readout default, new setting, canopy as an affected consumer) or file (A) as its own proposal (W5.11) so the owner accepts the wider change knowingly.

### F8 — MAJOR — §3.4's structural argument is contradicted by §1.1, and its margin statistic is seed-selected

> N:234 "the aggregate sits 12 fold-stds above −1.0, and the only way the row can breach the bound is a configuration or code change — which is what a gate is for."

Evidence: (1) §1.1 establishes that the same request can be served different content with no configuration or code change (two mints, 12–19 % movement on the defaults); the E-H row mints from a live yfinance fetch per run (N:26 "per-run (cold) equities cache"; `generator.py:983` `yf.download(...)`), so an upstream revision or an omitted action column (F-P8) is a third way the number moves. The note's own Major finding refutes its own "only way". (2) "12 fold-stds" is seed 0's dispersion; from `F9` the same statistic is 8.9 / 12.3 / 7.6 / 7.6 / **3.9** for seeds 1–5 (per-seed population std 0.098 / 0.071 / 0.111 / 0.110 / 0.191). The fold std is the dispersion of five values, not a sampling std of the aggregate; it is not a margin. (3) Not circular as such — "`_phi` is a cosine so predictions are bounded" is a real structural property (`readouts.py:290–293`); the overclaim is the "only way" clause.

Change: "the ways the row can breach the bound are a configuration/code change or an upstream data change (F-P8); a gate surfaces all three, which is the desired behaviour once W5.7's `actions_present` guard distinguishes the third"; delete "12 fold-stds" or report "3.9–12.3 across seeds".

### F9 — MAJOR — the "wrong columns" correction is itself wrong about `cost_basis`

> N:174 "The only exactly-constant memory columns are `split_ratio`'s sixteen (zero until the 2020-08-31 split; folds 0–3); `cost_basis`'s memory columns vary with the irregular `dt` pattern and `total_shares` has a coefficient of variation of 0.63 — v1.0.0 named the wrong columns."

Evidence: Lane A3's own `30-numpy-checks.json`: `X_last_step_n_zero_std_columns: 1`, `X_last_step_std_argmin: 9` (column 9 = `cost_basis` in the F5 ordering), `X_all_steps_n_zero_std_columns: 1`, value `27.3325`. From the Scenario-A NPZ: `cost_basis` min = max = 27.3325 over all 1,698 × 64 cells (std 3.8e-6, float32 noise). `cost_basis` is an **exactly-constant feature**; its sixteen memory columns are 27.33 × the LMU's response to the `dt` sequence alone and carry no price information — which is what "near-constant column" meant. v1.0.0 was right about `cost_basis` and wrong about `total_shares` (CV 0.629, recomputed). The F5 keys the sentence cites (`per_feature_memory_col_std_min_max.cost_basis` = [0.046, 1.02]) measure the memory columns, not the feature.

Change: "The only exactly-constant memory columns are `split_ratio`'s sixteen (folds 0–3). `cost_basis` is an exactly-constant feature (27.3325) whose memory columns vary only with the `dt` sequence; `total_shares` (CV 0.63) is not near-constant — v1.0.0 was right about the first and wrong about the second."

### F10 — MAJOR — §3.5 does not list what the new facts move in the plan

> N:237–244 (§3.5, whole)

Omitted consequences, each created or sharpened by a v1.1.0 change:

- (a) **Release placement.** N:211 "A pre-1.0 'Changed' entry in recurrence 0.6.0" — recurrence 0.6.0 is W1.13's P1 publication (plan:400, 420; M1 2026-11-21, plan:509) and W5.8 is P5 "after M1" (plan:634). Either W5.8 moves into P1 or the entry is 0.7.0. The model halves of W5.8(ii)/W5.9/W5.10 sit the same way against model 0.4.0 (W1.13), and the plan's status table books P5 model work as "model 0.4.x" (plan:595, 512) — a patch line that cannot carry a default or behaviour change. §3.5 mentions neither W1.13 nor the version.
- (b) **W5.2's population vs the band.** N:184 says W5.2's population "is not the one measured here" and N:235 says it "gets its own measurement before it gets a band" — but W5.2 Details (plan:492) apply the `test` exclusion to CV generally ("CV runs over `train+val`"), including the single-entity E-H row, so once W5.2 lands the E-H row's own population becomes 1,522 windows. The order W5.2 → re-measure → W5.4 encode (or "band encoded for the pre-W5.2 population, re-measure item filed") is not stated, and the plan's dependency table (plan:666) has no W5.2 → W5.4 edge.
- (c) **W5.3's `test_r2`.** N:184 "fold 4's eval holds … the entire 176-row `test` partition" means `test_r2` is not held out until W5.2 lands; W5.3 therefore depends on W5.2 — not an edge in plan:665. And R5 (plan:752) asks for a band on "`cv_r2`/`test_r2`"; the recommendation offers no `test_r2` row and no explicit deferral.
- (d) **Plan text that now carries withdrawn claims.** plan:263–268 (F-SCI1 "resolved 2026-10-04") still says "(d) is not implicated (the one rung that standardises per fold is the one that works)", "amplification up to 2.6e4", "the audited digits (−83,452) did not reproduce (−93,606) on byte-identical arrays and code", "tuning-and-documentation", and W5.9 "extend the grid" (plan:481). plan:405–407 (W1.1 Details) justify `normalize_features: false` with "(−0.115 raw vs −0.142 normalised)" — which N:152 now calls noise — and carry "(or `gcv` once the grid ceiling is lifted, proposed W5.9)", which N:220 withdraws. plan:168 (F-P8) still says "all 28 arrays are byte-identical" and "the `dataset_id` did pin the content". N:239 says "§3.9's 'what the measurement does and does not say' is superseded" but names none of these paragraphs.

Change: add (a)–(d) to §3.5 by plan line; propose the W5.2 → W5.3 and W5.2 → W5.4 edges; say whether W5.8/W5.10 target 0.6.0 (then they are P1) or 0.7.0.

### F11 — MINOR — §3.4 contradicts §2.3(b) on the normalisation leak

> N:229 "the one leak the matrix contains (pooled-train scaling) lowered the number"

N:152: "the difference (−0.115 raw vs −0.142 scaled) is **below the RFF seed spread** … so it supports no direction." The same 0.027 is noise in §2.3 and an effect in §3.4. Change: "did not raise the number (−0.142 vs −0.115, within seed noise)".

### F12 — MINOR — the overlap effect is quoted below the note's own noise floor

> N:185 "near-duplicate rows across the boundary flatter an over-fitted readout by ≈ 0.04 (embargo 64: …)"

0.04 is below the "≈ 0.05 … is noise" of N:183; with `test` excluded the quoted difference is 0.01; the numbers are unsourced (F2). Change: "≤ 0.04, within seed noise" — and source it.

### F13 — MINOR — the GCV "optimum is known" paragraph overstates fold 0 and understates what extension changes

> N:155 "for the RFF rung it is the null model (λ → ∞, the intercept-only fit) in folds 0, 3 and 4 … No grid extension changes that"

`reconciler-rederive.json` fold 0: `D_rff_gcv_ext_lambda 199526`, `D_rff_gcv_ext_at_edge false`, `D_rff_gcv_ext_min_over_null_minus_1 −4.2e-9` — an interior optimum that is *effectively* null (train r² 1.2e-5), not λ → ∞; folds 3–4 are at the 1e12 edge ✓. "No grid extension changes that" is true of the class; the §3.2 table shows extension moves the numbers materially (−247 → −35; −0.195 → −0.019). Change: "effectively the null model in fold 0 (λ ≈ 2e5), λ → ∞ in folds 3–4; extension changes the digits, not the class."

### F14 — MINOR — §1.1 asserts a mechanism §4 says is unknown

> N:51 "so a transiently incomplete fetch is served, silently, under the same id."
> N:256 "why yfinance omitted the action columns for one fetch and not for another 85 s earlier" (not known)

Other mechanisms consistent with the evidence: a per-run cache CSV lacking the columns (`generator.py:975` reads `cache` when `use_cache`), or a column-flattening edge in `_normalize_ohlcv_columns` (`generator.py:997–1006`). Change: "an upstream response without the action columns — cause unknown — is served silently".

### F15 — MINOR — F-P8's framing conflates the design with the defect; "Major" is defensible; the guard mostly follows

> N:53 "the `dataset_id` hashes the request, not the content"
> N:214 "`equities/generator.py` zero-fills `dividend` / `split_ratio` when yfinance omits the action columns, so an incomplete upstream response is served as a complete artifact with no log line"

Request-addressing is the cache design (the id is the key; content is unknowable before generation). "Zero-fills … with no log line" is a **fair reading**: `generator.py:794–799` fills on absence with no `_logger` call. The W5.7 additions follow for `actions_present` + a log line; "or refuse the mint" cannot be decided by the generator (it does not know whether actions exist in range) — refuse only on request. Major is defensible on consequence (a silent 12–19 % change to a scientific result under one id). Change: "the id is request-addressed by design; the defect is that an incomplete upstream response is indistinguishable from a complete one".

### F16 — MINOR — §3.1 rewrites the consensus-validated gating definition and widens W5.1's go branch

> N:198 "this makes **W5.1 a documentation-and-defaults-hardening task**, not a model/CV defect investigation ("tuning" is the wrong word …)"

plan:342 (validated at v1.2.0) defines "go" as "a tuning and documentation task"; plan:473 defines W5.1's go content as "record the sane number". The relabel turns the go branch into three code items. Keep as the note's gloss; do not propagate into the gating paragraph; the code items are proposals needing acceptance (the note says so at N:211–213).

### F17 — MINOR — off-by-one in the target-gap claim

> N:185 "eval targets ≥ day t+5"

`F7`: train 0..280, eval from 283 (embargo 2); the first eval window ends 3 days after the last train window, so its next-day target is t+4. No effect on "no target leakage".

### F18 — MINOR — a double negative inverts the intended meaning

> N:94 "nothing it read had not changed"

Reads as "everything it read had changed"; two of fifteen columns did. Change: "two of the columns it read had changed".

### F19 — MINOR — the `train_r2` withdrawal is justified but its number is from the matrix, not the train phase

> N:232 "the train phase's in-sample r² at n = 1,346, where no defective configuration exceeds 0.229"

0.229 is rff/0.0/on's fold-4 (n = 1,413) train r² from `21-matrix-cells.json`; no n = 1,346 train-phase run of a defective configuration exists. The inference is reasonable; say where the number is from. Withdrawal is justified: R5 (plan:752) asks about `cv_r2`/`test_r2`, not an overfit tell, and a report-mode row that cannot fire is noise. The right tell is per-fold train r² on fold 0 once W5.10 exists — worth one sentence.

### F20 — MINOR — framing: sentences that steer beyond the data (not already listed)

- N:7 "upheld by every re-measurement" — includes the unsourced ones (F2).
- N:196 "its predictions never exceed |0.021|" — seed 0 only (max |pred| 0.0213 in `21-matrix-cells.json`); seeds 1–5 have no prediction record.
- N:153 "The catastrophe needs both" — from three leaky draws on one artifact (F4).
- N:202 "expected for any non-stationary real-data input by the mechanism of §2.4" — hedged as "expected"; acceptable.
- N:174 "That is why column scaling is part of any fix" — consistent with every measured fix; acceptable.

---

## 2. Attacked and HELD (so the reconciler knows what survived)

- **§1.1 two-mint story**: `X_val` col 11 (`split_ratio`) differs in exactly **64** cells (A nonzero 64, B 0); `dividend` 1,367 / 180 / 178 cells; meta `created_at` A `09:14:24.6Z`, B `09:15:49.7Z` → **85 s** ✓; checksum `c02004e1…` on 2026-10-03 (A), 10-04, 10-05 ✓ (`00-dataset-create.json` ×2, archive meta); 10-05 NPZ whole-file sha256 `cff84fe5…` equals the archive's (`30-numpy-checks.json` `npz_file_bytes_identical: true`); every audited digit reproduced on mint B (`F1.linear_ridge0_on_B`, aggregate −18081.54317 = `24-c-crossval-shadow` excerpt).
- **Checksum is a content fingerprint**: `artifacts.py:33–47` sorted keys + uncompressed `np.savez`; `:50–63` sha256 ✓.
- **Producer scaling is min-max [0,1] on train** (`params.py:94–96`) — v1.1.0's correction of "z-scored" ✓.
- **Digits reproducible / rounding story withdrawn**: `54-thread-sweep-fold0.json` max deviation 3.8e-4 (threads = 4), fold 4 ≤ 6.8e-5 (`50-fold-threads-*`); all 24 cells and both replays EXACT on the 10-05 stack (`41-compare.md:97–102`, replay rows); the 1e-7 r² difference is consistent with model-core `_metrics.py:30–31` (float64 coercion) vs `model.py:54` (none).
- **GCV**: 15/20 at λ = 1000 (30/40 with twins, `41-compare.md:94`); `_GCV_GRID = logspace(−6, 3, 60)` semantics per `readouts.py:119–153`; `D_linear_null_is_below_every_grid_point` true in all five folds; (i) −246.9 / ext −35.1; (ii) −191.9; (i)+(ii) −0.195 / −0.019; standardised ridge-0 −8.76e12 — all in `reconciler-rederive.json`.
- **§2.4 numbers**: raw fold-0 rank 113 / σ_max 2.80e12; fold-4 σ_max 8.87e12; standardised rank 226 / 242 and 242 (`F5`); scaled fold-0 cond 1.75e24 → "1.8e24" (v1.1.0 right, v1.0.0's 1.7e24 was truncated) (`23-linear-conditioning.json`).
- **Fold composition**: fold 3 = 214 train + 69 val; fold 4 = 107 val + 176 test (`F7`); test `window_end_date` 2021-04-21 → 2021-12-29 (NPZ) ✓; 61/64-day overlap by construction ✓.
- **Seed sweep**: −0.115 … −0.252, mean −0.155, std 0.045, seed 0 best (`F9`) ✓.
- **`cv_r2_std ≤ 0.5` false-fail test**: per-seed population std = **0.074 / 0.098 / 0.071 / 0.111 / 0.110 / 0.191** → no seed fails; linear/1.0/on std 8.75 ✓; one-outlier std = 0.4|x| ✓ (population); 7× margins ✓; the W0.4 headline is the service's `eval_std.r2`, a population std (`executor.py:54, 65`) ✓; the suite's recorded `cv_r2_std` 0.07353723443032745 equals it (`scenario-a-rerun/registry.jsonl`).
- **Band arithmetic**: sane per-fold [−0.28, +0.00], aggregate [−0.142, −0.013]; nearest non-sane −4.52 (4.5×); 1/0.142 = 7.0× ✓; dropping fold 0 → −0.124 / −2,029 ✓; "0.51×" is rff/1.0/on fold 4 (0.51), rff/1.0/off max 0.48 ✓.
- **§3.2 code claims**: canopy forwards `d`/`theta`/`ridge` only ✓; CLI `--ridge`/`--readout` default `None` → settings / linear (`main.py:56–57`) ✓; `irregular-sine-rff.yaml` is the E-H `base_config` and pins `default_ridge: 0.0` ✓; manifest `"git": {}` ✓ (`c001-manifest.json`); wall 32.1 s / fit 10.3 s per cell ✓ (`wall_seconds`, `fit_seconds`).
- **R-6 origin** (`JUNIPER_2026-07-29_…CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md:1241`): "fail or throttle on network/API limits … informational, never gating" — N:234's characterisation ✓; plan R6's last clause "`gate` mode is the row's explicit opt-in to fail" is permission, as N:234 says ✓.
- **No contradiction found** with the R4 note (plan:757–759: fold-local memory standardisation required; (B)(ii) is exactly that), with the plan's out-of-scope line (plan:779: memory standardisation is in scope), or with the consensus record's §6 "attacked and held" items.

## 3. UNTESTED

- N:57 "the suite's `dataset.params` override replaces the base YAML's params wholesale" — consistent with the six-key override in the suite YAML and the accepted body, loader not read.
- N:202 "cannot select RFF" at canopy's **UI** (adapter verified; UI not).
- Whether a block-held-out in-era control (F4) changes the (a)/(drift) reading — not run; it is the test the note needs.
- The RFF rung in-support (F5) — no artifact exists.

---

## 4. Verdict

**(a)** v1.1.0 should **not** go to the owner for R5 as written. The GO verdict and the two band numbers (`cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`, both `gate`) survive every test I could run, including the seed-sweep false-fail test — R5's *numbers* are ready. The *recommendation text* that frames them has ten MAJOR defects introduced or left by the fix pass: an F-SCI1 cause statement that re-opens the withdrawn (b) hypothesis and does not match the remedy (F3), a drift inference from a leaky control (F4) and a (d) verdict re-based on it plus an unsourced number (F5), an option ranking on an in-sample criterion over the best of six seeds that exceeds W5.8's scope (F6, F7), a structural gate argument the note's own F-P8 refutes (F8), a false universal (F1), a mis-correction about `cost_basis` (F9), seven numbers with no instrument (F2), and a §3.5 that omits the release-placement, population and `test_r2` consequences (F10). A v1.1.1 pass confined to §2.3(a)/(d), §2.4, §2.5, §3.1–§3.2, §3.4 and §3.5 — plus either the F10–F14 re-derivation keys or the strike-through — is enough; the matrix need not be re-run. Round 3 should then be a single Lane A check of the new keys.

**(b)** Tallies: **FATAL 0 / MAJOR 10 (F1–F10) / MINOR 10 (F11–F20) / HELD 14 groups (§2) / UNTESTED 4.** One re-opened closed question (F3). Numbers without a declared source: 7 (F2).
