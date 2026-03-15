# Reference

## juniper-ml Technical Reference

**Version:** 0.2.0
**Status:** Active
**Last Updated:** March 3, 2026
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Package Overview](#package-overview)
- [Extras Reference](#extras-reference)
- [Ecosystem Compatibility](#ecosystem-compatibility)
- [Version History](#version-history)
- [Build and Release](#build-and-release)

---

## Package Overview

`juniper-ml` is a meta-package with zero base dependencies and no importable Python modules. It exists solely to provide optional dependency groups for installing Juniper ecosystem packages.

| Field | Value |
|-------|-------|
| **PyPI Name** | `juniper-ml` |
| **Version** | `0.2.0` |
| **Python** | `>=3.12` |
| **Base Dependencies** | None |
| **Importable Modules** | None |

---

## Extras Reference

### Available Extras

| Extra | Packages Installed | Min Version |
|-------|--------------------|-------------|
| `clients` | `juniper-data-client` | `>=0.3.0` |
| | `juniper-cascor-client` | `>=0.1.0` |
| `worker` | `juniper-cascor-worker` | `>=0.1.0` |
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

| juniper-ml | juniper-data | juniper-cascor | juniper-canopy |
|------------|-------------|----------------|----------------|
| 0.2.x | 0.4.x | 0.3.x | 0.2.x |

### Service Ports

| Service | Default Port | Health Endpoint |
|---------|-------------|-----------------|
| juniper-data | 8100 | `/v1/health` |
| juniper-cascor | 8200 | `/v1/health` |
| juniper-canopy | 8050 | `/v1/health` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.0 | 2026-02-27 | Added CLAUDE.md, raised Python to >=3.12, renamed from "juniper" |
| 0.1.0 | 2026-02-22 | Initial release with TestPyPI + PyPI publishing |

---

## Build and Release

### Build

```bash
python -m build
```

### CI/CD Pipeline

The `publish.yml` GitHub Actions workflow runs on release events:

1. **Build** -- Creates wheel and sdist
2. **TestPyPI** -- Uploads and verifies install with `--no-deps`
3. **PyPI** -- Uploads after manual reviewer approval

Both upload steps use trusted publishing (OIDC) with `attestations: false`.

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

**Last Updated:** March 3, 2026
**Version:** 0.2.0
**Maintainer:** Paul Calnon
