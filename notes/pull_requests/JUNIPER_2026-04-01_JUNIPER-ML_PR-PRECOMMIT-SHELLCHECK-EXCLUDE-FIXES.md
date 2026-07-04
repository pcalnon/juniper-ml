# Pull Request: Fix Pre-commit Failures — ShellCheck Warnings and Exclude Pattern

**Date:** 2026-04-01
**Version(s):** 0.2.0
**Author:** Paul Calnon
**Status:** READY_FOR_MERGE

---

## Summary

Fix all pre-commit hook failures across shell scripts and configuration. Resolves a broken directory exclude regex pattern in `.pre-commit-config.yaml` that failed to match files within excluded directories, and addresses all ShellCheck warnings in utility scripts.

---

## Context / Motivation

Running `pre-commit run --all-files` produced three categories of failures:

1. **end-of-file-fixer** — Two util scripts had extra trailing newlines
2. **trailing-whitespace** — Two files had trailing whitespace (one in `prompts/` which should have been excluded but wasn't due to the regex bug)
3. **shellcheck** — 11 warnings across three utility scripts (unguarded `cd`, non-constant `source`, unused variables, `exec` before shell function)

The root cause of the prompts file being checked was a bug in the global exclude pattern: bare directory entries like `prompts/` inside `^(...)$` regex anchors only match the literal string "prompts/", not files within the directory like "prompts/prompt056_2026-03-31.md".

---

## Changes

### Fixed

- Broken directory exclude regex in `.pre-commit-config.yaml` — appended `.*` to all directory-based patterns so they match files within those directories
- ShellCheck SC2164: added `|| exit` / `|| return` to all unguarded `cd` commands in `launch_full_monty.bash`, `worktree_activate.bash`, `worktree_new.bash`
- ShellCheck SC1090: added `# shellcheck source=/dev/null` directives for non-constant `source` commands in `launch_full_monty.bash`, `worktree_new.bash`
- ShellCheck SC2034: removed unused `TRUE` / `FALSE` variables in `worktree_new.bash`
- ShellCheck SC2093: removed invalid `exec` before `conda activate` shell function in `worktree_new.bash`
- Missing EOF newlines in `get_cascor_dkdk.bash`, `launch_full_monty.bash`
- Trailing whitespace in `prompt056_2026-03-31.md`, `worktree_new.bash`

---

## Impact & SemVer

- **SemVer impact:** PATCH
- **User-visible behavior change:** NO
- **Breaking changes:** NO
- **Performance impact:** NONE
- **Security/privacy impact:** NONE

---

## Testing & Results

### Test Summary

| Test Type   | Passed | Failed | Skipped | Notes                              |
| ----------- | ------ | ------ | ------- | ---------------------------------- |
| Unit        | 60     | 0      | 0       | test_wake_the_claude.py            |
| Regression  | 1      | 0      | N/A     | test_resume_file_safety.bash       |
| Pre-commit  | 17     | 0      | 0       | All hooks pass on --all-files      |

---

## Files Changed

- `.pre-commit-config.yaml` — Fixed directory exclude regex patterns
- `util/launch_full_monty.bash` — Added shellcheck directive, `|| exit` on `cd`, fixed EOF
- `util/worktree_activate.bash` — Quoted variable, added `|| return` on `cd`
- `util/worktree_new.bash` — Removed unused vars, added shellcheck directive, `|| exit` on `cd`, removed `exec` before `conda activate`, fixed trailing whitespace
- `util/get_cascor_dkdk.bash` — Fixed EOF newline
- `prompts/prompt056_2026-03-31.md` — Fixed trailing whitespace
