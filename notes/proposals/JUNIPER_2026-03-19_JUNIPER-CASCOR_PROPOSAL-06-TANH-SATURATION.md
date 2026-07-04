# Proposal 6: Tanh Saturation from Growing Input Dimension

**Severity**: MODERATE
**Root Cause ID**: RC-P9

---

## Summary

Candidate weight initialization uses a fixed `std=0.1` regardless of input dimension. As cascade depth grows (input_dim = 2 + N hidden units), pre-activation variance increases linearly, causing tanh saturation. Saturated units produce constant output, contributing zero discriminative information.

## Mechanism

1. Candidate weights: `randn(input_dim) * 0.1`, fixed std regardless of input_dim
2. Pre-activation: `z = sum(input * weights) + bias`
3. Var(z) = input_dim × Var(input) × Var(weights) ∝ input_dim
4. For input_dim=2: Var(z) ≈ 0.02, tanh operates in linear region
5. For input_dim=12 (10 hidden units): Var(z) ≈ 0.12, tanh begins saturating
6. For input_dim=22 (20 hidden units): Var(z) ≈ 0.22, significant saturation
7. Candidate training (Adam, 600 steps) drives weights further toward saturation to maximize correlation

## Impact

- Saturated tanh output → constant feature → output weight for that unit acts as redundant bias
- Each subsequent unit increasingly likely to saturate → diminishing returns
- After 5-8 units, new units contribute negligibly

## Proposed Fix

**Option A**: Scale initialization by fan-in: `init_std = 1.0 / sqrt(input_dim)` (Xavier-like)
**Option B**: Clamp pre-activation: `z = torch.clamp(z, -4.0, 4.0)` before tanh
**Option C**: Apply batch normalization before tanh activation

## Risk Assessment

- **Low effort**: Option A is 1 line change
- **Low risk**: Xavier scaling is well-established
- **Medium reward**: Prevents saturation for deeper cascades; more impactful for complex datasets requiring many hidden units
