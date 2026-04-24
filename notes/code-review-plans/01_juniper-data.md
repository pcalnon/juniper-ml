# juniper-data — Metrics & Monitoring Code Review Plan

- **Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-data/`
- **Target file once distributed**: `juniper-data/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
- **Inherits**: `00_ECOSYSTEM_ROADMAP.md` (issue framework §3, validation gates §6, procedural constraints §8)
- **Created**: 2026-04-24
- **Phase**: A — Foundation contracts (run first)

---

## 1. Scope

Metrics & monitoring surface of juniper-data (FastAPI dataset-generation service, port 8100).
In-scope:

- Service-level Prometheus exposition (`/metrics`) and middleware
- Health endpoints (`/v1/health`, `/v1/health/live`, `/v1/health/ready`)
- Request-level instrumentation (latency, error rates, request counts)
- Dataset-generation domain metrics (rows produced, generation time, cache)
- Logging stack as observability substrate (structured JSON, request_id)
- Sentry integration
- Tests covering all of the above

Out-of-scope: dataset semantics, NPZ format, generator algorithms, REST contract surface beyond the metrics/health endpoints.

---

## 2. Pre-existing evidence (from initial survey)

This section is **not** the review — it is the prior survey, so the reviewer can start from a known baseline.
Verify each item before treating it as fact.

### 2.1 Surface inventory

- `/metrics` mounted at `juniper_data/api/app.py:121` via `get_prometheus_app()`, gated on `JUNIPER_DATA_METRICS_ENABLED=true`.
- `/v1/health` (`health.py:20–27`) — shallow.
- `/v1/health/live` (`health.py:30–40`) — bare liveness.
- `/v1/health/ready` (`health.py:43–76`) — deep: storage path, NPZ count, `DependencyStatus`, `ready|degraded`.
- `PrometheusMiddleware` (`observability.py:70–105`):
  - `juniper_data_http_requests_total{method,endpoint,status}` (Counter)
  - `juniper_data_http_request_duration_seconds{method,endpoint}` (Histogram)
- `record_dataset_generation()` and `set_datasets_cached()` defined at `observability.py:218–238` but **not called from production code**.
- Histogram buckets for generation duration: `(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, inf)` at `constants.py:82–94`.

### 2.2 Settings (env var → effect)

| Env var                                  | Default | Effect                                            |
|------------------------------------------|---------|---------------------------------------------------|
| `JUNIPER_DATA_METRICS_ENABLED`           | `False` | Mounts `/metrics` and adds `PrometheusMiddleware` |
| `JUNIPER_DATA_LOG_LEVEL`                 | `INFO`  | Root logger level                                 |
| `JUNIPER_DATA_LOG_FORMAT`                | `text`  | `json` switches to `JuniperJsonFormatter`         |
| `JUNIPER_DATA_SENTRY_DSN`                | unset   | Sentry init                                       |
| `JUNIPER_DATA_SENTRY_TRACES_SAMPLE_RATE` | `0.1`   | Sentry transaction sampling                       |

### 2.3 Dependencies

- `prometheus-client>=0.20.0` (extra `observability`)
- `sentry-sdk[fastapi]>=2.0.0` (core)
- No OpenTelemetry, no slowapi, no metrics-from-logs pipeline.

### 2.4 Tests

- `test_observability.py`: `JuniperJsonFormatter`, `RequestIdMiddleware`, `configure_logging`, `configure_sentry`, `PrometheusMiddleware`, `TestDatasetMetrics` (covers `record_dataset_generation`).
- `test_health_enhanced.py`: model + endpoint tests for `/v1/health*`.
- No integration test that the live `/metrics` endpoint emits valid Prometheus exposition format.
- No test verifying `metrics_enabled=False` vs `True` middleware installation behavior end-to-end.

### 2.5 Already-suspected findings (to be confirmed during review)

These are *hypotheses* from the survey, not confirmed findings.
The review must validate each, classify per the framework, and remediate.

| #   | Hypothesis                                                                                                               | File:line                                                |
|-----|--------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| H1  | Dataset-generation domain metrics defined but never recorded — observability surface:                                    | `observability.py:218–238`, `datasets.py` POST endpoint  |
|     | -- "architecturally complete but operationally hollow"                                                                   |                                                          |
| H2  | Cache-hit path exists but emits no metric                                                                                | `datasets.py:98`                                         |
| H3  | Failure-status histogram dropped (`status != "success"` skips histogram observe)                                         | `observability.py:228`                                   |
| H4  | Histograms have no exemplars (no trace correlation)                                                                      | `observability.py:83–87`                                 |
| H5  | Metrics off by default — production may run blind                                                                        | `settings.py:78`                                         |
| H6  | Generator execution time untracked                                                                                       | `datasets.py:107`                                        |
| H7  | Readiness probe walks all NPZ files (potential N+1 / O(N) glob each request)                                             | `health.py:57`                                           |
| H8  | No integration test for `/metrics` endpoint format                                                                       | tests                                                    |
| H9  | Health response timestamp always "now" — no staleness detection                                                          | `health.py` models, line 24                              |
| H10 | Logs lack W3C trace IDs — no Tempo/Jaeger correlation possible                                                           | `JuniperJsonFormatter`, `observability.py:31–49`         |
| H11 | `/metrics` **NOT** in `EXEMPT_PATHS` (`constants.py:23–31`): API key auth, rate limits if enabled. Borked?               | `app.py:121` mount + `constants.py:23–31` exemption list |
|     | -- Risks: scrape fails w/o Prometheus credentials, OR info leak, if exempted w/o security review.                        |                                                          |
| H12 | `endpoint` label uses `request.url.path` (raw) at `observability.py:98` — query-string / dynamic-ID cardinality risk     | `observability.py:98`                                    |
| H13 | **Env-var surface undercount**: extraction surfaced `JUNIPER_DATA_RATE_LIMIT_ENABLED` / `_REQUESTS_PER_MINUTE` /         | settings.py:120, 143–144, 148                            |
|     | -- `_API_KEYS` / `_SENTRY_SEND_PII` — 4 settings not in §2.2. See `07_ENV_VAR_INVENTORY.md` §4.                          |                                                          |
| H14 | Confirmed from `08_METRIC_CATALOG.md` §4: of 6 metrics, 3 (dataset-generation counter/histogram + cached-datasets gauge) | observability.py:199–212                                 |
|     | -- are defined-but-unused — the **H1 operational-hollowness finding is now confirmed by extraction**.                    |                                                          |

---

### 2.6 Audit corrections (2026-04-24)

The initial survey was audited against `main` HEAD. Corrections applied:

- `health.py:20–27` — substantive content correct; line 20 is the `@router.get` decorator (not docstring). Treat as accurate.
- All other `:line` citations in §2.1–§2.4 verified.
- `__version__` is exported from `juniper_data/__init__.py` (verify during Phase 1 inventory; may be useful for client-server schema pinning).

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk the metrics surface from §2 against current `main`; record any drift since the survey (this app changes; survey was 2026-04-24).
2. Catalog every Prometheus metric (name, type, labels, help text) into a table; flag label-cardinality risks (especially `endpoint`).
3. Catalog every env var with observability effect; verify default behavior matches documentation.
4. Cross-check versus parent CLAUDE.md "Service Ports" table.

**Exit criterion**: Inventory section in `notes/REVIEW_FINDINGS.md` matches reality on `main` HEAD.

### Phase 2 — Functionality verification

1. Run the service locally with `JUNIPER_DATA_METRICS_ENABLED=true`; curl `/metrics` and verify Prometheus format parses (use `prometheus_client.parser.text_string_to_metric_families`).
2. Issue 100+ requests across 5+ endpoints; confirm counter increments and histogram observes match expectations.
3. Trigger a known failure (e.g. malformed POST); confirm the error path does or does not record histogram (validates H3).
4. Run health probes under: nominal state, missing storage path, dataset count = 0, dataset count = 10 000 (validates H7 cost).

**Exit criterion**: Each pre-existing hypothesis is either upgraded to a confirmed finding or downgraded to "not reproduced".

### Phase 2.5 — Security & cardinality review (added)

1. **Auth posture**: confirm whether `/metrics` is intended to be public-on-localhost-only or scraped over a trusted network.
    - Decide: add to `EXEMPT_PATHS`, or document the API-key requirement for Prometheus configuration.
2. **Cardinality bounds**: enumerate every Prometheus label across the middleware and dataset metrics; classify each label as `enumerated`, `bounded`, or `unbounded`.
    - For unbounded labels (notably `endpoint` when raw paths are used), produce a remediation option in §5 (recommend FastAPI route templates: `request.scope["route"].path`).
3. **Log PII**: review `JuniperJsonFormatter` output and the request middleware to confirm no API keys, dataset payloads, or user identifiers leak into log records.
4. **Info disclosure on health-ready**: `/v1/health/ready` reports storage path and dataset count — confirm this is acceptable for the deployment trust boundary.

### Phase 2.6 — CI/CD review (added)

1. Read `.github/workflows/ci.yml` (and any other workflow files); record which test markers are run, which are excluded, and what coverage thresholds gate the pipeline.
2. Verify that the `/metrics` endpoint format is exercised in CI (Prometheus `text_string_to_metric_families` parse).
3. Verify that secret scanning / dependency audit jobs cover the observability extras.
4. If `pip-audit` is in CI, ensure the `observability` extra is included in the audit set.

### Phase 3 — Test-suite audit

1. Run the full test suite per app conventions:

    ```bash
    cd juniper-data
    pytest juniper_data/tests/ -v --tb=short --cov=juniper_data --cov-report=term-missing
    ```

2. Record: collection errors, runtime errors, runtime warnings, skipped tests, xfail tests, marker filters that exclude tests.
3. For each metrics-related test, verify the assertion actually checks the metric value, not just `200 OK`.
4. Identify coverage gaps: lines/branches in `observability.py`, `health.py` not covered.
5. Inventory missing test types per the prompt's required categories (unit, integration, regression, e2e, performance, security).

**Exit criterion**: Test-audit table in `notes/REVIEW_FINDINGS.md` lists every metrics-touching test, its coverage assertion, and its gap.

### Phase 4 — Issue classification & risk assessment

For every confirmed finding from Phases 1–3:

1. Assign type per ecosystem framework §3.1, one of the following:
    - Architectural
    - Logical
    - Syntactical
    - Code Smell
    - Departure from Requirements
    - Deviation from Best Practices
    - Formatting & Linting
2. Assign all five characteristics per §3.2.
3. Compute Priority = Severity × Likelihood; sort findings by Priority.

**Exit criterion**: Findings register complete, sorted, reviewed.

### Phase 5 — Remediation design

For every Critical / High finding:

1. Root cause analysis (not symptom).
2. ≥2 remediation options for Critical, ≥1 for High, with strengths, weaknesses, risks-introduced, guardrails.
3. Recommendation with reasoning.
4. Validation plan: specific tests to add, manual verification, post-deploy metrics to watch.

For Medium findings: ≥1 option + validation plan.

For Low / Informational: one-line entry, no remediation design required.

### Phase 6 — Validation

1. Apply remediations on a worktree branch.
2. Re-run full test suite — must pass per §6.1 of the ecosystem roadmap.
3. Re-run Phase 2 functional verification end-to-end.
4. Update findings register: each Critical/High finding marked `Remediated`, `Deferred`, or `Won't Fix` with reason.

### Phase 7 — Documentation

1. Update `juniper-data/CLAUDE.md` if the public observability contract changed.
2. Update `juniper-data/docs/` if env vars / endpoints / metric names changed.
3. Add CHANGELOG entry.
4. Hand back to ecosystem roadmap §7 synthesis.

---

## 4. Deliverables

To be produced in `juniper-data/notes/` as the review proceeds:

| File                                         | Contents                                             |
|----------------------------------------------|------------------------------------------------------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan (or its distributed copy)                  |
| `REVIEW_FINDINGS.md`                         | All findings, classified, with remediation blocks    |
| `REVIEW_VALIDATION.md`                       | Test-run logs, before/after metric outputs, sign-off |

---

## 5. Remediation framework — preliminary design notes

These are *prior thoughts* on the hypotheses in §2.5; they must be revisited once findings are confirmed.

### H1 (operationally hollow domain metrics)

**Provisional options**:

- **Option A** — Wire `record_dataset_generation()` into the POST `/v1/datasets` handler.
  - Pros: minimal code; uses existing helpers.
  - Cons: ties metric emission to a single endpoint; if generation moves to a background task later, the metric needs to move too.
- **Option B** — Decorator/middleware on the dataset-generation service layer.
  - Pros: emission survives endpoint refactors; single instrumentation point.
  - Cons: indirection; harder to spot during debugging.
- **Option C** — Pull-style metrics (don't emit on every generation; query a `DatasetStore.stats()` once on `/metrics` scrape).
  - Pros: zero hot-path cost.
  - Cons: loses per-event histograms; depends on store internals.

**Provisional recommendation**: Option A first (smallest change with biggest visibility win), with a note to re-evaluate Option B if the service grows additional generation entry points.

### H3 (failure-status histogram dropped)

**Provisional**: drop the `status == "success"` guard on histogram observe; add a `status` label to the histogram instead.

- Risk: cardinality (only 5 HTTP status classes, acceptable).
- Validation: integration test that forces a 500 and asserts the histogram observed.

### H5 (metrics off by default)

**Cross-cutting**: see `00_ECOSYSTEM_ROADMAP.md` §5.4.
Defer the policy choice to the synthesis; document the recommendation locally.

### H7 (readiness probe NPZ glob cost)

**Provisional**: cache the NPZ count with a short TTL (e.g. 5 s) so a healthcheck loop at 1 Hz does not iterate the directory every request.

- Risk: stale count on rapid additions (acceptable for readiness signal).
- Alternative: switch from "count files" to "directory accessible".

(All other hypotheses receive their full remediation blocks during the actual review.)

---

## 6. Tooling & commands

```bash
# Activate env
conda activate JuniperData

# Full test run
cd juniper-data
pytest juniper_data/tests/ -v --tb=short --cov=juniper_data --cov-report=term-missing

# Coverage gap report (metrics + health only)
pytest juniper_data/tests/ --cov=juniper_data.api.observability --cov=juniper_data.api.routes.health --cov-report=term-missing

# Local metrics smoke test
JUNIPER_DATA_METRICS_ENABLED=true python -m juniper_data.api &
sleep 2
curl -s http://localhost:8100/metrics | head -50
curl -s http://localhost:8100/v1/health | jq .
curl -s http://localhost:8100/v1/health/ready | jq .
```

---

## 7. Owner / sign-off

- **Plan owner**: (assign during distribution)
- **Reviewer**: (assign during distribution)
- **Sign-off blocked on**: ecosystem-roadmap §6.1 gates green.
