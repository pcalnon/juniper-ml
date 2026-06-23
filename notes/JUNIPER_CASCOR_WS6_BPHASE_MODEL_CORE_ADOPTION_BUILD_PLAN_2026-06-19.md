# juniper-cascor WS-6 B-phase — Native model-core Adoption: Design / Build Plan

**Project**: Juniper ML Research Platform — juniper-cascor model/middleware refactor (roadmap **WS-6**, B-phase / 6b)
**Repository**: pcalnon/juniper-cascor (the refactor lands here); plan hosted in pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT — fact-checked + completeness-critiqued; pending Paul ratification)
**Last Updated**: 2026-06-19

---

> **⟢ STATUS 2026-06-21 (post-execution).** B-phase PRs **B1 (cascor #345), B2a (#346), B2b (#347) are MERGED**
> to cascor `origin/main`; the WS-6 gate (golden #340 + conformance #341) stays green. **B3** (the `on_event`
> sink, §5) is **NOT STARTED but spike-validated** — OQ-B1 is decided: proceed with the full migration
> (`on_event` for the coarse projection via CCN's native `on_epoch_callback`/`on_grow_iteration_callback`
> hooks + a *retained* drain→broadcast side-channel for the 50 Hz `/ws/training` per-candidate stream).
> **B4** follows. The **A-phase (6a)** stays blocked on the OUT-11 `juniper-service-core` 0.2.0 publish
> (ml #502). Full reconciliation: `JUNIPER_DOCS_REALITY_AUDIT_2026-06-21.md`.
>
> **⟢ UPDATE 2026-06-23.** **B3 is now fully MERGED** — B3.1 (#352) + B3.2 (#353) + B3.3 (#355, the
> manager monitoring cutover; the fit/grow monkey-patches are gone). The §0/§5 "B3 NOT STARTED" framing
> above is superseded; of the B-phase only **B4** (point native conformance at production `CascorModel`;
> retire the test-only `CascorModelCoreAdapter`) remains, and it has no PR/branch yet. **`juniper-service-core`
> 0.2.0 is LIVE on PyPI** (#502 merged), clearing the A-phase publish-blocker — the A-phase remains gated
> on B4 + the three owner decisions (DR-1 / soak-OQ-17 / manager-appetite); see
> `JUNIPER_WS6_APHASE_READINESS_VALIDATION_2026-06-22.md`.

> **What this is.** A build plan for the **B-phase** of the juniper-cascor refactor (WS-6, sub-phase
> 6b): make the production cascor service operate against the abstract `juniper_model_core`
> `TrainableModel` / `GrowableModel` interfaces, replacing the *test-only* `CascorModelCoreAdapter`
> with native production conformance. This is the **dependency-clear** cutover step ratified as
> **DR-1 (do B now; defer the A-phase decision)** in
> [`JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md`](JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md) §2
> (juniper-ml #475, merged).
>
> **The headline decision.** cascor adopts the interface through a **thin production wrapper**
> `CascorModel(GrowableModel)` — *not* by making `CascadeCorrelationNetwork` (CCN) implement the
> interface directly. The wrapper leaves CCN's numerics byte-identical (the golden gate's hard
> constraint) and keeps the change inside cascor-the-service (CCN's separate `juniper-cascor-model`
> package is untouched). It is the production *adaptation* of the proven test-only adapter shipped in
> cascor #341 — but **not a naïve copy** of it (see §4.2).
>
> **Grounding.** Built from four independent read-only reality audits (2026-06-19) against
> juniper-cascor `origin/main` (post-#342, gate armed), juniper-model-core (installed 0.2.0 / repo
> 0.3.0), and juniper-service-core (`ServiceLifecycleManager`, merged-unpublished), then fact-checked
> against ground truth and completeness-critiqued (§0.1). Pairs with the OUT-12 golden suite (#340)
> and OUT-13 conformance baseline (#341) as the two halves of the WS-6 gate, both **required** status
> checks on ruleset `juniper-cascor-rules-1` (id 15081045).

---

## §0. Status, scope, and the gate

- **Gate: ARMED + ENFORCED.** `Golden / Snapshot Regression` (#340) and `model-core Conformance`
  (#341) are required checks. A B-phase PR that shifts training trajectories, event order, or metric
  semantics is **blocked, not merely flagged**. Both must stay green on every PR.
- **Kill-criterion (refactor plan §2.7):** if conformance cannot be made/kept green without an
  observable-behavior change, WS-6 is abandoned (cascor keeps its own stack). It has **not** fired
  (#341 is green). The B-phase's riskiest PR (the `on_event` migration, §5 PR-B3) is the live test of
  this criterion — and that test is **WebSocket-inclusive**, not REST-only (§3.3, H4).
- **In scope (6b):** cascor's lifecycle/routes operate against the model-core interfaces; native
  production conformance replaces the test-only adapter; the lifecycle manager is shaped against the
  future `ServiceLifecycleManager` subclass seam so the A-phase is a thin repoint.
- **Out of scope (6a / A-phase — separate, deferred per DR-1):** turning cascor's `src/api/**` into
  re-export shims over `juniper_service_core`. Blocked on OUT-11 being **published + soaked**. The
  B-phase aligns to the seam's *shape* only (source-level), importing nothing from service-core.
- **Owner boundaries (DO-NOT-TOUCH):** WS-5 (canopy) and OUT-11 (service-core T2) are owned by
  concurrent sessions. This plan reads service-core for seam shape but changes nothing there.

### §0.1 Validation record (2026-06-19)

This plan was fact-checked against ground truth and completeness-critiqued by two independent
read-only sub-agents before ratification. **All load-bearing claims confirmed**, with corrections
folded in:

- **Confirmed:** golden computes trajectory/predict goldens by calling CCN `fit` directly; CCN is not
  an `nn.Module` and has no `state_dict` (the `:2516`/`:2909` refs are dead code); the
  `ServiceLifecycleManager` seam (`self.model` + `attach_model()`, no `_create_model()` hook, `run` →
  `self.model.fit(on_event=...)`); the version/publish state; the ruleset enforcement; the pytest gate
  flags.
- **Corrected paths/lines:** golden harness is `src/tests/golden_support.py` (not under `integration/`);
  `_install_monitoring_hooks` body ends ~`:1876`; the CCN construction assignment is at `:1421`.
- **Material gaps found + addressed (this revision):** the `self.network` bridge must handle **four
  assignment sites** including an unwrapped HDF5-load (§4.3, H1); PR-B2 renames break the required
  **Unit Tests** lane and must update call sites same-PR (§5, H2); a new runtime dep trips **Lockfile
  Freshness** and needs a same-PR `requirements.lock` regen (§5 PR-B1, H3); the `on_event` migration
  risks the **`/ws/training` per-candidate stream** canopy renders, which the REST golden does not
  cover (§3.3 + §5 PR-B3, H4); the wrapper must **not** re-seed/re-construct the way the test adapter
  does inside `fit` (§4.2, M1); the decision-boundary stays on `forward`, not interface `predict`
  (§4.3, M3).

---

## §1. TL;DR — the decision and the staged path

**Decision: a production `CascorModel(GrowableModel)` wrapper, not CCN-direct.** Four grounded reasons:

1. **Golden safety (decisive).** The golden suite computes its trajectory and predict goldens by
   calling `CascadeCorrelationNetwork(**GOLDEN_NET_CONFIG).fit(...)` **directly**, not through the
   manager (`src/tests/golden_support.py:194-200`). Making CCN implement `GrowableModel` would change
   `fit`'s signature/RNG draw order — the exact path the golden exercises — risking every float series
   (tolerance is only `rtol=1e-3` / predict round-trip `atol=1e-6`). A wrapper leaves CCN **100%
   untouched** → the trajectory and predict goldens are structurally safe.
2. **Dependency-clear.** CCN lives in the *separate* `juniper-cascor-model` PyPI package. CCN-direct
   would add a `juniper-model-core` dependency to that package and force a republish. The wrapper adds
   `juniper-model-core` (already published) as a **cascor-service runtime** dependency and touches only
   the cascor repo — exactly the "needs no other package" property DR-1 requires.
3. **Proven mapping.** The test-only `CascorModelCoreAdapter` (cascor #341) demonstrates the full
   interface mapping works (fit / predict / metrics / topology / events / no-op grow). The B-phase
   *adapts* that mapping to production — re-using the translation logic, but with a different
   construction/seed/execution contract (§4.2).
4. **Seam-matched.** `ServiceLifecycleManager` holds `self.model: TrainableModel`, **injected** via
   `attach_model()`. A `CascorModel(GrowableModel)` is exactly the object that gets attached — the
   B-phase and the future A-phase want the same wrapper.

**Staged PRs (ordered by risk; each keeps the gate green):**

| PR | Title | Behavior change? | Gate exposure |
| --- | --- | --- | --- |
| **B1** | Production `CascorModel` + manager holds `self.model` (4 assignment sites + lockfile regen) | None (CCN + projections untouched) | Trivially green; **Lockfile Freshness + Unit Tests in scope** |
| **B2a** | Seam-align attribute & method **names**; update unit-test call sites | None (renames) | Green; **Unit Tests lane is load-bearing** |
| **B2b** | Converge method **signatures/returns** (snapshot bool→dict; `start_training` params) | None (snapshot routes not golden-pinned) | Green |
| **B3** | Replace monkey-patch monitoring with the `on_event` `TrainingEvent` sink | **Mechanism only** — REST projection *and* WS granularity must hold | **Kill-criterion test (REST golden + WS assertion)** |
| **B4** | Point native conformance at `CascorModel`; retire the test-only adapter | None (test wiring) | Conformance green against production code |
| **B5** | (Optional) read-route projection delegation cleanups | None | Only if provably projection-identical |

B1–B2b are mechanical and low-risk (but each touches a required CI lane — §7/§8). **B3 is the crux** —
isolated, spike-gated, and the live kill-criterion test. B4 completes "native conformance." B5 is
opportunistic.

---

## §2. Reality-audit synthesis — the coupling surface

### §2.1 The manager is the whole story; routes are a thin shim

- The sole production coupling to CCN is `TrainingLifecycleManager` (`src/api/lifecycle/manager.py`,
  ~4339 lines, class at `:1069`, no base class). It holds the CCN at `self.network` and constructs it
  in `create_network` (assignment at `:1421`, within `:1407-1430`) via
  `CascadeCorrelationConfig.create_simple_config(**kwargs)` → `CascadeCorrelationNetwork(config=...)`.
- The route layer is an almost perfectly thin shim over `lifecycle.<method>()`. The **only** direct
  `.network` reach is `src/api/routes/snapshots.py:66` (`getattr(lifecycle, "network", None)` inside
  `_compute_snapshot_window`) — and it has a graceful `None` fallback, so it *survives* a getter that
  returns `self.model.network`; it is a cleanliness re-point, **not** a hard break. (The genuine hard
  work is the four `self.network =` assignments inside the manager — §4.3.)
- **Fully model-agnostic, zero changes:** `routes/{admin,dataset,workers}.py`,
  `lifecycle/state_machine.py`, `lifecycle/monitor.py`, `workers/coordinator.py` (its only
  `CascadeCorrelationNetwork` mention, `:357`, is a doc comment).

### §2.2 The coupling is overwhelmingly cascor-specific

Of ~50 distinct touchpoints to the CCN instance, only ~9 *kinds* map to the 13-member interface; ~40+
are cascor-specific. The split:

- **Interface-mappable (the training-loop kernel):** `fit` (production call at `manager.py:2172`);
  `n_units` (= `len(self.network.hidden_units)`); `input_shape`/`output_shape` (=
  `self.network.input_size`/`output_size`); `predict` (exercised by conformance — the manager's own
  inference site, the decision boundary, stays on `forward`, §4.3/M3).
- **Irreducibly cascor-specific (stay behind the concrete model / override points):** HDF5 snapshot
  save/load/replay (external `CascadeHDF5Serializer`); live dataset swap with monotonic network resize
  (`_resize_network_for_dataset`, `active_output_dim` masking); manual weight/unit surgery
  (`patch_weights`, `add_hidden_unit_manual`, `remove_hidden_unit_manual` — INVESTIGATING-mode only);
  the ~25-field hyperparameter surface (`get_training_params`/`update_params`); the `network.history`
  dict (metrics curves, `dataset_swaps`, `_completion_reason`); the `weight_history` replay
  side-channel; topology weight tensors (`output_weights`/`output_bias`/`hidden_units` dicts); the
  worker/candidate machinery (`set_worker_coordinator`, `_persistent_progress_queue`,
  `_grow_iteration_callback`, the drain→broadcast path).

### §2.3 Three facts that shape the design

1. **Monkey-patching is the deepest seam.** Monitoring works by reassigning `self.network.fit`,
   `grow_network`, and `validate_training` on the instance and injecting private callbacks
   (`manager.py:1504-1876`). model-core's contract (D4) forbids this; `fit(on_event=...)` is its
   intended replacement. This is PR-B3 — and the monkey-patch also drives the **per-candidate WS
   stream** (§3.3, H4), which the coarse event vocabulary does not capture.
2. **CCN is not `nn.Module`; it has no `state_dict`.** The `state_dict`/`load_state_dict` references at
   `manager.py:2516`/`:2909` are **dead defensive code** (always `None`/no-op). Serialization is HDF5
   via an external serializer; live-swap rollback clones raw tensors. This is why D-C4 (skip the
   bit-exact serialization conformance check) is correct and stays.
3. **Real growth is `fit`-internal only** (D-C3 confirmed). The lone single-step grow
   (`_install_hidden_unit` + `_resize_output_layer_for_new_units`, `:3681`/`:3696`) is the
   INVESTIGATING-mode manual editor, not a training mechanism. So `CascorModel.grow_step` stays a
   contract-legal no-op, exactly as the test adapter ships it.

---

## §3. The behavior-preservation contract (what the gate actually pins)

This is the hard constraint envelope. The refactor is **accepted only if it stays inside it.**

### §3.1 Golden suite pins two things

1. **CCN numerical behavior** — the trajectory golden (`src/tests/integration/test_golden_trajectory.py`)
   freezes the `network.history` series (`train_loss`/`value_loss`/`train_accuracy`/`value_accuracy`,
   4 rows), per-unit `correlation`/`weight_shape`/`unit_index`, `growth_count=3`,
   `completion_reason="max_iterations"`; the predict golden
   (`test_golden_serialization_roundtrip.py`) freezes `predict` output (60×2) at `rtol=1e-3`/`atol=1e-4`
   and the HDF5 round-trip at `atol=1e-6`. **All computed by calling CCN directly** (`golden_support.py`).
   → *Do not touch CCN's numerics, RNG order, or `fit` signature.*
2. **The route projection** — the API-snapshot goldens (`api/test_golden_api_snapshots.py`) freeze the
   **exact key-sets and scalar values** of `/v1/network`, `/v1/network/topology`, `/v1/network/stats`,
   `/v1/metrics` (post-train) and `/v1/health`, `/v1/training/status`, `/v1/metrics/history`,
   `/v1/metrics/transport`, `/v1/history/dataset_swaps` (fresh). Volatile keys (timestamps, ids,
   `*_total`, durations) are scrubbed; everything else — `epoch:3`, `hidden_units:2`,
   `current_phase:"output"`, `activation:"Tanh"`, the dict key-sets — is **exact-compared, not
   float-tolerant**. → *Keep the read-route serializers emitting identical key-sets/strings/counts.*

### §3.2 Conformance pins the interface only

The `GrowableModelConformance` subclass asserts shapes / keys / event-order / counts — **never float
values** (`conformance.yml` header: "carries no cross-build tolerance risk"). `predict`-never-argmax
(RK-6) is honored by returning raw scores. `grow_step` no-op is guarded (`suite.py:133`
`if outcome.added:`); serialization is skipped (`make_serializer=None`, D-C4). → *Robustly safe; the
production `CascorModel` satisfies it as easily as the test adapter does.*

### §3.3 The fragile surfaces (and the escape hatch)

- **Fragile #1 — CCN numerical determinism.** Any change to RNG draws, weight init, iteration order, or
  the candidate path moves every float series. Mitigation: the wrapper never reaches into CCN's
  training math; CCN stays frozen; the wrapper does **not** re-seed (§4.2/M1).
- **Fragile #2 — the exact REST projection.** Renaming/adding/dropping a key or changing a phase string
  in `/v1/network*`, `/v1/training/status`, `/v1/metrics` fails the exact-compare. Mitigation: read
  routes keep their **legacy projection**; do **not** swap them to model-core's native
  `describe_topology()` (`nodes/edges/meta`) shape.
- **Fragile #3 — the `/ws/training` per-candidate stream (NOT golden-covered; H4).** The monkey-patch
  emits fine-grained `candidate_progress` / `grow_iteration` / `all_correlations` frames (drain thread
  `_drain_progress_queue:1734`, `_grow_iteration_callback:1778`, broadcast at `:1344`). model-core's
  `TrainingEvent` vocabulary is **five coarse types** (`training_start`/`training_end`/`epoch_end`/
  `unit_added`/`phase_change`, `events.py:18-33`) and its docstring prescribes collapsing
  `candidate_progress → phase_change`, **discarding** the fine signal. canopy renders this at 50Hz
  (`ws_dash_bridge.js:10`, `dashboard_manager.py:1705`, locked by `test_phase_b_bridge.py:246`). **No
  golden captures the WS stream**, so an `on_event`-only PR-B3 can stay green while silently degrading
  the live dashboard. → *PR-B3 must preserve per-candidate WS granularity (retain a side-channel or
  extend events), and assert it (§5 PR-B3).*
- **Escape hatch (for B3):** the *golden* pins what the user observes via the **read routes**, not how
  it is wired — no golden captures the event stream or callback order. So replacing the monkey-patch
  mechanism is **golden-legal as long as the new sink writes the same REST projection** — but it is
  **not behavior-preserving** unless the WS granularity (Fragile #3) is also held. A genuine projection
  change requires golden re-capture + Paul's reviewed sign-off, and counts against the kill-criterion.

---

## §4. Target design — `CascorModel(GrowableModel)`

### §4.1 The wrapper

- **New production module** under cascor `src/` (proposed `src/api/model/cascor_model.py`; final
  location an implementation detail, OQ-B3). It re-uses the translation logic of
  `src/tests/conformance/cascor_model_core_adapter.py` and is importable by the lifecycle manager and
  reused by the conformance test (PR-B4).
- **Class `CascorModel(GrowableModel)`** wraps a `CascadeCorrelationNetwork`:
  - Implements the 13 interface members: numpy↔torch translation; `fit(X, y, *, X_val, y_val,
    on_event, **kw)`; `predict` returning raw scores as `np.ndarray` (RK-6, numpy-at-boundary D2);
    `metrics()` → `{accuracy, loss}`; `describe_topology()` → the model-agnostic graph; `n_units`,
    `input_shape`/`output_shape`; no-op `grow_step` (D-C3); `freeze()`.
  - **Accepts a pre-built CCN** (`CascorModel(network=<ccn>)`) and **exposes it as a public `.network`
    property** so cascor-specific manager code reaches `self.model.network.<attr>`. (The test adapter,
    by contrast, *owns* `self._net` and has no `.network` — that difference is load-bearing, §4.2.)

### §4.2 ⚠️ Construction/seed/execution parity — the crux of B1 (M1)

The test adapter is **not** a drop-in production model. Its `fit` **constructs a fresh CCN and re-seeds
inside `fit`** (`cascor_model_core_adapter.py:63-65`). The manager's path is fundamentally different
and must be preserved exactly:

- The CCN is built **once** in `create_network` (`:1421`), long before training.
- Hyperparameters are applied via the manager's `_apply_params_unlocked(network_kwargs)` split
  (`:2154`) — **before** `fit`, as attributes — not passed into `fit`.
- Training runs inside a **`ThreadPoolExecutor` future** (`_run_training:2165` → `self.network.fit(x, y,
  x_val=, y_val=, **kwargs)` at `:2172`), under the **monkey-patched** `fit` (until B3).
- The manager does **not** re-seed inside `fit`.

**Therefore `CascorModel.fit` MUST:** wrap the *existing* CCN (never re-construct); **never re-seed**;
not duplicate the `_apply_params_unlocked` split (the manager still applies params before calling
`fit`); and run the wrapped `net.fit` with the same args the manager passes today. Naïvely promoting
the adapter (rebuild + re-seed) would double-construct/double-seed → **trajectory golden break**. The
parity check is: golden trajectory + predict re-run byte-identical after B1.

### §4.3 The manager holds the interface — the four assignment sites (H1)

`self.network` becomes a **read/write property** over `self.model` (or the four sites are rewritten
directly). A getter-only property is insufficient because the manager **assigns** `self.network` in
four places, each of which must operate on `self.model`:

| Site | `manager.py` | Action under B1 |
| --- | --- | --- |
| `__init__` | `:1080` (`= None`) | `self.model = None` |
| `create_network` | `:1421` (`= CCN(config=...)`) | build CCN, then `self.model = CascorModel(network=ccn)` (the `attach_model` seam, §6) |
| `delete_network` | `:1452` (`= None`) | `self.model = None` |
| `_load_snapshot_to_network` | `:3941` (`= <bare CCN from HDF5>`) | **re-wrap**: `self.model = CascorModel(network=<loaded ccn>)` — the HDF5 path yields an *unwrapped* CCN; a getter-only property would leave `self.model` stale |

Recommended shape: keep `self.network` as a property with **both** getter (`return self.model.network`)
and setter (`self.model = CascorModel(network=value)` when handed a bare CCN), so the four sites and the
`snapshots.py:66` reader all resolve consistently. **Write-through mutations survive untouched** —
`self.network.<attr> = x` (live-swap rollback `:2870-2905`), monkey-patch method reassignment
(`:1515`/`:1691`/`:1875`), and helper-class construction (`_WeightHistoryRecorder(self.network, ...)`)
all go *through* the reference and need no change in B1/B2 (the monkey-patch is removed only at B3). Do
not "fix" these.

**Decision boundary stays on `forward` (M3).** The manager's inference site
(`get_decision_boundary:3834`) does `predictions = self.network.forward(grid); predictions.argmax(dim=1)`.
Keep it on `self.model.network.forward(...)` (a cascor-specific torch path) — do **not** route it
through interface `predict`, which returns `np.ndarray` (D2) and would break the immediate
`.argmax(dim=1)`. The interface `predict` is exercised by conformance instead.

### §4.4 What stays cascor-specific

Everything in §2.2's cascor-specific list stays, reached via `self.model.network` (or kept as manager
methods). In the A-phase these become the cascor subclass body over `ServiceLifecycleManager`; in the
B-phase they are grouped under an explicit "cascor-specific overrides/extensions" banner so the A-phase
boundary is unambiguous.

---

## §5. The staged PR breakdown

Each PR states its behavior-preservation argument, its **full** required-lane checklist (§8), and a
one-line rollback. Run the relevant lanes on `JuniperCascor1` before pushing each.

### PR-B1 — Production `CascorModel` + manager holds `self.model` (+ lockfile regen)

- **Do:** add the production module (re-using the adapter's translation logic, honoring §4.2 parity);
  add `juniper-model-core` as a cascor **runtime** dependency; **regenerate `requirements.lock` in the
  same PR** (H3 — the Lockfile Freshness gate recompiles with `--extra ml --extra api --extra
  observability --extra juniper-data`, so a new runtime pin must land in the lock or the gate fails);
  rewrite the **four `self.network =` assignment sites** to operate on `self.model` (§4.3, including the
  HDF5 re-wrap); add the `self.network` get/set property; re-point `routes/snapshots.py:66` at a manager
  accessor for cleanliness; add `CascorModel` unit tests (property get/set, the four assignment paths,
  `predict` return-type, fit-no-reseed parity).
- **Behavior-preserving because:** CCN is constructed/seeded/trained identically (§4.2); all read-route
  projections untouched; monkey-patch monitoring and the WS stream are unchanged; decision boundary
  stays on `forward`.
- **Lanes:** golden + conformance (zero fixture change), **Lockfile Freshness**, **Unit Tests** (×3 +
  macOS), pre-commit (mypy/flake8/black/isort), Quality Gate.
- **Rollback:** revert the PR — additive module + four localized rewrites + lock diff; no fixture or
  behavior change to unwind.

### PR-B2a — Seam-align attribute & method **names** (+ unit-test call sites)

- **Do (public renames):** `self.training_monitor`→`self.monitor`; `self._training_lock`→`self._lock`;
  `self._stop_requested`→`self._stop_event`; `self._network_params`→`self._params`;
  `has_network()`→`has_model()` (keep a deprecated alias if any external caller needs it); add
  `self._dataset_name`, `self._last_result`, `self._last_error`, `join(timeout=None)`. **Update every
  by-name call site in `src/tests/unit/` in the same PR** (H2 — `patch.object(..., "has_network")` and
  `mgr.training_monitor`/`mgr._stop_requested` sites raise `AttributeError` at patch time, failing the
  required Unit Tests lane on 3.12/3.13/3.14).
- **Behavior-preserving because:** pure renames; no projection on any pinned route changes. **Not**
  "purely internal" — these are public attributes with unit-suite call sites, updated here.
- **Lanes:** **Unit Tests (load-bearing)**, golden + conformance, pre-commit, Quality Gate.
- **Rollback:** revert — mechanical rename, self-contained.

### PR-B2b — Converge method **signatures/returns**

- **Do:** `start_training` params `x→X, y→y, x_val→X_val, y_val→y_val` plus `*, dataset_name=None,
  **fit_kwargs`; converge `load_snapshot`/`restore_for_retrain`/`resume_from_snapshot` to return the
  **status dict** (not `bool`), updating their routes + unit tests.
- **Behavior-preserving because:** the snapshot routes are **not golden-pinned** (only
  network/status/metrics are); the return-shape change touches only those routes.
- **Lanes:** Unit Tests, golden + conformance, pre-commit, Quality Gate; manually re-exercise snapshot
  routes for shape sanity.
- **Rollback:** revert — isolated to snapshot routes + `start_training` signature.

### PR-B3 — Replace monkey-patch monitoring with the `on_event` sink (the crux)

- **Spike first (OQ-B1).** Prove the CCN can drive `on_event` richly enough to reproduce **both** (a)
  the REST projection (`current_epoch`, `current_hidden_units`, `current_phase`, `total_metrics`,
  post-train `epoch:3`/`hidden_units:2`) **and** (b) the **`/ws/training` per-candidate stream** (H4 —
  `candidate_progress`, `grow_iteration`, `all_correlations` at per-candidate granularity). The five
  coarse `TrainingEvent` types discard per-candidate detail, so the spike must decide: extend the event
  payload, or **retain the drain→broadcast side-channel** alongside `on_event`. **Exit test = REST
  API-snapshot golden AND a WS-granularity assertion** (over a real `fit`+`grow`, `/ws/training` still
  emits per-candidate frames).
- **Do (if the spike passes):** `CascorModel.fit` emits events through `on_event`; a manager
  `_handle_event` updates the **same** `TrainingMonitor`/`TrainingState` objects the read routes
  serialize (and the WS side-channel if retained); delete `_install_monitoring_hooks` /
  `_original_methods` / `_restore_original_methods`.
- **Behavior-preserving because:** REST projection held byte-identical (golden) **and** WS granularity
  preserved (assertion). If either cannot hold without CCN-invasive change → escalate: re-captured
  golden (declared change) or **cut the B-phase at B2b** (interface adopted for the kernel; monitoring
  mechanism deferred to the A-phase). This is the kill-criterion in action.
- **Lanes:** golden (REST) + conformance + **a new WS-granularity test** + Unit Tests + Quality Gate.
- **Rollback:** revert — restores the monkey-patch path wholesale (keep it in one commit for clean
  revert).

### PR-B4 — Native conformance against `CascorModel`

- **Do:** point `test_model_core_conformance.py` at the production `CascorModel` (via `make_model()`),
  so conformance runs against production code = "native conformance"; retire the test-only
  `cascor_model_core_adapter.py` (delete, or reduce to a thin re-export). Keep the classification
  dataset factory + `make_serializer=None` (D-C4) and the no-op `grow_step` guard (D-C3).
- **Behavior-preserving because:** test-only wiring; production behavior unchanged.
- **Lanes:** conformance (against production), golden untouched, Quality Gate.
- **Rollback:** revert — test wiring only.

### PR-B5 — (Optional) read-route projection delegation

- **Do (only if provably identical):** where a read route's legacy JSON equals what an interface member
  produces, delegate (e.g. `get_network_info` sizes via `input_shape`/`output_shape`). Do **not** adopt
  model-core's native topology shape on any pinned route.
- **Lanes:** golden exact-compare must pass with no fixture change, else revert the delegation.
- **Rollback:** revert the delegation; legacy projection restored.

---

## §6. Seam alignment — making the A-phase a thin repoint

`ServiceLifecycleManager` (juniper-service-core, merged) holds `self.model` injected via
`attach_model()` (no `_create_model()` hook), drives `self.model.fit(..., on_event=self._handle_event,
...)`, and ships generic `/v1/training|metrics|dataset|network` routes. Alignment actions (folded into
B1/B2):

- **Model seam:** `create_network` builds the CCN, wraps it in `CascorModel`, and calls
  `self.attach_model(<CascorModel>)` (sets `self.model`). Keep `create_network` as the cascor-only
  model-building override the base anticipates.
- **Attribute names:** converge to the base's canonical names (`self.model`, `self.monitor`,
  `self._lock`, `self._stop_event`, `self._params`, `self._dataset_name`, `self._last_result`,
  `self._last_error`) — PR-B2a.
- **Method names/returns:** snapshot methods + lifecycle verbs already match the base names; converge
  signatures/returns (PR-B2b). `update_params` is the base's *designated override* (cascor `super()`s
  then applies candidate-pool validation). cascor's richer liveness heartbeat stays a marked extension.
- **Monitoring:** the `on_event` sink (PR-B3) is what lets the A-phase inherit `run` /
  `_train_thread_target` / `_handle_event` verbatim. Until then the B-phase is interface-adopted but
  not fully seam-aligned on monitoring.

**A-phase prerequisites (NOT B-phase blockers, but record them):**

- `juniper-service-core` is **merged but unpublished** (`_version.py` + PyPI both still `0.1.0`); the
  T2 code (#473/#476/#478) needs a version bump + release before any consumer can pin it.
- The `JuniperCascor1` editable install of `juniper-service-core` is **stale** — it resolves to a
  pre-T2 worktree (`.../.claude/worktrees/validated-herding-pretzel/...`) whose `lifecycle` is the flat
  T1 stub, so `from juniper_service_core.lifecycle.manager import ServiceLifecycleManager` raises
  `ModuleNotFoundError` in that env today. The A-phase must re-point or publish first. The B-phase does
  not import service-core, so this does not block it — flag it (the class of orphaned editable install
  `util/editable_install_drift_check.py` exists to catch).

---

## §7. Risks, guardrails, kill-criterion

| Risk | Guardrail |
| --- | --- |
| CCN numerics drift → trajectory/predict goldens break | Wrapper never touches CCN math; **never re-seeds/re-constructs** (§4.2); CCN frozen; golden lane every PR |
| REST projection key-set/string/count drift → API-snapshot goldens break | Read routes keep legacy projection; never adopt model-core's native topology shape on a pinned route |
| **WS per-candidate stream degrades silently (H4)** | PR-B3 spike exit includes a WS-granularity assertion; retain drain→broadcast side-channel or extend events; REST golden alone is insufficient |
| **`self.network` property can't take the 4 assignments (H1)** | Property has get **and** set; HDF5-load re-wraps the bare CCN; write-through sites left untouched |
| **New runtime dep fails Lockfile Freshness (H3)** | PR-B1 regenerates `requirements.lock` (`--extra ml api observability juniper-data`, `--no-emit-package torch`) same-PR; keep `lockfile-update.yml` recipe in lock-step |
| **Public renames fail Unit Tests lane (H2)** | PR-B2a updates all `src/tests/unit/` call sites + `patch.object` targets same-PR |
| Wrapper `predict` returns numpy → manager `.argmax(dim=1)` breaks (M3) | Decision boundary stays on `self.model.network.forward` (torch); interface `predict` returns numpy and is for conformance |
| model-core version skew (env 0.2.0 / PyPI 0.3.0 / conformance pin `<0.3.0`) | Pin production to match conformance (`>=0.2.0,<0.3.0`); a 0.3.0 bump is a separate lockstep PR (OQ-B2). model-core has zero deps / no torch import |
| Concurrent-session collision | DUP-GUARD before each PR: `gh pr list -R pcalnon/juniper-cascor` **and** scan `worktrees/` for cascor branches |
| Squash-merge dropping follow-up commits | One clean commit per PR, or Rebase-and-merge (per standing feedback) |

**Standing rules:** Paul approves all merges + PyPI/deploy gates (drive to the gate, hand off).
Worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/`. Scripts under `util/` (never
`/tmp/`). Run the gate on `JuniperCascor1`. Note `uv.lock` is a stale stub (no CI consumes it — only
`requirements.lock` gates); do not waste effort regenerating it.

---

## §8. Verification — required lanes (run on JuniperCascor1)

The gate is golden + conformance, but several other **required** checks are in scope for B-phase PRs
(see §5 per-PR lanes): Unit Tests + Coverage (3.12/3.13/3.14 + macOS-3.12, 80% gate), pre-commit
(mypy/flake8/black/isort ×3), Lockfile Freshness, Async-route audit, Security Scans, Quick/Full
Integration Tests, Quality Gate. The two gate lanes, run from the cascor worktree root:

```bash
conda activate JuniperCascor1

# Golden / Snapshot Regression (modules under src/tests/integration; harness src/tests/golden_support.py)
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
python -m pytest -m golden --golden --slow --integration \
    src/tests/integration --verbose --timeout=300

# model-core Conformance
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 CASCOR_NUM_PROCESSES=1 \
python -m pytest -m conformance --conformance --slow --integration \
    src/tests/conformance --verbose --timeout=300

# Lockfile freshness check (PR-B1) — regenerate, then diff must be empty
uv pip compile pyproject.toml --extra ml --extra api --extra observability --extra juniper-data \
    --index-strategy unsafe-best-match --no-emit-package torch --upgrade -o requirements.lock
```

Both gate flags (`--golden` / `--conformance`) are off by default and require marker+flag+`--integration`+`--slow`
to collect. Re-capture goldens (only with Paul's reviewed sign-off) by prepending `GOLDEN_CAPTURE=1`.
Each lane runs in low tens of seconds. After lint-green, also `gh workflow run` the lanes on the branch
(lint-green ≠ run-green).

---

## §9. Open questions (for the build thread / Paul)

- **OQ-B1 — the `on_event` appetite (PR-B3), now WS-inclusive.** Can the CCN drive `on_event` richly
  enough to reproduce both the REST projection **and** the `/ws/training` per-candidate granularity
  (H4) without CCN-invasive changes? Recommended: spike it with **both** exit tests. If it needs
  invasive CCN event emission (touching `juniper-cascor-model`) or a retained side-channel, that is an
  appetite/kill-criterion decision for Paul — do the full migration (true seam alignment; A-phase
  inherits `run` verbatim) vs. **cut the B-phase at B2b** (interface adopted for the kernel; monitoring
  mechanism deferred to the A-phase). This is the single biggest scoping decision in the B-phase.
- **OQ-B2 — model-core production pin.** The interface is stable across 0.2.0/0.3.0; the conformance
  test pins `>=0.2.0,<0.3.0`; the env has 0.2.0 installed. Recommended: pin the production dependency to
  **match** (`>=0.2.0,<0.3.0`) for the B-phase (an unbounded `>=0.2.0` could let pip resolve 0.3.0 and
  violate the conformance `<0.3.0`); adopt 0.3.0 later as a trivial lockstep (widen both pins + install)
  only if a 0.3.0 feature is needed.
- **OQ-B3 — `CascorModel` module location.** Proposed `src/api/model/cascor_model.py`; finalize so it
  is importable by both the lifecycle manager and the conformance test without a circular import.
- **OQ-B4 — `self.network` retention shape.** Recommended: a **get/set** property over `self.model`
  (§4.3) through B1–B3 to minimize churn on the ~40 cascor-specific reaches and absorb the four
  assignment sites; drop it (or keep as a documented back-compat alias) only when convenient.

---

## §10. Provenance

- **Audits (this thread, 2026-06-19, read-only against the cascor worktree at `origin/main` post-#342):**
  (A) `manager.py` model coupling + CCN public surface; (B) routes/state-machine/monitor/coordinator
  consumers; (C) model-core `TrainingLifecycleBase` + service-core `ServiceLifecycleManager` seam;
  (D) gate invariants — golden #340 + conformance #341 + run harness. **Validation (§0.1):** an
  independent fact-check (all load-bearing claims confirmed; 3 path/line corrections) + a
  completeness/risk critique (4 HIGH + 4 lesser gaps, all folded into this revision).
- **Design of record:** [`JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md`](JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md)
  §2 (DR-1); [`JUNIPER_CASCOR_MODEL_CORE_CONFORMANCE_WIRING_PLAN_2026-06-18.md`](JUNIPER_CASCOR_MODEL_CORE_CONFORMANCE_WIRING_PLAN_2026-06-18.md)
  (D-C1…D-C5, the adapter mapping). Refactor plan `JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`
  (Part 8 §8.4 A/B split, §2.7 kill-criterion); service-core T2 audit
  `JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md`.
- **Gate evidence:** cascor #340 (golden), #341 (conformance), #342 (release enforcement); ruleset
  `juniper-cascor-rules-1` (id 15081045, active) with both gate halves required. model-core installed
  0.2.0 / repo + PyPI 0.3.0; service-core merged-unpublished 0.1.0.
