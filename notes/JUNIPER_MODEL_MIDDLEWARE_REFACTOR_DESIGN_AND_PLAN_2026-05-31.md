# Juniper — Model/Middleware Refactor Design & Implementation Plan

**Project**: Juniper ML Research Platform — model↔service separation enabling new-model addition (juniper-recurrence being the first consumer)
**Repository**: pcalnon/juniper-ml (design doc); touches juniper-cascor, juniper-data, juniper-canopy, juniper-deploy, and two new shared packages
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.3.4 (DRAFT — pre-implementation design; split from the master plan 2026-06-03; Round-2 live-code re-verification + Part 8 migration/cutover path added 2026-06-04; OQ-16/17/18 folded into Part 5 2026-06-07; Part 5 OQ-1/2/3/4/5/7 statuses reconciled to Paul's answers 2026-06-07; Status Tracker reconciled to shipped reality + nomenclature refresh 2026-06-17; WS-4b app + WS-6 trigger marked met 2026-06-18)
**Last Updated**: 2026-06-18

---

> **Document status:** design of record. **WS-0 RATIFIED 2026-06-14.** **Execution state (2026-06-18, reconciled into the Status Tracker below):** WS-1/WS-2/WS-3/WS-4 shipped & published
> (`juniper-service-core` 0.1.0 + `juniper-model-core` 0.1.0/0.2.0 on PyPI; the WS-4b recurrence app + `POST /v1/crossval` landed on `juniper-recurrence` main). The model-core **cross-validation
> layer** (0.2.0) is **shipped**, and the **WS-6 trigger is MET** (cascor golden #340 + conformance #341 both green). **WS-5 / WS-7 remain** (WS-8 deferred). Broader reconciled roadmap:
> [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md).
> This document covers the **service/middleware refactor** (extracting the model↔service seam into shared packages so any new model plugs in) plus the **shared scaffolding** for the whole effort.
> The companion document covers the recurrent model itself.
>
> **Provenance:** This document is the **refactor half** of a 2026-06-03 two-way split of the original single master plan (`JUNIPER_RECURSE_DESIGN_AND_PLAN_2026-05-31.md`).
> It is also the designated home for content that is **cross-cutting** to both halves (Status Tracker, binding constraints, method, Risk Register, Open-Questions table, Verification Log, internal sources) — each such block is marked **⚑ CROSS-CUTTING (review)**.
> All WS-*/OQ-*/RK-*/C*/F* identifiers are preserved verbatim across both halves.
> The original five-lens verification pass (Round 1, 2026-05-31) covered the combined content and is reproduced in full in Part 7.

## Companion documents & how to read them

| Document                                                                                               | Scope                                                                                                                                                                                      |
|:-------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Recurrent Model Design & Plan](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md)** — *companion* | The recurrent NN capability: requirements, candidate-architecture survey, top-3 deep dives, recommendation, model-level testing, model risks & open questions, external literature survey. |
|                                                                                                        | -- **Note (RESOLVED 2026-06-14):** the model pick is **P3-C / LMU + Approach-C**; OQ-4 resolved (ceiling not binding — dataset audit).                                                                                                            |
| **This document** — *Model/Middleware Refactor*                                                        | Extracting `juniper-service-core` + `juniper-model-core` from cascor (the "model-addition template"), juniper-data extensions, canopy generalization, ecosystem changes, phased rollout,   |
|                                                                                                        | -- middleware/cross-cutting testing, and the shared scaffolding.                                                                                                                           |

> **The coupling (read this):** this refactor defines the **abstractions the new model plugs into** (`juniper-model-core`'s `TrainableModel`/`GrowableModel`; `juniper-service-core`'s app/service scaffolding).
> The companion model is built **greenfield against these abstractions first**, which is how the template is proven *before* production cascor is refactored (WS-6, trigger-conditioned).
> So: **the companion decides *what to build*; this document decides *what it plugs into* and *how cascor eventually adopts it*.**

---

## Status Tracker

> **⚑ CROSS-CUTTING (review):** The Status Tracker spans both halves (model + refactor) and is the **canonical** workstream state for the whole effort. Housed here per the 2026-06-03 split convention. The companion document carries a model-only slice (WS-0, WS-4) that points back here.
>
> Update this table as workstreams progress. Statuses: `PLANNED` · `IN DESIGN` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `SHIPPED` · `DEFERRED`. "Trigger" names the condition that must hold before a deferred/conditioned workstream starts. **Size** is a coarse effort estimate (S ≈ days, M ≈ 1–2 weeks, L ≈ 3+ weeks / multi-PR) — refine at workstream open. The **Part** column points to the section (and document) that specifies the workstream; `A§` = companion model document.

| ID       | Workstream                                                               | Part        | Size | Status      | Depends on       | Trigger / Notes                                                                                                                            |
|:---------|:-------------------------------------------------------------------------|:------------|:-----|:------------|:-----------------|:-------------------------------------------------------------------------------------------------------------------------------------------|
| **WS-0** | Design ratification (this effort)                                        | All         | S    | `SHIPPED`   | —                | **RATIFIED 2026-06-14 (Paul).** OQ-1 recurrent · OQ-2 C1-binds · OQ-3 framework · OQ-5 synthetics — resolved (companion §10). —             |
|          |                                                                          |             |      |             |                  | -- **OQ-4 RESOLVED:** the star-free ceiling is NOT binding (dataset audit — exception list empty); **model pick = P3-C / LMU + Approach-C**. |
|          |                                                                          |             |      |             |                  | -- OQ-19 rename `recurse`→`recurrence` + OQ-20 fixed-order-LMU-first ratified. Workstream PRs (WS-1…WS-4) may open. See Part 5 OQ-4.         |
| **WS-1** | juniper-data: time-series + regression support                           | 2.4         | M    | `SHIPPED`   | WS-0             | Foundation; unblocks model training. Additive, low risk. **Resolve [OQ-5] here at ratification**                                           |
| **WS-2** | Extract `juniper-service-core` (Tier-1 generic infra)                    | 2.3         | L    | `SHIPPED`   | WS-0             | Additive shared package; cascor adopts behind a no-op shim                                                                                 |
| **WS-3** | Define `juniper-model-core` abstract interfaces                          | 2.3         | M    | `SHIPPED`   | WS-0             | **SHIPPED** — 0.1.0 on PyPI; ABCs + event/serialization contracts + conformance kit (66 tests / ~97%); 0.2.0 crossval designed, not built                                                                        |
| **WS-4** | Build `juniper-recurrence` (LMU reference model) + `juniper-recurrence-client` | A§1.5 / 2.3 | L    | `SHIPPED`   | WS-1, WS-2, WS-3 | **Model SHIPPED** — LMU passes the model-core conformance kit 10/10. **App (WS-4b) SHIPPED** — full FastAPI app on `juniper-recurrence` main (#6–#19), incl. `POST /v1/crossval` consuming model-core 0.2.0; pins `juniper-model-core[crossval]>=0.2.0`.                                                 |
| **WS-5** | Generalize `juniper-canopy` (model-agnostic UI + recurrence backend)        | 2.5         | M    | `PLANNED`   | WS-4             | Builds on canopy's existing `BackendProtocol` seam                                                                                         |
| **WS-6** | Refactor `juniper-cascor` onto shared packages                           | 2.3 / 2.7   | L    | `PLANNED`   | WS-2, WS-3, WS-4 | **TRIGGER MET 2026-06-18** — recurrence interfaces proven (LMU conformance 10/10 + live `/crossval` app) **and** cascor conformance suite green (#341); golden regression-safety captured (#340). The 6a/6b cutover may now begin (kill-criterion §2.7). De-risks production system                                     |
| **WS-7** | Ecosystem integration: `juniper-deploy`, `juniper-ml` extras             | 2.6         | S    | `IN PROGRESS`   | WS-4             | **IN PROGRESS** — juniper-ml `[tools]` extras done (model-core + service-core); juniper-deploy compose service still pending                                                                                                        |
| **WS-8** | (future) `juniper-recurrence-worker` distributed training                   | 2.6         | L    | `DEFERRED`  | WS-4             | **Trigger:** recurrence training cost justifies distribution                                                                                  |
| **WS-T** | Testing architecture (cuts across all)                                   | 3           | M    | `IN PROGRESS` | WS-0             | Conformance kit is a first-class deliverable, not an afterthought                                                                          |

---

## Executive Summary (refactor & testing)

The companion document selects a **recurrent neural-network model** (`juniper-recurrence`) to extend the platform beyond Cascade-Correlation. This document covers the two coupled deliverables that make that model *cheap to add and safe to integrate*: the middleware refactor and the testing architecture.

1. **Middleware refactor (Part 2).**
    - Grounding confirms ~5.5 KLOC *(grounding-pass estimate)* of *already-generic* service infrastructure in cascor, plus a concentrated model↔service seam (`TrainingLifecycleManager`) and several classification-only assumptions (`argmax`, 2-D decision boundary) that a regression/time-series model would break.
    - The target architecture extracts a **`juniper-service-core`** package (FastAPI factory, settings, security, middleware, websocket/worker infra, generic routes, lifecycle base) and a
      **`juniper-model-core`** package (the abstract `TrainableModel` / `GrowableModel` interface, training-event contract, serialization interface, and a reusable conformance test kit), reuses
      the existing `juniper-observability` / `juniper-data-client` / `juniper-config-tools`, and assigns all dataset capability to `juniper-data`.
    - This directly continues documented intent in `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` (ideas #2 Common API, #4 New ABC, #7 Split up juniper-cascor).
    - Per the ratified decision, the **target is comprehensive** but the **cascor refactor is phased and trigger-conditioned** — recurrence is built greenfield against the new interfaces *first*, proving the template before the production system is touched.

2. **Testing architecture (Part 3).**
    - Treated as a first-class deliverable: a reusable **interface-conformance test kit** that any model (cascor included) must pass; numerical-correctness / determinism / growth-loop / regression-metric / temporal-leakage suites for the new model (companion §3.2); contract tests for the shared packages; and regression-safety (golden/snapshot) coverage that gates the cascor refactor.

**The single most important sequencing insight:** `juniper-data` cannot serve this model today (all nine generators are classification + 2-D tabular; the NPZ contract assumes 2-D; splits shuffle and so destroy temporal order). WS-1 (data foundation) is therefore the critical path and should start first.

---

## Part 0 — Scope, Method, and How to Use This Document

> **⚑ CROSS-CUTTING (review):** Part 0 (scope, ratified decisions, binding constraints, method/provenance) frames **both** halves of the effort. It is housed here as the shared home; the companion reproduces only §0.5 (terminology) and C1 (the constraint that shapes the model). Review whether any portion should instead be duplicated into the companion for standalone readability.

### 0.1 What this is and is not

- **Is:** an investigation + analysis + design + implementation plan for the middleware extraction, the associated `juniper-data` / `juniper-canopy` / ecosystem changes, and the testing architecture — together with the recurrent model selected in the companion document, with sources and tracked open questions.
- **Is not:** code. Nothing here is to be implemented until ratified and split into workstream PRs. The plan deliberately surfaces uncertainty rather than papering over it.

### 0.2 Ratified design decisions (input to this draft)

The following were decided by Paul before drafting and are treated as fixed inputs:

| Decision               | Choice                                                                                      | Consequence                                                                                                                                                                         |
|:-----------------------|:--------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Model focus**        | *Span both* growing and fixed-topology recurrent classes                                    | Companion Part 1 surveys the whole space and the top 3 deliberately spans both classes                                                                                              |
| **Middleware scope**   | *Comprehensive target, phased rollout*                                                      | Part 2 designs the full template but stages cascor's adoption behind triggers (WS-6)                                                                                                |
| **Document structure** | ~~*Single master document*~~ → **SUPERSEDED 2026-06-03: split into two** (model + refactor) | **⚑ REVIEW:** the original "single master document" decision was reversed by Paul on 2026-06-03; this file and its companion are the result. Status-tracked; sub-parts within each. |

### 0.3 Binding platform constraints (derived from existing docs, not optional)

These are not requirements the user re-stated; they are pre-existing platform commitments that the design must honor. Each is cited.

- **C1 — First-principles implementation.** *"…implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail… candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper."*
  - (`RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md` §2.) → The recurrent model's recurrence, state, and growth must be inspectable code, **not** a `torch.nn.LSTM` black box.
  - This constraint materially shapes the model ranking (companion Part 1).
- **C2 — Dual-mode application shape.** Every Juniper service has a FastAPI `create_app()` factory (`server.py`) **and** a standalone CLI (`main.py`), Pydantic settings with an env prefix, and the canonical 6-field `AGENTS.md` header (enforced by `tests/test_agents_md_header_schema.py`). juniper-recurrence follows this exactly; env prefix `JUNIPER_RECURSE_`.
- **C3 — Shared-data contract.** Datasets flow `juniper-data → juniper-data-client → model` as NPZ artifacts. All dataset capability belongs to `juniper-data` (per the user's component-boundary statement). juniper-recurrence must consume datasets via `juniper-data-client`, not generate its own.
- **C4 — Shared observability.** Metrics/logging/health/middleware come from `juniper-observability` (`>=0.3.0`; the on-disk version is 0.3.0 and already provides `MetricsAuthMiddleware` — 0.3.1 only adds an unparseable-client-IP warning); new Prometheus collectors use `register_or_reuse` & friends. (`juniper-cascor/AGENTS.md` "Programming Conventions".)
- **C5 — Python ≥ 3.12, line length 512, pytest + 80% coverage, worktree procedures, `util/` script placement.** Ecosystem conventions (`Juniper/AGENTS.md`).

### 0.4 Method & provenance

This document (and its companion) was produced by:

1. A **grounding pass** — five independent read-only agents mapped (a) the cascor model↔service seam, (b) the existing shared packages, (c) juniper-data's time-series/regression gap, (d) juniper-canopy's model coupling, (e) prior design intent and the research philosophy.
2. A **literature survey** — four independent research agents, each required to cite primary sources and self-flag unverifiable claims, covered: constructive/growing RNNs; gated/vanilla RNNs; reservoir + continuous-time nets; modern SSMs + memory models + TCN.
3. **Local verification** of flagged claims (port numbers, dependency-pin conventions, generator inventory, prior-art file existence) against the actual repositories.
4. A **multi-agent verification pass** over the original combined draft (Part 7) to exclude hallucinations and integrate corrections.

> **Anti-hallucination posture.** Where research agents could not read a primary PDF (e.g., scanned 1990s NIPS papers), the affected numbers are explicitly flagged as secondary-sourced.
> Cascade-Correlation-integration claims for non-cascor architectures are uniformly labeled **[speculative]** — no published work implements them.
> Specific cascor source line numbers from the grounding pass are **not** reproduced as load-bearing facts; coupling is cited at the module/behavior level that the cascor `AGENTS.md` independently corroborates, with exact lines deferred to implementation-time confirmation.

### 0.5 Terminology: "recursive" vs. "recurrent"

Moved to the companion model document (§0.5). Summary: the target is interpreted as **recurrent** (temporal chain), not tree-**recursive**, given the time-series/regression emphasis; recorded as [OQ-1].

---

## Part 2 — Middleware Refactor

> **Goal (from the brief):** identify all functionality currently in juniper-cascor that should be **extracted** so the new model need not duplicate it, move it to new or existing middleware
> applications, and thereby *"create a template for the addition of new neural-network models."* Component boundaries (the brief's own words): canopy = front-end/monitoring/control GUI;
> cascor = the Cascade-Correlation model; data = all dataset functionality for any model; observability = metrics/status extraction for monitoring.

### 2.1 The current cascor architecture and the model↔service seam

juniper-cascor (`src/` layout) is a dual-mode app: `src/server.py` (FastAPI) + `src/main.py` (CLI). Its service layer (`src/api/**`) wraps a model-specific core (`src/cascade_correlation/**`, `src/candidate_unit/**`). The grounding pass established that the coupling between them is **concentrated**, not diffuse — it lives almost entirely in `src/api/lifecycle/manager.py` (`TrainingLifecycleManager`), which:

- **imports and instantiates the concrete model** (`CascadeCorrelationNetwork`) rather than an abstract interface;
- **wraps/monkey-patches the model's `fit()`** to emit lifecycle events without modifying the core (a pattern the cascor `AGENTS.md` describes explicitly);
- **introspects model-specific topology** (`hidden_units`, `input_size`, `output_size`);
- **hardcodes the HDF5 serializer** for snapshots;
- **assumes 2-D classification** in the decision-boundary path (`argmax` over outputs; a `shape[1] == 2` input gate).

The last point is the critical compatibility hazard, and verification confirmed it reaches **further than the decision-boundary route** — the accuracy assumption also surfaces in the metrics-history path, metrics collection, and the "auto-snapshot best" feature.
**A regression / time-series model breaks these classification assumptions** (accuracy metric, `argmax`, decision-boundary) baked into routes, monitoring, and the canopy UI.
*(These behaviors are corroborated by `juniper-cascor/AGENTS.md`; exact line numbers from the grounding pass are deferred to implementation-time confirmation — see §0.4 anti-hallucination posture.)*

This matches **documented prior intent**: `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` idea **#4 "New ABC"** ("extract shared functionality from `CascadeCorrelationNetwork` and `CandidateUnit` into a new Abstract Base Class") and idea **#7 "Split up juniper-cascor"** ("decompose into ABC, two child classes, and a management layer").
The present plan generalizes that intent from *intra-cascor* (ABC over network/candidate) to *cross-model* (ABC/Protocol over any Juniper learning model).

### 2.2 Classification of cascor functionality (extract / abstract / keep)

From the grounding cartography (classifications anchored to cascor's documented module map):

| Tier                                                   | Cascor modules                                                                                     | Classification | Disposition                                                                                                      |
|:-------------------------------------------------------|:---------------------------------------------------------------------------------------------------|:---------------|:-----------------------------------------------------------------------------------------------------------------|
| **T1 — Pure infra (≈5.5 KLOC [grounding estimate];**   | `api/app.py`, `api/settings.py` (base), `api/security.py`, `api/secrets.py`, `api/middleware.py`,  | GENERIC-INFRA  | **Extract → `juniper-service-core`** (mostly lift-and-shift). Several already re-export `juniper-observability`. |
| -- **~0 model coupling — worker-subsystem inclusion**  | -- `api/observability.py`, `api/service_launcher.py`, `api/websocket/manager.py`,                  |                |                                                                                                                  |
| -- **is contingent on [OQ-11])**                       | -- `api/websocket/worker_stream.py`, `api/workers/{protocol,registry,audit,metrics,security}.py`,  |                |                                                                                                                  |
|                                                        | -- `log_config/**`, `profiling/**`, `utils/**`                                                     |                |                                                                                                                  |
| **T2 — Semi-generic (needs an interface to decouple)** | `api/lifecycle/{manager,monitor,state_machine}.py`, `api/workers/coordinator.py`,                  | SEMI-GENERIC   | **Extract base + keep cascor subclass.** Base lifecycle/routes/serializer in `juniper-service-core`;             |
|                                                        | -- `api/routes/{training,dataset,history,snapshots,metrics,health}.py`,                            |                | cascor-specific bits (cascade events, candidate fields, HDF5 weight layout) move to a cascor subclass.           |
|                                                        | -- `parallelism/task_distributor.py`, `snapshots/snapshot_serializer.py`, `api/models/training.py` |                |                                                                                                                  |
| **T3 — Model-specific (the model)**                    | `cascade_correlation/**`, `candidate_unit/**`, `cascor_constants/**`, `cascor_plotter/**`,         | MODEL-SPECIFIC | **Stays in cascor.** (Two-spiral is arguably a *dataset* and could migrate to juniper-data per C3 — see [OQ-8].) |
|                                                        | -- `api/routes/decision_boundary.py`, `spiral_problem/**`                                          |                |                                                                                                                  |

Full ecosystem Status Tracker (all workstreams WS-0…WS-T) lives in the companion document. This is the model-only slice.

Two new shared packages, plus reuse of three existing ones, plus the new app.
(Packaging follows the established Juniper shared-package template: `juniper_<name>/` import package, `pyproject.toml` with setuptools, independent publish workflow on a `juniper-<name>-v*` tag, semver.
**Pin convention is mixed across the ecosystem** — `juniper-doc-tools`/`juniper-config-tools` pin `>=X.Y.Z,<0.2.0` while `juniper-observability`/`juniper-ci-tools` are floor-only; **recommendation:** new pre-1.0 packages adopt the *capped* form `>=X.Y.Z,<X.(Y+1).0` for safety.)

```bash
                         ┌─────────────────────────────────────────────────────┐
                         │  EXISTING shared packages (reuse as-is)             │
                         │  • juniper-observability  (metrics/log/health/mw)   |
                         │  • juniper-data-client    (dataset fetch)           │
                         │  • juniper-config-tools   (env aliases)             │
                         └─────────────────────────────────────────────────────┘
                                           ▲              ▲
                                           │              │
   ┌─────────────────────────────┐   ┌─────┴──────────────┴─────────┐
   │  juniper-model-core (NEW)   │   │  juniper-service-core(NEW)   │
   │  • TrainableModel (ABC/     │   │  • create_app() factory      │
   │    Protocol)                │◄──│  • SettingsBase (env pfx)    │
   │  • GrowableModel            │   │  • security / middleware     │
   │  • TrainingEvent contract   │   │  • websocket + worker infra  │
   │  • ModelSerializer iface    │   │  • generic routes:           │
   │  • TrainingLifecycleBase    │   │    health/training/metrics/  │
   │  • conformance test kit     │   │    dataset/snapshots         │
   └─────────────────────────────┘   │  • TaskDistributor           │
            ▲            ▲           └──────────────────────────────┘
            │            │                    ▲           ▲
            |            |                    |           |
   ┌────────┴───┐  ┌─────┴────────┐   ┌───────┴───┐  ┌────┴──────────────────┐
   │ juniper-   │  │ juniper-     │   │ juniper-  │  │ juniper-recurrence    │
   │ cascor     │  │ recurrence   │   │ cascor    │  │ (NEW app, WS-4)       │
   │ (CascadeCC │  │ (RCC, then   │   │ refactor  │  │ • RCC model           │
   │  impl T3)  │  │  ESN, LMU)   │   │ WS-6      │  │ • recurrent           │
   │ WS-6       │  │              │   │ triggered │  │   lifecycle subclass  │
   └────────────┘  └──────────────┘   └───────────┘  └───────────────────────┘
```

**`juniper-model-core` (the *model* template).** The linchpin (cf. journal idea #4). Defines:

- `TrainableModel` — the minimal contract the service layer needs: `fit(X, y, X_val=, y_val=, **kw)`, `predict(X)` / `forward(X)`, `input_shape` / `output_shape`, `task_type ∈ {classification, regression}`, `metrics() -> dict`, plus model-introspection (`describe_topology()`).
- `GrowableModel(TrainableModel)` — for constructive models (RCC, Growing ESN): `grow_step()`, `n_units`, growth-event hooks, `freeze()`. Fixed-topology models (LMU, LSTM) implement only `TrainableModel`.
- `TrainingEvent` contract — a generalized, model-agnostic event vocabulary (`training_start/end`, `epoch_end`, `unit_added`, `phase_change`) that *subsumes* cascor's events.
  - The monitor consumes the generic vocabulary; each model maps its events onto it.
  - **Illustrative mapping:** cascor `cascade_add` → `unit_added`; `candidate_progress` → `phase_change` (phase=`candidate_training`, per-candidate detail in payload); `epoch_end`/`training_start`/`training_end` map 1:1.
  - RCC reuses `unit_added`; Growing-ESN maps sub-reservoir addition → `unit_added`.
  - (Confirming this mapping preserves cascor's monitoring fidelity is a WS-6 acceptance criterion.)
- `ModelSerializer` interface — `save(model, path)` / `load(path)`; cascor's HDF5 serializer becomes one implementation.
- `TrainingLifecycleBase` — the de-cascored manager (threading, FSM, dataset mgmt, monitoring hooks) that operates only against `TrainableModel`/`GrowableModel`.
- The **conformance test kit** (see §3.3) — a reusable pytest suite any implementer must pass.

> **Design sketch (illustrative — NOT final code; here only to make the contract concrete):**
>
> ```python
> # juniper_model_core/interfaces.py  (SKETCH)
> from typing import Protocol, Literal, runtime_checkable
>
> TaskType = Literal["classification", "regression"]
>
> @runtime_checkable
> class TrainableModel(Protocol):
>     task_type: TaskType
>     def fit(self, X, y, *, X_val=None, y_val=None, **kw) -> "TrainResult": ...
>     def predict(self, X): ...                 # continuous for regression; logits/proba for classification
>     def metrics(self) -> dict[str, float]: ...  # mse/mae/r2 OR accuracy/loss — model declares which
>     def describe_topology(self) -> dict: ...     # model-agnostic nodes/edges for canopy
>     @property
>     def input_shape(self) -> tuple[int, ...]: ...   # (features,) or (timesteps, features)
>     @property
>     def output_shape(self) -> tuple[int, ...]: ...
>
> class GrowableModel(TrainableModel, Protocol):
>     @property
>     def n_units(self) -> int: ...
>     def grow_step(self, residual) -> "GrowthOutcome": ...   # add+freeze one unit; emits unit_added
>
> # describe_topology() returns a model-agnostic graph that canopy renders WITHOUT
> # knowing the model type — the contract seam between juniper-model-core and the UI:
> # {
> #   "model_type": "rcc" | "growing_esn" | "lmu" | "cascade_correlation",
> #   "nodes": [{"id": str, "kind": "input|hidden|output|reservoir|memory", "frozen": bool}],
> #   "edges": [{"src": str, "dst": str, "recurrent": bool}],
> #   "meta":  {"n_units": int, "task_type": TaskType}
> # }
> ```

**`juniper-service-core` (the *service* template).** The de-cascored T1 + T2-base: `create_app()`, `SettingsBase` (subclassed per app to set the env prefix), security/middleware, websocket + worker subsystems, generic routes, `TaskDistributor`. Apps subclass routes/lifecycle and inject their `TrainableModel`.

**What juniper-recurrence actually contains (small!):** its concrete recurrent model(s) (RCC first — see companion Part 1), a `RecurrentLifecycle(TrainingLifecycleBase)` mapping recurrent growth onto `TrainingEvent`s, a `Settings(SettingsBase)` with prefix `JUNIPER_RECURSE_`, and a CLI problem (time-series regression analog of two-spiral). Everything else is inherited. **This is the template working as intended.**

### 2.4 juniper-data extensions (WS-1 — the critical path)

Per C3, *all* dataset capability belongs to juniper-data. Grounding found it **cannot serve this model today**:

| Capability        | Today                                                                                                                                           | Needed                                                             | Gap         |
|:------------------|:------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------|:------------|
| Generators        | 9, **all classification, all 2-D tabular** (arc_agi, checkerboard, circles, csv_import, gaussian, mnist, moon, spiral, xor — confirmed on disk) | ≥1 regression + ≥1 time-series generator                           | **MISSING** |
| NPZ shape         | 2-D assumed (`X.shape[1]`=features; one-hot `y`)                                                                                                | 3-D `(samples, timesteps, features)`; scalar/vector regression `y` | **MISSING** |
| Splits            | shuffle-based                                                                                                                                   | **temporal** (non-shuffled) train/val/test; walk-forward option    | **MISSING** |
| Sequence metadata | none                                                                                                                                            | optional `seq_lengths`, `padding_mask`, target `scaling` params    | **MISSING** |

WS-1 adds: regression generators (**multi-sine, Mackey-Glass, AR(p)** — per [OQ-5], provisionally resolved 2026-06-02); a 3-D-aware NPZ contract (back-compatible: 2-D still valid); a `temporal_split`; and task-type/scaling metadata in the artifact + data-client.
**This is additive and low-risk to existing consumers** and must precede WS-4.
The NPZ contract change is the one ecosystem-wide ripple — it touches the data-client and any shape-validating consumer; design it as an *extension* (new optional keys, `X.ndim` dispatch) not a breaking change.
Recorded as **[OQ-6]**.

### 2.5 juniper-canopy generalization (WS-5)

Grounding found canopy **already has a model-agnostic seam** — a `BackendProtocol` with demo/service backends — which is a genuine asset. Disposition:

- **Reuse as-is:** FastAPI server, `BackendProtocol`, websocket manager, observability, health, snapshot/redis/cassandra panels.
- **Adapt (moderate):** metrics panel (accuracy → MSE/MAE/R² driven by the model's declared `task_type`/`metrics()`), dataset plotter (2-D scatter → time-series line plot), network visualizer (cascade columns → recurrent-cell/topology view from `describe_topology()`), training-monitor phase names (generic vocabulary).
- **Replace/conditionally-render:** decision-boundary, candidate-metrics, and cascade-evolution panels are cascor-specific — render them only when the backend advertises those capabilities.
- **Add:** a `juniper-recurrence-client` backend behind the existing `BackendProtocol`.

The clean path is **schema-driven UI**: backends advertise their param schema, available metrics, and model type; canopy renders conditionally. This is the canopy half of the "template." *(Watch the documented Playwright/Dash `dbc.Input(type=number)` limitation when testing — tests must POST to the param endpoint directly; see §3.4.)*

### 2.6 Ecosystem changes

| Repo                                | Change                                                                                                                               | Risk                                                 |
|:------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------|
| **(new) juniper-recurrence**           | New service app (WS-4)                                                                                                               | New code, isolated                                   |
| **(new) juniper-recurrence-client**    | HTTP/WS client, mirrors juniper-cascor-client (cf. journal idea #5)                                                                  | Low                                                  |
| **juniper-data**                    | Time-series/regression support (WS-1)                                                                                                | Additive                                             |
| **juniper-canopy**                  | Model-agnostic UI + recurrence backend (WS-5)                                                                                           | Moderate (UI)                                        |
| **juniper-cascor**                  | Adopt service-core + implement model-core (WS-6)                                                                                     | **Highest — production system; trigger-conditioned** |
| **juniper-deploy**                  | Compose service + port (suggest host 8211→ctr 8210, mirroring cascor's 8201→8200) **[OQ-15]** (WS-7)                                 | Low                                                  |
| **juniper-ml**                      | Add `juniper-recurrence-client` to extras; new shared packages to `[tools]`/`[all]`; lint contracts (`test_pyproject_extras.py`) (WS-7) | Low; must update extras lint in same PR              |
| **(future) juniper-recurrence-worker** | Distributed training (WS-8)                                                                                                          | Deferred                                             |

### 2.7 Phased rollout (comprehensive target, trigger-conditioned cascor)

Sequencing embodies the ratified "comprehensive target, phased rollout" decision. **The defining principle: prove the template on greenfield recurrence *before* refactoring production cascor.**

1. **WS-1 — Data foundation** (additive; critical path). Time-series + regression generators, 3-D NPZ, temporal split.
2. **WS-2 — Extract `juniper-service-core`** from cascor T1 infra. Cascor keeps working via a thin re-export shim (no behavior change).
3. **WS-3 — Define `juniper-model-core`** interfaces + conformance kit (design + tests; no app disruption).
4. **WS-4 — Build juniper-recurrence** (RCC) + client, greenfield against WS-2/WS-3. **This validates the abstractions without risk to cascor.** (Model substance: companion Part 1.)
5. **WS-5 — Generalize canopy** + add recurrence backend.
6. **WS-6 — Refactor cascor** onto service-core + model-core.
    - **TRIGGER MET (2026-06-18).** WS-4 has shipped, and the cascor golden/snapshot regression suite (#340) and the model-core conformance suite (#341) are both green — so WS-6 may now begin.
      - Through the deferred period cascor stayed as-is (it lost nothing; it simply did not yet consume the shared packages).
    - **Kill-criterion:** if the conformance suite cannot be made green for cascor without changing observable behavior, WS-6 is abandoned — cascor keeps its own service stack, recurrence still benefits from the shared packages, and the one-sided extraction is documented rather than forced.
7. **WS-7 — deploy/meta-package** integration. **WS-8 — recurrence-worker** (deferred; trigger = training cost).

### 2.8 Risks & guardrails — the refactor

| Risk                                                                    | Guardrail                                                                                                                                                                       |
|:------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Premature/over-abstraction**                                          | Adopt the journal's rule (paraphrasing its two clauses): *"shared by default, override if needed,"* and *"move to children only when semantically necessary."*                  |
| -- (journal's own §4 risk: "putting too much in the ABC                 | -- Drive the interface from **two** real implementers (cascor + RCC) before freezing it — never design the ABC from cascor alone.                                               |
| --  makes child classes trivial; too little defeats the purpose")       |                                                                                                                                                                                 |
| **Destabilizing production cascor**                                     | WS-6 is trigger-conditioned and gated by a golden-regression suite captured *before* any refactor. service-core extraction (WS-2) ships behind a no-op re-export shim.          |
| **NPZ contract change ripples**                                         | Make it purely additive (optional new keys, `X.ndim` dispatch); 2-D path byte-identical; version the artifact.                                                                  |
| **Classification assumptions leak into "generic" routes**               | The conformance kit asserts a *regression* model round-trips through every generic route (no `argmax`, no accuracy assumption).                                                 |
| **Shared-package proliferation / maintenance burden**                   | Exactly two new packages; justify each against the ≥2-consumer bar that `juniper-observability` set. Resist a third (`juniper-serialization`) until a second serializer exists. |
| **Cross-repo version skew**                                             | Reuse the existing drift-lint pattern (`test_doc_tools_drift.py` / `test_ci_tools_drift.py`) for the new packages.                                                              |
| **Concurrent-session race on shared CI files** (known ecosystem hazard) | Land shared-package + workflow edits in dedicated PRs; verify each new workflow with `gh workflow run` before relying on it.                                                    |

### 2.9 Open questions — refactor

> The full consolidated table (all OQs, both halves) is in Part 5; OQ identifiers are shared. The refactor-owned questions:

- **[OQ-6]** NPZ 3-D extension: confirm additive-only (no breaking change) is acceptable, and which optional keys (`seq_lengths`, `padding_mask`, `scaling`) are in-scope for WS-1 vs. deferred.
- **[OQ-8]** Should `spiral_problem` (and a future recurrence CLI problem) migrate into juniper-data per the "all dataset functionality in juniper-data" boundary, or stay as in-app CLI demos?
- **[OQ-9]** Package granularity: two packages (`service-core` + `model-core`) vs. one combined `juniper-core` with submodules. (Recommend two — different change cadences, different consumers.)
- **[OQ-10]** Does the abstract `TrainableModel` live in a new package, or (journal idea #4's narrower framing) inside cascor first and migrate later? (Recommend new package, designed against two implementers.)
- **[OQ-11]** Worker protocol: is recurrent candidate/unit training parallelizable in a way that reuses cascor's worker protocol, or does it need a different task payload? (Affects whether service-core's worker layer is truly model-agnostic.)

---

## Part 3 — Testing Architecture

> Testing is a **first-class deliverable (WS-T)**, not an afterthought, and spans three targets named in the brief: (a) the new juniper-recurrence app, (b) any new middleware package(s), (c) modifications to existing apps. The centerpiece is the **interface-conformance test kit** — the testing analog of the model-addition template. **The model-specific suite (§3.2) lives in the companion document;** everything else is here.

### 3.1 Principles & inherited conventions

> **⚑ CROSS-CUTTING (review):** testing principles/conventions apply to both halves.

- **Framework & gates:** pytest; ecosystem-standard markers (`unit`, `integration`, `performance`, `slow`, `long`, `gpu`, `multiprocessing`, plus model-domain markers like `growth`, `regression`, `timeseries`); **80% coverage threshold**; pre-commit (flake8/black/isort/mypy/bandit/shellcheck); CI on push/PR.
- **Determinism is testable, not aspirational:** every model exposes a `random_seed`; tests assert bit-/tolerance-reproducibility across runs (mirrors cascor's `random_seed` convention).
- **Inherit the ecosystem's hard-won pytest defenses** (from prior incidents, now standard): block dash/playwright **plugin autoload** (SIGSEGV defense); reap orphaned multiprocessing children; set BLAS thread limits before imports; pyproject is the single source of pytest config (no stray `pytest.ini`). New repos copy these from cascor.
- **`juniper-observability.testing.reset_prometheus_registry`** fixture for any test touching Prometheus collectors.

### 3.2 Testing the new model (juniper-recurrence)

Moved to the companion model document (§3.2) — numerical-correctness, known-answer/golden, regression-metric, time-series-leakage, growth-loop, determinism, overfit-tiny, and architecture-specific stability suites for RCC/ESN/LMU.

### 3.3 The interface-conformance test kit (first-class, ships in `juniper-model-core`)

A **single reusable, parametrized pytest suite** that *any* `TrainableModel`/`GrowableModel` implementation must pass. Both juniper-recurrence (RCC, ESN, LMU) **and refactored cascor** run it against their models. This is what makes the "template" verifiable rather than aspirational.

It asserts, for a supplied model factory + tiny dataset fixture:

- Interface compliance (`isinstance(model, TrainableModel)`; all methods present, correct signatures/return types).
- `fit → predict → metrics` round-trips; `metrics()` keys match the declared `task_type`.
- `describe_topology()` returns canopy-renderable, model-agnostic structure.
- Serialization round-trip via `ModelSerializer` is **lossless** (predictions identical after save/load).
- `TrainingEvent`s are emitted in a legal order (`training_start` … `training_end`); for `GrowableModel`, `unit_added` increments `n_units`.
- Every **generic service route** accepts the model (a regression model must traverse training/metrics/snapshot routes with no classification assumption).

> **Why this is load-bearing:** it converts "we extracted shared code" into "any new model is *proven* pluggable," and it is the regression-safety net that gates the cascor refactor (WS-6).

### 3.4 Testing the middleware packages & modifications to existing apps

- **`juniper-service-core` / `juniper-model-core`:** unit tests per module; **contract tests** that a minimal stub model drives every generic route + websocket channel; backward-compat tests
  proving the extracted code matches cascor's prior behavior (golden responses captured pre-extraction). Follow the `juniper-observability` package-test pattern (isolated registry, own CI lane,
  `juniper-<name>-v*` publish gating). Add a **drift lint** (clone of `test_doc_tools_drift.py`) so consumer pins can't fall behind.
- **juniper-cascor (WS-6 regression safety):** **before** any refactor, capture a golden/snapshot suite (training trajectories on two-spiral with fixed seed; API response snapshots; snapshot-serialization round-trips). The refactor is accepted only if golden suite + conformance kit stay green. This is the concrete guardrail behind the WS-6 trigger.
- **juniper-data (WS-1):** generator output-shape/dtype tests (2-D *and* 3-D); **temporal-split leakage** tests (property-based: for any split, `max(train_time) < min(test_time)`); NPZ contract back-compat (2-D artifacts still load); scaling round-trip (denormalize recovers originals).
- **juniper-canopy (WS-5):** model-agnostic rendering tests (regression backend → MSE panel, no decision-boundary); conditional-panel tests; backend-protocol conformance for the recurrence backend. **Known constraint:** Playwright cannot drive Dash `dbc.Input(type=number)` React state — UI param tests must **POST to the param endpoint directly**, and the UI subsuite must run isolated (autoload-blocked) to avoid the documented event-loop leak.

### 3.5 Cross-cutting test concerns

> **⚑ CROSS-CUTTING (review):** applies to both halves.

- **Integration / E2E:** recurrence ↔ juniper-data (fetch a time-series regression dataset, train, serve metrics) ↔ canopy (render). A docker-compose E2E in juniper-deploy (mirrors cascor's `test_juniper_data_e2e.py`).
- **Performance benchmarks:** micro (forward/step latency, growth-step cost, readout-solve time) + end-to-end, mirroring cascor's `tests/performance/`. Establish baselines early to catch regressions.
- **Property-based testing (hypothesis):** shape/dtype invariants, temporal-split properties, serialization round-trips — high leverage for the contract surfaces.
- **CI/CD:** per-repo pipeline cloned from cascor (pre-commit, unit, integration, build, security, docs); cross-repo dispatch for the shared packages; **verify each new workflow with `gh workflow run` immediately** (a workflow can pass yamllint yet fail at first real execution — a repeatedly-observed ecosystem failure mode).
- **Security:** bandit + gitleaks + pip-audit, as elsewhere; metrics endpoint gated by `MetricsAuthMiddleware` (observability ≥0.3.0).

### 3.6 Toolset summary

| Concern        | Tool                                                      | Notes                               |
|----------------|-----------------------------------------------------------|-------------------------------------|
| Test runner    | pytest                                                    | markers, `--run-long`, coverage     |
| Coverage       | pytest-cov / coverage[toml]                               | 80% gate                            |
| Async / API    | pytest-asyncio, httpx                                     | FastAPI `TestClient` pattern        |
| Property-based | hypothesis                                                | shapes, splits, round-trips         |
| Parallel       | pytest-xdist                                              | mind multiprocessing-orphan reaping |
| Numerical      | numpy/torch finite-diff helpers                           | gradient checks                     |
| Perf           | pytest-benchmark or cascor's micro-bench harness          | baselines                           |
| Prometheus     | `juniper_observability.testing.reset_prometheus_registry` | registry isolation                  |
| Lint/security  | flake8/black/isort/mypy/bandit, gitleaks, pip-audit       | pre-commit + CI                     |

### 3.7 Open questions — testing

- **[OQ-12]** Where does the conformance kit physically live so both recurrence and cascor consume it — exported from `juniper-model-core` as an installable `pytest` plugin, or a `[test]` extra? (Recommend installable kit + thin per-repo wrapper.)
- **[OQ-13]** Golden-test substrate for cascor regression safety before WS-6: trajectory hashing vs. tolerance-based numeric comparison (seed/BLAS nondeterminism may force tolerance-based).
- **[OQ-14]** Performance baseline acceptance bands for a research (vs. production) model — how much regression is "a finding" vs. "a failure"?

---

## Part 4 — Consolidated Risk Register

> **⚑ CROSS-CUTTING (review):** the Risk Register spans both halves and is the **canonical** register for the whole effort. The companion model document carries a model-only slice (RK-2, RK-3, RK-7, RK-13).

| #     | Risk                                                                              | L×I                                                   | Mitigation / Guardrail                                                                                        | WS       |
|-------|-----------------------------------------------------------------------------------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|----------|
| RK-1  | **juniper-data can't serve time-series regression** — blocks everything           | High × High                                           | WS-1 first; additive NPZ extension                                                                            | WS-1     |
| RK-2  | **RCC representational ceiling** (star-free only) bites on a chosen task          | Med × Med → **under [OQ-4] re-evaluation 2026-06-02** | Scope regression/smooth signals; framework fallback LMU/gated/group-implementing unit; OQ-4 change model pick | WS-4     |
| RK-3  | **RCC regression is unproven** in the literature                                  | Med × Med                                             | Treat as research; golden known-answer tests; ESN (native regression) as parallel track                       | WS-4     |
| RK-4  | **Premature/over-abstraction** of the model interface                             | Med × High                                            | Design ABC against ≥2 implementers (cascor+RCC); "shared by default, override if needed"                      | WS-3     |
| RK-5  | **Destabilizing production cascor** during refactor                               | Med × High                                            | WS-6 trigger-conditioned; pre-refactor golden suite; service-core via no-op shim                              | WS-6     |
| RK-6  | **Classification assumptions leak** into "generic" routes                         | Med × Med                                             | Conformance kit drives a regression model through every route                                                 | WS-3     |
| RK-7  | **First-principles vs. capability tension** (C1 vs. R5) unresolved                | Med × Med                                             | [OQ-2]; default to first-principles per C1, document any exception                                            | WS-0     |
| RK-8  | **Shared-package proliferation / maintenance**                                    | Low × Med                                             | Exactly two packages; ≥2-consumer bar; drift-lint                                                             | WS-2/3   |
| RK-9  | **NPZ contract change breaks existing consumers**                                 | Low × High                                            | Additive-only; 2-D path byte-identical; version artifact                                                      | WS-1     |
| RK-10 | **New CI workflows pass lint but fail first run** (observed pattern)              | Med × Low                                             | `gh workflow run` each new workflow immediately                                                               | WS-2/4/7 |
| RK-11 | **Concurrent-session races on shared CI/extras files**                            | Med × Low                                             | Dedicated PRs; update extras lint in same PR                                                                  | WS-7     |
| RK-12 | **Canopy UI test fragility** (Dash/Playwright `type=number` gap; event-loop leak) | Med × Low                                             | POST param endpoint directly; isolate UI subsuite                                                             | WS-5     |
| RK-13 | **SSM/Mamba temptation** pulls scope toward black-box dependencies                | Low × Med                                             | Mamba is baseline-only; S5/diagonal-S4 deferred behind LMU                                                    | WS-4     |

---

## Part 5 — Open Questions & Areas of Uncertainty

> **⚑ CROSS-CUTTING (review):** the consolidated Open-Questions table spans both halves and is **canonical**. The companion model document discusses the model-owned questions (OQ-1..5, OQ-7) inline in its §1.6; this table is the single source of truth for status.

| ID        | Question                                                                                        | Part      | Owner WS | Author's lean / status                                                                                                                        |
|:----------|:------------------------------------------------------------------------------------------------|:----------|:---------|:----------------------------------------------------------------------------------------------------------------------------------------------|
| **OQ-1**  | "recursive" intended as **recurrent** (temporal), not tree-recursive?                           | A§0.5     | WS-0     | **Resolved (Paul 2026-06-06): recurrent confirmed** — the relevant special case of recursive NNs                                              |
| **OQ-2**  | Does R5 ("capability over simplicity") override C1 (first-principles) where they conflict?      | A§1.6     | WS-0     | **Resolved (Paul): neither overrides — both bind.** The tension is real and deliberately acknowledged;                                        |
|           |                                                                                                 |           |          | -- C1's transparency is *complementary to* (it enables) R5's capability — exposing low-level structure is what lets most                      |
|           |                                                                                                 |           |          | -- capable Juniper NNs reach real-world problems. Balance the two per problem location and document the balance struck.                       |
| **OQ-3**  | Framework hosting 3 unit types, or single-model (RCC only) first?                               | A§1.5/1.6 | WS-0     | **Resolved (Paul): framework, RCC-first** — endorsed as a cleaner/lower-risk path to the *full* requirement set;                              |
|           |                                                                                                 |           |          | -- RCC-only is a sequencing step, **not** a reduced final scope. **Model pick RESOLVED (OQ-4, 2026-06-14): P3-C/LMU + Approach-C** (P1/RCC = cheap hidden-recurrence increment)                                      |
| **OQ-4**  | Ship RCC despite star-free ceiling (benign for regression)?                                     | A§1.6     | WS-0     | **RESOLVED 2026-06-14 (Paul): the star-free ceiling is NOT binding** — the dataset audit found no Juniper dataset requires a ceiling-break (exception list empty);                              |
|           |                                                                                                 |           |          | -- **Model pick = P3-C / LMU + Approach-C** (Δt-native continuous-time memory); design of record = companion §0.6/§2–§4; ship fixed-order first (OQ-20). |
|           |                                                                                                 |           |          | -- Knorozova & Ronca (AAAI 2024, arXiv:2312.09048): recurrent cascades = **exactly** star-free, remedy = group-implementing units;            |
|           |                                                                                                 |           |          | -- P1/RCC retained as the cheap hidden-recurrence increment; ESN/NEAT evaluated and not selected; P2/P7 group-unit ceiling-break deferred (trigger-gated).                                                                        |
| **OQ-5**  | First CLI/datasets (Mackey-Glass? multi-sine? AR(p)?) — **resolve at WS-0**; WS-1 critical path | A§1.6     | WS-1     | **Resolved (Paul): juniper-data serves (not limited to) spiral, XOR/non-separable, MNIST, equities, and time-series**                         |
|           |                                                                                                 |           |          | -- **Time-series datasets — multi-sine, Mackey-Glass, AR(p).** Drives WS-1 / juniper-data#168                                                 |
| **OQ-6**  | NPZ 3-D extension additive-only; which optional keys in WS-1?                                   | 2.4/2.9   | WS-1     | Additive; `seq_lengths`+`scaling` in-scope                                                                                                    |
| **OQ-7**  | When do irregular-Δt datasets become relevant?                                                  | A§1.3.4   | WS-1     | **Resolved (Paul): GATING — irregular-Δt regression required for *completed* state, NOT deferrable**                                          |
|           |                                                                                                 |           |          | -- (intermediate phasing is fine, but completion requires it). The LMU's solver-free ZOH path (A§1.3.4) keeps it C1-clean;                    |
|           |                                                                                                 |           |          | -- the long pole is the data contract (Δt note §6 / juniper-data#168).                                                                        |
| **OQ-8**  | Migrate spiral/recurrence CLI problems into juniper-data?                                          | 2.9       | WS-1     | Lean yes (per C3)                                                                                                                             |
| **OQ-9**  | Two packages vs. one combined `juniper-core`?                                                   | 2.9       | WS-2/3   | Two                                                                                                                                           |
| **OQ-10** | Abstract model interface: new package vs. inside cascor first?                                  | 2.9       | WS-3     | New package, 2-implementer design                                                                                                             |
| **OQ-11** | Is recurrent unit training parallelizable via cascor's worker protocol?                         | 2.9       | WS-3     | Unknown — investigate                                                                                                                         |
| **OQ-12** | Conformance kit packaging (pytest plugin vs. `[test]` extra)?                                   | 3.7       | WS-3     | **RESOLVED (D7):** installable subclass-base kit + thin per-repo wrapper; shipped in model-core 0.1.0                                                                                                                     |
| **OQ-13** | Cascor golden-test substrate: trajectory hash vs. tolerance?                                    | 3.7       | WS-6     | Tolerance (nondeterminism)                                                                                                                    |
| **OQ-14** | Performance acceptance bands for a research model?                                              | 3.7       | WS-T     | TBD with Paul                                                                                                                                 |
| **OQ-15** | Service port assignment (proposed host 8211→ctr 8210)?                                          | 2.6       | WS-7     | Confirm no conflict                                                                                                                           |
| **OQ-16** | Recurrent env strategy: dedicated `JuniperRecurrent` (LIBTORCH hook) or reuse `JuniperCascor1`? | 8.3       | WS-4     | Dedicated env if CPU-torch (needs the isolate hook); else reuse `JuniperCascor1`                                                              |
| **OQ-17** | TestPyPI soak duration for `service-core`/`model-core` before the cascor docker lock pins them? | 8.3/8.4   | WS-2/6   | Reuse the meta-package "install lightest extra after bare" verify; fixed window TBD                                                           |
| **OQ-18** | On-host recurrence port: 8211 (host-port mirror) vs 8202 (next-free)?                              | 8.4       | WS-4/7   | 8211 (mirrors cascor's on-host 8201); ties to OQ-15                                                                                           |

**Standing uncertainties (not resolvable by decision — flagged honestly):**

- RCC's exact original experiment figures are **secondary-sourced** (scanned PDF unreadable); the *mechanism* and *task types* are well-corroborated.
- **All cascor-integration claims for non-RCC architectures (ESN/LMU/LSTM/etc.) are `[speculative]`** — no published hybrid exists. The framework framing makes them tractable, but they are novel research, not known-good patterns.
- The "modern growing-RNN literature is thin" finding is an absence-of-evidence judgment from bounded searches, not a proof of absence.
- Exact cascor source line numbers were intentionally **not** treated as load-bearing; module/behavior-level coupling is corroborated by `juniper-cascor/AGENTS.md`, but precise call sites need implementation-time confirmation.

---

## Part 6 — Sources & References

> **⚑ CROSS-CUTTING (review):** internal sources and the method note are housed here; the **external literature survey (§6.2 of the original) moved to the companion model document** (it is overwhelmingly model-related).

### 6.1 Internal Juniper sources (consulted, with paths)

| Source                             | Path                                                                                                                      | Used for                                                              |
|------------------------------------|---------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Cascor architecture & conventions  | `juniper-cascor/AGENTS.md`                                                                                                | §2.1–2.2 seam, conventions, testing                                   |
| Cascor model↔service seam          | `juniper-cascor/src/api/lifecycle/manager.py`, `src/api/routes/**`, `src/snapshots/**`                                    | §2.1 coupling (module-level)                                          |
| Cascor architecture guide          | `juniper-cascor/notes/ARCHITECTURE_GUIDE.md`                                                                              | Context (not deep-read)                                               |
| Research philosophy (canonical)    | `juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md`                                                      | C1, platform thesis, §0.3                                             |
| Architectural design journal       | `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` (ideas #2 Common-API, #4 New-ABC, #5 ABC-client, #7 split-cascor) | §2.1–2.3 prior intent, ABC, split-cascor; #5 ↔ juniper-recurrence-client |
| Multi-network orchestration design | `juniper-ml/notes/PHASE_6E_MULTI_NETWORK_DESIGN.md`                                                                       | "network populations" context                                         |
| Observability exports (0.3.x)      | `juniper-ml/juniper-observability/juniper_observability/**`                                                               | C4, reuse inventory                                                   |
| Shared-package template            | `juniper-ml/juniper-{config,ci,doc}-tools/**`, `juniper-ml/pyproject.toml`                                                | §2.3 packaging/pin convention                                         |
| Data service & contract            | `juniper-data/juniper_data/**` (generators/, api/routes/datasets.py, core/split.py)                                       | §2.4 gap analysis                                                     |
| Data client                        | `juniper-data-client/juniper_data_client/client.py`                                                                       | §2.4 client surface                                                   |
| Canopy coupling & BackendProtocol  | `juniper-canopy/src/{main.py,backend/protocol.py,backend/*adapter*.py,frontend/components/**}`                            | §2.5                                                                  |
| Ecosystem conventions              | `Juniper/AGENTS.md`, `juniper-ml/AGENTS.md`                                                                               | C2–C5, ports, worktrees                                               |
| (Note) `prompt116_2026-05-31.md`   | `juniper-ml/prompts/`                                                                                                     | This task's own archived brief — *not independent prior art*          |

### 6.2 External sources (literature survey)

Moved to the companion model document (§"Sources — external literature survey"). All citations verified by the Round-1 research agents; caveats in Part 7.

### 6.3 Method / tooling

final choice pending ongoing analysis/discussion/lit-eval, resolving in dedicated doc/section (cf. #377 RCC OQ-4 proposals, #386 handoff).
Grounding + literature surveys conducted via independent sub-agents (read-only `Explore` for code; `general-purpose` with web/arXiv/Hugging Face paper search for literature), each required to cite primary sources and self-flag unverifiable claims. Local verification via repository inspection. See Part 7.

---

## Part 7 — Verification Log

> **⚑ CROSS-CUTTING (review):** the verification log records the Round-1 pass over the **original combined draft** (before the 2026-06-03 split). It is reproduced here in full and is canonical for both halves. Future re-verification rounds (e.g. after the OQ-4 model-pick redesign) should be appended here.
>
> The brief mandates **multiple independent sub-agents to validate all aspects** and **integrate valid changes**. This section records what the verification pass checked, what it found, and what was corrected.

### Round 1 — initial multi-agent verification (2026-05-31)

**Status: COMPLETE.** Five independent adversarial sub-agents each verified a distinct lens against the *primary sources / live code* (not this document's restatement). **No CRITICAL or factually-WRONG claims were found.** Citations verified accurate to an unusually high degree; every cascor / juniper-data / juniper-canopy / juniper-observability code claim was CONFIRMED against the live repositories. The valid findings below are integrated into the Parts above (across both documents).

**Verifier coverage:**

- **V1 — model claims & citations** (web/arXiv/DOI): all 13 candidate architectures + ~50 references, the RCC representational-ceiling chain, ESN/LMU/SSM/gated/continuous-time clusters.
- **V2 — cascor grounding** (live `juniper-cascor/src`): the model↔service seam, T1/T3 module existence, dual-mode shape, port, serializer, classification assumptions.
- **V3 — feasibility + internal consistency + prior-art** (doc + journal): journal quotes, WS/OQ-ID integrity, two-package acyclicity, port non-conflict, decision logic under C1.
- **V4 — data/canopy/observability/testing** (live repos): generator inventory, NPZ shape, split, BackendProtocol, observability exports + version, pin convention, pytest defenses.
- **V5 — completeness** vs. every brief deliverable.

| ID  | Lens  | Finding                                                                                                                        | Severity           | Resolution                                                                                          |
|-----|-------|--------------------------------------------------------------------------------------------------------------------------------|--------------------|-----------------------------------------------------------------------------------------------------|
| F1  | V4    | `juniper-observability` on-disk version is **0.3.0**, not the 0.3.1 the C4 pin claimed                                         | HIGH (pin)         | **Fixed** — C4 & §3.5 pin `>=0.3.0` (`MetricsAuthMiddleware` ships in 0.3.0; 0.3.1 adds IP warning) |
| F2  | V3/V5 | Header asserted a *completed* verification while Part 7 read PENDING                                                           | MEDIUM             | **Fixed** — this log populated; header now scoped to "Round 1, 2026-05-31"                          |
| F3  | V3    | §1.3 deep dives mis-numbered `1.4.x` under a `1.3` parent (no `1.4` existed)                                                   | MEDIUM             | **Fixed** — renumbered to 1.3.1–1.3.3; following sections → 1.4/1.5/1.6; all cross-refs updated     |
| F4  | V1    | Giles et al. 1995 author list incomplete (six authors)                                                                         | MINOR              | **Fixed** — §1.3.1 & §6.2 corrected                                                                 |
| F5  | V1    | LMU `O(θω/d)` not traceable to the cited paper (its stated bound is `O(d/√m)`, spiking impl)                                   | MINOR              | **Fixed** — §1.3.3 reworded; spurious big-O removed                                                 |
| F6  | V1    | Knorozova-Ronca result is for *recurrent neural cascades* (sign/tanh, +recurrent weights), applied to Fahlman's RCC by analogy | MINOR              | **Fixed** — scoping clause added in §1.3.1                                                          |
| F7  | V3    | §2.8 labelled a two-clause splice "verbatim"                                                                                   | MINOR              | **Fixed** — now "paraphrasing"; clauses quoted separately                                           |
| F8  | V2    | The classification-only assumption breaks **more** than decision-boundary (metrics history, collection, auto-snapshot-best)    | MAJOR (strengthen) | **Integrated** — §2.1 broadened; RK-6 already covers                                                |
| F9  | V5    | No per-workstream effort sizing                                                                                                | MEDIUM             | **Integrated** — Size (S/M/L) column added to Status Tracker                                        |
| F10 | V5    | Framework unit-swap mechanism unspecified                                                                                      | MEDIUM             | **Integrated** — candidate-unit-factory hypothesis added to companion §1.5                          |
| F11 | V5    | `describe_topology()` → canopy contract undefined                                                                              | MEDIUM             | **Integrated** — illustrative schema added to the §2.3 sketch                                       |
| F12 | V5    | `TrainingEvent` "subsumes" cascor events with no mapping shown                                                                 | LOW-MED            | **Integrated** — explicit event mapping added to §2.3                                               |
| F13 | V5/V3 | 5.5 KLOC stated as fact; worker-layer genericity is contingent on OQ-11                                                        | LOW-MED            | **Integrated** — tagged "[grounding estimate]" + OQ-11 contingency (exec summary, §2.2)             |
| F14 | V5    | No WS-6 kill-criterion / abort path                                                                                            | LOW                | **Integrated** — kill-criterion added to §2.7                                                       |
| F15 | V3    | OQ-15 not inline-tagged in §2.6; §6.1 idea-#5 set mismatch                                                                     | LOW                | **Fixed** — OQ-15 tag added; journal idea-#5 ↔ recurrence-client noted                                 |
| F16 | V5/V3 | OQ-5 (dataset choice) blocks the WS-1 critical path                                                                            | LOW                | **Fixed** — flagged "resolve at WS-0" in Status Tracker + OQ table                                  |
| F17 | V5    | `cascor_plotter`/`profiling`/`utils` extraction rationale missing                                                              | LOW                | **Integrated** — per-module dispositions added after §2.2                                           |

**Confirmed clean (no change needed):**

- All 13 candidate-architecture citations and the full Fahlman→Giles→Kremer→Knorozova-Ronca ceiling chain with correct DOIs/pages/venues (V1).
- The cascor model↔service seam:
  - monkey-patched `fit()`
  - `hidden_units`/`input_size`/`output_size` introspection
  - hardcoded `CascadeHDF5Serializer`
  - the 2-D/`argmax` decision-boundary
  - dual-mode `server.py`+`main.py`
  - env prefix `JUNIPER_CASCOR_`
  - default port 8200
  - all T1/T3 module existence (V2)
- The 9 classification-only 2-D generators, the `X.shape[1]` NPZ assumption, and the shuffling split (V4); canopy's `BackendProtocol` + demo/service backends + the reusable/adapt/replace split (V4)
- Every observability export named in C4/§3 and the *mixed* pin convention (V4)
- pytest autoload + orphan-reaper defenses and the 80% gate (V4)
- The two-package split's characteristics: (following soundly from the scoring under C1 (V3)):
  - acyclicity
  - component-boundary consistency
  - 8210/8211 port non-conflict
  - plus the top-3 recommendation
  following soundly from the scoring under C1 (V3)
- all WS/OQ IDs defined; all journal prior-art quotes accurate (V3); every brief deliverable FULLY or PARTIALLY met (V5).

**Residual `[unverified]` / `[speculative]` items (by design, not defects):** RCC time-series-*regression* benchmark (none published); all non-RCC cascor-integration hypotheses (no published hybrid exists); RCC's exact 1990s experiment counts (image-only scanned PDF); the unit-swap interface (design hypothesis, pending ≥2-implementer validation). These are intentionally surfaced, not hidden.

> **Pending — Round 2 (post-split / post-OQ-4):** when the OQ-4 model-pick redesign lands, re-verify (a) the revised model recommendation and any new citations, and (b) that the A/B split introduced no dangling cross-references or dropped content. Append results here.

### Round 2 — refactor-scope re-verification against live code (2026-06-04)

**Status: COMPLETE (refactor scope).**
Seven independent read-only agents re-verified this document's *refactor-half* claims against the **current** repositories (commits through 2026-06-03), under strict anti-hallucination rules: exactly one of CONFIRMED / REFUTED / DRIFTED / CANNOT-VERIFY per claim, primary-source (file:line or command output) evidence mandatory, adversarial-falsification posture, no reliance on this document's own restatement.
Scope covered the **(b)** split-integrity check the Round-1 note deferred, plus a full live-code drift sweep of Parts 0/2/3/4/5/6 and a grounding pass over both deployment stacks (feeding Part 8).
**The (a) OQ-4 model-pick re-verification remains PENDING** in the companion (model scope; gated on the OQ-4 research landing).

**Outcome:** the document is **structurally sound and was accurate when written** — no hallucinations, no dangling IDs/cross-references, the §2.3 diagram is a true DAG, and every architectural claim re-confirmed against today's code.
Three days of active development introduced the drift below; all findings are integrated **append-only** (original Parts 0–7 are left as the as-written record; this log and Part 8 carry the corrections).
Round-2 finding IDs use the `G` prefix to avoid collision with Round-1's `F1–F17`.

**Verifier coverage (Round 2):** R1 cascor seam (live `src`); R2 juniper-data gap (live); R3 canopy coupling (live); R4 shared-pkgs / observability / ports (live + juniper-deploy); R5 doc internal-consistency + cited sources; R6 on-host stack grounding; R7 docker stack grounding.

| ID | Lens     | Finding                                                                                                         | Severity                 | Resolution                                                                                                                              |
|:---|:---------|:----------------------------------------------------------------------------------------------------------------|:-------------------------|:----------------------------------------------------------------------------------------------------------------------------------------|
| G1 | R2       | **`equities` generator (juniper-data #164) landed 2026-06-03, after the content freeze.**                       | **MAJOR (load-bearing)** | **Integrated** — the Exec-Summary "single most important sequencing insight," §2.4 table, and RK-1 are **re-scoped**:                   |
|    |          | Ships regression target (`y_reg_*` next-close), time-ordered OHLCV, & temporal (non-shuffled) split —           |                          | juniper-data is no longer "cannot serve this model today" but **"~30–40% demonstrated via #164; needs generalization."**                |
|    |          | verified end-to-end (`generators/equities/generator.py:197-198,174-184` → `storage/local_fs.py:143`             |                          | WS-1 is reframed from build-from-zero to *generalize the equities pattern* (see §8.4 WS-1); RK-1 likelihood downgraded.                 |
|    |          | `np.savez_compressed(**arrays)` → data-client passthrough `client.py:554`).                                     |                          |                                                                                                                                         |
| G2 | R2       | equities closes the gap by **bypassing** the classification contract, not fixing it —                           | MAJOR (strengthen)       | **Integrated** — **reinforces RK-6**: classification assumptions are baked into routes/metadata, independently confirmed by how #164    |
|    |          | it emits a dummy one-hot `y_*` so `api/routes/datasets.py:172` (`n_classes=y.shape[1]`, `argmax`,               |                          | had to contort around them. WS-1's *architectural* work (optional `n_classes`, `task_type`, `X.ndim` dispatch, shared `temporal_split`, |
|    |          | required `class_distribution`) won't crash, and rides the real target in extra `y_reg_*` keys.                  |                          | persisted scaling, 3-D contract) is still required; the §2.4 "3-D NPZ MISSING" row stays accurate.                                      |
|    |          | X stays 2-D `(n,10)` — no 3-D windowing.                                                                        |                          |                                                                                                                                         |
| G3 | R4       | `juniper-observability` on-disk: **0.3.1**, not 0.3.0 (cascor `pyproject.toml:66` & data `:76` pin `>=0.3.1`).  | LOW (pin)                | **Integrated** — C4/F1's "on-disk is 0.3.0" phrasing is stale; the new recurrence app should pin **`>=0.3.1`** to match the fleet floor.   |
|    |          |                                                                                                                 |                          | (The doc's `>=0.3.0` still resolves, but sits one patch below every live sibling.)                                                      |
| G4 | R1       | New cascor seam attributes since 2026-05-31: `current_hidden_units` on the monitor (#316);                      | MEDIUM                   | **Integrated** — the `describe_topology()` / `TrainingEvent` contract (§2.3) must cover these three attributes; `routes/network.py`     |
|    |          | `completion_reason` plumbed into `get_status` via model-private `_completion_reason` (#320);                    |                          | is **T3-adjacent** (model-topology-mutating) and should be classified alongside `decision_boundary.py`.                                 |
|    |          | `round_id` distributed-dispatch tagging (#321). **`api/routes/network.py`** mutates `hidden_units`              |                          | Folds into the §2.3 abstraction surface and the WS-6 acceptance criteria.                                                               |
|    |          | (POST/DELETE) but is absent from the §2.2 T3 route list.                                                        |                          |                                                                                                                                         |
| G5 | R1/R3/R4 | Precision corrections: **(a)** "~5.5 KLOC T1" is *conservative* — the 14 named `api/` files are ~5.0 KLOC,      | LOW                      | **Integrated** — (a) effort sizing for WS-2/WS-6 should budget against the larger figure; (b) §3.1/§3.4 wording corrected —             |
|    |          | adding `log_config/`+`profiling/`+`utils/` brings T1 to ~8.3 KLOC; **(b)** canopy's UI-test isolation is        |                          | the carried-forward constraint is "POST to the param endpoint + an isolated, separately-invoked UI subsuite";                           |
|    |          | **path-exclusion (`--ignore=src/tests/ui`) + a separate CI job**, *not* "plugin-autoload blocking";             |                          | (c) noted in the §2.3 pin discussion.                                                                                                   |
|    |          | **(c)** "ci-tools floor-only" pin claim holds in `pyproject.toml` but consumer CI workflows cap it `<0.5.0`     |                          |                                                                                                                                         |
| G6 | R5       | Split-integrity (the Round-1-deferred **(b)** check): WS-0..8/WS-T, OQ-1..15, RK-1..13, F1..17, C1..5           | — (clean)                | **No change** — the A/B split introduced no dangling cross-references or dropped content. (Sole nuance: journal idea #5's literal title |
|    |          |                                                                                                                 |                          | is "New juniper-cascor Client"; the doc's "ABC-client" shorthand is a faithful paraphrase.)                                             |
| G7 | R4/R7    | Port proposal **host 8211 → ctr 8210 confirmed free** (OQ-15) across `docker-compose.yml` & published port set. | LOW                      | **Integrated** — OQ-15 resolves to host 8211 / ctr 8210; §8 records the on-host 8200 collision and recommends on-host recurrence bind      |
|    |          | Nuance: **8210 is already the cascor-worker's container-internal health port** (no host mapping → no conflict). |                          | **8211** (mirroring cascor's on-host 8201 = the docker *host* port).                                                                    |
|    |          | On-host, **8200 is occupied by `duplicati-serve`** — cascor stays on 8201 (forced by plant_all).                |                          |                                                                                                                                         |

**Process note:** this document was **merged to `main` (juniper-ml #344, `22c32bd`)** during the Round-2 pass; it is now canonical (no longer branch-only). Round-2 was produced from a fresh worktree off `origin/main`.

**Still PENDING (unchanged):** Round-2 **(a)** — re-verification of the OQ-4 model-pick redesign and any new model citations — remains open in the companion model document.

---

## Part 8 — Migration & Cutover Path: Preserving the On-Host and Docker Stacks

> **⚑ CROSS-CUTTING (review):** added 2026-06-04 (Round 2). §2.7 specifies *what order to build the workstreams*; **Part 8 specifies how to ship each step without taking down a running deployment.** It is grounded in a live read of both stacks (Round-2 verifiers R6 on-host, R7 docker) and is canonical for rollout operations. It changes **no** architecture in Part 2 — it is the operational wrapper around it.

### 8.0 The two stacks (current ground truth)

**On-host stack** — `util/juniper_plant_all.bash` starts services sequentially, each gated on `/v1/health` before the next, after `conda activate`-ing a per-service env:

| Service               | Conda env (Python)                  | Launch                             | On-host bind                                        | Health                |
|-----------------------|-------------------------------------|------------------------------------|-----------------------------------------------------|-----------------------|
| juniper-data          | `JuniperData` (3.14)                | `uvicorn juniper_data.api.app:app` | `0.0.0.0:8100`                                      | `:8100/v1/health`     |
| juniper-cascor        | `JuniperCascor1` (3.13, torch 2.11) | `cd src; python server.py`         | `127.0.0.1:8201` (forced via `JUNIPER_CASCOR_PORT`) | `:8201/v1/health`     |
| juniper-canopy        | `JuniperCanopy1` (3.13)             | `cd src; python main.py`           | `127.0.0.1:8050`                                    | `:8050/v1/health`     |
| juniper-cascor-worker | `JuniperCascor1`                    | console-script (WS client)         | health `127.0.0.1:8210/v1/health/ready`             | (no inbound app port) |

Teardown: `util/juniper_chop_all.bash` (reads `JuniperProject.pid`). **Hazards (R6):** cascor's *default* port 8200 is occupied on-host by `duplicati-serve` — the stack only works because plant_all forces 8201; **`JuniperCascor1` has no LIBTORCH activate hooks** (only `JuniperCanopy1` does), so a fresh torch-using `JuniperRecurse` env replicating the CPU-torch pattern would need the isolate hook copied in; the `get_cascor_*.bash` utilities read **`CASCOR_HOST`/`CASCOR_PORT`** (not `JUNIPER_CASCOR_*`).

**Docker stack** — `juniper-deploy/docker-compose.yml`; 4 images **built** from sibling repos (data/cascor/canopy/worker), infra **pulled** (prometheus/grafana/alertmanager/redis); profiles `full | demo | dev | test | observability`:

| Service               | Build/Image                      | host:ctr         | depends_on        | profile            |
|-----------------------|----------------------------------|------------------|-------------------|--------------------|
| juniper-data          | build `../juniper-data`          | 8100:8100        | —                 | full,demo,dev,test |
| juniper-cascor        | build `../juniper-cascor`        | 8201:8200        | data (healthy)    | full,dev,test      |
| juniper-cascor-worker | build `../juniper-cascor-worker` | none             | cascor (healthy)  | full,test          |
| juniper-canopy        | build `../juniper-canopy`        | 8050:8050        | data,cascor,redis | full,test          |
| prometheus / grafana  | pulled                           | 9090 / 3001:3000 | —                 | observability      |

Validation: `docker compose --profile full config` (exits 0 today); `make up && make wait && make health`; `make test` (3-service e2e in `tests/test_full_stack.py`).

### 8.1 Why the two stacks need different handling — the dependency-resolution asymmetry

This is the crux of the entire migration. The two new packages reach the two stacks by **incompatible mechanisms**:

|                                     | On-host                                                                      | Docker                                                                                                                                       |
|-------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| How `juniper-*` deps arrive         | **editable** `pip install -e` from the local sibling repo into the conda env | **PyPI wheels** pinned in `requirements.lock`; build context is the single repo (no sibling source copied in)                                |
| To introduce a new shared package   | `pip install -e <new-repo>` into each consuming env                          | **publish to PyPI/TestPyPI _first_**, then add the pin, **regenerate `requirements.lock`**, rebuild the image                                |
| Failure mode if the step is skipped | `ImportError` at service boot → `/v1/health` never comes up                  | **build stays green, container dies at runtime** with `ModuleNotFoundError` (pin is in `pyproject.toml`, package absent from the locked set) |

**Two consequences that shape every step below:**

1. **Publish-first is mandatory.** No consumer — on-host *or* docker — pins `juniper-service-core`/`juniper-model-core` until those packages are on PyPI (TestPyPI soak first, per the meta-package extras-resolution verify convention). The docker stack physically cannot build otherwise.
2. **The `pyproject.toml` pin and the `requirements.lock` regen must land in the _same change_.** The single highest-risk docker action in the refactor is bumping a pin without regenerating the lock — `docker compose build` succeeds, then the container `ModuleNotFoundError`s at startup while the *build* reported healthy. Use the documented lock-regen recipe (`rm -f requirements.lock`, or compile-to-`/tmp`-then-`mv`) to avoid the self-pin trap.

### 8.2 Invariants — must hold green after EVERY step

- **On-host:** `juniper_plant_all.bash` brings all services to healthy `/v1/health`; cascor still binds **8201**; `get_cascor_*.bash` still answer.
- **Docker:** `docker compose --profile full config` exits 0; `make up && make wait && make health` green; `make test` (3-service e2e) green.
- **Data contract:** the 2-D NPZ path is **byte-identical** for existing cascor (RK-9); pre-existing artifacts still load.
- **Behavior:** cascor's observable behavior is unchanged until WS-6 is *explicitly* triggered and passes its golden-regression gate.

### 8.3 Cross-cutting pre-flight (once, before any workstream touches a consumer)

- **Publishing rail.** Add `publish-service-core.yml` / `publish-model-core.yml` (clone `publish-observability.yml`; trigger on `juniper-service-core-v*` / `juniper-model-core-v*`). **Verify each with `gh workflow run` immediately** — a workflow can pass yamllint yet fail first execution (RK-10).
- **On-host env hygiene** (clears latent drift the migration would otherwise trip on — all found by R6):
  - Bump `JuniperCascor1`'s editable `juniper-observability` **0.2.0 → ≥0.3.1** (the env is currently *below* cascor's own pyproject pin).
  - Re-point 3 **stale editable installs** (`juniper-cascor-client`, `juniper-ci-tools`, `juniper-data`) that reference deleted worktree paths to live repos (else a later `pip install -e` resolves an inconsistent env).
- **Recurse env decision** ([OQ-16]). New `JuniperRecurse` env (copy the LIBTORCH isolate hook if it uses CPU-torch) vs reuse `JuniperCascor1`.
- **Docker hygiene.** Confirm the lock-regen recipe; plan to delete `docker-compose.cw05-stopgap.yml` (it bind-mounts cascor `src` into the worker) once the shared-package extraction removes its reason to exist.

### 8.4 Per-workstream cutover runbook

Each step lists **precondition → on-host actions → docker actions → verification gate → rollback**. Order follows §2.7; the defining principle holds — **prove the template on greenfield recurrence before touching production cascor.**

**WS-1 — juniper-data: time-series + regression** (additive; critical path; now ~30–40% demonstrated via #164).

- *Re-scope (Round-2 G1/G2):* generalize the equities-demonstrated patterns rather than build from zero — promote its temporal split into a reusable `core/temporal_split`; make `DatasetMeta.n_classes`/`class_distribution` optional and add `task_type`; add `X.ndim` dispatch in `api/routes/datasets.py`; persist scaling params; and add the deterministic synthetic generators ([OQ-5] multi-sine / Mackey-Glass / AR(p)) that real-market, network-dependent equities cannot be.
- *On-host:* pure-Python additive changes in the `JuniperData` env; **no env or launcher change**, no new import.
- *Docker:* `juniper-data` image rebuild picks up new code. **No new external dependency** unless a synthetic generator needs a new lib (then: pin + regen `juniper-data/requirements.lock` in the same change).
- *Gate:* 2-D artifacts load byte-identical (RK-9); property test `max(train_time) < min(test_time)`; on-host `curl :8100/v1/health`; docker `docker compose build juniper-data && make test`.
- *Rollback:* additive keys only → revert the generator/route commit; existing artifacts unaffected.

**WS-2 — extract `juniper-service-core` (T1 infra) + publish. Cascor NOT yet repointed.**

- *Clarification the migration surfaces:* §2.7 step 2 / RK-5 describe cascor "adopting behind a no-op shim." To honor the overriding *greenfield-first* principle, **the cascor→service-core repoint is deferred to the start of WS-6** (behind the golden gate). At WS-2, service-core is extracted and **published**, but **cascor keeps its own `src/api/**` copy** and is byte-unchanged on both stacks. The first real consumer is recurrence (WS-4).
- *On-host:* nothing changes for cascor/canopy/data. (`pip install -e juniper-service-core` happens only in the recurrence env, at WS-4.)
- *Docker:* no consumer image changes. service-core's own CI builds/tests it standalone (clone the `juniper-observability` package-test + publish gating; add a **drift-lint** clone of `test_doc_tools_drift.py`).
- *Gate:* service-core unit + contract tests green (a stub model drives every generic route); TestPyPI install verification; **both stacks untouched → re-run the §8.2 invariants to prove zero impact.**
- *Rollback:* delete the package + workflow; nothing depends on it yet.

**WS-3 — define `juniper-model-core` interfaces + conformance kit + publish.** Same shape as WS-2 (design + tests + publish; no consumer repoint; both stacks untouched). The conformance kit ships as an installable pytest plugin ([OQ-12]). *Gate:* kit self-tests green against a reference stub; both-stack invariants unchanged.

**WS-4 — build `juniper-recurrence` greenfield** (FIRST real consumer; this validates the template).

- *On-host:* create/select the recurrence env; `pip install -e juniper-service-core juniper-model-core juniper-recurrence` into it.
  - Add a launch block to `plant_all.bash` mirroring the cascor block (constants, pre-flight `check_port_available`, `cd src; python server.py`, `wait_for_health`, a `juniper-recurrence=PID` line in the PID writer).
  - **On-host bind = 8211** (mirrors cascor's on-host = the docker *host* port; 8200 is duplicati, 8210 is the worker health port — avoid both; [OQ-18]).
  - `chop_all.bash` needs no change (it iterates the PID file); only the `--systemd` reverse-order list would.
- *Docker:* add `juniper-recurrence/Dockerfile` cloning the **worker's CPU-lock two-stage pattern** (NOT cascor's — cascor's lock pulls the full CUDA stack → 7.5 GB image); `EXPOSE 8210`; recurrence's own `requirements.lock` pins service-core/model-core/data-client/observability from PyPI.
  - Add a compose service block after canopy (build `../juniper-recurrence`; `ports "${BIND_HOST:-127.0.0.1}:${RECURSE_HOST_PORT:-8211}:${RECURSE_PORT:-8210}"`; `JUNIPER_DATA_URL`; metrics trusted-IPs; `juniper_data_api_keys` secret mount; `depends_on: juniper-data healthy`; healthcheck `:8210/v1/health/ready`; `networks: [backend, data]`).
  - Add `RECURSE_PORT`/`RECURSE_HOST_PORT` to `.env.example`; add `juniper-recurrence:${RECURSE_HOST_PORT}` to `scripts/health_check.sh` `SERVICES=` and `wait_for_services.sh`; add a prometheus scrape job to **both** `prometheus.yml` and the hand-mirrored `prometheus.demo.yml`.
- *Gate:* **the conformance kit is the acceptance test** — recurrence's model passes every `TrainableModel`/`GrowableModel` assertion and traverses every generic route as a *regression* model (no `argmax`, no accuracy).
  - On-host `curl :8211/v1/health` + PID line present.
  - Docker `docker compose build juniper-recurrence && docker compose --profile full up -d juniper-recurrence && curl :8211/v1/health/ready`; `docker compose exec juniper-recurrence python -c "...reach juniper-data:8100..."`; prometheus target `up`.
  - **Existing services untouched → §8.2 invariants still green.**
- *Rollback:* remove the compose block + plant_all block; recurrence is isolated, nothing else depends on it.

**WS-5 — generalize canopy + recurrence backend** (moderate; UI).

- *On-host / Docker:* canopy gains a `juniper-recurrence-client` backend behind the existing `BackendProtocol`; conditional/schema-driven panels (render decision-boundary/candidate/cascade only when the backend advertises them). Add `JUNIPER_CANOPY_RECURSE_SERVICE_URL` to the on-host launcher + compose env + `.env.example`.
- *Gate:* canopy unit + the **isolated, separately-invoked** UI subsuite (Round-2 G5: POST to the param endpoint; `--ignore=src/tests/ui` + a separate job — *not* autoload-blocking); regression backend → MSE panel, no decision-boundary. The cascor path is unchanged → existing canopy↔cascor stays green on both stacks.
- *Rollback:* the recurrence backend is additive behind the protocol; revert leaves cascor monitoring intact.

**WS-6 — refactor cascor onto shared packages** (DEFERRED; trigger-gated; the only behavior-risky step).

- *Trigger (unchanged):* WS-4 shipped **and** a cascor golden/snapshot regression suite + the conformance suite are green for cascor.
- *Step 6a — service-core repoint (mechanical):* cascor's `src/api/**` become thin re-export shims importing from `juniper_service_core` (the "no-op shim").
  - **On-host:** `pip install -e juniper-service-core juniper-model-core` into `JuniperCascor1` **before** re-running cascor — R6's single riskiest on-host action; skip it and boot dies at import.
  - Launcher unchanged (`cd src; python server.py` still resolves).
  - **Docker:** add the pins to `juniper-cascor/pyproject.toml` **and regenerate `juniper-cascor/requirements.lock` in the same commit**; `docker compose build --no-cache juniper-cascor`; `up -d` and **grep the container log for `ModuleNotFoundError`** (catches the build-green/runtime-red gap).
- *Step 6b — model-core interface adoption (behavioral):* the lifecycle/routes stop naming `CascadeCorrelationNetwork` and operate against `TrainableModel`/`GrowableModel`; the new seam attributes (G4: `current_hidden_units`, `_completion_reason`, `round_id`) and `routes/network.py` are covered by `describe_topology()`/`TrainingEvent`.
- *Gate:* the **pre-captured golden suite + conformance kit must stay green** (training trajectories on two-spiral at fixed seed; API response snapshots; HDF5 round-trips).
  - On-host: `python -c "import juniper_service_core, juniper_model_core"` in the env, then `cd src; python -c "import api.app"`, then plant_all + full health + `get_cascor_status`.
  - Docker: `make test` (3-service e2e) green.
- *Kill-criterion (unchanged):* if the conformance suite cannot be made green for cascor without changing observable behavior, **WS-6 is abandoned** — cascor keeps its own service stack, recurrence still benefits, the one-sided extraction is documented.
  - Both stacks revert to the WS-5 state (cascor never repointed), which stayed green throughout.
- *Rollback:* because 6a/6b land as separate commits behind the golden gate, revert to cascor's own `src/api` copy (still present until WS-6) — on-host the editable installs are inert if unused; docker rebuilds from the reverted lock.

**WS-7 — deploy / meta-package integration.** Add `juniper-recurrence-client` to `juniper-ml` extras + the two shared packages to `[tools]`/`[all]`; **update `test_pyproject_extras.py` in the same PR** (the lint fails otherwise). Land shared-CI/extras edits in **dedicated PRs** (RK-11 concurrent-session race). **WS-8** (recurrence-worker) deferred.

### 8.5 Rollout ordering & the both-stacks-green ladder

The safe global order — every rung leaves both stacks fully operational:

1. Pre-flight (publish rail + env hygiene) — no consumer touched.
2. **WS-1** data (additive; 2-D path byte-identical).
3. **WS-2 / WS-3** publish service-core + model-core — *no consumer repointed* (both stacks untouched; the key de-risking move).
4. **WS-4** recurrence — a *new* service added to both stacks; existing services untouched.
5. **WS-5** canopy recurrence backend — additive behind `BackendProtocol`.
6. **WS-7** deploy / meta-package.
7. **WS-6** cascor cutover — *last*, trigger-gated, golden-guarded, kill-criterion-bounded, under the publish-first + pin-and-lock-together rules of §8.1.

Because cascor (the production system, and the most-coupled node in both stacks) is repointed **only at the final, gated step**, the stacks are green at every rung 1–6 by construction, and rung 7 is reversible to rung 6's green state.

### 8.6 Open questions — migration (folded into the Part 5 canonical table 2026-06-07)

- **[OQ-16]** Recurse env strategy on-host: dedicated `JuniperRecurse` (with copied LIBTORCH hook) vs reuse `JuniperCascor1`? (Affects torch isolation and the `pip install -e` surface.)
- **[OQ-17]** TestPyPI soak duration for service-core/model-core before the cascor (WS-6) docker lock pins them — reuse the meta-package "install lightest extra after bare" verify, or a fixed soak window?
- **[OQ-18]** On-host recurrence port: **8211** (host-port mirror, recommended) vs 8202 (next-free) — confirm against any future on-host service map; ties to [OQ-15].

---

*End of refactor document. This is a living plan — the Status Tracker, Open-Questions table, Verification Log, and Part 8 migration runbook above are canonical for the whole effort (both this document and the [companion model document](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md)).*
