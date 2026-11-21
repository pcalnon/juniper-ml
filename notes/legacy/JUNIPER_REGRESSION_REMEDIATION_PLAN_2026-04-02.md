# Juniper Regression Remediation Plan

**Date**: 2026-04-02
**Companion**: `JUNIPER_REGRESSION_ANALYSIS_2026-04-02.md` (referenced by name; the companion analysis file was never landed in this repo)
**Author**: Claude Code (Opus 4.6)

---

## C-1: SharedMemory Premature Cleanup (CRITICAL)

### Problem

`_execute_parallel_training()` unconditionally unlinks SharedMemory blocks in its `finally` block, even when `_execute_candidate_training()` will subsequently call `_execute_sequential_training()` as a fallback, which needs those same blocks.

### Approach A: Deferred SharedMemory Cleanup (RECOMMENDED)

Move SharedMemory cleanup from `_execute_parallel_training()` to `_execute_candidate_training()`, which owns the lifecycle of both parallel and sequential paths.

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

#### Change 1: Remove cleanup from `_execute_parallel_training()` finally block

**Current** (lines 2129-2135):
```python
finally:
    # OPT-5: Release SharedMemory blocks for this round (runs even on error/interrupt)
    for shm_block in list(self._active_shm_blocks):
        try:
            shm_block.close_and_unlink()
            self._active_shm_blocks.remove(shm_block)
        except Exception as shm_e:
            self.logger.warning(f"...: OPT-5 SharedMemory cleanup error: {shm_e}")

    self.logger.trace("...: Parallel training round complete (persistent pool, no cleanup needed)")
```

**Proposed**:
```python
finally:
    # OPT-5: SharedMemory cleanup is now deferred to _execute_candidate_training()
    # to ensure sequential fallback can access the blocks if parallel fails.
    self.logger.trace("...: Parallel training round complete (persistent pool, no cleanup needed)")
```

#### Change 2: Add cleanup to `_execute_candidate_training()` after all paths complete

**Current** (lines 1906-1989 — end of method):
```python
        # Ensure we have some results...
        if not results:
            ...
            results = self._get_dummy_results(len(tasks))
        return results
```

**Proposed** — wrap entire method body in try/finally:
```python
    def _execute_candidate_training(self, tasks: list, process_count: int) -> list:
        """..."""
        self.logger.info(f"...: Training {len(tasks)} candidates with {process_count} processes")

        results = []
        try:
            # ... existing logic (lines 1926-1988) unchanged ...
        finally:
            # OPT-5: Release SharedMemory blocks AFTER both parallel and sequential
            # paths have completed (or failed). This prevents the race condition where
            # the sequential fallback cannot access blocks cleaned up by parallel's finally.
            for shm_block in list(self._active_shm_blocks):
                try:
                    shm_block.close_and_unlink()
                    self._active_shm_blocks.remove(shm_block)
                except Exception as shm_e:
                    self.logger.warning(f"...: OPT-5 SharedMemory cleanup error: {shm_e}")

        # Ensure we have some results
        if not results:
            ...
            results = self._get_dummy_results(len(tasks))
        return results
```

#### Strengths
- Directly addresses root cause
- Minimal code change (move cleanup, don't rewrite)
- SharedMemory lifecycle aligns with the scope that creates it (candidate training round)
- Sequential fallback now has full access to SharedMemory blocks

#### Weaknesses
- SharedMemory blocks live slightly longer in the normal case (not meaningfully different)
- If `_execute_candidate_training()` itself crashes before finally, blocks may leak

#### Guardrails
- `_active_shm_blocks` tracking ensures blocks are always eventually cleaned
- The try/finally ensures cleanup even on unexpected exceptions

---

### Approach B: Populate Fallback Tensors in Task Metadata

Add serialized tensor copies as `_fallback_tensors` in the SharedMemory metadata dict, so `_build_candidate_inputs()` can use them when SharedMemory is unavailable.

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`

**Location**: `_generate_candidate_tasks()` — where task tuples are created with SharedMemory metadata.

**Change**: When creating the SharedMemory metadata dict, include:
```python
metadata["_fallback_tensors"] = (
    candidate_input.clone(),
    y.clone(),
    residual_error.clone(),
)
```

#### Strengths
- `_build_candidate_inputs()` already has fallback logic (lines 2857-2861)
- Defense-in-depth: works even if SharedMemory fails for any reason

#### Weaknesses
- Defeats the purpose of OPT-5 (SharedMemory avoids redundant serialization)
- Increases memory usage by duplicating tensors
- Masking the underlying timing bug rather than fixing it

#### Risk Assessment
- LOW risk for Approach A (recommended)
- MEDIUM risk for Approach B (memory overhead negates OPT-5 benefits)

---

## C-2: UnboundLocalError Guard (CRITICAL)

### Problem

The `candidate_inputs = None` guard at line 2716 was added after the bug was observed. Verify it's present and complete.

### Fix

**Current code at line 2716** (already present):
```python
candidate_inputs = None  # Guard: prevent UnboundLocalError if _build_candidate_inputs raises
```

**Status**: Guard IS present in current source. **No additional code change needed** — but the fix only masks C-1. Both C-1 and C-2 must be addressed together.

---

## H-3: Network Information Shows Zeros

### Problem

`_update_network_info_handler()` reads `input_size` and `output_size` from `/api/status`. The `service_backend.py` reads these from the training state dict: `ts.get("input_size", 0)`. If cascor's training state doesn't broadcast these values, defaults to 0.

### Fix

**File**: `juniper-canopy/src/backend/service_backend.py` lines 134-135

**Current**:
```python
"input_size": ts.get("input_size", 0),
"output_size": ts.get("output_size", 0),
```

**Proposed**: Also check the `monitor` dict and the raw response:
```python
"input_size": _first_defined(
    ts.get("input_size"),
    monitor.get("input_size"),
    raw.get("input_size"),
    default=0,
),
"output_size": _first_defined(
    ts.get("output_size"),
    monitor.get("output_size"),
    raw.get("output_size"),
    default=0,
),
```

**Additionally**: Verify that cascor's `LifecycleManager.get_status()` includes `input_size` and `output_size` in the training state. Currently, `get_status()` (line 587) returns:
```python
{
    "state_machine": state_summary,
    "monitor": monitor_state,
    "training_state": training_state,
    "network_loaded": ...,
    "training_active": ...,
}
```

The `training_state` dict from `self.training_state.get_state()` may not include `input_size`/`output_size`. These should be added.

**File**: `juniper-cascor/src/api/lifecycle/manager.py`

In `get_status()` (line 587), add network dimensions:
```python
def get_status(self) -> Dict[str, Any]:
    state_summary = self.state_machine.get_state_summary()
    monitor_state = self.training_monitor.get_current_state()
    training_state = self.training_state.get_state()

    # Ensure network dimensions are available
    if self.network is not None:
        training_state.setdefault("input_size", self.network.input_size)
        training_state.setdefault("output_size", self.network.output_size)

    return {
        "state_machine": state_summary,
        "monitor": monitor_state,
        "training_state": training_state,
        "network_loaded": self.network is not None,
        "training_active": self.state_machine.is_started(),
    }
```

#### Strengths
- Ensures network dimensions are always available when a network exists
- Uses `setdefault` to not override explicitly set values

#### Weaknesses
- Requires changes in both cascor and canopy codebases

---

## H-4: Parameters Show Constants Defaults

### Problem

In service mode, `/api/state` populates `nn_*`/`cn_*` keys with defaults via `setdefault()`, then overrides with `backend._adapter.get_canopy_params()`. If the adapter doesn't map all cascor parameters to canopy keys, defaults persist.

### Fix

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

Audit `get_canopy_params()` to ensure it maps all 22 `nn_*`/`cn_*` parameter keys from cascor's network attributes.

**Required mappings**:

| Canopy Key | Cascor Network Attribute |
|-----------|------------------------|
| `nn_max_iterations` | `max_iterations` |
| `nn_max_total_epochs` | `epochs_max` |
| `nn_learning_rate` | `learning_rate` |
| `nn_max_hidden_units` | `max_hidden_units` |
| `nn_multi_node_layers` | `candidates_per_layer > 1` |
| `nn_growth_trigger` | `growth_trigger` |
| `nn_growth_preset_epochs` | `growth_preset_epochs` |
| `nn_growth_convergence_threshold` | `convergence_threshold` |
| `cn_pool_size` | `candidate_pool_size` |
| `cn_correlation_threshold` | `correlation_threshold` |
| `cn_training_iterations` | `candidate_epochs` |
| `cn_training_convergence_threshold` | `candidate_convergence_threshold` |

---

## H-5: Convergence Threshold Shows Epochs Value

### Problem

The parameter initialization callback Output ordering was verified CORRECT (Output #6 = preset_epochs, Output #7 = convergence_threshold). The issue is in the **backend data mapping**: `CascorServiceAdapter.get_canopy_params()` either doesn't map `nn_growth_convergence_threshold` or maps it to the wrong cascor attribute, causing canopy to fall back to `TrainingConstants.DEFAULT_CONVERGENCE_THRESHOLD` which may equal the epochs default.

### Fix

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

Audit `get_canopy_params()` to ensure:
1. `nn_growth_convergence_threshold` maps to `network.convergence_threshold` (not `network.epochs_max`)
2. `nn_growth_preset_epochs` maps to `network.growth_preset_epochs` (not `network.convergence_threshold`)

If the adapter doesn't expose these keys at all, add them:
```python
def get_canopy_params(self):
    network = self.network
    if network is None:
        return {}
    return {
        ...
        "nn_growth_convergence_threshold": getattr(network, "convergence_threshold", None),
        "nn_growth_preset_epochs": getattr(network, "growth_preset_epochs", None),
        ...
    }
```

---

## M-1: Candidate Loss Graph Dark Mode

### Problem

`_create_candidate_loss_figure()` hardcodes light-mode colors.

### Fix

**File**: `juniper-canopy/src/frontend/components/candidate_metrics_panel.py`

**Current** (lines 567-573):
```python
fig.update_layout(
    xaxis_title="Epoch",
    yaxis_title="Loss",
    template="plotly",
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="#ffffff",
    ...
)
```

**Proposed**:
```python
def _create_candidate_loss_figure(self, epochs, losses, phases=None, theme="light"):
    ...
    is_dark = theme == "dark"
    fig.update_layout(
        xaxis_title="Epoch",
        yaxis_title="Loss",
        template="plotly_dark" if is_dark else "plotly",
        plot_bgcolor="#1a1a1a" if is_dark else "#f8f9fa",
        paper_bgcolor="#242424" if is_dark else "#ffffff",
        font_color="#e9ecef" if is_dark else "#212529",
        ...
    )
```

Also update the callback that calls this method to pass the current theme from `theme-state` store.

---

## M-2 & M-3: Parameters and Tutorial Tab Dark Mode

### Problem

HTML tables in Parameters and Tutorial panels have white backgrounds in dark mode.

### Fix

**File**: `juniper-canopy/src/frontend/assets/dark_mode.css`

Add CSS rules targeting the specific table elements:

```css
/* Parameters tab dark mode */
.dark-mode .parameters-table,
.dark-mode .parameters-table th,
.dark-mode .parameters-table td {
    background-color: var(--bg-secondary) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
}

/* Tutorial tab dark mode */
.dark-mode .tutorial-table,
.dark-mode .tutorial-table th,
.dark-mode .tutorial-table td {
    background-color: var(--bg-secondary) !important;
    color: var(--text-color) !important;
    border-color: var(--border-color) !important;
}
```

Alternatively, ensure the tables use Bootstrap's `table-dark` class when in dark mode, or apply CSS variables directly.

---

## M-4 & M-5: Decision Boundary and Dataset View Aspect Ratio

### Problem

Fixed height containers cause scatter plots to stretch horizontally without preserving aspect ratio.

### Fix

Use Plotly's `scaleanchor` and `scaleratio` properties:

```python
fig.update_layout(
    yaxis=dict(
        scaleanchor="x",
        scaleratio=1,
    ),
)
```

And adjust the container style to allow natural height:

```python
style={"width": "100%", "aspectRatio": "1 / 1", "maxHeight": "800px"}
```

---

## M-6: Cassandra API URL Error

### Problem

`CassandraPanel._api_url()` uses Flask request context which may not be available during Dash callbacks.

### Fix

**File**: `juniper-canopy/src/frontend/components/cassandra_panel.py`

**Proposed**: Use a configuration-based approach instead of runtime request context:

```python
def _api_url(self, path: str) -> str:
    base_url = self.config.get("api_base_url", "http://127.0.0.1:8050")
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
```

Or use the same pattern as `dashboard_manager.py`'s `_api_url()` method for consistency.

---

## M-7: Snapshots Refresh Button Position

### Fix

**File**: `juniper-canopy/src/frontend/components/hdf5_snapshots_panel.py`

Move the refresh button and status message from the tab header into the "Available Snapshots" section heading using a `dbc.Row` with `justify="between"`:

```python
dbc.CardHeader(
    dbc.Row([
        dbc.Col(html.H5("Available Snapshots"), width="auto"),
        dbc.Col([
            refresh_button,
            status_message,
        ], width="auto"),
    ], justify="between", align="center"),
),
```

---

## L-1: Decision Boundary History/Replay

### Enhancement Design

Add a slider control showing hidden unit count from 0 to current, with a play/pause button:

1. Store decision boundary images at each hidden unit addition in the backend
2. Add a `dcc.Slider` below the visualization with range [0, current_hidden_units]
3. Add a play button that auto-advances the slider
4. On slider change, display the corresponding boundary image

**Scope**: New feature — approximately 150-200 lines of new code across decision_boundary.py and the backend API.

---

## L-2, L-3, L-4: Dataset View Enhancements

### L-2: Dataset Dropdown Population

Add a callback that fetches available generators from juniper-data:
```python
@app.callback(
    Output("dataset-selector", "options"),
    Input("visualization-tabs", "active_tab"),
)
def populate_dataset_selector(active_tab):
    if active_tab != "dataset":
        return dash.no_update
    generators = fetch_generators_from_juniper_data()
    return [{"label": g["name"], "value": g["id"]} for g in generators]
```

### L-3: Dynamic Dataset Section Heading

Change the sidebar section from "Spiral Dataset" to "Current Dataset" and dynamically show/hide parameter fields based on selected dataset type.

### L-4: Generate Dataset Workflow

Implement the full workflow:
1. Stop training when new dataset is generated
2. Display new scatter plot
3. Check network compatibility (input/output dimensions)
4. Prompt user if incompatible
5. Allow training restart with compatible network

---

## Summary of Files to Modify

### juniper-cascor

| File | Change | Priority |
|------|--------|----------|
| `src/cascade_correlation/cascade_correlation.py` | C-1: Move SharedMemory cleanup | CRITICAL |
| `src/api/lifecycle/manager.py` | H-3: Add input_size/output_size to status | HIGH |

### juniper-canopy

| File | Change | Priority |
|------|--------|----------|
| `src/backend/service_backend.py` | H-3: Multi-source input/output size | HIGH |
| `src/backend/cascor_service_adapter.py` | H-4: Audit parameter mapping | HIGH |
| `src/frontend/dashboard_manager.py` | H-5: Verify callback output ordering | HIGH |
| `src/frontend/components/candidate_metrics_panel.py` | M-1: Dark mode graph colors | MEDIUM |
| `src/frontend/assets/dark_mode.css` | M-2/M-3: Table dark mode rules | MEDIUM |
| `src/frontend/components/cassandra_panel.py` | M-6: API URL construction | MEDIUM |
| `src/frontend/components/hdf5_snapshots_panel.py` | M-7: Refresh button position | MEDIUM |
| `src/frontend/components/decision_boundary.py` | M-4/L-1: Aspect ratio + replay | MEDIUM/LOW |
| `src/frontend/components/dataset_plotter.py` | M-5/L-2-4: Aspect ratio + enhancements | MEDIUM/LOW |
| `src/frontend/components/parameters_panel.py` | M-2: Add dark mode CSS classes | MEDIUM |
| `src/frontend/components/tutorial_panel.py` | M-3: Add dark mode CSS classes | MEDIUM |

---

## Recommended Implementation Order

1. **C-1** → Unblocks all training and most downstream issues
2. **C-2** → Verify guard is present (already done)
3. **H-3** → Network info immediately useful post-training-fix
4. **H-4** → Parameters correctly populated
5. **H-5** → Convergence threshold displays correctly
6. **M-1, M-2, M-3** → Dark mode batch (independent, parallelizable)
7. **M-4, M-5** → Aspect ratio fixes (independent)
8. **M-6** → Cassandra URL fix
9. **M-7** → Snapshots layout
10. **L-1 through L-4** → Feature enhancements (defer to next sprint)
