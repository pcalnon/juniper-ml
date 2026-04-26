# Juniper Metrics & Monitoring — Cross-Repo Analysis Baseline

**Status:** BASELINE (current-state inventory; review pending)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-25
**Scope:** Metrics, monitoring, observability, health, telemetry surface
**Repos in scope (6):** juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client
**Companion documents:**
- [METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) — review methodology and phased execution
- [METRICS_MONITORING_ROADMAP_2026-04-25.md](METRICS_MONITORING_ROADMAP_2026-04-25.md) — prioritized work breakdown

---

## 1. Purpose

This document captures the **current state** of the metrics/monitoring surface across the six in-scope Juniper applications **before** the comprehensive review begins. It exists so that:

1. The review plan can be scoped credibly (effort estimates anchored in real surface area).
2. Reviewers entering the work cold have a single consolidated map of what exists, where, and what is already known to be problematic.
3. Post-review, gap closure can be measured against this baseline.

This is **not** the review. It is the inventory the review consumes.

---

## 2. Surface area at a glance

| Repo                  | Prom metrics | Health endpoints       | WS metric frames | Sentry | Observability tests | Inter-repo emit/consume               |
|-----------------------|:------------:|------------------------|:----------------:|:------:|---------------------|---------------------------------------|
| juniper-cascor        | 23+ (training + WS) | `/health`, `/health/live`, `/health/ready` | Yes (broadcast: metrics, state, topology, cascade_add) | Yes | ~5 test files (~600+ LOC) | Emits to canopy + cascor-client + worker |
| juniper-cascor-client | 0            | none                   | consumer only    | No     | 0                   | Consumes cascor WS only               |
| juniper-cascor-worker | 0            | none                   | consumer only    | No     | 0                   | Consumes cascor WS, embeds progress in result payloads |
| juniper-canopy        | 6 custom     | `/v1/health`, `/live`, `/ready` | Internal (training/control channels) | Yes | ~31 test cases | Probes data + cascor health at startup; no scrape |
| juniper-data          | 6 custom (incl. dataset gen) | `/v1/health`, `/live`, `/ready` | N/A          | Yes | ~31 test cases (+ Phase 2D) | Emits dataset-gen metrics; nothing scrapes |
| juniper-data-client   | 0            | N/A                    | N/A              | No     | 0                   | No metrics; pure HTTP client |

**Headline observation.** Observability is **bimodal**: server-side apps (cascor, canopy, data) have substantial Prometheus + Sentry + JSON-logging machinery and dedicated tests. Client/worker libraries have **none** — no health, no instrumentation, no schema validation on inbound frames. Whether this asymmetry is intentional (libraries should be observed by their hosts) or a gap (workers run unattended in production and need at least heartbeat + error counters) is the first architectural question the review must answer.

---

## 3. Per-repo inventory

### 3.1 juniper-cascor

**Source files (key paths)**
- `src/api/observability.py` — Prometheus, Sentry, JSON logging, RequestID middleware. Defines 23+ metrics (8 training Gauges/Counters/Histograms; 15 WebSocket Gauges/Counters/Histograms covering `seq_current`, `replay_buffer_occupancy`, `resume_requests`, `broadcast_timeout`, `connections_active`, `command_responses`, etc.).
- `src/api/routes/metrics.py` — `GET /metrics` (snapshot, line 17), `GET /metrics/history?count=N` (line 26, deque-backed, `_PROJECT_API_METRICS_BUFFER_SIZE`).
- `src/api/routes/health.py` — `GET /health` (l. 24), `/health/live` (l. 30), `/health/ready` (l. 36).
- `src/api/lifecycle/monitor.py` — `TrainingState` (l. 59–83), `TrainingMonitor`; `get_state()` returns dict with 26 fields (status, phase, learning_rate, epochs, correlations, candidates_trained, …). Replay buffer wired here at l. 153.
- `src/api/models/health.py` — `ReadinessResponse` (l. 20), `DependencyStatus` (l. 11), `probe_dependency()` HTTP probe.
- `src/api/websocket/messages.py` — `create_metrics_message()` (l. 52), `create_state_message()` (l. 62) with `seq` and `emitted_at_monotonic` instrumentation fields.
- `src/api/websocket/manager.py` — Thread-safe broadcast fan-out; sequence gap detection.

**Tests**
- `test_api_observability.py` (61 LOC), `test_metrics_routes.py` (61 LOC), `test_api_health.py` (189 LOC), `test_lifecycle_monitor.py` (365 LOC), `test_monitoring_hooks.py`. Endpoints exercised; **metric correctness (label cardinality, latency-bucket selection, atomicity of state transitions under concurrency) not consistently asserted.**

**Known issues / smells**
- **BUG-CC-07** flagged in `monitor.py:167` — phase-change handler may lag actual state transitions (state machine driven, handler async).
- `TrainingState` defaults all numeric fields to 0 with no validators (l. 59–83) — no rejection of impossible values (negative epochs, NaN loss).
- **Cardinality risk:** `PrometheusMiddleware` (`observability.py:64–100`) labels by `route.path`; falls back to raw URL path when route template not resolvable, which is **unbounded** under path params.
- `_PROJECT_API_METRICS_BUFFER_SIZE` hardcoded; no overflow behavior documented; no test for buffer wrap.
- `/health/ready` returns HTTP 200 even when `overall="degraded"` (`health.py:62–66`) — load balancers cannot use it for failover.
- `build_info()` Prometheus metric (`observability.py:233`) has no documented scrape target or retention policy.

### 3.2 juniper-cascor-client

**Source files** — none related to metrics. Pure WebSocket consumer (`ws_client.py`) and REST wrapper.

**External deps** — `requests`, `urllib3`, `websockets`. No `prometheus-client`, `sentry-sdk`, `opentelemetry-*`.

**Tests** — `test_client.py`, `test_ws_client.py`. Cover handshake, message parsing, reconnect. **No metric validation.**

**Gaps**
- No local health endpoint or Prometheus scrape target — production users of this library cannot observe it.
- No timeout/retry instrumentation on WebSocket resume/reconnect (BUG-CC-?? candidate).
- **No schema validation on incoming `metrics`/`state` frames** — any cascor protocol drift breaks the consumer silently.

### 3.3 juniper-cascor-worker

**Source files** — none related to metrics. Compute agent connecting via `ws_connection.py`.

**External deps** — `numpy`, `torch`, `websockets`. No observability libraries.

**Tests** — `test_worker.py`, `test_ws_connection.py`. Cover WS protocol and task execution.

**Gaps**
- **No health/readiness probe** — workers in Kubernetes cannot be liveness-checked.
- No training-loop instrumentation (epoch timing, per-task loss, RSS/CPU, GPU utilization).
- No graceful-shutdown metrics (in-flight task count at SIGTERM).
- `task_executor.py` exception-swallowing is unverified; suspected silent-drop path.
- Progress is embedded in task result payloads — no independent emission, so a stuck/dead worker is invisible until a task times out.

### 3.4 juniper-canopy

**Source files**
- `src/observability.py` — Prometheus + Sentry + JSON logging + RequestID middleware. 6 custom metrics (`juniper_canopy_websocket_connections_active`, `…_messages_total{channel,type}`, `…_demo_mode_active`, `…_http_requests_total{method,endpoint,status}`, `…_http_request_duration_seconds{method,endpoint}`, `…_build` Info).
- `src/health.py` — Shared `DependencyStatus`/`ReadinessResponse`; `probe_dependency()`.
- `src/canopy_constants.py` — Health paths, exempt paths, update intervals.
- `src/main.py` — `GET /metrics` (l. 296, Prometheus ASGI), `/v1/health[/live|/ready]` (~l. 2030–2070), `GET /api/metrics` (l. 890), `/api/metrics/history` (l. 900), `/api/v1/metrics/layouts` (l. 1853, CRUD).
- `src/websocket_manager.py` — `inc_websocket_messages(channel, msg_type)` instrumentation; training/control channel emission documented l. 36–81.

**Tests**
- `tests/unit/test_observability.py` (359 LOC, ~31 cases) — middleware, formatter, Sentry, WS metric helpers.
- `tests/unit/test_health.py` — health endpoint behavior.
- `tests/integration/test_*metrics*.py` (5+ files) — panel layouts, candidate metric streaming.

**Known issues / smells**
- `@pytest.mark.skip(reason="Method _create_metrics_panel not exposed as public API")` in `test_dashboard_manager.py` — **disabled test in scope.**
- Cardinality risk: middleware falls back to raw `request.url.path` when route template unavailable (`observability.py:89`).
- `set_demo_mode_active()` not integration-tested — gauge could drift from real state.
- **Blocking `urllib.request.urlopen()` inside async health probe** (`health.py:44`) — event-loop stall under slow upstream.

### 3.5 juniper-data

**Source files**
- `juniper_data/api/observability.py` — Prometheus + Sentry + JSON logging + RequestID. 6 metrics (`juniper_data_dataset_generations_total{generator,status}`, `…_dataset_generation_duration_seconds{generator}` with explicit buckets in `constants.py:82–94`, `…_datasets_cached`, `…_http_requests_total{method,endpoint,status}`, `…_http_request_duration_seconds`, `…_build` Info).
- `juniper_data/api/routes/health.py` — `GET /v1/health` (l. 20), `/live` (l. 30, **always returns `{"status": "alive"}` — no actual check**), `/ready` (l. 43, checks storage dir + `.npz` count).
- `juniper_data/api/models/health.py` — `ReadinessResponse` (l. 18), `DependencyStatus` (l. 9).
- `juniper_data/api/constants.py` — Histogram buckets, status constants.
- `juniper_data/api/app.py` — `GET /metrics` Prometheus ASGI mount (l. 121).

**Tests**
- `tests/unit/test_observability.py` (354 LOC, ~31 cases).
- `tests/unit/test_health_enhanced.py` (138 LOC).
- `tests/unit/test_phase_2d_metrics.py` — validates `record_dataset_generation()` integration with `POST /v1/datasets`. **Mocked-only — no live integration test.**

**Known issues / smells**
- **BUG-JD-09** (`observability.py:98`) — same unbounded-cardinality pattern as cascor/canopy.
- **BUG-JD-06** (`models/health.py:24`) — UTC timestamp consistency note across services.
- **BUG-JD-07** (`test_phase_2d_metrics.py:7`) — generation metric only mocked; no live-fire test.
- Liveness probe is a **no-op** — does not detect process wedge.
- Readiness probe checks storage only (no DB, no cache) — partial signal.
- `pytest.importorskip("sentry_sdk")` — Sentry tests are conditionally skipped, masking regressions when extra is uninstalled.

### 3.6 juniper-data-client

**Source files** — none related to metrics. HTTP client over `requests` + `urllib3`.

**Tests** — Cover HTTP behavior; no metrics tests.

**Gaps**
- No request instrumentation (latency, error counts, request-ID propagation).
- Callers (canopy, cascor) must wrap with their own observability — verifiable inconsistency risk.

---

## 4. Cross-cutting observations

### 4.1 Architectural

- **Two health-model lineages.** `DependencyStatus`/`ReadinessResponse` are duplicated in cascor (`api/models/health.py`), canopy (`src/health.py`), and data (`api/models/health.py`) with subtly different field semantics (timestamp formatting, `details` payload shape). This is an architectural fragility: cross-repo aggregator dashboards must reconcile per-service shapes.
- **No shared observability library.** Each server reimplements `PrometheusMiddleware`, `RequestIdMiddleware`, `JuniperJsonFormatter`. Drift is observable in cardinality-fallback behavior and bucket selection.
- **Probe direction is not bidirectional.** Canopy probes data + cascor at startup; cascor and data do not probe each other. Workers and clients probe nothing. Network partitions visible only from the canopy side.

### 4.2 Logical / correctness

- Cardinality fallback (raw `request.url.path`) is present in **all three** server middlewares and is the most likely production-degrading defect (Prometheus storage cost + scrape latency).
- Liveness probes are no-op in juniper-data and trivially-passing in cascor/canopy. They do not satisfy the contract documented as "process is alive AND functioning."
- Replay/buffer overflow behavior in cascor's metrics history is undocumented and untested.

### 4.3 Test coverage

| Repo                  | Observability test LOC (approx) | Validates correctness? | Validates contract drift? |
|-----------------------|:-------------------------------:|:----------------------:|:-------------------------:|
| juniper-cascor        | ~600                            | Partial                | No                        |
| juniper-cascor-client | 0                               | —                      | **No (silent-drift risk)**|
| juniper-cascor-worker | 0                               | —                      | **No**                    |
| juniper-canopy        | ~360                            | Yes (middleware level) | Partial                   |
| juniper-data          | ~490                            | Yes (incl. Phase 2D)   | Partial                   |
| juniper-data-client   | 0                               | —                      | —                         |

No repo has end-to-end metric tests across the wire (cascor → canopy WS metric frames). Cardinality and bucket selection have no production-tier load tests.

### 4.4 Best-practice deviations

- Sentry `importorskip` masks regressions in optional path.
- Health 200-on-degraded breaks LB integration.
- Blocking I/O in async probe.
- No SLO/SLI definitions tied to the emitted metrics.
- No documented retention or scrape config (Prometheus operator manifests, ServiceMonitor).

---

## 5. Inputs the review will consume

This baseline document, plus:
- AGENTS.md / CLAUDE.md per repo (contracts and command surface).
- `pyproject.toml` extras and dependency pins.
- `.github/workflows/` CI pipelines (whether observability tests are gated).
- Existing bug ledger entries: **BUG-CC-07**, **BUG-JD-06**, **BUG-JD-07**, **BUG-JD-09**, plus newly-created entries the review will assign.
- juniper-deploy compose/k8s manifests (if present) for Prometheus/Grafana scrape config.

---

## 6. Open questions for the review

1. Is the client/worker observability gap intentional? If yes, document the contract; if no, design a minimal heartbeat/error-counter surface.
2. Should `DependencyStatus`/`ReadinessResponse` be hoisted into a shared library (`juniper-ml` extras? new `juniper-observability` package?) to eliminate drift?
3. What is the canonical cardinality strategy — strict route-template-only, with a fallback bucket `"_unmatched"`?
4. Should liveness be strengthened to test the actual primary code path (training loop tick for cascor, dataset cache read for data, dashboard render hook for canopy)?
5. Are there agreed SLOs the metrics should serve? (Without these, gauge/histogram bucket choices are arbitrary.)

---

## 7. Risks if review is not performed

| Risk                                                              | Likelihood | Severity | Notes                                                       |
|-------------------------------------------------------------------|:----------:|:--------:|-------------------------------------------------------------|
| Prometheus cardinality blow-up under attacker-driven path params  | Medium     | High     | Observed in 3 of 6 repos; one bursty incident exhausts TSDB |
| Silent worker death undetected by orchestrator                    | Medium     | High     | No worker liveness; results-channel is the only signal      |
| Client breakage on cascor protocol change (no schema validation)  | Medium     | Medium   | Caught only in production logs, not CI                      |
| Dashboard misreport during demo mode (gauge drift)                | Low        | Medium   | Untested code path; user-visible                            |
| LB failover does not occur on degraded readiness                  | Medium     | Medium   | 200-on-degraded violates k8s readinessProbe contract        |

---

## 8. Acceptance of this baseline

This document is the agreed starting point for the review. Subsequent finding numbers (METRICS-MON-### per the plan) reference paths and concerns named here. If a fact in this document is later contradicted by code inspection, the review records the correction and updates this baseline rather than working from a stale snapshot.
