# Recurrent Cascade-Correlation — "P5" Recurrent (NARX) Output Layer: Design Evaluation

**Project**: juniper-recurse (recurrent NN initiative) — OQ-4 model-pick exploration; P5 design evaluation
**Repository**: pcalnon/juniper-ml (working notes)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0 (WORKING DRAFT — exploration, not ratified)
**Last Updated**: 2026-06-10

---

> **What this is.** An adversarial, anti-hallucination-gated evaluation of **"P5"**: the most charitable P4 (frozen **P4-FIR** delay-line modules bolted onto each tenured hidden node) **plus a *trained recurrent output layer*** — each output node gets its own TDNN module whose delayed outputs feed *back* as additional inputs to that same node, and the (now recurrent) output layer is retrained by BPTT after each hidden addition. Headline form = **nonlinear** self-recurrent output `o(t)=g(W·h(t)+Σ vₖ·o(t−k)+b)`, `g=tanh`; contrast = **linear** (`g=identity`, what cascor ships today). Pairs with — does not duplicate — the
> [P4 evaluation](JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md), the [OQ-4 proposals](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md) (P1/P2/P3) and the [Δt doc](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md).
>
> **Headline verdict — the question you cared most about.** **P5 does *not* lift the star-free / no-count ceiling — for *either* the nonlinear headline or the linear contrast.** The two forms are *empirically indistinguishable* on every ceiling task. The obstruction is **representational, not a training failure**: parity is the recurrence `o(t)=XOR(x(t),o(t−1))`, a single neuron cannot compute XOR (Minsky–Papert 1969), and P5's FIR drive is **output-state-blind** (`cascade_correlation.py:1942-1946`, verified), so it cannot supply the `x·o(t−1)` cross-term parity needs. What P5 *does* buy is modest and measured: a **trained fading-memory IIR readout** that softly extends the tail just past the FIR window — better memory, **same ceiling**.

---

## 0. Provenance & method

- **13-agent adversarial workflow** (grounding readers → numpy POC build + independent re-run/validity check → 4 lenses, the **ceiling lens** the heavyweight, each carrying the nonlinear headline *and* linear contrast → per-lens refuters explicitly tasked to *break* the no-ceiling-lift thesis → citation/consistency audit). No synthesis agent — this doc is authored directly from the verified findings (the P4 synth agent failed twice; direct authoring is more reliable).
- **Empirical POC**: [`../util/ad-hoc/verify_p5_recurrent_output_eval.py`](../util/ad-hoc/verify_p5_recurrent_output_eval.py) — numpy-only, `SEED=20260610`, deterministic, re-run independently. PE3 (gradient) and the PE7 verdict are the load-bearing checks. Reuses the P4 POC harness.
- **Anti-hallucination corrections applied before writing** (audit/verifier-flagged): (1) the decisive held-out numbers are the **seeded PE7** figures, *not* the build agent's unreproducible loose-stdout `0.622→0.539`; the diagnostic was **folded into the POC as a named, seeded `PE7`**; (2) cascor source paths corrected (`src/cascade_correlation/`, `src/candidate_unit/`, not `src/cascor/`) — every cited line was re-read first-hand; (3) the negative-weight mechanism stated precisely (§2.3); (4) throughput quoted as a *cost shape* (~order 10×, environment-dependent), not a hard 14–15×; (5) the Zₙ>2 negative labelled a **conjecture** (Knorozova–Ronca), parity/C2 as **closed**; (6) the POC's stale "§8.6" LMU reference fixed to **§8.7**.

> **Scope honesty.** (1) The ceiling result is established at the **single output node** level — the granularity P5 actually specifies (one self-recurrent neuron per output, self-feedback only). (2) The POC's FIR basis is a 1-D delay embedding `[x(t)…x(t−Kₕ+1)]` (the most-charitable P4-FIR), not the trained cascor hidden cascade, so absolute `|corr|` magnitudes are illustrative. (3) Equities (PE6) is single-seed, single-ticker (AAPL, recent 1500 days), close-only FIR drive. (4) cascor has **no temporal substrate today** — Workstream 0 is the shared prerequisite. (5) The parity negative is *strong measured + literature* evidence, not a from-scratch impossibility proof (that is the literature's).

---

## 1. The design as evaluated

- **Hidden cascade = P4-FIR, frozen.** Each tenured hidden node carries a bolt-on TDNN/FIR delay line; the cascade is a finite-memory feed-forward TDNN (no feedback). Established by the P4 evaluation: it cannot count.
- **Output layer = recurrent (NARX), trained.** Each output node `j` gets its own TDNN module and its delayed outputs `[oⱼ(t−1)…oⱼ(t−K+1)]` feed back as **additional inputs to node `j` only** → an order-K *self-recurrent* output neuron `oⱼ(t)=g(W·h(t)+Σ_{k} vₖ·oⱼ(t−k)+b)`. **Headline `g=tanh` (nonlinear); contrast `g=identity` (linear — cascor today).**
- **Training.** Grow FIR hidden candidate → freeze → **retrain the (now recurrent) output layer by BPTT-over-window**. The hidden cascade is FIR-frozen, so the *only* live recurrence is at the output; output BPTT flows through the small output layer + its self-feedback, **not** the frozen cascade.

---

## 2. THE CEILING QUESTION (your priority) — does P5 lift the star-free ceiling?

**No — neither arm.** This is unanimous across all four lenses, survived every refutation attempt, and is the *measured* result of the POC.

### 2.1 The decisive evidence (measured)

- **PE1 — no learning.** On running parity, parity-of-last-m (in- and out-of-window), and mod-3 counting, **no arm learns the task**: accuracy hugs chance (0.55–0.59 vs 0.50), and the recurrent output beats the *no-feedback* FIR readout by only **~0.01 |corr|** everywhere. Nonlinear and linear are indistinguishable.
- **PE7 — the decisive held-out test.** Train a single self-recurrent output on running parity on one Bernoulli stream, freeze `(W,b,v)`, evaluate on a **disjoint** stream. If P5 *represented* parity, held-out accuracy would stay high. Instead it **collapses to the majority-class floor**: tanh TRAIN→TEST acc ≈ `0.568→0.482`, identity ≈ `0.561→0.497`, floor ≈ `0.500`, held-out `|corr| ≈ 0.02`. **The in-sample `|corr|≈0.2–0.25` is spurious finite-sample correlation, not computed parity.**
- **PE2 — XOR obstruction + failed escape hatch.** A single recurrent output on the one-step task `o(t)=XOR(x(t),o(t−1))` reaches an in-sample `|corr|=0.25` (tanh) / `0.20` (linear) that collapses on held-out data; the refuter's escape hatch — a **second, cross-fed** recurrent output node — makes it *worse* (`|corr|=0.08`), not better.

This is a **representational obstruction (H2), not under-training (H3)**: the BPTT gradient is verified correct (**PE3**, max rel err `7.82e-09 < 1e-5`, hard assert), capacity is ample, multi-restart, and **negative recurrent weights are permitted** (clipped to `[−1.5,+1.5]`) — yet held-out still collapses.

### 2.2 The mechanism (literature-grounded, web-verified)

Parity needs the **second-order cross-term `x(t)·o(t−1)`** (the input gates whether the state toggles). A single self-recurrent output node computes an **affine-then-monotone** function of its inputs — it cannot represent XOR (**Minsky–Papert 1969**) — and P5's FIR drive depends on the **input history only** (`_compute_hidden_outputs` fills its buffer from inputs + prior *hidden* units and never reads any output: `cascade_correlation.py:1942-1946`, verified verbatim), so it cannot supply the missing cross-term. Adding more self-feedback taps `o(t−k)` or more FIR taps does not help — none of them is the *product* of the data bit and the node's own prior state.

**Why NARX universality (H1) does not rescue P5.** Output-feedback (NARX) recurrent nets *are* computationally equivalent to fully-recurrent nets (**Siegelmann, Horne & Giles 1997**, IEEE Trans. SMC-B 27(2):208-215) — but that result requires the **output map to be a multi-unit MLP**. P5 has **no hidden MLP between the FIR features and the single recurrent neuron**; it is one affine-pre-activation self-loop. The universality theorem's hypothesis is not met, so its conclusion does not transfer.

### 2.3 The negative-weight nuance (precise)

It is *not* that P5 "lacks negative weights." P5's feedback weights `vₖ` are **sign-unconstrained and BPTT-trained**, so P5 *does* explore Knorozova–Ronca **Thm-7** territory (a negative self-weight). But a negative weight buys **autonomous period-2 oscillation under *constant* input** — *not* the **input-gated** toggle parity requires. Free oscillation flips every step regardless of input; parity must flip only on a "1". A single additive-pre-activation neuron cannot make the flip *conditional* on the input (that is the XOR/Minsky–Papert obstruction again). The second-order multiplicative mechanism that *would* implement group structure (Knorozova–Ronca Props 5/6) is absent — P5's pre-activation is strictly affine, no multiplicative term.

### 2.4 Scope of the negative

- **Parity / C2: closed.** A single self-recurrent output cannot do it (Minsky–Papert + output-state-blind drive), measured and mechanistic.
- **General Zₙ counting (n>2): strongly supported, not formally closed.** Knorozova–Ronca 2024 leave it a **conjecture** (verbatim: *"We conjecture that sign or tanh neurons are not able to capture an actual grouplike semiautomaton"*). P5 instantiates no group-implementing unit, so it almost certainly cannot, but this rests on a conjecture, not a theorem.

### 2.5 What P5 *does* buy (measured, modest)

A **learnable IIR fading-memory tail**: **PE4** shows the output feedback extends recall to `|corr|≈0.42–0.45` at lag 40 (one step past the FIR window `Kₕ=35`) vs the FIR-only `0.16` — a real exponentially-fading echo — but it stays **below the 0.5 threshold** and the effective-horizon cutoff is **unchanged (34 for all arms)**. Better fading memory, **no group structure, same ceiling.**

---

## 3. Functionality & correctness — Q1

P5's output recurrence is a **genuinely new training mode for cascor**: today the output layer is a **static linear fit** (`forward` does `output = torch.matmul(output_input, output_weights) + output_bias`, `cascade_correlation.py:1979`; `train_output_layer` at `:1986` retrains it as a stock `nn.Linear` each round; candidate training is stateless single-shot, `candidate_unit.py:479`/`:1050`). P5 makes that output a recurrent BPTT-over-window neuron — the gradient is implemented correctly (PE3). So P5 *does* add real recurrence and trains it correctly. **But it is recurrence in the wrong place and too thin** (a single self-recurrent output fed by output-state-blind features) to change the expressivity class (§2). Nonlinear vs linear: identical on every ceiling task; the nonlinear form differs only in adding a weak, sometimes worse-fitting saturation (§4, §5).

## 4. Irregular-Δt — Q2

Neither arm is Δt-aware. The FIR drive is index-tapped, so a fixed real-time delay maps to no fixed index tap on an irregular grid, and the output IIR feedback does not restore grid-invariance. **PE5** measured FIR-only `reg 0.001 / irr 0.122` (116×) and P5-tanh `reg 0.079 / irr 0.161` (2.04×) — but **this ratio is confounded**: P5-tanh's much worse *regular*-grid baseline (tanh saturation under-fitting a clean sinusoid) deflates its ratio; **do not read 2.04 < 116 as P5 being more grid-robust.** Both are grid-**dependent**; neither approaches the LMU's `~1.15×` grid-invariance (Δt-doc §8.7). The principled fix remains Approach A/C from the Δt doc, not P5.

## 5. Effective horizon — Q3

- **(a) Regular time-series.** Cutoff = **34 for all arms** (PE4); P5 adds only the sub-threshold fading tail at lag 40 (§2.5).
- **(b) Irregular-Δt.** Real-time horizon uncontrolled (PE5); index taps misalign.
- **(c) Equities.** PE6: next-close is near-perfect **persistence** (baseline `|corr|=0.998`); the day-axis recurrent output adds little on the residual/return — **P5-tanh `0.081`, P5-linear `0.048`** (P4 ref: FIR `0.196` / IIR `0.018`). Both small; below the P4 FIR readout. *Suggestive only* — P5 here drives its FIR basis from the close column alone vs P4's multi-feature node.

## 6. Mini-batch & performance — Q4

The recurrent output forces a **sequential BPTT-over-window** at the output (it breaks per-timestep shuffling), but only through the **small output layer** — the hidden FIR cascade stays frozen and its features remain precomputable/cacheable, so the recurrence is *thin*. Cost **shape**: a recurrent rollout is order ~10× a static one-matmul-per-epoch fit (the exact constant is BLAS/solver/hardware-dependent — not a fixed 14–15×). **Cost ranking: P4-FIR ≪ P5 ≪ P4-IIR.** Crucially, **the worker subsystem is untouched** — output training is in-process, unlike P4-IIR which required deploying a recurrent candidate trainer worker-side. (A throughput number is honestly *declined as unmeasured*; the POC trains single streams, not mini-batches.)

## 7. Integration challenges & cost vs. the real cascor code

P5 needs a **custom recurrent output module replacing the static fit**. Verified locations:

| Concern | Today | P5 delta |
|---|---|---|
| Output forward | linear matmul `output_input @ output_weights + output_bias` (`:1979`) | per-node `g(W·h + Σ vₖ·o(t−k) + b)`; needs a time axis + state |
| Output training | `train_output_layer` (`:1986`) retrains a stock `nn.Linear` statically each round | BPTT-over-window recurrent trainer, retrained each round; new `vₖ` parameters |
| Output-state visibility | buffer is inputs + prior *hidden* units only (`:1942-1946`) | unchanged — and this output-state-blindness is exactly why the ceiling holds (§2.2) |
| Widen on install | `_resize_output_layer_for_new_units` (`:4051`) widens for hidden **features** | must also carry the per-node `K` self-feedback taps + recurrence state |
| Snapshot | linear weights | must persist `vₖ` / recurrence config |
| Worker | candidate training only | **untouched** (output training in-process) |

**Net**: heavier than P4-FIR (a real recurrent trainer + time axis at the output) but **lighter than P4-IIR on the worker axis** (no worker-side recurrence). All of it sits on Workstream 0 (the temporal substrate), which does not exist yet.

## 8. Strengths / weaknesses / risks / guardrails

| Strengths | Weaknesses |
|---|---|
| C1-clean; genuinely trains recurrence (PE3 correct) | Does **not** lift the ceiling — parity/counting unlearnable (PE1/PE2/PE7), both arms |
| Recurrence confined to a thin output layer; worker untouched | Not Δt-aware (PE5); horizon cutoff unchanged (PE4) |
| Buys a learnable fading-memory tail | Nonlinear adds little over linear; can fit a clean delay *worse* (PE5 reg baseline) |
| Cheaper to integrate than P4-IIR | Output BPTT breaks timestep shuffling; needs a Workstream-0 time axis |

- **Risks**: mistaking spurious in-sample `|corr|` for capability (PE7 is the guardrail); recurrent-output stability (clamp `v`); BPTT gradient bugs (PE3-style conformance test).
- **Guardrails**: a held-out generalization test (PE7) gated into CI before any "P5 learns X" claim; a `K=1`/`T=1`-identity migration; a snapshot round-trip test asserting `vₖ` survives.

## 9. Position vs. P1 / P2 / P3 / P4

- **P5 relocates recurrence to a *trained* output** — architecturally more promising than P4 (which has no trained recurrence past the frozen cascade), and it was worth testing. But the relocation is *too thin* (single self-recurrent neuron, output-state-blind features) to clear the bar.
- **vs P4**: P5 ⊃ P4-FIR (it *is* P4-FIR plus the recurrent output). It adds genuine (if weak) recurrence P4-FIR lacks, at lower worker cost than P4-IIR — but the same ceiling as both.
- **vs P1/P2/P3**: like P1/P3, it does not break star-free; unlike P2 (the only ceiling-breaker, still recipe-less) it adds no group-implementing units.
- **Bottom line**: P5 is a reasonable *fading-memory recurrent readout* option, not a path past the ceiling. If the ceiling is acceptable for bounded-horizon regression, **P4-FIR remains the cheapest temporal-reach option** and P5 is a heavier variant that buys a small memory tail; if breaking the ceiling is required, the answer is group-implementing units (the P2 research track), **not** output recurrence.

---

## 10. POC results (measured — `util/ad-hoc/verify_p5_recurrent_output_eval.py`, seed 20260610, numpy 2.4.4)

```
PE3 BPTT vs finite-diff   : max rel err 7.82e-09  PASS (hard assert; tanh & identity, mse & corr)
PE1 parity/counting       : FIR-base ≈ P5-tanh ≈ P5-linear at ALL m; acc 0.55–0.59 (chance 0.50);
                            recurrent output adds only ~+0.01 |corr| over the no-feedback FIR readout
PE2 one-step XOR          : in-sample tanh 0.25 / linear 0.20 (spurious); 2-cross-fed-node hatch 0.08 (worse)
PE7 DECISIVE held-out     : running parity train→test acc tanh 0.568→0.482, identity 0.561→0.497,
                            floor 0.500, test |corr| ≈ 0.02  → collapse to floor → parity NOT computed
PE4 horizon               : cutoff (|corr|≥0.5) = 34 for ALL arms; P5 extends lag-40 to 0.42–0.45 (vs FIR 0.16),
                            still sub-threshold → no horizon gain, just a fading tail
PE5 irregular-Δt          : FIR-only 116× ; P5-tanh 2.04× (CONFOUNDED by worse reg baseline) ; LMU §8.7 1.15×
PE6 equities (AAPL 1500d) : baseline 0.998 ; residual P5-tanh 0.081 / P5-linear 0.048 (P4 ref FIR 0.196/IIR 0.018)
```

The nonlinear headline and the linear contrast are **empirically indistinguishable on every ceiling task** (PE1/PE2/PE7). PE7 is the decisive number.

---

## 11. Open questions for Paul + recommended next step

1. **Given P5 does not lift the ceiling, is the ceiling acceptable for the intended bounded-horizon regression?** If yes, P4-FIR is the cheapest reach; P5 is a heavier variant buying a small memory tail. If no, the only route is **group-implementing units** (P2 research track), not output recurrence.
2. **Is P5's fading-memory tail (PE4) worth its cost** over P4-FIR, or is the output recurrence not earning its BPTT/integration overhead?
3. **Would a *richer* output map change the verdict?** A hidden MLP between FIR features and the recurrent output (making it a real NARX net, per Siegelmann–Horne–Giles) *could* clear the bar — but that is no longer "a recurrent output layer," it is a recurrent sub-network, and worth a separate "P6?" if you want to pursue ceiling-breaking by output enrichment.

**Recommended next step.** Record P5 in the OQ-4 set as *"trained recurrent (NARX) output readout — fading memory, ceiling unchanged."* Fold its conclusion into the model pick alongside P1–P4. Do not ship code until Workstream 0 exists.

---

## References (verified)

- Minsky & Papert 1969 — *Perceptrons* (a single linear-threshold neuron cannot represent XOR).
- Giles, Chen, Sun, Chen, Lee & Goudreau 1995 — Constructive learning of recurrent NNs: limitations of RCC. IEEE TNN 6(4):829-836.
- Kremer 1996 — Comments on "Constructive learning…". IEEE TNN 7(4):1047-1051.
- Knorozova & Ronca 2024 — On the Expressivity of Recurrent Neural Cascades. AAAI 38(9):10589-10596; arXiv:2312.09048 (star-free; negative-weight Thm 7; 2nd-order Props 5/6; Zₙ>2 conjecture).
- Siegelmann, Horne & Giles 1997 — Computational capabilities of recurrent NARX neural networks. IEEE Trans. SMC-B 27(2):208-215 (NARX ⇔ fully-recurrent *with an MLP output map*).
- Lin, Horne, Tiňo & Giles 1996/1998 — Learning long-term dependencies in NARX recurrent neural networks. IEEE TNN 7(6) / jump-ahead connections.

## Cross-references

- P4 evaluation (P5 ⊃ P4-FIR): [`JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md`](JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md)
- OQ-4 proposals (P1/P2/P3): [`JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md`](JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md)
- Irregular-Δt & continuous-time: [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md)
- Empirical POC: [`../util/ad-hoc/verify_p5_recurrent_output_eval.py`](../util/ad-hoc/verify_p5_recurrent_output_eval.py)

---

*Working draft. Evaluates the P5 trained-recurrent-output design (nonlinear headline + linear contrast). Centers on the star-free ceiling (verdict: not lifted, either arm — a representational obstruction). Feeds the OQ-4 model pick; pairs with the P4, proposals, and Δt docs. No code ships on this basis until ratified and Workstream 0 is opened.*
