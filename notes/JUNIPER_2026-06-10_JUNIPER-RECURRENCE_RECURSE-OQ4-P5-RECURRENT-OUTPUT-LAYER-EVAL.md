# Recurrent Cascade-Correlation — P5 "Recurrent Output Layer" Module: Adversarial Evaluation

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 P5 design evaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-10

---

> **Epistemic legend (carried throughout).** `VERIFIED` = checked against opened code (`file:line`) or a quoted source (PDF/web) this session. `VERIFIED-PRIMARY` = quoted from a PDF/source opened and read. `VERIFIED-SECONDARY` = corroborated across ≥2 independent sources where the primary PDF text was not machine-extractable. `INFERRED` = a deduction (lower confidence; flagged). **P5 is novel and unpublished — every P5-specific verdict is an INFERENCE of the design-delta against verified code and verified literature, EXCEPT the autoregressive-node period facts, which were empirically re-run this session** (`util/ad-hoc/verify_ar_node_period_p5.py`). The three-axis separation mandated by the anti-hallucination rules — **REPRESENTABILITY** (what the architecture CAN express) vs **LEARNABILITY** (what BPTT-over-≤30-window can FIND) vs **DEPLOYED bound** (D≤30 stateless-per-window) — is kept strict in every section.

> **Evaluation provenance.** Produced 2026-06-10 by a maximal-depth adversarial multi-agent workflow with a dedicated formal-language ceiling sub-panel (182 sub-agents, ~15.4 M tokens, 2 827 tool calls): a 4-agent reality-brief (live cascor code, output-layer focus + corpus + POC + FIR/IIR/NARX/RNC-ceiling literature) → 8 adversarial lenses → **3-vote perspective-diverse refutation of every material finding** → a 6-angle ceiling sub-panel reading Knorozova-Ronca / Giles / Siegelmann-Horne-Giles directly → comparison → synthesis → two independent critics (completeness 0.90, anti-hallucination 0.93). **43 of 53 candidate findings survived refutation; 10 were rejected** (§18). The order-D AR-node period facts were empirically re-run this session via `util/ad-hoc/verify_ar_node_period_p5.py`. Companion to the P4 evaluation (`JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-OQ4-DELAY-LINE-OUTPUT-MODULE-EVAL.md`).

---

## 1. Executive Summary + Headline Verdict

### 1.1 The ceiling answer (PRIMARY interest) — FIRST

**P5 CAN break the star-free / no-count representational ceiling — PARTIALLY, into the bounded cyclic-group (mod-k) fragment, NOT full regular, and only at the OUTPUT layer — but the break is CONDITIONAL on a saturating output activation; as currently specced (linear readout + `nn.MSELoss`, VERIFIED `cascade_correlation.py:1979`/`:2018`) P5 does NOT break it (LTI fading memory only).**

The entire representational lift lives in the **new per-output autoregressive (AR) self-loop** at the readout:
`y_o(t) = f( W_o·[hidden activations + lag taps + raw inputs](t) + Σ_{k=1..D} v_{o,k}·y_o(t−k) )`.

The decisive evidence is empirical, re-run this session: a **single ADDITIVE sign/tanh node of AR order D≥2, under constant exogenous drive, realizes autonomous limit cycles of period > 2** (period-4 at D=2, period-6 at D=3, up to 16 at D=5/6; the order-1 case is capped at exactly period-2, reproducing Giles-1995/Fahlman). A period-k>1 orbit induces a **cyclic group Z_k** in the node's transition semigroup, which by McNaughton-Papert is **non-counter-free, hence non-star-free**. (`util/ad-hoc/verify_ar_node_period_p5.py`, re-run this session; K&R establish group-free = star-free, `2312.09048v2` p.4, VERIFIED-PRIMARY.) So P5 reaches a **bounded modular counter (mod-k)** — strictly more than P1's order-1 parity/Z2 and more than the Thm-7 toggle's mod-2.

**The break is bounded on every axis:**

- **Representationally — cyclic/abelian only, NOT full regular.** P5's loop is **FIRST-ORDER ADDITIVE** (Σ-of-taps inside one nonlinearity), not the **SECOND-ORDER MULTIPLICATIVE** neuron Knorozova-Ronca construct a group with (their Props 5/6 build C₂ via ⊕=product, and conjecture the extension to finite simple groups). A single additive node's state is D sign bits, so its representable period ceiling is the **2^D pigeonhole bound**; random search over `(c, v, init)` *found* periods 4, 6, 8, 16, 16 for D=2..6 — a constructive lower bound (> 2 and > D), **not** the representable max. Crucially, the **exponential 2^D−1** period (reached by experiment [B] of the POC) requires a **multiplicative / XOR (LFSR) feedback** that an additive sign node provably cannot synthesize (parity-via-product is not additive) — that 2^D−1 register is **P2's second-order territory, NOT P5's**. So depth widens P5's reachable PERIODS (bounded cyclic counting) but not the ALGEBRA, and the exponential ceiling is out of additive reach.
- **NOT NARX-Turing-universal — the central misattribution to avoid.** Siegelmann-Horne-Giles 1997 get Turing-equivalence **because the fed-back output re-enters the full hidden MLP Ψ** (the hidden neurons simulate FSM states; the output is a passive linear node). P5 deliberately **silos** the feedback per-output, wraps it in **one** nonlinearity, and forbids it routing through the hidden cascade (CODE-confirmed: hidden fan-in `cascade_correlation.py:1944-1946` is strictly lower-triangular and `y_o` never re-enters any hidden unit). P5 is the constrained **Finite-Memory-Machine** regime, not the universal one.
- **Siloing blocks group composition across outputs.** Each output is at most one isolated cyclic counter; there is no inter-output coupling to compose into larger/non-abelian groups.
- **The hidden FIR cascade contributes ZERO lift.** It has no recurrent weight (strictly lower-triangular fan-in, no self-tap), so it is exactly K&R's arbitrary feedforward input-function β, over which their impossibility theorems already quantify (and which hold for non-constant *convergent* input). FIR + AR composition ceiling = AR ceiling alone; no super-additivity.

**Then the windowed caveat (kept separate, does NOT collapse the asymptotic answer).** The ratified DEPLOYED architecture is **D ≤ window ≤ 30, STATELESS PER WINDOW** (state — both hidden FIR registers and the output AR register — resets each window; no carry-across-windows). A recursion that resets every ≤30 steps unrolls the IIR to ≤30 lags = a finite-window FIR-of-outputs, so **any realizable counting period is capped at ≤ the window (≤30)**; a mod-k counter with k>30 is architecturally impossible regardless of representability or learnability. **The deployed bound is the hardest of the three ceilings.**

**And the learnability gate (the third axis, strictly below representability).** Even where mod-k is representable, BPTT-over-≤30-window on a single saturating AR loop is the classic vanishing/exploding-gradient regime, and a period-k limit cycle requires AR poles at marginal stability |λ|≈1 — **exactly** the gradient knife-edge. MSE supplies no pressure toward a cycle unless the target demands exact counting. So the counting lift is **largely unreachable/unmaintainable in practice**; P5's robust, real gain over P4 is the **fading-memory decay tail**, not reliable modular counting.

**Net headline:** REPRESENTABILITY (star-free + bounded cyclic, period > 2 — ~2D-3D observed per additive node, ≤ 2^D representable) **>** windowed-DEPLOYED (period ≤30) **≈** LEARNABILITY (BPTT-fragile, biased to no-count). On the ceiling axis, **P4 < P5 ≈ relocated+deepened P1 < P2**.

### 1.2 The four questions — one-liners

- **Q1 (recurrence correctness/effectiveness).** **AFFIRMATIVE at the readout, NEGATIVE in the hidden path.** P5 is a HYBRID: FIR exogenous feature cascade + genuine IIR autoregressive readout. The output loop satisfies the formal feedback litmus (unlike P4, which was a flat NEGATIVE), but is siloed and strictly weaker than NARX/Jordan. (VERIFIED structure; INFERRED P5 delta.)
- **Q2 (irregular-Δt).** **Poorly positioned — no improvement in Δt-awareness over P4.** The AR loop is sample-position-indexed (lag k), not elapsed-time-indexed; a 3-day gap ≡ a 1-day gap. Only Approach A (Δt-as-feature) applies; B/C are structurally inapplicable to a discrete AR register. One narrow gain: a *fed* Δt feature can now be *integrated* across the window via the loop (better than P4's static readout). (VERIFIED against the AR form + `_sequence.py:113-116`.)
- **Q3 (effective horizon).** **Headline gain over P4 at the readout: IIR fading-memory tail replaces P4's hard FIR cliff** — but only for the autoregressive component of the target; the exogenous/feature memory stays FIR-capped at D. Horizon is sample-count not real-time; deployed horizon is hard-capped at ≤30 by the window reset. (VERIFIED structure; INFERRED IIR tail.)
- **Q4 (mini-batch).** **Heavier than P4 on the output path, lighter than full stateful-RNN training.** P4 kept BOTH candidate and output training as order-free static solves; P5 inherits the order-free candidate path but makes OUTPUT training BPTT (within-window order becomes sacred; CR-060 hoist invalidated for the AR term). Crucially the recurrence never crosses the worker wire. (VERIFIED `cascade_correlation.py:2066-2076`, `:272-273`.)

---

## 2. What P5 Is + Taxonomy vs P4/P1/P2/P3

### 2.1 P5 definition

P5 = **P4's hidden layer (most-charitable FIR delay-lines) PLUS a NEW recurrent (IIR) output layer.**

**(1) Hidden layer = the most charitable P4.** Each selected candidate (hidden) node keeps a bolt-on depth-D TDNN/FIR delay-line on its OUTPUT — a shift register of its last D activations — attached at install. The lag taps are FLATTENED into the cascade fan-in so downstream candidates AND the output layer can consume them ("one cascade-layer late"). There is **NO feedback into a hidden node's own activation**; the hidden layer stays FIR / feed-forward. Candidate training is UNCHANGED (the P4 property).

**(2) Output layer = the NEW recurrence.** Each output node gets a TDNN/delay module whose **delayed outputs are fed back AS ADDITIONAL INPUTS TO THAT SAME OUTPUT NODE**:
`y_o(t) = f( W_o·[hidden activations + lag taps + raw inputs](t) + Σ_{k=1..D} v_{o,k}·y_o(t−k) )`.
This is genuine IIR/autoregressive feedback — a per-output-node self-loop. The feedback is **SILOED**: each output node sees only its OWN past outputs (not other outputs), and the fed-back outputs do NOT route back through the hidden cascade (the hidden FIR features are exogenous to the output AR). This is a **Jordan-network / NARX-flavored** structure (FIR exogenous features + AR output).

**(3) Training.** After each hidden-node install (all hidden weights frozen, exactly as cascor freezes today), the OUTPUT layer is retrained — but it is now RECURRENT, so the current static single-pass `nn.Linear` solve must become **BACKPROP-THROUGH-TIME (BPTT)** over the window; the feedback weights `v_{o,k}` (and the feedforward weights) are learned by backprop.

### 2.2 Where P5 slots in the OQ-4 taxonomy (corpus P1/P2/P3 VERIFIED; P4 VERIFIED; P5 INFERRED)

All proposals extend cascor's `grow → correlation-train candidate → install → freeze (tenure) → train-output` loop. They differ in the recurrent unit and how they treat the **star-free / no-count ceiling**.

| | Recurrence location & type | Ceiling treatment | Corpus / this-eval verdict |
|---|---|---|---|
| **P1** faithful RCC | One trainable self-recurrent weight on each HIDDEN candidate's own delayed activation; depth-1 IIR; correlation-trained during selection, frozen on tenure | **INHERITS** (+parity via a negative weight; Giles-1995 territory) | keep-with-fixes, "most citation-accurate, lowest-risk" (VERIFIED corpus) |
| **P2** group-implementing units | Cyclic-group (C₂) units via **negative-weight 2nd-order (multiplicative) neurons** in the HIDDEN pool; IIR + group state | **BREAKS — in-principle only** (no known constructive training recipe) | keep-with-fixes, heavily re-anchored; the OQ-4 moonshot (VERIFIED corpus) |
| **P3** grown reservoir/memory | Fixed ESN sub-reservoir / LMU cell per grown HIDDEN candidate; genuine evolving (fading/continuous) state; only read-in/readout trained | **INHERITS** — corpus corrects "avoids ceiling" to a **CATEGORY ERROR** (fading memory ≠ counting) | keep-with-fixes; "most architecturally honest and genuinely recurrent" (VERIFIED corpus) |
| **P4** hidden FIR delay-lines | Per-node OUTPUT delay-line buffering last D activations; **NO feedback anywhere**; pure FIR / TDNN / Takens embedding | **INHERITS — the WEAKEST** (threshold counting only) | mechanically implementable, NOT recurrence; does not advance OQ-4 (VERIFIED corpus + code) |
| **P5** (this eval) | **HYBRID**: P4's FIR hidden cascade + a NEW siloed per-output **IIR AR self-loop at the READOUT** | **BREAKS PARTIALLY** — bounded cyclic/mod-k, NOT full regular (INFERRED + empirically-verified period facts) | this document |

**The two pieces of P5 map onto the taxonomy differently:**

- P5's **hidden layer** = exactly P4 ⇒ reuse every P4 verdict for the hidden half (FIR, inherits ceiling, Δt-blind by position-indexing, D≤30 horizon, fan-in inflation, three-site lockstep change, RC-5 resync, untouched candidate training).
- P5's **output layer** = a NEW per-output AR self-loop ⇒ closest in spirit to **P1's depth-1 IIR self-loop, but RELOCATED to the readout, DEEPENED to order-D, SILOED, and BPTT-trained instead of correlation-trained**.

---

## 3. THE STAR-FREE CEILING — The Headline Question

This is the marquee section. Per Paul's ruling, the **asymptotic representational verdict** (output recurrence analyzed as a recurrence over UNBOUNDED sequences) comes FIRST; the **D≤30 windowed caveat** is layered on SEPARATELY afterward.

### 3.1 The formal backbone (theorems quoted, attributions exact)

**Knorozova & Ronca 2024, `arXiv:2312.09048v2` — "On The Expressivity of Recurrent Neural Cascades"** (VERIFIED-PRIMARY, full read). The exact characterization:

- **Theorem 5 (the ceiling):** *"The class of regular functions that can be implemented by RNCs of sign or tanh neurons with **positive weight** is the group-free regular functions."* (p.8)
- **Theorem 4 (the negative result):** *"For any regular function F that is not group-free, there is no RNC implementing F whose components are neurons with sign or tanh activation and **positive weight**."* (p.8)
- **group-free = star-free:** *"The group-free regular languages … coincide with the star-free regular languages, cf. (Ginzburg 1968)."* (p.4)
- **Theorem 7 (the negative-weight escape):** *"There is an RNC consisting of a single sign or tanh neuron with **negative weight** that implements a regular function that is not group-free regular."* (p.8) Worked example (p.23): *"a toggle neuron that recognises the language consisting of all strings of **odd length**, which is regular but not group-free."* (odd-length = parity = the cyclic group ℤ₂.)
- **The route to all-regular (contribution bullet 4, p.1):** *"It suffices to identify appropriate recurrent neurons. In particular, neurons that can implement finite simple groups. As a first step, we show that **second-order sign and tanh neurons can implement the cyclic group of order two**."* The paper's own definition of a second-order neuron (p.3): *"By default we will assume that the operator ⊕ is addition. We will also consider the case where ⊕ is product; in this case we refer to the neuron as a **second-order neuron**."*

**Giles, Chen, Sun, Chen, Lee, Goudreau 1995, IEEE TNN 6(4):829-836** (VERIFIED-SECONDARY; PDF font-scrambled, corroborated across PubMed 18255858, IEEE Xplore 392247, the Kremer abstract): Fahlman's RCC **cannot realize finite-state automata with state-cycles of length > 2 under a constant input signal**, under a **monotone (Heaviside / monotonically-increasing) activation**. The mechanism (VERIFIED-PRIMARY for the unit equation, `NIPS-1990` RCC paper p.191-192): the self-recurrent unit `V(t) = σ(Σ_i I_i(t)·w_i + V(t−1)·w_s)` either fixes (period 1, strongly positive self-weight) or *"oscillate[s] between positive and negative outputs on each time-step"* (period 2, negative self-weight) — a single order-1 monotone self-recurrent unit has no internal mechanism for period ≥3.

**Kremer 1996, IEEE TNN 7(4):1047-1051** (VERIFIED-PRIMARY abstract, PubMed 18263501): *"This paper extends the conclusions of Giles et al. by showing that there exists a corollary to their original proof which identifies a large second class of automata, that is also unrepresentable by RCC."* Kremer extends the **negative** results; it does NOT give a complete positive characterization.

**Siegelmann, Horne & Giles 1997, IEEE Trans. SMC-B 27(2):208-215** (VERIFIED-PRIMARY abstract, PubMed 18255858): *"NARX networks have a limited feedback which comes **only from the output neuron rather than from hidden states** … y(t)=Ψ(u(t−n_u),…,u(t),y(t−n_y),…,y(t−1)) … the function Ψ is the mapping performed by a Multilayer Perceptron. We constructively prove that the NARX networks … are computationally as strong as fully connected recurrent networks and thus Turing machines."* And the converse bound (VERIFIED-SECONDARY — this result is in the paper BODY, not the abstract; corroborated via the UMass tech-report PDF + web): *"when hard-limiting nonlinearities are used … NARX networks are only capable of implementing a subclass of FSM's called Finite Memory Machines (FMM's) … the reason FMM's are constrained is that there is a limited amount of information that can be represented by feeding back the outputs alone."*

**McNaughton & Papert 1971 + Schützenberger 1965** (VERIFIED-SECONDARY, formal-language identities): star-free = aperiodic = counter-free = group-free; counter-free automata **cannot count modulo any integer > 1, but CAN count to a threshold** (`1, 2, …, n−1, n-or-more`).

### 3.2 ASYMPTOTIC representational verdict (unbounded-sequence frame) — does the output self-loop lift the class?

**YES, partially — into bounded cyclic / mod-k counting.** The reasoning chain, with the empirical anchor:

1. **Where the lift can come from.** The hidden FIR cascade has **no recurrent weight** (strictly lower-triangular fan-in `unit_input = buffer[:, :col]`, `cascade_correlation.py:1945`, VERIFIED — unit `i` reads only inputs + earlier units, never its own or later column), so it is feed-forward / finite-window — strictly *below* even the star-free RNC class. In the K&R formalism the hidden cascade is exactly the recurrent neuron's arbitrary **feedforward input-function β** (*"the composition of a core recurrent neuron N with an input function β:U→V that can be implemented by a feedforward neural network"*, K&R p.3-4). K&R's impossibility theorems quantify over **all** such β, and K&R's convergent-input robustness (*"such a sequence is convergent even when the input is not constant but itself convergent"*, the sign/tanh flip-flop state-boundary discussion, formalized in Lemmas 10/11, VERIFIED-PRIMARY) kills the "a time-varying FIR drive helps" loophole. **So any super-star-free capability must come from the OUTPUT AR loop.** (`P5-CEIL-04`, VERIFIED.)

2. **The output AR loop empirically reaches period > 2.** Re-run this session of `util/ad-hoc/verify_ar_node_period_p5.py`: a single **additive** sign node of order 1 has max period exactly **2** (PASS — reproduces Giles/Fahlman); a single additive sign node of order D under constant exogenous drive has max observed period **4, 6, 8, 16, 16** for D = 2, 3, 4, 5, 6 (period > 2 AND > D, all ≤ 2^D). (`P5-CEIL-01`, VERIFIED empirically.)

3. **Period > 2 ⇒ a cyclic group ⇒ non-star-free.** A period-k>1 orbit is a k-cycle permutation in the node's transition semigroup, generating the cyclic group **Z_k**. By the McNaughton-Papert counter-free test (*counter-free iff `q.u^n = q ⇒ q.u = q`*; a period-k>1 orbit violates it), the automaton is **non-counter-free = non-aperiodic = non-star-free = non-group-free** (using K&R's group-free=star-free coincidence). So **P5's deployed-asymptotic representational class strictly contains star-free** — it can express a **bounded modular (mod-k) counter**. (`P5-CEIL-01`: the empirical period > 2 is VERIFIED via the POC; the period-k orbit ⇒ non-aperiodic syntactic monoid ⇒ non-star-free step is INFERRED via Schützenberger 1965 / McNaughton-Papert 1971.)

   This **corrects** the first-pass under-statement (some angles confined any P5 break to parity/ℤ₂, the Thm-7 toggle). Order-D additive feedback **exceeds** mod-2, reaching bounded cyclic counting. Thm-7 (negative weight → toggle → parity) is the *order-1* lower bound on the same phenomenon; the order-D node simply does more.

4. **But NOT full regular — the structural ceiling on the lift.** Two independent facts cap it at the cyclic/abelian fragment:
   - **First-order additive, not second-order multiplicative.** K&R prove the only mechanism that implements an actual group is the **second-order (⊕=product) neuron** — and even that realizes only C₂ (Props 5/6). A single additive node `Σ_k v_k·y_o(t−k)` wrapped in one nonlinearity cannot manufacture multiplicative group structure regardless of depth D; **depth widens reachable PERIODS but not the algebra**: random search found periods 4,6,8,16,16 (a constructive lower bound, ≤ the 2^D pigeonhole ceiling), while the exponential 2^D−1 of a true XOR/LFSR register is out of additive reach — that is P2's second-order territory (§1.1). K&R themselves conjecture first-order sign/tanh *"are not able to capture an actual grouplike semiautomaton."* (`P5-CEIL-02`, VERIFIED structural bound.)
   - **Siloing blocks group composition.** Each output sees only its own past (no inter-output feedback), so even if one node realized a small cyclic group, there is **no mechanism to compose groups across outputs** into the larger/non-abelian groups full-regular needs. The outputs are parallel isolated AR loops, not a coupled group-implementing network. (K&R's all-regular result (Thm 6) is moreover for an RNN/*network*, not an RNC/*cascade*; P5 at the output is even more restricted than an RNC — siloed scalars.) (`P5-CEIL-05` structural argument, VERIFIED.)

5. **The NARX-universality crux — does feedback route THROUGH the hidden layer? NO, and that is decisive.** The single most misattribution-prone claim here is reading P5 as "NARX-flavored" and importing NARX Turing-equivalence. **Reject it.** Siegelmann-Horne-Giles get universality **precisely because** the fed-back outputs re-enter the full MLP Ψ and mix nonlinearly with the exogenous inputs across hidden units — their construction makes the **hidden neurons simulate the FSM states** while *"the output node is then simply the linear combination … so that the output of the network is equal to the value of the currently active hidden layer node"* (VERIFIED). P5 deliberately **removes exactly this enabling hypothesis**: the feedback `Σ_k v_{o,k}·y_o(t−k)` is a per-output scalar pre-activation term that (i) sees only that output's own past, (ii) does NOT route back through the hidden cascade (CODE-confirmed via the strictly lower-triangular fan-in `cascade_correlation.py:1945`, where `y_o` provably never re-enters any hidden unit), and (iii) never participates in multi-unit nonlinear mixing. With hard-limiting nonlinearity the SHG paper itself says output-only feedback yields only **Finite-Memory-Machines, "a subclass of FSMs"** — exactly where P5 lives. **P5 is a single nonlinear order-D AR node per output, dramatically weaker than NARX.** Claiming P5 inherits NARX power is the precise hallucination to guard against (the prior P4 round's "rotation matrix" misattribution class). (`P5-CEIL-03`, VERIFIED.)

6. **Giles-1995 period cap does NOT transfer to P5's order-D node.** Giles' "no state-cycle > 2 under constant input" is a property of a **single-state (order-1)** monotone self-recurrent unit; P5's order-D readout empirically reaches period-4 at D=2 already, so the period-2 cap does not bind it. And Giles/Kremer concern RCC's HIDDEN self-recurrent unit — P5's hidden path is pure FIR (no self-recurrence), so Giles is entirely silent on P5's hidden cascade. Giles-1995 is the order-1 *special case* / nearest cautionary precedent, **not** a hard cap on P5's order-D readout. (`P5-CEIL-07`, VERIFIED.)

7. **Conditionality flag (INFERRED, important).** P5's output activation `f` is unspecified, and the current solve is a **linear MSE regression readout** (`cascade_correlation.py:2018` `nn.MSELoss()`; `:1979` linear matmul). If `f` is identity/linear, the AR node is an **LTI filter with no parity/modular structure** — no asymptotic break, only a damped IIR decay tail (still a horizon win over P4). The cyclic-counting break materializes ONLY if the readout is made **saturating/sign-like** AND BPTT finds the toggling/oscillating regime. K&R Thm-7 makes parity *plausible* (a sign-unconstrained negative weight exists) but does **not** prove it for P5's specific linear-AR-into-a-readout construction — Thm 7's neuron is `sign(w·x+v)` with recurrence on the neuron's own STATE through the toggling sign, which is an **analogy, not a covering theorem** for P5. (`CEIL-3`, INFERRED, residual uncertainty.)

**Asymptotic verdict, stated precisely:** P5's representable class = **star-free ∪ {bounded cyclic / mod-k counting, period > 2 — ~2D-3D observed per additive node, ≤ 2^D representable}**, conditional on a saturating readout. It is a **partial break** of the star-free → bounded-periodic gap and a **no-break** of the bounded-periodic → full-regular gap. Under a pure-linear MSE readout it nullifies to **no-break** (LTI fading memory only).

### 3.3 The D≤30 windowed caveat (SEPARATE layer — does not collapse §3.2)

The ratified DEPLOYED architecture is **D ≤ window ≤ 30, STATELESS PER WINDOW** (the design "~35" figure is treated as ≤30; state — both hidden FIR registers and the output AR register — resets each window; NO carry-across-windows). This is the **hardest** of the three ceilings and dominates the deployed machine:

- A recursion that resets every ≤30 steps **unrolls the IIR to ≤30 lags** = a finite-window FIR-of-outputs object, finite-state.
- Therefore **any realizable counting PERIOD is capped at ≤ the window (≤30)**, and a **mod-k counter with k>30 is architecturally impossible** regardless of representability or learnability.
- This mirrors Fahlman's original RCC, which zeroes internal state at the start of each string (*"The internal state of the network is zeroed at the start of each string"*, `NIPS-1990` p.191, VERIFIED) — the exact analog.
- **T=1 reduces P5 to today's feed-forward cascor exactly** (the AR loop has no past at a single step), preserving subsumption. (INFERRED for the AR loop specifically — must be coded so `y_o(t−k)` is empty/zero at T=1, not assumed.)

(`P5-CEIL-05`, VERIFIED from the ratified spec.)

### 3.4 The learnability gate (third axis — strictly below representability)

Even where mod-k is representable, **BPTT is unlikely to find or maintain it:**

- BPTT over the ≤30-step window on a single saturating AR loop is the classic **vanishing/exploding-gradient** regime (Bengio et al. 1994, cited inside K&R's own bibliography).
- A persistent period-k limit cycle requires the AR feedback poles at **marginal stability |λ|≈1** — which is **exactly** the gradient knife-edge. The marginal-stability ↔ vanishing-gradient coupling is standard (Bengio et al. 1994; Pascanu, Mikolov & Bengio 2013, *On the difficulty of training RNNs*, ICML, arXiv:1211.5063; Ribeiro et al. 2020, *Beyond exploding and vanishing gradients*, AISTATS PMLR 108:2370-2380 — learning attractors and gradient-vanishing are governed by the same condition).
- MSE gives **no pressure toward a cycle** unless the target sequence literally demands exact modular counting (rare in regression/equities). So gradient descent on free `v_{o,k}` is biased toward **contractive fading-memory** (|λ|<1) solutions where gradients behave.

**Consequence:** the TRAINABLE ceiling collapses back toward aperiodic/fading-memory (effectively star-free); the representational counting lift is **largely unreachable/unmaintainable**. P5's genuine, robust gain over P4 is the **fading-memory decay tail** at the readout, NOT reliable modular counting. (`P5-CEIL-06`, INFERRED from verified gradient/dynamics literature.)

### 3.5 How P5 compares to P1 / P2 / P4 on the ceiling (synthesis)

- **P5 > P4.** P4 is pure FIR — a finite threshold window that can only ask "did X happen within the last D steps" (threshold counting, which counter-free automata already do) and provably cannot count modulo anything; it INHERITS the ceiling and is the WEAKEST. P5 adds the one thing the FIR/IIR litmus says converts FIR→recurrence (feedback on past outputs), and that empirically buys a bounded mod-k counter. This is the decisive P5-vs-P4 delta.
- **P5 ≈ relocated + deepened P1.** Same mechanism class (a trained nonlinear scalar self-loop, structurally RCC's `V(t)=σ(…+V(t−1)w_s)`, Giles-1995 territory). P1 is order-1 (period ≤ 2, parity/ℤ₂) on HIDDEN candidates (correlation-trained, frozen — recurrence stays in the discardable candidate phase, output retrain stays static). P5 is order-D (period > 2, bounded mod-k) on the PERMANENT OUTPUT path (BPTT-trained). P5 buys mod-k over ℤ₂ but forfeits cascor's output-stays-static / monotone-improvement guarantee (see §6).
- **P5 < P2.** P2's second-order multiplicative group units are the ONLY mechanism that reaches arbitrary groups / full regular; P5's first-order additive loop provably cannot compose groups. But P5 is FAR more trainable (P2 has no constructive recipe).
- **P3 is orthogonal.** P3 has genuine fading/continuous state in the *feature* path and the best Δt story, but INHERITS the ceiling (the corpus-corrected category error: fading memory ≠ counting). P5 actually *leaves* star-free (partially) where P3 does not.

**`breaks_partially` — AT MOST, conditional on a saturating readout, bounded to bounded-periodic, never full-regular; nullifies to `no_break` under a pure-linear MSE readout; and capped at period ≤30 by the deployed window.**

---

## 4. Functionality (Output-AR Fan-in + Hidden N+1-D)

All anchors VERIFIED by opening `juniper-cascor/src/cascade_correlation/cascade_correlation.py` this session.

### 4.1 Hidden N+1-D fan-in — byte-identical to P4

The single fan-in builder is `_compute_hidden_outputs` (CC:1921-1947). It pre-allocates a buffer of width `input_size + n_hidden` (CC:1940), writes raw inputs into the first `input_size` columns (CC:1942), then for each unit computes its activation over **only the columns to its left** (CC:1943-1946):

```python
col = self.input_size + i
unit_input = buffer[:, :col]
buffer[:, col] = unit["activation_fn"](torch.sum(unit_input * unit["weights"], dim=1) + unit["bias"])
```

This is the cascade triangular fan-in. **Both consumers read the same buffer:** the output layer via `output_input` (forward at CC:1971, matmul at CC:1979) and downstream candidates via `_prepare_candidate_input` (CC:2199, OPT-4 cache). P5's hidden lag taps FLATTEN into this exact buffer — `CC:1940-1946 must widen` the buffer from `input_size + n_hidden` to `input_size + Σ_i(1 + D_i)` (each delay-lined unit contributes 1 current + D_i lagged columns), and the per-unit loop must emit the activation plus its shift-register. Because both consumers read the same buffer, widening here automatically exposes taps to the readout and to later candidates "one cascade-layer late." The strict lower-triangularity (CC:1945) is why a unit can only see *earlier* units' taps — this is why the hidden layer stays FIR. (`F1` hidden half / `F6`, VERIFIED.)

### 4.2 The output-AR fan-in — the load-bearing functional break

Today the readout is **ONE static GEMM** with no time/feedback dimension:

```python
output = torch.matmul(output_input, self.output_weights) + self.output_bias   # CC:1979
```

with `output_weights` shaped `[input_size, output_size]` (CC:738) and `output_bias` shaped `[output_size]` (CC:739). P5's `y_o(t)=f(W_o·feats(t) + Σ_{k=1..D} v_{o,k}·y_o(t−k))` makes **row t depend on rows t−1..t−D of the SAME output**, destroying the matmul's row-independence. The forward must become a **per-window time-loop with a per-output ring buffer of the last D outputs** (genuine BPTT). (`F1`, VERIFIED `cascade_correlation.py:1979`.)

### 4.3 Quantified parameter / fan-in change

Two compounding widenings at the output (`F2`/`F3`/`F4`, VERIFIED shapes):

1. **Hidden-tap inflation of the design matrix.** `output_weights` rows grow from `input_size + n_hidden` (CC:1940) to `input_size + Σ_i(1 + D_i)` — at D=30, up to **~31× the hidden-column count**, multiplying the GEMM cost accordingly.
2. **Feedback parameters.** A NEW tensor `v` of shape **`[output_size, D]`** (diagonal/per-output — NOT `[output_size, output_size, D]`, since siloing means no cross-output coupling) adds exactly **`output_size · D`** parameters (≈ `+30·output_size` at D=30). The single `nn.Linear` (CC:2032) cannot hold `v`; a custom `nn.Module` exposing `(W_o, b_o, v)` is required, and the write-back (CC:2086-2091, today only `output_weights`/`output_bias`) must persist `v` or the recurrence silently vanishes.

The width-grow helper `_resize_output_layer_for_new_units` (CC:4051-4086) computes `new_input_size = prev_input_size + num_added` (CC:4079); under P5 it must become `prev_input_size + Σ(1 + D_i)_added`. (`F4`, VERIFIED.)

### 4.4 Worker payload — untouched by the recurrence

The AR loop stays server-side; only tap-widened (still 2-D) arrays cross the wire. (See §9.4.)

---

## 5. Recurrence Correctness — Q1 (the FIR + IIR Hybrid)

### 5.1 The output layer IS genuine IIR recurrence (flips P4's NEGATIVE)

Unlike P4 (pure FIR everywhere), P5 adds a true feedback loop at the output node. This satisfies the formal recurrence litmus the corpus itself defines: **IIR means recursion on past OUTPUTS, and the response persists beyond any finite window** (VERIFIED-SECONDARY, dsprelated.com: *"The IIR filter feeds back a copy of the output from the delay element … creating a recursive filter"*). The corpus P4 verdict states the converse rule that resolves this directly: *"NARX also uses tapped delay lines, but because it taps fed-back outputs, it crosses into genuine recurrence/IIR … the feedback does [make it recurrent]"* (P4 §4.6, VERIFIED). P5 supplies exactly that feedback. **Today's code has NO such term** — the forward readout is a single static matmul (`cascade_correlation.py:1979`, VERIFIED). So on the Q1 axis, P5 is categorically distinct from P4: **P5 flips P4's flat NEGATIVE recurrence verdict to AFFIRMATIVE, but only at the readout.** (`Q1-1`, VERIFIED.)

### 5.2 The hidden half is NOT recurrence — P5 is a HYBRID, not a recurrent network

P5's hidden layer is exactly P4: depth-D delay-lines on each frozen unit's output, taps flattened into the fan-in, NO feedback into any hidden node's own activation. The cascade is strictly lower-triangular (`cascade_correlation.py:1945`), so a unit reads earlier units' taps but never its own or later ones — this is precisely why the hidden layer stays feed-forward. The hidden forward is state-free, one column per unit (`cascade_correlation.py:1943-1946`). The correct Q1 characterization is therefore a **HYBRID: FIR exogenous feature cascade + IIR autoregressive readout** — NOT a recurrent network in the Elman/RCC sense (no recurrence in feature extraction). **All stateful/long-memory capacity lives solely in the output IIR loop.** Calling P5 "a recurrent cascor" without the "at the readout only" qualifier overstates it. (`Q1-4`, VERIFIED.)

### 5.3 The recurrence is SILOED — strictly weaker than NARX/Jordan

P5's feedback is confined to a per-output scalar AR loop (each `y_o` sees only its OWN past) and explicitly does NOT route through the hidden cascade. This makes P5 NARX/Jordan-**flavored** but strictly weaker than either:

- **vs NARX (Siegelmann-Horne-Giles 1997, VERIFIED-PRIMARY):** in true NARX the fed-back outputs re-enter the FULL MLP Ψ and mix nonlinearly with inputs across hidden units — that mixing is the enabling hypothesis for Turing-equivalence. P5 removes it.
- **vs Jordan (1986, VERIFIED-SECONDARY):** a true Jordan net routes output feedback INTO the hidden layer via context units (*"recurrent connections from the network output to its hidden units via a 'memory unit'"*). P5 bypasses the hidden layer entirely. (Note Jordan's classic memory unit is a *decaying running average* of past outputs — a specific exponential/IIR kernel — whereas P5 uses *independent learnable taps* `v_k`, a more general order-D IIR loop.)

**Any claim that P5 inherits NARX or Jordan expressivity is a misattribution.** (`Q1-2`, VERIFIED; refuted-count 1 and survived.)

### 5.4 Two correctness caveats bounding effectiveness (considered)

(See §18 for the full "considered" treatment of `Q1-3`/`Q1-5`.) Briefly: (1) IIR is **not inherently stable** — BPTT must find stable `v_{o,k}` poles (the hidden FIR half has no such risk); (2) the **D≤30 stateless-per-window reset collapses the deployed object back to finite-window FIR-of-outputs** (representability = genuine IIR; deployed = ≤30-lag). Both layers of the answer must be kept.

**Q1 verdict:** P5 contains **genuine recurrence (the output IIR loop passes the feedback test)** — materially stronger than P4's flat NEGATIVE — but qualified: it is hybrid (hidden stays FIR), siloed (weaker than NARX/Jordan), and the deployed object is finite-window.

---

## 6. Coherence with Grow / Freeze / Retrain

P5 is **coherent with the constructive SCAFFOLD but incoherent in the RETRAIN STEP's mathematical character and in the selection-criterion/readout pairing.** All anchors re-opened this session.

### 6.1 The scaffold is preserved (coherent)

The growth ordering — initial `train_output_layer(x_train, y_train, max_epochs)` (CC:1875) → `grow_network` (CC:1903) → per-iteration `train_candidates` (CC:4595) → `_add_best_candidate` (`add_unit` CC:4622, `_retrain_output_layer` CC:4624) — is structurally preserved. Candidate training is genuinely unchanged (the P4 property): the instantaneous, order-invariant Pearson correlation (`candidate_unit.py:935-936` flatten + `:941` `torch.dot`) and the state-free candidate forward (`candidate_unit.py:479`). Hidden freeze is untouched and structural: units are plain detached dict tensors `{weights, bias, activation_fn, correlation}` (CC:4032-4037), read-only in `_compute_hidden_outputs` (CC:1946) and never in the output optimizer's param set (CC:2041 passes only `output_layer.parameters()`); install is install-only (CC:4014-4018). The install/resize separation cleanly isolates the AR change to `train_output_layer`. **T=1 subsumption holds.** (`P5-COH-06`, VERIFIED.)

### 6.2 Three coherence breaks (the incoherent part)

1. **Selection criterion is BLIND to the recurrence it now feeds (`P5-COH-01`, VERIFIED).** A hidden unit is chosen to maximize the *instantaneous* correlation between its scalar activation and the *current* residual (`candidate_unit.py:941`, a single scalar covariance over the shuffled batch, no time axis). But the readout that consumes it is now autoregressive. A unit whose value is only realizable through the AR feedback (e.g., one that helps track a decaying mode) is invisible to, and can be rejected by, the selector. This is a **deepened** P4 defect: P4 gave a unit a temporal apparatus its objective never evaluated; P5 additionally makes the *consumer* recurrent.

2. **CONVEXITY LOSS (`P5-COH-02`, INFERRED).** Today's per-round re-solve is a single linear layer + MSE over a *frozen* design matrix (CC:2032/CC:2018/CC:2066-2076) — **convex**, re-run from scratch every round (CC:4624) with reliable monotone improvement, so re-seeding from prior weights (CC:2033-2037) reliably reaches the (essentially unique) optimum for the widened basis. P5 replaces the body (CC:2067) with **non-convex BPTT** over `Σ_k v·y_o(t−k)`. Re-running a non-convex BPTT from scratch each growth round (a) forfeits the convex monotone-improvement property that justifies cascor's "install then re-fit output" step, (b) can move the readout to a *worse* local optimum after a unit is added (the guarantee that "adding a unit cannot hurt the output" is no longer assured), and (c) makes each step depend on `v`-init and BPTT noise.

3. **TRACTABILITY INVERSION (`P5-COH-03`, VERIFIED).** The corpus repeatedly grounds cascor's advantage as: *"with all hidden units frozen and outputs NOT fed back, output-layer training stays STATIC … Live recurrence exists only in candidate training"* (PROPOSALS §5/§7.1). **P5 deliberately violates the "outputs not fed back" precondition**, moving live recurrence INTO the permanent output path — the exact thing cascor was architected to avoid. P4 kept BOTH candidate AND output training static (its headline edge); **P5 keeps candidate training static (inherited) but makes OUTPUT training recurrent (BPTT).**

### 6.3 Concrete code-level break: CR-060 hoist partially invalidated

The CR-060 optimization hoists `output_input = self._compute_hidden_outputs(x)` ONCE above the epoch loop (CC:2047-2051, comment: *"Hidden unit weights are frozen during output training, so their outputs are constant across epochs"*) because there is no feedback today. Under P5 it survives only for the **exogenous half** (the siloed design keeps hidden FIR features exogenous, hidden weights still frozen); the **AR contribution `Σ_k v·y_o(t−k)` is NOT hoistable** — it changes every backward pass as `v` updates (CC:2076) and must be recomputed by unrolling the window each epoch. So the single hoisted GEMM body (CC:2067) must split into (hoisted exogenous projection) + (per-epoch, per-timestep AR unroll). The cheapest part of the constructive loop becomes the most expensive. (`P5-COH-05`/`F5`, VERIFIED.)

**Coherence verdict:** P5 is a **coherent retrofit of the constructive scaffold** and an **incoherent retrofit of the retrain step's character**. The defect is *sticky*: aligning the selector to the recurrent readout would require a recurrence-aware candidate objective (BPTT-in-candidate-training) — the exact cost P5 exists to avoid. Acceptability hinges on the representability/learnability question (§3), not the scaffold.

---

## 7. Irregular-Δt — Q2

**Verdict: the recurrent output layer does NOT make P5 Δt-aware.**

### 7.1 The output AR loop is sample-position-indexed, not elapsed-time-indexed

Both the hidden FIR registers AND the new output AR delay-line index by integer SAMPLE POSITION (lag k), not elapsed time — there is **no Δt term anywhere** in `y_o(t)=f(W_o·[...](t)+Σ_{k=1..D} v_{o,k}·y_o(t−k))`. The fed-back `y_o(t−1)` is "one sample ago," never "one calendar day ago." A Fri→Mon 3-day gap advances the AR loop by exactly one tap, identical to a 1-day gap. This is verified against the live windowing code: `juniper-data/juniper_data/generators/_sequence.py:106` windows by row index (`for i in range(lookback - 1, n - 1)`), and `:113-116` carries `dt` as a **separate feature** via `np.diff` of date ordinals (`dt[0]=0.0; dt[1:]=np.diff(win_ords)  # calendar-day gaps`), never to advance state. The static-readout baseline (`cascade_correlation.py:1979`) has no time axis today. (`Q2-1`, VERIFIED.)

### 7.2 Only Approach A applies; B/C structurally inapplicable

The Δt-note taxonomy maps onto P5 exactly as onto P4:

- **Approach A (Δt-as-feature / Time2Vec):** the ONLY remedy P5 can use — the per-step `dt` vector feeds in through `W_o`'s exogenous fan-in like any other feature.
- **Approach B (time-gated RNNs / GRU-D decay):** inapplicable — P5's AR taps `v_{o,k}` multiply `y_o(t−k)` by a *constant* weight regardless of elapsed time; there is no continuous hidden state to decay-toward-baseline as `f(Δt)`.
- **Approach C (Neural-ODE / LMU continuous-time integration):** inapplicable — P5's feedback is a discrete per-tap register advanced once per sample, not a dynamical state integrated forward by Δt. (The LMU reference `util/ad-hoc/verify_delta_t_reference_code.py:31-60` is a feed-forward linear state-space readout of an *exogenous* input `u`; it is NOT autoregressive on its own output and is unrelated to a discrete AR register.)

(`Q2-2`, VERIFIED; refuted-count 1 and survived.)

### 7.3 The one genuine improvement over P4 (INFERRED, narrow)

Because the output node now has an IIR self-loop, a **fed Δt feature can be INTEGRATED/accumulated across the window** — a Δt feature entering at step t−k influences `y_o(t−k)`, which feeds back into `y_o(t)` via `v_{o,k}`, so the readout can learn a recursive function that approximates a fixed-coefficient GRU-D-like decay over elapsed time. P4's static least-squares readout (CC:2047-2076) can only combine a Δt feature *instantaneously*. So **P5 improves Δt-feature INTEGRATION, not Δt-AWARENESS** — and the improvement is hard-capped by the stateless-per-window D≤30 reset (any accumulated time quantity zeroes at each window boundary). (`Q2-3`, INFERRED — the key Q2 inference, moderate confidence; see §18.)

**Δt stays ORTHOGONAL to the ceiling** (Δt-note §1.6/§4.5: two distinct limits, "when" vs "what"), so Q2 is answered independently of §3. T=1 subsumption is consistent (a single-step window has no AR past). Net: **no better than P4 on Δt-awareness; far behind P3** (the only proposal with native B/C support).

---

## 8. Effective Horizon — Q3 (Output IIR vs Hidden FIR Cap; Three Dataset Classes)

### 8.1 Headline: IIR fading memory replaces P4's hard FIR cliff

P5's effective horizon AT THE READOUT is qualitatively different from P4. P4 is FIR — its response is identically zero after D steps (a hard memory cliff). P5's output node is IIR — its impulse response **decays-but-is-nonzero**, carrying information many steps beyond D. This is the textbook FIR-vs-IIR memory-depth tradeoff (VERIFIED-SECONDARY, dsprelated.com: *"The TDNN model has high memory resolution but low memory depth, whereas the [recurrent] models have low memory resolution but high memory depth"*). Today's readout is a single static matmul with NO feedback (`cascade_correlation.py:1979`), and the CR-060 hoist (CC:2051) is valid *only because* there is no output recurrence. P5 inverts this. (`Q3-1`, VERIFIED structure; INFERRED tail; refuted-count 1 and survived.)

### 8.2 Asymmetry: hidden path stays FIR-capped at D; only the readout gains long memory

The HIDDEN layer remains pure FIR (P4 property): each frozen unit emits a scalar instantaneous activation (`cascade_correlation.py:1946`) and its delay-line is a finite shift register of its last D activations with no feedback. So the hidden cascade's memory is HARD-CAPPED at D≤30 with a cliff, and information older than D steps is structurally unavailable to any hidden unit or any later candidate (which reads only earlier taps via the lower-triangular fan-in `cascade_correlation.py:1945`). **The long-memory capacity lives ENTIRELY in the output IIR loop.** Consequence — the NARX-vs-recurrent split: P5 carries a long-decaying trace of the **readout TARGET's own past (autoregressive)** but **cannot carry a feature/exogenous trace older than D** (those were only ever windowed FIR). (`Q3-2`, VERIFIED; refuted-count 1 and survived.)

### 8.3 Horizon is sample-count, NOT real-time

Both layers index by sample position, so the effective horizon is a count of samples (≤D hidden, ≤window readout), not wall-clock/calendar time. Under irregular Δt, "30 lags back" could span 30 calendar days, 30 trading sessions (≈6 weeks), or many months depending on sampling density — the realized real-time horizon **varies with the local sampling rate and is uncontrolled**. Only Approach A gives the network any signal about how much real time a lag represents, and even then `v_{o,k}` is tied to discrete sample lags. The IIR loop lengthens the SAMPLE-COUNT horizon but does nothing to make it a TIME horizon. (`Q3-4`, VERIFIED; Δt-orthogonality per Δt-note §4.5.)

### 8.4 Two hard bounds (considered in §18): window reset + IIR stability

- **`Q3-3` (window reset, the binding deployed ceiling):** the IIR loop is unrolled to ≤30 lags per window and re-zeroed at each boundary, so the **deployed horizon = min(unconstrained IIR decay length, window length ≤30)**. Across windows both P4 and P5 have the SAME zero horizon; P5's win is only WITHIN a window (smooth decay beats P4's mid-window cliff at lag D).
- **`Q3-5` (IIR stability ↔ learnability):** the maximum stable horizon is achieved only near pole-magnitude-1, which is exactly where BPTT gradients vanish/explode — coupling horizon to learnability. P4 had no such tension (FIR is unconditionally stable, trivially trained).

### 8.5 Per dataset class (`Q3-6`, INFERRED application of verified mechanics)

- **Regular time-series (uniform Δt):** modest within-window gain (smooth fading memory vs P4's lag-D cliff); capped at ≤30; across-window dependencies invisible to both.
- **Irregular-Δt:** UNRELIABLE — sample-count ≠ time; the AR decay is in sample steps, so the realized time-horizon fluctuates with sampling density; needs Δt-as-feature to be even interpretable, and the loop still cannot represent "when."
- **Equities (daily OHLCV, the WS-1 `equities_seq` generator):** BEST-matched — next-close regression *is* an autoregressive problem on the target, so feeding `y_o(t−k)` back is exactly the AR(D) structure momentum/mean-reversion needs WITHIN a window; the windowing emits per-step calendar `dt` and a positive `target_dt` horizon (`_sequence.py:113-123`) so Approach-A features are available. BUT the ≤30-window stateless reset caps lookback at **~30 trading sessions (≈6 weeks)**, leaving month/quarter regime memory unreachable.

**Q3 verdict:** longer effective *readout* memory than P4 (genuine fading-memory tail), shorter/less-controllable than P1/P2/P3 (whose memory is in the feature path), Δt-blind, and hard-capped at ≤30 by the deployed window.

---

## 9. Mini-batch — Q4 (Output BPTT, Loses P4's Static Solve)

### 9.1 Within-window order becomes sacred at the readout

P5's output recurrence forces the output-training loop to process timesteps in temporal order within each window, eliminating P4's free shuffleability of output-training rows. The exact line that breaks is **CC:2067** (`output = output_layer(output_input)`): today a single GEMM over a `(batch, features)` design matrix whose rows carry no ordering semantics (so the static solve can flatten (B,T)→(B·T) and shuffle freely). P5's AR dependence makes the loop a time-stepped recurrence carrying a per-output ring buffer of the last D outputs (BPTT-over-window). The window/batch axis stays shuffleable (stateless-per-window, h₀=0, no carry-across-windows), but within-window step order is now load-bearing for the OUTPUT path. **This is the single largest Q4 delta:** P4 kept BOTH candidate AND output training as order-free static solves; P5 keeps candidate training order-free (P4 property, via untouched `candidate_unit.py:479`/`:935-957`) but makes OUTPUT training order-sacred. (`Q4-1`, VERIFIED.)

### 9.2 CR-060 hoist invalidated for the AR contribution → per-round cost balloons

Under P5 the exogenous feature matrix is still epoch-invariant (hoistable once), but `Σ_k v_{o,k}·y_o(t−k)` must be re-unrolled every epoch. So per-install output-training cost changes from today's `E` forward GEMMs over a static matrix (full batch parallelism, `O(E·B·F)`) to **`E` epochs × T-step sequential unroll × BPTT backward** (`O(E · n_windows · T · (F+D))` with a SEQUENTIAL inner T-loop — timesteps cannot be parallelized because `y_o(t)` needs `y_o(t−1)`). With one such retrain after EVERY hidden install (the growth loop calls `_retrain_output_layer` per unit, CC:4624), the cumulative cost is `#units × E × T-step BPTT`, landing entirely on the single-process server. (`Q4-2`, VERIFIED.)

### 9.3 New 3-D, time-ordered, padded+masked loader for the output path

Today `train_output_layer` receives 2-D `(samples, features)` (CC:2021 `input_size = x.shape[1]`; the only shape contract beyond the batch-size check at CC:2014-2015) and masks columns via `active_output_dim` (CC:2062-2071) but never rows/time. P5 requires the ratified 3-D contract: `X (n_windows, T_max≤30, F)` + `seq_lengths` + `readout_mask` + dense `y`, with partial fills (valid length < D) zero-padded and the mask preventing padded steps from contributing to the loss or polluting the AR state. Within-window order must be preserved on load; the `n_windows` axis is freely shuffleable. cascor's POC data path delivers strictly 2-D tensors (`data_provider.py:200-205` asserts `ndim != 2 → error`), so the windowing/padding/masking machinery — which exists today only as a juniper-data DATA contract in `_sequence.py`, NOT consumed by any cascor training path — must be wired into the output trainer. The candidate/hidden loader is UNAFFECTED. (`Q4-3`, VERIFIED.)

### 9.4 Worker 3-D payload — the recurrence never crosses the wire

The output BPTT solve runs ONLY on the server (`train_output_layer`, CC:1986-2106, single-process; the fit growth loop calls `_retrain_output_layer` in-process), and the distributed workers exclusively run candidate correlation-training (`task_executor.py:114-120` calls only `candidate.train_detailed`). Therefore the recurrence and its window-batched 3-D output tensors **NEVER cross the worker wire**, and the hard `ndim > 2` reject in `SharedTrainingMemory` (`cascade_correlation.py:272-273`: *"SharedTrainingMemory only supports tensors up to 2 dimensions"*) is **NOT on the critical path** for the output BPTT. This is a real Q4 relief specific to P5's siloed-server-side design. Caveat (inherited from the P4 hidden half, not new): the hidden-FIR tap widening grows `candidate_input` WIDTH (still 2-D, transparent to the worker), and any future attempt to ship 3-D windowed tensors to workers would hit CC:272-273. **The worker payload schema is UNCHANGED by P5's recurrence.** (`Q4-5`, VERIFIED.)

### 9.5 Stateless-per-window makes window mini-batching tractable

The ratified STATELESS-PER-WINDOW rule (state resets each window, h₀=0, no carry-across-windows) is what makes standard mini-batch SGD tractable: the `n_windows` axis is i.i.d.-shuffleable and partitions into mini-batches with **no truncated-BPTT bookkeeping, no hidden-state handoff, no sequence-length-vs-batch coupling** beyond per-window padding. The BPTT graph is fully contained within each window; gradients average across windows exactly as today's MSE averages across the flat batch (CC:2071). Vectorizing across windows-in-a-batch is straightforward; vectorizing across TIMESTEPS within a window is NOT (the AR recurrence serializes the T-loop). (`Q4-6`, INFERRED standard-RNN-fact applied to the ratified constraint; refuted-count 1 and survived.)

### 9.6 IIR introduces a training-stability risk class absent from P4

P4's output is FIR (unconditionally stable). P5's is IIR — BPTT over the ≤30 unroll is exposed to vanishing/exploding gradients (Bengio 1994), and the AR poles can place the loop near instability. The saturating `f` keeps it bounded but flattens gradients. The stateless-per-window reset bounds the *deployed* blow-up to ≤30 steps (no unbounded IIR divergence at inference), but the per-epoch recurrent gradient instability is real. None of this exists in the current static solve, where every epoch is one independent GEMM (CC:2067) with a trivially well-conditioned single-layer gradient. (`Q4-4`, VERIFIED today's single-layer backward CC:2073-2076; INFERRED order-D dynamics.)

**Q4 verdict:** heavier than P4 on the OUTPUT path (sequential T-loop + BPTT + invalidated hoist + new 3-D loader + new optimized `v` tensor), but LIGHTER than full stateful-RNN mini-batching (stateless-per-window removes all cross-window/truncated-BPTT state handoff); candidate/hidden mini-batching stays P4-light. T=1 subsumes to today's static solve (AR sum empty → single GEMM).

---

## 10. Strengths

1. **Genuine recurrence at the readout (Q1 AFFIRMATIVE).** Unlike P4's flat NEGATIVE, P5's output IIR loop passes the formal feedback litmus — it is real recurrence, the corpus's own FIR→recurrence converter. (`Q1-1`, VERIFIED.)
2. **A real, if bounded, representational lift off star-free.** Empirically reaches bounded cyclic/mod-k counting (period 4..16 for D 2..6), exceeding P4's threshold-only counting and P1's/Thm-7's mod-2. (`P5-CEIL-01`, VERIFIED empirically.)
3. **A fading-memory horizon tail.** Replaces P4's hard FIR cliff at the readout — the robust, deployable Q3 gain (vs the mostly-theoretical counting lift). (`Q3-1`, VERIFIED structure.)
4. **Candidate training and the distributed worker substrate stay byte-untouched.** The recurrence is server-side only; the `ndim ≤ 2` worker cap is never on the critical path; only tap-widened 2-D arrays cross the wire. (`Q4-5`, VERIFIED.)
5. **The constructive scaffold and T=1 subsumption are preserved.** Grow/freeze ordering, hidden freeze, install/resize separation all carry over; T=1 reduces to today's cascor exactly. (`P5-COH-06`, VERIFIED.)
6. **C1-clean in principle.** The output BPTT-over-window reuses cascor's existing autograd path; the AR loop is an explicit Σ-of-taps + one nonlinearity (no library black box). (INFERRED from corpus §7.1.)
7. **Δt-feature integration improves over P4** (a fed Δt feature can be accumulated across the window via the loop). Narrow but genuine. (`Q2-3`, INFERRED.)

---

## 11. Weaknesses

1. **The representational counting lift is mostly GRADIENT-UNREACHABLE.** Mod-k requires AR poles at marginal stability |λ|≈1 = the vanishing-gradient knife-edge; MSE biases BPTT toward contractive no-count solutions. The headline "breaks star-free" is largely theoretical in deployment. (`P5-CEIL-06`, INFERRED.)
2. **Hard-capped at period ≤30 by the deployed window.** The stateless-per-window reset makes mod-k for k>30 architecturally impossible regardless of representability. (`P5-CEIL-05`, VERIFIED.)
3. **NOT full regular, and provably so.** First-order additive loop cannot compose the multiplicative groups full-regular needs; siloing blocks cross-output composition. (`P5-CEIL-02`/`P5-CEIL-05`, VERIFIED structural.)
4. **NOT Δt-aware** (Q2). The AR loop is sample-indexed; a 3-day gap ≡ a 1-day gap; only Approach A applies; far behind P3. (`Q2-1`/`Q2-2`, VERIFIED.)
5. **Exogenous memory still FIR-capped at D** (Q3). Only the target's autoregressive component gets long memory; feature memory cliffs at D. (`Q3-2`, VERIFIED.)
6. **Inverts cascor's output-stays-static tractability invariant** (coherence). Non-convex BPTT re-solve every growth round, forfeiting monotone-improvement. (`P5-COH-02`/`P5-COH-03`, VERIFIED/INFERRED.)
7. **Selection criterion mismatched to the recurrent readout** (a deepened P4 defect; sticky — fixing it requires the BPTT-in-candidate-training cost P5 exists to avoid). (`P5-COH-01`, VERIFIED.)
8. **NEW IIR-instability surface** that cascor has zero infrastructure for (see §12). (`F4`/`Q4-4`, VERIFIED.)
9. **Heaviest integration cost among the cascor-faithful options** (P1/P4/P5): P4's full hidden change-surface PLUS the primary output-layer rewrite (see §13). (`F1`-`F6`, VERIFIED.)

---

## 12. Risks + Guardrails (incl. Output-Feedback STABILITY)

| Risk | Severity | Guardrail |
|---|---|---|
| **IIR divergence / limit-cycle at training time.** Order-D AR loop wrapped in a saturating `f` can fixed-point, oscillate, or period-double; BPTT over the unroll exposes vanishing/exploding gradients. cascor has **ZERO gradient-clipping and ZERO pole/stability infrastructure today** (grep over `cascade_correlation.py` for `clip_grad`/`gradient_clip`/`torch.nn.utils.clip` returned no matches this session; the optimizer factory CC:3076-3229 is a bare constructor map). | HIGH (training) | Add training-time **gradient clipping** in the BPTT loop AND a **`v`-stability constraint** (spectral-radius cap / pole-magnitude projection / weight projection). Net-new code with no current hook. (`F4`, VERIFIED.) |
| **Recurrence silently vanishes on save/restore.** Today only `output_weights`/`output_bias` are persisted (write-back CC:2086-2091; snapshot `params/output_layer` SER:394-404). | HIGH (correctness) | Persist `v[output_size,D]` in write-back AND in the snapshot schema (new dataset under `params/output_layer` + checksum), plus per-unit `D_i` (new attr in each `unit_{i}` group). Add a round-trip test asserting `v` and `D_i` survive save→load. (`F3`, VERIFIED gap.) |
| **Counting lift advertised but unreachable.** The mod-k representability is real but BPTT won't find/maintain it; over-claiming "breaks star-free" risks designing tests for behavior the deployed system won't show. | MEDIUM | Keep the three axes separate in all reporting; add a **parity/mod-k probe test** (small synthetic) that PASSES only if BPTT actually finds a stable cycle — expect it to FAIL on regression targets, confirming the gap. |
| **Deployed period > window silently impossible.** | MEDIUM | Assert at config time that any target requiring period-k counting has `k ≤ window`; warn otherwise. |
| **Non-convex re-solve regresses the readout after a good install.** | MEDIUM | Keep a **best-so-far output checkpoint**; if a post-install BPTT re-solve worsens validation loss vs the pre-install readout, roll back (restores the monotone-improvement guarantee operationally). |
| **T=1 back-compat drift.** The AR loop must be empty/zero at a single step to stay byte-identical to 2-D cascor. | MEDIUM | Code `y_o(t−k)` as zero/empty at T=1 and add a **byte-identity test** vs today's static solve on a 2-D fixture (do not assume). (`P5-COH-06`, INFERRED.) |

---

## 13. Integration Challenges per Touch-Point (file:line)

All anchors VERIFIED by opening `juniper-cascor/src/cascade_correlation/cascade_correlation.py` (and `snapshot_serializer.py` / `task_executor.py`) this session unless flagged.

| Touch-point | file:line | Change | Cost |
|---|---|---|---|
| **THE PRIMARY REWRITE: static solve → BPTT** | `cascade_correlation.py:1986-2106`; breaking line **`:2067`** (`output = output_layer(output_input)`) | Convert the epoch body (CC:2066-2076) into a time-stepped recurrence over the ≤30-step window carrying a per-output ring buffer of the last D outputs = genuine BPTT. **The single load-bearing change.** | HIGH |
| Inference forward (static matmul) | `:1979` (`torch.matmul(output_input, self.output_weights)+self.output_bias`) | Must also become a recurrent, time-stepped free-running forward at deployment. | HIGH |
| New feedback tensor | `nn.Linear` rebuild `:2032`, seed `:2033-2037`, optimizer `:2041`, write-back **`:2086-2091`** | `nn.Linear` no longer captures the model — replace with a custom `nn.Module` exposing `(W_o, b_o, v[output_size,D])`; thread `v` through seed/optimize/write-back or it is dropped. | HIGH |
| CR-060 hoist | `:2047-2051` | Split: hoist the exogenous projection once; recompute the AR term per epoch by unrolling. | MEDIUM |
| Fan-in buffer (hidden FIR taps) | `:1940-1946` | Widen buffer to `input_size + Σ_i(1+D_i)`; emit a shift-register per delay-lined unit. | MEDIUM |
| Output-layer width re-derived independently | `:2021-2024` | Easy-to-miss site; must absorb +Σ(1+D_i) hidden taps. | MEDIUM |
| Output resize arithmetic | `:4051-4086`, width math `:4079` | `new_input_size = prev_input_size + Σ(1+D_i)_added`. | MEDIUM |
| Install / 4-key frozen dict | `:4032-4037` (install-only contract `:4014-4018`) | Add a `lag_depth` (`D_i`) descriptor for the hidden unit; `v` needs a new home (NOT a hidden-unit field). | LOW |
| RC-5 stale-candidate guard | `:4117-4124` | Trips after the first D>1 install unless candidate input-sizing resyncs (P4 §12 T10). | LOW |
| Stability infra (net-new) | optimizer factory `:3076-3229` (no clip/pole hook) | Add gradient clipping + `v`-stability constraint. | MEDIUM |
| Snapshot schema | `snapshot_serializer.py:381-425` (output), `:439-486` (units) | Persist `v` (+ checksum) and per-unit `D_i` or they vanish on round-trip. | MEDIUM |
| 2-D input validator | `:1632-1633` (`len(x.shape) != 2` hard-raise) | Forces the lag axis to be a feature-column flatten (hidden half). | LOW |
| Worker payload | `task_executor.py:50-167` (contract `:60-67`) | **UNCHANGED** — recurrence stays server-side; only tap-widened 2-D arrays cross the wire. | NONE (relief) |

**Bit-identity sensitivity:** the resize helper docstring (CC:4065-4069) flags bit-identity test sensitivity — the hidden-FIR widening edits must preserve it.

---

## 14. Performance Bottlenecks (per-round BPTT cost)

- **Dominant new cost:** per-install output retraining rises from `E` vectorized GEMMs (`O(E·B·F)`, full batch parallelism) to `E` epochs × **sequential T-step unroll** × BPTT backward (`O(E · n_windows · T · (F+D))`). The inner T-loop is serial (`y_o(t)` needs `y_o(t−1)`), so it does not vectorize. (`Q4-2`, VERIFIED.)
- **Multiplied by growth:** one retrain after EVERY hidden install (CC:4624), up to `max_hidden_units` times → cumulative `#units × E × T-step BPTT`. All on the single-process server (`train_output_layer` is server-only). (`F5`, VERIFIED.)
- **Activation memory:** the BPTT graph stores the unrolled `T`-step activations for the AR term → ~×T activation memory for the output graph vs today's single-layer backward. (`F5`/`Q4-4`, VERIFIED.)
- **GEMM widening:** the design matrix itself widens to `input_size + Σ(1+D_i)` (up to ~31× the hidden-column count at D=30), so even the hoisted exogenous projection costs more per epoch. (`F3`, VERIFIED.)
- **What stays cheap:** candidate-pool training and the distributed worker path are untouched (P4-light, 2-D). (`Q4-5`, VERIFIED.)

---

## 15. Dataset Constraints

- **ADDITIVE-ONLY data contract; X.ndim dispatch.** 2-D legacy path byte-identical; 3-D contract `X (n_windows, T_max≤30, F)` + `seq_lengths` + `readout_mask` + dense `y` + `scaling` + `task_type` + optional `dt`/`target_dt`/`observed_mask`/`padding_mask` (Δt-note §6.1; PROPOSALS §7.2). (VERIFIED corpus.)
- **D ≤ window ≤ 30**, partial fills (valid length < D) zero-padded; "~35" treated as ≤30. (VERIFIED ratified.)
- **STATELESS PER WINDOW** — both hidden FIR registers AND the output AR register reset per window; no carry-across-windows; batch axis fully shuffleable. (VERIFIED ratified.)
- **The 3-D windowing exists only as a juniper-data DATA contract** (`_sequence.py`), not yet consumed by any cascor training path; cascor's POC path is strictly 2-D (`data_provider.py:200-205` asserts `ndim != 2 → error`). P5 must wire the windowed loader into the output trainer (§9.3). (VERIFIED.)
- **Equities (`equities_seq`)** is the best-matched class: next-close regression is AR(D) on the target; per-step `dt` + positive `target_dt` available (`_sequence.py:113-123`); leakage invariants pinned by `test_sequence_windowing_leakage.py` (I1-I5). Lookback capped at ~30 trading sessions (≈6 weeks). (VERIFIED.)

---

## 16. The D≤30 / Stateless Reconciliation AND the Asymptotic-vs-Windowed Ceiling Reconciliation

Two reconciliations, kept explicitly separate (the anti-hallucination rule against letting windowing collapse the asymptotic analysis):

### 16.1 D≤30 / stateless-per-window vs the realized architecture

The ratified constraint binds the **realized architecture**: both the hidden FIR registers and the output AR register reset at each window boundary (`h₀=0`), D ≤ window ≤ 30, partial fills zero-padded. At **T=1** the design must reduce to today's feed-forward cascor exactly — D collapses to 1, no lag axis, the AR loop has no past to feed back, byte-identical 2-D path. This is a HARD back-compat requirement and must be coded + tested, not assumed (the AR-loop-empty-at-T=1 behavior is INFERRED). The reset is what makes window mini-batching tractable (§9.5) AND what caps the deployed counting period at ≤30 (§16.2).

### 16.2 Asymptotic representational ceiling vs the windowed/deployed/learnable bounds — BOTH kept

There are **three distinct ceilings**, and the windowing does NOT erase the asymptotic one:

| Layer | What it says about P5 | Strength |
|---|---|---|
| **ASYMPTOTIC REPRESENTABILITY** (unbounded sequences, §3.2) | Output AR loop lifts the class off pure star-free into **bounded cyclic / mod-k counting** (period > 2 — ~2D-3D observed per additive node, ≤ 2^D representable), NOT full regular. Conditional on a saturating readout; nullifies to no-break under a pure-linear MSE readout. | The real theoretical verdict. |
| **WINDOWED / DEPLOYED bound** (§3.3, §16.1) | The ≤30 stateless reset unrolls the IIR to ≤30 lags = finite-window FIR-of-outputs; any realizable period is capped at **≤ window (≤30)**. mod-k for k>30 impossible. | **Hardest; dominates the deployed machine.** |
| **LEARNABILITY** (§3.4) | BPTT over ≤30 lags is vanishing/exploding-prone; mod-k needs marginal-stability poles = the gradient knife-edge; MSE biases toward contractive no-count solutions. | Strictly below representability; collapses the *trainable* ceiling toward fading-memory. |

**Reconciliation statement:** P5's *theoretical* representational ceiling genuinely rises (partial star-free break into bounded-periodic), and that verdict stands on its own over unbounded sequences. But the *deployed* P5 — windowed, stateless-per-window, BPTT-trained — exhibits at most a ≤30-period counter that is moreover hard to learn, so in practice P5 ships a **fading-memory IIR tail** (real, robust) plus an **in-principle bounded-modular-counting lift** that is largely gradient-unreachable and window-capped. Do not let the windowing erase the asymptotic answer; do not let the asymptotic answer overstate the deployed capability. Both are true at their own layer.

---

## 17. Comparison vs P4 / P1 / P2 / P3

P1-P4 verdicts carried from the VERIFIED corpus; P5 verdicts INFERRED against verified code + literature, except the AR-node period facts (empirically re-run this session).

| Axis | P1 (faithful RCC) | P2 (group units) | P3 (reservoir/LMU) | P4 (hidden FIR) | **P5 (this eval)** |
|---|---|---|---|---|---|
| **Recurrence type & location** | IIR depth-1, HIDDEN candidates | IIR + group state, HIDDEN | Evolving/continuous state, HIDDEN (grown, frozen) | **NONE — pure FIR** | **HYBRID: FIR hidden + IIR depth-D at the READOUT, siloed** |
| **Star-free ceiling** | INHERITS (+parity via −weight) | **BREAKS** (in-principle; no recipe) | INHERITS (category-error correction) | INHERITS — **weakest** | **BREAKS PARTIALLY** — bounded cyclic/mod-k, NOT full regular |
| **Constructive fit** | Strong; recurrence in discardable candidate phase | Fits but recipe-gated | Strong; "most honest" | **BEST — lightest** | **INVERTS** P4's output-static edge (non-convex BPTT re-solve every round) |
| **Irregular-Δt** | Poor (sample-indexed); A only | Poor; A only | **BEST** — native B/C | Poor; A only | Poor; A only (+Δt-feature integration) — no better than P4 |
| **Horizon** | Fading memory in feature path | Group state in feature path | **Strongest** controllable long memory | **SHALLOW** — FIR cliff at D | IIR tail at readout (target-AR only); exogenous still FIR-capped; ≤30 deployed |
| **Integration cost** | MODERATE | HIGH (recipe gap) | HIGH (new unit types) | **LOWEST** | **HIGHEST** among cascor-faithful (P4 surface + output BPTT rewrite) |
| **C1 transparency** | Clean | Risky | Black-box-import risk | Cleanest | Clean (largest hand-built surface; +stability infra) |
| **Training-recipe maturity** | **HIGHEST** (Fahlman's RCC) | **LOWEST** (no recipe) | HIGH (convex readout) | High-but-shallow (coherence defect) | MIXED/LOW-MODERATE (BPTT knife-edge; unpublished) |
| **Overall risk** | **LOWEST** (safe, ceiling-inherited) | HIGHEST research risk | MODERATE | LOW build / LOW payoff | MODERATE-HIGH; real fading-memory gain, mostly-theoretical counting lift |

**The spectrum (where recurrence lives, how it treats the ceiling):** P4 (pure FIR, weakest, inherits) < P1 (IIR depth-1 self-loop in HIDDEN candidates, inherits + parity) ≈ **P5** on mechanism-class but deeper-and-relocated (IIR depth-D self-loop at the READOUT, breaks partially into bounded mod-k) < P2 (2nd-order multiplicative group units, the only genuine break toward full regular, but no recipe). **P3 sits orthogonally:** genuine fading/continuous state in the feature path, best Δt story, but INHERITS the ceiling.

**P5's distinctive niche** (held by no other proposal): the only design that places GENUINE IIR RECURRENCE on the OUTPUT/READOUT layer while keeping the entire feature-extraction path pure FIR. It buys mod-k counting (representable) over P1's/Thm-7's mod-2 and a fading-memory horizon (deployable) over P4's hard cliff, at the cost of a non-convex output re-solve, a new IIR-instability surface, and a selection/readout mismatch — with the big relief that the recurrence never crosses the worker wire.

---

## 18. Claims Considered and NOT Supported (brief)

- **`Q1-3` — "P5's output loop is just relocated P1."** Considered. Same mechanism class, but P5 differs decisively on LOCATION (output vs hidden), TRAINING (BPTT-after-install vs correlation-during-selection-then-freeze), and DEPTH (order-D vs order-1). Recorded as a *characterization* (relocated+deepened P1), not as equivalence. Not load-bearing.
- **`Q1-5` — "recurrence-at-the-readout-only is/ isn't genuine recurrence."** Considered. Resolved as: YES formally (the output IIR passes the feedback test), with two caveats (stability not guaranteed; deployed object collapses to finite-window FIR). Both layers kept; no single yes/no asserted as load-bearing.
- **`P5-COH-04` — "per-round AR re-fit against a changed exogenous basis is incoherent."** Considered. Real interaction (the frozen-FIR basis is non-stationary across rounds while `v` is a standing parameter), but it is a *consequence* of `P5-COH-02`/`P5-COH-03`, not an independent finding; not separately load-bearing.
- **`Q2-3` — "P5 improves Δt handling."** Considered and recorded as a NARROW, INFERRED improvement in Δt-*integration* (not Δt-*awareness*); explicitly NOT a claim that P5 becomes Δt-aware.
- **`Q3-3` / `Q3-5` — window-reset and IIR-stability horizon bounds.** Considered; folded into §8.4/§16 as the two hard bounds on the §8.1 gain, not as standalone gains.
- **`P5-CEIL-02` / `P5-CEIL-06` / `P5-CEIL-08`** — the full-regular structural bound, the learnability-≪-representability gate, and the comparative ranking. Considered and incorporated into §3; recorded as bounds/separations, NOT as ceiling-break claims.
- **First-pass "break confined to parity/ℤ₂"** (early kr-direct/narx/repr-vs-learn angles). Considered and **CORRECTED** by the empirical period re-run: order-D additive feedback reaches period > 2 (bounded mod-k), exceeding parity. The parity-only statement is the order-1 lower bound, not the order-D verdict.
- **"P5 inherits NARX Turing-universality."** Considered and **REJECTED** as the central misattribution (NARX requires feedback through Ψ; P5 silos it away → Finite-Memory-Machine regime). (`P5-CEIL-03`/`Q1-2`.)

---

## 19. Recommendation + Open Questions + Suggested Guardrail Tests

### 19.1 Recommendation

**P5 is a coherent, implementable, middle-path design — keep as an exploration, but right-size the claims.** Its niche is genuine: more recurrence-correct and higher-ceiling than P4/P1 *at the readout*, with a **deployable** payoff (fading-memory horizon) that is real and a **representable** payoff (bounded mod-k counting) that is largely gradient-unreachable and window-capped. Decisively:

- If the goal is the **safest faithful recurrence**, **P1 wins** (mature recipe, ceiling-inherited but lowest-risk).
- If the goal is **genuinely breaking the ceiling toward full regular**, **only P2 qualifies** (gated by the missing constructive recipe).
- **P5's value is the fading-memory readout tail and the AR-structured fit to equities-style next-step regression** — sell it on those, not on "breaks star-free," which is true only asymptotically/partially and mostly unreachable under BPTT + the ≤30 window.

Before any build, resolve the conditionality flag (§3.2 step 7): **specify the output activation `f`.** A pure-linear MSE readout yields *no* asymptotic break (LTI fading memory only); the bounded-mod-k lift requires a saturating readout AND BPTT finding the oscillating regime.

### 19.2 Open questions

1. **Is the output activation `f` identity (LTI, no break) or saturating (mod-k possible)?** Unspecified today (`cascade_correlation.py:2018` is `nn.MSELoss` over a linear readout). This single choice determines whether §3.2's break exists at all. (INFERRED gap.)
2. **Teacher-forcing vs free-running BPTT** on the output AR — changes both cost and what a "batch" means; the prompt leaves it open. (INFERRED.)
3. **Does the selection-criterion mismatch (`P5-COH-01`) materially degrade unit quality** under a recurrent readout, or does the post-install BPTT compensate? Needs empirical measurement.
4. **What `v`-stability constraint** (spectral-radius cap vs pole projection vs plain clipping) best trades long-horizon memory against trainability on the marginal-stability knife-edge?
5. **Per-output `D` uniform or per-output learned/variable?** Affects schema (`D_i`) and the `[output_size, D]` tensor shape.

### 19.3 Suggested guardrail tests

- **G1 — T=1 byte-identity.** On a 2-D fixture, assert P5's output equals today's static-solve readout bit-for-bit (AR loop empty at T=1). (Touch-point: `:1979`/`:2067`.)
- **G2 — Snapshot round-trip for `v` + `D_i`.** Save→load a grown P5 network; assert `v[output_size,D]` and every unit's `D_i` survive (would silently vanish today per `F3`). (Touch-point: `snapshot_serializer.py:381-486`.)
- **G3 — IIR stability under BPTT.** Train on a synthetic with adversarial `v`-init near |λ|=1; assert no NaN/Inf and bounded outputs with the new clipping + `v`-constraint active. (Touch-point: optimizer factory `:3076-3229`.)
- **G4 — parity/mod-k probe (expected to FAIL on regression).** A tiny synthetic parity target; assert PASS only if BPTT finds a stable cycle. Expect FAILURE on MSE/regression targets — documents the learnability gap (§3.4) as a test, not a claim.
- **G5 — monotone-improvement rollback.** After a post-install BPTT re-solve, assert validation loss did not regress vs the pre-install checkpoint; roll back if it did (operational recovery of the convex guarantee P5 loses, `P5-COH-02`).
- **G6 — RC-5 resync after first D>1 install.** Assert the stale-candidate guard (`:4117-4124`) does not trip after a delay-lined install (P4 §12 T10).
- **G7 — worker payload unchanged.** Assert the candidate task/result schema (`task_executor.py:60-67`/`:132-167`) is byte-identical with P5 enabled (only array widths differ). (`Q4-5`.)

---

## 20. References (verified only)

**Local PDFs read (primary):**

- Knorozova, N. A., & Ronca, A. (2024). *On The Expressivity of Recurrent Neural Cascades.* AAAI; `arXiv:2312.09048v2` (6 Sep 2024). `papers/On The Expressivity of Recurrent Neural Cascades-2312.09048v2.pdf` (full read, pp.1-24). Quoted: Thm 4/5/7 (p.8), group-free=star-free (p.4), second-order neuron defn (p.3), C₂ Props 5/6 + contribution bullet 4 (p.1, p.7), toggle/odd-length (p.23), input-function β (pp.3-4); convergent-input robustness via the flip-flop discussion, formalized in Lemmas 10/11.
- Fahlman, S. E. (1990). *The Recurrent Cascade-Correlation Architecture.* NIPS-1990. `papers/NIPS-1990-the-recurrent-cascade-correlation-architecture-Paper.pdf` (pp.1-9). Quoted: unit eqn `V(t)=σ(Σ I_i w_i + V(t−1)w_s)` (p.192), flip-flop/oscillate behavior + state-zeroed-per-string (p.191).

**Web sources (verbatim where quoted):**

- Siegelmann, H. T., Horne, B. G., & Giles, C. L. (1997). *Computational capabilities of recurrent NARX neural networks.* IEEE Trans. SMC-B 27(2):208-215. DOI 10.1109/3477.558801. PubMed 18255858. (VERIFIED-PRIMARY abstract for output-only-feedback + Turing-equivalence; the converse FMM bound is VERIFIED-SECONDARY from the paper body, not the abstract.)
- Giles, C. L., Chen, D., Sun, G.-Z., Chen, H.-H., Lee, Y.-C., & Goudreau, M. W. (1995). *Constructive learning of recurrent neural networks: Limitations of recurrent cascade correlation and a simple solution.* IEEE Trans. Neural Networks 6(4):829-836. DOI 10.1109/72.392247. (VERIFIED-SECONDARY; PDF font-scrambled — multi-source consensus; activation = Heaviside/monotone.)
- Kremer, S. C. (1996). *Comments on "Constructive learning of recurrent neural networks…".* IEEE Trans. Neural Networks 7(4):1047-1051. DOI 10.1109/72.508949. PubMed 18263501. (VERIFIED-PRIMARY abstract.)
- Jordan, M. I. (1986). *Serial Order: A Parallel Distributed Processing Approach.* UCSD ICS Report 8604. (VERIFIED-SECONDARY via Wikipedia "Recurrent neural network".)
- McNaughton, R., & Papert, S. (1971). *Counter-Free Automata.* MIT Press; Schützenberger, M. P. (1965). (VERIFIED-SECONDARY: star-free = aperiodic = counter-free = group-free; threshold-countable, not mod-countable.)
- FIR/IIR/TDL: dsprelated.com "Tapped Delay Line (TDL)". (VERIFIED-SECONDARY.)
- Bengio, Y., Simard, P., & Frasconi, P. (1994). *Learning long-term dependencies with gradient descent is difficult.* (cited inside K&R bibliography). Pascanu, R., Mikolov, T., & Bengio, Y. (2013); Ribeiro, A. H., et al. (2020). (VERIFIED-SECONDARY for the marginal-stability ↔ vanishing-gradient identity.)

**Code (juniper-cascor `src/`, all opened this session unless flagged):**

- `cascade_correlation/cascade_correlation.py`: fan-in builder `:1921-1947` (buffer width `:1940`, lower-triangular read `:1945`, scalar write `:1946`); output matmul `:1979`; **`train_output_layer` `:1986-2106`** (epochs `:2011`, MSE `:2018`, output-width re-derive `:2021-2024`, nn.Linear rebuild `:2027-2032`, seed `:2033-2037`, optimizer `:2041`, **CR-060 hoist `:2047-2051`**, active-dim mask `:2062-2071`, **breaking loop body `:2066-2076`**, write-back `:2086-2091`, final-loss `:2094-2097`); constructor `output_weights`/`output_bias` `:738-739`; 2-D validator `:1632-1633`; SharedMemory ndim cap `:272-273`; optimizer factory `:3076-3229`; install dict `:4032-4037` (install-only `:4014-4018`); resize helper `:4051-4086` (width math `:4079`, bit-identity note `:4065-4069`); RC-5 guard `:4117-4124`; growth loop `:1875`/`:1903`/`:4595`/`:4622`/`:4624`.
- `candidate_unit/candidate_unit.py`: state-free forward `:479`; correlation objective `:897-969` (flatten `:935-936`, `torch.dot` `:941`). (Line numbers carried from the verified P4-eval reference list.)
- `snapshots/snapshot_serializer.py`: output-layer schema `:381-425` (`weights`/`bias` `:394-404`, checksums `:407-414`, optimizer state `:417-423`); hidden-units schema `:439-486`. (Carried from the verified reference list.)
- `juniper-cascor-worker/juniper_cascor_worker/task_executor.py`: contract `:60-67`, candidate consume `:82-111`, `train_detailed` call `:114-120`, result/tensor schema `:132-167`.
- `juniper-cascor/src/spiral_problem/data_provider.py:200-205` (2-D assert); `juniper-data/juniper_data/generators/_sequence.py:106`/`:113-123`/`:160` (windowing, `dt`, `target_dt`); `juniper-data/.../tests/unit/test_sequence_windowing_leakage.py:71-134` (I1-I5).
- `util/ad-hoc/verify_ar_node_period_p5.py` (AR-node period re-run THIS session: order-1 max period 2; order-D max period 4,6,8,16,16 for D=2..6). `util/ad-hoc/verify_delta_t_reference_code.py:31-60` (LMU exogenous-input reference, not output-AR).

---

*End of working draft. Version 0.1.0 — exploration, not ratified. Every P5-specific verdict is an INFERENCE against verified code + literature (P5 is unpublished), EXCEPT the AR-node period facts, which were empirically verified this session.*
