<!-- markdownlint-disable -->

# Canopy E2E arc, Phase 8 (canopy#670) — validator report, round 3, 2026-09-23 (verbatim)

Archived by util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py from the session's subagent transcript: the last report after the agent's round-3 brief, which targeted the round-2 corrections frozen at canopy a967a5bd. EVIDENCE for Phase 8 of notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md; the reconciliation is in that phase.

## Lane B2 - round 3 on the round-2 corrections

*agent `a7e7deb96ecf6b34a` · round 3 · last-assistant-text (after its round-3 brief) · 6507 chars*

## Round 3, Lane B2: canopy#670 v3 (a967a5bd). Verdict: **MERGE**

v3 fixes D1, D2 and D3 at the logic level and in the browser clean room. Correction (3) does not break mount, a tab rebuild, the refill or any needed re-render. I found two minor follow-ups and no blocker.

I read only git objects: `a967a5bd` and `85415f3c` via `git show`, plus the corrections diff `9956de03..a967a5bd`. I also read `dash_renderer.dev.js` and the two consensus archives. I never read the fix worktree's working tree. The merge of main (#669/#667) does not touch `metrics_panel.py`: `git diff 85415f3c 9956de03 -- src/frontend/components/metrics_panel.py` is empty.

### (a) D1, D2 and D3 are fixed
**Logic level** (`util/ad-hoc/2026-09-23_f054_r3_laneB2_d123_on_v3.py`, same sequences run on each commit):

| Sequence | v2 (85415f3c) | v3 (a967a5bd) |
|---|---|---|
| D1: pause applied from its count, then its own trigger | `playing` (pause undone) | `paused`; the second run writes `no_update` ×8 |
| D2: step applied from its count, then its own trigger | index 22 (two steps) | index 21 (one step) |
| D3: lost seek to row 1 of 3, then its own trigger | row 0 (drift) | row 1 |

v2's four intended behaviours are unchanged on v3: a lost pause applies, merged steps apply twice, one click applies once, and a user seek applies.

**Browser, paired** (`util/ad-hoc/2026-09-23_f054_r3_laneB2_double_apply_v2_v3.py`, arm `k13_d60`, arms alternating v3/v2/v3/v2, 10 trials each):

| Build | Verdicts | Trials where the race occurred | Of those, a second toggle |
|---|---|---|---|
| v3 | 20 HELD | 1 | 0 |
| v2 | 18 HELD, 2 UNDONE | 2 | 2 |

- **v3 handled the race.** In v3a trial 6 a tick run applied the pause from the count. The click's own request then ran with `['replay-interval.n_intervals', 'replay-play.n_clicks']` and a consumed count, and v3 wrote nothing, so the pause held.
- **v2 undid the pause both times.** In v2a trials 7 and 8, the same sequence toggled the replay back to `playing` 92 ms and 310 ms after the pause.

### (b) What correction (3) breaks: nothing material
`util/ad-hoc/2026-09-23_f054_r3_laneB2_correction3_probe.py` runs each scenario on v2, v3, and v3-minus-3. v3-minus-3 is v3 with the early return keyed on a tick again, which isolates (3).
- **Mount (S1, S1b):** identical on all three builds, and it renders. A mount call has an empty `triggered` list and nothing pending.
- **Tab rebuild:**
  - A stale tick request that survives (the renderer drops the initial call when it is not alone, `:2992-2996`) writes nothing on all three builds, so this predates v3. The page then shows exactly what a mount render would write: `0 / 0`, `▶`, slider 0. The metrics-store is re-created as `[]`.
  - A stale play click that survives is ignored by v3. v2 would have started a fresh replay playing.
- **A no-op run that must still re-render:** the only thing (3) forgoes is re-drawing the slider thumb in a rare race run after a refill (S4). That is the stale thumb already conceded in round 1.
- **Refill:** the refill writes the max span alone, and a no-op run writes nothing, so a stale index cannot be written.
- **No other writers:** `replay-interval` is not in `_GATED_POLL_INTERVALS`, and nothing else writes the replay buttons or the interval.

**Finding F1 (minor, follow-up), from correction (2), not (3):**
- **What happens.** v3 skips a real user seek that lands exactly on `slider_w`, such as a quick drag out and back that merges into one request. The replay then does not pause, where v1 and v2 did (S5a, S5b). S5c, stopped at the end, stays `stopped`.
- **Where it can happen.** `slider_w` must be an integer, which with this slider means row 0, the last row, or a row where the max divides 100 × row (for 116 rows: rows 23, 46, 69 and 92). At the start, the window is before the first tick.
- **Alternative.** When the value equals `slider_w`, pause at the current index instead of skipping. That keeps v1's rule that a seek pauses and still avoids the drift.

### (c) Is the new wording true?
Mostly yes.
- Both cited archives exist and contain what is quoted:
  - `consensus/2026-09-23_validator_reports_round1.md`: Lane B, PAUSE-LOST 3/3 under forced saturation (L144-149) and 2 of 12 under dynamic load (L153-159).
  - `…_round2.md`: the double application, from me and independently from Lane B (`double_pause`, 3/3).
- "A trigger alone applies nothing" matches the code.
- The one-toggle limit is now stated.
- The lost-click order holds: `lost` follows `REPLAY_CONTROL_IDS` order, so step-forward then play, both lost, ends paused.

Two imprecisions:
- **"When the request that replaced it gets a slot (seconds…)":** a later request can replace that one too. Measured here the pause applied 206–786 ms after the click; nobody has measured it on canopy.
- **The D3 sentence** leaves out F1.

The 20/20 mutation result is not something I re-derived.

### §7 minimum record
- **Instruments:**
  - The node sequences could have shown v3 undoing the pause, stepping twice or drifting. They did not.
  - The browser clean room logs every run through a wrapper and has an UNDONE verdict, so it could have shown v3 toggling on a race run. It did not, and it did show v2 toggling.
- **The 60 ms lever is a construction.** It delays zero-delay timers so the deferred requested pass runs late. Its rates don't transfer to canopy.
- **Sample:** 20 v3 trials against 20 v2 trials. The race occurred 1 time on v3 and 2 times on v2, which is small. Round 2 added 2 undone pauses in 11 v2 trials.
- **Entry point:** git objects, not the working tree.
- **What the evidence cannot support:**
  - A D1 rate on canopy.
  - Any live-leg result for v3 from my lane.
  - Lane B's concurrent arms, which I did not read.

**Minimal change to flip:** nothing is needed for MERGE. For MERGE-WITH-CHANGES I'd add one clause to the D3 wording naming F1, or adopt the pause-at-current-index alternative. Evidence of v3 toggling on a race run would flip it to DO-NOT-MERGE.

**VERDICT: MERGE**

**Created** (untracked, juniper-ml worktree `partitioned-twirling-stream`):
- `util/ad-hoc/2026-09-23_f054_r3_laneB2_double_apply_v2_v3.py`
- `util/ad-hoc/2026-09-23_f054_r3_laneB2_correction3_probe.py`
- `util/ad-hoc/2026-09-23_f054_r3_laneB2_d123_on_v3.py`

The transcripts `r3_double_apply_v2_v3.json` and `.log` are in `…/scratchpad/laneB2/r3/` and should be archived before `/tmp` is cleared (it hit 100% of its inodes earlier today). **Changed:** no tracked file, and nothing in the canopy worktree.

---
