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
- `cascor_constants/` — candidate-relevant constants.

Per the migration plan these ship under the **same top-level package names** cascor uses,
so the canonical imports resolve verbatim.

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

## Worker serialization contract

`juniper-cascor-worker` receives candidate-training work through multiprocessing /
remote-worker serialization boundaries, so the core package must preserve more than
plain importability:

- `ActivationWithDerivative` serializes by activation name and must round-trip both
  lowercase functional activations and TitleCase `torch.nn` modules such as
  `Softmax`, `Tanh`, and `ReLU`.
- `CandidateUnit` must remain pickleable after removing transient logger / display
  callbacks in `__getstate__`; `__setstate__` recreates the logger so the restored
  object can still run `forward()`.
- `save_dataset()` and `load_dataset()` are a paired `torch.save` /
  `torch.load(weights_only=True)` checkpoint contract for `{"x": x, "y": y}` tensor
  payloads.
- `import juniper_cascor_core` is intentionally version-only and torch-free; import the
  worker-facing modules (`candidate_unit`, `utils`, `log_config`, `cascor_constants`)
  when running candidate code.

Concrete smoke path:

```python
import pickle

import torch

from candidate_unit.candidate_unit import CandidateUnit
from utils.activation import ActivationWithDerivative

activation = pickle.loads(pickle.dumps(ActivationWithDerivative(torch.nn.Tanh())))
candidate = CandidateUnit(
    CandidateUnit__activation_function=torch.nn.Tanh(),
    CandidateUnit__input_size=2,
    CandidateUnit__output_size=1,
    CandidateUnit__display_frequency=0,
    CandidateUnit__status_frequency=0,
    CandidateUnit__log_level_name="CRITICAL",
)

restored = pickle.loads(pickle.dumps(candidate))
assert restored.logger is not None
assert torch.is_tensor(restored.forward(torch.ones((1, 2))))
assert torch.is_tensor(activation(torch.ones(2)))
```

## Development checks

Install the package with test dependencies, then run its pytest suite from the repo root:

```bash
pip install -e "juniper-cascor-core[test]"
python -m pytest -q juniper-cascor-core/tests
```

The root CI workflow also runs these tests in the `juniper-cascor-core Tests` job.
The package publish workflow repeats the same suite before building distributions, then
verifies the TestPyPI artifact with `--no-deps` plus the version-only
`import juniper_cascor_core` check.

## Deployment-agnostic logging

The shared logger writes a log file under a source-relative `logs/` directory by default.
In containers where that path is not writable, set **`JUNIPER_CASCOR_LOG_DIR`** to a
writable directory — or leave it unset and file logging degrades to console-only rather
than raising (a missing log file never fails a candidate-training task). Log level is
controlled by `JUNIPER_CASCOR_LOG_LEVEL` (legacy `CASCOR_LOG_LEVEL` still honored).

## Relationship to juniper-cascor

This package is **extracted from** `juniper-cascor/src` and kept byte-identical to it by a
drift-guard test (the candidate-critical modules), pending `juniper-cascor` itself adopting
the package (CW-05 plan Wave 2). Until then, cascor remains the upstream source of truth for
the candidate-training code.

## License

MIT — see [LICENSE](LICENSE).
