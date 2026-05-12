# Requirements — OBS

**Area**: observability — metrics, logging, tracing, dashboards, alerting

**Total entries**: 54

**By status**: proposed=41 | in-progress=2 | shipped=8 | deferred=3

**By priority**: P0=7 | P1=26 | P2=16 | P3=5

**By owner**: ml=19 | dep=12 | can=11 | dat=7 | cas=5

---

### JR-DAT-OBS-001 — Security scanning (Bandit and pip-audit) must fail on vulnerabilities, not suppress with || true or || echo.

**Status**: shipped  **Priority**: P0  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 170-238)

**Notes**:

SEC-001 and SEC-002 CRITICAL. Status shipped per 2026-02-24 migration.

### JR-ML-OBS-001 — Fix 7 stale Grafana dashboard panels in juniper-cascor.json and juniper-overview.json - 3 inference panels and 4 placeholder texts.

**Status**: in-progress  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 125-135)

**Detail**:

G1 - Stale panels:
- 3 cascor inference panels query removed juniper_cascor_inference_* metrics
- 4 worker-bridge placeholder text panels never replaced with real PromQL
In-flight branch audit-fixup/stale-dashboard-panels exists as of 2026-05-06.

**Notes**:

Operational blocker. Recommend Option A - land in-flight PR + add dashboard-lint CI guardrail.

### JR-DEP-OBS-001 — Add juniper_cascor_training_sessions_completed_total counter with closed-set outcome labels.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 808-827)

**Detail**:

juniper_cascor_training_sessions_completed_total does not exist as of 2026-05-03.
Cascor currently exposes only training_sessions_active (Gauge) and training_epochs_total (Counter).
Recommendation: add counter with closed-set outcome ∈ {success, error, aborted} bumped from
training-loop completion handler. ~50 lines, R5.4 PR or separate R5.5a sub-track.

### JR-DEP-OBS-002 — Create Grafana dashboards for CasCor training, Data throughput, and Canopy requests.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 75-119)

**Detail**:

Phase 1 (v0.2.0) observability hardening. Three new dashboards: (1) cascor-training.json
with epoch progress, loss, hidden unit additions, latency histogram; (2) data-service.json
with generation rate, request count by endpoint, response time percentiles, error rate;
(3) canopy-requests.json with HTTP rate, WS connections, response codes, page load times.
Dashboard provider already watches provisioning directory; new JSON files auto-load.

### JR-DEP-OBS-003 — Create Prometheus alerting rules for health, latency, error rate, and restart loop.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/JUNIPER-DEPLOY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 111-119)

**Detail**:

Phase 1. Create prometheus/alerts.yml with recording and alerting rules: service health
endpoint down > 2 min, request error rate > 5%, P95 latency > 2s, container restart loop.
Wire into prometheus/prometheus.yml via rule_files directive. Add Grafana alert contact
point configuration to provisioning.

### JR-DEP-OBS-004 — Ship Prometheus burn-rate alerting rules derived from SLO targets with MWMBR pattern.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 102-140)

**Detail**:

Implement Multi-Window Multi-Burn-Rate alerts for the 5 user-facing SLOs (§3).
Fast-burn (5m/1h @ 14.4×) and mid-burn (30m/6h @ 6×) page on-call.
Slow-burn (2h/24h @ 3×) and long-burn (6h/72h @ 1×) create tickets only.
Internal-supporting SLIs (§4) emit log-only-severity alerts with same MWMBR shape.

### JR-ML-OBS-002 — Wire Alertmanager default and tickets receivers (email via Gmail SMTP) to unblock SLO program close-out by 2026-06-02.

**Status**: proposed  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 132-142)

**Detail**:

G2 - Alertmanager receivers silently drop alerts routed to default/tickets.
Both receivers exist as no-op placeholders. Soft blocker before 2026-06-02 soak-close.
Recommend Option A: Email-via-Gmail SMTP for both (use existing SOPS-encrypted creds).

### JR-CAS-OBS-001 — Add thread safety locks to monitoring loop metrics extraction (CascorIntegration._extract_current_metrics).

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 715-743)

### JR-DEP-OBS-005 — Define and catalogue 5 user-facing and 8 internal-supporting SLO/SLI targets for the Juniper observability stack.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 1-50)

**Detail**:

The SLO catalog is the single source of truth for Juniper SLOs. User-facing SLIs
(canopy availability, canopy render latency, cascor train-job success, cascor train-epoch p95,
data POST availability) are release-blocking with tight SLO targets. Internal-supporting SLIs
(worker heartbeat freshness, cascor pending-task queue, broadcast fan-out p95, command-handler
p95, data-client request latency, data-client error rate, dataset cache-hit ratio, http 5xx rate)
are graphed but not paging.

**Notes**:

SLO targets are provisional pending 30-day soak (§2.6). Burn-rate alerting uses
Multi-Window Multi-Burn-Rate pattern. Several forward-references to R5.3/R5.4 designs.

### JR-DEP-OBS-006 — Maintain health-readiness probe topology as a DAG with asymmetric severity policies.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 1-87)

**Detail**:

Canopy probes both cascor and data, returns 200 degraded (dashboard stays visible).
Cascor probes data (when URL set), returns 503 not_ready (gates traffic). Data probes
storage only, returns 503 not_ready. Worker probes nothing externally. Topology is
intentionally a DAG to avoid cascading false-503s. Regression tests pin both policies.
Document in repo readiness handlers.

**Notes**:

Closes METRICS-MON R2.3 seed-15. Operator runbook in §6.

### JR-DAT-OBS-002 — Prometheus histogram juniper_data_dataset_generation_duration_seconds buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, +inf.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 25-43)

**Notes**:

Tentative pending R5.1 SLO design. Bucket rationale documented for each boundary.

### JR-DAT-OBS-003 — Release notes document known issues, resolved issues, and What's Next with accurate status.

**Status**: shipped  **Priority**: P1  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 89-103)

**Notes**:

RD-001 complete 2026-02-24. Only B008 warnings remain. v0.5.0 scope updated.

### JR-ML-OBS-003 — Wire juniper_data_datasets_cached Gauge at every cache mutation site in juniper-data.

**Status**: in-progress  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 142-150)

**Detail**:

G3 - Dead Gauge with no production caller. Defined but never emitted.
In-flight sister PR exists. Add unit test asserting Gauge.value == len(cache) after each operation.

### JR-DEP-OBS-007 — Replace log-only burn-rate alert severity with paging severity after 30-day soak period.

**Status**: deferred  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 918-932)

**Detail**:

All numeric SLO targets in §3 are initial and provisional. R5.4 ships burn-rate alerts in
log-only severity. After 30-day production soak window (target 2026-06-15), compare actual
burn rates against targets, tighten or relax as needed, and lift log-only severity to paging
for §3.1, §3.2, §3.5 (which have all pre-conditions met today).

### JR-ML-OBS-004 — Add dashboard/alert lint lane to juniper-deploy CI.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 284-290)

**Detail**:

Cross-cutting recommendation: Add CI guardrail to prevent future stale panels.
Run promtool check rules on alert_rules.yml and recording_rules.yml.
JSON-schema validate each dashboard and promtool query instant against synthetic Prometheus.

### JR-DEP-OBS-008 — Bridge juniper_cascor_pending_tasks gauge from worker coordinator queue depth to Prometheus.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (lines 510-532)

**Detail**:

R4.4 worker heartbeat SLO (§4.1) is resolved via WorkerRegistryCollector. But §4.2
(pending-task queue depth) still requires a juniper_cascor_pending_tasks gauge from the
worker coordinator. Small cascor sub-track to add to existing WorkerRegistryCollector,
populated from coordinator's pending-task queue depth.

### JR-ML-OBS-005 — broadcast_from_thread adds Task.add_done_callback(_log_exception) (GAP-WS-29).

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 119-119)

**Notes**:

Phase 0-cascor checklist item from R3-03 §3.1 deliverables

### JR-ML-OBS-006 — Canopy must implement JSON audit logger for WebSocket control commands with scrubbing and CRLF escaping.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-02_security_hardening.md` (lines 250-320)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 800-846)

**Detail**:

New src/backend/audit_log.py: canopy.audit logger with JSON formatter, TimedRotatingFileHandler(when="midnight", backupCount=90).
AUDIT_SCRUB_ALLOWLIST auto-derived from SetParamsRequest.model_fields.keys().
audit_log.ws_control(event, ...): logs session_id hash, remote_addr, origin, endpoint, command, request_id, params_keys,
params_scrubbed (before/after), result, seq per R0-02 §4.6 rules 1-11.
CRLF escape every user-controlled field at write-time.
audit_log.ws_auth(...) for auth/origin/cookie failures.
Settings: audit_log_path, audit_log_retention_days.

**Notes**:

IMPL-SEC-32..35. Configurable path and retention. Phase B-pre (Day 6). M-SEC-10 consolidation per R1-03.

### JR-ML-OBS-007 — CCC-02: Observability stack — metrics/logging/tracing/dashboards/alerts before behavior, load-bearing SLO binding.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-03_cross_cutting_concerns.md` (lines 160-258)

**Detail**:

Principle: observability precedes behavior. Every Phase ships metrics, dashboards, alerts, runbooks **before** the feature flips.
Metrics naming convention: `{repo}_ws_{metric}` for WebSocket, `{repo}_training_{metric}` for training control.
Labels: `endpoint` (path), `event_type` (for audit), `transport` (rest/ws), `policy` (backpressure).
Dashboard panels: "WebSocket health" (latency p50/p95/p99), "Polling bandwidth" trend, "Connection state", "Rate limits",
"Audit events", "Backpressure drops".
Alerts: `WSSeqCurrentStalled` (PAGE), `WSResumeBufferNearCap` (ticket), `WSPendingConnectionStuck` (ticket), `WSSlowBroadcastP95` (ticket),
`CSRFFailureRate` (ticket), `AuditLogRotationFailure` (ticket).
Load-bearing SLO: P0 success metric `canopy_rest_polling_bytes_per_sec` >=90% reduction vs baseline. Binding after >=1 week production data.
Acceptance: all metrics present before PR merge, histogram test-fired in staging, gauge queries return non-zero.

**Notes**:

Cross-cutting. Principle from R1-02 principle 1. Dedup with R3-03.

### JR-ML-OBS-008 — _client_latency_ms private field on returned dict.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 223-223)

**Notes**:

Phase A-SDK checklist item from R3-03 §4.1 deliverables

### JR-CAN-OBS-001 — ColoredFormatter must not mutate LogRecord during formatting.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 151-151)

**Detail**:

Issue 3.1.1: ColoredFormatter adds ANSI codes to LogRecord.msg in-place,
affecting file output. Clone record before mutation or use format string.

### JR-DEP-OBS-009 — Consolidate health check timings and Prometheus scrape intervals into .env variables.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 9-145)

**Detail**:

110+ hardcoded values across docker-compose.yml, Prometheus configs, alert rules, scripts.
~24 are env-configurable, ~85 remain hardcoded. Priority HIGH: health check timings (28 values)
and Prometheus config (7 values). Approach A (RECOMMENDED): Docker Compose extension fields
(x-healthcheck-defaults) + .env expansion. Create scripts/config.sh for shell script defaults.
Add ~20 new variables to .env.example: HEALTHCHECK_INTERVAL, TIMEOUT, START_PERIOD, RETRIES;
PROMETHEUS_SCRAPE_INTERVAL, EVAL_INTERVAL, SCRAPE_TIMEOUT; per-service intervals.

### JR-ML-OBS-009 — Create register_or_reuse and register_fresh helpers in juniper-observability to centralize idempotent prometheus_client collector construction, eliminating ~10 copy-pasted implementations across consumer repos.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md` (lines 1-50)

**Detail**:

Two helpers needed:
1. register_or_reuse(factory, name, *args, **kwargs) - adopts existing collectors
2. register_fresh(factory, name, *args, **kwargs) - unregisters and recreates

Live in juniper_observability/prometheus_helpers.py, re-exported from __init__.
~150 lines code + docstrings + unit tests. Target: juniper-data, juniper-canopy, juniper-cascor-client, juniper-cascor.

**Design**:

Constraints:
- Production path zero-overhead
- Test-isolation honesty (predictable behavior)
- Optional-dependency friendly
- No new private-API surface beyond existing inline guards
- Migration is opt-in

API signature:
def register_or_reuse(factory: Callable, name: str, *args, **kwargs) -> T
def register_fresh(factory: Callable, name: str, *args, **kwargs) -> T

**Notes**:

Part of OBS-COLLECTOR-IDEMPOTENT track. Cascor has drop+recreate; 2026-05 PRs use adopt-existing. This centralizes into single canonical form.

### JR-DEP-OBS-010 — Decide on per-service vs. shared library approach for MetricsAuthMiddleware.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (lines 1-60)

**Detail**:

juniper-data ships MetricsAuthMiddleware (IP allowlist on /metrics). Cascor and canopy
expose /metrics without in-process auth. Question: lift to juniper-observability shared lib
or keep per-service? Decision (locked 2026-05-02): keep per-service. Cascor/canopy are
network-isolated (ClusterIP, no ingress routing); data is exposed beyond cluster boundary.
Asymmetry is deliberate. Re-open if: cascor/canopy exposed beyond boundary, third service
needs middleware, compliance audit mandates uniform posture, or NetworkPolicy isolation breaks.

### JR-DEP-OBS-011 — Define and document alert rule thresholds as environment-configurable constants.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 55-66)

**Detail**:

Prometheus alert_rules.yml contains 10+ hardcoded thresholds (error rate 0.05, data P95
latency 2.0s, cascor P95 5.0s, dataset gen 30.0s, correlation 0.01, restart count 3, windows
1m/5m/10m/15m/30m). Document all values clearly in YAML comments. Consider envsubst preprocessing
for full configurability across deployment targets. Medium priority per analysis.

### JR-DEP-OBS-012 — Emit X-Juniper-Readiness response header on all /v1/health/ready endpoints.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PROBE_GRAPH.md` (lines 89-94)

**Detail**:

All four services (cascor, data, canopy, cascor-worker) must emit
X-Juniper-Readiness: ready | degraded | not_ready response header on /v1/health/ready.
Header mirrors body status field byte-for-byte. Constant single-sourced in
juniper-observability (READINESS_HEADER). Cascor-worker uses same literal without import.

### JR-CAN-OBS-002 — Health checks must use async probes instead of blocking network calls.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 155-155)

**Detail**:

Issue 3.1.5: Health endpoints currently block on cascor connectivity checks.
Use async probes or timeout guards to prevent cascor slowness from blocking
health endpoint response.

### JR-CAN-OBS-003 — Logger wrapper instances must be cached to avoid re-wrapping overhead.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 152-152)

**Detail**:

Issue 3.1.2: Wrapper created fresh on each logger.info/debug call. Cache
wrapper per logger instance to improve performance.

### JR-CAN-OBS-004 — Production default log levels must prevent debug spam in production.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 156-156)

**Detail**:

Issue 3.1.6: Default log level may be too verbose in production. Set
production-safe default (INFO/WARNING) independent of dev config.

### JR-CAN-OBS-005 — Prometheus endpoint labels must be normalized to prevent cardinality explosion.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 154-154)

**Detail**:

Issue 3.1.4: Endpoint labels may include query params, causing unbounded cardinality.
Normalize to path template (e.g. /api/v1/params/{id} not /api/v1/params/123).

### JR-CAN-OBS-006 — Sentry sample rate must be configurable via environment variable.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 153-153)

**Detail**:

Issue 3.1.3: Sentry sample_rate hardcoded. Add SENTRY_SAMPLE_RATE env var
with sensible default (0.1 for production, 1.0 for dev).

### JR-ML-OBS-010 — Swap PrometheusMiddleware and RequestIdMiddleware order in canopy main.py:312 to fix mis-labeling.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 162-168)

**Detail**:

G5 - Middleware order causes request-id ContextVar to be unset during metric labeling.
One-line fix. Add unit test asserting request-id header present in metric labels.

### JR-ML-OBS-011 — Wire 9 cascor WS metrics (resume/replay/throttle observability) via OBS-WIRE-02, behind feature flag.

**Status**: proposed  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 148-162)

**Detail**:

G4 - 11 dead cascor_ws_* metrics with zero production callers defined but unwired.
OBS-WIRE-02 wires 9 viable metrics. Remove cascor_ws_seq_gap_detected_total and cascor_ws_connections_active as not feasible.
Deploy behind JUNIPER_CASCOR_WS_METRICS_FULL feature flag initially.

### JR-CAS-OBS-002 — Define Prometheus histogram buckets for latency metrics per observability requirements.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 1-50)

**Notes**:

See histogram_rationale file for bucket selection rationale.

### JR-CAN-OBS-007 — Phase 3 Wave 3—Redis and Cassandra cluster monitoring tabs.

**Status**: shipped  **Priority**: P2  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/proposals/phase3/README.md` (lines 604-897)

**Detail**:

P3-6: Redis monitoring (health badge, memory/ops/hit-rate metrics, auto-refresh). 
P3-7: Cassandra cluster overview (contact points, hosts table, keyspace/table metrics). 
Both integrate new backend clients (redis_client.py, cassandra_client.py), 
optional integration with soft-fail on missing libraries.

**PRs**: {'PR-series': 'Wave 3 (93 new tests, 640+ total for Phase 3)'}

### JR-ML-OBS-012 — Re-bucket cascor_ws_command_handler_seconds for better SLO breach-detection precision post-soak.

**Status**: deferred  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 173-182)

**Detail**:

G7 - 50 ms SLO target sits one bucket below 100 ms +inf cap, limiting breach-detection precision.
Deferred to R5.1c post-soak calibration per juniper-cascor/notes/HISTOGRAM_BUCKETS_RATIONALE.md.

### JR-ML-OBS-013 — Add phase="input" and phase="candidate" emission sites in cascor training_step_duration_seconds.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 169-178)

**Detail**:

G6 - training_step_duration_seconds only emits phase="output" despite SLO design intent of three phases.
Add input/candidate emission sites at corresponding training stages.

### JR-ML-OBS-014 — Canopy must observe set_params latency separately for WebSocket and REST transports.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R0-04_sdk_set_params.md` (lines 200-250)
- `juniper-ml/notes/interface_proposals/R1-04_operational_runbook.md` (lines 1225-1230)

**Detail**:

Histogram canopy_set_params_latency_ms with labels transport="websocket"|"rest".
Buckets: {5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000} ms.
WebSocket: read _client_latency_ms from ack envelope.
REST: measure time.monotonic() delta.

**Notes**:

Per R0-04 §7. Cross-transport comparison informs Phase C feature flag decision (§5.6 ack-vs-effect).

### JR-DAT-OBS-004 — Coverage reporting must upload to external service (Codecov, Coveralls) for trend tracking.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 68-69)

**Notes**:

INF-002 MEDIUM (P2).

### JR-CAS-OBS-003 — Create baseline py-spy profiles for key operations to enable performance regression detection.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 850-854)

### JR-CAS-OBS-004 — Define performance targets for latency and throughput.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

Benchmark harness needed to measure actual performance against targets.

### JR-ML-OBS-015 — emitted_at_monotonic: float on every /ws/training broadcast envelope.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 78-78)

**Notes**:

Settled position C-41 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-016 — GAP-WS-24 splits into 24a (browser JS emitter) + 24b (canopy /api/ws_latency + histogram).

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 57-57)

**Notes**:

Settled position C-20 from R3-03 table; cross-round consensus consolidation

### JR-DAT-OBS-005 — Histogram R5.1 ratification decides SLO targets p95 <100ms and p99 <1s, optionally collapses low-information buckets.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md` (lines 71-87)

**Notes**:

Tentative layout pending R5.1 SLO design. HELP-string marker points to rationale doc.

### JR-ML-OBS-017 — Observability-before-behavior rule: metrics + panels + alerts land BEFORE behavior change.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 75-75)

**Notes**:

Settled position C-38 from R3-03 table; cross-round consensus consolidation

### JR-ML-OBS-018 — P0 success metric: canopy_rest_polling_bytes_per_sec reduced >90% vs baseline.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 74-74)

**Notes**:

Settled position C-37 from R3-03 table; cross-round consensus consolidation

### JR-DAT-OBS-006 — SARIF upload must fail on error, not continue-on-error.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/history/test_suite_audit/TEST_SUITE_CICD_ENHANCEMENT_DEVELOPMENT_PLAN.md` (lines 70-71)

**Notes**:

INF-004 MEDIUM (P2). ci.yml:320.

### JR-CAS-OBS-005 — Verify WebSocket responsiveness under load when training runs via asyncio.run_in_executor().

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 870-874)

### JR-ML-OBS-019 — ws-metrics-buffer store shape = {events, gen, last_drain_ms}.

**Status**: proposed  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R3-03_lean_execution_document.md` (lines 55-55)

**Notes**:

Settled position C-18 from R3-03 table; cross-round consensus consolidation

### JR-DAT-OBS-007 — Continuous profiling (Grafana Pyroscope, Prometheus, OpenTelemetry) deferred until production deployment.

**Status**: deferred  **Priority**: P3  **Category**: OBS  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 493-516)

**Notes**:

RD-017 (DATA-020). Deferred. Partially addressed with Prometheus + Sentry in commit 830a0ef.

### JR-CAN-OBS-008 — All print() statements must be replaced with logger.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 237-237)

**Detail**:

Issue 5.2.3: print() bypasses logging config. Replace with appropriate
logger.info/debug/warning calls throughout codebase.

### JR-CAN-OBS-009 — FATAL_LEVEL constant conflict must be resolved.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 238-238)

**Detail**:

Issue 5.2.4: FATAL_LEVEL defined in multiple modules with different values.
Consolidate to single definition in logging module.

### JR-CAN-OBS-010 — Log timestamps must be timezone-aware (UTC).

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 236-236)

**Detail**:

Issue 5.2.2: Naive timestamps can cause ambiguity in distributed logs.
Use datetime.now(timezone.utc) or equivalent.

### JR-CAN-OBS-011 — Logger must capture real call site instead of logger.py:line-N.

**Status**: proposed  **Priority**: P3  **Category**: OBS  **Owner**: can

**Sources**:
- `juniper-canopy/notes/history/CODE_REVIEW_DEVELOPMENT_ROADMAP_2026-04-04.md` (lines 235-235)

**Detail**:

Issue 5.2.1: _log_with_context wrapper causes all logs to appear from
logger.py instead of actual call site. Use inspect.stack() to get caller.

