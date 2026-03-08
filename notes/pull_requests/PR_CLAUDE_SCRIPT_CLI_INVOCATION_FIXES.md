# Pull Request: Claude Code Launcher Script — CLI Invocation Fixes and Interactive Mode

**Date:** 2026-03-08
**Version(s):** N/A (tooling script, no package version)
**Author:** Paul Calnon
**Status:** DRAFT

---

## Summary

Fixes bash argument-passing issues in `wake_the_claude.bash` that caused Claude Code CLI flags and values to be split into separate array elements (breaking invocation), adds support for interactive (non-headless) launch mode, and introduces a convenience wrapper script for default interactive sessions.

---

## Context / Motivation

When `wake_the_claude.bash` built the `CLAUDE_CODE_PARAMS` array, it added CLI flags and their values as separate array elements (e.g., `+=("--resume" "<uuid>")`). When the array was expanded with `"${CLAUDE_CODE_PARAMS[@]}"`, this produced correct quoting — but the script's invocation logic and the way `nohup` handled the expansion caused arguments to be misinterpreted by the Claude Code CLI.

Additionally, the script always launched Claude via `nohup ... &` (headless mode), with no path for interactive (foreground) sessions. Users wanting a quick interactive session had to manually construct the full `claude` command with all flags.

---

## Priority & Work Status

| Priority | Work Item | Owner | Status |
| -------- | --------- | ----- | ------ |
| P1 | Fix CLI argument passing for flag+value pairs | Paul Calnon | Complete |
| P1 | Fix prompt string character escaping | Paul Calnon | Complete |
| P2 | Add interactive (foreground) launch mode | Paul Calnon | Complete |
| P2 | Add convenience wrapper for default interactive sessions | Paul Calnon | Complete |
| P3 | Update .gitignore for nohup and worktree artifacts | Paul Calnon | Complete |

---

## Changes

### Added

- `scripts/default_interactive_session_claude_code.bash` — Convenience wrapper that launches `wake_the_claude.bash` with sensible defaults for an interactive session (`--id --worktree --dangerously-skip-permissions --effort high`)
- `cly` — Symlink to `default_interactive_session_claude_code.bash` for quick invocation from the repo root
- `scripts/test.bash` — Manual end-to-end test harness that exercises session creation, session ID file persistence, and session resume
- `scripts/test_prompt-000.md`, `scripts/test_prompt-001.md`, `scripts/test_prompt-002.md` — Test prompt files used by `test.bash` and for troubleshooting script issues

### Changed

- `scripts/wake_the_claude.bash` — Multiple argument-passing and invocation changes:
  - **Flag+value concatenation**: Resume, session-id, effort, and model flags are now added to `CLAUDE_CODE_PARAMS` as a single concatenated string (`"${FLAG} ${VALUE}"`) instead of two separate array elements, fixing CLI argument splitting
  - **Prompt quoting**: Prompt string is now wrapped in escaped double quotes when added to the params array, preventing word splitting
  - **Interactive vs. headless launch**: Invocation block now branches on `HEADLESS_VALUE` — headless sessions use `nohup ... &`, interactive sessions run `claude` in the foreground
  - **Unquoted array expansion**: `${CLAUDE_CODE_PARAMS[@]}` (without quotes) is used at invocation to allow the concatenated flag+value strings to be split by the shell, matching the intended CLI argument structure
  - **File path validation**: Commented out an early `if -f` check on the raw path that short-circuited directory-based file resolution
- `.gitignore` — Added patterns for `nohup.out` files and `.claude/worktrees/` directories

### Removed

- Unconditional `nohup` launch — replaced with conditional headless/interactive branching

---

## Impact & SemVer

- **SemVer impact:** N/A (tooling script, not a published package)
- **User-visible behavior change:** YES — Interactive sessions now launch in the foreground; flag+value arguments are passed correctly to the Claude CLI
- **Breaking changes:** NO
- **Performance impact:** NONE
- **Security/privacy impact:** NONE
- **Guarded by feature flag:** NO

---

## Testing & Results

### Test Summary

| Test Type | Passed | Failed | Skipped | Notes |
| --------- | ------ | ------ | ------- | ----- |
| Manual | 2 | 0 | 0 | Interactive launch and headless launch verified |
| E2E | N/A | N/A | 3 | `test.bash` requires active `claude` CLI; test prompts included for manual runs |

### Environments Tested

- Local (bash, Ubuntu, Linux 6.17.0): Interactive and headless invocation verified

---

## Verification Checklist

- [ ] Interactive launch works via `./cly` convenience symlink
- [ ] Headless launch works with `--headless`/`--print` flag
- [ ] `--resume <uuid>` passes session ID correctly to `claude`
- [ ] `--session-id` generates and passes UUID correctly
- [ ] `--effort` and `--model` flags are received correctly by `claude`
- [ ] Prompt strings with spaces and special characters are preserved
- [ ] No regression in `--usage`, `--help` flag parsing
- [ ] `.gitignore` excludes nohup and worktree artifacts

---

## Files Changed

### New Components

- `scripts/default_interactive_session_claude_code.bash` — Default interactive session launcher
- `cly` — Symlink to the above for repo-root convenience
- `scripts/test.bash` — E2E test harness for session create/resume flow
- `scripts/test_prompt-000.md` — Simple test prompt
- `scripts/test_prompt-001.md` — Resume test prompt
- `scripts/test_prompt-002.md` — Detailed troubleshooting prompt (used for debugging the session validation bugs)

### Modified Components

**Scripts:**

- `scripts/wake_the_claude.bash` — Argument passing, prompt quoting, and invocation mode fixes

**Configuration:**

- `.gitignore` — Nohup output and worktree directory exclusions

---

## Risks & Rollback Plan

- **Key risks:** Unquoted array expansion (`${CLAUDE_CODE_PARAMS[@]}`) relies on flag+value strings being simple (no embedded special characters beyond spaces). Prompt strings with unusual quoting may require further escaping adjustments.
- **Rollback plan:** Revert to `main` branch; the previous `nohup`-only invocation path still functions for headless use.

---

## Related Issues / Tickets

- Related PRs: `PR_SESSION_ID_VALIDATION_BUGFIX.md`, `PR_PREVENT_RESUME_ARBITRARY_FILE_DELETION.md` (follow-up fixes merged to `main` that address session validation bugs discovered during this branch's development)

---

## What's Next

### Remaining Items

| Feature | Status | Priority |
| ------- | ------ | -------- |
| Clean up committed session ID `.txt` files (3 files in `scripts/`) | Not Started | P1 |
| Remove commented-out code blocks in `wake_the_claude.bash` | Not Started | P2 |
| Add `.txt` session files to `.gitignore` | Not Started | P2 |
| Formalize interactive vs. headless mode documentation | Not Started | P3 |

---

## Review Notes

1. Three session ID `.txt` files (`scripts/21c5f66d-*.txt`, `scripts/38c3bb49-*.txt`, `scripts/9196be9d-*.txt`) are committed — these are test artifacts that should be removed before merge.
2. Several blocks of commented-out code remain in `wake_the_claude.bash` and `default_interactive_session_claude_code.bash` from the debugging process. Consider cleaning these up.
3. The shift from quoted `"${CLAUDE_CODE_PARAMS[@]}"` to unquoted `${CLAUDE_CODE_PARAMS[@]}` is intentional — flag+value pairs are stored as single strings like `"--resume <uuid>"` and need shell word-splitting at invocation time. This is a pragmatic workaround but diverges from bash best practices for array expansion.
