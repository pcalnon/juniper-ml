# Proposal 4: Convergence Detection Timing Pathology

**Severity**: HIGH
**Root Cause ID**: RC-P2 (subset of RC-P1)

---

## Summary

The convergence detector uses `recent[0] - recent[-1]` (two-point comparison over 10 epochs) to decide when to add a hidden unit. After the 1000-step retrain converges the output, the subsequent 10 epochs of 1-step training show < 0.001 improvement, always triggering another cascade addition. The detector is correct but measuring artificial stagnation.

## Mechanism

1. 1000-step retrain converges output layer to near-optimum
2. Fresh Adam optimizer created (zero momentum)
3. 50 cooldown epochs: 1 step each, ~0.00001 loss change per epoch
4. Cooldown expires; convergence checks last 10 epochs
5. `improvement = recent[0] - recent[-1]` ≈ 0.0001 < threshold 0.001
6. Cascade addition triggered immediately
7. Net inter-cascade interval: always 50 (cooldown) + first eligible epoch ≈ 51 epochs

## Bugs in Detection Logic

1. **Two-point comparison is fragile**: Only checks endpoints, not trend. Loss oscillation makes `improvement` negative → triggers addition
2. **No awareness of retrain baseline**: Detector doesn't know the retrain already converged; it evaluates post-retrain single steps
3. **Fresh optimizer pollutes the window**: First few steps with cold Adam produce erratic loss values
4. **Fixed schedule never fires**: Cooldown (50) > cascade_every (30), so overlapping cooldowns permanently suppress the fixed schedule fallback

## Proposed Fix

**Option A (Targeted):** Replace two-point comparison with linear regression slope over the window:

```python
slope = np.polyfit(range(len(recent)), recent, 1)[0]
if slope > -conv_threshold: return True  # not improving fast enough
```

**Option B (Structural):** Replace convergence detection entirely with a correlation threshold check (matching production CasCor): if no candidate exceeds correlation 0.0005, stop growing.

**Option C (Complementary):** Inject a full window (10 entries) of post-retrain loss into history, giving the detector a clean baseline.

## Risk Assessment

- **Low-Medium effort**: Option A is ~5 lines; Option B requires restructuring
- **Low risk**: All options are backward-compatible
- **Medium reward**: Prevents premature cascade triggering; more impactful when combined with Proposal 1
