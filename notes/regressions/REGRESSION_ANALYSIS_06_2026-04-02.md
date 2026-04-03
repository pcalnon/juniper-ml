# Juniper Canopy — Comprehensive Regression Analysis

**Date**: 2026-04-02
**Author**: Automated Analysis (Amp)
**Status**: Analysis Complete
**Scope**: juniper-canopy application

---

## Executive Summary

The juniper-canopy application has 25+ distinct issues across 5 categories: training system failures, UI layout/ordering, dark mode styling, data flow/population, and feature gaps. The most critical issues are the demo training deadlock (P0) and the algorithmic mismatches causing training stalls (P0). UI issues range from P1 (incorrect tab ordering, broken data display) to P3 (cosmetic styling).

---

## Issue Catalog

### P0 — Critical (Blocks All Functionality)

#### P0-1: Demo Training Loop Deadlock

- **Symptoms**: Training thread hangs indefinitely; `thread.join(timeout=90)` times out; Status shows "Failed"
- **Root Cause**: Non-reentrant `threading.Lock()` used in `_training_loop()`. At line ~1126-1132, `_update_training_status()` is called from inside a `with self._lock:` block. `_update_training_status()` itself acquires `self._lock` (line 624), causing permanent deadlock.
- **Files**: `src/demo_mode.py` lines 624, 1126-1132
- **Fix**: Move `_update_training_status()` call outside the lock block, or change to `threading.RLock()`
- **Status**: Documented in `notes/FAILING_TESTS_35_ANALYSIS_2026-04-02.md`

#### P0-2: Training Stall After First Hidden Unit (5 Algorithmic Mismatches)

- **Symptoms**: Training progress stops without errors; loss plateaus; cascade units added too frequently without improvement
- **Root Causes** (from `notes/ROOT_CAUSE_PROPOSAL_TRAINING_STALL.md`):
  1. **Single-step-per-epoch** vs reference's 1000-step phase-based training
  2. **Output weight warm-start** with only 500-step retrain vs reference's 1000-step retrain
  3. **Loss stagnation trigger** (10-epoch window) vs reference's correlation threshold trigger
  4. **Stale residual error** — candidates trained against residual computed before output retrain
  5. **Artificial loss manipulation** — `current_loss *= 1.5` after cascade addition corrupts metrics
- **Files**: `src/demo_mode.py` lines 681-713, 751-780, 816-872
- **Fix**: Restructure training loop to match CasCor phase-based architecture

### P1 — High (Major Functionality/Display Issues)

#### P1-1: Tab Ordering Incorrect

- **Symptoms**: Tabs appear in wrong order in the dashboard
- **Current Order**: Training Metrics, Candidate Metrics, Network Topology, Decision Boundaries, Dataset View, HDF5 Snapshots, Redis, Cassandra, Workers, About, Parameters, Tutorial
- **Required Order**: Training Metrics, Candidate Metrics, Network Topology, Decision Boundary, Dataset View, Workers, Parameters, HDF5 Snapshots, Redis, Cassandra, Tutorial, About
- **Files**: `src/frontend/dashboard_manager.py` lines 1073-1134
- **Fix**: Reorder the `dbc.Tab()` elements in the `dbc.Tabs()` component

#### P1-2: Network Information Shows All Zeros

- **Symptoms**: Input Nodes, Output Nodes, and all detail fields show 0
- **Root Cause**: The `/api/status` endpoint returns `input_size` and `output_size` from `network.input_size` / `network.output_size` (demo_backend.py line 104-105), but the `_update_network_info_handler` in dashboard_manager.py (line 2198) accesses `status.get("input_size", 0)`. If the network hasn't been initialized or `get_current_state()` returns incomplete data, these default to 0.
- **Files**: `src/backend/demo_backend.py` lines 88-114, `src/frontend/dashboard_manager.py` lines 2183-2256

#### P1-3: Training Metrics — Loss Graph Incorrect, Accuracy Graph Empty

- **Symptoms**: Training loss over time graph displays incorrectly; accuracy graph shows no data
- **Root Cause**: The demo training stall (P0-2) means metrics stop updating. Additionally, the artificial loss manipulation (P0-2 mismatch 5) creates false spikes.
- **Files**: `src/demo_mode.py`, `src/frontend/components/training_metrics.py`

#### P1-4: Convergence Threshold Shows Wrong Value

- **Symptoms**: Left menu, Neural Growth Triggers, Convergence Threshold value is filled with the Number of Epochs field value
- **Root Cause**: Likely a Dash callback issue where the wrong Input ID is mapped to the Convergence Threshold output, or the values are being cross-populated
- **Files**: `src/frontend/dashboard_manager.py` — callback mapping for `nn-growth-convergence-threshold-input` (line 699)

#### P1-5: Left Menu Network Parameters Show Constants Defaults

- **Symptoms**: Neural Network sub-section values all appear to be from defaults in constants class rather than reflecting the running network's actual parameters
- **Root Cause**: The sidebar parameter fields are initialized with `TrainingConstants.DEFAULT_*` values and never updated from the running training state
- **Files**: `src/frontend/dashboard_manager.py`, `src/canopy_constants.py`

#### P1-6: Learning Rate Mismatch

- **Symptoms**: Learning rate in graph section heading differs from left menu Neural Network section
- **Root Cause**: Two different sources for the value — the graph heading reads from API state, the sidebar reads from the input field default
- **Files**: `src/frontend/components/training_metrics.py`, `src/frontend/dashboard_manager.py`

#### P1-7: Candidate Metrics Tab — All Data Missing

- **Symptoms**: Progress bar stalled, Pool Details empty, Pool Training Metrics all zeros, Loss graph empty
- **Root Cause**: Cascading effect of P0-2 (training stall). No candidate training data flows to the UI when training is stuck.
- **Files**: `src/frontend/components/candidate_metrics_panel.py`

#### P1-8: Network Topology — Output Node Count Discrepancy

- **Symptoms**: Two output nodes shown; user expects one
- **Root Cause**: The real cascor uses `output_size = _SPIRAL_PROBLEM_NUM_SPIRALS = 2` (2-class classification). The demo uses `output_size=1`. If user is monitoring real cascor, 2 outputs is architecturally correct for the spiral problem. If monitoring demo, the demo correctly shows 1. The discrepancy is between the user's expectation and the actual network architecture.
- **Files**: `src/backend/demo_backend.py` lines 158-170, cascor `constants_problem.py` line 862
- **Note**: May need clarification — if the network specification says 1 output, the constants need updating

#### P1-9: Cassandra Tab — API URL Error

- **Symptoms**: Error message displayed indicating an API URL problem
- **Root Cause**: The `_api_url()` method (cassandra_panel.py line 113) strips leading `/` and returns relative path like `api/v1/cassandra/status`. This may not resolve correctly depending on the Dash/FastAPI routing configuration.
- **Files**: `src/frontend/components/cassandra_panel.py` line 99-113

### P2 — Medium (Feature Gaps / Enhancements)

#### P2-1: Decision Boundary — Aspect Ratio Issue

- **Symptoms**: Visualization stretches width without adjusting height
- **Fix**: Set appropriate CSS height on the display container to maintain native aspect ratio
- **Files**: `src/frontend/components/decision_boundary.py`

#### P2-2: Decision Boundary — Missing Hidden Node History Replay

- **Symptoms**: Cannot view boundary evolution per hidden node; no replay functionality
- **Fix**: Store boundary snapshots at each hidden node addition; add slider/controls for replay
- **Files**: `src/frontend/components/decision_boundary.py`, `src/demo_mode.py`

#### P2-3: Dataset View — Aspect Ratio Issue

- **Symptoms**: Same as P2-1 but for dataset scatter plot
- **Files**: `src/frontend/components/dataset_plotter.py`

#### P2-4: Dataset View — Dropdown Not Populated

- **Symptoms**: Dataset dropdown not populated with available generators from juniper-data
- **Fix**: Query juniper-data `/v1/generators` endpoint to populate dropdown
- **Files**: `src/frontend/components/dataset_plotter.py`

#### P2-5: Dataset View — Dropdown Not Pre-populated

- **Symptoms**: Current dataset not pre-selected in dropdown
- **Files**: `src/frontend/components/dataset_plotter.py`

#### P2-6: Dataset View — Section Heading Not Generic

- **Symptoms**: Left menu shows "Spiral Dataset" instead of generic "Current Dataset"
- **Files**: `src/frontend/dashboard_manager.py`

#### P2-7: Dataset View — Fields Don't Adapt to Dataset Type

- **Symptoms**: Parameters section always shows spiral-specific fields regardless of dataset
- **Fix**: Dynamic field rendering based on selected dataset generator
- **Files**: `src/frontend/dashboard_manager.py`

#### P2-8: Dataset View — Generate Dataset Button Incomplete

- **Symptoms**: Clicking Generate Dataset doesn't stop training, update display, or handle compatibility
- **Fix**: Implement full workflow: stop training → generate → display → compatibility check
- **Files**: `src/frontend/dashboard_manager.py`, `src/demo_mode.py`

#### P2-9: HDF5 Snapshots Tab — Rename to "Snapshots"

- **Files**: `src/frontend/dashboard_manager.py` line 1102

#### P2-10: HDF5 Snapshots Tab — Move Refresh Button

- **Symptoms**: Refresh button and status message should be in Available Snapshots section heading
- **Files**: `src/frontend/components/hdf5_snapshots_panel.py`

### P3 — Low (Cosmetic/Styling)

#### P3-1: Candidate Training Loss Graph — White Background in Dark Mode

- **Files**: `src/frontend/components/candidate_metrics_panel.py`

#### P3-2: Parameters Tab — White Background in Dark Mode

- **Symptoms**: Meta Parameters tables show white background
- **Files**: `src/frontend/components/parameters_panel.py`

#### P3-3: Tutorial Tab — White Background in Dark Mode

- **Symptoms**: Dashboard Components and Parameters Reference tables show white background
- **Files**: `src/frontend/components/tutorial_panel.py`

#### P3-4: Decision Boundary Tab Label

- **Symptoms**: Label says "Decision Boundaries" (plural), should be "Decision Boundary"
- **Files**: `src/frontend/dashboard_manager.py` line 1092

---

## Files Affected Summary

| File | Issues |
|------|--------|
| `src/demo_mode.py` | P0-1, P0-2, P2-2, P2-8 |
| `src/frontend/dashboard_manager.py` | P1-1, P1-2, P1-4, P1-5, P1-6, P2-6, P2-7, P2-9, P3-4 |
| `src/frontend/components/training_metrics.py` | P1-3, P1-6 |
| `src/frontend/components/candidate_metrics_panel.py` | P1-7, P3-1 |
| `src/frontend/components/network_visualizer.py` | P1-8 |
| `src/frontend/components/cassandra_panel.py` | P1-9 |
| `src/frontend/components/decision_boundary.py` | P2-1, P2-2 |
| `src/frontend/components/dataset_plotter.py` | P2-3, P2-4, P2-5 |
| `src/frontend/components/hdf5_snapshots_panel.py` | P2-10 |
| `src/frontend/components/parameters_panel.py` | P3-2 |
| `src/frontend/components/tutorial_panel.py` | P3-3 |
| `src/backend/demo_backend.py` | P1-2, P1-8 |
| `src/canopy_constants.py` | P1-5 |

---

## Dependencies and Fix Ordering

1. **P0-1 (Deadlock)** must be fixed first — everything else depends on training being functional
2. **P0-2 (Training stall)** is next — metrics, graphs, and candidate data all depend on training producing data
3. **P1-1 (Tab ordering)** is independent and can be fixed in parallel
4. **P1-2 to P1-6** (data display issues) should be addressed after P0-2 since some may self-resolve
5. **P2-* (feature gaps)** should be addressed after P0/P1 fixes
6. **P3-* (styling)** can be addressed last, independently

---

## Verification Plan

1. Fix P0-1 → run demo mode → verify training thread starts and doesn't hang
2. Fix P0-2 → run demo mode → verify loss decreases monotonically, accuracy improves
3. Fix P1-1 → verify tab order visually in browser
4. Run full test suite: `cd src && pytest tests/ -v`
5. Verify dark mode styling across all affected tabs
6. Verify network info panel populates with correct values
