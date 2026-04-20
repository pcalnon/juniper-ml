# Dataset View Tab Display Bug — Development Plan

**Date**: 2026-03-30
**Related Analysis**: [DATASET_DISPLAY_BUG_ANALYSIS.md](DATASET_DISPLAY_BUG_ANALYSIS.md)
**Affected Component**: Juniper Canopy Dashboard → Dataset View Tab
**Status**: Plan drafted

---

## Table of Contents

- [Summary](#summary)
- [Phase 1: Immediate Fix — Restore Dataset Display](#phase-1-immediate-fix--restore-dataset-display)
  - [Step 1.1: Re-install juniper-cascor-client from main repo](#step-11-re-install-juniper-cascor-client-from-main-repo)
  - [Step 1.2: Verify the fix](#step-12-verify-the-fix)
- [Phase 2: Testing Gap Closure](#phase-2-testing-gap-closure)
  - [Step 2.1: Add get\_dataset\_data() to FakeCascorClient](#step-21-add-get_dataset_data-to-fakecascorclient)
  - [Step 2.2: Add interface conformance test](#step-22-add-interface-conformance-test)
  - [Step 2.3: Add tests for get\_dataset\_data() through CascorServiceAdapter](#step-23-add-tests-for-get_dataset_data-through-cascorserviceadapter)
- [Phase 3: Dashboard Resilience](#phase-3-dashboard-resilience)
  - [Step 3.1: Add response.ok checks to all 6 affected handlers](#step-31-add-responseok-checks-to-all-6-affected-handlers)
- [Phase 4: Worktree Cleanup](#phase-4-worktree-cleanup)
  - [Step 4.1: Remove the specific stale worktree causing this bug](#step-41-remove-the-specific-stale-worktree-causing-this-bug)
  - [Step 4.2: Clean up all stale worktrees](#step-42-clean-up-all-stale-worktrees)
  - [Step 4.3: Add worktree hygiene automation (optional)](#step-43-add-worktree-hygiene-automation-optional)
- [Phase 5: Preventive Measures](#phase-5-preventive-measures)
  - [Step 5.1: Add a startup check to Canopy](#step-51-add-a-startup-check-to-canopy)
- [Summary Table](#summary-table)

---

## Summary

This plan addresses all root causes and contributing factors identified in [DATASET_DISPLAY_BUG_ANALYSIS.md](DATASET_DISPLAY_BUG_ANALYSIS.md). Work is organized into five phases, ordered by priority:

1. **Immediate Fix** — Restore the Dataset View tab by re-installing the client package
2. **Testing Gap Closure** — Prevent recurrence by closing the `FakeCascorClient` API surface gap
3. **Dashboard Resilience** — Add missing `response.ok` checks to prevent cascading errors
4. **Worktree Cleanup** — Remove 51 stale worktrees and the specific worktree that caused this bug
5. **Preventive Measures** — Add startup validation to catch stale installs early

Each step includes multiple solution approaches where applicable, with strengths, weaknesses, and a recommendation.

---

## Phase 1: Immediate Fix — Restore Dataset Display

> **Priority**: Critical | **Effort**: < 30 min

**Goal**: Get the Dataset View tab working again immediately.

### Step 1.1: Re-install juniper-cascor-client from main repo

**Task**: Re-install the editable package in JuniperCanopy from the correct source directory, replacing the stale worktree-based editable install.

#### Approach A — Re-install editable from main source

```bash
conda activate JuniperCanopy
pip install -e /home/pcalnon/Development/python/Juniper/juniper-cascor-client
```

| Dimension          | Assessment                                                                                                        |
|--------------------|-------------------------------------------------------------------------------------------------------------------|
| **Strengths**      | Minimal effort, immediately resolves the AttributeError, JuniperCanopy always picks up latest main branch changes |
| **Weaknesses**     | Editable installs remain fragile — any future worktree `pip install` could repeat this issue                      |
| **Recommendation** | ✅ **Recommended as the immediate fix**                                                                           |

#### Approach B — Install pinned release version (non-editable)

```bash
conda activate JuniperCanopy
pip install juniper-cascor-client==0.2.0
```

| Dimension          | Assessment                                                                                                                                   |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **Strengths**      | Stable, version-locked, immune to worktree path issues                                                                                       |
| **Weaknesses**     | Requires publishing to PyPI/TestPyPI first; won't pick up development changes automatically; adds a publish step to the development workflow |
| **Recommendation** | Consider for production/CI environments but not for active development                                                                       |

### Step 1.2: Verify the fix

**Task**: Confirm `get_dataset_data()` is now available and the Dataset View works.

```bash
/opt/miniforge3/envs/JuniperCanopy/bin/python -c "
from juniper_cascor_client.client import JuniperCascorClient
c = JuniperCascorClient.__new__(JuniperCascorClient)
print('has get_dataset_data:', hasattr(c, 'get_dataset_data'))
"
```

**Expected output**: `has get_dataset_data: True`

Then start the Canopy dashboard and open the Dataset View tab to confirm dataset scatter plots render correctly.

---

## Phase 2: Testing Gap Closure

> **Priority**: High | **Effort**: 1-2 hours

**Goal**: Ensure `FakeCascorClient` matches the real client's API surface to prevent similar issues.

### Step 2.1: Add get\_dataset\_data() to FakeCascorClient

**File**: `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py`

#### Approach A — Minimal stub returning stored dataset arrays

```python
def get_dataset_data(self) -> Dict[str, Any]:
    """Get dataset arrays for visualization."""
    with self._lock:
        self._check_closed()
        self._maybe_raise_error("get_dataset_data")
        if self._dataset is None:
            return self._success_envelope({})
        result = {}
        if "train_x" in self._dataset:
            result["train_x"] = copy.deepcopy(self._dataset["train_x"])
        if "train_y" in self._dataset:
            result["train_y"] = copy.deepcopy(self._dataset["train_y"])
        if "val_x" in self._dataset:
            result["val_x"] = copy.deepcopy(self._dataset["val_x"])
        if "val_y" in self._dataset:
            result["val_y"] = copy.deepcopy(self._dataset["val_y"])
        return self._success_envelope(result)
```

| Dimension          | Assessment                                                                                                            |
|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Strengths**      | Simple, follows existing `FakeCascorClient` patterns, directly maps to real client behavior                           |
| **Weaknesses**     | Requires the fake dataset to contain array data fields (`train_x`, `train_y`) which may not always be set up in tests |
| **Recommendation** | ✅ **Recommended**                                                                                                    |

#### Approach B — Derive arrays from stored dataset metadata

Generate synthetic `train_x`/`train_y` arrays from the dataset metadata (`num_samples`, `num_features`, etc.) so tests don't need to set up raw arrays.

| Dimension          | Assessment                                                                                       |
|--------------------|--------------------------------------------------------------------------------------------------|
| **Strengths**      | Tests get plausible data without manual array setup                                              |
| **Weaknesses**     | More complex, synthetic data may not match real patterns, test behavior diverges from production |
| **Recommendation** | Not recommended — keep test doubles simple                                                       |

### Step 2.2: Add interface conformance test

**File**: `juniper-cascor-client/tests/test_fake_client_conformance.py` (new file)

#### Approach A — Method name check

```python
def test_fake_client_matches_real_client_api():
    real_methods = {
        m for m in dir(JuniperCascorClient)
        if not m.startswith('_') and callable(getattr(JuniperCascorClient, m))
    }
    fake_methods = {
        m for m in dir(FakeCascorClient)
        if not m.startswith('_') and callable(getattr(FakeCascorClient, m))
    }
    missing = real_methods - fake_methods
    assert not missing, f"FakeCascorClient is missing methods: {missing}"
```

| Dimension          | Assessment                                                   |
|--------------------|--------------------------------------------------------------|
| **Strengths**      | Simple, catches missing methods immediately, low maintenance |
| **Weaknesses**     | Doesn't verify method signatures match                       |
| **Recommendation** | ✅ **Recommended as a minimum**                              |

#### Approach B — Method name + signature check

Use `inspect.signature()` to also verify parameter names and types match between the real client and the fake client.

| Dimension          | Assessment                                                                     |
|--------------------|--------------------------------------------------------------------------------|
| **Strengths**      | Catches signature drift (different parameter names, missing parameters)        |
| **Weaknesses**     | Slightly more complex, may be overly strict for optional parameter differences |
| **Recommendation** | Recommended as an enhancement to Approach A                                    |

### Step 2.3: Add tests for get\_dataset\_data() through CascorServiceAdapter

**File**: Add tests in `juniper-canopy/tests/` that exercise the `CascorServiceAdapter.get_dataset_data()` → `FakeCascorClient.get_dataset_data()` path.

**Task**: Write integration-level tests that call `CascorServiceAdapter.get_dataset_data()` with a `FakeCascorClient` injected, verifying:

1. The adapter calls `get_dataset_data()` on the client (not `get_dataset()`)
2. The response is correctly unwrapped and returned to the caller
3. Error cases (client returns error envelope, client raises exception) are handled gracefully

---

## Phase 3: Dashboard Resilience

> **Priority**: Medium | **Effort**: 1-2 hours

**Goal**: Add `response.ok` checks to all dashboard API handlers to prevent secondary `JSONDecodeError` failures.

### Step 3.1: Add response.ok checks to all 6 affected handlers

**File**: `juniper-canopy/src/frontend/dashboard_manager.py`

**Affected handlers** (all need the same pattern):

| # | Handler                                  | Line | Endpoint               |
|---|------------------------------------------|------|------------------------|
| 1 | `_update_network_info_handler`           | 1637 | `/api/status`          |
| 2 | `_update_network_info_details_handler`   | 1708 | `/api/network/stats`   |
| 3 | `_update_metrics_store_handler`          | 1732 | `/api/metrics/history` |
| 4 | `_update_topology_store_handler`         | 1762 | `/api/topology`        |
| 5 | `_update_dataset_store_handler`          | 1778 | `/api/dataset`         |
| 6 | `_update_boundary_dataset_store_handler` | 1815 | `/api/dataset`         |

#### Approach A — Add inline response.ok check to each handler

Add `if not response.ok: self.logger.warning(...); return None` before `response.json()` in each handler, matching the existing pattern at lines 1797–1798.

| Dimension          | Assessment                                                                               |
|--------------------|------------------------------------------------------------------------------------------|
| **Strengths**      | Minimal change, consistent with existing pattern in the boundary handler, easy to review |
| **Weaknesses**     | Repetitive — same check in 6 places                                                      |
| **Recommendation** | ✅ **Recommended**                                                                       |

#### Approach B — Extract a helper method

```python
def _api_get(self, endpoint: str, timeout: int = None) -> Optional[dict]:
    """Fetch JSON from an API endpoint, returning None on failure."""
    try:
        url = self._api_url(endpoint)
        response = requests.get(url, timeout=timeout or DashboardConstants.API_TIMEOUT_SECONDS)
        if not response.ok:
            self.logger.warning(f"API {endpoint} returned {response.status_code}")
            return None
        return response.json()
    except Exception as e:
        self.logger.warning(f"Failed to fetch {endpoint}: {type(e).__name__}: {e}")
        return None
```

| Dimension          | Assessment                                                                               |
|--------------------|------------------------------------------------------------------------------------------|
| **Strengths**      | DRY, single place to add logging/error handling, reduces boilerplate across all handlers |
| **Weaknesses**     | Slightly more refactoring, changes the pattern used by existing working handlers         |
| **Recommendation** | Recommended as a follow-up improvement                                                   |

---

## Phase 4: Worktree Cleanup

> **Priority**: Medium | **Effort**: 30-60 min

**Goal**: Remove all 51 stale worktrees and prevent future accumulation.

### Step 4.1: Remove the specific stale worktree causing this bug

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
git worktree remove /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor-client--fix--fake-client-response-envelope--20260326-0410--9b2ca303
git worktree prune
```

### Step 4.2: Clean up all stale worktrees

Use the existing `scripts/worktree_cleanup.bash` or manual cleanup for all 51 stale worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/`.

Stale worktree breakdown:

| Category                                               | Count  | Date Range |
|--------------------------------------------------------|--------|------------|
| `juniper-canopy-cascor--fix--connect-canopy-cascor--*` | 35     | Mar 24-25  |
| `juniper-cascor--*`                                    | 6      | Mar 2-16   |
| `juniper-data--*` / `juniper-data-client--*`           | 4      | Mar 3-12   |
| `juniper-deploy--*`                                    | 3      | Mar 3-12   |
| `juniper-cascor-worker--*`                             | 2      | Mar 3-12   |
| `juniper-cascor-client--*`                             | 1      | Mar 26     |
| **Total**                                              | **51** |            |

### Step 4.3: Add worktree hygiene automation (optional)

#### Approach A — Pre-commit hook that warns about stale worktrees

| Dimension      | Assessment                              |
|----------------|-----------------------------------------|
| **Strengths**  | Passive notification, no forced cleanup |
| **Weaknesses** | Easy to ignore                          |

#### Approach B — Scheduled cleanup script

A cron job or git hook that checks for worktrees whose branches have been merged and reminds/offers cleanup.

| Dimension      | Assessment                                                         |
|----------------|--------------------------------------------------------------------|
| **Strengths**  | Proactive, prevents accumulation                                   |
| **Weaknesses** | Requires careful implementation to avoid deleting active worktrees |

---

## Phase 5: Preventive Measures

> **Priority**: Low | **Effort**: 2-4 hours

**Goal**: Prevent stale editable installs from causing runtime failures.

### Step 5.1: Add a startup check to Canopy

Add a check in juniper-canopy's startup sequence that verifies the installed `juniper-cascor-client` provides all required methods.

#### Approach A — Version check at import time

```python
import juniper_cascor_client

expected_version = "0.2.0"
if juniper_cascor_client.__version__ != expected_version:
    logger.warning(
        f"juniper-cascor-client version mismatch: "
        f"{juniper_cascor_client.__version__} != {expected_version}"
    )
```

| Dimension      | Assessment                                                 |
|----------------|------------------------------------------------------------|
| **Strengths**  | Simple, catches version drift                              |
| **Weaknesses** | Fragile — version must be updated manually on each release |

#### Approach B — Method existence check at startup

```python
required_methods = ['get_dataset_data', 'get_decision_boundary', ...]
missing = [m for m in required_methods if not hasattr(JuniperCascorClient, m)]
if missing:
    logger.error(
        f"juniper-cascor-client is missing required methods: {missing}"
    )
```

| Dimension          | Assessment                                                               |
|--------------------|--------------------------------------------------------------------------|
| **Strengths**      | Catches the exact failure mode that caused this bug, version-independent |
| **Weaknesses**     | Must maintain a list of required methods                                 |
| **Recommendation** | ✅ **Recommended** — catches the specific problem class                  |

---

## Summary Table

| Phase | Priority | Effort    | Description                                      |
|-------|----------|-----------|--------------------------------------------------|
| 1     | Critical | < 30 min  | Re-install client from main, verify fix          |
| 2     | High     | 1-2 hrs   | Add missing fake method, conformance test        |
| 3     | Medium   | 1-2 hrs   | Add `response.ok` checks to 6 dashboard handlers |
| 4     | Medium   | 30-60 min | Clean up 51 stale worktrees                      |
| 5     | Low      | 2-4 hrs   | Add startup validation checks                    |
