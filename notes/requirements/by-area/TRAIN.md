# Requirements — TRAIN

**Area**: training — cascor algorithm, candidates, convergence, model state

**Total entries**: 35

**By status**: proposed=13 | shipped=22

**By priority**: P0=15 | P1=6 | P2=13 | P3=1

**By owner**: ml=19 | cas=15 | can=1

---

### JR-ML-TRAIN-001 — Fix activation function mismatch: use tanh instead of sigmoid in demo mode.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 87-103)

**Detail**:

Tanh critical for CasCor algorithm: outputs ∈ {-1,+1} create binary partitions; sigmoid ∈ {0,1} can produce constant features with zero gradient. Sigmoid mean-shift also biases output layer.

**Notes**:

Root cause RC-1; doc status indicates implementation complete

### JR-CAS-TRAIN-001 — Fix candidate task parameter wiring: use correct dictionary keys (candidate_seed, candidate_epochs, candidate_learning_rate).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 235-273)

### JR-CAS-TRAIN-002 — Fix candidate training runtime errors (method name mismatch, pickling, parameter handling).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 94-122)

**Detail**:

Fix _train_candidate_worker → _train_candidate_unit method call mismatch; add __getstate__/__setstate__ to LogConfig and CascadeCorrelationConfig for multiprocessing pickling support; update CascadeCorrelationNetwork.__getstate__ to exclude log_config.

### JR-ML-TRAIN-002 — Fix drain thread race condition in cascor lifecycle manager for candidate progress monitoring.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 121-142)

**Detail**:

Progress queue drain thread checks for queue before it exists in grow_network(). Fix: deferred queue discovery in drain thread or pre-create queue before original_grow().

**Notes**:

Status marked COMPLETE (Section 1, line 7-8); Phase 1 critical fix

### JR-ML-TRAIN-003 — Fix grow progress bar denominator to use max_hidden_units instead of max_epochs.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 104-118)

**Detail**:

Demo mode passes max_epochs (10000) as progress denominator instead of max_hidden_units (10), causing 0.12% → 0% display. Fix: use max_hidden_units in Canopy progress handler, cap at 100%.

**Notes**:

Phase 1 critical fix; doc status COMPLETE

### JR-CAS-TRAIN-003 — Fix logger pickling error in multiprocessing (BUG-002).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 28-36)

**Detail**:

Enhance CascadeCorrelationNetwork and CascadeCorrelationPlotter __getstate__/__setstate__ methods for pickle support; verify CandidateUnit has pickling support.

### JR-ML-TRAIN-004 — Fix loss function: use MSE on raw output instead of BCE with sigmoid.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 104-117)

**Detail**:

BCE residuals bounded [-1,1]; MSE residuals unbounded. MSE gradient stronger; residual magnitude larger. CasCor candidate training mathematically designed around MSE residuals.

**Notes**:

Root cause RC-2; doc status indicates implementation complete

### JR-CAS-TRAIN-004 — Fix multiprocessing completion logic that can hang indefinitely due to unreliable empty()/qsize() usage.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 59-99)

**Detail**:

Replace unreliable busy-wait loop using Manager queue empty()/qsize() with bounded timeout loop. Add worker liveness checks to detect crashed workers early. Exit immediately when all workers complete.

### JR-CAS-TRAIN-005 — Fix plotting subprocess to use spawn context instead of forkserver for reliable module import in child processes.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 342-386)

### JR-CAS-TRAIN-006 — Fix save_object() method TypeError due to argument count mismatch with _save_root_attributes().

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/PRE-DEPLOYMENT_ROADMAP.md` (lines 200-232)

### JR-CAS-TRAIN-007 — Fix test random state restoration failures (BUG-001).

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 18-26)

### JR-ML-TRAIN-005 — Increase output retraining from 50 mini-batch steps to full-batch training after hidden unit installation.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 118-131)

**Detail**:

Demo: ~1,600 sample evaluations; CasCor: ~2,000,000 (1,250× difference). New hidden unit weight initialized ~0.1; needs ample optimization time. Current 50 steps insufficient (~0.125 total change).

**Notes**:

Root cause RC-3; doc status indicates implementation complete

### JR-ML-TRAIN-006 — Use Adam optimizer instead of vanilla SGD for output training.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 225-242)

**Detail**:

Adam adapts per-parameter effective learning rates using first/second moment estimates. Vanilla SGD shares same lr across all params; new hidden unit columns converge poorly.

**Notes**:

Root cause RC-9; Phase 3 investigation finding; doc status indicates implementation complete

### JR-ML-TRAIN-007 — Use full-batch training between cascade additions instead of mini-batch.

**Status**: shipped  **Priority**: P0  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 243-258)

**Detail**:

Mini-batch between cascades (960 evals) undoes full-batch retrain (40,000 evals). High gradient variance causes random walk of carefully retrained weights. Fix: full-batch for 30 epochs instead of mini-batch.

**Notes**:

Root cause RC-10; Phase 3 finding; ~40× weaker training; doc status indicates implementation complete

### JR-CAN-TRAIN-001 — Single-iteration auto-pause after stop+reset due to cleared _pause_event.

**Status**: proposed  **Priority**: P0  **Category**: TRAIN  **Owner**: can

**Sources**:
- `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` (lines 42-42)

**Detail**:

cascor lifecycle manager leaves _pause_event cleared after reset(). 
Fix: one-line change to clear+set instead of reassign.

**PRs**: PR-5 (cascor fix, ordered first in remediation)

### JR-ML-TRAIN-008 — Derive candidate_pool_phase from phase_detail in Canopy adapter.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 686-709)

**Detail**:

Adapter derives candidate_pool_status but not candidate_pool_phase. One-line fix: map phase_detail to pool phase (Training/Selecting/Idle).

**Notes**:

Phase 2 P1 fix; doc status COMPLETE; simple derivation gap

### JR-ML-TRAIN-009 — Enhance grow iteration callback with top 2 candidate ID and correlation data.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md` (lines 148-167)

**Detail**:

Top candidate info never forwarded from CasCor to Canopy; TrainingResults dataclass contains data but callback does not pass it. Fix: add best_candidate_id, best_candidate_uuid, second_candidate fields to callback signature.

**Notes**:

Phase 2 P1 fix; data already available in TrainingResults; doc status COMPLETE

### JR-CAS-TRAIN-008 — Expand format validation for HDF5 snapshot files.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 73-83)

**Detail**:

Check format name/version; validate required groups and datasets; verify hidden units consistency.

### JR-CAS-TRAIN-009 — Implement hidden units checksums for integrity verification.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 53-61)

### JR-CAS-TRAIN-010 — Implement shape validation for serialized network structure.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/IMPLEMENTATION_CHECKLIST.md` (lines 63-71)

**Detail**:

Implement _validate_shapes() method; validate output layer and hidden units; call from load_network().

### JR-ML-TRAIN-010 — Use Pearson correlation (normalized) instead of raw covariance in candidate training.

**Status**: shipped  **Priority**: P1  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` (lines 259-283)

**Detail**:

Raw covariance scales with residual magnitude; after first hidden unit, residuals shrink, candidate training gradients weaken (~8× decay observed). Pearson normalized by stddev, scale-invariant.

**Notes**:

Root cause RC-11; Phase 3 finding; doc status indicates implementation complete

### JR-CAS-TRAIN-011 — Implement flexible optimizer system supporting Adam, SGD, RMSprop, AdamW.

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

OptimizerConfig dataclass and _create_optimizer() method already exist in codebase.

### JR-CAS-TRAIN-012 — Implement N-best candidate selection (candidates_per_layer configuration).

**Status**: shipped  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/CASCOR_ENHANCEMENTS_ROADMAP.md` (lines 1-50)

**Notes**:

_select_best_candidates() and add_units_as_layer() methods already exist.

### JR-ML-TRAIN-011 — Adam Optimizer Pathology: fix Adam optimizer pathology issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_07_ADAM_OPTIMIZER_PATHOLOGY.md` (lines 1-44)

### JR-ML-TRAIN-012 — Candidate Quality Decay: address candidate quality degradation in long training runs.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_02_CANDIDATE_QUALITY_DECAY.md` (lines 1-40)

### JR-ML-TRAIN-013 — Convergence Timing: optimize convergence detection timing.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_04_CONVERGENCE_TIMING.md` (lines 1-46)

### JR-CAS-TRAIN-013 — Fix validate_training_results None initialization bug in training loop.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 374-378)

**Detail**:

Variable initialized as None; if training loop doesn't execute (e.g. max_epochs=0), debug log crashes with AttributeError on .early_stop.

### JR-ML-TRAIN-014 — Output Weight Initialization: improve output layer weight init.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_05_OUTPUT_WEIGHT_INIT.md` (lines 1-38)

### JR-ML-TRAIN-015 — Phantom Inter-Cascade Training Phase: remove 1-step/epoch phantom training phase.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_01_PHANTOM_TRAINING_PHASE.md` (lines 30-49)

### JR-ML-TRAIN-016 — Post-Reset Desynchronization: fix desync after model reset.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_10_POST_RESET_DESYNC.md` (lines 1-38)

### JR-ML-TRAIN-017 — Residual Variance Collapse: address residual variance collapse in training.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_09_RESIDUAL_VARIANCE_COLLAPSE.md` (lines 1-46)

### JR-ML-TRAIN-018 — Spiral Complexity: limit spiral depth and complexity growth.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_03_SPIRAL_COMPLEXITY.md` (lines 1-50)

### JR-CAS-TRAIN-014 — Support multiple optimizer types via configuration (Adam, SGD, RMSprop, AdamW).

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 749-773)

### JR-ML-TRAIN-019 — Tanh Saturation: address tanh saturation issues.

**Status**: proposed  **Priority**: P2  **Category**: TRAIN  **Owner**: ml

**Sources**:
- `juniper-ml/notes/proposals/PROPOSAL_06_TANH_SATURATION.md` (lines 1-38)

### JR-CAS-TRAIN-015 — Per-instance queue management to avoid cross-instance interference.

**Status**: proposed  **Priority**: P3  **Category**: TRAIN  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md` (lines 1-50)

**Notes**:

Complex refactor; deferred to later phase.

