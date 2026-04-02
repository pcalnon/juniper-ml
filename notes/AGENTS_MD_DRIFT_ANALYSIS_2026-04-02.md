# AGENTS.md Drift Analysis

**Project**: Juniper / juniper-ml
**Document Version**: 1.0.0
**Date**: 2026-04-02
**Author**: Claude Code (Opus 4.6)
**Scope**: Full audit of AGENTS.md v0.2.0 against codebase at pyproject.toml v0.3.0

---

## Executive Summary

The juniper-ml AGENTS.md file (v0.2.0) has significant drift from the current codebase state (v0.3.0). The repository has undergone substantial growth since the AGENTS.md was last updated, adding an entire `util/` directory with 22 scripts, expanding CI/CD from 1 to 5 GitHub Actions workflows, adding a `docs/` directory with 5 documentation files, adding 2 new test files, and introducing multiple configuration systems (SOPS encryption, Serena integration, pre-commit hooks, Git LFS, dependabot). The AGENTS.md must be comprehensively updated to reflect all of these changes.

**Drift severity**: **High** — The document omits multiple entire directories, misnames files that have been moved or renamed, and lacks documentation of critical operational infrastructure (CI/CD, secrets management, pre-commit hooks).

---

## 1. Version Mismatch

| Item | AGENTS.md States | Actual |
|------|-----------------|--------|
| AGENTS.md version | 0.2.0 | Should be 0.3.0 (matching pyproject.toml) |
| pyproject.toml version | Not explicitly stated | 0.3.0 |
| Python classifiers | Not mentioned | 3.12, 3.13, 3.14 |

**Impact**: The AGENTS.md version number is out of sync with the package version. The AGENTS.md should be updated to v0.3.0 to match the current release.

---

## 2. File Renames and Relocations

### 2.1 `cly` Renamed to `claudey`

**AGENTS.md states** (line 46):
> `cly` — Repo-root shortcut for the default interactive launcher

**Actual state**: `cly` does not exist. It has been renamed to `claudey`, which is a symlink to `scripts/claude_interactive.bash` (not to `scripts/default_interactive_session_claude_code.bash` as the old name implied).

### 2.2 `scripts/worktree_cleanup.bash` Relocated to `util/worktree_cleanup.bash`

**AGENTS.md states** (line 49):
> `scripts/worktree_cleanup.bash` — Automated worktree cleanup with CWD-safe session continuity (V2 procedure)

**Actual state**: `scripts/worktree_cleanup.bash` does not exist. The worktree cleanup script is now at `util/worktree_cleanup.bash` (v1.0.0, with full flag support: `--old-worktree`, `--old-branch`, `--parent-branch`, `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--dry-run`).

---

## 3. Undocumented `util/` Directory (22 Files)

The entire `util/` directory is absent from AGENTS.md. This directory contains the following categories of scripts:

### 3.1 Worktree Management Suite (6 scripts)

| File | Purpose |
|------|---------|
| `worktree_cleanup.bash` | V2 cleanup orchestrator — push, new worktree, PR, remove old, prune (CWD-trap safe) |
| `worktree_new.bash` | Creates new git worktree under `.claude/worktrees/` |
| `worktree_activate.bash` | Bash helper for `.bashrc` to activate worktrees (provides `activate_new_worktree()`) |
| `worktree_close.bash` | Validates and removes a git worktree, deletes branch, prunes |
| `worktree_wipeout.bash` | Bulk removal of worktrees matching a pattern (default: "fix--connect-canopy-cascor") |
| `remove_stale_worktrees.bash` | Iterates and removes all worktrees matching "worktrees" pattern |

### 3.2 Cascor Service Query Utilities (7 scripts)

| File | Endpoint | Purpose |
|------|----------|---------|
| `get_cascor_status.bash` | `GET /v1/training/status` | Training system status |
| `get_cascor_metrics.bash` | `GET /v1/metrics` | Current metrics snapshot |
| `get_cascor_history.bash` | `GET /v1/metrics/history?count=10` | Last 10 metrics records |
| `get_cascor_history-plus.bash` | `GET /v1/metrics/history?count=100` | Last 100 metrics with count summary |
| `get_cascor_network.bash` | `GET /v1/network` | Network topology |
| `get_cascor_topology.bash` | `GET /v1/network/topology` | Detailed network topology |
| `get_cascor_dkdk.bash` | (incomplete) | Appears truncated/incomplete |

All query `http://localhost:8201/v1/` and format JSON output.

### 3.3 Juniper Ecosystem Management (2 scripts)

| File | Purpose |
|------|---------|
| `juniper_plant_all.bash` | Starts/initializes all Juniper ecosystem services |
| `juniper_chop_all.bash` | Stops all Juniper ecosystem services; references JuniperProject.pid |

### 3.4 Git Maintenance (2 scripts)

| File | Purpose |
|------|---------|
| `prune_git_branches_without_working_dirs.bash` | Removes branches with "worktree-" prefix that lack corresponding working directories |
| `cleanup_open_worktrees.bash` | Removes all active worktrees via `git worktree list` |

### 3.5 Documentation and Validation (2 scripts)

| File | Purpose |
|------|---------|
| `check_doc_links.py` | Python v0.6.0 — Validates internal markdown links (relative files, anchors); skips external URLs; handles cross-repo links with regex classification. Used in CI/CD. |
| `generate_dep_docs.sh` | Generates dependency documentation: `requirements_ci.txt` (pip freeze) and `conda_environment_ci.yaml` (conda list). Preserves existing files with timestamped backups. |

### 3.6 System Utilities (3 scripts)

| File | Purpose |
|------|---------|
| `kill_all_pythons.bash` | Emergency Python process terminator (`sudo kill -9`) |
| `search_file_in_all_repos_and_worktrees.bash` | Cross-repository file search across all Juniper repos and their worktrees |
| `global_text_replace.bash` | Batch find-and-replace across codebase using sed (template script) |

---

## 4. Undocumented Scripts in `scripts/`

### 4.1 New Scripts

| File | Purpose |
|------|---------|
| `claude_interactive.bash` | Main interactive Claude Code agent launcher (target of `claudey` symlink) |
| `activate_conda_env.bash` | Initializes and manages Conda environment activation/deactivation |
| `resume_session.bash` | Convenience wrapper to resume a specific Claude Code session |

### 4.2 New Subdirectories

| Directory | Purpose |
|-----------|---------|
| `scripts/sessions/` | Session storage directory (contains `.gitkeep` placeholder) |
| `scripts/backups/` | Backup copies of older script versions (activate_conda_env.bash, worktree_new.bash, experimental scripts) |

### 4.3 Symlink

| File | Target |
|------|--------|
| `scripts/check_doc_links.py` | `../util/check_doc_links.py` (symlink to util copy) |

---

## 5. Undocumented Test Files

AGENTS.md mentions only 2 test artifacts:

- `tests/test_wake_the_claude.py` (documented)
- `scripts/test_resume_file_safety.bash` (documented)

**Missing from AGENTS.md**:

| File | Lines | Framework | Purpose |
|------|-------|-----------|---------|
| `tests/test_check_doc_links.py` | 283 | unittest | Regression tests for `util/check_doc_links.py` (code block handling, link validation) |
| `tests/test_worktree_cleanup.py` | 225 | unittest | Tests for `util/worktree_cleanup.bash` (argument parsing, dry-run, error handling) |

**Test command section is incomplete**. Current AGENTS.md only shows:

```bash
python3 -m unittest -v tests/test_wake_the_claude.py
bash scripts/test_resume_file_safety.bash
```

Should also include:

```bash
python3 -m unittest -v tests/test_check_doc_links.py
python3 -m unittest -v tests/test_worktree_cleanup.py
```

---

## 6. Undocumented `docs/` Directory (5 Files)

AGENTS.md makes no mention of the `docs/` directory. It contains:

| File | Version | Purpose |
|------|---------|---------|
| `DOCUMENTATION_OVERVIEW.md` | 0.2.1 | Navigation guide and index for all juniper-ml documentation |
| `QUICK_START.md` | 0.2.0 | Installation and verification guide |
| `REFERENCE.md` | 0.2.0 | Technical reference: extras, compatibility matrix, service ports, env vars |
| `DEVELOPER_CHEATSHEET_JUNIPER-ML.md` | 1.0.1 | Quick-reference card for development tasks, Claude Code, worktrees, CI/CD |
| `DEVELOPER_CHEATSHEET-ORIGINAL.md` | 1.3.0 | **DEPRECATED** — Monolithic cross-project cheatsheet (retained for historical reference) |

---

## 7. CI/CD Expansion (4 Undocumented Workflows)

AGENTS.md only documents `.github/workflows/publish.yml`. The repository now has **5 workflows**:

| Workflow | Trigger | Purpose | Documented? |
|----------|---------|---------|-------------|
| `publish.yml` | Release event | PyPI publishing (TestPyPI + PyPI, OIDC) | **Yes** |
| `ci.yml` | Push/PR to main, develop, feature/**, fix/** | Main CI: pre-commit, tests, build, docs, security, dependency-docs | **No** |
| `docs-full-check.yml` | Weekly (Mon 06:00 UTC), manual | Full documentation link validation including cross-repo | **No** |
| `security-scan.yml` | Weekly (Mon 06:00 UTC), manual | pip-audit dependency vulnerability scanning | **No** |
| `claude.yml` | Issue/PR comments mentioning @claude | Claude Code action for issue/PR automation | **No** |

---

## 8. Undocumented Configuration Files

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Pre-commit hooks: flake8, bandit, shellcheck, markdownlint, yamllint, SOPS env check |
| `.markdownlint.yaml` | Markdown linting config (line length 512, ol-prefix disabled, siblings-only headings) |
| `.sops.yaml` | SOPS encryption configuration for `.env` and `.env.secrets` files using age key |
| `.env.enc` | Encrypted environment variables (SOPS-encrypted) |
| `.serena/project.yml` | Serena code agent integration config (project: juniper_ml, language: python) |
| `.gitattributes` | Git LFS tracking for image files (jpg, png, ico, xcf, svg, etc.) |
| `MANIFEST.in` | Source distribution includes (`.gitignore`) |
| `CHANGELOG.md` | Version history in Keep a Changelog format (latest: v0.3.0 on 2026-03-12) |
| `.github/CODEOWNERS` | Code ownership: @pcalnon for all files |
| `.github/dependabot.yml` | Automated dependency updates: pip (weekly) and github-actions (weekly) |

---

## 9. Undocumented Ecosystem Files

| File/Directory | Purpose |
|----------------|---------|
| `JuniperProject.pid` | PID file for Juniper ecosystem service management |
| `juniper-project-pids.txt` | PID tracking for all running Juniper services |
| `images/` | Project branding: logos (versions 0-9 in PNG/XCF/ICO), tree reference photos |
| `resources/` | External resources (imager_2.0.6_amd64.AppImage) |
| `logs/` | Log output directory (with `.gitkeep`) |

---

## 10. Undocumented `notes/` Subdirectory Structure

AGENTS.md references `notes/WORKTREE_SETUP_PROCEDURE.md`, `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`, and `notes/THREAD_HANDOFF_PROCEDURE.md` but does not document the full notes directory structure:

| Subdirectory | Contents | Purpose |
|--------------|----------|---------|
| `notes/backups/` | 18 files | Backup analysis/plan documents (cascor concurrency, demo training errors, decision boundary fixes) |
| `notes/concurrency/` | 4 files | Concurrency-related thread handoff and implementation delta analysis |
| `notes/development/` | 6 files | Dataset display bug analysis and development plans |
| `notes/documentation/` | 4 files | Documentation audit plans and disposition reports |
| `notes/history/` | 22 files | Historical plans, procedures, and migration plans (worktree cleanup V1, security remediation, PyPI deployment) |
| `notes/proposals/` | 10 files | Research proposals (phantom training phase, candidate quality decay, spiral complexity, convergence timing, etc.) |
| `notes/pull_requests/` | 7 files | PR description archives for key pull requests |
| `notes/templates/` | 5 files | Document templates (development roadmap, issue tracking, PR description, release notes, security release notes) |

---

## 11. Missing `prompts/thread-handoff_automated-prompts/` Subdirectory

The user's prompt references this directory for automated thread handoff prompts. **This directory does not exist yet** and would need to be created if the automated handoff workflow is to be supported.

---

## 12. Key Files Section Completeness

The AGENTS.md "Key Files" section (lines 39-49) lists 10 files. The complete inventory should include approximately **30+ key files** across scripts, util, docs, tests, and configuration.

### Files listed but incorrect:

| Listed File | Issue |
|-------------|-------|
| `cly` | Renamed to `claudey` |
| `scripts/worktree_cleanup.bash` | Moved to `util/worktree_cleanup.bash` |

### Files that should be added:

| Category | Files |
|----------|-------|
| Configuration | `.pre-commit-config.yaml`, `.markdownlint.yaml`, `.sops.yaml`, `CHANGELOG.md`, `.serena/project.yml` |
| Documentation | `docs/DOCUMENTATION_OVERVIEW.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` |
| Scripts | `scripts/claude_interactive.bash`, `scripts/activate_conda_env.bash`, `scripts/resume_session.bash` |
| Utilities | `util/worktree_cleanup.bash`, `util/check_doc_links.py`, `util/generate_dep_docs.sh`, `util/juniper_plant_all.bash`, `util/juniper_chop_all.bash` |
| Tests | `tests/test_check_doc_links.py`, `tests/test_worktree_cleanup.py` |
| CI/CD | `.github/workflows/ci.yml`, `.github/workflows/docs-full-check.yml`, `.github/workflows/security-scan.yml`, `.github/workflows/claude.yml` |

---

## 13. Documentation of Pre-commit Hooks

AGENTS.md makes no mention of pre-commit hooks. The repository has a comprehensive `.pre-commit-config.yaml` with the following hooks:

- **pre-commit-hooks** (v4.6.0): YAML/TOML/JSON check, end-of-file fixer, trailing whitespace, merge conflict check, large files, case conflicts, Python AST, debug statements, private key detection
- **flake8** (7.1.1): Python linting with bugbear, comprehensions, simplify plugins (max-line-length: 512)
- **bandit** (1.9.4): Security scanning for Python scripts
- **shellcheck** (v0.10.0.1): Shell script linting (severity: warning)
- **markdownlint** (v0.42.0): Markdown linting with auto-fix
- **yamllint** (v1.35.1): YAML linting (relaxed mode)
- **local/no-unencrypted-env**: Blocks unencrypted `.env` files from being committed

---

## 14. Secrets Management (SOPS)

AGENTS.md makes no mention of SOPS encryption. The repository has:

- `.sops.yaml` — Configuration for age-based encryption of `.env` and `.env.secrets` files
- `.env.enc` — Encrypted environment file
- Pre-commit hook blocking unencrypted `.env` files
- `notes/SOPS_USAGE_GUIDE.md` — Usage documentation

---

## 15. MCP Server Availability

AGENTS.md makes no mention of MCP (Model Context Protocol) server availability. The current environment provides access to:

- **chrome-devtools** — Browser automation and testing
- **context7** — Library documentation fetching
- **deepwiki** — AI-powered GitHub repository documentation
- **hf-mcp-server** — Hugging Face Hub integration
- **kaggle** — Dataset search and download
- **serena** — Semantic code analysis (configured in `.serena/project.yml`)

---

## 16. Summary of All Drift Categories

| # | Category | Severity | Items |
|---|----------|----------|-------|
| 1 | Version mismatch | High | AGENTS.md v0.2.0 vs pyproject.toml v0.3.0 |
| 2 | File renames/relocations | High | `cly` -> `claudey`, `scripts/worktree_cleanup.bash` -> `util/worktree_cleanup.bash` |
| 3 | Undocumented `util/` directory | High | 22 scripts across 6 categories |
| 4 | Undocumented scripts | Medium | 3 new scripts, 2 new subdirectories, 1 symlink |
| 5 | Undocumented test files | Medium | 2 new test files (508 lines total) |
| 6 | Undocumented `docs/` directory | High | 5 documentation files |
| 7 | CI/CD expansion | High | 4 undocumented workflows |
| 8 | Undocumented configuration files | High | 10 configuration files |
| 9 | Undocumented ecosystem files | Low | 5 files/directories (PID, images, resources, logs) |
| 10 | Undocumented `notes/` structure | Medium | 8 subdirectories with categorized content |
| 11 | Missing automated handoff directory | Low | `prompts/thread-handoff_automated-prompts/` does not exist |
| 12 | Incomplete Key Files section | High | Lists 10, should list ~30+ |
| 13 | Missing pre-commit documentation | Medium | 7 hook groups undocumented |
| 14 | Missing secrets management docs | Medium | SOPS encryption undocumented |
| 15 | Missing MCP server documentation | Low | Available MCP servers not listed |

---

## Recommendations

1. **Bump AGENTS.md version to 0.3.0** to match pyproject.toml
2. **Fix all file renames**: `cly` -> `claudey`, `scripts/worktree_cleanup.bash` -> `util/worktree_cleanup.bash`
3. **Add `util/` directory section** documenting all 22 utility scripts
4. **Add `docs/` directory section** documenting all 5 documentation files
5. **Expand CI/CD section** to cover all 5 workflows
6. **Add Configuration section** covering pre-commit, SOPS, markdownlint, Serena, Git LFS, dependabot
7. **Update Key Files section** to be comprehensive
8. **Update Build & Package Commands** to include all test commands
9. **Add directory layout diagram** showing the full repository structure
10. **Add MCP server availability note** for Claude Code sessions
11. **Create `prompts/thread-handoff_automated-prompts/`** directory if automated handoff is desired
