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
> service template is missing. **OUT-11** in [`JUNIPER_2026-06-17_JUNIPER-ECOSYSTEM_PLATFORM-ENVIRONMENT-STATE-AND-ROADMAP.md`](JUNIPER_2026-06-17_JUNIPER-ECOSYSTEM_PLATFORM-ENVIRONMENT-STATE-AND-ROADMAP.md);
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

## §9. As-built status & deferred follow-ups (updated 2026-06-21; steps 2 + 3a + 3b appended)

**As-built.** Step 1 grew in scope and was split into three PRs; step 2 (the WebSocket subsystem)
and step 3 (the worker subsystem, itself split 3a/3b) follow. All merged to `main` except step 3b
(open PR):

| Step | PR | Delivered |
|------|----|-----------|
| 1a | #473 | `ServiceLifecycleManager` (threaded orchestrator + cooperative pause/stop) + `LifecycleStateMachine` (open-string phase) + `LifecycleMonitor` (`TrainingEvent` accumulator) + generic `/v1/{training,metrics,dataset,network}` routes + `ResponseEnvelope` |
| 1b | #476 | Snapshot persistence — `SnapshotStore` (injected model-core `ModelSerializer` + JSON sidecar) + manager `save`/`list`/`get`/`load`(→`INVESTIGATING`)/`restore_for_retrain`(→`STOPPED`)/`resume_from_snapshot`(→`RESUME_READY`) + `/v1/snapshots` routes |
| 1c | #478 | Snapshot replay — `ReplaySession` (timed playback; play/pause/seek/speed/range/stop) + manager `start_replay`(→`REPLAYING`)/`replay_control`/`stop_replay`/`get_replay_state` + `/v1/snapshots/{id}/replay[/control]` |
| 2 | #484 | WebSocket subsystem (`juniper_service_core.websocket`) — `WebSocketManager` (seq / replay-buffer / oversized-message chunking / thread-safe broadcast, `api.observability` emissions dropped) + plain-dict message builders (the generic 7 frames; `cascade_add` / `candidate_progress` dropped) + control-path security (`validate_control_origin` / `LeakyBucket` / `HandshakeCooldown`) + `training_stream` / `control_stream` handlers + an **injectable `CommandExecutor`** (control-dispatch adapter; default `LifecycleCommandExecutor`) + `build_websocket_router` (`/ws/training` + `/ws/control`) + `attach_websocket` broadcast bridge. Live-training **and** replay frames push via a new additive manager `frame_sink` (resolves **FW-3**). `worker_stream` deferred to step 3. 25-test both-stacks-green contract drives every channel with the regression stub (RK-6); cascor untouched |

| 3a | #492 | Worker-pool foundations (`juniper_service_core.workers`) — the GENERIC pool-infra layer the OQ-11 audit cleared: `WorkerRegistry` / `WorkerRegistration` / `WorkerRegistryFullError` (registration, heartbeat, health-score, idle/stale queries, capacity cap) + security primitives (`TLSConfig` mTLS, `ConnectionRateLimiter` token-bucket, `AnomalyDetector` generalized from cascade `correlation` → a generic bounded quality `score`) + audit (`AuditLogger` + `WorkerMetrics` + `AuditEventType`) + `WorkerRegistryCollector` (Prometheus bridge; `juniper_cascor_worker_` prefix → configurable `metric_prefix`, pending-tasks via an injected callable, no coordinator import). De-cascored: `api.observability` emissions dropped, `cascor_constants` → local consts, loggers renamed. Lazy-exported (stdlib-only; dependency-free import preserved). 17-unit-test pool-infra coverage (RK-6 stub-free); cascor untouched |

| 3b | #496 | Worker coordinator + `/ws/workers` stream. `WorkerCoordinator` (`juniper_service_core.workers.coordinator`, stdlib-only): generic idle-worker assignment, per-task timeout/retry, result collection (+ worker-liveness early-exit), `pending_tasks_count` (wired into 3a's `WorkerRegistryCollector`), and the background health monitor — with the two cascade-bound operations injected behind a `WorkerTaskProtocol` seam (the step-2 `CommandExecutor` analogue): `build_assignment(task)→(msg, frames)` + `parse_result(worker_id, msg, frames)→ParsedResult\|None` (+ `result_attachments` to drive binary-frame receipt). Anomaly detection runs over 3a's generic `score` (not `correlation`). **Result reduction stays consumer-side** — `collect_results` returns the raw list and the consumer reduces (cascor's `TaskDistributor`), so no reducer hook is added (faithful to OQ-11; avoids RK-4 dead surface). Generic `/ws/workers` handler (`juniper_service_core.websocket.worker_stream`): origin-reject / `X-API-Key` auth / per-source rate-limit / registration handshake (server-assigned id, untrusted `client_name`) / heartbeat + enriched-field forwarding / dispatch + binary-frame transport, with `attach_worker_pool` app-wiring + `build_worker_router` (default `/ws/workers`, `path=` for cascor's `/ws/v1/workers`); `"worker"` added to `DEFAULT_WS_ENDPOINTS`. Cascade-bound `protocol.py` (`Task`/`TaskResult` envelope + numpy `BinaryFrame`) + `task_distributor` reduction stay deferred to **WS-8** / cascor. Lazy-exported (dependency-free top-level import preserved). 36-test both-stacks-green contract drives register→heartbeat→dispatch→collect→timeout (+ transport edge paths) with a trivial protocol (RK-6); full suite **185 green** (≥80% coverage gate held — `worker_stream` 94%, `router` 100%); cascor untouched |

**Step 3 split** (scope grew, mirroring step 1's 1a/1b/1c): **3a** ships the four clean pool-infra foundation modules. **3b** (this PR) extracts the `WorkerCoordinator` — task dispatch/collect/timeout/retry over an **injectable task-protocol seam** (`build_assignment` + `parse_result`, the analogue of step 2's `CommandExecutor`) — plus the `/ws/workers` stream handler (adding a `"worker"` endpoint bucket to the websocket manager). As-built refinement: the seam is encode/parse only; **result reduction is left to the consumer** (cascor's `TaskDistributor` reduces the `collect_results` list), faithful to the cascor source where the coordinator never reduces — so no `reduce_results` hook was added. The cascade-bound `Task`/`TaskResult` envelope (`protocol.py`: `candidate_data` / `correlation` / …) + correlation-based result reduction stay deferred to **WS-8** / cascor-side per OQ-11.

Step **4** (publish-rail + `[tools]` drift-lint) remains.

**Deferred follow-ups (future work):**

- **FW-1 — Generic dataset-swap-history.** cascor's `get_snapshot_dataset_swaps` /
  `/snapshots/{id}/history/dataset_swaps` reads **live-dataset-swap** events from a snapshot — its
  P2 live-swap feature. The generic service-core base has no live-swap concept, so a generic snapshot
  carries no swap events; this is **kept cascor-only for now**. *Future work:* once a second service
  needs a live-dataset-swap (or a generic "dataset-change log"), generalize a `DatasetEvent` log on the
  lifecycle, capture it in the snapshot sidecar (mirroring how metric history already is), and expose a
  generic `/v1/snapshots/{id}/history/…` route. Until a real second consumer exists it stays
  cascor-subclassed (RK-4: don't force-generalize a single-consumer feature).
- **FW-2 — Replay history-continuation.** On `resume_from_snapshot` → `RESUME_READY`, the generic base
  reloads the model (weights preserved) but a subsequent `start` begins a *fresh* metric history rather
  than appending from `resume_point_epoch` (cascor appends). Genericizing continuation (the monitor seeds
  from the restored history instead of clearing on `training_start`) is deferred.
- **FW-3 — Replay live push. RESOLVED (step 2, #484).** Replay frames now push live: the manager's
  `frame_sink` is passed to `ReplaySession.on_frame`, and the step-2 `attach_websocket` bridge routes
  it (alongside live-training metrics/state frames) to the `/ws/training` broadcast. Without a wired
  transport the sink is a no-op and only the pollable replay state advances — the step-1c behavior is
  preserved.
- **FW-4 — cascor topology-evolution + per-sample-weight replay (CAN-015g).** Cascade-specific; stays
  cascor-side.
