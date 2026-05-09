# Juniper Ecosystem Metrics Documentation

**Author**: Paul Calnon
**Last Updated**: 2026-05-08
**Scope**: All Juniper repositories — `juniper-observability`, `juniper-cascor`, `juniper-cascor-worker`, `juniper-data`, `juniper-canopy`, `juniper-deploy`

This document is the canonical reference for the Juniper observability surface: the emission infrastructure, the complete metric inventory, the middlewares, the Prometheus / Grafana integration, the dashboards consumed via Canopy and Grafana, and the procedures for adding or removing a metric.

---

## 1. Metric Emission Infrastructure

### 1.1 The shared package: `juniper-observability`

`juniper-observability` (this repo's `juniper-observability/` subdirectory; published to PyPI as a standalone package) is the canonical home for cross-service observability primitives.
 Current minimum pin: `juniper-observability>=0.2.0`.

It is a **pure helper layer**. It defines no concrete `Counter` / `Gauge` / `Histogram` / `Summary` instances itself — services own their metric definitions.
The package provides:

- Idempotent registration helpers wrapping `prometheus_client`.
- Two FastAPI/Starlette ASGI middlewares applied by every service.
- A standard `/metrics` ASGI app factory.
- A `set_build_info(...)` helper that registers a `<namespace>_build` Info metric.
- A `JuniperJsonFormatter` and `configure_logging` for structured-JSON logs with request-id propagation.
- A pytest fixture `reset_prometheus_registry` for clean test isolation.
- Sentry initialization helper (`configure_sentry`) with the SEC-10 `before_send` redaction hook.

### 1.2 Public API surface (`juniper_observability/__init__.py`)

| Symbol                                                                       | Purpose                                                                                                                                |
|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `register_or_reuse(factory, name, *args, **kwargs)`                          | Adopt-existing on duplicate; **default choice** for almost every collector registration. Preserves accumulated samples across re-init. |
| `register_fresh(factory, name, *args, **kwargs)`                             | Drop-and-recreate on duplicate; use only when intentionally changing buckets/labels.                                                   |
| `register_info_or_update(name, description, **info_labels)`                  | Sugar for the `Info` two-step (register, then `.info({...})`).                                                                         |
| `lazy_register_or_reuse(factory, name, *args, **kwargs)`                     | Like `register_or_reuse` but caches the result in a module-private dict. Use on the lazy-init-with-`None`-sentinel hot path.           |
| `PrometheusMiddleware`                                                       | HTTP request-count / duration / unmatched-route middleware (bounded cardinality).                                                      |
| `RequestIdMiddleware`                                                        | Injects/propagates `X-Request-ID` and stores it in the `request_id_var` ContextVar.                                                    |
| `get_prometheus_app()`                                                       | Returns an ASGI app that serves `/metrics` from the global Prometheus registry.                                                        |
| `set_build_info(namespace, version)`                                         | Registers `<namespace>_build` Info metric with `version` and `python_version` labels.                                                  |
| `JuniperJsonFormatter`, `configure_logging`                                  | Structured-JSON logging with stable keys (`timestamp`, `level`, `logger`, `message`, `service`, `request_id`, optional `exception`).   |
| `probe_dependency()`, `DependencyStatus`, `ReadinessResponse`                | Synchronous HTTP health-check primitives shared across `/v1/health/ready`.                                                             |
| Constants: `HEADER_X_REQUEST_ID`, `LIVENESS_STALENESS_SECONDS`,              | Cross-service contract values (R1.1/R1.2/R1.3).                                                                                        |
| -- `LIVENESS_TICK_BUDGET_MS`, `READINESS_HEADER`, `UNMATCHED_ENDPOINT_LABEL` |                                                                                                                                        |
| `juniper_observability.testing.reset_prometheus_registry`                    | pytest fixture; snapshots collectors before each test, unregisters new ones after, clears the `lazy_register_or_reuse` cache.          |

Source-of-truth file paths (within `juniper-observability/juniper_observability/`):

- `prometheus_helpers.py:88-309` — register helpers
- `middleware/prometheus.py:28-90` — `PrometheusMiddleware`
- `middleware/request_id.py:23-43` — `RequestIdMiddleware`
- `prometheus.py:29-50` — `set_build_info`
- `logging.py` — JSON formatter and `configure_logging`
- `testing.py:44-95` — `reset_prometheus_registry`

### 1.3 Registration patterns

All metric definitions in consumer services follow one of these patterns:

**Lazy-init dict pattern** (preferred for state-rich collectors, e.g. cascor's training and WS metrics):

```python
_TRAIN_METRICS: dict[str, MetricBase] = {}
_train_lock = threading.Lock()

def _ensure_training_metrics() -> None:
    if _TRAIN_METRICS:
        return
    with _train_lock:
        if _TRAIN_METRICS:
            return
        _TRAIN_METRICS["sessions_active"] = register_or_reuse(
            Gauge,
            "juniper_cascor_training_sessions_active",
            "Number of currently active training sessions",
        )
        # ...
```

**One-shot Info pattern** (for build info):

```python
set_build_info("juniper_cascor", _API_VERSION)  # called once during lifespan startup
```

**Custom collector pattern** (used by cascor's worker registry — emits per-worker gauges via `GaugeMetricFamily` on every scrape):

```python
class WorkerCollector:
    def collect(self) -> Iterator[Metric]:
        yield GaugeMetricFamily(
            "juniper_cascor_worker_heartbeat_age_seconds",
            "Seconds since worker's last heartbeat",
            labels=["worker_id"],
            value=...,
        )
```

### 1.4 Cross-service contract constants

The `R1.x` contract pins the following values across every Juniper service.
Do not redefine these locally — import from `juniper_observability`:

| Constant                     | Value          | Purpose                                                                 |
|------------------------------|----------------|-------------------------------------------------------------------------|
| `HEADER_X_REQUEST_ID`        | `X-Request-ID` | Wire-format request-id header                                           |
| `LIVENESS_STALENESS_SECONDS` | `30`           | `/v1/health/live` heartbeat staleness ceiling                           |
| `LIVENESS_TICK_BUDGET_MS`    | `250`          | Liveness probe wall-clock budget                                        |
| `UNMATCHED_ENDPOINT_LABEL`   | `_unmatched`   | `endpoint` label value for routes that don't match a Starlette template |

---

## 2. Middleware

Every FastAPI service in the ecosystem wires the same two middlewares from `juniper_observability`.
Middleware ordering matters because Starlette evaluates the stack LIFO — the LAST middleware added is the OUTERMOST.
The convention is that `RequestIdMiddleware` is added LAST so the `request_id` ContextVar is populated before `PrometheusMiddleware` records its samples.

### 2.1 `PrometheusMiddleware`

Source: `juniper-observability/juniper_observability/middleware/prometheus.py:28-90`

Constructor: `PrometheusMiddleware(app, service_name="juniper-service", namespace="juniper")`

Emits three metrics, each prefixed with `<namespace>_`:

| Metric                               | Type      | Labels                         | Notes                                                                                                 |
|--------------------------------------|-----------|--------------------------------|-------------------------------------------------------------------------------------------------------|
| `<ns>_http_requests_total`           | Counter   | `method`, `endpoint`, `status` | `endpoint` is the Starlette route template (e.g. `/v1/datasets/{id}`)                                 |
| `<ns>_http_request_duration_seconds` | Histogram | `method`, `endpoint`           | Default `prometheus_client` buckets                                                                   |
| `<ns>_http_unmatched_requests_total` | Counter   | `method`                       | Incremented when no route template matches; `endpoint` collapsed to `_unmatched` to bound cardinality |

### 2.2 `RequestIdMiddleware`

Source: `juniper-observability/juniper_observability/middleware/request_id.py:23-43`

Generates a UUID4 `X-Request-ID` if not present on the inbound request, stores it in `request_id_var`, and echoes it on the response.
The JSON log formatter reads `request_id_var` so every log emitted during the request is tagged.

### 2.3 Service-specific middlewares (non-metrics)

For completeness, services also stack:

- **`SecurityMiddleware`** — API-key auth + rate limiting (canopy, cascor, data).
- **`SecurityHeadersMiddleware`** — CSP, HSTS, X-Frame-Options.
- **`MetricsAuthMiddleware`** — IP allowlist gating `/metrics` on juniper-data (`juniper_data/api/app.py:129-132`); cascor and canopy expose `/metrics` without auth on the assumption of network-level isolation.
- **`RequestBodyLimitMiddleware`** (canopy) — 16 MB cap, configurable.

---

## 3. Per-Service Metric Inventories

This section enumerates every Prometheus metric currently emitted by the four services.
Metrics from `PrometheusMiddleware` are listed once at the end of each subsection and referred to as "HTTP middleware metrics" in the service-specific tables.

### 3.1 `juniper-cascor`

**Metrics endpoint**: `/metrics`, mounted via `app.mount("/metrics", get_prometheus_app())` at `src/api/app.py:477`. Gated by `settings.metrics_enabled`.
**Build info**: `set_build_info("juniper_cascor", _API_VERSION)` called during lifespan startup at `src/api/app.py:165`. `_API_VERSION` is read from `importlib.metadata.version("juniper-cascor")` with fallback `"0.0.0-dev"`.
**Middleware**: `PrometheusMiddleware(service_name="juniper-cascor", namespace="juniper_cascor")` at `src/api/app.py:457`.

#### Training subsystem (`src/api/obs.py`)

| Metric                                             | Type      | Labels               | Description                                                               |
|----------------------------------------------------|-----------|----------------------|---------------------------------------------------------------------------|
| `juniper_cascor_training_sessions_active`          | Gauge     | —                    | Active training sessions in flight                                        |
| `juniper_cascor_training_sessions_completed_total` | Counter   | `status`             | Terminal session transitions; `status` ∈ {success, failure, cancelled}    |
| `juniper_cascor_training_epochs_total`             | Counter   | `phase`              | Total epochs completed across all sessions; `phase` ∈ {output, candidate} |
| `juniper_cascor_training_loss`                     | Gauge     | `phase`, `loss_type` | Current loss value (last-write-wins per label set)                        |
| `juniper_cascor_training_accuracy_ratio`           | Gauge     | `phase`              | Current training accuracy in [0, 1]                                       |
| `juniper_cascor_hidden_units_total`                | Gauge     | —                    | Current number of hidden units in the cascade                             |
| `juniper_cascor_candidate_correlation`             | Gauge     | —                    | Best candidate-unit correlation with residual error                       |
| `juniper_cascor_training_step_duration_seconds`    | Histogram | —                    | Train-step duration; buckets 50 ms → 30 s, targeting SLO 3.4 (p95 < 5 s)  |

#### WebSocket subsystem (`src/api/obs.py`, `src/api/control_stream.py`)

| Metric                                         | Type      | Labels              | Description                                                                                |
|------------------------------------------------|-----------|---------------------|--------------------------------------------------------------------------------------------|
| `cascor_ws_connections_active`                 | Gauge     | `endpoint`          | Active WS connections per endpoint; `endpoint` ∈ {training, control, workers}              |
| `cascor_ws_seq_current`                        | Gauge     | —                   | Current sequence number for WS broadcasts                                                  |
| `cascor_ws_replay_buffer_occupancy`            | Gauge     | —                   | Messages currently held in the replay buffer                                               |
| `cascor_ws_replay_buffer_bytes`                | Gauge     | —                   | Approximate replay-buffer memory footprint                                                 |
| `cascor_ws_replay_buffer_capacity_configured`  | Gauge     | —                   | Configured maximum replay-buffer size                                                      |
| `cascor_ws_resume_requests_total`              | Counter   | `outcome`           | Resume handshakes; `outcome` ∈ {success, out_of_range, malformed_resume, server_restarted} |
| `cascor_ws_resume_replayed_events`             | Histogram | —                   | Events replayed per successful resume; buckets 0..1024                                     |
| `cascor_ws_pending_connections`                | Gauge     | —                   | Connections in the pending (resume-handshake) state                                        |
| `cascor_ws_state_throttle_coalesced_total`     | Counter   | —                   | State broadcasts coalesced by the throttle                                                 |
| `cascor_ws_broadcast_timeout_total`            | Counter   | `type`              | Broadcast send timeouts per message type                                                   |
| `cascor_ws_broadcast_send_duration_seconds`    | Histogram | `type`              | Per-message-type send latency; sub-ms buckets (100µs → 100ms), SLI 4.3                     |
| `cascor_ws_broadcast_from_thread_errors_total` | Counter   | —                   | Errors from `broadcast_from_thread` coroutine                                              |
| `cascor_ws_control_command_received_total`     | Counter   | `command`           | Control commands received; closed-set `command` validated upstream                         |
| `cascor_ws_command_responses_total`            | Counter   | `command`, `status` | Command responses; `status` ∈ {success, error, rate_limited}                               |
| `cascor_ws_command_handler_seconds`            | Histogram | `command`           | Handler execution time; sub-ms buckets                                                     |

#### Worker subsystem (custom collector — `src/api/metrics.py`)

Emitted via a `WorkerCollector` registered at `src/api/app.py:93-97` and unregistered at shutdown (line 116).
On every scrape it walks the `WorkerRegistry` and yields:

| Metric                                                   | Type  | Labels      | Description                                                    |
|----------------------------------------------------------|-------|-------------|----------------------------------------------------------------|
| `juniper_cascor_worker_last_task_duration_seconds`       | Gauge | `worker_id` | Wall-clock duration of the worker's most recent task           |
| `juniper_cascor_worker_gpu_utilization_pct`              | Gauge | `worker_id` | Best-effort 0-100 GPU utilization on the worker                |
| `juniper_cascor_worker_recent_task_duration_seconds_p50` | Gauge | `worker_id` | p50 of the rolling window of recent task durations             |
| `juniper_cascor_worker_recent_task_duration_seconds_p95` | Gauge | `worker_id` | p95 of the rolling window of recent task durations             |
| `juniper_cascor_worker_heartbeat_age_seconds`            | Gauge | `worker_id` | Seconds since the worker's last heartbeat (critical SLI input) |
| `juniper_cascor_pending_tasks`                           | Gauge | —           | In-flight tasks tracked by the coordinator                     |

Plus the standard HTTP middleware trio under namespace `juniper_cascor` and the `juniper_cascor_build` Info metric.

### 3.2 `juniper-data`

**Metrics endpoint**: `/metrics`, mounted at `juniper_data/api/app.py:129-132`,  Gated by `MetricsAuthMiddleware` (IP allowlist via `settings.metrics_trusted_ips`).
**Build info**: `set_build_info("juniper_data", __version__)` at `juniper_data/api/app.py:42`.
**Middleware**: `PrometheusMiddleware(namespace="juniper_data")` at `juniper_data/api/app.py:119`.
**Lazy init**: `_ensure_dataset_metrics()` at `juniper_data/observability.py:105-158`.

| Metric                                             | Type      | Labels                         | Description                                                                                    |
|----------------------------------------------------|-----------|--------------------------------|------------------------------------------------------------------------------------------------|
| `juniper_data_dataset_generations_total`           | Counter   | `generator`, `status`          | Total generation attempts; `status` ∈ {success, error}. Incremented on every attempt           |
| `juniper_data_dataset_generation_duration_seconds` | Histogram | `generator`                    | Generation latency; populated **only on success**. Buckets: 10 ms → 30 s                       |
| `juniper_data_dataset_post_total`                  | Counter   | `generator`, `status`, `cache` | Every `POST /v1/datasets`; `cache` ∈ {hit, miss} (closed-set, R1.1)                            |
| `juniper_data_datasets_cached`                     | Gauge     | —                              | Datasets currently in the cache backend; refreshed on each `save()` via `_emit_cached_count()` |

Plus HTTP middleware trio (`juniper_data_http_*`) and the `juniper_data_build`
Info metric.

### 3.3 `juniper-canopy`

**Metrics endpoint**: `/metrics`, mounted at `main.py:321`.
**Build info**: `set_build_info("juniper_canopy", APP_VERSION)` at `main.py:137`. `APP_VERSION` from `importlib.metadata.version("juniper-canopy")` with fallback `"0.4.0"`.
**Middleware**: `PrometheusMiddleware` at `main.py:320`; `RequestIdMiddleware` added LAST at `main.py:322` so it becomes outermost (LIFO) and the `request_id` ContextVar is set before the Prometheus middleware records its sample.

Canopy is special: it both **emits** metrics about its own behaviour and acts as a **client** to cascor's WebSocket streams.
Its metrics therefore cover the client-side health of the cascor link as well as canopy-internal state.

#### WebSocket / adapter (`backend/observability.py`, `backend/adapter_validation.py`)

| Metric                                        | Type    | Labels               | Description                                                      |
|-----------------------------------------------|---------|----------------------|------------------------------------------------------------------|
| `juniper_canopy_websocket_connections_active` | Gauge   | `channel`            | Active WS connections to cascor by `channel` (training, control) |
| `juniper_canopy_websocket_messages_total`     | Counter | `channel`, `type`    | WS messages by channel and envelope `type`                       |
| `juniper_canopy_unrecognized_ws_frames_total` | Counter | `type`, `endpoint`   | Frames failing envelope validation                               |
| `juniper_canopy_ws_seq_gap_detected_total`    | Counter | `service`, `channel` | Client-side WS sequence gaps detected                            |
| `canopy_adapter_inbound_invalid_total`        | Counter | —                    | Malformed frames received from cascor                            |

#### Outbound HTTP client (`backend/observability.py`)

| Metric                                           | Type      | Labels                                 | Description                                                  |
|--------------------------------------------------|-----------|----------------------------------------|--------------------------------------------------------------|
| `juniper_canopy_data_client_requests_total`      | Counter   | `method`, `status_class`, `error_type` | Outbound `juniper-data-client` HTTP requests                 |
| `juniper_canopy_data_client_request_duration_ms` | Histogram | `method`, `status_class`               | Latency in milliseconds; buckets 1 ms → 5 s (R4.1 tentative) |

#### Operating mode

| Metric                            | Type  | Labels | Description                                   |
|-----------------------------------|-------|--------|-----------------------------------------------|
| `juniper_canopy_demo_mode_active` | Gauge | —      | Binary 0/1 indicator that demo mode is active |

Plus HTTP middleware trio (`juniper_canopy_http_*`) and the `juniper_canopy_build` Info metric.

### 3.4 `juniper-cascor-worker`

The worker is **deliberately not a Prometheus emitter**.
It does not import `prometheus_client` and does not expose `/metrics`.
Instead, all of its state is bridged into Prometheus via the cascor coordinator's `WorkerCollector` (see §3.1, "Worker subsystem"), which scrapes the worker's heartbeat payload and re-emits it.

The worker's HTTP surface is a hand-rolled asyncio health server on **port 8210** (localhost-only by default) at `juniper_cascor_worker/http_health.py`:

- `GET /v1/health` → 200 (no-op liveness)
- `GET /v1/health/live` → liveness tick within `LIVENESS_TICK_BUDGET_MS`
- `GET /v1/health/ready` → readiness tick

The heartbeat payload (the wire-format that becomes the cascor coordinator's metric source) carries:

- `in_flight_tasks` (concurrent active tasks)
- `tasks_completed`, `tasks_failed` (lifetime counters)
- `last_task_duration_seconds`
- `recent_task_durations_seconds` (rolling window, maxlen=100, used for p50/p95)
- `last_task_completed_at` (Unix seconds)

If the worker is ever changed to export Prometheus metrics directly, the metric names should match the coordinator-side names from §3.1 with `worker_id` as the sole differentiating label.

---

## 4. Prometheus Integration (`juniper-deploy`)

### 4.1 Prometheus configuration

Location: `juniper-deploy/prometheus/prometheus.yml`.

Global: `scrape_interval: 15s`, `evaluation_interval: 15s`, `scrape_timeout: 10s`.
Retention: 30 days (set in `docker-compose.yml`).

| Job              | Target           | Port | Interval | Path       | Notes                                     |
|------------------|------------------|------|----------|------------|-------------------------------------------|
| `prometheus`     | `localhost`      | 9090 | 15 s     | `/metrics` | Self-scrape                               |
| `juniper-data`   | `juniper-data`   | 8100 | 10 s     | `/metrics` | `MetricsAuthMiddleware` IP-allowlist gate |
| `juniper-cascor` | `juniper-cascor` | 8200 | 10 s     | `/metrics` | No auth — internal network                |
| `juniper-canopy` | `juniper-canopy` | 8050 | 15 s     | `/metrics` | No auth — internal network                |

### 4.2 Container topology

`juniper-deploy/docker-compose.yml`:

| Service        | Image                       | Host port        | Notes                                                                             |
|----------------|-----------------------------|------------------|-----------------------------------------------------------------------------------|
| `prometheus`   | `prom/prometheus:v3.10.0`   | `127.0.0.1:9090` | Networks: backend, data, frontend, monitoring; 30 d retention                     |
| `grafana`      | `grafana/grafana:12.4.0`    | `127.0.0.1:3000` | Provisioned from `./grafana/provisioning`; home dashboard `juniper-overview.json` |
| `alertmanager` | `prom/alertmanager:v0.27.0` | `127.0.0.1:9093` | SMTP secret via `/run/secrets/alertmanager_smtp_password` (OBS-ROUTE-01)          |

### 4.3 Alert rules

Location: `juniper-deploy/prometheus/alert_rules.yml` (1147 lines).

| Group                            | Sample alerts                                                             | Severity                   |
|----------------------------------|---------------------------------------------------------------------------|----------------------------|
| `juniper_service_health`         | `ServiceDown`, `ServiceRestartLoop`                                       | Page on `up == 0` for >1 m |
| `juniper_error_rates`            | `HighErrorRate_{Data,Cascor,Canopy}`                                      | Page on 5xx > 5 % over 5 m |
| `juniper_latency`                | `HighLatency_Data` (p95>2s), `HighLatency_Cascor` (p95>5s)                | Warning                    |
| `juniper_training`               | `TrainingStalled`, `TrainingLossNotDecreasing`, `LowCandidateCorrelation` | Info                       |
| `juniper_data_operations`        | `DatasetGenerationFailures`, `SlowDatasetGeneration`                      | Info / warning             |
| `juniper_infrastructure`         | `NoWebSocketConnections`                                                  | Info                       |
| `juniper_slo_*` (5 groups)       | Burn-rate alerts (MWMBR): fast-burn 14.4× pages, slow-burn 6× tickets     | SLO routing                |
| `juniper_threshold_*` (4 groups) | `CascorWorkerHeartbeatStale` (>60 s for 2 m), `JuniperServiceScrapeDown`  | Threshold                  |
|                                  | -- (>2 m), `CascorPendingTasksSaturated`, per-service 5xx                    |                            |

Recording rules (lines 1-63) precompute request rates, error ratios, p50/p95/p99
latency and epoch rates so that dashboards do not pay raw-histogram cost on
every refresh.

### 4.4 Grafana dashboards

Location: `juniper-deploy/grafana/provisioning/dashboards/`.

| Dashboard JSON          | Description                                                                                               |
|-------------------------|-----------------------------------------------------------------------------------------------------------|
| `juniper-overview.json` | Cross-service health overview (set as Grafana home dashboard)                                             |
| `juniper-data.json`     | Dataset generation service: HTTP, generation latency, cache size, error rate                              |
| `juniper-cascor.json`   | Training service: epochs, loss, accuracy, hidden units, candidate correlation, WS health, worker registry |
| `juniper-canopy.json`   | Dashboard service: HTTP, WS-client connections, demo-mode flag, data-client latency                       |

Provisioning provider config: `dashboard-providers.yml` in the same directory.

### 4.5 Network isolation

Prometheus joins the `backend`, `data`, `frontend`, and `monitoring` Docker
networks so it can reach every service. Grafana and AlertManager are confined
to the `monitoring` network — they cannot directly reach service containers and
must read through Prometheus.

---

## 5. Dashboards

### 5.1 Grafana dashboards

See §4.4. Grafana is the production observability surface for operators and
on-call. It reads exclusively from Prometheus.

### 5.2 Canopy dashboards (Dash UI)

Canopy renders a tabbed Dash dashboard at `/dashboard`. Tabs are mounted in
`dbc.Tabs(active_tab="metrics")` at `dashboard_manager.py:1331-1411`. Each
component inherits `BaseComponent` and lives in `src/frontend/components/`.

| Tab | Component file | Data source | Description |
|-----|----------------|-------------|-------------|
| Training Metrics | `metrics_panel.py` | `/api/metrics` (1 s polling) | Loss / accuracy / learning-rate / phase indicators |
| Candidate Metrics | `candidate_metrics_panel.py` | Cascor WS | Candidate-unit training progress and curves |
| Network Topology | `network_visualizer.py` | Cascor WS | Force-directed graph of neurons + synapses |
| Network Evolution | `network_evolution.py` | Cascor WS | Small-multiples timeline of cascade growth |
| Decision Boundary | `decision_boundary.py` | Cascor WS | 2-D classifier surface |
| Dataset View | `dataset_plotter.py` | Dataset snapshots | Scatter / contour with predictions |
| Workers | `worker_panel.py` | `/api/workers` | Remote worker status + utilization |
| Parameters | `parameters_panel.py` | `/api/params` | Live parameter controls |
| Snapshots | `hdf5_snapshots_panel.py` | `/api/v1/snapshots` | Stored checkpoints; replay POST |
| Replay | `replay_player_panel.py` | HDF5 replay store | Frame-by-frame snapshot playback |
| Network Editor | `network_editor_panel.py` | `/api/v1/network/*` | Surgical network mutations (FSM = Investigating) |
| Redis | `redis_panel.py` | `/api/v1/redis/metrics` | Key cardinality, memory, evictions |
| Cassandra | `cassandra_panel.py` | `/api/v1/cassandra/metrics` | Partitions, R/W latency, compactions |
| Tutorial | `tutorial_panel.py` | Static | Walkthrough |
| About | `about_panel.py` | Static | Version / license / credits |

WebSocket consumption flows in `communication/websocket_manager.py`:

- `inc_websocket_messages(channel, type)` (line 495-499) on every inbound frame
- `set_websocket_connections(channel, count)` (line 342-346, 441-445) on connect/disconnect
- `inc_ws_seq_gap_detected(channel)` in the relay loop on sequence gaps

---

## 6. Procedures

### 6.1 Adding a new metric (creation path)

The path varies slightly depending on whether the metric is a routine
service-internal counter/gauge or one that an operator dashboard / alert / SLO
will consume.

#### Step-by-step

1. **Choose the right helper.**
   - Default: `register_or_reuse(...)` (adopt-existing on duplicate, samples
     preserved across in-process re-init).
   - Hot path with module-level `_metric: Optional[Counter] = None` sentinel:
     `lazy_register_or_reuse(...)`.
   - Test/migration intentionally changing buckets or labels: `register_fresh`.
   - Build/version metadata: `register_info_or_update` or `set_build_info`.

2. **Pick a name** that follows the ecosystem convention:
   `<service_namespace>_<subsystem>_<unit>` (e.g.
   `juniper_cascor_training_loss`, `juniper_data_dataset_generations_total`).
   Counters end in `_total`; durations end in `_seconds`; ratios end in `_ratio`
   or `_pct`. Keep `cascor_ws_*` for cascor's WebSocket subsystem (legacy
   prefix, retained for dashboard continuity).

3. **Bound the cardinality.** Labels must come from a closed enum or a
   pre-validated set. The pattern across the ecosystem is to declare a tuple
   like `_VALID_COMMANDS = (...)` and validate before incrementing. Never label
   on user input, request body fields, or open-ended IDs — use a custom
   collector (cf. cascor's `WorkerCollector`) when per-entity gauges are
   needed.

4. **Define the metric** in the owning service. Add it to the lazy-init dict in
   the relevant `obs.py` / `observability.py` module:

   ```python
   _METRICS["my_thing"] = register_or_reuse(
       Counter,
       "juniper_<svc>_my_thing_total",
       "Description ending without a period",
       ["label_a", "label_b"],
   )
   ```

5. **Wire the emission** at the call site. Prefer a thin helper
   (`inc_my_thing(label_a, label_b)`) over scattering `_METRICS["my_thing"].labels(...).inc()`
   across the codebase — easier to grep, easier to delete.

6. **Add tests.** Use the `reset_prometheus_registry` fixture from
   `juniper_observability.testing`. Assert on the metric value via
   `prometheus_client.REGISTRY.get_sample_value(...)`.

7. **Add a Grafana panel** if the metric is operator-facing. Edit the
   appropriate `juniper-deploy/grafana/provisioning/dashboards/<svc>.json`
   panel JSON and commit. Grafana picks up the change on next provisioning
   reload (container restart or `SIGHUP`).

8. **Add a recording / alert rule** if the metric drives an SLO or page. Edit
   `juniper-deploy/prometheus/alert_rules.yml`. Reload Prometheus
   (`POST /-/reload` or container restart). Page rules go in `juniper_slo_*`
   groups; threshold-only rules in `juniper_threshold_*`; informational rules
   in the topical group.

9. **Document.** Add the metric to §3 of this document and to the relevant
   service's README / AGENTS.md if the metric is operator-facing.

#### Special: adding a Canopy dashboard tab

A Canopy "dashboard" in the UI sense is a tab. Steps:

1. Create `src/frontend/components/my_panel.py` inheriting `BaseComponent`,
   implementing `get_layout()` and any `@self.app.callback`s.
2. Instantiate in `DashboardManager._initialize_components()`
   (`dashboard_manager.py:437-505`):
   ```python
   self.my_panel = MyPanel(self.config.get("my_panel", {}), component_id="my-panel")
   self.register_component(self.my_panel)
   ```
3. Add `dbc.Tab(self.my_panel.get_layout(), label="My Panel", tab_id="my-panel")`
   to the `dbc.Tabs` list (`dashboard_manager.py:1328-1411`).
4. Wire data callbacks against the canopy backend (`/api/...`) or via the
   existing `WebSocketManager` for cascor live data.

There is no tab-registry file — adding a tab is purely an inline edit to
`dashboard_manager.py`. Dashboard layout is rebuilt on every
`DashboardManager` instantiation (`main.py:338`).

### 6.2 Removing / renaming a metric (delete path)

Deleting a Prometheus metric is operationally disruptive — every dashboard,
recording rule, and alert that references it will go silent. Follow this
sequence:

1. **Audit consumers.** Grep across the ecosystem (and operator-side
   `juniper-deploy/`) for the metric name and any of its label values:

   ```bash
   util/search_file_in_all_repos_and_worktrees.bash juniper_<svc>_<metric_name>
   grep -rn "juniper_<svc>_<metric_name>" \
     juniper-deploy/grafana/provisioning/dashboards \
     juniper-deploy/prometheus
   ```

2. **Migrate consumers first.** If renaming, add the new metric (emit both
   old and new in parallel for at least one release). Update Grafana panels
   and Prometheus rules to reference the new metric. Confirm the new metric
   is being scraped and showing data in Grafana before proceeding.

3. **Delete the emission site.** Remove the `register_or_reuse(...)` call,
   the lazy-init dict entry, and any helper functions that referenced it.
   Do not leave a stub that no longer registers — that creates a silent
   "this collector exists with zero samples" state.

4. **Delete dashboard panels and alert rules** that reference the metric.
   Empty Grafana panels and silently-firing-on-`absent()` alerts are common
   leftovers.

5. **Delete recording rules** that derive from the metric. These are easy
   to miss because they live in `alert_rules.yml` but look like normal
   metrics from the consumer side.

6. **Reload Prometheus and Grafana.** Either restart the containers or
   `POST /-/reload` to Prometheus.

7. **Remove tests** that asserted on the old metric. The
   `reset_prometheus_registry` fixture will *not* fail if you leave
   assertions referencing a metric that's no longer registered — they will
   read `None` and silently pass `assert value == 0` when the test author
   meant `value > 0`.

8. **Update §3 of this document** so the inventory remains accurate.

#### Notes on safety

- **Counters cannot be reset by deleting the metric.** Prometheus retains the
  series for 30 days (the deploy retention). Scrapes after deletion will see
  `absent(metric)` go to 1; alerts using `absent()` as a guard need updating
  before the deletion lands.
- **Histograms with bucket changes** must use `register_fresh` (drop+recreate)
  rather than `register_or_reuse`, otherwise the existing collector's buckets
  are silently retained. Bucket changes are functionally a delete-and-add
  from the Prometheus storage perspective — the old `_bucket{le=...}` series
  go stale; the new series start at zero.
- **Renaming is preferred to deletion** for any metric that is referenced by
  a public dashboard or alert. Run the dual-emit period on the order of one
  full release cycle.

---

## 7. Testing & Pre-Commit

### 7.1 The `reset_prometheus_registry` fixture

Source: `juniper-observability/juniper_observability/testing.py:44-95`.
Function-scoped, snapshots collectors before each test, unregisters anything
new after, clears the `lazy_register_or_reuse` cache. Wire it in `conftest.py`
as `autouse=True` whenever the test module touches Prometheus collectors.

### 7.2 Pre-commit

The cross-repo `Async-route audit (BUG-JD-10 class)` ruff hook (`ASYNC*`
codes) catches sync-in-async footguns that would manifest as latency-metric
regressions. The async-route audit lane is wired in all four service repos
(`juniper-cascor`, `juniper-data`, `juniper-canopy`, `juniper-cascor-worker`)
and in `juniper-ml`'s pre-commit config — see
`notes/FOLLOWUP_ASYNC_ROUTE_AUDIT.md`.

---

## 8. References

- Shared helper design: `notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`
- Async route audit follow-ups: `notes/FOLLOWUP_ASYNC_ROUTE_AUDIT.md`
- SLO catalog (drives `juniper_slo_*` rule groups): `notes/SLO_CATALOG_2026-05-03.md`
- Per-service AGENTS.md files for service-specific commands and architecture
- Parent ecosystem map: `/home/pcalnon/Development/python/Juniper/CLAUDE.md`

---

## Appendix A: Quick metric count per service

| Service | Service-defined metrics | HTTP middleware metrics | Build info | Total |
|---------|------------------------:|------------------------:|-----------:|------:|
| juniper-cascor | 29 | 3 | 1 | 33 |
| juniper-data | 4 | 3 | 1 | 8 |
| juniper-canopy | 8 | 3 | 1 | 12 |
| juniper-cascor-worker | 0 (bridged via cascor) | 0 | 0 | 0 |

## Appendix B: Service / port / path summary

| Service | Host port | Container port | Metrics path | Auth |
|---------|----------:|---------------:|--------------|------|
| juniper-data | 8100 | 8100 | `/metrics` | `MetricsAuthMiddleware` (IP allowlist) |
| juniper-cascor | 8201 | 8200 | `/metrics` | None (internal) |
| juniper-canopy | 8050 | 8050 | `/metrics` | None (internal) |
| juniper-cascor-worker | 8210 | 8210 | (none — heartbeat only) | localhost-only |
| Prometheus | 9090 | 9090 | `/metrics` | None (loopback bind) |
| Grafana | 3000 | 3000 | n/a | Login required |
| AlertManager | 9093 | 9093 | n/a | None (loopback bind) |
