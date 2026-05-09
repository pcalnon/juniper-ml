# CasCor Demo Training Stall — Comprehensive Analysis

**Project**: Juniper Ecosystem (juniper-canopy + juniper-cascor)
**Created**: 2026-03-19
**Author**: Paul Calnon (via Claude Code)
**Status**: Analysis Complete
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor reference)

---

## Background

Despite extensive remediation through Phases 1-5.2 of the CASCOR_DEMO_TRAINING_ERROR_PLAN, the juniper-canopy demo mode neural network training continues to exhibit stalling behavior after the first hidden node is added. This document presents a comprehensive multi-agent analysis of the remaining root causes.

## Prior Work Summary

Phases 1-5.2 resolved the following issues:

| Phase     | Fixes Applied                                                                                                  | Status   |
|-----------|----------------------------------------------------------------------------------------------------------------|----------|
| Phase 1   | Sigmoid→Tanh activation, BCE→MSE loss, increased retrain steps, tanh derivative, candidate pool                | Complete |
| Phase 2   | Candidate pool selection, correlation return, convergence-based addition                                       | Complete |
| Phase 4   | nn.Linear+Adam, autograd+Pearson correlation, input normalization, full-batch training, 500→1000 retrain steps | Complete |
| Phase 5   | Convergence UI controls (checkbox + threshold)                                                                 | Complete |
| Phase 5.1 | Bugfix: removed continuous backend sync, split Training Controls card                                          | Complete |
| Phase 5.2 | Bugfix: /api/state convergence params, one-shot init, status message preservation                              | Complete |

## Current Codebase State

### Architecture Match (Post-Phase 4)

| Aspect                    | Demo Mode                         | Production CasCor         | Match?   |
|---------------------------|-----------------------------------|---------------------------|----------|
| Hidden activation         | torch.tanh [-1, 1]                | nn.Tanh [-1, 1]           | Yes      |
| Output activation         | Raw linear (nn.Linear)            | Raw linear (nn.Linear)    | Yes      |
| Loss function             | MSE (nn.MSELoss) + autograd       | MSE (nn.MSELoss)          | Yes      |
| Output optimizer          | Adam (lr=0.01)                    | Adam (lr=0.01)            | Yes      |
| Fresh optimizer per phase | Yes (new Adam after each install) | Yes                       | Yes      |
| Candidate correlation     | Pearson (normalized)              | Pearson (normalized)      | Yes      |
| Input normalization       | Min-max to [-1, 1]                | None (smaller-range data) | Yes      |
| Output retrain steps      | 1000                              | 1000                      | Yes      |
| Candidate pool size       | 32                                | 16                        | Exceeded |
| Candidate training steps  | 600 (with patience=30)            | Configurable              | Exceeded |

### Current Training Constants (canopy_constants.py)

| Constant                      | Value |
|-------------------------------|-------|
| CASCADE_COOLDOWN_EPOCHS       | 50    |
| CANDIDATE_POOL_SIZE           | 32    |
| CANDIDATE_TRAINING_STEPS      | 600   |
| CANDIDATE_PATIENCE            | 30    |
| OUTPUT_RETRAIN_STEPS          | 1000  |
| OUTPUT_WEIGHT_INIT_STD        | 0.1   |
| DEFAULT_CONVERGENCE_THRESHOLD | 0.001 |
| DEFAULT_CONVERGENCE_ENABLED   | True  |
| CANDIDATE_GRAD_CLIP_NORM      | 5.0   |

### Key Confirmed Non-Issues

| Item                            | Status  | Details                                       |
|---------------------------------|---------|-----------------------------------------------|
| MSE gradient math               | Correct | All formulas verified                         |
| Tanh derivative                 | Correct | 1 - v*v is standard                           |
| Hidden weight freezing          | Working | No code path modifies frozen weights          |
| Output weight expansion         | Correct | Old weights properly preserved via warm-start |
| Forward pass cascade            | Correct | All hidden units included during retrain      |
| Feature concatenation           | Correct | [x, h0, h1, ...] order is consistent          |
| Input normalization             | Applied | Min-max to [-1, 1] at dataset load            |
| Decision boundary normalization | Applied | Grid normalized before forward()              |

---

## Critical Finding: Structural Mismatch with CasCor Algorithm

The most significant finding from the analysis is that the demo's training loop architecture is **fundamentally different** from the CasCor algorithm specification:

### Production CasCor: Two-Phase Loop (No Inter-Cascade Training)

```bash
grow_network():
    for epoch in range(max_epochs):
        1. Compute residual error
        2. Train candidate pool against residual
        3. If best_correlation < threshold: STOP
        4. Install best candidate, retrain output (1000 epochs)
        5. Check early stopping
        # NOTE: No inter-cascade training — goes directly back to step 1
```

### Demo Mode: Three-Phase Loop (Phantom Inter-Cascade Phase)

```bash
_training_loop():
    while not stopped:
        1. One gradient step on output layer          ← PHANTOM PHASE
        2. Record metrics, increment epoch
        3. Check _should_add_cascade_unit():
           - If cooldown > 0: decrement, skip
           - If convergence: loss plateau detected → add unit
           - Fallback: fixed schedule every 30 epochs
        4. If adding: add_hidden_unit() (1000-step retrain internally)
        5. Set cooldown = 50 epochs
        6. Wait 1 second, loop to step 1
```

The "phantom phase" (step 1 repeated 50+ times between cascade additions) is the central problem. The 1000-step retrain inside `add_hidden_unit()` already converges the output layer. The subsequent 50 single-step epochs are provably unproductive on an already-converged convex surface.

---

## Identified Root Causes (New, Post-Phase 4)

### RC-P1 (CRITICAL): Phantom Inter-Cascade Training Phase

The demo invented a per-epoch outer training loop that doesn't exist in the CasCor algorithm. Each "visual epoch" performs 1 gradient step on an already-converged output layer, producing negligible loss change that the convergence detector correctly identifies as stagnation.

### RC-P2 (CRITICAL): Cascade Addition Timing Driven by Convergence-on-Converged

The convergence detector evaluates 10 epochs of post-retrain single-step training. Since the retrain already found the optimum, these 10 epochs show < 0.001 improvement, always triggering another cascade addition. The detector is correct — but it's detecting an artificial stagnation caused by the phantom phase.

### RC-P3 (HIGH): Fresh Adam Optimizer Perturbs Converged Weights

Line 241 creates a fresh Adam optimizer after the 1000-step retrain. Adam's bias correction ensures the first step has effective lr = 0.01 regardless of gradient magnitude, perturbing carefully converged weights by a fixed amount.

### RC-P4 (HIGH): 3-Rotation Spiral Complexity vs. Per-Unit Visibility

The default spiral dataset uses 3 rotations (6 boundary crossings), requiring 10-15 hidden units for good classification. Per-unit MSE improvement is ~0.001-0.003, which is sub-pixel on the default chart scale.

### RC-P5 (HIGH): Candidate Quality Degradation

Gradient clipping (max_norm=5.0) and aggressive early stopping threshold (best + 1e-6) are not present in the production CasCor. These cause premature termination of candidate training when residuals are small.

### RC-P6 (HIGH): No Correlation Threshold Guard

The demo always installs the best candidate regardless of correlation quality. The production CasCor checks `best_correlation > 0.0005` before installing. Without this guard, useless candidates are installed, wasting network capacity.

### RC-P7 (HIGH): UI Lock Held During Entire add_hidden_unit()

The training lock is held for ~20,000 gradient steps (32 candidates × 600 steps + 1000 retrain), blocking all UI updates for 5-20 seconds during each cascade addition.

### RC-P8 (MODERATE): Residual Variance Collapse

As the network improves, the residual becomes small and concentrated on boundary samples. Pearson correlation's numerical conditioning degrades, and candidate correlations approach noise level.

### RC-P9 (MODERATE): Tanh Saturation from Growing Input Dimension

Weight initialization (randn × 0.1) is fixed regardless of input dimension. As cascade depth grows, pre-activation magnitudes increase, leading to tanh saturation and constant hidden unit outputs.

### RC-P10 (LOW): Post-Reset Parameter Desynchronization

After training reset, backend convergence parameters revert to defaults while UI retains stale "applied" values. The one-shot init callback doesn't re-fire.

---

## Test Suite Gaps

| Gap                                                                            | Impact                                  |
|--------------------------------------------------------------------------------|-----------------------------------------|
| No test exercises `_training_loop()` end-to-end with cascade addition          | Tests bypass the phantom phase entirely |
| No test runs > 2 hidden unit additions with continued improvement verification | Stall after unit 2+ is untested         |
| Tests call `add_hidden_unit()` + `train_output_step()` directly (100+ steps)   | Masks the 1-step-per-epoch behavior     |
| `test_loss_is_mse_not_bce` is tautological (compares value to itself)          | Provides false confidence               |
| No integration test verifies final accuracy target on spiral dataset           | Training quality is unverified          |
| No test verifies candidate correlation quality across successive units         | Degradation goes undetected             |

---

## Analysis Methodology

This analysis was performed by 4 specialized sub-agents in parallel:

1. **Demo Engine Agent**: Deep analysis of demo_mode.py current implementation
2. **CasCor Reference Agent**: Comparative analysis with production cascade_correlation.py
3. **Dashboard/Backend Agent**: UI callbacks, parameter flow, thread safety
4. **Test Suite Agent**: Coverage gaps, false positives, missing regression tests

Findings were cross-referenced across all agents for consistency.
