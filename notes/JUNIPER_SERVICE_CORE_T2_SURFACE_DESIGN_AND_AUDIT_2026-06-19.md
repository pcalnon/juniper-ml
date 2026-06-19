# juniper-service-core T2 Surface — Design, Gate-Audit & Build Plan (OUT-11)

**Project**: Juniper ML Research Platform — service-tier template (roadmap **OUT-11**)
**Repository**: pcalnon/juniper-ml (the `juniper-service-core/` subdir package)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (DRAFT — scoped from a live read of cascor `api/` + service-core T1, 2026-06-19; pending §0 ratification)
**Last Updated**: 2026-06-19

---

> **What this is.** The design + gate-audit + build plan for the **T2 surface** of `juniper-service-core` —
> the websocket subsystem, worker subsystem + `TaskDistributor`, generic routes, and lifecycle base that the
> service template is missing. **OUT-11** in [`JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md`](JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md);
> the consumer that pulls it is WS-6's A-phase (cascor adoption). Sequenced (Paul, 2026-06-19): **ratify this
> note → audit that OUT-11's gates aren't already met (§5) → full build (§6).**
>
> **The headline finding.** OUT-11 is **not greenfield — it is an EXTRACTION.** cascor already ships a complete,
> working T2 implementation; service-core has **zero** T2 files. OUT-11 = *de-cascor* cascor's T2 modules into a
> model-agnostic base (the refactor plan's "extract base, keep cascor subclass"), driven by a stub model. This is
> lower-implementation-risk than a from-scratch build (the code exists and works) but higher-**decoupling**-risk
> (cascor-specific assumptions — cascade/candidate/correlation — must be lifted out behind the `TrainableModel` /
> `GrowableModel` / `TrainingEvent` interfaces that `juniper-model-core` already defines).

---

## §0. Status & decisions needing Paul

- **D-T1 — OUT-11 is an EXTRACTION from cascor, not a greenfield build (§3).** Confirmed by code: cascor's
  `api/{websocket,workers,lifecycle,routes}/` + `parallelism/task_distributor.py` are the source. **Concur?**
- **D-T2 — No immediate consumer; cascor (WS-6) is the only real one.** recurrence wrote its own synchronous
  routes (no ws, no worker); ws→WS-5 (canopy, hot), worker→WS-8 (deferred, OQ-11 open). Building T2 now is
  *foundation-first* and front-runs its consumer (RK-4). Paul has chosen to proceed (Option 3) after the audit.
  **Confirm the front-run is accepted.**
- **D-T3 — Decoupling seam = the model-core interfaces.** Generic routes/lifecycle/ws operate on a
  `TrainableModel`/`GrowableModel` + emit `TrainingEvent`s (already defined in `juniper-model-core`). The
  conformance kit's stub `ReferenceGrowableModel` is the contract-test driver. **Concur?**
- **D-T4 — OQ-11 (worker-layer genericity) is resolved in the audit (§5.2), not assumed.** If cascor's worker
  protocol is too cascade-specific to generalize, the worker subsystem ships cascor-subclassed (or defers to
  WS-8). **Concur the audit gates the worker layer?**
- **D-T5 — Build order = consumer-priority (§6): routes+lifecycle base → ws → worker.** Routes are what WS-6's
  A-phase needs first and are the lowest-coupling extraction; worker is last (OQ-11). **Concur?**

## §1. The T2 surface (what's missing from service-core)

service-core today is **T1 only**: `app.py` (factory), `health.py`, `security.py`, `middleware.py`, `launcher.py`,
`lifecycle.py` (a thin training-lifecycle base + `TrainingEvent` sink), `settings.py`, `secrets.py`. The refactor
plan (§ Part 4, T1/T2 table; §"juniper-service-core") defines T2 as the **semi-generic service machinery**:

| T2 component | What it is | cascor source (extraction src) | Consumer |
|--------------|-----------|--------------------------------|----------|
| **Generic routes** | model-agnostic training/status/metrics/dataset/snapshot routes over an injected model | `src/api/routes/{training,metrics,dataset,snapshots,history,network}.py` | WS-6 (cascor) |
| **Lifecycle base** | run/monitor/state-machine over `model.fit(on_event=…)` | `src/api/lifecycle/{manager,monitor,state_machine}.py` | WS-6 |
| **WebSocket subsystem** | live metrics/state/event streaming + control channel | `src/api/websocket/{manager,messages,training_stream,control_stream,control_security,worker_stream}.py` | WS-5 (canopy live monitor) |
| **Worker subsystem + TaskDistributor** | distributed candidate/unit training | `src/api/workers/{coordinator,protocol,registry,audit,metrics,security}.py` + `src/parallelism/task_distributor.py` | WS-8 (deferred; OQ-11) |

## §2. Grounding (verified 2026-06-19)

- service-core `juniper_service_core/`: **0** files under ws/workers/routes/lifecycle-dir — T2 is genuinely unbuilt.
- cascor `src/api/`: full T2 present (the table above), working in production, exercised by cascor's own tests +
  the OUT-12 golden API snapshots + OUT-13 conformance adapter.
- model-core (v0.2.0) already provides the decoupling vocabulary: `TrainableModel`/`GrowableModel` ABCs,
  `TrainingEvent` + `TRAINING_EVENT_TYPES`, `Topology`, `validate_*`, and the `conformance` kit (stub models).

## §3. Why this is an extraction, and what that changes

cascor's T2 modules are **written against cascor** (cascade growth, candidate pools, correlation, two-spiral). The
extraction must lift each onto the model-core interfaces so a *stub regression model* (`ReferenceGrowableModel`)
drives the same routes/ws with no `argmax`/accuracy/cascade assumptions (the RK-6 guard). The win: the code is
proven; the work is **decoupling + a contract test**, not invention. The risk: hidden cascor coupling (the
"semi-generic" tag). §5 audits exactly how deep that coupling runs **before** the build commits to it.

## §4. Consumer analysis (the front-run reality)

| Consumer | Pulls | When |
|----------|-------|------|
| cascor (WS-6 A-phase) | routes + lifecycle + ws + worker | deferred (gated by the now-green OUT-12/OUT-13 WS-6 gate) |
| recurrence app | **nothing** — wrote its own sync routes, no ws, no worker | n/a |
| canopy (WS-5) | ws live-monitor | hot (another session); not via service-core yet |
| recurrence-worker (WS-8) | worker subsystem | deferred; **OQ-11 unresolved** |

⇒ Building T2 now lays the foundation **ahead of** its consumer. Paul has accepted this (Option 3) — the value is
that WS-6 then becomes a thin adoption rather than a big extraction, and the OUT-12/OUT-13 gate protects it.

## §5. Gate-audit (run BEFORE §6 — "verify OUT-11's gates aren't already met")

A focused, read-only audit of cascor's T2 to confirm the build premise and surface blockers:

- **§5.1 Extractability per module.** For each T2 module, grep for cascor-only symbols (cascade, candidate,
  correlation, two-spiral, `CascadeCorrelationNetwork`, `hidden_units`). Classify: **clean** (operates on
  generic model/events already), **adapter** (needs a thin interface shim), **cascor-bound** (stays subclassed).
  Output: a per-module extraction ledger.
- **§5.2 OQ-11 — worker genericity (resolve by evidence, OQ-13-style).** Read `workers/protocol.py` +
  `task_distributor.py`: is the task payload cascade-specific (candidate weights/correlation) or a generic
  "train this sub-unit on this data" envelope? If cascade-specific ⇒ worker layer ships cascor-subclassed or
  defers to WS-8. Record the verdict + evidence.
- **§5.3 Already-met check.** Confirm nothing already provides T2: no service-core stubs (verified: 0), no other
  in-flight extraction (dup-guard: worktrees dir + remote), and the recurrence app genuinely doesn't need it.
- **§5.4 Interface sufficiency.** Verify model-core's `TrainableModel`/`GrowableModel`/`TrainingEvent`/`Topology`
  cover everything the generic routes/ws need; note any gap (a model-core follow-up, not a blocker).
- **§5.5 Contract-test driver.** Confirm `ReferenceGrowableModel` (+ a tiny dataset) can drive every generic
  route + ws channel — the both-stacks-green proof.

The audit's output is a go/no-go + a per-module extraction ledger that the §6 build follows.

### §5.6 Audit findings (executed 2026-06-19, three parallel module audits) — GATE: **GO (scoped)**

**Routes + lifecycle (~70% extractable).**
- **CLEAN** (extract as-is): `routes/{admin,dataset,health,history,metrics,workers,snapshots}` + most of `routes/training` + `lifecycle/state_machine`.
- **ADAPTER** (thin shim): `routes/network` (→ `GrowableModel` topology/unit iface), `routes/training` (move spiral helper + candidate-pool validation to a cascor adapter), `lifecycle/monitor` (candidate/correlation become cascor `TrainingEvent` *payload*, not base monitor state).
- **CASCOR-BOUND** (cascor keeps subclass): `routes/decision_boundary` (intrinsic 2-D viz), `lifecycle/manager` (3k-line orchestrator). ⇒ Build a generic `ServiceLifecycleManager` base; cascor subclasses it.

**WebSocket (~70-80% extractable).**
- **CLEAN**: `manager` (broadcast/seq/replay/chunk infra), `training_stream`, `control_security`, `messages` (the generic 7 of 9 frames).
- **ADAPTER**: `control_stream` (command dispatch → injectable `CommandExecutor` callback).
- **OUT OF SCOPE / stub**: `worker_stream` (belongs with the worker subsystem, not the client ws), and the `cascade_add` / `candidate_progress` frames (cascor-specific — drop/stub).

**OQ-11 worker — RESOLVED by evidence: model-agnostic at the pool-infra layer, cascade-bound at the protocol/reduction layer.**
- **GENERIC** (extract now): `workers/{registry,coordinator,audit,metrics,security}` — registration, heartbeat, dispatch/collect, health, mTLS/rate-limit/anomaly, metrics.
- **ADAPTER/DEFER**: the task-payload + `TaskResult` schema (`candidate_data`, `correlation`, `all_correlations`, …) is cascade-specific; `task_distributor` dispatch is generic but the task tuples encode cascade data. ⇒ defer a generic `Task`/`TaskResult` envelope to WS-8 / a 2nd consumer.
- **CASCADE-BOUND** (stays cascor / WS-8): result reduction (correlation-based candidate selection, `CandidateUnit` reconstruction).

**Conclusion.** OUT-11 is a viable, well-bounded extraction — ~70% reusable; the cascor-bound parts are clearly identified and stay subclassed. The §6 build is "extract base, keep cascor subclass," driven by a stub regression model, **deferring the cascade-bound task-envelope to WS-8**. It spans 4 subsystems ⇒ **phase it** (routes+lifecycle base → ws → worker-pool infra), each a PR, each both-stacks-green.

## §6. Build plan (Option 3 — full T2, consumer-priority order)

1. **Routes + lifecycle base** (lowest coupling; WS-6's first need): extract a model-agnostic route set
   (training/status/metrics/dataset/snapshot) + lifecycle (manager/monitor/state_machine) onto the model-core
   interfaces; cascor keeps its subclass. Contract test: stub model drives every route.
2. **WebSocket subsystem**: extract manager + messages + training/control streams onto generic
   `TrainingEvent`/state/metrics frames; contract test drives every channel with the stub model.
3. **Worker subsystem + TaskDistributor**: gated on §5.2. If generic, extract; else cascor-subclassed / defer.
4. **Cross-cutting**: `[tools]` extras pin for the new surface, drift-lint, publish-rail (service-core
   `juniper-service-core-v*` tag → PyPI), and a `test_pyproject_extras`-style contract update in lockstep.

Each step leaves **both stacks green** (cascor unchanged via its subclass; the stub model proves the base).

## §7. Risks & guardrails

| Risk | Guardrail |
|------|-----------|
| RK-4 front-run / over-abstraction (no live consumer) | Foundation-first accepted (D-T2); WS-6 is the near consumer; every step proven by the stub-model contract test, not speculation |
| Hidden cascor coupling bloats the extraction | §5.1 per-module audit *before* building; "extract base, keep cascor subclass" — don't force-generalize cascor-bound bits |
| OQ-11 — worker layer not model-agnostic | §5.2 evidence gate; worker ships subclassed or defers (D-T4) |
| Classification/`argmax` assumptions leak into "generic" routes | Stub is a **regression** model; RK-6 guard via the model-core conformance vocabulary |
| Shared-package churn | service-core already exists (WS-2); T2 is additive; ≥2-consumer bar already met by the template intent |

## §8. Provenance
Scoped from a live read of cascor `origin/main` `api/` (the extraction source) + service-core T1 (the target),
2026-06-19. Dup-guarded (worktrees dir + remote: no in-flight T2 extraction). OUT-11 confirmed greenfield-in-
service-core / extraction-from-cascor. Build is gated on the §5 audit.
