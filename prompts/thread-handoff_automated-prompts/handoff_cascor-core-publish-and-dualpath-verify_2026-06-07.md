# Thread Handoff — finish juniper-cascor #319 dual-path arc + CW-05

**Date:** 2026-06-07 (worktree/CI facts re-verified 2026-06-08)
**Origin:** cascor #319 defect work → cascor#324 (dispatch int() fix + juniper-cascor-core drift backport), MERGED.

---

**Continue: finish the juniper-cascor #319 dual-path arc + CW-05 — publish `juniper-cascor-core`, regenerate the worker locks against it, revert the deploy stopgap, and do the MANDATORY live dual-path verification (remote workers must grow hidden units).**

## Completed so far

- cascor #321 (defects 1/2)
  - #322 (defects 3/4/5)
  - **#324 (MERGED 2026-06-07, commit `5dab0cc`)**
  - #324 = dispatch root-cause fix
    - `float()`→`int()` for `random_max_value`/`sequence_max_value`, `cascade_correlation.py:1224-1225`
    - backport of the `juniper-cascor-core` worker-payload normalization (`CandidateUnit._coerce_int_like` + `ActivationWithDerivative._normalize_activation_fn`) into cascor src
  - restoring the `package == src` drift invariant (drift-guard verified green)
  - +1 dispatch guard
  - +1 new `test_candidate_core_worker_contracts.py`
- Worktree cleaned up
- juniper-cascor-core Wave 0 (ml#345) merged.
  - **Worker Wave 1 (worker#98) merged — it ALREADY added the `juniper-cascor-core>=0.1.0` pyproject dependency** (`juniper-cascor-worker/pyproject.toml`) + the `candidate_unit`/`ACTIVATION_MAP` import wiring.
  - So the "worker adopt" is mostly DONE in source.
- Drift still in sync (package's two backported files unchanged since juniper-ml@`f4d66db`).

## Remaining work (critical path, in order)

1. **Publish juniper-cascor-core 0.1.0.** `publish-cascor-core.yml` is ready (tag `juniper-cascor-core-v*` → TestPyPI→PyPI) but has NEVER fired (PyPI 404, TestPyPI empty, no release).
**BLOCKED ON PAUL:** (a) configure PyPI + TestPyPI **trusted-publishing pending-publisher** for the new project (admin-only); (b) cut tag/release `juniper-cascor-core-v0.1.0`; (c) approve the pypi-env dual gate (wait_timer + manual reviewer).
2. **Regenerate the worker locks** (the only remaining worker step — pyproject dep already landed in #98).
Both `requirements.lock` and `requirements-cpu.lock` are STALE (missing `juniper-cascor-core`); they can't be regenerated until 0.1.0 is on PyPI.
Command (GPU lock): `uv pip compile pyproject.toml --no-emit-package torch -o requirements.lock`.
The CPU lock additionally excludes torch (Dockerfile installs CPU torch from the PyTorch index).
NOTE: worker main is **already red from multiple causes** (the unpublished-dep lock staleness AND a pre-existing failure — e.g. the gitleaks v3 bump #96); don't assume publish+lock alone greens it — check the full CI.
3. **Revert the deploy stopgap — OPERATIONAL, NOT A PR.** `juniper-deploy/docker-compose.cw05-stopgap.yml` is an **untracked, never-committed local overlay** (plus the runtime `docker cp` PyYAML / `mkdir /logs` container patches).
There is nothing in git to revert.
Cleanup: stop applying `-f docker-compose.cw05-stopgap.yml`, delete the local file, rebuild/restart the worker container so it imports `candidate_unit` from the installed package (no `--cascor-path`).
4. **MANDATORY live dual-path verification** (the original #319 goal): on the running deploy stack (2 workers), confirm cascade training grows hidden units via the **REMOTE tier**.
**Read WORKER logs, not just cascor status** (2026-06-02 dual-path-stall lesson).
Success = `All N remote tasks completed successfully` + workers `tasks_completed>0` + network grows past local-only.

## Decision for Paul

Publish 0.1.0 from juniper-ml now (unblocks worker/deploy) vs first resolve the deferred org-strategy question (`notes/JUNIPER_2026-06-05_JUNIPER-ECOSYSTEM_CODE-ORGANIZATION-STRATEGY.md` recommends moving juniper-cascor-core to the cascor family). **Recommend publish-now**; the repo-move is a separate future migration (package name is stable either way).

## Key context

- **Concurrency:** a parallel session drove ml #345–#384+ (it keeps advancing main). Run `gh pr list` + check recent main before acting; coordinate, don't race.
- Env: `JuniperCascor1` (Py3.13). Use worktrees per convention.

## Verify start state

- `gh pr view 324 -R pcalnon/juniper-cascor --json state` → `MERGED`
- `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/juniper-cascor-core/json` → `404` until published
- `grep juniper-cascor-core juniper-cascor-worker/requirements.lock` → absent until step 2
- `gh run list -R pcalnon/juniper-cascor-worker --branch main` → red (multi-cause)

## Git status

All #319 cascor work is on cascor main (`5dab0cc`). No worker/deploy PRs are staged because the worker adopt already merged (#98) and the deploy stopgap is untracked/operational. No open PRs on cascor; juniper-ml/worker/deploy have only Dependabot PRs open.
