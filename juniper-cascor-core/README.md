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

Use the top-level package names exported by this distribution. `juniper_cascor_core`
exists for package metadata such as `__version__`; worker/runtime imports should use
the same paths that `juniper-cascor` uses today.

```python
from candidate_unit.candidate_unit import CandidateUnit
from utils.activation import ActivationWithDerivative

assert "Tanh" in ActivationWithDerivative.ACTIVATION_MAP   # 33 activations, both casings
```

## Worker-Facing Contracts

These are the compatibility points the distributed worker depends on when a candidate
is constructed in one process and executed in another.

### Picklable Activations

`ActivationWithDerivative` serializes activation wrappers by activation name, then
reconstructs the PyTorch callable during unpickle. This supports both lowercase
functional names (`"tanh"`, `"relu"`) and TitleCase `torch.nn` module names
(`"Tanh"`, `"ReLU"`, `"Softmax"`). Unknown activation names raise `ValueError`
during deserialization.

`Softmax` has one extra guard: if the configured module dimension is invalid for
the current tensor rank, the wrapper falls back to the last dimension. This keeps
worker-side 1-D candidate vectors executable even when the reconstructed module was
configured with `dim=1`.

```python
import pickle
import torch

from utils.activation import ActivationWithDerivative

activation = ActivationWithDerivative(torch.nn.Softmax(dim=1))
restored = pickle.loads(pickle.dumps(activation))

scores = restored(torch.tensor([1.0, 2.0, 3.0]))
assert torch.isclose(scores.sum(), torch.tensor(1.0))
```

### Tensor Dataset Round Trips

`save_dataset(x, y, path)` writes a `torch.save` checkpoint containing
`{"x": x, "y": y}`. `load_dataset(path)` inverts that format with
`torch.load(..., map_location="cpu", weights_only=True)` and returns `(x, y)`.
The file is not YAML and should not contain arbitrary Python objects.

```python
import torch

from utils.utils import load_dataset, save_dataset

x = torch.tensor([[0.0, 1.0], [2.0, 3.0]])
y = torch.tensor([[1.0, 0.0], [0.0, 1.0]])

save_dataset(x, y, "candidate_dataset.pt")
loaded_x, loaded_y = load_dataset("candidate_dataset.pt")
assert torch.equal(loaded_x, x)
assert torch.equal(loaded_y, y)
```

### CandidateUnit Serialization

`CandidateUnit` removes transient logger and display lambdas from its pickle state.
On unpickle it restores `Logger`, reapplies the instance log level, and leaves
display helpers to be recreated lazily by training paths. Forward-pass parameters
(`weights`, `bias`, activation wrapper, dimensions, UUID/candidate metadata) remain
part of the serialized state.

```python
import pickle
import torch

from candidate_unit.candidate_unit import CandidateUnit

candidate = CandidateUnit(
    CandidateUnit__activation_function=torch.nn.Tanh(),
    CandidateUnit__input_size=2,
    CandidateUnit__output_size=1,
    CandidateUnit__log_level_name="CRITICAL",
)
candidate.weights = torch.tensor([0.5, -0.25])
candidate.bias = torch.tensor([0.1])

x = torch.tensor([[2.0, 4.0], [1.0, -1.0]])
expected = candidate.forward(x)
restored = pickle.loads(pickle.dumps(candidate))

assert restored.logger is not None
assert torch.allclose(restored.forward(x), expected)
```

## Deployment-agnostic logging

The shared logger writes a log file under a source-relative `logs/` directory by default.
In containers where that path is not writable, set **`JUNIPER_CASCOR_LOG_DIR`** to a
writable directory — or leave it unset and file logging degrades to console-only rather
than raising (a missing log file never fails a candidate-training task). Log level is
controlled by `JUNIPER_CASCOR_LOG_LEVEL` (legacy `CASCOR_LOG_LEVEL` still honored).

Useful worker settings:

```bash
export JUNIPER_CASCOR_LOG_DIR=/var/log/juniper-cascor
export JUNIPER_CASCOR_LOG_LEVEL=WARNING
```

Supported log levels are `TRACE`, `VERBOSE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`,
`CRITICAL`, and `FATAL`. When both `JUNIPER_CASCOR_LOG_LEVEL` and legacy
`CASCOR_LOG_LEVEL` are set, the prefixed variable wins.

## Validation

Run the package's worker-contract tests from the repository root:

```bash
python -m pytest -q juniper-cascor-core/tests
```

The same test path is part of the main CI workflow and the
`publish-cascor-core.yml` release workflow, so activation serialization, dataset
round-tripping, and `CandidateUnit` pickle/forward behavior block regressions before
package publication.

## Relationship to juniper-cascor

This package is **extracted from** `juniper-cascor/src` and kept byte-identical to it by a
drift-guard test (the candidate-critical modules), pending `juniper-cascor` itself adopting
the package (CW-05 plan Wave 2). Until then, cascor remains the upstream source of truth for
the candidate-training code.

## License

MIT — see [LICENSE](LICENSE).
