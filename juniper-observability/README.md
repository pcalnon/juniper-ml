<!-- markdownlint-disable MD013 MD033 MD041 -->
<!--
  MD013 (line-length): README contains prose paragraphs that intentionally
                       exceed the 512-char ecosystem limit. Disabled file-wide
                       since wrapping mid-sentence harms PyPI rendering.
  MD033 (no-inline-html): The right-aligned logo + spacing rely on HTML.
  MD041 (first-line-heading): The HTML logo is the first line by design.
-->
<div align="right" width="150px" height="150px" align="right" valign="top"> <img src="images/Juniper_Logo_150px.png" alt="Juniper" align="right" valign="top" width="150px" /></div>
<br /> <br /> <br /> <br />

# Juniper: Dynamic Neural Network Research Platform

Juniper is an AI/ML research platform for investigating dynamic neural network architectures and novel learning paradigms.  The project emphasizes ground-up implementations from primary literature, enabling a more transparent exploration of fundamental algorithms.

## Juniper Observability

`juniper-observability` is the **shared observability primitives package** for the Juniper platform. It provides the Pydantic health-response models used by every Juniper server's `/v1/health/ready` endpoint, the structured-JSON logging configuration with `request_id` propagation, the Starlette middlewares (`RequestIdMiddleware` and `PrometheusMiddleware`) applied across the service fleet, the **idempotent `prometheus_client` collector helpers** — `register_or_reuse`, `register_fresh`, `register_info_or_update`, and `lazy_register_or_reuse` — that every Juniper service uses to register `Counter` / `Gauge` / `Histogram` / `Summary` / `Info` / `Enum` collectors, the matching `juniper_observability.testing.reset_prometheus_registry` pytest fixture, and the Sentry initialisation surface with the SEC-10 `before_send` hook always installed. The package is hosted in the `juniper-ml` repository under `juniper-observability/` but published to PyPI on its own tag pattern (`juniper-observability-v*`), independently of the meta-package release cadence.

## Distribution

`juniper-observability` is published on PyPI as **[`juniper-observability`](https://pypi.org/project/juniper-observability/)**.
The package is also referenced through the platform meta-distribution
**[`juniper-ml`](https://pypi.org/project/juniper-ml/)**, though it is **not** aggregated under any `juniper-ml` extra — services that need the shared observability primitives install it directly:

```bash
pip install juniper-observability                          # core only
pip install "juniper-observability[prometheus]"            # + Prometheus middleware/utilities
pip install "juniper-observability[sentry]"                # + Sentry init
pip install "juniper-observability[all]"                   # everything
```

## Ecosystem Compatibility

This shared-primitives package is part of the [Juniper](https://github.com/pcalnon/juniper-ml) ecosystem.
Minimum compatible version for service consumers:

| Consumer | Minimum `juniper-observability` pin | Notes |
|----------|--------------------------------------|-------|
| `juniper-data` | `>=0.2.0` | Migrated to `register_or_reuse` 2026-05-06 |
| `juniper-cascor` | `>=0.2.0` | Migrated to `register_or_reuse` 2026-05-06 |
| `juniper-canopy` | `>=0.2.0` | Migrated to `register_or_reuse` 2026-05-06 |
| `juniper-cascor-client` | `>=0.2.0` (via `[observability]` extra) | Prometheus-counter integration for unrecognised-frame observation |
| `juniper-data-client` | `>=0.2.0` (via `[observability]` extra) | `X-Request-ID` propagation through the `on_request` hook |

For full-stack Docker deployment and integration tests, see [`juniper-deploy`](https://github.com/pcalnon/juniper-deploy).

## Architecture

`juniper-observability` is a shared infrastructure library — it has no service of its own and is consumed at import time by every Juniper service plus the two client libraries that integrate with Prometheus or `X-Request-ID` propagation.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         juniper-observability                        │
│  health models · logging · middleware · register_or_reuse · Sentry   │
└──────────┬────────────┬────────────┬─────────────┬──────────────────┘
           │ import     │ import     │ import      │ import (extra)
           ▼            ▼            ▼             ▼
   ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐
   │ juniper-    │ │ juniper- │ │ juniper- │ │ juniper-{data,cascor}│
   │ data        │ │ cascor   │ │ canopy   │ │ -client              │
   └─────────────┘ └──────────┘ └──────────┘ └──────────────────────┘
```

The `register_or_reuse` family is the default surface through which every Juniper service registers `prometheus_client` collectors. It exists to make repeated registration safe across module-reload and pytest-fixture-reset scenarios that would otherwise raise `Duplicated timeseries in CollectorRegistry`. The matching `juniper_observability.testing.reset_prometheus_registry` fixture is the canonical reset hook for tests that exercise collector state.

## Related Services

| Component | Relationship | Notes |
|-----------|-------------|-------|
| [juniper-data](https://github.com/pcalnon/juniper-data), [juniper-cascor](https://github.com/pcalnon/juniper-cascor), [juniper-canopy](https://github.com/pcalnon/juniper-canopy) | Service consumers — import the middlewares, health models, and `register_or_reuse` helpers | Pin `juniper-observability>=0.2.0` |
| [juniper-data-client](https://github.com/pcalnon/juniper-data-client), [juniper-cascor-client](https://github.com/pcalnon/juniper-cascor-client) | Client-library consumers — pull in via `[observability]` extra | Optional dependency |
| [juniper-doc-tools](../juniper-doc-tools/README.md) | Sibling library published from the same repository on an independent tag pattern (`juniper-doc-tools-v*`) | Cross-link |

## Design Notes

| Document | Purpose |
|----------|---------|
| [`../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`](../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md) | Design rationale for the `register_or_reuse` / `register_fresh` / `register_info_or_update` / `lazy_register_or_reuse` family + migration history |
| [`../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) | Original METRICS-MON R2.1 cross-service design (archived 2026-05-05) |

## Quick Start Guide

### Prerequisites

- Python ≥ 3.12
- A service or library that needs cross-cutting observability primitives

### Installation

```bash
pip install "juniper-observability[all]"
```

### Verification

Confirm the package is importable and that the `register_or_reuse` helper resolves the duplicate-registration case:

```python
from prometheus_client import CollectorRegistry, Counter
from juniper_observability import register_or_reuse

registry = CollectorRegistry()
c1 = register_or_reuse(Counter, "demo_total", "demo counter", registry=registry)
c2 = register_or_reuse(Counter, "demo_total", "demo counter", registry=registry)
assert c1 is c2, "register_or_reuse must return the existing collector on duplicate registration"
```

For tests that exercise collector state, use the canonical reset fixture:

```python
from juniper_observability.testing import reset_prometheus_registry  # pytest fixture
```

### Next Steps

- [`../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`](../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md) — design rationale and migration history for the `register_or_reuse` family
- [`../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) — original METRICS-MON R2.1 cross-service design (archived to `notes/legacy/` 2026-05-05 after the program closed)
- [`juniper-ml`](https://pypi.org/project/juniper-ml/) — platform meta-package on PyPI

## Research Philosophy

The Juniper platform exists to study learning algorithms whose network architecture is not fixed in advance. Its initial anchor is the Cascade-Correlation algorithm of Fahlman and Lebiere (1990), implemented from the primary literature without recourse to higher-level abstractions that elide the algorithm's operational detail. The organising commitment is that algorithm implementations remain inspectable at the level at which they were originally specified: candidate units, correlation objectives, weight-freezing semantics, and the structural events that grow the network are first-class artifacts of the codebase rather than internal details of a library wrapper. This permits comparative work — across algorithms, datasets, and hyperparameter regimes — to be conducted on a known and reproducible substrate.

The current platform comprises a Cascade-Correlation training service exposing a REST and WebSocket interface, a dataset-generation service with a named-version registry that includes the ARC-AGI families, a real-time monitoring dashboard for inspecting training dynamics as they occur, and a distributed worker that parallelises candidate-unit training across hosts. Near-term work extends the architectural-growth catalogue beyond Cascade-Correlation, introduces multi-network orchestration for comparative experiments at the level of network populations rather than individual runs, and tightens the dataset–training–monitoring loop into a reproducible research workbench. The longer-term direction is the systematic empirical study of constructive and architecture-growing learning algorithms, with first-class infrastructure for the ablation, comparison, and replication that such a study requires.

## Documentation

| Document | Purpose |
|----------|---------|
| [`../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`](../notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md) | Design rationale and migration history for the `register_or_reuse` family of collector helpers |
| [`../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](../notes/legacy/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md) | Original METRICS-MON R2.1 cross-service design (archived 2026-05-05) |
| [`../README.md`](../README.md) | Parent `juniper-ml` meta-package README |
| [`../docs/REFERENCE.md`](../docs/REFERENCE.md) | Parent `juniper-ml` reference (extras, compatibility matrix, environment variables) |

### Per-service metrics stay in each repo

This package intentionally exposes only **cross-cutting** observability infrastructure. Service-specific metric definitions (training-loop counters, dataset-gen histograms, websocket gauges, etc.) live in their owning repo and register via `register_or_reuse` against `prometheus_client.REGISTRY` directly.

### Release Workflow

`juniper-observability` is versioned and published independently of the root `juniper-ml` meta-package.

| Package | Tag pattern | Workflow | Build root |
|---------|-------------|----------|------------|
| `juniper-ml` | `v*` GitHub releases | `.github/workflows/publish.yml` | repository root |
| `juniper-observability` | `juniper-observability-v*` tag pushes | `.github/workflows/publish-observability.yml` | `juniper-observability/` |
| `juniper-doc-tools` | `juniper-doc-tools-v*` tag pushes | `.github/workflows/publish-doc-tools.yml` | `juniper-doc-tools/` |

The observability workflow builds an sdist and wheel from this subdirectory, publishes first to TestPyPI through OIDC trusted publishing, retries installation from TestPyPI to tolerate index lag, imports `juniper_observability` as the smoke test, then promotes the same artifact to PyPI after the `pypi` environment gate.

Operational constraints:

- Trusted publishers must be configured on both TestPyPI and PyPI for project `juniper-observability`, workflow `.github/workflows/publish-observability.yml`, and environments `testpypi` / `pypi`.
- The publish steps set `verbose: true` on `pypa/gh-action-pypi-publish` so upload failures include the package-index response body.
- Keep `pyproject.toml` and `juniper_observability/_version.py` in sync before tagging; the workflow's import smoke test prints `__version__`, but it does not compare it to the built artifact version.

## License

MIT — see [`../LICENSE`](../LICENSE).
