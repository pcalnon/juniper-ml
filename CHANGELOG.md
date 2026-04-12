# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Hardcoded-values refactor (Wave 3 + Wave 4): all 6 `util/get_cascor_*.bash` REST query utilities now read `JUNIPER_CASCOR_HOST` and `JUNIPER_CASCOR_PORT` from the environment (defaulting to `localhost` / `8201`) so a single environment override targets every utility instead of editing each script individually.
- `util/juniper_plant_all.bash` `JUNIPER_CASCOR_HOST` is now an env-var override (`JUNIPER_CASCOR_HOST=${JUNIPER_CASCOR_HOST:-localhost}`) — useful for orchestrating remote services from a control host.
- New regression test suite `tests/test_worktree_cleanup.py` covering argument parsing, dry-run output, error handling, and the critical safety property that the new worktree is created before the old one is removed (CWD-trap prevention).

### Changed

- Hardcoded-values refactor (Wave 3): `util/worktree_cleanup.bash` `MAIN_REPO` is now derived from `${BASH_SOURCE[0]}` (one directory up from the script) instead of being hardcoded to `/home/pcalnon/Development/python/Juniper/juniper-ml`. An optional `JUNIPER_ML_MAIN_REPO` environment variable overrides the derived path for test fixtures and unusual layouts. This makes the script portable across machines and CI runners.
- Test timeout constants extracted in `tests/test_wake_the_claude.py` and `tests/test_worktree_cleanup.py` (`SCRIPT_TIMEOUT_SECONDS`) instead of inline `subprocess.run(..., timeout=30)` calls.
- AGENTS.md "Utilities" section updated to document the new env-var overrides for `worktree_cleanup.bash`, `juniper_plant_all.bash`, and the `get_cascor_*.bash` utilities.

### Notes

- All 88 unittest tests pass plus the bash `test_resume_file_safety.bash` regression script; pre-commit (17 hooks: flake8, bandit, shellcheck, markdownlint, yamllint, sops-check) is clean.
- This branch is on `feature/hardcoded-values-wave3` rather than `wave1` because juniper-ml had no Wave 1 task in the master roadmap (the meta-package owns no application code that needed a constants module).

## [0.4.0] - 2026-04-09

**Summary**: Microservices orchestration layer (`juniper_plant_all.bash` / `juniper_chop_all.bash`), full systemd integration, V2 worktree cleanup orchestrator with CWD-safe session continuity, CasCor REST API query utilities, the `claudey` interactive launcher, and ecosystem version convergence — extras bumped to track the latest released `juniper-data-client`, `juniper-cascor-client`, and `juniper-cascor-worker`. Also incorporates the cross-project release-prep code review and remediation plan.

See [`notes/releases/RELEASE_NOTES_v0.4.0.md`](notes/releases/RELEASE_NOTES_v0.4.0.md) for the full release notes.

### Changed

- Bumped minimum versions of optional dependency extras to track latest releases:
  - `juniper-data-client` from `>=0.3.0` to `>=0.4.0` (adds batch operations and dataset versioning)
  - `juniper-cascor-client` from `>=0.1.0` to `>=0.3.0` (adds worker/snapshot/dataset methods, testing module)
  - `juniper-cascor-worker` from `>=0.1.0` to `>=0.3.0` (WebSocket-based agent, TLS support, deprecates legacy mode)

### Added

- `util/juniper_plant_all.bash` -- Microservices startup script with health checks, conda environment activation, and PID file management
- `util/juniper_chop_all.bash` -- Microservices shutdown script with graceful SIGTERM/SIGKILL escalation, PID file parsing, and orphaned worker cleanup
- Systemd integration (`--systemd` mode) for both startup and shutdown scripts, including `juniper-all-ctl` management script and `juniper-all.target` unit
- Cascor-worker integration into systemd target and startup/shutdown scripts (Phase 3)
- `util/worktree_cleanup.bash` -- V2 automated worktree cleanup orchestrator with CWD-safe session continuity
- `tests/test_worktree_cleanup.py` -- Regression tests for worktree cleanup argument parsing, dry-run, and error handling
- `util/worktree_new.bash`, `util/worktree_activate.bash`, `util/worktree_close.bash`, `util/worktree_wipeout.bash` -- Worktree management utilities
- `util/get_cascor_status.bash`, `util/get_cascor_metrics.bash`, `util/get_cascor_history.bash`, `util/get_cascor_network.bash`, `util/get_cascor_topology.bash` -- CasCor REST API query utilities
- `scripts/claude_interactive.bash` -- Interactive Claude Code agent launcher (`claudey` symlink at repo root)
- Cross-project regression analysis, remediation plans, and development roadmaps in `notes/`

### Changed

- `AGENTS.md` updated to v0.4.0 with comprehensive structure documentation, CI/CD pipeline details, and worktree/handoff procedures
- Dependabot CI action version bumps: `anthropics/claude-code-action` (1.0.62 -> 1.0.89), `actions/cache` (4.2.3 -> 5.0.4), `actions/upload-artifact` (6.0.0 -> 7.0.0), `actions/download-artifact` (8.0.0 -> 8.0.1)
- Moved worktree management and documentation utilities from `scripts/` to `util/`

### Fixed

- CI `dependency-docs` job path corrected from `scripts/generate_dep_docs.sh` to `util/generate_dep_docs.sh`
- PID file parsing in `juniper_chop_all.bash` replaced `read -d ''` (whitespace splitting) with `mapfile -t` (line-oriented) to handle multi-word PID file lines correctly
- Removed contradictory `done < PID_FILE` redirect from for-loop that iterated over an already-populated array
- `juniper_chop_all.bash` `KILL_WORKERS` default changed from hardcoded `"1"` to `"0"` to match documented behavior
- `juniper_chop_all.bash` `SIGTERM_TIMEOUT` default changed from hardcoded `"10"` to environment-variable-driven `"15"` to match documented behavior
- Worker search term narrowed from `"cascor"` to `"juniper-cascor-worker"` to prevent false-positive matches against the cascor backend
- Added `test_worktree_cleanup.py` to CI pipeline test execution
- PID reference fixes in startup scripts (`juniper_plant_all.bash`)
- Test script paths updated after `scripts/` to `util/` migration

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
