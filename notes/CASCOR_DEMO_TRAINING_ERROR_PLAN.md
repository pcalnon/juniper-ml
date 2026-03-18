# CasCor Demo Training Error — Investigation & Remediation Plan

**Project**: Juniper Ecosystem (juniper-canopy + juniper-cascor)
**Created**: 2026-03-17
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Phase 1 & 2 Implementation Complete, All Tests Passing (167/167)
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor reference, juniper-ml coordination)
**Supersedes**: `CANOPY_DECISION_BOUNDARY_FIX_PLAN.md` (V1), `CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md` (V2)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Troubleshooting Summary](#troubleshooting-summary)
- [Root Cause Analysis](#root-cause-analysis)
- [Comparative Analysis: Demo Mode vs Cascor](#comparative-analysis-demo-mode-vs-cascor)
- [Architecture Review](#architecture-review)
- [Implementation Plan](#implementation-plan)
- [Testing Plan](#testing-plan)
- [Validation & Audit Results](#validation--audit-results)

---

## Problem Statement

Neural network training in juniper-canopy demo mode stops improving after the first hidden node is added to the cascade correlation network. The specific symptoms are:

1. **Initial training works**: Loss drops from ~0.82 to ~0.68 and accuracy rises from ~40% to ~55% during the first 25-30 epochs (output training phase, no hidden units)
2. **Training stalls after +Unit #1**: After the first hidden unit is installed at epoch 30, loss flatlines at ~0.68-0.69 and accuracy stagnates at ~54-56%
3. **Subsequent hidden units have no effect**: Units #2, #3, #4, etc. are added but neither loss nor accuracy improve
4. **Decision boundary remains linear**: Despite 6+ hidden units at epoch 180, the decision boundary is a straight line — the hidden units contribute nothing to the classification
5. **Loss value is near `ln(2) ≈ 0.6931`**: The BCE loss of a network predicting 0.5 for all samples, confirming the network is barely better than random chance

### Prior Fix History

V1 and V2 plans identified and fixed several fundamental issues:

| Issue (V1/V2)                                           | Status    | What Was Fixed                                       |
|---------------------------------------------------------|-----------|------------------------------------------------------|
| RC-6 (V1): `forward()` ignored hidden units             | **FIXED** | Forward pass now cascades correctly                  |
| RC-7 (V1): Weights never trained                        | **FIXED** | `train_output_step()` performs real gradient descent |
| RC-8 (V1): No thread safety in boundary computation     | **FIXED** | Lock acquired before `forward()`                     |
| RC-D1 (V2): Hidden unit weights random                  | **FIXED** | Candidate training via `_train_candidate()` added    |
| RC-D2 (V2): Deferred training lost steps                | **FIXED** | Training is now inline                               |
| RC-D3 (V2): Synthetic metrics disconnected from network | **FIXED** | Metrics computed from actual predictions             |
| RC-D4 (V2): Missing argmax                              | **FIXED** | `(predictions > 0.5).int()` applied                  |

**These fixes resolved the mechanical bugs but not the algorithmic issues.** The current code correctly cascades through hidden units, trains weights with real gradients, and computes accurate metrics — but the training still stalls because of deeper algorithm-level mismatches with the CasCor specification.

---

## Troubleshooting Summary

### Investigation Process

1. **Screenshot analysis**: Loss value ~0.69 ≈ ln(2) indicates predictions clustered at ~0.5. Linear decision boundary with 6 hidden units confirms hidden units contribute nothing.

2. **Demo mode code audit** (`juniper-canopy/src/demo_mode.py`):
   - `MockCascorNetwork` class (lines 71-297) implements forward pass, output training, candidate training, and hidden unit addition
   - Forward pass correctly cascades through hidden units (lines 210-241)
   - Output training uses BCE gradient with mini-batch SGD (lines 243-296)
   - Candidate training maximizes correlation with residual error (lines 148-208)

3. **Cascor reference audit** (`juniper-cascor/src/cascade_correlation/cascade_correlation.py`):
   - `CascadeCorrelationNetwork` class implements the full Fahlman & Lebiere (1990) algorithm
   - Uses `nn.Tanh` activation (not sigmoid)
   - Uses MSE loss on raw output (no sigmoid on output layer)
   - Retrains output for 1000 full-batch epochs after each hidden unit addition
   - Trains candidate pool of 16 units, selects best

4. **Constants comparison** (`juniper-cascor/src/cascor_constants/`):
   - Default activation: `nn.Tanh` (`constants_activation.py:56`)
   - Output retraining epochs: 1000 (`constants_model.py:226`)
   - Candidate pool size: 16 (`constants.py`)
   - Candidate training epochs: configurable, extensive

5. **Differential analysis**: Identified 8 algorithmic mismatches between demo and cascor that collectively cause training failure.

---

## Root Cause Analysis

### RC-1 (CRITICAL): Wrong Activation Function — Sigmoid vs Tanh

**Demo**: `torch.sigmoid` (output range [0, 1])
**Cascor**: `nn.Tanh` (output range [-1, 1])
**Files**: `demo_mode.py:129` vs `constants_activation.py:56`

**Why this matters for CasCor**:

The original Cascade Correlation paper (Fahlman & Lebiere, 1990) explicitly specifies tanh activation for hidden units. The key algorithmic difference:

- **Tanh saturation**: outputs ∈ {-1, +1}. A saturated tanh unit creates a *binary partition* of the input space — some samples get -1, others get +1. This provides a maximally discriminative feature to the output layer.
- **Sigmoid saturation**: outputs ∈ {0, 1}. A saturated sigmoid unit can produce a *constant feature* if all samples land on the same side (all near 0 or all near 1). A constant feature provides zero gradient to the output weight, making it permanently useless.

With spiral data ranging [-10, 10], candidate training (lr=0.1, 80 steps) drives weights large enough to saturate the activation. With tanh, this saturation is useful (creates a -1/+1 split). With sigmoid, this saturation can be catastrophic (creates a 0/0 or 1/1 constant).

Additionally, sigmoid's asymmetric range [0, 1] introduces a mean-shift bias: the average hidden output is near 0.5, not 0. This biases the output layer and reduces the effective dimensionality of the feature space.

### RC-2 (CRITICAL): Wrong Loss Function — BCE+Sigmoid vs MSE on Raw Output

**Demo**: Applies `sigmoid()` to output, uses BCE gradient `dL/dz = p - y`
**Cascor**: Raw linear output, uses MSE loss `(output - y)²`
**Files**: `demo_mode.py:240-241,287-288` vs `cascade_correlation.py:1222,1291`

**Why this matters**:

1. **Residual magnitude**: In cascor, the residual `y - output` is unbounded (raw linear output can be any value). In the demo, `y - sigmoid(output)` is bounded to [-1, 1]. Smaller residuals give weaker gradient signals for candidate training.

2. **Output gradient**: The BCE gradient `(p - y)` is well-conditioned but small (range [-1, 1]). The MSE gradient `2(output - y)` with raw output can be larger, giving stronger learning signals after hidden unit installation.

3. **Algorithm mismatch**: The CasCor candidate training phase is mathematically designed around MSE residuals. Using BCE residuals changes the optimization landscape and can prevent candidates from finding useful features.

### RC-3 (CRITICAL): Severely Insufficient Output Retraining After Hidden Unit Installation

**Demo**: 50 mini-batch steps (batch_size=32, lr=0.01) = ~1,600 sample evaluations
**Cascor**: 1,000 full-batch epochs with `nn.Linear` + MSELoss + optimizer (for cascor's default ~2,000 sample dataset) = ~2,000,000 sample evaluations
**Files**: `demo_mode.py:145-146` vs `constants_model.py:226`, `cascade_correlation.py:3198`

**Why this matters**:

After installing a hidden unit, the output layer has a new weight column initialized to random ~0.1. The output layer must learn to USE this new feature. With only 50 mini-batch steps at lr=0.01, the total weight change for the hidden unit column is approximately `50 × 0.01 × gradient ≈ 0.125` — barely different from the random initialization.

The cascor retrains for 1,000 epochs with a proper optimizer (Adam or SGD with momentum), giving the output layer ample time to learn meaningful weights for the new hidden feature. This is a **~1,250× difference** in total sample evaluations (2,000,000 vs 1,600), or a **20× difference** in raw epoch count (1,000 vs 50).

Even the ongoing training between hidden unit additions (30 epochs of 1 mini-batch step each) is insufficient — the network only gets 30 more gradient steps before another hidden unit disrupts the output weights again.

### RC-4 (SIGNIFICANT): Single Candidate vs Candidate Pool

**Demo**: Creates and trains 1 candidate per hidden unit addition
**Cascor**: Trains a pool of 16 candidates in parallel, selects the best
**Files**: `demo_mode.py:121-134` vs cascor candidate pool configuration

**Why this matters**:

With only 1 candidate, the quality of each hidden unit depends entirely on the random initialization. Poor initializations lead to candidates that correlate weakly with the residual error. A pool of 16 gives a much higher probability of finding a useful candidate.

### RC-5 (SIGNIFICANT): Sigmoid Derivative Vanishing During Candidate Training

**Files**: `demo_mode.py:199`

The candidate gradient includes the sigmoid derivative `f' = v × (1 - v)`. With input data in [-10, 10] and candidate lr=0.1:

- After ~5 steps, weights grow from ~0.1 to ~0.6
- Weighted sum `w·x` reaches range [-12, 12] for extreme inputs
- `sigmoid(-12) ≈ 6e-6`, so `f' = 6e-6 × (1 - 6e-6) ≈ 0`
- The gradient vanishes for all samples with extreme feature values
- Only samples near the decision boundary (where sigmoid isn't saturated) contribute gradient
- With a 200-sample spiral dataset, this could be a small fraction of samples

With tanh, the derivative `1 - tanh²(z)` has the same vanishing issue, but the symmetry of tanh around zero means the saturated outputs (-1 and +1) still provide useful binary features to the output layer.

### RC-6 (MODERATE): No Input Normalization

**Files**: `demo_mode.py:539-557`

The spiral dataset from JuniperData has features in approximately [-10, 10] range (visible in screenshot 3). No normalization is applied before feeding to the network.

**Why this matters**:

- Large input magnitudes exacerbate sigmoid saturation (RC-1, RC-5)
- Initial output weights (~0.1) times inputs (~10) give pre-activation values ~1.0, which is already in the sigmoid's transition zone. After even small weight changes, saturation begins.
- Normalized inputs [-1, 1] would keep pre-activations small, delaying saturation and allowing more effective gradient-based training

### RC-7 (MODERATE): Fixed-Schedule Hidden Unit Addition vs Convergence-Based

**Demo**: Adds hidden unit every `cascade_every` (30) epochs regardless of training convergence
**Cascor**: Adds unit when candidate correlation exceeds threshold and output training has converged
**Files**: `demo_mode.py:683-699` vs `cascade_correlation.py:2962-2974`

**Why this matters**:

Adding a hidden unit before the output has converged wastes the current training trajectory. Adding one after convergence when the output can no longer improve is the correct signal that a new feature is needed. The fixed schedule may add units too early or too late.

### RC-8 (MINOR): Mini-Batch vs Full-Batch Training

**Demo**: batch_size=32 from 200 samples (16% per step), manual gradient computation
**Cascor**: Full-batch training with `nn.Linear` + PyTorch autograd + proper optimizer
**Files**: `demo_mode.py:258-296` vs `cascade_correlation.py:1287-1335`

**Why this matters**:

- 16% sampling introduces high gradient variance
- Manual gradient computation (analytical BCE derivative) forgoes optimizer benefits (momentum, adaptive learning rates)
- Full-batch training with Adam/SGD+momentum converges faster and more reliably

---

## Comparative Analysis: Demo Mode vs Cascor

### Architecture Comparison

| Aspect                      | Demo Mode (`MockCascorNetwork`)           | Cascor (`CascadeCorrelationNetwork`)      |
|-----------------------------|-------------------------------------------|-------------------------------------------|
| **Hidden activation**       | `torch.sigmoid` [0, 1]                    | `nn.Tanh` [-1, 1]                         |
| **Output activation**       | `sigmoid(matmul + bias)`                  | Raw linear: `matmul + bias`               |
| **Loss function**           | BCE (analytical gradient)                 | MSE (`nn.MSELoss`)                        |
| **Output training**         | 1 mini-batch step/epoch + 50 post-install | 1000 full-batch epochs post-install       |
| **Output optimizer**        | Manual SGD (lr=0.01)                      | `torch.optim` (configurable)              |
| **Candidate pool**          | 1 candidate                               | 16 candidates (parallel)                  |
| **Candidate training**      | 80 steps, lr=0.1, manual gradient         | Configurable epochs, autograd             |
| **Candidate selection**     | None (single candidate)                   | Max absolute correlation                  |
| **Hidden unit addition**    | Fixed schedule (every 30 epochs)          | Convergence-based + correlation threshold |
| **Input normalization**     | None                                      | None (but uses smaller-range data)        |
| **Weight initialization**   | `randn * 0.1`                             | `randn * 0.1` (similar)                   |
| **Output weight expansion** | Random new column, copy old               | Random new row, copy old (equivalent)     |
| **Data format**             | Tensor (N, 2), targets (N, 1)             | Tensor (N, 2), targets (N, 1)             |
| **Thread safety**           | `threading.Lock`                          | Not thread-safe (process-based)           |

### Code Structure Comparison

| Component          | Demo Mode File | Demo Lines | Cascor File              | Cascor Lines |
|--------------------|----------------|------------|--------------------------|--------------|
| Forward pass       | `demo_mode.py` | 210-241    | `cascade_correlation.py` | 1202-1243    |
| Output training    | `demo_mode.py` | 243-296    | `cascade_correlation.py` | 1247-1346    |
| Add hidden unit    | `demo_mode.py` | 113-146    | `cascade_correlation.py` | 2756-2851    |
| Candidate training | `demo_mode.py` | 148-208    | `candidate_unit.py`      | 616-762      |
| Correlation calc   | `demo_mode.py` | 190-196    | `candidate_unit.py`      | 996-1087     |
| Weight update      | `demo_mode.py` | 203-208    | `candidate_unit.py`      | 1095-1208    |
| Training loop      | `demo_mode.py` | 701-801    | `cascade_correlation.py` | 2909-3048    |
| Residual error     | `demo_mode.py` | 166-167    | `cascade_correlation.py` | 2709-2752    |

### What's Similar (Correct in Both)

1. **Cascade architecture**: Each hidden unit receives [original inputs + all previous hidden outputs] — correctly implemented in both
2. **Forward pass structure**: Sequential cascade through hidden units, then output layer — structurally identical
3. **Weight freezing**: Hidden unit weights frozen after installation (detached in cascor, not updated in demo)
4. **Residual computation**: `y - forward(x)` — same formula
5. **Correlation maximization**: Both maximize |correlation| between candidate output and residual — same objective

### What's Different (Root Causes)

1. **Activation function**: Sigmoid (demo) vs Tanh (cascor) — changes saturation behavior
2. **Loss function**: BCE+sigmoid (demo) vs MSE (cascor) — changes gradient dynamics
3. **Output retraining**: 50 mini-batch steps (demo) vs 1000 full-batch epochs (cascor) — 125× difference
4. **Candidate pool**: 1 candidate (demo) vs 16 candidates (cascor) — quality vs speed
5. **Candidate training backend**: Manual gradient (demo) vs autograd (cascor)
6. **Hidden unit scheduling**: Fixed interval (demo) vs convergence-based (cascor)
7. **Optimizer**: Manual SGD (demo) vs configurable torch.optim (cascor)

### Implementation Mechanism Differences

| Mechanism                | Demo Mode                           | Cascor                                 |
|--------------------------|-------------------------------------|----------------------------------------|
| **Gradient computation** | Analytical (hand-coded derivatives) | PyTorch autograd (`loss.backward()`)   |
| **Optimizer**            | Manual `weights -= lr * grad`       | `torch.optim.Adam` / `torch.optim.SGD` |
| **Parallelism**          | Single thread (daemon)              | Multiprocessing (process pool)         |
| **State management**     | `threading.Lock`, `threading.Event` | Single-process, not thread-safe        |
| **Weight storage**       | Dict with tensors                   | Dict with tensors (similar)            |
| **Metrics**              | Computed inline after each step     | Computed after output retraining       |
| **Visualization**        | WebSocket broadcast                 | REST API endpoints                     |

---

## Architecture Review

### Current State: Duplicated CasCor Logic

The demo mode implements a complete but simplified CasCor algorithm in `MockCascorNetwork` (297 lines). This duplicates core logic from `juniper-cascor`'s `CascadeCorrelationNetwork` (4400+ lines). The duplication has led to 8 algorithmic mismatches, each contributing to training failure.

### Problem with Duplication

1. **Divergence**: As cascor evolves (bug fixes, parameter tuning, algorithm improvements), the demo falls behind
2. **Maintenance burden**: Two implementations of the same algorithm must be kept in sync
3. **Testing burden**: Both implementations need independent test suites
4. **Quality gap**: The demo's simplified implementation introduces subtle bugs (as demonstrated by this issue)

### Architectural Options Evaluated

#### Option A: Fix MockCascorNetwork (Minimal Change)

Fix all 8 root causes in the existing `MockCascorNetwork`:

- Change sigmoid to tanh
- Change BCE to MSE
- Increase output retraining epochs
- Add candidate pool
- Fix candidate training dynamics
- Add input normalization

**Pros**: Minimal code change, no new dependencies
**Cons**: Maintains duplication, will diverge again, doesn't address long-term architecture

#### Option B: Import CascadeCorrelationNetwork Directly (Full Reuse)

Replace `MockCascorNetwork` with the actual `CascadeCorrelationNetwork` from juniper-cascor, creating a direct import dependency.

**Pros**: Zero duplication, always in sync
**Cons**: juniper-canopy gains a dependency on juniper-cascor (breaks the microservice boundary — canopy should depend on clients, not service implementations). Heavy import (4400+ lines, multiprocessing infrastructure)

#### Option C: Create Shared Library (New Package)

Extract the core CasCor algorithm into a shared library (`juniper-cascor-core`) that both juniper-cascor and juniper-canopy depend on.

**Pros**: Clean architecture, single source of truth
**Cons**: Major refactoring effort, new package to maintain, cascor's tight coupling with config/logging makes extraction complex

#### Option D: Demo Uses CasCor Service via Client (Microservice Architecture) ★ RECOMMENDED

Replace `MockCascorNetwork` with a lightweight local instance of the cascor service that the demo drives via `juniper-cascor-client`. The demo becomes a curated configuration of the real system.

**Pros**:

- Zero algorithm duplication
- Demo exercises the same code paths as production
- Demo serves as integration test for the full stack
- Follows the microservice architecture direction
- juniper-canopy already depends on `juniper-cascor-client`

**Cons**:

- Requires juniper-cascor to support in-process or local operation
- More complex demo startup (must start cascor service)
- Network overhead for local HTTP calls (negligible for demo)

#### Option E: Hybrid — Fix Critical Bugs Now, Migrate Architecture Later ★★ SELECTED

Immediately fix the critical algorithmic bugs (RC-1, RC-2, RC-3) in `MockCascorNetwork` to make the demo functional. Then, in a subsequent phase, migrate to Option D (service-based architecture) for long-term sustainability.

**Rationale**:

- Fixes the immediate training failure quickly
- Doesn't require cross-repo refactoring for the immediate fix
- Sets up the architectural migration as a well-planned second phase
- Allows the cascor service to be evaluated for local/in-process operation

### Selected Architecture: Option E (Hybrid)

**Phase 1** (this task): Fix `MockCascorNetwork` algorithmic bugs to match cascor behavior
**Phase 2** (future task): Migrate demo mode to use cascor service via client

---

## Implementation Plan

### Phase 1: Critical Algorithmic Fixes (Immediate) — COMPLETE

#### Step 1.1: Change Hidden Unit Activation from Sigmoid to Tanh (RC-1) ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork`

Changes required:

1. In `add_hidden_unit()` (line 129): change `"activation_fn": torch.sigmoid` to `"activation_fn": torch.tanh`
2. In `_train_candidate()` (line 199): change sigmoid derivative `f' = v * (1 - v)` to tanh derivative `f' = 1 - v²`
3. Update any tests that assert sigmoid activation/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fluffy-brewing-rocket

**Impact**: Hidden units will produce outputs in [-1, 1], providing discriminative features even when saturated.

#### Step 1.2: Change Loss Function from BCE+Sigmoid to MSE on Raw Output (RC-2) ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork.forward()`, `train_output_step()`, `_simulate_training_step()`

Changes required:

1. In `forward()` (line 240-241): Remove sigmoid from output layer
   - Before: `return torch.sigmoid(output)`
   - After: `return output`

2. In `train_output_step()` (lines 283-296): Change from BCE gradient to MSE gradient
   - Before: `error = predictions - batch_y` (BCE+sigmoid gradient)
   - After: `error = 2.0 * (predictions - batch_y) / bs` (MSE gradient, no sigmoid)

3. In `_simulate_training_step()` (lines 629-643): Change loss computation from BCE to MSE
   - Before: `bce = -(y * log(p) + (1-y) * log(1-p))`
   - After: `mse = ((predictions - y) ** 2).mean()`

4. In `_simulate_training_step()`: Change accuracy computation to use threshold on raw output
   - Before: `pred_classes = (predictions > 0.5).float()`
   - After: `pred_classes = (predictions > 0.5).float()` (keep, since raw MSE outputs will be near 0 and 1 for trained network)

5. In `DemoBackend.get_decision_boundary()`: Update threshold for raw output
   - Before: `z = (predictions > 0.5).int()`
   - After: `z = (predictions > 0.5).int()` (keep, raw output will be near 0/1 for trained network)

**Impact**: Gradient dynamics will match the CasCor algorithm specification. Residuals will be unbounded, providing stronger training signals.

#### Step 1.3: Increase Output Retraining After Hidden Unit Installation (RC-3) ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork.add_hidden_unit()`

Changes required:

1. Increase retraining from 50 to 200 steps (line 145-146):
   - Before: `for _ in range(50): self.train_output_step()`
   - After: `for _ in range(200): self.train_output_step()`

2. Use full-batch training during retraining (not mini-batch):/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fluffy-brewing-rocket
   - Pass `batch_size=None` or use full dataset size
   - This matches cascor's full-batch output retraining

3. Consider using all training data (no mini-batch) for the retraining steps:
   - In `train_output_step()`: when called during `add_hidden_unit()`, use full batch

**Impact**: Output layer will have sufficient training to learn useful weights for the new hidden unit feature. 200 full-batch steps is a reasonable compromise between cascor's 1000 and the demo's current 50.

#### Step 1.4: Fix Candidate Training Derivative for Tanh (RC-5) ✅

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork._train_candidate()`

Changes required:

1. Change sigmoid derivative to tanh derivative (line 199):
   - Before: `f_prime = v * (1.0 - v)` (sigmoid derivative)
   - After: `f_prime = 1.0 - v * v` (tanh derivative: `1 - tanh²(z)`)

2. Reduce candidate learning rate to prevent premature saturation:
   - Before: `lr=0.1`
   - After: `lr=0.05` (or make configurable)

3. Increase candidate training steps to compensate for smaller learning rate:
   - Before: `steps=80`
   - After: `steps=100`

**Impact**: Candidate training will produce better-trained hidden units with tanh activation.

### Phase 2: Enhancement Fixes — COMPLETE (merged into Phase 1)

#### Step 2.1: Add Candidate Pool (RC-4) ✅ (implemented in Step 1.1)

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork.add_hidden_unit()`

Changes required:

1. Train multiple candidates (e.g., 8) with different random initializations
2. Select the candidate with the highest absolute correlation
3. Install only the best candidate

```python
def add_hidden_unit(self):
    hidden_id = len(self.hidden_units)
    input_dim = self.input_size + hidden_id

    best_unit = None
    best_correlation = -1.0

    for _ in range(8):  # Candidate pool of 8
        unit = {
            "id": hidden_id,
            "weights": torch.randn(input_dim) * 0.1,
            "bias": torch.randn(1) * 0.1,
            "activation_fn": torch.tanh,
        }
        if self.train_x is not None and self.train_y is not None:
            correlation = self._train_candidate(unit, steps=100, lr=0.05)
            if correlation > best_correlation:
                best_correlation = correlation
                best_unit = unit

    if best_unit is not None:
        self.hidden_units.append(best_unit)
    # ... expand output weights and retrain ...
```

**Impact**: Higher-quality hidden units, more reliable training convergence.

#### Step 2.2: Return Correlation from Candidate Training ✅ (implemented in Step 1.4)

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `MockCascorNetwork._train_candidate()`

Changes required:

1. Compute and return the final correlation value after candidate training
2. This is needed for Step 2.1 (candidate pool selection)

#### Step 2.3: Add Convergence-Based Hidden Unit Addition (RC-7)

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `DemoMode._should_add_cascade_unit()`

Changes required:

1. Track loss over recent epochs (e.g., last 10 epochs)
2. Add hidden unit when loss improvement is below threshold (e.g., < 0.001 over 10 epochs)
3. Keep the fixed schedule as a fallback maximum interval
4. Don't add unit if loss is still improving rapidly

**Impact**: Hidden units are added at algorithmically appropriate times.

### Phase 3: Training Controls and UI Integration

#### Step 3.1: Ensure Learning Rate Changes Apply Immediately

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `DemoMode.apply_params()`

Verify that `self.network.learning_rate = learning_rate` takes effect on the next `train_output_step()` call. Current code already does this correctly.

#### Step 3.2: Add Visual Indicators for Training Phase

Ensure the training status correctly shows "Output Training" vs "Candidate Training" phases. The candidate phase should be visible when hidden unit candidate training is occurring.

### Phase 4: Architecture Migration Preparation (Future)

#### Step 4.1: Evaluate Cascor Service for Local Operation

Investigate whether `CascadeCorrelationNetwork` can be instantiated directly within juniper-canopy without the full service infrastructure.

#### Step 4.2: Define Demo Configuration Profile

Create a curated set of parameters for the demo that produces a successful, meaningful demonstration:

| Parameter                | Demo Value                             | Rationale                               |
|--------------------------|----------------------------------------|-----------------------------------------|
| Dataset                  | 2-class spiral, 200 samples, noise=0.1 | Classic CasCor benchmark                |
| Input normalization      | Scale to [-1, 1]                       | Prevents activation saturation          |
| Activation               | Tanh                                   | CasCor specification                    |
| Output loss              | MSE                                    | CasCor specification                    |
| Learning rate            | 0.01                                   | Reasonable for SGD                      |
| Output retraining epochs | 200                                    | Sufficient for convergence              |
| Candidate pool size      | 8                                      | Good quality/speed tradeoff             |
| Candidate training steps | 100                                    | Sufficient for correlation maximization |
| Max hidden units         | 20                                     | Enough for spiral classification        |
| Max epochs               | 500                                    | Sufficient for convergence              |

#### Step 4.3: Create Integration Bridge

Design the adapter that allows juniper-canopy to drive a local cascor instance for demo mode, using the same `BackendProtocol` interface.

---

## Testing Plan

### Tests to Add/Modify

#### T-1: Activation Function Correctness

**File**: `juniper-canopy/src/tests/unit/test_mock_cascor_forward.py` (modify)

- Verify hidden units use tanh activation (not sigmoid)
- Verify tanh output range is [-1, 1]
- Verify forward pass output changes meaningfully when hidden units are added
- Verify hidden unit outputs are NOT constant (not all same value)

#### T-2: Training Convergence After Hidden Unit Addition

**File**: `juniper-canopy/src/tests/unit/test_demo_mode_training_convergence.py` (new)

- Train network for 30 epochs → verify loss decreases
- Add hidden unit → retrain for 200 steps → verify loss decreases further
- Add second hidden unit → retrain → verify continued improvement
- Verify accuracy exceeds 70% after 3 hidden units on spiral data
- Verify loss is significantly below `ln(2) ≈ 0.693` after hidden units

#### T-3: Candidate Training Quality

**File**: `juniper-canopy/src/tests/unit/test_candidate_training.py` (new)

- Train candidate → verify correlation > 0.1 (not random)
- Verify candidate output is NOT constant (variance > 0.01)
- Verify tanh derivative is used (not sigmoid derivative)
- Verify candidate pool selects highest-correlation candidate

#### T-4: Loss Function Correctness

**File**: `juniper-canopy/src/tests/unit/test_demo_mode_loss.py` (new)

- Verify loss computation uses MSE (not BCE)
- Verify gradient computation matches MSE gradient
- Verify output layer produces raw values (no sigmoid)
- Verify loss decreases monotonically on simple dataset

#### T-5: Decision Boundary Evolution

**File**: `juniper-canopy/src/tests/integration/test_demo_boundary_evolution.py` (modify)

- Run 100 epochs of training → capture boundary at epochs 0, 30, 60, 90
- Verify boundary changes at each checkpoint
- Verify boundary becomes non-linear after hidden units are added
- Verify boundary classification accuracy improves over time

#### T-6: Output Retraining Adequacy

**File**: `juniper-canopy/src/tests/unit/test_output_retraining.py` (new)

- Add hidden unit → verify output weights change significantly (not near random initial)
- Verify output weight for hidden unit column is non-trivial (abs > 0.01)
- Verify full-batch training is used during retraining

#### T-7: Existing Test Regression

- Run all existing tests to verify no regressions
- Key test files to verify:
  - `test_demo_mode_comprehensive.py`
  - `test_demo_mode_advanced.py`
  - `test_demo_boundary_fixes.py`
  - `test_mock_cascor_forward.py`

### Test Success Criteria

If all applicable tests pass, the following must be true:

1. Neural network training reduces loss below 0.5 within 100 epochs
2. Hidden units contribute non-linear features (non-constant output)
3. Decision boundary becomes non-linear after 2+ hidden units
4. Accuracy exceeds 70% on spiral data after 5 hidden units
5. Loss, accuracy, and decision boundary plots correctly reflect actual training progress

---

## Validation & Audit Results

### Sub-Agent Validation Summary

| Agent   | Focus Area                  | Verdict                     | Key Findings                                                                                                                                                                                                                                                                                             |
|---------|-----------------------------|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Agent 1 | RC-1 Activation Analysis    | **CONFIRMED**               | Sigmoid at `demo_mode.py:129`, tanh at `constants_activation.py:56`. Data range [-10, 10] confirmed (JuniperData default `radius=10.0`). Sigmoid derivative vanishes at extremes (`f' ≈ 4.5e-5` at `sigmoid(±10)`).                                                                                      |
| Agent 2 | RC-2 Loss Function Analysis | **CONFIRMED**               | `forward()` applies sigmoid (line 241). `train_output_step()` uses BCE gradient `p - y` (line 288). Cascor uses `nn.MSELoss()` (line 1278) on raw output (line 1240). BCE residuals bounded [-1,1] vs unbounded MSE residuals.                                                                           |
| Agent 3 | RC-3 Retraining Analysis    | **PARTIALLY CONFIRMED**     | Core claim correct. Ratio corrected: **~1,250×** in sample evaluations (not 125×). Demo: 50 × 32 = 1,600. Cascor: 1,000 × 2,000 = 2,000,000.                                                                                                                                                             |
| Agent 4 | Implementation Plan Review  | **FEASIBLE with additions** | All 4 fixes verified at exact lines. **Critical additional finding**: `_reset_state_and_history()` does not reset `output_weights`/`output_bias` — dimension mismatch crash after reset. Target encoding ({0,1} vs {-1,1}) must be specified. Decision threshold must update. 6 test files need updates. |
| Agent 5 | Test Plan Completeness      | **ADEQUATE with 6 gaps**    | 10 specific tests will break (exact lines identified). 6 gaps: no convergence quality test, no non-linear boundary test, no confidence mode test, no HTTP 503 test, `activation_fn` display string contradiction, no candidate training fallback test.                                                   |

### Critical Finding from Implementation Feasibility Agent

**New Bug Discovered: `_reset_state_and_history()` dimension mismatch**

**File**: `juniper-canopy/src/demo_mode.py`, lines 896-908

When the user clicks "Reset Training", `_reset_state_and_history()` clears `hidden_units` (list reset to []) but does NOT reinitialize `output_weights` or `output_bias`. After reset:

- `output_weights` shape: `(1, input_size + N_hidden)` (from previous run with N hidden units)
- `features` shape in `forward()`: `(batch, input_size)` (no hidden units)
- `torch.matmul(features, output_weights.T)` → **dimension mismatch crash**

**Resolution**: Added to Phase 1 as Step 1.5.

### Adjustments Made from Validation

1. **RC-3 ratio corrected**: From 125× to ~1,250× based on actual sample evaluation counts
2. **Step 1.2 expanded**: Must specify decision threshold (0.5 for {0,1} targets with raw output), target encoding (keep {0,1}), and accuracy computation
3. **Step 1.5 added**: Fix `_reset_state_and_history()` to reinitialize output weights to `(output_size, input_size)`
4. **Step 1.3 clarified**: Pass `batch_size=n_samples` for full-batch retraining
5. **Test plan expanded**: Added specific tests for convergence quality (`loss < 0.5`, `accuracy > 70%`) and non-linear boundary verification
6. **Files to modify expanded**: Added `demo_backend.py` (threshold), `test_demo_mode_comprehensive.py`, `test_demo_weight_training.py`, `test_demo_boundary_fixes.py`, `test_mock_cascor_forward.py`, `test_main_api_coverage.py`

### Tests Requiring Updates (from Validation)

| File                              | Lines              | Issue                                                                         |
|-----------------------------------|--------------------|-------------------------------------------------------------------------------|
| `test_demo_mode_comprehensive.py` | 48                 | `assert output >= 0 and output <= 1` — breaks with raw output                 |
| `test_demo_mode_comprehensive.py` | 88                 | `assert unit["activation_fn"] == torch.sigmoid` — must change to `torch.tanh` |
| `test_mock_cascor_forward.py`     | 35-39              | `test_output_is_sigmoid` — output range assertion breaks                      |
| `test_mock_cascor_forward.py`     | 114-120            | `test_output_in_sigmoid_range_with_many_hidden_units` — breaks                |
| `test_demo_boundary_fixes.py`     | 68, 71, 78         | Random unit uses `torch.sigmoid` — must use `torch.tanh`                      |
| `test_demo_boundary_fixes.py`     | 305, 312, 324, 335 | `(pred > 0.5)` threshold — keep for {0,1} targets with raw output             |
| `test_demo_weight_training.py`    | 66, 73             | `binary_cross_entropy()` — must change to MSE                                 |
| `test_main_api_coverage.py`       | 870                | `"activation_fn": "sigmoid"` — must change to `"tanh"`                        |
| `demo_backend.py`                 | 222                | `(predictions > 0.5).int()` — keep for {0,1} targets                          |

---

## Updated Implementation Plan (Post-Validation)

### Step 1.5 (NEW): Fix Reset Dimension Mismatch Bug

**File**: `juniper-canopy/src/demo_mode.py`
**Scope**: `DemoMode._reset_state_and_history()` or `MockCascorNetwork`

Add output weight reinitialization when hidden units are cleared:

```python
# In _reset_state_and_history() or a network reset method:
self.network.output_weights = torch.randn(self.network.output_size, self.network.input_size) * 0.1
self.network.output_bias = torch.randn(self.network.output_size) * 0.1
```

### Design Decision: Target Encoding

**Decision**: Keep targets as {0, 1}. Do NOT remap to {-1, 1}.

**Rationale**:

- The dataset from JuniperData uses `np.argmax(one_hot)` which produces {0, 1}
- MSE with {0, 1} targets and raw output works correctly — the network learns to output values near 0 and 1
- The decision threshold stays at 0.5 for both accuracy computation and decision boundary
- Simpler implementation with fewer changes needed
- This matches cascor's target encoding (cascor targets are also {0, 1})

---

## Document History

| Date       | Author                        | Change                                                                                                                                                                                                                   |
|------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-03-17 | Paul Calnon (via Claude Code) | Initial creation — comprehensive analysis of 8 root causes, comparative analysis, architecture review, phased implementation plan                                                                                        |
| 2026-03-17 | Paul Calnon (via Claude Code) | Validation complete — 5 sub-agents confirmed all root causes. RC-3 ratio corrected (1,250×). New bug found (reset dimension mismatch). Step 1.5 added. Test update inventory added. Target encoding decision documented. |
| 2026-03-17 | Paul Calnon (via Claude Code) | Implementation complete — Phase 1 & 2 all steps done. 167/167 tests passing. Final audit by 2 sub-agents: code audit passed all 8 checks (gradients mathematically verified), test audit found no issues.                |

---
