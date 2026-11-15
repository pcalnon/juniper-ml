# Handoff: Python 3.15 -- deploy Pre-commit now 3.12-3.14 and required; phase 2 started with h5py

**Date**: 2026-11-15 (facts read 04:58Z to 05:45Z)
**Session**: host yamaguchi, juniper-ml worktree `.claude/worktrees/zazzy-seeking-wirth` (session c473918e).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_python-3-15-phase-2-approved-deploy-precommit-matrix.md`.
It is on `main` through juniper-ml#2582. So is its own predecessor,
`HANDOFF_2026-11-15_python-3-15-informational-checks-phase-1-rolled-out.md`. Read both; this file adds only what
this session did and found.

## Goal statement

Continue phase 2 of the Python 3.15 migration: work through what the informational 3.15 legs show. The 3.15 legs
stay INFORMATIONAL (green with a warning). Do not make any 3.15 check required (phase 3), and do not move
`/usr/bin/python3` off 3.14 (phase 4). **The owner granted merge approval for this arc's PRs in this session
(2026-11-15). It does not carry to a new session: confirm with the owner first.**

## Done this session

1. **Task 1 is closed.** juniper-deploy#276 merged at 05:13:44Z as squash `219edf94`. Its `pre-commit` job is a
   3.12/3.13/3.14 matrix with no `experimental` key and no `continue-on-error`, so every leg blocks. The 3.12 leg
   still posts `Pre-commit`, through an expression name. `main`'s CI on `219edf94` concluded `success`, with all
   three Pre-commit contexts green.
   - Ruleset 14715370 then gained `Pre-commit (Python 3.13)` and `Pre-commit (Python 3.14)`, both with
     integration_id 15368. It was one full-replacement PUT from the live JSON, made by
     `util/ad-hoc/2026-11-15_deploy_ruleset_require_precommit_legs.py --execute`.
   - The post-check passed: 12 -> 14 contexts, no existing id drifted, and nothing else changed.
   - The before, PUT-body and after JSON are in `juniper-ml/tmp/py315-phase2-2026-11-15/deploy-ruleset/` (the
     PRIMARY's `tmp/`).
   - `Unit Tests (Python 3.13)` and `(Python 3.14)` are still not required. That is unasked and untouched.
2. **Phase 2, item 1: h5py.** PyPI was re-probed on 2026-11-15. h5py 3.16.0 (2026-03-06) is the newest release, with
   cp310-cp314 wheels only. On `main`, the 3.15 sdist build dies at `Unable to load dependency HDF5 … libhdf5.so:
   cannot open shared object file`. The fix is a step before `Install dependencies`, gated to the 3.15 leg:
   `Install the HDF5 headers h5py builds against (Python 3.15 only)`, running `apt-get install libhdf5-dev
   pkg-config`, with an `id` and the leg's `continue-on-error`. It also adds a CHANGELOG `### Fixed` entry.
   - **juniper-canopy#821** (head `9ab11328`) **MERGED** at 05:42:00Z as `d4e79e06`, with 21/21 required checks
     green. Its 3.15 leg posted `every step passed on Python 3.15`, and **the whole suite passes on 3.15**:
     `8380 passed, 16 skipped`, 0 failed.
     - `main`'s earlier `5 failed, 5120 passed` was a TRUNCATED run. `unit-tests` runs pytest with `--maxfail=5`
       (`ci.yml:279`), so about 3,260 tests never ran.
     - canopy's `unit-tests` has no 3.15 problem left.
   - **juniper-cascor#762** (head `3808ec4e`) **MERGED** at 05:36:08Z as `683eed44`, with 24/24 required checks
     green. On its 3.15 leg, `libhdf5-dev` 1.14.6 installed (the runner image is now Ubuntu 26.04 "resolute"),
     **h5py 3.16.0 built from the sdist**, and the suite ran on 3.15 for the first time: `2 failed, 6065 passed,
     8 skipped`.
     - Both failures are dill: `AttributeError: 'code' object has no attribute 'co_lnotab'`, in
       `test_utils_coverage.py::TestCheckObjectPickleabilityExtended::test_check_object_pickleability_with_unpickleable_attr`
       and
       `test_utils_extended.py::TestCheckObjectPickleabilityFalsePath::test_pickleability_returns_false_for_problematic_attr`.
     - That confirms the inference about `src/utils/utils.py`. See Remaining work item 3.
   - The edits are applied by `util/ad-hoc/2026-11-15_py315_h5py_hdf5_headers.py --repo <r> --worktree <wt>`, and
     checked by `util/ad-hoc/2026-11-15_py315_check_added_step.py`.

## Remaining work (priority order)

1. ~~Finish #821 / #762~~: both merged, and their CI results are recorded in each PR body.
2. **juniper-ml `Regression Tests` 3.15 leg: juniper-ml#2586** (head `cddf5824`) is OPEN with the same step. It
   was opened after flood-4 sent "flood-4 sitting done" at about 05:50Z, which lifted the hold.
   - On `main` (run 43681267307) the failed h5py build ended `Install test dependencies` early, so setuptools, wheel
     and cryptography were never installed, and 6 tests failed on `No module named 'setuptools'`.
   - Read #2586's 3.15 leg, record it in its `## CI result`, and merge with `util/safe_merge.py`.
   - Locally, `tests/test_workflow_script_paths.py`'s `test_raises_when_no_dot_github_workflows_in_ancestors` fails
     because `TMPDIR` is inside the checkout. That is environmental, and the test would need a ceiling. It is not
     #2586's concern.
   - flood-4's peer hold on juniper-ml's `ci.yml`, `CHANGELOG.md`, `docs/REFERENCE.md`, `AGENTS.md` and
     `main-verify.yml` is LIFTED. flood-4 will send one more juniper-ml PR later, porting the gitleaks
     pull-request scan into `ci.yml`'s Security Scan job and `CHANGELOG.md`. It is rebuilt three-way on the
     latest `main`, so nothing needs holding for it.
3. **dill / `code.co_lnotab`**: cascor's 2 failing 3.15 tests, measured on #762, and 2 of juniper-cascor-model's 3.
   No released dill handles 3.15.
   0.4.1 (2026-01-19) is the newest, and its classifiers stop at 3.14. The fix is on dill's `master` only: commit
   `37d2bf71` (2026-05-23), "handle missing co_lntab in 3.15.0b1", which uses `getattr(obj, 'co_lnotab', b'')`.
   - Options: wait for dill 0.4.2 and raise the floor; or install dill from that commit on the 3.15 leg only, which
     is CI-only and informational; or avoid dill on code objects in cascor-model. **That choice is the owner's;
     ask.**
   - Do not cite `uqfoundation/dill#NNN` in a PR body: it posts a backlink on the external project's timeline.
4. **Pre-existing defects** (not 3.15), each worth its own PR, both still open:
   - `scheduled-tests.yml`'s `-m "slow or integration"` errors with `Unknown marker(s) … slow` in
     juniper-data-client, juniper-cascor-client and juniper-cascor-worker;
   - `ci-cascor-model.yml` is red on cascor `main`, because cascor#687's `_PROJECT_API_START_FRESH_REQUIRED_MARKER`
     never reached `juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`.
5. **Cleanup** (`notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`; check each `tmp/` against the retention rule first):
   - this session's worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`:
     `juniper-deploy--ci--pre-commit-python-matrix--20261114-2302--dd299fbf` (merged; its `tmp/` holds scratch venvs
     and logs only) and the two `*--ci--python-3-15-h5py-hdf5-headers--20261114-2312--*`;
   - the predecessor's nine `*python-3-15-informational*` and six `*python-3-15-green-legs*` worktrees;
   - `juniper-ml/.claude/worktrees/agent-a071c56ac10b0da13`.

## Open owner questions

1. **dill on 3.15.** Should we wait for a dill release and raise the floor, install dill from commit `37d2bf71` on
   the informational 3.15 leg only, or stop pickling code objects with dill in cascor and cascor-model?
2. Carried over from the predecessor and still unanswered: should deploy's `Unit Tests (Python 3.13)` and
   `(Python 3.14)` become required in ruleset 14715370? Today they block only through the Quality Gate.

## Key context / traps found this session

- **This session's isolation refuses** any command that names git with `$(...)`, a loop, a heredoc, `--exclude-dir=.git`,
  or (in some forms) a `.github/` path. Use plain single commands, or a `util/ad-hoc/` script that builds the
  path itself. The Write tool also refuses juniper-ml's PRIMARY checkout: a paths file written there silently
  did not exist, and `2026-11-15_py315_readback.bash` then exited 0 having checked NOTHING. Check `test -s` first.
- **`… | tail` hides the exit code.** Capture `$?` unpiped.
- **juniper-deploy's `pytest tests/` drives live local services.** Its canopy smoke POSTed to a live canopy on
  127.0.0.1:8050, and only auth (401) stopped a training start. Memory:
  `reference_deploy_pytest_drives_live_local_services.md`.
- The flood-4 session is porting the Gitleaks PR-commit scan to juniper-deploy. Its PR is rebuilt three-way on the
  latest `main`, and it knows about #276 and the ruleset change.

## Verification commands

```bash
/usr/bin/python3 --version                                  # 3.14.x
gh api repos/pcalnon/juniper-deploy/rules/branches/main --jq '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]|length'   # 14
gh pr view 821 --repo pcalnon/juniper-canopy --json state,mergedAt
gh pr view 762 --repo pcalnon/juniper-cascor --json state,mergedAt
gh run list --repo pcalnon/juniper-ml --workflow ci.yml --branch main --limit 1 --json conclusion,headSha
```

## Git status

- The juniper-ml worktree `zazzy-seeking-wirth` was fast-forwarded to `main` `725c6343`. It holds #2586's
  `ci.yml` and `CHANGELOG.md` edits, uncommitted, because #2586's signed API commit carries them. Restore both
  from `origin/main` once #2586 merges.
- This file and four `util/ad-hoc/2026-11-15_*` scripts reach `main` through a provenance PR that only adds files:
  `deploy_precommit_python_matrix.py`, `deploy_ruleset_require_precommit_legs.py`, `py315_h5py_hdf5_headers.py`
  and `py315_check_added_step.py`.
- Open branches of this arc: juniper-ml `docs/handoff-py315-phase2-deploy-precommit-h5py` (#2585, provenance) and
  `ci/python-3-15-h5py-hdf5-headers` (#2586). No other repo has one. canopy's `ci/gitleaks-pr-commit-scan` PR
  (#822) is the flood-4 session's. Its CHANGELOG hunk (line 51) does not overlap #821's (line 37).
