# Juniper-Recurrence — State Evaluation & Forward Roadmap

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; build lands in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT — state evaluation + roadmap; pending Paul's review)
**Last Updated**: 2026-06-17

---

> **What this is.** A ground-truth evaluation of the juniper-recurrence effort (the Δt-native LMU
> recurrence model + its FastAPI/CLI application) as it actually stands in source, git, and PyPI on
> 2026-06-17 — reconciled against the ratified design/plan corpus — followed by a prioritized,
> grouped, dependency-ordered roadmap of the outstanding work. Where more than one credible path
> exists, the roadmap presents **design/dev approach options** with strengths, weaknesses, risks,
> and guardrails rather than a single prescribed answer. Every factual claim here was produced by
> five independent, primary-source-grounded analysis sub-agents and re-validated by a second,
> independent validation pass (see [§11](#11-method-validation--evidence-base) and Appendix A).

> **Status update (2026-06-17, same session).** This document was landed as
> [juniper-ml#438](https://github.com/pcalnon/juniper-ml/pull/438). The Group-A recovery it
> recommends — PR [juniper-recurrence#9](https://github.com/pcalnon/juniper-recurrence/pull/9),
> `feature/ws4b-app-publish-docs → main`, opened independently by a concurrent session — is **green
> and `MERGEABLE` / `CLEAN`** (20 files / +1,362/-24; all CI checks pass on Python 3.12 / 3.13 /
> 3.14). This **retires discrepancy [D-2](#4-validated-discrepancies-and-their-consequences)** (the
> unverified first-CI-run risk): **A1 and A2 are effectively complete**, awaiting only Paul's merge
> signal. Publishing the app (A4) remains Paul-gated.

---

## Table of contents

- [1. Scope, method, and the naming map](#1-scope-method-and-the-naming-map)
- [2. Executive summary — the seven headline findings](#2-executive-summary--the-seven-headline-findings)
- [3. Current-state evaluation: plan-claimed vs code-verified](#3-current-state-evaluation-plan-claimed-vs-code-verified)
- [4. Validated discrepancies and their consequences](#4-validated-discrepancies-and-their-consequences)
- [5. Outstanding-work inventory (grouped)](#5-outstanding-work-inventory-grouped)
- [6. Roadmap: ordering, grouping, prioritization](#6-roadmap-ordering-grouping-prioritization)
- [7. Design / dev approach options](#7-design--dev-approach-options)
- [8. Consolidated risks and guardrails](#8-consolidated-risks-and-guardrails)
- [9. Recommendations and immediate next actions](#9-recommendations-and-immediate-next-actions)
- [10. Cross-references](#10-cross-references)
- [11. Method, validation, & evidence base](#11-method-validation--evidence-base)
- [Appendix A — Verified status-claim diff ledger](#appendix-a--verified-status-claim-diff-ledger)
- [Appendix B — Git/PyPI forensic anchors](#appendix-b--gitpypi-forensic-anchors)

---

## 1. Scope, method, and the naming map

### 1.1 Scope

This document centers on the **recurrence model** (`juniper-recurrence-model`) and the **recurrence
application** (`juniper-recurrence`) — workstreams WS-4 and WS-4b — as the spine. The shared
substrate they sit on (`juniper-model-core` / WS-3, `juniper-service-core` / WS-2, the WS-1 data
foundation) is evaluated as a **dependency and gating layer** (verified, not re-planned). The larger
ecosystem workstreams (WS-5 canopy, WS-6 cascor adoption, WS-8 distributed worker) and the
research-tier ceiling-break work are treated as **future options**, not near-term build targets.

If Paul wants the altitude shifted (e.g., a full WS-5/WS-6 design, or a deep cascor-3D-ingestion
build plan), that is a natural follow-on and is flagged at the relevant points below.

### 1.2 Method

Five independent sub-agents each audited one slice from primary sources: (1) the architecture /
decision doc corpus; (2) the build-plan / status-claim doc corpus; (3) the model package source +
tests (tests were actually executed); (4) the app source + git/PR forensics; (5) the
dependency / publish / integration substrate (PyPI checked live). Their findings cross-corroborate.
A second, independent validation pass then re-checked every load-bearing claim in this document
against the repos. See [§11](#11-method-validation--evidence-base).

### 1.3 The naming map (resolving "juniper-recurrence-core / juniper-recurrence")

There is **no package literally named `juniper-recurrence-core`**. The prompt's "core / application"
split maps onto three real artifacts plus one shared contract:

| Informal name | Real artifact | Lives in | Role |
|---|---|---|---|
| "the contract / core" | `juniper-model-core` | `juniper-ml/juniper-model-core/` (subdir pkg) | Shared `TrainableModel`/`GrowableModel` ABCs + conformance kit the model plugs into (WS-3) |
| "the model / core model" | `juniper-recurrence-model` | `juniper-recurrence/juniper-recurrence-model/` (subdir pkg) | The Δt-native LMU regressor implementing `TrainableModel` (WS-4) |
| "the application" | `juniper-recurrence` | `juniper-recurrence/juniper-recurrence/` (subdir pkg) | FastAPI + CLI service wrapping the model on `juniper-service-core` (WS-4b) |
| "the service framework" | `juniper-service-core` | `juniper-ml/juniper-service-core/` (subdir pkg) | Generic FastAPI/lifecycle/security framework the app builds on (WS-2) |

The `juniper-recurrence` **git repository** is the umbrella holding *two* published distributions:
the model (`juniper-recurrence-model`) and the app (`juniper-recurrence`). The `*-core` shared
packages are juniper-ml subdirectories per the ratified placement convention (D4).

### 1.4 ID conventions

Risk IDs (`RK-*`), Δt-risk IDs (`R-Δt-*`), open-question IDs (`OQ-*`), and decision IDs (`D1`–`D10`,
`D-WS4-*`, `D-WS4b-*`, `D-CV-*`) used throughout are carried verbatim from the linked design and
build plans ([§10](#10-cross-references)); they are not redefined here.

---

## 2. Executive summary — the seven headline findings

1. **The model (WS-4) is genuinely done.** `juniper-recurrence-model 0.1.0` implements the full
   `TrainableModel` contract, passes **53/53 tests in 0.69 s** (incl. the 10-check model-core
   conformance suite), has **no stale TODOs, stubs, or contract divergences**, and is **live on PyPI**
   (uploaded 2026-06-16). Every test the WS-4 plan's matrix required exists, plus ~25 bonus tests.

2. **The app (WS-4b) is code-complete but stranded off `main`.** The full application — 23 `.py`
   files (15 package modules + 8 test modules) plus its publish workflow — exists and conforms fully
   to the WS-4b plan, but lives on the `feature/ws4b-app-routes` branch. `main` carries the
   **skeleton only**. Cause: PR #7 (routes) merged into the *skeleton branch* and PR #8 (publish/docs)
   merged into the *routes branch*; neither was retargeted to `main`. Remediation is **one
   zero-conflict merge PR** (20 files, +1,362/-24; `git merge-tree` shows no conflicts).

3. **The full app has never executed in CI.** Because PR #7/#8 targeted non-`main` bases,
   `ci-recurrence-app.yml` (filtered to `branches: [main]`) never fired on the routes/data/state/
   schema/event code. The remediation PR will be the **first CI run** of the real suite — it could
   surface latent failures even though the code reads as self-consistent and well-tested.

4. **Publish-first is no longer the bottleneck.** Live PyPI checks confirm `juniper-model-core 0.1.0`,
   `juniper-service-core 0.1.0`, and `juniper-recurrence-model 0.1.0` are **all published**. The
   plan-era gates (`0.1.0a0 → 0.1.0` bump, service-core publish) are **all cleared**. Only the app
   itself remains unpublished (404, no tag) — three of the four packages in the publish chain
   (model-core, service-core, recurrence-model) are live; only the app is not.

5. **Multiple design-doc status claims are now stale.** The WS-4b plan's §0 table ("service-core
   404 / not in extras", "recurrence-model `0.1.0a0`", "app greenfield"), the model-core CHANGELOG
   ("not yet published"), the recurrence-model `egg-info` (`0.1.0a0`), and the MEMORY note
   ("data-client 0.4.1 lacks `validate_npz_contract`") are each contradicted by verified reality.
   These are harmless to runtime but actively misleading to a reader.

6. **The substrate is wired and verified.** `juniper-service-core` and `juniper-model-core` are both
   in juniper-ml `[tools]`/`[all]` with the extras lint (`test_pyproject_extras.py`) in lockstep;
   `juniper-data-client 0.4.1` exposes the full `validate_npz_contract` 3-D sequence validator; the
   service-core "as-built is simpler than the design" reconciliation (no auto-middleware, concrete
   synchronous `TrainingLifecycle`, no dual-mode CLI helper) is confirmed exactly as the WS-4b plan
   described.

7. **The forward work splits cleanly into a short, mechanical critical path and a long, optional
   research frontier.** Landing + publishing the app is days of low-risk, mostly Paul-gated work. The
   `crossval` (model-core 0.2.0), torch-readout, cascor-3D recurrence, and ceiling-break tracks are
   independent, individually deferrable, and each carry genuine design choices (see [§7](#7-design--dev-approach-options)).

---

## 3. Current-state evaluation: plan-claimed vs code-verified

### 3.1 Workstream status matrix (verified 2026-06-17)

| WS | Item | Plan-claimed (as of doc date) | Verified reality (2026-06-17) | Verdict |
|---|---|---|---|---|
| WS-0 | Model pick P3-C / LMU / Approach-C | RATIFIED (#411, 2026-06-14) | Ratification commit present; design corpus consistent | ✅ Matches |
| WS-1 | 3-D NPZ + Δt + temporal split + `equities_seq` | SHIPPED (data #169-171 + data-client #87) | `data-client 0.4.1` on PyPI exposes full `validate_npz_contract` (tabular/sequence) | ✅ Matches (exceeds — see §4) |
| WS-2 | `juniper-service-core` framework | MERGED to juniper-ml main; **NOT on PyPI**; **NOT in extras** | **On PyPI 0.1.0** (2026-06-16); **in `[tools]`/`[all]`**; lint in lockstep | ⚠️ Plan stale — further along |
| WS-3 | `juniper-model-core` contract + kit | SHIPPED (#416/#418); PyPI 0.1.0; in `[tools]`/`[all]` | On PyPI 0.1.0 (2026-06-14); 66 tests / 97% cov; CHANGELOG says "not yet published" | ✅ Matches (CHANGELOG stale) |
| WS-4 | `LMURegressor` model | SHIPPED to recurrence main @ `18815b7`; dist `0.1.0a0`; NOT on PyPI | **`0.1.0` on PyPI** (2026-06-16); **53/53 tests pass**; full conformance | ⚠️ Plan stale — DONE |
| WS-4b | FastAPI/CLI app | "404 / greenfield" | **Code-complete on `feature/ws4b-app-routes`**; skeleton-only on `main`; **never CI-tested**; not on PyPI | ⚠️ Plan stale — built but stranded |
| — | `crossval` (model-core 0.2.0) | RATIFIED design 2026-06-16 (D-CV-1…5) | **Design-only; zero code** anywhere; targets 0.2.0 + `[crossval]` extra | ✅ Matches (unbuilt by design) |
| WS-5 | canopy generalization | DEFERRED (after WS-4) | Not started | ✅ Matches |
| WS-6 | cascor refactor onto shared pkgs | DEFERRED (trigger-gated) | Not started; cascor still 2-D-only at its ingestion boundary | ✅ Matches |
| WS-7 | juniper-ml `[servers]` extra for the app | DEFERRED (after app on PyPI) | App not in `[servers]`/`[all]` (correctly) | ✅ Matches |
| WS-8 | distributed recurrence worker | DEFERRED (trigger-gated) | Not started | ✅ Matches |

### 3.2 Model package — contract & test conformance (WS-4, verified by execution)

- **Contract**: every `TrainableModel` member the WS-4 plan §5 mapped is present and matches —
  `task_type="regression"`; `fit(X, y, *, X_val, y_val, on_event, **kw)` reading `dt`/`target_dt`/
  `readout_mask`/`seq_lengths` and closed-form `lstsq` of `[M | target_dt | 1] → y`, emitting
  `training_start → epoch_end(0) → training_end`; `predict` **widened LSP-safe** with optional
  `dt`/`target_dt`/… and a uniform-`dt` fallback, never `argmax`; `metrics()` exactly
  `{mse, rmse, mae, r2, loss}`; `describe_topology()` with `model_type="lmu"`, a `frozen` memory
  node and a `recurrent=True` self-edge; a lossless `LMUSerializer`.
- **Tests**: 53 pass / 0 fail / 0 skip (Python 3.13, numpy 2.4.4). The plan's full §7 matrix is
  covered — grid-invariance, **batched-rollout parity**, conformance suite (`tiny_regression_3d`),
  fit/predict known-answer, **R-Δt-3 shuffle-`dt` guardrail**, determinism, overfit-tiny, and the
  **§9.1a fixed-step negative control** — plus the stale `TODO §9.1a` is gone.
- **Deferred-by-design** (not gaps): dense many-to-many readout (guarded `NotImplementedError`),
  memory-advance by `target_dt` (D-WS4-2), trained projection / nonlinear readout (the torch
  "increment 1(b)"), and `dt`-bucket caching (a documented perf optimization).

### 3.3 App package — plan conformance (WS-4b, verified on `feature/ws4b-app-routes`)

- **File layout (§5), endpoint surface (§6), settings/secrets (§7), data path (§8), CLI dual-mode
  (§11), and test matrix (§12) all conform** — `/v1/train` (synchronous, D-WS4b-2), `/v1/training/
  status`, `/v1/predict` (409 before train), `/v1/model`, `/v1/dataset`, health auto-mounted and
  exempt; `env_prefix="JUNIPER_RECURRENCE_"`, port 8210, `_FILE` secret indirection, no `.env` leak;
  RK-6 enforced (no `argmax`/`accuracy` in routers, asserted by a test).
- **`publish-recurrence-app.yml`** uses the hardened `--no-deps` TestPyPI verify (no
  `--extra-index-url` fallback). **`publish-recurrence-model.yml` was already aligned** off
  `--extra-index-url` in PR #4 — the WS-4b §15 concern is resolved.
- **`validate_npz_contract` guard** in the app's `data.py` is defensive (optional import → `None` on
  `ImportError`); since `data-client 0.4.1` actually ships the validator, the guard is
  belt-and-suspenders, not load-bearing.

---

## 4. Validated discrepancies and their consequences

| # | Discrepancy | Evidence | Consequence | Severity |
|---|---|---|---|---|
| D-1 | **App routes/docs stranded off `main`** — PR #7→skeleton branch, PR #8→routes branch; only PR #6 (skeleton) reached `main` | `gh pr view` base refs; `git diff --stat origin/main origin/feature/ws4b-app-routes` = 20 files / +1,362/-24 | Installing/cloning `main` yields a non-functional skeleton; the working app is inert until a routes→main PR lands | **High** (blocks everything app-side) |
| D-2 | **Full app never CI-tested** — `ci-recurrence-app.yml` filters `branches:[main]`; PR #7/#8 bases were non-main | `gh pr checks 7/8` → "no checks reported"; only PR #6 skeleton runs exist | First green-on-`main` is unverified; remediation PR is the first real CI exercise | **High** (latent-failure risk) |
| D-3 | **Publish-first claims stale** — service-core/recurrence-model shown as 404 in plans | Live `curl pypi.org/pypi/<pkg>/json`: both 200, uploaded 2026-06-16 | The roadmap's critical path is *shorter* than the plans imply; app publish is unblocked | Low (good news) |
| D-4 | **`0.1.0a0` alpha trap already resolved** — plan lists it as a gate | `_version.py = 0.1.0`; tag `juniper-recurrence-model-v0.1.0`; PyPI 0.1.0; only a stale `egg-info` still says `0.1.0a0` | A planned gate is already cleared; rebuild the stale egg-info to avoid confusion | Low |
| D-5 | **`validate_npz_contract` present** — MEMORY note says absent in 0.4.1 | `juniper_data_client/contract.py:41`; exported in `__all__` | The app guard is unnecessary defensiveness; the pin can be tightened to make validation mandatory | Low |
| D-6 | **`TrainingLifecycleBase` wording** — WS-4b §2 says "there is no `TrainingLifecycleBase`" | The ABC *does* exist in `model-core/lifecycle.py`; service-core ships the concrete `TrainingLifecycle` subclass | Semantic only — the app correctly needs no subclass; future readers should not infer the base is absent | Low |
| D-7 | **`predict(**kw)` ABC asymmetry (D3)** — model-core ABC has `**kw` on `fit` but `predict(self, X)` is 2-arg | `model-core/interfaces.py`; recurrence model widens `predict` covariantly | A generic caller cannot pass `dt` through the typed ABC; harmless today (sequence models widen on their side); ABC doc deferred to 0.2.0 | Low |
| D-8 | **Doc/CHANGELOG staleness** — model-core CHANGELOG "not yet published"; WS-4/WS-4b plans not marked "executed" | CHANGELOG text; plan §0 tables | Reader confusion; the plans read as future tense for already-done work | Low (hygiene) |

The two High-severity items (D-1, D-2) are the same physical fact viewed two ways and are resolved
by the same action: **land the routes branch on `main` via a normal PR and watch its checks**.

---

## 5. Outstanding-work inventory (grouped)

Work items are grouped by theme; each carries an ID used in the roadmap ([§6](#6-roadmap-ordering-grouping-prioritization)) and options ([§7](#7-design--dev-approach-options)). "Paul-gated" marks
actions that require Paul's explicit signal or approval (merge signals, PyPI deploy approvals) per
standing rules — this document plans them but does **not** execute them.

### Group A — Ship & stabilize the app (critical path)

- **A1 — Land the stranded app on `main`.** One PR, `feature/ws4b-app-routes → main` (zero-conflict).
  Paul-gated (merge signal). See option set [§7.1](#71-option-set-a--consolidating-the-stranded-app-onto-main).
- **A2 — Verify CI green on the full app.** First real run of the app's full test suite (8 test
  modules never yet CI-exercised); triage any latent failures (RK-10). Fix-forward in the same PR or
  a fast-follow.
- **A3 — Pull local `main`** in the `juniper-recurrence` clone (2 commits behind origin) so on-host
  work sees the app. Mechanical.
- **A4 — Publish the app.** Pending-publisher registration (Paul) + tag `juniper-recurrence-v0.1.0` +
  `pypi` dual-gate approval (Paul). Paul-gated.
- **A5 — Branch & doc hygiene.** After A1: delete `feature/ws4b-app-{skeleton,routes,publish-docs}`,
  `git worktree prune`; rebuild the stale `0.1.0a0` egg-info; mark WS-4/WS-4b plans "executed";
  fix the model-core CHANGELOG "not yet published" line.

### Group B — Ecosystem wiring (follows app publish)

- **B1 — WS-7 extras.** Add `juniper-recurrence` to juniper-ml `[servers]`/`[all]` and update
  `test_pyproject_extras.py` in the **same PR** (RK-11). Only after A4.
- **B2 — juniper-deploy compose entry.** Host `8211 → ctr 8210`; reuse the worker's CPU-lock docker
  pattern (not cascor's CUDA image). Resolves OQ-15/OQ-18.

### Group C — model-core 0.2.0 increment (independent track)

- **C1 — Build the `crossval` layer.** `juniper_model_core.crossval` (`metrics`/`splits`/`executor`)
  behind a `[crossval]` extra; factory-based (`Callable[[int], TrainableModel]`), external scoring,
  walk-forward folds with embargo; serial v1. Self-contained PR. The gated consumer opt-ins — a
  recurrence-app `/v1/crossval` endpoint and a recurrence-side `LMURegressor` cross-validation test —
  follow publish (C3). See [§7.2](#72-option-set-b--model-core-020-packaging).
- **C2 — `predict(**kw)` ABC documentation (D3).** Rides the 0.2.0 release (C3) as an optional
  additive bundle — Paul's call.
- **C3 — Publish model-core 0.2.0**, then widen consumer pins where a consumer needs it.
- **C4 — Populate `test_model_core_drift.py`.** Create/activate the consumer-drift lint clone when a
  consumer first pins `juniper-model-core>=0.2.0` (nothing to guard until then; model-core interface
  §10 / §8). Lands with the pin-widen PR (RK-11 lockstep).
- **C5 — Deferred contract methods.** Optional on-demand `evaluate(X, y)` (D9) and an external
  held-out `score()` on `TrainableModel` are version-tagged for 0.2.x / 0.3, not 0.2.0 (interface §3;
  crossval §1/§8).

### Group D — model increments (deferred; torch frontier)

- **D1 — `target_dt` memory-advance** (advance the LMU memory by the forecast horizon instead of
  only concatenating `target_dt` as a readout column).
- **D2 — Dense many-to-many readout** (currently a guarded `NotImplementedError`).
- **D3 — Trained projection read-in / nonlinear readout** — the "increment 1(b)" where torch enters.
  See [§7.3](#73-option-set-c--the-next-model-increment).
- **D4 — `dt`-bucket caching** perf optimization (documented as future in the rollout).

### Group E — recurrence-in-cascor & bigger workstreams (gated)

- **E1 — cascor 3-D recurrent ingestion (Path B).** Make cascor consume the 3-D/`dt` contract via a
  recurrent block fronting the 2-D cascade head — the genuine "make cascor recurrent" work. The
  cheap flatten (Path A) is explicitly a trap (it *is* the rejected delay-line and discards `dt`).
  The cascor/worker `ndim>2` ingestion cap is **OQ-11**. See [§7.4](#74-option-set-d--cascor-recurrence-integration-path-b).
- **E2 — WS-5 canopy generalization** (model-agnostic UI + recurrence backend).
- **E3 — WS-6 cascor refactor onto the shared packages** (trigger: interfaces proven + cascor
  conformance green).
- **E4 — WS-8 distributed recurrence worker** (trigger: training cost justifies distribution). The
  heaviest single integration (detailed-design Part 8): a 3-D `(B, T, F)` + `seq_lengths` +
  `readout_mask` worker payload, an immutable-time / shardable-batch ordering contract, and the
  recurrent forward **and gradient** deployed worker-side — transport is already N-D-ready, the math
  is not (OQ-11).

### Group F — research frontier (trigger-gated)

- **F1 — Ceiling-break track.** Only if a *verified non-star-free* (parity / mod-n / group-counting)
  dataset appears. Candidates: P7 (Grazzi negative-eigenvalue block, the cascor-native breaker), P2
  (group-implementing units — needs a correlation-compatible training recipe, the gating research
  deliverable), or NEAT (breaks the ceiling but discards the cascor engine). The delay-line (P4),
  recurrent-output (P5), and NARX-MLP (P6) variants were evaluated and **rejected** as deployment
  targets (P6 retained only as a representability reference) — do not re-propose without a new trigger.
- **F2 — P1 self-recurrent RCC** as the cheap genuine-hidden-recurrence increment (kept alongside
  P3-C; inherits the star-free ceiling).
- **F3 — RTRL gradient** (vs BPTT-over-window) for unbounded/online sequences.
- **F4 — Synthetic regression generators** (`multi_sine` / `mackey_glass` / `ar_p`) + walk-forward
  split (WS-1 follow-ups; currently unbuilt).
- **F5 — Grown-cascade LMU candidate (open research).** The `GrowableModel` form of the LMU — growing
  a heterogeneous candidate pool of state-carrying memory blocks under a correlation-compatible
  training recipe — vs the shipped fixed-order `TrainableModel`. The homogeneous-pool growability gap
  (detailed-design Part 8 / §4.2; WS-4 §10; OQ-20). Distinct from F1 (ceiling) and D3 (torch readout).

### Group G — observability / ops (fast-follow)

- **G1 — `/v1/metrics`** Prometheus surface + `MetricsAuthMiddleware` (the `[observability]` extra is
  already declared in the app's pyproject). Note the app is `workers=1` / in-process for v1;
  persistence and horizontal scale-out are deferred (WS-4b §4).

---

## 6. Roadmap: ordering, grouping, prioritization

### 6.1 Dependency graph

```text
A1 (land app) ──► A2 (CI green) ──► A4 (publish app) ──► B1 (WS-7 extras) ──► B2 (deploy)
   │                                      ▲
   └─► A3 (pull local main)               │
   └─► A5 (branch/doc hygiene) ───────────┘ (after A1)

C1 (crossval) ──► C3 (publish 0.2.0) ──► (consumers opt in)   [independent of A/B]
C2 (predict **kw doc) ──┘ (optional bundle into 0.2.0)

D1/D2/D3/D4  — independent; gated on product need (torch for D3)
E1 (cascor 3-D) — large; gated; unblocks E3/E4 conceptually
E2/E3/E4 — large workstreams; trigger-gated
F1/F2/F3/F4 — research; dataset/cost-trigger-gated
G1 — fast-follow on A4
```

The only hard ordering is **A1 → A2 → A4 → B1 → B2**. Everything else (C, D, E, F, G) is parallelizable
and independently deferrable.

### 6.2 Phased sequence

- **P0 — Land & verify (now, ~1 day, mostly mechanical + Paul merge signal).** A1, A2, A3. Outcome:
  `main` holds the working app and CI is green on the real suite. This is the single highest-value
  action and retires both High-severity discrepancies.
- **P1 — Publish & wire (days, Paul-gated).** A4 → B1 → B2; A5 hygiene folded in. Outcome:
  `pip install juniper-recurrence` works; `juniper-ml[servers]` includes it; deployable.
- **P2 — model-core 0.2.0 / crossval (independent, ~1–2 days build).** C1 (+ optional C2) → C3.
  Outcome: cross-validation / walk-forward available to any `TrainableModel`; unlocks a future
  `/v1/crossval` app endpoint and a recurrence-side CV test (C1's gated opt-ins; C4/C5 follow).
- **P3 — Model capability increments (product-driven).** D1 → D2 → D3 (D3 introduces torch; gate it
  behind a real need). G1 observability can land anytime after P1.
- **P4 — Recurrence-in-cascor & ecosystem (large, gated).** E1 (cascor 3-D recurrence) is the
  flagship; E2/E3/E4 follow their triggers.
- **P5 — Research frontier (trigger-gated).** F1–F4; only F4 (synthetic generators) is build-ready
  today and only if needed for evaluation.

### 6.3 Priority / effort / risk table

| ID | Priority | Effort | Risk | Blocking? | Gate |
|---|---|---|---|---|---|
| A1 | P0 | XS | Low (zero-conflict) | Yes — blocks all app work | Paul merge signal |
| A2 | P0 | S | Med (first CI run) | Yes | via the A1 PR |
| A3 | P0 | XS | None | No | — |
| A4 | P1 | S | Low | Yes — blocks B1 | Paul pending-publisher + dual-gate |
| A5 | P1 | S | None | No | after A1 |
| B1 | P1 | S | Low (RK-11 lockstep) | No | after A4 |
| B2 | P1 | M | Low | No | after A4 |
| C1 | P2 | M | Low | No | — |
| C2 | P2 | XS | Low | No | Paul (bundle?) |
| C3 | P2 | S | Low | No | Paul pending-publisher |
| D1 | P3 | S | Low | No | product need |
| D2 | P3 | M | Med | No | product need |
| D3 | P3 | L | Med (torch blast radius) | No | product need + env |
| E1 | P4 | XL | High (algorithmic core) | No | trigger |
| E2/E3/E4 | P4 | L–XL | Med–High | No | triggers |
| F1 | P5 | XL | High (open research) | No | non-star-free dataset |
| F2/F3/F4 | P5 | S–L | Low–Med | No | need/cost |
| G1 | P1 | S | Low | No | after A1 (fast-follow) |

---

## 7. Design / dev approach options

Each option set below gives concrete alternatives with strengths, weaknesses, risks, and guardrails,
then a recommendation. The recommendation is a default, not a mandate.

### 7.1 Option set A — consolidating the stranded app onto `main`

The full app is on `feature/ws4b-app-routes` (identical tree to `feature/ws4b-app-publish-docs`);
`main` has the skeleton. How to bring the remaining 20 files to `main`?

- **A-opt-1 — Single merge PR `feature/ws4b-app-routes → main` (recommended).**
  - *Strengths*: preserves the real commit history of PR #7/#8; `git merge-tree` confirms
    zero conflicts; triggers `ci-recurrence-app.yml` (path + branch match) so the full suite finally
    runs; smallest human effort.
  - *Weaknesses*: the PR's "merged-into-feature-branch" lineage is slightly unusual to read.
  - *Risks*: first-ever CI run may fail (D-2) — but that is a risk of *any* option and is exactly
    what we want surfaced before publish.
  - *Guardrails*: open as a normal PR (not a direct push); require green checks before merge; Paul's
    explicit merge signal; `gh pr view` MERGED confirmation before branch cleanup.

- **A-opt-2 — Fresh squashed branch off `main`.** Re-create the app as one clean commit on a new
  branch, PR to `main`.
  - *Strengths*: linear, easy-to-read history; drops the odd stacked lineage.
  - *Weaknesses*: discards the PR #7/#8 commit granularity; manual; risk of transcription error vs
    the verified tree.
  - *Risks*: human error reproducing 1,362 lines; loses the audit trail.
  - *Guardrails*: derive the branch *from* `feature/ws4b-app-routes` (e.g. `git switch -c … routes`),
    not by hand; diff the resulting tree against `routes` (must be identical) before PR.

- **A-opt-3 — Cherry-pick the PR #7/#8 commits onto `main`.**
  - *Strengths*: keeps individual commits; linear.
  - *Weaknesses*: most fiddly; merge commits complicate the pick set.
  - *Risks*: easy to miss a commit; re-introduces the "did everything land?" question this whole
    audit had to answer.
  - *Guardrails*: verify final tree hash equals `routes`' tree before opening the PR.

**Recommendation: A-opt-1.** Lowest effort, verified zero-conflict, and it forces the missing CI
exercise. If the unusual lineage bothers Paul, A-opt-2 *derived from* the routes branch (never by
hand) is the clean-history fallback. In all cases, gate on green CI + Paul's merge signal, and verify
the post-merge tree equals `feature/ws4b-app-routes`.

### 7.2 Option set B — model-core 0.2.0 packaging

The `crossval` layer (C1) and the `predict(**kw)` ABC documentation (C2) both target model-core
0.2.0. How to package the release?

- **B-opt-1 — Bundle `crossval` + `predict(**kw)` doc in one 0.2.0 (recommended).**
  - *Strengths*: one minor bump, one publish, one consumer-pin-widen event; the `predict(**kw)` doc
    is tiny and additive; fewer publish-first cycles.
  - *Weaknesses*: couples a doc-only change to a feature; a `crossval` slip delays the ABC doc.
  - *Risks*: low; both are additive and backward-compatible.
  - *Guardrails*: keep them in separate PRs *into* the 0.2.0 line; the ABC `**kw` must remain
    optional/keyword-only (no positional break); dogfood `crossval` against `ReferenceLinearModel`
    in-repo so model-core stays dependency-clean.

- **B-opt-2 — `crossval` only in 0.2.0; defer the ABC doc.**
  - *Strengths*: keeps the feature release focused.
  - *Weaknesses*: leaves the D3 asymmetry undocumented longer; a second release later for the doc.
  - *Risks*: low; the asymmetry is currently invisible to all real callers.
  - *Guardrails*: track the ABC doc as an explicit 0.3.0 (or later 0.2.x) item.

- **B-opt-3 — Defer `crossval` entirely until a consumer needs it (YAGNI).**
  - *Strengths*: zero speculative surface; the existing `>=0.1.0,<0.2.0` pins keep resolving.
  - *Weaknesses*: walk-forward CV is a near-certain need for the equities regression evaluation; a
    later scramble.
  - *Risks*: low now, medium later (a rushed build under evaluation pressure).
  - *Guardrails*: only choose this if the evaluation roadmap genuinely won't need folds soon.

**Recommendation: B-opt-1.** The `crossval` layer is the natural next substrate increment (the
equities forecast story wants walk-forward folds), and folding the trivial ABC doc in avoids an
extra publish cycle. Build `crossval` against the in-repo reference model to preserve model-core's
zero-runtime-dependency import contract.

### 7.3 Option set C — the next model increment

Once the app ships, which model capability comes next (Group D)? These are not mutually exclusive,
but ordering them sets the torch-introduction point.

- **C-opt-1 — `target_dt` memory-advance first (recommended).**
  - *Strengths*: stays numpy-only (no torch); directly improves irregular-horizon forecasting (the
    Approach-C thesis); small, well-scoped; testable with the existing shuffle-`dt` style guardrails.
  - *Weaknesses*: incremental accuracy gain only; not a new capability class.
  - *Risks*: low; pure extension of the existing closed-form path.
  - *Guardrails*: add a known-answer test that advancing by `target_dt` beats the concatenated-column
    baseline on a synthetic with long horizons; keep the column path as a fallback.

- **C-opt-2 — Dense many-to-many readout.**
  - *Strengths*: unlocks sequence-to-sequence outputs; removes a guarded `NotImplementedError`.
  - *Weaknesses*: more design rows (mask semantics, per-step targets); limited current demand.
  - *Risks*: medium (readout-mask edge cases).
  - *Guardrails*: drive it from a real many-to-many dataset need; property-test mask alignment.

- **C-opt-3 — Trained projection / nonlinear readout (torch — "increment 1(b)").**
  - *Strengths*: the biggest capability jump; learned read-in beyond per-feature identity.
  - *Weaknesses*: **introduces torch** to a numpy-only package — env, CI, image-size, and C1
    (first-principles) implications; far larger blast radius.
  - *Risks*: medium-high (dependency weight, training stability, conda env work — the env strategy,
    a dedicated `JuniperRecurrence` env vs reuse of `JuniperCascor1`, is open question **OQ-16**; a
    torch env also needs the LIBTORCH-strip hooks).
  - *Guardrails*: gate behind a demonstrated accuracy ceiling on the numpy path; isolate torch behind
    an optional extra so the closed-form model stays installable without it; keep the fixed LMU
    matrices non-differentiated (C1).

**Recommendation: C-opt-1, then re-evaluate.** Exhaust the numpy-only, C1-clean gains
(`target_dt`-advance) before paying the torch tax. Introduce torch (C-opt-3) only when a measured
accuracy ceiling on real data justifies it, and isolate it behind an extra + dedicated env.

### 7.4 Option set D — cascor recurrence integration (Path B)

E1 — making cascor actually consume the 3-D/`dt` contract — is the flagship future architectural
work. The ingestion-gate analysis already rejected the cheap flatten (Path A is the delay-line trap
that discards `dt`). Within the genuine Path B, *where* does the recurrent block train?

- **D-opt-1 — Standalone-model-only, indefinitely (recommended near-term posture).**
  - *Strengths*: zero cascor risk; the shipped `LMURegressor` already delivers the Δt win as a
    standalone `TrainableModel`; defers the hardest work until a need is proven.
  - *Weaknesses*: cascor stays 2-D / non-recurrent; no constructive *growth* of recurrent capacity.
  - *Risks*: low.
  - *Guardrails*: keep `T=1`-identity as the golden cutover gate for if/when integration starts.

- **D-opt-2 — In-process pool: extend `SharedTrainingMemory` to 3-D.**
  - *Strengths*: reuses cascor's existing in-process training; the descriptor extension is a small,
    fixed-size change (`"<QQBBIII2x"`, adds `shape_2`, still 32 B).
  - *Weaknesses*: touches the algorithmic 2-D core (GEMM forward, sum-over-`dim=1`) — the real
    feedforward↔recurrent boundary, ~10 silent mis-index sites + Tier-3 math; high blast radius in
    production cascor.
  - *Risks*: high (destabilizing production cascor — RK-5).
  - *Guardrails*: kill-criterion + cascor golden trajectory tests before any core edit; land behind a
    no-op shim; the two byte-identical `CandidateUnit` copies must change together (or in cascor-core).

- **D-opt-3 — Distributed-worker-first (transport is already N-D-ready).**
  - *Strengths*: `SharedBinaryFrame` already carries N-D up to 10 dims; avoids the in-process
    descriptor limit.
  - *Weaknesses*: the worker still delegates to the same 2-D `CandidateUnit` math — transport-ready
    is not math-ready; pulls in WS-8 scope.
  - *Risks*: high (couples cascor-3D to distributed training).
  - *Guardrails*: prove the recurrent candidate math standalone first; reuse the worker CPU-lock
    pattern; treat as WS-8-coupled.

**Recommendation: D-opt-1 now; D-opt-2 when triggered.** There is no cheap path to recurrent 3-D
ingestion, and the dataset audit found no current dataset *needs* it beyond what the standalone model
already delivers. Stay standalone until a concrete need arises; when it does, prefer the in-process
descriptor extension (D-opt-2) behind a kill-criterion and cascor golden tests, not a
distributed-first detour.

### 7.5 Option set E — overall roadmap posture

A meta-choice that colors prioritization.

- **E-opt-1 — Ship-and-stabilize first (recommended).** Finish P0–P1 (land, verify, publish, wire)
  before any new capability.
  - *Strengths*: converts a large body of already-built, inert work into shipped value; retires both
    High-severity discrepancies (D-1, D-2); small, bounded effort.
  - *Weaknesses*: defers research novelty by days.
  - *Risks*: low — the work is mostly mechanical + Paul-gated.
  - *Guardrails*: timebox to days; do not let A5 hygiene expand into scope creep.
- **E-opt-2 — Research-forward.** Jump straight to `crossval` / torch readout / ceiling-break,
  leaving the app where it sits.
  - *Strengths*: maximizes novel capability per unit time; correct **if** shipping the app is
    explicitly not this cycle's goal, or if a research question (e.g. a newly-arrived non-star-free
    dataset) is genuinely time-sensitive.
  - *Weaknesses*: leaves finished, tested work stranded and unpublished; compounds the stale-doc
    confusion this audit just surfaced.
  - *Risks*: medium — sunk-cost inertia; the longer the app sits off `main`, the more the three
    feature branches drift and the more a future session re-litigates "is the app done?".
  - *Guardrails*: choose only with an explicit decision that the app is not the priority; even then,
    still land the app on `main` (A1) to stop branch drift while publish (A4) waits.
- **E-opt-3 — Parallel split.** Land/publish the app (P0–P1) while building `crossval` (P2) on a
  separate track.
  - *Strengths*: both tracks progress; they share no files, so they are genuinely independent.
  - *Weaknesses*: context-switching cost; two concurrent review streams.
  - *Risks*: low–medium — concurrent-session races (RK-11) on shared juniper-ml CI/extras files.
  - *Guardrails*: dedicated PRs; `gh pr list` + `gh run list --branch main` before assuming a red
    `main` is yours; keep extras/lint edits in the same PR.

**Recommendation: E-opt-1, widening to E-opt-3** once the app is on `main` — `crossval` shares no
files with the app track, so the parallelism is safe.

---

## 8. Consolidated risks and guardrails

| Risk | Where | Guardrail |
|---|---|---|
| **First CI run of the full app fails** (D-2, RK-10) | A1/A2 | Land via PR with required green checks; triage before merge; never direct-push to `main` |
| **Wrong source branch for remediation** (skeleton branch is subtly behind — no publish workflow/docs) | A1 | Use `feature/ws4b-app-routes` or `…publish-docs` (identical, fullest); verify post-merge tree hash |
| **Premature branch deletion** strands routes/publish-docs work | A5 | Delete the three feature branches only *after* `gh pr view` shows MERGED; then `git worktree prune` |
| **RK-11 — extras/CI lockstep** | B1, C3 | Edit pyproject + `test_pyproject_extras.py` (or the drift lint) in the *same* PR |
| **RK-6 — classification leak into generic routes** | B1, C1, G1, any new regression route | No `argmax`/`accuracy` in routes; keep the conformance-style assert (`test_no_argmax_call_in_routers`) + regression-only metric keys |
| **PyPI deploy gates** | A4, C3 | Paul-managed: pending-publisher registration + `pypi` dual-gate (wait_timer + reviewer); never auto-approve |
| **PyPI CDN cache lag** post-publish | A4, C3 | Poll the version-specific JSON endpoint; expect 5–30 s staleness; retry |
| **Stale editable install after worktree cleanup** | dev envs | model-core resolved to an editable install inside a worktree clone in one env; ensure envs pin the PyPI wheel, not a cleanup-prone worktree path |
| **torch blast radius** (D3; env strategy = OQ-16) | P3 | Isolate behind an optional extra + dedicated `JuniperRecurrence` env (LIBTORCH-strip hooks); keep LMU matrices non-differentiated (C1) |
| **RK-5 — destabilizing production cascor** | E1 | Kill-criterion + golden trajectory tests; no-op shim; change both `CandidateUnit` copies together |
| **R-Δt-3 — "Δt presented ≠ Δt used"** | model increments | Keep the shuffle-`dt` degradation test in the matrix for any new Δt-consuming path |
| **R-Δt-4 — fixed-Δt negative control was analytic** | model | Now measured (§9.1a port); keep the negative-control test green |
| **Concurrent-session races** | all PRs | `gh pr list` + `gh run list --branch main` before assuming a red `main` is yours; dedicated PRs |
| **Stale docs mislead** (D-8) | A5 | Mark WS-4/WS-4b plans "executed"; fix model-core CHANGELOG; rebuild egg-info |

---

## 9. Recommendations and immediate next actions

**Posture**: ship-and-stabilize first ([§7.5](#75-option-set-e--overall-roadmap-posture), E-opt-1), then widen to a parallel `crossval`
track once the app is on `main`.

**Immediate next actions (P0), in order:**

1. **A3 (mechanical, do now):** in the `juniper-recurrence` clone, `git fetch && git pull` so local
   `main` matches `origin/main` (currently 2 behind) — no work is lost; this just surfaces the
   skeleton locally.
2. **A1 (Paul-gated):** open one PR `feature/ws4b-app-routes → main` ([§7.1](#71-option-set-a--consolidating-the-stranded-app-onto-main), A-opt-1). Do **not** merge
   without Paul's explicit signal + green checks.
3. **A2:** treat the PR's `ci-recurrence-app.yml` run as the first real verification; triage any
   failure fix-forward.
4. **A5:** after MERGED — clean up the three feature branches, rebuild the stale egg-info, and mark
   the WS-4/WS-4b plans executed.

**Then (P1):** A4 publish (Paul-gated) → B1 WS-7 extras (same-PR lint update) → B2 deploy entry.

**In parallel once `main` has the app (P2):** C1 `crossval` for model-core 0.2.0 ([§7.2](#72-option-set-b--model-core-020-packaging), B-opt-1).

**Explicitly deferred** until product/dataset/cost triggers fire: D3 (torch readout), E1 (cascor 3-D
recurrence), E2/E3/E4 (WS-5/6/8), F1–F4 (research). G1 (`/v1/metrics`) is a low-risk fast-follow
anytime after P1.

**This document executes none of the above** — it plans them. The merge (A1), publishes (A4/C3), and
deploy approvals are Paul-gated and await his signal.

---

## 10. Cross-references

- Canonical model design: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Model build plan (WS-4): [`JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md)
- App build plan (WS-4b): [`JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md)
- Model-core interface (WS-3): [`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md)
- Cross-validation layer (model-core 0.2.0): [`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md)
- Architecture re-evaluation (P3-C pick): [`JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md`](JUNIPER_RECURSE_OQ4_ARCHITECTURE_REEVALUATION_2026-06-12.md)
- Exhaustive option re-evaluation: [`JUNIPER_RECURSE_OQ4_EXHAUSTIVE_REEVALUATION_2026-06-12.md`](JUNIPER_RECURSE_OQ4_EXHAUSTIVE_REEVALUATION_2026-06-12.md)
- Dataset audit (ceiling not binding): [`JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md`](JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md)
- cascor 3-D ingestion gate (Path A vs B): [`JUNIPER_RECURSE_OQ4_CASCOR_3D_INGESTION_GATE_2026-06-14.md`](JUNIPER_RECURSE_OQ4_CASCOR_3D_INGESTION_GATE_2026-06-14.md)
- Δt handling (Approach C): [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md)
- P7 Grazzi block (ceiling breaker): [`JUNIPER_RECURSE_OQ4_P7_GRAZZI_BLOCK_DESIGN_2026-06-13.md`](JUNIPER_RECURSE_OQ4_P7_GRAZZI_BLOCK_DESIGN_2026-06-13.md)
- Overall design & workstream plan: [`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md)

---

## 11. Method, validation, & evidence base

This evaluation was produced by **five independent, primary-source-grounded analysis sub-agents**,
each owning one slice and required to cite evidence (file:line, doc §, git ref, or live PyPI):

1. Architecture & decisions doc corpus (the "why / what-if" layer).
2. Build-plans & status-claims doc corpus (the "how / claimed-status" layer).
3. Recurrence-model source + tests (tests executed: **53/53 pass**).
4. App source + git/PR forensics (`git merge-tree` conflict check; branch-completeness ranking).
5. Dependency / publish / integration substrate (PyPI verified live via `curl`).

Their findings cross-corroborate (e.g., the git forensics, the live PyPI status, and the stale-claim
ledger were each reached independently by different agents). Every load-bearing claim in this
document was then re-checked by a second, independent pass of **four validators** — factual/source
accuracy, completeness/coverage, internal-consistency & roadmap-soundness, and
markdown-lint/link integrity — each re-grounded against the repos. That pass found **zero material
factual errors** (the model test count, live PyPI status, `git merge-tree` clean-merge, branch
tree-hash identity, and PR bases were all re-verified exact) plus a set of completeness and polish
additions, which were applied before finalization. Residual uncertainties are stated inline rather
than smoothed over (most notably D-2: the full app suite's *behavior* under CI is unverified until
A1/A2).

---

## Appendix A — Verified status-claim diff ledger

"Claimed" = the most recent design-doc assertion; "Verified" = ground truth on 2026-06-17.

| Item | Claimed (doc) | Verified (2026-06-17) | Δ |
|---|---|---|---|
| model-core on PyPI | "not yet published" (CHANGELOG) | 0.1.0 live, 2026-06-14T21:59Z | Stale doc |
| model-core in `[tools]`/`[all]` | done (#416/#418) | present; lint in lockstep | Matches |
| service-core on PyPI | 404 (WS-4b §0) | 0.1.0 live, 2026-06-16T04:39Z | Stale doc |
| service-core in extras | "NOT in extras" (WS-4b §0) | in `[tools]`/`[all]`; lint asserts it | Stale doc |
| recurrence-model version | `0.1.0a0` alpha (WS-4b §0) | `0.1.0` (`_version.py`, tag, PyPI); only egg-info stale | Stale doc/artifact |
| recurrence-model on PyPI | 404 (WS-4b §0) | 0.1.0 live, 2026-06-16T04:40Z | Stale doc |
| recurrence-model tests | matrix planned | 53/53 pass; 10/10 conformance | Verified done |
| app dist | "404 / greenfield" (WS-4b §0) | code-complete on `feature/ws4b-app-routes`; skeleton on `main`; 404 on PyPI | Stale doc |
| app on `main` | PR-1/2/3 sequencing | only PR-1 (skeleton) on `main`; PR-2/3 stranded | Partial |
| app CI status | RK-10 "verify immediately" | full suite never ran (non-main PR bases) | Gap |
| publish-recurrence-model.yml verify | "uses `--extra-index-url`, align it" (§15) | already aligned to `--no-deps` in PR #4 | Resolved |
| `validate_npz_contract` in data-client 0.4.1 | "absent" (MEMORY) | present + exported (`contract.py:41`) | Stale memory |
| `crossval` layer | ratified design 2026-06-16 | design-only; zero code; targets 0.2.0 | Matches (unbuilt) |
| `predict(**kw)` on ABC | deferred to 0.2.0 (Paul's call) | ABC `predict(self, X)` 2-arg; model widens covariantly | Matches |

---

## Appendix B — Git/PyPI forensic anchors

```text
juniper-recurrence repo
  local main      = 58e63a3 (Merge PR #4; tag juniper-recurrence-model-v0.1.0)  [2 behind origin]
  origin/main     = c2e9736 (Merge PR #6, app skeleton)
  fullest branch  = origin/feature/ws4b-app-routes  (tree 0053082; == …/publish-docs)
  remediation     = diff origin/main..origin/feature/ws4b-app-routes = 20 files, +1362/-24
  merge-tree      = clean (no conflicts) → routes→main is a content-clean merge PR

PR lineage
  #1/#2/#3  model (WS-4)           → main
  #4        0.1.0 publish prep      → main   (0.1.0a0 → 0.1.0; hardened publish verify)
  #5        3-D NPZ data path       → main
  #6        app skeleton            → main   (origin/main HEAD)
  #7        app routes              → feature/ws4b-app-skeleton   (NOT main)
  #8        app publish/docs        → feature/ws4b-app-routes      (NOT main)

PyPI (live, 2026-06-17)
  juniper-model-core        0.1.0  (2026-06-14T21:59Z)
  juniper-service-core      0.1.0  (2026-06-16T04:39Z)
  juniper-recurrence-model  0.1.0  (2026-06-16T04:40Z)
  juniper-data-client       0.4.1
  juniper-recurrence (app)  404 / not published; no juniper-recurrence-v* tag

Ports: host 8211 → container 8210 (OQ-15 / OQ-18)
WS-0 ratification: P3-C / LMU / Approach-C (#411, 2026-06-14)
```
