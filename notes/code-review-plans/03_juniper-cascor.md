# juniper-cascor — Metrics & Monitoring Code Review Plan

**Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-cascor/`
**Target file once distributed**: `juniper-cascor/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
**Inherits**: `00_ECOSYSTEM_ROADMAP.md`
**Created**: 2026-04-24
**Phase**: B — Core service (run after Phase A)

---

## 1. Scope

Metrics & monitoring surface of juniper-cascor (CasCor neural-network
backend, FastAPI + WebSocket on port 8201/8200). This is the largest
observability surface in the ecosystem. In-scope:

- REST: `/v1/metrics`, `/v1/metrics/history`, `/v1/training/status`,
  `/v1/network/topology`
- Health: `/v1/health`, `/v1/health/live`, `/v1/health/ready`
- WebSocket: `/ws/training` — real-time metrics stream
- Prometheus middleware + custom training/inference/WebSocket metrics
- Lifecycle/monitor in-memory state (`TrainingMonitor`, replay buffer)
- Cross-thread / cross-worker metric flow (threading + remote workers)
- Logging substrate (JSON formatter, request_id, file rotation)
- Sentry integration
- Tests for all of the above

Out-of-scope: model algorithm correctness, training-loop math, network
serialization formats unrelated to metrics.

---

## 2. Pre-existing evidence (from initial survey)

### 2.1 Surface inventory

**REST**:
- `/v1/metrics` (`api/routes/metrics.py:17–33`) — `lifecycle.get_metrics()`
- `/v1/metrics/history?count=N` (same file) — bounded history buffer
- `/v1/training/status`, `/v1/network/topology` — adjacent surfaces

**Health** (`api/routes/health.py:24–74`):
- `/v1/health` flat
- `/v1/health/live` flat
- `/v1/health/ready` deep — checks lifecycle availability, network
  loaded, training state, optionally probes `JUNIPER_DATA_URL`

**WebSocket** (`api/websocket/training_stream.py`, `api/websocket/manager.py:51–92`):
- `/ws/training` real-time stream of epoch-end, cascade-add,
  candidate-progress events
- Replay buffer (`JUNIPER_CASCOR_WS_REPLAY_BUFFER_SIZE` default 1024)
- State broadcast coalescing (`ws_state_throttle_coalesce_ms` default 1000)

**Lifecycle / monitor** (`api/lifecycle/monitor.py:141–267`):
- `TrainingMonitor` callbacks: `on_epoch_end`, `on_cascade_add`,
  `on_candidate_progress`
- Bounded deque, maxlen 10 000 (`_PROJECT_API_METRICS_BUFFER_SIZE`)
- `threading.Lock()` on metrics buffer

**Lifecycle manager** (`api/lifecycle/manager.py:627–656`):
- `get_metrics()` reads directly from `network.history` (separate
  storage from `TrainingMonitor.get_metrics_history()`)
- Protected by `_metrics_lock`

**Prometheus surface** (`api/observability.py:213–471`):
- Training: `juniper_cascor_training_sessions_active`,
  `_epochs_total{phase}`, `_loss{phase,loss_type}`,
  `_accuracy_ratio{phase}`, `_hidden_units_total`,
  `_candidate_correlation`, `_inference_requests_total`,
  `_inference_duration_seconds`
- WebSocket: seq tracking, replay buffer occupancy/capacity,
  resume/broadcast metrics, connection state, command handlers
- HTTP: 10-bucket histogram (0.001 → ∞)

### 2.2 Settings

| Env var | Default | Effect |
|---------|---------|--------|
| `JUNIPER_CASCOR_METRICS_ENABLED` | `false` | Gates Prometheus middleware + build info |
| `JUNIPER_CASCOR_LOG_LEVEL` | `INFO` | Root logger level |
| `JUNIPER_CASCOR_LOG_FORMAT` | `text` | `json` triggers `JuniperJsonFormatter` |
| `JUNIPER_CASCOR_WS_REPLAY_BUFFER_SIZE` | `1024` | Replay capacity |
| `JUNIPER_CASCOR_WS_STATE_THROTTLE_COALESCE_MS` | `1000` | Coalescing window |

### 2.3 Process model

- No multiprocessing in API layer (no forkserver — survey result; verify)
- `concurrent.futures.ThreadPoolExecutor` for training threads
- Remote worker coordination via WebSocket (worker registry + coordinator)
- WebSocket replay/seq state managed in-process

### 2.4 Dependencies

- `prometheus-client>=0.20.0` (extra `observability`)
- `sentry-sdk>=2.0.0` (core)
- No OpenTelemetry; hand-rolled WebSocket framing

### 2.5 Tests

- `test_metrics_routes.py` — 6 tests (no-network, with-network, history
  variants, count validation)
- `test_lifecycle_monitor.py` — **26** tests on `TrainingState` /
  `TrainingMonitor` (atomic updates, callbacks, buffer bounds)
  *(initial survey said 20; audit corrected)*
- `test_api_health.py` — **15** tests (flat responses, dep-health, mocks)
  *(initial survey said 17; audit corrected)*
- `test_api_observability.py` — **19** tests: formatter, log levels,
  Prometheus, Sentry, training metrics recording
- `test_websocket_streaming.py` — integration, real-time stream
- `test_api_full_lifecycle.py` — e2e training + metrics flow

### 2.6 Already-suspected findings

| # | Hypothesis | File:line |
|---|------------|-----------|
| H1 | Two independent metric stores: `network.history` (read by `get_metrics`) vs `TrainingMonitor` deque (read by `get_metrics_history`) — drift risk | `manager.py:627–656`, `monitor.py` |
| H2 | Metrics off by default — production may run blind | `settings.py:14–52` |
| H3 | `TrainingMonitor.on_candidate_progress()` called from worker thread; callback async-safety unclear | `monitor.py:241–243` |
| H4 | Worker coordinator `threading.Lock()` + synchronous callbacks → race if callback slow | `workers/coordinator.py:72–100` |
| H5 | WebSocket replay buffer stores full message objects; no compression / dedup → memory growth | `websocket/manager.py` |
| H6 | WebSocket send timeout (0.5 s) silently drops slow clients; no backpressure to training thread | `websocket/manager.py` |
| H7 | WebSocket sequence resets on server restart; no `server_start_time` in metrics → consumer confusion | `websocket/` |
| H8 | Prometheus `endpoint` label = path → unbounded cardinality risk under adversarial requests | `observability.py:25–100` |
| H9 | No tests for WebSocket replay-buffer overflow / recovery (only snapshot tests) | tests |
| H10 | No tests asserting actual coalescing of `ws_state_throttle_coalesce_ms` | tests |
| H11 | No race-condition tests on `_metrics_lock` under concurrent emission | tests |
| H12 | Replay buffer growth under sustained high-frequency updates not load-tested | tests |
| H13 | `RotatingFileHandler` 10 MB × 5 backups — log loss under sustained DEBUG (no warning) | `observability.py:103–158` |
| H14 | No CHANGELOG entry for any monitoring regression — institutional memory weak | docs |
| H15 | `/metrics` endpoint mounted via `make_asgi_app()` (`observability.py:191`) with **no auth layer** and not gated by `EXEMPT_PATHS`. Information disclosure risk: training topology, loss values, hidden_units, candidate correlation are all exposed. Severity depends on deployment trust boundary. | `observability.py:191`, settings auth config |
| H16 | `JUNIPER_WS_*` alternate prefix is supported via Pydantic `AliasChoices` (`settings.py:138, 144`) — **two valid env-var prefixes for the same settings**. Documentation does not flag the alias. Surfaces at deployment time. | `settings.py:138, 144` |
| H17 | No load/perf tests for replay buffer under sustained high-frequency updates; only functional snapshot tests | `test_websocket_streaming.py` |
| H18 | **Metric-name prefix drift**: 15 WebSocket metrics use `cascor_ws_*` (no `juniper_` namespace), while training/inference/HTTP use `juniper_cascor_*`. Inconsistent for dashboards, alert rules, and federated scrape. | `observability.py:348–414` |
| H19 | **24 of 26 Prometheus metrics defined in `observability.py` have NO production emission callsite** (only tests). This is the most severe form of the juniper-data H1 pattern. 8 training/inference metrics + 15 WS Phase-0 metrics are declared but never emitted. See `08_METRIC_CATALOG.md` §5.2, §5.3. | `observability.py:213–471` |
| H20 | **Env-var surface undercount**: extraction found `JUNIPER_CASCOR_WS_PENDING_MAX_DURATION_S`, `_RATE_LIMIT_*` (2), `_WORKER_AUDIT_LOGGING_ENABLED`, `_WORKER_METRICS_ENABLED` — 5 settings not in original §2.2 table | settings.py:156–160, 185–186, 215–216 |
| H21 | HTTP request histogram uses **default Prometheus buckets** (0.005…10 s). Large buckets mismatch CasCor training latency profile — training endpoints will all fall in the same bucket for most of their distribution. | `observability.py` HTTP histogram |

---

### 2.7 Audit corrections (2026-04-24)

The plan was audited against `main` HEAD. Material corrections:

- Test counts adjusted in §2.5 (above).
- New hypotheses **H15** (security), **H16** (alias-choices alt prefix),
  **H17** (load testing) added.
- `JUNIPER_DATA_URL` health-probe is **soft** (optional dependency
  probe), not a hard dependency. Confirmed via spot-check of
  `health.py:56–60`.
- Multiprocessing claim ("no multiprocessing in API layer") confirmed
  — only `concurrent.futures.ThreadPoolExecutor`. Project's
  multiprocessing forkserver use is in the model/training internals,
  not the API layer.
- All other `:line` citations verified.

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk every metric (Prometheus + WS + REST) against current `main`.
2. Build a metrics catalog table:
   `name | type | labels | help text | label cardinality bound | emit site(s)`.
3. For each label, classify cardinality bound: `enumerated`, `bounded`,
   `unbounded`. Flag `unbounded` for Phase 4 (Deviation from Best
   Practices, candidate Critical).
4. Walk WebSocket message types; build a producer/consumer schema table
   that pairs with `juniper-cascor-client` and `juniper-canopy` schemas
   (cross-app drift surfaces in synthesis §7).

### Phase 2 — Functionality verification

1. Run service locally with `JUNIPER_CASCOR_METRICS_ENABLED=true`.
2. Trigger a full training run; capture `/metrics` snapshots at intervals;
   confirm counters monotonic, histograms reasonable.
3. Connect a WebSocket client; verify message ordering, sequence
   monotonicity across simulated reconnects, replay buffer behavior.
4. Compare `/v1/metrics` output vs `TrainingMonitor.get_metrics_history()`
   internal state — confirm or refute H1 (drift between two stores).
5. Issue concurrent training + metric reads; capture any lock contention
   visible in logs; sanity-check H3 / H4 / H11.

### Phase 3 — Test-suite audit

1. Full run:
   ```bash
   cd juniper-cascor/src/tests
   bash scripts/run_tests.bash 2>&1 | tee /tmp/cascor_test_run.log
   ```
2. Inventory: collection / runtime errors, warnings, skips, xfails,
   marker exclusions.
3. For every metrics-touching test, verify the assertion checks the
   metric's value/shape, not just `200 OK`.
4. Coverage gap report on `api/observability.py`,
   `api/lifecycle/monitor.py`, `api/lifecycle/manager.py` (metric paths
   only), `api/websocket/manager.py`.
5. Inventory missing test types per prompt categories (unit, integration,
   regression, e2e, performance, security).

### Phase 4 — Issue classification

Apply ecosystem framework §3.1–3.2.

### Phase 5 — Remediation design

See §5 below. Critical/High findings get ≥2 options; Medium ≥1.

### Phase 6 — Validation

1. Land remediations on a worktree branch.
2. Re-run full suite + functional verification from Phase 2.
3. Run cross-repo smoke per `juniper-ml/CLAUDE.md`.
4. Specifically verify downstream juniper-cascor-client and
   juniper-canopy can still parse `/v1/metrics`, `/v1/metrics/history`,
   and `/ws/training` messages.

### Phase 6.5 — Security & cardinality review (added)

1. **Auth posture for `/metrics`** (H15): decide between
   - (a) auth-gating the endpoint (require API key header),
   - (b) network-level isolation (bind to localhost / sidecar pattern),
   - (c) explicit "intentionally public on trusted network" with a
     prominent doc note.
   Document the chosen posture in `juniper-cascor/CLAUDE.md`.
2. **Cardinality bounds** (H8): for every Prometheus metric in
   `observability.py:213–471`, classify each label as
   `enumerated | bounded | unbounded`. Recommend
   `request.scope["route"].path` (FastAPI route template) as the
   replacement for raw `request.url.path`.
3. **Env var alias documentation** (H16): document the `JUNIPER_WS_*`
   alternate prefix in `juniper-cascor/CLAUDE.md` and decide whether
   to deprecate one of the two prefixes for v0.5.0.
4. **Log PII**: review `JuniperJsonFormatter` for accidental capture
   of API keys, dataset payloads, training tensors, or worker tokens.
5. **WebSocket auth**: confirm `/ws/training` does not stream
   sensitive content to unauthenticated clients.

### Phase 6.6 — CI/CD review (added)

1. Read all `.github/workflows/*.yml`; record:
   - Which markers are run (`integration and not slow`?)
   - Whether `@pytest.mark.requires_*` gates exclude metric-path tests
   - Whether `/metrics` Prometheus-format parse is exercised in CI
2. Confirm WebSocket integration tests run in CI (or are quarantined).
3. Confirm `pip-audit` covers the `observability` extra.

### Phase 7 — Documentation

1. Update `juniper-cascor/CLAUDE.md` if contracts changed.
2. Update OpenAPI spec / WebSocket schema docs if changed.
3. CHANGELOG entry.

---

## 4. Deliverables

| File | Contents |
|------|----------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan |
| `REVIEW_FINDINGS.md` | Findings register |
| `REVIEW_VALIDATION.md` | Test logs + before/after metric snapshots |
| `METRIC_CATALOG.md` | Single-source-of-truth metric catalog (Phase 1 §1 output) |
| `WEBSOCKET_SCHEMA.md` | Message-type schema (feeds cross-app reconciliation) |

---

## 5. Remediation framework — preliminary design notes

### H1 (dual metric stores)

This is the highest-priority architectural finding from the survey.

**Options**:

- **Option A** — Make `TrainingMonitor` the single source of truth;
  `lifecycle.get_metrics()` reads from monitor, drops direct `network.history`
  access. Pros: one store, one lock; consistent semantics.
  Cons: `network.history` is the algorithm-side state — refactor risk.
- **Option B** — Make `network.history` the single source of truth;
  delete the `TrainingMonitor` deque; rebuild monitor on top of history.
  Pros: removes a duplicate buffer. Cons: monitor's bounded deque
  (10 000) is a memory safety guard — losing it risks unbounded growth
  if `network.history` grows without bound.
- **Option C** — Keep both stores; add explicit reconciliation invariant
  + a check (in DEBUG mode? in tests?) that asserts they stay in sync.
  Pros: smallest change. Cons: doesn't fix the root cause, just makes
  drift detectable.

**Provisional recommendation**: **Option A** if `network.history` access
patterns can be funneled through `TrainingMonitor`; else **Option C** as
a hold-the-line measure with **Option A** as a follow-up. Severity
likely High; Likelihood Possible (drift only matters if history shape
changes). The actual review must assess which.

**Validation**: dedicated test that runs a training cycle and asserts
`get_metrics() == TrainingMonitor.snapshot()` at every cascade-add.

### H8 (Prometheus label cardinality on `endpoint`)

**Options**:

- **Option A** — Replace raw path with route template (FastAPI's
  `Route.path_format`, e.g. `/v1/datasets/{dataset_id}` not
  `/v1/datasets/abc-123`). Pros: bounded cardinality.
  Cons: requires route-resolution lookup per request; small overhead.
- **Option B** — Allowlist a fixed set of endpoint labels; everything
  else collapses to `other`. Pros: hard cardinality bound.
  Cons: loses per-endpoint visibility for new routes until allowlist
  updated.

**Provisional recommendation**: **Option A**. Standard practice; minimal
operational burden.

### H5 + H6 (WebSocket replay buffer + send-timeout silent drops)

**Provisional**: introduce a dedicated `slow_consumer_disconnects_total`
counter and a `replay_buffer_bytes` gauge; emit a warning log when a
client is dropped for slowness; cap replay buffer in bytes (not just
message count) so memory growth is bounded under high-frequency states.

### H7 (WebSocket sequence resets on restart)

**Provisional**: include a stable `server_session_id` (UUID generated
at server start) in every WS message envelope; clients use it to detect
restart and reset their local seq tracking explicitly rather than
silently re-syncing.

(Other hypotheses receive full remediation blocks during the actual
review.)

---

## 6. Tooling & commands

```bash
conda activate JuniperCascor

# Full test run
cd juniper-cascor/src/tests
bash scripts/run_tests.bash 2>&1 | tee /tmp/cascor_test_run.log

# Coverage focus
cd juniper-cascor
pytest src/tests -v \
  --cov=src/api/observability \
  --cov=src/api/lifecycle/monitor \
  --cov=src/api/lifecycle/manager \
  --cov=src/api/websocket/manager \
  --cov-report=term-missing

# Local smoke
JUNIPER_CASCOR_METRICS_ENABLED=true \
  python -m src.api.app &
sleep 3
curl -s http://localhost:8201/metrics | grep juniper_cascor | head -30
curl -s http://localhost:8201/v1/health/ready | jq .
```

---

## 7. Owner / sign-off

- Plan owner: (assign during distribution)
- Reviewer: (assign during distribution; this is the largest review —
  consider splitting REST/WS/lifecycle reviewers)
- Sign-off blocked on: ecosystem roadmap §6.1 + downstream
  juniper-cascor-client and juniper-canopy smoke passes.
