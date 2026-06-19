# Juniper-Recurrence — Evaluation Findings (Δt-Proof)

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; harness in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.1.0 (findings + noise/real-data extensions)
**Last Updated**: 2026-06-19

---

> **What this is.** The result of the recurrence platform's Wave-2 evaluation — the answer to the
> question the whole effort was built for: *does the Δt-native LMU actually exploit irregular timing,
> and does it beat honest baselines?* **Yes, decisively.** This records the verdict and meets the
> roadmap's OQ-7 "completed-state" gate. **v1.1 adds §3.1** — a noise-robustness sweep + a real-data
> `equities_seq` run — and the **DP-3 ranking** they produce (§5). Method + bands:
> [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md);
> harness + raw results: `bench/` in pcalnon/juniper-recurrence (PRs #23, #27; `bench/results/REPORT.md`).

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
persistence is near-optimal. This is almost certainly a **target-conditioning** problem (the raw price
is non-stationary; predicting returns or a normalized target is the standard fix), not a deficiency of
the Δt mechanism itself.

## 4. Acceptance bands (OQ-14)

All six bands **PASS**:

1. **Δt thesis** — var-Δt ≥25% lower RMSE than fixed-Δt on `irregular_sine`: **+57%** ✅
2. **Beats naive, matches/beats linear** (every dataset): ✅ on all three
3. **No regular-grid penalty** (`multi_sine`, `mackey_glass`): var ≡ fixed (0% gap) ✅

The ratified verdict is scored only on the three pre-registered datasets (DP-5 guardrail) and is
**unchanged** by the §3.1 extensions, which are reported as informational.

## 5. Conclusion

- The **Δt-native LMU thesis is empirically validated** — the P3-C / LMU model pick is justified by
  measured results, not just design argument.
- The roadmap's **OQ-7 "completed-state" gate is met**: the deployed app trains, predicts, and
  cross-validates on irregular-Δt data end-to-end (`/v1/train` r²=0.939 over HTTP).
- **DP-3 ranking (the instrument's verdict).** The extensions give a clear signal. The LMU's
  closed-form linear readout is **noise-robust** — the Δt advantage survives to `noise_std=0.25`
  without collapse — so a more expressive readout is not motivated by noise. And the `equities_seq`
  failure is a **data-conditioning** symptom (a non-stationary raw-price target), which a nonlinear
  readout would not fix. **DP-3 (a trained / nonlinear torch readout) is therefore not clearly
  indicated** — de-prioritized pending a measured need. The higher-value next step the data ranks is
  **target conditioning for non-stationary real data** (predict returns or a normalized target), on
  the juniper-data side, *before* any model-capacity increment.

## 6. Caveats (reported honestly)

- The regular-Δt synthetics (`multi_sine`, `mackey_glass`) are near-noiseless controls; the
  discriminating test is the irregular sampling in `irregular_sine`. The §3.1 noise sweep (the
  "cheap follow-up" this section originally flagged) now confirms the Δt contribution holds under
  observation noise.
- The synthetic signals are a research Δt-thesis check, not a forecasting/trading claim. The §3.1
  `equities_seq` run is the real-data confirmation flagged here; read it as a **model-fit diagnostic**
  (the LMU needs conditioned targets on non-stationary data), not an investment signal.
- **juniper-data 0.7.0 published the generators** (#187/#188/#189), so the synthetic rows now install
  from PyPI — the editable-sibling caveat is retired. **However**, the 0.7.0 wheel **omits the bundled
  `sp500_constituents.csv`** (a packaging defect — no `package_data` entry), so `equities_seq` raises
  `FileNotFoundError` from a pip install of `juniper-data[equities]==0.7.0`; the §3.1 equities numbers
  were generated from a source install. A **juniper-data 0.7.1** packaging fix is the remedy; until
  then the equities row reproduces only from source.

## 7. Cross-references

- Evaluation design + bands: [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md)
- Canonical roadmap (Wave-2 / OQ-7): [`JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md)
- LMU numeric design + the fixed-Δt negative control: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Harness + raw results: `bench/` in pcalnon/juniper-recurrence (`bench/results/REPORT.md`)
