# Proposal 5: Output Weight Initialization Gradient Scale Mismatch

**Severity**: MEDIUM-LOW
**Root Cause ID**: RC-P9 (partial)

---

## Summary

The new output column for a hidden unit is initialized with `randn * 0.1`, matching the production CasCor. While not wrong in isolation, the combination of small initialization + warm-started dominant old weights + fresh Adam optimizer creates a gradient scale mismatch that disadvantages the new column during the 1000-step retrain.

## Mechanism

1. Old output weights are at their converged values (magnitude ~0.5-5.0)
2. New column initialized at ~0.1 (contributes ~0.1 × tanh output to prediction)
3. Old weights already explain most variance; residual is small
4. Gradient for new column is proportional to (small residual) × (hidden output)
5. Old columns absorb gradient signal via small adjustments, stealing from new column
6. Fresh Adam normalizes per-parameter, but new column starts in a flat region

## Evidence

- Demo: `torch.randn(...) * 0.1` (line 231, OUTPUT_WEIGHT_INIT_STD = 0.1)
- Production: `torch.randn(...) * 0.1` (line 2823, same constant)
- Both create fresh optimizers for retrain
- Production CasCor successfully trains past first unit with these same parameters

## Proposed Fix (Low Priority)

**Option A**: Initialize new column at zero (network output unchanged at addition time)
**Option B**: Per-parameter-group learning rate (5-10x higher for new column)
**Option C**: Two-phase retrain: 200 steps new-column-only, then 800 steps joint

## Risk Assessment

- **Low effort**: Options A/B are 2-5 lines each
- **Low risk**: All conservative changes
- **Low-Medium reward**: Secondary factor; production CasCor works with same init
