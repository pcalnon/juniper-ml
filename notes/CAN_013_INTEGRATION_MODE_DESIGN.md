# CAN-013 — Candidate node integration modes (full design, incl. weighted ensemble)

**Status**: Design • **Date**: 2026-04-29 • **Sprint**: Phase 6E Sprint C (dedicated)

## TL;DR

CAN-013 adds an `integration_mode` parameter to cascor's training config with three modes that control how candidate nodes get installed during cascade growth:

| Mode | Behavior | Status |
|---|---|---|
| `sequential` | Install the single best candidate per cascade iteration. | Today's default — wire-through only. |
| `batch` | Install the top-K candidates as K separate parallel hidden units. | Already implemented via `candidates_per_layer` — wire-through only. |
| `weighted_ensemble` | Install the top-K candidates as **one virtual hidden unit** whose pre-activation is a learned convex combination of the K candidates' pre-activations, with the nonlinearity applied once at the end. | **Greenfield** — this design covers it. |

The first two modes are renames over existing code. The third mode is a new unit-type that requires a hidden-unit dict schema extension, a forward-pass unroll, and a snapshot-format version bump.

This document specifies the weighted-ensemble unit completely — data model, training, inference, serialization, output-retraining contract, and PR breakdown.

## Background — why weighted ensemble for cascade correlation?

Standard cascade correlation installs one candidate per iteration. The motivation is to keep the network minimal and force each new unit to capture residual error the existing structure can't. But the candidate pool already trains K candidates with different random initializations — picking only the best discards K-1 networks' worth of training signal.

Two existing variants mitigate this:

- **Batch mode** (already in cascor as `candidates_per_layer`) installs top-K as separate parallel units in one cascade step. This grows the network faster and uses more candidates, but each unit becomes a permanent first-class participant in subsequent cascade levels — so a mediocre candidate in slot K=3 still influences every later unit's input vector.

- **Weighted ensemble** (this design) installs top-K as **one** unit. The K candidates' pre-activations are linearly combined via a learned weight vector `α ∈ ℝᴷ`, then the nonlinearity is applied once. Subsequent cascade levels see one unit's output, not K. The ensemble unit captures more candidate-pool signal than `sequential` while keeping the cascade depth-progression of `sequential`.

Algebraically, for a virtual ensemble unit at cascade depth d with input vector `xᵢₙ`:

```
zᵢ = Wᵢ · xᵢₙ + bᵢ           (pre-activation of candidate i, i ∈ 1..K)
z = Σᵢ αᵢ · zᵢ                (linear combination)
y = φ(z)                      (single nonlinearity)
```

`α ∈ ℝᴷ` is learnable during the post-installation output-retraining step. `Wᵢ` and `bᵢ` are frozen at install time per the cascade-correlation invariant.

## Code-surface evidence (verified 2026-04-29)

### Hidden unit data model

`juniper-cascor/src/cascade_correlation/cascade_correlation.py:3597–3602` — hidden units are **plain dicts**, not `torch.nn.Module` subclasses:

```python
new_unit = {
    "weights": candidate.weights.clone().detach(),
    "bias": candidate.bias.clone().detach(),
    "activation_fn": self.activation_fn,
    "correlation": candidate.correlation,
}
self.hidden_units.append(new_unit)
```

**Implication**: extending the schema is a dict-key addition, not a class-hierarchy refactor. Backward compat is straightforward — existing units just don't carry the new keys.

### Forward pass

`cascade_correlation.py:1496–1522` — `_compute_hidden_outputs(x)`:

```python
for i, unit in enumerate(self.hidden_units):
    col = self.input_size + i
    unit_input = buffer[:, :col]
    buffer[:, col] = unit["activation_fn"](
        torch.sum(unit_input * unit["weights"], dim=1) + unit["bias"]
    )
```

**Implication**: per-unit forward is one dot product + activation. Adding a `unit_type` switch and unrolling for the ensemble case is local — affects this method only.

### Output retraining

`cascade_correlation.py:1561–1640` — `train_output_layer(x, y, epochs)`:

- Computes hidden outputs once via `_compute_hidden_outputs`
- Passes through `nn.Linear` (output layer)
- Optimizer trains only `output_layer.weight` and `output_layer.bias`

**Implication**: ensemble weights `α` are not currently in scope of any optimizer. We need to register them — but ONLY the `α` vector is trainable, not the candidate weights `Wᵢ`.

### Frozen-weights invariant

Implicit in the code — frozen units' weights are never added to the optimizer scope. Tensors are `.clone().detach()` at install time (line 3598) so they share no autograd tape with the candidate-training graph.

For weighted ensemble: explicitly call `weights.requires_grad_(False)` on each `Wᵢ` and `bᵢ` for safety, and `α.requires_grad_(True)` for the learnable combination weights.

### Snapshot format

`juniper-cascor/src/snapshots/snapshot_serializer.py:420–467` — per-unit HDF5 group:

```
hidden_units/
  unit_0/
    weights         (dataset, shape [input_size + i])
    bias            (dataset, scalar)
    activation_function_name  (attr, str)
    correlation     (attr, float)
  unit_1/
    ...
```

**No format version field today.** Adding ensemble units without versioning would silently break old snapshot loaders. PR adds a `format_version` attribute on the root group and a discriminator `unit_type` per unit.

## Design

### `integration_mode` config field

Add to `juniper-cascor/src/api/models/training.py` `TrainingParams`:

```python
integration_mode: Literal["sequential", "batch", "weighted_ensemble"] = "sequential"
ensemble_size: int = Field(default=3, ge=2, le=16)
```

`ensemble_size` (= K) is only used when `integration_mode == "weighted_ensemble"` (and the upper bound of 16 is to keep snapshot file sizes sane). For `batch`, K is the existing `candidates_per_layer`.

Thread to `OptimizerConfig` / network construction:

```python
network = CascadeCorrelationNetwork(
    config=CascadeCorrelationConfig(
        ...,
        integration_mode=params.integration_mode,
        ensemble_size=params.ensemble_size,
    ),
)
```

### Ensemble unit dict schema

Extends the existing dict (`cascade_correlation.py:3597–3602`):

```python
ensemble_unit = {
    "unit_type": "ensemble",                    # NEW — discriminator
    "candidate_weights": [W_1, W_2, ..., W_K],  # NEW — list of K frozen tensors
    "candidate_biases": [b_1, b_2, ..., b_K],   # NEW — list of K frozen scalars
    "ensemble_alpha": alpha,                    # NEW — torch.nn.Parameter, shape (K,)
    "activation_fn": self.activation_fn,
    "correlation": mean_correlation,            # mean of K candidate correlations
    "candidate_correlations": [c_1, ..., c_K],  # NEW — per-candidate correlations
}
```

Sequential and batch units stay as today — `unit_type: "sequential"` (or absent — defaults to sequential on load for back-compat).

Initialization of `α`: proportional to candidate correlations, normalized:
```
α_i = c_i / Σⱼ c_j     (correlation-weighted)
```
Then training refines α via gradient descent during output-layer retraining.

### Forward pass with ensemble units

In `_compute_hidden_outputs` (`cascade_correlation.py:1496–1522`):

```python
for i, unit in enumerate(self.hidden_units):
    col = self.input_size + i
    unit_input = buffer[:, :col]
    if unit.get("unit_type") == "ensemble":
        # Compute K candidate pre-activations.
        pre_activations = torch.stack([
            torch.sum(unit_input * W_k, dim=1) + b_k
            for W_k, b_k in zip(unit["candidate_weights"], unit["candidate_biases"], strict=True)
        ], dim=1)  # shape (batch, K)
        # Linear combination via α (learnable).
        z = pre_activations @ unit["ensemble_alpha"]  # shape (batch,)
        buffer[:, col] = unit["activation_fn"](z)
    else:
        # Sequential / batch unit — unchanged.
        buffer[:, col] = unit["activation_fn"](
            torch.sum(unit_input * unit["weights"], dim=1) + unit["bias"]
        )
```

### Output retraining sees ensemble α as trainable

Modify `train_output_layer` to register `α` parameters from any ensemble units:

```python
ensemble_alphas = [
    unit["ensemble_alpha"]
    for unit in self.hidden_units
    if unit.get("unit_type") == "ensemble"
]
optimizer = torch.optim.Adam(
    [self.output_layer.weight, self.output_layer.bias, *ensemble_alphas],
    lr=self.config.output_learning_rate,
)
```

The candidate weights `Wᵢ` and biases `bᵢ` stay out of the optimizer — frozen-weights invariant preserved. Only `α` for ensemble units, plus output-layer weights, get gradients.

After retraining, optionally normalize α:
```python
unit["ensemble_alpha"].data /= unit["ensemble_alpha"].data.sum()  # constrain to convex combination
```
Optional — design choice. Default: don't constrain (let α be any real vector). Constrained convex-combination interpretation is more interpretable but loses one degree of freedom.

### Installation path

In `grow_network()` (`cascade_correlation.py:3735+`):

```python
if integration_mode == "sequential":
    selected = [training_results.best_candidate]
    self._add_best_candidate(selected[0], x_train, y_train, growth_iteration)
elif integration_mode == "batch":
    selected = self._select_top_candidates(training_results, k=candidates_per_layer)
    self.add_units_as_layer(selected, x_train)
elif integration_mode == "weighted_ensemble":
    selected = self._select_top_candidates(training_results, k=self.config.ensemble_size)
    self._add_ensemble_unit(selected, x_train)
```

`_add_ensemble_unit` is new — builds the ensemble dict, appends to `self.hidden_units`, resizes the output layer by 1 (not K).

### Snapshot serialization with versioning

`snapshot_serializer.py` — add a root-group `format_version` attribute (set to `"2"` for snapshots containing ensemble units; `"1"` for legacy):

```python
root.attrs["format_version"] = "2"
```

For each unit, add `unit_type` attribute:

```python
unit_group.attrs["unit_type"] = unit.get("unit_type", "sequential")
if unit_group.attrs["unit_type"] == "ensemble":
    save_tensor_list(unit_group, "candidate_weights", unit["candidate_weights"])
    save_tensor_list(unit_group, "candidate_biases", unit["candidate_biases"])
    save_tensor(unit_group, "ensemble_alpha", unit["ensemble_alpha"])
    write_attr_list(unit_group, "candidate_correlations", unit["candidate_correlations"])
else:
    save_tensor(unit_group, "weights", unit["weights"])
    save_tensor(unit_group, "bias", unit["bias"])
```

Loader (`_load_hidden_units`) checks `format_version` and `unit_type`; falls back to legacy fields when absent.

### Canopy UI surface

After cascor PR ships:

- Sidebar dropdown: "Integration mode" → sequential / batch / weighted_ensemble
- When `batch` selected: `candidates_per_layer` integer input becomes visible
- When `weighted_ensemble` selected: `ensemble_size` integer input becomes visible (default 3)
- Network Topology tab: ensemble units rendered with a slightly different visual marker (e.g., outline color, "K=3" label inside the node) so the user can see which units are ensembles
- Network Evolution timeline: ensemble units' delta reads "+1 ensemble unit (K=3)" instead of "+1 unit"

## PR plan (Sprint C)

| # | PR | Repo | Scope | Notes |
|---|---|---|---|---|
| C-1 | `integration_mode` config field + sequential/batch wire-through | cascor | S | Rename of existing `candidates_per_layer` semantics. Tests verify default is sequential. |
| C-2 | Ensemble unit data model + forward pass | cascor | M | New unit dict schema; `_compute_hidden_outputs` switch; α as `torch.nn.Parameter`. Tests on a tiny synthetic dataset verify forward pass produces same output as a single-unit baseline when K=1. |
| C-3 | Ensemble unit installation + output retraining with α | cascor | M | `_add_ensemble_unit`; α registered in optimizer; α gradients flow during output-layer retraining. Test: α.grad is non-zero after one retraining step. |
| C-4 | Snapshot format v2 + ensemble unit serialization | cascor | M | `format_version` on root; `unit_type` per unit; loader back-compat for v1 (no version attr → treat as v1). Round-trip test. |
| C-5 | Canopy UI for integration mode | canopy | S | Sidebar dropdown + conditional inputs. Tests source-level (mode dropdown ID present, conditional logic for batch/ensemble inputs). |

5 PRs total, 1×S + 3×M + 1×S. All independent of Sprints A and B.

## Tests

For each cascor PR, expected coverage areas (estimating ~150–250 lines of tests per PR):

- **Config validation**: `integration_mode` accepts only the three literals; `ensemble_size` rejects values outside [2, 16]; backward compat — params without `integration_mode` default to sequential.
- **Forward pass equivalence**: ensemble unit with K=1 and α=[1.0] produces the same output as a sequential unit on identical inputs.
- **Frozen-weights invariant**: after installing an ensemble unit, the candidate weights have `requires_grad=False`; α has `requires_grad=True`.
- **Output retraining**: α gradient is non-zero after a retraining step; candidate weights' grad stays None.
- **Snapshot round-trip**: save → load reproduces the exact ensemble unit (α, candidate weights, candidate correlations) bit-for-bit.
- **Backward compat**: a v1 snapshot (no `format_version`) loads cleanly into the new code as sequential units.

Plus an integration test that runs a full training session in `weighted_ensemble` mode against a known dataset and verifies the network reaches a target accuracy — guards against subtle issues in the gradient flow through α.

## Risks

1. **α optimization stability**: training α via gradient descent during output retraining could push it to extreme values (one weight near 1, rest near 0 — collapsing the ensemble back to a single candidate). Mitigation: add an optional regularization term (e.g., entropy of softmax(α)) to encourage diversity. Default off; add if smoke tests show collapse.
2. **Snapshot back-compat**: legacy snapshots written before the format_version bump have no `format_version` attribute. Loader must default to `"1"` and treat all units as sequential. Test explicitly.
3. **WS topology message size**: an ensemble unit holds K weight tensors. With ensemble_size=16 and large input dims, the topology broadcast could exceed the chunking threshold — but GAP-WS-18 already handles that. Verify in integration test.
4. **Canopy network visualizer rendering**: the existing visualizer assumes one weight tensor per unit. Ensemble units need either (a) "show all K candidates" mode or (b) "show effective unit" mode (treat as if it's one unit for layout purposes). Default to (b); add (a) as a follow-up.

## Out of scope

- **Constrained convex combination** (α ∈ simplex via softmax): mentioned as a design choice; default is unconstrained α. If this turns out to be necessary for stability, it's a one-line change inside `train_output_layer` post-step.
- **Per-candidate-pair correlation features** (capturing candidate diversity): potentially interesting for selecting which K to install, but orthogonal to integration mode. Future work.
- **Training α directly during candidate training**: the current design only updates α during output retraining. Training α earlier (during candidate training itself) would require restructuring candidate training and is out of scope.

## Decision points for the user

1. **Constrained vs. unconstrained α** — start with unconstrained (more expressive, simpler code) or with softmax-constrained (more interpretable, slightly more code)? My lean: unconstrained, with a regularization escape hatch if smoke tests show collapse.
2. **Ensemble size default** — 3 is the doc's recommendation. Reasonable other defaults: 2 (minimum useful), 5 (matches a typical candidate pool size). My lean: 3.
3. **UI visualization** — render ensemble units as one node (cleanest) or as a "stack of K" node (more informative)? My lean: one node with a "K=3" label inside.
