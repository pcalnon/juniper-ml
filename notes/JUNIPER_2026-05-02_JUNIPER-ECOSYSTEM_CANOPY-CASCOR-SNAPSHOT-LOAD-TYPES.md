# Open decisions

## D1. Endpoint shape

**Options:** new API endpoint vs flag on existing API endpoint

- A: New endpoint POST /v1/snapshots/{id}/replay (or /restore-for-retrain)
- B: Flag on existing POST /v1/snapshots/{id}/restore?reset_for_retrain=true

**Lean:** A. Different semantics deserve a distinct route — restore preserves history (post-A-5 contract), replay resets it. Two endpoints share most code via a common _load_snapshot_inner(reset) helper. Flag-on-existing makes the side-effect surprising and harder to document.

**Answer:**
New API endpoints should be used; however, the design requirements are not as simplistic as described above.
The additional design decision should be incorporated into all existing design and roadmap documents as applicable.

### Detailed Design Update

The snapshot loading API endpoints should include the following:

1. **Restore** a Snapshot:
    - Endpoint: POST /v1/snapshots/{id}/restore
    - Behavior:
      - This endpoint should preserve the entire history of the model state, all meta-parameters, network topology evolution, and weight training.
      - This option should completely restore the full state of a previous moment-in-time for a given model and the history of how it got there.
      - The time index for this model's training should be set to the end of the snapshot time window by default.
    - Intended Use:
      - User intends to load a model and recreate its exact state, dataset, meta-parameters, and training history that existed when the snapshot was taken.
      - This could be used to set up an existing, snapshotted network for modification and re-snapshotting.
      - This could also be used to allow for a detailed investigation into a specific model state at a specific moment-in-time.
    - Controls:
      - User should be able to modify any meta-parameter.
      - User should be able to modify the dataset.
      - User should be able to modify the network topology.
      - User should be able to modify the network weights.
2. **Replay** a Snapshot:
    - Endpoint: POST /v1/snapshots/{id}/replay
    - Behavior:
      - This endpoint should preserve the entire history of the model state, all meta-parameters, network topology evolution, and weight training.
      - This option should completely restore the full state of a previous moment-in-time for a given model and the history of how it got there.
      - The time index for this model's training should be set to the beginning of the snapshot time window by default.
    - Intended Use:
      - User intends to watch a replay of previously completed (and snapshotted) training of a specific model.
    - Controls:
      - The primary controls for Replay should include a play button to begin the replay.
      - The primary controls should also include a pause button to temporarily stop the replay.
      - User controls should also include ability to set replay speed with a slider that extends in both the faster and slower directions from normal speed.
      - User should be able to select an arbitrary time index within the snapshot and have playback begin from that point.
      - User should be able to select an arbitrary time range within the snapshot and have playback only include that time range.
3. **Resume** a Snapshot:
    - Endpoint: POST /v1/snapshots/{id}/resume
    - Behavior:
      - This endpoint should preserve the entire history of the model state, all meta-parameters, network topology evolution, and weight training.
      - This option should completely restore the full state of a previous moment-in-time for a given model and the history of how it got there.
      - The time index for this model's training should be set to the end of the snapshot time window by default.
    - Intended Use:
      - User intends to continue training a previously trained model beginning at the specific time index when the snapshot was taken.
      - User may decide to modify meta-parameters or even change datasets, but the prepended history of the existing network's state and training should be read-only prior to the Delimited Training Continuation time.
    - Controls:
      - The primary control should be a continue training button.
      - User should be able to modify any meta-parameter.
      - User should be able to modify the dataset.
4. **Retrain** a Snapshot:
    - Endpoint: POST /v1/snapshots/{id}/retrain
    - Behavior:
      - This endpoint should preserve the exact state of the model, all meta-parameter values, and the network topology at the final time index of the snapshot.
      - All history related parameters from the snapshot should be reset to their defaults.
      - This option should completely restore a previously snapshotted model, but should otherwise present a clean-slate for training.
      - The time index for this model's training should be set to Time 0, since all history related data has been reset.
    - Intended Use:
      - User intends to use a potentially, previously trained model as an initial starting point for network training.
      - User may decide to modify meta-parameters or even change datasets before retraining begins.
    - Controls:
      - The primary control should be a begin training button.
      - User should be able to modify any meta-parameter.
      - User should be able to modify the dataset.

## D2. Reset scope

**Options:** What exactly gets reset?

┌───────────────────────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────┐
│                         Field                         │             Reset on replay?              │                                      Why                                      │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ Network weights                                       │ No                                        │ The whole point of replay                                                     │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ Tunable params (learning_rate, optimizer_type, …)     │ No                                        │ A-5 made these round-trip; user can re-tune via PATCH after replay            │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ network training history arrays (train_loss[], etc.)  │ Yes                                       │ Fresh run = fresh metrics                                                     │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ lifecycle.training_state.current_epoch / current_step │ Yes                                       │ Counter starts at 0                                                           │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ lifecycle.training_state.history                      │ Yes                                       │ UI's metrics deque                                                            │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ lifecycle._auto_snap_best_metric                      │ Yes (already does this in start_training) │ Each run judged on its own ceiling                                            │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ lifecycle.state_machine state                         │ Yes → Stopped / Idle                      │ So start_training can transition cleanly                                      │
├───────────────────────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
│ lifecycle.training_monitor.metrics_buffer             │ Yes                                       │ Already cleared on on_training_start, but explicit clear on replay is cleaner │
└───────────────────────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────┘

Lean: this exact list. Conservative — preserves anything that constitutes the model itself, resets anything that constitutes "this training run."

**Answer:**
Note that this question and answer should ONLY pertain to the Retrain API endpoint: POST /v1/snapshots/{id}/retrain.
This exact list should be used to determine what aspects of a snapshot should be reset for the Retrain endpoint.

## D3. Loaded snapshot's training history

How is training history for a loaded snapshot handled?

**Options:** Where does it go?

a. Discarded — fresh metrics start empty
b. Prepended with a visual boundary in canopy
c. Replayed as synthetic monitor events for visualization

**Lean:** (a) for this sprint, (b) as a follow-up if user finds it valuable. (a) is the simplest implementation, matches the "fresh training" semantics, and avoids the canopy-side complication of how to render "this is historical, this is new." If the user's mental model is "I want to see how this snapshot trained then watch the new tuning run from scratch," (a) is correct. If they want to compare-against, that's option (b) and a separate canopy feature.

**Answer:**
The answer to this question is included in the Detailed Design Update section of the D1. question above.

## D4. UX flow

Should Canopy use a single button or a two-step process for snapshot replays?

**Options:**  Starting snapshot replay

- X: Single "Replay" button on snapshot list → endpoint → user is now Stopped/Idle with reset counters → user edits params in sidebar (existing UI) → user clicks "Start Training" (existing button)
- Y: Two-step modal → "Replay" opens dialog with editable params → "Start Replay Training" button does load + reset + start in one call

**Lean:** X. Reuses existing UI surfaces (sidebar, Start Training button), keeps the UX consistent with the rest of canopy, and gives the user maximum flexibility (they can replay-then-walk-away without committing). Y is more "guided" but adds a modal path that doesn't exist anywhere else in canopy.

**Answer:**
The controls providing access to the four operations/endpoints, described in the Detailed Design Update section of the D1. question above, should be made available in the following ways:

- A two-step modal option, launched from the Load button of the snapshot list, that allows one of the viable options to be selected.
- A dropdown from the Load button of the snapshot list that allows a specific option to be selected.
- A right-click context menu, exposed for each the individual snapshots in the snapshot list, that allows one of the viable options to be selected.

## D5. Recommended scope

Work should be done using which of the PR breakdowns?

- 2 paired PRs (cascor + canopy) as proposed
- single combined PR per the original JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_PHASE-6E-DESIGN.md row

**Lean:** Existing JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_PHASE-6E-DESIGN.md:85-86 describes B as 1 PR but follows the same single-row pattern Sprint A used for paired wire-throughs — I'm treating it as 2 PRs to match the established cascor+canopy pairing.

**Answer:**
Use the 2 paired PRs (Sprint A style) as recommended.

---

## Answers to Sharpening Questions

### Answer 1

implementing a replay that is limited to metrics and topology is acceptable as a first step.  ultimately, replay will need full weight history.  rigorously documenting the full replay requirements and adding to appropriate design and roadmap docs should be completed, with notes indicating that this work is being scoped and prioritzed for implementation at a later point in the roadmap.

### Answer 2

to meet the enhanced set of requirements, the endpoint naming should be modified as necessary to provide symmetry with the three new endpoints

### Answer 3

The 5 PRs approach is acceptable

### Answer 4

**Compare:**
fundamentally, resume is about continuing the training of a snapshotted model, possibly with updated meta-parameters, etc.
restore, in contrast, is about restoring to a previously snapshotted state for the purposes of investigating that network model, state, and training.

**Contrast:**

- **Resume:**
  - resume keeps history read-only because training is resuming at the snapshotted point in time.
  - if the resumed network is trained and then re-snapshotted, the new snapshot can be loaded using resume, and the entire training history including pre and post initial resume will be loaded providing a comprehensive picture of how the network's entire training has progressed.

- **Restore:**
  - restore wouldn't be used as a load and then train function.
  - restore is about a facilitating a deep dive into a previously trained and snapshotted network--to better understand its training behavior or topology quirks.
  - a full range of modifications are allowed to provide an extreme level of flexibility enabling a network to be loaded as it existed at snapshot and then changed in significant and/or subtle ways before being saved as a new snapshot.
  - The tweaked snapshot can be used for inference, performance analysis, as a starting point for new training, etc.

---

Q5: Restore's modify-weights / modify-topology surface

  Your Restore controls list four user-modifiable surfaces:

- ✅ Modify meta-parameters — already exists (PATCH /v1/training/params)
- ✅ Modify dataset — already exists (start_training body / set_data flow)
- ❌ Modify network topology — no current API
- ❌ Modify network weights — no current API

  The last two are net-new capabilities. They're substantial — modifying topology means adding/removing/replacing cascade units in a stopped network; modifying weights means a tensor-edit endpoint with shape validation, ideally with bulk import/export
  support. Each is potentially its own sprint.

  Q5: Two paths:

- (I) Tight Sprint B: ship Restore endpoint with loading + FSM "Investigating" state but defer the weight/topology editing capability to a follow-up sprint. The Restore endpoint still completes its primary job (load for inspection) and the user can
  still re-snapshot — they just can't yet edit weights/topology through the API.
- (II) Wide Sprint B: include weight + topology editing endpoints as part of B-1's Restore PR, growing it to ~3-4 PRs on its own.

My lean: (I). Sprint B then becomes manageable; the editing capability gets its own design pass (it's a non-trivial design — versioning, validation, batch vs per-element, undo semantics, etc.). I'll document the deferred work in the design doc with a
clear scope marker.

Locked plan (pending your Q5 answer)

Assuming Q5 = (I):

┌─────┬────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────┐
│ PR  │  Repo  │                                                                           Description                                                                            │                    Deferred                    │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-1 │ cascor │ POST /v1/snapshots/{id}/retrain + lifecycle reset path + tests                                                                                                   │ —                                              │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-2 │ cascor │ POST /v1/snapshots/{id}/resume + read-only-history marker + FSM "Resumed" state + tests                                                                          │ —                                              │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-3 │ cascor │ POST /v1/snapshots/{id}/replay (start) + /replay/control (play/pause/seek/speed/range) + FSM "Replaying" state + server-driven event emission                    │ Per-epoch weight replay (own sprint)           │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-4 │ cascor │ POST /v1/snapshots/{id}/restore enrichment: FSM "Investigating" state + response shape unified with the other 3 endpoints                                        │ Weight/topology editing endpoints (own sprint) │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-5 │ canopy │ UX entry points: Load-button two-step modal + dropdown + right-click context menu, routed to all four cascor endpoints; sidebar wiring for tune-then-train flows │ —                                              │
├─────┼────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ B-6 │ canopy │ Replay player UI: play/pause, bidirectional speed slider, scrubber, time-range selector                                                                          │ Per-epoch weight visualization (own sprint)    │
└─────┴────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────┘

That's 6 PRs (4 cascor + 2 canopy), one more than my earlier 5-PR sketch — the new B-4 reflects the existing /restore endpoint needing FSM-state work to match the new semantics.

Documentation deliverables

After Q5 confirmation:

1. New juniper-ml/notes/JUNIPER_2026-05-01_JUNIPER-ECOSYSTEM_PHASE-6E-SPRINT-B-DESIGN.md — deep-dive doc covering:
    - Four-endpoint matrix with semantics, FSM transitions, response shapes
    - Time-index concept (UI metadata, not state-affecting for Restore/Resume/Retrain)
    - Replay V1 scope (metrics + topology) + V2 deferred (weight history)
    - Restore editing scope deferred (weights, topology endpoints)
    - PR breakdown
2. Update juniper-ml/notes/JUNIPER_2026-05-02_JUNIPER-ECOSYSTEM_PHASE-6E-DESIGN.md — replace the 1-row B-1 entry with the new 6-PR breakdown; reference the new design doc
3. Update juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md — fan out CAN-015 to CAN-015a through CAN-015d, plus deferred items CAN-015e (weight replay) and CAN-015f (Restore editing)
4. Update juniper-cascor/notes/development/PRE-DEPLOYMENT_ROADMAP-2.md and juniper-canopy/notes/development/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md — point at the new design doc

Implementation order (post-design)

B-1 → B-2 → B-4 → B-3 → B-5 → B-6.

Reasoning: Retrain (B-1) is smallest and fully understood — fast win to validate the approach. Resume (B-2) extends the same lifecycle pattern. B-4 (Restore enrichment) cleans up the existing endpoint before B-3's replay state machine extends it
further. Replay infrastructure (B-3) before its UI (B-6). Other canopy entry points (B-5) can land any time after B-1's first endpoint exists.

One question to lock: Q5 — (I) tight or (II) wide?
