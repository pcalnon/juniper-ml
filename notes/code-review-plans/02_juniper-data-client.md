# juniper-data-client — Metrics & Monitoring Code Review Plan

**Target repo path on disk**: `/home/pcalnon/Development/python/Juniper/juniper-data-client/`
**Target file once distributed**: `juniper-data-client/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`
**Inherits**: `00_ECOSYSTEM_ROADMAP.md`
**Created**: 2026-04-24
**Phase**: A — Foundation contracts (run after juniper-data review)

---

## 1. Scope

Metrics & monitoring surface of juniper-data-client (sync HTTP client
library for juniper-data). The library is **not** a service; the metrics
surface is narrow and consists of:

- Health-probe API methods (`health_check`, `is_ready`)
- Client-side timing / retry behavior visible to callers
- Any callbacks/hooks the client exposes for instrumentation
- Tests covering the above

Out-of-scope: dataset payload validation, NPZ contract, generic HTTP
behavior unrelated to monitoring.

---

## 2. Pre-existing evidence (from initial survey)

### 2.1 Surface inventory

- `client.py:205–215` — `health_check()` → calls `/v1/health`, returns
  raw JSON with `status` field. **No timing collected.**
- `client.py:217–227` — `is_ready()` → polls `/v1/health/ready` for
  `status == "ready"`. **Silent failure — returns `False` on any error.**
- `client.py:137–142` — `_create_session()` configures `urllib3.Retry`:
  - status_forcelist `[429, 500, 502, 503, 504]`
  - allowed_methods includes `POST, PATCH, DELETE` (idempotency unstated)
  - total = 3 retries
  - backoff_factor = 0.5
- **Retries silent**: no metric, no callback, no caller-visible counter.

### 2.2 Configuration

| Setting | Default | Source |
|---------|---------|--------|
| `base_url` | `http://localhost:8100` | constructor |
| `timeout` | 30 s | `constants.py:25` |
| `retries` | 3 | `constants.py:26` |
| `backoff_factor` | 0.5 | `constants.py:27` |
| pool: connections / maxsize | 10 / 10 | `constants.py:50–51` |
| ready polling: interval / timeout | 0.5 s / 30 s | `constants.py:40–41` |
| `JUNIPER_DATA_API_KEY` | env-only | `constants.py:47` |

### 2.3 Dependencies

- `requests>=2.28.0`
- `urllib3>=2.0.0`
- **No** Prometheus, OpenTelemetry, StatsD, or instrumentation libs.

### 2.4 Tests

- `TestHealthEndpoints` (`test_client.py:127–182`): success, ready=true,
  ready=false-on-error, ready=false-on-connection-error.
- `TestErrorHandling` (`test_client.py:530–598`): connection, timeout,
  generic, server-error, error-detail extraction.
- `test_performance.py:194–200, 287–292`: health latency benchmarks
  using `_measure()` helper — measured externally, not exposed by client.

### 2.5 Already-suspected findings

| # | Hypothesis | File:line |
|---|------------|-----------|
| H1 | `is_ready()` swallows all `JuniperDataClientError` — caller cannot tell timeout from 404 | `client.py:226–227` |
| H2 | No callback / hook API for caller instrumentation | (absent) |
| H3 | Retry count and backoff delays not exposed to caller | `client.py:137–142` |
| H4 | Single 30 s timeout used for health probe — slow backend → timeout → silent "not ready" | `constants.py:25, 40` |
| H5 | Sync-only blocking I/O — risk of thread-pool saturation in juniper-cascor / juniper-canopy callers | (architectural) |
| H6 | POST/PATCH/DELETE retried without documented idempotency contract — risk of partial batch effects | `client.py` retry config + `batch_*` methods |
| H7 | No env-var overrides for pool size, per-endpoint timeout, retry threshold | `constants.py` |
| H8 | No tests for retry exhaustion behavior | tests |
| H9 | No tests asserting timeout on health endpoint | tests |
| H10 | No connection-pool exhaustion test | tests |
| H11 | No test verifying `is_ready()` error-swallow behavior produces meaningful logs | tests |
| H12 | `requests.Session` is shared across calls (`client.py` constructor) but `requests.Session` is **not thread-safe by design** — risk under concurrent caller threads in juniper-cascor / juniper-canopy | `client.py` (Session creation) |
| H13 | `wait_for_ready(timeout=...)` is the actual caller pattern in juniper-cascor's app start-up — not `is_ready()`. Plan must verify both surfaces, not just `is_ready()`. | juniper-cascor `src/api/app.py` (calls into client) |

---

### 2.6 Audit corrections (2026-04-24)

The plan was audited against `main` HEAD. Findings:

- All cited file:line references verified.
- `py.typed` marker is present (`pyproject.toml:61`) — typed export
  flows to downstream consumers; type-drift surfaces during their
  builds, which is good.
- `__version__ = "0.4.0"` exported from `juniper_data_client/__init__.py`.
  Useful for future schema-pinning between client and server.
- A `wait_for_ready()` method exists and is the actively-used surface
  in juniper-cascor; original plan over-focused on `is_ready()`.
  Folded into H13 above.

---

## 3. Review phases

### Phase 1 — Inventory & freeze

1. Re-walk public API; record any drift since the survey.
2. Build a table of every public method that crosses an HTTP boundary,
   with: method name, endpoint hit, error path, retry policy, exposed
   metric, exposed callback. Flag any "(none)" cells as candidate findings.
3. Reconcile constants (`constants.py`) versus the juniper-data server's
   actual contract (port, paths) — must match the ecosystem roadmap §5.1
   port table.

### Phase 2 — Functionality verification

1. Spin up juniper-data locally; exercise `health_check()`, `is_ready()`
   under: nominal, server down, server slow (>30 s), server returning
   500, server returning 503-then-200 (retry success), server returning
   500-500-500 (retry exhaustion).
2. Verify `is_ready()` behavior matches docstring under each scenario.
3. Confirm whether retry attempts emit anything observable (logs at what
   level? structured fields?). Document the gap.

### Phase 3 — Test-suite audit

1. Full run:
   ```bash
   cd juniper-data-client
   pytest tests/ -v --tb=short --cov=juniper_data_client --cov-report=term-missing
   ```
2. Record collection / runtime errors, warnings, skipped tests.
3. Verify `TestHealthEndpoints` assertions actually exercise the wire
   behavior (not just mock returns).
4. Identify missing test scenarios from §2.5 (H8–H11).

### Phase 4 — Issue classification

Apply ecosystem framework §3.1–3.2 to every confirmed finding.

### Phase 5 — Remediation design

See §5 below for preliminary remediation thoughts on the highest-impact
hypotheses.

### Phase 6 — Validation

1. Land remediations.
2. Re-run full suite.
3. Run cross-repo integration smoke per `juniper-ml/CLAUDE.md`:
   `cd juniper-data-client && pytest tests/ -v` and downstream
   `cd juniper-cascor/src/tests && bash scripts/run_tests.bash` to
   confirm no consumer breakage.

### Phase 6.5 — CI/CD review (added)

1. Read `.github/workflows/ci.yml`; record:
   - Python version matrix (currently 3.12 / 3.13 / 3.14)
   - Coverage gate (currently 80% fail-under)
   - Whether `pre-commit` is run in CI
   - Whether `pip-audit` is run on the resolved dependency tree
2. Verify the test job exercises both `health_check()` and
   `wait_for_ready()` paths under failure scenarios (covers H11, H13).
3. If a future test job is added for retry exhaustion (H8), wire it
   into the CI matrix so regressions cannot land silently.

### Phase 7 — Documentation

1. Update README and CHANGELOG if API surface changed.
2. Update `juniper-data-client/CLAUDE.md` if the contract changed.
3. Hand back to ecosystem roadmap §7 synthesis.

---

## 4. Deliverables

| File | Contents |
|------|----------|
| `CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | This plan |
| `REVIEW_FINDINGS.md` | Classified findings + remediation blocks |
| `REVIEW_VALIDATION.md` | Test-run results + before/after evidence |

---

## 5. Remediation framework — preliminary design notes

### H1 (silent error swallowing in `is_ready`)

**Options**:

- **Option A** — Add a `raise_on_error: bool = False` keyword to
  `is_ready()`. Callers who care can opt in. Pros: backward-compatible;
  minimal change. Cons: silent default unchanged; new code paths likely
  to keep using the silent default.
- **Option B** — Replace `is_ready()` with `readiness_status()` returning
  an enum: `READY | NOT_READY | UNREACHABLE | TIMEOUT | UNAUTHORIZED`.
  Pros: callers see the actual reason; no information loss.
  Cons: API change; deprecation cycle needed.
- **Option C** — Keep `is_ready()` but emit a structured warning log on
  error swallow; expose `last_readiness_error` attribute. Pros: zero API
  break. Cons: callers must opt in to inspect; race-prone state
  attribute.

**Provisional recommendation**: **Option B** as the long-term shape,
with **Option A** added in the same release as a backward-compatible
bridge. Justification: the loss of error type at the boundary is the
root cause of the observability gap; A alone doesn't fix it.

**Validation**: parametrized test covering each enum value.

### H2 + H3 (no callback / hook API + invisible retries)

**Options**:

- **Option A** — Accept an optional `request_hook: Callable[[RequestEvent], None]`
  in the client constructor; emit events for `request_start`,
  `request_end`, `retry`, `error`. Pros: composable; integrators can
  plumb to Prometheus, OTel, logs. Cons: defines a new event interface
  the project must own.
- **Option B** — Integrate `urllib3` `HTTPAdapter`-level hooks (mount
  custom adapter that records timings into a `client.metrics` snapshot).
  Pros: contained inside client. Cons: `urllib3` API is not stable for
  this use; couples to internals.
- **Option C** — Add a hard dependency on `prometheus_client` and emit
  metrics directly. Pros: works for the dominant downstream consumer
  (juniper-cascor + juniper-canopy already use Prometheus).
  Cons: bloats the client; consumers without Prometheus pay the cost.

**Provisional recommendation**: **Option A**. It's the shape that lets
the cascor/canopy services plumb into their existing Prometheus
infrastructure without forcing the dependency on lighter consumers.
Defer Option C to a separate `juniper-data-client[prometheus]` extra if
demand materializes.

### H4 (single 30 s timeout for health probe)

**Provisional**: split into `request_timeout` and `health_timeout`
(default 5 s for health). Risk: changing default may surface previously
hidden slow backends — exactly the signal we want.

### H5 (sync-only blocking I/O)

**Cross-cutting** — not a metrics issue per se, but it caps the
observability quality of consumers. Document as Architectural finding;
defer the async-port decision to a separate review.

### H6 (POST/PATCH/DELETE silent retry)

**Provisional**: remove POST/PATCH/DELETE from `RETRY_ALLOWED_METHODS`
unless an explicit idempotency-key header is supplied. Severity could be
High depending on whether `batch_*` operations are non-idempotent.

(H7–H11 receive full remediation blocks during the actual review.)

---

## 6. Tooling & commands

```bash
# (Library lives in any Python env — no dedicated conda env)
cd juniper-data-client
pip install -e ".[dev]"

# Full suite
pytest tests/ -v --tb=short --cov=juniper_data_client --cov-report=term-missing

# Targeted observability paths
pytest tests/test_client.py::TestHealthEndpoints tests/test_client.py::TestErrorHandling -v

# Performance baseline (if tests are present)
pytest tests/test_performance.py -v --benchmark-only 2>/dev/null || pytest tests/test_performance.py -v
```

---

## 7. Owner / sign-off

- Plan owner: (assign during distribution)
- Reviewer: (assign during distribution)
- Sign-off blocked on: ecosystem roadmap §6.1 gates + downstream
  juniper-cascor smoke pass.
