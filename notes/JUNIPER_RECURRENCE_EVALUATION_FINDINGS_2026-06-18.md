# Juniper-Recurrence — Evaluation Findings (Δt-Proof)

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; harness in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (findings)
**Last Updated**: 2026-06-18

---

> **What this is.** The result of the recurrence platform's Wave-2 evaluation — the answer to the
> question the whole effort was built for: *does the Δt-native LMU actually exploit irregular timing,
> and does it beat honest baselines?* **Yes, decisively.** This records the verdict and meets the
> roadmap's OQ-7 "completed-state" gate. Method + bands: [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md);
> harness + raw results: `bench/` in pcalnon/juniper-recurrence (PR #23, `bench/results/REPORT.md`).

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

## 4. Acceptance bands (OQ-14)

All six bands **PASS**:

1. **Δt thesis** — var-Δt ≥25% lower RMSE than fixed-Δt on `irregular_sine`: **+57%** ✅
2. **Beats naive, matches/beats linear** (every dataset): ✅ on all three
3. **No regular-grid penalty** (`multi_sine`, `mackey_glass`): var ≡ fixed (0% gap) ✅

## 5. Conclusion

- The **Δt-native LMU thesis is empirically validated** — the P3-C / LMU model pick is justified by
  measured results, not just design argument.
- The roadmap's **OQ-7 "completed-state" gate is met**: the deployed app trains, predicts, and
  cross-validates on irregular-Δt data end-to-end (`/v1/train` r²=0.939 over HTTP).
- Per DP-3, the next model increment (e.g. the trained / nonlinear torch readout) should be gated on a
  *measured* need; this benchmark is the ranking instrument for that decision.

## 6. Caveats (reported honestly)

- The regular-Δt synthetics (`multi_sine`, `mackey_glass`) are **noiseless** (their default), so the
  LMU fits them near-perfectly; they are controls (no-penalty + beats-baselines checks), not the
  discriminating test. The **irregular sampling** in `irregular_sine` is what makes the task
  non-trivial and is where the Δt contribution shows. A noisy variant is a cheap follow-up.
- Results are on **synthetic** signals — a research Δt-thesis check, not a forecasting/trading claim.
  Real-data confirmation on `equities_seq` is an available next step.
- The harness's `[bench]` extra needs juniper-data's generators (#187/#188), which are on juniper-data
  `main` but not yet in a PyPI release; runs use an editable sibling until juniper-data republishes.

## 7. Cross-references

- Evaluation design + bands: [`JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_DESIGN_2026-06-18.md)
- Canonical roadmap (Wave-2 / OQ-7): [`JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md)
- LMU numeric design + the fixed-Δt negative control: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Harness + raw results: `bench/` in pcalnon/juniper-recurrence (`bench/results/REPORT.md`)
