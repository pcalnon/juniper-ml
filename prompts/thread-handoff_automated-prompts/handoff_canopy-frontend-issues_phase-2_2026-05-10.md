# Thread Handoff — Begin Implementing Issue #3 Phase 2 (Live Dataset Swap)

Begin implementing the work documented in `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md`. The §8 open questions are all answered (in the doc + repeated below).

## Read first, in this order

1. `juniper-canopy/notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md` — the canonical Phase 2 spec (P2-1 … P2-7).
2. `juniper-canopy/notes/FRONTEND_ISSUES_PLAN_2026-05-09.md` §8 + §3.4.2 — Phase 2 fits *after* the Phase 1 cold-swap work shipped in PR-6/PR-7 (already merged).
3. `/home/pcalnon/Development/python/Juniper/CLAUDE.md` — ecosystem map + worktree rules.
4. The `/home/pcalnon/.claude/projects/.../memory/` files referenced in MEMORY.md, especially `project_playwright_dash_react_input_gap.md` (UI-test harness limitation that will block any P2-6 Playwright work the same way it blocks PR-10).

## Open-question resolutions (lock these into the implementation)

1. **Experimental-functions toggle**: ship **both** — local `dcc.Store(persistence_type="local")` for UX persistence + server-side env-var gate that authoritatively overrides the client.
2. **Snapshots tab on swap**: show pre-swap snapshot + paired diff + post-swap snapshot.
3. **Replay**: animate as instantaneous transformation (no architecture-change animation).
4. **Warning copy**: ship verbatim from §3.4.2; mark for post-launch UX review.

## Phase 1 status (prerequisite — fully landed)

§8 PR series (11 PRs) is complete and merged on `main` of both `juniper-cascor` and `juniper-canopy`:

- cascor: #240, #241, #242, #243
- canopy: #254, #255, #256, #257, #258, #259, #260, #263

Phase 1 cold-swap behavior (`POST /v1/training/dataset` stage + `DELETE` cancel + `start_training` reload) ships and works. Phase 2 builds on this — P2-1 must NOT regress Phase 1's cold-swap path.

## Recommended start: P2-1

`cascor — swap_dataset_live() + POST /v1/training/dataset/live (gated)` is the smallest, server-side, no-cross-repo-lockstep PR. Get the experimental gate (`/api/v1/admin/experimental_functions`) wired first since P2-1 needs it.

## Verification commands for the new thread

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-canopy
git fetch origin && git status
ls -la notes/ISSUE_3_PHASE_2_LIVE_DATASET_SWAP_2026-05-09.md

cd /home/pcalnon/Development/python/Juniper/juniper-cascor
git fetch origin && git status
# Phase 1 surface to build on:
sed -n '2050,2090p' src/api/lifecycle/manager.py   # stage_dataset_config et al
sed -n '160,200p' src/api/routes/training.py        # POST/DELETE/GET dataset routes
```

## Worktree & cross-repo notes

Per `/home/pcalnon/Development/python/Juniper/CLAUDE.md`: all task work uses centralized worktrees at `/home/pcalnon/Development/python/Juniper/worktrees/`. Branch naming: `phase2/p2-N-<slug>`. Phase 2 has cross-repo lockstep PRs (P2-1 cascor must merge before P2-5 canopy adapter consumes it).

## Key carry-over context

- **Conda envs**: cascor work → `JuniperCascor1`; canopy work → `JuniperCanopy1`. Legacy `JuniperCascor` is broken (torch _C/ stub).
- **Q1 demo parity**: every new server feature needs a `src/demo_mode.py` mirror.
- **UI test harness gap**: `Playwright fill()` doesn't propagate to Dash `dbc.Input(type=number)` React state — any P2-6 Playwright tests must verify via `/api/state` HTTP, not via type-then-click-Apply. Memory entry has the diagnostic trail.
- **Snapshot test**: `test_panel_layout_snapshots.py` uses newline-tolerant compare to survive the pre-commit EOF-fixer; preserve that pattern when adding new snapshot baselines.

## Git status at handoff (juniper-ml worktree)

- Worktree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/purrfect-inventing-aho`
- Branch: `main`
- No uncommitted in-flight work; all PR-10 work is in juniper-canopy worktree (now merged).

Do not narrate the plan back to the user; start by running the verification commands, then propose the P2-1 branch + worktree.
