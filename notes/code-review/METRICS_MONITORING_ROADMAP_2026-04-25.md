# Juniper Metrics & Monitoring — Development Roadmap

**Status:** PROPOSED (consumes findings produced by the review plan)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-25
**Scope:** Metrics, monitoring, observability, telemetry, health surface
**Repos in scope (6):** juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client
**Companion documents:**

- [METRICS_MONITORING_ANALYSIS_2026-04-25.md](METRICS_MONITORING_ANALYSIS_2026-04-25.md) — current-state baseline
- [METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) — review methodology

---

## 1. Purpose

This roadmap turns the review's **findings** (METRICS-MON-NNN) into a **prioritized, sequenced, owner-attributable** body of work. The roadmap is consumed by the implementation phase that follows the review; it is not the review itself.

The roadmap exists so that, once the review is signed off, work can be picked up in order without re-arguing priority, scope, or sequencing.

---

## 2. Sequencing principles

1. **Composite severity first.** Composite ≥ 4 findings (per §4 of the review plan) are release-blocking and lead the queue.
2. **Architectural before logical before cosmetic.** When two findings have equal severity, the architectural one ships first to prevent rework.
3. **Cross-repo before single-repo.** Shared remediations that eliminate duplicated bugs ship before single-repo fixes that would otherwise drift.
4. **Upstream before downstream.** Cascor (server) before cascor-client/worker (consumers); data before data-client; canopy is consumer-side and ships last in any cluster it depends on.
5. **Tests pinned to the same PR.** No fix merges without the test that prevents regression.
6. **Each phase ends green.** Every repo's full test suite passes between phases.

---

## 3. Phase overview

| Phase | Title                                                       | Composite severity served | Effort (eng-days, est.) | Repo blast radius                           |
|-------|-------------------------------------------------------------|:-------------------------:|:-----------------------:|---------------------------------------------|
| R1    | Release-blocking fixes                                      | 4–5                       | 6–9                     | cascor, canopy, data, worker                |
| R2    | Cross-repo unification (architectural)                      | 3–4                       | 8–12                    | cross-repo + new shared lib                 |
| R3    | Test-coverage and correctness gap closure                   | 3                         | 5–7                     | all six                                     |
| R4    | Best-practice and ergonomic improvements                    | 2                         | 4–6                     | all six                                     |
| R5    | Observability for SLOs, scrape config, dashboards           | 2–3                       | 3–5                     | juniper-deploy + per-repo metric definitions|

Total estimate: **26–39 engineer-days** if executed sequentially. R3 and R4 have parallel sub-tasks that can compress wall-clock time.

---

## 4. Phase R1 — Release-blocking fixes

**Trigger:** Phase 7 of the review plan completes.
**Exit:** All composite ≥ 4 findings closed; all in-scope test suites pass; PRs merged to main.

### R1.1 Bound Prometheus middleware cardinality (seed-01)

**Repos:** cascor, canopy, data
**Composite:** 4
**Approach (recommended after Phase 5 design):** Restrict the `endpoint` label to the resolved `route.path` template; under unmatched routes, emit a single bucket `"_unmatched"` and increment a separate counter `juniper_<svc>_http_unmatched_requests_total`. Reject any non-template fallback path.
**Worktrees:** one per repo.
**Tests:** Cardinality stress test sending requests with high-entropy path params; assert label set never exceeds N buckets.

### R1.2 Health probe semantics + status-code propagation (seed-02, seed-03)

**Repos:** cascor, canopy, data
**Composite:** 4
**Approach:** `/health/ready` returns 503 when any dependency is `unhealthy` and 200 with `Status: degraded` only when partial degradation is documented as acceptable. Liveness probes must exercise a real code path (e.g., dataset cache read for data, training-loop tick check for cascor, dashboard render hook for canopy) within a strict timeout; on timeout return 503.
**Coordination:** Helm chart probe wiring in juniper-deploy may need updating in lockstep.
**Tests:** Probe contract tests with simulated dependency failures; integration test that LB withdraws traffic on degraded.

### R1.3 Worker liveness + heartbeat (seed-04)

**Repo:** cascor-worker
**Composite:** 4
**Approach:** Add a minimal HTTP server (or expose health over the existing WS connection as a `worker_heartbeat` frame) emitting `worker_id`, `in_flight_tasks`, `last_task_completed_at`, `rss_mb`. Cascor records the heartbeat; `/v1/workers` route exposes it. Reaper marks worker dead if heartbeat older than threshold.
**Coordination:** Cascor-side route additions; cascor-client may surface worker liveness in CLI.
**Tests:** Worker heartbeat emission unit test; cascor-side staleness-detection test; integration test with simulated worker death (SIGSTOP).

**Phase R1 exit gate:** All four R1 work-items merged. Full test suites green per repo. Roadmap §6 status table reflects R1 = complete.

---

## 5. Phase R2 — Cross-repo unification

### R2.1 Shared `DependencyStatus` / `ReadinessResponse` library (seed-06)

**Composite:** 3
**Approach (recommended):** Promote the duplicated models into a new package `juniper-observability` published from juniper-ml's repo (or as a new sibling repo if owners prefer). Pin from cascor, canopy, data. Eliminate three copies; future changes happen in one place.
**Trade-off:** Adds a new package and dependency edge; pre-empts drift cost.
**Sequencing:** Ship the new package first (PyPI alpha), then migrate consumers in dependency order: data → cascor → canopy.
**Tests:** Per-repo regression test that the migrated model is wire-compatible with the previous shape (`pydantic.BaseModel.model_dump()` snapshot equality).

### R2.2 WS frame schema validation in consumers (seed-05)

**Repos:** cascor-client, cascor-worker
**Composite:** 3
**Approach:** Cascor exposes its WS payload schemas as Pydantic models in a shared module; clients import and validate every inbound frame. Unrecognized frame types log + emit a `juniper_<svc>_unrecognized_ws_frames_total` counter (clients gain minimal observability surface here as a side effect of seed-05).
**Sequencing:** Schema export from cascor first (re-uses R2.1's shared lib if available), then consumer adoption.
**Tests:** Round-trip test: cascor emit → client validate → assert no errors; chaos test sends malformed frames and asserts they are rejected without crashing the consumer.

### R2.3 Probe-direction symmetry (seed-15)

**Composite:** 2 (lifted to 3 if R1.2 reveals deeper issues)
**Approach:** All servers probe their declared upstream dependencies at health-ready time. Cascor probes data; data probes nothing (it is a leaf); canopy probes both. Document the probe graph in `juniper-deploy/notes/`.
**Tests:** Per-repo readiness test that injects a "down" upstream and asserts readiness reflects it.

**Phase R2 exit gate:** Shared lib published; probes symmetric; WS frames validated in clients/workers; all suites green.

---

## 6. Phase R3 — Test-coverage and correctness gap closure

### R3.1 Live integration test for dataset-gen metric (seed-08, BUG-JD-07)

**Repo:** juniper-data
**Composite:** 3
**Tests required:** End-to-end test that POSTs `/v1/datasets`, scrapes `/metrics`, asserts `juniper_data_dataset_generations_total{generator="<X>",status="success"}` incremented by 1 and the duration histogram observed exactly one sample.

### R3.2 Demo-mode gauge integration test (seed-11)

**Repo:** juniper-canopy
**Composite:** 2
**Tests required:** Integration test toggling demo mode and asserting `juniper_canopy_demo_mode_active` reflects within one update tick.

### R3.3 Restore skipped `_create_metrics_panel` test (seed-12)

**Repo:** juniper-canopy
**Composite:** 2
**Approach:** Either (a) expose the method on a public testable surface and unskip; or (b) replace with a black-box test against the dashboard layout endpoint that exercises the same code path. Decision recorded in finding remediation.

### R3.4 Sentry tests unconditional (seed-09)

**Repos:** cascor, canopy, data
**Composite:** 2
**Approach:** Make `sentry-sdk` a hard dev-dep; remove `importorskip`. Sentry hook tests run on every CI run.

### R3.5 Replay-buffer overflow test (seed-07)

**Repo:** cascor
**Composite:** 2
**Tests required:** Drive `_PROJECT_API_METRICS_BUFFER_SIZE + 1` updates; assert oldest entry evicted, newest retained, no exception.

### R3.6 Coverage-matrix gap closure

**All repos.** For every cell marked **GAP** in §10 of the review plan, either close with a test (preferred) or document an accepted-gap rationale in the corresponding finding.

**Phase R3 exit gate:** Coverage matrix has zero unjustified gaps; all suites green.

---

## 7. Phase R4 — Best-practice and ergonomic improvements

### R4.1 Histogram bucket rationales (seed-14)

**Repos:** cascor, canopy, data
**Composite:** 2
**Approach:** Per metric, document the SLO target each bucket boundary serves (e.g., 0.1s for "p95 < 100ms" SLO). Adjust bucket layout if no SLO maps to current buckets.

### R4.2 Async-safe health probes (seed-10)

**Repo:** canopy (verify others)
**Composite:** 2 (3 if blocking observed in production)
**Approach:** Replace `urllib.request.urlopen()` in async health-probe paths with `httpx.AsyncClient` (or equivalent). Add a stress test that fires N concurrent probes against a slow upstream and asserts event loop is not stalled (latency p99 within bound).

### R4.3 Data-client request instrumentation (seed-13)

**Repo:** juniper-data-client
**Composite:** 2
**Approach (recommended):** Optional instrumentation hook accepting a callable invoked on each request with `method, url, status, duration_ms, error`. Default no-op; canopy provides a Prometheus-emitting hook. Avoids forcing prometheus dep into a thin client.
**Tests:** Hook-firing unit test; canopy-side test that requests through the hook produce the expected counter increments.

### R4.4 Worker training-loop instrumentation

**Repo:** cascor-worker
**Composite:** 2
**Approach:** Per-task timing, RSS reporting, GPU utilization (if applicable) emitted as part of the heartbeat frame from R1.3. No new endpoint; reuses heartbeat surface.

**Phase R4 exit gate:** All best-practice findings closed or accepted with documented rationale.

---

## 8. Phase R5 — SLO/SLI definition, scrape config, dashboards

### R5.1 SLO/SLI catalog

**Location:** `juniper-deploy/notes/SLO_CATALOG_2026-04-25.md` (created during this phase).
**Approach:** For each service, define availability SLI (success ratio over rolling window), latency SLI (histogram quantile), and saturation SLI (resource gauge). Tie metric definitions to SLIs. Re-validate histogram bucket choices against SLO targets (revisits R4.1).

### R5.2 Prometheus / ServiceMonitor manifests

**Repo:** juniper-deploy
**Approach:** Confirm scrape configs hit each `/metrics` endpoint; pin scrape interval and label munging; emit `ServiceMonitor` CRDs if running on Prometheus Operator.

### R5.3 Grafana dashboards

**Repo:** juniper-deploy
**Approach:** One dashboard per service, plus a cross-cutting "platform overview" panel set. Dashboard JSON committed and validated by `jsonnet` build (if currently used) or pinned to a snapshot.

### R5.4 Alerting rules

**Repo:** juniper-deploy
**Approach:** PrometheusRule CRDs (or alertmanager config) for each release-blocking SLI. Alert on burn-rate, not on instantaneous threshold breach.

**Phase R5 exit gate:** SLOs documented and instrumented; deployment manifests reproduce dashboards from a clean checkout.

---

## 9. Status tracker (updated through execution)

| Phase | Item                         | Status      | Owner | PR(s) | Worktree | Notes |
|-------|------------------------------|-------------|-------|-------|----------|-------|
| R1.1  | seed-01 cardinality          | **done**    | Paul Calnon | juniper-data#49, juniper-cascor#143, juniper-canopy#178 | cleaned | Unified `_unmatched` bucket + `http_unmatched_requests_total{method}` counter across all 3 servers (merged 2026-04-27) |
| R1.2  | seed-02/03 probe semantics   | **done**    | Paul Calnon | juniper-data#51, juniper-cascor#147, juniper-canopy#183, juniper-deploy#35 | cleaned | Liveness tick (250 ms budget), readiness 503-on-not_ready, `X-Juniper-Readiness` header, cascor lifecycle heartbeat counter, Helm chart v1.0.0 with corrected probe paths (merged 2026-04-27) |
| R1.3  | seed-04 worker heartbeat     | design pending |    |       |          | Awaiting [METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md](METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md) |
| R2.1  | seed-06 shared lib           | not started |       |       |          |       |
| R2.2  | seed-05 WS schema validation | not started |       |       |          |       |
| R2.3  | seed-15 probe symmetry       | not started |       |       |          |       |
| R3.1  | seed-08 dataset-gen e2e      | not started |       |       |          |       |
| R3.2  | seed-11 demo-mode test       | not started |       |       |          |       |
| R3.3  | seed-12 restore skipped test | not started |       |       |          |       |
| R3.4  | seed-09 Sentry unconditional | not started |       |       |          |       |
| R3.5  | seed-07 replay-buffer test   | not started |       |       |          |       |
| R3.6  | coverage-matrix gaps         | not started |       |       |          |       |
| R4.1  | seed-14 bucket rationales    | not started |       |       |          |       |
| R4.2  | seed-10 async-safe probes    | not started |       |       |          |       |
| R4.3  | seed-13 data-client hooks    | not started |       |       |          |       |
| R4.4  | worker training-loop instr   | not started |       |       |          |       |
| R5.1  | SLO catalog                  | not started |       |       |          |       |
| R5.2  | scrape manifests             | not started |       |       |          |       |
| R5.3  | Grafana dashboards           | not started |       |       |          |       |
| R5.4  | alerting rules               | not started |       |       |          |       |

---

## 10. Cross-cutting risks during execution

| Risk                                                                            | Mitigation                                                                           |
|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Shared lib (R2.1) blocks every consumer and slips                               | Ship it as alpha pre-release; consumers pin range; allow incremental migration       |
| Probe-semantics change (R1.2) trips Helm probe failure thresholds and pages SRE | Roll out in staging first; coordinate with juniper-deploy probe-threshold update     |
| Cardinality fix (R1.1) suppresses metrics needed by existing dashboards         | Keep `_unmatched` bucket; emit deprecation warning on raw-path label use for one rel |
| Worker heartbeat (R1.3) introduces new failure mode (heartbeat itself fails)    | Heartbeat failure is best-effort logged; absence treated as soft-degraded, not down  |
| Test-suite expansion balloons CI time                                           | Mark new perf/cardinality tests `@pytest.mark.performance` and gate weekly, not PR   |

---

## 11. Per-repo execution checklist

When picking up an item, the engineer must:

1. **Read the finding** (METRICS-MON-NNN in §9 of the review plan).
2. **Read the recommendation** (Phase 5 output).
3. **Create a worktree** under `/home/pcalnon/Development/python/Juniper/worktrees/` per the project Worktree Setup procedure.
4. **Branch name**: `metrics-mon-<NNN>-<short-slug>` (e.g., `metrics-mon-001-cardinality-fallback`).
5. **Implement + test in the same PR**; do not split fix from test.
6. **Pre-commit must pass.** Do not bypass.
7. **Open PR** against the affected repo's main; cite finding ID in title and body.
8. **After merge**: Worktree Cleanup V2 (`util/worktree_cleanup.bash`).
9. **Update §9 status tracker** in this roadmap.

---

## 12. Definition of done (per item)

An item is **done** when:

- PR is merged to the affected repo's main.
- The associated test exists, runs in CI, and asserts the corrected behavior.
- The finding's status in the review plan is moved to `RESOLVED` with a link to the PR.
- The roadmap §9 row is updated with PR link, owner, and resolution notes.
- If the item changed an AGENTS.md / CLAUDE.md contract, that file is updated in the same PR.

A **phase** is **done** when:

- All items in the phase are done.
- Full test suites pass for every affected repo (no errors, no warnings, no criteria failures).
- A phase summary is appended to this roadmap describing scope shipped, deferred items (with new IDs), and any newly-discovered findings.

---

## 13. Review-to-roadmap traceability

Every roadmap item references one or more findings. No roadmap work is performed without a corresponding finding. New findings discovered during implementation are added to §9 of the review plan first, then a new roadmap row is created. This prevents scope drift.

---

## 14. Closure of the roadmap

The roadmap is **closed** when:

- All phases R1–R5 are done.
- A retrospective document `notes/code-review/METRICS_MONITORING_RETROSPECTIVE_<date>.md` is written summarizing what shipped, what slipped, and what should be added to the next review's baseline.
- The next review's baseline document is opened (or this document is re-baselined for an incremental review).
