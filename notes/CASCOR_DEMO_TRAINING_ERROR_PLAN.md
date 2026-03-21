# CasCor Demo Training Error — Investigation & Remediation Plan

**Project**: Juniper Ecosystem (juniper-canopy + juniper-cascor)
**Created**: 2026-03-17
**Author**: Paul Calnon (via Claude Code)
**Status**: Active — Phase 1-5.2 Implementation Complete (19 skipped)
**Scope**: Cross-repo (juniper-canopy primary, juniper-cascor reference, juniper-ml coordination)
**Supersedes**: `CANOPY_DECISION_BOUNDARY_FIX_PLAN.md` (V1), `CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md` (V2)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Troubleshooting Summary](#troubleshooting-summary)
- [Root Cause Analysis](#root-cause-analysis)
- [Phase 3 Investigation: Post-Implementation Plateau](#phase-3-investigation-post-implementation-plateau)
- [Architecture Review](#architecture-review)
- [Implementation Plan](#implementation-plan)
- [Remediation Options: Phase 4](#remediation-options-phase-4)
- [Testing Plan](#testing-plan)
- [Validation & Audit Results](#validation--audit-results)
- [Phase 5.1: Convergence UI Controls Bugfix](#phase-51-convergence-ui-controls-bugfix)
- [Phase 5.2: Convergence UI Controls — Residual Bugfix](#phase-52-convergence-ui-controls--residual-bugfix)

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

## Phase 3 Investigation: Post-Implementation Plateau

### Current Symptom (2026-03-17, after Phase 1 & 2 fixes)

Despite implementing all Phase 1 & 2 fixes (tanh activation, MSE loss, 200-step full-batch retrain, 8-candidate pool, tanh derivative, reset bug fix), the demo training **still plateaus** after the first hidden node:

- **Loss**: Drops from ~0.5 to ~0.27 during initial output training (epochs 0–30), then flatlines at ~0.24 after +Unit #1
- **Accuracy**: Jumps from ~40% to ~56% at +Unit #1, then flatlines
- **Decision boundary**: Shows initial improvement (non-linear curve visible), then maintains roughly the same shape
- **Hidden units**: Units #2, #3, etc. are added but produce no further improvement

The Phase 1 & 2 fixes resolved the **mechanical bugs** (wrong activation, wrong loss, insufficient retrain, no candidate pool) but did not resolve the **training dynamics and algorithmic fidelity** issues that remain.

### Mathematical Audit Results

A full mathematical audit of the MSE gradient computation confirmed:

| Item                        | Status      | Details                                                       |
|-----------------------------|-------------|---------------------------------------------------------------|
| Weight gradient formula     | **Correct** | `2.0 * error.T @ features / N` matches dL/dW for standard MSE |
| Factor of 2.0               | **Correct** | Consistent with non-halved MSE: L = (1/N)*sum(e^2)            |
| Bias gradient formula       | **Correct** | `2.0 * error.mean(dim=0)` = `2.0 * error.sum(dim=0) / N`      |
| Weight/bias consistency     | **Correct** | Both use the same 2/N scaling                                 |
| Tanh derivative             | **Correct** | `1 - tanh(z)^2` is the standard formula                       |
| Divergence risk             | **Low**     | MSE on linear output is convex; tanh features bounded         |
| Hidden unit weight freezing | **Correct** | No subsequent code path modifies frozen weights               |
| 0.5 decision threshold      | **Correct** | Appropriate for {0,1} targets with raw output                 |

**The gradient math is not the problem.** The remaining issues are training dynamics and algorithmic fidelity.

### New Root Causes Identified

#### RC-9 (CRITICAL): Vanilla SGD vs Adam Optimizer for Output Training

**Demo**: Manual vanilla SGD with fixed lr=0.01, no momentum, no adaptive rates
**Cascor**: `torch.optim.Adam` (default) with lr=0.01, beta1=0.9, beta2=0.999, eps=1e-8, applied to `nn.Linear` layer with `loss.backward()` + `optimizer.step()`

**Why this matters for post-hidden-unit training**:

Adam maintains per-parameter first and second moment estimates (m and v). When a new hidden unit is installed, the output weight column for that unit has a different gradient scale than existing columns (hidden outputs are in [-1,1] while inputs are in [-10,10]). Adam adapts the effective learning rate for each parameter independently:

- New hidden unit column: gradient magnitude ~0.6, Adam effective lr ~0.01/√(0.6²) ≈ 0.017
- Old input columns: gradient magnitude ~3.2, Adam effective lr ~0.01/√(3.2²) ≈ 0.003

With vanilla SGD, all parameters share the same lr=0.01. The new hidden unit output weight changes at the same rate as the dominant input weights, preventing it from converging to a useful value.

Additionally, cascor creates a **fresh optimizer** for each output retraining phase (no stale momentum from the pre-unit-addition landscape). The demo has no optimizer state at all — neither an advantage nor disadvantage, but without momentum the convergence is significantly slower.

**Files**: `demo_mode.py:272-324` vs `cascade_correlation.py:1297`, `cascade_correlation_config.py:94`

#### RC-10 (CRITICAL): Mini-Batch Training Between Cascade Additions Undoes Full-Batch Retrain

**Mechanism**:

1. `add_hidden_unit()` performs 200 **full-batch** (N=200) retrain steps, converging output weights to a good configuration
2. On the very next training loop iteration, `_simulate_training_step()` calls `train_output_step(batch_size=32)` — a single **mini-batch** step with only 16% of the data
3. The mini-batch gradient has extremely high variance (measured signal-to-noise ratios):
   - Input column x1: SNR = 0.08
   - Input column x2: SNR = 0.001
   - Hidden unit column: SNR = 0.17
4. With SNR << 1, the mini-batch gradient is dominated by noise. The output weights perform a **random walk** rather than converging
5. Over 30 epochs of mini-batch training before the next cascade addition, the carefully retrained weights are perturbed away from their optimum

**Quantification**: Between cascade additions, the network gets 30 mini-batch steps × 32 samples = 960 sample evaluations (~4.8 full passes). The retrain provides 200 full-batch steps × 200 samples = 40,000 sample evaluations (~200 full passes). The inter-cascade training is **~40× weaker** than the retrain.

**Files**: `demo_mode.py:654` (calls `train_output_step()` with default `batch_size=32`), `demo_mode.py:160-161` (retrain uses `batch_size=n_samples`)

#### RC-11 (SIGNIFICANT): Un-Normalized Covariance vs Pearson Correlation in Candidate Training

**Demo** (`demo_mode.py:217`): Computes raw un-normalized covariance:

```python
correlation = (v_centered.unsqueeze(1) * e_centered).sum(dim=0)
```

No division by standard deviations. The tracked "correlation" value scales with residual magnitude.

**Cascor** (`candidate_unit.py:1053-1079`): Computes **Pearson correlation coefficient**, normalized by standard deviations:

```python
correlation = |sum(norm_output * norm_error)| / sqrt(sum(norm_output^2) * sum(norm_error^2) + eps)
```

This produces a value in [0, 1] regardless of residual scale. The gradient via autograd flows through the normalization.

**Why this matters after the first hidden unit**:

After the first hidden unit is installed and output weights retrained, the residual error `(y - prediction)` shrinks (because the network improved). With un-normalized covariance, the gradient signal for candidate training shrinks proportionally — subsequent candidates receive weaker training signals and produce lower-quality features. With Pearson correlation, the gradient is scale-invariant and candidates train equally well regardless of residual magnitude.

**Measured impact**: Candidate correlation decays from ~2.5 (first unit) to ~0.3 (seventh unit), a ~8× reduction. With Pearson normalization, the correlation would remain in [0, 1] for all candidates.

#### RC-12 (SIGNIFICANT): Spiral Dataset Complexity vs Hidden Unit Capacity

**Observation**: The spiral dataset from JuniperData uses default parameters that produce a **3-rotation spiral** with radius 10. This creates approximately **6 decision boundary crossings** between the two classes.

**Why this limits training**:

Each tanh hidden unit contributes roughly one nonlinear decision boundary (a sigmoid-like step along a hyperplane in the input space). To fully classify a 3-rotation spiral, the network needs approximately 10–15 hidden units, each positioned at a different angle/radius to carve out the spiral arms.

**Measured improvement per unit** (with current hyperparameters):

| Hidden Units | MSE Loss | Improvement |
|--------------|----------|-------------|
| 0            | 0.2457   | —           |
| 1            | 0.2430   | 0.003       |
| 3            | 0.2410   | 0.002       |
| 7            | 0.2398   | 0.001       |
| 12           | 0.2392   | 0.0005      |

Even with **optimal least-squares** output weights (analytically computed), 7 hidden units only reach MSE = 0.233. The improvement per unit (~0.001–0.003) is too small to be visually distinguishable in the dashboard charts, creating the appearance of a plateau even when the algorithm is functioning correctly.

A **1-rotation spiral** has only ~2 boundary crossings and would be solvable by 3–5 hidden units, producing a visually compelling training curve.

### RC-6 Revisited: Input Normalization Impact (MODERATE, elevated from original assessment)

The [-10, 10] input range has three compounding effects:

1. **Feature scale mismatch in output layer**: Input feature columns have abs_mean = 3.2 while hidden unit output columns have abs_mean = 0.63. The effective learning rate for hidden-connected weights is ~5× slower than for input-connected weights with vanilla SGD.

2. **Accelerated tanh saturation in candidate training**: With candidate weights growing during training (|w| ~ 0.22 by step 40), pre-activation values |z| = |w*x| reach ~2.2 for extreme inputs, where tanh'(z) = 0.03. By step 100, ~13% of samples are saturated.

3. **Weight initialization mismatch**: Standard `randn * 0.1` initialization with inputs in [-10, 10] produces initial outputs in [-1.8, 1.3], already overshooting the [0, 1] target range. With normalized [-1, 1] inputs, initial outputs would be in [-0.18, 0.13], a much better starting point.

### Confirmed Non-Issues

| Item                                 | Status            | Details                                |
|--------------------------------------|-------------------|----------------------------------------|
| MSE gradient math                    | **Correct**       | All formulas verified                  |
| Tanh derivative                      | **Correct**       | `1 - v*v` is standard                  |
| Hidden weight freezing               | **Working**       | No code path modifies frozen weights   |
| Output divergence                    | **Not occurring** | MSE on linear output is convex         |
| 0.5 decision threshold               | **Appropriate**   | Correct for {0,1} targets              |
| Weight/bias gradient consistency     | **Matched**       | Both use 2/N scaling                   |
| Artificial loss inflation (line 816) | **Harmless**      | Overwritten by real MSE next iteration |
| `target_loss` variable               | **Dead code**     | Written but never read; cosmetic only  |

---

## Remediation Options: Phase 4

### Overview

Four remediation approaches are presented, from minimal change to comprehensive refactor. All address the newly identified root causes (RC-9 through RC-12 and elevated RC-6). Approaches can be combined.

### Option 4A: Targeted Hyperparameter Fixes (Minimal Code Change)

Fix the training dynamics issues within the existing manual gradient framework.

**Changes**:

1. **Use full-batch for ALL output training** (RC-10): Change `_simulate_training_step()` to call `train_output_step(batch_size=n_samples)` instead of the default 32
2. **Increase output retraining to 500 steps** (RC-3/RC-10): Change from 200 to 500 in `add_hidden_unit()`
3. **Normalize inputs to [-1, 1]** (RC-6): Apply min-max normalization in `_generate_spiral_dataset_from_juniper_data()` after loading data
4. **Reduce spiral complexity** (RC-12): Pass `n_rotations=1` to JuniperData or reduce the radius
5. **Increase candidate training steps** to 200 with lr=0.03 and pool size 16 (RC-11 mitigation)

```python
# In _simulate_training_step():
n_samples = self.network.train_x.shape[0]
self.network.train_output_step(batch_size=n_samples)  # full-batch

# In _generate_spiral_dataset_from_juniper_data(), after loading:
inputs_min = inputs.min(axis=0)
inputs_max = inputs.max(axis=0)
inputs = 2.0 * (inputs - inputs_min) / (inputs_max - inputs_min + 1e-8) - 1.0
```

**Pros**: Minimal code change (~20 lines), no new dependencies, preserves existing test structure
**Cons**: Does not fix RC-9 (SGD vs Adam) or RC-11 (un-normalized correlation). May require further tuning.

**Estimated impact**: Moderate improvement. Full-batch training eliminates the gradient noise problem. Input normalization fixes the scale mismatch. Simpler spiral makes progress visible. But without Adam, convergence will remain slow.

### Option 4B: Replace Manual SGD with PyTorch Autograd + Adam (Recommended)

Replace the manual gradient computation in both `train_output_step()` and `_train_candidate()` with PyTorch autograd and Adam optimizer.

**Changes**:

1. **Output layer**: Replace manual weight tensors with `nn.Linear` + `torch.optim.Adam`
2. **Output retraining**: Create a fresh Adam optimizer after each hidden unit installation
3. **Candidate training**: Use `nn.Parameter` + `torch.optim.Adam` for candidate weight optimization
4. **Candidate correlation**: Normalize to Pearson correlation (divide by std product)
5. **Input normalization**: Apply min-max normalization
6. **Full-batch training**: Use full dataset for all gradient steps

```python
class MockCascorNetwork:
    def __init__(self, input_size=2, output_size=1):
        # ...
        self.output_layer = torch.nn.Linear(input_size, output_size)
        self.output_optimizer = torch.optim.Adam(self.output_layer.parameters(), lr=0.01)
        self.loss_fn = torch.nn.MSELoss()

    def forward(self, x):
        # Cascade through hidden units (unchanged)
        # ...
        return self.output_layer(features)

    def train_output_step(self, batch_size=None):
        # Use full batch by default
        x = self.train_x if batch_size is None else self.train_x[indices]
        y = self.train_y if batch_size is None else self.train_y[indices]

        self.output_optimizer.zero_grad()
        predictions = self.forward(x)
        loss = self.loss_fn(predictions, y)
        loss.backward()
        self.output_optimizer.step()

    def add_hidden_unit(self):
        # ... train candidate pool (unchanged) ...
        # Install best candidate
        self.hidden_units.append(best_unit)

        # Create new output layer with expanded input dimension
        old_layer = self.output_layer
        new_dim = self.input_size + len(self.hidden_units)
        self.output_layer = torch.nn.Linear(new_dim, self.output_size)
        with torch.no_grad():
            self.output_layer.weight[:, :old_layer.in_features] = old_layer.weight
            self.output_layer.bias[:] = old_layer.bias
            # New column initialized by nn.Linear default (small random)

        # Fresh optimizer for retraining (no stale momentum)
        self.output_optimizer = torch.optim.Adam(self.output_layer.parameters(), lr=0.01)

        # Retrain output with full batch
        for _ in range(500):
            self.train_output_step()

    def _train_candidate(self, unit, steps=200, lr=0.01):
        # ... (build candidate_input as before) ...
        weights = torch.nn.Parameter(unit["weights"].clone())
        bias = torch.nn.Parameter(unit["bias"].clone())
        optimizer = torch.optim.Adam([weights, bias], lr=lr)

        for _ in range(steps):
            optimizer.zero_grad()
            z = candidate_input @ weights + bias
            v = torch.tanh(z)
            v_centered = v - v.mean()
            e_centered = residual - residual.mean(dim=0)
            # Pearson correlation (normalized)
            cov = (v_centered.unsqueeze(1) * e_centered).sum(dim=0)
            std_v = torch.sqrt((v_centered ** 2).sum() + 1e-8)
            std_e = torch.sqrt((e_centered ** 2).sum(dim=0) + 1e-8)
            correlation = (cov / (std_v * std_e)).abs().sum()
            (-correlation).backward()  # maximize
            optimizer.step()
            optimizer.zero_grad()

        unit["weights"] = weights.detach()
        unit["bias"] = bias.detach()
        return float(correlation.detach())
```

**Pros**:

- Addresses RC-9 (Adam), RC-10 (full-batch), RC-11 (Pearson correlation), RC-6 (normalization)
- Eliminates all manual gradient code — no more derivative bugs possible
- Matches cascor's optimizer and correlation strategy
- Fresh optimizer state after each hidden unit installation (matches cascor behavior)
- More maintainable — less custom math code

**Cons**:

- Requires `torch.no_grad()` / `requires_grad` management in the training loop (since forward() is used both for training and inference)
- Changes to `forward()` need to work both with and without gradient tracking
- More extensive test updates needed (output weights now in `nn.Linear` instead of raw tensors)
- ~150 lines of code change

**Estimated impact**: High. Adam + Pearson correlation + full-batch addresses all critical root causes. The network should show continuous improvement across hidden unit additions.

### Option 4C: Reduce Spiral Complexity for Demo (Complementary)

Independently of Options 4A/4B, reduce the spiral dataset complexity to produce more visually compelling demo results.

**Changes**:

1. **Reduce spiral rotations**: Pass `n_rotations=1` or `turns=1.0` to JuniperData when generating the demo dataset. A 1-rotation spiral has ~2 boundary crossings, solvable by 3–5 hidden units.
2. **Reduce radius or normalize**: Either pass `radius=1.0` to JuniperData, or normalize the returned data to [-1, 1]
3. **Optionally reduce sample count**: 100–150 samples (from 200) for faster training steps

```python
# In _generate_spiral_dataset_from_juniper_data():
params = {
    "n_points_per_spiral": n_samples // 2,
    "n_spirals": 2,
    "noise": 0.1,
    "seed": 42,
    "turns": 1.0,       # 1 rotation instead of default 3
    "radius": 1.0,      # normalized range
}
```

**Pros**: Single-line parameter change. Dramatic improvement in visual training progression. No changes to the network code.
**Cons**: Doesn't fix the underlying algorithm issues (they just matter less for a simpler problem). If users change dataset parameters in the UI, the plateau would return for complex datasets.

**Estimated impact**: High for demo visual quality. A 1-rotation spiral with normalized inputs would show clear accuracy improvement from ~50% to 90%+ over 5 hidden units, even with the current SGD-based training.

### Option 4D: Convergence-Based Hidden Unit Addition (Enhancement)

Replace the fixed-schedule cascade addition (`cascade_every=30`) with convergence-based addition, matching the real CasCor algorithm.

**Changes**:

1. Track loss over a sliding window (e.g., last 10 epochs)
2. Add hidden unit when loss improvement falls below threshold (e.g., < 0.001 over 10 epochs)
3. Keep the fixed schedule as a fallback maximum interval
4. Don't add unit if loss is still improving rapidly

```python
def _should_add_cascade_unit(self) -> bool:
    with self._lock:
        max_units = self.max_hidden_units
        current_units = len(self.network.hidden_units)

    if current_units >= max_units:
        return False

    # Convergence-based: check if loss has stopped improving
    if len(self.network.history["train_loss"]) >= 10:
        recent = list(self.network.history["train_loss"])[-10:]
        improvement = recent[0] - recent[-1]
        if improvement < 0.001:
            return True

    # Fallback: fixed schedule as maximum interval
    return self.current_epoch > 0 and self.current_epoch % self.cascade_every == 0
```

**Pros**: Adds units at algorithmically appropriate times. Prevents adding units while output is still converging. Matches cascor behavior.
**Cons**: Small code change but introduces a new hyperparameter (improvement threshold). May add units too early if loss oscillates (mini-batch noise).

**Estimated impact**: Low to moderate alone. Most effective when combined with Option 4B (where full-batch training eliminates the noise that could trigger false convergence).

### Recommended Approach: Option 4B + 4D Combined ★★ SELECTED

**Note**: Option 4C (reduce spiral complexity) was explicitly **excluded** per user direction. The spiral dataset retains its default complexity; the algorithmic fixes must handle it.

**Phase 4 Implementation (Complete — implemented 2026-03-18)**:

> **History**: A prior session documented Phase 4 as complete but the changes were not applied to the codebase. A full audit on 2026-03-18 identified this discrepancy and all 9 steps were then properly implemented and verified.

1. **Step 4.1**: Apply input normalization to [-1, 1] ✅ — `_generate_spiral_dataset_from_juniper_data()` normalizes after loading; normalization params stored on network for decision boundary use; `normalize_inputs()` method added to `MockCascorNetwork`
2. **Step 4.2**: Replace manual SGD with `nn.Linear` + `torch.optim.Adam` for output training ✅ — `output_layer = nn.Linear(...)`, `output_optimizer = Adam(...)`, `loss_fn = MSELoss()`; backward-compatible `output_weights`/`output_bias` properties
3. **Step 4.3**: Replace manual candidate gradient with autograd + Adam + Pearson correlation ✅ — candidate weights wrapped as `nn.Parameter`, Pearson normalized by std product, Adam optimizer per candidate
4. **Step 4.4**: Add convergence-based cascade addition ✅ — checks loss improvement over 10-epoch sliding window (threshold < 0.001), with fixed schedule as fallback
5. **Step 4.5**: Full-batch training for all output steps ✅ — `train_output_step()` defaults to `batch_size=None` (full batch)
6. **Step 4.6**: Output retraining increased to 500 steps ✅ — up from 200, with fresh Adam optimizer
7. **Step 4.7**: Candidate training increased to 200 steps with lr=0.01 ✅ — up from 100/lr=0.05
8. **Step 4.8**: Update affected tests ✅ — optimizer assertions updated (SGD→Adam), variance thresholds relaxed for normalized inputs, `torch.no_grad()` added to inference calls, 29 new Phase 4 tests added
9. **Step 4.9**: Decision boundary normalization ✅ — `demo_backend.py` normalizes grid points via `network.normalize_inputs()` before forward pass

### Files Modified (Phase 4) — Implemented 2026-03-18

| File                                | Changes                                                                                                                                                                      |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `demo_mode.py`                      | `MockCascorNetwork.__init__()`: `nn.Linear` + Adam replaces manual weights; `normalize_inputs()` method added; backward-compatible `output_weights`/`output_bias` properties |
| `demo_mode.py`                      | `forward()`: refactor to use `_cascade_features()` + `self.output_layer(features)`                                                                                           |
| `demo_mode.py`                      | `train_output_step()`: autograd + Adam replaces manual gradient; full-batch default                                                                                          |
| `demo_mode.py`                      | `_train_candidate()`: autograd + Adam + Pearson correlation replaces manual gradient                                                                                         |
| `demo_mode.py`                      | `add_hidden_unit()`: expand `nn.Linear` with warm-start; fresh optimizer; 500 retrain steps                                                                                  |
| `demo_mode.py`                      | `_simulate_training_step()`: use `output_layer.eval()`/`.train()` for metrics                                                                                                |
| `demo_mode.py`                      | `_should_add_cascade_unit()`: convergence-based with 10-epoch sliding window                                                                                                 |
| `demo_mode.py`                      | `_reset_state_and_history()`: reinitialize `nn.Linear` + fresh optimizer                                                                                                     |
| `demo_mode.py`                      | `_generate_spiral_dataset_from_juniper_data()`: normalize inputs to [-1, 1]                                                                                                  |
| `demo_backend.py`                   | `get_network_topology()`: read from `network.output_layer.weight.data`                                                                                                       |
| `demo_backend.py`                   | `get_decision_boundary()`: normalize grid points via `network.normalize_inputs()`                                                                                            |
| `test_demo_weight_training.py`      | `test_works_with_hidden_units`: reset optimizer to test after convergence                                                                                                    |
| `test_demo_training_convergence.py` | `test_hidden_unit_output_is_not_constant`: use `_cascade_features()`, relaxed threshold for normalized inputs                                                                |
| `test_demo_training_convergence.py` | `test_initial_training_reduces_loss`: wrap with `torch.no_grad()`                                                                                                            |

---

### Architecture Comparison (Post-Phase 4)

| Aspect                        | Demo Mode (`MockCascorNetwork`)      | Cascor (`CascadeCorrelationNetwork`)         | Match? |
|-------------------------------|--------------------------------------|----------------------------------------------|--------|
| **Hidden activation**         | `torch.tanh` [-1, 1]                 | `nn.Tanh` [-1, 1]                            | ✅     |
| **Output activation**         | Raw linear: `nn.Linear`              | Raw linear: `nn.Linear`                      | ✅     |
| **Loss function**             | MSE (`nn.MSELoss`) + autograd        | MSE (`nn.MSELoss`)                           | ✅     |
| **Output training**           | Full-batch + 500 post-install        | Full-batch + 1000 post-install               | ≈      |
| **Output optimizer**          | `torch.optim.Adam` (lr=0.01)         | `torch.optim.Adam` (lr=0.01)                 | ✅     |
| **Fresh optimizer per phase** | Yes (new Adam after each install)    | Yes (new optimizer per `train_output_layer`) | ✅     |
| **Candidate pool**            | 8 candidates                         | 16 candidates (parallel)                     | ≈      |
| **Candidate training**        | 200 steps, Adam, autograd            | Configurable epochs, autograd                | ✅     |
| **Candidate correlation**     | Pearson (normalized)                 | Pearson (normalized)                         | ✅     |
| **Candidate selection**       | Max absolute Pearson correlation     | Max absolute correlation                     | ✅     |
| **Hidden unit addition**      | Convergence-based + fixed fallback   | Convergence-based + correlation threshold    | ✅     |
| **Input normalization**       | Min-max to [-1, 1]                   | None (uses smaller-range data)               | ✅     |
| **Weight initialization**     | `nn.init.normal_(std=0.1)`           | `randn * 0.1`                                | ✅     |
| **Output weight expansion**   | Warm-start: copy old, random new col | Warm-start: copy old, random new row         | ✅     |
| **Data format**               | Tensor (N, 2), targets (N, 1)        | Tensor (N, 2), targets (N, 1)                | ✅     |
| **Thread safety**             | `threading.Lock`                     | Not thread-safe (process-based)              | N/A    |

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

### Remaining Differences (Post-Phase 4)

1. **Output retraining epochs**: 500 (demo) vs 1000 (cascor) — acceptable for demo speed
2. **Candidate pool size**: 8 (demo) vs 16 (cascor) — acceptable tradeoff
3. **Candidate training epochs**: 200 (demo) vs configurable/longer (cascor) — acceptable for demo
4. **Parallelism**: Single-threaded candidates (demo) vs multiprocess pool (cascor)

All critical algorithmic mismatches (activation, loss, optimizer, correlation, normalization, scheduling) have been resolved.

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
# In _reset_state_and_history() or a network reset method:# Juniper Cascor Concurrency

develop a detailed plan to perform an in-depth investigation and analysis of the juniper-cascor application's concurrent programming implementation

## Detailed analysis

utilize multiple sub-agents to perform the following analysis:

- include all aspects of the cascor app's codebase that are utilizing parallelism of any kind
- pay particular attention to the code used to implement concurrency for the cascor worker objects, the juniper-cascor-worker and juniper-cascor-client applications, and the code infrastructure that supports them
- the codebase originally used process based parallelism using the multiprocessing library and implementing the thread-server object to manage a long-lived worker process pool
- some work has been done to add thread-based parallelism since python 3.14 allows the GIL to be disabled
- analyze the current code base concurrency implementation
- consider previous solutions (or partial solutions)
- take into account a critical requirement of the Juniper Project:
  - the juniper cascor worker pool needs to be able to easily manage remote workers
  - these remote workers will need to be able to connect before or after processing has started
  - the remote workers will be running on a diverse set of hardware and/or VMs
  - remote workers will be running heterogeneous operating systems
  - connections might be intermittent
  - remote worker code should be lightweight
    - but not to the detriment of flexibility, functionality, or performance
  - remote worker code should be implemented in python avoiding non-standard libraries unless they are needed
    - this requirement should not be used to justify limiting worker flexibility, functionality, or performance
- consider best practices with respect to:
  - performance
  - flexibility
  - security
  - maintainability
- analysis should be performed with the following assumptions:
  - high performance is critical
  - all remote worker machines will have access to python 3.14+
  - security solution should consider both:
    - the security of the distributed worker network wrt external risks
    - the security of the individual remote workers wrt other potentially malicious workers
    - the security of the primary workstation wrt all remote workers
    - the security of the primary workstation wrt external risks

## Present multiple approaches

use multiple sug-agents to utilize the analysis to generate multiple proposals:

- for how to implement concurrency
- and how to manage concurrency
  - on the local workstation
  - and on the heterogeneous set of remote workers
- types of concurrency
  - how they are used
  - where in the code-base they are utilized
- the overall architectural choices for concurrency
- guardrails to maintain stability and performance

## Plan Document

when the plan has been developed, write it into a markdown file in the notes/ directory
update as necessary to include the following:

- include all analysis and investigation performed during this process in the plan document, from all sub-agents
- include all potential approaches and proposals, from all sub-agents
- include all considerations regarding various aspects of this plan, from all sub-agents
- include analysis of approaches with respect to project requirements
  - requirements should include, but not be limited to, those defined above
- include strengths and weakness of proposals and approaches
- include discussions of risks and guardrails for proposals and approaches
- include supporting code and infrastructure needed for proposals
- include detailed design elements for proposed approaches
- develop recommendations among the various proposals
- list the reasoning behind selections

## Testing Updates

- add additional tests as needed
  - document tests needed to validate the correctness and accuracy of this enahancement
  - document tests to ensure no regressions are introduced while adding this feature

## Pre-Work Validation

when the plan has been developed, utilize multiple sub-agents to evaluate and validate all aspects of this plan
synthesize and integrate input from sub-agents
update the plan as needed to reflect results of sub-agent validation

commit all changes made so far

## Implementation

once validation is complete and plan has been updated accordingly, begin implementing the plan

## Thread Handoff

A key requirement for this work is to avoid thread compaction

if, at any time during this work, the context utilization exceeds 80%, perform a thread handoff in accordance with the procedure documented in the notes/ directory
when the thread handoff prompt is complete, pass it to the wake_the_claude.bash script to create a new thread that will continue performing this work

## Post work validation

when all work is complete for this enhancement, use multiple sub-agents to perform an in depth audit of the juniper-cascor code with respect to the development plan
synthesize and validate this information and make any necessary additions or modifications to the plan document

## Cleanup

when validation is complete, commit all changes, and push

- then create pull requests for all of the committed changes

- once the pull requests have been merged, perform the worktree cleanup v2 procedure as documented in the notes/ directory
  - use particular care to avoid the bash invalid CWD trap as documented in the procedure

---


### Design Decision: Target Encoding

**Decision**: Keep targets as {0, 1}. Do NOT remap to {-1, 1}.

**Rationale**:

- The dataset from JuniperData uses `np.argmax(one_hot)` which produces {0, 1}
- MSE with {0, 1} targets and raw output works correctly — the network learns to output values near 0 and 1
- The decision threshold stays at 0.5 for both accuracy computation and decision boundary
- Simpler implementation with fewer changes needed
- This matches cascor's target encoding (cascor targets are also {0, 1})

---

## Phase 5: Convergence Window UI Controls Enhancement

### Overview

Add user-facing controls to the Training Metrics panel to allow toggling and tuning the convergence-based cascade unit addition feature introduced in Phase 4. Currently, the convergence detection (10-epoch sliding window with threshold 0.001) is always enabled with hardcoded parameters. This enhancement makes it configurable at runtime.

### Requirements

1. **Checkbox**: Enable/disable the "Convergence-Based Sliding Window" feature
   - Default: **enabled** (checked)
   - When disabled, cascade units are added only on the fixed schedule (`cascade_every` epochs)
   - When enabled, convergence detection can trigger early cascade addition

2. **Numeric input field**: Adjust the convergence threshold
   - Default: **0.001** (current hardcoded value)
   - Range: 0.0001 to 0.1 (step 0.0001)
   - Pre-populated with the current default value
   - Only active when the checkbox is enabled (visually disabled otherwise)

3. Both controls must integrate with the existing "Apply Parameters" workflow (change detection → button enable → POST /api/set_params → DemoMode.apply_params())

### Implementation Plan

#### Step 5.1: Add Constants

**File**: `canopy_constants.py`

Add to `TrainingConstants`:

```python
DEFAULT_CONVERGENCE_ENABLED: Final[bool] = True
DEFAULT_CONVERGENCE_THRESHOLD: Final[float] = 0.001
MIN_CONVERGENCE_THRESHOLD: Final[float] = 0.0001
MAX_CONVERGENCE_THRESHOLD: Final[float] = 0.1
```

#### Step 5.2: Add Instance Attributes to DemoMode

**File**: `demo_mode.py` — `DemoMode.__init__()`

Add after `self.cascade_every`:

```python
self.convergence_enabled = TrainingConstants.DEFAULT_CONVERGENCE_ENABLED
self.convergence_threshold = TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD
```

#### Step 5.3: Update `_should_add_cascade_unit()` to Use Instance Attributes

**File**: `demo_mode.py`

Replace hardcoded `10` and `0.001` with `self.convergence_enabled` guard and `self.convergence_threshold`:

```python
if self.convergence_enabled and len(self.network.history["train_loss"]) >= 10:
    recent = list(self.network.history["train_loss"])[-10:]
    improvement = recent[0] - recent[-1]
    if improvement < self.convergence_threshold:
        return True
```

#### Step 5.4: Extend `DemoMode.apply_params()`

**File**: `demo_mode.py`

Add parameters:

```python
def apply_params(
    self,
    learning_rate=None,
    max_hidden_units=None,
    max_epochs=None,
    convergence_enabled=None,
    convergence_threshold=None,
):
```

In the `with self._lock:` block:

```python
if convergence_enabled is not None:
    self.convergence_enabled = bool(convergence_enabled)
if convergence_threshold is not None:
    self.convergence_threshold = float(convergence_threshold)
```

#### Step 5.5: Update `DemoBackend.apply_params()`

**File**: `backend/demo_backend.py`

Forward new params:

```python
self._demo.apply_params(
    ...
    convergence_enabled=params.get("convergence_enabled"),
    convergence_threshold=params.get("convergence_threshold"),
)
```

#### Step 5.6: Update FastAPI Endpoint

**File**: `main.py` — `api_set_params()`

Extract and forward:

```python
convergence_enabled = params.get("convergence_enabled")
convergence_threshold = params.get("convergence_threshold")
```

#### Step 5.7: Add UI Controls to Dashboard

**File**: `frontend/dashboard_manager.py` — `_build_layout()`

Insert between "Maximum Epochs" input and the `html.Hr()` before "Apply Parameters":

```python
html.Hr(),
html.P("Convergence Detection:", className="mb-1 fw-bold"),
dcc.Checklist(
    id="convergence-enabled-checkbox",
    options=[{"label": " Enable sliding window", "value": "enabled"}],
    value=["enabled"],
    className="mb-2",
),
html.P("Convergence Threshold:", className="mb-1 fw-bold"),
dbc.Input(
    id="convergence-threshold-input",
    type="number",
    value=TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD,
    step=0.0001,
    min=TrainingConstants.MIN_CONVERGENCE_THRESHOLD,
    max=TrainingConstants.MAX_CONVERGENCE_THRESHOLD,
    className="mb-2",
    debounce=True,
),
```

#### Step 5.8: Wire Callbacks in Dashboard Manager

**File**: `frontend/dashboard_manager.py`

1. **Change detection** (`_track_param_changes_handler`): Add `convergence-enabled-checkbox.value` and `convergence-threshold-input.value` as inputs
2. **Apply handler** (`_apply_parameters_handler`): Include `convergence_enabled` and `convergence_threshold` in POST body. **Note**: `dcc.Checklist` returns `["enabled"]` or `[]` — convert to boolean: `convergence_enabled = "enabled" in checklist_value`
3. **Backend sync** (`_sync_input_values_from_backend_handler`): Expand return tuple to 5 values (add convergence checkbox value and threshold)
4. **Init handler** (`_init_applied_params_handler`): Include convergence defaults in applied-params-store
5. **Backend params store** (`backend-params-state`): Update initial data dict to include `convergence_enabled` and `convergence_threshold`

#### Step 5.9: Update `_reset_state_and_history()` (from validation)

**File**: `demo_mode.py`

Reset convergence params to defaults on training reset:

```python
self.convergence_enabled = TrainingConstants.DEFAULT_CONVERGENCE_ENABLED
self.convergence_threshold = TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD
```

#### Step 5.10: Update `get_current_state()` (from validation)

**File**: `demo_mode.py`

Include convergence params in state dict so `/api/state` exposes them for frontend sync.

#### Step 5.11: Update existing `_make_demo()` helper (from validation)

**File**: `tests/unit/test_phase4_implementation.py`

The `_make_demo()` helper uses `DemoMode.__new__()` (bypasses `__init__`). Must add:

```python
demo.convergence_enabled = True
demo.convergence_threshold = 0.001
```

Without this, 5 existing Phase 4 tests will fail with `AttributeError`.

### Validation Agent Findings

| Agent       | Verdict                         | Critical Findings                                         |
|-------------|---------------------------------|-----------------------------------------------------------|
| Feasibility | **FEASIBLE WITH MODIFICATIONS** | 8 additional steps/considerations identified              |
| Test Plan   | **ADEQUATE with 11 gaps**       | 5 must-have test additions, 4 should-have, 2 nice-to-have |

**Must-fix items incorporated**: Steps 5.9, 5.10, 5.11 added. Checklist-to-boolean conversion noted in Step 5.8. `backend-params-state` store update noted.

### Testing Plan (Phase 5)

#### T-5.1: Unit Tests — Convergence Toggle

**File**: `tests/unit/test_convergence_ui_controls.py` (new)

| Test                                                 | Description                                                                                            |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `test_convergence_enabled_by_default`                | `DemoMode` initializes with `convergence_enabled=True`                                                 |
| `test_convergence_threshold_default_value`           | `DemoMode` initializes with `convergence_threshold=0.001`                                              |
| `test_apply_params_sets_convergence_enabled`         | `apply_params(convergence_enabled=False)` disables convergence                                         |
| `test_apply_params_sets_convergence_threshold`       | `apply_params(convergence_threshold=0.01)` updates threshold                                           |
| `test_disabled_convergence_uses_fixed_schedule_only` | With `convergence_enabled=False`, `_should_add_cascade_unit()` only fires on `cascade_every` intervals |
| `test_enabled_convergence_fires_on_plateau`          | With `convergence_enabled=True` and loss plateau, unit is added before `cascade_every`                 |
| `test_threshold_affects_sensitivity`                 | Higher threshold (0.01) triggers earlier than lower threshold (0.0001)                                 |
| `test_apply_params_threshold_bounds`                 | Values outside [0.0001, 0.1] are clamped or rejected                                                   |

#### T-5.2: Integration Tests — API Endpoint

**File**: `tests/integration/test_convergence_params_api.py` (new)

| Test                                         | Description                                                                |
|----------------------------------------------|----------------------------------------------------------------------------|
| `test_set_params_convergence_enabled`        | POST `/api/set_params` with `convergence_enabled=false` persists           |
| `test_set_params_convergence_threshold`      | POST `/api/set_params` with `convergence_threshold=0.01` persists          |
| `test_get_state_includes_convergence_params` | GET `/api/state` returns `convergence_enabled` and `convergence_threshold` |
| `test_params_survive_pause_resume`           | Convergence params persist through pause/resume cycle                      |

#### T-5.3: Regression Tests

| Test                                         | Description                                                          | File                                |
|----------------------------------------------|----------------------------------------------------------------------|-------------------------------------|
| `test_existing_params_still_work`            | `learning_rate`, `max_hidden_units`, `max_epochs` unchanged          | `test_apply_button_parameters.py`   |
| `test_training_convergence_unchanged`        | Training convergence behavior with default params matches Phase 4    | `test_demo_training_convergence.py` |
| `test_apply_params_button_enables_on_change` | Button enables when convergence params change                        | `test_parameter_persistence.py`     |
| `test_reset_restores_convergence_defaults`   | Reset training restores convergence_enabled=True and threshold=0.001 | new test                            |

### Files to Modify (Phase 5)

| File                                                     | Changes                                                                                                               |
|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `canopy_constants.py`                                    | Add convergence constants to `TrainingConstants`                                                                      |
| `demo_mode.py`                                           | Add instance attrs, update `_should_add_cascade_unit()`, extend `apply_params()`, update `_reset_state_and_history()` |
| `backend/demo_backend.py`                                | Forward convergence params in `apply_params()`                                                                        |
| `main.py`                                                | Extract convergence params in `api_set_params()`                                                                      |
| `frontend/dashboard_manager.py`                          | Add checkbox + threshold input, wire callbacks                                                                        |
| `tests/unit/test_convergence_ui_controls.py` (new)       | Unit tests for convergence toggle and threshold                                                                       |
| `tests/integration/test_convergence_params_api.py` (new) | API integration tests                                                                                                 |

---

## Phase 5.1: Convergence UI Controls Bugfix

### Overview

Fixes four bugs in the Phase 5 convergence UI controls implementation that prevented user interaction from working correctly.

### Bugs Fixed

| Bug                                 | Symptom                                                                   | Root Cause                                                                                                                                          | Fix                                                                                        |
|-------------------------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **B-5.1**: Checkbox uncheck reverts | Unchecking convergence checkbox and clicking Apply restores it to checked | `sync_input_values_from_backend` Callbk writes `backend-params-state` IP / 5s via `slow-update-interval`                                            | Removed the continuous sync callback chain                                                 |
| **B-5.2**: Threshold value reverts  | Editing convergence threshold and clicking Apply resets to default        | Same root cause as B-5.1 — periodic sync overwrites user edits before Apply can be clicked                                                          | Same fix as B-5.1                                                                          |
| **B-5.3**: Meta-param vals refresh  | param fields (lr, hidden units, epochs, conv ctrls) overwritten/5 sec     | `sync_backend_params` polls `/api/state` per 5s → writes `backend-params-state` → triggers `sync_input_values_from_backend` → overwrites all inputs | Replaced continuous polling with one-time initialization on first load                     |
| **B-5.4**: Missing section heading  | Meta-params missing section heading (e.g., Train Ctrl, Network Info)      | All parameters were inside the Training Controls card without separation                                                                            | Split into separate "Training Controls" (buttons) and "Training Parameters" (inputs) cards |

### Implementation

#### Step 5.1.1: Remove Continuous Backend Sync (B-5.1, B-5.2, B-5.3)

**File**: `frontend/dashboard_manager.py`

**Removed:**

- `sync_input_values_from_backend` callback and `_sync_input_values_from_backend_handler` — continuously overwrote inputs from backend state
- `sync_backend_params` callback and `_sync_backend_params_handler` — polled `/api/state` every 5 seconds to update `backend-params-state`
- `init_applied_params` callback and `_init_applied_params_handler` — replaced by combined handler
- `backend-params-state` dcc.Store — no longer needed (was only consumed by removed callbacks)
- `pending-params-store` dcc.Store — dead code, never referenced by any callback

**Added:**

- `init_params_from_backend` callback and `_init_params_from_backend_handler` — fires once on first `slow-update-interval` tick, initializes both input fields AND `applied-params-store` from backend state. Returns `no_update` on all subsequent ticks (gated by `current_applied` truthiness).

**Data flow (corrected):**

```bash
1. Dashboard loads → inputs show defaults from constants
2. First slow-update-interval tick → init_params_from_backend fires
3. Fetches /api/state → populates inputs + applied-params-store
4. Never fires again (applied-params-store now truthy)
5. User edits inputs freely — no periodic overwrites
6. track_param_changes detects diff → Apply button enables
7. User clicks Apply → apply_parameters POSTs to backend + updates applied-params-store
```

#### Step 5.1.2: Split Training Controls Card (B-5.4)

**File**: `frontend/dashboard_manager.py`

Split the single "Training Controls" card into two separate cards:

- **"Training Controls"** — Start, Pause, Resume, Stop, Reset buttons only
- **"Training Parameters"** — Learning Rate, Max Hidden Units, Maximum Epochs inputs, Convergence Detection controls, and Apply Parameters button

### Testing

Tests updated across 5 test files:

| File                                 | Changes                                                                                                                                                                               |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_dashboard_manager_handlers.py` | Del 7 tests for handlers (`_sync_backend_params_handler`, `_sync_input_values_from_backend_handler`, `_init_applied_params_handler`). Add 5 `_init_params_from_backend_handler` tests |
| `test_dashboard_manager.py`          | Removed 5 tests for deleted handlers. Added 3 replacement tests.                                                                                                                      |
| `test_dashboard_manager_95.py`       | Removed 6 tests for deleted handlers. Added 4 replacement tests. Updated registered callback list assertion.                                                                          |
| `test_apply_button_parameters.py`    | Updated 1 test from `_init_applied_params_handler` to `_init_params_from_backend_handler`.                                                                                            |
| `test_max_epochs_parameter.py`       | update assertons `applied-params-store` vs `backend-params-state`, section name updated from "Training Controls" to "Training Parameters".                                            |

**Test results**: 3585 passed, 0 failed, 19 skipped.

---

## Phase 5.2: Convergence UI Controls — Residual Bugfix

### Overview

Phase 5.1 removed the continuous 5-second backend sync callbacks, but three residual bugs remained because the replacement `init_params_from_backend` callback still had structural issues. Phase 5.2 addresses the root causes with targeted fixes.

### Bugs Fixed

| Bug                                      | Symptom                                                                                                    | Root Cause                                                                                                                                                                                          | Fix                                                                                                                               |
|------------------------------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **B-5.5**: `/api/state` no conv params   | `init_params_from_backend` always defaults convergence to `enabled=True`, `threshold=0.001`                | `TrainingState.get_state()` not include `convergence_enabled` or `convergence_threshold` (in `DemoMode`). `/api/state` endpoint -> TrainingState w/o merging DemoMode cnvergence fields.            | Merge `DemoMode.convergence_enabled` and `DemoMode.convergence_threshold` into `/api/state` response                              |
| **B-5.6**: Init callbk every 5s          | `init_params_from_backend` -> `slow-update-interval`, fires / 5s. `if current_applied:`, reqs store=truthy | No `max_intervals` on `slow-update-interval`. If store resets (Dash re-render, edge case), init re-fires, replaces edits w/ `/api/state` defaults                                                   | Add `params-init-interval`, `max_intervals=1` (fire 1s after load). Intvl -> `init_params_from_backend` vs `slow-update-interval` |
| **B-5.7**: "✓ Params applied" msg clears | success state overwritten after clicking Apply                                                             | `track_param_changes` -> `params-status` children. `applied-params-store` update trigger `track_param_changes`, clrs status (no changes), dels `"✓ Parameters applied"` msg from `apply_parameters` | Return `dash.no_update` for `params-status` w/ no changes (keeps status message).                                                 |

### Implementation

#### Step 5.2.1: Include convergence params in `/api/state` (B-5.5)

**File**: `main.py`

Modified the `/api/state` endpoint to merge `convergence_enabled` and `convergence_threshold` from the `DemoMode` instance into the response. Uses `getattr()` with defaults for safety.

**Before**: Returned `training_state.get_state()` which lacks convergence fields.
**After**: Merges `demo.convergence_enabled` and `demo.convergence_threshold` into the state dict before returning.

**Scope note**: Convergence params are only merged for demo backend mode. Service backend (CasCor) has its own parameter management and does not use the convergence UI controls. This is consistent with the Phase 5 design where convergence controls are demo-mode-only.

#### Step 5.2.2: One-shot parameter initialization (B-5.6)

**File**: `frontend/dashboard_manager.py`

1. Added `dcc.Interval(id="params-init-interval", interval=1000, max_intervals=1, n_intervals=0)` — fires exactly once, 1 second after page load.
2. Changed `init_params_from_backend` callback Input from `slow-update-interval` to `params-init-interval`.
3. Retained the `if current_applied:` guard as a safety measure, but `max_intervals=1` is the primary one-shot guarantee.

#### Step 5.2.3: Preserve status message on no-change (B-5.7)

**File**: `frontend/dashboard_manager.py`

Changed `_track_param_changes_handler` to return `dash.no_update` for `params-status` when no changes are detected, instead of `""`. This preserves the existing status message (e.g., `"✓ Parameters applied"`) until the user makes a new change.

### Testing

Tests updated across 6 test files:

| File                                 | Changes                                                                                                                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_apply_button_parameters.py`    | Updated 2 assertions (`status == ""` → `status is dash.no_update`). Added 9 new tests: 4 for `/api/state` convergence params, 5 for convergence apply round-trip scenarios. |
| `test_dashboard_manager.py`          | Updated 2 assertions for no-change status (`""` → `dash.no_update`).                                                                                                        |
| `test_dashboard_manager_95.py`       | Updated 1 assertion for float precision edge case.                                                                                                                          |
| `test_dashboard_manager_handlers.py` | Updated 1 assertion for no-change handler result.                                                                                                                           |
| `test_dashboard_helpers_coverage.py` | Updated 1 assertion for no-change tracking.                                                                                                                                 |

---

## Document History

| Date       | Author      | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|------------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2026-03-17 | Paul Calnon | Initial creation — comprehensive analysis of 8 root causes, comparative analysis, architecture review, phased implementation plan                                                                                                                                                                                                                                                                                                                                                       |
| 2026-03-17 | Paul Calnon | 5 sub-agents validated root causes. RC-3 ratio corrected (1,250×). New bug (reset dimension mismatch). Add Step 1.5. Add Test update Inventory. Target encoding documented.                                                                                                                                                                                                                                                                                                             |
| 2026-03-17 | Paul Calnon | Done w/ Impl — Phase 1 & 2 done. 167/167 tests passing. Final audit by 2 sub-agents: code audit passed all 8 checks (gradients mathematically verified), test audit found no issues.                                                                                                                                                                                                                                                                                                    |
| 2026-03-17 | Paul Calnon | Phase 3 complete — 5 parallel sub-agents (math audit, training dynamics, cascor comparison, numerical stability, algorithm research). MSE gradient math correct. 4 new root causes identified: RC-9 (SGD vs Adam), RC-10 (mini-batch noise undoes retrain), RC-11 (un-normalized correlation), RC-12 (spiral complexity). RC-6 elevated. 4 remediation options documented (4A–4D). Recommended approach: 4B+4C+4D combined (autograd+Adam, simpler spiral, convergence-based addition). |
| 2026-03-18 | Paul Calnon | ~~Phase 4 complete~~ **RETRACTED** — Phase 4 was documented as complete but NOT implemented in the codebase. All 9 steps (4.1–4.9) were marked ✅ but none exist in the actual source code.                                                                                                                                                                                                                                                                                             |
| 2026-03-18 | Paul Calnon | **Full audit** — 5 sub-agents verified the codebase against the plan. Phase 1-2 fixes confirmed. Phase 4 items all missing. Architecture table and line numbers corrected. Test status: 3548 passed, 3 failed (2 pre-existing WS + 1 convergence regression).                                                                                                                                                                                                                           |
| 2026-03-18 | Paul Calnon | **Phase 4 implemented** — All 9 Phase 4 steps applied to codebase. `nn.Linear` + Adam, autograd + Pearson correlation, input normalization, convergence-based cascade, full-batch default, 500-step retrain, backward-compatible properties. 29 new Phase 4 tests. 3579/3580 tests passing (1 pre-existing WS failure).                                                                                                                                                                 |
| 2026-03-18 | Paul Calnon | Phase 5 complete — Convergence Window UI Controls. Checkbox + numeric threshold input added to Training Controls. Full param flow: UI → callbacks → POST /api/set_params → DemoBackend → DemoMode.apply_params. Convergence params in get_current_state(), reset restores defaults, threshold clamped to [0.0001, 0.1]. 18 new unit tests + 52 test updates. Audit: 20/22 pass. 3598/3598 tests passing.                                                                                |
| 2026-03-18 | Paul Calnon | Phase 5.1 complete — Bugfix for convergence UI controls. Fixed 4 bugs: checkbox reverting (B-5.1), threshold resetting (B-5.2), constant meta-parameter refresh (B-5.3), missing section heading (B-5.4). Replaced continuous 5s backend sync with one-time init. Split Training Controls card into "Training Controls" (buttons) and "Training Parameters" (inputs). 3585/3585 tests passing (19 skipped).                                                                             |
| 2026-03-19 | Paul Calnon | Phase 5.2 complete — Residual bugfix for convergence UI controls. Fixed 3 remaining bugs: `/api/state` missing convergence params (B-5.5), init callback firing every 5s instead of once (B-5.6), status message immediately disappearing after Apply (B-5.7). Added `params-init-interval` with `max_intervals=1`, merged DemoMode convergence params into `/api/state`, preserved status on no-change. 9 new tests added.                                                             |

---
