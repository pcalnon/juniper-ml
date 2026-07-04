# "P7" Design — a Grazzi Negative-Eigenvalue Block Grown in Cascade-Correlation's Constructive Frame

**Project**: juniper-recurse — recurrent NN initiative; OQ-4 ceiling-breaker design
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-13

---

> **What this is.**
> The design + open-problem investigation for **"P7"**: growing a **Grazzi negative-eigenvalue input-dependent linear-RNN block** (the one ceiling-breaker the [OQ-4 exhaustive reevaluation](JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md) found to be *both general and trainable*) as a **Cascade-Correlation candidate unit**.
> The motivating constraint: the cheap star-free default (P4-FIR + Δt) is *near-term* only; mid/long-term needs a true ceiling-breaker, and P7 is the cascor-native route.
> Pairs with the reevaluation, the [P1/P2/P3 proposals](JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md), the [Δt doc](JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md), and the [model doc](JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md).
>
> **Headline finding (and it overturned the prediction).**
> The central open question was: *can cascor's correlation objective — a centered second-order statistic — ever drive a block to the **negative eigenvalues** that state-tracking needs, or is it constitutionally blind to group structure?*
> The decisive POC answers **NO, it is not blind — for parity**: maximizing `|corr(block_output, residual)|` over the window by BPTT trains a diagonal Grazzi block to do **held-out parity** (`0.982`, margin `+0.463` over floor), driving the input-dependent eigenvalue `a(1) → −1.00`, **identically to ordinary task-loss gradient descent.**
> So **cascor can grow a negative-eigenvalue block to break the parity (C2) ceiling with its own growth objective** — modulo three concrete preconditions (BPTT + an adaptive optimizer + recurrent state in the candidate trainer, all absent today).
> The **remaining** open problem is everything past C2: general counting needs a **non-diagonal, jointly-trained** block (Grazzi Thm 2), which collides with cascor's greedy one-candidate-at-a-time growth.

---

## 0. Provenance, method & a process note

- **Method:** a 13-agent adversarial workflow (ground → numpy POC build+verify → four solution threads S1–S4 → refuters → cross-cutting audit). No synthesis agent; this doc is authored directly from the verified findings + the POC I re-ran myself.
- **Empirical core:** [`../util/ad-hoc/verify_p7_grazzi_block_growth.py`](../util/ad-hoc/verify_p7_grazzi_block_growth.py) — numpy-only, `SEED=20260613`, deterministic, **Adam** optimizer (faithful to the paper). Gradient hard-gated against finite differences (`1.25e-06`). Reuses the P5/OQ-4 BPTT + held-out harness.
- **Anti-hallucination:** every literature claim web-verified; every code claim cited at live `file:line`; every number measured.
  - The audit re-verified the riskiest citations (incl. the forward-dated/paywalled ones) and **resolved a sharp S1-vs-refuter contradiction**: the two had run *two different commits* of the POC — `c0fe019` (plain-SGD, which fails) vs `ba7596e` (Adam, which works).
  - **Adam is required**; this doc uses the Adam results.
  - Excluded defects: a fabricated `4.4e-16`-style precision figure and an unverifiable ESP washout number flagged in sibling threads.
- **⚠ Process note (git hygiene):** during this workflow, sub-agents committed the POC to the Phase-A branch and it was merged via #403, so a **plain-SGD (non-working) POC version inadvertently landed on `main`.**
  - This PR ships the corrected **Adam** version over it.
  - (An unrelated uncommitted `wake_the_claude.bash` change found in the worktree was preserved to `git stash`, not discarded — provenance unclear.)
- **Scope honesty:** the POC measures *learn-and-generalize-or-not* for an **isolated single block**; it does **not** exercise in-cascor growth, freeze-on-tenure, the worker, or snapshots — those are *design proposals against cited code* (§5), not demonstrated capabilities.
  - The "P7 breaks the ceiling" claim is established **for parity / C2 only**.

---

## 1. The design — what P7 is

**The block (Grazzi, ICLR 2025).** A small input-dependent **linear** recurrence whose state-transition eigenvalues are allowed to be **negative** (range `[−1,1]`):

```psuedocode
h(t) = a(x_t) ⊙ h(t−1) + b(x_t) ⊙ u(t)         # diagonal form (the POC's block)
o(t) = w · h(t) + c                            # linear readout
a(x_t) = 2σ(α_{x_t}) − 1 ∈ (−1,1)              # input-dependent eigenvalue; CAN be negative
```

`a`, `b` are small per-symbol tables (`α, β : (|Σ|, d)`); `w : (d,)`, `c` scalar; state dim `d` small.
The diagonal form realizes the cyclic group **C2 = ℤ/2ℤ**: set `a(1) = −1` (flip on a 1-bit), `a(0) = +1` (hold) ⇒ `h(t)` toggles with `(#1s mod 2)` = **parity**.
General regular languages need the **Generalized-Householder** form `A = I − 2φvvᵀ` (non-diagonal, eigenvalues still in `[−1,1]`).

**Grown as a cascor candidate.**
The constructive loop is preserved: train a pool of candidate **blocks** to maximize `|corr(o(t), residual_error)|` over the window, install the best, **freeze (tenure)**, and let it feed downstream — exactly cascor's recipe, but the "candidate" is now a state-carrying recurrent block trained by BPTT rather than a stateless single-shot neuron.

---

## 2. The decisive result — the correlation recipe works for parity

POC, same diagonal block under three regimes (all Adam + BPTT; held-out = train one Bernoulli stream, freeze, eval a disjoint stream; floor ≈ 0.518):

| Regime                                       | loss                 | eigenvalue range | held-out parity (best) | margin            | learned `a(1)`    |
|----------------------------------------------|----------------------|------------------|------------------------|-------------------|-------------------|
| **(i) task-MSE / neg** (Grazzi baseline)     | MSE                  | `(−1,1)`         | **0.982** (d=8)        | **+0.463**        | min **−1.00**     |
| **(ii) positive-only** (ablation)            | MSE                  | `(0,1)`          | 0.512 (all d)          | **−0.007** (fail) | stuck **≥ +0.04** |
| **(iii) `\|corr\|` / neg** — *the P7 recipe* | `−\|corr(o,resid)\|` | `(−1,1)`         | **0.982** (d=4 & d=8)  | **+0.463**        | min **−1.00**     |

Supporting cells: **GRAD** analytic-BPTT vs finite-diff `1.25e-06` PASS; **CONTROL** (hand-set `a(0)=+1, a(1)=−1`) `0.988` ⇒ the block *can represent* parity, so any failure is optimization not capacity; **MOD-3** all three regimes `~0.33` (fail) ⇒ the diagonal block is **parity-only**.

**Reading it:**

- **(iii) ≡ (i):** the cascor `|corr|` objective reaches the *same* held-out accuracy and drives `a(1)` to the *same* `−1.00` as the task loss.
  - **Correlation is not blind to the C2 sign.**
- **(ii) fails:** same block, same optimizer, only the eigenvalue range differs ⇒ the **negative eigenvalue is the causal mechanism** (Grazzi Thm 1: positive-only LRNNs cannot solve parity — web-verified).
- **Caveats (load-bearing):** **Adam is required** (plain SGD gets stuck in a "predict-the-mean / saturate" basin — this is the c0fe019-vs-ba7596e provenance story); success needs **d ≥ 4** (d=1 fails) and is **seed/restart-sensitive** (8 restarts × 300 epochs); the diagonal block is **parity-only**.

---

## 3. Why correlation-BPTT *can* see the sign (the S4 theory)

The load-bearing distinction — conflating these two objects is the central error to avoid:

| object                                   | what it is                 | order / locality                                              |
|------------------------------------------|----------------------------|---------------------------------------------------------------|
| `corr(o, residual)`                      | one scalar over the window | centered **2nd-order** statistic; **sequence-position-blind** |
| `∂ corr / ∂α_{1}` (the eigenvalue logit) | the BPTT adjoint           | a **per-timestep credit signal summed over the window**       |

The correlation *value* genuinely cannot see the sign flip (it is invariant to global readout-sign and to temporal ordering within the centered moment).
But the correlation *gradient* is computed by back-propagating through the recurrence, so it carries the sequential credit that distinguishes `a(1)=−1` from `a(1)=+1`.
The POC proves this gradient **suffices for parity when the residual already encodes the running-parity trajectory.**
It does **not** prove correlation can supervise group structure in general (§4).

---

## 4. The refined open problem & candidate solutions

**What is solved:** P7-diagonal for **parity / C2** — a correlation-compatible growth recipe **exists and is measured** (direct correlation-BPTT, Adam). Sub-problem (1) ("is correlation blind?") = **No**, for C2.

**What remains open:**

- **(2) General counting / groups need a *non-diagonal, multi-dimensional, jointly-trained* block** (Grazzi Thm 2: "non-triangular matrices are needed to count modulo 3" — web-verified; POC mod-3 fails all regimes). This **collides with cascor's greedy, one-candidate-at-a-time, frozen-on-tenure growth** — the deepest open problem.
- **(3) Integration gaps:** the candidate trainer is today stateless single-shot **plain SGD** (`candidate_unit.py:1061-1063`), with **no BPTT, no adaptive optimizer, no recurrent state**; the 4-key frozen-unit dict (`cascade_correlation.py:4032-4037`) and the stateless replay (`:1946`) have **no slot** for a transition table or carried state. P7 needs all of these added (§5).

**Candidate solutions to (2)** (developed + refuted; none yet measured end-to-end):

- **B — decouple training from selection (most viable).**
  - GD-train each candidate block (internally, Adam+BPTT, on a local residual-prediction loss) and keep cascor's **correlation-based *selection*** (`_select_best_candidates` ranks by `abs(correlation)`, `cascade_correlation.py:4214`) and freeze-on-tenure.
  - Cascor's `|corr|` does *selection*, not unit-training — which the POC shows is unnecessary for the *recurrence* (GD trains it) yet preserved for the *constructive* loop.
  - This sidesteps "can correlation train a non-diagonal block."
- **C — joint "macro-candidate" per round.**
  - Grow a small multi-dimensional non-diagonal (Generalized-Householder) block as a cohort jointly trained, then tenure it as one unit — relaxing greedy *single-neuron* growth to greedy *single-block* growth.
- **D — parameterization bias.**
  - Parameterize the transition so the correlation gradient is pushed toward negative eigenvalues / Householder structure when the residual carries periodic structure.
- **Hypothetical-solution shape (if B/C/D under-deliver).**
  - Any correlation-compatible recipe for state-tracking beyond C2 must supply: (a) a **residual that already encodes the target state-trajectory** (so the BPTT adjoint has signal), (b) a **per-timestep credit signal** (not just a window-global scalar), and (c) a **surrogate objective that is correlation-compatible *and* structure-sensitive**.
  - The open research question is whether such an objective exists for non-Abelian groups, or whether greedy growth is fundamentally limited to solvable (Abelian) structure.

---

## 5. Cascor integration design (against the real code)

| Concern            | Today (cited)                                                                                                                                  | P7 delta                                                                                                                                                                       |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Candidate trainer  | stateless single-shot **plain SGD** (`candidate_unit.py:1061-1063`); forward `:1011-1012`; loss `=−\|corr\|` `:1045`; one `backward()` `:1050` | **BPTT-over-window + Adam + recurrent rollout** in the candidate trainer (the P5/OQ-4 harness already has the `−\|corr\|`-BPTT machinery to reuse)                             |
| Frozen-unit record | exactly 4 keys `{weights,bias,activation_fn,correlation}` (`cascade_correlation.py:4032-4037`)                                                 | **tagged-union extension**: a `kind="grazzi"` unit carries `α,β` transition/drive tables, `w,c` readout, `state_init` — leaving the 4-key path byte-identical for legacy units |
| Frozen replay      | stateless dot-product, no time axis (`:1946`, `unit_input` is input+earlier-hidden only)                                                       | a **stateful rollout** for recurrent units: `_compute_hidden_outputs` gains a time loop producing the block's `h`-trajectory; frozen blocks are constants (no grad), cacheable |
| Selection          | rank by `abs(correlation)` (`:4214`); cohort strategy (`:4164-4203`)                                                                           | **unchanged** — this is exactly the hook solution **B** exploits                                                                                                               |
| Output layer       | bare-affine output (`:1979`), static MSE fit (`:2018`)                                                                                         | unchanged (freeze localizes recurrence to the block; output stays a static solve)                                                                                              |
| Snapshot / worker  | 4-key save/load; scalar worker tuples                                                                                                          | extend schema for the transition tables + state; deploy the recurrent forward + BPTT worker-side                                                                               |

**Integration cost:** heavier than P4-FIR/P5 (a real recurrent+Adam+BPTT candidate trainer + a state-carrying frozen unit + Workstream-0 time axis), but it is the **first cascor-native ceiling-breaker** and reuses cascor's selection/freeze loop intact (unlike NEAT, which replaces the engine).
Cheaper than P2 only in that it *has* a training recipe.

---

## 6. Recommendation & next step

1. **P7-diagonal (parity / C2) is buildable with a correlation-compatible recipe** — *demonstrated* in isolation (the recipe works; Adam+BPTT+state are the required candidate-API upgrades).
    - It is the **first cascor-native route past the star-free ceiling**, gated behind the same trigger as the rest of the OQ-4 decision: a dataset with a verified non-star-free target.
2. **The general case (non-Abelian / mod-n, non-diagonal block) remains open** — the greedy-growth vs jointly-trained-block collision is the real research problem; **solution B (decouple train/select)** is the most promising near-term reconciliation, with the hypothetical-solution shape (§4) as the fallback map.
3. **Recommended next step (when the trigger fires):** prototype **P7-diagonal** — (i) add BPTT + Adam + recurrent state to the candidate trainer (the hardest engineering lift; Workstream-0-adjacent), (ii) the tagged-union frozen-unit schema, (iii) validate against the POC's parity result *inside* cascor; then research the non-diagonal/greedy reconciliation (B/C) on a real mod-n/group task.

## 7. Open questions

1. **Does solution B actually preserve state-tracking** once the block is GD-trained-then-correlation-*selected* and frozen — i.e., can later candidates build on a frozen state-tracking unit? (Untested; the POC is single-block.)
2. **Is there a correlation-compatible objective for non-Abelian groups at all**, or is greedy constructive growth fundamentally capped at solvable structure?
3. **Is the Adam dependence essential** or can a cascor-friendly second-order/Quickprop-style step reach the negative-eigenvalue basin? (Quickprop is cascor's native optimizer; the POC used Adam.)

---

## References (web-verified)

- Grazzi, Siems, Zela, Franke, Hutter & Pontil 2025 — *Unlocking State-Tracking in Linear RNNs through Negative Eigenvalues*, ICLR (Oral); arXiv:2411.12537. (Thm 1: positive-only eigenvalues ⇒ no parity; Thm 2: mod-3 ⇒ non-triangular matrices; `Diag(2σ(x)−1)` + Generalized-Householder `I−2φvvᵀ`, eigenvalues `[−1,1]`, learns any regular language, GD-trained. The arXiv revision history's "Correction to Theorem 1 and 2" confirms these are real, named theorems.)
- Knorozova & Ronca 2024 — *On the Expressivity of Recurrent Neural Cascades*, AAAI; arXiv:2312.09048 (RNC = star-free; group-implementing-neuron remedy; Thm 7 negative-weight).
- Sarrof, Veitsman & Hahn 2024 — nonnegative SSM = star-free; no parity (arXiv:2405.17394); Merrill, Petty & Sabharwal 2024 — *Illusion of State* (all SSMs ∈ TC⁰; arXiv:2404.08819). *(context from the reevaluation)*
- Fahlman 1991 — *The Recurrent Cascade-Correlation Architecture*, NIPS-3 (the correlation/freeze growth recipe P7 must fit).

## Cross-references

- OQ-4 exhaustive reevaluation (why P7 is the route): [`JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md`](JUNIPER_2026-06-12_JUNIPER-RECURRENCE_RECURSE-OQ4-EXHAUSTIVE-REEVALUATION.md)
- OQ-4 proposals (P1/P2/P3): [`JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md`](JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md)
- Irregular-Δt / continuous-time: [`JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md`](JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md)
- Model design & plan (OQ-4 RESOLVED callout): [`JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md`](JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md)
- Empirical POC: [`../util/ad-hoc/verify_p7_grazzi_block_growth.py`](../util/ad-hoc/verify_p7_grazzi_block_growth.py)

---

*Working draft. Designs the P7 Grazzi negative-eigenvalue block in cascor's constructive frame and investigates the correlation-compatible growth recipe. Decisive finding: the recipe **works for parity/C2** (correlation-BPTT drives `a(1)→−1`); the **general non-diagonal case vs greedy growth** is the remaining open problem, with solution B (decouple train/select) the most promising direction. No code ships on this basis until ratified and Workstream 0 is opened.*

---
