# Juniper-Recurrence × Equities — End-to-End Audit and Development Plan

- **Project**: Juniper — juniper-recurrence (with juniper-data, juniper-data-client, juniper-canopy, juniper-ml experiment stack)
- **Author**: Paul Calnon
- **Date**: 2026-10-03
- **Version**: 1.3.0
- **Status**: VALIDATED BY CONSENSUS at v1.2.0 (two rounds; record: `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`); **P0 execution started 2026-10-04** (v1.3.0: W0.8/W0.9 measured, verdict GO, status table live, W5.8/W5.9 proposed, F-P8 added). The v1.3.0 additions are the author's and have not been through a consensus round; the W5.1 note they rest on is owed one before R5 is ruled.
- **Owner**: Paul Calnon
- **Template**: `notes/templates/TEMPLATE_DEVELOPMENT_ROADMAP.md`
- **Evidence**: `juniper-ml/.amp/in/artifacts/recurrence-equities-audit/` (103 files; git-excluded; see §2.3 for the index)

---

## Overview

The project reports errors running the juniper-recurrence (LMU) model against juniper-data's equities datasets. This note audits that path end to end — environment, launcher, service, model, producer contract, canopy integration, CLI experiment driver, tests, CI, logging and documentation — for both launch modes (juniper-canopy one-shot fit; juniper-ml CLI experiment stack), reproduces the failures live, and lays out a phased development plan with acceptance tests and owners.

The headline result is that **there is no single bug**. Four independent defects compound, two deployment and concurrency gaps sit around them, and a scientific-validity problem is exposed as soon as the first four are cleared:

1. **Environment (ENV)**: the conda env the launcher defaults to (`JuniperCascor1`) serves a stale `juniper-recurrence-model 0.1.5` wheel that lacks `derive_full_split`, so `POST /v1/crossval` fails with `NPZ artifact is missing required key 'X_full'` on every post-decision-11 artifact. The launcher does no dependency preflight and `/v1/health/ready` passes anyway.
2. **Driver (CODE)**: the suite runner records that failed cell as `outcome: succeeded`, exits 0, and its aggregate carries no recurrence metric at all — so the breakage was invisible to the one tool meant to surface it.
3. **Parameters (DATA + CODE)**: `equities_seq` at bare defaults is untrainable (`fundamentals_fill="nan"` → non-finite `X`); the headless CLI has `--generator` but no way to pass params; canopy forwards operator-staged params that defeat its own safe seed and then drops the service's 422 detail body before it reaches the log or the UI.
4. **Contract (DATA)**: published juniper-data 0.16.0 still serves `equities_seq` as `5.0.0 / classification`, which canopy's regression gate refuses; `main` is `6.0.0 / regression`.
5. **Deployment (DEPLOY)**: `juniper-deploy/docker-compose.yml` pins juniper-data 0.16.0, juniper-recurrence 0.5.0 and canopy 0.8.1, so the published stack reproduces item 4 by construction, and the recurrence Compose service mounts no snapshot volume. No earlier draft of this plan owned the Compose update.
6. **Concurrency (CONCURRENCY)**: canopy and the CLI stack can address the same recurrence service; one `train_lock`, no run identity on predict/snapshot, no cancellation, and a 30 s data-client timeout inside the service that none of the outer timeouts know about.
7. **Science (SCI)**: with ENV fixed, shadowed cross-validation **runs** but — under the service defaults the audit request actually exercised (`readout=linear`, `ridge=0.0`) — returns an aggregate eval `r2 = −18,081` (per-fold −3.7 … −83,452) against in-fold train `r2 = +0.14 … +0.45`. The cause is unresolved (§3.9). The equities path has never produced a credible out-of-sample metric; the suite comment that expects "r2 ≈ 0, NOT negative blowups" is not encoded anywhere as a check.

### Scope & Timeframe

- **Timeframe**: 2026-10 to 2026-12 (six phases; P0 within two weeks of approval). Dates assume one owner plus agent sessions, serialised across repos — see "Milestones".
- **Product area(s)**: juniper-recurrence (app, model, client, bench, CI), juniper-data equities generators and REST error surface, juniper-data-client NPZ validator, juniper-canopy recurrence adapter/backend/registry/UI, juniper-ml `util/experiment_stack.bash` + `util/experiments/*`, juniper-deploy Compose pins, documentation across all of the above and the parent `AGENTS.md`
- **Target version(s)**: juniper-recurrence 0.6.0, juniper-recurrence-model 0.4.0, juniper-data-client 0.6.0, juniper-data 0.17.0, juniper-canopy 0.9.0, juniper-ml 0.11.0, juniper-deploy (Compose pins bumped in step)

### Out of Scope

- Changing the equities feature set, the SEC/yfinance ingestion, or the symbol ceiling (`juniper-data#395`, `#404`, the 14-symbol cap) — this plan consumes the producer contract as it stands at `5.0.0` / `6.0.0`.
- The CasCor path against equities (covered by its own notes).
- Flat 2-D `equities` as a recurrence input. It is correctly refused today (§3.3 F-S4) and stays refused; a windowing adapter is a future idea (see "Out-of-Scope / Future Ideas").
- Implementing any fix. This arc is planning only.

---

## 1. What the operator actually sees today

Two launch paths, four distinct symptoms. All reproduced live on 2026-10-03 (§2).

| Launch path | Operator action | What happens | Root class |
| --- | --- | --- | --- |
| CLI stack (`experiment_stack.bash --up --recurrence`, `run_suite.py --suite p4/e-h-recurrence-real-data.yaml`) | Runs the recorded E-H suite | Train 200 (`r2 0.116` in-sample); crossval **422** `missing required key 'X_full'`; predict 200. Suite prints `c001: succeeded`, exits 0, `registry.jsonl` has `exit_code: 1`, `metrics: {}`. | ENV + CODE (driver) |
| CLI headless (`juniper-recurrence train --generator equities_seq`) | Tries to fit from the CLI | `--params` does not exist → exit 2; without params the generator runs at bare defaults → **422** `X_train has non-finite values (NaN/Inf)` | CODE + DATA |
| Canopy, no staging | Select Recurrence + `equities_seq`, Start | Fits with the registry seed (5 symbols, `return`, `drop`): 200, `r2 0.008`, 46.5 s, 15,592 windows | Works — but see SCI |
| Canopy, after Apply | Stage equities form (e.g. `next_close`, `start_date 2000-01-01`, `max_symbols 14`, `normalize_features`), Start | Staged values override the seed; generic `n_samples`/`noise` may be forwarded → juniper-data **422**; the UI and `system.log` show only `recurrence service error 422 on POST /v1/train` with no detail; a long fit trips the 300 s timeout → canopy `failed` while the service keeps fitting → next Start gets **409** | CODE (canopy) |
| Canopy against published juniper-data 0.16.0 (or the Compose stack, which pins it) | Select Recurrence + `equities_seq` | Registry requires `task_type: regression`; 0.16.0 serves `equities_seq` as `classification` → pair refused | DATA (release lag) + DEPLOY (pins) |

Correction to an earlier premise: a recurrence × equities run **did** exist historically — `~/.local/state/juniper-experiments/index.jsonl` (477 rows at audit time) carries two rows dated 2026-08-09 for E-H cell `c001-0d8782ae` (`equities_seq-1.0.0-075eb51abb6d2dbe`, recurrence 0.2.0, 10 features). It predates decision 11 and says nothing about today's path.
The same index now also carries the 2026-10-03 Scenario-A replay, recorded as `succeeded` with acceptance failed on `X_full` — the F-D1 defect written into the shared run state.

---

## 2. How the audit was run

### 2.1 Instruments

- **Live reproduction** (two scenarios) on loopback ports consistent with the launcher's ranges (data 8110, recurrence 8260), everything torn down afterwards (`99-final-listeners.txt`).
  - Scenario A: the launcher exactly as an operator runs it (`JuniperCascor1` as served), then `run_suite.py` on the E-H suite.
  - Scenario B: code-vs-env separation — the same service started with `PYTHONPATH` shadowing the stale wheels with the checkout (`juniper-recurrence-model` 0.3.0, `juniper-service-core` 0.7.0), then driven request by request with curl (train AAPL, train canopy seed, crossval shadowed and plain, predict, flat `equities`, bare defaults, CLI `train`).
    The curl bodies carried only the dataset selector and fold settings — **no readout, ridge or theta** — so every Scenario-B fit ran at the service defaults (`readout=linear`, `default_ridge=0.0`, data-driven theta), not at the E-H suite's `irregular-sine-rff.yaml` base config. §3.9 is written against what was measured.
- **Test suites** of all four recurrence packages plus the repo-level suite, run twice each (shadowed vs as-served), plus canopy's recurrence tests in `JuniperCanopy1`, juniper-data's equities unit tests in `JuniperData`, and juniper-ml's driver/suite tests in `JuniperCascor1`.
- **Static audit** by seven independent read-only workers with distinct briefs (canopy integration; tests/bench/CI; documentation; logging; CLI driver; producer contract; live repro).
  Every claim they returned that this plan relies on was re-derived by the reconciler against the file or artifact it cites (§5.2 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).
  The load-bearing ones (`--params` absent, `RequestIdMiddleware` absent, `_STAGED_PARAM_KEYS`, `lifecycle.run` unguarded, suite `outcome` derivation, `_headline_metrics` key mismatch, crossval fold values) were re-opened by hand.

Could the instruments have produced a different answer? Yes: Scenario B's shadowed crossval returned 200 where Scenario A's returned 422 on the same artifact and the same request, which is what makes the ENV attribution a measurement rather than a story. Sample size is one host, one day, one ticker set — see "Risks & Assumptions" for what that cannot support.

### 2.2 Baseline environment facts (verified)

| Fact | Evidence |
| --- | --- |
| `JuniperCascor1`: `juniper-recurrence 0.5.0` editable; `juniper-recurrence-model 0.1.5` wheel; `juniper-service-core` **pip metadata 0.5.0 but the importable module reports `0.4.0`** (two installs disagree — the env is inconsistent with itself, not merely stale); `pip check` flags both against the app's pins (`>=0.3.0,<0.4.0`, `>=0.6.0,<0.8.0`). `pip check` also lists unrelated CUDA/torch mismatches, so a preflight must scope to the recurrence dependency closure. | `00-baseline.txt:5,12,16` |
| `derive_full_split` is absent from the as-served model wheel: bench tests fail with `cannot import name 'derive_full_split'`; `/v1/crossval` 422s on it | `tests-bench-env.log`; `31-c-crossval-plain.txt` |
| `JuniperData`: juniper-data editable (current `main`, `equities_seq` 6.0.0); yfinance present | `00-baseline.txt`, `40-seq-meta-http.txt` |
| `JuniperCanopy1`: libtorch ABI break (`undefined symbol: _PyObject_NextNotImplemented`) → canopy's recurrence tests error out | canopy test run (§3.7 F-T9) |
| `experiment_stack.bash:142` defaults the recurrence env to `JuniperCascor1`; parent `AGENTS.md` says recurrence "has no conda environment" | `util/experiment_stack.bash:67,142` |

### 2.3 Evidence index

All under `juniper-ml/.amp/in/artifacts/recurrence-equities-audit/`:

- `00-baseline.txt` — pip check, versions, shadow check
- `10-scenario-a-launch.txt`, `11-scenario-a-suite.txt` (+ `.exit`), `12-scenario-a-down.txt`, `scenario-a-suite/{registry.jsonl,aggregate.csv,REPORT.md,suite_manifest.json}`, `scenario-a-runs/<run_id>/{manifest.json,logs/*.log,artifacts/results/stats.json,config/*.yaml}`
- `20-data.log`, `21-recurrence-shadow.log`, `30-recurrence-plain.log`
- `22-a-train-aapl.txt`, `23-b-train-canopy-seed.txt`, `24-c-crossval-shadow.txt`, `25-d-predict.txt`, `26-e-flat-equities.txt`, `27-f-default-nan.txt`, `28-e-flat-equities-retry.txt`, `31-c-crossval-plain.txt`, `32/33-g-cli-params-*.txt`, `34-g-cli-help.txt`
- `40-seq-meta-http.txt`, `41-flat-meta-http.txt`, `42-npz-inventory.json`, `*.meta.json`
- `tests-{app,model,client,bench,root}-{shadowed,env}.log`
- `99-final-listeners.txt`

---

## 3. Findings register

Each finding carries an ID used by the work items in §6. Severity: **Blocker** (the path cannot run or lies about running), **Major** (wrong result or operator cannot diagnose), **Minor**, **Doc**. Owner is the repo that must change.

### 3.1 Environment and launcher (ENV)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-E1 | Blocker | `JuniperCascor1` serves model 0.1.5 and service-core 0.5.0 under an app pinned to `>=0.3.0,<0.4.0` / `>=0.6.0,<0.8.0`. 0.1.5 lacks `derive_full_split`, so every `split="full"` request (`/v1/crossval`) 422s with `missing required key 'X_full'`. Shadowed checkout returns 200 on the same request. | `00-baseline.txt` (versions); `tests-bench-env.log` (import failure ×14); `31-c-crossval-plain.txt` vs `24-c-crossval-shadow.txt`; `routers/crossval.py:65-73` | host env / juniper-ml launcher |
| F-E2 | Blocker | The launcher gates the recurrence env on the console script existing and on `/v1/health/ready` only; no `pip check`, no version floor, no import probe. | `util/experiment_stack.bash:731-757`; `util/isolated_stack.bash:363-380` | juniper-ml |
| F-E3 | Major | Readiness is too shallow to certify crossval: it does not exercise full-split derivation, so a stale model passes readiness and fails on the first `split="full"` request. | `routers/crossval.py:65-73`; §3.1 F-E1 | juniper-recurrence |
| F-E4 | Major | Bench tests under the as-served env: 14 failed / 23 passed (all `cannot import name 'derive_full_split'`); shadowed: 37 passed. App: 1 failure as-served (`test_docs_require_auth_when_enabled`, `assert 200 == 401`, a service-core 0.5.0 behaviour). | `tests-bench-env.log`, `tests-bench-shadowed.log`, `tests-app-env.log` | host env |
| F-E5 | Doc | Parent `AGENTS.md` and `juniper-recurrence/AGENTS.md:126` say recurrence has no conda environment; both host launchers default to `JuniperCascor1`. The mismatch is exactly how F-E1 went unnoticed. | `util/experiment_stack.bash:67,142`; `util/isolated_stack.bash:44-46,94-97` | juniper-ml, juniper-recurrence, parent `AGENTS.md` |

### 3.2 CLI experiment driver and suite (DRV)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-D1 | Blocker | A cell whose crossval 422'd is recorded `outcome: succeeded` with `exit_code: 1`, `acceptance.ok: false`; the suite prints `succeeded`, counts a success, exits 0. `run_suite.py:694` copies `manifest.outcome`, which the driver sets from train alone (`run_experiment.py:1993`); crossval/predict failures only add acceptance reasons (`:1932-1948`). | `scenario-a-suite/registry.jsonl`; `11-scenario-a-suite.exit` = 0; `run_suite.py:694,781-782`; `run_experiment.py:1993,2030` | juniper-ml |
| F-D2 | Blocker | `_headline_metrics` reads `train_r2`/`cv_r2`/`r2` at the top of `stats["recurrence"]`, but the train numbers nest under `final_metrics` → `metrics: {}` for every recurrence cell; `aggregate.csv`/`REPORT.md` carry no r2. | `run_suite.py:585-600`; `scenario-a-runs/…/artifacts/results/stats.json`; `run_experiment.py:1999-2004` | juniper-ml |
| F-D3 | Major | The E-H suite comment expects "r2 ≈ 0 … NOT negative blowups" but no band is encoded; plan R-6 makes equities rows informational. A −18081 aggregate passes. | `suites/p4/e-h-recurrence-real-data.yaml:1-3`; `…EXPERIMENTATION-PLAN.md:904-919,1241` | juniper-ml |
| F-D4 | Major | `save_model` re-runs `juniper-recurrence train` via `shutil.which` on the **driver's** PATH, not the launcher-selected env; a missing CLI becomes an acceptance failure (exit 1) with the run still `succeeded`. | `run_experiment.py:1869-1890,2013-2022` | juniper-ml |
| F-D5 | Major | Timeouts are split and non-cancelling: dataset creation 120 s fixed; train/predict/crossval `max_wall_seconds` (900 s); suite 1200 s; none governs the service's **inner** 30 s data-client default (F-S9). | `run_experiment.py:831,1932-1938,1973-1979`; `run_suite.py:683-689`; `routers/training.py:44-105`; §3.3 F-S9 | juniper-ml, juniper-recurrence |
| F-D6 | Minor | Per-run `JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache` → cold Yahoo/SEC fetch on every cell; the plan's `--shared-equities-cache` opt-in (H-9) is not implemented. | `util/experiment_stack.bash:492-500,607-618`; `…EXPERIMENTATION-PLAN.md:781,1241` | juniper-ml |
| F-D7 | Major | On failure the manifest stores HTTP detail truncated to 500 chars (read from the code path; the audited 422 body was shorter, so truncation was not observed), no service-log tail, and `completion_reason: None` hard-coded. | `run_experiment.py:406-428,466-472,1981-1984,2083` | juniper-ml |
| F-D8 | Minor | `stats_summary.py` reports sequence dimensions and class distribution but no regression-target summary (plan requires "class balance or target summary stats"). | `util/experiments/stats_summary.py:124-153` | juniper-ml |
| F-D9 | Minor | `recurrence_up` creates `${RUN_DIR}/snapshots` but does not export `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`; snapshots land in `${RUN_DIR}/recurrence-snapshots` (settings default is CWD-relative). | `util/experiment_stack.bash:492,736-754`; `settings.py:201-204` | juniper-ml |
| F-D10 | Minor (accepted) | `isolated_stack.bash:100` still defaults its whole scratch tree to `${TMPDIR:-/tmp}/juniper-e2e` (reaping hazard the comments acknowledge). No script source is written to `/tmp`, so the ecosystem rule is not breached; **disposition: accepted, no work item** — the isolated stack is a disposable E2E scratch tree by design. | `util/isolated_stack.bash:100,275-276` | juniper-ml |

Details (DRV):

- **F-D2** — The audited `stats.json` has `crossval: null` (the phase failed), so the crossval nesting (`crossval.eval_aggregate`) is read from the driver's writer at `run_experiment.py:1999-2004`, not observed in an artifact.
- **F-D5** — The 120 s budget covers dataset creation, where the cold yfinance fetch happens. A client timeout does not stop the service, which keeps `train_lock` until its `finally`. Because no outer budget governs the inner data-client call, a cold `equities_seq` creation can fail inside recurrence while every outer timer is still green.

### 3.3 Recurrence service and model code (SVC)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-S1 | Blocker | `juniper-recurrence train` exposes `--generator` but no `--params`/`--params-file`; the CLI passes no `params`, so `load_sequence_data` receives `None` and `data.py` substitutes `{}` — equities runs at bare defaults and 422s on NaN. The only CLI route to a trainable equities fit is `--dataset <id>` of an artifact minted elsewhere. | `main.py:50-66,137-144`; `data.py:45-46`; `32/33-g-cli-params-*.txt` (exit 2) | juniper-recurrence |
| F-S2 | Major | Reader prefers `y_reg_{split}` but silently falls back to one-hot `y_{split}`; a regression run becomes a two-output direction fit with no warning. | `juniper_recurrence_model/data.py:153-159` | juniper-recurrence-model |
| F-S3 | Minor | `target_dt_*` and `seq_lengths_*` are read without finiteness/sign validation. | `juniper_recurrence_model/data.py:194-195` | juniper-recurrence-model |
| F-S4 | Verified control | Flat 2-D `equities` is refused: `X_train must be 3-D (W, L, F) for a sequence artifact; got 2-D` → 422. Message is correct and survives to the client. (The first attempt, `26-e-flat-equities.txt`, returned 409 because the bare-defaults request `27-f` issued 5 ms earlier was holding `train_lock` — see F-S6; the 422 is in the retry.) | `28-e-flat-equities-retry.txt`; `data.py:146-150`; `routers/_common.py:49-52` | — |
| F-S5 | Major | `/v1/train` reports **in-sample** metrics only (`final_metrics` on the train split); `/v1/predict` returns predictions without metrics. The only out-of-sample number the path can emit is crossval's — which is the one that fails (ENV) or blows up (SCI). | `22-a-train-aapl.txt`; `25-d-predict.txt`; `routers/training.py:88-105` | juniper-recurrence |
| F-S6 | Major | No cancellation: a fit continues after the caller times out; `train_lock` is acquired **before** the dataset fetch and held until the route's `finally`, so the next caller gets 409 `a training run is already in progress`. | `routers/training.py:44-105`; `23-b-train-canopy-seed.txt` vs `21-recurrence-shadow.log:11-12`; `26-e-flat-equities.txt` vs `27-f-default-nan.txt` | juniper-recurrence |
| F-S7 | Minor | The train start log reports `theta=None` for data-driven theta; the resolved value (`median(sum(dt))`) is never logged. | `routers/training.py:88`; `model.py:172-179` | juniper-recurrence |
| F-S8 | Minor | Readiness/metadata: recurrence never fetches or checks `task_type`; it validates the NPZ and reads `y_reg` directly, so it is indifferent to the 5.0.0/6.0.0 relabel (good) but cannot tell the operator a classification artifact was fed to a regression fit (bad, see F-S2). | `juniper_recurrence/data.py:73-92` | juniper-recurrence |
| F-S9 | Major | Inner timeout nobody configures: `load_sequence_data` constructs `JuniperDataClient(base_url=…, api_key=…)` with no `timeout`, so the client default of **30 s** governs dataset creation; no setting exposes it. | `juniper_recurrence/data.py:73`; `juniper_data_client/client.py:178-188,204`; `settings.py:174-178` | juniper-recurrence |

Details (SVC):

- **F-S6** — Reproduced: two `/v1/train` requests 5 ms apart — the second was refused in 3 ms (`26-e-flat-equities.txt`, `TIME_TOTAL=0.003`) while the first (`27-f-default-nan.txt`) was still fetching its dataset. The canopy-seed fit spent 12 s in dataset fetch (curl 46.5 s in `23-b-train-canopy-seed.txt` vs logged `duration=34.463s`) with the lock held and nothing logged.
- **F-S9** — A cold `equities_seq` request (yfinance + SEC for several symbols) can exceed 30 s; the failure surfaces as a 502-class dataset error inside recurrence while canopy's 300 s and the driver's 120 s budgets are untouched. The canopy-seed fetch took 12 s with AAPL already cached and four symbols cold; a cold 14-symbol fetch is the risk case. `settings.py:174-178` carries URL and key only.

### 3.4 Producer contract — juniper-data and juniper-data-client (DATA)

Key inventory for `equities_seq` (per split `train/val/test`, from `42-npz-inventory.json` and the producer): `X (W,64,15) f32`, `y (W,2) f32` one-hot, `y_reg (W,1) f32`, `date (W,64) i32`, `dt (W,64) f32` calendar-day gaps with `dt[:,0]=0`, `target_dt (W,) f32`, `window_end_date (W,) i32`, `ticker_code (W,) i32`, `observed_mask (W,64) u8` (the inventory proves shape/dtype/finiteness; "all ones" is read from the producer, which emits no gaps), `ticker_vocab (E,) <U`.
Not emitted: `seq_lengths_*`, `t_*`, `padding_mask_*`, `*_full`. Flat `equities`: `X (N,15) f32`, `y (N,2)`, `y_reg (N,1)`, provenance date arrays.
All numeric keys were 100 % finite in the audited artifacts (which were minted with `drop` or with no fundamentals columns missing for AAPL).

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-P1 | Blocker | Bare defaults are untrainable: `fundamentals_fill="nan"`, `normalize_features=False`, `regression_target="next_close"` → NaN in columns 7/8/14 (`total_shares`, `market_cap`, `days_since_report`) → recurrence 422 `X_train has non-finite values`. Canopy measured 9.1 % non-finite at defaults. (`juniper-data#409`) | `equities/defaults.py:33-50,103`; `27-f-default-nan.txt`; `model_registry.py:306-330` | juniper-data (preset) + every caller (explicit params) |
| F-P2 | Major | `cost_basis` is NaN before `purchase_date` regardless of `fundamentals_fill`; `drop` only removes missing-share rows. A purchase date after series start yields non-finite windows under `drop`. | `equities/generator.py:924-927,938-956` | juniper-data (owner ruling) |
| F-P3 | Major | `validate_npz_contract` checks `dt` shape/sign/first-zero but not finiteness, ignores `target_dt`, and does not enforce dtype — the advertised full-contract gate is partial. | `juniper_data_client/contract.py:1338-1428` | juniper-data-client |
| F-P4 | Blocker (deployment) | Published juniper-data 0.16.0 (PyPI latest as of 2026-10-03; no 0.17.0) serves `equities_seq` at `5.0.0 / classification / n_classes 2`; `main` is `6.0.0 / regression / null` (#437, X8). Canopy's regression gate refuses the pair against the published image. | parent `AGENTS.md` Data Contract; `40-seq-meta-http.txt`; PyPI probe (`laneA3.md` §6); §3.10 | juniper-data release + juniper-ml floors + juniper-deploy pins |
| F-P5 | Major | Per-symbol fetch failures are caught and skipped; the universe can shrink silently with no truncation metadata. | `equities/generator.py:319-329`; `equities_seq/generator.py:156-168` | juniper-data |
| F-P6 | Minor | No positivity/finiteness guard on `close` before `return`/`log_return`; a zero close yields Inf/NaN in `y_reg` (caught downstream by the reader). | `equities/generator.py:1283-1302` | juniper-data |
| F-P7 | Major (science) | Partitions are split-major with entity blocks inside each split; the retired `_full` was entity-major; `derive_full_split` faithfully rebuilds entity-major. Expanding folds by row index over a multi-ticker `full` view are therefore **not chronological**. | `equities_seq/generator.py:274-300`; `juniper_recurrence_model/data.py:103-126` | juniper-recurrence (CV design) |
| F-P8 | Minor (added v1.3.0) | The meta `checksum` fingerprints the NPZ **container**, not the arrays: two mints of one `dataset_id` (2026-10-03, 2026-10-04) differ in checksum while all 28 arrays are byte-identical. A checksum comparison reports a false "changed"; the `dataset_id` did pin the content. | `JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §1.1 | juniper-data (doc, or hash the arrays) |

Details (DATA):

- **F-P4** — `40-seq-meta-http.txt` shows `6.0.0` on `main`. §3.10 (F-DEP1) records the Compose pins that make the published 0.16.0 behaviour the default deployed state.

### 3.5 Canopy integration (CAN)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-C1 | Blocker | The service's 422 `detail` body is dropped end to end: adapter keeps it only as `body=` on the exception; `outbound_error_text` returns `str(exc)` for status-bearing errors; backend logs `recurrence fit failed: %s` with that string; UI shows `recurrence service error 422 on POST /v1/train` truncated to 120 chars. | `recurrence_service_adapter.py:325-333`; `outbound_errors.py:45-62`; `recurrence_backend.py:214-226,264-296`; `dashboard_manager.py:7337-7397` | juniper-canopy |
| F-C2 | Major | Staged form values override the registry seed wholesale (`params.update(cfg["nn_dataset_params"])`), so `regression_target: next_close`, `start_date: 2000-01-01`, `max_symbols: 14` from the equities form reach the service. No preview of the effective request before Start. | `recurrence_backend.py:126-131`; `model_registry.py:332-336`; `logs/juniper-canopy_2026-09-26_0332.log:219` | juniper-canopy |
| F-C3 | Major | Generic `nn_dataset_elements→n_samples`, `nn_dataset_noise→noise` are forwarded to `equities_seq`, which has no such params → juniper-data 422. | `recurrence_backend.py:104,127-130` | juniper-canopy |
| F-C4 | Major | 300 s adapter timeout vs. non-cancelling service (F-S6): canopy records `failed`, service keeps fitting, next Start → 409; UI text is `RecurrenceServiceTimeoutError` with no remedy. | `recurrence_service_adapter.py:101,210,318-319`; `recurrence_backend.py:220-225` | juniper-canopy |
| F-C5 | Minor | 401 remedy says "check recurrence_api_key" instead of `JUNIPER_CANOPY_RECURRENCE_API_KEY` (`_FILE`). | `recurrence_service_adapter.py:330-331`; `settings.py:547-565` | juniper-canopy |
| F-C6 | Minor | Service `StatusResponse.state` includes `restored` + `restored_from`; canopy models `idle` / `trained` only. | `schemas.py:179-196`; `recurrence_service_adapter.py:165-177,287-293` | juniper-canopy |
| F-C7 | Minor | 429 is a generic HTTP error; `Retry-After` is not surfaced. Dashboard polling cannot trip the 60 rpm limit (it polls canopy, not the service). | `recurrence_service_adapter.py:332-333`; `main.py:1491-1505` | juniper-canopy |
| F-C8 | Major | Registry displays recurrence model version `0.1.0`; service is `0.5.0`; canopy has no `juniper-recurrence` dependency or contract floor. | `model_registry.py:467,491`; canopy `pyproject.toml` | juniper-canopy |
| F-C9 | Minor | Recurrence availability (URL configured?) is not shown before selection; refusal after selection is actionable (names `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL`). | `main.py:3968-3980,4021-4022,4087-4090`; `dashboard_manager.py:3663-3668,8634-8639` | juniper-canopy |
| F-C10 | Verified control | Flat `equities` is gated off for recurrence client-side **and** server-side (`/api/stage_dataset` refusal). The regression metrics panel renders r2/rmse/mae honestly; nothing treats `loss` as accuracy. | `model_registry.py:267-276,485-495`; `main.py:4061-4066,4481-4487`; `metrics_panel.py:983-1002,1872-1911` | — |
| F-C11 | Minor | `system.log` lines read `None:<line>` because the custom logger calls `makeRecord(...)` without `func`; the `rotation: when: midnight` block in `app_config.yaml` is dead (handler is size-based, 500 MB × 5). | `src/logger/logger.py:251-272,288-305`; `conf/app_config.yaml:63-67,78-85,121-126` | juniper-canopy |

### 3.6 Logging and observability (LOG)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-L1 | Blocker | Exceptions inside the synchronous `lifecycle.run(...)` and `cross_validate(...)` are not caught or logged by the recurrence routes; the `logger.exception("Training failed")` in service-core lives only in the background-thread path. A numerical failure is a bare 500. | `routers/training.py:91`; `routers/crossval.py:117-130`; `juniper_service_core/lifecycle/manager.py:257-284` | juniper-recurrence |
| F-L2 | Blocker | No `RequestIdMiddleware` in `build_app()`; canopy sends no `X-Request-ID`; the data-client would forward a ContextVar id that is never set. Canopy → recurrence → juniper-data logs cannot be joined. | `app.py:93-139`; `recurrence_service_adapter.py:297-301`; `juniper_data_client/client.py:304-328`; `juniper_observability/request_id.py:62-89` | juniper-recurrence, juniper-canopy |
| F-L3 | Major | Service logs neither the generator params it sent to juniper-data nor the artifact inventory (keys/shapes/dtypes/finite fractions) before fitting; dataset failures log only the selector + `str(exc)`. | `juniper_recurrence/data.py:45-49,73-80`; `routers/training.py:58-60` | juniper-recurrence |
| F-L4 | Major | The model package has no logger calls: resolved theta, GCV λ, design rank, condition number, NaN after rollout, `np.linalg` warnings — nothing; `logging.captureWarnings` not enabled. | `model.py:172-179`; `readouts.py:183-193` | juniper-recurrence-model |
| F-L5 | Major | Snapshot router: listing swallows `except Exception: return {}`; save unguarded; restore catches everything → 422 without a log line; restore-lock 409 unlogged. | `routers/snapshots.py:118-122,153-166,200-206` | juniper-recurrence |
| F-L6 | Major | Non-2xx without any application log: predict-before-train 409, snapshot 4xx, security 401, quota 429 (only the failed-auth throttle logs). | `routers/predict.py:36-38`; `juniper_service_core/middleware.py:216-243` | juniper-recurrence, juniper-service-core |
| F-L7 | Major | `init_logging` runs in lifespan, after `uvicorn.run`, so boot/access lines use uvicorn's format; the CLI `train` never calls `init_logging` at all. | `app.py:62-68`; `main.py:71-84,121-175` | juniper-recurrence |
| F-L8 | Minor | Zero `logger.debug` calls in app or model; `service.log_level: DEBUG` changes nothing recurrence-specific. | `rg logger.debug` → no matches | juniper-recurrence |
| F-L9 | Major | Prometheus counters count successes only (`*_runs_total` incremented after success); no `*_failures_total`, no in-progress gauge, no duration histogram on failed attempts. | `metrics.py:26-72` | juniper-recurrence |
| F-L10 | Minor | Producer refuses over-cap universes and fills/drops NaN without a log line; the 422 body is correct but the producer log cannot corroborate it. | `equities/generator.py:507-510,719-736,799,924-936` | juniper-data |
| F-L11 | Minor | Launcher does not export `JUNIPER_RECURRENCE_LOG_LEVEL`/`LOG_FORMAT`; only the YAML `service:` block can set them. | `util/experiment_stack.bash:731-754` | juniper-ml |

### 3.7 Tests and CI (TST)

Current state (2026-10-03): app 234, model 141, client 75, bench 37, repo 57 (+7 subtests). Shadowed: all green. As-served: app 233/1, bench 23/14 (§3.1 F-E4). Canopy's recurrence tests: 5 failed / 15 errors, all libtorch ABI (env). juniper-data `test_val_emission_guards.py`: 16 passed; `-k equities` unit: 170 passed. juniper-ml driver/suite/launcher tests: 524 passed / 1 failed (unrelated E-C wall-budget pin) / 4 skipped.

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-T1 | Major | App fixtures are train-only synthetic stubs with `validate_npz_contract` monkeypatched to `lambda …: "sequence"`; `equities` vs `equities_seq` differ only in id resolution. No app test runs the real validator on an equities-shaped three-partition artifact. | `juniper-recurrence/tests/conftest.py:42-48,72`; `test_data_adapter.py:15-46` | juniper-recurrence |
| F-T2 | Major | No `/v1/train` route test for 2-D X, non-finite X, non-finite y, missing `dt`/`t`, or a juniper-data 422 (14-symbol cap). Present: 502, 409. | `tests/test_routes.py:64-71,118-122,213-225` | juniper-recurrence |
| F-T3 | Major | `test_crossval_routes.py` still builds only `*_full` keys (retired) and bypasses the validator; `/v1/crossval` is never proven on a no-`_full` artifact at route level. | `tests/test_crossval_routes.py:34-40,64` | juniper-recurrence |
| F-T4 | Major | App CI installs `juniper-recurrence-model` from PyPI (`pip install -e ".[test]"`), never the sibling checkout; model CI tests only the model. Both lanes can be green while app + model checkouts are incompatible — the exact shape of F-E1. | `.github/workflows/ci-recurrence-app.yml:126-135`; `pyproject.toml:53` | juniper-recurrence |
| F-T5 | Minor | Bench installs `[test,bench,bench-plots]`, not `[bench-equities]`; the equities row is recorded skipped; only registration is asserted. | `ci-recurrence-bench.yml:161-164`; `run_benchmark.py:350-356`; `test_bench_smoke.py:160` | juniper-recurrence |
| F-T6 | Minor | `recurrence#178` (open): `ci-recurrence-bench` is a **path-scoped lane**, so a break introduced by a dependency (model or client checkout, or a published juniper-data) does not trigger it. Its later fix commits mention a dispatch, but the issue is the trigger gap, not a PAT scope. The lane that would have caught F-E1's shape does not run on the changes that cause it. | `gh issue view 178` (title and body); `.github/workflows/ci-recurrence-bench.yml` `paths:` | juniper-recurrence |
| F-T7 | Minor | `scripts/check_version_drift.py` passes while `AGENTS.md` Status prose still says 0.3.0/0.2.0/0.2.0 (table says 0.5.0/0.3.0/0.3.0); the script checks the table, not the paragraph. | `AGENTS.md:43-47` + Status paragraph; drift output "OK (no drift)" | juniper-recurrence |
| F-T8 | Minor | No recurrence equivalent of the ecosystem guards (`juniper-ml/tests/test_equities_symbol_cap_operator.py`; `juniper-data/.../test_val_emission_guards.py`): no 14-symbol request guard, no generator-version floor, no real-validator fixture. | both files | juniper-recurrence |
| F-T9 | Major (env) | `JuniperCanopy1` cannot import torch (`_PyObject_NextNotImplemented`), so canopy's recurrence adapter/routing/protocol tests cannot run on the host. | canopy test run output | host env |

### 3.8 Documentation (DOC)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-X1 | Doc (misleading) | Recurrence README and client README show `client.train(name="equities", …)` — flat 2-D `equities`, which the service refuses. | `juniper-recurrence/README.md:173,177`; `juniper-recurrence-client/README.md:43,50` | juniper-recurrence |
| F-X2 | Doc (missing) | No runbook for "recurrence against equities" from canopy or from the CLI; the only accurate parameter guidance is in dated source comments (`model_registry.py:286-336`). | canopy `docs/USER_MANUAL.md:252-262`; `docs/REFERENCE.md`; `ENVIRONMENT_SETUP.md` | juniper-canopy, juniper-recurrence, juniper-ml |
| F-X3 | Doc (missing) | No operator-facing statement of the **required** equities conditioning (explicit `symbols`, finite fill, stationary target, normalization choice). | README examples at `juniper-recurrence/README.md:149-160`; app README `:66-80` | juniper-recurrence |
| F-X4 | Doc (contradiction) | E-H uses `log_return`; canopy seeds `return`; both valid (`params.py:84-86`); nowhere explained. | `suites/p4/e-h-recurrence-real-data.yaml:13`; `model_registry.py:334` | juniper-ml, juniper-canopy |
| F-X5 | Doc (stale) | juniper-data `README.md:9-10` says "train/test/full split"; `docs/REFERENCE.md:1693` says default fill `zero`; `equities_seq/params.py:23-26` describes a two-way boundary; juniper-ml `docs/REFERENCE.md:6470-6510` says 10 features / zero fill / silent `max_symbols` slicing. | as cited | juniper-data, juniper-ml |
| F-X6 | Doc (stale) | App README `:7` says 0.2.0 (is 0.5.0); `AGENTS.md` Status prose stale (F-T7). | `juniper-recurrence/juniper-recurrence/README.md:7`; `_version.py:9` | juniper-recurrence |
| F-X7 | Doc (missing) | Parent `AGENTS.md` dependency graph, port table and agent-file table omit recurrence (8210/8211; `juniper-recurrence/AGENTS.md`). Compose maps host 8211 → container 8210. | parent `AGENTS.md:50-77`; `juniper-deploy/docker-compose.yml:583-601,673-677` | parent `AGENTS.md` |
| F-X8 | Doc (misleading) | Ports 8210 (native), 8211 (Compose host), 8260–8289 (per-run experiment) appear without labelling which is which. | `settings.py:152`; README `:145-155,172`; `experiment_stack.bash:6-9,126-127` | juniper-recurrence, juniper-ml |
| F-X9 | Doc (stale) | Persistence design still recommends a named volume; `settings.py:189-203` documents the bind-mount decision. | `JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md:103,233,257-280` | juniper-ml notes |
| F-X10 | Doc (pending) | `recurrence#184` (refuse `snapshots_dir` in experiment YAML — "YAML beats env" is the behaviour it objects to) and `#183` (anchor the CWD-relative `snapshots_dir` default to the repo): the sentences that will need editing when either lands live at `conf/experiments/irregular-sine-rff.yaml:5`, app `CHANGELOG.md:211`, CLI plan `:257,:898`, `settings.py:60-71,113,130-143`, `tests/test_experiment_yaml_settings.py:3-8,59-69`. | as cited | juniper-recurrence, juniper-ml notes |
| F-X11 | Doc (stale, historical) | The 2026-06 recurrence design/evaluation notes describe `train/test/full`, emitted `X_full`, 10 features, pre-release versions as current. | `JUNIPER_2026-06-14_…MODEL-DETAILED-DESIGN.md`, `…06-17_…STATE-ASSESSMENT-AND-ROADMAP.md`, `…06-18_…EVALUATION-FINDINGS.md`, `…06-24_…FULL-AUDIT.md` | juniper-ml notes |

### 3.9 Scientific validity (SCI)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-SCI1 | Major | Shadowed crossval on the E-H dataset selector **at the service defaults** (`readout=linear`, `ridge=0.0`): train-fold r2 +0.45 → +0.14; eval-fold r2 −83,452 / −815 / −3.7 / −78 / −6,059; aggregate −18,081. **The E-H suite's own RFF configuration has not been measured on this artifact.** Cause unresolved — see below. | `24-c-crossval-shadow.txt`; `21-recurrence-shadow.log:14` (`readout=linear`); `settings.py:183` (`default_ridge = 0.0`) | recurrence bench + juniper-ml suite |
| F-SCI2 | Major | Multi-ticker expanding CV is not chronological (F-P7). The 5-symbol canopy seed, if ever cross-validated, would train on all eras of ticker 0 and validate on the early era of ticker 1. | §3.4 F-P7 | juniper-recurrence |
| F-SCI3 | Major | The happy path emits no honest held-out metric: train is in-sample (F-S5), predict has no metrics, crossval is broken (ENV) or uninterpretable (SCI1). Canopy's `r2 0.008` and the suite's `r2 0.116` are both in-sample. | `22-a-train-aapl.txt`; `23-b-train-canopy-seed.txt`; `scenario-a-runs/…/stats.json` | juniper-recurrence, juniper-ml |
| F-SCI4 | Major | No acceptance band exists for any equities metric (F-D3), so neither −18,081 nor a future regression to it can fail a run. | §3.2 F-D3 | juniper-ml |

**F-SCI1 — the measurement.** Selector: AAPL 2015–2022, `log_return`, lookback 64, `split="full"` with **1,698 windows** (the response's `dataset.n_windows`; the frozen meta has `n_samples=1698`, `n_train=1346` — the 1,346 figure in v1.1.0 was the train partition, not the CV population), 5 expanding folds, embargo 2.
The request carried no model parameters (§2.1), so the service defaults applied: `d=16`, `readout=linear`, `ridge=0.0` (unregularised), data-driven theta.
Per fold: train r2 +0.45 / +0.32 / +0.25 / +0.18 / +0.14; eval r2 −83,452 / −815 / −3.7 / −78 / −6,059; eval RMSE 3.27 / 0.38 / 0.04 / 0.25 / 1.24 against train-fold RMSE 0.0128 / 0.0121 / 0.0124 / 0.0143 / 0.0175.
The E-H suite's own configuration (RFF readout, `ridge=1.0`, 256 features, median gamma from `irregular-sine-rff.yaml`) was not measured because the Scenario-A crossval that would have measured it 422'd on ENV.

**F-SCI1 — what the measurement does and does not say.** The number is a catastrophic out-of-sample error under an **unregularised linear readout** on a 240-column LMU memory (`model.py:148`: `n_features * d` = 15 × 16) fitted on roughly 281–1,413 windows per expanding fold (derived, not reported: model-core `splits.py:111` cuts `fold_size = 1698 // 6 = 283` and the expanding train is `283 × (i + 1) − 2` after the embargo; the response carries no per-fold sizes).
That configuration is sufficient on its own to produce eval r2 in the thousands negative when test-period memory states leave the training-fold support, so the measurement does **not** isolate a cause. Candidate explanations, each testable:

- (a) the unregularised linear readout extrapolating (`ridge=0.0`) — the E-H config's `ridge=1.0` RFF readout may or may not share the failure;
- (b) unnormalised price-level features (`normalize_features` unset) drifting out of support fold by fold — weakened as the sole cause by the fact that the RFF readout already standardises the memory block per fold, train-fold-only (`readouts.py:226-259`), so if E-H's config also blows up, normalisation is not the lever;
- (c) theta: the fold-local data-driven `median(sum(dt))` is never logged (F-S7), so a theta mismatch between folds cannot be ruled out from the artifact;
- (d) a genuine model or `dt`-handling defect.

**W0.8** replays the exact E-H request (RFF, `ridge=1.0`, 256 features, median gamma) on the same frozen dataset id and captures resolved theta, ridge, gamma and per-fold prediction/target ranges before any suite or model change is proposed; **W0.9** widens that to a matrix and issues the go/no-go for P5.
The earlier draft's normalisation hypothesis is withdrawn as a hypothesis-of-record; it survives only as candidate (b).

**F-SCI1 — resolved 2026-10-04 (v1.3.0).** Both measurements are in `JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`, and the paragraph above is superseded by its §2.
The E-H configuration replayed on the frozen artifact gives eval r² −0.080 / −0.050 / −0.102 / −0.086 / −0.258, aggregate **−0.115** (RMSE 0.0186, at the target's own std) — the "r² ≈ 0" the suite comment expects; the service defaults on the same artifact the same day give −20,345 (fold 0 −93,606).
The 24-cell matrix confirms **candidate (a)**: every `ridge = 0.0` cell is catastrophic in both readouts and both normalisations; the linear rung stays catastrophic at `ridge = 1.0` because it does not standardise the memory block (raw feature scales up to 7.9e11), while the RFF rung standardises per fold and is sane at `ridge = 1.0` (−0.115 raw, −0.142 normalised).
Candidate **(c)** is refuted (theta resolves to 91.0 in every fold; configured and fold-resolved cells are identical), **(b)** is refuted as the lever (normalisation makes the unregularised solve worse, −4.3e12, and does not rescue linear ridge 1.0), and **(d)** is not implicated (the one rung that standardises per fold is the one that works).
The mechanism is conditioning: the 242-column linear design has numerical rank 113–161 and condition number 1e22–1e32 per fold, so the min-norm solve extrapolates eval rows along near-null directions with amplification up to 2.6e4; the same ill-posedness is why the audited digits (−83,452) did not reproduce (−93,606) on byte-identical arrays and code.
**Verdict: GO** — W5.1 is a tuning-and-documentation task; the service default `readout=linear`, `ridge=0.0` must not be used for equities (proposed W5.8); the GCV grid's ceiling of 1000 was selected in 15 of 20 GCV folds (proposed W5.9).

### 3.10 Deployment pins (DEPLOY)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-DEP1 | Blocker (deployment) | `juniper-deploy/docker-compose.yml` pins `juniper-data:0.16.0`, `juniper-recurrence:0.5.0`, `juniper-canopy:0.8.1`; the Compose stack serves `equities_seq` as `5.0.0 / classification` and canopy refuses the pair (F-P4) **by construction**. | `docker-compose.yml:164,523` (data), `:598` (recurrence), `:662,806,897` (canopy) | juniper-deploy |
| F-DEP2 | Major | The recurrence Compose service declares **no volume** and no `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`, although `settings.py:189-203` documents a bind-mount decision for snapshots; snapshots written in the container die with it. | `docker-compose.yml:589-647` (no `volumes:`); `settings.py:189-203`; `JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` | juniper-deploy, juniper-recurrence |

Details (DEPLOY):

- **F-DEP1** — The refusal persists after juniper-data 0.17.0 ships until the pin moves. No earlier draft of this plan named juniper-deploy as an owner.
- **F-DEP2** — Nothing in the stack restores a model on boot, and this plan does not propose that it should; the finding is that the documented persistence decision is not deployed.

### 3.11 Concurrency and shared-service identity (CONCURRENCY)

| ID | Severity | Finding | Evidence | Owner |
| --- | --- | --- | --- | --- |
| F-CON1 | Major | Canopy and the CLI stack can point at **the same** recurrence service (native `:8210` or Compose `:8211`) and nothing distinguishes their runs: one process-wide `train_lock`, one in-memory model, one snapshot directory. | `routers/training.py:44-105`; `routers/predict.py:36-38`; `lifecycle` single-model state | juniper-recurrence |
| F-CON2 | Major | No run identity: `/v1/train` returns no operation or model id; `/v1/predict` and `/v1/snapshots/save` accept none; `GET /v1/training/status` reports state without saying which request produced it. (Snapshot *resources* have ids — see Details.) | `schemas.py:162-168` (`TrainResponse`), `:179-196` (`StatusResponse`); `routers/predict.py`; `routers/snapshots.py` | juniper-recurrence, juniper-canopy (consumer) |
| F-CON3 | Minor | The experiment launcher avoids the collision only by convention (per-run ports 8260–8289), and canopy's default `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL` is not one of them; an operator running canopy and a CLI suite side by side against the native service recreates F-CON1 without any warning from either side. | `experiment_stack.bash:6-9,126-127`; canopy `settings.py:547-565` | juniper-ml, juniper-canopy (docs) |

Details (CONCURRENCY):

- **F-CON1** — A canopy Start during a CLI cell gets a 409 with no indication of who holds the lock (F-S6); the CLI's `predict` after a canopy fit silently scores canopy's model.
- **F-CON2** — `TrainResponse` carries metrics and dataset only; `StatusResponse` carries no id. A caller cannot prove that the predictions or the snapshot it received came from the model it trained.
  Snapshot resources do have their own ids (`routers/snapshots.py`); the finding is that nothing ties a snapshot, or a prediction, to the training *request* that produced the in-memory model.

---

## Goals

- **G1 — Truthful tooling**: a failed or degraded equities run is reported as failed by the launcher, the suite, canopy's UI and the service's logs and metrics, with the service's reason intact.
- **G2 — Runnable from both entry points**: an operator can produce a trainable `equities_seq` fit from canopy without staging and from the CLI without hand-minting an artifact, against the env the launcher actually selects.
- **G3 — Diagnosable**: one request id joins canopy → recurrence → juniper-data logs; fit exceptions, artifact inventory, resolved hyperparameters and numerical diagnostics are logged; failures are counted.
- **G4 — Guarded**: the compositional (app + model + validator + real artifact shape) failure that produced F-E1 is caught in CI and at launch, not at crossval time.
- **G5 — Scientifically honest**: an out-of-sample equities metric exists, its CV folds are chronological per entity, and an owner-approved acceptance band is enforced or report-only by explicit choice.
- **G6 — Documented**: two runbooks (canopy, CLI), a required-parameters statement, a port-context table, correct versions, and the parent `AGENTS.md` inventories include recurrence.
- **G7 — Deployed as documented**: the Compose stack serves the contract this plan is written against (juniper-data ≥ 0.17.0, recurrence 0.6.0, canopy 0.9.0), with the snapshot mount the persistence design decided on, and a shared service tells its callers whose model it holds.

### Success Metrics

| Metric | Current | Target | Notes |
| --- | --- | --- | --- |
| E-H suite exit code when crossval 422s | 0 | non-zero; cell `outcome: degraded` | F-D1 |
| Recurrence metric columns in `aggregate.csv` | 0 | `train_r2`, `cv_r2` present | F-D2 |
| Launcher refusal on `pip check` failure in recurrence env | none | refuses with the `pip check` lines | F-E2 |
| `/v1/crossval` on a 3-partition artifact in the as-served env | 422 | 200 | F-E1 (env repair + preflight) |
| CLI `juniper-recurrence train --generator equities_seq --params …` | exit 2 | 200-equivalent fit | F-S1 |
| Canopy UI/log text on a service 422 | generic | includes `detail` (≤ 300 chars) | F-C1 |
| Requests carrying `X-Request-ID` across all three services | 0 / 3 | 3 / 3 | F-L2 |
| Unlogged non-2xx paths in recurrence | 8 | 0 | F-L5, F-L6 |
| App route tests on real-validator 3-partition equities fixture | 0 | ≥ 6 (train 2-D/NaN-X/NaN-y/no-dt/data-422; crossval no-`_full`) | F-T1–T3 |
| CI lane installing local app + local model together | none | 1 (compositional) | F-T4 |
| Equities OOS r2 reported by the suite | none | present, within band or flagged | F-SCI3/4 |
| Train response and canopy panel label in-sample metrics as such | no | `metrics_scope: in_sample` in the response; panel says "in-sample" | F-S5, F-SCI3 |
| E-H crossval measured under the suite's own RFF/ridge config on a frozen dataset id | never | once, with resolved theta/ridge/gamma and per-fold ranges recorded | F-SCI1 (W0.8) |
| Compose pins vs plan target versions | data 0.16.0 / recurrence 0.5.0 / canopy 0.8.1 | ≥ 0.17.0 / 0.6.0 / 0.9.0, with an authenticated canopy → recurrence → data smoke | F-DEP1 |
| Operator runbooks (canopy, CLI) | 0 | 2 | F-X2 |

---

## Implementation Plan

Phases are ordered so each one leaves the path more truthful before it is made more capable. Each work item names the finding(s) it closes, the owner repo, the acceptance test, and a size (S < ½ day, M ≤ 2 days, L > 2 days).

- **Phase 0 — Stop lying, and measure the real thing** (`P0`, ~3 weeks): env repair + preflight, suite outcome/metrics, canopy 422 detail, CLI `--params` (the CLI entry point cannot run at all without it), in-sample labelling, the E-H replay (W0.8) and — closing the phase — the controlled matrix that issues the **go/no-go for P5** (W0.9).
  Closes the four symptoms in §1 as *reported* problems and produces the measurement §3.9, R5 and P5 are reasoned from.
- **Phase 1 — Make both entry points runnable, and deploy the contract** (`P1`, ~4 weeks): canopy param filtering + effective-request preview, `y_reg` required, validator gaps, timeout/409/identity semantics, 401/429/`restored`, juniper-data 0.17.0 release + floors + Compose pins + authenticated smoke, and the P1 release train (W1.13).
- **Phase 2 — Observability** (`P2`, ~2 weeks): request ids, exception logging, artifact inventory, model diagnostics, failure metrics, snapshot logs, driver evidence capture, canopy `funcName`.
- **Phase 3 — Tests and CI** (`P3`, ~1–2 weeks, can overlap P2): compositional lane, realistic fixtures, error-path tests, deep readiness, crossval route test on a 3-partition fixture, bench equities lane on a cached fixture, drift-script prose, recurrence guards, #178.
- **Phase 4 — Documentation** (`P4`, ~1 week, overlaps P3): runbooks, README corrections, required params, port table, parent `AGENTS.md`, versions, #183/#184 sentence list, banners on legacy notes.
- **Phase 5 — Scientific validity** (`P5`, ~3 weeks, gated on W0.9's go/no-go): CV cause investigation note, entity-grouped chronological folds, OOS metric on the happy path, acceptance-band facility and ruling.

Gating: P2–P4 are hardening and documentation and proceed regardless of W0.9's verdict; **P5's content depends on it** (a "no-go" — the E-H configuration also blows up — turns W5.1 into a model/CV defect investigation before any band or fold work; a "go" — E-H's config is sane — makes W5.1 a tuning and documentation task).
Within P0 the code items (W0.1–W0.7) merge independently of the measurement items (W0.8, W0.9); M0 closes only when W0.9's verdict is issued.

Placement of the go/no-go matrix (W0.9): v1.1.0 put it in P1 as W1.0 with W0.8 (one replay) as the P0 item. Round-1 lane B2 dissented that the matrix is the real gate for P5 and R5 and that a single-configuration replay cannot carry a go/no-go.
Round-2 lane B1, briefed on the change and not on B2's report, reached the same finding independently and added that the plan's own text already made P1 depend on it (W1.1(a) sets `normalize_features` "per its finding"; M1 required its verdict) and that its stated prerequisites (W0.1 env repair, W0.6 CLI `--params`) are themselves P0 items, so "run it once the env and CLI can" is an argument for the *end of P0*, not for P1.
The reconciler accepted both: W0.9 closes P0, P0 grows from ~2 to ~3 weeks, and M0 moves accordingly. No dissent remains on placement.

Table convention: where a work item's Change or Acceptance text exceeds one table line it is summarised in the row and spelled out in the **Details** list beneath the table, under the same WI id. The Details text is normative; the row is the index.

### Phase 0 — Stop lying, and measure the real thing (P0)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W0.1 | F-E1, F-E4 | operator (Paul); recipe in `juniper-recurrence/AGENTS.md` | Repair `JuniperCascor1` (editable model 0.3.x + service-core 0.7.x; remove stale service-core pair; restart pre-repair listeners; record recipe and `python -s` probe). | Scoped `pip check` clean; `python -s` probe ok; bench 37/37 as-served; `/v1/crossval` 200 on `equities_seq-6.0.0-…` without `PYTHONPATH`; recipe recorded. | S |
| W0.2 | F-E2, F-E5 | juniper-ml | `recurrence_up` preflight before `serve`: scoped `pip check`, floors from `pyproject.toml`, `derive_full_split` import; refuse verbatim; `--skip-env-preflight` logs loudly. | Synthetic stale env refuses with the text; unrelated `pip check` noise does **not** refuse; as-served host env refuses until W0.1. | M |
| W0.3 | F-D1 | juniper-ml | Per-phase result block in the manifest; `outcome: degraded` derived from phase results (not `acceptance.ok`); `degraded` in `TERMINAL_OUTCOMES`; non-success in summary/`REPORT.md`/exit; consumers audited. | Mocked 422 on `/v1/crossval` → `degraded`, exit ≠ 0, `1 succeeded, 1 degraded`; `acceptance.ok false` alone is **not** degraded; E-H re-run on stale env exits non-zero. R6 fixes exit semantics. | M |
| W0.4 | F-D2 | juniper-ml | `_headline_metrics` reads `final_metrics.r2` → `train_r2`, `crossval.eval_aggregate.r2` → `cv_r2`, `eval_std.r2` → `cv_r2_std`, plus `n_windows`; null `crossval` → no `cv_*` key. | Four fixtures (audited `crossval: null`; successful; `cv_r2 = 0.0`; `cv_r2 < 0`) surfaced verbatim; `aggregate.csv` gains the columns. | S |
| W0.5 | F-C1 | juniper-canopy | Adapter parses `{"detail": …}` (string or list) into the exception message (≤ 300 chars); `outbound_error_text` passes it through; backend WARNING carries status/path/detail; UI shows the bound or a tooltip. | Adapter test: 422 with `{"detail":"invalid dataset: X_train has non-finite values (NaN/Inf)"}` → `completion_reason` contains it; UI test asserts render. | M |
| W0.6 | F-S1, F-P1 | juniper-recurrence | **(moved from P1)** CLI `train` gains `--params <json>` / `--params-file <path>` (mutually exclusive) threaded into `load_sequence_data(params=…)`; `--help` shows an `equities_seq` example. | `test_cli_train.py` ×3 (params reach `create_dataset`; both flags → exit 2; malformed JSON → exit 2); bounded offline E2E completes and prints `final_metrics`. | S |
| W0.7 | F-S5, F-SCI3 (label half) | juniper-recurrence + juniper-canopy | `TrainResponse.metrics_scope: "in_sample"` (constant for now; W5.3 adds scopes); canopy's regression panel titles the block "in-sample (train split)". No number changes. | Route test asserts the field; canopy panel test asserts the title. | S |
| W0.8 | F-SCI1 (measurement) | recurrence bench + juniper-ml suite | **Replay the real E-H crossval** on the frozen id with the request body E-H actually sends (RFF, `ridge=1.0`, 256 features, median gamma); capture theta/ridge/gamma and per-fold ranges; write as §1 of the W5.1 note. | Note exists with the table and one of three verdicts: E-H config also blows up (no-go), E-H config is sane (go), or inconclusive with the reason. | S |
| W0.9 | F-SCI1 (go/no-go) | recurrence bench + juniper-ml suite | **(was W1.0; moved to close P0)** Widen W0.8 to a controlled matrix on the same artifact ({readout} × {ridge} × {normalisation} × {theta}), 5 folds, one ticker; issue the **go/no-go** for P5 as §2 of the W5.1 note. Needs W0.1 and W0.6; the other P0 items do not wait for it. | Note section with the matrix and the verdict; reviewed under the consensus procedure before R5 is ruled. **M0 requires this item.** | M |

Details (P0):

- **W0.1** — Install `juniper-recurrence-model` 0.3.x and `juniper-service-core` 0.7.x editable from the checkouts (matching how `juniper-recurrence` is installed); remove the stale `juniper-service-core` 0.4.0/0.5.0 pair so pip metadata and the importable module agree.
  Record in `juniper-recurrence/AGENTS.md`: the interpreter path, the three checkout SHAs installed, and the `python -s -c "import juniper_recurrence_model.data as d; d.derive_full_split"` probe (`-s` so a `~/.local` package cannot mask an env gap — parent `AGENTS.md` Conda note).
  **Restart any recurrence listener started before the repair** (the parent note's deleted-interpreter trap). Raise the recurrence app's `juniper-data-client` floor to `>=0.5.0` (the first decision-11 release) if it is below.
  Acceptance: `pip check` reports no recurrence-closure lines (CUDA lines are out of scope and listed as such).
- **W0.2** — Run `<env>/bin/python -s -m pip check` **filtered to the recurrence dependency closure** (`juniper-recurrence*`, `juniper-service-core`, `juniper-observability`, `juniper-data-client`, `juniper-model-core`), assert the model and service-core floors from the app's `pyproject.toml`, and `python -s -c "from juniper_recurrence_model.data import derive_full_split"`. Refuse with the verbatim lines. `--skip-env-preflight` logs a loud WARNING into the run's `launch.log`.
  Acceptance: a new test in `juniper-ml/tests/` builds a **synthetic stale env** (a venv with a stub `juniper_recurrence_model` lacking `derive_full_split` and mismatched metadata) and asserts the refusal text and exit code; a second case asserts unrelated `pip check` lines (a fake `cuda-python` conflict) do **not** refuse.
- **W0.3** — `run_experiment.py` records `phases: {train: ok, crossval: failed(422 …), predict: ok, save_model: skipped}` in the manifest and derives `outcome: degraded` when train succeeded but an **enabled phase failed** — from those records, **not** from `acceptance.ok`, so that a future acceptance-band failure (W5.4) stays `failed`/`flagged` rather than `degraded`. Keep `EXIT_ACCEPTANCE`.
  `run_suite.py`: add `degraded` to `TERMINAL_OUTCOMES` (`:81`); `degraded` is not-succeeded in the summary, `REPORT.md` and the exit code; print `degraded (crossval failed: …)`. Audit every consumer of `outcome` (`read_run_metrics.py:70`, `list_runs.py`, `stats_summary.py`, `compare_baseline.py`) in the same PR.
  Acceptance: unit tests drive **real mocked phase failures** (fake recurrence server returning 422 on `/v1/crossval`), not hand-edited manifests.
- **W0.4** — Acceptance fixtures: the audited `stats.json` (`crossval: null`) → `{"train_r2": 0.1163, "n_windows": …}` and no `cv_r2`; a synthetic successful crossval → `cv_r2` present; `cv_r2 = 0.0`; `cv_r2 < 0` (the −18,081 case).
- **W0.6** — `--help` example uses `equities_seq` with `symbols`, `fundamentals_fill: drop`, `regression_target: log_return`. The **bounded integration test** uses an offline real-client fixture: explicit params → a finite three-partition artifact → the CLI fit completes.
- **W0.8** — Request body from the `irregular-sine-rff.yaml` base: RFF readout, `ridge=1.0`, 256 features, median gamma, `d` and `theta` as configured; dataset id `equities_seq-6.0.0-15505731cba5b86d`; run against the shadowed/repaired env.
  Capture: resolved theta per fold (requires a temporary debug print if F-S7 is not yet fixed), selected ridge, gamma, per-fold prediction and target min/max/std, train and eval r2/RMSE. No code change beyond a throwaway script under `juniper-ml/util/ad-hoc/`.
- **W0.9** — Matrix: {readout `linear`/`rff`} × {`ridge` 0.0/1.0/`gcv`} × {`normalize_features` off/on} × {theta configured vs fold-resolved}. Record `dt` diagnostics (fold `sum(dt)` medians), memory-state z-ranges per fold and prediction ranges.
  Driven unattended through the W0.6 CLI against the W0.1-repaired env (or shadowed by hand if W0.6 slips; the verdict does not depend on how the runs were launched). Written as §2 of the W5.1 note; W0.8 is its §1.
  The verdict feeds W1.1(a)'s `normalize_features` value, W5.1's content and R5. It is the only P0 item M0 waits for beyond the code merges.

### Phase 1 — Make both entry points runnable, and deploy the contract (P1)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W1.1 | F-P1 | juniper-data | **(a) now**: document the recurrence-ready **explicit bundle** in the `equities_seq` docstring, REFERENCE and runbooks (needs no ruling). **(b) optional, ruling R1**: a `preset: "lmu"` param expanding to the bundle and hashed into `dataset_id`. | (a) docs reviewed against `defaults.py`/`params.py`; (b) unit test: preset expands to the bundle and changes the id. | S / S–M |
| W1.2 | F-C2, F-C3 | juniper-canopy | `recurrence_backend` forwards only params in the generator's schema (`dataset_schema.py`); no `_STAGED_PARAM_KEYS` translation where `n_samples`/`noise` do not exist. Precedence policy per ruling R7 (recommended default in Details). | `test_recurrence_staging.py`: three separate tests (untouched form; staged generic field; explicitly edited equities field) — see Details. | M |
| W1.3 | F-S2, F-S8 | juniper-recurrence-model | `sequence_data_from_arrays(..., target=…)` with `reg` / `class` / `auto`; default `reg` for service and CLI; `auto` keeps today's behaviour but WARNs on one-hot fallback. Ruling **R8** on the breaking default. | Model test: `y_*`-only artifact with `target="reg"` → `ValueError("regression target 'y_reg_train' missing")`; `auto` test asserts the WARNING. | S |
| W1.4 | F-P3, F-S3 | juniper-data-client + model | Validator: finite `dt`; `target_dt_*` 1-D finite ≥ 0; `seq_lengths_*` int in `[1, L]`; **enforce `float32`** on `X_*`/`y_*`/`y_reg_*` per the Data Contract (ruling **R2**). Model reader mirrors the checks. | Contract tests for each new rejection; recurrence app tests exercise the real validator (W3.2). | M |
| W1.5 | F-S6, F-S9, F-C4, F-D5, F-CON1, F-CON2 | recurrence + canopy + juniper-ml | **Service**: `operation_id` on train/409/status; terminal `failed`; `expect_operation_id` on predict/save; data-client timeout setting. **Canopy**: poll status after `ReadTimeout`; never `succeeded` blindly. **Driver**: separate dataset-create timeout. Runbooks: one caller per service. | Route tests (409, status, stale id → 409); adapter tests for **four races**; driver test with a 40 s fake data server — see Details. | L |
| W1.6 | F-C5, F-C6, F-C7 | juniper-canopy | 401 remedy names `JUNIPER_CANOPY_RECURRENCE_API_KEY`/`_FILE`; `RecurrenceStatus` gains `restored` + `restored_from` mapped to model-present; 429 mapped to `RecurrenceServiceRateLimited` with `Retry-After` in the message. | Three adapter tests. | S |
| W1.7 | F-C8 | juniper-canopy | Replace the hard-coded `0.1.0` with the service's reported version from `/v1/health` (or `GET /`), add `juniper-recurrence-client>=0.3.0,<0.5.0` (or a documented contract floor) to `pyproject.toml` `[service]` extra. | Registry test reads version from a fake health payload. | S |
| W1.8 | F-P2 | juniper-data | Owner ruling **R3**: under `fundamentals_fill="drop"`, either drop pre-purchase rows too, or fill `cost_basis` with a documented finite sentinel, or refuse the request when `purchase_date` is after `start_date`. Implement the ruling; bump `generator_version` only if emitted values change for an existing id. | Unit test for the chosen behaviour; `test_val_emission_guards.py` allow-list updated if bumped. | S–M |
| W1.9 | F-D4 | juniper-ml | Launcher records the resolved recurrence CLI path **and effective launch settings** in `${RUN_DIR}/ports.json` (or `env/launch.env`); driver prefers the recorded path over `shutil.which` and asserts **rerun parity** for `save_model`. | Driver test: `save_model_rerun.cmd[0]` equals the launcher-recorded path; parity test fails when the recorded interpreter differs from the served one. | S |
| W1.10 | F-D9, F-L11 | juniper-ml | `recurrence_up` exports `JUNIPER_RECURRENCE_SNAPSHOTS_DIR=${RUN_DIR}/snapshots` and passes `JUNIPER_RECURRENCE_LOG_LEVEL`/`LOG_FORMAT` when set in the environment. | Launcher test (bash harness in `juniper-ml/tests/`) asserts the exported env. | S |
| W1.11 | F-P4, F-DEP1 | juniper-data + juniper-ml + juniper-deploy | **(moved from P5)** Release juniper-data 0.17.0 (`equities_seq` 6.0.0/regression, #437); bump the juniper-ml `[all]` floor; move the Compose pins (one PR per pin); add a canopy → recurrence → juniper-data smoke to `juniper-deploy-test`. | PyPI 0.17.0 probe shows `regression`; wheel probe re-run; `docker compose config` shows the new pins; smoke passes on published images. **M1 requires it**; slip rule in Details. | M (release + ops) |
| W1.12 | F-DEP2 | juniper-deploy + juniper-recurrence | Add the snapshot bind mount the persistence design decided on (`JUNIPER_RECURRENCE_SNAPSHOTS_DIR` + `volumes:` entry) to the recurrence Compose service; document that no restore-on-boot exists and that `restored` is reached only via `POST /v1/snapshots/restore`. | `docker compose config` shows the mount; a save → container restart → list → restore round trip passes in the deploy smoke. | S |
| W1.13 | — (release train) | five repos (Details) | **P1 release train**: publish recurrence 0.6.0, model 0.4.0, data-client 0.6.0, canopy 0.9.0 after their P1 items merge; move the remaining Compose pins; re-run the W1.11 smoke. | PyPI/GHCR probes for all four; `docker compose config` shows the pins; smoke green on published images. | M (release + ops) |

Details (P1):

- **W1.1** — The dataset half of the bundle: `fundamentals_fill: drop`, **`normalize_features: false`**, `regression_target: log_return`, explicit `symbols`.
  The `false` is W0.9's finding (2026-10-04): producer normalisation does not help the sane configuration (−0.115 raw vs −0.142 normalised) and makes the unsafe one worse (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §2.3(b)).
  The model half, which W0.9 showed decides the outcome: `readout: rff`, `ridge: 1.0` (or `gcv` once the grid ceiling is lifted, proposed W5.9), `rff_features: 256`, `rff_gamma: median`.
  (a) is the plan's recommendation; (b) needs ruling R1. W0.9 has reported, so (a) may merge.
- **W1.2** — Recommended precedence (R7): generic-form defaults never override the registry seed; an explicitly edited recurrence-aware form field wins over the seed; a read-only JSON "effective request" preview is shown before Start and logged at INFO.
  Tests: (1) untouched generic form → body equals the seed exactly; (2) staged `n_samples` + untouched equities fields → body has schema keys only and still equals the seed; (3) explicitly edited `regression_target: next_close` → body carries it and the preview matches.
- **W1.3** — The default change is breaking for a `y_*`-only artifact. R8 decides whether it ships in recurrence 0.6.0 (pre-1.0 minor, CHANGELOG "Breaking") or waits behind a deprecation warning.
- **W1.4** — `np.isfinite(dt)` required; `target_dt_*` if present must be 1-D `(W,)`, finite, ≥ 0; `seq_lengths_*` if present `(W,)` int in `[1, L]`. The plan recommends dtype enforcement; the owner may choose documented tolerance instead (R2).
- **W1.5** — Service: `POST /v1/train` returns an `operation_id`, also in the 409 `detail` and in `GET /v1/training/status` with `busy_since`, `dataset_id`, `requested_by` (= `X-Request-ID` if sent); status gains terminal states including `failed`; `/v1/predict` and `/v1/snapshots/save` accept an optional `expect_operation_id` and 409 on mismatch; new setting `juniper_data_timeout_seconds` (default ≥ 120) is passed to `JuniperDataClient(timeout=…)`.
  Canopy: on `ReadTimeout`, poll status with the operation id; still fitting → `running (upstream)`; `failed` → `failed` with the detail; unreachable → `unknown (upstream unreachable)`, never `succeeded`.
  Driver: separate `dataset_create_timeout_seconds` from `max_wall_seconds`; document that the fit is non-cancelling; pass `expect_operation_id` on predict. Both runbooks document that a service is **exclusively owned by one caller at a time** and how the launcher's per-run ports avoid the collision (F-CON3).
  Acceptance: route tests — 409 carries `operation_id` + `busy_since`; status terminal `failed`; predict with a stale `expect_operation_id` → 409. Adapter tests for the four races: timeout-then-success, timeout-then-failure, timeout-then-unreachable, 409-from-another-caller. Driver test: both timeout knobs plumbed; a fake data server that sleeps 40 s no longer fails inside recurrence.
- **W1.9** — Effective settings recorded: env name, interpreter, snapshots dir, log level. Rerun parity: the `save_model` rerun must resolve the same interpreter and model version as the served process.
- **W1.11** — Floors: juniper-ml `[all]` → `juniper-data>=0.17.0`; canopy registry comment and gate note updated. Compose pins move to `juniper-data:0.17.0` in this item; the recurrence 0.6.0 / canopy 0.9.0 pins belong to W1.13, each PR citing this plan. Smoke: select `equities_seq`, start, expect 200 and a regression metrics block. The wheel probe follows `2026-09-10_verify_published_wheels.py`.
  **Slip rule**: the code half (floor bump PR drafted, pin PR drafted, smoke green against a `main` checkout of juniper-data) is M1-blocking; the publication half (0.17.0 on PyPI and GHCR) is not under the plan's control. If publication has not happened by the M1 date, M1 is declared **"M1 — code complete, publication pending"** with the two PRs open, and the deploy smoke on *published* images moves to W1.13's acceptance. M1 is not re-dated for the slip; W1.13's date is.
- **W1.13** — Publication order follows the dependency order: data-client 0.6.0 → model 0.4.0 → recurrence 0.6.0 → canopy 0.9.0 (canopy's `[service]` extra floors the recurrence client, W1.7). Each release uses its repo's existing publish workflow; the parent `AGENTS.md` "RELEASED to PyPI" paragraph is updated in the same PR as the last pin. If a release slips past M1, the milestone notes which versions are pending; nothing in P2–P4 waits for publication.

### Phase 2 — Observability (P2)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W2.1 | F-L1 | juniper-recurrence | Wrap `lifecycle.run` and `cross_validate` in `try/except Exception`; `logger.error(..., exc_info=True)` with dataset id, split, shape, `d`, resolved theta, readout, ridge, folds, elapsed; return 500 with an `incident_id` echoed in the log. | Route test with a model that raises → one ERROR line with the fields, 500 body has `incident_id`. | S |
| W2.2 | F-L2 | juniper-recurrence + juniper-canopy | Add `RequestIdMiddleware` to `build_app()`; adapter sends `X-Request-ID` (inbound canopy id or a fresh uuid) and logs the echoed id; verify the data-client forwards it. | Three-service integration test (fake data server) asserts the same id in all three logs. | M |
| W2.3 | F-L3 | juniper-recurrence | `data.py`: INFO before `create_dataset` (generator, normalized params with secrets redacted) and after resolution (dataset id, cache hit if known); INFO artifact inventory after download (keys, shapes, dtypes, finite fraction per numeric key); WARNING validation summary on failure. Never log array values. | Caplog tests; equities-shaped artifact produces the inventory line. | M |
| W2.4 | F-L4, F-S7 | juniper-recurrence-model | Module logger: INFO fit summary (resolved theta, readout, selected ridge/GCV λ, design shape, rank, condition number, duration); WARNING on rank deficiency, cond > threshold, non-finite intermediates; `logging.captureWarnings(True)` in `init_logging`. Route start log prints the resolved theta. | Model caplog tests; route test asserts `theta=<float>`. | M |
| W2.5 | F-L5, F-L6 | juniper-recurrence + juniper-service-core | Snapshot save/restore INFO start/complete, ERROR with traceback on failure, WARNING for unreadable entries and lock refusals; predict-before-train 409 WARNING; security-middleware 401/429 WARNING with path + sanitized client identity (no key material). | Route caplog tests per path; the §3.6 "unlogged non-2xx" count reaches 0. | M |
| W2.6 | F-L7, F-L8 | juniper-recurrence | Call `init_logging(settings)` before `uvicorn.run` and at the top of CLI `train`; pass uvicorn a `log_config` that routes access logs through the service formatter; add DEBUG lines at id resolution, inventory, fold boundaries, readout construction, snapshot paths. | Smoke test captures a boot line in the service format; CLI `train` emits the inventory line. | S |
| W2.7 | F-L9 | juniper-recurrence | Add `juniper_recurrence_{train,predict,crossval}_failures_total{reason}` with bounded reasons (`dataset`, `validation`, `lock`, `model`, `torch`), in-progress gauge, duration histogram observed on failure too. | Metrics test scrapes after a forced failure. | S |
| W2.8 | F-D7 | juniper-ml | On any non-2xx, write the full sanitized body to `artifacts/results/http_error_<phase>.json`; write bounded tails (200 lines) of `juniper-recurrence.log` and `juniper-data.log` into `artifacts/results/log_tail_<service>.txt`; set `completion_reason` from the first acceptance reason. | Driver test with a fake 422 → both files exist and manifest paths point at them. | S |
| W2.9 | F-C11 | juniper-canopy | `makeRecord(..., func=caller.f_code.co_name)` (or `logger.log(..., stacklevel=…)`); delete or implement the midnight-rotation block. | Logger test asserts `funcName` populated. | S |
| W2.10 | F-L10 | juniper-data | WARNING on cap refusal (requested, cap) and permitted truncation; INFO data-quality summary (symbols requested/kept/dropped, rows before/after, per-column fill counts). | Generator caplog tests with mocked sources. | S |

### Phase 3 — Tests and CI (P3)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W3.0a | F-T3 | juniper-recurrence | Rewrite `test_crossval_routes.py` fixture to a three-partition equities-shaped artifact (no `_full`, `ticker_code_*` present, two tickers), run the **real** `validate_npz_contract`, assert 200 and that `dataset.split == "full"` with `n_windows == train+val+test`. Uses the W3.2 fixture; P3 landing order **W3.1 → W3.2 → W3.0a**. | Test fails on model 0.1.5, passes on 0.3.0 (red/green verified by shadow toggle). | S |
| W3.0b | F-E3 | juniper-recurrence | `/v1/health/ready` additionally asserts `derive_full_split` is importable and `juniper_recurrence_model.__version__` satisfies the app's pin; report both in the ready payload. (W0.2's launcher preflight covers the host path in P0; this covers the Compose path, where there is no launcher.) | Route test with a monkeypatched stale module returns 503 with the reason. | S |
| W3.1 | F-T4 | juniper-recurrence | **Land first in P3** — the lane that the rest of P3's tests run under. New workflow lane `ci-recurrence-compositional.yml`: `pip install -e ./juniper-recurrence-model -e ./juniper-recurrence[test] -e ./juniper-recurrence-client`, run app + client + bench unit tests; triggers on any package path. | Lane goes red when the model checkout removes `derive_full_split` (verified once by a scratch branch, then documented). | M |
| W3.2 | F-T1, F-T2, F-T8 | juniper-recurrence | Shared fixture `equities_seq_artifact(tickers=2, splits=3, lookback=8, features=15)` producing the §3.4 key inventory; stop monkeypatching `validate_npz_contract`; add `/v1/train` tests for 2-D X, NaN X, NaN y, missing `dt`/`t`, data-client 422 (cap text); add a 14-symbol request guard test mirroring `test_equities_symbol_cap_operator.py`. | ≥ 6 new route tests; the real validator runs in app tests. | M |
| W3.3 | F-T5 | juniper-recurrence | Bench CI: add a lane with `[bench-equities]` running against a **committed cached fixture** (small OHLCV/shares cache for one ticker under `bench/fixtures/`), network disabled. | Bench equities row executes (not skipped) in CI. | M |
| W3.4 | F-T7, F-X6 | juniper-recurrence | `check_version_drift.py` also scans `AGENTS.md` prose for `app X.Y.Z / model X.Y.Z / client X.Y.Z` patterns and the app README's version line. | Script fails on the current stale paragraph; passes after W4.4. | S |
| W3.5 | F-T6 | juniper-recurrence | Close #178 as filed: the bench lane is **path-scoped** and so blind to a dependency break that arrives without touching `bench/` — widen its `paths:` triggers to the model and app package paths (or make it a `workflow_call` from the compositional lane, W3.1) so that a model change re-runs the bench. Any dispatch-token work belongs to a separate issue. | A scratch model-only change triggers the bench lane; link recorded in #178. | S (ops) |
| W3.6 | F-T9 | host env | Repair `JuniperCanopy1` torch/libtorch ABI (reinstall torch for Python 3.13 in that env); record in canopy `AGENTS.md`. | Canopy recurrence tests collect and pass. | S (ops) |
| W3.7 | F-C1–C4 (regression coverage) | juniper-canopy | **Regression coverage** for the tests W0.5, W1.2, W1.5 and W1.6 add: exact default `equities_seq` body; schema filtering; `next_close` override only via explicit form; 422 detail rendered; the four timeout races; 429; `restored` — one `tests/test_recurrence_equities_path.py` module that reads as the canopy-side contract. | The module exists and each listed behaviour has a named test; no new behaviour. | M |

### Phase 4 — Documentation (P4)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W4.1 | F-X2, F-X3, F-X4, F-CON3 | juniper-recurrence + juniper-canopy | New `juniper-recurrence/docs/RUNBOOK_EQUITIES_CLI.md` and canopy `docs/RUNBOOK_EQUITIES_RECURRENCE.md`; both state the **required** conditioning and exclusive single-caller ownership of a service; **defer** r² interpretation until R5. | Linted; linked from README/USER_MANUAL/REFERENCE/ENVIRONMENT_SETUP; no r² interpretation text before R5. | M |
| W4.2 | F-X1 | juniper-recurrence | README and client README examples use `equities_seq` with explicit params; add one sentence that flat `equities` is refused and why. | Doc test (`tests/test_readme_examples.py` if present) or manual. | S |
| W4.3 | F-X7, F-X8, F-E5 | parent `AGENTS.md`, juniper-recurrence, juniper-ml | Add recurrence to the dependency graph, port table (8210 container / 8211 Compose host / 8260–8289 experiment), agent-file table; one canonical port-context table in `juniper-recurrence/README.md`; "no dedicated env; host launchers default to `JuniperCascor1` (`JUNIPER_EXP_RECURRENCE_CONDA`)". | Reviewed. | S |
| W4.4 | F-X6, F-T7 | juniper-recurrence | README `0.5.0`; `AGENTS.md` Status prose to 0.5.0/0.3.0/0.3.0 (or whatever is current at merge). | W3.4 passes. | S |
| W4.5 | F-X5 | juniper-data, juniper-ml | juniper-data README/REFERENCE: three-way split, default fill `nan`, 15 features, cap refusal semantics; `equities_seq/params.py:23-26` docstring; juniper-ml `docs/REFERENCE.md:6470-6510`. | Reviewed against `defaults.py`/`params.py`. | S |
| W4.6 | F-X9, F-X10, F-X11 | juniper-ml notes, juniper-recurrence | "Superseded" banner on the persistence design §11.1 (bind mount); when #183/#184 land, edit the six listed locations in the same PR; add a current-contract banner to the four 2026-06 recurrence notes. | Checklist in the PR body names each file. | S |

Details (P4):

- **W4.1** — CLI runbook: launcher command, preflight, `--params` example, in-sample vs CV metrics (the **label**, per W0.7), `log_return`/`return` rationale, port context, the explicit param bundle from W1.1(a).
  Canopy runbook: configure the service URL, select, (don't) stage, start, read the panel.
  Ownership sentence: a recurrence service is **exclusively owned by one caller at a time** (one canopy *or* one driver per listener; the launcher's per-run ports exist for this).
  Until R5 is ruled the runbooks say only that the number is in-sample and unbanded; any sentence interpreting what a "good" r² is waits for the ruling.

### Phase 5 — Scientific validity (P5)

| WI | Closes | Owner | Change | Acceptance | Size |
| --- | --- | --- | --- | --- | --- |
| W5.1 | F-SCI1 (cause) | recurrence bench + juniper-ml | **Cause investigation note** `JUNIPER_<date>_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` (§1 = W0.8, §2 = W0.9); content gated by W0.9's verdict (no-go → defect investigation over candidates a–d; go → record the sane number). Ends in an R5 recommendation. | Note exists with the matrix, the per-candidate verdicts, and an R5 recommendation; reviewed under the consensus procedure before R5 is ruled. | L |
| W5.2 | F-P7, F-SCI2 | juniper-recurrence + juniper-model-core (integration) | **Independent of W5.1.** Pass model-core's existing `order=`/`groups=` from `routers/crossval.py`; expose `ticker_code_*`, `window_end_date_*`, `target_dt_*` via `SequenceData`; cut folds on global `window_end_date`; embargo in windows ≥ `lookback` (separate `embargo_days` gap); exclude `test`. | Four tests (chronology; lookback non-overlap; label availability; `test` excluded) — see Details. Bench gains a multi-ticker row. | L |
| W5.3 | F-S5, F-SCI3 (OOS half) | juniper-recurrence + juniper-canopy + juniper-ml | `/v1/predict` returns `r2`/`rmse`/`mae` when `y_reg_{split}` exists, with `metrics_scope: "out_of_sample"`, `split` and the scoring `operation_id`; propagate scope/split through canopy; driver records `test_r2` **only when `split == "test"`**. | Route test; adapter/backend/UI tests for scope propagation; driver test: `split=val` metrics land under `val_r2`, not `test_r2`; `aggregate.csv` gains `test_r2`. | M |
| W5.4 | F-D3, F-SCI4 | juniper-ml | **No YAML `acceptance:` facility exists today** (`run_suite.py:742` is reporting-only). Build it: per-row schema `acceptance: {metric, min, max, mode: gate / report}`, parser, comparator over W0.4 keys, outcome semantics per R6, report columns; then encode the **R5** band for E-H. | Suite tests: `cv_r2 = −18081` → `failed` under `gate`, `flagged` under `report`; missing metric follows the mode (Details); schema error → suite refuses at load. | M–L |
| W5.5 | F-D8 | juniper-ml | `stats_summary.py`: regression target summary (mean/std/min/max/finite fraction) per split. | Unit test on the audited artifact. | S |
| W5.6 | F-D6 | juniper-ml | Implement `--shared-equities-cache <dir>` (plan H-9) as an explicit opt-in; default stays per-run; this item adds its own runbook section (W4.1 lands earlier and cannot document it). | Launcher test; runbook section present in the same PR. | S |
| W5.7 | F-P5, F-P6 | juniper-data | Record dropped-symbol list in `meta.data_quality`; refuse (or flag) when a **requested** symbol is lost; guard `close > 0` and finite before computing return targets. | Generator tests. | S |
| W5.8 | F-SCI1 (cause); **proposed by W0.9, needs owner acceptance** | juniper-recurrence + model | Retire the unsafe service default (`readout=linear`, `ridge=0.0`: what a bare request gets, and what produced −18,081): `default_ridge` → `"gcv"`, and/or per-fold standardisation on the linear rung; at minimum document the hazard. Details below. | Route test: a bare `/v1/crossval` on the E-H artifact aggregates above −1; model test: the linear rung standardises train-fold-only. | S–M |
| W5.9 | F-SCI1 (GCV ceiling); **proposed by W0.9** | juniper-recurrence-model | `_GCV_GRID = logspace(-6, 3, 60)` tops out at 1000, which 15 of 20 GCV folds selected; extend the grid or warn on an edge selection so "GCV-selected" is a selection. | Unit test: an edge selection is reported; the E-H GCV cells re-run off the ceiling. | S |

Details (P5):

- **W5.8** — Preferred: `Settings.default_ridge` `0.0` → `"gcv"` (a pre-1.0 "Changed" entry in recurrence 0.6.0; `conf/experiments/irregular-sine-rff.yaml` pins `default_ridge: 0.0` explicitly, so the reference experiment is unaffected).
  Complementary: give the linear rung the per-fold, train-only standardisation the RFF rung already has (`readouts.py::_standardize_fit`), so a float ridge means the same thing on both rungs.
  Minimum: document on the route and in canopy's registry seed that the linear rung with `ridge=0.0` is a min-norm solve that extrapolates on non-stationary inputs (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §2.4, §3.2).

- **W5.1** — On **no-go** (E-H config also blows up) the note is a model/CV defect investigation. Candidates, each with a falsifying experiment: (a) unregularised linear readout on a 240-dim memory with fold-local rank deficiency; (b) RFF median-gamma fitted on drifting inputs; (c) `dt` in calendar days vs the configured theta; (d) per-fold standardisation on a non-stationary memory.
  On **go** it documents why the service default (linear, `ridge=0.0`) must not be used for equities and records the sane number. Fold-local preprocessing is **required regardless** (see the R4 note).
- **W5.2** — `walk_forward_folds` in `juniper-model-core/juniper_model_core/crossval/splits.py` already accepts `order=` and `groups=`; the recurrence `routers/crossval.py:81-88` does not pass them. The route passes `groups=ticker_code`, `order=window_end_date`, and cuts folds on the global `window_end_date` so every ticker's rows before the cut are train and after are eval.
  **Embargo stays in windows** and must be ≥ `lookback` so no eval window's history overlaps a train window; `embargo_days` is a separately named duration gap. The **selection pool excludes the final `test` partition** (CV runs over `train+val`; `test` is touched once by W5.3). Row-index folds remain for single-entity datasets.
  Tests: (1) two tickers — no eval row precedes a train row in time; (2) per-ticker lookback non-overlap — no eval window's input span intersects any train window's; (3) label availability — a window whose `target_dt` crosses the cut is excluded from train; (4) `test` rows never appear in any fold.
- **W5.3** — Metrics are computed on the named split. The `operation_id` comes from W1.5. W0.7 added the scope label; this item adds the values and propagates `metrics_scope`/`split` through the canopy adapter → backend → UI panel. The suite surfaces `test_r2`.
- **W5.4** — `run_experiment.py`'s `acceptance` block is the per-phase pass/fail the driver computes itself, not a metric band. The facility: (1) suite-YAML schema `acceptance: {metric: cv_r2, min: …, max: …, mode: gate / report}` per row; (2) parser with validation; (3) comparator reading the W0.4 headline keys; (4) outcome semantics — `mode: gate` failing → row `failed` and non-zero exit, `mode: report` failing → row `flagged`, exit unchanged (R6); (5) `REPORT.md`/`aggregate.csv` columns.
  A **missing metric follows the mode**: under `gate` it is `failed (metric absent)` with non-zero exit (a gate that cannot be evaluated has not passed); under `report` it is `flagged (metric absent)` with exit unchanged.
  A missing metric is distinct from `degraded` (W0.3): `degraded` says an enabled *phase* did not run; `metric absent` says the phase ran but the headline key the band names is not in its output.

---

## Milestones

Staffing assumption: one owner (Paul) plus agent sessions, working the phases largely in sequence with P2/P3/P4 overlapping. Dates are targets under that assumption, not commitments; the round-1 consensus judged the v1.0.0 dates (M0 in one week, M4 in seven) infeasible for the item count and they were rebaselined in v1.1.0.
Round 2 judged the v1.1.0 M1 (2026-11-07) non-credible: P1 then held one L, three M and seven S items plus a release, and named four publications no work item owned. v1.2.0 moves W0.9 into P0 (M0 +1 week), adds W1.13 to own the publications, and gives M1 four weeks after M0. **The dates below are the author's estimate and are the one item of this plan the owner is asked to confirm or re-set** (see the consensus note); agents parallelise drafting, not owner review or release authority.

| Milestone | Target Date | Version(s) | Description | Status |
| --- | --- | --- | --- | --- |
| M0 — Truthful path, go/no-go issued | 2026-10-24 | juniper-ml 0.10.x, recurrence 0.5.x, canopy 0.8.x | P0 merged: env repaired (operator recipe recorded), scoped preflight, phase-derived `degraded` outcome, headline metrics on four fixtures, 422 detail, CLI `--params`, `metrics_scope` label, W0.8 replay written up, **W0.9 matrix run and the P5 go/no-go issued** | In Progress — **GO** issued 2026-10-04; W0.1 model half, W0.6, W0.7 (service) merged; the rest in PRs; owner to confirm date |
| M1 — Runnable from both entry points, contract deployed | 2026-11-21 | recurrence 0.6.0, model 0.4.0, data-client 0.6.0, canopy 0.9.0, **juniper-data 0.17.0** | P1 merged: canopy filtering/preview (R7), `y_reg` required (R8), validator gaps (R2), operation-id/timeout/identity semantics, 401/429/`restored`, R1/R3 applied, W1.12; **requires W1.11's code half**; publications (0.17.0, W1.13) per the W1.11 slip rule — if pending, "code complete, publication pending" | Planned (owner to confirm date) |
| M2 — Diagnosable | 2026-12-12 | recurrence 0.6.x, canopy 0.9.x | P2 + P3 merged: request ids, exception/inventory/diagnostic logging, failure metrics, compositional CI, realistic fixtures, deep readiness, crossval route test, #178 | Planned (owner to confirm date) |
| M3 — Documented | 2026-12-12 | all | P4 merged: runbooks (exclusive-ownership statement; no r² interpretation before R5), README fixes, parent `AGENTS.md`, versions | Planned (owner to confirm date) |
| M4 — Scientifically honest | 2027-01-15 | model 0.4.x, juniper-ml 0.11.0 | P5: cause investigation note, entity-grouped chronological folds, predict/OOS metrics through canopy, acceptance-band facility and R5 band (three working weeks after M2/M3, allowing for the year-end break) | Planned (owner to confirm date) |

---

## Feature & Fix Roadmap

### Fixes and Enhancements by Area

#### juniper-ml (launcher, driver, suite)

- **Fix:** scoped env preflight in `recurrence_up` (W0.2); phase-derived degraded outcome and non-zero suite exit (W0.3, R6); headline metrics schema (W0.4); launcher-recorded CLI path + rerun parity (W1.9); snapshots/log env export (W1.10); driver timeout knobs + `expect_operation_id` (W1.5); HTTP body + log tails on failure (W2.8); regression target summary (W5.5); juniper-ml `[all]` floor → `juniper-data>=0.17.0` (W1.11).
- **Feat:** E-H replay (W0.8) and go/no-go matrix (W0.9); acceptance-band facility and E-H band (W5.4, R5); `--shared-equities-cache` (W5.6); `test_r2` surfaced from `split == "test"` only (W5.3).

#### juniper-recurrence (app)

- **Fix:** `metrics_scope: in_sample` on `TrainResponse` (W0.7); `operation_id`/`busy_since`/terminal `failed` status, `expect_operation_id` on predict/save, `juniper_data_timeout_seconds` (W1.5); fit/crossval exception logging (W2.1); request-id middleware (W2.2); dataset/artifact logging (W2.3); snapshot and 4xx logging (W2.5); `init_logging` placement (W2.6); failure metrics (W2.7); deep readiness (W3.0b); crossval route test on 3-partition fixture (W3.0a).
- **Feat:** CLI `--params`/`--params-file` (W0.6); `/v1/predict` OOS metrics with scope, split and model identity (W5.3); grouped chronological CV wired through the route (W5.2).

#### juniper-recurrence-model and juniper-model-core

- **Fix:** explicit target selection, no silent one-hot fallback (W1.3, R8); `target_dt`/`seq_lengths` validation mirror (W1.4); numerical diagnostics logging (W2.4).
- **Feat:** `SequenceData` exposes `ticker_code`/`window_end_date`/`target_dt` so the existing `walk_forward_folds(order=, groups=)` can be used; window-embargo ≥ lookback plus `embargo_days` (W5.2).

#### juniper-recurrence (tests, bench, CI)

- **Fix:** compositional CI lane (W3.1, first); realistic fixture and error-path tests (W3.2); bench equities lane on cached fixture (W3.3); drift script prose scan (W3.4); #178 bench-lane triggers (W3.5).

#### juniper-data and juniper-data-client

- **Fix:** validator finiteness/`target_dt`/float32 (W1.4, R2); `cost_basis` under `drop` ruling (W1.8, R3); cap/fill logging (W2.10); dropped-symbol recording and close guard (W5.7); docs (W4.5).
- **Feat:** documented recurrence-ready param bundle (W1.1a) and optional preset (W1.1b, R1); release 0.17.0 (W1.11).

#### juniper-canopy

- **Fix:** 422 detail end to end (W0.5); in-sample label on the metrics panel (W0.7); schema-filtered params, precedence policy and request preview (W1.2, R7); operation-id-aware timeout handling, four races (W1.5); 401/429/`restored` (W1.6); version display and dependency floor (W1.7); `funcName`/rotation (W2.9); regression-coverage module (W3.7); runbook (W4.1); scope/split propagation to the UI (W5.3).

#### juniper-deploy

- **Fix:** Compose pins to juniper-data 0.17.0 (then recurrence 0.6.0 / canopy 0.9.0) with an authenticated canopy → recurrence → juniper-data smoke in `juniper-deploy-test` (W1.11); recurrence snapshot bind mount (W1.12).

#### Documentation (all repos, parent `AGENTS.md`)

- **Fix:** runbooks (W4.1); README examples (W4.2); parent inventories and port table (W4.3); versions (W4.4); stale juniper-data/juniper-ml references (W4.5); banners and #183/#184 sentences (W4.6).

---

## Current Status of Features and Fixes

### Status per Feature

| Priority | Feature / Fix | Status | Phase | Target Version |
| --- | --- | --- | --- | --- |
| **P0** | Env repair (operator recipe) + scoped launcher preflight (W0.1, W0.2) | In Progress — W0.1 model half applied 2026-10-04 (bench 37/37; `/v1/crossval` 200 without `PYTHONPATH`), service-core half deferred (live cascor on `:8202` imports from the env), recipe recorded (juniper-recurrence#189); W0.2 PR in flight | 0 | juniper-ml 0.10.x |
| **P0** | Suite phase-derived `degraded` outcome + exit code (W0.3, R6) | Planned | 0 | juniper-ml 0.10.x |
| **P0** | Headline metrics schema on four fixtures (W0.4) | Planned | 0 | juniper-ml 0.10.x |
| **P0** | Canopy 422 detail end to end (W0.5) | Planned | 0 | canopy 0.8.x |
| **P0** | CLI `--params`/`--params-file` (W0.6) | Planned | 0 | recurrence 0.5.x |
| **P0** | `metrics_scope: in_sample` label, service + canopy panel (W0.7) | Planned | 0 | recurrence 0.5.x, canopy 0.8.x |
| **P0** | E-H crossval replay diagnostic (W0.8) | Done 2026-10-04 — §1 of `JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`: E-H config eval r² −0.115 (per fold −0.08 … −0.26); service defaults −20,345 on the same artifact | 0 | note |
| **P0** | Controlled matrix and P5 go/no-go (W0.9) | Done 2026-10-04 — §2 of `JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` (24 cells); verdict **GO**: (a) confirmed, (b)/(c) refuted, (d) not implicated; consensus review owed before R5 | 0 | note |
| **P1** | Documented param bundle; optional preset (W1.1, R1) | Planned | 1 | juniper-data docs / 0.17.0 |
| **P1** | Canopy schema-filtered params, precedence, preview (W1.2, R7) | Planned | 1 | canopy 0.9.0 |
| **P1** | Explicit target selection (W1.3, R8) | Planned | 1 | model 0.4.0, recurrence 0.6.0 |
| **P1** | Validator gaps incl. float32 (W1.4, R2) | Planned | 1 | data-client 0.6.0 |
| **P1** | Operation id, timeouts, model identity, four races (W1.5) | Planned | 1 | recurrence 0.6.0, canopy 0.9.0, juniper-ml 0.10.x |
| **P1** | 401/429/`restored`, version floor (W1.6, W1.7) | Planned | 1 | canopy 0.9.0 |
| **P1** | `cost_basis` under `drop` (W1.8, R3) | Planned | 1 | juniper-data 0.17.0 |
| **P1** | Launcher CLI path + rerun parity, snapshots/log env (W1.9, W1.10) | Planned | 1 | juniper-ml 0.10.x |
| **P1** | juniper-data 0.17.0 release, floors, Compose pins, deploy smoke (W1.11) | Planned | 1 | juniper-data 0.17.0, juniper-ml 0.11.0, juniper-deploy |
| **P1** | P1 release train: recurrence 0.6.0, model 0.4.0, data-client 0.6.0, canopy 0.9.0 + remaining pins (W1.13) | Planned | 1 | those four, juniper-deploy |
| **P1** | Recurrence snapshot bind mount in Compose (W1.12) | Planned | 1 | juniper-deploy |
| **P2** | Exception + inventory + diagnostics logging (W2.1, W2.3, W2.4) | Planned | 2 | recurrence 0.6.x, model 0.4.x |
| **P2** | Request ids across three services (W2.2) | Planned | 2 | recurrence 0.6.x, canopy 0.9.x |
| **P2** | Snapshot/4xx logging, `init_logging`, DEBUG (W2.5, W2.6) | Planned | 2 | recurrence 0.6.x |
| **P2** | Failure metrics (W2.7) | Planned | 2 | recurrence 0.6.x |
| **P2** | Driver failure evidence capture (W2.8) | Planned | 2 | juniper-ml 0.10.x |
| **P2** | Canopy `funcName`/rotation; producer logging (W2.9, W2.10) | Planned | 2 | canopy 0.9.x, juniper-data 0.17.0 |
| **P3** | Crossval route test on 3-partition fixture; deep readiness (W3.0a, W3.0b) | Planned | 3 | recurrence 0.6.x |
| **P3** | Compositional CI lane (W3.1, lands first) | Planned | 3 | recurrence CI |
| **P3** | Realistic fixtures + error-path tests (W3.2) | Planned | 3 | recurrence 0.6.x |
| **P3** | Bench equities lane, drift prose, #178 triggers, canopy env, canopy regression module (W3.3–W3.7) | Planned | 3 | — |
| **P4** | Runbooks ×2 (exclusive ownership; r² text deferred to R5), README, parent `AGENTS.md`, versions, stale refs, banners (W4.1–W4.6) | Planned | 4 | — |
| **P5** | CV cause investigation note, content gated by W0.9 (W5.1) | In Progress — verdict GO, so W5.1 is tuning + documentation; §1–§2 written (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`); remaining: consensus review, R5 ruling | 5 | note |
| **P5** | Entity-grouped chronological CV via model-core `order`/`groups` (W5.2) | Planned | 5 | recurrence 0.6.x, model 0.4.x |
| **P5** | Predict OOS metrics with scope/split/identity through canopy; `test_r2` (W5.3) | Planned | 5 | recurrence 0.6.x, canopy 0.9.x, juniper-ml 0.11.0 |
| **P5** | Acceptance-band facility + E-H band (W5.4, R5, R6) | Planned | 5 | juniper-ml 0.11.0 |
| **P5** | Target summary, shared cache, producer guards (W5.5–W5.7) | Planned | 5 | — |

### Status Legend

| Status | Description |
| --- | --- |
| Done | Implemented, tested, and released |
| In Progress | Currently being worked on |
| Planned | Scheduled for future implementation |
| Deferred | Postponed to a later phase or version |
| Cancelled | No longer planned |

### Priority Legend

- **P0 (Phase 0)**: Critical — the path lies about its own state; fix first
- **P1 (Phase 1)**: High — the path cannot be driven correctly from one or both entry points
- **P2 (Phase 2)**: High — the path cannot be diagnosed when it fails
- **P3 (Phase 3)**: Medium — the failure class is not caught by CI
- **P4 (Phase 4)**: Medium — operators are misled by documentation
- **P5 (Phase 5)**: High but dependent — the numbers the path produces are not yet trustworthy

---

## What's Next

### Near-Term (Next 2-4 Weeks)

- Owner rulings **R1–R8** (§"Risks & Assumptions"). R6 (degraded exit semantics) gates W0.3 and so is needed first; R2, R3, R7, R8 gate P1 items (W1.4, W1.8, W1.2, W1.3); R1 is optional (W1.1b); R5 waits on W0.9's verdict; R4 is converted to a note (no ruling needed).
- P0 in one PR per repo (juniper-ml, juniper-recurrence, juniper-canopy) plus the operator env repair on the host (W0.1); re-run Scenario A and attach the new `registry.jsonl` showing `degraded` → then `succeeded` after W0.1; run W0.8 and write §1 of the W5.1 note; run the W0.9 matrix once W0.1 and W0.6 have landed and issue the go/no-go as §2 — M0 closes on that verdict.
  **Progress 2026-10-04**: W0.8 and W0.9 are done and the verdict is GO (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`); juniper-recurrence#189 (W0.1 recipe) and #190 (W0.6, W0.7 service half) are merged; juniper-ml was split into two PRs (W0.2; W0.3 + W0.4) for independent review; the Scenario-A re-run with `degraded` is still owed once W0.3 lands; the W5.1 note's consensus review is owed before R5.
- P1 in dependency order: juniper-data-client (W1.4) → juniper-recurrence-model (W1.3, W1.4) → juniper-recurrence (W1.5 service half) → juniper-canopy (W1.2, W1.5 canopy half, W1.6, W1.7) → juniper-ml (W1.5 driver half, W1.9, W1.10); juniper-data (W1.1, W1.8, W1.11 release) and juniper-deploy (W1.11 pins + smoke, W1.12) in parallel; W1.13 publications last, in data-client → model → recurrence → canopy order.

### Next Release (v0.6.0 juniper-recurrence / v0.9.0 juniper-canopy / v0.11.0 juniper-ml)

- P2 and P3 together; W3.1 (compositional lane) lands first so the logging PRs' tests run against both checkouts.
- P4 alongside, each doc PR naming the findings it closes; runbooks hold the r² interpretation text until R5.
- P5 after M1, with content set by W0.9's verdict: W5.1 (cause note) and W5.2 (grouped CV) proceed independently; W5.3 needs W1.5's `operation_id`; W5.4 builds the acceptance facility before R5's band is encoded.

### Coverage Goals

- `juniper_recurrence/routers/training.py`, `crossval.py`, `snapshots.py`: every non-2xx branch has a route test and a caplog assertion (currently 2 of ~12 branches).
- `juniper_recurrence/data.py`: exercised with the real `validate_npz_contract` (currently 0 %).
- `juniper_recurrence/cli.py` `train`: `--params` reaches the client and a bounded offline E2E completes (W0.6; currently the CLI cannot drive equities at all).
- `util/experiments/run_suite.py::_headline_metrics` and the outcome derivation: unit-tested on four `stats.json` fixtures and a phase-failed manifest (currently untested).
- `juniper-canopy` recurrence adapter: the four timeout races and the 409-from-another-caller case each have a named test (W1.5/W3.7).

---

## Dependencies

| Dependent Item | Depends On | Type | Risk Level | Notes |
| --- | --- | --- | --- | --- |
| W0.2 preflight refusing | W0.1 env repair | ORG | L | Until W0.1 lands the launcher will (correctly) refuse to start recurrence in `JuniperCascor1`; W0.3/W0.4 do **not** depend on W0.2 and can merge in parallel |
| W0.3 degraded outcome | R6 ruling | ORG | L | Exit semantics for informational rows must be ruled before the suite's exit code changes |
| W0.8 replay, W0.9 matrix | W0.1 env repair, W0.6 CLI `--params` (for unattended runs) | TECH | M | W0.8 can run shadowed by hand; W0.9 needs the repaired env and the CLI to drive it (or is run shadowed by hand if W0.6 slips) |
| W0.9 go/no-go | W0.8 | ORG | H | Sets P5's content and W1.1(a)'s `normalize_features` value; R5 is not ruled before it; M0 requires it |
| W1.1(a) bundle merge | W0.9 verdict | TECH | L | Draft early; merge after the verdict so the documented bundle never contradicts the matrix |
| W1.13 release train | W1.3, W1.4, W1.5, W1.6, W1.7 merged; W1.11 published | ORG | M | Owns the four publications M1 names; slip handled by the W1.11 slip rule |
| W3.0a, W3.2 fixtures | `juniper-data-client` validator behaviour (W1.4) | TECH | M | Fixture must satisfy the validator as it is at merge time; land W1.4 first or pin the client |
| W1.3 model target default | R8 ruling | ORG | M | Breaking for `y_*`-only artifacts; independent of W1.4 |
| W1.2 preview and filtering | `dataset_schema.py` declaring every `equities_seq` param; R7 ruling | TECH / ORG | M | Schema must be complete or the filter drops valid params |
| W1.5 canopy half | W1.5 recurrence half (`operation_id` on train/409/status) | TECH | L | Merge recurrence first; canopy tests use a fake service in the meantime |
| W1.5 driver half (`expect_operation_id`) | W1.5 recurrence half | TECH | L | Same |
| W1.11 | #437 on `main` (done), juniper-data release process, juniper-deploy PR access | ORG | M | **M1 requires it**; floors in juniper-ml 0.11.0 and the Compose pins follow the PyPI/GHCR publish |
| canopy against 6.0.0 metadata | W1.11 | TECH | M | Until then only a `main` checkout of juniper-data serves `regression` |
| W2.2 request ids | `juniper-observability` `RequestIdMiddleware` (exists) | TECH | L | Canopy must forward; data-client already does if ContextVar set |
| W3.2 and later P3 tests | W3.1 compositional lane | TECH | L | Lane first so the fixture-driven tests run against both checkouts |
| W5.3 `test_r2` | W1.5 `operation_id`, W0.7 label, W5.4 band columns | TECH | M | Model identity on predict comes from W1.5; the `test_r2` band cell needs W5.4's facility |
| W5.4 band | W5.4 facility (new), W0.9 verdict, R5 ruling | ORG | H | No `acceptance:` facility exists; a band chosen before the blow-up is understood will be wrong |
| W5.2 grouped CV | `SequenceData` exposing `ticker_code`/`window_end_date`/`target_dt`; model-core `splits.py` (exists) | TECH | M | Independent of W5.1 |

### Critical Dependencies

```text
W0.1 env repair ──▶ W0.2 preflight ──▶ Scenario A re-run (truthful)
R6 ──▶ W0.3 degraded ──┐
W0.4 headline ─────────┴──▶ W5.4 facility ──▶ R5 band
W0.6 CLI --params ──▶ CLI E2E (W0.6 acceptance) ──▶ W0.9 unattended matrix
W0.8 replay ──▶ W0.9 go/no-go ──▶ M0 ──▶ P5 content ──▶ R5 ──▶ W5.4 band
W1.4 validator ──▶ W3.0a / W3.2 fixtures ──▶ (after W3.1 lane) P3 tests
R8 ──▶ W1.3 model target
R7 ──▶ W1.2 canopy precedence
W1.5 recurrence operation_id ──▶ W1.5 canopy poll / W1.5 driver expect_operation_id ──▶ W5.3 model identity
#437 (done) ──▶ W1.11 juniper-data 0.17.0 ──▶ juniper-ml floors ──▶ Compose pins + deploy smoke ──▶ M1 (code half) ──▶ W1.13 publications
W0.7 label ──▶ W5.3 scope/split values ──▶ test_r2 band cell
```

### Shared Dependencies

All items share dependencies on:

- the decision-11 NPZ contract (`train|val|test`, no `*_full`) as recorded in the parent `AGENTS.md` Data Contract section;
- `juniper-observability` and `juniper-service-core` from the juniper-ml checkout (0.7.0) for middleware and lifecycle;
- the owner rulings R1–R8 (R4 is a recorded note, not a pending ruling).

---

## Risks & Assumptions

### Risks

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| The CV blow-up (F-SCI1) is a model/CV defect that the E-H configuration also exhibits (W0.9 returns "no-go") | H | M | W0.8 measures this in P0 under the real configuration before any P5 design; W0.9 widens to a controlled matrix with linear/RFF, three ridge settings and `gcv`; the result is written up before any suite or band change |
| The −18,081 is attributed to the wrong cause because the audited request was service-default (linear, `ridge=0.0`), not E-H's RFF config | H | H (today) | §3.9 F-SCI1 now states the cause is unresolved and names the measured configuration; W0.8 replays the real one |
| Preflight (W0.2) blocks every recurrence launch on this host until W0.1 is done, or refuses on unrelated `pip check` noise (the CUDA conflicts) | M | H | Land W0.1 first; preflight is scoped to the recurrence closure; `--skip-env-preflight` exists for emergencies and logs loudly |
| Canopy schema filtering (W1.2) drops a legitimately staged param because `dataset_schema.py` is incomplete, or the precedence rule overrides operator intent | M | M | Test enumerates `equities_seq/params.py` fields against the schema; R7 fixes the precedence; the preview shows the effective body |
| `degraded` outcome (W0.3) breaks consumers of `registry.jsonl`/`index.jsonl` that only know `succeeded` / `failed` / `timed_out`, or is derived from the wrong signal and later conflicts with W5.4's band outcomes | M | M | `TERMINAL_OUTCOMES` and every consumer audited in the same PR; derived from per-phase results, not `acceptance.ok`; R6 fixes exit semantics |
| Requiring `y_reg` (W1.3) breaks a non-equities artifact that only has `y_*` | M | L | `target="auto"` retained for the bench; R8 decides semver handling; CHANGELOG "Breaking" if shipped in 0.6.0 |
| Two callers share one recurrence listener (F-CON3) and one sees the other's 409 or scores the other's model | M | M | W1.5 adds `operation_id`/`expect_operation_id`; W4.1 documents exclusive ownership; the launcher's per-run ports remain the default |
| Grouped chronological CV (W5.2) changes bench numbers | L | H | Bench bands re-baselined with a note; single-entity behaviour unchanged |
| juniper-data 0.17.0 bumps the `dataset_id` for `equities_seq` on every published deployment (6.0.0) | L | H | Intended (X8); caches re-mint |
| The published Compose stack (data 0.16.0 / recurrence 0.5.0 / canopy 0.8.1) keeps serving `equities_seq` as `classification` until W1.11 lands | M | H (today) | W1.11 is P1 and M1 requires it; the deploy smoke proves the published images end to end |

### High-Risk Areas

1. **Scientific interpretation (P5)**
   - Risk: a band is set to make the current number pass, or the blow-up is "fixed" by hiding it.
   - Mitigation: W0.8 and W0.9 are measured under the real configuration first; the W5.1 note is a note of record reviewed under the consensus procedure before R5 is ruled; the W5.4 facility ships before the band is encoded.

### Medium-Risk Areas

1. **Canopy request shaping (W1.2)**
   - Risk: operator intent is overridden silently in the other direction (seed beats form).
   - Mitigation: the preview element shows the effective body; the rule (R7 recommended default) is "explicit recurrence-aware form change wins, generic form does not".
2. **Environment drift recurrence (W0.1/W0.2)**
   - Risk: another `conda` upgrade recreates F-E1 silently.
   - Mitigation: preflight is in the launcher, not in a note; deep readiness (W3.0b) covers the Compose path; the compositional CI lane catches the code side.
3. **Service identity across callers (W1.5)**
   - Risk: a timed-out canopy run and a driver run share a listener and one scores the other's model.
   - Mitigation: `operation_id` on every mutating response and `expect_operation_id` on predict/save; exclusive ownership documented.

### Low-Risk Areas

- Logging additions (P2) — additive, caplog-tested, no behaviour change.
- Documentation (P4) — reviewed against code lines cited here.

### Assumptions

- **A1**: the user's reported "errors" are the ones reproduced in §1; no other failure mode was reported. If a different symptom exists (e.g. a 500 from the fit), §3.6 F-L1 explains why it would have no useful log, and W2.1 is the first fix.
- **A2**: one host, one day, one ticker set (AAPL; the 5-symbol canopy seed). The ENV attribution (F-E1) is solid because the same request succeeded shadowed; the SCI observation (F-SCI1) is **n = 1 artifact under the service-default configuration** (linear readout, `ridge=0.0`), which is not the configuration E-H runs — its cause is unresolved until W0.8.
- **A3**: the producer contract at `equities_seq` 6.0.0 / `equities` 5.0.0 is stable for the plan's horizon; X8 is the last relabel.
- **A4**: owner rulings R1–R3 and R5–R8 will be given; the plan's P0, P1 and P5 items are written so that any ruling is implementable. R4 needs no ruling (see below).
- **A5**: `juniper-canopy` continues to call the recurrence service over HTTP via `recurrence_service_adapter.py` (no in-process backend).
- **A6**: one owner plus agent sessions is the staffing for the milestone dates.

### Owner rulings required

| Ruling | Question | Plan's recommendation | Gates |
| --- | --- | --- | --- |
| R1 | Should juniper-data expose a recurrence-ready `equities_seq` preset (param bundle hashed into the id), or is the documented explicit bundle (W1.1a) enough? | Preset is **optional**; the documented bundle is the recommendation and ships regardless | W1.1b |
| R2 | Should `validate_npz_contract` enforce `float32` (contract as documented) or document dtype tolerance (behaviour as implemented)? | **Enforce** — the Data Contract says `float32`, and a tolerant validator is one more place the contract and the behaviour differ | W1.4 |
| R3 | Under `fundamentals_fill="drop"`, what happens to pre-`purchase_date` `cost_basis` NaN: drop rows, finite sentinel, or refuse? | Refuse when `purchase_date > start_date` under `drop` (the request is contradictory); otherwise drop rows | W1.8 |
| R4 | *(converted to a note — no ruling needed)* Fold-local preprocessing is **required regardless** of W0.9's verdict; see the R4 note below the table. | — | W5.1, W5.2 (owner note) |
| R5 | Acceptance band for E-H `cv_r2`/`test_r2` and gate vs report-only (plan R-6 says equities rows are informational). | Ruled **after** W0.9's verdict and the W5.1 recommendation; the plan does not propose numbers before the measurement | W5.4 |
| R6 | Exit semantics for informational rows: when an informational (equities) row is `degraded` or `flagged`, does the suite exit non-zero? | **Yes for `degraded`** (a phase that was asked for did not run — that is a suite defect, not a science result); **no for `flagged`** (report mode); `gate` mode is the row's explicit opt-in to fail | W0.3, W5.4 |
| R7 | Canopy forwarding precedence when the registry seed and the staging form disagree. | Generic-form defaults never override the seed; an explicitly edited recurrence-aware field wins; the preview shows the result | W1.2 |
| R8 | Changing the model's target default to `reg` breaks `y_*`-only artifacts. Ship in recurrence 0.6.0 as a pre-1.0 "Breaking" minor, or keep `auto` default with a deprecation warning for one release? | Ship in 0.6.0 with CHANGELOG "Breaking"; the bench keeps `auto` explicitly | W1.3 |

**R4 note.** The producer's `normalize_features` is fitted on the pooled `train` partition, so under full-view CV its statistics leak into the early folds whose eval rows are inside that partition.
The recurrence fit must standardise memory per fold (it already does for RFF, `readouts.py:226-259`), and any feature normalisation it adds must be fitted on the fold's train rows.
Producer-side `normalize_features: true` remains a valid convenience for the happy path, not a CV control.

---

## Test Coverage Requirements

| Phase | Unit Tests | Integration Tests | Target Coverage |
| --- | --- | --- | --- |
| Phase 0 | 14 (preflight stale ×1 + unrelated-noise ×1, degraded phase-derived ×2, headline fixtures ×4, 422 detail ×2, CLI params ×3, `metrics_scope` ×2) | 4 (Scenario A re-run, as-served env; CLI offline E2E; W0.8 replay; W0.9 matrix) | `run_suite.py::_headline_metrics` 100 %; `cli.py` `train` params path 100 % |
| Phase 1 | 22 (canopy staging ×3, target ×2, validator ×4, operation-id routes ×3, canopy races ×4, driver knobs ×2, 401/429/restored ×3, version ×1) | 3 (canopy → recurrence → fake data, timeout → status; deploy smoke on published images) | adapter + backend ≥ 90 %; `routers/training.py` ≥ 90 % |
| Phase 2 | 12 (caplog per path; metrics; request id ×3; driver evidence ×2) | 1 (request id across three services) | routers/*.py non-2xx branches 100 % logged |
| Phase 3 | 10+ (crossval route on 3-partition fixture; deep ready; fixture-driven route tests; guard; drift prose) | 2 lanes (compositional; bench-equities cached) + #178 trigger proof | `juniper_recurrence/data.py` 100 % with real validator; `routers/crossval.py` ≥ 90 % |
| Phase 5 | 11 (grouped CV ×4, predict metrics + scope ×3, band facility ×3, target summary, close guard) | 1 (E-H suite end to end with band) | model `crossval.py` ≥ 90 %; `run_suite.py` acceptance parser 100 % |

---

## Out-of-Scope / Future Ideas

- **Flat `equities` → sequence adapter** in the recurrence app (window the 2-D artifact per ticker on the fly) — not now; `equities_seq` exists for this and the 2-D refusal is correct.
- **Cancellable training** (`DELETE /v1/training`) — would close F-S6 fully; deferred because the LMU fit is a closed-form solve and the long pole is the yfinance fetch, which lives in juniper-data. W1.5's `operation_id` is the prerequisite if it is ever built.
- **Service-side feature normalisation beyond memory standardisation** — fold-local preprocessing is required (R4 note) and the RFF readout already standardises memory per fold; adding fold-local *feature* scaling in the service is a P5 follow-up only if W0.9 shows it matters.
- **Canopy pre-selection availability badge** (F-C9) — cosmetic; after P1.
- **JSON logging by default across the three services** — after W2.2 proves correlation in text mode.
- **Restore-on-boot for snapshots** in the Compose service — W1.12 mounts the directory; automatic restore is a separate design decision.

---

## References

- Consensus record for this plan: `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`
- Consensus lane reports (round 1 and round 2): `juniper-ml/reports/2026-10-03_recurrence-equities-consensus/laneA1.md`, `laneA2.md`, `laneA3.md`, `laneB1.md`, `laneB2.md`, `oracle.md`, `laneA1-r2.md`, `laneB1-r2.md`
- Procedure: `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
- Deployment pins and the recurrence Compose block: `juniper-deploy/docker-compose.yml` (`:164`, `:523` juniper-data 0.16.0; `:598` recurrence 0.5.0; `:662`, `:806`, `:897` canopy 0.8.1; recurrence service block `:586-648`, no `volumes:`)
- Existing grouped/ordered fold support: `juniper-model-core/juniper_model_core/crossval/splits.py` (`walk_forward_folds(order=, groups=)`; tests in `juniper-model-core/tests/test_crossval_splits.py`)
- Template: `notes/templates/TEMPLATE_DEVELOPMENT_ROADMAP.md`
- CLI experiment-mode design of record: `JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md` (§5, §6, §8.2, §10.5, H-9, R-6)
- Persistence design: `JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` (§11.1)
- Equities ingest sizing: `JUNIPER_2026-09-04_JUNIPER-DATA_EQUITIES-INGEST-SIZING-AND-FIELD-AVAILABILITY.md`
- Earlier recurrence notes (to receive banners, W4.6): `JUNIPER_2026-06-14_JUNIPER-RECURRENCE_MODEL-DETAILED-DESIGN.md`, `JUNIPER_2026-06-15_JUNIPER-RECURRENCE_WS4B-APP-BUILD-PLAN.md`, `JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md`, `JUNIPER_2026-06-18_JUNIPER-RECURRENCE_EVALUATION-FINDINGS.md`, `JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md`, `JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md`
- Related consensus precedent: `JUNIPER_2026-09-05_JUNIPER-CANOPY_SELECTION-DEADLOCK-CONSENSUS-VALIDATION.md`
- Parent ecosystem guide: `/home/pcalnon/Development/python/Juniper/AGENTS.md` (Data Contract; Conda Environments)
- Repo guides: `juniper-recurrence/AGENTS.md`, `juniper-canopy/AGENTS.md`, `juniper-data/AGENTS.md`, `juniper-ml/AGENTS.md`
- Suite and configs: `juniper-ml/util/experiments/suites/p4/e-h-recurrence-real-data.yaml`; `juniper-recurrence/conf/experiments/irregular-sine-rff.yaml`
- Ecosystem guards: `juniper-ml/tests/test_equities_symbol_cap_operator.py`; `juniper-data/juniper_data/tests/unit/test_val_emission_guards.py`
- Open issues for context (none modified by this arc): juniper-recurrence #178, #182, #183, #184; juniper-canopy #368; juniper-data #409, #423, #437; juniper-ml #1994
- Evidence: `juniper-ml/.amp/in/artifacts/recurrence-equities-audit/` (§2.3)

---

## Change Log

| Date | Version | Changes | Author |
| --- | --- | --- | --- |
| 2026-10-03 | 1.0.0 | Initial audit and development plan; pending consensus validation | Paul Calnon |
| 2026-10-03 | 1.1.0 | Round-1 consensus corrections: F-SCI1 rewritten (cause unresolved); new §3.10 DEPLOY and §3.11 CONCURRENCY classes; F-S9 added; P0 gains W0.6–W0.8; W1.0 go/no-go; W1.11 release/pins moved to P1 as an M1 requirement; W1.12, W3.0a/b added; W5.2/W5.4 rewritten; R4 → note; R6–R8 added; milestones rebaselined. Itemised in the consensus note. | Paul Calnon |
| 2026-10-03 | 1.2.0 | Round-2 consensus corrections: F-SCI1 CV population 1,698 windows (not 1,346), per-fold RMSE, F-E1 evidence, F-CON2 wording; W1.0 → **W0.9** closing P0 (M0 requires it); W1.13 release train; W1.11 slip rule; W5.4 missing-metric by mode; W5.2/W5.6/W3 order fixes; milestones rebaselined (owner to confirm); Status → validated. Itemised in the consensus note. | Paul Calnon |
| 2026-10-04 | 1.3.0 | P0 execution: W0.8/W0.9 measured (`JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md`); F-SCI1 resolved, **verdict GO**; W1.1 bundle fixed (`normalize_features: false` + model half); W5.8/W5.9 proposed; F-P8 added; W0.1 model half applied, recipe recorded (juniper-recurrence#189), service-core half deferred; status table and M0 track the P0 PRs. Not consensus-reviewed. | Paul Calnon |
