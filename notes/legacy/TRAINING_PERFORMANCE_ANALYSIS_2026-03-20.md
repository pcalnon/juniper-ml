# Training Performance Analysis: Output Training Stagnation

**Date**: 2026-03-20
**Thread**: `imperative-meandering-steele`
**Inputs**: Screenshots of Canopy dashboard, prior analysis documents (6 files + 10 proposals), source code review

---

## Observed Problem

From the dashboard screenshots:
1. **Image #3** (Epoch 404, 22 hidden units): Output training phases (yellow bands) show flat loss (~0.1144) and accuracy (~82.50%) with no visible improvement. Each output training phase spans only 1-5 epoch ticks.
2. **Image #4** (Epoch 661, 35 hidden units): "Between Hidden Units" mode shows loss **spikes** during output training after unit #35, then recovers. Accuracy drops to 0 during output phase then recovers. Pattern worsens with more hidden units.

---

## Root Cause Analysis

### Finding 1: Output Training IS Running 1000 Steps — Only 2-5 Epochs Displayed

The code at `demo_mode.py:1069-1088` runs `OUTPUT_RETRAIN_STEPS = 1000` gradient steps per hidden unit installation. However, metric emissions are **time-based** (every ~1 second, controlled by `update_interval`). Since 1000 gradient steps complete in 2-5 seconds wall-clock time, only **2-5 epoch data points** are emitted per retrain phase.

**This is a display artifact, not a training deficit.** The retrain is running its full 1000-step budget.

### Finding 2: Fresh Optimizer Bias Correction Causes First-Step Overshoot

Each hidden unit installation (via `install_candidate()` at line 339) creates a **fresh Adam optimizer**:
```python
self.output_optimizer = torch.optim.Adam(self.output_layer.parameters(), lr=self.learning_rate)
```

Adam's bias correction amplifies the first gradient step:
- First step: `m_hat = m / (1 - 0.9^1) = 10x amplification`
- First step: `v_hat = v / (1 - 0.999^1) = 1000x amplification`

This causes the **loss spike** visible in Image #4 — the first few optimizer steps after unit installation overshoot the optimal weights, temporarily disrupting the already-converged output layer.

**Prior analysis status**: Phase 6A identified this as RC-P3 and noted the fix at lines 252-255 (retain optimizer after retrain). However, `install_candidate()` at line 339 **still creates a fresh optimizer**, which means the fix only applies within `add_hidden_unit()`, not in the `_training_loop()` path.

**Impact**: HIGH — explains the loss spikes and temporary accuracy collapse in Image #4.

### Finding 3: New Output Column Initialized with Noise (0.1 std)

When a hidden unit is installed (`install_candidate()` line 337):
```python
self.output_layer.weight[:, old_layer.in_features:] = torch.randn(...) * 0.1
```

The new weight column connecting the new hidden unit to outputs is random noise with std=0.1. The old weights (already converged) are preserved via warm-start (line 335).

**Why this matters**: The 0.1 std initialization may be too large or too small relative to the scale of the hidden unit's output (which passed through tanh, range [-1, 1]). The optimizer must learn the correct weight from scratch, but:
- The old weights are already near-optimal for the previous architecture
- The single new weight column has limited gradient signal (one feature added)
- 1000 steps may be sufficient to find the right weight, but the improvement is small

### Finding 4: Per-Unit Loss Improvement Is Genuinely Small After 5-10 Units

This is the **core algorithmic finding**, confirmed by multiple analysis paths:

**Residual variance collapse**: After each hidden unit is installed and output retrained, the residual error shrinks. Later candidates maximize correlation with a progressively smaller residual. Each new unit's contribution to loss reduction is proportionally smaller:

| Hidden Units | Typical Per-Unit Loss Reduction | Visual on 400px Chart |
|-------------|-------------------------------|----------------------|
| 1-5 | 0.01-0.05 MSE | 10-50 pixels (visible staircase) |
| 5-10 | 0.003-0.01 MSE | 3-10 pixels (barely visible) |
| 10-20 | 0.001-0.003 MSE | ~1 pixel (invisible) |
| 20-35 | 0.0005-0.001 MSE | sub-pixel (completely invisible) |

**This is inherent to the CasCor algorithm on complex problems.** The 3-rotation spiral requires ~15+ units, and each contributes diminishing returns after the first major features are learned.

### Finding 5: Convergence Detection Is Dead Code (Validated Correction)

**Original claim**: Convergence detection triggers prematurely.

**Validated finding**: `_should_add_cascade_unit()` (line 896) is **never called** in the training loop. Cascade additions are driven entirely by candidate pool training success at lines 1028-1040. The convergence check, window, threshold, and cooldown mechanism are all inert.

The cascade loop runs unconditionally until `max_hidden_units` or `max_epochs` is reached, adding one unit per iteration as long as `train_candidate_pool()` returns a candidate with correlation >= `MIN_CANDIDATE_CORRELATION` (0.01).

**Implication**: The convergence UI controls (checkbox + threshold slider) have **no effect on training**. This is a UX issue — users adjusting these controls will see no change in behavior.

### Finding 6: Candidate Quality IS Maintained (Phase 6A Fixes Effective)

The correlation threshold guard (`MIN_CANDIDATE_CORRELATION = 0.01`) prevents noise-level candidates from being installed. Xavier initialization prevents tanh saturation. These Phase 6A fixes are correctly implemented.

However, the guard threshold of 0.01 may be too low — a correlation of 0.01 represents minimal signal relative to noise, and installing such candidates provides negligible loss improvement.

---

## Synthesis: Why Training Stagnates After 5-10 Hidden Units

The stagnation is caused by **four reinforcing factors**:

1. **Diminishing residuals** (algorithmic): Each unit reduces the residual, leaving less signal for the next candidate. This is fundamental to CasCor and expected.

2. **Fresh optimizer disruption** (bug — Priority 1): Each `install_candidate()` creates a fresh Adam optimizer that overshoots on the first few steps, temporarily increasing loss. The 1000-step retrain recovers, but the net improvement over the previous state is small. The Phase 6A.1 fix was applied to dead code and does not affect the production path.

3. **Epoch compression** (display): 1000 gradient steps compressed into 2-5 epoch ticks makes the output training phase appear to have zero improvement, even when small improvements occur within the retrain.

4. **Y-axis autoranging** (visualization): Plotly autoranges the y-axis to the full loss range. Once loss drops from ~0.5 to ~0.1 (first 5 units), subsequent improvements of 0.001-0.003 are invisible at the chart scale.

---

## Specific Code Issues

### Issue A: Fresh Optimizer in `install_candidate()` (CONFIRMED BUG)

**Severity**: HIGH — validated by multiple agents as a real, active bug in the production training path.

`install_candidate()` at line 339 creates a fresh Adam optimizer every time a candidate is installed. The Phase 6A comment at lines 252-255 (in `add_hidden_unit()`) explicitly warns that this causes "~1000x overshoot on the first step due to Adam's bias correction."

**Critical validation discovery**: `add_hidden_unit()` is **dead code** — it is defined at line 185 but never called anywhere in the codebase. The production training path in `_training_loop()` calls `train_candidate_pool()` (line 1028) then `install_candidate()` (line 1046). This means the Phase 6A.1 fix (optimizer retention comment at lines 252-255) was applied to the **wrong method** and has zero effect on actual training.

**Evidence chain**:
- `_training_loop()` line 1046: calls `self.network.install_candidate(best_unit)`
- `install_candidate()` line 339: creates fresh optimizer unconditionally
- `add_hidden_unit()` line 246: also creates fresh optimizer but has the Phase 6A.1 comment — **never called**

**Fix**: Apply the optimizer warm-start fix to `install_candidate()` at line 339 (the method that is actually called).

### Issue B: Convergence Detection Is Dead Code (CORRECTED BY VALIDATION)

**Severity**: N/A — originally identified as an active issue but validated as **dead code**.

`_should_add_cascade_unit()` is defined at line 896 but **never called** in `_training_loop()`. Cascade additions are triggered solely by successful candidate pool training (lines 1028-1040): the cascade loop runs `train_candidate_pool()` and installs the result if correlation >= `MIN_CANDIDATE_CORRELATION` (0.01).

The convergence threshold, window size, cooldown mechanism, and convergence UI controls are all **inert**. They have no effect on training behavior.

**Note**: The convergence UI controls (checkbox + threshold slider) in the dashboard are wired to `_should_add_cascade_unit()` but since that method is never called, changing these controls has no effect on training. This is a separate UX issue (dead controls).

### Issue C: Metric Emission Frequency During Retrain

With only 2-5 epoch emissions per 1000-step retrain, the dashboard cannot show the within-retrain improvement curve. Users see a flat line where there may be actual descent.

**Fix**: Emit more frequently during retrain phases to show the within-retrain loss curve (e.g., emit every 200 steps or reduce update_interval to 0.2 seconds during retrain).

### Issue D: Consider Log-Scale or Delta Loss Visualization

Add an option to show loss improvement per unit (delta) rather than absolute loss, making sub-pixel improvements visible.

---

## Validation Corrections

The following items from the initial analysis were **corrected by validation sub-agents**:

| Original Claim | Validation Finding | Status |
|----------------|-------------------|--------|
| Convergence detection triggers prematurely | `_should_add_cascade_unit()` is never called — dead code | **CORRECTED** |
| Convergence threshold too sensitive (0.001) | Threshold has no effect — function never invoked | **CORRECTED** |
| Convergence window spans phase boundaries | Window logic exists but is never executed | **CORRECTED** |
| Phase 6A.1 fix partially applied | Fix was applied to dead code (`add_hidden_unit()`), NOT the production path (`install_candidate()`) | **CONFIRMED AND ESCALATED** |

---

## Relationship to Prior Analysis Documents

| Prior Finding | Status | This Analysis |
|--------------|--------|---------------|
| RC-P1 (Phantom Phase) | Fixed in Phase 6A | Confirmed: phantom phase eliminated in `_training_loop()`. |
| RC-P2 (Convergence Timing) | Dead Code | `_should_add_cascade_unit()` is never called. Convergence UI controls are inert. |
| RC-P3 (Fresh Adam Optimizer) | **NOT FIXED** | Phase 6A.1 fix applied to dead code (`add_hidden_unit()`). Production path (`install_candidate()` line 339) still creates fresh optimizer. |
| RC-P4 (Spiral Complexity) | By Design | Confirmed: per-unit improvements are sub-pixel after unit 10. |
| RC-P5 (Gradient Clipping) | Fixed | Confirmed removed from all paths. |
| RC-P6 (Correlation Threshold) | Fixed | Guard at 0.01 is active in `train_candidate_pool()`. |
| RC-P7 (UI Lock) | Deferred | Lock granularity is good — brief locks throughout. |
| RC-P8 (Residual Variance Collapse) | Acknowledged | Fundamental to CasCor; mitigated by Pearson normalization but not eliminated. |
| RC-P9 (Tanh Saturation) | Fixed | Xavier init confirmed in `add_hidden_unit()` (line 206). Also present in `train_candidate_pool()`. |
| RC-P10 (Parameter Desync) | Deferred | Not evaluated in this analysis. |

---

## Recommended Actions (Priority Order)

### Priority 1: Fix Fresh Optimizer in `install_candidate()` (Bug)

**File**: `juniper-canopy/src/demo_mode.py`, line 339

The production cascade path creates a fresh Adam optimizer after every unit installation, discarding learned momentum and causing bias-correction overshoot. Apply the same warm-start approach documented in the Phase 6A.1 comment (lines 252-255 of the dead `add_hidden_unit()`).

### Priority 2: Remove or Connect Dead Code

Either:
- **Remove** `add_hidden_unit()` and `_should_add_cascade_unit()` (dead code cleanup), OR
- **Connect** the convergence detection to the training loop if it's intended to be functional, and ensure the convergence UI controls actually affect behavior

### Priority 3: Increase Retrain Emission Frequency

Reduce `update_interval` during retrain phases to show the within-retrain loss curve (e.g., emit every 200 steps or reduce to 0.2 seconds during retrain).

### Priority 4: Consider Log-Scale or Delta Loss Visualization

Add an option to show loss improvement per unit (delta) rather than absolute loss, making sub-pixel improvements visible.
