# `register_or_reuse` — Analysis & Design — 2026-05-05

**Project**: Juniper
**File Name**: `REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`
**Description**: Promote a single canonical idempotent-`prometheus_client`-collector
helper into `juniper-observability` so the recurring "Duplicated timeseries"
bug pattern has one fix point instead of N copy-pasted inline guards.
**Author**: Paul Calnon
**Version**: 0.1.0
**License**: MIT
**Status**: PROPOSAL — entry-plan input for an OBS-COLLECTOR-IDEMPOTENT track

---

## 1. TL;DR

Between 2026-05-02 and 2026-05-04, the same `prometheus_client.REGISTRY`
duplicated-timeseries bug surfaced and was fixed in five different code
paths across four repos (canopy V34a, juniper-data #87, juniper-ml #211 +
#214, juniper-cascor #216, juniper-cascor-client #37, juniper-canopy #240).
Counting the older cascor `_register_or_reuse` and the new sibling helpers,
the same try/except + REGISTRY-lookup pattern is now copy-pasted in
**~10 production sites**.

The fixes work but the duplication is now a maintenance liability: there are
**two subtly different implementations** in the wild (cascor's "drop and
recreate" vs the rest's "adopt existing"), neither obviously dominant. New
collector call sites added in any consumer repo have no canonical reference
to copy.

This document analyzes the bug, compares the two existing implementations,
and proposes a single `juniper_observability.register_or_reuse(...)` helper
plus a phased migration of all current call sites.

---

## 2. Background — the bug pattern

### 2.1 Mechanism

`prometheus_client.Counter` / `Histogram` / `Gauge` / `Info` constructors
register themselves with the global default `REGISTRY` on construction and
raise `ValueError("Duplicated timeseries in CollectorRegistry: {...}")` if
the metric name is already present. The library does not provide a
"register-if-absent" or "get-or-create" primitive — every consumer that
might re-instantiate a collector must implement that themselves.

Three production scenarios trigger the duplicate:

1. **Pytest sessions that re-create the app.** Starlette/FastAPI builds
   the middleware stack lazily on first request, so each `TestClient(app)`
   constructs a fresh `PrometheusMiddleware`. The first test registers,
   the second crashes.
2. **Module-level construction under `importlib.reload`.** Dev autoreload,
   live reloaders, and test harnesses that scrub `sys.modules` re-execute
   module body code. The second run hits a populated `REGISTRY`.
3. **Cached lazy-init that lost its module-global cache.** Patterns like
   `if _foo is None: _foo = Counter(...)` work fine until a test fixture
   sets `_foo = None` to force re-init without unregistering from
   `REGISTRY` first.

Production behaviour is identical: a service started once never trips this.
The bug is exclusively a multi-construction artifact.

### 2.2 Symptom

```
ValueError: Duplicated timeseries in CollectorRegistry:
  {'juniper_data_dataset_generations',
   'juniper_data_dataset_generations_created',
   'juniper_data_dataset_generations_total'}
```

The set notation lists every name `prometheus_client` registers internally
for the collector — for `Counter("foo_total", ...)` that is `foo_total`,
`foo`, `foo_created`. Lookups by any one of those names return the same
collector object.

### 2.3 Failure surface in pytest

Most affected tests are runnable in isolation but fail in the full suite,
because:

- File-local autouse fixtures that snapshot REGISTRY before/after each
  test only see collectors registered *during* their tests; pollution
  from earlier tests (in other files) is invisible.
- Module-level metric construction runs once per process, so the file
  that first imports the module wins; subsequent imports are no-ops, but
  any test that explicitly re-creates the app via `create_app()` re-runs
  the middleware constructors.

This is the same shape as the "stdout buffer + `os._exit`" bug class in
[`project_cascor_pytest_summary_truncation_2026-05-03`](
../../../../.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_cascor_pytest_summary_truncation_2026-05-03.md
) — production-clean code that turns hostile under pytest's session-spanning
process model.

---

## 3. Current-state survey

### 3.1 All known production call sites (post-2026-05-04 sweep)

| Repo | File:line | Metric kind | Status as of 2026-05-05 | Implementation |
|---|---|---|---|---|
| juniper-cascor | `src/api/observability.py:228` (training) | Counter / Gauge / Histogram | guarded | cascor `_register_or_reuse` (drop+recreate) |
| juniper-cascor | `src/api/observability.py:520` (ws) | Counter / Gauge / Histogram | guarded | cascor `_register_or_reuse` (drop+recreate) |
| juniper-cascor | `src/api/websocket/control_stream.py:64` | Counter | guarded (PR #216) | inline adopt-existing |
| juniper-cascor-client | `juniper_cascor_client/observability.py:53` | Counter | guarded (PR #37) | inline adopt-existing |
| juniper-canopy | `src/observability.py:104` (`_ensure_canopy_metrics`) | Counter / Gauge | guarded (V34a) | inline adopt-existing |
| juniper-canopy | `src/main.py:2965` | Histogram + Counter | guarded (PR #240) | inline `_ws_register_or_reuse` (adopt-existing) |
| juniper-canopy | `src/adapter_validation.py:51` | Counter | guarded (PR #240) | inline adopt-existing |
| juniper-canopy | `src/frontend/dashboard_manager.py:3317` | Gauge | guarded (PR #240) | inline adopt-existing |
| juniper-data | `juniper_data/api/observability.py:105` (`_ensure_dataset_metrics`) | Counter / Histogram / Gauge | guarded (PR #87) | inline `_get_or_create` (adopt-existing) |
| juniper-observability | `juniper_observability/middleware/prometheus.py:35` (`PrometheusMiddleware.__init__`) | Counter / Histogram | guarded (PR #211) | inline `_get_or_create` (adopt-existing) |
| juniper-observability | `juniper_observability/prometheus.py:29` (`set_build_info`) | Info | guarded (PR #214) | inline try/except adopt |

**N/A — not registry-bound**:

- `juniper-cascor/src/api/workers/metrics.py:120` — `GaugeMetricFamily` is
  emitted from a custom collector's `collect()` method; it never registers
  globally.
- `juniper-cascor/src/api/observability.py:191`, `app.py:78`, `app.py:100`,
  `juniper-cascor-client/observability.py:102` — `from prometheus_client
  import REGISTRY` only, no collector construction.
- `juniper-ml/.../prometheus.py:24` — `make_asgi_app()`, no construction.
- `juniper-cascor-worker`, `juniper-deploy` — no `prometheus_client` use.

### 3.2 Two implementations in the wild

**A. cascor's "drop and recreate"** —
[`juniper-cascor/src/api/observability.py:174-205`](
../../../juniper-cascor/src/api/observability.py
):

```python
def _register_or_reuse(cls, name: str, *args, **kwargs):
    from prometheus_client import REGISTRY
    try:
        return cls(name, *args, **kwargs)
    except ValueError as exc:
        if "Duplicated timeseries" not in str(exc):
            raise
        for collector, names in list(REGISTRY._collector_to_names.items()):
            if name in names:
                REGISTRY.unregister(collector)
                break
        return cls(name, *args, **kwargs)
```

**B. The 2026-05-* PRs' "adopt existing"** — used in canopy V34a, juniper-data #87,
juniper-ml #211 / #214, juniper-cascor #216, juniper-cascor-client #37,
juniper-canopy #240:

```python
def _get_or_create(factory, name, *args, **kwargs):
    try:
        return factory(name, *args, **kwargs)
    except ValueError:
        existing = REGISTRY._names_to_collectors.get(name)
        if existing is None:
            raise
        return existing
```

### 3.3 Implementation comparison

| Concern | cascor (drop+recreate) | 2026-05 PRs (adopt-existing) |
|---|---|---|
| Returned object identity | Fresh collector per call | Same collector across calls |
| Existing accumulated samples | **Discarded** on duplicate | **Preserved** |
| Latest call's `description` / `labels` / `buckets` | Wins | Silently ignored |
| Lookup cost on duplicate | O(N) scan of `_collector_to_names` | O(1) dict lookup on `_names_to_collectors` |
| Error filter | Matches `"Duplicated timeseries"` substring | Catches all `ValueError` |
| Underlying assumption | "Tests want fresh state; we trust the latest call" | "Production wants samples preserved; subsequent calls have identical args" |
| Failure mode if collector type mismatch | Raises `ValueError` from re-construction | Returns existing of wrong type — `.labels(...)` may behave oddly |

Both implementations are correct for the failing tests they were written
against. Neither is universally correct.

---

## 4. Design

### 4.1 Constraints

C1. **Production-path zero-overhead.** First call must hit the same code
path as `factory(name, ...)` directly — no extra branches, no lookup
work, no log output. Services start once; the helper must not tax the
happy path.

C2. **Test-isolation honesty.** A test fixture that calls the helper
twice with *different* args (e.g. different bucket boundaries) should
produce predictable behaviour — either always-fresh or always-adopt,
documented and testable. The current ambiguity ("cascor recreates, the
others adopt") is itself a footgun.

C3. **Optional-dependency-friendly.** `prometheus_client` is an optional
runtime dep on the `[prometheus]` / `[observability]` extras. The
helper's import shape must allow callers to defer import until the
`prometheus_client` branch is actually taken.

C4. **No new private-API surface.** The helper's correctness should not
hinge on `REGISTRY._names_to_collectors` or `REGISTRY._collector_to_names`
beyond what the existing inline fixes already lean on. Both internals
have been stable in `prometheus_client` for years; using one is fine,
relying on both is unnecessary.

C5. **Migration is opt-in.** Existing inline guards keep working; the
shared helper is additive. A consumer migrates one call site at a time.

### 4.2 Proposed API

```python
# juniper_observability/prometheus_helpers.py  (new module)

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


def register_or_reuse(
    factory: Callable[..., T],
    name: str,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Construct a ``prometheus_client`` collector idempotently.

    On first call with a given ``name``, behaves identically to
    ``factory(name, *args, **kwargs)`` — the collector is registered
    with the default ``REGISTRY`` and returned.

    On a subsequent call with the same ``name`` (typically because a
    test fixture cleared a module-level cache without unregistering, or
    because the host module was re-imported), catches the resulting
    ``ValueError("Duplicated timeseries ...")`` and **adopts** the
    already-registered collector — accumulated samples are preserved
    and the latest call's ``args`` / ``kwargs`` are silently ignored.

    Use ``register_fresh`` (below) instead when the latest call's
    ``args`` are intentionally different from the original (test
    fixtures exercising different bucket boundaries, label sets, etc.).

    Lazy-imports ``prometheus_client`` so callers without the optional
    dependency only pay the import cost on the duplicate path.

    Args:
        factory: A ``prometheus_client`` collector class — ``Counter``,
            ``Gauge``, ``Histogram``, ``Summary``, ``Info``, ``Enum``.
        name: The metric name passed as the first positional arg to
            ``factory``.
        *args, **kwargs: Forwarded to ``factory`` on first call;
            ignored on the adopt path.

    Returns:
        The collector — newly registered on first call, or the existing
        collector from ``REGISTRY`` on the duplicate path.

    Raises:
        ValueError: For any ``ValueError`` from ``factory`` that is not
            a ``Duplicated timeseries`` error (e.g. genuinely invalid
            metric name).
    """


def register_fresh(
    factory: Callable[..., T],
    name: str,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Construct a ``prometheus_client`` collector, unregistering any
    pre-existing collector of the same name first.

    Use this when the latest call's ``args`` are intentionally
    different from a prior registration — test fixtures exercising
    different bucket boundaries, deliberately cleared sample state, etc.
    Discards any samples accumulated by the prior collector.

    Equivalent to cascor's pre-existing ``_register_or_reuse`` shape.
    The name distinguishes the two semantics at the call site so a
    reader doesn't have to remember which one is which.
    """
```

### 4.3 Why two functions, not one with a `mode=` kwarg

A single function with `mode={"adopt", "fresh"}` (or a `force_fresh: bool`
flag) collapses to the same line count at the call site but loses the
"name as documentation" value: the call site's choice of helper *is* the
documentation that a reader needs to understand the semantics. Conditional
branches inside one function also raise the bar for accurate type hints
(generic over factory return). Two narrowly-scoped functions are easier
to argue about.

### 4.4 Where it lives

`juniper_observability/prometheus_helpers.py`. Re-exported from
`juniper_observability.__init__` so `from juniper_observability import
register_or_reuse` works.

The existing `juniper_observability/prometheus.py` stays as the
lower-level wrapper around `make_asgi_app` / `set_build_info`. Putting
both helpers into `prometheus.py` would conflate the two concerns
(`prometheus.py` is "things that wrap or expose `prometheus_client`
machinery"; `prometheus_helpers.py` is "patterns for safely using
`prometheus_client` directly from consumers").

### 4.5 What about the `_total` / `_created` / `_bucket` suffixes?

`prometheus_client` registers a collector under multiple names:

- `Counter("foo_total")` — registered as `foo_total`, `foo`, `foo_created`
- `Histogram("bar_seconds")` — registered as `bar_seconds`, `bar_seconds_bucket`,
  `bar_seconds_sum`, `bar_seconds_count`, `bar_seconds_created`
- `Info("baz")` — registered as `baz`, `baz_info`

All entries point at the **same collector object**. The proposed
`register_or_reuse` looks up via `REGISTRY._names_to_collectors[name]`
where `name` is the value the caller passed; since at least one entry
in `_names_to_collectors` always matches the caller's `name`, the
lookup always succeeds when a duplicate is detected.

Verified empirically in the 2026-05-04 work: `Counter("foo_total")`,
`Gauge("foo")`, `Histogram("foo_seconds")`, and `Info("foo")` all
resolve correctly via the bare `name` lookup.

### 4.6 Edge cases & non-goals

- **Custom registries**: out of scope. The helper targets the default
  `REGISTRY` exclusively. Consumers using their own `CollectorRegistry`
  manage their own lifecycle and don't have the cross-test-pollution
  issue.
- **Type-mismatch on adopt**: if a caller passes `Counter` but the
  registered collector is a `Gauge` of the same name, the helper
  returns the `Gauge` and a subsequent `.labels(...)` may surprise.
  This is a programming error (two collectors of the same name with
  different types is itself the bug), and it manifests as
  `AttributeError` on the next call — loud enough to catch.
- **Concurrency**: `prometheus_client.REGISTRY.register` is
  thread-safe. The proposed helper is not, but neither is the current
  code; both have an inner race window between the `factory(...)` call
  and the `_names_to_collectors.get(name)` lookup. In practice the
  collector construction and the test-fixture clear-and-recreate
  sequence both run on the main thread of a pytest session. Documented
  as a known non-goal.
- **`Histogram` buckets**: on `register_or_reuse` (adopt mode), the
  caller's `buckets=` kwarg is silently ignored. If a test wants to
  exercise different buckets, it must use `register_fresh`. Documented
  in the docstring.

---

## 5. Migration plan

Six existing call sites guarded inline (after the 2026-05-04 sweep)
plus cascor's two `_register_or_reuse` sites — eight total — should be
migrated. The migration is mechanical and verifiable per-site by re-running
the affected repo's test suite.

### 5.1 Phasing

**Phase 0 — Land the helper.** PR in `juniper-ml` adds
`juniper_observability/prometheus_helpers.py` + re-export +
unit tests + a CHANGELOG entry. No migration; existing inline guards
keep working. Tag a juniper-observability release once merged.

**Phase 1 — Migrate juniper-observability's own call sites.**
`PrometheusMiddleware` and `set_build_info` switch to the new helper.
Single PR. Verifies the helper against juniper-observability's own
test suite + the consumer fleet's CI.

**Phase 2 — Per-consumer migration.** One PR per repo, in dependency
order: `juniper-data` → `juniper-canopy` → `juniper-cascor-client` →
`juniper-cascor`. Each PR:

  1. Bumps the `juniper-observability` dep pin to the Phase-0 release.
  2. Replaces the inline `_get_or_create` / `_register_or_reuse` with
     `register_or_reuse` from the shared lib.
  3. Drops the duplicated helper.
  4. Verifies the consumer's full test suite is unchanged.

cascor's existing `_register_or_reuse` shape (drop + recreate) maps to
`register_fresh`; consumers will need to choose per call site whether
they want adopt or fresh semantics. The default for migration is
`register_or_reuse` (adopt) — that is the cheaper path and preserves
samples; switch to `register_fresh` only where the call site actively
relies on the discard-and-recreate behaviour.

**Phase 3 — Memory + close.** Update the four 2026-05-* memories
(`project_cascor_*_2026-05-03.md`, etc.) to reference the helper as
the canonical fix going forward. Update relevant CLAUDE.md files in
juniper-ml and consumer repos with a one-line note.

### 5.2 Sequencing constraints

- `juniper-data` blocks on Phase 0 (needs the helper imported).
- `juniper-canopy` and `juniper-cascor-client` are independent.
- `juniper-cascor` should be migrated last because it has the most
  call sites and an existing competing implementation; consolidating
  the eight-site pattern is the largest churn.

### 5.3 Backward compatibility

Inline guards in consumer repos keep working until each consumer's
Phase-2 PR lands. There is no required version bump; the helper is
purely additive.

---

## 6. Testing strategy

Unit tests in `juniper-observability/tests/test_prometheus_helpers.py`:

1. **First-call happy path**: `register_or_reuse(Counter, "test_a", ...)`
   returns a fresh `Counter`; the collector is registered with REGISTRY.
2. **Second-call adopt**: a second call with the same name returns the
   *same object* (assert by `id`), accumulated samples preserved.
3. **Second-call args ignored**: documented behaviour — second call
   with different `description` / `labels` / `buckets` returns the
   first collector unchanged. Test asserts the existing collector's
   description survives.
4. **`register_fresh` discards**: second call returns a *different*
   object (assert `id(...)` differs); the prior collector is no longer
   in `REGISTRY`. Test asserts the new collector's args take effect.
5. **Non-duplicate `ValueError` propagates**: pass a bad metric name
   (e.g. `"foo bar"` — invalid character) and assert `ValueError` reaches
   the caller without the `"Duplicated timeseries"` substring filter
   masking it.
6. **Each collector type smoke test**: parameterize over `Counter`,
   `Gauge`, `Histogram`, `Summary`, `Info`, `Enum`. All five must
   round-trip through both helpers.
7. **Optional-dependency**: monkeypatch `sys.modules["prometheus_client"]`
   to `None` and assert `register_or_reuse` raises `ImportError`
   cleanly at call time (not at import time).

Integration / consumer tests stay as-is — the helper is an internal
implementation detail; the consumers' existing duplicated-timeseries
regression tests (e.g. juniper-data `TestSEC16MetricsAppIntegration`)
exercise the helper indirectly post-migration.

---

## 7. Open questions

OQ-1. **Should `register_or_reuse` log on the adopt path?** A `DEBUG`
or `INFO` log line on the duplicate branch would surface unexpected
re-registrations during dev, but might also be noisy in normal
test-suite runs (every test that re-creates the app would log once
per metric). Recommendation: no logging in the helper itself;
consumers can wrap if they want it.

OQ-2. **Should we also lift the `juniper_observability.set_build_info`
fix into a generic `register_info_or_update(...)` helper that re-uses
the existing collector and updates its labels?** That's the unique
feature of `Info` — it has both registration and a separate `info(...)`
label-update step. Probably worth a separate small helper. Out of
scope for the v1 design; revisit after Phase 2.

OQ-3. **Promotion target for the canopy `_inbound_invalid_counter`
sentinel pattern?** Three call sites (canopy `adapter_validation.py`,
canopy `dashboard_manager.py`, cascor `control_stream.py`) follow the
same "lazy-init with `None` sentinel that gets re-tested per call"
shape. The proposed helper covers the construction step but not the
sentinel orchestration. Recommendation: a sibling helper
`lazy_register_or_reuse(factory, name, *args, **kwargs)` that caches
the result in a module-private dict keyed by name. v2 territory.

OQ-4. **Should we ship a pytest fixture in `juniper_observability.testing`
that scrubs REGISTRY between tests?** Many consumer test files have a
hand-rolled `_reset_prometheus_registry` autouse fixture. A shared
implementation would prevent the file-scope-only blind spot that
caused the juniper-data SEC-16 regression. Likely yes; out of scope
for the helper itself.

---

## 8. Decision points for sign-off

- [ ] Two helpers (`register_or_reuse` + `register_fresh`) vs one with a
  `mode=` kwarg — see §4.3
- [ ] Module placement — new `prometheus_helpers.py` vs add to existing
  `prometheus.py` — see §4.4
- [ ] Logging policy on the adopt branch — see OQ-1
- [ ] Whether OQ-3 (`lazy_register_or_reuse`) and OQ-4 (testing fixture)
  ship in the same release as v1 or are deferred

Once these are settled, Phase 0 becomes a ~150-line PR (helper +
docstring + unit tests + CHANGELOG + re-export). Phase 1 is another
~50-line PR. Phase 2 is one ~30-line PR per consumer.

---

## 9. References

- canopy V34a — `b33f81f` (2026-05-02): `_ensure_canopy_metrics`
  REGISTRY adoption
- juniper-canopy PR #240 — three sites: `main.py`, `adapter_validation.py`,
  `dashboard_manager.py`
- juniper-data PR #87 — `_ensure_dataset_metrics`
- juniper-ml PR #211 — `PrometheusMiddleware.__init__`
- juniper-ml PR #214 — `set_build_info` Info
- juniper-cascor PR #216 — `control_stream._get_command_counter`
- juniper-cascor-client PR #37 — `_ensure_counter`
- juniper-cascor `src/api/observability.py:174` — pre-existing
  `_register_or_reuse` (drop + recreate)
- Memory:
  [`project_cascor_orphan_forkserver_workers_2026-05-03`](
  ../../../../.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_cascor_orphan_forkserver_workers_2026-05-03.md
  ) — analogous "production-clean code goes hostile under pytest's
  process model" pattern
