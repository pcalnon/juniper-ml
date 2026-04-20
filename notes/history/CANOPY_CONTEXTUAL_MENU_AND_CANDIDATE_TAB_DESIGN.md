# Canopy Contextual Left Menu & Candidate Metrics Tab Enhancement Design

**Version**: 1.3.0
**Created**: 2026-03-31
**Updated**: 2026-04-01
**Status**: IMPLEMENTED
**Project**: juniper-canopy
**Implementation Branch**: `feature/contextual-sidebar-candidate-tab`
**Author**: Claude Code (Principal Engineer)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Enhancement 1: Contextual Left Menu](#3-enhancement-1-contextual-left-menu)
4. [Enhancement 2: Candidate Metrics Tab](#4-enhancement-2-candidate-metrics-tab)
5. [Implementation Approaches](#5-implementation-approaches)
6. [Phased Implementation Plan](#6-phased-implementation-plan)
7. [Risk Analysis & Guardrails](#7-risk-analysis--guardrails)
8. [Testing Strategy](#8-testing-strategy)
9. [File Impact Matrix](#9-file-impact-matrix)
10. [Appendix: Component ID Registry](#10-appendix-component-id-registry)

---

## 1. Executive Summary

### Problem Statement

The juniper-canopy dashboard's left sidebar displays **all** control sections (Training Controls, Meta Parameters with Neural Network and Candidate Nodes subsections, Network Information) regardless of which tab is active. As the application has grown to 12 tabs (11 existing + 1 proposed), this creates:

1. **Visual clutter**: Users see irrelevant controls for the active tab
2. **Cognitive overload**: The sidebar is long and scrollable, burying contextually relevant controls
3. **Missing separation of concerns**: Candidate pool metrics are embedded within the Training Metrics tab rather than having their own dedicated tab

### Proposed Changes

| Enhancement               | Description                                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Contextual Left Menu**  | Sidebar sections dynamically show/hide based on which top-menu tab is active. Training Controls always visible. |
| **Candidate Metrics Tab** | New top-level tab dedicated to candidate pool training, performance, and history visualization.                 |

### Scope

- **In scope**: Sidebar visibility logic, new tab creation, content extraction from metrics_panel.py
- **Out of scope**: New backend API endpoints, new data models, CSS redesign, mobile responsive changes

---

## 2. Current State Analysis

### 2.1 Current Sidebar Structure

The sidebar is implemented in `dashboard_manager.py` (lines 382-829) as a `dbc.Col(width=3)` containing three `dbc.Card` components:

```bash
Left Sidebar (width=3)
├── Card 1: Training Controls
│   ├── ▶ Start Training (id: start-button)
│   ├── ⏸ Pause Training (id: pause-button)
│   ├── ⏯ Resume Training (id: resume-button)
│   ├── ⏹ Stop Training (id: stop-button)
│   └── ↻ Reset Training (id: reset-button)
│
├── Card 2: Meta Parameters
│   ├── Neural Network subsection (id: nn-subsection-collapse, is_open=True)
│   │   ├── [Unlabeled] Top Level Meta Parameters
│   │   │   ├── Maximum Iterations (id: nn-max-iterations-input)
│   │   │   ├── Maximum Total Epochs (id: nn-max-total-epochs-input)
│   │   │   ├── Learning Rate (id: nn-learning-rate-input)
│   │   │   └── Maximum Hidden Units (id: nn-max-hidden-units-input)
│   │   ├── Multi-Node Layers (id: nn-multi-node-layers-checkbox)
│   │   ├── Network Growth Triggers
│   │   │   ├── Radio: Preset Epochs / Convergence (id: nn-growth-trigger-radio)
│   │   │   ├── Preset Epochs input (id: nn-growth-preset-epochs-input)
│   │   │   └── Convergence Threshold input (id: nn-growth-convergence-threshold-input)
│   │   └── Spiral Dataset
│   │       ├── Rotations (id: nn-spiral-rotations-input)
│   │       ├── Number (id: nn-spiral-number-input)
│   │       ├── Elements (id: nn-dataset-elements-input)
│   │       └── Noise (id: nn-dataset-noise-input)
│   │
│   ├── Candidate Nodes subsection (id: cn-subsection-collapse, is_open=False)
│   │   ├── [Unlabeled] Candidate Pool Meta Parameters
│   │   │   ├── Pool Size (id: cn-pool-size-input)
│   │   │   ├── Correlation Threshold (id: cn-correlation-threshold-input)
│   │   │   └── Selected Candidates (id: cn-selected-candidates-input)
│   │   ├── Pool Training Complete
│   │   │   ├── Radio: Preset Epochs / Convergence (id: cn-training-complete-radio)
│   │   │   ├── Training Iterations input (id: cn-training-iterations-input)
│   │   │   └── Convergence Threshold input (id: cn-training-convergence-threshold-input)
│   │   └── Multi Candidate Selection
│   │       ├── Enable checkbox (id: cn-multi-candidate-checkbox)
│   │       ├── Radio: Top Tier / Random (id: cn-candidate-selection-radio)
│   │       ├── Top Candidates input (id: cn-top-candidates-input)
│   │       └── Random Candidates input (id: cn-random-candidates-input)
│   │
│   └── Apply Parameters button (id: apply-params-button)
│
└── Card 3: Network Information (id: network-info-collapse, is_open=True)
    ├── [Unnamed] Neural Network Training Status (id: network-info-panel)
    └── Network Information: Details (id: network-info-details-collapse, is_open=False)
        └── Details panel (id: network-info-details-panel)
```

### 2.2 Current Tab Structure

Implemented in `dashboard_manager.py` (lines 833-893) using `dbc.Tabs(id="visualization-tabs")`:

| Tab ID       | Label               | Component          | File                      |
|--------------|---------------------|--------------------|---------------------------|
| `metrics`    | Training Metrics    | MetricsPanel       | `metrics_panel.py`        |
| `topology`   | Network Topology    | NetworkVisualizer  | `network_visualizer.py`   |
| `boundaries` | Decision Boundaries | DecisionBoundary   | `decision_boundary.py`    |
| `dataset`    | Dataset View        | DatasetPlotter     | `dataset_plotter.py`      |
| `snapshots`  | HDF5 Snapshots      | HDF5SnapshotsPanel | `hdf5_snapshots_panel.py` |
| `redis`      | Redis               | RedisPanel         | `redis_panel.py`          |
| `cassandra`  | Cassandra           | CassandraPanel     | `cassandra_panel.py`      |
| `workers`    | Workers             | WorkerPanel        | `worker_panel.py`         |
| `about`      | About               | AboutPanel         | `about_panel.py`          |
| `parameters` | Parameters          | ParametersPanel    | `parameters_panel.py`     |
| `tutorial`   | Tutorial            | TutorialPanel      | `tutorial_panel.py`       |

### 2.3 Candidate Content Currently in Training Metrics

The `metrics_panel.py` (2,169 lines) contains embedded candidate content:

| Content                              | Location        | Component IDs                                                                     |
|--------------------------------------|-----------------|-----------------------------------------------------------------------------------|
| Candidate pool section (collapsible) | Lines 500-531   | `{id}-candidate-pool-section`, `{id}-candidate-toggle`, `{id}-candidate-collapse` |
| Pool info display                    | Lines 1939-2096 | `{id}-candidate-pool-info`                                                        |
| Pool history section                 | Lines 657-772   | `{id}-candidate-history-section`, `{id}-candidate-pools-history`                  |
| Candidate training trace (loss plot) | Lines 1563-1596 | N/A (embedded in loss figure)                                                     |
| Candidate epoch progress bar         | Layout section  | `{id}-candidate-epoch-progress`                                                   |

### 2.4 Existing Collapsible Section Pattern

The codebase uses a consistent pattern for collapsible sections:

**Layout pattern:**

```python
html.H6(
    [
        html.Span("▼"/"▶", id="<section>-icon", className="collapse-icon"),
        "Section Title",
    ],
    id="<section>-header",
    className="collapsible-header",
),
dbc.Collapse(
    html.Div([...content...]),
    id="<section>-collapse",
    is_open=True/False,
),
```

**Callback pattern:**

```python
@self.app.callback(
    [Output("<section>-collapse", "is_open"), Output("<section>-icon", "children")],
    Input("<section>-header", "n_clicks"),
    State("<section>-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_section(n_clicks, is_open):
    return not is_open, "▼" if not is_open else "▶"
```

**CSS:**

```css
.collapsible-header { cursor: pointer; user-select: none; padding: 4px 8px; ... }
.collapsible-header:hover { background-color: var(--bg-secondary); }
.collapse-icon { display: inline-block; margin-right: 6px; font-size: 0.7em; ... }
```

### 2.5 Existing Callback Infrastructure

Key callbacks that interact with the sidebar and must be preserved:

| Callback                      | Inputs                               | Outputs                                            | Purpose                 |
|-------------------------------|--------------------------------------|----------------------------------------------------|-------------------------|
| `toggle_nn_subsection`        | nn-subsection-header.n_clicks        | nn-subsection-collapse.is_open, nn-subsection-icon | Toggle NN section       |
| `toggle_cn_subsection`        | cn-subsection-header.n_clicks        | cn-subsection-collapse.is_open, cn-subsection-icon | Toggle CN section       |
| `toggle_network_info`         | network-info-header.n_clicks         | network-info-collapse.is_open                      | Toggle Network Info     |
| `toggle_network_info_details` | network-info-details-header.n_clicks | network-info-details-collapse.is_open, icon        | Toggle details          |
| `track_param_changes`         | All 22 param inputs                  | apply-params-button.disabled, params-status        | Enable/disable Apply    |
| `apply_parameters`            | apply-params-button.n_clicks         | applied-params-store, params-status                | Send params to backend  |
| `init_params_from_backend`    | params-init-interval                 | All 22 param inputs                                | Initialize from backend |
| `sync_multi_node_checkboxes`  | Both checkboxes                      | Synchronized values                                | Cross-section sync      |

---

## 3. Enhancement 1: Contextual Left Menu

### 3.1 Requirements

The sidebar must show different sections based on the active tab. Training Controls are always visible. All other sections are conditionally displayed.

### 3.2 Contextual Menu Mapping

| Tab                 | Training Control | Top Level Meta Params | Network Grow Triggers | Multi-Node Layers | Spiral Dataset | Cand Pool Meta Params | Pool Train Complete | Multi Candidate Select | Network Info: Status | Network Info: Details |
|---------------------|:----------------:|:---------------------:|:---------------------:|:-----------------:|:--------------:|:---------------------:|:-------------------:|:----------------------:|:--------------------:|:---------------------:|
| Training Metrics    |      Always      |        Visible        |      Collapsible      |         -         |       -        |           -           |          -          |           -            |     Collapsible      |      Collapsible      |
| Candidate Metrics   |      Always      |           -           |           -           |    Collapsible    |       -        |        Visible        |     Collapsible     |           -            |          -           |           -           |
| Network Topology    |      Always      |        Visible        |           -           |    Collapsible    |       -        |           -           |          -          |           -            |     Collapsible      |      Collapsible      |
| Decision Boundaries |      Always      |           -           |           -           |         -         |       -        |        Visible        |          -          |           -            |          -           |      Collapsible      |
| Dataset View        |      Always      |           -           |           -           |         -         |    Visible     |           -           |          -          |           -            |          -           |      Collapsible      |
| HDF5 Snapshots      |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| Redis               |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| Cassandra           |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| Workers             |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| About               |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| Parameters          |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |
| Tutorial            |      Always      |           -           |           -           |         -         |       -        |           -           |          -          |           -            |          -           |           -           |

**Legend**: "Visible" = always shown when tab active, "Collapsible" = shown but user can collapse, "-" = hidden

### 3.3 Approach A: Visibility Toggle via Callback (Recommended)

**Description**: Keep all sidebar components in the DOM at all times. Use a single callback that listens to `visualization-tabs.active_tab` and toggles the `style.display` property of each conditional section between `"block"` and `"none"`.

**Implementation**:

```python
# New wrapper divs around each conditional section
html.Div(
    [...meta parameters card content...],
    id="sidebar-meta-params-section",
    style={"display": "block"},  # default visible
),
html.Div(
    [...network info card content...],
    id="sidebar-network-info-section",
    style={"display": "block"},  # default visible
),
```

The sidebar sections need to be decomposed into individually addressable units:

| Section ID                     | Content                                                     | Wraps                              |
|--------------------------------|-------------------------------------------------------------|------------------------------------|
| `sidebar-training-control`     | Training Controls card                                      | Always visible (no wrapper needed) |
| `sidebar-nn-top-params`        | Max Iterations, Max Epochs, Learning Rate, Max Hidden Units | Top-level NN meta params           |
| `sidebar-nn-growth-triggers`   | Growth trigger radio + inputs                               | Network Growth Triggers            |
| `sidebar-nn-multi-node-layers` | Multi-node layers checkbox                                  | Multi-Node Layers                  |
| `sidebar-nn-spiral-dataset`    | Spiral rotations, number, elements, noise                   | Spiral Dataset                     |
| `sidebar-cn-pool-params`       | Pool size, correlation threshold, selected candidates       | Candidate Pool Meta Params         |
| `sidebar-cn-pool-training`     | Pool Training Complete radio + inputs                       | Pool Training Complete             |
| `sidebar-cn-multi-candidate`   | Multi Candidate Selection checkbox + radios + inputs        | Multi Candidate Selection          |
| `sidebar-network-info`         | Network Information card (parent)                           | Network Info wrapper               |
| `sidebar-network-info-status`  | Neural Network Training Status panel                        | Status sub-section                 |
| `sidebar-network-info-details` | Network Information: Details panel                          | Details sub-section                |

**Callback**:

```python
# TAB_SIDEBAR_CONFIG defines which sections are visible per tab
# NOTE: Must include entries for ALL 12 tabs. Tabs not listed default to all-hidden.
# Network Info uses separate keys for status/details to support partial visibility
# (e.g., Decision Boundaries shows details but not status).
TAB_SIDEBAR_CONFIG = {
    "metrics": {
        "sidebar-meta-params-card": True,
        "sidebar-nn-section": True,
        "sidebar-nn-top-params": True,
        "sidebar-nn-growth-triggers": True,   # collapsible
        "sidebar-nn-multi-node-layers": False,
        "sidebar-nn-spiral-dataset": False,
        "sidebar-cn-section": False,
        "sidebar-cn-pool-params": False,
        "sidebar-cn-pool-training": False,
        "sidebar-cn-multi-candidate": False,
        "sidebar-apply-section": True,
        "sidebar-network-info-section": True,
        "sidebar-network-info-status": True,   # collapsible
        "sidebar-network-info-details": True,  # collapsible
    },
    "candidates": {
        "sidebar-meta-params-card": True,
        "sidebar-nn-section": False,
        "sidebar-nn-top-params": False,
        "sidebar-nn-growth-triggers": False,
        "sidebar-nn-multi-node-layers": True,  # collapsible (shown outside NN collapse)
        "sidebar-nn-spiral-dataset": False,
        "sidebar-cn-section": True,
        "sidebar-cn-pool-params": True,
        "sidebar-cn-pool-training": True,      # collapsible
        "sidebar-cn-multi-candidate": False,
        "sidebar-apply-section": True,
        "sidebar-network-info-section": False,
        "sidebar-network-info-status": False,
        "sidebar-network-info-details": False,
    },
    "topology": {
        "sidebar-meta-params-card": True,
        "sidebar-nn-section": True,
        "sidebar-nn-top-params": True,
        "sidebar-nn-growth-triggers": False,
        "sidebar-nn-multi-node-layers": True,  # collapsible
        "sidebar-nn-spiral-dataset": False,
        "sidebar-cn-section": False,
        "sidebar-cn-pool-params": False,
        "sidebar-cn-pool-training": False,
        "sidebar-cn-multi-candidate": False,
        "sidebar-apply-section": True,
        "sidebar-network-info-section": True,
        "sidebar-network-info-status": True,   # collapsible
        "sidebar-network-info-details": True,  # collapsible
    },
    "boundaries": {
        "sidebar-meta-params-card": True,
        "sidebar-nn-section": False,
        "sidebar-nn-top-params": False,
        "sidebar-nn-growth-triggers": False,
        "sidebar-nn-multi-node-layers": False,
        "sidebar-nn-spiral-dataset": False,
        "sidebar-cn-section": True,
        "sidebar-cn-pool-params": True,
        "sidebar-cn-pool-training": False,
        "sidebar-cn-multi-candidate": False,
        "sidebar-apply-section": True,
        "sidebar-network-info-section": True,
        "sidebar-network-info-status": False,  # omitted per spec
        "sidebar-network-info-details": True,  # collapsible
    },
    "dataset": {
        "sidebar-meta-params-card": True,
        "sidebar-nn-section": True,
        "sidebar-nn-top-params": False,
        "sidebar-nn-growth-triggers": False,
        "sidebar-nn-multi-node-layers": False,
        "sidebar-nn-spiral-dataset": True,
        "sidebar-cn-section": False,
        "sidebar-cn-pool-params": False,
        "sidebar-cn-pool-training": False,
        "sidebar-cn-multi-candidate": False,
        "sidebar-apply-section": True,
        "sidebar-network-info-section": True,
        "sidebar-network-info-status": False,
        "sidebar-network-info-details": True,  # collapsible
    },
    # Tabs with only Training Controls:
    "snapshots": {},    # all sidebar sections hidden
    "redis": {},
    "cassandra": {},
    "workers": {},
    "about": {},
    "parameters": {},
    "tutorial": {},
}

@self.app.callback(
    [Output(section_id, "style") for section_id in SIDEBAR_SECTION_IDS]
    + [
        Output("nn-subsection-collapse", "is_open", allow_duplicate=True),
        Output("cn-subsection-collapse", "is_open", allow_duplicate=True),
        Output("sidebar-meta-params-header", "children"),
    ],
    Input("visualization-tabs", "active_tab"),
    prevent_initial_call=True,
)
def update_sidebar_visibility(active_tab):
    config = TAB_SIDEBAR_CONFIG.get(active_tab, {})
    styles = [
        {"display": "block"} if config.get(section_id, False) else {"display": "none"}
        for section_id in SIDEBAR_SECTION_IDS
    ]
    # Auto-open NN/CN collapses when their content is contextually visible
    nn_open = config.get("sidebar-nn-section", False)
    cn_open = config.get("sidebar-cn-section", False)
    # Dynamic card header text
    header_map = {
        "metrics": "Network Parameters", "topology": "Network Parameters",
        "candidates": "Candidate Parameters", "boundaries": "Candidate Parameters",
        "dataset": "Dataset Parameters",
    }
    header_text = header_map.get(active_tab, "Meta Parameters")
    return styles + [nn_open, cn_open, header_text]
```

**Strengths**:

- All components remain in DOM; no re-rendering cost
- Existing callbacks on sidebar inputs continue to work without modification
- Parameter values are preserved when switching tabs (no state loss)
- `track_param_changes` callback (monitors all 22 inputs) works unchanged
- `apply_parameters` and `init_params_from_backend` callbacks unaffected
- Simple, declarative configuration via `TAB_SIDEBAR_CONFIG` dict
- Easy to extend for future tabs
- Minimal risk to existing functionality

**Weaknesses**:

- Hidden components still receive callback updates (minor performance cost)
- DOM contains all sections even when hidden (negligible memory impact for this scale)
- All input IDs must remain globally unique (already the case)

**Risks**:

- **LOW**: The `track_param_changes` callback listens to all 22 input components. Hidden inputs still fire change events. This is benign — the callback already handles all inputs simultaneously.
- **LOW**: The `init_params_from_backend` callback writes to all 22 inputs on load. Hidden inputs receive values correctly since they're in the DOM.

### 3.4 Approach B: Dynamic Content via Tab Callback

**Description**: Replace the static sidebar with a single container. A callback on `active_tab` dynamically generates and returns the sidebar layout for the selected tab.

**Implementation**:

```python
dbc.Col(
    [
        # Training Controls card (always rendered)
        training_controls_card,
        # Dynamic content area
        html.Div(id="sidebar-dynamic-content"),
    ],
    width=3,
)

@self.app.callback(
    Output("sidebar-dynamic-content", "children"),
    Input("visualization-tabs", "active_tab"),
)
def render_sidebar_content(active_tab):
    return self._build_sidebar_for_tab(active_tab)
```

**Strengths**:

- Clean DOM — only relevant components are rendered
- Clear separation of tab-specific sidebar content
- Slightly better performance for tabs with minimal sidebar content

**Weaknesses**:

- **CRITICAL**: Re-rendering destroys component state. Input values typed by the user but not yet applied would be lost on tab switch.
- **CRITICAL**: The `track_param_changes` callback references all 22 input IDs as Inputs. If some IDs don't exist in the DOM (because a different tab is active), Dash throws `NonExistentIdException` or silently fails.
- **HIGH**: `init_params_from_backend` writes to all 22 inputs — missing IDs cause errors.
- **HIGH**: `sync_multi_node_checkboxes` cross-references NN and CN inputs that may not coexist.
- Complex: Requires maintaining separate layout builder methods per tab
- Requires careful state management to preserve user inputs across tab switches

**Risks**:

- **HIGH**: Callback ID resolution failures when referencing non-rendered component IDs
- **HIGH**: User-entered parameter values lost on tab switch
- **MEDIUM**: Increased code complexity and maintenance burden

### 3.5 Approach C: Clientside Callback with CSS Classes

**Description**: Use a clientside (JavaScript) callback for instantaneous visibility toggling via CSS class manipulation.

**Implementation**:

```python
self.app.clientside_callback(
    """
    function(activeTab) {
        const config = {
            "metrics": ["sidebar-nn-top-params", "sidebar-nn-growth-triggers", "sidebar-network-info"],
            "candidates": ["sidebar-cn-pool-params", "sidebar-cn-pool-training", "sidebar-nn-multi-node-layers"],
            // ... etc
        };
        const allSections = [...all section IDs...];
        const visibleSections = config[activeTab] || [];
        allSections.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.style.display = visibleSections.includes(id) ? 'block' : 'none';
            }
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("sidebar-dynamic-content", "data"),  # dummy output
    Input("visualization-tabs", "active_tab"),
)
```

**Strengths**:

- Zero server roundtrip — instant tab switch response
- No re-rendering, no state loss
- All existing callbacks continue to work
- Fastest possible UX

**Weaknesses**:

- JavaScript code lives in Python string (harder to test, lint, debug)
- Duplicates visibility configuration in JS (must keep in sync with any Python-side config)
- Direct DOM manipulation bypasses Dash's component model
- Harder for future developers to discover and modify

**Risks**:

- **LOW**: DOM element IDs must match exactly between Python layout and JS config
- **LOW**: If Dash re-renders the sidebar (e.g., theme change), JS-set styles could be overwritten

### 3.6 Approach Comparison & Recommendation

| Criteria                  | Approach A (Visibility Toggle) | Approach B (Dynamic Content) | Approach C (Clientside JS) |
|---------------------------|:------------------------------:|:----------------------------:|:--------------------------:|
| Preserves input state     |              Yes               |            **No**            |            Yes             |
| Existing callbacks work   |              Yes               |            **No**            |            Yes             |
| Implementation complexity |              Low               |             High             |           Medium           |
| Performance               |              Good              |           Variable           |            Best            |
| Maintainability           |            **Best**            |             Fair             |            Good            |
| Testability               |            **Best**            |             Good             |            Fair            |
| Risk level                |            **Low**             |           **High**           |            Low             |

**Recommendation: Approach A (Visibility Toggle via Callback):**

Approach A is the clear winner. It preserves all existing callback infrastructure, maintains input state across tab switches, and is the simplest to implement and maintain. The minor performance cost of hidden DOM elements is negligible for this sidebar scale (~20 input components).

### 3.7 Sidebar Decomposition Design

The current monolithic Meta Parameters card must be decomposed into individually addressable sections. Two sub-approaches:

#### Sub-Approach A1: Wrapper Divs Inside Existing Card (Recommended)

Keep the existing `dbc.Card` structure but wrap each logical section in a `html.Div` with a unique ID:

```python
dbc.Card([
    dbc.CardHeader(html.H5("Meta Parameters")),
    dbc.CardBody([
        # Wrapper: Top-level NN params (always visible for metrics/topology tabs)
        html.Div([
            html.H6([html.Span("▼", id="nn-subsection-icon", ...), "Neural Network"], ...),
            dbc.Collapse([
                # Top-level params
                html.Div([
                    ...max_iterations, max_epochs, learning_rate, max_hidden_units...
                ], id="sidebar-nn-top-params"),

                # Multi-Node Layers
                html.Div([
                    ...multi_node_layers_checkbox...
                ], id="sidebar-nn-multi-node-layers"),

                # Network Growth Triggers
                # NOTE: Internal html.Hr() dividers (lines 499, 547 in original)
                # are included as the FIRST child of the section that follows them,
                # so they hide/show with that section.
                html.Div([
                    html.Hr(),  # absorb divider from line 499
                    ...growth_trigger_radio, preset_epochs, convergence_threshold...
                ], id="sidebar-nn-growth-triggers"),

                # Spiral Dataset
                html.Div([
                    html.Hr(),  # absorb divider from line 547
                    ...spiral_rotations, spiral_number, dataset_elements, dataset_noise...
                ], id="sidebar-nn-spiral-dataset"),
            ], id="nn-subsection-collapse", is_open=True),
        ], id="sidebar-nn-section"),

        html.Hr(id="sidebar-nn-cn-divider"),

        # Wrapper: Candidate Nodes section
        html.Div([
            html.H6([html.Span("▶", id="cn-subsection-icon", ...), "Candidate Nodes"], ...),
            dbc.Collapse([
                html.Div([
                    ...pool_size, correlation_threshold, selected_candidates...
                ], id="sidebar-cn-pool-params"),

                # NOTE: Internal html.Hr() dividers (lines 651, 699 in original)
                # are included as the FIRST child of the section that follows them.
                html.Div([
                    html.Hr(className="my-2"),  # absorb divider from line 651
                    ...pool_training_complete_radio, training_iterations, convergence_threshold...
                ], id="sidebar-cn-pool-training"),

                html.Div([
                    html.Hr(className="my-2"),  # absorb divider from line 699
                    ...multi_candidate_checkbox, selection_radio, top/random inputs...
                ], id="sidebar-cn-multi-candidate"),
            ], id="cn-subsection-collapse", is_open=False),
        ], id="sidebar-cn-section"),

        html.Hr(id="sidebar-params-divider"),

        # Apply button (always visible when Meta Parameters card is visible)
        html.Div([
            dbc.Button("Apply Parameters", id="apply-params-button", ...),
            html.Div(id="params-status", ...),
        ], id="sidebar-apply-section"),
    ]),
], id="sidebar-meta-params-card")
```

**Strengths**: Minimal structural change, preserves card visual grouping, easy to wrap existing code.
**Weaknesses**: Card header "Meta Parameters" may not be contextually accurate for all tabs.

#### Sub-Approach A2: Separate Cards Per Section

Break the Meta Parameters card into multiple smaller cards, each independently toggle-able:

**Strengths**: Each card is a self-contained visual unit with its own header.
**Weaknesses**: More visual noise with multiple card borders, larger structural refactor, Apply button needs its own visibility logic.

**Recommendation**: Sub-Approach A1. It minimizes structural changes while achieving the required granularity.

### 3.8 Meta Parameters Card Header — Dynamic Update

Since the Meta Parameters card shows different content per tab, the card header should dynamically reflect the active context:

| Tab                 | Card Header Text                 |
|---------------------|----------------------------------|
| Training Metrics    | "Network Parameters"             |
| Candidate Metrics   | "Candidate Parameters"           |
| Network Topology    | "Network Parameters"             |
| Decision Boundaries | "Candidate Parameters"           |
| Dataset View        | "Dataset Parameters"             |
| Other tabs          | Hidden (no Meta Parameters card) |

This can be achieved by adding the card header text as an additional Output in the visibility callback.

### 3.9 Apply Button Visibility

The Apply Parameters button should be visible whenever **any** parameter input is visible. This is handled naturally: if the Meta Parameters card is visible (any section within it is shown), the Apply button should be visible. For tabs that show no parameters (HDF5 Snapshots, Redis, Cassandra, Workers, About), the entire Meta Parameters card is hidden.

### 3.10 Collapsible Sections in Contextual Menu

Per the requirements, some sections should be collapsible when shown in the contextual menu. The existing collapsible pattern (Section 2.4) will be reused. New collapsible wrappers are needed for sections that are currently non-collapsible:

| Section                    |          Currently Collapsible          |         Needs Collapsible Wrapper          |
|----------------------------|:---------------------------------------:|:------------------------------------------:|
| Top Level Meta Params      |       No (content of NN collapse)       |    No — shown as always-visible content    |
| Network Growth Triggers    |       No (content of NN collapse)       |     **Yes** — new collapsible wrapper      |
| Multi-Node Layers          |       No (content of NN collapse)       |     **Yes** — new collapsible wrapper      |
| Spiral Dataset             |       No (content of NN collapse)       |     **Yes** — new collapsible wrapper      |
| Candidate Pool Meta Params |       No (content of CN collapse)       |    No — shown as always-visible content    |
| Pool Training Complete     |       No (content of CN collapse)       |     **Yes** — new collapsible wrapper      |
| Multi Candidate Selection  |       No (content of CN collapse)       | No — not shown in contextual menu per spec |
| Network Info: Status       |     Yes (via network-info-collapse)     |            Already collapsible             |
| Network Info: Details      | Yes (via network-info-details-collapse) |            Already collapsible             |

New collapse component IDs needed:

| Section                 | Header ID                    | Collapse ID                    | Icon ID                    |
|-------------------------|------------------------------|--------------------------------|----------------------------|
| Network Growth Triggers | `ctx-growth-triggers-header` | `ctx-growth-triggers-collapse` | `ctx-growth-triggers-icon` |
| Multi-Node Layers       | `ctx-multi-node-header`      | `ctx-multi-node-collapse`      | `ctx-multi-node-icon`      |
| Spiral Dataset          | `ctx-spiral-dataset-header`  | `ctx-spiral-dataset-collapse`  | `ctx-spiral-dataset-icon`  |
| Pool Training Complete  | `ctx-pool-training-header`   | `ctx-pool-training-collapse`   | `ctx-pool-training-icon`   |

> **Default state**: All new `ctx-*-collapse` components should default to `is_open=True`. When a section is made visible by the contextual menu, the user expects to see its content immediately — requiring an extra click to expand defeats the contextual purpose. Users can still collapse sections they don't need.

---

## 4. Enhancement 2: Candidate Metrics Tab

### 4.1 Requirements

A new top-level tab (`tab_id="candidates"`, label="Candidate Metrics") that displays:

1. Candidate pool status and configuration
2. Candidate training progress (real-time)
3. Candidate performance metrics (correlation scores, loss, accuracy, etc.)
4. Candidate pool history (completed pools)
5. Candidate-specific visualizations

### 4.2 Content Source Analysis

Content for the new tab will be sourced from:

| Content                              | Current Location                    | Action                                  |
|--------------------------------------|-------------------------------------|-----------------------------------------|
| Candidate pool section (collapsible) | `metrics_panel.py` lines 500-531    | **Move** to new component               |
| Pool info display method             | `metrics_panel.py` lines 1939-2096  | **Move** to new component               |
| Pool history tracking + rendering    | `metrics_panel.py` lines 657-772    | **Move** to new component               |
| Candidate epoch progress bar         | `metrics_panel.py` layout           | **Copy** — keep in Training Metrics, add to new component |
| Candidate training trace (loss plot) | `metrics_panel.py` lines 1563-1596  | **Copy** — keep in Training Metrics too |
| `_update_candidate_pool_handler`     | `metrics_panel.py` handler method   | **Move** to new component (candidate pool update logic) |
| `_update_progress_detail_handler` (candidate portions) | `metrics_panel.py` handler method | **Copy** — extract candidate-specific output logic |
| CandidatePool backend class          | `training_monitor.py` lines 48-220  | **Shared** — no change                  |
| Training state candidate fields      | `training_monitor.py` TrainingState | **Shared** — no change                  |

### 4.3 New Component: CandidateMetricsPanel

**File**: `src/frontend/components/candidate_metrics_panel.py`
**Class**: `CandidateMetricsPanel(BaseComponent)`
**Constructor `component_id`**: `"candidate-metrics-panel"` (matches naming convention: `metrics-panel`, `redis-panel`, etc.)
**Component ID prefix**: `candidate-metrics-panel`

#### Layout Structure

```bash
Candidate Metrics Tab
├── Header: "Candidate Metrics"
├── Status Section
│   ├── Status Badge (Active/Inactive)
│   ├── Current Phase (Training/Evaluating/Selecting/Idle)
│   ├── Pool Size
│   └── Candidate Epoch Progress Bar
│
├── Top Candidates Section
│   └── Table: Rank, ID, Correlation Score (top N candidates)
│
├── Pool Metrics Section
│   ├── Avg Loss card
│   ├── Avg Accuracy card
│   ├── Avg Precision card
│   ├── Avg Recall card
│   └── Avg F1 Score card
│
├── Candidate Loss Plot (candidate-phase only trace)
│   └── Orange trace: candidate training loss over epochs
│
├── Pool History Section (collapsible)
│   └── Expandable cards for each completed pool
│       ├── Pool epoch, status, top candidate
│       └── Full metrics breakdown
│
└── Data Stores
    ├── candidate-metrics-panel-training-state-store
    ├── candidate-metrics-panel-pool-history-store
    └── candidate-metrics-panel-update-interval
```

#### Component IDs

| Component            | ID                                             | Type         |
|----------------------|------------------------------------------------|--------------|
| Status badge         | `candidate-metrics-panel-status`               | html.Div     |
| Phase display        | `candidate-metrics-panel-phase`                | html.Div     |
| Pool size display    | `candidate-metrics-panel-pool-size`            | html.Div     |
| Pool info display    | `candidate-metrics-panel-pool-info`            | html.Div     |
| Candidate toggle     | `candidate-metrics-panel-candidate-toggle`     | html.H6      |
| Toggle icon          | `candidate-metrics-panel-toggle-icon`          | html.Span    |
| Epoch progress       | `candidate-metrics-panel-epoch-progress`       | dbc.Progress |
| Top candidates table | `candidate-metrics-panel-top-candidates`       | dbc.Table    |
| Pool metrics cards   | `candidate-metrics-panel-pool-metrics`         | html.Div     |
| Candidate loss plot  | `candidate-metrics-panel-loss-plot`            | dcc.Graph    |
| Pool history section | `candidate-metrics-panel-history-section`      | html.Div     |
| History toggle       | `candidate-metrics-panel-history-toggle`       | html.H6      |
| History collapse     | `candidate-metrics-panel-history-collapse`     | dbc.Collapse |
| History icon         | `candidate-metrics-panel-history-icon`         | html.Span    |
| Training state store | `candidate-metrics-panel-training-state-store` | dcc.Store    |
| Pool history store   | `candidate-metrics-panel-pool-history-store`   | dcc.Store    |
| Update interval      | `candidate-metrics-panel-update-interval`      | dcc.Interval |

#### Callbacks

| Callback                   | Input                                           | Output                                   | Purpose                     |
|----------------------------|-------------------------------------------------|------------------------------------------|-----------------------------|
| Update training state      | update-interval + active_tab                    | training-state-store                     | Fetch state when tab active |
| Update status display      | training-state-store                            | status, phase, pool-size, epoch-progress | Render real-time status     |
| Update top candidates      | training-state-store                            | top-candidates table                     | Render candidate ranking    |
| Update pool metrics        | training-state-store                            | pool-metrics cards                       | Render aggregated metrics   |
| Update candidate loss plot | training-state-store + theme                    | loss-plot figure                         | Render candidate loss chart |
| Update pool history        | training-state-store, State: pool-history-store | pool-history-store                       | Track completed pools       |
| Render pool history        | pool-history-store                              | history-section children                 | Render historical pools     |
| Toggle history             | history-toggle.n_clicks                         | history-collapse.is_open, icon           | Collapse toggle             |

#### Data Sources

All data comes from the existing `/api/state` endpoint, which returns `TrainingState` including:

- `candidate_pool_status`, `candidate_pool_phase`, `candidate_pool_size`
- `top_candidate_id`, `top_candidate_score`, `second_candidate_id`, `second_candidate_score`
- `candidate_epoch`, `candidate_total_epochs`
- `pool_metrics` (dict with avg_loss, avg_accuracy, avg_precision, avg_recall, avg_f1_score)

No new API endpoints are required.

#### Required Imports and Helper Methods

The new `CandidateMetricsPanel` will require the following imports and copied helper methods from `metrics_panel.py`:

| Import / Method             | Source              | Action   | Purpose                                           |
|-----------------------------|---------------------|----------|---------------------------------------------------|
| `time`                      | stdlib              | Import   | Timestamp formatting                              |
| `dash`                      | dash                | Import   | Dash framework core                               |
| `dash_bootstrap_components` | dbc                 | Import   | Bootstrap layout components                       |
| `plotly.graph_objects`      | plotly              | Import   | Candidate loss plot construction                  |
| `BaseComponent`             | `base_component.py` | Import   | Parent class for component pattern                |
| `_candidate_add_trace()`    | `metrics_panel.py`  | **Copy** | Adds candidate training trace to loss figure      |
| `_phase_band_color()`       | `metrics_panel.py`  | **Copy** | Returns color for training phase background bands |
| `_create_empty_plot()`      | `metrics_panel.py`  | **Copy** | Creates empty placeholder figure with styling     |
| `_get_status_style()`       | `metrics_panel.py`  | **Copy** | Returns CSS style dict for status badge coloring  |

> **Note**: Copied methods should be refactored into a shared utility module in a follow-up cleanup pass to eliminate duplication. For the initial implementation, copying maintains independence between components and avoids modifying the existing MetricsPanel.

### 4.4 Impact on Training Metrics Tab

After extraction, the Training Metrics tab will:

1. **Remove**: Candidate pool section (collapsible), pool info display, pool history
2. **Keep**: Candidate training trace in loss plot (orange line) — this is integral to understanding the overall training flow
3. **Keep**: Candidate epoch progress bar — provides context during candidate phases
4. **Remove**: Candidate pool history tracking callbacks

The Training Metrics tab remains the primary view for overall training progress, with candidate phases shown as context in the loss plot. The dedicated Candidate Metrics tab provides the deep-dive into candidate-specific data.

### 4.5 Implementation Notes

#### 4.5.1 Pre-Existing Bug: Pool History Card Toggle

The existing pool history cards in `metrics_panel.py` use **pattern-matching IDs** (e.g., `{"type": "pool-history-card", "index": pool_epoch}`) but have **no corresponding toggle callback** registered. Clicking a history card header does nothing. The new `CandidateMetricsPanel` must add the missing toggle callback for pool history card expansion/collapse.

#### 4.5.2 Pool History Store Isolation

Both the Training Metrics tab and the new Candidate Metrics tab cannot independently accumulate pool history in separate `dcc.Store` components — they would diverge based on which tab was active when a pool completed.

**Recommended approach**: Move pool history tracking exclusively to the Candidate Metrics tab. The Training Metrics tab loses pool history display (already removed per Section 4.4). If shared history is later needed, promote the store to a shared `dcc.Store` at the dashboard level.

#### 4.5.3 `_update_training_progress_handler` Coupling

The existing `_update_training_progress_handler` in `metrics_panel.py` outputs to **both** `grow-progress` (network growth progress bar) and `candidate-epoch-progress` (candidate training progress bar) in a single callback. Since candidate epoch progress is being **copied** to the new tab (Section 4.2), splitting this handler requires:

1. The existing handler continues to output to its `candidate-epoch-progress` output (kept in Training Metrics)
2. The new `CandidateMetricsPanel` registers its **own** callback to update `candidate-metrics-panel-epoch-progress` from the training state store — **no modification** to the existing handler is needed

#### 4.5.4 Pool History Store Configuration

- **Maximum history entries**: 20 (oldest entries evicted when limit reached)
- **Storage type**: `dcc.Store(storage_type="memory")` — pool history is **lost on page refresh**. This is acceptable for real-time monitoring; persistent history is available via the backend's Cassandra store.

### 4.6 Tab Placement

The new Candidate Metrics tab should be placed immediately after Training Metrics in the tab bar, since it's the most closely related:

```bash
Training Metrics | Candidate Metrics | Network Topology | Decision Boundaries | ...
```

Tab ID: `"candidates"`

---

## 5. Implementation Approaches

### 5.1 Approach: Incremental Refactor (Recommended)

Build the contextual menu and candidate tab in sequential phases, maintaining a working application at each step.

**Phase 1**: Add wrapper divs to existing sidebar sections (no behavior change)
**Phase 2**: Add visibility callback driven by active tab
**Phase 3**: Create CandidateMetricsPanel component
**Phase 4**: Register new tab and wire up callbacks
**Phase 5**: Extract candidate content from MetricsPanel
**Phase 6**: Add new collapsible wrappers for contextual sections
**Phase 7**: Testing and polish

**Strengths**: Low risk per step, easy to test and rollback, working app at each phase.
**Weaknesses**: More commits, longer total development time.

### 5.2 Approach: Big Bang Refactor

Implement both enhancements simultaneously in a single branch/PR.

**Strengths**: Fewer intermediate states to manage, single coherent diff.
**Weaknesses**: Higher risk, harder to debug failures, difficult to review.

**Recommendation**: Incremental Refactor (5.1). The interplay between sidebar visibility and tab content is complex enough to warrant step-by-step validation.

---

## 6. Phased Implementation Plan

### Phase 1: Sidebar Decomposition (Structural Only)

**Goal**: Wrap existing sidebar sections in addressable `html.Div` containers without changing any behavior.

**Steps**:

| Step | Task                                                                                  | File                   | Effort |
|------|---------------------------------------------------------------------------------------|------------------------|--------|
| 1.1  | Add `id="sidebar-nn-top-params"` wrapper div around top-level NN params               | `dashboard_manager.py` | Low    |
| 1.2  | Add `id="sidebar-nn-growth-triggers"` wrapper div around growth triggers section      | `dashboard_manager.py` | Low    |
| 1.3  | Add `id="sidebar-nn-multi-node-layers"` wrapper div around multi-node checkbox        | `dashboard_manager.py` | Low    |
| 1.4  | Add `id="sidebar-nn-spiral-dataset"` wrapper div around spiral dataset section        | `dashboard_manager.py` | Low    |
| 1.5  | Add `id="sidebar-cn-pool-params"` wrapper div around CN top-level params              | `dashboard_manager.py` | Low    |
| 1.6  | Add `id="sidebar-cn-pool-training"` wrapper div around pool training complete section | `dashboard_manager.py` | Low    |
| 1.7  | Add `id="sidebar-cn-multi-candidate"` wrapper div around multi candidate section      | `dashboard_manager.py` | Low    |
| 1.8  | Add `id="sidebar-nn-section"` wrapper around entire NN subsection                     | `dashboard_manager.py` | Low    |
| 1.9  | Add `id="sidebar-cn-section"` wrapper around entire CN subsection                     | `dashboard_manager.py` | Low    |
| 1.10 | Add `id="sidebar-network-info-section"` wrapper around Network Info card              | `dashboard_manager.py` | Low    |
| 1.11 | Add `id="sidebar-meta-params-card"` to Meta Parameters card                           | `dashboard_manager.py` | Low    |
| 1.12 | Add `id="sidebar-meta-params-header"` to card header H5                               | `dashboard_manager.py` | Low    |
| 1.13 | Verify all existing callbacks still function correctly                                | Manual test            | Low    |

**Verification**: Run application, verify sidebar renders identically to current state.

### Phase 2: Contextual Visibility Callback

**Goal**: Implement the tab-driven sidebar visibility system.

**Steps**:

| Step | Task                                                                 | File                   | Effort |
|------|----------------------------------------------------------------------|------------------------|--------|
| 2.1  | Define `TAB_SIDEBAR_CONFIG` dict with visibility mapping per tab     | `dashboard_manager.py` | Medium |
| 2.2  | Define `SIDEBAR_SECTION_IDS` ordered list of all section wrapper IDs | `dashboard_manager.py` | Low    |
| 2.3  | Implement `_setup_sidebar_visibility_callback()` method              | `dashboard_manager.py` | Medium |
| 2.4  | Register callback in `_setup_callbacks()`                            | `dashboard_manager.py` | Low    |
| 2.5  | Add Meta Parameters card header dynamic text output to callback      | `dashboard_manager.py` | Low    |
| 2.6  | Test sidebar shows correct sections for each tab                     | Manual + unit test     | Medium |
| 2.7  | Test that hidden inputs preserve their values                        | Manual test            | Low    |
| 2.8  | Test Apply Parameters works from any tab                             | Manual test            | Low    |

**Verification**: Switch between all tabs, verify correct sections shown/hidden, verify parameter Apply still works.

### Phase 3: New Collapsible Section Wrappers

**Goal**: Add collapsible headers to sections that require them in the contextual menu.

**Steps**:

| Step | Task                                                                       | File                   | Effort |
|------|----------------------------------------------------------------------------|------------------------|--------|
| 3.1  | Add collapsible header + `dbc.Collapse` wrapper to Network Growth Triggers | `dashboard_manager.py` | Medium |
| 3.2  | Add collapsible header + `dbc.Collapse` wrapper to Multi-Node Layers       | `dashboard_manager.py` | Medium |
| 3.3  | Add collapsible header + `dbc.Collapse` wrapper to Spiral Dataset          | `dashboard_manager.py` | Medium |
| 3.4  | Add collapsible header + `dbc.Collapse` wrapper to Pool Training Complete  | `dashboard_manager.py` | Medium |
| 3.5  | Register toggle callbacks for all new collapsible sections                 | `dashboard_manager.py` | Medium |
| 3.6  | Verify collapse toggle works for each new section                          | Manual test            | Low    |

**Verification**: Each new collapsible section toggles correctly, icons update, content hides/shows.

### Phase 4: Create CandidateMetricsPanel Component

**Goal**: Build the new component file with layout and callbacks.

**Steps**:

| Step | Task                                                                              | File     | Effort |
|------|-----------------------------------------------------------------------------------|----------|--------|
| 4.1  | Create `candidate_metrics_panel.py` with class skeleton extending `BaseComponent` | New file | Low    |
| 4.2  | Implement `get_layout()` with status, candidates, metrics, plot, history sections | New file | High   |
| 4.3  | Implement `_create_candidate_pool_display()` (adapted from metrics_panel.py)      | New file | Medium |
| 4.4  | Implement candidate loss plot creation method                                     | New file | Medium |
| 4.5  | Implement pool history tracking and rendering (adapted from metrics_panel.py)     | New file | Medium |
| 4.6  | Implement `register_callbacks()` with all callback definitions                    | New file | High   |
| 4.7  | Add file header per juniper conventions                                           | New file | Low    |

**Verification**: Component can be imported and `get_layout()` returns valid Dash layout.

### Phase 5: Register Tab and Wire Up

**Goal**: Add the Candidate Metrics tab to the dashboard and connect everything.

**Steps**:

| Step | Task                                                                                                                                                                                 | File                   | Effort |
|------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|--------|
| 5.1  | Import `CandidateMetricsPanel` in `dashboard_manager.py`                                                                                                                             | `dashboard_manager.py` | Low    |
| 5.2  | Initialize component in `_initialize_components()`                                                                                                                                   | `dashboard_manager.py` | Low    |
| 5.3  | Add `dbc.Tab` entry after Training Metrics tab                                                                                                                                       | `dashboard_manager.py` | Low    |
| 5.4  | Add `"candidates"` entry to `TAB_SIDEBAR_CONFIG`                                                                                                                                     | `dashboard_manager.py` | Low    |
| 5.5  | ~~No changes~~ — active-tab-aware data store callbacks NOT updating; `CandidateMetricsPanel.register_callbacks()` register data fetch callback gated on `active_tab == "candidates"` | N/A                    | None   |
| 5.6  | Update localStorage tab persistence (no change needed — works automatically)                                                                                                         | N/A                    | None   |
| 5.7  | Verify tab renders and data updates in real-time                                                                                                                                     | Manual test            | Medium |

**Verification**: New tab appears, displays candidate data, updates in real-time.

### Phase 6: Extract Candidate Content from MetricsPanel

**Goal**: Remove extracted candidate content from the Training Metrics tab.

**Steps**:

| Step | Task                                                    | File               | Effort |
|------|---------------------------------------------------------|--------------------|--------|
| 6.1  | Remove candidate pool section from metrics_panel layout | `metrics_panel.py` | Medium |
| 6.2  | Remove pool history tracking callback                   | `metrics_panel.py` | Medium |
| 6.3  | Remove pool history rendering callback                  | `metrics_panel.py` | Medium |
| 6.4  | Remove `_create_candidate_pool_display()` method        | `metrics_panel.py` | Low    |
| 6.5  | Keep candidate training trace in loss plot              | `metrics_panel.py` | None   |
| 6.6  | Keep candidate epoch progress bar (provides context)    | `metrics_panel.py` | None   |
| 6.7  | Remove candidate-pools-history dcc.Store                | `metrics_panel.py` | Low    |
| 6.8  | Verify Training Metrics tab still works correctly       | Manual + unit test | Medium |
| 6.9  | Verify no orphaned callback references                  | Static analysis    | Low    |

**Verification**: Training Metrics tab functions correctly without candidate sections, no console errors.

### Phase 7: Testing & Polish

**Goal**: Comprehensive testing and final adjustments.

**Steps**:

| Step | Task                                                   | File                                                 | Effort   |
|------|--------------------------------------------------------|------------------------------------------------------|----------|
| 7.1  | Write unit tests for sidebar visibility callback       | `tests/unit/frontend/`                               | Medium   |
| 7.2  | Write unit tests for CandidateMetricsPanel layout      | `tests/unit/frontend/`                               | Medium   |
| 7.3  | Write integration test for tab switch + sidebar update | `tests/integration/`                                 | Medium   |
| 7.4  | Update existing meta parameters layout tests           | `tests/unit/frontend/test_meta_parameters_layout.py` | Medium   |
| 7.5  | Run full test suite and fix regressions                | All test files                                       | Variable |
| 7.6  | Verify dark mode works for all new components          | Manual test                                          | Low      |
| 7.7  | Verify demo mode works with new tab                    | Manual test                                          | Low      |
| 7.8  | Update CHANGELOG.md                                    | `CHANGELOG.md`                                       | Low      |

---

## 7. Risk Analysis & Guardrails

### 7.1 Risk Matrix

| Risk                                                       | Severity | Likelihood | Mitigation                                                                                                                                            |
|------------------------------------------------------------|----------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sidebar visibility callback breaks existing param tracking | High     | Low        | Phase 1 adds wrappers only; Phase 2 tested independently. `track_param_changes` monitors Input values, not display state.                             |
| Hidden inputs cause Apply Parameters to send stale data    | High     | Low        | Hidden inputs retain their values in DOM. `applied-params-store` always reflects last applied state. Test explicitly.                                 |
| CandidateMetricsPanel callbacks conflict with existing IDs | High     | Low        | Unique prefix `candidate-metrics-panel-` for all new IDs. Verify against Component ID Registry (Appendix).                                            |
| Loss plot candidate trace removed from Training Metrics    | Medium   | Medium     | Spec says keep it. Explicitly marked as "Keep" in Phase 6 steps.                                                                                      |
| Tab persistence breaks with new tab ID                     | Low      | Low        | localStorage saves string `"candidates"` — auto-compatible. Only risk: user's saved tab doesn't exist in older versions (fallback to "metrics").      |
| `init_params_from_backend` writes to hidden inputs         | Medium   | Low        | Hidden inputs accept Dash property updates normally. Test: switch to non-param tab, wait for init interval, switch back, verify values.               |
| Collapsible sections nested inside visibility wrappers     | Medium   | Low        | `dbc.Collapse` operates on `is_open` regardless of parent `display` state. No interaction issues.                                                     |
| Multi-node checkbox sync across NN/CN sections             | Medium   | Medium     | `sync_multi_node_checkboxes` c/b fires w/o vis. Both sections hidden, sync still works in DOM. If only one vis, sync updates the hidden one — benign. |
| Performance impact of sidebar visibility callback          | Low      | Low        | Single callback returning list of `{"display": "block"/"none"}` dicts. Negligible computation.                                                        |

### 7.2 Guardrails

1. **No removal of existing component IDs**: All existing IDs are preserved. New wrapper divs add IDs that don't conflict.
2. **Incremental phases**: Each phase produces a working application. Rollback to previous phase is possible.
3. **Backward compatibility**: Tab persistence falls back to "metrics" if saved tab doesn't exist. Old localStorage keys continue to work.
4. **Test gates**: Each phase has explicit verification criteria before proceeding.
5. **Demo mode**: All changes must work in demo mode (no real backend required).
6. **Dark mode**: All new components must use CSS variables (`var(--bg-card)`, etc.) for theme compatibility.
7. **Convention compliance**: New component follows `BaseComponent` pattern. File header per juniper conventions. IDs follow established naming patterns.
8. **Optional optimization**: Network Info update callbacks (`_update_network_info_handler`, `_update_network_details_handler`) could be gated on `active_tab` to skip API calls when the Network Info sidebar section is hidden. Not required for initial implementation — the overhead is minimal (updates happen on the existing interval regardless).

---

## 8. Testing Strategy

### 8.1 Unit Tests

| Test                                           | Target                   | Assertions                                             |
|------------------------------------------------|--------------------------|--------------------------------------------------------|
| `test_sidebar_section_ids_complete`            | `TAB_SIDEBAR_CONFIG`     | All section IDs in config exist in layout              |
| `test_sidebar_config_all_tabs`                 | `TAB_SIDEBAR_CONFIG`     | All tab IDs have config entries                        |
| `test_sidebar_training_control_always_visible` | Visibility callback      | Training Controls visible for every tab                |
| `test_sidebar_metrics_tab_sections`            | Visibility callback      | Correct sections for metrics tab                       |
| `test_sidebar_candidates_tab_sections`         | Visibility callback      | Correct sections for candidates tab                    |
| `test_sidebar_minimal_tabs`                    | Visibility callback      | HDF5/Redis/Cassandra/About show only Training Controls |
| `test_candidate_metrics_layout`                | CandidateMetricsPanel    | Layout contains all required component IDs             |
| `test_candidate_metrics_no_id_conflicts`       | CandidateMetricsPanel    | No ID overlaps with other components                   |
| `test_collapsible_sections_pattern`            | New collapsible wrappers | Correct structure and IDs                              |

### 8.2 Integration Tests

| Test                                   | Target                          | Assertions                                             |
|----------------------------------------|---------------------------------|--------------------------------------------------------|
| `test_tab_switch_sidebar_update`       | Full dashboard                  | Switching tabs updates sidebar visibility              |
| `test_param_values_persist_tab_switch` | Full dashboard                  | Parameter values preserved across tab switches         |
| `test_apply_params_from_any_tab`       | Full dashboard                  | Apply works regardless of which tab exposed the inputs |
| `test_candidate_tab_data_flow`         | CandidateMetricsPanel + backend | Pool data flows from backend to display                |
| `test_candidate_tab_history_tracking`  | CandidateMetricsPanel           | Pool history accumulates correctly                     |

### 8.3 Regression Tests

| Test                                          | Target        | Assertions                             |
|-----------------------------------------------|---------------|----------------------------------------|
| `test_training_metrics_no_candidate_section`  | MetricsPanel  | Candidate pool section removed         |
| `test_training_metrics_keeps_candidate_trace` | MetricsPanel  | Loss plot still shows candidate trace  |
| `test_existing_callbacks_unchanged`           | All callbacks | No callback signature changes          |
| `test_meta_parameters_layout_backward_compat` | Meta params   | All 22 inputs still exist and function |

---

## 9. File Impact Matrix

| File                                                      | Change Type         | Description                                                                                |
|-----------------------------------------------------------|---------------------|--------------------------------------------------------------------------------------------|
| `src/frontend/dashboard_manager.py`                       | **Major Modify**    | Sidebar decomposition, visibility callback, new tab registration, new collapsible sections |
| `src/frontend/components/candidate_metrics_panel.py`      | **New File**        | CandidateMetricsPanel component                                                            |
| `src/frontend/components/metrics_panel.py`                | **Moderate Modify** | Remove candidate pool section, history callbacks, pool display method                      |
| `src/frontend/components/__init__.py`                     | **No Change**       | Not needed — existing components use direct imports, not `__init__.py` re-exports           |
| `src/frontend/__init__.py`                                | **No Change**       | Not needed — `dashboard_manager.py` imports components directly via their module path       |
| `src/frontend/assets/controls.css`                        | **Minor Modify**    | Styles for new collapsible section wrappers (if needed)                                    |
| `src/frontend/assets/dark_mode.css`                       | **No Change**       | Existing `.collapsible-header` styles apply to new sections                                |
| `src/backend/training_monitor.py`                         | **No Change**       | CandidatePool class shared, no modifications                                               |
| `src/main.py`                                             | **No Change**       | API endpoints unchanged                                                                    |
| `src/canopy_constants.py`                                 | **No Change**       | Constants unchanged                                                                        |
| `src/tests/unit/frontend/test_meta_parameters_layout.py`  | **Modify**          | Update for new wrapper div IDs                                                             |
| `src/tests/unit/frontend/test_sidebar_visibility.py`      | **New File**        | Visibility callback tests                                                                  |
| `src/tests/unit/frontend/test_candidate_metrics_panel.py` | **New File**        | CandidateMetricsPanel unit tests                                                           |
| `src/tests/integration/test_contextual_sidebar.py`        | **New File**        | Integration tests for sidebar + tab interaction                                            |
| `CHANGELOG.md`                                            | **Modify**          | Document new features                                                                      |

---

## 10. Appendix: Component ID Registry

### 10.1 New Sidebar Wrapper IDs

| ID                             | Type     | Purpose                                |
|--------------------------------|----------|----------------------------------------|
| `sidebar-nn-section`           | html.Div | Neural Network subsection wrapper      |
| `sidebar-nn-top-params`        | html.Div | Top-level NN params wrapper            |
| `sidebar-nn-growth-triggers`   | html.Div | Growth triggers wrapper                |
| `sidebar-nn-multi-node-layers` | html.Div | Multi-node layers wrapper              |
| `sidebar-nn-spiral-dataset`    | html.Div | Spiral dataset wrapper                 |
| `sidebar-cn-section`           | html.Div | Candidate Nodes subsection wrapper     |
| `sidebar-cn-pool-params`       | html.Div | CN pool params wrapper                 |
| `sidebar-cn-pool-training`     | html.Div | Pool training complete wrapper         |
| `sidebar-cn-multi-candidate`   | html.Div | Multi candidate selection wrapper      |
| `sidebar-network-info-section` | html.Div | Network Information card wrapper       |
| `sidebar-meta-params-card`     | dbc.Card | Meta Parameters card (ID added)        |
| `sidebar-meta-params-header`   | html.H5  | Dynamic card header text               |
| `sidebar-nn-cn-divider`        | html.Hr  | Divider between NN and CN (for hiding) |
| `sidebar-params-divider`       | html.Hr  | Divider before Apply button            |
| `sidebar-apply-section`        | html.Div | Apply button wrapper                   |

### 10.2 New Collapsible Section IDs

| ID                             | Type         | Purpose                                |
|--------------------------------|--------------|----------------------------------------|
| `ctx-growth-triggers-header`   | html.H6      | Growth Triggers collapse header        |
| `ctx-growth-triggers-collapse` | dbc.Collapse | Growth Triggers collapse body          |
| `ctx-growth-triggers-icon`     | html.Span    | Growth Triggers collapse icon          |
| `ctx-multi-node-header`        | html.H6      | Multi-Node Layers collapse header      |
| `ctx-multi-node-collapse`      | dbc.Collapse | Multi-Node Layers collapse body        |
| `ctx-multi-node-icon`          | html.Span    | Multi-Node Layers collapse icon        |
| `ctx-spiral-dataset-header`    | html.H6      | Spiral Dataset collapse header         |
| `ctx-spiral-dataset-collapse`  | dbc.Collapse | Spiral Dataset collapse body           |
| `ctx-spiral-dataset-icon`      | html.Span    | Spiral Dataset collapse icon           |
| `ctx-pool-training-header`     | html.H6      | Pool Training Complete collapse header |
| `ctx-pool-training-collapse`   | dbc.Collapse | Pool Training Complete collapse body   |
| `ctx-pool-training-icon`       | html.Span    | Pool Training Complete collapse icon   |

### 10.3 New CandidateMetricsPanel Component IDs

| ID                                       | Type         | Purpose                      |
|------------------------------------------|--------------|------------------------------|
| `candidate-metrics-panel-status`               | html.Div     | Status badge                 |
| `candidate-metrics-panel-phase`                | html.Div     | Phase display                |
| `candidate-metrics-panel-pool-size`            | html.Div     | Pool size display            |
| `candidate-metrics-panel-pool-info`            | html.Div     | Pool info display            |
| `candidate-metrics-panel-candidate-toggle`     | html.H6      | Candidate section toggle     |
| `candidate-metrics-panel-toggle-icon`          | html.Span    | Candidate toggle icon        |
| `candidate-metrics-panel-epoch-progress`       | dbc.Progress | Candidate epoch progress bar |
| `candidate-metrics-panel-top-candidates`       | dbc.Table    | Top candidates table         |
| `candidate-metrics-panel-pool-metrics`         | html.Div     | Pool metrics cards           |
| `candidate-metrics-panel-loss-plot`            | dcc.Graph    | Candidate loss chart         |
| `candidate-metrics-panel-history-section`      | html.Div     | Pool history container       |
| `candidate-metrics-panel-history-toggle`       | html.H6      | History collapse header      |
| `candidate-metrics-panel-history-collapse`     | dbc.Collapse | History collapse body        |
| `candidate-metrics-panel-history-icon`         | html.Span    | History collapse icon        |
| `candidate-metrics-panel-training-state-store` | dcc.Store    | Training state data          |
| `candidate-metrics-panel-pool-history-store`   | dcc.Store    | Pool history data            |
| `candidate-metrics-panel-update-interval`      | dcc.Interval | Data refresh interval        |

### 10.4 Existing IDs — No Conflicts Verified

All new IDs use prefixes (`sidebar-`, `ctx-`, `candidate-metrics-panel-`) that do not overlap with any existing component IDs in the codebase. The existing prefixes are:

- `nn-` (Neural Network params)
- `cn-` (Candidate Nodes params)
- `network-info-` (Network Information)
- `metrics-panel-` (Training Metrics)
- `network-visualizer-` (Network Topology)
- `decision-boundary-` (Decision Boundaries)
- `dataset-plotter-` (Dataset View)
- `hdf5-snapshots-panel-` (HDF5 Snapshots)
- `redis-panel-` (Redis)
- `cassandra-panel-` (Cassandra)
- `worker-panel-` (Workers)
- `about-panel-` (About)
- `parameters-panel-` (Parameters)
- `tutorial-panel-` (Tutorial)

---

## 11. Implementation Results

**Date**: 2026-04-01
**Branch**: `feature/contextual-sidebar-candidate-tab` (juniper-canopy)

### 11.1 Phase Completion Summary

| Phase | Title | Status | Commits |
|-------|-------|--------|---------|
| Phase 1 | Sidebar Decomposition | COMPLETE | `234b85b` |
| Phase 2 | Contextual Visibility Callback | COMPLETE | `9596627` |
| Phase 3 | Collapsible Section Wrappers | COMPLETE | `6566588` |
| Phase 4 | CandidateMetricsPanel Component | COMPLETE | `39f2527` |
| Phase 5 | Register Tab and Wire Up | COMPLETE | `b995002` |
| Phase 6 | Extract Candidate Content | COMPLETE | `8133d84` |
| Phase 7 | Testing & Polish | COMPLETE | `31f88a2`, `3d4e378`, `d82a27a`, final commit |

### 11.2 Implementation Deviations from Design

1. **Status badge ID**: Implementation uses `candidate-metrics-panel-status-badge` instead of `candidate-metrics-panel-status`. The `-badge` suffix better conveys the visual purpose.

2. **Combined callbacks**: The design specified separate "Update top candidates" and "Update pool metrics" callbacks. Implementation combines them into a single `update_pool_info` callback that renders both within the `pool-info` container. This is architecturally simpler since both consume the same input (`training-state-store`).

3. **Separate epoch progress callback**: Implementation adds a dedicated `update_epoch_progress` callback not in the original design. This cleanly separates progress bar visibility/value from the status display callback.

4. **Pool details toggle**: Implementation adds a `toggle_pool_details` callback for the collapsible pool info section, providing better UX for the detailed pool view.

### 11.3 Test Coverage

| Test File | Type | Tests | Status |
|-----------|------|-------|--------|
| `test_sidebar_visibility.py` | Unit | 37 | NEW |
| `test_candidate_metrics_panel.py` | Unit | 31 | NEW |
| `test_dashboard_enhancements.py` | Integration | 1 fix | UPDATED |
| `test_dashboard_manager.py` | Unit | 1 fix | UPDATED |
| `test_dashboard_manager_coverage.py` | Unit | 1 fix | UPDATED |
| `test_meta_parameters_layout.py` | Unit | 1 fix | UPDATED |
| `test_metrics_panel_coverage.py` | Unit | 2 removed | UPDATED |
| `test_metrics_panel_handlers.py` | Unit | 2 removed | UPDATED |
| `test_metrics_panel_helpers_coverage.py` | Unit | 3 removed | UPDATED |

**Full suite**: 4000+ tests pass, 0 failures.

### 11.4 Files Changed

| File | Change | Lines |
|------|--------|-------|
| `src/frontend/dashboard_manager.py` | Major Modify | +1051/-853 |
| `src/frontend/components/candidate_metrics_panel.py` | New File | +702 |
| `src/frontend/components/metrics_panel.py` | Moderate Modify | -361 |
| `src/tests/unit/frontend/test_sidebar_visibility.py` | New File | +159 |
| `src/tests/unit/frontend/test_candidate_metrics_panel.py` | New File | +222 |
| `CHANGELOG.md` | Updated | +10 |
| 7 test files | Count/fixture fixes | ~-100 |

---

## End of Design Document
