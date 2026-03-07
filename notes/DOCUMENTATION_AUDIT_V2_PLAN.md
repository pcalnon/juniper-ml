# Juniper Documentation Audit v2 - Implementation Plan

**Created**: 2026-03-02
**Author**: Paul Calnon (via Claude Code)
**Scope**: All 8 active repositories + parent directory
**Status**: Approved for execution

---

## Context

A project-wide search-and-replace converted PascalCase repo names (e.g., `JuniperCascor`) to kebab-case (`juniper-cascor`) across all 8 repos. While correct for many prose references, this broke:

- **Conda env names**: `JuniperCascor` -> `juniper-cascor` (no such env exists)
- **Python class names**: `JuniperDataClient` -> `juniper-dataClient` (invalid Python)
- **CLAUDE.md symlinks**: Replaced with full file copies
- **Historical references**: Where old PascalCase names were correct context

501 files are modified across 8 repos (uncommitted). A prior audit (2026-03-02) produced 47 remediation items (R-01 through R-47), many already committed. This iteration reverts the search-and-replace damage, then systematically audits and fixes all documentation.

### Audit Criteria

1. **Validate links**: Internal anchors, cross-doc links, cross-app links, external URLs
2. **Validate directory structures**: Trees, paths, filenames
3. **Validate referenced tools**: Conda envs (PascalCase), toolsets, MCP servers, utility scripts
4. **Validate documented procedures**: Commands, URLs, paths, configs, envs
5. **Validate repo name replacements**: Revert incorrect kebab-case back to PascalCase where appropriate

### Decisions

- **Revert scope**: Revert ALL uncommitted changes (code + docs) via `git checkout -- .`
- **Deploy URLs**: Annotate `juniper-deploy` clone URLs as "(private repository)"
- **Branch strategy**: Worktree branches per-repo (`docs/audit-v2`)
- **Config files**: Include `.conf` files with wrong conda env names in scope
- **Commit strategy**: Single commit per repo with descriptive message

---

## Phase 0: Revert Working Tree Contamination (PREREQUISITE)

**All 8 repos** — Revert all uncommitted changes via `git checkout -- .`

### Steps

1. For each repo:
   ```bash
   cd /home/pcalnon/Development/python/Juniper/<repo>
   git checkout -- .
   ```

2. Verify symlinks restored:
   ```bash
   for repo in juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-ml juniper-canopy juniper-deploy; do
     ls -la /home/pcalnon/Development/python/Juniper/$repo/CLAUDE.md
   done
   ```
   Each should show `CLAUDE.md -> AGENTS.md`.

3. Verify Python code integrity:
   ```bash
   cd /home/pcalnon/Development/python/Juniper/juniper-data-client
   python -c "from juniper_data_client import JuniperDataClient; print('OK')"
   cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
   python -c "from juniper_cascor_client import JuniperCascorClient; print('OK')"
   ```

4. Verify `git status` shows clean working tree (only untracked files OK).

---

## Phase 1: juniper-cascor

**Worktree branch**: `docs/audit-v2`
**Conda env**: `JuniperCascor`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| `README.md` | `conda activate juniper-cascor` -> `JuniperCascor`; annotate juniper-deploy clone URL as private |
| `docs/install/quick-start.md` | `conda activate juniper-cascor` -> `JuniperCascor` |
| `docs/install/environment-setup.md` | Same conda env fix |
| `docs/testing/environment-setup.md` | Same conda env fix |
| `docs/ci/environment-setup.md` | Same conda env fix |
| `notes/setup_config_guides/forkserver_fix.md` | 8 instances of conda env name fix |
| `docs/DOCUMENTATION_OVERVIEW.md` | Verify directory tree, GitHub URLs |
| `docs/index.md` | Verify GitHub URLs (underscore vs hyphen) |
| `docs/ci/reference.md` | Verify badge URLs (R-20 committed) |
| `.conf` files | Check `CONDA_ENV_NAME` correctness |
| All docs/ | Verify `JuniperDataClient` class names correct after revert |
| AGENTS.md | Verify all paths in Key Entry Points / Documentation Files tables |

### Verification

```bash
grep -rn "conda activate juniper-" docs/ README.md AGENTS.md notes/ --include="*.md" | grep -v history/
grep -rn "juniper-dataClient\|juniper-cascorClient" docs/ --include="*.md"
```

---

## Phase 2: juniper-canopy

**Worktree branch**: `docs/audit-v2`
**Conda env**: `JuniperPython`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| `README.md` | `conda activate juniper-canopy` -> `conda activate JuniperPython`; annotate deploy URL; R-21: version 0.25.0 -> 0.3.0 |
| `.github/instructions/copilot-instructions.md` | `JuniperCanopy` -> `JuniperPython` (3 instances) |
| `notes/CONDA_DEPENDENCY_FILE_HEADER.md` | `name: juniper-canopy` -> `name: JuniperPython` |
| `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md` | `name: juniper-canopy` conda ref |
| AGENTS.md | R-16: `docs/CONSTANTS_GUIDE.md` -> `docs/cascor/CONSTANTS_GUIDE.md` |
| AGENTS.md | R-17: `src/constants.py` -> `src/canopy_constants.py` |
| AGENTS.md | R-18: `notes/DEVELOPMENT_ROADMAP.md` -> `notes/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md` |
| `notes/templates/TEMPLATE_SECURITY_RELEASE_NOTES.md` | R-35: `../CHANGELOG.md` -> `../../CHANGELOG.md` |
| `.conf` files | Check conda env name correctness in conf/init.conf, setup scripts |

### Verification

```bash
grep -rn "conda activate juniper-" README.md docs/ notes/ --include="*.md"
grep -rn "JuniperCanopy" .github/ notes/ docs/ --include="*.md"
```

---

## Phase 3: juniper-data

**Worktree branch**: `docs/audit-v2`
**Conda env**: `JuniperData`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| `docs/QUICK_START.md` | `conda activate juniper-data` -> `JuniperData`; version 0.4.0 -> 0.4.2; clone URL fix |
| `README.md` | R-23: verify ruff vs black/isort docs; annotate deploy URL |
| `docs/CONSTANTS_GUIDE.md` | R-07: Fix port 8050 -> 8100 (or flag as canopy artifact for removal) |
| `docs/api/API_REFERENCE.md` | R-07: Fix port 8050 -> 8100 (or flag as canopy artifact) |
| `docs/` directory broadly | R-01: Audit for canopy documentation that doesn't belong (MAJOR - flag/annotate/remove) |
| `.conf` files | Check conda env name correctness |

### R-01 Assessment

The entire `docs/` directory (~30 files) in juniper-data contains documentation written for juniper-canopy. Only `docs/api/JUNIPER_DATA_API.md`, `docs/QUICK_START.md`, and `docs/api/API_SCHEMAS.md` are genuine juniper-data content. Strategy:
- Keep genuine juniper-data docs
- Add a `docs/README.md` noting which files are placeholder/canopy-era and pending rewrite
- Do NOT delete files in this pass (too destructive for a docs audit)

### Verification

```bash
grep -rn "conda activate juniper-" docs/ README.md --include="*.md"
grep -rn "8050\|Canopy\|canopy" docs/ --include="*.md" | head -20
```

---

## Phase 4: juniper-data-client

**Worktree branch**: `docs/audit-v2`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| All .md files | Verify `JuniperDataClient`/`JuniperDataError` class names restored after Phase 0 revert |
| README.md | R-24: Python version >=3.11 -> >=3.12 (verify if already committed) |
| AGENTS.md | R-25: Version 0.3.0 -> 0.3.1 (verify if already committed) |

### Verification

```bash
grep -rn "juniper-dataClient\|juniper-dataError" --include="*.md"
```

---

## Phase 5: juniper-cascor-client

**Worktree branch**: `docs/audit-v2`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| AGENTS.md | R-03: Verify `training_stream.py`/`control_stream.py` -> `ws_client.py` fix (committed) |
| All .md files | Verify `JuniperCascorClient`/`JuniperCascorClientError` class names |
| CHANGELOG.md | R-27: Verify exists (committed) |

### Verification

```bash
grep -rn "juniper-cascorClient\|juniper-cascorError\|training_stream\|control_stream" --include="*.md"
```

---

## Phase 6: juniper-cascor-worker

**Worktree branch**: `docs/audit-v2`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| AGENTS.md | R-26: Verify env var defaults fix (committed) |
| CHANGELOG.md | R-27: Verify exists |
| All .md files | Check for PascalCase class name corruption |

---

## Phase 7: juniper-ml

**Worktree branch**: `docs/audit-v2`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| `notes/MICROSERVICES-ARCHITECTURE_DEVELOPMENT-ROADMAP.md` | ~30 `juniper-dataClient`/`juniper-cascorClient` instances (verify revert fixes these) |
| `notes/CANOPY_REPO_RENAME_MIGRATION_PLAN.md` | Leave as-is (this doc analyzes the rename; kebab examples are intentional) |
| README.md | R-39 deploy link fix (verify committed); annotate deploy URL as private |

### Verification

```bash
grep -rn "juniper-dataClient\|juniper-cascorClient" --include="*.md"
```

---

## Phase 8: juniper-deploy

**Worktree branch**: `docs/audit-v2`

### Files to Audit and Fix

| File | Issues |
|------|--------|
| README.md | Env var documentation completeness |
| AGENTS.md | Verify env vars match docker-compose.yml |
| CHANGELOG.md | R-27: Verify exists |
| All docs | 8 undocumented env vars found in code - add to AGENTS.md |

---

## Phase 9: Parent Directory

**No worktree** — parent is not a git repo; edit files directly.

### Files to Audit and Fix

| File | Issues |
|------|--------|
| `AGENTS.md`/`CLAUDE.md` | Verify conda env table, legacy directory table, directory structure tree |
| `AGENTS.md` | R-37: Add architectural dependency note for cascor-worker |
| `AGENTS.md` | R-38: Add JUNIPER_DATA_URL context-dependent default note |
| `notes/WORKTREE_IMPLEMENTATION_PLAN.md` | R-44: Update repo count 7 -> 8 |
| `notes/STEP_7_4_OBSERVABILITY_FOUNDATION_PLAN.md` | R-45: Update status |

---

## Phase 10: Cross-Repo Verification Sweep

Run global checks after all per-repo work:

### 10.1 Conda Environment Names
```bash
grep -rn "conda activate" juniper-*/README.md juniper-*/docs/**/*.md juniper-*/notes/WORKTREE_SETUP_PROCEDURE.md
```

Expected correct mappings:

| Repo | Env Name |
|------|----------|
| juniper-cascor | `JuniperCascor` |
| juniper-data | `JuniperData` |
| juniper-canopy | `JuniperPython` |

### 10.2 PascalCase Class Names
```bash
grep -rn "juniper-[a-zA-Z]*Client\|juniper-[a-zA-Z]*Error" juniper-*/ --include="*.md" | grep -v legacy | grep -v audit_data | grep -v history
```
Expected: zero matches.

### 10.3 GitHub URL Underscore Check
```bash
grep -rn "github.com/pcalnon/juniper_" juniper-*/ --include="*.md" | grep -v legacy | grep -v audit_data
```
Expected: zero matches.

### 10.4 Deploy URL Annotation
Verify all `github.com/pcalnon/juniper-deploy` references are annotated as private.

### 10.5 Version Consistency
For each repo, verify AGENTS.md/README.md version matches `pyproject.toml`.

---

## Execution Summary

| Phase | Repo | Priority | Dependencies |
|-------|------|----------|-------------|
| 0 | All 8 repos | BLOCKER | None |
| 1 | juniper-cascor | Critical | Phase 0 |
| 2 | juniper-canopy | Critical | Phase 0 |
| 3 | juniper-data | High | Phase 0 |
| 4 | juniper-data-client | High | Phase 0 |
| 5 | juniper-cascor-client | Medium | Phase 0 |
| 6 | juniper-cascor-worker | Medium | Phase 0 |
| 7 | juniper-ml | Medium | Phase 0 |
| 8 | juniper-deploy | Medium | Phase 0 |
| 9 | Parent directory | Low | Phases 1-8 |
| 10 | Cross-repo verification | Required | Phases 1-9 |
