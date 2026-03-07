# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.2.0
**Status:** Active
**Last Updated:** March 3, 2026
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
| `clients` | `juniper-data-client>=0.3.0`, `juniper-cascor-client>=0.1.0` |
| `worker` | `juniper-cascor-worker>=0.1.0` |
| `all` | All three packages above |

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`):

```
juniper-cascor-client    0.1.0
juniper-cascor-worker    0.1.0
juniper-data-client      0.3.1
juniper-ml               0.2.0
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
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** March 3, 2026
**Version:** 0.2.0
**Status:** Active
