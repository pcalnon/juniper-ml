# juniper-model-core — Interface Design & Scaffold (WS-3)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Application**: juniper-model-core (subdirectory of juniper-ml)
**Author**: Paul Calnon
**Status**: Design ratified (D1–D10), scaffold landed + published 0.1.0; **WS-0 ratified 2026-06-14**
**Version**: 0.1.0
**Date Created**: 2026-06-14
**Last Updated**: 2026-06-17

---

## 1. What this is

`juniper-model-core` is the shared **model-contract template** for the Juniper ML platform —
WS-3 of the model/middleware refactor (`notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`,
§2.3 / §3.3). It defines the minimal interface the Juniper service layer needs from *any*
learning model, plus a reusable conformance test kit that makes "any new model is pluggable"
verifiable rather than aspirational.

Per the ratified placement convention (`notes/JUNIPER_PACKAGE_PLACEMENT_AND_RELOCATION_PLAN_2026-06-09.md`,
D4), `-core` is reserved for genuinely-shared abstractions, which live as **juniper-ml
subdirectories** alongside `juniper-observability` / `juniper-ci-tools` / etc. The integration
mechanism is **subclass + inject**, not an entry-point registry.

This document is the canonical spec for the package. The model-side view of how the LMU plugs
in is `notes/JUNIPER_RECURRENCE_MODEL_DETAILED_DESIGN_2026-06-14.md` §6.3.

### Scope

**In (this workstream):** the model-contract surface — `TrainableModel` / `GrowableModel`
ABCs, the value types, the `TrainingEvent` vocabulary, `ModelSerializer`, the
`describe_topology()` schema, the validation free functions, and the conformance kit.

**Declared but deferred:** `TrainingLifecycleBase`. §2.3's diagram homes it in model-core, but
its body (threading, FSM, dataset management, worker coordination) couples to WS-2
(`juniper-service-core`) and OQ-11 (worker parallelism). WS-3 declares the *seam*; WS-2
designs the *body* (decision D8).

**Out:** the generic FastAPI service layer (WS-2), the recurrence model itself (WS-4), canopy
generalization (WS-5), the cascor refactor onto these packages (WS-6, trigger-conditioned).

---

## 2. Design anchors — two implementers (RK-4)

The brief's hard rule: drive the interface from **two** real implementers, never cascor
alone. The defining asymmetry:

| Need | cascor `CascadeCorrelationNetwork` | recurrence LMU (wraps `VariableStepLMUMemory`) |
|---|---|---|
| `task_type` | `classification` | `regression` |
| Data | 2-D `(n, F)`, torch.Tensor | 3-D `(n, T, F)` + `dt`/`readout_mask`, numpy |
| Topology | **grows** (`grow_network`/`add_unit`), freezes units | **fixed-order** (`d`, `θ` at construction) |
| Output | `predict` + `predict_classes` (argmax) | `predict` (continuous) |
| Metrics | accuracy, loss | mse/mae/r² |
| Serialize | HDF5 (`save_to_hdf5`) | hyperparams + eigendecomp + read-in/readout |
| Events | start/epoch_end/**cascade_add**/**candidate_progress**/end | start/epoch_end/end |
| ABC | `GrowableModel` | `TrainableModel` **only** |

**The load-bearing consequence:** `TrainableModel` has two real implementers and is frozen
now; `GrowableModel` has only one (cascor) until RCC lands in WS-4, so it is kept deliberately
minimal and provisional. This is the central RK-4 move.

---

## 3. Ratified decision ledger (D1–D10)

| # | Decision | Resolution |
|---|---|---|
| **D1** | ABC vs `Protocol` | **ABC** — reliable `isinstance` for the kit, fits subclass+inject, enforces methods at instantiation. |
| **D2** | Boundary array type | **numpy ndarray** — matches NPZ + data-client; models convert framework tensors internally. |
| **D3** | dt/readout_mask/seq_lengths threading | **documented `**kw`** on `fit`/`predict` — additive, 2-D-safe. |
| **D4** | Event emission | **injected `on_event` callback** — no monkey-patching. |
| **D5** | GrowableModel scope | freeze `TrainableModel` now; **`GrowableModel` minimal/provisional** until RCC (WS-4). |
| **D6** | Serializer shape | **standalone `ModelSerializer` strategy** in model-core; no `juniper-serialization` (RK-8). |
| **D7** | Conformance kit packaging (OQ-12) | **importable subclass-base + fixtures**, thin per-repo wrapper. |
| **D8** | `TrainingLifecycleBase` | **declare seam in WS-3, design body in WS-2.** |
| **D9** | `metrics()` statefulness | keep stateful `metrics()`; on-demand `evaluate(X, y)` deferred (not yet needed). |
| **D10** | `model_type` field type | **open `str`**, not a closed Literal. |

(Verbatim proposal + ratification in Appendix A.)

> Note on D9: the proposal floated adding an optional `evaluate(X, y)`. It is **not** in the
> 0.1.0 surface — no implementer needs it yet, and YAGNI beats a speculative method on the
> frozen `TrainableModel` ABC. It can be added additively later without breaking the contract.

---

## 4. Package layout (as built)

```text
juniper-ml/juniper-model-core/
├── pyproject.toml              # setuptools, dynamic version, py>=3.12, ruff @ 512, [conformance]/[test] extras
├── README.md  CHANGELOG.md  LICENSE
├── juniper_model_core/
│   ├── __init__.py             # numpy-free re-exports of the whole contract
│   ├── _version.py             # single source of truth (0.1.0)
│   ├── interfaces.py           # TrainableModel, GrowableModel (ABCs) + TaskType/TrainResult/GrowthOutcome
│   ├── events.py               # TrainingEvent, TrainingEventType, TRAINING_EVENT_TYPES
│   ├── serialization.py        # ModelSerializer (ABC)
│   ├── topology.py             # NodeKind, TopologyNode/Edge, Topology (TypedDicts)
│   ├── validation.py           # validate_metrics / validate_topology / legal_event_order (free fns)
│   ├── lifecycle.py            # TrainingLifecycleBase — SEAM ONLY (body → WS-2)
│   └── conformance/
│       ├── __init__.py
│       ├── fixtures.py         # ConformanceDataset + tiny_regression_2d / _3d
│       ├── reference.py        # ReferenceLinearModel / ReferenceGrowableModel + serializer (the RK-6 canary)
│       └── suite.py            # TrainableModelConformance / GrowableModelConformance
└── tests/                      # dogfood + free-fn + contract-type + dependency-free-import tests
```

**C1 (first-principles / no black-box base classes).** The ABCs are interface-only (all
`@abstractmethod`); every piece of shared *behavior* lives in `validation.py` as inspectable
free functions that implementers and the kit call explicitly. Nothing is inherited-and-magic.

**Dependency-free contract (key property).** `import juniper_model_core` pulls **no**
third-party runtime dependency: numpy is referenced only in type annotations (under
`TYPE_CHECKING`, with `from __future__ import annotations`). numpy/pytest live in the
`[conformance]` extra. A subprocess test (`test_dependency_free_import.py`) and the CI build
job's bare-wheel smoke test both enforce this. It is what lets the publish-verify run a clean
`--no-deps` import check with no `pypi.org` fallback (the target-squatting-safe verify policy).

---

## 5. The contract surface

### 5.1 `TrainableModel` (ABC)

```text
task_type: TaskType                         # "classification" | "regression"
random_seed: int | None
fit(X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult
predict(X) -> np.ndarray                     # continuous (reg) | logits/proba (clf); NEVER argmax
metrics() -> dict[str, float]                # keys valid for task_type; regression never reports accuracy
describe_topology() -> Topology
input_shape -> tuple[int, ...]               # per-sample: (F,) or (T, F)
output_shape -> tuple[int, ...]
```

`X` is `(n_samples, *input_shape)`. Sequence models read `dt` / `readout_mask` / `seq_lengths`
from `**kw`; tabular models ignore them (D3). `on_event` (D4) receives `TrainingEvent`s in a
legal order. `TrainResult` = `{final_metrics, n_epochs, history?, stopped_reason?}` (frozen).

### 5.2 `GrowableModel(TrainableModel)` — minimal & provisional

```text
n_units -> int
grow_step(**kw) -> GrowthOutcome             # add+freeze one unit; emit unit_added (within fit)
freeze() -> None                             # finalize topology; further grow_step is a no-op
```

`grow_step` deliberately does **not** take cascor's `residual` tensor — that would over-fit to
the one current implementer (RK-4). `GrowthOutcome` = `{added, n_units, unit_id?, score?}`.
The signature is re-evaluated against RCC in WS-4.

### 5.3 `TrainingEvent`

Closed vocabulary `TrainingEventType` = `training_start | training_end | epoch_end |
unit_added | phase_change`. `TrainingEvent` = `{type, payload, seq}` (frozen; `seq` is a
monotonic per-run counter for ordering assertions). Documented payloads: `epoch_end →
{epoch, metrics}`, `unit_added → {n_units, unit_id, score}`, `phase_change → {phase, detail}`.

### 5.4 `ModelSerializer` (ABC)

`save(model, path)` / `load(path) -> model`, a standalone strategy decoupled from the model
(D6). Round-trips must be **lossless** (predictions identical after reload — the kit asserts
`np.array_equal`). cascor's HDF5 and the LMU's hyperparam+eigendecomp serializers each become
one implementation. No `juniper-serialization` package until a third format exists (RK-8).

### 5.5 `describe_topology()` schema — the canopy seam

```python
Topology = {
  "model_type": str,                                   # OPEN str (D10), not a closed Literal
  "nodes": [{"id": str, "kind": NodeKind, "frozen": bool}],
  "edges": [{"src": str, "dst": str, "recurrent": bool}],
  "meta":  {"n_units": int, "task_type": TaskType, ...},  # extra keys allowed
}
# NodeKind = "input" | "hidden" | "output" | "memory" | "reservoir"   (∪ of cascor + recurrence)
```

`validate_topology()` checks: required keys; non-empty `model_type`; ≥1 node; unique non-empty
ids; legal kinds; every edge endpoint references an existing node; `meta.task_type` present.

### 5.6 Validation free functions (shared behavior, C1)

- `validate_metrics(task_type, metrics)` — the **RK-6 guard**: a regression model must report a
  canonical regression key and **no** classification-only key (e.g. `accuracy`).
- `validate_topology(topology)` — see §5.5.
- `legal_event_order(events)` — `training_start` first, `training_end` last (each once), all
  types known, `seq` non-decreasing.

Canonical key sets: `REGRESSION_METRIC_KEYS = {mse, rmse, mae, r2, loss}`;
`CLASSIFICATION_METRIC_KEYS = {accuracy, loss, cross_entropy, f1, precision, recall}`. Extra
keys are permitted (cost of model #20); the one hard rule is the regression/accuracy
exclusion.

---

## 6. The conformance kit (OQ-12)

Importable from `juniper_model_core.conformance` (D7 / OQ-12: "installable kit + thin per-repo
wrapper"). A consumer subclasses `TrainableModelConformance` / `GrowableModelConformance`,
supplies `make_model` / `make_dataset` / `make_serializer`, and pytest runs every contract
assertion:

- interface compliance (`isinstance`); `task_type` declared;
- `fit → predict → metrics` round-trip; `metrics()` keys consistent with `task_type`;
- `predict` per-sample shape == `output_shape`;
- **regression model carries no accuracy key** (RK-6, self-applied);
- `describe_topology()` renderable + `meta.task_type` matches;
- legal `TrainingEvent` order;
- lossless serialization round-trip (skipped if `make_serializer` returns `None`);
- (`GrowableModel`) `grow_step` increments `n_units`; `freeze` stops growth.

**RK-6 is built into the kit.** `conformance/reference.py` ships a stub **regression** model
(`ReferenceLinearModel`, closed-form least squares) plus a growable variant, and the kit
dogfoods them in model-core's own tests — so the kit cannot harbor an `argmax`/accuracy
assumption without its own CI failing.

**Honest scoping.** §3.3's "drive a regression model through every generic *service route*"
needs WS-2's routes. WS-3 ships **model-contract conformance** now; the **route-traversal**
layer activates with WS-2 and reuses this same reference model.

Tests: 66, **97% coverage** (gate 85%), all green on Python 3.13 locally; CI matrixes
3.12/3.13/3.14.

---

## 7. Two-implementer mapping (the RK-4 proof)

**LMU (`TrainableModel`):** `fit(X3d, y, dt=…, readout_mask=…)` trains the read-in/readout
around `VariableStepLMUMemory`; `predict` → continuous; `metrics` → {mse,mae,r2};
`describe_topology` → `model_type="lmu"`, `kind="memory"`, `recurrent=True`; emits
start/epoch_end/end; serializer persists `(d, θ, eigendecomp, readout)`.

**cascor (`GrowableModel`), via a thin WS-6 adapter — no core rewrite:**

| cascor today | generic contract |
|---|---|
| `fit(X2d, y, …)` | `fit` (2-D, ignores `dt`/`mask`) |
| `predict` / ~~`predict_classes`~~ | `predict` (argmax stays out of the contract) |
| `grow_network`/`add_unit` | `grow_step()` |
| `calculate_accuracy` | `metrics()["accuracy"]` |
| `save_to_hdf5` | `HDF5Serializer.save` |
| `cascade_add` event | `unit_added` |
| `candidate_progress` event | `phase_change{phase:"candidate_training"}` |
| `training_start/epoch_end/training_end` | 1:1 |

Both fit without bending the contract → the abstraction is real, not cascor-shaped.

---

## 8. Packaging, CI, and the publish-first extras deferral

- **CI lane:** `.github/workflows/ci-model-core.yml` (mirrors `ci-doc-tools.yml`) — pytest +
  coverage (85% gate) on 3.12/3.13/3.14, build + twine check + a **bare-wheel
  dependency-free import** smoke test.
- **Publish:** `.github/workflows/publish-model-core.yml` (mirrors `publish-cascor-core.yml`)
  — tag `juniper-model-core-v*` → TestPyPI (with a `--no-deps`, no-fallback verify) → PyPI,
  OIDC trusted publishing.
- **Autoload defense:** model-core's pytest config blocks the dash/playwright plugins
  (ecosystem SIGSEGV-on-3.14t defense).

**Publish-first extras deferral (deviation from the original step list, by design).** The
binding publish-first rule (§6.8 / §6.8 of the recurrence doc, and OQ-17) says no consumer
pins `juniper-model-core` until it is on PyPI (docker cannot build from sibling source). The
concrete precedent is `juniper-cascor-core`: scaffolded with its own publish workflow but
**absent from juniper-ml's `[all]`/`[tools]` extras and from `test_pyproject_extras.py`** until
published. This PR follows that precedent exactly:

- **NOT done here:** adding `juniper-model-core` to `[tools]`/`[all]`, editing
  `test_pyproject_extras.py`, or adding a drift-lint (a drift-lint has nothing to guard until
  there are pinned consumers).
- **Follow-up PR (post-TestPyPI soak):** wire the extra + update the extras lint + add the
  `test_model_core_drift.py` clone, all in one PR (RK-11 — never split shared-CI/extras edits).

---

## 9. Risk / constraint compliance

- **RK-4 (over-abstraction):** `TrainableModel` designed against 2 implementers and frozen;
  `GrowableModel` minimal/provisional (1 implementer) until RCC. `grow_step` carries no
  cascor-ism.
- **RK-6 (classification leak):** numpy boundary, no argmax/accuracy in the generic surface;
  `validate_metrics` enforces the regression/accuracy exclusion; the kit ships + dogfoods a
  regression model.
- **RK-8 (package proliferation):** serializer stays in model-core; no third package.
- **C1 (first-principles):** interface-only ABCs; behavior in inspectable free functions.
- **C-constraints:** Python ≥3.12; ruff line-length 512; pytest ≥80% (actual 97%).

---

## 10. Open follow-ups

1. **Post-publish wiring (RK-11):** `[tools]`/`[all]` + `test_pyproject_extras.py` +
   `test_model_core_drift.py`, in one PR after the TestPyPI soak (OQ-17).
2. **WS-2:** flesh out `TrainingLifecycleBase`; add the route-traversal conformance layer that
   drives the reference regression model through every generic service route.
3. **WS-4:** re-tighten the `GrowableModel` / `grow_step` surface against RCC (the second
   growable implementer); wire the LMU model to `TrainableModel` + run the kit.
4. **Verify the two new workflows** with `gh workflow run` immediately after merge (RK-10 —
   workflows can pass lint yet fail first run).
5. **WS-0** (overall design ratification) — **RATIFIED 2026-06-14 (Paul)**; WS-4 has since shipped, WS-6 stays trigger-gated.

---

## Appendix A — Verbatim design proposal & ratification (2026-06-14)

> Preserved per the design-conversation convention. The proposal below was presented for
> review; Paul ratified with: *"Decision ledger confirmed as written / continue with next
> steps as listed."*

### A.1 Proposal (as presented)

The proposal presented: scope (model-contract surface in; `TrainingLifecycleBase` body
deferred to WS-2); the two-implementer anchor table (§2 above); the package layout (§4); the
contract sketches for `TrainableModel`, `GrowableModel` (minimal/provisional), `TrainingEvent`,
`ModelSerializer`, and the `describe_topology()` schema (§5); the conformance-kit shape with
the RK-6 reference-model canary and the route-traversal scoping caveat (§6); the
two-implementer mapping with the cascor event table (§7); and the decision ledger D1–D10 (§3),
with the explicit recommendation to accept D1–D10 as listed and the note that D3 (`**kw`) was
the one genuinely-debatable point (a typed `Batch` container being the principled alternative
if type-level enforcement of the 3-D contract was wanted).

### A.2 Ratification

Paul: **"Decision ledger confirmed as written / continue with next steps as listed."** D3
(`**kw`) accepted as proposed. Next steps as listed: (1) bank this design doc; (2) create
`feature/juniper-model-core-ws3`; (3) scaffold the package + kit + dogfood tests (extras
wiring deferred per the publish-first rule, §8).
