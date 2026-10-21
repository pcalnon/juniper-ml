# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.0 is on PyPI; plan v1.7.15

**Date**: 2026-10-21
**Host**: turing (Darwin, Intel x86_64; no commit signing; bash 3.2). Every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md` (juniper-ml#2309)
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.15** (this session, via `util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py --publish-run 39577119562 --archive-sha 3a0bea06 --recheck-sha 0c9a0baf`)

---

## Goal

Continue the arc from plan v1.7.15. **This session** (turing session 9) picked up the predecessor handoff's remaining work. The owner granted merge approval at its start.

- **Item 1, the publish, is done.** The owner approved the `pypi` gate. In `publish.yml` run 39577119562, the "Publish to PyPI" job ran from 21:08:22Z to 21:08:55Z and passed.
  - `https://pypi.org/pypi/juniper-ml/0.11.0/json` serves the wheel (uploaded 21:08:50Z) and the sdist (21:08:52Z).
  - `requires_dist` carries `juniper-recurrence<0.9.0,>=0.8.0`, `juniper-recurrence-model<0.7.0,>=0.6.0`, `juniper-data>=0.17.0` and `juniper-canopy>=0.9.0`.
  - The project-level JSON (`/pypi/juniper-ml/json`) still read 0.10.0 at 21:10Z and read 0.11.0 a few minutes later. That is CDN lag; check the version endpoint first.
  - Release `v0.11.0` is the repo's latest. The archive PR juniper-ml#2307 merged as `3a0bea06`.
- **Item 3, the post-merge re-check, passed.** It ran on `main` `0c9a0baf` at 21:10Z, twelve hours and four merges after juniper-ml#2306. Both greps print 1: README's lead-in names 0.11.0, and `docs/REFERENCE.md` has the `| 0.11.x ` row.
- **Item 2, the `propose.py` fix, belongs to a concurrent session.** Session "generic-hugging-hamster" `[08bf3d]` claimed it at 21:07Z, about four minutes before this one asked, and is building it. The split was agreed by cross-session message: that session owns `util/release_train/propose.py`, `tests/test_release_train_propose.py` and a `CHANGELOG.md` `### Fixed` entry; this session owns the plan and the handoffs.
  - **The fix's scope is wider than the predecessor handoff said** (confirmed by reading `build_proposal`).
  - Step 5b-ii moves README's `### Extras` table through `_INLINE_EXTRAS_TABLES`. It never moves the `## Ecosystem Compatibility` rows, which `tests/test_pyproject_extras.py` `ReadmeCompatTableTest.test_compat_table_matches_pyproject` also checks. So an in-repo sub-package bump that escapes a meta ceiling is red as generated, as well as the meta bump's lead-in.
  - The likely next such bump is juniper-config-tools 0.2.0, against the meta's `<0.2.0`.
  - That session also found a stale "Reviewer action required -- this generator has a known gap" blockquote in `_pr_body`. #1460 added it, and #1478 closed the gap without removing it.
- **Plan v1.7.15** changes three things: the Status line, the Progress block (a session 9 bullet, with Next rewritten) and the revision row. It lands in one PR with this handoff and the script.

## Remaining work, in order

1. **Item 2: confirm it landed, then record it.** Do not duplicate it.
   - `gh pr list --repo pcalnon/juniper-ml --state all --search "propose.py README"` finds the PR. If it is still open, `ListAgents` shows whether its session is alive; message it before touching `propose.py`.
   - Once it merges, the next plan revision records its PR number and merge sha.
   - **Ordering constraint for the owner:** a juniper-config-tools 0.2.0 cut needs this fix on `main` first. Otherwise its proposal needs a hand co-change: `util/ad-hoc/2026-09-21_sync_readme_compat_table.py` on the proposal branch, the 0.11.0 pattern.
2. **juniper-ml#2211 (recommended next agent task).** Make `save_model` persist the model the run scored, through `POST /v1/model/snapshots` with `expect_operation_id` (juniper-recurrence#192), instead of re-fitting it in a second process. Current locations on `main` `0c9a0baf` (the issue's line numbers are against `98a8525a`):
   - in `util/experiments/run_experiment.py`: `_save_model_rerun` at :2161 (its 600 s CLI re-fit at :2201), `_train_operation_id` at :2252, and predict's `expect_operation_id` / 409 handling at :2404-2420, which is the pattern to copy;
   - the module docstring at :76-81 says the driver never calls the snapshot route, and has to change with the code;
   - `util/experiment_stack.bash` points the service's snapshot root at `${RUN_DIR}/snapshots` (:114-122, :636).

   Before writing code, read the 0.8.0 route's request and response contract from the published source, not the local checkout (which may be stale; see item 4). Get it from the GitHub tarball at tag `juniper-recurrence-v0.8.0`, `juniper_recurrence/routers/snapshots.py`.

   Keep the re-fit as the fallback when the train response carries no `operation_id`, and record in the manifest which path produced `model.npz`. Tests: the W1.5 stub in `tests/test_recurrence_operation_identity_and_dataset_budget.py` answers 404 for unknown routes. Add a snapshot route, plus success, 409 and fallback cases. The re-fit's evidence chain is pinned in `tests/test_run_experiment.py`, `tests/test_save_model_recorded_cli_contract.py` and `tests/test_recurrence_launch_record_edges.py`. Those suites must stay green, or be changed deliberately.
3. **juniper-ml#2210.** `per_run_timeout_seconds` is checked against `max_wall_seconds` only. Compute each cell's worst-case driver budget and refuse at `load_suite`, or derive the subprocess timeout from it. The budget is the dataset budget, plus the health waits, plus `max_wall` for each HTTP phase, plus `save_model`. Do it after #2211, which changes the `save_model` term. The issue has the full budget table.
4. **Owner** (carried):
   - the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0); that file is not on turing;
   - the juniper-recurrence-client 0.3.1 release (it carries juniper-recurrence#221's embargo fix), and whether to add `embargo_days`;
   - juniper-config-tools 0.2.0 for the typing marker (backfill its `[Unreleased]` first; mind item 1's ordering), or leave it;
   - the W0.1 service-core half;
   - juniper-data's next release carrying W5.7;
   - refreshing the juniper-recurrence and juniper-data checkouts (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data).
5. **Follow-ups** (carried):
   - the W1.12 / W1.11 smokes on the 0.8.0 image, on a host whose Docker reaches GHCR;
   - juniper-canopy#735–738 and #751, and juniper-deploy#250;
   - the `ARCHIVE_B64_MAX_DEFAULT` runner-side measurement in `util/release_train/ceremony.py` (0.11.0's archive was 2,968 B under the cap);
   - optional: a first real run of the E-H suite with `--shared-equities-cache`.

## Landing rules learned this session

- **Two sessions picked up this arc within four minutes.** One started from the v1.7.13 handoff, found its step 1 done, and moved on to the v1.7.14 handoff's item 2. This one started from v1.7.14. `ListAgents` at the start showed a busy "recurrence" session started 5 minutes earlier, and one cross-session message settled the split before either wrote code. The first claimant kept the code task; the other took the plan. Repeat that check at the start of every session on this arc.
- **Session names move.** Between two `ListAgents` calls this session became "recurrence" and the other became "recurrence equities", a name it shares with the idle predecessor `[cbe77f]`. Address a peer as `name [ref]` whenever two rows share a name.
- **After a publish, check the version endpoint first.** `https://pypi.org/pypi/<pkg>/<version>/json` confirms it at once, while `/pypi/<pkg>/json` can lag by minutes.
- Everything else is as in the predecessor:
  - the `pypi` gate is the owner's;
  - write one plain command per call under the worktree guard (a `$VAR` path in `sed` is refused; spell the path out);
  - build every whole-file upload from a fresh `origin/main` copy.

## Verification commands for the new thread

```bash
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.15 (or later)
python3 -I util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py --publish-run 39577119562 --archive-sha 3a0bea06 --recheck-sha 0c9a0baf --check   # every edit "already applied", exit 0
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.0
gh pr list --repo pcalnon/juniper-ml --state all --search "propose.py README" --json number,state,title   # item 2's PR (the concurrent session's)
gh issue view 2211 --repo pcalnon/juniper-ml --json state -q .state   # OPEN: the recommended next agent task (Remaining work, item 2)
git show origin/main:README.md | grep -c 'pyproject pins matching .juniper-ml. 0.11.0'   # 1
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/mellow-juggling-fox` on branch `worktree-mellow-juggling-fox`, at `main` `0c9a0baf`. Nothing is committed locally; the plan edit, this handoff and the v1.7.15 script are the working-tree changes the plan PR carries (landed through `util/open_signed_pr.py`). Once it merges, `git checkout -- . && git clean -fd` on the worktree is safe.
- The juniper-recurrence and juniper-data checkouts are untouched.

## Documents created or modified this session

- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.14 → v1.7.15)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-published-plan-v1-7-15.md` (this file)
- `util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py` (new)
- Referenced:
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md` (the predecessor);
  - `util/ad-hoc/2026-10-21_plan_v1_7_14_juniper_ml_0_11_0_cut.py` (the revision script this follows);
  - `util/release_train/propose.py` (`build_proposal` step 5b-ii, `_INLINE_EXTRAS_TABLES`, `_pr_body`), `tests/test_pyproject_extras.py` (`ReadmeCompatTableTest`), `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`;
  - `util/experiments/run_experiment.py`, `util/experiment_stack.bash`, `tests/test_recurrence_operation_identity_and_dataset_budget.py`, `tests/test_run_experiment.py`, `tests/test_save_model_recorded_cli_contract.py`, `tests/test_recurrence_launch_record_edges.py` (for juniper-ml#2211);
  - `util/release_train/ceremony.py` (`ARCHIVE_B64_MAX_DEFAULT`).
