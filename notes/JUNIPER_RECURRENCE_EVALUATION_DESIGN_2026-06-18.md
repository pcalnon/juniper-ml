# Juniper-Recurrence — Evaluation & Δt-Proof: Design

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; harness lands in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (design ratified 2026-06-18; pending build)
**Last Updated**: 2026-06-18

---

> **What this is.** The design for the recurrence platform's **evaluation** — the canonical roadmap's
> Wave-2 exit (C2 + I2). It answers the research question the whole effort was built to answer:
> *does the Δt-native LMU actually exploit irregular timing, and does it beat honest baselines?* It
> combines a reproducible **direct-library benchmark** (C2) with an **end-to-end Δt proof through the
> deployed app** (I2). All dependencies are now satisfied: `juniper-model-core[crossval] 0.2.0`, the
> `juniper-data` synthetic + irregular-Δt generators (#187/#188/#189), `juniper-data-client 0.4.2`,
> and the app's `/v1/train` · `/v1/predict` · `/v1/crossval` surface. The harness lands as one PR in
> `pcalnon/juniper-recurrence`.

---

## 1. Goal and scope

The roadmap ([`…STATE_ASSESSMENT_AND_ROADMAP…`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md))
Wave-2 exit criterion: *"a reproducible benchmark report on ≥1 irregular-Δt and ≥1 regular-Δt dataset,
with baselines; and the OQ-7 'completed-state' gate met (I1 + I2)."* This design delivers it.

**In scope:** a reproducible benchmark (LMU vs baselines + a fixed-Δt negative control, walk-forward
CV, declared metrics + acceptance bands) on generated datasets; an end-to-end proof that the deployed
app handles irregular-Δt data; a committed report.

**Out of scope:** a full hyper-parameter sweep (a small *declared* grid only — DP-5 guardrail); a
torch / nonlinear readout (DP-3, deferred — this evaluation is what *ranks* whether it's worth it);
a Grafana dashboard; real-money trading claims.

## 2. The two tracks

- **C2 — benchmark (direct library).** `model-core.crossval` (`walk_forward_folds`, `cross_validate`,
  `score`) over the LMU and baselines on generated datasets. No running service — fully reproducible
  from a seed. This is the *evidence*.
- **I2 — end-to-end Δt proof (through the app).** Generate an `irregular_sine` NPZ → `POST /v1/train`
  → `POST /v1/predict` (and `POST /v1/crossval`) → assert the deployed path runs and its LMU metrics
  match the direct-library path within tolerance. This is the *OQ-7 "completed-state" gate* — the app
  actually trains and predicts on irregular-Δt data.

The two share dataset generation and the metric definitions; only the execution path differs.

## 3. Datasets (fixed seeds, generated reproducibly)

Generated directly via the `juniper-data` generators (imported as a bench dependency — no live
service), each producing the 3-D sequence NPZ contract (`X (n,T,F)`, `y`/`y_reg`, `dt (n,T)`,
`target_dt (n,)`, `seq_lengths`, …).

| Dataset | Grid | Role |
|---|---|---|
| `irregular_sine` (#188) | **irregular-Δt** | the thesis — where Δt-awareness should pay |
| `multi_sine` (#187) | regular-Δt | control — Δt-awareness must not *hurt* here |
| `mackey_glass` (#187) | regular-Δt (harder) | a non-trivial regular-Δt sanity check (optional) |
| `equities_seq` | real, irregular (calendar gaps) | real-data sanity (optional, if cheap) |

Datasets are pre-registered here (DP-5 guardrail against post-hoc dataset cherry-picking).

## 4. Models and baselines

All four are run through the **same** walk-forward CV so the comparison is apples-to-apples.

| Model | What it is | Why |
|---|---|---|
| **LMU (variable-Δt)** | `LMURegressor(d, θ, ridge)` consuming `dt`/`target_dt` (the Approach-C win) | the model under test |
| **LMU (fixed-Δt)** | the same LMU with `dt` forced to a uniform grid (the §9.1a `FixedStepLMUMemory` foil) | **negative control** — isolates the Δt contribution; the single most important comparison |
| **Naive persistence** | predict the last observed target value | floor baseline |
| **Linear ridge** | closed-form ridge on the last valid step (and/or flattened window) — no temporal memory | honest non-temporal baseline |

Baselines are wrapped as minimal `TrainableModel`s (so `cross_validate`'s factory drives them
identically) **or** scored directly with `score()` per fold; the harness uses whichever keeps the
fold splits identical across all four (§5).

The LMU runs over a **small declared grid** of `d ∈ {8,16,32}`, `θ` (data-derived default + one
alternative), `ridge ∈ {0, 1e-3}` — reported in full, not just the best cell (DP-5 anti-p-hack
guardrail).

## 5. CV scheme and metrics

- **Splits:** `walk_forward_folds(...)` — expanding train window + embargo (no test window's lookback
  reaches into train; the López-de-Prado purge the Δt-handling doc's I-invariants require). Same fold
  indices reused across all four models per dataset.
- **Executor:** `cross_validate(factory, X, y, folds, aux=…)` — `aux` carries `dt`/`target_dt`/
  `seq_lengths` sliced per fold so the 3-D Δt path "just works" (crossval design §4).
- **Metrics:** `score("regression", y_true, y_pred)` → `{mse, rmse, mae, r2}`. Reported as
  **mean ± std across folds** per dataset × model, plus the headline **Δt-contribution deltas**
  (variable-Δt vs fixed-Δt LMU).

## 6. Acceptance bands (OQ-14 — ratified by Paul, 2026-06-18)

1. **Δt thesis (primary).** On `irregular_sine`, the variable-Δt LMU **materially beats** the fixed-Δt
   LMU — target **≥25% lower RMSE** (mean across folds). This is the core "Δt-awareness pays" claim;
   failing it would reopen the P3-C/LMU model pick.
2. **Beats naive + matches/beats linear.** LMU `r2` **> naive persistence** on every dataset, and
   **≥ the linear ridge baseline** within fold noise (overlapping mean ± std is acceptable; the LMU
   need not crush a linear model, but must not lose to it).
3. **No regular-grid penalty.** On `multi_sine`, variable-Δt LMU **≈** fixed-Δt LMU (RMSE within
   ~10%) — Δt-awareness must not hurt when the grid is already regular.

A run is a **pass** when (1) holds and (2)–(3) hold on the regular/irregular pair. Results that miss a
band are reported honestly (the benchmark's value is the measurement, not a green checkmark).

## 7. Harness layout and packaging

A self-contained `bench/` harness in the **`juniper-recurrence`** repo (the eval exercises the model +
crossval; it belongs next to them):

```text
juniper-recurrence/
└── bench/
    ├── __init__.py
    ├── datasets.py       # generate the §3 datasets via juniper-data generators (fixed seeds)
    ├── baselines.py      # naive + linear ridge + the fixed-Δt LMU foil (TrainableModel-shaped)
    ├── run_benchmark.py  # walk_forward_folds + cross_validate + score; emit results JSON + report
    ├── app_e2e.py        # I2: train/predict/crossval through the app (TestClient or live URL)
    └── results/          # committed run artifacts (JSON) + the generated report
pyproject.toml            # new [bench] extra: juniper-data, numpy (model/crossval already deps)
```

- **`[bench]` extra** pulls `juniper-data` (for the generators) — kept optional so the app's runtime
  deps are unchanged.
- Runnable as `python -m bench.run_benchmark` (writes `bench/results/`), reproducible from a seed.
- **Alternative considered:** a `util/` harness in juniper-ml. Rejected — the harness imports the
  model/app/generators, which read most naturally from the recurrence repo.

## 8. The report (the deliverable)

`run_benchmark.py` emits:

- `bench/results/<dataset>_<timestamp>.json` — raw per-fold metrics for every model (reproducible).
- A generated **markdown report** (`bench/results/REPORT.md`) — the per-dataset × per-model table,
  the Δt-contribution deltas, and a pass/fail line against each §6 band.
- A short **narrative `notes/` doc** in juniper-ml summarizing the finding (the OQ-7 "completed-state"
  verdict) and linking the raw results.

## 9. Risks and guardrails

| Risk | Guardrail |
|---|---|
| Dataset cherry-picking | datasets + grid **pre-registered** in §3/§4; report the full grid (DP-5) |
| Fixed-Δt foil not a fair control | reuse the §9.1a `FixedStepLMUMemory` math; same fold splits; only `dt` differs |
| Temporal leakage in CV | `walk_forward_folds` expanding + embargo; assert `max(train target_time) < min(test target_time)` |
| `cross_validate` over-abstraction (RK-4) | drive ≥2 callers (LMU + baselines) through the same API; serial v1 |
| p-hacking the grid | fixed small grid, reported in full, not best-cell |
| Non-reproducibility | fixed seeds everywhere; commit the results JSON |
| Result misread as a trading claim | report is a *research* Δt-thesis check on synthetic data; no financial claim |

## 10. Implementation plan (one PR, `pcalnon/juniper-recurrence`)

1. `bench/datasets.py` — generate the §3 datasets (fixed seeds) via the juniper-data generators.
2. `bench/baselines.py` — naive, linear ridge, fixed-Δt LMU foil (TrainableModel-shaped).
3. `bench/run_benchmark.py` — `walk_forward_folds` + `cross_validate` + `score`; emit results + report.
4. `bench/app_e2e.py` — I2 e2e proof via the app (`/v1/train` → `/v1/predict` → `/v1/crossval`).
5. `pyproject.toml` — `[bench]` extra (`juniper-data`); a couple of harness unit tests (shapes,
   leakage assertion, determinism) under `tests/`.
6. Run it; commit `bench/results/` + the narrative `notes/` doc; evaluate vs §6 bands.

Worktree off `juniper-recurrence` `main`; PR; no merge without Paul's explicit signal.

## 11. Cross-references

- Canonical roadmap (Wave-2 exit; C2/I2; DP-5/DP-3; OQ-14): [`JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md`](JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md)
- Crossval / fold-executor layer (the `cross_validate` API): [`JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md`](JUNIPER_MODEL_CORE_CROSSVAL_LAYER_DESIGN_2026-06-16.md)
- LMU numeric design + the §9.1a fixed-Δt negative control: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Δt math + windowing invariants (I1–I5) + the grid-invariance bound: [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md)
- Dataset audit (which datasets need the Δt path): [`JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md`](JUNIPER_RECURSE_OQ4_DATASET_AUDIT_2026-06-13.md)
- App `/metrics` (sibling fast-follow, same as-built pattern): [`JUNIPER_RECURRENCE_METRICS_ENDPOINT_DESIGN_2026-06-18.md`](JUNIPER_RECURRENCE_METRICS_ENDPOINT_DESIGN_2026-06-18.md)
- Generators / executor source (cross-repo): `juniper-data/juniper_data/generators/{irregular_sine,multi_sine,mackey_glass}/`; `juniper-ml/juniper-model-core/juniper_model_core/crossval/{executor,splits,metrics}.py`
