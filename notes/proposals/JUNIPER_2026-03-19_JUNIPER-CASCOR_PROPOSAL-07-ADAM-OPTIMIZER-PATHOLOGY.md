# Proposal 7: Fresh Adam Optimizer Perturbs Converged Weights

**Severity**: MODERATE-HIGH
**Root Cause ID**: RC-P3

---

## Summary

Line 241 of demo_mode.py creates a fresh Adam optimizer after the 1000-step retrain. Adam's bias correction ensures the first step has effective learning rate exactly equal to `lr=0.01` regardless of gradient magnitude, producing a fixed-magnitude perturbation of already-converged weights. This perturbation undoes retrain work and contributes to the flat loss curve during cooldown.

## Mechanism

Adam's first step with zero moments and bias correction:

```bash
m_hat = g / (1 - 0.9^1) / (1/(1-0.9)) = g  (the gradient itself)
v_hat = g^2 / (1 - 0.999^1) / (1/(1-0.999)) = g^2
update = lr * g / (|g| + eps) = lr * sign(g) = 0.01 * sign(g)
```

This is a fixed-magnitude step of 0.01 regardless of gradient size. On converged weights (gradient ~1e-5), this is a ~1000x overshot.

## Evidence

- Line 234: Fresh Adam for retrain (correct — starts fresh for expanded architecture)
- Lines 237-238: 1000 retrain steps (converges the output)
- Line 241: SECOND fresh Adam (problematic — discards well-conditioned retrain moments)
- Comment: "Fresh optimizer for outer-loop (reset stale retrain moments)"
- The retrain moments are NOT stale — they accurately reflect the converged loss landscape

## Proposed Fix

**Option A (Recommended)**: Delete line 241 entirely. Retain the retrain optimizer. Its moments encode the loss curvature at the converged minimum, which is exactly what the outer loop needs.

**Option B**: Skip outer-loop training during cooldown (only compute metrics, no gradient steps).

**Option C**: Use much lower lr for post-retrain optimizer (lr × 0.01 = 0.0001).

## Risk Assessment

- **Very low effort**: Option A is deleting 1 line + comment
- **Low risk**: Keeping warm optimizer is standard practice; retrain landscape = outer loop landscape
- **Medium reward**: Eliminates post-cascade perturbation; loss curve becomes monotonically decreasing
