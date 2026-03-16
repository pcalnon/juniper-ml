# Documentation Audit V2 — Item Disposition

**Date**: 2026-03-14
**Context**: Phase 1.1.4 of the Documentation Audit and Upgrade Plan
**Reference**: `notes/DOCUMENTATION_AUDIT_V2_PLAN.md`

---

## Phase 0 Status: RESOLVED

The 501 uncommitted files from the PascalCase/kebab-case conversion have been fully reverted. All 8 repos are clean on `main` with correct `CLAUDE.md` symlinks.

---

## Item Disposition Summary

| Status | Count | Items |
|--------|-------|-------|
| COMPLETE | 7 | R-03, R-07, R-16, R-18, R-20, R-24, R-26, R-39 |
| COMPLETE (this session) | 3 | R-01, R-17, R-25 |
| PARTIALLY COMPLETE | 1 | R-27 |
| DEFERRED (non-blocking) | 36 | All remaining items |

---

## Detailed Disposition

### COMPLETE (Previously Committed)

| ID | Description | Evidence |
|----|-------------|----------|
| R-03 | Fix AGENTS.md file references (ws_client.py) | Committed to juniper-cascor-client |
| R-20 | Fix CI badge URLs in docs/ci/reference.md | Committed to juniper-cascor |
| R-24 | Fix README Python version (>=3.12) | README.md and pyproject.toml both say >=3.12 |
| R-26 | Fix env var defaults in AGENTS.md | Committed to juniper-cascor-worker |
| R-39 | Fix template placeholder URLs (your-org) | No "your-org" found in juniper-ml or juniper-deploy |

### COMPLETE (Resolved as False Positive or Already Fixed)

| ID | Description | Finding |
|----|-------------|---------|
| R-07 | Fix port 8050→8100 in juniper-data docs | FALSE POSITIVE. Port 8050 correctly refers to juniper-canopy as a consumer. juniper-data is consistently shown as 8100. |
| R-16 | Fix docs/CONSTANTS_GUIDE.md link in canopy AGENTS.md | ALREADY FIXED. AGENTS.md already uses correct `docs/cascor/CONSTANTS_GUIDE.md` path. 3 stale refs remain in peripheral files (notes/, CHANGELOG) — deferred as non-critical historical cleanup. |
| R-18 | Fix notes/DEVELOPMENT_ROADMAP.md refs in canopy | ALREADY FIXED. AGENTS.md links correctly point to `notes/JUNIPER-CANOPY_POST-RELEASE_DEVELOPMENT-ROADMAP.md`. ~12 stale refs remain in docs/ and notes/ — deferred to Phase 3 documentation audit. |

### COMPLETE (Fixed This Session — 2026-03-14)

| ID | Description | Action Taken |
|----|-------------|--------------|
| R-01 | Remove misplaced Canopy docs in juniper-data | Deleted `juniper-data/docs/history/TASK_2025-12-04.txt`. Original claim of "~30 misplaced files" was inaccurate — only 1 file was genuinely misplaced. Other canopy references are legitimate cross-project documentation. |
| R-17 | Fix stale src/constants.py reference in canopy | Fixed 1 line in AGENTS.md (line 291: `constants.py` → `canopy_constants.py`) and 4 occurrences in `docs/cascor/CONSTANTS_GUIDE.md`. |
| R-25 | Fix AGENTS.md version in juniper-data-client | Updated version from 0.3.1 to 0.3.2 to match pyproject.toml. |

### PARTIALLY COMPLETE

| ID | Description | Status |
|----|-------------|--------|
| R-27 | Create missing CHANGELOG.md | juniper-cascor-client: DONE. juniper-cascor-worker: STILL NEEDED. juniper-deploy: STILL NEEDED. |

### DEFERRED (Non-Blocking for Phases 2–5)

These items are deferred because they either:
- (a) Do not conflict with Phases 2–5 of the Documentation Audit and Upgrade Plan
- (b) Will be addressed naturally by Phase 3 (documentation consistency audit)
- (c) Affect only historical/peripheral files

| ID | Description | Reason for Deferral |
|----|-------------|---------------------|
| R-02 | Resolve version chaos in juniper-cascor | Will be addressed in Phase 3 AGENTS.md consistency audit |
| R-04 | Fix juniper-deploy GitHub URLs | Cross-cutting; Phase 3.4 cross-project alignment |
| R-05 | Fix underscore GitHub URLs | Phase 3.4 |
| R-06 | Fix worktree procedure conda env name | Phase 3.3 procedural docs audit |
| R-08 | Fix port in test fixture | Code fix, not documentation |
| R-09 | Update Documentation Files table | Phase 3.2 docs content audit |
| R-10 | Remove stale directory structure | Phase 3.2 |
| R-11 | Rewrite Legacy Directories table | Phase 3.4 parent directory |
| R-12 | Update Parent Directory Structure tree | Phase 3.4 parent directory |
| R-13 | Converge THREAD_HANDOFF_PROCEDURE.md | Phase 3.3 procedural docs audit |
| R-14 | Document conda environment split | Phase 3.4 parent directory |
| R-15 | Document Python version split | Phase 3.4 parent directory |
| R-19 | Fix conda env name in cascor docs | Phase 3.2 |
| R-21 | Fix README version in canopy | Phase 3.2 |
| R-22 | Fix AGENTS.md version in juniper-data | Phase 3.2 |
| R-23 | Fix README formatting tool docs | Phase 3.2 |
| R-27 | Create CHANGELOG.md (remaining 2 repos) | Phase 3.2 |
| R-28 | Fix env var "Used By" columns | Phase 3.4 parent directory |
| R-29 | Rewrite line length convention | Phase 3.4 parent directory |
| R-30 | Converge worktree procedures | Phase 3.3 |
| R-31 | Update "Amp sessions" references | Phase 3.3 |
| R-32 | Fix THREAD_HANDOFF wording | Phase 3.3 |
| R-33 | Fix port env var docs in canopy | Phase 3.2 |
| R-34 | Fix docs/history/INDEX.md references | Phase 3.3 |
| R-35 | Fix template CHANGELOG.md link path | Phase 3.3 |
| R-36 | Fix notes/history relative links | Phase 3.3 |
| R-37 | Add architectural dependency note | Phase 3.4 parent directory |
| R-38 | Note JUNIPER_DATA_URL default varies | Phase 3.4 parent directory |
| R-40 | Fix root dir name in juniper-data docs | Phase 3.2 |
| R-41 | Extract AGENTS.md template sections | Phase 3.2 |
| R-42 | Add version header to AGENTS.md files | Phase 3.2 |
| R-43 | Update Python badge in cascor | Phase 3.2 |
| R-44 | Update repo count in parent docs | Phase 3.4 parent directory |
| R-45 | Update STEP_7_4 plan status | Phase 3.4 parent directory |
| R-46 | Fix dead Dependabot URLs | Phase 3.4 |
| R-47 | Fix docs/history file count claim | Phase 3.2 |

---

## Phase 1.1 Success Criteria Assessment

| Criterion | Status |
|-----------|--------|
| All V2 items classified (COMPLETE/STILL REQUIRED/DEFERRED) | **MET** |
| No uncommitted changes in any repo | **MET** (2 untracked files: `prompts/bla` in juniper-ml, `.coverage` in juniper-deploy — neither related) |
| R-01 resolved | **MET** (1 file deleted; original scope was overstated) |
| R-07 resolved | **MET** (false positive — no fix needed) |
| R-16 resolved | **MET** (already fixed in AGENTS.md) |
| R-17 resolved | **MET** (fixed this session) |
| R-18 resolved | **MET** (already fixed in AGENTS.md) |
| Deferred items assessed for Phase 2–5 conflicts | **MET** (none conflict) |

**Conclusion**: Phase 1.1 is COMPLETE. Phase 2 is unblocked.
