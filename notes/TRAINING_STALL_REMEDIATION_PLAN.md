# CasCor Demo Training Stall — Remediation Plan (Phase 6)

**Project**: Juniper Ecosystem (juniper-canopy + juniper-cascor)
**Created**: 2026-03-19
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Phase 6A Implementation Complete
**Scope**: Cross-repo (juniper-canopy primary)
**Supersedes**: Phases 1-5.2 addressed mechanical/algorithmic bugs; this phase addresses the structural training loop mismatch and remaining algorithmic deficiencies

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Root Cause Ranking](#root-cause-ranking)
- [Implementation Strategy](#implementation-strategy)
- [Phase 6A: Quick Wins](#phase-6a-quick-wins-30-minutes)
- [Phase 6B: Evaluate and Decide](#phase-6b-evaluate-and-decide)
- [Phase 6C: Structural Refactor](#phase-6c-structural-refactor-4-8-hours)
- [Testing Plan](#testing-plan)
- [Validation Methodology](#validation-methodology)
- [Audit Trail](#audit-trail)

---

## Executive Summary

Despite Phases 1-5.2 resolving all mechanical and algorithmic bugs (activation function, loss function, optimizer, correlation normalization, input normalization, convergence UI controls), the demo training continues to stall after the first hidden node is added.

A comprehensive multi-agent analysis identified **10 distinct root causes** organized into 3 clusters:

1. **Structural mismatch** (CRITICAL): The demo's training loop has a "phantom inter-cascade phase" — a 1-step-per-epoch outer training loop between cascade additions — that does not exist in the CasCor algorithm. The 1000-step retrain inside `add_hidden_unit()` already converges the output; the subsequent 50+ single-step epochs are provably unproductive on the converged convex surface.

2. **Candidate quality degradation** (HIGH): Gradient clipping (not in production CasCor), aggressive early stopping threshold, missing correlation threshold guard, and residual variance collapse combine to produce progressively weaker candidates that contribute nothing when installed.

3. **Visualization/UX issues** (HIGH for user experience): 3-rotation spiral requires 10-15 units for visible improvement; UI lock held for 5-20 seconds during cascade addition; post-retrain metrics not immediately visible.

### Core Fix Path

Three changes address the primary root cause, the most impactful secondary cause, and the primary amplifier:

| Fix                                             | Target | Effort  | Impact                                          |
|-------------------------------------------------|--------|---------|-------------------------------------------------|
| Delete second fresh Adam optimizer (line 241)   | RC-P3  | 1 line  | Eliminates post-retrain weight perturbation     |
| Remove gradient clipping + early stopping delta | RC-P5  | 2 lines | Restores candidate training quality             |
| Add correlation threshold guard                 | RC-P6  | 4 lines | Prevents installation of noise-level candidates |

---

## Root Cause Ranking

Ranked by **likelihood of being the actual root cause** (algorithmic expert assessment):

| Rank | ID     | Proposal                                                   | Severity      | Role                                                      |
|------|--------|------------------------------------------------------------|---------------|-----------------------------------------------------------|
| 1    | RC-P1  | Phantom inter-cascade training phase                       | CRITICAL      | PRIMARY ROOT CAUSE — structural mismatch with CasCor spec |
| 2    | RC-P2  | Convergence timing pathology                               | CRITICAL      | Same as #1 (observable symptom side)                      |
| 3    | RC-P6  | Missing correlation threshold + residual variance collapse | HIGH          | SECONDARY ROOT CAUSE — independent algorithmic deficiency |
| 4    | RC-P3  | Fresh Adam optimizer perturbs converged weights            | MOD-HIGH      | AMPLIFIER of #1 — damaging only within phantom phase      |
| 5    | RC-P5  | Candidate quality decay (grad clipping + early stop)       | HIGH          | AMPLIFIER of #3 — accelerates residual collapse           |
| 6    | RC-P9  | Tanh saturation from growing input dimension               | MODERATE      | TERTIARY — only relevant at 20+ hidden units              |
| 7    | RC-P7  | UI lock contention during cascade addition                 | CRITICAL (UX) | UX BUG — masks progress, does not prevent it              |
| 8    | RC-P4  | Spiral dataset complexity                                  | HIGH (UX)     | DESIGN CHOICE — amplifies perception of stall             |
| 9    | RC-P8  | Output weight initialization scale                         | LOW-MED       | NOT A BUG — matches working production CasCor             |
| 10   | RC-P10 | Post-reset parameter desynchronization                     | LOW           | EDGE CASE — does not cause primary stall                  |

### Cluster Analysis

| Cluster                  | Proposals       | Description                                                                                                                         | Fix Strategy                                                  |
|--------------------------|-----------------|-------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| A: Phantom Phase         | P1, P2, P3      | Structural mismatch: inter-cascade single-step training + convergence detection on converged surface + fresh optimizer perturbation | Loop restructure OR quick-win mitigations                     |
| B: Candidate Degradation | P5, P6, P9      | Candidate quality degrades: gradient clipping + early stop threshold + missing correlation guard + variance collapse + saturation   | Quick wins: remove clipping, add threshold guard, Xavier init |
| C: Visualization/UX      | P4, P7, P8, P10 | User perceives stall: sub-pixel improvements + UI freeze + missing metrics + param desync                                           | Spiral complexity + lock refactoring                          |

---

## Implementation Strategy

The plan is organized into three phases: **quick wins** (independent, low-risk fixes), **evaluate** (test effectiveness of quick wins), and **structural refactor** (if needed).

```bash
Phase 6A: Quick Wins (30 min) ─────────────────────────────────┐
  ├─ Step 6A.1: Delete second fresh Adam optimizer             │
  ├─ Step 6A.2: Remove candidate gradient clipping             │
  ├─ Step 6A.3: Remove early stopping 1e-6 threshold           │
  ├─ Step 6A.4: Add correlation threshold guard                │
  ├─ Step 6A.5: Xavier-scale candidate weight init             │
  └─ Step 6A.6: Update/add affected tests                      │
                                                               │
Phase 6B: Evaluate (30 min) ───────────────────────────────────┤
  ├─ Run demo on 3-rotation spiral → observe training curve    │
  ├─ Run demo on 1-rotation spiral → compare                   │
  └─ Decision: Is Phase 6C needed?                             │
                                                               │
Phase 6C: Structural Refactor (4-8 hrs) ───────────────────────┘
  ├─ Step 6C.1: Restructure _training_loop() to CasCor spec
  ├─ Step 6C.2: Replace convergence detection with correlation threshold
  ├─ Step 6C.3: Break lock granularity in add_hidden_unit()
  ├─ Step 6C.4: Emit retrain progress for dashboard
  ├─ Step 6C.5: Add cascade event markers to loss chart
  └─ Step 6C.6: Comprehensive test suite update
```

---

## Phase 6A: Quick Wins (~30 minutes)

All steps are independent and can be applied in any order. Each addresses a confirmed deficiency relative to the production CasCor implementation.

### Step 6A.1: Delete Second Fresh Adam Optimizer ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Line**: 241

**Change**: Delete line 241 and its comment. The optimizer created at line 234 (for the retrain) has well-conditioned moment estimates that accurately reflect the converged loss landscape. Discarding them and creating a fresh optimizer causes a ~1000x overshoot on the first outer-loop step.

```python
# DELETE these lines:
# Fresh optimizer for outer-loop (reset stale retrain moments)
self.output_optimizer = torch.optim.Adam(self.output_layer.parameters(), lr=self.learning_rate)
```

**Rationale**: The retrain optimizer's moments are NOT stale — they encode the curvature at the converged minimum. Production CasCor creates fresh optimizers only when starting a new `train_output_layer()` call, not between retrain and outer loop.

**Tests affected**: `test_phase6_implementation.py::test_fresh_optimizer_after_retrain` — currently asserts optimizer state is empty (validating the bug as intended behavior). Must be updated to assert optimizer state is NON-empty.

### Step 6A.2: Remove Candidate Gradient Clipping ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Line**: 298

**Change**: Delete the gradient clipping line. Production CasCor has no gradient clipping in candidate training.

```python
# DELETE this line:
torch.nn.utils.clip_grad_norm_([weights, bias], max_norm=TrainingConstants.CANDIDATE_GRAD_CLIP_NORM)
```

**Rationale**: Gradient clipping at 5.0 creates Adam moment estimate instability when gradients oscillate near the boundary. With Pearson correlation as the objective and Adam as the optimizer, gradients are naturally bounded; clipping is unnecessary and harmful for small-gradient regimes.

**Tests affected**: `test_phase6_implementation.py::test_candidate_gradient_clipping` — currently validates clipping behavior. Must be removed or inverted.

### Step 6A.3: Remove Early Stopping Minimum Delta ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Line**: 303

**Change**: Remove the `+ 1e-6` improvement threshold from candidate early stopping.

```python
# BEFORE:
if abs_corr > best_correlation + 1e-6:
# AFTER:
if abs_corr > best_correlation:
```

**Rationale**: Production CasCor's early stopping resets patience on ANY improvement (`abs(current) > abs(best)`). The 1e-6 threshold causes premature termination when correlations improve slowly (common with small residuals), resulting in candidates trained for only 50-100 of their 600 allocated steps.

**Tests affected**: May need to update any test that asserts specific early stopping behavior.

### Step 6A.4: Add Correlation Threshold Guard ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Location**: Inside `_training_loop()`, before `self.network.add_hidden_unit()` at line 887

**Change**: Add a correlation threshold check before installing a candidate. If the best candidate's correlation is below the threshold, skip the cascade addition.

This requires `add_hidden_unit()` to return the best correlation (or a boolean indicating whether a unit was actually installed). The simplest approach:

```python
# In add_hidden_unit(), at the end of candidate pool evaluation (before installation):
if best_correlation < TrainingConstants.MIN_CANDIDATE_CORRELATION:
    return None  # No candidate met quality threshold

# ... proceed with installation only if correlation is sufficient ...
return best_correlation
```

```python
# In _training_loop(), line 886-907 (inside the lock block):
with self._lock:
    result = self.network.add_hidden_unit()
    if result is not None:
        # Unit was installed — record post-retrain metrics and set cooldown
        hidden_count = len(self.network.hidden_units)
        # ... existing post-retrain metric recording (lines 894-901) ...
        self._cascade_cooldown_remaining = TrainingConstants.CASCADE_COOLDOWN_EPOCHS
    # else: no quality candidate found, skip post-processing
```

**Note**: The `add_hidden_unit()` call is wrapped in `with self._lock:` (line 886). The conditional post-processing must remain inside the same lock block. Python's `with` statement handles early exit correctly, but the existing post-processing logic (metric recording, cooldown reset) at lines 888-904 must be guarded by `if result is not None:`.

**New constant**: `MIN_CANDIDATE_CORRELATION = 0.01` in `canopy_constants.py`

**Rationale**: Production CasCor checks `best_correlation > 0.0005` before installing (line 2974). The demo has no such guard and blindly installs noise-level candidates. This is the most impactful single change for preventing the degenerative feedback loop.

### Step 6A.5: Xavier-Scale Candidate Weight Initialization ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Line**: ~203 (candidate weight initialization in `add_hidden_unit()`)

**Change**: Scale initialization std by `1/sqrt(input_dim)` instead of fixed 0.1.

```python
# BEFORE:
"weights": torch.randn(input_dim) * TrainingConstants.OUTPUT_WEIGHT_INIT_STD,
"bias": torch.randn(1) * TrainingConstants.OUTPUT_WEIGHT_INIT_STD,
# AFTER:
import math
init_std = 1.0 / math.sqrt(input_dim)
"weights": torch.randn(input_dim) * init_std,
"bias": torch.randn(1) * init_std,
```

**Rationale**: With fixed std=0.1 and growing input_dim (2 + N hidden units), pre-activation variance grows linearly, causing tanh saturation at cascade depth >5. Xavier scaling keeps pre-activation variance approximately constant regardless of depth.

**Tests affected**: Update any test that asserts specific weight initialization magnitudes.

### Step 6A.6: Update Affected Tests ✅

| Test File                                                           | Change                                                                         |
|---------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `test_phase6_implementation.py::test_fresh_optimizer_after_retrain` | Assert optimizer state is NON-empty (warm optimizer retained)                  |
| `test_phase6_implementation.py::test_candidate_gradient_clipping`   | Remove or invert (clipping no longer applied)                                  |
| `test_convergence_ui_controls.py` (if needed)                       | Verify correlation threshold guard integration                                 |
| New: `test_candidate_correlation_guard.py`                          | Test that `add_hidden_unit()` returns None when no candidate exceeds threshold |
| New: `test_candidate_training_steps_stable.py`                      | Test that candidate step counts remain stable across 5 successive units        |

### Files Modified (Phase 6A)

| File                  | Changes                                                                                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `demo_mode.py`        | Delete line 241 (fresh Adam); delete line 298 (grad clipping); change line 303 (early stop delta); add correlation guard in `add_hidden_unit()`; Xavier scaling for candidate init |
| `canopy_constants.py` | Add `MIN_CANDIDATE_CORRELATION = 0.01`; optionally remove `CANDIDATE_GRAD_CLIP_NORM`                                                                                               |
| Test files            | Update/add tests per table above                                                                                                                                                   |

---

## Phase 6B: Evaluate and Decide

After implementing Phase 6A quick wins:

1. **Run the demo on 3-rotation spiral** for 300 epochs. Observe:
   - Does the loss chart show visible improvement after each hidden unit addition?
   - Does accuracy exceed 60% after 10 hidden units?
   - Is the decision boundary becoming visibly non-linear?

2. **Run the demo on 1-rotation spiral** (`n_rotations=1.0` temporarily) for 150 epochs. Observe:
   - Does the loss chart show clear staircase descent?
   - Does accuracy exceed 85% after 5 hidden units?

3. **Decision matrix**:

| Observation                                  | Decision                                                                          |
|----------------------------------------------|-----------------------------------------------------------------------------------|
| 3-rotation shows visible improvement         | Phase 6A sufficient; skip Phase 6C; consider adding `n_rotations` as configurable |
| 1-rotation works but 3-rotation appears flat | Spiral complexity is the visual bottleneck; implement n_rotations parameter       |
| Neither shows improvement                    | Proceed to Phase 6C (structural refactor)                                         |
| Both work but UI freezes during cascade      | Implement Phase 6C.3 (lock granularity) independently                             |

---

## Phase 6C: Structural Refactor (4-8 hours)

**Only implement if Phase 6A quick wins are insufficient.**

This phase restructures the training loop to match the CasCor two-phase specification, eliminates the phantom inter-cascade phase, and resolves the UI lock contention.

### Step 6C.1: Restructure `_training_loop()` to CasCor Specification

**File**: `juniper-canopy/src/demo_mode.py`

Replace the current per-epoch loop with a two-phase CasCor cycle:

```python
def _training_loop(self):
    """CasCor two-phase training loop."""
    # Phase 1: Initial output training (only once, at start)
    for step in range(TrainingConstants.OUTPUT_RETRAIN_STEPS):
        self.network.train_output_step()
        if step % 50 == 0:
            self._emit_progress(step)  # Dashboard update

    # Phase 2: Grow network (cascade additions)
    while not self._stop.is_set():
        if len(self.network.hidden_units) >= self.max_hidden_units:
            break

        # Train candidate pool and get best correlation
        result = self.network.add_hidden_unit()

        if result is None:  # No candidate met correlation threshold
            break  # Network has reached capacity

        # Record and broadcast post-retrain metrics
        self._record_metrics()
        self._broadcast_cascade_event()

        # Check stopping criteria
        if self._check_stopping_criteria():
            break
```

### Step 6C.2: Replace Convergence Detection with Correlation Threshold

Remove `_should_add_cascade_unit()` entirely. The decision to add another unit is made by the correlation threshold in `add_hidden_unit()` (already added in Step 6A.4). If no candidate exceeds the threshold, the network stops growing.

Remove: `convergence_enabled`, `convergence_threshold`, `_cascade_cooldown_remaining`, `cascade_every`.

The convergence UI controls (Phase 5) should be repurposed or removed. The correlation threshold could be the user-facing parameter instead.

### Step 6C.3: Break Lock Granularity

**File**: `juniper-canopy/src/demo_mode.py`

Currently the lock is held for the entire `add_hidden_unit()` call (~20,000 gradient steps). Break into:

1. **Candidate training**: No lock needed (candidate-local state only)
2. **Installation**: Brief lock for appending to `hidden_units` and expanding `output_layer`
3. **Retrain**: Lock per batch of N steps (e.g., every 100 steps), releasing between batches for UI queries

### Step 6C.4: Emit Retrain Progress for Dashboard

During the 1000-step retrain inside `add_hidden_unit()`, emit intermediate progress every 100 steps. The dashboard can show the output layer converging in real-time within each cascade cycle, creating a much richer visualization than the current "freeze then jump" behavior.

### Step 6C.5: Add Cascade Event Markers to Loss Chart

Annotate the loss chart with vertical markers at each cascade addition event, showing "+Unit #N" with the correlation quality. This helps users understand the training dynamics.

### Step 6C.6: Comprehensive Test Suite Update

Add the critical missing test: **`test_end_to_end_training_loop_with_cascade_progression`**

```python
def test_end_to_end_training_loop_with_cascade_progression():
    """The single most important missing test in the suite."""
    demo = DemoMode(...)
    demo.start()

    # Let training run for N cascade additions
    wait_for_condition(lambda: len(demo.network.hidden_units) >= 5, timeout=60)
    demo.stop()

    # Verify loss monotonically decreases at cascade boundaries
    history = demo.network.history["train_loss"]
    # ... assert staircase pattern with each step lower than previous

    # Verify final accuracy exceeds threshold
    assert demo.current_accuracy > 0.70
```

---

## Testing Plan

### New Tests Required (Phase 6A)

| Test                                              | File                            | Description                                                                   |
|---------------------------------------------------|---------------------------------|-------------------------------------------------------------------------------|
| `test_warm_optimizer_retained_after_retrain`      | `test_phase6_implementation.py` | Assert optimizer state is non-empty after `add_hidden_unit()`                 |
| `test_no_candidate_gradient_clipping`             | `test_phase6_implementation.py` | Verify no gradient clipping applied during candidate training                 |
| `test_candidate_early_stop_any_improvement`       | `test_phase6_implementation.py` | Verify patience resets on ANY improvement (no minimum delta)                  |
| `test_correlation_threshold_guard_rejects_weak`   | New file                        | `add_hidden_unit()` returns None when candidates have noise-level correlation |
| `test_correlation_threshold_guard_accepts_strong` | New file                        | `add_hidden_unit()` installs when best candidate exceeds threshold            |
| `test_xavier_scaled_candidate_init`               | `test_phase6_implementation.py` | Verify init std scales as 1/sqrt(input_dim)                                   |
| `test_candidate_quality_stable_across_depth`      | New file                        | Best correlation remains > threshold across 5 successive units                |

### Diagnostic Tests (Phase 6B)

| Test                                        | Purpose                                                                               |
|---------------------------------------------|---------------------------------------------------------------------------------------|
| `test_post_retrain_loss_stability`          | After `add_hidden_unit()`, one `train_output_step()` does NOT increase loss by >0.001 |
| `test_per_unit_improvement_visible`         | On 1-rotation spiral, each unit produces MSE delta > 0.005                            |
| `test_training_stops_when_capacity_reached` | On XOR, training stops adding units after 2-3 (not blindly installing to max)         |

### Integration Tests (Phase 6C)

| Test                                    | Purpose                                                                                        |
|-----------------------------------------|------------------------------------------------------------------------------------------------|
| `test_end_to_end_cascade_progression`   | THE critical missing test: `_training_loop()` produces monotonic loss decrease across 5+ units |
| `test_ui_responsiveness_during_cascade` | `get_current_state()` returns within 200ms even during cascade addition                        |
| `test_retrain_progress_emission`        | WebSocket metrics arrive at ≥1 per 2 seconds during cascade                                    |

---

## Validation Methodology

### Proposal Verification Strategy

| Proposal                | Diagnostic Test                                                     | How to Verify It's Fixed                                            |
|-------------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|
| P1 (Phantom phase)      | Count outer-loop single steps vs retrain steps                      | After 6C.1: no single-step epochs between cascades                  |
| P2 (Convergence timing) | Check convergence window after retrain: is improvement < threshold? | After 6C.2: convergence detection replaced by correlation threshold |
| P3 (Fresh Adam)         | First post-retrain step loss increase > 0.001?                      | After 6A.1: first step loss increase < 0.0001                       |
| P4 (Spiral complexity)  | Per-unit MSE delta on 3-rotation spiral                             | After all fixes: delta > 0.001 per unit consistently                |
| P5 (Candidate decay)    | Candidate step count decreases across depth?                        | After 6A.2-3: step counts stable (< 30% decrease)                   |
| P6 (Correlation guard)  | Noise-level candidates installed?                                   | After 6A.4: candidates below threshold not installed                |
| P7 (UI lock)            | Dashboard freeze > 2 seconds during cascade?                        | After 6C.3: get_current_state() returns within 200ms                |
| P8 (Residual collapse)  | Residual std < 0.01 after 3 units?                                  | After 6A.4: training stops instead of installing noise candidates   |
| P9 (Tanh saturation)    | Hidden unit output variance < 0.001 at depth >5?                    | After 6A.5: variance > 0.01 through depth 15                        |
| P10 (Reset desync)      | Applied params differ from backend after reset?                     | Deferred — edge case                                                |

---

## Audit Trail

### Analysis Methodology

| Phase                         | Agents            | Duration | Focus                                                          |
|-------------------------------|-------------------|----------|----------------------------------------------------------------|
| Phase 1: Codebase Exploration | 2 Explore agents  | ~2 min   | juniper-canopy demo mode, juniper-cascor reference             |
| Phase 2: Deep Analysis        | 4 General agents  | ~4 min   | demo_mode.py, cascor comparison, dashboard/backend, test suite |
| Phase 3: Proposals            | 10 General agents | ~5 min   | 10 independent root cause hypotheses                           |
| Phase 4: Evaluation           | 3 General agents  | ~3 min   | Algorithmic ranking, engineering feasibility, testing strategy |
| Phase 5: Synthesis            | 1 (main thread)   | ~5 min   | Integrated plan with prioritization                            |

### Key Findings Cross-Validated

| Finding                                         | Validated By                                        | Confidence  |
|-------------------------------------------------|-----------------------------------------------------|-------------|
| Phantom phase exists                            | Algorithmic + Engineering agents, code verification | HIGH        |
| Production CasCor has no inter-cascade training | Cascor reference agent, code line citations         | HIGH        |
| Fresh Adam perturbation is ~1000x overshoot     | Math analysis + code verification                   | HIGH        |
| Gradient clipping absent in production CasCor   | Cascor reference agent grep                         | HIGH        |
| Missing correlation threshold guard             | Algorithmic agent grep, production line 2974        | HIGH        |
| 3-rotation spiral needs 10-15 units             | ML expert analysis + theoretical estimates          | MEDIUM-HIGH |
| UI lock held for 20,000 steps                   | Code line 886-904 verification                      | HIGH        |
| No end-to-end training loop test exists         | Test suite agent comprehensive search               | HIGH        |

---

## Audit Results

### Code Verification Audit (2026-03-19)

All line references and code content verified against the actual codebase by a dedicated audit agent.

| Step                         | Line Reference | Content Match                                                                    | Status       |
|------------------------------|----------------|----------------------------------------------------------------------------------|--------------|
| 6A.1 (fresh Adam)            | Line 241       | Exact match: `self.output_optimizer = torch.optim.Adam(...)`                     | **VERIFIED** |
| 6A.2 (grad clipping)         | Line 298       | Exact match: `torch.nn.utils.clip_grad_norm_(...)`                               | **VERIFIED** |
| 6A.3 (early stop delta)      | Line 303       | Exact match: `if abs_corr > best_correlation + 1e-6:`                            | **VERIFIED** |
| 6A.4 (correlation guard)     | Line 887       | Call location verified; lock context integration updated                         | **VERIFIED** |
| 6A.5 (Xavier init)           | Lines 203-204  | Exact match: `torch.randn(input_dim) * TrainingConstants.OUTPUT_WEIGHT_INIT_STD` | **VERIFIED** |
| Constants (all 7)            | Lines 63-69    | All values match plan                                                            | **VERIFIED** |
| `_should_add_cascade_unit()` | Lines 768-802  | Behavior matches description                                                     | **VERIFIED** |
| `_training_loop()` cascade   | Lines 883-911  | Lock scope matches description                                                   | **VERIFIED** |

### Issues Found and Resolved

| # | Issue                                                                     | Resolution                                                                             |
|---|---------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| 1 | Step 6A.4 code snippet didn't account for `with self._lock:` context      | Updated plan with correct lock-aware integration pattern                               |
| 2 | `add_hidden_unit()` docstring says "500 steps" but constant is 1000       | Pre-existing stale docstring; noted for cleanup during implementation                  |
| 3 | `OUTPUT_WEIGHT_INIT_STD` also used at line 231 for output layer expansion | Intentionally left at 0.1 for output expansion (different concern from candidate init) |
| 4 | Test class names slightly differ from plan references                     | Noted as minor naming discrepancy; test intent is correctly identified                 |

### Audit Conclusion

The plan is **highly accurate**. All proposed changes target the correct lines with the correct content. The one substantive integration issue (lock context for Step 6A.4) has been resolved in the plan. The plan is ready for implementation.

---

## Document History

| Date       | Author      | Change                                                                                                |
|------------|-------------|-------------------------------------------------------------------------------------------------------|
| 2026-03-19 | Paul Calnon | Initial creation — comprehensive 10-proposal analysis, 3-evaluator synthesis, phased remediation plan |
| 2026-03-19 | Paul Calnon | Audit complete — all line references verified; Step 6A.4 lock context integration updated |
| 2026-03-19 | Paul Calnon | Phase 6A implemented — 5 code changes + 6 new tests + 3 test updates. 3617/3617 passing (19 skipped) |
