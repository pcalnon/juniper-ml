# Dataset Display Fix — Development Plan

**Date**: 2026-03-30
**Analysis**: [DATASET_DISPLAY_FAILURE_ANALYSIS.md](DATASET_DISPLAY_FAILURE_ANALYSIS.md)

---

## Phase 1: Immediate Restoration (CRITICAL — ~5 minutes)

### Fix 1.1: Reinstall juniper-cascor-client from correct source (RC-1)

The JuniperCanopy conda env has an editable install pointing to a stale worktree. Reinstall from the main development directory.

```bash
/opt/miniforge3/envs/JuniperCanopy/bin/pip install -e /home/pcalnon/Development/python/Juniper/juniper-cascor-client
```

**Verification**:

```bash
/opt/miniforge3/envs/JuniperCanopy/bin/pip show juniper-cascor-client
# Editable project location should be: /home/pcalnon/Development/python/Juniper/juniper-cascor-client
/opt/miniforge3/envs/JuniperCanopy/bin/python -c "from juniper_cascor_client.client import JuniperCascorClient; print(hasattr(JuniperCascorClient, 'get_dataset_data'))"
# Should print: True
```

### Fix 1.2: Clean up stale worktree (RC-1 cleanup)

The worktree's branch (`fix/fake-client-response-envelope`) was merged via PR #11. Safe to remove.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
git worktree remove /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor-client--fix--fake-client-response-envelope--20260326-0410--9b2ca303
git worktree prune
```

---

## Phase 2: Defensive Resilience in juniper-canopy (HIGH — ~30 minutes)

### Fix 2.1: Broaden exception handling in adapter (RC-2 + CF-4)

**File**: `src/backend/cascor_service_adapter.py`

**Current** (line 691):

```python
except JuniperCascorClientError:
    return None
```

**Solution approaches**:

| Approach                             | Code                                                                 | Strengths                                                          | Weaknesses                                   |
|--------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------|----------------------------------------------|
| **A: Catch Exception (recommended)** | `except (JuniperCascorClientError, Exception) as e:` + warning log   | Matches `get_decision_boundary` pattern; catches all failure modes | Could mask genuine bugs if logging is missed |
| **B: Catch specific exceptions**     | `except (JuniperCascorClientError, AttributeError, TypeError) as e:` | Explicit about tolerated failures                                  | May miss other unexpected errors             |
| **C: hasattr guard + narrow catch**  | `if not hasattr(self._client, 'get_dataset_data'): return None`      | Clear diagnostic log for version mismatches                        | Doesn't help with other runtime errors       |

**Recommendation**: Combine A + C. The `hasattr` guard provides an actionable log message for version mismatches. The broadened `except` is a safety net for unexpected runtime errors. Both log at WARNING level.

```python
def get_dataset_data(self) -> Optional[Dict[str, Any]]:
    if not hasattr(self._client, "get_dataset_data"):
        self.logger.warning("Client does not support get_dataset_data (version mismatch?)")
        return None
    try:
        ...
    except (JuniperCascorClientError, Exception) as e:
        self.logger.warning("Failed to fetch dataset data: %s: %s", type(e).__name__, e)
        return None
```

### Fix 2.2: Audit other adapter exception handlers

Several other methods catch only `JuniperCascorClientError` and return defaults. These should be broadened to also catch `Exception` (with logging) where the method returns a safe default:

| Method                                | Line | Current Catch              | Returns | Action  |
|---------------------------------------|------|----------------------------|---------|---------|
| `_ServiceTrainingMonitor.is_training` | ~88  | `JuniperCascorClientError` | `False` | Broaden |
| `get_current_metrics`                 | ~102 | `JuniperCascorClientError` | `{}`    | Broaden |
| `get_recent_metrics`                  | ~116 | `JuniperCascorClientError` | `[]`    | Broaden |
| `network` property                    | ~315 | `JuniperCascorClientError` | `None`  | Broaden |
| `extract_network_topology`            | ~641 | `JuniperCascorClientError` | `None`  | Broaden |
| `get_dataset_info`                    | ~649 | `JuniperCascorClientError` | `None`  | Broaden |
| `get_dataset_data`                    | ~691 | `JuniperCascorClientError` | `None`  | Broaden |

**Leave as-is** (caller needs error details): `create_network`, `start_training_background`, training control methods (pause/resume/stop/reset).

### Fix 2.3: Add `response.ok` guard in dashboard handlers (CF-3)

**File**: `src/frontend/dashboard_manager.py`

Two handlers call `response.json()` without checking HTTP status:

1. `_update_dataset_store_handler` (lines 1770-1784): Add `if not response.ok: return None` before `.json()` at line 1779
2. `_update_boundary_dataset_store_handler` (lines 1807-1819): Same fix before `.json()` at line 1816

The pattern already exists in `_update_boundary_store_handler` (lines 1797-1799) — apply it to BOTH handlers above.

---

## Phase 3: FakeCascorClient Parity in juniper-cascor-client (HIGH — ~1 hour)

### Fix 3.1: Add `get_dataset_data()` to FakeCascorClient (RC-3)

**File**: `juniper_cascor_client/testing/fake_client.py`

**Solution approaches**:

| Approach                                             | Description                                                                     | Strengths                                                  | Weaknesses                                             |
|------------------------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------|--------------------------------------------------------|
| **A: Generate from scenario metadata (recommended)** | Use `samples`, `features`, `classes` from scenario to generate synthetic arrays | Meaningful data for visualization; exercises full pipeline | More code to write                                     |
| **B: Hardcoded minimal data**                        | Return fixed small arrays regardless of scenario                                | Simplest; quick to implement                               | Doesn't test dimension handling; useless for demo mode |

**Recommendation**: Approach A. Generate deterministic synthetic data using `sin`/`cos` arithmetic (matching the existing `generate_decision_boundary` pattern). This enables demo mode visualization and properly tests the adapter's target conversion logic (binary threshold vs argmax).

**Insert after** `get_dataset()` (line 640), before `get_decision_boundary()`:

```python
def get_dataset_data(self) -> Dict[str, Any]:
    """Get dataset arrays for visualization."""
    with self._lock:
        self._check_closed()
        self._maybe_raise_error("get_dataset_data")
        if self._dataset is None:
            raise JuniperCascorNotFoundError("No dataset loaded.")
        samples = self._dataset.get("train_samples", 4)
        features = self._dataset.get("features", 2)
        classes = self._dataset.get("classes", 2)
        train_x = generate_dataset_inputs(samples, features)
        train_y = generate_dataset_targets(samples, classes)
        return self._success_envelope({"train_x": train_x, "train_y": train_y})
```

### Fix 3.2: Add data generator functions to scenarios.py (CF-2)

**File**: `juniper_cascor_client/testing/scenarios.py`

Add after the existing `generate_decision_boundary` function:

- `generate_dataset_inputs(num_samples, num_features) -> List[List[float]]`: Deterministic using `math.sin`/`math.cos` seeded on sample index
- `generate_dataset_targets(num_samples, num_classes) -> List[List[float]]`: One-hot encoded; for binary (classes <= 2), returns `[[0.0], [1.0], ...]`; for multiclass, returns one-hot vectors

### Fix 3.3: Keep scenario metadata-only (design decision)

**Do NOT embed** `train_x`/`train_y` arrays in `TWO_SPIRAL_DATASET` or `XOR_DATASET`. The `service_backend.get_dataset()` fallback path (metadata → array fetch) is *correct behavior* for service mode. Embedding arrays would mask the fallback and prevent testing of the cross-repo integration path.

### Fix 3.4: Add FakeCascorClient dataset data tests

**File**: `tests/test_fake_client.py`

| Test                                      | Fixture          | Assertion                                                            |
|-------------------------------------------|------------------|----------------------------------------------------------------------|
| `test_get_dataset_data_returns_arrays`    | `fake_training`  | Has `train_x` (155 samples x 2 features) and `train_y` (155 samples) |
| `test_get_dataset_data_no_dataset_raises` | `fake_idle`      | Raises `JuniperCascorNotFoundError`                                  |
| `test_get_dataset_data_xor`               | `fake_converged` | Has 4 samples x 2 features                                           |
| `test_get_dataset_data_closed_raises`     | N/A              | Raises `JuniperCascorClientError` after `close()`                    |

---

## Phase 4: Version Governance in juniper-cascor-client (MEDIUM — ~10 minutes)

### Fix 4.1: Bump version to 0.3.0 and align (CF-1)

Current state has a pre-existing mismatch:

- `pyproject.toml` line 7: `version = "0.2.0"`
- `__init__.py` line 11: `__version__ = "0.1.0"`

Both should update to `0.3.0` to reflect the new public API method.

**Files**: `pyproject.toml`, `juniper_cascor_client/__init__.py`

### Fix 4.2: Version consistency check (future, optional)

Add CI step or test asserting `pyproject.toml` version == `__init__.__version__`. Out of scope for this fix.

---

## Phase 5: Regression Prevention in juniper-canopy (MEDIUM — ~45 minutes)

### Fix 5.1: Integration test with real FakeCascorClient

**Solution approaches**:

| Approach                                        | Description                                                                                                         | Strengths                                             | Weaknesses                                                     |
|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|----------------------------------------------------------------|
| **A: Full-path integration test (recommended)** | Construct `CascorServiceAdapter(FakeCascorClient("two_spiral_training"))` → `ServiceBackend(adapter).get_dataset()` | Catches real interface mismatches; tests entire chain | Slower test; requires FakeCascorClient fixes from Phase 3      |
| **B: Protocol/ABC enforcement**                 | Define `CascorClientProtocol` (typing.Protocol) for mypy                                                            | Catches missing methods at type-check time            | Doesn't test runtime behavior; may be noisy with existing code |

**Recommendation**: Both. Approach A catches runtime issues in CI. Approach B prevents the class of issue statically.

### Fix 5.2: Adapter AttributeError handling test

Add test to `test_response_normalization.py` where mock client raises `AttributeError` on `get_dataset_data`. Verify adapter returns `None` without raising.

---

## Implementation Sequence

```bash
Phase 1 (Immediate, ~5 min)           repo: environment + git
  1.1  Reinstall editable package       /opt/miniforge3/envs/JuniperCanopy/
  1.2  Remove stale worktree            juniper-cascor-client worktree

Phase 2 (Same day, ~30 min)           repo: juniper-canopy
  2.1  Broaden exception handling        cascor_service_adapter.py
  2.2  Audit other handler methods       cascor_service_adapter.py
  2.3  Add response.ok guards            dashboard_manager.py

Phase 3 (Same day, ~1 hour)           repo: juniper-cascor-client
  3.1  Add get_dataset_data to Fake      fake_client.py
  3.2  Add data generators               scenarios.py
  3.3  (No change — design decision)
  3.4  Add Fake dataset data tests       test_fake_client.py

Phase 4 (With Phase 3 commit)         repo: juniper-cascor-client
  4.1  Bump version to 0.3.0            pyproject.toml, __init__.py

Phase 5 (Next session, ~45 min)       repo: juniper-canopy
  5.1  Integration test with Fake        new or extended test file
  5.2  AttributeError handling test      test_response_normalization.py
```

### Dependencies

- Phase 1 first (restores user functionality)
- Phase 2 and Phase 3+4 can proceed in parallel (different repos)
- Phase 5 depends on Phase 3 (needs FakeCascorClient.get_dataset_data())
- After Phase 3+4 commit: re-run Phase 1.1 to pick up new version

---

## Risk Assessment

| Change                              | Risk                                       | Mitigation                                                   |
|-------------------------------------|--------------------------------------------|--------------------------------------------------------------|
| Broadening exception to `Exception` | Could mask genuine bugs                    | Always log at WARNING; review logs in monitoring             |
| Synthetic dataset generators        | May not match real CasCor response shape   | Validate dimensions against `test_client.py` response format |
| Version bump to 0.3.0               | Breaks editable installs in other envs     | Re-run `pip install -e .` in all consuming envs              |
| `hasattr` guard                     | False security if client interface changes | Pair with Protocol for static checking                       |
