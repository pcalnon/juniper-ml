# Recurrent Cascade-Correlation — "P4" Delay-Line / Shift-Register Output Module: Design Evaluation

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 model-pick exploration; P4 design evaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-10

---

> **What this is.** An adversarial, anti-hallucination-gated evaluation of a *fourth* proposal — **"P4"** — for adding recurrence to Cascade-Correlation: a multi-step **delay element (shift register)** appended as the final output stage of a hidden node. It is evaluated as two arms (the design as written, plus a feedback variant requested 2026-06-09) and feeds the OQ-4 model pick. It **pairs with, and does not duplicate,** the three-proposal exploration in
> [`JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md`](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md) (P1/P2/P3) and the irregular-Δt analysis in
> [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md).
>
> **Headline verdict.** P4 is a sound, **C1-clean** way to give a cascor node *finite temporal memory* — but it is a **horizon / embedding mechanism, not a fix for the OQ-4 representational ceiling.**
> - **ARM A** (as written — the shift register *stores* past outputs, no feedback) is a **constructively-grown Time-Delay Neural Network (TDNN / FIR)**. It is *not* recurrence in the dynamical-systems sense.
> - **ARM B** (feedback — the taps feed back into the activation) is **genuine recurrence (IIR)**, a K-tap generalization of P1/RCC's single self-loop, but single-neuron-class and still ceiling-bound.
> - **Neither arm lifts the star-free / no-count ceiling, and neither is Δt-aware.** ARM A is nearly free to integrate and is mini-batch-friendly; ARM B needs a real recurrence-aware gradient plus worker/snapshot schema changes.
> - **2026-06-10 update — P5:** a *trained recurrent (NARX) output layer* added on top of the P4-FIR cascade (this doc's ARM A) **also does not lift the ceiling** — a single self-recurrent output node cannot form the `x(t)·o(t−1)` XOR cross-term parity needs. It buys only a modest fading-memory tail, at *lower* integration cost than ARM B (the worker subsystem is untouched). Full evaluation in the **P5 update section** below.

---

## 0. Provenance & method

- **16-agent adversarial workflow**: 4 grounding readers (cascor candidate unit, cascade orchestration, worker protocol, equities + Δt windower) → a numpy POC build + an independent re-run/validity check → 4 adversarial lenses (recurrence theory, codebase feasibility, Δt/horizon, mini-batch/perf), each evaluating **both arms**, pipelined into per-lens refuters → a cross-cutting citation/consistency auditor. ~2.2M tokens across build + recovery passes.
- **Empirical POC**: [`../util/ad-hoc/verify_delay_line_node_eval.py`](../util/ad-hoc/verify_delay_line_node_eval.py) — numpy-only, `SEED=20260609`, fully deterministic, re-run independently (E1 and E5 are hard asserts). Measured results in §10.
- **Anti-hallucination posture**: every load-bearing code claim was checked at `file:line` against the live `juniper-cascor` / `juniper-cascor-worker` / `juniper-data` trees; every literature claim is primary-source-verifiable; every number comes from measured POC output. The audit pass independently re-read the cited code lines and verified the disputed citations.
- **Four audit-flagged defects were corrected before writing**: (1) the Giles citation now reads IEEE TNN 6(4):829-836 (a wrong document-ID was dropped); (2) the LMU 1.15× grid-invariance number is attributed to Δt-doc **§8.7** (measured), not §8.6 (the test); (3) a fabricated "lag-34=1.000 / lag-35=0.156" boundary pair (never in the POC grid) is replaced by the actual measured `L30=1.00 → L35=0.18`; (4) a refuted "~100×" throughput figure is corrected to **~4×**.

> **Scope honesty (read before trusting any single claim).**
> 1. The OQ-4 ceiling result (E3) is established at the **single candidate node** level. A *deep cascade* of frozen P4 nodes composing nonlinearly was not exhaustively tested. Single-node is the correct granularity for "what does one P4 candidate contribute," but "P4 cannot count" is rigorously shown only there + by the literature.
> 2. The **IIR-specific Δt blindness is inferred**, not measured — E4 ran the FIR readout. (Open item: run E4 against `iir_rollout`.)
> 3. The equities numbers (E6) are **single-seed, single-ticker (AAPL, most-recent 2000 days capped), 2009-onward fundamentals zero-filled**, and the time axis is a POC stand-in for the streaming axis cascor does not yet have.
> 4. **cascor has no temporal substrate today** — this is the shared "Workstream 0" prerequisite for *every* recurrence proposal, P4 included.

---

## 1. The design as evaluated

### 1.1 Verbatim author description (Paul Calnon, 2026-06-07)

> Recurrent functionality is added to hidden nodes by introducing a multi-step delay element that borrows the effective functionality of a simple shift register. The delay element would be added as an additional, final output component of the node. This approach should leave intact all of the current functionality and structure of cascor hidden nodes — from input weights through the output activation function. The modified hidden node would generate its activation output exactly as it currently does. Rather than being passed directly to the downstream nodes, however, node output becomes the input to the node's new recurrence module. The number of previous samples considered by the module — the bit-wise size of the "shift register" which serves as the time series embedding dimension — is assumed to be finite and bounded; in practice on the order of 35. The recurrent module's output will be an ordered collection of the hidden node's output tensors. Effectively, the new, augmented hidden node should produce an N+1 dimension output tensor that adds a single dimension to the original hidden node's N dimension tensor. Candidate node training would proceed normally; when the best-correlation candidate(s) are selected, the recurrence module is added prior to integration into the existing cascor network.

### 1.2 The two arms

- **ARM A — P4-FIR (as written).** The node computes `a(t)=f(W·x(t))` exactly as today. The shift register *stores* its last `K` activations and emits the ordered vector `[a(t), a(t−1), …, a(t−K+1)]` (K≈35) to downstream consumers — the "N+1 dimension." **`a(t)` does not depend on its own past outputs → no cycle in the compute graph → a finite impulse response (FIR) tapped-delay-line.**
- **ARM B — P4-IIR (feedback variant).** The delayed taps feed *back* into the activation with learnable weights: `a(t)=f(W·x(t) + Σ_{k=1..K} v_k · a(t−k))`. This is genuine feedback recurrence (IIR) and a K-tap generalization of P1 (faithful RCC), whose single self-loop is the `K=1` special case.

---

## 2. Functionality & correctness — Q1 ("how correctly/effectively does this implement recurrence?")

### 2.1 ARM A is not recurrence — it is a grown TDNN

In signal-processing terms the augmented node is a **finite impulse response** filter on the node's activation: the output at time `t` is a (downstream-learned) function of `{a(t), …, a(t−K+1)}`, with **no feedback path**. A single node's temporal receptive field is exactly `K`. Because Cascade-Correlation *stacks* nodes and each new candidate may read a frozen node's taps, a cascade of delay-line nodes extends the receptive field **additively** — roughly `O(depth × K)` — exactly like a stack of 1-D temporal-convolution / TDNN layers. It is **never unbounded**. This is precisely the "windowed feed-forward (TDNN), *not* recurrence" pattern the proposals doc §5 warns about. TDNNs are a respectable, well-understood class (Waibel et al. 1989; the FIR/TCN family, Bai, Kolter & Koltun 2018 show such convolutional models are often competitive with RNNs) — so "not recurrence" is a *characterization*, not a dismissal: for **bounded-horizon regression** a grown TDNN may be entirely adequate.

- **E1 (measured): the tap embedding is exactly a precomputable window.** Sequential shift-register vs. vectorized `sliding_window_view` agree to `max|diff| = 0.00e+00`; the per-timestep activation is permutation-equivariant. ⇒ ARM A adds *no* recurrence to the gradient and is trivially batchable (see §5).
- **E2 (measured): the horizon is a hard cliff.** A pure fixed-lag recall task (`target = x(t−L0)`) gives FIR `|corr| = 1.00` for `L0 ∈ {1,5,10,20,30}` then collapses to `0.18` at `L0 = 35`. Structurally the register holds taps `0..K−1 = 0..34`, so exact recall is possible only up to lag `K−1 = 34`; the measured grid shows the collapse between 30 and 35.

### 2.2 ARM B is genuine recurrence — but single-neuron-class

ARM B has a real feedback loop, so it is a true IIR/recurrent unit and a strict generalization of P1's self-recurrent RCC candidate.

- **E5 (measured, hard assert): the recurrence-aware gradient is correct.** Analytic BPTT-over-window of the correlation loss through the K-tap recurrence matches central finite differences to `max rel err = 8.76e-10` (≪ 1e-5). So the feedback arm is *trainable* via the BPTT-over-window default the proposals doc §7 already commits to — but cascor has no such gradient path today (§6).
- **E2 (measured): feedback carries signal past K, but weakly.** IIR `|corr|` stays `0.4–0.6` across lags 1–30 and the `≥0.5` cutoff lands at only **lag 5** (single-seed, fixed training budget) — materially below FIR's exact-recall reach within the window. Feedback buys *fading memory beyond the window*, not *more reliable memory inside it*.

### 2.3 Both arms hit the OQ-4 star-free / no-count ceiling

- **E3 (measured): parity is unlearned at every `m`, and unbounded counting fails.** Parity of the last `m` bits gives FIR `|corr| ≈ 0.15–0.17` for **all** `m` (including `m=3`, inside the window) and IIR `|corr| ≈ 0.03–0.09`; an unbounded mod-3 count gives FIR `0.17` / IIR `0.14`.
- **Honest reading.** A single node + linear readout *cannot represent* parity at any `m` (parity is not linearly separable over the taps), and a single IIR neuron *does not learn* it here either. The POC shows **failure-to-learn**, which is *consistent with* — but **not a proof of** — the representational ceiling. The impossibility is the **literature's**: RCC captures exactly the star-free / group-free regular languages, i.e. no modulo/parity counting (Giles, Chen, Sun, Chen, Lee & Goudreau 1995, IEEE TNN 6(4):829-836; Kremer 1996; Knorozova & Ronca 2024, arXiv:2312.09048). ARM B inherits this (a sign-unconstrained self-loop can exceed star-free per Knorozova–Ronca's negative-weight neuron, but a single neuron still does not implement cyclic-group structure). **Neither arm adds group-implementing units, so neither lifts the ceiling.**

**Q1 answer.** ARM A does **not** implement recurrence — it is a finite delay-line embedding (FIR/TDNN) with a hard `~depth×K` horizon. ARM B **does** implement genuine feedback recurrence (correctly trainable via E5), but it is single-neuron-class (RCC neighborhood) and remains under the star-free/no-count ceiling. The design's stated goal — *leave the candidate-training process intact* — is **fully met by ARM A** (the candidate is trained exactly as today and the module bolts on afterward) and **only partly by ARM B** (candidate training must become recurrence-aware).

---

## 3. Irregular-Δt handling — Q2

Both arms index memory by **sample position**, not elapsed time: tap/lag `k` means "k samples ago," never "k time-units ago." On an irregularly-sampled series this conflates a 1-day step with a 3-day weekend gap.

- **E4 (measured, corrected experiment): index-tap delays are grid-dependent.** Reconstructing a value at a fixed **real-time** delay `τ` (the §8.6-style grid-invariance test, not an index lag), the FIR readout degrades **7.80×** from the regular to the irregular grid (RMSE `0.015 → 0.120`). Feeding `Δt` as an extra input channel ("Approach A") barely helps with a linear readout (**7.60×**). Contrast the variable-step LMU, which is grid-invariant by construction: `e_irr ≈ 1.15× e_reg` (Δt-doc **§8.7**, measured).
- **ARM B inherits the same blindness** (the self-loop lag is equally sample-indexed). This is *architecturally inferred*, not directly measured — see scope caveat (2).
- **The principled fix is not P4.** It is the Δt-doc's Approach A (cheap, learn-to-use) or Approach C (variable-step LMU, C1-clean continuous-time memory). P4 would need `Δt` plumbed as a feature at minimum; the equities NPZ carries dates but **no `dt` key** (`X_full(2928646,10) + y_reg_full + date_full`), so `Δt` must be derived.

**Q2 answer.** P4 (either arm) is **not Δt-aware**; on irregular grids it degrades sharply and the cheap `Δt`-as-feature mitigation is weak. Real-world relevance is concrete: equities daily bars are Fri→Mon = 3 calendar days (§4c).

---

## 4. Effective horizon of prediction — Q3 (a / b / c)

- **(a) Regular time-series.** ARM A: a **hard, finite** horizon ≈ `depth × K` (single node exact to lag `K−1 = 34`, E2; the cascade extends it additively). ARM B: **fading memory past K** but weak and decaying (E2 cutoff ~lag 5). Neither offers a long, reliable tail; for horizons inside `K`, ARM A's exact recall dominates.
- **(b) Irregular-Δt.** The horizon is **ill-defined in real-time units**: a fixed tap count spans a *variable* real-time window, so "how far back" jitters per step (the E4 degradation is the symptom). Without `Δt`-awareness the effective real-time horizon is uncontrolled.
- **(c) The equities dataset.** E6 (corrected, per-ticker **day axis**, AAPL most-recent 2000 days): next-day close is a near-perfect **persistence** target — `|corr(last_close, next_close)| = 0.999` — so the regression is dominated by random-walk persistence. The delay-line candidate adds little on the **residual/return**: FIR `|corr| = 0.196`, IIR `0.018`, and realized day-axis tap-`|corr|` vs. the residual is `≈ 0.001–0.003` at all lags. The `Δt` structure is real (1d 78.3% / Fri→Mon 3d 18.1% / holiday 4d 2.6%) but the lagged feature history carries essentially **no linear signal about next-day returns** — the well-known difficulty of return prediction, not a P4-specific failure. Single-seed/single-ticker caveat applies.

**Q3 answer.** ARM A's effective horizon is bounded and crisp (`~depth×K`, exact within the window); ARM B's is a weak fading tail beyond it. On irregular Δt the real-time horizon is uncontrolled; on equities the realized predictive horizon over these features is ≈ 0 for the return component.

---

## 5. Mini-batch processing & performance — Q4

- **ARM A is a strong mini-batch fit.** Because there is no feedback, the entire tap embedding is a **precomputable windowed `unfold`** (E1: precompute ≡ sequential, exact), each `(taps, target)` row is an independent sample, the batch axis is fully shuffleable, and **no BPTT is needed** — candidate training reuses cascor's existing single-shot autograd. The corrected lens estimate puts ARM A's candidate-training throughput edge over ARM B at roughly **~4×** (the originally-cited ~100× was refuted by its own checker).
- **ARM B forfeits this.** Genuine recurrence forces a **sequential BPTT-over-window** candidate trainer (time axis immutable; batch axis still shardable). It composes with cascor's freeze property — output-layer training stays a static solve regardless — but the candidate inner loop is now `O(T)` sequential.
- **Shared cost — ×K feature inflation.** Either arm makes a frozen node emit a `K`-vector instead of a scalar, so the frozen-feature space and the output-layer column count grow **×K** (K≈35). Each later candidate's input dimension grows `K×` faster, raising weight count, compute, overfitting risk, and worker payload size.

**Q4 answer.** ARM A: excellent — precompute + shuffle + no BPTT. ARM B: poor — sequential BPTT. The ×K inflation is the main shared performance tax.

---

## 6. Integration challenges & cost vs. the real cascor code

All locations verified against `juniper-cascor` (the 4-key dict and output-widen helper were re-read first-hand for this writeup).

**Today's reality (no temporal substrate).** Candidate forward is a stateless single-shot dot-product (`candidate_unit.py:244` flat 1-D weights, no `v_k`; `:479` stateless forward); candidate training builds one autograd graph and calls `loss.backward()` once (`candidate_unit.py:1011-1012`, `:1050`) with no BPTT; selection is `argmax|corr|` (`candidate_unit.py:739`); the network rejects `ndim > 2` inputs outright (`cascade_correlation.py:272-273`); the output buffer is 2-D, one column per unit (`:1941`, `:1946`); a **frozen unit is exactly a 4-key dict** `{weights, bias, activation_fn, correlation}` (`:4032-4037`, verified) and the output layer is widened by `num_added` columns on install (`_resize_output_layer_for_new_units`, `:4051-4086`, verified).

| Concern | ARM A (FIR) | ARM B (IIR) |
|---|---|---|
| Candidate gradient | **None** — single-shot autograd untouched; module bolts on post-selection | **New** — BPTT-over-window in the candidate trainer (validated in E5); cascor has none today |
| Frozen-unit record | +1 field (tap config / `K`) on the 4-key dict | +`v_k` recurrent weights on the 4-key dict |
| Snapshot / restore | tap field must thread through install → save → load | **Risk**: `snapshot_serializer.py` (`src/snapshots/`) `_load` rebuilds a unit from the 4-key schema, so an un-threaded 5th field (`v_k`) is **silently dropped on restore** — a provable data-loss path that must be closed |
| Hidden-output compute | `_compute_hidden_outputs` becomes a time loop producing `(B,T,n_units,K)` taps; frozen trajectories cacheable | same, plus a stateful recurrent forward |
| Output layer | widen by `K×` columns per unit (extend `:4051-4086`) | same |
| Worker protocol | 3-D `(B,T,F)` payload + ordering contract | same payload **plus** the recurrent forward + recurrence-aware gradient deployed worker-side; `task_executor.py` (worker) result tensor carries only `weights/bias/norm_output/norm_error` — **no `v` slot** |
| Input contract | reject-`ndim>2` (`:272-273`) must learn the 3-D path | same |

**Net integration cost.** ARM A ≈ *additive and localized* (schema + buffer width + a tap-emit step; the candidate process is genuinely untouched, honoring the design's stated goal). ARM B ≈ *materially heavier* (a second gradient path, worker-side recurrence, snapshot schema with a real silent-drop hazard) — essentially "build the temporal substrate **and** a recurrent candidate trainer."

---

## 7. Strengths / weaknesses / risks / guardrails

### ARM A — P4-FIR

| Strengths | Weaknesses |
|---|---|
| C1-clean (a shift register is elementary) | Not recurrence — finite TDNN; hard `K−1=34` horizon |
| Candidate training **unchanged** (design goal met) | Does not lift the OQ-4 ceiling |
| Mini-batch trivial: precompute + shuffle, no BPTT (E1) | Not Δt-aware (E4 7.8× degradation) |
| Lowest integration risk; additive schema | ×K feature/column inflation |

- **Risks**: ×K input-dim blowup → overfitting on deeper cascades; "selected on instantaneous corr, then taps bolted on" means the taps were never part of the selection objective.
- **Guardrails**: cap `K` and monitor frozen-feature dimensionality; conformance test that `K=1` (or `T=1`) is byte-identical to today's cascor; ablate "candidate selected with taps vs. without."

### ARM B — P4-IIR

| Strengths | Weaknesses |
|---|---|
| Genuine recurrence; trainable (E5 BPTT correct) | Heavy integration (new gradient + worker + snapshot) |
| Fading memory beyond `K` | Memory past `K` is weak/decaying (E2 cutoff ~5) |
| Generalizes P1; same freeze-localization story | Same ceiling; not Δt-aware |
| Output training stays a static solve | Snapshot 5th-key **silent-drop** data-loss hazard |

- **Risks**: hand-rolled/BPTT gradient bugs; recurrence stability (clamp `v`); worker divergence if the recurrent forward isn't deployed identically.
- **Guardrails**: gate behind an E5-style gradient conformance test (BPTT ≈ finite-diff); a snapshot round-trip test asserting `v_k` survives; `T=1`-identity migration.

---

## 8. Performance bottlenecks & dataset constraints

- **Bottlenecks**: (1) ×K frozen-feature inflation (compute, memory, worker payload); (2) ARM B's sequential BPTT inner loop; (3) cached frozen trajectories cost ×T memory (paid once, reused across the pool).
- **Dataset constraints**: cascor's `ndim>2` rejection (`:272-273`) blocks 3-D today; the equities NPZ is flat `(2,928,646 × 10)` with **no time axis and no `dt` key** — sequences must be re-windowed **per ticker** (no cross-ticker taps) and `Δt` derived from `date_*` (see Δt-doc §6.3/§7). All of this is **Workstream 0** (the temporal substrate), shared by every recurrence proposal.

---

## 9. Position vs. P1 / P2 / P3 — does P4 belong in the OQ-4 set?

- **P4-FIR is *weaker* than P1.** P1 is genuinely recurrent (a real self-loop); P4-FIR has no feedback and is the "windowed feed-forward (TDNN)" the proposals doc §5 explicitly flags as *not* recurrence. Its appeal is orthogonal to expressivity: **lowest integration risk + best mini-batch story**.
- **P4-IIR ≈ P1, generalized.** A multi-tap self-loop is a higher-order RCC candidate; same ceiling, strictly more parameters and integration cost than P1's single `w_jj`. If feedback is wanted, P1 is the cheaper entry point and P4-IIR the richer-memory upgrade.
- **P4 is neither P2 nor P3.** It adds no group-implementing units (P2, the only ceiling-breaker, still has no training recipe) and no intrinsic-state reservoir/fading-memory block (P3).

**Recommendation.** Record P4 in the OQ-4 set as **"P4 — delay-line / TDNN-ization,"** with ARM A positioned as *the low-risk, mini-batch-friendly, bounded-horizon-regression option* and ARM B as *a heavier generalization of P1*. **If the star-free ceiling is acceptable for bounded-horizon time-series regression** (the hinge the proposals doc identifies), **ARM A (P4-FIR) is the cheapest, most cascor-faithful way to add temporal reach** — provided `Δt`-awareness is added separately (Approach A/C) and `K` is capped. It does not replace P1/P3 on expressivity; it competes on integration cost and throughput.

---

## 10. POC results (measured — `util/ad-hoc/verify_delay_line_node_eval.py`, seed 20260609, numpy 2.4.4)

```
E1 precompute ≡ sequential : max|diff| = 0.00e+00 (shuffled 0.00e+00)        PASS (hard assert)
E2 FIR horizon             : L1..L30 = 1.00 ; L35 = 0.18  → hard cliff at K−1 = 34
E2 IIR horizon             : L1:0.59 L5:0.64 L10:0.47 L20:0.48 L30:0.42 ; ≥0.5 cutoff = lag 5
E3 parity (m = 3..60)      : FIR ≈ 0.15–0.17 / IIR ≈ 0.03–0.09 at ALL m (incl. in-window m=3)
E3 mod-3 count (unbounded) : FIR 0.17 / IIR 0.14  → neither solves counting (ceiling)
E4 irregular-Δt (real-time): reg RMSE 0.015 → irr 0.120 = 7.80× ; +dt 7.60× ; LMU §8.7 = 1.15×
E5 IIR BPTT vs finite-diff : max rel err = 8.76e-10                          PASS (hard assert)
E6 equities Δt distribution: 1d 78.3% / 3d (Fri→Mon) 18.1% / 4d (holiday) 2.6%
E6 AAPL (2000 days)        : baseline |corr| 0.999 ; delay-line on residual FIR 0.196 / IIR 0.018 ;
                             realized day-axis tap-|corr| vs residual ≈ 0.001–0.003 at all lags
```

Validity notes: E1/E5 are exact asserts; E4 uses a fixed **real-time** delay target (an index-lag target would be matched by an index tap on any grid and would hide the effect); E6 runs the delay line over the genuine per-ticker **day axis** (no window-flatten, no cross-ticker taps). See §0 scope caveats.

---

## 11. Open questions for Paul

1. **Is the star-free / no-count ceiling acceptable for the intended use (bounded-horizon time-series regression)?** If yes, ARM A (P4-FIR) is the low-risk pick and the OQ-4 hinge resolves toward "horizon mechanism, not counting machine." If no, none of P1/P3/P4 suffice — only P2's (recipe-less) group units do.
2. **Δt ownership for P4**: feed `Δt` as a feature (Approach A) at the model boundary, or commit to the variable-step LMU (Approach C) for genuine grid-invariance? P4 alone is not Δt-aware.
3. **Cap on `K`** given the ×K frozen-feature inflation — is ~35 acceptable as the embedding dimension, or should it be tunable/smaller on deeper cascades?
4. **If feedback is desired**, prefer P1 (single self-loop, cheapest) or P4-IIR (multi-tap, richer memory, heavier)? They are the `K=1` and `K>1` ends of the same axis.

**Recommended next step.** Treat ARM A (P4-FIR) as the front-runner for a bounded-horizon-regression substrate, fold this evaluation's conclusions into the OQ-4 model pick (proposals-doc §-level, alongside P1/P2/P3), and keep ARM B as the documented feedback upgrade. Do **not** ship code until Workstream 0 (the temporal substrate) is opened — every arm depends on it.

---

## Update (2026-06-10) — P5: a trained recurrent (NARX) output layer

> **What P5 is.** P5 builds *directly on this P4 design*: take the most charitable P4 — the **ARM A / P4-FIR** frozen delay-line hidden cascade above — and **add a trained recurrent output layer**. Each output node gets its own TDNN module whose delayed outputs feed *back* as additional inputs to that same node — an order-K **self-recurrent NARX neuron** `o(t)=g(W·h(t)+Σ vₖ·o(t−k)+b)` — and the now-recurrent output layer is retrained by BPTT after each hidden addition. **Headline form `g=tanh` (nonlinear); contrast `g=identity` (linear — what cascor ships today).** The hidden cascade stays FIR-frozen, so the *only* live recurrence is at the output. Evaluated by the same adversarial + empirical method (13-agent workflow, no synth agent); POC: [`../util/ad-hoc/verify_p5_recurrent_output_eval.py`](../util/ad-hoc/verify_p5_recurrent_output_eval.py) (numpy, seed-fixed, PE1–PE7, incl. a folded decisive held-out diagnostic). P5 *relocates* recurrence from the frozen cascade (where RCC's ceiling is proven) to a *trained* output — architecturally more promising than either P4 arm, which is why it was worth testing.

### P5.1 Ceiling verdict (the question that motivated P5) — NOT lifted

**P5 does *not* lift the star-free / no-count ceiling — for either the nonlinear headline or the linear contrast.** Unanimous across all four lenses; the refuters tried to break it and failed. The obstruction is **representational, not a training failure** — the BPTT gradient is verified correct (PE3 `7.82e-09`), capacity is ample, multi-restart, and negative feedback weights are permitted.

- **Decisive held-out evidence (PE7):** train a self-recurrent output on running parity, freeze `(W,b,v)`, evaluate on a *disjoint* stream → accuracy **collapses to the majority-class floor** (tanh `0.568→0.482`, identity `0.561→0.497`, floor `0.500`; held-out `|corr|≈0.02`). The tempting in-sample `|corr|≈0.2–0.25` (PE1/PE2) is **spurious finite-sample correlation, not computed parity**.
- **Mechanism.** Parity is `o(t)=XOR(x(t),o(t−1))`, which needs the second-order cross-term `x(t)·o(t−1)`; a single neuron cannot represent XOR (Minsky–Papert 1969), and P5's FIR drive is **output-state-blind** (`_compute_hidden_outputs` fills its buffer from inputs + prior *hidden* units and never reads any output: `cascade_correlation.py:1942-1946`, verified), so it cannot supply that cross-term. NARX universality (Siegelmann–Horne & Giles 1997) **does not transfer** — it requires a hidden MLP output map P5 lacks. P5's sign-free feedback weights do reach Knorozova–Ronca Thm-7 territory, but a negative weight buys *autonomous* period-2 oscillation under constant input, **not** the *input-gated* toggle parity needs. The refuter's escape hatch — a second, cross-fed recurrent output node — makes it *worse* (`|corr|=0.08`). General Zₙ>2 counting is left a **conjecture** by Knorozova–Ronca; **parity/C2 is closed**.
- **What P5 *does* buy (measured, modest):** a learnable **fading-memory tail** (PE4: lag-40 `|corr|≈0.42–0.45` vs FIR-only `0.16`) — but **below threshold**, so the effective-horizon cutoff is **unchanged (34, all arms)**. Better memory, no group structure, same ceiling.

### P5.2 The four questions (cf. P4 above)

- **Q1 recurrence.** A genuinely new, BPTT-correct training mode for cascor — today the output is a *static linear fit* (`output = matmul(output_input, output_weights) + output_bias`, `cascade_correlation.py:1979`; `train_output_layer` at `:1986` retrains a stock `nn.Linear` each round). But the recurrence is in the *wrong place / too thin* (one self-recurrent output, output-state-blind features) to change the expressivity class.
- **Q2 irregular-Δt.** Not Δt-aware, both arms; the output IIR does not restore grid-invariance. PE5 `116×` (FIR-only) vs `2.04×` (P5-tanh) is **confounded** by P5-tanh's worse regular-grid fit — both are grid-*dependent*; the LMU (Δt-doc §8.7) is `~1.15×`.
- **Q3 horizon.** Cutoff unchanged (34); on equities, persistence dominates (baseline `0.998`), residual `0.081` (tanh) / `0.048` (linear) — P4 ref FIR `0.196` / IIR `0.018`, suggestive (close-only FIR drive).
- **Q4 mini-batch/perf.** The recurrent output forces a *sequential* BPTT-over-window, but only through the **thin** output layer (hidden FIR frozen → cacheable). Cost shape ~order 10× a static fit (environment-dependent); ranking **P4-FIR ≪ P5 ≪ P4-IIR**; crucially the **worker subsystem is untouched** (output training is in-process) — so P5 is *cheaper to integrate than P4-IIR*.

### P5.3 POC results (measured — `util/ad-hoc/verify_p5_recurrent_output_eval.py`, seed 20260610, numpy 2.4.4)

```
PE3 BPTT vs finite-diff : 7.82e-09 PASS (hard assert; tanh & identity)
PE1 parity/counting     : FIR-base ≈ P5-tanh ≈ P5-linear at all m; acc 0.55–0.59 (chance 0.50); +~0.01 |corr|
PE2 one-step XOR        : in-sample tanh 0.25 / linear 0.20 (spurious); 2-cross-fed hatch 0.08 (worse)
PE7 DECISIVE held-out   : tanh 0.568→0.482, identity 0.561→0.497, floor 0.500 → parity NOT computed
PE4 horizon             : cutoff 34 ALL arms; P5 lag-40 0.42–0.45 vs FIR 0.16 (sub-threshold tail)
PE5 irregular-Δt        : FIR 116× ; P5-tanh 2.04× (confounded) ; both grid-dependent ; LMU §8.7 1.15×
PE6 equities (AAPL)     : baseline 0.998 ; residual P5-tanh 0.081 / P5-linear 0.048
```

### P5.4 Position & verdict

P5 ⊃ P4-FIR (it *is* P4-FIR plus the recurrent output). It adds genuine — if weak — recurrence at **lower worker-integration cost than ARM B / P4-IIR**, but the **same ceiling** as every proposal except P2. Across the family: **P1, P3, P4, and now P5 all leave the star-free ceiling intact; only P2's group-implementing units break it (and still have no training recipe).** If the ceiling is acceptable for bounded-horizon regression, **P4-FIR (ARM A) remains the cheapest temporal-reach option**, with P5 a heavier variant buying a small memory tail; if breaking the ceiling is required, the route is **group-implementing units (the P2 track), not output recurrence.** A *richer* output map — a hidden MLP making it a true NARX net — *could* clear the bar, but that is a recurrent sub-network, not "a recurrent output layer," and would warrant a separate proposal.

*P5-specific sources (verified):* Minsky & Papert 1969 (a single linear-threshold neuron cannot represent XOR); Siegelmann, Horne & Giles 1997, *Computational capabilities of recurrent NARX neural networks*, IEEE Trans. SMC-B 27(2):208-215 (NARX ⇔ fully-recurrent **with an MLP output map**). Shared with P4 (below): Giles 1995; Kremer 1996; Knorozova & Ronca 2024 (arXiv:2312.09048; Thm 7 negative-weight; Props 5/6 second-order; Zₙ>2 conjecture).

---

## References (verified)

- Waibel, Hanazawa, Hinton, Shikano & Lang 1989 — Phoneme recognition using time-delay neural networks (TDNN). IEEE TASSP 37(3).
- Bai, Kolter & Koltun 2018 — An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling. arXiv:1803.01271.
- Lin, Horne, Tiňo & Giles 1996 — Learning long-term dependencies in NARX recurrent neural networks. IEEE TNN 7(6).
- Giles, Chen, Sun, Chen, Lee & Goudreau 1995 — Constructive learning of recurrent NNs: limitations of RCC… IEEE TNN 6(4):829-836.
- Kremer 1996 — Comments on "Constructive learning…". IEEE TNN 7(4):1047-1051.
- Knorozova & Ronca 2024 — On the Expressivity of Recurrent Neural Cascades. AAAI; arXiv:2312.09048.
- Fahlman 1991 — The Recurrent Cascade-Correlation Architecture. NIPS-3.

## Cross-references

- OQ-4 proposals (P1/P2/P3): [`JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md`](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md)
- Irregular-Δt & continuous-time: [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md)
- Model design (read-only here): [`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md)
- Refactor / temporal substrate (read-only here): [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md)
- Empirical POC: [`../util/ad-hoc/verify_delay_line_node_eval.py`](../util/ad-hoc/verify_delay_line_node_eval.py)

---

*Working draft. Evaluates the P4 delay-line / shift-register output module (ARM A FIR as-written + ARM B IIR feedback). Feeds the OQ-4 model pick; pairs with the proposals and Δt docs above. No code ships on this basis until ratified and Workstream 0 is opened.*
