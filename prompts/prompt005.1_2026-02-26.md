# Canopy Repo Rename

Continue the Canopy repository rename migration for the Juniper ecosystem.

## Completed so far

- Full cross-repo audit of all JuniperCanopy references across 7 Juniper repos
- Full internal Canopy audit: 333 references across .py, .conf, .bash, .yaml, .md, Dockerfile
- Identified critical issues: app_config.yaml relative path breakage, phase ordering risk, 42 conf files underestimated
- Wrote comprehensive migration plan with review corrections applied
- Migration plan finalized at: Juniper/juniper-ml/notes/CANOPY_REPO_RENAME_MIGRATION_PLAN.md

## Remaining work

1. Resolve Decision 1 (Section 6): Sub-Project display name in headers/shell variables — keep PascalCase or change to kebab-case? Recommendation is Option B (keep PascalCase for display names, only change paths)
2. Resolve Decision 2 (Section 6): Conda environment name references — update stale JuniperCanopy to JuniperPython? Recommendation is Option A (update to match reality)
3. Execute Phase 0: Pre-migration preparation (clean state, verify worktrees, record HEAD SHA)
4. Execute Phase 1: Canopy internal updates on worktree branch (Steps 1.1–1.15)
5. Execute Phase 2: Atomic merge + directory move (Steps 2.1–2.7)
6. Execute Phase 3: Cross-repo updates (juniper-deploy critical, then cascor/data/data-client/ml)
7. Execute Phase 4: Parent ecosystem CLAUDE.md/AGENTS.md updates
8. Execute Phase 5: Validation, global grep, cleanup

## Key context

- The migration plan document is the single source of truth: Juniper/juniper-ml/notes/CANOPY_REPO_RENAME_MIGRATION_PLAN.md
- READ THAT FILE FIRST — it contains all file paths, line numbers, sed commands, and decision points
- Canopy git repo is at: Juniper/JuniperCanopy/juniper_canopy/ (HEAD: 0f0efe1, branch: main, clean)
- Remote is already correct: git@github.com-juniper-canopy:pcalnon/juniper-canopy.git
- Phase 2 merge and directory move MUST be atomic (no scripts/tests between merge and mv)
- app_config.yaml relative path changes from ../../JuniperCascor/juniper_cascor to ../juniper-cascor (depth changes)
- conf/ has 42 .conf files; ~20 have functional runtime variables beyond headers
- Cassandra cluster name "JuniperCanopy Demo Cluster" in cassandra_client.py:233 should be left unchanged
- Canopy lacks worktree procedure files — create them during Phase 1 Step 1.14

## Verification for new thread

- cat Juniper/juniper-ml/notes/CANOPY_REPO_RENAME_MIGRATION_PLAN.md | head -10  (confirm plan exists)
- cd Juniper/JuniperCanopy/juniper_canopy && git status && git log --oneline -3  (confirm clean state)
- git worktree list  (confirm no active worktrees)

## Git status

All repos on main, clean working directories, no uncommitted work.


Present the two naming decisions to resolve first, then proceed with execution.
