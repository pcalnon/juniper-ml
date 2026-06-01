# Juniper-Recurse — Design & Implementation Plan

**Project**: juniper-recurse — Recurrent / Constructive Neural-Network Application for the Juniper ML Research Platform
**Repository**: (proposed) pcalnon/juniper-recurse — design doc hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (DRAFT — pre-implementation design)
**Last Updated**: 2026-05-31

---

> **Document status:** DRAFT. This is a **planning and design document only**. No application code is to be written, and no existing code modified, on the basis of this document until the plan is ratified and individual workstreams are opened. Status of each workstream is tracked in [§Status Tracker](#status-tracker); open questions are consolidated in [§Open Questions](#part-5--open-questions--areas-of-uncertainty).
>
> **Verification status:** This draft was authored from a multi-agent grounding pass and a multi-agent literature survey, then subjected to an independent **five-lens** multi-agent verification pass (Round 1, 2026-05-31) whose findings are integrated into the Parts below and logged in [§Part 7 — Verification Log](#part-7--verification-log). Claims are tagged where they are **[unverified]**, **[speculative]**, or **[design hypothesis]** so that downstream readers can distinguish established fact from project-author judgment.

---

## Status Tracker

> Update this table as workstreams progress. Statuses: `PLANNED` · `IN DESIGN` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `SHIPPED` · `DEFERRED`. "Trigger" names the condition that must hold before a deferred/conditioned workstream starts. **Size** is a coarse effort estimate (S ≈ days, M ≈ 1–2 weeks, L ≈ 3+ weeks / multi-PR) — refine at workstream open.

| ID | Workstream | Part | Size | Status | Depends on | Trigger / Notes |
|----|------------|------|------|--------|-----------|-----------------|
| **WS-0** | Design ratification (this document) | All | S | `IN REVIEW` | — | Awaiting Paul's sign-off on model pick + middleware target + phasing |
| **WS-1** | juniper-data: time-series + regression support | 2.4 | M | `PLANNED` | WS-0 | Foundation; unblocks model training. Additive, low risk. **Resolve [OQ-5] here at ratification** |
| **WS-2** | Extract `juniper-service-core` (Tier-1 generic infra) | 2.3 | L | `PLANNED` | WS-0 | Additive shared package; cascor adopts behind a no-op shim |
| **WS-3** | Define `juniper-model-core` abstract interfaces | 2.3 | M | `PLANNED` | WS-0 | ABC/Protocol + event/serialization contracts + conformance test kit |
| **WS-4** | Build `juniper-recurse` (RCC reference model) + `juniper-recurse-client` | 1.5 / 2.3 | L | `PLANNED` | WS-1, WS-2, WS-3 | Greenfield; proves the template without touching cascor |
| **WS-5** | Generalize `juniper-canopy` (model-agnostic UI + recurse backend) | 2.5 | M | `PLANNED` | WS-4 | Builds on canopy's existing `BackendProtocol` seam |
| **WS-6** | Refactor `juniper-cascor` onto shared packages | 2.3 / 2.7 | L | `DEFERRED` | WS-2, WS-3, WS-4 | **Trigger:** interfaces proven by recurse + cascor conformance suite green. De-risks production system |
| **WS-7** | Ecosystem integration: `juniper-deploy`, `juniper-ml` extras | 2.6 | S | `PLANNED` | WS-4 | Compose service, meta-package extra |
| **WS-8** | (future) `juniper-recurse-worker` distributed training | 2.6 | L | `DEFERRED` | WS-4 | **Trigger:** recurse training cost justifies distribution |
| **WS-T** | Testing architecture (cuts across all) | 3 | M | `IN DESIGN` | WS-0 | Conformance kit is a first-class deliverable, not an afterthought |

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Part 0 — Scope, Method, and How to Use This Document](#part-0--scope-method-and-how-to-use-this-document)
- [Part 1 — New Model Development](#part-1--new-model-development)
- [Part 2 — Middleware Refactor](#part-2--middleware-refactor)
- [Part 3 — Testing Architecture](#part-3--testing-architecture)
- [Part 4 — Consolidated Risk Register](#part-4--consolidated-risk-register)
- [Part 5 — Open Questions & Areas of Uncertainty](#part-5--open-questions--areas-of-uncertainty)
- [Part 6 — Sources & References](#part-6--sources--references)
- [Part 7 — Verification Log](#part-7--verification-log)

---

## Executive Summary

`juniper-recurse` is a proposed new Juniper application that implements a **recurrent neural-network model**, structurally parallel to `juniper-cascor`, to extend the platform "beyond Cascade-Correlation" in line with its stated research direction (the canonical Research Philosophy commits the platform to *"the systematic empirical study of constructive and architecture-growing learning algorithms"*; `juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md`). The effort has three coupled deliverables, each a Part of this document:

1. **New model selection (Part 1).** Surveying both *constructive/growing* and *fixed-topology* recurrent architectures against six desired characteristics plus two binding platform constraints (first-principles implementability; ecosystem fit), the recommended **top three** are:
   - **① Recurrent Cascade-Correlation (RCC)** — Fahlman (1991). The direct constructive-recurrent analog of cascor; native integration, maximal first-principles transparency, grows its own topology. Carries a *known representational ceiling* (captures exactly the star-free/group-free regular languages) that is largely benign for continuous-valued regression.
   - **② Growing Echo State Network (Growing ESN / Reservoir Computing)** — Jaeger (2001); incremental-growth variant Qiao et al. (2017). Regression is *native* (the readout is literally ridge regression — mirroring cascor's output-layer training); highly transparent; reservoir grows in sub-reservoir blocks.
   - **③ Legendre Memory Unit (LMU)** — Voelker, Kajić & Eliasmith (2019). Modern continuous-time recurrent memory with **closed-form** dynamics matrices (no ODE solver, no custom kernel), a single principled growth knob, and a clean migration path toward structured state-space models (S4/Mamba) for future capability.

   These three span both architecture classes (per the ratified "span both" decision), are all implementable from primary literature without black-box layers, and each has a credible — if in places **[speculative]** — Cascade-Correlation integration story. The recommended construction is a **growable-recurrent *framework*** (juniper-recurse) with **RCC as the first concrete model**, the framework being able to host ESN and LMU units behind a common growth loop.

2. **Middleware refactor (Part 2).** Grounding confirms ~5.5 KLOC *(grounding-pass estimate)* of *already-generic* service infrastructure in cascor, plus a concentrated model↔service seam (`TrainingLifecycleManager`) and several classification-only assumptions (`argmax`, 2-D decision boundary) that a regression/time-series model would break. The target architecture extracts a **`juniper-service-core`** package (FastAPI factory, settings, security, middleware, websocket/worker infra, generic routes, lifecycle base) and a **`juniper-model-core`** package (the abstract `TrainableModel` / `GrowableModel` interface, training-event contract, serialization interface, and a reusable conformance test kit), reuses the existing `juniper-observability` / `juniper-data-client` / `juniper-config-tools`, and assigns all dataset capability to `juniper-data`. This directly continues documented intent in `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` (ideas #2 Common API, #4 New ABC, #7 Split up juniper-cascor). Per the ratified decision, the **target is comprehensive** but the **cascor refactor is phased and trigger-conditioned** — recurse is built greenfield against the new interfaces *first*, proving the template before the production system is touched.

3. **Testing architecture (Part 3).** Treated as a first-class deliverable: a reusable **interface-conformance test kit** that any model (cascor included) must pass; numerical-correctness / determinism / growth-loop / regression-metric / temporal-leakage suites for the new model; contract tests for the shared packages; and regression-safety (golden/snapshot) coverage that gates the cascor refactor.

**The single most important sequencing insight:** `juniper-data` cannot serve this model today (all nine generators are classification + 2-D tabular; the NPZ contract assumes 2-D; splits shuffle and so destroy temporal order). WS-1 (data foundation) is therefore the critical path and should start first.

---

## Part 0 — Scope, Method, and How to Use This Document

### 0.1 What this is and is not

- **Is:** an investigation + analysis + design + implementation plan for `juniper-recurse`, the associated middleware extraction, and the testing architecture, with sources and tracked open questions.
- **Is not:** code. Nothing here is to be implemented until ratified and split into workstream PRs. The plan deliberately surfaces uncertainty rather than papering over it.

### 0.2 Ratified design decisions (input to this draft)

The following were decided by Paul before drafting and are treated as fixed inputs:

| Decision | Choice | Consequence in this doc |
|----------|--------|-------------------------|
| **Model focus** | *Span both* growing and fixed-topology recurrent classes | Part 1 surveys the whole space and the top 3 deliberately spans both classes |
| **Middleware scope** | *Comprehensive target, phased rollout* | Part 2 designs the full template but stages cascor's adoption behind triggers (WS-6) |
| **Document structure** | *Single master document* | This file; status-tracked; sub-parts rather than separate docs |

### 0.3 Binding platform constraints (derived from existing docs, not optional)

These are not requirements the user re-stated; they are pre-existing platform commitments that the design must honor. Each is cited.

- **C1 — First-principles implementation.** *"…implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail… candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper."* (`RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md` §2.) → The recurrent model's recurrence, state, and growth must be inspectable code, **not** a `torch.nn.LSTM` black box. This constraint materially shapes the model ranking (Part 1).
- **C2 — Dual-mode application shape.** Every Juniper service has a FastAPI `create_app()` factory (`server.py`) **and** a standalone CLI (`main.py`), Pydantic settings with an env prefix, and the canonical 6-field `AGENTS.md` header (enforced by `tests/test_agents_md_header_schema.py`). juniper-recurse follows this exactly; env prefix `JUNIPER_RECURSE_`.
- **C3 — Shared-data contract.** Datasets flow `juniper-data → juniper-data-client → model` as NPZ artifacts. All dataset capability belongs to `juniper-data` (per the user's component-boundary statement). juniper-recurse must consume datasets via `juniper-data-client`, not generate its own.
- **C4 — Shared observability.** Metrics/logging/health/middleware come from `juniper-observability` (`>=0.3.0`; the on-disk version is 0.3.0 and already provides `MetricsAuthMiddleware` — 0.3.1 only adds an unparseable-client-IP warning); new Prometheus collectors use `register_or_reuse` & friends. (`juniper-cascor/AGENTS.md` "Programming Conventions".)
- **C5 — Python ≥ 3.12, line length 512, pytest + 80% coverage, worktree procedures, `util/` script placement.** Ecosystem conventions (`Juniper/AGENTS.md`).

### 0.4 Method & provenance

This document was produced by:

1. A **grounding pass** — five independent read-only agents mapped (a) the cascor model↔service seam, (b) the existing shared packages, (c) juniper-data's time-series/regression gap, (d) juniper-canopy's model coupling, (e) prior design intent and the research philosophy.
2. A **literature survey** — four independent research agents, each required to cite primary sources and self-flag unverifiable claims, covered: constructive/growing RNNs; gated/vanilla RNNs; reservoir + continuous-time nets; modern SSMs + memory models + TCN.
3. **Local verification** of flagged claims (port numbers, dependency-pin conventions, generator inventory, prior-art file existence) against the actual repositories.
4. A **multi-agent verification pass** over this draft (Part 7) to exclude hallucinations and integrate corrections.

> **Anti-hallucination posture.** Where research agents could not read a primary PDF (e.g., scanned 1990s NIPS papers), the affected numbers are explicitly flagged as secondary-sourced. Cascade-Correlation-integration claims for non-cascor architectures are uniformly labeled **[speculative]** — no published work implements them. Specific cascor source line numbers from the grounding pass are **not** reproduced as load-bearing facts; coupling is cited at the module/behavior level that the cascor `AGENTS.md` independently corroborates, with exact lines deferred to implementation-time confirmation.

### 0.5 Terminology: "recursive" vs. "recurrent"

The user's brief says "recursive nn model." In the literature these are distinct:

- **Recurrent NN (RNN):** processes a *linear/temporal chain*; hidden state at step *t* depends on input *t* and state *t−1*. **This is the sense that applies to time-series.** (Lipton et al. 2015, arXiv:1506.00019.)
- **Recursive NN (RvNN):** applies shared weights over a *tree/DAG structure*, trained by backpropagation-through-structure (Pollack 1990; Goller & Küchler 1996). Used for parse trees, not time-series. An RNN is formally the chain-structured special case of an RvNN.

Given the brief's emphasis on **time-series and regression**, this document interprets the target as **recurrent**. This interpretation is recorded as **[OQ-1]** in Part 5 for explicit confirmation.

---

## Part 1 — New Model Development

### 1.1 Requirements and how they are scored

The six desired characteristics from the brief, plus the two binding constraints from §0.3 that act as additional axes:

| Axis | Requirement | Interpretation used for scoring |
|------|-------------|---------------------------------|
| **R1** | Handles time-series data | Native sequence/temporal modeling |
| **R2** | Performs regression, not just classification | Continuous-valued targets are first-class, not bolted on |
| **R3** | Structurally amenable to dynamic operation | *Both* senses scored: (a) structural growth during training; (b) adaptive/continuous-time dynamics at inference |
| **R4** | Fundamentally flexible wrt dataset types | Works across regular/irregular sampling, uni/multivariate, varying lengths |
| **R5** | Prioritizes problem-solving ability over simplicity | Capability ceiling matters more than minimal implementation |
| **R6** | *Bonus:* integrable with cascor networks | Shares mechanism with cascade-correlation (growth, frozen units, correlation/linear-readout output training) |
| **P** | (C1) First-principles implementability | Implementable transparently from primary literature, no black-box layer |
| **E** | (C2–C5) Ecosystem fit | Fits dual-mode service shape, data contract, observability, Python/test conventions |

> Scoring is **qualitative and evidence-anchored**, not a single composite number — a weighted score would imply false precision given that several cells rest on architectural inference rather than published benchmarks. Legend: ✅ strong/native · 🟧 partial/conditional · ⚠️ weak/needs-work · 🔬 speculative (no direct source).

### 1.2 Candidate landscape (both classes)

| # | Architecture | Class | R1 | R2 | R3 | R4 | R5 | R6 | P | Verdict |
|---|--------------|-------|----|----|----|----|----|----|----|---------|
| 1 | **Recurrent Cascade-Correlation (RCC)** | Growing | ✅ | 🟧¹ | ✅ | 🟧 | 🟧² | ✅ | ✅ | **TOP-3 ①** |
| 2 | **Growing Echo State Network** | Reservoir/Growing | ✅ | ✅ | ✅ | ✅ | 🟧 | 🔬³ | ✅ | **TOP-3 ②** |
| 3 | **Legendre Memory Unit (LMU)** | Continuous-time recurrent | ✅ | ✅ | ✅⁴ | ✅ | ✅ | 🔬 | ✅ | **TOP-3 ③** |
| 4 | LSTM / GRU | Gated, fixed-topology | ✅ | ✅ | ⚠️⁵ | ✅ | ✅ | 🔬 | 🟧⁶ | Baseline / candidate-cell substrate |
| 5 | Closed-form Continuous-time (CfC) | Continuous-time | ✅ | ✅ | ✅ | ✅ | ✅ | 🟧⁷ | Honorable mention (most tractable liquid net) |
| 6 | Liquid Time-Constant (LTC) | Continuous-time | ✅ | ✅ | ✅ | ✅ | 🟧 | 🔬 | Strong dynamics, solver dependency |
| 7 | Neural ODE / Latent ODE / ODE-RNN | Continuous-time | ✅ | ✅ | ✅ | ✅ | 🟧 | 🔬 | ⚠️ | Best for irregular Δt; low transparency |
| 8 | S5 / diagonal-S4 (SSM) | State-space | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️⁸ | Future capability tier |
| 9 | Mamba (selective SSM) | State-space | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️⁹ | External baseline only (custom CUDA) |
| 10 | NEAT / Evolino | Neuroevolution | ✅ | 🟧 | ✅ | ✅ | ✅ | 🟧 | Different paradigm; low cascor fit |
| 11 | Grow-and-Prune LSTM | Growing (efficiency) | ✅ | ⚠️ | ✅ | 🟧 | 🟧 | 🟧 | Efficiency-oriented, not regression |
| 12 | Vanilla / Elman RNN | Fixed-topology | ✅ | 🟧 | ⚠️ | 🟧 | ⚠️ | 🔬 | Pedagogical baseline only |
| 13 | Temporal Convolutional Network (TCN) | **Not recurrent** | ✅ | ✅ | ❌ | ✅ | ✅ | 🔬 | **Disqualified** as core (feed-forward); baseline only |

**Footnotes (each is a real caveat, not a hedge):**
1. RCC's original demonstrations were sequence *classification* (grammar induction, Morse). Its correlation/Quickprop machinery supports continuous outputs, but **no published RCC time-series-*regression* benchmark was located** — R2 for RCC is architectural inference **[unverified]**.
2. RCC's representational ceiling (see §1.3.1) caps ultimate problem-solving reach on certain symbolic automata.
3. ESN↔cascor integration is an *analogy* (grown reservoir + linear readout vs. cascor candidate + output training); no cited paper builds the hybrid **[speculative]**.
4. LMU growth = increasing memory order *d* (more Legendre coefficients); a single, principled knob.
5. Gated RNNs are fixed-topology; "dynamic" only via online/continual learning, not structural growth.
6. LSTM/GRU are first-principles-implementable as cells, but the *fast path* (`torch.nn.LSTM`) is a fused black box; the from-scratch cell also differs from PyTorch's dual-bias parameterization.
7. CfC drops the ODE solver (closed-form), making it the most transparent continuous-time option, but it is still gradient-trained end-to-end (not closed-form *training* like ESN).
8. S4/S5 require HiPPO initialization + structured-matrix kernels (NPLR/Cauchy) — implementable transparently for S5/diagonal-S4 but onerous.
9. Mamba's selective scan needs a hand-written hardware-aware CUDA kernel; conflicts hardest with C1.

### 1.3 Top-3 deep dives

#### 1.3.1 ① Recurrent Cascade-Correlation (RCC)

**What it is / mechanism.** RCC is the recurrent member of the Cascade-Correlation family. It begins with inputs wired to outputs (trained by Quickprop); when error stalls it trains a *pool of candidate units* to maximize correlation with the residual error, installs the best, **freezes its input weights ("tenure")**, and makes it a new one-unit layer feeding all downstream units. The recurrent twist: each candidate also receives **its own previous output, delayed one time step**, with that self-loop weight trained by the same correlation procedure and frozen on tenure. The network thereby "builds up a finite-state machine tailored specifically for the current problem." (Fahlman 1991, NIPS-3; Fahlman & Lebiere 1990, NIPS-2.)

**Demonstrated on** finite-state grammar induction (Reber grammar, including the harder embedded form) and Morse-code recognition. *Exact experiment counts (run/pool/string figures) are reported in CMU secondary material rather than read off the scanned NIPS PDF — treat as secondary-sourced [unverified].*

**The known limitation (load-bearing, well-established).** RCC has a proven representational ceiling:
- Giles et al. (1995, IEEE TNN 6(4):829–836 — six authors: Giles, Chen, Sun, Chen, Lee, Goudreau) proved RCC **cannot represent certain finite-state automata** — specifically automata with state cycles of length > 2 under a constant input symbol — and proposed a constructive fix.
- Kremer (1996, IEEE TNN 7(4):1047–1051) identified a *second* large class of unrepresentable automata.
- Knorozova & Ronca (2024, AAAI; arXiv:2312.09048) gave the exact characterization: recurrent *cascades* capture **exactly the star-free / group-free regular languages** — anything needing a non-trivial "group" (e.g. a parity/mod-counter cycle) is out of reach; full cyclic RNNs are required for those. *(This exact result is proved for* recurrent neural cascades *with sign/tanh activations and positive recurrent weights; it applies to Fahlman's Quickprop-trained RCC by close analogy, not as a literal theorem about RCC.)*

| Axis | Verdict | Basis |
|------|---------|-------|
| R1 time-series | ✅ | Purpose-built input-sequence→output mapping [published] |
| R2 regression | 🟧→✅ | Architecturally supported (continuous outputs + correlation/Quickprop); **no published regression benchmark [unverified]** |
| R3 dynamic (growth) | ✅ | Adds recurrent units one at a time, on demand — the defining feature [published] |
| R4 dataset flexibility | 🟧 | Sequence-agnostic in principle; original demos are small symbolic sequences [published] |
| R5 capability > simplicity | 🟧 | Leans parsimonious; the star-free ceiling caps reach on symbolic automata |
| R6 cascor integration | ✅ **native** | RCC *is* the recurrent Cascade-Correlation; identical lineage [published] |
| P first-principles | ✅ **best-in-class** | Fully specified in primary literature; small; no black-box RNN layer needed |

**Strengths.** Native cascor integration (R6); maximal first-principles transparency (P); literally "approximates the structure of juniper-cascor"; the constructive growth directly advances the platform thesis; small and inspectable.

**Weaknesses / risks & guardrails.**
- *Representational ceiling* (star-free only). **Guardrail:** scope RCC to regression / short-memory / smooth-signal tasks where the discrete-automata pathologies are largely irrelevant; if a task needs parity/long modular cycles, expect failure and fall back to a cyclic recurrent unit (e.g., an LMU or gated cell hosted in the same framework).
- *Frozen cascade can build deep narrow recurrence* — watch latency and signal attenuation through many frozen layers. **Guardrail:** cap depth; monitor per-unit contribution.
- *1990s-scale, sparse modern reproductions; Quickprop-specific.* **Guardrail:** re-validate on modern data; provide a golden Reber-grammar regression test as a known-answer anchor.

**Recommendation role:** **Primary / reference model.** It is the most defensible first implementation: it satisfies R6 and P maximally and makes juniper-recurse a true structural sibling of cascor.

#### 1.3.2 ② Growing Echo State Network (Reservoir Computing)

**What it is / mechanism.** An ESN drives a **fixed, randomly-initialized recurrent reservoir** with the input and trains **only a linear readout** (reservoir state → output) by ridge regression. The **Growing ESN** variant adds reservoir neurons incrementally — Qiao et al. (2017, IEEE TNNLS 28(2):391–404) add hidden units "group by group" as sub-reservoirs, update the output weights incrementally, and preserve the Echo State Property by construction.

| Axis | Verdict | Basis |
|------|---------|-------|
| R1 time-series | ✅ | Reservoir computing is built for temporal signals (Lukoševičius & Jaeger 2009) |
| R2 regression | ✅ **native** | The readout *is* a ridge regression — regression is the training objective, not an add-on |
| R3 dynamic | ✅ (discrete-time) | Nonlinear dynamical reservoir with fading memory; **verified incremental growth** (Qiao 2017) |
| R4 dataset flexibility | ✅ | Standard across diverse time-series; caveat: classic ESN assumes regular Δt |
| R5 capability > simplicity | 🟧 | Simplicity-leaning (one closed-form solve); expressivity bounded by the random reservoir |
| R6 cascor integration | 🔬 **best analog** | Readout training ↔ cascor output-layer training; grown sub-reservoirs ↔ candidate units — **[speculative]**, no cited hybrid |
| P first-principles | ✅ **best-in-class** | Random matrices + spectral-radius scaling + closed-form ridge solve; no solver, no autodiff required |

**Strengths.** Regression is native (R2) — and the readout maps *directly* onto machinery cascor already has (output-layer training), making it the strongest *mechanistic* analog among non-RCC options. Cheapest to train; extremely transparent (P). Growth is verified in the literature (R3).

**Weaknesses / risks & guardrails.**
- *Echo State Property tuning is the #1 footgun:* the common rule "spectral radius ρ < 1" is necessary-in-practice but **provably not sufficient** (Yildiz, Jaeger & Kiebel 2012, *Neural Networks* 35:1–9). **Guardrail:** validate ESP empirically (state-contraction/washout tests), don't trust ρ<1 alone.
- *Reservoir weights stay random/untrained* — unlike cascor's *trained-then-frozen* candidates, so the R6 analogy is partial. **Guardrail:** be explicit in the design that the integration is by *interface* (growth loop + linear output) not by identical training semantics.
- *Run-to-run reproducibility* depends on reservoir seeding. **Guardrail:** seed + persist reservoir matrices in snapshots.

**Recommendation role:** **Strong alternative — the regression workhorse.** Its native ridge-regression readout makes it the most pragmatic path to *good regression results quickly*, and it reuses cascor's output-training mental model.

#### 1.3.3 ③ Legendre Memory Unit (LMU)

**What it is / mechanism.** A recurrent cell that maintains a continuous-time history by orthogonalizing it onto Legendre polynomials. Its linear memory state obeys `θ·ṁ(t) = A·m(t) + B·u(t)` with **closed-form** matrices `A`, `B` derived (via Padé approximation of a continuous delay) — no learned or iterative kernel construction. The memory couples to a nonlinear hidden state. Memory order `d` is the capacity knob (higher `d` → finer delay approximation; the paper reports an `O(d/√m)` error bound for the *spiking* implementation, `m` = neurons). (Voelker, Kajić & Eliasmith 2019, NeurIPS.) HiPPO (Gu et al. 2020) later re-derives the LMU "from first principles," making it the conceptual bridge to S4/Mamba.

| Axis | Verdict | Basis |
|------|---------|-------|
| R1 time-series | ✅ | Outperformed equivalently-sized LSTM on a chaotic time-series task; handles 10⁵-step dependencies [published] |
| R2 regression | ✅ | Continuous-output recurrent model; chaotic-series prediction is regression |
| R3 dynamic | ✅ | Explicit continuous-time dynamical system; **growth = increase order d** (principled single knob) |
| R4 dataset flexibility | ✅ | Continuous-time formulation adapts to step size (window θ, Δt) |
| R5 capability > simplicity | ✅ | Strong results at tiny parameter counts; favorable capability/footprint balance |
| R6 cascor integration | 🔬 | Clean linear-memory/nonlinear-unit split + single growth knob → conceptually compatible with incremental unit addition **[speculative]** |
| P first-principles | ✅ | Closed-form matrices, elementary discretization, plain-framework reference impl — satisfies C1 without heavy libraries |

**Strengths.** Best modern combination of recurrence + continuous-time dynamics + first-principles transparency + principled growth. Tiny footprint. **Future-proofing:** because HiPPO unifies LMU with S4, an LMU implementation is a low-risk stepping stone toward structured state-space capability later, preserving conceptual continuity.

**Weaknesses / risks & guardrails.**
- *Lower large-scale SOTA ceiling than Mamba/S4*; headline results are RNN-scale (psMNIST, chaotic series). **Guardrail:** acceptable for a research platform centered on transparency + time-series regression; document the ceiling.
- *Smaller ecosystem/tooling* than the SSM family. **Guardrail:** rely on the closed-form spec (well-defined) rather than third-party impls.
- *Timescale mis-setting* (θ/Δt) degrades memory. **Guardrail:** expose θ/Δt as inspectable, validated hyperparameters; add an analytic delay-line unit test.

**Recommendation role:** **Strong alternative — the modern, principled option** and the platform's bridge to state-space models.

### 1.4 Runners-up and explicit rejections (with rationale)

- **LSTM / GRU — *included as baseline + candidate-cell substrate, not top-3.*** They are the industry workhorses and are regression/time-series-capable, but they are **fixed-topology** (weak R3), advance the platform's constructive thesis the least, and their cascor integration is pure **[speculation]**. *They remain important:* (a) as the comparison baseline every model is measured against (cf. the live "are Transformers even better than linear models?" debate — Zeng et al. 2023 — which cautions that complexity must be *empirically* justified), and (b) a GRU cell (fewer params, single state) is the most plausible *gated* recurrent candidate-unit substrate if the framework later hosts gated units. The tension with R5 ("capability over simplicity") is real and recorded as **[OQ-2]**.
- **CfC — honorable mention.** The most tractable "liquid" continuous-time net (drops the ODE solver via a closed-form approximation; reported 1–5 orders of magnitude faster than DE-based counterparts — Hasani et al. 2022, *Nature Machine Intelligence*). Strong R3. Not top-3 only because its cascor structural fit is weak and it is gradient-trained end-to-end (less inspectable than ESN/LMU). A good second-wave addition.
- **LTC / Neural ODE / Latent ODE — deferred.** Best-in-class for *irregularly-sampled* series (Rubanova et al. 2019), but the **ODE-solver dependency** undercuts C1 transparency and there is no clean cascor structural mapping. Revisit if irregular-Δt datasets become central **[OQ-7]**.
- **S5 / diagonal-S4 — future capability tier.** SOTA long-range performance and explicit state recurrence, but HiPPO + structured-matrix kernels make a transparent from-scratch implementation onerous. Plausible *after* LMU (same HiPPO lineage). **Mamba** is recommended **as an external baseline only** — its selective scan needs a custom CUDA kernel, conflicting hardest with C1.
- **NEAT / Evolino — different paradigm.** Population-based neuroevolution; no shared training loop with cascor (low R6); higher reproducibility variance. Out of scope for a first model.
- **TCN — disqualified as the core model.** Strong sequence baseline but **not recurrent** (feed-forward dilated convolutions, fixed receptive field) — fails R3 and the recurrent requirement. Carry it as a *baseline only*; do not let strong baseline numbers tempt a scope change.

### 1.5 Recommendation

**Build `juniper-recurse` as a "growable recurrent-network framework," with Recurrent Cascade-Correlation as the first concrete model.** Rationale:

1. **RCC satisfies the brief and the constraints most completely** — it is the recurrent Cascade-Correlation (R6 native), maximally first-principles (P), grows (R3), and literally "approximates the structure of juniper-cascor."
2. **The framing as a *framework* operationalizes "span both classes" and the middleware "template" goal simultaneously.** The same growth-loop + model-interface that hosts RCC's self-recurrent candidate units can host **ESN reservoir blocks** and **LMU cells** as additional unit types — giving the platform comparative experiments across constructive *and* fixed-topology recurrence (the platform's stated "network populations" agenda) without three separate applications.
3. **Sequencing minimizes risk to production cascor:** RCC + the abstract interfaces are exercised greenfield in recurse first; only then is cascor refactored to consume them (WS-6, trigger-conditioned).

**Concretely, the first implementation (WS-4) is RCC; ESN (②) and LMU (③) are the next two unit types** hosted by the same framework, in that priority order (ESN first for its native-regression quick win; LMU next for modern capability + the SSM bridge).

***How unit types swap (design hypothesis, [OQ-3]).*** The `GrowableModel` growth loop is parameterized by a **candidate-unit factory**: RCC contributes a self-recurrent candidate, Growing-ESN a sub-reservoir block, and (where growth applies) a memory cell — each sharing one `grow_step()` → train-candidate → freeze/install → emit `unit_added` interface. RCC and Growing-ESN are genuinely *growable*; LMU is naturally a fixed-order `TrainableModel` (its "growth" is choosing order `d`), so it is hosted as a non-growing model rather than swapped into the growth loop. This unit-swap interface is the riskiest abstraction in the framework and **must be validated against ≥2 unit types before it is frozen** (see RK-4).

### 1.6 Open questions — Part 1

- **[OQ-1]** Confirm "recursive" is intended as **recurrent** (temporal), not tree-recursive (§0.5).
- **[OQ-2]** Does "prioritize problem-solving ability over simplicity" override the platform's first-principles transparency commitment (C1) where they conflict (e.g., would a `torch.nn.LSTM` fast-path be acceptable for capability, or must everything be hand-rolled)? This is the single biggest value tension in the model choice.
- **[OQ-3]** Is the *framework-hosting-three-unit-types* framing desired, or should the first deliverable be a single model (RCC only) with the others strictly deferred?
- **[OQ-4]** Acceptable to ship RCC despite the star-free representational ceiling, given the regression focus makes it largely benign? (Recommended: yes, with the documented guardrail.)
- **[OQ-5]** Target first datasets/problems for the CLI "hello-world" (cascor uses two-spiral; recurse needs a time-series-regression analog — e.g. Mackey-Glass, multi-sine, or a synthetic AR process). Drives WS-1 generator priorities.

---

## Part 2 — Middleware Refactor

> **Goal (from the brief):** identify all functionality currently in juniper-cascor that should be **extracted** so the new model need not duplicate it, move it to new or existing middleware applications, and thereby *"create a template for the addition of new neural-network models."* Component boundaries (the brief's own words): canopy = front-end/monitoring/control GUI; cascor = the Cascade-Correlation model; data = all dataset functionality for any model; observability = metrics/status extraction for monitoring.

### 2.1 The current cascor architecture and the model↔service seam

juniper-cascor (`src/` layout) is a dual-mode app: `src/server.py` (FastAPI) + `src/main.py` (CLI). Its service layer (`src/api/**`) wraps a model-specific core (`src/cascade_correlation/**`, `src/candidate_unit/**`). The grounding pass established that the coupling between them is **concentrated**, not diffuse — it lives almost entirely in `src/api/lifecycle/manager.py` (`TrainingLifecycleManager`), which:

- **imports and instantiates the concrete model** (`CascadeCorrelationNetwork`) rather than an abstract interface;
- **wraps/monkey-patches the model's `fit()`** to emit lifecycle events without modifying the core (a pattern the cascor `AGENTS.md` describes explicitly);
- **introspects model-specific topology** (`hidden_units`, `input_size`, `output_size`);
- **hardcodes the HDF5 serializer** for snapshots;
- **assumes 2-D classification** in the decision-boundary path (`argmax` over outputs; a `shape[1] == 2` input gate).

The last point is the critical compatibility hazard, and verification confirmed it reaches **further than the decision-boundary route** — the accuracy assumption also surfaces in the metrics-history path, metrics collection, and the "auto-snapshot best" feature. **A regression / time-series model breaks these classification assumptions** (accuracy metric, `argmax`, decision-boundary) baked into routes, monitoring, and the canopy UI. *(These behaviors are corroborated by `juniper-cascor/AGENTS.md`; exact line numbers from the grounding pass are deferred to implementation-time confirmation — see §0.4 anti-hallucination posture.)*

This matches **documented prior intent**: `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` idea **#4 "New ABC"** ("extract shared functionality from `CascadeCorrelationNetwork` and `CandidateUnit` into a new Abstract Base Class") and idea **#7 "Split up juniper-cascor"** ("decompose into ABC, two child classes, and a management layer"). The present plan generalizes that intent from *intra-cascor* (ABC over network/candidate) to *cross-model* (ABC/Protocol over any Juniper learning model).

### 2.2 Classification of cascor functionality (extract / abstract / keep)

From the grounding cartography (classifications anchored to cascor's documented module map):

| Tier | Cascor modules | Classification | Disposition |
|------|----------------|----------------|-------------|
| **T1 — Pure infra (≈5.5 KLOC [grounding estimate]; ~0 model coupling — worker-subsystem inclusion is contingent on [OQ-11])** | `api/app.py`, `api/settings.py` (base), `api/security.py`, `api/secrets.py`, `api/middleware.py`, `api/observability.py`, `api/service_launcher.py`, `api/websocket/manager.py`, `api/websocket/worker_stream.py`, `api/workers/{protocol,registry,audit,metrics,security}.py`, `log_config/**`, `profiling/**`, `utils/**` | GENERIC-INFRA | **Extract → `juniper-service-core`** (mostly lift-and-shift). Several already re-export `juniper-observability`. |
| **T2 — Semi-generic (needs an interface to decouple)** | `api/lifecycle/{manager,monitor,state_machine}.py`, `api/routes/{training,dataset,history,snapshots,metrics,health}.py`, `api/workers/coordinator.py`, `parallelism/task_distributor.py`, `snapshots/snapshot_serializer.py`, `api/models/training.py` | SEMI-GENERIC | **Extract base + keep cascor subclass.** Base lifecycle/routes/serializer in `juniper-service-core`; cascor-specific bits (cascade events, candidate fields, HDF5 weight layout) move to a cascor subclass. |
| **T3 — Model-specific (the model)** | `cascade_correlation/**`, `candidate_unit/**`, `cascor_constants/**`, `cascor_plotter/**`, `api/routes/decision_boundary.py`, `spiral_problem/**` | MODEL-SPECIFIC | **Stays in cascor.** (Two-spiral is arguably a *dataset* and could migrate to juniper-data per C3 — see [OQ-8].) |

The seam to abstract is therefore precisely the T2 boundary: introduce a model interface so the lifecycle/routes never name `CascadeCorrelationNetwork`.

*Per-module dispositions worth an explicit note:* `cascor_plotter/**` **stays in cascor** (spiral/2-D-classification plotting; live rendering belongs to canopy anyway per the component boundary). `profiling/**` and `utils/**` are lift-and-shift to `juniper-service-core` **only after** confirming `utils/**` is not a grab-bag — any model-specific helper is split out first, honoring the journal's "shared by default, override if needed" rule.

### 2.3 Target architecture — the model-addition template

Two new shared packages, plus reuse of three existing ones, plus the new app. (Packaging follows the established Juniper shared-package template: `juniper_<name>/` import package, `pyproject.toml` with setuptools, independent publish workflow on a `juniper-<name>-v*` tag, semver. **Pin convention is mixed across the ecosystem** — `juniper-doc-tools`/`juniper-config-tools` pin `>=X.Y.Z,<0.2.0` while `juniper-observability`/`juniper-ci-tools` are floor-only; **recommendation:** new pre-1.0 packages adopt the *capped* form `>=X.Y.Z,<X.(Y+1).0` for safety.)

```
                         ┌─────────────────────────────────────────────┐
                         │  EXISTING shared packages (reuse as-is)      │
                         │  • juniper-observability  (metrics/log/health/mw)
                         │  • juniper-data-client    (dataset fetch)    │
                         │  • juniper-config-tools   (env aliases)      │
                         └─────────────────────────────────────────────┘
                                        ▲              ▲
                                        │              │
   ┌──────────────────────────┐   ┌─────┴──────────────┴─────┐
   │  juniper-model-core (NEW) │   │  juniper-service-core(NEW)│
   │  • TrainableModel (ABC/   │   │  • create_app() factory   │
   │    Protocol)              │◄──│  • SettingsBase (env pfx) │
   │  • GrowableModel          │   │  • security / middleware  │
   │  • TrainingEvent contract │   │  • websocket + worker infra│
   │  • ModelSerializer iface  │   │  • generic routes:        │
   │  • TrainingLifecycleBase  │   │    health/training/metrics/│
   │  • conformance test kit   │   │    dataset/snapshots      │
   └──────────────────────────┘   │  • TaskDistributor        │
            ▲            ▲          └───────────────────────────┘
            │            │                    ▲           ▲
   ┌────────┴───┐  ┌─────┴────────┐   ┌───────┴───┐  ┌────┴──────────────┐
   │ juniper-   │  │ juniper-     │   │ juniper-  │  │ juniper-recurse    │
   │ cascor     │  │ recurse      │   │ cascor    │  │ (NEW app, WS-4)    │
   │ (CascadeCC │  │ (RCC, then   │   │ refactor  │  │ • RCC model        │
   │  impl T3)  │  │  ESN, LMU)   │   │ WS-6      │  │ • recurrent        │
   │ WS-6       │  │              │   │ trigger'd │  │   lifecycle subclass│
   └────────────┘  └──────────────┘   └───────────┘  └────────────────────┘
```

**`juniper-model-core` (the *model* template).** The linchpin (cf. journal idea #4). Defines:

- `TrainableModel` — the minimal contract the service layer needs: `fit(X, y, X_val=, y_val=, **kw)`, `predict(X)` / `forward(X)`, `input_shape` / `output_shape`, `task_type ∈ {classification, regression}`, `metrics() -> dict`, plus model-introspection (`describe_topology()`).
- `GrowableModel(TrainableModel)` — for constructive models (RCC, Growing ESN): `grow_step()`, `n_units`, growth-event hooks, `freeze()`. Fixed-topology models (LMU, LSTM) implement only `TrainableModel`.
- `TrainingEvent` contract — a generalized, model-agnostic event vocabulary (`training_start/end`, `epoch_end`, `unit_added`, `phase_change`) that *subsumes* cascor's events. The monitor consumes the generic vocabulary; each model maps its events onto it. **Illustrative mapping:** cascor `cascade_add` → `unit_added`; `candidate_progress` → `phase_change` (phase=`candidate_training`, per-candidate detail in payload); `epoch_end`/`training_start`/`training_end` map 1:1. RCC reuses `unit_added`; Growing-ESN maps sub-reservoir addition → `unit_added`. (Confirming this mapping preserves cascor's monitoring fidelity is a WS-6 acceptance criterion.)
- `ModelSerializer` interface — `save(model, path)` / `load(path)`; cascor's HDF5 serializer becomes one implementation.
- `TrainingLifecycleBase` — the de-cascored manager (threading, FSM, dataset mgmt, monitoring hooks) that operates only against `TrainableModel`/`GrowableModel`.
- The **conformance test kit** (see Part 3.3) — a reusable pytest suite any implementer must pass.

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

**What juniper-recurse actually contains (small!):** its concrete recurrent model(s) (RCC first), a `RecurrentLifecycle(TrainingLifecycleBase)` mapping recurrent growth onto `TrainingEvent`s, a `Settings(SettingsBase)` with prefix `JUNIPER_RECURSE_`, and a CLI problem (time-series regression analog of two-spiral). Everything else is inherited. **This is the template working as intended.**

### 2.4 juniper-data extensions (WS-1 — the critical path)

Per C3, *all* dataset capability belongs to juniper-data. Grounding found it **cannot serve this model today**:

| Capability | Today | Needed | Gap |
|------------|-------|--------|-----|
| Generators | 9, **all classification, all 2-D tabular** (arc_agi, checkerboard, circles, csv_import, gaussian, mnist, moon, spiral, xor — confirmed on disk) | ≥1 regression + ≥1 time-series generator | **MISSING** |
| NPZ shape | 2-D assumed (`X.shape[1]`=features; one-hot `y`) | 3-D `(samples, timesteps, features)`; scalar/vector regression `y` | **MISSING** |
| Splits | shuffle-based | **temporal** (non-shuffled) train/val/test; walk-forward option | **MISSING** |
| Sequence metadata | none | optional `seq_lengths`, `padding_mask`, target `scaling` params | **MISSING** |

WS-1 adds: regression generators (e.g. noisy multi-sine, AR(p), Mackey-Glass — see [OQ-5]); a 3-D-aware NPZ contract (back-compatible: 2-D still valid); a `temporal_split`; and task-type/scaling metadata in the artifact + data-client. **This is additive and low-risk to existing consumers** and must precede WS-4. The NPZ contract change is the one ecosystem-wide ripple — it touches the data-client and any shape-validating consumer; design it as an *extension* (new optional keys, `X.ndim` dispatch) not a breaking change. Recorded as **[OQ-6]**.

### 2.5 juniper-canopy generalization (WS-5)

Grounding found canopy **already has a model-agnostic seam** — a `BackendProtocol` with demo/service backends — which is a genuine asset. Disposition:

- **Reuse as-is:** FastAPI server, `BackendProtocol`, websocket manager, observability, health, snapshot/redis/cassandra panels.
- **Adapt (moderate):** metrics panel (accuracy → MSE/MAE/R² driven by the model's declared `task_type`/`metrics()`), dataset plotter (2-D scatter → time-series line plot), network visualizer (cascade columns → recurrent-cell/topology view from `describe_topology()`), training-monitor phase names (generic vocabulary).
- **Replace/conditionally-render:** decision-boundary, candidate-metrics, and cascade-evolution panels are cascor-specific — render them only when the backend advertises those capabilities.
- **Add:** a `juniper-recurse-client` backend behind the existing `BackendProtocol`.

The clean path is **schema-driven UI**: backends advertise their param schema, available metrics, and model type; canopy renders conditionally. This is the canopy half of the "template." *(Watch the documented Playwright/Dash `dbc.Input(type=number)` limitation when testing — tests must POST to the param endpoint directly; see Part 3.4.)*

### 2.6 Ecosystem changes

| Repo | Change | Risk |
|------|--------|------|
| **(new) juniper-recurse** | New service app (WS-4) | New code, isolated |
| **(new) juniper-recurse-client** | HTTP/WS client, mirrors juniper-cascor-client (cf. journal idea #5) | Low |
| **juniper-data** | Time-series/regression support (WS-1) | Additive |
| **juniper-canopy** | Model-agnostic UI + recurse backend (WS-5) | Moderate (UI) |
| **juniper-cascor** | Adopt service-core + implement model-core (WS-6) | **Highest — production system; trigger-conditioned** |
| **juniper-deploy** | Compose service + port (suggest host 8211→ctr 8210, mirroring cascor's 8201→8200) **[OQ-15]** (WS-7) | Low |
| **juniper-ml** | Add `juniper-recurse-client` to extras; new shared packages to `[tools]`/`[all]`; lint contracts (`test_pyproject_extras.py`) (WS-7) | Low; must update extras lint in same PR |
| **(future) juniper-recurse-worker** | Distributed training (WS-8) | Deferred |

### 2.7 Phased rollout (comprehensive target, trigger-conditioned cascor)

Sequencing embodies the ratified "comprehensive target, phased rollout" decision. **The defining principle: prove the template on greenfield recurse *before* refactoring production cascor.**

1. **WS-1 — Data foundation** (additive; critical path). Time-series + regression generators, 3-D NPZ, temporal split.
2. **WS-2 — Extract `juniper-service-core`** from cascor T1 infra. Cascor keeps working via a thin re-export shim (no behavior change).
3. **WS-3 — Define `juniper-model-core`** interfaces + conformance kit (design + tests; no app disruption).
4. **WS-4 — Build juniper-recurse** (RCC) + client, greenfield against WS-2/WS-3. **This validates the abstractions without risk to cascor.**
5. **WS-5 — Generalize canopy** + add recurse backend.
6. **WS-6 — Refactor cascor** onto service-core + model-core. **DEFERRED. Trigger:** WS-4 has shipped *and* a cascor golden/snapshot regression suite + the conformance suite are green for cascor. Until then, cascor stays as-is (it loses nothing; it simply doesn't yet consume the shared packages). **Kill-criterion:** if the conformance suite cannot be made green for cascor without changing observable behavior, WS-6 is abandoned — cascor keeps its own service stack, recurse still benefits from the shared packages, and the one-sided extraction is documented rather than forced.
7. **WS-7 — deploy/meta-package** integration. **WS-8 — recurse-worker** (deferred; trigger = training cost).

### 2.8 Risks & guardrails — the refactor

| Risk | Guardrail |
|------|-----------|
| **Premature/over-abstraction** (journal's own §4 risk: "putting too much in the ABC makes child classes trivial; too little defeats the purpose") | Adopt the journal's rule (paraphrasing its two clauses): *"shared by default, override if needed,"* and *"move to children only when semantically necessary."* Drive the interface from **two** real implementers (cascor + RCC) before freezing it — never design the ABC from cascor alone. |
| **Destabilizing production cascor** | WS-6 is trigger-conditioned and gated by a golden-regression suite captured *before* any refactor. service-core extraction (WS-2) ships behind a no-op re-export shim. |
| **NPZ contract change ripples** | Make it purely additive (optional new keys, `X.ndim` dispatch); 2-D path byte-identical; version the artifact. |
| **Classification assumptions leak into "generic" routes** | The conformance kit asserts a *regression* model round-trips through every generic route (no `argmax`, no accuracy assumption). |
| **Shared-package proliferation / maintenance burden** | Exactly two new packages; justify each against the ≥2-consumer bar that `juniper-observability` set. Resist a third (`juniper-serialization`) until a second serializer exists. |
| **Cross-repo version skew** | Reuse the existing drift-lint pattern (`test_doc_tools_drift.py` / `test_ci_tools_drift.py`) for the new packages. |
| **Concurrent-session race on shared CI files** (known ecosystem hazard) | Land shared-package + workflow edits in dedicated PRs; verify each new workflow with `gh workflow run` before relying on it. |

### 2.9 Open questions — Part 2

- **[OQ-6]** NPZ 3-D extension: confirm additive-only (no breaking change) is acceptable, and which optional keys (`seq_lengths`, `padding_mask`, `scaling`) are in-scope for WS-1 vs. deferred.
- **[OQ-8]** Should `spiral_problem` (and a future recurse CLI problem) migrate into juniper-data per the "all dataset functionality in juniper-data" boundary, or stay as in-app CLI demos?
- **[OQ-9]** Package granularity: two packages (`service-core` + `model-core`) vs. one combined `juniper-core` with submodules. (Recommend two — different change cadences, different consumers.)
- **[OQ-10]** Does the abstract `TrainableModel` live in a new package, or (journal idea #4's narrower framing) inside cascor first and migrate later? (Recommend new package, designed against two implementers.)
- **[OQ-11]** Worker protocol: is recurrent candidate/unit training parallelizable in a way that reuses cascor's worker protocol, or does it need a different task payload? (Affects whether service-core's worker layer is truly model-agnostic.)

---

## Part 3 — Testing Architecture

> Testing is a **first-class deliverable (WS-T)**, not an afterthought, and spans three targets named in the brief: (a) the new juniper-recurse app, (b) any new middleware package(s), (c) modifications to existing apps. The centerpiece is the **interface-conformance test kit** — the testing analog of the model-addition template.

### 3.1 Principles & inherited conventions

- **Framework & gates:** pytest; ecosystem-standard markers (`unit`, `integration`, `performance`, `slow`, `long`, `gpu`, `multiprocessing`, plus model-domain markers like `growth`, `regression`, `timeseries`); **80% coverage threshold**; pre-commit (flake8/black/isort/mypy/bandit/shellcheck); CI on push/PR.
- **Determinism is testable, not aspirational:** every model exposes a `random_seed`; tests assert bit-/tolerance-reproducibility across runs (mirrors cascor's `random_seed` convention).
- **Inherit the ecosystem's hard-won pytest defenses** (from prior incidents, now standard): block dash/playwright **plugin autoload** (SIGSEGV defense); reap orphaned multiprocessing children; set BLAS thread limits before imports; pyproject is the single source of pytest config (no stray `pytest.ini`). New repos copy these from cascor.
- **`juniper-observability.testing.reset_prometheus_registry`** fixture for any test touching Prometheus collectors.

### 3.2 Testing the new model (juniper-recurse)

| Suite | What it asserts | Technique |
|-------|-----------------|-----------|
| **Numerical correctness** | Forward pass and gradients are correct | Finite-difference gradient checks on the (hand-rolled, per C1) recurrent cell; compare to analytic gradients |
| **Known-answer / golden** | The model solves a problem with a known solution | RCC on the **Reber grammar** (golden classification anchor); ESN readout recovers a **linear system** exactly (closed-form); LMU **delay line** reproduces a pure delay to tolerance |
| **Regression metrics** | Regression is first-class | Assert MSE/MAE/R² computed and surfaced; assert **no `argmax`/accuracy path** is exercised for `task_type="regression"` |
| **Time-series correctness** | No temporal leakage; windowing correct | Verify temporal split keeps test strictly after train; verify windowed targets align; adversarial "shuffle would leak" negative test |
| **Growth-loop correctness** (GrowableModel) | Adding a unit is sound | After `grow_step()`: unit count +1; previously-frozen weights unchanged; training error non-increasing on the fit set (or documented exception); `unit_added` event emitted |
| **Determinism** | Reproducible | Same seed → same trajectory within tolerance |
| **Overfit-tiny sanity** | The model *can* learn | Memorize a tiny dataset to ~0 error (catches dead training loops) |
| **Stability guardrails** | Architecture-specific risks are caught | ESN: assert Echo State Property empirically (state contraction), **not** merely ρ<1 (per Yildiz 2012); RCC: assert frozen-weight invariance; LMU: assert state boundedness across θ/Δt |

### 3.3 The interface-conformance test kit (first-class, ships in `juniper-model-core`)

A **single reusable, parametrized pytest suite** that *any* `TrainableModel`/`GrowableModel` implementation must pass. Both juniper-recurse (RCC, ESN, LMU) **and refactored cascor** run it against their models. This is what makes the "template" verifiable rather than aspirational.

It asserts, for a supplied model factory + tiny dataset fixture:

- Interface compliance (`isinstance(model, TrainableModel)`; all methods present, correct signatures/return types).
- `fit → predict → metrics` round-trips; `metrics()` keys match the declared `task_type`.
- `describe_topology()` returns canopy-renderable, model-agnostic structure.
- Serialization round-trip via `ModelSerializer` is **lossless** (predictions identical after save/load).
- `TrainingEvent`s are emitted in a legal order (`training_start` … `training_end`); for `GrowableModel`, `unit_added` increments `n_units`.
- Every **generic service route** accepts the model (a regression model must traverse training/metrics/snapshot routes with no classification assumption).

> **Why this is load-bearing:** it converts "we extracted shared code" into "any new model is *proven* pluggable," and it is the regression-safety net that gates the cascor refactor (WS-6).

### 3.4 Testing the middleware packages & modifications to existing apps

- **`juniper-service-core` / `juniper-model-core`:** unit tests per module; **contract tests** that a minimal stub model drives every generic route + websocket channel; backward-compat tests proving the extracted code matches cascor's prior behavior (golden responses captured pre-extraction). Follow the `juniper-observability` package-test pattern (isolated registry, own CI lane, `juniper-<name>-v*` publish gating). Add a **drift lint** (clone of `test_doc_tools_drift.py`) so consumer pins can't fall behind.
- **juniper-cascor (WS-6 regression safety):** **before** any refactor, capture a golden/snapshot suite (training trajectories on two-spiral with fixed seed; API response snapshots; snapshot-serialization round-trips). The refactor is accepted only if golden suite + conformance kit stay green. This is the concrete guardrail behind the WS-6 trigger.
- **juniper-data (WS-1):** generator output-shape/dtype tests (2-D *and* 3-D); **temporal-split leakage** tests (property-based: for any split, `max(train_time) < min(test_time)`); NPZ contract back-compat (2-D artifacts still load); scaling round-trip (denormalize recovers originals).
- **juniper-canopy (WS-5):** model-agnostic rendering tests (regression backend → MSE panel, no decision-boundary); conditional-panel tests; backend-protocol conformance for the recurse backend. **Known constraint:** Playwright cannot drive Dash `dbc.Input(type=number)` React state — UI param tests must **POST to the param endpoint directly**, and the UI subsuite must run isolated (autoload-blocked) to avoid the documented event-loop leak.

### 3.5 Cross-cutting test concerns

- **Integration / E2E:** recurse ↔ juniper-data (fetch a time-series regression dataset, train, serve metrics) ↔ canopy (render). A docker-compose E2E in juniper-deploy (mirrors cascor's `test_juniper_data_e2e.py`).
- **Performance benchmarks:** micro (forward/step latency, growth-step cost, readout-solve time) + end-to-end, mirroring cascor's `tests/performance/`. Establish baselines early to catch regressions.
- **Property-based testing (hypothesis):** shape/dtype invariants, temporal-split properties, serialization round-trips — high leverage for the contract surfaces.
- **CI/CD:** per-repo pipeline cloned from cascor (pre-commit, unit, integration, build, security, docs); cross-repo dispatch for the shared packages; **verify each new workflow with `gh workflow run` immediately** (a workflow can pass yamllint yet fail at first real execution — a repeatedly-observed ecosystem failure mode).
- **Security:** bandit + gitleaks + pip-audit, as elsewhere; metrics endpoint gated by `MetricsAuthMiddleware` (observability ≥0.3.0).

### 3.6 Toolset summary

| Concern | Tool | Notes |
|---------|------|-------|
| Test runner | pytest | markers, `--run-long`, coverage |
| Coverage | pytest-cov / coverage[toml] | 80% gate |
| Async / API | pytest-asyncio, httpx | FastAPI `TestClient` pattern |
| Property-based | hypothesis | shapes, splits, round-trips |
| Parallel | pytest-xdist | mind multiprocessing-orphan reaping |
| Numerical | numpy/torch finite-diff helpers | gradient checks |
| Perf | pytest-benchmark or cascor's micro-bench harness | baselines |
| Prometheus | `juniper_observability.testing.reset_prometheus_registry` | registry isolation |
| Lint/security | flake8/black/isort/mypy/bandit, gitleaks, pip-audit | pre-commit + CI |

### 3.7 Open questions — Part 3

- **[OQ-12]** Where does the conformance kit physically live so both recurse and cascor consume it — exported from `juniper-model-core` as an installable `pytest` plugin, or a `[test]` extra? (Recommend installable kit + thin per-repo wrapper.)
- **[OQ-13]** Golden-test substrate for cascor regression safety before WS-6: trajectory hashing vs. tolerance-based numeric comparison (seed/BLAS nondeterminism may force tolerance-based).
- **[OQ-14]** Performance baseline acceptance bands for a research (vs. production) model — how much regression is "a finding" vs. "a failure"?

---

## Part 4 — Consolidated Risk Register

| # | Risk | L×I | Mitigation / Guardrail | WS |
|---|------|-----|------------------------|----|
| RK-1 | **juniper-data can't serve time-series regression** — blocks everything | High × High | WS-1 first; additive NPZ extension | WS-1 |
| RK-2 | **RCC representational ceiling** (star-free only) bites on a chosen task | Med × Med | Scope to regression/smooth signals; framework can fall back to LMU/gated unit | WS-4 |
| RK-3 | **RCC regression is unproven** in the literature | Med × Med | Treat as research; golden known-answer tests; ESN (native regression) as parallel track | WS-4 |
| RK-4 | **Premature/over-abstraction** of the model interface | Med × High | Design ABC against ≥2 implementers (cascor+RCC); "shared by default, override if needed" | WS-3 |
| RK-5 | **Destabilizing production cascor** during refactor | Med × High | WS-6 trigger-conditioned; pre-refactor golden suite; service-core via no-op shim | WS-6 |
| RK-6 | **Classification assumptions leak** into "generic" routes | Med × Med | Conformance kit drives a regression model through every route | WS-3 |
| RK-7 | **First-principles vs. capability tension** (C1 vs. R5) unresolved | Med × Med | [OQ-2]; default to first-principles per C1, document any exception | WS-0 |
| RK-8 | **Shared-package proliferation / maintenance** | Low × Med | Exactly two packages; ≥2-consumer bar; drift-lint | WS-2/3 |
| RK-9 | **NPZ contract change breaks existing consumers** | Low × High | Additive-only; 2-D path byte-identical; version artifact | WS-1 |
| RK-10 | **New CI workflows pass lint but fail first run** (observed pattern) | Med × Low | `gh workflow run` each new workflow immediately | WS-2/4/7 |
| RK-11 | **Concurrent-session races on shared CI/extras files** | Med × Low | Dedicated PRs; update extras lint in same PR | WS-7 |
| RK-12 | **Canopy UI test fragility** (Dash/Playwright `type=number` gap; event-loop leak) | Med × Low | POST param endpoint directly; isolate UI subsuite | WS-5 |
| RK-13 | **SSM/Mamba temptation** pulls scope toward black-box dependencies | Low × Med | Mamba is baseline-only; S5/diagonal-S4 deferred behind LMU | WS-4 |

---

## Part 5 — Open Questions & Areas of Uncertainty

> The brief requires **explicit acknowledgement of all open questions and areas of uncertainty.** Consolidated here for tracking; resolve before or during the owning workstream.

| ID | Question | Part | Owner WS | Author's lean |
|----|----------|------|----------|---------------|
| **OQ-1** | "recursive" intended as **recurrent** (temporal), not tree-recursive? | 0.5 | WS-0 | Recurrent (given time-series focus) |
| **OQ-2** | Does R5 ("capability over simplicity") override C1 (first-principles) where they conflict? | 1.6 | WS-0 | No — C1 binds; document exceptions |
| **OQ-3** | Framework hosting 3 unit types, or single-model (RCC only) first? | 1.5/1.6 | WS-0 | Framework, RCC first |
| **OQ-4** | Ship RCC despite star-free ceiling (benign for regression)? | 1.6 | WS-0 | Yes, with guardrail |
| **OQ-5** | First CLI/datasets (Mackey-Glass? multi-sine? AR(p)?) — **resolve at WS-0**; WS-1 critical path depends on it | 1.6 | WS-1 | Multi-sine + Mackey-Glass |
| **OQ-6** | NPZ 3-D extension additive-only; which optional keys in WS-1? | 2.4/2.9 | WS-1 | Additive; `seq_lengths`+`scaling` in-scope |
| **OQ-7** | When do irregular-Δt datasets (→ Neural ODE/Latent ODE) become relevant? | 1.4 | future | Defer |
| **OQ-8** | Migrate spiral/recurse CLI problems into juniper-data? | 2.9 | WS-1 | Lean yes (per C3) |
| **OQ-9** | Two packages vs. one combined `juniper-core`? | 2.9 | WS-2/3 | Two |
| **OQ-10** | Abstract model interface: new package vs. inside cascor first? | 2.9 | WS-3 | New package, 2-implementer design |
| **OQ-11** | Is recurrent unit training parallelizable via cascor's worker protocol? | 2.9 | WS-3 | Unknown — investigate |
| **OQ-12** | Conformance kit packaging (pytest plugin vs. `[test]` extra)? | 3.7 | WS-3 | Installable kit + wrapper |
| **OQ-13** | Cascor golden-test substrate: trajectory hash vs. tolerance? | 3.7 | WS-6 | Tolerance (nondeterminism) |
| **OQ-14** | Performance acceptance bands for a research model? | 3.7 | WS-T | TBD with Paul |
| **OQ-15** | Service port assignment (proposed host 8211→ctr 8210)? | 2.6 | WS-7 | Confirm no conflict |

**Standing uncertainties (not resolvable by decision — flagged honestly):**

- RCC's exact original experiment figures are **secondary-sourced** (scanned PDF unreadable); the *mechanism* and *task types* are well-corroborated.
- **All cascor-integration claims for non-RCC architectures (ESN/LMU/LSTM/etc.) are `[speculative]`** — no published hybrid exists. The framework framing makes them tractable, but they are novel research, not known-good patterns.
- The "modern growing-RNN literature is thin" finding is an absence-of-evidence judgment from bounded searches, not a proof of absence.
- Exact cascor source line numbers were intentionally **not** treated as load-bearing; module/behavior-level coupling is corroborated by `juniper-cascor/AGENTS.md`, but precise call sites need implementation-time confirmation.

---

## Part 6 — Sources & References

### 6.1 Internal Juniper sources (consulted, with paths)

| Source | Path | Used for |
|--------|------|----------|
| Cascor architecture & conventions | `juniper-cascor/AGENTS.md` | §2.1–2.2 seam, conventions, testing |
| Cascor model↔service seam | `juniper-cascor/src/api/lifecycle/manager.py`, `src/api/routes/**`, `src/snapshots/**` | §2.1 coupling (module-level) |
| Cascor architecture guide | `juniper-cascor/notes/ARCHITECTURE_GUIDE.md` | Context (not deep-read) |
| Research philosophy (canonical) | `juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md` | C1, platform thesis, §0.3 |
| Architectural design journal | `Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` (ideas #2 Common-API, #4 New-ABC, #5 ABC-client, #7 split-cascor) | §2.1–2.3 prior intent, ABC, split-cascor; #5 ↔ juniper-recurse-client |
| Multi-network orchestration design | `juniper-ml/notes/PHASE_6E_MULTI_NETWORK_DESIGN.md` | "network populations" context |
| Observability exports (0.3.x) | `juniper-ml/juniper-observability/juniper_observability/**` | C4, reuse inventory |
| Shared-package template | `juniper-ml/juniper-{config,ci,doc}-tools/**`, `juniper-ml/pyproject.toml` | §2.3 packaging/pin convention |
| Data service & contract | `juniper-data/juniper_data/**` (generators/, api/routes/datasets.py, core/split.py) | §2.4 gap analysis |
| Data client | `juniper-data-client/juniper_data_client/client.py` | §2.4 client surface |
| Canopy coupling & BackendProtocol | `juniper-canopy/src/{main.py,backend/protocol.py,backend/*adapter*.py,frontend/components/**}` | §2.5 |
| Ecosystem conventions | `Juniper/AGENTS.md`, `juniper-ml/AGENTS.md` | C2–C5, ports, worktrees |
| (Note) `prompt116_2026-05-31.md` | `juniper-ml/prompts/` | This task's own archived brief — *not independent prior art* |

### 6.2 External sources (literature survey — all citations verified by the research agents; caveats in Part 7)

**Cascade-Correlation & constructive/recurrent:**
- Fahlman & Lebiere (1990). *The Cascade-Correlation Learning Architecture.* NIPS-2. https://proceedings.neurips.cc/paper/1989/hash/69adc1e107f7f7d035d7baf04342e1ca-Abstract.html
- Fahlman (1991). *The Recurrent Cascade-Correlation Architecture.* NIPS-3. https://papers.nips.cc/paper/1990/hash/fe73f687e5bc5280214e0486b273a5f9-Abstract.html
- Giles, Chen, Sun, Lee & Goudreau (1995). *Constructive Learning of Recurrent NNs: Limitations of RCC…* IEEE TNN 6(4):829–836. DOI 10.1109/72.392247
- Kremer (1996). *Comments on "Constructive learning…"* IEEE TNN 7(4):1047–1051. DOI 10.1109/72.508949
- Knorozova & Ronca (2024). *On The Expressivity of Recurrent Neural Cascades.* AAAI; arXiv:2312.09048
- Reber (1967). *Implicit Learning of Artificial Grammars.* JVLVB 6:855–863. · Cleeremans, Servan-Schreiber & McClelland (1989). *Finite State Automata and Simple Recurrent Networks.* Neural Computation 1(3)
- Stanley & Miikkulainen (2002). *NEAT.* Evolutionary Computation 10(2):99–127
- Schmidhuber, Wierstra, Gagliolo & Gomez (2007). *Training Recurrent Networks by Evolino.* Neural Computation 19(3):757–779
- Dai, Yin & Jha (2020). *Grow and Prune… LSTMs.* arXiv:1805.11797 · Cossu et al. (2021). arXiv:2103.07492
- Lipton, Berkowitz & Elkan (2015). *A Critical Review of RNNs.* arXiv:1506.00019 · Pollack (1990); Goller & Küchler (1996) [recursive-NN origin]

**Gated/vanilla RNN & forecasting standing:**
- Elman (1990). *Finding Structure in Time.* Cognitive Science 14(2):179–211
- Bengio, Simard & Frasconi (1994). IEEE TNN 5(2):157–166. DOI 10.1109/72.279181 · Pascanu, Mikolov & Bengio (2013). ICML; arXiv:1211.5063 · Williams & Zipser (1989). Neural Computation 1(2):270–280
- Hochreiter & Schmidhuber (1997). *LSTM.* Neural Computation 9(8):1735–1780 · Gers, Schmidhuber & Cummins (2000). *Learning to Forget.* Neural Computation 12(10):2451–2471 · Greff et al. (2017). *LSTM: A Search Space Odyssey.* IEEE TNNLS 28(10); arXiv:1503.04069
- Cho et al. (2014). *GRU / RNN Encoder-Decoder.* EMNLP; arXiv:1406.1078 · Chung et al. (2014). *Empirical Evaluation of GRNNs.* arXiv:1412.3555 · Sutskever, Vinyals & Le (2014). *Seq2Seq.* arXiv:1409.3215 · Tallec & Ollivier (2017). arXiv:1705.08209
- Hewamalage, Bergmeir & Bandara (2021). *RNNs for TSF.* IJF 37(1):388–427; arXiv:1909.00590 · Salinas et al. (2020). *DeepAR.* IJF 36(3):1181–1191; arXiv:1704.04110 · Petneházi (2019). arXiv:1901.00069 · Zeng et al. (2023). *Are Transformers Effective for TSF?* AAAI; arXiv:2205.13504

**Reservoir & continuous-time:**
- Jaeger (2001). *The "echo state" approach.* GMD Report 148 *(tech report; cite the erratum version)* · Lukoševičius & Jaeger (2009). *Reservoir computing…* Computer Science Review 3(3):127–149. DOI 10.1016/j.cosrev.2009.03.005 · Yildiz, Jaeger & Kiebel (2012). *Re-visiting the echo state property.* Neural Networks 35:1–9
- Qiao, Li, Han & Li (2017). *Growing ESN with Multiple Subreservoirs.* IEEE TNNLS 28(2):391–404. DOI 10.1109/TNNLS.2016.2514275
- Maass, Natschläger & Markram (2002). *LSM.* Neural Computation 14(11):2531–2560
- Chen, Rubanova, Bettencourt & Duvenaud (2018). *Neural ODEs.* NeurIPS; arXiv:1806.07366 · Rubanova, Chen & Duvenaud (2019). *Latent ODEs.* NeurIPS; arXiv:1907.03907
- Hasani et al. (2021). *Liquid Time-constant Networks.* AAAI 35(9):7657–7666; arXiv:2006.04439 · Hasani et al. (2022). *Closed-form Continuous-time NNs.* Nature Machine Intelligence 4(11):992–1003; arXiv:2106.13898

**State-space, memory, convolutional baseline:**
- Gu, Goel & Ré (2022). *S4.* ICLR; arXiv:2111.00396 · Smith, Warrington & Linderman (2023). *S5.* ICLR; arXiv:2208.04933 · Gu & Dao (2023). *Mamba.* arXiv:2312.00752 · Gu et al. (2020). *HiPPO.* NeurIPS; arXiv:2008.07669 · Jelassi et al. (2024). *Repeat After Me.* arXiv:2402.01032
- Voelker, Kajić & Eliasmith (2019). *Legendre Memory Units.* NeurIPS. https://proceedings.neurips.cc/paper/2019/hash/952285b9b7e7a1be5aa7849f32ffff05-Abstract.html
- Bai, Kolter & Koltun (2018). *An Empirical Evaluation of Generic Convolutional and Recurrent Networks…* (TCN). arXiv:1803.01271

### 6.3 Method / tooling

Grounding + literature surveys conducted via independent sub-agents (read-only `Explore` for code; `general-purpose` with web/arXiv/Hugging Face paper search for literature), each required to cite primary sources and self-flag unverifiable claims. Local verification via repository inspection. See Part 7.

---

## Part 7 — Verification Log

> The brief mandates **multiple independent sub-agents to validate all aspects** and **integrate valid changes**. This section records what the verification pass checked, what it found, and what was corrected. Append future re-verification rounds here.

### Round 1 — initial multi-agent verification (2026-05-31)

**Status: COMPLETE.** Five independent adversarial sub-agents each verified a distinct lens against the *primary sources / live code* (not this document's restatement). **No CRITICAL or factually-WRONG claims were found.** Citations verified accurate to an unusually high degree; every cascor / juniper-data / juniper-canopy / juniper-observability code claim was CONFIRMED against the live repositories. The valid findings below are integrated into the Parts above.

**Verifier coverage:**
- **V1 — model claims & citations** (web/arXiv/DOI): all 13 candidate architectures + ~50 references, the RCC representational-ceiling chain, ESN/LMU/SSM/gated/continuous-time clusters.
- **V2 — cascor grounding** (live `juniper-cascor/src`): the model↔service seam, T1/T3 module existence, dual-mode shape, port, serializer, classification assumptions.
- **V3 — feasibility + internal consistency + prior-art** (doc + journal): journal quotes, WS/OQ-ID integrity, two-package acyclicity, port non-conflict, decision logic under C1.
- **V4 — data/canopy/observability/testing** (live repos): generator inventory, NPZ shape, split, BackendProtocol, observability exports + version, pin convention, pytest defenses.
- **V5 — completeness** vs. every brief deliverable.

| ID | Lens | Finding | Severity | Resolution |
|----|------|---------|----------|------------|
| F1 | V4 | `juniper-observability` on-disk version is **0.3.0**, not the 0.3.1 the C4 pin claimed | HIGH (pin) | **Fixed** — C4 & §3.5 pin `>=0.3.0` (`MetricsAuthMiddleware` ships in 0.3.0; 0.3.1 only adds the IP warning) |
| F2 | V3/V5 | Header asserted a *completed* verification while Part 7 read PENDING | MEDIUM | **Fixed** — this log populated; header now scoped to "Round 1, 2026-05-31" |
| F3 | V3 | §1.3 deep dives mis-numbered `1.4.x` under a `1.3` parent (no `1.4` existed) | MEDIUM | **Fixed** — renumbered to 1.3.1–1.3.3; following sections → 1.4/1.5/1.6; all cross-refs updated |
| F4 | V1 | Giles et al. 1995 author list incomplete (six authors) | MINOR | **Fixed** — §1.3.1 & §6.2 corrected |
| F5 | V1 | LMU `O(θω/d)` not traceable to the cited paper (its stated bound is `O(d/√m)`, spiking impl) | MINOR | **Fixed** — §1.3.3 reworded; spurious big-O removed |
| F6 | V1 | Knorozova-Ronca result is for *recurrent neural cascades* (sign/tanh, +recurrent weights), applied to Fahlman's RCC by analogy | MINOR | **Fixed** — scoping clause added in §1.3.1 |
| F7 | V3 | §2.8 labelled a two-clause splice "verbatim" | MINOR | **Fixed** — now "paraphrasing"; clauses quoted separately |
| F8 | V2 | The classification-only assumption breaks **more** than decision-boundary (metrics history, collection, auto-snapshot-best) | MAJOR (strengthen) | **Integrated** — §2.1 broadened; RK-6 already covers |
| F9 | V5 | No per-workstream effort sizing | MEDIUM | **Integrated** — Size (S/M/L) column added to Status Tracker |
| F10 | V5 | Framework unit-swap mechanism unspecified | MEDIUM | **Integrated** — candidate-unit-factory hypothesis added to §1.5 |
| F11 | V5 | `describe_topology()` → canopy contract undefined | MEDIUM | **Integrated** — illustrative schema added to the §2.3 sketch |
| F12 | V5 | `TrainingEvent` "subsumes" cascor events with no mapping shown | LOW-MED | **Integrated** — explicit event mapping added to §2.3 |
| F13 | V5/V3 | 5.5 KLOC stated as fact; worker-layer genericity is contingent on OQ-11 | LOW-MED | **Integrated** — tagged "[grounding estimate]" + OQ-11 contingency (exec summary, §2.2) |
| F14 | V5 | No WS-6 kill-criterion / abort path | LOW | **Integrated** — kill-criterion added to §2.7 |
| F15 | V3 | OQ-15 not inline-tagged in §2.6; §6.1 idea-#5 set mismatch | LOW | **Fixed** — OQ-15 tag added; journal idea-#5 ↔ recurse-client noted |
| F16 | V5/V3 | OQ-5 (dataset choice) blocks the WS-1 critical path | LOW | **Fixed** — flagged "resolve at WS-0" in Status Tracker + OQ table |
| F17 | V5 | `cascor_plotter`/`profiling`/`utils` extraction rationale missing | LOW | **Integrated** — per-module dispositions added after §2.2 |

**Confirmed clean (no change needed):** all 13 candidate-architecture citations and the full Fahlman→Giles→Kremer→Knorozova-Ronca ceiling chain with correct DOIs/pages/venues (V1); the cascor model↔service seam, monkey-patched `fit()`, `hidden_units`/`input_size`/`output_size` introspection, hardcoded `CascadeHDF5Serializer`, the 2-D/`argmax` decision-boundary, dual-mode `server.py`+`main.py`, env prefix `JUNIPER_CASCOR_`, default port 8200, and all T1/T3 module existence (V2); the 9 classification-only 2-D generators, the `X.shape[1]` NPZ assumption, and the shuffling split (V4); canopy's `BackendProtocol` + demo/service backends + the reusable/adapt/replace split (V4); every observability export named in C4/§3 and the *mixed* pin convention (V4); pytest autoload + orphan-reaper defenses and the 80% gate (V4); the two-package split's acyclicity, component-boundary consistency, and 8210/8211 port non-conflict, plus the top-3 recommendation following soundly from the scoring under C1 (V3); all WS/OQ IDs defined; all journal prior-art quotes accurate (V3); every brief deliverable FULLY or PARTIALLY met (V5).

**Residual `[unverified]` / `[speculative]` items (by design, not defects):** RCC time-series-*regression* benchmark (none published); all non-RCC cascor-integration hypotheses (no published hybrid exists); RCC's exact 1990s experiment counts (image-only scanned PDF); the unit-swap interface (design hypothesis, pending ≥2-implementer validation). These are intentionally surfaced, not hidden.

---

*End of document. This is a living plan — update the [Status Tracker](#status-tracker), [Open Questions](#part-5--open-questions--areas-of-uncertainty), and [Verification Log](#part-7--verification-log) as implementation proceeds.*
