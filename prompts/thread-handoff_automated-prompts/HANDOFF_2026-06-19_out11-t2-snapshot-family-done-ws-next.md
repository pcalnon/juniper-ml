# OUT-11 service-core T2 — snapshot family done, WebSocket (step 2) next

Continue the **`juniper-service-core` T2-surface build (OUT-11)** — next is **step 2, the WebSocket
subsystem** — per the ratified design + as-built status in
`notes/JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md` (§5.6 module ledger, §6 build
plan, **§9 as-built + deferred follow-ups**). Approach is "extract base, keep cascor subclass," proven
by model-core's **regression** `ReferenceGrowableModel` stub (RK-6 guard). cascor is untouched; its
adoption is WS-6.

## Completed so far (this session — all MERGED to `main`)

- **Step 1a (#473):** `ServiceLifecycleManager` (background-threaded orchestrator + cooperative
  pause/stop at `TrainingEvent` boundaries), `LifecycleStateMachine` (open-string phase),
  `LifecycleMonitor` (folds the 5 model-core `TrainingEvent` types), generic
  `/v1/{training,metrics,dataset,network}` routes + shared `ResponseEnvelope`. Also repaired
  `ci-service-core` (RED on main since #422) by adding `numpy>=1.24` to service-core deps.
- **Step 1b (#476):** snapshot persistence — `SnapshotStore` (injected model-core `ModelSerializer`
  `+` JSON sidecar of lifecycle state), manager `save`/`list`/`get`/`load`(→`INVESTIGATING`)/
  `restore_for_retrain`(→`STOPPED`)/`resume_from_snapshot`(→`RESUME_READY`), `/v1/snapshots` routes.
- **Step 1c (#478):** snapshot replay — `ReplaySession` (timed playback; play/pause/seek/speed/
  range/stop + an injectable `on_frame` sink), manager `start_replay`(→`REPLAYING`)/`replay_control`/
  `stop_replay`/`get_replay_state`, `/v1/snapshots/{id}/replay[/control]`.
- Merged main is green: **107 service-core tests pass.** Design-doc §9 records the as-built split + the
  deferred follow-ups FW-1..4 (incl. **dataset-swap-history kept cascor-only** — FW-1).

## Remaining work

1. **Step 2 — WebSocket.** Extract cascor `src/api/websocket/{manager,messages,training_stream,
   control_stream,control_security}` onto model-core `TrainingEvent`/state/metrics frames.
   `control_stream` → an injectable `CommandExecutor`. **DROP** `cascade_add`/`candidate_progress`
   frames + `worker_stream` (worker = step 3). The push source is the existing `LifecycleMonitor`
   `+` the **`ReplaySession.on_frame` sink** (built in 1c for exactly this). Contract test drives every
   channel with the stub model.
2. **Step 3 — worker-pool infra** (registry/coordinator/audit/metrics/security; defer the generic
   `Task`/`TaskResult` envelope to WS-8 per OQ-11).
3. **Step 4 — publish-rail** (`juniper-service-core-v*` tag → PyPI), `[tools]` drift-lint, the
   `test_pyproject_extras` lockstep, and a version bump (currently `0.1.0`; `test_smoke` asserts it).
4. **Deferred FW-1..4 (§9):** generic dataset-swap-history; replay history-continuation; replay
   live-push (wire the `on_frame` sink in step 2); cascor topology/weight replay (stays cascor-side).

## Key context

- **Read PR #475 (WS-5 & WS-6 reevaluation) FIRST** — it may re-sequence steps 2/3 (WS-6 is cascor's
  adoption of this package).
- **Build recipe:** run on conda env `JuniperCascor1` with
  `PYTHONPATH=<worktree>/juniper-service-core` to **shadow the stale editable install** (it's pinned to
  a different worktree — verify `import juniper_service_core; print(__file__)` points at YOUR worktree).
  Lint = flake8 with the repo pre-commit args (`--max-line-length=512
  --extend-ignore=E203,E265,E266,E501,W503,E722,E402,E226,C409,C901,B008,B904,B905,B907,F401,F811
  --max-complexity=20 --select=B,C,E,F,W,T4,B9`) + `ruff check --select F`.
- **CodeQL gotcha:** every new lazily-exported `__all__` name MUST be added to the `if TYPE_CHECKING:`
  import block in `juniper_service_core/__init__.py`, or CodeQL `py/undefined-export` fails (the lazy
  PEP 562 `__getattr__` is invisible to it).
- **CI gotcha:** `ci-service-core.yml` triggers only on PRs to `main` (path-scoped). A stacked PR
  (base ≠ main) gets **no** service-core CI — open step-2 PRs against `main` (or retarget before merge).
- **Dependency-free top-level import** is load-bearing (`test_smoke` blocks `fastapi`/`pydantic_settings`
  in a subprocess) — keep websocket modules off the eager import path (lazy export).
- **Dup-guard:** `gh pr list` + scan `/home/pcalnon/Development/python/Juniper/worktrees/` AND
  `.claude/worktrees/` before claiming work (concurrent sessions are active).
- Paul approves all merges + PyPI/deploy gates — drive to the gate, then hand off.

## Verify starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin
git log origin/main --oneline -4                                   # #478 (1c), #476 (1b), #473 (1a) present
ls juniper-service-core/juniper_service_core/lifecycle/            # snapshots.py + replay.py present
ls /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/websocket/   # the step-2 extraction source
```

## Git / branch state

- `origin/main` has 1a/1b/1c merged (tip `857dec2`, step 1c #478). No step-2 code exists yet.
- Stale local branches whose PRs merged (prune in cleanup): `feat/out-11-service-core-t2-snapshots`,
  `feat/out-11-service-core-t2-replay`, `docs/out-11-service-core-t2-plan`. Step 2 lands on a fresh
  branch off `main`, in a worktree under `/home/pcalnon/Development/python/Juniper/worktrees/` (or the
  harness's `.claude/worktrees/`).
