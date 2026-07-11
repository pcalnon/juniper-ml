# Plan / Design — juniper-canopy training-runtime defects (post training-start fix): stale live updates, control-plane failures, and the MNIST dataset start failure

## Role

You are a principal engineer / architect for the Juniper ecosystem (juniper-canopy primary; juniper-cascor, juniper-data, and juniper-data-client where implicated), with the judgement to weigh options, trade-offs, and risks and to commit to a defensible design. Your deliverable is a planning DOCUMENT — you change no code.

## Resources

**Repos and provenance** (all on `main`, clean, in sync with `origin/main` as of 2026-07-11; every line anchor below was independently line-verified on 2026-07-11 — canopy anchors were verified at `889dbfa` and re-verified unchanged at `f49a04ac`, whose diff touches only `pyproject.toml`/`requirements.lock`; if a HEAD has moved when you start, re-verify anchors against the new HEAD before relying on them):

| Repo | Path | HEAD |
| --- | --- | --- |
| juniper-canopy | `/home/pcalnon/Development/python/Juniper/juniper-canopy` | `f49a04ac` |
| juniper-cascor | `/home/pcalnon/Development/python/Juniper/juniper-cascor` | `2926245c` |
| juniper-data | `/home/pcalnon/Development/python/Juniper/juniper-data` | `fdbe0de1` |
| juniper-data-client | `/home/pcalnon/Development/python/Juniper/juniper-data-client` | `9a6453f2` |
| juniper-cascor-client | `/home/pcalnon/Development/python/Juniper/juniper-cascor-client` | `292c520c` |
| juniper-ml (deliverable target: the running checkout's `notes/`) | `/home/pcalnon/Development/python/Juniper/juniper-ml` | current `main` |

**Live stack**: the operator's on-host stack — canopy `http://localhost:8050`, cascor `http://localhost:8201` (container port 8200), juniper-data `http://localhost:8100`; health `GET /v1/health` on each. The running cascor may hold live training state; treat the stack as read-only evidence (see Constraints).

**Prior work (required reading, in order)**:

1. `notes/JUNIPER_2026-07-09_JUNIPER-ECOSYSTEM_TRAINING-START-FAILURE-DIAGNOSIS-AND-FIX-PLAN.md` (juniper-ml) — the immediately-preceding diagnosis-of-record. Its `### Follow-ups (documented, not in this round)` subsection (inside §6 "Fix Plan") names four open items this plan must triage: cold-swap button error surfacing, the `juniper_canopy_unrecognized_ws_frame` / `juniper_cascor_client_unrecognized_ws_frame` warnings, control-stream reconnect posture on policy rejections, and the PR-D confirm-defaults modal.
   - The subsection's fifth bullet (the not-chosen cascor-side auto-create alternative) is a design alternative to revisit where relevant (e.g. the I-6 restart design), not a triage item; give it a Coverage Matrix row marked as such.
2. The merged fix PRs from that round (all on `main`):
   - canopy#437 (`24c9360`, propagate backend ControlResult failures instead of success theater) and canopy#438 (`889dbfa`, first start on a fresh cascor stages the default dataset; carry start-failure detail);
   - cascor#396 (`2926245`, start_training creates the network from dataset dims; translate staged configs to juniper-data schema) and cascor#391 (`039a257`, snapshot RESTORE/LISTING repair — not the create path);
   - canopy#439/#440 (CI/hermeticity) and juniper-cascor-client#91 (`292c520`, FakeCascorClient `_request` parity); canopy#441 (`f49a04a`) floors `juniper-cascor-client>=0.6.0` to consume it.
3. `notes/JUNIPER_2026-07-04_JUNIPER-CANOPY_CANOPY-DEFECT-LIST.md` (juniper-ml) — an EMPTY 60-slot skeleton (D-001–D-060, four rows per dashboard tab, all descriptions blank). Treat it as a form this plan may propose to populate or retire; NEVER cite it as a content source.

**Reported symptoms (operator, 2026-07-11, with dashboard screenshots)** — training now launches and completes successfully; the remaining defects were previously shadowed by the training-start failure:

- During a live run the header status bar and the Training Metrics tab froze at mount-time values (Loss tile `0.2337`, Accuracy `--`, Training Step `10000`, Hidden Units `0 / 10000`) while the browser WS badge showed `WS: Connected`, latency 7 ms.
- The Decision Boundary tab DID update in real time throughout the same run, and its plot showed a well-fit spiral boundary — flatly contradicting the stale 0.2337 loss tile.
- A manual full-page refresh restored truth: Loss `0.0186`, Accuracy `99.62%`, Training Step `12`, Hidden Units `10 / 10000`, header `Status: Completed — early stopped | Epoch: 12 | Iteration: 10 / 10000`. So the backend had fresh data all along; the live-update path did not deliver it.
- The Network Topology tab graph also went stale as hidden units were added.
- Snapshots tab → Create Snapshot during the run failed with the doubled toast `Failed to create snapshot: Failed to create snapshot`; Available Snapshots shows `No snapshots available`.
- Apply Parameters shows the red toast `Failed to apply (502)` even though the parameter changes DO reach cascor and take effect.
- Dataset switching works for the 2-D synthetic sets (spirals, xor, moons, circles). Selecting Type = MNIST and clicking Start Training fails with `Start failed. HTTP 409: Training could not be started: Training cannot be started: juniper-data fetch failed: Request failed (500): Internal server error.`
- Clicking `Stop & Restart with new dataset` (pending-dataset banner) fails silently — no toast, no visible effect.
- Header/tile field-semantics oddities observed both before and after refresh: `Epoch: 10000` during the run vs `Epoch: 12` after; `Iteration: 0 / 10000`; the Hidden Units tile denominator reads `10000` (the output-epochs-per-pass value) while Maximum Hidden Units was 100 (first run) / 10 (second run).
- The Dataset Parameters panel showed spiral-ish fields (`Elements: 1000`, `Noise: 0.25`) while Type = MNIST was selected, under a model selector noting `2-D models only`.

**Canopy live-update architecture (verified)** — two independent paths feed the dashboard:

- Path A (REST self-polls): Dash server callbacks on `fast-update-interval` (1000 ms) / `slow-update-interval` (5000 ms) (`src/frontend/dashboard_manager.py:1696-1697`; constants `src/canopy_constants.py:212-213`) → canopy FastAPI routes → live cascor REST via `CascorServiceAdapter`.
- Path B (WS chain): cascor `/ws/training` → canopy relay `start_metrics_relay`/`_relay_loop` (`src/backend/cascor_service_adapter.py:324-518`, started at `src/backend/service_backend.py:324`) → `websocket_manager.broadcast` (`src/backend/cascor_service_adapter.py:411`) → browser `/ws/training` (`src/main.py:612-727`) → `ws_dash_bridge.js` ring buffers → per-tick clientside drains into `dcc.Store`s (`src/frontend/dashboard_manager.py:2942-3017`).
- The Phase-B "WS supersedes polling" gates: the metrics-store poll returns `dash.no_update` when `ws_bridge_enabled AND connected AND metricsReceived` (`src/frontend/dashboard_manager.py:5201`); the topology-store poll is likewise gated (`src/frontend/dashboard_manager.py:3232-3234`).
- The sticky flags `_metricsReceived`/`_topologyReceived` flip true on the first frame and are never reset (`src/frontend/assets/ws_dash_bridge.js:52-65`).
- But Path B writes no tiles: the only consumer of `ws-metrics-buffer` is the chart `Plotly.extendTraces` clientside callback (`src/frontend/components/metrics_panel.py:728-829`), which never writes tile Outputs; the tiles' sole writer is `update_metrics_display` (`src/frontend/components/metrics_panel.py:671-694`) fed by the gated store.
- `ws-state-buffer` and `ws-candidate-progress-buffer` have no Input consumers at all (dead-end stores).
- Topology WS frames originate only from the relay's `cascade_add` hook (`src/backend/cascor_service_adapter.py:414-418`); cascor does not stream topology per-epoch.
- The header bar is written solely by `update_unified_status_bar` (`src/frontend/dashboard_manager.py:2676-2693`; handler `:4916-4952`) polling `/api/status` — route `src/main.py:1197-1204` → `ServiceBackend.get_status` (`src/backend/service_backend.py:159-209`) → adapter `get_training_status` with a circuit-breaker fallback `{"is_training": False, ...}` (`src/backend/cascor_service_adapter.py:1274-1282`). This poll is NOT WS-gated.
- The strip/learning-rate/phase-duration/progress elements read `metrics-panel-training-state-store` fed by `fetch_training_state` → `/api/state` (`src/frontend/components/metrics_panel.py:561-567`, `:1122`); `/api/state` (`src/main.py:1107-1194`) serves the in-process `training_state` global whose only recurring writer during a live cascor-backed run is the Path-B relay callback (registered at `src/main.py:204`; one-shot writers exist on startup/demo/recurrence paths).
- The Decision Boundary tab never joined the Phase-B toggle: `update_boundary_store` polls `/api/decision_boundary` on every 1 s tick while the tab is active, with no WS gate (`src/frontend/dashboard_manager.py:3279-3289`, handler `:5320-5339`; route `src/main.py:1586-1599` → adapter `get_decision_boundary` `src/backend/cascor_service_adapter.py:1490-1535`) — which is exactly why it stays live.
- Mount-time behavior: data callbacks run at initial load (`prevent_initial_call=False`, e.g. `src/frontend/dashboard_manager.py:3171-3179`) and `ws-connection-status` initializes `{"connected": False}` (`src/frontend/dashboard_manager.py:1729`), so a full refresh re-runs the ungated polls once and shows fresh values.
- Kill switch: `JUNIPER_CANOPY_DISABLE_WS_BRIDGE=true` forces pure REST polling (`disable_ws_bridge` `src/settings.py:340`; `ws_bridge_enabled` property `src/settings.py:418-421`; `enable_browser_ws_bridge` `src/settings.py:339`).

**Issue inventory** (I-1 – I-7). For each: the reported symptom above, verified code facts, and hypotheses that the plan must CONFIRM OR REFUTE with live/log evidence before designing on them.

- **I-1 — Header + Training Metrics staleness during a live run.**
  - Verified: tiles have no WS writer and their REST poll is suppressed by the sticky WS gate (`dashboard_manager.py:5201`); `/api/state` consumers depend on the Path-B relay for all recurring updates (`main.py:204`); see the architecture map above.
  - HYPOTHESES (ranked): (a) the WS delivery chain silently under-delivers (relay down/reconnecting, dropped frames — see the §6 `unrecognized_ws_frame` warnings) while the browser socket stays healthy, so the sticky gate starves Path A; (b) tiles are stale-by-design even under a healthy WS because nothing maps `ws-metrics-buffer`/`ws-state-buffer` to tile Outputs.
  - Header-specific candidates: circuit-breaker fallback pinning `is_training: False` (`cascor_service_adapter.py:1276-1279`); a cascor `/v1/training/status` that does not advance; or the `apply-in-flight` interval clamp (`dashboard_manager.py:2761-2798`) — each must be reconciled with the observed live-updating decision boundary.
  - Also diagnose the field-semantics oddities (Epoch/Iteration/Hidden-Units denominators, Accuracy `--`) as display-mapping questions: tile builder `_build_unified_status_bar_content` (`dashboard_manager.py:4972`) and `update_metrics_display`.
- **I-2 — Network Topology staleness.**
  - Verified: topology REST poll gated by sticky `topologyReceived` (`dashboard_manager.py:3232-3234`); WS topology frames only on `cascade_add` (`cascor_service_adapter.py:414-418`); REST fallback only when the tab is active (handler `:5259-5283` → `/api/topology`).
  - HYPOTHESIS: same starvation class as I-1(a); additionally, between `cascade_add` events per-epoch weight changes are invisible by design.
- **I-3 — Create Snapshot fails during a run.**
  - Verified: the doubled toast is canopy's own 500 detail `"Failed to create snapshot"` (`src/main.py:2147-2152`) wrapped by the panel prefix (`src/frontend/components/hdf5_snapshots_panel.py:841-845`).
  - Verified: the panel's create POST is the ONLY snapshots-panel request whose `headers=internal_api_headers()` is trapped inside a trailing comment (`hdf5_snapshots_panel.py:409`; siblings pass headers at `:464`, `:491`, `:557`, `:608`) — exposing it to the API-key gate (`src/middleware.py:126-127`) and the rate limiter (`src/security.py:229-231`).
  - Verified upstream chain: cascor's serializer converts ANY save exception to `False` (`src/snapshots/snapshot_serializer.py:159-160`) → lifecycle returns `None` (`src/api/lifecycle/manager.py:3877-3880`) → route 404 (`src/api/routes/snapshots.py:140-141`); no lock isolates the HDF5 write from the live training thread (`save_snapshot` `manager.py:3842`; `_save_training_history` iterates `network.history` at `snapshot_serializer.py:631-641`).
  - HYPOTHESES: (a) mid-training concurrent-mutation failure inside `save_network`; (b) the headers defect (401/429) — distinguishable because (b) never reaches cascor. Confirm which occurred (cascor + canopy logs), then design for BOTH.
- **I-4 — Apply Parameters shows `Failed to apply (502)` yet parameters apply.**
  - Verified: the toast is built at `dashboard_manager.py:5833` and discards the response body (logged only, `:5832`); canopy mints the 502 whenever the adapter returns `ok: False` (`src/main.py:3458-3468`).
  - Verified applied-yet-red path 1: post-apply readback divergence in `_verify_apply_roundtrip` → `{"ok": False, "error": "verification_failed", ...}` (`src/backend/cascor_service_adapter.py:845-853`, def `:858`).
    - A persistent mismatch generator for path 1: cascor silently drops non-`hasattr` keys yet returns 200 (`src/api/lifecycle/manager.py:3241`), and the readback serves getattr defaults (`manager.py:3009-3065`).
  - Verified applied-yet-red path 2: the WS-first hot path applies on cascor (`src/api/websocket/control_stream.py:412-424`) but canopy's 1.0 s ack window lapses → falls back to REST (`cascor_service_adapter.py:1139-1152`, `:818-821`).
    - A REST-leg failure after a landed WS hot apply reports total failure despite live hot params.
  - HYPOTHESIS: which path dominates in the operator's runs — instrument via canopy logs (`WS set_params failed` lines) and the logged response bodies.
- **I-5 — MNIST start fails: juniper-data 500.**
  - Verified staging chain: canopy stages `{"dataset_type": "mnist", "n_samples": 1000, "noise": 0.25}` (`apply_dataset` `dashboard_manager.py:4114-4161`; param map `src/backend/cascor_service_adapter.py:907-913`; `stage_dataset` `:915-922`); `mnist` is an accepted staged type (cascor `StageDatasetRequest` `src/api/models/training.py:160`) and passes through translation un-aliased with `n_samples`+`noise` forwarded (`_translate_staged_config` `src/api/lifecycle/manager.py:2852-2891`).
  - Verified fetch chain: cascor calls `JuniperDataClient.create_dataset(generator="mnist", ...)` then `download_artifact_npz` (`manager.py:2958`, `:2960`) and wraps failure at `manager.py:2962` → 409 at `src/api/routes/training.py:92` → canopy 409 relay `src/main.py:3109`.
  - Verified error translation: juniper-data's generation exceptions bare-re-raise (`juniper_data/api/routes/datasets.py:148-159`) into the generic 500 `{"detail": "Internal server error"}` (`juniper_data/api/app.py:143-149`); the data-client wraps it as `Request failed (500): Internal server error` (`juniper_data_client/client.py:319`).
  - Verified root-cause candidate: juniper-data registers `mnist` (`juniper_data/api/routes/generators.py:161-166`) but `MnistGenerator.generate` hard-requires the Hugging Face `datasets` package (`juniper_data/generators/mnist/generator.py:15-21`, raise at `:54-55`), and that package appears NOWHERE in juniper-data's dependency surface (pyproject deps/extras, `requirements.lock`, `Dockerfile`).
    - Its unit tests mock the loader (`juniper_data/tests/unit/test_mnist_generator.py:46-49`), so CI never exercises real generation. The stray `noise` param is harmless (pydantic extra-ignore, `MnistParams` `juniper_data/generators/mnist/params.py:17-48`).
  - Contract note: flattened MNIST is rank-2 `float32` `(N, 784)` / one-hot `(N, 10)` and satisfies the NPZ contract; the #396 path would auto-create a 784×10 network (`manager.py:1918-1928`), so MNIST-on-CasCor is architecturally reachable once juniper-data can generate it.
  - CONFIRM the missing-dependency root cause against the LIVE juniper-data runtime, read-only (on-host: `conda run -n JuniperData python -c "import datasets"`; Docker: inspect the running juniper-data image/container), then decide the product question: ship MNIST end-to-end (add the dependency + offline/cache posture + CI that exercises real generation) vs gate it out gracefully (canopy-side capability discovery + a 4xx with an actionable message instead of a 500), vs both staged.
- **I-6 — `Stop & Restart with new dataset` fails silently.**
  - Verified: the callback `restart_with_new_dataset` (`dashboard_manager.py:4187-4218`) performs ONLY `POST /api/train/start?reset=true` (`:4205-4210`) — it never stops training first; its sole Output is the banner `is_open`; every failure path is `logger.warning` + `dash.no_update` (`:4214-4218`) — silent by construction.
  - Verified: with training running, `ServiceBackend.start_training` short-circuits `ControlResult(ok=False, error="Training already in progress")` (`src/backend/service_backend.py:106-107`) → canopy 409 (`main.py:3105-3109`) → swallowed; the `reset` query parameter is accepted but never forwarded to the adapter (`service_backend.py:105`, `:116`).
  - Verified adjacents: `apply_dataset` staging is likewise silent on failure (`dashboard_manager.py:4157-4161`); banner state is later reconciled from `/api/status` by `reconcile_pending_dataset_banner` (`:4220-4244`); cascor consumes-then-clears the staged config at `manager.py:1902-1904` and preserves it on fetch failure (`manager.py:2907-2909`).
  - Preferred design (deviate only if the evidence argues otherwise, recording the rationale): an explicit stop → (confirm) → start-with-staged sequence with surfaced errors, honoring the banner reconciliation and cascor's staged-consumption semantics.
- **I-7 — Dataset Parameters panel shows generator params inapplicable to the selected type.**
  - Verified: the panel is static layout, not type-conditional — `Elements`/`Noise` inputs always render (`dashboard_manager.py:1157-1180`; defaults `DEFAULT_DATASET_ELEMENTS=1000` `src/canopy_constants.py:147`, `DEFAULT_DATASET_NOISE=0.25` `:150`) and `apply_dataset` sends them for every type (`:4138-4146`).
  - Verified: the `2-D models only` hint is `dataset_model_hint` (`src/model_registry.py:375-395`); MNIST is declared `ndim=2` and cascor-compatible (`src/model_registry.py:135`, `:172`, gating `:311-318`, `:398-414`).
  - Cosmetic/UX severity; design a type-aware parameter panel or per-type visibility, and decide what `ndim` should mean in the hint text.

**Error-string grep keys** (all verified sources — use these to trace symptoms through logs and code):

- `Failed to apply (` → canopy `dashboard_manager.py:5833`; `Failed to create snapshot` → canopy `main.py:2147-2152` + `hdf5_snapshots_panel.py:841-845`; `Training could not be started:` → canopy `main.py:3109`.
- `juniper-data fetch failed:` → cascor `manager.py:2962`; `Request failed (` → data-client `client.py:319`; `Internal server error` → juniper-data `app.py:148`.
- In canopy logs (`juniper-canopy/logs/juniper-canopy_*.log`; cascor logs `juniper-cascor/logs/juniper-cascor_*.log`) also grep: `WS set_params failed`, `Cold-swap restart`, `unrecognized_ws_frame`, `Failed to fetch canopy params`.

**Read-only live probes** (safe against the running stack; if canopy's API-key auth is enabled you may receive 401 — note it and rely on logs/code instead; the dashboard's own polls use the internal token from `src/frontend/internal_api.py:63-79`):

```bash
util/get_cascor_status.bash                                  # juniper-ml helper: GET /v1/training/status (CASCOR_HOST/CASCOR_PORT, defaults localhost:8201)
curl -s http://localhost:8201/v1/metrics | head -c 400
curl -s http://localhost:8201/v1/network/topology | head -c 400
curl -s http://localhost:8050/api/status | head -c 400
curl -s http://localhost:8050/api/state | head -c 400
curl -s "http://localhost:8050/api/metrics/history?limit=3" | head -c 400
curl -s http://localhost:8100/v1/health
```

**Conventions** (current canonical values): line length 512 for all linters; notes are named `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<DESCRIPTION-PHRASE>.md`; generated prompts live in `prompts/generated/`; deliverable location for design docs: `notes/`; thread-handoff threshold 95-99%; PR descriptions SHOULD cite `JR-<REPO>-<AREA>-<NNN>` requirement IDs with verbs Closes / Partially closes / References / Supersedes.

## Primary Objective

Produce ONE clear, owner-actionable planning document — a diagnosis-of-record plus a phased fix plan — covering, at minimum, ALL issues in the inventory above (I-1 – I-7) and the triaged prior-doc §6 follow-ups, grounded in the real repositories and the live stack, with every factual claim verified, and with implementation latitude preserved wherever the owner has not pinned a design.

## Assigned Tasks / Directives

1. **Preflight.** Verify repo freshness (`git -C <repo> fetch origin && git -C <repo> status`) for the four target repos; record the HEADs your document grounds against. Re-confirm a sample of the anchors in `## Resources` (at least the load-bearing ones per issue) before relying on any; if an anchor does not resolve, re-locate the symbol and record the correction — never carry a stale anchor forward.
2. **Required reading.** Read the two prior-work notes documents and the PR subjects listed above; extract the four §6 follow-up items into this plan's scope — each becomes a triaged entry: in-scope and assigned to a roadmap work unit (phase + repo), or explicitly deferred with a reason.
3. **Live evidence (read-only).** Run the probe pack above against the running stack; sweep the current canopy/cascor/data logs with the grep keys; capture what the backend reports vs what the UI showed (the screenshots' values are operator observations, not ground truth — verify everything independently). Do NOT restart services, stop training, click mutating controls, or POST to the live stack.
   - If the stack is not running when you start, record that, skip the live probes, and rely on logs plus the isolated stack (directive 4) — never start or restart the operator's stack yourself.
4. **Mutating repros (isolated only).** Where a diagnosis needs a mutating reproduction (Apply Parameters, Create Snapshot, MNIST start, Stop & Restart), use an ISOLATED second stack on alternate ports launched from the repos (the prior doc's §7 E2E pattern, e.g. cascor 8202 + canopy 8051). Where isolation is impracticable, record the repro as pending owner approval.
   - A repro that generates datasets (I-5) must ALSO launch its own juniper-data on an alternate port (e.g. 8101) and point the isolated cascor's `JUNIPER_DATA_URL` at it — never POST to the operator's juniper-data on 8100.
   - Note: browser automation cannot type into Dash `dbc.Input(type=number)` fields — drive parameter repros via the REST surface instead.
5. **Per-issue diagnosis.** For each of I-1 – I-7: confirm or refute each listed hypothesis with evidence (log lines, probe output, code reading); state the confirmed root cause(s) with `file:line` anchors; where evidence is unobtainable read-only, mark the hypothesis OPEN and say exactly what experiment would close it.
6. **Per-issue fix design.** For each issue, provide:
   - options with trade-offs where the choice is architectural — mandatory for I-1's update-path posture (e.g. re-enable gated REST polls via a WS-health heartbeat, extend Path B to write tiles/stores, hybrid, or kill-switch default change) and for I-5's ship-vs-gate product decision;
   - the chosen design and why;
   - the tests that will pin it (name the real suites/files, e.g. canopy `src/tests/`, and note canopy's UI-harness split);
   - rollback/compatibility notes where behavior changes (e.g. anything relying on current `/api/train/start` semantics).
7. **Cross-cutting themes.** Address as first-class design sections:
   - error-surfacing uniformity — toasts must carry upstream detail (the `:5833` and `:2147-2152` flattening patterns);
   - WS-gate health semantics — sticky `metricsReceived`/`topologyReceived` vs actual delivery liveness;
   - partial-success reporting — I-4's applied-yet-failed contract, including cascor's silent `hasattr` drop at `manager.py:3241`;
   - silent-failure elimination for control callbacks (`restart_with_new_dataset`, `apply_dataset`);
   - the dead-end stores (`ws-state-buffer`, `ws-candidate-progress-buffer`) — wire or remove.
8. **Roadmap.** A phased fix roadmap of PR-sized work units: table with phase, repo, branch type, summary, dependency order (upstream repos before downstream consumers: juniper-data → juniper-data-client → juniper-cascor → juniper-cascor-client → juniper-canopy → juniper-ml/deploy), verification per unit, and which issues (I-numbers) each unit closes. Fixes land as PRs per repo convention; one work unit per PR.
9. **Risks + verification strategy.** Risks of each major design; a verification plan naming the repos' REAL test entry points (canopy: `pytest` per its AGENTS.md; cascor: `bash src/tests/scripts/run_tests.bash`; juniper-data: `pytest juniper_data/tests/ -v`) plus the isolated-stack E2E pattern; explicitly plan a regression test for every confirmed root cause.
10. **Multi-agent validation (mandatory before the document is final).**
    - Dispatch at least two INDEPENDENT read-only verification sub-agents (fresh context each, no shared conversation) with distinct lenses: Lens 1 re-probes EVERY `file:line`, symbol, route, port, env var, version, and PR number cited in the draft against the pinned HEADs (`git -C <repo> ...`, `sed -n`, `grep -n`); Lens 2 re-reads the implicated code and challenges every root-cause and behavioral claim (does the code actually do what the document says?).
    - Additionally dispatch a third skeptical-review sub-agent to attack the chosen designs (simpler alternative missed? interaction with the merged #437/#438/#396 behavior? consumer breakage?).
    - Resolve every finding by re-reading the source (never by vote); bound the loop at 3 rounds; unresolved items become explicitly-marked open questions.
    - Record the outcome in the document (agents dispatched, lenses, findings raised/resolved).
11. **Finalize.** Lint the document and produce the acceptance evidence (commands below).

## Key Deliverables & Requirements

- ONE document written to the `notes/` directory of the juniper-ml checkout the session is running in (report its absolute path), named `JUNIPER_<YYYY-MM-DD>_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md` (`<YYYY-MM-DD>` = the authoring date). Refuse and report if the path already exists.
- Required document structure (all sections present and non-empty): Executive Summary; Reported Symptoms; Architecture Context; Per-Issue Diagnosis & Fix Design (one subsection per I-1 – I-7: Symptom / Evidence / Root cause / Options & trade-offs (where architectural) / Chosen design / Tests); Cross-Cutting Themes; Phased Fix Roadmap; Risks; Verification Plan; Coverage Matrix; Validation Record; Open Questions.
- The Coverage Matrix maps every inventory issue (I-1 – I-7), every reported-symptom bullet, and every prior-doc §6 follow-up to the document section that addresses it (or an explicit deferral with reason) — nothing silently dropped.
- Every cited `file:line` is real at the recorded HEADs; every hypothesis from the inventory is explicitly confirmed, refuted, or marked OPEN with the evidence that decided it; refuted hypotheses are recorded as refuted, not silently omitted.
- The Validation Record documents the multi-agent verification of directive 10 with zero unresolved grounding findings.
- **Acceptance criteria** (run from the root of that same juniper-ml checkout; all must hold, with command output as evidence):

```bash
ls notes/JUNIPER_*_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md
npx markdownlint-cli --config .markdownlint.yaml "notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md"   # exit 0
```

## Constraints

- **Document only** — do NOT modify source code, configuration, or CI in any repo; this task produces a plan, not an implementation. Committing/PR-ing the finished document follows the owner's instruction at dispatch time; default is to leave it uncommitted and report.
- **Live-stack safety** — the running cascor holds live training state: read-only GETs only; never restart canopy/cascor/data, never stop/start/reset training, never apply parameters or datasets, and never create snapshots against the operator's stack. Mutating repros happen only on an isolated alternate-port stack (directive 4) or with explicit owner approval.
- **Model guardrails (Fable 5)** — this planning task develops no dual-use or exploit code; perform ALL work with the fable-5 model, including sub-agents (override any agent-frontmatter model pin with fable). If a specific component proves impossible on fable-5, split out ONLY that minimal component to opus-4.8 and record what was handed off and why in the Validation Record.
- Never invent APIs, paths, symbols, flags, versions, ports, or env-var names: if it is not in this prompt's grounding, the cited prior documents, or your own verified probing, do not assert it — re-confirm each cited `file:line`/symbol in-task and STOP-and-report rather than invent if one does not resolve.
- Treat this prompt's hypotheses as hypotheses: the ranked candidates in the inventory are leads to test, not conclusions to transcribe. Where live evidence contradicts them, the document records the contradiction and follows the evidence.
- The screenshots' UI values are operator observations of a possibly-buggy UI — never cite them as backend truth without independent confirmation.
- Do not weaken, skip, or propose deleting ANY existing test as part of any fix design.

## Finalize / Validation

- Re-confirm every `file:line` anchor cited in the finished document resolves in the actual repos at the recorded HEADs; drop or flag any that does not rather than inventing.
- The directive-10 multi-agent validation is the ratification gate: the document is not final until its Validation Record shows every grounding finding resolved and the skeptical design review answered.
- Produce the acceptance evidence (the `ls` + `markdownlint` commands above) and report the document path plus a one-paragraph summary of the chosen designs and the roadmap shape.
