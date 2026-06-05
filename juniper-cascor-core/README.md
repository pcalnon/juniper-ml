# juniper-cascor-core

Shared **CasCor candidate-training core** for the Juniper ML platform — the importable
model code a distributed CasCor worker needs to execute a candidate unit, decoupled from
the cascor server / training stack.

## Why this exists

`juniper-cascor-worker` executes candidate-training tasks dispatched by `juniper-cascor`.
To do that it must be able to import `CandidateUnit` and its dependencies — but the worker
container historically had **no** cascor codebase, no candidate-training deps, and several
environment mismatches, so every remote candidate crashed on import
(`ModuleNotFoundError: candidate_unit`). See
[juniper-cascor-worker#97 (CW-05)](https://github.com/pcalnon/juniper-cascor-worker/issues/97).

`juniper-cascor-core` is the canonical fix (CW-05 Approach A): a single package the
worker will depend on after the first trusted release, instead of needing the cascor source
tree on `sys.path`.

## What's inside

Extracted verbatim from `juniper-cascor/src` (zero coupling to the server/training stack —
no FastAPI, no `cascade_correlation`, no `api`):

- `candidate_unit/` — `CandidateUnit` (the trainable candidate node).
- `utils/` — `utils` helpers + `activation` (the full `ActivationWithDerivative.ACTIVATION_MAP` plus worker activation-tuple compatibility).
- `log_config/` — the shared logger (made deployment-agnostic, see below).
- `cascor_constants/` — candidate-relevant constants, including the remote result-collection timeout budget used by dual-path candidate training.

Per the migration plan these ship under the **same top-level package names** cascor uses,
so the canonical imports resolve verbatim.

## Public import surface

`juniper_cascor_core` is intentionally thin: importing it exposes only `__version__` and
does **not** import `torch`. Candidate-training code lives in the top-level modules below
so the worker can keep using the same import paths that cascor uses internally.

| Import path | Purpose | Notes |
|-------------|---------|-------|
| `juniper_cascor_core.__version__` | Package version check | Safe for lightweight install verification with `pip install --no-deps`. |
| `candidate_unit.candidate_unit.CandidateUnit` | Trainable candidate node | Requires `torch`; this is the exact import path the worker exercises. |
| `candidate_unit.candidate_unit.CandidateTrainingResult` | Structured `train_detailed()` result | Includes correlation, best index, normalized tensors, success flag, error message, and optional round ID. |
| `utils.activation.ActivationWithDerivative` | Picklable activation wrapper and registry | `ACTIVATION_MAP` includes lowercase functional names plus title-case `torch.nn` module names such as `Tanh`, `Sigmoid`, and `ReLU`; constructor input may be a callable or the worker's legacy `(activation, derivative)` tuple. |
| `utils.utils` | Dataset/tensor/display helpers | `dill` and `columnar` are imported lazily by debug helpers and live behind the `[full]` extra. |
| `log_config.logger.logger.Logger` | Shared CasCor logger | File logging is best-effort; console logging remains available if the log path is not writable. |
| `cascor_constants.constants` | Candidate-relevant defaults | Constants are copied from cascor and guarded against drift until Wave 2 adoption. Current worker-facing exports include `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_SECONDS_PER_EPOCH`, `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_MIN_TIMEOUT`, and `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_MAX_TIMEOUT`. |

Avoid adding new consumer imports from non-candidate cascor modules here. The extraction
boundary deliberately excludes service/API/training-orchestration code.

## Install

Until the first `juniper-cascor-core-v*` trusted release has completed, install from the
source checkout for local validation and worker experiments:

```bash
cd juniper-cascor-core
python -m pip install -e .
```

After the trusted PyPI release exists, install from the public package index:

```bash
pip install juniper-cascor-core           # core (numpy, torch, PyYAML)
pip install juniper-cascor-core[full]     # + optional dev/debug helpers (dill, columnar)
```

## Usage

```python
from candidate_unit.candidate_unit import CandidateUnit
from utils.activation import ActivationWithDerivative

assert "Tanh" in ActivationWithDerivative.ACTIVATION_MAP   # 33 activations, both casings
```

Minimal candidate construction mirrors the legacy cascor constructor names:

```python
import torch

from candidate_unit.candidate_unit import CandidateUnit

candidate = CandidateUnit(
    CandidateUnit__input_size=2,
    CandidateUnit__output_size=1,
    CandidateUnit__activation_function=torch.tanh,
    CandidateUnit__candidate_index=0,
)

x = torch.randn(4, 2)
residual_error = torch.randn(4, 1)

correlation = candidate.train(x=x, residual_error=residual_error, epochs=1)
result = candidate.train_detailed(x=x, residual_error=residual_error, epochs=1)

assert isinstance(correlation, float)
assert result.success is True
```

`train()` preserves the historical float-returning contract. Use `train_detailed()` when a
worker needs the full `CandidateTrainingResult` payload.

The distributed worker currently resolves activations as `(activation, derivative)` tuples.
`ActivationWithDerivative` normalizes that legacy shape by keeping only the callable in the
first tuple slot, which avoids retaining unpicklable derivative lambdas while preserving
`CandidateUnit.forward()` behavior:

```python
import torch

from candidate_unit.candidate_unit import CandidateUnit

candidate = CandidateUnit(
    CandidateUnit__input_size=2,
    CandidateUnit__output_size=1,
    CandidateUnit__activation_function=(
        torch.tanh,
        lambda x: 1.0 - torch.tanh(x) ** 2,
    ),
)

output = candidate.forward(torch.ones(2))
assert output.shape == (1,)
```

## Remote result collection budget

The current `juniper-cascor` dual-path trainer imports three constants from
`cascor_constants.constants` to bound how long it waits for remote candidate-training
results:

| Constant | Value | Purpose |
|----------|-------|---------|
| `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_SECONDS_PER_EPOCH` | `1.0` | Scales the collection budget with candidate-training epochs. |
| `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_MIN_TIMEOUT` | `120.0` | Floor for a full remote round so healthy workers are not marked late after the short shutdown timeout. |
| `_CASCADE_CORRELATION_NETWORK_REMOTE_COLLECT_MAX_TIMEOUT` | `900.0` | Hard ceiling for failure cases where remote workers disappear mid-round. |

These are an upper-bound wait budget, not a fixed delay: healthy rounds return as soon as
all expected results arrive. Keep these exports in sync with `juniper-cascor/src` until
Wave 2 removes the duplicated source copy.

## Deployment-agnostic logging

The shared logger writes a log file under a source-relative `logs/` directory by default.
In containers where that path is not writable, set `JUNIPER_CASCOR_LOG_DIR` to a writable
directory:

```bash
export JUNIPER_CASCOR_LOG_DIR=/var/log/juniper-cascor
export JUNIPER_CASCOR_LOG_LEVEL=WARNING
```

If the directory is unset or cannot be created, file logging degrades to console-only
rather than raising; a missing log file must never fail a candidate-training task. Log
level is controlled by `JUNIPER_CASCOR_LOG_LEVEL`. The legacy `CASCOR_LOG_LEVEL` variable
is still honored, but the prefixed variable wins when both are set.

## Relationship to juniper-cascor

This package is **extracted from** `juniper-cascor/src` and kept byte-identical to it by a
drift-guard test (the candidate-critical modules), pending `juniper-cascor` itself adopting
the package (CW-05 plan Wave 2). Until then, cascor remains the upstream source of truth for
the candidate-training code.

`log_config/logger/logger.py` intentionally differs from cascor today because it carries
the deployment-agnostic logging fix and should be backported when Wave 2 begins.
`cascor_constants/constants.py` also contains the package-only `JUNIPER_CASCOR_LOG_DIR`
override, but the drift guard normalizes that fragment before comparison so unrelated
constants -- including the remote collection timeout exports above -- still fail on drift.

To verify drift from a checkout that also has sibling repos on disk:

```bash
JUNIPER_ECOSYSTEM_ROOT=/path/to/Juniper \
  python3 -m unittest -v tests/test_cascor_core_drift.py
```

The test skips in isolated checkouts where `juniper-cascor/src` is unavailable.

## Release workflow

`juniper-cascor-core` publishes independently from the `juniper-ml` meta-package:

| Item | Value |
|------|-------|
| Package directory | `juniper-cascor-core/` |
| Tag pattern | `juniper-cascor-core-v*` |
| Workflow | `.github/workflows/publish-cascor-core.yml` |
| TestPyPI verification | Installs `juniper-cascor-core==<version>` with `--no-deps` and imports `juniper_cascor_core.__version__`. |
| Package metadata note | `pyproject.toml` declares `license = { text = "MIT" }` and sets `[tool.setuptools] license-files = []`; re-run build + `twine check` before changing this publishing contract. |

Run the package smoke tests before tagging:

```bash
cd juniper-cascor-core
python -m pytest -q
python -m build --sdist --wheel
twine check dist/*
```

## License

MIT — see [LICENSE](LICENSE).
