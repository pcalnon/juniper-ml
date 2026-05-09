# Canopy Test Failure Analysis — External CasCor Integration

**Date**: 2026-03-22
**Related Prompt**: prompts/prompt049_2026-03-22.md
**Feature**: External CasCor auto-discovery and service mode controls (PR #39)
**Test Suite**: juniper-canopy (`3755 passed, 13 failed, 19 skipped`)

---

## Summary

After merging the external cascor connectivity feature (commit `dcff60c`) and a follow-up fix (commit `5d9fd0e`), 13 tests were reported failing. Root cause analysis reveals **3 distinct failure categories** with well-understood causes and straightforward fixes.

| Category | Tests | Root Cause | Status |
|----------|-------|------------|--------|
| Asyncio event loop (Python 3.14) | 8 | Deprecated `asyncio.get_event_loop()` in sync test methods | **Needs fix** |
| Mock/delegation mismatch | 4 | Stale test expectations after implementation change | **Fixed by `5d9fd0e`** |
| Behavior evolution | 1 | Test asserts old error behavior; implementation now graceful | **Needs fix** |

**Remaining failures**: 9 (8 asyncio + 1 behavior mismatch)

---

## Category 1: Asyncio Event Loop Errors (8 tests)

### Affected File

`src/tests/unit/test_cascor_discovery.py`

### Failing Tests

1. `TestProbeCascorUrl::test_probe_returns_true_on_healthy_response`
2. `TestProbeCascorUrl::test_probe_returns_false_on_connection_error`
3. `TestProbeCascorUrl::test_probe_returns_false_on_wrong_status`
4. `TestProbeCascorUrl::test_probe_returns_false_on_wrong_body`
5. `TestDiscoverCascor::test_returns_url_when_cascor_found`
6. `TestDiscoverCascor::test_returns_none_when_no_cascor`
7. `TestDiscoverCascor::test_returns_first_responding_port`
8. `TestDiscoverCascor::test_empty_ports_returns_none`

### Error

```
RuntimeError: There is no current event loop in thread 'MainThread'.
```

### Root Cause

All 8 tests use the deprecated pattern:

```python
def test_something(self):
    result = asyncio.get_event_loop().run_until_complete(some_async_func())
```

Python 3.14 removed the implicit event loop in the main thread. `asyncio.get_event_loop()` raises `RuntimeError` when no loop is running, which was deprecated since Python 3.10 and enforced in 3.14.

The project has `asyncio_mode = "auto"` in `pyproject.toml` and a session-scoped `event_loop` fixture in `conftest.py`, so pytest-asyncio is properly configured. These tests simply weren't written as async.

### Fix

Convert all 8 test methods from synchronous + `run_until_complete()` to native `async def` tests. With `asyncio_mode = "auto"`, pytest-asyncio will automatically handle them.

**Before:**
```python
def test_probe_returns_true_on_healthy_response(self):
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = asyncio.get_event_loop().run_until_complete(
            probe_cascor_url("http://localhost:8200")
        )
    assert result is True
```

**After:**
```python
async def test_probe_returns_true_on_healthy_response(self):
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = await probe_cascor_url("http://localhost:8200")
    assert result is True
```

### Additional Fix Required

The `probe_cascor_url()` function itself (in `src/discovery.py:35`) also uses the deprecated `asyncio.get_event_loop()`:

```python
async def probe_cascor_url(url: str, timeout: float = _DEFAULT_TIMEOUT) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _probe_url_sync, url, timeout)
```

This must be updated to use `asyncio.get_running_loop()` (available since Python 3.7, correct for use inside an already-running coroutine):

```python
async def probe_cascor_url(url: str, timeout: float = _DEFAULT_TIMEOUT) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _probe_url_sync, url, timeout)
```

---

## Category 2: Mock/Delegation Mismatch (4 tests) — ALREADY FIXED

### Affected File

`src/tests/unit/test_service_backend.py`

### Original Failing Tests

1. `TestTrainingControl::test_pause_training_not_supported`
2. `TestTrainingControl::test_resume_training_not_supported`
3. `TestTrainingControl::test_reset_training_not_supported`
4. `TestParameters::test_apply_params_not_supported`

### Root Cause

These tests were written when `ServiceBackend` did not support pause/resume/reset/apply_params (returning `{"ok": False, ...}`). After the external cascor feature was implemented, these operations now delegate to `CascorServiceAdapter`, which forwards them to the cascor REST API.

The tests:
- Used the wrong names (`*_not_supported` instead of `*_delegates_to_adapter`)
- Did not configure mock return values for the new delegation methods
- Asserted `result["ok"] is False` when the operations now succeed

### Fix (Already Applied)

Commit `5d9fd0e` ("fix: update ServiceBackend unit tests to match adapter delegation pattern") renamed the tests and updated assertions:

- `test_pause_training_not_supported` → `test_pause_training_delegates_to_adapter`
- `test_resume_training_not_supported` → `test_resume_training_delegates_to_adapter`
- `test_reset_training_not_supported` → `test_reset_training_delegates_to_adapter`
- `test_apply_params_not_supported` → `test_apply_params_delegates_to_adapter`

Each now configures `mock_adapter.<method>.return_value = {"ok": True, "data": {...}}` and asserts `result["ok"] is True`.

**No further action needed.**

---

## Category 3: Behavior Evolution (1 test)

### Affected File

`src/tests/integration/test_fake_service_backend.py`

### Failing Test

`test_apply_params_not_supported` (line 225-228)

### Error

```
AssertionError: assert True is False
  where True = {'ok': True, 'data': {}, 'message': 'No cascor-mappable params provided'}.get('ok')
```

### Root Cause

The test passes `learning_rate=0.001` to `backend.apply_params()`, expecting it to fail (`ok=False`). However, `learning_rate` is not a key in the adapter's `_CANOPY_TO_CASCOR_PARAM_MAP` — the mapped key is `nn_learning_rate`. When no params map to cascor API names, the adapter now returns:

```python
{"ok": True, "data": {}, "message": "No cascor-mappable params provided"}
```

This is intentional graceful handling: passing canopy-only parameters (like `nn_spiral_rotations` or bare `learning_rate`) is not an error — those params simply have no cascor equivalent.

The test name (`test_apply_params_not_supported`) is also stale — `apply_params` IS supported in service mode; it delegates to the adapter.

### Fix

Update the test to reflect the actual behavior:

1. Rename from `test_apply_params_not_supported` to `test_apply_params_unmapped_keys_succeeds_gracefully`
2. Change assertion from `result.get("ok") is False` to `result.get("ok") is True`
3. Assert the message indicates no params were mapped
4. Add a companion test that verifies mapped params (e.g., `nn_learning_rate`) are forwarded correctly

---

## Implementation Plan

### Phase 1: Fix test_cascor_discovery.py (8 tests)

1. Update `src/discovery.py:35` — change `asyncio.get_event_loop()` to `asyncio.get_running_loop()`
2. Convert all 8 test methods in `test_cascor_discovery.py` from sync+`run_until_complete` to `async def` + `await`
3. Remove unused `import asyncio` from test file (no longer needed for `get_event_loop`)

### Phase 2: Fix test_fake_service_backend.py (1 test)

1. Rename `test_apply_params_not_supported` to `test_apply_params_unmapped_keys_succeeds_gracefully`
2. Update assertion to match new behavior (`ok=True`, check message)
3. Add `test_apply_params_mapped_keys_forwarded` to verify round-trip for `nn_learning_rate`

### Phase 3: Verify (no regressions)

1. Run full canopy test suite
2. Confirm all 13 previously failing tests now pass
3. Confirm no regressions in the 3755 previously passing tests

---

## Conclusion

The external cascor connectivity feature is architecturally complete across all three codebases (juniper-cascor, juniper-cascor-client, juniper-canopy). All 12 sub-requirements from prompt047 have working implementations. The 13 test failures are purely test-layer issues — no production code bugs were identified. After fix commit `5d9fd0e` addressed 4 of the 13 failures, the remaining 9 failures require:

- A one-line fix in `discovery.py` (deprecated API)
- Converting 8 sync test methods to async (standard pytest-asyncio pattern)
- Updating 1 integration test assertion to match intentional behavior change
- Adding 1 new integration test for mapped parameter forwarding

Total estimated changes: ~80 lines across 3 files.
