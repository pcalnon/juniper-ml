# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `scripts/test_resume_file_safety.bash` — Added a focused regression script that verifies invalid `--resume <file.txt>` input returns non-zero and preserves the source file.
- `notes/DEVELOPER_CHEATSHEET.md` — Added a `wake_the_claude.bash` quick runbook covering usage/help exit codes, debug-mode behavior, and `--resume` troubleshooting.
- `notes/DEVELOPER_CHEATSHEET.md` — Added a regression-test command (`python3 -m unittest tests/test_wake_the_claude.py -v`) and coverage notes for resume validation, symlink-write protection, and prompt argument safety.
- `notes/DEVELOPER_CHEATSHEET.md` — Documented regression-suite execution expectations (fake `claude` shim) and a troubleshooting note for `test_session_id_save_rejects_symlink_target` contract mismatches.
- `notes/DEVELOPER_CHEATSHEET.md` and `AGENTS.md` — Documented the `test_resume_file_safety.bash` workflow so resume-file preservation checks are part of standard troubleshooting and regression runs.
- `notes/DEVELOPER_CHEATSHEET.md` — Added explicit `--resume` missing/empty `.txt` validation checks, including expected single-usage failure behavior and no Claude launch on rejection.
- `notes/DEVELOPER_CHEATSHEET.md` — Documented `--resume` alias handling (`-r`, `--resume`, `--resume-thread`, `--resume-session`), canonical forwarding to `--resume <uuid>`, and a targeted regression command for trailing alias matching.
- `notes/DEVELOPER_CHEATSHEET.md` — Updated `wake_the_claude.bash` runbooks for interactive-vs-headless launch behavior, `scripts/sessions` session-file storage, headless log location/fallback, and `cly` wrapper usage.
- `docs/DOCUMENTATION_OVERVIEW.md` — Added navigation links for Claude session tooling runbooks so operational docs are discoverable from the docs index.

### Fixed

- `scripts/wake_the_claude.bash` — Replaced `eval`-based flag matching in `matches_pattern()` with split-and-compare logic.
- `scripts/wake_the_claude.bash` — Moved `debug_log` and `redact_uuid` definitions before top-level calls to prevent `command not found` stderr noise.
- `scripts/wake_the_claude.bash` — Hardened `--id` (without value) session generation to validate UUIDs across multiple fallback sources when `uuidgen` is unavailable.

### Security

- `scripts/wake_the_claude.bash` — Removed a latent command-injection vector by eliminating `eval` from pattern matching.

## [0.2.1] - 2026-03-06

### Added

- `scripts/wake_the_claude.bash` — Shell script to launch Claude Code sessions with configurable flags, session persistence, and resume support
- `notes/SESSION_ID_VALIDATION_BUGFIX_PLAN.md` — Root cause analysis and fix plan
- `notes/SECURITY_REMEDIATION_PLAN.md` — Security vulnerability analysis and remediation plan
- `notes/pull_requests/PR_SESSION_ID_VALIDATION_BUGFIX.md` — PR description archive
- `notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md` — PR description template (adopted from sibling repos)

### Fixed

- **Session ID validation**: Redirected diagnostic `echo` statements to stderr (`>&2`) in `is_valid_uuid`, `retrieve_session_id`, and `validate_session_id`, reserving stdout exclusively for return values captured via `$(...)`
- **Subshell exit status**: Moved `RETURN_VALUE=$?` to a separate line after command substitution so the exit status propagates to the parent scope
- **Double usage print**: Replaced `usage`/`exit` calls with `return` inside `validate_session_id`, since `exit` inside `$(...)` only terminates the subshell
- **Ambiguous log message**: Added `session_id_filename` local variable to preserve the original filename for the "from file" log message

### Security

- **Path traversal in `--resume`** (High): Reject filenames containing path separators (`/`) or lacking `.txt` extension; removed destructive `rm -f` from `retrieve_session_id`; suppressed raw file content in error logs
- **Arbitrary file write in `save_session_id`** (High): Added UUID format validation before any filesystem write; applied `basename` defense-in-depth; scoped `session_id` as `local`
- **Argument injection via `CLAUDE_CODE_PARAMS`** (Medium): Converted from flat string to bash array; execute with `"${CLAUDE_CODE_PARAMS[@]}"` to prevent word-splitting injection

## [0.2.0] - 2026-02-27

### Added

- CLAUDE.md for Claude Code onboarding
- PyPI publishing procedure documentation (`notes/pypi-publish-procedure.md`)

### Changed

- Renamed package from `juniper` to `juniper-ml`
- Raised minimum Python version to `>=3.12`
- Expanded keywords in package metadata

### Fixed

- Added `attestations: false` to publish.yml for both TestPyPI and PyPI steps

## [0.1.0] - 2026-02-22

### Added

- Initial `juniper` meta-package with `pyproject.toml`
- Optional dependency extras: `clients`, `worker`, `all`
- GitHub Actions CI/CD publish workflow (TestPyPI + PyPI with trusted publishing)
- README with installation instructions and ecosystem overview
- MIT License

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/pcalnon/juniper-ml/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
