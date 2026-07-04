# Recurrent Cascade-Correlation — OQ-4 Redesign: Proposals, Validation & Open-Question Analysis

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 model-pick redesign exploration
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.2.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-04

---

> **What this is.** A working record of the exploration into *how to add recurrent capability to Cascade-Correlation*, opened because **[OQ-4] was reopened** (RCC's no-count/no-group "star-free" representational ceiling is architectural, not guardrail-fixable). It captures three independently-generated proposals, the multi-agent validation of those proposals, and the running analysis of two open design questions. It feeds the model pick in the companion **[Recurrent Model Design & Plan](JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md)** (§1.5 / §1.6 [OQ-4]) and the substrate/wiring work in **[Model/Middleware Refactor Design & Plan](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md)**.
>
> **Status of the pieces:** §3 proposals = drafted + validated. §4 validation = complete. §5 (Q1 batching) = analyzed. §6 (Qa window) = decided. §7 (Qb mechanics + wiring) = **resolved** (BPTT-over-window default; RTRL deferred). §8 = RTRL future work.
>
> **Addendum (2026-06-09):** a fourth proposal — **P4**, a per-node *output* delay-line ("recurrent structure add-on") — is evaluated separately in [P4 Output-Delay-Line Adversarial Evaluation](JUNIPER_2026-06-09_JUNIPER-RECURRENCE_RECURSE-OQ4-DELAY-LINE-OUTPUT-MODULE-EVAL.md). Verdict: it is an **FIR / Takens delay-embedding, not recurrence** (no feedback in cascor's feed-forward DAG); it inherits the star-free ceiling and therefore does *not* advance OQ-4. Its sole edge is integration cheapness (candidate-training objective + worker transports untouched). For genuine recurrence prefer P1/P3.

---

## 1. Context — the OQ-4 question

The original plan picked **Recurrent Cascade-Correlation (RCC)** as the primary model. OQ-4 reopened it because RCC's self-recurrent cascade has a *proven* representational ceiling — it captures **exactly the star-free / group-free regular languages** (Giles et al. 1995; Kremer 1996; Knorozova & Ronca 2024), i.e. **no modulo/parity counting, no cyclic-group structure**. Knorozova & Ronca also name the remedy: **add group-implementing units**. The question this exploration answers: *what are the candidate ways to give Cascade-Correlation genuine recurrence, and how do they each treat that ceiling?*

## 2. The shared prerequisite — cascor has no temporal substrate today

The single most important finding (independently surfaced by the architecture and code-feasibility validators): **`juniper-cascor` is purely stateless feed-forward over a 2-D `(batch, features)` tensor.** There is no time axis anywhere —

- `CandidateUnit.forward` is a scalar dot-product (`candidate_unit.py`); `_update_weights_and_bias` (≈958-1050) builds a **single-shot autograd graph** with **no BPTT**;
- frozen units are stored as a **4-key dict** `{weights, bias, activation_fn, correlation}` (`cascade_correlation.py` ≈3982) — **no slot for recurrent state**; install hardcodes the activation;
- output training (`train_output_layer` ≈1936) is a static `nn.Linear` fit over a flat matrix;
- the parallel/remote worker protocol ships **fixed scalar tuples** over `(batch, features)`.

**Consequence:** every proposal below shares a large, previously-unscoped prerequisite — building the **temporal/sequential substrate** (a real time axis, stateful unit storage, a recurrence-aware gradient, sequence-aware data + worker contracts). This is effectively **"Workstream 0"** and is the subject of Open Questions 1 and (b).

> Data-side note (2026-06-04): juniper-data's `equities` generator (#164, landed after the design doc froze) now emits a **regression** target + temporal split, but `X` is still 2-D `(n,10)` and it *bypasses* the classification contract with a dummy one-hot `y`. So the **regression** half of WS-1 has started; the **3-D temporal** contract (below) has not.

## 3. The three proposals (corrected per validation)

All three are framed as extensions of cascor's grow → train-candidate-by-correlation → install → **freeze (tenure)** → train-output loop. They differ in the recurrent unit and in how they treat the ceiling: **inherit it (P1), break it (P2), or sidestep it into fading memory (P3).**

### P1 — Self-recurrent candidate units (faithful RCC)
Each candidate gains one trainable self-recurrent weight on its own delayed activation, `a_j(t)=f(Σ wᵢⱼxᵢ(t)+Σ wₖⱼhₖ(t)+w_jj·a_j(t−1))`; the self-loop is correlation-trained and frozen on tenure. **Ceiling:** inherits the star-free limit. **Validated corrections:** (a) the ceiling attribution must lead with the RCC-specific **Giles 1995 / Kremer 1996**, not Knorozova-Ronca — whose exact-star-free theorem assumes *positive* recurrent weights and never names RCC (a freely-trained `w_jj` is sign-unconstrained; their Thm 7 shows a negative-weight neuron can exceed star-free); parity-impossibility is a *conjecture* there. (b) the "tiny delta / reuse unchanged" claim is false against the code (needs temporal forward, recurrence-aware gradient, install/snapshot schema change). (c) commit to Fahlman's **RTRL-style** recurrence-aware gradient (cascor has no BPTT). **Verdict:** keep-with-fixes; most citation-accurate, lowest-risk.

### P2 — Group-implementing recurrent candidate units (ceiling-breaking)
Enrich the candidate pool with units implementing cyclic-group structure (Knorozova-Ronca's remedy) to break the star-free ceiling. **Validated corrections (functionality = FLAWED as written):** (a) the rotation/oscillator unit was an *extrapolation* — K&R's actual construction uses **negative-weight, second-order (multiplicative) neurons** implementing the cyclic group C2, not rotation matrices. (b) "full regular-language expressivity" is *in-principle only* (C2 is the sole concrete case). (c) the "mixed pool" was **fabricated** — cascor's candidate pool is homogeneous in code. (d) the Arjovsky uRNN citation is real but mispositioned (gradient-trained composed unitary matrices, architecturally opposite to CasCor). (e) it is really *P1's whole substrate + an unproven, objective-less group-unit training recipe.* **Verdict:** keep-with-fixes as the OQ-4 "option a" research direction, heavily re-anchored.

### P3 — Grown recurrent reservoir / memory blocks (regression-native)
Each grown candidate is a small **fixed** recurrent block — an ESN sub-reservoir (random, ESP-scaled) or an LMU memory cell (closed-form) — with only its read-in/readout trained and frozen, mirroring cascor's output training. **Validated corrections:** (a) **"avoids the star-free ceiling" is a category error** — an ESP-bounded reservoir has *fading memory* and **also cannot do parity/modular counting**; narrow the claim to "continuous/fading-memory regression," not ceiling-breaking. (b) **LMU is not "grow-one-block"** — it is fixed-order per our own design doc and the literature. (c) "native ridge solve / no autodiff" is wrong about *this* codebase (cascor is autograd throughout; no ridge solve exists). (d) Qiao preserves ESP via a predefined **singular-value spectrum**, not spectral-radius scaling. **Verdict:** keep-with-fixes; most architecturally honest and genuinely recurrent (intrinsic state sidesteps the BPTT-through-frozen-units problem).

## 4. Multi-agent validation (method & results)

**Method.** A 15-agent workflow: each proposal examined by **4 independent adversarial lenses** — (1) citations/accuracy (web-verified), (2) architectural functionality, (3) feasibility against the **real** `juniper-cascor` code, (4) hallucination/consistency sweep — then a synthesizer per proposal. ~1.3M tokens, 190 tool calls.

| Proposal | Accuracy | Functionality | Genuine hallucinations | Recommendation |
|----------|----------|---------------|------------------------|----------------|
| P1 self-recurrent (RCC) | pass-with-caveats | sound-with-caveats | 3 | keep-with-fixes |
| P2 group-implementing | pass-with-caveats | **flawed** (as written) | 5 | keep-with-fixes |
| P3 reservoir/memory | pass-with-caveats | sound-with-caveats | ~4 (7 flagged; rest were "citations clean") | keep-with-fixes |

**No fabricated citations** — every reference verified real and correctly attributed. The defects are overstatements (P1's integration cost, P3's "no autodiff") and two genuine errors (P2's misattribution of the rotation unit to K&R; P3's category error on the ceiling).

**Sharpened OQ-4 takeaway.** Only P2's *true* group units (2nd-order/multiplicative) genuinely break the no-count/no-group ceiling — **and there is no known constructive training recipe for them.** P1 inherits the ceiling; **P3 does not escape it either** (fading memory ≠ counting). All paths first require the temporal substrate (§2).

## 5. Open Question 1 — batching/mini-batching vs. the temporal component

**Core relationship.** Batch and time are *orthogonal* axes of the 3-D tensor `(time, batch, features)`. The **batch axis** = independent sequences (parallelizable; each row carries its own state, no cross-talk). The **time axis** = steps bound by `hₜ=f(xₜ,hₜ₋₁)` (inherently sequential). **Mini-batching parallelizes across sequences; it does nothing to the sequential time dependency.** The classic error — and one cascor is primed for, since it currently treats every row as an independent sample — is collapsing the two: feeding a series as independent batch rows yields a windowed feed-forward model (TDNN), **not** recurrence.

**Literature mechanics.** Gradient-variance reduction is per-*sequence*, not per-*timestep* (timesteps within a sequence are correlated); BPTT memory is `O(T·B·H)` (→ truncated BPTT to cap it; Williams & Peng 1990); RTRL (Williams & Zipser 1989) is the forward-only online alternative, `O(1)` in length but `O(N³)`/step in size; variable lengths force padding+masking (or packing); LayerNorm (not BatchNorm) is the batch-independent normalizer; *stateless* (reset per sequence) vs *stateful* (carry across batches for chunked streams, requires aligned non-shuffled batches).

**Cascor-specific.** The **freeze property localizes the recurrence**: with all hidden units frozen and outputs not fed back, **output-layer training stays static** — flatten `(B,T)→B·T` rows and it is the *same* regression cascor already does (no BPTT). **Live recurrence exists only in candidate training**, and because cascor trains **one candidate at a time** against frozen units, the recurrent sensitivity to track is just that single unit's self-loop → **RTRL is cheap and exact here** (this is why Fahlman could use a recurrence-aware gradient in 1991). Frozen trajectories `(B,T,n_frozen)` are cacheable (×T memory, computed once). Two genuine work items: the candidate **correlation objective must be redefined over `(sequence, timestep)`**, and the **worker protocol needs a 3-D payload + a time-ordering contract** (batch shuffle OK, time order sacred).

## 6. Open Question (a) — RESOLVED: variable time window

**Decision (Paul, 2026-06-04):** the design incorporates a **variable time window**, allowed sizes **1 … N** with a practical upper bound **N ≈ 30**. Consequently a target `y_t` may be produced **at every timestep or at a larger interval** (variable output stride).

Immediate implications (expanded in §7):
- **T ≤ 30 is small** → full BPTT over a padded window is memory-trivial; truncated BPTT is unnecessary; padding-to-30 + mask is cheaper than bucketing.
- **T = 1 ⇒ today's cascor** (no history) → the recurrent model *subsumes* the current feed-forward model; the 2-D contract is the `T=1` special case of the 3-D contract. Backward-compatible by construction.
- **Variable output stride ⇒ a readout mask**: state advances on *every* input step, but loss/correlation accumulate only at **readout positions**. State is dense; supervision is sparse.

## 7. Open Question (b) — training mechanics + contract/wiring

> Conclusions below fold in the §6 variable-window decision (T ∈ 1..~30, variable output stride). **Headline: the 1..30 cap turns the hardest training question (BPTT memory) into a non-issue, making BPTT-over-the-window the default; RTRL is deferred to future work (§8).**

### 7.1 Training mechanics

**Gradient method — BPTT default, RTRL deferred.** BPTT memory is `O(T·B·H)`; at `T≤30` a full unroll is memory-trivial, so truncated BPTT is unnecessary and **full BPTT via autograd over the window is the default**: a `t=1..T` tensor loop, `loss=-|corr|`, `loss.backward()`, reusing cascor's existing autograd path; frozen-unit trajectories are constants (no grad). Two reasons BPTT wins here over RTRL: (1) least new code (reuses autograd), and (2) the candidate **correlation objective is a batch-global, mean-centered statistic**, which composes naturally with reverse-mode autograd but awkwardly with RTRL's forward per-step accumulation. RTRL's strengths (O(1) in length, online, Fahlman-faithful) don't pay in the 1..30 regime; it is documented as future work in §8.

**Variable output stride = dense state, sparse supervision.** Carry a per-timestep **readout mask** `m(t)∈{0,1}`. The candidate's recurrence advances on **every** input step (state is dense), but the correlation objective accumulates **only at readout positions**: `V={a_j(t):m(t)=1}` correlated against residual `E` at those positions, mean-centered over that set. Because a readout step's state depends (through recurrence) on all prior unsupervised steps, BPTT flows gradient back through them — the candidate learns to *encode* the gap into state useful at the next readout (the encoder / many-to-fewer pattern). Special cases unify cleanly: readout-only-at-final-step ⇒ many-to-one (`m` has one 1 per sequence) ⇒ cascor's current per-sample correlation over sequence-final state; **`T=1` ⇒ today's feed-forward cascor exactly** (the recurrent model subsumes the current one).

**The freeze property keeps output training static.** With all hidden units frozen and outputs not fed back, output-layer training remains a static fit over the flattened readout rows `(Σ readouts, n_units) → (Σ readouts, output_dim)` — no BPTT, trivially batchable/shuffleable. **Live recurrence is confined to candidate training**; this confinement is what makes recurrent cascor tractable.

**State reset = stateless per window.** Treat each 1..30-step window as a self-contained example (`h₀=0`, reset per window) → the batch axis is fully shuffleable; padding-to-30 + mask is the only bookkeeping. Go stateful only if switching to one continuous stream (not the current intent); if more context is needed, widen the window (≤30) rather than carry state across batches.

### 7.2 Contract / wiring

**3-D NPZ contract (additive; WS-1 / OQ-6).** New optional keys, dispatched by `X.ndim`:
- `X`: `(n_windows, T_max=30, n_features)` float32, zero-padded.
- `seq_lengths`: `(n_windows,)` — actual length ≤30 (masks padded tail).
- `readout_mask`: `(n_windows, T_max)` bool — where targets exist / loss + correlation apply (this *is* the variable-stride mechanism).
- `y`: dense `(n_windows, T_max, output_dim)`, masked.
- `scaling`: persisted per-feature/target stats for reproducible denormalize (regression).
- `task_type`: `regression|classification`.
- **Back-compat free:** `X.ndim==2` ⇒ `(n,1,F)`, `T=1`, single readout ⇒ byte-identical to current cascor. The 3-D contract is a strict superset; 2-D consumers untouched. (`equities` #164 supplies the regression+scaling half already.)

**Windowing ownership (C3 boundary decision).** juniper-data owns slicing raw series into windows + readout-position policy + scaling, exposing `window_size`/`stride`/`readout_policy` as generation params; the model consumes pre-windowed artifacts and never slices raw series. Friction: a window-size sweep = multiple dataset requests; pragmatic lean — generate at `T_max=30` and allow a model-side **read-only sub-window view that only shrinks** (a benign loader concern, not dataset logic). Governs OQ-8 too.

**Worker / parallel protocol — heaviest item; logic, not just format.** Today: fixed ~8-field scalar task tuple + flat `(batch, features)` tensors over SharedTrainingMemory / WebSocket binary frames. Recurrence requires: 3-D `(B,T,F)` payload + `seq_lengths` + `readout_mask` + readout-position residual; task tuple gains `T_max`, `unit_kind`, recurrence hyperparams; an explicit **ordering contract** (batch axis shardable/shuffleable; **time axis immutable**); and the worker must run the **recurrent forward + recurrent gradient + readout-masked correlation** — so the recurrent candidate implementation is deployed worker-side, not just a new wire format.

**Lifecycle / snapshot / forward.** Frozen-unit record extends the 4-key dict → add `kind`, `recurrent_weights` (e.g. `w_jj` or block matrices), `state_init`; install / HDF5 snapshot / restore schema extends; old snapshots default `kind=feedforward`. `_compute_hidden_outputs` becomes a time loop producing `(B,T,n_units)` trajectories, **cacheable** for frozen units (×T memory paid once, reused across the candidate pool). Lifecycle event vocabulary unchanged; per-epoch metrics aggregate over `(seq, readout)`.

**Serving / predict route.** Recurrent inference accepts a 1..30-step window and returns `y` at readout positions (the 2-D route is the `T=1` case). A stateful **streaming** mode (one step at a time, carry state) is an optional later addition (touches canopy WS-5).

**Migration lever.** Because `T=1` is identity to current cascor, the substrate ships behind a default `T=1` (no behavior change), then `T>1` is enabled; the conformance kit asserts a `T=1` recurrent model matches the feed-forward model exactly — the safe, golden-gated cutover the refactor doc already wants.

### 7.3 Net design for the 1..30 regime

Cache frozen trajectories `(B,T,·)`; train candidates with **BPTT-over-the-window** (batch `B`, full unroll `T≤30`) against a **readout-masked correlation**; keep output training as the existing **static solve** over flattened readout rows; **stateless per-window**, padded-to-30 + masked; ship behind a **`T=1`-identity migration**. RTRL is the deferred alternative (§8).

---

## 8. Future work — RTRL (Real-Time Recurrent Learning) as an alternative candidate-gradient

> **Deferred, not rejected.** BPTT-over-the-window (§7.1) is the default *for the 1..30 regime*. RTRL (Williams & Zipser 1989) is documented here in full — strengths, weaknesses, risks, guardrails, design, integration, tradeoffs, and triggers — because it is the Fahlman-faithful method and becomes the better choice under specific future conditions. Recorded so the analysis is not lost when the default is implemented.

**Mechanism (single-candidate form).** Maintain the forward sensitivity `s(t)=∂a_j(t)/∂θ` of the candidate's activation w.r.t. its own parameters `θ` (input weights + self-loop `w_jj`): `s(t)=f'(z_t)·(φ_t + w_jj·s(t−1))`, where `z_t=Σ w·x(t)+w_jj·a_j(t−1)` and `φ_t` is the explicit input term. Forward-only; no stored unroll.

**Strengths.**
1. **`O(1)` memory in sequence length** — no activation unroll stored → handles unbounded/streaming sequences.
2. **Exact online gradient**, updated every step → fits true online / continual-learning.
3. **Cheap in cascor's structure** — one candidate at a time against frozen units ⇒ the sensitivity recursion is `O(candidate-params)`/step (the general-network `O(N³)`/step cost does **not** apply).
4. **Fahlman-faithful** — RCC's original recurrence-aware gradient is RTRL-style; using it keeps the implementation true to the primary source (C1).
5. Natural fit for **stateful streaming inference-time adaptation**.

**Weaknesses.**
1. General-network cost is `O(N³)`/step — bites only if multiple recurrent units are ever trained jointly or a recurrent output layer is added.
2. **Awkward composition with the batch-global, mean-centered correlation objective** — RTRL accumulates per-step sensitivities while the correlation's centering/normalization is a global statistic, requiring a two-pass or running-moment (Welford-style) treatment.
3. **Bespoke code** — does not reuse PyTorch autograd; a hand-rolled recursion with no autograd safety net.
4. Numerical care required for the sensitivity recursion (accumulation/conditioning).

**Risks.** Silent gradient bugs in the hand-rolled recursion; divergence from BPTT results if the correlation coupling is implemented wrong; maintenance burden of a second gradient path; added test surface.

**Guardrails.** Gate RTRL behind a **conformance test asserting RTRL gradient ≈ BPTT gradient** (finite-difference cross-check + agreement-to-tolerance) on small cases before trusting it; keep **BPTT as the reference oracle**; enable only in the regimes where it pays.

**Design.** Per-candidate, per-sequence sensitivity recursion (above); accumulate the correlation gradient via running moments for the mean-centering; reset `s(0)=0` per window (stateless) or carry across chunks (stateful streaming). Output training is unaffected (stays a static solve, §7.1).

**Integration.** Lives in **candidate training only** (freeze localization unchanged — output training stays static regardless of gradient method). Worker-side, the sensitivity recursion must be deployed alongside the recurrent candidate. **No change to the data contract** (§7.2) — RTRL vs BPTT is a candidate-trainer-internal choice.

**Tradeoffs vs BPTT.** Memory: RTRL wins for large `T`. Compute/step: BPTT wins. Implementation simplicity: BPTT wins (autograd). Objective composition: BPTT wins (global correlation). Online/streaming: RTRL wins. Fidelity to Fahlman: RTRL.

**Trigger conditions to revisit RTRL.** (a) the ~30 window cap is removed / sequences become unbounded; (b) a true online or continual-learning mode is added; (c) streaming inference-time adaptation is wanted; (d) BPTT truncation is empirically shown to harm learning; (e) joint training of multiple recurrent units makes the BPTT memory profile problematic.

## 9. References (verified in the validation pass)

- Fahlman 1991, *The Recurrent Cascade-Correlation Architecture*, NIPS-3.
- Giles, Chen, Sun, Chen, Lee, Goudreau 1995, *Constructive learning of recurrent NNs: limitations of RCC…*, IEEE TNN 6(4):829-836.
- Kremer 1996, *Comments on "Constructive learning…"*, IEEE TNN 7(4):1047-1051.
- Knorozova & Ronca 2024, *On the Expressivity of Recurrent Neural Cascades*, AAAI; arXiv:2312.09048.
- Williams & Zipser 1989 (RTRL), Neural Computation 1(2):270-280; Williams & Peng 1990 (truncated BPTT).
- Jaeger 2001 (ESN); Lukoševičius & Jaeger 2009 (reservoir computing survey); Qiao et al. 2017 (Growing ESN), IEEE TNNLS 28(2):391-404; Yildiz et al. 2012 (ESP non-sufficiency), Neural Networks 35:1-9.
- Voelker, Kajić & Eliasmith 2019 (LMU), NeurIPS.
- Arjovsky, Shah & Bengio 2016 (uRNN), ICML; arXiv:1511.06464 — *bibliographically valid; relevance as a CasCor analog is weak.*

---

*Working draft. Pairs with the [model doc](JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md) ([OQ-4]) and the [refactor doc](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md) (temporal substrate / WS-1).*
