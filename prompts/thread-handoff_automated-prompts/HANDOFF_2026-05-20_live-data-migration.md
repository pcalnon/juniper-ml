# New thread handoff prompt

Continue picking off actionable items from the v7 outstanding-development roadmap (`juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`) one small-PR at a time.

## Completed this session (2026-05-19 → 2026-05-20)

11 PRs shipped + cleaned up:

- juniper-data #123 (JD-PERF-02 metadata cache), #121 (PERF-JD-01 readiness cache), #111 (SOP propagation)
- juniper-cascor #270 (BUG-CC-09 max_epochs guard), #264 (SOP propagation), #259 (P2-7 follow-up snapshot history endpoint), #258 (cascade_correlation import fix)
- juniper-canopy #290 (BUG-CN-12 narrow except), #289 (BUG-CN-08 deque maxlen), #284 (P2-5 follow-ups A+B), #281 (P2-7 WS push), #280 (P2-7 snapshot markers)
- juniper-cascor-client #48 (CC-09..12 JSON decode guards)

Plus ops work done via direct API:

- Branch-protection rulesets updated for data, cascor, canopy, cascor-worker — broad gate set including Async-route audit (BUG-JD-10 class)

## Critical context — v7 roadmap is ~50% stale

Many items show no Status line in the first 8 lines but have "✅ Implemented" / "✅ Verified Fixed" / "Verification Status: ✅" at the BOTTOM of the section under `##### Verification Status`. Items confirmed non-actionable this session: SEC-01, SEC-02, SEC-04, CONC-01, BUG-CC-13, ERR-01, ERR-02, CI-03, BUG-JD-04, BUG-JD-06,
BUG-CC-03 (refactored away), BUG-CN-04 (false alarm — 127.0.0.1 is architecturally correct), BUG-CN-06 (covered by P0-8), BUG-CN-10 (already in _connections_lock), DEPLOY-04 (Helm template injects via helpers), CLN-CN-04 (not a call site).

Procedure for each candidate: (1) read full section for ✅ markers, (2) grep cited line numbers in actual code — they're often stale, (3) verify the bug pattern still exists.

## Suggested next-step candidates (not yet verified)

From the Task-13 punch list still worth spot-checking:

- **CLN-CN-12** (canopy network_visualizer logging error at L1651) — vague TODO; needs runtime repro
- **CLN-CC-13** (cascor `sys.path.append` at cascade_correlation.py:67)
- **CLN-CC-10** (cascor dill import unguarded at utils/utils.py:239)
- **CLN-JD-02 / CLN-JD-03** (fake_client reset; uvicorn factory mode)

Unscanned roadmap sections worth surveying: §17 Concurrency, §18 Error Handling, §19 Testing/CI gaps, §20 Config, §21 API Contract.

## Procedure (mandatory)

1. **Worktree per task** under `/home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--YYYYMMDD-HHMM--<sha>/`
2. **Cleanup gate** (incident 2026-05-15 + 2026-05-20): never run `git push origin --delete <branch>` unless BOTH (a) Paul says "PR merged" AND (b) `gh pr view <N> --json state,mergedAt` reports `state=MERGED` with non-null `mergedAt`. See `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15`.
3. **Memory**: read MEMORY.md before recommending anything — multiple items there describe Paul's preferences (design-first when scope grows, triad pattern for non-trivial bugfixes, no /tmp/ scripts).

## Starting state to verify

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-baking-deer
git status                                 # expect: branch worktree-happy-baking-deer, clean
git log --oneline origin/main..HEAD HEAD..origin/main  # expect: nothing in flight
for r in juniper-data juniper-cascor juniper-canopy juniper-cascor-client juniper-cascor-worker juniper-deploy juniper-ml; do
  cd /home/pcalnon/Development/python/Juniper/$r && gh pr list --state open --limit 5 --json number,title
done
```

Ask the user which candidate to start with — don't pick blindly given the v7 staleness rate.

---
