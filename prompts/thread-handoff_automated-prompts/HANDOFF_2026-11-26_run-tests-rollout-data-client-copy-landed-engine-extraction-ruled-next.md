# Handoff: run_tests rollout -- juniper-data-client's copy landed (data-client#273); the Overtoad ruled "extract into ci-tools"; the engine PR is next

**Date**: 2026-11-26 (written about 12:00Z)
**From**: session c62abc55, in worktree `juniper-ml/.claude/worktrees/floofy-doodling-aho`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_run-tests-rollout-recurrence-copy-landed-data-client-copy-next.md`.
All six of its verification commands passed by 01:33Z on 2026-11-26. Its traps still stand.
**Memory**: `project_run_tests_rollout_2026-11-24.md`
**The plan**: `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md` (the proposal). Its § 4 is
the design, and its § 5 records the rulings.

---

## Goal

Build option A of the proposal: the shared engine moves into juniper-ci-tools as `juniper_ci_tools.run_tests`
(ci-tools **0.10.0**), and each repo keeps a thin `util/run_tests.py` holding a `RepoSpec`. **The Overtoad ruled
"Extract into ci-tools" on 2026-11-26 at 11:30:12Z**, answering an AskUserQuestion asked at 02:16:21Z; both times are
from this session's transcript.

The order is the proposal's § 4.3:

1. the engine PR in juniper-ml, which is next;
2. the release, which the Overtoad cuts;
3. converting recurrence and data-client;
4. the seven repos.

**Merge approval does not carry over.** The "Merge both" ruling covered data-client#273 and juniper-ml#2668 only
(memory `feedback_headless_merge_approval_policy.md`), so ask before merging anything. A ci-tools release is a deploy,
and needs its own approval.

## Completed (this session)

- **juniper-data-client#273 MERGED** at 11:43:28Z as `51e34f71`. It holds:
  - `util/run_tests.py` (2,533 lines) and `tests/test_run_tests.py` (62 tests). The unit-tests job collects the
    suite, so no new workflow was needed.
  - `docs/REFERENCE.md` § Running Tests Locally, an `AGENTS.md` pointer (now 17,590 of its 17,604-character
    ceiling), and a `CHANGELOG.md` entry.
  - **The lanes are every workflow job that runs pytest.** `all` is unit-tests and integration-tests.
    generator-parity and security are opt-in through `OPT_IN`, and slow-or-integration-tests is optional because a
    schedule runs it.
  - **Only test and gate steps run.** Every other step is left out and listed, and a left-out step that runs a test is
    refused.
  - `env:` blocks are expanded and given to each step. The rc-capture idiom accepts exit 5, and every report goes
    to the run directory.
  - Measured locally under JuniperCascor1 (Python 3.14.7): `all` passed in 1m07s with 677 passed. All 62 runner tests
    also passed under 3.12. Its CI passed all 25 checks, macOS included. The mutation check killed all 16 mutants.
  - **#274 merged first**, and the two conflicted in REFERENCE.md's footer.
    - Fix commit `38307835` moved the section clear of the footer.
    - `git merge-tree` was then clean. The merged tree, materialized detached, passed `all`: unit-tests had 727
      passed, which includes #274's tests.
    - `util/safe_merge.py` updated the branch and merged it.
- **The proposal** is in this file's PR, juniper-ml#2668, which also holds this arc's six `util/ad-hoc/2026-11-26_*`
  scripts:
  - `run_tests_function_divergence.py`: 812 lines are identical in all three copies;
  - `run_tests_ci_tools_census.py`: all ten repos pin `juniper-ci-tools>=0.9.0,<0.10.0`;
  - `run_tests_data_client_mutation_check.py`;
  - `probe_sequence_safety_screens.py`;
  - `probe_merge_with_main.py`;
  - `add_required_check_to_ruleset.py`.
- **Ruling 3 is done.** juniper-recurrence's ruleset `juniper-recurrent-rules` (`20634527`) now requires
  `Local test runner suite` (integration 15368), 11 checks in all, and every other field is unchanged. The ruleset as it
  was before is saved under the scratch directory (see "Git state").

## Remaining work

### 1. The engine PR (juniper-ml)

- **Start from data-client's `util/run_tests.py` at its `main`**, the superset. Get it with
  `util/ad-hoc/2026-11-25_run_tests_rollout_sibling_worktree.py show --repo juniper-data-client --file util/run_tests.py`.
- **Put the engine in one module first**, `juniper-ci-tools/juniper_ci_tools/run_tests.py`, so the diff stays reviewable.
- **The per-repo surface becomes `RepoSpec`.** In data-client's copy it is:
  - `PROJECT` and `is_project_checkout`;
  - `OPT_IN`, `LANE_SUFFIX` and `GROUPS`;
  - `discover()`;
  - `_DESCRIPTION` and `_EPILOG`;
  - every message that names a docs path (the preflight's refusal names `docs/REFERENCE.md`);
  - the header line in `_main`.
- **The discovery strategies** (proposal § 4.1):
  - `job_lanes(workflows, jobs, name, optional)`, which covers data-client's discovery and, by workflow stem,
    recurrence's;
  - `unittest_lane()`;
  - `step_lane()`, for juniper-ml's `regression` and `bash` lanes. Read juniper-ml's `discover` first: it differs
    most.
- **Decide, and record in the PR:**
  - Rule B (test and gate steps only) against juniper-ml's package lanes. Compare its `--list` and `--dry-run` output
    before and after.
  - `GATING_EVENTS` for the unittest lane. recurrence's copy uses `LOCAL_EVENTS`, which admits `workflow_dispatch`.
- **The tests.**
  - Merge the three fake-checkout suites into `juniper-ci-tools/tests/`: juniper-ml's `tests/test_run_tests.py`,
    recurrence's and data-client's.
  - Each repo keeps its RealWorkflows and Docs tests.
  - Re-run a mutation check on the engine. `2026-11-26_run_tests_data_client_mutation_check.py` shows the pattern.
- **The version.** ci-tools 0.10.0: `pyproject.toml`, `_version.py`, `juniper-ci-tools/CHANGELOG.md`, and
  `notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md` from `notes/templates/TEMPLATE_RELEASE_NOTES.md`.
  Check what `ci-ci-tools.yml` runs.
- **juniper-ml's own runner becomes a thin spec over the in-repo engine.** Decide how it imports it: an in-repo path,
  or the installed package.

### 2. Then

- **The release**: the Overtoad cuts `juniper-ci-tools-v0.10.0`.
- **The conversions**: recurrence and data-client, each pinned `>=0.10.0,<0.11.0`, with `--list` and `--dry-run`
  identical before and after.
- **The seven**, in the 2026-11-24 order: cascor-client, cascor-worker, data, harcot, cascor, canopy, deploy. The
  proposal's § 2.3 says what each needs from the engine.
- **Still open**:
  - juniper-ml's four local-only failures (the 11-24 handoff, § 2);
  - optionally, recurrence's recipe in `conf/python_versions.yaml`.

## Key context and traps (this session)

- **The command guard refuses a Bash line that assigns a path to a shell variable and then uses it with git or a
  script.** For example, `S=util/...; python3 $S show ...` was refused as "names git in a form too complex". Write the
  literal paths, one command per call.
- **Bandit's B105 flags dict keys named like secrets** (`"SECRET"`, `"FAKE_TOKEN"`) in `tests/`. Rename them
  (`CI_ONLY`); never suppress.
- **pytest 9 reports a `subTest` failure as `SUBFAILED(...) node`.** data-client's `_PT_PROBLEM` reads it; the other
  copies do not.
- **To probe an unpushed change, use `commit-tree` with a throwaway index** (the two `probe_*` scripts). No ref moves,
  and the screens and `git merge-tree` see exactly what a push would.
- **A peer session, `moonlit-percolating-sun-fa`, sweeps the one-artifact publish template** across repos, editing
  `docs/REFERENCE.md`, `CHANGELOG.md` and `publish.yml`. Its #274 is what conflicted with #273. Expect the same
  overlap in the seven.
- **The AskUserQuestion sat 9 h 14 m.** Finish everything that does not depend on the answer before asking.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log --oneline -3 origin/main     # ml#2668
gh pr view 273 -R pcalnon/juniper-data-client --json state,mergeCommit --jq '.state, .mergeCommit.oid'    # MERGED
gh api repos/pcalnon/juniper-recurrence/rulesets/20634527 --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks | length'   # 11
python3 util/ad-hoc/2026-11-25_run_tests_rollout_sibling_worktree.py show --repo juniper-data-client --file util/run_tests.py | sed -n 2p
python3 util/ad-hoc/2026-11-26_run_tests_ci_tools_census.py | command grep "juniper-ci-tools:" | wc -l     # 10 repos
ls ~/Development/python/Juniper/juniper-ml/tmp/run-tests-rollout--floofy-doodling-aho | wc -l           # this session's scratch, kept
```

## Git state

- **juniper-ml**: this file's PR is juniper-ml#2668: the proposal with its rulings, the six scripts, and this
  handoff. Nothing else is open from this arc.
- **juniper-data-client**: `main` is at `51e34f71` or later. The worktree
  `worktrees/juniper-data-client--feat--local-test-runner--20261125-1925--5c329a39` and its local branch were removed
  after the merge. First its `CHANGELOG.md` and `docs/REFERENCE.md` were replaced by `main`'s merged copies; both had
  been checked to hold both PRs' changes. Then all five changed paths matched `main` byte for byte, and its `tmp/` was
  empty. GitHub deleted the remote branch on merge.
- **juniper-recurrence**: no branch or worktree; only the ruleset changed.
- **Scratch, kept under the retention rule**, in the juniper-ml primary's `tmp/run-tests-rollout--floofy-doodling-aho/`:
  - the PR and commit bodies;
  - recurrence's copies;
  - the ruleset as it was before the change;
  - the merge and check logs;
  - the 17 mutant copies (`mutants/`).

  data-client's run records are under its primary's `tmp/run-tests/`.
