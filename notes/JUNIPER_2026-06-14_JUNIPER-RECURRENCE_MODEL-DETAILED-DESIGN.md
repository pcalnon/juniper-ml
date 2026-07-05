# Juniper-Recurrence — Detailed Model Design: P3-C (LMU + Approach-C), the Δt-Native Continuous-Time Memory

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application for the Juniper ML Research Platform *(originally named `juniper-recurse`; see §0.2)*
**Repository**: (proposed) pcalnon/juniper-recurrence — design doc hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT — consolidated detailed design for the selected model; pre-implementation; **WS-0 RATIFIED 2026-06-14**)
**Last Updated**: 2026-06-14

---

> **What this document is.**
> A single, detailed, *model-specific* design + planning document for the model selected to give the Juniper platform continuous-time, irregular-Δt recurrent capability: **P3-C — a closed-form variable-Δt Legendre Memory Unit (LMU) discretization ("Approach C")**. It consolidates the full body of prior juniper-recurrence/`juniper-recurse` work — the literature review, the architecture evaluation (P1–P7, ESN, NEAT, LMU/SSM), the POC verification, the OQ-4 reevaluation, the dataset audit, and the Δt-handling analysis — and augments it with the theory, the reference implementation source code, the Juniper-ecosystem integration plan, and a risk/guardrail register specific to this model.
>
> It **synthesizes and does not duplicate** the companion documents (§0.4). Where those documents are the breadth (the whole option space), this is the depth (the one chosen model).
>
> **WS-0 RATIFIED 2026-06-14 (Paul) — workstream PRs (WS-1…WS-4) may now open** (each as its own reviewed PR). This is the design of record for the model pick on the Δt axis.

---

## Table of contents

- **Part 0** — Preface: scope, naming, provenance, source corpus, binding constraints, status
- **Part 1** — Executive summary: the decision and its logic
- **Part 2** — Theory & background: LMU, the star-free ceiling, the four Δt approaches, the SSM walls
- **Part 3** — Model design: the Δt-native LMU unit (Approach-C), with reference source code
- **Part 4** — Two-step implementation path: fixed-order first, grown cascade unit later
- **Part 5** — The temporal substrate (Workstream-0 dependency)
- **Part 6** — Juniper ecosystem integration (data, model-core, service-core, canopy, worker, packaging, deploy)
- **Part 7** — Strengths, weaknesses, risks, guardrails
- **Part 8** — Implementation challenges & complex integrations
- **Part 9** — Next steps (current work a/b/c; future work)
- **Part 10** — Consolidated open questions
- **Part 11** — References
- **Appendix A** — Full reference source code (LMU variable-step unit + sequence windowing + conformance test)
- **Appendix B** — Cross-references & provenance

---

# Part 0 — Preface

## 0.1 Purpose & scope

The Juniper platform's flagship model is Cascade-Correlation (cascor), a *stateless, feed-forward, classification-first* constructive network. The next model — **juniper-recurrence** — adds the one capability cascor structurally cannot express: **memory of the past over a real, possibly irregular, time axis**, in service of **time-series regression** (the equities use-case and the planned synthetic temporal datasets).

This document covers, in detail, the **selected model for that role** and the work required to land it:

1. **Model design & implementation** — the theory of the LMU, the Approach-C variable-Δt discretization math, what is learned vs. fixed, the reference source code, the numerical guardrails, and the empirical verification status.
2. **Juniper project integration** — the 3-D NPZ data contract, the `juniper-model-core` / `juniper-service-core` abstractions the model plugs into, canopy generalization, the worker protocol, packaging/placement, and the docker/on-host migration path.

Out of scope (covered by the companion docs, §0.4): the full P1–P7/ESN/NEAT option-space evaluation (summarized here only insofar as it justifies the pick), and the cascor-side middleware refactor mechanics.

## 0.2 Naming: `juniper-recurrence` (← `juniper-recurse`)

The initiative was originally named **`juniper-recurse`**. It is being renamed to **`juniper-recurrence`** (the term of art for temporal/chain recurrence; see the recurrent-vs-recursive terminology decision, OQ-1/Answer-1 — the target is a *recurrent* network, the chain-structured special case of a recursive network, per Lipton et al. 2015).

**The rename is cost-free now and should be locked before any package is published** (same logic that made the `juniper-cascor-core` rename free — nothing is on PyPI yet; every workstream is `PLANNED`/`DEFERRED`). It implies the following carry-overs, none of which has shipped:

| Artifact | Old (`recurse`) | New (`recurrence`) |
|---|---|---|
| App repo | `pcalnon/juniper-recurse` | `pcalnon/juniper-recurrence` |
| Client | `juniper-recurse-client` | `juniper-recurrence-client` |
| Model-specific core | `juniper-recurse-model` | `juniper-recurrence-model` |
| (future) worker | `juniper-recurse-worker` | `juniper-recurrence-worker` |
| Settings env prefix | `JUNIPER_RECURSE_` | `JUNIPER_RECURRENCE_` |
| Conda env (if dedicated) | `JuniperRecurse` | `JuniperRecurrence` |

**All `WS-*`, `OQ-*`, `RK-*`, `R-Δt-*`, `C1–C5`, and `P1–P7` identifiers are preserved verbatim** from the prior documents so existing references (PRs, commits, memory notes) keep resolving. The rename is tracked as a new decision item (§9.1, §10 OQ-19).

## 0.3 How this document was produced

This is a *review-and-synthesis* deliverable. The following prior artifacts were read in full or digested:

**Notes (design/eval corpus):**

- `JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md` — the decision map (read in full).
- `JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` — the four Δt approaches + Approach-C math + verification (digested in full).
- `JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md` — model landscape, top-3, §1.3.4 Δt-native LMU, OQ answers (digested in full).
- `JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` — integration seam, model-core/service-core, WS/OQ/RK registers (digested in full).
- `JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md` — P1/P2/P3 proposals + Workstream-0 + BPTT/RTRL (read in full).
- `JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-DELAY-LINE-NODE-DESIGN-EVAL.md` + `JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-OQ4-DELAY-LINE-OUTPUT-MODULE-EVAL.md` — P4 (digested).
- `JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-P7-GRAZZI-BLOCK-DESIGN.md` — P7 ceiling-breaker (digested).
- `JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md` + `JUNIPER_2026-06-05_JUNIPER-ECOSYSTEM_CODE-ORGANIZATION-STRATEGY.md` — placement/naming (digested).

**POC scripts (`util/ad-hoc/`):** `verify_delta_t_reference_code.py` (read in full — the Approach-C reference), `verify_oq4_expressivity_suite.py`, `verify_delay_line_node_eval.py`, `verify_fir_horizon_boundary.py`, `verify_p5_recurrent_output_eval.py`, `verify_p6_narx_mlp_output_eval.py`, `verify_p7_grazzi_block_growth.py`.

**Literature:** `papers/NeurIPS-2019-legendre-memory-units-...pdf` (LMU paper, on disk) + the verified citation set (§11).

**Concurrent-session work incorporated (2026-06-14, post-merge).** After this synthesis was drafted, four further recurrence documents merged to `main` from a parallel session and are reconciled here:

- `JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-ARCHITECTURE-REEVALUATION.md` — a *second*, distinct 2026-06-12 re-eval (188-agent; P6 / P2-P3-hybrid / P3-C-pairings / LMU-SSM), notable for the **REPRESENTABILITY vs LEARNABILITY vs DEPLOYED-bound** axis separation and the same bottom line (ship P3-C/LMU via Approach-C fixed-order + P1; P2 only if counting required; P6 as representability reference). Complements — does not duplicate — the `…EXHAUSTIVE_REEVALUATION…` decision map.
- `JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md` — the standalone dataset audit (exception list empty; irregular Δt is the one cross-cutting demand).
- `JUNIPER_2026-06-10_JUNIPER-RECURRENCE_RECURSE-OQ4-P5-RECURRENT-OUTPUT-LAYER-EVAL.md` — the P5 evaluation.
- **`JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md`** — the **build-side** scoping of current-work item (c): exactly how cascor must change to ingest 3-D windows. Its findings refine §4.3 (the "ndim>2 cap" is a three-tier boundary, not one cap), §6.1/§6.6 (cascor drops the Δt channel today), and §9.1(c) (Path A flatten=P4 trap vs Path B recurrent). VERIFIED-CODE against cascor `main @ 0914ca1`, 5-agent validated.

## 0.4 Relationship to the existing documents

This document is the **model-pick depth** for the Δt axis. It sits atop:

- the **model doc** (`…MODEL_DESIGN_AND_PLAN…`) — which ranks the candidates and introduces P3-C as §1.3.4;
- the **refactor doc** (`…MIDDLEWARE_REFACTOR…`) — which owns the substrate, the shared packages, and the WS/OQ/RK registers;
- the **Δt doc** (`…DELTA_T_HANDLING…`) — which owns the Approach A–D analysis and the reference math;
- the **OQ-4 reevaluation** — which settled that no cheap/cascor-native option breaks the star-free ceiling and that the ceiling is not binding for the current catalog.

Where any of those is more authoritative on a cross-cutting point, it governs; this document does not restate their full content.

## 0.5 Binding platform constraints (C1–C5)

These constrain every design choice below. The most load-bearing is **C1**.

- **C1 — First-principles implementation.** *"…implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail… candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper."* → recurrence, state, and growth must be **inspectable code**, not a `torch.nn.LSTM`/solver black box. **This is precisely why P3-C wins (§1, §2.4): it is the only continuous-time option that is C1-clean.**
- **C2 — Dual-mode app shape.** FastAPI `create_app()` + standalone CLI `main.py`; Pydantic settings with env prefix `JUNIPER_RECURRENCE_`; canonical 6-field `AGENTS.md` header.
- **C3 — Shared-data contract.** Datasets flow `juniper-data → juniper-data-client → model` as NPZ; all dataset capability lives in `juniper-data`; the model never slices raw series.
- **C4 — Shared observability.** `juniper-observability >= 0.3.1` (fleet floor); new Prometheus collectors via `register_or_reuse` & friends.
- **C5 — Conventions.** Python ≥ 3.12, line length 512, pytest + 80% coverage, worktree procedures, `util/` script placement.

## 0.6 Status & ratification state

| Item | State |
|---|---|
| Model pick on the **Δt axis** | **P3-C / LMU + Approach-C** — selected; **WS-0 RATIFIED 2026-06-14 (Paul)** |
| Star-free ceiling-breaker | **deferred** (P7/Grazzi route; trigger-gated, §9.2) — not part of this model |
| Data foundation (3-D NPZ + Δt keys + temporal split) | **SHIPPED** in juniper-data (#168 → #169/#170/#171 + data-client #87, merged 2026-06-09); `equities_seq` 3-D generator shipped 2026-06-13 |
| Model build (WS-4) | `PLANNED` — this document is its design input |
| Deployment as a grown cascade unit | **open research question** (§4.2) — fixed-order ships first |

---

# Part 1 — Executive summary: the decision and its logic

## 1.1 The model

**P3-C (LMU + Approach-C):** a Legendre Memory Unit whose linear memory cell is discretized **in closed form at the actual per-step time gap Δt**, via a matrix exponential of a *fixed* Legendre state matrix. The model carries a genuine, continuously-evolving recurrent state; its memory window is a single interpretable hyperparameter (θ); and its handling of irregular sampling is exact (zero-order-hold integration across the real gap), not learned and not approximated.

## 1.2 Why it was chosen — the decision narrative

Three findings, established empirically and from web-verified theory in the OQ-4 reevaluation, drive the pick:

1. **The Δt axis is the requirement that forces a model change.** Paul ratified (OQ-7 / Answer-7, 2026-06-06) that **the ability to process/regress on irregular-Δt datasets is a *critical, gating* requirement** for a completed state — intermediate phases may defer it, but the finished model may not. The dataset audit independently confirms the live use-case's hard axis is timing: `equities` is persistence-dominated (`|corr|≈0.998`; memory adds ≤0.13) with informative calendar gaps (1-day 78.3%, Fri→Mon 3-day 18.1%, holiday 4-day 2.6%). The signal worth modeling there is **when**, not how-much-history.
2. **Among all options, only the LMU is Δt-native and C1-clean.** Of the four Δt-handling strategies (§2.4), only Approach C delivers true continuous-time semantics, and it does so *without* an ODE solver — just a matrix exponential of a fixed, closed-form matrix. Empirically it is the **only measured Δt win**: grid-invariant reconstruction error `e_irr ≈ 0.039–0.043` vs regular-grid `e_reg ≈ 0.035` (≈1.15×), against P4-FIR's 7.8× degradation on the same irregular grid.
3. **The star-free ceiling — the limitation that dominated the initial design bias toward "real recurrence" — is not a binding constraint here.** The key discovery: **the star-free ceiling is a property of the dynamical-state substrate, not of capacity, depth, output richness, or memory length.** The entire star-free family (RCC, P4/P5/P6, ESN, LMU, nonnegative SSM) inherits it; *no* juniper-data dataset (built or planned) requires breaking it (the exception list is empty — `xor`/`checkerboard` are static-spatial parity, `arc_agi` is program synthesis, equities/equities_seq are memoryless-1-step). LMU inheriting the ceiling is therefore **not a defect for this platform's workload.**

**⇒ The pick is P3-C/LMU for the Δt-native fixed-order model, complemented by P1 (self-recurrent RCC candidate) for cheap hidden recurrence inside the cascade framework.** The cheap "P4-FIR + Δt-as-feature" default that the reevaluation recommends as the *near-term floor* is superseded *specifically because OQ-7 makes Δt-nativeness gating* — the one axis the reevaluation named as able to force the change.

## 1.3 What this model explicitly is NOT

- **It is not a star-free ceiling-breaker.** An LMU is a diagonal/nonnegative state-space model; it provably cannot do parity / modular counting / non-solvable-group tracking (Sarrof–Veitsman–Hahn 2024; all SSMs ∈ TC⁰, Merrill–Petty–Sabharwal 2024). Its value is **Δt-nativeness + transparency**, never wider expressivity. (An earlier "ESN/LMU escape the ceiling" framing in the model doc was a category error, corrected in place 2026-06-13.)
- **It is not, initially, a grown cascade unit.** The LMU is fundamentally a *fixed-order* model (its "growth" is choosing memory order `d`). It ships first as a standalone fixed-order model behind the common interface (§4.1). Growing it as a cascade candidate is an open research question (§4.2).

## 1.4 Headline PROs / CONs (expanded from the brief)

**PROs.**

- **C1-clean.** Matrix-exp of a *fixed* Legendre matrix `A`; `B` not learned; neither data-dependent. No ODE solver, no autodiff-through-solver. "Transparent without being trivial" (R-Δt-8).
- **Strongest Δt bias of all options** — the `dt` channel *is* the discretization step; the inductive bias toward real-time dynamics is built into the integrator, not learned.
- **Most transparent recurrent option** — every matrix is inspectable; eigenvalues are stable by construction (all `Re(λ) < 0`).
- **Longest controllable horizon** — the window θ is an explicit real-time knob, decoupled from parameter count (the LMU paper demonstrates 10⁵-step dependencies).
- **Genuinely recurrent** — a continuously-evolving state `m(t)`, not a finite delay-embedding (contrast P4-FIR).
- **Best measured irregular-Δt capability** — grid-invariance ≈1.15× (§3.7).
- **Future-proofing** — HiPPO (Gu et al. 2020) unifies the LMU with S4/Mamba; the same per-step `Δ` discretization is the SSM family's mechanism. An LMU is the low-risk stepping stone to structured state-space capability.

**CONs.**

- **Inherits the star-free ceiling** — *but this is not an issue for any current or planned dataset* (§1.3, §2.3). Equities forecasting is not a counting task.
- **No fixed-Δt negative control in the POC** — "fixed-Δt fails the `e_irr` bound" is currently an **analytic assertion, not a measurement** (the POC only instantiates the variable-step memory). Closing this is current-work item (a) (§9.1).
- **Grown-structure deployment is open** — instantiating P3-C as a grown cascade unit is a critical, still-open question; the homogeneous-pool growability gap and the worker `ndim>2` cap both bear on it. **Mitigation: ship fixed-order first** (§4.1), which sidesteps both.
- **LMU-only Δt-nativeness** — Approach C does not generalize to RCC/ESN units (they use Approach A/B). It advantages the third-priority unit type.
- **Eigenvector conditioning at large `d`** — keep `d ≲ 64`; Padé scaling-and-squaring fallback for larger orders (§3.6).

---

# Part 2 — Theory & background

## 2.1 The problem: irregular-Δt time-series regression

Real temporal data is not sampled on a uniform grid. Equities trade on business days with weekend and holiday gaps; event-driven and sensor data arrive at arbitrary times. A model that treats each step as "one tick" silently assumes a regular grid and discards the timing signal. The requirement (OQ-7, gating) is a model whose memory dynamics respond to the *real elapsed time* `Δt` between observations.

Naïve fixes inject bias (Approach D, §2.4): binning-to-grid + imputation fabricates structure (resampling fabricates ~2/7 of the equities series), blurs timing, and makes grid resolution itself a bias/variance knob. The principled answer is a **continuous-time** memory that is evaluated at the actual gap.

## 2.2 The Legendre Memory Unit (LMU)

The LMU (Voelker, Kajić & Eliasmith 2019, NeurIPS) maintains a compressed, continuous-time representation of an input's recent history by **orthogonalizing that history onto the Legendre polynomial basis** over a sliding window of length θ. The memory state `m(t) ∈ ℝ^d` holds the first `d` Legendre coefficients of the input over `[t−θ, t]`. It obeys a *linear* ordinary differential equation with **fixed, closed-form** matrices:

```
θ · ṁ(t) = A · m(t) + B · u(t)
```

with (derived from the shifted-Legendre projection; equivalently the HiPPO-LegT operator, Gu et al. 2020):

```
A[i, j] = (2i + 1) · ( −1            if i < j
                       (−1)^(i−j+1)  if i ≥ j )
B[i]    = (2i + 1) · (−1)^i                              i, j ∈ {0, …, d−1}
```

Two properties make this special for our purposes:

1. **`A` and `B` depend only on the order `d`** — they are **not learned and not data-dependent**. θ sets the memory window in real-time units (the same unit as `dt`).
2. The system is **linear**, so its *exact* discretization is a matrix exponential — no numerical ODE solver is required. This is the hinge of Approach C (§3).

The full LMU cell couples this linear memory to a (small) nonlinear hidden state; for the Δt-native regression model the trained parts are the **read-in** (features → scalar/low-dim drive `u`) and the **readout** (memory state `m` → output), with the memory matrices fixed. Memory order `d` is the single principled capacity knob (the paper reports an `O(d/√m)` delay-approximation error bound for the spiking implementation). Growth, if ever pursued, is "increase `d`."

## 2.3 The star-free ceiling — and why it does not bind here

**The discovery.** Recurrent Cascade-Correlation captures *exactly* the **star-free / group-free regular languages** (Giles et al. 1995; Kremer 1996; Knorozova & Ronca 2024, AAAI) — no modular/parity counting, no cyclic-group structure. The deeper, unifying result from the OQ-4 reevaluation: **this ceiling is a property of the dynamical-state substrate, not of capacity, depth, output richness, or memory length.** Concretely, measured on held-out running parity (majority floor 0.531) and mod-3:

| Candidate | held-out parity acc | margin vs floor | verdict |
|---|---|---|---|
| P5 — single recurrent output | 0.477 | −0.054 | fail |
| P6 — NARX hidden-MLP (Hd 16/32) | 0.513 / 0.507 | −0.018 / −0.024 | fail (the "credible breaker") |
| ESN — linear / mlp readout | 0.456 / 0.479 | −0.076 / −0.052 | fail (worst) |
| **LMU — linear / mlp readout** | **0.496 / 0.496** | **−0.036** | **fail** |

Enriching the output (P6's MLP), lengthening memory (LMU reaches horizon 40, the furthest of any candidate), or adding a random reservoir (ESN) — none lifts the ceiling. Only injecting **group structure / negative (non-commutative) recurrence into the state itself** does (P2 group units — no recipe; the Grazzi negative-eigenvalue linear-RNN — general + trainable but non-cascor; NEAT — topological, replaces the engine). **The LMU is squarely in the star-free family and inherits the ceiling.**

**Why it does not bind.** The dataset audit (OQ-4 reeval §5; the dedicated dataset audit, 2026-06-13) characterized every juniper-data generator:

| Dataset | task | temporal? | needs counting/group? |
|---|---|---|---|
| `checkerboard`, `xor` | classification | no | **no** (static-spatial `%2`; stateless MLP solves) |
| `circles`, `gaussian`, `moon`, `spiral`, `mnist` | classification | no | no (i.i.d.) |
| `equities`, `equities_seq` | regression | **yes** | **no** (persistence-dominated; hard axis = irregular Δt) |
| `arc_agi` | reasoning | grid→grid | **no — orthogonal** (program synthesis) |
| planned synthetics (`multi_sine`, `mackey_glass`, `ar_p`) | regression | yes | **no** (fading/bounded memory) |

**No dataset — built or planned — demands the ceiling-break; the exception list is empty.** The one temporal axis that *is* demanded is irregular Δt, which is exactly what P3-C delivers. So the LMU's ceiling is a non-issue for the workload, and the gating requirement (Δt) is met.

## 2.4 The four Δt-handling approaches — and why C

The original design "boxed itself in": *best Δt tool needs a solver → solver breaks C1 → defer Δt.* The missing observation: **continuous-time Δt handling does not require an ODE solver** — the LMU's *linear* memory already contains a solver-free one.

| | **A — Δt as input** | **B — Δt-gated decay** | **C — solver-free continuous-time LMU** | **D — resample + impute** |
|---|---|---|---|---|
| **Mechanism** | feed `dt` as an extra input dim | `h ← h·exp(−Δt/τ)`, learnable per-unit τ | discretize the LMU memory at the actual per-step Δt (§3) | grid + impute in juniper-data, mark `observed_mask` |
| **Models** | RCC/ESN/LMU unchanged | RCC + ESN + LMU | **LMU only** | all (unchanged) |
| **C1** | cleanest (Δt is data) | clean (exp is elementary) | **clean (matrix-exp of a fixed closed-form matrix)** | clean (no model change) |
| **Bias strength** | weak (must learn) | strong (real-time forgetting) | **strongest (true continuous memory)** | n/a (lossy) |
| **Key weakness** | presentation, not mechanism | perturbs ESP (ESN) / freeze (RCC) | advantages 3rd-priority unit; matrix-exp cost | fabricates data; informative-sampling lost |
| **Primary guardrail** | shuffle-`dt` degradation test | variable-Δt ESP/delay tests | grid-invariance delay test (§3.7) | mask must be consumed |

**Verdicts (Δt doc §10–§11):** **A is the default model handling** (works across all units, maximally C1-clean, but weak bias). **C is the principled target when irregular-Δt becomes a priority** — and it has (OQ-7 gating). **B** is the RCC/ESN-compatible middle path *if* those remain priority units. **D** is rejected (fabricates data; informative-sampling lost). Solver-based continuous-time models (Neural-ODE/Latent-ODE/LTC) are deferred on C1 grounds — the deferral applies to *solver-based* models, **not** to continuous-time handling per se, because Approach C exists.

## 2.5 The two SSM walls — where the LMU sits

A useful precision point: "the SSM ceiling" is **two** walls, and the LMU sits at the first.

| Level | Example | Group character | A diagonal/nonnegative SSM (LMU) |
|---|---|---|---|
| **(A) star-free / aperiodic** | "contains substring", flip-flop | trivial groups | **✓ can** (better than transformers here) |
| **(B) modular counting** | parity (Z₂), mod-3 | Abelian/solvable | **✗ if nonnegative** (Sarrof–Veitsman–Hahn 2024); ✓ only with negative/complex eigenvalues + input-dependence (Grazzi 2025) |
| **(C) non-solvable-group tracking** | S₅ permutation composition | non-solvable | **✗ for *any* SSM** — all SSMs ∈ TC⁰ (Merrill–Petty–Sabharwal 2024) |

Consequence: stepping outside cascor to an SSM buys **no** free ceiling-break (nonnegative SSMs are *exactly* star-free and carry a *second*, harder wall). The genuine LMU/SSM win is **continuous-time Δt-nativeness**, the Approach-C win — not expressivity. The LMU is the C1 sweet spot (matrix-exp of a fixed closed-form matrix) but, as a diagonal SSM, is solvable-groups-bounded.

---

# Part 3 — Model design: the Δt-native LMU unit (Approach-C)

This is the heart of the model. The full, runnable reference is in **Appendix A**; this part explains it.

## 3.1 The continuous system

The memory `m ∈ ℝ^d` (Legendre coefficients of the input history over window θ) obeys `θ·ṁ = A·m + B·u`, with the fixed `A`, `B` from §2.2. Rewrite as `ṁ = M·m + N·u`, where `M = A/θ`, `N = B/θ`.

## 3.2 Exact zero-order-hold (ZOH) discretization — Δt enters as the step

Holding `u` constant across an interval of *real* duration `Δt` (zero-order hold), the **exact** discrete update is:

```
m_{k+1} = Ā(Δt) · m_k + B̄(Δt) · u_k
Ā(Δt)  = exp(M · Δt) = exp((A/θ) · Δt)
B̄(Δt)  = M⁻¹ (Ā(Δt) − I) N  =  A⁻¹ (Ā(Δt) − I) B     (the θ cancels, since M⁻¹N = A⁻¹B)
```

The single, decisive observation: **standard LMU implementations bake `Ā`, `B̄` as constants for one fixed Δt; the only change for irregular sampling is to evaluate them at the actual gap `Δt_k`.** The dataset's `dt` channel (§6.1) *is* the discretization step — exactly the role the per-step `Δ` parameter plays in S4/Mamba. There is no ODE solver and no autodiff through a solver: just a matrix exponential of a small, fixed matrix.

## 3.3 Efficient per-step update via eigendecomposition

`A` is a fixed `d×d` matrix; **diagonalize it once**: `A = V·Λ·V⁻¹`, `Λ = diag(λ_0,…,λ_{d−1})` (eigenvalues come in conjugate pairs, all with negative real part → stable). Then each step needs only scalar exponentials:

```
z_i(Δt) = λ_i · Δt / θ
Ā(Δt) = V · diag( e^{z_i} )             · V⁻¹
B̄(Δt) = V · diag( expm1(z_i) / λ_i )    · (V⁻¹ B)
```

`V`, `V⁻¹`, `Λ`, `V⁻¹B` are **precomputed once** (they depend only on `d`, θ). Per step: `d` scalar `exp`/`expm1` evaluations + two `d×d` mat-vecs — or, if `dt` is quantized (e.g. integer calendar-day gaps for equities), **cache `Ā`, `B̄` per distinct bucket** (a handful of values). The removable singularity `(e^z − 1)/λ → Δt/θ` as `λ → 0` is handled for hygiene (LMU's `A` has no zero eigenvalue). `expm1` (not `exp(z) − 1`) avoids catastrophic cancellation at small `z`.

## 3.4 What is learned vs. fixed — the C1-clean property

| Component | Status |
|---|---|
| `A`, `B` (memory matrices) | **Fixed.** Depend only on order `d`. Not learned, not data-dependent. |
| `V`, `V⁻¹`, `Λ`, `V⁻¹B` (eigendecomposition) | **Precomputed once.** Depend only on `d`, θ. |
| `Δt` (the `dt` channel) | **Data.** The per-step discretization step, supplied per observation. |
| θ (window), `d` (order) | **Hyperparameters** — inspectable, validated. `d ≈ 4…64`. |
| read-in (features → drive `u`) | **Trained** (linear projection). |
| readout (memory `m` → output) | **Trained** (linear; optionally a small nonlinear hidden layer). |

This is the literal content of C1-clean: the recurrent dynamics are a matrix exponential of a fixed, closed-form, fully-inspectable matrix — the *opposite* of an ODE-solver black box. Only the thin read-in/readout layers are trained, mirroring cascor's own output-training discipline.

## 3.5 Reference implementation (excerpt)

The verified reference (numpy; Appendix A has the full file) is the `VariableStepLMUMemory` class. Its core:

```python
import numpy as np
from numpy.polynomial.legendre import Legendre

def lmu_matrices(d: int):
    """Fixed, closed-form Legendre (HiPPO-LegT) state matrices. Not learned, not data-dependent."""
    A = np.zeros((d, d)); B = np.zeros((d, 1))
    for i in range(d):
        B[i, 0] = (2 * i + 1) * ((-1) ** i)
        for j in range(d):
            A[i, j] = (2 * i + 1) * (-1.0 if i < j else (-1.0) ** (i - j + 1))
    return A, B

class VariableStepLMUMemory:
    """C1-clean variable-Δt LMU memory: matrix-exp of a FIXED matrix, evaluated at each real gap dt_k."""
    def __init__(self, d: int, theta: float):
        self.d, self.theta = d, float(theta)
        A, B = lmu_matrices(d)
        lam, V = np.linalg.eig(A)
        self.lam, self.V = lam, V
        self.Vinv = np.linalg.inv(V)
        self.VinvB = self.Vinv @ B

    def step_matrices(self, dt: float):
        z = self.lam * (dt / self.theta)
        Abar = (self.V * np.exp(z)) @ self.Vinv
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = np.expm1(z) / self.lam               # expm1 → no cancellation at small z
        fac = np.where(np.abs(self.lam) < 1e-12, dt / self.theta, fac)   # removable singularity
        Bbar = (self.V * fac) @ self.VinvB
        return Abar.real, Bbar.real

    def rollout(self, u: np.ndarray, dt: np.ndarray):
        m = np.zeros((self.d, 1)); out = np.zeros((len(u), self.d))
        for k in range(1, len(u)):                     # u[k-1] held across (t[k-1], t[k]] of length dt[k]
            Abar, Bbar = self.step_matrices(float(dt[k]))
            m = Abar @ m + Bbar * u[k - 1]
            out[k] = m[:, 0]
        return out

    def decode_weights(self, rho: float):
        """Read the memory at a delay rho*theta into the past via shifted-Legendre evaluation."""
        x = 2.0 * rho - 1.0
        return np.array([Legendre.basis(i)(x) for i in range(self.d)])
```

**Production note (torch).** In the shipped model the memory rollout is a fixed linear recurrence (no gradient flows through `A`/`B`), so `Ā`/`B̄` are precomputed constants (or per-bucket cached tensors); only the read-in and readout are `nn.Module` trained parameters. This keeps the autodiff graph thin and the C1 transparency intact (§3.4). The torch port mirrors the numpy reference 1:1; see Appendix A note.

## 3.6 Numerical guardrails

- **Conditioning (R-Δt-5).** The LegT `A` becomes ill-conditioned in `V` for large `d` (Vandermonde-like). **Keep `d ≲ 64`.** Fallback for larger `d`: Padé scaling-and-squaring of `M·Δt` (`scipy.linalg.expm`-style) plus the integral form of `B̄`, with a documented error bound — slower but robust.
- **Stability is automatic for Δt > 0.** `Re(λ_i) < 0 ⇒ |e^{z_i}| < 1`, so `Ā` is a contraction; no blow-up. Large `Δt/θ` simply drives memory toward zero (expected, not an error).
- **Small-gap accuracy.** Use `expm1`, not `exp − 1`.
- **Caching.** If `dt` is quantized (calendar-day integers 1–7 for equities), cache `Ā`, `B̄` per distinct gap.

## 3.7 Empirical verification status

Executed via `util/ad-hoc/verify_delta_t_reference_code.py` (numpy 2.4.4, Python 3.13, deterministic):

| Check | Result | Bound |
|---|---|---|
| LMU `A` (d=16) max eigenvalue real part | **−6.49** | < 0 (stable; no sign error) ✓ |
| Reconstruction RMSE `e_reg` (d∈{16,24}, ρ∈{0.5,0.8,1.0}) | **0.035** | < 0.05 ✓ (ZOH-floor-limited, ~flat in d/ρ) |
| Grid-invariance `e_irr` (irregular grid) | **0.039–0.043** (≈1.15× `e_reg`) | < 3·`e_reg` + 0.02 ✓ |
| Windowing invariants I1–I5 (2-ticker irregular example) | **all hold** | — |

So the Approach-C math is correct as written, the tolerances hold with margin, and the windowing satisfies the leakage invariants. `e_reg` is ZOH-floor-limited (not order-limited) — increasing `d` past ~16 barely moves it at this step size; to drop it, shrink the mean step or use a higher-order hold.

**⚠️ The one gap (CON, current-work item a).** There is **no executed fixed-Δt negative control.** The statement "a *fixed*-Δt discretization fails the `e_irr` bound on the irregular grid" is presented as "the proof Approach C delivers," but the POC only instantiates `VariableStepLMUMemory`; no fixed-Δt RMSE on the irregular grid is measured or tabulated. **"Fixed-Δt fails the bound" is an analytic assertion, not a measurement.** Closing it (adding the negative control to the POC) is §9.1(a) — a small, high-value diligence step that converts the central claim from analytic to empirical.

---

# Part 4 — Two-step implementation path

## 4.1 Step 1 — fixed-order standalone model behind the common interface

**Ship the LMU as a fixed-order `TrainableModel` first.** This is the natural shape of an LMU (the memory order `d` is chosen, not grown) and it **sidesteps both unresolved blockers** (§4.3):

- it does not enter cascor's candidate-growth loop, so the **homogeneous-pool growability gap** is irrelevant;
- in fixed-order form the model can run in-process (no distributed candidate training), so the **worker `ndim>2` cap** is not on the critical path for a first release.

The fixed-order model is a clean fit for `juniper-model-core`'s `TrainableModel` contract (§6.3): `fit`, `predict`/`forward`, `input_shape`/`output_shape`, `task_type="regression"`, `metrics()`, `describe_topology()`. Its `describe_topology()` advertises a `kind="memory"` node set (the Legendre memory) plus the trained read-in/readout — enough for canopy to render it model-agnostically. This is the safe, golden-gated first deliverable.

**Independently corroborated by the build-side investigation.** The `…CASCOR_3D_INGESTION_GATE_2026-06-14.md` analysis reaches the same shape from the code side: scope the recurrent model as **"a 3-D-native recurrent block fronting the existing 2-D cascade head," built fixed-order *outside* the cascade growth loop** — which "sidesteps both the candidate-growability question and the per-unit 2-D math." So a 3-D window is consumed (with `dt`) by the LMU block, which emits a 2-D representation the unchanged cascade head trains on as today. This is exactly Step 1, and it is why neither blocker is on the critical path.

## 4.2 Step 2 — grown cascade unit (open research question)

A later, more ambitious step is to instantiate the LMU memory as a **grown cascade candidate** — a small fixed recurrent block added by the cascor growth loop (train read-in/readout by correlation, install, freeze on tenure), mirroring P3 in the proposals doc. **This is a critical and as-yet-open question** for two reasons:

1. The model doc itself is internally inconsistent on this point — at places it treats the LMU as a swappable grown unit type, at others (correctly) as a fixed-order `TrainableModel` whose "growth" is choosing `d`. **Reconciliation (current-work item b, §9.1): the LMU is fundamentally fixed-order; ship it fixed-order first; treat grown-LMU-blocks as research.**
2. Growing fixed memory blocks as candidates runs into the homogeneous-pool growability gap and (for distributed training) the worker `ndim>2` cap (§4.3).

## 4.3 The two blockers (and why Step 1 avoids them)

- **Homogeneous-pool growability gap.** Cascor's candidate pool is *homogeneous in code* — every candidate is the same kind of single-shot scalar unit (`candidate_unit.py`), trained one-at-a-time against frozen units, installed, and frozen. There is no mechanism today to grow a *heterogeneous* pool containing state-carrying memory blocks alongside scalar units, nor a correlation-compatible recipe for training such a block as a candidate. (This is the growability analog of the star-free architectural gap: the cascor growth machinery is built for one unit shape.) **Fixed-order LMU does not grow candidates at all → gap avoided.**
- **The cascor 2-D ingestion gate (the "ndim>2 cap" is really a three-tier boundary).** The shorthand "worker `ndim>2` cap" under-describes the situation; the build-side investigation (`…CASCOR_3D_INGESTION_GATE_2026-06-14.md`, VERIFIED-CODE) decomposes it into three tiers:
  1. **Tier 1 — hard rejection gates (plumbing).** The in-process `SharedTrainingMemory` binary descriptor packs only two shape dims (`cascade_correlation.py:272-273`, descriptor `:301-317`) — *this* is the literal "ndim>2 cap." Cheap to extend: `"<QQBBII6x"` (32 B) → `"<QQBBIII2x"` (32 B) adds a third dim without growing the descriptor.
  2. **Tier 2 — ~10 silent mis-index sites** (`shape[1] ≡ features`) that run on 3-D but read the *lookback* axis.
  3. **Tier 3 — the algorithmic core (the real boundary, not a gate).** cascor's forward GEMM (`:1979`), hidden-unit sum (`:1939-1946`, `dim=1`), candidate correlation (`candidate_unit.py:479`), and output layer are **all 2-D by construction**. This is the feed-forward↔recurrent boundary itself.
  Two IPC paths differ: the **in-process pool** is blocked at Tier 1 (the 2-D descriptor); the **distributed worker** transport (`SharedBinaryFrame`) is **already N-D-capable** (round-trips up to `ndim=10`) — so the worker is *transport-ready but not math-ready* (it still runs the 2-D `CandidateUnit`). **Fixed-order LMU trains in-process and, built as a recurrent block fronting the 2-D cascade head (§4.1), needs neither the descriptor change nor a worker-math rewrite for a first release → the whole gate is off the critical path.** (Lifting Tier 3 = building distributed recurrent candidate training = WS-8/OQ-11, deferred.)

## 4.4 Migration lever: `T=1` is identity to current cascor

Because a 1-step window (`T=1`, `h₀=0`) is exactly today's feed-forward model, the recurrent substrate can ship behind a default `T=1` (no behavior change) and then enable `T>1`. The conformance kit asserts that a `T=1` recurrent model matches the feed-forward model exactly — the golden-gated cutover the refactor wants. The 3-D NPZ contract is a strict superset of the 2-D contract (`X.ndim==2 ⇒ (n,1,F)`), so 2-D consumers are untouched.

---

# Part 5 — The temporal substrate (Workstream-0 dependency)

Even the fixed-order LMU needs a *time axis*, which cascor lacks today. This is the shared "Workstream 0" prerequisite. For the **fixed-order** model the substrate need is modest (a sequence-aware data path + a stateful forward); the heavier recurrence-aware-gradient items below are only needed for the **grown** form (Step 2).

## 5.1 Cascor is stateless 2-D feed-forward today

`CandidateUnit.forward` is a scalar dot-product; `_update_weights_and_bias` builds a single-shot autograd graph with no BPTT; frozen units are a 4-key dict `{weights, bias, activation_fn, correlation}` with no slot for recurrent state; output training is a static `nn.Linear` over a flat matrix; the worker ships fixed scalar tuples over 2-D tensors. There is **no time axis anywhere.**

## 5.2 Gradient: BPTT-over-window default; RTRL deferred

The window is bounded (T ∈ 1..~30, Paul's variable-window decision, OQ-a). At `T ≤ 30` a full unroll is memory-trivial, so **full BPTT over the window via autograd is the default** (reuses cascor's existing autograd path; composes naturally with the batch-global mean-centered correlation objective). **RTRL** (Williams & Zipser 1989; Fahlman-faithful) is documented as deferred future work — it wins for unbounded sequences / online / streaming, but its forward per-step accumulation composes awkwardly with the global correlation statistic and it is bespoke (no autograd safety net). Trigger conditions to revisit RTRL: the window cap is removed, an online/continual mode is added, streaming inference-time adaptation is wanted, BPTT truncation is shown to harm, or joint multi-unit recurrent training makes BPTT memory problematic. *(For the fixed-order LMU readout, training is a static fit over the memory states — no BPTT through the memory at all, since `A`/`B` are fixed.)*

## 5.3 The freeze property localizes recurrence

With all hidden units frozen and outputs not fed back, output-layer training stays a static fit over flattened readout rows — the same regression cascor already does. **Live recurrence (in the grown form) is confined to candidate training**, one candidate at a time against frozen units. This confinement is what makes recurrent cascor tractable, and it is why the fixed-order LMU (no candidate growth) is so much simpler.

## 5.4 Variable output stride = dense state, sparse supervision

Carry a per-timestep readout mask `m(t) ∈ {0,1}`: the recurrence advances on every input step (state is dense), but loss/correlation accumulate only at readout positions (supervision is sparse). Special cases unify: readout-only-at-final-step ⇒ many-to-one; `T=1` ⇒ today's per-sample cascor exactly.

---

# Part 6 — Juniper ecosystem integration

## 6.1 The 3-D NPZ data contract (WS-1 — SHIPPED)

The additive 3-D contract is dispatched by `X.ndim` and is a strict superset of the 2-D contract. **Status: shipped in juniper-data (#168 → #169/#170/#171 + data-client #87, merged 2026-06-09).** Keys:

- `X`: `(n_windows, T_max=30, n_features)` float32, zero-padded.
- `seq_lengths`: `(n_windows,)` — actual length ≤ 30 (masks padded tail).
- `readout_mask`: `(n_windows, T_max)` bool — where targets/loss/correlation apply (the variable-stride mechanism).
- `y`: dense `(n_windows, T_max, output_dim)`, masked.
- **Δt keys (Approach-C critical):** `t` (absolute time per step) and/or `dt` (relative elapsed, `dt[:,0]=0`, `dt[:,k]=t[:,k]−t[:,k−1]`); `target_dt` (elapsed from last step to the predicted step). At least one of `{t, dt}` must be present for a 3-D artifact; `dt ≥ 0` everywhere; `time_unit` declared once in `meta.json` (e.g. `"calendar_days"`).
- `scaling`: persisted per-feature/target stats for reproducible denormalize.
- `task_type`: `regression | classification`.
- **Back-compat:** `X.ndim==2 ⇒ (n,1,F)`, `T=1`, single readout ⇒ byte-identical to current cascor.

The `dt` channel is exactly the per-step discretization step the LMU consumes (§3.2). For equities, `dt` = per-step elapsed calendar days (Fri→Mon = 3, holiday = 4). `equities_seq` emits `(W, 64, 10)` windows with `dt (W,L)` (`dt[:,0]==0`) and `target_dt (W,)`, and `juniper-data-client.validate_npz_contract` already dispatches on `X.ndim`.

**⚠️ Consumer gap (the real residual of RK-1).** cascor's own NPZ ingestion (`api/app.py:340-349`, `api/lifecycle/manager.py:2976-2988`) reads **only** the 2-D contract keys (`X_*`/`y_*`/`X_full`/`y_full`), does **not** call `validate_npz_contract`, and **never reads `dt`/`target_dt`/`observed_mask`/`ticker_code`** (exhaustive `src/` grep, zero hits — `…CASCOR_3D_INGESTION_GATE…` §7/§14). So the irregular-Δt signal that is the *entire rationale* for the P3-C pick is dropped at the cascor boundary today. **Consuming `dt` is part of the gate, not a later refinement** — and it is meaningful only under a recurrent (Δt-scaled state) path, never a flattened static GEMM. This is the substance of current-work item (c) (§9.1).

## 6.2 Windowing (juniper-data owns it — C3 boundary)

juniper-data owns slicing raw series into windows + the readout-position policy + scaling, exposing `window_size`/`stride`/`readout_policy` as generation params. **The model consumes pre-windowed artifacts and never slices raw series.** The reference `window_one_ticker` (Appendix A) enforces the leakage invariants:

- **I1** no cross-ticker windows; **I2** `max(train target_time) < min(test target_time)` (no future leak); **I3** monotone time (`dt[0]==0`, `dt[1:]>0`, `dt[1:]==diff(step_ordinals)`); **I4** embargo (no test window's first step predates the cut); **I5** `target_dt == ord(predicted_day) − ord(window_end_day) > 0`.

A model-side read-only sub-window view that only *shrinks* (≤ T_max) is a benign loader concern (avoids a dataset request per window-size sweep). The walk-forward split is deferred (WS-4).

## 6.3 `juniper-model-core` interfaces

The LMU plugs into the model template (a juniper-ml subdirectory package, D4-ratified):

- **`TrainableModel`** (the LMU's contract): `fit(X, y, X_val=, y_val=, **kw)`, `predict(X)`/`forward(X)`, `input_shape`/`output_shape`, `task_type ∈ {classification, regression}`, `metrics() -> dict`, `describe_topology()`.
- **`GrowableModel(TrainableModel)`** — for constructive models (RCC P1, Growing-ESN): `grow_step()`, `n_units`, growth hooks, `freeze()`. **The fixed-order LMU implements only `TrainableModel`** (not `GrowableModel`) — this is the interface-level expression of "LMU is fixed-order" (§4.1).
- **`describe_topology()`** schema (the seam canopy renders without knowing the model type):

```
{ "model_type": "lmu",
  "nodes": [{"id": str, "kind": "input|memory|hidden|output", "frozen": bool}],
  "edges": [{"src": str, "dst": str, "recurrent": bool}],
  "meta": {"n_units": int, "task_type": "regression"} }
```

- **`TrainingEvent`** vocabulary (`training_start/end`, `epoch_end`, `unit_added`, `phase_change`) — the fixed-order LMU emits `training_start`/`epoch_end`/`training_end` (no `unit_added`).
- **`ModelSerializer`** — the LMU serializes its hyperparameters (`d`, θ, `time_unit`), the precomputed eigendecomposition (or recompute-on-load from `d`/θ), and the trained read-in/readout. (No HDF5 weight-layout coupling.)

## 6.4 `juniper-service-core`

The de-cascored generic service layer (`create_app()`, `SettingsBase`, security/middleware, websocket + worker subsystems, generic routes, `TaskDistributor`). **juniper-recurrence is small**: its concrete LMU model, a `RecurrenceLifecycle(TrainingLifecycleBase)`, a `Settings(SettingsBase)` with prefix `JUNIPER_RECURRENCE_`, and a CLI problem (a time-series-regression analog of two-spiral — e.g. multi-sine or Mackey-Glass). Everything else is inherited via **subclass + inject** (not an entry-point registry). The critical compatibility hazard to clear: cascor's service layer **assumes 2-D classification** (`argmax`, a `shape[1]==2` gate) in the decision-boundary, metrics-history, metrics-collection, and auto-snapshot-best paths — a regression/time-series model must traverse generic routes with **no `argmax`, no accuracy** (RK-6; conformance kit drives a regression model through every route).

## 6.5 `juniper-canopy` generalization (WS-5)

Canopy already has a model-agnostic `BackendProtocol` (demo/service backends). Disposition for the LMU:

- **Reuse as-is:** server, `BackendProtocol`, websocket, observability, health, snapshot/redis/cassandra panels.
- **Adapt:** metrics panel (accuracy → MSE/MAE/R² driven by `task_type`/`metrics()`); dataset plotter (2-D scatter → time-series line plot); network visualizer (cascade columns → memory/topology view from `describe_topology()`); training-monitor phase names (generic vocabulary).
- **Replace/conditionally-render:** decision-boundary, candidate-metrics, cascade-evolution panels are cascor-specific — render only when a backend advertises them.
- **Add:** a `juniper-recurrence-client` backend behind `BackendProtocol`.
- Watch the Playwright/Dash `dbc.Input(type=number)` limitation — UI tests must POST the param endpoint directly (RK-12).

## 6.6 Worker / parallel protocol

For distributed recurrent candidate training the worker needs a 3-D `(B,T,F)` payload + `seq_lengths` + `readout_mask` + readout-masked correlation, an explicit ordering contract (**batch axis shardable/shuffleable; time axis immutable**), and the recurrent forward/gradient deployed worker-side (OQ-11). **Important nuance (from the build-side investigation):** the distributed worker's *transport* (`SharedBinaryFrame`) is **already N-D-capable** (round-trips up to `ndim=10`, with a passing 3-D test) — the blocker is its *math*, which still calls the 2-D `CandidateUnit` (`torch.sum(x*weights, dim=1)`). The two `CandidateUnit` copies (cascor `src/` and the cascor-core copy the worker imports) are byte-identical, so a math change must land in both (or in the single cascor-core source once the relocation/publish completes). **The fixed-order LMU (Step 1) trains in-process and does not require any of this**; distributed recurrent training is WS-8 (deferred, trigger = training cost).

## 6.7 Packaging & placement

Ratified placement/naming (2026-06-09):

- **`juniper-recurrence` (+ `-client`, future `-worker`) are model-specific → own repo** `pcalnon/juniper-recurrence` (gated on WS-0 + the model pick). Precedent: the cascor family.
- **Naming convention:** `-core` is reserved for *genuinely shared* abstractions (`juniper-model-core`, `juniper-service-core`); a model's *specific* implementation core takes the **`juniper-<model>-model`** suffix → a recurrence-specific core would be **`juniper-recurrence-model`**, homed as a *subdirectory of the model repo* (like `juniper-cascor-protocol` / the renamed `juniper-cascor-model`).
- **Shared `*-core` packages live as juniper-ml subdirectories** (D4) alongside observability/ci-tools/doc-tools/config-tools.
- **Governing rule:** place code by commonality; dependency arrow points *specific → common*, never the reverse; extend via interface-in-the-common-repo + adapter-with-the-model (ports & adapters, mechanism = subclass + inject). "The cost of model #20 must equal the cost of model #2."
- **juniper-ml extras:** add `juniper-recurrence-client` to extras; new shared packages to `[tools]`/`[all]`; update `test_pyproject_extras.py` in the same PR (RK-11).

## 6.8 Deploy, ports, env, migration

- **Dependency-resolution asymmetry (the crux).** On-host uses editable `pip install -e` from sibling repos; docker uses PyPI wheels pinned in `requirements.lock`. Two binding rules: **(1) publish-first is mandatory** — no consumer pins `juniper-service-core`/`juniper-model-core` until they are on PyPI (TestPyPI soak first), because docker cannot build from sibling source; **(2) the `pyproject.toml` pin bump and `requirements.lock` regen must land in the same change** (else `docker build` succeeds but the container `ModuleNotFoundError`s at runtime). Use the `rm -f requirements.lock` (or compile-to-`/tmp`-then-`mv`) regen recipe.
- **Docker image (WS-4).** Clone the **worker's CPU-lock two-stage pattern**, *not* cascor's (cascor's lock pulls full CUDA → ~7.5 GB). `EXPOSE 8210`; recurrence's own `requirements.lock` pins service-core/model-core/data-client/observability from PyPI.
- **Ports.** Compose: `"${BIND_HOST:-127.0.0.1}:${RECURRENCE_HOST_PORT:-8211}:${RECURRENCE_PORT:-8210}"`; `depends_on: juniper-data healthy`; healthcheck `:8210/v1/health/ready`; prometheus scrape added to **both** `prometheus.yml` and `prometheus.demo.yml`. On-host bind **8211** (8200 = duplicati, 8210 = worker health port — avoid both); add a launch block to `plant_all.bash` mirroring cascor.
- **Conda env (OQ-16).** Dedicated `JuniperRecurrence` env if CPU-torch is used (must copy the LIBTORCH isolate hook, as `JuniperCanopy1` has and `JuniperCascor1` does not); else reuse `JuniperCascor1`.

---

# Part 7 — Strengths, weaknesses, risks, guardrails

## 7.1 Strengths (consolidated)

C1-clean continuous-time memory (matrix-exp of a fixed matrix); strongest Δt inductive bias (the `dt` channel *is* the step); most transparent recurrent option (inspectable, stable-by-construction); longest controllable horizon (θ decoupled from params); genuinely recurrent (evolving state); best measured irregular-Δt capability (≈1.15× grid-invariance); SSM-bridge future-proofing (HiPPO → S4/Mamba); meets the gating OQ-7 requirement; small footprint; trained surface is only the thin read-in/readout.

## 7.2 Weaknesses & limitations (consolidated)

| Limitation | Severity for Juniper | Mitigation |
|---|---|---|
| Inherits the star-free ceiling | **Low** — no dataset needs the break (§2.3) | Don't position LMU as a breaker; P7 route exists if a counting dataset ever arrives (§9.2) |
| No fixed-Δt negative control measured | **Medium** — central claim is analytic | Add the control to the POC (§9.1a) |
| Grown-cascade-unit form is open | **Medium** — Step 2 only | Ship fixed-order first (§4.1); reconcile doc contradiction (§9.1b) |
| LMU-only Δt-nativeness | Low | Other units use Approach A/B; this advantages the 3rd unit deliberately |
| Eigenvector conditioning at large `d` | Low | `d ≲ 64`; Padé scaling-squaring fallback (§3.6) |
| ZOH-floor on `e_reg` | Low | Shrink mean step / higher-order hold if needed |
| 3-D worker path absent | Medium (Step 2 / distributed) | Fixed-order trains in-process; WS-8 deferred |

## 7.3 Consolidated risk register (model + Δt + integration)

| ID | Risk | L×I | Guardrail | WS |
|---|---|---|---|---|
| RK-1 | juniper-data can't serve time-series regression | High×High → **largely retired** (WS-1 shipped) | residual: wire 3-D into the consumer (§9.1c) | WS-1 |
| RK-2 | Star-free ceiling bites a chosen task | Low×Med (no dataset needs it) | scope to regression; P7 route gated on trigger | WS-4 |
| RK-3 | LMU/RCC regression unproven in lit. | Med×Med | golden known-answer tests; equities as the live anchor | WS-4 |
| RK-4 | Premature over-abstraction of model interface | Med×High | design ABC against ≥2 implementers (cascor + LMU) | WS-3 |
| RK-6 | Classification assumptions leak into "generic" routes | Med×Med | conformance kit drives a regression model through every route | WS-3 |
| RK-9 | NPZ change breaks consumers | Low×High (additive-only) | 2-D path byte-identical; version artifact | WS-1 |
| RK-13 | SSM/Mamba temptation toward black-box deps | Low×Med | Mamba baseline-only; S5/diagonal-S4 behind LMU | WS-4 |
| R-Δt-3 | "Δt presented ≠ Δt used" (Approach A false confidence) | Med×Med | shuffle-`dt` degradation conformance test | WS-1/4 |
| R-Δt-5 | matrix-exp instability / V ill-conditioning (large `d`) | Low×Med | `d ≲ 64`; scaling-squaring fallback; `expm1` | WS-4 |
| R-Δt-7 | NPZ contract ripple | Low×High | additive-only; `X.ndim` dispatch; 2-D byte-identical | WS-1 |
| R-Δt-8 | C1 pushback on Approach C | Low×Low | "transparent ≠ trivial": fixed-matrix exp is fully inspectable | WS-4 |

## 7.4 Guardrails & conformance tests

- **Grid-invariance delay test** (§3.7) — `e_irr < 3·e_reg + 0.02`; the model's core acceptance gate.
- **Fixed-Δt negative control** (to add, §9.1a) — assert a fixed-Δt scheme *fails* the bound the variable-step scheme passes.
- **State boundedness** across θ/Δt (LMU stability guardrail).
- **`T=1`-identity conformance** — a `T=1` recurrent model matches the feed-forward model exactly (golden cutover gate).
- **Windowing leakage invariants I1–I5** (Hypothesis property test, juniper-data).
- **Determinism** (seed → same trajectory within tolerance); **overfit-tiny sanity** (can memorize a tiny set).
- **Shuffle-`dt` degradation** (R-Δt-3) — performance must drop when `dt` is shuffled, proving the model *uses* timing.

---

# Part 8 — Implementation challenges & complex / large-scale integrations

The genuinely hard, cross-cutting items (in rough difficulty order):

1. **Lifting the worker `ndim>2` cap (OQ-11, WS-8).** The single heaviest integration: a 3-D `(B,T,F)` payload + `seq_lengths` + `readout_mask`, an immutable-time / shardable-batch ordering contract, and the recurrent forward + gradient deployed worker-side. **Deliberately deferred** — fixed-order LMU trains in-process so this is off the first-release path, but it gates distributed recurrent training.
2. **The homogeneous-pool growability gap (Step 2).** No mechanism to grow a heterogeneous candidate pool with state-carrying memory blocks, nor a correlation-compatible recipe to train one as a candidate. Open research; avoided by fixed-order Step 1.
3. **The model↔service refactor (WS-2/WS-3/WS-6).** Extracting `juniper-service-core` (T1 infra) + defining `juniper-model-core` (interfaces + conformance kit), then *eventually* repointing production cascor onto them — trigger-conditioned, with a kill-criterion (if cascor can't go green on the conformance suite without behavior change, WS-6 is abandoned and one-sided extraction is documented). Recurrence is built greenfield against these abstractions to **prove the template before cascor is touched**.
4. **Canopy generalization (WS-5).** Moving a classification-shaped UI (accuracy, decision boundaries, cascade columns) to a schema-driven, model-agnostic one (regression metrics, time-series plots, topology from `describe_topology()`), conditionally rendering cascor-only panels.
5. **The docker/on-host dependency asymmetry (§6.8).** Publish-first + same-PR pin-and-lock are mandatory; the build-green/runtime-red gap is the classic trap. New shared packages need a TestPyPI soak before any docker lock pins them.
6. **The rename ripple (`recurse` → `recurrence`).** Cheap now (nothing published), but touches repo names, env prefixes, client/worker/core package names, conda env, and compose/plant_all wiring. Lock it before first publish (§9.1).

---

# Part 9 — Next steps

## 9.1 Current work (in order)

- **(a) ✅ DONE 2026-06-14 — fixed-Δt negative control added.** `verify_delta_t_reference_code.py` now has a `FixedStepLMUMemory` (bakes `Ā`, `B̄` once at the mean Δt and applies them uniformly, ignoring per-step gaps). **Measured:** the variable-step passes `e_irr < 3·e_reg + 0.02` on every (d,ρ); the fixed-Δt control reconstructs *identically* on the regular grid (its mean **is** the gap) but its irregular-grid error runs **~2.5× (1.9–3.8×) the variable-step's** — the per-step Δt adaptation is now a *measurement*, not an analytic claim. **Refinement found by the measurement:** the lenient `3·e_reg + 0.02` gate only trips in the worst-conditioned case (1/6), so the degradation **ratio**, not the gate, is the load-bearing signal. (A bursty large-gap grid was tried and rejected: it raised *both* errors and masked the separation — small gaps `<< θ` are the sharp discriminator.) *(ad-hoc POC, `util/ad-hoc/`.)*
- **(b) Reconcile the LMU grown-vs-fixed contradiction in the model doc — ship fixed-order first.** Record explicitly that the LMU is a fixed-order `TrainableModel` (implements `TrainableModel`, **not** `GrowableModel`); the grown-cascade-block form is research (§4.2). Update the model doc's §1.3.3/§1.5 wording in place.
- **(c) Wire the already-shipped 3-D sequence data contract into the consumer.** WS-1 (3-D NPZ + Δt + temporal split) and the `equities_seq` generator are shipped, and `juniper-data-client` already dispatches on `X.ndim`; **the recurrent path is unreachable until cascor/the new model can ingest 3-D windows *and read `dt`*.** This item is now scoped in detail by `…CASCOR_3D_INGESTION_GATE_2026-06-14.md`, which is decision-critical: there are **two paths**, and they are not equal.
  - **Path A — FLATTEN `(B,L,F)→(B,L·F)`** is cheap (one reshape, no core change) but *is* the P4 lag-embedding — FIR, inherits the star-free ceiling, and **discards `dt`**. It is "a trap dressed as a quick win"; use it only as an explicitly-labeled plumbing smoke-test, never as the deliverable.
  - **Path B — a recurrent forward over the lookback axis that consumes `dt`** is the genuine work and the only path that realizes the P3-C/LMU Δt win. Build it as the fixed-order LMU block fronting the 2-D cascade head (§4.1). Sequence the plumbing prerequisites *with* the model: (i) cascor ingestion calls `validate_npz_contract` and carries `dt`/`target_dt` (§6.1 consumer gap); (ii) a shape-tuple input contract; (iii) the in-process descriptor extension (§4.3 Tier 1) *only if* the block trains via the in-process pool. **Do not ship Path A as the answer.**

## 9.2 Future work (gated)

- **Ceiling-breaking is gated behind one concrete trigger:** *the addition of a temporal dataset with a **verified non-star-free (parity / mod-n / group) target**.* Until then, do not build it (the dataset-audit exception list is empty).
- **If the trigger fires, the route is a negative-eigenvalue input-dependent linear-RNN block** (Grazzi et al. ICLR 2025) grown as a cascor candidate — the **P7** design. It is the only charted breaker that is both *general* and *trainable*; the open problem is a *correlation-compatible growth recipe* for the non-diagonal (general-counting) case (the diagonal/parity case is POC-verified: held-out parity 0.982, and the correlation objective drives the eigenvalue to −1.00). Prefer P7's most-viable sub-path: GD-train each candidate block internally (Adam + BPTT), keep cascor's correlation-based *selection* + freeze-on-tenure.
- **Fund P2 (group-implementing units) training-recipe research** as a preferred parallel research path; **keep P6 (NARX-MLP output enrichment) as a representability reference, not a deployed target** — it is empirically rejected (output enrichment cannot bootstrap state through cascor's output-state-blind drive).
- **Avoid the output-enrichment path entirely (P5/P6).** The obstruction is the state substrate, not the readout.
- **RTRL** as an alternative candidate gradient if the window cap is lifted or online/streaming modes are added (§5.2).
- **P1 (self-recurrent RCC candidate)** for cheap *hidden* recurrence inside the framework, complementary to the fixed-order LMU.

---

# Part 10 — Consolidated open questions

| ID | Question | Status |
|---|---|---|
| OQ-1 | "recursive" = recurrent (temporal)? | **Resolved:** recurrent |
| OQ-2 | R5 (capability) vs C1 (first-principles)? | **Resolved:** both bind; complementary |
| OQ-3 | Framework hosting unit types vs single model? | **Resolved:** framework, RCC/LMU sequenced |
| OQ-4 | Ship despite star-free ceiling? | **Resolved:** ceiling not binding; cheap path near-term, P7 long-term |
| OQ-5 | First datasets? | **Resolved:** spiral, XOR, MNIST, equities; time-series multi-sine / Mackey-Glass / AR(p) |
| OQ-6 | NPZ 3-D keys in WS-1? | **Resolved + shipped** (additive; `dt`/`t`/`target_dt`/`seq_lengths`/`readout_mask`/`scaling`/`task_type`) |
| OQ-7 | When is irregular-Δt relevant? | **Resolved: GATING** — required for completed state (drives the P3-C pick) |
| OQ-8 | Migrate CLI problems into juniper-data? | Lean yes (C3) |
| OQ-11 | Recurrent training parallelizable via worker protocol? | **Open** — the `ndim>2` cap; deferred (WS-8) |
| OQ-15/18 | Service port? | host **8211** → ctr **8210** |
| OQ-16 | Recurrence env strategy? | Dedicated `JuniperRecurrence` if CPU-torch (copy LIBTORCH hook); else reuse `JuniperCascor1` |
| **OQ-19 (new)** | Lock the `recurse → recurrence` rename before first publish? | **RATIFIED yes (2026-06-14)** — cost-free now; ripple per §0.2 |
| **OQ-20 (new)** | Fixed-order LMU as the first deliverable, grown-LMU as research? | **RATIFIED yes (2026-06-14)** (§4.1/§4.2) |

---

# Part 11 — References (web-verified in the prior validation passes)

**LMU / state-space / continuous-time:**

- Voelker, Kajić & Eliasmith 2019 — *Legendre Memory Units: Continuous-Time Representation in Recurrent Neural Networks*, NeurIPS. *(the model; PDF on disk in `papers/`)*
- Gu, Dao, Ermon, Rudra & Ré 2020 — *HiPPO: Recurrent Memory with Optimal Polynomial Projections*, NeurIPS; arXiv:2008.07669. *(re-derives the LMU; LMU→S4 bridge)*
- Gu, Goel & Ré 2022 — *S4*, ICLR; arXiv:2111.00396. Smith, Warrington & Linderman 2023 — *S5*, ICLR; arXiv:2208.04933. Gu & Dao 2023 — *Mamba*, arXiv:2312.00752. *(SSM family; baseline/future)*
- Sarrof, Veitsman & Hahn 2024 — *The Expressive Capacity of State-Space Models*, NeurIPS; arXiv:2405.17394. *(nonnegative SSM = star-free; no parity)*
- Merrill, Petty & Sabharwal 2024 — *The Illusion of State in State-Space Models*, ICML; arXiv:2404.08819. *(all SSMs ∈ TC⁰)*

**Cascade-Correlation & the ceiling:**

- Fahlman & Lebiere 1990 — *The Cascade-Correlation Learning Architecture*, NIPS-2. Fahlman 1991 — *The Recurrent Cascade-Correlation Architecture*, NIPS-3.
- Giles, Chen, Sun, Chen, Lee & Goudreau 1995 — IEEE TNN 6(4):829–836. Kremer 1996 — IEEE TNN 7(4):1047–1051. *(RCC = star-free)*
- Knorozova & Ronca 2024 — *On the Expressivity of Recurrent Neural Cascades*, AAAI; arXiv:2312.09048. *(exact star-free characterization; group-unit remedy)*
- Grazzi, Siems, Zela, Franke, Hutter & Pontil 2025 — *Unlocking State-Tracking in Linear RNNs through Negative Eigenvalues*, ICLR (Oral); arXiv:2411.12537. *(the P7 ceiling-breaker)*

**Reservoir / irregular-Δt / training:**

- Jaeger 2001 (ESN); Lukoševičius & Jaeger 2009 (reservoir survey); Yildiz, Jaeger & Kiebel 2012 (ESP ρ<1 not sufficient); Qiao et al. 2017 (Growing ESN); Grigoryeva & Ortega 2018 (ESN universal for the *fading-memory* class).
- Williams & Zipser 1989 (RTRL); Williams & Peng 1990 (truncated BPTT).
- Chen et al. 2018 (Neural ODE); Rubanova, Chen & Duvenaud 2019 (Latent ODE — irregular-Δt, solver-based, deferred); Hasani et al. 2021 (LTC), 2022 (CfC).
- Lipton, Berkowitz & Elkan 2015 (RNN definition, §0.2 terminology).

*(Full landscape citations — LSTM/GRU/TCN/NEAT/forecasting standing — are in the model doc §6.2.)*

---

# Appendix A — Reference source code

Verified numpy reference (`util/ad-hoc/verify_delta_t_reference_code.py`, numpy 2.4.4 / Python 3.13). Proposed shipping homes are noted per block. **Reference — not yet shipped.**

## A.1 The Δt-native LMU memory unit → `juniper_recurrence/units/lmu_varstep.py`

```python
from __future__ import annotations
import numpy as np
from numpy.polynomial.legendre import Legendre

def lmu_matrices(d: int):
    """Fixed, closed-form Legendre (HiPPO-LegT) state matrices A (d×d), B (d×1).
    C1: depend only on order d; not learned, not data-dependent."""
    A = np.zeros((d, d)); B = np.zeros((d, 1))
    for i in range(d):
        B[i, 0] = (2 * i + 1) * ((-1) ** i)
        for j in range(d):
            A[i, j] = (2 * i + 1) * (-1.0 if i < j else (-1.0) ** (i - j + 1))
    return A, B

class VariableStepLMUMemory:
    """Irregular-Δt-native LMU memory (Approach C).
    C1: no ODE solver, no autodiff-through-solver — only scalar exponentials of the
    eigenvalues of a FIXED, closed-form matrix. Fully inspectable."""
    def __init__(self, d: int, theta: float):
        self.d, self.theta = d, float(theta)
        A, B = lmu_matrices(d)
        lam, V = np.linalg.eig(A)
        self.lam, self.V = lam, V
        self.Vinv = np.linalg.inv(V)
        self.VinvB = self.Vinv @ B

    def step_matrices(self, dt: float):
        """Ā(Δt), B̄(Δt) for a single real gap dt, via eigendecomposition."""
        z = self.lam * (dt / self.theta)
        Abar = (self.V * np.exp(z)) @ self.Vinv
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = np.expm1(z) / self.lam
        fac = np.where(np.abs(self.lam) < 1e-12, dt / self.theta, fac)   # removable singularity
        Bbar = (self.V * fac) @ self.VinvB
        return Abar.real, Bbar.real

    def rollout(self, u: np.ndarray, dt: np.ndarray):
        """ZOH rollout: u[k-1] held across (t[k-1], t[k]] of length dt[k]. out[0]=0 (empty window)."""
        m = np.zeros((self.d, 1)); out = np.zeros((len(u), self.d))
        for k in range(1, len(u)):
            if dt[k] <= 0:
                raise ValueError(f"dt[{k}]={dt[k]} must be > 0 for k>=1")
            Abar, Bbar = self.step_matrices(float(dt[k]))
            m = Abar @ m + Bbar * u[k - 1]
            out[k] = m[:, 0]
        return out

    def decode_weights(self, rho: float):
        """Read the memory at delay rho*theta into the past (shifted-Legendre evaluation)."""
        x = 2.0 * rho - 1.0
        return np.array([Legendre.basis(i)(x) for i in range(self.d)])
```

**Torch port note.** Precompute `Ā`,`B̄` as constant tensors (or a per-`dt`-bucket dict); roll the memory with no grad through `A`/`B`; the only trained `nn.Parameter`s are the read-in (features→`u`) and readout (memory→output). Mirrors this reference 1:1.

## A.2 Sequence windowing (leakage-safe) → `juniper_data/generators/_sequence.py`

```python
import datetime as _dt
import numpy as np

def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64, count=len(dates))

def window_one_ticker(feats, dates_yyyymmdd, y_dir, y_reg, ticker_code, *,
                      lookback, cut_ordinal, embargo=False):
    """Slide a lookback window over ONE ticker's time-ordered rows; split by TARGET time.
    Enforces leakage invariants I1–I5 (see §6.2). dt[:,0]=0; dt[:,k]=calendar-day gap."""
    n, f = feats.shape
    ords = _yyyymmdd_to_ordinal(dates_yyyymmdd)
    assert np.all(np.diff(ords) > 0)                    # monotone time within ticker
    cols = {k: {"train": [], "test": []} for k in
            ("X", "y", "y_reg", "date", "dt", "target_dt", "window_end_date", "ticker_code")}
    for i in range(lookback - 1, n - 1):
        lo = i - lookback + 1
        target_time = int(ords[i + 1])
        split = "train" if target_time < cut_ordinal else "test"      # split by TARGET time (I2)
        if split == "test" and embargo and int(ords[lo]) < cut_ordinal:
            continue                                                  # embargo (I4)
        win_ords = ords[lo:i + 1].astype(np.float32)
        dt = np.empty(lookback, dtype=np.float32)
        dt[0] = 0.0
        dt[1:] = np.diff(win_ords)                                    # real elapsed gaps (I3)
        cols["X"][split].append(feats[lo:i + 1])
        cols["y"][split].append(y_dir[i]); cols["y_reg"][split].append(y_reg[i])
        cols["date"][split].append(dates_yyyymmdd[lo:i + 1])
        cols["dt"][split].append(dt)
        cols["target_dt"][split].append(np.float32(ords[i + 1] - ords[i]))   # horizon (I5)
        cols["window_end_date"][split].append(dates_yyyymmdd[i])
        cols["ticker_code"][split].append(np.int32(ticker_code))             # one ticker (I1)
    # ... (stacking into zero-padded arrays omitted; see the verified reference file) ...
    return cols
```

## A.3 Grid-invariance conformance test → `juniper_recurrence/tests/test_lmu_grid_invariance.py`

```python
import numpy as np
from juniper_recurrence.units.lmu_varstep import VariableStepLMUMemory

def _err_on(mem, times, theta, omega, rho, w):
    times = np.asarray(times, float)
    dt = np.empty_like(times); dt[0] = 0.0; dt[1:] = np.diff(times)
    u = np.sin(omega * times)
    recon = mem.rollout(u, dt) @ w
    warm = times >= (times[0] + theta)                  # score only after one window fills
    truth = np.sin(omega * (times - rho * theta))
    return float(np.sqrt(np.mean((recon[warm] - truth[warm]) ** 2)))

def test_lmu_grid_invariance():
    d, theta, omega, rho = 16, 1.0, 2.0, 1.0
    mem = VariableStepLMUMemory(d, theta); w = mem.decode_weights(rho)
    assert float(np.max(np.linalg.eigvals(mem.V @ np.diag(mem.lam) @ mem.Vinv).real)) < 0  # stable
    t_reg = np.linspace(0, 12, 240)
    gaps = np.r_[0.02, np.random.default_rng(0).uniform(0.02, 0.08, 239)]
    t_irr = np.cumsum(gaps)
    e_reg = _err_on(mem, t_reg, theta, omega, rho, w)
    e_irr = _err_on(mem, t_irr, theta, omega, rho, w)
    assert e_reg < 0.05                       # the method works at all
    assert e_irr < 3.0 * e_reg + 0.02         # irregular grid does not degrade it
    # TODO (current-work item a): add a FixedStepLMUMemory negative control asserting it FAILS this bound.
```

---

# Appendix B — Cross-references & provenance

- **Decision map:** `JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md`
- **Architecture re-eval (P6 / P2-P3-hybrid / P3-C-pairings / LMU-SSM; REPRESENTABILITY/LEARNABILITY/DEPLOYED axes):** `JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-ARCHITECTURE-REEVALUATION.md`
- **Dataset audit (requirement validator):** `JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-DATASET-AUDIT.md`
- **Cascor 3-D ingestion gate (build-side scoping of item c; two-IPC-path + three-tier analysis):** `JUNIPER_2026-06-14_JUNIPER-RECURRENCE_RECURSE-OQ4-CASCOR-3D-INGESTION-GATE.md`
- **P5 recurrent-output eval:** `JUNIPER_2026-06-10_JUNIPER-RECURRENCE_RECURSE-OQ4-P5-RECURRENT-OUTPUT-LAYER-EVAL.md`
- **Δt math & reference code:** `JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md`; POC `util/ad-hoc/verify_delta_t_reference_code.py`
- **Model landscape & §1.3.4 Δt-native LMU:** `JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md`
- **Substrate & shared packages, WS/OQ/RK registers:** `JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`
- **P1/P2/P3 proposals + Workstream-0:** `JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md`
- **Alternatives (P4–P7):** `JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-DELAY-LINE-NODE-DESIGN-EVAL.md`, `JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-OQ4-DELAY-LINE-OUTPUT-MODULE-EVAL.md`, `JUNIPER_2026-06-13_JUNIPER-RECURRENCE_RECURSE-OQ4-P7-GRAZZI-BLOCK-DESIGN.md`
- **Placement & naming:** `JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md`, `JUNIPER_2026-06-05_JUNIPER-ECOSYSTEM_CODE-ORGANIZATION-STRATEGY.md`
- **POCs:** `util/ad-hoc/verify_{delta_t_reference_code,oq4_expressivity_suite,delay_line_node_eval,fir_horizon_boundary,p5_recurrent_output_eval,p6_narx_mlp_output_eval,p7_grazzi_block_growth}.py`

---

*Draft 1.0.0. Consolidated detailed design for the selected juniper-recurrence model — P3-C (LMU + Approach-C), the Δt-native continuous-time memory. Synthesizes the full prior corpus (literature review, P1–P7/ESN/NEAT/LMU-SSM architecture evaluation, POC verification, OQ-4 reevaluation, dataset audit, Δt-handling analysis) and augments it with theory, reference source code, the Juniper integration plan, and a model-specific risk/guardrail register. WS-0 ratified 2026-06-14; workstream PRs (WS-1…WS-4) may now open, each as its own reviewed PR.*
