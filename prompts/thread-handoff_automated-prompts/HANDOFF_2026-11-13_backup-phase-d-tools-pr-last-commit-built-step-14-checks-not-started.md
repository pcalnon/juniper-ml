# Handoff: backup Phase D -- the tools PR's last commit is built and ready to push; no check of step 14 has run

**Date**: 2026-11-13 (facts read between 10:49Z and 11:26Z unless a time is given)
**Session**: host yamaguchi. `W` stands for the worktree
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle`
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_backup-phase-d-step14-tools-pr-open-false-alert-source-found.md`
(below: `HANDOFF_2026-11-12_…md`)

**Read the predecessor first.** Its limits, its "Key context", its open questions (Q1 to Q4, Q6 to Q8) and its steps
C.1 to C.11 still hold, except where this file says otherwise. This file holds only what changed and what is left.

**In every command below, replace `W` by the path above.** Shell state does not persist between tool calls, and an
unset variable would turn `W/tmp/…` into a path under the system temp directory.

---

## Goal statement

1. Push the last commit of juniper-ml#2548 and merge the PR. Nothing holds it any more.
2. Continue the Phase D sitting's step 14 at step C.1 of `HANDOFF_2026-11-12_…md`. None of C.1 to C.11 has run.
3. Carry the open questions to the owner.

Ask the owner for merge approval again in a new session.

### What changed since the predecessor

- **The 0.11.5 cut is done on GitHub.** The proposal, juniper-ml#2558, merged at 10:08:14Z (`48b66130`). The Release
  `v0.11.5` was published at 10:24:18Z on that commit, and the release session then lifted its request to hold
  merges. Its PyPI job was still waiting at its gate at 11:13Z. The release-notes PR, juniper-ml#2561, merged at
  10:38:29Z: `main` is `7ae846b6`.
- The predecessor merged as juniper-ml#2560 (`01f9f89b`, by the owner's account). The alert fix, juniper-ml#2559, is
  `ae801a70`.
- **juniper-ml#2548 is open at `1fbc2b02`** (10:49:58Z, an update-branch): `main` plus the PR's eleven files. It is
  red on purpose until its last commit. Auto-merge has been armed by the owner's account since 2026-11-12 23:07:17Z,
  with the first head's commit text stored.
- **The last commit is built on that head, proven, and not pushed** (`W/tmp/phase-d-finish/readd/state.txt`). Five
  files:
  - the four shared files, as `main`'s copies plus the PR's lines. 239 suites become 242. `AGENTS.md`'s count line
    and one sentence of `docs/REFERENCE.md` change in place; every other line of `main`'s copies survives. The
    CHANGELOG entry is inside `[Unreleased]` under a new `### Added`, and a `### Fixed` entry for juniper-ml#2559 is
    added, which covers the entry that step B.2 of `HANDOFF_2026-11-12_…md` calls owed;
  - `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py`, one line. Since `bf53a1d6` the finish suite imports
    `tests/redacted_env.py`, which the harness did not copy into its scratch tree: its baseline failed and it ran no
    mutant. With the fix it kills 208 of 208 (`W/tmp/phase-d-finish/mutants-v3-shard{0,1,2,3}.log`).
- **`W` is a checkout of that result**: HEAD detached at `1fbc2b02`, the five files modified and unstaged. What it
  held before is in `W/tmp/phase-d-finish/saved-20261113T101422Z/`; `build_readd.py` reads the PR's additions there,
  because `W`'s own copies now hold `main`'s changes too. Do not delete that directory.
  - The pinned pre-commit hooks pass on the five files.
  - Regression step, every command, past failures (`W/tmp/phase-d-finish/regression-run-4-final-tree.log`, ended
    11:06Z): 238 of 243 pass. Four failures are the suites that step A.4 of `HANDOFF_2026-11-12_…md` names as failing
    on this host only. The fifth is one test of `tests/test_isolated_stack_script.py`: `Errno 39`, directory not
    empty, while its temporary directory was removed. That suite passed in the run before (on `8f0d4bed`: 239 of
    243) and three times alone afterwards, and this PR does not touch it.
- **The primary checkout is on `main` again and does not hold the tools.** `HANDOFF_2026-11-12_…md` says it does.
  Until juniper-ml#2548 merges, the owner's commands use `W`'s copies: `D` is `W`.
- The running record is 708 lines, in `W/tmp/phase-d-sitting/` and in the primary's `tmp/phase-d-sitting/`. Its last
  section covers 2026-11-13 09:54Z to 11:30Z.

### Remaining work, in order

**A. juniper-ml#2548.** One command per line; the scripts work from any directory.

- Run for real so far: `build_readd.py`, `run_regression_list.py`, `update_pr_body.py` (it writes two scratch files and
  sends nothing), and `rebuild_after_main_moved.py --apply` once, at 10:49Z, before its checks for an untracked file
  and for a pushed commit were added.
- Run dry only: `push_readd.py`, `rearm_with_final_text.py`, `step_aside_again.py`.
- `W/tmp/phase-d-finish/test_helpers_offline.py` exercises on local git objects what no dry run reaches: seven
  checks, all holding at 11:25Z.

1. `python3 W/tmp/phase-d-finish/rebuild_after_main_moved.py`. It says whether the PR's branch, `main`, the UTC date
   or `W` moved since the build. If so, run it with `--apply`: it runs update-branch (a push to the PR's branch only),
   rebuilds, and puts `W` on the new head. Once the last commit is on the branch it says so and rebuilds nothing. **Merging this handoff's own PR moves `main`, so expect to need this**; the
   script then removes `W`'s untracked copy of this file, once it has checked that the new head holds the same bytes.
2. After a rebuild, run the regression list again, **in the background** (about 18 minutes):
   `DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent/no-session-bus python3 W/tmp/phase-d-finish/run_regression_list.py > W/tmp/phase-d-finish/regression-run-5.log 2>&1`,
   then `tail -n 8` of that log. Expect the four suites of step A.4 to fail. Run any other failing suite alone
   before reading it as a defect.
3. `python3 W/tmp/phase-d-finish/push_readd.py --dry-run`, then without the flag. If it refuses, it names the command
   to run; if the commit is already on the branch, it says so and sends nothing.
4. `python3 W/tmp/phase-d-finish/rearm_with_final_text.py --after-push --apply`. It arms the auto-merge with
   `W/tmp/phase-d-finish/final-squash-body.md` as the commit text. Without it the squash commit carries the first
   head's text or, after a refusal, the list of the branch's commit messages (the repository's default).
5. `python3 W/tmp/phase-d-finish/update_pr_body.py "<regression result>" "<mutation result>"`, then the
   `gh api -X PATCH` line it prints. It fetches the live body itself and sends nothing.
6. `python3 W/util/safe_merge.py --pr 2548 --repo juniper-ml --execute`, in the background; read its `MERGED` or
   `REFUSED` line. The ruleset is strict: an armed PR that falls behind `main` waits, and this tool re-syncs it.
   - On `REFUSED` it has disarmed the auto-merge. Fix the cause, repeat step 4, then this step.
   - `python3 W/tmp/phase-d-finish/step_aside_again.py` says whether `main` conflicts with the PR, and in which
     files (a CHANGELOG entry or a suite added on `main` does it). If it conflicts, run it with `--apply`, then
     steps 1 (`--apply`) to 6.
   - If it names unresolved review threads, read and answer each before resolving it.
7. Confirm that in `main`'s `CHANGELOG.md` the entry `Backup Phase D, step 14` sits between `## [Unreleased]` and
   `## [0.11.5]`.

**B. The sitting.** Steps C.1 to C.11 of `HANDOFF_2026-11-12_…md`, with `D` = `W`. Its host facts were read at
2026-11-13 02:19Z. Re-read at 10:51Z, as pcalnon: there is still no aside directory, no
`~/.local/state/duplicati/acceptance.json` and no probe unit; root's run directory cannot be read from here.

**C. For the owner.** Every open question of `HANDOFF_2026-11-12_…md` (Q1 to Q4, Q6 to Q8). First: Q2 (three
off-schedule runs: was the job's edit page saved near each start?), Q3 (AC-7 against D-14), Q6 (both halves), Q7 before
the retention save of step C.4, and whether the probe's listing of the destination is acceptable ("Where this segment
went past 'beyond `stat`'").

**D. Then** the record PR and the after-Phase-D items: steps C.10 and C.11 of `HANDOFF_2026-11-12_…md`. Add to the
record the three smaller sweep findings of its step B.3, the teardown race above, and the traps below.

### Traps met since the predecessor

- CI does not run the mutation harness, so a test change broke it unseen. Run it after any change to the two suites:
  `python3 W/util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py --shard K/4`, K = 0 to 3.
- This segment wrote times from memory in two documents and a PR comment; they were wrong by up to 14 minutes. The
  first draft of this file did it again. Read a time from a commit or the clock.
- The owner's account acts on these PRs too: it merged juniper-ml#2560 and updated juniper-ml#2548's branch at
  09:57Z. Read a PR's head before every push; the scripts pin it.
- A validating agent listed the host names in `gh`'s hosts file, which can hold a token. It printed no value, but
  that touched "Never read a secret file". Name that file in a brief's limits.

---

## Verification commands (start of the next thread)

```bash
gh pr view 2548 --repo pcalnon/juniper-ml --json state,mergeStateStatus,headRefOid,mergedAt
gh release view v0.11.5 --repo pcalnon/juniper-ml --json publishedAt,targetCommitish
python3 W/tmp/phase-d-finish/rebuild_after_main_moved.py
tail -n 8 W/tmp/phase-d-finish/regression-run-4-final-tree.log
```

**Expect:** the PR `OPEN` at `1fbc2b02…` (`BLOCKED`, or `BEHIND` once `main` has moved), or `MERGED` if another
session finished it; the release published at 10:24:18Z on `48b66130…`; the rebuild script printing the built, the
live and the worktree's heads and changing nothing; the log ending `238 of 243 passed` and five `FAILED` lines.

## Git status at handoff

- **juniper-ml#2548**: open at `1fbc2b02`, twelve commits, red on purpose, auto-merge armed by the owner's account.
- **`W`**: HEAD detached at `1fbc2b02`; `.github/workflows/ci.yml`, `AGENTS.md`, `CHANGELOG.md`, `docs/REFERENCE.md`
  and `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py` modified and unstaged (the last commit's content);
  this file untracked until step A.1 follows its PR's merge. The branch `worktree-swift-stargazing-spindle` still
  points at `15b5d9bb`.
- **Do not remove `W`, or the worktree `parallel-strolling-meteor`,** until juniper-ml#2548 and the record PR have
  merged: `W/tmp/` holds the scripts, the running record and the alert traces, and `parallel-strolling-meteor`'s
  `tmp/phase-d-sitting/` holds files that the primary's archive lacks.
