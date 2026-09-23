# HANDOFF — decision 11 round 3: juniper-ml 0.10.0 cut, every stale record closed, two owner actions outstanding

**Date**: 2026-09-23 · **Session**: <https://claude.ai/code/session_01HgnyH3xEAWeNh1HvZAgbDL>
**Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cryptic-juggling-truffle`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md`
(merged as ml#2012; §A below dispositions **every** item it carried)

---

## THE GOAL — paste this into the new thread

> **Continue the decision-11 release arc: land three open PRs, and finish the two items blocked on
> the owner.**
>
> **Completed so far**
>
> - **juniper-ml 0.10.0 is CUT.** The Release `v0.10.0` tag is at `288de462`, and the ceremony reached
>   `PENDING_PYPI_APPROVAL`. `[servers]` now floors `juniper-data>=0.15.0` (ml#2033, owner-ruled:
>   raise + release). TestPyPI serves 0.10.0; **PyPI returned 404 at handoff, because the deploy is
>   waiting at the `pypi` gate for Paul**: <https://github.com/pcalnon/juniper-ml/actions/runs/35879664979>.
> - The 0.10.0 notes describe everything the tag carries. #2049 closed `[Unreleased]` whole into
>   `[0.10.0]` and re-homed **four #2002 bullets that sat under the RELEASED `[0.9.0]`**.
> - **R-7 (recurrence#178), owner-ruled cross-repo dispatch: both halves merged.** The receiver is
>   juniper-recurrence#181; the sender is juniper-data#426 (`notify-consumers.yml`). **The
>   end-to-end run 403'd**: `CROSS_REPO_DISPATCH_TOKEN` can't reach juniper-recurrence.
> - R-2, R-3 and R-4 are applied or in PR (§A). R-6 is written as a new §11.7 of
>   `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`, inside ml#2051. The
>   release-notes renderer is fixed in ml#2051: 10/10 mutants killed.
>
> **Remaining work, in order**
>
> 1. **Land ml#2050, ml#2051 and ml#2052** (all armed). Under the strict ruleset they go BEHIND as
>    ~20 sessions merge. Re-run `util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py --pr N`
>    for any still open; it exits 4 on a conflict, and then a human resolves it. **ml#2050 is the
>    0.10.0 notes archive**: if it doesn't land, `detect.py` hygiene will read `NOTES_MISSING=1`.
> 2. **After Paul approves Gate 2**: verify `curl -s -o /dev/null -w '%{http_code}'
>    https://pypi.org/pypi/juniper-ml/0.10.0/json` returns 200. Then, in a venv holding
>    `juniper-data==0.14.0`, check that `uv pip install --dry-run "juniper-ml[servers]==0.10.0"`
>    shows `- juniper-data==0.14.0` / `+ juniper-data==0.15.0`. **Never approve the gate yourself.**
> 3. **After Paul scopes the token** (add `pcalnon/juniper-recurrence`, Contents: Read and write, to
>    the fine-grained PAT behind `CROSS_REPO_DISPATCH_TOKEN`): run
>    `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.15.0`, confirm a
>    green `repository_dispatch` run of `CI — bench harness` in juniper-recurrence, then close #178.
> 4. **ml#2046**: fix `_force_kill` in `tests/test_isolated_stack_script.py` (`:994`, `:1514`). It
>    returns on `ProcessLookupError` from `killpg`, which it also gets for a PID that is merely not
>    a group leader. The stub survives and races `TemporaryDirectory` cleanup, and that turned
>    `main` red and HALTed the ceremony.
> 5. Carried and not started: the §3 "Known and bounded" items of the predecessor (see §A).
>
> **Key context**
>
> - **Releases are Paul's.** He ruled "raise + release" for 0.10.0 in-session. That doesn't
>   extend to another cut.
> - **A floor admits without requiring.** A venv already holding 0.14.0 kept it under
>   `juniper-ml[servers]==0.9.0`; reproduced both ways in a clean venv.
> - **A PR authored against `[Unreleased]` that merges after a release lands in the RELEASED
>   section with no conflict** (#2002 did this 22 minutes after v0.9.0). Before any cut, run
>   `util/ad-hoc/2026-09-23_released_section_drift.py` against the previous release's archive.
> - **Run the ceremony from a clean worktree at `origin/main`.** It reads the CHANGELOG *and its own
>   code* from `--repo-root`. Date sections in UTC (`ceremony._today`).
> - **The daily `release-train.yml` cron can't cut anything**: `RELEASE_TRAIN_MODE` is unset (404),
>   so scheduled runs are report-only. Verified from yesterday's run, whose proposal and ceremony
>   jobs were *skipped*.
> - **Closed on `main` but unreleased**: juniper-data#422 (hf/kaggle stores, closes #411),
>   canopy#663 (#559's advisory check), cascor#672 (`__version__`). Each reaches users only with
>   its repo's next release.

---

**Documents REFERENCED** (more than one, so every reference carries its filename):

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md`: the predecessor
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`: §9 S-7, §10 (the release record)
- `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`: new §11.7, in ml#2051
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`: the protocol this file follows
- `/home/pcalnon/Development/python/Juniper/AGENTS.md`: § Data Contract. Unversioned, edited directly.

**Documents CHANGED**:

- juniper-ml, merged: `pyproject.toml`, `tests/test_pyproject_extras.py`, `AGENTS.md`, `README.md`,
  `docs/QUICK_START.md`, `docs/REFERENCE.md`, `CHANGELOG.md` (#2033, #2049), plus
  `util/ad-hoc/2026-09-22_raise_data_floor_0_15_0.py`,
  `util/ad-hoc/2026-09-23_fold_into_juniper_ml_0_10_0.py`,
  `util/ad-hoc/2026-09-23_released_section_drift.py` and
  `util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py`.
- juniper-ml, open: `util/release_train/notes_render.py`, `util/release_train/ceremony.py`,
  `tests/test_release_train_ceremony.py`, `CHANGELOG.md`,
  `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`,
  `util/ad-hoc/2026-09-22_breaking_marker_{corpus_diff,mutation_check}.py` (#2051), and
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` (#2052).
- juniper-recurrence: `.github/workflows/ci-recurrence-bench.yml` (#181).
- juniper-data: `.github/workflows/notify-consumers.yml` (new), `.github/workflows/publish.yml`,
  `CHANGELOG.md` (#426).
- Unversioned: `/home/pcalnon/Development/python/Juniper/AGENTS.md`, plus four memory files:
  `project_decision_11_released_2026-09-11.md`,
  `reference_release_cut_under_an_open_pr_changelog_automerges_silently.md`,
  `reference_vacuous_pass_check_class.md` and `reference_release_train_ceremony_traps_2026-09-09.md`.

---

## A. Every predecessor item, dispositioned against source

| item | disposition | evidence |
| --- | --- | --- |
| R-1 plan §10 versions | Added a dated "Superseded since" table instead of rewriting cells, because the cells are true as the versions that first carried decision 11. | ml#2052 (open) |
| R-2 plan §9 S-7 pin | Added a dated note correcting the pin and the comment. Closure is already in #2043's §10 update block, so it isn't restated. | ml#2052 (open) |
| R-3 parent AGENTS.md:189-190 | Applied. Also qualified "Nothing emits `X_full`": the HF/Kaggle stores did until data#422, and 0.15.0 still does. | direct edit |
| R-4 memory | Applied: the stale "still open" paragraph is marked, and a 2026-09-23 section added. | memory file |
| R-5 `[servers]` data floor | Owner ruled raise + release. 0.10.0 is cut and Gate 2 is pending. | ml#2033, run 35879664979 |
| R-6 ceremony lessons | New §11.7 covering five shapes and their controls, the cron mode and UTC dating. | ml#2051 (open) |
| R-7 recurrence#178 | Owner ruled cross-repo dispatch. Both halves merged; the e2e run 403'd on token scope. | #181, data#426, #178 comment |
| §2 item 3 marker normalisation | Fixed, plus two defects the handoff didn't name: heading qualifiers dropped from Release bodies, and `0.3.2` matching `0.3.21`. | ml#2051 (open) |
| C-1 data#411 | Closed by data#422 (another session). Unreleased. | `hf_store.py:103`, `:186` on main |
| C-2 cascor#668 | Closed by cascor#672 (another session). Unreleased. | `juniper_cascor/__init__.py:12` |
| C-3 canopy#559 | Closed by canopy#663 (advisory check, owner-ruled). Unreleased. | `cc3588a8` |
| C-4 Decision 12 | Has a v1 spec that round 1 rated unsound; zero code. The markdown hits were enumerated: 7 files, worktrees excluded. | data#423, `…PARTITION-PROVENANCE-SPEC.md` |
| C-5 model-core cap | Unchanged, as deliberately decided. | `pyproject.toml` |
| "7 UNRELEASED_CHANGES" | Now **6**: the worker released 0.6.1. Counts: cascor 15, canopy 10, cascor-model 7, recurrence 7, observability 2, service-core 1. | unscoped `detect.py`, 2026-09-23 |
| wheel-contract probe re-run | **Not done.** Its `main()` still returns `n_fail` only, so SKIP scores as success. | carry |
| data#409, cascor#582, cascor-client lockfile bullet | Untouched. | carry |

## B. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch -q origin
gh pr view 2050 --json state; gh pr view 2051 --json state; gh pr view 2052 --json state
gh release view v0.10.0 --json tagName --jq .tagName                    # v0.10.0
gh api repos/pcalnon/juniper-ml/git/matching-refs/tags/v0.10.0 --jq '.[].object.sha[0:8]'   # 288de462
curl -s -o /dev/null -w '%{http_code}\n' https://test.pypi.org/pypi/juniper-ml/0.10.0/json   # 200
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-ml/0.10.0/json        # 404 until Gate 2
python3 util/ad-hoc/2026-09-23_released_section_drift.py --changelog CHANGELOG.md \
    --archive notes/releases/RELEASE_NOTES_v0.9.0.md --version 0.9.0                      # 0 of 18
```

## C. Traps this session hit, and what they cost

1. **The fold raced the lane twice.** #2040 conflicted when #2047 added six `[Unreleased]` entries
   mid-CI. #2049 closed `[Unreleased]` whole instead of naming bullets. A clean merge then filed
   #2031's bullet, which really is in the tag, under `[0.10.0]`. The final preview differed from the
   reviewed one by exactly that bullet, and it was checked by ancestry before `--execute`.
2. **A rehearsal `--dry-run` HALTed on a red `main`** from the #2046 flake. Without the rehearsal,
   the real `--execute` would have HALTed.
3. **`cmd | tail; echo $?` reports `tail`**, twice this session, including a convergence
   watcher's DIRTY exit reading as 0. Run it unpiped.
4. **Whole-file uploads** (`open_signed_pr.py`, `push_signed_commit.py`) clobber anything `main`
   changed underneath. Before every upload, run `git log <base>..origin/main -- <paths>`. #2043
   changed the plan doc under PR-B, which was rebuilt on it.
5. **pip installs past an extra's cap silently, and `pip check` stays green.** Extra-conditional
   requirements are never re-evaluated. Measured with pip 26.2.1.

## D. Git state

This worktree is on `worktree-cryptic-juggling-truffle` at `b6580529`, with 11 staged or modified
entries. **Every one is a copy of a file already uploaded to #2049, #2051 or #2052, so nothing is
unique.** Once those merge, discard the copies. Both sibling worktrees (recurrence and data) and
the ceremony worktree are removed and pruned. The session's background convergence watchers stop
with the session, so re-run them if needed.
