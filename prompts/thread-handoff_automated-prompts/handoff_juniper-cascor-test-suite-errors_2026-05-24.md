# Juniper Canopy Tests

Investigate juniper-cascor test failures, identify root causes, and develop & implement fixes.

## Constraints (must follow)

- Do NOT disable, comment out, delete, remove, gate away, or remove checks from any existing test.
- Add regression tests for every fix so the bug can't silently regress.
- Add tests as necessary to ensure no other regressions are introduced.

## Working environment

- Repo: /home/pcalnon/Development/python/Juniper/juniper-cascor (parent CLAUDE.md at /home/pcalnon/Development/python/Juniper/CLAUDE.md; per-repo agent file at juniper-cascor/AGENTS.md — read both before starting).
- Conda env: JuniperCascor1 (Python 3.13 + torch 2.11.0; the unified server+worker env).
  - The legacy `JuniperCascor` env has a broken torch install — do NOT use it.
  - See memory `project_juniper_cascor_torch_env_broken`.
- Use a worktree per the parent CLAUDE.md "Worktree Procedures" section.
  - All worktrees go in /home/pcalnon/Development/python/Juniper/worktrees/ with the naming convention `<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`.
- Start a NEW worktree for this task; do not reuse an old one.

## Context

### Relevant context from memory

read these first — do not paraphrase, read the actual entries under ~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/

- project_juniper_cascor_torch_env_broken — use JuniperCascor1, not the legacy env
- project_pytest_autoload_segfault_fix_2026-05-01 — autoload SIGSEGV defense
- project_cascor_pytest_ini_drift_2026-05-03 — RESOLVED, may recur
- project_cascor_pytest_summary_truncation_2026-05-03 — root cause was os._exit skipping stdout flush; RESOLVED via cascor PR #205, may recur
- project_cascor_orphan_forkserver_workers_2026-05-03 — RESOLVED via PR #205 + juniper-ml#196 (util/reap_pytest_orphans.bash for pre-existing orphans)
- project_lockfile_refresh_after_pyproject_min_bump — 3rd distinct cascor lockfile footgun history
- feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15 — TWO gates before any worktree cleanup

### Methodology

Methodology that worked on the recent juniper-canopy investigation (juniper-canopy PR #317, merged 2026-05-23):

1. First categorize the test surface (`pytest --collect-only`, count by marker, identify opt-in markers like `slow`, `requires_server`, `requires_cascor`).
    - Don't try to run "the whole suite" blindly — find the marker groups CI actually runs, and the groups CI skips.
2. Run CI-equivalent invocations FIRST (mirror what the CI workflow does) to confirm what CI sees passes.
    - Then expand to opt-in markers to find what's masked.
3. Distinguish ERRORs (test setup failures — often fixture/plugin collisions or import errors) from FAILUREs (actual assertion failures).
    - They almost always have different root causes.
4. When a fix unmasks a downstream failure, fix that too — don't leave the test in a different broken state.
5. For test infrastructure bugs (fixture collisions, env leakage into in-process apps), add lint-style regression tests that scan the source to prevent re-introduction, plus a behavioral regression test that exercises the exact failure mode.

### Tasks

First steps for the new thread:

1. `cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git status` then `git pull origin main` to start from a clean main.
2. Read juniper-cascor/AGENTS.md to learn the project-specific test commands (the run-tests script lives at `src/tests/scripts/run_tests.bash` per the parent CLAUDE.md).
    - Read `.github/workflows/ci.yml` to see what CI actually runs.
3. Create a worktree per the procedure in `juniper-cascor/notes/WORKTREE_SETUP_PROCEDURE.md`.
4. Activate `JuniperCascor1` and run a `pytest --collect-only` to inventory the test surface.
    - Look for both passing- and erroring-collection.
5. Run the CI-equivalent invocation, then opt-in markers, and report the failure catalog before proposing fixes.
    - Don't fix until the user approves the direction (the canopy run had a design judgment call on the auth-401 case that needed an AskUserQuestion).

## Verification

Verification commands the new thread should run after any fix:

- The CI-equivalent test invocations from `.github/workflows/ci.yml`
- `pre-commit run --files <changed files>` (matches the canopy pattern)
- Any new regression tests both with and without the env vars they guard

## Commits and Cleanup

When the work is ready: commit (HEREDOC message, Co-Authored-By Claude), push with `-u origin <branch>`, and open a PR against main.
Do NOT clean up the worktree until the user explicitly confirms the PR is merged AND `gh pr view <N>` confirms `state=MERGED` with non-null `mergedAt`.

---
