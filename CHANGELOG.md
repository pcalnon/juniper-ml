# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **TestPyPI extras-resolution verification extended to `[tools]`.**
  `.github/workflows/publish.yml` now runs a third `pip install` step
  after the bare-package install and the `[clients]` install: it also
  installs `juniper-ml[tools]==${VERSION}` from TestPyPI and imports
  the three `[tools]` packages (`juniper-ci-tools`,
  `juniper-doc-tools`, `juniper-observability`). Both light extras
  (`[clients]` + `[tools]`) are now exercised at publish time, closing
  the gap documented in the v0.5.0 release runbook §7 (which
  previously called out `[tools]` as caught only by the schema lint,
  not at publish time). `[servers]` and `[worker]` remain
  schema-lint-only because their dependency trees are too heavy to
  resolve in every release run. Matching runbook §7 update so the
  documented behavior matches reality.

- **`juniper-ml[all]` install-size advisory corrected** in
  `docs/QUICK_START.md`, `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`,
  and `notes/META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`. The
  original v0.5.0 estimate of "roughly 2 GB" understated the resolved
  on-disk footprint by ~2.5x: the actual figure measured against PyPI
  on 2026-05-21 (Python 3.13, Linux x86_64) was **5 GB on disk after
  install**. The advisory also now gives concrete per-extra footprints
  (`[clients]`, `[tools]`, `[doc-tools]` < 50 MB each; `[servers]`
  < 200 MB). Pure documentation correction; no code or pin changes.

## [0.5.0] - 2026-05-21

### Added

- **TestPyPI extras-resolution verification step** in
  `.github/workflows/publish.yml`. After the bare-package install
  verification, the workflow now also installs `juniper-ml[clients]`
  from TestPyPI and imports both client modules. This exercises the
  full `[project.optional-dependencies]` resolution path against the
  published metadata, so a broken extras declaration (mistyped name,
  missing roll-up into `[all]`, dangling self-reference) fails the
  publish rather than landing on PyPI silently. `[clients]` is chosen
  because it is the lightest extra (no torch) and still walks the full
  resolver path.

- **`notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.5.0_2026-05-21.md`**
  -- runbook for the v0.5.0 release. Documents preconditions, the
  TestPyPI / PyPI flow, the new extras-resolution verification step,
  and the rollback options (yank vs. patch release) for a meta-package
  whose extras surface has expanded.

- **`tests/test_agents_md_version_drift.py`** -- new lint test pinning
  `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s
  `[project].version`. juniper-ml#295 bumped `pyproject.toml` from
  0.4.1 to 0.5.0 but left `AGENTS.md` at 0.4.0 for ~6 days (drift
  caught by ad-hoc grep + fixed in juniper-ml#304); this lint makes
  the failure class impossible to ship. Wired into the main CI tests
  job; intentionally portable (auto-locates the repo root) so the
  same module can be dropped into any Juniper repo's `tests/` to
  catch the same drift class there.

- **`notes/META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`** -- source
  requirements doc for the meta-package extras surface. Specifies the
  declared groups, `[all]` aggregate semantics, version-bump policy,
  documentation-consistency surfaces, regression-coverage expectations,
  and the install-size advisory. Written in the source-doc format that
  the next snapshot consolidation pass can ingest; `JR-ML-*` IDs will
  be assigned at that pass and referenced retroactively in PRs #293,
  #295, #299.

- **Install-size advisory for `juniper-ml[all]`** in `docs/QUICK_START.md`.
  Calls out that `[all]` transitively pulls a multi-GB dependency tree
  (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`,
  approx. 2 GB on a fresh env) and recommends narrower extras
  (`[clients]`, `[tools]`, `[doc-tools]`) when the worker / server
  distributions are not needed.

- **`tests/test_pyproject_extras.py`** -- new lint test pinning the
  `[project.optional-dependencies]` surface so accidental edits (drop,
  mistype, fail to roll up into `[all]`) fail loudly in CI. Schema-strict:
  any future change to extras must update the lint contract in the same
  PR. Wired into the main CI tests job; runs alongside
  `test_doc_tools_drift.py` and `test_workflow_script_paths.py`.

- **`[servers]` optional dependency group** for the three Juniper service
  packages on PyPI. `pip install juniper-ml[servers]` now installs
  `juniper-canopy>=0.3.0`, `juniper-cascor>=0.3.17`, and
  `juniper-data>=0.6.0` in a single step. Previously the meta-package
  only aggregated the client/worker libraries; the server distributions
  had to be installed by name.

- **`[tools]` optional dependency group** that aggregates the three
  PyPI-published Juniper tool packages: `juniper-ci-tools>=0.1.0`
  (dependency-documentation generator, Wave 1 of the dep-docs migration
  plan), `juniper-doc-tools>=0.1.0,<0.2.0` (markdown link validator),
  and `juniper-observability>=0.2.0` (shared Prometheus collector
  helpers + structured logging + Starlette middleware). The
  pre-existing `[doc-tools]` extra is retained for back-compat with
  callers that already installed via that name.

- **`[all]` extra expanded** to cover the new `[servers]` and `[tools]`
  groups in addition to `[clients]` and `[worker]`. A single
  `pip install juniper-ml[all]` now pulls in every published Juniper
  package: 3 servers, 2 clients, 1 worker, and 3 tools.

### Changed

- **Pre-tag docs polish for the 0.5.0 release.** Refreshes the three
  Ecosystem Compatibility tables (`README.md`, `docs/REFERENCE.md`,
  `docs/DOCUMENTATION_OVERVIEW.md`) to enumerate every package the
  meta-package now pins -- canopy / cascor / data / data-client /
  cascor-client / cascor-worker / ci-tools / doc-tools / observability
  -- with their actual pyproject pins (the previous tables only listed
  3-5 packages and used stale `0.4.x` headers). Adds `[servers]`,
  `[tools]`, and `[doc-tools]` editable-install commands to `AGENTS.md`
  and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, plus an explicit
  multi-GB callout on `[all]`.

- **Version bumped to 0.5.0** (semver minor) to mark the new optional
  dependency surface. No removals or breaking changes -- existing
  `[clients]`, `[worker]`, `[doc-tools]`, and `[all]` install commands
  continue to work; `[all]` is now a strict superset.
- **`juniper-observability` is now aggregated under `juniper-ml[tools]`
  and `juniper-ml[all]`.** Until 0.4.1 it was published from this
  repository as a sibling package that had to be installed directly.
  Documentation in `README.md`, `docs/QUICK_START.md`,
  `docs/REFERENCE.md`, and `docs/DOCUMENTATION_OVERVIEW.md` updated to
  reflect this. Independent versioning and the
  `juniper-observability-v*` tag pipeline are unchanged.

- **§5 drift-detection guard rails** for the `juniper-doc-tools` PyPI
  migration (plan
  [`notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)
  §5.1 + §5.2). Closes the open follow-ups from Wave 4.
  - `tests/test_doc_tools_drift.py` — consumer-version-pin lint. Reads
    the current `juniper-doc-tools` version from
    `juniper-doc-tools/pyproject.toml`, then walks each cloned consumer
    repo's `ci.yml` and asserts the `juniper-doc-tools>=X,<Y` pin still
    admits current. Soft-warns when a pin lags by more than 2 minors;
    hard-fails when the upper bound excludes current. Also lints
    juniper-ml's own `ci.yml` + `docs-full-check.yml` for the same pin
    rule (this case runs even per-PR; the cross-repo assertion auto-
    skips when siblings aren't on disk). Local runs skip the cross-repo
    assertion by default to avoid stale-working-tree false positives;
    set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to override.
  - `.github/workflows/docs-full-check.yml` — two new steps in the
    weekly cross-repo workflow:
    - "Lint doc-tools pins across consumer repos" invokes the new test.
    - "Downstream-consumer integration check" installs `juniper-doc-tools`,
      runs `juniper-check-doc-links` against each cloned consumer repo's
      docs with the canonical Juniper exclude set, and aggregates per-
      repo results. Per-repo failures are warned; the step fails only
      when `>=DOWNSTREAM_FAIL_THRESHOLD` consumers regress in the same
      week (default 5 of 6 = catastrophic juniper-doc-tools regression).

### Removed

- **`util/check_doc_links.py`** (the inline v0.7.0 validator) — Wave 2 + Wave 4 of the doc-link migration plan. Replaced by the PyPI-published `juniper-doc-tools` package; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`. The CI docs jobs (`ci.yml`, `docs-full-check.yml`) now install the package and run the console script. Inline copies in all 7 sibling repos (canopy / cascor / data / cascor-client / cascor-worker / data-client / ml) are deleted in the same wave.
- `scripts/check_doc_links.py` (symlink to the old `util/` copy), `util/check_doc_links.bash` (local-path-only convenience wrapper), and `tests/test_check_doc_links.py` (now covered by `juniper-doc-tools/tests/`).

### Added

- `util/check_doc_links.py` bumped to **v0.7.0**: classifies ecosystem-root paths (`../../CLAUDE.md`, `../../AGENTS.md`, `../../notes/`, `../../prompts/`, `../../resources/`, `../../backups/`, `../../logs/`, `../../worktrees/`, `../../juniper-legacy/`, `../../Juniper{,1}.code-workspace`) the same way as cross-repo `../juniper-X/` links: subject to the `--cross-repo` policy (skip/warn/check). Restores parity with the more permissive behavior repo docs were already relying on without silently accepting truly broken outside-repo links. 5 new regression tests in `tests/test_check_doc_links.py` cover the ecosystem-root paths and a guard against misclassifying intra-repo links that happen to traverse a `notes/`-named directory.
- `tests/test_workflow_script_paths.py` — new lint test that walks `.github/workflows/*.yml`, extracts every script path referenced via `python|bash <path>` / `python3 -m unittest ... <path.py>` / `$VAR <path>` patterns, and asserts each path exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18 when a script was renamed without updating the workflow. Designed to be copy-and-paste portable into the other Juniper repos' `tests/` directories.
- **`juniper-doc-tools` subpackage scaffold** — Wave 0 of the doc-link
  validator PyPI migration ([plan](notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md)).
  New `juniper-doc-tools/` subdirectory packages the v0.7.0 markdown link
  validator as a PyPI distribution with a stable CLI surface
  (`juniper-check-doc-links` + `python -m juniper_doc_tools`), a small
  library API (`validate_directory`, `validate_file`, `ValidationResult`),
  and the new `--strict-repo-boundary` opt-out flag from §3.4.1 / §8.4.
  Tests use pytest (§8.1); 30 tests cover the v0.7.0 behavior, the new
  flag, and CLI argparse end-to-end. `.github/workflows/ci-doc-tools.yml`
  runs the test matrix (3.12/3.13/3.14) + build + wheel smoke-test on
  PRs touching `juniper-doc-tools/**`. `.github/workflows/publish-doc-tools.yml`
  publishes to TestPyPI → PyPI on tags matching `juniper-doc-tools-v*`,
  mirroring the existing `publish-observability.yml`.
- **`juniper-doc-tools` 0.1.0 published to PyPI** — Wave 1 of the
  migration plan. Tag `juniper-doc-tools-v0.1.0` cut from `main` on
  2026-05-19; OIDC trusted publish went through TestPyPI → PyPI without
  intervention (TestPyPI verified install + console-script + module-form
  on a fresh runner). `pip install juniper-doc-tools` now works from
  any environment. New `[doc-tools]` extra in this `pyproject.toml`
  pins the consumer to `>=0.1.0,<0.2.0` so a future breaking minor
  bump does not auto-adopt before Wave 2 swaps each repo's CI over.
  Next: Wave 2 (per-repo CI swap) starts in juniper-ml itself, then
  fans out to the 7 other ecosystem repos.

## [0.4.1] - 2026-04-28

### Added

- **`juniper-observability` package (alpha `0.1.1a`)** — new sibling package living under `juniper-observability/` (METRICS-MON R2.1.1, PR #155). Provides cross-cutting observability primitives shared by every Juniper server: health models (`DependencyStatus`, `ReadinessResponse`), the synchronous `probe_dependency` helper, structured-JSON logging (`JuniperJsonFormatter`, `configure_logging`) with `request_id` propagation, Starlette middlewares (`RequestIdMiddleware`, `PrometheusMiddleware` with bounded label cardinality per R1.1), pinned cross-service constants (`UNMATCHED_ENDPOINT_LABEL`, `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`, `LIVENESS_STALENESS_SECONDS`), Prometheus utilities (`get_prometheus_app`, `set_build_info`), and Sentry init (`configure_sentry`) with the SEC-10 `before_send` hook always installed. Optional extras: `[prometheus]`, `[sentry]`, `[all]`. Per-service metric definitions intentionally stay in their owning repos; this package only exposes cross-cutting infrastructure.
- `.github/workflows/ci-observability.yml` — dedicated CI pipeline for the observability package.
- `.github/workflows/publish-observability.yml` — OIDC trusted-publishing workflow for `juniper-observability` (TestPyPI → install verification → PyPI), triggered by tags matching `juniper-observability-v*` so it stays decoupled from the meta-package's own `v*` release tags. `workflow_dispatch` is enabled so operators can re-fire a publish against any tag.
- Hardcoded-values refactor (Wave 3 + Wave 4): all 6 `util/get_cascor_*.bash` REST query utilities now read `JUNIPER_CASCOR_HOST` and `JUNIPER_CASCOR_PORT` from the environment (defaulting to `localhost` / `8201`) so a single environment override targets every utility instead of editing each script individually.
- `util/juniper_plant_all.bash` `JUNIPER_CASCOR_HOST` is now an env-var override (`JUNIPER_CASCOR_HOST=${JUNIPER_CASCOR_HOST:-localhost}`) — useful for orchestrating remote services from a control host.
- New regression test suite `tests/test_worktree_cleanup.py` covering argument parsing, dry-run output, error handling, and the critical safety property that the new worktree is created before the old one is removed (CWD-trap prevention).
- Metrics-monitoring roadmap and design notes under `notes/code-review/` covering R1.1–R1.3 contracts and the R2.1 shared-observability migration sequence; ongoing Track 1–6 status sweeps marking shipped/blocked/open work across the ecosystem.

### Changed

- `.github/workflows/publish-observability.yml` — `verbose: true` enabled on both the TestPyPI and PyPI `pypa/gh-action-pypi-publish` steps so upload failures surface the underlying response body instead of twine's bare `Bad Request` line.
- Hardcoded-values refactor (Wave 3): `util/worktree_cleanup.bash` `MAIN_REPO` is now derived from `${BASH_SOURCE[0]}` (one directory up from the script) instead of being hardcoded to `/home/pcalnon/Development/python/Juniper/juniper-ml`. An optional `JUNIPER_ML_MAIN_REPO` environment variable overrides the derived path for test fixtures and unusual layouts. This makes the script portable across machines and CI runners.
- Test timeout constants extracted in `tests/test_wake_the_claude.py` and `tests/test_worktree_cleanup.py` (`SCRIPT_TIMEOUT_SECONDS`) instead of inline `subprocess.run(..., timeout=30)` calls.
- AGENTS.md "Utilities" section updated to document the new env-var overrides for `worktree_cleanup.bash`, `juniper_plant_all.bash`, and the `get_cascor_*.bash` utilities.

### Notes

- All 88 unittest tests pass plus the bash `test_resume_file_safety.bash` regression script; pre-commit (17 hooks: flake8, bandit, shellcheck, markdownlint, yamllint, sops-check) is clean.
- This branch is on `feature/hardcoded-values-wave3` rather than `wave1` because juniper-ml had no Wave 1 task in the master roadmap (the meta-package owns no application code that needed a constants module).
- `juniper-observability` is not yet wired into the `juniper-ml[all]` extras. It will be added once the alpha graduates and downstream services start importing from it as part of the R2.1 migration.

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

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/pcalnon/juniper-ml/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/pcalnon/juniper-ml/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pcalnon/juniper-ml/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/pcalnon/juniper-ml/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
