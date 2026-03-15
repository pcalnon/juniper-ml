# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-03-12

### Added

- `scripts/activate_conda_env.bash` — Bash helper for conda environment activation/deactivation with structured sections for compilation workflows
- `scripts/cleanup_open_worktrees.bash` — Automates git worktree cleanup by iterating through worktrees and performing status/add/pull/push operations
- `scripts/prune_git_branches_without_working_dirs.bash` — Prunes local git branches that lack corresponding working directories; supports standard and forced deletion modes
- `scripts/remove_stale_worktrees.bash` — Iterates through and removes stale git worktrees
- `scripts/test_resume_file_safety.bash` — Focused regression script that verifies invalid `--resume <file.txt>` input returns non-zero and preserves the source file
- `notes/stack_overflow_answer.txt` — Reference material on managing conda environments programmatically in bash scripts
- `notes/pull_requests/PR_TOOLING_MORE_CLAUDE_UTILS.md` — PR description archive
- `notes/DEVELOPER_CHEATSHEET.md` — Added session ID workflow documentation, `wake_the_claude.bash` quick runbook, regression-test commands, `--resume` alias handling, interactive-vs-headless launch behavior, and troubleshooting sections
- `docs/DOCUMENTATION_OVERVIEW.md` — Added navigation links for Claude session tooling runbooks
- New test coverage in `tests/test_wake_the_claude.py` for default launcher argument forwarding, permissions handling, and prompt token validation

### Changed

- `scripts/wake_the_claude.bash` — Uncommented `EFFORT_VALUE` and `MODEL_VALUE` assignments; refactored nohup logging to handle missing log files; changed debug output to standard echo; consolidated exit status checks
- `.github/workflows/ci.yml` — Standardized comment spacing for action version tags (dependabot version bumps)
- `notes/CONDA_DEPENDENCY_FILE_HEADER.md` — Renamed back from `.yaml` to `.md` (matching all other repos' naming convention)
- `CHANGELOG.md` — Added version identifiers to section headers for released versions
- Documentation formatting pass across `notes/` planning documents — standardized Markdown table alignment, added `bash` language tags to code blocks, converted URLs to Markdown link syntax

### Fixed

- `scripts/wake_the_claude.bash` — Replaced `eval`-based flag matching in `matches_pattern()` with split-and-compare logic
- `scripts/wake_the_claude.bash` — Moved `debug_log` and `redact_uuid` definitions before top-level calls to prevent `command not found` stderr noise
- `scripts/wake_the_claude.bash` — Hardened `--id` (without value) session generation to validate UUIDs across multiple fallback sources when `uuidgen` is unavailable

### Security

- `scripts/wake_the_claude.bash` — Removed a latent command-injection vector by eliminating `eval` from pattern matching

## [0.2.1] - 2026-03-06

### Added, 0.2.1

- `scripts/wake_the_claude.bash` — Shell script to launch Claude Code sessions with configurable flags, session persistence, and resume support
- `notes/SESSION_ID_VALIDATION_BUGFIX_PLAN.md` — Root cause analysis and fix plan
- `notes/SECURITY_REMEDIATION_PLAN.md` — Security vulnerability analysis and remediation plan
- `notes/pull_requests/PR_SESSION_ID_VALIDATION_BUGFIX.md` — PR description archive
- `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md` — PR description template (adopted from sibling repos)

### Fixed, 0.2.1

- **Session ID validation**: Redirected diagnostic `echo` statements to stderr (`>&2`) in `is_valid_uuid`, `retrieve_session_id`, and `validate_session_id`, reserving stdout exclusively for return values captured via `$(...)`
- **Subshell exit status**: Moved `RETURN_VALUE=$?` to a separate line after command substitution so the exit status propagates to the parent scope
- **Double usage print**: Replaced `usage`/`exit` calls with `return` inside `validate_session_id`, since `exit` inside `$(...)` only terminates the subshell
- **Ambiguous log message**: Added `session_id_filename` local variable to preserve the original filename for the "from file" log message

### Security, 0.2.1

- **Path traversal in `--resume`** (High): Reject filenames containing path separators (`/`) or lacking `.txt` extension; removed destructive `rm -f` from `retrieve_session_id`; suppressed raw file content in error logs
- **Arbitrary file write in `save_session_id`** (High): Added UUID format validation before any filesystem write; applied `basename` defense-in-depth; scoped `session_id` as `local`
- **Argument injection via `CLAUDE_CODE_PARAMS`** (Medium): Converted from flat string to bash array; execute with `"${CLAUDE_CODE_PARAMS[@]}"` to prevent word-splitting injection

## [0.2.0] - 2026-02-27

### Added, 0.2.0

- CLAUDE.md for Claude Code onboarding
- PyPI publishing procedure documentation (`notes/pypi-publish-procedure.md`)

### Changed, 0.2.0

- Renamed package from `juniper` to `juniper-ml`
- Raised minimum Python version to `>=3.12`
- Expanded keywords in package metadata

### Fixed, 0.2.0

- Added `attestations: false` to publish.yml for both TestPyPI and PyPI steps

## [0.1.0] - 2026-02-22

### Added, 0.1.0

- Initial `juniper` meta-package with `pyproject.toml`
- Optional dependency extras: `clients`, `worker`, `all`
- GitHub Actions CI/CD publish workflow (TestPyPI + PyPI with trusted publishing)
- README with installation instructions and ecosystem overview
- MIT License

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/pcalnon/juniper-ml/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/pcalnon/juniper-ml/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
