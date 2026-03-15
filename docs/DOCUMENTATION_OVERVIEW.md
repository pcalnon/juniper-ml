# Documentation Overview

## Navigation Guide to juniper-ml Documentation

**Version:** 0.2.0
**Status:** Active
**Last Updated:** March 3, 2026
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
| **Quick-reference dev tasks** | [DEVELOPER_CHEATSHEET.md](DEVELOPER_CHEATSHEET.md) | docs/ |
| **Understand the project** | [README.md](../README.md) | Root |
| **See development conventions** | [AGENTS.md](../AGENTS.md) | Root |
| **See version history** | [CHANGELOG.md](../CHANGELOG.md) | Root |

---

## Document Index

### docs/ Directory

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **DOCUMENTATION_OVERVIEW.md** | ~80 | Overview | This file -- navigation index |
| **QUICK_START.md** | ~70 | Tutorial | Install Juniper packages in under a minute |
| **REFERENCE.md** | ~90 | Reference | Complete extras, compatibility, and version reference |
| **DEVELOPER_CHEATSHEET.md** | ~187 | Cheatsheet | Quick-reference card for common development tasks |

### Root Directory

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **README.md** | ~58 | Overview | PyPI landing page and installation examples |
| **AGENTS.md** | ~200 | Guide | Development conventions and worktree setup |
| **CHANGELOG.md** | ~40 | History | Version history and release notes |

### notes/ Directory (Selected Runbooks)

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| **DEVELOPER_CHEATSHEET.md** | ~1200 | Runbook | *(Deprecated)* Master cheatsheet — see `docs/DEVELOPER_CHEATSHEET.md` for per-project version |

---

## Ecosystem Context

`juniper-ml` is a meta-package that provides a single `pip install` entry point for the Juniper ecosystem. It contains no importable Python code -- only optional dependency groups that install the actual client libraries and worker.

### What It Installs

```
juniper-ml[clients] ──installs──> juniper-data-client, juniper-cascor-client
juniper-ml[worker]  ──installs──> juniper-cascor-worker
juniper-ml[all]     ──installs──> all three packages above
```

### Compatibility

| juniper-ml | juniper-data-client | juniper-cascor-client | juniper-cascor-worker |
|------------|--------------------|-----------------------|-----------------------|
| 0.2.x | >=0.3.0 | >=0.1.0 | >=0.1.0 |

---

## Related Documentation

### Installed Packages

- **juniper-data-client** -- [Docs](https://github.com/pcalnon/juniper-data-client) (HTTP client for juniper-data)
- **juniper-cascor-client** -- [Docs](https://github.com/pcalnon/juniper-cascor-client) (HTTP/WS client for juniper-cascor)
- **juniper-cascor-worker** -- [Docs](https://github.com/pcalnon/juniper-cascor-worker) (distributed training worker)

### Upstream Services

- **juniper-data** -- [Dataset Service](https://github.com/pcalnon/juniper-data)
- **juniper-cascor** -- [Training Service](https://github.com/pcalnon/juniper-cascor)

---

**Last Updated:** March 3, 2026
**Version:** 0.2.0
**Maintainer:** Paul Calnon
