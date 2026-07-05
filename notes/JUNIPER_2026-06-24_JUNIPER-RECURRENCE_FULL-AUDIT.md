# juniper-recurrence — Full Repository Audit

**Project**: juniper-recurrence — Recurrent / Continuous-Time Neural-Network Application
**Repository**: pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Document Type**: Full repository audit (source, logging, monitoring, testing, CI, docs, design-gap)
**Version**: 1.0
**Last Updated**: 2026-06-24
**Audited at**: `origin/main` HEAD `9ef1b0b` (through PR #60)

---

## 1. Executive summary

juniper-recurrence is a **well-engineered, substantially built-to-design** 4-sub-project monorepo
(app + model-core + client + bench), with three packages live on PyPI (app 0.2.0, model 0.1.5,
client 0.2.0). The core scientific claim — the C1-clean, closed-form variable-Δt LMU (P3-C / Approach-C)
— is **mathematically correct and independently re-derived** in this audit, the full DP-3 readout
spectrum shipped and is measured (RFF +0.83 r² capacity lift on `delay_product`), and the app correctly
consumes the shared `juniper-service-core` framework. Test volume is high (~260 tests) and the prior
2026-06-21 pre-commit/testing/CI audit has been **remediated almost completely**.

**Overall verdict: healthy and close to "done", with two High-severity operational gaps and a cluster
of documentation drift.** No Critical findings. No security holes. No data-loss defects.

**Headline findings:**

| # | Severity | Theme | One-line |
|---|----------|-------|----------|
| H1 | **High** | Logging | The application has **no logging** beyond one `getLogger` and **never configures logging** — no operational visibility into training/inference/failures. |
| H2 | **High** | Testing/CI | The shipped `readout="mlp"` (torch) feature has **no merge-gating test** and is **omitted from coverage** — it can regress green. |
| M1 | Medium | Source correctness | `NaN`/`Inf` in the `dt` channel **bypasses the `dt < 0` guard** and silently produces `NaN` / an opaque `LinAlgError`. |
| M2 | Medium | Docs | **Version drift across all narrative docs** (AGENTS.md root + client, 3 READMEs still describe a 0.1.x / linear-only surface). |
| M3 | Medium | Docs | **Confirmed factual error**: app CHANGELOG says `juniper-data>=0.8.0`; pyproject pins `>=0.9.0`. |

**The integrative finding:** repo *reality is ahead of repo documentation* — the mirror image of the
2026-06-17 roadmap era when code lagged design. Every major design intent shipped; what trails is the
docs, plus operational logging and a couple of CI gating refinements.

---

## 2. Scope & methodology

- **Target**: `origin/main` @ `9ef1b0b`, audited in an isolated worktree (the on-host checkout was 22
  commits behind; this audit reflects current reality).
- **Dimensions**: (A) model-core source, (B) app source, (C) client source, (D) logging/monitoring/
  observability, (E) testing, (F) CI/CD + pre-commit + release, (G) docs/notes + design-reality gap.
- **Method**: seven parallel evidence-cited sub-audits, each grounded against the juniper-ml
  design-of-record corpus (`JUNIPER_RECURRENCE_*` design / build-plan / evaluation / DP-3 / state docs)
  and the prior `JUNIPER_2026-06-21_JUNIPER-RECURRENCE_PRECOMMIT-TESTING-CI-AUDIT.md`. The five highest-severity
  findings were **independently re-verified against source** by the synthesizer.
- **Limitation**: static analysis only — no on-host conda env carries the app's deps, so test suites
  and coverage percentages were **not re-executed** (the ~98 %/98 %/94 % figures are pyproject-comment
  claims, not re-measured here). GitHub environment protections and live CI run status are server-side
  and out of checkout scope. See §8.

---

## 3. Consolidated findings (severity-ranked)

Severity: **Critical** (correctness/security/data-loss) · **High** (significant gap / likely bug /
missing-essential) · **Medium** (maintainability / minor-correctness / drift) · **Low** (nit) ·
**Info** (note). All High/Medium are detailed in §4; Low/Info are listed compactly per dimension.

| ID | Sev | Location | Finding |
|----|-----|----------|---------|
| OBS-01 | High | `juniper_recurrence/` (routers, data, state) | No application logging beyond two `logger.warning`; routers/data/state log nothing. |
| OBS-02 | High | `juniper_recurrence` (no `basicConfig`/`dictConfig`) | Logging never configured; `settings.log_level` is read by nothing; no structured JSON / custom levels. |
| TEST-01 | High | model `pyproject.toml:85`, `ci-recurrence-model.yml:124` | torch MLP readout omitted from coverage AND only in a non-gating CI job — shipped feature can regress green. |
| MODEL-01 | Medium | `units/lmu_varstep.py:211`, `data.py:95` | `NaN`/`Inf` `dt` bypasses `np.any(dt<0)` guard → silent NaN / opaque `LinAlgError`; no test. |
| DOC-01 | Medium | `AGENTS.md:7,22-24,114` | Root AGENTS.md version table stale: app 0.1.1/model 0.1.3/client 0.1.0 vs real 0.2.0/0.1.5/0.2.0. |
| DOC-02 | Medium | `juniper-recurrence-model/README.md:11,53-59` | Model README omits the entire DP-3 readout spectrum (describes linear-only). |
| DOC-03 | Medium | `juniper-recurrence/README.md:7,42-52` | App README stale at 0.1.1: missing `readout` enum, `[torch]` extra, and the `/v1/metrics` route. |
| DOC-04 | Medium | client `AGENTS.md:7`, `README.md:44-54` | Client AGENTS.md version 0.1.0 vs real 0.2.0; README API table omits readout/RFF/MLP params. |
| DOC-05 | Medium | `juniper-recurrence/CHANGELOG.md:64` | Factual error: states `[bench]` pins `juniper-data>=0.8.0`; pyproject pins `>=0.9.0`. |
| TEST-02 | Medium | model & client `pyproject.toml` (no `filterwarnings`) | warnings-as-errors landed in the app only; model & client run deprecations silently. |
| OBS-03 | Medium | `app.py:91` | `set_build_info` omits available `git_sha`/`build_date` provenance (capability present in obs ≥0.4.0). |
| OBS-04 | Medium | routers `training/predict/crossval.py` | No domain metrics (train/predict counters, last-metric gauges) — only HTTP defaults. *(design-deferred)* |
| CI-01 | Medium | `juniper-recurrence/CHANGELOG.md:60,64` | 0.2.0 "Changed" pins (model `>=0.1.3`, data `>=0.8.0`) contradict shipped `>=0.1.5`/`>=0.9.0`. |
| CI-04 | Medium | `ci-recurrence-bench.yml:31` | Bench push-CI triggers on `[main]` only — no pre-PR CI on `feature/**`/`fix/**` (parity gap). |
| CI-05 | Medium | `.github/` (none) | No `dependabot.yml`/`renovate.json` — 3 published pkgs + SHA-pinned actions have no update bot. |
| CI-06 | Medium | `.github/workflows/` (none) | No CHANGELOG/`_version.py`-vs-tag drift lint — the DOC-05/CI-01 drift is exactly what it would catch. |
| TEST-03 | Medium | `bench/run_benchmark.py:53,260,327` | Bench orchestration (`run_dataset`/`_render_report`/`main`) untested; only leaf helpers covered. |
| DOC-06 | Medium | `notes/releases/` | 5 of 11 published tags lack an archived release-notes file (convention partially satisfied). |
| MODEL-02 | Low | `units/lmu_varstep.py:156` vs `:211` | `dt==0` raises in `rollout()` but is a held no-op in `rollout_batch()` — divergent contract (intentional, undocumented). |
| MODEL-03 | Low | all model `*.py` | Modules use docstrings, not the canonical Juniper file-header block (unenforced; consistent w/ siblings). |
| MODEL-04 | Low | `readouts.py:291` | `RFFReadout(n_features_out=0)` → `ZeroDivisionError` (no lower-bound validation). |
| APP-02 | Low | `settings.py:59,82` | Docstring overstates `juniper_data_api_key` env binding (shared var resolved via model-validator, not field alias). |
| APP-03 | Low | `app.py:115` | Module-level `app = build_app()` makes a malformed `METRICS_TRUSTED_IPS` a hard import-time crash. |
| APP-04 | Low | `routers/predict.py:44` | `seq_lengths` coerced with default dtype (float-from-JSON) unlike int64 training path; mitigated by 422. |
| CI-02 | Low | model `CHANGELOG.md:212` | Compare-link footer frozen at v0.1.0; 0.1.1–0.1.5 have no link targets. |
| CI-03 | Low | app & client `CHANGELOG.md` | No Keep-a-Changelog compare-link footers at all. |
| CI-07 | Low | `ci-recurrence-bench.yml` | Bench lane has no `required-checks` aggregator (not branch-protection-stable). |
| CI-08 | Low | `publish-*.yml` build job | Publish build omits the clean-venv wheel-install smoke CI runs (mitigated by TestPyPI verify). |
| CI-09 | Low | `bench/results/*.json` | Generated benchmark artifacts committed to git (can drift from the now-tested evaluator). |
| TEST-04 | Low | all `pyproject.toml` | `--strict-markers` active with no `markers` table — first custom marker will hard-error. |
| TEST-05 | Low | `tests/test_cli_train.py:75` | CLI happy-path asserts only `"Metrics:"` printed — doesn't prove `--ridge gcv`/`--readout rff` took effect. |
| TEST-06 | Low | `test_cli.py`, `test_data_adapter.py` | CLI-vs-env and multi-dataset-ref precedence untested. |
| TEST-07 | Low | client `test_client.py:114` | `test_context_manager_closes` never asserts `session.close()` was called. |
| TEST-08 | Low | client `test_errors.py` | Non-JSON error bodies + exception messages + 401/403 mapping unasserted. |
| CLIENT-04 | Low | `client.py:375` | `predict(params=...)`-only silently drops the ref → server 422 (correct but late). |
| OBS-05 | Low | `app.py:86` | Guarded import catches `ImportError` but a partial `[prometheus]` install could fail at scrape time. |
| DOC-07 | Low | model `CHANGELOG.md:212`; client/app | CHANGELOG link-reference footers incomplete/absent. |
| DOC-08 | Low | `juniper-recurrence/README.md:104` | Publishing example uses stale `v0.1.0` tag + a bare-tag-push (vs the cut-a-Release convention). |
| INFO-* | Info | various | dt-conditioning near d≲64 ceiling (design-acknowledged); 422-literal style; torch `>=2.10` security floor; off-repo `notes/`; client retry-set divergence (correct). |

**Counts:** 3 High · 14 Medium · ~18 Low · several Info. **0 Critical.**

---

## 4. Detailed findings (High & Medium)

### H1 — No application logging, and logging is never configured (OBS-01 / OBS-02)

The entire app emits logging from exactly one site (`app.py:40` `logger = logging.getLogger(__name__)`,
used for the observability-absent warning at `app.py:86`). Every router (`training/predict/crossval/
model/dataset/_common`), `data.py`, `state.py`, and `_readout.py` log **nothing** — no startup line, no
training start/end, no audit of 409 conflicts, 503 torch-gaps, or upstream juniper-data failures
(`training.py:52,78`). And nothing anywhere calls `basicConfig`/`dictConfig`/`uvicorn ... log_config`,
so `settings.log_level` (a `SettingsBase` field) is **read by nothing**. The ecosystem norm of
structured-JSON logging + the custom TRACE/VERBOSE level system is absent.

*Impact*: a "completed" service with no operational visibility — production training failures,
upstream-data errors, and conflict/capability rejections are invisible in logs.
*Recommendation*: configure logging from `settings.log_level` at startup (in `build_app`/`_serve`, and
pass `log_config`/`log_level` to `uvicorn.run`); adopt the shared `juniper-observability` structured-JSON
logging helper if available; add module loggers to routers + `data.py` and log training start/end (dataset
id, duration, final metrics) at INFO and upstream/torch/conflict failures at WARNING/ERROR before raising.

### H2 — torch MLP readout is uncovered and non-gating (TEST-01)

`_readout_mlp.py` is excluded from coverage (`model/pyproject.toml:85` `omit = [..., "*/_readout_mlp.py"]`)
and the only job that installs real torch (`ci-recurrence-model.yml:124` `test-torch`) is **explicitly
excluded from `required-checks`** ("deliberately NOT in required-checks", line 127). The base matrix
`importorskip("torch")`-skips every MLP test, and the app/bench MLP paths toggle on `find_spec`, so the
*actual torch fit path* through `LMURegressor` / the app / the bench never runs in any merge-gating lane.
Net: the shipped `readout="mlp"` HTTP/CLI/client feature (DP-3 P3) has **no blocking test** and
contributes **0 %** to the enforced 90 % coverage bar — it can regress and still go green.

*Recommendation*: promote `test-torch` into `required-checks` (accept the ~1–3 GB torch install on one
leg), **or** measure `_readout_mlp.py` coverage within that optional job and assert ≥90 there; at minimum
record the deliberate non-gating decision as a tracked, time-boxed risk.

### M1 — `NaN`/`Inf` in `dt` bypasses validation (MODEL-01)

Both timing guards are `if np.any(dt < 0)` (`lmu_varstep.py:211`, `data.py:95`). `NaN < 0` is `False`, so
a `NaN`/`Inf` timestamp passes; there is no `isfinite` check on `dt` or `X`. The NaN propagates silently
through `rollout_batch`, and through the linear readout it surfaces only as an opaque LAPACK
`LinAlgError` ("DLASCL parameter ... had an illegal value") — never a clear "dt contains NaN/Inf". No test
feeds non-finite input.
*Recommendation*: replace the guards with `if not np.all(np.isfinite(dt))` (and ideally validate `X`) in
both `rollout_batch` and `data.sequence_data_from_arrays`, with an explicit message; add a regression test.

### M2 — Documentation version drift across all narrative docs (DOC-01 / 02 / 03 / 04)

Authoritative versions (`_version.py` + tags) are **app 0.2.0 / model 0.1.5 / client 0.2.0**, but:
- **Root `AGENTS.md`** header (`:7-8`, 0.1.1 / 2026-06-21), sub-project table (`:22-24`), and Status
  footer (`:114`) all state 0.1.1 / 0.1.3 / 0.1.0.
- **Model README** (`:11,53-59`) describes a *linear-readout-only* package — no mention of the RFF/MLP/GCV
  spectrum the package now ships (the package's own PyPI landing page understates its core feature).
- **App README** (`:7,42-52`) is stale at 0.1.1 — omits the `readout` enum, `ridge=gcv`, `[torch]` extra,
  and the `/v1/metrics` endpoint (shipped 0.1.1).
- **Client AGENTS.md** (`:7`, 0.1.0) + README API table omit the 0.2.0 readout params.

Contrast: juniper-ml's `[recurrence]` extra already pins `>=0.2.0`, so the meta-package is current while
the repo's own docs are not. *Recommendation*: a single doc-currency sweep (versions + the readout surface
in all three READMEs).

### M3 — Confirmed factual errors in CHANGELOGs (DOC-05 / CI-01)

`juniper-recurrence/CHANGELOG.md:64` states `[bench]` pins `juniper-data>=0.8.0`, but
`pyproject.toml:81` pins `>=0.9.0,<0.10.0` (the `delay_product` generator needs 0.9.0). The same 0.2.0
"Changed" block (`:60`) states a model floor `>=0.1.3` vs the actual `>=0.1.5`. These are intermediate
increments collapsed into the 0.2.0 release but never updated to final pins — the PyPI landing page
understates its own dependency floors. *Recommendation*: correct both lines to `>=0.9.0` / `>=0.1.5`.

### Medium — remaining

- **TEST-02** warnings-as-errors (`filterwarnings = ["error", ...]`) is in the app pyproject only; add it
  to the model (numpy-only — near-empty ignore list) and client.
- **OBS-03** thread `git_sha`/`build_date` into `set_build_info(...)` (obs ≥0.4.0 supports it; matches the
  cross-repo build-provenance standard).
- **OBS-04** register train/predict counters + last-metric gauges via `register_or_reuse` from the
  training/crossval routers. *(Explicitly design-deferred — fast-follow, not a defect.)*
- **CI-04** broaden the bench push filter to match the package CIs (`feature/**`/`fix/**`/...).
- **CI-05** add `.github/dependabot.yml` (pip per-package + github-actions, weekly) — SHA-pinned actions
  will silently rot without it.
- **CI-06** add a `_version.py` == latest-tag == top-CHANGELOG-heading drift lint (juniper-ml has the
  `test_agents_md_version_drift.py` precedent); also a README/AGENTS version lint.
- **TEST-03** one smoke test invoking `run_dataset` on the smallest dataset (asserts the model-dict keys
  `evaluate_bands` indexes by string) to close the producer/consumer contract gap.
- **DOC-06** backfill the 5 missing `notes/releases/` files (app 0.1.0 notes exist in juniper-ml).

---

## 5. Design-vs-reality gap (intended design → shipped reality)

| Design intent | Reality at `9ef1b0b` | Status |
|---|---|---|
| P3-C / LMU + Approach-C closed-form variable-Δt, no ODE/autodiff | `VariableStepLMUMemory` + `LMURegressor` (model 0.1.5); passes model-core conformance | **Shipped** |
| Δt-native 3-D irregular-Δt NPZ ingestion (WS-1 contract) | `data.py`/`SequenceData` map X/y/dt/target_dt/mask/seq_lengths; validator mandatory | **Shipped** |
| Readout Rung 0/1 linear + GCV ridge | `LinearReadoutSpec`, `ridge="gcv"`; HTTP/CLI/client exposed | **Shipped** |
| Readout Rung 2a numpy RFF | `RFFReadout` (0.1.4); `readout="rff"` end-to-end; bench row | **Shipped** |
| Readout Rung 2b torch MLP (gated; "build only if 2a lift warrants") | `MLPReadout` behind `[torch]`; torch-less → 503 | **Shipped** (built under decision D5 as capability insurance, *over* the design's stop-lean) |
| Nonlinear capacity dataset `y=x(t−τ₁)·x(t−τ₂)` | `delay_product` (juniper-data 0.9.0); measured **+0.83 r²** RFF-vs-linear | **Shipped** |
| Equities-readout finding + follow-ups (r²≈−50 was a readout artifact) | stationary `regression_target` + regularized readout re-bench shipped | **Shipped** |
| HTTP/CLI surface (train/status/predict/model/dataset + fast-follow metrics/crossval) | all routes + `/v1/metrics` + `/v1/crossval` + CLI shipped | **Shipped** (exceeds WS-4b minimum; README lags — DOC-03) |
| First `juniper-service-core` consumer (`create_app` + `TrainingLifecycle`) | `app.py`/`events.py`/`settings.py` consume the framework; no reinvention | **Shipped** |
| HTTP client | full client v0.2.0 + readout forwarding + typed errors | **Shipped** (was "out of scope" at 0.1.0; later built) |
| Container image / Dockerfile | multi-stage slim (~77 MB, non-root) + docker smoke CI | **Shipped** |
| cascor 3-D ingestion gate (WS-6/H4) | not addressed here by design; cascor still caps `ndim>2` | **Deferred (by design, tracked)** |
| Distributed / async / WS-streaming training (WS-8/OQ-11) | synchronous in-process only | **Deferred (by design, tracked)** |
| canopy generalization (WS-5/H2) | not in this repo (client enables it) | **Deferred (downstream)** |
| Open questions OQ-1..19 | all resolved except OQ-11 (deferred WS-8) | **Mostly resolved** |
| Application logging / operational visibility | effectively absent (H1) | **Gap** |
| Docs track shipped reality | READMEs/AGENTS/CHANGELOGs lag 0.2.0/0.1.5 | **Drifted** (M2/M3) |

---

## 6. Strengths (what is genuinely excellent)

- **The LMU math is exactly correct and independently reproducible** — ZOH closed form, eigenbasis
  factorization, `expm1` small-z guard, removable-singularity handling; eigenvalues stable by construction;
  batched rollout matches the single-sequence oracle to ~1e-13.
- **Conformance is genuine, not nominal** — `LMURegressor(TrainableModel)` passes the model-core kit for
  linear, RFF, and torch-MLP readouts, with **bit-exact** save/load round-trips on all three.
- **The app is architecturally disciplined** — correctly delegates to `juniper-service-core`,
  async-clean (sync routes → threadpool, no event-loop blocking → ASYNC* lint passes), correct lock
  discipline (acquire-before-try, publish-pointer-last), bounded `EventSink` (`deque(maxlen=256)`).
- **Security posture is solid** — canonical middleware order, API-key auth + rate limiting, `/metrics`
  IP-gated + auth-exempt, 10 MiB body cap, `_FILE` secret indirection, **no `.env`-leak** (dedicated test).
- **Client mirrors the server 100 %** — every route has a method; paths/literals byte-match; conservative
  idempotent-only retry; guarded X-Request-ID propagation; typed exception hierarchy.
- **Metrics layer is production-grade** — `register_or_reuse` idempotency, `MetricsAuthMiddleware`,
  guarded optional imports in both app and client, graceful disabled/absent behavior.
- **CI/CD & publish are best-in-class** — OIDC trusted publishing, TestPyPI-first **no-prod-fallback**
  verify, fully path-decoupled tags, GitHub-Release-required gate, 3.12/3.13/3.14 matrix,
  `--cov-fail-under=90`, concurrency groups, clean-venv wheel-install smoke, weekly `pip-audit`,
  `pr-base-branch-guard`. The prior "zero pre-commit" CRIT is fully closed.
- **Test quality is high** — closed-form-correctness, determinism, eigenvalue-stability,
  grid-invariance with a fixed-Δt **negative control**, Δt-shuffle degradation guardrail; RFF
  capacity-vs-linear assertions; branch-exhaustive route error mapping.

---

## 7. Prioritized remediation roadmap (PR-sized)

No P0 (no Critical findings). Suggested follow-up PRs, each independently shippable off `main`:

**P1 — High (operational completeness):**
1. **Wire application logging** — configure from `settings.log_level` (+ uvicorn `log_config`), add module
   loggers to routers/`data.py`, log training lifecycle + upstream/torch/conflict failures. *(OBS-01/02)*
2. **Gate the torch-MLP readout** — promote `test-torch` to `required-checks` or add coverage there +
   track the decision. *(TEST-01)*

**P2 — Medium (correctness, currency, hardening):**
3. **Model input hardening** — `isfinite` guards on `dt`/`X` + regression test; `RFFReadout` lower-bound
   validation. *(MODEL-01, MODEL-04)*
4. **Doc-currency sweep** — AGENTS.md (root + client) + 3 READMEs to 0.2.0/0.1.5/0.2.0; surface the readout
   spectrum (model README), `/v1/metrics` + `readout` (app README), readout params (client README); fix
   CHANGELOG pins. *(DOC-01..05, CI-01, DOC-08)*
5. **Drift guards** — `_version.py`/tag/CHANGELOG drift lint + README/AGENTS version lint; `dependabot.yml`.
   *(CI-05, CI-06)*
6. **warnings-as-errors** in model + client pyproject. *(TEST-02)*
7. **Build-info provenance** — `git_sha`/`build_date` into `set_build_info`. *(OBS-03)*
8. **Bench CI parity** — broaden push trigger + add `required-checks` aggregator. *(CI-04, CI-07)*

**P3 — Low / deferred (hygiene & optional):**
9. CHANGELOG link footers; markers table; CLI/precedence/context-manager/non-JSON-error tests;
   bench orchestration smoke; release-notes backfill; domain metrics instrumentation *(design fast-follow)*;
   gitignore (or CI-regenerate) `bench/results/`. *(CI-02/03/09, TEST-03..08, OBS-04, DOC-06/07)*

---

## 8. Could-not-verify / limitations

- **Coverage percentages and pass/fail** were **not re-executed** (no on-host env carrying the app's deps;
  heavy installs incl. torch avoided). The ~98 %/98 %/94 % figures are pyproject-comment claims.
- **Whether the torch path passes under real torch** — `test-torch` is statically well-formed; the
  *gating gap* (TEST-01) holds regardless.
- **GitHub environment dual-gate** (`pypi` wait-timer + manual reviewer), **trusted-publisher
  registration**, and **branch-protection required-check membership** are server-side, not in the checkout.
- **Live CI run / 3.12·3.13·3.14 matrix parity** — a single static checkout cannot certify runtime green.
- **cascor `ndim>2` cap at current cascor HEAD** — cited from the OQ-4 audit; juniper-cascor was outside
  read-scope (reported as suspected-current).

---

*Audit performed via 7 parallel evidence-cited sub-audits grounded against the juniper-ml design-of-record
corpus + the 2026-06-21 prior audit; five highest-severity findings independently re-verified against
source at `9ef1b0b`.*
