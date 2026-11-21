# Thread Handoff — R-OBS-SC-2 recorded in plan v1.15.15; owner items next

**Date**: 2026-11-09 UTC (host clock is local time, UTC−6)
**Session**: `09366253`, the Linux host, worktree `.claude/worktrees/groovy-petting-fiddle` (branch `worktree-groovy-petting-fiddle`, base `734aab58` = `origin/main` at the start). This file lands in the same PR as plan v1.15.15, through `util/open_signed_pr.py` (a signed API commit).
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_r-obs-sc-2-published-lock-round-merged-plan-v1-15-15-next.md` (session `e21d1414`). Its step 1 (plan v1.15.15) is done here; its step 2 (owner items) carries forward, corrected below.

## Goal

R-OBS-SC-2's session-side work ends when the v1.15.15 PR merges. What remains is owner decisions. They are recorded in `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, in §6's mid-wave sitting ("R-OBS-SC-2's follow-ups") and in §5's note on R-OBS-SC-2. A successor runs the post-merge re-check, surfaces the owner items, and acts only on a ruling.

**Approvals are per-session** (`feedback_headless_merge_approval_policy.md`). This session held "approval granted for PR merge and related operations" (the user's turn, 2026-11-09). **Re-ask in yours.** Paul approves every `pypi` gate.

## Completed this session

- **Ported the predecessors' 12 files** from worktree `bright-giggling-metcalfe` (sha256 compared, all equal): nine `util/ad-hoc/2026-11-09_*` tools and three handoffs. One was then changed. `util/ad-hoc/2026-11-09_lock_round_2_env_record.py` probes `fastapi.telemetry` through `importlib.import_module`, because CodeQL's unused-import query would flag the `import` statement. It gives the recorded answers in the lock round's own venvs: `True` under FastAPI 0.162.0 and `False` under 0.141.1.
- **Dated the owner's four rulings from the transcripts** with `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`:
  - 2026-11-08 08:59:56Z: 0.4.2 is "P3-07 + header names"; 0.7.2 is "Include ml#2514, then cut"; P3 D-03, for the lock PRs, is "This arc opens them".
  - 14:42:17Z: "Approve both cuts".
  - 2026-11-09 00:24:20Z: "Per-lock probe".
  - 09:49:26Z: "Approving now: wait".
- **Re-probed every recorded fact** with `util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py`: 0 FAIL. It covers the PRs, Releases, runs, approvals, deployments, PyPI and TestPyPI files, consumer locks, `pyproject.toml` files and newest Releases, the forks' throttle lines, the app factories' `telemetry=`, and the trio's environments.
- **Wrote plan v1.15.15** with `util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py`: 55 edits, idempotent. The 19 lines over 512 characters are `main`'s 19, and the ID coverage is 381 of 381.
- **Two independent reviewers** read the first draft, one re-deriving facts and one adversarial. They found 1 BLOCKER, 8 MAJOR, 9 MINOR and 7 NIT findings, all applied. The corrections below come from them, each re-checked at the source.

## Corrections to the predecessor (and to the first draft)

- **P3 D-03 has a recorded answer, but only for the lock PRs.** The question, as asked, was who opens the second round's image lock PRs. Who opens the **floor** PRs, D-03's third part, was never asked, so P3-17 stays open. "Floors go in each repo's release PR" is a session's plan, not a ruling.
- **The data F-fix PR is P3-09, not P3-03.** P3-03 is the separate data#438 fix-forward, which P3-09 follows.
- **"The trio's environments are not upgraded" is wrong for `JuniperCascor1`.**
  - Its observability and service-core are editable installs of the juniper-ml **primary** (W0.1). That checkout held 0.4.2's and 0.7.2's code on 2026-11-09, on another session's branch, `feat/wrote-quick-ad-hoc-pid-attribute-search`, while pip reports 0.4.1 and 0.7.1.
  - `JuniperData` (`python3.14t`) and `JuniperCanopy1` hold observability 0.4.0 and service-core 0.5.0.
- **0.4.2 does not end XC-SENTRY.** Query strings (canopy's `?api_key=`, sent under the default `send_pii=False`), Sentry Logs and exception values wait for 0.4.3, which the plan now carries as §5's R-OBS-SC-3.
- **Session `b4208d23` did write memory** (its transcript, 00:33:30Z), though its handoff says it changed nothing outside the repository.

## Remaining work

1. **Post-merge re-check** (commands below).
2. **Owner items** (report them; do not act). The plan's §6 lists them:
   - Whether the per-lock probe may stand in for S0.11's relay run at the trio's restart.
   - Who may move the juniper-ml primary, which `JuniperCascor1` imports. O13 names four other primaries.
   - Who opens the consumers' floor PRs, and juniper-ml 0.11.5 for the `[tools]` floor `juniper-observability>=0.4.2`.
   - A register row for the forks' `RateLimiter`, which truncates with no floor, so APD-SVCCORE-004's `Retry-After: 0` is live: data `juniper_data/api/security.py:250` and `:254`, cascor `src/api/security.py:229` and `:233`, canopy `src/security.py:270` and `:274`. The same row covers `FailedAuthThrottle`'s round-down (data `:427`, cascor `:386`).
   - data#454's telemetry opt-out for cascor and canopy.
   - When R-OBS-SC-3 (0.4.3) is designed.
   - The consumer cuts that carry the new locks. R-DATA-2's lock gate is met; P3-03 and P3-09 remain, and recurrence's bench caps widen first. For cascor, whether a fix-forward is owed is open. Canopy needs P4 D-4. Recurrence's next release carries them too. Each cut then needs juniper-deploy's pin and a restart.
   - Not this arc's: the canopy legs on `:8052` and `:8053` still write logs to `/tmp/juniper-e2e/`, about 40 MB each. The legs are guarded: check against `ss` before any reaper run.

## Traps

- Write and Edit refuse the primary checkout's `tmp/` (where the scratchpad lives). Put files in the worktree's `tmp/`.
- The isolation guard refuses `git -C` into a sibling worktree. It also refuses heredocs and compound commands that name git, and complex pipelines. Copy files in with `cp`, and run git and gh commands one at a time.
- `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` takes file paths only: `--help` is read as a path.
- The pre-commit secrets hook is vacuous on files that are not staged. Run gitleaks `dir` over copies, with a planted control.
- An agent's finding is evidence, not a verdict. Each one this session was re-checked at its source before it was applied.

## Verification commands

```bash
git fetch origin && git log -1 --format='%h %s' origin/main          # the v1.15.15 merge or later
python3 util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py --check   # exit 0, 55 already applied
python3 util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py          # 0 FAIL; the environment checks are 2026-11-09 state
command grep -c 'Version\*\*: 1.15.15' notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1
```

## Git state and files

The worktree `groovy-petting-fiddle` is at `734aab58`. The PR's 17 files are uncommitted here and land through the signed API commit. Its ignored `tmp/v1-15-15/` holds the PR body and commit body as sent.

Retention: the predecessors' evidence stays where it is: `bright-giggling-metcalfe`'s `tmp/lr2/` (trees, probe runs and venvs, drafts), plus `enchanted-foraging-rocket`'s and `fizzy-enchanting-deer`'s `tmp/`. The plan cites the probe results through the lock PRs' bodies, not those paths. Archive or delete them only under the retention rule. This session deleted nothing.

## Documents referenced / changed

- **Referenced**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`; `reports/2026-10-04_consolidated-development-plan/extraction-P3-defect-register.md` (D-02 and D-03; P3-03, P3-09, P3-17, P3-18); `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`; `notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`; `HANDOFF_2026-11-08_r-obs-sc-2-p3-07-written-round-1-validated-fix-pass-next.md` and the three predecessor handoffs this PR lands; ml#2523's body (P3-07's rounds); the four lock PRs' bodies.
- **Changed**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.15);
  - the 12 scripts `util/ad-hoc/2026-11-09_consolidated_plan_v1_15_15_r_obs_sc_2_shipped.py`, `…_r_obs_sc_2_record_reprobe.py`, `…_r_obs_sc_2_owner_answers.py`, `…_wait_for_pypi_gates.py` and the eight `…_lock_round_2_*.py`;
  - the three ported handoffs and this file;
  - outside the repo: memory `project_recurrence_equities_p0_arc_2026-10-04.md`.
