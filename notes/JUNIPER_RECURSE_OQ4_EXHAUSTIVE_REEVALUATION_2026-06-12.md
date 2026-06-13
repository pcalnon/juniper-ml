# OQ-4 Exhaustive Reevaluation — Recurrent Cascade-Correlation Options Decision Map

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 model-pick exhaustive reevaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-12

---

> **What this is.** A consolidated, adversarially-verified decision map for *how (and whether) to give Cascade-Correlation recurrent capability*, integrating the full option space — P1–P6, ESN, NEAT, LMU/SSM, P2 group-units, and the negative-eigenvalue linear-RNN — under constraint **C1** (first-principles, no library black box). It folds in four new investigation threads (T1 P6, T2 ESN/NEAT, T3 LMU/SSM, T4 a juniper-data operational-demands audit) plus a head-to-head **held-out generalization POC**, on top of the prior P1–P5 evaluations. Pairs with — does not duplicate — the P4/P5 evaluation (`JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md`, PR #400), the [P1/P2/P3 proposals](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md), and the [Δt doc](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md).
>
> **Headline verdict — two findings that settle the reevaluation.**
> 1. **No cheap or cascor-native option breaks the star-free / no-count ceiling.** The entire star-free family — RCC (P1), P4-FIR, P5, **P6 (the credible NARX breaker)**, ESN, LMU, vanilla nonnegative SSM — leaves it intact, confirmed *empirically* (held-out parity & mod-3 collapse to the majority floor; best margin **−0.018**) and from web-verified theory. The only genuine breakers add **group structure / negative (non-commutative) recurrence into the dynamical state**: P2 (group units, *no training recipe*), a **negative-eigenvalue input-dependent linear-RNN** (Grazzi et al. ICLR 2025 — general *and* trainable, but a non-cascor paradigm), and NEAT (topological, evolutionary, lowest cascor-fit).
> 2. **The ceiling is not a binding operational constraint for the current juniper-data catalog.** 9 of 10 generators are stateless non-temporal classification; the one temporal set (equities) is persistence-dominated (`|corr|=0.998`; memory adds ≤0.13); the two `%2` sets (`xor`, `checkerboard`) are *static-spatial* parity (stateless); `arc_agi` is *program synthesis*, orthogonal to counting.
>
> **⇒ Recommendation:** keep the cheap star-free path — **P4-FIR + Δt-as-feature** — as the rational default; treat **Δt-nativeness (LMU / Approach-C)** as the only axis that may force a model change; and **gate all ceiling-breaking work behind a concrete trigger**: the addition of a temporal dataset with a *verified non-star-free (parity / mod-n / group) target*. If that trigger fires, the route is a **negative-eigenvalue linear-RNN block**, not output enrichment (P6 is empirically rejected).

---

## 0. Provenance & method

- **Workflow:** a ≈15-agent adversarial reevaluation (grounding → a numpy POC build+verify → four threads, each web-verified and file:line-cited → per-thread refuters → a cross-cutting citation/consistency audit). No synthesis agent — this doc is authored directly from the verified thread findings + the POC I re-ran myself.
- **Empirical core:** [`../util/ad-hoc/verify_oq4_expressivity_suite.py`](../util/ad-hoc/verify_oq4_expressivity_suite.py) (+ helper `verify_p6_narx_mlp_output_eval.py`) — numpy-only, `SEED=20260612`, deterministic; I re-ran it end-to-end (exit 0, 522 s) and every figure below is from that run. P6's BPTT gradient is hard-gated against finite differences (`5.46e-07`).
- **Anti-hallucination:** every literature claim is a web-verified primary source; every code claim cites live `file:line`; every number is measured. The audit re-verified the riskiest citations (incl. forward-dated/paywalled ones). **Audit-flagged defects were excluded from this doc:** a fabricated `4.4e-16` precision figure (T1), a mislabeled ESN washout figure (T2a), and "`reproduced=true`" mis-cited as a printed token (T4). One *genuine* defect lives in another doc and is flagged in §7 (not fixed here — concurrent edits).
- **Scope honesty:** the POC measures *learn-and-generalize-or-not*; the impossibility itself is the literature's. P2 and the Grazzi linear-RNN are **literature-grounded, not measured** (P2 has no recipe to test; the linear-RNN is out of cascor scope). Held-out failure is *consistent with*, not a *proof of*, the ceiling.

---

## 1. The decisive empirical result — the ceiling is intact across the entire star-free family

The POC asks the one question that matters: **which mechanism learns parity / mod-counting that *generalizes* to a held-out stream?** (In-sample fit is a trap — a model with enough parameters memorizes a finite stream's parity spuriously.)

**Held-out running parity** (train → freeze → disjoint stream; majority floor **0.531**):

| Candidate | in-sample acc | **held-out acc** | margin vs floor | verdict |
|---|---|---|---|---|
| P5 — single recurrent output | 0.586 | 0.477 | −0.054 | fail |
| **P6 — NARX hidden-MLP (Hd 16 / 32)** | 0.73 / 0.76 | **0.513 / 0.507** | −0.018 / −0.024 | **fail** |
| ESN — linear / mlp readout | 0.67 / 0.56 | 0.456 / 0.479 | −0.076 / −0.052 | fail |
| LMU — linear / mlp readout | 0.57 / 0.64 | 0.496 / 0.496 | −0.036 | fail |

- **Mod-3 counting (Z₃):** every candidate `0.341–0.352` vs floor `0.351` — no modular counting generalizes either.
- **Positive CONTROL (the sharp diagnostic):** a plain 2-layer MLP fed the *clean* previous label `o(t−1)` learns XOR perfectly (**1.000 / 1.000**). So the MLP family *has* XOR-capacity — the recurrent candidates fail only because they must **bootstrap `o(t−1)` through an output-state-blind drive** (`cascade_correlation.py:1942-1946`). P6's failure is thus about the cascor substrate, not capacity or under-training (gradient verified `5.46e-07`).
- **Horizon is reach, not counting:** cutoffs (|corr|≥0.5) — FIR/P5 = 30, LMU = 40, ESN = 5. LMU reaches *furthest* yet still fails parity — a long memory does **not** lift the ceiling.

**P6 is the headline negative.** It is the one architecture the P5 doc flagged as the credible escape ("a hidden MLP making it a true NARX net *could* clear the bar"). The decisive test closes that hatch: **NARX universality (Siegelmann–Horne–Giles 1997) does not transfer**, because their construction feeds back the *true output*, while cascor's feature drive is output-state-blind. Richer/MLP recurrent *output* buys nothing over P5 on expressivity, at higher integration cost.

---

## 2. The full option taxonomy

| Option | Breaks ceiling? | Mechanism / why | Training recipe | Δt-native | C1 | cascor-fit | cost |
|---|---|---|---|---|---|---|---|
| **P1** self-recurrent RCC | **No** | self-loop, positive-recurrent → star-free | gradient/correlation | no | ✓ | native | high |
| **P4-FIR** delay line | **No** | finite TDNN (FIR) | none needed (precompute) | no | ✓ | native | **lowest** |
| **P4-IIR** feedback | **No** | single-neuron IIR | BPTT (worker-side) | no | ✓ | medium | high |
| **P5** recurrent output | **No** | single self-recurrent output, blind drive | BPTT (output) | no | ✓ | medium | medium |
| **P6** NARX hidden-MLP output | **No** *(empirically rejected)* | MLP has XOR-capacity but can't bootstrap state from blind drive | BPTT (output) | no | ✓ | medium | medium-high |
| **ESN** reservoir | **No** | fading memory = star-free (Grigoryeva–Ortega) | ridge readout (closed-form) | no (classic) | ⚠ random reservoir | **high** (readout = output layer) | low-medium |
| **LMU** | **No** | diagonal/positive SSM = star-free | readout trained | **yes** (Approach-C) | ✓ (matrix-exp of fixed matrix) | medium | medium |
| **vanilla SSM** (S4/Mamba) | **No** (+ 2nd TC⁰ wall) | nonnegative → star-free; all SSM ∈ TC⁰ | gradient | varies | ⚠ (selective Mamba heavier) | low (non-cascor) | high |
| **P2** group-implementing units | **Yes — C2 only** | negative-weight 2nd-order/multiplicative neurons (cyclic group) | **none** (no constructive recipe) | no | ✓ | needs new unit kind + WS-0 | research |
| **Neg-eigenvalue input-dep linear-RNN** (Grazzi) | **Yes — general** | eigenvalues in [−1,1] ⇒ any regular language | **plain GD, scales to 1.3B** | possible | ✓ (linear recurrence) | low (different paradigm) | medium |
| **NEAT** | **Yes — topological** | arbitrary recurrent cycles (not a cascade); Omlin–Giles DFA encoding | evolutionary (scales poorly on deep counting) | no | ⚠ (stochastic search) | **lowest** (replaces the engine) | high |

---

## 3. The three genuine ceiling-breakers — and why none is a cheap cascor extension

The ceiling is a property of the **cascade topology / output-state-blind drive / fading memory / nonnegative spectrum** — *not* of capacity, depth, output richness, or memory length. So every genuine breaker changes the *dynamical state substrate*:

- **P2 — group-implementing units.** Negative-weight second-order (multiplicative) neurons implementing the cyclic group C2 (Knorozova–Ronca 2024, Thm 7 / Props 5-6). Breaks the ceiling **only at C2/parity** in the concrete construction (general Zₙ>2 is left a *conjecture* there). **Fatal gap: no constructive / correlation-compatible training recipe exists.** Still the "research track."
- **Negative-eigenvalue input-dependent linear-RNN (Grazzi et al. ICLR 2025, arXiv:2411.12537).** The decision-relevant breaker: positive-eigenvalue linear RNNs *cannot* do parity, but eigenvalues in **[−1,1]** (products of I−outer-product/Householder matrices) let them learn **any regular language**, trained by **ordinary gradient descent at scale**. It is the *only* breaker that is both **general** and **trainable** — but it is a linear-RNN *block*, a different paradigm from cascor's grown candidate pool. The natural integration is "grow a small negative-eigenvalue linear-recurrence block as a candidate unit kind" (a P2-adjacent constructive variant worth a future proposal *iff* the trigger fires).
- **NEAT (Stanley–Miikkulainen 2002).** Breaks the ceiling **topologically** — its add-connection mutation wires arbitrary recurrent cycles (the ceiling is a property of the *cascade*, which NEAT is not; Omlin–Giles 1996 show 2nd-order RNNs stably encode DFAs of arbitrary length). It *has* a working recipe (evolutionary), unlike P2 — but it **discards the entire cascor engine** (correlation objective, freeze-on-tenure, worker/snapshot), scores lowest cascor-fit, and evolved plain RNNs scale poorly on deep counting. **Niche / parked: only if a counting dataset arrives *and* a second non-cascor engine is acceptable.**

---

## 4. The two SSM ceilings (T3) — and the real LMU/SSM win

The single most useful precision point: **"the SSM ceiling" is two walls**, and RCC's "star-free" sits between them.

| Level | Example | Group character | A **diagonal/nonnegative** SSM (LMU, S4D, Mamba) |
|---|---|---|---|
| **(A) star-free / aperiodic** | "contains substring", flip-flop | trivial groups | **✓ can** (better than transformers here) |
| **(B) modular counting** | parity (Z₂), mod-3 | Abelian/solvable | **✗ if nonnegative** (Sarrof–Veitsman–Hahn 2024); ✓ *iff* negative/complex eigenvalues + input-dependence (Grazzi) |
| **(C) non-solvable-group tracking** | S₅ permutation composition | non-solvable | **✗ for *any* SSM** — all SSMs ∈ TC⁰ (Merrill–Petty–Sabharwal 2024, "Illusion of State") |

**Consequences:** (1) stepping outside cascor to an SSM does **not** buy a free ceiling-break — nonnegative SSMs are *exactly* star-free, and they carry a *second*, strictly harder wall (C) that RCC's framing never names. (2) The genuine LMU/SSM advantage is **continuous-time Δt-nativeness** (the Approach-C win, already designed in the Δt doc §8), not expressivity. (3) The LMU is the C1 sweet spot (matrix-exp of a fixed closed-form matrix), but as a *diagonal* SSM it is solvable-groups-only.

---

## 5. The dataset audit (T4) — no current dataset demands the ceiling

Operational-demand characterization of every juniper-data generator:

| Dataset | task | temporal? | needs recurrence | needs counting / group | note |
|---|---|---|---|---|---|
| `checkerboard` | classification | no | no | **no** (static-spatial `%2`, stateless MLP solves) | not temporal parity |
| `xor` | classification | no | no | **no** (static 2-bit XOR; cascor's classic case) | not temporal parity |
| `circles`, `gaussian`, `moon`, `spiral` | classification | no | no | no | i.i.d. 2-D |
| `mnist` | classification | no | no | no | i.i.d. images |
| `csv_import` | generic | depends | depends | depends | user data |
| `equities` | regression | **yes** | bounded-horizon (weak) | **no** | persistence `0.998`; memory adds ≤0.13 |
| `arc_agi` | reasoning | no (grid→grid) | n/a | **no — orthogonal** | **program synthesis**, off the counting axis |

**The `arc_agi` hypothesis is refuted:** it was the one candidate ceiling-demander, but ARC is grid-to-grid *program induction*, a different and harder computational class than parity/group-counting — breaking the star-free ceiling would not help it. **No dataset in the catalog justifies the cost of ceiling-breaking**, and the empirical equities result independently confirms the ceiling is not binding for the live use-case.

---

## 6. The unifying mechanism

Across every thread and the POC, one statement explains all results: **the star-free ceiling is a property of the dynamical-state substrate, not of capacity, depth, output richness, or memory length.**

- Enrich the **output** (P6's MLP) → no help (the state, not the readout, is the bottleneck; the blind drive can't bootstrap `o(t−1)`).
- Lengthen **memory** (LMU reaches horizon 40) → no help (reach ≠ counting).
- Add a **random reservoir** (ESN) → no help (fading memory = star-free; ESN was the *worst* parity performer).

Every genuine breaker injects **group structure or negative/non-commutative recurrence into the state itself** (P2's multiplicative neurons; Grazzi's negative eigenvalues; NEAT's arbitrary cycles). That is the dividing line.

---

## 7. Recommendation & decision map

1. **Default (today): the cheap star-free path.** Adopt **P4-FIR + Δt-as-feature** as the temporal substrate — lowest integration cost, mini-batch-friendly, and sufficient for every dataset the catalog plausibly targets. The ceiling is not binding.
2. **The axis that can force a change is Δt, not expressivity.** If irregular-Δt becomes a priority, move to the **LMU / Approach-C** continuous-time memory (Δt doc §8) — C1-clean and the only native option. This is independent of the ceiling.
3. **Gate ceiling-breaking behind a concrete trigger.** Pursue a breaker *only* when a temporal dataset with a **verified non-star-free (parity / mod-n / group) target** is added. If it fires, the rational route is a **negative-eigenvalue input-dependent linear-RNN block grown as a candidate unit** (Grazzi — general + trainable), *not* output enrichment (P6 rejected) and *not* P2 (no recipe) unless a constructive recipe is found. NEAT only if a second engine is acceptable.
4. **Correction to carry (not fixed here):** the model doc (`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md:173`) still asserts ESN/LMU "does not share RCC's star-free ceiling" — a **category error** (ESN/LMU *are* star-free; SVH 2024 + the measured ESN parity collapse contradict it). It should be retracted to "fading-memory regression, not ceiling-breaking." Left for the model doc's owner (concurrent edits in flight; not edited here).

## 8. Open questions

1. **Is any future juniper dataset expected to need modular/group counting** (the trigger)? If not, the ceiling question is closed in favor of the cheap path.
2. **Is continuous-time Δt a priority** (equities calendar gaps, future event-driven data)? If yes, LMU/Approach-C jumps the queue regardless of the ceiling.
3. **Worth a "P7" sketch** — a grown negative-eigenvalue linear-recurrence candidate block (the Grazzi mechanism in cascor's constructive frame)? It is the one ceiling-breaker that is both general and trainable; the open problem is a *correlation-compatible* growth recipe.

---

## References (web-verified)

- Minsky & Papert 1969 — *Perceptrons* (single linear-threshold neuron cannot represent XOR).
- Giles, Chen, Sun, Chen, Lee & Goudreau 1995 — IEEE TNN 6(4):829-836; Kremer 1996 — IEEE TNN 7(4):1047-1051 (RCC = star-free).
- Omlin & Giles 1996 — *Constructing deterministic finite-state automata in recurrent neural networks*, JACM 43(6):937-972 (2nd-order RNN stable DFA encoding).
- Siegelmann, Horne & Giles 1997 — IEEE Trans. SMC-B 27(2):208-215 (NARX universality, *output-only feedback + MLP map*).
- Stanley & Miikkulainen 2002 — *Evolving Neural Networks through Augmenting Topologies* (NEAT), Evol. Comput. 10(2):99-127.
- Grigoryeva & Ortega 2018 — *Echo state networks are universal*, Neural Networks 108:495-508 (universal **for the fading-memory class**).
- Knorozova & Ronca 2024 — *On the Expressivity of Recurrent Neural Cascades*, AAAI; arXiv:2312.09048 (RNC = star-free; group-unit remedy; Thm 7).
- Merrill, Petty & Sabharwal 2024 — *The Illusion of State in State-Space Models*, ICML; arXiv:2404.08819 (all SSMs ∈ TC⁰).
- Sarrof, Veitsman & Hahn 2024 — *The Expressive Capacity of State-Space Models* (nonnegative SSM = star-free; no parity), NeurIPS; arXiv:2405.17394.
- Grazzi, Siems, Zela, Franke, Hutter & Pontil 2025 — *Unlocking State-Tracking in Linear RNNs through Negative Eigenvalues*, ICLR (Oral); arXiv:2411.12537.
- *(recent, supporting — verified this session):* Shakerinava et al. 2026 (diagonal-SSM state-tracking limits, arXiv:2603.01959); Khavari et al. 2025 (arXiv:2508.07395).

## Cross-references

- P4 + P5 evaluation (the star-free family): `JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md` (PR #400)
- OQ-4 proposals (P1/P2/P3): [`JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md`](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md)
- Irregular-Δt & continuous-time (LMU/Approach-C): [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md)
- Empirical POC: [`../util/ad-hoc/verify_oq4_expressivity_suite.py`](../util/ad-hoc/verify_oq4_expressivity_suite.py)

---

*Working draft. Consolidated decision map for the OQ-4 recurrent-Cascade-Correlation model pick across P1–P6 + ESN/NEAT/LMU-SSM + the genuine ceiling-breakers, grounded in a held-out generalization POC and a juniper-data operational-demands audit. No code ships on this basis until ratified and Workstream 0 is opened.*
