# CLAUDE.md

**Version**: 0.4.0

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
pip install -e ".[all]"        # everything

# Run all tests
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_check_doc_links.py
python3 -m unittest -v tests/test_worktree_cleanup.py
bash scripts/test_resume_file_safety.bash

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links
python util/check_doc_links.py --exclude templates --exclude history

# Validate documentation links (including cross-repo)
python util/check_doc_links.py --exclude templates --exclude history --cross-repo check
```

## Publishing

Releases are published via GitHub Actions (`.github/workflows/publish.yml`). The workflow is triggered by a GitHub release event and publishes first to TestPyPI (with install verification), then to PyPI. Both environments use trusted publishing (OIDC, no API tokens).

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
│   ├── DEVELOPER_CHEATSHEET_JUNIPER-ML.md# Quick-reference card for development tasks
│   └── DEVELOPER_CHEATSHEET-ORIGINAL.md  # DEPRECATED: monolithic cross-project reference
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
│
├── scripts/                   # Claude Code launcher and test scripts
│   ├── wake_the_claude.bash              # Core launcher: flag parsing, session persistence, resume
│   ├── claude_interactive.bash           # Interactive Claude Code agent launcher
│   ├── default_interactive_session_claude_code.bash  # Config template for interactive sessions
│   ├── activate_conda_env.bash           # Conda environment management
│   ├── resume_session.bash               # Session resume convenience wrapper
│   ├── check_doc_links.py               # Symlink -> ../util/check_doc_links.py
│   ├── test.bash                         # End-to-end test harness for launcher flows
│   ├── test_resume_file_safety.bash      # Regression: invalid --resume input safety
│   ├── test_prompt-*.md                  # Test prompt files for launcher testing
│   ├── sessions/                         # Session ID storage (.gitkeep)
│   └── backups/                          # Backup copies of older script versions
│
├── tests/                     # Regression test suites (Python unittest)
│   ├── test_wake_the_claude.py           # Launcher script regression (1470 lines)
│   ├── test_check_doc_links.py           # Doc link validator regression (283 lines)
│   └── test_worktree_cleanup.py          # Worktree cleanup script tests (225 lines)
│
└── util/                      # Utility scripts and tools
    ├── check_doc_links.py                # Doc link validator (v0.6.0) — used in CI/CD
    ├── generate_dep_docs.sh              # Generates dependency docs for CI
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
    ├── get_cascor_dkdk.bash              # Cascor query (incomplete)
    ├── kill_all_pythons.bash             # Emergency Python process terminator
    ├── search_file_in_all_repos_and_worktrees.bash   # Cross-repo file search
    └── global_text_replace.bash          # Batch sed find-and-replace
```

## Key Files

### Package and Metadata

- `pyproject.toml` -- Package metadata, version (`0.4.0`), and optional dependency groups (`clients`, `worker`, `all`)
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

- `util/worktree_cleanup.bash` -- Automated worktree cleanup with CWD-safe session continuity (V2 procedure). Supports `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`.
- `util/check_doc_links.py` -- Documentation link validator (v0.6.0) for internal markdown links; used in CI/CD pipelines
- `util/generate_dep_docs.sh` -- Generates `requirements_ci.txt` and `conda_environment_ci.yaml` for CI
- `util/juniper_plant_all.bash` -- Starts all Juniper ecosystem services
- `util/juniper_chop_all.bash` -- Stops all Juniper ecosystem services
- `util/get_cascor_*.bash` -- Cascor REST API query utilities (status, metrics, history, network, topology)

### Tests

- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`
- `tests/test_check_doc_links.py` -- Regression tests for `util/check_doc_links.py` documentation link validation
- `tests/test_worktree_cleanup.py` -- Tests for `util/worktree_cleanup.bash` argument parsing, dry-run, and error handling
- `scripts/test.bash` -- Manual end-to-end harness for session create/resume launcher flows
- `scripts/test_resume_file_safety.bash` -- Regression script ensuring invalid `--resume <file.txt>` input does not delete the source file

### CI/CD Workflows

- `.github/workflows/ci.yml` -- Main CI pipeline: pre-commit hooks, unit tests, package build, doc validation, security audit, dependency docs
- `.github/workflows/publish.yml` -- PyPI publishing: TestPyPI with install verification, then PyPI (OIDC trusted publishing)
- `.github/workflows/docs-full-check.yml` -- Weekly full documentation link validation including cross-repo checks
- `.github/workflows/security-scan.yml` -- Weekly pip-audit dependency vulnerability scanning
- `.github/workflows/claude.yml` -- Claude Code action for issue/PR automation (@claude mentions)

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
2. **tests** -- Python unittest (`test_wake_the_claude.py`, `test_check_doc_links.py`) and bash regression tests
3. **build** -- Package build, twine validation, extras metadata verification
4. **docs** -- Documentation link validation (`--cross-repo skip`)
5. **security** -- pip-audit for dependency vulnerabilities
6. **dependency-docs** -- Generates dependency documentation via `util/generate_dep_docs.sh`
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
| `clients` | `juniper-data-client>=0.4.0`, `juniper-cascor-client>=0.3.0` |
| `worker` | `juniper-cascor-worker>=0.3.0` |
| `all` | All of the above |

## Conventions

- Python >=3.12 required (classifiers include 3.12, 3.13, 3.14)
- Package name on PyPI: `juniper-ml`
- Import name: none (meta-package, no importable modules)
- Version tracked in `pyproject.toml` under `[project].version`
- Line length: 512 for all linters (flake8, markdownlint)
- Shell scripts use bash with `shellcheck` compliance
- Markdown files use `.markdownlint.yaml` configuration

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
