# Thread Handoff Prompt — 2026-06-21 (OUT-11 T2 step 3a shipped → step 3b: worker coordinator + `/ws/workers`)

Continue **OUT-11 — `juniper-service-core`'s T2 surface** (the model/middleware refactor; the last
prerequisite for the WS-6 cascor cutover). The prior thread shipped **step 2 (WebSocket subsystem)**
and **step 3a (worker-pool foundations)**; the next piece is **step 3b — the `WorkerCoordinator` +
the `/ws/workers` stream**, the design-heavy half of the worker subsystem.

Approach (unchanged, ratified): **"extract base, keep cascor subclass,"** driven by a stub — de-cascor
cascor's modules onto the `juniper-model-core` interfaces. **cascor is untouched; its adoption is WS-6.**
Canonical plan: `notes/JUNIPER_2026-06-19_JUNIPER-ML_SERVICE-CORE-T2-SURFACE-DESIGN-AND-AUDIT.md` — **§5.6** (the
per-module extraction ledger + the OQ-11 worker verdict), **§6** (build plan), **§9** (as-built + the
step-3 `3a`/`3b` split, updated by #492).

## Completed in the prior thread (verify, don't redo)

- **#484 (MERGED)** — **step 2 WebSocket subsystem** (`juniper_service_core/websocket/`): `WebSocketManager`
  (seq / replay buffer / oversized-message chunking / thread-safe broadcast; cascor `api.observability`
  emissions dropped) + plain-dict message builders (the generic 7 frames; `cascade_add` /
  `candidate_progress` dropped) + control-path security (`validate_control_origin` / `LeakyBucket` /
  `HandshakeCooldown`) + `training_stream` / `control_stream` handlers + an **injectable `CommandExecutor`**
  (control-dispatch adapter; default `LifecycleCommandExecutor`) + `build_websocket_router`
  (`/ws/training` + `/ws/control`) + `attach_websocket` bridge. A new additive `frame_sink` on
  `ServiceLifecycleManager` pushes live-training **and** replay frames (resolved design **FW-3**).
- **#488 (MERGED)** — de-flaked `test_replay_controls_are_synchronous` (a step-1c daemon-vs-`step()` race;
  dropped `start()` from the synchronous-surface test).
- **#492 (MERGED)** — **step 3a worker-pool foundations** (`juniper_service_core/workers/`): `WorkerRegistry`
  / `WorkerRegistration` / `WorkerRegistryFullError` + security (`TLSConfig` mTLS, `ConnectionRateLimiter`
  token-bucket, `AnomalyDetector` generalized from cascade `correlation` → a generic bounded quality
  `score`) + audit (`AuditLogger` / `WorkerMetrics` / `AuditEventType`) + `WorkerRegistryCollector`
  (Prometheus bridge; configurable `metric_prefix`, pending-tasks via an injected callable — **no
  coordinator import**). De-cascored (loggers renamed, `cascor_constants` → local consts); lazy-exported;
  17 unit tests; full suite **149 green**.

## Current state (verified 2026-06-21)

- `juniper-service-core` now ships **T1** (`app`/`settings`/`security`/`middleware`/`health`/`launcher`/
  `secrets`) **+ T2 routes + lifecycle** (steps 1a/1b/1c) **+ websocket** (step 2) **+ worker pool-infra
  foundations** (step 3a). Still version **`0.1.0`** (`test_smoke` asserts it) — the publish-rail is step 4.
- The **injectable-seam pattern is proven twice**: the step-2 `CommandExecutor` (control-channel dispatch
  read off `app.state.command_executor`) and the step-3a metrics `pending_tasks_source` callable. Step 3b's
  coordinator follows the same shape — **the cascade specifics are injected, not hard-coded.**
- `WebSocketManager` currently advertises `DEFAULT_WS_ENDPOINTS = ("training", "control")` — step 3b adds
  the `"worker"` endpoint bucket.

## Remaining work — step 3b (then step 4)

1. **`WorkerCoordinator`** — extract cascor `src/api/workers/coordinator.py` (522 lines, **not yet read** by
   the prior thread) as a **generic** coordinator: the model-agnostic parts are assignment bookkeeping
   (which idle worker gets which task), per-task **timeout / retry**, result **collection**, and
   `pending_tasks_count()` (which the step-3a `WorkerRegistryCollector` already consumes via its injected
   callable). The cascade-specific parts — **building** the task-assignment payload and **parsing +
   reducing** results (correlation-based candidate selection) — are **injected** behind a task-protocol /
   result-reducer seam (the step-2 `CommandExecutor` analogue). cascor injects its cascade schema + reducer.
2. **`/ws/workers` stream** — extract cascor `src/api/websocket/worker_stream.py` (384 lines) onto the
   step-2 `WebSocketManager` (registration handshake → `WorkerRegistry`, heartbeat, dispatch/collect
   transport). Add `"worker"` to `DEFAULT_WS_ENDPOINTS`. This is the module **deferred from step 2**.
3. **DEFER (WS-8 / cascor-side, per OQ-11):** the cascade-bound `Task` / `TaskResult` envelope — cascor
   `src/api/workers/protocol.py` (`candidate_index` / `candidate_data` / `correlation` / `all_correlations`
   / `numerator` / `denominator` / `best_corr_idx`; the wire enum lives in the separate
   `juniper_cascor_protocol` PyPI package) — and `src/parallelism/task_distributor.py`'s cascade task tuples
   + the correlation reduction. Do **not** build a generic envelope now; the coordinator dispatches over
   **opaque payloads** + the injected codec/reducer.
4. **Contract test** — drive a **stub worker** through register → heartbeat → dispatch → collect → timeout
   with a trivial injected codec/reducer (RK-6: no cascade assumptions). Update design-doc **§9** (3b as-built).
5. **Step 4 (after 3b)** — publish-rail (`juniper-service-core-v*` tag → PyPI, the cut-a-GitHub-Release
   convention), the `[tools]` extras pin + drift-lint, the `test_pyproject_extras` lockstep, and a version
   bump off `0.1.0` (update `test_smoke`'s assertion in the same PR).

## Key context / lessons (read these — they cost real time to learn)

- **The seam is the whole job.** Read `coordinator.py` + `task_distributor.py` **first** (the prior thread
  read only `protocol.py` + `registry.py`). Find the exact line where cascade data enters: cascor builds
  `TaskAssignment(candidate_data=…)` and reduces results by `correlation` / `best_corr_idx`. Everything
  around that (idle-worker selection, timeout, retry, collect, pending count) is generic. Inject a small
  protocol — e.g. an object on `app.state` with `build_task(...) -> dict` and `reduce_results(list) -> Any`
  — exactly as step 2 injected `CommandExecutor` and step 3a injected `pending_tasks_source`.
- **Build recipe.** conda env `JuniperCascor1` with `PYTHONPATH=<worktree>/juniper-service-core` to **shadow
  the stale editable install** (verify `import juniper_service_core; print(__file__)` points at YOUR
  worktree). Lint gate = `flake8` with the repo pre-commit args (`--max-line-length=512
  --extend-ignore=E203,E265,E266,E501,W503,E722,E402,E226,C409,C901,B008,B904,B905,B907,F401,F811
  --max-complexity=20 --select=B,C,E,F,W,T4,B9`) + `ruff check --select F`. Fix `I001` import-sorting via
  `ruff check --fix --select I` (service-core's full `ruff E,F,W,B,I,N` is NOT CI-enforced — only `F` +
  flake8 are — but keep imports sorted).
- **Lazy-export discipline (CodeQL).** Every new public name goes in `juniper_service_core/__init__.py` in
  **all three** places: the `if TYPE_CHECKING:` import block (or CodeQL `py/undefined-export` fails — the
  PEP 562 `__getattr__` is invisible to it), `__all__`, and `_LAZY_EXPORTS`. The `/ws/workers` handler needs
  `fastapi`, so keep `worker_stream` / the coordinator-if-it-imports-fastapi **off the eager import path**;
  `registry`/`security`/`audit`/`metrics` are stdlib-only and already lazy. `test_smoke` blocks
  `fastapi`/`pydantic_settings` in a subprocess — the **dependency-free top-level import is load-bearing**.
- **CI gotcha.** `ci-service-core.yml` triggers **only on PRs to `main`** (path-scoped). Open the 3b PR
  against `main`, never stacked on another feature branch (a stacked PR gets **no** service-core CI).
- **BOT-CORRUPTION (cost real time on #484).** While an OUT-11 PR sat open and green, automation (CodeQL
  "Empty except" autofix + Cursor bots + a manual "fixed syntax issue" commit) pushed to the branch and
  **silently corrupted it** — one commit overwrote `pong_received = asyncio.Event()` with a hallucinated
  `logging.debug("…disconnected")`, breaking every control test with `NameError`. **After ANY bot push to a
  PR branch, re-pull + re-run CI before treating it as merge-ready** — do not assume your last green state
  holds.
- **Docs hygiene.** `notes/` and `prompts/` are excluded from the CI markdownlint hook, but the
  **`Documentation Links` validator does NOT exclude `prompts/`** — keep handoff docs **link-free** (use
  backtick code-span paths, never inline Markdown links). When editing `notes/` docs, run
  `npx markdownlint-cli@0.42.0 --config=./.markdownlint.yaml <doc>` (line-length 512; table rows can't wrap
  — trim cells).
- **Process guardrails.** No merge without Paul's explicit per-PR "merged" signal **and** `gh pr view` =
  MERGED; PyPI/deploy gates are Paul-driven (don't self-approve). Dup-guard before building: `gh pr list` +
  scan `worktrees/` and `.claude/worktrees/` (concurrent sessions are active — e.g. #491/#493 DP-3
  recurrence docs landed alongside this work).

## Verification commands (confirm starting state)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin
git log origin/main --oneline -5                    # #492 (3a), #484 (step 2) present
# step 3a foundations on main (expect 5 files):
git ls-tree origin/main --name-only juniper-service-core/juniper_service_core/workers/
# the step-3b extraction sources (not yet read: coordinator + worker_stream):
wc -l ../juniper-cascor/src/api/workers/coordinator.py \
      ../juniper-cascor/src/api/websocket/worker_stream.py \
      ../juniper-cascor/src/parallelism/task_distributor.py
# baseline green (149) on JuniperCascor1 with the PYTHONPATH shadow:
conda activate JuniperCascor1
cd juniper-service-core && PYTHONPATH="$PWD" python -m pytest tests/ -q
# dup-guard (expect no open 3b/coordinator PR):
gh pr list --state open | grep -iE 'service-core|coordinator|worker'
```

## Git / PR status (2026-06-21)

- **Merged this arc:** #484 (step 2), #488 (de-flake), #492 (step 3a). All on `origin/main`
  (tip `65436a8` is #492; current tip `e3054cc` after concurrent recurrence docs #491/#493).
- **No open service-core PRs.** Step 3b lands on a fresh branch off `origin/main`, in a worktree under
  `/home/pcalnon/Development/python/Juniper/worktrees/` (or the harness's `.claude/worktrees/`).
- **Stale local branches to prune** (PRs merged): `feat/out-11-service-core-t2-websocket`,
  `fix/out-11-replay-test-race`, `feat/out-11-service-core-t2-workers` (and this handoff's
  `docs/out-11-t2-step3b-handoff` once its PR merges).
- **Memory:** `project_ws2_juniper_service_core_2026-06-14.md` is the canonical session record (the full
  T1→T2 arc, the step-3 `3a`/`3b` split, the seam pattern, and the bot-corruption lesson).
