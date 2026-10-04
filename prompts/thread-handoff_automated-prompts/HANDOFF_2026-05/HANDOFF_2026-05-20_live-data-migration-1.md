# Live Data Migration

Continue picking off actionable items from the v7 outstanding-development roadmap (juniper-ml/notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md) one small-PR at a time.

## Completed in this session (2026-05-20)

10 PRs shipped + cleaned up:

- juniper-cascor #278 (CLN-CC-10 dill import guard + [debug] extra), #279 (CLN-CC-13 cascade_correlation.py sys.path), #280 (CLN-CC-13 follow-on remote_client.py), #283 (ERR-06 — 7 from e chains in routes/network.py + training.py)
- juniper-data-client #66 (CLN-JD-02 FakeDataClient.close preserves data + new reset())
- juniper-data #127 (CLN-JD-03 lazy get_app() factory + uvicorn --factory, 9 files), #130 (ERR-07/08 narrow except + correlation-ID error)
- juniper-canopy #297 (main.py:93 dead-comment), #299 (API-01 health status "healthy" → "ok")
- juniper-ml #286 (notes/JUNIPER_2026-05-20_JUNIPER-ECOSYSTEM_CONFTEST-SYS-PATH-AUDIT.md — closeout doc for CLN-CC-13 sweep)

## Where the session ended

Mid-survey of §17–§21 of v7 for the next round. Confirmed shipped: most of §17 CONC-01..12 (only CONC-04 open), ERR-01/02/06/07/08/12/ROBUST-01, CI-01..05. Unverified/likely-open: ERR-13 (data arc_agi silent fallback at juniper_data/generators/arc_agi/), ERR-14 (cascor-client ws_client.py:79-80 ConnectionClosed swallowing — file
confirmed exists with stream() at line 126), API-02 (canopy health schema diverges — natural follow-on to API-01), CLN-CN-12 (vague TODO at network_visualizer.py:1651, needs runtime repro), and most of API-04..PROTO-01, CFG-, COV-, TQ-*.

Paul was about to pick next direction. Surface 3–4 options.

## Critical context

- Roadmap is ~50% stale — always grep cited line numbers and look for ✅/Implemented/Shipped markers BEFORE recommending. Several roadmap items I tried this session had drifted lines but pattern held; one (ERR-06) was missing a 7th site the citation didn't list. Always re-scan.
- Cleanup gate (mandatory, two gates): never git push origin --delete <branch> unless (a) Paul explicitly says "PR merged" for THAT PR AND (b) gh pr view <N> --json state,mergedAt reports state=MERGED with non-null mergedAt. Memory: feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.
- Canopy local main has 2 unpushed commits (be838e9 env normalization + a3d9047 merge). Branch from origin/main, NOT local main, in canopy.
- WIP stashes preserved: cascor 1, data 3, ml 1. Don't pop without checking with Paul.
- README.md markdownlint pattern: PR #125 (data) + canopy README normalization both admin-merged through markdownlint failures; fix is the 8-line disable block from juniper-ml #283 mirrored in juniper-data #127. If touching a README, check whether the disable block is already present.
- Memory: read MEMORY.md before recommending — Paul's preferences (design-first when scope grows, triad pattern, no /tmp/ scripts, defect-PRs separate from feature-PRs).

## Procedure

1. Worktree per task under /home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--YYYYMMDD-HHMM--<sha>/
2. For each candidate: read full roadmap section for ✅ markers → grep cited line numbers → verify bug pattern still exists → only then PR.
3. Ask user which option to pick; don't pick blindly.

## Starting state to verify

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-baking-deer
git status                                                  # expect: branch worktree-happy-baking-deer, clean
for r in juniper-data juniper-cascor juniper-canopy juniper-cascor-client juniper-cascor-worker juniper-deploy juniper-ml juniper-data-client; do
  cd /home/pcalnon/Development/python/Juniper/$r && gh pr list --state open --limit 5 --json number,title
done
```

Ask the user which candidate to start with — ERR-13, ERR-14, API-02, CLN-CN-12, or a deeper §17–§21 audit pass.

---
