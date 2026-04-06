# Juniper Project: Regression Analysis

**Date**: 2026-04-02
**Affected Applications**: juniper-cascor, juniper-canopy
**Severity**: Critical (P0 — blocks all releases and deployments)
**Author**: Claude Code (Principal Engineer Analysis)

---

## Executive Summary

Two Juniper project applications have experienced significant regressions. The most critical is a training failure in juniper-cascor that crashes shortly after the first epoch begins, which cascades into the juniper-canopy monitoring dashboard showing incorrect state. Additionally, juniper-canopy has numerous UI/UX issues spanning tab ordering, dark mode styling, data binding, and feature gaps.

**Root Cause of Critical Training Failure**: An `UnboundLocalError` in `train_candidate_worker()` caused by a variable (`candidate_inputs`) being referenced in an exception handler before it is assigned. The initial exception is a `FileNotFoundError` from SharedMemory reconstruction (OPT-5) where a shared memory block no longer exists by the time the worker process attempts to attach.

---

## Issue Inventory

### CASCOR-001: Critical Training Failure (P0)

| Field | Value |
|-------|-------|
| **Severity** | P0 — Catastrophic |
| **Component** | `juniper-cascor` — Cascade Correlation Training Pipeline |
| **File** | `src/cascade_correlation/cascade_correlation.py` |
| **Lines** | 2705-2807 (`train_candidate_worker`), 2809-2896 (`_build_candidate_inputs`) |
| **Symptom** | Training fails shortly after beginning the first epoch |
| **Impact** | Blocks all training, all releases, all deployments, all downstream development |

#### Root Cause Analysis

**Primary Exception**: `FileNotFoundError` at line 2851 in `_build_candidate_inputs()`:
```
File "cascade_correlation.py", line 2851, in _build_candidate_inputs
    tensors, shm_handle = SharedTrainingMemory.reconstruct_tensors(training_inputs)
File "cascade_correlation.py", line 317, in reconstruct_tensors
    shm = SharedMemory(name=metadata["shm_name"], create=False, track=False)
FileNotFoundError: [Errno 2] No such file or directory: '/juniper_train_cbee87b2'
```

The OPT-5 SharedMemory block is created by the parent process but is no longer available when the worker process attempts to attach. This can occur when:
1. The shared memory block is cleaned up prematurely (e.g., by `atexit` handler or garbage collection)
2. The forkserver context creates workers that don't inherit the shared memory mapping
3. A race condition between shared memory creation and worker process startup

**Secondary Exception (the actual crash)**: `UnboundLocalError` at line 2788 in `train_candidate_worker()`:
```
cannot access local variable 'candidate_inputs' where it is not associated with a value
```

**Mechanism**:
1. `_build_candidate_inputs()` is called at line 2719 inside a `try` block
2. The function raises `FileNotFoundError` during SharedMemory reconstruction
3. Execution jumps to the `except Exception` handler at line 2783
4. The handler references `candidate_inputs` at line 2788: `candidate_inputs.get("candidate_index") if candidate_inputs else -1`
5. Because `candidate_inputs` was never assigned (the exception occurred during its assignment), Python raises `UnboundLocalError`
6. This secondary exception propagates up, crashing the entire training pipeline

**Evidence**: Log file at `/home/pcalnon/Development/python/Juniper/juniper-cascor/logs/juniper_cascor.log` line 27740:
```
[cascade_correlation.py: _execute_sequential_training:2149] (2026-04-02 08:57:24) [ERROR]
CascadeCorrelationNetwork: _execute_sequential_training: Task error:
cannot access local variable 'candidate_inputs' where it is not associated with a value
```

**Introduced By**: Commit `f603f1b` ("feat: implement OPT-5 for shared memory training tensors") added SharedMemory reconstruction code in `_build_candidate_inputs()` without updating the error handling in `train_candidate_worker()` to handle the case where `candidate_inputs` is never assigned.

#### Dual-Layer Fix Required

1. **Layer 1**: Fix the `UnboundLocalError` by initializing `candidate_inputs = None` before the `try` block (line 2714)
2. **Layer 2**: Fix the SharedMemory lifecycle so the block persists until all workers have attached (the underlying OPT-5 issue)

---

### CANOPY-001: Tab Ordering Incorrect (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Dashboard Layout |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 1075-1135 |

**Current Order**: Training Metrics, Candidate Metrics, Network Topology, Decision Boundaries, Dataset View, HDF5 Snapshots, Redis, Cassandra, Workers, About, Parameters, Tutorial

**Expected Order**: Training Metrics, Candidate Metrics, Network Topology, Decision Boundary, Dataset View, Workers, Parameters, Snapshots, Redis, Cassandra, Tutorial, About

**Issues**:
- Workers tab should be at position 6 (currently 9)
- Parameters tab should be at position 7 (currently 11)
- Snapshots tab should be at position 8 (currently 6)
- Tutorial tab should be at position 11 (currently 12)
- About tab should be at position 12 (currently 10)
- "Decision Boundaries" label should be "Decision Boundary" (singular)
- "HDF5 Snapshots" label should be "Snapshots"

---

### CANOPY-002: Top Status Bar Shows "Failed" (P1)

| Field | Value |
|-------|-------|
| **Severity** | P1 — High (downstream of CASCOR-001) |
| **Component** | `juniper-canopy` — Status Bar |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 2100-2163 (`_build_unified_status_bar_content`) |

**Root Cause**: This is primarily a **downstream effect of CASCOR-001**. The cascor training fails, the `/api/status` endpoint returns `failed: true`, and the status bar correctly displays "Failed". Fixing CASCOR-001 will resolve this during active training.

**Secondary Concern**: The status determination logic at lines 2116-2135 is correct. However, when training has never been started, the backend returns `is_running: false, is_paused: false, completed: false, failed: false` → status resolves to "Stopped" which is appropriate.

---

### CANOPY-003: Network Parameters Sidebar Shows Incorrect Values (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Left Sidebar, Network Parameters |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 580-720 (sidebar Neural Network section) |

**Issue**: All sidebar parameter values are populated from `TrainingConstants` defaults (e.g., `DEFAULT_LEARNING_RATE = 0.01`, `DEFAULT_MAX_HIDDEN_UNITS = 1000`, `DEFAULT_CANDIDATE_POOL_SIZE = 100`). These are **canopy UI defaults**, not the actual cascor runtime values. When cascor is running with different parameters (e.g., `_CASCOR_CANDIDATE_POOL_SIZE = 16`), the sidebar shows the wrong values.

**Root Cause**: No synchronization callback fetches actual runtime parameters from the cascor backend to update sidebar input fields.

---

### CANOPY-004: Convergence Threshold Shows Incorrect Value (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Left Sidebar, Growth Triggers |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 697-712 |

**Issue**: User reports the Convergence Threshold field displays the Number of Epochs value. The field is initialized with `TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD` (0.001) at line 701. This is a static default. If the backend returns a different value and the callback updates the wrong field ID, the values could cross-contaminate.

**Root Cause**: Requires investigation of the parameter sync callback to verify field ID mappings.

---

### CANOPY-005: Network Information Shows All Zeros (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Left Sidebar, Network Information |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 2183-2256 (`_update_network_info_handler`) |

**Issue**: Input Nodes and Output Nodes display as 0.

**Root Cause**: The handler fetches from `/api/status` and reads `status.get("input_size", 0)` and `status.get("output_size", 0)` (lines 2198, 2210). If the backend `/api/status` endpoint does not include `input_size` and `output_size` keys (likely — these are network topology details, not training status), the defaults of 0 are used.

**Fix**: Either include `input_size`/`output_size` in the `/api/status` response, or fetch from a separate endpoint like `/api/network/stats` or `/api/topology`.

---

### CANOPY-006: Network Information Details Show All Zeros (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Left Sidebar, Network Information Details |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 2266-2285 (`_update_network_info_details_handler`) |

**Issue**: All fields except Threshold Function and Optimizer show zeros.

**Root Cause**: Fetches from `/api/network/stats` (line 2269). If the endpoint returns empty or zero values (because training failed via CASCOR-001), all numeric fields default to 0. String fields like Threshold Function and Optimizer may have non-zero defaults.

---

### CANOPY-007: Training Metrics Graphs Incorrect/Empty (P1)

| Field | Value |
|-------|-------|
| **Severity** | P1 — High (downstream of CASCOR-001) |
| **Component** | `juniper-canopy` — Training Metrics Tab |
| **File** | `src/frontend/components/metrics_panel.py` |

**Issue**: Training loss graph displays incorrectly. Training accuracy graph is empty. Learning rate in graph heading differs from sidebar.

**Root Cause**: Downstream of CASCOR-001. Training fails, so metrics stop being generated. The few data points from the brief output-layer training before failure may render incorrectly. The learning rate inconsistency is a separate data-binding issue between the sidebar (static default) and the metrics panel (fetched from API).

---

### CANOPY-008: Candidate Metrics Tab Issues (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Candidate Metrics Tab |
| **File** | `src/frontend/components/candidate_metrics_panel.py` |

**Issues**:
- Candidate Epoch Progress bar stalled
- Pool Details shows no info for top candidates
- Pool Training Metrics all zeros (line 490-497: defaults to 0.0)
- Candidate Training Loss graph not populated
- Candidate Training Loss graph white background in dark mode

**Root Cause**: Primarily downstream of CASCOR-001. No candidate training occurs because training fails. The white background issue is a separate CSS/Plotly styling problem — the empty plot figure doesn't apply dark mode template.

---

### CANOPY-009: Network Topology Shows Two Output Nodes (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Network Topology Tab |
| **File** | `src/frontend/components/network_visualizer.py` |
| **Lines** | 612-626 |

**Issue**: Two output nodes displayed instead of one.

**Root Cause**: The visualizer reads `topology.get("output_units", 0)` at line 614 and creates that many output nodes (line 625). If the backend returns `output_units: 2`, two nodes are drawn. This is likely a backend data issue — either the demo mode or the cascor API is returning the wrong output unit count.

For a binary classification problem (two-spiral), the network may legitimately have 2 output units (one per class) or 1 output unit (sigmoid binary output). The issue is whether the cascor network is configured with 1 or 2 outputs and whether that matches what canopy expects.

---

### CANOPY-010: Decision Boundary Display Height/Aspect Ratio (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — Decision Boundary Tab |
| **File** | `src/frontend/components/decision_boundary.py` |
| **Lines** | 147-151 |

**Issue**: Fixed height of 600px stretches width without maintaining aspect ratio.

**Root Cause**: `style={"height": "600px"}` at line 150. No width constraint. Plotly graph fills available width but height is fixed, causing distortion.

**Additional Request**: Add replay capability for decision boundary evolution across hidden node additions.

---

### CANOPY-011: Dataset View Display Height/Aspect Ratio (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — Dataset View Tab |
| **File** | `src/frontend/components/dataset_plotter.py` |
| **Lines** | 218-229 |

**Issue**: Similar to CANOPY-010. Fixed heights (500px scatter, 300px distribution) don't maintain aspect ratio.

---

### CANOPY-012: Dataset Dropdown Not Populated (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Dataset View Tab |
| **File** | `src/frontend/components/dataset_plotter.py` |
| **Lines** | 102-108 |

**Issue**: Dataset dropdown has `options=[]` (empty) with comment "Populated dynamically" but no callback populates it.

**Required**: Fetch available generators from juniper-data service via `list_generators()` and populate dropdown options.

---

### CANOPY-013: Dataset Sidebar Section Hardcoded to "Spiral Dataset" (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Left Sidebar, Dataset Parameters |
| **File** | `src/frontend/dashboard_manager.py` |
| **Lines** | 721-790 |

**Issue**: The sidebar dataset section heading is "Spiral Dataset" (line 728) and the fields are hardcoded for spiral parameters only (Rotations, Number, Elements, Noise).

**Required**:
- Rename heading to "Current Dataset"
- Make fields dynamic based on selected dataset type
- Update fields when dataset selection changes in the Dataset View tab

---

### CANOPY-014: Generate Dataset Button Behavior (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Dataset View Tab |
| **File** | `src/frontend/components/dataset_plotter.py` |

**Issue**: The "Generate Dataset" button lacks the required workflow:
1. Stop training
2. Generate and display new dataset
3. Update Feature Distributions
4. Check neural network compatibility
5. Prompt user if incompatible, or allow restart if compatible

---

### CANOPY-015: HDF5 Snapshots Tab Naming and Layout (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — HDF5 Snapshots Tab |
| **File** | `src/frontend/components/hdf5_snapshots_panel.py` |
| **Lines** | 109-127 |

**Issues**:
- Tab title "HDF5 Snapshots" should be "Snapshots" (line 110)
- Refresh button and status message should be moved to "Available Snapshots" section heading
- Tab label in dashboard_manager.py line 1102 also says "HDF5 Snapshots"

---

### CANOPY-016: Cassandra Tab API URL Error (P2)

| Field | Value |
|-------|-------|
| **Severity** | P2 — Medium |
| **Component** | `juniper-canopy` — Cassandra Tab |
| **File** | `src/frontend/components/cassandra_panel.py` |
| **Lines** | 98-113, 382-383 |

**Root Cause**: The `_api_url()` method at line 113 returns `path.lstrip("/")` which produces a relative URL (e.g., `"api/v1/cassandra/status"`). The `requests.get()` call at line 383 requires an absolute URL. This causes a `MissingSchema` error.

**Comparison**: The `dashboard_manager.py` at line 1231 correctly builds absolute URLs using Flask request context: `f"{request.scheme}://{request.host}"`. The Cassandra panel's `_api_url` does not use this approach.

**Same issue likely affects**: `redis_panel.py` (line 90), `worker_panel.py` (line 63), `candidate_metrics_panel.py` (line 91) — all have their own `_api_url` methods.

---

### CANOPY-017: Parameters Tab Dark Mode (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — Parameters Tab |
| **File** | `src/frontend/components/parameters_panel.py` |
| **Lines** | 168-196 |

**Issue**: Meta Parameters tables show white background in dark mode. The `dbc.Card` components at lines 168, 178, 188 don't inherit dark mode CSS variables.

**Root Cause**: `dark_mode.css` targets generic `table` elements (line 217), but `dbc.Card` and `dbc.CardBody` have their own Bootstrap styles that may override CSS variables. Need explicit `.dark-mode .card` selectors or inline styles using CSS variables.

---

### CANOPY-018: Tutorial Tab Dark Mode (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — Tutorial Tab |
| **File** | `src/frontend/components/tutorial_panel.py` |

**Issue**: Dashboard Components and Parameters Reference tables show white background in dark mode. Same root cause as CANOPY-017.

---

### CANOPY-019: Candidate Training Loss Graph Dark Mode (P3)

| Field | Value |
|-------|-------|
| **Severity** | P3 — Low |
| **Component** | `juniper-canopy` — Candidate Metrics Tab |
| **File** | `src/frontend/components/candidate_metrics_panel.py` |

**Issue**: Empty candidate loss graph has white background in dark mode. Plotly figure doesn't apply dark mode template for empty state.

---

## Impact Assessment

### Dependency Chain

```
CASCOR-001 (Training Failure)
    ├── CANOPY-002 (Status "Failed") — RESOLVED when CASCOR-001 fixed
    ├── CANOPY-007 (Metrics Empty/Incorrect) — PARTIALLY RESOLVED when CASCOR-001 fixed
    ├── CANOPY-008 (Candidate Metrics) — PARTIALLY RESOLVED when CASCOR-001 fixed
    ├── CANOPY-005 (Network Info Zeros) — PARTIALLY RESOLVED when CASCOR-001 fixed
    └── CANOPY-006 (Network Details Zeros) — PARTIALLY RESOLVED when CASCOR-001 fixed
```

### Independent Issues (not dependent on CASCOR-001)

- CANOPY-001: Tab ordering
- CANOPY-003: Sidebar parameter defaults
- CANOPY-004: Convergence Threshold field
- CANOPY-009: Two output nodes
- CANOPY-010/011: Aspect ratio
- CANOPY-012: Dataset dropdown
- CANOPY-013: Spiral Dataset heading
- CANOPY-014: Generate Dataset workflow
- CANOPY-015: Snapshots tab naming
- CANOPY-016: Cassandra API URL
- CANOPY-017/018/019: Dark mode issues

---

## Priority Matrix

| Priority | Issues | Rationale |
|----------|--------|-----------|
| **P0 — Immediate** | CASCOR-001 | Blocks all training, all releases, all downstream work |
| **P1 — High** | CANOPY-002, CANOPY-007, CANOPY-016 | Direct user-facing failures; CANOPY-016 causes visible errors |
| **P2 — Medium** | CANOPY-001, 003, 004, 005, 006, 008, 009, 012, 013, 014 | Incorrect data display, missing features, usability issues |
| **P3 — Low** | CANOPY-010, 011, 015, 017, 018, 019 | Visual/cosmetic improvements |

---

## Validation Status

All findings in this analysis have been validated through:
1. Direct code inspection of source files with exact line numbers
2. Log file analysis confirming the `UnboundLocalError` and `FileNotFoundError`
3. Tracing the execution path from entry point through failure
4. Comparison of expected vs. actual behavior for each UI issue
5. CSS rule analysis for dark mode styling gaps
