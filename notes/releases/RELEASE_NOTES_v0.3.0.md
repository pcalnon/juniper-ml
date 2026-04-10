# Juniper ML v0.3.0 Release Notes

**Release Date:** 2026-03-12
**Version:** 0.3.0
**Codename:** Claude Tooling Suite
**Release Type:** MINOR

---

## Overview

This release expands the developer-tooling surface around Claude Code workflows: conda environment helpers, git worktree management, branch hygiene, and a focused regression test for `--resume` file safety. It also continues hardening `wake_the_claude.bash` (removing an `eval`-based command-injection vector) and standardizes documentation formatting across the `notes/` directory.

> **Status:** STABLE — Tooling-only release; no runtime dependency changes to the meta-package.

---

## Release Summary

- **Release type:** MINOR
- **Primary focus:** Claude Code tooling, worktree/branch management, documentation standardization
- **Breaking changes:** No
- **Priority summary:** Adds 5 new utility scripts, removes one `eval`-based command-injection vector, broadens `wake_the_claude.bash` test coverage

---

## What's New

### Conda & Workflow Helpers

- `scripts/activate_conda_env.bash` — Bash helper for conda environment activation/deactivation with structured sections for compilation workflows

### Git Worktree & Branch Management

- `scripts/cleanup_open_worktrees.bash` — Iterates through open git worktrees and performs status / add / pull / push operations
- `scripts/remove_stale_worktrees.bash` — Iterates through and removes stale git worktrees
- `scripts/prune_git_branches_without_working_dirs.bash` — Prunes local git branches that lack corresponding working directories; supports standard and forced deletion modes

### Regression Testing

- `scripts/test_resume_file_safety.bash` — Focused regression script that verifies invalid `--resume <file.txt>` input returns non-zero **and** preserves the source file (no destructive `rm`)
- New test coverage in `tests/test_wake_the_claude.py` for default launcher argument forwarding, permissions handling, and prompt token validation

### Documentation

- `notes/DEVELOPER_CHEATSHEET.md` — Added session ID workflow documentation, `wake_the_claude.bash` quick runbook, regression-test commands, `--resume` alias handling, interactive-vs-headless launch behavior, and troubleshooting sections
- `docs/DOCUMENTATION_OVERVIEW.md` — Added navigation links for Claude session tooling runbooks
- `notes/stack_overflow_answer.txt` — Reference material on managing conda environments programmatically in bash scripts
- `notes/pull_requests/PR_TOOLING_MORE_CLAUDE_UTILS.md` — PR description archive

---

## Bug Fixes

### `wake_the_claude.bash` Pattern Matching

**Problem:** `matches_pattern()` used `eval` for flag-pattern matching, which both presented a latent command-injection risk and produced subtle quoting bugs around tokens with metacharacters.

**Solution:** Replaced `eval`-based flag matching with a split-and-compare implementation that walks the pattern array directly.

### Function Definition Order

**Problem:** Top-level calls referenced `debug_log` and `redact_uuid` before they were defined, producing `command not found` stderr noise during launcher startup.

**Solution:** Moved `debug_log` and `redact_uuid` definitions before the top-level calls.

### `--id` UUID Validation Hardening

**Problem:** When `--id` was supplied without a value, the launcher attempted to generate a UUID via `uuidgen`. On hosts where `uuidgen` was unavailable, the code path produced an invalid session identifier.

**Solution:** Hardened `--id` (without value) generation to validate UUIDs across multiple fallback sources (`/proc/sys/kernel/random/uuid`, Python `uuid` module, etc.) when `uuidgen` is unavailable.

---

## Security

### Eliminated `eval` in Pattern Matching

**Risk (latent):** The previous `matches_pattern()` implementation invoked `eval` on user-supplied flag-pattern arguments. While not directly exploitable in the launcher's documented usage, the vector existed and could become exploitable through future refactoring or a misconfigured caller.

**Fix:** Removed `eval` entirely from `matches_pattern()`. Pattern matching now uses split-and-compare logic over arrays.

**Files:** `scripts/wake_the_claude.bash`

---

## Changes

- `scripts/wake_the_claude.bash` — Uncommented `EFFORT_VALUE` and `MODEL_VALUE` assignments; refactored nohup logging to handle missing log files; changed debug output to standard echo; consolidated exit status checks
- `.github/workflows/ci.yml` — Standardized comment spacing for action version tags (Dependabot version bumps)
- `notes/CONDA_DEPENDENCY_FILE_HEADER.md` — Renamed back from `.yaml` to `.md` (matching all other repos' naming convention)
- `CHANGELOG.md` — Added version identifiers to section headers for released versions
- Documentation formatting pass across `notes/` planning documents — standardized Markdown table alignment, added `bash` language tags to code blocks, converted URLs to Markdown link syntax

---

## Upgrade Notes

This is a backward-compatible release. No migration steps required. The published meta-package's runtime dependencies are unchanged.

```bash
# Update via pip (meta-package install path)
pip install --upgrade juniper-ml==0.3.0

# Or for tooling, pull from git
git pull origin main
git checkout v0.3.0
```

### Adopting the New Utility Scripts

```bash
# Activate a conda environment with structured sections
source scripts/activate_conda_env.bash JuniperData

# Clean up stale worktrees
bash scripts/remove_stale_worktrees.bash

# Prune local branches that no longer have a working directory
bash scripts/prune_git_branches_without_working_dirs.bash
```

---

## Known Issues

None known at time of release.

---

## Version History

| Version | Date       | Description                                                                                  |
| ------- | ---------- | -------------------------------------------------------------------------------------------- |
| 0.1.0   | 2026-02-22 | Initial `juniper` meta-package with optional dependency extras                               |
| 0.2.0   | 2026-02-27 | Renamed to `juniper-ml`, raised Python minimum to >=3.12, publish workflow tweaks            |
| 0.2.1   | 2026-03-06 | `wake_the_claude.bash` launcher with session ID security fixes                               |
| 0.3.0   | 2026-03-12 | Claude tooling suite (conda/worktree/branch helpers), `eval` removal, `--resume` regression test |

---

## Links

- [Full Changelog](../../CHANGELOG.md)
- [Previous Release: v0.2.1](RELEASE_NOTES_v0.2.1.md)
