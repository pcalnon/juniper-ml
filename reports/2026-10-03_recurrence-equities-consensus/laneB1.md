# Lane B agent B1 — adversarial review, lens: CORRECTNESS / OMISSION

**Procedure**: `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B and §7  
**Target**: `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`  
**Subject repos + HEAD SHAs**: juniper-ml `afb028015cb5`; juniper-recurrence `be081fae0749`; juniper-data `1c67f8d65841`; juniper-canopy `72b1a5f68be7`; juniper-data-client `0ec4b3019f04`; juniper-deploy `9403dbf5d1f8`  
**Date**: 2026-10-03  
**Brief**: refute

---

## 0. Instrument

| Instrument | Could it produce a different answer? | Sample size | What was NOT done |
|---|---|---|---|
| Direct static trace of the target plan, recurrence model/app, model-core CV, canopy request construction, experiment outcome consumers, and Compose declarations | Yes. Branches and precedence rules were followed to their concrete consumers; several attacks below failed | Six repositories; one audited AAPL artifact/run; all in-tree `outcome` consumers under `util/experiments/` | No services, test suites, network, browser, or package mutation; no numerical synthetic probe; no second host/artifact/ticker |
| Raw audit artifacts, especially `24-c-crossval-shadow.txt` and Scenario A `stats.json` | Yes. They contain per-fold values and exact 422 text rather than the plan's interpretation | One AAPL artifact, five folds, one host/day | No independent rerun; no matrix from W5.1 |

## FATAL

### F1 — W5.2 specifies a duplicate in the wrong repository and changes embargo semantics

**Claim attacked**: W5.2 asks `juniper-recurrence-model` to add `cross_validate(..., group_by="ticker_code", order_by="window_end_date")`, with “embargo in days,” as the fix for panel chronology.

**Evidence**: The fold API already supports `order` and `groups` in `juniper-model-core/juniper_model_core/crossval/splits.py:41-50,66-79,98-153`. The recurrence route is the missing wiring: `juniper-recurrence/juniper_recurrence/routers/crossval.py:81-88` calls it without either array, despite loading sequence auxiliaries. The existing contract defines embargo as a count of windows/rows, per group, not calendar days (`splits.py:63-79,139-145`).

W5.2's acceptance criterion (“no eval row precedes a train row”) is also too weak: ordinary pooled date sorting satisfies it while same-ticker lookback windows can still overlap unless the embargo is at least the lookback in windows.

**Severity**: FATAL — implementing the P5 item exactly as written can create a second CV API while leaving `/v1/crossval` unchanged, and silently changes the public meaning of `embargo`.

**Smallest correction**: Make the owner juniper-recurrence + juniper-model-core integration. Expose `ticker_code` and `window_end_date` from `SequenceData`, pass them as existing `groups`/`order`, retain embargo in windows (or add a separately named duration embargo), and test per-ticker lookback non-overlap as well as global chronology.

## MAJOR

### M-A — F-SCI1 attributes the failure to unnormalised RFF inputs despite mandatory train-fold RFF standardisation

**Claim attacked**: “`normalize_features` is unset ... raw price-level features drift out of the RFF kernel's training support,” with the observed pattern “consistent with regime shifts rather than a code fault.”

**Evidence**: `juniper-recurrence-model/juniper_recurrence_model/readouts.py:226-259` makes per-column standardisation of the LMU memory mandatory and train-fold-only; RFF fits and persists those statistics. `model.py:186-211` materialises a fresh readout on every fit. The plan discusses producer normalisation as though raw price levels enter the RFF kernel directly. They do not. Producer normalisation may still alter LMU dynamics, but that is a different mechanism.

The raw artifact shows predictions large enough for RMSE 3.27 against return-scale targets (`24-c-crossval-shadow.txt`), which deserves direct prediction/design diagnostics before “regime shift.”

**Severity**: MAJOR — the leading mechanism is mis-stated and can send R4 toward a producer toggle that does not diagnose the actual extrapolating component.

**Smallest correction**: State that RFF standardises **memory states**, not raw X. Add matrix cells/diagnostics for memory-state train/eval z-score range, RFF design range, target variance, prediction range, `target_dt`, theta, coefficient norm, and ridge conditioning. Remove the regime-shift inference until measured.

### M-B — the plan omits a direct code-level SCI hypothesis: service-default theta bypasses fold-local resolution

**Claim attacked**: W5.1's matrix is sufficient to distinguish normalisation/readout/ridge causes.

**Evidence**: `LMURegressor.fit` resolves data-driven theta only when `self.theta is None`, then mutates `self.theta` (`model.py:172-179`). Fresh models prevent cross-fold state carry-over, so that attack failed. But the service computes `theta = req.theta if supplied else settings.default_theta` and closes over that value for every fold (`routers/crossval.py:78-110`). If `default_theta` is non-null, every fold bypasses fold-local resolution.

W5.1 does not vary pinned versus fold-resolved theta or calendar-day `dt`, although the plan itself names dt/theta as a risk.

**Severity**: MAJOR — a plausible code/config mechanism is absent from the controlled matrix.

**Smallest correction**: Add `{theta: configured, theta: null/fold-resolved}` and dt-distribution diagnostics to W5.1; record the actual resolved theta per fold.

### M-C — W0.3's acceptance test conflates auxiliary-phase degradation with any acceptance failure

**Claim attacked**: “`outcome: degraded` when train succeeded but an enabled phase failed,” accepted by “train ok + `acceptance.ok false` → degraded.”

**Evidence**: The driver appends auxiliary failures and other failures to one `acceptance_reasons` list (`run_experiment.py:1932-1948,2022,2028`) and derives the exit code from whether that list is empty (`:2029-2032`). A future metric-band failure is also an acceptance failure. The proposed fixture cannot distinguish a failed crossval/predict/save from a scientifically failed acceptance band. Implemented literally, a bad metric becomes “degraded” rather than “failed.”

**Severity**: MAJOR — a P0 truthfulness fix can weaken the later P5 scientific gate.

**Smallest correction**: Derive `degraded` from explicit enabled-phase result records only. Keep acceptance-band failure as `failed` (or a separately ruled `flagged` state), and test both.

### M-D — the `degraded` consumer mitigation misses a schema/terminal declaration

**Claim attacked**: The risk mitigation “grep consumers ... treat `degraded` as non-success everywhere” covers the new value.

**Evidence**: `run_suite.py:81` declares `TERMINAL_OUTCOMES` as exactly succeeded/failed/stalled/timed_out. The plan names `list_runs.py`, `stats_summary.py`, and `compare_baseline.py`, but not this declaration. Existing comparison and baseline consumers already safely use `outcome != "succeeded"` (`compare_baseline.py:170-172`, `make_baseline.py:176-178`); the explicit enum is the drift-prone site. `read_run_metrics.py:70` separately enumerates truncating outcomes and should deliberately exclude degraded.

**Severity**: MAJOR — the mitigation inventory is backwards: it names tolerant consumers and omits the explicit outcome vocabulary.

**Smallest correction**: Add `degraded` to `TERMINAL_OUTCOMES`, audit every explicit outcome set, and add registry/index round-trip plus resume tests.

### M-E — Compose snapshot persistence is absent and no work item fixes it

**Claim attacked**: The plan covers runnable canopy/Compose and persistence-related operator behavior sufficiently via W1.7 and W1.11.

**Evidence**: `juniper-deploy/docker-compose.yml:589-647` defines recurrence without any snapshot bind/volume, while recurrence settings explicitly require a bind-mounted host store (`settings.py:189-203`). W1.11 sets a per-run snapshots directory only in the juniper-ml launcher. W1.7 only teaches canopy to interpret an already restored status; nothing makes a Compose-created equities snapshot survive container replacement or restores one on boot.

There is no restore-on-boot implementation in the app; restore is an explicit POST (`routers/snapshots.py:184-213`).

**Severity**: MAJOR — the Compose-launched canopy path loses saved models, and the specified fixes do not alter that operator experience.

**Smallest correction**: Add a Compose bind mount and explicit restore policy/runbook (manual or startup-selected snapshot), then test container replacement and canopy's `restored` rendering.

### M-F — the five root classes hide independent deployment and concurrency causes

**Claim attacked**: ENV/driver/params/contract/SCI are the useful root partition.

**Evidence**: Compose pins data 0.16.0, recurrence 0.5.0, canopy 0.8.1 (`docker-compose.yml:164,598,662`) and has its own secrets/wiring. That is release/deployment compatibility, not host ENV. Separately, recurrence serialises training and CV with independent locks, while canopy and CLI can target the same service; status/model state is process-global.

The plan handles a train 409 and crossval 409 individually but never establishes cross-operation exclusion or ownership. A canopy fit and CLI CV/snapshot/predict can therefore contend for or observe one shared model without run identity.

**Severity**: MAJOR — two omitted root classes (deployment/version topology; shared-service ownership/concurrency) require work beyond the five labels.

**Smallest correction**: Add DEPLOY and CONCURRENCY classes. Specify supported image-version tuples and a request/run owner identity plus cross-operation lock/state rules.

### M-G — W0.6's fixture does not prove the attribution it claims

**Claim attacked**: Rewriting one route fixture “fails on model 0.1.5, passes on 0.3.0” closes F-E1/F-T3.

**Evidence**: F-E1 was measured against one artifact and one stale installed wheel. W0.6 requires `ticker_code_*` but not `window_end_date_*`, despite the next scientific fix requiring chronology; it also asserts only a 200 and total count. A 0.3.x model can still reject a no-`_full` equities artifact whose entity-order metadata is incomplete or malformed. The app's route docstring itself remains stale and asserts `_full` emission/order (`routers/crossval.py:1-14`).

**Severity**: MAJOR — P0 can go green while the supported artifact family and chronology metadata remain unproved.

**Smallest correction**: Parameterise real-validator route tests over single/multi-ticker artifacts, missing/malformed ticker/date metadata, and old tolerated `_full` artifacts; assert derived row order, not only count; update the stale route contract.

## MINOR

1. **n=1 overreach**: canopy's registry says `max_symbols: 5` failed “on every Start” (`model_registry.py:295-303`), but the cited measurement establishes the default-universe request on one deployment, not every future registry/default universe. Replace with “with the then-current default universe.”
2. **n=1 overreach**: “`drop` beats `zero` on every measured axis” (`model_registry.py:313-315`, repeated as evidence in the plan) is one seed/host/artifact and selected metrics, not a general equities claim. Name the measured seed and axes.
3. **stale quantitative claim**: the canopy comment still foregrounds 39.6 s / 15,476 × 16 and then admits generator 5.0.0 was not re-fit (`model_registry.py:322-331`). Therefore using “46.5 s fit” or 39.6 s to dismiss the 300 s timeout for the current five-symbol seed is unsupported. Mark current-generator timing UNTESTED.
4. **“zero unlogged paths” acceptance overreach**: W2.5 can cover enumerated paths, but the plan's count of eight is from one audit and cannot prove all framework-generated validation/exception responses. Say “enumerated paths reach zero.”

## UNTESTED

- Whether near-zero eval target variance materially amplifies the reported r2. The artifact gives MSE/r2, from which it appears target variance is ordinary return-scale, but raw per-fold y was not independently loaded.
- Whether calendar-day dt versus trading-day dt causes the blow-up. The model contract intentionally uses elapsed units; no counterfactual was run.
- Whether RFF normal-equation float64 conditioning or coefficient magnitude is pathological. No synthetic/numerical probe was run.
- Whether a correct 0.3.0 wheel rejects a particular incomplete artifact. Code supports metadata-sensitive derivation, but no constructed artifact was executed.
- Current five-symbol canopy runtime against generator 6.0.0. The cited fit timing was explicitly not remeasured.

## Attacks that failed

1. **State carry-over between folds** — failed. `cross_validate` requests a fresh model per fold (`executor.py:129-154`), and each model materialises a fresh readout (`model.py:186-206`).
2. **Full-view scaler leakage** — failed. RFF statistics are fit inside each model/readout from the training memory block (`readouts.py:226-259`); leakage would tend to improve rather than explain the catastrophe.
3. **Embargo off-by-one for the audited single ticker** — failed. `train_end = eval_start - embargo` and eval begins at `eval_start` (`splits.py:117-133`), producing exactly the requested row gap. The configured embargo may be scientifically too small, but it is not off by one.
4. **No-staging canopy path accidentally sends generic `nn_dataset_elements=1000`** — failed. `_resolve_oneshot_start_body_handler` uses only registry defaults (`dashboard_manager.py:2921-2946`). Generic typed fields enter only the staged path, where the real defect exists (`recurrence_backend.py:100-131`).
5. **Compose lacks recurrence auth wiring/image declaration** — failed. Compose pins recurrence 0.5.0 and symmetrically mounts recurrence/data keys (`docker-compose.yml:598,610-634,673-677,715-720`). Snapshot persistence, not auth, is the deployment omission.
6. **Stale wheel attribution unsupported** — failed for the observed artifact. The same request's shadowed success and as-served `X_full` failure strongly isolate the installed model version. The correction needed is narrower supported-artifact coverage, not withdrawal of the observed attribution.

## Verdict

The plan correctly isolates the observed stale-wheel 422 and several operator-reporting defects, but it is not implementation-safe as written. W5.2 duplicates an existing model-core capability in the wrong package and changes embargo units; W0.3 can relabel scientific failure as degradation; and the SCI hypothesis overlooks mandatory RFF memory-state standardisation and a theta-resolution branch.

Compose snapshot persistence and shared-service concurrency remain outside the five-root-class story. Evidence is one host/day and one AAPL artifact, so broad timing and causal language must remain provisional.
