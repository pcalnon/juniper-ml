# Requirements — TOOL

**Area**: dev tooling / scripts / workflow — worktree procs, claude-code launchers

**Total entries**: 45

**By status**: proposed=40 | shipped=5

**By priority**: P0=1 | P1=4 | P2=38 | P3=2

**By owner**: ml=36 | cwk=3 | cas=2 | dat=2 | dep=2

---

### JR-CAS-TOOL-001 — Fix ./try convenience script path resolution errors in helper scripts.

**Status**: proposed  **Priority**: P0  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/history/DEVELOPMENT_ROADMAP.md` (lines 201-252)

**Detail**:

Helper scripts (GET_OS_SCRIPT, GET_PROJECT_SCRIPT, DATE_FUNCTIONS_SCRIPT) are overridden as bare filenames. Fix to use absolute paths derived from BASH_SOURCE[0]. Update conf/script_util.cfg to correctly compute ROOT_PROJECT_DIR with proper project hierarchy.

### JR-DAT-TOOL-001 — Line length normalized to 120 characters in [tool.ruff] as single source of truth.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 390-408)

**Notes**:

RD-013 complete 2026-02-25. 24 files reformatted. Current value 320 per 2026-03-15 audit.

### JR-DAT-TOOL-002 — Linter migrated from flake8+isort+black+pyupgrade to ruff v0.15.2.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: dat

**Sources**:
- `juniper-data/notes/JUNIPER-DATA_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 359-388)

**Notes**:

RD-012 complete 2026-02-25. 2 ruff hooks replace 5 pre-commit hooks. All 700 tests pass.

### JR-CWK-TOOL-001 — Worktree cleanup procedure with CWD continuity: create new worktree before removing old one to avoid trapping Claude Code sessions in invalid paths.

**Status**: shipped  **Priority**: P1  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (lines 1-15)

**Detail**:

The V1 procedure (see notes/history/WORKTREE_CLEANUP_PROCEDURE_V1.md) removed the worktree directory without first creating a replacement, leaving the session trapped. V2 creates a new worktree and switches CWD before removing the old one (Phase 2 must complete before Phase 4). Phases: 1 Save & Push, 2 Create New Worktree (session continuity gate), 3 Merge & Pull Request, 4 Remove Old Worktree (prerequisite: new CWD verified), 5 Verify.

**Design**:

Phase 2 is the critical gate: CWD must move to the new worktree (Step 5) before the old one is removed (Phase 4, Step 9). The procedure enforces this with explicit verification gates in Step 6.

### JR-DEP-TOOL-001 — Create juniper-ctl CLI wrapper for systemd management (start/stop/restart/logs/health/resources).

**Status**: proposed  **Priority**: P1  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/PHASE2_SYSTEMD_IMPLEMENTATION_PLAN.md` (lines 256-274)

**Detail**:

Management CLI wrapping systemctl --user commands with 10+ subcommands:
start/stop/restart (single or all), status (all services), logs/follow, health (latest checks),
resources (CPU/memory/IO usage), install (symlink units + daemon-reload), enable/disable (auto-start).

### JR-CWK-TOOL-002 — Thread handoff procedure: preserve context fidelity when thread compaction degrades output by proactively handing off to fresh thread before context saturation.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/THREAD_HANDOFF_PROCEDURE.md` (lines 1-35)

**Detail**:

Thread compaction introduces information loss (subtle decisions, edge cases, partial progress, reasoning get dropped). Triggers: (1) context saturation after 15+ tool calls or 5+ file edits, (2) phase boundary completion, (3) degraded recall (re-reading files), (4) multi-module transitions, (5) user request. Do NOT handoff when task is nearly complete (<2 steps) or thread is still sharp. Handoff goal structure: original task, completed items, remaining work, key discoveries, file paths.

**Design**:

Handoff protocol: (1) Checkpoint current state (task, completed, remaining, discovered, files in play), (2) Compose concise actionable goal (be specific, include paths, state decisions, mention test status, keep <500 words), (3) Present to user via handoff() tool if available (follow=true for current thread stop, follow=false rare).

### JR-CWK-TOOL-003 — Worktree setup procedure: standardized protocol for creating git worktrees when beginning a new task, centralizing worktrees in /home/pcalnon/Development/python/Juniper/worktrees/.

**Status**: shipped  **Priority**: P2  **Category**: TOOL  **Owner**: cwk

**Sources**:
- `juniper-cascor-worker/notes/WORKTREE_SETUP_PROCEDURE.md` (lines 1-30)

**Detail**:

Prerequisites: must be in primary directory (not already in worktree), working tree clean, target branch not already checked out elsewhere. Protocol: (1) Ensure clean state, (2) Fetch and update parent branch (typically main), (3) Create working branch, (4) Compute worktree directory name using format <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>, (5) Create worktree, (6) Verify and begin work.

**Design**:

Naming convention: <repo-name>--<branch-name>--<YYYYMMDD-HHMM>--<short-hash>. All worktrees in /home/pcalnon/Development/python/Juniper/worktrees/. Example: juniper-cascor-worker--feature--add-gpu-support--20260225-1430--047c3f61.

### JR-ML-TOOL-001 — CLN-CC-01: Delete Legacy `remote_client/` Directory.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1317-1343)

### JR-ML-TOOL-002 — CLN-CC-02: Delete Stale `check.py` Duplicate (600 Lines).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1346-1361)

### JR-ML-TOOL-003 — CLN-CC-03: Remove 9 Local `import traceback` in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1364-1378)

### JR-ML-TOOL-004 — CLN-CC-04: Enable mypy Strict Mode.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1381-1395)

### JR-ML-TOOL-005 — CLN-CC-05: Legacy Spiral Code — Trivial Getter/Setter Methods, No @deprecated.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1398-1412)

### JR-ML-TOOL-006 — CLN-CC-06: Remove "Roll" Concept in CandidateUnit.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1415-1421)

### JR-ML-TOOL-007 — CLN-CC-07: Candidate Factory Refactor.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1424-1430)

### JR-ML-TOOL-008 — CLN-CC-08: Remove Commented-Out Code Blocks.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1433-1439)

### JR-ML-TOOL-009 — CLN-CC-09: Line Length Reduction to 120 Characters.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1442-1448)

### JR-ML-TOOL-010 — CLN-CC-10: `utils.py:238` — Broken `check_object_pickleability` Uses `dill` Not in Deps.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1451-1473)

### JR-ML-TOOL-011 — CLN-CC-11: `snapshot_serializer.py` — Extend Optimizer Support (In-Code TODO).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1476-1490)

### JR-ML-TOOL-012 — CLN-CC-12: `.ipynb_checkpoints` Directories Committed to Repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1493-1507)

### JR-ML-TOOL-013 — CLN-CC-13: `sys.path.append` at Module Level in cascade_correlation.py.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1510-1524)

### JR-ML-TOOL-014 — CLN-CC-14: Empty `# TODO :` Headers in 18+ Files.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1527-1541)

### JR-ML-TOOL-015 — CLN-CC-15: `_object_attributes_to_table` Return Type Annotation Wrong.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1544-1558)

### JR-ML-TOOL-016 — CLN-CN-01: `theme-table` CSS Class Never Implemented.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1563-1588)

### JR-ML-TOOL-017 — CLN-CN-02: NPZ Validation Only in DemoMode, Not ServiceBackend.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1591-1605)

### JR-ML-TOOL-018 — CLN-CN-03: Performance Test Suite Minimal.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1608-1622)

### JR-ML-TOOL-019 — CLN-CN-04: JuniperData-Specific Error Handling Missing.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1625-1639)

### JR-ML-TOOL-020 — CLN-CN-05: DashboardManager Extraction (3,232 → Component Classes).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1642-1657)

### JR-ML-TOOL-021 — CLN-CN-06: Re-enable Remaining MyPy Disabled Codes.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1660-1674)

### JR-ML-TOOL-022 — CLN-CN-07: Real Backend Path Test Coverage.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1677-1691)

### JR-ML-TOOL-023 — CLN-CN-08: Convert Skipped Integration Tests (4 Files with `requires_server`).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1694-1708)

### JR-ML-TOOL-024 — CLN-CN-09: main.py Coverage Gap (84% vs 95% Target).

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1711-1725)

### JR-ML-TOOL-025 — CLN-CN-10: `main.py` Is 2,543 Lines — Second God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1728-1742)

### JR-ML-TOOL-026 — CLN-CN-11: `metrics_panel.py` Is 1,790 Lines — Third God File.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1745-1759)

### JR-ML-TOOL-027 — CLN-CN-12: `network_visualizer.py:1512` — Active TODO Indicating Logging Error Bug.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1762-1776)

### JR-ML-TOOL-028 — CLN-CN-13: Deprecated `_generate_spiral_dataset_local()` Still Called.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1779-1793)

### JR-ML-TOOL-029 — CLN-CN-14: `np.random.seed(42)` Sets Global Numpy Seed.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1796-1810)

### JR-ML-TOOL-030 — CLN-JD-01: `python-dotenv` Hard Dependency for Optional ARC-AGI Feature.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1815-1829)

### JR-ML-TOOL-031 — CLN-JD-02: `FakeDataClient.close()` Destroys Data.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1832-1846)

### JR-ML-TOOL-032 — CLN-JD-03: Module-Level `create_app()` at `app.py:142` — Import-Time Side Effects.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/development/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V6_REMEDIATION_ANALYSIS.md` (lines 1849-1863)

### JR-DEP-TOOL-002 — Consolidate demo dataset parameters and shell script timeouts into config.sh.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: dep

**Sources**:
- `juniper-deploy/notes/HARDCODED_VALUES_ANALYSIS.md` (lines 93-117)

**Detail**:

Shell scripts have 8 hardcoded timeouts (90s service wait, 3s poll, 3s curl, 5s health,
120s demo test, 3s demo poll, 5s training start, 90s enhanced test). Demo has 7 hardcoded
parameters (n_spirals=2, n_points=200, noise=0.15, seed=42, learning_rate=0.01, 500 epochs).
Source all from scripts/config.sh. Lower priority (LOW) per analysis.

### JR-ML-TOOL-033 — Fix broken check_object_pickleability function in utils.py:238 which uses dill not in dependencies.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3580-3590)

**Detail**:

CLN-CC-10: utils.py:238 imports and uses `dill` library which is not in project dependencies.
Function is broken. Fix by either adding dill to deps or refactoring to use pickle only.

### JR-ML-TOOL-034 — Remove 9 stale local import traceback statements from cascade_correlation.py by uncomenting top-level import at line 64.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3568-3580)

**Detail**:

CLN-CC-03: 9 local `import traceback` statements scattered in cascade_correlation.py
across lines 2270, 2804, 3775, 3840 and other files. Consolidate via uncommented 
line 64 top-level import. Effort: 30 minutes.

### JR-ML-TOOL-035 — Remove committed .ipynb_checkpoints directories from repository.

**Status**: proposed  **Priority**: P2  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md` (lines 3590-3600)

**Detail**:

CLN-CC-12: Jupyter notebook checkpoint directories committed to repository in 
src/cascade_correlation/.ipynb_checkpoints/, src/candidate_unit/, src/
These should be in .gitignore. Effort: 10 minutes.

### JR-ML-TOOL-036 — Phase I (folded into Phase B): Asset cache busting for `websocket_client.js` + `ws_dash_bridge.js`.

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: ml

**Sources**:
- `juniper-ml/notes/interface_proposals/R2-02_phase_execution_contracts.md` (lines 1080-1099)

**Detail**:

Bump `assets_folder_snapshot` or equivalent query param in Dash config so browsers pick up new JS without hard refresh.
Included as deliverable MVS-FE-16 in Phase B (§6.3), not a standalone phase.
Verify via browser devtools that JS URL includes cache-bust query parameter changing on deploy.

**Design**:

Part of Phase B PR (P6). Ensures stale JS in browser cache doesn't cause mismatches with new protocol.

**Notes**:

Folded into Phase B per R1-05 §6.2. No independent gate. Rollback: revert cache-bust config (5 min TTF).
Priority P3 (folded, low-visibility change).

### JR-CAS-TOOL-002 — Remove legacy stale duplicate file check.py (duplicate of spiral_problem.py).

**Status**: proposed  **Priority**: P3  **Category**: TOOL  **Owner**: cas

**Sources**:
- `juniper-cascor/notes/development/JUNIPER-CASCOR_POST-RELEASE_DEVELOPMENT-ROADMAP.md` (lines 275-279)

