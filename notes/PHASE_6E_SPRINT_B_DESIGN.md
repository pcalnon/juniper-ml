# Phase 6E Sprint B — Snapshot operations: Restore, Replay, Resume, Retrain

**Status**: Design — pending implementation • **Last updated**: 2026-05-01
**Owner**: Paul Calnon • **Sprint**: Phase 6E Sprint B • **Linear/issue**: CAN-015 (parent)

## Executive summary

Sprint B expands the snapshot interaction surface from a single ambiguous
"restore" operation into **four distinct, semantically-clear operations**
each with its own endpoint, FSM transitions, and UI controls:

1. **Restore** — load a snapshot for inspection and modification (NOT for
   continuing training). Time index defaults to *end* of snapshot. User
   can investigate, modify, and re-snapshot. Successor sprints will add
   weight/topology editing endpoints; this sprint exposes the meta-param
   and dataset modification paths that already exist post-Sprint A.
2. **Replay** — read-only playback of a snapshotted training run's
   metrics and topology evolution. Time index starts at *beginning* of
   snapshot window; user controls play/pause/speed/scrubber/range. No
   training occurs. **V1 scope: metrics + topology only** (per-epoch
   weight history is deferred — see §10).
3. **Resume** — load a snapshot and continue training from where it left
   off. Pre-resume history is read-only; new training extends the same
   history arrays. Re-snapshotting captures the comprehensive history.
   Time index defaults to *end* of snapshot window.
4. **Retrain** — load a snapshot's weights + topology + meta-params but
   reset all training history / counters / FSM state. The fresh run
   starts from time index 0. Closest match to the original "snapshot
   replay → fresh training" intent in the Phase 6E roadmap.

The four operations share a single underlying load path, differing in
post-load FSM state, history-locking semantics, and which controls are
available next.

This doc supersedes the single B-1 row in
[`PHASE_6E_DESIGN.md`](./PHASE_6E_DESIGN.md#sprint-b--snapshot-replay-loop)
and expands CAN-015 in
[`JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`](./JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md)
into:

- **Active (Sprint B)**: CAN-015a (Retrain), CAN-015b (Resume),
  CAN-015c (Replay V1 infra), CAN-015d (Restore enrichment),
  CAN-015e (canopy entry points), CAN-015f (canopy replay player V1)
- **Deferred to dedicated post-Phase-6E sprints**: CAN-015g (Replay V2
  with per-epoch weight history), CAN-015h (Restore weight + topology
  editing endpoints)

## 1. Operation matrix

| Operation | Endpoint | Time index default | Training next? | Pre-load history | What's editable post-load |
|---|---|---|---|---|---|
| **Restore** | `POST /v1/snapshots/{id}/restore` | End of window | **Investigation only** (training requires explicit Retrain or new start) | Editable in V2 (deferred) | Meta-params, dataset (V1); + weights, topology (V2 deferred) |
| **Replay** | `POST /v1/snapshots/{id}/replay` + `/replay/control` | Start of window | No (replay is read-only) | Read-only | Playback controls only (play/pause/speed/seek/range) |
| **Resume** | `POST /v1/snapshots/{id}/resume` | End of window | **Yes** (continues into existing history) | Read-only (locked at resume point) | Meta-params, dataset |
| **Retrain** | `POST /v1/snapshots/{id}/retrain` | 0 (reset) | **Yes** (fresh history) | Discarded | Meta-params, dataset |

**Symmetry note**: All four endpoints follow the same shape
(`POST /v1/snapshots/{id}/<verb>`), share the same load path internally,
and return a unified response body (see §3).

## 2. Per-endpoint specifications

### 2.1 Restore — `POST /v1/snapshots/{id}/restore`

**Purpose**: load a previously-snapshotted network for inspection or
modification, **not** to continue training. Use cases include:
investigating training behavior, exploring topology quirks, modifying
the network as a starting point for a new snapshot (which can then be
fed to Resume / Retrain / inference).

**Behavior**:

- Loads weights, topology, full training history, all meta-parameters,
  per-A-5 (CAN-014) parameter round-trip.
- FSM transitions to a new **`Investigating`** state — distinct from
  `Stopped`/`Idle`/`Paused`.
- `Investigating` rejects `start_training` / `pause_training` /
  `resume_training` commands. The user must explicitly invoke a new
  operation (Retrain, Resume, or save-then-load) to enter a training
  state.
- Time-index metadata in the response is "end of window" (the snapshot's
  final state — which is what the loaded model actually represents,
  since intermediate weights aren't persisted).

**Allowed mutations while in `Investigating`** (V1):

- `PATCH /v1/training/params` — meta-param edits
- Dataset replacement (existing API surface)
- `POST /v1/snapshots` — re-snapshot the modified state

**Allowed mutations while in `Investigating`** (V2, deferred — see §10):

- Weight tensor editing endpoints (e.g. `PATCH /v1/network/weights`)
- Topology editing endpoints (e.g. `POST /v1/network/hidden-units`,
  `DELETE /v1/network/hidden-units/{idx}`)

**Response shape**:

```json
{
  "status": "success",
  "data": {
    "snapshot_id": "snapshot_20260501T040200Z",
    "operation": "restore",
    "fsm_state": "Investigating",
    "time_index": {
      "default": "end",
      "snapshot_window": {"start_epoch": 0, "end_epoch": 1234}
    },
    "training_params": { /* same shape as GET /v1/training/params */ }
  }
}
```

**FSM transition**: `* → Investigating` (from any non-active state;
rejects with 409 if currently training).

### 2.2 Replay — `POST /v1/snapshots/{id}/replay` + `/replay/control`

**Purpose**: read-only playback of a snapshotted training run for
visualization and analysis. Lets users watch how training metrics and
topology evolved over time without re-running training.

**V1 scope** (this sprint):

- Metric arrays: `train_loss[]`, `value_loss[]`, `train_accuracy[]`,
  `value_accuracy[]` — all already persisted today.
- Topology evolution: per-cascade-unit metadata (insertion epoch,
  correlation, weight shape) — already persisted today.

**V2 deferred** (own sprint, post-Phase-6E):

- Per-epoch weight tensor playback (decision boundary animation,
  per-unit weight evolution). Requires a new snapshot-format extension
  to persist weight tensors at every epoch (see §10 for risk analysis).

**Behavior**:

- `POST /v1/snapshots/{id}/replay` enters a new **`Replaying`** FSM
  state. Returns the snapshot metadata + replay session ID + initial
  time index.
- `POST /v1/snapshots/{id}/replay/control` accepts a body with one of:
  - `{"action": "play"}` — start advancing the time index at current speed
  - `{"action": "pause"}` — stop advancing
  - `{"action": "seek", "time_index": <int>}` — jump to a specific epoch
  - `{"action": "speed", "value": <float>}` — set playback speed
    (allowed range: 0.1×–10×, with 0× equivalent to pause; bidirectional
    means -1× plays backward, etc.)
  - `{"action": "range", "start": <int>, "end": <int>}` — restrict
    playback to a sub-window
  - `{"action": "stop"}` — exit `Replaying` state, return to prior FSM
- Server-driven event emission: while playing, the lifecycle emits
  synthetic `epoch_end`-style events on the WebSocket so canopy can
  render the playback through its existing metrics-curve and
  topology-evolution components.

**FSM transitions**:
- `Stopped → Replaying` (via `/replay`)
- `Replaying → Stopped` (via `/replay/control` with `stop`)
- `Replaying` rejects `start_training`, `pause_training`,
  `resume_training`, `update_params`, dataset changes (407 Locked).
- `Replaying` accepts only `replay/control`.

**Read-only history guarantee**: nothing in the snapshot or the
network's training_state can be mutated while in `Replaying`. The
synthetic events are emitted to subscribers but don't append to
`metrics_buffer`.

### 2.3 Resume — `POST /v1/snapshots/{id}/resume`

**Purpose**: continue training a previously-snapshotted network from
exactly where the snapshot left off, possibly with adjusted meta-params
or dataset. The pre-resume history is read-only; new training appends
to the same history arrays so re-snapshotting captures a comprehensive
end-to-end record.

**Behavior**:

- Loads the snapshot identically to Restore.
- FSM transitions to **`ResumeReady`** (a sibling of `Stopped` that
  records the resume point). `start_training` from `ResumeReady`
  appends to existing history arrays rather than clearing them.
- `lifecycle._auto_snap_best_metric` is **preserved** (the previous
  run's accuracy ceiling is the new baseline — beating it is the bar
  for fresh auto-snaps).
- A `resume_point_epoch` marker is set on the lifecycle so canopy can
  render a visual boundary in the metrics-curve component (e.g. a
  vertical dashed line) without modifying the underlying arrays.
- Time-index metadata in the response is "end of window."

**Allowed mutations between `/resume` and `start_training`**:

- `PATCH /v1/training/params` — meta-param edits
- Dataset replacement

**FSM transitions**:
- `* → ResumeReady` (from non-active states; rejects with 409 if active)
- `ResumeReady → Started` (via `start_training`, normal transition)

### 2.4 Retrain — `POST /v1/snapshots/{id}/retrain`

**Purpose**: use a previously-trained network as a starting point for a
**fresh** training run. Weights and topology are preserved (so the user
benefits from prior training) but all history-related state is reset
(so the new run is judged on its own merits).

**Behavior**:

- Loads the snapshot identically to Restore/Resume.
- **Resets** the following fields (per Sprint B answer to D2):

| Field | Action |
|---|---|
| Network weights | **Preserved** |
| Tunable params (learning_rate, optimizer_type, …) | **Preserved** |
| Network training history arrays (`train_loss[]`, etc.) | **Cleared** |
| `lifecycle.training_state.current_epoch` / `current_step` | Reset to 0 |
| `lifecycle.training_state.history` | Cleared |
| `lifecycle._auto_snap_best_metric` | Reset to None (already happens in `start_training`; explicit clear on retrain is cleaner) |
| `lifecycle.state_machine` | Transition to `Stopped` / `Idle` |
| `lifecycle.training_monitor.metrics_buffer` | Cleared |

- FSM transitions to `Stopped` / `Idle` directly (no intermediate state
  needed — Retrain is functionally equivalent to "freshly created
  network with the snapshot's weights/topology/params loaded").
- Time index reset to 0.

**Allowed mutations between `/retrain` and `start_training`**:

- `PATCH /v1/training/params`
- Dataset replacement

This is the closest analog to "snapshot replay → fresh training" in the
original Phase 6E roadmap and is the simplest of the four endpoints to
implement and test.

## 3. Unified response shape

All four endpoints return a body with this shape (some fields conditional):

```json
{
  "status": "success",
  "data": {
    "snapshot_id": "<id>",
    "operation": "restore" | "replay" | "resume" | "retrain",
    "fsm_state": "Investigating" | "Replaying" | "ResumeReady" | "Stopped",
    "time_index": {
      "default": "start" | "end" | 0,
      "snapshot_window": {"start_epoch": <int>, "end_epoch": <int>}
    },
    "training_params": { /* same as GET /v1/training/params, omitted for replay */ }
  }
}
```

This is a strict superset of the post-A-5 `/restore` response, so
existing clients that ignore unknown keys are unaffected.

## 4. Time-index concept

The "time index" is **UI metadata, not state-affecting** for Restore /
Resume / Retrain — the underlying loaded model is always the snapshot's
final-epoch state (because intermediate weights aren't persisted). The
time index tells the canopy UI *where the user is conceptually* in the
snapshot's narrative:

- **Restore**: end of window — the user is examining the model "as it
  finished training."
- **Replay**: start of window — playback begins from epoch 0 and walks
  forward.
- **Resume**: end of window — the user is at the resume point about to
  continue.
- **Retrain**: 0 — the snapshot's history is gone; we start fresh.

For Replay, the time index *is* state-affecting — it determines what
playback frame is currently visible.

## 5. FSM extensions

Three new states are added to `TrainingStateMachine`:

| State | Purpose | Permitted commands |
|---|---|---|
| `Investigating` | Restore landed, user inspecting/modifying | `update_params`, snapshot ops, dataset replacement, `restart` (any of replay/resume/retrain) |
| `Replaying` | Replay playback active | Only `/replay/control` |
| `ResumeReady` | Resume landed, ready to continue training | `update_params`, dataset replacement, `start_training` (which appends to existing history) |

`Stopped` is unchanged. Existing transitions are preserved. Each new
state has explicit guards to reject incompatible commands with HTTP 409
(Conflict) for "wrong state" or 423 (Locked) for "explicit read-only."

## 6. Lifecycle plumbing

A single `_load_snapshot_inner(snapshot_id, mode)` helper handles the
common load logic. `mode` is one of `"restore"`, `"replay"`,
`"resume"`, `"retrain"` and drives:

- Which FSM state to transition into post-load
- Whether to reset history fields (only Retrain)
- Whether to set the `resume_point_epoch` marker (only Resume)
- Whether to set up the replay event emitter (only Replay)
- What time-index default to surface

This keeps the four endpoint handlers thin (each just calls the helper
with a different mode and formats the response).

## 7. UX entry points (canopy)

Three parallel surfaces, all routed to the same four endpoints:

1. **Two-step modal** launched from the Load button on the snapshot
   list. Modal shows the four operations as primary buttons with
   inline descriptions ("Restore for inspection", "Replay this run",
   "Resume training from end", "Retrain from these weights"). User
   selects one, modal closes, app transitions to the resulting FSM
   state.
2. **Dropdown** from the Load button on the snapshot list — same four
   options, no modal, single-click action.
3. **Right-click context menu** on each snapshot list item — same four
   options as menu items.

All three surfaces resolve to the same `cascor_service_adapter` method
per operation (e.g. `adapter.restore_snapshot(id)`,
`adapter.replay_snapshot(id)`, etc.).

For Restore / Resume / Retrain, after the operation lands the user is
in the appropriate FSM state and can:

- Edit meta-params via the existing sidebar (Phase 6E Sprint A
  controls)
- Edit the dataset via the existing dataset surface
- Click "Start Training" (existing button) when ready (only fires when
  FSM allows — Investigating disables it; ResumeReady enables it;
  Stopped/Retrain enables it)

For Replay, a new player UI is shown (B-6):

- Play / Pause buttons
- Speed slider, bidirectional from 1.0× (range 0.1×–10×, including
  negative values for backward playback)
- Scrubber showing current epoch / total epochs
- Time-range selector to restrict playback to a sub-window

## 8. PR breakdown

Six PRs total — four cascor, two canopy. Each is independently
reviewable and shippable.

| PR | CAN-ID | Repo | Title (working) | Touches |
|---|---|---|---|---|
| **B-1** | CAN-015a | cascor | `feat(snapshot): retrain endpoint + lifecycle reset path` | `lifecycle/manager.py`, `routes/snapshots.py`, tests |
| **B-2** | CAN-015b | cascor | `feat(snapshot): resume endpoint + ResumeReady FSM state + read-only-history boundary` | `lifecycle/manager.py`, `routes/snapshots.py`, FSM, tests |
| **B-3** | CAN-015c | cascor | `feat(snapshot): replay infrastructure + Replaying FSM state + control endpoint` | `lifecycle/manager.py`, `routes/snapshots.py`, FSM, replay event emitter, tests |
| **B-4** | CAN-015d | cascor | `feat(snapshot): restore enrichment + Investigating FSM state + unified response shape` | `lifecycle/manager.py`, `routes/snapshots.py`, FSM, tests |
| **B-5** | CAN-015e | canopy | `feat(snapshots): UX entry points — modal + dropdown + context menu for restore/replay/resume/retrain` | snapshot-list panel, sidebar wiring, adapter |
| **B-6** | CAN-015f | canopy | `feat(replay): metrics + topology playback player UI (V1)` | new replay-player component, control bindings to B-3 |

### 8.1 Implementation order

Recommended sequence (roughly dependency-aware):

1. **B-1** (Retrain) — smallest, cleanest semantics, fastest validation
   of the four-endpoint approach.
2. **B-2** (Resume) — extends the same lifecycle helper; adds first new
   FSM state.
3. **B-4** (Restore enrichment) — cleans up the existing `/restore`
   endpoint to fit the unified shape before B-3 extends the FSM
   further.
4. **B-3** (Replay infrastructure) — most complex cascor PR; depends
   on the FSM extensions being settled.
5. **B-5** (Canopy entry points) — can land any time after B-1's first
   endpoint exists, but most useful after the full four-endpoint
   matrix is in.
6. **B-6** (Canopy replay player) — depends on B-3 being live.

## 9. Reset scope (Retrain only)

Only Retrain resets history. The exact scope (per Sprint B design
decision D2):

| Field | Reset on `retrain`? |
|---|---|
| Network weights | No |
| Tunable params | No |
| Network training history arrays (`train_loss[]`, etc.) | Yes |
| `lifecycle.training_state.current_epoch` / `current_step` | Yes |
| `lifecycle.training_state.history` | Yes |
| `lifecycle._auto_snap_best_metric` | Yes |
| `lifecycle.state_machine` | Reset to `Stopped` / `Idle` |
| `lifecycle.training_monitor.metrics_buffer` | Yes |

Restore, Replay, and Resume preserve all of the above (Replay locks
them read-only; Resume locks pre-resume history specifically).

## 10. Deferred work (post-Phase-6E)

Two pieces of the user-facing spec are intentionally deferred from
Sprint B and tracked as separate roadmap items:

### 10.1 CAN-015g — Replay V2: per-epoch weight history

**Status**: Deferred to a dedicated future sprint • **Priority**: P3

**Scope**:

- Extend the HDF5 snapshot serializer to persist weight tensors at
  every epoch (or at a configurable subsampling rate).
- Add an in-memory weight-cache to the lifecycle's replay session so
  scrubbing through time produces accurate weight reconstructions.
- Extend canopy's replay player to render decision-boundary surfaces
  and per-unit weight values at the current time index.

**Risks** (must be addressed in the dedicated sprint's design):

- File-size inflation: a 10000-epoch run with 50 hidden units and 10
  inputs would persist ~5×10⁶ weight values × 8 bytes × 10000 epochs ≈
  400 GB per snapshot. Subsampling, delta encoding, or
  trigger-based-snapshotting (e.g. every cascade growth event) is
  necessary.
- Backward compatibility: V1-replay snapshots (without weight history)
  must still load; the player should gracefully fall back to
  metrics-only playback.

**Documented references**:

- This doc, §1, §2.2 ("V2 deferred")
- [`PHASE_6E_DESIGN.md`](./PHASE_6E_DESIGN.md) — to be updated to point
  here
- [`JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`](./JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md)
  — to be updated with a CAN-015e row

### 10.2 CAN-015h — Restore editing: weight + topology modification

**Status**: Deferred to a dedicated future sprint • **Priority**: P3

**Scope**:

- Weight-edit endpoints — design TBD (likely `PATCH /v1/network/weights`
  with shape validation, plus bulk import/export for tensor files).
- Topology-edit endpoints — design TBD (likely
  `POST /v1/network/hidden-units` and
  `DELETE /v1/network/hidden-units/{idx}` with cascade-rebuild
  semantics).
- Canopy UI for both — likely a separate "Network editor" panel
  reachable from the `Investigating` state.

**Why deferred**:

- Weight editing requires careful validation (NaN/Inf checks, shape
  enforcement, dtype matching).
- Topology editing has subtle invariants (cascade order, connectivity
  matrix consistency, optimizer state when units are added/removed).
- Each non-trivial alone, together they're a separate sprint of
  similar size to current Sprint B.

**Documented references** — same as 10.1.

## 11. Risks and open questions

### 11.1 Replay event-emission cadence

Server-driven event emission means the cascor lifecycle pushes
synthetic events out at the playback speed. At 10× speed and 10000
epochs, the WebSocket emits events every ~100µs — likely overwhelms
the canopy renderer.

**Mitigation**: subsample events at high speeds (e.g. emit only every
Nth epoch when speed > 1×) or use coalesced batched updates. Decide in
B-3 design.

### 11.2 Concurrent operations

Two clients sending `/replay` for the same snapshot — does the cascor
backend support concurrent replay sessions? **Decision**: V1 is single-
session (only one operation active at a time, FSM enforces this).

### 11.3 Long-running replay vs idle timeout

A user can leave Replay paused for hours. The lifecycle has no idle-
timeout for `Replaying` today. **Decision**: V1 leaves this open;
canopy should disconnect-and-reconnect cleanly without breaking the
replay session.

### 11.4 Backward compatibility of `/restore` endpoint

The existing `/restore` endpoint already has clients (canopy's
`Restore` button). B-4 changes its FSM transition (now goes to
`Investigating` instead of `Stopped`) and enriches its response shape.

**Mitigation**: response shape is strictly additive; existing clients
that key off `snapshot_id` and `status` continue to work. The
`Investigating` state is permissive enough that nothing the existing
canopy does will be rejected (it doesn't try to start_training
immediately after restore today).

## 12. Test plan summary

### Cascor (per PR)

- B-1: Retrain reset semantics — every field in §9 verified pre/post.
  Round-trip test: train → snapshot → retrain → start_training →
  verify history is fresh.
- B-2: Resume continuation — train → snapshot → resume → start_training
  → verify history extends, `resume_point_epoch` is set, auto-snap
  baseline is preserved.
- B-3: Replay state machine — enter/exit, reject training commands in
  Replaying, control endpoint actions, event emission cadence.
- B-4: Restore Investigating state — reject training commands, allow
  PATCH params, snapshot save round-trips through the FSM cleanly.

### Canopy (per PR)

- B-5: Each of the three entry surfaces (modal / dropdown / context
  menu) routes correctly for each of the four operations. Adapter unit
  tests for each `(snapshot_id, op)` pair.
- B-6: Replay player controls — play/pause, speed, scrubber, range
  selector. Snapshot-driven event consumption.

## 13. Documentation deliverables

This sprint produces / updates:

- **This doc** — `notes/PHASE_6E_SPRINT_B_DESIGN.md` (new)
- **`notes/PHASE_6E_DESIGN.md`** — replace single B-1 row with the
  6-PR breakdown; reference this doc
- **`notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`**
  — fan out CAN-015 to CAN-015a..d (active) + CAN-015e..f (deferred)
- **`juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md`** —
  cross-reference to this doc
- **`juniper-canopy/notes/development/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md`**
  — cross-reference to this doc

## 14. Glossary

- **Snapshot** — HDF5 file persisted by `CascadeHDF5Serializer`,
  containing weights, topology, training history, and (post A-5) all
  runtime-tunable params.
- **Time index / time window** — conceptual position within a
  snapshotted training run's lifetime. UI metadata for Restore /
  Resume / Retrain; state-affecting for Replay.
- **FSM** — `TrainingStateMachine` in `api/lifecycle/state_machine.py`.
- **Read-only history** — the metrics arrays from the loaded snapshot
  cannot be modified or appended to from outside the new training run
  (Resume) or at all (Replay).
- **Resume point** — the epoch index at which Resume began; rendered
  in canopy as a visual boundary.
