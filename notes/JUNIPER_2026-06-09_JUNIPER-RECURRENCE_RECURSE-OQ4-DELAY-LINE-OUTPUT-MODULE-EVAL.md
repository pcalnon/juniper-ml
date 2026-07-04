# Recurrent Cascade-Correlation — P4 "Output Delay-Line" Module: Adversarial Evaluation

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 P4 design evaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-09

---

## 1. Executive Summary + Headline Verdict

**Headline verdict.** P4 — a per-node *output* delay-line ("recurrence output module") that buffers a hidden node's last `D` activations and emits them as an ordered collection, attached **only after** candidate-pool training and best-correlation selection — is **mechanically implementable but is not recurrence**. It is a **finite-impulse-response (FIR) / tapped-delay-line / Takens delay-coordinate embedding** of each node's activation signal. The corpus names this exact construct: feeding past activations as a fixed window "yields a windowed feed-forward model (TDNN), **not** recurrence" (PROPOSALS §5).

The four-question answers, in one line each:

- **Q1 (correctness of recurrence): NEGATIVE on the formal claim, mixed on efficacy.** P4 does not implement recurrence in the genuine IIR / dynamical-system sense — there is no feedback into the node's own activation, so the node's impulse response is zero beyond `D` steps by construction. It *is* an accurate, potentially useful finite-memory embedding (the TDNN/FIR/TCN family), but it must not be labeled "recurrence." It also **inherits the star-free / no-count ceiling** and therefore does **not** advance the reopened OQ-4 concern.
- **Q2 (irregular-Δt): POORLY POSITIONED.** The register indexes by *sample position*, not elapsed time. A 3-day weekend gap is indistinguishable from a 1-day gap. Only Approach A (Δt-as-feature) can help; Approaches B/C are structurally inapplicable to a stateless buffer. The single empirically-verified irregular-Δt robustness result in the corpus belongs to the competing LMU/Approach-C design.
- **Q3 (horizon): SHARP BUT SHALLOW.** Hard cap at `D ≤ 30` samples with no decay tail (FIR cliff). Cascade stacking compounds the receptive field but only as an uncontrolled, greedily-frozen composition. Far short of the fading/continuous memory of P3.
- **Q4 (mini-batch): LIGHTEST BURDEN OF ANY RECURRENCE PROPOSAL, BUT NOT FREE.** Because the register attaches post-selection and never feeds back, candidate-pool training stays in today's exact full-batch shuffleable form. But a new window-batched, time-ordered, padded/masked loader plus a forward time-loop are still required, and any 3-D worker payload hits a hard `ndim ≤ 2` cap.

**P4's genuine edge** is integration tractability: its candidate-training **objective** and worker transport stay scalar/2-D — alone among the four it avoids the recurrence-aware candidate gradient (BPTT-over-window; RTRL deferred per PROPOSALS §8) that P1/P2/P3 require, because the delay-line attaches *after* best-correlation selection. (One asterisk: candidate input-*sizing* must still absorb upstream lag width after the first `D > 1` install or the RC-5 guard trips — §12 T10; the training objective and worker IO are themselves untouched.) **P4's decisive deficits** are that it is not recurrence, does not touch the OQ-4 ceiling, and is the worst-positioned of all four options for irregular Δt.

**Bottom line for Paul:** Position P4 honestly as a **finite-memory lag-embedding / feature-enrichment device**, not as recurrence. If the goal is genuine recurrence or resolving OQ-4's no-count ceiling, P4 cannot deliver it — that requires feedback (P1), groups (P2), or evolving internal state (P3). P4 only competes when the real requirement is a cheap, transparent, regularly-sampled finite-window temporal feature for short-horizon regression.

> **Anti-hallucination scope note.** P4 is novel and unpublished; the corpus **never names P4**. Every P4-specific verdict in this document is an INFERENCE from P4's stated description against VERIFIED live code and VERIFIED literature. Facts about P1/P2/P3, the live cascor code, and the cited papers are VERIFIED and flagged as such. Where line numbers come from corpus *grounding-pass* notes rather than files opened this session, they are flagged.

> **Evaluation provenance.** Produced 2026-06-09 by a maximal-depth adversarial multi-agent workflow (141 sub-agents, ~8.9 M tokens, 2 291 tool calls): a 4-agent shared reality-brief (live cascor code + corpus + POC + FIR/IIR/Takens literature) → 7 adversarial lenses (recurrence-theory, N+1-D functionality, code-feasibility, constructive-coherence, irregular-Δt, horizon, mini-batch) → **3-vote perspective-diverse refutation (code / literature / consistency angles, default-to-refuted) of every material finding** → P1/P2/P3 + Δt-A–D comparison → synthesis → two independent critics (completeness 0.92, anti-hallucination 0.93). **17 of 42 candidate findings survived refutation; 25 were rejected** (summarised in §17). Mirrors the 15-agent validation method recorded in PROPOSALS §4.

---

## 2. What P4 Is + How It Maps Onto the Existing Taxonomy

### 2.1 The design under evaluation

P4 modifies a cascor hidden node as follows:

1. The node computes its activation **exactly as today**: input weights → weighted sum → output activation function. This is unchanged.
2. Instead of passing its scalar activation directly downstream, the activation becomes the **input to a new "recurrence module"** appended as the node's final output stage.
3. The module is a multi-step delay element functioning as a **shift register of depth `D`** (the time-series embedding dimension): it holds the node's last `D` activations. `D` is finite and bounded.
4. The module output is an **ordered collection of the node's last `D` activation tensors**, so the augmented node emits an (N+1)-dimensional output tensor (one extra "lag" axis added to the original N-dimensional output).
5. **Integration timing:** candidate-pool training proceeds **normally and unchanged** (the usual single-shot correlation training). **Only after** the candidate pool is trained and the best-correlation candidate(s) selected is the recurrence module attached to the new hidden node(s), just before they are installed/frozen into the network.

### 2.2 The defining mechanical fact (VERIFIED)

A cascor node activation today is a **scalar-per-sample** (one column). VERIFIED in two places:

- Candidate forward: `output = self.activation_fn(torch.sum(x * self.weights, dim=1) + self.bias)` at `candidate_unit.py:479`. `self.weights` is a 1-D vector (`candidate_unit.py:244`), `self.bias` is shape `[1]` (`candidate_unit.py:246`); `torch.sum(..., dim=1)` collapses the feature axis to a 1-D `[batch]` result.
- Frozen-unit forward: `unit["activation_fn"](torch.sum(unit_input * unit["weights"], dim=1) + unit["bias"])` written to **one column** `buffer[:, col]` at `cascade_correlation.py:1946`.

P4 takes that scalar and buffers its last `D` values. **No feedback path returns the buffered output into the node's own activation.** This is the load-bearing structural fact for the entire evaluation.

### 2.3 The corpus taxonomy P1/P2/P3 and where P4 lands

The corpus (PROPOSALS §3/§4) defines three recurrence proposals, all framed as extensions of cascor's *grow → correlation-train candidate → install → freeze (tenure) → train-output* loop. They differ on the recurrent unit and on the **star-free representational ceiling** (inherit / break / sidestep):

| | Mechanism | Recurrence type | Ceiling | Corpus verdict |
|---|---|---|---|---|
| **P1** self-recurrent RCC | each candidate gains a trainable self-loop `w_jj·a_j(t−1)` on its own delayed activation; correlation-trained during selection, frozen on tenure | **IIR, depth-1** (genuine feedback) | inherits | keep-with-fixes; "most citation-accurate, lowest-risk" (PROPOSALS §3.39, §4) |
| **P2** group-implementing units | enrich candidate pool with cyclic-group (C2) units via negative-weight 2nd-order/multiplicative neurons (Knorozova-Ronca remedy) | **IIR + group state** | **breaks** (in-principle only) | keep-with-fixes, heavily re-anchored; "no known constructive training recipe" (PROPOSALS §3.42, §4) |
| **P3** grown reservoir/memory | each grown candidate is a fixed ESN sub-reservoir or LMU cell; only read-in/readout trained and frozen | **genuine evolving state** (fading / continuous) | inherits (corpus corrects "avoids ceiling" to a CATEGORY ERROR) | keep-with-fixes; "most architecturally honest and genuinely recurrent" (PROPOSALS §3.45) |
| **P4** *(this doc)* | per-node OUTPUT delay-line of depth `D`; buffers last `D` activations; attached AFTER selection | **FIR / finite-memory** (no feedback) | inherits AND weakest | not a corpus proposal; INFERRED to be the TDNN pattern PROPOSALS §5 labels "not recurrence" |

**Where P4 slots (INFERRED, high confidence):**

- P4 is closest in *spirit* to P1 (a single-delay idea), but moves the delay to the **output** and **outside** candidate training. P1's self-recurrent weight is correlation-trained *during* candidate training (PROPOSALS §3.39); P4 explicitly leaves candidate training untouched.
- P4 carries **no evolving state** at all, making it strictly weaker than P3 (validated "genuinely recurrent") on the recurrence axis.
- P4 adds neither group structure (not P2) nor state feedback (not P1/P3), so it **inherits the star-free ceiling and additionally lacks even fading memory** — it is the lightest-weight and least-recurrent of the four.

---

## 3. Functionality — Including the N+1-D Fan-In

This section establishes exactly how P4's "(N+1)-D output tensor" must be realized against the live code, and why "leaves all current functionality intact" is only half true.

### 3.1 How a node's output is consumed downstream today (VERIFIED)

The fan-in vector for both the output layer and the next candidate is a **flat concatenation `[raw_inputs | hidden_0 | hidden_1 | ...]`**, one scalar column per node, built into a pre-allocated 2-D buffer:

- `_compute_hidden_outputs` (`cascade_correlation.py:1921-1947`): `total_features = self.input_size + n_hidden` (line 1940) — **one column per hidden unit, hardcoded**. `buffer = torch.empty(batch_size, total_features)` (1941) — strictly 2-D. Raw inputs fill `buffer[:, :self.input_size]` (1942); each unit fills `buffer[:, col]` where `col = self.input_size + i` (1944-1946).
- **Cascade wiring (the defining cascor property):** `unit_input = buffer[:, :col]` (1945) — unit *i* reads raw inputs **plus all earlier hidden units' outputs**. So `unit["weights"]` for unit *i* has length `input_size + i`. The documented invariant is "Hidden unit *i* has weight vector shape `[self.input_size + i]`" (`cascade_correlation.py:952`). (The live forward this invariant governs is line 1946; the docstring's own internal pointer to "line 1544" is a stale pre-refactor reference and was not relied upon.)
- **Output layer:** `output = torch.matmul(output_input, self.output_weights) + self.output_bias` (`cascade_correlation.py:1979`). `output_weights` has shape `[input_size + n_hidden, output_size]`. The matmul **requires** `output_input` to be exactly 2-D `[batch, input_size + n_hidden]`.
- **Input validation gate:** `forward` calls `_validate_tensor_shapes`, which at **`cascade_correlation.py:1632-1633` hard-raises** `ValidationError` if `len(x.shape) != 2`. Same gate on `predict` and `predict_classes`.

### 3.2 P4's "(N+1)-D output" is only implementable as a feature-axis FLATTEN (VERIFIED)

Three live consumers force the lag axis to be folded into the feature axis rather than kept as a literal rank-3 tensor (finding L-AF-F2, VERIFIED):

1. **Single-column write:** `buffer[:, col] = ...` (`cascade_correlation.py:1946`) assigns exactly ONE column — a `[batch, D]` block cannot occupy a scalar slot.
2. **2-D output matmul:** `torch.matmul(output_input, self.output_weights)` (`cascade_correlation.py:1979`) requires `output_input` to be 2-D.
3. **Rank-2 network-input validator:** `len(x.shape) != 2` hard-raises (`cascade_correlation.py:1632-1633`).

**Therefore the only mechanically viable interpretation of P4 is "this unit contributes `D` columns to the flat fan-in instead of 1."** A literal `(N+1)-D` rank-3 fan-in fails both the matmul and the line-1632 validator. This reframes P4 from "add a tensor axis" to "**widen the flat fan-in by `Σ D_i` columns**."

### 3.3 The cascade weight-vector invariant breaks at THREE independent sites (VERIFIED)

Cascor enforces "one column per unit" at three independent enforcement sites (finding L-AF-F1 / L1-F2, VERIFIED). To admit `D`-wide units, all three must change from `+1` to `+D_i` in lockstep:

1. **Fan-in buffer width:** `total_features = self.input_size + n_hidden` (`cascade_correlation.py:1940`) and per-unit column `col = self.input_size + i` (1944), with single-column write at 1946.
2. **Output-layer width — re-derived independently:** `input_size += len(self.hidden_units)` inside `train_output_layer` (`cascade_correlation.py:2024`). This is **especially easy to miss** because it re-derives the width independently of the `output_weights` tensor it must match; a partial change here silently mismatches the rebuilt `nn.Linear` against `output_weights` and raises at the `copy_` (≈2034) or the matmul (1979).
3. **Resize arithmetic:** `new_input_size = prev_input_size + num_added` in `_resize_output_layer_for_new_units` (`cascade_correlation.py:4079`), with `num_added=1` per single add (≈4149).

Plus the **per-unit weight-shape invariant** at `cascade_correlation.py:952` — each downstream unit's `weights` length and `input_size` grow by `D` per upstream lag-expanded predecessor, not 1.

### 3.4 Quantitative fan-in inflation (VERIFIED structure, arithmetic INFERRED)

Because unit *i* reads all predecessors (`unit_input = buffer[:, :col]`, line 1945), a depth-`k` candidate receiving from `m` upstream units sees `input_size + Σ_{j<k} D_j` inputs (`= input_size + k·D` for uniform `D`) instead of `input_size + k`. At `D = 30`:

- A unit at cascade depth `k` sees up to **~30× inflation** of the hidden-contributed fan-in.
- The output-weight matrix rows inflate identically.
- Worked example (**INFERRED arithmetic**): 10 stacked units at `D = 30` → deepest candidate sees `input_size + 300` columns vs `input_size + 10` today. Parameter-count scaling per unit goes from `O(input_size + k)` to `O(input_size + k·D)`.

### 3.5 The "leaves intact all current functionality" claim is HALF TRUE (VERIFIED)

The design claim that P4 "leaves intact all current functionality and structure of cascor hidden nodes from input weights through output activation" splits cleanly (finding L-AF-F3, VERIFIED):

- **INTACT:** the node's INTERNAL scalar math (input-weights → weighted-sum → activation) is genuinely unchanged — `candidate_unit.py:479` and the frozen-unit equivalent `cascade_correlation.py:1946` both still produce a scalar-per-sample, and P4 feeds *that* scalar into its register. "From input weights through output activation" is literally preserved.
- **NOT INTACT:** everything that consumes the node's output downstream. Because the activation now fans out as `D` columns: (i) the next unit's weight-vector length and `input_size` change (the 952 invariant); (ii) the output-layer width changes (2024/4079); (iii) the frozen-unit dict needs a `lag_depth` field (install at `cascade_correlation.py:4032-4037` stores only 4 keys); (iv) the RC-5 stale-candidate guard `candidate.weights.shape[0] == candidate_input.shape[1]` (`cascade_correlation.py:4121-4124`) would mismatch the moment any upstream unit is `D`-wide.

The node's **internal structure** is intact; its **interface to the cascade** is exactly what the fan-in change rewrites. The design claim is therefore misleading as stated.

### 3.6 Flatten vs pool — the design implicitly chose flatten (VERIFIED)

To admit `D`-wide units, the fan-in construction must EITHER (finding L-AF-F5, VERIFIED):

- **(a) FLATTEN:** give each downstream weight vector `D_i` extra entries per upstream unit. Preserves full lag information; multiplies parameter count and fan-in by ~`D`; the only option consistent with P4's stated "ordered collection of last `D` activations" semantics.
- **(b) POOL:** reduce each unit's `D` lags to a scalar (mean/last) before the dot product. Keeps fan-in at `+1`/unit and keeps the 952 invariant intact, but **discards the lag structure P4 exists to provide** — self-defeating.

P4 as described (emits an ordered `D`-collection, adds a lag axis) **implies FLATTEN**, so the fan-in/parameter inflation is unavoidable.

### 3.7 Cascade-compounding produces a deep nonlinear FIR filter bank (INFERRED, high confidence)

Because each unit's activation is itself a nonlinear function of upstream *lagged* activations (line 1945), stacking delay-lined units composes finite-memory filters: unit `k`'s window over unit `k−1`'s windowed-nonlinear outputs is a **deep nonlinear FIR / tapped-delay cascade** — the corpus "TDNN, not recurrence" family (PROPOSALS §5; literature Wan 1993 FIR-nets, Bai et al. 2018 TCN). The effective temporal receptive field **deepens with cascade depth** but remains FIR / finite-memory with **no state feedback** (no `a_j(t−1)` re-enters the node), categorically weaker than RCC's IIR self-loop.

> *(Note: the specific compounding arithmetic and "deep nonlinear FIR filter bank" framing was offered as a candidate finding and is listed in §17 as "considered, not load-bearing" — the underlying cascade-read mechanism at line 1945 is VERIFIED; the filter-bank characterization is a sound but non-refuted-survivor inference.)*

### 3.8 The stateless-per-window register-fill loop (INFERRED — C1 sketch)

cascor today evaluates the whole batch in one vectorized pass (`_compute_hidden_outputs`, no time axis), so P4's `D ≤ 30` stateless-per-window semantics require an explicit within-window time-loop. The minimal first-principles fill (per window; INFERRED — no implementation exists yet):

```text
for each window w (batch axis — shuffleable):
    reset every unit's depth-D ring buffer to 0          # h0 = 0, stateless per window
    for t in 0 .. L-1:                                   # within-window time — ORDER-SACRED
        buf = [ raw_inputs(w, t) ]                       # rebuild the flat fan-in at step t
        for unit i in cascade order (0 .. n_hidden-1):  # DAG order: i reads only predecessors
            a_i = activation_fn( sum(buf * weights_i) + bias_i )   # scalar, exactly as today
            push a_i into ring_buffer_i                  # depth-D shift register
            buf += last D taps of ring_buffer_i          # zero-padded where t < D (partial fill)
        if readout_mask(w, t): record a readout row at t
```

Invariants: the **window/batch axis stays fully shuffleable**; the **within-window step order is immutable**; partial fills (`t < D`) are **zero-padded**; at `T = 1` the inner loop runs once, `D` collapses to 1, and the emitted fan-in is byte-identical to today's. This is Workstream-0 substrate (T15/T16), not a freeze-time attachment.

---

## 4. Correctness of "Recurrence" — FIR vs IIR, Ceiling Placement (Q1)

### 4.1 The FIR/IIR distinction (VERIFIED definitions)

- **FIR (finite impulse response):** impulse response settles to zero in finite time *because there is no feedback*; output depends only on present and past **inputs**. "Lack of feedback guarantees that the impulse response will be finite, making 'finite impulse response' nearly synonymous with 'no feedback'." (Wikipedia, "Finite impulse response.")
- **IIR (infinite impulse response):** has internal **feedback** (recursion on past **outputs**); response can persist indefinitely. Also called "recursive" / "feedback" filters. (ScienceDirect, "Infinite Impulse Response.")

### 4.2 P4 is FIR, not genuine recurrence (VERIFIED + INFERRED, high confidence — finding L1-F1)

P4 attaches a depth-`D` tapped delay-line of a node's past **output** activations with **no feedback path into the node's own activation**. The node activation is computed exactly as today — a stateless instantaneous function of the current fan-in (`candidate_unit.py:479`; frozen-unit form `cascade_correlation.py:1946`). A delay-line that only buffers past outputs and never recurses them back into the unit's own dynamics is an **FIR / tapped-delay-line element**: its impulse response is zero after `D` steps by construction.

The two formal litmus tests both fail:

- **Dynamical-system test (Knorozova & Ronca 2024, `papers/On The Expressivity of Recurrent Neural Cascades-2312.09048v2.pdf` p.2):** a recurrent component carries an evolving state `x_t = f(x_{t-1}, u_t)`. P4 has no such state-evolution function on the node — only a buffer of past stateless outputs — so it is **not** a dynamical-system/recurrent component in that formal sense.
- **Fahlman's framing (`papers/NIPS-1990-the-recurrent-cascade-correlation-architecture-Paper.pdf` p.191):** plain cascade-correlation "has no short-term memory in the network. The outputs at any given time are a function only of the current inputs and the network's weights," and "the network must be able to form recurrent loops if it is to retain state for an indefinite time." **P4 adds a finite buffer, not a loop.**

**Q1 answer (correctness):** P4 does **not** implement recurrence in the IIR / dynamical sense. It implements a finite-memory FIR / TDNN embedding. This is a labeling/taxonomy result, decisive on its own terms.

### 4.3 P4 is STRICTLY WEAKER than RCC (P1) and a different mechanism (VERIFIED — finding L1-F4)

RCC (Fahlman p.192) augments each candidate with a single self-recurrent weight feeding back the unit's OWN previous output:

> **V(t) = σ( Σᵢ Iᵢ(t)·wᵢ + V(t−1)·w_s )**

— genuine depth-1 **IIR feedback**, and the self-weight `w_s` is correlation-**trained DURING candidate selection** via a recurrence-aware gradient `dV(t)/dw = σ'(t)·(Iᵢ(t) + w_s·dV(t−1)/dw)` that propagates through time (RTRL-style). Fahlman states each frozen RCC unit "is in effect a single state variable in a finite-state machine" (p.192).

P4 differs on **three axes simultaneously**:

1. **No feedback** (FIR vs IIR).
2. **Lag structure attached AFTER selection** — the unit was chosen for a purely instantaneous correlation objective. VERIFIED: the candidate update at `candidate_unit.py:1011-1042` builds a single-shot autograd graph `logits = sum(x*w) + b` with **no temporal term**, and the correlation `torch.dot` at ≈1038 is order-invariant over the batch.
3. **Depth-`D` buffer vs depth-1 state.**

Representational consequence: an RCC unit **is** an FSM state variable; a P4 unit is a fixed FIR window with **no state variable at all**. So describing P4 as "RCC's delay moved to the output" is wrong — **removing the feedback removes the recurrence**.

### 4.4 P4 lacks the evolving state that makes P3 genuinely recurrent (INFERRED — finding L1-F5)

P3 grows fixed recurrent blocks (ESN `h = f(x, h_{t-1})` with echo-state-property-bounded fading memory, or the LMU linear-memory ODE projected onto Legendre polynomials). These ARE dynamical-system components (state `x_t = f(x_{t-1}, u_t)`). P4 carries no evolving state — a pure buffer. Consequences: (a) on the "genuinely recurrent" axis P4 is weaker than P3; (b) on horizon, P3's fading/continuous memory reaches beyond its block size via decay, while P4's reach is hard-capped at exactly `D` steps; (c) on the ceiling, *both* P3 and P4 still cannot count/parity. P4 is the lightest-weight and least-recurrent of the four.

### 4.5 Ceiling placement: P4 stays WITHIN star-free / no-count (INFERRED from VERIFIED theorems)

The star-free hierarchy (all VERIFIED from the Knorozova-Ronca PDF and the formal-language sources):

- **Star-free = aperiodic = counter-free = group-free** (Schützenberger 1965; McNaughton & Papert, *Counter-Free Automata*, MIT Press 1971; cited Knorozova-Ronca pp.1-2). Counter-free automata "**cannot count modulo any integer > 1**, though they can count to a threshold" (`1, 2, …, n−1, n-or-more`).
- **Knorozova & Ronca 2024 (p.6):** Theorem 5 — positive-weight sign/tanh RNCs implement **exactly** the group-free (= star-free) regular functions. Theorem 4 — for any regular function that is *not* group-free, there is **no** positive-weight sign/tanh RNC implementing it. Theorem 7 establishes the **negative-weight** escape from star-free; the cyclic-group-of-order-two construction via **second-order sign/tanh neurons** is stated in the Abstract / "Our contribution" (p.1) and the Theorem-6 discussion. The lift requires **groups + negative recurrent weights** — a feed-forward delay line has neither.
- **Giles et al. 1995 (IEEE TNN 6(4):829-836, web-verified):** RCC cannot realize finite-state automata with state-cycles of length > 2 under constant input — the original "no-modular-counting" RCC ceiling.
- **Kremer 1996 (IEEE TNN 7(4):1047-1051, web-verified):** adds a second, larger unrepresentable class.

**Application to P4 (INFERRED, high confidence):** a depth-`D` tapped delay-line is a literal finite **threshold window** over the last `D` activations — it can express "did event X happen within the last `D` steps" (threshold counting, exactly what counter-free/aperiodic automata already do) but **cannot** implement a modular/periodic counter of unbounded period. What breaks the ceiling is **groups / feedback**, not delay lines. A feed-forward FIR delay line provides neither, so it is **orthogonal** to the mechanism that would lift the ceiling. **P4 inherits the star-free ceiling and therefore does NOT resolve the reopened OQ-4 concern** (OQ-4 reopened precisely because the no-count/no-group ceiling is architectural, not guardrail-fixable — MODEL §1.6 OQ-4).

### 4.6 P4 is not dismissible on efficacy (VERIFIED literature family)

The "not recurrence" verdict is a **labeling** result, not an **efficacy** dismissal. Finite-window models over activations are a well-established, empirically effective family:

- **TDNN** — Waibel, Hanazawa, Hinton, Shikano, Lang, "Phoneme Recognition Using Time-Delay Neural Networks," IEEE TASSP 37(3):328-339, 1989 (web-verified). Feeds each unit a tapped delay line of its inputs; feed-forward, finite memory, shift-invariant.
- **FIR networks / temporal backprop** — Wan 1993 (Weigend & Gershenfeld eds., pp.195-217, web-verified). Each synapse is an FIR linear filter; FIR networks unfold into static feed-forward nets — they add no genuine recurrence.
- **TCN / WaveNet** — Bai, Kolter, Koltun, arXiv:1803.01271, 2018; van den Oord et al., arXiv:1609.03499, 2016 (web-verified). Causal dilated convolutions are FIR filters over the sequence; finite (if large) receptive field, no recurrence, fully parallel; match or beat RNNs on many benchmarks.

**The NARX boundary case (web-verified, the clean way to communicate the distinction):** NARX (Lin, Horne, Tiňo, Giles, IEEE TNN 7(6):1329-1338, 1996) *also* uses tapped delay lines, but because it taps **fed-back outputs**, it crosses into genuine recurrence/IIR. P4 is "the FIR half of NARX without the feedback half." **The presence of a delay line alone does not make something recurrent; the feedback does.**

**Q1 synthesis.** On *labeling*: P4 is FIR, not recurrence — decisive. On *efficacy*: P4 sits in the proven-effective TDNN/FIR/TCN family and can be useful for finite-horizon regression. The honest framing is **"finite-memory delay-embedding feature enrichment,"** never "recurrence."

---

## 5. Coherence with the Constructive / Correlation Engine (Post-Hoc-Buffer Analysis)

### 5.1 The correlation objective is structurally blind to the lag buffer (VERIFIED — finding L-COH-F1)

Under P4 the delay module is attached only after candidate selection, so the correlation objective never sees the temporal buffer. The candidate's forward (`candidate_unit.py:479`) and the autograd objective (`candidate_unit.py:1011-1012`: `logits = torch.sum(x*weights_param, dim=1) + bias_param`; `output = activation_fn(logits)`) compute an instantaneous scalar per row. `_calculate_correlation` (`candidate_unit.py:935-957`) flattens output and error to 1-D and takes Pearson over the whole batch — **there is no lag axis in scope**. The candidate's weights are optimized purely to make the *instantaneous* activation correlate with the residual; the `D`-tap history P4 adds is never part of the objective the unit was selected for.

This is the load-bearing coherence defect: cascor's defining act of discovery (correlation-train then select) operates on a feature set that **excludes the very temporal structure P4 claims to add**.

### 5.2 Temporal discovery is deferred — never to the owning unit (VERIFIED — finding L-COH-F2/F3)

Because the buffer is attached post-selection and the unit is then frozen (`weights.clone().detach()`, `cascade_correlation.py:4033`), the only consumers that can ever USE the `D` taps are:

- **(a) the static output-layer MSE solve** — which can only weight the frozen taps **linearly** (an FIR readout); and
- **(b) a LATER candidate** — which sees the `D` taps as flat input columns, because the candidate pool's `input_size = candidate_input.shape[1]` (`cascade_correlation.py:2219`). So if unit *i* emitted `D` columns, candidate *i+1* receives them as `D` ordinary features and could correlation-train a linear-in-lags combination against the residual.

This is real temporal discovery, but it is **"lagged by one full cascade layer"**: the lag structure of unit *i* is only exploited by the *next* growth step's correlation objective, and for co-installed layers (`add_units_as_layer`, where fan-in is pre-computed once) it is deferred even further. The unit that owns the buffer **never optimized anything about it**.

This caps P4's discoverable temporal class to the **FIR / tapped-delay family** (TDNN/FIR/TCN), strictly weaker than P1, where the self-recurrent weight `w_s` is itself correlation-trained, SELECTED for, then frozen — genuine IIR recurrence the engine actually discovers.

### 5.3 Instantaneous |Pearson| is the wrong selection criterion for a temporal task (VERIFIED context)

The selection gate ranks candidates by order-invariant batch correlation against `residual = y − output` (`cascade_correlation.py:3964`) compared to an adaptive threshold `max(1e-6, min(correlation_threshold, residual_mag*0.01))`. Two consequences for a temporal task: (1) the criterion is **invariant to row permutation** (the `torch.dot` over flattened vectors) — it cannot reward "this activation predicts the residual `D` steps later"; (2) the depth/contents of the buffer that gets bolted on are **not a function of the objective at all**. So selection and the added mechanism are decoupled, which is incoherent with cascor's premise that the thing you train the candidate for is the thing you install.

### 5.4 Freeze/tenure is benign for buffer CONTENTS but the install invariant must change (VERIFIED — finding L-COH-F5)

Freezing does not conflict with a stateless shift register per se: the buffer holds **no learnable parameter** (it is pure delayed copies of the unit's deterministic output), so `.detach()` (line 4033) loses nothing — there is no temporal weight to freeze, unlike P1's `w_s`. The genuine interaction is **structural**: `_install_hidden_unit` stores a 4-key dict with no depth field (`cascade_correlation.py:4032-4037`); `add_unit`'s stale-candidate guard asserts `candidate.weights.shape[0] == candidate_input.shape[1]` (`cascade_correlation.py:4121-4124`); the output resize uses `num_added=1` / `prev_input_size=candidate_input.shape[1]` (≈4148-4151). A `D`-column unit breaks the `+1` accounting. These are mechanical edits, **not a learning-coherence flaw** — provided the lag axis is flattened into feature columns.

### 5.5 Net coherence verdict (VERIFIED synthesis — finding L-COH-F6)

P4 is coherent with the constructive ENGINE only in a **shallow, structural** sense (it leaves candidate training byte-for-byte today's static single-shot correlation loop and therefore leaves the worker protocol untouched), and **INCOHERENT with the correlation engine's PURPOSE**: cascor's value is that a unit is installed *because* it was correlation-selected for a specific contribution; P4 installs a unit selected for instantaneous fit and then attaches a temporal apparatus the objective never evaluated. **P4 should be framed as a lag-embedding / feature-enrichment device, not as recurrence the constructive correlation engine discovers.** Its one genuine engine-level virtue is that candidate training and the worker protocol stay untouched (2-D IO), avoiding the `ndim > 2` `SharedTrainingMemory` wall.

---

## 6. Irregular-Δt — Answer Q2

### 6.1 A shift register indexes by sample position, not elapsed time (VERIFIED — finding Q2-F1, the core defect)

P4's depth-`D` output delay-line holds the node's last `D` activations indexed by **sample/row position**. `a(t−1)` means "previous stored sample" irrespective of whether 1 trading day or a 3-day weekend separates the rows. This is structurally identical to RCC's "discrete one-step self-delay; no elapsed-time notion" (DELTA-T §4.3). The cascor forward path confirms position-indexing is the only thing available: `_compute_hidden_outputs` writes one scalar per unit to `buffer[:, col]` (`cascade_correlation.py:1943-1946`) with **no time coordinate anywhere**, and candidate forward is a pure instantaneous dot-product (`candidate_unit.py:479`).

On an irregular-Δt series the `D` taps therefore span an **inconsistent, data-dependent real-time horizon**: a window ending after a holiday week covers more wall-clock time than one inside a dense trading run, with no way for the node to distinguish them. **P4 is a regular-Δt construction by default and is biased/incorrect on irregular-Δt data unless explicitly augmented.**

### 6.2 A delay-line is a Takens embedding that assumes uniform sampling (VERIFIED — finding Q2-F4)

A per-node depth-`D` delay-line emitting the last `D` activations is precisely a **Takens delay-coordinate embedding** of that node's scalar activation signal: φ_T(x) = (α(x), α(f(x)), …, α(f^{k−1}(x))) (Takens 1981, LNM 898:366-381; statement verified via Wikipedia "Takens's theorem"). The reconstruction guarantee requires embedding dimension `k > 2·d_A` (box-counting dimension of the attractor) and is formulated over **successive applications of the time-evolution map at a fixed lag τ** — i.e., observations at **regular discrete time steps**. The standard theorem does **not** cover irregular/non-uniform sampling. So the very justification for *why* a tapped delay-line carries temporal information assumes uniform Δt; under equities weekend/holiday gaps or any event-stream Δt, the embedding is no longer over a fixed temporal horizon.

### 6.3 Only Approach A applies; B/C are inapplicable (VERIFIED contract — findings Q2-F3, Q2-F6)

The DELTA-T note's four Δt approaches (DELTA-T §5 table):

- **Approach A (Δt as input channel):** feed `dt` as an extra input dimension. Because a node computes its activation from its input fan-in *before* buffering, supplying `dt` as a feature lets the elapsed-time signal propagate into the activations the delay-line then stores. **This is the one principled Δt remedy compatible with P4.** The data contract already supplies the key: `dt_{split}` derived from calendar-day diffs (`_sequence.py:114-116` — `dt[0]=0`, `dt[1:]=np.diff(win_ords)`; `target_dt` at `:123`), validated by `test_sequence_windowing_leakage.py` invariant I3.
- **Approach B (Δt-gated decay `h ← h·exp(−Δt/τ)`):** INAPPLICABLE — P4 has no evolving internal state to decay.
- **Approach C (solver-free continuous-time LMU re-discretization):** INAPPLICABLE — P4 has no linear-memory ODE to discretize.
- **Approach D (resample + impute):** model-agnostic (juniper-data owns it), but lossy and discards informative-sampling signal.

**Two viable injection points, both with costs (Q2-F6, VERIFIED blockers):** (a) feeding `dt` to candidate *training* so correlation selection sees it would require a wider candidate input — `dt`-as-an-extra-*column* (still 2-D) sidesteps the rank gates but then `dt` competes as just another correlation feature; a 3-D candidate input collides with the hard 2-D gate `_validate_tensor_shapes` (`cascade_correlation.py:1632-1633`) and the `SharedTrainingMemory` `ndim > 2` `ValueError` (`cascade_correlation.py:272-273`). (b) P4's stated post-selection attach keeps candidate training 2-D but then the `dt` signal was correlation-selected on the *instantaneous* objective. **Either way, P4 never selects a unit FOR its irregular-Δt behavior.**

Critically, **Approach A only PRESENTS Δt** — the model must learn to use it; DELTA-T grades it "weak ... presentation, not mechanism" (§5). It is strictly weaker than the continuous-time bias of Approach C.

### 6.4 Δt-awareness stays ORTHOGONAL to the ceiling (VERIFIED — finding Q2-F5)

DELTA-T §4.5 (verbatim, VERIFIED): "Δt handling is **orthogonal** to RCC's star-free ceiling: adding Δt awareness does not fix the no-count limitation, and fixing the ceiling ... does not address Δt." §1.6: "two distinct limits (can't express *when*; can't express certain *whats*)." A Δt-augmented P4 is **still no-count**, and a ceiling-fixed variant is still Δt-blind. P4 is doubly limited: FIR/finite-memory (no feedback ⇒ stays within star-free) **and** elapsed-time-blind.

### 6.5 The one measured irregular-Δt robustness belongs to the alternative (VERIFIED — POC anchor)

The single quantified irregular-Δt result in the entire corpus — **grid-invariance** `e_irr ≈ 0.039-0.043` vs `e_reg ≈ 0.035` (DELTA-T §8.7, executed via `util/ad-hoc/verify_delta_t_reference_code.py`, numpy 2.4.4) — validates the **LMU / Approach-C** design, which is P3's mechanism. Grid-invariance is precisely the property a tapped delay line **lacks**. So the only measured irregular-Δt evidence in the corpus is evidence *for the alternative*, not for P4.

**Q2 answer.** P4 handles irregular-Δt **poorly out of the box** (position-indexed, Takens-uniform-sampling premise violated), is **salvageable to "Δt-aware-by-presentation"** via Approach A over the existing `dt` contract, but **cannot reach the continuous-time correctness** of the LMU/Approach-C alternative, and resolves neither the "when" nor the "what" limitation.

---

## 7. Effective Horizon — Answer Q3 (time-series / irregular-Δt / equities)

### 7.1 Direct memory horizon is hard-capped at D ≤ 30 samples, no decay tail (VERIFIED — finding H-F1)

Under the ratified `D ≤ window ≤ 30` stateless-per-window constraint, P4's per-node output delay-line gives each node access to **exactly** its last `D` activations and nothing older. Because there is **no feedback** into the node's own activation (cascor forward is a feed-forward DAG: `candidate_unit.py:479` and `cascade_correlation.py:1946` are identically state-free), the node is an FIR element whose impulse response is **exactly zero beyond `D` steps**. This is the strictest possible memory-horizon semantics: a **sharp cliff at `D`, no graceful decay tail**.

Contrast (VERIFIED): an IIR/recurrent element (RCC's `V(t) = σ(Σ Iᵢ wᵢ + V(t−1)·w_s)`, Fahlman p.192) or a fading-memory reservoir/LMU carries a decaying-but-nonzero response **indefinitely**.

### 7.2 Cascade stacking compounds the receptive field — but only as a greedily-frozen composition (VERIFIED structure — finding H-F2)

Stacking delay-lined units extends the effective horizon beyond a single unit's `D` because the cascade fan-in (`cascade_correlation.py:1945`, unit *i* reads `buffer[:, :col]` = raw inputs PLUS all earlier hidden units' lag-columns) lets a later unit consume earlier units' delay-line columns. So effective horizon **CAN exceed a single `D` via depth**. BUT two code facts bound this: (1) each installed unit is **frozen** (`weights.clone().detach()`, line 4033), so the temporal mixing a layer performs over its predecessors' lags is selected once and can never be re-optimized; (2) the selected candidate was trained on the **instantaneous** 2-D fan-in (correlation training never sees a lag axis). The compounded reach is therefore an **uncontrolled, greedily-frozen composition, not a clean multiplicative `D·depth` product**, and it degrades unpredictably with depth.

### 7.3 Horizon is in SAMPLE COUNT, not real time (VERIFIED — finding H-F3)

P4's delay-line indexes by step position; the **real-time** horizon = sum of the `D` most-recent inter-sample gaps, which under irregular Δt is variable per window and data-dependent. The Takens embedding loses coherence (fixed-τ assumption violated). To regain any Δt awareness P4 must adopt Approach A; B/C are inapplicable (§6.3).

### 7.4 Q3(a) — regular time-series

Adequate **only** when the true dependency length is short and known to fit the window / compounded receptive field. Within `D` the lags are **exact** (no decay distortion), and the reach is **static, predictable, and parallel** — a genuine strength for short, sharp, known-length lag dependencies. It **fails** for long-range, unknown-length, or periodic/modular structure. The star-free/counter-free ceiling (Knorozova-Ronca Theorem 5, VERIFIED p.6) further caps horizon-relevant **expressivity** to threshold counting, never modular/periodic, at any `D`. Concretely: for a regularly-sampled series with true dependency length `L_true`, P4 is adequate iff `L_true ≤ D` (single unit) or `L_true ≤` the compounded cascade receptive field, and **fails for any periodic structure of period > 1 regardless of `D`** (the modular-counting impossibility — Knorozova-Ronca Thm 5 / Giles 1995).

### 7.5 Q3(b) — irregular-Δt datasets

**Structurally compromised.** The only measured grid-invariance result in the corpus (§8.7, `e_irr ≈ 1.15× e_reg`) validates the LMU alternative — the exact property a delay line lacks. P4's `D` taps mix unequal real-time intervals; the real-time reach is variable and data-dependent. Even with Approach A, P4 only *presents* the gaps; it does not gain continuous-time reach.

### 7.6 Q3(c) — the existing equities dataset (VERIFIED layout — finding H-F4)

The shipped equities generator (`juniper-data/.../generators/equities/generator.py`) emits the **flat 2-D** variant — canonical NPZ keys plus `y_reg_*` reshaped to `(-1, 1)` (line 198); each row is one ticker-day with 10 features. A `D ≤ 30` window over daily OHLCV spans **~30 trading days ≈ 6 calendar weeks** of lookback — **adequate in magnitude** for short-horizon next-day direction/return targets. But two horizon limits are concrete:

1. **The Friday→Monday gap is 3 calendar days while consuming one tap** (`_sequence.py:116`, weekends ⇒ 3), so 30 taps is **not** 30 calendar days and the real-time horizon drifts across windows.
2. **The prediction TARGET HORIZON is itself irregular** — `target_dt = ords[i+1] − ords[i]` (`_sequence.py:123`) is the gap to the predicted day. Over a weekend the model is asked to predict **3 calendar days ahead** from the same window **with no architectural signal that the horizon changed**. P4 has no mechanism to condition on `target_dt`; an Approach-A `dt`/`target_dt` feature is the minimum fix.

> **Data-readiness caveat (VERIFIED):** the 3-D windowed building block (`_sequence.py`) exists and is leakage-tested, but the sequence consumer `equities_seq` is **NOT present** in the generators directory (`arc_agi, checkerboard, circles, csv_import, equities, gaussian, mnist, moon, spiral, xor` — no `equities_seq`). So the 3-D contract produces **no artifact yet**, and the cascor side **cannot ingest `ndim > 2`**. Both ends of a P4 pipeline are currently stubs/blockers for the windowed path.

### 7.7 Horizon vs the alternatives (VERIFIED LMU figures — finding H-F5)

P4's hard FIR cliff at `D ≤ 30` is **dramatically shorter** than the IIR/continuous-memory alternatives. VERIFIED from the LMU NeurIPS-2019 paper abstract: LMUs "efficiently handle temporal dependencies spanning **100,000 time-steps**" and improve memory capacity by two orders of magnitude over equally-sized LSTMs; the LMU's reach is set by a **continuous window length θ** and fidelity by memory order `d`, so its horizon is **decoupled from a discrete tap count** — the opposite of P4, where horizon == tap count == `D ≤ 30`. P3-style fading-memory reservoirs similarly carry a nonzero decaying response past any fixed window. **On raw horizon, P4 is the weakest of the surveyed memory mechanisms;** its only horizon-relevant advantage is that within `D` the lags are exact.

**Q3 answer.** P4's effective horizon is a **windowed-feedforward receptive field hard-capped at `D ≤ 30` samples per node** (compounded uncontrollably by cascade depth), **not** recurrent reach. It is adequate for short, sharp, known-length, regularly-sampled dependencies; inadequate for long-range, periodic/modular, or irregularly-spaced structure; and for equities it is magnitude-adequate (weeks of lookback) but **blind to the irregular Friday→Monday gap and, more seriously, to the irregular target horizon `target_dt`**.

---

## 8. Mini-Batch — Answer Q4

### 8.1 Batch axis ⊥ time axis (VERIFIED framing — finding L4-F1)

The corpus establishes batch and time as orthogonal axes of the 3-D tensor: the **batch axis** = independent windows/sequences (shuffleable, parallelizable, no cross-talk); the **time axis** = within-window steps bound by `h_t = f(x_t, h_{t-1})` (inherently sequential). For P4 the delay register is filled by sequential evaluation within a window, so the **time/lag axis is order-sensitive** while the **window/sequence (batch) axis is fully shuffleable**. Mini-batching parallelizes across windows; it must **never reorder the within-window step sequence**. P4 mini-batching is valid IFF the data-loader batches whole windows and never shuffles timesteps inside a window. (Axis-order note: the corpus prose orders the tensor `(time, batch, features)` (PROPOSALS §5), while the shipped data contract uses `(n_windows, L, F)` = `(batch, time, features)` (`_sequence.py`). The two differ in ordering, not semantics; P4's flatten-to-2-D collapses the lag axis into feature columns regardless of which convention the loader adopts.)

### 8.2 The central tension is real in the live code (VERIFIED — finding L4-F2)

cascor today has **no DataLoader** and treats every row as an exchangeable i.i.d. sample: `fit()` runs full-batch over the whole tensor (`cascade_correlation.py:1875, 1903`), and the correlation objective flattens output and error across the whole batch and computes a single `torch.dot`, which is **invariant to row order** (`candidate_unit.py:935-941`). Rows are fully exchangeable today. This is exactly the "collapse batch and time" hazard the corpus names: "feeding a series as independent batch rows yields a windowed feed-forward model (TDNN), not recurrence" (PROPOSALS §5). Any P4 data-loader that flattens (window, timestep) into independent rows for the forward pass reproduces this hazard.

### 8.3 P4's saving grace: post-selection attach keeps candidate training in today's form (VERIFIED — finding L4-F3)

Because P4 attaches the register only AFTER the candidate pool is trained and the best correlation candidate selected, and the register has no feedback into the candidate's own activation, **candidate training never sees the lag axis and remains a stateless scalar-output correlation fit**. The candidate forward (`candidate_unit.py:479`) and the order-invariant correlation (`candidate_unit.py:935-941`) are unchanged, so candidate-pool mini-batching stays exactly as today: rows exchangeable, no time-ordering contract needed during selection. **This is P4's genuine mini-batch advantage over P1/P2/P3**, all of which require live recurrence (and therefore a time-ordering contract + recurrence-aware gradient) DURING candidate training. The mini-batch burden for P4 is confined to (a) the inference/forward time-loop that fills the register, and (b) the worker payload.

### 8.4 The output-layer static solve stays batchable, and the D-inflation cost is paid once (VERIFIED — finding L4-F4)

With the register frozen at install time and no output feedback, output-layer training stays a static MSE fit and the readout rows can be flattened and shuffled freely. In the live code, `train_output_layer` hoists `output_input = self._compute_hidden_outputs(x)` **once** above the epoch loop (`cascade_correlation.py:2051`) because frozen-unit outputs are constant across output-training epochs (the CR-060 optimization); the per-epoch loop then only re-runs the cheap `nn.Linear` matmul + MSE. **For P4 the `D`-inflated fan-in is materialized once per output-training pass, not per-epoch.** The only required change is sizing the rebuilt `nn.Linear(input_size, ...)` (≈2032) and `output_weights` to the inflated width. The static solve imposes no new ordering constraint.

### 8.5 Memory cost is trivial; the structural widening is the real cost (INFERRED — finding L4-F5)

Per-node buffer memory is `D · n_units · batch` activations. For the ratified regime (`D ≤ 30`, padded-to-30 windows), with ~30 units and batch `B`, the inflated activation block is `~30·30·B = 900·B` float32 ≈ **3.6 KB · B** — memory-trivial at typical batch sizes. The cost is bounded and batchable, but it (1) **widens every downstream weight vector and the output matmul**, and (2) frozen trajectories over time cost an extra factor of `T` memory (computed once, cacheable). The buffer memory is not a blocker; the structural fan-in widening (every consumer indexes `D` columns per unit, not 1) is.

### 8.6 The hard blocker: 3-D worker payload (VERIFIED — finding L4-F6)

If P4's mini-batch data path ever ships a 3-D windowed tensor `(n_windows, T, F)` to the parallel/remote candidate workers — which a windowed forward time-loop requires once candidates need pre-windowed input — it hits a hard rejection. `SharedTrainingMemory.__init__` raises `ValueError("SharedTrainingMemory only supports tensors up to 2 dimensions")` for any `ct.ndim > 2` (`cascade_correlation.py:272-273`), and its 32-byte descriptor struct `"<QQBBII6x"` stores **only `shape_0` and `shape_1`** (`cascade_correlation.py:303-317`), structurally capping the format at rank 2. The current candidate task path feeds exactly `[candidate_input, y, residual_error]` through this block (≈2224-2227). The corpus flags the worker 3-D payload + time-ordering contract as the heaviest new bookkeeping item, and **OQ-11 ("Is recurrent unit training parallelizable via cascor's worker protocol?") is open/unknown** (REFACTOR §2.9). P4's post-selection attach AVOIDS this **only as long as candidate IO stays strictly 2-D**.

### 8.7 T=1 subsumption (VERIFIED — finding L4-... / RATIFIED constraint)

`T = 1` cleanly subsumes to today's mini-batch behavior. At `T = 1` the window is a single timestep, so the register depth **`D` necessarily collapses to `1`** (one tap = the current activation, no lag axis); the fan-in width arithmetic is then unchanged and the 2-D path stays **byte-identical**. (`T` is the window/sequence length; `D ≤ window` is the register depth — distinct axes that coincide only at this `T = 1` boundary.) This satisfies the hard backward-compatibility constraint (PROPOSALS §6/§7.1).

### 8.8 Readout mask / variable output stride — an open mechanical question (OPEN)

The corpus makes `readout_mask` / `seq_lengths` the variable-output-stride mechanism and a hard part of the 3-D contract (PROPOSALS §7.1; DELTA-T §6.1). For a stateless-per-window FIR embedding whose units each emit `D` columns per timestep, the masked correlation/MSE applies **at the masked readout positions** over the flattened `(window × readout-position, Σ D_i)` rows. **OPEN:** whether the static output solve runs **per-readout-position** (one row per masked step — dense state, sparse supervision) or **per-window-aggregate** (one row per window at its final readout). The P4 description does not resolve this; it is recorded as a P4-specific open question (§18.2).

**Q4 answer.** Mini-batching **across windows is sound and shuffleable**, and P4's loader change is **lighter than any recurrent proposal** (candidate training and the worker path stay untouched for 2-D IO). But it is **NOT free**: a new **window-batched, time-ordered, padded/masked loader** plus a **forward time-loop** replacing the order-agnostic row-wise `_compute_hidden_outputs` are required, and the existing `ndim ≤ 2` worker cap **blocks any 3-D candidate/activation transport**.

---

## 9. Strengths

All VERIFIED unless noted.

1. **Least-disruptive integration on the hardest surfaces.** P4 is the only proposal whose candidate-training **objective** and **both** worker transports stay untouched (the candidate input-*sizing* must still resync after the first `D > 1` install — §12 T10 — but the objective and the worker IO do not change). It alone avoids the recurrence-aware candidate gradient (BPTT-over-window; RTRL deferred per PROPOSALS §8) that P1/P2/P3 all require, because the delay-line is attached AFTER best-correlation selection. It sidesteps the OPT-5 shared-memory `ndim > 2` hard-reject (`cascade_correlation.py:272-273`) that the lag-aware candidate inputs of P1/P2/P3 would collide with. This matches the corpus's strongest tractability finding: "live recurrence exists only in candidate training" (PROPOSALS §5). (findings L1-F6, L4-F3, L1-F3)
2. **The node's internal activation math is genuinely untouched.** `candidate_unit.py:479` and `cascade_correlation.py:1946` are byte-for-byte the scalar dot-product they are today; P4 feeds *that* scalar into its register. (finding L-AF-F3)
3. **Trivial C1 transparency.** A literal shift register of past activations is the most inspectable mechanism of the four — no learned temporal parameters, no ODE solver, no group machinery, no library black box. Fully compliant with C1 (MODEL/REFACTOR §0.3). Its transparency is never in question; only its expressive value is.
4. **Mechanism maturity as a family.** Finite-window convolution over activations is a well-understood, effective, explicitly non-recurrent temporal device (TDNN Waibel 1989; FIR nets Wan 1993; TCN/WaveNet Bai 2018 / van den Oord 2016, all web-verified). For pure regression with short fixed horizons it can work.
5. **Within `D`, the lags are exact** — no decay distortion. This suits short, sharp, known-length lag dependencies and is a real (if narrow) horizon advantage over fading-memory approaches.
6. **Cheap output-layer integration.** The CR-060 hoist (`cascade_correlation.py:2051`) means the `D`-inflated fan-in is materialized once per output-training pass, not per-epoch. (finding L4-F4)
7. **Clean `T=1` subsumption** — byte-identical to today's feed-forward cascor at `D=1`. (RATIFIED constraint satisfied)

---

## 10. Weaknesses

All VERIFIED or INFERRED-from-VERIFIED as flagged.

1. **It is NOT recurrence (the decisive weakness).** With no feedback into the node's own activation (`candidate_unit.py:479` / `cascade_correlation.py:1946` are state-free), P4 is FIR/finite-memory, failing the dynamical-system state-evolution test (Knorozova-Ronca p.2). It is exactly the TDNN pattern the corpus labels "not recurrence" (PROPOSALS §5). Marketing P4 as "recurrence" commits the precise "collapse batch and time" error cascor is primed for. (finding L1-F1, VERIFIED)
2. **It does NOT advance OQ-4.** P4 inherits the star-free/no-count ceiling (like P1/P3) AND additionally lacks even fading-memory state, making it the weakest of all four on expressivity. Since OQ-4 reopened precisely because the ceiling is architectural, a FIR window contributes nothing to the question that motivated the exploration. (finding L1-F3 / §17, INFERRED from VERIFIED theorems)
3. **Worst irregular-Δt position.** Indexes by sample position, not elapsed time; under irregular Δt the `D` taps span an inconsistent real-time horizon; cannot use Approaches B or C, only A. The one empirically-verified irregular-Δt result in the corpus belongs to P3's LMU/Approach-C. (findings Q2-F1, Q2-F4, VERIFIED)
4. **Sharpest/shallowest horizon.** Hard cap at `D ≤ 30` with no decay tail (FIR), versus P3's beyond-block fading/continuous memory (LMU: ~10⁵ steps) and P1/P2's indefinite state. (findings H-F1, H-F5, VERIFIED)
5. **Breaks the constructive contract.** The unit is correlation-selected for instantaneous fit, then given a temporal apparatus the objective never evaluated; temporal credit is deferred to the static output solve and a later candidate one cascade-layer late, capping discoverable structure to one-layer-late FIR taps — strictly weaker than P1. (findings L-COH-F1/F2/F3, VERIFIED)
6. **The "(N+1)-D output" misframing.** A literal extra tensor axis is incompatible with three live consumers; P4 is only implementable as a feature-axis flatten (`+D_i` columns), which inflates parameter count per unit from `O(input_size + k)` to `O(input_size + k·D)`. (findings L-AF-F2, L-AF-F5, VERIFIED)
7. **Multi-site lockstep change.** Three independent `+1`-column-per-unit width sites must all move to `+D_i`, including one (`train_output_layer`, line 2024) that re-derives width independently of the tensor it must match — easy to miss, silent mismatch on partial change. (findings L-AF-F1, L1-F2, VERIFIED)
8. **The "leaves all functionality intact" claim is misleading.** True only for the node's internal scalar math; false for the node-as-network-citizen (downstream weight lengths, output width, frozen dict, RC-5 guard, snapshot connectivity). (finding L-AF-F3, VERIFIED)

---

## 11. Risks + Guardrails

| # | Risk | Severity | Evidence | Guardrail |
|---|------|----------|----------|-----------|
| R1 | **Mislabeling P4 as "recurrence"** in docs/code, committing the "collapse batch and time → TDNN, not recurrence" error | HIGH (conceptual) | PROPOSALS §5; FIR/IIR defs; `candidate_unit.py:479` state-free | Rename consistently to "output delay-line / lag-embedding (FIR)"; add a docstring banner on the module asserting "finite-memory, NOT recurrent (no feedback)"; lint for the word "recurrence" near the module |
| R2 | **Assuming P4 resolves OQ-4's ceiling** | HIGH | Knorozova-Ronca Thm 4/5 (PDF p.6); Giles 1995; DELTA-T §4.5 | Document explicitly that P4 inherits star-free; do NOT close OQ-4 on a P4 ship; reserve P2 (groups) as the ceiling answer |
| R3 | **Silent output-width mismatch** when the three width sites are not changed in lockstep (esp. line 2024) | HIGH | `cascade_correlation.py:1940, 2024, 4079` | Add an assertion `output_weights.shape[0] == input_size + Σ D_i` at the top of `train_output_layer` and after every resize; unit test the invariant |
| R4 | **Restored network loses per-node `lag_depth`** → fan-in width mismatch on load | HIGH | `snapshot_serializer.py:447-486` persists only 4 keys; connectivity `= len(unit["weights"]) if "weights" in unit else 0` at line 371 | Extend `_save_hidden_units` + loader to round-trip `lag_depth`; round-trip test (save → load → forward identical) on every output-training snapshot (line 2100) |
| R5 | **RC-5 stale-candidate guard fails** because the next pool was sized for pre-expansion width | HIGH | `cascade_correlation.py:4121-4124` | Thread lag width into candidate input-sizing *before* the next pool is created; test that grow → install (D>1) → grow does not raise |
| R6 | **3-D worker payload hits `ndim ≤ 2` cap** if any windowed candidate input is introduced | MEDIUM | `cascade_correlation.py:272-273, 303-317` | Keep candidate IO strictly 2-D; assert `candidate_input.ndim == 2` before dispatch; gate any future 3-D path behind an explicit shm-format extension (OQ-11) |
| R7 | **Cross-window lag leakage** if the loader shuffles timesteps or carries state across windows | MEDIUM | PROPOSALS §7.1 (stateless per window); `_sequence.py` L-axis ordering | Stateless-per-window loader: reset register to `h₀=0` per window, zero-pad partial fills, never shuffle within a window; property test (no cross-window dependency) |
| R8 | **Irregular-Δt bias** (3-day gap ≡ 1-day gap) goes unnoticed | MEDIUM | Q2-F1 (`cascade_correlation.py:1943-1946`); Takens uniform-τ | Adopt Approach A (`dt`/`target_dt` as features); add a "shuffle-`dt` degradation" guardrail test (performance must drop when `dt` is randomized iff the model uses it) |
| R9 | **Over-claiming horizon** for long-range or periodic structure | MEDIUM | H-F1/H-F5; Knorozova-Ronca Thm 5 | Document the hard `D ≤ 30` cliff; add a parity/modular-counting negative test that P4 is expected to fail |
| R10 | **`D > 30` design figure** (the "~35" in the P4 doc) violates the ratified window | MEDIUM | Paul's ruling; PROPOSALS §6/§7 (N≈30) | Enforce `D ≤ window ≤ 30` at construction; assertion + config validation (see §15) |

---

## 12. Integration Challenges — Per Touch-Point (file:line)

All file:line references VERIFIED by opening the live files this session. Repo root: `/home/pcalnon/Development/python/Juniper/juniper-cascor/src/`.

| # | Touch-point | File:line | Change required | Effort |
|---|-------------|-----------|-----------------|--------|
| T1 | Node/candidate activation math | `candidate_unit/candidate_unit.py:479`; `cascade_correlation/cascade_correlation.py:1946` | **NONE** — scalar activation is the register's input | — |
| T2 | Candidate correlation-training loop (single-shot autograd, no BPTT) | `candidate_unit/candidate_unit.py:528-679, 897-969, 977-1069` | **NONE** — P4 attaches post-selection; candidate trains on today's 2-D fan-in | — |
| T3 | Fan-in buffer (1 col/unit, 2-D) | `cascade_correlation/cascade_correlation.py:1940-1946` | Allocate `input_size + Σ D_i` columns; per-unit `D_i`-wide block slice instead of `buffer[:, col]` | HIGH |
| T4 | Cascade weight-length invariant | `cascade_correlation/cascade_correlation.py:945-958 (esp. 952), 1945` | Downstream units' `input_size`/`weights` grow by `D` per predecessor, not 1 | HIGH |
| T5 | 2-D input validator | `cascade_correlation/cascade_correlation.py:1632-1633` | **NONE if** lags folded into feature columns; MUST RELAX if a 3-D network input is ever introduced | LOW/— |
| T6 | Output matmul | `cascade_correlation/cascade_correlation.py:1979` | **NONE** — works once fan-in is flattened 2-D | — |
| T7 | Output-layer width (re-derived independently) | `cascade_correlation/cascade_correlation.py:2021-2024, 2032-2034` | `input_size += Σ D_i`; size rebuilt `nn.Linear` + `output_weights` to inflated width | MEDIUM |
| T8 | Output resize arithmetic | `cascade_correlation/cascade_correlation.py:4051-4086 (esp. 4079, 4149)` | `+num_added` → `+Σ D_i_added` | MEDIUM |
| T9 | Frozen-unit dict (4 keys) + install | `cascade_correlation/cascade_correlation.py:4032-4037`; signature `4000-4004` | Add `lag_depth`; thread `D` through `_install_hidden_unit` | MEDIUM |
| T10 | RC-5 stale-candidate guard | `cascade_correlation/cascade_correlation.py:4121-4124` (and `add_units_as_layer` ≈4297-4301) | Width check must account for `D`-wide predecessors; re-sync candidate sizing before next pool | HIGH |
| T11 | HDF5 snapshot schema | `snapshots/snapshot_serializer.py:447-486, 358-385 (connectivity 371)` | Persist/restore `lag_depth`; fix `input_connections = len(unit["weights"]) if "weights" in unit else 0` width accounting | MEDIUM |
| T12 | Local MP task tuple | `cascade_correlation/cascade_correlation.py:2204-2272, 3337-3435` | **NONE** (post-selection attach; candidates stay scalar 2-D) | — |
| T13 | OPT-5 shared-memory block | `cascade_correlation/cascade_correlation.py:272-273, 303-317` | **NONE as-described**; HARD `ndim ≤ 2` CAP blocks any future 3-D candidate input | — / BLOCKER |
| T14 | Remote WS wire + worker | `cascade_correlation/cascade_correlation.py:1162-1326`; `juniper-cascor-worker/.../task_executor.py:50-175` | **NONE** (workers train plain scalar candidates) | — |
| T15 | **NEW: forward time-loop substrate** | new code replacing/augmenting `_compute_hidden_outputs` row-wise eval | Window-time-aware, stateless-per-window, zero-pad partial fills, register fill in order | HIGH (Workstream-0) |
| T16 | **NEW: window-batched data-loader** | new code (no DataLoader exists today; `fit` is full-batch `cascade_correlation.py:1875`) | Batch whole windows, never shuffle within a window, padding + mask | HIGH (Workstream-0) |

**Single most important integration fact (VERIFIED):** "attach the module AFTER candidate selection, just before install" **breaks the next grow-iteration's contract** (T10). The grow loop trains the candidate pool against the current fan-in width, then installs and validates `candidate.weights.shape[0] == candidate_input.shape[1]` (`cascade_correlation.py:4121-4124`). If an installed unit's register widens the fan-in by `D > 1` columns, the next pool — trained against the pre-expansion width because P4 keeps candidate training scalar — fails that guard. So **lag-awareness must be threaded back into candidate input-sizing BEFORE the next pool is created**, which contradicts the "candidate training unchanged" framing for grow-iterations *after* the first `D`-wide install. (This is the rejected-finding L1-F1 nuance; it is listed in §17 but the underlying mechanism at lines 4121-4124 is VERIFIED.)

**Overall integration cost: MEDIUM-HIGH**, concentrated in the candidate-pool/fan-in resync (T10) and the new windowed forward substrate (T15/T16), not in any single touch-point.

---

## 13. Performance Bottlenecks

1. **Fan-in width inflation (the dominant cost).** Parameter count and the materialized fan-in tensor scale from `O(input_size + k)` to `O(input_size + k·D)` per unit (§3.4). At `D = 30` this is up to ~30× inflation of hidden-contributed fan-in and identical inflation of `output_weights` rows. (INFERRED from VERIFIED line 1945 cascade-read)
2. **Buffer memory is NOT a bottleneck.** `D · n_units · batch` float32 ≈ 3.6 KB · `B` at `D=30`, `n_units=30` — trivial (finding L4-F5). The *structural* widening, not the buffer, is the cost.
3. **Output-layer cost is paid once, not per-epoch.** The CR-060 hoist (`cascade_correlation.py:2051`) materializes the `D`-inflated fan-in once per output-training pass (finding L4-F4). The per-epoch loop is a cheap `nn.Linear` matmul + MSE over the inflated width.
4. **Forward time-loop replaces vectorized row-wise eval.** Today `_compute_hidden_outputs` is a single vectorized pass over an unordered batch. A stateless-per-window register fill requires iterating the time axis within each window (T15), adding a `T`-factor to the forward pass (computed once, cacheable for frozen units). (INFERRED, high confidence)
5. **Worker parallelism is preserved for 2-D candidate IO** (T12/T13/T14), but **forfeited for any 3-D windowed candidate input** (the `ndim ≤ 2` cap, finding L4-F6). OQ-11 (worker parallelizability of recurrent training) is open.
6. **Cascade depth compounds forward cost** super-linearly because each later unit reads all predecessors' `D`-wide columns (`cascade_correlation.py:1945`). (INFERRED)

---

## 14. Dataset Constraints

All VERIFIED.

1. **cascor today is strictly 2-D `(batch, features)`.** Enforced at `_validate_tensor_shapes` (`cascade_correlation.py:1632-1633`), at the spiral data provider (`spiral_problem/data_provider.py:200-205`, exactly 2 feature columns, `ndim == 2`), and at the shared-memory cap (`cascade_correlation.py:272-273`). The legacy 2-D path must remain **byte-identical** (ADDITIVE-only contract; `X.ndim` dispatch; DELTA-T §6.1).
2. **The 3-D windowed contract exists but is unwired.** `_sequence.py` (`juniper-data/juniper_data/generators/_sequence.py`) constructs `(n_windows, L, F)` 3-D `X` plus `dt`, `target_dt`, `observed_mask`, `ticker_code`, and is leakage-tested via `test_sequence_windowing_leakage.py` (Hypothesis property test, `max_examples=200`, invariants I1-I5). But the sequence generator `equities_seq` is **absent** from the generators directory — the 3-D contract produces **no artifact yet**.
3. **The shipped equities generator is the flat 2-D variant.** `equities/generator.py` emits canonical NPZ keys plus `y_reg_*` reshaped to `(-1, 1)` (line 198). Each row is one ticker-day (10 features); the Friday→Monday gap is implicit, recoverable only by diffing the separate `date_*` array.
4. **The `dt` channel a P4+Approach-A path needs is available** from `_sequence.py:114-116` (`dt[0]=0`, `dt[1:]=np.diff(win_ords)`; weekends ⇒ 3) with `target_dt` at `:123`, validated by invariant I3 — but only on the (unwired) 3-D path.
5. **No POC currently exercises temporal/recurrent behavior.** Exhaustive grep over `juniper-cascor/src/**/*.py` for `recurren|shift.?register|delay.?line|lag|timestep|temporal` returns only the incidental filename `test_swap_dataset_live.py` — zero matches in any cascade/candidate/parallelism source module. Both ends of a P4 pipeline are currently stubs/blockers for the windowed path.

---

## 15. The D ≤ 30 / Stateless-Per-Window Reconciliation (HARD Constraint)

**The ratified constraint (Paul, this session; corpus PROPOSALS §6/§7.1):**

- **Variable time window, `T ∈ 1..~30`, STATELESS PER WINDOW** — state resets each window (`h₀ = 0`, reset per window); NO carry-across-windows. The batch axis is fully shuffleable; padding-to-30 + mask is the only bookkeeping.
- **`D ≤ window length ≤ 30`** — the delay-register depth must fit within the window.
- **Where valid length < `D`, the register is zero-padded** (partial fill).
- **`T = 1` must reduce to today's feed-forward cascor exactly** (subsumption).

**The "~35" reconciliation (VERIFIED corpus check + FLAG):** The corpus ground-truth figure is **`N ≈ 30`** (PROPOSALS §6/§7; MODEL §1.6; REFACTOR §2.4). **No "~35" figure appears anywhere in the four corpus notes** — it originates in the P4 design description, which is *outside* this corpus. Therefore Paul's ruling to "drop ~35 to ≤ 30" is **already consistent with corpus ground truth**: analyze P4 under `D ≤ 30`, register filling within one stateless window, zero-padded where valid length < `D`.

**What the constraint forces (VERIFIED + INFERRED):**

1. **The ordered axis MUST be an explicit within-window time axis, folded into feature columns** — it **cannot** be the batch axis (which stays shuffleable per PROPOSALS §7.1). cascor today flattens everything to `(rows, features)` and treats rows as i.i.d. (VERIFIED: correlation/MSE/buffer all row-agnostic). So P4 must add a **forward time-loop that respects within-window order while keeping cross-window shuffleability** — this is **Workstream-0 substrate, not a freeze-time attachment** (T15/T16).
2. **Stateless reset per window prevents cross-window lag leakage** and keeps the batch axis fully shuffleable (R7). The register fills from `h₀ = 0` within each ≤30-step window; partial fills (valid length < `D`) are zero-padded.
3. **`T = 1` ⇒ `D = 1` ⇒ no taps ⇒ byte-identical 2-D path.** Subsumption holds trivially: the fan-in width arithmetic is unchanged at `D = 1`, so the legacy path is preserved.
4. **`D ≤ 30` bounds the worst-case fan-in inflation** to ~30× per unit and the buffer memory to ~3.6 KB · `B` for 30 units — both acceptable.
5. **Construction-time enforcement** is required: assert `D ≤ window ≤ 30` and reject the design "~35" figure (R10).

**Net:** the D ≤ 30 / stateless-per-window ruling makes P4's register a **within-window FIR embedding** — which is internally consistent and avoids the stateful-continuous-stream interpretation entirely, but it does **not** change any of the Q1-Q3 verdicts: a finite within-window delay window is still FIR (Q1), still position-indexed and Δt-blind (Q2), and still horizon-capped at `D ≤ 30` (Q3).

---

## 16. Comparison vs P1/P2/P3 and Δt A-D

The matrix below is the load-bearing comparison. VERIFIED vs INFERRED is flagged per cell. P4-specific cells are INFERRED from P4's description against VERIFIED code/literature; P1/P2/P3 cells are VERIFIED against the corpus and the read PDFs.

| Axis | P1 (self-recurrent RCC) | P2 (group-implementing) | P3 (reservoir / LMU) | **P4 (output delay-line)** | Δt A→D |
|------|-------------------------|--------------------------|----------------------|----------------------------|--------|
| **Genuine recurrence (IIR vs FIR)** | **IIR, depth-1.** `V(t)=σ(Σ Iᵢwᵢ + V(t−1)·w_s)` (Fahlman p.192, VERIFIED PDF); "single state variable in an FSM." | **IIR + group state.** P1 substrate + cyclic-group (C2) units; strongest dynamical state but "P1's substrate + unproven group recipe." | **Genuine evolving state.** ESN `h=f(x,h_{t-1})` / LMU linear-memory ODE; "most genuinely recurrent." | **FIR ONLY — NOT recurrence.** Buffers last `D` outputs, no feedback. `candidate_unit.py:479` / `cascade_correlation.py:1946` state-free. Fails `x_t=f(x_{t-1},u_t)` (K-R p.2). TDNN per PROPOSALS §5. | N/A — A-D are Δt layers, not recurrent units (DELTA-T §4.5). |
| **Star-free / no-count ceiling** | INHERITS (Giles 1995: no state-cycle > 2; K-R Thm 5). | **The ONLY breaker** — but in-principle only (C2 sole concrete case; **no known training recipe**). | INHERITS (corpus corrects "avoids ceiling" → CATEGORY ERROR; fading memory ≠ counting). | **INHERITS AND weakest.** Threshold counting only (= counter-free, McNaughton-Papert 1971); no group, no feedback. | ORTHOGONAL for all (DELTA-T §4.5, VERIFIED). |
| **Fit with constructive process** | Fits but needs recurrence-aware candidate gradient (`w_s` trained during selection). Highest fidelity to "train for what you install." | Same substrate + **objective-less group-unit trainer** — worst recipe fit. | Good — only read-in/readout trained, mirrors cascor's static solve; sidesteps BPTT-through-frozen-units. | **DUAL.** WINS on candidate disruption (training *objective* stays today's static loop, VERIFIED `candidate_unit.py:1011-1063`; alone avoids the recurrence-aware gradient — BPTT-over-window, RTRL deferred — **but see T10: input-*sizing* resync after the first `D>1` install**). LOSES on contract — unit selected for instantaneous fit, temporal credit deferred to output solve + later candidate one layer late. | A cleanest (Δt is data); B perturbs freeze/ESP; C touches LMU only; D model-agnostic. |
| **Irregular-Δt** | Δt-blind by default (DELTA-T §4.3); needs A or B. | Same blindness as P1. | ESN assumes regular Δt; **LMU = the native hook** (Approach C, EMPIRICALLY VERIFIED §8.7: `e_reg=0.035`, `e_irr≈0.04`, grid-invariant). | **Δt-blind, worst-positioned.** Indexes by sample position; Takens fixed-τ premise violated; only A applies (B/C inapplicable to a pure buffer). The one measured §8.7 robustness belongs to P3-LMU. | This IS the A-D axis. Default A, principled C (DELTA-T §11). |
| **Effective horizon** | Indefinite-but-decaying (IIR tail), bounded by ceiling. | Indefinite, group-structured (unbounded period in principle). | Beyond block size via fading/continuous memory (LMU ~10⁵ steps, VERIFIED NeurIPS-2019). | **HARD-CAPPED at `D ≤ 30`, no decay tail** (FIR cliff). Sharpest but shallowest. | B sets a forgetting τ; C gives continuous window θ; A/D don't change horizon. |
| **Integration / code cost** | HIGH — temporal forward, recurrence-aware gradient, extended dict, snapshot, 3-D worker payload (Workstream-0). | HIGHEST — all of P1 + heterogeneous pool + nonexistent group forward/gradient. | HIGH but contained — block forward + static readout reuses output solve; larger stored object. | **MEDIUM, asymmetric.** WINS: candidate-training objective + both worker transports INTACT (avoids `ndim>2` shm cap `272-273`, VERIFIED; input-sizing must resync after the first `D>1` install, T10). LOSES: three `+1→+D` width sites in lockstep (`1940/2024/4079`), per-unit weight invariant, RC-5 guard (`4121-4124`), lag_depth in dict + serializer; `(N+1)-D` MUST flatten (matmul `1979`, gate `1632-1633`). | A LOWEST cost (one input dim); D data-side only; B/C heavier. |
| **C1 transparency** | Clean (one inspectable scalar weight + recurrence equation). | Clean-but-exotic (multiplicative neurons). | Clean (random-but-inspectable ESN; fixed Legendre matrix LMU). | **Cleanest/most trivial** — literal shift register, no learned temporal params, no solver. | All four C1-clean (DELTA-T §5). |
| **Training-recipe maturity** | MATURE (RCC published; BPTT standard; RTRL specified). | IMMATURE/NONEXISTENT (no recipe for group units). | MATURE (ESN/LMU published; readout mirrors cascor solve). | **SPLIT** — mechanism mature (TDNN/FIR/TCN) but the post-selection-attach variant is NOVEL/unpublished; not a corpus proposal. | A/C evidence-backed (§8.7); D mature but lossy. |
| **Overall risk** | LOW-MEDIUM (proven; inherits ceiling — fine for regression). | HIGH (breaks ceiling but no recipe; most speculative). | MEDIUM (genuinely recurrent, irregular-Δt-capable via C; doesn't break ceiling). | **MEDIUM mechanically, but a CORRECTNESS-FRAMING risk dominates** — low to ship, HIGH that it does not deliver the recurrence OQ-4 wants (it is FIR, inherits ceiling, Δt-blind, horizon-capped). | Lowest-risk A/D; higher B/C; all additive, none resolves OQ-4. |

**Δt approaches A-D (the separate axis, VERIFIED DELTA-T §5/§11):** A = `dt`-as-input (cleanest, models unchanged, weak bias); B = `dt`-gated exp decay (strong real-time-forgetting bias, perturbs ESP/freeze); C = solver-free continuous-time LMU (strongest bias, LMU-only, empirically verified §8.7); D = resample + impute (lossy, data-side, loses informative-sampling signal). Bias strength A < B < C. **For P4, only A is applicable.** All four are ADDITIVE and ORTHOGONAL to the ceiling.

**Comparative bottom line.** On genuine recurrence: P2 ≥ P1 ≈ P3 (all IIR/stateful) ≫ **P4 (FIR)**. On the ceiling: only P2 breaks it (no recipe); P1/P3/**P4** inherit. On irregular-Δt: P3-LMU/Approach-C is strongest (empirically verified); **P4 is worst-positioned**. On integration cost: **P4 is cheapest on the candidate/worker path** (its genuine edge). If the goal is genuine recurrence for OQ-4, **P1 (lowest-risk, ceiling-inheriting) or P3 (genuinely recurrent, regression-native, irregular-Δt-capable via C) dominate P4**; P4 only competes if the actual requirement is a cheap finite-window temporal feature for short, regularly-sampled regression.

---

## 17. Claims Considered and NOT Supported by Verification (Brief)

These were generated during analysis but **failed 3-vote refutation** or were demoted to non-load-bearing. They are listed for transparency; do not cite them as load-bearing.

- **"Attach-after-selection is NOT mechanically clean — it desyncs the next pool from the lag-widened fan-in and trips RC-5" (L1-F1, refuted as overstated).** The *mechanism* (the RC-5 guard at `cascade_correlation.py:4121-4124`, VERIFIED) is real and IS a genuine integration challenge (captured in §12 T10). The refutation: it does not make P4 un-implementable; it means lag width must be threaded into candidate sizing before the next pool — a known, bounded fix, not a fatal flaw. **Considered, partially supported (mechanism VERIFIED, "not clean" framing softened).**
- **"Labeling vs efficacy must be separated — P4 is in the effective TCN/WaveNet family" (rejected as a standalone finding).** This is *true* and is folded into §4.6 and §9; it was rejected only as a *separate refutation-surviving finding* because it restates the literature rather than adding a new verified fact. **Considered, supported, merged into §4.6.**
- **"P4 stays within the star-free ceiling" (L1-F3, listed as rejected-standalone but INFERRED-supported).** The underlying theorems (Knorozova-Ronca Thm 4/5; McNaughton-Papert counter-free) are VERIFIED; the *application to P4 specifically* is an INFERENCE (the corpus never names P4). It is load-bearing in §4.5 / §10 / §16 **as an inference**, flagged accordingly. **Considered, INFERRED-supported.**
- **"Cascade-compounding makes a deep nonlinear FIR filter bank with `Σ D_i` fan-in" (L-AF-F4, rejected-standalone).** The cascade-read at `cascade_correlation.py:1945` and the `Σ D_i` arithmetic are VERIFIED/INFERRED; the "filter bank" *characterization* is a sound inference but was not a refutation-surviving standalone finding. Used in §3.7 with an explicit caveat. **Considered, INFERRED-supported.**
- **"Post-selection attach is what makes P4 tractable" (L-AF-F6, rejected as duplicative).** True and folded into §9.1 / §16; rejected only as a duplicate of L1-F6. **Considered, supported, merged.**
- **Several per-finding restatements (L1-F4 snapshot, L1-F5 output-fit, L1-F6 mini-batch from the feasibility lens)** were demoted as duplicative of the surviving findings now in §11/§12/§8. **Considered, merged.**

No fabricated or unsupported claim is used as load-bearing anywhere in this document.

---

## 18. Recommendation + Open Questions + Suggested Guardrail Tests

### 18.1 Recommendation

1. **Do NOT label or ship P4 as "recurrence."** Rename it consistently to an **"output delay-line / finite-memory lag-embedding (FIR) module"** and document, in the module's own docstring, that it is finite-memory and **not** a recurrent (IIR / state-feedback) element (R1). This is the single most important framing correction.
2. **Do NOT treat a P4 ship as resolving OQ-4.** P4 inherits the star-free / no-count ceiling and adds neither group structure nor evolving state; it contributes nothing to the architectural concern that reopened OQ-4 (R2). Keep OQ-4 open; reserve P2 (group units) as the in-principle ceiling answer and P1/P3 as the genuine-recurrence answers.
3. **If a cheap, transparent, regularly-sampled finite-window temporal feature is genuinely what is wanted for short-horizon regression, P4 is a reasonable, low-risk choice** — and its post-selection-attach trick (untouched candidate training + worker path) is a real engineering advantage worth keeping. Build it as **feature enrichment**, with eyes open about the FIR ceiling and `D ≤ 30` horizon cap.
4. **For genuine recurrence / OQ-4, prefer P1 (lowest-risk, ceiling-inheriting, regression-benign) or P3 (genuinely recurrent, regression-native, irregular-Δt-capable via Approach C).** P3-LMU/Approach-C is the only path with *measured* irregular-Δt robustness in the corpus (§8.7).
5. **If P4 proceeds, adopt Approach A (`dt`/`target_dt` as input features) from day one** — it is the only Δt remedy compatible with a stateless buffer, and the `dt` contract already exists in `_sequence.py` (it just needs an `equities_seq` generator to be wired).
6. **Enforce `D ≤ window ≤ 30` at construction** and treat the design's "~35" figure as a defect to correct (the corpus is already at `N ≈ 30`).

### 18.2 Open questions

- **OQ-4 (REOPENED, under research):** the no-count/no-group ceiling is architectural; P4 does not address it. RCC-first pick is provisional; WS-0 not ratified (MODEL §1.6; REFACTOR Part 5).
- **OQ-11 (Unknown — investigate):** is recurrent (or windowed) unit training parallelizable via cascor's worker protocol? Directly gates any 3-D candidate payload against the `ndim ≤ 2` shm cap (REFACTOR §2.9).
- **OQ-6 (REFACTOR-owned):** which optional NPZ keys (`seq_lengths`, `padding_mask`, `scaling`) are in-scope for the additive 3-D contract a P4 windowed path would consume.
- **OQ-7 (MODEL-owned):** irregular-Δt relevance; the LMU affords a solver-free Approach-C path, so irregular-Δt support may be additive — but the long pole is the data contract (which `equities_seq` would supply).
- **P4-specific (network-level expressivity):** does the *aggregate* cascade (many frozen delay-lined units stacked in the DAG) stay star-free? The single-node FIR claim is solid; the network-level composition claim must be checked against the live implementation before it is asserted (per anti-hallucination rule 1 — not verified against a P4 implementation, which does not yet exist).
- **P4-specific (readout granularity):** for the stateless-per-window FIR variant, does the static output solve operate **per-readout-position** or **per-window-aggregate** once each unit emits `D` columns per timestep (§8.8)? Unresolved by the P4 description; bears on how `readout_mask` (PROPOSALS §7.1) folds into the flattened fan-in.

### 18.3 Suggested guardrail tests

1. **FIR/not-recurrence assertion test** — feed an impulse to a single P4 node; assert the output is exactly zero after `D` steps (confirms FIR, no feedback). (R1)
2. **Parity / modular-counting negative test** — a sequence task requiring counting mod `k`; assert P4 **fails** (documents the inherited ceiling so it is never silently over-claimed). (R9)
3. **`T=1` byte-identity test** — at `D=1`, assert the network output is byte-identical to today's feed-forward cascor on the 2-D path. (RATIFIED constraint)
4. **Output-width invariant test** — assert `output_weights.shape[0] == input_size + Σ D_i` after every install and resize; fuzz `D_i` per unit. (R3)
5. **Snapshot round-trip test** — save → load → forward; assert identical outputs and that `lag_depth` survives. Run on the snapshot created at `cascade_correlation.py:2100`. (R4)
6. **Grow-after-D>1-install test** — grow → install a `D>1` unit → grow again; assert the next pool does not trip the RC-5 guard (`cascade_correlation.py:4121-4124`). (R5)
7. **Stateless-per-window / no-leakage property test** — Hypothesis-style, mirroring `test_sequence_windowing_leakage.py`; assert no cross-window lag dependency and zero-padded partial fills. (R7)
8. **Shuffle-`dt` degradation test** — with Approach A, randomize the `dt` feature; assert performance degrades **iff** the model actually uses `dt` (catches the "presentation not mechanism" weakness). (R8)
9. **`ndim ≤ 2` candidate-IO guard test** — assert `candidate_input.ndim == 2` before any worker dispatch; assert a 3-D input raises the documented `SharedTrainingMemory` `ValueError`. (R6)
10. **`D ≤ 30` construction-validation test** — assert the module rejects `D > window` and `D > 30`. (R10)

---

## 19. References (Verified Only)

**Read PDFs (opened this session / corpus diligence):**

- S. E. Fahlman, "The Recurrent Cascade-Correlation Architecture," *NIPS* 3, 1990, pp. 190-196. `papers/NIPS-1990-the-recurrent-cascade-correlation-architecture-Paper.pdf` — pp. 191-192 read: plain cascor "has no short-term memory"; RCC self-recurrent feedback `V(t)=σ(Σ Iᵢwᵢ + V(t−1)·w_s)`; "single state variable in a finite-state machine."
- N. A. Knorozova, A. Ronca, "On The Expressivity of Recurrent Neural Cascades," arXiv:2312.09048v2, 2024. `papers/On The Expressivity of Recurrent Neural Cascades-2312.09048v2.pdf` — pp. 1-6 read: dynamical-system definition `x_t=f(x_{t-1},u_t)` (p.2); Theorems 3/4/5/6/7; positive-weight sign/tanh RNCs = exactly group-free = star-free; group/negative-weight units required to exceed it; cites Giles 1995.

**Web-verified (publisher/index pages + corroborating summaries; original PDFs not opened):**

- A. Waibel et al., "Phoneme Recognition Using Time-Delay Neural Networks," IEEE TASSP 37(3):328-339, 1989 — TDNN (tapped delay line, feed-forward).
- E. A. Wan, "Time series prediction ... internal delay lines," in Weigend & Gershenfeld (eds.), 1993/94, pp. 195-217 — FIR networks; FIR unfolds to static feed-forward.
- F. Takens, "Detecting strange attractors in turbulence," LNM 898:366-381, Springer, 1981 — delay-coordinate embedding; fixed-lag τ / uniform-sampling premise (statement verified via Wikipedia "Takens's theorem").
- S. Bai, J. Z. Kolter, V. Koltun, "An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling," arXiv:1803.01271, 2018 — TCN; causal convolution = FIR, finite receptive field, no recurrence.
- A. van den Oord et al., "WaveNet," arXiv:1609.03499, 2016 — causal dilated convolution (FIR).
- T. Lin, B. G. Horne, P. Tiňo, C. L. Giles, "Learning long-term dependencies in NARX recurrent neural networks," IEEE TNN 7(6):1329-1338, 1996 — NARX taps fed-back outputs ⇒ genuine recurrence (the FIR/IIR boundary case).
- C. L. Giles et al., "Constructive learning ... limitations of recurrent cascade correlation ...," IEEE TNN 6(4):829-836, 1995 — RCC cannot sustain state-cycles of period > 2 under constant input.
- S. C. Kremer, "Comments on ...," IEEE TNN 7(4):1047-1051, 1996 — second unrepresentable automata class.
- M. P. Schützenberger 1965; R. McNaughton, S. Papert, *Counter-Free Automata*, MIT Press, 1971 — star-free = aperiodic = counter-free; counter-free cannot count modulo > 1 (threshold counting only); verified via Wikipedia "Aperiodic finite-state automaton."
- FIR/IIR definitions — Wikipedia "Finite impulse response" ("no feedback ⇔ finite impulse response"); ScienceDirect "Infinite Impulse Response" (feedback/recursive).
- LMU — A. Voelker, I. Kajić, C. Eliasmith, "Legendre Memory Units," NeurIPS 2019 — abstract verified: handles dependencies spanning 100,000 time-steps; continuous window length θ decoupled from tap count.

**Live code (all VERIFIED by opening files this session; repo root `/home/pcalnon/Development/python/Juniper/juniper-cascor/src/`):**

- `candidate_unit/candidate_unit.py` — activation `:479`; init `:244-246`; correlation `:897-969 (dot :941)`; training loop `:528-679`; weight update / single-shot autograd `:977-1069 (graph :1011-1042)`.
- `cascade_correlation/cascade_correlation.py` — frozen-unit forward `:1946`; fan-in buffer `:1940-1946`; cascade read `:1945`; weight-shape invariant docstring `:952`; output matmul `:1979`; 2-D validator `:1632-1633`; output-width re-derivation `:2021-2024`; CR-060 hoist `:2051`; resize `:4051-4086 (4079, 4149)`; install / 4-key dict `:4032-4037`; RC-5 guard `:4121-4124`; SharedTrainingMemory `ndim>2` cap `:272-273`, descriptor `:303-317`; `fit` `:1795-1917 (1875, 1903)`; local MP tasks `:2204-2272`; remote WS `:1162-1326`; residual `:3964`.
- `snapshots/snapshot_serializer.py` — per-unit save `:447-486`; architecture/connectivity `:358-385 (371)`.
- `spiral_problem/data_provider.py` — 2-D enforcement `:200-205`.
- `juniper-cascor-worker/juniper_cascor_worker/task_executor.py` — worker training `:50-175`.

**Corpus notes (VERIFIED, repo `notes/`):**

- `JUNIPER_2026-06-04_JUNIPER-RECURRENCE_RECURSE-OQ4-RECURRENT-CASCOR-PROPOSALS.md` (PROPOSALS) — §2 (cascor today stateless), §3 (P1/P2/P3 defs), §4 (validation), §5 ("TDNN, not recurrence"; batch ⊥ time), §6/§7 (window N≈30, stateless-per-window, T=1 subsumption).
- `JUNIPER_2026-06-05_JUNIPER-RECURRENCE_RECURSE-DELTA-T-HANDLING.md` (DELTA-T) — §4.3 (no elapsed-time notion), §4.5 (orthogonality to ceiling), §5 (A-D table), §6.1 (`X.ndim` dispatch / `dt` keys), §8.7 (measured `e_reg`/`e_irr`/grid-invariance), §11 (recommendation A default, C principled).
- `JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md` (MODEL) — §0.3 (C1), §1.3.3-1.3.4 (LMU long-horizon; Approach-C), §1.6 (OQ-4 reopened, OQ-7).
- `JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` (REFACTOR) — §0.3 (C1), §2.4/§2.8/§2.9 (additive contract, OQ-6, OQ-11), Part 5 (status; grounding-pass line numbers not load-bearing).

**POC artifact (VERIFIED):**

- `util/ad-hoc/verify_delta_t_reference_code.py` (numpy-only LMU/windowing diligence; validates the LMU/Approach-C math, not P4).
- `juniper-data/juniper_data/generators/_sequence.py` + `tests/unit/test_sequence_windowing_leakage.py` (3-D windowed contract + leakage invariants I1-I5; building block only, `equities_seq` consumer absent).
- `juniper-data/juniper_data/generators/equities/generator.py` (flat 2-D output, `y_reg_*` reshaped `(-1,1)` at line 198).

> **Confidence flags.** HIGH on all FIR/IIR/Takens/RCC-ceiling characterizations and on the two fully-read PDFs (Fahlman; Knorozova-Ronca). MEDIUM-HIGH on web-only papers' exact page/volume (verified via index pages, original PDFs not opened) — except **Giles 1995 (IEEE TNN 6(4):829-836, DOI 10.1109/72.392247)** and **Waibel 1989 (IEEE TASSP 37(3):328-339)**, whose exact bibliographic details are web-VERIFIED. All cascor file:line claims VERIFIED against live files this session. Every **P4-specific** verdict is an INFERENCE from P4's stated description against VERIFIED code/literature (the corpus never names P4) and is flagged as such throughout. The **network-level** expressivity claim (aggregate cascade stays star-free) was NOT verified against a P4 implementation (none exists) and must be re-checked at implementation time.
