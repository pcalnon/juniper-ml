# Canopy Candidate Display — Residual Bug Analysis

- **Version**: 1.0.0
- **Date**: 2026-03-31
- **Status**: ANALYSIS COMPLETE — FIXES PENDING
- **Scope**: juniper-cascor (primary), juniper-canopy (secondary)
- **Prereqs**: CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md Phase 1–3 (all applied ✅)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Context — Prior Fix](#2-context--prior-fix)
3. [Current Symptoms](#3-current-symptoms)
4. [Root Cause Analysis](#4-root-cause-analysis)
5. [Issue Details](#5-issue-details)
6. [Fix Design — Approaches & Evaluation](#6-fix-design--approaches--evaluation)
7. [Recommended Approach per Issue](#7-recommended-approach-per-issue)
8. [Implementation Plan](#8-implementation-plan)
9. [Verification Plan](#9-verification-plan)
10. [Risk Assessment](#10-risk-assessment)
11. [Files Requiring Modification](#11-files-requiring-modification)

---

## 1. Executive Summary

### Problem Statement

After applying all phases from `CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` (WebSocket
state broadcasts, candidate_pool_status derivation, initial sync enhancement), the
juniper-canopy dashboard **still does not display** candidate training progress correctly.

Screenshots from a live training session (2026-03-31 15:59–16:00) confirm:

- Grow Iteration progress bar: **0%** (empty)
- Candidate Epoch progress bar: **0%** (empty)
- Top 2 Candidates table: **"No candidates"**
- Pool Training Metrics: **all 0.0000**
- Previous Pools: **"Best: (0.000)"** for all epochs
- Candidate Pool Phase: **"Idle"** (should show "Training" or "Selecting")

### Root Cause Summary

The prior fix resolved the "CasCor never broadcasts state" problem. Data IS now being
broadcast and received. However, **6 distinct residual bugs** prevent the data from
rendering correctly:

| # | Bug | Category | Severity |
|---|-----|----------|----------|
| 1 | `grow_max` set to `max_epochs` (10000), not `max_hidden_units` (10) | Semantic mismatch | **Critical** |
| 2 | Drain thread never starts (progress queue race condition) | Timing bug | **Critical** |
| 3 | Top candidate IDs never forwarded from CasCor to Canopy | Missing data | **High** |
| 4 | Pool training metrics never populated | Missing data | **Medium** |
| 5 | Previous pools show "Best: (0.000)" | Cascading from #3 | **Medium** |
| 6 | `candidate_pool_phase` never set in adapter | Missing derivation | **Low** |

---

## 2. Context — Prior Fix

The `CANDIDATE_TRAINING_DISPLAY_FIXES_PLAN.md` (v1.1.0) identified and fixed:

- **Phase 1**: Added `_broadcast_training_state()` to CasCor lifecycle manager with
  1-second throttling. Broadcasts at all 13 state transitions. ✅
- **Phase 2**: Derived `candidate_pool_status` from `phase_detail` in Canopy adapter. ✅
- **Phase 3**: Enhanced initial sync to populate `progress_fields` on reconnect. ✅

These fixes were correct and are still in place. The **broadcast infrastructure now works**.
The issues identified below are problems that exist *downstream* of the broadcast —
the data is broadcast but is either semantically wrong, never generated, or not derived.

---

## 3. Current Symptoms

### Screenshot Evidence (2026-03-31 15:59:51)

**Image 1 — Training Metrics tab:**
- Status bar: `Phase: Candidate Pool | Epoch: 14 | Hidden Units: 0/10`
- Metrics: `Current Epoch: 14 | Loss: 0.1702 | Accuracy: 72.90% | Hidden Units: 13/10`
- Progress detail text: `Adding Candidate | Iteration 12/10000 | Best Corr: 0.1611 | Candidates: 40/40`
- Grow Iteration bar: **empty (0%)**
- Candidate Epoch bar: **empty (0%)**

**Image 2 — Candidate Pool section (scrolled down):**
- Status: `Selecting Best` | Phase: `Idle` | Pool Size: 40
- Top 2 Candidates: **"No candidates"**
- Pool Training Metrics: all **0.0000**
- Previous Pools (epochs 9–13): all **"Best: (0.000)"**

### Key Observation from Progress Detail Text

The text `"Iteration 12/10000"` proves that `grow_iteration=12` and `grow_max=10000`
ARE reaching Canopy. The broadcast fix works. But 12/10000 yields 0.12% → `int(0.12)` = **0**.

---

## 4. Root Cause Analysis

### 4.1 Bug 1: Grow Progress Bar Shows 0% — Semantic Mismatch

**Root Cause**: CasCor's `grow_network()` passes `max_epochs` (the loop iteration limit)
as `max_iterations` to the grow iteration callback. This value (default 1000, actual 10000
in this session) represents the *theoretical maximum grow iterations*, not the user's
configured `max_hidden_units` target.

**Evidence chain:**

1. `cascade_correlation.py:3362` — `for epoch in range(max_epochs):`
2. `cascade_correlation.py:3388` — `max_iterations=max_epochs` passed to callback
3. `manager.py:311` — `grow_max=max_iterations` stored in TrainingState
4. `metrics_panel.py:1223` — `grow_pct = int(100 * grow_iter / grow_max)` = `int(100 * 12 / 10000)` = **0**

**Expected**: Progress should be relative to `max_hidden_units` (10), showing ~120% or capped at 100%.

### 4.2 Bug 2: Candidate Epoch Bar Always Empty — Drain Thread Race Condition

**Root Cause**: The progress queue drain thread checks `_persistent_progress_queue`
BEFORE `grow_network()` creates it. The queue is `None` at check time, so the drain
thread never starts. Candidate epoch data from workers is never consumed.

**Evidence chain:**

1. `cascade_correlation.py:687` — `self._persistent_progress_queue = None` (init)
2. `manager.py:356` — `_pq = getattr(network, "_persistent_progress_queue", None)` → **None**
3. `manager.py:357-364` — `if _pq is not None:` → False; drain thread NOT started
4. `manager.py:367` — `result = original_grow(...)` starts grow_network
5. `cascade_correlation.py:1832` → `_ensure_worker_pool()` called INSIDE grow_network
6. `cascade_correlation.py:2823` — Queue created **AFTER** drain thread check
7. `candidate_unit.py:724-732` — Workers emit progress into queue
8. Nobody reads the queue → `candidate_epoch` stays 0

**Consequence**: Since the drain thread never runs:
- `candidate_epoch` and `candidate_total_epochs` remain 0 in CasCor's TrainingState
- No `candidate_progress` WebSocket messages are broadcast
- Canopy's `candidate_epoch` stays at its default 0
- The candidate epoch progress bar and detail text never show data

### 4.3 Bug 3: Top 2 Candidates Never Populated — Missing Data in Callback

**Root Cause**: CasCor's grow iteration callback does NOT include per-candidate identity
information. The Canopy adapter does not set `top_candidate_id`, `top_candidate_score`,
`second_candidate_id`, or `second_candidate_score`.

**Evidence chain:**

1. `cascade_correlation.py:3386-3393` — callback receives: `iteration`, `max_iterations`,
   `best_correlation`, `candidates_trained`, `candidates_total`, `phase_detail`
   — **no candidate IDs**
2. `manager.py:308-317` — `_grow_iteration_callback` forwards same fields to state
   — **no top candidate fields**
3. `cascor_service_adapter.py:248-267` — state message handler forwards grow/candidate
   fields but **never sets** `top_candidate_id` / `top_candidate_score`
4. `training_monitor.py:281-284` — fields exist, initialized to "" / 0.0, never updated
5. `metrics_panel.py:1958` — `if top_cand_id:` → empty string → **"No candidates"**

**Available data**: `TrainingResults` dataclass (line 136-155) DOES contain
`best_candidate_id`, `best_candidate_uuid`, `correlations`, `candidate_ids`, and
`candidate_uuids` — all the data needed to populate top 2 candidates. It's simply
not forwarded through the callback.

### 4.4 Bug 4: Pool Training Metrics Always Zero — Data Doesn't Exist

**Root Cause**: CasCor's candidate training pipeline optimizes **correlation**, not
loss/accuracy/precision/recall/F1. These metrics do not exist for individual candidates
during candidate training. The `pool_metrics` dict in Canopy's TrainingState is never
populated because the source data doesn't exist.

**Evidence chain:**

1. `candidate_unit.py:617-732` — `train_detailed()` only tracks correlation
2. `cascade_correlation.py:136-155` — `TrainingResults` has `correlations` list, no loss/accuracy
3. `training_monitor.py:285` — `self.__pool_metrics: Dict[str, Any] = {}` — never updated
4. `metrics_panel.py:2057-2063` — reads `pool_metrics.get('avg_loss', 0.0)` → **0.0000**

### 4.5 Bug 5: Previous Pools Show "Best: (0.000)" — Cascading from Bug 3

**Root Cause**: Pool history snapshots capture `top_candidate_id` and `top_candidate_score`
from TrainingState. Since these are never populated (Bug 3), every snapshot records
empty/zero values.

**Evidence chain:**

1. `metrics_panel.py:678-682` — snapshot captures `top_candidate_id: ""`, `top_candidate_score: 0.0`
2. `metrics_panel.py:710-721` — renders `"Best: {top_id} ({top_score:.3f})"` → `"Best:  (0.000)"`

### 4.6 Bug 6: candidate_pool_phase Always "Idle" — Missing Derivation

**Root Cause**: The Canopy adapter derives `candidate_pool_status` from `phase_detail`
(per the prior fix) but does NOT derive `candidate_pool_phase`. Only `demo_mode.py`
sets this field.

**Evidence chain:**

1. `cascor_service_adapter.py:242-266` — derives `candidate_pool_status` but not
   `candidate_pool_phase`
2. `training_monitor.py:279` — `self.__candidate_pool_phase: str = "Idle"` — never changed
3. `metrics_panel.py:1948` — `pool_phase = state.get("candidate_pool_phase", "Idle")` → **"Idle"**
4. Screenshot shows `Phase: Idle` even while status shows `Selecting Best`

---

## 5. Issue Details

### 5.1 Issue Dependency Graph

```
Bug 2 (Drain thread race) ←── Blocks candidate_epoch data generation
    ↓
Bug 1 (grow_max semantic) ←── Independent, causes grow bar 0%
    ↓
Bug 3 (Top candidates missing) ←── Independent, causes empty table
    ↓
Bug 5 (Previous pools 0.000) ←── Cascading from Bug 3
    ↓
Bug 4 (Pool metrics zero) ←── Independent, requires new data path
    ↓
Bug 6 (Pool phase "Idle") ←── Independent, simple derivation gap
```

### 5.2 Fix Priority

| Priority | Bug | Rationale |
|----------|-----|-----------|
| P0 | Bug 2 | Blocks ALL candidate epoch data — nothing else can display without this |
| P0 | Bug 1 | Makes grow bar permanently 0% regardless of actual progress |
| P1 | Bug 3 | Top candidates table is a prominent, empty UI element |
| P1 | Bug 6 | Simple one-line fix, should be bundled with P0/P1 work |
| P2 | Bug 5 | Automatically fixed by Bug 3 fix |
| P2 | Bug 4 | Requires redefining pool metrics around correlation (larger scope) |

---

## 6. Fix Design — Approaches & Evaluation

### 6.1 Bug 1: grow_max Semantic Mismatch

#### Approach A: Use `max_hidden_units` from TrainingState in Canopy (Canopy-only)

In `_update_training_progress_handler`, replace `grow_max` with `max_hidden_units`:

```python
grow_max = state.get("max_hidden_units") or state.get("grow_max")
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | No CasCor changes; immediate fix; uses existing data |
| **Weaknesses** | `max_hidden_units` is the config target, not the iteration limit; could show >100% |
| **Risks** | Progress exceeding 100% if more units added than configured max |
| **Guardrails** | Cap percentage at 100%: `min(100, int(100 * grow_iter / grow_max))` |

#### Approach B: Pass `max_hidden_units` in CasCor callback alongside `max_epochs`

Modify `cascade_correlation.py:3386-3393` to pass `self.max_hidden_units`:

```python
_grow_cb(
    iteration=epoch,
    max_iterations=max_epochs,
    target_hidden_units=self.max_hidden_units,  # NEW
    ...
)
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Sends both values; Canopy can choose which to use |
| **Weaknesses** | Cross-repo change; callback signature change requires update in lifecycle manager |
| **Risks** | Must update all callback consumers |
| **Guardrails** | Use `**kwargs` or default parameter for backward compatibility |

#### Approach C: Change `max_iterations` to `max_hidden_units` in callback

Modify `cascade_correlation.py:3388` to `max_iterations=self.max_hidden_units`:

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Direct fix at the source |
| **Weaknesses** | `max_hidden_units` may not always be set; changes callback semantics |
| **Risks** | Could break other callback consumers that rely on the loop limit |
| **Guardrails** | Use `getattr(self, "max_hidden_units", max_epochs)` fallback |

### 6.2 Bug 2: Drain Thread Race Condition

#### Approach A: Deferred Queue Discovery in Drain Thread

Modify `_drain_progress_queue` to poll for the queue inside its loop:

```python
def _drain_progress_queue(network_ref, stop_event):
    import queue as _queue_mod
    _pq = None
    while not stop_event.is_set():
        if _pq is None:
            _pq = getattr(network_ref, "_persistent_progress_queue", None)
            if _pq is None:
                import time
                time.sleep(0.1)
                continue
        try:
            progress = _pq.get(timeout=0.25)
        except _queue_mod.Empty:
            continue
        # ... update state and broadcast
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Minimal change; drain thread always starts; discovers queue dynamically |
| **Weaknesses** | Polling for queue existence (0.1s intervals) |
| **Risks** | If queue is never created, thread polls until stop_event |
| **Guardrails** | `stop_event` already provides clean shutdown |

#### Approach B: Pre-create Progress Queue in `monitored_grow`

Create the queue before `original_grow()` runs:

```python
if manager_ref.network._persistent_progress_queue is None:
    manager_ref.network._persistent_progress_queue = manager_ref.network._mp_ctx.Queue(...)
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Queue guaranteed to exist when drain thread checks |
| **Weaknesses** | Reaches into network internals; may conflict with `_ensure_worker_pool` |
| **Risks** | Double-creating queue if `_ensure_worker_pool` also creates one |
| **Guardrails** | Only create if None; `_ensure_worker_pool` checks for existing pool |

#### Approach C: Always Start Drain Thread, Use Queue Reference From Network

Always start the drain thread, passing a reference to the network object. Thread reads
`network._persistent_progress_queue` directly on each iteration:

```python
_drain_thread = threading.Thread(
    target=_drain_progress_queue,
    args=(manager_ref.network, _drain_stop),
    daemon=True,
)
_drain_thread.start()  # Always start, regardless of queue state
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Clean separation; works for any queue creation timing |
| **Weaknesses** | Thread must handle None queue gracefully |
| **Risks** | Minimal — thread simply sleeps when no queue |
| **Guardrails** | `stop_event` + timeout ensure clean shutdown |

### 6.3 Bug 3: Top Candidates Not Forwarded

#### Approach A: Enhance grow_iteration_callback with Top Candidate Data

Modify `cascade_correlation.py` to pass top candidate info in callback:

```python
# In grow_network, after line 3393:
sorted_results = sorted(training_results.candidate_objects or [],
                        key=lambda c: abs(getattr(c, "correlation", 0.0) if c else 0.0),
                        reverse=True)
_grow_cb(
    ...,
    best_candidate_id=training_results.best_candidate_id,
    best_candidate_uuid=training_results.best_candidate_uuid,
    second_candidate_id=(training_results.candidate_ids[1] if len(training_results.candidate_ids) > 1 else None),
    second_candidate_score=(training_results.correlations[1] if len(training_results.correlations) > 1 else 0.0),
)
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Data already available in TrainingResults; direct forwarding |
| **Weaknesses** | Cross-repo change; callback signature grows |
| **Risks** | Must update lifecycle manager callback and adapter |
| **Guardrails** | Use `**kwargs` for backward compatibility |

#### Approach B: Separate WebSocket message type for pool details

Create a `pool_update` message type broadcast after each grow iteration.

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Clean separation of concerns; doesn't modify callback |
| **Weaknesses** | New message type; new handler in adapter; more complexity |
| **Risks** | Out-of-order messages if pool_update arrives before state update |
| **Guardrails** | Use same throttle as state broadcasts |

### 6.4 Bug 4: Pool Training Metrics

#### Approach A: Redefine Pool Metrics Using Correlation Statistics

Replace loss/accuracy/precision/recall/F1 with correlation-based metrics:

```python
pool_metrics = {
    "avg_correlation": mean(correlations),
    "max_correlation": max(correlations),
    "min_correlation": min(correlations),
    "std_correlation": std(correlations),
    "success_rate": success_count / total,
}
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Aligns with CasCor's actual training objective; data already available |
| **Weaknesses** | Different metric names than current UI expects; requires UI change |
| **Risks** | Breaking change to pool_metrics schema |
| **Guardrails** | Version the schema; update UI to display correlation metrics |

#### Approach B: Populate Existing Metrics Where Possible

Map `best_correlation` to `avg_loss` slot (as a proxy), leave others N/A.

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Minimal code change |
| **Weaknesses** | Semantically misleading; "Avg Loss" showing correlation is confusing |
| **Risks** | User confusion |
| **Guardrails** | Add tooltips explaining metric source |

#### Approach C: Hide Pool Metrics, Show Correlation Summary Instead

Replace the pool metrics table with a correlation summary panel:

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | Honest representation; no misleading metrics |
| **Weaknesses** | UI layout change |
| **Risks** | Low |
| **Guardrails** | Progressive enhancement — add more metrics as CasCor evolves |

### 6.5 Bug 6: candidate_pool_phase Not Derived

#### Single Approach: Derive from phase_detail

```python
# In cascor_service_adapter.py, alongside candidate_pool_status derivation:
if phase_detail in ("training_candidates", "candidate_training"):
    candidate_pool_phase = "Training"
elif phase_detail == "adding_candidate":
    candidate_pool_phase = "Selecting"
else:
    candidate_pool_phase = "Idle"
```

| Attribute | Assessment |
|-----------|-----------|
| **Strengths** | One-line fix; follows same pattern as status derivation |
| **Weaknesses** | None |
| **Risks** | None |
| **Guardrails** | None needed |

---

## 7. Recommended Approach per Issue

| Bug | Recommended | Rationale |
|-----|-------------|-----------|
| 1 | **Approach A** (Canopy-only, use `max_hidden_units`) | Fastest fix; no cross-repo dependency; cap at 100% handles edge case |
| 2 | **Approach C** (Always start drain thread, deferred discovery) | Most robust; clean separation; handles any creation timing |
| 3 | **Approach A** (Enhance callback with top candidate data) | Most direct; data already available in TrainingResults |
| 4 | **Approach C** (Hide current metrics, show correlation summary) | Honest; avoids misleading users with wrong metric types |
| 5 | *(Automatic)* | Fixed by Bug 3 fix |
| 6 | **Single approach** (Derive from phase_detail) | Trivial fix |

---

## 8. Implementation Plan

### Phase 1: Critical Fixes (P0) — Bugs 1 + 2

#### Step 1.1: Fix Drain Thread Race Condition (Bug 2)

**File**: `juniper-cascor/src/api/lifecycle/manager.py`
**Location**: Lines 339-367 (`monitored_grow` inner function)

**Current code** (problematic):

```python
def monitored_grow(*args, **kwargs):
    # ...
    _drain_stop = threading.Event()
    _drain_thread = None
    _pq = getattr(manager_ref.network, "_persistent_progress_queue", None)
    if _pq is not None:                    # ← BUG: Always None here!
        _drain_thread = threading.Thread(
            target=_drain_progress_queue,
            args=(_pq, _drain_stop),
            daemon=True,
            name="candidate-progress-drain",
        )
        _drain_thread.start()
    # ...
    result = original_grow(*args, **kwargs)  # ← Queue created INSIDE here
```

**Fixed code**:

```python
def monitored_grow(*args, **kwargs):
    # ...
    _drain_stop = threading.Event()
    # Always start drain thread — it discovers the queue dynamically
    _drain_thread = threading.Thread(
        target=_drain_progress_queue,
        args=(manager_ref.network, _drain_stop),  # Pass network ref, not queue
        daemon=True,
        name="candidate-progress-drain",
    )
    _drain_thread.start()
    # ...
    result = original_grow(*args, **kwargs)
```

**Also update `_drain_progress_queue`**:

```python
def _drain_progress_queue(network_ref, stop_event):
    """Background thread that reads candidate progress from workers."""
    import queue as _queue_mod
    _pq = None
    while not stop_event.is_set():
        # Deferred queue discovery — queue is created lazily inside grow_network
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
        state.update_state(
            phase_detail="training_candidates",
            candidate_epoch=progress.get("epoch", 0),
            candidate_total_epochs=progress.get("total_epochs", 0),
            best_correlation=progress.get("correlation", 0.0),
        )
        monitor.on_candidate_progress(progress)
        manager_ref._broadcast_training_state()
```

**Test changes needed**:
- `juniper-cascor/src/tests/unit/api/test_monitoring_hooks.py` — Update drain thread
  tests to verify deferred queue discovery
- `juniper-cascor/src/tests/unit/api/test_lifecycle_manager.py` — Verify drain thread
  starts even when progress queue is initially None

#### Step 1.2: Fix Grow Progress Bar Denominator (Bug 1)

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`
**Location**: Lines 1212-1228 (`_update_training_progress_handler`)

**Current code** (problematic):

```python
grow_iter = state.get("grow_iteration")
grow_max = state.get("grow_max")     # ← 10000 (max_epochs), not meaningful target
# ...
grow_pct = int(100 * grow_iter / grow_max) if has_grow else 0  # ← 0%!
```

**Fixed code**:

```python
grow_iter = state.get("grow_iteration")
# Use max_hidden_units as the meaningful progress target; fall back to grow_max
grow_max = state.get("max_hidden_units") or state.get("grow_max")
# ...
grow_pct = min(100, int(100 * grow_iter / grow_max)) if has_grow else 0
```

**Test changes needed**:
- `juniper-canopy/src/tests/unit/frontend/test_metrics_panel_handlers.py` — Add test
  case where `grow_max >> max_hidden_units`, verify bar uses `max_hidden_units`
- Add test case where `max_hidden_units` is 0 or None, verify fallback to `grow_max`

### Phase 2: High Priority Fixes (P1) — Bugs 3 + 6

#### Step 2.1: Add Top Candidate Data to Grow Callback (Bug 3)

**File**: `juniper-cascor/src/cascade_correlation/cascade_correlation.py`
**Location**: Lines 3382-3393 (grow iteration callback invocation)

**Current code**:

```python
_grow_cb(
    iteration=epoch,
    max_iterations=max_epochs,
    best_correlation=float(training_results.best_candidate.get_correlation()),
    candidates_trained=len(getattr(training_results, "candidate_objects", [])),
    candidates_total=pool_size,
    phase_detail="adding_candidate",
)
```

**Fixed code**:

```python
# Extract top 2 candidate info from sorted results
_candidate_ids = getattr(training_results, "candidate_ids", [])
_correlations = getattr(training_results, "correlations", [])
_candidate_uuids = getattr(training_results, "candidate_uuids", [])

_grow_cb(
    iteration=epoch,
    max_iterations=max_epochs,
    best_correlation=float(training_results.best_candidate.get_correlation()),
    candidates_trained=len(getattr(training_results, "candidate_objects", [])),
    candidates_total=pool_size,
    phase_detail="adding_candidate",
    # Top candidate data (NEW)
    best_candidate_id=getattr(training_results, "best_candidate_id", -1),
    best_candidate_uuid=getattr(training_results, "best_candidate_uuid", ""),
    second_candidate_id=_candidate_ids[1] if len(_candidate_ids) > 1 else None,
    second_candidate_correlation=float(_correlations[1]) if len(_correlations) > 1 else 0.0,
    all_correlations=_correlations,
)
```

#### Step 2.2: Forward Top Candidate Data in Lifecycle Manager

**File**: `juniper-cascor/src/api/lifecycle/manager.py`
**Location**: Lines 308-317 (`_grow_iteration_callback`)

**Fixed code**:

```python
def _grow_iteration_callback(iteration, max_iterations, best_correlation,
                              candidates_trained, candidates_total, phase_detail,
                              **kwargs):  # Accept additional kwargs
    state.update_state(
        grow_iteration=iteration,
        grow_max=max_iterations,
        best_correlation=best_correlation,
        candidates_trained=candidates_trained,
        candidates_total=candidates_total,
        phase_detail=phase_detail,
    )
    # Store top candidate info for WebSocket broadcast
    # (These fields are in the state message, picked up by canopy adapter)
    top_candidate_data = {
        "best_candidate_id": kwargs.get("best_candidate_id"),
        "best_candidate_uuid": kwargs.get("best_candidate_uuid"),
        "second_candidate_id": kwargs.get("second_candidate_id"),
        "second_candidate_correlation": kwargs.get("second_candidate_correlation", 0.0),
        "all_correlations": kwargs.get("all_correlations", []),
    }
    manager_ref._broadcast_training_state(extra_data=top_candidate_data)
```

Alternatively, add top candidate fields to CasCor's `TrainingState` and include them
in the standard state broadcast (simpler, consistent).

#### Step 2.3: Map Top Candidate Data in Canopy Adapter

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`
**Location**: Lines 248-267 (state message handler)

**Add** to the `_state_update_callback` call:

```python
top_candidate_id=str(data.get("best_candidate_id", "")),
top_candidate_score=data.get("best_correlation", 0.0),
second_candidate_id=str(data.get("second_candidate_id", "")),
second_candidate_score=data.get("second_candidate_correlation", 0.0),
```

#### Step 2.4: Derive candidate_pool_phase (Bug 6)

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`
**Location**: Lines 242-247 (alongside candidate_pool_status derivation)

**Add**:

```python
if phase_detail in ("training_candidates", "candidate_training"):
    candidate_pool_status = "Training"
    candidate_pool_phase = "Training"    # NEW
elif phase_detail == "adding_candidate":
    candidate_pool_status = "Selecting Best"
    candidate_pool_phase = "Selecting"   # NEW
else:
    candidate_pool_status = "Inactive"
    candidate_pool_phase = "Idle"        # NEW (explicit)

self._state_update_callback(
    ...,
    candidate_pool_phase=candidate_pool_phase,  # NEW
)
```

### Phase 3: Medium Priority (P2) — Bug 4

#### Step 3.1: Redefine Pool Metrics Around Correlation

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`
**Location**: Lines 2056-2084 (pool metrics table)

**Replace** the loss/accuracy/precision/recall/F1 table with correlation statistics:

```python
# Compute from all_correlations if available, otherwise from best_correlation
all_corrs = state.get("all_correlations", [])
if all_corrs:
    import statistics
    pool_metrics_rows = [
        ("Avg Correlation", f"{statistics.mean(all_corrs):.4f}"),
        ("Max Correlation", f"{max(all_corrs):.4f}"),
        ("Min Correlation", f"{min(all_corrs):.4f}"),
        ("Std Deviation", f"{statistics.stdev(all_corrs) if len(all_corrs) > 1 else 0.0:.4f}"),
        ("Success Rate", f"{sum(1 for c in all_corrs if c > 0) / len(all_corrs):.1%}"),
    ]
else:
    best_corr = state.get("best_correlation", 0.0)
    pool_metrics_rows = [
        ("Best Correlation", f"{best_corr:.4f}"),
        ("Pool Size", str(state.get("candidate_pool_size", 0))),
    ]
```

**Also**: Forward `all_correlations` through the data pipeline:
- CasCor → grow callback → lifecycle manager → WebSocket state message
- Canopy adapter → TrainingState (add `all_correlations` field)
- `/api/state` → frontend

#### Step 3.2: Update Previous Pool History Rendering

**File**: `juniper-canopy/src/frontend/components/metrics_panel.py`
**Location**: Lines 673-693 (history snapshot) and 701-772 (render)

Update snapshot to capture `best_correlation` (which IS populated) in addition to
`top_candidate_score`:

```python
pool_snapshot = {
    # ...existing fields...
    "best_correlation": state.get("best_correlation", 0.0),  # NEW fallback
}
```

Update header rendering to prefer `best_correlation`:

```python
top_score = pool.get("top_candidate_score") or pool.get("best_correlation", 0.0)
```

---

## 9. Verification Plan

### 9.1 Unit Tests

```bash
# CasCor — verify drain thread fix and callback changes
cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src
conda run -n JuniperCascor pytest tests/unit/api/test_lifecycle_manager.py \
    tests/unit/api/test_lifecycle_manager_coverage.py -q --timeout=30

# Canopy — verify progress bar and candidate pool display fixes
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda run -n JuniperPython pytest tests/unit/ -q --timeout=30
```

### 9.2 Specific Test Cases Required

| Bug | Test Description | Expected Result |
|-----|-----------------|-----------------|
| 1 | Progress handler with `grow_max=10000, max_hidden_units=10, grow_iteration=5` | `grow_pct=50`, label `"5/10"` |
| 1 | Progress handler with `max_hidden_units=0` (fallback) | Falls back to `grow_max` |
| 1 | Progress handler with `grow_iteration > max_hidden_units` | Capped at 100% |
| 2 | Drain thread starts when `_persistent_progress_queue` is initially None | Thread starts, discovers queue when created |
| 2 | Drain thread exits cleanly when stop_event is set before queue exists | No errors, clean shutdown |
| 3 | State message with `best_candidate_id` populates Top 2 table | Candidate rows appear |
| 6 | State message with `phase_detail="training_candidates"` | `candidate_pool_phase="Training"` |

### 9.3 Integration Validation

```bash
# Launch services
${HOME}/Development/python/Juniper/juniper-ml/util/launch_full_monty.bash

# Verify via REST API during candidate training phase:
curl -s http://localhost:8050/api/state | python3 -c "
import json, sys
s = json.load(sys.stdin)
print(f'grow_iteration: {s.get(\"grow_iteration\")}')
print(f'grow_max: {s.get(\"grow_max\")}')
print(f'max_hidden_units: {s.get(\"max_hidden_units\")}')
print(f'candidate_epoch: {s.get(\"candidate_epoch\")}')
print(f'candidate_total_epochs: {s.get(\"candidate_total_epochs\")}')
print(f'top_candidate_id: {s.get(\"top_candidate_id\")}')
print(f'candidate_pool_phase: {s.get(\"candidate_pool_phase\")}')
"
```

### 9.4 Visual Verification Checklist

- [ ] Grow Iteration bar shows meaningful progress (e.g., "5/10" at 50%)
- [ ] Grow Iteration bar caps at 100% when hidden units exceed target
- [ ] Candidate Epoch bar shows progress during candidate training phase
- [ ] Candidate Epoch bar resets between grow iterations
- [ ] Top 2 Candidates table shows ranked candidates with IDs and scores
- [ ] Pool Training Metrics shows correlation-based statistics
- [ ] candidate_pool_phase shows "Training" during candidate training
- [ ] candidate_pool_phase shows "Selecting" during candidate selection
- [ ] Previous Pools show "Best: {id} ({score:.3f})" with real data
- [ ] All fields reset when training stops

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Drain thread polling wastes CPU while waiting for queue | Low | Low | 0.1s sleep interval; stop_event provides immediate exit |
| `all_correlations` list grows large in WebSocket message | Low | Medium | Limit to top N (e.g., 50) or send summary statistics only |
| Callback `**kwargs` breaks existing tests | Medium | Low | Add `**kwargs` acceptance; update test mocks |
| `max_hidden_units` not in state when grow bar renders | Low | Medium | Fallback chain: `max_hidden_units` → `grow_max` → hide bar |
| Pool metrics schema change breaks history snapshots | Low | Low | History is ephemeral (in-memory Store); no persistence to migrate |
| Drain thread references stale progress queue after pool restart | Low | Medium | Re-discover queue each time `_pq` becomes None |

---

## 11. Files Requiring Modification

### Phase 1: Critical (P0)

| File | Changes | Bug |
|------|---------|-----|
| `juniper-cascor/src/api/lifecycle/manager.py` | Modify `_drain_progress_queue` for deferred queue discovery; always start drain thread in `monitored_grow` | Bug 2 |
| `juniper-canopy/src/frontend/components/metrics_panel.py` | Use `max_hidden_units` for grow bar denominator; cap at 100% | Bug 1 |

### Phase 2: High (P1)

| File | Changes | Bug |
|------|---------|-----|
| `juniper-cascor/src/cascade_correlation/cascade_correlation.py` | Add top candidate data to grow callback invocation | Bug 3 |
| `juniper-cascor/src/api/lifecycle/manager.py` | Forward top candidate data in `_grow_iteration_callback`; add `**kwargs` | Bug 3 |
| `juniper-canopy/src/backend/cascor_service_adapter.py` | Map top candidate fields from state message; derive `candidate_pool_phase` | Bugs 3, 6 |

### Phase 3: Medium (P2)

| File | Changes | Bug |
|------|---------|-----|
| `juniper-canopy/src/frontend/components/metrics_panel.py` | Redefine pool metrics as correlation statistics; update history rendering | Bugs 4, 5 |
| `juniper-canopy/src/backend/training_monitor.py` | Add `all_correlations` field to TrainingState | Bug 4 |

### Test Files Requiring Updates

| File | Changes |
|------|---------|
| `juniper-cascor/src/tests/unit/api/test_monitoring_hooks.py` | Update drain thread tests for deferred discovery |
| `juniper-cascor/src/tests/unit/api/test_lifecycle_manager.py` | Verify drain thread starts with None queue |
| `juniper-cascor/src/tests/unit/test_cascade_correlation_callback_hooks.py` | Update callback invocation tests for new kwargs |
| `juniper-canopy/src/tests/unit/frontend/test_metrics_panel_handlers.py` | Test grow bar with `max_hidden_units` denominator |
| `juniper-canopy/src/tests/unit/backend/test_cascor_service_adapter_boundary.py` | Test `candidate_pool_phase` derivation |
