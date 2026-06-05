# Juniper-Recurse — Recurrent Model Design & Implementation Plan

**Project**: juniper-recurse — Recurrent / Constructive Neural-Network Application for the Juniper ML Research Platform
**Repository**: (proposed) pcalnon/juniper-recurse — design doc hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.2.0 (DRAFT — pre-implementation design; split from the master plan 2026-06-03)
**Last Updated**: 2026-06-03

---

> **Document status:** DRAFT. **Planning and design only** — no application code is written, and no existing code modified, on the basis of this document until the plan is ratified and individual workstreams are opened. This document covers **the recurrent model itself** (selection, design, and model-level testing). The companion document covers the service/middleware refactor that hosts it.
>
> **Provenance:** This document is the **model half** of a 2026-06-03 two-way split of the original single master plan (`JUNIPER_RECURSE_DESIGN_AND_PLAN_2026-05-31.md`). All workstream (WS-*), open-question (OQ-*), risk (RK-*), constraint (C*), and verification (F*) identifiers are preserved verbatim across both halves so cross-references stay stable. The original five-lens verification pass (Round 1, 2026-05-31) covered the combined content; its full log lives in the companion document.

## Companion documents & how to read them

| Document | Scope |
|----------|-------|
| **This document** — *Recurrent Model Design* | The recurrent NN capability: requirements, candidate-architecture survey, the top-3 deep dives, the recommendation, model-level testing, model risks & open questions, and the external literature survey. |
| **[Model/Middleware Refactor Design & Plan](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md)** — *companion* | Extracting `juniper-service-core` + `juniper-model-core` from cascor (the "model-addition template"), juniper-data extensions, canopy generalization, ecosystem changes, phased rollout, middleware/cross-cutting testing, **and the shared scaffolding** (Status Tracker, binding constraints, method/provenance, consolidated Risk Register, consolidated Open-Questions table, Verification Log, internal sources). |

> **The coupling (read this):** `juniper-recurse` is built **greenfield against the abstractions defined in the companion document** (`juniper-model-core`'s `TrainableModel` / `GrowableModel` interface; `juniper-service-core`'s app/service scaffolding). The model proves those abstractions before the production cascor system is refactored to consume them. So: **this document decides *what to build*; the companion decides *what it plugs into*.** Where the model's needs drive a refactor decision (e.g. the regression/time-series data contract, the model-agnostic topology schema), the canonical text lives in the companion and is cross-referenced here.

---

## Model Status (focused view)

> Full ecosystem Status Tracker (all workstreams WS-0…WS-T) lives in the [companion document](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md#status-tracker). This is the model-only slice.

| ID | Workstream | Size | Status | Depends on | Trigger / Notes |
|----|------------|------|--------|-----------|-----------------|
| **WS-0** | Design ratification (model pick) | S | `IN REVIEW` | — | **Not ratified.** Provisional 2026-06-02: OQ-1 recurrent · OQ-2 C1-binds · OQ-3 framework/RCC-first · OQ-5 multi-sine+Mackey-Glass+AR(p) — **all contingent on the model pick.** **OQ-4 REOPENED — under research** (RCC's no-count/no-group [star-free] ceiling); model pick may change. See §1.6 + [OQ-4]. |
| **WS-4** | Build `juniper-recurse` (RCC reference model) + `juniper-recurse-client` | L | `PLANNED` | WS-1, WS-2, WS-3 | Greenfield; proves the template without touching cascor. WS-1/2/3 are companion-doc workstreams. |

---

## Executive Summary (model)

`juniper-recurse` is a proposed new Juniper application that implements a **recurrent neural-network model**, structurally parallel to `juniper-cascor`, to extend the platform "beyond Cascade-Correlation" in line with its stated research direction (the canonical Research Philosophy commits the platform to *"the systematic empirical study of constructive and architecture-growing learning algorithms"*; `juniper-ml/notes/RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md`).

**Model selection (Part 1).** Surveying both *constructive/growing* and *fixed-topology* recurrent architectures against six desired characteristics plus two binding platform constraints (first-principles implementability; ecosystem fit), the recommended **top three** are:

- **① Recurrent Cascade-Correlation (RCC)** — Fahlman (1991). The direct constructive-recurrent analog of cascor; native integration, maximal first-principles transparency, grows its own topology. Carries a *known representational ceiling* (captures exactly the star-free/group-free regular languages). **Whether that ceiling is acceptable is the reopened [OQ-4] now under active research** — see §1.3.1 and §1.6.
- **② Growing Echo State Network (Growing ESN / Reservoir Computing)** — Jaeger (2001); incremental-growth variant Qiao et al. (2017). Regression is *native* (the readout is literally ridge regression — mirroring cascor's output-layer training); highly transparent; reservoir grows in sub-reservoir blocks.
- **③ Legendre Memory Unit (LMU)** — Voelker, Kajić & Eliasmith (2019). Modern continuous-time recurrent memory with **closed-form** dynamics matrices (no ODE solver, no custom kernel), a single principled growth knob, and a clean migration path toward structured state-space models (S4/Mamba) for future capability.

These three span both architecture classes (per the ratified "span both" decision), are all implementable from primary literature without black-box layers, and each has a credible — if in places **[speculative]** — Cascade-Correlation integration story. The recommended construction is a **growable-recurrent *framework*** (juniper-recurse) with **RCC as the first concrete model**, the framework being able to host ESN and LMU units behind a common growth loop.

> **Open design tension (active):** the model pick (RCC-first) is **provisional and contingent on [OQ-4]**, reopened 2026-06-02 because RCC's no-count/no-group (star-free) ceiling is an *architectural* property, not something a guardrail removes. See §1.3.1 ("known limitation"), §1.6 [OQ-4], and the companion Risk Register entry RK-2.

**Relationship to the refactor:** the model is small by design because almost everything non-model is inherited from the shared packages defined in the companion document. *"What juniper-recurse actually contains"* (a concrete recurrent model, a `RecurrentLifecycle` mapping growth onto generic training events, a `Settings` subclass, and a CLI problem) is specified in the companion's §2.3.

---

## Part 0 (model-relevant excerpts)

> Scope/method/provenance and the *full* binding-constraint set (C1–C5) live in the companion document's Part 0. Reproduced here: the terminology decision and the one constraint that materially shapes the model ranking (C1). C2–C5 (ecosystem fit) are summarized; see companion §0.3 for the cited full text.

### 0.5 Terminology: "recursive" vs. "recurrent"

The user's brief says "recursive nn model." In the literature these are distinct:

- **Recurrent NN (RNN):** processes a *linear/temporal chain*; hidden state at step *t* depends on input *t* and state *t−1*. **This is the sense that applies to time-series.** (Lipton et al. 2015, arXiv:1506.00019.)
- **Recursive NN (RvNN):** applies shared weights over a *tree/DAG structure*, trained by backpropagation-through-structure (Pollack 1990; Goller & Küchler 1996). Used for parse trees, not time-series. An RNN is formally the chain-structured special case of an RvNN.

Given the brief's emphasis on **time-series and regression**, this document interprets the target as **recurrent**. This interpretation is recorded as **[OQ-1]** (§1.6) for explicit confirmation.

### Binding constraint that shapes the model (C1)

- **C1 — First-principles implementation.** *"…implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail… candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper."* (`RESEARCH_PHILOSOPHY_CANONICAL_DRAFT_2026-05-19.md` §2.) → The recurrent model's recurrence, state, and growth must be inspectable code, **not** a `torch.nn.LSTM` black box. This constraint materially shapes the model ranking below.

- **C2–C5 (summary; full text + citations in companion §0.3):** C2 dual-mode app shape (FastAPI `create_app()` + CLI `main.py`, Pydantic settings, env prefix `JUNIPER_RECURSE_`); C3 shared-data contract (datasets via `juniper-data-client`, all dataset capability in juniper-data); C4 shared observability (`juniper-observability >= 0.3.0`); C5 Python ≥ 3.12, line length 512, pytest + 80% coverage, worktree procedures, `util/` script placement.

---

## Part 1 — New Model Development

### 1.1 Requirements and how they are scored

The six desired characteristics from the brief, plus the two binding constraints from §0.3 (companion) that act as additional axes:

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

**The known limitation (load-bearing, well-established — and the basis for the reopened [OQ-4]).** RCC has a proven representational ceiling:
- Giles et al. (1995, IEEE TNN 6(4):829–836 — six authors: Giles, Chen, Sun, Chen, Lee, Goudreau) proved RCC **cannot represent certain finite-state automata** — specifically automata with state cycles of length > 2 under a constant input symbol — and proposed a constructive fix.
- Kremer (1996, IEEE TNN 7(4):1047–1051) identified a *second* large class of unrepresentable automata.
- Knorozova & Ronca (2024, AAAI; arXiv:2312.09048) gave the exact characterization: recurrent *cascades* capture **exactly the star-free / group-free regular languages** — anything needing a non-trivial "group" (e.g. a parity/mod-counter cycle) is out of reach; full cyclic RNNs are required for those. The same work shows the remedy is to **introduce group-implementing neurons**. *(This exact result is proved for* recurrent neural cascades *with sign/tanh activations and positive recurrent weights; it applies to Fahlman's Quickprop-trained RCC by close analogy, not as a literal theorem about RCC.)*

> **⚑ Active review ([OQ-4]).** This ceiling is the reason the RCC-primary pick was reopened on 2026-06-02. The concern (Paul's): the no-count/no-group limitation is *architectural*, so the previously-proposed "scope-to-regression guardrail" mitigates symptoms rather than the cause. Live options under research: (a) keep a growable cascade but add a group-implementing unit type to break aperiodicity; (b) lead with a model that never had the ceiling (ESN/reservoir is regression-native; NEAT grows true recurrent cycles). See §1.6 [OQ-4] and companion RK-2.

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
- *Representational ceiling* (star-free only). **Guardrail (under [OQ-4] review — see callout above):** scope RCC to regression / short-memory / smooth-signal tasks where the discrete-automata pathologies are largely irrelevant; if a task needs parity/long modular cycles, expect failure and fall back to a cyclic recurrent unit (e.g., an LMU or gated cell hosted in the same framework), or a group-implementing unit per Knorozova & Ronca (2024).
- *Frozen cascade can build deep narrow recurrence* — watch latency and signal attenuation through many frozen layers. **Guardrail:** cap depth; monitor per-unit contribution.
- *1990s-scale, sparse modern reproductions; Quickprop-specific.* **Guardrail:** re-validate on modern data; provide a golden Reber-grammar regression test as a known-answer anchor.

**Recommendation role:** **Primary / reference model — provisional, pending [OQ-4].** Absent the ceiling concern it is the most defensible first implementation (it satisfies R6 and P maximally and makes juniper-recurse a true structural sibling of cascor); the reopened OQ-4 may demote it or add a group-implementing unit type.

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

**Strengths.** Regression is native (R2) — and the readout maps *directly* onto machinery cascor already has (output-layer training), making it the strongest *mechanistic* analog among non-RCC options. Cheapest to train; extremely transparent (P). Growth is verified in the literature (R3). **Does not share RCC's star-free ceiling** — a random nonlinear reservoir realizes cyclic/periodic dynamics — which is why it is the leading [OQ-4] alternative.

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
- **NEAT / Evolino — different paradigm; now an active [OQ-4] candidate.** Population-based neuroevolution; no shared training loop with cascor (low R6); higher reproducibility variance. Out of scope for a *first* model under the original ranking — but because NEAT grows arbitrary recurrent topology (including the cyclic structures RCC cannot form), it is back under consideration as part of the OQ-4 model-pick review.
- **TCN — disqualified as the core model.** Strong sequence baseline but **not recurrent** (feed-forward dilated convolutions, fixed receptive field) — fails R3 and the recurrent requirement. Carry it as a *baseline only*; do not let strong baseline numbers tempt a scope change.

### 1.5 Recommendation

> **Status: PROVISIONAL — contingent on [OQ-4] (reopened 2026-06-02).** The recommendation below stands as the original analysis; the model pick may change pending the OQ-4 literature review.

**Build `juniper-recurse` as a "growable recurrent-network framework," with Recurrent Cascade-Correlation as the first concrete model.** Rationale:

1. **RCC satisfies the brief and the constraints most completely** — it is the recurrent Cascade-Correlation (R6 native), maximally first-principles (P), grows (R3), and literally "approximates the structure of juniper-cascor."
2. **The framing as a *framework* operationalizes "span both classes" and the middleware "template" goal simultaneously.** The same growth-loop + model-interface that hosts RCC's self-recurrent candidate units can host **ESN reservoir blocks** and **LMU cells** as additional unit types — giving the platform comparative experiments across constructive *and* fixed-topology recurrence (the platform's stated "network populations" agenda) without three separate applications.
3. **Sequencing minimizes risk to production cascor:** RCC + the abstract interfaces are exercised greenfield in recurse first; only then is cascor refactored to consume them (WS-6, trigger-conditioned — companion §2.7).

**Concretely, the first implementation (WS-4) is RCC; ESN (②) and LMU (③) are the next two unit types** hosted by the same framework, in that priority order (ESN first for its native-regression quick win; LMU next for modern capability + the SSM bridge). *(The OQ-4 review may reorder this — e.g. ESN-first — or add a group-implementing unit type.)*

***How unit types swap (design hypothesis, [OQ-3]).*** The `GrowableModel` growth loop is parameterized by a **candidate-unit factory**: RCC contributes a self-recurrent candidate, Growing-ESN a sub-reservoir block, and (where growth applies) a memory cell — each sharing one `grow_step()` → train-candidate → freeze/install → emit `unit_added` interface. RCC and Growing-ESN are genuinely *growable*; LMU is naturally a fixed-order `TrainableModel` (its "growth" is choosing order `d`), so it is hosted as a non-growing model rather than swapped into the growth loop. This unit-swap interface is the riskiest abstraction in the framework and **must be validated against ≥2 unit types before it is frozen** (see companion RK-4). The `GrowableModel` / `TrainableModel` interfaces themselves are defined in the companion's `juniper-model-core` (§2.3).

### 1.6 Open questions — model

> These are the model-owned open questions. The full consolidated table (all OQs, both halves) lives in the companion's Part 5; OQ identifiers are shared.

- **[OQ-1]** Confirm "recursive" is intended as **recurrent** (temporal), not tree-recursive (§0.5). *(Provisional: recurrent.)*
- **[OQ-2]** Does "prioritize problem-solving ability over simplicity" (R5) override the platform's first-principles transparency commitment (C1) where they conflict (e.g., would a `torch.nn.LSTM` fast-path be acceptable for capability, or must everything be hand-rolled)? This is the single biggest value tension in the model choice. *(Provisional: No — C1 binds; document exceptions.)*
- **[OQ-3]** Is the *framework-hosting-three-unit-types* framing desired, or should the first deliverable be a single model (RCC only) with the others strictly deferred? *(Provisional: framework, RCC first — contingent on OQ-4.)*
- **[OQ-4]** **REOPENED 2026-06-02 — under research.** (Was: acceptable to ship RCC despite the star-free ceiling, given the regression focus makes it largely benign? Recommended yes, with guardrail.) Paul's concern: the no-count/no-group ceiling is **architectural, not guardrail-fixable**. Literature review in progress — Knorozova & Ronca (AAAI 2024, arXiv:2312.09048) confirms recurrent cascades = **exactly** star-free and that the remedy is **group-implementing units**; ESN/reservoir and NEAT alternatives are under consideration. **Probable redesign of the model pick (OQ-3).**
- **[OQ-5]** Target first datasets/problems for the CLI "hello-world" (cascor uses two-spiral; recurse needs a time-series-regression analog). *(Provisional 2026-06-02: **multi-sine + Mackey-Glass + AR(p)**.)* Drives the WS-1 generator priorities (companion §2.4).
- **[OQ-7]** When do irregular-Δt datasets (→ Neural ODE/Latent ODE) become relevant? *(Lean: defer; §1.4.)*

---

## Part 3 (model) — Testing the new model

> Full testing architecture (principles, the conformance kit, middleware/app testing, cross-cutting concerns, toolset) is in the companion's Part 3. Reproduced here: the model-specific suite (companion §3.2). Determinism, markers, coverage gate, and the inherited pytest defenses are described in companion §3.1.

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

The reusable **interface-conformance kit** that *any* model (including RCC/ESN/LMU and refactored cascor) must pass is defined in the companion's §3.3 — it ships in `juniper-model-core` and is the testing analog of the model-addition template.

---

## Model risks (focused view)

> Full consolidated Risk Register (RK-1…RK-13, all workstreams) is in the companion's Part 4. The model-relevant subset:

| # | Risk | L×I | Mitigation / Guardrail | WS |
|---|------|-----|------------------------|----|
| RK-2 | **RCC representational ceiling** (star-free only) bites on a chosen task | Med × Med → **under [OQ-4] re-evaluation** | Scope to regression/smooth signals; framework can fall back to LMU/gated/group-implementing unit; OQ-4 may change the model pick | WS-4 |
| RK-3 | **RCC regression is unproven** in the literature | Med × Med | Treat as research; golden known-answer tests; ESN (native regression) as parallel track | WS-4 |
| RK-7 | **First-principles vs. capability tension** (C1 vs. R5) unresolved | Med × Med | [OQ-2]; default to first-principles per C1, document any exception | WS-0 |
| RK-13 | **SSM/Mamba temptation** pulls scope toward black-box dependencies | Low × Med | Mamba is baseline-only; S5/diagonal-S4 deferred behind LMU | WS-4 |

---

## Sources — external literature survey

> Internal Juniper sources (cascor seam, journal, etc.), the method/tooling note, and the consolidated reference list live in the companion's Part 6. Reproduced here: the external literature survey (companion §6.2), which is overwhelmingly model-related. *All citations were verified by the Round-1 research agents; caveats in the companion's Verification Log (Part 7).*

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

---

*End of model document. This is a living plan — coordinate updates with the [companion refactor document](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md), whose Status Tracker, Open-Questions table, and Verification Log are canonical for cross-cutting state.*
