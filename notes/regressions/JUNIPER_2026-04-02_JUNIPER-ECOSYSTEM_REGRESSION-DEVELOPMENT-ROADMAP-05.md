# Juniper Project: Regression Development Roadmap

**Date**: 2026-04-02
**Reference**: `REGRESSION_ANALYSIS_2026-04-02.md`, `REGRESSION_REMEDIATION_PLAN_2026-04-02.md`
**Author**: Claude Code (Principal Engineer Analysis)

---

## Roadmap Overview

| Phase | Priority | Scope | Est. Effort |
|-------|----------|-------|-------------|
| **Phase 1** | P0 Critical | Cascor training failure fix | Small |
| **Phase 2** | P1/P2 High | Canopy core UI fixes | Medium |
| **Phase 3** | P2 Medium | Data integration & features | Large |
| **Phase 4** | P3 Low | Visual polish & enhancements | Medium |
| **Phase 5** | Validation | Full test suite pass | Medium |

---

## Phase 1: Critical Training Failure Fix (CASCOR-001)

**Priority**: P0 — IMMEDIATE
**Application**: juniper-cascor
**Branch**: `fix/cascor-training-failure-opt5`

### Step 1.1: Fix UnboundLocalError in train_candidate_worker

| Item | Detail |
|------|--------|
| **Issue** | CASCOR-001 (Layer 1) |
| **File** | `src/cascade_correlation/cascade_correlation.py` |
| **Line** | 2714 |
| **Action** | Add `candidate_inputs = None` initialization before `try` block |
| **Tests** | Run existing candidate training tests |
| **Verification** | `grep -n 'candidate_inputs = None' src/cascade_correlation/cascade_correlation.py` |

### Step 1.2: Add defensive SharedMemory fallback in _build_candidate_inputs

| Item | Detail |
|------|--------|
| **Issue** | CASCOR-001 (Layer 2) |
| **File** | `src/cascade_correlation/cascade_correlation.py` |
| **Lines** | 2846-2864 |
| **Action** | Wrap SharedMemory reconstruction in try-except with fallback to legacy tuple path |
| **Tests** | Add unit test for SharedMemory failure fallback |
| **Verification** | Run training end-to-end; verify training completes without crash |

### Step 1.3: Validate fix with full test suite

| Item | Detail |
|------|--------|
| **Action** | Run `cd src/tests && bash scripts/run_tests.bash` |
| **Expected** | All 2926+ tests pass |
| **Verification** | No new test failures |

---

## Phase 2: Canopy Core UI Fixes

**Priority**: P1/P2
**Application**: juniper-canopy
**Branch**: `fix/canopy-regression-ui`

### Step 2.1: Fix tab ordering and labels

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-001 |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 1075-1135 |
| **Action** | Reorder tabs to: metrics, candidates, topology, boundaries, dataset, workers, parameters, snapshots, redis, cassandra, tutorial, about. Fix labels: "Decision Boundary", "Snapshots" |
| **Tests** | Update any tab-order assertions in tests |

### Step 2.2: Fix Cassandra panel API URL construction

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-016 |
| **Files** | `src/frontend/components/cassandra_panel.py`, `redis_panel.py`, `worker_panel.py`, `candidate_metrics_panel.py` |
| **Action** | Replace broken `_api_url()` methods with Flask request-context-aware URL builder. Preferably extract to `BaseComponent`. |
| **Tests** | Verify Cassandra, Redis, Workers tabs load without API URL errors |

### Step 2.3: Fix Snapshots tab naming and layout

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-015 |
| **Files** | `src/frontend/components/hdf5_snapshots_panel.py`, `src/frontend/dashboard_manager.py` |
| **Action** | Rename "HDF5 Snapshots" → "Snapshots" in both tab label and panel header. Move Refresh button to Available Snapshots section. |
| **Tests** | Update label assertions in tests |

### Step 2.4: Fix dark mode for cards and tables

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-017, CANOPY-018, CANOPY-019 |
| **File** | `src/frontend/assets/dark_mode.css` |
| **Action** | Add `.dark-mode .card`, `.dark-mode .card-header`, `.dark-mode .card-body` CSS rules. Fix Plotly empty-state figures to use dark template. |
| **Tests** | Visual verification in dark mode |

### Step 2.5: Fix Network Information data binding

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-005, CANOPY-006 |
| **Files** | `src/main.py` (API endpoint), `src/frontend/dashboard_manager.py` (handler) |
| **Action** | Ensure `/api/status` includes `input_size` and `output_size` from network configuration. Update network info handler to use correct field names. |
| **Tests** | API response schema tests |

### Step 2.6: Fix Decision Boundary and Dataset View aspect ratios

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-010, CANOPY-011 |
| **Files** | `src/frontend/components/decision_boundary.py`, `dataset_plotter.py` |
| **Action** | Replace fixed heights with responsive sizing. Add Plotly `scaleanchor` for 1:1 aspect ratio on scatter plots. |
| **Tests** | Visual verification |

### Step 2.7: Fix Network Topology output nodes

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-009 |
| **Files** | `src/frontend/components/network_visualizer.py`, backend topology endpoint |
| **Action** | Verify cascor network `output_units` value. If binary classification uses 1 sigmoid output, ensure topology returns `output_units: 1`. |
| **Tests** | Topology data validation tests |

---

## Phase 3: Data Integration & Feature Enhancements

**Priority**: P2
**Application**: juniper-canopy
**Branch**: `feat/canopy-dataset-integration`

### Step 3.1: Populate dataset dropdown from juniper-data

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-012 |
| **File** | `src/frontend/components/dataset_plotter.py` |
| **Action** | Add callback to fetch available generators via data adapter and populate dropdown options. Pre-select current dataset. |
| **Dependencies** | juniper-data-client `list_generators()` API |

### Step 3.2: Make dataset sidebar dynamic

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-013 |
| **File** | `src/frontend/dashboard_manager.py` |
| **Action** | Rename "Spiral Dataset" → "Current Dataset". Replace hardcoded spiral fields with dynamic container that updates based on selected dataset type. |
| **Dependencies** | Step 3.1 (dropdown populated) |

### Step 3.3: Implement Generate Dataset workflow

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-014 |
| **Files** | `src/frontend/components/dataset_plotter.py`, `src/backend/data_adapter.py`, `src/main.py` |
| **Action** | Stop training → generate new dataset → display → update distributions → check NN compatibility → prompt user |
| **Dependencies** | Steps 3.1, 3.2 |

### Step 3.4: Sync sidebar parameters with backend

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-003, CANOPY-004 |
| **Files** | `src/frontend/dashboard_manager.py` |
| **Action** | Add callback to fetch actual runtime parameters from cascor backend and update sidebar input fields. Verify Convergence Threshold field mapping. |
| **Dependencies** | CASCOR-001 fixed (training must work for params to be meaningful) |

---

## Phase 4: Visual Polish & Enhancements

**Priority**: P3
**Application**: juniper-canopy
**Branch**: `feat/canopy-visual-polish`

### Step 4.1: Decision boundary replay capability

| Item | Detail |
|------|--------|
| **Issue** | CANOPY-010 (enhancement) |
| **Files** | `src/frontend/components/decision_boundary.py`, backend API |
| **Action** | Add slider/stepper for viewing boundary evolution per hidden node addition. Requires backend to store boundary history. |

### Step 4.2: Learning rate display consistency

| Item | Detail |
|------|--------|
| **Issue** | Part of CANOPY-007 |
| **Files** | `src/frontend/components/metrics_panel.py`, `dashboard_manager.py` |
| **Action** | Ensure learning rate in metrics graph heading matches sidebar value. Both should reflect actual runtime value. |

---

## Phase 5: Validation & Release

### Step 5.1: Run juniper-cascor full test suite

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
conda activate JuniperCascor
cd src/tests && bash scripts/run_tests.bash
```

**Expected**: All 2926+ tests pass.

### Step 5.2: Run juniper-canopy full test suite

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
conda activate JuniperPython
bash util/run_all_tests.bash
```

**Expected**: All 4184+ tests pass.

### Step 5.3: Manual verification

1. Start juniper-data service
2. Start juniper-cascor service
3. Start juniper-canopy in service mode
4. Verify training runs to completion without crash
5. Verify all tabs display correctly in correct order
6. Verify dark mode on all tabs
7. Verify Cassandra/Redis tabs load without errors
8. Verify network topology shows correct output node count

### Step 5.4: Commit, push, and create PRs

| Application | Branch | PR Target |
|-------------|--------|-----------|
| juniper-cascor | `fix/cascor-training-failure-opt5` | `main` |
| juniper-canopy | `fix/canopy-regression-ui` | `main` |
| juniper-canopy | `feat/canopy-dataset-integration` | `main` (after regression fix merged) |
| juniper-canopy | `feat/canopy-visual-polish` | `main` (after dataset integration merged) |

---

## Execution Order

```
Phase 1 (CASCOR-001)  ──────────────────────────────────────> PR #1
    │
    ├── Phase 2 (Canopy Core UI) ───────────────────────────> PR #2
    │       │
    │       ├── Phase 3 (Data Integration) ─────────────────> PR #3
    │       │       │
    │       │       └── Phase 4 (Visual Polish) ────────────> PR #4
    │       │
    │       └── Phase 5 (Validation) ──── continuous ──────>
    │
    └── Phase 5 (Cascor Validation) ─── immediate ────────>
```

Phase 1 is the critical path. Everything else can proceed in parallel but Phase 3 depends on Phase 2 completion and Phase 4 depends on Phase 3.
