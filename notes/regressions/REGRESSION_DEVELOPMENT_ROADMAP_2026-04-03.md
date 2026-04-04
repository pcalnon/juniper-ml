# Juniper Project Regression Development Roadmap - 2026-04-03

**Author**: Claude Code (Principal Engineer)
**Date**: 2026-04-03
**Companion Documents**: `REGRESSION_ANALYSIS_2026-04-03.md`, `REGRESSION_REMEDIATION_PLAN_2026-04-03.md`
**Status**: Active - Implementation Complete, Testing In Progress

---

## Phase 1: Repository Setup (P0)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T1 | Stash uncommitted changes from main | cascor + canopy | Complete (changes already on worktree branches) |
| T2 | Create worktree branches | cascor + canopy | Complete (pre-existing worktrees used) |
| T3 | Apply stashed changes to worktree branches | cascor + canopy | Complete |

## Phase 2: Training Stall Fix (P0)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T4 | Implement adaptive correlation threshold in grow_network() | juniper-cascor | Complete |
| T5 | Add unit tests for adaptive threshold and convergence threshold | juniper-cascor | Complete (4 new tests) |
| T6 | Verify convergence_threshold plumbing (constants -> config -> network -> patience check) | juniper-cascor | Complete (validated by sub-agent) |

## Phase 3: Parameter Update Fixes (P1)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T7 | Validate corrected parameter mapping (convergence_threshold, patience) | juniper-canopy | Complete (validated by sub-agent) |
| T8 | Validate new patience UI controls render and submit correctly | juniper-canopy | Complete (29 integration tests pass) |
| T9 | Validate API model accepts new fields (convergence_threshold, candidate_patience, candidate_convergence_threshold) | juniper-cascor | Complete (validated by sub-agent) |

## Phase 4: Epoch/Iteration Semantic Fix (P1)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T10 | Rename "Current Epoch" -> "Current Iteration" in metrics panel | juniper-canopy | Complete |
| T11 | Rename "Grow Iteration" -> "Cascade Iteration" in progress bars | juniper-canopy | Complete |
| T12 | Update progress detail text to use "Cascade Iteration" | juniper-canopy | Complete |
| T13 | Update plot x-axis labels from "Epoch" to "Iteration" | juniper-canopy | Complete |
| T14 | Update test assertions for new label text | juniper-canopy | Complete |

## Phase 5: Plot Height Fix (P2)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T15 | Increase decision boundary plot to 800px/900px | juniper-canopy | Complete |
| T16 | Increase dataset scatter plot to 800px/900px | juniper-canopy | Complete |
| T17 | Increase distribution plot max height to 450px | juniper-canopy | Complete |

## Phase 6: Testing and Validation (P0)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T18 | Run juniper-cascor full test suite | juniper-cascor | In Progress |
| T19 | Run juniper-canopy full test suite | juniper-canopy | In Progress |
| T20 | Fix any test failures introduced by changes | both | Complete (1 assertion fix) |
| T21 | Validate with sub-agents | both | Complete (both passed) |

## Phase 7: Commit, PR, Cleanup (P0)

| Task | Description | Repository | Status |
|------|-------------|------------|--------|
| T22 | Commit all juniper-cascor changes | juniper-cascor | Pending |
| T23 | Commit all juniper-canopy changes | juniper-canopy | Pending |
| T24 | Push branches to remote | both | Pending |
| T25 | Create PRs | both | Pending |
| T26 | Worktree cleanup after merge | both | Pending (deferred to post-merge) |

---

## Summary

- Total: 26 tasks
- Complete: 21 tasks
- In Progress: 2 tasks (test suites running)
- Pending: 3 tasks (commit/PR/cleanup)
