# R2.1 — Shared juniper-observability Library

**Status:** PROPOSED (awaiting review before implementation)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-28
**Roadmap item:** [METRICS_MONITORING_ROADMAP_2026-04-25.md §R2.1](METRICS_MONITORING_ROADMAP_2026-04-25.md)
**Seed finding:** seed-06 (duplicated `DependencyStatus`/`ReadinessResponse` across 3 repos; broader observability duplication identified during R1.2/R1.3 implementation)
**Composite severity:** 3 (must-have for next release)
**Affected repos:** **new** juniper-observability (hosted in juniper-ml repo), juniper-data, juniper-cascor, juniper-canopy
**Predecessor cluster:** R1.1 (cardinality), R1.2 (probe semantics), R1.3 (worker heartbeat) — all merged 2026-04-27/28

---

## 1. Problem statement

The R1.1 / R1.2 / R1.3 work proved that drift across the three server repos is real, costly, and continues to accumulate:

- **Three nearly-identical `observability.py` modules.** ~1100 LOC across `juniper-data` (337), `juniper-cascor` (519), `juniper-canopy` (253). The R1.1 cardinality fix had to land in three PRs with hand-applied identical changes; the R1.2 probe contract had to land in four. Each cycle costs PR-review time and risks subtle inconsistency.
- **Drifted signatures already in production.**
  - `configure_sentry(dsn, service_name, version)` (canopy) vs `configure_sentry(dsn, service_name, version, traces_sample_rate=0.1)` (cascor) vs `configure_sentry(dsn, service_name, version, *, send_pii=False, traces_sample_rate=DEFAULT_SENTRY_TRACES_SAMPLE_RATE)` (data — gained `send_pii` for SEC-10).
  - `ReadinessResponse.timestamp` uses `datetime.now(UTC).timestamp()` in juniper-data (BUG-JD-06 fix, timezone-aware) but naive `datetime.now().timestamp()` in juniper-cascor — local-time leakage.
- **Three copies of the same Pydantic models.** `DependencyStatus`/`ReadinessResponse` are character-for-character identical except for timestamp drift. Any change to the contract — say, adding the `X-Juniper-Readiness` header field validation — has to be hand-replayed three times.
- **Three independent test suites for the same logic.** Each repo's `test_observability.py` exercises identical middleware behavior. The R1.1 cardinality stress test was duplicated three times.

After R1.2 and R1.3 closed the contract gaps, the substrate is now stable enough to extract. Doing it now costs three PRs of migration work; deferring it costs three PRs **per future change** to the shared surface.

---

## 2. Goals

- **Single source of truth** for `DependencyStatus`, `ReadinessResponse`, `probe_dependency`, `JuniperJsonFormatter`, `RequestIdMiddleware`, `PrometheusMiddleware`, and the R1.1/R1.2 contract constants (`UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS`).
- **Wire-compatible migration**: existing JSON shapes on `/v1/health/ready`, log lines, Prometheus metric names — all unchanged after migration.
- **No new heavyweight runtime dependency** beyond what every consumer already depends on (Pydantic, Starlette, optional `prometheus_client` / `sentry_sdk`).
- **Per-service metrics stay in each repo.** Only cross-cutting infrastructure moves; training-loop metrics, dataset-gen metrics, websocket metrics remain in their respective `observability.py`.
- **Versioning supports incremental migration.** Each consumer can migrate independently without coordinating cuts.

## 3. Non-goals

- **Replacing service-specific metrics.** R5.x will define SLOs and may consolidate metric naming, but per-service metric definitions stay in their owning repo for now.
- **Replacing FastAPI / Starlette / Pydantic.** The shared lib is additive — it provides reusable building blocks, not a replacement framework.
- **A monolithic juniper-platform package.** R2.1 is scoped to observability. A future R2.x could extract other shared concerns (security middleware, settings loaders) but that's not this design.
- **Covering juniper-cascor-worker.** The worker has a different observability surface (`http_health.py` written in R1.3 deliberately uses no FastAPI/Starlette so the worker stays slim). The shared lib should not pull the worker in until/unless a clear need emerges.
- **Replacing `MetricsAuthMiddleware`** (juniper-data only, SEC-16). Service-specific security middleware stays in its repo.

---

## 4. Package layout

### 4.1 Hosting decision

**Hosted in juniper-ml repo as a sub-package** (recommended), not a new sibling repo.

| Option | Pro | Con |
|---|---|---|
| **A. juniper-ml sub-package** (recommended) | Reuses existing CI / publishing pipeline; juniper-ml is already a meta-package on PyPI; one repo for the whole observability story; aligned with the roadmap's original recommendation | Couples the shared lib's release cadence to juniper-ml; adds Python source code to a meta-package that has none today |
| B. New sibling repo (`juniper-observability`) | Clean separation of concerns; independent versioning | New repo, new CI, new dependabot config, new release process; three more repos for operators to track |
| C. Inside `juniper-ml/util/` | Zero new infra | Not installable from PyPI; importing from a script directory is fragile; defeats the purpose |

The roadmap proposed Option A and the juniper-ml repo is well-suited (already publishes to PyPI as a meta-package via `.github/workflows/publish.yml`). Going with **Option A**.

### 4.2 Package name and import path

| Aspect | Value |
|---|---|
| PyPI name | **`juniper-observability`** |
| Import name | `juniper_observability` |
| Repo path | `juniper-ml/juniper_observability/` |
| Setuptools / pyproject | New `pyproject.toml` next to the package; or extend juniper-ml's existing `pyproject.toml` to include the package and a separate distribution. **See §4.4 build choice.** |

### 4.3 Module structure

```
juniper_observability/
├── __init__.py             # Public API re-exports (see §5.1)
├── _version.py             # __version__ string (single source)
├── constants.py            # UNMATCHED_ENDPOINT_LABEL, READINESS_HEADER,
│                           # LIVENESS_TICK_BUDGET_MS, LIVENESS_STALENESS_SECONDS
├── health/
│   ├── __init__.py
│   ├── models.py           # DependencyStatus, ReadinessResponse (Pydantic)
│   └── probe.py            # probe_dependency(...)
├── logging.py              # JuniperJsonFormatter, configure_logging
├── middleware/
│   ├── __init__.py
│   ├── prometheus.py       # PrometheusMiddleware (with R1.1 cardinality fix)
│   └── request_id.py       # RequestIdMiddleware, request_id_var
├── prometheus.py           # get_prometheus_app, set_build_info
└── sentry.py               # configure_sentry (with reconciled signature, SEC-10)
```

### 4.4 Build / distribution choice

**Two PyPI distributions from one repo** is cleanest:

- `juniper-ml` (existing, meta-package, no Python source today) keeps its existing PyPI identity for the `juniper-ml[all]` install convenience.
- `juniper-observability` (new, this package) is published from the same repo via a separate `pyproject-juniper-observability.toml` (or via PEP 621 multi-package layout if upgraded). Tagged releases trigger separate publish workflows.

If splitting `pyproject.toml` becomes too invasive, fallback to a **monorepo-style separate subdirectory** with its own `pyproject.toml` — `juniper-ml/juniper-observability/{pyproject.toml,juniper_observability/}`. The exact tooling shape is a §10 open question.

### 4.5 Python / runtime dependencies

| Dep | Status | Reason |
|---|---|---|
| `pydantic >= 2.0` | required | health models |
| `starlette` | required | middleware base classes |
| `prometheus_client >= 0.20.0` | optional, `[prometheus]` extra | only needed for `PrometheusMiddleware`, `get_prometheus_app`, `set_build_info` |
| `sentry-sdk[fastapi] >= 2.0.0` | optional, `[sentry]` extra | only needed for `configure_sentry` |
| `fastapi` | NOT a direct dep | consumers bring it; shared lib only touches Starlette primitives |

`pip install juniper-observability` → just models + middleware base.
`pip install juniper-observability[prometheus,sentry]` → full surface.
The `juniper-ml[all]` extra in the existing meta-package will pull this transitively.

---

## 5. Public API surface

### 5.1 `juniper_observability/__init__.py` re-exports

```python
from juniper_observability._version import __version__
from juniper_observability.constants import (
    LIVENESS_STALENESS_SECONDS,
    LIVENESS_TICK_BUDGET_MS,
    READINESS_HEADER,
    UNMATCHED_ENDPOINT_LABEL,
)
from juniper_observability.health.models import DependencyStatus, ReadinessResponse
from juniper_observability.health.probe import probe_dependency
from juniper_observability.logging import JuniperJsonFormatter, configure_logging
from juniper_observability.middleware import PrometheusMiddleware, RequestIdMiddleware, request_id_var
from juniper_observability.prometheus import get_prometheus_app, set_build_info
from juniper_observability.sentry import configure_sentry
```

Consumers get one `from juniper_observability import …` import and the public surface is stable across services.

### 5.2 Reconciled `configure_sentry` signature

```python
def configure_sentry(
    dsn: str | None,
    service_name: str,
    version: str,
    *,
    send_pii: bool = False,
    traces_sample_rate: float = 0.1,
) -> None: ...
```

- Adopts juniper-data's superset signature (`send_pii` keyword-only).
- Always installs the SEC-10 `before_send` hook that scrubs `X-API-Key`, `Authorization`, `Cookie` headers — defense-in-depth regardless of `send_pii`.
- Default `traces_sample_rate=0.1` matches all three repos' current defaults.
- Backwards-compatible for cascor (added `traces_sample_rate=0.1` already) and canopy (added `traces_sample_rate=0.1` post-R1.2). The new `send_pii=False` default matches every existing call site.

### 5.3 Reconciled `ReadinessResponse.timestamp`

```python
class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded", "not_ready"]
    version: str
    service: str
    # Always timezone-aware UTC (BUG-JD-06 — closes the cascor naive-tz drift)
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())
    dependencies: dict[str, DependencyStatus] = Field(default_factory=dict)
    details: dict[str, object] = Field(default_factory=dict)
```

The juniper-cascor migration **fixes** the latent BUG-JD-06-equivalent bug (naive `datetime.now()` → unix-ts via `.timestamp()` is locale-dependent in some Python builds). This is a wire-format change visible to consumers reading `timestamp` as a float; the values remain unix-epoch-seconds and only change by the tz-offset (irrelevant to clients computing diffs).

### 5.4 Per-service customization hooks

`PrometheusMiddleware.__init__` keeps the `service_name` and `namespace` kwargs so each service produces its own metric names (`juniper_data_*`, `juniper_cascor_*`, `juniper_canopy_*`).

`JuniperJsonFormatter(service=...)` keeps the `service` kwarg so log lines surface the right service identity.

`configure_logging(log_level, log_format, service_name=...)` keeps the `service_name` kwarg.

`set_build_info(namespace, version)` keeps both kwargs.

The shared lib defines no service-specific defaults — every consumer passes its own identity. This matches existing behavior; no API change for consumers.

---

## 6. Migration sequence

Per roadmap §R2.1, dependency order:

| Order | Repo | What ships |
|---|---|---|
| 0 | juniper-ml | Publish `juniper-observability==0.1.0a0` (alpha), populate package, no consumer migrations yet |
| 1 | juniper-data | Migrate to `juniper-observability==0.1.0a0`; remove duplicated code; assert wire-compat snapshot |
| 2 | juniper-ml | Bump `juniper-observability` to `0.1.0` (stable) once juniper-data soaks for one release cycle |
| 3 | juniper-cascor | Migrate to `juniper-observability==0.1.0`; remove duplicated code; assert wire-compat snapshot |
| 4 | juniper-canopy | Migrate to `juniper-observability==0.1.0`; remove duplicated code; assert wire-compat snapshot |
| 5 | juniper-ml | Optional `0.2.0` after all three consumers migrate, freeing the lib to break compat for future R2.x work |

**Why data first:** smallest observability surface (337 LOC), simplest dependency graph (no upstream services to probe). If the migration model has a flaw, juniper-data surfaces it cheapest.

**Why cascor before canopy:** cascor is upstream of canopy in the dep graph; if cascor's migration changes the wire shape unexpectedly, canopy notices via integration tests before canopy's own migration lands.

Each migration PR has the same shape:
1. Add `juniper-observability` to `pyproject.toml` deps (with `[prometheus]`, `[sentry]` extras).
2. Replace the relevant imports in the consumer's `observability.py` and health route handlers with `from juniper_observability import …`.
3. Delete the now-duplicated code from the consumer's `observability.py`.
4. Add a wire-compat snapshot test asserting the JSON output of `/v1/health/ready` and the Prometheus scrape format are unchanged.
5. Run the consumer's existing test suite — every test that exercises observability should pass without modification.

---

## 7. Wire-compatibility regression strategy

Each migration PR adds a new test that captures the **pre-migration** wire format and asserts the post-migration behavior matches:

```python
# In each consumer repo's tests/
def test_readiness_wire_compat_against_pre_r2_1_snapshot():
    """METRICS-MON R2.1: the migration to juniper-observability must not change
    the JSON shape of /v1/health/ready as observed by external monitors.
    """
    snapshot = json.loads(SNAPSHOT_PATH.read_text())  # captured from main pre-migration
    response = client.get("/v1/health/ready")
    body = response.json()
    # Assert keys, types, value semantics — but allow timestamp to differ since
    # it's wall-clock-dependent.
    assert set(body.keys()) == set(snapshot.keys())
    for key in ("status", "version", "service"):
        assert body[key] == snapshot[key], f"key {key!r} drifted"
    # Dependencies dict shape unchanged
    assert set(body["dependencies"].keys()) == set(snapshot["dependencies"].keys())
```

Each consumer's PR captures its own snapshot before migrating. The snapshot files live in `tests/fixtures/r2_1_pre_migration_*.json`.

Prometheus scrape compat: each consumer adds a test that scrapes `/metrics` post-migration and asserts the **set of metric names** is unchanged. Label sets may legitimately shrink (R1.1 already fixed cardinality), but no metric should disappear.

---

## 8. Backwards compatibility

| Audience | Impact | Mitigation |
|---|---|---|
| External monitoring of `/v1/health/ready` | None — JSON keys, types, status enum unchanged | Wire-compat snapshot test guards each migration |
| External Prometheus scrape | None — metric names + labels unchanged (timestamps reconciled to UTC; consumers using `timestamp` as opaque float unaffected) | Scrape snapshot test |
| Sentry integrations | `send_pii=False` becomes default everywhere (was already the default in all three consumers); SEC-10 `before_send` hook always installed | No-op for current call sites |
| Log line consumers | None — `JuniperJsonFormatter` produces the same JSON keys (`timestamp`, `level`, `logger`, `message`, `service`, `request_id`, optional `exception`) | Snapshot test |
| Internal Python imports of `observability` symbols | Move from `from <repo>.observability import …` to `from juniper_observability import …` | One-line search-and-replace per consumer; service-specific metrics stay where they are |
| `juniper-cascor`'s timestamp consumers | Naive → tz-aware UTC (~hours-of-offset shift, still epoch seconds) | Documented in juniper-cascor's CHANGELOG migration entry |

---

## 9. Test matrix (covers all five PRs)

| Behavior to assert | juniper-ml (pkg) | juniper-data | juniper-cascor | juniper-canopy |
|---|:---:|:---:|:---:|:---:|
| `DependencyStatus` round-trips through Pydantic v2 | ✓ | — | — | — |
| `ReadinessResponse.timestamp` is tz-aware UTC | ✓ | — | — | — |
| `probe_dependency` happy path / unhealthy / timeout | ✓ | — | — | — |
| `JuniperJsonFormatter` emits documented keys + request_id | ✓ | — | — | — |
| `PrometheusMiddleware` cardinality bound (R1.1) | ✓ | — | — | — |
| `RequestIdMiddleware` propagates header + contextvar | ✓ | — | — | — |
| `configure_sentry` installs `before_send` SEC-10 hook | ✓ | — | — | — |
| `configure_sentry` honors `send_pii` keyword-only flag | ✓ | — | — | — |
| `/v1/health/ready` wire-compat snapshot | — | ✓ | ✓ | ✓ |
| `/metrics` scrape format snapshot (metric names) | — | ✓ | ✓ | ✓ |
| Service-specific metrics still emit correctly | — | ✓ | ✓ | ✓ |
| Existing test suite passes without modification | — | ✓ | ✓ | ✓ |

---

## 10. Open questions before kickoff

1. **Build layout — split `pyproject.toml` or monorepo subdir?** The juniper-ml meta-package's `publish.yml` workflow publishes one distribution today. Option A: extend it to publish two from the same `pyproject.toml` (PEP 621 multi-package, requires hatch / setuptools update). Option B: subdirectory `juniper-ml/juniper-observability/` with its own `pyproject.toml` and a separate publish workflow. **Recommendation: Option B (subdirectory).** It keeps the existing meta-package wholly unchanged and lets the shared lib have its own publish cadence. Option A is reversible later if both ship in lockstep.
2. **Initial version — `0.1.0a0` (alpha) or jump to `0.1.0` stable?** Alpha first allows a rapid-iteration period during the first consumer (juniper-data) migration without committing to stable contract. **Recommendation: alpha first, stable after data migration soaks.**
3. **Should the shared lib expose `MetricsAuthMiddleware` (juniper-data's SEC-16 IP allowlist)?** Currently single-repo. **Recommendation: keep service-specific for now.** R5.x SLO/scrape work may revisit.
4. **Naming: `juniper-observability` vs `juniper-platform-obs` vs `juniper-platform`?** Going with **`juniper-observability`** as the most descriptive and the name implied in the roadmap.
5. **Should the worker (`juniper-cascor-worker`) eventually adopt this lib?** The worker's `http_health.py` deliberately uses no FastAPI/Starlette to keep the image slim. Adopting the shared lib would pull Starlette in. **Recommendation: defer.** R2.x can revisit if the cost of the slim worker becomes painful.
6. **CI integration: should the shared lib's tests run in each consumer's PR?** Probably not — each consumer pins a version, so the shared lib's contract is what matters. **Recommendation: shared lib has its own CI; consumers verify via wire-compat snapshot tests.**

---

## 11. Implementation sequence (PR list)

| # | Repo | Branch | What | Tests |
|---|---|---|---|---|
| 1 | juniper-ml | `metrics-mon-seed-06-shared-obs-init` | Create `juniper-observability` package, populate from juniper-data's modules (most-correct timestamp + Sentry shape), publish `0.1.0a0` to TestPyPI then PyPI | Unit suite for every public symbol; >= 95% coverage |
| 2 | juniper-data | `metrics-mon-seed-06-migrate-data` | Replace duplicated code with `juniper-observability` import; delete duplicated code; add wire-compat snapshot | Existing tests pass + new snapshot test |
| 3 | juniper-ml | `metrics-mon-seed-06-shared-obs-stable` | Promote `0.1.0a0` → `0.1.0` after data soaks | Same unit suite |
| 4 | juniper-cascor | `metrics-mon-seed-06-migrate-cascor` | Same as #2; **also** fixes BUG-JD-06-equivalent naive-tz drift | Existing tests + snapshot |
| 5 | juniper-canopy | `metrics-mon-seed-06-migrate-canopy` | Same as #2 | Existing tests + snapshot |

**Total: 5 PRs.** PRs #2, #4, #5 each delete net Python LOC from their respective repos.

---

## 12. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|:---:|---|
| Shared lib introduces a subtle wire-format change consumers don't catch | Medium | Wire-compat snapshot test in every migration PR |
| Pydantic v2 migration in shared lib breaks consumers still on v1 | Low | All three consumers already on Pydantic v2; lib pins `>= 2.0` |
| `send_pii=False` hardening accidentally breaks operators relying on PII forwarding | Low | All current consumers default to `False`; this is no-op |
| Cascor naive-tz fix changes `timestamp` value by hours-of-offset | Low | Documented in juniper-cascor CHANGELOG; consumers reading `timestamp` for diffs unaffected |
| Publishing two distributions from one repo complicates `publish.yml` | Medium | Option B (subdirectory) keeps the workflows independent |
| Shared lib evolves faster than slowest consumer can adopt | Medium | Stable `0.1.x` line for a quarter; breaking changes go to `0.2.0` only after all three migrate |
| Optional extras (`[prometheus]`, `[sentry]`) confuse operators on minimal installs | Low | Default `juniper-ml[all]` continues to pull both; document explicitly |

---

## 13. Acceptance criteria

R2.1 is **done** when:

- `juniper-observability==0.1.0` is published on PyPI from the juniper-ml repo.
- juniper-data, juniper-cascor, juniper-canopy all import the relevant symbols from `juniper_observability` instead of their local `observability.py`.
- Each consumer's `observability.py` is reduced to **only** service-specific metric definitions (training-loop, dataset-gen, websocket, demo-mode, etc.) — the cross-cutting ~250 LOC per repo is gone.
- Each consumer ships a wire-compat snapshot test for `/v1/health/ready` and a Prometheus scrape snapshot test.
- Cascor's naive-tz `ReadinessResponse.timestamp` defect is closed (documented in cascor CHANGELOG).
- Roadmap §9 R2.1 status flips to **done** with PR links to all 5 PRs.
- A short retrospective note added to `notes/code-review/` summarizing what shipped and any deferred items spawned (e.g., `MetricsAuthMiddleware` if it surfaces as a candidate for R5.x).
