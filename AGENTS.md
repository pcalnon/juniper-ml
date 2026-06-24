# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-24

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is `juniper-ml`, a **meta-package** for the Juniper ML research platform. It provides a single `pip install juniper-ml[all]` entry point that pulls in the actual Juniper packages as dependencies, and also contains internal automation scripts used for Claude Code workflows, utility tooling for the Juniper ecosystem, and project documentation.

There is no importable Python application package in this repository. Functional behavior here is primarily package metadata (`pyproject.toml`) plus shell tooling in `scripts/` and `util/`, with regression coverage in `tests/`.

## Build & Package Commands

```bash
# Build
pip install build twine
python -m build

# Validate package
twine check dist/*

# Install locally (editable)
pip install -e .               # base (no deps)
pip install -e ".[clients]"    # client libraries
pip install -e ".[worker]"     # distributed worker
pip install -e ".[servers]"    # canopy + cascor + data service packages
pip install -e ".[tools]"      # ci-tools + doc-tools + observability
pip install -e ".[doc-tools]"  # markdown link validator (back-compat alias)
pip install -e ".[all]"        # everything (multi-GB; pulls torch via worker)

# Run all tests
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_worktree_cleanup.py
python3 -m unittest -v tests/test_worktree_sweep_scripts.py
python3 -m unittest -v tests/test_reap_pytest_orphans.py
python3 -m unittest -v tests/test_requirements_drift_check.py
python3 -m unittest -v tests/test_editable_install_drift_check.py
python3 -m unittest -v tests/test_workflow_script_paths.py
python3 -m unittest -v tests/test_doc_tools_drift.py
python3 -m unittest -v tests/test_pyproject_extras.py
python3 -m unittest -v tests/test_template_library_drift.py
python3 -m unittest -v tests/test_agents_md_version_drift.py
python3 -m unittest -v tests/test_agents_md_header_schema.py
bash scripts/test_resume_file_safety.bash
# doc-link validator regression tests live in juniper-doc-tools/tests/
# and run under the dedicated `CI -- juniper-doc-tools` workflow.

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links (requires `pip install juniper-doc-tools`
# or `pip install -e juniper-doc-tools/` for editable local development)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy

# Validate documentation links (including cross-repo)
juniper-check-doc-links --exclude templates --exclude history --exclude legacy --cross-repo check
```

## Publishing

Releases are published via GitHub Actions (`.github/workflows/publish.yml`). The workflow is triggered by a GitHub release event and publishes first to TestPyPI (with install verification), then to PyPI. Both environments use trusted publishing (OIDC, no API tokens).

**Release convention (mandatory, all packages).** Every PyPI deploy — the meta-package and every
shared / sub-package — is performed by **cutting a GitHub Release** (never a bare `git push <tag>`),
and the release notes are authored from
[`notes/templates/TEMPLATE_RELEASE_NOTES.md`](notes/templates/TEMPLATE_RELEASE_NOTES.md) and
**archived under `notes/releases/`** (`RELEASE_NOTES_v<version>.md` for the meta-package;
`RELEASE_NOTES_<pkg>_v<version>.md` for a shared / sub-package). For the meta-package the Release
event triggers `publish.yml`; for a tag-triggered shared / sub-package, cutting the Release
**creates** the `juniper-<pkg>-v*` tag, which triggers its `publish-<pkg>.yml`. Full steps:
[`notes/PYPI-PUBLISH-PROCEDURE.md` §11](notes/PYPI-PUBLISH-PROCEDURE.md). (This convention drifted
during rapid concurrent refactoring — several sub-packages shipped tag-only — and is being restored.)

The shared `juniper-observability` package is published separately from the same repo (subdirectory `juniper-observability/`) by `.github/workflows/publish-observability.yml`, triggered by tags matching `juniper-observability-v*`.

The shared `juniper-doc-tools` package (Wave 0 scaffold, plan
[`notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](notes/JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md))
is published from subdirectory `juniper-doc-tools/` by
`.github/workflows/publish-doc-tools.yml`, triggered by tags matching
`juniper-doc-tools-v*`. It packages the markdown link validator
(`juniper-check-doc-links` console script + `python -m juniper_doc_tools`
module form) so that the 8 ecosystem repos can replace their inline
`scripts/check_doc_links.py` copies with a single PyPI dependency.

The shared `juniper-ci-tools` package (Wave 0 scaffold, plan
[`notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`](notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md))
is published from subdirectory `juniper-ci-tools/` by
`.github/workflows/publish-ci-tools.yml`, triggered by tags matching
`juniper-ci-tools-v*`. It packages the dependency-documentation generator
(`juniper-generate-dep-docs` console script + `python -m juniper_ci_tools`
module form), Python port of the legacy `scripts/generate_dep_docs.sh` that
drifted across 8 Juniper repos. Replaces all consumer inline copies via a
single PyPI dependency; carries the cascor 2026-05-20 awk-extraction fix as
the canonical implementation.

## Shared Observability Helpers

`juniper-observability` (this repo's `juniper-observability/` subdirectory, published as a standalone PyPI package) is the canonical home for cross-service observability primitives — middlewares, the build-info `Info` metric helper, structured-JSON logging, and **idempotent `prometheus_client` collector helpers**. Any new `Counter` / `Gauge` / `Histogram` / `Summary` / `Info` / `Enum` registration in any Juniper service should go through:

- `register_or_reuse(factory, name, *args, **kwargs)` — adopt-existing on duplicate (preserves accumulated samples; **default choice for almost every call site**).
- `register_fresh(factory, name, *args, **kwargs)` — drop-and-recreate (use only when test fixtures or migrations intentionally want different buckets/labels).
- `register_info_or_update(name, description, **info_labels)` — sugar for the `Info` two-step register-then-`.info({...})` pattern.
- `lazy_register_or_reuse(factory, name, *args, **kwargs)` — like `register_or_reuse` but caches the result in a module-private dict; for the lazy-init-with-`None`-sentinel pattern.

Tests touching these collectors should use `juniper_observability.testing.reset_prometheus_registry`. Minimum pin: `juniper-observability>=0.2.0`. See [`notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md`](notes/observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md) for the design rationale and the migration history.

## Repository Structure

```bash
juniper-ml/
├── AGENTS.md                  # This file (CLAUDE.md is a symlink to this)
├── CHANGELOG.md               # Version history (Keep a Changelog format)
├── LICENSE                    # MIT License
├── MANIFEST.in                # Source distribution includes
├── README.md                  # PyPI landing page content
├── pyproject.toml             # Package metadata, version, dependency extras
├── claudey                    # Symlink -> scripts/claude_interactive.bash
│
├── .github/
│   ├── CODEOWNERS             # Code ownership (@pcalnon)
│   ├── dependabot.yml         # Automated dependency updates (pip + actions)
│   └── workflows/
│       ├── ci.yml             # Main CI pipeline (pre-commit, tests, build, docs, security)
│       ├── publish.yml        # PyPI publishing (TestPyPI + PyPI, OIDC)
│       ├── docs-full-check.yml# Weekly full documentation link validation (cross-repo)
│       ├── security-scan.yml  # Weekly pip-audit security scanning
│       └── claude.yml         # Claude Code action for issue/PR automation
│
├── .serena/                   # Serena code agent integration config
│   └── project.yml            # Project: juniper_ml, language: python
│
├── docs/                      # User-facing documentation
│   ├── DOCUMENTATION_OVERVIEW.md         # Navigation index for all docs
│   ├── QUICK_START.md                    # Installation and verification guide
│   ├── REFERENCE.md                      # Extras, compatibility, env vars, service ports
│   └── DEVELOPER_CHEATSHEET_JUNIPER-ML.md# Quick-reference card for development tasks
│
├── images/                    # Project branding (logos v0-v9 in PNG/XCF/ICO, tree photos)
├── logs/                      # Runtime log output (.gitkeep)
├── resources/                 # External resources (AppImages, etc.)
│
├── notes/                     # Development notes, plans, and procedures
│   ├── WORKTREE_SETUP_PROCEDURE.md       # Worktree creation procedure
│   ├── WORKTREE_CLEANUP_PROCEDURE_V2.md  # Worktree cleanup procedure (CWD-safe)
│   ├── THREAD_HANDOFF_PROCEDURE.md       # Thread handoff protocol
│   ├── SOPS_USAGE_GUIDE.md              # Secrets encryption guide
│   ├── backups/               # Backup analysis/plan documents
│   ├── concurrency/           # Concurrency-related handoff notes
│   ├── development/           # Development analysis documents
│   ├── documentation/         # Documentation audit plans
│   ├── history/               # Historical plans and procedures
│   ├── proposals/             # Research proposals
│   ├── pull_requests/         # PR description archives
│   └── templates/             # Document templates (roadmap, issue, PR, release notes)
│
├── prompts/                   # Claude Code session prompts (chronological archive)
│   └── templates/             # Custom-agent prompt templates: manifest.yaml + generic.md + RUBRIC (drift-linted)
│
├── scripts/                   # Claude Code launcher and test scripts
│   ├── wake_the_claude.bash              # Core launcher: flag parsing, session persistence, resume
│   ├── claude_interactive.bash           # Interactive Claude Code agent launcher
│   ├── default_interactive_session_claude_code.bash  # Config template for interactive sessions
│   ├── activate_conda_env.bash           # Conda environment management
│   ├── resume_session.bash               # Session resume convenience wrapper
│   ├── cleanup_session_worktrees.py      # Bulk-clean Claude Code session worktrees in .claude/worktrees/
│   ├── test.bash                         # End-to-end test harness for launcher flows
│   ├── test_resume_file_safety.bash      # Regression: invalid --resume input safety
│   ├── test_prompt-*.md                  # Test prompt files for launcher testing
│   ├── sessions/                         # Session ID storage (.gitkeep)
│   └── backups/                          # Backup copies of older script versions
│
├── tests/                     # Regression test suites (Python unittest)
│   ├── test_wake_the_claude.py           # Launcher script regression (1470 lines)
│   ├── test_worktree_cleanup.py          # Worktree cleanup script tests (225 lines)
│   ├── test_worktree_sweep_scripts.py    # Ad-hoc sweep script safety/contract tests
│   ├── test_reap_pytest_orphans.py       # Orphan pytest process reaper tests
│   ├── test_requirements_drift_check.py  # Requirements snapshot drift checker tests
│   ├── test_editable_install_drift_check.py # Editable-install drift checker tests (orphaned / worktree-pinned)
│   ├── test_workflow_script_paths.py     # Lint: every .github/workflows/*.yml script path exists
│   ├── test_doc_tools_drift.py           # Lint: consumer-repo juniper-doc-tools pins still admit current version (plan §5.1)
│   ├── test_pyproject_extras.py          # Lint: pyproject [project.optional-dependencies] surface matches the contract
│   ├── test_template_library_drift.py    # Lint: custom-agent template library (prompts/templates/) manifest <-> templates
│   ├── test_agents_md_version_drift.py   # Lint: AGENTS.md **Version** header matches pyproject.toml [project].version
│   └── test_agents_md_header_schema.py   # Lint: AGENTS.md canonical header schema (6 required fields, ISO date format)
│   # Doc-link validator regression tests moved to juniper-doc-tools/tests/
│   # (Wave 4 of the doc-link migration plan; published under the dedicated
│   #  juniper-doc-tools PyPI package).
│
└── util/                      # Utility scripts and tools
    ├── ad-hoc/                           # Single-use / temporary / unfinished scripts (see ad-hoc/README.md)
    ├── requirements_drift_check.py       # Drift checker for the requirements snapshot (--mode quick)
    ├── editable_install_drift_check.py   # Drift checker for juniper editable installs across conda envs
    ├── worktree_cleanup.bash             # V2 cleanup orchestrator (CWD-safe)
    ├── worktree_new.bash                 # Creates new git worktree
    ├── worktree_activate.bash            # Bash helper for worktree activation
    ├── worktree_close.bash               # Removes a worktree, branch, and prunes
    ├── worktree_wipeout.bash             # Bulk removal by pattern
    ├── remove_stale_worktrees.bash       # Removes all stale worktrees
    ├── cleanup_open_worktrees.bash       # Removes all active worktrees
    ├── prune_git_branches_without_working_dirs.bash  # Branch hygiene
    ├── juniper_plant_all.bash            # Starts all Juniper ecosystem services
    ├── juniper_chop_all.bash             # Stops all Juniper ecosystem services
    ├── get_cascor_status.bash            # GET /v1/training/status
    ├── get_cascor_metrics.bash           # GET /v1/metrics
    ├── get_cascor_history.bash           # GET /v1/metrics/history?count=10
    ├── get_cascor_history-plus.bash      # GET /v1/metrics/history?count=100
    ├── get_cascor_network.bash           # GET /v1/network
    ├── get_cascor_topology.bash          # GET /v1/network/topology
    ├── kill_all_pythons.bash             # Emergency Python process terminator
    ├── search_file_in_all_repos_and_worktrees.bash   # Cross-repo file search
    └── global_text_replace.bash          # Batch sed find-and-replace
```

## Key Files

### Package and Metadata

- `pyproject.toml` -- Package metadata, version (`0.6.0`), and optional dependency groups (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`)
- `README.md` -- PyPI landing page content
- `CHANGELOG.md` -- Version history in Keep a Changelog format
- `MANIFEST.in` -- Source distribution file includes
- `LICENSE` -- MIT License

### Documentation

- `docs/DOCUMENTATION_OVERVIEW.md` -- Navigation index for all juniper-ml documentation
- `docs/QUICK_START.md` -- Installation and verification guide
- `docs/REFERENCE.md` -- Technical reference: extras, compatibility matrix, service ports, environment variables
- `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` -- Quick-reference card for development tasks

### Scripts and Launchers

- `scripts/wake_the_claude.bash` -- Claude Code launcher with flag parsing, session ID persistence, resume handling, and interactive/headless execution modes
- `scripts/claude_interactive.bash` -- Main interactive Claude Code agent launcher
- `scripts/default_interactive_session_claude_code.bash` -- Configuration template for default interactive Claude sessions
- `scripts/activate_conda_env.bash` -- Conda environment activation and management
- `scripts/resume_session.bash` -- Convenience wrapper for resuming a Claude Code session
- `claudey` -- Repo-root symlink to `scripts/claude_interactive.bash` for interactive sessions

### Utilities

- `util/worktree_cleanup.bash` -- Automated worktree cleanup with CWD-safe session continuity (V2 procedure). The `MAIN_REPO` path is now derived from `${BASH_SOURCE[0]}` (one directory up from the script) with an optional `JUNIPER_ML_MAIN_REPO` environment override for test fixtures and unusual layouts. Supports `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`.
- `util/reap_pytest_orphans.bash` -- Safely reaps orphaned Juniper pytest multiprocessing children. Supports `JUNIPER_REAP_PROC_ROOT` and `JUNIPER_REAP_KILL_CMD` test hooks for deterministic regression tests.
- Documentation link validator now lives in [`juniper-doc-tools/`](juniper-doc-tools/) and is published to PyPI as `juniper-doc-tools` (Wave 4 of the doc-link migration plan; install with `pip install juniper-doc-tools` and invoke via `juniper-check-doc-links`).
- `util/requirements_drift_check.py` -- Drift checker for the requirements snapshot at `notes/requirements/id_assignments.yaml`. Default `--mode quick` validates path resolution + structural line-range integrity for every citation; emits a human report or `--json`. Exit code 1 on any drift. Implements the spec in [`notes/REQUIREMENTS_NEXT_STEPS.md` §7](notes/REQUIREMENTS_NEXT_STEPS.md#7-stale--drift-detection); `--mode full` / `--mode rewrite` are reserved for future work.
- `util/editable_install_drift_check.py` -- Drift checker for juniper editable installs in the conda environments. Reads each env's `*.dist-info/direct_url.json` directly (robust to broken envs); classifies every `juniper-*` editable as `FRESH` / `WORKTREE_PINNED` (under a `worktrees` path) / `ORPHANED` (missing). `*-DEPRECATED` skipped by default; exit 1 on ORPHANED; `--json`; `--fix` re-points orphans to their canonical repo (`--dry-run` previews).
- `util/ad-hoc/` -- Home for single-use / temporary / unfinished scripts. See `util/ad-hoc/README.md` for file-header conventions and graduation lifecycle. `/tmp/` is prohibited for script source files per the [Script placement](#script-placement-mandatory) rule.
- Dependency-documentation generator now lives in [`juniper-ci-tools/`](juniper-ci-tools/) and is published to PyPI as `juniper-ci-tools` (Wave 4 of the dep-docs migration plan; install with `pip install juniper-ci-tools` and invoke via `juniper-generate-dep-docs`). The legacy `util/generate_dep_docs.sh` was deleted in juniper-ml#298.
- `util/juniper_plant_all.bash` -- Starts all Juniper ecosystem services. `JUNIPER_CASCOR_HOST` defaults to `localhost` and `JUNIPER_CASCOR_PORT` defaults to `8201`; both can be overridden via the environment (e.g. `JUNIPER_CASCOR_HOST=remote.example.com JUNIPER_CASCOR_PORT=8201 util/juniper_plant_all.bash`).
- `util/juniper_chop_all.bash` -- Stops all Juniper ecosystem services
- `util/get_cascor_*.bash` -- Cascor REST API query utilities (status, metrics, history, network, topology). These helpers read legacy `CASCOR_HOST` and `CASCOR_PORT` environment variables (with `localhost` / `8201` defaults). Do not confuse them with the `JUNIPER_CASCOR_*` variables used by `util/juniper_plant_all.bash`.

### Tests

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- Doc-link validator regression tests live in [`juniper-doc-tools/tests/`](juniper-doc-tools/tests/) (Wave 4 of the doc-link migration; exercised by the dedicated `CI -- juniper-doc-tools` workflow).
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling
- `tests/test_worktree_sweep_scripts.py` -- Tests for `util/ad-hoc/worktree_sweep_*.bash`: survey/apply row compatibility, `SAFE`-only removal, and unknown-repo skips
- `tests/test_reap_pytest_orphans.py` -- Tests for `util/reap_pytest_orphans.bash` dry-run, live-parent safety, orphan detection, and isolated kill invocation
- `tests/test_requirements_drift_check.py` -- Tests for `util/requirements_drift_check.py`: structural range validation, BAD_PATH / BAD_RANGE classification, `--ecosystem-root` rewriting, CLI exit codes, JSON output
- `tests/test_editable_install_drift_check.py` -- Tests for `util/editable_install_drift_check.py`: FRESH / WORKTREE_PINNED / ORPHANED classification, `*-DEPRECATED` env exclusion, `--env` filtering, dedup across interpreter trees, CLI exit codes (0/1/2), JSON output, and `--fix --dry-run` canonical-source resolution (synthetic conda-dir fixture; no real pip)
- `tests/test_workflow_script_paths.py` -- Lint test: every `python <path.py>` / `bash <path.bash>` invocation in `.github/workflows/*.yml` must reference a path that exists in the repo. Cross-repo paths (`juniper-X/...`) are skipped as runtime-resolved. Catches the failure class that broke 3 juniper-X CIs on 2026-05-18.
- `tests/test_doc_tools_drift.py` -- Lint test (plan §5.1) for `juniper-doc-tools` pins. Extracts the `juniper-doc-tools>=X,<Y` pin from juniper-ml's own workflows and each cloned consumer repo's `ci.yml`, then asserts the range still admits the current version (read from `juniper-doc-tools/pyproject.toml`). Soft-warns on pins more than 2 minors behind; hard-fails when the upper bound excludes current.
- `tests/test_pyproject_extras.py` -- Lint test pinning the `[project.optional-dependencies]` surface (`clients`, `worker`, `servers`, `tools`, `doc-tools`, `all`). Asserts the exact set of extras, the exact membership of each, that `[all]` aggregates every non-alias extra exactly once, and that `[project].version` is semver-ish. Added pre-0.5.0 after juniper-ml#295 introduced `[servers]` + `[tools]` without regression coverage; any future edit to extras must update the lint contract in the same PR.
  - juniper-ml's own pin check runs every PR; the cross-repo assertion auto-skips when siblings aren't on disk and additionally skips local runs by default. Set `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` to opt in locally.
- `tests/test_template_library_drift.py` -- Lint test enforcing manifest <-> template consistency for the custom-agent template library (`prompts/templates/`): every registered template exists and every template is registered; each follows the canonical section skeleton in order; every `{{placeholder}}` matches the systematic convention; the `generic` fallback always matches.
  - The **sole gate** for the library because `prompts/**` is excluded from all pre-commit hooks, so it must stay wired into `ci.yml`. Design-of-record §5.4/§9.
- `tests/test_ci_tools_drift.py` -- Lint test (dep-docs plan §5.1) for `juniper-ci-tools` pins. Mirrors `test_doc_tools_drift.py`: walks juniper-ml's own workflows (`ci.yml`, `lockfile-update.yml`, `docs-full-check.yml`) plus each cloned consumer repo's `ci.yml`, extracts the `juniper-ci-tools>=X,<Y` pin, and asserts the range still admits the current version (read from `juniper-ci-tools/pyproject.toml`). Same skip semantics and `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` override as the doc-tools sibling.
- `tests/test_agents_md_version_drift.py` -- Lint test pinning `AGENTS.md`'s `**Version**:` header to `pyproject.toml`'s `[project].version`. Added after juniper-ml#295 bumped pyproject 0.4.1→0.5.0 but left AGENTS.md at 0.4.0 for ~6 days (fixed in juniper-ml#304); this lint makes the drift impossible to ship. Intentionally portable: auto-locates the repo root, so the module can be dropped into any Juniper repo's `tests/` (skips loudly if AGENTS.md has no canonical header).
- `tests/test_agents_md_header_schema.py` -- Lint pinning `AGENTS.md`'s canonical header schema. Six required fields in this relative order: `**Project**`, `**Repository**`, `**Author**`, `**License**`, `**Version**`, `**Last Updated**`. Extras (e.g. `**Python**:`) may be interleaved freely. Validates each value non-empty and `**Last Updated**` is `YYYY-MM-DD`. Currency of the date is enforced by `.github/workflows/agents-md-touch-up.yml`. Portable (self-locating).
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

### CI/CD Workflows

- `.github/workflows/ci.yml` -- Main CI pipeline: pre-commit hooks, unit tests, package build, doc validation, security audit, dependency docs
- `.github/workflows/publish.yml` -- PyPI publishing: TestPyPI with install verification, then PyPI (OIDC trusted publishing)
- `.github/workflows/docs-full-check.yml` -- Weekly full documentation link validation including cross-repo checks
- `.github/workflows/security-scan.yml` -- Weekly pip-audit dependency vulnerability scanning
- `.github/workflows/claude.yml` -- Claude Code action for issue/PR automation (@claude mentions)
- `.github/workflows/agents-md-touch-up.yml` -- Auto-bumps `AGENTS.md`'s `**Last Updated**:` field to today's UTC date on every PR push that touches `AGENTS.md`. Idempotent (no-op when the date is already current); commits with `github-actions[bot]` authorship and `[skip ci]` so the bump itself does not re-trigger workflows. Companion to `tests/test_agents_md_header_schema.py`.

### Configuration

- `.pre-commit-config.yaml` -- Pre-commit hooks: flake8, bandit, shellcheck, markdownlint, yamllint, SOPS env check
- `.markdownlint.yaml` -- Markdown linting rules (line length: 512, ol-prefix disabled)
- `.sops.yaml` -- SOPS encryption configuration for `.env` and `.env.secrets` using age key
- `.serena/project.yml` -- Serena code agent integration (project: juniper_ml, language: python)
- `.gitattributes` -- Git LFS tracking for image files (jpg, png, ico, xcf, svg, etc.)
- `.github/CODEOWNERS` -- Code ownership: @pcalnon for all files
- `.github/dependabot.yml` -- Automated dependency updates: pip (weekly) and github-actions (weekly)

## CI/CD Pipelines

### Main CI (`ci.yml`)

Triggered on push to `main`/`develop`/`feature/**`/`fix/**` branches and PRs to `main`/`develop`.

Jobs:

1. **pre-commit** -- Runs all pre-commit hooks (flake8, bandit, shellcheck, yamllint, markdownlint)
2. **tests** -- Python unittest (`test_wake_the_claude.py`, `test_workflow_script_paths.py`, etc.) and bash regression tests
3. **build** -- Package build, twine validation, extras metadata verification
4. **docs** -- Documentation link validation (`--cross-repo skip`)
5. **security** -- pip-audit for dependency vulnerabilities
6. **dependency-docs** -- Generates dependency documentation via the `juniper-generate-dep-docs` console script from the PyPI-published `juniper-ci-tools>=0.1.0,<0.2.0` package (replaces the legacy `util/generate_dep_docs.sh` deleted in juniper-ml#298)
7. **required-checks** -- Quality gate enforcing all checks must pass

### Publishing (`publish.yml`)

Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first (with install verification), then PyPI.

### Documentation Full Check (`docs-full-check.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Clones all Juniper ecosystem repos and runs full cross-repo documentation link validation.

### Security Scan (`security-scan.yml`)

Weekly schedule (Monday 06:00 UTC) and manual dispatch. Runs `pip-audit --strict --desc on` for dependency vulnerability scanning.

### Claude Code Action (`claude.yml`)

Triggered by issue/PR comments and events mentioning @claude. Uses `anthropics/claude-code-action` for automated issue/PR assistance.

## Pre-commit Hooks

Setup:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Configured hooks (`.pre-commit-config.yaml`):

| Hook Group | Version | Scope | Purpose |
|------------|---------|-------|---------|
| pre-commit-hooks | v4.6.0 | All files | YAML/TOML/JSON check, EOF fixer, trailing whitespace, merge conflicts, large files, AST check, debug statements, private keys |
| flake8 | 7.1.1 | `scripts/`, `tests/` `.py` | Python linting (max-line-length: 512) with bugbear, comprehensions, simplify |
| bandit | 1.9.4 | `scripts/`, `tests/` `.py` | Python security scanning |
| shellcheck | v0.10.0.1 | `.sh`, `.bash` | Shell script linting (severity: warning) |
| markdownlint | v0.42.0 | `.md` (excl. CHANGELOG, notes/, docs/, prompts/) | Markdown linting with auto-fix |
| yamllint | v1.35.1 | YAML files | YAML linting (relaxed mode) |
| no-unencrypted-env | local | `.env`, `.env.secrets` | Blocks unencrypted env files from commit |

## Secrets Management (SOPS)

The repository uses [SOPS](https://github.com/getsops/sops) with age encryption for secrets:

- **Encrypted files**: `.env`, `.env.secrets` (matched by `.sops.yaml`)
- **Encryption key**: age key configured in `.sops.yaml`
- **Existing encrypted file**: `.env.enc`
- **Pre-commit protection**: The `no-unencrypted-env` hook blocks unencrypted `.env` files from being committed
- **Usage guide**: `notes/SOPS_USAGE_GUIDE.md`

## Ecosystem Context

This repo is part of the broader Juniper ecosystem. See the parent directory's `CLAUDE.md` at `/home/pcalnon/Development/python/Juniper/CLAUDE.md` for the full project map, dependency graph, shared conventions, and conda environment details.

### Dependency extras reference

| Extra | Packages |
|-------|----------|
| `clients` | `juniper-data-client>=0.4.1`, `juniper-cascor-client>=0.5.0` |
| `worker` | `juniper-cascor-worker>=0.4.0` |
| `servers` | `juniper-canopy>=0.5.0`, `juniper-cascor>=0.5.0`, `juniper-data>=0.6.0` |
| `tools` | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.2.0`, `juniper-observability>=0.2.0`, `juniper-service-core>=0.2.0,<0.3.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`) |
| `recurrence` | `juniper-recurrence-model>=0.1.0,<0.2.0`, `juniper-recurrence>=0.1.0,<0.2.0`, `juniper-recurrence-client>=0.1.0,<0.2.0` |
| `all` | All of the above |

## Conventions

- Python >=3.12 required (classifiers include 3.12, 3.13, 3.14)
- Package name on PyPI: `juniper-ml`
- Import name: none (meta-package, no importable modules)
- Version tracked in `pyproject.toml` under `[project].version`
- Line length: 512 for all linters (flake8, markdownlint)
- Shell scripts use bash with `shellcheck` compliance
- Markdown files use `.markdownlint.yaml` configuration

### Script placement (mandatory)

Utility, single-use, temporary, and unfinished scripts MUST be created under `util/`:

| Script type                                    | Destination               |
| ---------------------------------------------- | ------------------------- |
| Permanent utility, regularly used              | `util/<name>.{py,bash}`   |
| Single-use, temporary, ad-hoc, or unfinished   | `util/ad-hoc/<name>.{py,bash}` |

**`/tmp/` is prohibited** as the home for any script that produces, modifies, or analyzes repository content. `/tmp/` is reaped when sessions / sandboxes / containers end, and scripts placed there are lost. `/tmp/` remains acceptable as a scratch *workspace* for intermediate artifacts that the script itself creates and reads (e.g., `uv pip compile -o /tmp/lock && mv /tmp/lock requirements.lock`) — the prohibition is on script *source files*, not on transient data.

**Incident motivating this rule**: `phase4_consolidate.py` and `v2_citation_validate.py` were authored in `/tmp/` across the v1-v4 requirements snapshot effort and are now irrecoverable. See [`notes/REQUIREMENTS_NEXT_STEPS.md` §7](notes/REQUIREMENTS_NEXT_STEPS.md#7-stale--drift-detection) and [plan-doc §12](notes/REQUIREMENTS_IDENTIFICATION_PLAN_2026-05-11.md#12-open-issues--questions-discovered-during-execution).

See [`util/ad-hoc/README.md`](util/ad-hoc/README.md) for the ad-hoc-script convention (file-header requirements, when to graduate to `util/` proper).

---

## Pull Request Conventions

### Requirements (JR-ID) cross-references

PR descriptions on juniper-ml SHOULD include a `## Requirements` section that lists the [`JR-<REPO>-<AREA>-<NNN>` IDs](notes/REQUIREMENTS_INDEX.md) this PR touches. The repository-level [`.github/pull_request_template.md`](.github/pull_request_template.md) pre-fills the section; delete it only if no tracked requirement applies.

**Verb conventions** (from [`REQUIREMENTS_NEXT_STEPS.md` §4](notes/REQUIREMENTS_NEXT_STEPS.md#4-jr-id-references-in-prs)):

| Verb                    | Meaning                                                                            | Refresh-time effect       |
| ----------------------- | ---------------------------------------------------------------------------------- | ------------------------- |
| `Closes JR-*`           | This PR fully satisfies the requirement.                                           | Status → `shipped`.       |
| `Partially closes JR-*` | This PR satisfies some of the requirement; describe which parts in the same line. | Status unchanged.         |
| `References JR-*`       | This PR is informed by but does not change the requirement.                        | Status unchanged.         |
| `Supersedes JR-*`       | This PR's design replaces an earlier requirement.                                  | Old entry → `superseded`. |

**Looking up an ID**:

- Browse [`notes/REQUIREMENTS_INDEX.md`](notes/REQUIREMENTS_INDEX.md) or [`notes/requirements/by-area/<CODE>.md`](notes/requirements/) for human-readable views.
- For programmatic queries, see [`REQUIREMENTS_NEXT_STEPS.md` §3 recipes](notes/REQUIREMENTS_NEXT_STEPS.md#3-snapshot-consumption-recipes).
- Never `grep` `id_assignments.yaml` for content — briefs there are truncated.

**Scope**: Apply the convention in PR *descriptions* only — not commit messages. CI lint validating IDs is deferred until the convention has organic uptake (see [`REQUIREMENTS_NEXT_STEPS.md` §6](notes/REQUIREMENTS_NEXT_STEPS.md#6-ci-lint-validating-jr-id-references)).

### Other PR description conventions

For larger / cross-cutting PRs, the long-form template at [`notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md`](notes/templates/TEMPLATE_PULL_REQUEST_DESCRIPTION.md) covers Summary, Context, Priority table, Keep-a-Changelog grouping, Impact/SemVer, Testing, and rollback plans. The repo-level `.github/pull_request_template.md` is the lightweight default; the long-form template is opt-in for PRs that warrant it.

---

## Worktree Procedures (Mandatory -- Task Isolation)

> **OPERATING INSTRUCTION**: All feature, bugfix, and task work SHOULD use git worktrees for isolation. Worktrees keep the main working directory on the default branch while task work proceeds in a separate checkout.

### What This Is

Git worktrees allow multiple branches of a repository to be checked out simultaneously in separate directories. For the Juniper ecosystem, all worktrees are centralized in **`/home/pcalnon/Development/python/Juniper/worktrees/`** using a standardized naming convention.

The full setup and cleanup procedures are defined in:

- **`notes/WORKTREE_SETUP_PROCEDURE.md`** -- Creating a worktree for a new task
- **`notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`** -- Merging, removing, and pushing after task completion (V2 -- fixes CWD-trap bug)

Read the appropriate file when starting or completing a task.

### Worktree Directory Naming

Format: `<repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>`

Example: `juniper-ml--chore--update-deps--20260225-1430--519bda91`

- Slashes in branch names are replaced with `--`
- All worktrees reside in `/home/pcalnon/Development/python/Juniper/worktrees/`

### When to Use Worktrees

| Scenario | Use Worktree? |
| -------- | ------------- |
| Feature development (new feature branch) | **Yes** |
| Bug fix requiring a dedicated branch | **Yes** |
| Quick single-file documentation fix on main | No |
| Exploratory work that may be discarded | **Yes** |
| Hotfix requiring immediate merge | **Yes** |

### Quick Reference

**Setup** (full procedure in `notes/WORKTREE_SETUP_PROCEDURE.md`):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git checkout main && git pull origin main
BRANCH_NAME="chore/my-task"
git branch "$BRANCH_NAME" main
REPO_NAME=$(basename "$(pwd)")
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's|/|--|g')
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
```

**Cleanup** (full procedure in `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`):

```bash
# Phase 1: Push current work
cd "$OLD_WORKTREE_DIR" && git push origin "$OLD_BRANCH"
# Phase 2: Create new worktree BEFORE removing old (prevents CWD-trap)
git fetch origin
git worktree add "$NEW_WORKTREE_DIR" -b "$NEW_BRANCH" origin/main
cd "$NEW_WORKTREE_DIR"
# Phase 3: Create PR (do NOT merge directly to main)
gh pr create --base main --head "$OLD_BRANCH" --title "<title>" --body "<body>"
# Phase 4: Cleanup
git worktree remove "$OLD_WORKTREE_DIR"
git branch -d "$OLD_BRANCH"
git worktree prune
```

**Automated cleanup** (via script):

```bash
util/worktree_cleanup.bash \
  --old-worktree "$OLD_WORKTREE_DIR" \
  --old-branch "$OLD_BRANCH" \
  --parent-branch main
```

### Rules

- **Centralized location**: All worktrees go in `/home/pcalnon/Development/python/Juniper/worktrees/`. Never create worktrees inside the repo directory.
- **Clean before you start**: Ensure the main working directory is clean before creating a worktree.
- **Push before you merge**: Always push the working branch to remote before merging (backup).
- **Prune after cleanup**: Run `git worktree prune` after removing a worktree to clean metadata.
- **Do not leave stale worktrees**: Clean up worktrees promptly after merging.

---

## Thread Handoff (Mandatory -- Replaces Thread Compaction)

> **CRITICAL OPERATING INSTRUCTION**: Thread handoff MUST be performed instead of
> thread compaction. This section defines mandatory behavior that overrides Claude
> Code's default compaction process.

### What This Is

When a long-running conversation approaches context limits, Claude Code normally
performs **thread compaction** -- summarizing prior context to free token capacity.
This introduces information loss. Instead, Claude Code instances working on this
project MUST perform a **proactive thread handoff**: transferring a curated,
high-signal summary to a fresh thread with full context capacity.

The full handoff protocol is defined in **`notes/THREAD_HANDOFF_PROCEDURE.md`**.
Read that file when a handoff is triggered.

### When to Trigger a Handoff

**Automatic trigger (pre-compaction threshold):** Initiate a thread handoff when
token utilization reaches **95% to 99%** of the level at which thread compaction
would normally be triggered. This means the handoff fires when you are within
**1% to 5%** of the compaction threshold, ensuring the handoff completes before
compaction would occur.

Concretely:

- If compaction would trigger at N% context utilization, begin handoff at
  (N - 5)% to (N - 1)%.
- **Self-assessment rule**: At each turn where you are performing multi-step work,
  assess whether you are approaching the compaction threshold. If you estimate you
  are within 5% of it, begin the handoff protocol immediately.
- When the system compresses prior messages or you receive a context compression
  notification, treat this as a signal that handoff should have already occurred --
  immediately initiate one.

**Additional triggers** (from `notes/THREAD_HANDOFF_PROCEDURE.md`):

| Condition                   | Indicator                                            |
| --------------------------- | ---------------------------------------------------- |
| **Context saturation**      | 15+ tool calls or 5+ files edited                    |
| **Phase boundary**          | Logical phase of work is complete                    |
| **Degraded recall**         | Re-reading files or re-asking resolved questions     |
| **Multi-file transition**   | Moving between major concerns                        |
| **User request**            | User says "hand off", "new thread", or similar       |

**Do NOT handoff** when:

- Task is nearly complete (< 2 remaining steps)
- Current thread is still sharp and producing correct output
- Work is tightly coupled and splitting would lose in-flight state

### How to Execute a Handoff

1. **Checkpoint**: Inventory what was done, what remains, what was discovered,
   and what files are in play
2. **Compose the handoff goal**: Write a concise, actionable summary
   (see templates in `notes/THREAD_HANDOFF_PROCEDURE.md`)
3. **Present to user**: Output the handoff goal and recommend starting a new
   thread with that goal as the initial prompt
4. **Include verification commands**: Specify how the new thread should verify
   its starting state
5. **State git status**: Mention branch, staged files, and uncommitted work

### Rules

- **This is not optional.** Every Claude Code instance on this project must
  follow these rules.
- **Handoff early, not late.** A handoff at 70% context is better than
  compaction at 95%.
- **Do not duplicate CLAUDE.md content** in the handoff goal.
- **Be specific**: Include file paths, decisions made, and verification status.
