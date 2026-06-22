# WS-6 A-phase Readiness — Design-Assumptions-vs-Reality Validation

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml (validation note; subject = juniper-cascor WS-6 **A-phase / 6a** adoption of `juniper-service-core` 0.2.0)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-22
**Status**: Validation findings (read-only, pre-development gate-check). **Verdict: A-phase is NOT ready to start — see §1.**

---

## 0. What this is & method

A pre-development reality-check of the **WS-6 A-phase (6a)** — turning cascor's `src/api/**` into thin
re-export shims / subclasses over the now-published `juniper-service-core` 0.2.0 — run before any A-phase
code, on the principle "validate reality against the design assumptions first."

**Design-of-record validated against:** `notes/JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md` (DR-1..DR-5,
§2.2 the A/B split) and `notes/JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md` (§5.6 the
per-module CLEAN / ADAPTER / CASCOR-BOUND extraction ledger), with the B-phase plan
`notes/JUNIPER_CASCOR_WS6_BPHASE_MODEL_CORE_ADOPTION_BUILD_PLAN_2026-06-19.md`.

**Method:** two independent read-only validators surveyed `origin/main` of juniper-cascor and juniper-ml
(local clones are known-stale) plus live PR/ruleset state and PyPI — one re-derived the §5.6 per-module
ledger against cascor's *current* (post-B-phase) `src/api/`, the other validated sequencing/gate/soak.
Every claim below is cited to `file:symbol` / PR# / release.

The trigger that unblocked this check: **`juniper-service-core` 0.2.0 is live on PyPI** (releases 0.1.0,
0.2.0; via ml #502, merged 2026-06-22) — the design's stated publish blocker is genuinely cleared.

---

## 1. Verdict

**A-phase is not ready to start.** The publish blocker is cleared, but **four of the six load-bearing
assumptions need correction**, the design's "thin re-export shim" premise breaks at the most important
module, and the B-phase that A-phase depends on is mid-flight and actively rewriting the exact surface
A-phase must inherit. This is a sequencing/scoping gate, not a defect — building now would collide with
in-flight work and materially underestimate the effort.

---

## 2. Assumption validation

| # | Assumption (as designed) | Reality (2026-06-22) | Verdict |
|---|---|---|---|
| **A1** | A-phase is a **thin re-export shim** repoint (lowest-coupling extraction) | True for the generic leaf modules; **breaks at `lifecycle/manager` + three routes** (§3) | ⚠️ PARTIAL |
| **A2** | Blocked until service-core T2 is **published + soaked** | Published ✓ (ml #502; GH Releases v0.1.0/v0.2.0 cut 2026-06-22 ~22:14Z). **No soak window/criteria is defined anywhere** for the A-phase; release is hours old. The only durational "soak" reference (OQ-17) is an *open question* about the cascor docker-lock pin, not the repoint trigger | ⚠️ NEEDS-UPDATE |
| **A3** | DR-1 ratified as **B→A** (proceed to A-phase after B) | DR-1 (ratified via ml #475) = *"do B now; **defer** the A-decision until OUT-11 published+soaked, then choose B→A vs park (S2)."* **Not a committed B→A.** The "OQ-B1 = proceed" note is a **different** decision — the *B-phase* on_event appetite, not DR-1 | ⚠️ NEEDS-UPDATE |
| **A4** | B-phase built cascor's `lifecycle/manager` against a `ServiceLifecycleManager` **subclass seam**, so A-phase is a thin repoint | "Seam-shaped, not seam-wired": #346 converged manager attr **names**, but **deliberately deferred** the seam fields the A-phase consumes (`_dataset_name` / `_last_result` / `_last_error` / `join`) to the A-phase itself; the plan states the manager is "not fully seam-aligned on monitoring" until the (unshipped) B3 `on_event` sink lands | ⚠️ NEEDS-UPDATE |
| **A5** | Gate: golden #340 + conformance #341 are required + green; an A-phase PR shifting event/metric semantics must pass | Both are **REQUIRED** on the active ruleset (`id 15081045`, `juniper-cascor-rules-1`) and **green** on `origin/main` | ✅ HOLDS |
| **A6 (RK-4)** | cascor A-phase is T2's **first** production consumer (recurrence wrote its own routes; canopy uses its own adapter) | Confirmed. Recurrence imports **T1 only** (`create_app`, middlewares, `SettingsBase`, `get_secret`, `TrainingLifecycle`) — none of the T2 surface; canopy A1 (#383) uses an in-canopy `RecurrenceServiceAdapter`; cascor production imports **zero** `juniper_service_core` | ✅ HOLDS |
| **Seq.** | Sequencing **B→A**: the B-phase (6b) is complete before the A-phase (6a) | **VIOLATED** — B-phase is mid-flight: B3 is a 3-PR split (B3.1 #352 merged, **B3.2 #353 open**, **B3.3 — the manager cutover — not yet created**), **B4 pending**. B3.3 rewrites the exact `lifecycle/manager` monitoring path the A-phase must inherit | ❌ VIOLATED |

---

## 3. Corrected §5.6 extraction ledger

The 2026-06-19 ledger was drawn against cascor's then-current `src/api/`; the B-phase (#345/#346/#347)
and in-flight B3 have reshaped that surface, and cascor's `src/api/` now structurally **mirrors**
service-core 0.2.0 — but mirroring is not adoption (cascor declares no `juniper-service-core` dependency
and contains zero `import juniper_service_core` in `src/api/`). Re-validated per module:

### Mechanical (HOLDS — structural twins of 0.2.0; repoint is genuinely thin)

- **Routes:** `training`, `metrics`, `dataset`, `network` (read routes), `snapshots`.
- **WebSocket:** `manager`, `training_stream`, `control_security`, `messages` (the shared 7 frames).
- **Workers (pool-infra):** `registry`, `audit`, `metrics`, `security`.

These are 1:1 surface matches with `juniper_service_core` 0.2.0 and would repoint to re-exports/subclasses
mechanically (cascor keeps its feature-specific extras as additive routes/frames).

### 🔴 BLOCKED — not thin, real work required

- **`lifecycle/manager`** (the headline). cascor's `TrainingLifecycleManager` (`src/api/lifecycle/manager.py`)
  is a **bare class** — it does not import or subclass service-core's `ServiceLifecycleManager`
  (`juniper_service_core/lifecycle/manager.py`). Concrete blockers to a thin subclass: a `ThreadPoolExecutor`
  + `_training_future` model (vs service-core's `_thread`); a **second `training_state` object**; progress via
  a **monkey-patch of `network.fit`** (vs service-core's `_handle_event`); **HDF5** snapshots (vs the injected
  `SnapshotStore`); a **torch-tensor** boundary (vs numpy); and divergent `start_training` / `get_status` /
  `load_snapshot` contracts (cascor `start_training(X=None, y=None, *, X_val, y_val, **kwargs) -> Dict`;
  service-core `start_training(X, y, X_val=None, y_val=None, *, dataset_name=None, **fit_kwargs) -> dict`).
  This is the deepest A-phase work and what the "thin shim" framing most underestimates.
- **Routes `admin`, `history`, `workers`.** The ledger marked these **CLEAN re-export**, but service-core 0.2.0
  ships **no counterpart** to re-export — each is cascor-feature-coupled (`admin` gates experimental
  functions incl. `swap_dataset_live`; `history` is live-dataset-swap history; `workers` are read-only fleet
  views over cascor's registry). They **stay cascor-only**.

### 🟡 NEEDS-WIRING — seams exist in 0.2.0 but cascor is not on them (mechanical, but not done)

- **`websocket/control_stream` → `CommandExecutor`.** service-core ships `CommandExecutor` /
  `LifecycleCommandExecutor` (`juniper_service_core/websocket/commands.py`) and `control_stream_handler`
  reads `app.state.command_executor`; cascor still hardcodes a module-level `_VALID_COMMANDS` + `_execute_command`.
- **`workers/coordinator` → `WorkerTaskProtocol`.** service-core's `WorkerCoordinator.__init__(…, protocol)`
  takes an injectable `WorkerTaskProtocol` (`build_assignment` / `parse_result`); cascor's `WorkerCoordinator`
  has no `protocol` param and inlines `BinaryFrame` + `WorkerProtocol`. cascor's `workers/protocol.py:WorkerProtocol`
  is a static-method class and does **not** satisfy the instance-shaped Protocol — a WS-6 adapter must wrap it
  (the design anticipates this; result reduction correctly stays consumer-side per OQ-11 / WS-8).
- **`lifecycle/monitor` on_event adapter** is unrealized. cascor's `on_event`/`TrainingEvent` flow currently
  lives only as a **coarse, granularity-discarding reconstruction** in `src/api/models/cascor_model.py:fit(on_event=…)`
  → `_emit_events` (its own docstring flags that the real migration is PR-B3); the manager/monitor remain the
  legacy callback-registry path. So adopting service-core's `LifecycleMonitor.on_event(TrainingEvent)` is
  gated on B3 completing.

### Already correctly cascor-bound (no change)

- `routes/decision_boundary` (intrinsic 2-D classifier viz); the cascade-bound worker task-envelope +
  correlation-based reduction (deferred to WS-8); `ws/worker_stream` (cascor's `/ws/v1/workers`, cascade
  binary frames).

---

## 4. Drift & incidental findings

- **Mirroring ≠ adoption.** B-phase #346/#347 renamed cascor's classes to *look like* the service-core seam
  and converged `start_training`'s shape, but cascor took **no `juniper-service-core` dependency** (pyproject
  pins only `juniper-model-core>=0.2.0,<0.4.0`) and subclasses nothing. The "convergence" is cosmetic
  alignment that eases — but does not constitute — the A-phase repoint.
- **`state_machine` "CLEAN" is a parallel clone, not a re-export.** cascor's `TrainingStateMachine` is
  contract-compatible on status/command but carries a closed cascade phase enum (`IDLE/OUTPUT/CANDIDATE/INFERENCE`)
  + candidate sub-state, so a literal re-export of service-core's open-string `LifecycleStateMachine` would lose
  cascor behavior — it is an ADAPTER, not CLEAN.
- **`routes/health` "CLEAN" is half-true.** service-core ships a 2-route health stub (top-level `health.py`);
  cascor's 3-route observability-grade probe (`/health/live` budgeted tick, rich readiness) exceeds it.
- **Two stale docstrings inside service-core 0.2.0 itself:** (1) `routes/snapshots.py` claimed replay was
  "deferred/cascor-bound" but `/replay` + `/replay/control` are implemented (step 1c) — **fixed** in juniper-ml
  PR #512; (2) `routes/models.py` is a request-models file under `routes/` (no `APIRouter`) — verified **not**
  a stale docstring (its docstring accurately says "Request models for the generic routes"); a naming/discoverability
  nuance only, **no change made**.

---

## 5. Recommended A-phase trigger condition

Open the A-phase repoint only when **all** hold:

1. **B-phase complete & lifecycle quiescent** — B3.2 (#353), B3.3 (manager cutover, to be created), and B4
   merged; no open WS-6-B PR touching `src/api/lifecycle/`.
2. **DR-1 explicitly resolved B→A** — currently *deferred/leaning*, owner-gated.
3. **A defined soak is satisfied** — resolve OQ-17 into a concrete bar. Suggested: service-core 0.2.0
   clean-install-from-PyPI verified + the meta-package "install lightest-extra-after-bare" extras-resolution
   check + ≥ 48–72 h since the 2026-06-22 release.
4. **The A-phase PR is green on both required gates** (golden #340, conformance #341), since it shifts
   event/metric semantics.

And re-scope the build from the corrected ledger (§3): plan `lifecycle/manager` as real
orchestrator-convergence work; keep `routes/{admin,history,workers}` cascor-only; wire the two seams
(`CommandExecutor`, `WorkerTaskProtocol`); gate the `lifecycle/monitor` adapter on B3.

---

## 6. Decisions for the owner

| ID | Decision | Note |
|----|----------|------|
| **DR-1** | Commit **B→A**, or **park after B** (S2)? | Park leaves T2 with zero production consumers (RK-4); B→A gives it cascor as a real consumer. Currently deferred. |
| **Soak** | Define the soak bar (resolve **OQ-17**). | Undefined today; the 0.2.0 release is hours old. |
| **Manager appetite** | Accept that `lifecycle/manager` is real convergence work, or keep cascor's manager subclassed-divergent indefinitely? | The single largest A-phase cost; the "thin shim" framing does not hold here. |

---

## 7. Provenance

- Validated against `origin/main` of juniper-cascor and juniper-ml (post-fetch, 2026-06-22) + live `gh`
  PR/ruleset state + PyPI. Local clones were stale (the recurring WS-6 footgun) and were not trusted.
- Subject surfaces: cascor `src/api/{lifecycle,routes,websocket,workers,models}/**`, `pyproject.toml`;
  service-core `juniper-service-core/juniper_service_core/{lifecycle,routes,websocket,workers}/**`.
- Evidence base: cascor #340/#341 (gate), #345/#346/#347 (B1/B2a/B2b), #352 (B3.1), #353 (B3.2, open);
  juniper-ml #473/#476/#478/#484/#492/#496 (T2 steps), #475 (DR ratification), #502 (0.2.0 publish);
  active ruleset 15081045; PyPI `juniper-service-core` releases 0.1.0/0.2.0.
- Two independent read-only validators (per-module ledger; sequencing/gate/soak); findings cross-checked
  against `notes/JUNIPER_DOCS_REALITY_AUDIT_2026-06-21.md`.
