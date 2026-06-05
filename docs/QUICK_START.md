# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.3.1
**Status:** Active
**Last Updated:** June 4, 2026
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

# Server packages (juniper-canopy + juniper-cascor + juniper-data)
pip install juniper-ml[servers]

# Shared tooling (juniper-ci-tools + juniper-doc-tools + juniper-observability)
pip install juniper-ml[tools]

# Markdown link validator only (back-compat alias for one entry in [tools])
pip install juniper-ml[doc-tools]

# Everything
pip install juniper-ml[all]
```

> **Note on install size.** `juniper-ml[all]` transitively pulls a multi-GB dependency tree (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`). On a fresh environment this resolves to approximately **5 GB on disk after install** (measured on Python 3.13 + Linux x86_64 against PyPI on 2026-05-21).
> Callers who do not need the worker or server distributions should prefer a narrower extra: `[clients]`, `[tools]`, and `[doc-tools]` each resolve to under 50 MB; `[servers]` is under 200 MB (no torch).

### What Each Extra Installs

| Extra       | Packages                                                                                              |
|-------------|-------------------------------------------------------------------------------------------------------|
| `clients`   | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0`                                          |
| `worker`    | `juniper-cascor-worker>=0.4.0`                                                                        |
| `servers`   | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0`                               |
| `tools`     | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-observability>=0.2.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)              |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools`                                          |

### Shared Observability Package

Since `juniper-ml` 0.5.0, `juniper-observability` is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will install it alongside the rest of the platform. Callers that only want the shared observability primitives without the full meta-package can still install it directly:

```bash
pip install "juniper-observability[all]"
```

See [`../juniper-observability/README.md`](../juniper-observability/README.md) for its public surface and independent release workflow.

### Shared CasCor Candidate Core

`juniper-cascor-core` is configured for independent publication from this repository but is **not** part of any `juniper-ml` extra yet. In a source checkout, install it directly when you need the extracted CasCor candidate-training modules without the full `juniper-cascor` server tree:

```bash
pip install -e juniper-cascor-core
pip install -e "juniper-cascor-core[full]"  # optional dill + columnar debug helpers
```

After a `juniper-cascor-core-v*` release tag publishes the package, use `pip install juniper-cascor-core` from PyPI instead.

The package exposes two surfaces:

- `import juniper_cascor_core` for version checks; this stays lightweight and does not import `torch`.
- The CasCor-compatible top-level packages `candidate_unit`, `utils`, `log_config`, and `cascor_constants`; these are the worker-facing runtime modules and require the package dependencies (`numpy`, `torch`, `PyYAML`).

See [`../juniper-cascor-core/README.md`](../juniper-cascor-core/README.md) for the candidate-worker contract, activation tuple compatibility, logging constraints, and drift-guard expectations.

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`):

```bash
juniper-canopy           0.5.x
juniper-cascor           0.5.x
juniper-cascor-client    0.5.x
juniper-cascor-worker    0.4.x
juniper-ci-tools         0.4.x
juniper-config-tools     0.1.x
juniper-data             0.6.x
juniper-data-client      0.4.x
juniper-doc-tools        0.1.x
juniper-ml               0.6.0
juniper-observability    0.2.x
```

```python
# Verify client imports
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
from juniper_cascor_worker import CandidateTrainingWorker
```

```python
# Version-only check for the candidate-core sibling package.
# Install from source first: pip install -e juniper-cascor-core
import juniper_cascor_core

print(juniper_cascor_core.__version__)
```

```python
# Candidate runtime imports require torch through juniper-cascor-core's base deps.
from candidate_unit.candidate_unit import CandidateUnit
from utils.activation import ActivationWithDerivative

assert "Tanh" in ActivationWithDerivative.ACTIVATION_MAP
```

---

## 3. Next Steps

- [Documentation Overview](DOCUMENTATION_OVERVIEW.md) -- navigation index
- [Reference](REFERENCE.md) -- extras, compatibility, and version reference
- [Host Orchestration Utilities](REFERENCE.md#host-orchestration-utilities) -- run services on-host with `util/juniper_plant_all.bash` and `util/juniper_chop_all.bash`
- [juniper-observability README](../juniper-observability/README.md) -- shared observability primitives
- [juniper-cascor-core README](../juniper-cascor-core/README.md) -- shared CasCor candidate-training core
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** June 4, 2026
**Version:** 0.3.1
**Status:** Active
