# juniper-model-core

The shared **model-contract template** for the [Juniper ML](https://github.com/pcalnon/juniper-ml)
research platform: the minimal interface the Juniper service layer needs from *any* learning
model, plus a reusable **conformance test kit** that proves a model is pluggable.

It is the linchpin of the model/middleware refactor — the seam that lets a new neural-network
model drop into the ecosystem (data → training → monitoring → serving) without the service
layer knowing the model type. The contract is derived from **two** real implementers — the
Cascade-Correlation network (a growable classifier) and the Δt-native Legendre Memory Unit (a
fixed-order regressor) — never from one model alone.

## Install

```bash
pip install juniper-model-core                 # the contract (no third-party runtime deps)
pip install "juniper-model-core[conformance]"  # + numpy/pytest, to run the conformance kit
```

`import juniper_model_core` pulls **no** third-party runtime dependency: the contract
references `numpy` only in type annotations. numpy is needed only to *run* the conformance
kit.

## The contract

| Element | What it is |
|---|---|
| `TrainableModel` (ABC) | `fit` / `predict` / `metrics` / `describe_topology` + `task_type`, `input_shape`, `output_shape`. numpy at the boundary; no `argmax`/accuracy in the generic surface. |
| `GrowableModel(TrainableModel)` | adds `n_units` / `grow_step` / `freeze` for constructive models (Cascade-Correlation, RCC, Growing-ESN). Fixed-topology models implement only `TrainableModel`. |
| `TrainingEvent` | the model-agnostic event vocabulary (`training_start`/`end`, `epoch_end`, `unit_added`, `phase_change`) every model maps its native events onto. |
| `ModelSerializer` (ABC) | a `save`/`load` strategy decoupled from the model; round-trips must be lossless. |
| `describe_topology()` | a model-agnostic `{nodes, edges, meta}` graph the front-end renders without knowing the model type. |
| `juniper_model_core.conformance` | the reusable pytest kit any implementer subclasses to prove compliance. |

Shared *behavior* (metric/topology/event validation) lives in `juniper_model_core.validation`
as inspectable free functions — the ABCs themselves are interface-only (first-principles, no
black-box base classes).

## Using the conformance kit

```python
from juniper_model_core.conformance import TrainableModelConformance, tiny_regression_3d

class TestMyModelConformance(TrainableModelConformance):
    def make_model(self):      return MyModel(task_type="regression")
    def make_dataset(self):    return tiny_regression_3d()
    def make_serializer(self): return MySerializer()
```

pytest then runs every contract assertion (interface compliance, `fit→predict→metrics`,
task-type-consistent metrics, renderable topology, lossless serialization, legal event
order, and — for `GrowableModel` — `grow_step` incrementing `n_units`) against your model.

## Design

See `notes/JUNIPER_2026-06-14_JUNIPER-ML_MODEL-CORE-INTERFACE-DESIGN.md` and
`notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` (§2.3, §3.3) in the
juniper-ml repository.

## License

MIT — see [LICENSE](LICENSE).
