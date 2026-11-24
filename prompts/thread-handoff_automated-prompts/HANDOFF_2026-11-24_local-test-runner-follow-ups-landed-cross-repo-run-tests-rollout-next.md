# Handoff: local test runner -- follow-ups landed (ml#2640, ml#2641); repo-specific `run_tests` scripts for the nine other repos next

**Date**: 2026-11-24 (written about 21:45Z)
**From**: session cf7e3bfa, in worktree `juniper-ml/.claude/worktrees/delegated-questing-bentley` (removed after ml#2641 merged)
**Predecessor**: none. The arc began with the Overtoad's request "the juniper-ml repo appears to lack any convenience script(s) for running testing locally"
**Memory**: `reference_ci_merge_mechanics_hub.md` (the runner's pointer; the same-day `Verify AGENTS.md Last Updated` limit; the DIRTY re-land recipe)

---

## Goal

Give each of the other nine active Juniper repos its own local test runner, modelled on juniper-ml's `util/run_tests.py`: one command
that runs any subset of that repo's tests locally with the commands its CI runs, read from its workflows on every run. The nine are
juniper-recurrence, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-harcot (private),
juniper-cascor, juniper-canopy and juniper-deploy. One signed PR per repo. Merge none without the Overtoad's explicit approval in
the new session: a handoff cannot carry one (memory `feedback_headless_merge_approval_policy.md`).

## Completed (this arc)

- **ml#2629 MERGED** 2026-11-24 12:10Z as `d7709ef7`, re-landing ml#2615 and ml#2621, which each went DIRTY and were closed.
  - `util/run_tests.py` and `tests/test_run_tests.py` (suite 263).
  - The operator documentation: `docs/REFERENCE.md` § Test Suite Reference, "Running tests locally".
- **ml#2640 MERGED** 2026-11-24 21:41Z as `42f56b45` (all 17 required contexts green; every file on main equals the one tested):
  - `tests/test_a0_restore_scripts.py` passes where `TMPDIR` is under `/home` (21 tests).
    - Its `install` stub refuses a path that resolves under `/home` or the real home unless it is inside the test's scratch
      directory.
    - `InstallStubSafetyNet` pins the net itself.
    - `util/ad-hoc/2026-11-24_a0_install_stub_mutation_check.py` kills six mutants.
  - `conf/python_versions.yaml`'s juniper-ml recipe is `python util/run_tests.py regression --python "$VIRTUAL_ENV/bin/python"`.
    Measured under a fresh 3.14 venv: 265 jobs in 4m57s, 262 passed, and the 3 failures are the known ones (item 2).
  - In `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`, section 11's registry-walk row reads
    **Done** and section 4.8 says so.
  - `docs/REFERENCE.md` 0.6.83 and `CHANGELOG.md` follow.
- **ml#2641, this file's PR**:
  - the arc's 20 scratch scripts archived from the worktree's `tmp/` to `util/ad-hoc/<date>_run_tests_*.py`;
  - the archiver, `util/ad-hoc/2026-11-24_run_tests_archive_scratch.py` (`--verify`: code identical, original docstrings kept);
  - `util/ad-hoc/2026-11-24_worktree_matches_commit.py`;
  - `util/ad-hoc/2026-11-24_run_tests_rollout_survey.py`.
- **Cleanup.**
  - Remote branches `feat/local-test-runner` and `feat/local-test-runner-2` are deleted. Their commits survive as
    `refs/pull/2615/head` and `refs/pull/2621/head`. `feat/local-test-runner-3` was deleted when its PR merged.
  - The arc's scratch data moved to the primary's `tmp/run-tests-design--delegated-questing-bentley/`: run logs,
    gate outputs, PR bodies, the upload snapshot, merge inputs and file copies. It is kept under the retention rule, section 6 of
    `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`.
  - The worktree is removed.

## Remaining work

### 1. The rollout (the goal)

For each repo, in its own worktree under `Juniper/worktrees/`, and after reading that repo's `AGENTS.md`:

1. **Survey** its CI test jobs from the repo's own `origin/main`. `python3 util/ad-hoc/2026-11-24_run_tests_rollout_survey.py`
   (juniper-ml) reads the sibling primaries, which can lag.
2. **Write `util/run_tests.py`** for that repo, starting from juniper-ml's. Its lanes are the repo's CI test jobs.
3. **A hermetic test suite** in the repo's own test layout, using a fake checkout under the repo's `tmp/`, wired into its CI.
   Include a check that every `--help` option is documented.
4. **Documentation:** its `AGENTS.md` testing section, its reference documentation if it has any, and `CHANGELOG.md`.
5. **Optionally**, switch its recipe in juniper-ml's `conf/python_versions.yaml` to the new runner.
6. **Land it:** a signed PR (juniper-ml's `util/open_signed_pr.py --repo <name>`), the Overtoad's approval, then
   `util/safe_merge.py`.

This table comes from the survey of 2026-11-24, read from the primaries:

| # | Repo | CI test surface | Local wrapper today | Port notes |
|---|------|-----------------|---------------------|------------|
| 1 | juniper-recurrence | one workflow per package, `ci-recurrence-{model,client,app,bench}.yml` (cov 90 + gap map; model's `test-torch` lane); unittest lanes in `memory-budget.yml` and `sequence-safety.yml` | none | closest to juniper-ml's package lanes; no conda env |
| 2 | juniper-data-client, juniper-cascor-client, juniper-cascor-worker | `ci.yml` unit-tests (3.12-3.14, `coverage report --fail-under=${COVERAGE_FAIL_UNDER}`, gap map), integration, security (gitleaks), `scheduled-tests.yml`; data-client's generator-parity needs a live registry | `util/run_coverage.bash` | one shape: build once, copy twice; the worker pulls torch |
| 3 | juniper-data | the same shape; `-m slow` treats exit 5 as failure | `util/run_coverage.bash` | ruff, not black; env `JuniperData` |
| 4 | juniper-harcot | unit-tests (fail-under), contract-tests (drives juniper-ml's experiment runner) | `util/run_coverage.bash` | private; env `JuniperHarcot` |
| 5 | juniper-cascor | `ci.yml` unit, quick-integration, integration, security; `conformance.yml`, `golden-regression.yml`, `scheduled-tests.yml`; package lanes `ci-cascor-model.yml` (gap map) and `ci-protocol.yml` (cov 95 + gap map) | `util/run_coverage.bash`, `src/tests/scripts/run_tests.bash` | env `JuniperCascor1`; 6 tests fail if `JUNIPER_CASCOR_LOG_DIR` is set; never edit the primary while a stack imports it |
| 6 | juniper-canopy | unit (CI tolerates SIGABRT 134 when JUnit shows 0 failures), integration, ui-tests (Playwright), security, scheduled | `util/run_coverage.bash`, `util/run_tests.bash`, Makefile `test`/`test-all`/`test-ui` | reconcile with its `util/run_tests.bash`; env `JuniperCanopy1` |
| 7 | juniper-deploy | `ci.yml` tests: `pytest tests/` and `python3 -m unittest -v util/test_workflow_script_paths.py`; gitleaks tests; `publish-image.yml`'s live modules | Makefile `test` (Docker), `scripts/test_*.sh` | **hazard**: its pytest drives live local services (POSTs to canopy on :8050), so make live modules opt-in and check `ss` first |

**Keep from juniper-ml's runner:**

- Lanes are read from the workflows on every run, never from a hand-kept list. Logical lines are joined across `\`, and shlex
  splits with `punctuation_chars`.
- Each step runs in its own process group, killed on a timeout (900 s), on Ctrl-C or SIGTERM, and when it leaves processes
  behind.
- Each child gets the D-Bus guard (the ml#2559 class), no `DISPLAY` or `PYTHONPATH`, and a `TMPDIR` that is never the system
  temp directory.
- The preflight installs nothing. It prints the `pip install` command for whatever is missing, and refuses a lane that would
  import from outside the checkout.
- Records go under the PRIMARY's `tmp/run-tests/<checkout>/<UTC stamp>/` (`summary.json` schema 1). Exit codes are 0/1/2/3/5/130.
- `-j auto` re-runs a failed job alone; `--changed`, `--failed`, `-k`, `-x`, `--list` and `--dry-run` carry over.

**New in the other repos**, which juniper-ml's runner never needed:

- Workflow `env:` and matrix indirection inside commands, such as `${COVERAGE_FAIL_UNDER}` and `${{ env.COVERAGE_FAIL_UNDER }}`.
- Pipelines and exit rules written into steps: `| tee`, `|| rc=$?`, data's exit-5 rule and canopy's 134 rule. Reproduce
  each rule, or run the bare pytest and apply it in the runner.
- Prep steps (`mkdir -p reports/...`) and coverage written under `reports/`. Route coverage to the run directory.
- Lanes that need services or the network (integration, generator-parity, Playwright, deploy's live modules, cascor's
  long-running and performance lanes). Make them opt-in by name, outside the default `all`.
- A separate conda env per repo, which `--python` must name.

**A decision for the Overtoad before the second port.** One option is a copy per repo, which is what was asked for:
"repo-specific run_tests scripts". The other moves the engine into juniper-ci-tools, which is canonical in juniper-ml, with a
thin per-repo `util/run_tests.py`. A ci-tools release is a deploy that the Overtoad approves. **Recommendation:** port
juniper-recurrence and one single-package repo as copies, then extract the shared engine once two real variants show it,
before the other six. Ask with AskUserQuestion. A dialog blocks the session, so finish time-critical steps first.

### 2. juniper-ml: the four remaining local-only failures

`docs/REFERENCE.md` § Test Suite Reference, "Known local-only failures", lists four:

- `tests/test_workflow_script_paths.py`, 1 of 13;
- `tests/test_e2e_f037_render_census.py`, 1 of 13;
- `tests/test_replay_redrive_stack_refusal.py`, 13 of 17;
- ci-tools, 9 of 309.

Each walks up from a temp directory and finds the enclosing checkout, because `TMPDIR`, the primary's `tmp/`, sits inside one.
Bound each walk the way ml#2640 made the a0 suite hermetic, so that `python3 util/run_tests.py` is green locally. Until then the
measured remedy is `--tmpdir` outside every checkout, as a per-run choice and never a default: section 4.2 of
`notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md` puts `TMPDIR` in the repo's `tmp/`.

## Key context and traps

- **The worktree guard** refuses a Bash line that names `.github`, a heredoc holding a `for` loop, `git -C <other repo>` or a
  compound git line. Put such logic in a script under `util/ad-hoc/`, never under `tmp/` (AGENTS.md § Script placement).
- **Gates on `util/` Python**:
  - check-ast, gitleaks and CodeQL apply (`util/ad-hoc/2026-10-05_codeql_python_prescreen.py` predicts CodeQL alerts).
  - G-TMP applies, and misreads `<x>/tmp/` in prose as a system temp path.
  - G-PATH applies: `/home/pcalnon` is refused, so derive paths from `git rev-parse --git-common-dir`.
  - black, flake8, mypy and bandit cover only `scripts/` and `tests/`.
- **Signed commits only.**
  - Put a large file (`docs/REFERENCE.md`, about 1.4 MB) in its own commit.
  - Upload a whole file only onto a base that has not changed it: re-fetch and diff the file list first.
- **`Verify AGENTS.md Last Updated`** is not required. It fails a second PR that edits `AGENTS.md` on the same UTC day.
- **A DIRTY PR** is re-landed from main by a three-way merge, and the old PR is closed with a pointer to the new one.
- **`util/safe_merge.py`**: read its `MERGED` line; exit 0 alone does not mean merged.
- **`--failed` keys records by checkout name only**, so after a `util/python_version_check.py` run it picks up that run
  whatever its Python version.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log --oneline -3 origin/main   # ml#2641 and ml#2640
python3 util/run_tests.py a0_restore_scripts                         # 21 tests pass with TMPDIR under /home
python3 util/run_tests.py --list | head -5                           # lanes read from the workflows
python3 util/python_version_check.py --list | grep -A5 '^juniper-ml'  # test: util/run_tests.py regression
git worktree list | grep -c delegated-questing-bentley               # 0
ls tmp/run-tests-design--delegated-questing-bentley | wc -l          # the arc's data, kept
python3 util/ad-hoc/2026-11-24_run_tests_rollout_survey.py           # the rollout input
```

## Git state

- juniper-ml `main` is at ml#2641's squash or later.
- This arc leaves no open branch, PR or uncommitted work.
- The nine target repos are untouched.
