# Proposal 1: Phantom Inter-Cascade Training Phase

**Severity**: CRITICAL
**Root Cause ID**: RC-P1 + RC-P2
**Agents**: Proposal 1 (Single-Step Outer Loop) + Proposal 10 (Cooldown + Convergence Interaction)

---

## Summary

The demo's `_training_loop()` performs 1 gradient step per epoch between cascade additions — a training phase that **does not exist in the CasCor algorithm**. The production CasCor goes directly from output retrain → compute residual → train candidates → install → retrain. The demo's phantom phase produces provably zero useful training on an already-converged surface, and the convergence detector correctly identifies this as stagnation, triggering premature cascade additions.

## Mechanism

1. `add_hidden_unit()` runs 1000 full-batch Adam steps, converging the output layer
2. A fresh Adam optimizer is created (line 241) for the outer loop
3. For 50 cooldown epochs, the outer loop does 1 step/epoch on the converged surface
4. Loss changes by ~0.00001 per epoch (provably negligible for convex MSE)
5. After cooldown, convergence detector checks 10 epochs: improvement < 0.001 → triggers next cascade
6. Cycle repeats every ~60 epochs until max_hidden_units exhausted

## Evidence

- Production `grow_network()` (cascor lines 2959-3048): no inter-cascade training
- Production goes directly from `_retrain_output_layer()` to `_calculate_residual_error_safe()`
- Demo `_training_loop()` line 839: calls `_simulate_training_step()` every epoch
- `_simulate_training_step()` line 711: calls `train_output_step()` once (1 gradient step)
- CASCADE_COOLDOWN_EPOCHS = 50, convergence window = 10 epochs, threshold = 0.001

## Proposed Fix

**Restructure _training_loop() to match the CasCor two-phase cycle:**

Each iteration of the training loop should:

1. Run `add_hidden_unit()` (candidate training + installation + 1000-step retrain)
2. Compute post-retrain metrics and broadcast
3. Check stopping criteria (max units, correlation threshold, accuracy target)
4. Emit intermediate progress during retrain for dashboard visualization

Remove: phantom 1-step/epoch training, convergence-based cascade detection, cascade cooldown.
Replace convergence detection with: correlation threshold check (matching production CasCor).

## Risk Assessment

- **High effort**: Requires restructuring the core training loop
- **Medium risk**: Changes visible training dynamics; dashboard expects 1-epoch-per-second updates
- **High reward**: Eliminates the fundamental algorithmic mismatch; training would match production CasCor behavior
