# AGENTS.md Update Plan

**Project**: Juniper / juniper-ml
**Document Version**: 1.0.0
**Date**: 2026-04-02
**Author**: Claude Code (Opus 4.6)
**Related**: `notes/AGENTS_MD_DRIFT_ANALYSIS_2026-04-02.md`

---

## Objective

Bring the juniper-ml AGENTS.md file into full alignment with the current codebase state (v0.3.0), addressing all 15 categories of drift identified in the analysis document.

---

## Phase 1: Version and Identity Updates

### Step 1.1: Update version header

- Change `**Version**: 0.2.0` to `**Version**: 0.3.0`
- Confirm this matches `pyproject.toml` `[project].version`

### Step 1.2: Fix file references

- Replace `cly` with `claudey` and update description to reference `scripts/claude_interactive.bash`
- Replace `scripts/worktree_cleanup.bash` with `util/worktree_cleanup.bash` and update description

---

## Phase 2: Structural Additions

### Step 2.1: Add complete directory layout

Add a "Repository Structure" section showing the full directory tree:

```
juniper-ml/
├── .github/workflows/     # CI/CD pipelines (5 workflows)
├── .serena/               # Serena code agent config
├── docs/                  # User-facing documentation
├── images/                # Project branding and logos
├── logs/                  # Runtime log output
├── notes/                 # Development notes, plans, procedures
│   ├── backups/           # Backup analysis documents
│   ├── concurrency/       # Concurrency handoff notes
│   ├── development/       # Development analysis documents
│   ├── documentation/     # Documentation audit plans
│   ├── history/           # Historical plans and procedures
│   ├── proposals/         # Research proposals
│   ├── pull_requests/     # PR description archives
│   └── templates/         # Document templates
├── prompts/               # Claude Code session prompts
├── resources/             # External resources
├── scripts/               # Claude Code launcher and test scripts
│   ├── backups/           # Backup copies of older scripts
│   └── sessions/          # Session ID storage
├── tests/                 # Regression test suites
└── util/                  # Utility scripts and tools
```

### Step 2.2: Add `docs/` directory section

Document all 5 files in docs/ with their versions and purposes.

### Step 2.3: Add `util/` directory section

Document all utility scripts organized by category:
- Worktree management (6 scripts)
- Cascor service queries (7 scripts)
- Ecosystem management (2 scripts)
- Git maintenance (2 scripts)
- Documentation validation (2 scripts)
- System utilities (3 scripts)

### Step 2.4: Update `scripts/` documentation

Add the 3 new scripts and 2 new subdirectories not currently documented.

---

## Phase 3: CI/CD and Configuration

### Step 3.1: Expand CI/CD section

Replace the single-workflow "Publishing" section with a comprehensive "CI/CD" section covering all 5 workflows:
- `ci.yml` — Main CI pipeline
- `publish.yml` — PyPI publishing (existing, update)
- `docs-full-check.yml` — Weekly documentation validation
- `security-scan.yml` — Weekly security scanning
- `claude.yml` — Claude Code issue/PR automation

### Step 3.2: Add Configuration section

Document:
- `.pre-commit-config.yaml` — Hook groups and setup commands
- `.markdownlint.yaml` — Linting rules
- `.sops.yaml` — SOPS encryption config
- `.serena/project.yml` — Serena integration
- `.gitattributes` — Git LFS for images
- `.github/CODEOWNERS` — Code ownership
- `.github/dependabot.yml` — Automated dependency updates
- `MANIFEST.in` — Distribution includes

### Step 3.3: Add Secrets Management section

Document the SOPS encryption workflow:
- What is encrypted (`.env`, `.env.secrets`)
- How to decrypt/encrypt
- Reference `notes/SOPS_USAGE_GUIDE.md`
- Pre-commit hook that blocks unencrypted env files

---

## Phase 4: Key Files and Commands Updates

### Step 4.1: Update Key Files section

Reorganize into categorized subsections:
- Package metadata
- Documentation
- Scripts and launchers
- Utilities
- Tests
- CI/CD
- Configuration

### Step 4.2: Update Build & Package Commands

Add all test commands:

```bash
# Run all tests
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_check_doc_links.py
python3 -m unittest -v tests/test_worktree_cleanup.py
bash scripts/test_resume_file_safety.bash

# Run pre-commit hooks
pre-commit run --all-files

# Validate documentation links
python util/check_doc_links.py --exclude templates --exclude history
```

---

## Phase 5: Operational Additions

### Step 5.1: Add MCP Server Availability note

List available MCP servers that Claude Code sessions can access, referencing `.serena/project.yml` for the Serena configuration.

### Step 5.2: Verify `notes/` procedure references

Confirm all referenced procedure files exist and are current:
- `notes/WORKTREE_SETUP_PROCEDURE.md`
- `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`
- `notes/THREAD_HANDOFF_PROCEDURE.md`

### Step 5.3: Create missing directories

Create `prompts/thread-handoff_automated-prompts/` with `.gitkeep` if automated thread handoff is desired (optional, per user's prompt).

---

## Phase 6: Validation

### Step 6.1: Internal consistency check

- Every file path referenced in AGENTS.md exists in the repository
- Every key script/config file in the repository is documented
- Version numbers are consistent across AGENTS.md, pyproject.toml, CHANGELOG.md
- All test commands execute successfully

### Step 6.2: Cross-reference check

- Verify AGENTS.md aligns with `docs/DOCUMENTATION_OVERVIEW.md`
- Verify AGENTS.md aligns with `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
- Verify worktree procedure references are current

### Step 6.3: Run test suite

```bash
python3 -m unittest -v tests/test_wake_the_claude.py
python3 -m unittest -v tests/test_check_doc_links.py
python3 -m unittest -v tests/test_worktree_cleanup.py
bash scripts/test_resume_file_safety.bash
```

---

## Phase 7: Finalization

### Step 7.1: Commit changes

- Commit AGENTS.md update and all deliverable documents
- Push working branch to remote

### Step 7.2: Create pull request

- PR title: "docs: update AGENTS.md to v0.3.0 addressing comprehensive drift"
- Include summary of all changes in PR body

### Step 7.3: Post-merge cleanup

- Follow `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`

---

## Dependencies and Risks

| Risk | Mitigation |
|------|-----------|
| AGENTS.md becomes too long and unwieldy | Organize into clear sections with table of contents; keep descriptions concise |
| Referenced files may change during update | Verify all paths at end of process |
| Thread context limits during implementation | Phase work for natural handoff points |
| Pre-commit hooks may fail on new/modified files | Run `pre-commit run --all-files` before commit |

---

## Estimated Scope

| Phase | Items | Complexity |
|-------|-------|------------|
| Phase 1: Version and Identity | 2 steps | Low |
| Phase 2: Structural Additions | 4 steps | High |
| Phase 3: CI/CD and Configuration | 3 steps | Medium |
| Phase 4: Key Files and Commands | 2 steps | Medium |
| Phase 5: Operational Additions | 3 steps | Low |
| Phase 6: Validation | 3 steps | Medium |
| Phase 7: Finalization | 3 steps | Low |
