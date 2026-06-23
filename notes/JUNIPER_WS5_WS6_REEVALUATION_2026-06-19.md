# Juniper WS-5 & WS-6 Reevaluation — Reality Audit + Recommended Sequencing

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-19

---

> **⟢ STATUS 2026-06-21.** DR-1..DR-5 ratified; since then: WS-6 B-phase **B1/B2a/B2b MERGED** (cascor
> #345/#346/#347); OUT-11 service-core T2 fully merged (0.2.0 publish = ml #502, pending); WS-5 A0 + 3-D
> viz shipped (canopy #372, #374–#379). §2.2's "OUT-11 step 3 remaining" is superseded. See
> `JUNIPER_DOCS_REALITY_AUDIT_2026-06-21.md`.
>
> **⟢ UPDATE 2026-06-23.** (a) **WS-6 B-phase B3 fully MERGED** (cascor B3.1 #352 / B3.2 #353 / B3.3 #355 —
> the `on_event` cutover; only **B4** remains) and **service-core 0.2.0 is LIVE on PyPI** (#502), so the
> A-phase publish-blocker is cleared. (b) **DR-1 is NOT a committed B→A** — it was ratified only as "defer
> the A-decision"; the A-phase is now gated on B4 + DR-1 / soak (OQ-17) / manager-appetite (see
> `JUNIPER_WS6_APHASE_READINESS_VALIDATION_2026-06-22.md`). (c) **WS-5 A1 is no longer "0% built"** — A1-i
> (canopy #383, `RecurrenceServiceAdapter`) + A1-ii (#385, `RecurrenceBackend` + provider-keyed routing,
> the D1-A one-shot bridge) shipped; A1-iii scope = #516. The §1/§2.3/§3.1 "A1 designed-only / 0% built"
> and "`execution`-field-first" claims are superseded (routing shipped via `provider`/`status`, no
> `ModelSpec.execution` field — DR-2's field-first sequencing is now a stale prerequisite).

## 0. Purpose & method

The model/middleware refactor's last two unshipped workstreams — **WS-5** (generalize juniper-canopy)
and **WS-6** (refactor juniper-cascor onto the shared packages) — were last described in roadmap text
that now predates several merges. This document **reevaluates both against current `origin/main`
reality** and recommends the near-term sequence. It does **not** redesign either workstream; the
design-of-record docs (cited inline) stand.

**Method:** two independent reality-audit sub-agents surveyed `origin/main` of juniper-ml,
juniper-cascor, and juniper-canopy (plus merged/open PRs and the active branch rulesets); the synthesis
was then put through two more adversarial passes (a fact-checker that re-verified every load-bearing
claim against `origin/main` down to merge SHAs, and a completeness/risk critic). Their corrections are
folded in. A recurring footgun all audits hit: **local working clones were stale** (juniper-cascor and
juniper-canopy both behind `origin/main`, `src/model_registry.py` absent locally) — all claims here are
taken against `origin/main` after `git fetch`, not the local trees (roadmap OUT-2).

---

## 1. TL;DR

| Workstream | Headline (corrected) | Dependency-clear next move | Pivotal decision for Paul |
| --- | --- | --- | --- |
| **WS-6** | **Gate ARMED, cutover not started.** Both gate halves merged + required (golden #340, conformance #341). "Trigger MET" is true but *overstates readiness*: the **A-phase is blocked on OUT-11** (service-core T2 unpublished); only the **B-phase is dependency-clear**. | WS-6 **B-phase** (cascor adopts `TrainableModel`/`GrowableModel`; keeps its own service stack). | **WS-6 appetite (DR-1):** pursue **B→A** (the roadmap's recommendation) once OUT-11 lands, or **park after B** (S2)? |
| **WS-5** | **A0 shipped, A1 designed-only.** Registry merged (canopy #372); selection surface 0% built (no open PR). The real lift is **not** the UI — it is **3-D dataset display** (D2) and the **execution-paradigm mismatch** (canopy live-poll vs. recurrence one-shot fit), unratified as D1. | **D2** (3-D dataset load + display — independent, user-visible) **+ A1a** (after the `execution` field ratifies). | **D1 execution paradigm (DR-2):** canopy grows a one-shot fit path, or recurrence grows async? |

**Both** "stale roadmap" findings are real and should be reconciled (§5). **Neither** workstream is
blocked by the other; WS-5 sits ahead of WS-6 on the critical path.

---

## 2. WS-6 reevaluation — juniper-cascor refactor

### 2.1 Corrected status

- **Gate: COMPLETE / ARMED.** Both halves are merged to juniper-cascor `origin/main` and are **required
  status checks** on the active ruleset `juniper-cascor-rules-1` (id 15081045):
  - **OUT-12 golden/snapshot suite** — cascor PR #340, merged 2026-06-18 (merge `b45d71c`). Adds
    `src/tests/integration/test_golden_trajectory.py`, a serialization round-trip + API snapshots, a
    `--golden` gate, frozen `src/tests/fixtures/golden/two_spiral_seed42.npz`, and
    `golden-regression.yml`. Tolerance-based (rtol 1e-3 / atol 1e-4; structural signals exact) — OQ-13
    resolved.
  - **OUT-13 model-core conformance adapter** — cascor PR **#341, MERGED 2026-06-18** (merge
    `e22342a`), all required checks green. Adds `src/tests/conformance/cascor_model_core_adapter.py`
    (`CascorModelCoreAdapter(GrowableModel)`), `conformance.yml`, and the test-dep
    `juniper-model-core[conformance]>=0.2.0,<0.3.0`. **Test-only — no production change.** (Earlier
    notes that called #341 "open" are stale.)
- **Cutover (6a/6b): NOT started — correct.** cascor production has **zero** `juniper_service_core` /
  `juniper_model_core` imports outside `src/tests/`; cascor still ships its own `src/api/**`. This is
  the design's intent: the cutover is the last, gated step.
- **Not WS-6 (do not conflate):** the **cascor-core → `juniper-cascor-model` relocation** is DONE
  (cascor #328, PyPI `juniper-cascor-model` 0.1.0). That is the package-placement anchor, a *different*
  package from `juniper-model-core` (the abstract kit the gate consumes; PyPI 0.1.0/0.2.0).

### 2.2 The A-phase / B-phase split, and what OUT-11 changes

The cutover splits into two sub-phases (refactor plan Part 8 §8.4; corroborated by platform roadmap
line 312):

- **6b — model-core adoption (behavioral):** cascor's lifecycle/routes operate against
  `TrainableModel`/`GrowableModel` instead of naming `CascadeCorrelationNetwork`. **Dependency-clear
  today** — the gate is green and it needs no other package.
- **6a — service-core repoint (mechanical):** cascor's `src/api/**` become thin re-export shims over
  `juniper_service_core`. **Blocked on OUT-11** (and on OUT-11 being *published*).

**Crucial nuance the bare "trigger MET" hides:** OUT-11 (build juniper-service-core's T2 surface) is
**already authorized and being built regardless of the WS-6 A-decision** — the T2 design/audit doc
records "Paul has chosen to proceed (Option 3)… **GATE: GO (scoped)**", a deliberate foundation-first
front-run of its consumer (RK-4, accepted). Status:

- Step 1a merged (juniper-ml #473, merge `abfb0bf`): `ServiceLifecycleManager` + generic
  `/v1/training|metrics|dataset|network` routes; 82 tests; cascor + model-core untouched.
- Remaining: snapshots/replay (step 1b), websocket subsystem (step 2), worker-pool +
  `TaskDistributor` (step 3). **OQ-11 is now resolved by evidence** (T2 audit §5.2/§5.6: the worker
  *pool infrastructure* is generic but the task envelope/reduction is cascade-bound → defer the
  generic envelope to WS-8). So **routes + lifecycle + websocket are fully extractable now**; only the
  worker envelope defers.
- **Publish gap:** `juniper-service-core` is still **0.1.0 on PyPI** and `_version.py` on `origin/main`
  is still `0.1.0` — the #473 T2 code is **unpublished**. Per the publish-first invariant (refactor
  plan §8.1), no consumer can pin T2 until it is on PyPI/soaked, or the container dies with
  `ModuleNotFoundError`.

**Consequence for cost accounting:** because OUT-11 is a committed build, the A-phase *marginal* cost
is **not** "build OUT-11 + publish + repoint" — it is just the repoint of cascor's `src/api/**` to
thin shims (the T2 audit classifies this as the lowest-coupling extraction). This materially changes
the WS-6-appetite trade (DR-1).

### 2.3 Recommendation

1. **Reframe the status line** everywhere from "WS-6 trigger MET" to **"WS-6 gate ARMED; B-phase ready;
   A-phase blocked on OUT-11 (service-core T2 unpublished)."** The bare "trigger MET" reads as "WS-6 may
   proceed," which is only half-true.
2. **Do the B-phase now** (if WS-6 proceeds past the gate) — it is the only dependency-clear cutover,
   it exercises the conformance gate against real behavior (the merged adapter is test-only, with a
   no-op `grow_step`), and it is the roadmap's own first step (B→A, §5.4). **Design the B-phase changes
   to the CASCOR-BOUND `lifecycle/manager` against the future `ServiceLifecycleManager` subclass seam**
   (T2 audit §5.6), so a later A-phase does not redo them. Note both gate checks (golden #340,
   conformance #341) are **required** — a B-phase PR that shifts event/metric semantics will be
   *blocked*, not merely flagged.
3. **Raise the WS-6-appetite decision now (DR-1).** The roadmap recommends **B→A** (adopt model-core
   first; repoint to service-core once OUT-11 lands — roadmap §5.4 line 245). The alternative is **S2:
   park after B** (roadmap §6.1) — an *appetite* posture, distinct from the **kill-criterion** (refactor
   plan §2.7), which fires only if conformance *cannot be made green* and therefore has **not** fired
   (#341 is green). Recommendation: **do B now, defer the A-decision until OUT-11 is published +
   soaked**, then choose B→A vs. park with full information. The counterweight to parking: under
   park-after-B, service-core's **entire T2 surface ships with zero production consumers** (recurrence
   wrote its own synchronous routes and consumes none of T2; cascor-B keeps its own stack) — the RK-4
   over-abstraction risk, and itself an argument for eventually doing the A-phase to give T2 a real
   consumer. This is Paul's call; the doc only frames it.

---

## 3. WS-5 reevaluation — juniper-canopy generalization

### 3.1 Corrected status

- **A0 (registry substrate): SHIPPED** — canopy PR **#372** (merge `9d1274b`, 2026-06-18), *not* #368.
  (**#368 is the tracking issue**, not a PR.) Adds `src/model_registry.py` (frozen `DatasetTypeSpec` /
  `ModelSpec`, 5 dataset seeds, `cascor` [live, 2-D] + `recurrence` [coming_soon, 3-D, `requires_dt`]),
  `dataset_type_options()`, and rewires the hardcoded dropdown at `dashboard_manager.py:1115`.
  **Behavior-preserving plumbing; no user-visible feature.**
- **A1 (dedicated selection surface): DESIGNED ONLY — 0% built.** Zero open canopy PRs; the
  compatibility predicate / resolvers / Models surface / `RecurrenceServiceAdapter` / model→backend
  routing exist **nowhere** on `origin/main` except as TODOs in the A0 registry header. `create_backend()`
  still keys only on demo-vs-service, not `nn_model`/`provider`.
- **3-D dataset load + display (D2): NOT built.** Canopy's local data/plot path hard-assumes 2-D
  (`demo_mode.py:833`: `if inputs.ndim != 2: raise ValueError(...)`) — a wrong-direction debt for any
  3-D model. No sequence/Δt plotter mode, no 3-D `DatasetTypeSpec` rows.
- **UI-regression harness: fully enrolled.** L1 control-graph lint + L2 behavioral gate shipped via
  canopy #364, with #366 completing the orphan wiring (and recovering #365's fix, lost to a
  stacked-squash footgun) and **#373** enrolling the last three controls in L2. `KNOWN_ORPHANS` is now
  empty with anti-rot guards. (Note: "#430" in earlier notes is a *juniper-ml* PR; the canopy harness
  set is #364/#365/#366/#373.)

### 3.2 The real lift is the execution paradigm + 3-D display, not the table UI

The A1-enabler scope doc names **two** dominant canopy lifts, neither of which is the selection table:

- **D2 — 3-D dataset load + display** (enabler §3.4). Canopy must gain `ndim`-aware load + a
  sequence/Δt plotter so a user can *view* a 3-D dataset. **Independently valuable, no upstream gate**,
  and it reverses the `ndim==2` debt. *Training delivery stays service-side* — D2 is display only.
- **D1 — the execution-paradigm mismatch** (unratified). Canopy is a live-poll monitor; the recurrence
  service is a synchronous one-shot fit. Making `recurrence` a *meaningful* selectable model requires
  either canopy grows a one-shot fit + render path (D1-A, the enabler's explicit recommendation) or the
  recurrence service grows async lifecycle (D1-B). The enabler rejects D1-B (it would fabricate
  per-epoch progress for a single lstsq solve).

Beyond those: a live recurrence service in juniper-deploy (Phase 0; Paul-gated), and canopy integration
(Phase 2): a `RecurrenceServiceAdapter` (httpx, sync REST, **must send `X-API-Key`**, generous
read-timeout, 409/timeout handling), an `nn_model`/`provider`-keyed `create_backend()`, cascade-panel
suppression, the `nn_model` backend mirror, and flipping `recurrence.status` `coming_soon → live`.

### 3.3 Recommendation

1. **Do D2 (3-D dataset load + display) now** — it is the genuinely dependency-clear, independently
   valuable WS-5 move (no upstream gate; delivers user-visible capability; reverses the `ndim==2`
   debt). It has the stronger standalone payoff of the "do-now" candidates.
2. **Ratify D1 (DR-2), including the `ModelSpec.execution` axis, *before* A1a.** A1a's compatibility
   predicate and panel-suppression logic encode `execution` mode (D1-A makes it a first-class registry
   field), so building A1a's predicate before the field is ratified risks rework. Sequence:
   **`execution` field → A1a predicate/surface.**
3. **A1a (compatibility engine + sidebar gate) follows the `execution`-field ratification**, UI-only,
   against the soft-gated `coming_soon` recurrence. **A1b (full facet table)** follows A1a. The *payoff*
   (a real second model) needs the cross-repo enabler (Phase 0 + Phase 2), not the UI shell.
4. **Resolve the transport decision (DR-5):** the two source docs conflict — the umbrella roadmap makes
   **OUT-8 (`juniper-recurrence-client`) "blocks WS-5"** (OUT-9 depends on OUT-8), while the A1-enabler
   recommends an **in-canopy `RecurrenceServiceAdapter` (D3)** and deferring the client unless a second
   consumer exists. Recommendation: **in-canopy adapter first** (canopy is the only consumer today),
   which removes OUT-8 from the WS-5 critical path; promote to a published client when a second consumer
   appears.
5. **Keep Task B (canopy + model-core crossval) OUT of WS-5 scope (DR-3).** Note the asymmetry: the
   **service side already exists** (the recurrence app ships `POST /v1/crossval` on model-core 0.2.0+);
   only the **canopy surface** is deferred. It is not in the WS-5 design-of-record, has zero canopy
   code, and appears only as A1-enabler **OQ-2**. Revisit after A1 + recurrence-live.

---

## 4. Cross-cutting — shared dependencies & ownership

- **WS-5 and WS-6 are independent of each other.** WS-5 (step 5) sits ahead of WS-6 (step 6, Wave E,
  sequenced last). Neither blocks the other.
- **OUT-11 (service-core T2) is shared infra**, but for *different* slices and is **already committed**
  (Option 3, §2.2): WS-6-6a needs **step 1** (routes + lifecycle); WS-5 Phase 2 *may* reuse **step 2**
  (websocket subsystem) for live recurrence streaming — *if* WS-5 elects the ws subsystem over a
  bespoke adapter. So OUT-11's completion is not conditional on the WS-6 A-decision; the A-decision only
  governs whether cascor *repoints onto* it.
- **OUT-8 vs. in-canopy adapter** is the open WS-5 transport decision (DR-5, §3.3) — it determines
  whether `juniper-recurrence-client` is on the WS-5 critical path at all.
- **Recurrence deploy service (Phase 0):** the Dockerfile is **already done** (recurrence #21,
  `76ad27a`); the parent plan assigns the compose service to **WS-7**, and the A1-enabler notes it "may
  land from the concurrent WS-7/OUT-4 effort." So the live action is **not** a fresh ownership
  assignment but **verification** (DR-4): confirm the concurrent WS-7 session ships it *with* the
  canopy-required `juniper_recurrence_api_keys` secret + outbound `X-API-Key` wiring, and detect a
  stall / incomplete hand-off.

---

## 5. Doc-hygiene actions (reconcile stale text)

Low-risk text reconciliations that should land regardless of the DR decisions — but **as dedicated
doc-only PRs after a `gh pr list` check**, not blanket in-place edits: the parent plan / roadmap may be
mid-edit by concurrent sessions (the roadmap itself declined its own hygiene fixes for that reason), so
mirror that caution (RK-11).

1. **`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`** §3.3/§4: WS-6 still shows "Not
   started / gate not captured" and OUT-13 "▶ NEXT" — both stale post-#341 (the doc self-admits its body
   cells were not rewritten). Update to "gate ARMED; cutover B-ready, A-blocked-on-OUT-11."
2. **`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`** Status Tracker line 54: WS-5 is
   still `PLANNED`; A0 (#372) has shipped → mark **WS-5 IN PROGRESS (A0 done; A1/D2 designed)**. (The
   WS-6 row was already corrected by #466.)
3. **MEMORY / notes** that cite "A0 = canopy #368" should read **#372** (#368 is the issue); the canopy
   UI-harness set is #364/#365/#366/#373 (not #430, a juniper-ml PR).

---

## 6. Recommended near-term sequence

Ordered by dependency-clarity (earlier items have no upstream blocker):

1. **Doc hygiene (§5)** — dedicated doc-only PRs after `gh pr list`. *No blocker.*
2. **Ratify the decisions:** DR-1 (B→A vs. park-after-B), DR-2 (D1 + the `ModelSpec.execution` field),
   DR-5 (in-canopy adapter vs. published client). These set the WS-5 integration shape and whether the
   A-phase / OUT-8 are on the critical path. *Paul-gated.*
3. **Dependency-clear build (parallelizable):**
   - WS-6 **B-phase** (if WS-6 proceeds) — native `TrainableModel`/`GrowableModel` in cascor, designed
     against the `ServiceLifecycleManager` seam; keep golden #340 + conformance #341 (required) green;
     honor the kill-criterion.
   - WS-5 **D2** (3-D dataset load + display) — independent, do now.
   - WS-5 **A1a** (compatibility engine + sidebar gate) — *after* the `execution` field ratifies (DR-2).
   - OUT-11 **step 1b/2** continues (already authorized, Option 3) toward a publishable `0.2.0`.
4. **Paul-gated cross-repo enabler:** recurrence **deploy service** (Phase 0, WS-7-owned — *verify* per
   DR-4) → unlocks WS-5 **Phase 2** (canopy recurrence training) once DR-2 + DR-5 are settled.
5. **Deferred:** WS-6 **A-phase** (only after OUT-11 published & soaked, if B→A is chosen); WS-5 **A1b**
   and panel adaptations; **Task B** canopy crossval surface (only if DR-3 pulls it in scope).

---

## 7. Decisions requested (ratification)

| ID | Decision | Recommendation | Why it matters |
| --- | --- | --- | --- |
| **DR-1** | **WS-6 appetite:** pursue **B→A** (model-core now; service-core repoint once OUT-11 lands + soaks) or **park after B** (S2)? | **Do B now; defer the A-decision** until OUT-11 is published + soaked, then choose. Lean B→A given OUT-11 is already committed (A-phase marginal cost ≈ the cascor route-repoint). | OUT-11 is being built regardless; the decision is only whether cascor repoints onto it. Park-after-B leaves T2 with zero consumers (RK-4). |
| **DR-2** | **WS-5 D1 execution paradigm:** canopy grows a one-shot fit path (D1-A) or recurrence grows async (D1-B)? **Plus:** ratify the `ModelSpec.execution` field before A1a. | **D1-A** (canopy one-shot path; `execution = "live"\|"one_shot"`), per the enabler's explicit recommendation; ratify the `execution` field first. | The dominant WS-5 lift; gates Phase 2 *and* the A1a predicate shape (sequencing inversion if A1a precedes it). |
| **DR-3** | **Task B (canopy + model-core crossval) placement:** in WS-5/A1, or separate downstream? | **Separate / deferred** (service-side `/v1/crossval` already exists; only the canopy surface is open). Revisit at A1-enabler OQ-2. | Avoids scope-creeping WS-5 with a code-less, undecided canopy feature. |
| **DR-4** | **Recurrence deploy service:** confirm the concurrent WS-7/OUT-4 delivery (not a fresh assignment). | **Verify** WS-7 ships it with the `juniper_recurrence_api_keys` secret + outbound `X-API-Key` wiring; detect stall. | Dockerfile (#21) is done; the risk is drop-between-sessions / incomplete hand-off, not double-counting. |
| **DR-5** | **WS-5 transport:** in-canopy `RecurrenceServiceAdapter` (enabler D3) or published `juniper-recurrence-client` (umbrella OUT-8)? | **In-canopy adapter first** (single consumer); promote to a client when a second consumer appears. | The two source docs conflict; determines whether OUT-8 is on the WS-5 critical path. |

---

## 8. Provenance

- WS-6 design of record: `JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` (Part 2.3/2.7,
  Part 8 §8.4), `JUNIPER_CASCOR_GOLDEN_REGRESSION_SUITE_BUILD_PLAN_2026-06-17.md`,
  `JUNIPER_CASCOR_MODEL_CORE_CONFORMANCE_WIRING_PLAN_2026-06-18.md` (cascor repo).
- WS-5 design of record: `JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` (D1–D8),
  `JUNIPER_CANOPY_MODEL_SELECTION_A1_ENABLER_SCOPE_2026-06-18.md` (D1/D2/D3 + phases),
  `JUNIPER_CANOPY_AUDIT_REGRESSIONS_AND_MODEL_SELECTION_2026-06-15.md`.
- OUT-11: `JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md` (Option 3 / GO-scoped; OQ-11
  resolution §5.2/§5.6); juniper-ml #473.
- Platform roadmap (B→A §5.4; S2 §6.1; A↔OUT-11 edge line 312):
  `JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`.
- Evidence: cascor #328 / #340 / #341; canopy #364 / #365 / #366 / #372 / #373; juniper-ml #466 / #473.
  Audit basis: `origin/main` of all three repos (2026-06-19), active ruleset 15081045. Synthesis
  fact-checked + completeness-critiqued by two independent adversarial passes.
