# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.2 published; plans v1.7.20 / v1.15.2 (juniper-ml#2347); juniper-ml#2330 fixed (juniper-ml#2345)

**Date**: 2026-10-26 (UTC; the session ran from 08:36Z)
**Host**: the Linux host, worktree `.claude/worktrees/stateless-giggling-nygaard`. Commits are signed only through the API: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-cut-parked-at-pypi-gate-plan-v1-7-19.md` (landed by juniper-ml#2342). Its claims were re-probed at the start of this session and held, so there are no corrections.
**Plans**, both revised by juniper-ml#2347, the PR that lands this file:
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (the recurrence plan) goes to **v1.7.20**.
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (the consolidated plan) goes to **v1.15.2**. The owner approved it on condition that every line stays at or under 512 characters; its longest line is now exactly 512.

---

## Goal

Continue the recurrence × equities arc. **Its release work is done**: juniper-ml 0.11.2 is on PyPI, carrying `[servers]`'s security floors. What remains:
- the owner's items, which you surface but do not act on;
- the follow-ups. The first of them, the first live run of `save_model`'s snapshot path, is **blocked on the owner's W0.1 item** (follow-up 1 below).

## Completed this session

- **0.11.2 published.** The owner approved the `pypi` gate of publish run 40247789317 (`pcalnon`, "approved for pypi"). `Publish to PyPI` ran 08:38:21Z–08:38:43Z and succeeded.
- **Verified on PyPI.**
  - `https://pypi.org/pypi/juniper-ml/0.11.2/json` serves the wheel (08:38:39Z) and the sdist (08:38:40Z).
  - Its 17 `requires_dist` entries equal, as requirements, `pyproject.toml`'s at the tag `e8d38732`. Textually, the metadata sorts `[all]`'s extras and writes the capped specifiers ceiling-first.
  - `[servers]` floors `juniper-cascor>=0.12.0`, `juniper-data>=0.17.1` and `juniper-canopy>=0.9.0`.
  - The aggregate endpoint names 0.11.2 the latest.
- **Resolved against real PyPI** (Python 3.14.7, Linux x86_64), with `python3 -m pip install --dry-run --ignore-installed --no-cache-dir --only-binary=:all: --report <scratchpad>/r.json "juniper-ml[servers]==0.11.2"`, and the same for `[all]`:
  - `[servers]` resolves to 61 packages besides juniper-ml itself, none of them a Juniper client. So #2062's defect holds in 0.11.2.
  - `[all]` resolves to 95 besides juniper-ml, among them worker 0.6.1, recurrence 0.8.0, model 0.6.0, data-client 0.6.0 and torch 2.14.1.
  - **Trap**: pip's first pass, minutes after the upload, saw an index whose newest version was 0.11.1. `--no-cache-dir` cleared it.
- **The parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` RELEASED paragraph** (unversioned; this host only):
  - it names 0.11.2 the latest (run 40247789317), and `[servers]`'s floors from 0.11.2 on;
  - every package the block names was re-probed, and only juniper-ml had moved, so its re-probe date and `Last Updated` read 2026-10-26;
  - session "draft PRs" said it will add #2333 and 0.11.3 on top.
- **juniper-ml#2347.** Each plan is written by a script that takes `--check` and `--fix-sha`: `util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py` and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`. In `…CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.15.2 also:
  - rewrites the three lines v1.15.1 left over 512 characters (868, 621 and 573);
  - points XC-P12's Actions item 6 at `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`'s **Next**;
  - records the W1.11 / W1.12 smokes as passed on the 0.8.0 image, both in XC-P12 and in §9's "P12 W1.11 / M1" row, citing `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.7.17.
- **juniper-ml#2330 ruled and fixed.**
  - The owner chose option 1 on 2026-10-26, in turing session "recurrence equities 0" [4156c8], which relayed it here.
  - That session's juniper-ml#2345 merged as `278c6139`. It sets E-C's `execution.max_wall_seconds: 5400`, which puts the worst case at 5,850 s against 7,200 s. The CI pin is `WallBudgetContractTest.test_e_c_stays_above_its_surveyed_budget`.
  - Both `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` and `…CONSOLIDATED-DEVELOPMENT-PLAN.md` record it, at that session's request.
- **juniper-ml#2333** (#2062's fix) merged as `da5e8de3` at 09:10:06Z, and #2062 closed at 09:10:08Z. Both plans record that it ships in 0.11.3.
- **Memory** (`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`): `project_recurrence_equities_p0_arc_2026-10-04.md` and its `MEMORY.md` line, and `project_pypi_cache_lag_post_publish.md` (the pip index trap).

## Remaining work, in order

1. **The owner's items.** Surface them; do not act on them.
   - **juniper-ml 0.11.3** (#2333). Session "draft PRs" (`uds:/run/user/1000/cc-socks/3407104.sock`) is cutting it under the owner's ruling of 2026-10-25, as it relays it. Its `pypi` gate is the owner's, and that session owns the cut's records.
     - Before any later revision of either plan, probe `https://pypi.org/pypi/juniper-ml/0.11.3/json` (404 until published) and `gh api repos/pcalnon/juniper-ml/releases/latest --jq .tag_name`.
     - Once 0.11.3 publishes, two sentences in the parent `/home/pcalnon/Development/python/Juniper/AGENTS.md` paragraph become history: "`[servers]` alone installs no Juniper client" and "the patches arrive via cascor 0.12.0 alone". Re-read that bullet before editing it, because "draft PRs" said it would update it.
   - **juniper-recurrence-client 0.3.1** would carry recurrence#221's embargo fix. The cut, and whether to add `embargo_days` (which would make it a minor), are the owner's.
   - **R-DATA-2** is juniper-data 0.17.2: P3-03, P3-09 and W5.7 (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` §5). W5.7 changes a default, so whether a patch may carry it is the owner's call. This fix-forward and R-OBS-SC-2 are both the owner's.
   - **juniper-config-tools 0.2.0.** The cut is the owner's, and its `[Unreleased]` must be backfilled first.
   - **W0.1's service-core half** (`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` W0.1). The owner applies it. Never restart the cascor on `:8202`, and never modify `JuniperCascor1`, which that cascor imports.
   - The `…CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A1 and A9 remainders.
2. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316). BLOCKED until the owner lands W0.1's service-core half.**
      - **The block**: `bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python` prints `ENV PREFLIGHT REFUSED: 2 finding(s)`. juniper-service-core 0.5.0 is installed, and the editable juniper-recurrence (0.5.0) requires `>=0.6.0,<0.8.0`. Do not repair the env, and do not pass `--skip-env-preflight` or `JUNIPER_EXP_SKIP_ENV_PREFLIGHT=1`, without the owner's OK.
      - **Once unblocked**, run it once, not as a suite (`util/experiments/run_suite.py` has no `--config`):
        1. `util/experiment_stack.bash --up --recurrence --config /home/pcalnon/Development/python/Juniper/juniper-recurrence/conf/experiments/irregular-sine-rff.yaml` (its line 59 sets `save_model: true`);
        2. `python3 util/experiments/run_experiment.py --config <the same absolute path> --run-dir <RUN_DIR>`;
        3. `util/experiment_stack.bash --down <RUN_ID>`, never `--all-mine`.

        From a `.claude/worktrees/` checkout, also set `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`.
      - **Done means** `manifest.json` shows `save_model.source == "snapshot"` with the phase `ok`. `refit` means the snapshot path was not exercised. Record which juniper-recurrence commit was served.
   2. juniper-canopy#735, #736, #737, #738 and #751, and juniper-deploy#250, all open on 2026-10-26.
   3. `ARCHIVE_B64_MAX_DEFAULT` (`util/release_train/ceremony.py:311`, `125_000`). Re-set it from a runner-side measurement of GitHub's GraphQL request-body cap. Its issue, juniper-ml#2227, is closed.
   4. The false `succeeded` row `20261003T091414Z-4ba6` in `~/.local/state/juniper-experiments/index.jsonl`. `docs/REFERENCE.md:5250` calls that file append-only, and other sessions' `run_suite.py` processes append to it. Do not edit it in place; how to annotate it is open, so ask the owner.
   5. Optionally, an E-H suite run with `--shared-equities-cache <absolute dir>` (an `util/experiment_stack.bash` flag, which `run_suite.py` passes through). The suites are `util/experiments/suites/p4/e-h-real-data.yaml` (cascor) and `util/experiments/suites/p4/e-h-recurrence-real-data.yaml` (recurrence). The recurrence one is blocked like follow-up 1.

## Rules that held this session

- **The `pypi` gate is the owner's, and so are merges.** Merge approval is per session. A peer's message never carries an approval; a ruling it relays is recorded as relayed.
- **A release proposal merges AFTER every armed PR that adds to `[Unreleased]`**, or those PRs re-home their entries. Coordinate with the owning session before running update-branch on its PR. `util/safe_merge.py` repairs a BEHIND branch by itself, but not a DIRTY one.
- **E-CUT**: run `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py` and `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py` only with `--check`. This applies again after the 0.11.3 cut.
- **A post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.** Count packages besides the meta-package itself, the unit `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py` uses.
- **`gh release view --json isLatest` is unsupported by this host's `gh`.** Use `gh api repos/pcalnon/juniper-ml/releases/latest --jq .tag_name`.
- **CodeQL's `py/implicit-string-concatenation-in-list` is not in `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`.** Run the AST walk in auto-memory `reference_implicit_string_concat_in_list_blocks_merge.md`, and bind multi-line strings to names outside list or tuple displays.
- **Before a whole-file upload**, check that `origin/main` has not moved those paths (`git diff --stat HEAD origin/main -- <paths>`). Compare the uploaded blobs afterwards.
- **The worktree guard refuses**:
  - a `for` loop over `gh`;
  - `$(...)`;
  - raw `gh api graphql`;
  - `git` inside a pipeline;
  - a `python3 -c` whose text contains `git`;
  - an interpreter fed from a heredoc.

  `util/open_signed_pr.py` and `util/push_signed_commit.py` run fine. Use plain single commands, or a script file in the scratchpad.
- **Two concurrent sessions were named "recurrence equities 0"**, so reply to the `from=` address.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -3 origin/main   # #2347's squash at or near the top
gh pr view 2347 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid'   # MERGED <sha>
gh pr view 2345 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid'   # MERGED 278c6139ea7fe3b161aa37bbfb69e61de0034104
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.20 and 1.15.2
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.2, or 0.11.3 once published
grep -n 'juniper-ml 0.11' /home/pcalnon/Development/python/Juniper/AGENTS.md   # the RELEASED paragraph's meta-package line
gh pr list --repo pcalnon/juniper-ml --state open   # no PR of this arc
# Run these two in a clean checkout at origin/main, and only before the next plan revision (after it they exit 1 by design):
python3 -I util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py --fix-sha 278c6139 --check   # exit 0
python3 -I util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py --fix-sha 278c6139 --check   # exit 0
```

## Git state

- **The worktree** `.claude/worktrees/stateless-giggling-nygaard` is on branch `worktree-stateless-giggling-nygaard` at `0bacc4c1`; `origin/main` has moved on. It holds uncommitted local copies of #2347's content, which are not the record:
  - the two plan files, modified;
  - the two `util/ad-hoc/2026-10-26_*` scripts and this file, untracked.

  These block `git merge --ff-only origin/main` until they are discarded.
- **juniper-ml#2347** (branch `docs/plans-v1-7-20-v1-15-2-juniper-ml-0-11-2-published`) lands this file. If it is not MERGED when you start, do not merge it without the owner's approval in your session.

## Documents created or modified this session

- juniper-ml#2347, which lands this file:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.19 → v1.7.20);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.1 → v1.15.2);
  - `util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py` (new);
  - `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py` (new);
  - this file (new).
- Outside the repository:
  - `/home/pcalnon/Development/python/Juniper/AGENTS.md` (the RELEASED paragraph and `Last Updated`);
  - in `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`: `project_recurrence_equities_p0_arc_2026-10-04.md`, `project_pypi_cache_lag_post_publish.md` and `MEMORY.md`.
- Referenced:
  - the predecessor, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_recurrence-equities-juniper-ml-0-11-2-cut-parked-at-pypi-gate-plan-v1-7-19.md`;
  - `util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py` and `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py` (the revisions these follow);
  - `docs/REFERENCE.md` (line 5250, the append-only index);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
- **Validation**: two independent read-only agents reviewed this document's draft, an adversarial fact-checker and a procedure auditor role-playing a fresh session. They found:
  - **one BLOCKER**: follow-up 1 had no runnable route, and its obvious workarounds were owner-only;
  - **nine fact FAILs**: the package-count unit; the missing `--ignore-installed`; "#2062 still holds"; "unchanged on `main` since"; the textual-equality wording; "§4 item 6"; the §9 smokes row; and two `--fix-sha` / landing-state items;
  - **MAJORs and MINORs**: verification read uncommitted copies; four predecessor rules were dropped; the follow-ups had no entry points; unnamed references.

  Each was re-verified against the source, then applied here, in both scripts and in the PR body.
