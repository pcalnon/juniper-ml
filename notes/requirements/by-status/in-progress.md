# Requirements — status: in-progress

**Total entries**: 9

**By priority**: P0=1 | P1=4 | P2=4

**By category**: UI=4 | OBS=3 | TEST=1 | SEC=1

**By owner**: ml=9

---

### JR-ML-OBS-002 — Fix 7 stale Grafana dashboard panels in juniper-cascor.json and juniper-overview.json - 3 inference panels and 4 placeholder texts.

**Status**: in-progress  **Priority**: P0  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 125-135)

**Detail**:

G1 - Stale panels:
- 3 cascor inference panels query removed juniper_cascor_inference_* metrics
- 4 worker-bridge placeholder text panels never replaced with real PromQL
In-flight branch audit-fixup/stale-dashboard-panels exists as of 2026-05-06.

**Notes**:

Operational blocker. Recommend Option A - land in-flight PR + add dashboard-lint CI guardrail.

### JR-ML-TEST-003 — Complete comprehensive requirements audit and test plan for juniper-canopy with 16 action items.

**Status**: in-progress  **Priority**: P1  **Category**: TEST  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_REQUIREMENTS_AUDIT_AND_TEST_PLAN.md` (lines 1-100)

**Notes**:

Prerequisite for other canopy development items.

### JR-ML-UI-004 — Fix dataset display bug with comprehensive development plan.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/DATASET_DISPLAY_BUG_DEVELOPMENT_PLAN-FINAL.md` (lines 1-100)

**Notes**:

FINAL revision; check for duplicate with DEVELOPMENT_PLAN.md

### JR-ML-UI-005 — Fix decision boundary visualization in Canopy UI with implementation approach addressing NaN propagation and numerical instability.

**Status**: in-progress  **Priority**: P1  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DECISION_BOUNDARY_FIX_PLAN_V2.md` (lines 1-100)

**Notes**:

V2 revision addressing issues from initial plan.

### JR-ML-OBS-019 — Wire juniper_data_datasets_cached Gauge at every cache mutation site in juniper-data.

**Status**: in-progress  **Priority**: P1  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md` (lines 142-150)

**Detail**:

G3 - Dead Gauge with no production caller. Defined but never emitted.
In-flight sister PR exists. Add unit test asserting Gauge.value == len(cache) after each operation.

### JR-ML-OBS-053 — 2D. Phase Duration Display.

**Status**: in-progress  **Priority**: P2  **Category**: OBS  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/DASHBOARD_AUGMENTATION_PLAN.md` (lines 108-116)

**Detail**:

**File:** `src/frontend/components/metrics_panel.py`

### JR-ML-UI-020 — Fix candidate training display rendering issues in Canopy.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` (lines 1-100)

### JR-ML-UI-021 — Fix Canopy dashboard display issues with layout and rendering.

**Status**: in-progress  **Priority**: P2  **Category**: UI  **Owner**: ml

**Sources**:
- `juniper-ml/notes/legacy/CANOPY_DASHBOARD_DISPLAY_FIXES.md` (lines 1-100)

### JR-ML-SEC-111 — Step 1: Workspace Setup.

**Status**: in-progress  **Priority**: P2  **Category**: SEC  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/CONVERGENCE_UI_FIX_PLAN.md` (lines 48-70)

**Detail**:

- Branch: `main` with committed Phase 5.1/5.2 fixes
