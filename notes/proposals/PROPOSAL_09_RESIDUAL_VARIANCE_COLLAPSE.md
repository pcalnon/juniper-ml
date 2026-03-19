# Proposal 9: Residual Variance Collapse and Missing Correlation Threshold

**Severity**: HIGH
**Root Cause ID**: RC-P6 + RC-P8

---

## Summary

As the network improves, the residual error shrinks and its variance collapses. Pearson correlation's numerical conditioning degrades, candidate correlations approach noise level. Additionally, the demo has **no correlation threshold guard** — it always installs the best candidate regardless of quality, unlike the production CasCor which checks `best_correlation > 0.0005`.

## Mechanism

### Residual Variance Collapse

1. After 1-2 hidden units, residual shrinks (e.g., per-sample error ~0.02)
2. `e_centered = residual - residual.mean()` produces values on order 1e-4 to 1e-5
3. Covariance `(v_centered * e_centered).sum()` suffers catastrophic floating-point cancellation
4. std_v remains healthy (~0.1-1.0), std_e shrinks → correlation pushed toward zero
5. All 32 candidates produce noise-level correlations

### Missing Correlation Threshold

- Production CasCor checks `best_correlation > 0.0005` before installing (line 2974)
- Demo has no such check — installs candidate regardless of quality
- Low-correlation candidates provide no useful feature to the output layer
- Output retrain cannot improve because the new feature is noise

## Evidence

- Demo `_train_candidate()` lines 289-294: standard Pearson with epsilon 1e-8 inside sqrt
- Production `_calculate_correlation` line 1060: same epsilon approach
- Production `grow_network()` line 2973-2976: correlation threshold check
- Demo `_should_add_cascade_unit()`: no correlation quality check anywhere

## Proposed Fix

1. **Add correlation threshold guard**: Before installing a candidate, check `if best_correlation > 0.1` (or configurable threshold). If no candidate meets threshold, skip cascade addition.
2. **Normalize residual before candidate training**: Scale residual to unit variance: `residual_norm = residual / (residual.std() + 1e-6)`. This improves numerical conditioning without changing the theoretical optimum.
3. **Move epsilon outside sqrt**: Change `sqrt(sum + 1e-8)` to `sqrt(sum) + 1e-12` for better conditioning at small scales.

## Risk Assessment

- **Low effort**: Threshold guard is 3-4 lines; normalization is 1 line
- **Low risk**: Conservative changes; production CasCor already uses correlation threshold
- **High reward**: Prevents installation of useless candidates; stops the degenerative feedback loop
