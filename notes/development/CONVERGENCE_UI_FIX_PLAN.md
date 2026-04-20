# Plan: Fix Convergence UI Controls — juniper-canopy

**Created**: 2026-03-19
**Author**: Paul Calnon (via Claude Code)
**Status**: COMPLETE — All bugs fixed in Phase 5.1/5.2 (commits c8f2740, e11b100), regression tests passing (47/47)
**Scope**: juniper-canopy (primary), juniper-ml (plan coordination)

---

## Context

The juniper-canopy Phase 5 enhancement added convergence-based sliding window controls (checkbox + threshold input) to the Training Parameters panel. The user reports 4 bugs:

1. **B-5.1**: Unchecking checkbox + Apply → checkbox restores to checked
2. **B-5.2**: Changing threshold + Apply → reverts to default
3. **B-5.3**: Meta-parameter values refreshed every few seconds (overwrites user edits)
4. **B-5.4**: Meta-parameter section missing section heading

**Finding**: These 4 bugs were already documented and fixed in Phase 5.1 (commit `c8f2740`) and Phase 5.2 (commit `e11b100`), merged via PR #34. The fixes are:

- Removed continuous `sync_backend_params` / `sync_input_values_from_backend` callbacks (B-5.1, B-5.2, B-5.3)
- Added one-shot `params-init-interval` with `max_intervals=1` (B-5.6)
- Split "Training Controls" card into "Training Controls" (buttons) + "Training Parameters" (inputs) (B-5.4)
- Merged convergence params into `/api/state` (B-5.5)
- `_track_param_changes_handler` returns `dash.no_update` for status when no changes (B-5.7)

**Additionally**: The canopy repo has uncommitted Phase 6 changes (training improvements + spiral_rotations UI parameter) that extend the working pattern but don't reintroduce any bugs.

**Test status**: 47/47 convergence-specific tests pass with current code.

---

## What Needs to Be Done

Since the bug fixes are already committed, the work is:

1. **Workspace setup**: Handle dirty canopy repo state, create worktree
2. **Validate fixes**: Run tests, trace each bug fix through code
3. **Add regression tests**: Explicit B-5.x regression tests targeting each original bug
4. **Organize and commit Phase 6 work**: The uncommitted changes need proper commits
5. **Update plan document**: Add Phase 5.3 (this validation/regression work)
6. **PR and cleanup**

---

## Implementation

### Step 1: Workspace Setup

**Canopy repo state** (`/home/pcalnon/Development/python/Juniper/juniper-canopy/`):

- Branch: `main` with committed Phase 5.1/5.2 fixes
- Staged changes: `canopy_constants.py`, `demo_mode.py`, 3 test files, new `test_phase6_implementation.py`
- Unstaged changes: `dashboard_manager.py`, `main.py`, `demo_backend.py`, 8+ test files

**Actions**:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git stash -u --message "Phase 6 + spiral_rotations WIP"
git fetch origin && git pull origin main
BRANCH_NAME="fix/convergence-ui-validation"
git branch "$BRANCH_NAME" main
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--convergence-ui-validation--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
git stash pop
```

### Step 2: Validate Existing Fixes

Run full test suite:

```bash
conda activate JuniperPython
cd src && pytest tests/ -v --tb=short
```

Run convergence-specific tests:

```bash
pytest tests/unit/test_convergence_ui_controls.py -v
pytest tests/integration/test_apply_button_parameters.py -v
```

Code-level verification for each bug:

| Bug | Verification |
|-----|-------------|
| B-5.1 | `_apply_parameters_handler` stores `"enabled" in (conv_enabled or [])` → correct boolean. No continuous sync. |
| B-5.2 | `_apply_parameters_handler` stores `float(conv_threshold)` → user's value. No overwrite. |
| B-5.3 | `params-init-interval` has `max_intervals=1`. No `backend-params-state` store. No `sync_backend_params` callback. |
| B-5.4 | Two separate cards: "Training Controls" (line 373) and "Training Parameters" (line 419). |

### Step 3: Add Regression Tests

#### New file: `src/tests/unit/test_convergence_ui_regression.py`

~20 regression tests organized by bug ID:

- **TestB51_CheckboxDoesNotRevertAfterApply** (3 tests)
  - Apply with unchecked → store has `convergence_enabled=False`
  - Track changes after unchecked apply → no diff detected
  - No continuous sync callback exists in callback map

- **TestB52_ThresholdDoesNotRevertAfterApply** (3 tests)
  - Apply with custom threshold → store has that value
  - Track changes after custom apply → no diff detected
  - Multiple apply cycles preserve value

- **TestB53_NoPeriodicMetaParameterRefresh** (3 tests)
  - `params-init-interval` has `max_intervals=1`
  - Init handler returns `no_update` when `current_applied` is truthy
  - No `backend-params-state` store in layout

- **TestB54_SeparateTrainingParametersCard** (3 tests)
  - "Training Controls" card has header
  - "Training Parameters" card has header
  - Buttons in controls card, inputs in parameters card

- **TestB55_ApiStateIncludesConvergenceParams** (3 tests)
  - `/api/state` has `convergence_enabled`
  - `/api/state` has `convergence_threshold`
  - Changed values reflected in `/api/state`

- **TestB56_InitCallbackFiresOnlyOnce** (2 tests)
  - Uses `params-init-interval`, not `slow-update-interval`
  - `max_intervals=1` prevents repeated firing

- **TestB57_StatusMessagePreserved** (3 tests)
  - No changes → `dash.no_update` for status
  - Changes detected → "⚠️ Unsaved changes"
  - Successful apply → "✓ Parameters applied"

#### New file: `src/tests/unit/frontend/test_convergence_layout.py`

~8 layout structure tests:

- Checkbox exists with correct ID and default value
- Threshold input exists with correct min/max/step/default
- Apply button exists
- `applied-params-store` exists
- `params-init-interval` exists with `max_intervals=1`
- Spiral rotations input exists

### Step 4: Commit Strategy

Three logical commits:

1. **Phase 6 training improvements**: Constants, demo_mode algorithm changes, demo_backend, phase6 tests
2. **Spiral rotations UI**: dashboard_manager, main.py, all test signature updates
3. **Convergence regression tests**: New regression test files, layout tests

### Step 5: Update Plan Document

Add Phase 5.3 section to `notes/CASCOR_DEMO_TRAINING_ERROR_PLAN.md` documenting:

- Validation results
- New regression test inventory
- Test-to-bug mapping

### Step 6: PR and Worktree Cleanup

```bash
git push origin fix/convergence-ui-validation
gh pr create --base main --head fix/convergence-ui-validation
```

Then follow `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.

---

## Critical Files

| File | Purpose |
|------|---------|
| `src/frontend/dashboard_manager.py` | UI layout, callback handlers |
| `src/main.py` | `/api/state`, `/api/set_params` endpoints |
| `src/demo_mode.py` | DemoMode convergence logic, apply_params |
| `src/backend/demo_backend.py` | DemoBackend wrapper |
| `src/canopy_constants.py` | TrainingConstants |
| `src/tests/unit/test_convergence_ui_controls.py` | Existing convergence tests |
| `src/tests/integration/test_apply_button_parameters.py` | Existing API tests |
| `src/tests/unit/test_convergence_ui_regression.py` | **NEW** — B-5.x regression tests |
| `src/tests/unit/frontend/test_convergence_layout.py` | **NEW** — Layout structure tests |

---

## Verification

1. `cd src && pytest tests/ -v --tb=short` — full suite passes
2. `pytest tests/unit/test_convergence_ui_regression.py -v` — all regression tests pass
3. `pytest tests/unit/frontend/test_convergence_layout.py -v` — all layout tests pass
4. `pytest tests/unit/test_convergence_ui_controls.py tests/integration/test_apply_button_parameters.py -v` — existing convergence tests still pass

---

## Document History

| Date       | Author      | Change |
|------------|-------------|--------|
| 2026-03-19 | Paul Calnon | Initial creation — plan for convergence UI fix validation and regression tests |
