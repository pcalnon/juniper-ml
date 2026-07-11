# Canopy Training-Runtime Defects — Diagnosis and Fix Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: juniper-canopy (primary), juniper-cascor, juniper-data, juniper-cascor-client, juniper-data-client
**Author**: Paul Calnon (investigation by Claude Code)
**Date**: 2026-07-11
**Status**: Diagnosed against the live 2026-07-10/11 session; validated by a three-lens multi-agent pass (§11); fix roadmap proposed (owner-gated)
**Driving prompt**: `prompts/generated/JUNIPER_CANOPY_TRAINING-RUNTIME-DEFECTS_PLAN_2026-07-11_0842.md`
**Prior work**: `notes/JUNIPER_2026-07-09_JUNIPER-ECOSYSTEM_TRAINING-START-FAILURE-DIAGNOSIS-AND-FIX-PLAN.md` (training start now works; these defects were shadowed behind it)

---

## 1. Executive Summary

Training now starts, runs, and completes from the Canopy dashboard — six runs completed in the observed session (2026-07-10 18:15 → 2026-07-11 06:40).
But the dashboard is effectively **blind and mute while it happens**: live tiles freeze at stale values, the topology graph goes stale, controls give no feedback (three dataset cold-swaps trained to completion **invisibly** while the operator concluded they had failed), and the errors that are surfaced hide their cause.
Seven issues (I-1 – I-7) were diagnosed with code anchors, live-stack probes, and a full log sweep, then hardened by a three-lens validation (§11) that overturned four early conclusions. The load-bearing findings:

1. **Staleness is a starved-fallback design plus an undetected-dead-socket problem.**
   The browser-side `metricsReceived` flag is sticky (set once, never reset — `ws_dash_bridge.js:52-65`) and gates off the REST metrics poll (`dashboard_manager.py:5201`).
   The flag-setting `initial_metrics` frame is broadcast once per **relay** connect (cascor `training_stream.py:59-77`) — so long-lived tabs that saw it stop polling forever, while the WS path writes charts only (never tiles) and delivered no per-epoch metrics in this session.
   A refreshed tab never receives `initial_metrics`, keeps polling at 1 Hz, and shows fresh data — exactly the observed "refresh fixes it".
   Separately, cascor closed canopy's control WS 40 s after connect (`heartbeat timeout`, 18:17:03) — cascor pings every 30 s with a 10 s pong window (`control_stream.py:22-24`, `:251`) and the cascor-client WS layer implements no ping/pong handling — and canopy's supervisor (`is_connected` ⇔ `_ws is not None`) cannot see a half-open socket, so it never reconnected in 12+ hours.
2. **The "Failed to apply (502)" is real rejection caused by cascor's own incoherent bounds, with the reason hidden.**
   Cascor's model default `epochs_max = 100000000000` (`constants_model.py:206`, config default `cascade_correlation_config.py:148`) exceeds cascor's own PATCH validation ceiling (`le=1_000_000`, `api/models/training.py:54`, `:218`).
   Canopy echoes the backend value into the form on load (`init_params_from_backend`, `dashboard_manager.py:5871-5875`), so every full-form apply is wholesale-rejected 422 — and the toast discards the reason (`dashboard_manager.py:5833`).
   Canopy's own default is fine (1e6 — `settings.py:111`, `canopy_constants.py:45`); 1e11 is the field max (`canopy_constants.py:44`) and cascor's echoed default.
   No Apply-button change reached cascor all session; the impression that "parameter updates work" traces to values echoed back from cascor and engine-internal defaults, not to applied operator input (validated §11, Lens 2 #4).
3. **Snapshot creation failed on a one-field validation bug at canopy's route seam, not concurrency.**
   The panel correctly omits a blank description (`hdf5_snapshots_panel.py:400-404`), but canopy's route defaults it to `None` (`description: str = None`, `main.py:1997-1998`) and forwards it (`:2078`) → the client posts `{"description": null}` → cascor 422s (its `description: str = ""` accepts omission but not explicit null, `snapshots.py:42-45`).
   Canopy then flattens the detail into the doubled toast (`main.py:2147-2152` + panel prefix `:841-845`). The `headers=internal_api_headers()`-inside-a-comment defect (`:409`) is real but latent (auth was off).
4. **"Stop & Restart with new dataset" gives zero feedback — its idle-time restarts actually worked.**
   All three cold-swaps (xor 05:10, moons 05:19, circles 05:28) returned 200 end-to-end and cascor trained each (~5 min, `Starting main training loop` 05:10:39/05:19:06/05:28:20) — invisible on the frozen dashboard, so they read as silent failures.
   The callback's only Output is the banner; every failure path is log-only (`dashboard_manager.py:4214-4218`); no stop step exists despite the button's name; `reset=true` is accepted and dropped (`service_backend.py:105`, `:116`). Behavior during an *active* run is untested (E-2).
5. **MNIST cannot work as shipped**: `MnistGenerator.generate` raised `ImportError: Hugging Face datasets package not installed` 71 times (05:48:54–06:23:23) —
   the `datasets` package is absent from juniper-data's entire dependency surface and from the live `JuniperData` conda env (verified by import check).
   The rest of the MNIST path (staging, translation, NPZ contract, 784×10 network auto-creation) is intact.

The fix roadmap (§7) is dependency-ordered (juniper-data → cascor → cascor-client → canopy) in PR-sized units.
Independent quick wins: **N4** (snapshot route-seam + headers one-liners) and **D1** (actionable generator errors).

## 2. Reported Symptoms

Operator report of 2026-07-11 (dashboard screenshots ~04:58–06:23), against the on-host stack launched 2026-07-10 18:15:

| #   | Symptom                                                                                                                                                                  | Issue            |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| S1  | Training launches and completes successfully (context — prior round's fixes hold; 6 completed runs this session)                                                         | —                |
| S2  | Page not refreshed to reflect ongoing training progress                                                                                                                  | I-1              |
| S3  | Numerous fields, metrics, and status indicators stale (Loss tile 0.2337 vs 0.0186 shown after refresh; Accuracy `--`)                                                    | I-1              |
| S4  | Network Topology graph not updated in real time; goes stale as units are added                                                                                           | I-2              |
| S5  | Decision Boundary plot DOES update (contrast case — driven by tab-activation/slider Inputs and an un-gated poll)                                                         | I-1/I-2 evidence |
| S6  | Manual page refresh restores correct values (fresh tabs never receive the flag-setting frame and keep polling)                                                           | I-1 evidence     |
| S7  | Apply Parameters shows `Failed to apply (502)` though "parameter updates appear to be working"                                                                           | I-4              |
| S8  | Dataset switching "appears to work" for 2-D sets — confirmed: idle-time swaps genuinely trained (invisibly)                                                              | I-6 evidence     |
| S9  | MNIST start fails: `Start failed. HTTP 409: … juniper-data fetch failed: Request failed (500): Internal server error.`                                                   | I-5              |
| S10 | `Stop & Restart with new dataset` fails silently — zero feedback by construction; MNIST-era failures logged but never shown                                              | I-6              |
| S11 | Snapshot create fails: `Failed to create snapshot: Failed to create snapshot`                                                                                            | I-3              |
| S12 | Header/tile semantics oddities: `Epoch: 10000` vs `12`; Hidden Units denominator `10000`; `Iteration: 0 / 10000`; spiral params under Type=MNIST; `2-D models only` hint | I-1c, I-7        |

## 3. Architecture Context

Two independent update paths feed the dashboard (anchors line-verified at canopy `f49a04ac`, cascor `2926245c`, data `fdbe0de1`, data-client `9a6453f2`, cascor-client `292c520c`):

- **Path A — REST self-polls**: Dash callbacks on `fast-update-interval` (1000 ms) / `slow-update-interval` (5000 ms) (`src/frontend/dashboard_manager.py:1696-1697`) → canopy FastAPI routes → live cascor REST.
  The header (`update_unified_status_bar`, `dashboard_manager.py:2676-2693` → `/api/status` → `src/main.py:1197-1204`) polls un-gated;
  the Decision Boundary tab (`update_boundary_store`, `dashboard_manager.py:3279-3289` → `/api/decision_boundary`, `src/main.py:1586-1599`) polls un-gated **and** refreshes on tab-activation/slider Inputs — why it stayed live (S5).
- **Path B — WS chain**: cascor `/ws/training` → canopy relay (`start_metrics_relay`/`_relay_loop`, `src/backend/cascor_service_adapter.py:324-518`) → `websocket_manager.broadcast` (`:411`)
  → browser `/ws/training` (`src/main.py:612-727`; sends `initial_status` + `state` on mount, `:687`, `:692` — **not** `initial_metrics`) → `ws_dash_bridge.js` ring buffers → per-tick drains into stores (`dashboard_manager.py:2942-3017`).
  `initial_metrics` originates from **cascor's** stream once per relay connect (cascor `src/api/websocket/training_stream.py:59-77`) and reaches only the tabs connected at that moment.
- **The Phase-B gates**: the metrics-store poll returns `dash.no_update` when `ws_bridge_enabled AND connected AND metricsReceived` (`dashboard_manager.py:5201`); topology likewise via `topologyReceived` (`:3232-3234`).
  The flags are sticky — set on the first metrics/`initial_metrics`/topology frame, never reset (`src/frontend/assets/ws_dash_bridge.js:52-65`, setters `:217`/`:235`/`:262`).
- **Path B writes no tiles**: the only `ws-metrics-buffer` consumer extends chart traces (`src/frontend/components/metrics_panel.py:728-829`);
  the tiles' sole writer is `update_metrics_display` (`metrics_panel.py:671-694`) fed by the gated store. `ws-state-buffer` and `ws-candidate-progress-buffer` have no consumers at all.
- **`/api/state`** (`src/main.py:1107-1194`) is a hybrid: in service mode it live-fetches the nn_/cn_ parameter keys from cascor on every GET (`get_canopy_params()`, `main.py:1190`; adapter `:1154-1170`),
  but the **base fields** (status/phase/current_epoch/timestamp) come only from the in-process `training_state` global, whose sole recurring writer is the relay's state callback (registered `src/main.py:204`).
  The metrics-panel strip/learning-rate/duration/progress read it via `fetch_training_state` (`metrics_panel.py:561-567`).
- **Control plane**: Apply Parameters → `/api/set_params` (`api_set_params`, `src/main.py:3357`) → adapter `apply_params` (`cascor_service_adapter.py:769`),
  WS-first (`_apply_params_hot` `:1124`, 1.0 s ack window `:1139-1152`) then REST `PATCH /v1/training/params`; any `ok: False` → canopy 502 (`main.py:3458-3468`).
  Restart-with-dataset → `restart_with_new_dataset` (`dashboard_manager.py:4187-4218`).
  Snapshots → panel `_create_snapshot_handler` (`src/frontend/components/hdf5_snapshots_panel.py:388`) → `POST /api/v1/snapshots` (`src/main.py:1995`) → cascor `POST /v1/snapshots` (`src/api/routes/snapshots.py:129-141`).

Evidence base for §4: (a) the code anchors above; (b) read-only live probes of 2026-07-11
(cascor `/v1/training/status`, `/v1/network`, `/v1/metrics`, `/v1/network/topology`, `/v1/training/dataset/pending`; canopy `/api/status`, `/api/state`, `/api/metrics/history`; data `/v1/health`);
(c) full log sweep of the session logs `juniper-canopy_2026-07-10_1815.log` (13k lines), `juniper-cascor_2026-07-10_1815.log` + `juniper_cascor.log` (596/622 MB), `juniper-data_2026-07-10_1815.log` (41k lines), `system.log`;
(d) the three-lens validation pass (§11), whose corrections are incorporated throughout.

**Session timeline (log-verified).** Stack up 18:15-18:16; relay + control WS connect 18:16:23; control WS closed by cascor 18:17:03 (never re-established).
Six training runs (`Starting main training loop`): 18:21:13, 19:00:00, 05:10:39, 05:19:06, 05:28:20, 05:39:17; completions 19:49:14, 05:15:33, 05:24:11, 05:33:48, 05:43:59 (early-stopped).
Snapshot-create failures 04:59:58–05:25:21; Apply-Parameters 422/502s 18:52–06:40 (59 lines); MNIST attempts with 71 juniper-data ImportError 500s 05:48:54–06:23:23.
Cascor's uvicorn access log went silent after 18:19:56, and both cascor logs end at 05:43:59.

## 4. Per-Issue Diagnosis & Fix Design

### I-1 — Header + Training Metrics staleness during a live run

**Symptom.** S2/S3/S6/S12: tiles and header froze at stale values while the WS badge showed `Connected`; a manual refresh showed correct values.

**Evidence.**

- Browser→server traffic 04:30–06:30 (system.log): only `Received message: pong` (239×). Server→client broadcasts are not logged, so "no metrics frames delivered" is inference from the frozen UI plus the relay's input being heartbeat-only (next bullet).
- The relay socket received one unrecognized frame per ~30 s all session (mirrored warning pairs: `juniper_cascor_client_unrecognized_ws_frame` + `juniper_canopy_unrecognized_ws_frame`, ~2,42x each at authoring cutoff;
  cadence matches cascor's 30 s ping interval, and the cascor-client WS layer implements no ping/pong handling), with no relay lifecycle logging after the single 18:16:22 `Metrics relay started`.
- Live probe: canopy `/api/state` base-field timestamp `1783768946` vs cascor `/v1/metrics` timestamp `1783797687` — the relay-fed state was **28,741 s (~8 h) stale** with `current_epoch: 0`,
  while cascor's REST reported epoch 20 / 14 hidden units / loss 0.0307 in the same minute. `/api/status` (un-gated proxy) served fresh values on probe.
- `/api/metrics/history?limit=2` returned `{"history": []}` post-run and cascor's monitor reported `total_metrics: 0` — cascor clears metrics on reset/retrain (`manager.py:2142`, `:4042`), so the REST history fallback can be empty after completion (Q4; N1 empty-guard).
- Display semantics (S12): cascor's surfaces disagree — `/v1/network` says `max_hidden_units: 6, learning_rate: 0.08` while `/v1/training/status` says `max_hidden_units: 10000, learning_rate: 0.01` —
  two independent default sets (engine-config layer, e.g. `create_simple_config(learning_rate=0.1, max_hidden_units=10)` `cascade_correlation_config.py:333`, vs lifecycle/API layer `constants_api_defaults.py`), not applied parameters (Lens 2 #4).
  The Hidden-Units tile denominator `10000` faithfully displays `training_state.max_hidden_units`. The header `Completed — early stopped / Epoch: 12` seen after refresh (~05:06) was **truthful** (run 2 completed 19:49:14; cascor idle at that moment).
  The pre-refresh tab (img of 04:58) showing `Running / Epoch 10000 / Phase Duration 894m` while cascor was idle is an artifact of the frozen tab, not of `/api/status` (which was fresh on probe) — mechanism OPEN, see root cause 4 and E-3.

**Root cause** (four cooperating defects):

1. **Sticky-gate starvation of long-lived tabs (confirmed, mechanism corrected in validation).** `initial_metrics` is broadcast once per relay connect (18:16:22) to the tabs connected at that moment; any metrics-class frame sets the sticky `metricsReceived` (`ws_dash_bridge.js:217`/`:235`).
   Once set, the gate (`dashboard_manager.py:5201`) suppresses that tab's metrics-store poll indefinitely — even when no further frames ever arrive.
   A refreshed tab never receives `initial_metrics` (canopy's browser mount sends only `initial_status`+`state`, `main.py:687`/`:692`), keeps `metricsReceived=false`, and polls at 1 Hz — which is why refresh restores liveness.
2. **No tile writer on Path B (confirmed by construction).** Even a healthy WS never updates the tiles or the `/api/state` base fields beyond charts.
3. **Path B delivered no per-epoch metrics (confirmed effect; emission point OPEN).** The relay's input was heartbeat-shaped only; whether cascor's `/ws/training` emitted no per-epoch metrics or the client dropped them unlogged is undecidable from these logs (no throughput logging; warnings omit `msg_type`) — experiment E-1.
4. **The pre-refresh tab's TOTAL freeze (header included) has an additional, unidentified mechanism (OPEN).** The header poll is un-gated, yet the 04:58 tab showed stale header values.
   Candidates: the `apply-in-flight` interval clamp (`dashboard_manager.py:2761-2798`) stuck after the evening's failed applies, or browser background-tab timer throttling.
   The earlier refutation of the clamp ("decision boundary kept polling") does not hold — the boundary also refreshes on tab-activation/slider Inputs, which fire on a clamped tab. Experiment E-3.

Refuted from the prompt's candidate list: circuit-breaker pinning and "cascor status not advancing" (fresh `/api/status`/REST probes). The interval clamp is **reopened** as a candidate for root cause 4 only.

**Options & trade-offs** (update-path posture — the architectural decision the prompt mandates):

- **O1 — Liveness gate**: replace sticky flags with a freshness window; poll auto-resumes when WS goes quiet. Keeps Phase-B's savings; adds JS freshness bookkeeping and a predicate to test.
- **O2 — Un-gate the polls**: tiles/figures depend on the store; treat WS as latency polish. Simplest correct fix; restores ~1 req/s (verified `FAST_UPDATE_INTERVAL_MS=1000`) — the Decision Boundary already does this; topology adds ~0.2 req/s only while its tab is open (5 s slow interval + tab gating).
- **O3 — Make Path B write tiles/state**: real-time UX, but doubles write paths and depends on Path B actually delivering (root cause 3 unresolved).
- **O4 — Flip the kill switch** (`JUNIPER_CANOPY_DISABLE_WS_BRIDGE=true` default): blunt; forfeits WS gains and hides the WS defects.

**Chosen design.** O2 for **both** metrics and topology (one mechanism, less machinery — validation §11 skeptic #4; the topology poll stays tab-gated on the slow interval, and tab-activation refetch already exists via its `active_tab` Input once the gate is gone).
Guard rails required by validation (§11 skeptic #1, #6): the store poll must return `no_update` (not `[]`) when the fetch is empty/errored and the store already holds data — today `_update_metrics_store_handler` returns `[]` on empty/error (`dashboard_manager.py:5215`, `:5257`) and an un-gated 1 Hz poll would otherwise wipe a completed run's charts (cascor clears metrics post-run);
the upstream call inside `async def get_metrics_history` (`main.py:1217-1227`) must move to a thread (`asyncio.to_thread`) so a slow cascor cannot stall canopy's event loop; and full-history display modes must bound their fetch (today `limit=0` fetches up to 10k rows per tick, `:5207-5210`).
Path-B trustworthiness is the N2/C3/CL1 workstream: supervised reconnect with logging, half-open detection (the supervisor's `is_connected` is `_ws is not None`, `cascor_service_adapter.py:99-100` — blind to dead sockets), client ping/pong handling, `/api/state` made live-first for base fields (§11 skeptic #5: it already pays a live cascor call per GET — derive status/epoch from that same fetch, keep the relay-fed global for demo mode and WS push granularity), and a degraded-mode indicator.
Dead-end stores removed or wired when O3 lands. Header semantics fixed in N6 with C2b's surface reconciliation. E-3 resolves root cause 4 before N2 is finalized.

**Tests.** Unit: store-poll un-gating + empty-guard (`no_update` on empty fetch with non-empty store); to_thread wrapping. UI harness (canopy `src/tests/ui/`): WS-silent scenario — tiles advance via poll within 2 s on a long-lived tab; post-completion charts persist under the 1 Hz poll; header matches a scripted cascor status.

### I-2 — Network Topology staleness

**Symptom.** S4: the topology graph froze as hidden units were added.

**Evidence.** Same session evidence as I-1 (heartbeat-only relay input; sticky `topologyReceived`); topology WS pushes originate only from the relay's `cascade_add` hook (`cascor_service_adapter.py:414-418`);
the REST fallback poll is gated by the sticky flag and tab-activation (`dashboard_manager.py:3232-3234`, handler `:5259-5283`).

**Root cause.** Same starvation class as I-1(1): with `cascade_add` frames never arriving and the sticky flag set, neither push nor poll updates the store. The defect is that the fallback never engages when pushes stop.

**Chosen design.** O2: delete the `topologyReceived` gate (the poll remains tab-gated on the 5 s interval; `active_tab` Input already refetches on tab switch), keep `cascade_add` push as the fast path. Weight-heatmap raw store is already un-gated (`dashboard_manager.py:3242-3261`).

**Tests.** UI harness: with WS quiet, topology store refreshes on the slow interval and on tab switch.

### I-3 — Create Snapshot fails during a run

**Symptom.** S11: doubled toast `Failed to create snapshot: Failed to create snapshot`; empty snapshot list.

**Evidence.** Canopy log 04:59:58.893 (and 05:00:12, 05:00:14, 05:05:54, 05:25:21):
`Failed to save snapshot: [{'type': 'string_type', 'loc': ['body', 'description'], 'msg': 'Input should be a valid string', 'input': None}]` — a cascor request-validation rejection: the request **reached cascor** and died at body validation.
The doubled toast is canopy's own 500 detail `"Failed to create snapshot"` (`src/main.py:2147-2152`) wrapped by the panel prefix (`hdf5_snapshots_panel.py:841-845`).

**Root cause (confirmed; seam corrected in validation).** The panel omits a blank description (`if description:` — `hdf5_snapshots_panel.py:400-404`), but canopy's **route** defaults the query param to `None` (`description: str = None`, `main.py:1997-1998`) and forwards it (`main.py:2078`),
so the cascor-client posts `{"description": null}` (`client.py:295`); cascor's `SnapshotCreateRequest.description: str = ""` (`snapshots.py:42-45`) accepts omission but 422s explicit null.
**Refuted for this incident**: the concurrent-HDF5-write hypothesis (no serializer error; training's own periodic saves continued) and the missing-headers hypothesis as trigger (request reached cascor; auth off).
Both remain **latent, code-verified defects**: `headers=internal_api_headers()` trapped in a trailing comment (`hdf5_snapshots_panel.py:409`; siblings live at `:464`/`:491`/`:557`/`:608`) bites the moment API-key auth or rate limiting is active;
the serializer swallows any exception into `False` (`snapshot_serializer.py:158-160`) → lifecycle `None` (`manager.py:3877-3880`) → cascor 404 (`snapshots.py:140-141`), with no lock isolating `_save_training_history` (`snapshot_serializer.py:631-641`) from the training thread.

**Chosen design.** Canopy N4 (independent quick win — cascor already accepts omission): fix the route/adapter seam — default the route param to `""` or omit `None` before the client call (`main.py:1998`/`:2078`), restore the commented-out headers kwarg (one line), and propagate upstream error detail into the toast.
Cascor C1 (robustness, not a gate for N4): accept `Optional[str]` explicitly, propagate serializer failure detail instead of blanket `None`→404 (correct status + reason), and harden snapshot-vs-training write isolation (serialize from a consistent view).

**Tests.** Canopy: blank-description create sends no `null` (regression at the route seam); create POST carries internal headers; toast includes upstream detail. Cascor: explicit-null tolerated post-C1; create failure carries reason.

### I-4 — Apply Parameters shows `Failed to apply (502)` yet parameters "appear to apply"

**Symptom.** S7.

**Evidence.** Every logged Apply follows one pattern (e.g. 05:10:01.416–.432):
`WS set_params failed (ConnectionClosedError: sent 1011 (internal error) keepalive ping timeout; no close frame received), will use REST fallback` →
`Failed to update cascor params via REST: [{'type': 'less_than_equal', 'loc': ['body', 'epochs_max'], … 'input': 100000000000, 'ctx': {'le': 1000000}}]` →
`Failed to apply: 502 …`. 59 such lines across 18:52–06:40.
No `verification_failed` and no partial-success lines exist anywhere in the session log. The control WS died at 18:17:03 and was never re-established — every WS attempt hit the same half-open socket.

**Root cause (confirmed; attribution corrected in validation).**

1. **Cascor-internal bound incoherence, echoed by canopy**: cascor's model default `epochs_max = 100000000000` (`constants_model.py:206`; config default `cascade_correlation_config.py:148`) exceeds cascor's own PATCH ceiling (`le=1_000_000`, `api/models/training.py:54`/`:218`) —
   the start path accepts the default unvalidated (live `training_state` holds `max_epochs: 1e11`), `GET /v1/training/params` echoes it (`manager.py:3031`), and canopy seeds the form from the backend (`init_params_from_backend`, `dashboard_manager.py:5871-5875`, Output `:4070`).
   Every full-form apply (`dashboard_manager.py:3961-3997`; `nn_max_total_epochs → epochs_max`, adapter `:659`) is therefore wholesale-rejected 422 at request-model validation — cascor applied nothing.
   Canopy's own default is compliant (1e6); "lower canopy's default" would NOT fix this, because the form is re-seeded from cascor on every load (Lens 2 #3).
2. **Reason hidden**: the toast is built at `dashboard_manager.py:5833` and discards `response.text` (logged only, `:5832`).
3. **Dead control WS + blind supervisor**: cascor pings every 30 s and closes after a 10 s pong window (`control_stream.py:22-24`, `:251`); the cascor-client WS layer has no ping/pong handling, so the socket died at 18:17:03;
   the supervisor's `is_connected` (`_ws is not None`) cannot detect it, so every apply burned the 1.0 s WS window before falling back to REST.
4. **"Parameters appear to apply" is an echo, not an apply** (Lens 2 #4): start/restart payloads carry no parameters (bare `?reset=true` → empty body; `routes/training.py:73-77` forwards `body.params` only if present),
   and the divergent live values (`learning_rate 0.08` / `max_hidden_units 6` on the network object vs `0.01`/`10000` on training_state) are two independent engine default layers — no operator value landed this session.
5. The prompt's two "applied-yet-red" paths — `_verify_apply_roundtrip` divergence (`cascor_service_adapter.py:845-853`) fed by the silent `hasattr` drop (`manager.py:3241`), and the WS-applied/ack-lapsed race — are **latent but did not fire** (no matching log lines; the WS leg never connected).

**Options & trade-offs.** Fixing the bound on either side alone is insufficient: cascor must make its own default admissible under its own PATCH validation (default → ≤1e6, or ceiling raised to admit the default — a 1e11-epoch ceiling has no physical meaning, so lowering the default is preferred);
canopy should defensively clamp/validate seeded values against the documented PATCH bounds. Full per-key partial apply was considered and **deferred** (validation §11 skeptic #2): the observed failure is body-atomic model validation;
"apply the rest" would require loosening pydantic bounds, re-validating per key, mirroring the WS leg, and churning cascor-client/Fake/test surfaces — overreach for the problem. The durable, additive contract is `applied`/`skipped(reason)` **reporting** (which also kills the silent `hasattr` drop).

**Chosen design.** Cascor C2a: additive `applied`/`skipped(reason)` response reporting; eliminate the silent `hasattr` drop; keep atomic 422 for bound violations.
Cascor C2b: bound coherence (default `epochs_max` ≤ PATCH ceiling) + reconcile the `/v1/network` vs `/v1/training/status` parameter surfaces (single source of truth) + document counter semantics.
Canopy N5: clamp/validate backend-seeded form values against the PATCH bounds at init and apply; surface `response.text` verbatim in the toast; skip the WS-first leg while the control stream is marked dead (consumes N2's liveness state).

**Tests.** T-4a canopy unit: toast carries upstream detail; seeded out-of-bound values are clamped/flagged at init. T-4b cascor: default-vs-ceiling coherence regression; surface-consistency regression; applied/skipped shape.
T-4c isolated-stack E2E: full-form Apply with backend-seeded values succeeds end-to-end; a genuinely out-of-range field yields a visible, specific rejection.

### I-5 — MNIST start fails: juniper-data 500

**Symptom.** S9; the pending-dataset banner then sticks around (staged config preserved on failure — by design, `manager.py:2907-2909`).

**Evidence.** juniper-data log: 71 identical `Unhandled exception` tracebacks 05:48:54 → 06:23:23, each ending
`File ".../juniper_data/generators/mnist/generator.py", line 55, in generate / raise ImportError("Hugging Face datasets package not installed. Install with: pip install datasets")`
followed by `POST /v1/datasets … 500`.
Live env check: `conda run -n JuniperData python -c "import datasets"` fails — the package is absent from the runtime, and from juniper-data's entire dependency surface (pyproject deps/extras, `requirements.lock`, `Dockerfile`).
The full error chain matched the prediction exactly: `datasets.py:148-159` bare re-raise → `app.py:143-149` generic 500 (no ImportError-specific handler) → data-client `client.py:319` `Request failed (500)` →
cascor `manager.py:2962` `juniper-data fetch failed` → 409 (`routes/training.py:92`) → canopy relay (`main.py:3109`). The Start-button toast surfaced the chain (S9) — the error text worked; the failure is upstream capability + a 500 where a 4xx belongs.

**Root cause (confirmed).** Missing optional dependency, invisible to CI because the unit tests mock the loader (`juniper_data/tests/unit/test_mnist_generator.py:46-49`).
Everything else on the path is sound: `mnist` is registered (`generators.py:161-166`; registry/schema endpoints expose no availability info today, `generators.py:178-215`) and an accepted staged type (`training.py:160`);
translation forwards `n_samples` (+ `noise`, tolerated by pydantic's default extra-handling in `MnistParams`, `params.py:17-48`); flattened MNIST is rank-2 float32 `(N, 784)`/one-hot `(N, 10)`, NPZ-contract-compliant; cascor would auto-create a 784×10 network (`manager.py:1918-1928`).

**Options & trade-offs** (ship vs gate): gate-only leaves MNIST dead but honest; ship-only adds a heavy dependency chain (HF `datasets` + pyarrow) to every install and needs an offline/cache posture; both-staged gives an honest UI immediately and a working MNIST behind an explicit extra.
Status code for "generator unavailable": 503 invites retries/health-tooling misreads for a deterministic condition — prefer **501** (not implemented in this deployment) or 422 with the install hint (validation §11 skeptic #8; confirm data-client's retry policy for the chosen code).

**Chosen design (both, staged).** juniper-data D1 first: catch capability errors at the generation seam and return 501/422 with the install hint; expose `available: bool` per generator in the registry/schema responses.
juniper-data D2: add `datasets` behind a `[mnist]` extra; install in the Docker image and the `JuniperData` env; document the HF cache/offline posture; add a real-generation test (cache-seeded or skip-marked offline).
Canopy N7: consume the availability flag to grey out unavailable dataset types with the reason — compat posture: flag-absent (older juniper-data) defaults to available, and the deploy-level juniper-data version floor is bumped when N7 lands (canopy reads `/v1/generators` via direct httpx, `main.py:1555-1567` — no client-library release needed).
Cascor: no change on this path (its 409 already carries the upstream text).

**Tests.** D1: unavailable generator → 501/422 + hint (no 500); availability flag present. D2: real generation produces contract-compliant NPZ shapes. N7: unavailable type not selectable with reason shown; flag-absent compat. E2E: staged MNIST trains end-to-end on the isolated stack once D2 lands.

### I-6 — `Stop & Restart with new dataset` gives no feedback (and never stops)

**Symptom.** S10 (perceived silent failure); S8 (2-D swaps "appear to work").

**Evidence (corrected in validation — the original "restarts never reached cascor" was wrong).**
All three cold-swaps during the session — 05:10:34 (xor), 05:19:00 (moons), 05:28:13 (circles) — logged `Cold-swap restart with staged dataset`, which is emitted **only on HTTP 200** (`dashboard_manager.py:4211-4212`), and each was followed within ~6 s by a real cascor training start
(`Starting main training loop` 05:10:39 / 05:19:06 / 05:28:20; juniper-data shows the xor/moon/circles dataset creations in exact swap order) and a ~5-minute run to completion.
Cascor was **idle** at each swap (run 2 completed 19:49:14), so the starts were legitimately accepted. The user saw none of it: the dashboard was frozen (I-1) and the callback surfaces nothing.
During the MNIST attempts the same callback DID log `Restart with new dataset failed: 409 …` — still invisible to the operator (log-only).
The earlier "no cascor activity / exactly one start_training" reading was an artifact: `start_training:` is logged only in the no-network branch (`manager.py:1923-1927`), and route-level failures log at DEBUG (`routes/training.py:91`).

**Root cause (revised).**

1. **Zero feedback by construction (confirmed)**: the callback's sole Output is the banner `is_open` (`dashboard_manager.py:4188`); success shows nothing; every failure path is `logger.warning` + `dash.no_update` (`:4214-4218`); `apply_dataset` staging is likewise silent (`:4157-4161`).
   Combined with I-1's frozen dashboard, three successful runs read as silent failures.
2. **No stop step (confirmed)**: the button performs only `POST /api/train/start?reset=true` (`:4205-4210`) despite its name. This session never exercised a swap during an active run;
   code reading (Lens 2 #6) indicates canopy's live in-progress guard (`is_training_in_progress` is a live status GET, adapter `:609-620`) would 409 — silently — and that cascor-side, near-simultaneous starts queue on a 1-worker executor (`manager.py:1970-1971`, `:1994`). Characterize in E-2.
3. **`reset=true` accepted but dropped (confirmed)**: `service_backend.py:105`, `:116`.

**Chosen design** (the prompt's preferred shape, now with a confirm step — validation §11 skeptic #11: N3 turns a button that today stops nothing into one that can kill a multi-hour run; the accident cost is asymmetric).
Canopy N3: implement the promised sequence — lightweight confirm → `stop()` → await stopped (bounded) → `start()` consuming the staged dataset — surfacing each step's outcome through the §S10 alert machinery
(the restart and `apply_dataset` callbacks gain alert Outputs; failures keep the pending banner open); forward `reset`; regression-pin the active-run path per E-2's findings.
Interaction with cascor#396 staging semantics verified safe: `stop_training()`/`reset()` do not touch `_pending_dataset_config` (`manager.py:2104-2150`); consume-then-clear happens under `_lock` in `start_training` (`:1902-1904`), fetch-failure preserves staging — no lost/double-consumed staging in stop→await→start.
The prior doc's fifth follow-up bullet (cascor-side auto-create/restart alternative) was revisited: still not chosen (canopy-side orchestration keeps the engine API minimal, consistent with the 2026-07-09 decision); a cascor-side atomic restart remains the documented fallback if the stop-window race proves troublesome.

**Tests.** Unit: restart handler sequence (confirm → stop → await → start); failures produce alert payloads; `reset` reaches the adapter. UI harness: a 409 on restart renders a visible alert; success renders a visible confirmation.
E2E (isolated): cold-swap during an active run stops, restages, restarts visibly; idle-time swap remains one click + confirm.

### I-7 — Dataset Parameters panel shows inapplicable generator params

**Symptom.** S12 (partial): spiral-ish `Elements`/`Noise` fields shown while Type = MNIST; `2-D models only` hint reads as excluding MNIST.

**Evidence & root cause (confirmed, cosmetic).** The panel is static layout — `Elements`/`Noise` always render (`dashboard_manager.py:1157-1180`; defaults `canopy_constants.py:147`, `:150`)
and `apply_dataset` sends them for every type (`:4138-4146`); harmless downstream (pydantic default extra-handling in `MnistParams`).
The hint text comes from `dataset_model_hint` (`model_registry.py:375-395`); MNIST is declared `ndim=2` and cascor-compatible (`model_registry.py:135`, `:172`) — the hint is about tensor rank, not feature count, and confuses.

**Chosen design.** Canopy N7 (same PR family as the capability gating): drive per-type parameter visibility from the dataset-type registry (ideally juniper-data's generator schema via D1, falling back to a static per-type map),
stop sending inapplicable params, and reword the model hint (e.g. "rank-2 (tabular) datasets only"). Low priority; ships after the correctness fixes.

**Tests.** Unit: per-type visible-param sets; staged payload contains only applicable keys; hint text snapshot.

## 5. Cross-Cutting Themes

- **T1 — Error-detail propagation.** Three confirmed flattenings hid this session's root causes: `Failed to apply ({status})` discards the body (`dashboard_manager.py:5833`);
  snapshot 500 replaces the upstream pydantic message (`main.py:2147-2152` + panel prefix `:841-845`); restart failures are log-only (`:4214-4218`).
  Standard: every control toast carries the upstream `detail`/`error` text verbatim (truncated for display); canopy routes forward upstream status+detail rather than minting constants. (N3/N4/N5)
- **T2 — WS liveness semantics.** Sticky `metricsReceived`/`topologyReceived` gates removed (N1); the control-stream supervisor must detect half-open sockets (`is_connected` ⇔ `_ws is not None` today) and reconnect with logged backoff;
  the canopy↔cascor heartbeat contract must be explicit — cascor pings every 30 s and closes after a 10 s pong window while the cascor-client WS layer implements no ping/pong handling; the UI gets a degraded-mode indicator when streams are quiet. (N2/C3/CL1)
- **T3 — Apply reporting contract.** Cascor returns per-key `applied`/`skipped(reason)` additively (killing the silent `hasattr` drop, `manager.py:3241`) while keeping atomic 422 for bound violations; canopy renders both sets. (C2a/N5)
- **T4 — Silent-failure elimination.** Every control callback (`restart_with_new_dataset`, `apply_dataset`, stop/reset paths whose outcomes the log never showed) surfaces success AND failure via the §S10 machinery. (N3)
- **T5 — Observability gaps that hid this incident.** Cascor's uvicorn access logging died when training started (last access record 18:19:56; the 05:44–06:40 API window is unlogged; cf. cascor#205 history);
  `unrecognized_ws_frame` warnings omit `msg_type` (thousands of warnings, zero diagnostic value — logged as mirrored pairs by cascor-client and canopy); the relay has no throughput counters; route-level start failures log at DEBUG (`routes/training.py:91`).
  Fix: access-log survival regression, `msg_type` on unrecognized frames, relay frames-forwarded counter + periodic INFO, start-failure logging at WARNING. (C4/CL1/N2)
- **T6 — Dead stores.** `ws-state-buffer`/`ws-candidate-progress-buffer` drains have no consumers — remove or wire when O3 lands. (N1 cleanup)

## 6. Hypothesis Disposition (from the driving prompt, updated post-validation)

| Prompt hypothesis                                                                        | Disposition                                                                                                                                                                                                       |
|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| I-1(a) WS chain under-delivers while browser socket healthy → sticky gate starves Path A | **Confirmed, mechanism refined**: `initial_metrics` is a relay-connect broadcast (not per-mount); starvation hits long-lived tabs; fresh tabs keep polling                                                        |
| I-1(b) tiles stale-by-design (no WS writer)                                              | **Confirmed** by construction                                                                                                                                                                                     |
| I-1(c) circuit-breaker fallback / cascor status frozen                                   | **Refuted** (fresh probes)                                                                                                                                                                                        |
| I-1(c) `apply-in-flight` interval clamp                                                  | **Reopened** as a candidate for the pre-refresh tab's total freeze (header included) — the boundary-based refutation was invalid (tab-activation Inputs fire regardless); OPEN → E-3                              |
| I-2 same starvation class + cascade_add-only pushes                                      | **Confirmed**                                                                                                                                                                                                     |
| I-3(a) concurrent HDF5 write vs training thread                                          | **Refuted for this incident**; latent (no lock) — hardening in C1                                                                                                                                                 |
| I-3(b) headers-in-comment → 401/429                                                      | **Refuted as trigger** (request reached cascor; auth off); latent one-line defect — fixed in N4                                                                                                                   |
| I-3 actual cause                                                                         | **New finding (corrected seam)**: canopy route mints `description: None` (`main.py:1997-1998` → `:2078`); cascor 422s explicit null (panel already omits blanks)                                                  |
| I-4 path 1 verification_failed (hasattr drop)                                            | **Not observed** this session; latent — C2a                                                                                                                                                                       |
| I-4 path 2 WS-applied + ack lapse                                                        | **Refuted as mechanism** (control WS dead since 18:17:03; WS leg never applied anything)                                                                                                                          |
| I-4 actual cause                                                                         | **New finding (corrected attribution)**: cascor's own `epochs_max` default (1e11) exceeds its own PATCH ceiling (1e6); canopy echoes it via `init_params_from_backend` → wholesale 422 every apply; detail hidden |
| I-4 "params applied via start payloads"                                                  | **Unsupported** (Lens 2): start/restart carry no params; divergent live values are two engine default layers                                                                                                      |
| I-5 missing HF `datasets` dependency                                                     | **Confirmed** (71 ImportError tracebacks + live env import failure)                                                                                                                                               |
| I-6 silent-by-construction restart                                                       | **Confirmed**; **corrected**: idle-time restarts DID reach cascor and trained successfully (invisibly); active-run behavior untested → E-2                                                                        |
| I-7 static panel / hint semantics                                                        | **Confirmed** (cosmetic)                                                                                                                                                                                          |

## 7. Phased Fix Roadmap

PR-sized work units, dependency-ordered (upstream before consumers). Every unit lands as its own PR (owner merges); each names its verification.

| Unit | Repo                           | Type  | Summary                                                                                                                                                                                                         | Depends on              | Closes                               | Verify                                  |
|------|--------------------------------|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|--------------------------------------|-----------------------------------------|
| D1   | juniper-data                   | fix   | Generator availability surfaced: registry/schema `available` flag; unavailable generator → 501/422 + install hint (no masked 500)                                                                               | —                       | I-5 (gate half)                      | `pytest juniper_data/tests/ -v`         |
| D2   | juniper-data                   | feat  | `[mnist]` extra ships HF `datasets`; Docker/env install; offline-cache doc; real-generation test                                                                                                                | D1                      | I-5 (ship half)                      | same + isolated E2E                     |
| C1   | juniper-cascor                 | fix   | Snapshot create: tolerate explicit-null `description`; propagate serializer failure detail (correct status); write-isolation hardening                                                                          | —                       | I-3 (robustness)                     | `bash src/tests/scripts/run_tests.bash` |
| C2a  | juniper-cascor                 | fix   | Apply reporting: additive per-key `applied`/`skipped(reason)`; remove silent `hasattr` drop; keep atomic 422 for bound violations                                                                               | —                       | I-4 (contract), T3                   | same                                    |
| C2b  | juniper-cascor                 | fix   | Bound + surface coherence: `epochs_max` default ≤ PATCH ceiling; reconcile `/v1/network` vs `/v1/training/status` params; document counter semantics                                                            | —                       | I-4 (root), I-1c                     | same                                    |
| C3   | juniper-cascor                 | fix   | Control-WS heartbeat contract (tolerate pong-less clients or specify the requirement); `/ws/training` metrics-emission instrumentation (E-1)                                                                    | —                       | I-1 (Path B), I-4 (WS leg)           | same + E-1                              |
| C4   | juniper-cascor                 | fix   | Access-log survival after training start (logging-init clobber) + start-failure logging at WARNING + regression                                                                                                 | —                       | T5                                   | same                                    |
| CL1  | juniper-cascor-client          | fix   | WS ping/pong handling (root fix for the 40 s close); `msg_type` on unrecognized frames; half-open detection surfaced to consumers                                                                               | —                       | I-1/I-4 (WS), T2/T5                  | client suite                            |
| CL2  | juniper-cascor-client + canopy | chore | Cut cascor-client GitHub Release (per convention); bump canopy floor; `FakeCascorClient` parity for new surfaces                                                                                                | CL1                     | gates wave 2                         | drift lints + canopy suite              |
| N1   | juniper-canopy                 | fix   | Un-gate metrics + topology polls (O2) with empty-guard (`no_update` on empty/error vs non-empty store); `asyncio.to_thread` for history fetch; bound full-mode `limit`; remove dead drains; fix stale docstring | Q4 answered; CL2 (soft) | I-1 tiles/charts, I-2, T6            | `pytest` per AGENTS.md + UI harness     |
| N2   | juniper-canopy                 | fix   | Supervisor/relay hardening: half-open detection + logged reconnect/backoff; `/api/state` live-first base fields (keep global for demo/WS); degraded-mode indicator; relay throughput counter; E-3 resolution    | CL2                     | I-1 state/header, T2/T5              | same                                    |
| N3   | juniper-canopy                 | fix   | Restart orchestration: confirm → stop → await → start(staged); surface all outcomes (restart + apply_dataset alerts); forward `reset`; pin active-run path per E-2                                              | —                       | I-6, T1/T4, §6 follow-up (cold-swap) | same                                    |
| N4   | juniper-canopy                 | fix   | Snapshot route seam: no `None` description (`main.py:1998`/`:2078`); restore `headers=internal_api_headers()`; toast carries upstream detail                                                                    | —                       | I-3, T1                              | same                                    |
| N5   | juniper-canopy                 | fix   | Apply-params UX: clamp/validate backend-seeded values against PATCH bounds; toast carries rejection detail verbatim; render applied/skipped; skip WS leg when stream dead                                       | C2a, C2b, N2            | I-4, T1/T3                           | same                                    |
| N6   | juniper-canopy                 | fix   | Header/tile semantics: correct Epoch/Step/Iteration/Hidden-Units mappings + denominators from the reconciled surface; document counter semantics                                                                | C2b                     | I-1c / S12                           | same + UI snapshot                      |
| N7   | juniper-canopy                 | feat  | Dataset panel type-awareness (schema-driven params); capability gating (flag-absent → available; deploy data-floor bump); hint rewording                                                                        | D1                      | I-7, I-5 (UX)                        | same                                    |
| E1   | juniper-ml                     | chore | Isolated-stack E2E checklist additions (per closed issue) to the smoke tooling/docs                                                                                                                             | all                     | verification                         | scripted E2E                            |

Independent quick wins: **N4** and **D1** (no dependencies). Suggested waves: wave 1 = D1 + C1 + C2a + C2b + N4; wave 2 = CL1 + CL2 + C3 + C4 + N1 + N2 (N1 additionally gated on Q4); wave 3 = N3 + N5 + N6; wave 4 = D2 + N7 + E1.

## 8. Risks

- **Chart/tile wipe under the un-gated poll (N1)**: the store handler currently returns `[]` on empty/error fetches (`dashboard_manager.py:5215`, `:5257`) and cascor clears metrics post-run — without the empty-guard, the 1 Hz poll would blank a completed run's charts (today's sticky gate accidentally preserves them). The guard is a hard N1 requirement; Q4 (retention) decides the durable posture.
- **Event-loop blocking (N1)**: `get_metrics_history` makes a synchronous cascor-client call inside an async route (`main.py:1217-1227`); un-gated 1 Hz polling turns a slow cascor into a canopy-wide stall. `asyncio.to_thread` is a hard N1 requirement; full-history mode must bound its fetch (`limit=0` → up to 10k rows/tick today, `:5207-5210`).
- **Poll-load regression (N1)**: ~1 req/s/browser for metrics (Decision-Boundary precedent), ~0.2 req/s tab-gated for topology. Acceptable; the liveness-gate option remains available if measured load says otherwise.
- **Dual-path chart writes (N1)**: poll full-redraw + WS `extendTraces` can transiently double-append (≤1 tick; the next rebuild overwrites). Optional keying mitigation; UI-harness regression.
- **Cascor response/validation changes (C1/C2a/C2b)**: consumers of `PATCH /v1/training/params` and `POST /v1/snapshots` see additive fields / new bounds. Today's only PATCH consumer is canopy's adapter; cascor-client + Fake updated via CL2; version-gated floors.
- **Stop→start race (N3)**: a bounded stop-wait can time out mid-swap; staging survives by design (`manager.py:2104-2150`, `:1902-1904`). Mitigation: keep banner open with a retriable error; cascor-side atomic restart remains the documented fallback. The confirm step mitigates the accidental-stop asymmetry.
- **MNIST dependency weight (D2)**: HF `datasets` pulls a heavy chain — extra-gated, never in base install; Docker image size checked in PR.
- **Behavior change on restart semantics (N3)**: anything scripted against the current fire-and-forget restart may notice. Mitigation: UI-harness + E2E checklist; changelog note.
- **Release sequencing (CL2)**: N1/N2's client-surface dependencies require a cascor-client release + canopy floor bump + Fake parity — the exact class canopy#441 just paid down; skipping it re-opens the drift.

## 9. Verification Plan

- **Per-repo suites** (every roadmap unit): canopy `pytest` per its AGENTS.md (incl. the UI harness split), cascor `bash src/tests/scripts/run_tests.bash`, juniper-data `pytest juniper_data/tests/ -v`, cascor-client suite.
  A regression test is mandatory per confirmed root cause (sticky gate; route-seam `None` description; bound incoherence; feedback-free restart; ImportError mapping; headers kwarg; empty-fetch wipe guard).
- **Isolated-stack E2E** (prior doc §7 pattern — cascor 8202 + canopy 8051, **plus juniper-data on 8101 with `JUNIPER_DATA_URL` pointed at it**; never against the operator's stack):
  per-issue scripted checks — long-lived tab advances via poll with WS silenced; post-completion charts persist; topology refreshes on unit add and tab switch; snapshot create succeeds (blank + filled description);
  full-form Apply succeeds with backend-seeded values; cold-swap during an active run stops, restages, restarts with visible outcomes; MNIST end-to-end post-D2.
- **Targeted experiments for OPEN items**:
  **E-1** (I-1 Path B): raw WS client on cascor `/ws/training` during an isolated training run, logging every frame type — decides cascor-emission vs client-drop for per-epoch metrics (feeds C3 and Q6).
  **E-2** (I-6): cold-swap during an active isolated run — characterize canopy's live in-progress 409 vs cascor's 1-worker executor queueing (`manager.py:1970-1971`, `:1994`); pins N3's active-run design.
  **E-3** (I-1 root cause 4): reproduce the pre-refresh tab's total freeze — drive failed applies (evening-502 pattern) and observe whether `apply-in-flight` (`dashboard_manager.py:2761-2798`) sticks the intervals off; separately assess background-tab timer throttling; decides whether N2 needs an in-flight watchdog.
- **Docker parity**: after canopy/cascor/data merges, rebuild images and re-run the E2E checklist under `make up` (deploy's build-freshness/provenance guards apply).

## 10. Coverage Matrix

| Item                                                                                   | Where addressed                                                                                          |
|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| S1–S12 (symptoms)                                                                      | §2 table maps each to its issue; all issues covered in §4                                                |
| I-1                                                                                    | §4 I-1; roadmap N1/N2/N6 (+C2b/C3/CL1); E-1/E-3                                                          |
| I-2                                                                                    | §4 I-2; roadmap N1                                                                                       |
| I-3                                                                                    | §4 I-3; roadmap N4 (quick win) + C1 (robustness)                                                         |
| I-4                                                                                    | §4 I-4; roadmap C2a/C2b/N5 (+N2)                                                                         |
| I-5                                                                                    | §4 I-5; roadmap D1/D2/N7                                                                                 |
| I-6                                                                                    | §4 I-6; roadmap N3; E-2                                                                                  |
| I-7                                                                                    | §4 I-7; roadmap N7                                                                                       |
| §6 follow-up: cold-swap error surfacing                                                | I-6 / N3 (in scope)                                                                                      |
| §6 follow-up: `unrecognized_ws_frame` warnings                                         | I-1 evidence + CL1/C3 (in scope; ping-frame cause strongly supported; `msg_type` logging)                |
| §6 follow-up: control-stream reconnect posture                                         | N2/C3/CL1 (in scope; extended to half-open detection + ping/pong handling — this session's failure mode) |
| §6 follow-up: PR-D confirm-defaults modal                                              | Partially folded in: N3 gains a lightweight confirm; the full defaults-modal remains deferred (Q3)       |
| §6 fifth bullet: cascor-side auto-create alternative (not chosen)                      | Design alternative revisited in I-6 chosen design; still not chosen                                      |
| Defect-list skeleton (`notes/JUNIPER_2026-07-04_JUNIPER-CANOPY_CANOPY-DEFECT-LIST.md`) | Q5: propose populating it from this plan's issue IDs or retiring it                                      |

## 11. Validation Record

Multi-agent validation per the driving prompt (directive 10), all agents on Fable 5, fresh contexts, read-only:

- **Lens 1 (anchor re-probe)**: 88 claims checked → 76 verified, **8 failed**, 4 unverifiable (browser-state/stateful-probe items, marked as inference in the text).
  Failures fixed in this revision: the I-6 "restarts never reached cascor" reading (6 real training starts found — `Starting main training loop`; the grepped `start_training:` string logs only in the no-network branch);
  the single-run timeline; the "UI default = 1e11" attribution (canopy default is 1e6; 1e11 is the field max and cascor's echoed default); the snapshot `None` seam (route `main.py:1997-1998`, panel already omits);
  the `initial_metrics`-per-mount mechanism (relay-connect broadcast only); the combined unrecognized-frame count (mirrored pairs, two warning names); the Apply-502 count/window (59 lines through 06:40); the `MnistParams` extra-ignore wording (pydantic default, not explicit config).
- **Lens 2 (semantic challenge)**: 8 load-bearing claims re-derived from code → 2 supported, **6 needing correction**, all folded in:
  the `initial_metrics` origin (cascor `training_stream.py:59-77`); `/api/state`'s hybrid live-fetch (`main.py:1190`); the epochs bound incoherence being cascor-internal (`constants_model.py:206` vs `training.py:54`/`:218`) with canopy echo (`dashboard_manager.py:5871-5875`);
  the "params applied via start payloads" claim (unsupported — start carries no params; divergent values are two engine default layers); the snapshot seam; and the I-6 mechanism (200s end-to-end; live in-progress guard; 1-worker executor queueing; both prior OPEN mechanisms code-refuted).
- **Skeptical design review**: 13 findings (3 major / 7 minor / 3 info), verdict NEEDS-REVISION — all majors adopted (N1 empty-guard + Q4 coupling; C2 split into C2a/C2b with partial-apply deferred; CL2 release/floor/Fake unit added)
  and all minors adopted or reflected (O2 for topology too; `/api/state` live-first; event-loop + full-history risks; N4 independence; 501/422 over 503; N7 compat posture; C2b on the critical path made explicit; N3 confirm step).
- **Orchestrator spot-verification**: the six most load-bearing corrections were independently re-probed first-hand before adoption (epochs default/max constants, route `None` seam, cascor `description: str = ""`, `epochs_max le=1_000_000`, the 6 `Starting main training loop` entries).

Round 1 (3 agents): findings raised **27** (8 + 6 + 13); resolved **27** (this revision); unresolved grounding findings: **0**.
Items that remain genuinely undecidable from this session's evidence are carried as OPEN experiments (E-1/E-2/E-3) and owner questions (§12), not as claims.

## 12. Open Questions (owner decisions)

### Questions

- **Q1 (I-4)**: Bound coherence direction — lower cascor's `epochs_max` **default** to ≤1e6 (recommended; a 1e11-epoch ceiling has no physical meaning) vs raise the PATCH ceiling to admit the current default. Canopy clamps defensively either way (N5).
- **Q2 (I-5)**: Priority of D2 (ship real MNIST behind `[mnist]`) vs D1-only gating for now. Is MNIST-on-CasCor a near-term research goal or a menu item that should be honest-but-disabled?
- **Q3 (§6 follow-up)**: N3 folds in a lightweight confirm before stop→restart. Should the full PR-D confirm-defaults modal (model+dataset defaults preview) still ship as a separate UX increment, and when?
- **Q4 (N1 precondition)**: cascor reports `total_metrics: 0` and empty `/v1/metrics/history` after run completion — is post-run metrics clearing (`manager.py:2142`, `:4042`) intended?
  If retention is desired, that is an eighth defect candidate; either way N1's empty-guard makes the un-gated poll safe.
- **Q5**: Populate the 2026-07-04 defect-list skeleton from this plan's issue IDs (D-001 ff. ← I-1…I-7 rows) or retire it in favor of issue-tracked work?
- **Q6 (E-1 outcome-dependent)**: if cascor genuinely emits no per-epoch metrics on `/ws/training`, decide whether it should (cascor change) or whether REST polling remains the metrics source of truth and Path B is demoted to events-only (topology/state/candidate).

### Answers

- **Q1 (I-4)**:
  - Answer: the meaning and significance of the epochs_max meta parameter has evolved over the course of juniper-canopy and cascor development.
    - initially, max epochs was a param that offered a reasonable and meaningful way to place a hard limit on the training of what, at the time, was a very simplistic model that could potentially plateau and train indefinitely.
    - over the development process, the increasing complexity of the cascor models have motiviated the addition of several, independently tracked meta parameters including:
      - training of individual candidate node epochs
      - candidate pool-wide training iterations
      - full cascor network output training epochs
      - max cascor network output training iterations
    - the max epochs param, while still setting an upper limit, is now a more arbitrary value that risks hiding the more granular and independently set, candidate pool and cascor network training limits.
    - as such, the role and calculation of the max epochs meta param should be reevaluated and employ one of the following new approaches:
      - be set to a significantly large, but fundamentally arbitrary value intended to ensure that the more granular limits are not being shadowed.
      - be removed completely as a meta parameter, including its calculation, tracking, gating, and display code.
      - be determined pragmatically, per training run, based on the total calculated number of epochs implied by the newer, more granular meta parameter limits.

- **Q2 (I-5)**:
  - Answer: the availability and viability of the MNIST dataset represents a near-term research goal.
    - the ability to train a cascor network on MNIST data is part of the infastructure needed for an ongoing experiment involving:
      - repeatedly training a single cascor model on multiple datasets of diverse types.

- **Q3 (§6 follow-up)**:
  - Answer: the idea of a light-weight confirm prior to stop->restart is a good one.
    - based on the nature of the juniper project, however, a full confirm-defaults confirm is also desirable.
    - as a compromise intended to preserve both the accessibility and flexibility of the canopy front-end, let's evaluate the following:
      - using a simple confirm modal before stop-restart actions that assumes all other meta parameters, structures, and processes remain unchanged
      - with a expandable dropdown section--itself potentailly organized using multiple, collapseable sub-sections that enable:
        - a detailed, granular verification of all existing network params, meta-params, and components
        - a custom modification of any number of existing values for network params, meta-params, and components.

- **Q4 (N1 precondition)**:
  - Answer: there are two, current use-cases included in this particular aspect of the design:
    - first, continuing the training process, likely with new datasets, using the current cascor model as trained.
      - in this use-case, it seems reasonable to default to retaining the values for total metrics and history so that continuity is provided across training processes spanning multiple datasets.
      - at the same time, the trained model itself is the primary artifact created throughout the multi-dataset training process, and the ability to clear the metric count and history could conceivably be useful.
      - adding a control that allows the existing model to be retailed
        - the control should include meaningful fallback functionality as either:
          - an "are you sure, the data will be permanently cone" confirmation
          - a reset button that reverses the clearing of these values
        - the fallback mechanism should be accessible at any point up until the new training process has begun.
    - second, discarding the model and all corresponding, retained data
      - in this use-case, the multi-dataset training process is being restarted with a new, vanilla, untrained cascor model
      - selecting for this usecase should be functionally identical to a clean launch of the juniper stack
        - with the exception of artifacts that have an expectation of permanence:
          - e.g., snapshots, etc.
      - this should arguably be the initial choice--defaulting to false--presented when confirming training with a new dataset.
        - if a simple confirm occurs and this "start fresh" control isn't selected, then the first use-case above is selected.

- **Q5**:
  - Answer: let's retire the older defect-list skeleton and track all status and/or state changes in this document directly.
    - as such, state/status updates should be captured in this document in a frequent and ongoing process
    - updating the document as work is performed, modified, completed, and validated should be included as a key compenent of the default remediation workflow.

- **Q6 (E-1 outcome-dependent)**:
  - Answer: preferentially, the canopy front-end should use ws communication to the extent practicable.
    - API only, i.e., polling, communication should be used for messages and/or updates that are not needed in real, or near-real, time.
    - the fundamental requirement that defines the need-based distinction between ws and polling communication is the display accuracy and interaction responsiveness of the canopy web app.

---

*Generated by dispatching `prompts/generated/JUNIPER_CANOPY_TRAINING-RUNTIME-DEFECTS_PLAN_2026-07-11_0842.md`;
grounded in canopy `f49a04ac`, cascor `2926245c`, juniper-data `fdbe0de1`, data-client `9a6453f2`, cascor-client `292c520c`;
live-stack probes and log sweep of the 2026-07-10 18:15 session (read-only throughout — the operator's stack was never mutated);
validated by three independent Fable 5 agents (anchor re-probe / semantic challenge / skeptical design review) with all 27 findings resolved in this revision.*
