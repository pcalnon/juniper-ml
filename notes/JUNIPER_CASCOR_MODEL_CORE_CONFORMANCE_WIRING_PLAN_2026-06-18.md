# juniper-cascor — model-core Conformance Wiring: Design / Build Plan (WS-6 Gate, half 2)

**Project**: Juniper ML Research Platform — cascor pre-refactor conformance baseline (roadmap **OUT-13**)
**Repository**: pcalnon/juniper-cascor (the wiring lands here); plan hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.1.0 (RATIFIED — §0 decisions D-C1…D-C5 confirmed by Paul + plan independently audited against reality, 2026-06-18)
**Last Updated**: 2026-06-18

---

> **What this is.** A build plan for wiring `juniper-cascor`'s `CascadeCorrelationNetwork` to the
> `juniper-model-core` **conformance kit** — **OUT-13** in
> [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md)
> and the **second half of the WS-6 trigger-gate** (the first half, the golden/snapshot suite
> OUT-12, shipped in juniper-cascor#340 and is a required check). Together they gate the WS-6
> cutover: cascor may refactor onto `juniper-service-core` / `juniper-model-core` only if both
> stay green.
>
> **The headline finding.** The model-core interface (`TrainableModel` / `GrowableModel`) was
> *designed with cascor as one of its two reference implementers* (`interfaces.py` docstring),
> but `CascadeCorrelationNetwork`'s **current** surface does not implement that contract. So
> OUT-13 is a **cascor→model-core adapter** + a conformance-test subclass — not a thin wrapper.
> The adapter is **test-only** (additive, no production change), exactly like OUT-12; WS-6's
> 6b phase later replaces it with native conformance.
>
> **Grounding.** Read live against juniper-model-core @ `juniper-model-core-v0.2.0` (conformance
> kit: `conformance/{suite,reference,fixtures}.py`, `interfaces.py`, `events.py`, `topology.py`,
> `validation.py`, `serialization.py`) and cascor @ `origin/main` (post-#340). Dup-guard
> 2026-06-18: no open cascor PR touches conformance/model-core.

---

## §0. Status & ratified decisions

> **RATIFIED 2026-06-18 (Paul).** D-C1…D-C5 confirmed as proposed, on the evidence of the
> independent audit recorded in §0.1 (all plan claims verified against cascor #340 + model-core 0.2.0).

- **D-C1 — Adapter is TEST-ONLY** (lives in cascor `src/tests/`, imports nothing into production).
  OUT-13 proves cascor *can* conform pre-refactor (insurance); WS-6-6b makes it native. **RATIFIED: test-only.**
- **D-C2 — Implement the full `GrowableModel`** (not `TrainableModel`-only). cascor is the kit's
  canonical growable classifier; the baseline should exercise both halves. **RATIFIED: full GrowableModel.**
- **D-C3 — `grow_step` is best-effort.** cascor grows *inside* `fit()`; it exposes no clean
  "add exactly one frozen unit" public API. The conformance suite tolerates this: its growth test
  is guarded by `if outcome.added:` (see §3.1). **Proposed:** ship `grow_step` returning
  `added=False` (a no-op that still satisfies the contract) + `freeze()` flag, and capture the
  REAL growth dynamics through OUT-12's trajectory golden instead. Option B (wire a genuine
  single-step growth by driving cascor's internal cascade machinery) is deferred to WS-6-6b where
  native growth is built. **RATIFIED: Option A (no-op grow_step now).** The audit confirmed it is
  contract-legal (`suite.py:133` `if outcome.added:` guard), that cascor exposes no public single-step
  grow API, and that OUT-12's trajectory golden already pins the real growth dynamics.
- **D-C4 — Skip the serialization conformance check** (`make_serializer = None`). The kit's
  `test_serialization_roundtrip_lossless` asserts **`np.array_equal` (bit-exact)**; cascor's HDF5
  round-trip is `torch.allclose(atol=1e-6)`-stable, not bit-exact (OUT-12 evidence). OUT-12's
  `test_golden_serialization_roundtrip` already covers serialization *at the correct tolerance*.
  **Proposed:** skip it here and cross-reference OUT-12. (Alternative, separate: relax the kit's
  check to `allclose` — a juniper-model-core change, out of scope for OUT-13.) **RATIFIED: skip here +
  cross-reference OUT-12; the kit's bit-exact default stands (it is correct for the LMU + reference model).**
- **D-C5 — CI lane.** Reuse the existing `golden` marker/`--golden` serial lane, **or** add a
  sibling `conformance` marker + lane. **Proposed:** a new `conformance` marker sharing the same
  serial/GIL/BLAS-pinned harness, so the two gate-halves report as distinct checks. **RATIFIED: new
  `conformance` marker, shared serial/BLAS harness, distinct check** (build-detail: lean a second job in
  the existing `golden-regression.yml`).

Everything else is mechanical (§7).

## §0.1 Audit record (2026-06-18)

The plan's claims were independently audited against ground truth before ratification —
juniper-model-core's conformance kit @ v0.2.0 (`conformance/suite.py`) and juniper-cascor @
`origin/main` (post-#340). **Every claim confirmed; no breaking discrepancies; the plan is buildable
as written.**

- **Kit side** (`suite.py`): the growth test's `if outcome.added:` guard (`suite.py:133`) makes a
  no-op `grow_step` contract-legal (D-C3); `test_serialization_roundtrip_lossless` asserts
  `np.array_equal` (bit-exact, `suite.py:119`) and `make_serializer=None` early-returns (D-C4); exactly
  13 contract methods (10 base + 3 growable); classification `{accuracy, loss}` ∈ `CLASSIFICATION_METRIC_KEYS`.
- **cascor side** (`cascade_correlation.py`): `fit(...) -> Dict[str, List]` returning `self.history`;
  `early_stopping=True` default; `history` carries `train_loss`/`train_accuracy` + `hidden_units_added`
  (with a `correlation` score, plus the `unit_index=-1` sentinel §3.3 already skips); `predict ->
  torch.Tensor`; `input_size`/`output_size`/`hidden_units`/`_completion_reason` all present; growth is
  internal to `fit()` (no public single-step grow API); cascor is not yet model-core-wired; OUT-12's
  golden suite + `two_spiral_seed42.npz` `(60,2)`/`(60,2)` one-hot shipped in #340.

**Build-thread notes (non-blocking):** (1) the adapter must use cascor's real
`fit(x_train, y_train, x_val, y_val, …)` param names, not the `x, y` shorthand in §2; (2) `add_unit()`
is internal machinery (it needs a `CandidateUnit`), not a single-step grow API — worth a one-line
adapter comment; (3) `grow_network()` returns `ValidateTrainingResults`, not a dict (moot for the
no-op `grow_step`).

## §1. The contract (model-core `GrowableModel`)

From `juniper_model_core.interfaces` (ABCs; numpy at the boundary; D1–D3):

| Member | Signature / type | Notes |
|--------|------------------|-------|
| `task_type` | `Literal["classification","regression"]` | cascor → `"classification"` |
| `random_seed` | `int \| None` | cascor → `42` |
| `fit(X, y, *, X_val, y_val, on_event, **kw)` | `-> TrainResult` | emit `TrainingEvent`s via `on_event` in legal order |
| `predict(X, **kw)` | `-> np.ndarray` | **class scores, never argmax** (RK-6) |
| `metrics()` | `-> dict[str,float]` | classification keys (`validate_metrics`) |
| `describe_topology()` | `-> Topology` | model-agnostic node/edge graph (`validate_topology`) |
| `input_shape` / `output_shape` | `-> tuple[int,...]` | per-sample, excl. batch axis |
| `n_units` | `-> int` | grown-unit count |
| `grow_step(**kw)` | `-> GrowthOutcome` | add ≤1 unit |
| `freeze()` | `-> None` | further `grow_step` is a no-op |

`TrainResult(final_metrics, n_epochs, history=None, stopped_reason=None)`;
`GrowthOutcome(added, n_units, unit_id=None, score=None)`;
`TrainingEvent(type, payload, seq)` with `type ∈ {training_start, training_end, epoch_end, unit_added, phase_change}`.

The conformance suite (`conformance/suite.py`) is a base class `GrowableModelConformance`; the
consumer subclasses it and supplies `make_model()` / `make_dataset()` / `make_serializer()`.
pytest then runs ~13 `test_*` contract methods against the adapter.

## §2. cascor today vs. the contract (the gap the adapter bridges)

| Contract | `CascadeCorrelationNetwork` today | Adapter strategy |
|----------|-----------------------------------|------------------|
| `fit(...) -> TrainResult` | `fit(x,y,x_val,y_val,...) -> history dict` | numpy→torch; call `net.fit(early_stopping=False)`; build `TrainResult(final_metrics=metrics(), n_epochs=len(history["train_loss"]), history=[...per-epoch...], stopped_reason=net._completion_reason)` |
| `predict(X) -> np.ndarray` | `predict(x) -> torch.Tensor` | numpy→torch→`net.predict`→`.detach().cpu().numpy()`; return raw scores |
| `task_type` | — | constant `"classification"` |
| `metrics()` | `history` only | `{"accuracy": history["train_accuracy"][-1], "loss": history["train_loss"][-1]}` (both ∈ CLASSIFICATION_METRIC_KEYS) |
| `input_shape`/`output_shape` | `net.input_size`/`net.output_size` | `(input_size,)` / `(output_size,)` |
| `describe_topology()` | `hidden_units` + output weights | build `Topology` (§3.2) |
| `n_units` | `len(net.hidden_units)` | direct |
| `grow_step`/`freeze` | growth is internal to `fit()` | §3.1 — best-effort + freeze flag (D-C3) |

## §3. The three non-trivial mappings

### §3.1 `grow_step` / `freeze` (D-C3)

cascor has no public "add one frozen unit" call. The suite's growth test is:
`before=n_units; outcome=grow_step(); if outcome.added: assert n_units==before+1`. So `added=False`
is contract-legal. **Plan:** `freeze()` sets `self._frozen=True`; `grow_step()` returns
`GrowthOutcome(added=False, n_units=self.n_units)` (always, in the no-op variant). The conformance
`test_freeze_stops_growth` passes (freeze → no-op); `test_grow_step_increments_n_units` passes
(guarded). cascor's *real* growth dynamics (3 units, correlations, shapes) are pinned by OUT-12's
trajectory golden — the conformance kit asserts the *interface*, OUT-12 asserts the *behavior*.

### §3.2 `describe_topology() -> Topology`

Build the model-agnostic graph (`validate_topology` rules: ≥1 node, unique non-empty ids,
`kind ∈ {input,hidden,output,...}`, edges reference existing nodes, `meta.task_type` present):

- nodes: one `input` node, one `hidden` node per `net.hidden_units` (`frozen=True`), one `output`.
- edges: input→output; input→each hidden; hidden→each later hidden (cascade); each hidden→output.
- meta: `{"task_type": "classification", "n_units": n, "n_in": input_size, "n_out": output_size}`.

### §3.3 `on_event` → `TrainingEvent` (legal order)

cascor's `fit()` has no event sink, so the adapter reconstructs events **post-hoc from `history`**
after `net.fit()` returns (the suite checks *order*, not timing): emit `training_start` (seq 0),
then one `unit_added` per real `hidden_units_added` entry (skip the sentinel; seq increments,
payload `{"n_units": k, "unit_id": f"h{k}", "score": correlation}`), then `training_end` (last
seq). `legal_event_order` ⇒ first=start, last=end, each once, seq non-decreasing. ✓

## §4. Dataset (classification)

The kit's fixtures are **regression-only** (RK-6 canary). cascor is classification, so the adapter
supplies its own `ConformanceDataset(X, y, X_val, y_val, task_type="classification")`. **Reuse
OUT-12's frozen `src/tests/fixtures/golden/two_spiral_seed42.npz`** (X `(60,2)`, y `(60,2)` one-hot)
split into train/val — one fixed dataset shared by both gate-halves. `fit_kwargs={}` (2-D model).

## §5. File layout, dependency, CI

```text
src/tests/conformance/                         # NEW
  __init__.py                                  # (namespace ok; mirrors existing test dirs)
  cascor_model_core_adapter.py                 # CascorModelCoreAdapter(GrowableModel) + dataset/serializer factories
  test_model_core_conformance.py               # class TestCascorConformance(GrowableModelConformance)
```

- **Dependency:** add `juniper-model-core[conformance]>=0.2.0,<0.3.0` to cascor's test/dev deps
  (pyproject `[project.optional-dependencies].test` or the dev group). It pulls numpy (already present).
- **Marker + lane (D-C5):** add a `conformance` marker; run serially on the GIL env, BLAS-pinned,
  `CASCOR_NUM_PROCESSES=1` — reuse OUT-12's `golden-regression.yml` harness shape (a sibling job or
  a second marker in the same workflow).

## §6. Determinism

Reuse the OUT-12 hardening verbatim (`CASCOR_NUM_PROCESSES=1`, single-thread BLAS,
`torch.set_num_threads(1)`, `seed=42`). The suite instantiates `make_model()`/`make_dataset()`
fresh per `test_*` (~13 trainings ≈ 15–20 s on the serial lane — acceptable; `slow`-tagged).

## §7. Implementation steps (for the build thread)

1. Add `juniper-model-core[conformance]` test dep + `conformance` marker (+ `--conformance` gate if
   matching the `--golden` isolation pattern).
2. Write `CascorModelCoreAdapter(GrowableModel)` — fit/predict/metrics/describe_topology/shapes/
   n_units + no-op grow_step/freeze (§2, §3).
3. Write the classification `ConformanceDataset` factory (reuse the frozen npz).
4. Write `TestCascorConformance(GrowableModelConformance)` (`make_serializer` returns `None`, D-C4).
5. Run serially on `JuniperCascor1`; iterate until all contract methods pass; 2–3 runs for stability.
6. `gh workflow run` the lane (lint-green ≠ run-green).
7. PR into juniper-cascor (`test(conformance): WS-6 model-core conformance baseline`), referencing
   this plan + OUT-13; note the OUT-12 cross-reference for serialization.

## §8. Risks & guardrails

| Risk | Guardrail |
|------|-----------|
| Adapter drifts from cascor's real API | Test-only; trains the real network; OUT-12 golden pins behavior |
| `predict` scores vs argmax (RK-6) | Return raw network output; never argmax (the contract forbids it) |
| Serialization bit-exactness fails the kit | Skip it (D-C4); OUT-12 covers round-trip at `atol=1e-6` |
| `grow_step` no-op under-claims growth | Documented (D-C3); behavior captured by OUT-12; revisit in WS-6-6b |
| Conformance kit version drift | Pin `>=0.2.0,<0.3.0`; a kit bump that adds checks is caught by this lane |
| WS-6 changes break conformance | Re-run after 6a/6b; any new failure blocks the cutover (kill-criterion) |

## §9. Provenance

Scoped from a live read of juniper-model-core's conformance kit (v0.2.0) and cascor `origin/main`
(post-#340), 2026-06-18. Pairs with the OUT-12 golden suite as the two halves of the WS-6 gate.
Implementation is a separate build phase (needs `JuniperCascor1` to run the suite).
