# Handoff — cascor #319 defect #3 (remote collect timeout) — 2026-06-03

Continue **juniper-cascor #319**: with remote workers connected, cascade-correlation training cannot grow hidden units on the dual-path. Two of four defects are fixed and merged; pick up **defect #3**, the remaining unlock.

## Completed so far

- **cascor#316** (merged) — `current_hidden_units` status field; live-verified working.
- **cascor#321** (merged, commit `fff242d` on main) — fixed the two remote-dispatch **crashes** in `_dispatch_to_remote_workers` + added `repr(e)`+traceback diagnostics:
  - **#1 `KeyError(1)`** (the trigger): `training_inputs[1]/[4]/[5]` indexed the OPT-5 SharedMemory **dict** → now sourced from `self.candidate_epochs/learning_rate/display_frequency`.
  - **#2 `IndexError`**: `task_specs[tr.candidate_id]` indexed the local subset by the **global** pool index → now mapped by `candidate_index`, skipping unknown results.
  - Regression tests in `src/tests/unit/test_candidate_result_collection_dualpath_regression.py::TestRemoteDispatchCandidateIdMapping`.
- Result: the infinite hang is gone; network now grows **0→1 and completes cleanly**.

## Remaining work (this task)

**Defect #3 (the unlock):** `_dispatch_to_remote_workers` (`src/cascade_correlation/cascade_correlation.py:~1195`) calls `self._worker_coordinator.collect_results(timeout=getattr(self, "candidate_training_shutdown_timeout", 120.0))`.

- On the deploy stack that resolves to **~10s**, but candidate training takes **~70s**, so `collect_results` (`src/api/workers/coordinator.py:~333`, does `self._results_ready.wait(timeout)`) **always** returns `0/2` → `TaskDistributor._execute_remote_with_fallback` retries the 2 tasks locally every round → effective 38-candidate pool, low yield, network caps at 1 unit.
- The remote tier never contributes.
- The fix is to give the remote collection a budget scaled to candidate training (e.g. derive from `candidate_epochs`), not the *shutdown* timeout.
- Beware: too long risks a hang if a worker dies — pair with the worker-liveness check.

**Defect #4 (smaller, optional same PR):** remote `TaskResult` (`coordinator.py:42-57`) has no `round_id`; add it + attach in `submit_result` so #315's RC-5 stale-round filter protects the remote leg.

## Verify (mandatory — live, dual-path)

Unit tests mock the coordinator and will NOT catch #3. The `juniper-deploy` stack is up (2 workers = dual-path).

- Repro: `KEY=$(cat /home/pcalnon/Development/python/Juniper/juniper-deploy/secrets/juniper_cascor_api_keys.txt)`, then `POST http://localhost:8201/v1/training/reset`, then `POST /v1/training/start` with header `X-API-Key: $KEY` and body `{"epochs":1000,"dataset":{"generator":"spiral","params":{"n_per_spiral":100,"n_spirals":2}},"params":{"max_hidden_units":3,"output_epochs":20,"candidate_epochs":30,"candidate_pool_size":40}}`.
- Poll `GET /v1/network` → `data.hidden_units`. **Success = reaches 2–3** (was capped at 1). Watch logs for `TaskDistributor: ... remote tasks completed successfully` (good) vs `Remote returned 0/2` (the bug).
- Rebuild the image from your worktree (deploy builds from the main checkout, so build directly): `docker build -t juniper-cascor:latest <worktree>` then `cd juniper-deploy && docker compose --profile full up -d --wait juniper-cascor`. Confirm the fix is in-container via `docker exec juniper-cascor grep ...`.

## Key context / gotchas

- **Always `repr(e)`+traceback before theorizing** — a swallowed `str(e)`="(1)" hid a `KeyError(1)`; the first root-cause guess (the IndexError) was wrong and only the live-verify + diagnostic patch corrected it.
- Deterministic 38/2 split = `TaskDistributor._split_tasks` caps remote at #available workers; `distribute_and_collect` runs local-then-remote sequentially.
- cascor#315 grew 0→2 on the dual-path on 2026-05-31, so #3 may be load/timing-sensitive or a recent regression (#318 deps bump is the bisection suspect — see #319 comment).
- Full detail in [juniper-cascor#319](https://github.com/pcalnon/juniper-cascor/issues/319) (4-defect table + live-verify findings) and memory `project_cascor_dualpath_candidate_stall_2026-06-02`.

## Git / setup

- `main` @ `fff242d` (has #321). Create a fresh worktree per the convention:
  `cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git fetch origin && git worktree add /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--cascor-319-remote-collect-timeout--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 origin/main) -b fix/cascor-319-remote-collect-timeout origin/main`
- Env for tests: `conda activate JuniperCascor1`. Verify start: `gh issue view 319 --repo pcalnon/juniper-cascor`, `git -C juniper-cascor log --oneline -1`.
