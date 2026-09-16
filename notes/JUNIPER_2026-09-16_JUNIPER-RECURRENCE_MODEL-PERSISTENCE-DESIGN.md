# juniper-recurrence — Model Persistence: Design

- **Project**: Juniper — juniper-recurrence (with juniper-canopy, juniper-deploy)
- **Author**: Paul Calnon
- **Date**: 2026-09-16
- **Status**: Design for owner ruling — §4, §5 and §6 each need a decision before implementation
- **Closes**: Y2 of the canopy selection-reachability arc (`JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`, item 4 of the residue in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md`)

---

## 1. What this decides

Whether and how the juniper-recurrence service persists a trained LMU, so that canopy's snapshot
affordance stops reporting success over a model it never saved.

Three questions need an owner ruling — §4 (where the bytes live), §5 (retention), §6 (what a
restored model reports). §7–§8 are the mechanical consequence of those answers and need no ruling.

---

## 2. The defect, measured

canopy's snapshot workflow **reports success at both ends and never touches the model** under the
recurrence backend.

**Save.** `POST /api/snapshots` (`juniper-canopy/src/main.py`) routes to cascor's adapter only when
`backend.backend_type == "service"`. Every other backend takes an h5py fallback that writes:

- `created` / `description` / `mode` attrs;
- a `training_state` group of scalar fields off canopy's own `training_state` object;
- a `meta_params` group of **cascor-shaped** `nn_*` / `cn_*` parameters.

No model state of any kind. It then `stat()`s the file and returns success with a real byte size,
so the operator sees *"snapshot saved, 4.2 KB"*.

**Restore.** The mirror is worse than the handoff recorded. `POST /api/snapshots/{id}/restore` reads
that file back, calls `training_state.update_state(**restored_attrs)` — rewinding canopy's *display*
counters — re-applies `meta_params` via `backend.apply_params`, returns *"Restored from snapshot
X"*, and broadcasts `snapshot_restored` over the WebSocket.

So an operator gets a complete, plausible save→restore cycle. What actually moves is the UI's
epoch/loss counters and some hyperparameters. **The trained LMU is never written and never read.**

For a benchmarking platform this is the N5 class — *"silent misattribution is worse than a blocked
control"* — except it spans provenance rather than a label: a restored run is presented as the run
that was saved.

**There is nothing to serialise today.** `RecurrenceServiceAdapter` (`juniper-canopy/src/backend/
recurrence_service_adapter.py`) exposes only `train` and `training_status`. Upstream the service
offers `/v1/train`, `/v1/predict`, `/v1/model`, `/v1/crossval`, `/v1/crossval/status`,
`/v1/dataset`, `/v1/training/status` — and `/v1/model` returns **topology + metrics**
(`routers/model.py`), a description, not weights. The model lives in `AppState._model`
(`juniper_recurrence/state.py`) in process memory and dies with the process.

---

## 3. What already exists — and it is the expensive half

**The serializer is done, and it is lossless.** `LMUSerializer`
(`juniper-recurrence-model/juniper_recurrence_model/model.py:288`) is a versioned (`schema: 2`)
`.npz` + JSON serializer:

- `save(model, path)` (`:302`) refuses an unfitted model, captures the LMU envelope
  (`d` / `theta` / `ridge` / `time_unit` / `random_seed` / `task_type` / shapes / `n_features` /
  `uses_target_dt` / `metrics`) plus the readout's own fitted state via `readout.save_state()`,
  namespaced `readout__*`;
- `load(path)` (`:326`) reads with **`allow_pickle=False`** and reconstructs, with an explicit
  backward-compatibility branch for pre-DP-3 files (top-level `coef`, no `meta["readout"]`);
- the fixed memory eigendecomposition is **recomputed** from `d`/θ on load rather than stored, so a
  linear readout's reloaded predictions are bit-identical — the conformance kit's lossless
  round-trip assertion.

Every readout implements `save_state()` (`readouts.py:90`, `:200`, `:320`; `_readout_mlp.py:190`).

**Consequence for scope: this work is HTTP surface, not persistence.** No serialisation needs to be
designed, written or validated. That is what makes the feature tractable at all.

---

## 4. Question 1 — where do the bytes live? **(needs a ruling)**

**The recurrence service writes nothing to disk today.** `Settings`
(`juniper-recurrence/juniper_recurrence/settings.py:125`) has no directory field of any kind — the
whole config surface is identity/bind, logging, auth, rate-limit, the juniper-data client, LMU
defaults and metrics.

**And its container has no volume.** The `juniper-recurrence` service in
`juniper-deploy/docker-compose.yml` declares `ports`, `security_opt`, `cap_drop`, `environment` and
`secrets` — **no `volumes:` key at all**. A snapshot written inside that container is lost on
restart.

That last point is decisive: shipping endpoints without a volume rebuilds the same lie with extra
steps — the API would report a durable artifact that a `docker compose restart` silently destroys.

**Options**

| | Approach | Cost | Risk |
|---|---|---|---|
| **A** | `snapshots_dir` setting + a named volume in juniper-deploy | One setting, one compose stanza, one env var | Introduces the service's first persisted artifact class — backup posture, permissions, image `USER` all newly relevant |
| **B** | Return the `.npz` **in the HTTP response**; canopy stores it | No service-side storage, no volume, no retention question | Breaks the cascor precedent (server-side ownership); moves MBs through canopy; canopy then owns durability it has never owned |
| **C** | Persist into juniper-data as a dataset-adjacent artifact | Reuses an existing storage tier | juniper-data stores *datasets*; a model is not one, and the `dataset_id` hashing contract does not describe it |

**Recommendation: A.** It matches the cascor precedent exactly — cascor names and stores snapshots
server-side, and canopy shares no filesystem with it, which `main.py`'s own comment records as a
Wave-1 E2E finding (the local `snapshot_path` is a hint the adapter deliberately ignores). B is
cheaper today and puts durability in the component least able to provide it.

**A is not done until the volume exists.** The compose change is part of this work, not a follow-up.

---

## 5. Question 2 — retention **(needs a ruling, but the ecosystem has already answered once)**

`§6.4` of `JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md` was
**ratified 2026-08-23 (ml#1296) as no-deletion**: no file in the 27.9k cascor snapshot archive has a
deletion path, truncated writes are quarantined rather than deleted, and the ruling explicitly says
**do not build deletion tooling**.

**Options**

- **A — inherit no-deletion.** Consistent with the ratified policy; the operator prunes by hand.
- **B — a bounded cap** (keep N most recent). Diverges from a ratified ecosystem policy, and the
  divergence would be invisible to anyone reading only that design.

**Recommendation: A, inherit.** An LMU `.npz` is small (the envelope plus one readout's fitted
state — no per-epoch history, no candidate pool), so the pressure that would motivate a cap does not
exist here. If a cap is ever wanted it should amend §6.4 rather than fork it per-service.

**This is listed as a question only because inheriting is a choice.** Recording it as inherited is
what stops the next reader assuming recurrence has its own policy.

---

## 6. Question 3 — what does a restored model report? **(needs a ruling; partly self-answering)**

`AppState.set_trained` (`state.py:48`) takes `model`, `result: TrainResult`, `events: EventSink`
and `dataset: DatasetDescriptor`. **A restore has the model and none of the other three.** And
`status()` (`:69`) returns `("trained", ...)` iff `_model is not None`, so a restored model reports
`trained` regardless.

The trap: making the tuple well-formed by *synthesising* a `TrainResult` would fabricate metrics
for a run this process never performed — the exact defect class Y2 exists to close.

**Two facts make the honest answer cheap:**

1. `status()` already returns `TrainResult | None`, so `("trained", None, [])` is **representable
   today** — no type changes.
2. canopy already tolerates it. `RecurrenceBackend.get_status`
   (`juniper-canopy/src/backend/recurrence_backend.py:254`) guards with `elif result is not None:`,
   so a `None` result simply omits `current_epoch` and `completion_reason`. It does not raise, and
   it does not invent a value.

**Options**

- **A — "trained, no run result".** Add a `set_restored(model, source)` to `AppState` that sets
  `_model` and leaves `_result` / `_events` / `_dataset` as `None`, plus a provenance marker naming
  the snapshot id. `/v1/training/status` reports `trained` with `result: null`.
- **B — synthesise a `TrainResult`** from the metrics stored in the snapshot's `meta`. Makes the
  status shape uniform — and reports a training run that did not happen in this process, with
  epoch/timing fields that are either fabricated or zero.
- **C — a distinct `restored` status** alongside `idle` / `trained`. Most precise, but every
  consumer branching on the two-value status must learn a third.

**Recommendation: A.** It is the only option that adds no fiction, it needs no type change, and both
sides already handle `None`. The snapshot's `meta["metrics"]` are still available through
`GET /v1/model`, which reports `model.metrics()` — so the metrics are not lost, they are simply not
dressed up as a run.

**A carries one requirement**: the restore response and `/v1/training/status` must name the snapshot
id, so a restored model is distinguishable from a freshly-trained one. Without that, A trades a
fabricated result for an ambiguous one.

---

## 7. Proposed API surface (follows from §4A)

Mirroring cascor's shape (`juniper-cascor/src/api/routes/snapshots.py`), minus the cascade-specific
verbs (`retrain`, `resume`, `replay`) which have no LMU meaning:

| Method + path | Behaviour |
|---|---|
| `POST /v1/model/snapshots` | Serialise `state.model` via `LMUSerializer.save` into `snapshots_dir`. **409** when `state.model is None`, mirroring `/v1/model`'s existing refusal. Returns id, created, size, and the stored `meta`. |
| `GET /v1/model/snapshots` | List stored snapshots (id, created, size, `meta` summary). |
| `GET /v1/model/snapshots/{id}` | One snapshot's metadata. |
| `POST /v1/model/snapshots/{id}/restore` | `LMUSerializer.load` into `AppState` via `set_restored`. **404** unknown id. |

Notes that are consequences, not choices:

- `LMUSerializer.save` **raises on an unfitted model** (`model.py:305-306`), so the 409 must be checked
  before calling it rather than relying on the exception.
- `load` appends `.npz` when absent (`:327-329`); ids should be stored without the extension so the
  two halves agree.
- The id must be sanitised against traversal before joining it to `snapshots_dir` — canopy already
  has `_sanitize_snapshot_name` for its own path and the service needs its own equivalent.

---

## 8. canopy wiring (follows from §7)

1. `RecurrenceServiceAdapter` — `save_snapshot()` / `load_snapshot(id)` / `list_snapshots()`,
   alongside the existing `train` / `training_status`.
2. `RecurrenceBackend` — the `BackendProtocol` side. Note Y1's lesson
   (`juniper-canopy/src/backend/protocol.py`, canopy#633): if canopy's routes are to call snapshot
   methods on `backend` unconditionally, **declare them on `BackendProtocol`** rather than leaving a
   de-facto contract three of four backends happen to satisfy.
3. `main.py` — the save and restore gates both read `backend.backend_type == "service"` and must
   widen to a capability test. The h5py fallback stays for `DemoBackend`, whose model is synthetic
   and in-process; **that branch is shared, which is why "just make it refuse" was never a one-line
   fix.**

---

## 9. Explicitly out of scope

- **Changing demo-mode snapshot behaviour.** A metadata-only snapshot of a synthetic in-process
  model may well be intended. This design does not rule on it.
- **Cross-service snapshot portability.** A cascor `.h5` and an LMU `.npz` are different formats for
  different models; nothing here makes them interchangeable.
- **Retention tooling.** §5A inherits no-deletion, and the ratified policy says do not build it.
- **`retrain` / `resume` / `replay`.** cascor verbs with no LMU equivalent — a one-shot ridge solve
  has no partial state to resume from.

---

## 10. Owner rulings needed

| § | Question | Recommendation |
|---|---|---|
| **4** | Where do the bytes live? | **A** — `snapshots_dir` + a named volume in juniper-deploy, matching cascor's server-side ownership. Not done until the volume exists. |
| **5** | Retention? | **A** — inherit §6.4's ratified no-deletion; record it as inherited rather than assumed. |
| **6** | What does a restored model report? | **A** — `trained` with `result: null`, plus the snapshot id as provenance. Both sides already handle `None`; B fabricates a run. |

Implementation is two repos (juniper-recurrence, juniper-canopy) plus one compose stanza in
juniper-deploy, and is best split: the service half and its tests first, the canopy wiring second,
so the endpoints can be exercised before anything depends on them.
