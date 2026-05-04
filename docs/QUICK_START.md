# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.2.1
**Status:** Active
**Last Updated:** May 4, 2026
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Install](#1-install)
- [Verify](#2-verify)
- [Next Steps](#3-next-steps)

---

## Prerequisites

- **Python 3.12+** (`python --version`)

---

## 1. Install

`juniper-ml` is a meta-package with no code of its own. Choose the extra that matches your use case:

```bash
# Client libraries only (juniper-data-client + juniper-cascor-client)
pip install juniper-ml[clients]

# Distributed training worker only (juniper-cascor-worker)
pip install juniper-ml[worker]

# Everything
pip install juniper-ml[all]
```

### What Each Extra Installs

| Extra | Packages |
|-------|----------|
| `clients` | `juniper-data-client>=0.4.0`, `juniper-cascor-client>=0.3.0` |
| `worker` | `juniper-cascor-worker>=0.3.0` |
| `all` | All three packages above |

### Shared Observability Package

`juniper-observability` is a sibling package in this repository, not part of `juniper-ml[all]`. Install it directly when a service needs the shared health models, request-ID middleware/logging, Prometheus helpers, or Sentry setup:

```bash
pip install "juniper-observability[all]"
```

See [`../juniper-observability/README.md`](../juniper-observability/README.md) for its public surface and independent release workflow.

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`):

```
juniper-cascor-client    0.3.x
juniper-cascor-worker    0.3.x
juniper-data-client      0.4.x
juniper-ml               0.4.1
```

```python
# Verify client imports
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
from juniper_cascor_worker import CandidateTrainingWorker
```

---

## 3. Next Steps

- [Documentation Overview](DOCUMENTATION_OVERVIEW.md) -- navigation index
- [Reference](REFERENCE.md) -- extras, compatibility, and version reference
- [juniper-observability README](../juniper-observability/README.md) -- shared observability primitives
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** May 4, 2026
**Version:** 0.2.1
**Status:** Active
