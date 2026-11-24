# Handoff: one-artifact sweep. juniper-cascor#777 MERGED (`f5ed3017`); round 6 found a BLOCKER in the port checker (a line continuation hides a `$(…)`); fix pass 5, then round 7; then the 15 ports in 7 repos, and plan v1.15.18

**Written**: 2026-11-24 at 00:58Z (`date -u`) by session `ffffd3` (`d935c226`), ListAgents name
`one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772`.
**Worktree**: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-23_one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772.md`
(juniper-ml#2614).

**Merge approval** is per-session. The owner granted it at this session's start; ask again. Nothing below merges until
the owner grants it in YOUR session.

**Start the next session IN `$W`.** The arc's untracked scripts and every review's evidence exist only there.

## Goal

1. Close the port checker's review: fix pass 5 (round 6's BLOCKER), then round 7 (`$W/tmp/sweep/ROUND7_BRIEF.md`). No
   port is built until a round reports no BLOCKER and no MAJOR.
2. Port cascor `main`'s merged template to the 15 publishers in 7 repos, one PR per repo.
3. Plan v1.15.18, and land the sweep's scripts.

## Done this session (receipts; all in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`)

- **Fix pass 3** (executor; brief `tmp/sweep/FIXPASS3_BRIEF.md`; tree `tmp/sweep/cascor-r4/`): round 4's fixes. On both
  bases (`802399ab`, `e9c86f83`): 161 tests; 45/45 mutation proof; test lens 70/70 + 10/10; checker proof 153/153;
  15/15 port simulations; every earlier mutant fails. § "Fix pass 3".
- **Round 5** (fresh reviewer; `tmp/sweep/ROUND5_BRIEF.md`; outputs `tmp/r5review/`): 0 BLOCKER, 1 MAJOR, 5 MINOR,
  2 NIT. The MAJOR (an `echo`'s `${x@P}` / `${a[x]}` expansion runs a hidden command) and 4 MINORs were in the CHECKER;
  cascor's tree was sound on `36dd6f2d`. § "Round-5 review" records the decision: the cascor PR lands, the checker gets
  fix pass 4 and round 6 before any port. NIT 8 fixed in the writer (`c47940ad…`).
- **juniper-cascor#777 MERGED** 2026-11-24 00:56:52Z as `f5ed3017` (parent `36dd6f2d`, signature verified, 11 files,
  `Allow-Symbol-Loss:` in the squash message). Two commits: `a12b2c5f` (the sweep) and `74971d3a` (three date lines:
  `Verify AGENTS.md Last Updated` failed after midnight UTC; the writer re-run with `--date 2026-11-24`). 25/25
  required checks green on both heads. § "Landed". Post-merge runs on `main` all SUCCESS at 01:09:15Z (CI/CD,
  CodeQL, Conformance, Golden Regression, Post-Merge Main Verification): `tmp/sweep/land/evidence/main_runs_f5ed3017.log`.
- **Fix pass 4** (executor; `tmp/sweep/FIXPASS4_BRIEF.md`; `tmp/sweep/checker-r5/`): the checker
  (`util/ad-hoc/2026-11-23_publish_port_template_identity.py`) now sha256 `ebeb7556…`, 1623 lines; install scripts
  judged by a positive allow-list of command names after quote removal; `exit 1` only; no `trap`; `BASH_ENV`/`ENV`/
  `BASHOPTS`/`SHELLOPTS` refused. 3/3 cascor, 15/15 port simulations, every mutant (R5 18, R4 15, R2 7, N 14, its own
  16) FAILS, `checker_proof_r5.py` 261/261. § "Fix pass 4".
- **Round 6** (fresh reviewer, `tmp/sweep/ROUND6_BRIEF.md`; report `tmp/r6review/ROUND6_REPORT.md`): 1 BLOCKER, 0
  MINOR, 2 NIT. The checker joins `\<newline>` with a space where bash deletes it, so `echo "… $\` + newline +
  `(pip install … pypi.org …)"` looks plain and runs a hidden install; a NUL byte likewise. Six executed mutants
  (R6-1..R6-6) PASS the checker. Over-strictness: none against a real port. § "Round-6 review".
- **Fix pass 5** launched 2026-11-24 ~01:30Z (executor, `tmp/sweep/FIXPASS5_BRIEF.md`, work dir
  `tmp/sweep/checker-r6/`). Its durable outputs: § "Fix pass 5" in the dispositions file, `tmp/sweep/ROUND7_BRIEF.md`,
  the regenerated manifest (old one kept as `tmp/arc/sweep_scripts.r6.sha256`). See item 1.
- `tmp/ports/verify_all_mains_v2.bash` (the new checker, `--repo` per repo): `3 of 18 pass` after #777 (cascor's 3).
- Peers: `tmp/arc/plan_v1_15_18_inputs.md` holds [9660dc]'s inputs (deploy#284, the archived worktrees, ml#2619's
  inventory: this lane's group C R28-R41, group E R58-R65, §4 gaps 1-9) and the rename session's corrections.

## Remaining work

1. **Fix pass 5, then round 7.** This session may still launch round 7 after this handoff lands. So check in this
   order: if `tmp/r7review/ROUND7_REPORT.md` exists, round 7 already ran (record its dispositions, then go on); if
   `ListAgents` shows this session busy, ask it before launching anything. Then check whether fix pass 5 finished
   (`grep -n '^## ' tmp/sweep/REVIEW_DISPOSITIONS.md`).
   - **"Fix pass 5" present and `tmp/sweep/ROUND7_BRIEF.md` exists**: check `sha256sum -c tmp/arc/sweep_scripts.sha256`,
     then launch ONE fresh `general-purpose` reviewer on `ROUND7_BRIEF.md`, unedited. Its report goes to
     `tmp/r7review/ROUND7_REPORT.md`. Record its dispositions in the earlier sections' style. A BLOCKER or MAJOR means
     fix pass 6 and round 8, the same way.
   - **"Fix pass 5" missing**: the executor did not finish. If the live checker matches neither the manifest's line nor
     `tmp/sweep/checker-r6/checker_r5_as_reviewed.py` (`ebeb7556…`), it is a half-edit: restore that saved copy, then
     re-run fix pass 5 from `tmp/sweep/FIXPASS5_BRIEF.md` with a fresh executor.
   - For every checker change: save the reviewed copy first, regenerate the manifest (keep the old one), and re-run 3/3,
     15/15 and every mutant.
2. **The ports** (handoff predecessor's item 3 still holds; changes below). The template is cascor `main`'s
   `publish.yml` at `f5ed3017` (its workflows equal `tmp/sweep/cascor-r4/main/juniper-cascor`'s).
   - Briefs: `$W/tmp/ports/SWEEP_BRIEF.md` (template A-G), `$W/tmp/ports/BRIEF.md` (tests/docs/rules; stale paths and
     session links), the predecessor handoff's item 3 (per-port changes, R4-1, R4-5, digests, envs).
   - Added since: R5-F5 (ml: `tests/test_publish_testpypi_verify.py:477` asserts the template's lag-error text, beside
     R4-1); ml `publish.yml` adopts the template's exact lag-error text (fix pass 3); the checker needs `--repo`.
   - data#547 MERGED (20:39:16Z, `2ad7b7b5`): data's test has 2 renamed docstring lines; build on data `main`.
   - Per PR: fresh clone (`2026-11-15_publish_port_clone.py`), writer modelled on the 11-15 port writer, tests, the
     gate, `run_open_signed_pr.py` (dry-run first), `readback_branch.py`, the 11-23 checker on the fetched head, an
     independent review, CI, merge with approval. Commit body: `Allow-Symbol-Loss:
     TestFindReleaseRun.test_the_newest_release_run_that_still_holds_the_artifact_is_found`. An `AGENTS.md` edit's
     `**Last Updated**` = the UTC day of the COMMIT (see Traps).
   - Done when `bash tmp/ports/verify_all_mains_v2.bash` prints `18 of 18 pass`.
   - Message `overtoad-rename-repair-ml-2606-recurrence-deploy-next` [301392] before arming/merging the ml port (it
     holds ml#2606, which keeps `publish*.yml` and `tests/test_publish_one_artifact.py` at main's bytes).
3. **Plan v1.15.18**, on a FRESH clone of juniper-ml `main` (never from `$W`: its tracked plan is v1.15.16). Records
   #777, reviews 1-6 with fix passes 1-4, the ports, SWEEP items 28 (M5) and 29 (N6), `tmp/arc/plan_v1_15_18_inputs.md`.
   Lands the 6 scripts (`tmp/arc/sweep_scripts.sha256`) and promotes or archives the proof tools in
   `tmp/sweep/cascor-r3/`, `cascor-r4/`, `checker-r5/`. CodeQL prescreen + pre-commit on every new script first.

## Traps

- **Date checks cross midnight UTC.** #777's first commit (00:30Z) carried the previous day's `**Last Updated**`. Run
  the writer with `--date` = `date -u`'s day at UPLOAD time.
- **cascor's squash is COMMIT_MESSAGES**, so a fix-up commit's message joins the squash; `safe_merge.py` leaves
  `commitBody` null. Confirm the waiver in the landed message (`gh api …/commits/<merge> --jq .commit.message`).
- **An unattributed `/tmp` write**: `/tmp/vFI4WZy/` (2026-11-24 00:28:39Z), two copies of juniper-ml's `.gitignore`
  named `4.1.1` and `5.1.1`. Not from this session's push, gate or merge tools; left as evidence.
- `cd` in a Bash call persists for the session; return to `$W` (`cd $W`) after any `cd` into a tree.
- The Bash guard refuses `git -C`, `.github` paths in some loops, and `cd … && python3 - <<EOF`: use script files.
- Never estimate a time; `date -u`.

## Git state of `$W` and retention (00:58Z)

- Branch `worktree-ethereal-munching-peacock` at `81b8eaf7`, behind `origin/main` `5d22fbe9`. Nothing staged.
- Untracked: this handoff, the predecessor handoff (on main via #2614), 28 copies on main via #2610, and the 6 scripts
  only here (`tmp/arc/sweep_scripts.sha256`; two of them changed this session: the writer `c47940ad…`, the checker
  `ebeb7556…`). NEVER delete the 6.
- Gitignored `tmp/`: add `sweep/cascor-r4/`, `sweep/checker-r5/`, `sweep/checker-r6/`, `sweep/land/`, `r5review/`,
  `r6review/`, `r7review/` (once made), the briefs `sweep/{FIXPASS3,FIXPASS4,FIXPASS5,ROUND5,ROUND6,ROUND7,LAND}_BRIEF.md`,
  `ports/verify_all_mains_v2*`, `arc/plan_v1_15_18_inputs.md`, `arc/sweep_scripts.{r3,r4,r5nit,r6}.sha256`. Retention as the predecessor states:
  keep `$W` until the 6 scripts land, the proof tools are promoted or archived, and `tmp/` is archived.

## Verification commands (from `$W`, one per call)

```bash
gh pr view 777 --repo pcalnon/juniper-cascor --json state,mergeCommit   # MERGED, f5ed3017…
sha256sum -c tmp/arc/sweep_scripts.sha256                                # 6 x OK
grep -n '^## ' tmp/sweep/REVIEW_DISPOSITIONS.md                          # "Fix pass 5"? "Round-7 review"?
bash tmp/ports/verify_all_mains_v2.bash                                  # "3 of 18 pass" until the ports land
cat tmp/sweep/land/evidence/main_runs_f5ed3017.log                       # cascor main's post-merge runs
```

## Documents referenced / changed

- **Referenced**: the predecessor handoff; `tmp/ports/SWEEP_BRIEF.md`, `tmp/ports/BRIEF.md`;
  `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.17);
  `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (ml#2619).
- **Changed on GitHub**: juniper-cascor's 11 files through #777 (`.github/workflows/publish.yml`,
  `publish-cascor-model.yml`, `publish-protocol.yml`, `src/tests/unit/test_publish_one_artifact.py`,
  `src/tests/unit/test_publish_docs_bounds.py` (new), `docs/ci_cd/MANUAL.md`, `REFERENCE.md`, `QUICK_START.md`,
  `docs/DEVELOPER_CHEATSHEET.md`, `AGENTS.md`, `CHANGELOG.md`).
- **Changed in `$W`, untracked**: `util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`,
  `util/ad-hoc/2026-11-23_publish_port_template_identity.py`.
- **New or appended in `$W/tmp/`**: `tmp/sweep/REVIEW_DISPOSITIONS.md` (§ Fix pass 3, Round-5 review, Fix pass 4,
  Landed, Round-6 review; Fix pass 5 by its executor), the briefs (`FIXPASS3/4/5`, `ROUND5/6`, `LAND`;
  `ROUND6_BRIEF.md` and `ROUND7_BRIEF.md` by the executors), `tmp/arc/plan_v1_15_18_inputs.md`,
  `tmp/ports/verify_all_mains_v2.bash`.
- This handoff lands through its own one-file PR.
