# Juniper Regression Development Roadmap

**Date**: 2026-04-02
**Companion Documents**: `JUNIPER_REGRESSION_ANALYSIS_2026-04-02.md`, `JUNIPER_REGRESSION_REMEDIATION_PLAN_2026-04-02.md` (referenced by name; these companion files were never landed in this repo)

**Author**: Claude Code (Opus 4.6)

---

## Phase 1: Critical Training Pipeline Fix

**Goal**: Restore functional training in juniper-cascor
**Blocks**: All downstream canopy monitoring fixes

### Step 1.1: Fix SharedMemory Premature Cleanup (C-1)

- [ ] **Task 1.1.1**: Remove SharedMemory cleanup from `_execute_parallel_training()` finally block
  - File: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
  - Lines: 2129-2135 — remove `close_and_unlink()` calls from finally
  - Replace with logging statement

- [ ] **Task 1.1.2**: Add SharedMemory cleanup to `_execute_candidate_training()`
  - File: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
  - Wrap method body in try/finally
  - Add cleanup in finally block after both parallel and sequential paths complete

- [ ] **Task 1.1.3**: Verify `candidate_inputs = None` guard (C-2)
  - File: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
  - Line 2716 — confirm guard is present
  - Status: Already verified present

### Step 1.2: Verify Training Pipeline

- [ ] **Task 1.2.1**: Run cascor unit tests
  - Command: `cd juniper-cascor && conda activate JuniperCascor && pytest src/tests/unit/ -v --timeout=60`

- [ ] **Task 1.2.2**: Run cascor integration tests
  - Command: `cd juniper-cascor && pytest src/tests/integration/ -v --timeout=120`

- [ ] **Task 1.2.3**: Manual training verification
  - Start cascor service
  - Initiate training via REST API
  - Verify training proceeds past first epoch
  - Verify multiple hidden units are added
  - Confirm clean shutdown

---

## Phase 2: Cascor Status API Enrichment

**Goal**: Ensure cascor exposes all required fields for canopy consumption

### Step 2.1: Add Network Dimensions to Status (H-3)

- [ ] **Task 2.1.1**: Update `LifecycleManager.get_status()` to include `input_size` and `output_size`
  - File: `juniper-cascor/src/api/lifecycle/manager.py`
  - Method: `get_status()` (line 587)
  - Add: `training_state.setdefault("input_size", self.network.input_size)` when network exists
  - Add: `training_state.setdefault("output_size", self.network.output_size)` when network exists

### Step 2.2: Verify Status API Response

- [ ] **Task 2.2.1**: Test `/v1/training/status` endpoint returns `input_size` and `output_size`
- [ ] **Task 2.2.2**: Test canopy `service_backend.py` correctly extracts dimensions

---

## Phase 3: Canopy Parameter and Status Fixes

**Goal**: Fix parameter initialization and value mapping issues

### Step 3.1: Fix Parameter Mapping (H-4)

- [ ] **Task 3.1.1**: Audit `CascorServiceAdapter.get_canopy_params()` method
  - File: `juniper-canopy/src/backend/cascor_service_adapter.py`
  - Verify all 22 `nn_*`/`cn_*` keys are mapped from cascor network attributes
  - Add missing mappings

### Step 3.2: Fix Convergence Threshold Value Swap (H-5)

- [ ] **Task 3.2.1**: Callback Output ordering verified CORRECT (no swap)
  - Output #6 = `nn-growth-preset-epochs-input`, Output #7 = `nn-growth-convergence-threshold-input`
  - Return indices match: index 6 = `nn_growth_epochs`, index 7 = `nn_growth_conv_thresh`

- [ ] **Task 3.2.2**: Audit `CascorServiceAdapter.get_canopy_params()` for correct `nn_growth_convergence_threshold` mapping
  - File: `juniper-canopy/src/backend/cascor_service_adapter.py`
  - Ensure `nn_growth_convergence_threshold` maps to `network.convergence_threshold`
  - Ensure `nn_growth_preset_epochs` maps to `network.growth_preset_epochs`
  - Add missing mappings if absent

### Step 3.3: Fix Multi-Source Network Info (H-3 canopy side)

- [ ] **Task 3.3.1**: Update `service_backend.py` to check multiple sources for `input_size`/`output_size`
  - File: `juniper-canopy/src/backend/service_backend.py`
  - Use `_first_defined()` pattern to check `ts`, `monitor`, and `raw` dicts

### Step 3.4: Verify Status and Parameters

- [ ] **Task 3.4.1**: Run canopy unit tests
  - Command: `cd juniper-canopy && conda activate JuniperPython && pytest src/tests/unit/ -v --timeout=60`

- [ ] **Task 3.4.2**: Run canopy integration tests
  - Command: `cd juniper-canopy && pytest src/tests/integration/ -v --timeout=120`

---

## Phase 4: Dark Mode and UI Polish

**Goal**: Fix all dark mode styling issues and UI layout problems

### Step 4.1: Candidate Loss Graph Dark Mode (M-1)

- [ ] **Task 4.1.1**: Add `theme` parameter to `_create_candidate_loss_figure()`
  - File: `juniper-canopy/src/frontend/components/candidate_metrics_panel.py`
  - Update graph colors based on theme
  - Update calling callback to pass theme from `theme-state` store

### Step 4.2: Parameters Tab Dark Mode (M-2)

- [ ] **Task 4.2.1**: Add dark mode CSS rules for Parameters tab tables
  - File: `juniper-canopy/src/frontend/assets/dark_mode.css`
  - Target `.dark-mode` scope for all table elements in parameters panel
  - Or add appropriate CSS classes to `parameters_panel.py` table elements

### Step 4.3: Tutorial Tab Dark Mode (M-3)

- [ ] **Task 4.3.1**: Add dark mode CSS rules for Tutorial tab tables
  - File: `juniper-canopy/src/frontend/assets/dark_mode.css`
  - Target Dashboard Components and Parameters Reference tables

### Step 4.4: Decision Boundary Aspect Ratio (M-4)

- [ ] **Task 4.4.1**: Add `scaleanchor`/`scaleratio` to decision boundary plots
  - File: `juniper-canopy/src/frontend/components/decision_boundary.py`
  - Add `yaxis=dict(scaleanchor="x", scaleratio=1)` to figure layout
  - Adjust container style for responsive aspect ratio

### Step 4.5: Dataset View Aspect Ratio (M-5)

- [ ] **Task 4.5.1**: Add `scaleanchor`/`scaleratio` to dataset scatter plots
  - File: `juniper-canopy/src/frontend/components/dataset_plotter.py`
  - Same approach as Decision Boundary

### Step 4.6: Cassandra API URL Fix (M-6)

- [ ] **Task 4.6.1**: Fix `_api_url()` to use config-based base URL
  - File: `juniper-canopy/src/frontend/components/cassandra_panel.py`
  - Replace Flask request context with configuration value
  - Test with both demo and service modes

### Step 4.7: Snapshots Refresh Button Position (M-7)

- [ ] **Task 4.7.1**: Move refresh button to "Available Snapshots" section heading
  - File: `juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py`
  - Use `dbc.Row` with `justify="between"` in card header

### Step 4.8: Verify UI Polish

- [ ] **Task 4.8.1**: Run canopy UI-related tests
- [ ] **Task 4.8.2**: Manual verification of dark mode across all tabs
- [ ] **Task 4.8.3**: Manual verification of aspect ratios

---

## Phase 5: Feature Enhancements (Deferred)

**Goal**: Implement new features requested in the regression report

### Step 5.1: Decision Boundary History/Replay (L-1)

- [ ] **Task 5.1.1**: Add boundary snapshot storage in cascor backend
- [ ] **Task 5.1.2**: Add boundary history API endpoint
- [ ] **Task 5.1.3**: Add slider control to decision boundary component
- [ ] **Task 5.1.4**: Add replay/animation functionality
- [ ] **Task 5.1.5**: Write tests for new functionality

### Step 5.2: Dataset View Enhancements (L-2, L-3, L-4)

- [ ] **Task 5.2.1**: Populate dataset dropdown from juniper-data generators
- [ ] **Task 5.2.2**: Pre-populate dropdown with current dataset
- [ ] **Task 5.2.3**: Rename sidebar section to "Current Dataset"
- [ ] **Task 5.2.4**: Dynamic sidebar fields based on dataset type
- [ ] **Task 5.2.5**: Implement stop-training-on-new-dataset workflow
- [ ] **Task 5.2.6**: Implement network compatibility checking
- [ ] **Task 5.2.7**: Add user prompts for incompatible datasets
- [ ] **Task 5.2.8**: Write tests for new functionality

---

## Phase 6: Validation and Release

### Step 6.1: Full Test Suite Runs

- [ ] **Task 6.1.1**: Run complete cascor test suite
  - Command: `cd juniper-cascor && bash scripts/run_tests.bash`
  - Expected: All tests pass

- [ ] **Task 6.1.2**: Run complete canopy test suite
  - Command: `cd juniper-canopy && bash scripts/run_all_tests.bash`
  - Expected: All tests pass

### Step 6.2: Integration Verification

- [ ] **Task 6.2.1**: Start full stack (cascor + canopy)
- [ ] **Task 6.2.2**: Verify training starts and completes epoch 1+
- [ ] **Task 6.2.3**: Verify canopy status bar shows "Running"
- [ ] **Task 6.2.4**: Verify metrics graphs populate
- [ ] **Task 6.2.5**: Verify network info shows correct values
- [ ] **Task 6.2.6**: Verify parameters show correct values
- [ ] **Task 6.2.7**: Toggle dark mode — verify all tabs
- [ ] **Task 6.2.8**: Verify Cassandra tab loads without error

### Step 6.3: Commit and PR

- [ ] **Task 6.3.1**: Commit cascor changes to feature branch
- [ ] **Task 6.3.2**: Push cascor branch and create PR
- [ ] **Task 6.3.3**: Commit canopy changes to feature branch
- [ ] **Task 6.3.4**: Push canopy branch and create PR
- [ ] **Task 6.3.5**: Worktree cleanup after merge

---

## Timeline Estimates

| Phase | Dependencies | Parallelizable |
|-------|-------------|----------------|
| Phase 1 | None | No (blocks Phase 2-3) |
| Phase 2 | Phase 1 | Partially (cascor-only) |
| Phase 3 | Phase 2 | Yes (canopy changes parallel to Phase 2 verification) |
| Phase 4 | None | Yes (fully independent of Phase 1-3) |
| Phase 5 | Phase 4 | Yes (independent features) |
| Phase 6 | Phase 1-4 | No (requires all fixes) |

**Critical path**: Phase 1 → Phase 2 → Phase 3 → Phase 6
**Parallel track**: Phase 4 (can start immediately)
