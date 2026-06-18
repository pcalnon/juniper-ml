# juniper-model-core — Cross-Validation / Fold-Executor Layer: Design & Build Plan

**Project**: juniper-ml — `juniper-model-core` shared model-contract package
**Repository**: pcalnon/juniper-ml (package subdir `juniper-model-core/`)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.1.0 (RATIFIED — placement concurred 2026-06-16; §4 API ratified D-CV-6…10 by Paul 2026-06-17)
**Last Updated**: 2026-06-17

---

> **What this is.** The design + build plan for the **fold executor / cross-validation layer** —
> the orchestration tier *above* a single model (loop folds → fit each → aggregate) that WS-4b
> explicitly defers (the §A.4 "multi-fold-split needs a fold executor to be useful" dependency).
> It exists in no repo today: every model in the platform is single-fit, and nothing can consume a
> multi-fold split. This layer is the missing piece both consumption routes (indirect via a service
> endpoint / CLI, direct via canopy) block on. It ships as an **optional, model-agnostic submodule of
> `juniper-model-core` (0.2.0)**, built purely on the `TrainableModel` contract.

---

## 0. Status & provenance (verified across the stack, 2026-06-16)

| Fact | State |
|---|---|
| Any CV / fold / walk-forward logic in the ecosystem | **None.** Ecosystem grep clean; every model single-fit. |
| `juniper-data` split surface | `core/split.py:temporal_split_index(n, train_ratio)` = a **single** chronological cut. Walk-forward is **explicitly deferred** (docstring: *"WS-1 / juniper-data#168 scope C, intentionally not implemented"*). NPZ ships a single baked `train`/`test`/`full` split. |
| `juniper-model-core` (0.1.0, PyPI, `dependencies=[]`) | Has the per-fold *step* (the conformance kit's `_fit`: `model.fit(X, y, X_val=…, y_val=…, on_event=…, **fit_kwargs)`) + `validate_metrics` + `REGRESSION_METRIC_KEYS`. **No executor, no `reset()`/`clone()`, no `score(X, y)`.** |
| Consumers | recurrence `LMURegressor` **is** a `TrainableModel` (drivable now); cascor `network.fit()` is torch/history-dict, **not** yet a `TrainableModel` (WS-6). |

**Two routes both block on this layer** (Paul's framing): *indirect* (a compatible dataset selection → a service/CLI runs folds → aggregate) and *direct* (canopy). Neither works without a fold executor.

---

## 1. The two contract gaps the executor surfaces

A second consumer of the model contract reveals two gaps (the CV-analogue of the `predict(**kw)` D3 gap recurrence surfaced):

1. **No `reset()`/`clone()`** — the contract is "construct fresh, then `fit()` once." ⇒ the executor takes a **model factory** `Callable[[int], TrainableModel]` (fold index → fresh model), never a model instance.
2. **No held-out `score(X, y)`** — `metrics()` returns the model's own (train-time) metrics; there is no held-out scoring. ⇒ the executor **computes eval metrics itself** from `predict(eval.X)` vs `eval.y`.

**Decision:** keep scoring *external* (in the CV layer), not in the contract — the `TrainableModel` ABC stays lean. A future optional `score()` on the contract is noted as a possible 0.2.x/0.3 addition if a second need appears, but is **out of scope here**.

---

## 2. Ratified decisions

- **D-CV-1 (Paul, 2026-06-16) — Placement:** the layer is a new **`juniper_model_core.crossval`** submodule behind an optional **`[crossval]`** extra (numpy), shipped in **model-core 0.2.0**. Preserves model-core's deliberate dep-free core import (numpy stays out of the base import path; `crossval` is opt-in). Sits beside the conformance kit, which already drives models the same way. Extract to a standalone `juniper-eval-core` later only if evaluation scope grows.
- **D-CV-2 — Factory-based** (forced by §1.1): fresh model per fold.
- **D-CV-3 — External held-out scoring** (forced by §1.2): a small `metrics` helper computes regression metrics; classification deferred.
- **D-CV-4 — No `juniper-data` change for v1:** the NPZ already ships `*_full` arrays (+ `window_end_date` / `ticker_code` for leakage-safe ordering), so folds are re-derived **client-side** from `_full`. juniper-data#168 scope C (server-side fold materialization) becomes an optional future optimization, not a prerequisite.
- **D-CV-5 — Serial v1:** folds are independent and *could* parallelize, but parallel/distributed execution is deferred to the worker subsystem (OQ-11 / WS-8).
- **D-CV-6 (Paul, 2026-06-17) — 2nd-implementer test:** an **in-repo 3-D `TrainableModel` stub** in model-core's tests proves the executor is model-agnostic (3-D + `aux` slicing); the *real* LMU-CV test lives on the recurrence side. Keeps model-core dependency-clean (no model-core→recurrence import edge / cycle; the dep-free top-level import is preserved).
- **D-CV-7 — Bundle `predict(**kw)` (D3) into 0.2.0:** add `**kw` to the `TrainableModel.predict` ABC **and** widen `ReferenceLinearModel.predict` (`reference.py`) + the 3-D stub to accept-and-ignore it, all in the **same PR**. The ABC edit alone is insufficient — the executor's `m.predict(X[ev], **aux[ev])` raises `TypeError` against an un-widened concrete `predict`.
- **D-CV-8 — Shared metric math:** the regression-metric formulas live in a single private **`juniper_model_core/_metrics.py`** (numpy), imported by both `crossval/metrics.py` and `conformance/reference.py`. It is **never re-exported from `__init__`**, so the dep-free top-level import is preserved (only the numpy-gated consumers import it). A parity test asserts both call sites agree.
- **D-CV-9 — Val-set policy (reconciled to the merged #442 default; Paul concurred 2026-06-17):** `cross_validate` keeps the eval fold **held-out by default** (`pass_eval_as_val=False`) — the rigorous default that avoids eval-fold leakage for models that early-stop on the validation set; `pass_eval_as_val=True` doubles the eval fold as `X_val`/`y_val` for callers that want it. `scheme` is typed **`Literal["expanding", "rolling"]`**. (This supersedes the initially-proposed eval-as-val default after the concurrent #442 build landed the held-out default in working, tested code — the safer scientific choice.)
- **D-CV-10 — Parallelism seam:** per-fold execution is factored into a pure `_run_fold(...)` that `cross_validate` applies via a serial `map` (no parallel impl — honors D-CV-5); this localizes the future WS-8 parallelization to swapping the map.

---

## 3. Architecture (model-agnostic; numpy-only; built on `TrainableModel`)

```text
ordered full arrays            model factory               (X, y, aux: dt/target_dt/seq_lengths)
 X_full,y_full,aux,order  ──►  fold_idx → fresh model  ──►  sliced per fold by index
        │                              │
        ▼  splits.walk_forward_folds   │
   [Fold(train_idx, eval_idx), …]      │
        └──────────────►  executor.cross_validate(factory, X, y, folds, aux=…)  ◄──┘
                                 │  per fold f:
                                 │    m = factory(f)
                                 │    m.fit(X[tr], y[tr], X_val=X[ev], y_val=y[ev], on_event, **aux[tr])
                                 │    ŷ = m.predict(X[ev], **aux[ev])
                                 │    eval = metrics.score(task_type, y[ev], ŷ)   # held-out
                                 ▼
                         CrossValResult(per-fold + mean/std aggregate)
```

Three small parts (all under `juniper_model_core/crossval/`):

1. **`metrics.py`** — held-out scoring.
2. **`splits.py`** — index-based walk-forward fold generation (shape-agnostic: works for 2-D tabular and 3-D sequence, since it returns indices).
3. **`executor.py`** — `cross_validate(...)` (slices all arrays by fold indices, drives the per-fold step, aggregates).

---

## 4. Concrete interfaces (RATIFIED 2026-06-17 — D-CV-6…10)

```python
# crossval/metrics.py
def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """{'mse','rmse','mae','r2','loss'} (loss == mse). Keys ⊆ REGRESSION_METRIC_KEYS."""

def score(task_type: TaskType, y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Dispatch on task_type. regression → regression_metrics; classification → NotImplementedError (v1)."""

# crossval/splits.py
@dataclass(frozen=True)
class Fold:
    train_idx: np.ndarray     # int indices into the ordered full arrays
    eval_idx:  np.ndarray

def walk_forward_folds(
    n_samples: int, *, n_folds: int, scheme: Literal["expanding", "rolling"] = "expanding",
    min_train: int | None = None, embargo: int = 0,
    order: np.ndarray | None = None,                              # e.g. window_end_date; enforces chronology
) -> list[Fold]:
    """Time-ordered expanding (default) or rolling folds. `embargo` drops samples between
    train-end and eval-start to prevent leakage. `order` sorts by a time key first."""

# crossval/executor.py
@dataclass(frozen=True)
class FoldResult:
    fold: int
    train_metrics: dict[str, float]   # from TrainResult.final_metrics
    eval_metrics:  dict[str, float]   # held-out score
    n_epochs: int

@dataclass(frozen=True)
class CrossValResult:
    task_type: TaskType
    folds: list[FoldResult]
    eval_aggregate: dict[str, float]  # per-metric mean across folds
    eval_std:       dict[str, float]  # per-metric std

def cross_validate(
    model_factory: Callable[[int], TrainableModel],
    X: np.ndarray, y: np.ndarray, folds: Sequence[Fold], *,
    aux: dict[str, np.ndarray] | None = None,                    # dt/target_dt/seq_lengths; sliced axis-0 per fold
    on_event: Callable[[int, TrainingEvent], None] | None = None, # (fold_idx, event)
    pass_eval_as_val: bool = False,                              # D-CV-9: default held-out; True doubles eval as X_val/y_val
    map_fn: Callable = map,                                       # D-CV-10 seam: serial map; inject a parallel map (WS-8)
) -> CrossValResult:
    ...
```

`aux` values are per-sample arrays (first axis = sample axis), sliced by the fold indices exactly like `X`/`y` — so the recurrence path passes `aux=SequenceData.fit_kwargs()` and it "just works" for the 3-D Δt case.

---

## 5. Packaging — model-core 0.2.0

- `pyproject.toml`: add `[project.optional-dependencies] crossval = ["numpy>=1.24"]`; bump version `0.1.0 → 0.2.0` (the `crossval` submodule is the headline; **`predict(**kw)` is bundled into 0.2.0 per D-CV-7** — the ABC + `ReferenceLinearModel.predict` + the 3-D stub are widened together).
- **Publish-first:** 0.2.0 must reach PyPI before any consumer pins `>=0.2.0`. Existing `>=0.1.0,<0.2.0` pins (juniper-ml `[tools]`, recurrence-model) keep resolving 0.1.x and are unaffected until a consumer opts into a `crossval` feature; the `test_model_core_drift.py` lint guards the pin/version relationship.
- CHANGELOG (model-core) `[0.2.0]` entry. **F-CRIT-1 (supersedes the earlier "separate follow-up" pin plan):**
  bumping `_version` → 0.2.0 reds required CI — `test_model_core_drift.py` reads `_version.py` dynamically and
  `test_pyproject_extras.py` hardcodes the pin string — unless the juniper-ml `[tools]` pin widens to
  `>=0.1.0,<0.3.0` **in the same PR** as the version bump. Safe pre-publish (still resolves 0.1.0 until 0.2.0 is
  on PyPI). Widen surgically (negative-control at `test_model_core_drift.py:190`); `[all]` needs no edit
  (recursive `juniper-ml[…,tools]` ref); leave the external recurrence-model `<0.2.0` pin alone (not lint-coupled).

---

## 6. Test matrix

| Test | Asserts |
|---|---|
| `regression_metrics` known-answer | mse/rmse/mae/r2 vs hand-computed on a tiny array; `loss==mse` |
| `walk_forward_folds` shape/order | expanding & rolling fold counts, monotonic train growth, no eval-before-train, `embargo` drops the right samples, `order` enforces chronology |
| leakage guard | every `eval_idx` is strictly *after* its `train_idx` under `order`; embargo gap respected |
| `cross_validate` dogfood | factory = model-core's `ReferenceLinearModel`; CV on a linear synthetic → high mean `r2`, sane per-fold + aggregate shapes |
| **2nd implementer** | factory = recurrence `LMURegressor` over a 3-D sequence fixture with `aux={dt,target_dt,seq_lengths}` → folds run, Δt path engaged (proves the layer is genuinely model-agnostic) |
| determinism | same factory/seed/folds → identical `CrossValResult` |
| aggregate correctness | `eval_aggregate`/`eval_std` == numpy mean/std of per-fold `eval_metrics` |
| event forwarding | `on_event(fold_idx, event)` fires per fold in legal order (`legal_event_order` per fold) |

The LMURegressor 2nd-implementer test lives in model-core's `[crossval,test]` env (it imports `juniper-recurrence-model`, a published dep) **or**, to avoid a model-core→recurrence dependency, a tiny in-repo 3-D `TrainableModel` stub. **Decision in PR:** prefer the stub (keeps model-core dependency-clean); recurrence's own suite adds the real LMURegressor-CV test on its side.

---

## 7. PR sequencing

1. **PR-1 (juniper-ml)** — `juniper_model_core/crossval/{__init__,metrics,splits,executor}.py` + `[crossval]` extra + 0.2.0 version bump + CHANGELOG + the full §6 test matrix (using the in-repo stub). Self-contained; no consumer changes.
2. **(later, gated)** model-core 0.2.0 publish (your pending-publisher already covers model-core) → then consumers opt in: recurrence app `/v1/crossval` endpoint + a recurrence-side LMURegressor-CV test; juniper-ml `[tools]` pin widen if/when needed.

**Standing rules:** no merge without your explicit per-PR signal + `gh pr view` MERGED; `gh pr list` + `gh run list --branch main` green before assuming a red PR is ours (heavy concurrent-session activity).

---

## 8. Out of scope (deferred / gated)

Parallel / distributed fold execution (OQ-11 / WS-8 worker) · canopy *direct* fold-aware control + per-fold aggregation UI (WS-5-adjacent; the audit landed #430) · server-side fold materialization in juniper-data (#168 scope C) · multi-ticker embargo-aware walk-forward (v1 targets time-ordered single-series/synthetic; equities multi-entity folds are a refinement using `ticker_code`) · classification held-out metrics (regression first) · a `score()` method on the `TrainableModel` contract.

---

## 9. Cross-references

- WS-4b deferral of the fold executor: [`JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md`](JUNIPER_RECURRENCE_WS4B_APP_BUILD_PLAN_2026-06-15.md).
- Model contract (D3 `**kw`, the lean-ABC philosophy, conformance kit): [`JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md`](JUNIPER_MODEL_CORE_INTERFACE_DESIGN_2026-06-14.md).
- Workstream/refactor context (WS-2/3/8, OQ-11): [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md).
- Implementation targets: `juniper-model-core/juniper_model_core/{interfaces,validation,conformance}.py`; the split semantics to mirror: `juniper-data/juniper_data/core/split.py`.
