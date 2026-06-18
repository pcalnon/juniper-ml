# Juniper-Recurrence — State Assessment & Design / Development / Testing Roadmap

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-recurrence (model + app); assessment doc hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT — multi-agent-validated state assessment + forward roadmap)
**Last Updated**: 2026-06-17

---

> **What this document is.**
> A validated snapshot of where the `juniper-recurrence` effort actually stands — measured against the
> source code, the git/PR reality, and the live PyPI state, not against the design docs' claims — followed
> by a prioritized design / development / testing roadmap for the outstanding work. Every current-state
> claim was independently re-derived by parallel sub-agents and cross-checked against `file:line`, commit
> SHAs, and live registry queries. Where a forward decision admits more than one credible approach, the
> options are laid out with strengths, weaknesses, risks, and guardrails, and a recommendation is given.
>
> This document **synthesizes and does not duplicate** the design corpus it references (see
> [§9 Source Corpus](#9-source-corpus--evidence-base)). Where those documents are the *intent*, this is
> the *reconciliation of intent against reality* plus the *path forward*.

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Methodology & Validation](#2-methodology--validation)
- [3. Current-State Assessment (validated against source)](#3-current-state-assessment-validated-against-source)
- [4. Defect Register (validated)](#4-defect-register-validated)
- [5. Outstanding Work Inventory](#5-outstanding-work-inventory)
- [6. Roadmap — Prioritization, Ordering, Grouping](#6-roadmap--prioritization-ordering-grouping)
- [7. Design / Development Approach Options](#7-design--development-approach-options)
- [8. Risks & Guardrails (consolidated)](#8-risks--guardrails-consolidated)
- [9. Source Corpus & Evidence Base](#9-source-corpus--evidence-base)
- [10. Open Questions for Paul](#10-open-questions-for-paul)

---

## 1. Executive Summary

The recurrence effort is **substantially further along than the design docs claim**, with one **release-blocking,
high-priority defect** and a small cluster of polish/integration gaps.

**Headlines:**

1. **The model is real, complete, and published.** `juniper-recurrence-model` 0.1.0 is on PyPI, with a genuinely
   first-principles Δt-native LMU (closed-form ZOH discretization in the eigenbasis — no ODE solver, no autodiff),
   **53 tests green**, and a passing `juniper-model-core` conformance suite. The previously-tracked "D3 `predict(**kw)`
   gap" is **closed**.
2. **`juniper-recurrence` `main` is missing the WS-4b app.** The WS-4b app shipped as a 3-PR stack (#6 skeleton →
   #7 routes → #8 publish/docs), but **#7 and #8 merged into their stacked base branches, not `main`**. GitHub reports
   all three "MERGED"; in reality `origin/main` contains only the skeleton. Its `app.py` is deliberately import-clean
   (`create_app(routers=())`, verified), so `main` *runs* — but only as a **health-only app**: the four substantive
   routers, the data path, the CLI `train` command, schemas, state, and tests (13 files) plus the publish workflow are
   **stranded** on `origin/feature/ws4b-app-publish-docs`. This is a recurrence of the known "squash-merge ships first
   commit only" stacked-PR hazard.
3. **Recovery is clean and cheap.** A single non-fast-forward merge PR (`feature/ws4b-app-publish-docs` → `main`)
   carries #7+#8 intact with **zero conflicts** (verified by `git merge-tree`).
4. **The platform plumbing is done.** `juniper-model-core` 0.1.0 and `juniper-service-core` 0.1.0 are both published
   and wired into `juniper-ml [tools]`. WS-1 (3-D irregular-Δt NPZ data foundation) shipped.
5. **The next strategic layer is design-only.** The `juniper-model-core` 0.2.0 cross-validation / fold-executor layer
   is **ratified design with zero code** — and it is the layer that both downstream consumption routes (service/CLI
   evaluation and canopy) block on.
6. **One silent integration gap.** `validate_npz_contract` exists in `juniper-data-client` *source* but is **absent
   from the published 0.4.1 wheel**; the app guards around it, so the Δt full-contract gate is a **no-op on a clean
   PyPI install** until data-client re-publishes.

**The single most important next action** is to land the orphaned WS-4b app onto `main` (Wave 0, below). Everything
else is sequenced behind it.

---

## 2. Methodology & Validation

This assessment was produced in two passes, both multi-agent:

**Pass 1 — Investigation (4 independent sub-agents, parallel).** Each agent was given a disjoint scope, an absolute
path set, and a mandate to return dense, `file:line`-cited findings (not prose, not file dumps):

| Agent | Scope | Key independent finding |
| ----- | ----- | ----------------------- |
| Design-intent | The 5 named design/plan docs + crossval + the companion WS tracker | WS structure, deferral catalogue, doc-staleness list |
| Model-source | `juniper-recurrence-model` source + tests | 53 tests green; D3 gap closed; README API drift |
| App-source + git | `juniper-recurrence` app + PR/merge reality | Re-derived the stacked-merge orphan cold; 0-conflict recovery |
| model-core + integration | `juniper-model-core` + PyPI + data contract | crossval is design-only; data-client wheel lacks the validator |

The two agents touching git/PyPI state (`App-source` and `model-core`) **independently confirmed** the orphaned-merge
defect and the data-client validator gap, respectively — neither was told the other's conclusion.

**Pass 2 — Validation (this document).** Every section was checked by four additional independent, adversarial
sub-agents: (A) source/git accuracy, (B) design-doc fidelity, (C) roadmap completeness & soundness, (D) markdown lint &
internal consistency. **Outcome:** A → PASS-with-fixes — the corrections are folded in below, most notably that
`main`'s app is *health-only* (import-clean), **not** crashing; B → PASS (no misattributions); C → sound, with the
added work items (R6, H6a, H7, both Prometheus configs) and the interim-release / OQ-7-gating clarifications
incorporated; D → clean (`markdownlint-cli` exit 0, zero violations).

**Provenance note.** Live registry checks and git ancestry tests were run against `origin` at the time of writing
(2026-06-17). The local `juniper-recurrence` `main` checkout was **2 commits stale** (behind even the skeleton merge)
during the audit; all merge-state conclusions are stated against `origin/*`, not the local checkout.

---

## 3. Current-State Assessment (validated against source)

### 3.1 Component status (live-verified)

| Component | Ver | On PyPI | In `juniper-ml` extras | State | Evidence |
| --------- | --- | ------- | ---------------------- | ----- | -------- |
| `juniper-model-core` | 0.1.0 | **Yes** | Yes (`[tools]`,`[all]`) | WS-3 shipped; 0.2.0 crossval = design-only | PyPI JSON `['0.1.0']`; `pyproject.toml` extras |
| `juniper-service-core` | 0.1.0 | **Yes** | Yes (`[tools]`,`[all]`) | WS-2 shipped | PyPI JSON; juniper-ml `pyproject.toml:57` |
| `juniper-recurrence-model` | 0.1.0 | **Yes** | **No** | WS-4/4a shipped; 53 tests green | PyPI JSON; `pytest -q` → 53 passed |
| `juniper-recurrence` (app) | 0.1.0 | **No** | **No** | **WS-4b: skeleton on `main`; routes/publish ORPHANED** | `gh pr view`; `git merge-base --is-ancestor` |
| `juniper-data-client` | 0.4.1 | Yes (wheel lacks validator) | n/a (transitive) | WS-1 data shipped; `validate_npz_contract` unreleased | app guard `data.py:23-30`; PyPI 0.4.1 |

### 3.2 Work-stream tracker (doc-claimed vs. actual)

The canonical WS tracker lives in `JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md:44-55`. Its status
column predates the last three weeks of execution and is **stale**; the "Actual" column below is the validated reality.

| WS | Scope | Doc status | **Actual status (validated)** |
| -- | ----- | ---------- | ----------------------------- |
| WS-0 | Design ratification / model pick (P3-C / LMU + Approach-C) | SHIPPED | ✅ RATIFIED 2026-06-14 (ml#411) |
| WS-1 | juniper-data: 3-D irregular-Δt NPZ + regression | PLANNED | ✅ SHIPPED (data #169–171, data-client #87) |
| WS-2 | Extract `juniper-service-core` | PLANNED | ✅ SHIPPED + **PyPI 0.1.0** + wired into `[tools]` |
| WS-3 | `juniper-model-core` interfaces + conformance kit | PLANNED | ✅ SHIPPED + **PyPI 0.1.0** + wired into `[tools]` |
| WS-3.2 | model-core 0.2.0 crossval / fold-executor layer | (new, 2026-06-16) | 🟡 **DESIGN-ONLY — zero code** |
| WS-4 / 4a | Build the LMU regressor (model package) | PLANNED | ✅ SHIPPED + **PyPI 0.1.0** (53 tests) |
| WS-4b | FastAPI / CLI app wrapping the model | (split, 2026-06-15) | 🔴 **PARTIAL — skeleton on `main`, routes+publish ORPHANED** |
| WS-5 | Generalize `juniper-canopy` (model-agnostic UI + backend) | PLANNED | ⏸️ Deferred — gated on WS-4(b) complete |
| WS-6 | Refactor `juniper-cascor` onto shared pkgs + 3-D ingestion | DEFERRED | ⏸️ Scoping draft only; trigger-conditioned; **not a recurrence blocker** |
| WS-7 | Ecosystem integration: `juniper-deploy`, `juniper-ml` extras | PLANNED | ⬜ Not started — gated on app publish |
| WS-8 | Distributed worker / async / WS-streaming training | DEFERRED | ⏸️ Deferred — trigger = training cost (OQ-11) |
| WS-T | Testing architecture (cross-cutting) | IN DESIGN | 🟡 Conformance kit shipped; acceptance bands (OQ-14) TBD |

### 3.3 The model (juniper-recurrence-model 0.1.0) — what's actually built

- **`LMURegressor(TrainableModel)`** (`model.py:51`): per-feature **identity read-in** + **closed-form `lstsq`/ridge
  readout** (the only trained surface). Implements `fit`/`predict`/`metrics`/`describe_topology`/`input_shape`/
  `output_shape`; serialization via standalone `LMUSerializer(ModelSerializer)` (`model.py:219`).
- **`VariableStepLMUMemory`** (`units/lmu_varstep.py:78`): Δt-native LMU. One-time eigendecomposition of the fixed
  HiPPO-LegT `A`; per-step `Ā(Δt)=V·diag(exp(λ·Δt/θ))·V⁻¹` with `expm1`-stabilized `B̄`, a `λ≈0` removable-singularity
  guard, and `dt==0` held-step (padding-safe). **C1-clean**: no ODE solver, no autodiff.
- **Conformance**: `tests/test_conformance.py` subclasses the installed `juniper_model_core.conformance.
  TrainableModelConformance` over `tiny_regression_3d` — 10 contract checks, all pass. The **D3 `predict(**kw)` gap is
  closed**: every sequence keyword (`dt`/`target_dt`/`readout_mask`/`seq_lengths`) is optional with a uniform-grid
  fallback for bare `predict(X)`.
- **Tests**: 53 total across conformance (10), grid-invariance (8), model (23), sequence-data (12). No `skip`/`xfail`/
  `TODO` markers. Includes the §9.1a fixed-Δt negative control and the R-Δt-3 shuffle-`dt` guardrail.

### 3.4 The app (juniper-recurrence) — what's built vs. where it lives

The **real** app lives at the stack tip `origin/feature/ws4b-app-publish-docs` (`06bf7a5`): a FastAPI service built on
`juniper-service-core`'s `create_app`, with four router modules — `training` (exposing `/v1/train` synchronous +
`/v1/training/status`), `predict` (`/v1/predict`), `model` (`/v1/model`), `dataset` (`/v1/dataset`) — a framework-light
`data.py` (data-client → 3-D NPZ → fit/predict kwargs), `state.py` (lock-guarded holder, 409 on concurrent train),
`events.py` (bounded sink), 9 pydantic `schemas`, a dual-mode CLI (`serve` / `train`), 49 tests across 7 files gated at
`--cov-fail-under=90`, and `publish-recurrence-app.yml`.

**The problem is purely a merge-target defect, not a code-quality defect** — see §4.1.

**No client package.** The original WS-4 envisioned a `juniper-recurrence-client`; none was built. It is currently out
of scope — canopy (WS-5 / H2) will need *an* HTTP path to the app (a client lib or direct HTTP), tracked as H7.

### 3.5 The integration surface

- **model-core 0.2.0 crossval/fold-executor**: ratified design (`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`),
  **no code** (exhaustive grep: zero hits for `fold|crossval|cv|executor`). Proposed `juniper_model_core.crossval`
  submodule behind a `[crossval]` extra: `metrics.py` (`score`), `splits.py` (`walk_forward_folds`), `executor.py`
  (`cross_validate(model_factory, …)`). Factory-based, serial v1, no juniper-data change.
- **Data contract (Δt)**: `validate_npz_contract` is in data-client *source* but **not in the published 0.4.1 wheel**.
  The app imports it under `try/except ImportError` and only calls it when present — so a clean PyPI install **skips the
  full Δt contract gate** (model-side shape checks still apply). OQ-7 marks irregular-Δt regression **gating for the
  "completed" state**, so this gap matters for the end-to-end claim even though it does not crash.
- **cascor**: discards `dt` today and rejects `ndim>2` at three tiers (hard gates, ~10 silent mis-index sites, and the
  2-D-by-construction algorithmic core). The recurrence stack is **deliberately standalone** — it does not depend on
  cascor. cascor 3-D ingestion (WS-6) is independent, trigger-conditioned future work.

---

## 4. Defect Register (validated)

| ID | Severity | Defect | Evidence | Fix locus |
| -- | -------- | ------ | -------- | --------- |
| **D-1** | 🔴 **Blocker** | WS-4b routes+publish orphaned; `main` carries only the health-only skeleton — the app deliverable is stranded | §4.1 | one merge PR → `main` |
| **D-2** | 🟠 Major | `juniper-data-client` 0.4.1 wheel lacks `validate_npz_contract`; Δt gate is a no-op on clean install | `data.py:23-30`; PyPI 0.4.1 | data-client republish + pin bump |
| **D-3** | 🟡 Minor | recurrence-model `README.md` API drift — references `FixedOrderLMURegressor`, `LMURegressorSerializer`, `tests/test_lmu_conformance.py` (none exist); **quick-start `import` is broken** | `README.md:8,53,55,63`; actual exports `__init__.py:15` | README edit |
| **D-4** | 🟡 Minor | Empty `juniper_recurrence_model/models/` directory (dead, no `__init__.py`) | leftover from consolidation (CHANGELOG) | `git rm` |
| **D-5** | 🟢 Latent | `LMURegressor.predict` has no `**_` catch-all; an unknown forwarded kwarg would `TypeError` (conformant today) | `model.py:169` | optional `**_` sink |
| **D-6** | 🟢 Doc | Design-doc staleness cluster (see §4.2) | per-item below | doc touch-ups |

### 4.1 D-1 — the orphaned WS-4b stack (full evidence)

| PR | Title | **Base branch** | Merge commit | Reached `main`? |
| -- | ----- | --------------- | ------------ | --------------- |
| #6 | skeleton (PR-1) | `main` | `c2e9736` | ✅ YES |
| #7 | routes (PR-2) | `feature/ws4b-app-skeleton` | `282e720` | ❌ NO |
| #8 | publish/docs (PR-3) | `feature/ws4b-app-routes` | `2bc63c4` | ❌ NO |

- `git merge-base --is-ancestor origin/feature/ws4b-app-routes origin/main` → **NO**; same for `…-publish-docs` → **NO**.
- `origin/main` HEAD = `c2e9736` (skeleton only). `app.py` on `main` calls `create_app(routers=())` (verified) — it
  imports and runs cleanly but exposes **only the health router**; the four substantive routers and the data path
  never reach `main`.
- Missing from `main`: 13 net-new files (`data.py`, `events.py`, `state.py`, `schemas.py`, `routers/*`, 3 test files) +
  modifications to `app.py`/`main.py`/`pyproject.toml`/`conftest.py`/`README.md`/`CHANGELOG.md` + the
  `publish-recurrence-app.yml` workflow. `git diff --stat` = 19 files, +1209/−24.
- **Recovery is conflict-free**: `git merge-tree` over the merge base shows zero `<<<<<<<` markers (only "added in
  remote"). A single non-FF merge PR `feature/ws4b-app-publish-docs` → `main` lands #7+#8 intact.
- The local `juniper-recurrence` `main` (`58e63a3`) is additionally **2 commits behind** `origin/main` — sync required
  before any local operation.

### 4.2 D-6 — design-doc staleness cluster

- **Negative-control status conflict**: detailed-design §3.7 (`:374`) calls the fixed-Δt negative control an unresolved
  gap; the WS-4 build plan (`:163`) marks it **DONE** and the test exists (`test_lmu_grid_invariance.py`). Detailed
  design is stale.
- **Model dist version**: WS-4b plan describes the model as `0.1.0a0`, "not on PyPI". Reality: bumped to **0.1.0 and
  published** (PR #4 "0.1.0-prep").
- **`juniper-recurse` → `juniper-recurrence` rename** is incomplete across the corpus (OQ-19 open); cross-references mix
  both names.
- **Master-plan status table** (`…MIDDLEWARE_REFACTOR…:44-55`) lists WS-1/2/3/4 as `PLANNED`; all four have shipped.
- **`TrainingLifecycleBase`**: model-core's interface design declares the *seam* (WS-3) with the *body* deferred to WS-2;
  service-core shipped a concrete synchronous `TrainingLifecycle` (no FSM/threading). Design prose is aspirational vs.
  as-built — reconcile in the model-core/service-core docs.

---

## 5. Outstanding Work Inventory

Grouped by theme; each item carries size (S/M/L), risk (Lo/Me/Hi), and dependency. Items map to roadmap waves in §6.

### 5.1 Recovery & release (the critical path)

| # | Item | Size | Risk | Depends on |
| - | ---- | ---- | ---- | ---------- |
| R1 | Land orphaned WS-4b app onto `main` (merge PR) | S | Lo | — |
| R2 | Sync local `main`; clean 3 stale `ws4b` worktrees+branches (after R1 merges) | S | Lo | R1 |
| R3 | Fix recurrence-model README API drift (D-3) + remove empty `models/` (D-4); decide `0.1.1` patch vs. carry-on-`main` (§10 Q7) | S | Lo | — |
| R4 | Register PyPI/TestPyPI pending-publishers for `juniper-recurrence`; tag `juniper-recurrence-v0.1.0` → publish | S | Me | R1, Paul-gated |
| R5 | WS-7: add recurrence-model + app to `juniper-ml` extras; update `test_pyproject_extras.py` (same PR) | S | Lo | R4 |
| R6 | New-repo governance: `juniper-recurrence` AGENTS.md (canonical header + drift lint), CODEOWNERS, branch protection + required checks | S | Lo | — |

### 5.2 Integration correctness

| # | Item | Size | Risk | Depends on |
| - | ---- | ---- | ---- | ---------- |
| I1 | data-client: cut a release shipping `validate_npz_contract` (`contract.py`); bump app pin; flip the guard (D-2) | M | Me | — |
| I2 | End-to-end irregular-Δt proof (OQ-7 gating): data → app `/v1/train` → `/v1/predict` on an irregular-Δt dataset | M | Me | R1, I1 |

### 5.3 Capability (model + evaluation)

| # | Item | Size | Risk | Depends on |
| - | ---- | ---- | ---- | ---------- |
| C1 | model-core 0.2.0 crossval/fold-executor layer (PR-1: `crossval` submodule + `[crossval]` extra) | M | Me | — |
| C2 | Evaluation/benchmark harness (walk-forward, baselines, acceptance bands) | M | Me | C1 |
| C3 | Synthetic generators in juniper-data (`multi_sine`, `mackey_glass`, `ar_p`) + walk-forward split | M | Me | — |
| C4 | Next model increment — one of: trained/nonlinear readout (torch enters), dense many-to-many, multi-output readout coverage | M–L | Me | §7 DP-3 |
| C5 | `predict(**_)` forward-compat sink (D-5) | S | Lo | — |

### 5.4 Hardening & ecosystem (deferred / triggered)

| # | Item | Size | Risk | Trigger |
| - | ---- | ---- | ---- | ------- |
| H1 | App Prometheus `/v1/metrics` + `MetricsAuthMiddleware` + observability wiring; verify API-key `_FILE` + rate-limiter on `main` | S | Lo | fast-follow |
| H2 | WS-5: canopy generalization (model-agnostic UI + recurrence backend) | M | Me | WS-4(b) complete |
| H3 | WS-8: distributed worker / async / WS-streaming training | L | Me | training cost (OQ-11) |
| H4 | WS-6: cascor 3-D ingestion (Path B recurrent) | L | Hi | interfaces proven + golden suite |
| H5 | Grown-cascade LMU unit (open research question) | L | Hi | research decision |
| H6 | juniper-deploy: compose service (port 8211→8210), prometheus scrape in **both** `prometheus.yml` + `prometheus.demo.yml`, demo profile | M | Me | R4 |
| H6a | Author app `Dockerfile` (2-stage, CPU-locked base — clone the worker's pattern, not cascor's CUDA image); wire into juniper-deploy | M | Me | R1 |
| H7 | `juniper-recurrence-client` (HTTP client lib) — WS-4 envisioned it; currently out of scope. canopy (H2) needs *an* HTTP path (client lib or direct HTTP) | M | Lo | H2 decision |

---

## 6. Roadmap — Prioritization, Ordering, Grouping

Four waves, sequenced by dependency and risk. **Wave 0 is a stop-the-line fix** (default branch is broken).

### Wave 0 — Recover the orphaned WS-4b deliverable (highest priority, do first)

- **R1** — open one merge PR `feature/ws4b-app-publish-docs` → `main`; confirm `ci-recurrence-app.yml` green on the PR;
  merge (non-FF). This is the single highest-value action in the entire roadmap.
- **R2** — sync local `main`; after R1 is confirmed `MERGED`, remove the three stale `ws4b` worktrees + branches and
  `git worktree prune` (gated on the explicit-merge signal for *those* branches).

Exit criteria: the four routers (`training`/`predict`/`model`/`dataset`) are present on `main` and `/v1/train`, `/v1/predict`, `/v1/model`, `/v1/dataset` are exposed; the full app test suite (49 tests) is green on `main`.

### Wave 1 — Publish & polish (near-term)

- **R3** — README/dead-dir cleanup on recurrence-model (consider a `0.1.1` patch so the PyPI page's quick-start works).
- **R4** — pending-publisher registration + `juniper-recurrence-v0.1.0` tag → TestPyPI soak → PyPI (Paul approves the
  `pypi` environment gate; do not auto-approve).
- **R5** — wire both recurrence packages into `juniper-ml` extras (see §7 DP-7 for the extra-shape options) with the
  lint update in the same PR.
- **I1** — data-client validator release + app pin bump (can run in parallel; unblocks I2).

**Note:** `juniper-recurrence` 0.1.0 (R4) is an *interim* release — it ships the working app, but the OQ-7
"completed-state" claim (end-to-end irregular-Δt regression) is not proven until I1 + I2 land in Wave 2.

Exit criteria: `pip install juniper-recurrence` resolves from PyPI; `juniper-ml[all]` includes the recurrence stack;
the API-key `_FILE` indirection and rate-limiter are confirmed on `main`.

### Wave 2 — Correctness proof & capability (mid-term)

- **I2** — end-to-end irregular-Δt proof (closes the OQ-7 gating claim for "completed" state).
- **C1** — model-core 0.2.0 crossval/fold-executor PR-1 (unblocks evaluation **and** the eventual canopy route).
- **C2 / C3** — evaluation harness + synthetic generators (C3 can lead if datasets are the bottleneck for C2).
- **C4** — first capability increment (sequence chosen per §7 DP-3); **C5** rides along cheaply.

Exit criteria: a reproducible benchmark report on ≥1 irregular-Δt and ≥1 regular-Δt dataset, with baselines; and the OQ-7 "completed-state" gate met — which requires **I1** (data-client validator release) **+ I2** (end-to-end Δt proof) to have landed.

### Wave 3 — Hardening & ecosystem (deferred / trigger-gated)

- **H1** (fast-follow), **H6** (deploy), then the trigger-gated **H2/H3/H4/H5** as their conditions are met.

### 6.1 Dependency-ordering at a glance

```text
R1 ──► R2
  ├──► R4 ──► R5
  ├──► I2 ◄── I1
  └──► H6a (Dockerfile) ──► H6 (deploy)
R6 (repo governance — independent)
C1 ──► C2 ◄── C3
C4 (─ rides with C5)
H1 (fast-follow)   H2/H3/H4/H5/H7 (trigger-gated)
```

### 6.2 Grouping into PRs / sessions

- **Session A (Wave 0)**: R1 + R2 — single repo, single afternoon, unblocks everything.
- **Session B (Wave 1)**: R3 (model patch) ‖ R4 (app publish) ‖ I1 (data-client) — three repos, mostly parallel.
- **Session C (Wave 1 tail)**: R5 (juniper-ml extras) — after R4 publishes.
- **Session D (Wave 2)**: I2 + C1 first, then C2/C3/C4.

---

## 7. Design / Development Approach Options

For each decision point: **Options → Strengths / Weaknesses / Risks / Guardrails → Recommendation.**

### DP-1 — How to recover the orphaned WS-4b app (D-1)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. One merge PR `publish-docs` → `main`** (recommended) | Carries #7+#8 commits intact; preserves authorship/history; **0 conflicts verified**; one review | Non-FF merge commit on `main` | Re-introduces a stacked-branch base into history (cosmetic) | Verify CI green on PR; confirm `import juniper_recurrence.app` post-merge |
| B. Cherry-pick `04f1e91`+`06bf7a5` onto a fresh branch → PR | Linear history; drops the stacked bases | Re-resolves any incidental drift by hand; rewrites SHAs | Cherry-pick conflict if branches drift further | `git range-diff` the result vs. stack tip before merge |
| C. Open *new* PRs cherry-picking #7/#8 onto `main` | Mirrors the intent of the original "retarget #7/#8 → main" step | **Reopen+retarget is impossible** — GitHub treats #7/#8 as MERGED and auto-closes them; this collapses into Option B | Re-resolving incidental drift by hand | Effectively equals B; prefer B's single-branch cherry-pick |
| D. Rebuild routes on a new branch | Clean slate | Throws away 49 reviewed tests + working code; wasteful | High — re-introduces bugs already fixed | Do not, unless the branch is unrecoverable |

**Recommendation: Option A.** Fastest, safest, verified conflict-free. Follow with the systemic guardrail in §8 (G-1)
so this class of defect cannot recur.

### DP-2 — The data-client `validate_npz_contract` gap (D-2)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. Release data-client (0.4.2/0.5.0) with `contract.py`, then bump app pin + flip guard** (recommended) | Single source of truth; the Δt gate becomes real for all consumers | Requires a data-client release cycle (Paul-gated publish) | PyPI cache lag post-publish | Publish-first discipline; bump pin + `requirements.lock` in the same PR |
| B. Vendor `validate_npz_contract` into the app temporarily | Closes the gate immediately, no upstream dependency | Code duplication; drift risk vs. data-client source | Two diverging validators | Mark as a temp shim with a `remove-after data-client publishes` note |
| C. Keep the guard; accept model-side checks only | Zero work; app already degrades gracefully | OQ-7 "completed" claim stays unproven on clean installs | Silent acceptance of malformed Δt artifacts | Only acceptable as the interim state until I1 |

**Recommendation: Option A**, with **C as the explicitly-acknowledged interim**. Avoid B unless I1 slips past Wave 2.

### DP-3 — Next model capability increment ordering (C4)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. Trained / nonlinear readout (torch enters)** | Biggest capability lift; the documented "increment 1(b)" | Adds torch dep + env complexity (OQ-16) | Scope creep; env/LIBTORCH friction | Keep numpy path as default; torch behind an extra; conformance must still pass |
| B. Dense many-to-many readout | Removes a `NotImplementedError`; small, well-scoped | Lower strategic value | Low | Add the test that currently asserts the raise, inverted |
| C. Multi-output readout coverage (`output_dim>1`) | Closes a real test gap (always `(n,1)` today) | Incremental | Low | Property test across output dims |
| D. Defer model work; do evaluation (C2) first | Evaluation tells you *which* increment matters | Delays capability | Analysis paralysis | Time-box the eval; let results pick A/B/C |

**Recommendation: D then B/C then A.** Let the evaluation harness (C2) rank what matters; clear the cheap B/C gaps
opportunistically; gate the torch increment (A) behind a measured need and an OQ-16 env decision.

### DP-4 — model-core 0.2.0 crossval layer: timing & build (C1)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. Build now, serial v1 per the ratified design** (recommended) | Unblocks evaluation **and** canopy; design already concurred | One more package release to sequence | Over-abstraction (RK-4) | Design against ≥2 callers (app eval + a test); ship serial, defer parallel folds |
| B. Inline a throwaway CV loop in the eval harness | No model-core release needed | Duplicates logic the design says belongs in model-core | Drift; re-work when the real layer lands | Only if C1 can't be sequenced before C2 |
| C. Defer crossval entirely | Less work now | Both consumption routes stay blocked | Strands canopy (WS-5) | Don't — it's a known chokepoint |

**Recommendation: Option A.** It is the layer both downstream routes block on; building it serially is low-risk and
high-leverage.

### DP-5 — Evaluation / benchmarking strategy (C2)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. Walk-forward CV on irregular-Δt + regular-Δt, vs. naive/linear baselines** (recommended) | Directly tests the Δt thesis; honest baselines | Needs C1 (folds) + C3 (datasets) | Cherry-picked datasets | Pre-register datasets + metrics; include a fixed-Δt negative control |
| B. Single train/test split, headline metric only | Fast | Weak evidence; no temporal honesty | Overfit-to-split | Use only as a smoke check, not the report |
| C. Full hyper-parameter sweep over `d`/`θ`/ridge | Thorough | Expensive; easy to p-hack | Compute cost | Fix a small grid; report the grid, not the best cell |

**Recommendation: Option A**, seeded with a small declared grid (borrow from C). Acceptance bands = OQ-14 (needs Paul).

### DP-6 — cascor integration path (H4, deferred)

| Option | Strengths | Weaknesses | Risks | Guardrails |
| ------ | --------- | ---------- | ----- | ---------- |
| **A. Defer (status quo)** (recommended now) | Recurrence stack is standalone; zero cascor risk | No cascade+Δt synthesis yet | None | Revisit only when the WS-6 trigger fires |
| B. Path B — recurrent forward over lookback (P3-C in cascade) | The genuine architecture; consumes Δt | Large; touches cascor's 2-D core (3 tiers) | Destabilizes production cascor (RK-5) | Pre-refactor golden-regression suite; no-op shim |
| C. Path A — flatten `(b,L,F)→(b,L·F)` lag-embedding | Quick plumbing win | **Drops Δt**; FIR, inherits star-free ceiling; the OQ-4-ranked-weakest option | False sense of "recurrent" support | Reject as the strategic path; allowable only as an explicit lag-embedding baseline |

**Recommendation: A now; B when triggered; never sell C as recurrence.**

### DP-7 — `juniper-ml` extra shape for the recurrence stack (R5) + recurrent env (OQ-16)

| Sub-decision | Options | Recommendation |
| ------------ | ------- | -------------- |
| Extras placement | (a) new `[recurrence]` extra; (b) fold app into `[servers]` + model into `[tools]`; (c) one combined `[recurrence]` holding both | **(c)** a dedicated `[recurrence]` extra holding model+app reads cleanest and keeps `[servers]`/`[tools]` semantics intact; **also add `[recurrence]` to `[all]`** and update `test_pyproject_extras.py` in the same PR (the lint requires `[all]` to aggregate every non-alias extra exactly once) |
| Recurrent env (OQ-16) | (a) dedicated `JuniperRecurrent` (needs LIBTORCH isolate hook) if/when torch enters; (b) reuse `JuniperCascor1` | **(b) reuse `JuniperCascor1` while numpy-only**; switch to **(a)** only when DP-3 Option A (torch) is chosen |

---

## 8. Risks & Guardrails (consolidated)

| ID | Risk | Likelihood × Impact | Guardrail |
| -- | ---- | ------------------- | --------- |
| **G-1** | **Stacked-PR squash-merge ships only the base** (the D-1 defect class — 3rd+ occurrence) | Med × High | **Never merge a stacked PR whose base is a feature branch**; retarget to `main` before merge, OR land the whole stack as one PR; add a CI check that warns when a PR's base ≠ default branch (roll out to `juniper-recurrence` first, then ecosystem-wide) |
| G-2 | Publishing a consumer before its `-core` dep is on PyPI (docker can't build from sibling source) | Low × High | Publish-first discipline; pin-bump + `requirements.lock` regen in the same PR; TestPyPI soak first |
| G-3 | New CI workflow passes lint but fails first run (observed pattern) | Med × Low | `gh workflow run` each new workflow immediately on first push (RK-10) |
| G-4 | Over-abstraction of the crossval/model interface (RK-4) | Med × High | Design against ≥2 callers; "shared by default, override if needed"; serial-first |
| G-5 | Δt artifacts silently malformed because the contract gate is a no-op (D-2) | Med × Med | Land I1; keep the model-side shape checks as defense-in-depth |
| G-6 | Destabilizing production cascor during any WS-6 work (RK-5) | Med × High | Trigger-conditioned; pre-refactor golden suite; service-core via no-op shim |
| G-7 | Concurrent-session races on shared CI/extras files (RK-11) | Med × Low | Dedicated PRs; update the extras lint in the same PR; `gh pr list` before touching shared files |
| G-8 | pydantic `.env` leak into the test session (no `env_file=` on Settings) | Low × Med | Already honored in app `settings.py`; keep it; covered by `test_settings.py` |
| G-9 | Deployment/PyPI approval gates auto-approved | Low × High | Paul manages all env/PyPI deployment gates; drive to the gate and hand off |

---

## 9. Source Corpus & Evidence Base

**Design / plan docs (read in full by the investigation agents):**

- `notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md` — master model design + plan
- `notes/JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md` — detailed P3-C/LMU design
- `notes/JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md` — model build plan
- `notes/JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md` — app build plan
- `notes/JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md` — model-core interfaces
- `notes/JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md` — crossval/fold-executor (0.2.0)
- `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` — **canonical WS tracker** (`:44-55`)
- `notes/JUNIPER_RECURSE_OQ4_*` — architecture re-evaluation, dataset audit, 3-D ingestion gate (decision: P3-C/LMU)

**Source trees audited:**

- `juniper-recurrence/juniper-recurrence-model/` — model package (model.py, units/lmu_varstep.py, data.py, tests)
- `juniper-recurrence/juniper-recurrence/` — app package (app.py, routers/*, data.py, main.py, tests) at stack tip
- `juniper-ml/juniper-model-core/` — interfaces + conformance kit

**Live state verified:** PyPI versions for `juniper-model-core`/`juniper-service-core`/`juniper-recurrence-model`/
`juniper-data-client`; `gh pr view` for PRs #6/#7/#8; `git merge-base --is-ancestor` / `git merge-tree` for the orphan
analysis; `pytest -q` for the model suite (53 passed).

---

## 10. Open Questions for Paul

1. **Recovery approach (DP-1)** — confirm **Option A** (single merge PR `feature/ws4b-app-publish-docs` → `main`)? This
   is the highest-priority unblock — it lands the entire WS-4b deliverable.
2. **Systemic guardrail (G-1)** — want a branch-protection / CI check added now so the stacked-PR class can't recur, or
   handle it by convention?
3. **`juniper-ml` extra shape (DP-7)** — dedicated `[recurrence]` extra (recommended) vs. splitting across
   `[servers]`/`[tools]`?
4. **Next model increment (DP-3)** — endorse "evaluate first, then B/C, gate torch (A)"?
5. **Evaluation acceptance bands (OQ-14)** — what counts as "good enough" for this research model?
6. **Recurrent env (OQ-16)** — stay on `JuniperCascor1` while numpy-only; spin `JuniperRecurrent` only when torch enters?
7. **Release cadence** — fold the README fix (D-3) into a `0.1.1` model patch, or carry it on `main` until the next
   feature release?

---

## Appendix — Package naming map (consolidated from the companion roadmap)

> Folded in from the companion analysis `JUNIPER_RECURRENCE_STATE_AND_ROADMAP_2026-06-17.md` (an
> independent, parallel state-evaluation produced the same session), which has been **consolidated
> into this canonical roadmap**. Its other unique material — the detailed design/dev options (this
> doc's §7 is canonical), the verified status-claim diff ledger (covered by §3), and the git/PyPI
> forensic anchors (a now-historical pre-publish snapshot) — remains in git history.

There is **no package literally named `juniper-recurrence-core`**. The "core / application" split
maps onto three real artifacts plus one shared contract:

| Informal name | Real artifact | Lives in | Role |
|---|---|---|---|
| "the contract / core" | `juniper-model-core` | `juniper-ml/juniper-model-core/` (subdir pkg) | Shared `TrainableModel`/`GrowableModel` ABCs + conformance kit the model plugs into (WS-3) |
| "the model / core model" | `juniper-recurrence-model` | `juniper-recurrence/juniper-recurrence-model/` (subdir pkg) | The Δt-native LMU regressor implementing `TrainableModel` (WS-4) |
| "the application" | `juniper-recurrence` | `juniper-recurrence/juniper-recurrence/` (subdir pkg) | FastAPI + CLI service wrapping the model on `juniper-service-core` (WS-4b) |
| "the service framework" | `juniper-service-core` | `juniper-ml/juniper-service-core/` (subdir pkg) | Generic FastAPI/lifecycle/security framework the app builds on (WS-2) |

The `juniper-recurrence` **git repository** is the umbrella holding *two* published distributions:
the model (`juniper-recurrence-model`) and the app (`juniper-recurrence`). The `*-core` shared
packages are juniper-ml subdirectories per the ratified placement convention (D4).

---

*Generated 2026-06-17. Current-state claims validated by independent sub-agents against source, git, and live registry
state. Forward-looking sections (roadmap, options) are recommendations pending Paul's decisions in §10.*
