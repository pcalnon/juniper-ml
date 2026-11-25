# Handoff: run_tests rollout -- juniper-recurrence's copy landed (recurrence#240); juniper-data-client's copy next, then the engine-extraction proposal

**Date**: 2026-11-25 (written about 12:35Z)
**From**: session 12f6c9b3, in worktree `juniper-ml/.claude/worktrees/jazzy-plotting-steele`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_local-test-runner-follow-ups-landed-cross-repo-run-tests-rollout-next.md`.
Its seven verification commands all passed at 02:09Z. Its section 1 (the per-repo table, what carries over, what is new, the
order) and its traps still stand, so read it first. Its section 2 (juniper-ml's four local-only failures) is untouched.
**Memory**: `project_run_tests_rollout_2026-11-24.md` (the Overtoad's ruling and this state)

---

## Goal

Continue the per-repo `run_tests` rollout. **The Overtoad ruled at 2026-11-25 11:58:05Z** (AskUserQuestion, asked at
02:10:15Z): "Two copies, then decide". juniper-recurrence and juniper-data-client each get a standalone copy of juniper-ml's
`util/run_tests.py`. After both, bring the Overtoad a concrete proposal for moving the shared engine into juniper-ci-tools,
**before** the other seven repos. A ci-tools release is a deploy, and needs its own approval.

Copy 1 (recurrence) is merged. Next comes copy 2 (juniper-data-client), then the proposal.

**Merge approval.** The Overtoad's "merge approval granted" covered this rollout's PRs in session 12f6c9b3 only. A handoff
cannot carry it (memory `feedback_headless_merge_approval_policy.md`), so ask again before merging anything.

## Completed (this session)

- **juniper-recurrence#240 MERGED** 2026-11-25 12:18:41Z as `2ce346da` (signed commit `7b28d377`). Every check was green,
  including the new `Local test runner suite` (21 s), CodeQL, Pre-commit, Sequence Safety and Memory Budget.
  - `util/run_tests.py` (2,229 lines) and `tests/test_run_tests.py` (49 tests).
  - `.github/workflows/ci-tooling.yml`, new. **It is not a required check**: adding `Local test runner suite` to ruleset
    `juniper-recurrent-rules` (id `20634527`) is the Overtoad's call, and it is still open.
  - `README.md` § Running tests locally. The suite checks that every option `--help` lists is documented there.
  - `AGENTS.md`: one sentence. The file is at **19,972 / 20,000** characters, so the next AGENTS.md edit there needs a
    cut or an `Allow-Budget-Overrun: AGENTS.md` trailer.
  - Measured locally under `JuniperCascor1` (Python 3.14.7):
    - `all` passed 7 jobs in 43.5 s: the unittest lane ran 3 suites (106 tests); app 485, model 227 and client 77 passed
      with their coverage gates; bench passed 41.
    - `optional` (`model-torch`) passed 16.
  - The worktree was removed after a byte check against `main`, and both branches, local and remote, are gone.
- **How recurrence's copy differs from juniper-ml's** (its README § Running tests locally has the operator view):
  - The lanes come from the `test` job of each `ci-recurrence-*.yml`. The directory names are aliases.
  - The unittest lane comes from **every** pull-request or push workflow that runs `python3 -m unittest`.
  - A local non-editable install (`pip install "./juniper-recurrence[...]"`) is read like an editable one.
  - Steps that run only on another event (`if: github.event_name == 'repository_dispatch'`) are left out.
  - A `test-<name>` job is an opt-in lane, outside `all`.
  - `--changed` uses each lane workflow's own `changes`-job `grep -qE` regex.
- **juniper-ml, this file's PR.** Three `util/ad-hoc/` scripts:
  - `2026-11-25_run_tests_rollout_sibling_worktree.py`: `create`, `status`, `changed`, `workflows`, `show`,
    `verify-upload` and `remove --merged-into main` for a sibling repo's worktree under `Juniper/worktrees/`.
  - `2026-11-25_run_tests_rollout_workflow_steps.py`: prints a checkout's workflow jobs and steps compactly. Point it at a
    worktree made from `origin/main`.
  - `2026-11-25_run_tests_copy_divergence.py`: section-by-section divergence between two copies of the runner.

## Remaining work

### 1. Copy 2: juniper-data-client

1. Run `create --repo juniper-data-client --branch feat/local-test-runner`, read its `AGENTS.md`, and survey it with the
   workflow-steps script.
2. Start from **recurrence's copy**. It is the more general one. Get it with
   `sibling_worktree.py show --repo juniper-recurrence --file util/run_tests.py`.
3. The predecessor's table names the data-client CI test surface. Its lanes are the **jobs of `ci.yml`**, not per-package
   workflows. New for the engine:
   - `${COVERAGE_FAIL_UNDER}` / `${{ env.COVERAGE_FAIL_UNDER }}`, read from the workflow's or job's `env:` (`package_lane`
     refuses `${{` today);
   - `--cov-report=xml:reports/...` routed to the run directory;
   - generator-parity needs a live registry, so make it opt-in;
   - `scheduled-tests.yml` is probably opt-in too.
4. Write the hermetic suite, wire it into CI, document it in README or AGENTS.md (check that repo's memory budget first),
   then land it: `util/open_signed_pr.py --repo juniper-data-client`, `verify-upload`, then the Overtoad's approval and
   `python3 -u util/safe_merge.py --pr N --repo juniper-data-client --execute`. Read its `MERGED` line.

### 2. The engine-extraction proposal (after copy 2)

The divergence of recurrence's copy from juniper-ml's original, by section, from
`2026-11-25_run_tests_copy_divergence.py`:

| Section | Original lines | Copy lines | Added | Removed | Verdict |
|---|---:|---:|---:|---:|---|
| preamble (docstring, constants) | 186 | 193 | 37 | 30 | changed |
| Reading the workflows | 233 | 268 | 45 | 10 | changed |
| Lanes and jobs | 185 | 243 | 114 | 56 | changed |
| Selection | 194 | 194 | 24 | 24 | changed |
| Environment | 133 | 131 | 0 | 2 | changed |
| Preflight | 132 | 128 | 1 | 5 | changed |
| Planning | 129 | 129 | 0 | 0 | identical |
| Running | 339 | 339 | 0 | 0 | identical |
| Output | 100 | 100 | 0 | 0 | identical |
| The command line | 502 | 504 | 41 | 39 | changed |

Run it again with data-client's copy as a third argument. The likely shape:

- **The engine** becomes a `juniper_ci_tools.run_tests` module. It holds the parsing helpers, environment, preflight,
  planning, running, output, records and the CLI skeleton. Seven of the nine repos already install juniper-ci-tools in CI.
- **A thin per-repo `util/run_tests.py`** holds `discover()`, the groups and aliases, the help text and the checkout check.

Put it to the Overtoad with AskUserQuestion, or with a `notes/` design document and then a question. A dialog sat 9 h 48 m
this session, so ask early and with nothing in flight.

### 3. Still open

- The predecessor's section 2: juniper-ml's four local-only failures.
- Optional: switch recurrence's recipe in juniper-ml's `conf/python_versions.yaml` to `python util/run_tests.py ...`. Its
  venv must also install `juniper-ci-tools`, or the coverage gates are UNAVAILABLE (exit 3).
- The Overtoad's call: make recurrence's `Local test runner suite` a required check.

## Key context and traps (this session)

- **Write and Edit refuse every path under the juniper-ml PRIMARY's `tmp/`**, the session scratchpad included. Write
  scratch files to the worktree's own `tmp/`. Write and Edit **can** write into sibling worktrees under `Juniper/worktrees/`.
- **The command guard also refused:**
  - a `for` loop over `gh api repos/...` URLs;
  - an `echo` naming `$GIT_CEILING_DIRECTORIES`;
  - any compound git line.

  Use the sibling-worktree script. Its `verify-upload` replaces the per-file `gh api` loop.
- **A signed API upload never becomes a local commit**, so the worktree looks dirty after the merge.
  `remove --merged-into main` verifies first, refuses a non-empty `tmp/`, and only then forces.
- **Recurrence's lane jobs skip on a PR that touches no package** (job-level `changes` filters). A runner-only PR's green CI
  proves the runner suite and the gates, not the lanes. The lanes were proven locally (the numbers above).
- **The app lane installs `.[test]` only** (AGENTS.md says `[test,observability]`). The runner follows CI.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log --oneline -3 origin/main      # this file's PR
gh pr view 240 -R pcalnon/juniper-recurrence --json state,mergeCommit --jq '.state, .mergeCommit.oid'   # MERGED 2ce346da...
python3 util/ad-hoc/2026-11-25_run_tests_rollout_sibling_worktree.py show --repo juniper-recurrence --file util/run_tests.py | sed -n 2p
python3 util/ad-hoc/2026-11-25_run_tests_copy_divergence.py util/run_tests.py <recurrence's copy, saved under tmp/>   # the table above
gh pr list -R pcalnon/juniper-data-client --state open --json number,title   # nobody else on run_tests
ls ~/Development/python/Juniper/juniper-ml/tmp/run-tests-rollout--jazzy-plotting-steele | wc -l           # this session's scratch, kept
```

## Git state

- juniper-ml: this file's PR adds this handoff and the three scripts. Nothing else is open from this arc.
- juniper-recurrence: `main` is at `2ce346da` or later. No branch or worktree is left.
- juniper-data-client and the other seven repos are untouched.
- Scratch kept under the retention rule:
  - the juniper-ml primary's `tmp/run-tests-rollout--jazzy-plotting-steele/`: the PR and commit bodies, recurrence's copy
    and the check log;
  - the recurrence primary's `tmp/run-tests/juniper-recurrence--feat--local-test-runner--20261125-0559--be3418c8/`: the
    run directories.
