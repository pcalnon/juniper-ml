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

`juniper-cascor-core` is the canonical fix (CW-05 Approach A): a single PyPI package the
worker depends on, instead of needing the cascor source tree on `sys.path`.

## What's inside

Extracted verbatim from `juniper-cascor/src` (zero coupling to the server/training stack —
no FastAPI, no `cascade_correlation`, no `api`):

- `candidate_unit/` — `CandidateUnit` (the trainable candidate node).
- `utils/` — `utils` helpers + `activation` (the full `ActivationWithDerivative.ACTIVATION_MAP`).
- `log_config/` — the shared logger (made deployment-agnostic, see below).
- `cascor_constants/` — the copied constants tree (`constants_candidates`,
  `constants_model`, `constants_problem`, `constants_api`, `constants_hdf5`,
  logging, activation, and aggregate re-exports).

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
| `utils.activation.ActivationWithDerivative` | Picklable activation wrapper and registry | `ACTIVATION_MAP` includes lowercase functional names plus title-case `torch.nn` module names such as `Tanh`, `Sigmoid`, and `ReLU`. |
| `utils.utils` | Dataset/tensor/display helpers | `dill` and `columnar` are imported lazily by debug helpers and live behind the `[full]` extra. |
| `log_config.logger.logger.Logger` | Shared CasCor logger | File logging is best-effort; console logging remains available if the log path is not writable. |
| `cascor_constants.*` | Candidate-relevant defaults | Constants are copied from cascor and guarded against drift until Wave 2 adoption. |

Avoid adding new consumer imports from non-candidate cascor modules here. The extraction
boundary deliberately excludes service/API/training-orchestration code.

## Install

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

### Candidate training contract

`CandidateUnit` trains against the residual error supplied by `juniper-cascor`; it does not
compute that error itself. For a candidate pool, pass the same residual-error tensor to every
candidate in the same round so candidates optimize against a fixed network error.

- `x` must be a `torch.Tensor` with shape `[batch, input_size]`. `forward()` accepts a
  1-D input and temporarily expands it to `[1, input_size]`.
- `residual_error` must be a `torch.Tensor` with shape `[batch]` for single-output
  training or `[batch, output_size]` for multi-output training.
- The output and residual-error tensors must share the same batch size, must have one or
  two dimensions, and must agree on feature count when `residual_error` is 2-D. Violations
  raise `ValueError` or `TypeError`.
- The objective is absolute Pearson correlation. For multi-output residuals, each output
  column is evaluated and the best absolute correlation is selected.
- `train()` returns the final correlation as `float` and stores the detailed result on
  `last_training_result`. `train_detailed()` returns `CandidateTrainingResult` directly.
- `train_detailed(progress_callback=...)` invokes the callback every 50 epochs and on the
  final epoch with `candidate_id`, `candidate_uuid`, `epoch`, `total_epochs`, and
  `correlation`.

### Worker integration pitfalls

Remote worker dispatch must preserve the constructor types used by cascor:

- `CandidateUnit__random_max_value` and `CandidateUnit__sequence_max_value` are integers.
  Do not coerce them to floats while serializing JSON or queue payloads; the RNG setup uses
  `random.randint(...)` and `range(...)`.
- `CandidateUnit__candidate_index` offsets the random seed (`random_seed + candidate_index`)
  so candidates in a pool get distinct initial weights.
- Random sequence rolling is capped at `10000` discarded values to avoid large memory/time
  spikes; sequences above that cap continue with a warning.
- `CandidateUnit__uuid` is set once. Calling `set_uuid()` after a UUID already exists logs
  a fatal error and exits the process.
- `ActivationWithDerivative` pickles by activation name and restores from
  `ActivationWithDerivative.ACTIVATION_MAP`; unknown activation names raise `ValueError`
  while unpickling.
- `CandidateUnit.__getstate__()` strips the logger and display helpers before
  multiprocessing / HDF5 serialization. They are recreated or lazily initialized after
  unpickling.

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
is still honored, but the prefixed variable wins when both are set. Valid log-level names
are `TRACE`, `VERBOSE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, and `FATAL`.

If `CASCOR_LOG_LEVEL` is set by itself, import-time configuration emits a
`DeprecationWarning`. If both variables are set to different values, the prefixed variable
wins and a `CFG-05` warning is printed to stderr so split configuration is visible.

## Relationship to juniper-cascor

This package is **extracted from** `juniper-cascor/src` and kept byte-identical to it by a
drift-guard test (the candidate-critical modules), pending `juniper-cascor` itself adopting
the package (CW-05 plan Wave 2). Until then, cascor remains the upstream source of truth for
the candidate-training code.

Two files intentionally differ from cascor today because they carry the deployment-agnostic
logging fix and should be backported when Wave 2 begins:

- `log_config/logger/logger.py`
- `cascor_constants/constants.py`

To verify drift from a checkout that also has sibling repos on disk:

```bash
JUNIPER_ECOSYSTEM_ROOT=/path/to/Juniper \
  python3 -m unittest -v tests/test_cascor_core_drift.py
```

The test skips in isolated checkouts where `juniper-cascor/src` is unavailable.

Run the package smoke tests from the subdirectory when changing the worker import surface,
activation registry, or logging behavior:

```bash
cd juniper-cascor-core
python -m pytest -q
```

## Release workflow

`juniper-cascor-core` publishes independently from the `juniper-ml` meta-package:

| Item | Value |
|------|-------|
| Package directory | `juniper-cascor-core/` |
| Tag pattern | `juniper-cascor-core-v*` |
| Workflow | `.github/workflows/publish-cascor-core.yml` |
| TestPyPI verification | Installs `juniper-cascor-core==<version>` with `--no-deps` and imports `juniper_cascor_core.__version__`. |

Run the package smoke tests before tagging:

```bash
cd juniper-cascor-core
python -m pytest -q
python -m build --sdist --wheel
twine check dist/*
```

## License

MIT — see [LICENSE](LICENSE).
