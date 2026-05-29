# Reference

## juniper-ml Technical Reference

**Version:** 0.6.0
**Status:** Active
**Last Updated:** May 23, 2026
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Package Overview](#package-overview)
- [Extras Reference](#extras-reference)
- [Ecosystem Compatibility](#ecosystem-compatibility)
- [Sibling Packages](#sibling-packages)
- [Version History](#version-history)
- [Build and Release](#build-and-release)

---

## Package Overview

`juniper-ml` is a meta-package with zero base dependencies and no importable Python modules. It exists solely to provide optional dependency groups for installing Juniper ecosystem packages.

| Field                  | Value        |
|------------------------|--------------|
| **PyPI Name**          | `juniper-ml` |
| **Version**            | `0.6.0`      |
| **Python**             | `>=3.12`     |
| **Base Dependencies**  | None         |
| **Importable Modules** | None         |

---

## Extras Reference

### Available Extras

| Extra       | Packages Installed                                                                       | Min Version       |
|-------------|------------------------------------------------------------------------------------------|-------------------|
| `clients`   | `juniper-data-client`                                                                    | `>=0.4.1`         |
|             | `juniper-cascor-client`                                                                  | `>=0.5.0`         |
| `worker`    | `juniper-cascor-worker`                                                                  | `>=0.4.0`         |
| `servers`   | `juniper-canopy`                                                                         | `>=0.5.0`         |
|             | `juniper-cascor`                                                                         | `>=0.5.0`         |
|             | `juniper-data`                                                                           | `>=0.6.0`         |
| `tools`     | `juniper-ci-tools`                                                                       | `>=0.1.0`         |
|             | `juniper-config-tools`                                                                   | `>=0.1.0,<0.2.0`  |
|             | `juniper-doc-tools`                                                                      | `>=0.1.0,<0.2.0`  |
|             | `juniper-observability`                                                                  | `>=0.2.0`         |
| `doc-tools` | `juniper-doc-tools` (back-compat alias for the doc-tools entry in `tools`)               | `>=0.1.0,<0.2.0`  |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools`                             | --                |

### Installation Commands

```bash
pip install juniper-ml[clients]   # Data + CasCor HTTP/WS clients
pip install juniper-ml[worker]    # Distributed training worker
pip install juniper-ml[servers]   # Canopy + Cascor + Data services
pip install juniper-ml[tools]     # CI tools + doc tools + observability
pip install juniper-ml[doc-tools] # Markdown link validator only (back-compat alias)
pip install juniper-ml[all]       # Everything
```

### Package Descriptions

| Package                   | Purpose                                                                         |
|---------------------------|---------------------------------------------------------------------------------|
| **juniper-canopy**        | Real-time monitoring dashboard (Dash/FastAPI) for training dynamics             |
| **juniper-cascor**        | Cascade-Correlation training service (REST + WebSocket)                         |
| **juniper-data**          | Dataset-generation REST service (FastAPI)                                       |
| **juniper-data-client**   | Synchronous HTTP client for the juniper-data REST API (dataset generation)      |
| **juniper-cascor-client** | Synchronous HTTP + async WebSocket client for the juniper-cascor API (training) |
| **juniper-cascor-worker** | Remote candidate training worker using multiprocessing IPC                      |
| **juniper-ci-tools**      | Dependency-documentation generator (`juniper-generate-dep-docs`) used by every Juniper repo's CI |
| **juniper-doc-tools**     | Markdown link validator (`juniper-check-doc-links`) for intra- and cross-repo docs |
| **juniper-observability** | Shared Prometheus collector helpers, structured-JSON logging, Starlette middleware |

---

## Ecosystem Compatibility

`juniper-ml` 0.6.0 declares the following pins. Every package below ships from PyPI; servers and tools land under their own extras, clients and worker keep their existing groups.

| juniper-ml | juniper-data | juniper-cascor | juniper-canopy | juniper-data-client | juniper-cascor-client | juniper-cascor-worker | juniper-ci-tools | juniper-doc-tools  | juniper-observability |
|------------|--------------|----------------|----------------|---------------------|-----------------------|-----------------------|------------------|--------------------|-----------------------|
| 0.6.x      | >=0.6.0      | >=0.5.0        | >=0.5.0        | >=0.4.1             | >=0.4.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |

### Service Ports

| Service        | Default Port | Health Endpoint |
|----------------|--------------|-----------------|
| juniper-data   | 8100         | `/v1/health`    |
| juniper-cascor | 8200         | `/v1/health`    |
| juniper-canopy | 8050         | `/v1/health`    |

### Rate Limiting Defaults

The three services intentionally ship with **different** `rate_limit_enabled` defaults — `juniper-data` enables rate limiting out of the box; `juniper-cascor` and `juniper-canopy` leave it disabled by default for local-dev ergonomics. The per-minute threshold is uniform across services (60 req/min) so only the enable flag varies.

| Service          | `rate_limit_enabled` default | `rate_limit_requests_per_minute` default | Source                                                                  |
|------------------|------------------------------|------------------------------------------|-------------------------------------------------------------------------|
| `juniper-data`   | **`True`**                   | `60`                                     | `juniper-data/juniper_data/api/settings.py:151-152` (sentinel-defined)  |
| `juniper-cascor` | `False`                      | `60`                                     | `juniper-cascor/src/api/settings.py:208-209` (sentinel-defined)         |
| `juniper-canopy` | `False`                      | `60`                                     | `juniper-canopy/src/settings.py:164-165` (literal-defined)              |

**Production**: enable rate limiting on every service. Each service's pydantic `Settings` class picks the value up from its own prefixed env var via `env_prefix`:

| Service          | Enable env var                       | Per-minute env var                                |
|------------------|--------------------------------------|---------------------------------------------------|
| `juniper-data`   | `JUNIPER_DATA_RATE_LIMIT_ENABLED`    | `JUNIPER_DATA_RATE_LIMIT_REQUESTS_PER_MINUTE`     |
| `juniper-cascor` | `JUNIPER_CASCOR_RATE_LIMIT_ENABLED`  | `JUNIPER_CASCOR_RATE_LIMIT_REQUESTS_PER_MINUTE`   |
| `juniper-canopy` | `JUNIPER_CANOPY_RATE_LIMIT_ENABLED`  | `JUNIPER_CANOPY_RATE_LIMIT_REQUESTS_PER_MINUTE`   |

The split-default is intentional, not an oversight: `juniper-data` is a higher-risk public-shaped surface (dataset generation, paginated reads), so it ships rate-limited by default; the other two run behind a known reverse-proxy / authenticated client surface where the rate-limit value adds operator friction during local development. Closes the documentation gap tracked in the v7 outstanding-development roadmap under CFG-08.

---

## Sibling Packages

### juniper-observability

`juniper-observability` lives under `juniper-observability/` in this repository and publishes independently from the `juniper-ml` meta-package. Since `juniper-ml` 0.5.0 it is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will pull it in alongside the rest of the platform. Services that don't need the full meta-package can still depend on `juniper-observability` directly when they only want the shared health models, request-ID logging/middleware, Prometheus helpers, or Sentry setup.

| Field                 | Value                                                                      |
|-----------------------|----------------------------------------------------------------------------|
| **PyPI Name**         | `juniper-observability`                                                    |
| **Current Version**   | `0.1.1`                                                                    |
| **Python**            | `>=3.12`                                                                   |
| **Importable Module** | `juniper_observability`                                                    |
| **Package Docs**      | [`../juniper-observability/README.md`](../juniper-observability/README.md) |

Available extras:

| Extra        | Additional packages          |
|--------------|------------------------------|
| `prometheus` | `prometheus-client>=0.20.0`  |
| `sentry`     | `sentry-sdk[fastapi]>=2.0.0` |
| `all`        | Both optional groups         |

Publish and CI constraints:

1. `ci-observability.yml` runs package tests on Python 3.12 and 3.13, then builds and validates the distribution.
2. `publish-observability.yml` runs only for `juniper-observability-v*` tags or manual dispatch, builds from the subdirectory, publishes to TestPyPI, verifies installation, then publishes the same artifact to PyPI.
3. The publish workflow uses OIDC trusted publishing, GitHub-hosted `ubuntu-latest` runners, and SHA-pinned actions. If the runner type or pinned artifact actions change, verify compatibility before tagging a release.

---

## Version History

| Version | Date       | Changes                                                                                   |
|---------|------------|-------------------------------------------------------------------------------------------|
| 0.6.0   | 2026-05-23 | Floor-bumped `[clients]` / `[worker]` / `[servers]` extras to today's ecosystem release wave (cascor/canopy 0.5.0, cascor-client/cascor-worker 0.4.0, data-client 0.4.1) |
| 0.5.0   | 2026-05-21 | Added `[servers]` and `[tools]` extras; expanded `[all]` to install every Juniper package |
| 0.4.1   | 2026-04-28 | Added `juniper-observability` sibling package and dedicated CI/publish workflows          |
| 0.4.0   | 2026-04-09 | Added service orchestration utilities, worktree cleanup tooling, and updated package pins |
| 0.2.0   | 2026-02-27 | Added CLAUDE.md, raised Python to >=3.12, renamed from "juniper"                          |
| 0.1.0   | 2026-02-22 | Initial release with TestPyPI + PyPI publishing                                           |

---

## Build and Release

### Build

```bash
python -m build
```

### Meta-Package Publish Pipeline

The `.github/workflows/publish.yml` workflow publishes the `juniper-ml` meta-package. It runs when a GitHub Release is published and also supports manual `workflow_dispatch` reruns against a tag:

```bash
gh workflow run publish.yml --repo pcalnon/juniper-ml --ref <tag>
```

Release flow:

1. **Build and Validate** -- checks out the tag, installs `build` and `twine`, runs `python -m build`, validates with `twine check dist/*`, and uploads the `dist/` artifact.
2. **Publish to TestPyPI** -- downloads the artifact, publishes to TestPyPI with OIDC trusted publishing, and enables PyPI attestations.
3. **Verify TestPyPI Install** -- installs `juniper-ml==${VERSION}` from TestPyPI with PyPI as the extra index for dependencies, then verifies the installed distribution through `importlib.metadata`.
4. **Publish to PyPI** -- runs only after TestPyPI verification and publishes the same artifact with OIDC trusted publishing and attestations enabled.

### Observability Package Publish Pipeline

The `.github/workflows/publish-observability.yml` workflow publishes the sibling `juniper-observability` package from the `juniper-observability/` subdirectory. It is intentionally decoupled from the meta-package release tags:

| Package                 | Tag Pattern                           | Workflow                                      | Build Directory          |
|-------------------------|---------------------------------------|-----------------------------------------------|--------------------------|
| `juniper-ml`            | `v*` GitHub releases                  | `.github/workflows/publish.yml`               | repository root          |
| `juniper-observability` | `juniper-observability-v*` tag pushes | `.github/workflows/publish-observability.yml` | `juniper-observability/` |

Observability release flow:

1. **Build and Validate** -- runs `python -m build --sdist --wheel` in `juniper-observability/`, validates with `twine check dist/*`, and uploads `juniper-observability/dist/`.
2. **Publish to TestPyPI** -- downloads the artifact into `dist/`, publishes with `packages-dir: dist/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body.
3. **Verify TestPyPI Install** -- sparse-checks out `juniper-observability/pyproject.toml`, reads the package version, retries the TestPyPI install up to five times to tolerate index lag, then imports `juniper_observability` and prints `juniper_observability.__version__`.
4. **Publish to PyPI** -- runs only after TestPyPI install verification and publishes the same artifact with `packages-dir: dist/` and `verbose: true`.

Both publish workflows require GitHub Actions environments named `testpypi` and `pypi`, plus matching trusted-publisher entries on TestPyPI and PyPI for the workflow file, environment, owner, repository, and project name. See [`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`](../notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md) for the v0.5.0 runbook covering the expanded extras surface and the TestPyPI extras-resolution verify step; the prior [`RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md`](../notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md) walkthrough remains the canonical source for the trusted-publisher prerequisite and pending-publisher gotchas.

---

## Environment Variables

These variables are used by consumer applications when juniper-ml extras are installed:

| Variable                 | Used By               | Default                 | Description                               |
|--------------------------|-----------------------|-------------------------|-------------------------------------------|
| `JUNIPER_DATA_URL`       | juniper-data-client   | `http://localhost:8100` | juniper-data service URL                  |
| `JUNIPER_DATA_API_KEY`   | juniper-data-client   | *(none)*                | API key for juniper-data authentication   |
| `CASCOR_SERVICE_URL`     | juniper-cascor-client | `http://localhost:8200` | juniper-cascor service URL                |
| `JUNIPER_CASCOR_API_KEY` | juniper-cascor-client | *(none)*                | API key for juniper-cascor authentication |
| `CASCOR_MANAGER_HOST`    | juniper-cascor-worker | `127.0.0.1`             | Worker manager host                       |
| `CASCOR_MANAGER_PORT`    | juniper-cascor-worker | `50000`                 | Worker manager port                       |

> These are not set by juniper-ml itself — they are consumed by the installed sub-packages.

---

**Last Updated:** May 23, 2026
**Version:** 0.6.0
**Maintainer:** Paul Calnon
