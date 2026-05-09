# Multi-Network Architecture — CAS-008 / CAS-009 / CAN-021

**Status**: Design • **Date**: 2026-04-29 • **Sprint**: Phase 6E Sprint E (XL, separate effort)

## TL;DR

Three Phase 6E items share one architectural change: removing cascor's
single-`self.network` assumption so the lifecycle can hold multiple
concurrent networks.

| Item | Description | Bundled with multi-network because |
|---|---|---|
| CAS-008 | Multi-hierarchical CasCor — multiple cascade hierarchies on one network | Each hierarchy is effectively a sub-network; needs the same lifecycle plumbing as multi-network |
| CAS-009 | Population management — train an ensemble of independent networks | Direct ask for the multi-network refactor |
| CAN-021 | Parallel-network ensemble UI view | Pure UI; depends on CAS-009's API to read N networks |

All three are blocked on the same refactor. This doc designs that
refactor.

**Scope**: 7 cross-repo PRs (5 cascor + 2 canopy), with the cascor
side following a registry pattern that wraps each network's
state in a `SingleNetworkLifecycleState` object. The migration is
gradual — the existing `lifecycle.network` API stays as a
"`active_network` shorthand" through the migration so existing tests
and clients keep working until they're explicitly updated.

## Code-surface evidence (verified 2026-04-29)

### The singular assumption

`juniper-cascor/src/api/lifecycle/manager.py:37`:
```python
self.network: Optional[CascadeCorrelationNetwork] = None
```

**74 direct references** across 5 functional categories:

- ~8 sites: network creation/deletion (lines 265, 292, 299, 303, 306–311)
- ~18 sites: monitoring hooks via monkey-patching `self.network.fit`,
  `validate_training`, `grow_network` (lines 326–555)
- ~5 sites: training control (`_run_training` calls
  `self.network.fit()`, lines 689, 744–746, 752)
- ~12 sites: metrics extraction (`_extract_and_record_metrics` reads
  `self.network.history`, `.hidden_units`, lines 580–620)
- ~20 sites: parameters / topology / stats / decision boundary /
  snapshots (lines 823–1057)

### Threading invariants

Four locks tied to "the network":
- `_training_lock` (line 43): protects `create_network`,
  `delete_network`, `start_training`, `update_params` — prevents
  concurrent network swaps during training
- `_metrics_lock` (line 44): protects read-snapshot-then-emit cycle
  (lines 593–624)
- `_topology_lock` (line 45): protects topology / stats / decision
  boundary (lines 916, 943, 976)
- `_broadcast_lock` (line 51): throttles training-state broadcasts
  (lines 232–237)

### Training thread

Single `ThreadPoolExecutor(max_workers=1)` (line 676). One thread per
process. `_run_training()` blocks until `self.network.fit()` returns.

### WebSocket broadcast routing

`juniper-cascor/src/api/websocket/manager.py:432–447`. All broadcasts
go to one global channel per WS endpoint. Replay buffer is global
(`deque(maxlen=1024)`, line 93–94). Messages have no `network_id`
field. State throttle (`_broadcast_lock`) operates on a single
`training_state` object.

### Snapshot storage

`juniper-cascor/src/api/lifecycle/manager.py:1006–1088`. Filename:
`snapshot_{timestamp}.h5` (line 1021). Flat directory layout. No
network identity in filename or metadata.

### Control commands

`juniper-cascor/src/api/websocket/control_stream.py:42`. Six commands
(`start`, `stop`, `pause`, `resume`, `reset`, `set_params`) all dispatch
to `lifecycle` methods with no network-ID parameter. Implicit "the
network".

### State machine

`juniper-cascor/src/api/lifecycle/state_machine.py`. One global
`TrainingStateMachine` instance on `lifecycle.state_machine`
(manager.py:38). With N networks, each needs its own FSM so concurrent
start/stop/pause are independent.

### Canopy adapter

`juniper-canopy/src/backend/cascor_service_adapter.py`. Methods like
`get_topology()`, `set_params()`, `start_training()` have no
`network_id` parameter. The adapter is method-by-method singular —
`get_topology()` returns "the topology", not `get_topology(network_id)`
returning that specific network's topology.

## Design

### Registry pattern, not active-singleton

The cascor refactor introduces:

```python
class SingleNetworkLifecycleState:
    """Wraps one CascadeCorrelationNetwork with its locks, FSM, monitor."""

    def __init__(self, network_id: str, network: CascadeCorrelationNetwork):
        self.network_id = network_id
        self.network = network
        self._training_lock = threading.Lock()
        self._metrics_lock = threading.Lock()
        self._topology_lock = threading.Lock()
        self.state_machine = TrainingStateMachine()
        self.training_monitor = TrainingMonitor(...)
        # ... per-network thread, history, etc.
```

`TrainingLifecycleManager` becomes a router:

```python
class TrainingLifecycleManager:
    def __init__(self):
        self._networks: Dict[str, SingleNetworkLifecycleState] = {}
        self._active_network_id: Optional[str] = None  # back-compat shim
        self._registry_lock = threading.Lock()  # protects _networks dict
        self._broadcast_lock = threading.Lock()  # global broadcast throttle stays

    @property
    def network(self) -> Optional[CascadeCorrelationNetwork]:
        """Back-compat shorthand — returns the active network or None."""
        if self._active_network_id is None:
            return None
        return self._networks[self._active_network_id].network

    def create_network(self, network_id: str = "default", **kwargs) -> Dict:
        ...
```

**Why registry over active-singleton-with-switching**:

- 74 singular sites collapse cleanly into per-network methods on
  `SingleNetworkLifecycleState`. The manager itself becomes a thin
  router.
- Active-singleton-with-switching keeps the monolithic manager but
  adds racy switching semantics. Every method becomes "load the
  active network at start, hope nobody switches mid-call" — death by
  a thousand TOCTOU bugs.
- Registry pattern makes the `network_id` param explicit at the API
  boundary, which matches how REST endpoints will route it.

### Migration without breaking existing clients

The `lifecycle.network` property stays as back-compat — returns the
"active" network's reference, where active is the most-recently-
operated-on network (or "default" if only one exists). All existing
tests that use `lifecycle.network` keep working through the migration.

The `_active_network_id` shim is removed in the final canopy-side PR
once both ends speak the new `network_id` API.

### Per-network threading vs. shared training thread

**Decision**: per-network training thread.

- `SingleNetworkLifecycleState` owns its own `ThreadPoolExecutor(max_workers=1)`.
- Two networks can train concurrently — one per thread.
- Total active threads bounded by: `N_networks * 1` (training) +
  candidate-pool threads (already pooled internally per network).
- Memory bound: each network owns its tensors; no shared state to
  guard.

Risk: if a user creates 50 networks and starts training on all of
them, that's 50 training threads + each their own candidate pool
(currently up to 8 workers each). At absolute worst case, 450 threads
on one machine. Mitigation: a `max_concurrent_training_networks: int = 4`
config knob. Default 4; users can raise it on big machines.

### WebSocket message routing

**Decision**: per-message `network_id` field, not per-channel.

```json
{
  "type": "metrics",
  "network_id": "default",
  "data": {...},
  "seq": 42,
  "emitted_at_monotonic": ...
}
```

All current broadcast types (`metrics`, `state`, `topology`,
`cascade_add`, `candidate_progress`, `event`) get a `network_id`
field. Clients filter locally if they want to follow a specific
network; default behavior is "show all networks" with the dashboard
displaying the network ID alongside each event.

**Why message-level filtering, not channel-level**:

- Single replay buffer — no per-network buffer state to maintain.
  When a client reconnects, they replay from `seq > last_seq` and get
  ALL networks' events; filter clientside.
- Existing replay protocol (GAP-WS-13) keeps working unchanged.
- Channel-based routing would require new connect-time parameters
  and per-channel buffers — adds protocol surface for marginal benefit.

Per-message overhead: one short string field (~30 bytes per message).
Negligible vs. the typical metrics payload (~500 bytes).

### Snapshot storage layout

```
src/snapshots/
  default/                            (= network_id)
    snapshot_2026-04-29T10:00:00Z.h5
    snapshot_2026-04-29T10:05:00Z.h5
  experiment-2/
    snapshot_2026-04-29T10:01:00Z.h5
```

One subdirectory per network; same filename pattern within. Snapshot
metadata (already inside the HDF5 file) gains a `network_id` field
for sanity-check on load.

Migration: existing flat-layout snapshots get auto-moved to a
`default/` subdirectory on first startup of the new code. One-time
migration script + idempotent (skips if already migrated).

### State machine — per-network FSM

Each `SingleNetworkLifecycleState` owns its own
`TrainingStateMachine`. The global `lifecycle.state_machine` becomes
a back-compat shim returning the active network's FSM.

A user can have one network paused while another is training. The
existing FSM stays unchanged — we just give each network its own
copy.

### REST API surface

New routes:

```
POST   /v1/networks                           (create)
GET    /v1/networks                           (list)
GET    /v1/networks/{network_id}              (info)
DELETE /v1/networks/{network_id}              (delete)

POST   /v1/networks/{network_id}/training/start
POST   /v1/networks/{network_id}/training/stop
POST   /v1/networks/{network_id}/training/pause
POST   /v1/networks/{network_id}/training/resume
PATCH  /v1/networks/{network_id}/params

GET    /v1/networks/{network_id}/topology
GET    /v1/networks/{network_id}/metrics
GET    /v1/networks/{network_id}/network/stats

POST   /v1/networks/{network_id}/snapshots
GET    /v1/networks/{network_id}/snapshots
GET    /v1/networks/{network_id}/snapshots/{snapshot_id}
```

Existing routes (`POST /v1/network`, `GET /v1/network/topology`,
etc.) stay as **back-compat aliases** — they target the active
network. Deprecated but functional. Removed in a follow-up PR after
canopy fully migrates.

### Control WebSocket commands

Each command grows an optional `network_id` field:

```json
{
  "type": "command",
  "command": "start",
  "command_id": "uuid",
  "network_id": "experiment-2",
  "params": {}
}
```

When `network_id` is omitted, target the active network (back-compat).

### Canopy adapter changes

`CascorServiceAdapter` gains `network_id` as a constructor
parameter or per-method optional override:

```python
class CascorServiceAdapter:
    def __init__(self, client, default_network_id: str = "default"):
        self._client = client
        self._network_id = default_network_id

    def get_topology(self, network_id: Optional[str] = None) -> Dict:
        nid = network_id or self._network_id
        return self._client.get(f"/v1/networks/{nid}/topology")
```

Backward-compat: methods called without `network_id` use the
adapter's `default_network_id`.

### Canopy UI

A new "Networks" sidebar section lists all networks with status
indicators (running / stopped / error). Selecting one switches the
adapter's `_network_id`. Status bar shows the active network ID.

CAN-021's "Population" tab becomes a grid of mini network views,
one per network — built on top of the existing Network Evolution
component (which already does small-multiples). The Population tab
is "small multiples across networks", Network Evolution stays
"small multiples across time for one network".

## PR plan (Sprint E)

| # | PR | Repo | Scope | Notes |
|---|---|---|---|---|
| E-1 | `SingleNetworkLifecycleState` extraction + manager registry | cascor | **L** | The big one. Refactors the 74 singular sites into per-network methods. Adds back-compat `network` shim. ~600–800 LoC. |
| E-2 | New `/v1/networks/*` REST routes + back-compat aliases | cascor | M | Adds the URL surface. Existing routes stay as aliases pointing to `_active_network_id`. |
| E-3 | Control WS: `network_id` in commands; broadcast: `network_id` in messages | cascor | M | Protocol change. Clients without `network_id` keep working (active-network default). |
| E-4 | Snapshot storage layout migration | cascor | S–M | One-time migration of flat layout to per-network subdirs. Idempotent. |
| E-5 | Per-network training thread + max-concurrent config | cascor | S | Each `SingleNetworkLifecycleState` owns its `ThreadPoolExecutor(1)`. New `max_concurrent_training_networks` setting. |
| E-6 | Canopy adapter: `network_id` parameter threading | canopy | M | Adapter methods grow `network_id`; falls back to a per-instance default. Tests update accordingly. |
| E-7 | Canopy UI: Networks sidebar + Population tab | canopy | M–L | New sidebar list with switcher; new "Population" tab (CAN-021). Reuses Network Evolution's small-multiples renderer. |

7 PRs. Cascor-side ordering matters (E-1 → E-2 → E-3 → E-4/E-5).
Canopy E-6 and E-7 are sequential; both depend on cascor side.

Total estimate: **~2 weeks of focused work** plus review cycles.
This is the "real XL" item in Phase 6E.

## Migration strategy

The "active network" back-compat shim is critical. Here's the
expected user-visible state through the rollout:

| After PR | Cascor behavior | Canopy behavior |
|---|---|---|
| E-1 merged | Internally registry; `lifecycle.network` shim still works | Unchanged (still uses old API) |
| E-2 merged | New `/v1/networks/*` routes available; old routes alias to active network | Unchanged |
| E-3 merged | WS messages carry `network_id`; commands accept optional `network_id` | Unchanged (clients ignore the new field) |
| E-4 merged | Snapshots in per-network subdirs; existing snapshots auto-migrated to `default/` | Unchanged |
| E-5 merged | Per-network training thread; cap configurable | Unchanged |
| E-6 merged | — | Adapter aware of `network_id`; default falls back to "default" |
| E-7 merged | — | Networks sidebar + Population tab visible |

After E-7, all existing single-network workflows still work
identically (everything defaults to network_id="default"). New
multi-network workflows are opt-in.

## Tests

Each cascor PR carries ~150–300 lines of new tests. Highlights:

- **E-1**: registry CRUD; back-compat — `lifecycle.network` returns
  active network's reference; concurrent network creation under
  `_registry_lock`; per-network state isolation (training one network
  doesn't update another's metrics).
- **E-2**: REST route round-trips; alias routes return same data as
  ID'd routes for the active network.
- **E-3**: broadcast messages carry `network_id`; client filtering
  works; replay protocol still hands out broadcasts in monotonic seq
  order across all networks.
- **E-4**: snapshot save/load round-trips per network; auto-migration
  is idempotent and detects already-migrated state.
- **E-5**: two networks training concurrently produce independent
  metrics streams; `max_concurrent_training_networks` enforces the
  cap.
- **E-6/E-7**: source-level invariants (matching the pattern from
  CAN-016b, CAN-019, CAN-020 PRs).

## Risks

1. **Thread explosion**: if a user creates many networks and starts
   training on all of them, candidate pools could spawn hundreds of
   workers. Mitigation in E-5; verify with stress test.
2. **WS message size growth**: every broadcast gains a `network_id`
   string. Negligible per-message but adds up. GAP-WS-18's chunking
   handles oversized broadcasts already.
3. **Snapshot migration edge cases**: power-loss mid-migration could
   leave the directory half-flat / half-nested. Migration must be
   idempotent and check both states. Tests cover.
4. **Active-network race conditions**: the back-compat
   `lifecycle.network` property reads `_active_network_id` without a
   lock. Two callers might disagree about which network is active.
   Mitigation: deprecate the shim quickly (in E-6/E-7) so it doesn't
   become a permanent hazard.
5. **Canopy state-machine assumptions**: the dashboard probably has
   places that bake in "the FSM" (training_state buffer, etc.). Each
   has to be audited as part of E-6/E-7.

## Out of scope

- **Multi-process scaling** (one network per process, multiple
   processes orchestrated by a parent): different architectural
   decision; this design is multi-network in one process. Could come
   later if N gets large enough.
- **Cross-network parameter sharing** (e.g., transfer learning, hot
   start a new network from another's snapshot): orthogonal feature.
   Could land after this design is proven.
- **Network templates** (pre-configured `TrainingParams` bundles
   keyed by template name): could simplify the "create N networks
   from a template" workflow but isn't required for the architectural
   refactor.

## Decision points for the user

1. **Default `max_concurrent_training_networks`** — 4 is the doc's
   default. Reasonable alternatives: 1 (preserves current behavior
   strictly), 2 (small parallelism without thread explosion). My
   lean: 4 — most users won't notice; power users get parallelism.
2. **REST route deprecation timeline** — back-compat aliases stay
   forever, removed in N minor versions, or removed once canopy
   migrates? My lean: removed once canopy migrates (= when E-6 lands)
   to keep one source of truth.
3. **Sprint E sequencing** — all 7 PRs in one sprint, or split
   E-1/E-2/E-3 (foundation) into Sprint E1 and E-4/E-5/E-6/E-7
   (migration + UI) into Sprint E2? My lean: split. The first three
   are the hard part; the rest can land at a calmer pace once the
   foundation proves stable.
