# Juniper-Recurrence — DP-3 Readout-Spectrum Design

**Project**: juniper-recurrence — Recurrent / Constructive Neural-Network Application
**Repository**: design notes hosted in pcalnon/juniper-ml; model in pcalnon/juniper-recurrence (`juniper-recurrence-model/`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.2.0 (revised after independent sub-agent validation — see Appendix A)
**Last Updated**: 2026-06-20

---

> **What this is.** The design-of-record for **DP-3** — making the LMU regressor's *readout* (its only
> trained surface) a **configurable spectrum**, from the cheap data-ranked lever (a regularized linear
> readout) through a numpy nonlinear readout to an optional torch-backed learned readout. It is the
> "design-first" half of the 2026-06-19 plan's step 3; implementation in `juniper-recurrence-model`
> follows ratification. **This v0.2.0 incorporates four independent adversarial sub-agent reviews**
> (conformance/serialization, ML soundness, packaging/determinism, API/backcompat) — Appendix A.
>
> **Why now.** The §3.2 re-bench
> ([`JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md))
> showed the `equities_seq` r²≈−50 "failure" was **dominantly an unregularized-readout artifact** (the
> bench's `ridge=0` default), not target non-stationarity — and that on a stationary **log-return**
> target a *regularized* readout reaches the efficient-market predictability ceiling (r²≈0) and beats
> linear ridge. The readout, not the memory, is where the action is. DP-3 was ranked
> "build-for-insight, not strictly indicated"; Paul elected to build it anyway, **scoped as a spectrum**
> so it subsumes the cheap regularization lever (juniper-recurrence#28) and the nonlinear-readout
> insight in one coherent design.

---

## 1. Scope and non-goals

**In scope.** The *readout* of the standalone fixed-order LMU regressor (`LMURegressor` in
`juniper-recurrence-model/juniper_recurrence_model/model.py`): the trained map from the per-window LMU
memory state `M ∈ ℝ^{F·d}` (plus the `target_dt` horizon and a bias) to the regression target.

**Non-goals (unchanged from WS-4 §10).** The fixed LMU memory operator (`VariableStepLMUMemory` — the
A/B matrices stay closed-form and untrained, C1-clean); a trained `F→k` *read-in* projection; dense
many-to-many readout; cascor-cascade integration; classification. This design touches **only** the
readout; the Δt memory rollout is unchanged. **D-WS4-1/3 and the "memory is the only fixed surface"
invariant are preserved; D-WS4-2 (`target_dt` as a readout feature) is preserved by §6's boundary rule.**

## 2. Background: what exists today

- **Memory feature map (fixed, float64).** `VariableStepLMUMemory.rollout_batch(X, dt)` → trajectory
  `(n, T, F, d)`; the regressor gathers the readout step → memory state `M (n, F·d)`. For equities
  `F=10, d=16 → 160` memory columns; for the synthetic single-channel case `F=1`.
- **Readout (trained).** `LMURegressor._features` builds the design matrix `[ M | target_dt? | 1 ]`
  (162 cols for equities), then `ridge==0.0` (default) → `np.linalg.lstsq`; `ridge>0.0` → ridge normal
  equations (bias never penalised). A `ridge` parameter **already exists**.
- **Public surface that is load-bearing today** (verified against tests): the constructor
  `LMURegressor(d, theta, *, ridge, time_unit, random_seed)`; `model._coef` (read by `LMUSerializer`
  and asserted in `tests/test_lmu_model.py`); `model._uses_target_dt`; `describe_topology()["meta"]`
  keys `d, theta, time_unit, n_features, n_units, task_type` and top-level `model_type=="lmu"`
  (`juniper-recurrence/tests/test_routes.py` asserts `meta["d"]==4`; the client test asserts
  `model_type=="lmu"`); `LMUSerializer.save/load`. The **shipped WS-4b app imports `LMURegressor` and
  `LMUSerializer` directly** in 4 places and exposes `ridge` over HTTP (`schemas.py`, `settings.py`,
  CLI). Backcompat is therefore a cross-repo, shipped-API concern — not just internal tests.
- **Packaging.** `juniper-recurrence-model` is deliberately **numpy-only**
  (`dependencies = ["numpy>=1.24", "juniper-model-core…"]`). Its own pyproject note already flags a
  "torch-backed … nonlinear readout" as *the* deferred increment.

## 3. Design constraints (the hard contract)

From the `juniper-model-core` conformance kit (`juniper_model_core/conformance/suite.py`, verified):

| Constraint | Source | Implication |
|---|---|---|
| `isinstance(TrainableModel)` + `task_type ∈ {classification,regression}` | `test_isinstance`/`test_declares_task_type` | keep the surface |
| `fit` → `TrainResult(n_epochs≥1, non-empty final_metrics)` | `test_fit_returns_train_result` | closed-form → `n_epochs=1`; torch → `n_epochs=N` |
| valid **regression** metric keys, **no `accuracy`** (RK-6) | `test_metrics_*` | reuse `_regression_metrics` |
| `predict(X_val)` (no aux kwargs) → shape `(n, *output_shape)` | `test_predict_output_shape` | **the kit calls bare `predict(X)`** — uniform-Δt fallback must keep working |
| renderable topology; `meta["task_type"]==task_type`; node `kind ∈ {input,hidden,output,memory,reservoir}` | `test_describe_topology_renderable` + `validation.py` | readout descriptor goes in a **nested** `meta["readout"]`; readout nodes reuse `hidden`/`output` |
| legal event order: exactly one `training_start` … `training_end`, **non-decreasing `seq`** | `test_event_ordering`/`legal_event_order` | a multi-epoch torch readout threads one `seq` counter, bookends once |
| **lossless serialization** — `np.array_equal(pred_before, pred_after)` (**bit-exact**) | `test_serialization_roundtrip_lossless` | **the single sharp constraint** (see below) |

**Verified central finding: the kit has NO fit-quality / "overfit-tiny" assertion.** Every
prediction-touching check tests *shape*, *metric-key legality*, or *serialization equality* — never
error magnitude. (The "overfit-tiny" property is only a *package* unit test, `test_lmu_model.py`, and
the min-norm `lstsq` does **not** even reproduce the kit's n=48/d=16 fixture exactly.) Corollaries:
regularized **and** nonlinear readouts conform — including a **numpy-only** nonlinear one. The only
sharp constraint is **bit-exact lossless serialization**, which means:

- **numpy readouts** must persist *every fitted array* (coef, and for RFF the sampled `W,b` **and** the
  per-column standardization stats), and the predict path must be bit-stable. Note `predict` for a
  nonlinear readout recomputes `cos(W·m+b)` of a matmul of `m` — and `m` is itself recomputed from
  `d/θ` on load; any BLAS/threading drift in that recompute is amplified by `cos` into an
  `np.array_equal` **failure**. RFF losslessness is therefore **gated by a round-trip conformance
  subclass**, not assumed ("trivially lossless" was wrong — Appendix A/Agent 1). Also: a NaN anywhere
  in the val predictions fails `array_equal` spuriously (NaN≠NaN) → predictions must be finite.
- **torch readout** must be **CPU-only on the serialization path**, a **single fixed dtype end-to-end**
  (float32 is fine — bit-exactness is *self-consistency*, not agreement with the numpy rungs),
  `eval()` (no dropout/BN), `torch.use_deterministic_algorithms(True)` + `torch.set_num_threads(1)`,
  and its state persisted as **named npz arrays** (not `torch.save` — the serializer loads with
  `allow_pickle=False`). **No cross-machine bit-exactness is claimed** (torch float forwards are not
  cross-BLAS/-device bit-stable; the kit only re-runs `predict` in-process after load, which is what we
  guarantee).

**Other constraints.** numpy-only base (torch behind an extra); per-fold construction is cheap and
side-effect-free (`cross_validate` calls `model_factory(fold)` fresh, no `reset()`); Python 3.12–3.14
for the base; determinism/repro for the bench. **Backcompat freeze (verified load-bearing):** the
constructor signature, `ridge=0.0` default, `model._coef` (as a forwarding property), `meta["d"]` =
*memory order* (not RFF feature count), `model_type=="lmu"`, and old-format `LMUSerializer.load`.

## 4. The readout spectrum

### Rung 0 — linear least-squares (`ridge=0`) — *exists; keep as default*

Today's default min-norm `lstsq`. **Keep as the constructor default and the conformance instance — for
backcompat only** (the kit imposes no fit-quality gate, and exact tiny-fit is not guaranteed anyway;
the earlier "needed for conformance" rationale was struck — Appendix A/Agent 1). numpy, deterministic,
lossless.

### Rung 1 — regularized linear (`ridge>0`) — *exists; the #28 lever; make it usable*

Already implemented. The §3.2-ranked lever (r²≈−50 vs reaching the ceiling). Work here is selection +
defaults, not mechanism:

- **Keep `ridge=0.0` the constructor default as a hard invariant** (backcompat: `test_overfit_tiny`,
  `test_settings.py::default_ridge==0.0`, `test_routes.py`). GCV is **opt-in**.
- Add closed-form-per-λ **GCV ridge selection** (`ridge="gcv"`): one SVD of the design matrix makes
  each `GCV(λ)=(n·RSS)/(n−tr H)²` evaluation O(p) (`tr H = Σ sᵢ²/(sᵢ²+λ)`); λ is then chosen by a
  cheap **1-D search** over a log-grid — *not* a single closed-form value (Appendix A/Agent 2), but no
  held-out split and no inner-CV refit (≈1–4 s at n≈3000). The **selected λ must be written back to
  `self.ridge`/meta** (the lossless test won't catch its omission — `predict` uses `coef`, not `ridge`
  — but retraining fidelity needs it).
- `ridge="gcv"` widens the type to `float | Literal["gcv"]`; this propagates cross-repo to the app
  `schemas.py` / CLI `--ridge` / `settings.default_ridge` (Appendix A/Agent 4) — scoped in §9 P1.

### Rung 2a — numpy nonlinear readout (random Fourier features + ridge) — *recommended DP-3 build*

A genuine nonlinear readout with **no torch**: standardize the memory block, map it through a fixed
random feature map approximating an RBF kernel (Rahimi & Recht 2007), then ridge on the features.

**Design matrix (precise — Appendix A/Agent 2):** `[ φ(standardize(M)) | target_dt | 1 ]`. RFF is
applied to the **memory block only**; `target_dt` and the bias are appended **linearly** (never passed
through the Gaussian projection — cosine-of-a-constant is degenerate, and the horizon's units differ
from memory units).

- **Mandatory per-column standardization of `M`** (z-score, stats fit on the **train fold only**). The
  Legendre memory columns span ≈**25×** in RMS (high orders carry less energy — measured on the actual
  `VariableStepLMUMemory(d=16)`); an isotropic `W~𝒩(0,γ²I)` with one bandwidth would otherwise let the
  low-order columns dominate `Wm` and silently ignore the fine-grained history the high orders encode.
- **`φ(m)=√(2/D)·cos(Wm+b)`**, `W~𝒩(0,γ²I)`, `b~U[0,2π)`, sampled once at `fit` from `random_seed`.
  **Bandwidth `γ` needs its own selection** (median heuristic on pairwise distances of standardized
  `M`, or a small grid) — **ridge/GCV cannot select γ** (Appendix A/Agent 2).
- **`D` scales with the smallest train fold.** At 5-fold expanding-window walk-forward on n≈3000, the
  first fold trains on ≈600 rows; `D=512` gives `p/n≈0.85` (high-variance) — cap `D` relative to the
  smallest fold; **ridge is mandatory** (`ridge>0` default, GCV-selectable) for this rung.
- **Conformance/serialization:** persist `W,b` as **float64** (matching the float64 pipeline) + the
  standardization stats + γ + λ + coef, all train-fold-only-fit. Lossless is **gated by an RFF
  conformance subclass** (the `cos`-of-matmul bit-stability check), with a finite-prediction assertion.
- **Weaknesses.** A kernel *approximation*, not a *learned* nonlinearity; γ/D are hyperparameters.

### Rung 2b — torch MLP readout — *optional; behind a `[torch]` extra; the "true DP-3"*

A small trained MLP (`F·d → h → h → output`, GELU, weight decay, early stopping on the `X_val/y_val`
`fit` already receives). The first point at which torch + autodiff enter — the WS-4-named deferred
increment.

- **Packaging (corrected — Appendix A/Agent 3).** torch ships **cp314 wheels since torch 2.9.0
  (2025-10-15)**; CPython 3.14.0 final shipped 2025-10-07 — so there is **no Python-3.14 wheel gap**
  for CPU torch. Pin a **torch floor (`torch>=2.9`)** in the `[torch]` extra, *not* a Python ceiling.
  Residual risk is the CUDA/GPU cp314 variant timing — moot for a CPU-only MLP readout.
- **Determinism for the bit-exact round-trip:** CPU-only, single fixed dtype, `eval()`,
  `use_deterministic_algorithms(True)`, `set_num_threads(1)`; state-dict flattened to **named npz
  arrays** (no `torch.save` pickle). No cross-machine bit claim.
- **CI (Appendix A/Agent 3):** a **separate, optional** job (a torch install adds ~1–3 GB) — *not*
  added to the 3.12/3.13/3.14 base matrix; and the torch module must be **excluded from the base job's
  `--cov-fail-under=90`** (otherwise an uninstalled-extra module drops coverage and fails CI).
- **Recommendation: gate it hard.** Given the §3.2 ceiling≈0, a learned readout is **not expected to
  add skill**; build only if Rung 2a's *measured* lift is non-trivial.

### Rung 2c — exact kernel ridge — *noted, rejected* (`O(n²)` at n≈3000; RFF is the scalable substitute).

## 5. Recommendation

1. **Ship Rung 1 properly** — keep `ridge=0.0` default (invariant); add GCV (`ridge="gcv"`, one SVD +
   1-D search) + documented real-data guidance; persist the selected λ. Resolves juniper-recurrence#28.
2. **Build Rung 2a** (standardize → RFF → GCV-ridge) as the **primary DP-3 insight build** — numpy-only,
   deterministic, conformance-clean.
3. **Gate Rung 2b** (torch MLP) behind a `[torch]` extra; build only if 2a's measured lift warrants.

**Honest expected outcome (Appendix A/Agent 2).** The linear readout is *already at the ceiling*
everywhere measured: r²=0.988 on `irregular_sine` (≤1.2% headroom, mostly memory-truncation a readout
cannot recover) and r²=0.9999 on `mackey_glass` (≤0.01%). So the realistic P2 result is a **tie to ~3
decimals on the synthetics** and a **tie at the ≈0 ceiling on equities** — *not* "a small win." None of
the three current datasets has a target the linear readout provably *can't* fit, so 2a can **confirm
the absence of a nonlinear benefit here** but cannot, alone, demonstrate nonlinear *capacity*. The
deliverable is therefore an **instrument** (quantify the linear→nonlinear gap; confirm the ceiling),
and it is correctly ranked **below** the target-conditioning work the data already endorsed (shipped in
juniper-data 0.8.0). A capacity-demonstrating dataset (a target that is a genuine nonlinear functional
of recent history) is possible future work (§8 Q3).

## 6. Integration

- **API — an immutable readout *spec* (frozen dataclass), not a live object (Appendix A/Agent 4).**
  `LMURegressor(d, theta, *, readout=None, ridge=0.0, time_unit, random_seed)`. When `readout is None`,
  build `LinearReadoutSpec(ridge=ridge)` → `LMURegressor(d, theta, ridge=…)` is byte-identical to
  today. Reject passing both a non-default `ridge` and a non-linear `readout` (one source of truth).
  A **spec** (not a constructed readout) avoids the cross-fold trap: a shared live readout instance in
  a `lambda i: LMURegressor(readout=ro)` closure would have fold *k*'s `fit` overwrite fold *k−1*'s
  `W,b`/coef under a parallel `map_fn`. `W,b`/stats are sampled inside `fit()` from `random_seed`
  (data-independent, fixed across folds), never from a module-global RNG.
- **Readout receives `M` only; `LMURegressor` keeps owning `target_dt` + bias (preserves D-WS4-2).**
  `target_dt` is a **linear side-channel appended *after* any nonlinearity**; bias is the readout's
  concern. `model._coef` stays as a **read-only forwarding property** to the linear readout's
  coefficients (keeps the serializer's unfitted check + `test_lmu_model.py` green); `None` for
  non-linear readouts (the "unfitted" check moves to `readout.is_fitted`).
- **Serialization — registry + old-format fallback.** Each readout owns `save_state()/load_state()`
  returning/consuming **named numpy arrays + a JSON-safe descriptor with a `kind` tag**
  (`"linear"|"rff"|"mlp"`); `LMUSerializer.save` writes `meta["readout"]=descriptor` (+ a `schema`
  version) and namespaces the arrays; `load` reads `meta["readout"]["kind"]`, looks it up in a registry,
  and reconstructs. **A file with no `meta["readout"]` (pre-DP-3) defaults to
  `LinearReadout(ridge=meta["ridge"])` + `coef`.** The LMU **envelope meta** (`d, theta, time_unit,
  n_features, uses_target_dt, in/out shape, task_type`) is still persisted alongside the readout state.
  All descriptors stay JSON (npz `allow_pickle=False`).
- **Topology.** Add a **nested** `meta["readout"]={kind,…}`; **freeze** `model_type=="lmu"` and the
  existing `meta` keys (esp. `meta["d"]` = memory order). Any readout *node* uses a legal `kind`
  (`hidden`/`output`).
- **crossval + bench.** Each readout is a `TrainableModel` factory (`lambda i: LMURegressor(readout=…
  Spec)`). Extend `bench/run_benchmark.py` with the nonlinear row (informational; expect a tie — §5).
- **App / HTTP edge (Appendix A/Agent 4).** The shipped app imports `LMURegressor`/`LMUSerializer`
  directly and exposes `ridge` over HTTP. Exposing readouts/GCV over `/v1/train`·`/v1/crossval` needs a
  `readout: Literal["linear","rff","mlp"]` enum + per-readout param fields (a tagged enum at the edge,
  even though the Python API uses a spec object) and the `ridge: float|Literal["gcv"]` widening in
  `schemas.py`/CLI/`settings`. **Scope the HTTP exposure into P2, or explicitly defer it** (an internal-
  only readout the app can't reach buys nothing).
- **Conformance.** Add `RFFReadout` (and, under the extra, `MLPReadout`) conformance subclasses — the
  bit-exact round-trip + a finite-prediction assertion are the checks that matter. The existing
  `LinearReadout(ridge=0)` instance is unchanged.

## 7. Risks and guardrails

| Risk | Severity | Guardrail |
|---|---|---|
| torch turns the numpy-only base heavy / leaks into the app | High | torch only in a `[torch]` extra (verified: a plain dep never activates another pkg's extras, so the app stays torch-free); base import path never imports torch (lazy import inside the readout) |
| **RFF `cos`-of-matmul breaks bit-exact `np.array_equal`** | High | persist `W,b` (float64) + standardization stats; **gate with an RFF round-trip conformance subclass** (not assumed); assert finite predictions (NaN≠NaN trap) |
| torch forward not bit-exact across save/load | High | CPU-only path, single fixed dtype, `eval()`, `use_deterministic_algorithms(True)`, `set_num_threads(1)`; state as named npz arrays (no `torch.save`); **no cross-machine claim** |
| ~~torch wheels lag Python 3.14~~ **(corrected)** | n/a | torch ships cp314 since 2.9.0; pin `torch>=2.9` floor, not a Python ceiling; residual = GPU cp314 only (moot for CPU MLP) |
| nonlinear readout overfits low-signal data | High | nonlinear rungs **regularize by default** (`ridge>0`/weight decay) + GCV — the §3.2 lesson as a default |
| CV leakage via standardization/γ/λ fit on full data | High | **all** of {per-column mean/std, γ, λ, `W,b`} fit on the **train fold only**; persisted in readout state |
| GCV-selected λ not persisted | Low (lossless test can't catch it) | write the selected λ to meta for retraining fidelity |
| CI coverage gate (`--cov-fail-under=90`) drops on the uninstalled torch module | Med | exclude the torch module from the base job's coverage; run the torch job separately with its own coverage |
| over-engineering vs ceiling≈0 | Med | phase it (§9); **gate 2b on a measured 2a lift**; each rung independently useful |
| API churn (shipped app + tests + HTTP) | Med | `LMURegressor(d, theta, ridge=…)` stays byte-identical; `_coef` forwarding property; old-format `load`; frozen `meta` keys; this is a **careful two-repo refactor**, not "tens of lines" |
| base numpy round-trip is bit-exact only on a *pinned* numpy/LAPACK stack (`eig`/`inv`) | Low | honesty note; absorbed by basis-invariant reconstruction; same realism that makes "persist W,b" correct |

## 8. Open questions for ratification

1. **Readout API shape** — recommended: an **immutable spec** internally + a **tagged enum + params at
   the HTTP edge**. Confirm.
2. **Default ridge** — recommended **hard invariant `ridge=0.0`**; GCV opt-in via `ridge="gcv"`. Confirm
   the cross-repo type widening (model + app schemas/CLI/settings) lands in P1 or is deferred.
3. **Build 2b (torch) now or gate** — recommended **gate** (build 2a first; 2b only on a measured lift).
   Also: do we want a **capacity-demonstrating nonlinear dataset** so 2a/2b can show an *upside*, not
   just confirm a tie?
4. **2a feature map** — RFF/RBF (recommended) vs polynomial vs both.
5. ~~Separate `…-model-torch` package~~ — **closed**: use the `[torch]` extra (a separate package
   doubles publish/CI surface for a maybe-never rung; note the meta-package `recurrence`/`tools` extra
   pins would also need updating if a new package appeared).
6. **HTTP exposure** — expose readout selection over the app API in P2, or defer (internal-only first)?

## 9. Phasing (PR plan)

- **P1 — readout-spec refactor + Rung 1 (GCV).** Extract the `Readout` protocol + `LinearReadoutSpec`;
  `LMURegressor` delegates; **byte-identical backcompat** (`_coef` forwarding property, frozen `meta`,
  old-format `LMUSerializer.load` fallback, exact 3-event stream for the linear path); GCV ridge
  selection; `ridge: float|Literal["gcv"]` widening propagated to the app schemas/CLI/settings.
  Resolves juniper-recurrence#28. *(numpy; a careful two-repo refactor — not trivial.)*
- **P2 — Rung 2a (RFF).** `RFFReadoutSpec` (standardize → RFF → GCV-ridge, train-fold-only, `D` capped
  to the smallest fold) + RFF conformance subclass + serializer registry/schema-version + bench row +
  findings-doc update (linear-vs-nonlinear: expect a tie, confirm the ceiling) + (decision §8 Q6) the
  HTTP enum. *(numpy)*
- **P3 — Rung 2b (torch), gated.** `MLPReadoutSpec` behind `[torch]`; CPU/dtype/thread determinism;
  named-npz state; separate optional CI job + coverage exclusion; bench row. Build only if P2 warrants.
  *(torch)*

## 10. Cross-references

- Evaluation findings (motivating §3.2):
  [`JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md`](JUNIPER_RECURRENCE_EVALUATION_FINDINGS_2026-06-18.md)
- WS-4 model build plan (ratified D-WS4-1/2/3 + "torch enters here"):
  [`JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4_MODEL_BUILD_PLAN_2026-06-15.md)
- LMU numeric design:
  [`JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md`](JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md)
- Readout-regularization follow-up: juniper-recurrence#28 · target-conditioning: juniper-data#195 · bench: juniper-recurrence#29
- Reference: Rahimi & Recht (2007), *Random Features for Large-Scale Kernel Machines*, NeurIPS.

## Appendix A — independent sub-agent validation (2026-06-20)

Four independent adversarial reviewers read the v0.1.0 draft + the actual code; their findings produced
this v0.2.0. Summary of what each changed:

- **Conformance & serialization.** Confirmed the central "no fit-quality gate" thesis. Struck the false
  "exact tiny-fit needed for conformance" rationale (the fixture isn't fit exactly anyway). Downgraded
  RFF "trivially lossless" → gated by a round-trip subclass (`cos`-of-matmul amplifies ULP drift in the
  recomputed memory). Stated torch's bit-exact requirements precisely (no cross-machine claim). Added
  overlooked sub-contracts: bare `predict(X)`, `output_shape`, legal node `kind`, envelope-meta
  persistence, NaN→`array_equal` trap.
- **ML soundness.** Confirmed the RFF math. Added the **mandatory per-column standardization** of `M`
  (≈25× RMS disparity across Legendre orders, measured), **separate γ selection** (ridge can't pick γ),
  the explicit `[φ(standardize(M))|target_dt|1]` design, and `D`-scaled-to-smallest-fold. Corrected
  "GCV closed-form" → one SVD + 1-D search. Replaced "small synthetic win" with the headroom arithmetic
  (tie to ~3 decimals) and the "can't demonstrate capacity on current datasets" caveat. Added the
  train-fold-only leakage guardrail.
- **Packaging / determinism.** **Corrected the torch-3.14 factual error** (cp314 wheels since torch
  2.9.0) → pin a torch floor, not a Python ceiling. Required CPU-only + single-dtype + thread-pinning
  for the bit-exact round-trip. Forbade `torch.save` (pickle) under the `allow_pickle=False` serializer.
  Added the CI **coverage-gate** risk + separate-job requirement. Confirmed "persist W,b (float64)".
  Confirmed the app stays torch-free (a plain dep never activates extras).
- **API / backcompat.** Surfaced the load-bearing backcompat set (`meta["d"]==4`, `_coef`,
  old-format `load`), the `ridge="gcv"` **cross-repo type change**, and the **D-WS4-2 boundary**
  (readout takes `M` only; `target_dt` linear side-channel). Recommended the **immutable spec** over a
  live object (cross-fold state trap) and the **registry + old-format fallback** serializer mechanism;
  noted the HTTP edge re-introduces a tagged enum; re-scoped P1 as a careful two-repo refactor.
