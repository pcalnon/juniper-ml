# Recurrent Cascade-Correlation — OQ-4 Architecture Re-Evaluation: P6, Pairings & LMU/SSM

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 architecture re-evaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-12

---

> **Epistemic legend.** `VERIFIED-PRIMARY` = quoted from a PDF/source opened this session. `VERIFIED-SECONDARY` = corroborated across ≥2 independent sources where the primary text was not machine-extractable. `VERIFIED-CODE` = checked against a live cascor `file:line` re-read this session. `INFERRED` = a deduction (lower confidence; flagged). Every **novel-design** verdict (P4/P5/P6/P3-C/P2P3-hybrid) is an INFERENCE against VERIFIED theorems + code — these designs are unpublished. The three axes — **REPRESENTABILITY** (can express, unbounded state) vs **LEARNABILITY** (BPTT can find) vs **DEPLOYED** bound (D≤window≤30, stateless-per-window) — are kept strictly separate; conflating them is the failure mode this work guards against.

> **Provenance & a caveat on this document.** Produced 2026-06-12 by a maximal adversarial multi-agent workflow (188 sub-agents across two runs, ~27 M tokens, ~5,600 tool calls): a 4-agent reality-brief → 17 strand lenses across P6 / P2P3-hybrid / P3-C+pairings / LMU-SSM → 3-vote perspective-diverse refutation → two 6-angle **ceiling sub-panels** (P6, P2/P3-hybrid) reading Knorozova-Ronca / Siegelmann-Horne-Giles / the SSM-expressivity literature directly → comparison → synthesis. **33 of 52 findings survived refutation; the two ceiling sub-panel syntheses completed and are the spine of §3–§4.** A server-side rate-limit storm followed by a session usage limit blocked the *final agent-synthesis pass and the two automated critics*; **this document was therefore assembled by the lead from the verified comparison matrix + ceiling-panel outputs, with the epistemic discipline applied by hand rather than by the automated completeness/hallucination critics.** Treat citation line-numbers and the two newest sources (Sarrof-Veitsman-Hahn 2024; Khavari 2025) as agent-verified-not-yet-lead-reverified. The **dataset audit** (the requirement validator, §9) is a deferred follow-up.

---

## 1. Executive Summary

This round evaluated four new architecture strands against the P1–P5 baseline, with the star-free ceiling as the marquee question. **Two findings dominate.**

**(A) The ceiling question is now resolved — and points away from itself.** P6 is the *only* strand that genuinely clears the ceiling, and even it does so only in an idealization:

- **P6 (NARX-MLP output) BREAKS THE CEILING FULLY on REPRESENTABILITY.** Routing the fed-back outputs *through* a hidden MLP that also ingests the FIR features is the **literal Siegelmann-Horne-Giles 1997 NARX construction** — proven Turing/FSM-universal, the strongest break in the set, and the *exact enabling hypothesis P5 lacked* (P5's feedback was siloed, single-nonlinearity, and bypassed the hidden layer). **But it does not survive deployment**: the D≤30 stateless-per-window reset re-imposes a finite-memory machine (FMM ⊊ FSM, by SHG's own hard-limiter converse), and BPTT-through-MLP+recurrence does not reliably *learn* counting (Lin-Horne-Tiňo-Giles 1996: NARX buys only a 2–3× constant on the *same* vanishing-gradient decay). So P6's real deployed gain over P5 is modest, purchased at the highest C1/trainability cost and by shattering cascor's two-tensor output-state contract.
- **The P2/P3 hybrid BREAKS PARTIALLY to the C2 / mod-2 cyclic group** — carried *entirely* by the P2 arm (the LMU arm contributes zero break). Full-regular is **not** achieved (it is K&R's *conjecture*, not a result). And it is **un-learnable today** (the P2 recipe-gap is fully inherited). It is the highest-risk option and internally cannibalizes.

**(B) The break is almost certainly not required.** Equities/forecasting is real-valued regression, not a mod-k counting task; SSMs (LMU/S4/Mamba) sit at the *same* star-free ceiling by theorem (Sarrof-Veitsman-Hahn 2024) yet are the field's strongest sequence models. **The load-bearing deliverable is the irregular-Δt front, not the ceiling break.**

**Bottom line:** Run the **dataset audit** to confirm no counting requirement (expected). If confirmed, ship **P3-C/LMU via Approach-C** (the only *measured* irregular-Δt win, C1-clean, longest horizon) as a standalone fixed-order Δt-native model; keep **P1** as the cheap genuine-hidden-recurrence increment. Only if counting *is* required, fund the **P2 group-unit training-recipe research** before any integration, and treat **P6 as a representability reference, not a deployment target**.

---

## 2. Method & Provenance

See the provenance blockquote above. Lens strands: **P6** (richer NARX output — a small hidden MLP between the FIR features and the recurrent output), **P2/P3 hybrid** (heterogeneous group-unit + LMU pool), **P3-C + pairings** (LMU + Approach-C; screened combinations), **LMU/SSM** (the continuous-time family + the SSM frontier). Two ceiling sub-panels (P6, P2/P3) ran 6 formal-language angles each, reconciled by a synthesis agent and 3-vote refuted. Anti-hallucination rules required every theorem to be quoted from an opened source and every code claim cited to a live `file:line`; the representability / learnability / deployed separation was mandatory throughout.

---

## 3. P6 — Richer NARX Output (the marquee)

**Design.** P5's FIR hidden cascade, but the recurrent readout is a **small hidden MLP**: `y(t) = Ψ( FIR_features(t), y(t−1..t−D) )`, where the fed-back outputs **re-enter the hidden layer Ψ and mix with the exogenous features across hidden units**.

### 3.1 Representability — FULL break (VERIFIED-PRIMARY + INFERRED)

P6 *is* the literal Siegelmann-Horne-Giles 1997 NARX form `y(t)=Ψ(u-taps, y-taps)` with Ψ an MLP, which SHG "constructively prove … computationally as strong as fully connected recurrent networks and thus **Turing machines**" (PubMed 18255858, abstract, opened this session). Turing-universality strictly dominates the full-regular/FSM class, so **P6 clears the entire star-free ceiling** — the strongest break in the strand set. The lift comes from **feedback × hidden-unit mixing** (the MLP Ψ), which is exactly the K&R cascade-vs-network distinction (VERIFIED-PRIMARY, local PDF: a network/MLP component "has access to the state of all components" vs a cascade's "preceding components" only). This is the precise enabling hypothesis **P5 lacked** (siloed single-nonlinearity ⇒ NOT NARX-universal, only bounded mod-k).

### 3.2 Deployed — RE-CAPPED to finite memory (VERIFIED-SECONDARY)

A recurrence that resets every ≤30 steps unrolls the IIR to ≤30 lags = a finite-window FIR-of-outputs = **a finite-memory machine**. This is exactly SHG's own hard-limiter converse (NARX with hard-limiting nonlinearities collapse to **FMM ⊊ FSM**; paper body, not in the scrambled PDF/abstract). So the headline Turing/FSM-universality is an **unbounded-state / offline idealization**; under the ratified window, **mod-k for k>30 is architecturally impossible** with no state crossing the window boundary. The deployed bound is identical to P5's; cross-output coupling (shared vs per-output MLP) is moot here.

### 3.3 Learnability — strictly below representability (INFERRED)

BPTT through MLP+recurrence at the marginal-stability poles (|λ|≈1) a counter needs is the classic vanishing/exploding-gradient knife-edge, with no MSE pressure toward a cycle. The most P6-favorable result (**Lin-Horne-Tiňo-Giles 1996**) caps the NARX benefit at a **2–3× constant on the SAME vanishing-gradient decay** and provably does *not* circumvent it; even Dyck-1 counting is empirically unlearnable-to-extrapolation. Consistent with the empirically-grounded P5 learnability finding.

### 3.4 Cost — highest in the set (VERIFIED-CODE)

- **C1 transparency: LOWEST** — the MLP readout is the least transparent piece evaluated. Not a *violation* (a hand-rolled small MLP is inspectable) but the C1 cost of NARX.
- **Cascade-correlation identity: weakest of any strand** — the universality-bearing piece is a grafted NARX-MLP readout, orthogonal to the grow→correlate→freeze machinery.
- **Output-state contract: shattered** — pickle (`:3012-3041`), HDF5 (`:4914-4933`), grow (`:921-946`), resize (`:4051-4086`) all assume exactly `output_weights + output_bias`; the CR-060 hoist (`:2047-2051`) is invalidated for the AR term; the epoch call (`:2067`) becomes a windowed BPTT unroll.

**Ceiling ranking (representability):** P4 (no break) < P1 (mod-2 only) < P5 (bounded mod-k, not full-regular, not NARX-universal) < P2 (full-regular via group units, **no recipe**) ≤ **P6 (Turing/FSM-universal via NARX-MLP, AND has a constructive trainer: BPTT)**. P6 is the only strand that is *both* genuinely ceiling-breaking *and* equipped with a trainer — but the trainer cannot reliably reach counting, and the window re-caps it regardless.

---

## 4. P2/P3 Hybrid — group units + LMU in one pool

**Design.** A *heterogeneous* candidate pool with both P2 group-implementing units (2nd-order multiplicative, for the ceiling) and P3 LMU cells (for Δt/horizon); grow by best-correlating candidate from the mixed pool.

### 4.1 Ceiling — `breaks_partially`, to C2 only (VERIFIED-PRIMARY)

The break is to the **cyclic group C2 (= Z2 = mod-2/parity)**, **PROVEN** (K&R Prop 5/6: second-order multiplicative neurons are core C2-neurons; Thm 7: a single negative-weight sign/tanh neuron escapes group-free via the toggle/period-2 semiautomaton). **Full-regular is NOT proven** — C2 is explicitly "a first step" toward "finite simple groups," and K&R *conjectures* (does not prove) that sign/tanh neurons cannot capture an arbitrary grouplike semiautomaton. The break is sourced **entirely from the P2 arm**; the P3/LMU arm inherits star-free (Sarrof-Veitsman-Hahn 2024 Cor 14) and buys Δt/horizon orthogonally.

### 4.2 Learnability — blocked (VERIFIED-CODE)

The central OQ-4 gap, fully inherited: K&R is representability-only (hand-specified weight partitions, zero training); cascor's order-invariant scalar Pearson objective (`candidate_unit.py:935-941`) is **group-structure-blind**, and the additive forward (`:479`) is the wrong parameterization vs K&R's required *product* form. Heterogeneity buys only deployment-**gating** leverage (argmax can decline a useless unit), **not** a training recipe.

### 4.3 Deployed — asymmetric

Too shallow to cap the C2/mod-2 break (depth-1 state survives the window), but it **truncates the LMU's ~10⁵-step horizon to ≤30**, and a 3-D window hits the `ndim>2` worker wall (`cascade_correlation.py:272-273`).

### 4.4 Composition (VERIFIED-PRIMARY + VERIFIED-CODE)

The cascade *mechanically* supports mixed frozen units (lower-triangular read `:1944-1946`; untyped install dict `:4032-4037`), and **K&R's mixed-cascade theorem (Lemma 7** — corrected from a three-angle mislabel "Lemma 2") makes a *single* group neuron suffice to lift the class. But group-break and fading-memory **co-exist side-by-side, not fused** into a Δt-aware counter, and the 2-state C2 unit needs a multi-column buffer the one-column-per-unit schema lacks. **The hybrid internally cannibalizes**: its ceiling arm can't be grown (no recipe) or even evaluated (homogeneous stateless-scalar substrate); its horizon arm is window-truncated. **Its only clean win — LMU Approach-C grid-invariance — is delivered by P3-C alone, without the P2 baggage.** Highest risk in the set.

---

## 5. P3-C + Pairings

**P3-C (LMU + Approach-C) — the standout sub-result.** A closed-form variable-Δt LMU discretization that is **C1-CLEAN** (matrix-exp of a *fixed* Legendre matrix — A, B not learned, not data-dependent; no ODE solver, no autodiff-through-solver; "transparent ≠ trivial", VERIFIED §8.4) and delivers the **only MEASURED irregular-Δt robustness in the corpus** (grid-invariance `e_reg≈0.035`, `e_irr≈0.039–0.043`, ~1.15×; re-reproduced this session). It **inherits** the ceiling — which is fine, because forecasting is not a counting task. Δt-handling **best in class** (the `dt` channel *is* the discretization step). Genuinely recurrent, longest controllable horizon (window θ), most transparent recurrent option.

- **Honest gaps:** the POC has **no fixed-Δt negative control**, so "fixed-Δt fails the e_irr bound" is an analytic *assertion*, not yet a measurement. The **grown story is the open question** (model-doc self-contradiction, §6) — ship the **fixed-order** framing first.

**Other pairings (screened):** the genuinely-additive combinations are limited. Most "combos" (P4-FIR-taps → LMU read-in; P1 self-loop on a reservoir; P3-features → P5/P6 recurrent readout) either duplicate a capability P3-C already provides or stack two un-recipe'd parts. **No screened pairing dominates P3-C** on the {genuine recurrence, Δt, horizon, C1, cost} bundle; the hybrid (§4) is the one explicitly evaluated and it loses to P3-C-alone.

---

## 6. LMU / SSM Deep-Dive

**Ceiling placement — INHERITS, by theorem.** SSMs (LMU, S4, Mamba) sit at the **same star-free ceiling** (Sarrof-Veitsman-Hahn 2024, Thm 4 / Cor 14, VERIFIED-SECONDARY). **Mamba's selectivity does NOT help** — breaking requires **both** input-dependence **and** negative eigenvalues (Khavari 2025), and the fading-memory options have neither. Fading memory ≠ counting (the corpus "category error" correction, re-confirmed).

**Horizon — longest native.** LMU handles dependencies spanning ~10⁵ steps with ~105 state variables and **no training of the memory** (VERIFIED LMU abstract + Fig. 3); the knob is the window θ. **But truncated to ≤30 under the stateless-per-window contract** — the very property that motivates LMU is window-clipped unless the contract widens.

**Growability — NOT a growable unit.** Fixed-order whole-model; best fit is **hosting one fixed LMU cell behind the common interface, not as a tenured cascade unit**. This exposed a **model-doc self-contradiction**: §1.3.3 ("growth = increase order d") vs §1.3.4 ("LMU is a fixed-order model OUTSIDE the growth loop", marked SPECULATIVE). Recommendation: ship the fixed-order framing; treat "grow by order d" as separate later research.

**C1 — highest among genuinely-recurrent options.** The recurrent core is a known orthogonal-polynomial (Legendre/HiPPO) projection; only encoders/readout are learned.

**Net:** LMU is the cascor-compatible sweet spot of the SSM family and the bridge to the modern SSM frontier — strongest genuine-recurrence + horizon + Δt foundation, and the ceiling-break is orthogonal and **not needed** for forecasting.

---

## 7. Operational Deltas vs P1–P5 (Q1–Q4)

- **Q1 Recurrence (where the state lives):** genuine *hidden* recurrence — P1, P2, P3, P3-C, P2P3, LMU/SSM. Recurrence at the *readout only* (never crosses the worker wire) — P5, P6. Not recurrence — P4.
- **Q2 Irregular-Δt:** **BEST = P3-C / LMU** (Approach-C, the only measured win). P1/P2 weak (Approach-A only); P4 worst (grid-dependent); P5/P6 poor (discrete-lag AR; Approach-C inapplicable to output feedback).
- **Q3 Horizon:** **longest native = LMU/SSM (~10⁵)**, P3-C long via θ — but **all truncated to ≤30 by the stateless window**. P1/P2 short; P4 ≤D; P5/P6 ≤window.
- **Q4 Mini-batch / training:** P1/P3-C/LMU mature (memory needs no training); P5/P6 require windowed BPTT at the readout (P6 invalidates the CR-060 hoist); P2/hybrid have **no recipe** for the break.

---

## 8. Updated OQ-4 Option Matrix (P1–P6 + P3-C + P2/P3 + LMU/SSM)

| Option                  | Recurrence            | Star-free ceiling                              | Irregular-Δt        | Horizon         | Growable / faithful      | C1          | Recipe                      | Overall risk |
|-------------------------|-----------------------|------------------------------------------------|---------------------|-----------------|--------------------------|-------------|-----------------------------|--------------|
| **P1** RCC self-loop    | hidden depth-1 IIR    | INHERITS (+mod-2 via −weight)                  | weak                | short           | **HIGH**                 | HIGH        | **MATURE**                  | **LOWEST**   |
| **P2** group units      | hidden IIR + group    | **BREAKS→full-regular** (conj.; only C2 built) | weak                | short           | shape-only               | hi-form     | **ABSENT**                  | HIGH         |
| **P3** reservoir/LMU    | hidden evolving state | INHERITS                                       | good (LMU)          | long (LMU)      | MEDIUM (unproven)        | MED         | partial                     | MEDIUM       |
| **P4** output FIR       | **none**              | INHERITS (weakest)                             | worst               | ≤D              | hi (attach)              | **HIGHEST** | trivial                     | low-value    |
| **P5** output AR        | readout IIR (siloed)  | partial mod-k (cond., ≤30)                     | poor                | ≤30             | LOW                      | HIGH        | BPTT-fragile                | MEDIUM       |
| **P6** NARX-MLP         | readout IIR via MLP Ψ | **FULL (repr.)** / FMM deployed                | poor                | ≤30 dep.        | **LOWEST**               | **LOWEST**  | BPTT (can't learn counting) | HIGH         |
| **P3-C** LMU+Approach-C | hidden LMU state      | INHERITS (n/a needed)                          | **BEST (measured)** | long→≤30        | MED (grown open)         | HIGH        | mature (Δt); growth open    | **MED-LOW**  |
| **P2/P3** hybrid        | both arms             | partial C2 (P2 arm only)                       | good (LMU arm)      | ≤30             | LOW                      | MIXED       | ABSENT (break)              | **HIGHEST**  |
| **LMU/SSM**             | d-dim linear state    | INHERITS (Mamba sel. no help)                  | **BEST**            | **longest→≤30** | not a unit (fixed-order) | **HIGHEST** | mature (fixed-order)        | LOW-MED      |

*(Full per-axis cell detail in the source comparison; terse here.)*:

---

## 9. The Requirement-First Decision Framing

The entire ceiling-break debate is downstream of one unanswered question: **does the target workload actually require mod-k / aperiodicity-breaking counting over arbitrary-length sequences?** The corpus position — which this synthesis concurs with on the evidence — is that **forecasting a real-valued series is NOT a mod-k task**, so the star-free ceiling is **very likely irrelevant to the near-term requirement**.

**The validator is the deferred DATASET AUDIT** (the queued follow-up): characterize each Juniper dataset (equities + the planned synthetics, and the static benchmarks) for whether its label is a regression/forecasting function of recent windowed history (**star-free-sufficient**) versus a genuine modulo/period/parity-counting function over arbitrary-length sequences (**ceiling-break-requiring**). Carefully separate the conflations — e.g., **XOR is a static 2-input logical op, not temporal parity-counting**; spiral/MNIST are static. If the audit confirms no counting requirement, the ceiling-break options (P2, P6, hybrid) are **de-prioritized as solving a problem the data does not pose**, and the decision collapses to *"which genuinely-recurrent, irregular-Δt-capable, C1-clean, cascor-faithful option is lowest risk?"* → **P3-C/LMU.**

---

## 10. Risks & Guardrails

| #  | Risk                                                                       | Guardrail                                                                                                                                                    |
|----|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| R1 | Conflating P6's **representational** full-break with a deployed capability | Always state the axis; the deployed P6 is finite-memory (≤30) and BPTT can't learn counting — keep §3.1/§3.2/§3.3 separate                                   |
| R2 | Treating the ceiling-break as a *requirement* before the audit             | Run the dataset audit first (§9); do not fund P2/P6 research until a real counting dataset is shown                                                          |
| R3 | Shipping LMU "grown-as-a-unit" on the unproven §1.3.3 framing              | Ship **fixed-order LMU** first; reconcile the §1.3.3↔§1.3.4 contradiction; treat growth as separate research                                                 |
| R4 | Asserting "fixed-Δt fails" without measuring it                            | Add a **fixed-Δt negative control** to `verify_delta_t_reference_code.py` so the grid-invariance claim is measured, not analytic                             |
| R5 | The recurrent path being unreachable                                       | **Wire the 3-D sequence contract into cascor** (`equities_seq` consumer / `X.ndim` dispatch); the `ndim>2` worker cap (`:272-273`) blocks 3-D payloads today |
| R6 | Funding the P2/hybrid ceiling-break without the recipe                     | The **group-unit training recipe is the gating research deliverable**, not an implementation task — do it *before* any integration                           |
| R7 | Adopting P6 and breaking the output-state contract                         | If P6 is ever built, it must extend pickle/HDF5/grow/resize off the two-tensor assumption — treat as a representability *reference*, not a near-term target  |

---

## 11. Flagged Uncertainties / Claims Not Load-Bearing

1. **P5/P6's break is gated by an UNSPECIFIED readout nonlinearity** — identity/linear readout ⇒ no break (today's readout is a bare linear GEMM, `:1979`). This single choice must be pinned before either claims a break.
2. **Network-level (stacked-unit) expressivity of P4/P5/P6 is NOT verified against an implementation** (none exists) — re-check at build time.
3. **The SHG-1997 verbatim FMM/Turing quotes** rest on prior-round transcription from a now-font-scrambled PDF; universality + FMM-converse are corroborated by independent web sources but the exact wording is agent-verified, not lead-re-read this session.
4. **Multi-output NARX coupling** (shared vs per-output MLP) is INFERRED — SHG prove SISO and assert the vector extension without analyzing coupling. (Per-output MLP already restores the hidden routing P5 lacked; shared-vs-per-output does not change the universality *class*.)
5. **P2's group-unit training recipe** is the central unresolved gap for the entire ceiling-break thesis.
6. **Sarrof-Veitsman-Hahn 2024 and Khavari 2025** are newly surfaced; carry as VERIFIED-SECONDARY pending lead re-read.
7. **This document was lead-assembled** (the automated synthesis + completeness/hallucination critics were blocked by a session usage limit) — it has not had an independent automated critic pass.

---

## 12. Recommendation

**Step 0 — resolve the prerequisite before picking a model.** Run the **dataset audit** (§9). The expected outcome (forecasting ≠ counting) de-prioritizes every ceiling-break option.

**Primary pick (conditional on the audit showing no counting requirement): P3-C / LMU via Approach-C** as the recurrent **foundation**, instantiated initially as a **standalone fixed-order model behind the common interface** (NOT yet a grown cascade unit). It is the only option with *measured* irregular-Δt robustness, is C1-clean, has the longest controllable horizon, and is the most transparent genuinely-recurrent option. Deploying it fixed-order **sidesteps the two unresolved blockers** (the homogeneous-pool growability gap and the worker `ndim>2` cap). Required follow-on, in order: **(a)** add the fixed-Δt negative control to the POC; **(b)** reconcile the LMU grown-vs-fixed model-doc contradiction (ship fixed-order first); **(c)** wire the already-shipped 3-D sequence data contract into cascor (`equities_seq` / `X.ndim` dispatch) — the recurrent path is unreachable until 3-D windows can be ingested.

**Lowest-risk increment (if a *hidden-pool* recurrent unit is wanted now, independent of Δt): P1 self-recurrent RCC.** Smallest blast radius (`candidate_unit.py:479` + window-unroll), mature recipe, reuses the install dict and worker payload; genuine depth-1 IIR and mod-2 via a learned negative weight, at minimal cost.

**If the audit DOES show a real counting requirement:** the only options that address it are **P2/hybrid** (C2/mod-2, **un-buildable** without first solving the group-unit training recipe — that recipe is the gating research deliverable) and **P6** (full-regular representationally, but deployed-demoted to finite-memory by the ≤30 window and BPTT-unreachable for counting). Fund a focused **research spike on the P2 second-order-multiplicative training recipe** before any integration; keep **P6 as a representability reference, not a deployment target**.

**De-prioritize:** **P4** (not recurrence; worst Δt — cheap feature-enrichment only), **P5** (conditional on an unspecified saturating readout, capped ≤30, mostly BPTT-unreachable — its robust gain is a fading decay tail P3-C delivers more cleanly), and the **P2/P3-hybrid** (highest risk; cannibalizes; its only clean win is delivered by P3-C alone).

**One-line decision rule:** *Audit the data first; if no mod-k counting is required (expected), ship P3-C/LMU as a fixed-order Δt-native model (optionally P1 for a cheap genuine hidden-recurrence increment); only if counting IS required, fund the P2 group-unit training-recipe research before touching integration, and keep P6 as a representability reference rather than a deployed target.*

---

## 13. References (verified)

**Primary (PDFs opened):**

- Knorozova, N. A., & Ronca, A. (2024). *On The Expressivity of Recurrent Neural Cascades.* AAAI; arXiv:2312.09048v2. — group-free = star-free (p.4); Thm 4/5 (positive-weight ceiling), Thm 7 (negative-weight C2 escape), Prop 5/6 (second-order ⊕=product = cyclic group C2), Lemma 7 (mixed-cascade: one group neuron lifts the class); full-regular is conjecture.
- Voelker, A., Kajić, I., & Eliasmith, C. (2019). *Legendre Memory Units.* NeurIPS. — Legendre/HiPPO memory; ~10⁵-step dependencies; A,B fixed (no training).

**Web-verified (secondary):**

- Siegelmann, H. T., Horne, B. G., & Giles, C. L. (1997). *Computational Capabilities of Recurrent NARX Neural Networks.* IEEE Trans. SMC-B 27(2):208-215; PubMed 18255858. — NARX (output feedback through MLP Ψ) is Turing-universal; hard-limiter converse → Finite-Memory-Machines (FMM ⊊ FSM).
- Giles, C. L., et al. (1995). *Limitations of Recurrent Cascade Correlation.* IEEE TNN 6(4):829-836. — RCC period-2 cap under constant input; remedy = full recurrence (distinct from K&R's second-order remedy).
- Kremer, S. C. (1996). IEEE TNN 7(4):1047-1051. — a second unrepresentable automata class.
- Lin, T., Horne, B. G., Tiňo, P., & Giles, C. L. (1996). *Learning long-term dependencies in NARX networks.* IEEE TNN 7(6):1329-1338. — NARX buys only a 2–3× constant on the same vanishing-gradient decay; does not circumvent it.
- Sarrof, Veitsman & Hahn (2024). *On the expressivity of state-space / SSM models.* — SSMs are star-free (Thm 4 / Cor 14). *[lead re-read pending]*
- Khavari (2025). — breaking star-free needs both input-dependence and negative eigenvalues; Mamba selectivity alone does not. *[lead re-read pending]*
- McNaughton, R., & Papert, S. (1971). *Counter-Free Automata*; Schützenberger (1965). — star-free = aperiodic = counter-free = group-free; threshold-countable, not mod-countable.

**Live code (juniper-cascor `src/`, re-read this session):**

- `cascade_correlation/cascade_correlation.py`: lower-triangular fan-in `:1944-1946`; static linear readout `:1979`; MSELoss `:2018`; nn.Linear rebuild `:2032`; CR-060 hoist `:2047-2051`; epoch call `:2067`; output params `:738-739`; SharedTrainingMemory `ndim>2` cap `:272-273`; install dict `:4032-4037`; resize `:4051-4086`; pickle `:3012-3041`; HDF5 `:4914-4933`; grow `:921-946`.
- `candidate_unit/candidate_unit.py`: additive forward `:479`; order-invariant correlation `:935-941`.

**POC artifacts:**

- `util/ad-hoc/verify_delta_t_reference_code.py` — Approach-C LMU variable-step discretization; grid-invariance (`e_reg≈0.035`, `e_irr≈1.15×`).
- `util/ad-hoc/verify_ar_node_period_p5.py` — AR-node period scaling (P5 baseline).

---

*Working draft. Pairs with the [P4](JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-OQ4-DELAY-LINE-OUTPUT-MODULE-EVAL.md) and [P5](JUNIPER_2026-06-10_JUNIPER-RECURRENCE_RECURSE-OQ4-P5-RECURRENT-OUTPUT-LAYER-EVAL.md) evaluations and the [Δt-handling note](JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md). The dataset audit (§9) is the deferred validator. Lead-assembled from verified workflow outputs; not yet through an automated critic pass.*
