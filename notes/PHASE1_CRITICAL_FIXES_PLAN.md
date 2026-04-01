# Phase 1: Critical Fixes (P0) — Bugs 1 + 2

- **Version**: 1.0.0
- **Date**: 2026-03-31
- **Status**: PLAN — PENDING IMPLEMENTATION
- **Scope**: juniper-cascor (Bug 2), juniper-canopy (Bug 1)
- **Prereqs**: CANOPY_CANDIDATE_DISPLAY_RESIDUAL_BUGS.md analysis complete

---

## Context

After `CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` was fully applied, the juniper-canopy
dashboard still shows empty progress bars during CasCor training. Two critical bugs
prevent data from rendering even though WebSocket broadcasts are now working:

1. **Grow bar 0%**: `grow_max` = `max_epochs` (10000) makes `int(100*12/10000)` = 0
2. **Candidate epoch bar empty**: Drain thread never starts because the progress queue
   doesn't exist yet when checked

---

## Changes

### 1. Fix drain thread race condition (Bug 2)

**File**: `juniper-cascor/src/api/lifecycle/manager.py` (lines 318-363)

**Problem**: `_pq = getattr(network, "_persistent_progress_queue", None)` at line 355
returns None because the queue is created lazily inside `grow_network()` →
`_execute_parallel_training()` → `_ensure_worker_pool()` (cascade_correlation.py:2823),
which runs AFTER the check.

**Fix**: Modify `_drain_progress_queue` to accept a network reference instead of a queue,
and poll for the queue inside its loop. Always start the drain thread unconditionally.

```python
# _drain_progress_queue signature changes from:
def _drain_progress_queue(progress_queue, stop_event):
# to:
def _drain_progress_queue(network_ref, stop_event):
```

Inside the loop, discover the queue dynamically:

```python
_pq = None
while not stop_event.is_set():
    if _pq is None:
        _pq = getattr(network_ref, "_persistent_progress_queue", None)
        if _pq is None:
            try:
                stop_event.wait(timeout=0.1)
            except Exception:
                break
            continue
    try:
        progress = _pq.get(timeout=0.25)
    except _queue_mod.Empty:
        continue
    except Exception:
        break
    # ... existing state update + broadcast logic unchanged
```

In `monitored_grow`, remove the conditional and always start the thread:

```python
# Remove: _pq = getattr(...) / if _pq is not None:
_drain_stop = threading.Event()
_drain_thread = threading.Thread(
    target=_drain_progress_queue,
    args=(manager_ref.network, _drain_stop),
    daemon=True,
    name="candidate-progress-drain",
)
_drain_thread.start()
```

Update the finally block to always join (remove `if _drain_thread is not None` guard).

### 2. Fix grow progress bar denominator (Bug 1)

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py` (lines 1212-1228)

**Problem**: `grow_max` from CasCor is `max_epochs` (10000), but the meaningful target
is `max_hidden_units` (10). `max_hidden_units` is already available in the canopy
training state (forwarded by the adapter at line 254).

**Fix**: Use `max_hidden_units` as denominator, fall back to `grow_max`, cap at 100%.

```python
grow_iter = state.get("grow_iteration")
# Use max_hidden_units as meaningful target; fall back to grow_max
grow_max = state.get("max_hidden_units") or state.get("grow_max")
cand_epoch = state.get("candidate_epoch")
cand_total = state.get("candidate_total_epochs")

has_grow = grow_iter is not None and grow_max
has_cand = cand_epoch is not None and cand_total

if not has_grow and not has_cand:
    return hidden_style, 0, "", 0, ""

grow_pct = min(100, int(100 * grow_iter / grow_max)) if has_grow else 0
grow_label = f"{grow_iter}/{grow_max}" if has_grow else ""
cand_pct = min(100, int(100 * cand_epoch / cand_total)) if has_cand else 0
cand_label = f"{cand_epoch}/{cand_total}" if has_cand else ""
```

### 3. Update tests

**File**: `juniper-cascor/src/tests/unit/api/test_monitoring_hooks.py`

Update `test_monitored_grow_drains_progress_queue_and_resets_candidate_progress` (line 298):

- Remove line 328 (`manager.network._persistent_progress_queue = Queue()`) — this pre-set
  the queue, masking the real-world timing
- Modify `fake_grow` to create the queue itself (simulating real `_ensure_worker_pool`
  behavior), then put progress data into it
- Assert drain thread discovers the queue and reads progress

Add new test: `test_drain_thread_starts_without_progress_queue`:

- Verify drain thread starts and exits cleanly when stop_event is set before any
  queue is created (no-queue scenario)

**File**: `juniper-canopy/src/tests/unit/frontend/test_metrics_panel_handlers.py`

Update existing test `test_grow_iteration_progress` (line 1717):

- Change to include `max_hidden_units` in state, verify it's used as denominator

Add new tests:

- `test_grow_uses_max_hidden_units_over_grow_max`: State with `grow_max=10000`,
  `max_hidden_units=10`, `grow_iteration=5` → `grow_pct=50`, label `"5/10"`
- `test_grow_falls_back_to_grow_max`: State without `max_hidden_units`, only
  `grow_max=10` → still works
- `test_grow_caps_at_100_percent`: State with `grow_iteration=15`,
  `max_hidden_units=10` → `grow_pct=100` (not 150)
- `test_candidate_epoch_caps_at_100`: Analogous for candidate bar

---

## Verification

```bash
# CasCor tests
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src && \
  conda run -n JuniperCascor pytest tests/unit/api/test_monitoring_hooks.py -q --timeout=30

# Canopy tests
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src && \
  conda run -n JuniperPython pytest tests/unit/frontend/test_metrics_panel_handlers.py -q --timeout=30
```

---

## Files Modified

| File | Repo | Change |
|------|------|--------|
| `src/api/lifecycle/manager.py` | juniper-cascor | Drain thread deferred queue discovery |
| `src/tests/unit/api/test_monitoring_hooks.py` | juniper-cascor | Update drain thread test |
| `src/frontend/components/metrics_panel.py` | juniper-canopy | Grow bar denominator fix |
| `src/tests/unit/frontend/test_metrics_panel_handlers.py` | juniper-canopy | New/updated progress bar tests |
