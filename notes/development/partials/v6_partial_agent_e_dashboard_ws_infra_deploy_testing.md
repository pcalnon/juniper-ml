# V6 Partial — Agent E: Dashboard, WebSocket, Infrastructure, CasCor, Deploy, Testing

**Sections Covered**: 7 (Dashboard), 8 (WebSocket), 9 (Infrastructure), 10 (CasCor), 13 (Deploy), 14.2-14.3 (Data Perf/Roadmap), 19 (Testing/CI)
**Generated**: 2026-04-22
**Source Verification**: Infrastructure and deploy items verified against live configs

---

### Issue Remediations, Section 7

#### CAN-CRIT-001: Decision Boundary Non-Functional in Production/Service Mode

**Current Code**: Core decision boundary logic present but not wired in service mode.
**Root Cause**: Decision boundary visualization was developed for demo mode only; service mode adapter doesn't provide required data.

**Approach A — Wire into Service Backend**:
- *Implementation*: Add `get_decision_boundary_data()` to `CascorServiceAdapter` that fetches network weights and computes boundary grid server-side (or delegates to cascor API). Wire into existing visualization callback.
- *Strengths*: Completes planned functionality; key visual feature.
- *Weaknesses*: Compute-intensive for large networks; requires cascor API support.
- *Risks*: Performance impact on cascor service during boundary computation.
- *Guardrails*: Cache boundary data; compute on-demand only; throttle to max 1 computation/second.

**Recommended**: Approach A because decision boundary is a critical dashboard feature.

---

#### CAN-CRIT-002: Save/Load Snapshot in Adapter — Blocked on `/v1/snapshots/*` API

**Current Code**: Scope reduced — blocked on cascor snapshot API endpoints.
**Root Cause**: Cascor snapshot REST endpoints not implemented yet.

**Approach A — Implement Cascor Snapshot API First**:
- *Implementation*: Implement `/v1/snapshots/save`, `/v1/snapshots/load`, `/v1/snapshots/list`, `/v1/snapshots/delete` in cascor. Then wire canopy adapter.
- *Strengths*: Enables training session recovery; complete snapshot workflow.
- *Weaknesses*: Cascor API work required first; medium-large effort.
- *Risks*: API design must support all snapshot use cases.
- *Guardrails*: Design API spec before implementation; review with canopy team.

**Recommended**: Approach A — implement cascor API as prerequisite.

---

#### CAN-HIGH-005: Remote Worker Status Dashboard

**Current Code**: Not started.
**Root Cause**: Feature not yet implemented.

**Approach A — Worker Status Panel**:
- *Implementation*: Add new dashboard tab showing connected workers (from `/v1/workers` API), their status, assigned tasks, and health. Subscribe to worker WS events for real-time updates.
- *Strengths*: Visibility into distributed training; operational monitoring.
- *Weaknesses*: Requires cascor worker coordinator API.
- *Risks*: Worker coordinator API may not expose all needed data.
- *Guardrails*: Start with read-only status display; add management controls later.

**Recommended**: Approach A.

---

#### KL-1: Dataset Scatter Plot Empty in Service Mode

**Current Code**: Known limitation — dataset visualization unavailable in service mode.
**Root Cause**: Service adapter doesn't provide raw dataset arrays needed for scatter plot.

**Approach A — Fetch Data via API**:
- *Implementation*: Add `get_dataset_preview(n=1000)` to service adapter that fetches a subset of training data from cascor's dataset endpoint. Display in scatter plot.
- *Strengths*: Functional scatter plot in service mode.
- *Weaknesses*: Network overhead for data transfer.
- *Risks*: Large datasets may be slow to transfer.
- *Guardrails*: Limit preview to 1000 points; cache on client side.

**Recommended**: Approach A.

---

#### CAN-DEF-008: Advanced 3D Node Interactions

**Approach A — Deferred**: 🔵 Explicitly deferred per V5 document. Low priority (P4).

---

#### CAN-000 through CAN-021: Enhancement Backlog (22 items)

All items are 🔴 NOT STARTED feature enhancements. Brief remediation notes:

#### CAN-000: Periodic Updates Pause When Apply Parameters Active

**Approach A**: Add `_apply_in_progress` flag. Pause polling intervals while parameters dialog is open. Resume on Apply or Cancel.
**Recommended**: Approach A — UI state management.

#### CAN-001/CAN-002: Training Loss Time Window Toggle/Custom Rolling Window

**Approach A**: Add Plotly `xaxis.range` slider for time window. Store window preference in client state.
**Recommended**: Combined implementation as time window feature.

#### CAN-003: Retain Candidate Pool Data Per Node Addition

**Approach A**: Store candidate pool metrics in list indexed by node addition count. Add expandable "Previous Pools" UI section.
**Recommended**: Approach A.

#### CAN-004 through CAN-013: Meta Parameter Tuning Tab (10 items)

**Approach A**: Create new `MetaParameterTuningPanel` component with all meta parameters. Each param gets a slider/input with range validation. Pin/unpin to side menu via user preference store.
**Recommended**: Implement as a cohesive feature, not individual items.

#### CAN-014/CAN-015: Snapshot Tuning Capture and Replay

**Approach A**: Extend snapshot format to include current parameter values. Add replay UI that restores parameters and optionally starts new training.
**Recommended**: Approach A — requires CAN-CRIT-002 (snapshot API) first.

#### CAN-016a/CAN-016b: Save/Load Layout + Import/Generate Dataset

**Approach A**: Use browser localStorage for layout state. Add file upload and REST-based dataset import.
**Recommended**: Independent features; implement separately.

#### CAN-017/CAN-018/CAN-019: Tooltips, Right-Click Tutorials, Walk-Through

**Approach A**: Add `dcc.Tooltip` components. Right-click context menus with doc links. Walk-through using `dash-intro-js` or similar library.
**Recommended**: Progressive implementation by priority (tooltips first).

#### CAN-020/CAN-021: Hierarchy Level and Population Views

**Approach A**: Extend network visualizer to support hierarchy filtering and ensemble/population display.
**Recommended**: P4 priority; implement when multi-hierarchical CasCor (CAS-008) is available.

---

### Issue Remediations, Section 8

#### Phase E: Backpressure Pump Tasks

**Current Code**: Not started — conditional on telemetry data.
**Root Cause**: Requires measuring actual WS message throughput before designing backpressure.

**Approach A — Implement with Telemetry**:
- *Implementation*: Add WS send queue depth metrics. Implement backpressure: when queue > threshold, drop low-priority messages (metrics before state, state before topology). Use priority queue for WS send buffer.
- *Strengths*: Prevents client overwhelm; prioritizes critical messages.
- *Weaknesses*: Message loss for low-priority events.
- *Risks*: Priority tuning requires production telemetry.
- *Guardrails*: Default threshold conservative (1000 messages); counter for dropped messages.

**Recommended**: Approach A after gathering telemetry data.

---

#### Phase F: Heartbeat Jitter

**Approach A — Add Random Jitter**:
- *Implementation*: Add `±10%` random jitter to heartbeat interval: `interval * (0.9 + random.random() * 0.2)`.
- *Strengths*: Prevents thundering herd from synchronized heartbeats.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Keep within ±10% of configured interval.

**Recommended**: Approach A — trivial addition.

---

#### Phase G: Integration Tests for `set_params` via WS

**Approach A — End-to-End Test**:
- *Implementation*: Write integration test: connect WS, send `set_params`, verify parameter change via `/v1/network` GET. Use `requires_server` marker.
- *Strengths*: Validates the full param update flow.
- *Weaknesses*: Requires running server.
- *Risks*: Flaky if server slow to apply params.
- *Guardrails*: Retry with backoff on GET verification; timeout at 10s.

**Recommended**: Approach A.

---

#### Phase H: `_normalize_metric` Audit

**Approach A — Comprehensive Audit**:
- *Implementation*: Audit all `_normalize_metric` callsites. Verify each metric name maps correctly to the canonical name. Document metric naming conventions.
- *Strengths*: Ensures consistent metric names across dashboard.
- *Weaknesses*: Manual audit effort.
- *Risks*: None.
- *Guardrails*: Add unit test for each metric normalization.

**Recommended**: Approach A.

---

#### GAP-WS-16: `/api/metrics/history` Polling Bandwidth Bomb (~3 MB/s)

**Current Code**: REST polling for metrics history; ~3 MB/s per dashboard tab.
**Root Cause**: Polling-based architecture transfers all history on every poll.

**Approach A — WS Push with Delta Updates**:
- *Implementation*: Replace polling with WS subscription. Server pushes only new metric entries since client's last sequence number. Client appends to local buffer.
- *Strengths*: ~99% bandwidth reduction; real-time updates.
- *Weaknesses*: Requires WS subscription management.
- *Risks*: Must handle reconnection and catch-up.
- *Guardrails*: Keep REST endpoint as fallback; add sequence-based delta API.

**Recommended**: Approach A because 3 MB/s per tab is unsustainable.

---

#### GAP-WS-14: Plotly `extendTraces` with `maxPoints` Limit

**Current Code**: Full figure rebuild on each update (80-200ms).
**Root Cause**: Replacing entire figure data instead of appending to existing traces.

**Approach A — Use `extendTraces`**:
- *Implementation*: Use Plotly.js `Plotly.extendTraces(divId, update, traceIndices, maxPoints)` via clientside callback. Set `maxPoints` to limit (e.g., 10000).
- *Strengths*: ~10x rendering speedup; bounded memory.
- *Weaknesses*: Requires Dash clientside callback.
- *Risks*: Must handle trace initialization and reset.
- *Guardrails*: Add `maxPoints` to Settings; default 10000.

**Recommended**: Approach A because full figure rebuild at 50Hz is prohibitively expensive.

---

#### GAP-WS-15: Browser-Side rAF Coalescing for 50Hz Candidate Events

**Approach A — requestAnimationFrame Batching**:
- *Implementation*: Buffer incoming WS events. Process batch once per `requestAnimationFrame` (~60fps). Use latest value for each metric (skip intermediate).
- *Strengths*: Prevents 50Hz DOM updates; smooth animations.
- *Weaknesses*: Slight message delivery latency.
- *Risks*: None.
- *Guardrails*: Max batch size 100; flush timer for low-frequency events.

**Recommended**: Approach A.

---

#### GAP-WS-13: Lossless Reconnect via Sequence Numbers and Replay Buffer

**Approach A — Sequence-Based Replay**:
- *Implementation*: Client sends last-received sequence number on reconnect. Server replays from sequence N+1 using replay buffer. Already partially implemented in cascor (`ws_replay_buffer_size: 1024`).
- *Strengths*: No event loss during brief disconnects.
- *Weaknesses*: Buffer overflow loses old events.
- *Risks*: Replay buffer size must accommodate typical disconnect durations.
- *Guardrails*: Log replay events at DEBUG; alert on buffer overflow.

**Recommended**: Approach A — partially implemented, needs client-side integration.

---

#### GAP-WS-25: WebSocket-Health-Aware Polling Toggle

**Approach A — Health-Aware Fallback**:
- *Implementation*: When WS is healthy, disable REST polling. On WS disconnect, enable REST polling. On WS reconnect, disable polling again. Use `WSHealthMonitor` component.
- *Strengths*: Eliminates duplicate data; reduces load.
- *Weaknesses*: Must handle transition periods.
- *Risks*: Brief gap during toggle.
- *Guardrails*: 5-second overlap during transition to prevent data gaps.

**Recommended**: Approach A.

---

#### GAP-WS-26: Visible Connection Status Indicator

**Approach A — Status Badge Component**:
- *Implementation*: Add `ConnectionStatusBadge` component: green (connected), yellow (reconnecting), red (disconnected). Position in dashboard header.
- *Strengths*: User visibility into connection state.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Include tooltip with connection details.

**Recommended**: Approach A.

---

#### GAP-WS-18: Topology Message >64KB Causes Connection Teardown

**Approach A — Message Chunking**:
- *Implementation*: Add topology message size check. If >64KB, split into chunks with sequence header: `{"chunk": 1, "total": 3, "data": ...}`. Client reassembles.
- *Strengths*: Handles arbitrarily large topologies.
- *Weaknesses*: Chunking protocol complexity.
- *Risks*: Chunk reassembly failures.
- *Guardrails*: Fallback to REST fetch if chunked delivery fails.

**Approach B — Topology Compression**:
- *Implementation*: Compress topology JSON with zlib before WS send. Client decompresses.
- *Strengths*: Simple; typically 5-10x compression for JSON.
- *Weaknesses*: CPU overhead for compression.
- *Risks*: Client must support decompression.
- *Guardrails*: Only compress messages > 10KB.

**Recommended**: Approach B for simplicity; Approach A for guaranteed delivery.

---

#### GAP-WS-21: 1 Hz State Throttle Drops Terminal Transitions

**Cross-References**: Same as BUG-CN-06.
**Approach A**: See BUG-CN-06 remediation (always send terminal states).
**Recommended**: See BUG-CN-06.

---

#### GAP-WS-28: Multi-Key `update_params` Torn-Write Race

**Approach A — Atomic Parameter Update**:
- *Implementation*: Server applies all params from a single `update_params` message atomically (within a lock). No partial application.
- *Strengths*: Consistent parameter state.
- *Weaknesses*: Lock contention during training.
- *Risks*: Must not block training thread.
- *Guardrails*: Queue param updates; apply between training steps.

**Recommended**: Approach A.

---

#### GAP-WS-31: Unbounded Reconnect Cap — Stops After 10

**Approach A — Infinite Reconnect with Backoff**:
- *Implementation*: Remove max reconnect limit. Use exponential backoff with cap (e.g., max 5 minutes between attempts). Add configurable `max_reconnect_interval`.
- *Strengths*: Dashboards never permanently lose connection.
- *Weaknesses*: Persistent retries on permanently dead servers.
- *Risks*: Resource usage from retry polling.
- *Guardrails*: Show user notification after 10 failures; continue retrying silently.

**Recommended**: Approach A.

---

#### GAP-WS-32: Per-Command Timeouts and Orphaned-Command Resolution

**Approach A — Command Timeout with Cleanup**:
- *Implementation*: Add per-command timeout (default 30s). On timeout, resolve pending future with `TimeoutError`. Clean up command from pending map. Log orphaned commands.
- *Strengths*: Prevents indefinite hangs; clean resource management.
- *Weaknesses*: Must choose appropriate timeout per command type.
- *Risks*: Premature timeout on slow operations.
- *Guardrails*: Configurable per-command timeouts; log timeouts at WARNING.

**Recommended**: Approach A.

---

#### Phase B-pre-b: CSWSH/CSRF on `/ws/control`

**Cross-References**: Related to SEC-05.
**Approach A**: Apply same Origin validation as SEC-05 fix specifically to `/ws/control`.
**Recommended**: Implement alongside SEC-05.

---

### Issue Remediations, Section 9

#### 5.1: AlertManager Receivers — Placeholders Only

**Approach A — Configure Real Receivers**:
- *Implementation*: Add Slack webhook URL and/or email SMTP config to `alertmanager.yml`. Keep placeholders for unused channels.
- *Strengths*: Functional alerting.
- *Weaknesses*: Requires external service config.
- *Risks*: Webhook URL must be kept secret.
- *Guardrails*: Use environment variables for webhook URLs.

**Recommended**: Approach A.

---

#### 5.3: Standardize Health Endpoints

**Cross-References**: Related to API-01, API-02, XREPO-13.
**Approach A**: Standardize all health endpoints to `{"status": "ok", "version": "x.y.z", "service": "name"}`. See API-01/API-02 remediations.
**Recommended**: See API-01/API-02.

---

#### 5.4: Volume Backup/Restore Documentation

**Approach A — Create Documentation**:
- *Implementation*: Write `docs/BACKUP_RESTORE.md` covering: Docker volume backup (`docker cp`/`docker volume`), data directory backup, snapshot backup, restore procedures.
- *Strengths*: Operational documentation; disaster recovery.
- *Weaknesses*: Documentation effort.
- *Risks*: None.
- *Guardrails*: Test restore procedure in staging.

**Recommended**: Approach A.

---

#### 5.5: Startup Validation Test Suite

**Approach A — Add Service Startup Tests**:
- *Implementation*: Create tests that verify each service starts correctly: health endpoint responds, correct version reported, configuration loaded properly.
- *Strengths*: Catches startup regressions.
- *Weaknesses*: Requires running services in CI.
- *Risks*: Flaky if services slow to start.
- *Guardrails*: Health check polling with timeout.

**Recommended**: Approach A.

---

### Issue Remediations, Section 10

All CasCor enhancement items are feature requests. Brief remediation approaches:

#### CAS-002/CAS-003: Separate Epoch Limits and Max Iterations

**Approach A**: Add `network_max_epochs`, `candidate_max_epochs`, `max_iterations` to training parameters. Enforce in training loop.
**Recommended**: Approach A — parameter additions.

#### CAS-006: Auto-Snap Best Network

**Approach A**: Track best accuracy in training loop. Auto-save snapshot when new best achieved. Add `auto_snapshot_best: bool = True` setting.
**Recommended**: Approach A.

#### ENH-006/ENH-007: Flexible Optimizer and N-Best Candidate Selection

**Approach A**: Create `OptimizerFactory` supporting Adam/SGD/RMSprop/AdamW. For N-best: train candidate pool, rank by correlation, install top-N.
**Recommended**: Approach A — separate features.

#### CAS-008/CAS-009: Hierarchy and Population Management

**Approach A**: P4 priority. Design architecture for multi-hierarchical CasCor and ensemble approaches. Implement after core algorithm stabilizes.
**Recommended**: Deferred — design phase only.

#### ENH-001 through ENH-005, ENH-008: Serialization and Validation

**Approach A**: Implement remaining 7 serialization tests (ENH-001). Add SHA256 checksum (ENH-002), shape validation (ENH-003), format validation (ENH-004). Refactor candidate factory (ENH-005). Add SIGKILL fallback for worker cleanup (ENH-008).
**Recommended**: Approach A — implement as a serialization hardening sprint.

#### CAS-005, CAS-010, and Other Storage Items

**Approach A**: Extract shared code to `juniper-core` package (CAS-005). Snapshot vector DB (CAS-010) is P4. Shared memory sweep, snapshot API, GPU support, file refactoring, API docs — implement per priority.
**Recommended**: Prioritize by dependency graph; CAS-005 enables other items.

---

### Issue Remediations, Section 13

#### DEPLOY-01: Docker Secret Name/Path Mismatch

**Current Code**: `docker-compose.yml:110` uses `juniper_data_api_key` (singular); app expects `juniper_data_api_keys` (plural).
**Root Cause**: Naming inconsistency between compose secret name and application config.

**Approach A — Fix Secret Name to Plural**:
- *Implementation*: Change `docker-compose.yml` secret name from `juniper_data_api_key` to `juniper_data_api_keys` to match application expectation.
- *Strengths*: One-line fix; matches app config.
- *Weaknesses*: Must update any deployment scripts referencing old name.
- *Risks*: Existing deployments must update.
- *Guardrails*: Document change in CHANGELOG.

**Recommended**: Approach A — trivial naming fix.

---

#### DEPLOY-02: AlertManager Service Missing from docker-compose.yml

**Current Code**: `prometheus.yml:34` references `alertmanager:9093`; config file exists but no compose service.
**Root Cause**: AlertManager config was created but service definition never added to compose.

**Approach A — Add AlertManager Service**:
- *Implementation*: Add alertmanager service to docker-compose.yml: image `prom/alertmanager`, ports `9093`, volume mount `./alertmanager:/etc/alertmanager`, network `backend`.
- *Strengths*: Complete monitoring stack.
- *Weaknesses*: Additional container resource usage.
- *Risks*: Must configure real receivers (see 5.1).
- *Guardrails*: Add healthcheck; include in monitoring profile.

**Recommended**: Approach A.

---

#### DEPLOY-03/DEPLOY-14: Prometheus Rules Not Mounted

**Current Code**: `docker-compose.yml:422` — only `prometheus.yml` file mounted, not rules directory.
**Root Cause**: Single file mount; rules files exist in `prometheus/` directory but aren't accessible in container.

**Approach A — Mount Entire Directory**:
- *Implementation*: Change from `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro` to `./prometheus:/etc/prometheus:ro`.
- *Strengths*: All config files accessible; includes alert_rules.yml, recording_rules.yml.
- *Weaknesses*: Entire directory mounted (acceptable for config).
- *Risks*: None.
- *Guardrails*: Verify `prometheus.yml` references use correct paths after mount change.

**Recommended**: Approach A — one-line fix.

---

#### DEPLOY-04: K8s Canopy Missing Service URL Env Vars

**Approach A — Add to Helm Values**:
- *Implementation*: Add `JUNIPER_CANOPY_JUNIPER_DATA_URL` and `JUNIPER_CANOPY_CASCOR_SERVICE_URL` to canopy deployment env in `values.yaml`.
- *Strengths*: Canopy can reach dependent services in K8s.
- *Weaknesses*: None.
- *Risks*: Must use correct K8s service DNS names.
- *Guardrails*: Use Helm templating: `http://{{ .Release.Name }}-data:8100`.

**Recommended**: Approach A.

---

#### DEPLOY-05 through DEPLOY-12, DEPLOY-15 through DEPLOY-23: Infrastructure Items

Brief remediations for remaining deploy items:

- **DEPLOY-05**: Add `auth.enabled: true` and `auth.password` to Redis values.yaml.
- **DEPLOY-06**: Set non-empty Grafana admin password via Helm values secret.
- **DEPLOY-07**: Add `deploy.resources.limits` to each compose service.
- **DEPLOY-08**: Bind to `127.0.0.1` instead of `0.0.0.0` for local-only services.
- **DEPLOY-09**: Use Docker secrets for worker auth token (same as compose secrets).
- **DEPLOY-10**: Add security hardening to demo profiles (rate limiting, auth).
- **DEPLOY-11**: Set non-empty `JUNIPER_DATA_API_KEYS` default; require explicit disable.
- **DEPLOY-12**: Use env vars for ports in `wait_for_services.sh`.
- **DEPLOY-13**: Add `canopy-dev` to both `frontend` and `backend` networks.
- **DEPLOY-15**: Pin image tags to specific versions (e.g., `0.4.0`) instead of `latest`.
- **DEPLOY-16**: Same as DEPLOY-06 for kube-prometheus-stack.
- **DEPLOY-17**: Stub all 4 Dockerfiles and 7 secrets in CI validation.
- **DEPLOY-18/19**: Add healthchecks for Prometheus and Grafana containers.
- **DEPLOY-20**: Document Redis persistence limitation; acceptable for cache.
- **DEPLOY-21**: Add Redis dependency to demo/dev profiles.
- **DEPLOY-22**: Pin `python:3.12-slim` to digest or patch version.
- **DEPLOY-23**: Add `helm lint` and `helm template` to CI.

#### DEPLOY-24/25/26: Helm Missing Critical Env Vars

**Approach A — Add Missing Env Vars**:
- *Implementation*: Add `JUNIPER_DATA_URL` to canopy and cascor sections. Add `CASCOR_SERVER_URL` to worker section of `values.yaml`.
- *Strengths*: Services can discover each other in K8s.
- *Weaknesses*: None.
- *Risks*: Must use correct K8s service DNS names.
- *Guardrails*: Use Helm templating for dynamic service discovery.

**Recommended**: Approach A — critical for K8s deployments.

---

#### DEPLOY-RD-01 through DEPLOY-RD-08: Roadmap Items

All roadmap items are 🔴 NOT DONE. Brief approaches:

- **DEPLOY-RD-01**: Create `docker-compose.production.yml` overlay with resource limits, health checks, restart policies.
- **DEPLOY-RD-02**: Add nginx/traefik reverse proxy service for TLS termination.
- **DEPLOY-RD-03**: Add GitHub Actions scheduled workflow for weekly integration tests.
- **DEPLOY-RD-04**: Add Trivy/Grype container scanning to CI.
- **DEPLOY-RD-05**: Create `systemd/` directory with unit files for all 4 services.
- **DEPLOY-RD-06**: Implement Docker integration CI: build → start → health check → teardown.
- **DEPLOY-RD-07/08**: SOPS multi-key and Docker secrets integration — deferred to Phase 5.

---

### Issue Remediations, Section 14 — Performance and Roadmap

#### JD-PERF-01: Sync `generator.generate()` Blocks Event Loop

**Cross-References**: JD-PERF-01 = SEC-04 = CONC-04
**Approach A**: See SEC-04/CONC-04 remediation (asyncio.to_thread).

---

#### JD-PERF-02: `filter_datasets`/`get_stats` Load ALL Metadata

**Current Code**: `storage/base.py:261,317` — O(n) disk reads on every call.
**Root Cause**: No indexing or caching of metadata.

**Approach A — In-Memory Metadata Cache**:
- *Implementation*: Maintain in-memory metadata index updated on save/delete. Filter and stats operate on cached data.
- *Strengths*: O(1) queries after initial load.
- *Weaknesses*: Memory usage proportional to dataset count.
- *Risks*: Cache invalidation on external file changes.
- *Guardrails*: Periodic cache refresh; cache size limit.

**Recommended**: Approach A.

---

#### JD-PERF-03: `list_versions` Loads All Metadata

**Approach A — DB-Level Filtering for Postgres**:
- *Implementation*: Override `list_versions()` in `PostgresStore` with SQL query filtering. Keep filesystem implementation as-is for LocalFS.
- *Strengths*: Efficient for Postgres; no regression for LocalFS.
- *Weaknesses*: Dual implementation.
- *Risks*: None.
- *Guardrails*: Test both storage backends.

**Recommended**: Approach A.

---

#### JD-PERF-04: No Connection Pooling for Postgres

**Current Code**: `psycopg2.connect()` per operation; `close()` is a no-op.
**Root Cause**: Connection-per-request pattern without pooling.

**Approach A — Connection Pool**:
- *Implementation*: Use `psycopg2.pool.SimpleConnectionPool` or `psycopg_pool.ConnectionPool` (psycopg3). Set min/max connections.
- *Strengths*: Reuse connections; reduced latency.
- *Weaknesses*: Pool management lifecycle.
- *Risks*: Must handle pool exhaustion.
- *Guardrails*: Max pool size configurable via Settings; timeout on pool acquisition.

**Recommended**: Approach A.

---

#### JD-PERF-05: Readiness Probe Filesystem Glob

**Cross-References**: JD-PERF-05 = PERF-JD-01
**Approach A**: See PERF-JD-01 remediation.

---

#### RD-008/RD-015/RD-016/RD-017: Deferred Roadmap Items

All 🔵 DEFERRED. No immediate remediation required.

---

### Issue Remediations, Section 19

#### CI-01: cascor-client CI Doesn't Test Python 3.14

**Current Code**: CI matrix missing 3.14; consumers run on 3.14.
**Root Cause**: CI not updated when 3.14 support was classified.

**Approach A — Add 3.14 to CI Matrix**:
- *Implementation*: Add `"3.14"` to the Python version matrix in `.github/workflows/ci.yml`.
- *Strengths*: Catches 3.14 incompatibilities before consumer deployment.
- *Weaknesses*: Longer CI runs.
- *Risks*: 3.14 may not be available in CI runner images (use `actions/setup-python@v5`).
- *Guardrails*: Allow 3.14 failures initially (non-blocking).

**Recommended**: Approach A.

---

#### CI-02: cascor-worker CI Doesn't Test Python 3.14

**Approach A**: Same as CI-01 — add 3.14 to matrix.
**Recommended**: Approach A.

---

#### CI-03: juniper-deploy CI Runs ZERO Tests

**Current Code**: 1,177 lines of tests exist but never run in CI.
**Root Cause**: Pytest job not configured in deploy CI workflow.

**Approach A — Add Pytest Job**:
- *Implementation*: Add `pytest tests/ -v --tb=short` job to `.github/workflows/ci.yml`.
- *Strengths*: Existing tests become useful; catches regressions.
- *Weaknesses*: May require test dependencies.
- *Risks*: Tests may fail if they depend on Docker.
- *Guardrails*: Run unit tests only (skip Docker-dependent tests in CI).

**Recommended**: Approach A because 1,177 lines of untested tests provide zero value.

---

#### CI-04: Missing Weekly security-scan.yml for cascor-client

**Approach A — Create Workflow**:
- *Implementation*: Copy `security-scan.yml` from juniper-cascor or juniper-ml. Add pip-audit and dependabot for cascor-client.
- *Strengths*: Closes supply chain vulnerability window.
- *Weaknesses*: Weekly cadence may miss urgent CVEs.
- *Risks*: None.
- *Guardrails*: Also enable Dependabot security alerts.

**Recommended**: Approach A.

---

#### CI-05: Missing lockfile-update.yml for cascor-client

**Approach A — Create Workflow**:
- *Implementation*: Add scheduled workflow to update `requirements.lock` and open PR on changes.
- *Strengths*: Prevents stale dependencies.
- *Weaknesses*: Auto-PRs may be noisy.
- *Risks*: Updates may break compatibility.
- *Guardrails*: Auto-PR requires passing CI before merge.

**Recommended**: Approach A.

---

#### CI-06: juniper-deploy No Coverage Configuration

**Approach A — Add Coverage Config**:
- *Implementation*: Add `[tool.coverage]` to `pyproject.toml`. Add `--cov` flag to pytest command. Set initial threshold at 50%.
- *Strengths*: Measurable test coverage; improvement tracking.
- *Weaknesses*: Low initial threshold.
- *Risks*: None.
- *Guardrails*: Gradually increase threshold.

**Recommended**: Approach A.

---

#### CI-07: Inconsistent GitHub Actions Versions Across Repos

**Approach A — Standardize Versions**:
- *Implementation*: Align all repos to same versions of `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, etc.
- *Strengths*: Consistent CI behavior; easier maintenance.
- *Weaknesses*: Coordination across 8 repos.
- *Risks*: Version upgrades may break workflows.
- *Guardrails*: Test one repo first; roll out to others.

**Recommended**: Approach A.

---

#### COV-01: Deploy Tests Exist but Zero Coverage

**Cross-References**: COV-01 = CI-06.
**Approach A**: See CI-06 remediation.

---

#### COV-02: Canopy No Per-Module Coverage Gate

**Approach A — Add Per-Module Coverage**:
- *Implementation*: Add `[tool.coverage.run] source = ["src"]` and module-level minimums in `pyproject.toml`.
- *Strengths*: Prevents coverage regression per module.
- *Weaknesses*: Setup effort.
- *Risks*: Some modules may be below threshold.
- *Guardrails*: Start with 60% per-module; increase gradually.

**Recommended**: Approach A.

---

#### COV-04: Coverage Gate Mismatch — CI Comment 95% vs Actual 80%

**Approach A — Align Documentation**:
- *Implementation*: Update CI comment to match actual `COVERAGE_FAIL_UNDER=80`. Or raise threshold if 95% is the real target.
- *Strengths*: Consistent documentation.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A — fix documentation to match reality.

---

#### TQ-01: 10+ Tests with No Assertions (cascor)

**Approach A — Add Assertions**:
- *Implementation*: Review each assertion-free test. Add appropriate assertions (return values, state changes, exception types).
- *Strengths*: Tests actually verify behavior.
- *Weaknesses*: Must understand test intent.
- *Risks*: Some tests may be deliberately assertion-free (smoke tests).
- *Guardrails*: Mark intentional smoke tests with `# smoke test` comment.

**Recommended**: Approach A.

---

#### TQ-02: 149 `time.sleep` Calls in canopy Tests

**Approach A — Replace with Event-Based Waits**:
- *Implementation*: Replace `time.sleep(n)` with `wait_for_condition(lambda: ..., timeout=n)` helper. Poll condition every 50ms.
- *Strengths*: Tests run faster; less flaky.
- *Weaknesses*: Must identify correct condition for each wait.
- *Risks*: Some waits may be for side effects without observable conditions.
- *Guardrails*: Keep timeout as upper bound; reduce gradually.

**Recommended**: Approach A — incremental replacement.

---

#### TQ-03: Worker Config Validation Tests with No Assertions

**Approach A — Add Assertions**:
- *Implementation*: Add assertions verifying config values after validation.
- *Strengths*: Tests verify behavior.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: None needed.

**Recommended**: Approach A.

---

#### TQ-04: 139 `hasattr` Guards in cascor Tests

**Approach A**: Same pattern as BUG-CN-03 — remove guards, fix mocks.
**Recommended**: See BUG-CN-03 remediation.

---

#### TQ-05: 10 Unit Tests Import httpx (Integration-Level)

**Approach A — Re-Classify as Integration Tests**:
- *Implementation*: Move tests using `httpx` to `tests/integration/` directory. Apply `requires_server` marker.
- *Strengths*: Correct test classification; clear expectations.
- *Weaknesses*: None.
- *Risks*: None.
- *Guardrails*: Run in separate CI job.

**Recommended**: Approach A.

---

#### CI-SEC-01: No Weekly Security Scan for cascor-client

**Cross-References**: CI-SEC-01 = CI-04.
**Approach A**: See CI-04 remediation.

---

#### CI-SEC-02: No Security Scanning in juniper-deploy

**Approach A — Add Basic Scanning**:
- *Implementation*: Add `shellcheck` to CI for shell scripts. Add `bandit` scan for Python helpers. Add container image scanning with Trivy.
- *Strengths*: Basic security hygiene.
- *Weaknesses*: May produce false positives.
- *Risks*: None.
- *Guardrails*: Start with warning-only mode.

**Recommended**: Approach A.

---

*End of Agent E partial — 27 dashboard + 16 WebSocket + 5 infrastructure + 17 CasCor + 29 deploy + 9 data perf/roadmap + 17 testing/CI = ~120 items covered*
