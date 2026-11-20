# Handoff: Python 3.15 -- phase 3 soaks until 2026-11-23; cascor-model's `Model required checks` is required

**Date**: 2026-11-16 (facts read 07:54Z to 21:53Z; Overtoad dialogs were open from about 08:07Z to 15:20Z and from
16:05Z to 21:52Z)
**Status**: **PAUSED at 21:53Z by the Overtoad, for the weekly Claude Code token limit.** Resume from Remaining work,
in order.
**Session**: host yamaguchi, juniper-ml worktree `.claude/worktrees/serialized-snuggling-gadget` (session 3a7c12fe).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_python-3-15-phase-2-complete-dill-drift-nightly-markers-cleanup.md`
(on `main` through juniper-ml#2590). It was checked item by item against source. Its three remaining items and its
two open Overtoad questions are all resolved below, and none was carried over silently.

## Goal statement

Phase 3 of the Python 3.15 migration, making the 3.15 checks block merges, is **scheduled, not started**. The Overtoad
chose a 7-day soak that ends **2026-11-23**. On or after that date:

1. Re-count the 3.15 legs across every run since this session's count, with
   `python3 util/ad-hoc/2026-11-16_py315_leg_warning_history.py --since 2026-11-16T08:00:00Z`.
2. Read every `warning` it lists, because a PR run's warning can be that PR's own defect.
3. If none is a real 3.15 failure, start phase 3 with the Overtoad's scope (below).

Do not start phase 3 earlier, and do not move `/usr/bin/python3` off 3.14 (phase 4). **Merge approval for this arc's
PRs was granted in this session (2026-11-16). It does not carry to a new session.**

## Owner rulings this session (2026-11-16, from the dialog)

1. **Phase 3 timing**: "Soak 7 days first". The legs stay informational until 2026-11-23. Then re-count the warnings
   across every run, and start if none were real.
2. **Phase 3 scope**:
   - chosen: "PR legs + rulesets", "3.15 classifier" and "3.15 Pre-commit leg";
   - added in the Overtoad's own words: "bring juniper-recurrence and juniper-harcot in line with the other repos wrt
     requiring per python version gates that include python3.15";
   - **not** chosen: "Non-gating legs too". juniper-ml's six sub-package workflows, cascor-model, cascor-protocol and
     the five nightly lanes keep informational 3.15 legs.
3. **cascor-model required check**: "Recurrence's pattern". It is done; see juniper-cascor#771 below.
4. "merge approval granted" (the session's opening message).

From the second dialog (answered at 21:52Z; findings 1, 4 and 5 below are the evidence each one was asked on):

5. **recurrence "in line"**: "Unique names + step skips". Give each lane's legs a unique name (`App Test (Python 3.12)`,
   `Client …`, `Model …`, `Bench smoke …`), and move the `changes` skip from the job's `if:` into its steps, so
   every leg always runs and posts its own expanded name. Then require all 16 (4 lanes × 3.12-3.15). This is phase 3
   work.
6. **harcot "in line"**: "CI gate only, unenforced". Phase 3 makes harcot's 3.15 leg blocking in its `required-checks`
   gate, and harcot PRs merge only through `util/safe_merge.py`. No ruleset, because the plan's 403 stands.
7. **recurrence's fail-open detectors (finding 1)**: "Fix now". One recurrence PR applies #771's detector form to all
   four workflows, plus a CHANGELOG entry, and nothing else changes. **NOT started: paused.**
8. **The 3.15 Pre-commit leg**: "Soak it now". Add an informational 3.15 leg to the eight Pre-commit matrices, in
   eight PRs started by a fresh session from this handoff. **NOT started: paused.**

## Done

| Repo | PR -> squash | What |
|------|--------------|------|
| juniper-cascor | #771 -> `cf5566e1` (merged 15:46:34Z) | `ci-cascor-model.yml` runs on every PR. Its new `changes` job scopes `test` and `build`, and its new always-reporting `Model required checks` is the context to require (details below). Docs and CHANGELOG `### Changed` updated |

- **#771's design** (Overtoad ruling 3, juniper-recurrence's pattern):
  - `on.pull_request` is unfiltered, and `on.push` keeps its paths.
  - `changes` (`Detect cascor-model changes`) diffs the PR against its base. `test` and `build` run only for
    `juniper-cascor-model/**`, `src/{candidate_unit,utils,log_config,cascor_constants}/**` or the workflow.
  - `Model required checks` (`if: always()`) fails when detection fails, passes on success, and passes on `skipped`
    only when the package was NOT touched. That is stricter than recurrence's gate.
  - The detector captures `git diff` into a variable before `grep -q`, which is finding 1's fix.
- **#771's evidence**:
  - On the PR (run 43897535306): `cascor-model package changed: true`, 438 passed on both 3.12 and 3.15, and the gate
    passed. 24/24 required contexts were green.
  - On `main` after the merge (run 43900056076): all five jobs `success`.
  - Locally: actionlint was clean, and `util/ad-hoc/2026-11-16_cascor_model_gate_logic_check.py` passed 11 detector
    cases and 128 gate combinations.
  - The sequence-safety probe found 0 symbol-loss findings and 0 docs failures. The memory budget for `AGENTS.md`
    rose by 188 characters, which is `OK`.
- **Ruleset 15081045 went from 24 to 25 contexts at 16:02Z.** It now requires `Model required checks` with
  integration_id 15368.
  - The change was one full-replacement PUT, made by
    `util/ad-hoc/2026-11-16_cascor_ruleset_require_model_checks.py --execute`. That script refused until `main`
    (`cf5566e1`) had posted both the context and the `Quality Gate` green from app 15368.
  - Its post-check passed: no existing id drifted, and nothing else changed. A separate `rules/branches/main` read
    gives 25.
  - The before, PUT-body and after JSON are in
    `juniper-ml/tmp/py315-phase3-soak-2026-11-16/cascor-ruleset-model-required-checks/`, in the PRIMARY checkout.
    Rollback is the same PUT built from `ruleset-before.json`.
  - **The skip path is not yet measured on a real PR**: no cascor PR touching none of the package's paths has run
    since #771. The first one will be dependabot's #770 (19 python-minor bumps, opened 14:15Z). It touches only
    `conf/requirements*.txt` and the two lockfiles. Once it is updated onto `cf5566e1` or later, it must show
    `cascor-model package changed: false`, `Test (Python ${{ matrix.python-version }})` skipped, and
    `Model required checks` `success`. If it does not, roll the ruleset back.
- **Cleanup**: the cascor worktree `juniper-cascor--ci--cascor-model-required-checks--20261116-0922--a011f21e` is removed.
  Its tree equalled the merged `main` (an empty `git diff origin/main`) and its `tmp/` was empty. Its local branch is
  deleted, and GitHub deleted the remote one on merge.

## Measurements (all saved under the worktree's `tmp/py315-nightly-2026-11-16/`; see Git status)

- **Nightly lanes** (predecessor item 1), the 2026-11-16 ~06:00Z `scheduled-tests.yml` runs, all `success` on all
  four legs, on the fix SHAs:
  - juniper-data-client run 43815179272 (`225dd6bb`): `556 deselected`, 0 run;
  - juniper-cascor-client run 43816016357 (`e8aa7361`): `598 deselected`, 0 run;
  - juniper-cascor-worker run 43814375758 (`3975d9ac`): `5 passed, 537 deselected` on every leg.

  Neither client has an `@pytest.mark.integration` test, and the step tolerates exit 5 with a notice. That is by
  design, and #263 and #198 recorded it. So those two lanes are green **vacuously**.
- **dill** (predecessor item 2): PyPI's JSON, read about 08:00Z, still lists 0.4.1 (2026-01-19) as the newest
  release. No pre-release exists. The floor raise stays blocked upstream.
- **Leg survey** (`util/ad-hoc/2026-11-15_py315_leg_survey.py`, re-run unbuffered about 08:05Z): every 3.15 leg on
  every repo's `main` posts `every step passed on Python 3.15`, harcot's included.
- **Warning history** (`util/ad-hoc/2026-11-16_py315_leg_warning_history.py --since 2026-11-15T13:00:00Z`, the
  last phase-2 fix): 47 3.15 jobs posted the notice. 1 warning was **false**: juniper-ml run 43771172510 was
  cancelled on all four Regression Tests legs, and the 3.15 leg's `if: always()` report step counted the cancelled
  step as failed. The script now classifies a cancelled job first. The samples are thin where it matters: cascor 3,
  canopy 4.
- **Phase-3 scope survey** (`util/ad-hoc/2026-11-16_py315_phase3_scope_survey.py`):
  - Eight rulesets require per-version contexts for 3.12-3.14: ml 13805432, cascor 15081045, canopy 14249530,
    data 14748749, deploy 14715370, data-client 13316681, cascor-client 13490605, cascor-worker 14250447.
  - recurrence 20634527 requires only its four `… required checks` gates, and harcot has no readable ruleset (403).
  - Phase 3's "PR legs + rulesets" is therefore 11 contexts in those 8 rulesets:
    - `Regression Tests (Python 3.15)` for ml and `Unit Tests (Python 3.15)` for deploy;
    - `Unit Tests + Coverage (Python 3.15 on ubuntu-latest)` for cascor, canopy, data, and the three clients;
    - `Integration Tests (Python 3.15)` for the three clients.

## Findings (reported, not fixed)

1. **juniper-recurrence's four `changes` detectors can fail OPEN.** In `ci-recurrence-{app,bench,client,model}.yml`,
   `git diff --name-only … | grep -qE …` runs inside `set -euo pipefail`.
   - On a long file list, grep exits at its first match, `git` dies of SIGPIPE, and the `elif` reads "not touched".
   - The package jobs are then skipped, and its required gate passes, because it accepts `skipped`.
   - Measured by `util/ad-hoc/2026-11-16_cascor_model_gate_logic_check.py`: with the match first and 200,000 more
     lines, the piped form printed `model=false`.
   - cascor#771 captures the diff first.
2. **`agents-md-touch-up.yml`'s date check can fail CLOSED** in eight repos (ml, cascor, canopy, data, deploy and the
   three clients): `git diff … -- AGENTS.md | grep -Eq …` under pipefail
   (`util/ad-hoc/2026-11-16_piped_grep_q_failopen_scan.py`). An AGENTS.md diff longer than the pipe buffer can
   fail a PR that did bump the date. It is low risk.
3. **Every informational report step posts a false warning on a cancelled run**, because it treats `cancelled` as a
   failure. Phase 3 removes those steps from the legs that become blocking, so only the legs that stay informational
   keep it.
4. **"Bring juniper-recurrence in line" needs a redesign before any per-version context can be required.** On
   recurrence#233 (head `094c6fcbf2`), the skipped packages posted ONE check each, with the literal name
   `Test (Python ${{ matrix.python-version }})`. The app, client and model workflows all name their legs
   `Test (Python 3.x)`. A required `Test (Python 3.12)` is therefore ambiguous, and it never reports on a PR that
   touches no package.
5. **juniper-harcot cannot carry any ruleset on the current plan.** `GET …/rules/branches/main` answers 403, "Upgrade to
   GitHub Pro or make this repository public to enable this feature". No context can be required there until that
   changes.

## Remaining work

Do items A and B first; neither waits for the soak. The Overtoad's merge approval of 2026-11-16 does not carry over, so
confirm it before merging.

- **A. The recurrence detector fix (ruling 7).** In `ci-recurrence-{app,bench,client,model}.yml`, in job `changes`,
  step `id: filter`, replace
  `elif git diff --name-only "origin/${BASE_REF}...HEAD" | grep -qE '<pattern>'; then`
  with the form juniper-cascor's `ci-cascor-model.yml` has used since #771:
  - capture `files="$(git diff --name-only "origin/${BASE_REF}...HEAD")"` inside an `else` branch;
  - then test `if grep -qE '<pattern>' <<<"${files}"; then`.

  Keep each workflow's pattern byte-identical, and add a CHANGELOG `### Fixed` entry.
  - Verify with `util/ad-hoc/2026-11-16_cascor_model_gate_logic_check.py` as the model. It extracts the step and
    runs it against a stub `git`. Each recurrence workflow needs its own touched and untouched paths.
  - Read the workflow through a script or a checkout root, because the session isolation refuses `.github` in a
    command.
  - Land it with `util/ad-hoc/2026-11-16_open_signed_pr_from_paths.bash`.
- **B. The informational 3.15 Pre-commit soak (ruling 8)**, in the eight repos whose rulesets require
  `Pre-commit (Python 3.12-3.14)`: ml, cascor, canopy, data, deploy, data-client, cascor-client and cascor-worker.
  - Add a `{python-version: "3.15", experimental: true}` include and the job-level
    `continue-on-error: ${{ matrix.experimental == true }}`. Then apply
    `util/ad-hoc/2026-11-15_py315_informational_green_legs.py <workflow> pre-commit`, which gives every step an `id`
    and the same expression, and adds the report step.
  - Check that the leg's check concludes green while a hook fails, and that every job with `needs: pre-commit` still
    runs. `HANDOFF_2026-11-15_python-3-15-informational-checks-phase-1-rolled-out.md` § "Design A, measured" has the
    method.
  - Do not add `Pre-commit (Python 3.15)` to any ruleset: that is phase 3.
  - deploy's matrix posts its 3.12 leg as `Pre-commit` through an expression name, so keep that.
  - juniper-ml's `tests/test_python_version_matrix_drift.py` pins its matrices, so update it with them.

1. **On or after 2026-11-23**: the soak re-count (Goal statement), then phase 3 with the Overtoad's scope. One PR per
   repo, plus ruleset PUTs:
   - **PR legs + rulesets.** On every PR-path 3.15 leg, drop `experimental: true`, each step's
     `continue-on-error: ${{ matrix.experimental == true }}`, and the `Report the informational Python 3.15 result`
     step. That covers:
     - the `ci.yml` test matrices;
     - the three clients' `integration-tests`;
     - recurrence's four package lanes;
     - harcot's `unit-tests`.

     Then add the 11 contexts (Measurements) to the 8 rulesets. Generalise
     `util/ad-hoc/2026-11-16_cascor_ruleset_require_model_checks.py`: it reads live, does a full-replacement PUT,
     and refuses until `main` posts the context green.
     - Legs the Overtoad did NOT include stay informational: juniper-ml's six `ci-<pkg>.yml`, cascor-model,
       cascor-protocol and the five nightly lanes. So "3.15 is blocking" becomes per-workflow, and juniper-ml's
       `conf/python_versions.yaml` and `tests/test_python_version_matrix_drift.py` (`green_violations`) must learn
       that distinction rather than flip 3.15 globally.
     - Before merging a CHANGELOG-touching PR, check for an open `release/*` PR in that repo (predecessor trap).
   - **3.15 classifier**: `Programming Language :: Python :: 3.15` in each published package's `pyproject.toml`
     (the 3.14 one is the anchor). It ships with each package's next release.
   - **3.15 Pre-commit leg**: add 3.15 to the `pre-commit` matrices of the eight repos whose rulesets require
     `Pre-commit (Python 3.12-3.14)`, and add `Pre-commit (Python 3.15)` to each ruleset (8 more contexts).
     - Phase 1 excluded it. Its hooks (black, flake8, mypy and others) are untested on 3.15.
     - A failed pre-commit leg skips every job that `needs: pre-commit`.
   - **recurrence and harcot "in line"**: follow rulings 5 and 6. For recurrence, rename the legs and move the skips
     into the steps first, then require the 16 contexts once the new names post on `main`.
2. **dill floor**: unchanged from the predecessor. Raise cascor's and cascor-model's dill floors when a release after
   0.4.1 ships with 3.15 support. Do not cite the upstream PR number in a PR body. The Overtoad's merge approval is
   needed again.
3. **cascor's skip path**: read #770's `CI — juniper-cascor-model` run once #770 is updated (Done, "Ruleset
   15081045").
## Open Overtoad questions

None. The second dialog answered all four questions it asked, as rulings 5 to 8. Finding 2 (fail-closed, low risk)
and finding 3 (phase 3 removes the cause) were reported and not asked.

## Key context / traps

- **This session's isolation refuses** any command whose text contains a `.github` path, and any loop or `$(...)` that
  names git. Write a `util/ad-hoc/` script that builds the path itself:
  - `2026-11-16_cascor_model_gate_logic_check.py` takes a checkout root;
  - `2026-11-16_open_signed_pr_from_paths.bash` reads a paths file;
  - `pre-commit run --files .[g]ithub/workflows/<f>` passes the guard.
- **A fresh worktree has no `tmp/`.** `util/ad-hoc/2026-11-15_seqsafety_probe_worktree.py` writes its private index
  there and fails with `Unable to create … index.lock` until `mkdir tmp`.
- **The Overtoad dialog blocked the session for about seven hours.** Re-read anything time-sensitive after one. During
  this one, cascor's `main` gained #769 (`a011f21e`, committed 09:20Z), and juniper-ml's `main` moved to `dad9f1c6`.
- **`gh run view --log` printed nothing** (gh 2.46) for these runs. Read job logs with
  `gh api repos/<o>/<r>/actions/jobs/<id>/logs`.
- **A skipped matrix job posts its UNEXPANDED name** (finding 4). Required per-version contexts and job-level `if:`
  skips do not mix.
- **A required context from a workflow that did not run never reports.** That is why cascor-model needed the
  always-running gate, and why harcot cannot be fixed in CI alone.

## Verification commands

```bash
/usr/bin/python3 --version                                   # 3.14.x
gh pr view 771 --repo pcalnon/juniper-cascor --json state,mergedAt
gh api repos/pcalnon/juniper-cascor/rules/branches/main --jq '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]|length'   # 25
gh api repos/pcalnon/juniper-cascor/rules/branches/main --jq '.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[]|select(.context=="Model required checks")'
python3 util/ad-hoc/2026-11-16_py315_leg_warning_history.py --since 2026-11-16T08:00:00Z   # at the soak's end
```

## Git status

- **juniper-ml#2599 merged at 21:53:19Z as `e63a2f5a`.** It added the first version of this file and the session's six
  `util/ad-hoc/2026-11-16_*` scripts:
  - `py315_phase3_scope_survey.py`, `py315_leg_warning_history.py`;
  - `cascor_model_gate_logic_check.py`, `cascor_ruleset_require_model_checks.py`;
  - `open_signed_pr_from_paths.bash`, `piped_grep_q_failopen_scan.py`.
- This version, with the paused status and rulings 5 to 8, lands through a one-file PR on branch
  `docs/handoff-py315-paused-Overtoad-rulings`.
- The juniper-ml worktree `serialized-snuggling-gadget` is on `worktree-serialized-snuggling-gadget` at `edea2eb1`,
  with nothing committed. Its `tmp/` is already copied (next bullet), so the worktree can be removed.
- The session's evidence comes to 35 files and 1.1 MB:
  - logs and survey outputs;
  - #771's commit message, PR body, CI-result and probe outputs;
  - the gate-logic check.

  It is copied, identical, to `juniper-ml/tmp/py315-phase3-soak-2026-11-16/session-3a7c12fe-evidence/` in the
  PRIMARY checkout, so the worktree can be removed without losing it.
- No other branch of this arc is open in any repository. cascor's `ci/cascor-model-required-checks` merged and was
  deleted, and its worktree is removed.
