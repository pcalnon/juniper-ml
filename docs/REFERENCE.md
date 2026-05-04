# Reference

## juniper-ml Technical Reference

**Version:** 0.4.1
**Status:** Active
**Last Updated:** May 4, 2026
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

| Field | Value |
|-------|-------|
| **PyPI Name** | `juniper-ml` |
| **Version** | `0.4.1` |
| **Python** | `>=3.12` |
| **Base Dependencies** | None |
| **Importable Modules** | None |

---

## Extras Reference

### Available Extras

| Extra | Packages Installed | Min Version |
|-------|--------------------|-------------|
| `clients` | `juniper-data-client` | `>=0.4.0` |
| | `juniper-cascor-client` | `>=0.3.0` |
| `worker` | `juniper-cascor-worker` | `>=0.3.0` |
| `all` | All packages from `clients` + `worker` | -- |

### Installation Commands

```bash
pip install juniper-ml[clients]   # Data + CasCor HTTP/WS clients
pip install juniper-ml[worker]    # Distributed training worker
pip install juniper-ml[all]       # Everything
```

### Package Descriptions

| Package | Purpose |
|---------|---------|
| **juniper-data-client** | Synchronous HTTP client for the juniper-data REST API (dataset generation) |
| **juniper-cascor-client** | Synchronous HTTP + async WebSocket client for the juniper-cascor API (training) |
| **juniper-cascor-worker** | Remote candidate training worker using multiprocessing IPC |

---

## Ecosystem Compatibility

| juniper-ml | juniper-data | juniper-cascor | juniper-canopy | juniper-observability |
|------------|-------------|----------------|----------------|-----------------------|
| 0.4.x | 0.4.x | 0.3.x | 0.2.x | >=0.1.1 |

### Service Ports

| Service | Default Port | Health Endpoint |
|---------|-------------|-----------------|
| juniper-data | 8100 | `/v1/health` |
| juniper-cascor | 8200 | `/v1/health` |
| juniper-canopy | 8050 | `/v1/health` |

---

## Sibling Packages

### juniper-observability

`juniper-observability` lives under `juniper-observability/` in this repository and publishes independently from the `juniper-ml` meta-package. It is not installed by `juniper-ml[all]`; services should depend on `juniper-observability` directly when they need shared health models, request-ID logging/middleware, Prometheus helpers, or Sentry setup.

| Field | Value |
|-------|-------|
| **PyPI Name** | `juniper-observability` |
| **Current Version** | `0.1.1` |
| **Python** | `>=3.12` |
| **Importable Module** | `juniper_observability` |
| **Package Docs** | [`../juniper-observability/README.md`](../juniper-observability/README.md) |

Available extras:

| Extra | Additional packages |
|-------|---------------------|
| `prometheus` | `prometheus-client>=0.20.0` |
| `sentry` | `sentry-sdk[fastapi]>=2.0.0` |
| `all` | Both optional groups |

Publish and CI constraints:

1. `ci-observability.yml` runs package tests on Python 3.12 and 3.13, then builds and validates the distribution.
2. `publish-observability.yml` runs only for `juniper-observability-v*` tags or manual dispatch, builds from the subdirectory, publishes to TestPyPI, verifies installation, then publishes the same artifact to PyPI.
3. The publish workflow uses OIDC trusted publishing, GitHub-hosted `ubuntu-latest` runners, and SHA-pinned actions. If the runner type or pinned artifact actions change, verify compatibility before tagging a release.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.4.1 | 2026-04-28 | Added `juniper-observability` sibling package and dedicated CI/publish workflows |
| 0.4.0 | 2026-04-09 | Added service orchestration utilities, worktree cleanup tooling, and updated package pins |
| 0.2.0 | 2026-02-27 | Added CLAUDE.md, raised Python to >=3.12, renamed from "juniper" |
| 0.1.0 | 2026-02-22 | Initial release with TestPyPI + PyPI publishing |

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

| Package | Tag Pattern | Workflow | Build Directory |
|---------|-------------|----------|-----------------|
| `juniper-ml` | `v*` GitHub releases | `.github/workflows/publish.yml` | repository root |
| `juniper-observability` | `juniper-observability-v*` tag pushes | `.github/workflows/publish-observability.yml` | `juniper-observability/` |

Observability release flow:

1. **Build and Validate** -- runs `python -m build --sdist --wheel` in `juniper-observability/`, validates with `twine check dist/*`, and uploads `juniper-observability/dist/`.
2. **Publish to TestPyPI** -- downloads the artifact into `dist/`, publishes with `packages-dir: dist/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body.
3. **Verify TestPyPI Install** -- sparse-checks out `juniper-observability/pyproject.toml`, reads the package version, retries the TestPyPI install up to five times to tolerate index lag, then imports `juniper_observability` and prints `juniper_observability.__version__`.
4. **Publish to PyPI** -- runs only after TestPyPI install verification and publishes the same artifact with `packages-dir: dist/` and `verbose: true`.

Both publish workflows require GitHub Actions environments named `testpypi` and `pypi`, plus matching trusted-publisher entries on TestPyPI and PyPI for the workflow file, environment, owner, repository, and project name. See `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md` for the full release runbook and trusted-publisher troubleshooting notes.

---

## Environment Variables

These variables are used by consumer applications when juniper-ml extras are installed:

| Variable | Used By | Default | Description |
|----------|---------|---------|-------------|
| `JUNIPER_DATA_URL` | juniper-data-client | `http://localhost:8100` | juniper-data service URL |
| `JUNIPER_DATA_API_KEY` | juniper-data-client | *(none)* | API key for juniper-data authentication |
| `CASCOR_SERVICE_URL` | juniper-cascor-client | `http://localhost:8200` | juniper-cascor service URL |
| `JUNIPER_CASCOR_API_KEY` | juniper-cascor-client | *(none)* | API key for juniper-cascor authentication |
| `CASCOR_MANAGER_HOST` | juniper-cascor-worker | `127.0.0.1` | Worker manager host |
| `CASCOR_MANAGER_PORT` | juniper-cascor-worker | `50000` | Worker manager port |

> These are not set by juniper-ml itself — they are consumed by the installed sub-packages.

---

**Last Updated:** May 4, 2026
**Version:** 0.4.1
**Maintainer:** Paul Calnon
