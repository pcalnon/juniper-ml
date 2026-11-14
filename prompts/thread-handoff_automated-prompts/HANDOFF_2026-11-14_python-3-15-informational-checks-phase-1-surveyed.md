# Handoff: Python 3.15 as an informational check, ecosystem-wide -- phase 1 surveyed, design to settle on a pilot PR

**Date**: 2026-11-14 (facts read between 22:20Z and 22:50Z)
**Session**: host yamaguchi, worktree `juniper-ml/.claude/worktrees/humble-dreaming-quail` (the same session also landed
juniper-ml#2548 for the backup arc; that arc has its own handoff,
`HANDOFF_2026-11-14_backup-phase-d-tools-merged-sitting-resumes-at-c1.md`). **No repository has been changed for this arc.**

## The owner's request (2026-11-14, verbatim)

> default python upgrade has been deferred for now due to the issues that occurred.
> as a first step towards the python 3.15 migration, let's add python3.15 to the list of tested python versions in local
> test infrastructure and in CI settings.
> at this stage, the python3.15 checks should report results but not block commits, merges, or deployments.
> next steps will include working through identified problems with the juniper code base on python3.15.
> when we're comfortable that the code base works as expected with python3.15, we can begin making the new python3.15 checks
> required.
> then, when we've established that python3.15 local and CI checks are passing normally, we can migrate the local python
> default version from 3.14 to 3.15.

## Goal statement

Phase 1 of 4: Python 3.15 runs in every repo's CI test matrix and in local test infrastructure, and its results are
visible but block nothing: no commit (never in pre-commit hooks), no merge (no gate `needs:` it, no ruleset requires it),
no deployment (no publish or release path waits on it). Phases 2-4 are the owner's sequence above; do not start them.

### Completed so far

- **Two read-only surveys** of the 10 repos (juniper-cascor, -data, -data-client, -cascor-client, -cascor-worker, -ml with its
  six sub-packages, -canopy, -deploy, -recurrence, -harcot) at `origin/main`, saved verbatim. **Read both before editing:**
  `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md` and
  `…/survey-local-2026-11-14.md` (copies in `humble-dreaming-quail`'s `tmp/py315-informational-2026-11-14/`).
- **3.15 on runners: available.** `actions/setup-python` is SHA-pinned to v7.1.0 in all 194 uses; the manifest marks
  3.15.0-3.15.2 `stable`, with linux x64 builds for 22.04, 24.04 and 26.04 (`ubuntu-latest` is 26.04). No `allow-prereleases`.
- **3.15 on this host:** `/usr/bin/python3.15` 3.15.2 with `venv`/`ensurepip`. `/usr/bin/python3` must stay 3.14: the
  owner's deferral followed the 2026-11-14 switch that broke the backup drills and `JuniperCascor1` (memory note
  `project_host_python3_switched_to_315_2026-11-14.md`). No conda env has 3.15.

### Key findings (details and file:line in the surveys)

1. **Adding "3.15" to an existing PR matrix blocks merges in 7 repos** (ml, cascor, data, data-client, cascor-client,
   cascor-worker, canopy; recurrence too, through its per-package `… required checks`). Not through the new leg's own check
   (no ruleset requires one), but through the required aggregate gate: `if [[ "${{ needs.<job>.result }}" != "success" ]]`,
   and a matrix job's result is `failure` when any leg fails.
2. **A failed pre-commit leg also skips every job that `needs: pre-commit`** (tests, build, audits). Treat pre-commit
   separately from the test matrices.
3. **Deployments**: no `publish*.yml` / `publish-image.yml` needs a test job. Indirect paths: release-train's archive-PR
   auto-merge waits for the required checks; data-client, cascor-client and cascor-worker skip `notify-downstream` when the
   gate fails on `main`.
4. **Repo specifics.** cascor, data, cascor-worker and canopy `unit-tests` already carry
   `continue-on-error: ${{ matrix.experimental == true }}` (macOS include `experimental: false`). data-client and cascor-client
   do not; their `integration-tests` matrices are soft in the gate (warning only). juniper-ml: `ci.yml` pre-commit and tests
   (hard), six path-filtered `ci-<pkg>.yml` with no gate (safe). **juniper-deploy has no matrix and its required contexts
   (`Unit Tests`, `Pre-commit`) carry no version: never turn them into a matrix** (the required names would stop posting).
   juniper-recurrence: four package matrices, gates accept `success` or `skipped`. juniper-harcot: private, no enforceable
   ruleset (403), gate fails on any non-success. cascor's `ci-cascor-model.yml` / `ci-protocol.yml`: no gate.
5. **Pinning tests**: juniper-ml `tests/test_ci_quality_gate.py:132-140` and juniper-data
   `juniper_data/tests/unit/test_quality_gate_results.py:97-103` pin the gates' exact `needs:` lists (keep new jobs out of
   them); juniper-ml `tests/test_subpackage_ci_workflows.py:132-140` forbids a new file named `ci-*.yml`; ml
   `tests/test_host_state_check.py:933-940` ties `conf/hosts/turing/conda-envs/*.yml` to `expected.yaml`.
6. **Local**: no tox, nox or version list anywhere; every local runner uses the active `python`. Wrappers that accept another
   interpreter: each repo's `util/run_coverage.bash` / `make coverage`, cascor `src/tests/scripts/run_tests.bash`, canopy
   `PYTEST=`, harcot `PYTHON=`.
7. **Phase 1 leaves alone**: the `3.15` classifier (it claims support), `requires-python`, mypy `python_version`, black and ruff
   targets (the cached black hooks accept py314 at most), Dockerfile bases, conda env specs.

### The design question, and how to settle it

- **A. Matrix leg**: `include: {python-version: "3.15", experimental: true}` plus job-level
  `continue-on-error: ${{ matrix.experimental == true }}` (GitHub's documented experimental pattern; the alls-green action
  builds on it). Same steps as the blocking legs, so no drift. **Unverified**: whether a gate's `needs.<job>.result` reads
  `success` when only the `continue-on-error` leg failed. History did not settle it: juniper-data 2026-02-01 to 05-02, 315
  runs, one failed experimental macOS leg, and the other legs failed in that run too. Scans of cascor-worker, canopy and
  cascor were still running at handoff:
  `humble-dreaming-quail/tmp/py315-informational-2026-11-14/coe-evidence-{cascor-worker,canopy,cascor}.txt`.
- **B. Separate job** (`… (Python 3.15, informational)`), `continue-on-error: true`, outside every gate's `needs:` and every
  ruleset: the precedent is juniper-ml's `markdown-structure-advisory` (`ci.yml:2150`). Non-blocking by construction; the
  steps are duplicated, so a test should pin them to the blocking job's.
- **Recommendation**: pilot A on juniper-data, which is likely to fail somewhere on 3.15 and so shows what the gate reads.
  Gate green with the 3.15 leg red: roll A out. Gate red: use B everywhere. Pre-commit on 3.15, if wanted at all: B only.

### Remaining work (phase 1)

1. **Ask the owner first** (one batch): (a) local infrastructure: recommended, a juniper-ml helper plus a
   `conf/python_versions.yaml` (blocking 3.12-3.14, informational 3.15) that builds one venv per repo from
   `/usr/bin/python3.15` at a fixed path in that repo's primary `tmp/`, runs the repo's existing wrapper, exits 0 unless
   `--strict`, and is never wired into pre-commit; (b) pre-commit on 3.15 now or later; (c) juniper-deploy and juniper-harcot
   in scope.
2. **Pilot**: juniper-data, one PR: the leg (design A), the docs lines the local survey lists. Read the run: the 3.15 leg's
   conclusion, the Quality Gate's, and its log line for `needs.unit-tests.result`. Record the evidence in the PR body.
3. **Roll out** one PR per repo: a worktree under `Juniper/worktrees/` per the naming convention, branch
   `ci/python-3-15-informational`, signed commits (`util/open_signed_pr.py` / `util/push_signed_commit.py`). For juniper-ml,
   wire any new test into `ci.yml` and `docs/REFERENCE.md` and bump `AGENTS.md`'s count and Last Updated date.
4. **Local helper** in juniper-ml, if the owner approves, with its own tests.
5. **Merges**: only with the owner's approval given in that session, `util/safe_merge.py` per PR. Note: its local merge
   drops a curated squash body (memory note `reference_squash_body_excludes_merge_commits.md`).

## Verification commands (start of the next thread)

```bash
head -n 20 /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/py315-informational-2026-11-14/survey-ci-2026-11-14.md
tail -n 3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humble-dreaming-quail/tmp/py315-informational-2026-11-14/coe-evidence-canopy.txt
/usr/bin/python3 --version
/usr/bin/python3.15 --version
gh api repos/pcalnon/juniper-data/rules/branches/main --jq '[.[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context] | length'
```

**Expect:** the survey's title line; each evidence file ending with a count of runs with a failed macOS job; Python 3.14.x
and 3.15.2; 22 required contexts for juniper-data.

## Git status at handoff

No branch, worktree or file exists for this arc in any repository. This file and the backup arc's 2026-11-14 handoff travel
in one juniper-ml PR.
