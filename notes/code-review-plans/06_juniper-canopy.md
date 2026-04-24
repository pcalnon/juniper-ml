# juniper-canopy — Metrics & Monitoring Code Review Plan

**Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-canopy/`
**Target file once distributed**: `juniper-canopy/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
**Inherits**: `00_ECOSYSTEM_ROADMAP.md`
**Created**: 2026-04-24
**Phase**: C — Consumers (run last; depends on cascor and cascor-client)

---

## 1. Scope

Metrics & monitoring surface of juniper-canopy (Dash + FastAPI dashboard,
port 8050). Canopy is **both** a metrics consumer (from cascor / data)
**and** a metrics producer (its own observability + WS broadcast). In-scope:

- Self-instrumentation: Prometheus middleware, `/metrics`, build info,
  WebSocket message/connection gauges
- Health endpoints (`/v1/health`, `/v1/health/live`, `/v1/health/ready`,
  deprecated `/health`, `/api/health`)
- Internal training-state stores (`TrainingState`, `CandidatePool`,
  `TrainingMonitor`)
- WebSocket pathways: `/ws/train` (broadcast metrics) and `/ws/control`
  (control commands)
- Frontend metric panels (`metrics_panel.py`,
  `candidate_metrics_panel.py`)
- Sentry integration
- REST endpoints `/api/metrics`, `/api/metrics/history`
- Tests for all of the above

Out-of-scope: dashboard UX, plotting library specifics, layout
persistence beyond its impact on metric display.

---

## 2. Pre-existing evidence (from initial survey)

### 2.1 Surface inventory

**Self-observability** (`src/observability.py`):
- `PrometheusMiddleware` (lines 100–170)
- `set_build_info()`, `inc_websocket_messages()`,
  `set_websocket_connections()` (line 200+)
- `/metrics` mounted in `src/main.py:290–295` if `metrics_enabled`

**Health** (`src/health.py:24–72`, `src/main.py:680–740`):
- `/v1/health` combined
- `/v1/health/live` liveness
- `/v1/health/ready` with dep probes (JuniperData, JuniperCascor) via
  `asyncio.to_thread()`
- Deprecated aliases: `/health`, `/api/health`

**Internal stores** (`src/backend/training_monitor.py`):
- `CandidatePool` (lines 50–200) — candidate metrics
- `TrainingState` — global instance at `src/main.py:112`
- `WebSocketManager` (`src/communication/websocket_manager.py`) —
  broadcast and connection state
- Standardized WS schema (`websocket_manager.py:36–119`)

**Endpoints** (`src/main.py`):
- `/api/metrics` (line 843), `/api/metrics/history` (line 853) — REST
- `/ws/train` real-time stream
- `/ws/control` (line 462+) with per-command timeouts at lines 114–124
  (`_PHASE_D_CONTROL_TIMEOUTS`)

**Frontend**:
- `src/frontend/components/metrics_panel.py`
- `src/frontend/components/candidate_metrics_panel.py`
- Dashboard manager (`src/frontend/dashboard_manager.py`) — accesses
  `enable_ws_control_buttons` (defined in `settings.py:186`,
  auto-derived from env via Pydantic `env_prefix`).
  **NOTE (audit 2026-04-24)**: prior memory file
  `project_phase_d_control_buttons_shipped.md` cited
  `dashboard_manager.py:1898`; that line no longer exists (file has
  been refactored / split). The setting itself is intact; only the
  citation is stale. Update the memory file after Phase 1 inventory.

### 2.2 Settings (env vars: `JUNIPER_CANOPY_*` with `CASCOR_*` legacy
fallback emitting deprecation warnings)

| Setting | Notes |
|---------|-------|
| `JUNIPER_CANOPY_METRICS_ENABLED` | default off; gates middleware + endpoint |
| `JUNIPER_CANOPY_SENTRY_DSN` | None default; no Sentry |
| `JUNIPER_CANOPY_SENTRY_TRACES_SAMPLE_RATE` | per `settings.py` |
| WebSocket: `max_connections`, `heartbeat_interval`, `idle_timeout`, `max_message_size_*` | `settings.py:84–102` |

WebSocket message size limits (`max_message_size_training` 4 KB,
`max_message_size_control` 64 KB) are **not documented** as breaking
constraints.

### 2.3 Dependencies

- `prometheus-client>=0.20.0`, `sentry-sdk>=2.0.0` (lazy import)
- `juniper-data-client>=0.3.0`, `juniper-cascor-client>=0.1.0` (optional
  extras — versions may lag and need bumps to consume the changes from
  per-app reviews 02 / 05)
- `websockets>=12.0`, `fastapi>=0.100.0`, `a2wsgi>=1.10.0`

### 2.4 Tests

- `test_observability.py` — formatter, middleware, Sentry
- `test_observability_coverage.py` — WS metrics, build info, demo flag
- `test_health.py` — 152 lines; models, probes, endpoints
- `test_metrics_panel.py` — panel rendering
- `test_websocket_comprehensive.py` — **869 lines** (initial survey
  said 31 K; corrected) — message schema, state/metrics/topology
- `test_candidate_metrics_stream.py` (integration)
- `test_metrics_layouts_api.py` — **257 lines** (initial survey said
  9.5 K; corrected) — layout persistence
- `test_websocket_message_schema.py` (integration)
- ~28 disabled tests; 80% coverage target
- **Marker usage**: markers (`requires_cascor`, `requires_redis`,
  `requires_cassandra`) are *registered* in `pyproject.toml:247–261`
  but applied to **only ~2 test sites** in the repo. Risk: gated
  selectors in CI may have no effect; coverage gaps hidden behind
  marker filters.

### 2.5 Already-suspected findings

| # | Hypothesis | File:line |
|---|------------|-----------|
| H1 | No OpenTelemetry — Prometheus only; no distributed tracing | observability.py |
| H2 | Sentry off by default (DSN None) — production may run without error tracking | settings.py |
| H3 | WebSocket message envelope lacks message-ID for request-response correlation (only `command_id` for control) | websocket_manager.py:36–119 |
| H4 | No trace_id propagation in request middleware | observability.py |
| H5 | Deprecated health endpoints (`/health`, `/api/health`) still active; no sunset timeline | main.py:664–677 |
| H6 | Health-check logic duplicated between `/v1/health` and `/api/health` | main.py |
| H7 | `training_state` global + separately maintained in demo backend + fetched from cascor → reconciliation complexity at startup | main.py:201–222 |
| H8 | WS message size limits undocumented as breaking | settings.py |
| H9 | Metrics off by default — production may run blind | settings.py |
| H10 | No mock-backend metrics tests when `juniper-cascor-client` not installed (skipif) — coverage hole | tests |
| H11 | No load tests for WS broadcast at scale (1000+ connections) | tests |
| H12 | No tests for Prometheus scrape-format validity | tests |
| H13 | No tests for label-cardinality control | tests |
| H14 | TODOs in `dashboard_manager.py:29`, `:220`, `training_monitor.py:32`, `websocket_manager.py:23` (mostly empty placeholders or magic-number cleanups) | source |
| H15 | Optional client deps (`juniper-data-client`, `juniper-cascor-client`) version pins lag — may need bumps to consume changes from upstream per-app reviews | pyproject.toml |
| H16 | `request_id` ContextVar (`observability.py:14, 50`) is propagated for HTTP requests but **not** into WebSocket message envelopes. Result: a logical "session" cannot be traced from REST → WS → cascor stream. Refines original H3/H4. | `observability.py` + `websocket_manager.py` |
| H17 | `requires_cascor` / `requires_redis` / `requires_cassandra` markers registered but applied to only ~2 test sites — CI marker selectors are functionally inert | tests |
| H18 | `/metrics` exposure posture undocumented (auth? rate limit? trusted-network only?) — same cross-cutting concern as cascor H15 / data H11 | observability + main.py mount |
| H19 | `juniper-deploy` healthcheck wiring for canopy container not verified against `/v1/health/live` and `/v1/health/ready` — risk of orchestrator probing the deprecated `/health` instead | `juniper-deploy/` Docker config |
| H20 | **3 of 6 metrics defined-but-unused**: `juniper_canopy_websocket_connections_active`, `juniper_canopy_websocket_messages_total`, `juniper_canopy_demo_mode_active` — helpers defined in `observability.py:189–200, :214, :224, :233` but no production callsite. Panels in any dashboard will be empty. See `08_METRIC_CATALOG.md` §6. | `observability.py` + consumer sites missing |
| H21 | **Env-var surface undercount**: extraction found **23 env vars** not listed in §2.2, including an entire security surface (CSRF, per-IP caps, audit-log path, message-size limits, WS timeout matrix). These are not bonuses — they gate whether `/ws/control` even accepts a connection. See `07_ENV_VAR_INVENTORY.md` §6. | settings.py:87–195 (many) |
| H22 | `JUNIPER_CANOPY_AUDIT_LOG_PATH` defaults to `/var/log/canopy/audit.log` — may not exist in container or local-dev; if `AUDIT_LOG_ENABLED=True` (default), logger may raise on write | settings.py:171–172 |

---

### 2.6 Audit corrections (2026-04-24)

- `test_metrics_layouts_api.py` and `test_websocket_comprehensive.py`
  line-count claims in §2.4 were **inflated by ~30–100×** in the
  initial survey. Corrected above. The *substance* of those tests
  (message schema, state streaming, layout persistence) is unchanged.
- `dashboard_manager.py:1898` reference removed; replaced with
  pointer to `settings.py:186` (see §2.1 note).
- All `pyproject.toml` dependency claims in §2.3 verified.
- `request_id` ContextVar IS propagated for HTTP requests (audit
  found `RequestIdMiddleware` at `observability.py:14, 50`) — H3/H4
  refined into new H16 to capture the **WS-envelope** gap, which is
  the actual problem.

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk surface against current `main`.
2. Build a metrics catalog (Prometheus + custom WS gauges) similar to
   the cascor catalog, with cardinality bounds.
3. Reconcile WS schema versus the schemas documented in plan 03 (cascor
   producer) and plan 05 (cascor-client consumer). Drift is the
   highest-risk category for canopy because it sits at the consumer end
   of two streams.
4. Inventory legacy `CASCOR_*` aliases — verify deprecation path is
   active and dated.

### Phase 2 — Functionality verification

1. Spin up the full stack: juniper-data → juniper-cascor → juniper-canopy
   (use `juniper-deploy` Docker stack or local bring-up).
2. Open canopy, drive a training session; watch metrics flow end-to-end.
3. Issue 1 000+ rapid metric updates via cascor; observe canopy WS
   broadcast behavior (back-pressure, drop, queue growth).
4. Disconnect/reconnect cascor mid-session; observe canopy recovery.
5. Curl canopy `/metrics`; verify Prometheus format parses; verify
   WS gauges (`_websocket_connections`, `_websocket_messages_total`)
   reflect reality.

### Phase 3 — Test-suite audit

1. Full run:
   ```bash
   conda activate JuniperCanopy
   cd juniper-canopy
   pytest src/tests -v --tb=short \
     --cov=src --cov-report=term-missing
   ```
2. Inventory ~28 disabled tests — for each, confirm whether the skip is
   still valid or should be re-enabled.
3. Verify metrics-panel and metrics-stream tests assert the actual
   metric values reaching the panels, not just panel render success.
4. Identify gaps from §2.5 H10–H13.

### Phase 4 — Issue classification

Apply ecosystem framework §3.1–3.2.

### Phase 5 — Remediation design

See §5.

### Phase 6 — Validation

1. Land remediations on a worktree branch.
2. Re-run unit + integration suites.
3. Full-stack smoke per `juniper-ml/CLAUDE.md` — confirm cascor + data +
   canopy still interoperate.
4. Run any cross-repo integration suite that includes canopy.

### Phase 6.5 — Security, control-endpoint & deploy review (added)

1. **`/v1/control` auth & rate-limit**: confirm whether control
   endpoints require auth and whether `rate_limit_enabled`
   (`settings.py:164`) actually applies to them. Document the
   chosen posture.
2. **`/metrics` exposure** (H18): coordinate with cascor H15 and
   data H11 — single ecosystem decision.
3. **`juniper-deploy` healthcheck wiring** (H19): inspect
   `juniper-deploy/docker-compose.yml` (or k8s manifests) to confirm
   container HEALTHCHECK and orchestrator readiness probe target
   `/v1/health/live` and `/v1/health/ready` — NOT the deprecated
   `/health` aliases.
4. **Marker hygiene** (H17): for each `@pytest.mark.requires_*`
   marker registered in `pyproject.toml:247–261`, either apply it
   meaningfully or remove the registration. Inert markers mislead
   readers about coverage gating.

### Phase 6.6 — CI/CD review (added)

1. Read `.github/workflows/*.yml`; for each marker, record whether
   CI selects, excludes, or ignores it. Cross-check against actual
   marker usage in the suite (H17).
2. Confirm Prometheus-format parse test exists for `/metrics`.
3. Confirm dependency-audit covers the optional `juniper-data-client`
   and `juniper-cascor-client` extras that pull metrics into canopy.

### Phase 7 — Documentation

1. Update `juniper-canopy/CLAUDE.md` if contracts changed.
2. Update `juniper-canopy/docs/` for new env vars / endpoints.
3. CHANGELOG entry.

---

## 4. Deliverables

| File | Contents |
|------|----------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan |
| `REVIEW_FINDINGS.md` | Findings register |
| `REVIEW_VALIDATION.md` | Test logs + full-stack evidence |
| `METRIC_CATALOG.md` | Self-emitted metrics catalog |
| `WS_SCHEMA_RECONCILIATION.md` | Reconciliation against plans 03 + 05 |

---

## 5. Remediation framework — preliminary design notes

### H3 + H4 (no message-ID / no trace_id propagation)

**Options**:

- **Option A** — Add `traceparent`/`tracestate` middleware (W3C trace
  context) on incoming requests; propagate to outgoing
  `juniper-data-client` and `juniper-cascor-client` calls; include in WS
  envelopes. Pros: standards-based; works with any tracing backend.
  Cons: needs OTel SDK (or hand-roll the headers).
- **Option B** — Generate a `correlation_id` per request/WS message
  (UUID); echo in logs and downstream calls. Pros: no SDK dependency.
  Cons: not interoperable with external tracing systems.
- **Option C** — Defer until OpenTelemetry decision is made
  ecosystem-wide.

**Provisional recommendation**: **Option B** as the immediate
incremental win (correlation across the local stack); **Option A** as
the longer-term direction once the ecosystem decides on OTel
(coordinate via roadmap §5.2).

### H5 + H6 (deprecated health endpoints + duplicated logic)

**Provisional**: pick a sunset version (e.g. v0.5.0); add a
`Sunset:` HTTP header on `/health` and `/api/health` with that date;
collapse implementation into a single function. Trivial-to-Small effort.

### H7 (state reconciliation complexity)

**Provisional**: introduce a `StateBackend` interface; provide
implementations `DemoBackend`, `CascorClientBackend`, `LocalBackend`;
select via setting at startup; remove the conditional reconciliation
branch in `main.py:201–222`. Architectural finding; Medium effort.

### H10–H13 (test coverage gaps)

**Provisional**: add a fixture that injects a fake cascor-client (mock
metric stream) so tests are not skipped when the optional dep is
missing. Add a Prometheus-format parse test. Add a label-cardinality
guard test. Add a small (10–100 connection) WS load test in CI;
defer the 1000+ scale test to a manual perf job.

### H15 (optional dep version lag)

**Provisional**: bump the lower bounds when plans 02 and 05 ship their
remediations; coordinate via ecosystem roadmap §7 synthesis.

(Other hypotheses receive full remediation blocks during the actual
review.)

---

## 6. Tooling & commands

```bash
conda activate JuniperCanopy

# Full suite
cd juniper-canopy
pytest src/tests -v --tb=short \
  --cov=src --cov-report=term-missing

# Targeted observability paths
pytest src/tests/unit/test_observability.py \
       src/tests/unit/test_observability_coverage.py \
       src/tests/unit/test_health.py -v

# Local smoke (requires data + cascor running)
JUNIPER_CANOPY_METRICS_ENABLED=true \
  python -m src.main &
sleep 3
curl -s http://localhost:8050/metrics | grep juniper_canopy | head -30
curl -s http://localhost:8050/v1/health/ready | jq .
```

---

## 7. Owner / sign-off

- Plan owner: (assign during distribution)
- Reviewer: (assign during distribution)
- Sign-off blocked on: ecosystem roadmap §6.1 + full-stack integration
  pass.
