# Proposal 2: Candidate Quality Degradation from Gradient Clipping and Early Stopping

**Severity**: HIGH
**Root Cause ID**: RC-P5

---

## Summary

The demo's candidate training includes gradient clipping (max_norm=5.0) and an early stopping threshold (best + 1e-6) that are **not present in the production CasCor**.
These cause premature termination of candidate training when residuals are small (after the first hidden unit), producing low-quality candidates that contribute minimal improvement when installed.

## Mechanism

1. After first hidden unit reduces error, residual shrinks
2. Gradient magnitudes for candidate training decrease proportionally
3. Gradient clipping at 5.0 is a no-op for small gradients but creates Adam moment estimate instability when gradients occasionally spike
4. Early stopping threshold (1e-6) terminates training when improvements are small but steady
5. Production CasCor uses `abs(current) > abs(best)` (ANY improvement resets patience) — demo requires improvement > 1e-6
6. Result: candidates are "trained" for only 50-100 of their 600 allocated steps

## Evidence

| Feature                  | Demo                                    | Production CasCor                  |
|--------------------------|-----------------------------------------|------------------------------------|
| Gradient clipping        | clip_grad_norm_max_norm=5.0 (line 298)  | **None**                           |
| Early stopping threshold | best + 1e-6 (line 303)                  | abs(current) > abs(best), no delta |
| Optimizer                | Adam per candidate                      | Manual SGD via autograd            |

## Proposed Fix

1. **Remove gradient clipping**: Delete line 298 (`clip_grad_norm_`)
2. **Remove minimum improvement threshold**: Change `best + 1e-6` to `best` for early stopping
3. **Consider switching from Adam to plain SGD for candidates**: Matches production CasCor; plain SGD is more robust for small-gradient regimes

## Risk Assessment

- **Low effort**: 2 line changes
- **Low risk**: Removing clipping cannot cause crashes; removing threshold only allows longer training
- **Medium-High reward**: Directly improves candidate quality, especially for later hidden units
