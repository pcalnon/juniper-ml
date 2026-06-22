# Juniper-Recurrence — Evaluation Findings (Δt-Proof)

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; harness in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.3.0 (findings + noise/real-data extensions + data-conditioning re-bench + DP-3 capacity)
**Last Updated**: 2026-06-22

---

> **What this is.** The result of the recurrence platform's Wave-2 evaluation — the answer to the
> question the whole effort was built for: *does the Δt-native LMU actually exploit irregular timing,
> and does it beat honest baselines?* **Yes, decisively.** This records the verdict and meets the
> roadmap's OQ-7 "completed-state" gate. **v1.1 adds §3.1** — a noise-robustness sweep + a real-data
> `equities_seq` run — and the **DP-3 ranking** they produce (§5). **v1.2 adds §3.2** — a direct
> data-conditioning re-bench that revises the §3.1 equities reading (the r²≈−50 failure was *mostly* a
> readout-regularization artifact, not non-stationarity) and refines the DP-3 ranking accordingly.
> **v1.3 adds §3.3** — the DP-3 P2 capacity result: a purpose-built `delay_product` dataset on which the
> nonlinear RFF readout beats the linear readout by a **+0.83 r² gap**, demonstrating nonlinear-readout
> *capacity* (the existing datasets only ever *tie* at their linear ceiling).
> Method + bands:
> [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md);
> harness + raw results: `bench/` in pcalnon/juniper-recurrence (PRs #23, #27, #29; `bench/results/REPORT.md`).

---

## 1. The question

The P3-C / LMU model pick rests on one empirical claim: an LMU that consumes the real per-step Δt
should outperform the same model that assumes a regular grid, on irregularly-timed data. Everything
upstream (the 3-D Δt NPZ contract, the variable-step rollout, the data-client validator, the app's
`/v1/train` · `/v1/crossval`) was built to make this testable. Wave-2 tests it.

## 2. Method (summary)

Walk-forward cross-validation (`juniper_model_core.crossval`) of four models on identical folds, on
generated datasets: the **Δt-native LMU**, a **fixed-Δt negative control** (the same `LMURegressor`
with the per-step timing replaced by a uniform grid — isolating the Δt contribution), **naive
persistence**, and a **linear ridge** baseline. Plus an end-to-end proof through the deployed app
(`POST /v1/train` → `/v1/predict` → `/v1/crossval` on irregular-Δt data). Datasets, grid, and the
OQ-7 acceptance bands were pre-registered in the design doc (DP-5 anti-cherry-pick guardrail).

## 3. Results

Walk-forward CV, 5 folds, mean across folds (full table in `bench/results/REPORT.md`):

| dataset | model | rmse | r2 |
|---|---|---|---|
| `irregular_sine` (irregular-Δt) | **LMU (variable-Δt)** | **0.153** | **0.988** |
| `irregular_sine` | LMU (fixed-Δt control) | 0.358 | 0.935 |
| `irregular_sine` | naive persistence | 0.445 | 0.900 |
| `irregular_sine` | linear ridge | 0.440 | 0.902 |
| `multi_sine` (regular-Δt) | LMU (var ≡ fixed) | 0.000 | 1.000 |
| `mackey_glass` (regular-Δt) | LMU (var ≡ fixed) | 0.0025 | 0.9999 |

**Headline: on `irregular_sine` the Δt-native LMU cuts RMSE by 57% vs the same model ignoring timing**
(0.358 → 0.153), and beats naive/linear by a wide margin. On the regular grids the variable-Δt model
is identical to the fixed-Δt one (the per-step grid *is* uniform there) — no penalty for Δt-awareness.

## 3.1 Extensions — noise robustness + real data (2026-06-19)

Two follow-ups flagged in §6 were run as informational extensions (not scored against the ratified
bands — DP-5 guardrail; full tables in `bench/results/REPORT.md`).

**Noise robustness (synthetic).** Re-running `irregular_sine` and `multi_sine` with additive Gaussian
observation noise (`noise_std ∈ {0.10, 0.25}`) shows the **Δt advantage degrades gracefully but
survives**:

| dataset | var-Δt RMSE | fixed-Δt RMSE | Δt reduction | var-Δt r² |
|---|---|---|---|---|
| `irregular_sine` (clean) | 0.153 | 0.358 | **+57.1%** | 0.988 |
| `irregular_sine_noise0.10` | 0.195 | 0.400 | **+51.1%** | 0.981 |
| `irregular_sine_noise0.25` | 0.328 | 0.526 | **+37.6%** | 0.947 |

The reduction stays above the 25% thesis bar even at heavy noise, the LMU keeps beating naive + linear
at every level, and on the regular grids the var ≡ fixed identity holds exactly under noise (0% gap) —
Δt-awareness still costs nothing when the grid is regular.

**Real data (`equities_seq`, single ticker AAPL 2010–2022, calendar-gap Δt).** Here the LMU **fails**:
on the non-stationary raw next-day-close target the Δt-native LMU lands at r² ≈ **−50** (RMSE 15.0) and
the fixed-Δt control at r² ≈ −88, while the trivial **`linear_ridge` baseline wins outright (r² 0.985,
RMSE 0.96)**. The Δt-aware LMU is still *less bad* than the fixed-Δt one (+22.8% RMSE), so the Δt
contribution is directionally real even here — but the headline is that a closed-form Legendre-memory
regressor extrapolates badly on a trending, non-stationary price level where last-step linear
persistence is near-optimal. The §3.1 read was that this is a **target-conditioning** problem (predict
returns); the **§3.2 re-bench revises that** — it was *dominantly* an unregularized-readout artifact,
with target non-stationarity a secondary effect. Either way it is not a deficiency of the Δt mechanism.

## 3.2 Data-conditioning re-bench — the equities failure was mostly a readout artifact (2026-06-19)

§3.1 predicted a stationary target would fix the `equities_seq` failure ("predicting returns … is the
standard fix"). A direct re-bench — juniper-data 0.8.0's new `regression_target` option (juniper-data
#195) plus a ridge sweep on the LMU readout (harness juniper-recurrence #29) — shows that prediction was
**only partly right**, and the fuller picture is more useful. AAPL 2010–2022, single ticker, 5-fold
walk-forward CV, mean r² across folds:

| readout | `next_close` (std 38) | `log_return` (std 0.018) |
|---|---|---|
| LMU **ridge=0** (the bench default) | **−50.6** | **−4422** |
| LMU ridge=1e-3 | +0.905 | −3.84 |
| LMU ridge=0.1 | +0.829 | −0.051 |
| LMU ridge=1.0 | −0.029 | −0.038 |
| LMU ridge=100 | — | **−0.001** |
| `linear_ridge` (ridge=1e-3) | **+0.985** | **−1.72** |
| `naive_persistence` | −34.2 | −238.7 |

1. **The r²≈−50 catastrophe was dominantly an *unregularized-readout* artifact, not target
   non-stationarity.** The bench builds `LMURegressor` with the default `ridge=0.0` — a plain `lstsq`
   over the 162-column LMU-memory map — while the `linear_ridge` baseline uses `ridge=1e-3`. On the
   *raw* `next_close` target, simply adding `ridge=1e-3` lifts the LMU from **−50.6 → +0.905**. Per the
   model docstring, `ridge=0` is an intentional `juniper-model-core` conformance default (the
   "overfit-tiny exactly" guarantee) — the wrong setting for real low-signal data. So the catastrophe
   was a **bench-configuration** issue, not a model bug, and not (primarily) the target.
2. **Target conditioning is real but secondary.** `linear_ridge`'s headline +0.985 on `next_close` was
   a **non-stationarity artifact** (last-step close ≈ next close); it dissolves to **−1.72** on the
   stationary log-return target. The genuine predictability ceiling for daily AAPL returns is **≈0** —
   the efficient-market floor; no model here has return-forecasting *skill* (as expected).
3. **On the stationary target with a regularized readout, the Δt-LMU is the *best* model.** It reaches
   the ≈0 ceiling (ridge ≥ 0.1 → r² −0.05 … −0.001) and **beats `linear_ridge`** (−1.72). The
   variable-Δt and fixed-Δt regularized LMUs are ~tied here (var −0.038, fixed −0.030): at the
   efficient-market floor there is no temporal signal for Δt-awareness to exploit, so it neither helps
   nor hurts — consistent with the synthetic result that Δt only helps where timing carries information.

**Net:** two independent fixes — a stationary target (shipped: juniper-data 0.8.0 `regression_target`)
*and* a regularized readout (the dominant lever; applied in the bench, model-default question tracked in
juniper-recurrence #28). With both, the real-data row stops being a catastrophe and the Δt-LMU is
competitive at the (low) ceiling. Read this as a **model-fit / fairness diagnostic**, not a forecasting
claim.

## 3.3 DP-3 P2 — nonlinear-readout capacity (the `delay_product` instrument, 2026-06-22)

§3.2 showed the existing datasets sit at the linear readout's ceiling, so the DP-3 nonlinear (RFF)
readout merely *ties* there — it could confirm the absence of a nonlinear benefit but could not, alone,
demonstrate nonlinear *capacity*. DP-3 P2 closes that gap with a purpose-built capacity dataset and an
RFF readout row (design §8a; the `delay_product` generator in juniper-data #203; the bench RFF row in
juniper-recurrence #44).

**The instrument.** `delay_product` is an irregularly-sampled sinusoid superposition whose regression
target is the **bilinear product of two delayed in-window values**, `y = x(t−τ₁)·x(t−τ₂)` (both delays
kept inside the lookback). Because the LMU memory is a *linear* compression of the window, the target is
a **quadratic form in the memory state**: a linear readout provably cannot represent it (its r² is
bounded well below 1), while a random-Fourier-feature readout can approximate it. A model-free check in
the generator's own tests confirms the premise — an unrestricted linear map of the *entire* window
reaches r² ≈ 0.01, while the exact product feature reaches r² = 1.0.

**Measured (LMU d=16, 5-fold walk-forward CV; harness juniper-recurrence #44):**

| dataset | linear readout r² | RFF readout r² | gap |
|---|---|---|---|
| `delay_product` (capacity) | **−0.04** | **+0.79** | **+0.83** |
| `irregular_sine` (near-linear) | +0.988 | +0.985 | −0.003 (tie) |

**Reading.** Exactly the predicted signature: on the capacity dataset the linear readout cannot fit the
bilinear target (r² ≈ 0) while the RFF readout recovers most of it (r² ≈ 0.79 — the residual is the LMU
memory's order-`d` truncation, not a readout limitation); on the near-linear synthetics the two readouts
tie at the ceiling, so the nonlinear readout **costs nothing** where it is not needed. This validates
that the DP-3 Rung 2a RFF readout has **genuine nonlinear capacity** — it is the *instrument* that proves
the readout spectrum works, complementing §3.2's finding that none of the *original* datasets needed it.
It does **not** revise the §3.2/§5 ranking for the real data (their predictability ceiling is still
≈0); it establishes capacity, available for any future target that is a genuine nonlinear functional of
recent history. (The RFF readout is reachable over the service edge via the DP-3 P2c HTTP `readout` enum,
juniper-recurrence #45.)

## 4. Acceptance bands (OQ-14)

All six bands **PASS**:

1. **Δt thesis** — var-Δt ≥25% lower RMSE than fixed-Δt on `irregular_sine`: **+57%** ✅
2. **Beats naive, matches/beats linear** (every dataset): ✅ on all three
3. **No regular-grid penalty** (`multi_sine`, `mackey_glass`): var ≡ fixed (0% gap) ✅

The ratified verdict is scored only on the three pre-registered datasets (DP-5 guardrail) and is
**unchanged** by the §3.1/§3.2 extensions, which are reported as informational.

## 5. Conclusion

- The **Δt-native LMU thesis is empirically validated** — the P3-C / LMU model pick is justified by
  measured results, not just design argument.
- The roadmap's **OQ-7 "completed-state" gate is met**: the deployed app trains, predicts, and
  cross-validates on irregular-Δt data end-to-end (`/v1/train` r²=0.939 over HTTP).
- **DP-3 ranking (the instrument's verdict) — refined by the §3.2 re-bench.** The LMU's closed-form
  linear readout is **noise-robust** — the Δt advantage survives to `noise_std=0.25` without collapse —
  so a more expressive readout is not motivated by noise. The §3.1 read attributed the `equities_seq`
  failure to data-conditioning; the **§3.2 re-bench revises that**: it was *dominantly* an
  unregularized-readout artifact (the bench's `ridge=0` conformance default), with target
  non-stationarity secondary. On a stationary target with a *regularized* readout the Δt-LMU reaches the
  efficient-market ceiling and beats linear ridge — i.e. there is **no measured return-forecasting skill
  to unlock on this data for any readout** (the ceiling is ≈0). **DP-3 (a trained / nonlinear torch
  readout) therefore remains not strictly indicated by the data** — its value is analytical / insight
  (which is why it is being built regardless of the ranking). **§3.3 (DP-3 P2) now demonstrates the numpy
  RFF readout (Rung 2a) has genuine nonlinear capacity** — a +0.83 r² gap on the purpose-built
  `delay_product` dataset — so the readout *spectrum* is proven to work; it simply remains unneeded for
  the current near-linear datasets (where it ties), and the torch rung (2b) stays gated on a measured 2a
  lift the real data does not provide. What the re-bench *does* rank highest is a
  cheaper lever: a **regularized-readout default for real low-signal data** (a one-line bench fix,
  applied; the model-default question tracked in juniper-recurrence #28) — alongside the **target
  conditioning** that shipped in juniper-data 0.8.0 (#195).

## 6. Caveats (reported honestly)

- The regular-Δt synthetics (`multi_sine`, `mackey_glass`) are near-noiseless controls; the
  discriminating test is the irregular sampling in `irregular_sine`. The §3.1 noise sweep (the
  "cheap follow-up" this section originally flagged) now confirms the Δt contribution holds under
  observation noise.
- The synthetic signals are a research Δt-thesis check, not a forecasting/trading claim. Read the
  `equities_seq` run as a **model-fit / fairness diagnostic** (per §3.2: the LMU needs a regularized
  readout — and, secondarily, a stationary target — on real low-signal data), not an investment signal.
  Daily single-name returns are near-efficient: the measured ceiling for every model is r² ≈ 0.
- **Reproducibility.** juniper-data 0.7.0 published the generators (#187/#188/#189); **0.7.1** fixed the
  wheel to ship the bundled `sp500_constituents.csv`; **0.8.0** added the `regression_target` option
  (#195). The §3.2 numbers reproduce from `juniper-data[equities]>=0.8.0` (the bench `[bench]` extra
  pins it) — no source / editable-sibling step. The §3.1 numbers (raw-close target) were generated
  before 0.7.1 from a source install.

## 7. Cross-references

- Evaluation design + bands: [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md)
- Canonical roadmap (Wave-2 / OQ-7): [`JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md)
- LMU numeric design + the fixed-Δt negative control: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Harness + raw results: `bench/` in pcalnon/juniper-recurrence (`bench/results/REPORT.md`)
- §3.2 re-bench: juniper-data #195 (`regression_target`), juniper-recurrence #29 (bench), and the
  readout-regularization follow-up juniper-recurrence #28
- DP-3 readout spectrum design: [`JUNIPER_RECURRENCE_DP3_READOUT_SPECTRUM_DESIGN_2026-06-20.md`](JUNIPER_RECURRENCE_DP3_READOUT_SPECTRUM_DESIGN_2026-06-20.md)
- §3.3 DP-3 P2 capacity: juniper-data #203 (`delay_product` generator), juniper-recurrence #44 (bench RFF row), juniper-recurrence #45 (HTTP `readout` enum)
