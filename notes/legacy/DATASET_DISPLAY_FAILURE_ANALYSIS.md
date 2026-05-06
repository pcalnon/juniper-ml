# Dataset Display Failure Analysis

**Date**: 2026-03-30
**Symptom**: Dataset View tab in Canopy dashboard fails with `AttributeError: 'JuniperCascorClient' object has no attribute 'get_dataset_data'`

---

## Root Causes

### RC-1: Stale Worktree Editable Install (PRIMARY)

The JuniperCanopy conda environment has `juniper-cascor-client v0.2.0` installed as an editable package, but it points to a **stale worktree** rather than the main development directory:

| Environment   | Install Source                                                                                                                                                         | Has `get_dataset_data()`? |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| JuniperPython | `/home/pcalnon/Development/python/Juniper/juniper-cascor-client` (main, commit `6ed0fda`)                                                                              | Yes                       |
| JuniperCanopy | `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor-client--fix--fake-client-response-envelope--20260326-0410--9b2ca303` (old branch, commit `d144a7c`) | **No**                    |

The worktree was created on 2026-03-26 for a FakeCascorClient fix. The `get_dataset_data()` method was added on 2026-03-30 in commit `6ed0fda`. The JuniperCanopy env still points to the pre-feature worktree.

Both environments report version `0.2.0`, masking the mismatch — the version was not bumped when the feature was added.

### RC-2: Narrow Exception Handling in CascorServiceAdapter

`cascor_service_adapter.py` line 691 catches only `JuniperCascorClientError`:

```python
except JuniperCascorClientError:
    return None
```

An `AttributeError` (from calling a non-existent method) is not a subclass of `JuniperCascorClientError`, so it escapes the handler and propagates as an unhandled HTTP 500 error.

### RC-3: Missing `get_dataset_data()` in FakeCascorClient

The `FakeCascorClient` class in `juniper_cascor_client/testing/fake_client.py` does not implement `get_dataset_data()`. It has `get_dataset()` and `get_decision_boundary()` but omits the data array method. This means:

- Demo/fake mode would also fail on the same code path
- No test could catch this regression via FakeCascorClient

---

## Contributing Factors

### CF-1: Version Number Not Bumped on Feature Addition

Both the old worktree and the new main code report `v0.2.0`. Adding `get_dataset_data()` should have bumped the version (e.g., to `0.3.0`), which would have made the mismatch visible via `pip show`.

### CF-2: Test Scenario Data Lacks Array Fields

The test scenarios in `juniper_cascor_client/testing/scenarios.py` contain only metadata (`train_samples`, `test_samples`, `features`, `classes`) but not `inputs`/`targets` arrays. This means the `service_backend.get_dataset()` fallback path (line 173: `if "inputs" not in result`) is always triggered in service mode, forcing the call to `get_dataset_data()`.

### CF-3: Frontend Error Cascading

When the backend returns HTTP 500, the dashboard's `_update_dataset_store_handler` attempts `response.json()` which fails with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` because the 500 response is HTML, not JSON. The user sees no dataset and a cryptic secondary error in logs.

### CF-4: No `hasattr` Guard Before Client Method Call

The `cascor_service_adapter.get_dataset_data()` calls `self._client.get_dataset_data()` without checking if the method exists. A defensive `hasattr()` check or broader exception handling would have prevented the crash.

---

## Error Call Chain

```bash
User opens Dataset View tab
    |
Dashboard calls GET /api/dataset
    |
main.py:727 -> backend.get_dataset()
    |
service_backend.py:157 -> adapter.get_dataset_info()   [returns metadata-only dict]
service_backend.py:173 -> "inputs" not in result        [True, metadata has no arrays]
service_backend.py:174 -> adapter.get_dataset_data()    [fallback path triggered]
    |
cascor_service_adapter.py:669 -> self._client.get_dataset_data()
    |
JuniperCascorClient (installed from stale worktree) has no get_dataset_data()
    |
AttributeError raised
    |
cascor_service_adapter.py:691 -> except JuniperCascorClientError  [does NOT catch AttributeError]
    |
Exception propagates to FastAPI -> HTTP 500
    |
dashboard_manager.py:1779 -> response.json()  [JSONDecodeError on HTML error page]
    |
Dataset View shows empty / "No data available"
```

---

## Verification Evidence

### Installed Package Locations

```bash
# JuniperCanopy (STALE)
$ /opt/miniforge3/envs/JuniperCanopy/bin/pip show juniper-cascor-client
Version: 0.2.0
Editable project location: /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor-client--fix--fake-client-response-envelope--20260326-0410--9b2ca303

# JuniperPython (CORRECT)
$ /opt/miniforge3/envs/JuniperPython/bin/pip show juniper-cascor-client
Version: 0.2.0
Editable project location: /home/pcalnon/Development/python/Juniper/juniper-cascor-client
```

### Method Presence

```bash
# Development main (correct): client.py has 305 lines, get_dataset_data at line 219
# Stale worktree (broken): client.py has 301 lines, no get_dataset_data
```

### Cascor Endpoint Status

The server-side endpoint `GET /v1/dataset/data` exists and is deployed:

- Route: `juniper-cascor/src/api/routes/dataset.py` lines 24-31
- Manager: `juniper-cascor/src/api/lifecycle/manager.py` lines 591-602
- Registration: `juniper-cascor/src/api/app.py` line 298
- Committed: `57df9de` (2026-03-30)
- Editable install in JuniperCascor env points to development directory (correct)

---

## Impact Assessment

| Impact                       | Severity | Description                                                                    |
|------------------------------|----------|--------------------------------------------------------------------------------|
| Dataset visualization broken | HIGH     | Users cannot view loaded dataset in service mode                               |
| Error log noise              | MEDIUM   | HTTP 500 + JSONDecodeError logged on every tab switch                          |
| Demo/fake mode affected      | HIGH     | FakeCascorClient also missing the method                                       |
| No regression detection      | MEDIUM   | Tests pass because they don't exercise the fallback path with FakeCascorClient |

---

## Recommendations

1. **Immediate fix**: Reinstall `juniper-cascor-client` in JuniperCanopy env from the main development directory
2. **Add `get_dataset_data()` to FakeCascorClient** for demo mode parity
3. **Broaden exception handling** in `cascor_service_adapter.get_dataset_data()` to catch `Exception` or add `AttributeError`
4. **Clean up stale worktree** that the JuniperCanopy env was pointing to
5. **Add `hasattr` guard** or try/except around client method calls for forward compatibility
6. **Bump version** when adding public API methods to client libraries
7. **Add integration test** that exercises the full dataset fetch path through FakeCascorClient
