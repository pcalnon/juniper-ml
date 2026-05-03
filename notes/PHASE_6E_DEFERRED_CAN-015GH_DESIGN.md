# Phase 6E Deferred Work: CAN-015g + CAN-015h Design

**Owner**: Paul Calnon • **Status**: Draft • **Created**: 2026-05-02
**Tracks**: `CAN-015g` (Replay V2 — per-epoch weight history),
`CAN-015h` (Restore editing — weight + topology modification)
**Parent design**: [`PHASE_6E_SPRINT_B_DESIGN.md`](./PHASE_6E_SPRINT_B_DESIGN.md) §10

---

## Executive summary

Phase 6E Sprint B shipped the four-endpoint snapshot operations matrix
(Restore, Replay V1, Resume, Retrain). Two pieces of the original spec
were deliberately deferred from Sprint B and are scoped here as a
single follow-on sprint:

- **CAN-015g — Replay V2**: per-epoch weight tensor playback. Lifts
  Replay from "metric-curve replay" to "decision-boundary animation
  with per-unit weight evolution."
- **CAN-015h — Restore editing**: in-place network mutation
  (weights + topology) reachable from the post-restore
  `Investigating` FSM state. Adds three cascor mutation endpoints
  plus a canopy "Network editor" panel.

These are complementary but independently shippable. Recommended
sequencing is **g first** (snapshot-format change is the hardest part
and gates Replay improvements) then **h** (mutation endpoints land on
top of a stable serializer).

> **Status note (2026-05-02)**: this plan assumes Sprint B is fully
> merged. At the time of writing the prerequisite check below
> (§"Prerequisite status") flagged that cascor B-3 (#173) and cascor
> B-4 (#171) appear to have merged into stacked parent branches
> rather than `main`, and canopy B-6 (#214) is still open. **Resolve
> the prerequisite block before starting CAN-015g/h work.**
>
> **Revision 2026-05-03**: g-1 (#180), g-2 (#184), and g-3 (#187)
> have been opened against cascor as a stacked PR series and run
> green locally in JuniperCascor1 env. Implementation surfaced one
> gap not in the original draft — nothing in the cascor training
> loop currently *populates* `network.weight_history`, so the V2
> protocol can play back ad-hoc fixtures but not real training
> runs. **g-6** (this revision) adds the live-capture path. See
> §"Live capture during training (g-6)" and the revised
> §"PR breakdown — CAN-015g".

---

## Prerequisite status (verify before starting)

CAN-015g consumes the Replay V1 infrastructure (B-3) and CAN-015h
consumes the `Investigating` FSM state and unified response shape
(B-4). Neither item can begin until both are confirmed on their
respective `main` branches.

| Prereq | Repo | PR | Verification command | Expected | Risk if unmet |
|---|---|---|---|---|---|
| B-1 Retrain | cascor | #169 | `git log origin/main --oneline \| grep CAN-015a` | found (`ecb36df`) | none — verified |
| B-2 Resume | cascor | #170 | `git log origin/main --oneline \| grep CAN-015b` | found (`d45b376`) | none — verified |
| B-3 Replay V1 | cascor | #173 | `git merge-base --is-ancestor e9d51ea origin/main` | exit 0 | **CAN-015g blocked** — Replay V2 extends V1's `_ReplaySession`. PR base was the stacked `feature/b-4-restore-investigating` branch, not `main`. |
| B-4 Investigating FSM | cascor | #171 | `git merge-base --is-ancestor b84cf6c origin/main` | exit 0 | **CAN-015h blocked** — mutation endpoints live behind the `Investigating` gate. PR base was the stacked `feature/b-2-snapshot-resume` branch, not `main`. |
| B-5 UX entry points | canopy | #213 | `git log origin/main --oneline \| grep CAN-015e` | found (`a45877c`) | none — verified |
| B-6 Replay player V1 | canopy | #214 | `gh pr view 214 --json mergedAt -q .mergedAt` | non-null | **CAN-015g player work is stacked on B-6's player surface**; if B-6 doesn't land, V2 ships into a missing UI. |

**Action required before kickoff**: re-merge cascor #171 and #173 with
base `main` (or open new PRs against `main` if the stacked branches
were force-rebased). Confirm canopy #214 is merged. Capture the SHA
of cascor `main` HEAD in the kickoff doc so the implementation team
has an unambiguous base.

---

## CAN-015g — Replay V2: per-epoch weight history

### Problem statement

Replay V1 plays back **metric arrays only**. The loaded model is the
snapshot's final-epoch state for the entire playback — scrubbing to
epoch 50 in a 100-epoch run does not load epoch-50 weights, only
epoch-50 metrics. This means:

- Decision-boundary surfaces in canopy stay frozen at the snapshot's
  final state during replay.
- The per-unit correlation / weight shape evolution shown in
  `network_evolution.py` is wallpaper (cascade-add timestamps only;
  the weight tensors themselves don't change with the scrubber).

V2's goal: at any time index `t` during replay, the canopy frontend
sees the network exactly as it was at epoch `t`, including output
weights, hidden-unit weights, and biases.

### Anchor points (current state)

| File | Symbols | Current behaviour | V2 change |
|---|---|---|---|
| `juniper-cascor/src/snapshots/snapshot_serializer.py` | `CascadeHDF5Serializer.save_network` line ~120, `_save_training_history` line 616, `_save_parameters` line 381, `_save_hidden_units` line 439 | Saves output weights once at snapshot time; saves metric arrays per-epoch; saves `hidden_units_added` metadata-only history | Add a `history/weights/` HDF5 group keyed by epoch (or by sampled-epoch index when subsampling) |
| `juniper-cascor/src/api/lifecycle/manager.py` | `_ReplaySession` (added in B-3, branch `feature/b-3-snapshot-replay`); driver thread emits synthetic `epoch_end` events | Driver reads `network.history["train_loss"][i]` etc. and emits | Driver also reads `network.history["weights"][i]` and emits a parallel weight payload |
| `juniper-cascor/src/api/lifecycle/monitor.py` | `_trigger_callbacks("epoch_end", ...)` | Carries metric values | Optionally include a `weights` payload (size-bounded) |
| `juniper-canopy/src/frontend/components/replay_player_panel.py` | `ReplayPlayerPanel`, `_session_window`, `_merge_session` | Player UI consumes `time_index` only | Subscribe to per-epoch weight payloads, fan out to decision-boundary + network-evolution components |

### Storage strategy (chosen approach)

The 400 GB blow-up cited in the parent design (`§10.1`) makes naive
per-epoch persistence non-viable. Four options were considered; the
plan picks **Option C — adaptive subsampling** with the others
explicitly rejected to lock in the decision.

| Option | Approach | Pros | Cons | Decision |
|---|---|---|---|---|
| **A. Full** | Persist every epoch's weight tensors uncompressed | Pixel-perfect playback; simplest replay logic | 400 GB / 10k-epoch run; HDF5 file would not fit in RAM during load | **Rejected** |
| **B. Delta-encoded** | Persist epoch 0 baseline + per-epoch deltas | Significant size reduction for slow-changing weights | Reconstruction cost is `O(n)` per scrubber move; cumulative float error; complicates partial loads | Rejected — defer to a future V3 if A becomes viable |
| **C. Adaptive subsampling** | Persist weights at every cascade-grow event + every Nth epoch (default `N=50`, configurable per snapshot) | 100×–1000× size reduction; growth events captured exactly; smooth playback between samples via UI interpolation | Scrubbing inside an inter-sample window shows the nearest-sampled state, not exact epoch; user-visible "snap to sample" behaviour | **Chosen — V1 of Replay V2** |
| **D. Trigger-only** | Persist weights only on cascade-grow events | Smallest size; zero overhead between growths | Decision-boundary playback would jump in chunks; useless for runs with infrequent growth | Rejected — Option C subsumes it |

**Rationale**: Option C is the only choice that survives the 400 GB
risk while preserving usability. The cascade-grow trigger is
critical because growth events are *the* visually interesting moment
of cascade-correlation training; sampling them exactly preserves the
narrative arc. The configurable `N` lets advanced users opt into
denser sampling for short-but-detailed runs (`N=1` is equivalent to
Option A for runs that fit in memory).

#### Storage format

HDF5 group structure under each snapshot file:

```text
history/
  weights/
    sample_index/                # int64 array, len = num_samples
                                 # epoch numbers at which weights were captured
    output_weights/              # float32 array [num_samples, in+hid, out]
    output_bias/                 # float32 array [num_samples, out]
    hidden_units/
      0000/                      # one group per hidden unit
        weights/                 # float32 array [num_samples_after_unit_added, in+i]
        bias/                    # float32 array [num_samples_after_unit_added]
        activation/              # uint8 array (enum-coded activation function id)
      0001/
      ...
  meta/
    sampling_strategy            # str attr: "adaptive" | "every_n" | "trigger"
    sampling_interval            # int attr: N (epochs)
    schema_version               # int attr: 2 (V1 snapshots have no `weights/` group)
```

Compression: HDF5 `gzip` level 4 to match the existing
`save_numpy_array` calls in `snapshot_serializer.py` (line 633). The
checksum mechanism already in place (`_save_hidden_units` line 486)
is reused for each weight array.

#### In-memory cache

`_ReplaySession` (lifecycle/manager.py) gains a `WeightCache` helper:

```python
class _WeightCache:
    """Snapshot-scoped cache of per-sample weight tensors.

    Loads lazily — only fetches tensors for the sample range the
    current scrubber position is touching. Eviction policy is LRU
    with a configurable byte budget (default 256 MB) so long-running
    replay sessions on large snapshots don't OOM the cascor process.
    """

    def get(self, sample_index: int) -> dict[str, np.ndarray]:
        ...
    def warm(self, sample_index_range: tuple[int, int]) -> None:
        """Pre-fetch a window — used when /replay/control's `range`
        action narrows the playback window."""
        ...
```

Eviction stats are exposed via the existing
`/v1/replay/control` GET-equivalent (TBD) for ops monitoring. If
deemed too cumbersome, the cache is process-global with a single
budget.

### Backward compatibility

V1 snapshots have no `history/weights/` group. The loader checks
`history/weights/meta/schema_version` and, if missing, the replay
session degrades to V1 behaviour (final-state weights for the whole
playback). The replay/control response shape gains an optional
`weights_available: bool` field; canopy renders the
decision-boundary scrubber as disabled when false.

### Wire format changes

#### `POST /v1/snapshots/{id}/replay` response (additive)

```jsonc
{
  "data": {
    "snapshot_id": "snap_001",
    "operation": "replay",
    "fsm_state": "Replaying",
    "time_index": { /* unchanged */ },
    "session": { /* unchanged from B-3 */ },

    // NEW (CAN-015g):
    "weights_available": true,
    "weight_sampling": {
      "strategy": "adaptive",
      "interval": 50,
      "num_samples": 204,
      "sample_epochs": [0, 50, 100, 137, 150, ...]
    }
  }
}
```

#### Synthetic `epoch_end` event (additive)

The B-3 emitter currently produces metric-only events. V2 extends
them with an optional `weights` block keyed by sample index (not
epoch — the receiver maps sample → epoch via `sample_epochs`). To
keep WebSocket frames small, weights are sent on
**sample-boundary** epochs only; in-between metric events carry
only `epoch` + metric values, and canopy holds the previous weight
snapshot until a new one arrives.

```jsonc
{
  "type": "replay_event",
  "data": {
    "epoch": 137,
    "is_sample_boundary": true,
    "metrics": { "train_loss": 0.12, ... },
    "weights": {  // present only when is_sample_boundary
      "sample_index": 50,
      "output_weights": "<base64 float32 tensor>",
      "output_bias": "<base64 float32 tensor>",
      "hidden_units": [ ... ]
    }
  }
}
```

Tensors are base64-encoded float32 to keep the JSON path simple;
binary WebSocket frames are out of scope for V2 and tracked
separately if profile data shows the JSON overhead matters.

### Canopy consumption

Three components subscribe to the new event:

1. **`replay_player_panel.py`** — gains a "weights at sample" badge
   on the scrubber and a `weights_available` indicator next to the
   FSM badge.
2. **`decision_boundary.py`** — already consumes a current network
   for boundary rendering; replay V2 swaps the live network for the
   replay-session network at the current sample. New callback:
   `update_decision_boundary_from_replay(replay_event)`.
3. **`network_evolution.py`** — already shows a cascade-grow
   timeline; per-sample weight-norm sparklines per unit are added
   when V2 data is present.

A new `dcc.Store(id="replay-weight-buffer")` holds the most-recent
1000 weight events (LRU-evicted older entries) so scrubber moves
within the buffer window are local — no round-trips to cascor.

### Live capture during training (g-6)

> Added 2026-05-03 after g-1/g-2/g-3 implementation surfaced that
> the V2 protocol could *play back* a `weight_history` but nothing
> in the training loop was actually *populating* it. This
> subsection and the g-6 PR row close that gap. Without g-6, V2
> replay only works against snapshots written by ad-hoc test
> fixtures or hand-constructed payloads — production training runs
> would still produce V1-only snapshots even after g-1..g-5 land.

The lifecycle's training loop must populate `network.weight_history`
as training progresses so that `save_snapshot` (existing path)
captures a meaningful V2 payload. Three trigger points cover the
**adaptive subsampling** strategy chosen in §"Storage strategy":

1. **Every Nth epoch** (default `N=50`, configurable per network
   via `config.weight_history_sampling_interval`). The training
   monitor's `on_epoch_end` hook is the natural attach point — it
   already fires once per epoch and runs in the training thread so
   it can read `network.output_weights` / per-unit weights without
   cross-thread locking.
2. **Every cascade-grow event** — the existing cascade-add code
   path appends to `network.history["hidden_units_added"]`; g-6
   appends a parallel record to `network.weight_history` capturing
   the post-grow state. Critical because cascade-grow is the most
   visually interesting moment.
3. **Final epoch of training** — fires from `start_training`'s
   completion path so the last sample reflects the truly-terminal
   weights even when training stops mid-interval.

#### Trigger ordering and idempotency

A single epoch can fire two triggers simultaneously (e.g. epoch
50 is both "Nth-epoch" and the same epoch as a cascade-add).
g-6's append helper deduplicates by `time_index` — a sample for a
given epoch is recorded at most once, with the latest tensors
winning if both fire. This matches the read-side cache assumption
that `sample_indices` is strictly monotonic.

#### Memory ceiling

Per the parent design's 400 GB risk, in-memory weight history must
not grow unboundedly in long runs. g-6 enforces a soft cap of
**1000 samples** by default (configurable via
`config.weight_history_max_samples`); on overflow it follows a
"keep recent + cascade events" policy:

- All cascade-add samples are retained (they're the narrative
  anchors).
- Inter-cascade samples are decimated by 2× whenever the count
  would exceed the cap, doubling the *effective* sampling
  interval.

The cap is conservative — at 1000 samples × ~10 KB/sample for a
small network, memory cost is ~10 MB. Production-sized networks
(100+ MB per sample) will hit the cap in tens of samples and
that's fine: V2 still produces a usable history even with
aggressive decimation, and the user can always lower N via config
to capture more density at the cost of memory.

#### Configuration surface

Two new fields on `CascadeCorrelationConfig`:

| Field | Default | Purpose |
|---|---|---|
| `weight_history_sampling_interval` | `50` | N for the every-Nth-epoch trigger. Set to `1` to capture every epoch (Option A behaviour). Set to `0` to disable the periodic trigger entirely (cascade-grow only — Option D). |
| `weight_history_max_samples` | `1000` | Soft cap before decimation kicks in. `0` means unbounded (use with care). |

Both are runtime-tunable via the existing PATCH `/v1/training/params`
flow (no new endpoint needed). Changes mid-training take effect at
the next `on_epoch_end` hook.

#### Backward compatibility

Networks created before g-6 lands won't have a `weight_history`
attribute initialized. The append helper does `getattr(network,
"weight_history", None) or _init_weight_history(network)` so
pre-g-6 networks pick up V2 capture seamlessly the first time they
hit a trigger.

### PR breakdown — CAN-015g

| PR | Repo | Title | Touches |
|---|---|---|---|
| g-1 | cascor | `feat(snapshot): persist per-sample weights with adaptive sampling (CAN-015g)` | `snapshots/snapshot_serializer.py`, schema_version bump, fixture |
| g-2 | cascor | `feat(replay): wire weight cache into _ReplaySession + extend control response (CAN-015g)` | `lifecycle/manager.py`, `routes/snapshots.py`, route schemas |
| g-3 | cascor | `feat(replay): emit weight payloads on sample-boundary events (CAN-015g)` | `lifecycle/monitor.py`, replay driver thread |
| g-4 | canopy | `feat(replay): consume weight payloads in decision-boundary + network-evolution (CAN-015g)` | `replay_player_panel.py`, `decision_boundary.py`, `network_evolution.py`, dashboard wiring |
| g-5 | both | `docs(snapshot): schema v2 migration notes + interpolation behaviour FAQ` | docs + small README updates |
| g-6 | cascor | `feat(training): capture per-sample weight history during training (CAN-015g)` | `lifecycle/manager.py` training loop, `lifecycle/monitor.py` epoch hook, `cascade_correlation.py` cascade-add hook, `cascade_correlation_config.py` two new tunables |

Order is dependency-driven: g-1 lands the file format, g-2 wires
the read path, g-3 adds emission, g-4 lands canopy. g-5 is
documentation and can land alongside any of g-1..g-4. **g-6**
depends only on g-1 (the schema it writes into) and is otherwise
independent — it can land in parallel with g-2/g-3/g-4 in any
order. Recommended to land g-6 *before* g-4 so the canopy
acceptance test can exercise a snapshot produced by an actual
training run rather than a synthetic fixture; the inverse is also
viable because g-4's tests can synthesize `weight_history`
directly.

### Risks — CAN-015g

| Risk | Severity | Mitigation |
|---|---|---|
| File-size inflation despite Option C | Med | Add `du -h` regression assertion in g-1 fixture: 100-epoch toy run with default `N=50` produces a snapshot ≤ `1.5 ×` the V1 size. Fail fast in CI. |
| In-memory cache OOM on large snapshots | Med | LRU budget (256 MB default) + `warm()` is best-effort; failed pre-fetch logs WARNING but does not abort the session. Add chaos test that exercises 10 GB snapshots. |
| Float drift between save and load | Low | Use float32 throughout; document that NaN/Inf in weights produce `weights_available: false` for the affected sample (graceful degradation). |
| Older canopy clients receive V2 events | Low | Events are additive — old clients ignore the unknown `weights` block. Verify with a B-6-only canopy regression test. |
| Sampling interval too sparse for short runs | Low | Loader emits a WARNING when fewer than 10 samples exist for a snapshot >100 epochs; expose `weight_sampling.num_samples` in `/v1/snapshots/{id}` metadata for ops. |
| g-6 capture overhead slows training (per-epoch tensor copy) | Med | Benchmark in g-6 fixture: 1000-epoch toy run with `N=50` adds ≤ 5% wall-clock to training. Fail merge if the regression exceeds the budget. Offload the copy via `torch.no_grad()` + `.detach().cpu().numpy()` to skip autograd graph retention. |
| g-6 in-memory growth blows memory on long runs | Med | `weight_history_max_samples` cap (default 1000) + decimation policy (cascade-add samples retained; inter-cascade decimated 2× on overflow). Add a chaos test that runs a 100k-epoch synthetic loop and asserts memory stays bounded. |
| g-6 capture races with concurrent replay session | Low | Capture is a thread-local mutation on `network.weight_history`; replay sessions read from a snapshot-loaded copy. The training thread writes; the replay driver thread reads from a *different* network instance (rehydrated from disk). No shared mutation. |
| g-6 trigger fires during cascade-add mid-update (partial weights) | Low | The cascade-add hook fires *after* the new unit is fully installed (same point in the loop where `hidden_units_added` is appended today). The Nth-epoch hook fires from `on_epoch_end` which is after the optimizer step. Both are quiescent points. |

---

## CAN-015h — Restore editing: weight + topology modification

### Problem statement

After `/restore` lands the user in the `Investigating` FSM state
(B-4), the user can inspect the network but cannot mutate it.
CAN-015h adds three mutation endpoints scoped to `Investigating` so
researchers can:

- Patch a specific weight tensor in place (e.g. zero out a unit's
  weights to test ablation).
- Append a fresh hidden unit at the cascade tail (manual
  cascade-grow).
- Remove a hidden unit by index (cascade prune).

After any mutation, the user can re-snapshot, restart training (via
`Resume` or `Retrain`), or simply leave the modified network in
place for inspection.

### Anchor points (current state)

| File | Symbols | Current behaviour | h change |
|---|---|---|---|
| `juniper-cascor/src/cascade_correlation/cascade_correlation.py` | `CascadeCorrelationNetwork.hidden_units`, `output_weights`, `output_optimizer`, candidate-acceptance code paths | Mutation only via training loop | Extract a private `_install_hidden_unit(weights, bias, activation, position=None)` helper that the existing cascade-grow path AND the new endpoint both call |
| `juniper-cascor/src/api/routes/network.py` (73 lines) | `POST /v1/network`, `GET /v1/network`, `DELETE /v1/network`, `GET /v1/network/topology`, `GET /v1/network/stats` | Read-only + create/delete | Add three mutation endpoints (PATCH /weights, POST /hidden-units, DELETE /hidden-units/{idx}) |
| `juniper-cascor/src/api/lifecycle/state_machine.py` | `INVESTIGATING` (B-4), `handle_command` | Permits param/dataset/snapshot ops; rejects training | Extend permit list to include three new commands: `patch_weights`, `add_hidden_unit`, `remove_hidden_unit` |
| `juniper-cascor/src/snapshots/snapshot_serializer.py` | `_save_parameters` line 381, `_save_hidden_units` line 439 | Already saves optimizer state | After mutation, save still works because the optimizer is rebuilt; no serializer change needed |
| `juniper-canopy/...` | none | n/a | New `network_editor_panel.py` reachable from the Snapshots tab when `Investigating` is active |

### Endpoint design

#### 1. `PATCH /v1/network/weights`

```http
PATCH /v1/network/weights
Content-Type: application/json

{
  "target": "output" | "hidden_unit",
  "hidden_unit_index": 3,            // required iff target == "hidden_unit"
  "field": "weights" | "bias",
  "values": [[...], [...]],          // shape must match target tensor exactly
  "dtype": "float32"                 // optional; default float32
}
```

Response (200): unified shape — `{snapshot_id: null, operation:
"patch_weights", fsm_state: "Investigating", network: { ... }}`.
The `network` block carries the post-patch topology snapshot
(reuses `GET /v1/network/topology`'s shape).

**Validation rules**:

- Caller must include the **exact** shape — partial updates are
  rejected with 400. Rationale: prevents subtle off-by-one bugs in
  the wire layer and forces the canopy UI to be explicit.
- NaN / Inf values are rejected with 422.
- Dtype mismatches are auto-cast where lossless (float64 → float32),
  rejected otherwise.
- After applying the patch, the optimizer's state for the touched
  parameter group is **zeroed** (Adam `m` and `v`) since stale
  momentum from pre-patch weights is meaningless.

**FSM gate**: requires `Investigating`. Returns 409 from any other
state.

#### 2. `POST /v1/network/hidden-units`

```http
POST /v1/network/hidden-units
Content-Type: application/json

{
  "weights": [...],                  // shape [in_size + num_existing_units]
  "bias": 0.0,
  "activation": "tanh" | "sigmoid" | "linear" | "relu",
  "position": "tail" | int           // default "tail"; int inserts at index
}
```

Response: same unified shape as PATCH; `operation: "add_hidden_unit"`,
`network` block updated with the new unit appended.

**Cascade rebuild semantics**:

- The output layer is reshaped to `[in + num_units + 1, out]` and
  the **new column** is initialized to **zero** (i.e. the appended
  unit contributes nothing until the user re-trains the output
  layer or patches its weights). This is the same convention the
  existing cascade-grow path uses.
- The optimizer is rebuilt from scratch — no attempt to preserve
  per-parameter momentum across a topology change.
- Inserting at a non-tail position requires a connectivity-matrix
  rewrite. Document in g-2's PR description that the cascade order
  is preserved by always **renumbering** (the unit becomes index
  `position`, all subsequent units shift up by one); inputs that
  pointed at the old index `position` continue to point at it (now
  the inserted unit). This is the safest interpretation but is
  user-surprising — clear UI text required in canopy.

**Validation**:

- Reject if `len(network.hidden_units) >= network.max_hidden_units`
  with 409 (matches training-loop semantics).
- Reject malformed activation strings with 422.
- NaN / Inf in weights or bias → 422.

#### 3. `DELETE /v1/network/hidden-units/{idx}`

```http
DELETE /v1/network/hidden-units/3
```

Response: same unified shape; `operation: "remove_hidden_unit"`.

**Semantics**:

- The unit at `idx` is removed; subsequent units shift down by one.
- The **column** of `output_weights` corresponding to that unit is
  removed; output weights re-shape to `[in + num_units - 1, out]`.
- The optimizer is rebuilt from scratch.
- If `idx >= num_hidden_units` → 404. If `num_hidden_units == 0` →
  404 (rather than the more confusing 409).

#### Common: `_install_hidden_unit` extraction

To avoid divergence between the training loop's cascade-grow code
and the new endpoint, refactor the candidate-acceptance code in
`cascade_correlation.py` to call a shared
`_install_hidden_unit(weights, bias, activation, position)` helper.
The existing training-loop path passes `position="tail"` and the
candidate's trained weights; the new endpoint passes the
user-supplied tensor.

This refactor is a **prerequisite PR (h-0)** before the endpoint
PRs land — it should not change behaviour, and lands with a unit
test that asserts the existing cascade-grow path still produces
bit-identical output for a fixed-seed toy run.

### Canopy "Network editor" panel

New component at `juniper-canopy/src/frontend/components/network_editor_panel.py`:

- Idle state when FSM != `Investigating`: explains "Restore a
  snapshot to enable editing" with a deeplink to the Snapshots tab.
- Active state (Investigating):
  - Topology table mirroring `GET /v1/network/topology`. Each
    hidden-unit row has an inline "Delete" button (with
    confirmation modal) and a "Patch weights" expander.
  - "Append hidden unit" form at the tail of the table.
  - Output-layer "Patch weights" expander as a separate card.
  - All forms use the existing tensor-input convention from the
    Parameters tab.
- New tab "Network Editor" between "Replay" and "Redis" in
  `dashboard_manager.py`'s `visualization-tabs`.

### Investigating FSM extension

`Investigating` already permits `update_params` and dataset
changes. Add three commands to its allowed set:

```python
# state_machine.py — Investigating permitted_commands
permitted_commands = {
    "update_params",
    "replace_dataset",
    "snapshot_op",        # any of {restore, replay, resume, retrain}
    # CAN-015h additions:
    "patch_weights",
    "add_hidden_unit",
    "remove_hidden_unit",
}
```

### PR breakdown — CAN-015h

| PR | Repo | Title | Touches |
|---|---|---|---|
| h-0 | cascor | `refactor(network): extract _install_hidden_unit helper (no behaviour change) (CAN-015h prep)` | `cascade_correlation.py`, fixed-seed bit-identity test |
| h-1 | cascor | `feat(network): PATCH /v1/network/weights with shape + NaN validation (CAN-015h)` | `routes/network.py`, FSM extension, optimizer state zero-out |
| h-2 | cascor | `feat(network): POST /v1/network/hidden-units with cascade rebuild (CAN-015h)` | `routes/network.py`, `cascade_correlation.py` (uses h-0) |
| h-3 | cascor | `feat(network): DELETE /v1/network/hidden-units/{idx} with cascade rebuild (CAN-015h)` | same as h-2 |
| h-4 | canopy | `feat(network-editor): adapter wrappers for the three mutation endpoints (CAN-015h)` | `cascor_service_adapter.py` + adapter tests |
| h-5 | canopy | `feat(network-editor): network editor panel + tab + Investigating-state gating (CAN-015h)` | new component, dashboard wiring |
| h-6 | canopy | `test(network-editor): integration with B-5 confirm modal + Investigating FSM gating` | snapshot panel + new component glue tests |

Order: h-0 → (h-1, h-2, h-3 parallelizable) → h-4 → (h-5, h-6
parallelizable). Total of seven PRs vs. CAN-015g's five — the
mutation-endpoint surface is naturally more granular.

### Risks — CAN-015h

| Risk | Severity | Mitigation |
|---|---|---|
| h-0's "no behaviour change" assertion is wrong | High | Bit-identity test on a fixed-seed 50-epoch run: pre-refactor and post-refactor `network.history["train_loss"]` arrays must be `np.array_equal`. Block merge on diff. |
| Optimizer rebuild after add/remove unit corrupts subsequent training | Med | Round-trip integration test: snapshot → restore → add unit → re-snapshot → resume training → verify training converges. (Won't cover all edge cases but catches the most common regressions.) |
| User patches weights to NaN via float64 → float32 cast | Low | Reject any cast that loses precision (use `np.allclose(orig, cast.astype(orig.dtype), atol=0)`); 422 with explicit message. |
| Topology mutation under concurrent training requests | Low | FSM enforces `Investigating` exclusively — can't reach mutation endpoints from `Started`. Add a unit test that verifies 409 from every other FSM state. |
| Canopy "delete unit" UI is dangerous (no undo) | Med | The B-5 confirmation-modal pattern is reused; the modal text spells out "this cannot be undone without restoring a previous snapshot." Add a "snapshot first?" prompt that, if checked, fires `POST /v1/snapshots` before the DELETE. |
| Insert-at-position semantics surprise users | Med | Default UI to "append at tail" only in V1; insert-at-position is exposed only via a "Show advanced" toggle and the form text explicitly walks through the renumbering rule. Track a docs deliverable for the FAQ. |

---

## Cross-cutting risks

| Risk | Severity | Mitigation |
|---|---|---|
| Sprint B prerequisites (B-3, B-4, B-6) not yet on `main` | **High** | Resolve before kickoff (see "Prerequisite status" §). All PRs in this plan **block** on the prereq branches being on `main`. |
| Schema version bump in CAN-015g breaks existing snapshot fixtures | Med | New `schema_version=2` is backward-compatible (V1 files load fine); existing fixtures stay at V1 and get a `tests/fixtures/snapshots_v2/` sibling. |
| CAN-015g + CAN-015h ship overlapping refactors of the network/serializer | Low | Sequential delivery (g first, then h). h-0 lands before g-1 only if scheduling forces it; refactor is small enough that rebase cost is acceptable either order. |
| Canopy UI tab list keeps growing | Low | The two new tabs ("Network Editor" added by h-5, "Replay" already added by B-6) bring the total to 16. Defer a UI-density refactor to a future sprint; flag with the canopy roadmap maintainer. |

---

## Test plan summary

### CAN-015g

- **g-1**: serializer round-trip — write a 100-epoch toy snapshot
  with `N=10`, read it back, assert sample-epoch list and weight
  tensor shapes match. Schema-version regression: V1 fixture still
  loads.
- **g-1 size assertion**: `du -b` of the round-trip snapshot is
  ≤ 1.5 × V1 size.
- **g-2**: replay session warm/get cache hit/miss counters; LRU
  eviction under a tight budget.
- **g-3**: emitter test — synthetic playback emits a weight payload
  on every sample-boundary epoch and **only** on those.
- **g-4 (canopy)**: replay player updates decision-boundary at
  scrubber moves; weights store stays under 1000 entries.
- **g-6**: capture trigger test — train a 1000-epoch toy run with
  `N=50` and assert `network.weight_history["sample_indices"]`
  matches `[0, 50, 100, ..., 999_terminal]`. Cascade-add trigger
  test — train a run that produces a known cascade-grow event at
  epoch 17 and assert sample 17 is present even though it's
  not on the Nth-epoch grid. Decimation test — run with
  `weight_history_max_samples=10` and `N=1` over 100 epochs;
  assert final sample count ≤ 10 + cascade-add count, and that
  every cascade-add sample is retained. Wall-clock benchmark:
  `N=50` adds ≤ 5% overhead vs. a baseline run with capture
  disabled (`N=0`).
- **End-to-end**: cascor live + canopy headless — start replay
  on a snapshot **produced by g-6 (real training run, not a
  fixture)**, scrub to mid-run, verify decision-boundary frame
  matches a pre-recorded reference plot (image diff with
  tolerance).

### CAN-015h

- **h-0**: bit-identity train pre/post refactor.
- **h-1**: shape mismatch, NaN, dtype-cast, FSM-gate (401 from
  every non-`Investigating` state); successful patch updates the
  optimizer-state zero-out.
- **h-2**: append, full-cascade train, snapshot, restore, append
  again — round-trip and bit-identity of pre-mutation weights.
  `max_hidden_units` 409. Insert-at-position renumbering preserves
  cascade order.
- **h-3**: delete tail, delete middle, delete only unit, delete
  out-of-range. Optimizer rebuild produces a working training run
  on the post-delete network.
- **h-4 (canopy)**: adapter wraps each endpoint; demo-mode 501
  short-circuit (mirrors B-5 pattern).
- **h-5 (canopy)**: panel idle state when FSM≠Investigating; active
  state renders topology + edit forms; modal confirmation flow.
- **h-6**: integration — B-5 modal → Restore → Investigating →
  Network Editor tab loads → mutation succeeds → re-snapshot.

### Coverage gates

Both items target ≥ 80% line coverage on the new files and 100% of
new public endpoints (every status code path exercised). The
existing 80% coverage threshold on cascor and canopy applies to
this work without exception.

---

## Documentation deliverables

- **This doc** — `notes/PHASE_6E_DEFERRED_CAN-015GH_DESIGN.md` (new).
- **`PHASE_6E_SPRINT_B_DESIGN.md`** — update §10 to point to this
  doc as the active design.
- **`PHASE_6E_DESIGN.md`** — replace the deferred line items with a
  reference to this doc.
- **`JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`** —
  add CAN-015g and CAN-015h rows pointing here (parent design noted
  this in §10 was still TODO).
- **cascor `notes/development/`** — CHANGELOG line per PR, plus a
  `SNAPSHOT_SCHEMA_V2.md` once g-1 lands.
- **canopy `notes/development/`** — CHANGELOG line per PR plus a
  user-facing FAQ for the network-editor "delete unit" semantics.

---

## Out of scope (further-deferred)

- **Replay V3**: full per-epoch storage with delta encoding (Option
  B above). Revisit if user research demonstrates that scrubber
  "snap to sample" is unacceptable and Option C subsampling is
  insufficient.
- **Binary WebSocket frames** for weight payloads. Revisit if
  base64 overhead profiles as a bottleneck on multi-MB tensors.
- **Cascade-grow undo**: an explicit undo stack across mutations.
  V1 expects users to snapshot before mutating; an undo stack is a
  product decision, not a technical one.
- **Multi-snapshot diff viewer**: side-by-side comparison of two
  snapshots in canopy. Standalone feature, not gated on either of
  these items.

---

## Glossary

| Term | Meaning |
|---|---|
| **V1 / V2** (Replay) | V1 = metric-only playback (B-3 / B-6, shipped). V2 = metric + weight playback (this doc). |
| **Sample boundary** | An epoch at which the cascor backend persisted weight tensors. Determined by Option C (every cascade-grow event + every Nth epoch). |
| **Investigating FSM state** | The `Investigating` state introduced by B-4 — entered on `/restore`, permits inspection and (with CAN-015h) mutation. |
| **`_install_hidden_unit`** | Private helper extracted by h-0; the single point where new hidden units enter the network's `hidden_units` list. |
| **Schema version 2** | The HDF5 snapshot format that includes `history/weights/`. V1 files (no group) load with `weights_available = false`. |
