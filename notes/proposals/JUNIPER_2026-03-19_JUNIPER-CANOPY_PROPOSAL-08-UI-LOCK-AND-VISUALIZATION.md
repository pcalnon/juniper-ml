# Proposal 8: UI Lock Contention and Visualization Pipeline Issues

**Severity**: CRITICAL (for user experience)
**Root Cause ID**: RC-P7

---

## Summary

The training lock is held for the entire duration of `add_hidden_unit()`, which executes ~20,200 gradient steps (32 candidates × 600 steps + 1000 retrain steps). This blocks ALL UI updates for 5-20 seconds during each cascade addition. The dashboard appears frozen, then suddenly jumps to new values.

## Mechanism

1. Training loop acquires `self._lock` at line 886
2. Calls `self.network.add_hidden_unit()` under the lock
3. Inside: 32 × 600 = 19,200 candidate training steps + 1000 retrain steps
4. All dashboard callbacks attempt to acquire the lock and block:
   - `get_decision_boundary()` → blocked
   - `get_current_state()` → blocked
   - `get_metrics_history()` → blocked
5. Fast-update-interval (1s) and slow-update-interval (5s) callbacks all fail
6. User sees frozen dashboard for entire lock duration

## Additional Visualization Issues

| Bug                                         | Severity     | Description                                    |
|---------------------------------------------|--------------|------------------------------------------------|
| Lock contention                             | CRITICAL     | 5-20 second UI freeze during cascade addition  |
| Sliding window (100 epochs)                 | MODERATE     | Default window shows mostly cooldown flat-line |
| History deque maxlen=1000                   | MODERATE     | Early history silently evicted in "full" mode  |
| Post-retrain metrics not in metrics_history | LOW          | Dashboard misses exact improvement moment      |
| Decision boundary polls only every 5s       | LOW-MODERATE | Boundary lags behind network state             |

## Proposed Fix

1. **Break the lock granularity**: Release lock during candidate training (candidate-local state only). Acquire briefly for installation, expansion, and each retrain batch.
2. **Emit progress during retrain**: Broadcast intermediate metrics during the 1000-step retrain so dashboard shows real-time convergence.
3. **Add cascade event markers**: Annotate loss chart with cascade addition events.
4. **Append post-retrain metrics to metrics_history**: Dashboard immediately reflects improvement.

## Risk Assessment

- **Medium effort**: Lock refactoring requires careful analysis of shared state
- **Medium risk**: Incorrect lock granularity could cause race conditions
- **High reward**: Eliminates the most jarring UX issue; dashboard shows smooth progress
