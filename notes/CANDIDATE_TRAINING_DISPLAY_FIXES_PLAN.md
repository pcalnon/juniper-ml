# Candidate Training Display Fixes Plan

- **Version**: 1.0.0
- **Date**: 2026-03-31
- **Status**: VALIDATED — READY FOR IMPLEMENTATION
- **Scope**: juniper-cascor (primary), juniper-canopy (secondary)
- **Prereqs**: INTEGRATED_DASHBOARD_PLAN.md Phase 1–3 items (merged ✅)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Audit Results](#2-audit-results)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Approaches & Evaluation](#4-approaches--evaluation)
5. [Recommended Approach](#5-recommended-approach)
6. [Implementation Plan](#6-implementation-plan)
7. [Verification Plan](#7-verification-plan)
8. [Risk Assessment](#8-risk-assessment)
9. [Files Requiring Modification](#9-files-requiring-modification)

---

## 1. Executive Summary

### Problem Statement

The juniper-canopy dashboard has **fully implemented** UI components for displaying
candidate training progress, including:

- `dbc.Progress` bars for grow iteration and candidate epoch
- Per-epoch candidate training status (phase detail, best correlation, candidates trained/total)
- Candidate pool state display with historical snapshots
- Phase badge with duration timer
- Learning rate card

However, **none of these components display real data when connected to a live
juniper-cascor instance**. All progress fields remain at their default zero/empty values.

### Root Cause (Single Sentence)

**CasCor updates its internal `TrainingState` with all progress fields but never broadcasts
them via WebSocket**, so Canopy's WebSocket relay never receives the data, never updates its
own `TrainingState`, and the `/api/state` endpoint always returns zeros for progress fields.

### Impact Summary

| Component | Expected Display | Actual Display |
|-----------|-----------------|----------------|
| Grow iteration progress bar | "3/10" with progress fill | Hidden (0/0) |
| Candidate epoch progress bar | "45/100 (45%)" | Hidden (0/0) |
| Phase detail text | "training_candidates" | "" |
| Best correlation | "0.9234" | Not shown |
| Candidates trained/total | "2/8" | Not shown |
| Phase duration | "2m 45s" | Not shown |
| Candidate pool display | Rich table with top-2 candidates | "Inactive" |

---

## 2. Audit Results

### 2.1 Canopy Frontend (metrics_panel.py) — FULLY IMPLEMENTED ✅

All UI components exist and callbacks are correctly wired:

| Component | Implementation | Callback |
|-----------|---------------|----------|
| `dbc.Progress` grow bar | Lines 452–488 | `update_training_progress` (line 628) |
| `dbc.Progress` candidate bar | Lines 452–488 | Same callback |
| Progress detail text | Lines 148, 607–612 | `_update_progress_detail_handler` (line 1157) |
| Candidate pool display | Lines 502–532, 597–605 | `_update_candidate_pool_handler` (line 1938) |
| Phase badge | Lines 136–147 | `_get_status_style` (line 1880) |
| Phase duration | Lines 158–167, 621–626 | `_update_phase_duration_handler` (line 1231) |
| Learning rate card | Lines 614–619 | Separate callback |

All callbacks read from `training-state-store`, which is populated by polling `GET /api/state`
every 5 seconds.

### 2.2 Canopy Backend (/api/state) — PASSES THROUGH CORRECTLY ✅

The `/api/state` endpoint (main.py ~line 600) returns `training_state.get_state()` which
includes all 28 `_STATE_FIELDS`. The data pipeline is:

```
TrainingState.get_state() → /api/state → training-state-store → callbacks
```

This pipeline is correct. The problem is upstream.

### 2.3 Canopy Service Adapter — RELAY WORKS FOR MESSAGES RECEIVED ✅

The WebSocket relay (cascor_service_adapter.py) correctly handles:

- `"state"` messages → updates TrainingState with all fields present
- `"candidate_progress"` messages → updates candidate_epoch, candidate_total_epochs, best_correlation

The relay correctly forwards whatever it receives.

### 2.4 CasCor TrainingState Fields — ALL POPULATED INTERNALLY ✅

The CasCor `TrainingState` (monitor.py) has all 20 progress fields:

- `_grow_iteration_callback` sets: grow_iteration, grow_max, best_correlation,
  candidates_trained, candidates_total, phase_detail
- `_drain_progress_queue` sets: candidate_epoch, candidate_total_epochs, best_correlation
- `_output_training_callback` sets: phase_detail, phase_started_at

### 2.5 CasCor WebSocket Broadcasts — ❌ THE GAP

| Data | Stored in TrainingState? | Broadcast via WebSocket? |
|------|------------------------|------------------------|
| status/phase | ✅ | ⚠️ Only at training start, hardcoded `{"status": "Started", "phase": "Output"}` |
| grow_iteration, grow_max | ✅ | ❌ **NEVER BROADCAST** |
| candidates_trained/total | ✅ | ❌ **NEVER BROADCAST** |
| phase_detail | ✅ | ❌ **NEVER BROADCAST** |
| phase_started_at | ✅ | ❌ **NEVER BROADCAST** |
| candidate_epoch/total | ✅ | ✅ Via `candidate_progress` messages |
| best_correlation | ✅ | ✅ Via `candidate_progress` messages |

**Key insight**: `candidate_epoch` and `best_correlation` DO flow through (via
`candidate_progress` messages) but ALL grow-level and phase-level fields are
**only stored locally, never broadcast**.

### 2.6 CasCor-Client — NO GAP

The client has `get_training_status()` which returns the full training status composite
including all `TrainingState` fields. It also has `CascorTrainingStream` for WebSocket.
The client itself is not the bottleneck.

### 2.7 Candidate Pool Status — CANOPY-ONLY CONCEPT

The `candidate_pool_status` field displayed in the candidate pool section is a Canopy-only
concept. CasCor has no `candidate_pool_status` field. This needs to be derived in the
adapter from phase/phase_detail transitions.

---

## 3. Root Cause Analysis

### 3.1 Primary Root Cause: Missing WebSocket State Broadcasts in CasCor

**Location**: `juniper-cascor/src/api/lifecycle/manager.py`

The `_grow_iteration_callback` (line ~285) and related callbacks update the local
`TrainingState` object via `state.update_state()` but **never call
`ws.broadcast_from_thread(create_state_message(...))`.** The only `create_state_message()`
call in the entire CasCor codebase is the hardcoded training-start message at line ~110:

```python
create_state_message({"status": "Started", "phase": "Output"})
```

This means:
1. Grow iteration progress → stored locally, never broadcast
2. Phase transitions (output→candidate→adding_candidate) → stored locally, never broadcast
3. Phase detail/started_at → stored locally, never broadcast
4. Candidates trained/total → stored locally, never broadcast

### 3.2 Secondary Root Cause: No REST Polling Fallback for State

Even without WebSocket, Canopy could periodically poll CasCor's REST API for the full
training state. The CasCor `GET /v1/training/status` endpoint DOES return the full
`TrainingState` (including all progress fields) in its response. However, Canopy only
polls this at initial sync time (via `CascorStateSync.sync()`) and never again — it
relies entirely on WebSocket for ongoing updates.

### 3.3 Tertiary Root Cause: Candidate Pool Status Not Derived

CasCor has no `candidate_pool_status` field. Canopy expects this for the pool display.
Even if all progress fields were broadcast, the pool display would show "Inactive"
unless the adapter derives this from phase_detail.

### 3.4 Root Cause Dependency

```
Primary: CasCor callbacks don't broadcast TrainingState via WebSocket
    └── Secondary: No REST polling fallback in Canopy
         └── Tertiary: candidate_pool_status not derived
```

---

## 4. Approaches & Evaluation

### Approach A: Add WebSocket State Broadcasts to CasCor

**Description**: Modify CasCor's `_grow_iteration_callback`, `_output_training_callback`,
and phase transition code to broadcast the full `TrainingState` via WebSocket after each
update.

**Strengths**:
- Fixes the root cause directly
- Low latency — progress updates arrive immediately
- Canopy relay already handles `state` messages with all fields
- Consistent with the existing `candidate_progress` broadcast pattern
- No polling overhead

**Weaknesses**:
- Cross-repo change (requires CasCor modification)
- High-frequency broadcasts during candidate training (each grow iteration callback)
- Could flood WebSocket during fast training

**Risks**:
- Broadcast frequency may need throttling for very fast training scenarios
- Must ensure `create_state_message()` can handle the full `TrainingState` dict

**Guardrails**:
- Throttle broadcasts to max 1 per second (same pattern as candidate_progress 50-epoch throttle)
- Only broadcast fields that changed (or always send full state — simpler)

### Approach B: Add REST State Polling to Canopy Service Adapter

**Description**: Add a periodic REST poll from Canopy to CasCor's `GET /v1/training/status`
endpoint (alongside the existing WebSocket relay) to fetch the full TrainingState including
all progress fields.

**Strengths**:
- No CasCor changes required (canopy-only)
- Works even if WebSocket is disconnected
- Simple implementation — add a timer to poll and update TrainingState

**Weaknesses**:
- Adds latency (polling interval = max delay)
- Adds HTTP overhead per poll cycle
- Duplicates data fetching (WebSocket + REST)
- Masks the real issue (CasCor should broadcast state)

**Risks**:
- Polling too frequently wastes bandwidth
- Polling too infrequently gives stale progress data
- Race conditions between WebSocket updates and REST poll updates

**Guardrails**:
- Use 2-3 second poll interval
- Only update fields that are zero/empty (don't overwrite WS-sourced data)

### Approach C: Hybrid — CasCor Broadcast + Canopy Sync Enhancement

**Description**: Add WebSocket state broadcasts to CasCor (Approach A) AND enhance
Canopy's initial state sync to populate all progress fields on connect (handles
mid-training reconnection).

**Strengths**:
- Fixes root cause AND handles reconnection
- Real-time updates via WebSocket
- Full state recovery on reconnect via enhanced sync
- Most robust solution

**Weaknesses**:
- Requires changes in both repos
- More code to maintain
- Initial sync enhancement may be partially redundant with existing logic

**Risks**:
- Same as Approach A, plus sync timing during reconnect
- Must ensure sync and relay don't produce conflicting updates

**Guardrails**:
- Sync populates state first, then relay takes over
- TrainingState.update_state() is already idempotent (ignores None values)

---

## 5. Recommended Approach

### **Approach C (Hybrid)** — with Approach A as the critical first phase

**Rationale**:

1. **Approach A alone would work for 95% of cases** — the WebSocket relay is stable
   and handles reconnection. Adding broadcasts fixes the root cause.

2. **Approach B alone is a workaround, not a fix** — it masks the CasCor deficiency
   and adds unnecessary polling overhead.

3. **Approach C covers the reconnection edge case** — if Canopy reconnects mid-training,
   the enhanced sync populates all progress fields immediately rather than waiting for
   the next broadcast.

### Implementation Priority

- **Phase 1** (CRITICAL): Approach A — Add WebSocket state broadcasts to CasCor
- **Phase 2** (IMPORTANT): Derive `candidate_pool_status` in Canopy adapter
- **Phase 3** (NICE-TO-HAVE): Enhance initial sync for mid-training reconnect

---

## 6. Implementation Plan

### Phase 1: Add WebSocket State Broadcasts to CasCor

#### Step 1.1: Broadcast Full State on Phase Transitions

**File**: `juniper-cascor/src/api/lifecycle/manager.py`

After each phase transition (output→candidate, candidate→adding_candidate,
adding_candidate→output), broadcast the full TrainingState:

```python
# After state.update_state(...) in phase transition code:
self._broadcast_training_state()
```

Add helper method:

```python
def _broadcast_training_state(self):
    """Broadcast full training state via WebSocket."""
    if self._ws_manager:
        state_dict = self.training_state.get_state()
        self._ws_manager.broadcast_from_thread(
            create_state_message(state_dict)
        )
```

#### Step 1.2: Broadcast State After Grow Iteration Updates

**File**: `juniper-cascor/src/api/lifecycle/manager.py`

In `_grow_iteration_callback`, after calling `state.update_state(...)`, broadcast:

```python
def _grow_iteration_callback(self, iteration, max_iterations, ...):
    self.training_state.update_state(
        grow_iteration=iteration,
        grow_max=max_iterations,
        # ... other fields
    )
    self._broadcast_training_state()  # NEW
```

#### Step 1.3: Broadcast State After Output Training Phase Starts

**File**: `juniper-cascor/src/api/lifecycle/manager.py`

In `_output_training_callback`, broadcast state:

```python
def _output_training_callback(self, epoch, total_epochs, loss):
    self.training_state.update_state(
        phase_detail="training_output",
        # ... other fields
    )
    self._broadcast_training_state()  # NEW (throttled)
```

#### Step 1.4: Throttle High-Frequency Broadcasts

Add a simple time-based throttle to prevent flooding:

```python
import time

def _broadcast_training_state(self, force=False):
    """Broadcast full training state via WebSocket (throttled to 1/sec)."""
    now = time.monotonic()
    if not force and hasattr(self, '_last_state_broadcast') and now - self._last_state_broadcast < 1.0:
        return
    self._last_state_broadcast = now
    if self._ws_manager:
        state_dict = self.training_state.get_state()
        self._ws_manager.broadcast_from_thread(
            create_state_message(state_dict)
        )
```

#### Step 1.5: Replace Hardcoded Training Start Message

Replace the hardcoded `{"status": "Started", "phase": "Output"}` broadcast with a full
state broadcast:

```python
# BEFORE:
create_state_message({"status": "Started", "phase": "Output"})

# AFTER:
self._broadcast_training_state(force=True)
```

### Phase 2: Derive candidate_pool_status in Canopy Adapter

#### Step 2.1: Map phase_detail to candidate_pool_status

**File**: `juniper-canopy/src/backend/cascor_service_adapter.py`

In the `_state_update_callback` (the relay handler for `state` messages), derive
`candidate_pool_status` from `phase_detail`:

```python
# In the state message handler:
phase_detail = data.get("phase_detail", "")
candidate_pool_status = "Inactive"
if phase_detail == "training_candidates":
    candidate_pool_status = "Training"
elif phase_detail == "adding_candidate":
    candidate_pool_status = "Selecting Best"
elif phase_detail == "training_output":
    candidate_pool_status = "Inactive"

self._state_update_callback(
    ...,
    candidate_pool_status=candidate_pool_status,
)
```

#### Step 2.2: Add candidate_pool_status to TrainingState (if not present)

**File**: `juniper-canopy/src/backend/state_sync.py` (or wherever TrainingState is defined)

Ensure `candidate_pool_status` is in the `_STATE_FIELDS` dict with default `"Inactive"`.

### Phase 3: Enhance Initial Sync (Mid-Training Reconnect)

#### Step 3.1: Fetch Full Training State on Initial Sync

**File**: `juniper-canopy/src/backend/state_sync.py`

During `CascorStateSync.sync()`, also extract progress fields from the training status
response (which already contains the full `TrainingState`):

```python
# In sync():
status = self._client.get_training_status()
training_state = status.get("training_state", {})
# Extract ALL progress fields
state.update_state(
    grow_iteration=training_state.get("grow_iteration", 0),
    grow_max=training_state.get("grow_max", 0),
    candidates_trained=training_state.get("candidates_trained", 0),
    candidates_total=training_state.get("candidates_total", 0),
    phase_detail=training_state.get("phase_detail", ""),
    phase_started_at=training_state.get("phase_started_at", ""),
    candidate_epoch=training_state.get("candidate_epoch", 0),
    candidate_total_epochs=training_state.get("candidate_total_epochs", 0),
    best_correlation=training_state.get("best_correlation", 0.0),
)
```

---

## 7. Verification Plan

### 7.1 Unit Tests

```bash
# CasCor — verify broadcasts
cd /home/pcalnon/Development/python/Juniper/juniper-cascor
conda activate JuniperCascor
pytest src/tests/unit/api/ -v -k "broadcast or state_message"

# Canopy — verify display handlers
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
conda activate JuniperPython
pytest tests/unit/ -v -k "progress or candidate_pool"
```

### 7.2 Integration Validation

```bash
# Launch all services
${HOME}/Development/python/Juniper/juniper-ml/util/launch_full_monty.bash

# Open dashboard
# http://localhost:8050/dashboard

# Start training via dashboard or curl:
curl -X POST http://localhost:8201/v1/training/start

# Verify:
# 1. Grow iteration progress bar appears and fills
# 2. Candidate epoch progress bar appears during candidate phase
# 3. Phase detail text updates ("training_output" → "training_candidates" → "adding_candidate")
# 4. Best correlation updates during candidate training
# 5. Candidates trained/total updates
# 6. Phase duration timer counts up
# 7. Candidate pool display shows "Training" status with candidate data
```

### 7.3 Visual Verification Checklist

- [ ] Progress bars appear when training starts
- [ ] Grow iteration bar shows "N/M" with correct fill percentage
- [ ] Candidate epoch bar shows "N/M" with correct fill percentage
- [ ] Bars hide when training is stopped/idle
- [ ] Phase detail text updates on phase transitions
- [ ] Best correlation value updates during candidate training
- [ ] Candidates trained/total increments correctly
- [ ] Phase duration timer counts up during active phase
- [ ] Candidate pool section shows "Training" during candidate phase
- [ ] Candidate pool section shows "Inactive" during output phase
- [ ] All fields reset to zero/empty when training completes or is stopped

### 7.4 REST API Verification

```bash
# During active training:
curl http://localhost:8050/api/state | python3 -m json.tool

# Verify these fields are non-zero:
# grow_iteration, grow_max, phase_detail, phase_started_at
# During candidate phase additionally:
# candidate_epoch, candidate_total_epochs, best_correlation, candidates_trained, candidates_total
```

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WebSocket broadcast floods during fast training | Medium | Low | 1-second throttle on `_broadcast_training_state` |
| `create_state_message()` can't handle full TrainingState dict | Low | High | Verify format compatibility; `create_state_message` wraps any dict |
| Canopy relay doesn't handle new fields in state messages | Low | Low | Relay already forwards all fields via `data.get()` patterns |
| Thread safety in `_broadcast_training_state` | Medium | Medium | `broadcast_from_thread` is already thread-safe (uses queue) |
| Breaking existing WebSocket consumers | Low | Medium | State message format is additive (more fields, same structure) |
| Candidate pool status derivation incorrect | Low | Low | Simple phase_detail → status mapping; easy to adjust |
| Mid-training reconnect sync races with relay | Low | Low | `update_state()` is idempotent; last-write-wins is acceptable |
| CasCor tests fail due to new broadcasts | Medium | Low | Mock WebSocket manager in tests; broadcasts are fire-and-forget |

---

## 9. Files Requiring Modification

### Phase 1: CasCor WebSocket Broadcasts

| File | Changes |
|------|---------|
| `juniper-cascor/src/api/lifecycle/manager.py` | Add `_broadcast_training_state()` method; call it in `_grow_iteration_callback`, `_output_training_callback`, phase transitions; replace hardcoded training start message |

### Phase 2: Canopy Candidate Pool Status

| File | Changes |
|------|---------|
| `juniper-canopy/src/backend/cascor_service_adapter.py` | Derive `candidate_pool_status` from `phase_detail` in state relay handler |

### Phase 3: Canopy Initial Sync Enhancement

| File | Changes |
|------|---------|
| `juniper-canopy/src/backend/state_sync.py` | Extract all progress fields during initial sync |

### Files NOT Requiring Modification

- `metrics_panel.py` — UI components and callbacks already correct
- `dashboard_manager.py` — state store data flow already correct
- `main.py` — `/api/state` endpoint already returns full TrainingState
- `monitor.py` (CasCor) — TrainingState fields already correct
- `training.py` routes — REST endpoints already return full state

---

*End of Candidate Training Display Fixes Plan*
