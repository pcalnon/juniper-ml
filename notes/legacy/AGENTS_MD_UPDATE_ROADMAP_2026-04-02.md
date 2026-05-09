# AGENTS.md Update Development Roadmap

**Project**: Juniper / juniper-ml
**Document Version**: 1.0.0
**Date**: 2026-04-02
**Author**: Claude Code (Opus 4.6)
**Related**:

- `notes/AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md`
- `notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md`

---

## Roadmap Overview

All work items for bringing AGENTS.md from v0.2.0 to v0.3.0, organized by priority and phase.

---

## Phase 1: Critical Fixes (Priority: P0)

These items fix incorrect information that would cause confusion or errors for any Claude Code agent reading the AGENTS.md.

### Task 1.1: Bump AGENTS.md version to 0.3.0

- **File**: `AGENTS.md`
- **Change**: Line 3: `**Version**: 0.2.0` -> `**Version**: 0.3.0`
- **Status**: Pending

### Task 1.2: Fix `cly` -> `claudey` rename

- **File**: `AGENTS.md`
- **Change**: Replace `cly` reference with `claudey` — Repo-root symlink to `scripts/claude_interactive.bash` for interactive Claude Code sessions
- **Status**: Pending

### Task 1.3: Fix `scripts/worktree_cleanup.bash` -> `util/worktree_cleanup.bash` relocation

- **File**: `AGENTS.md`
- **Change**: Update file path and description. Update the automated cleanup command in the Worktree Procedures section.
- **Status**: Pending

---

## Phase 2: High-Priority Additions (Priority: P1)

These items document entire directories and systems that are currently invisible to Claude Code agents.

### Task 2.1: Add `util/` directory documentation

- **File**: `AGENTS.md`
- **Change**: Add new "Utility Scripts (`util/`)" section documenting all 22 scripts organized by category
- **Categories**: Worktree management (6), Cascor queries (7), Ecosystem management (2), Git maintenance (2), Documentation validation (2), System utilities (3)
- **Status**: Pending

### Task 2.2: Add `docs/` directory documentation

- **File**: `AGENTS.md`
- **Change**: Add new "Documentation (`docs/`)" section listing all 5 docs files
- **Files**: DOCUMENTATION_OVERVIEW.md, QUICK_START.md, REFERENCE.md, DEVELOPER_CHEATSHEET_JUNIPER-ML.md, DEVELOPER_CHEATSHEET-ORIGINAL.md (deprecated)
- **Status**: Pending

### Task 2.3: Expand CI/CD documentation

- **File**: `AGENTS.md`
- **Change**: Replace single-workflow "Publishing" section with comprehensive "CI/CD Pipelines" section covering all 5 workflows
- **Workflows**: ci.yml, publish.yml, docs-full-check.yml, security-scan.yml, claude.yml
- **Status**: Pending

### Task 2.4: Add Configuration section

- **File**: `AGENTS.md`
- **Change**: Add new "Configuration" section documenting pre-commit hooks, SOPS, markdownlint, Serena, Git LFS, CODEOWNERS, dependabot
- **Status**: Pending

### Task 2.5: Add Repository Structure diagram

- **File**: `AGENTS.md`
- **Change**: Add directory tree showing top-level structure and key subdirectories
- **Status**: Pending

---

## Phase 3: Medium-Priority Updates (Priority: P2)

These items improve completeness and accuracy of existing sections.

### Task 3.1: Update Key Files section

- **File**: `AGENTS.md`
- **Change**: Expand from 10 files to comprehensive categorized listing (~30 key files)
- **Categories**: Package, Documentation, Scripts, Utilities, Tests, CI/CD, Configuration
- **Status**: Pending

### Task 3.2: Update Build & Package Commands with all test commands

- **File**: `AGENTS.md`
- **Change**: Add `test_check_doc_links.py`, `test_worktree_cleanup.py`, pre-commit, and doc validation commands
- **Status**: Pending

### Task 3.3: Document new `scripts/` files

- **File**: `AGENTS.md`
- **Change**: Add `claude_interactive.bash`, `activate_conda_env.bash`, `resume_session.bash`, `sessions/`, `backups/`
- **Status**: Pending

### Task 3.4: Add Secrets Management section

- **File**: `AGENTS.md`
- **Change**: Document SOPS encryption workflow, encrypted files, and reference to `notes/SOPS_USAGE_GUIDE.md`
- **Status**: Pending

### Task 3.5: Document `notes/` subdirectory structure

- **File**: `AGENTS.md`
- **Change**: Add table documenting all 8 subdirectories under `notes/`
- **Status**: Pending

---

## Phase 4: Low-Priority Additions (Priority: P3)

These items add useful context but are not critical for correct operation.

### Task 4.1: Add MCP Server Availability note

- **File**: `AGENTS.md`
- **Change**: Note available MCP servers and reference `.serena/project.yml`
- **Status**: Pending

### Task 4.2: Document ecosystem files

- **File**: `AGENTS.md`
- **Change**: Note `JuniperProject.pid`, `juniper-project-pids.txt`, `images/`, `resources/`, `logs/`
- **Status**: Pending

### Task 4.3: Create `prompts/thread-handoff_automated-prompts/` directory

- **File**: New directory with `.gitkeep`
- **Change**: Create the directory referenced in the automated thread handoff workflow
- **Status**: Pending

---

## Phase 5: Validation (Priority: P0)

### Task 5.1: Verify all file paths in updated AGENTS.md exist

- **Method**: Manual path verification or `util/check_doc_links.py`
- **Status**: Pending

### Task 5.2: Run full test suite

- **Commands**:
  - `python3 -m unittest -v tests/test_wake_the_claude.py`
  - `python3 -m unittest -v tests/test_check_doc_links.py`
  - `python3 -m unittest -v tests/test_worktree_cleanup.py`
  - `bash scripts/test_resume_file_safety.bash`
- **Status**: Pending

### Task 5.3: Run pre-commit hooks

- **Command**: `pre-commit run --all-files`
- **Status**: Pending

### Task 5.4: Cross-reference consistency check

- Verify AGENTS.md aligns with docs/DOCUMENTATION_OVERVIEW.md
- Verify AGENTS.md aligns with docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md
- Verify version consistency across AGENTS.md, pyproject.toml, CHANGELOG.md
- **Status**: Pending

---

## Phase 6: Commit, Push, and PR (Priority: P0)

### Task 6.1: Commit all changes

- Branch: `worktree-structured-coalescing-squirrel`
- Files: AGENTS.md, notes/AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md, notes/AGENTS_MD_UPDATE_PLAN_2026-04-02.md, notes/AGENTS_MD_UPDATE_ROADMAP_2026-04-02.md
- **Status**: Pending

### Task 6.2: Push to remote

- **Command**: `git push origin worktree-structured-coalescing-squirrel`
- **Status**: Pending

### Task 6.3: Create pull request

- **Title**: "docs: update AGENTS.md to v0.3.0 addressing comprehensive drift"
- **Base**: main
- **Head**: worktree-structured-coalescing-squirrel
- **Status**: Pending

### Task 6.4: Post-merge worktree cleanup

- Follow `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`
- **Status**: Pending (post-merge)

---

## Task Status Summary

| Phase | Tasks | Priority | Status |
|-------|-------|----------|--------|
| Phase 1: Critical Fixes | 3 | P0 | Pending |
| Phase 2: High-Priority Additions | 5 | P1 | Pending |
| Phase 3: Medium-Priority Updates | 5 | P2 | Pending |
| Phase 4: Low-Priority Additions | 3 | P3 | Pending |
| Phase 5: Validation | 4 | P0 | Pending |
| Phase 6: Commit, Push, PR | 4 | P0 | Pending |
| **Total** | **24** | | |
