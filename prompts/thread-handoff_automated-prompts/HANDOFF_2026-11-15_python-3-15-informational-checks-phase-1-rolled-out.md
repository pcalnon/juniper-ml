# Handoff: Python 3.15 informational checks -- phase 1 rolled out to all ten repos; phase 2 waits on the owner

**Date**: 2026-11-15 (facts read 00:06Z to 01:51Z)
**Session**: host yamaguchi, juniper-ml worktree `.claude/worktrees/witty-giggling-twilight` (session 2d726db0).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-14_python-3-15-informational-checks-phase-1-surveyed.md`
(juniper-ml#2566). Its owner request and phase plan stand; its open design question is settled below.

## Goal statement

Phase 1 of 4 is done: Python 3.15 runs in every repo's CI test matrices and through a local helper, and its results
are visible but block nothing. The next step is **phase 2: work through the 3.15 problems below. It needs the
owner's go-ahead. Do not start it, and do not make any 3.15 check required (phase 3) or move the host default
(phase 4).**

## Owner rulings (2026-11-14)

1. Local: a juniper-ml `util/` helper plus `conf/python_versions.yaml` (blocking 3.12-3.14, informational 3.15),
   never in pre-commit. 2. **No 3.15 pre-commit** in phase 1. 3. juniper-harcot in scope; **juniper-deploy gets a
   3.12-3.15 test matrix**. 4. Merge approval was granted for this arc's PRs in that session. **It does not carry to a
   new session.**

## Design A, measured

juniper-data#538, run 43655144734: a temporary step failed the 3.15 leg on purpose. The leg's check read `failure`,
but the hard Quality Gate printed `Unit Tests: success` and passed, every `needs: [unit-tests]` job ran, the run
concluded `success`, and the PR was `UNSTABLE`, which merges accept. cascor#759, canopy#819 and ml#2567 then
reproduced this with REAL failures.

The pattern:
- an `include: {python-version: "3.15", experimental: true}` entry, plus `os: ubuntu-latest` where the matrix has an
  os axis;
- job-level `continue-on-error: ${{ matrix.experimental == true }}`;
- the new context in no ruleset and in no gate's `needs:`.

A static job name gets the auto-suffix `(3.15, true)`, so spell the suffix out:
`Slow / Integration Tests (${{ matrix.python-version }})`. Memory:
`reference_matrix_leg_continue_on_error_keeps_needs_result_success.md`.

## PR ledger (all squash-merged under the session's approval)

| Repo | PR -> squash | 3.15 result on the PR run |
|------|--------------|---------------------------|
| juniper-data | #538 -> `d48c22e3` | pass (2401 passed, 98.12%); the scheduled matrix gained the leg too |
| juniper-recurrence | #234 -> `5de501c8` | app, client, model and bench all pass |
| juniper-ml | #2567 -> `a949d504` | regression leg FAILS at install (h5py); the six sub-package workflows have the leg and run on their path filters |
| juniper-deploy | #274 -> `c5df10d1` | 3.12 leg keeps the required `Unit Tests` through an expression name; 3.13, 3.14 and 3.15 pass |
| juniper-data-client | #261 -> `27b5f2f5` | unit pass; the integration leg selects 0 tests |
| juniper-cascor-client | #195 -> `62c5bac6` | unit pass; the integration leg selects 0 tests |
| juniper-cascor-worker | #228 -> `7a83b024` | unit (torch 2.14.0+cpu) and integration pass |
| juniper-harcot | #21 -> `36c07da0` | pass (1151 passed, 100%); merged by hand (`gh pr merge --match-head-commit`), since rulesets 403 there |
| juniper-cascor | #759 -> `f97ea0c5` | unit FAILS at install (h5py); cascor-model: `dill` reads `code.co_lnotab` |
| juniper-canopy | #819 -> `528efa3c` | unit FAILS at install (h5py 3.16.0); the scheduled lane passes on 3.15.2 (532 passed) |
| juniper-ml (helper) | #2571 -> `0578d2ec` | `util/python_version_check.py` + `conf/python_versions.yaml`; local smoke run on data-client 3.15.2 PASSED (537 passed) |

**A release proposal merged under two of these PRs** (cascor#758 v0.14.0, canopy#818 v0.10.0, both armed). Each
update-branch merge then filed the 3.15 entry inside the released section.
`util/ad-hoc/2026-11-15_py315_cascor_changelog_relocate.py` moved each entry back under `[Unreleased]`. Before
merging a CHANGELOG-touching PR, check for an open `release/*` PR in that repo, and let the proposal land first.

## Local helper (juniper-ml#2571)

```bash
python3 util/python_version_check.py --list
python3 util/python_version_check.py --repo juniper-data-client --python 3.15   # exit 0 unless --strict
```

- Venv: `{JUNIPER_ROOT}/<repo>/tmp/pyvenv/py<ver>/`, built from `/usr/bin/python<ver>`.
- Output: logs and `summary.json` in `juniper-ml/tmp/python-version-checks/<UTC stamp>/`.
- `tests/test_python_version_matrix_drift.py` holds juniper-ml's CI matrices to the config.

## Phase-2 input (the 3.15 problems; fix nothing in phase 1)

1. **h5py has no CPython 3.15 wheel.** The sdist build needs libhdf5, which the runners lack. It stops the 3.15 leg
   at `Install dependencies` in juniper-ml, juniper-cascor and juniper-canopy, so those legs test nothing yet.
2. **`dill` reads `code.co_lnotab`, which 3.15 removed.** This is 2 of juniper-cascor-model's 3 failures on 3.15.
   Inferred, not measured: cascor's `src/utils/utils.py` may hit it once h5py installs.

## Pre-existing defects found (not 3.15; report, don't fix)

- `scheduled-tests.yml` is red on EVERY leg since about 2026-10-28 in juniper-data-client, juniper-cascor-client
  and juniper-cascor-worker: `ERROR: Unknown marker(s) in '-m' expression: slow` (pytest exit 4).
- `ci-cascor-model.yml` is red on cascor `main`: cascor#687's `_PROJECT_API_START_FRESH_REQUIRED_MARKER` never
  reached `juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`.
- The integration matrices of data-client and cascor-client select zero tests on every version.
- The `JuniperCanopy1` env is below canopy's floors: observability 0.4.0 (floor `>=0.4.1`) and service-core 0.5.0
  (floor `>=0.7.1`).
- canopy's `.codecov.yml` sets `after_n_builds: 3`, but four reports upload.
- Stale version claims the agents left alone, listed in each PR body:
  - cascor-client `AGENTS.md:119-121` and `docs/QUICK_START.md:27`;
  - worker `AGENTS.md:8`;
  - recurrence `AGENTS.md:250` § Status;
  - deploy `AGENTS.md` § CI/CD job table.

## Open owner questions

1. Should juniper-deploy's `Pre-commit` also run 3.13 and 3.14?
2. Should deploy's `Unit Tests (Python 3.13)` and `(Python 3.14)` become required in ruleset 14715370? Today they
   block only through its Quality Gate.

## Follow-up the same night: the informational legs now conclude GREEN (owner request 2026-11-15)

The owner reported that every juniper-ml PR read as failing. The job-level `continue-on-error` kept the gates green
(#2568, #2569 and #2572 merged past it, and no 3.15 context is required), but the 3.15 leg's own check concluded
`failure`: a red X on every PR, `UNSTABLE`, and `gh pr checks` failing.

**juniper-ml#2578** (branch `ci/python-3-15-informational-green-legs`) makes the leg conclude green:
- every step of each 3.15 job gets an `id` and `continue-on-error: ${{ matrix.experimental == true }}`;
- a last step, `Report the informational Python 3.15 result`, reads `toJSON(steps)` and emits a `::warning` naming
  the failed steps (or a `::notice` when all passed), plus a job-summary table;
- applied by `util/ad-hoc/2026-11-15_py315_informational_green_legs.py`;
- guarded by `tests/test_python_version_matrix_drift.py`'s `green_violations`.

It was measured on #2578's head `91591864`: `Regression Tests (Python 3.15)` concluded `success` while 2 of its steps
failed, and carried the warning. **#2578 merged 2026-11-15T04:10:39Z (`be092a2e`).** The owner chose "All nine now", and
the same script, applied on branch `ci/python-3-15-green-legs`, is MERGED in every sibling repo:

| Repo | PR -> squash | 3.15 check after the fix |
|------|--------------|--------------------------|
| juniper-cascor | #760 -> `28975264` | unit `success` + warning (install, tests and coverage steps failed: h5py); cascor-model `success` + warning (3 tests); protocol notice |
| juniper-canopy | #820 -> `bab3ec8d` | unit `success` + warning (install failed; then 5120 passed, 5 failed `No module named 'h5py'`); scheduled notice |
| juniper-data | #541 -> `de9ff9d6` | unit notice (2530 passed) |
| juniper-cascor-worker | #229 -> `68782443` | unit and integration notice |
| juniper-data-client | #262 -> `56ab8ebb` | unit and integration notice |
| juniper-cascor-client | #197 -> `1ad7f5c8` | unit and integration notice |
| juniper-deploy | #275 -> `dd299fbf` | `Unit Tests (Python 3.15)` notice; the required `Unit Tests` still posts |
| juniper-recurrence | #235 -> `e150add6` | all four lanes notice |
| juniper-harcot | #23 -> `6e5e4bd2` | notice |

How these PRs merged:
- **None was merged by the session or its agents.** Auto-merge was armed from the `pcalnon` account (the owner's PR
  sweeper; see memory `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`). The same account
  re-armed #2575 after the session had disarmed it to honour a peer's merge hold.
- **harcot#23 merged before its checks finished.** That private repo enforces no rules. Its checks then passed on the
  merged head, and so did `main`.
- **The squash merges reorder the commit trailers.** GitHub moves `Co-authored-by` into its own final paragraph.
- **Phase-2 findings** are unchanged by the fix, and now readable from each leg's warning: h5py (ml, cascor, canopy)
  and dill's `co_lnotab` (cascor-model).

## Remaining work

1. Clean up the rollout worktrees per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`. Their `tmp/` dirs hold test venvs
   and CI logs: check each against the retention rule before `git worktree remove`.
   - `Juniper/worktrees/<repo>--ci--python-3-15-informational--*`, nine of them (counted 2026-11-15 01:51Z):
     data, recurrence, deploy, data-client, cascor-client, cascor, cascor-worker, canopy, harcot. List them with
     `ls -d /home/pcalnon/Development/python/Juniper/worktrees/*python-3-15*`.
   - the helper agent's `juniper-ml/.claude/worktrees/agent-a071c56ac10b0da13`.
2. Put the two open questions to the owner, then phase 2 if the owner says go. Start with h5py, which blocks three
   repos' legs.

## Verification commands

```bash
/usr/bin/python3 --version     # must stay 3.14.x (phase 4 is deferred)
for r in juniper-data juniper-cascor juniper-canopy juniper-ml; do gh pr list --repo pcalnon/$r --state merged --head ci/python-3-15-informational --json number,mergedAt --jq '.[]|"'$r' #\(.number) \(.mergedAt)"'; done
gh pr view 2571 --repo pcalnon/juniper-ml --json state,mergedAt
gh run list --repo pcalnon/juniper-ml --workflow ci.yml --branch main --limit 1 --json conclusion,headSha
```

**Expect** Python 3.14.x; one merged PR per repo; #2571 merged; main's last ci.yml run `success`, even though its
`Regression Tests (Python 3.15)` job fails.

## Git status

The juniper-ml worktree `witty-giggling-twilight` is at `main`. The provenance PR carrying this file adds the 16
`util/ad-hoc/` scripts the arc used:
- eight per-repo `2026-11-14_py315_informational_<repo>.py` edit scripts;
- seven `2026-11-15_py315_*` helpers from the cascor agent;
- the CHANGELOG relocate script.

No other branch for this arc remains open.
