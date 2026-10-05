# Juniper-Recurrence × Equities — Consensus Validation of the CV Blow-up Investigation (W5.1 note)

- **Project**: Juniper — juniper-recurrence (with juniper-data, juniper-data-client, juniper-recurrence-model, juniper-model-core, juniper-ml experiment stack)
- **Author**: Paul Calnon
- **Date**: 2026-10-05
- **Status**: Validation complete after three rounds (3 Lane A + 2 Lane B; 1 + 1 on the corrections; 1 Lane A on the round-2 keys); the W5.1 note is **upheld with corrections** at v1.1.2 — verdict GO and the R5 band numbers unchanged throughout, the explanatory layer rewritten twice. Owner decisions left: §9. Nothing committed by this review itself; the plan carries the consequences at v1.4.0.
- **Validates**: [`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`](JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md) (v1.0.0) — the W5.1 cause-investigation note that issues the P5 go/no-go (**GO**) and the R5 band recommendation for the plan [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md) (v1.3.0)
- **Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) (§2 lanes, §3 sizing, §4 iteration, §5 reconciliation, §7 minimum record)
- **Precedent followed**: [`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`](JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md) (the plan's own two-round validation)
- **Agent reports**: `reports/2026-10-05_recurrence-equities-cv-consensus/{laneA1,laneA2,laneA3,laneB1,laneB2}.md` (round 1), `{laneA1-r2,laneB1-r2}.md` (round 2), `laneA1-r3.md` (round 3); Lane A3's fresh measurement under `laneA3-rerun/` (its sixteen `*.log` stack and probe logs are git-ignored repo-wide and live only on the host; the JSON and markdown evidence is committed); the reconciler's re-derivations `reconciler-rederive.json`, `reconciler-rederive-b1.json`, `reconciler-rederive-b1r2.json`
- **Evidence under review**: `reports/2026-10-04_recurrence-equities-cv-matrix/` (the note's evidence tree, 8 files + `scenario-a-rerun/`); instruments `util/ad-hoc/2026-10-04_recurrence_equities_cv_matrix.py`, `util/ad-hoc/2026-10-04_recurrence_equities_linear_conditioning.py`

---

## 1. Why this ran

The plan's W0.9 row says the go/no-go is "reviewed under the consensus procedure before R5 is ruled", and the note's own Status line says it has not been. The note is a document of record for six repositories: it closes finding F-SCI1 ("cause unresolved" → candidate (a) confirmed), issues the verdict that fixes the content of P5, proposes two plan items (W5.8 `default_ridge`, W5.9 GCV grid), fixes the W1.1(a) bundle, and recommends the R5 acceptance band (`cv_r2 ∈ [−1.0, +0.5]`, `mode: gate`).

Under §3 of the procedure that is **high criticality × high uncertainty**, and every escalator fires: the conclusion overturns a standing paragraph of record (F-SCI1), the sample is one ticker / one window / one seed / five folds, both instruments are new ad-hoc scripts, the note carries universal quantifiers ("every ridge = 0.0 cell", "theta 91.0 in every fold", "all 28 keys"), fixes and a ruling hang on it (W5.8, W5.9, R5), and the finding is convenient — it confirms the candidate the plan's author listed
first. The one de-escalator in the procedure (independent end-to-end reproduction by a different instrument) applies only to the two cells both the HTTP route and the in-process fit ran, and to the E-H aggregate the suite path reproduced; the other 22 cells and the conditioning analysis rest on one instrument each. The top-right cell therefore applies: three or more Lane A agents with distinct entry points, two or more Lane B agents with opposing briefs, and at least two iterations.

---

## 2. Instrument and sample (as the note states them; the lanes test this)

| Instrument | Could it have produced a different answer? | Sample |
| --- | --- | --- |
| `POST /v1/crossval` through the per-run stack (`replay` mode): the E-H body and the bare body on one frozen `dataset_id` | Yes — the two bodies returned −0.115 and −20,345 on the same artifact, so the route distinguishes configurations | 2 requests, 5 folds each, 1 ticker (AAPL 2015–2022), 1 seed |
| In-process matrix (`matrix` mode) through `build_lmu_regressor` → `LMURegressor.fit` / `predict` over model-core `walk_forward_folds` | Yes — 24 cells span five orders of magnitude; fidelity to the route checked on the two shared cells only | 24 cells × 5 folds, 2 artifacts (raw / producer-normalised), 1 ticker, 1 seed, `d = 16` |
| SVD of the rebuilt linear design (`linear_conditioning` script) | Yes — rank and condition number are computed, not assumed; but it is the only instrument behind §2.4 and it rebuilds the design rather than reading the solver's | 5 folds × 2 artifacts |
| Suite path (`run_suite.py` Scenario-A re-run) | Yes — the audited run recorded `succeeded` + `exit 1` + `metrics: {}`; the re-run recorded `cv_r2 −0.1153` | 1 run, 2 cells |

---

## 3. Lanes, agents and entry points

| Round | Lane | Agent | Entry point | Brief |
| --- | --- | --- | --- | --- |
| 1 | A | A1 | the evidence tree only (`reports/2026-10-04_recurrence-equities-cv-matrix/`); no source, no re-run | re-derive every number and quantified claim in §0–§4 from the JSON/CSV/JSONL; all 24 cells, not the 12 the note prints |
| 1 | A | A2 | source only (recurrence app + model, model-core as installed, juniper-data, data-client, the two instruments, the suite YAML chain); the evidence tree not opened | re-derive every claim about code behaviour and what each instrument measures; line-by-line fidelity of the in-process path to the route |
| 1 | A | A3 | a fresh per-run stack: re-run `replay`, `matrix` and the conditioning script into `laneA3-rerun/`; numpy checks that bypass both instruments (`sum(dt)` medians, target stats, byte comparison against the audit's archived NPZ) | which digits reproduce, which reproduce only in class, and whether the note's §2.4 reproducibility prediction held |
| 1 | B | B1 | note + plan §3.9 / P5 gating + source | refute; lens **correctness / omission**; steelman NO-GO / INCONCLUSIVE |
| 1 | B | B2 | note §3–§4 + plan R5 / R6 / W5.4 / W1.1 / W5.8 / W5.9 + the matrix JSON | refute; lens **actionability / decision consequences / self-serving framing**; accept the measurements, attack every recommendation |

Round-2 agents (A1-r2, B1-r2) are briefed on the corrections round 1 forces, not on the whole note, and are not given the round-1 reports.

Round-1 tallies: A1 67 confirmed / 26 partial / 2 refuted / 19 no artifact (114 claims); A2 39 confirmed / 2 partial / 3 refuted / 5 not found (49); A3 17 confirmed / 5 partial / 2 refuted / 3 could-not-run (fresh stack `20261005T132907Z-5493`: both replays, all 24 cells and all 10 conditioning rows **bitwise identical** to 2026-10-04; refuted the F-P8 mechanism and §1.3's "same arrays" independently; the §2.4 "digits move between runs" prediction did not hold, 0 of 6 groups moved); B1 0 FATAL / 7 MAJOR /
10 MINOR / 6 UNTESTED; B2 2 FATAL / 9 MAJOR / 6 MINOR.

Round-2 (on v1.1.0): A1-r2 68 confirmed / 10 partial / 2 refuted / 10 no artifact over 90 claims — both refutations were introduced by the fix pass (`X_val` dividend cells 180, not 244; "fold 4 is the worst fold in every sane cell" true only for the rff/1.0 cells) and three internal contradictions (solve-vs-r² wording in §2.4; mint-B −0.101 vs train+val-only −0.101 counted as two survivals; "null model" overstated for fold 0) — all applied to v1.1.0 the same day. B1-r2 0 FATAL / 10 MAJOR / 10 MINOR / 14
groups held / 4 untested (§5). Round 3 (on v1.1.1): A1-r3 42 confirmed / 1 partial / 1 refuted / 1 n/a over 45 checks — one parenthetical number changed, no disposition (§5, last paragraph).

**Reconciler re-derivations** (procedure §5.2 — a lone finding is a lead until re-derived): every load-bearing finding that only one lane reported was recomputed through the model's own readout functions on the frozen artifact: `util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive.py` (B2's standardised-linear and GCV-versus-null cells) and `util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive_b1.py` (B1's two-artifacts finding, rank-versus-scale, partition overlap, RFF seed sweep,
shuffled split), outputs `reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive.json`, `reconciler-rederive-b1.json` and (round 2) `reconciler-rederive-b1r2.json`. Every one reproduced to the printed digits; none was dropped or softened.

---

## 4. Round 1 — what v1.0.0 got wrong (→ v1.1.0)

### 4.1 Measurement disputes, settled by opening the artifact

1. **The audited digits reproduce exactly; the two days measured two different artifacts served under one `dataset_id`** (B1 F1; re-derived). The audit ran two stacks on 2026-10-03. Scenario A's data service minted `equities_seq-6.0.0-15505731cba5b86d` at 09:14:24Z with checksum `c02004e1…` — the copy the note byte-diffed, and it is indeed byte-identical to the 2026-10-04 mint. Scenario B's data service (`.amp/in/scratch/data-store/`) minted the same id 85 s later at 09:15:49Z with checksum `037baab7…`, and
   **that** is the artifact `24-c-crossval-shadow.txt` (the −18,081) was solved on. The two differ in exactly two feature columns: `dividend` (index 10) is all zero in B across all three partitions (A: 0 … 0.22; 1,367 + 244 + 178 cells), and `split_ratio` (index 11) is zero in B's `X_val` where A carries the 2020-08-31 4:1 split (64 cells). Mechanism, from the producer: `equities/generator.py` zero-fills `dividend` / `split_ratio` when yfinance's response omits the action columns ("absent means none
   happened"), so a transiently incomplete fetch is served, silently, under the same id. Re-solving `linear / ridge 0.0` on the B arrays gives −83,451.610 / −814.665 / −3.720 / −78.492 / −6,059.229, aggregate **−18,081.543** — every audited digit. Consequences: the note's §1.3 ("same arrays … decided by rounding"), §2.4's rounding paragraph and §4's "rounding artefacts" are wrong; the "first reading" the note rejected ("the equities data drifted under the same id") was right; and F-P8's mechanism is wrong
   twice over — `compute_checksum` is content-deterministic (A2: sorted keys, uncompressed `np.savez`, sha256; numpy writes fixed 1980-01-01 zip timestamps; `c02004e1` has now been reproduced on three days), so a different checksum meant different content. Within one environment the ill-conditioned solve reproduces **bit-for-bit** across processes (A1: per-fold `mse` / `rmse` / `mae` identical between the HTTP service and the in-process script in all ten folds of both configurations; B1: an 8-thread rerun
   equals the HTTP digits exactly, and thread count / row order / ulp noise move fold 4 by ≤ 1.8e-4). **F-P8 is re-filed as a Major DATA finding** (the id does not pin content; the producer zero-fills absent action columns silently) with a work item in W5.7's territory, and the class does not change (rff/1.0 on the B arrays −0.101; rff/gcv −0.015).
2. **Arithmetic and units** (A1): "four hundred million times worse" is 2.1e8; "a 980 % one-day move" reads a `log_return` of 9.81 as a simple return (e^9.81 ≈ 18,000×); "the sane class sits in [−0.26, +0.00] per fold … across the four sane cells" — there are **five** in-band configurations (rff/1.0 ×2 normalisations, rff/gcv ×2, linear/gcv/on) with a per-fold floor of −0.2765 (rff/1.0/on fold 4) and five different aggregates; "below −1 by three or more orders of magnitude" is 2.4 decades for linear/gcv/off
   (−247) and **0.66 decades for linear/1.0/on (−4.52)** — the −1 cut still separates all 24 cells (nearest non-sane −4.52, lowest sane −0.142, a 32× gap); rff/gcv/off prints −0.015 not −0.014; fold-1 target std is 0.013; "identical to every printed digit" is fold 0 −93,606.24 (HTTP) vs −93,606.23 (in-process) — the route's scorer casts `y` to float64 and the script's does not (A2 D1), a 1e-7 relative formula difference on an exactly reproduced solve; the registry's `n_windows 1346` is the train partition
   while the CV ran on 1,698.
3. **Code and instrument claims** (A2; B1 F5; re-derived): producer `normalize_features` is **min-max to [0, 1]** fitted on the pooled train rows, not z-scoring; the §2.4 "weak-direction amplification" column takes the ten smallest singular directions (indices 232–241 of 242) and every reported rank is ≤ 226, so all ten lie below `lstsq`'s cutoff and are discarded — the column is an out-of-support indicator, not "what the min-norm solution does"; σ_max/σ_min is κ₂ including the rounding floor, not the
   amplification of the retained system; the constant memory columns are **`split_ratio`** (16 columns, folds 0–3; zero until the 2020 split), not `cost_basis` / `total_shares`; and the "rank deficiency by a third to a half" is a **column-scale artefact** of the relative cutoff under a σ_max set by `market_cap` / `total_shares` / `volume` (1e7–1e12): the same fold-0 design column-standardised has rank 226 / 242 and fold 4 has **full rank 242**. The mechanism survives in corrected form — `lstsq`'s relative
   cutoff, dominated by three huge-scale feature blocks, truncates ~130 directions carrying nearly all the price information, and the retained weak directions are then extrapolated — which is exactly why column scaling is part of any fix. Also: the "irregular-sine YAML pins 0.0 explicitly" refers to the `service:` block (line 20), and that YAML is the E-H suite's `base_config`, so changing `Settings.default_ridge` alone would not change what a bare request to an E-H-launched stack receives.

### 4.2 Interpretation disputes (Lane B), with the reconciler's decision

4. **Cause attribution** (B1 F2; re-derived). `ridge = 0` is neither necessary — ridge 1.0 (−2,064) and GCV (−247) on the raw linear rung also blow up — nor sufficient: a same-pool **shuffled** split of fold-4 size, identical design and solver, scores −0.33 / −0.001 / −0.08 against the chronological −7,239. The cause is the conjunction of a linearly-extrapolating readout on an unscaled design and eval rows 8–199 σ outside the train support; `ridge = 0` sets the magnitude. Decision: §2.3(a) becomes
   "necessary amplifier, not sole cause"; every matrix cell is chronological, so the matrix cannot separate (a) from the drift the plan listed under (b) and (d), and the note must say so.
5. **"(d) not implicated"** (B1 F4, B2 F2; re-derived). "The only rung that standardises per fold is the one that works" is false in both directions on the note's own table (rff/0.0 standardises and scores −1,986; linear/gcv/on does not and scores −0.015). The RFF rung is sane because `cos()` bounds its features and the penalty shrinks them — the standardised linear rung at the same ridge 1.0 scores **−192**. Decision: (d) stays "not implicated" on the strength of the control (irregular sine `cv_r2 0.975`
   through the same route) and the in-support result (rff/1.0 shuffled ≈ −0.05, bounded), not on that sentence; "standardisation is part of the remedy" is reworded to "standardisation is necessary but not sufficient".
6. **"(b) refuted as the lever"** (B1 F9/F10; re-derived). The RFF projection seed is hard-wired to 0 (`LMURegressor(random_seed=0)`; the factory never passes one), and across seeds 0–5 the rff/1.0 aggregate is −0.115 / −0.131 / −0.126 / −0.153 / −0.156 / −0.252 (std 0.045; the matrix's draw is the best of six). The raw-vs-normalised delta (0.027) is below that floor, so it supports no direction. Decision: "refuted" is kept for the blow-up lever (normalisation makes ridge 0 worse by 2.1e8×) and dropped as
   evidence for the sane cell; "gives no reason to turn it on" stands.
7. **W5.8** (B2 F1/F2, B1 F3; re-derived through the model's own `_gcv_select`, `_ridge_solve`, `_standardize_fit`). Option (i) alone: −247 on the shipped grid, −35 with the grid extended to 1e12, and GCV(λ→∞) — the intercept-only model — is below every finite grid point in all five folds. Option (ii) alone: −192. Both together: −0.195 (λ pinned to 1000 in every fold) or −0.019 as the null model once the grid is extended. Decision: the note's preferred option is a measured failure and the "and/or" in the
   plan's W5.8 row becomes "and"; the evidence supports (A) a default **readout** of rff/1.0 (the only in-band configuration that retains fit, train r² 0.12–0.18) or (B) `gcv` **and** per-fold standardisation, both preceded by the selected λ / null-model flag in the response; (ii) must not alter the ridge = 0 path (the bench's conformance baseline); the irregular-sine YAML `service.default_ridge` must change in the same PR; canopy forwards only `d` / `theta` / `ridge` and cannot select RFF (`main.py:932`),
   so for canopy the default is the only fix.
8. **W5.9** (B2 M3; re-derived). GCV's optimum on the RFF rung is the null model in folds 0, 3 and 4 (extended argmin at the 1e12 edge, or 2.0e5 with GCV within 4e-9 of the null value); folds 1 and 2 are interior at 398 / 63. No grid extension makes "re-run off the ceiling" satisfiable. Decision: W5.9 becomes "detect and report a null-model / at-ceiling selection" (model WARNING plus a flag in the crossval / train response); the note's "the GCV-optimal penalty is unknown" becomes "it is the null model".
9. **The R5 band** (A1 items 106–110; B2 M1 / M2 / F3 / m1 / m2; B1 F7 / F8 / F9; re-derived). `cv_r2 ∈ [−1.0, +0.5]` with `mode: gate` **survives every re-measurement**: six RFF seeds (worst aggregate −0.252, worst fold −0.558), embargo 64 (−0.153), the `test` partition excluded (−0.101), the Scenario-B arrays (−0.101), and in-support (≈ −0.05). What changes: the margin sentence (the nearest defect is 4.5× below the bound, the sane cells 7× above it); a single catastrophic fold is diluted 5× by the
   aggregate, so a fold down to −4.6 would pass — the existing headline `cv_r2_std ≤ 0.5` closes that (sane 0.018–0.074; linear/1.0/on 8.75); the `train_r2 ≤ 0.9` row is dropped — it keys on the train-phase r² at n = 1,346 where no defective configuration exceeds 0.229, so it can never fire, and even on fold 0 it misses the audited configuration (0.453); +0.5 is labelled a prior; the R6 argument is a category error (a band failure is a science result in R6's own taxonomy) and is replaced by the structural
   argument (prediction std ≤ 0.51× target in every sane fold, 12 fold-stds of headroom) plus the fact that since W0.3 the suite already exits non-zero on any failed / degraded cell; the band is row-scoped (the control row's 0.975 would fail +0.5). Two omissions become statements of record: **fold 4's eval is the entire `test` partition plus 107 `val` rows** (so W5.3's "test is touched once" is already void for any full-view CV run, and W5.2's train+val pool is a different population — re-measure the band
   there), and embargo 2 against a 64-step look-back leaves 61 of 64 days shared across every fold boundary (no target leakage — the target is next-day; ≈ 0.04 of optimism).
10. **The W1.1(a) bundle** (B2 M4 / M5, B1 F11). "(or `gcv` once W5.9 lands)" is deleted — `gcv` is the null model on this rung regardless of the grid; `ridge: 1.0` is kept with its reason stated (retains fit; `gcv` abstains). The measured configuration used `fundamentals_fill: nan` (the generator default) while the bundle says `drop`; because the fill is hashed into the id, a reader following the bundle mints a different `dataset_id` and cannot cross-check `15505731cba5b86d`. For AAPL 2015–2022 every array
    is finite so `drop` has nothing to drop and the rows are expected to be identical — **UNTESTED** (needs a data service). The bundle must also list `d: 16`, `n_folds: 5`, `scheme: expanding`, `embargo: 2`, `lookback: 64`, the dataset seed 20260807 and the RFF seed 0.
11. **§3.2 item 3** (B2 M8): per-fold θ / λ / γ in the crossval **response** is in no work item (W2.4 is the model's logs). Decision: extend W2.4 or add W5.10; the band and any null-model flag depend on it.
12. **§3.2 item 4 / F-P8** (B2 m3): a fork, not an action — resolved by item 1 (re-filed as a producer finding with a work item).
13. **Framing** (B2 census; B1 F12–F16): "the efficient-market ceiling" is an interpretation — the in-support rff/1.0 result is also ≈ −0.05, so the honest sentence is "these features with this readout carry no demonstrable next-day signal"; "tuning-and-documentation" becomes "documentation and defaults hardening"; "24 cells" is 12 distinct (the theta axis is degenerate by construction); theta was never varied, so "theta is not a lever" is scoped to "theta does not differ between folds"; "same measurement"
    is withdrawn (item 1).

---

## 5. Round 2 — what the v1.1.0 fix pass got wrong (→ v1.1.1)

Round 2 was briefed on the corrections only, with the round-1 reports withheld. Lane A1-r2 re-derived 90 claims the fix pass added or changed (68 confirmed / 10 partial / 2 refuted / 10 no artifact); Lane B1-r2 attacked the corrections (0 FATAL / 10 MAJOR / 10 MINOR / 14 groups held / 4 untested). **The GO verdict and both band numbers survived round 2 untouched** — B1-r2 computed the per-seed `cv_r2_std` (0.071–0.191) and found no seed on which the new `≤ 0.5` gate false-fails. What did not survive was, as
the procedure warns, the fix pass itself:

1. **A universal introduced by the fix** (A1-r2, B1-r2 F1): "fold 4 is the worst fold in every sane cell" is true for the two rff/1.0 cells only — in all three GCV cells fold 0 is worst and fold 4 best. Corrected the same day (v1.1.0 text).
2. **Seven numbers with no artifact** (A1-r2 "no artifact" list; B1-r2 F2): the train + val-only cells, the embargo-64 cells, the RFF rung in-support, the mint-B rff numbers, rff/gcv per seed, the row-order / float32 probes and the `total_shares` CV came from Lane B1's appendix, not from any instrument the note declares — and the same value −0.101 was quoted for two different conditions. Resolution: `util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive_b1r2.py` → `reconciler-rederive-b1r2.json`
   (F10–F16) puts an artifact behind each; v1.1.1 cites the keys and disambiguates the two −0.101 values.
3. **The cause statement over-reached the other way** (B1-r2 F3 / F4): "the cause is extrapolation under drift" re-elevated the plan-consensus-withdrawn candidate (b) while every remedy acts on (a); and the shuffled control that supported it has no embargo, so it removed drift **and** inserted 61-of-64-day near-duplicate rows — it can show "in-support" but not "drift". Resolution: an embargoed in-era block control was added (F15: eval = fold 2's 283-window block inside fold 4's training era, a 64-window
   embargo on both sides, 1,002 training rows — linear ridge 0 −1.8, ridge 1.0 −2.3, GCV −0.42, rff/1.0 −0.081, rff/gcv −0.006, against −3.70 for the chronological fold with the same eval block; the 10³–10⁴ catastrophes are the era-boundary folds 0 and 4); F-SCI1's statement becomes "the service-default readout applied to a chronologically drifting input — both necessary, neither separated by this matrix; the actionable lever is the default", and (b) stays withdrawn as a hypothesis of record.
4. **(d) re-based on a non-discriminating control** (B1-r2 F5): the irregular-sine control is stationary, so it shows the route and configuration are sound on a stationary signal and does not test a drift-conditioned defect; the RFF in-support number it leaned on had no artifact (now F12 / F15). v1.1.1 scopes the sentence accordingly.
5. **The W5.8 option table ranked on a criterion the owner did not set** (B1-r2 F6 / F7): "retains a fit" is in-sample, option (A) was quoted at the best of six seeds, the RFF rung's own default (gcv, −0.015, in band) was absent from the table, and (A) needs a `Settings.default_readout` that does not exist and changes what canopy is served. Resolution: (A) is filed as its own proposal (**W5.11**) with the seed-mean quoted; W5.8 is (B) gcv **and** standardisation, gated on W5.10; the rff/gcv row is in the
   table.
6. **The structural gate argument contradicted §1.1** (B1-r2 F8): "the only way the row can breach the bound is a configuration or code change" — F-P8 is a third way (an upstream data change under the same id), and "12 fold-stds above −1.0" is seed 0's dispersion (3.9 at seed 5). Resolution: three ways named, W5.7's `actions_present` guard distinguishes the third; the fold-std statistic is dropped.
7. **The "wrong columns" correction was itself half wrong** (B1-r2 F9; re-derived from Lane A3's `30-numpy-checks.json` and F16): `cost_basis` **is** an exactly-constant raw feature (27.3325 over every window and step; the one zero-std column); its sixteen memory columns vary only with the `dt` sequence. v1.0.0 was right about `cost_basis` and wrong about `total_shares` (CV 0.63); v1.1.0 inverted both.
8. **§3.5 omitted what the new facts move in the plan** (B1-r2 F10): release placement of W5.8 / W5.10 (recurrence 0.6.0 is W1.13's P1 publication, W5.8 is P5 after M1 — one of them moves; the model halves cannot ship in "0.4.x"), the W5.2 → W5.4 re-measurement edge, the W5.2 → W5.3 held-out-`test` dependency, and the plan paragraphs still carrying withdrawn claims. Resolution: plan v1.4.0 carries all four.
9. **Minors** (B1-r2 F11–F20; A1-r2 contradictions): the leak sentence in §3.4 contradicted §2.3(b); the ≈ 0.04 overlap effect is below the note's own noise floor; fold 0's GCV optimum is "effectively" null (λ ≈ 2e5), not λ → ∞; §1.1 asserted a transient-fetch mechanism §4 calls unknown; the F-P8 framing conflated the request-addressed design with the defect (an incomplete response indistinguishable from a complete one); "tuning" → "documentation and defaults hardening" is the note's gloss, not a rewrite of
   the plan's gating definition; `t+5` is `t+4`; a double negative; the 0.229 figure is a matrix fold-4 value, not a train-phase run; "never exceed |0.021|" is seed 0 only. All applied in v1.1.1.

Round 2 changed wording, one plan item's placement and the provenance of seven numbers; it changed **no measured number and no disposition** (GO; the two bands; F-P8 Major; W5.8's measured options). Per procedure §4 a round 3 was owed because round 2 produced corrections. **Round 3 (Lane A1-r3, 45 checks: 42 confirmed / 1 partial / 1 refuted / 1 n/a / 0 no artifact)**: every F10–F16 number v1.1.1 cites resolves to its key in `reconciler-rederive-b1r2.json`, F16 was recomputed independently from both NPZ
mints with numpy, the two −0.101 values are distinguished at every site, no question the plan's record closed is re-opened ((b) stays withdrawn; the GO definition is unchanged; R4 stays a note). It changed **one quoted number**: §2.3(a)'s "last-step feature std from 3.8e-4" was `20-matrix-datasets.json`'s float32-arithmetic std of the exactly-constant `cost_basis` column (0.0 in float64; the smallest non-zero std is 0.022) — a clause that contradicted the round-2 `cost_basis` correction — and it scoped
"rff/gcv is seed-stable" to the three seeds measured. Applied as v1.1.2. **Round 3 changed no disposition and no action, so the process terminates here** (procedure §4: stop when a round changes no number, disposition or action — the one number was a parenthetical lower bound).

---

## 6. Attacked and held

- **The GO verdict** as the plan defines it (P5 gating paragraph: "E-H's config is sane"): bounded and finite on both 2026-10-03 mints, six RFF seeds (worst aggregate −0.252, worst fold −0.558), embargo 64, `test` excluded, and in-support; the instrument could have said no (`rff / 0.0` → −1,986).
- **Every per-fold and aggregate number** in the note's §1.2, §1.3 (2026-10-04 column), §2.2 and §2.4 tables, including theta 91.0 in 120 / 120 folds, bit-identical configured twins, 15 of 20 GCV folds at the ceiling, and the Scenario-A re-run's `cv_r2` equal to the HTTP replay to every digit (A1); all of them reproduced bitwise on a fresh stack (A3).
- **The code chain** (A2, 39 confirmed): service defaults → linear rung → `np.linalg.lstsq(rcond=None)` min-norm; the RFF rung standardises train-only per fold and the linear rung does not; the 242-column design; `_GCV_GRID` ending at 1000.0; `derive_full_split` entity-major; the in-process path is the route's step for step.
- **The R5 band**: `cv_r2 ∈ [−1.0, +0.5]` separates all 24 cells with the nearest non-sane at −4.52; `cv_r2_std ≤ 0.5` has no false-fail across seeds (0.071–0.191) and fails the one-outlier cell at 8.75 (B1-r2 §2).
- **F-P8 at Major** and the W5.7 guard's `actions_present` + log half (B1-r2 F15: "zero-fills with no log line" is a fair reading; refusal is a request-level decision).
- **The plan's R4 note** (fold-local memory standardisation required) — consistent with W5.8 (B); the plan's own consensus record §6 items — none re-opened by v1.1.x except as B1-r2 F3 notes for (b), now re-closed.

---

## 7. Unresolved dissent

- **Attribution of cause vs amplifier** (B1-r2 F3 vs round-1 B1 F2): round 1 argued the drift is necessary and `ridge = 0` only sets the magnitude; round 2 argued the shuffled control cannot separate drift from near-duplicate leakage and that "cause = drift" misaligns with every remedy. The reconciler's F15 control (embargoed, in-era) settles what the shuffled control could not; the recorded statement is the conjunction, with the default as the actionable lever. No reviewer disputed that statement after it
  was written, but no reviewer has yet read it either — round 3 checks it.
- **Option (A), a default readout change**: round-1 B2 recommended it (the only in-band default that retains a fit); round-2 B1 held that the criterion is in-sample and the scope exceeds W5.8. Both are recorded; the owner decides between W5.8 (B) and W5.11 with the trade-off stated (a fit that scores worse out of sample vs an abstention that must be flagged).
- **Milestone dates** remain unconfirmed by the owner (carried from the plan's own record).

---

## 8. What the evidence cannot support

- Any statement about multi-ticker artifacts, other `d`, the MLP rung, other tickers, windows or dataset seeds — one ticker, one window, one dataset seed throughout.
- A separation of the default readout from the drift as **the** cause: every matrix cell is chronological; the embargoed in-era control (F15) is one block, one artifact.
- Skill: r² ≈ −0.1 in-support as well as out means these features with this readout carry no demonstrable next-day signal; "efficient-market ceiling" is interpretation.
- Precision beyond the RFF seed spread (≈ 0.05 in aggregate) or the ≈ 0.04 boundary-overlap effect; the service always uses seed 0.
- What the Scenario-B mint's upstream response looked like, or why yfinance omitted the action columns for one fetch 85 s after a complete one (cache CSV, column-flattening and a transient response are all consistent with the evidence).
- The recurrence tree's state on 2026-10-03 (reflog places `be081fae` on `main` from 2026-10-02; the tree is clean today).
- Numbers that live only in a reconciler JSON and no instrument the note originally declared (F10–F16): train + val-only, embargo-64, in-era, mint-B rff, rff/gcv per seed, row-order / float32 — re-derivable from the scripts, measured once.
- The milestone dates.

---

## 9. Disposition

The W5.1 note is **upheld with corrections** at v1.1.2: verdict GO, R5 band `cv_r2 ∈ [−1.0, +0.5]` plus `cv_r2_std ≤ 0.5` (both `gate`, row-scoped, to be re-measured on W5.2's population before W5.4 encodes it). Its explanatory layer was rewritten twice (v1.1.0 after round 1, v1.1.1 after round 2) and round 3 changed one parenthetical number (v1.1.2); the review terminates and R5 may be ruled. The plan carries the consequences at v1.4.0
(`JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`): F-SCI1's corrected
statement, F-P8 re-filed Major with a W5.7 guard, W5.8 rewritten around its measured options, W5.9 as reporting, W5.10 and W5.11 proposed, the W5.2 → W5.3 / W5.4 edges, and the "applied pending ruling" record for R2, R3 and R8.

The owner decisions this review leaves, in the order the plan needs them:

| Decision | Gates | Recommendation of record |
| --- | --- | --- |
| R5 — band and mode | W5.4 | `cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`, `gate`, row-scoped; re-measure on W5.2's population before encoding |
| W5.8 (B) and/or W5.11 (A) | the service default | (B) gcv + standardisation gated on W5.10, or (A) default readout rff/1.0 — the owner picks; neither ships without the response flag |
| W5.9 as reporting; W5.10 | the response contract | accept |
| F-P8 Major; W5.7 guard | juniper-data | accept |
| R8 re-ruling | W1.3 (shipped `auto`) | keep `auto` until the producer names the regression target consistently or the service passes `target` from `task_type` |
| Release placement of W5.8 / W5.10 | W1.13 vs 0.7.0 | owner |

Instruments and sample for the record (procedure §7): the two 2026-10-04 ad-hoc scripts (HTTP replay + in-process matrix; SVD of the rebuilt design), a fresh-stack rerun of both, three reconciler re-derivation scripts through the model's own readout functions, and numpy-only checks; one ticker, one window, five folds, 12 distinct cells, six RFF seeds, two mints of one id. Three Lane A entry points and two Lane B briefs in round 1, one of each in round 2, two iterations so far; dissent as recorded in §7.

---

## Change Log

| Date | Version | Changes | Author |
| --- | --- | --- | --- |
| 2026-10-05 | 0.1.0 | Skeleton: sizing argument, instruments, lanes and entry points; round 1 launched | Paul Calnon |
| 2026-10-05 | 1.0.0 | Record of three rounds against note v1.0.0 → v1.1.0 → v1.1.1 → v1.1.2: round-1 reconciliation (§4), round-2 corrections and the round-3 termination (§5), what held (§6), dissent (§7), limits (§8), disposition and owner decisions (§9) | Paul Calnon |
