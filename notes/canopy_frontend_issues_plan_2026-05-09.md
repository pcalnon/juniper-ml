# Canopy Frontend Issues — Cross-Repo Implementation Plan (Pointer)

**Date**: 2026-05-09
**Status**: Plan finalized v1.2; implementation starting with PR-1
**Canonical plan**: [`juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md`](../../juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md)
**Phase 2 spec**: [`juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md`](../../juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md)

---

## TL;DR

Six user-facing frontend issues in juniper-canopy, remediated through a cross-repo PR series spanning **juniper-cascor** and **juniper-canopy**. Total optimistic ≈ 33h, realistic ≈ 82h.

| # | Issue | Repos touched | PR(s) |
|---|-------|---------------|-------|
| 1 | Metaparameter edits don't reach cascor (silent drop in adapter) | cascor + canopy | PR-4 (cascor PATCH endpoints), PR-5 (canopy adapter) |
| 2 | Numeric inputs reject either typing OR spinner | canopy | PR-2 |
| 3 | Dataset View tab doesn't affect training (Phase 1: cancel; Phase 2: live swap) | cascor + canopy | PR-6 (cascor cancel route), PR-6.5 (canopy cancel UI), Phase 2 deferred |
| 4 | UI test sub-suite missing | canopy | PR-3 (Playwright skeleton), PR-10 (full coverage) |
| 5 | Single-iteration auto-pause after Stop+Reset | cascor | **PR-1** (starting first) |
| 6 | Left sidebar too wide on Training Metrics tab | canopy | PR-9 / PR-9.5 |

## PR ordering (per canonical plan §8)

`5 → 1 → 3 → 4 (skeleton) → 2 → 6 → 6.5 → 4 (full)`

Rationale: PR-1 (Issue #5) is the smallest, highest-pain payoff; lockstep cross-repo PRs (4↔5, 6↔6.5) must merge **cascor first** to avoid 404 storms in canopy adapter map (canonical §9 hard dependencies).

## Branch naming convention

Across all worktrees: `frontend-issues/pr-N-<slug>`.
Centralized worktree dir: `/home/pcalnon/Development/python/Juniper/worktrees/`.

## Open-question resolutions (canonical §10)

- **Q1** Demo mode stays — every new endpoint needs a `src/demo_mode.py` mirror.
- **Q2** PR-4 must include candidate-pool triple invariants (canonical §1.5 C2.1) — atomic post-merge validation.
- **Q3** New UI lane must add ≤5 min wall-clock CI (parallel + browser cache + `--maxfail=3` + slow marker).
- **Q4** PR-9 introduces `src/frontend/ui_standards.py`; PR-9.5 seeds `notes/UI_STANDARDS.md` as the single layout-constant source of truth.

## What lives in juniper-ml for this initiative

This pointer doc and (eventually) any cross-repo CI scaffolding the meta-package coordinates. Implementation diffs land in juniper-cascor and juniper-canopy.
