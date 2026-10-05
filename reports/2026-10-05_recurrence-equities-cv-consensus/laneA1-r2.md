# Lane A1-r2 — re-derivation of every number v1.1.0 added or changed

- **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` at v1.1.0 (worktree copy; scope = `git diff` against the committed v1.0.0, 100 insertions / 75 deletions)
- **Lane**: A1, round 2 — measurement re-creation of the **corrections** only (procedure §2 Lane A, §4 "brief round 2 on the corrections")
- **Entry point**: the diff, then every number traced to a file under `reports/2026-10-04_recurrence-equities-cv-matrix/`, `reports/2026-10-05_recurrence-equities-cv-consensus/{laneA3-rerun/,reconciler-rederive.json,reconciler-rederive-b1.json}`, the audit archive `.amp/in/artifacts/recurrence-equities-audit/` and the Scenario-B store `.amp/in/scratch/data-store/`. The two reconciler scripts were read for key semantics only. Arithmetic was re-done with numpy over `21-matrix-cells.json`, the two HTTP JSONs and the two NPZ mints (script source in §5 — it lives in the session scratchpad, so it is reproduced here).
- **Not opened**: `laneA1.md`, `laneA2.md`, `laneA3.md`, `laneB1.md`, `laneB2.md`, the consensus record note. Nothing in `notes/` was modified. No git write commands.
- **Verdict key**: CONFIRMED = re-derived from a primary file to the stated precision; PARTIAL = the number is right but the statement around it is not, or only part of it is in the tree; REFUTED = the artifact gives a different value; NO ARTIFACT = no file in the permitted tree carries it. "n" = how many independent values the row covers.

## 1. Claim table (grouped by section of v1.1.0)

| § | claim (v1.1.0) | artifact value | verdict | file / key | n |
| --- | --- | --- | --- | --- | --- |
| 0.1 | Reproduced 2026-10-05 as run `20261005T132907Z-5493`, same ports, same versions | run id, data `:8110`, recurrence `:8260`; recurrence 0.5.0, model 0.3.0, service-core 0.5.0 | CONFIRMED | `laneA3-rerun/00-stack-up.log` L2–6; `03-launch.log` L6–10; `04-juniper-recurrence-after-replay.log` L3 | 1 |
| 0.1 | OpenBLAS 0.3.34, 16 threads by default | `libopenblasp-r0.3.34.so`; `cpu_count 16`, `openblas_get_num_threads 16` | CONFIRMED | `05-blas-threadpool.txt`; `51-ab-isolation-default.json` | 2 |
| 0.1 | fold 3 eval holds 69 `val` rows; fold 4 eval = 107 `val` + all 176 `test` | fold 3: 214 train / 69 val; fold 4: 107 val / 176 test (eval rows 1415–1697 vs partition cuts 1346 / 1522) | CONFIRMED | `reconciler-rederive-b1.json` F7; re-derived independently by index arithmetic (§5) | 5 |
| 0.1 | RFF seed 0 everywhere (HTTP, matrix, suite) | seed-0 in-process fold r² == HTTP fold r² to every digit (−0.08027410347435637 …) | CONFIRMED (by consequence) | `10-crossval-eh-rff.json`; `b1.json` F9 seed 0 | 5 |
| 0.2 | solve bit-identical HTTP vs in-process: per-fold `mse`/`rmse`/`mae` equal to the last bit, both configurations | 10/10 folds, 3/3 metrics, train and eval, exactly equal | CONFIRMED | `10-crossval-*.json` vs `21-matrix-cells.json` (§5 arithmetic) | 60 |
| 0.2 | only r² differs, at ~1e-7 relative | defaults cell: 1.4e-8 … 1.2e-7 relative; RFF cell: 1.7e-7 … **1.6e-6** relative on r² (absolute ≤ 1.3e-7; r² near zero inflates the ratio). Mechanism-level ~1e-7 holds | PARTIAL | same | 10 |
| 0.2 | fold 0 defaults −93,606.24 HTTP / −93,606.23 in-process; aggregate −20,344.64 both ways | −93606.2421298088 / −93606.2310410387; −20344.6377 / −20344.6354 | CONFIRMED | same | 3 |
| 0.2 | fresh stack reproduced both replays, all 24 cells, all 10 conditioning rows **bitwise** | replay: 54/54 compared metrics EXACT; matrix: 24/24 cells EXACT on every compared field; conditioning 10/10 EXACT (rank, cond, ‖coef‖, amp) | CONFIRMED (over the compared fields) | `laneA3-rerun/41-compare.md`, `40-compare.json` | 88+ |
| 1.1 | all 28 keys byte-identical (A vs 10-04); 10-05 mint byte-identical again, whole-file sha256 reproduced | 28 keys, 28/28 `tobytes_equal`, `npz_file_bytes_identical true`, sha256 `cff84fe5…` both; 10-04 checksum `c02004e1…` | CONFIRMED | `laneA3-rerun/30-numpy-checks.json` archive block; `00-dataset-create.json` (10-04) | 28 |
| 1.1 | Scenario A minted 09:14:24Z, checksum `c02004e1…` | `created_at 2026-10-03T09:14:24.638625+00:00`, checksum `c02004e1708e…` | CONFIRMED | `scenario-a-runs/20261003T091414Z-4ba6/data/*.meta.json` | 2 |
| 1.1 | −18,081 belongs to Scenario B, minted 85 s later (09:15:49Z), checksum `037baab7…` | `created_at 09:15:49.655245` (Δ = 85.02 s); checksum `037baab750…`; audit HTTP meta same checksum; shadow crossval agg −18081.54317 | CONFIRMED | `.amp/in/scratch/data-store/*.meta.json`; `40-seq-meta-http.txt`; `24-c-crossval-shadow.txt` | 4 |
| 1.1 | the two mints differ in exactly two feature columns | only cols 10 (`dividend`) and 11 (`split_ratio`) differ; no non-`X_*` key differs | CONFIRMED | NPZ diff (§5); `b1.json` F1 | 28 |
| 1.1 | `dividend` all zero in B in every partition (A: 0 … 0.22) | B max 0.0 ×3; A max 0.205 / 0.205 / 0.22 | CONFIRMED | NPZ diff (§5) | 6 |
| 1.1 | `dividend` differs in **1,367 + 244 + 178** cells | dividend: 1,367 (train) + **180** (val) + 178 (test) = 1,725. **244 is `X_val`'s total across both columns** (180 dividend + 64 split_ratio) — the note read b1's per-key `cells_differ` as a per-column count | REFUTED (as attributed) | NPZ diff (§5); `b1.json` F1 `differing_keys.X_val.cells_differ = 244` | 3 |
| 1.1 | `split_ratio` zero in `X_val` where A carries the 2020-08-31 4:1 split (64 cells) | 64 cells, value 4.0, in-window date 20200831 | CONFIRMED | NPZ diff (§5); `b1.json` F1 | 3 |
| 1.1 | re-solving linear / ridge 0 on the B arrays reproduces every audited digit (0.452957979 / −83,451.610; −814.665 / −3.720 / −78.492 / −6,059.229; −18,081.543) | b1 re-solve on B: 0.45295797869944143 / −83451.6101647795 / −814.6647303831381 / −3.7198060564183617 / −78.49243017276824 / −6059.228738766733 / −18081.54317403171 — bitwise equal to the audit's JSON | CONFIRMED (re-solve is reconciler-only; target digits primary) | `b1.json` F1 `linear_ridge0_on_B`; `24-c-crossval-shadow.txt` | 7 |
| 1.1 | `checksum` = sha256 of uncompressed `np.savez` over sorted keys → content fingerprint; `c02004e1…` reproduced on three days | algorithm reproduces `c02004e1…` from A's arrays and `037baab7…` from B's (my run and b1); `c02004e1…` recorded 10-03 (A), 10-04 (two mints: 21:06Z and 22:14Z), 10-05 | CONFIRMED | §5; `b1.json` F1; `00-dataset-create.json`; `scenario-a-rerun/c001-manifest.json`; `30-numpy-checks.json` meta | 5 |
| 1.2 | std 0.0735 is the **population** std; aggregate = plain mean of fold r²; aggregate RMSE = mean of per-fold RMSE | pop std 0.0735372 = `eval_std.r2` (sample std would be 0.0822); mean(fold r²) = −0.11526097 = `eval_aggregate.r2`; mean(fold rmse) = 0.0185701 = `eval_aggregate.rmse` | CONFIRMED | `10-crossval-eh-rff.json` (§5) | 3 |
| 1.3 | columns differ by 12 % (fold 0) and 19 % (fold 4) | 12.17 %; 19.47 % | CONFIRMED | `10-crossval-service-defaults.json` vs `24-c-crossval-shadow.txt` | 2 |
| 1.3 | thread count (1/2/4/8/16) moves fold 0 by ≤ 4e-4 relative, fold 4 by ≤ 2e-4 | fold 0: max 3.8e-4 (4 threads; 1–6, 8, 10, 12, 14–16 swept); fold 4: max 6.8e-5 (2 threads) — only 1 / 2 / 4 / default(16) swept, **8 not measured for fold 4** | CONFIRMED (fold 0) / PARTIAL (fold 4 set) | `54-thread-sweep-fold0.json`; `50-fold-threads-{1,2,4,default}.json` | 15 |
| 1.3 | three hundred times smaller than the audited gap | 12.2 % / 3.8e-4 ≈ 320 | CONFIRMED | arithmetic | 1 |
| 1.3 | audit in-sample train r² fold 0 0.45296 vs 0.45324 | 0.45295797869944143 / 0.4532378241225371 | CONFIRMED | `24-c-crossval-shadow.txt`; `10-crossval-service-defaults.json` | 2 |
| 1.3 | within one environment the solve is bit-identical across processes and across days | 10-04 HTTP == 10-05 HTTP == 10-05 repeat (−93606.2421298088); pure-path A == B; alignment probe 6/6 identical | CONFIRMED | `41-compare.md`; `11-crossval-service-defaults-repeat.json`; `52-pure-matrix-path-repro.log`; `53-alignment-probe.json` | 4 |
| 1.4 | suite `cv_r2` equals the §1.2 aggregate **to every digit** (−0.11526096841533144) | registry / manifest `cv_r2 −0.11526096841533144` == HTTP `eval_aggregate.r2` | CONFIRMED | `scenario-a-rerun/registry.jsonl`, `c001-manifest.json`; `10-crossval-eh-rff.json` | 1 |
| 1.4 | `n_windows` 1346 is the **train partition's** count; the `crossval` block records no window count | `train.dataset.n_windows 1346`, `split "train"`; `crossval` holds only `n_folds`, `task_type`, `eval_aggregate`, `eval_std` | CONFIRMED | `c001-manifest.json` | 2 |
| 1.4 | manifest `git: {}`; dist version of an editable install | `"git": {}`; `juniper-ml 0.6.0` (pyproject 0.10.0), `juniper-data 0.14.0` for an editable `main` checkout | CONFIRMED | `c001-manifest.json` | 2 |
| 2.1 | theta axis degenerate: configured cells duplicate fold-resolved twins **bit for bit**; 12 distinct cells | 12/12 configured cells equal on every fold metric and prediction statistic | CONFIRMED | `21-matrix-cells.json` (§5) | 12 |
| 2.1 | normalised artifact is **min-max scaled to [0, 1]**, scaler fitted on pooled `train` | `X_train` min 0.000 / max 1.000 exactly; `X_val` / `X_test` reach 8.008 (9 columns > 1) | CONFIRMED | `laneA3-rerun/data/equities_seq-6.0.0-fa3aae11ac374c94.npz` (§5) | 3 |
| 2.1 | wall ≈ 32 s per cell (≈ 10 s fitting); total ≈ 13 min | wall 29.1–37.4 s (mean 32.0 over the 12 fold-resolved cells); `fit_seconds` sums 9.3–13.3 s; 24 × 32 s ≈ 12.8 min | CONFIRMED | `21-matrix-cells.json` `wall_seconds`, `folds[].fit_seconds` | 24 |
| 2.2 | rff / gcv / off aggregate **−0.015** (was −0.014) | −0.0145435 | CONFIRMED (correct fix) | `21-matrix-cells.json` | 1 |
| 2.2 | target std per fold 0.011 / **0.013** / 0.020 / 0.028 / 0.016 (fold 1 was 0.014) | 0.01132 / 0.01347 / 0.01964 / 0.02766 / 0.01590 | CONFIRMED (correct fix) | `21-matrix-cells.json` `target_eval.std` | 5 |
| 2.2 | predicts a log return of 9.8 (e^9.8 ≈ 18,000×); scaled ridge-0 up to 137,000 | max \|pred\| 9.81; e^9.8 = 18,034; 1.365e5 | CONFIRMED | `21-matrix-cells.json` `pred_eval` | 3 |
| 2.2 | in every sane fold the RFF rung's prediction std ≤ 0.51× the target's | max ratio 0.512 (rff/1.0/on fold 4); rff/1.0/off ≤ 0.479; rff/gcv ≤ 0.04 | CONFIRMED (0.512 rounds to 0.51) | same | 20 |
| 2.2 | all other table cells (unchanged rows re-checked in passing) | 60 fold r², 12 aggregates, train r², λ, γ, max\|z\| all match | CONFIRMED | `21-matrix-cells.json`, `22-matrix-table.md` | 100+ |
| 2.3 | (b) scaling makes ridge 0 **2.1e8×** worse (−20,345 → −4.3e12); rank 113–161 → 210–226 | ratio 2.108e8; ranks 113/149/159/160/161 → 210/210/210/210/226 | CONFIRMED | `21-matrix-cells.json`; `23-linear-conditioning.json` | 11 |
| 2.3 | (b) −0.115 vs −0.142 is below the seed spread (−0.115 … −0.252, std 0.045) | Δ 0.027 < 0.045 | CONFIRMED | `b1.json` F9 | 2 |
| 2.3 | (a) shuffled split −0.33 / −0.001 / −0.08 instead of −7,239 | −0.3269 / −0.00088 / −0.0833; chronological −7239.17 | CONFIRMED (reconciler-only) | `b1.json` F2 | 4 |
| 2.3 | (a) last-step feature std 3.8e-4 … 7.9e11 (`volume`, `total_shares`, `market_cap`) | 3.81e-4 (`cost_basis`) … 7.94e11 (`market_cap`); `volume` 6.7e7, `total_shares` 4.4e9 | CONFIRMED | `20-matrix-datasets.json` | 15 |
| 2.3 | (a) eval inputs 8–199 σ outside the train support; (d) 28–100 % rows > 5 σ; raw last-step 10–58 | 7.5–198.6; 0.28–1.00; 9.9–57.7 | CONFIRMED | `21-matrix-cells.json` `memory_z_eval_vs_train`, `raw_last_step_z_eval_vs_train` | 15 |
| 2.3 | (d) in-support the **RFF rung is bounded (≈ −0.05)** and the linear rung is finite | linear: −0.33 / −0.001 / −0.08 (finite) ✓; **no RFF shuffled-split value exists in the tree** | PARTIAL (linear) / NO ARTIFACT (RFF ≈ −0.05) | `b1.json` F2 (linear only) | 1 |
| 2.3 | (d) linear rung with per-fold train-only standardisation and ridge 1.0 scores **−192** | −191.897 | CONFIRMED (reconciler-only) | `reconciler-rederive.json` aggregates `C_std_linear_ridge1_eval_r2` | 1 |
| 2.3 | (d) `rff / 0.0` standardises and scores −1,986; `linear / gcv / on` scores −0.015 | −1986.28; −0.01474 | CONFIRMED | `21-matrix-cells.json` | 2 |
| 2.3 | GCV: three of four GCV configurations collapse (train r² ≈ 0.002, eval −0.01); `linear / gcv / off` −247 with λ at the ceiling in three of five folds | rff/gcv/off, linear/gcv/on, rff/gcv/on: train r² 0.001–0.015, agg −0.013 … −0.015; linear/gcv/off λ = 1000 / 1000 / 85.5 / 60.2 / 1000 | CONFIRMED | `21-matrix-cells.json` | 9 |
| 2.3 | 15 of 20 GCV folds at λ = 1000.0; grid `logspace(−6, 3, 60)` | 3 + 3 + 5 + 4 = 15 (A3: 30/40 over 24 cells); 60.2 / 85.5 / 495 are logspace(−6,3,60) points k = 51 / 52 / 57 | CONFIRMED | `22-matrix-table.md`; `41-compare.md` | 20 |
| 2.3 | RFF optimum is the **null model in folds 0, 3, 4**, interior (λ ≈ 398 / 63) in folds 1, 2 | folds 3, 4: extended argmin at λ = 1e12, `at_edge true`, GCV/null − 1 ≈ 1e-12 ✓; **fold 0: argmin interior at λ = 199,526, `at_edge false`**, GCV 4.2e-9 *below* the null — effectively null, not literally; folds 1 / 2: 398.1 / 63.1 ✓ | PARTIAL (fold 0) | `reconciler-rederive.json` `D_rff_gcv_ext_*` | 5 |
| 2.3 | linear/raw: null model's GCV below every finite grid point in all five folds | `D_linear_null_is_below_every_grid_point true` ×5 (best finite point 2–18 % above null) | CONFIRMED (reconciler-only) | `reconciler-rederive.json` | 5 |
| 2.4 | scaled fold 0 σmax/σmin **1.8e24** (was 1.7e24) | 1.7549e24 | CONFIRMED (correct fix) | `23-linear-conditioning.json` | 1 |
| 2.4 | the 8-row table (ranks, cond, ‖coef‖, p99 train → eval) | all values match to the printed precision | CONFIRMED | `23-linear-conditioning.json`; `23-conditioning-stdout.log` (10-05) | 40 |
| 2.4 | every reported rank ≤ 226, so all ten smallest directions lie below the cutoff; σ_max 2.8e12 … 8.9e12 | max rank 226 of 242 (≥ 16 discarded); σ_max 2.80e12 (fold 0) … 8.87e12 (fold 4) | CONFIRMED | same | 10 |
| 2.4 | ~130 directions carrying the price/return information are truncated | 242 − 113 = 129 (fold 0); 93 / 83 / 82 / 81 in folds 1–4 | PARTIAL (fold-0 figure, unlabelled) | same | 5 |
| 2.4 | only exactly-constant memory columns are `split_ratio`'s sixteen (zero until 2020-08-31; folds 0–3) | fold 0: 16 constant columns, all `split_ratio`; fold 4: 0. Split rows are full-view 1362–1425, so folds 0–3 train (rows < 1130) are all-zero and fold 4 train is not | CONFIRMED | `b1.json` F5; NPZ (§5) | 4 |
| 2.4 | `cost_basis` memory columns vary with `dt`; `total_shares` CV 0.63 | cost_basis memory col std 0.046–1.02 (fold 0); total_shares last-step CV 0.629 (also 4.43e9 / 7.04e9 from `20-matrix-datasets.json`) | CONFIRMED | `b1.json` F5; `20-matrix-datasets.json`; §5 | 2 |
| 2.4 | column-standardised fold 0 rank 226 / 242; fold 4 full rank 242 | `std_rank_eps` 226; 242 | CONFIRMED (reconciler-only) | `b1.json` F5 | 2 |
| 2.4 | min-norm train r² 0.14–0.45 | 0.135–0.453 | CONFIRMED | `21-matrix-cells.json` | 5 |
| 2.4 | "The digits are reproducible. **Bit-identical across the HTTP service process and the in-process script**" | true for `mse` / `rmse` / `mae`; **r² (the digits under discussion) differs**: −93,606.242 vs −93,606.231 — as §0.2 itself states | PARTIAL (contradicts §0.2) | `10-crossval-service-defaults.json` vs `21-matrix-cells.json` | 5 |
| 2.4 | bit-identical across two service processes and across 10-04 / 10-05 | 10-04 and 10-05 services both return −93606.2421298088 | CONFIRMED | `41-compare.md`; `11-crossval-service-defaults-repeat.json` | 1 |
| 2.4 | **row order ≤ 2.5 %**; **float32 round-trip of the design 6 %** | no row-permutation or float32 probe in any permitted file | NO ARTIFACT | — | 2 |
| 2.4 | all far below the 12–19 % between audit and note | 12.2 % / 19.5 % | CONFIRMED | as §1.3 | 2 |
| 2.4 | fold 0 is the one rounding-sensitive fold **at the per-cent level** | thread sweep moves fold 0 by 0.04 % (3.8e-4); folds 1–4 ≤ 7e-5. Only the un-evidenced row-order / float32 figures reach per-cent | PARTIAL (rests on NO-ARTIFACT numbers) | `54-thread-sweep-fold0.json` | 1 |
| 2.4 | dropping fold 0: sane −0.115 → **−0.124**; defaults −20,345 → **−2,029** | −0.12401; −2,029.24 | CONFIRMED | `21-matrix-cells.json` (§5) | 2 |
| 2.5 | seeds 0–5 rff/1.0: −0.115 / −0.131 / −0.126 / −0.153 / −0.156 / −0.252; mean −0.155, std 0.045; per-fold min −0.558 (seed 5, fold 4); seed 0 is the best | −0.11526 / −0.13050 / −0.12603 / −0.15327 / −0.15571 / −0.25180; mean −0.15543, std 0.04545; −0.55759 at seed 5 fold 4; `seed0_is_best true` | CONFIRMED (reconciler-only) | `b1.json` F9 | 10 |
| 2.5 | `rff / gcv` is **seed-stable (−0.013 … −0.015)** | no rff/gcv seed sweep in either JSON; the quoted range is the **seed-0** rff/gcv values across normalisation (−0.0134 on, −0.0145 off) and the extended grid (−0.0151) | NO ARTIFACT | — | 1 |
| 2.5 | fold 4 eval = 107 val + 176 test (2021-04-21 → 2021-12-29); train + val = 1,522 windows | test `window_end_date` 20210421–20211229; 1346 + 176 = 1522 | CONFIRMED | NPZ (§5); `30-numpy-checks.json` | 3 |
| 2.5 | **"Fold 4 is the worst fold in every sane cell"** | rff/1.0/off: fold 4 worst (−0.258) ✓; rff/1.0/on: fold 4 worst (−0.277) ✓; **rff/gcv/off: fold 0 worst (−0.049), fold 4 best (+0.0003)**; **linear/gcv/on: fold 0 worst (−0.051), fold 4 −0.006**; **rff/gcv/on: fold 0 worst (−0.050), fold 4 best (+0.0003)** | REFUTED (2 of 5 sane cells) | `21-matrix-cells.json`, §2.2's own table | 5 |
| 2.5 | train + val only: rff/1.0 **−0.101**, rff/gcv **−0.006**, service defaults **−17,365** | not in any permitted file (grep for `17,?365`, `-0.101`, `-0.006` finds only unrelated fold values) | NO ARTIFACT | — | 3 |
| 2.5 | every fold's first eval window shares **61 of its 64** days with the last train window | 61 / 64 at all five boundaries (rows 280→283, 563→566, 846→849, 1129→1132, 1412→1415) | CONFIRMED | NPZ `date_*` (§5) | 5 |
| 2.5 | no target leakage: train targets ≤ day t+1, eval targets ≥ day t+5 | `target_dt` ∈ {1,2,3,4} calendar days; in trading days last-train target = t+1, first-eval target = t+4; in calendar days (Fri boundary, fold 0) 05-16 vs 05-19 = t+3 vs t+6. Gap ≥ 3 trading days either way — the no-leakage conclusion holds; the "t+5" mixes units | PARTIAL (units) | NPZ (§5); `30-numpy-checks.json` fold dates | 5 |
| 2.5 | boundary overlap flatters by ≈ 0.04 (embargo 64: rff/1.0 **−0.153** full, **−0.111** test excluded; rff/gcv **−0.017 / −0.009**) | no embargo-64 run in any permitted file; 0.153 − 0.115 = 0.038 is consistent *if* −0.153 holds | NO ARTIFACT | — | 4 |
| 2.5 | in-support the RFF rung still scores **≈ −0.05** | see §2.3(d) row | NO ARTIFACT | — | 1 |
| 3.1 | bounded on **both 2026-10-03 mints (−0.115 / −0.101)** | b1 re-solved only linear/ridge 0 on mint B; no rff/1.0 solve on B exists. **−0.101 is also the §2.5 train+val-only figure** | NO ARTIFACT (and a collision, §3 item B) | `b1.json` F1 (linear only) | 1 |
| 3.1 | six seeds (worst −0.252); embargo 64 (−0.153); test excluded (−0.101); in-support (≈ −0.05) | seeds ✓ (`b1.json` F9); the other three: no file | CONFIRMED / NO ARTIFACT ×3 | — | 4 |
| 3.1 | predictions never exceed \|0.021\| against a target std of 0.018; `rff / 0.0` returned −1,986 | max \|pred\| 0.02127 (rff/1.0/off); target std 0.01835; −1986.28 | CONFIRMED | `21-matrix-cells.json`; `20-matrix-datasets.json` | 3 |
| 3.2 | (i) gcv alone **−247** (grid to 1e12: **−35**) | −246.89; −35.13 (λ 1.6e4 / 2.5e5 / 4.0e5 / 4.0e7 / 1e12) | CONFIRMED (−35 reconciler-only) | `reconciler-rederive.json` B_* | 2 |
| 3.2 | (ii) standardised linear, ridge 1.0 **−192** | −191.897 | CONFIRMED (reconciler-only) | same, C_std_linear_ridge1 | 1 |
| 3.2 | (i)+(ii) **−0.195** (λ at the ceiling in every fold) / **−0.019** (grid extended; **the null model**); train r² 0.06–0.10 / ≈ 0 | −0.19492 with λ = 1000 ×5 ✓; −0.01857 ✓ but extended λ = 1e12 only in folds 0–2 (**folds 3 / 4 interior at 1.26e5 / 6.3e3**); train r² capped 0.064–0.103 ✓; extended 3e-10 … **0.038** (≈ 0 in 3 of 5 folds) | PARTIAL | same, C_std_linear_gcv_* | 6 |
| 3.2 | (A) rff ridge 1.0 **−0.115**, train r² 0.12–0.18 | −0.11526; 0.124–0.184 | CONFIRMED | `21-matrix-cells.json` | 2 |
| 3.2 | standardised min-norm (ridge 0) is a different solution: **−8.8e12** | −8.763e12 | CONFIRMED (reconciler-only) | same, C_std_linear_ridge0 | 1 |
| 3.2 | item 2: null model for RFF in three of five folds, raw linear in all five | see §2.3 rows (fold 0 effectively, not literally, null) | PARTIAL / CONFIRMED | `reconciler-rederive.json` | 2 |
| 3.3 | measured at `fundamentals_fill: nan` (generator default); reproducing −0.1153 needs `n_folds 5`, `expanding`, `embargo 2`, `lookback 64`, seed 20260807, `random_seed 0` | request params omit the fill, meta records `"nan"`; request body carries the CV / lookback / seed values; seed-0 identity as above | CONFIRMED | `00-dataset-create.json`; `10-crossval-eh-rff.json` | 7 |
| 3.4 | sane class = **five** configurations, [−0.28, +0.00] per fold, [−0.142, −0.013] aggregate | 5 cells with agg > −1; per-fold −0.2765 … +0.0003; agg −0.1424 … −0.0134 | CONFIRMED | `21-matrix-cells.json` (§5) | 5 |
| 3.4 | nearest non-sane −4.52, **4.5×** below the bound; sane cells **7×** above it; ridge-0 class ≥ 3 orders below | −4.523 (4.52×); −1 / −0.1424 = 7.0×; −1,986 is 3.3 orders, −4.3e12 is 12.6 | CONFIRMED | same | 4 |
| 3.4 | the one leak (pooled-train scaling) lowered the number | −0.115 → −0.142 | CONFIRMED | same | 1 |
| 3.4 | one catastrophic fold diluted 5×; a single fold down to −4.6 passes `cv_r2 > −1` | with four sane folds ≈ −0.1: (−0.4 + x)/5 > −1 ⇒ x > −4.6 | CONFIRMED (arithmetic) | — | 1 |
| 3.4 | `cv_r2_std`: sane 0.018–0.074; linear/1.0/scaled 8.75; one-outlier std = 0.4·\|x\|; 0.5 fails any fold below −1.25; 7× margin | 0.0179–0.0735; 8.746; population std of [0,0,0,0,x] = 0.4\|x\| exactly; 0.5 / 0.4 = 1.25; 0.5 / 0.0735 = 6.8 | CONFIRMED | `21-matrix-cells.json` `eval_std.r2` (§5) | 6 |
| 3.4 | withdrawn `train_r2` row: at **n = 1,346** no defective configuration exceeds **0.229**; misses the audited configuration (0.453) on fold 0 | 0.229 is the maximum **fold-4 (n = 1,413)** train r² over the seven defective cells (rff/0.0/on); no defective-configuration fit at n = 1,346 exists in the tree; 0.4532 ✓ | PARTIAL (n mislabelled) / CONFIRMED | `21-matrix-cells.json` | 8 |
| 3.4 | prediction std ≤ 0.51× target in every sane fold; aggregate sits **12** fold-stds above −1.0 | 0.512; (−0.1153 + 1) / 0.07354 = 12.03 | CONFIRMED | same | 2 |
| 3.4 | irregular-sine control `cv_r2 0.975` would fail +0.5 under a suite-level band | 0.9749 > 0.5 | CONFIRMED | `scenario-a-rerun/registry.jsonl` | 1 |
| 4 | precision beyond the seed spread (≈ 0.05) or the ≈ 0.04 boundary overlap | 0.045 ✓; ≈ 0.04 rests on the embargo-64 numbers | CONFIRMED / NO ARTIFACT | `b1.json` F9 | 2 |
| 4 | the reflog places `be081fae` on `main` from 2026-10-02 | git-history claim; no evidence file; outside this lane's instrument | NO ARTIFACT (out of lane) | — | 1 |
| log | arithmetic / unit fixes (2.1e8×, e^9.8, −0.015, 0.013) | 2.108e8; 18,034; −0.01454; 0.01347 | CONFIRMED ×4 | as above | 4 |

## 2. Tallies

Counted over the **90 rows** above (a row with two verdicts is counted once under its weaker verdict; counted mechanically from the table, not by hand):

| verdict | rows |
| --- | --- |
| CONFIRMED | 68 |
| PARTIAL | 10 |
| REFUTED | 2 (`1,367 + 244 + 178` dividend cells; "Fold 4 is the worst fold in every sane cell") |
| NO ARTIFACT | 10 |

Independent values re-derived: ≈ 760 (the bitwise comparisons and the 24-cell matrix dominate the count).

**Numbers the corrections got right**: every arithmetic and unit fix the change log names (2.1e8×, e^9.8, −0.015, 0.013, 1.8e24) is correct; every number read from the matrix, the HTTP responses, the conditioning JSON, the Scenario-A rerun manifest and the two mints' metadata re-derives exactly; the Lane A3 bitwise reproduction is as described; the two-mint column diff, the audited-digit re-solve, the partition-row counts, the 61/64 overlap, the split date, the checksum algorithm and the min-max claim all re-derive from the NPZ files with an instrument that shares no code with the reconciler's.

**What the fix pass broke or left unsupported** — the §3 and §4 lists.

## 3. Internal contradictions in v1.1.0

- **A. §0.2 vs §2.4 (r² fidelity).** §0.2: "only r² differs, at ~1e-7 relative … −93,606.24 via HTTP, −93,606.23 in-process". §2.4: "The digits are reproducible. Bit-identical across the HTTP service process and the in-process script". The digits §2.4 is defending are r² digits, and those are the ones §0.2 says differ. True statement: the *solve* (mse / rmse / mae) is bit-identical HTTP↔in-process; r² agrees to 7 significant figures; HTTP↔HTTP (10-04, 10-05, repeat) is bit-identical.
- **B. §3.1 vs §2.5 vs §3.4 (−0.101 used twice).** §3.1 gives rff/1.0 on the Scenario-B mint as −0.101; §2.5 gives the **train + val only** rff/1.0 as −0.101; §3.4 lists "test excluded (−0.101)" and "both 2026-10-03 mints" as two separate survivals. No rff/1.0 solve on the B arrays exists in the tree (b1 F1 re-solves linear/ridge 0 only), so one of the two −0.101s is a transcription of the other. The band conclusion does not depend on it, but §3.1's "on both mints" is currently unevidenced.
- **C. §1.1 internal (244 double-counts the 64).** "`dividend` … 1,367 + 244 + 178 cells" and "`split_ratio` … (64 cells)" cannot both hold: 244 is `X_val`'s differing-cell total across both columns (180 dividend + 64 split_ratio). The per-column dividend count is 1,367 + 180 + 178 = 1,725.
- **D. §2.5 vs §2.2's table ("Fold 4 is the worst fold in every sane cell").** The sentence was added in v1.1.0 to motivate the `test`-in-fold-4 point; the §2.2 table two pages above it shows fold 0 as the worst fold in all three GCV cells and fold 4 as their best. It holds only for the two rff/1.0 cells.
- **E. §2.5 "rff / gcv is seed-stable (−0.013 … −0.015)" vs §2.2.** Those are the seed-0 rff/gcv aggregates of the two normalisations (and the extended grid); no seed sweep of rff/gcv exists. The sentence restates a normalisation range as a seed range.
- **F. §2.4 "rounding-sensitive at the per-cent level" vs §1.3 / §2.4's own thread figure.** The only measured perturbation (thread count) moves fold 0 by 0.04 %; the per-cent figures (row order 2.5 %, float32 6 %) have no artifact.
- **G. §3.3 "GCV selects the null model on this rung" vs §2.3 "null in folds 0, 3, 4; interior in folds 1, 2".** Overstated in §3.3 (3 of 5 folds; and fold 0 is "effectively" null — argmin at λ ≈ 2e5, 4e-9 below the null). Direction of the W1.1(a) bundle choice is unaffected.
- **H. §3.2 "(i)+(ii) −0.019 (grid extended; the null model)" vs `reconciler-rederive.json`.** The extended-grid selection is the edge (1e12) in folds 0–2 only; folds 3 and 4 pick interior λ (1.26e5, 6.3e3) with train r² 0.004 / 0.038. "Passes by abstaining" is right for three folds, not five.
- Checked and **consistent**: §0.2 vs §1.3 (bitwise across processes / days); §2.3(a) vs §3.1 vs §3.5 (amplifier-under-drift wording); §2.3(b) vs §4 (cannot separate (a) from drift); §3.2 table vs §3.4 band (every option number and the −1 bound); §2.3 GCV vs §3.2 item 2 (15 of 20; null in three of five); §1.1 vs §1.3 (two mints, 12 % / 19 %).

## 4. Claims resting only on a reconciler JSON, or on no file at all

**Only in a reconciler JSON** (no independent artifact; the provenance is the two `util/ad-hoc/2026-10-05_recurrence_equities_consensus_rederive*.py` scripts): the audited-digit re-solve on mint B (b1 F1 — the target digits themselves are primary in `24-c-crossval-shadow.txt`); the ranks 113→226 and 161→242 and the 16 constant `split_ratio` columns (b1 F5); the seed sweep (b1 F9); the shuffled linear split (b1 F2); the extended-grid −35, the standardised-linear −8.8e12 / −192 / −0.195 / −0.019, and every GCV-vs-null statement (rederive.json B / C / D). Of these, this lane independently re-derived from the NPZ files: the two-mint column diff, the partition rows per fold, the folds 0–3 `split_ratio` constancy, and the checksum algorithm — those are no longer reconciler-only.

**No artifact anywhere in the permitted tree** (grep over `reports/2026-10-04_…`, `laneA3-rerun/`, both reconciler JSONs, the five instrument scripts and the audit archive): the train + val-only numbers (−0.101 / −0.006 / −17,365, §2.5); the embargo-64 numbers (−0.153 / −0.111 / −0.017 / −0.009, §2.5, §3.1, §3.4) and the "≈ 0.04" derived from them (§2.5, §4); "row order ≤ 2.5 %" and "float32 round-trip 6 %" (§2.4); the RFF in-support "≈ −0.05" (§2.3(d), §2.5, §3.1); the "rff / gcv is seed-stable" range (§2.5); rff/1.0 on the Scenario-B mint "−0.101" (§3.1, §3.4 "both mints"); the reflog placement of `be081fae` (§4). If these were measured in a round-1 lane report they should be promoted into an evidence file; as the tree stands, §3.1's "established it more broadly" rests on the seed sweep alone for its measured breadth.

## 5. Method — the numpy pass (reproduced so nothing lives only in the scratchpad)

Run as `/opt/miniforge3/envs/JuniperCascor1/bin/python <file>`; reads only; prints only. The per-cell arithmetic over `21-matrix-cells.json` (twin bitwise identity, sane-class ranges, `cv_r2_std`, drop-fold-0 aggregates, prediction/target std ratios, the 2.1e8 ratio, e^9.8, the 0.4·|x| identity, the 12-fold-std figure, and the HTTP-vs-in-process per-metric equality) was an inline heredoc of the same shape and is fully described by the table rows it supports.

```python
import hashlib, io
import numpy as np
PA = ".amp/in/artifacts/recurrence-equities-audit/scenario-a-runs/20261003T091414Z-4ba6/data/equities_seq-6.0.0-15505731cba5b86d.npz"
PB = ".amp/in/scratch/data-store/equities_seq-6.0.0-15505731cba5b86d.npz"
PN = "reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/data/equities_seq-6.0.0-fa3aae11ac374c94.npz"
FE = ["open","high","low","close","volume","week52_high","week52_low","total_shares","market_cap","cost_basis","dividend","split_ratio","dsw52h","dsw52l","dsr"]
a = dict(np.load(PA)); b = dict(np.load(PB))
def cs(d):
    buf = io.BytesIO(); np.savez(buf, **{k: d[k] for k in sorted(d)}); return hashlib.sha256(buf.getvalue()).hexdigest()
print(len(a), len(b), cs(a)[:8], cs(b)[:8])                       # 28 28 c02004e1 037baab7
for part in ("train", "val", "test"):
    d = a["X_"+part] != b["X_"+part]; cols = np.flatnonzero(d.any(axis=(0, 1)))
    print(part, int(d.sum()), {FE[c]: int(d[..., c].sum()) for c in cols})   # train 1367 {dividend:1367}; val 244 {dividend:180, split_ratio:64}; test 178 {dividend:178}
Xv, Dv = a["X_val"], a["date_val"]; idx = np.argwhere(Xv[..., 11] != 0)
print(len(idx), set(Xv[..., 11][Xv[..., 11] != 0].tolist()), set(Dv[idx[:, 0], idx[:, 1]].tolist()))   # 64 {4.0} {20200831}
Xf = np.concatenate([a["X_train"], a["X_val"], a["X_test"]]); Df = np.concatenate([a["date_train"], a["date_val"], a["date_test"]])
rows = np.flatnonzero((Xf[..., 11] != 0).any(axis=1)); print(rows.min(), rows.max(), (Xf[:1130, :, 11] == 0).all(), (Xf[:1413, :, 11] == 0).all())  # 1362 1425 True False
print(1522 - 1415, 1698 - 1522, 1346 - 1132, 1415 - 1346)          # 107 176 214 69
for tl, ef in [(280, 283), (563, 566), (846, 849), (1129, 1132), (1412, 1415)]:
    print(len(set(Df[tl].tolist()) & set(Df[ef].tolist())))        # 61 ×5
print(int(a["window_end_date_test"].min()), int(a["window_end_date_test"].max()))   # 20210421 20211229
ls = Xf[:, -1, :]; print(ls[:, 7].std() / ls[:, 7].mean())         # 0.629
n = np.load(PN); print(float(n["X_train"].min()), float(n["X_train"].max()), float(n["X_val"].max()))   # 0.0 1.0 8.008
```
