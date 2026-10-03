# Thread Handoff Prompt — 2026-06-21 (WS-6 B-phase: B1/B2a/B2b shipped → B3 `on_event` sink next)

Continue the **juniper-cascor WS-6 B-phase** at **PR-B3** — replace the monkey-patch monitoring with a
`CascorModel.fit(on_event=…)` sink. The prior thread shipped **B1/B2a/B2b** (all merged + CI-green) and ran
the **B3 spike**: full migration is **FEASIBLE — the kill-criterion does NOT fire**. **OQ-B1 is DECIDED:
proceed with the full migration.** Design-first → staged PR; keep golden + conformance + a NEW
WS-granularity test green throughout. Paul approves all merges + PyPI/deploy gates (drive to the gate, hand off).

## Completed in the prior thread (verify, don't redo)

- **B1 — cascor #345** (`8c9ade2`): production `CascorModel(GrowableModel)` wrapper + manager holds
  `self.model` with a back-compat `self.network` get/set property; 4 assignment sites converted (incl. HDF5
  re-wrap); `juniper-model-core>=0.2.0,<0.3.0` runtime dep + lockfile.
- **B2a — cascor #346** (`7c07ce3`): seam attribute renames (`training_monitor→monitor`,
  `_training_lock→_lock`, `_stop_requested→_stop_event`, `_network_params→_params`, `has_network()→has_model()`
  - deprecated `has_network` alias); ~160 call sites.
- **B2b — cascor #347** (`f3ec5d9`): `start_training` → model-core `fit(X, y, *, X_val, y_val, …)` shape;
  snapshot verbs `load_snapshot`/`restore_for_retrain`/`resume_from_snapshot` return a status dict (via
  `_snapshot_result`) — routes check `result["loaded"]`, HTTP responses byte-identical.
- **B3 spike** (3 sub-agents): on_event payload is an arbitrary dict (conformance checks only order/seq);
  CCN has the native hooks; the only catch is the per-candidate stream is async (worker processes).

## B3 design (decided — from the spike)

- `CascorModel.fit` streams the **coarse** sequence (`training_start`/`epoch_end`/`unit_added`/`training_end`)
  **during** fit by wiring CCN's **native callback hooks** — `train_output_layer(on_epoch_callback=)`,
  `grow_network(on_grow_iteration_callback=)` + instance-attr fallbacks (`_output_epoch_callback`,
  `_grow_iteration_callback`). **No CCN-invasive change.**
- Manager `_handle_event(on_event)` updates the same `TrainingMonitor`/`TrainingState` the read routes
  serialize (replacing `monitored_fit`/`grow`/`validate`'s coarse projection).
- **RETAIN** the `_persistent_progress_queue` drain→`candidate_progress` broadcast for the **50 Hz**
  per-candidate `/ws/training` stream — it's async (worker processes), can't ride synchronous `on_event`.
- Remove `_install_monitoring_hooks`/`_restore_original_methods`, **preserving** their FSM transitions,
  start/end bookkeeping, metrics extraction, and stop/pause interrupt (the interrupt already rides CCN's
  native hooks, so it is independent of the removed `fit`/`grow_network` wrapping).
- Design against the `ServiceLifecycleManager` seam (`run` → `self.model.fit(on_event=self._handle_event)`)
  so the deferred A-phase inherits `run`/`_handle_event` verbatim.

## Remaining work

1. **B3** — the above, staged + spike-gated. **NEW WS-granularity assertion** (real fit+grow → `/ws/training`
   still emits per-candidate frames) is the kill-criterion exit test, alongside the REST golden + conformance.
2. **B4** — point `test_model_core_conformance` at the production `CascorModel` (native conformance); retire
   the test-only `CascorModelCoreAdapter` (cascor #341).
3. **A-phase (6a)** — BLOCKED: needs `juniper-service-core` **0.2.0** on PyPI (ml **#502** OPEN — T2 is merged
   but unpublished) + soak. Not this task; deferred per DR-1.

## Current Juniper state (verified 2026-06-21 — see `notes/JUNIPER_2026-06-21_JUNIPER-ECOSYSTEM_DOCS-REALITY-AUDIT.md`)

- **PyPI**: model-core 0.3.0 · service-core 0.1.0 (T1; T2 merged-unpublished, #502) · recurrence 0.1.1 ·
  recurrence-model 0.1.4 · recurrence-client 0.1.0 · juniper-data 0.8.0.
- **WS-5 canopy**: A0 registry + 3-D dataset viz shipped (#372, #374–#379); regression harness gating;
  A1 training-integration NOT started (D1 paradigm unratified — DR-2, recommend D1-A). Concurrent-owned.
- **recurrence**: WS-4/4b shipped; DP-3 implementing in parallel (Rung-2a RFF in model 0.1.4; P2-remaining =
  ml #501 handoff). Concurrent-owned.

## Key context / lessons (cost real time)

- **Read `origin/main`, never stale local working trees** (`git -C <repo> fetch` first); sibling checkouts lag.
- **Line-based sed/grep MISS multi-line calls + string-form refs** (`getattr`/`patch.object("name")`) — always
  sweep multi-line-aware + grep quoted forms; the unit lane catches stragglers.
- **cascor's pytest summary line is suppressed** (os._exit flush) — trust the pytest **exit code**, not a
  (missing) "N passed" line. Run the gate on **JuniperCascor1** with serial env vars
  (`OMP_NUM_THREADS=1 … CASCOR_NUM_PROCESSES=1`).
- **Helper classes** `_WeightHistoryRecorder`/`_WeightCache`/`_ReplaySession` share the seam names —
  attribute-qualify any rename.
- Paul merges fast; base new work off fresh `origin/main`; one clean commit per PR (squash-merge strands
  follow-ups). `notes/` is markdownlint-excluded from CI — markdownlint edited docs manually (line-length 512).

## Verification commands (confirm starting state)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git fetch origin
git log origin/main --oneline -5        # f3ec5d9 #347 (B2b), 7c07ce3 #346, 8c9ade2 #345
git grep -n 'def _install_monitoring_hooks' origin/main -- src/api/lifecycle/manager.py  # the monkey-patch B3 removes
git grep -nE 'on_epoch_callback|on_grow_iteration_callback' origin/main -- src/cascade_correlation/cascade_correlation.py  # CCN native hooks
gh api repos/pcalnon/juniper-cascor/rulesets/15081045 | python3 -c 'import sys,json;print(json.load(sys.stdin)["name"])'  # gate armed
gh pr view 502 -R pcalnon/juniper-ml    # OUT-11 0.2.0 publish (A-phase unblocker)
```

## Git / PR status (2026-06-21)

- cascor `origin/main` = `f3ec5d9` (#347). B1/B2a/B2b worktrees retired. **B3 worktree READY:**
  `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--refactor--ws6-bphase-b3-on-event-sink--20260621-1902--f3ec5d9b` (branch `refactor/ws6-bphase-b3-on-event-sink`, off `f3ec5d9`). No B3 WIP yet.
- Plan: juniper-ml **#485** `notes/JUNIPER_2026-06-19_JUNIPER-CASCOR_WS6-BPHASE-MODEL-CORE-ADOPTION-BUILD-PLAN.md` §5 PR-B3.
  Decision: juniper-ml **#475** (DR-1). Predecessors: cascor #340/#341 (gate), #345/#346/#347 (B1/B2a/B2b).
- **Memory**: `project_cascor_ws6_bphase_plan_2026-06-19.md` is the canonical session record (B-phase shipped,
  B3 spike + OQ-B1 decision, the recurring gotchas).
