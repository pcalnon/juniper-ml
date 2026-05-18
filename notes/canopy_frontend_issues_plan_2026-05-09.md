# Canopy Frontend Issues Plan — Pointer (2026-05-09)

This is a **pointer** note. The canonical, full plan lives in the
juniper-canopy repo:

* **Canonical**:
  [`juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md`](../../../../../juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md)
* **Absolute path**:
  `/home/pcalnon/Development/python/Juniper/juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md`

## Why this pointer exists

The plan addresses six juniper-canopy frontend bugs (and one cross-repo cascor
fix) but was scoped from this juniper-ml worktree. Keeping a pointer here so
ecosystem-level ops see the work and don't double-spec.

## Revisions

| Date       | Rev  | Note                                                                    |
|------------|------|-------------------------------------------------------------------------|
| 2026-05-09 | v1.0 | Initial plan posted.                                                    |
| 2026-05-09 | v1.1 | Open questions Q1-Q4 resolved (see canonical §10 Resolution log). PR series gains PR-9.5; PR-4 scope hardened with candidate-pool invariants. |
| 2026-05-09 | v1.2 | Issue #3 Recommendation superseded by §3.4.2 alternate approach. Phase 1 (cold-swap + Cancel) stays in canonical plan; Phase 2 (live in-flight swap behind experimental gate, with History/Snapshots/Replay persistence) lives in a separate spec at `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md`. New PR series P2-1…P2-7. |

## TL;DR

| #   | Issue | Severity | Recommended PR |
|-----|---|---|---|
| 1   | Metaparam edits don't reach cascor (silent param-map drop) | P0 | canopy + cascor (PR-2, PR-4, PR-5) |
| 2   | Numeric input typing vs spinner mismatch | P1 | canopy (PR-8) |
| 3   | Dataset View edits don't change training dataset | P0 | **Phase 1**: canopy + cascor (PR-6, PR-7 — cold swap + Cancel button). **Phase 2**: in-flight swap behind experimental gate + History/Snapshots/Replay persistence (PRs P2-1…P2-7, separate spec doc). |
| 4   | No real UI test sub-suite | P1 | canopy (PR-3 skeleton, PR-10 full) |
| 5   | Single-iteration auto-pause after stop+reset+start | P0 | cascor 1-line (PR-1) |
| 6   | Sidebar too wide on Training Metrics tab | P3 | canopy (PR-9 + PR-9.5 spec doc) |

## Recommended ordering

`5 → 1 → 3 → 4 (skeleton) → 2 → 6 → 6.5 (UI spec doc + experiment) → 4 (full coverage)`.
Full dependency graph, diff-ready patches, and validation are in the
canonical doc.

## Issue #3 — alternate approach (v1.2, 2026-05-09)

The §3 Recommendation has been replaced by the user-authored §3.4.2 alternate
approach. The work is now split into two phases:

* **Phase 1 (in canonical plan)** — cold swap + a Cancel button on the
  pending-dataset banner. Resolves the user-visible Issue #3 bug. Ships in
  PR-6 / PR-7.
* **Phase 2 (separate spec doc)** — in-flight (live) dataset switch behind an
  "Enable Experimental Functions" toggle, two-step warning modal, server-side
  gate, and full History/Snapshots/Replay persistence of the swap. Required
  for CasCor cross-training experiments. Specified in
  `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md`.

The §3.4.2 functional requirements (F2.1–F2.10 in the Phase 2 doc) are the
source of truth. Implementation specifics in the Phase 2 doc are starting
points and may be adjusted during review without invalidating the plan.

## Resolved scope notes (from canonical §10 Resolution log)

* **Q1 — Demo mode is staying.** Mirror every new endpoint in
  `juniper-canopy/src/demo_mode.py`. Reuse-refactor filed as out-of-scope
  follow-up.
* **Q2 — Candidate-pool knobs are real product surface.** PR-4 must implement
  the constrained-triple invariants (`S = T + R` with degenerate cases) as
  atomic post-merge validation, not five independent setters.
* **Q3 — CI minutes budget capped at +5 min wall-clock** for the new UI lane.
  Strategy: parallel job, browser cache, `--maxfail=3`, `slow` marker on heavy
  snapshot tests. Accuracy beats speed.
* **Q4 — No brand-spec exists; this work seeds one.** PR-9 introduces
  `src/frontend/ui_standards.py` (constants); PR-9.5 introduces
  `notes/UI_STANDARDS.md` and runs the Training-Metrics narrowing experiment
  under Playwright.

## Cross-repo touchpoints (from juniper-ml's perspective)

* **juniper-cascor** changes required for PRs 1, 4, 6.
* **juniper-canopy** changes required for PRs 2, 3, 5, 7, 8, 9, 9.5, 10.
* **juniper-data-client** unaffected (uses existing `fetch_dataset` for
  PR-6's dataset reload).
* **juniper-ml** unaffected at the package level; this pointer only.
