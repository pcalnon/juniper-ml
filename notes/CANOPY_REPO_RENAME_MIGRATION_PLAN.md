# Canopy Repository Rename — Analysis and Migration Plan

**Project**: Juniper Ecosystem
**Subject**: Rename local Canopy repo from `JuniperCanopy/juniper_canopy` to `juniper-canopy`
**Author**: Paul Calnon
**Created**: 2026-02-25
**Revised**: 2026-02-26
**Status**: Complete (executed 2026-02-26)

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Current State Analysis](#2-current-state-analysis)
  - [2.1 Canopy Repository Identity](#21-canopy-repository-identity)
  - [2.2 Ecosystem Naming Convention Comparison](#22-ecosystem-naming-convention-comparison)
  - [2.3 Legacy PascalCase Directories](#23-legacy-pascalcase-directories)
- [3. Root Cause Analysis](#3-root-cause-analysis)
- [4. Cross-Repo Audit — Old Name References](#4-cross-repo-audit--old-name-references)
  - [4.1 juniper-deploy (Docker Compose Orchestration)](#41-juniper-deploy-docker-compose-orchestration)
  - [4.2 juniper-cascor (CasCor Backend)](#42-juniper-cascor-cascor-backend)
  - [4.3 juniper-data (Dataset Service)](#43-juniper-data-dataset-service)
  - [4.4 juniper-data-client (HTTP Client Library)](#44-juniper-data-client-http-client-library)
  - [4.5 juniper-cascor-client (CasCor Client)](#45-juniper-cascor-client-cascor-client)
  - [4.6 juniper-cascor-worker (Distributed Worker)](#46-juniper-cascor-worker-distributed-worker)
  - [4.7 juniper-ml (Meta-Package)](#47-juniper-ml-meta-package)
  - [4.8 Parent Ecosystem Files (Juniper/)](#48-parent-ecosystem-files-juniper)
  - [4.9 Archived Prompts](#49-archived-prompts)
  - [4.10 VS Code Workspace](#410-vs-code-workspace)
- [5. Internal Canopy Audit — Old Name References](#5-internal-canopy-audit--old-name-references)
  - [5.1 Configuration Files — Hardcoded Paths (Would Break)](#51-configuration-files--hardcoded-paths-would-break)
  - [5.2 Relative Path Breakage from Directory Depth Change](#52-relative-path-breakage-from-directory-depth-change)
  - [5.3 CI/CD Workflow](#53-cicd-workflow)
  - [5.4 GitHub/Copilot Instructions (Would Break)](#54-githubcopilot-instructions-would-break)
  - [5.5 Shell Configuration Files — Functional References (42 files)](#55-shell-configuration-files--functional-references-42-files)
  - [5.6 Utility Bash Scripts (20+ files)](#56-utility-bash-scripts-20-files)
  - [5.7 Dockerfiles and Docker Compose](#57-dockerfiles-and-docker-compose)
  - [5.8 Conda Environment YAML Files](#58-conda-environment-yaml-files)
  - [5.9 Python Source — File Headers](#59-python-source--file-headers)
  - [5.10 Python Source — Functional References](#510-python-source--functional-references)
  - [5.11 Documentation Files (Path Examples)](#511-documentation-files-path-examples)
  - [5.12 Notes and Historical Files](#512-notes-and-historical-files)
  - [5.13 Reference Count Summary](#513-reference-count-summary)
- [6. Naming Convention Decisions](#6-naming-convention-decisions)
- [7. Migration Impact Assessment](#7-migration-impact-assessment)
- [8. Migration Plan](#8-migration-plan)
  - [Phase 0: Pre-Migration Preparation](#phase-0-pre-migration-preparation)
  - [Phase 1: Canopy Internal Updates (Worktree Branch)](#phase-1-canopy-internal-updates-worktree-branch)
  - [Phase 2: Atomic Merge and Directory Move](#phase-2-atomic-merge-and-directory-move)
  - [Phase 3: Cross-Repo Updates](#phase-3-cross-repo-updates)
  - [Phase 4: Parent Ecosystem Updates](#phase-4-parent-ecosystem-updates)
  - [Phase 5: Validation and Cleanup](#phase-5-validation-and-cleanup)
- [9. Rollback Plan](#9-rollback-plan)
- [10. Post-Migration Verification Checklist](#10-post-migration-verification-checklist)

---

## 1. Executive Summary

The Juniper Canopy application is the only project in the Juniper ecosystem whose local directory name does not follow the standardized kebab-case naming convention. All other projects (`juniper-cascor`, `juniper-data`, `juniper-data-client`, `juniper-ml`, `juniper-cascor-worker`, `juniper-cascor-client`, `juniper-deploy`) use lowercase hyphenated names for their local directories, remote GitHub repository names, and PyPI package names.

Canopy currently lives at:

```
Juniper/JuniperCanopy/juniper_canopy/   (PascalCase wrapper + snake_case git root)
```

It should live at:

```
Juniper/juniper-canopy/                 (kebab-case, flat — matching all other repos)
```

The remote GitHub repo (`pcalnon/juniper-canopy`), PyPI package name (`juniper-canopy`), and Docker service name (`juniper-canopy`) already use the correct convention. Only the local directory structure is non-conformant.

**Scope of change**: 333 references to `JuniperCanopy` exist within the Canopy repo across all file types (`.py`, `.conf`, `.bash`, `.yaml`, `.md`, `Dockerfile`). Of these, ~20 are functional runtime references in shell scripts, ~5 are hardcoded path references that would break on move, and the remainder are file headers, documentation, and comments. An additional ~30 cross-repo references exist across 6 other Juniper repositories.

This document provides a complete audit of all references to the old naming convention across the entire Juniper ecosystem and a phased migration plan.

---

## 2. Current State Analysis

### 2.1 Canopy Repository Identity

| Aspect | Current Value | Convention Status |
|--------|---------------|-------------------|
| **Local directory** | `JuniperCanopy/juniper_canopy/` | Non-conformant (PascalCase wrapper + snake_case) |
| **Git root** | `JuniperCanopy/juniper_canopy/` | Non-conformant (nested) |
| **Remote URL** | `git@github.com-juniper-canopy:pcalnon/juniper-canopy.git` | Correct (kebab-case) |
| **GitHub repo** | `pcalnon/juniper-canopy` | Correct |
| **PyPI package** | `juniper-canopy` | Correct |
| **Python module** | `juniper_canopy` | Correct (PEP 8 — underscores for importable modules) |
| **Docker service** | `juniper-canopy` | Correct |
| **Docker image** | `juniper-canopy:latest` | Correct |
| **Current branch** | `main` | — |
| **HEAD** | `0f0efe1` | — |

### 2.2 Ecosystem Naming Convention Comparison

All other Juniper repos follow a consistent pattern where the local directory name matches the GitHub repo name and PyPI package name:

| Repository | Local Directory | Remote URL | PyPI Package | Conforms? |
|------------|----------------|------------|--------------|-----------|
| CasCor Backend | `juniper-cascor/` | `pcalnon/juniper-cascor` | `juniper-cascor` | Yes |
| Data Service | `juniper-data/` | `pcalnon/juniper-data` | `juniper-data` | Yes |
| Data Client | `juniper-data-client/` | `pcalnon/juniper-data-client` | `juniper-data-client` | Yes |
| CasCor Worker | `juniper-cascor-worker/` | `pcalnon/juniper-cascor-worker` | `juniper-cascor-worker` | Yes |
| CasCor Client | `juniper-cascor-client/` | `pcalnon/juniper-cascor-client` | `juniper-cascor-client` | Yes |
| ML Meta-Package | `juniper-ml/` | `pcalnon/juniper-ml` | `juniper-ml` | Yes |
| Deployment | `juniper-deploy/` | `pcalnon/juniper-deploy` | N/A | Yes |
| **Canopy** | **`JuniperCanopy/juniper_canopy/`** | `pcalnon/juniper-canopy` | `juniper-canopy` | **No** |

### 2.3 Legacy PascalCase Directories

Three legacy PascalCase wrapper directories exist under `Juniper/`:

| Directory | Contains | Has `.git`? | Purpose |
|-----------|----------|-------------|---------|
| `JuniperCanopy/` | `juniper_canopy/` (git repo) + misc files | No (wrapper only) | Legacy wrapper; git repo is nested inside |
| `JuniperCascor/` | `juniper_cascor/` (non-git copy) + misc files | No | Deprecated — active repo is `juniper-cascor/` |
| `JuniperData/` | `juniper_data/` (non-git copy) + misc files | No | Deprecated — active repo is `juniper-data/` |

For CasCor and Data, the migration to kebab-case top-level directories was completed previously. The legacy PascalCase directories remain as inactive artifacts. Canopy is the only project where the PascalCase directory still holds the **active** git repository.

---

## 3. Root Cause Analysis

The Canopy repo name was not migrated because:

1. **Historical convention**: All Juniper projects originally used PascalCase parent directories (`JuniperCascor/`, `JuniperData/`, `JuniperCanopy/`) with snake_case git roots nested inside. This was the original project layout.

2. **Incremental migration**: When the microservices architecture was adopted, new repos (`juniper-cascor-worker`, `juniper-cascor-client`, `juniper-deploy`) were created with kebab-case names from inception. Existing repos (`juniper-cascor`, `juniper-data`, `juniper-data-client`) were migrated to kebab-case top-level directories.

3. **Canopy was skipped**: During the migration of other repos, Canopy was not moved. The likely reasons:
   - Canopy was undergoing significant development at the time (CI/CD overhaul, test suite expansion, CasCor decoupling)
   - The remote repo and PyPI name were already correct, so the local naming discrepancy was a lower priority
   - The `JuniperCanopy/` wrapper directory contains non-repo files (images archive, workspace file, coverage artifacts) that would need separate handling

4. **No blocking functional issue**: Since `git remote` and `pyproject.toml` already use `juniper-canopy`, the mismatch doesn't break git operations or package publishing. It's a local filesystem convention issue.

5. **juniper-deploy hardcodes the path**: The Docker Compose build context at `juniper-deploy/docker-compose.yml:85` uses `../JuniperCanopy/juniper_canopy`, which reinforces the current structure as a dependency.

---

## 4. Cross-Repo Audit — Old Name References

### 4.1 juniper-deploy (Docker Compose Orchestration)

**Severity: CRITICAL — Would break Docker builds on rename**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `docker-compose.yml` | 85 | `context: ../JuniperCanopy/juniper_canopy` | Build path | **Must update to `../juniper-canopy`** |
| `docker-compose.yml` | 81 | `# JuniperCanopy — Monitoring Dashboard` | Comment | Update to `juniper-canopy` |
| `.env.example` | 16 | `# JuniperCanopy` | Comment | Update to `juniper-canopy` |
| `README.md` | 6-7 | `JuniperCanopy` in service description | Documentation | Update |
| `README.md` | 18 | `└── JuniperCanopy/juniper_canopy/` in directory tree | Documentation | Update to `juniper-canopy/` |
| `README.md` | 44 | `JuniperCanopy` in service table | Documentation | Update |
| `tests/test_health.py` | 135 | `class TestJuniperCanopyHealth:` | Test class name | No change needed — PascalCase is correct for Python class names |
| `tests/conftest.py` | 36, 68-69 | `CANOPY_URL`, `canopy_url` fixture | Test infrastructure | No change (uses `CANOPY` prefix, not directory name) |
| `tests/test_full_stack.py` | 152 | `class TestCanopyEndToEnd:` | Test class name | No change (abbreviated form) |

### 4.2 juniper-cascor (CasCor Backend)

**Severity: LOW — Documentation and comments only**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `src/api/websocket/messages.py` | 10 | `Compatible with JuniperCanopy's WebSocket message protocol.` | Docstring | Update to `juniper-canopy` |
| `src/api/lifecycle/monitor.py` | 3 | `Ported from JuniperCanopy backend/training_monitor.py.` | Docstring | Update to `juniper-canopy` |
| `src/api/lifecycle/state_machine.py` | 3 | `Ported from JuniperCanopy backend/training_state_machine.py.` | Docstring | Update to `juniper-canopy` |
| `README.md` | 22-29 | Mixed `JuniperCanopy` (text) and `juniper-canopy` (links) | Documentation | Standardize text to `juniper-canopy` |
| `notes/DECOUPLE_CANOPY_FROM_CASCOR_PLAN.md` | 1, 21 | `JuniperCanopy` references | Historical notes | Update if not archived |
| `notes/MONOREPO_ANALYSIS.md` | 42-45 | `JuniperCanopy` in ecosystem table | Historical notes | Update if not archived |
| `notes/INTEGRATION_ROADMAP-01.md` | 16-20 | `JuniperCanopy` in analysis table | Historical notes | Update if not archived |

### 4.3 juniper-data (Dataset Service)

**Severity: LOW — Documentation only**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `README.md` | 22-45 | Mixed `JuniperCanopy` (text) and `juniper-canopy` (links) | Documentation | Standardize text to `juniper-canopy` |
| `README.md` | 168 | `juniper-canopy` reference | Documentation | Already correct |

### 4.4 juniper-data-client (HTTP Client Library)

**Severity: LOW — Documentation and docstrings**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `README.md` | 7-16 | `JuniperCanopy` in description | Documentation | Update |
| `juniper_data_client/__init__.py` | 4 | `used by both JuniperCascor and JuniperCanopy` | Docstring | Update |
| `juniper_data_client/client.py` | 4 | `for JuniperCascor and JuniperCanopy applications` | Docstring | Update |

### 4.5 juniper-cascor-client (CasCor Client)

**Severity: LOW — Documentation only**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `README.md` | 10-12 | `juniper-canopy` in compatibility table | Documentation | Already correct |

### 4.6 juniper-cascor-worker (Distributed Worker)

**Severity: LOW — Documentation only**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `README.md` | 15-17 | `juniper-canopy` in compatibility table | Documentation | Already correct |

### 4.7 juniper-ml (Meta-Package)

**Severity: LOW — Documentation only**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `README.md` | 25-27 | `juniper-canopy` in compatibility table | Documentation | Already correct |
| `README.md` | 53 | `**JuniperCanopy** - Real-time monitoring dashboard` | Documentation | Update to `**juniper-canopy**` |

### 4.8 Parent Ecosystem Files (Juniper/)

**Severity: MEDIUM — Ecosystem documentation**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `CLAUDE.md` / `AGENTS.md` | Multiple | `JuniperCanopy/juniper_canopy/` path references | Documentation | Update directory references |
| `CLAUDE.md` / `AGENTS.md` | Multiple | `JuniperCanopy` in project tables | Documentation | Update |
| `CLAUDE.md` / `AGENTS.md` | 153 | `├── JuniperCanopy/` in directory tree (shown as legacy) | Documentation | Update to reflect `juniper-canopy/` |

### 4.9 Archived Prompts

**Severity: NONE — Historical records**

| File | Line(s) | Content | Type | Action |
|------|---------|---------|------|--------|
| `prompts/prompt19_2026-01-08.md` | 8, 11-12, 14, 20-21 | Old absolute paths `JuniperCanopy/juniper_canopy` | Archived session | No change (historical record) |
| `juniper-ml/prompts/prompt005_2026-02-25.md` | 5-19 | This migration task definition | Active prompt | No change |

### 4.10 VS Code Workspace

**Severity: NONE — No path-specific references**

| File | Content | Action |
|------|---------|--------|
| `Juniper.code-workspace` | Only contains `{"folders": [{"path": "."}]}` | No change needed |
| `.vscode/settings.json` | Only contains cSpell word list (includes `JUNIPERCANOPY`) | Optional: could update cSpell entry |

---

## 5. Internal Canopy Audit — Old Name References

References within the Canopy repo itself (`JuniperCanopy/juniper_canopy/`). Total: **333 references** to `JuniperCanopy` across all file types.

### 5.1 Configuration Files — Hardcoded Paths (Would Break)

| File | Line | Content | Severity |
|------|------|---------|----------|
| `conf/setup_environment.conf` | 56 | `export PROJECT_DIR="${HOME}/Development/python/JuniperCanopy/juniper_canopy"` | **CRITICAL** — Hardcoded absolute path; used by shell scripts at runtime |
| `conf/juniper_canopy.conf` | 30 | `~/Development/python/JuniperCanopy/juniper_canopy/conf/test_prototype_conf.bash` | **HIGH** — Hardcoded path in comment/reference |
| `conf/juniper_canopy_functions.conf` | 30 | `~/Development/python/JuniperCanopy/juniper_canopy/conf/test_prototype_conf.bash` | **HIGH** — Same hardcoded path |

### 5.2 Relative Path Breakage from Directory Depth Change

**Severity: CRITICAL — This is caused directly by the directory move, not a separate issue.**

The directory nesting depth changes from 2 levels (inside `Juniper/`) to 1 level:

- **Before** (`Juniper/JuniperCanopy/juniper_canopy/`): `../../` from git root resolves to `Juniper/`
- **After** (`Juniper/juniper-canopy/`): `../../` from git root resolves to `Development/python/`

| File | Line | Content | Impact |
|------|------|---------|--------|
| `conf/app_config.yaml` | 266 | `backend_path: "${CASCOR_BACKEND_PATH:../../JuniperCascor/juniper_cascor}"` | **Breaks** — relative path resolves incorrectly after move |
| `conf/app_config.yaml` | 263-265 | Comment lines referencing `../../JuniperCascor/juniper_cascor` and `~/Development/python/JuniperCanopy/juniper_cascor` | Update comments |

**Required fix**: The relative fallback must change from `../../JuniperCascor/juniper_cascor` to `../juniper-cascor` (one level up from `juniper-canopy/` reaches `Juniper/`, then into `juniper-cascor/`).

### 5.3 CI/CD Workflow

| File | Line | Content | Severity |
|------|------|---------|----------|
| `.github/workflows/ci.yml` | 4 | `# Sub-Project:   JuniperCanopy` | LOW — File header |
| `.github/workflows/ci.yml` | 5 | `# Application:   juniper_canopy` | LOW — File header |
| `.github/workflows/ci.yml` | 54 | `ENV_NAME: JuniperCanopy` | **MEDIUM** — CI environment variable. May affect conda env activation in CI pipeline. See [Section 6 Decision 2](#decision-2-conda-environment-name-references) |

### 5.4 GitHub/Copilot Instructions (Would Break)

| File | Line | Content | Severity |
|------|------|---------|----------|
| `.github/instructions/copilot-instructions.md` | 773 | `WorkingDirectory=/home/pcalnon/Development/python/JuniperCanopy/juniper_canopy/src` | **HIGH** — Absolute path |
| `.github/instructions/copilot-instructions.md` | 775 | `CASCOR_BACKEND_PATH=/home/pcalnon/Development/python/JuniperCascor/juniper_cascor/src` | **MEDIUM** — References old CasCor path too |

### 5.5 Shell Configuration Files — Functional References (42 files)

All 42 `.conf` files in `conf/` contain at least one `JuniperCanopy` reference (file headers). Beyond headers, **~20 files contain functional (runtime) references** that export shell variables or define paths:

#### Exported Shell Variables (Runtime — Must Decide)

These variables are set at runtime by the shell configuration framework. See [Section 6 Decision 1](#decision-1-sub-project-display-name-in-headers-and-shell-variables) for the naming decision.

| Variable | Files | Current Value |
|----------|-------|---------------|
| `SUB_PROJECT_NAME` | `common.conf:158`, `get_module_filenames.conf:73` | `"JuniperCanopy"` |
| `SUBPROJECT_NAME` | `juniper_canopy.conf:84` | `"JuniperCanopy"` |
| `SUB_PROJ_NAME` | `get_todo_comments.conf:75`, `get_file_lines.conf:72`, `get_file_todo.conf:73`, `script_template.bash:57` | `"JuniperCanopy"` |
| `ROOT_SUB_PROJECT_NAME` | `source_tree.conf:52` | `"JuniperCanopy"` |
| `ROOT_SUB_PROJ_NAME` | `random_seed.conf:60` | `"JuniperCanopy"` |
| `PROJ_NAME` | `get_code_stats.conf:87`, `git_branch_ages.conf:79` | `"JuniperCanopy"` |
| `NEW_PATH` | `change_path.conf:53` | `"JuniperCanopy"` |

#### Conda Environment Name References (Runtime — Likely Stale)

These reference a `JuniperCanopy` conda environment. The active shared environment is `JuniperPython` per the ecosystem CLAUDE.md. See [Section 6 Decision 2](#decision-2-conda-environment-name-references).

| Variable / Reference | Files | Current Value |
|---------------------|-------|---------------|
| `CONDA_ENV_NAME` | `juniper_canopy.conf:179`, `conda_env_update.conf:50` | `"JuniperCanopy"` |
| `PYTHON_ENV_ROOT` | `create_performance_profile.conf:78` | `"/opt/miniforge3/envs/JuniperCanopy/bin"` |
| `PYTHON_LOC_MACOS` | `random_seed.conf:85` | `"${CONDA_MACOS}/envs/JuniperCanopy/bin/python"` |
| `PYTHON_LOC_LINUX` | `random_seed.conf:86` | `"${CONDA_LINUX}/envs/JuniperCanopy/bin/python"` |

#### File Headers in conf/ (42 files — Cosmetic)

Every `.conf` file in `conf/` has a standardized header containing:
```
# Sub-Project:   JuniperCanopy
# Application:   juniper_canopy
```

Full list of conf files with headers: `__date_functions.conf`, `__git_log_weeks.conf`, `change_path.conf`, `color_display_codes.conf`, `common.conf`, `common_functions.conf`, `conda_env_update.conf`, `create_performance_profile.conf`, `create_performance_profile_functions.conf`, `get_code_stats.conf`, `get_code_stats_functions.conf`, `get_file_lines.conf`, `get_file_todo.conf`, `get_file_todo_functions.conf`, `get_module_filenames.conf`, `get_module_filenames_functions.conf`, `get_script_path.conf`, `get_script_path_functions.conf`, `get_todo_comments.conf`, `get_todo_comments_functions.conf`, `git_branch_ages.conf`, `init.conf`, `juniper_canopy.conf`, `juniper_canopy-demo.conf`, `juniper_canopy_functions.conf`, `last_mod_update.conf`, `logging.conf`, `logging_colors.conf`, `logging_functions.conf`, `main.conf`, `proto.conf`, `random_seed.conf`, `run_all_tests.conf`, `save_to_usb.conf`, `setup_environment.conf`, `setup_environment_functions.conf`, `setup_test.conf`, `source_tree.conf`, `test_common.conf`, `test_prototype.conf`, `todo_search.conf`, `update_weekly.conf`.

### 5.6 Utility Bash Scripts (20+ files)

All bash scripts in `util/` have standardized headers with `Sub-Project: JuniperCanopy`. At least one has a functional reference:

| File | Line | Content | Type |
|------|------|---------|------|
| `util/script_template.bash` | 57 | `export SUB_PROJ_NAME="JuniperCanopy"` | Functional — exported variable |
| `util/rsink.bash` | 20 | `sync data from the JuniperCanopy application` | Docstring |
| `util/setup_test.bash` | 20 | `setup the test environment for the JuniperCanopy application` | Docstring |

All other `util/*.bash` files have header-only references: `last_mod_update.bash`, `save_to_usb.bash`, `run_all_tests.bash`, `source_tree.bash`, `color_display_codes.bash`, `juniper_canopy-demo.bash`, `mv2_bash_n_back.bash`, `todo_search.bash`, `__get_os_name.bash`, `proto.bash`, `setup_test.bash`, `git_branch_ages.bash`, `color_table.py`, `get_todo_comments.bash`, `__get_project_dir.bash`.

### 5.7 Dockerfiles and Docker Compose

**Two Dockerfiles exist** (root and `conf/`):

| File | Line | Content | Severity |
|------|------|---------|----------|
| `Dockerfile` | 1-3 | `# JuniperCanopy — Monitoring Dashboard` | LOW — Comment |
| `Dockerfile` | 43 | `LABEL org.opencontainers.image.title="JuniperCanopy"` | LOW — OCI label |
| `conf/Dockerfile` | 2 | `docker build -t juniper_canopy .` | LOW — Comment example |
| `conf/Dockerfile` | 3 | `docker run -p 8050:8050 juniper_canopy` | LOW — Comment example |
| `conf/docker-compose.yaml` | 34 | Service named `juniper_canopy` (underscore) | **MEDIUM** — Inconsistent with `juniper-deploy` which uses `juniper-canopy` (hyphen) |

### 5.8 Conda Environment YAML Files

These define a conda environment named `JuniperCanopy`, which appears stale since the active shared environment is `JuniperPython`. See [Section 6 Decision 2](#decision-2-conda-environment-name-references).

| File | Line | Content |
|------|------|---------|
| `conf/conda_environment_ci.yaml` | 54 | `name: JuniperCanopy` |
| `conf/conda_environment_ci.yaml` | 40, 42, 44 | Comments: `conda create --name JuniperCanopy`, `conda env update --name JuniperCanopy` |
| `conf/conda_environment-ORIG.yaml` | 52-53 | `name: JuniperCanopy` |
| `conf/conda_environment_ci-ORIG.yaml` | 54 | `name: JuniperCanopy` |
| `conf/conda_environment_ci-ORIG.yaml` | 40, 42, 44 | Comments referencing `JuniperCanopy` |

### 5.9 Python Source — File Headers

Multiple Python source files contain a standardized header block with `Sub-Project: JuniperCanopy` and `File Path: ${HOME}/Development/python/JuniperCanopy/juniper_canopy/src/`. Approximately 5 Python files have these headers. See [Section 6 Decision 1](#decision-1-sub-project-display-name-in-headers-and-shell-variables) for the naming convention decision.

Known files with headers:

- `src/main.py`
- `src/demo_mode.py`
- `src/tests/integration/test_cascor_ws_control.py`
- `src/tests/unit/test_juniper_data_integration.py`
- `src/tests/unit/test_juniper_data_url_validation.py`

### 5.10 Python Source — Functional References

Non-header references in Python source that use `JuniperCanopy` at runtime or in meaningful context:

| File | Line | Content | Type | Action |
|------|------|---------|------|--------|
| `src/backend/cassandra_client.py` | 233 | `"cluster_name": "JuniperCanopy Demo Cluster"` | Runtime string (Cassandra cluster display name) | **Decision point**: this is a display name passed to Cassandra, not a path. Changing it would affect any existing Cassandra data. Recommend leaving unchanged or treating as a separate follow-up |
| `src/tests/regression/test_startup_regression.py` | 20 | `Regression tests for the JuniperCanopy startup failure` | Test docstring | Update to `juniper-canopy` |

### 5.11 Documentation Files (Path Examples)

| File | Content | Severity |
|------|---------|----------|
| `docs/cascor/CASCOR_BACKEND_QUICK_START.md` | `cd ~/Development/python/JuniperCanopy/juniper_canopy` | LOW |
| `docs/USER_MANUAL.md` | `cd ~/Development/python/JuniperCanopy/juniper_canopy` | LOW |
| `docs/ENVIRONMENT_SETUP.md` | `cd ~/Development/python/JuniperCanopy` | LOW |
| `docs/QUICK_START.md` | `cd ~/Development/python/JuniperCanopy` | LOW |
| `docs/cascor/CASCOR_BACKEND_MANUAL.md` | `cd ~/Development/python/JuniperCanopy` | LOW |
| `docs/testing/TESTING_ANALYSIS_REPORT.md` | Absolute path reference to `JuniperCanopy/juniper_canopy` | LOW |
| `docs/testing/TESTING_ENVIRONMENT_SETUP.md` | `PYTHONPATH` export with old path | LOW |
| `docs/ci_cd/CICD_QUICK_START.md` | `file:///` URL with old path | LOW |

### 5.12 Notes and Historical Files

Multiple files in `notes/` contain old path references. These are historical records of development work and analysis:

| File | Content | Action |
|------|---------|--------|
| `notes/analysis/DEMO_HANG_ANALYSIS_2026-01-03.md` | Old paths in analysis | Optional update |
| `notes/fixes/BASH_SCRIPT_FIXES_2025-12-31.md` | Documents old hardcoded paths | Optional update |
| `notes/fixes/FIX_BASH_SCRIPTS_2026-01-01.md` | Log paths referencing old structure | Optional update |
| `notes/history/CANOPY_JUNIPER_DATA_INTEGRATION_PLAN.md` | Old paths in links/code | No change (historical) |

### 5.13 Reference Count Summary

| Category | Files | Total References | Action Type |
|----------|-------|-----------------|-------------|
| Hardcoded absolute paths | 3 | 3 | **Must fix** — runtime breakage |
| Relative path (depth-dependent) | 1 | 1 | **Must fix** — resolves wrong after move |
| CI workflow environment variable | 1 | 1 | **Must evaluate** — may affect pipeline |
| GitHub/Copilot instructions | 1 | 2 | **Must fix** — absolute paths |
| Shell variables (functional) | ~15 | ~20 | **Decision required** — see Section 6 |
| Conda env name references | ~5 | ~8 | **Decision required** — likely stale |
| File headers (`conf/`, `util/`, `src/`) | ~65 | ~130 | Update — cosmetic but high volume |
| Dockerfiles + compose | 3 | 5 | Update |
| Documentation (`docs/`, `*.md`) | ~8 | ~15 | Update |
| Python functional references | 2 | 2 | Decision point per-reference |
| Notes/history | ~4 | ~10 | Optional |
| **Total** | **~100+** | **~333** | |

---

## 6. Naming Convention Decisions

Two naming decisions must be made before executing the migration. These affect the scope and content of many updates.

### Decision 1: Sub-Project Display Name in Headers and Shell Variables

**Question**: Should the `Sub-Project` field in file headers and exported shell variables like `SUB_PROJECT_NAME` change from `JuniperCanopy` (PascalCase) to `juniper-canopy` (kebab-case)?

**Context**: The `Sub-Project` field in the standardized file header is a **display/product name**, not a directory name. Other repos presumably use PascalCase for this field (e.g., `Sub-Project: JuniperCascor`). The shell variable `SUB_PROJECT_NAME="JuniperCanopy"` is also used as a display name in scripts, not as a path component.

**Options**:

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A** | Change to `juniper-canopy` everywhere | Full consistency with repo/package name | Breaks convention with other repos' headers; mixes display names with identifiers |
| **B** | Keep `JuniperCanopy` in headers and display variables; only change path references | Consistent with other repos' header conventions; smaller diff | Two naming conventions coexist within the repo |
| **C** | Change headers to `juniper-canopy`; leave shell display variables as `JuniperCanopy` | Partial update | Inconsistent within the repo |

**Recommendation**: **Option B** — Keep `JuniperCanopy` as the product display name in headers and shell variables. Only update references that are **paths** or **directory names**. This is consistent with how other Juniper repos handle the distinction between product name and package/directory name.

**If Option B is chosen**: The scope of `conf/` and `util/` header updates drops from ~130 references to 0 (headers unchanged). Only the ~20 functional path references need updating.

**If Option A is chosen**: All 333 references change. The `find | sed` commands in Phase 1 must cover `*.conf`, `*.bash`, `*.py`, `*.yaml`, `*.yml`, `*.md`, and `Dockerfile` files.

### Decision 2: Conda Environment Name References

**Question**: What should happen to references to a `JuniperCanopy` conda environment?

**Context**: Multiple `conf/` files and conda YAML files reference `CONDA_ENV_NAME="JuniperCanopy"` or `name: JuniperCanopy`. However, the ecosystem-wide CLAUDE.md documents the shared environment as `JuniperPython` (`/opt/miniforge3/envs/JuniperPython`). The `JuniperCanopy` environment appears to be a stale artifact from before environment consolidation.

**Options**:

| Option | Approach |
|--------|----------|
| **A** | Update all conda env references from `JuniperCanopy` to `JuniperPython` (the actual active environment) |
| **B** | Leave conda env references unchanged (they're already stale/unused) |
| **C** | Remove the stale conda YAML files entirely (the `-ORIG` files and CI-specific ones) |

**Recommendation**: **Option A** — Update to `JuniperPython` to match reality. The stale references cause confusion and would fail if actually used.

---

## 7. Migration Impact Assessment

### Summary by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 3 | `juniper-deploy/docker-compose.yml` build context; `conf/setup_environment.conf` hardcoded path; `conf/app_config.yaml` relative path depth breakage |
| **HIGH** | 3 | `.github/instructions/copilot-instructions.md` absolute paths; `conf/juniper_canopy.conf` and `conf/juniper_canopy_functions.conf` hardcoded paths |
| **MEDIUM** | 5 | CI workflow `ENV_NAME`; `conf/docker-compose.yaml` service name; parent `CLAUDE.md`/`AGENTS.md`; `juniper-ml/README.md`; deploy `README.md` |
| **LOW** | 100+ | File headers (conf/util/src), documentation paths, Dockerfile labels, docstrings, conda YAML names |
| **NONE** | 5+ | Historical/archived files, VS Code workspace, archived prompts |

### What Does NOT Need to Change

- **Remote URL**: Already `juniper-canopy`
- **PyPI package name**: Already `juniper-canopy`
- **Python module name**: `juniper_canopy` (underscores) is correct per PEP 8 — this stays
- **Docker service name** (in `juniper-deploy`): Already `juniper-canopy`
- **Environment variables**: Use `CASCOR_*` and `CANOPY_*` prefixes (not directory-based)
- **Python imports**: All use `juniper_canopy` module name (unaffected by directory rename)
- **Test fixtures**: Use `canopy_url`, `CANOPY_URL` etc. (not path-based)
- **Cassandra cluster name**: `"JuniperCanopy Demo Cluster"` — display name, recommend leaving unchanged

### What Must Change

1. **Physical directory**: `JuniperCanopy/juniper_canopy/` moves to `juniper-canopy/`
2. **Build context**: `juniper-deploy/docker-compose.yml` line 85
3. **Relative path**: `conf/app_config.yaml` backend_path fallback (depth changes)
4. **Hardcoded absolute paths**: `conf/setup_environment.conf`, `.github/instructions/copilot-instructions.md`
5. **Hardcoded path comments**: `conf/juniper_canopy.conf`, `conf/juniper_canopy_functions.conf`
6. **Documentation**: ~25 files across the ecosystem with path examples
7. **CI environment variable**: `.github/workflows/ci.yml` `ENV_NAME` (if conda env name decision changes it)
8. **File headers**: scope depends on [Decision 1](#decision-1-sub-project-display-name-in-headers-and-shell-variables) (0 files if Option B, ~65+ files if Option A)
9. **Conda env references**: scope depends on [Decision 2](#decision-2-conda-environment-name-references)

---

## 8. Migration Plan

### Prerequisites

- All repos on `main` branch with clean working directories
- No active worktrees referencing Canopy paths
- No running Docker containers using the Canopy image
- [Decision 1](#decision-1-sub-project-display-name-in-headers-and-shell-variables) and [Decision 2](#decision-2-conda-environment-name-references) resolved before starting

### Phase 0: Pre-Migration Preparation

**Goal**: Ensure clean state and create backup.

| Step | Command / Action | Verify |
|------|-----------------|--------|
| 0.1 | Ensure Canopy working directory is clean | `cd JuniperCanopy/juniper_canopy && git status` shows clean |
| 0.2 | Ensure all Canopy changes are pushed | `git log --oneline origin/main..HEAD` shows nothing |
| 0.3 | Ensure juniper-deploy is clean | `cd juniper-deploy && git status` shows clean |
| 0.4 | Stop any running Docker Compose stack | `cd juniper-deploy && docker compose down` |
| 0.5 | Note the current HEAD SHA for rollback | `cd JuniperCanopy/juniper_canopy && git rev-parse HEAD` — record as `$PRE_MIGRATION_SHA` |
| 0.6 | Verify no active worktrees | `cd JuniperCanopy/juniper_canopy && git worktree list` shows only main |
| 0.7 | Run `git worktree prune` | Clean any stale worktree metadata that could contain absolute paths |

### Phase 1: Canopy Internal Updates (Worktree Branch)

**Goal**: Update all internal references to use the new path convention. Changes are made on a branch but **NOT merged to main yet** — they stay on the branch until Phase 2 merges and moves atomically.

> **Important**: Do NOT merge this branch to main before the directory move. Between merge and move, the internal references would point to a path that doesn't exist, breaking all shell scripts and configuration. Phase 2 handles the atomic merge-then-move.

**Create a worktree** (per Juniper conventions):

```bash
cd /home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy
git checkout main && git pull origin main
BRANCH_NAME="chore/rename-local-directory"
git branch "$BRANCH_NAME" main
REPO_NAME="juniper-canopy"
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's|/|--|g')
WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/${REPO_NAME}--${SAFE_BRANCH}--$(date +%Y%m%d-%H%M)--$(git rev-parse --short=8 HEAD)"
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
cd "$WORKTREE_DIR"
```

**Step 1.1 — Hardcoded absolute paths** (CRITICAL):

| File | Change |
|------|--------|
| `conf/setup_environment.conf:56` | `${HOME}/Development/python/JuniperCanopy/juniper_canopy` → `${HOME}/Development/python/Juniper/juniper-canopy` |
| `conf/juniper_canopy.conf:30` | `~/Development/python/JuniperCanopy/juniper_canopy/conf/` → `~/Development/python/Juniper/juniper-canopy/conf/` |
| `conf/juniper_canopy_functions.conf:30` | Same pattern as above |

**Step 1.2 — Relative path depth fix** (CRITICAL):

| File | Change |
|------|--------|
| `conf/app_config.yaml:266` | `backend_path: "${CASCOR_BACKEND_PATH:../../JuniperCascor/juniper_cascor}"` → `backend_path: "${CASCOR_BACKEND_PATH:../juniper-cascor}"` |
| `conf/app_config.yaml:263-265` | Update comment lines to reflect new relative path and remove old path examples |

**Step 1.3 — GitHub/Copilot instructions**:

| File | Change |
|------|--------|
| `.github/instructions/copilot-instructions.md:773` | `JuniperCanopy/juniper_canopy/src` → `Juniper/juniper-canopy/src` |
| `.github/instructions/copilot-instructions.md:775` | `JuniperCascor/juniper_cascor/src` → `Juniper/juniper-cascor/src` (fix CasCor path too) |

**Step 1.4 — CI/CD workflow**:

| File | Change |
|------|--------|
| `.github/workflows/ci.yml:54` | `ENV_NAME: JuniperCanopy` → `ENV_NAME: JuniperPython` (if Decision 2 = Option A) or leave if the CI pipeline doesn't actually use this for conda activation |

**Step 1.5 — Dockerfiles and Docker Compose**:

| File | Change |
|------|--------|
| `Dockerfile:1-3` | Comment: `JuniperCanopy` → `juniper-canopy` |
| `Dockerfile:43` | `org.opencontainers.image.title="JuniperCanopy"` → `"juniper-canopy"` |
| `conf/Dockerfile:2-3` | Comment examples: `juniper_canopy` → `juniper-canopy` |
| `conf/docker-compose.yaml:34` | Service name: `juniper_canopy` → `juniper-canopy` (align with `juniper-deploy` convention) |

**Step 1.6 — Shell configuration functional references** (paths only):

Update hardcoded path references in `conf/` files. If Decision 1 = Option B, leave display-name variables (`SUB_PROJECT_NAME`, etc.) unchanged.

Path references to update:

```bash
# Preview path-based references (excluding headers and display names)
grep -rn "Development/python/JuniperCanopy" conf/ util/
grep -rn "envs/JuniperCanopy" conf/
```

| File | Line | Old | New |
|------|------|-----|-----|
| `conf/create_performance_profile.conf` | 78 | `"/opt/miniforge3/envs/JuniperCanopy/bin"` | `"/opt/miniforge3/envs/JuniperPython/bin"` (Decision 2) |
| `conf/random_seed.conf` | 85 | `"${CONDA_MACOS}/envs/JuniperCanopy/bin/python"` | `"${CONDA_MACOS}/envs/JuniperPython/bin/python"` (Decision 2) |
| `conf/random_seed.conf` | 86 | `"${CONDA_LINUX}/envs/JuniperCanopy/bin/python"` | `"${CONDA_LINUX}/envs/JuniperPython/bin/python"` (Decision 2) |
| `conf/juniper_canopy.conf` | 179 | `CONDA_ENV_NAME="JuniperCanopy"` | `CONDA_ENV_NAME="JuniperPython"` (Decision 2) |
| `conf/conda_env_update.conf` | 50 | `CONDA_ENV_NAME="JuniperCanopy"` | `CONDA_ENV_NAME="JuniperPython"` (Decision 2) |
| `conf/change_path.conf` | 53 | `NEW_PATH="JuniperCanopy"` | `NEW_PATH="juniper-canopy"` (this is a directory name, not a display name) |

**Step 1.7 — Conda environment YAML files** (if Decision 2 = Option A):

| File | Change |
|------|--------|
| `conf/conda_environment_ci.yaml:54` | `name: JuniperCanopy` → `name: JuniperPython` |
| `conf/conda_environment_ci.yaml:40,42,44` | Comment examples: `--name JuniperCanopy` → `--name JuniperPython` |
| `conf/conda_environment-ORIG.yaml:52-53` | Same pattern |
| `conf/conda_environment_ci-ORIG.yaml:54,40,42,44` | Same pattern |

**Step 1.8 — File headers** (if Decision 1 = Option A):

> Skip this step entirely if Decision 1 = Option B (keep PascalCase display names).

If updating headers, use project-wide find-and-replace across `src/`, `conf/`, and `util/`:

```bash
# Preview scope
grep -rn "Sub-Project:   JuniperCanopy" src/ conf/ util/ --include="*.py" --include="*.conf" --include="*.bash" --include="*.yaml" --include="*.yml"

# Apply (only if Decision 1 = Option A)
find src/ conf/ util/ \( -name "*.py" -o -name "*.conf" -o -name "*.bash" -o -name "*.yaml" -o -name "*.yml" \) \
  -exec sed -i 's|Sub-Project:   JuniperCanopy|Sub-Project:   juniper-canopy|g' {} +
```

**Step 1.9 — Python file header path updates**:

Regardless of Decision 1, the `File Path:` line in Python headers contains a directory path that must change:

```bash
# Preview
grep -rn "Development/python/JuniperCanopy/juniper_canopy" src/ --include="*.py"

# Apply
find src/ -name "*.py" -exec sed -i \
  's|Development/python/JuniperCanopy/juniper_canopy|Development/python/Juniper/juniper-canopy|g' {} +
```

**Step 1.10 — Documentation path updates**:

Update all `docs/` and root documentation files. Use multiple sed passes to handle different path patterns:

```bash
# Pass 1: Full paths with both components (most specific first)
find docs/ -name "*.md" -exec sed -i \
  's|Development/python/JuniperCanopy/juniper_canopy|Development/python/Juniper/juniper-canopy|g' {} +

# Pass 2: Paths with only the PascalCase parent (e.g., "cd ~/Development/python/JuniperCanopy")
find docs/ -name "*.md" -exec sed -i \
  's|Development/python/JuniperCanopy|Development/python/Juniper/juniper-canopy|g' {} +

# Pass 3: Root-level markdown files
sed -i 's|Development/python/JuniperCanopy/juniper_canopy|Development/python/Juniper/juniper-canopy|g' *.md
sed -i 's|Development/python/JuniperCanopy|Development/python/Juniper/juniper-canopy|g' *.md

# Manual review: check for any remaining JuniperCanopy in prose that is NOT a path
grep -rn "JuniperCanopy" docs/ *.md | grep -v "Development/python"
# These may be product name references — update case-by-case
```

**Step 1.11 — Python functional references**:

| File | Change |
|------|--------|
| `src/tests/regression/test_startup_regression.py:20` | `JuniperCanopy startup failure` → `juniper-canopy startup failure` |
| `src/backend/cassandra_client.py:233` | **Leave unchanged** — `"JuniperCanopy Demo Cluster"` is a Cassandra display name, not a path |

**Step 1.12 — Canopy CLAUDE.md / AGENTS.md**:

Update the agent file to reflect the new directory name in all path references, directory trees, and instructions. This is a large file — use targeted replacements:

```bash
# Path references
sed -i 's|Development/python/JuniperCanopy/juniper_canopy|Development/python/Juniper/juniper-canopy|g' CLAUDE.md AGENTS.md
sed -i 's|Development/python/JuniperCanopy|Development/python/Juniper/juniper-canopy|g' CLAUDE.md AGENTS.md

# Manual review for remaining prose references
grep -n "JuniperCanopy" CLAUDE.md AGENTS.md
```

**Step 1.13 — Notes files** (optional — historical references):

Recommendation: update actively referenced notes, leave clearly historical/archived files unchanged.

**Step 1.14 — Create worktree procedure files**:

Canopy currently lacks `notes/WORKTREE_SETUP_PROCEDURE.md` and `notes/WORKTREE_CLEANUP_PROCEDURE.md`. Create these using the new `juniper-canopy` path, following the templates from other repos (e.g., `juniper-ml/notes/`).

**Step 1.15 — Commit and push branch** (do NOT merge yet):

```bash
git add -A
git commit -m "chore: update internal references for directory rename to juniper-canopy

Updates hardcoded paths, relative path fallbacks, file headers,
documentation, and configuration for the move from
JuniperCanopy/juniper_canopy to juniper-canopy."
git push origin "$BRANCH_NAME"
```

### Phase 2: Atomic Merge and Directory Move

**Goal**: Merge the reference updates and move the directory in a single uninterrupted sequence. This eliminates the breakage window where references point to a non-existent path.

> **CRITICAL**: Steps 2.1 through 2.4 must be executed without interruption. Do not run any Canopy scripts or tests between the merge and the move.

**Step 2.1 — Merge branch to main** (from the main working directory, not the worktree):

```bash
cd /home/pcalnon/Development/python/Juniper/JuniperCanopy/juniper_canopy
git checkout main && git pull origin main
git merge chore/rename-local-directory
```

**Step 2.2 — Immediately move the directory** (before pushing or running anything):

```bash
cd /home/pcalnon/Development/python/Juniper
mv JuniperCanopy/juniper_canopy juniper-canopy
```

**Step 2.3 — Push from the new location**:

```bash
cd juniper-canopy
git push origin main
```

**Step 2.4 — Verify git integrity**:

```bash
git status           # Should show clean working directory
git remote -v        # Should show juniper-canopy remote
git log --oneline -5 # Should show merge commit and Phase 1 changes
```

**Step 2.5 — Clean up worktree**:

```bash
git worktree remove "$WORKTREE_DIR" 2>/dev/null || true
git branch -d chore/rename-local-directory
git push origin --delete chore/rename-local-directory
git worktree prune
```

**Step 2.6 — Handle the legacy wrapper directory**:

The `JuniperCanopy/` wrapper directory contains non-repo files:

```
JuniperCanopy/
├── .serena/                        # Serena config (can discard)
├── .vscode/                        # VS Code settings (check if needed)
├── CONSOLIDATION_SUMMARY.md        # Historical (can archive or discard)
├── DEBUGGING_ANALYSIS_2025-12-06.md # Historical
├── JuniperCanopy.code-workspace    # Legacy workspace file
├── Juniper_Tree_Images.tgz         # Image archive (may want to keep)
├── coverage.xml                    # Build artifact (can discard)
├── happy_dance.css                 # Miscellaneous
├── imager_2.0.3_amd64.AppImage     # Application binary
├── temp/                           # Temporary files (can discard)
```

Recommended action:

```bash
# Move any needed files to the new location or an archive
# Example: move image archive if desired
mv JuniperCanopy/Juniper_Tree_Images.tgz juniper-canopy/ 2>/dev/null || true

# Remove the legacy wrapper (after confirming nothing important remains)
# CAUTION: Review contents before removing
ls -la JuniperCanopy/
# rm -rf JuniperCanopy/  # Only after manual review
```

**Step 2.7 — Verify Canopy tests pass**:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
conda activate JuniperPython
cd src
pytest tests/ -v --tb=short
```

### Phase 3: Cross-Repo Updates

**Goal**: Update all other repos that reference the old path.

Per the worktree guidance in CLAUDE.md, simple documentation-only fixes on `main` do not require a worktree. For repos with only README/docstring changes (cascor, data, data-client, ml), direct commits on `main` are acceptable. For `juniper-deploy` (which has a critical build path change), use a worktree.

**Step 3.1 — juniper-deploy (CRITICAL)**:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
```

| File | Line | Old | New |
|------|------|-----|-----|
| `docker-compose.yml` | 81 | `# JuniperCanopy — Monitoring Dashboard` | `# juniper-canopy — Monitoring Dashboard` |
| `docker-compose.yml` | 85 | `context: ../JuniperCanopy/juniper_canopy` | `context: ../juniper-canopy` |
| `.env.example` | 16 | `# JuniperCanopy` | `# juniper-canopy` |
| `README.md` | Multiple | `JuniperCanopy` references | `juniper-canopy` |
| `README.md` | 18 | `└── JuniperCanopy/juniper_canopy/` | `└── juniper-canopy/` |

Verify Docker build works:

```bash
docker compose config   # Validate compose file
docker compose build juniper-canopy  # Test build
```

**Step 3.2 — juniper-cascor**:

| File | Change |
|------|--------|
| `src/api/websocket/messages.py:10` | `JuniperCanopy's` → `juniper-canopy's` |
| `src/api/lifecycle/monitor.py:3` | `JuniperCanopy` → `juniper-canopy` |
| `src/api/lifecycle/state_machine.py:3` | `JuniperCanopy` → `juniper-canopy` |
| `README.md` | Standardize all `JuniperCanopy` text to `juniper-canopy` |

Notes files (`DECOUPLE_CANOPY_FROM_CASCOR_PLAN.md`, `MONOREPO_ANALYSIS.md`, `INTEGRATION_ROADMAP-01.md`): Update if actively referenced, leave if archived.

**Step 3.3 — juniper-data**:

| File | Change |
|------|--------|
| `README.md` | Standardize `JuniperCanopy` text references to `juniper-canopy` |

**Step 3.4 — juniper-data-client**:

| File | Change |
|------|--------|
| `README.md` | `JuniperCanopy` → `juniper-canopy` |
| `juniper_data_client/__init__.py:4` | `JuniperCanopy` → `juniper-canopy` |
| `juniper_data_client/client.py:4` | `JuniperCanopy` → `juniper-canopy` |

**Step 3.5 — juniper-ml**:

| File | Change |
|------|--------|
| `README.md:53` | `**JuniperCanopy**` → `**juniper-canopy**` |

### Phase 4: Parent Ecosystem Updates

**Step 4.1 — Update `Juniper/CLAUDE.md` and `Juniper/AGENTS.md`**:

Update all references to the Canopy directory path:

| Section | Old | New |
|---------|-----|-----|
| Projects table | `JuniperCanopy/juniper_canopy/` | `juniper-canopy/` |
| Agent File Location table | `JuniperCanopy/juniper_canopy/CLAUDE.md` | `juniper-canopy/CLAUDE.md` |
| Directory Structure tree | `├── JuniperCanopy/` | Remove legacy line or update to `├── juniper-canopy/` |
| Integration Testing | `cd JuniperCanopy/juniper_canopy/src` | `cd juniper-canopy/src` |
| Dependency graph | Any path references | Update |

**Step 4.2 — Update `.vscode/settings.json`** (optional):

The cSpell word `JUNIPERCANOPY` can be updated or removed if no longer needed.

### Phase 5: Validation and Cleanup

**Step 5.1 — Verify all repos**:

```bash
# Canopy tests
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
pytest tests/ -v

# juniper-deploy Docker build
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
docker compose config
docker compose build juniper-canopy

# Cross-repo test suite (if services are running)
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
docker compose up -d
bash scripts/wait_for_services.sh
pytest tests/ -v
docker compose down
```

**Step 5.2 — Global grep for remnants**:

```bash
cd /home/pcalnon/Development/python/Juniper

# Check for old directory path pattern (should return zero results)
grep -rn "JuniperCanopy/juniper_canopy" \
  --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" \
  --include="*.toml" --include="*.conf" --include="*.sh" --include="*.bash" \
  --include="Dockerfile" --include="*.json" \
  --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="worktrees" \
  --exclude-dir="prompts"

# Check for standalone JuniperCanopy (review each hit — some may be intentional display names)
grep -rn "JuniperCanopy" \
  --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" \
  --include="*.toml" --include="*.conf" --include="*.sh" --include="*.bash" \
  --include="Dockerfile" --include="*.json" \
  --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="worktrees" \
  --exclude-dir="prompts" --exclude-dir="notes"
```

If Decision 1 = Option B, the second grep will still return hits for display-name variables and headers. This is expected and correct.

**Step 5.3 — Remove legacy wrapper** (if not done in Phase 2):

```bash
# Final review
ls -la JuniperCanopy/
# Remove after confirming no important files remain
rm -rf JuniperCanopy/
```

**Step 5.4 — Commit and push all repos**:

Commit changes in each affected repo with a consistent message:

```
chore: update JuniperCanopy references to juniper-canopy

Part of the Canopy local directory rename migration from
JuniperCanopy/juniper_canopy to juniper-canopy.
```

---

## 9. Rollback Plan

### Rollback Scope by Phase

| Completed Phase | Rollback Approach |
|----------------|-------------------|
| Phase 1 only (branch not merged) | Delete the branch: `git branch -D chore/rename-local-directory` |
| Phase 2 (merged + moved) | Reverse the move AND revert the merge commit (both required) |
| Phase 3+ (cross-repo changes) | Revert each cross-repo commit individually |

### Full Rollback from Phase 2

If issues are discovered after the directory move, **both** the move and the internal reference changes must be reverted together:

```bash
cd /home/pcalnon/Development/python/Juniper

# Step 1: Reverse the directory move
mkdir -p JuniperCanopy
mv juniper-canopy JuniperCanopy/juniper_canopy

# Step 2: Revert the Phase 1 merge commit (restores old internal references)
cd JuniperCanopy/juniper_canopy
git revert HEAD --no-edit   # HEAD is the merge commit
git push origin main

# Step 3: Verify
git status
git log --oneline -5
```

> **Why both steps are needed**: After Phase 2, the internal references point to the new path (`Juniper/juniper-canopy`). If only the directory is moved back, those references still point to the new path — breaking everything. Reverting the merge commit restores the old references to match the old directory structure.

### Full Rollback from Phase 3+

After cross-repo changes have been committed:

```bash
# Revert each cross-repo commit
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
git revert HEAD --no-edit && git push origin main

cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git revert HEAD --no-edit && git push origin main

# ... repeat for each affected repo

# Then perform the Phase 2 rollback above
```

---

## 10. Post-Migration Verification Checklist

- [ ] `juniper-canopy/` directory exists at `Juniper/juniper-canopy/`
- [ ] `JuniperCanopy/` directory is removed (or archived)
- [ ] `git status` is clean in `juniper-canopy/`
- [ ] `git remote -v` shows correct remote URL
- [ ] `git log` shows full history preserved
- [ ] Canopy pytest suite passes: `cd juniper-canopy/src && pytest tests/ -v`
- [ ] `conf/app_config.yaml` backend_path relative fallback resolves correctly from new location
- [ ] `conf/setup_environment.conf` PROJECT_DIR points to new path
- [ ] Shell scripts source correctly: `source conf/init.conf` works from new location
- [ ] `juniper-deploy/docker-compose.yml` build context updated
- [ ] `docker compose config` validates successfully in `juniper-deploy/`
- [ ] `docker compose build juniper-canopy` succeeds
- [ ] No `JuniperCanopy/juniper_canopy` path references remain (grep confirms)
- [ ] All affected repos committed and pushed
- [ ] Parent `CLAUDE.md` / `AGENTS.md` updated
- [ ] Canopy CLAUDE.md / AGENTS.md updated
- [ ] Canopy worktree procedures (`notes/WORKTREE_SETUP_PROCEDURE.md`, `notes/WORKTREE_CLEANUP_PROCEDURE.md`) created for new path
- [ ] CI workflow `ENV_NAME` updated (if Decision 2 applied)
- [ ] Conda environment YAML names updated (if Decision 2 applied)
