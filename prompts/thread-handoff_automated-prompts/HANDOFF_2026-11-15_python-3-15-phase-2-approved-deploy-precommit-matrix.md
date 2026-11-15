# Handoff: Python 3.15 -- phase 2 approved; juniper-deploy pre-commit gets a 3.12-3.14 matrix first

**Date**: 2026-11-15 (facts read up to 04:45Z)
**Session**: host yamaguchi, juniper-ml worktree `.claude/worktrees/witty-giggling-twilight` (session 2d726db0).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_python-3-15-informational-checks-phase-1-rolled-out.md`.
It is on `main` through juniper-ml#2575 and #2580, and holds:
- the phase-1 PR ledger (eleven PRs);
- the green-informational-legs fix (juniper-ml#2578 plus nine sibling PRs, all merged);
- the measured design;
- the pre-existing defects found.

Read it first. This file adds only the owner's two new directives and the plan for them.

## The owner's directives (2026-11-15, verbatim)

> deploy's pre-commit job should also run on 3.13 and 3.14, with these checks treated the same as the existing 3.12
> check.
> approval for phase 2 granted.

**Merge approval does not carry to a new session.** The owner's memory policy is
`feedback_headless_merge_approval_policy.md`. Confirm with the owner that "approval for phase 2 granted" covers
merging the phase-2 PRs before you merge any.

## Task 1: juniper-deploy `Pre-commit` on 3.12, 3.13 and 3.14, all blocking and required

Today `.github/workflows/ci.yml` job `pre-commit` (`name: Pre-commit`) runs once, on `env.PYTHON_VERSION` "3.12".
Ruleset 14715370 requires the version-less context `Pre-commit`, and the Quality Gate hard-checks
`needs.pre-commit.result`.

**Design** (the same trick juniper-deploy#274 used for `Unit Tests`):
1. `strategy: {fail-fast: false, matrix: {python-version: ["3.12", "3.13", "3.14"]}}`. Add no `experimental` key and
   no `continue-on-error`: all three legs block.
2. Name the job `name: ${{ matrix.python-version == '3.12' && 'Pre-commit' || format('Pre-commit (Python {0})',
   matrix.python-version) }}`. The 3.12 leg still posts exactly `Pre-commit`.
3. In this job only, setup-python and its cache key use `matrix.python-version` instead of `env.PYTHON_VERSION`.
   Today the key is `pre-commit-${{ runner.os }}-${{ env.PYTHON_VERSION }}-…`.
4. Check what `needs: [pre-commit]`. A failed 3.13/3.14 leg now fails `needs.pre-commit.result`, which is intended:
   blocking, the same as 3.12.
5. Run deploy's tests that read `ci.yml` (`tests/test_gitleaks_config.py`, `tests/test_published_image_refs.py`, and
   any other reader a grep finds), and pre-commit itself under 3.13 and 3.14 locally if you can. The other repos
   already run their pre-commit on 3.12-3.14.
6. CHANGELOG `[Unreleased]` entry, plus the CI doc lines that list deploy's jobs.

**"Treated the same as the existing 3.12 check" means REQUIRED too.** Only after the PR merges and `main` posts both
new contexts:
- add `Pre-commit (Python 3.13)` and `Pre-commit (Python 3.14)` to ruleset 14715370's `required_status_checks`;
- use a full-replacement PUT built from the ruleset's CURRENT JSON;
- **preserve every existing context's `integration_id`** (a hard-coded id once made five repos unmergeable: memory
  `project_branch_protection_headless_merge_2026-08-12.md`), and give the two new contexts GitHub Actions' id, read
  from an existing Actions context in the same ruleset;
- verify afterwards: the context count goes up by 2, and no surviving context's id drifted.

Adding them before the merge would block every open deploy PR, because none of those posts the new names. Ask the
owner before the ruleset PUT if in doubt, since it is a repo-settings change.

**Still unanswered:** whether deploy's `Unit Tests (Python 3.13)` / `(Python 3.14)` should also become required.
Today they block only through the Quality Gate. Do not change that unasked.

## Task 2: phase 2 -- work through the 3.15 problems (approved)

Phase 2 is the owner's "working through identified problems with the juniper code base on python3.15". The 3.15 legs
stay INFORMATIONAL (green, with a warning): do not make any 3.15 check required (phase 3), and do not move
`/usr/bin/python3` off 3.14 (phase 4). Each leg's warning annotation and job summary name the failing steps; the
local helper reproduces them on this host:

```bash
python3 util/python_version_check.py --repo <repo> --python 3.15     # juniper-ml; logs in tmp/python-version-checks/
```

Known problems, in priority order:
1. **h5py has no CPython 3.15 wheel**; the sdist needs libhdf5 headers. It stops the 3.15 leg at install in
   juniper-ml (`Regression Tests`), juniper-cascor (`unit-tests`) and juniper-canopy (`unit-tests`), and canopy then
   fails 5 tests on `No module named 'h5py'`.
   - First, re-probe PyPI for a release that ships cp315 wheels (canopy's run used h5py 3.16.0).
   - If none exists, install the headers on the 3.15 leg only (e.g. `sudo apt-get install -y libhdf5-dev pkg-config`
     in a step gated `if: matrix.experimental == true`) and let the sdist build.
   - Either way, re-run and read the next layer of failures.
2. **`dill` reads `code.co_lnotab`**, which Python 3.15 removed. It causes 2 of juniper-cascor-model's 3 failing
   tests on 3.15; the third is pre-existing `main` drift (below). Check dill's newest release for 3.15 support and
   raise the floor, or patch the call site. Inferred, not measured: cascor's `src/utils/utils.py` may hit the same
   once h5py installs.
3. Whatever the next layer shows. Expect more once install succeeds in ml, cascor and canopy.

**Pre-existing defects, NOT 3.15**, each worth its own PR:
- `scheduled-tests.yml`'s `-m "slow or integration"` errors with `Unknown marker(s) ... slow` in juniper-data-client,
  juniper-cascor-client and juniper-cascor-worker. It has been red on every leg since about 2026-10-28.
- `ci-cascor-model.yml` is red on cascor `main`: cascor#687's `_PROJECT_API_START_FRESH_REQUIRED_MARKER` never
  reached `juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`.

## Mechanics (unchanged; see the predecessor and `tmp/py315/ROLLOUT_BRIEF.md` in this worktree)

- Use signed API commits: `util/open_signed_pr.py` and `util/push_signed_commit.py`. Never `git commit`.
- Re-check that `main` has not moved immediately before every whole-file upload, and read back by git blob SHA.
- Merge with `util/safe_merge.py`. juniper-harcot is the exception: merge by hand with
  `gh pr merge --match-head-commit` after `wait_for_checks.py --anchor observed`.
- Before merging a CHANGELOG-touching PR, check for an open `release/*` PR, and let it land first. If it does, move
  the entry back with `util/ad-hoc/2026-11-15_py315_cascor_changelog_relocate.py`.
- The owner's PR sweeper arms auto-merge on open PRs, and re-armed one this session had disarmed. A PR you open may
  merge as soon as its required checks pass, so make it right before you open it.
- **Peer hold:** the Cursor flood-4 session asked other sessions not to merge juniper-ml PRs that touch `ci.yml`,
  `CHANGELOG.md`, `docs/REFERENCE.md`, `AGENTS.md` or `main-verify.yml` until it sends "flood-4 sitting done"
  (asked 04:12Z, for about 2-3 hours). PRs that only add files are fine. Check `ListAgents` and the inbox first.

## Cleanup still owed

Rollout worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`:
- `*python-3-15-informational*`: nine;
- `*python-3-15-green-legs*`: six;
- the helper agent's `juniper-ml/.claude/worktrees/agent-a071c56ac10b0da13`.

All their PRs are merged. Their `tmp/` dirs hold test venvs and logs: check each against the tmp retention rule
before `git worktree remove` (`notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`).

## Verification commands

```bash
/usr/bin/python3 --version                                    # 3.14.x
gh api repos/pcalnon/juniper-deploy/rules/branches/main --jq '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]|sort'
git -C /home/pcalnon/Development/python/Juniper/juniper-deploy show origin/main:.github/workflows/ci.yml | sed -n '/^  pre-commit:/,/^  [a-z]/p' | head -30
gh run list --repo pcalnon/juniper-ml --workflow ci.yml --branch main --limit 1 --json conclusion,headSha
```

**Expect:**
- Python 3.14.x;
- deploy's 12 required contexts, with `Pre-commit` among them and no `Pre-commit (Python 3.1x)` yet;
- a single-version `pre-commit` job;
- juniper-ml main `success`.

## Git status

The juniper-ml worktree `witty-giggling-twilight` is at `main` (`be092a2e` or later) and holds nothing uncommitted
that matters; scratch lives in its gitignored `tmp/py315/`. No branch of this arc is open in any repo.
