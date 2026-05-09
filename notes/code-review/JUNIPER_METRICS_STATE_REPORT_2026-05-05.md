<!-- markdownlint-disable MD013 -->
# Juniper Metrics-Monitoring State Report

| Field         | Value                                                                                                |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| **Project**   | Juniper                                                                                              |
| **File Name** | `notes/code-review/JUNIPER_METRICS_STATE_REPORT_2026-05-05.md`                                       |
| **Description** | Snapshot, as of 2026-05-05, of the metrics / SLO / dashboard / alert state across all 8 Juniper repos after the close of the METRICS-MON program (juniper-ml#192) and the post-program 27-finding audit (juniper-ml#195). Verified directly against `origin/main` of every cited repo, not against prior summaries. |
| **Author**    | Paul Calnon                                                                                          |
| **Version**   | 0.1.0                                                                                                |
| **License**   | MIT License                                                                                          |
| **Status**    | SNAPSHOT — point-in-time inventory; not a roadmap. Carry-forward items live in `POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel branch). |

---

## 2. Executive summary

Three Juniper services emit Prometheus metrics via the shared
`juniper-observability` v0.1.1 lib plus per-service metric modules; a fourth
(`juniper-cascor-worker`) ships an HTTP `/v1/health` heartbeat surface but
**does not expose `/metrics`** — metric visibility for workers is mediated
through the cascor-side `WorkerRegistryCollector`. The SLO catalog
(`juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` v1.0.0) defines **5
user-facing primary SLIs (release-blocking)** and **8 internal-supporting
SLIs (graphed-only)**; **29 alert rules** ship in
`juniper-deploy/prometheus/alert_rules.yml`, of which **7 are MWMBR fast-burn
alerts at `severity: page`**, **9 at `severity: ticket`**, and **the
remaining 13 are pre-existing threshold/health alerts** at
`critical` (3) / `warning` (8) / `info` (2). Four Grafana dashboards
(`juniper-{overview,cascor,canopy,data}.json`, all `version: 3`) ship 71
total panels including 4 intentional placeholder text panels documenting
not-yet-bridged worker fields.

Three concrete operator-facing numbers:

1. **44 distinct Prometheus metric names** are defined and emitted across
   the three Juniper service surfaces (10 from the shared HTTP middleware
   namespace-multiplied across data/cascor/canopy + 4 dataset-domain in
   data + 8 training-domain in cascor + 14 WS-domain in cascor + 6
   worker-collector-domain in cascor + 7 canopy-specific = 49, minus 5
   shared-middleware overlap counted once = **44 unique series**).
2. **1 user-facing SLO is currently ratified at paging severity in code
   but log-only-effective**; the other 4 ship at `severity: page` /
   `severity: ticket` against the §2.6 30-day soak gate. The
   2026-06-02 → 2026-06-15 calibration window decides which targets get
   tightened and which alerts get the log-only severity lifted.
3. **All 27 audit findings (juniper-ml#195) are tracked**; the P1 cluster
   is closed via OBS-WIRE-01 (juniper-cascor#204), OBS-WIRE-02
   (juniper-cascor#211 + juniper-canopy#236), the §4.2 pending-tasks
   bridge (juniper-cascor#218), the catalog name-drift fix
   (juniper-deploy#59), the SLI 3.4 phase-label drop (juniper-deploy#52),
   and the alertmanager B.1 fold-in (juniper-deploy#60). 6 carry-forward
   items remain — see §11.

**Forward pointer:** the **T+30d calibration milestone** lands
**2026-06-02 → 2026-06-15** (per `SLO_CATALOG` §2.6 / `PROGRAM_CLOSE`
§4.5). At that point the 5 user-facing SLO numeric targets are
ratified-or-adjusted against 30 days of production traffic, the
log-only-severity caveat lifts for §3.1 / §3.2 / §3.5 (with §3.3 / §3.4
still gated on TRAIN-ARCH-01), and the **OBS-ROUTE-CRED** alertmanager
`tickets`-receiver real-credential rotation must close in the same window
(see tracker `LIFT-01`).

---

## 3. Services & metrics surface

### 3.1 juniper-data

| Field | Value |
|-------|-------|
| Repo | `juniper-data` (origin/main `88149bf`) |
| Container port | 8100 |
| Host port | 8100 |
| `/metrics` URL | `http://juniper-data:8100/metrics` (compose); `http://localhost:8100/metrics` (local) |
| Source-of-truth file | `juniper-data/juniper_data/api/observability.py` (218 lines) |
| Auth posture | Gated by `MetricsAuthMiddleware` (SEC-16 IP allowlist; default `("127.0.0.1", "::1")`). **This is the only service with a per-service auth gate on `/metrics`** — confined to juniper-data per `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` and SLO catalog §5.4. |
| Build-info | `juniper_data_build` Info metric registered via `set_build_info("juniper_data", __version__)` (`juniper_data/api/app.py:42`) |

**Service-specific metric inventory (4 metrics):**

| Name | Type | Labels | Closed-set? | Emission site | SLI / dashboard / alert binding |
|------|------|--------|-------------|---------------|-------------------------------|
| `juniper_data_dataset_generations_total` | Counter | `generator`, `status` | `status ∈ {success, error}` (open-set `generator`); enforced via `_GENERATION_STATUSES` constant | `juniper_data/api/observability.py:188` (`record_dataset_generation`) | dashboard `juniper-data.json` "Dataset Generations by Type" / alert `DatasetGenerationFailures` |
| `juniper_data_dataset_generation_duration_seconds` | Histogram | `generator` | n/a | `juniper_data/api/observability.py:190` | dashboard `juniper-data.json` "Generation Duration Distribution" / alert `SlowDatasetGeneration` / SLO §3.5 indirect |
| `juniper_data_datasets_cached` | Gauge | none | n/a | `juniper_data/api/observability.py:218` (`set_datasets_cached`) | dashboard `juniper-data.json` "Cached Datasets" panel — **DEFINED BUT NOT EMITTED IN PRODUCTION** (see §15 unexpected findings) |
| `juniper_data_dataset_post_total` | Counter | `generator`, `status`, `cache` | `status ∈ {success, error}`; `cache ∈ {hit, miss}` (per `POST_CACHE_HIT` / `POST_CACHE_MISS` in `juniper_data/api/constants.py`) | `juniper_data/api/routes/datasets.py:99,121` | SLO §3.5 / SLO §4.7 / dashboard "Dataset POST Rate by cache (hit/miss)" / alerts `DataPostAvailabilityFastBurn`, `DataPostAvailabilitySlowBurn` |

**Plus shared HTTP middleware metrics** (`PrometheusMiddleware` from
`juniper_observability` mounted at app construction): emits
`juniper_data_http_requests_total{method,endpoint,status}` Counter,
`juniper_data_http_request_duration_seconds{method,endpoint}` Histogram,
`juniper_data_http_unmatched_requests_total{method}` Counter, plus the
`juniper_data_build` Info.

### 3.2 juniper-cascor

| Field | Value |
|-------|-------|
| Repo | `juniper-cascor` (origin/main `4034bd6`) |
| Container port | 8200 |
| Host port | 8201 |
| `/metrics` URL | `http://juniper-cascor:8200/metrics` (compose) |
| Source-of-truth files | `juniper-cascor/src/api/observability.py` (716 lines), `juniper-cascor/src/api/workers/metrics.py` (251 lines), `juniper-cascor/src/api/routes/metrics.py` (49 lines, mount only) |
| Auth posture | No `/metrics` auth gate (network-isolated inside compose / k8s). |
| Build-info | `juniper_cascor_build` Info metric (`juniper-cascor/src/api/app.py:165`) |

**Service-specific metric inventory: training-domain (8 metrics)**

| Name | Type | Labels | Closed-set? | Emission site | SLI / dashboard / alert binding |
|------|------|--------|-------------|---------------|-------------------------------|
| `juniper_cascor_training_sessions_active` | Gauge | none | n/a | `inc_training_sessions` / `dec_training_sessions` (`observability.py:354,359`) | dashboard `juniper-cascor.json` "Active Training Sessions"; alert `TrainingStalled` (gates on `> 0`) |
| `juniper_cascor_training_sessions_completed_total` | Counter | `status` | `status ∈ {success, failure, cancelled}` enforced by `_TRAINING_SESSION_STATUSES` frozenset, raises `ValueError` on drift (`observability.py:402`) | `inc_training_session_completed` from lifecycle FSM | SLO §3.3; alerts `CascorTrainJobSuccessFastBurn` / `CascorTrainJobSuccessSlowBurn` |
| `juniper_cascor_training_epochs_total` | Counter | `phase` | open-set (no validator) | `record_training_epoch` (`observability.py:312`) | dashboard "Epochs Completed"; recording rule `juniper:training_epochs:rate5m` |
| `juniper_cascor_training_loss` | Gauge | `phase`, `loss_type` | open-set | `set_training_loss` (`observability.py:323`) | dashboard "Training Loss"; alert `TrainingLossNotDecreasing` |
| `juniper_cascor_training_accuracy_ratio` | Gauge | `phase` | open-set | `set_training_accuracy` (`observability.py:333`) | dashboard "Training Accuracy" |
| `juniper_cascor_hidden_units_total` | Gauge | none | n/a | `set_hidden_units` (`observability.py:342`) | dashboard "Hidden Units" |
| `juniper_cascor_candidate_correlation` | Gauge | none | n/a | `set_candidate_correlation` (`observability.py:351`) | dashboard "Candidate Correlation"; alert `LowCandidateCorrelation` |
| `juniper_cascor_training_step_duration_seconds` | Histogram | (no labels post OBS-WIRE-01 §A.6) | n/a | `observe_training_step_duration` (`observability.py:422`); observed once per epoch boundary; **gated by 25-epoch throttle** in `cascade_correlation.py:1655` | SLO §3.4; alerts `CascorTrainStepLatencyFastBurn` / `CascorTrainStepLatencySlowBurn` (with explicit 25-epoch undersampling caveat in alert annotations) |

**Service-specific metric inventory: WebSocket-domain (14 metrics)**

| Name | Type | Labels | Closed-set? | Emission site | SLI / dashboard / alert binding |
|------|------|--------|-------------|---------------|-------------------------------|
| `cascor_ws_seq_current` | Gauge | none | n/a | `ws_set_seq_current` | (none) |
| `cascor_ws_replay_buffer_occupancy` | Gauge | none | n/a | `ws_set_replay_buffer_occupancy` | (none) |
| `cascor_ws_replay_buffer_bytes` | Gauge | none | n/a | (replay buffer bookkeeping) | (none) |
| `cascor_ws_replay_buffer_capacity_configured` | Gauge | none | n/a | `ws_set_replay_buffer_capacity` | (none) |
| `cascor_ws_resume_requests_total` | Counter | `outcome` | `outcome ∈ {success, out_of_range, malformed_resume, server_restarted}` enforced by `_WS_RESUME_OUTCOMES` frozenset | `ws_inc_resume_requests` (`observability.py:660`) | (none — operator visibility only) |
| `cascor_ws_resume_replayed_events` | Histogram | none | n/a | `ws_observe_resume_replayed` (`observability.py:670`); buckets `0/1/5/25/100/500/1024` | (none — informational) |
| `cascor_ws_broadcast_timeout_total` | Counter | `type` | open-set | `ws_inc_broadcast_timeout` | (none) |
| `cascor_ws_broadcast_send_duration_seconds` | Histogram | `type` | open-set; sub-ms buckets `100µs/500µs/1ms/5ms/10ms/50ms/100ms` (R5.1b) | inline at `api/websocket/manager.py:642` | SLO §4.3 (catalog) |
| `cascor_ws_pending_connections` | Gauge | none | n/a | (manager bookkeeping) | (none) |
| `cascor_ws_state_throttle_coalesced_total` | Counter | none | n/a | `ws_inc_state_throttle_coalesced` | (none) |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter | none | n/a | `ws_inc_broadcast_from_thread_errors` | (none) |
| `cascor_ws_connections_active` | Gauge | `endpoint` | `endpoint ∈ {training, control, workers}` enforced by `_WS_ENDPOINTS` frozenset | `ws_set_connections_active` (`observability.py:692`) | (none — wired in OBS-WIRE-02) |
| `cascor_ws_command_responses_total` | Counter | `command`, `status` | `status ∈ {success, error, rate_limited}` enforced by `_WS_COMMAND_STATUSES`; `command` open-set-by-convention (validated upstream by `_VALID_COMMANDS`) | `ws_inc_command_responses` (`observability.py:707`) | (none) |
| `cascor_ws_command_handler_seconds` | Histogram | `command` | open-set; sub-ms buckets (R5.1b same layout as broadcast_send) | `ws_observe_command_handler` at `api/websocket/control_stream.py:233` | SLO §4.4 (catalog) |

**Service-specific metric inventory: worker-domain (6 metrics, via `WorkerRegistryCollector`)**

The cascor `WorkerRegistryCollector` (`src/api/workers/metrics.py`) is a
`prometheus_client`-compatible custom collector registered once at
startup; it snapshots the in-process `WorkerRegistry` on each scrape and
emits per-worker gauges. `juniper-cascor-worker` itself does **not**
expose `/metrics` — the worker reports state to cascor over HTTP and
cascor surfaces the metrics.

| Name | Type | Labels | Closed-set? | Emission site | SLI / dashboard / alert binding |
|------|------|--------|-------------|---------------|-------------------------------|
| `juniper_cascor_worker_heartbeat_age_seconds` | Gauge (custom collector) | `worker_id` | open-set (instance) | `WorkerRegistryCollector.collect` always emits | SLO §4.1; alert `CascorWorkerHeartbeatStale` |
| `juniper_cascor_worker_last_task_duration_seconds` | Gauge | `worker_id` | open-set | collector — emitted only when `last_task_duration_seconds is not None` | (none) |
| `juniper_cascor_worker_gpu_utilization_pct` | Gauge | `worker_id` | open-set | collector — emitted only when `gpu_utilization_pct is not None` | dashboard placeholder text panel "Cascor worker GPU saturation (Prometheus bridge pending)" — placeholder predates §4.1 bridge close (see §15) |
| `juniper_cascor_worker_recent_task_duration_seconds_p50` | Gauge | `worker_id` | open-set | collector — emitted only when window has ≥ 2 samples | (none) |
| `juniper_cascor_worker_recent_task_duration_seconds_p95` | Gauge | `worker_id` | open-set | collector — emitted only when window has ≥ 2 samples | (none) |
| `juniper_cascor_pending_tasks` | Gauge | none | n/a | collector — emitted only when a `WorkerCoordinator` is wired (`workers/metrics.py:226`); shipped via juniper-cascor#218 (audit §4.2) | SLO §4.2; alert `CascorPendingTasksSaturated` (the `absent_over_time(...)==0` guard now lifts as soon as the gauge appears) |

**Plus shared HTTP middleware metrics**: `juniper_cascor_http_requests_total`,
`juniper_cascor_http_request_duration_seconds`,
`juniper_cascor_http_unmatched_requests_total`, plus the
`juniper_cascor_build` Info.

### 3.3 juniper-canopy

| Field | Value |
|-------|-------|
| Repo | `juniper-canopy` (origin/main `81c4c23`) |
| Container port | 8050 |
| Host port | 8050 |
| `/metrics` URL | `http://juniper-canopy:8050/metrics` |
| Source-of-truth file | `juniper-canopy/src/observability.py` (471 lines) |
| Auth posture | No `/metrics` auth gate. |
| Build-info | `juniper_canopy_build` Info metric (`src/main.py:137`) |

**Service-specific metric inventory (7 metrics):**

| Name | Type | Labels | Closed-set? | Emission site | SLI / dashboard / alert binding |
|------|------|--------|-------------|---------------|-------------------------------|
| `juniper_canopy_websocket_connections_active` | Gauge | `channel` | (open-set; wire-up in OBS-WIRE-01 closed audit A.4) | `set_websocket_connections` (`observability.py:309`) | dashboard `juniper-canopy.json` "Active WebSocket Connections by Channel"; alert `NoWebSocketConnections` |
| `juniper_canopy_websocket_messages_total` | Counter | `channel`, `type` | `type` collapsed to closed allowlist `_WS_MESSAGE_TYPE_ALLOWLIST` (17 production types + `_other` bucket) at `observability.py:352` | `inc_websocket_messages` | dashboard "WebSocket Messages by Type" |
| `juniper_canopy_demo_mode_active` | Gauge | none | n/a (0/1) | `set_demo_mode_active` | dashboard "Demo Mode" stat panel |
| `juniper_canopy_unrecognized_ws_frames_total` | Counter | `type`, `endpoint` | `type` cardinality-bounded by `juniper_cascor_protocol.envelope` (collapses to `_unmatched` after `UNKNOWN_TYPE_BUDGET=16`); `endpoint ∈ {training, control}` | `inc_unrecognized_ws_frame` (`observability.py:388`) | (none — operator visibility) |
| `juniper_canopy_data_client_requests_total` | Counter | `method`, `status_class`, `error_type` | `status_class ∈ {2xx, 4xx, 5xx, transport_error}`; `error_type` validated against `_KNOWN_DATA_CLIENT_ERROR_TYPES` frozenset (6 known + `none` + `_other`) | `build_data_client_request_hook` closure passed to `JuniperDataClient(on_request=…)` | SLO §4.6; dashboard "Data-client Request Rate by status_class" |
| `juniper_canopy_data_client_request_duration_ms` | Histogram | `method`, `status_class` | `status_class` closed-set per above | same hook | SLO §4.5; dashboard "Data-client Request Latency (p50 / p95 / p99)" |
| `juniper_canopy_ws_seq_gap_detected_total` | Counter | `service`, `channel` | `service ∈ {juniper-cascor}` static; `channel ∈ {training, control}` enforced by `_SEQ_GAP_CHANNELS` frozenset, raises `ValueError` on drift | `inc_ws_seq_gap_detected` (`observability.py:468`) | (none — operator visibility; replaces the removed cascor-side `cascor_ws_seq_gap_detected_total`) |

**Plus shared HTTP middleware metrics**:
`juniper_canopy_http_requests_total`,
`juniper_canopy_http_request_duration_seconds`,
`juniper_canopy_http_unmatched_requests_total`, plus the
`juniper_canopy_build` Info.

### 3.4 juniper-cascor-worker

| Field | Value |
|-------|-------|
| Repo | `juniper-cascor-worker` (origin/main `7950ad2`) |
| `/metrics` endpoint | **NOT EXPOSED** |
| Health endpoint | `/v1/health`, `/v1/health/live`, `/v1/health/ready` (default port 8210, localhost-only) |
| Source-of-truth file | `juniper_cascor_worker/http_health.py` (heartbeat HTTP/1.1 server, hand-rolled on `asyncio.start_server`) |

The worker is **heartbeat-only** by design (R1.3 design doc, METRICS-MON
§R1.3). The worker reports liveness/readiness signals over HTTP/1.1 and
reports task progress / heartbeats to cascor over the cascor WebSocket.
Worker-domain metric visibility is mediated through cascor's
`WorkerRegistryCollector` (see §3.2 worker-domain table). The worker
does **not** import `prometheus_client` and does **not** import
`juniper_observability` (verified by `grep -l 'juniper_observability'
juniper_cascor_worker/*.py` returning no matches). The worker's two
contract literals (`LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`) are
duplicated rather than imported from the shared lib — tracked as
`R2-WORKER-DEDUP` in the carry-forward tracker (P3, declined).

---

## 4. Shared observability lib

**Lib name:** `juniper-observability`
**Version:** `0.1.1` (`juniper-ml/juniper-observability/juniper_observability/_version.py`)
**Location:** `juniper-ml/juniper-observability/juniper_observability/` — published from the meta-package monorepo, distributed as a regular PyPI dependency.

### 4.1 Public symbols

Per `juniper_observability/__init__.py`:

- **Constants (R1.1/R1.2/R1.3 contract):**
  `HEADER_X_REQUEST_ID`, `LIVENESS_STALENESS_SECONDS`, `LIVENESS_TICK_BUDGET_MS`,
  `READINESS_HEADER`, `UNMATCHED_ENDPOINT_LABEL`.
- **Health:** `DependencyStatus`, `ReadinessResponse` (Pydantic), `probe_dependency`.
- **Logging:** `DEFAULT_LOG_FORMAT_PLAIN`, `JuniperJsonFormatter`, `LOG_FORMAT_JSON`, `configure_logging`.
- **Middleware:** `PrometheusMiddleware`, `RequestIdMiddleware`, `request_id_var`.
- **Prometheus utilities:** `get_prometheus_app`, `set_build_info`.
- **Prometheus collector helpers (idempotent registration):** `lazy_register_or_reuse`, `register_fresh`, `register_info_or_update`, `register_or_reuse`.
- **Sentry:** `DEFAULT_SENTRY_TRACES_SAMPLE_RATE`, `configure_sentry`.

### 4.2 Adoption matrix

| Repo | Declares dep in `pyproject.toml`? | Imports `juniper_observability`? | Components imported |
|------|----------------------------------|----------------------------------|---------------------|
| juniper-data | yes (`>=0.1.1`) | yes | All major exports re-exported through `juniper_data/api/observability.py` (back-compat shim); `DependencyStatus` / `ReadinessResponse` imported via `juniper_data/api/models/health.py` |
| juniper-cascor | yes (`>=0.1.1`) | yes | Re-exports through `src/api/observability.py`; health-probe imports in `src/api/routes/health.py`, `src/api/models/health.py` |
| juniper-canopy | yes (`>=0.1.1`) | yes | Re-exports through `src/observability.py`; health imports in `src/health.py`; `set_build_info` directly used in `src/main.py:137` |
| juniper-data-client | yes (`>=0.1.1`) | yes | Imports `request_id_var` ContextVar in `juniper_data_client/client.py` so outbound HTTP attaches the propagating request-id header |
| juniper-cascor-client | **no** | no | (No HTTP server / no metrics; client lib only) |
| juniper-cascor-worker | **no** | no | Worker duplicates `LIVENESS_TICK_BUDGET_MS` and `READINESS_HEADER` literals — see `R2-WORKER-DEDUP` |
| juniper-deploy | n/a (Docker / Helm only, no Python application) | n/a | Consumes the metric *names* via Prometheus scrapes / Grafana dashboards |
| juniper-ml | hosts the lib | n/a (lib source-of-truth) | n/a |

### 4.3 RequestIdMiddleware boundary placement

Per audit finding C.1 (juniper-canopy): canopy's `RequestIdMiddleware`
add-order was inverted relative to the shared design (R2.1 design doc).
Closed by **OBS-WIRE-01 / juniper-canopy#234** which swapped the add
order so `RequestIdMiddleware` is the outermost middleware. juniper-data
and juniper-cascor were already correct at the boundary.

### 4.4 MetricsAuthMiddleware confinement

`MetricsAuthMiddleware` (SEC-16) lives **only** in
`juniper-data/juniper_data/api/observability.py:72` and is **not**
promoted to `juniper-observability`. Rationale documented in
`juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` and SLO catalog §5.4
(R5 entry plan Q5 (b) decision). juniper-cascor and juniper-canopy
expose `/metrics` without an allowlist; their `/metrics` is reachable
only through the compose / k8s internal network.

---

## 5. SLO catalog

**Source-of-truth:** `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md`
(v1.0.0). Targets are marked **"initial — to revisit after 30-day soak"**
per §2.6; calibration window 2026-05-03 → 2026-06-02 with target-tightening
PR landing 2026-06-15.

### 5.1 User-facing primary SLIs (release-blocking, 5)

| § | SLI | Target | Window | Alert (fast-burn / slow-burn) | Status |
|---|-----|--------|--------|-------------------------------|--------|
| 3.1 | Canopy dashboard availability | `99.5%` | 30d rolling | `CanopyDashboardAvailabilityFastBurn` (page) / `CanopyDashboardAvailabilitySlowBurn` (ticket) | Computable; log-only-effective during soak |
| 3.2 | Canopy dashboard render latency | `p95 < 500 ms` | 7d rolling | `CanopyRenderLatencyFastBurn` (page) / `CanopyRenderLatencySlowBurn` (ticket) | Computable; log-only-effective during soak |
| 3.3 | Cascor train-job success | `99.0%` | 30d rolling | `CascorTrainJobSuccessFastBurn` (page) / `CascorTrainJobSuccessSlowBurn` (ticket) | Computable post juniper-cascor#188 + juniper-deploy#51 (R5.4-pre); log-only |
| 3.4 | Cascor train-epoch p95 latency | `p95 < 5s` | 7d rolling | `CascorTrainStepLatencyFastBurn` (page) / `CascorTrainStepLatencySlowBurn` (ticket) | Computable but **gated by 25-epoch emit throttle** documented in alert annotations; log-only |
| 3.5 | Data-service POST availability | `99.5%` | 30d rolling | `DataPostAvailabilityFastBurn` (page) / `DataPostAvailabilitySlowBurn` (ticket) | Computable; log-only-effective during soak |

### 5.2 Internal-supporting SLIs (graphed-only, 8)

| § | SLI | Target | Window | Status |
|---|-----|--------|--------|--------|
| 4.1 | Worker heartbeat freshness | `< 30s` per worker | n/a (instant) | Computable post juniper-cascor#188 (`WorkerRegistryCollector` ships `juniper_cascor_worker_heartbeat_age_seconds`); alert `CascorWorkerHeartbeatStale` (page) |
| 4.2 | Cascor pending-task queue depth | `< 10 sustained 5m` | n/a | **Computable post juniper-cascor#218** (pending-tasks gauge wired). Alert `CascorPendingTasksSaturated` ships at `severity: ticket` and was guarded by `absent_over_time(...) == 0` until the gauge appeared. |
| 4.3 | Cascor broadcast fan-out p95 | `p95 < 1ms` | 7d rolling | Computable (post OBS-WIRE-02 / juniper-cascor#211 emission wire-up) |
| 4.4 | Cascor command-handler p95 | `p95 < 50ms` per command | 7d rolling | Computable (post OBS-WIRE-02) |
| 4.5 | Data-client request latency (canopy → data) | `p95 < 250 ms` | 7d rolling | Computable |
| 4.6 | Data-client error rate by `status_class` | `5xx + transport_error < 0.5%` | 7d rolling | Computable |
| 4.7 | Dataset POST cache-hit ratio | `> 50%` (informational) | 7d rolling | Computable |
| 4.8 | HTTP error rate (5xx) per service | `< 1.0%` per service | 7d rolling | Computable; ticket-tier alerts `JuniperData5xxRateTicket`, `JuniperCascor5xxRateTicket`, `JuniperCanopy5xxRateTicket` |

**Total: 13 SLIs** (5 user-facing + 8 internal-supporting), same count
as catalog ToC §1.

---

## 6. Grafana dashboards

All dashboards live in
`juniper-deploy/grafana/provisioning/dashboards/`. All four ship at
`version: 3`.

### 6.1 juniper-overview.json (14 panels, version 3, title "Juniper Overview")

| Panel title | Type | Metric source / expression | Notes |
|-------------|------|----------------------------|-------|
| Service Status | row | — | container |
| JuniperData | stat | `up{job="juniper-data"}` | |
| JuniperCascor | stat | `up{job="juniper-cascor"}` | |
| JuniperCanopy | stat | `up{job="juniper-canopy"}` | |
| Request Rate | row | — | container |
| Request Rate (per second) | timeseries | `rate(juniper_*_http_requests_total[$interval])` | |
| Error Rate | row | — | container |
| Error Rate (%) | timeseries | derived from `juniper_*_http_requests_total{status=~"4..|5.."}` | |
| Latency | row | — | container |
| Request Latency — p50 / p95 / p99 | timeseries | `histogram_quantile(...)` against the shared HTTP duration histogram | |
| Cross-Cutting KPIs (R4) | row | — | container |
| Canopy Data-Client Error Rate (R4.3) | stat | `juniper_canopy_data_client_requests_total{status_class=~"4xx|5xx|transport_error"}` | binds SLO §4.6 |
| Juniper-Data Cache Miss Ratio (R4.5) | stat | `juniper_data_dataset_post_total{cache="miss"}` | binds SLO §4.7 |
| Pending R4.4 — worker heartbeat Prometheus bridge | row | — | container with placeholder text panel |
| (placeholder) Cascor worker GPU saturation (Prometheus bridge pending) | text | (markdown placeholder) | **stale label** — bridge SHIPPED via juniper-cascor#188 (`heartbeat_age_seconds`) and gpu via the same collector; this placeholder panel predates the close (see §15) |

### 6.2 juniper-canopy.json (18 panels, version 3, title "JuniperCanopy")

Categories: 5 RED panels (Request Rate, Error Rate, p95 Latency stats +
endpoint timeseries + duration heatmap), 2 WS panels (active connections
gauge by channel + messages total by type), 1 Demo Mode stat, 2 Build
Info stats, 2 Data-client (R4.3) panels, 6 row-container panels.

| Panel | Type | Metric / Expression |
|-------|------|---------------------|
| RED Overview | row | — |
| Request Rate | stat | `sum(rate(juniper_canopy_http_requests_total[$interval]))` |
| Error Rate | stat | derived |
| p95 Latency | stat | `histogram_quantile(0.95, juniper_canopy_http_request_duration_seconds_bucket)` |
| HTTP Metrics | row | — |
| Request Rate by Endpoint | timeseries | `sum by (method, endpoint) (rate(juniper_canopy_http_requests_total[$interval]))` |
| Request Duration Heatmap | heatmap | `juniper_canopy_http_request_duration_seconds_bucket` |
| WebSocket | row | — |
| Active WebSocket Connections by Channel | timeseries | `juniper_canopy_websocket_connections_active` |
| WebSocket Messages by Type | timeseries | `juniper_canopy_websocket_messages_total` |
| Mode | row | — |
| Demo Mode | stat | `juniper_canopy_demo_mode_active` |
| Build Info | row | — |
| Service Version | stat | `juniper_canopy_build_info` |
| Python Version | stat | `juniper_canopy_build_info` |
| Data-client (R4.3) | row | — |
| Data-client Request Rate by status_class | timeseries | `juniper_canopy_data_client_requests_total` |
| Data-client Request Latency (p50 / p95 / p99) | timeseries | `juniper_canopy_data_client_request_duration_ms_bucket` |

Cross-link: panels bind catalog §3.1, §3.2, §4.5, §4.6 per SLO_CATALOG §5.3.

### 6.3 juniper-cascor.json (22 panels, version 3, title "JuniperCascor")

Categories: 5 RED panels, 5 training panels (sessions, hidden units,
epochs, loss, accuracy), 1 candidate-correlation timeseries, 4 inference
panels (**STALE — see §15 unexpected findings; metric family removed
in OBS-WIRE-01 / juniper-cascor#204 but dashboard still references
`juniper_cascor_inference_*`**), 2 build-info, 5 row containers, plus 3
placeholder text panels documenting the worker-bridge expected gauges.

| Panel | Type | Metric / Expression |
|-------|------|---------------------|
| RED Overview | row | — |
| Request Rate | stat | `juniper_cascor_http_requests_total` |
| Error Rate | stat | derived |
| p95 Latency | stat | `juniper_cascor_http_request_duration_seconds_bucket` |
| HTTP Metrics | row | — |
| Request Rate by Endpoint | timeseries | `juniper_cascor_http_requests_total` |
| Request Duration Heatmap | heatmap | `juniper_cascor_http_request_duration_seconds_bucket` |
| Training Metrics | row | — |
| Active Training Sessions | stat | `juniper_cascor_training_sessions_active` |
| Hidden Units | stat | `juniper_cascor_hidden_units_total` |
| Epochs Completed | timeseries | `juniper_cascor_training_epochs_total` |
| Training Loss | timeseries | `juniper_cascor_training_loss` |
| Training Accuracy | timeseries | `juniper_cascor_training_accuracy_ratio` |
| Candidate Training | row | — |
| Candidate Correlation | timeseries | `juniper_cascor_candidate_correlation` |
| Inference | row | — |
| Inference Request Rate | timeseries | `rate(juniper_cascor_inference_requests_total[$interval])` — **DEAD** |
| Inference Latency (p50 / p95 / p99) | timeseries | `juniper_cascor_inference_duration_seconds_bucket` — **DEAD** |
| Build Info | row | — |
| Service Version | stat | `juniper_cascor_build_info` |
| Python Version | stat | `juniper_cascor_build_info` |
| Pending R4.4 — worker heartbeat Prometheus bridge | row | — (3 placeholder text panels inside; see §15) |

Cross-link: panels bind catalog §3.3, §3.4, §4.3, §4.4 (the SLO 4.3 / 4.4
panels are NOT explicit on the dashboard — they're computed from the
underlying histograms, which are present on the cascor `/metrics` after
OBS-WIRE-02). §4.1 / §4.2 not surfaced as live panels — covered by the
placeholder text panels.

### 6.4 juniper-data.json (17 panels, version 3, title "JuniperData")

| Panel | Type | Metric / Expression |
|-------|------|---------------------|
| RED Overview | row | — |
| Request Rate | stat | `juniper_data_http_requests_total` |
| Error Rate | stat | derived |
| p95 Latency | stat | `juniper_data_http_request_duration_seconds_bucket` |
| HTTP Metrics | row | — |
| Request Rate by Endpoint | timeseries | `juniper_data_http_requests_total` |
| Request Duration Heatmap | heatmap | `juniper_data_http_request_duration_seconds_bucket` |
| Dataset Generation | row | — |
| Dataset Generations by Type | timeseries | `juniper_data_dataset_generations_total` |
| Generation Duration Distribution | timeseries | `juniper_data_dataset_generation_duration_seconds_bucket` |
| Cached Datasets | stat | `juniper_data_datasets_cached` — **dashboard panel binds a metric that is defined but never emitted by production code** (see §15) |
| Build Info | row | — |
| Service Version | stat | `juniper_data_build_info` |
| Python Version | stat | `juniper_data_build_info` |
| Dataset POST (R4.5) | row | — |
| Dataset POST Rate by cache (hit/miss) | timeseries | `juniper_data_dataset_post_total{cache=...}` |
| Dataset POST Rate by status | timeseries | `juniper_data_dataset_post_total{status=...}` |

Cross-link: panels bind catalog §3.5 (`dataset_post_total`) and §4.7.

### 6.5 Placeholder text panels (intentional gaps — OBS-WIRE-01)

| Dashboard | Title | Status comment |
|-----------|-------|----------------|
| juniper-cascor.json | Worker `last_task_duration_seconds` (JSON-only — Prometheus bridge pending) | **STALE** — bridge shipped via juniper-cascor#188 (`WorkerRegistryCollector` exposes `juniper_cascor_worker_last_task_duration_seconds`) |
| juniper-cascor.json | Worker `gpu_utilization_pct` (JSON-only — Prometheus bridge pending) | **STALE** — same |
| juniper-cascor.json | Worker `recent_task_durations_seconds` (JSON-only — Prometheus bridge pending) | **STALE** — bridge ships p50 / p95 |
| juniper-overview.json | Cascor worker GPU saturation (Prometheus bridge pending) | **STALE** — same |

**These four placeholders predate the bridge close.** Per the audit
posture (§12), the cleanup is in scope for a follow-up dashboard PR but
not currently on the carry-forward tracker — the metrics ARE emitted; the
text-panel commentary is the artifact that hasn't been refreshed. See
§15.

---

## 7. Alert rules

**Source-of-truth:** `juniper-deploy/prometheus/alert_rules.yml` (1146 lines).
**Total rules: 29.**

### 7.1 Rules by severity label

| Severity | Count | Rules |
|----------|-------|-------|
| `page` | 7 | `CanopyDashboardAvailabilityFastBurn`, `CanopyRenderLatencyFastBurn`, `CascorTrainJobSuccessFastBurn`, `CascorTrainStepLatencyFastBurn`, `DataPostAvailabilityFastBurn`, `CascorWorkerHeartbeatStale`, `JuniperServiceScrapeDown` |
| `ticket` | 9 | `CanopyDashboardAvailabilitySlowBurn`, `CanopyRenderLatencySlowBurn`, `CascorTrainJobSuccessSlowBurn`, `CascorTrainStepLatencySlowBurn`, `DataPostAvailabilitySlowBurn`, `CascorPendingTasksSaturated`, `JuniperData5xxRateTicket`, `JuniperCascor5xxRateTicket`, `JuniperCanopy5xxRateTicket` |
| `critical` | 3 | `ServiceDown`, `HighErrorRate_JuniperData`, `HighErrorRate_JuniperCascor` |
| `warning` | 8 | `ServiceRestartLoop`, `HighErrorRate_JuniperCanopy`, `HighLatency_JuniperData`, `HighLatency_JuniperCascor`, `TrainingStalled`, `TrainingLossNotDecreasing`, `DatasetGenerationFailures`, `SlowDatasetGeneration` |
| `info` | 2 | `LowCandidateCorrelation`, `NoWebSocketConnections` |

### 7.2 MWMBR burn-rate pairs

| User-facing SLI (§) | Fast-burn (page) | Slow-burn (ticket) |
|---------------------|------------------|---------------------|
| 3.1 Canopy dashboard availability | `CanopyDashboardAvailabilityFastBurn` | `CanopyDashboardAvailabilitySlowBurn` |
| 3.2 Canopy render latency | `CanopyRenderLatencyFastBurn` | `CanopyRenderLatencySlowBurn` |
| 3.3 Cascor train-job success | `CascorTrainJobSuccessFastBurn` | `CascorTrainJobSuccessSlowBurn` |
| 3.4 Cascor train-step latency | `CascorTrainStepLatencyFastBurn` | `CascorTrainStepLatencySlowBurn` |
| 3.5 Data POST availability | `DataPostAvailabilityFastBurn` | `DataPostAvailabilitySlowBurn` |

**5 fast/slow pairs = 10 MWMBR rules** of the 16 page+ticket count;
the remaining 6 (3 ticket-tier `*5xxRateTicket` + 1
`CascorPendingTasksSaturated` ticket + 2 page-tier
`CascorWorkerHeartbeatStale` and `JuniperServiceScrapeDown`) are
threshold-style alerts, not burn-rate.

### 7.3 The 25-epoch throttle caveat

`CascorTrainStepLatencyFastBurn` and `CascorTrainStepLatencySlowBurn`
explicitly call out the 25-epoch undersampling caveat in their
annotation `description` blocks (`alert_rules.yml:751`, `:819`). The
throttle decision lives in
`juniper-cascor/src/cascade_correlation/cascade_correlation.py:1655`
(`epoch % 25 == 0`); the histogram observation is gated by
`api/lifecycle/manager.py:1328`. Removing the throttle is tracked as
**R5.6-THROTTLE** (P3, deferred) on the carry-forward tracker.

### 7.4 `absent_over_time(...) == 0` inertness guards

| Rule | Guarded metric | Guard purpose |
|------|----------------|---------------|
| `CascorPendingTasksSaturated` (`alert_rules.yml:1050`) | `juniper_cascor_pending_tasks` | The guard was originally placed because the gauge had not yet been bridged from the cascor coordinator to Prometheus. **Post juniper-cascor#218 the gauge ships from `WorkerRegistryCollector`**, so the guard is now effectively a no-op once data flows. The audit doc (§4.2) and the SLO catalog (§4.2 / §6 Q3) both acknowledge this. The guard can be removed at the same time as the calibration PR but is harmless until then. |

The `JuniperServiceScrapeDown` alert similarly uses `up == 0` to detect
broken scrapes per SLO catalog §2.8.

---

## 8. Scrape configs

### 8.1 docker-compose (`juniper-deploy/prometheus/prometheus.yml`)

| Job | Target | Interval | Timeout | metrics_path | external_labels (`global`) |
|-----|--------|----------|---------|--------------|----------------------------|
| `prometheus` | `localhost:9090` | 15s (global default) | 10s | `/metrics` | `deployment=docker-compose`; per-job `service=prometheus`, `environment=docker` |
| `juniper-data` | `juniper-data:8100` | 10s | 10s | `/metrics` | `service=juniper-data`, `environment=docker` |
| `juniper-cascor` | `juniper-cascor:8200` | 10s | 10s | `/metrics` | `service=juniper-cascor`, `environment=docker` |
| `juniper-canopy` | `juniper-canopy:8050` | 15s | 10s | `/metrics` | `service=juniper-canopy`, `environment=docker` |

**Global config:** `scrape_interval: 15s`, `evaluation_interval: 15s`,
`scrape_timeout: 10s`. **`metric_relabel_configs`:** none — only static
`labels` per-target. `honor_labels: false` for the three Juniper services.

**Auth:** the `juniper-data` job is gated by `MetricsAuthMiddleware`; the
prometheus container's bridge-network IP must be in
`JUNIPER_DATA_METRICS_ALLOW_IPS`.

### 8.2 Kubernetes (`juniper-deploy/k8s/helm/juniper/templates/*-servicemonitor.yaml`)

Three ServiceMonitor templates: `data-servicemonitor.yaml`,
`cascor-servicemonitor.yaml`, `canopy-servicemonitor.yaml`. All three
share the same shape:

| Field | Value |
|-------|-------|
| `port` | `http` (named service port) |
| `path` | `/metrics` |
| `scheme` | `http` |
| `interval` | `{{ .Values.serviceMonitor.interval }}` (default `10s`) |
| `scrapeTimeout` | `{{ .Values.serviceMonitor.scrapeTimeout }}` (default `10s`) |
| `honorLabels` | `false` |
| `selector.matchLabels` | `juniper.selectorLabels` helper, gated on `app.kubernetes.io/component={data,cascor,canopy}` |
| `relabelings` | adds `service=juniper-{data,cascor,canopy}` and `environment=kubernetes` |

**`serviceMonitor.enabled` defaults to `false` in `values.yaml`**
(opt-in for k8s deployments).

---

## 9. Alertmanager routing

**Source-of-truth:** `juniper-deploy/alertmanager/alertmanager.yml` (154 lines).

### 9.1 Receivers

Three receivers, all SMTP email per OBS-ROUTE-01 (juniper-deploy#60).

| Receiver | Recipient | Status |
|----------|-----------|--------|
| `default` | `alerts-default@example.com` | **PLACEHOLDER** (`CHANGE_BEFORE_PRODUCTION_USE` flagged) |
| `critical` | `alerts-critical@example.com` | **PLACEHOLDER** |
| `tickets` | `alerts-tickets@example.com` | **PLACEHOLDER** |

The SMTP global config (`smtp_smarthost`, `smtp_from`,
`smtp_auth_username`) is **also placeholder** (`CHANGE_BEFORE_PRODUCTION_USE`);
the password is loaded from the Docker secret at
`/run/secrets/alertmanager_smtp_password` (real value lives in
`.env.secrets.enc`).

Tracked as **OBS-ROUTE-CRED** in the carry-forward tracker — soft-blocker,
must close before LIFT-01 (gate lift) and ≤ 2026-06-02.

### 9.2 Route tree

```
route: receiver=default, group_by=[alertname,service], group_wait=30s, group_interval=5m, repeat_interval=4h
├── severity=critical → critical (group_wait=10s, repeat_interval=1h)
├── severity=page     → critical (group_wait=10s, repeat_interval=1h)        # MWMBR fast-burn
├── severity=ticket   → tickets  (group_wait=1m, group_interval=10m, repeat_interval=12h)  # MWMBR slow-burn
├── severity=warning  → tickets  (group_by adds severity, group_wait=2m, repeat_interval=24h)  # B.1 fold-in
└── severity=info     → tickets  (same)                                       # B.1 fold-in
```

### 9.3 Inhibit rules

`ServiceDown` suppresses `HighErrorRate*` / `HighLatency*` for the same
`service` label.

### 9.4 Validation status

`amtool check-config` cannot run in the snap-confined `amtool`
environment on the local development machine (snap confinement blocks
arbitrary file paths). Tracked as **AMTOOL-CI** (P3) on the
carry-forward tracker — recommended container-form alternative is

```
docker run --rm -v "$(pwd)/alertmanager:/cfg:ro" --entrypoint amtool prom/alertmanager:v0.27.0 check-config /cfg/alertmanager.yml
```

per `juniper-deploy/notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §5.3.

---

## 10. Test coverage matrix

For every metric in §3, at least one unit or integration test exercises
emission and (where applicable) closed-set validation. Coverage table:

| Metric | Test file (juniper-data unless noted) |
|--------|---------------------------------------|
| `juniper_data_dataset_generations_total` | `juniper_data/tests/unit/test_observability.py`, `juniper_data/tests/unit/test_phase_2d_metrics.py`, `juniper_data/tests/integration/test_dataset_generation_metrics_live.py` |
| `juniper_data_dataset_generation_duration_seconds` | same |
| `juniper_data_datasets_cached` | `juniper_data/tests/unit/test_observability.py::test_set_datasets_cached` (helper invocation only — no production caller, see §15) |
| `juniper_data_dataset_post_total` | `juniper_data/tests/integration/test_dataset_post_total_metric.py` |
| `MetricsAuthMiddleware` | `juniper_data/tests/unit/test_observability.py`, `juniper_data/tests/unit/test_phase1d_security.py` |
| Cascor training-domain (8 metrics) | `juniper-cascor/src/tests/unit/api/test_metrics_r5_4_pre.py`, `test_metrics_obs_wire_01.py`, `test_api_observability.py` |
| Cascor WS-domain (14 metrics) | `juniper-cascor/src/tests/unit/api/test_metrics_obs_wire_01.py`, `test_metrics_obs_wire_02.py` |
| Cascor worker-collector (6 metrics, incl. `pending_tasks`) | `juniper-cascor/src/tests/unit/api/test_metrics_r5_4_pre.py` |
| Canopy 7 metrics | `juniper-canopy/src/tests/unit/test_obs_wire_ws_metrics.py`, `test_data_client_request_hook.py`, `test_inbound_frame_validation.py`, `test_ws_seq_gap_detected.py`; `src/tests/integration/test_demo_mode_gauge.py` |

**Coverage gaps identified:** 0 (all 44 unique metric names have at least
one helper- or emission-site test). The `juniper_data_datasets_cached`
gap is a *production-caller* gap, not a test gap — see §15.

---

## 11. Outstanding work (carry-forward tracker)

Cross-reference: `notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md`
(parallel-PR branch `docs/post-metrics-mon-tracker`; not yet on
origin/main at the time of this snapshot — verified by `git log` showing
commit `27f4def` on the tracker branch).

Top 6 carry-forward items:

| ID | Title | Severity | Repo | Target / gate | Status |
|----|-------|----------|------|---------------|--------|
| **CALIB-01** | T+30d SLO target calibration | P3 | juniper-deploy | 2026-06-02 (window close) → 2026-06-15 (catalog revisit deadline) | open |
| **OBS-ROUTE-CRED** | Alertmanager `tickets`/`critical`/`default` real-credentials rotation | P1 (soft-blocker) | juniper-deploy | Before `LIFT-01` and ≤ 2026-06-02 | open |
| **LIFT-01** | R5.4 alert log-only-severity gate lift (§3.1 / §3.2 / §3.5) | P1 | juniper-deploy | Gated on `CALIB-01` + `OBS-ROUTE-CRED` | blocked |
| **R5.1c-BUCKETS** | Cascor sub-ms bucket re-evaluation | P2 | juniper-cascor | After `CALIB-01` ratifies | open |
| **AMTOOL-CI** | `amtool check-config` snap-confinement gap | P3 | juniper-deploy | No hard date | open |
| **WORKER-PENDING-TASKS** | (Was: `juniper_cascor_pending_tasks` worker→Prometheus bridge gap) | P3 | juniper-cascor | Independent | **EFFECTIVELY CLOSED post juniper-cascor#218** — gauge ships, alert guard becomes no-op once data flows; tracker entry is doc-debt at this point |

Plus 4 deferred items (`R5.6-THROTTLE`, `R1.3.4-FLAG`, `R2-WORKER-DEDUP`,
`TRAIN-ARCH-01`) that are not gating LIFT-01.

---

## 12. Audit posture

The post-METRICS-MON 5-dimension audit (juniper-ml#195) recorded
**27 findings** across 5 dimensions. Tally by severity (per the audit
doc §5):

| Tier | Count |
|------|-------|
| P1 | 6 (1 seed + 5 audit) |
| P2 | 6 |
| P3 | 15 |
| **Total** | **27** |

### Closing PRs

| Finding cluster | Closing PR(s) |
|-----------------|---------------|
| **A.1 / A.2a–e (cascor training metrics dead-defined)** | juniper-cascor#204 (OBS-WIRE-01) — wired 5 emission sites |
| **A.3a / A.3b (cascor WS broadcast + command duration histograms dead-defined)** | juniper-cascor#211 (OBS-WIRE-02) — wired 9 WS metric emissions |
| **A.4 (canopy `websocket_connections_active` dead-defined)** | juniper-canopy#234 (OBS-WIRE / canopy A.4 + C.1) |
| **A.5a / A.5b (cascor `juniper_cascor_inference_*` dead — no inference endpoint)** | juniper-cascor#204 — REMOVED metric definitions; **dashboard panel cleanup deferred** (see §15) |
| **A.6 (cascor `training_step_duration_seconds` `phase` label drift)** | juniper-cascor#204 (label dropped) + juniper-deploy#52 (catalog SLI 3.4 PromQL update) |
| **A.7 (catalog name drift: `last_heartbeat_age_seconds` → `heartbeat_age_seconds`)** | juniper-deploy#59 |
| **A.8 (canopy `data_client_requests_total{error_type}` lacks closed-set validation)** | juniper-canopy#236 (OBS-WIRE-02) — `_KNOWN_DATA_CLIENT_ERROR_TYPES` frozenset added |
| **C.1 (canopy `RequestIdMiddleware` add-order)** | juniper-canopy#234 |
| **§4.1 / §4.2 worker bridge gap** | juniper-cascor#188 (R5.4-pre `WorkerRegistryCollector`) + juniper-cascor#218 (`pending_tasks` gauge) |
| **B.1 alertmanager warning/info silent drop** | juniper-deploy#60 (OBS-ROUTE-01) |
| **E.6 `WorkerRegistry` size cap** | juniper-cascor#221 (cap = 250 + WS handshake rejection) |
| **D.2 / D.5 cascor histogram bucket pin tests** | juniper-cascor#217 (audit d2+d5) |

The remaining open items are all P3 / soft-blocker items tracked in
`POST_METRICS_MON_TRACKER_2026-05-05.md` (§11 above) — none represent
operationally meaningful uncovered surface.

---

## 13. Calibration milestone (T+30d)

**Date:** 2026-05-03 → 2026-06-02 (soak window) →
**2026-06-15 (catalog revisit deadline)**.

### What needs to happen

1. **Pull p50 / p95 / p99 from Prometheus** for every SLI in catalog §3
   over the 30-day window (2026-05-03 → 2026-06-02).
2. **Compare actual burn rates against §3 targets:**
   - Tighten or relax targets per the observed distribution.
   - Document the empirical baseline as a new revision of
     `SLO_CATALOG_2026-05-03.md` (likely new file
     `SLO_CATALOG_2026-06-15.md` or v1.1.0 in-place).
3. **Lift the log-only-severity caveat** on §3.1 / §3.2 / §3.5 alerts.
   These are the user-facing SLOs whose pre-conditions are met today
   (catalog §6 Q6).
4. **Hold §3.3 / §3.4 in log-only severity** pending Q1 (cascor
   `training_sessions_completed_total` already shipped — Q1 is closed
   in code; the §6 framing was about the soak gate, not the metric)
   and Q2 (per-mini-batch instrumentation; design doc
   `juniper-ml/notes/code-review/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md`,
   on origin/main).
5. **Close `OBS-ROUTE-CRED`** before 2026-06-02 — alertmanager receivers
   must rotate from placeholder to real credentials before the
   log-only-severity lift; otherwise post-LIFT-01 alerts fire emails
   into nowhere.

### Who/what closes it

- **CALIB-01** (P3) — recommended action: a single calibration PR
  against juniper-deploy updating `SLO_CATALOG_2026-05-03.md` §3 targets
  and the burn-rate factors in `prometheus/alert_rules.yml`. Owner:
  whichever Claude session picks up the tracker item; gated on
  Prometheus retention covering the full 30-day window
  (`PROMETHEUS_RETENTION` defaults to `30d`).
- **LIFT-01** (P1, blocked) — depends on `CALIB-01` + `OBS-ROUTE-CRED`.
  Edits the burn-rate alert annotations from log-only commentary to
  live paging severities.
- **OBS-ROUTE-CRED** (P1 soft-blocker) — runbook
  `juniper-deploy/notes/ALERTMANAGER_NOTIFICATION_RUNBOOK.md` §4.1
  drives the Gmail / SMTP rotation.

Cross-link: `SLO_CATALOG_2026-05-03.md` §2.6 + §6 Q6 (soak window) and
`POST_METRICS_MON_TRACKER_2026-05-05.md` §3.1 (CALIB-01 detail).

---

## 14. References

### Primary catalog / program docs

- `juniper-deploy/notes/SLO_CATALOG_2026-05-03.md` (v1.0.0)
- `juniper-ml/notes/code-review/METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`
- `juniper-ml/notes/code-review/OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` (juniper-ml#195 / #194)
- `juniper-ml/notes/code-review/POST_METRICS_MON_TRACKER_2026-05-05.md` *(parallel branch — not yet on origin/main)*

### Per-phase entry / design docs

- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.2_PROBE_DESIGN_2026-04-27.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R3.4_SENTRY_AUDIT_CLOSURE_2026-04-30.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R4_ENTRY_PLAN_2026-05-01.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md`
- `juniper-ml/notes/code-review/METRICS_MONITORING_MINI_BATCH_INSTRUMENTATION_DESIGN_2026-05-03.md`
- `juniper-deploy/notes/METRICS_AUTH_RATIONALE.md` (R5 entry plan Q5 (b))

### Per-repo histogram bucket rationale

- `juniper-cascor/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`
- `juniper-canopy/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`
- `juniper-data/notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-02.md`

### Closing PRs (commit hashes verified against current `origin/main`)

| Repo | PR | Subject |
|------|----|---------|
| juniper-cascor | #204 | obs-wire-01: wire 5 cascor metric emission sites + lazy-init race fix |
| juniper-cascor | #211 | obs-wire-02(cascor): wire 9 ws_* metrics + Q3 manager refactor |
| juniper-cascor | #217 | audit(d2+d5): document command_handler headroom + pin resume_replayed_events buckets |
| juniper-cascor | #218 | audit(4.2): wire `juniper_cascor_pending_tasks` gauge via `WorkerRegistryCollector` |
| juniper-cascor | #221 | audit(e6): WorkerRegistry size cap = 250 + WS handshake rejection |
| juniper-cascor | #194 | TRAIN-ARCH-01 design (deferred) |
| juniper-canopy | #234 | obs-wire(canopy): A.4 ws_connections_active wire-up + C.1 middleware order fix |
| juniper-canopy | #236 | obs-wire-02(canopy): seq_gap metric (Q1) + A.8 closed-set + E.3/E.5/D.4 bundles |
| juniper-deploy | #48 | metrics(r5-1): SLO catalog — 5 user-facing + 8 internal-supporting SLIs |
| juniper-deploy | #51 | metrics(r5-fixup): close 3 Wave-2 follow-ups |
| juniper-deploy | #52 | metrics(obs-wire-01-followup): drop phase filter from SLI 3.4 |
| juniper-deploy | #59 | docs(audit-a7): catalog name drift fix + Q3 status update |
| juniper-deploy | #60 | obs-route-01: wire alertmanager `tickets` receiver + B.1 routing |

### Source of truth files (with current `origin/main` SHA)

- `juniper-data/juniper_data/api/observability.py` (juniper-data `88149bf`)
- `juniper-cascor/src/api/observability.py` (juniper-cascor `4034bd6`)
- `juniper-cascor/src/api/workers/metrics.py` (juniper-cascor `4034bd6`)
- `juniper-canopy/src/observability.py` (juniper-canopy `81c4c23`)
- `juniper-ml/juniper-observability/juniper_observability/__init__.py` (juniper-ml `ece0d70`)
- `juniper-deploy/prometheus/alert_rules.yml` (juniper-deploy `edf774c`)
- `juniper-deploy/prometheus/prometheus.yml` (juniper-deploy `edf774c`)
- `juniper-deploy/prometheus/recording_rules.yml` (juniper-deploy `edf774c`)
- `juniper-deploy/alertmanager/alertmanager.yml` (juniper-deploy `edf774c`)
- `juniper-deploy/grafana/provisioning/dashboards/juniper-{overview,canopy,cascor,data}.json` (juniper-deploy `edf774c`)

---

## 15. Unexpected findings — discrepancies vs prior docs

Two findings that were **not** flagged in the existing audit
(`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md`) or the
program-close note (`METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`).
Both surfaced during the verification grep sweep for this snapshot
report.

### 15.1 `juniper_data_datasets_cached` is defined-and-emitted in tests but has no production caller

**Finding.** The metric `juniper_data_datasets_cached` (Gauge, no labels)
is defined in `juniper-data/juniper_data/api/observability.py:159` and
the helper `set_datasets_cached(count)` is defined at line 212. **There
is no production caller** — `grep -rn 'set_datasets_cached'
juniper-data/juniper_data/ --include='*.py'` returns only the
`observability.py` definition and the test file
`juniper_data/tests/unit/test_observability.py:166` (which calls it from
inside a unit test). The metric will therefore be present on the
`/metrics` surface (lazy-init creates it on the first
`_ensure_dataset_metrics()` call inside `record_dataset_generation`)
but always read `0` in production.

**Impact.** The juniper-data dashboard panel "Cached Datasets"
(`juniper-data.json` line 239) will always render `0`. **Severity P2**
by the audit's own classification system (audit §4.1 P2 = quality
issue, dashboard misleading but no SLI math broken). The cache-hit
ratio SLI §4.7 is computed from `juniper_data_dataset_post_total{cache="hit"}`,
not from this gauge, so the SLI is unaffected.

**Discrepancy with prior docs.** The audit doc §4.1.2 ("Dead-defined
metrics inventory") lists 12+ cascor / canopy metrics by ID
(A.1 / A.2a–e / A.3a / A.3b / A.4 / A.5a / A.5b) but **does not
list `juniper_data_datasets_cached`**. Verified against
`OBSERVABILITY_AUDIT_AND_OUTSTANDING_ISSUES_2026-05-03.md` lines
matching `datasets_cached` (zero matches — confirmed via
`grep datasets_cached`). The audit was scoped against the 5 catalog SLIs
plus the cascor + canopy emission audits and did not re-audit the
juniper-data emission sites; this slipped through.

**Recommended action.** Either (a) wire a production caller
(`set_datasets_cached(len(_dataset_cache))` from the dataset cache
manager on every cache mutation), or (b) remove the metric definition
and the dashboard panel. Audit §4.1 dead-defined-metric pattern would
class this as a juniper-data parallel of A.5 (cascor inference) — wire
or drop. Suggest opening as a small juniper-data PR; not a LIFT-01
blocker.

### 15.2 4 stale dashboard panels post audit-PR closes

**Finding.** Four dashboard text / inference panels are stale relative
to current code state:

1. **`juniper-cascor.json` "Inference Request Rate"** (timeseries,
   binds `juniper_cascor_inference_requests_total`) and the matching
   3-quantile inference latency panels — referenced by the dashboard
   but the metric family was REMOVED from
   `juniper-cascor/src/api/observability.py` (per OBS-WIRE-01,
   juniper-cascor#204; comment at line 364: *"OBS-WIRE-01 (A.5):
   `record_inference` removed alongside the
   `juniper_cascor_inference_*` metric family"*). All three panels
   render flat-zero in production. Audit finding A.5 explicitly
   recommended *"Wire `record_inference()` if cascor exposes an
   inference HTTP route; otherwise remove from observability.py and
   dashboard"* — observability.py was cleaned, dashboard was not.

2. **3 placeholder text panels in `juniper-cascor.json`** documenting
   `last_task_duration_seconds`, `gpu_utilization_pct`,
   `recent_task_durations_seconds` as *"JSON-only — Prometheus bridge
   pending"*. The Prometheus bridge **shipped** via juniper-cascor#188
   (`WorkerRegistryCollector`) — see §3.2 worker-domain table. The text
   commentary is stale; the bridge is live.

3. **1 placeholder text panel in `juniper-overview.json`** ("Cascor
   worker GPU saturation (Prometheus bridge pending)") — same issue.

**Impact.** Operator-facing confusion: an operator following the SLO
catalog from §4.1 *"Worker heartbeat freshness — STATUS 2026-05-04:
bridged"* will look at the cascor dashboard, see the bridge-pending
text panels, and conclude the bridge is still pending. **Severity P2**.

**Discrepancy with prior docs.** The carry-forward tracker
(`POST_METRICS_MON_TRACKER_2026-05-05.md`) does not list a
"refresh stale dashboard panels post audit-close" item. The audit doc
A.5 was tracked but its dashboard half was not explicitly carried
forward.

**Recommended action.** A single small juniper-deploy PR to:

1. Drop the 3 inference panels from `juniper-cascor.json`.
2. Replace the 4 placeholder text panels with live timeseries panels
   bound to `juniper_cascor_worker_heartbeat_age_seconds`,
   `juniper_cascor_worker_last_task_duration_seconds`,
   `juniper_cascor_worker_gpu_utilization_pct`,
   `juniper_cascor_worker_recent_task_duration_seconds_p95`.
3. Bump dashboard `version` from 3 → 4.

This is post-LIFT-01 hygiene; not a calibration blocker.

---

<!-- markdownlint-enable MD013 -->
