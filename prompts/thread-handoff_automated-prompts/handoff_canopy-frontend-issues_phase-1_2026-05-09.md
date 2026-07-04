# HANDOFF — Begin implementation of FRONTEND_ISSUES_PLAN_2026-05-09

Begin implementation of the juniper-canopy frontend remediation plan at juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md (canonical, v1.2).

## Read first, in this order

1. juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md — full plan, especially:
    - §0 Executive Summary + §8 Recommended PR series
    - §9 Hard dependencies + mermaid graph
    - §10 Resolution log (Q1–Q4 already CLOSED 2026-05-09)
2. juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md — separate authoritative spec for Issue #3 Phase 2 (live dataset swap behind experimental gate).
3. juniper-ml/notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md — pointer with TL;DR + cross-repo summary.
4. /home/pcalnon/Development/python/Juniper/CLAUDE.md — ecosystem map, worktree rules.

## What's been done

- Plan written, reviewed, and revised through v1.2.
- All four open questions resolved by user (in §10 Resolution log).
- Issue #3 Recommendation superseded by user-authored §3.4.2 → split into Phase 1 (in canonical plan) + Phase 2 (separate spec doc).
- Plan files are committed-ready but untracked as of handoff. Verify with git status before starting.

## What to do next — recommended PR-1 first

Per §8 ordering: 5 → 1 → 3 → 4 (skeleton) → 2 → 6 → 6.5 → 4 (full).

Start with PR-1 (cascor — reset() pause-event fix + invariant tests).
Smallest, highest user-pain payoff, no dependencies on any other PR.
Spec at canonical §4.5.
One-line code change at juniper-cascor/src/api/lifecycle/manager.py:1908 (add self._pause_event.set() to reset()); plus invariant tests per §4.6.

## Worktree & cross-repo notes

- Plan implementation spans juniper-cascor and juniper-canopy. Each PR lands in its own worktree per /home/pcalnon/Development/python/Juniper/CLAUDE.md Worktree Procedures.
- Centralized worktree dir: /home/pcalnon/Development/python/Juniper/worktrees/
- Branch naming: use a consistent prefix like frontend-issues/pr-N-<slug>.
- Cross-repo lockstep PRs: PR-4↔PR-5 and PR-6↔PR-7 must merge cascor-first (see §9 Hard dependencies). Do NOT merge canopy adapter map extensions before the cascor endpoint exists — would cause 404 storms in CI.

## Verification commands for the new thread

cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git status                                    # confirm canonical plan exists (untracked or committed)
ls -la notes/FRONTEND_ISSUES_PLAN_2026-05-09.md notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md

cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin && git status
sed -n '1900,1930p' src/api/lifecycle/manager.py    # confirm reset() at line 1908 still matches plan §4

cd /home/pcalnon/Development/python/Juniper/juniper-ml
ls -la notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md

## Git status at handoff (juniper-ml worktree)

- Worktree: /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/enumerated-prancing-widget
- Branch: main
- Untracked (in juniper-ml): notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md
- Untracked (in juniper-canopy main, separate working dir): notes/FRONTEND_ISSUES_PLAN_2026-05-09.md, notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md
- No staged changes. No uncommitted in-flight work other than the plan files themselves.
- First housekeeping step: decide whether to commit the three plan files on main of each repo (recommended) or to land them as part of PR-1's branch. Plan files are review-ready; user has approved.

## Constraints to respect (from §10 Resolution log)

- Q1: Demo mode stays — every new endpoint needs a src/demo_mode.py mirror.
- Q2: PR-4 must include the candidate-pool triple invariants (§1.5 C2.1) — atomic post-merge validation, not five independent setters.
- Q3: New UI lane must add ≤5 min wall-clock CI (parallel job + browser cache + --maxfail=3 + slow marker).
- Q4: PR-9 introduces src/frontend/ui_standards.py; PR-9.5 seeds notes/UI_STANDARDS.md — single source of truth for layout constants.

Do not narrate the plan back to the user; start by running the verification commands, then propose the PR-1 branch + worktree.
