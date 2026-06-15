# Juniper-Recurrence WS-4 — Fixed-Order LMU Regressor: Model-Build Implementation Plan

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; build lands in pcalnon/juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (RATIFIED build plan — decisions D-WS4-1…3 concurred by Paul 2026-06-15)
**Last Updated**: 2026-06-15

---

> **What this is.** The concrete build plan for **WS-4 — the model build**: turning the
> already-scaffolded `VariableStepLMUMemory` cell into a `juniper_model_core.TrainableModel`
> implementation — a standalone, fixed-order, Δt-native LMU **regressor**. It is the
> implementation-side complement to the canonical
> [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
> (Parts 3/4/6) and the
> [`…CASCOR_3D_INGESTION_GATE_2026-06-14.md`](JUNIPER_RECURSE_OQ4_CASCOR_3D_INGESTION_GATE_2026-06-14.md)
> Part-9c decision (Path B, plan-first). It **does not restate** their theory; it pins file
> layout, the contract mapping against the *as-shipped* `juniper-model-core` (#416), the
> numeric design, the test/conformance matrix, and PR sequencing.

---

## 0. Status & provenance (verified on disk, 2026-06-15)

| Prerequisite | State |
|---|---|
| WS-0 model pick (P3-C/LMU + Approach-C) | **RATIFIED** 2026-06-14 |
| WS-1 data foundation (3-D NPZ + Δt + temporal split + `equities_seq`) | **SHIPPED** (juniper-data #169/#170/#171 + data-client #87, 2026-06-09) |
| WS-3 `juniper-model-core` (interfaces + conformance kit) | **SHIPPED** as juniper-ml #416; present in this repo at `juniper-model-core/` |
| `pcalnon/juniper-recurrence` repo + `juniper-recurrence-model` package | **SCAFFOLDED** (`f94c254` core, `d2b5588` CI/publish); `VariableStepLMUMemory` + grid-invariance test only. No open PRs/branches/worktrees. |

**Placement is already correct (§6.7).** The model is model-specific → its own repo
`pcalnon/juniper-recurrence`, package `juniper-recurrence-model` (subdir, mirroring
`juniper-cascor-protocol`). The earlier handoff phrase *"D4 juniper-ml subdir package"* was a
compression of detailed-design §6.3: the D4 juniper-ml-subdir package is **`juniper-model-core`**
(the dependency the LMU *plugs into*), **not** this package. Nothing for WS-4 belongs in
juniper-ml except this plan doc.

**This build is standalone (D-WS4-3).** The handoff's *"fronting the 2-D cascade head"* is the
**separate, deferred** cascor-integration (detailed-design §9.1c / the ingestion-gate doc); the
standalone regressor has its **own** readout and does **not** touch cascor.

---

## 1. The gap WS-4 closes

`juniper-recurrence-model` today ships the memory **unit** (`units/lmu_varstep.py`:
`VariableStepLMUMemory` + `lmu_matrices`) and its grid-invariance test. There is **no model**:
nothing implements `juniper_model_core.TrainableModel`, nothing consumes a 3-D NPZ window or the
`dt` channel at the model level, nothing trains a readout. The package `pyproject.toml` does not
yet depend on `juniper-model-core`. WS-4 adds the model layer that wraps the fixed memory.

---

## 2. Ratified decisions (Paul, 2026-06-15)

- **D-WS4-1 — Per-feature identity read-in.** Each of the `F` input features drives its **own**
  order-`d` LMU memory through the **same** fixed `A`/`B`/θ. No trained read-in projection; the
  per-window memory state is the concatenation `M ∈ ℝ^{F·d}`. **Only the readout is trained.**
  (A trained `F→k` projection read-in and/or a nonlinear readout is the deferred increment 1(b);
  it is the point at which torch enters — see §8.)
- **D-WS4-2 — `target_dt` as a readout feature.** The irregular forecast horizon `target_dt`
  is concatenated to the readout design matrix (alongside the memory state + bias). Memory-advance
  by `target_dt` is **not** done in the first cut.
- **D-WS4-3 — Standalone scope.** Deliver the standalone fixed-order regressor only. Deferred:
  cascor 3-D ingestion / cascade-head fronting (§9.1c), `juniper-service-core` + the FastAPI/CLI
  app (C2), canopy (WS-5), the grown-cascade form (§4.2), distributed worker (WS-8).

---

## 3. Architecture — numpy-only, closed-form

The model is `juniper_model_core.conformance.ReferenceLinearModel` with one substitution: replace
its `_flatten(X)` feature map with a **dt-aware roll-through-the-fixed-LMU-memory**, keep the
**closed-form `lstsq` readout**. The memory matrices are fixed and never differentiated, so no
autodiff framework is required (this is the literal content of C1-clean, detailed-design §3.4).

```
X (n, T, F)                        dt (n, T)            target_dt (n,)
    │  per feature f: drive u_f = X[:, :, f]   │                 │
    ▼                                          ▼                 │
  F parallel order-d LMU memories  ──ZOH at per-step dt──▶  m_f ∈ ℝ^d
    │  (FIXED A/B/θ; eigenbasis rollout; no grad)                │
    ▼  gather at readout step(s) per readout_mask                ▼
  M ∈ ℝ^{n × (F·d)} ───────────────────────▶ Φ = [ M | target_dt | 1 ]
                                                     │ closed-form ridge/lstsq
                                                     ▼
                                                 ŷ (n, output_dim)   (regression)
```

- **Read-in**: identity (feature = its own scalar drive). No parameters.
- **Memory**: `F` parallel order-`d` memories sharing one fixed eigendecomposition (reuse the
  unit's precomputed `lam`/`V`/`Vinv`/`VinvB`). Fixed ⇒ no grad.
- **Readout**: closed-form least squares (optionally L2-regularized ridge) from
  `[M | target_dt | bias]` → target. Deterministic, fast, numpy-only. This *is* the single
  trained surface.

---

## 4. The batched memory rollout (the one substantial new numeric component)

`VariableStepLMUMemory.rollout` is single-sequence, scalar-`u`. WS-4 adds a **batched, multi-feature**
rollout that reuses the unit's precomputed eigendecomposition and rolls in the **eigenbasis** so
each step is elementwise (no per-sample `d×d` matmul):

- State in eigen-coordinates `p ∈ ℂ^{n × d × F}`, init 0.
- Per step `k = 1…T-1`, with `z = lam[None,:,None] · (dt[:, k, None, None] / θ)` (shape `(n,d,1)`):
  - `p ← exp(z) ⊙ p + (expm1(z)/lam) ⊙ (VinvB ⊙ u[:, k-1, :])`  (removable-singularity guard as in the unit)
  - real memory state `M_k = Re(V @ p)` → `(n, d, F)`.
- `dt`-bucket caching: equities gaps are integer calendar-days (1–7); cache `exp(z)`/`expm1(z)/lam`
  per distinct gap to avoid recomputation (detailed-design §3.3/§3.6).
- The numpy `VariableStepLMUMemory` stays the **validation oracle**: a parity test asserts the
  batched rollout matches per-feature `rollout()` to tolerance, so the existing grid-invariance
  test keeps covering the math.

No `dt[:,0]` use (empty initial window); padded steps beyond `seq_lengths` contribute nothing
because the readout gathers only masked positions.

---

## 5. `TrainableModel` contract mapping (against `juniper-model-core` #416, verified)

| Contract member | LMU implementation |
|---|---|
| `task_type` | `"regression"` (set in `__init__`) |
| `random_seed` | stored; fit is deterministic regardless |
| `fit(X, y, *, X_val, y_val, on_event, **kw)` | reads `dt`/`readout_mask`/`seq_lengths` from `**kw` (D3); rolls memory (no grad); gathers `M` at masked steps; closed-form `lstsq` of `[M\|target_dt\|1]→y`; emits `training_start`→`epoch_end`(epoch 0)→`training_end` with monotonic `seq`; returns `TrainResult(final_metrics, n_epochs=1, history=[…], stopped_reason="converged")` |
| `predict(self, X, *, dt=None, target_dt=None, readout_mask=None, seq_lengths=None)` | **signature widened with optional keywords** (LSP-safe; ABC checks the name only). The conformance kit calls bare `predict(X)`; when `dt` is absent default to **uniform `dt=1`**, `target_dt=0`, **last-valid-step** readout. Returns continuous values — **never `argmax`** (RK-6). |
| `metrics()` | `{mse, rmse, mae, r2, loss}` (⊆ `REGRESSION_METRIC_KEYS`); never `accuracy` |
| `describe_topology()` | `model_type="lmu"`; nodes `input`(F) + `memory`(`kind="memory"`, `frozen=True`) + `output`; edge `memory→memory recurrent=True` + `memory→output`; `meta={n_units:0, task_type:"regression", theta, d, time_unit}` |
| `input_shape` / `output_shape` | `(T, F)` / `(output_dim,)` (e.g. `(1,)` for next-close) |
| serializer (optional) | `LMUSerializer` (npz readout coef + JSON meta `{d, θ, time_unit, in/out shape, metrics}`); recompute memory from `d`/θ on load → `array_equal` lossless-roundtrip holds |

**Why bare `predict(X)` is sound here.** `tiny_regression_3d` supplies `dt` only in `fit_kwargs`;
the kit's `predict(X_val)` passes none. Conformance asserts prediction **shape** + valid **metrics**
(the stored train metrics), not prediction *quality*, so the uniform-`dt` fallback passes the kit;
real callers (and the R-Δt-3 test) pass `dt` explicitly to engage the Δt path.

---

## 6. `dt` / `target_dt` / mask / lengths mechanics

- **`dt (n,T)`** — the per-step ZOH gap; `dt[:,0]=0` unused; drives `exp(z)`/`expm1(z)` per step. *This is the Approach-C win* (the channel cascor drops at its boundary today, §9.1c).
- **`target_dt (n,)`** — concatenated as a readout column (D-WS4-2), making the irregular horizon explicit to the linear map.
- **`readout_mask (n,T)` bool** — selects supervised/readout steps; equities_seq is many-to-one (final valid step). Dense many-to-many is supported (more design rows) but untested in the first cut.
- **`seq_lengths (n,)`** — bounds the valid prefix (≤ `T_max`); padded tail masked out of the readout gather.

---

## 7. Test & conformance matrix

| Test | Asserts | Source |
|---|---|---|
| existing `test_lmu_grid_invariance.py` | unit math (stability, `e_reg`, `e_irr` grid-invariance) | already shipped |
| **batched-rollout parity** | batched eigenbasis rollout == per-feature `VariableStepLMUMemory.rollout()` to tol | NEW |
| **conformance suite** | subclass `TrainableModelConformance`; `make_dataset → tiny_regression_3d()`; runs isinstance/fit/predict-shape/metrics-keys/no-accuracy(RK-6)/topology/event-order/serializer-roundtrip | model-core kit |
| **fit/predict known-answer** | recovers a linear-over-memory synthetic; R² high | NEW |
| **R-Δt-3 shuffle-`dt`** | metrics degrade when `dt` is shuffled vs. true gaps → proves the model *uses* timing | NEW (guardrail) |
| **determinism** | same seed/inputs → identical coef & predictions | NEW |
| **overfit-tiny** | memorizes a tiny set (near-zero train MSE) | NEW |
| **§9.1a negative-control reconciliation** | port `FixedStepLMUMemory` from the juniper-ml POC (`verify_delta_t_reference_code.py`, item (a) **DONE**) into the package; assert fixed-Δt *fails* the bound the variable-step passes; **delete the stale `TODO §9.1a`** in `test_lmu_grid_invariance.py` | reconciliation |

`T=1`-identity is **N/A** for a standalone model (that golden gate belongs to the cascor cutover).

---

## 8. Packaging & dependency ordering

- Add `juniper-model-core` to `juniper-recurrence-model` deps. **Publish-first (§6.8):** the
  published wheel may not pin `juniper-model-core` until it is on PyPI (TestPyPI soak first).
  **Action:** confirm model-core's PyPI status; until published, dev/CI install it **editable from
  the sibling clone** (the `docs-full-check.yml` cross-repo-clone pattern) and gate the
  `juniper-recurrence-model` release on model-core publish-first.
- **No torch** for the first cut (numpy-only; consistent with the package's current
  `dependencies = ["numpy>=1.24"]` and its own pyproject note). Torch enters only with increment
  1(b) (trained projection read-in / nonlinear readout).
- Dev env: reuse `JuniperCascor1` (OQ-16) — numpy-only build needs no dedicated env.
- CI: extend `ci-recurrence-model.yml` to install model-core (editable, pre-PyPI) before `pytest`.

---

## 9. PR sequencing (worktree off `juniper-recurrence` `main`, per worktree procedures)

1. **PR-1 — model + core tests.** Batched rollout + `LMURegressor(TrainableModel)` + `LMUSerializer`;
   parity / known-answer / determinism / overfit-tiny tests; pyproject `juniper-model-core` dep +
   CI editable-install wiring; CHANGELOG.
2. **PR-2 — conformance + Δt guardrails.** `TestLMUConformance(TrainableModelConformance)` against
   `tiny_regression_3d`; R-Δt-3 shuffle-`dt`; §9.1a `FixedStepLMUMemory` negative-control port +
   stale-TODO deletion.

(Collapsible into one PR if review prefers; kept split so the contract-conformance lands as a
discrete, reviewable unit.) **No merge without Paul's explicit per-PR merge signal + `gh pr view`
MERGED confirmation** (standing rule).

---

## 10. Explicitly out of scope (deferred, trigger-gated)

cascor 3-D ingestion + cascade-head fronting (§9.1c) · `juniper-service-core` + FastAPI/CLI app (C2)
· canopy generalization (WS-5) · grown-cascade LMU candidate (§4.2) · distributed recurrent worker
(WS-8) · trained projection read-in / nonlinear readout (increment 1(b)) · walk-forward split (WS-4 data, already deferred).

---

## 11. Risks touched

`RK-3` (LMU regression unproven → golden known-answer + overfit-tiny) · `RK-6` (classification
leak → conformance `no-accuracy` + regression metric keys) · `R-Δt-3` (Δt-presented≠Δt-used →
shuffle-`dt`) · `R-Δt-5` (eigenvector conditioning → keep `d ≲ 64`; `expm1`) · `R-Δt-8` (C1
pushback → fixed-matrix readout, numpy-only) · **publish-first ordering** (model-core must reach
PyPI before the recurrence wheel pins it, §6.8).

---

## 12. Cross-references

- Canonical model design: [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md) (Parts 3/4/6; §9.1 current work; OQ-19/20 ratified).
- Build-side gate (Path A vs B): [`JUNIPER_RECURSE_OQ4_CASCOR_3D_INGESTION_GATE_2026-06-14.md`](JUNIPER_RECURSE_OQ4_CASCOR_3D_INGESTION_GATE_2026-06-14.md).
- Δt math + reference code + the (now-DONE) fixed-Δt negative control: [`JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md`](JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md); POC `util/ad-hoc/verify_delta_t_reference_code.py`.
- Placement & naming: [`JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md`](JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md).
- Contract being implemented: `juniper-model-core/juniper_model_core/{interfaces,topology,events,validation,serialization,conformance}.py` (#416).
