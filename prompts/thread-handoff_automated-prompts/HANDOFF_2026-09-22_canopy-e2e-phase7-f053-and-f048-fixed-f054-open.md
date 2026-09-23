# HANDOFF — canopy E2E arc, Phase 7: F-CANOPY-053 and F-CANOPY-048 fixed and verified live, F-CANOPY-054 open

**Date**: 2026-09-22 · **Session**: <https://claude.ai/code/session_0171uABjF34XxFiu1n1L9wcG> ·
**Worktree**: `juniper-ml/.claude/worktrees/lively-humming-pixel` (branch `worktree-lively-humming-pixel`,
all work pushed to PR branch `docs/canopy-e2e-phase7-2026-09-22`)

**Documents REFERENCED** (the filename is carried on every citation):

- `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: the ledger; **Phase 7** is this
  session;
- `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: the matrix;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md`:
  the handoff this session re-evaluated. Its new top section, "★ RE-EVALUATED 2026-09-22", is the
  item-by-item status;
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`: the procedure
  followed.

**Documents CHANGED**: all of the above except the procedure, plus `util/ad-hoc/README.md`,
`util/isolated_stack.bash`, `tests/test_isolated_stack_script.py`, three repaired ad-hoc drivers, 19 new
`util/ad-hoc/2026-09-22_*` files, 49 transcripts and 3 verbatim report archives under
`reports/e2e-canopy-2026-09-02/`, and this file. All of it is in **juniper-ml#2030**.

---

## Goal

Continue the juniper-canopy E2E validation arc from Phase 7 of the ledger
(`…_E2E-VALIDATION-EVIDENCE.md`). The next work is the ledger's "Still owed after this phase" list,
led by F-CANOPY-054 and the latency root cause behind F-053.

## Completed this session

- **F-CANOPY-053 (P1)**: the Candidate Metrics writer never applied a periodic write on `9bffaba1`.
  - A regression since `f9defb4`.
  - The first fix, `running=` on the tab-gated lane, was REFUTED by round-2 review (it would re-break
    F-027).
  - canopy#657 merged as `d7d641b9`: a 10 s period, write only real changes, hold the last good value.
  - Verified live: the DOM tracked a growth window with a ~10–20 s lag, and the lane stayed gated
    off-tab.
- **F-CANOPY-048**: a two-callback cycle, and dash-renderer's breaker fires only when nothing else is
  pending.
  - canopy#658 merges the callbacks and adds a whole-app cycle test.
  - Verified live: six of seven replay rows PASS at the 16 s settle.
  - MERGE STATE: see the verification below.
- **F-CANOPY-054 (P2, OPEN, new)**: a late `replay_tick` response, computed from pre-click State,
  undoes a pause. M-METRICS-13 FAILs on it.
- **F-CANOPY-052** closed on M-CANDIDATES-07's own script, with its mechanism corrected to readiness.
- **F-CANOPY-038** closed in behaviour.
- **F-CASCOR-004** fixed by cascor#674 `f9818b01`, after two review rounds.
- **Ledger**: 65 / 47 fixed / 15 open (2 P1, 13 P2). **Matrix**: BLOCKED 20.

## Remaining work (the ledger's Phase 7 list, in order)

1. **F-CANOPY-054**: make `replay_tick` clientside, or version the state; re-drive M-METRICS-13. Do NOT
   fold the tick into the merged callback: same-identity eviction would drop the ticks.
2. **The F-053 regression**: what raised the page's delivery latency L (p50 5 s at idle) between
   `f9defb4` and `9bffaba1`. Profile both builds with
   `util/ad-hoc/2026-09-22_canopy_idle_cpu_profile.py`, and take a dispatch-rate census by source.
3. **Cheap dispatch-rate cuts**: the dead 1 Hz `metrics-panel-update-interval`, the ungated 500 ms
   `replay-player-panel-weight-drain`, and timestamp-only `/api/state` rewrites. Then re-profile.
4. **The top status bar**: a one-browser measurement, then file or fold. It is a candidate fourth
   writer of the F-053 class.
5. **Owner decisions**: F-CANOPY-004's contract (interaction re-render measured at 22–30 s against
   ≤16 s), and `FULL_HISTORY_POLL_TICK_MODULUS` → 1 (measured 32.4 s).
6. **Source-derived, unobserved**: canopy#613's guard vs the apply clamp; CAN-015's replay-player loop.
7. **F-CANOPY-049**, and #674's follow-ups: the same swallow-and-forget pattern in
   juniper-service-core's and canopy's own WS managers.
8. M-CANDIDATES-10/-11 (now re-drivable), the M-DATASET-17..26 owner question, and the M-TOPOLOGY-16
   fade half.

## Key context

- **Subagents hit the WEEKLY limit** (resets Sep 23, 22:00 CT). The round-2 checks of #657, #658 and
  #674 were therefore orchestrator-only. The ledger's consensus record says so.
- **The trio stays up**: `:8051` canopy `9bffaba1`, `:8202` cascor `05c13d5` (BEFORE #674), `:8101`
  data. The fixture is 2/68/2, uuid `1cd15120…`. A resumed snapshot has NO metrics history.
- **Browser runs**: `JUNIPER_E2E_BROWSER_GPU=1` (the default is SwiftShader). Keep concurrent browsers
  at 3 or fewer (canopy's per-IP WS cap is 5). Export `JUNIPER_E2E_CANOPY_URL`.
- **The two renderer mechanisms separate on the wire.** Delivered but never applied means eviction; no
  request at all means a readiness block. An A/B that stops a trigger cannot tell them apart.
- **MEMORY.md is over its load limit** (~25.8 KB against 24.4 KB). Compact per
  `feedback_memory_index_target_is_20kb`: retire entries and keep hazard hooks.

## Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
gh pr view 2030 --json state,mergedAt; gh pr view 658 -R pcalnon/juniper-canopy --json state,mergedAt,mergeCommit
python3 util/ad-hoc/e2e_finding_triage.py --note notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md | tail -7   # 65/47/15
grep -cE '^\| [A-Z0-9.-]+ .*\| BLOCKED' notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md                  # 20
ss -ltn | grep -E ':(8051|8055|8101|8202)\b'; curl -s http://127.0.0.1:8202/v1/network                                          # hidden_units 68
```

**Git state at handoff**: every change is on juniper-ml PR branch `docs/canopy-e2e-phase7-2026-09-22`
(#2030), as five signed API commits. The local worktree holds the same changes STAGED, not committed.
canopy#657 and cascor#674 are MERGED. canopy#658 has auto-merge ARMED; confirm it merged.
