# Lane A3 — independent re-measurement on a fresh stack, plus numpy-only checks

- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A (measurement re-creation).
- **Artifact under review**: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` v1.0.0 (the W5.1 note; P5 go/no-go GO; R5 band recommendation) for the plan `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.3.0.
- **Entry point of this lane**: a fresh per-run stack brought up from this checkout (juniper-ml `main` `a0a120d5`), the note's two instruments re-run against it, then numpy-only checks that share no code with the instruments, plus the audit's archived artifact under `juniper-ml/.amp/in/artifacts/recurrence-equities-audit/`. The predecessor's evidence under `reports/2026-10-04_recurrence-equities-cv-matrix/` was opened only for the comparison step.
- **Evidence**: `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/` (index in §12). Own script: `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py` (subcommands `checks` = numpy only; `compare` = digit-level comparison; `fold-threads` = thread/process probes, which **use** the model code and are labelled so).
- **Iterations**: one. **Reviewers in this lane**: one (A3). No dissent to record within the lane.
- **Headline**: every number the note prints for W0.8 (§1) and W0.9 (§2.2–2.4) reproduces on the fresh stack — the HTTP replays, all 24 matrix cells, and the 10 conditioning rows are **bitwise identical** to the 2026-10-04 JSON. The dataset-level facts of §0.1 reproduce under numpy alone. Three things do **not** survive: the F-P8 mechanism in §1.1 (the checksum hashes the arrays, not the container), the "same arrays" premise of §1.3 (the audited −18,081 was computed on a different mint, whose arrays are not archived), and the §2.4 claim that the ridge-0 digits are "reproducible only to their order of magnitude" (they are bitwise reproducible run-to-run; thread count moves them in the 4th significant figure; the 12 % audited gap is ~300× larger than anything rounding produced here). The GO verdict's inputs are not touched by any of these; the attribution of the 2026-10-03 digits is.

---

## 1. Stack record

| Item | Value |
| --- | --- |
| Launch (from this worktree) | `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1 bash util/experiment_stack.bash --up --recurrence --config /home/pcalnon/Development/python/Juniper/juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` — the relative `--config` path the predecessor recorded does not resolve from a `.claude/worktrees/` checkout (the launcher `cp`s it from the CWD), so the absolute path to the same file was used; a `--dry-run` preceded the real launch (`00-stack-up.log`). |
| Run | id **`20261005T132907Z-5493`**, run dir `/home/pcalnon/.local/state/juniper-experiments/20261005T132907Z-5493`, up 13:29:07Z, torn down 14:01:25Z (`90-stack-down.log`, `teardown.json`). |
| Ports | data **`127.0.0.1:8110`** (pid 3870498), recurrence **`127.0.0.1:8260`** (pid 3870903); `06-ports.json`. Same ports as the predecessor's run `20261004T210331Z-491a`, which had released them. |
| Health | data `GET /v1/health` → `{"status":"ok","version":"0.12.0","service":"juniper-data","git_sha":null,"build_date":null}` (`01-data-health.json`); recurrence `GET /v1/health` → `{"status":"ok"}`, `/v1/health/ready` → `{"status":"ready"}` — the recurrence health route reports **no version** (`01-recurrence-health-mine.json`). |
| Preflight | skipped as instructed; `launch.log` carries 4 WARNING lines, the finding being `juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0; installed 0.5.0` (`03-launch.log`). Expected; not a finding. |
| juniper-data | `JuniperData` env, Python 3.14.2 (free-threaded `python3.14t` site-packages, launched with `PYTHON_GIL=0`), editable checkout at **`29be6d3`** (clean; HEAD and the three commits before it are CI/dependency bumps only — `publish-image.yml`, codecov, codeql, pyflakes — so the generator code is the 2026-10-02 code), dist metadata 0.12.0, numpy 2.4.1, pandas 3.0.3, yfinance 1.4.1; `equities_seq` generator `6.0.0` (meta). Per-run storage `<run>/data`, per-run cold equities cache `<run>/equities-cache`. |
| juniper-recurrence | `JuniperCascor1` env, Python 3.14.7; juniper-recurrence 0.5.0 editable at **`be081fa`** (clean, committed 2026-10-02T21:23Z); juniper-recurrence-model 0.3.0 editable (same checkout); juniper-service-core **dist 0.5.0 / module `__version__` 0.4.0**; juniper-model-core 0.2.0; juniper-data-client 0.5.0 editable at `75f15a6`; numpy 2.5.3; scipy 1.17.1; torch 2.11.0; BLAS/LAPACK = **OpenBLAS 0.3.34 pthreads** (`libblas.so.3 → libopenblasp-r0.3.34.so`), 16 CPUs, default `openblas_get_num_threads() = 16`; `threadpoolctl` not installed (`05-blas-threadpool.txt`). |
| Foreign listeners | `127.0.0.1:8051`, `:8101`, `:8202` (another session's canopy E2E stack) present before, during and after; never touched. `ss -ltnp` after teardown: the three foreign listeners remain, **0** listeners in 8110–8139 / 8260–8289 (`02-listeners-up.txt`, `91-listeners-after-down.txt`). `util/reap_pytest_orphans.bash` and `util/juniper_chop_all.bash` were not run. |

The note's §0.1 "stack as served" row is **CONFIRMED** item by item (checkouts `29be6d35` / `be081fae`, model 0.3.0 editable, service-core dist 0.5.0 / module 0.4.0, model-core 0.2.0, data-client 0.5.0, numpy 2.5.3, generator 6.0.0).

## 2. Replay (W0.8, `POST /v1/crossval`) — my run vs the note vs the 2026-10-04 JSON

Dataset: `POST /v1/datasets` resolved to **`equities_seq-6.0.0-15505731cba5b86d`** (expected; `MATCH`) in 3.3 s from the cold per-run cache (`00-dataset-create.json`; data log: `equities_seq: [1/1] AAPL -> 1762 rows`).

**E-H body** (`{"d":16,"ridge":1.0,"readout":"rff","rff_features":256,"rff_gamma":"median"}` + 5 expanding folds, embargo 2) → HTTP 200 in 15.4 s (note: 11.2 s).

| fold | n_train | note train r² | note eval r² | note eval RMSE | mine (full precision; **bitwise = 2026-10-04 JSON**) train r² / eval r² / eval RMSE |
| --- | --- | --- | --- | --- | --- |
| 0 | 281 | +0.1843 | −0.0803 | 0.01177 | 0.18425734696545304 / −0.08027410347435637 / 0.011767970562964492 |
| 1 | 564 | +0.1604 | −0.0500 | 0.01380 | 0.16043227273595284 / −0.050026437320272565 / 0.01380346406800385 |
| 2 | 847 | +0.1392 | −0.1020 | 0.02062 | 0.1391709396666495 / −0.1019728052541875 / 0.02061861754805457 |
| 3 | 1,130 | +0.1262 | −0.0856 | 0.02882 | 0.1261839639360519 / −0.0855859667520531 / 0.028824350270245432 |
| 4 | 1,413 | +0.1239 | −0.2584 | 0.01784 | 0.12388855137480626 / −0.2584455292757877 / 0.017836298407318436 |
| agg | | | −0.1153 (std 0.0735) | 0.01857 (MAE 0.01337) | −0.11526096841533144 (std 0.07353723443032745) / RMSE 0.018570140171317355 / MAE 0.013371934065211014 |

**Service-defaults body** (no model parameters → `readout=linear`, `ridge=0.0`) → HTTP 200 in 17.9 s (note 10.9 s); repeated once more in the same service process (`11-crossval-service-defaults-repeat.json`, 21.0 s): **bitwise identical**.

| fold | note train r² | note eval r² (2026-10-04) | note eval r² (audit 2026-10-03) | mine eval r² (**bitwise = 2026-10-04 JSON**) | mine eval RMSE | audit 2026-10-03 full precision (`24-c-crossval-shadow.txt`) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | +0.4532 | −93,606 | −83,452 | −93606.2421298088 | 3.464091188469113 | train r² 0.45295797869944143; eval −83451.6101647795 |
| 1 | +0.3224 | −798.5 | −815 | −798.4669029752575 | 0.38088004235480577 | 0.3223292113086098; −814.6647303831381 |
| 2 | +0.2487 | −3.70 | −3.7 | −3.696331338492504 | 0.042565081520498815 | 0.24814986248864412; −3.7198060564183617 |
| 3 | +0.1836 | −75.6 | −78 | −75.61767366018817 | 0.2421541392443082 | 0.18370343780160026; −78.49243017276824 |
| 4 | +0.1353 | −7,239 | −6,059 | −7239.1656160853 | 1.3528877638467969 | 0.13759590416847334; −6059.228738766733 |
| agg | | −20,345 (std 36,731) | −18,081 | −20344.637730773607 (std 36730.52121489702) | RMSE 1.0965156430871044 | −18081.54317403171 (std 32762.308611429213) |

Every float in both replays (train/eval r², RMSE, MAE, MSE, aggregate, std) is **EXACT** (bitwise) against `reports/2026-10-04_recurrence-equities-cv-matrix/10-crossval-*.json` (`41-compare.md`, 52 compared scalars, 0 differences). Both requests returned 200 with no `PYTHONPATH` on a decision-11 artifact (the note's W0.1 acceptance remark): **CONFIRMED**.

Note the last column: the audit's **in-sample** train r² also differs from 2026-10-04/05 (fold 0: 0.45296 vs 0.45324, rel 6e-4; fold 2: 0.24815 vs 0.24871), not only the ill-conditioned eval numbers. See §7 for what the audit's request consumed.

## 3. Matrix (W0.9) — 24 cells

Both artifacts resolved as expected: raw **`equities_seq-6.0.0-15505731cba5b86d`**, normalised sibling **`equities_seq-6.0.0-fa3aae11ac374c94`** (`20-matrix-datasets.json`). 24 cells, 0 errors, 957 s total (note: ≈13 min). Theta resolved to **91.0 in every fold of every cell**; every `configured` row is bitwise identical to its `fold-resolved` twin, as the note states. Columns: the note's printed aggregate (§2.2; "= twin" where the note shows only the fold-resolved row), my aggregate, whether it reproduces, and the note's printed per-fold eval r² against mine rounded the same way. "EXACT" = every per-fold eval r², train r², theta, gamma, resolved ridge, memory max-|z|, prediction std/max and the aggregate are bitwise equal to the 2026-10-04 `21-matrix-cells.json` (`40-compare.json`).

| # | cell (readout / ridge / normalize / theta) | note agg | mine agg | reproduces? | note per-fold eval r² → mine |
| --- | --- | --- | --- | --- | --- |
| 1 | linear / 0.0 / off / fold-resolved | −20,345 | −20344.635437913923 | **EXACT** (all fields) | −93,606 / −798 / −3.70 / −75.6 / −7,239 → identical |
| 2 | linear / 0.0 / off / configured | = twin | −20344.635437913923 | EXACT, = twin | identical |
| 3 | linear / 1.0 / off / fold-resolved | −2,064 | −2063.6752055497195 | EXACT | −6,688 / −147 / −5.56 / −121 / −3,356 → identical |
| 4 | linear / 1.0 / off / configured | = twin | −2063.6752055497195 | EXACT, = twin | identical |
| 5 | linear / gcv / off / fold-resolved | −247 | −246.89020360724552 | EXACT; λ 1000 / 1000 / 85.5 / 60.2 / 1000 | −218 / −2.66 / −2.04 / −36.6 / −976 → identical |
| 6 | linear / gcv / off / configured | = twin | −246.89020360724552 | EXACT, = twin | identical |
| 7 | rff / 0.0 / off / fold-resolved | −1,986 | −1986.2845979305002 | EXACT; γ 0.0508 / 0.0512 / 0.0499 / 0.0499 / 0.0553 | −9,869 / −50.9 / −3.03 / −1.96 / −6.35 → identical |
| 8 | rff / 0.0 / off / configured | = twin | −1986.2845979305002 | EXACT, = twin | identical |
| 9 | **rff / 1.0 / off / fold-resolved** | **−0.115** | **−0.11526091596856643** | EXACT; γ as row 7 | −0.08 / −0.05 / −0.10 / −0.09 / −0.26 → identical |
| 10 | rff / 1.0 / off / configured | = twin | −0.11526091596856643 | EXACT, = twin | identical |
| 11 | rff / gcv / off / fold-resolved | −0.014 | −0.014543504619033509 | EXACT; λ 1000 / 495 / 60.2 / 1000 / 1000 | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 → identical |
| 12 | rff / gcv / off / configured | = twin | −0.014543504619033509 | EXACT, = twin | identical |
| 13 | linear / 0.0 / on / fold-resolved | −4.3e12 | −4289388869437.3467 | EXACT | −2.1e13 / −8.5e6 / −22.2 / −207 / −12,319 → identical |
| 14 | linear / 0.0 / on / configured | = twin | −4289388869437.3467 | EXACT, = twin | identical |
| 15 | linear / 1.0 / on / fold-resolved | −4.52 | −4.523027673129632 | EXACT | −0.27 / −0.09 / −0.11 / −0.13 / −22.0 → identical |
| 16 | linear / 1.0 / on / configured | = twin | −4.523027673129632 | EXACT, = twin | identical |
| 17 | linear / gcv / on / fold-resolved | −0.015 | −0.01473984067469134 | EXACT; λ 1000 × 5 | −0.05 / −0.01 / −0.00 / −0.01 / −0.01 → identical |
| 18 | linear / gcv / on / configured | = twin | −0.01473984067469134 | EXACT, = twin | identical |
| 19 | rff / 0.0 / on / fold-resolved | −3,197 | −3196.643478628517 | EXACT; γ 0.0495 / 0.0506 / 0.0505 / 0.0484 / 0.0607 | −15,904 / −62.5 / −3.42 / −3.24 / −10.0 → identical |
| 20 | rff / 0.0 / on / configured | = twin | −3196.643478628517 | EXACT, = twin | identical |
| 21 | **rff / 1.0 / on / fold-resolved** | **−0.142** | **−0.14237481029725402** | EXACT | −0.14 / −0.06 / −0.12 / −0.11 / −0.28 → identical |
| 22 | rff / 1.0 / on / configured | = twin | −0.14237481029725402 | EXACT, = twin | identical |
| 23 | rff / gcv / on / fold-resolved | −0.013 | −0.01341546392631976 | EXACT; λ 1000 / 1000 / 495 / 1000 / 1000 | −0.05 / −0.01 / −0.01 / −0.01 / +0.00 → identical |
| 24 | rff / gcv / on / configured | = twin | −0.01341546392631976 | EXACT, = twin | identical |

Other §2.2 / §2.3 figures: train r² f0 → f4 per row (0.453→0.135, 0.425→0.168, 0.317→0.088, 0.959→0.221, 0.184→0.124, 0.002→0.001, 0.907→0.212, 0.140→0.085, 0.002→0.003, 0.956→0.229, 0.186→0.119, 0.002→0.001) — identical; eval-memory max |z| per fold 24 / 23 / 8 / 199 / 44 (raw) and 24 / 23 / 11 / 337 / 50 (normalised) — identical; prediction-scale table (e.g. linear/0.0/off pred std 3.458 / 0.2104 / 0.0296 / 0.239 / 0.4254, max |pred| 9.81; linear/0.0/on 2.80e4 / 22.0 / 0.083 / 0.398 / 0.858, max 1.37e5; rff/1.0/off 0.00426 / 0.00399 / 0.00427 / 0.00618 / 0.00762, max 0.0213; rff/gcv/off 1.9e-4 … 3.6e-4, max 0.0036) — identical to the printed digits and bitwise to the JSON. **GCV at the grid ceiling λ = 1000.0: 15 of 20 fold-resolved folds** (linear/off 3, rff/off 3, linear/on 5, rff/on 4; 30/40 counting the configured twins) — the note's "15 of 20" **CONFIRMED**; `_GCV_GRID` is `logspace(-6, 3, 60)`, last point 1000.0 (read from `readouts.py`).

**The §2.4 prediction, cell by cell** ("ridge-0 digits move between runs while RFF ridge-1 digits are stable"): across runs — my 2026-10-05 cells vs the 2026-10-04 cells — the maximum relative difference of the aggregate eval r² is **0.0 in all six readout/ridge groups** (`linear/0.0`, `linear/1.0`, `linear/gcv`, `rff/0.0`, `rff/1.0`, `rff/gcv`, n = 4 cells each): the ridge-0 digits did **not** move between runs. The prediction as stated for run-to-run variation is **REFUTED** (n = 2 runs, one day apart, same host and env). What *does* move them is in §8.

## 4. Linear-design conditioning (§2.4) — mine vs the 2026-10-04 JSON

All ten rows **EXACT** in every field (rank, σmax, σmin, cond, ‖coef‖, weak-direction amplification p99 train/eval and eval max, singular-value deciles) — `23-linear-conditioning.json` vs the reference; the dataset ids match.

| artifact | fold | n_train | rank (eps) / 242 | σmax/σmin | ‖coef‖₂ | amp p99 train → eval (eval max) | note §2.4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw | 0 | 281 | 113 | 8.62e32 | 0.160 | 0.331 → 2.65e4 (3.51e4) | 113 / 8.6e32 / 0.16 / 0.33 → 26,500 ✓ |
| raw | 1 | 564 | 149 | 2.41e31 | 0.103 | 10.5 → 2.54e3 (2.74e3) | 149 / 2.4e31 / 0.10 / 10.5 → 2,540 ✓ |
| raw | 2 | 847 | 159 | 2.52e31 | 0.0622 | 0.0556 → 0.872 (1.79) | 159 / 2.5e31 / 0.062 / 0.056 → 0.87 ✓ |
| raw | 3 | 1,130 | 160 | 1.31e31 | 0.0472 | 6.42e-14 → 454 (876) | 160 / 1.3e31 / 0.047 / 6e-14 → 454 ✓ |
| raw | 4 | 1,413 | 161 | 1.54e22 | 0.0263 | 2.14e-5 → 0.00279 (0.00962) | 161 / 1.5e22 / 0.026 / 2e-5 → 0.0028 ✓ |
| normalised | 0 | 281 | 210 | 1.75e24 | 6.56e6 | 5.6e-7 → 0.0989 (0.152) | 210 / 1.7e24 / 6.6e6 / 6e-7 → 0.099 ✓ |
| normalised | 1 | 564 | 210 | 3.37e22 | 5.9e3 | 3.85e-5 → 0.0218 (0.0263) | (not printed in the note) |
| normalised | 2 | 847 | 210 | 2.15e21 | 55.5 | 1.38e-4 → 7.96e-4 (1.16e-3) | (not printed) |
| normalised | 3 | 1,130 | 210 | 1.22e21 | 44.0 | 1.8e-4 → 4.53e13 (8.64e13) | 210 / 1.2e21 / 44 / 1.8e-4 → 4.5e13 ✓ |
| normalised | 4 | 1,413 | 226 | 1.11e20 | 20.6 | 7.2e-4 → 0.109 (0.199) | 226 / 1.1e20 / 20.6 / 7e-4 → 0.11 ✓ |

The design is 242 columns (`[memory 15×16 | target_dt | 1]`) as the note says. **CONFIRMED.** (Instrument caveat: this is the note's own script re-run, so it establishes reproducibility of the instrument, not its correctness; the SVD of a 242-column design is not something the numpy checks re-derive independently.)

## 5. Numpy-only checks (no instrument code) — `30-numpy-checks.json`

Loaded with `np.load` from the run's storage dir (`<run>/data/equities_seq-6.0.0-15505731cba5b86d.npz`, copied to `laneA3-rerun/data/`). `full` view rebuilt as `concat(train, val, test)` followed by a stable argsort on `ticker_code` (the documented entity-major rule); fold cut stated exactly as: `fold_size = 1698 // 6 = 283`; fold *i* trains on rows `[0, 283·(i+1) − 2)` and evaluates on `[283·(i+1), 283·(i+2))`, *i* = 0…4 — verified against `walk_forward_folds` source (`juniper_model_core/crossval/__init__.py`) before use.

| check | note says | numpy says | verdict |
| --- | --- | --- | --- |
| keys / dtype | 28 keys | 28 keys; `X_*` float32 (W, 64, 15); no `*_full` family in the file | CONFIRMED |
| partitions | 1,346 / 176 / 176 | 1346 / 176 / 176, sum 1698 | CONFIRMED |
| `full` view | 1,698 windows | 1698; one `ticker_code` value; the entity-major order is the identity (so concatenation = entity-major for this artifact) | CONFIRMED |
| fold sizes | 281 / 564 / 847 / 1,130 / 1,413 train, 283 eval | train ends 281, 564, 847, 1130, 1413; eval 283 each | CONFIRMED |
| `sum(dt)` per window | 88–97, mean 91.3, std 1.7 | min 88.0, max 97.0, mean 91.322, std 1.699, median 91.0 | CONFIRMED |
| median `sum(dt)` per expanding train fold | 91.0 everywhere (theta) | 91.0 / 91.0 / 91.0 / 91.0 / 91.0 (eval folds also 91.0); `theta=None` resolves to exactly this quantity at fit (`model.py:176`) | CONFIRMED — theta = 91.0 is a property of the data, checked without the model |
| target `y_reg` | mean 0.00101, std 0.01835 | mean 0.0010143, std 0.018353 (min −0.1377, max 0.1132); all finite | CONFIRMED |
| target std per eval fold | 0.011 / 0.014 / 0.020 / 0.028 / 0.016 | 0.01132 / **0.01347** / 0.01964 / 0.02766 / 0.01590 (eval means 0.00147 / 0.00140 / 0.00009 / 0.00275 / 0.00142) | PARTIAL — fold 1 prints as 0.013, the note says 0.014 (rounding slip; nothing rests on it) |
| last-step feature column std | "from 3.8e-4 to 7.9e11" | float64: max **7.936e11** (col 8); min **0.0 exactly** (col 9, constant 27.3325 in every window — `cost_basis` for one ticker with a fixed `purchase_date`); smallest non-zero 2.211e-2 (col 10). The matrix instrument reduces in float32: `X[:, -1, :].std(axis=0)` on float32 gives **3.815e-4** for the constant column — the note's 3.8e-4 is a float32 rounding artifact, not a feature scale | PARTIAL — the max and the 13-orders-of-magnitude point stand; the minimum is an instrument artifact and the true fact (an exactly constant column, hence an exactly rank-deficient design on that feature's 16 memory columns) is stronger than the note's |
| `dt` convention | — | `dt[:, 0] == 0` everywhere; no negative gaps | (not claimed; recorded) |
| constant column over all steps | "near-constant columns — `cost_basis`, `total_shares`" (§2.4) | exactly **one** feature column (col 9) has zero variance over **all 64 steps of all 1,698 windows** (value 27.3325); every other column varies | CONFIRMED and sharpened — one column is exactly, not nearly, constant |
| chronological order of the `full` view | — | `window_end_date` non-decreasing, 20150406 → 20211229; no `*_full` keys in the file (decision-11 artifact) | (not claimed; recorded — the fold cut by row index is a chronological cut) |
| archive comparison | "all 28 keys byte-identical" to `scenario-a-runs/20261003T091414Z-4ba6/data/` | 28/28 `np.array_equal`, 28/28 `tobytes()` equal, same key set; the **NPZ files themselves** are byte-identical: sha256 `cff84fe5cd9c1c0ad71fce3bf5db61c313fdab257f5fff4adeaa7bbaec79c550`, 133,161 bytes, for the 2026-10-03 archive, the predecessor's 2026-10-04 run dir and my 2026-10-05 mint | CONFIRMED (and stronger: the container is identical too) |
| meta `checksum` of the two mints | `037baab7…` (2026-10-03) vs `c02004e1…` (2026-10-04) | archive `…4ba6/data/*.meta.json` (created 2026-10-03T09:14:24Z): **`c02004e1708e489a…`**; predecessor's (created 2026-10-04T21:06:08Z): `c02004e1…`; mine (2026-10-05T13:30:38Z): `c02004e1…`; normalised sibling `97e778900093da01…` on both 10-04 and 10-05 | REFUTED as stated — see §7 |

## 6. What the comparison step found beyond the note's claims

### 6.1 Service vs in-process: identical at the printed digits, not "to every printed digit"

§0.2 / §2.5 say the in-process cells reproduce the HTTP control "to every printed digit (aggregate −20,344.64; fold 0 −93,606.23)". The JSON — the predecessor's as much as mine — says:

| quantity | HTTP service (2026-10-04 and 2026-10-05 and the repeat: 3 runs, bitwise equal) | in-process matrix (2026-10-04 and 2026-10-05: 2 runs, bitwise equal) | rel. diff |
| --- | --- | --- | --- |
| service-defaults fold 0 eval r² | −93606.2421298088 (prints −93,606.**24**) | −93606.2310410387 (prints −93,606.**23**) | 1.2e-7 |
| service-defaults aggregate | −20344.637730773607 | −20344.635437913923 | 1.1e-7 |
| E-H fold 0 eval r² | −0.08027410347435637 | −0.08027397550443771 | 1.6e-6 |
| E-H aggregate | −0.11526096841533144 | −0.11526091596856643 | 4.6e-7 |

Identical at the 4–5 significant figures the tables print; the parenthetical's "fold 0 −93,606.23" is the in-process value, and the HTTP value rounds to −93,606.24. **PARTIAL.** The gap is of the same order for the sane RFF cell as for the catastrophic one, so it is not ill-conditioning; it is some difference between the service process and a standalone interpreter that I could not identify (§8).

### 6.2 Digit stability of the ridge-0 cell (what §2.4 attributes to "BLAS reduction order, thread count")

Measured with `fold-threads` on the same NPZ (`50-*`, `51-*`, `53-*`, `54-*`, `55-*`, `56-*`):

| condition | service-defaults fold 0 eval r² | aggregate | rff/1.0 aggregate |
| --- | --- | --- | --- |
| same configuration, repeated (service ×3 over two days; matrix ×2 over two days; standalone probes ×10) | **bitwise identical within each launch mode** | bitwise | bitwise |
| OpenBLAS threads 1 | −93606.3265563381 | −20344.667583946724 | −0.11526091596856629 |
| 2 | −93607.13621308593 | −20344.715814320654 | −0.11526091596856673 |
| 3 | −93606.62118269815 | — | — |
| **4** | **−93570.74060137903** | **−20337.575466922586** | −0.11526091596856655 |
| 5 | −93606.2251794564 | — | — |
| 6, 8, 10, 12, 14, 15, 16 | −93606.2310410387 | −20344.635437913923 | −0.11526091596856643 |
| input alignment (offsets 1, 3 elements), heap perturbation, fresh contiguous copies, pre-fit reductions, second cell in-process | −93606.2310410387 (all six variants) | — | — |

So: thread count moves the ridge-0 fold-0 number by up to **rel 3.8e-4** (4 threads) — the 4th significant figure — and the aggregate by 3.5e-4, while the RFF ridge-1 aggregate moves by **4e-16** (3 ulps). *That* half of §2.4 holds: on this design the min-norm solve is sensitive to reduction order in a way the regularised, standardised rung is not. But the sensitivity is three to four orders of magnitude below "reproducible only to its order of magnitude", and nothing I varied reaches the audited gap: fold 0 **−83,452 (2026-10-03) vs −93,606** is rel **0.11–0.12**, ~300× the largest rounding effect produced here. No thread count from 1 to 16 reproduces the service's −93606.2421 either (`54-thread-sweep-fold0.json`).

## 7. The two checksums (§1.1, F-P8) and what the audit's crossval consumed

- `juniper_data/core/artifacts.py:50` — `compute_checksum(arrays)` = SHA-256 of `np.savez` over the **arrays with keys sorted** (`arrays_to_bytes`). `api/http_cache.py` documents it as "a CANONICAL serialization of the arrays … not the compressed bytes a store serves". Recomputing it with juniper-data's own function over the archived 2026-10-03 arrays and over mine gives `c02004e1…` both times. Every zip entry of all three NPZ containers carries the fixed date `(1980, 1, 1, 0, 0, 0)` — there are no write timestamps in the container. The note's mechanism — "it fingerprints the NPZ container, whose zip entries carry write timestamps, not the arrays" — is **REFUTED** by the source, by the containers and by recomputation.
- Where `037baab7…` comes from: it is real, but it is **not the mint the note byte-compared**. `.amp/in/artifacts/recurrence-equities-audit/equities_seq-6.0.0-15505731cba5b86d.meta.json` (top level, not under `scenario-a-runs/…4ba6/data/`) and `40-seq-meta-http.txt` carry `037baab750acd80f…` with `created_at 2026-10-03T09:15:49Z`. The audit's `20-data.log` shows that mint being created on the **manual shadow stack's** data service at `:8110` (run `20261003T091338Z-ef01`, `scenario-a-manual/ports.json`), 85 s after the suite run `4ba6` minted `c02004e1…` on its own data service at `:8111` (`…4ba6/manifest.json`, `created_at 09:14:24Z`). Same request, same generator code (juniper-data's commits between then and now are CI bumps), two cold per-run caches, two different array-level checksums. The `scenario-a-manual/data/` directory in the archive is **empty**: for the `037baab7` mint there is **NO ARTIFACT**, so what differed in its arrays, and by how much, cannot be said.
- Which mint the audited numbers came from: `24-c-crossval-shadow.txt` (09:16:51Z, `POST /v1/crossval` to the manual stack's recurrence at `:8260`, whose `JUNIPER_DATA_URL` is the `:8110` service; `21-recurrence-shadow.log` line 14) is the −83,452 / −18,081 measurement, and it ran 62 s after the `037baab7` mint on that service. The §1.3 premise "Same arrays (§1.1) … and the fold-0 number moved by 12 %" is therefore **unsupported**: the arrays the note byte-compared (`c02004e1`, run `4ba6`) are the ones every 2026-10-04/05 number used, and they reproduce bitwise; the 2026-10-03 number used a mint whose array checksum differs and whose arrays are gone. The note's own first reading — "the equities data drifted under the same id" — is the only one consistent with `compute_checksum`, and `http_cache.py` already warns that `dataset_id` hashes the request, not the content. The in-sample train r² differing between the two days (§2, last column) points the same way, since in-sample fit on the row space is not where a cond-1e32 solve is fragile.
- Consequence for the plan's F-P8 ("checksum fingerprints the container, not the arrays; two mints … differ in checksum while all 28 arrays are byte-identical", Minor): the two mints whose arrays were compared have the **same** checksum; the mint with the different checksum was never array-compared. That is a Lane B matter (what F-P8 should say, and whether "equities data can differ under one id across data-service instances" belongs in the DATA findings at a higher severity); this lane reports only that the recorded finding does not match the artifacts.

## 8. Claim register

| # | claim (where) | verdict | numbers / sample | instrument adequacy — could it have answered differently? |
| --- | --- | --- | --- | --- |
| 1 | Stack as served (§0.1) | CONFIRMED | checkouts, dists, modules, numpy, generator all as listed; 1 fresh stack | yes — read from the live env and health routes |
| 2 | Resolved id `…15505731cba5b86d` (§1.1) | CONFIRMED | `MATCH`, 1 mint | yes — the id is the service's answer |
| 3 | Normalised sibling `…fa3aae11ac374c94` (§2.1) | CONFIRMED | 1 mint; NPZ sha256 `5ec4b4d0…` equal to the predecessor's | yes |
| 4 | 28 keys byte-identical to the audit's `4ba6` archive (§1.1) | CONFIRMED | 28/28 arrays, 28/28 bytes, whole file identical; numpy only | yes — any byte difference would show |
| 5 | Checksum differs because the container carries timestamps (§1.1, F-P8) | **REFUTED** | source, zip dates all 1980-01-01, recomputation `c02004e1…` ×2, three metas equal | yes |
| 6 | "Same arrays" behind the 12 % fold-0 move (§1.3) | **REFUTED** (premise) | audited crossval consumed the `037baab7` mint; NO ARTIFACT for its arrays | partly — the archive proves which mint was used, not what its arrays were |
| 7 | E-H replay numbers (§1.2) | CONFIRMED | bitwise, 26 scalars, 1 run | yes |
| 8 | Service-defaults 2026-10-04 numbers (§1.3) | CONFIRMED | bitwise, 26 scalars, 1 run + 1 in-process repeat | yes |
| 9 | Audited class reproduces (§1.3) | CONFIRMED | −20,345 vs −18,081 same class; every ridge-0 cell catastrophic | yes |
| 10 | Audited digits "not expected to reproduce … rounding artefacts of an ill-posed solve" (§2.4, §4) | **PARTIAL → the attribution is REFUTED** | run-to-run bitwise (n = 2 days × 2–3 processes); thread count ≤ 3.8e-4; audited gap 0.11 on a different mint | yes — a bitwise comparison can only agree or not |
| 11 | W0.1 acceptance: 200 without `PYTHONPATH` (§1.3) | CONFIRMED | 3 HTTP 200s | yes |
| 12 | In-process = HTTP "to every printed digit" (§0.2, §2.5) | PARTIAL | equal at table precision; fold 0 −93,606.24 (HTTP) vs −93,606.23 (in-process); E-H agg rel 4.6e-7 | yes — visible in the predecessor's own JSON |
| 13 | 24-cell aggregates and per-fold values (§2.2) | CONFIRMED | bitwise, 24/24 cells × 5 folds | yes |
| 14 | Configured = fold-resolved twins; theta 91.0 everywhere (§2.2, §2.3c) | CONFIRMED | 12/12 pairs bitwise; numpy median = 91.0 per fold | yes; the numpy half is instrument-free |
| 15 | GCV 15 of 20 at λ = 1000 (§2.3, §3.2.2) | CONFIRMED | 15/20 fold-resolved (30/40 with twins) | yes |
| 16 | Train r² overfit tells 0.959 / 0.907 (§3.4) | CONFIRMED | bitwise | yes |
| 17 | Prediction-scale table (§2.2) | CONFIRMED | pred std / max |pred| bitwise, 24 cells | yes |
| 18 | Eval memory max |z| 8–199 raw, 11–337 normalised (§2.3d) | CONFIRMED | bitwise | yes |
| 19 | Conditioning table (§2.4) | CONFIRMED | 10/10 rows bitwise | reproducibility only (same instrument) |
| 20 | Last-step std "3.8e-4 to 7.9e11" (§2.3a) | PARTIAL | max 7.936e11 ✓; min is a float32 artifact of an exactly constant column | yes — float64 vs float32 reductions disagree |
| 21 | Target std per fold (§1.2, §2.2) | PARTIAL (one rounding slip) | fold 1 = 0.01347 | yes |
| 22 | `sum(dt)` 88–97, mean 91.3, std 1.7; target 0.00101 / 0.01835; partitions; fold sizes (§0.1) | CONFIRMED | numpy only | yes |
| 23 | Only the RFF rung standardises; linear solves the raw design (§2.3a/d) | CONFIRMED (source) | `readouts.py:182–193` vs `:298` | n/a (source read) |
| 24 | Wall times (11.2 s / 10.9 s / ≈13 min) | PARTIAL | 15.4 s / 17.9 s / 957 s — same class, slower | yes |
| 25 | Scenario A suite re-run (§1.4) | COULD NOT RUN — not attempted; outside this lane's brief | — | — |
| 26 | What the `037baab7` arrays were | NO ARTIFACT | `scenario-a-manual/data/` empty | — |
| 27 | Cause of the service-vs-standalone 1e-7 gap (§6.1) | COULD NOT DETERMINE | not thread count (1–16), alignment, heap state, load path, kwargs, pre-fit reductions | — |

## 9. Tallies

- **CONFIRMED: 17** (claims 1–4, 7–9, 11, 13–19, 22, 23).
- **PARTIAL: 5** (10 — the mechanism exists at the 4th–5th digit but does not reach the audited gap; 12, 20, 21, 24).
- **REFUTED: 2** (5, 6) — both about the provenance of the 2026-10-03 numbers, neither about the 2026-10-04 measurements.
- **COULD NOT RUN / NO ARTIFACT / COULD NOT DETERMINE: 3** (25, 26, 27).
- Matrix: **24 of 24 cells reproduce to every printed digit** (bitwise); replays: **2 of 2** (bitwise); conditioning: **10 of 10** rows (bitwise); the §2.4 run-to-run prediction: **0 of 6** readout/ridge groups moved.

## 10. What this evidence cannot support

- Anything beyond one ticker (AAPL), one window (2015–2022), one seed, five expanding folds, `d = 16`, this host and this OpenBLAS — the note's own §2.5 list stands, and so does "no demonstrated skill" (r² ≈ −0.1 is not better than the mean).
- What the `037baab7` mint's arrays contained, how far they were from `c02004e1`'s, or whether the 2026-10-03 digits would reproduce on them: there is no artifact. Only that the audited request consumed that mint, and that the checksum is array-determined.
- Whether another host, BLAS, or thread count reproduces the 2026-10-04/05 digits beyond the 4th significant figure — only that on this host they are bitwise stable per launch mode and move in the 4th figure with thread count.
- The cause of the 1e-7 service-vs-standalone difference (§6.1); it affects sane and catastrophic cells alike and changes no printed table digit.
- The GO verdict, the R5 band and W1.1(a): Lane B questions. This lane says only that every measurement those rest on reproduces exactly, and that the note's account of *why the 2026-10-03 number differs* does not.
- The service-core half of W0.1 (not applied; `:8202` still live) — untouched by this lane, as by the note.

## 11. Changed / created files

- **Created**: `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3.md` (this report); `reports/2026-10-05_recurrence-equities-cv-consensus/laneA3-rerun/*` (evidence, §12); `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py` (v0.3.0; `checks` / `compare` / `fold-threads`).
- **Not modified**: the note, the plan, `reports/2026-10-04_recurrence-equities-cv-matrix/*`, any checkout, the `.amp/` archive, the foreign stack. No git write commands were run.

## 12. Evidence index (`laneA3-rerun/`)

`00-stack-up.log`, `01-data-health.json`, `01-recurrence-health-mine.json`, `02-listeners-up.txt`, `03-launch.log`, `04-juniper-*-after-replay.log`, `05-blas-threadpool.txt`, `06-ports.json` — stack record. `00-dataset-create.json`, `01-recurrence-health.json`, `10-crossval-eh-rff.json`, `10-crossval-service-defaults.json`, `10-replay-stdout.log`, `11-crossval-service-defaults-repeat.json` — replay. `20-matrix-datasets.json`, `21-matrix-cells.json`, `22-matrix-table.md`, `20-matrix-stdout.log` — matrix. `23-linear-conditioning.json`, `23-conditioning-stdout.log` — conditioning. `30-numpy-checks.json`, `30-numpy-checks-stdout.log`, `data/` (both NPZs + metas as minted) — numpy checks. `40-compare.json`, `41-compare.md` — digit-level comparison. `50-fold-threads-*.json`, `51-ab-isolation-*.json`, `52-pure-matrix-path-repro.log`, `53-alignment-probe.json`, `54-thread-sweep-fold0.json`, `55-heap-state-probe.json`, `56-thread-sweep-rff.json` (+ `.log`s) — digit-stability probes. `90-stack-down.log`, `91-listeners-after-down.txt` — teardown.
