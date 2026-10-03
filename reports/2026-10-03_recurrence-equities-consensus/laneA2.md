# Lane A agent A2 — source-citation re-derivation

**Procedure:** `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A and §7  
**Target:** `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`  
**Entry point:** source checkouts only; `.amp/in/artifacts` was not opened  
**Repos measured:** juniper-recurrence `be081fa` (0 dirty); juniper-canopy `72b1a5f6` (0); juniper-data `1c67f8d` (0); juniper-data-client `0ec4b30` (0); juniper-ml `afb02801` (229); juniper-deploy `9403dbf` (0)  
**Date:** 2026-10-03  
**Brief:** Independently check the plan's source citations and stated code behavior. Line drift of at most ten lines is accepted when the cited implementation is present.

## 0. Instrument

| Instrument | Could it produce a different answer? | Sample size | What was NOT done |
| --- | --- | ---: | --- |
| `nl -ba`, `sed`, `rg`, `awk`, `find`, `git rev-parse`, and `git status` against source checkouts | Yes. Searches could find absent/present symbols, and direct line reads could contradict the prose. | 40 citations/findings | No services or tests; no environment/package probes; no evidence-artifact reads; no validation of runtime measurements or scientific numeric results. |

## 3.1 Environment and launcher

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-E2 | `util/experiment_stack.bash:731-757` | VERIFIED | Lines 733-740 resolve the console script and only call `require_env_bin`; line 757 calls `wait_for_health ... /v1/health/ready`. No `pip check`, version-floor, or import probe appears. |
| F-E3 | `routers/crossval.py:65-73`; app readiness | VERIFIED | Crossval lines 65-73 call `load_sequence_data(... split="full")`. `app.py:86-91` delegates generic health creation to `create_app`; no full-split derivation probe is added. |
| F-E5 | launcher env defaults | VERIFIED | `experiment_stack.bash:67,142`: recurrence defaults to `JuniperCascor1`; `isolated_stack.bash:43-46,93-97` says no dedicated env and selects the same environment. |

## 3.2 CLI experiment driver and suite

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-D1a | `run_suite.py:694` | VERIFIED | Line 694: `row["outcome"] = manifest.get("outcome", "failed")`. |
| F-D1b | `run_suite.py:781-782` | VERIFIED | Success is exactly `outcome == "succeeded"`; every other non-None outcome enters `failed`. |
| F-D1c | `run_experiment.py:1932-1948,1993,2030` | VERIFIED | `_aux_phase` appends `acceptance_reasons` and returns `None`; line 1993 sets `outcome = "succeeded"` after train; line 2030 changes only `exit_code` when acceptance reasons exist. |
| F-D2 | `run_suite.py:585-600` | VERIFIED | Lines 594-599 inspect only top-level `stats["cascor"/"recurrence"][metric]` for `final_accuracy`, `test_accuracy`, `val_accuracy`, `train_r2`, `cv_r2`, or `r2`; no nested `final_metrics`/`crossval.eval_aggregate`. |
| F-D3 | E-H YAML | VERIFIED | Lines 1-3 say `expect r2 ~ 0 ... NOT negative blowups`; line 13 sets `regression_target: log_return`; there is no `acceptance` or `normalize_features` setting. |
| F-D4 | `run_experiment.py:1869-1890` | VERIFIED | Line 1874 is `cli = shutil.which("juniper-recurrence")`; failure returns “CLI not found on PATH”. |
| F-D5 | timeout sites | VERIFIED | Dataset creation uses fixed `timeout=120.0` at line 831; auxiliary calls use `timeout=max_wall` at 1937; suite subprocess uses its own `timeout` at 683. |
| F-D8 | `stats_summary.py` | VERIFIED | The source summarizes dimensions/classes and contains no regression-target finite/mean/std/min/max summary. |
| F-D9 | launcher and settings | VERIFIED | Launcher lines 742-754 export metrics, rate-limit, data URL, and config only. No `JUNIPER_RECURRENCE_SNAPSHOTS_DIR` exists in either launcher. `settings.py:201-204` defaults to relative `Path("recurrence-snapshots")`. |

## 3.3 Recurrence service and model code

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-S1 | `main.py:50-66,137-144`; `data.py:45-46` | CONTRADICTED | The substantive defect is real, but the exact claim “passes `params={}`” is false. Train defines dataset/name/generator/split plus model/config/output options, with no `--params` or `--params-file`; lines 137-144 omit `params` entirely. The default reaches `data.py:46`, `params=dict(params or {})`, and therefore becomes `{}`. |
| F-S2 | model `data.py:153-159` | VERIFIED | `y_reg_*` is preferred, then `y_*` silently; the branch contains no warning/log call. |
| F-S4 | model data and `_common.py` | VERIFIED | Model `data.py:147-150` rejects non-3-D X. `_common.py:49-52` maps `ValueError` to HTTP 422 with `invalid dataset: {exc}`. |
| F-S5 | training and predict routers | VERIFIED | `training.py:91-103` returns `result.final_metrics` from the fitted train split. `predict.py:73-74` returns only `predictions` and `shape`, no metrics. |
| F-S6 | `routers/training.py:44-105` | VERIFIED | Line 44 acquires `train_lock` non-blocking, lines 45-46 return 409 if busy, and lines 104-105 release only in `finally`; no cancellation endpoint/mechanism appears. |

## 3.4 Data producer and contract

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-P1 | equities `defaults.py` | VERIFIED | Lines 45, 50, 103 set `fundamentals_fill="nan"`, `normalize_features=False`, and `regression_target="next_close"`. |
| F-P2 | equities `generator.py:924-963` | VERIFIED | `drop` removes rows only on `total_shares` at line 927. Lines 951-956 set pre-basis `cost_basis` to NaN. The later `dropna` at line 963 names only OHLCV and `next_close`, not `cost_basis`. |
| F-P3 | data-client `contract.py:45-125` | VERIFIED | Current lines differ greatly from the plan. `_validate_dt` checks shape, negative values, and first-column zero, but not finiteness/dtype. No `target_dt` validation or dtype policy exists. |
| F-P7 | seq generator and model derivation | VERIFIED | Producer lines 296-300 concatenate by split, hence split-major. Model lines 116,121-124 concatenate train/val/test then stable-sort by `ticker_code`, yielding entity-major order. |

## 3.5 Canopy

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-C1 | adapter and `outbound_errors.py` | VERIFIED | Adapter lines 328-333 put `response.text` only in `body=` while exception messages contain status/path only. `outbound_error_text:60-61` returns `str(exc)`, so the body/detail is not carried through. |
| F-C2 | `recurrence_backend.py:104,127-130` | VERIFIED | `_STAGED_PARAM_KEYS = {"nn_dataset_elements": "n_samples", "nn_dataset_noise": "noise"}`; loop lines 127-129 forwards them. |
| F-C3 | `recurrence_backend.py:130` | VERIFIED | Exact line: `params.update(cfg.get("nn_dataset_params") or {})`; schema filtering is absent. |
| F-C8 | `model_registry.py`; `pyproject.toml` | VERIFIED | Registry lines 467 and 491 hard-code model version `0.1.0`. `pyproject.toml` has no `juniper-recurrence` dependency (only the unrelated cascor protocol match). |
| F-C11 | logger and config | VERIFIED | `logger.py:299` calls `makeRecord(... fn=fn, lno=lno, msg=..., args=..., exc_info=None)` with no `func`. `app_config.yaml:121-126` specifies midnight rotation, while `logger.py:257` constructs size-based `RotatingFileHandler`. |

## 3.6 Logging and observability

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-L1 | training/crossval routers | VERIFIED | `training.py:90-97` calls `lifecycle.run` directly; `crossval.py:117-130` calls `cross_validate` directly. Neither call has an exception-logging wrapper. |
| F-L2 | `app.py:93-139` | VERIFIED | Added middlewares are `RequestBodyLimitMiddleware`, `SecurityHeadersMiddleware`, optional `PrometheusMiddleware` plus mounted `MetricsAuthMiddleware`, and `SecurityMiddleware`. `RequestIdMiddleware` is neither imported nor added. |
| F-L8 | `rg -n 'logger\.debug'` | VERIFIED | Search across `juniper-recurrence` and `juniper-recurrence-model` returned 0 matches. |
| F-L9 | `metrics.py:26-72` | VERIFIED | Only completed-run/request counters and last-value gauges exist; increments occur inside success recorders at lines 54, 63, and 70. No failure counter, in-progress gauge, or histogram appears. |

## 3.7 Tests and CI

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-T1 | app `tests/conftest.py` | VERIFIED | Fixture lines 35-48 creates only train arrays; line 72 monkeypatches validator to `lambda arrays, **kw: "sequence"`. |
| F-T3 | `test_crossval_routes.py` | VERIFIED | Lines 34-40 create only `X_full`, `y_reg_full`, `dt_full`, `target_dt_full`, and `seq_lengths_full`; line 64 bypasses validation. |
| F-T4 | `ci-recurrence-app.yml:126-135` | VERIFIED | Workflow runs `pip install -e ".[test]"` from the app package and does not install sibling `juniper-recurrence-model`; app dependency resolution therefore comes from package index. |
| F-T7 | root `AGENTS.md` | VERIFIED | Version table lines 45-47 says app/model/client `0.5.0/0.3.0/0.3.0`; Status line 193 says `0.3.0/0.2.0/0.2.0`. |

## 3.8 Documentation

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-X1 | root/client READMEs | VERIFIED | Root lines 173 and 177 use `name="equities"`; client lines 43 and 50 do likewise. |
| F-X6 | app README and `_version.py` | VERIFIED | App README line 7 says `0.2.0`; `_version.py:9` says `0.5.0`. |
| F-X7 | parent guide and Compose | VERIFIED | Parent `AGENTS.md:44-77` omits recurrence from dependency graph, service ports, and agent-file table (despite its Active Repositories row). Compose lines 583-601 document/map host 8211 to container 8210; lines 673-677 point canopy to container port 8210. |

## 3.9 Scientific validity

| ID | Citation | Verdict | Evidence (quoted) |
| --- | --- | --- | --- |
| F-SCI2 | F-P7 source | VERIFIED | Producer explicitly documents split-major order at lines 281-290; model stable-sorts concatenated partitions by ticker at lines 121-124. Row-index walk-forward folds therefore are not globally chronological for multiple tickers. |
| F-SCI3 | training/predict source | VERIFIED | Train response exposes fit `final_metrics` (`training.py:91-103`); predict response has no metric (`predict.py:73-74`). Thus these routes provide no held-out metric. |
| F-SCI4 | E-H YAML | VERIFIED | The complete 14-line suite has no `acceptance` block or metric band, so source configuration cannot reject an extreme CV metric. |

## Tally

| VERIFIED | CONTRADICTED | NOT FOUND | Total |
| ---: | ---: | ---: | ---: |
| 39 | 1 | 0 | 40 |

## Verdict

The source citations overwhelmingly re-derive: 39 of 40 checks match the plan's stated behavior. The sole contradiction is wording, not the underlying defect: F-S1 says the CLI explicitly passes `params={}`, while it actually omits `params`; the callee's `dict(params or {})` still produces the same empty generator parameters. Runtime environment versions, recorded executions, and numerical scientific results remain outside what this source-only lane can support.
