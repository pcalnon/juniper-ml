# Juniper Observability Audit and Outstanding Issues — 2026-05-03

**Project**: Juniper
**File Name**: OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md
**Description**: Tracks observability gaps, errors, and outstanding work items at the
completion of the METRICS-MON program (closed 2026-05-03 via juniper-ml#192). Seeded
with 3 known residuals from the program-close note and extended with comprehensive
audit findings across 8 repos.
**Author**: Paul Calnon
**Version**: 0.1.0
**License**: MIT
**Status**: ACTIVE — receiving audit findings

---

## 1. Purpose

The METRICS-MON program shipped 78 PRs across 8 repos in 9 calendar days, closing
all 5 phases (R1 cardinality / R2 shared-lib / R3 test-coverage / R4 ergonomic /
R5 SLO + dashboards + alerts). The program-close note
([`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md))
recorded 6+ residual follow-ups carried forward.

This document is the **post-program issue tracker**. Its purpose is to:

1. Hold the residuals from the program-close note as actionable, tracked items.
2. Catch issues that the in-flight program execution didn't surface (label drift,
   dead metrics, stale dashboard references, unintentional throttles, race
   conditions, missing tests).
3. Provide a single doc for triage, prioritization, and follow-up sub-track
   sequencing.

Findings are added here as they're discovered. Each item includes severity,
owning repo, blocker/non-blocker classification, and recommended action.

---

## 2. Severity legend

| Severity | Meaning |
|----------|---------|
| **P0** | Production-incident-class — paging surface broken, metric corruption, security exposure |
| **P1** | Operationally meaningful — alerts inert, dashboards wrong, SLI math undermined |
| **P2** | Quality / hygiene — doc/code drift, dead paths, missing tests, hidden tech debt |
| **P3** | Future / aspirational — design discussions, optional improvements, soak-window adjustments |

Each item also carries a status: `open` | `triaged` | `in-progress` | `resolved` | `deferred`.

---

## 3. Seed residuals (from METRICS-MON program-close note)

These three items were explicitly carried forward in the program-close note §6
and need ongoing attention.

### 3.1 SLO catalog target calibration against soak-window data

- **Severity**: P3
- **Status**: open (30-day soak underway)
- **Repo**: juniper-deploy
- **File**: [`notes/SLO_CATALOG_2026-05-03.md`](https://github.com/pcalnon/juniper-deploy/blob/main/notes/SLO_CATALOG_2026-05-03.md) (cross-repo)
- **Background**: The R5.1 SLO catalog deliberately picked conservative
  initial targets (99.5% availability, 99.0% train-job success, sub-millisecond
  latency boundaries from R5.1b) without observed traffic data. Each target is
  marked "initial — to revisit after 30-day soak" in the catalog itself.
- **The work**: At T+30 days from R5.4 alert deployment (2026-06-02), pull
  observed `/metrics` series, compute the 30-day p50/p95/p99 distributions per
  SLI, and either ratify the existing targets or open a calibration PR adjusting
  them based on real data.
- **Cross-cutting**: Calibration changes propagate to R5.4 burn-rate alert
  thresholds (the `(1 - slo_target) * 14.4` factor) and to dashboard panel
  thresholds. A single catalog edit triggers a fan-out PR.
- **Recommended action**: Schedule a `/schedule` agent for 2026-06-02 to review
  observed metrics and open a calibration PR. Decision-blocker: whether 30-day
  data is sufficient signal for targets; some SLIs (train-job success) may need
  60-90 days of soak before they have enough sample volume to ratify.
- **Cross-references**:
  - juniper-deploy#48 (initial catalog)
  - juniper-deploy#49 (SLI 3.4 rename to train-epoch)
  - juniper-deploy#50 (R5.4 burn-rate alerts that depend on these targets)
  - juniper-deploy#51 (catalog §3.3 label fix)

### 3.2 Alertmanager `tickets` receiver placeholder

- **Severity**: P1
- **Status**: open — operational gap
- **Repo**: juniper-deploy
- **File**: [`alertmanager/alertmanager.yml`](https://github.com/pcalnon/juniper-deploy/blob/main/alertmanager/alertmanager.yml) (cross-repo)
- **Background**: The Wave-2 fixup PR (juniper-deploy#51) added routing for
  `severity: page` and `severity: ticket` labels emitted by the R5.4 burn-rate
  alerts. The `tickets` receiver was added as a **placeholder** with no real
  notification config wired (no webhook URL, no email integration, no Slack
  channel). The placeholder is acknowledged in the PR body as "configure before
  production use".
- **The work**: Decide on a ticket sink (likely options: GitHub Issues via webhook,
  PagerDuty low-urgency, Slack low-priority channel, email alias) and wire real
  config into the receiver. Update the placeholder comment in the YAML to point
  at runbook documentation.
- **Operational impact while unresolved**: Slow-burn alerts (the 6× burn-rate
  pairs over 6h windows) currently fire and route to the `tickets` receiver,
  which silently drops them. This means **error-budget consumption that's slow
  enough to ride a 30m+ window goes unobserved by ops**. Fast-burn (page) alerts
  are unaffected — they route to the existing `critical` receiver pattern.
- **Recommended action**: Open a small juniper-deploy PR adding a real receiver
  config. Consider whether `severity: ticket` is the right label or if some
  alerts should be re-classified as `severity: critical` until the ticket flow
  is real.
- **Cross-references**:
  - juniper-deploy#51 (placeholder added)
  - juniper-deploy#50 (R5.4 alerts that emit these labels)

### 3.3 TRAIN-ARCH-01 cascor mini-batch restoration

- **Severity**: P3
- **Status**: deferred (user explicitly paused at design-doc stage)
- **Repo**: juniper-cascor
- **Design doc**: [`juniper-cascor#194`](https://github.com/pcalnon/juniper-cascor/pull/194) (`notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md`)
- **Background**: While drafting metrics-instrumentation work in Wave 2, the
  R5.4-pre agent discovered cascor is **full-batch end-to-end** —
  `cascade_correlation.py:1638` and `candidate_unit.py:564` use
  `for epoch in range(epochs):` with one full-tensor forward + backward + step.
  No `DataLoader`, no mini-batch idioms anywhere. The user initially framed this
  as a regression; the design doc agent's git archaeology proved it was an
  **absence, not a regression** (initial commit `2076d21` was already full-batch;
  every legacy variant in `juniper-legacy/` matches).
- **Two key constraints** captured in the design doc:
  1. **Cascade-correlation algorithmically requires full-batch for the candidate
     phase** — `_calculate_correlation` (`candidate_unit.py:878-950`) computes
     Pearson via `output.mean()` / `error.mean()` as population statistics; mini-
     batching produces biased (wrong-direction) gradient estimators.
  2. **Output-trainer mini-batching is feasible** — the design proposes
     `use_mini_batch: bool = True` and `mini_batch_size: int = 256` knobs
     (constants-backed) restricted to the output-trainer; candidate phase keeps
     full-batch.
- **The work** (when un-deferred): A 3-4 PR sub-track (constants → config → output
  trainer + tests → optional convergence-equivalence test). Open questions Q1
  (default-flip timing), Q4 (per-epoch vs per-step metrics emit), Q5 (auto-scale
  `output_epochs` when mini-batch enabled) require user resolution before the
  sub-track entry plan is written.
- **Cross-cutting**: Q4 in particular intersects with the R5.6 throttle-removal
  work (also deferred) — the 25-epoch throttle becomes inadequate for sub-epoch
  step granularity. Sequencing matters.
- **Recommended action**: Pure user-discretion item. Do not pre-empt; surface in
  next observability planning meeting as input for a possible TRAIN-ARCH program.
- **Cross-references**:
  - juniper-cascor#194 (design doc, OPEN, deferred)
  - juniper-ml#189 (parallel mini-batch metrics design doc that surfaced the
    underlying gap)
  - juniper-cascor#188 (R5.4-pre — the work that triggered the discovery)

---

## 4. Comprehensive audit findings (2026-05-03)

This section receives findings from the 5-dimension audit launched against the
post-METRICS-MON codebase. Each dimension is audited by a focused agent;
findings are added here in dedicated subsections.

> **Status**: audit in progress at the time of this doc's first commit.
> Subsequent commits append findings as agents return.

### 4.1 Dimension A — Metrics surface integrity

**Scope**: Verify all metrics referenced in the R5.1 SLO catalog, `alert_rules.yml`,
and the 4 Grafana dashboards are actually exposed on `/metrics` in their
respective services. Find dead-defined metrics. Verify cardinality discipline.
Catch label-name drift.

#### 4.1.0 HEADLINE FINDING — observability scaffolding outpaced production wiring

> **The METRICS-MON program shipped metric definitions, dashboards, alerts, and
> SLO catalog entries without validating that the underlying metrics are
> actually emitted by production code.**
>
> The pre-program observability surface (the `_ensure_*_metrics()` family in
> `juniper-cascor/src/api/observability.py`, plus several juniper-canopy WS
> metrics) was never wired to production call sites. The program then added
> dashboards and alerts referencing these dead metrics, and the R5.1 SLO catalog
> bound 2 user-supporting SLIs (§4.3, §4.4) to 2 of them. Result: ≥8 dashboard
> panels show flat zeros, ≥3 alerts cannot fire, and 2 SLO calculations are
> uncomputable. R5.4-pre's NEW metrics (`training_sessions_completed_total`,
> `training_step_duration_seconds`, `worker_*` bridge gauges) ARE wired and ARE
> the only production-binding emission sites in cascor.
>
> Severity classification of this finding cluster: **P1** (operationally
> meaningful — paging surfaces broken, dashboards mislead operators).

#### 4.1.1 SLO catalog SLI binding

| SLI | Metric | Status |
|-----|--------|--------|
| 3.1 Canopy availability | `juniper_canopy_http_requests_total` | EXPOSED (shared `PrometheusMiddleware`) |
| 3.2 Canopy render p95 | `juniper_canopy_http_request_duration_seconds_bucket` | EXPOSED |
| 3.3 Cascor train-job success | `juniper_cascor_training_sessions_completed_total{status}` | EXPOSED (R5.4-pre wired at `lifecycle/manager.py:1372/1379/1388`) |
| 3.4 Cascor train-epoch p95 | `juniper_cascor_training_step_duration_seconds_bucket` | EXPOSED (single emission site at `manager.py:1328`) |
| 3.5 Data POST availability | `juniper_data_dataset_post_total{cache, status}` | EXPOSED |
| 4.1 Worker heartbeat freshness | `juniper_cascor_worker_heartbeat_age_seconds` | **EXPOSED but catalog has prose drift** — catalog §4.1 names `juniper_cascor_worker_last_heartbeat_age_seconds`; alert rule + code use the as-shipped name |
| 4.2 Pending-task queue | `juniper_cascor_pending_tasks` | NOT-FOUND (catalog self-flags; alert guarded by `absent_over_time(...)==0`) |
| **4.3 Broadcast fan-out p95** | `cascor_ws_broadcast_send_duration_seconds` | **DEFINED-NOT-EMITTED — SLI uncomputable** |
| **4.4 Command-handler p95** | `cascor_ws_command_handler_seconds` | **DEFINED-NOT-EMITTED — SLI uncomputable** |
| 4.5 Data-client p95 | `juniper_canopy_data_client_request_duration_ms` | EXPOSED (R4.3 hook) |
| 4.6 Data-client error rate | `juniper_canopy_data_client_requests_total{status_class}` | EXPOSED |
| 4.7 Cache-hit ratio | `juniper_data_dataset_post_total{cache}` | EXPOSED |
| 4.8 HTTP 5xx per service | `juniper_*_http_requests_total{status=~"5.."}` | EXPOSED |

#### 4.1.2 Dead-defined metrics inventory

| ID | Metric | Repo | Severity | Catalog/alert/dashboard ref? |
|----|--------|------|----------|------------------------------|
| A.1 | `juniper_cascor_training_sessions_active` | cascor | **P1** | 3 alerts gate on `>0`; permanently inert |
| A.2a | `juniper_cascor_training_loss` | cascor | **P1** | `TrainingLossNotDecreasing` alert; cascor dashboard panel |
| A.2b | `juniper_cascor_training_epochs_total` | cascor | **P1** | dashboard panel |
| A.2c | `juniper_cascor_candidate_correlation` | cascor | **P1** | `LowCandidateCorrelation` alert; dashboard panel |
| A.2d | `juniper_cascor_training_accuracy_ratio` | cascor | P2 | dashboard panel |
| A.2e | `juniper_cascor_hidden_units_total` | cascor | P2 | dashboard panel |
| A.3a | `cascor_ws_broadcast_send_duration_seconds` | cascor | **P1** | catalog SLI 4.3 |
| A.3b | `cascor_ws_command_handler_seconds` | cascor | **P1** | catalog SLI 4.4 |
| A.4 | `juniper_canopy_websocket_connections_active` | canopy | **P1** | `NoWebSocketConnections` alert; dashboard panel |
| A.5a | `juniper_cascor_inference_requests_total` | cascor | P2 | 1 dashboard panel |
| A.5b | `juniper_cascor_inference_duration_seconds` | cascor | P2 | 3 dashboard panels |
| A.9 | 12+ cascor `cascor_ws_*` metrics (full list in dim-E E-01) | cascor | P3 | none currently |
| (canopy) | `juniper_canopy_websocket_messages_total` | canopy | P2 | dashboard panel |

#### 4.1.3 Other dimension-A findings

- **A.6 (P2)**: `juniper_cascor_training_step_duration_seconds` is observed
  with `phase="output"` ONLY (`manager.py:1328` hard-codes the label). Catalog
  §3.4 SLI PromQL filters `phase=~"input|candidate|output"`; in practice the
  regex matches only `output`. Either drop the `phase` label (effectively
  constant) or add input/candidate emission sites.
- **A.7 (P3)**: SLO catalog §4.1 prose drift — `last_heartbeat_age_seconds` →
  `heartbeat_age_seconds`. Doc-only fix.
- **A.8 (P3)**: `juniper_canopy_data_client_requests_total{error_type}` lacks
  closed-set validation at the emission site. If juniper-data-client adds a
  new exception class, the label silently expands. Mirror the cascor
  `_TRAINING_SESSION_STATUSES` pattern with `_KNOWN_ERROR_TYPES` frozenset.

#### 4.1.4 Cardinality discipline

No P0/P1 cardinality leakage found. Closed-set labels (`status_class`, `cache`,
`status`) are correctly enforced where `frozenset` validation is wired. The
`endpoint` label uses route-template collapse (not raw URL), preventing the
classic cardinality blow-up. `worker_id` cardinality grows with worker fleet
lifetime — already tracked as catalog §6 Q3.

### 4.2 Dimension B — PromQL + scrape correctness

**Scope**: Verify alert/dashboard/scrape configs are technically correct.

**Result: clean.** No high-severity findings. R5.4 burn-rate math is
mathematically correct (14.4× / 6× factors per SRE Workbook); all 65 dashboard
expressions parse via promtool; scrape configs and ServiceMonitor manifests
align between docker-compose and k8s deployments; `pending_tasks`
`absent_over_time(...)==0` guard works.

| ID | Severity | Title | Recommended action |
|----|----------|-------|--------------------|
| B.1 | P3 | `severity: warning` and `severity: info` alerts (pre-R5.4 R-series) have no alertmanager route — fall through to unconfigured `default` receiver | Either add a `warning → tickets` route or document explicitly that pre-R5.4 R-series alerts are intentionally non-paging. (Separate from the §3.2 `tickets` placeholder.) |
| B.2 | info | Grafana panel JSONs have `id: null` (auto-assigned at import) | None; cite by `title:` in audits |

### 4.3 Dimension C — Shared lib + WS schema + middleware

**Scope**: Verify R2.1 lib adoption, R2.2 WS schema alignment, R4.6
request-id propagation, and middleware boundary placement.

**Lib home**: `juniper-ml/juniper-observability/` (sub-package within
juniper-ml repo); current version `0.1.1`.

**Adoption matrix**: 3 of 4 server consumers declare and import the lib in
production. juniper-cascor-worker correctly opts out (no HTTP).

**WS frame schema**: Single source at
`juniper-cascor/juniper-cascor-protocol/juniper_cascor_protocol/worker/messages.py:12`
(`WorkerMessageType(StrEnum)`). Both cascor server and cascor-worker import
from this shared package. **No drift.**

**R4.6 request-id propagation**: Correctly implemented and well-tested in
juniper-data-client `_request()`. Caller-supplied headers win; ImportError +
LookupError caught silently; `[observability]` extra in pyproject.toml.

**MetricsAuthMiddleware confinement (Q5 decision)**: juniper-data only —
verified. Test guard at `juniper-data/tests/unit/test_observability.py:67`
asserts module ownership.

| ID | Severity | Repo | Title | Recommended action |
|----|----------|------|-------|--------------------|
| C.1 | **P2** | juniper-canopy | `RequestIdMiddleware` is INNER, not outer. `PrometheusMiddleware` added AFTER at `src/main.py:312` runs OUTER per starlette LIFO. Metrics emit before request-id contextvar is set. | Swap order: add `PrometheusMiddleware` first, then `RequestIdMiddleware` last so request-id is the outermost wrapper. Match the data/cascor pattern. |
| C.2 | P3 | juniper-data | Looser observability dep floor (`>=0.1.0a0` vs others' `>=0.1.1`) | Bump `juniper-data/pyproject.toml:59` to `>=0.1.1` |
| C.3 | P3 | juniper-cascor-worker | Worker does NOT read `request_id` from inbound WS frames | Likely intentional (R4.6 was HTTP-only); confirm and either (a) close as design-by-decision or (b) extend the protocol if WS-level correlation is desired |

### 4.4 Dimension D — Buckets + test coverage

**Scope**: Bucket→SLO alignment, R5.1b coverage of the 2 non-re-bucketed
cascor histograms, test-coverage matrix verification.

**Bucket alignment**: 6 of 7 production histograms have appropriate bucket
layouts for their documented SLO targets. One TIGHT case below.

**HELP-string marker state**: All correct — broadcast_send + command_handler
have marker REMOVED (R5.1b); the 2 non-re-bucketed cascor histograms
(`cascor_inference_duration_seconds`, `cascor_ws_resume_replayed_events`) plus
the 3 non-cascor histograms still have marker PRESENT.

**Catalog §3.2 binds a histogram NOT in R4.1's "6 production histograms"
inventory**: `juniper_canopy_http_request_duration_seconds` (Starlette shared
middleware) is the actual SLI source for canopy render p95, not
`canopy_ws_browser_latency_ms`. The R4.1 inventory undercounted.

| ID | Severity | Repo | Title | Recommended action |
|----|----------|------|-------|--------------------|
| D.1 | **P2** | juniper-canopy | `canopy_ws_browser_latency_ms` + `canopy_ws_browser_errors_total` lack ANY unit test | Add a unit test exercising emission via the `WsLatencyReport` ingest path; assert label `endpoint` and `_upper_bounds` |
| D.2 | P2 | juniper-cascor | `command_handler_seconds` SLO target (50ms) sits one bucket below `+inf` cap (100ms) — TIGHT headroom for breach detection | Add `0.025` and `0.2` boundaries OR document the trade-off as accepted (per rationale doc §5.2) |
| D.3 | P3 | juniper-data | `dataset_generation_duration_seconds` lacks `_upper_bounds` boundary-pin test | Add assertion mirroring the cascor R5.4-pre pattern |
| D.4 | P3 | juniper-canopy | `data_client_request_duration_ms` lacks `_upper_bounds` boundary-pin test | Same as D.3 pattern |
| D.5 | P3 | juniper-cascor | `cascor_inference_duration_seconds` + `cascor_ws_resume_replayed_events` lack bucket-boundary tests | Acceptable while R4.1-tentative; add at R5.1c ratification |

### 4.5 Dimension E — Throttles + tech debt + race conditions

**Scope**: Find hidden throttles beyond the known `cascade_correlation.py:1655`,
dead paths, race conditions, memory-leak risks.

**Throttles**: Only the known 25-epoch throttle gates `prometheus_client`
emission. Two other `% N == 0` patterns exist (`candidate_unit.py:615` for WS
progress, `control_security.py:128` for cleanup) but neither gates metrics. No
hidden Prometheus emission throttles.

**Dead paths**: Confirmed Dim A's finding (cascor `observability.py` has 18+
helpers with zero production callers).

**TODO/FIXME/HACK**: 3 empty `# TODO :` banner placeholders in canopy frontend
components — cosmetic, no actionable items.

| ID | Severity | Repo | Title | Recommended action |
|----|----------|------|-------|--------------------|
| E.1 | **P2** | juniper-cascor | Lazy-init race in `_ensure_training_metrics` / `_ensure_ws_metrics` (`observability.py:196,436`) — concurrent first-callers can orphan a collector via the `_register_or_reuse` recovery path | Wrap dict-init in module-level `threading.Lock` or use `functools.lru_cache(maxsize=1)`. Cold-start window only — rare but real |
| E.2 | P3 | juniper-cascor | `WorkerRegistryCollector.collect()` reads `recent_task_durations_seconds` outside registry lock (`workers/metrics.py:174`); under free-threading (3.13t/3.14t) `list(deque)` torn-read possible | Snapshot per-worker fields under `self._registry._lock`, or expose a registry method `snapshot_for_metrics()` that does |
| E.3 | P3 | juniper-canopy | Legacy `TrainingMetricsComponent` (`frontend/components/training_metrics.py:43`) self-marked "will be removed in a future release"; only test references it | Delete or remove the deprecation comment |
| E.4 | P3 | juniper-cascor | Stale `.ipynb_checkpoints/cascade_correlation-checkpoint.py` shipped in `src/` | Add `.ipynb_checkpoints/` to `.gitignore`; remove |
| E.5 | P3 | juniper-canopy | 3 empty `# TODO :` banner comments in metrics components | Cosmetic — fill or remove |
| E.6 | P3 | juniper-cascor | No `WorkerRegistry` size cap (`workers/registry.py:137`) | Document expected max worker count or add a cap |

**Worker-bridge memory-leak risk**: NONE found at the cascor side —
`WorkerCoordinator._health_monitor_loop` correctly prunes stale workers; the
collector only emits gauges for currently-registered workers. Prometheus TSDB
would still hold stale `worker_id` series until its `staleness_marker` window
elapses (~5min) — that's a Prometheus design property, not a cascor bug.

---

## 5. Consolidated action items

Sorted by severity. Each row maps a finding to a recommended PR / sub-track /
decision. The §3 seed items appear at the top by ID; §4 audit findings follow
within each severity tier.

### P1 — Operationally meaningful (alerts inert, dashboards wrong, SLI math broken)

| ID | Repo | Title | Recommended action |
|----|------|-------|--------------------|
| **3.2** | juniper-deploy | Alertmanager `tickets` receiver is a placeholder | Open small PR wiring real notification config (webhook/email/Slack); decide which severity owns "ticket" semantics |
| **A.1** | juniper-cascor | `juniper_cascor_training_sessions_active` Gauge has no production emit site → `TrainingStalled`/`TrainingLossNotDecreasing`/`LowCandidateCorrelation` alerts permanently inert | Wire `inc_training_sessions()`/`dec_training_sessions()` from `lifecycle/manager.py` around session start/end |
| **A.2** | juniper-cascor | 5 cascor training metrics dead (`training_loss`, `training_epochs_total`, `candidate_correlation`, `training_accuracy_ratio`, `hidden_units_total`) → 5 dashboard panels show flat zeros + 2 alerts inert | Either (a) wire from cascade-correlation training loop alongside existing checkpointing/logging hooks, or (b) remove the metric definitions, dashboard panels, and alert rules |
| **A.3** | juniper-cascor | SLO catalog §4.3 + §4.4 reference `cascor_ws_broadcast_send_duration_seconds` + `cascor_ws_command_handler_seconds`; **no production code observes either** → catalog SLIs uncomputable | Wire `ws_observe_command_handler` around WS dispatch path; add `broadcast_send_duration_seconds.observe()` site around per-connection `await ws.send(...)` in the broadcast loop |
| **A.4** | juniper-canopy | `juniper_canopy_websocket_connections_active` dead → `NoWebSocketConnections` alert + dashboard panel both broken | Either wire `set_websocket_connections_active(channel, count)` from canopy's WS lifecycle, or drop the metric and adjust the alert + panel |

### P2 — Quality / correctness (real but lower-impact)

| ID | Repo | Title | Recommended action |
|----|------|-------|--------------------|
| **A.5** | juniper-cascor | `juniper_cascor_inference_*` (counter + histogram) dead → 4 dashboard panels show flat zeros | Wire `record_inference()` if cascor exposes an inference HTTP route; otherwise remove from observability.py and dashboard |
| **A.6** | juniper-cascor | `juniper_cascor_training_step_duration_seconds` only ever observed with `phase="output"` despite catalog SLI filtering `phase=~"input\|candidate\|output"` | Either drop the `phase` label (effectively constant) or add input/candidate emission sites |
| **C.1** | juniper-canopy | `RequestIdMiddleware` is INNER, not outer — metrics emit before request-id contextvar is set | Swap middleware-add order in `src/main.py` to make RequestIdMiddleware outermost |
| **D.1** | juniper-canopy | `canopy_ws_browser_latency_ms` + `canopy_ws_browser_errors_total` lack any unit test | Add unit test exercising emission via `WsLatencyReport` ingest path; assert label `endpoint` and `_upper_bounds` |
| **D.2** | juniper-cascor | `command_handler_seconds` SLO target (50 ms) sits one bucket below `+inf` cap — limited breach-detection precision | Add `0.025` and `0.2` boundaries when R5.1c lands, or document the trade-off as accepted |
| **E.1** | juniper-cascor | Lazy-init race in `_ensure_training_metrics` / `_ensure_ws_metrics` can orphan a collector under concurrent first-touch | Wrap dict-init in module-level `threading.Lock` or use `functools.lru_cache(maxsize=1)` |

### P3 — Hygiene / future / aspirational

| ID | Repo | Title | Recommended action |
|----|------|-------|--------------------|
| **3.1** | juniper-deploy | SLO catalog calibration vs soak-window data | Schedule T+30d agent for 2026-06-02; open calibration PR if observed data warrants |
| **3.3** | juniper-cascor | TRAIN-ARCH-01 mini-batch restoration deferred | User-discretion; design doc juniper-cascor#194 captures findings |
| **A.7** | juniper-deploy | SLO catalog §4.1 metric-name prose drift (`last_heartbeat_age_seconds` → `heartbeat_age_seconds`) | Doc-only fix to align catalog with as-shipped metric |
| **A.8** | juniper-canopy | `data_client_requests_total{error_type}` lacks closed-set validation at emission site | Add `_KNOWN_ERROR_TYPES` frozenset check mirroring cascor `_TRAINING_SESSION_STATUSES` pattern |
| **A.9** | juniper-cascor | 12+ cascor `cascor_ws_*` metrics dead (no SLI/alert/dashboard ref currently, but defined and shipping in the metric surface) | Either wire from WS broadcast/dispatch paths, or remove from `observability.py` |
| **B.1** | juniper-deploy | `severity: warning` and `severity: info` (pre-R5.4 R-series alerts) have no alertmanager route → fall through to unconfigured `default` receiver | Add `warning → tickets` route OR document explicitly that R-series alerts are intentionally non-paging |
| **C.2** | juniper-data | Looser observability dep floor (`>=0.1.0a0` vs others' `>=0.1.1`) | Bump `juniper-data/pyproject.toml:59` to `>=0.1.1` |
| **C.3** | juniper-cascor-worker | Worker doesn't read `request_id` from inbound WS frames | Likely intentional (R4.6 was HTTP-only); confirm and close as design-by-decision OR extend protocol |
| **D.3** | juniper-data | `dataset_generation_duration_seconds` lacks `_upper_bounds` boundary-pin test | Add assertion mirroring cascor R5.4-pre pattern |
| **D.4** | juniper-canopy | `data_client_request_duration_ms` lacks `_upper_bounds` boundary-pin test | Same as D.3 pattern |
| **D.5** | juniper-cascor | `cascor_inference_duration_seconds` + `cascor_ws_resume_replayed_events` lack bucket-boundary tests | Acceptable while R4.1-tentative; add at R5.1c ratification time |
| **E.2** | juniper-cascor | `WorkerRegistryCollector.collect()` reads worker fields outside registry lock → torn-read risk under free-threading | Snapshot per-worker fields under `self._registry._lock` or expose a `snapshot_for_metrics()` method |
| **E.3** | juniper-canopy | Legacy `TrainingMetricsComponent` (test-only callers, self-marked deprecated) | Delete or remove deprecation comment |
| **E.4** | juniper-cascor | Stale `.ipynb_checkpoints/cascade_correlation-checkpoint.py` in `src/` | Add `.ipynb_checkpoints/` to `.gitignore`; remove the file |
| **E.5** | juniper-canopy | 3 empty `# TODO :` banner comments in metrics components | Cosmetic — fill or remove |
| **E.6** | juniper-cascor | No `WorkerRegistry` size cap | Document expected max worker count or add a cap |

### Tally by severity

| Tier | Count |
|------|-------|
| P1 | **6** (1 seed + 5 audit — all in cascor/canopy/deploy) |
| P2 | **6** |
| P3 | **15** |
| **Total** | **27** |

### Severity-1 cluster headline

5 of the 6 P1 audit items are in **juniper-cascor** and reflect the same root
cause: the pre-METRICS-MON observability scaffolding in
`juniper-cascor/src/api/observability.py` was never wired to production code.
The METRICS-MON program inherited this surface, added dashboards/alerts/SLO
references, and shipped them without verifying production emission. A focused
"observability scaffolding wire-up" sub-track (proposed name **OBS-WIRE-01**)
addressing A.1–A.4 + A.5–A.6 in one juniper-cascor PR would close 7 of 27
findings (~26%) in a single shot.

The 6th P1 (3.2 alertmanager `tickets` receiver) is independent and is a single
small juniper-deploy PR.

---

## 6. References

### Primary

- [`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`](METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md) — program-close note (PR juniper-ml#192)
- [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) — full program tracker (CLOSED 2026-05-03)
- juniper-deploy `notes/SLO_CATALOG_2026-05-03.md` (cross-repo) — SLI/SLO authority
- juniper-deploy `prometheus/alert_rules.yml` (cross-repo) — alert authority
- juniper-deploy `alertmanager/alertmanager.yml` (cross-repo) — routing authority
- juniper-cascor `notes/training/MINI_BATCH_RESTORATION_DESIGN_2026-05-03.md` (cross-repo) — TRAIN-ARCH-01 design

### Per-phase entry plans

- [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md)
- [`METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md`](METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md)
- [`METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`](METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md)

### Design docs

- [`METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`](METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md)
- [`METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md`](METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md)
- [`METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md)
- [`METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md`](METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md)
- [`METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md`](METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md)

---

_End of seed. Audit findings appended in subsequent commits on the same branch._
