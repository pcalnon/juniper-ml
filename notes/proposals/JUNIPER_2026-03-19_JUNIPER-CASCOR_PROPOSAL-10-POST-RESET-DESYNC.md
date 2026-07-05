# Proposal 10: Post-Reset Parameter Desynchronization

**Severity**: LOW-MEDIUM
**Root Cause ID**: RC-P10

---

## Summary

After training reset, backend convergence parameters revert to defaults while the UI's `applied-params-store` retains stale user-applied values. The one-shot `init_params_from_backend` callback (max_intervals=1) doesn't re-fire after reset, so the UI shows old parameters but the backend runs with defaults.

## Mechanism

1. User applies custom convergence params (e.g., threshold=0.05, enabled=False)
2. `applied-params-store` stores these values
3. User clicks "Reset Training"
4. `_reset_state_and_history()` resets: `convergence_enabled=True`, `convergence_threshold=0.001`
5. UI still shows the user's old values (threshold=0.05, enabled=False)
6. Apply button shows no unsaved changes (UI matches stale applied-params-store)
7. Backend actually running with defaults — silent desynchronization

## Evidence

- `demo_mode.py` lines 1029-1032: Reset unconditionally restores defaults
- `dashboard_manager.py`: `params-init-interval` has `max_intervals=1` — fires once only
- No callback re-syncs UI from backend after reset

## Proposed Fix

1. After reset, trigger a re-sync of parameter UI from backend state
2. Either: fire the `params-init-interval` again, or add a dedicated reset-sync callback
3. Reset the `applied-params-store` to defaults so change detection works correctly

## Risk Assessment

- **Low effort**: Small callback change
- **Very low risk**: UI-only change
- **Low reward**: Edge case that only affects users who customize params then reset
