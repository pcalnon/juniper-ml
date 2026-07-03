# Thread Handoff — Juniper Per-File Coverage Rollout (C-5 heavy-env remainder)

**Date:** 2026-07-03
**Author:** Paul Calnon (Claude Code, custom-agent suite)
**Continue:** the per-file coverage rollout — remaining C-5 heavy-env units **canopy, cascor, cascor-worker, recurrence-model**, then the **meta/deploy exemption documentation**. One PR per unit, task-executor agents in centralized worktrees, owner-gated merges.

**READ FIRST (juniper-ml main):** `notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md` (§2 waiver policy, §4 deferred-unit rows, §5 C-5, §6 risks) + parent plan `notes/JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md`.

## Completed (this session)

- **C-4 COMPLETE, gate live on main:** ml#607 (websocket lift), ml#609 (workers/tail + prometheus-client `[test]` fix), ml#611 (blocking gate) — all MERGED. Merged main measures 97.81% overall; CI logs show `Enforcing gate: PASS`. C-4 worktrees cleaned.
- **DISC-1 FIXED + MERGED** (recurrence#78): class-based filter → message-based `"ignore:Using \`httpx\` with \`starlette.testclient\` is deprecated:Warning"`. The class is version-dependent (absent in the 06-30 resolution, present in starlette 1.3.1). Client audited: no starlette, untouched.
- **C-5 wave delivered — 4 PRs AWAITING OWNER MERGE** (all checks green, gates verified live in CI, single clean commit each):
  - **cascor#365** cascor-model: 71.98→**98.93%**, 40→425 tests, FIRST-ever gate. `log_config/log_config.py` (0%) was **live API** (`src/spiral_problem/spiral_problem.py:111` imports it) — real tests 0→98.76, NO waiver.
  - **data#211**: 86.77→**98.31%**, all 23 sub-modules ≥95. Root cause: 6 genuine unit suites missing the `unit` marker (now marked). Advisory `scripts/check_module_coverage.py` RETAINED (pre-push hook + `util/run_coverage.bash` reference it); only the CI step swapped to the shared gate.
  - **recurrence#79** app: 95.21→**99.37%**; `[test]` self-references `[observability]` → 15 skips → 0; `metrics.py` 42→100.
  - **recurrence#80** client: pooled 93.96→**100%**; `[test]` += `juniper-observability>=0.3.1,<0.5.0`.

## Remaining work

1. **On each owner-merge signal:** verify `gh pr view` state=MERGED, then gated worktree cleanup (live-cwd scan + clean-tree + merged-only; delete lingering remote branch — recurrence does NOT auto-delete). Executor worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`: `juniper-cascor--test--cascor-model-coverage-gate--20260703-0525--b3e6817e`, `juniper-data--feature--per-file-coverage-gate--20260703-0527--9c85399b`, `juniper-recurrence--test--recurrence-app-coverage-gate--20260703-0558--038859c9`, `juniper-recurrence--test--recurrence-client-coverage-gate--20260703-0559--038859c9`, plus this handoff's `juniper-ml--docs--handoff-c5-heavy-env--20260703-0620--0b4319e5`.
2. **canopy** — `JuniperCanopy1` env; measure the WHOLE `src` (today's gate is a unit+regression subset); expect subset-scope findings (flag, don't fake); canopy unit tests span 2 dirs; regen panel snapshot only if `get_layout()` changes (it shouldn't — tests only).
3. **cascor** — `JuniperCascor1`; bash harness `src/tests/scripts/run_tests.bash`, subset `-m "unit and not slow"`; the LARGEST unit — expect a C-4-style split (lift PR(s) → separate gate PR last).
4. **cascor-worker** — torch; the CPU-torch fresh-venv recipe from cascor-model works (`pip install --index-url https://download.pytorch.org/whl/cpu torch`).
5. **recurrence-model** — torch; two-lane `.coveragerc.torch` (base-omit + torch-include) — measure per lane, gate on the union.
6. **Exemptions** — juniper-ml meta (`packages = []` → N/A or scope to `util/`) + juniper-deploy (no source): document per scoping §5 "special-cased" row (short scoping-doc amendment PR).

## Key context / gotchas

- Gate = **statement** basis + **pooled_percent** (never mean-of-files); the tool computes statement % itself even under `branch=true` configs. Pin `juniper-ci-tools>=0.6.0,<0.7.0`; wiring mirrors `ci-observability.yml` / `ci-protocol.yml`.
- **LIBTORCH collision:** host exports `LIBTORCH`/`LD_LIBRARY_PATH` → rust_mudgeon libtorch breaks venv torch (`undefined symbol: _PyObject_NextNotImplemented`). Prefix `env -u LD_LIBRARY_PATH -u LIBTORCH` on every plain-venv torch invocation.
- **cascor main pre-existing red:** repo-wide `CI/CD Pipeline` `Unit Tests (Python 3.14)` + `Quality Gate` failed on main before #365 (dependency-install failure) yet passed on #365's run — check main first before blaming any cascor PR.
- Test-dep-gap pattern (prometheus/observability class): if tests skip for a missing optional dep, add it to `[test]` FIRST, re-measure, then lift.
- Process: single-commit PRs (squash-merge; amend+force-push fixes); `gh pr list` dup-guard (concurrent sessions!); wait for ALL checks incl. Pre-commit; owner merges everything; never self-approve deploy/publish gates; pre-commit binary at `/opt/miniforge3/envs/JuniperCascor1/bin/pre-commit`; data repo: `feature/**` branches only, no `[skip ci]`.
- recurrence: flaky truncated final pytest summary (cosmetic — exit code + coverage.json reliable; validate the JSON each run).
- Open side-thread (not rollout): recurrence Scheduled Security Scan failed 2026-06-29; cascor main 3.14 lane above.

## Verification commands (new thread, before acting)

```bash
for p in "pcalnon/juniper-cascor 365" "pcalnon/juniper-data 211" "pcalnon/juniper-recurrence 79" "pcalnon/juniper-recurrence 80"; do set -- $p; gh pr view "$2" --repo "$1" --json number,state --jq '"\(.number) \(.state)"'; done
git -C /home/pcalnon/Development/python/Juniper/juniper-ml fetch origin && git -C /home/pcalnon/Development/python/Juniper/juniper-ml log --oneline -1 origin/main   # expect >= 0b4319e
ls /home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md
```

## Git state

All delivered work lives on remote PR branches (nothing uncommitted); the 5 worktrees above await post-merge cleanup. juniper-ml main HEAD at handoff ≈ `0b4319e` (C-4 gate live). Start the new thread clean: `git fetch origin` per repo and verify against refreshed `origin/main`, never the parked working trees.
