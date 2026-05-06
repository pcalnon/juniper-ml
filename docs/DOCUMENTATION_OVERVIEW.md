# Documentation Overview

## Navigation Guide to juniper-ml Documentation

**Version:** 0.2.2
**Status:** Active
**Last Updated:** May 4, 2026
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Quick Navigation](#quick-navigation)
- [Document Index](#document-index)
- [Ecosystem Context](#ecosystem-context)
- [Related Documentation](#related-documentation)

---

## Quick Navigation

### I Want To

| Goal | Document | Location |
|------|----------|----------|
| **Install Juniper packages** | [QUICK_START.md](QUICK_START.md) | docs/ |
| **See extras and version info** | [REFERENCE.md](REFERENCE.md) | docs/ |
| **Quick-reference dev tasks** | [DEVELOPER_CHEATSHEET_JUNIPER-ML.md](DEVELOPER_CHEATSHEET_JUNIPER-ML.md) | docs/ |
| **Understand the project** | [README.md](../README.md) | Root |
| **Use shared observability primitives** | [juniper-observability README](../juniper-observability/README.md) | juniper-observability/ |
| **See development conventions** | [AGENTS.md](../AGENTS.md) | Root |
| **See version history** | [CHANGELOG.md](../CHANGELOG.md) | Root |

---

## Document Index

### docs/ Directory

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **DOCUMENTATION_OVERVIEW.md** | ~90 | Overview | This file -- navigation index |
| **QUICK_START.md** | ~90 | Tutorial | Install Juniper packages in under a minute |
| **REFERENCE.md** | ~120 | Reference | Complete extras, compatibility, package, and release-workflow reference |
| **DEVELOPER_CHEATSHEET_JUNIPER-ML.md** | ~220 | Cheatsheet | Quick-reference card for common development tasks |

> The deprecated monolithic cheatsheet (`DEVELOPER_CHEATSHEET-ORIGINAL.md`)
> was relocated to `notes/history/` in 2026-04 and consolidated into
> `notes/legacy/` in 2026-05. Use the per-project
> `DEVELOPER_CHEATSHEET.md` files in each repo's `docs/` directory instead.

### Root Directory

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **README.md** | ~58 | Overview | PyPI landing page and installation examples |
| **AGENTS.md** | ~200 | Guide | Development conventions and worktree setup |
| **CHANGELOG.md** | ~40 | History | Version history and release notes |

### juniper-observability/ Subpackage

| File | Type | Purpose |
|------|------|---------|
| **README.md** | Package guide | Public surface, install extras, design link, and independent release workflow |
| **CHANGELOG.md** | Package history | Version history for `juniper-observability` releases |
| **pyproject.toml** | Package metadata | Dependencies, extras, package version, and pytest/ruff configuration |

### notes/ Directory (Selected Runbooks)

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **CANOPY_EXTERNAL_CASCOR_PLAN.md** | ~470 | Integration Plan | Cross-repo plan for connecting juniper-canopy to an externally running juniper-cascor service |
| **DOCUMENTATION_AUDIT_SUMMARY_2026-03-15.md** | ~100 | Summary | Status and outcomes of ecosystem-wide documentation audit/upgrade work |

---

## Ecosystem Context

`juniper-ml` is a meta-package that provides a single `pip install` entry point for the Juniper ecosystem. The root package contains no importable Python code -- only optional dependency groups that install the actual client libraries and worker.

This repository also houses the independent `juniper-observability` subpackage. It is not part of the `juniper-ml[all]` extras; install it directly when a service needs shared health, logging, request-id, Prometheus, or Sentry primitives.

### What It Installs

```
juniper-ml[clients] ──installs──> juniper-data-client, juniper-cascor-client
juniper-ml[worker]  ──installs──> juniper-cascor-worker
juniper-ml[all]     ──installs──> all three packages above
juniper-observability ─direct install only──> shared observability primitives
```

### Compatibility

| juniper-ml | juniper-data-client | juniper-cascor-client | juniper-cascor-worker |
|------------|--------------------|-----------------------|-----------------------|
| 0.4.x | >=0.4.0 | >=0.3.0 | >=0.3.0 |

---

## Related Documentation

### Installed Packages

- **juniper-data-client** -- [Docs](https://github.com/pcalnon/juniper-data-client) (HTTP client for juniper-data)
- **juniper-cascor-client** -- [Docs](https://github.com/pcalnon/juniper-cascor-client) (HTTP/WS client for juniper-cascor)
- **juniper-cascor-worker** -- [Docs](https://github.com/pcalnon/juniper-cascor-worker) (distributed training worker)
- **juniper-observability** -- [Local docs](../juniper-observability/README.md) (shared health, logging, middleware, Prometheus, and Sentry primitives)

### Upstream Services

- **juniper-data** -- [Dataset Service](https://github.com/pcalnon/juniper-data)
- **juniper-cascor** -- [Training Service](https://github.com/pcalnon/juniper-cascor)

---

**Last Updated:** May 4, 2026
**Version:** 0.2.2
**Maintainer:** Paul Calnon
