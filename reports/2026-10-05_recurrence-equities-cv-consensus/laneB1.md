# Lane B1 — adversarial analysis review of the W5.1 note (correctness and omission lens)

- **Reviewer**: Lane B1 (independent-agent consensus procedure §2 Lane B — brief: REFUTE; steelman NO-GO / INCONCLUSIVE)
- **Artifact under review**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.0.0 (line numbers below are from that file)
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.3.0 (§3.9 F-SCI1 at lines 238–261; the gating paragraph at line 342; W0.8/W0.9 rows at 362–363; W5.1/W5.2/W5.3/W5.4/W5.8/W5.9 at 473–481; Details at 486–490; status row at 571; R4/R5/R6 and the R4 note at 751–759)
- **Date**: 2026-10-05
- **Checkout**: juniper-ml `main` `a0a120d5` (worktree `misty-kindling-pascal`); juniper-recurrence checkout at `be081fae` (read-only); interpreter `/opt/miniforge3/envs/JuniperCascor1/bin/python` (3.14.7, numpy 2.5.3, libopenblas 0.3.34, juniper-model-core 0.2.0, juniper-recurrence-model 0.3.0 editable)
- **Method**: read the note, the plan sections named above, both instruments (`util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py`, `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py`), every file in `reports/2026-10-04_recurrence-equities-cv-matrix/`, the model source (`readouts.py`, `model.py`, `_readout.py`, `routers/crossval.py`, `settings.py`, model-core `splits.py`), the generator (`juniper-data/.../equities/generator.py`, `core/artifacts.py`) and the audit evidence tree (`.amp/in/artifacts/recurrence-equities-audit/`). Then **computed** every contested claim that could be computed, from the frozen NPZ the audit archived and the Scenario-B NPZ the audit's data store still holds. Scripts are reproduced in Appendix A; results in Appendix B. I did not read the other lanes' reports.
- **Nothing was edited** except this file. No git write commands were run.

---

## 0. Verdict in one line

**GO survives as the plan defines it (line 342: "a 'go' — E-H's config is sane"); the note's explanations do not.** Seven MAJOR correctness defects — the biggest being that the between-day digit change the note attributes to floating-point rounding is in fact a **data difference the note had the evidence for and explained away** (the 10-03 number was solved on an artifact whose `dividend` column is all zero and whose Aug-2020 4:1 split is missing; re-solving on that artifact reproduces every audited digit) — must be corrected before R5 is ruled. No finding makes INCONCLUSIVE the honest verdict.

---

## 1. Findings

Severity: **FATAL** = the GO verdict or the R5 recommendation cannot stand on the note as written; **MAJOR** = a stated conclusion, mechanism or recommendation is false and must be rewritten, verdict survives; **MINOR** = precision or wording. Evidence cites `file:line`, a JSON key path, or a computation in Appendix B (`B.n`).

### F1 — MAJOR — The between-day digit change is a data difference, not rounding; the note's F-P8 reading inverts the truth

**Attacked (L88)**: *"Same arrays (§1.1), same model code (`juniper-recurrence-model` at `be081fae` both days — the audit shadowed the checkout), same machine — and the fold-0 number moved by 12 % and fold 4 by 19 %. A solve whose out-of-sample answer changes while nothing it reads has changed is being decided by rounding; §2.4 measures why."*
**Attacked (L173)**: *"It is also why the digits moved between 2026-10-03 and 2026-10-04 on identical inputs: at cond 1e32 the solution in the near-null subspace is determined by floating-point rounding (BLAS reduction order, thread count), so the number is reproducible only to its order of magnitude."*
**Attacked (L174)**: *"The audited −18,081 and today's −20,345 are the same measurement."*
**Attacked (L49)**: *"The meta `checksum` nevertheless differs (`037baab7…` on 2026-10-03, `c02004e1…` on 2026-10-04): it fingerprints the NPZ container, whose zip entries carry write timestamps, not the arrays. Recorded in the plan as **F-P8** (Minor). The first reading of that difference — 'the equities data drifted under the same id' — was wrong"*
**Attacked (L233)**: *"The exact audited digits (−18,081, −83,452): at condition number 1e32 they are rounding artefacts of an ill-posed solve and were not expected to reproduce (§2.4)."*

**Evidence**:

1. *The −18,081 was not computed on the arrays the note diffed.* The audit's §2.1 (plan lines 62–70) ran Scenario A (launcher + suite) and Scenario B (hand-started shadowed service + curl) as separate stacks. The −18,081 is Scenario B's (`.amp/in/artifacts/recurrence-equities-audit/24-c-crossval-shadow.txt`, 2026-10-03T04:16:51 local). Scenario B's data service (`20-data.log:3-12`) ran with `Storage path: …/juniper-ml/.amp/in/scratch/data-store` and created the artifact **afresh** at 04:15:49 ("`equities_seq: [1/1] AAPL -> 1762 rows`"), 85 s after Scenario A's own fresh fetch (`scenario-a-runs/20261003T091414Z-4ba6/logs/juniper-data.log`, 04:14:24, also 1762 rows). The two creations have different `created_at` and different `checksum`: Scenario A's copy `c02004e1…` at 09:14:24Z (`scenario-a-runs/…/data/equities_seq-6.0.0-15505731cba5b86d.meta.json`); Scenario B's `037baab7…` at 09:15:49Z (`40-seq-meta-http.txt`, and the top-level `equities_seq-6.0.0-15505731cba5b86d.meta.json`). The note's §1.1 byte-diff (L47) compares the 10-04 artifact with **Scenario A's** copy — the copy that did *not* produce the number under investigation.
2. *The checksum is content-deterministic, so a different checksum meant different content.* `juniper-data/juniper_data/core/artifacts.py:40-62`: `arrays_to_bytes` sorts keys and `np.savez`es into a `BytesIO`; `compute_checksum` is sha256 of that. Recomputing today (B.7) gives `c02004e1` for the Scenario-A/10-04 arrays — the third time this checksum has been produced, on three different days (10-03 09:14Z, 10-04 21:06Z per `00-dataset-create.json`, 10-05 now) — and `037baab7` for the Scenario-B arrays. The note's "zip entries carry write timestamps" is false (numpy writes fixed 1980 zip timestamps); the "first reading" the note rejected was right.
3. *The Scenario-B artifact survives and differs in two feature columns.* `.amp/in/scratch/data-store/equities_seq-6.0.0-15505731cba5b86d.npz` (B.7): same 28 keys and shapes; `X_train`/`X_val`/`X_test` differ **only** in column 10 `dividend` (all 0.0 in B vs 0.16–0.22 in A; 1,367 + 180 + 178 cells) and, in `X_val`, column 11 `split_ratio` (0 in B vs 4.0 in A for the 64 cells around 2020-08-31 — the 4:1 split is absent). Every other key is byte-identical. Mechanism: `generator.py:794-799` zero-fills `dividend`/`split_ratio` when yfinance's response omits the action columns ("absent means 'none happened'"), so a response that transiently lacks the `actions=True` columns (`generator.py:983`) is served, silently, under the same `dataset_id`.
4. *Re-solving on the Scenario-B arrays reproduces every audited digit* (B.7): fold 0 train r² `0.452957979` / eval `−83451.610`; fold 1 `−814.665`; fold 2 `−3.720`; fold 3 `−78.492`; fold 4 train `0.137595904` / eval `−6059.229`; aggregate `−18081.543` — identical to `24-c-crossval-shadow.txt` to every printed digit. The audited digits **do** reproduce; they are a property of the data they were computed on.
5. *The rounding mechanism the note names is directly refuted for fold 4* (B.2, B.3): with OpenBLAS at 1/2/4/8 threads the fold-4 eval r² spans −7238.67 … −7239.95 (≤ 1.8e-4 relative); random row permutation ≤ 5e-5; multiplicative design noise at 1e-16 … 1e-6 ≤ 1.6e-4; a float32 round-trip of the design 7e-6. Nothing rounding-shaped moves fold 4 by 19 %, nor its train r² by 1.7 % (perturbations move train r² by < 1e-5). Fold 0 *is* rounding-sensitive at the 1–6 % level (B.3), which is why the note's story was plausible there — but the same-day HTTP-vs-in-process difference the note's own evidence already contains is 1.2e-7 relative (F6), six orders below the between-day move, a gap the note did not notice.
6. Libraries are unchanged between the days: numpy 2.5.3 `.so` mtime 2026-09-06, `libopenblas-0.3.34` in `conda-meta`, `juniper_model_core-0.2.0.dist-info` 2026-09-12; the only env change on 10-04 is the editable `juniper_recurrence_model` `.pth` (15:56). The recurrence reflog (`.git/logs/HEAD`) puts `be081fae` on `main` from 2026-10-02T23:31:59Z, before the audit, and the tracked tree is clean now — the "same model code" claim is supported (tree state on 10-03 itself: UNTESTED).

**What must change**: L88, L173–174, L233 and §1.1's "same arrays" must be rewritten: the audited digits reproduce exactly on the artifact they were solved on; the two days measured two *different artifacts served under one id*. F-P8 must be re-filed from "checksum fingerprints the container (Minor)" to a **DATA finding of at least Major**: the `equities_seq` id does not pin content, and `generator.py:794-799` zero-fills absent yfinance action columns silently — a producer defect in W5.7's territory (alongside F-P5/F-P6), with an obvious acceptance test (refuse or flag an AAPL-length window with zero dividends and no split event). The "same machine, same code — so rounding" inference pattern (asserting an unobserved mechanism for an inconvenient result) should be named in the note's own §4. **The class does not change** (B.7: `rff/1.0` on the Scenario-B arrays aggregates −0.101; `rff/gcv` −0.015; service defaults −18,081), so GO is unaffected.

### F2 — MAJOR — "(a) confirmed as the cause" is incomplete: the chronological drift is necessary, and the matrix cannot separate the two

**Attacked (L147)**: *"(a) unregularised linear readout extrapolating — confirmed as the cause of the audited number. Every `ridge = 0.0` cell is catastrophic in both readouts and both normalisations"*
**Attacked (L188)**: *"The −18,081 is a property of the service defaults — an unregularised linear readout on a rank-deficient, unstandardised memory design (§2.4) — not of the model, the data contract, theta or the `dt` handling."*
**Attacked (L220)**: *"F-SCI1: cause resolved → candidate (a), with (b) and (c) refuted and (d) not implicated"*

**Evidence** (B.4, shuffled same-era split — identical design, identical readout, identical fold sizes, but eval rows drawn from inside the train era so there is no drift):

| configuration (raw artifact) | chronological fold | same-pool shuffled, 3–5 draws |
| --- | --- | --- |
| linear / ridge 0.0, fold-0 sizes (281/283) | −93,606 | −0.52 … −9.75 |
| linear / ridge 0.0, fold-1 sizes | −798 | −0.15 … −0.39 |
| linear / ridge 0.0, fold-4 sizes (1413/283) | −7,239 | −0.04 … −0.21 |
| linear / ridge 1.0, fold-4 sizes | −3,356 | −0.13 … −0.21 |
| linear / gcv, fold-4 sizes | −976 | −0.09 … −0.12 |
| rff / ridge 1.0, fold-4 sizes | −0.258 | −0.05 … −0.06 |

With the drift removed, the "unregularised linear readout on a rank-deficient unstandardised design" is **not catastrophic** (fold 4: −0.04 to −0.21; even the n≈p fold 0 is four orders of magnitude better). With the drift present, ridge 1.0 and GCV on the same design are **still catastrophic** (−3,356 / −976; note's own table L117–118). So `ridge = 0` is neither necessary (ridge > 0 also blows up) nor sufficient (no drift → no blow-up) for the catastrophe; it sets the *magnitude* (10³× worse). The cause is the conjunction: a linearly-extrapolating readout on an unstandardised design × eval inputs 8–199 σ outside the train support (note L151). Every one of the 24 matrix cells carries the drift, so the matrix **cannot** attribute the blow-up to (a) rather than to the drift the plan listed under (b) and (d); the note's §2.3 declares (b) "refuted" and (d) "not implicated" on the strength of the *lever* each candidate proposed (producer normalisation; per-fold standardisation), not of the *mechanism* each named. The drift-free cell is what separates them, and the note does not have one.

**What must change**: §2.3(a) → "necessary amplifier, not sole cause"; §3.1 "not of … the data contract" is doubly wrong (F1 and this); §3.5 and the plan's F-SCI1 "cause resolved → (a)" must record the conjunction, which changes what W5.8 can promise (F3) and makes the feature representation (price levels, `market_cap`, `total_shares` as raw levels — a producer concern) part of the cause statement rather than something the note rules out.

### F3 — MAJOR — The note's preferred fix, W5.8 option (i), is contradicted by the note's own table

**Attacked (L195)**: *"(i) change `Settings.default_ridge` from `0.0` to `"gcv"` (the linear rung then shrinks instead of exploding; …)"* and plan W5.8 (line 480): acceptance *"Route test: a bare `/v1/crossval` on the E-H artifact aggregates above −1"*, Details (line 486) *"Preferred: `Settings.default_ridge` `0.0` → `"gcv"`"*.

**Evidence**: note L118 / `22-matrix-table.md` row `linear | gcv | off`: per fold −217.61 / −2.66 / −2.04 / −36.59 / −975.55, **aggregate −246.89**, with λ at the grid ceiling (1000) in three of five folds. On the E-H artifact, option (i) alone does not "shrink instead of exploding"; it fails W5.8's own acceptance test by two orders of magnitude. Only the normalised twin (`linear | gcv | on`, −0.015) is sane — i.e. the standardisation, option (ii), is the load-bearing half. Shuffled-split (B.4) confirms the same reading: GCV on the raw design is fine in-support (−0.09 … −0.12) and catastrophic under drift.

**What must change**: §3.2 item 1 must make (ii) per-fold train-only standardisation of the linear rung the necessary part and (i) the complement, and W5.8's acceptance must name the standardisation; as written, a route test passing under (i) alone is not reachable on this artifact.

### F4 — MAJOR — "(d) not implicated" rests on a non-sequitur

**Attacked (L150)**: *"(d) per-fold standardisation on a non-stationary memory — not implicated. The only rung that standardises per fold is the one that works."*

**Evidence**: the premise is false in both directions on the note's own table: `rff | 0.0 | off` standardises per fold (`readouts.py:298-299`) and is catastrophic (−1,986, L119); `linear | gcv | on` does not standardise per fold and works (−0.015, L124). "Standardises per fold" neither predicts nor explains sanity; bounded features (`cos`, `readouts.py:293`) plus enough shrinkage do. The candidate (d) the plan wrote was "a genuine model or `dt`-handling defect" (plan line 253) and, under no-go, "per-fold standardisation on a non-stationary memory" (plan line 489); neither is tested by that sentence. The evidence that *does* bear on a gross model/`dt` defect is in the note but unused: the Scenario-A control, `irregular_sine` `cv_r2 0.975` through the same route with the same configuration (L96, `scenario-a-rerun/registry.jsonl`), and the in-support `rff/1.0` result (B.4, −0.05 — bounded, no explosion, no skill).

**What must change**: replace the sentence with the control-based argument; state explicitly that (d)'s *drift* component is real (L151 already measures it) and is the same drift F2 names.

### F5 — MAJOR — "Rank-deficient by a third to a half" is a column-scale artefact of the relative cutoff, and the columns named as constant are the wrong ones

**Attacked (L172)**: *"The design is **rank-deficient by a third to a half** on the raw artifact (near-constant columns — `cost_basis`, `total_shares` for a single ticker — plus the Legendre memory of slowly varying price levels) and the 2-norm condition number is 1e22–1e32."*

**Evidence** (B.6): the "numerical rank" 113 (fold 0) / 161 (fold 4) is `numpy.linalg.lstsq`'s eps-rule relative to σ_max, and σ_max (2.8e12 … 8.9e12) is set by the `market_cap` block (per-column std 1.4e9 … 7.6e10). Standardising the columns of the *same* fold-0 design gives rank **226 / 242**, and fold 4 **242 / 242 — full rank**. Structural deficit: 16 exactly-constant columns in folds 0–3, and they are **`split_ratio`** (feature 11, zero until 2020-08-31; `defaults.py:127-152` column order), not `cost_basis` (its 16 memory columns have std 0.046 … 1.02 because the LMU memory of a constant input varies with the irregular `dt` pattern) and not `total_shares` (last-step std 4.4e9 on mean 7.0e9, coefficient of variation 0.63 — AAPL's buybacks and the 4:1 split; `20-matrix-datasets.json` → `X_last_step_full_per_feature_std[7]`). The precise mechanism is therefore: `lstsq`'s relative cutoff, dominated by three 1e7–1e12-scale feature blocks, truncates ~130 directions that carry nearly all the price/return information; the retained weak directions are then extrapolated. B.3's `rcond` sweep shows the same thing (fold 0 eval r² −5.8e6 at rcond 1e-15, −71 at 1e-12, −3.95 at 1e-10).

**What must change**: §2.4's mechanism paragraph; the named columns; and the "rank-deficient" framing, which suggests a degenerate dataset when the standardised design is (near-)full-rank — exactly why standardisation (F3) is the fix.

### F6 — MINOR — "Identical to every printed digit" is false at the digits the note prints

**Attacked (L34)**: *"the in-process cell matching the service defaults reproduces the HTTP control to every printed digit (aggregate −20,344.64; fold 0 −93,606.23)"*; **(L178)**: *"In-process vs HTTP: identical to every printed digit"*.

**Evidence**: `10-crossval-service-defaults.json` → `response.folds[0].eval_metrics.r2` = `−93606.2421298088` (prints −93,606.24); `21-matrix-cells.json[0].folds[0].eval_metrics.r2` = `−93606.2310410387` (prints −93,606.23). The note quotes the in-process value as the HTTP one. Per fold the HTTP/in-process relative differences are 1.2e-7 … 1.4e-8 (B.1); an in-process rerun today matches the HTTP digits bit-for-bit under the service's thread count (B.2: 8 threads). The materiality is F1's: this is the only within-day reproducibility measurement the note had, and it bounds the rounding effect at 1e-7.

### F7 — MAJOR — The CV consumed the `test` partition; "nothing here speaks to the `test` partition" is the opposite of the case

**Attacked (L179)**: *"Nothing here speaks to multi-ticker folds (F-P7 / W5.2), to the `test` partition (W5.3), to other `d`, or to the MLP rung."*

**Evidence**: `routers/crossval.py:72` cuts folds over `split="full"`; `20-matrix-datasets.json` → `n_train_partition 1346 / n_val 176 / n_test 176`, folds `eval_first_idx` 283/566/849/1132/1415 with `n_eval 283` (B.5, B.8): fold 3's eval holds 69 `val` rows; **fold 4's eval holds 107 `val` rows and all 176 `test` rows** (dates 2020-11-13 → 2021-12-29; the `test` partition is 2021-04-21 → 2021-12-29). Fold 4 is the worst fold in every sane cell (−0.26 / −0.28) and contributes a fifth of the aggregate. Consequences the note omits: the "sane number", the R5 band and the W1.1(a) bundle choice were all selected on a population that includes `test`, so W5.3's "`test` is touched once" (plan line 490) is already void for this artifact; and W5.2 will exclude `test` from the pool (plan line 490), so the population the band will govern is not the one it was measured on. Re-measured on train+val only (B.9): `rff/1.0` −0.101, `rff/gcv` −0.006, service defaults −17,365 — class unchanged.

**What must change**: §2.5 and §4 must state that fold 4 is the `test` partition plus `val`; §3.4 should carry the train+val numbers alongside; W5.3's owner should know the promise is already broken for every full-view CV run.

### F8 — MINOR — Embargo 2 against a 64-step look-back: every fold's first eval window shares 61 of 64 days with the last train window

**Attacked**: §0.1 L28 presents `embargo=2` as the fold design without comment; W5.2 (plan line 490) itself requires *"embargo in windows ≥ `lookback` so no eval window's history overlaps a train window"*.

**Evidence** (B.8): per fold, the first eval window's first step date precedes the last train window's end date; shared calendar days 61/64 in every fold (`splits.py:127` leaves a 3-window gap). The target is next-day `ln(next_close/close)` (`equities/generator.py:1288-1301`), so there is no *target* leakage (train targets ≤ day t+1, eval targets ≥ day t+5); the issue is near-duplicate rows across the boundary, which flatters an over-fitted readout. Re-measured with embargo 64 (B.9): `rff/1.0` −0.153 (full) / −0.111 (test excluded); `rff/gcv` −0.017 / −0.009. The as-measured −0.115 is mildly optimistic (by ~0.04, half the fold std); sign and class unchanged.

**What must change**: state it in §2.5/§4; W5.4's band should be re-measured once W5.2 lands, which the note's L216 half-says for the multi-ticker row only.

### F9 — MAJOR — One hard-wired RFF seed; the matrix's draw is the best of six, and the normalisation comparison sits below the seed noise floor

**Attacked (L179)**: *"one seed"* (which reads as the dataset seed); **(L212)**: *"The sane class sits in [−0.26, +0.00] per fold and −0.115 aggregate across the four sane cells"*; **(L145/L203)**: the −0.115 vs −0.142 comparison used to fix `normalize_features: false`.

**Evidence**: the RFF projection is drawn from `np.random.default_rng(random_seed)` (`readouts.py:296`) with `LMURegressor(random_seed=0)` (`model.py:89`), and `build_lmu_regressor` never passes a seed (`_readout.py:101-111`), so the HTTP route and the in-process script share seed 0 — the "to every digit" agreement on the RFF cell is seeding, not a reproducibility result. Sweeping seeds 0–5 on the raw artifact (B.10): aggregates −0.115 (seed 0), −0.131, −0.126, −0.153, −0.156, −0.252 — mean −0.155, std 0.045; per-fold minimum −0.558 (seed 5, fold 4). The matrix's one draw is the best of six. The raw-vs-normalised difference (0.027 aggregate; per fold 0.014–0.062, all the same sign) is smaller than the seed-to-seed spread, so §2.3(b)'s "−0.115 raw vs −0.142 normalised" and §3.3's use of it cannot support a direction; "gives no reason to turn it on" (L203) is the defensible wording and "is not needed by the sane configuration" (L145) is the overstated one. `rff/gcv` is seed-stable (−0.013 … −0.015). The R5 band itself survives (worst aggregate −0.25 against a −1.0 gate; the service always uses seed 0 on this row), but its stated margin "three or more orders of magnitude" (L212) describes the defect class, not the sane class's own spread (4× at the worst seed).

**What must change**: §2.5 must say the RFF seed is fixed at 0 and never varied; §3.4 should quote the seed-sweep range; §3.3 should not cite the normalisation delta as evidence.

### F10 — MINOR — "(b) refuted as the lever" is right for the blow-up and over-read for the sane cell

**Attacked (L145)**: *"(b) unnormalised features — refuted as the lever. Producer normalisation does not rescue the unregularised solve … and is not needed by the sane configuration (RFF ridge 1.0: −0.115 raw vs −0.142 normalised)."*

**Evidence**: the first half is solid (−20,345 → −4.3e12, L122). The second half is F9's delta, and the normalised artifact also carries the R4-note leakage (plan line 757; note L107), so even a favourable result would have been uninterpretable as a CV control. The plan's candidate (b) also named the *mechanism* "price-level features drifting out of support fold by fold" — which L151 confirms is real; "refuted" should be scoped to the producer-normalisation lever only (F2).

### F11 — MINOR — The W1.1(a) bundle documents the measured-worse ridge

**Attacked (L204)**: *"`readout: rff`, `ridge: 1.0` (or `gcv` once W5.9 lands)"*.

**Evidence**: `rff/gcv` beats `rff/1.0` in every fold on both normalisations (L121 vs L120; L127 vs L126), is the rung's own default (`_readout.py:40`), is seed-stable (F9) and reproduces the fold-mean predictor (B.1: GCV r² equals the train-mean-on-eval r² to 3 decimals in every fold). `ridge: 1.0` is a carry-over from the synthetic `irregular-sine-rff.yaml` (`conf/experiments/irregular-sine-rff.yaml:40`). The grid-ceiling caveat (W5.9) is legitimate, but a bundle whose purpose is regression detection documents an under-regularised value whose eval r² is pure prediction variance (B.1: for `rff/1.0` the measured r² equals −(pred_std² + bias²)/target_std² to within ±0.03 in folds 2–4, i.e. near-zero covariance with the target; folds 0–1 carry a small positive covariance, ρ ≈ 0.16 / 0.07). Either value is defensible; the note should say why it picks the worse-scoring one.

### F12 — MINOR — "24 cells" is 12

**Attacked (L106/L112)** and plan line 571 *"(24 cells)"*: the theta axis is degenerate by construction — the configured value is the full-set median `sum(dt)` (91.0), and every fold's median is 91.0 (`sum(dt)` std 1.7, L27), so all 12 configured cells equal their twins to every digit (`22-matrix-table.md`; B.1 confirms `theta_resolved` = 91.0 in 120/120 folds). The matrix has 12 distinct cells; the count should say so.

### F13 — MINOR — Theta was never varied, so "theta is not a lever on this artifact" is unsupported beyond 91.0

**Attacked (L144)**: *"Theta is not a lever on this artifact."* The matrix refutes the *fold-mismatch* hypothesis the plan's (c) actually posed (plan line 252) — correctly — but no cell tried a theta other than the data-driven value, so nothing is known about theta as a lever. Scope the sentence to "theta does not differ between folds".

### F14 — MINOR — "The efficient-market ceiling" is an interpretation presented as a finding

**Attacked (L71)**: *"which is what 'r² ≈ 0 at the efficient-market ceiling' looks like"*; **(L180)**: *"That is the efficient-market ceiling the suite comment anticipates"*.

**Evidence**: an EMH reading requires the model to be tested inside its domain; 28–100 % of eval rows per fold are > 5 σ out of the train support (L151; B.5). In-support (B.4, shuffled) `rff/1.0` is still −0.05 … −0.06 — the model has no skill *in* support either, so the honest sentence is "these features with this readout carry no demonstrable next-day signal", which L180's second half already says ("no demonstrated skill"). The ceiling is neither measured nor needed; leave it to the suite comment.

### F15 — MINOR — `n_windows: 1346` is quoted beside `cv_r2` without comment

**Attacked (L95)**: *"`metrics: {train_r2: 0.1163, cv_r2: -0.1153, cv_r2_std: 0.0735, n_windows: 1346}`"*. 1,346 is the `train` partition (the `/v1/train` population); the CV population is 1,698 (`10-crossval-eh-rff.json` → `response.dataset.n_windows`). The plan's F-SCI1 paragraph (line 247) already corrected this confusion once; the note re-introduces it by quoting the registry verbatim.

### F16 — MINOR — "A tuning-and-documentation task" when there is nothing to tune toward

**Attacked (L190)**: *"Under the plan's gating paragraph this makes **W5.1 a tuning-and-documentation task**"*. The plan's go-content (line 490) is "documents why the service default must not be used … and records the sane number" — documentation, not tuning. With no in-support skill (F14) and GCV collapsing to the fold mean, "tuning" implies a target that the evidence says is absent. Say "documentation and defaults hardening".

### F17 — MINOR — §4 ("what the evidence cannot support") is incomplete

Missing from L230–234: that fold 4 is the `test` partition (F7); the fixed RFF seed (F9); the 61/64-day overlap (F8); that the 10-03 artifact's content was never compared (F1 — now known to differ); that theta took one value (F13); and that no cell removes the drift (F2). Its one explicit reproducibility claim (L233) is wrong (F1).

---

## 2. Attack-by-attack answers to the brief

1. **(a) as THE cause / drift vs rank deficiency** — the matrix cannot separate them (every cell is chronological); the shuffled-split diagnostic (B.4) does, and shows drift is necessary while ridge 0 only sets the magnitude. The "rank deficiency" is a column-scale artefact (B.6). → F2, F5.
2. **(d) cleared by "the only rung that standardises is the one that works"** — non-sequitur on the note's own table (F4). The RFF rung's sane number is over-dispersed noise with near-zero covariance in folds 2–4 (B.1); "sane" means bounded and finite, nothing more, and the note's §2.5 says as much. Regularisation is not hiding a (d) defect that the control (`irregular_sine` 0.975) would have shown; the note just does not make that argument.
3. **(b) refuted from −0.115 vs −0.142** — five same-sign fold deltas of 0.014–0.062 against a seed-to-seed spread of 0.045 (std) / 0.14 (range): indistinguishable from the RFF draw (F9); "refuted" is right only for the blow-up lever (F10).
4. **Universals** — "theta 91.0 in every fold of every cell": verified 120/120 but never varied (F13). "All 24 cells": 12 (F12). "Every ridge = 0.0 cell": four distinct cells, all catastrophic — verified. "The same measurement": two different artifacts under one id (F1). §4's list: incomplete (F17).
5. **§2.4's rounding explanation** — asserted, and false: thread count/row order/ulp noise move fold 4 by ≤ 2e-4 (B.2, B.3); the Scenario-B artifact (which the note's evidence tree names by checksum and `created_at`, `40-seq-meta-http.txt`) differs in `dividend` and `split_ratio` and reproduces every 10-03 digit (B.7). "Same model code at be081fae both days" is supported by the reflog and a clean tree today (10-03 tree state UNTESTED). The distinguishing observation was the Scenario-B NPZ in `.amp/in/scratch/data-store`; the note had its checksum and dismissed it.
6. **GO under the plan's definition** — GO is correct as defined: the E-H configuration is bounded and finite on both artifact contents (−0.115 / −0.101), on six seeds (worst aggregate −0.25), with embargo 64 (−0.153), with `test` excluded (−0.101), and in-support (−0.05); and the instrument *could* have said no for the RFF rung — `rff | 0.0` returned −1,986. "Efficient-market ceiling" is an excuse-shaped interpretation (F14); P5's "tuning" has no target (F16); INCONCLUSIVE is not the honest verdict (see §3).
7. **Omissions** — `test` partition consumed by fold 4 (F7); 61/64-day overlap, no target leakage, −0.04 optimism (F8); fold 0 n≈p: dropping it changes the sane aggregate −0.115 → −0.124 and the defaults aggregate −20,345 → −2,029 — class unchanged either way (B.1 arithmetic); float32: inputs are float32 and cast to float64 at `model.py:137`; a float32 round-trip of the design moves fold 0 by 6 % and fold 4 by 7e-6 (B.3) — irrelevant to the class; MLP rung: UNTESTED (disclaimed at L179); RNG: seed 0 everywhere, so HTTP = in-process by seeding (F9); constant columns: only `split_ratio`'s 16 in folds 0–3 — the deficit is scale (F5); canopy 5-symbol seed: UNTESTED (multi-ticker order is F-P7's problem; nothing here transfers); W1.1(a) `ridge: 1.0`: F11.

---

## 3. The case for NO-GO / INCONCLUSIVE, and whether it survives

**(a) Strongest case for INCONCLUSIVE.** The matrix never ran a drift-free cell, so it cannot attribute the catastrophe to the readout rather than to inputs that sit 8–199 σ outside the training support in every fold; its one "sane" configuration is a single hard-wired random-feature draw (the best of six), scored on a population that includes the entire `test` partition, with 61-of-64-day overlap across every fold boundary, on an artifact whose `dataset_id` demonstrably does not pin its content — two creations under one id differed in two feature columns, and the note's explanation for the resulting digit change was an unobserved mechanism that direct perturbation refutes. The model has no skill in-support either, so "r² ≈ 0 at the efficient-market ceiling" is not a finding, P5's "tuning" has nothing to tune toward, the preferred fix (default ridge → GCV) leaves the linear rung at −247 on the note's own table, and the mechanism paragraph names the wrong constant columns and a rank deficiency that disappears under column scaling. A verdict whose every supporting explanation is wrong or untested should be INCONCLUSIVE until a drift-free cell and a dividend-complete artifact have been measured and the note's §2.3–§2.4 rewritten.

**(b) Does it survive the evidence? No.** The plan defines GO narrowly and operationally (line 342: "E-H's config is sane" versus "E-H configuration also blows up"), and that proposition is now established more broadly than the note established it: the E-H configuration is bounded and finite on both artifact contents (−0.115 / −0.101), across six RFF seeds (worst aggregate −0.25, worst fold −0.56), with the embargo W5.2 will require (−0.153), with `test` excluded (−0.101), and in-support (−0.05); its predictions never exceed |0.021| against a target std of 0.018. The instrument was capable of returning NO-GO for the same rung — `rff | 0.0` returned −1,986 — so the GO is a measurement, not a limitation of the instrument. The data-identity defect (F1) moves digits, not classes, and is a producer finding the plan must absorb, not a reason to withhold the verdict. What the evidence does not support is the note's *explanatory* layer — the cause attribution (F2), the rounding story and F-P8 (F1), the (d) argument (F4), the rank-deficiency mechanism (F5), the W5.8(i) promise (F3), and the scope statements about `test` and the seed (F7, F9) — and those must be corrected before R5 is ruled, because W5.8's acceptance test and the band's stated margin inherit them. The R5 band itself (−1.0 / +0.5, `gate`) survives every re-measurement in Appendix B; the `train_r2 ≤ 0.9` report band is unaffected.

**(c) Tallies.** FATAL 0 · MAJOR 7 (F1, F2, F3, F4, F5, F7, F9) · MINOR 10 (F6, F8, F10–F17) · UNTESTED 6 (below). Verdict on the verdict: **GO stands; the note does not stand as written.**

---

## 4. UNTESTED (could not test; not dropped)

- The MLP rung (torch-gated; nothing in the matrix or here).
- Multi-ticker artifacts / the canopy 5-symbol seed (F-P7 ordering makes any single-ticker result non-transferable).
- Other `d`, other tickers, other windows, other dataset seeds.
- The recurrence working tree's state on 2026-10-03 (clean today; reflog places `be081fae` on `main` from 2026-10-02T23:31:59Z).
- Why yfinance's `actions=True` response lacked the action columns for the Scenario-B fetch at 09:15:49Z and not for Scenario A's 85 s earlier (upstream transient vs a code path; the generator's zero-fill at `generator.py:794-799` is what turned it into a silently different artifact). The 10-04 run directory (`20261004T210331Z-491a`) is not on disk, so its data-service log could not be checked for a fresh fetch.
- The deferred service-core half of W0.1 (not numeric; outside this lens).

---

## Appendix A — Computation scripts (verbatim; they lived in the session scratchpad)

`cvattack.py` (run with `/opt/miniforge3/envs/JuniperCascor1/bin/python cvattack.py <base|threads|perturb|shuffle|rffseed|embargo|dates>`):

```python
#!/usr/bin/env python3
"""Lane B1 attack computations over the frozen E-H artifact (read-only; writes only to the scratchpad).

Subcommands: base | perturb | shuffle | rffseed | embargo | dates | threads
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

NPZ = "/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz"
SCRATCH = Path(__file__).resolve().parent
CACHE = SCRATCH / "M_full_theta91.npz"


def load_full():
    from juniper_recurrence_model import sequence_data_from_arrays

    with np.load(NPZ, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    seq = sequence_data_from_arrays(arrays, "full")
    return seq, arrays


def memory_block(seq, theta=91.0, d=16, cache=True):
    from juniper_recurrence_model.model import LMURegressor

    if cache and CACHE.exists():
        c = np.load(CACHE)
        return c["M"], c["extra"]
    aux = seq.fit_kwargs()
    m = LMURegressor(d=d, theta=theta)
    m._n_features = seq.X.shape[2]
    m._uses_target_dt = aux.get("target_dt") is not None
    M = m._memory_block(seq.X, aux.get("dt"), None, aux.get("seq_lengths"))
    extra = m._side_channel(aux.get("target_dt"), seq.X.shape[0])
    if cache:
        np.savez(CACHE, M=M, extra=extra)
    return M, extra


def metrics(y, p):
    from juniper_recurrence_model.model import _regression_metrics

    return _regression_metrics(np.asarray(y, float).reshape(-1, 1), np.asarray(p, float).reshape(-1, 1))


def folds(n, n_folds=5, embargo=2):
    from juniper_model_core.crossval import walk_forward_folds

    return walk_forward_folds(n, n_folds=n_folds, scheme="expanding", embargo=embargo)


def fit_linear(M, extra, y, tr, ev, ridge=0.0, rcond=None, noise=0.0, perm=False, seed=0):
    from juniper_recurrence_model.readouts import LinearReadout, _assemble_design

    Mtr, Etr, ytr = M[tr], extra[tr], y[tr].reshape(-1, 1)
    if perm:
        rng = np.random.default_rng(seed)
        p = rng.permutation(len(tr))
        Mtr, Etr, ytr = Mtr[p], Etr[p], ytr[p]
    if noise:
        rng = np.random.default_rng(seed + 1)
        Mtr = Mtr * (1.0 + noise * rng.standard_normal(Mtr.shape))
    if ridge == "gcv" or ridge > 0:
        r = LinearReadout(ridge=ridge)
        r.fit(Mtr, Etr, ytr)
        coef = r.coef
        sel = r.ridge
    else:
        D = _assemble_design(Mtr, Etr)
        coef, *_ = np.linalg.lstsq(D, ytr, rcond=rcond)
        sel = 0.0
    ptr = _assemble_design(Mtr, Etr) @ coef
    pev = _assemble_design(M[ev], extra[ev]) @ coef
    return metrics(ytr, ptr), metrics(y[ev], pev), sel, pev


def fit_rff(M, extra, y, tr, ev, ridge=1.0, seed=0, n_out=256):
    from juniper_recurrence_model.readouts import RFFReadout

    r = RFFReadout(n_features_out=n_out, gamma="median", ridge=ridge)
    r.fit(M[tr], extra[tr], y[tr].reshape(-1, 1), random_seed=seed)
    ptr = r.predict(M[tr], extra[tr])
    pev = r.predict(M[ev], extra[ev])
    return metrics(y[tr], ptr), metrics(y[ev], pev), r.ridge, r.gamma, pev


def cmd_base(cache=True):
    seq, arrays = load_full()
    M, extra = memory_block(seq, cache=cache)
    y = seq.y
    fs = folds(len(y))
    print(f"threads env: OPENBLAS_NUM_THREADS={os.environ.get('OPENBLAS_NUM_THREADS')} OMP={os.environ.get('OMP_NUM_THREADS')}  numpy {np.__version__}")
    print(f"X dtype {arrays['X_train'].dtype} full n={len(y)} M shape {M.shape} extra {extra.shape}")
    for i in (0, 4):
        tr, ev = fs[i].train_idx, fs[i].eval_idx
        mtr, mev, _, _ = fit_linear(M, extra, y, tr, ev)
        print(f"linear/0.0 fold {i}: train r2 {mtr['r2']!r} eval r2 {mev['r2']!r}")
    tr, ev = fs[0].train_idx, fs[0].eval_idx
    mtr, mev, lam, gam, _ = fit_rff(M, extra, y, tr, ev)
    print(f"rff/1.0 fold 0: train r2 {mtr['r2']!r} eval r2 {mev['r2']!r} gamma {gam!r}")


def cmd_threads():
    env_base = dict(os.environ)
    for t in ("1", "2", "4", "8"):
        env = dict(env_base)
        env["OPENBLAS_NUM_THREADS"] = t
        env["OMP_NUM_THREADS"] = t
        env["MKL_NUM_THREADS"] = t
        out = subprocess.run([sys.executable, __file__, "base", "nocache"], env=env, capture_output=True, text=True)
        print(f"=== threads={t} ===")
        print(out.stdout.strip())
        if out.returncode:
            print(out.stderr[-2000:])


def cmd_perturb():
    seq, _ = load_full()
    M, extra = memory_block(seq)
    y = seq.y
    fs = folds(len(y))
    for i in (0, 4):
        tr, ev = fs[i].train_idx, fs[i].eval_idx
        base_tr, base_ev, _, _ = fit_linear(M, extra, y, tr, ev)
        print(f"\n--- fold {i}: baseline train r2 {base_tr['r2']:.6f} eval r2 {base_ev['r2']:.3f}")
        for s in range(3):
            mtr, mev, _, _ = fit_linear(M, extra, y, tr, ev, perm=True, seed=s)
            print(f"  row-permutation seed {s}: train r2 {mtr['r2']:.6f} eval r2 {mev['r2']:.3f}  (rel move eval {abs(mev['r2']-base_ev['r2'])/abs(base_ev['r2']):.2e})")
        for nz in (1e-16, 1e-14, 1e-12, 1e-10, 1e-8, 1e-7, 1e-6):
            mtr, mev, _, _ = fit_linear(M, extra, y, tr, ev, noise=nz)
            print(f"  multiplicative noise {nz:.0e}: train r2 {mtr['r2']:.6f} eval r2 {mev['r2']:.3f}  (rel move eval {abs(mev['r2']-base_ev['r2'])/abs(base_ev['r2']):.2e})")
        for rc in (None, 1e-15, 1e-14, 1e-13, 1e-12, 1e-10, 1e-8):
            mtr, mev, _, _ = fit_linear(M, extra, y, tr, ev, rcond=rc)
            print(f"  rcond {rc}: train r2 {mtr['r2']:.6f} eval r2 {mev['r2']:.3f}")
        M32 = M.astype(np.float32).astype(np.float64)
        mtr, mev, _, _ = fit_linear(M32, extra, y, tr, ev)
        print(f"  float32 round-trip of M: train r2 {mtr['r2']:.6f} eval r2 {mev['r2']:.3f}")


def cmd_shuffle():
    """Drift vs rank-deficiency: same-era random train/eval of the same sizes as fold 0 / fold 4."""
    seq, _ = load_full()
    M, extra = memory_block(seq)
    y = seq.y
    fs = folds(len(y))
    rng = np.random.default_rng(0)
    for i in (0, 1, 4):
        tr, ev = fs[i].train_idx, fs[i].eval_idx
        pool = np.concatenate([tr, ev])
        chrono = fit_linear(M, extra, y, tr, ev)
        res = []
        for s in range(5):
            p = rng.permutation(pool)
            rtr, rev = np.sort(p[: len(tr)]), np.sort(p[len(tr) :])
            res.append(fit_linear(M, extra, y, rtr, rev)[1]["r2"])
        print(f"fold {i} (n_train {len(tr)}): chronological eval r2 {chrono[1]['r2']:.2f}; same-pool SHUFFLED eval r2 over 5 draws: {[round(r, 2) for r in res]}")
    tr, ev = fs[4].train_idx, fs[4].eval_idx
    pool = np.concatenate([tr, ev])
    for ridge in (1.0, "gcv"):
        res = []
        for s in range(3):
            p = rng.permutation(pool)
            rtr, rev = np.sort(p[: len(tr)]), np.sort(p[len(tr) :])
            res.append(fit_linear(M, extra, y, rtr, rev, ridge=ridge)[1]["r2"])
        print(f"linear ridge={ridge} raw, shuffled fold-4-size pools: {[round(r, 3) for r in res]} (chronological: {fit_linear(M, extra, y, tr, ev, ridge=ridge)[1]['r2']:.2f})")
    res = []
    for s in range(3):
        p = rng.permutation(pool)
        rtr, rev = np.sort(p[: len(tr)]), np.sort(p[len(tr) :])
        res.append(fit_rff(M, extra, y, rtr, rev)[1]["r2"])
    print(f"rff/1.0 raw, shuffled fold-4-size pools: {[round(r, 3) for r in res]} (chronological: {fit_rff(M, extra, y, tr, ev)[1]['r2']:.3f})")


def cmd_rffseed():
    seq, _ = load_full()
    M, extra = memory_block(seq)
    y = seq.y
    fs = folds(len(y))
    print("rff/1.0 raw, per-fold eval r2 by RFF random_seed (seed 0 = the matrix's only draw):")
    aggs = []
    for seed in range(6):
        r2s = [fit_rff(M, extra, y, f.train_idx, f.eval_idx, seed=seed)[1]["r2"] for f in fs]
        aggs.append(float(np.mean(r2s)))
        print(f"  seed {seed}: {[round(r, 3) for r in r2s]} agg {np.mean(r2s):+.4f}")
    print(f"  aggregate over seeds: mean {np.mean(aggs):+.4f} min {min(aggs):+.4f} max {max(aggs):+.4f} std {np.std(aggs):.4f}")
    print("rff/gcv raw by seed:")
    for seed in range(3):
        r2s = [fit_rff(M, extra, y, f.train_idx, f.eval_idx, ridge="gcv", seed=seed)[1]["r2"] for f in fs]
        print(f"  seed {seed}: {[round(r, 3) for r in r2s]} agg {np.mean(r2s):+.4f}")


def cmd_embargo():
    seq, arrays = load_full()
    M, extra = memory_block(seq)
    y = seq.y
    n = len(y)
    n_tv = arrays["X_train"].shape[0] + arrays["X_val"].shape[0]
    print(f"full n={n}; train+val n={n_tv}")
    for label, nn, emb in (("as-measured embargo 2, full", n, 2), ("embargo 64 (>= lookback), full", n, 64), ("embargo 2, test EXCLUDED (train+val only)", n_tv, 2), ("embargo 64, test EXCLUDED", n_tv, 64)):
        fs = folds(nn, embargo=emb)
        out = {}
        for name, fn in (("rff/1.0", lambda f: fit_rff(M, extra, y, f.train_idx, f.eval_idx)[1]["r2"]), ("rff/gcv", lambda f: fit_rff(M, extra, y, f.train_idx, f.eval_idx, ridge="gcv")[1]["r2"]), ("linear/0.0", lambda f: fit_linear(M, extra, y, f.train_idx, f.eval_idx)[1]["r2"])):
            r2s = [fn(f) for f in fs]
            out[name] = (r2s, float(np.mean(r2s)))
        sizes = [(len(f.train_idx), len(f.eval_idx)) for f in fs]
        print(f"\n{label}: fold sizes {sizes}")
        for k, (r2s, agg) in out.items():
            print(f"  {k}: {[round(r, 3) if abs(r) < 100 else round(r) for r in r2s]} agg {agg:+.4f}")


def cmd_dates():
    seq, arrays = load_full()
    from juniper_recurrence_model.data import derive_full_split

    full = derive_full_split(arrays)
    wed, dates, tdt = full["window_end_date_full"], full["date_full"], full["target_dt_full"]
    print("window_end_date strictly increasing over the full view:", bool(np.all(np.diff(wed.astype("int64")) > 0)))
    fs = folds(len(seq.y))
    for i, f in enumerate(fs):
        lt, fe = f.train_idx[-1], f.eval_idx[0]
        print(f"fold {i}: last train window end {wed[lt]} (target_dt {tdt[lt]}), first eval window end {wed[fe]} (target_dt {tdt[fe]}); eval first step {dates[fe][0]} <= last train end? {dates[fe][0] <= wed[lt]}; shared days {np.intersect1d(dates[lt], dates[fe]).size} of {dates.shape[1]}")
    ntr, nva = arrays["X_train"].shape[0], arrays["X_val"].shape[0]
    print("train partition ends", wed[ntr - 1], "val ends", wed[ntr + nva - 1], "test ends", wed[-1])
    print("fold 4 eval date range", wed[fs[4].eval_idx[0]], "->", wed[fs[4].eval_idx[-1]], "; test partition range", wed[ntr + nva], "->", wed[-1])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "base"
    if cmd == "base":
        cmd_base(cache=(len(sys.argv) < 3 or sys.argv[2] != "nocache"))
    else:
        globals()[f"cmd_{cmd}"]()
```

`scenario_b_diff.py` (B.7):

```python
import hashlib, io, sys
import numpy as np
sys.path.insert(0, ".")
import cvattack as A
from juniper_recurrence_model import sequence_data_from_arrays

NPZ_A = A.NPZ  # scenario-a copy == 10-04 arrays per the note (checksum c02004e1)
NPZ_B = "/home/pcalnon/Development/python/Juniper/juniper-ml/.amp/in/scratch/data-store/equities_seq-6.0.0-15505731cba5b86d.npz"  # scenario-B store (checksum 037baab7)

def load(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}

a, b = load(NPZ_A), load(NPZ_B)

def checksum(arrays):  # identical to juniper_data.core.artifacts.compute_checksum
    buf = io.BytesIO(); np.savez(buf, **{k: arrays[k] for k in sorted(arrays)}); buf.seek(0)
    return hashlib.sha256(buf.read()).hexdigest()

print("checksum(A):", checksum(a)[:8], " checksum(B):", checksum(b)[:8])
feats = ["open", "high", "low", "close", "volume", "week52_high", "week52_low", "total_shares", "market_cap", "cost_basis", "dividend", "split_ratio", "days_since_week52_high", "days_since_week52_low", "days_since_report"]
for k in sorted(a):
    if not np.array_equal(a[k], b[k]):
        d = a[k] != b[k]
        print(k, int(d.sum()), "cells differ; columns", [feats[i] for i in np.flatnonzero(d.any(axis=(0, 1)))] if a[k].ndim == 3 else "")
seqB = sequence_data_from_arrays(b, "full"); MB, EB = A.memory_block(seqB, cache=False); fs = A.folds(len(seqB.y))
for i, f in enumerate(fs):
    mtr, mev, _, _ = A.fit_linear(MB, EB, seqB.y, f.train_idx, f.eval_idx)
    print(f"linear/0.0 fold {i}: train r2 {mtr['r2']:.9f} eval r2 {mev['r2']:.3f}")
print("rff/1.0 per fold", [round(A.fit_rff(MB, EB, seqB.y, f.train_idx, f.eval_idx)[1]["r2"], 4) for f in fs])
print("rff/gcv per fold", [round(A.fit_rff(MB, EB, seqB.y, f.train_idx, f.eval_idx, ridge="gcv")[1]["r2"], 4) for f in fs])
```

Also run inline (B.1, B.5, B.6): the per-fold noise-model decomposition over `21-matrix-cells.json`, the fold-to-partition overlap arithmetic over `20-matrix-datasets.json`, and the SVD rank of the raw vs column-standardised fold designs; all reproducible from the snippets' descriptions in Appendix B.

## Appendix B — Computation results

**B.1 — `21-matrix-cells.json` / HTTP responses (no model runs).** `theta_resolved` = 91.0 in 120/120 folds. GCV at the grid ceiling in 30/40 folds (15/20 distinct). HTTP vs in-process eval r², fold 0 … 4, `linear/0.0/off`: −93606.2421298088 vs −93606.2310410387; −798.4669029752575 vs −798.4669485637338; −3.696331338492504 vs −3.6963308841699014; −75.61767366018817 vs −75.6176726299507; −7239.1656160853 vs −7239.165196453074 (relative 1.2e-7 / 5.7e-8 / 1.2e-7 / 1.4e-8 / 5.8e-8). Audit (10-03) vs HTTP (10-04) train r² relative moves 6.2e-4 / 2.6e-4 / 2.3e-3 / 5.3e-4 / **1.7e-2**; eval 1.2e-1 / 2.0e-2 / 6.3e-3 / 3.7e-2 / 1.9e-1. Noise-model decomposition for `rff/1.0/off`: measured r² vs −(pred_std² + (pred_mean − target_mean)²)/target_std² per fold: −0.080 vs −0.201 (implied 2·cov/SST +0.121, ρ ≈ 0.16); −0.050 vs −0.093 (+0.043); −0.102 vs −0.078 (−0.024); −0.086 vs −0.076 (−0.009); −0.258 vs −0.230 (−0.028). GCV cells equal the train-mean-on-eval r² (−0.051 / −0.008 / −0.001 / −0.007 / −0.001) to ≤ 0.008. Train r² for `rff/1.0/off` falls 0.184 → 0.124 as n grows 281 → 1413 (over-fit signature). Dropping fold 0: sane aggregate −0.124; defaults aggregate −2,029.

**B.2 — thread count (fresh process each, memory block recomputed).** `linear/0.0` fold 0 eval r²: 1 thread −93606.338; 2 −93607.147; 4 −93570.752; 8 −93606.242 (= HTTP bit-for-bit). Fold 4: −7239.247 / −7238.672 / −7239.351 / −7239.953. `rff/1.0` fold 0: −0.0802741034743{5615,5682,5637,5726}. Max relative move: fold 0 3.9e-4, fold 4 1.8e-4.

**B.3 — perturbations (`linear/0.0`).** Fold 0 (baseline −93606.242): row permutation −95899 / −94166 / −92895 (0.6–2.5 %); multiplicative noise 1e-16 … 1e-6 on the train design: −96427 / −96072 / −97221 / −96633 / −96711 / −95622 / −94491 (1–4 %, non-monotone); float32 round-trip −99259 (6 %); `rcond` 1e-15 / 1e-14 / 1e-13 / 1e-12 / 1e-10 / 1e-8: −5.8e6 / −41240 / −24482 / −71.2 / −3.95 / −2.05 (train r² 0.634 / 0.535 / 0.442 / 0.362 / 0.185 / 0.174). Fold 4 (baseline −7239.166): row permutation ≤ 5e-5; noise ≤ 1.6e-4; float32 round-trip −7239.118 (7e-6); train r² moves < 1e-5; `rcond` 1e-14 / 1e-13 / 1e-12 / 1e-10: −3744 / −3425 / −3956 / −63.5.

**B.4 — shuffled same-era split (drift removed).** Table in F2. Additionally `linear/0.0` fold-1 sizes: chronological −798.47 vs shuffled −0.39 / −0.33 / −0.18 / −0.15 / −0.37.

**B.5 — partition overlap (arithmetic over `20-matrix-datasets.json`).** Full view = train 0–1345 | val 1346–1521 | test 1522–1697. Eval rows per fold in (train, val, test): f0 (283,0,0); f1 (283,0,0); f2 (283,0,0); f3 (214,69,0); **f4 (0,107,176)**. Gap between last train and first eval window: 3 windows in every fold. Drift fractions for `rff/1.0/off` (eval rows with any memory column > 5 σ / > 10 σ of the train fold): f0 0.70/0.19; f1 0.69/0.65; f2 0.28/0.00; f3 0.82/0.25; f4 1.00/1.00.

**B.6 — rank vs column scale.** Fold 0 raw design: σ_max 2.8e12, eps-rank 113/242, 194 singular values < 1e-8·σ_max; **column-standardised: σ_max 142, rank 226/242**, 36 < 1e-8 rel; exactly-constant memory columns: 16 (feature 11 `split_ratio`). Fold 4 raw: rank 161/242; **standardised: rank 242/242**, 10 < 1e-8 rel; constant columns 0. Per-feature memory-column std, fold 0: f4 `volume` 2.2e7–5.3e7, f7 `total_shares` 1.2e7–2.2e8, f8 `market_cap` 1.4e9–1.6e10, f9 `cost_basis` 0.046–1.02, f10 `dividend` 1.8e-4–5.7e-3, f11 `split_ratio` 0–0, prices 0.2–2.3.

**B.7 — Scenario-B artifact.** `checksum(A)` = `c02004e1` (recomputed; same as 10-03 09:14Z and 10-04 21:06Z), `checksum(B)` = `037baab7`. Keys/shapes identical. Differences: `X_train` 1,367 cells, `X_val` 244, `X_test` 178 — all in `dividend` (A 0.16–0.22, B 0) plus 64 `X_val` cells in `split_ratio` (A 4.0, B 0). `linear/0.0` on B: fold 0 train 0.452957979 / eval −83451.610; f1 −814.665; f2 −3.720; f3 −78.492; f4 train 0.137595904 / eval −6059.229; aggregate −18081.543 (every digit of `24-c-crossval-shadow.txt`). `rff/1.0` on B: −0.070 / −0.029 / −0.116 / −0.104 / −0.188, aggregate −0.101. `rff/gcv` on B: aggregate −0.015.

**B.8 — dates.** `window_end_date` strictly increasing over the full view. Every fold: first eval window's first step date < last train window's end date; shared days 61/64. Train partition ends 2020-08-06, val 2021-04-20, test 2021-12-29; fold-4 eval 2020-11-13 → 2021-12-29. Target = next-day log return (`target_dt` 1–3 days).

**B.9 — embargo / population.** (`rff/1.0`, `rff/gcv`, `linear/0.0` aggregates) as measured: −0.1153 / −0.0145 / −20,345; embargo 64, full: −0.1534 / −0.0165 / −61,051; embargo 2, test excluded (n = 1,522): −0.1014 / −0.0059 / −17,365; embargo 64, test excluded: −0.1105 / −0.0086 / −32,492.

**B.10 — RFF seed sweep (`rff/1.0`, raw, embargo 2, full).** Seed 0: [−0.080, −0.050, −0.102, −0.086, −0.258] −0.1153; seed 1: [−0.166, −0.077, −0.059, −0.044, −0.307] −0.1305; seed 2: [−0.219, −0.022, −0.127, −0.077, −0.185] −0.1260; seed 3: [−0.190, −0.046, −0.125, −0.056, −0.350] −0.1533; seed 4: [−0.123, −0.112, −0.151, −0.032, −0.362] −0.1557; seed 5: [−0.389, −0.134, −0.124, −0.054, −0.558] −0.2518. `rff/gcv` seeds 0–2: −0.0145 / −0.0131 / −0.0132.
