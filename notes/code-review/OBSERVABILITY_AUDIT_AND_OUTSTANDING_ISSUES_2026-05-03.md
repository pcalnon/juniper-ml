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
respective services. Find dead-defined metrics (registered but never emitted).
Verify cardinality discipline (closed-set labels, no unbounded label values).
Catch label-name drift between docs and code (the SLO 3.3 `outcome → status`
case caught by the R5.4 fixup is the canonical example).

_Findings to be added once audit completes._

### 4.2 Dimension B — PromQL + scrape correctness

**Scope**: Verify every `expr:` in `alert_rules.yml` and every dashboard panel's
PromQL parses cleanly and references real metrics. Verify the burn-rate math
factors are correct (Google SRE Workbook recipe). Check `prometheus.yml`
relabeling and `metric_relabel_configs` don't drop metrics needed by alerts.
Look for stale references to renamed/removed metrics.

_Findings to be added once audit completes._

### 4.3 Dimension C — Shared lib + WS schema + middleware

**Scope**: Verify the R2.1 `juniper-observability` lib is actually adopted by all
consumer servers (not just imported). Confirm the R2.2 WS frame schema alignment
between cascor server and cascor-worker still holds post-program. Verify
`RequestIdMiddleware` is applied at every expected service boundary. Confirm
`MetricsAuthMiddleware` confinement matches the R5.2 Q5 decision (juniper-data
only). Verify the R4.6 request-id propagation hook in juniper-data-client
actually fires under `juniper_observability.request_id_var` set state.

_Findings to be added once audit completes._

### 4.4 Dimension D — Buckets + test coverage

**Scope**: Verify R4.1 histogram bucket choices align with the documented SLO
targets in the R5.1 catalog. Check the 2 cascor histograms NOT re-bucketed by
R5.1b (the ones R5.1b explicitly skipped per the rationale doc) — are they still
using inappropriate defaults? Spot-check the test-coverage matrix as claimed in
the program-close note against actual test files; flag any metrics with no
covering tests.

_Findings to be added once audit completes._

### 4.5 Dimension E — Throttles + tech debt + race conditions

**Scope**: The known 25-epoch throttle in `cascade_correlation.py:1655` was caught
by the R5.4 fixup. Are there other emit throttles like it? Find dead/unused
observability code paths post-program. Locate `TODO`/`FIXME`/`HACK` comments in
metrics-related code. Audit the worker-bridge collector (`juniper-cascor/src/api/workers/metrics.py`)
and concurrent metric recording paths for race conditions. Check the worker-bridge
collector for memory-leak risk under churn (workers joining/leaving
the registry).

_Findings to be added once audit completes._

---

## 5. Consolidated action items

_Populated after §4 findings are integrated. Each row maps a finding to a
recommended PR / sub-track / decision._

| ID | Severity | Repo(s) | Title | Status | Recommended action |
|----|----------|---------|-------|--------|--------------------|
| 3.1 | P3 | juniper-deploy | SLO calibration | open | Schedule T+30d agent |
| 3.2 | P1 | juniper-deploy | `tickets` receiver placeholder | open | Small PR wiring real notification |
| 3.3 | P3 | juniper-cascor | TRAIN-ARCH-01 deferred | deferred | User-discretion |

_Audit findings appended below as they integrate._

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
