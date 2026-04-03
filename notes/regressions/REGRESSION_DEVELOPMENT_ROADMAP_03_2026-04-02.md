# Juniper Project — Regression Remediation Development Roadmap

**Date**: 2026-04-02
**Author**: Automated Analysis (Amp)
**Status**: Planning Complete
**Scope**: juniper-cascor, juniper-canopy applications

---

## Overview

This roadmap addresses all identified regressions in the Juniper project across two applications: juniper-cascor (backend neural network) and juniper-canopy (monitoring dashboard). Work is organized into 5 phases by priority and dependency order.

---

## Phase 1: Critical Training Fixes (P0) — BLOCKING

**Goal**: Restore functional training in both cascor (production) and canopy (demo mode)

### Step 1.1: Fix Canopy Demo Training Deadlock (P0-1)
- **Task**: Fix non-reentrant Lock deadlock in `demo_mode.py`
- **File**: `juniper-canopy/src/demo_mode.py` line ~1126-1132
- **Change**: Move `_update_training_status()` call outside the `with self._lock:` block
- **Approach**:
  ```python
  # Before (deadlock):
  with self._lock:
      if self.current_epoch >= self.max_epochs:
          self.state_machine.mark_completed()
          self._update_training_status()  # DEADLOCK: acquires same lock
          self.is_running = False
          return

  # After (fixed):
  phase1_done = False
  with self._lock:
      if self.current_epoch >= self.max_epochs:
          self.state_machine.mark_completed()
          self.is_running = False
          phase1_done = True
  if phase1_done:
      self._update_training_status()
      return
  ```
- **Risk**: Low — straightforward lock ordering fix
- **Verification**: `cd src && pytest tests/unit/test_phase6_implementation.py -v`

### Step 1.2: Fix Cascor SharedMemory Resource Leaks (OPT-5)
- **Task**: Fix premature cleanup of SharedMemory blocks during persistent worker pool operation
- **File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
- **Changes**:
  1. Don't unlink SharedMemory in the parallel training `finally` block while persistent workers may still reference it
  2. Implement reference-counted SharedMemory lifecycle management
  3. Close shared memory handles in workers after tensor reconstruction (already done via `shm_handle.close()`)
  4. Clean up SharedMemory blocks only during pool shutdown or at process exit
- **Approach A (Recommended)**: Deferred cleanup — accumulate used blocks, clean up at start of next round
- **Approach B**: Reference counting with a shared counter in the SharedMemory metadata
- **Risk**: Medium — requires careful synchronization between main process and workers
- **Verification**: Run cascor training with `CASCOR_LOG_LEVEL=DEBUG` and check for resource tracker warnings

### Step 1.3: Fix Canopy Demo Training Algorithmic Mismatches (P0-2)
- **Task**: Restructure `_training_loop()` to match CasCor phase-based training
- **File**: `juniper-canopy/src/demo_mode.py`
- **Changes**:
  1. Replace single-step-per-epoch with configurable `OUTPUT_STEPS_PER_EPOCH` (recommended: 50)
  2. Replace loss-stagnation cascade trigger with correlation-threshold-based trigger
  3. Compute residual error AFTER output convergence, not before retrain
  4. Remove artificial loss manipulation (lines 871-872)
  5. Increase output retrain budget from 500 to 1000 steps
- **Files to add constants**: `juniper-canopy/src/canopy_constants.py`
- **Risk**: High — significant restructuring of the training loop; requires thorough testing
- **Verification**:
  - Run demo mode and verify loss decreases over epochs
  - Verify cascade additions spaced 20+ epochs apart
  - Verify >90% accuracy on spiral dataset within 300 epochs
  - Full test suite: `cd src && pytest tests/ -v`

---

## Phase 2: High-Priority UI Fixes (P1)

**Goal**: Fix major display/data issues visible to users

### Step 2.1: Fix Tab Ordering
- **Task**: Reorder tabs to match specification
- **File**: `juniper-canopy/src/frontend/dashboard_manager.py` lines 1073-1134
- **Required order**: Training Metrics, Candidate Metrics, Network Topology, Decision Boundary, Dataset View, Workers, Parameters, HDF5 Snapshots, Redis, Cassandra, Tutorial, About
- **Also fix**: "Decision Boundaries" → "Decision Boundary" (line 1092)
- **Risk**: Low
- **Effort**: 15 minutes

### Step 2.2: Fix Network Information Display
- **Task**: Ensure network info panel populates with correct values
- **File**: `juniper-canopy/src/backend/demo_backend.py` lines 88-114
- **Changes**: Verify `get_status()` returns correct `input_size`, `output_size` from the mock network
- **Risk**: Low
- **Effort**: 30 minutes

### Step 2.3: Fix Convergence Threshold Value Population
- **Task**: Fix convergence threshold showing epochs value instead of threshold
- **File**: `juniper-canopy/src/frontend/dashboard_manager.py` — callback for `nn-growth-convergence-threshold-input`
- **Changes**: Audit callback mappings to ensure correct input IDs are used
- **Risk**: Low
- **Effort**: 1 hour

### Step 2.4: Fix Parameter Sidebar Defaults
- **Task**: Update sidebar parameter values from running training state
- **File**: `juniper-canopy/src/frontend/dashboard_manager.py`
- **Changes**: Add callback to update sidebar inputs from API training state
- **Risk**: Medium — need to avoid circular callbacks
- **Effort**: 2 hours

### Step 2.5: Fix Learning Rate Mismatch
- **Task**: Ensure learning rate is consistent between graph heading and sidebar
- **Files**: `juniper-canopy/src/frontend/components/training_metrics.py`, dashboard_manager.py
- **Risk**: Low
- **Effort**: 30 minutes

### Step 2.6: Fix Cassandra Tab API URL Error
- **Task**: Fix API URL construction in CassandraPanel
- **File**: `juniper-canopy/src/frontend/components/cassandra_panel.py` line 99-113
- **Risk**: Low
- **Effort**: 15 minutes

### Step 2.7: Rename HDF5 Snapshots Tab to "Snapshots"
- **Task**: Update tab label
- **File**: `juniper-canopy/src/frontend/dashboard_manager.py` line 1102
- **Risk**: Low
- **Effort**: 5 minutes

---

## Phase 3: Dark Mode Styling Fixes (P3)

**Goal**: Fix all remaining dark mode styling issues

### Step 3.1: Candidate Training Loss Graph Background
- **File**: `juniper-canopy/src/frontend/components/candidate_metrics_panel.py`
- **Change**: Set plot background to transparent or dark theme colors

### Step 3.2: Parameters Tab Table Background
- **File**: `juniper-canopy/src/frontend/components/parameters_panel.py`
- **Change**: Apply dark mode CSS classes to Meta Parameters tables

### Step 3.3: Tutorial Tab Table Background
- **File**: `juniper-canopy/src/frontend/components/tutorial_panel.py`
- **Change**: Apply dark mode CSS classes to Dashboard Components and Parameters Reference tables

**Risk**: Low for all
**Effort**: 1-2 hours total

---

## Phase 4: Feature Enhancements (P2)

**Goal**: Implement missing features and improve UX

### Step 4.1: Decision Boundary Aspect Ratio
- **File**: `juniper-canopy/src/frontend/components/decision_boundary.py`
- **Change**: Set CSS `height` and `aspect-ratio` on visualization container

### Step 4.2: Decision Boundary History Replay
- **Files**: `juniper-canopy/src/demo_mode.py`, `decision_boundary.py`
- **Changes**:
  1. Store decision boundary snapshot at each hidden node addition
  2. Add slider control for navigating boundary evolution
  3. Add replay animation functionality

### Step 4.3: Dataset View Aspect Ratio
- **File**: `juniper-canopy/src/frontend/components/dataset_plotter.py`
- **Change**: Same approach as Step 4.1

### Step 4.4: Dataset View Dynamic Population
- **Files**: `juniper-canopy/src/frontend/components/dataset_plotter.py`, `dashboard_manager.py`
- **Changes**:
  1. Query juniper-data `/v1/generators` for available datasets
  2. Pre-populate dropdown with current dataset
  3. Dynamic field rendering based on selected generator type

### Step 4.5: Dataset View Section Heading
- **File**: `juniper-canopy/src/frontend/dashboard_manager.py`
- **Change**: "Spiral Dataset" → "Current Dataset"

### Step 4.6: Generate Dataset Workflow
- **Files**: `juniper-canopy/src/frontend/dashboard_manager.py`, `demo_mode.py`
- **Changes**: Implement stop → generate → display → compatibility check workflow

### Step 4.7: HDF5 Snapshots Tab Refresh Button Relocation
- **File**: `juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py`
- **Change**: Move refresh button to Available Snapshots section heading

---

## Phase 5: Cascor HDF5 Serialization (P2)

**Goal**: Fix HDF5 save/load errors

### Step 5.1: Fix Buffer API Error
- **File**: `juniper-cascor/src/snapshots/snapshot_serializer.py`
- **Change**: Ensure all objects passed to HDF5 writer support buffer protocol

### Step 5.2: Fix Missing Random Group
- **File**: `juniper-cascor/src/snapshots/snapshot_serializer.py`
- **Change**: Add `random` group to HDF5 serialization format

---

## Timeline Estimate

| Phase | Priority | Effort | Dependencies |
|-------|----------|--------|-------------|
| Phase 1 | P0 | 3-5 days | None |
| Phase 2 | P1 | 2-3 days | Phase 1 (partially) |
| Phase 3 | P3 | 0.5 day | None |
| Phase 4 | P2 | 3-5 days | Phase 1, Phase 2 |
| Phase 5 | P2 | 1-2 days | None |

**Total estimated effort**: 10-16 days

---

## Verification Checklist

- [ ] Canopy demo training runs without deadlock
- [ ] Canopy demo training shows decreasing loss and increasing accuracy
- [ ] Cascade additions occur at appropriate intervals
- [ ] Tab ordering matches specification
- [ ] Network info panel shows correct values
- [ ] All dark mode tables render with dark background
- [ ] Decision boundary and dataset views have correct aspect ratio
- [ ] All Canopy tests pass: `cd juniper-canopy/src && pytest tests/ -v`
- [ ] All Cascor tests pass: `cd juniper-cascor/src/tests && bash scripts/run_tests.bash`
- [ ] No resource tracker warnings during cascor training
- [ ] HDF5 save/load operations work correctly

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Training loop restructuring introduces new bugs | High | High | Comprehensive test suite; compare demo output with reference implementation |
| SharedMemory fixes cause performance regression | Medium | Medium | Benchmark before/after; keep OPT-5 path with improved lifecycle |
| Tab reordering breaks sidebar context switching | Low | Medium | Test all tabs after reordering; verify TAB_SIDEBAR_CONFIG mapping |
| Dark mode CSS conflicts with component libraries | Low | Low | Test in both light and dark modes |
