# Phase 6E Design — CasCor algorithm enhancements + bundled CAN-* items

**Status**: Design • **Date**: 2026-04-29 • **Author**: design pass after Phase 6D close

## TL;DR

Phase 6E was scoped at **14×M-XL** in the §25.2 roadmap row: 8 original CasCor algorithm items (CAS-002, CAS-003, CAS-005, CAS-006, CAS-008, CAS-009, ENH-006, ENH-007) plus 6 cross-repo CAN-* items deferred from 6D (CAN-010, CAN-011, CAN-013, CAN-014, CAN-015, CAN-021).

A scoping pass against juniper-cascor `main` reframes that.

**3 of the 6 "blocked" CAN-* items are not algorithm-blocked — the cascor infrastructure already exists, only the API + UI surfaces are missing.**

| Item | Was classified as | Actually is |
|---|---|---|
| CAN-010 (optimizer surface) | Blocked on cascor algorithm | **Wire-through** — `_create_optimizer` already supports 13 PyTorch optimizers via `OptimizerConfig` |
| CAN-011 (activation surface) | Blocked on cascor algorithm | **Wire-through** — `_init_activation_function` reads `config.activation_function_name` from a registry |
| CAN-014 (snapshot tuning capture) | Blocked on snapshot lifecycle | **Largely shipped** — `serializer.save_network(..., include_training_state=True)` already serializes config alongside weights |
| CAN-013 (integration mode) | Blocked on cascor algorithm | **Partially wired** — `candidates_per_layer > 1` already routes through `add_units_as_layer`; only the multi-mode strategy pattern is greenfield |
| CAN-015 (snapshot replay) | Blocked-on-CAN-014 | Medium — needs new "restore + retrain" lifecycle path |
| CAN-021 (parallel-network ensemble) | Deferred to 6E | **Genuinely XL** — single-`self.network` assumption baked into lifecycle |

This isn't the recurring "shipped-but-not-marked" pattern from Tracks 5/6 audits — the CAN-* items genuinely had no UI. But the *cascor groundwork* the items were waiting for is mostly already there. Wiring it through is small-medium PRs, not the cross-repo algorithm sprint Phase 6E was originally scoped as.

## Code-surface evidence (verified 2026-04-29)

### Optimizer factory (CAN-010 / ENH-006)

`juniper-cascor/src/cascade_correlation/cascade_correlation.py:2580` — `_create_optimizer(parameters, optimizer_config=None)` takes an `OptimizerConfig` (defined in `cascade_correlation_config/cascade_correlation_config.py:94–127`) and dispatches via a name→factory dict. Active optimizers in the registry: Adadelta, Adafactor, Adagrad, **Adam, AdamW**, SparseAdam, Adamax, ASGD, LBFGS, NAdam, RAdam, Rprop, RMSprop, SGD, Muon (13 variants live; lines 2624–2700+).

The wire-through gap: `TrainingParams` (`src/api/models/training.py:32–60`) has `learning_rate` and `candidate_learning_rate` as separate floats, but no `optimizer_type` field. Adding it + threading through to `OptimizerConfig.optimizer_type` is the entire CAN-010 / ENH-006 server-side scope.

### Activation function (CAN-011)

`juniper-cascor/src/cascade_correlation/cascade_correlation.py:705` — `_init_activation_function()` reads `self.config.activation_function_name` and looks it up in `self.config.activation_functions_dict`. Default activation set via constants. **Already pluggable**, just no API surface.

CAN-011 server side: add `activation_function_name: Literal[…]` to `TrainingParams`, map at network construction.

### Snapshot training-state capture (CAN-014)

`juniper-cascor/src/api/lifecycle/manager.py:1024` — `serializer.save_network(self.network, filepath, include_training_state=True)` already passes the flag. The HDF5 serializer captures network config + weights + training history. CAN-014's "snapshot captures tuning values" is **already true** — verification step is to confirm the round-trip preserves every `TrainingParams` field. If gaps exist, they're on the load side, not the save side.

### Grow-network with batched candidates (ENH-007 / CAN-013 partial)

`juniper-cascor/src/cascade_correlation/cascade_correlation.py:3735` — `candidates_per_layer = getattr(self, "candidates_per_layer", 1)`. If > 1, dispatches to `add_units_as_layer()` (line 3560) which adds N hidden units in one cascade step. **Already implemented**, no UI surface.

CAN-013's "integration mode" semantics need more design:
- Mode `"sequential"` = today's default (1 best candidate per iteration)
- Mode `"batch"` = today's `candidates_per_layer > 1` path (N best per iteration)
- Mode `"weighted_ensemble"` = greenfield (linear combination of top-K)
- Mode `"parallel_ensemble"` = overlaps with CAN-021 / CAS-009

If CAN-013 ships with just `sequential` + `batch` (= rename `candidates_per_layer` to `integration_mode` enum), it's a small wire-through. If it ships with weighted/parallel modes, it's medium-large.

### Single-network assumption (CAS-009 / CAN-021)

`juniper-cascor/src/api/lifecycle/manager.py:37` — `self.network: Optional[CascadeCorrelationNetwork] = None`. Single instance throughout. CAN-021 / CAS-009 require either:

1. **Multi-network lifecycle**: `self.networks: List[CascadeCorrelationNetwork]` with per-network state, training threads, snapshot scopes. Touches every method on `LifecycleManager`. **XL.**
2. **Network registry pattern**: a `NetworkRegistry` keyed by UUID; `LifecycleManager` operates on whichever is "active". XL but cleaner separation.

This is the only genuinely XL item in Phase 6E.

### Auto-snapshot on best accuracy (CAS-006)

`juniper-cascor/src/api/lifecycle/manager.py:1663` — `create_snapshot()` is called unconditionally after output-layer training. **Greenfield** for the "only-on-improvement" gate. Add a `_best_accuracy` field + comparison check + setting `auto_snapshot_best: bool = True` to `TrainingParams`.

## PR plan

**Updated 2026-04-29** after user direction:

1. CAS-005 held for Sprint D (was Sprint C in the original plan).
2. CAN-013 expanded to full weighted_ensemble and given its own sprint (Sprint C). Detailed design in [`CAN_013_INTEGRATION_MODE_DESIGN.md`](CAN_013_INTEGRATION_MODE_DESIGN.md).
3. Multi-network architecture (CAS-008 / CAS-009 / CAN-021) lifted out into its own design doc + sprint (Sprint E). See [`PHASE_6E_MULTI_NETWORK_DESIGN.md`](PHASE_6E_MULTI_NETWORK_DESIGN.md).

Grouping by surface affinity (= what touches the same files / mental model), not strictly by ID order. Each row is one PR.

| # | PR | Scope | Cascor changes | Canopy changes | Notes |
|---|---|---|---|---|---|
| **Sprint A — small wire-throughs (5 PRs)** | | | | | |
| A-1 | **Training params epoch separation** (CAS-002 + CAS-003) | S | Verify three epoch fields are surfaced through `TrainingParams`; add `network_max_epochs` if not already aliased | Add 3 inputs in sidebar | Pure parameter additions; existing infra in cascor |
| A-2 | **Optimizer surface** (CAN-010 + ENH-006) | S–M | `optimizer_type: Literal[…]` added to `TrainingParams`; thread to `OptimizerConfig` | Dropdown in sidebar; surface in Parameters tab | Cascor side ~30 LoC; canopy ~50 LoC |
| A-3 | **Activation surface** (CAN-011) | S | `activation_function_name: Literal[…]` added to `TrainingParams`; thread to network constructor | Dropdown in sidebar | Smaller than A-2; ~20 LoC each side |
| A-4 | **Auto-snap best** (CAS-006) | S | `_best_accuracy` tracking + `auto_snapshot_best` gate around `create_snapshot()` | Toggle in sidebar (or sticky default) | Pure cascor; canopy gets one boolean toggle |
| A-5 | **Snapshot tuning round-trip** (CAN-014) | S | Verification + tests; if any field is dropped on load, fix it | Surface "Loaded from snapshot N" indicator after restore | Mostly tests; small-but-hardening |
| **Sprint B — snapshot replay loop (1 PR)** | | | | | |
| B-1 | **Snapshot replay → fresh training** (CAN-015) | M | New lifecycle path `restore_for_retrain(snapshot_id)`: load weights → reset training counters → ready for new `start_training()` | Snapshots panel: "Replay" action button | Builds on A-5 |
| **Sprint C — CAN-013 full (5 PRs, see `CAN_013_INTEGRATION_MODE_DESIGN.md`)** | | | | | |
| C-1 | `integration_mode` config + sequential/batch wire-through | S | Add `integration_mode: Literal[…]` and `ensemble_size`; rename `candidates_per_layer` semantics | None | Tests verify default is sequential |
| C-2 | Ensemble unit data model + forward pass | M | New unit dict schema; `_compute_hidden_outputs` switch; `α` as `torch.nn.Parameter` | None | Tests on tiny synthetic dataset; K=1 equivalence to sequential |
| C-3 | Ensemble installation + output retraining with α | M | `_add_ensemble_unit`; α registered in optimizer; α gradients flow during output retraining | None | Frozen-weights invariant explicitly enforced |
| C-4 | Snapshot format v2 + ensemble unit serialization | M | `format_version` on root; `unit_type` per unit; loader back-compat for v1 | None | Round-trip test |
| C-5 | Canopy UI for integration mode | S | None | Sidebar dropdown + conditional inputs; ensemble-unit visualization | Visual marker on Network Topology; "+1 ensemble unit (K=3)" delta on Network Evolution |
| **Sprint D — independent cleanup (1 PR)** | | | | | |
| D-1 | **CAS-005: shared-code extraction** | M–L | Move duplicated cascor↔worker code into a `juniper-core` package | None | Held for Sprint D per user direction; mechanically independent of other sprints |
| **Sprint E — multi-network XL (7 PRs, see `PHASE_6E_MULTI_NETWORK_DESIGN.md`)** | | | | | |
| E-1 | `SingleNetworkLifecycleState` extraction + manager registry | cascor / **L** | Refactors 74 singular sites into per-network methods; back-compat `network` shim | — | The big one; ~600–800 LoC |
| E-2 | New `/v1/networks/*` REST routes + back-compat aliases | cascor / M | Adds URL surface; old routes alias to active network | — | |
| E-3 | Control WS: `network_id` in commands; broadcast: `network_id` in messages | cascor / M | Protocol change; clients without `network_id` keep working | — | |
| E-4 | Snapshot storage layout migration | cascor / S–M | Per-network subdirectories; one-time auto-migration | — | Idempotent |
| E-5 | Per-network training thread + max-concurrent config | cascor / S | Each `SingleNetworkLifecycleState` owns its `ThreadPoolExecutor(1)` | — | |
| E-6 | Canopy adapter: `network_id` parameter threading | — | — | canopy / M | Adapter methods grow `network_id`; falls back to a per-instance default |
| E-7 | Canopy UI: Networks sidebar + Population tab (CAN-021) | — | — | canopy / M–L | Reuses Network Evolution's small-multiples renderer |

19 PRs total across 5 sprints. Sprints A + B + C unblock the bulk of the CAN-* surface (3 wire-through + snapshot replay + full integration modes). Sprint D is independent cleanup. Sprint E is the genuinely XL multi-network refactor.

## Recommended order

```
Sprint A (small wins, ~1 week):           A-1, A-2, A-3, A-4, A-5
Sprint B (medium, ~few days):             B-1
Sprint C (CAN-013 full, ~1.5 weeks):      C-1, C-2, C-3, C-4, C-5
Sprint D (cleanup, independent):          D-1
Sprint E (XL, ~2+ weeks, separate):       E-1 .. E-7
```

Sprint A delivers visible UI surfaces (optimizer / activation / epoch-separation pickers, auto-snapshot toggle, snapshot tuning capture) without any algorithmic risk. After A, 3 of 6 deferred CAN items are unblocked and the dashboard exposes the major training knobs.

Sprint B closes the snapshot-replay loop (CAN-015 builds on A-5).

Sprint C is the deepest single-feature work — full CAN-013 with the new ensemble-unit type. Five PRs walking through the layers (config → forward pass → output retraining → serialization → UI). Detailed design in [`CAN_013_INTEGRATION_MODE_DESIGN.md`](CAN_013_INTEGRATION_MODE_DESIGN.md).

Sprint D is independent and can land anytime — slotted after C only because A/B/C carry visible UI value, while CAS-005 is internal cleanup.

Sprint E gets its own design doc in [`PHASE_6E_MULTI_NETWORK_DESIGN.md`](PHASE_6E_MULTI_NETWORK_DESIGN.md). The user has agreed to a separate scoping pass; no Sprint E code lands until that doc lands first.

## Out of scope for Phase 6E

These items are bundled in §25.2 6E but warrant deferring or splitting off:

- **CAS-008** (multi-hierarchical CasCor): folded into PR #10 since the architectural change is the same as CAN-021/CAS-009. If hierarchies turn out to be orthogonal to populations, split when designing PR #10.
- **CAS-005** (shared code extraction): mechanically independent. Could land before any Phase 6E work without conflict. Listed as PR #8 but order isn't load-bearing.
- **GPU/CUDA support, snapshot vector DB, large-file refactoring** (§10.5 entries): not in the §25.2 6E row at all; mentioned for completeness so we don't accidentally include them.

## Risks

1. **Verifying claims about cascor's existing infrastructure** is point-in-time. The Phase 6E PRs should each start with a quick re-check of the relevant code surface — the audit pattern says "the optimizer factory exists today" doesn't mean "exists when the PR is being written." Each PR description should cite the file:line it found.
2. **Snapshot round-trip (CAN-014)** is "verify it works" until proven otherwise. If the round-trip is broken in subtle ways (dtype downcast, missing fields, version skew), PR #6 grows.
3. **Multi-network architecture (PR #10)** has touch points across lifecycle, WS protocol, snapshots, and the Phase D control button mapping. Will need its own design pass; do not commit to scope until that's done.

## Decision points — resolved 2026-04-29

The three open questions from the original draft were resolved in conversation with the user:

1. ~~Sprint A vs. C ordering — CAS-005~~ → **Held for Sprint D**. Sprint A keeps the visible UI wins; cleanup ships after the user-visible surface is complete.
2. ~~CAN-013 narrow vs. extended~~ → **Full CAN-013 implemented**, including weighted_ensemble. Moved to its own sprint (Sprint C) with detailed design in [`CAN_013_INTEGRATION_MODE_DESIGN.md`](CAN_013_INTEGRATION_MODE_DESIGN.md).
3. ~~Multi-network design pass~~ → **Separate design doc**, [`PHASE_6E_MULTI_NETWORK_DESIGN.md`](PHASE_6E_MULTI_NETWORK_DESIGN.md). No Sprint E code lands until that doc reaches review.

Open questions raised inside the new design docs (lower-priority, can be picked up at PR-implementation time):

- CAN-013: constrained vs. unconstrained α (default unconstrained); ensemble_size default (3); UI visualization choice (one node with "K=3" label)
- Multi-network: `max_concurrent_training_networks` default (4); REST route deprecation timeline (when canopy migrates); Sprint E sequencing (single sprint vs. split E1+E2)

These are inside the per-design-doc "Decision points" sections — fold them into PR descriptions when the corresponding sprints start.
