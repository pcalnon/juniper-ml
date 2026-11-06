# Thread Handoff — Recurrence × Equities: recurrence 0.8.1 published, the 2026-11-06 rulings recorded; juniper-ml's `[recurrence]` floor is next

**Date**: 2026-11-06 UTC (this host's clock is local time, UTC−5)
**Session**: `ff40b833`, the Linux host, worktree `.claude/worktrees/vast-wiggling-parnas`. Commits are signed only through the API (`util/open_signed_pr.py`, or GraphQL `createCommitOnBranch`). Never use a local `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-01_recurrence-equities-apd-ml-002-closed-parent-agents-edited-owner-items-next.md` (landed by juniper-ml#2397). Start from this file. All eight of the owner's 2026-11-03 rulings that the earlier handoff listed have been carried out (below).

---

## Goal

Continue the recurrence × equities arc: P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, at v1.15.12 once the PR carrying this file merges. Three things come next:

1. Re-check that PR after it merges.
2. Ask the owner for go-ahead on the two follow-ups under **Remaining work**.
3. Do R-DATA-2 (juniper-data 0.18.0) once its gates clear.

## Completed this session (2026-11-03 → 11-06)

- **The 2026-11-03 rulings were recorded** in ml#2415 (`0368c3a2`):
  - the plan went to v1.15.11;
  - `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` went to v0.2.1, with W5 = data-client 0.7.0 and W11 = 0.7.1.
- **canopy#778 is closed** by canopy#788 (`af650373`).
- **juniper-config-tools 0.1.1 is on PyPI**:
  - ml#2408 carried the bump and CHANGELOG;
  - ml#2411 carried the notes;
  - publish run 41820362912 succeeded.
- **W0.1 ran on `JuniperCascor1`** (2026-11-04, on the owner's word): six editable `--no-deps` reinstalls.
  - Preflight passed and `pip check` was clean.
  - **The bench then failed 4 of 41.** The env held model-core 0.2.0, but recurrence 0.8.0 passes `walk_forward_folds(groups=)`, which exists only from model-core 0.3.0, so every `POST /v1/crossval` 500s.
  - On the owner's word, model-core 0.3.2 was installed into the env, and the bench passed 41 of 41.
- **juniper-recurrence 0.8.1 is on PyPI**, owner-approved.
  - recurrence#229 (`2a467adb`) floors `juniper-model-core[crossval]>=0.3.0,<0.4.0` and adds `tests/test_pyproject_floors.py`.
  - The Release is `juniper-recurrence-v0.8.1`; its notes are ml#2454 (`8d553b41`).
  - The image run 41935261283 and the PyPI run 41935261358 both succeeded.
  - Probed on 2026-11-06: PyPI's `requires_dist` reads `juniper-model-core[crossval]<0.4.0,>=0.3.0`.
- **The P12 worktree cleanup is done.** All six trees were removed, five of them with `--force` on the owner's word.
  - Their `tmp/` dirs are archived at `juniper-ml/tmp/worktree-cleanup-2026-11-03-p12/`.
  - `util/ad-hoc/2026-11-04_dirty_worktree_files_landed_check.py` showed that every dirty file had already landed.
- **`MEMORY.md` was compacted** to 19,608 B through `project_closed_arcs_hub.md`.
- **The owner ruled on 2026-11-06** (recorded by this PR in plan v1.15.12 and spec v0.2.2):
  1. canopy's and recurrence's data-client caps widen `<0.7.0` → **`<0.8.0`** before W5's Release.
  2. **R-DATA-2's lock gate stands**: 0.18.0 waits for R-OBS-SC-2 (observability 0.4.2 and service-core 0.7.2) and for data's second lock PR.
  3. **P3 D-07 is a retro-note**:
     - 0.18.0's notes name #437 (`equities_seq` 6.0.0) a contract break;
     - data's `CHANGELOG.md` `[0.17.0]` gains a BREAKING tag;
     - the v0.17.0 Release body is not edited.
  4. **P3 D-12 is answered**: a session cuts 0.18.0 once its gates clear, and the owner approves the `pypi` gate.

## Remaining work, in order

1. **Re-check this PR after it merges**:
   - plan v1.15.12 and spec v0.2.2 on `main`;
   - the two 2026-11-04 ad-hoc scripts and `util/ad-hoc/2026-11-06_plan_v1_15_12_spec_v0_2_2_owner_rulings.py` present.
2. **Ask the owner** to go ahead with raising juniper-ml `pyproject.toml:110` `[recurrence]` to `juniper-recurrence>=0.8.1,<0.9.0`.
   - Update `AGENTS.md`'s extras table in the same PR.
   - It reaches users only through a juniper-ml release, so ask whether to fold it into the next one.
3. **Ask the owner** to go ahead with fixing recurrence's stale smoke pin at `.github/workflows/publish-recurrence-model.yml:173`, which reads `juniper-model-core>=0.1.0,<0.2.0`.
4. **R-DATA-2**: see plan §5's R-DATA-2 row for its gates and order.
   - Gates in order: P3-03 merged and validated, then P3-09, then R-OBS-SC-2 on PyPI, then data's second lock PR.
   - Widen recurrence's `[bench]` and `[bench-equities]` caps from `<0.18.0` first.
   - Carry D-07's retro-note.
5. **P5 W4** (when P5 reaches it): widen the data-client caps to `<0.8.0`, in canopy's `pyproject.toml` (`juniper-data` extra) and recurrence's `juniper-recurrence/pyproject.toml:71`.
6. **The owner's still-open items**: §6 A1 (APD-ML OD-2, canopy#685 call (a), F-S10's three choices).

## Rules that held this session

- **Never the system temp dir** (global `CLAUDE.md`). Scratch goes in this worktree's `tmp/s3/`; check it against the retention rule before the worktree goes.
- **Release-Train Archive Guard**: `notes/releases/` changes go in their own add-only PR.
- **`safe_merge.py` can print `REFUSED` and still exit 0.** Read its `MERGED` line.
- **`pip check` cannot see an API-level floor bug.** Run the bench after any env change.
- **JuniperCascor1** is changed only on the owner's word. **#2360 merges LAST.** **Never run `util/remove_stale_worktrees.bash`.**
- **Paul approves every `pypi` gate**, and an approval does not carry over to another context.

## Verification commands for the new thread

```bash
cd ~/Development/python/Juniper/juniper-ml
gh pr list --repo pcalnon/juniper-ml --search "v1.15.12" --state all
gh api repos/pcalnon/juniper-ml/contents/notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md -H "Accept: application/vnd.github.raw" | grep -m1 "Version"
curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"   # expect 0.8.1+
grep -n "juniper-recurrence>=" pyproject.toml   # still >=0.8.0 until item 2
/opt/miniforge3/envs/JuniperCascor1/bin/python -s -c "import importlib.metadata as m; print(m.version('juniper-model-core'))"   # expect 0.3.2
```

## Git state

- Branch `worktree-vast-wiggling-parnas`. All of this session's files land through the PR that carries this handoff, as one signed API commit.
- Untracked locally: the same files (`util/ad-hoc/2026-11-01_simulate_w0_1_env_refresh_pip_check.py` and `…_p12_worktree_cleanup_check.bash` match `main` already).

## Documents created or modified by this PR

- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.11 → v1.15.12)
- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` (v0.2.1 → v0.2.2)
- `util/ad-hoc/2026-11-06_plan_v1_15_12_spec_v0_2_2_owner_rulings.py` (new)
- `util/ad-hoc/2026-11-04_dirty_worktree_files_landed_check.py` (new)
- `util/ad-hoc/2026-11-04_p12_force_remove_landed_worktrees.bash` (new)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_recurrence-equities-0-8-1-published-owner-rulings-recorded-ml-floor-next.md` (this file)
