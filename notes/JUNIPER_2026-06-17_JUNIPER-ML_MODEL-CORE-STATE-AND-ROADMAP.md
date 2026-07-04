# juniper-model-core — State Evaluation & Design/Development/Testing Roadmap

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Application**: juniper-model-core (subdirectory of juniper-ml)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0 (initial issue)
**Last Updated**: 2026-06-17

---

> **⟢ UPDATE 2026-06-23.** This is the **2026-06-17 snapshot**; its body ("0.1.0, crossval design-only")
> is now largely historical. Reality: `juniper-model-core` shipped **0.2.0 then 0.3.0** to PyPI — the
> `crossval/` layer (metrics / splits / executor) is **BUILT** (PR #442) and 0.3.0 added multi-entity
> `groups=` walk-forward folds (#472); the **D3 `predict(self, X, **kw)` drift is RESOLVED**
> (`interfaces.py`); the **coverage gate is raised to 95** (`ci-model-core.yml`); and the parent Status
> Tracker was reconciled (#439/#465/#466). Of the OW-* items, only **OW-12** (GrowableModel re-tighten),
> **OW-19** (`workflow_dispatch` verify), and **OW-20** (conftest autoload guard) remain genuinely open
> (all minor). Authoritative current-state: `JUNIPER_DOCS_REALITY_AUDIT_2026-06-21.md`.

## 0. Purpose and how to read this document

This document does two things, in order:

1. **Evaluates the current state of the model-core effort and validates it against the actual source code** —
   not against what the design docs *claim*. The headline finding is that the canonical workstream Status
   Tracker has drifted 5+ rows behind reality.
2. **Lays out the design / development / testing roadmap** — the consolidated outstanding-work inventory,
   multiple approach options for each genuinely-forked decision (with strengths / weaknesses / risks /
   guardrails), and a recommended phased ordering.

Every factual claim in Part 1 is grounded in either a `file:line` citation or a design-doc section, and was
cross-checked by independent sub-agents (Part 6 / Appendix B). Where a claim could not be verified from this
worktree (cross-repo state), it is marked **UNVERIFIED** rather than asserted.

**Companion documents** (the canonical specs this roadmap sits on top of):

- `notes/JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md` — the ratified 0.1.0 contract (D1–D10).
- `notes/JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md` — the 0.2.0 cross-validation / fold-executor design.
- `notes/JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md` — a **concurrent, focused** crossval 0.2.0 *build* roadmap (PR-1 mechanics + the F-CRIT-1 version/pin lint trap), produced by a parallel session. **This document is the umbrella state+roadmap; that one is the deep-dive on the crossval build (this roadmap's Phase 2 / G3).** Not present in this worktree — verify before consolidating.
- `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` — the parent program + canonical Status Tracker.
- `notes/JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md` — the placement convention (D4).
- `notes/JUNIPER_RECURRENCE_*` and `notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md` — the consumer/model side (WS-4 / WS-4b).

---

## 1. Executive summary

`juniper-model-core` is in a **healthy, shipped state for its 0.1.0 scope** and has a **single, well-designed
next increment (0.2.0) that is fully analysed but not yet built**. The work is genuinely ahead on the
*investigate / analyse / implement / test / automate* axes and genuinely behind on *design-completeness /
develop / harden / fix* for the next increment.

The most important finding is **not** a code defect — the 0.1.0 contract is clean and its 66-test suite passes
at ~97% coverage. It is a **process-tracking defect**: the canonical Status Tracker in the parent refactor doc
still lists WS-1, WS-2, WS-3, and WS-4 as `PLANNED`, when in reality model-core (WS-3) and service-core (WS-2)
are published, the data foundation (WS-1) is on disk, and the recurrence model (WS-4) already passes the
model-core conformance kit 10/10. A canonical document that trails reality by five rows will mis-sequence every
downstream decision, so **restoring documentation truth is Phase 0 of the roadmap** — cheap, zero code risk, and
a prerequisite for trusting any sequencing built on the tracker.

The single real source-vs-design discrepancy is **D3**: the decision ledger says the documented `**kw` escape
hatch lives on *both* `fit` and `predict`, but the implemented `predict` ABC (`interfaces.py:112`) has no `**kw`.
Harmless for today's models, but a predict-time-`dt` sequence model would hit it, and the cross-val design
already flags it as a candidate to fold into 0.2.0.

The headline development deliverable is the **0.2.0 cross-validation / fold-executor layer** — a model-agnostic,
numpy-only `juniper_model_core.crossval` submodule (`metrics` / `splits` / `executor`) behind an opt-in
`[crossval]` extra. Its *placement* and five `D-CV` decisions are ratified, but its concrete §4 API is explicitly
"proposed — please redline," so the roadmap separates **API ratification** (a decision) from **the build** (code)
to avoid building before the interface is final.

---

## 2. Current state — validated against source (Part 1 of the brief)

### 2.1 What model-core actually is (as-built 0.1.0)

A dependency-free model **contract** package plus a numpy-using **conformance kit**. Ten substantive modules, 21 public
symbols, published to PyPI as `0.1.0` and wired into `juniper-ml`'s `[tools]`/`[all]` extras.

| Module | Public surface | Role | Evidence |
|:-------|:---------------|:-----|:---------|
| `interfaces.py` | `TaskType`, `TrainResult`, `GrowthOutcome`, `TrainableModel`, `GrowableModel` | The frozen `TrainableModel` ABC + provisional `GrowableModel` ABC | `interfaces.py:40-46,78,145` |
| `events.py` | `TrainingEventType`, `TRAINING_EVENT_TYPES`, `TrainingEvent` | Closed 5-type event vocabulary | `events.py:15,18-52` |
| `serialization.py` | `ModelSerializer` (ABC) | Standalone save/load strategy (D6) | `serialization.py:22,25,28-34` |
| `topology.py` | `NodeKind`, `NODE_KINDS`, `TopologyNode`, `TopologyEdge`, `Topology` | Model-agnostic node/edge graph (canopy seam) | `topology.py:13-49` |
| `validation.py` | `REGRESSION_METRIC_KEYS`, `CLASSIFICATION_METRIC_KEYS`, `validate_metrics`, `validate_topology`, `legal_event_order` | Shared behaviour as inspectable free functions (C1) | `validation.py:23-117` |
| `lifecycle.py` | `TrainingLifecycleBase` (ABC) | Declared **seam only**; body deferred to WS-2 (D8) | `lifecycle.py:25,28-50` |
| `conformance/` | `ConformanceDataset`, `tiny_regression_2d/_3d`, `ReferenceLinearModel`, `ReferenceGrowableModel`, `ReferenceLinearSerializer`, `TrainableModelConformance`, `GrowableModelConformance` | Importable conformance kit + RK-6 regression canary | `conformance/{fixtures,reference,suite}.py` |

**Key load-bearing properties, all source-verified:**

- **Dependency-free contract.** `import juniper_model_core` pulls no third-party runtime dependency; numpy is
  referenced only under `TYPE_CHECKING`. A sub-agent empirically proved this by importing the package with numpy
  blocked at the meta-path (succeeds; numpy absent from `sys.modules`) while the conformance kit correctly fails.
  This is what lets the publish-verify run a clean `--no-deps` import with no `pypi.org` fallback.
- **Tests pass.** The full 66-test suite runs green in ~0.26s; the ~97% coverage figure was reproduced on a real
  run (CI gate is 85%).
- **Shipped + wired.** `juniper-model-core>=0.1.0,<0.2.0` is pinned in `pyproject.toml:55`; `ci-model-core.yml`,
  `publish-model-core.yml`, `tests/test_model_core_drift.py`, and `tests/test_pyproject_extras.py` all exist.

### 2.2 Process-lifecycle scorecard

The brief named nine lifecycle stages. Model-core's standing across them:

| Stage | Status | Evidence / note |
|:------|:-------|:----------------|
| Investigate | **DONE** | OQ-1…5, OQ-9…12 resolved; OQ-4 dataset audit closed the star-free-ceiling question. |
| Analyse | **DONE** | Tier analysis, RK-1…11, the D1–D10 ledger, and the 0.2.0 gap analysis all complete. |
| Design | **PARTIAL** | 0.1.x ratified+built; 0.2.0 *placement* ratified but its §4 API is "proposed — please redline"; `GrowableModel` provisional. |
| Develop | **PARTIAL** | 0.1.0 contract + kit developed; lifecycle is a seam; 0.2.0 crossval + advanced lifecycle undeveloped. |
| Implement | **DONE** | 11 modules + kit; 9/10 ledger decisions observable in code (D3 partial); reference models dogfooded. |
| Test | **DONE** | 66 tests green, ~97%, dep-free-import subprocess test, kit dogfooded + live LMU 10/10. Route-traversal + 0.2.0 matrix unwritten. |
| Automate | **DONE** | CI + publish workflows green; drift/extras lints run in `ci.yml`. Polish follow-ups remain. |
| Harden | **PARTIAL** | Dep-free boundary proven; RK-6 canary in kit; no-fallback publish-verify. Open: OW-10, OW-17, OW-20. |
| Fix | **PARTIAL** | D3 `predict` kwarg mismatch (OW-4) + doc-staleness cluster (OW-1/2/3). **No functional bug in 0.1.0.** |

### 2.3 Reconciliation — what the docs claim vs. what the source shows

Drift and stale entries first; confirmations after. Full matrix in Appendix A.

| Verdict | Claim | Source | Actual (verified) | Impact |
|:--------|:------|:-------|:------------------|:-------|
| **STALE** | Status Tracker lists WS-1/2/3/4 as `PLANNED` | refactor doc L47-50 | WS-3 model-core 0.1.0 published (verified in-worktree); WS-2 service-core published, WS-1 generators on disk, WS-4 LMU conformance 10/10 (cross-repo / memory-derived — see OW-11) | Canonical doc mis-sequences work. **Primary fix.** |
| **DRIFT** | WS-4 row names `juniper-recurse` / RCC | refactor doc L50 | OQ-19 renamed → `recurrence`; OQ-4 picked the LMU, not RCC; on-disk repo is `juniper-recurrence` | Part 8 cutover runbook names are stale |
| **DRIFT** | D3 = `**kw` on `fit` **and** `predict` | interface design §3 | `fit` has `**kw` (`interfaces.py:99`); `predict` ABC (`interfaces.py:112`) has none | Harmless now; a predict-time-`dt` model would hit it |
| **CONFIRMED** | 0.1.0 on PyPI; pinned `:55`; tests + workflows exist | orchestrator | All confirmed; suite ran green; 97% coverage reproduced | WS-3 complete |
| **CONFIRMED** | No crossval code; 0.2.0 unbuilt | orchestrator | `grep` clean; no `crossval` extra; `_version` is `0.1.0` | 0.2.0 is design-only |
| **CONFIRMED** | Ledger honoured; D4 placement OK; LMU 2nd impl 10/10 | multiple | 9/10 decisions in code; model-core is a `juniper-ml` subdir using subclass+inject; recurrence conformance passes 10/10 | Contract integrity high; several tracker rows *understate* reality |
| **RESOLVED** | WS-4b app merge state | orchestrator vs. survey vs. concurrent session (2026-06-17) | PR #6 (skeleton) on `main`; #7 (routes) / #8 (publish) merged into **stacked branches stranded off `main`**; app **not on PyPI**. Cross-repo — confirm live | WS-4b is *partially* landed, not done; OW-11 narrows to a live confirm + re-land |

### 2.4 Verification method

The state evaluation was produced by six independent survey sub-agents (source map + D1–D10-in-code; tests/CI/
publish/extras; each of the three named design docs; cross-doc dependencies) feeding a reconcile synthesizer,
cross-checked against the orchestrator's own first-hand reads of `interfaces.py`, `lifecycle.py`, the cross-val
design, and the parent Status Tracker. Agents were instructed to *independently verify* preliminary findings
rather than echo them; the D3 drift, the dependency-free property, and the 66-test pass were each reproduced by
an agent. Provenance detail is in Appendix B.

---

## 3. Outstanding-work inventory (Part 2 of the brief)

Twenty deduped items, grouped by theme, sized **S** (≈ days / one PR), **M** (≈ 1–2 weeks), **L** (≈ 3+ weeks /
multi-PR). "Dep" = the item(s) that must land first.

### G1 — Documentation truth restoration (doc)

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-1 | Update the refactor Status Tracker (L42-55): WS-1/2/3 → `SHIPPED`, WS-4 → `SHIPPED`/`IN REVIEW`, WS-7 / WS-T → `IN PROGRESS`; close OQ-12; bump doc version | S | OW-11 | Primary deliverable; tracker trails reality 5+ rows |
| OW-2 | Reconcile nomenclature `juniper-recurse`/RCC → `juniper-recurrence`/LMU (per OQ-19 + OQ-4) across WS-4/8 rows, diagrams, Part 8 | S | — | On-disk truth is `juniper-recurrence` |
| OW-3 | Refresh the interface-design header ("pre-WS-0-ratification") + §10 item 5 (WS-0 gate) to "WS-0 RATIFIED 2026-06-14" | S | — | Doc-internal staleness |

### G2 — Contract hygiene (fix / design)

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-4 | Resolve the D3 drift: add `**kw` to the `predict` ABC (target 0.2.0) **or** amend the ledger to "`fit`-only" | S | — | `interfaces.py:112` vs. interface design §3 |
| OW-12 | Re-tighten `GrowableModel` / `grow_step` against a *real* second growable implementer before freezing it | M | — | **OWED but DE-PRIORITIZED:** WS-4 LMU is `TrainableModel`-only; only the kit canary implements `GrowableModel`; RCC is off the near-term path post-OQ-4 |

### G3 — Cross-validation 0.2.0 (the headline dev work)

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-5 | **Ratify the §4 cross-val API** (`walk_forward_folds`, `Fold`/`FoldResult`/`CrossValResult`, `cross_validate`) + the open build calls: in-repo stub vs. import (D1), `predict(**kw)` bundling, metric-math home (shared `_metrics.py` vs. parity test), val-set policy, parallelism seam | S | — | Placement + D-CV-1..5 ratified, §4 API + these calls not; building first risks rework. The concurrent crossval build roadmap enumerates these open decisions |
| OW-6 | Build the `crossval/{metrics,splits,executor}` submodule (PR-1): `regression_metrics`+`score`; `Fold`+`walk_forward_folds` (expanding/rolling/embargo/order); `FoldResult`/`CrossValResult`+`cross_validate` (factory-based, serial, `aux` axis-0 slicing, `on_event`) | L | OW-5 | Keep numpy out of the base import — **never re-export `crossval` from `__init__.py`** (the `test_dependency_free_import.py` guard); `regression_metrics` math already exists in `reference.py` |
| OW-7 | **Atomic version+pin PR (F-CRIT-1):** add the `crossval` numpy extra; bump `_version`→`0.2.0`; in the **same PR** widen `juniper-ml [tools]` to `>=0.1.0,<0.3.0` + update `test_pyproject_extras.py`; CHANGELOG `[0.2.0]` | S | OW-6 | The drift + extras lints gate required CI → red if the bump ships without the pin widen. Safe pre-publish (resolves 0.1.0). Widen surgically (negative-control `test_model_core_drift.py:190`); `[all]` unaffected. Supersedes crossval §5/§7 |
| OW-8 | Write the §6 eight-test matrix (metrics known-answer, fold shape/order, leakage guard, dogfood `ReferenceLinearModel`, 3-D stub, determinism, aggregate correctness, event forwarding) | M | OW-6 | `ReferenceLinearModel` dogfood; the 3-D `TrainableModel` stub is a fresh artifact to build |
| OW-9 | Publish model-core `0.2.0` (publish-first) via `publish-model-core.yml`; consumers then opt into `crossval` on their own cadence (the `[tools]` pin already admits 0.2.0 from OW-7) | S | OW-7 | Release is Paul-driven. The `[tools]` pin-widen is NOT here — it rides with OW-7 (F-CRIT-1). The external recurrence-model `<0.2.0` pin is left alone (not lint-coupled) |

### G4 — WS-2-coupled (lifecycle body + route conformance)

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-13 | Flesh out the advanced `TrainingLifecycleBase` bodies (threaded / FSM / dataset hot-swap / worker) under WS-2 / OQ-11 | L | — | `lifecycle.run` is a docstring-only seam (D8); the substantive body — and its design fork — is owned by the WS-2 / `juniper-service-core` doc |
| OW-10 | Add the WS-2 **route-traversal conformance** layer: drive `ReferenceLinearModel` through every generic service-core route, asserting no `argmax`/accuracy leak | M | OW-13 | Gated on WS-2 routes existing; completes the RK-6 guarantee at the *route* level, not just the model object |

### G5 — Ecosystem / cross-repo integration

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-11 | Confirm the WS-4b app merge state live, then **re-land #7 (routes) / #8 (publish) on `main`** — they are stranded in stacked branches off `main`; #6 (skeleton) is on `main`; app not on PyPI | S | — | Cross-repo; state per a concurrent 2026-06-17 session — verify live before acting |
| OW-14 | WS-5: generalize canopy + the recurrence-client backend behind `BackendProtocol` | L | OW-11 | UI-facing; depends on WS-4 (satisfied) |
| OW-15 | WS-6 pre-work (**DEFERRED**): capture the cascor golden suite; make the kit green for cascor's `GrowableModel` | L | OW-12 | cascor has no model/service-core reference yet; deferral holds until the trigger |
| OW-16 | juniper-deploy half of WS-7: recurrence compose service (`8211→8210`), prometheus jobs, `env.example` port, health/wait entries | M | OW-11 | Absent from `docker-compose.yml` |
| OW-18 | Enrol `juniper-recurrence-model` into `test_model_core_drift.py`'s consumer roster so the cross-repo guard activates | S | OW-11 | Roster is empty → the subtest currently skips; recurrence-model now pins `0.1.x` |

### G6 — Hardening & automation polish

| ID | Item | Size | Dep | Note |
|:---|:-----|:-----|:----|:-----|
| OW-17 | Raise the model-core CI coverage gate `85 → ~95` | S | — | `cov-fail-under=85` vs. actual 97; uncovered = conformance stubs + a few branches |
| OW-19 | Verify both model-core workflows via explicit `gh workflow run` dispatch (RK-10) | S | — | Organic runs are green; the literal manual dispatch was never performed |
| OW-20 | Consider a `conftest.py` plugin-autoload SIGSEGV guard in model-core | S | — | Harmless today (numpy-only env); cheap ecosystem-consistency hardening |

---

## 4. Design / development approach options (Part 3 of the brief)

The genuinely-forked decisions, each with options, a strengths/weaknesses/risk read, a guardrail, and a
recommendation. Decisions that are already ratified (placement D-CV-1, the D1–D10 ledger) are **not** re-litigated
here.

### 4.A Roadmap ordering strategy

How to sequence the whole backlog. This is the highest-leverage choice.

**Option A1 — Documentation-truth-first (recommended).** Land G1 (and the cheap OW-11 cross-repo check that
feeds it) before any code, then contract hygiene + API ratification, then the 0.2.0 build, then WS-2/ecosystem.

- *Strengths:* The canonical tracker stops lying immediately (kills the top risk); every later sequencing decision
  rests on a true map; near-zero code risk; unblocks correct prioritization for *other* concurrent sessions.
- *Weaknesses:* Defers the visible feature (crossval) by one small phase.
- *Risk:* Low. The only dependency is OW-11 (cross-repo state), which is a read, not a change.
- *Guardrail:* Cap Phase 0 at one doc PR; do not let "fix the tracker" expand into re-writing the parent design.

**Option A2 — Ship-0.2.0-first.** Treat the crossval layer as the priority; fix docs opportunistically.

- *Strengths:* Fastest path to the user-visible capability both consumption routes block on.
- *Weaknesses:* Builds the most expensive item (OW-6, L) on top of an unratified API (OW-5) and a stale map;
  high rework exposure; the D3 question stays open while you build the very layer that surfaces it.
- *Risk:* Medium-high — this is exactly the "build before redline" risk (§4.C / R2).
- *Guardrail:* Would require freezing OW-5 *before* OW-6 regardless, which collapses A2 back toward A1's ordering.

**Option A3 — Contract-completeness-first.** Resolve every contract gap (D3 / OW-4, GrowableModel / OW-12, even a
speculative `score()`) before building anything on top.

- *Strengths:* Maximally clean contract before expansion.
- *Weaknesses:* OW-12 has **no second implementer to design against** — doing it now violates RK-4 (the
  two-implementer rule) and risks baking in guesses; over-invests in a frozen surface no one is pushing on.
- *Risk:* Medium — re-introduces the over-abstraction failure mode the whole design was built to avoid.
- *Guardrail:* Only pursue the *forced* contract gaps (D3, which a real consumer needs); explicitly hold OW-12.

**Recommendation: A1.** It directly retires the only high risk, is cheap, and makes every subsequent choice
trustworthy. A2's mandatory "freeze API first" step makes it converge on A1 anyway; A3 over-invests in a contract
no current implementer is straining.

### 4.B Resolving the D3 `predict(**kw)` drift (OW-4)

The ledger says `**kw` on `fit` and `predict`; the code has it only on `fit`.

**Option B1 — Add `**kw` to the `predict` ABC, bundled into 0.2.0 (recommended).** Make the code match the
ratified intent; ship it with the crossval layer that needs it.

- *Strengths:* Honours D3 as ratified; unblocks predict-time-`dt` sequence inference (the LMU's real need and the
  crossval executor's `m.predict(X[ev], **aux[ev])` call) — **provided the concrete `predict` signatures are widened
  in the same PR**: the ABC edit alone is necessary but not sufficient, since `ReferenceLinearModel.predict`
  (`reference.py:81`) and any 2-D implementer must accept-and-ignore `**kw` or the call raises `TypeError`. Additive
  and 2-D-safe once that pairing is done.
- *Weaknesses:* Touches the *frozen* `TrainableModel` ABC — but additively (a new optional `**kw` breaks no
  existing subclass).
- *Risk:* Low. Pure widening. The conformance kit's existing `predict` calls keep working.
- *Guardrail:* Land it in the same 0.2.0 PR series as crossval; add a one-line conformance assertion that
  `predict(**kw)` is accepted (ignored by 2-D models); update the §5.1 sketch in the interface design doc.

**Option B2 — Amend the ledger to "`fit`-only," leave code as-is.** Declare D3 narrower than written.

- *Strengths:* Zero code change; smallest possible action.
- *Weaknesses:* Contradicts the crossval design (which assumes `predict(**kw)`) and the LMU's inference need;
  pushes the problem to the first consumer who needs predict-time aux and forces a *later* non-bundled ABC edit.
- *Risk:* Medium — it papers over a real gap and creates a future un-batched contract change.
- *Guardrail:* Only choose this if a deliberate decision is made that no model will ever need predict-time aux —
  which the 3-D LMU already contradicts.

**Option B3 — Introduce a typed `Batch`/`SequenceData` container instead of `**kw`.** The "principled alternative"
the interface design's Appendix A flagged for D3.

- *Strengths:* Type-level enforcement of the 3-D contract; self-documenting.
- *Weaknesses:* Reverses a ratified decision (D3 chose `**kw` deliberately); larger blast radius across both
  implementers; over-engineered for the current need.
- *Risk:* Medium-high (re-opens a closed decision).
- *Guardrail:* Out of scope unless type-level 3-D enforcement becomes a stated requirement; note as a possible
  0.3 evolution, not a 0.2.0 action.

**Recommendation: B1**, bundled into the 0.2.0 PR series.

### 4.C Cross-val 0.2.0 — API-ratification vs. build ordering (OW-5 → OW-6)

The §4 interfaces are "proposed — please redline."

**Option C1 — Ratify (redline) the §4 API first, then build (recommended).** A short decision pass on the
signatures (and the two embedded sub-questions: in-repo stub vs. real LMU import for the 2nd-implementer test;
whether to bundle `predict(**kw)`), then PR-1.

- *Strengths:* Eliminates the rework risk; the build PR is mechanical once the API is frozen; lets the test matrix
  (OW-8) be written against a stable surface.
- *Weaknesses:* One extra (small) decision step before code.
- *Risk:* Low.
- *Guardrail:* Time-box the redline; the design is already concrete, so this is confirmation, not redesign.

**Option C2 — Build a thin spike, then ratify against working code.** Prototype `walk_forward_folds` +
`cross_validate` to pressure-test the signatures, then finalize.

- *Strengths:* Surfaces ergonomic problems the paper API can't; the dogfood test *is* the pressure test.
- *Weaknesses:* Risks the spike silently becoming the merged implementation without an explicit ratification gate;
  blurs OW-5/OW-6.
- *Risk:* Medium — "spike becomes product" is a known anti-pattern.
- *Guardrail:* If chosen, mark the spike branch explicitly throwaway and require a redline sign-off before PR-1
  merges.

**Recommendation: C1.** The design is concrete enough that ratification is a quick confirmation; C2's upside
(ergonomic feedback) is captured anyway by writing the dogfood test (OW-8) early against the ratified API.

### 4.D The second-implementer cross-val test — in-repo stub vs. real LMU import (sub-decision of OW-8)

The §6 matrix needs a 3-D `TrainableModel` to prove the executor is genuinely model-agnostic.

**Option D1 — In-repo 3-D `TrainableModel` stub (recommended; the design's own lean).** A tiny synthetic 3-D
model inside model-core's test tree.

- *Strengths:* Keeps model-core **dependency-clean** (no model-core → recurrence edge); fast, hermetic; no
  publish-ordering coupling.
- *Weaknesses:* Doesn't exercise the *real* LMU Δt path inside model-core's own CI.
- *Risk:* Low.
- *Guardrail:* Pair it with a recurrence-side `LMURegressor`-CV test (OW-9 follow-on) so the real model is proven
  on the consumer's side — best of both, no dependency inversion.

**Option D2 — Import the published `juniper-recurrence-model` in a `[crossval,test]` env.** Test against the real LMU.

- *Strengths:* Proves the actual 3-D Δt path end-to-end in model-core's CI.
- *Weaknesses:* Creates a model-core → recurrence test dependency (inverts the layering); couples model-core CI to
  a consumer's release cadence; heavier env.
- *Risk:* Medium (layering inversion; CI fragility).
- *Guardrail:* Only if the stub proves insufficient; even then, gate it behind an optional extra so the core test
  run stays hermetic.

**Recommendation: D1 + a recurrence-side real-LMU test.** This is what the cross-val design itself prefers.

### 4.E `GrowableModel` re-tightening timing (OW-12)

The `GrowableModel` ABC is deliberately provisional (RK-4) until a second growable implementer exists.

**Option E1 — Hold until a real second growable implementer (recommended).** Leave the surface provisional;
re-tighten only when RCC (or another grower) is on the near-term path.

- *Strengths:* Honours RK-4; avoids designing against a single implementer; zero churn on a frozen package.
- *Weaknesses:* The "provisional" caveat lingers in the shipped contract.
- *Risk:* Low — nothing strains the surface today (only the kit canary implements it; the LMU is
  `TrainableModel`-only).
- *Guardrail:* Keep the explicit "provisional until RCC" docstring (`interfaces.py:151`) so no consumer treats it
  as frozen; revisit when OW-15 (WS-6 cascor) or RCC is triggered.

**Option E2 — Speculatively tighten now (e.g. bake in cascor's growth shape).** Finalize `grow_step` against
cascor today.

- *Strengths:* Removes the "provisional" asterisk sooner.
- *Weaknesses:* Re-introduces exactly the cascor-shaped over-fit RK-4 forbids; likely wrong without a second
  data point.
- *Risk:* Medium-high.
- *Guardrail:* Explicitly out of scope until a second grower exists.

**Recommendation: E1 (hold).** Post-OQ-4, RCC is off the near-term path, so there is no second grower to design
against. Watch, don't touch.

### 4.F Coverage gate & hardening posture (OW-17 / OW-19 / OW-20)

Small, non-blocking hardening choices, bundleable into one opportunistic PR.

**Option F1 — Raise the gate to ~95 and do the cheap hardening now (recommended).** Tighten `cov-fail-under` to
~95 (12-pt headroom exists), perform the RK-10 `gh workflow run` dispatch, and add the conftest autoload guard.

- *Strengths:* Locks in the real coverage; closes the three known polish items in one S-sized PR;
  ecosystem-consistent.
- *Weaknesses:* A tighter gate can nag on a legitimate small dip.
- *Risk:* Low.
- *Guardrail:* Set the gate a few points *below* actual (e.g. 95 with 97 actual) so normal variance doesn't fail
  CI; keep it advisory-strict, not brittle.

**Option F2 — Defer all hardening until after 0.2.0.** Leave the gate at 85; skip the dispatch and conftest guard.

- *Strengths:* Zero distraction from the feature work.
- *Weaknesses:* The 12-pt gap silently permits coverage erosion during the 0.2.0 build — the worst time to lose
  the signal.
- *Risk:* Low-medium (silent erosion exactly when new code lands).
- *Guardrail:* If deferring, at minimum raise the gate *before* OW-6 so the new crossval code is held to the real
  bar.

**Recommendation: F1**, but sequence the gate-raise *before or with* OW-6 so 0.2.0 code is covered from day one.

---

## 5. Recommended phased roadmap (Part 2 ordering / grouping)

Derived from the recommended option in each fork above (A1, B1, C1, D1, E1, F1). Phases are ordered by dependency
and risk-retirement; within a phase, items can proceed in parallel.

### Phase 0 — Documentation truth restoration (S, ~1 PR; no code)

OW-11 (read cross-repo WS-4b state) → OW-1 (Status Tracker), OW-2 (naming), OW-3 (interface-design header).
**Why first:** retires the top risk (canonical-doc drift) at near-zero cost and makes all later sequencing
trustworthy. **Exit:** the Status Tracker matches reality; `gh pr view` MERGED on the doc PR.

### Phase 1 — Contract hygiene + 0.2.0 API ratification (S; decisions)

OW-4 (decide D3 → B1: add `predict(**kw)` in 0.2.0) and OW-5 (redline-ratify the §4 crossval API, incl. the
stub-vs-import D1 choice and the bundle-`predict(**kw)` choice). **Why second:** both are decisions that *gate*
the build; cheap to resolve, expensive to get wrong after code exists. **Exit:** §4 API frozen; D3 resolution
recorded in the interface-design doc.

### Phase 2 — Build & ship the 0.2.0 cross-val layer (L; the headline)

With the OW-17 coverage-gate raise applied **first** (so the new crossval code is held to the real bar), OW-6
(build `crossval/{metrics,splits,executor}` + `predict(**kw)`) gates two parallel branches — OW-8 (the §6 test
matrix) and OW-7 (extra + version bump + CHANGELOG) → OW-9 (publish-first to PyPI). **Why:** the
capability both consumption routes (service/CLI and canopy) block on. **Exit:** `0.2.0` on PyPI; `crossval` import
hermetic; CI green at the raised gate.

### Phase 3 — WS-2-coupled work (gated on service-core routes)

OW-13 (advanced `TrainingLifecycleBase` body, co-designed in service-core) → OW-10 (route-traversal conformance
proving the RK-6 no-leak guarantee at the route level). **Why later:** depends on WS-2's generic routes; not on the
0.2.0 critical path. **Exit:** the reference regression model traverses every generic route with no
argmax/accuracy leak.

### Phase 4 — Ecosystem / cross-repo integration (gated; parallelizable)

OW-18 (drift roster), OW-16 (deploy WS-7 recurrence service), OW-14 (WS-5 canopy generalization). OW-15 (WS-6
cascor pre-work) and OW-12 (`GrowableModel` re-tighten) remain **DEFERRED** behind their triggers (a real second
growable implementer / cascor adoption). **Why last:** mostly outside model-core's own tree; depends on OW-11 and
on consumers opting into 0.2.0.

### Hardening track (opportunistic, parallel to Phases 1–3)

OW-17 (coverage gate → ~95, **before** OW-6), OW-19 (RK-10 workflow dispatch), OW-20 (conftest autoload guard).
Bundle into one S-sized PR; OW-17 sequenced ahead of the 0.2.0 build.

### Dependency map

```text
Legend:  ─►  hard dependency (matches the §3 "Dep" column)     [ .. ]  soft sequencing note (not a dependency)

Phase 0 ─ OW-11 ─► OW-1
          OW-2, OW-3 (independent)
                 │
Phase 1 ─ OW-4 ──► (D3 resolved in the interface-design doc)
          OW-5 ──► (§4 cross-val API ratified)
                 │
Phase 2 ─ OW-5 ─► OW-6 ─┬─► OW-8                  [ OW-17 gate-raise sequenced before OW-6 ]
                        └─► OW-7 ─► OW-9 (publish 0.2.0)
                 │
Phase 3 ─ OW-13 ─► OW-10        (gated on WS-2 routes)
                 │
Phase 4 ─ OW-11 ─► {OW-18, OW-16, OW-14}
          OW-12 ─► OW-15        (both DEFERRED behind triggers)

Hardening (parallel): OW-17 ⟂ OW-19 ⟂ OW-20   [ OW-17 also sequenced before OW-6, per R6 / F1 ]
```

---

## 6. Consolidated risk register & guardrails

| # | Risk | Severity | Guardrail |
|:--|:-----|:---------|:----------|
| R1 | **Canonical Status Tracker drift** mis-sequences work (self-declared canonical, trails 5+ rows) | **High** | Phase 0 retires it first; cap at one doc PR (OW-1/2) |
| R2 | **Cross-val built before the §4 API redline** → discarded code | Medium | Phase 1 freezes OW-5 before OW-6; the build PR is mechanical only after ratification (C1) |
| R3 | **`GrowableModel` frozen without a real second growable implementer** | Medium | Hold OW-12 (E1); keep the "provisional until RCC" docstring; revisit on trigger |
| R4 | **Publish-first ordering violation on 0.2.0** (consumer pins `>=0.2.0` before it is on PyPI) | Medium | OW-9 (publish) gates on OW-7; the `[tools]` pin widens to `<0.3.0` **in the same PR as the version bump** (OW-7 / F-CRIT-1) — safe pre-publish (still resolves 0.1.0); `test_model_core_drift.py` + `test_pyproject_extras.py` enforce the coupling in required CI |
| R10 | **Version/pin lint trap (F-CRIT-1):** bumping `_version`→0.2.0 without widening the `[tools]` pin in the same PR turns required CI red | Medium | OW-7 couples version + pin + extras-lint atomically (RK-11); widen surgically (negative-control `test_model_core_drift.py:190`); supersedes the crossval design's 'pin later' sequencing |
| R5 | **RK-6 route-level no-leak unproven** until WS-2 traversal lands (asserted only against the model object) | Medium | OW-10 in Phase 3 drives the reference model through live routes |
| R6 | **Coverage gate (85) below actual (97)** permits silent erosion during the 0.2.0 build | Low | Raise the gate (OW-17) *before* OW-6 (F1) |
| R7 | **D3 left unresolved** pushes a non-bundled ABC edit to a later release | Low | Bundle B1 into the 0.2.0 series |
| R8 | **Cross-repo state assumed, not verified** (WS-4b) leads to a wrong tracker stamp | Low | OW-11 is an explicit read gate before OW-1 stamps WS-4/4b |
| R9 | **Concurrent-session merge races** (parallel Claude sessions on main + worktrees) cause dup-fix / wrong-blame | Low | `gh pr list` + `gh run list --branch main` before assuming a red main is ours; see standing guardrails below |

**Standing ecosystem guardrails** (apply to every PR in this roadmap): no merge without an explicit per-PR
"merged" signal **and** `gh pr view` showing `MERGED`; `gh pr list` + `gh run list --branch main` green before
assuming a red PR is ours (heavy concurrent-session activity); shared-CI/extras edits never split across PRs
(RK-11); releases are Paul-driven (the deployment gates are not auto-approved).

---

## 7. Validation record (multi-agent)

This document's factual basis and option analysis were validated by independent sub-agents, per the brief.

- **Survey + reconcile pass (complete).** Six independent survey agents + one reconcile synthesizer mapped the
  source and the design docs and built the drift matrix and outstanding-work inventory in §2–§3. They
  independently reproduced the D3 drift, the dependency-free import, and the 66-test pass. (Provenance: Appendix B.)
- **Adversarial validation pass (complete).** Four independent verifiers re-checked the draft against source and
  the design docs — (V1) Part 2 facts + Appendix A; (V2) the Part 3 backlog + Part 5 ordering; (V3) the Part 4
  options + Part 6 risks; (V4) whole-document completeness, cross-doc accuracy, and markdown structure. **V1 and V4
  returned SOLID** — every `file:line` / doc-§ citation independently re-verified, the 66-test suite re-run (66
  passed, 97% coverage), and the numpy-blocked import reproduced. **V2 and V3 returned MINOR_ISSUES**; every
  actionable finding below was applied in this revision.

| Section | Verdict | Finding | Resolution |
|:--------|:--------|:--------|:-----------|
| §2.1 facts + App. A | SOLID | All citations ACCURATE; suite re-run 66/97%; numpy-blocked import reproduced | No corrections needed; 2 precision NITs applied (serialization `:25` cite; "ten substantive modules") |
| §2.3 / App. A STALE row | NIT | Cross-repo sub-claims (WS-1/2/4) read as "verified" though §0 reserves UNVERIFIED for cross-repo | Tagged those sub-claims memory-derived / "see OW-11"; the STALE verdict itself rests on the in-worktree refactor-doc read |
| §3 deps ↔ §5 Phase 2 | INACCURATE | Phase 2 prose implied an OW-7→OW-8 chain; both actually depend on OW-6 in parallel | Phase 2 prose rewritten as parallel branches off OW-6 |
| §5 dependency map | INACCURATE | Map drew the soft OW-17►OW-6 edge but dropped the hard OW-5►OW-6 edge | Map redrawn with the OW-5►OW-6 hard edge + a hard/soft legend; OW-17 marked a sequencing note |
| §5 Phase 2 gate-raise | INACCURATE | Gate-raise bound to OW-8, contradicting four other "before OW-6" statements | Moved to before OW-6 |
| §3 OW-3 | OVERSTATED | Cited a non-existent "§10.5" of the interface-design doc | Changed to "§10 item 5 (WS-0 gate)" |
| §4.B Option B1 | OVERSTATED | "ABC edit unblocks the executor call / tabular ignore" is insufficient alone — `ReferenceLinearModel.predict` (`reference.py:81`) raises `TypeError` until widened too | Strength reworded to require widening the concrete `predict` signatures in the same PR (consistent with the B1 guardrail) |
| §4.A Option A2 | INACCURATE | Risk cross-reference "(§5)" pointed at the roadmap, not the risk | Repointed to "(§4.C / R2)" |
| §4.C / §4.D / §4.E | ACCURATE | C1 "please redline" confirmed verbatim (crossval §4); D1 stub-preference confirmed (crossval §6); E1 ↔ RK-4 confirmed (`interfaces.py:145-153`) | None |
| §6 risk register | ACCURATE | R1–R8 map to real Part 2/3 findings; no severity mis-rated | Added R9 (concurrent-session merge races) for symmetry with the standing guardrail |

**Post-validation reconciliation (2026-06-17).** After the validation pass, a memory-index check surfaced
**concurrent-session work** this roadmap was then reconciled against: (a) a focused crossval *build* roadmap
(`notes/JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md`) carrying finding **F-CRIT-1** — bumping
`_version`→0.2.0 turns `test_model_core_drift` + `test_pyproject_extras` (required CI) red unless the `[tools]` pin
widens to `<0.3.0` in the *same* PR; **independently verified here** against `tests/test_model_core_drift.py` (it
reads `_version.py` dynamically). OW-7 / OW-9 / R4 were corrected and R10 added accordingly. (b) WS-4b's real state
(#6 on `main`; #7/#8 stranded off `main`; app not on PyPI), which resolves the OW-11 / §2.3 UNVERIFIED row. This
umbrella roadmap and the concurrent build roadmap are complementary (umbrella vs. crossval-build deep-dive) and
cross-reference each other in §0.

---

## Appendix A — Full reconciliation matrix

| Verdict | Claim | Source | Actual | Impact |
|:--------|:------|:-------|:-------|:-------|
| STALE | Status Tracker WS-1/2/3/4 = `PLANNED` | refactor doc L47-50 | WS-3 model-core 0.1.0 published (verified in-worktree); WS-2 service-core 0.1.0 published, WS-1 generators on disk, WS-4 LMU conformance 10/10 (cross-repo / memory-derived — see OW-11) | Canonical doc mis-sequences work; primary fix |
| DRIFT | WS-4 row names `juniper-recurse` / RCC | refactor doc L50 | OQ-19 renamed → `recurrence`; OQ-4 picked LMU not RCC; repo is `juniper-recurrence` | Part 8 runbook names stale |
| DRIFT | D3 `**kw` on `fit` AND `predict` | interface design §3 D3 | `fit` has `**kw` (`interfaces.py:99`); `predict` ABC (`interfaces.py:112`) has none | Harmless now; predict-time-`dt` model would hit it |
| CONFIRMED | 0.1.0 on PyPI; pinned `:55`; tests + workflows exist | orchestrator | All confirmed; ran green; 97% coverage on a real run | WS-3 complete |
| CONFIRMED | No crossval code; 0.2.0 unbuilt | orchestrator | `grep` NONE; no `crossval` extra; `_version` 0.1.0 | 0.2.0 design-only |
| CONFIRMED | Ledger honoured; D4 placement + naming OK; LMU 2nd impl 10/10; WS-7/WS-T/OQ-12 also stale | interface design / placement / memory / refactor | 9/10 decisions in code (D3 partial); model-core a `juniper-ml` subdir subclass+inject; recurrence conformance 10 passed; WS-7 ml-extras half shipped but deploy half not; WS-T kit built; OQ-12 resolved in code | Contract integrity high; several tracker rows understate reality |
| RESOLVED | WS-4b app merge state | orchestrator vs. survey vs. concurrent session | Per a concurrent 2026-06-17 session: #6 skeleton on `main`; #7/#8 stranded in stacked branches off `main`; app not on PyPI | WS-4b partially landed; OW-11 narrows to a live confirm + re-land #7/#8 |

---

## Appendix B — Survey provenance & method

- **Orchestration:** a two-phase background workflow (`model-core-survey`) — six parallel survey agents into one
  reconcile synthesizer — plus the orchestrator's own first-hand reads.
- **Survey slices (independent):** (S1) source map + D1–D10-in-code; (S2) tests / coverage / CI / publish /
  extras wiring; (S3) the interface-design doc + its §10 follow-ups; (S4) the cross-val 0.2.0 design; (S5) the
  parent refactor doc + Status-Tracker audit; (S6) cross-doc dependency web (placement + recurrence).
- **Discipline:** agents were instructed to cite `file:line` / `DOC §N` for every fact and to *independently
  verify* the orchestrator's preliminary findings rather than echo them. The dependency-free import, the D3
  drift, and the 66-test pass were each reproduced by an agent running code/`grep`.
- **First-hand orchestrator reads:** `interfaces.py`, `lifecycle.py`,
  `JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`, `JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`,
  and the parent doc's Status Tracker — used to cross-check, not rubber-stamp, the survey output (the D3 drift and
  the "API-ratified-but-provisional" nuance were caught first-hand and confirmed by the survey).

---

_End of document._
