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

Grouping by surface affinity (= what touches the same files / mental model), not strictly by ID order. Each row is one PR.

| # | PR | Scope | Cascor changes | Canopy changes | Notes |
|---|---|---|---|---|---|
| 1 | **Training params epoch separation** (CAS-002 + CAS-003) | S | Verify three epoch fields are surfaced through `TrainingParams`; add `network_max_epochs` if not already aliased | Add 3 inputs in sidebar | Pure parameter additions; existing infra in cascor |
| 2 | **Optimizer surface** (CAN-010 + ENH-006) | S–M | `optimizer_type: Literal[…]` added to `TrainingParams`; thread to `OptimizerConfig` | Dropdown in sidebar; surface in Parameters tab | Cascor side ~30 LoC; canopy ~50 LoC |
| 3 | **Activation surface** (CAN-011) | S | `activation_function_name: Literal[…]` added to `TrainingParams`; thread to network constructor | Dropdown in sidebar | Smaller than #2; ~20 LoC each side |
| 4 | **N-best / integration_mode (sequential, batch)** (ENH-007 + CAN-013-narrow) | M | Rename `candidates_per_layer` to `integration_mode: Literal["sequential", "batch"]` + count; expose via `TrainingParams` | Mode radio + count input | Defers `weighted_ensemble` to a follow-up |
| 5 | **Auto-snap best** (CAS-006) | S | `_best_accuracy` tracking + `auto_snapshot_best` gate around `create_snapshot()` | Toggle in sidebar (or sticky default) | Pure cascor; canopy gets one boolean toggle |
| 6 | **Snapshot tuning round-trip** (CAN-014) | S | Verification + tests; if any field is dropped on load, fix it | Surface "Loaded from snapshot N" indicator after restore | Mostly tests; small-but-hardening |
| 7 | **Snapshot replay → fresh training** (CAN-015) | M | New lifecycle path `restore_for_retrain(snapshot_id)`: load weights → reset training counters → ready for new `start_training()` | Snapshots panel: "Replay" action button | Builds on #6 |
| 8 | **CAS-005: shared-code extraction** | M-L | Move duplicated cascor↔worker code into a `juniper-core` package | None | Cross-repo cleanup; independent of others |
| 9 | **CAN-013-extended: weighted_ensemble integration mode** | M-L | Add weighted-ensemble mode to grow_network's strategy switch | New mode option in #4's UI | Optional follow-up |
| 10 | **CAS-008 / CAS-009 / CAN-021: multi-network architecture** | **XL** | NetworkRegistry refactor; `LifecycleManager` operates on the active network; population APIs; snapshot scoping | New "Population" tab; cross-network comparison view | Genuinely XL; design doc in its own follow-up before coding |

Ten PRs total. **PRs 1–7 are all S–M and unblock the bulk of the CAN-* surface.** PR 8 is independent code-cleanup. PR 9 is optional. PR 10 is the only genuinely XL item.

## Recommended order

```
Sprint A (small wins, ~1 week):     1, 2, 3, 5, 6
Sprint B (medium, ~1 week):         4, 7
Sprint C (cleanup, optional):       8, 9
Sprint D (XL, separate effort):     10
```

Sprint A delivers visible UI surfaces (optimizer / activation / epoch-separation pickers, auto-snapshot toggle) without any algorithmic risk. After A, 3 of 6 deferred CAN items are unblocked and the dashboard exposes the major training knobs.

Sprint B closes the snapshot-replay loop (CAN-014/015) and the integration-mode picker (CAN-013).

Sprint C is independent and can ship anytime.

Sprint D needs its own design doc — multi-network state has cross-cutting implications for snapshot lifecycle, WS broadcast routing (per-network or merged?), and the existing "1 active training run" assumption baked into Phase D control buttons.

## Out of scope for Phase 6E

These items are bundled in §25.2 6E but warrant deferring or splitting off:

- **CAS-008** (multi-hierarchical CasCor): folded into PR #10 since the architectural change is the same as CAN-021/CAS-009. If hierarchies turn out to be orthogonal to populations, split when designing PR #10.
- **CAS-005** (shared code extraction): mechanically independent. Could land before any Phase 6E work without conflict. Listed as PR #8 but order isn't load-bearing.
- **GPU/CUDA support, snapshot vector DB, large-file refactoring** (§10.5 entries): not in the §25.2 6E row at all; mentioned for completeness so we don't accidentally include them.

## Risks

1. **Verifying claims about cascor's existing infrastructure** is point-in-time. The Phase 6E PRs should each start with a quick re-check of the relevant code surface — the audit pattern says "the optimizer factory exists today" doesn't mean "exists when the PR is being written." Each PR description should cite the file:line it found.
2. **Snapshot round-trip (CAN-014)** is "verify it works" until proven otherwise. If the round-trip is broken in subtle ways (dtype downcast, missing fields, version skew), PR #6 grows.
3. **Multi-network architecture (PR #10)** has touch points across lifecycle, WS protocol, snapshots, and the Phase D control button mapping. Will need its own design pass; do not commit to scope until that's done.

## Decision points for the user

Before PR #1 starts:

1. **Sprint A vs. C ordering** — PR #8 (CAS-005 shared code) is fully independent. It could go first if you'd rather de-risk the shared-code lift now, or it could slot in any time. My lean: hold for Sprint C since the visible UI wins (Sprint A) ship faster and have higher demo value.
2. **CAN-013 narrow vs. extended** — PR #4 ships sequential + batch modes (= rename of existing infra). PR #9 adds weighted_ensemble. Are weighted ensembles worth the extra design pass, or should we ship the rename and call CAN-013 done?
3. **PR #10 design pass** — agree to hold off on multi-network architecture until a separate design doc lands? Or should I scope it now in this same doc?
