<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 3: Lanes R3-A and R3-B, verbatim

Round 3 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 3f83b9c6, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R3-A re-derived round 2's new claims from their artifacts; Lane R3-B attacked round 2's corrections (acf1a93a..3f83b9c6). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR3A_phase9_ledger_brief.md and laneR3B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py; the ledger's consensus record lists what was and was not re-derived.

## Lane R3-A -- measurement re-creation, artifact-first

*agent `ac3b2d25aa13446ab` · round 1 · last-assistant-text (not resumed) · 13913 chars*

**VERDICT: SOUND-WITH-FIXES.** Every number and date I re-derived holds. None of the mismatches changes a disposition. Four change an action, and three change a stated number, so under §4 of the consensus procedure the review does not end here.

**TABLE**

| # | Claim | Re-derived value | Result | Evidence |
|---|---|---|---|---|
| 1a | cascor `/replay` returns `data.session`, and `range` is a dict | `success_response(_build_unified_payload(…, extra={"session": state_summary()}))` at `snapshots.py:449`. `state_summary()` returns `"range": {"start","end"}`. It has done so since `e01f57f`, which is cascor#178 and merged 2026-05-03T00:55:26Z | MATCH (date is a NIT, see 9) | `git -C cascor show 0e016a7c:src/api/lifecycle/manager.py` (lines 1156-1164); `git log -S` finds only `e01f57f` |
| 1b | What canopy stores and reads | `confirm_snapshot_op` stores the whole data block with `session` nested inside it (`hdf5_snapshots_panel.py:1316-1324`). `_session_summary` returns `data["session"]`. `render_session` then runs `range_value = dict`, and `f"[{range_value[0]}…"` fails at `:532` | MATCH | read from the `e9053227` extract |
| 1c | Executed in JuniperCanopy1 (py 3.13.13, dash 4.2.0), using the `registered_panel` wiring | With the dict range: `KeyError(0)` at `replay_player_panel.py:532`. With the list `[0,12]`: the active view, `0 / 12`, `[0, 12]` and the V2 weights badge. Driving `_cb_confirm_snapshot_op` with a cascor-shaped envelope (wrapped and unwrapped) and passing its output to `render_session` also raises `KeyError 0` | MATCH | `python -c` against the extract |
| 1d | Is there a dict→list converter, or a writer that renders? | No converter. The only list writer is `_merge_session`'s local fallback, which writes top-level `range` at `:873-874` and is bypassed whenever `session` is a dict. There are exactly two writers (`hdf5_snapshots_panel.py:1269`, `replay_player_panel.py:670`) and no JS `set_props` writer. Neither yields an active view against cascor | MATCH | `git grep` at `e9053227` |
| 1e | P0 under plan §6.3 and §1.1(d) | The plan (`…E2E-FRONTEND-VALIDATION-PLAN.md:359`) defines P0 as "blocks a mandate-named workflow", and §1.1(d) names "snapshots saving/loading/replaying". The rating holds, and the real impact is worse than stated (Finding 3) | MATCH | |
| 1f | The fixture says it was measured | `test_p2_wave_batch_a.py:179` reads "The exact shape measured off the running service", and `:190` has `"range": [3, 37]` | MATCH (NIT 11) | |
| 2 | Run 35928632707 | Attempt 1: the macOS 3.12 unit job failed at 22:40:57Z, then Quality Gate failed at 22:42:30Z. Attempt 2 started 01:22:32Z, triggered by pcalnon, re-ran all 19 jobs, and Quality Gate passed at 01:37:55Z. The merge at 01:38:02Z was 7 s later | MATCH | Actions API `attempts/{1,2}` and `…/jobs` |
| 3a | Re-running the scanner over the ledger's windows | Output is byte-identical to both archived `.out` files (684 and 488 calls) | MATCH | `cmp` |
| 3b | 38 background launches, 34 naming one PR | 38, of which 34 name one PR and 4 name none. The 4 name no PR in their full commands either, not just in the first 220 characters | MATCH (on the scanner's own terms) | awk and regex over the output, plus a full-command recheck |
| 3c | None names the 11 listed PRs | PRs named: 658, 670, 674, 680, 682, 683, 2015, 2027-2031, 2041, 2043, 2044, 2047, 2048, 2054, 2058, 2060, 2061, 2063 | MATCH | |
| 3d-f | Only non-undo `gh pr ready` is ml#2020 at 06:09:09Z; no draft-readying background launch since 09-20; last match at 21:27:05Z | As stated | MATCH | scan output; a broader scan finds nothing else |
| 3g | Drafting sessions | `259b4d16` at 19:44:36Z; `bc31e993` at 20:24:18Z and 20:24:24Z; `e6c1cb6d` at 21:26:16Z. The timelines' `convert_to_draft` events agree | MATCH | |
| 3h | The scanner "lists every Bash call … could … update-branch" (`…E2E-VALIDATION-EVIDENCE.md:8698-8699`) | False: six missed background launches (Finding 1) | MISMATCH | |
| 4 | The account's later actions | `4392ab5a` at 23:16:06Z, merged 23:24:21Z; `ae5a3b18` at 23:17:08Z, merged 23:22:46Z; ml#2045 disarmed 23:48:47Z and re-armed 23:48:52Z; cascor-worker#196 merged 01:21:37Z; `cdb0a18b` at 21:43:55Z (a web-flow merge); the shepherd's only write is `PUT …/update-branch`; its completion notice is at 21:53:09.035Z | MATCH, but the list is incomplete (Finding 2) | timelines, commits API, the script (byte-identical to the launched copy) |
| 5a | `run_watchdog_r3.json` | 5 fires. The fires at 57.8 s and 152.8 s evicted nothing: requests 11 and 35 applied. The fires at 92.8 s, 187.8 s and 232.8 s started cascades that lost 10 responses (ended when request 28 applied at 118.44 s), 3 (ended when request 45 applied at 196.88 s) and 4 (still running when the run ended). 17 of 56 were lost in all. A cascade ends when a request completes before the next one starts | MATCH | timeline dump |
| 5b | `run_watchdog.json` | 23 of 23 applied, `watchdog_fires: []` | MATCH; the "±" wording is wrong (NIT 6) | |
| 5c | Probabilities | Model: homogeneous Poisson, P = exp(−λT), with λ = 37–44/h for all fires and 29–33/h for evicting fires. This gives 0.077–0.116 (T=210 s), 0.146–0.184 (evicting, T=210 s), 0.087–0.128 (T=200 s; the ledger's 0.086–0.127 corresponds to T≈200.8 s) and a product of 0.0127–0.0236 | MATCH within rounding (NIT 7) | re-ran the alias simulation: 6.9–7.6 s gives 44/h (32.8 evicting), and seed 11 gives 37.6/h (29.4) |
| 6a | `no_update` status | HTTP 200 `{"multi":true,"response":{}}` for single- and multi-output callbacks; `PreventUpdate` gives 204. The code is `_callback.py:601-605`, with `has_output` set at `:640` and `:645` | MATCH | test client on dash 4.2.0 |
| 6b | Can a later store subscriber see a props-less answer in `executed`? | No. `applyProps` is the only dispatch between add and remove, and it runs only when there are props. Headless Chromium on dash 4.2.0: 0 of 15 `no_update` answers seen against 15 of 15 data answers, while a dispatch wrapper counted 15 `AddExecuted` actions for each. Exceptions exist only for synchronous error objects and re-entrant synchronous entries, and neither applies to the feeder | MATCH | synthetic app on ephemeral port 36709, now closed |
| 7 | Counts | 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open (1 open P0, 6 open P1). F-CANOPY-015 is OPEN at P2 | MATCH | `e2e_finding_triage.py` |
| 8 | F-CANOPY-057 history | #180 targeted `main` (merged 02:06:37Z). #184 targeted #180's branch (06:03:30Z). #187 targeted #184's branch (07:31:04Z). #189 targeted `main` (`b1d19948`, 19:52:10Z). #190 targeted #189's branch (20:05:12Z). The compare says diverged, 3 ahead and 512 behind, merge base `9348a26a`. None of g-3's symbols is on `main` | MATCH; one exception in Finding 4 | `gh api` pulls, compare, commits |
| 9 | Still owed items 3-9 | Every Phase 8 and Phase 7 item number is right. cascor#674 is `f9818b01`, merged 2026-09-23T00:45:02Z; canopy#674 is `894a2cc7` | MATCH | read both lists |
| – | F-059's line citations | Idle and controls are at `:112` and `:113`, not `:114` and `:115` | MISMATCH (NIT 5) | |

**FINDINGS**

1. **MINOR: the launch scanner is not exhaustive.**
   - Quoted: "lists every Bash call whose command line could ready, arm, merge, update-branch or re-run a PR" (`…E2E-VALIDATION-EVIDENCE.md:8698-8699`, repeated in its Instruments bullet).
   - Evidence: `util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py` calls `update-branch` in a loop. Session `23e65d0b` launched it in the background six times on 09-23, at 13:50:15Z and between 14:49:59Z and 15:19:51Z, for ml#2040 and ml#2049–2053. The regex matches none of these launches.
   - I also checked the regex directly against command forms it should catch, and it misses all of them:
     - `gh pr -R <repo> ready|merge N` (gh accepts this order; I checked with a read-only `view`);
     - `pulls/$PR/merge`;
     - GraphQL `updatePullRequestBranch`;
     - `check-suites/<id>/rerequest` and `rerequestCheckSuite`;
     - `gh api graphql -F query=@file`;
     - a `\`-newline between `pr` and the verb;
     - `git merge` followed by `git push` to the PR branch.
   - It also cannot see scripts run through indirection (scratchpad `.sh` files, scripts written by `Write`), non-Bash tools such as `Monitor`, or foreground calls that detach with `nohup … &`.
   - The conclusion survives. A broader scan of every tool_use from 09-20 to 09-24T04Z finds none of those forms used on the pass PRs, the converge runs had all ended by 17:19:51Z, and that script never readies or arms.
   - Fix: add those patterns (at minimum `converge_pr`) and say "matching the pattern" instead of "every".
   - Changes a number (update-capable background launches on 09-23 are 44, not 38; 40 name a PR, not 34) and an action. No disposition.

2. **MINOR: owner-question evidence found in round 2 was dropped.**
   - Quoted: "The actor is unidentified" (`…E2E-VALIDATION-EVIDENCE.md:8743`) and the later-actions list (`:8732-8736`).
   - Evidence: pushes made as `pcalnon`, PGP-signed locally rather than by web-flow, landed inside the window in which no Claude Code session on this host made a tool call (the PushEvent API):
     - `4c496443` on ml#2058, pushed at 21:45:24Z, two minutes before the pass's first ready;
     - `c666403b` on ml#2045 at 23:47:35Z, 72 s before that PR's disarm and re-arm;
     - a rebase force-push `b0223f18` at 00:00:39Z;
     - ml#2045 was then drafted at 03:04:45Z and readied at 03:05:02Z, with no transcript entries at all on this host between 02:55Z and 03:10Z.
   - Round 2's report (`…2026-09-24_validator_reports_phase9_ledger_round2.md:468`) raised `4c496443` "for the owner question", and the fix pass did not carry it.
   - Fix: add these to the account's-actions list and to the owner question.
   - Changes an action. No number or disposition.

3. **MINOR: F-CANOPY-059 understates its impact.**
   - Quoted: "Play, pause, seek, speed, range and Stop are never on screen" (`…E2E-VALIDATION-EVIDENCE.md:9095`).
   - Evidence: the player's Stop is canopy's only path to `replay/control stop` (`git grep`). While cascor is REPLAYING it refuses starting and stopping training (`manager.py:2452`, `:2842`), creating a network (`:1731`) and Restore/Resume/Retrain (`snapshots.py:278`, `329`, `378`).
   - So one Replay from the UI leaves cascor stranded until a restart or an out-of-band API stop.
   - Fix: say so, and make item 16's live check plan an API-level stop.
   - Changes an action. It is P0 already, so no disposition change.

4. **MINOR: F-CANOPY-057's open question about #184 can be closed.**
   - Quoted: "whether its diff reached `main` by another route is unchecked" (`…E2E-VALIDATION-EVIDENCE.md:9009-9010`).
   - Evidence: #189 ("[retarget #184]", `b1d19948`) has `manager.py` +/- lines identical to #184's (same md5) and the identical test blob `77455a9b93`.
   - Fix: record that it reached `main` through #189, and drop that sweep item.
   - Changes an action.

5. **NIT:** `replay_player_panel.py:114` and `:115` (`…E2E-VALIDATION-EVIDENCE.md:9093`) should be `:112` and `:113` at `e9053227`. Changes nothing.

6. **NIT: the latency notation is wrong.**
   - Quoted: "R = 3 ± 2 s" and "R = 7 ± 1 s" (`…E2E-VALIDATION-EVIDENCE.md:8924`, `8927`, `9033`, `9041`).
   - The repro sleeps `R + uniform(0, jitter)` (`2026-09-23_f055_r1_laneB_repro.py:96`), and the measured durations were 3.001–4.990 s and 7.001–7.995 s.
   - Fix: write "3–5 s" and "7–8 s".
   - Changes a stated number only.

7. **NIT: the probability model is never named.**
   - Lane B's own alias simulation gives fires more regular than Poisson. In 50-hour runs, the stationary chance of no fire in 210 s is 0.054–0.070 (evicting: 0.12–0.15), and at 7–8 s per request it is 0.076–0.099 over 200 s, at 35–37 fires/h.
   - Fix: say "under a Poisson approximation". The conclusion only gets stronger.
   - Changes numbers only.

8. **NIT:** "Phase 4 closed F-CANOPY-015 by test" (`…E2E-VALIDATION-EVIDENCE.md:9101`) contradicts Phase 4's own status correction (`:6135-6147`) and "stays OPEN" (`:9258`). It is a wording fix.

9. **NIT:** "2026-08-27" (`…E2E-VALIDATION-EVIDENCE.md:9099`) and "2026-05-02" (`:9085`) are local author dates. The merges were at 2026-08-28T04:16:14Z and 2026-05-03T00:55:26Z UTC, and the rest of the section uses UTC.

10. **NIT:** the pass also made six web-flow update-branches that the ledger does not list: ml#2032 at 22:27:32Z, data#428 at 22:30:06Z, ml#2059 at 22:50:08Z, ml#2066 at 22:50:21Z (`41379ff9`), data#431 at 22:51:03Z, and two on #676. "update-branches on ml#2066" (`:8733`) names only one of that PR's two.

11. **NIT, strengthens F-059:** the "measured" fixture differs from cascor's real payload in at least five more fields: `fsm_state`, `status`, `time_index.current`, `weight_sampling` and `paused`.

**WHAT YOU COULD NOT CHECK**
- Any live replay against canopy or cascor. It is not permitted, since it would write cascor.
- Actors off this host: the GitHub UI, other hosts, cloud sessions, automations. Whether the signed pushes came from the owner's IDE is unknown.
- "259b4d16 stayed open … until about 03:27Z". Its transcript ends at 21:01:29.583Z.
- The contents of `confirm_step.bash`. I read only the wrapper scripts, which are read-only.
- dash 4.4.1 line numbers. I checked 4.2.0 only.
- How well the simulation represents the real page, including the start-up effect when a census begins at page load.

**SECRETS/PII:** I printed no tokens, environment variables or credential files and requested no email fields. Transcript greps printed file names and bounded substrings only, one author line was email-redacted, and I read only the aliases block of gh's `config.yml`, never `hosts.yml`. No slips. Files changed: none. Scratch output is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r3a.YBcWgV`.

---

## Lane R3-B -- adversarial, on round 2's corrections

*agent `a67e2284dabe29682` · round 1 · last-assistant-text (not resumed) · 19402 chars*

**VERDICT: SOUND-WITH-FIXES.** The core of the correction pass holds. The replay is exact, the CI rows are correct, F-CANOPY-059's mechanism executes as described and the counts match. Several of the pass's new statements are still wrong or overstated. Findings 1, 2, 3, 5, 6, 8, 9 and 11 each change a number or an action, so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` calls for another round after these are fixed.

## FINDINGS

**Paths.**
- LEDGER = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda/notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `3f83b9c6`.
- ML-AH = the worktree's `util/ad-hoc/`.
- Canopy line numbers are at `e9053227`; cascor line numbers are at `0e016a7c`.

### 1. MINOR — Lane B's two per-request ranges are misstated four times

- **Quoted:**
  - LEDGER:8924 "R = 7 ± 1 s" and LEDGER:9041 "watchdog run at R = 7 ± 1 s".
  - LEDGER:8927 and LEDGER:9033 "Lane B's run at R = 3 ± 2 s".
- **Evidence:**
  - The jitter is one-sided. ML-AH `2026-09-23_f055_r1_laneB_repro.py:96` sleeps `R + random.uniform(0.0, JITTER)`.
  - `phase9-scratch/f055_r1_laneB/run_watchdog_r3.json` (R 3.0, jitter 2.0) has request durations of 3.001–4.990 s.
  - `run_watchdog.json` (R 7.0, jitter 1.0) has 7.001–7.995 s.
  - The same section's unchanged LEDGER:8883 and LEDGER:8890-8891 already say "R = 3–5 s" and "7–8 s", so the pass now contradicts itself.
  - The consensus record (LEDGER:9227-9228) says both runs were re-derived.
- **Fix:** "R = 3–5 s" and "R = 7–8 s". The probability figures do not change.
- **Changes a number:** yes (the stated ranges). **Disposition / action:** no.

### 2. MINOR — the launch scan cannot see an update-branch helper written that same day

- **Quoted:**
  - LEDGER:8698-8699 "lists every Bash call whose command line could ready, arm, merge, update-branch or re-run a PR".
  - LEDGER:8701-8702 "None of that day's 38 matching background launches…".
  - LEDGER:8735-8736 "none of the day's launches names ml#2066 or data#434".
  - `util/ad-hoc/README.md:740` says the same.
- **Evidence:**
  - The regex (`2026-09-24_merge_command_launch_scan.py:34`) matches only a few script names plus literal `gh` or GraphQL verbs.
  - ML-AH `2026-09-23_converge_pr_through_moving_main.py` (in the tree since `288de462`, 09-23T15:08:30Z) runs `gh api -X PUT …/update-branch` at its `:78`.
  - Session `23e65d0b` launched it in the background six times on 09-23: `--pr` 2040 (13:50:15Z), 2049, 2050, 2051, 2052 and 2053 (15:19:51Z).
  - None of those launches appears in the archived output or in my re-run of the scan (684 calls, 38 background, byte-identical to the archive; `converge` count 0).
  - The conclusions survive. None of the six names ml#2066 or data#434, and their 5400–7200 s timeouts ended them by about 17:20Z. The stated basis does not survive.
- **Fix:** add the helper (and `bot_pr_converge`) to the regex, or also scan the scripts a command runs. Call the 38 "regex matches" and cite this check.
- **Changes an action:** yes (the tool and its description). **Number / disposition:** no.

### 3. MINOR — F-CANOPY-059's "What a user sees" leaves out that cascor stays locked in REPLAYING

- **Quoted:** LEDGER:9094-9096 "switches to the Replay tab, which says '▶ No active replay session' while cascor replays".
- **Evidence (cascor `manager.py`):**
  - `:6001-6002` marks the FSM REPLAYING and sets training_state to "Stopped" / "Idle".
  - `:2452-2453` refuses start_training "while replaying a snapshot — invoke …/replay/control with action='stop' first".
  - `:4742-4743` refuses parameter updates; `:1731` refuses network creation; `:5784` refuses restore.
  - The only escape hatches are replay/control stop, which F-059 hides, and RESET (`:2878`).
  - The session also starts paused (`:1076` `self.paused = True`), so nothing is actually replaying.
- **Consequence:** after one Replay, Start and Apply fail while canopy shows Stopped, until the user finds the sidebar Reset. Nothing in canopy's `dashboard_manager.py` handles "replaying".
- **Fix:** state this. Add Start-after-Replay and the Reset escape to item 16's live check.
- **Changes an action:** yes.

### 4. MINOR — the P0 contradicts the ledger's own precedent

- **Quoted:** LEDGER:9103-9104 "P0, on plan §6.3's rule… 'snapshots saving/loading/replaying' (§1.1(d))".
- **Evidence:**
  - The P0 does follow §6.3's wording: `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360` and §1.1 at `:43-45`.
  - But F-CANOPY-014 (LEDGER:3907-3909), "the entire replay control surface is dead: play / pause / seek / speed / range / stop all fail", blocked the same workflow and was rated P1.
- **Fix:** say why the two differ, or put the precedent to the owner in item 15, which already asks about F-059's P0.
- **Changes the disposition:** possibly. **Action:** yes.

### 5. MINOR — the cascor#184 question the ledger leaves "unchecked" is answered by a PR the same paragraph cites

- **Quoted:**
  - LEDGER:9003-9005 "The same pattern a third time… cascor#184…".
  - LEDGER:9009-9010 "cascor#184 is one; whether its diff reached `main` by another route is unchecked".
- **Evidence:** `gh pr view 189`:
  - Title "…(Phase 6E CAN-015g, g-2) [retarget #184]", with head `…-cache-v2` and base `main`.
  - +524/−3 across 2 files, the same as #184's +524/−3 across 2 files.
  - Its body says "Original g-2 PR was #184 … its merge commit went into the stacked parent branch".
  - It merged as `b1d19948`, which is on main.
- **Consequence:** #184's diff reached main through #189. It is not an orphan and not a target for the sweep.
- **Changes an action:** yes.

### 6. MINOR — the canopy follow-up's review has not terminated, yet the ledger calls it "fixed" and schedules the PR

- **Quoted:**
  - LEDGER:8762-8763 "The first two are fixed on canopy branch `fix/idle-cuts-round3-wording` (local `9935b857`…)".
  - LEDGER:9332-9335 "Done as one canopy follow-up… Its review, Lanes C, C2 and C3".
- **Evidence:**
  - `consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`: C3 reviewed `15bd8135..2f2bc203` and returned MERGE-WITH-FIXES. Its finding 1 "Changes a number… and an action", and findings 2–5 change actions.
  - The canopy reflog shows `9935b857` as a commit amended after C3 (00:08:29 -0500). It changes CHANGELOG, REPLAY_V2_FAQ and the test (+21/−15), and no lane has reviewed that change.
  - The ledger applies exactly this rule to #676's round 3 (LEDGER:8673-8676) but not here.
- **Fix:** record that a round 4 on `2f2bc203..9935b857` is owed before the PR opens.
- **Changes an action:** yes.

### 7. MINOR — the run-2 transcript entered git before the merge, not after

- **Quoted:** LEDGER:8638 "the transcript first entered git after the merge, in this phase's `5a0e4ea9`".
- **Evidence:**
  - `800c20bb`, committed 2026-09-23T20:41:35Z on local branch `worktree-squishy-dancing-moth` with parent `51993b37`, already holds the same blob (`4c2c5304`).
  - `5a0e4ea9`'s committer date is its rebase onto `f9c81d80`; its author date is 20:41:35Z.
  - The claim came from Lane R2-F's table and was not re-derived. LEDGER:8798's "(`5a0e4ea9`)" has the same provenance problem.
- **Fix:** "committed locally at 20:41Z (`800c20bb`, unpushed)".
- **Changes a number / disposition / action:** no.

### 8. MINOR — the owner question leaves out evidence the pass already had

- **Quoted:** LEDGER:8723 "one pass over nine PRs, 21:47Z to 22:51Z"; item 15 (LEDGER:9360-9365).
- **Evidence:**
  - **The same pattern that morning.** From the timelines, ml#2032 was armed at 13:23:19Z, ml#2045 ("feat(reports): add new SMART report files…") at 13:26:23Z and data#428 at 13:29:27Z. The archived scan has no call that armed any of them.
  - **Why the drafts existed.** `bc31e993`'s 20:28:41Z handoff is titled "…four-prs-armed-by-an-unseen-actor…". That is why those PRs were drafted at 20:24Z, which is the ledger's own "beyond both lanes" point.
  - **A signed commit two minutes before the pass.** R2-B reported `4c496443`: pcalnon-authored and committed, signature valid, on ml#2058 at 21:45:22Z, inside the window where no tool call was made. The pass dropped it.
  - **Two more actions of the account.** ml#2066 had a second update-branch at 22:50:21Z (`41379ff9`), and ml#2045's branch received commits dated 23:59:00Z–00:00:07Z. Neither is listed.
- **Fix:** add these to "Who" and to item 15.
- **Changes an action:** yes.

### 9. MINOR — the new tools refuse and redact less than stated

- **Quoted:** LEDGER:9156-9157 "It refuses any file holding an e-mail address other than a `noreply` one"; the README says "token shapes redacted".
- **Evidence:**
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py:122` exempts `@codecov.io` addresses.
  - A test in scratch using fake strings: `_refuse` returned False for `gho_…`, `ghs_…`, a JWT bearer token, `_someone@example.com` and `x@codecov.io`. It returned True for `ghp_…` and a plain address. `gho_` is the gh CLI's own token shape.
  - The launch scan has the same token gap and redacts no e-mail addresses.
  - The archived outputs are clean today: no `gh[ousr]_` shapes, and the six `@` hits are `@dataclass`, `@/tmp` and a grep pattern.
- **Fix:** widen both regexes, and state the codecov exemption.
- **Changes an action:** yes.

### 10. MINOR — the README still carries the claim round 2 refuted

- **Quoted:** `util/ad-hoc/README.md:720` "It answers 'could any session here have done it?'".
- **Evidence:** this is the exact line R2-B's finding 3 quoted. It is unchanged in the diff, while `:740` now says the launch scan answers what the activity window cannot.
- **Fix:** reword it.
- **Changes an action:** yes.

### 11. MINOR — item 0's command fails as written

- **Quoted:** LEDGER:9291 "`…canopy_verify_instance.bash up <canopy worktree on main> <port>`".
- **Evidence:** the script's usage (`:47`, `:58-61`) requires `<worktree-src-dir containing main.py>` and exits 2 otherwise.
- **Fix:** use `<worktree>/src`.
- **Changes an action:** yes.

### 12. NIT — two of F-059's line numbers belong to the unpushed branch

- **Quoted:** LEDGER:9093 "`replay_player_panel.py:114` … `:115`".
- **Evidence:** on `e9053227` those lines are `:112` and `:113`. `:114/:115` are `9935b857`'s numbers, while the same entry's `:505-506` and `:532` are `e9053227`'s. No artifact of the orchestrator's execution is archived.
- **Changes a number / disposition / action:** no.

### 13. NIT — "Phase 4 closed F-CANOPY-015 by test" (LEDGER:9101)

- **Evidence:** it contradicts Phase 4's STATUS CORRECTION (LEDGER:6143-6147, "remain OPEN") and LEDGER:9258. Neither F-015's entry (LEDGER:3932) nor Phase 4's row (LEDGER:6161, "fixed") points to F-059, whereas Phase 7's 204 line got an in-place note.
- **Changes a number / disposition / action:** no.

### 14. NIT — two merge dates are local, not UTC

- **Evidence:** cascor#178 merged at 2026-05-03T00:55:26Z and canopy#532 at 2026-08-28T04:16:14Z. LEDGER:9085 and LEDGER:9099 give the local dates, while the neighbouring F-057 history uses UTC.
- **Changes a number / disposition / action:** no.

### 15. NIT — "nothing in this pass is applied by hand" (corrections script `:16`) and LEDGER:9221 "with no hand edit"

- **Evidence:** the same commit hand-edits both census docstrings, the README and the handoff note, and no script produces them. The tmpfs evidence came from a different script. The ledger replay itself is exact.
- **Changes a number / disposition / action:** no.

### 16. NIT — new bare "§4" references

- **Evidence:** LEDGER:8674, 9166 and 9208, against the rule that every reference to a document carries its filename.
- **Changes a number / disposition / action:** no.

### 17. NIT — item 15 and the termination bullet are incomplete

- **Evidence:**
  - Item 15's list of local-only commits omits canopy `9935b857`, which is now cited at LEDGER:8763 and 9333.
  - LEDGER:8676 says "nothing was left on #676 to review", but item 13 still owes #676's PR-body edit.
- **Changes a number / disposition / action:** no.

### 18. NIT — the "204" claim survives in cited evidence

- **Evidence:**
  - ML-AH `2026-09-24_ledger_r2_laneB_census_synth_app.py:14` says "FEED_MODE=204 … (HTTP 204)". Its `app204.log` shows only 200s.
  - The 09-10 handoff's `:159` also repeats it.
  - So LEDGER:9213's "corrected wherever it stood" holds only for the ledger.
- **Changes a number / disposition / action:** no.

### 19. NIT — LEDGER:9356 "passed review of its logic"

- **Evidence:** no lane passed the census's logic. R2-F only matched the ledger's description of the script, and R2-B refuted it.
- **Changes a number / disposition / action:** no.

### 20. NIT — R2-B's census figures are report-only

- **Evidence:** the 13/13 and "0 of 2 fires" figures have no archived result. The ledger labels B1's equivalent figures report-only, but not these.
- **Changes a number / disposition / action:** no.

## CORRECTIONS YOU COULD NOT REFUTE

### The replay, the CI rows and the account's actions

- **The replay is exact.** Replaying `2026-09-24_phase9_ledger_round2_corrections.py` on `acf1a93a`'s ledger in scratch printed "applied 82 substitutions and 1 insertion", and `cmp` against `3f83b9c6` is identical.
- **The CI rows.** Run 35928632707:
  - Attempt 1: the macOS 3.12 unit job failed at 22:40:57Z, then the Quality Gate at 22:42:30Z.
  - Attempt 2: `run_started_at` 01:22:32Z, `triggering_actor` pcalnon, every job re-run, Quality Gate at 01:37:55Z.
  - The merge came at 01:38:02Z.
  - Both of those jobs are required under canopy's `strict` ruleset. The other required checks were done by 22:32:20Z.
- **The account's later actions.** ml#2066 `4392ab5a` at 23:16:06Z and merged at 23:24:21Z; data#434 `ae5a3b18` at 23:17:08Z and merged at 23:22:46Z; ml#2045 disarmed and re-armed at 23:48:47Z and 23:48:52Z; cascor-worker#196 merged at 01:21:37Z. The five Cursor checks went neutral at 22:28:07–12Z.

### F-CANOPY-059

- **The mechanism.** cascor `snapshots.py:449` and `manager.py:1165` return range as an always-truthy dict, introduced in `e01f57f` (#178). canopy's `confirm_snapshot_op` (`:1313-1325`) sets `active_tab="replay"`.
- **Executed.** I registered canopy's callbacks on a scratch Dash app and called `render_session`:
  - With Phase 1's measured payload it raises `KeyError(0)`.
  - With `[0, 12]` it renders the active view and "V2 ✓ weights".
  - An empty dict falls back cleanly.
- **The regression and its surroundings.**
  - Before #532 (`359e1bf7^`), `:476` read the top-level range, so this is a regression from #532.
  - There is exactly one range read in canopy `src`, and the session Store has two writers.
  - The idle text is "▶ No active replay session".
  - The fixture at `test_p2_wave_batch_a.py:179-190` types the range as `[3, 37]`.
  - The Phase 1 quote is at LEDGER:4212-4214.

### The 204 correction and the census refutation

- **The 204 correction**, Phase 7's line included:
  - dash 4.2.0 `_callback.py:602` sets `has_update = … or has_output`.
  - canopy `src` has no `PreventUpdate` and no background callbacks.
- **The census-refutation text** matches the renderer and the code:
  - Renderer: `:2627` (the synchronous `removeExecutedCallbacks`), `:2676` and `:2707` (`addExecutedCallbacks`), and `:3798` (`window.store`, also set in the minified build).
  - Census: `:296-301` (`took()`) and `:327` (`release_mid_request` is recorded but never read).
  - `e2e_f027_redrive.py:228` waits 3500 ms.

### Counts, the launch scan and the window

- **Counts.** The triage tool gives 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open. 1 open P0 (F-059); 6 open P1 (F-055, 056, 057, 058, F-CASCOR-001, 002).
- **The launch scan's stated facts.**
  - `gh pr ready 2020` at 06:09:09Z is the only readying command.
  - The last match is at 21:27:05Z.
  - The four background launches that name no PR are `detect.py`, `ceremony.py`, and two `run_rows_clean.bash` runs whose only match is a `/rerun` inside a log filename.
  - There is no `fleet_merge_train` run from 09-20 on.
- **The window.** It holds five records: one queue-operation at 21:53:09.035Z, and four records of the refused turn at 00:07:22–23Z. There is no tool_use in the window.
- **`ml#2058`.** `cdb0a18b` landed at 21:43:55Z, and the shepherd script's only write is `update-branch` (`:70`).

### F-CANOPY-058, the probabilities and F-057

- **F-058's cascades.** Fires at 57.8, 92.8, 152.8, 187.8 and 232.8 s.
  - Responses lost: 10 (seq 18–27), 3 (seq 42–44) and 4 (seq 53–56, still running at the end) = 17 of 56.
  - The two fires that evicted nothing landed 0.43 s and 0.33 s before the in-flight response, which is consistent with the new "more than one period" wording.
- **The probabilities.** 0.077–0.116, 0.146–0.184 and 0.086–0.127; the combined product is 0.013–0.023.
- **F-057.**
  - The facts for #180, #184, #187, #189 and #190 hold. `d85c9ddd` and `dbc25277` are absent from the local cascor clone.
  - The stream promises are at `USER_MANUAL.md:763-764` and `REPLAY_V2_FAQ.md:253`, and `9935b857` corrects both files.
  - cascor#674 is `f9818b01` (00:45:02Z); canopy#674 is `894a2cc7`.

### Other checks

- **The console-listener correction.** It holds: `e2e_w3_params_driver.py:209` and `:215` are unchanged since 09-23T02:19Z, and the run log has 0 CONSOLE lines across its 5 navigations.
- **The round-2 archive script.** `--dry-run` prints "would copy 0, already present 36".

### Walk of round 2's findings

- **R2-F:**
  - APPLIED: 1, 3, 5, 6, 8, 9, 10, 12, 13, 14, 15, 17, 20, 21, and 2 (as F-059, with findings 3, 4, 12 and 13 above).
  - APPLIED but weakened: 11 (findings 2 and 8); 18 (finding 1).
  - PARTLY: 4 (R misstated, and A2 #10's disposition is still unrecorded); 7 (finding 6); 16 (finding 17); 19 (finding 16).
- **R2-B:**
  - APPLIED: 1, 4, 5, 6, 7, 8, 10; 2 (with residue in finding 18); 9 (but see finding 5).
  - PARTLY: 3 (findings 2, 8 and 10).
  - 11: applied except the 94-vs-103 test count, which needs no change. The parent junit has 103 cases: 7+45+42 in the three files, plus 8 in `test_idle_dispatch_cuts` and 1 other.

## WHAT I COULD NOT CHECK

- **Nothing live:** no canopy, cascor or browser was run. F-059 and the REPLAYING lock-in rest on source plus executing the callback on its own. I could not check whether canopy's Reset is enabled while cascor is REPLAYING.
- **Who acted:** the actor and source (UI, API or host) of the arms, the ready, the re-run and `4c496443`.
- **Processes outside Claude Code transcripts:** I checked the user crontab (only clamscan and freshclam), the user systemd timers, and the current hook settings (none). I did not check system-level timers, other users, or what the hook settings were on 09-23.
- **dash 4.4.1** source is not installed.
- **R2-B's census figures** and R2-F's reflog reading.

**SECRETS/PII:** no slip. Every GitHub call was a GET that selected logins, times and SHAs, never e-mail fields. Transcript scans printed only timestamps, session ids, tool names and bounded command substrings, with e-mail addresses and tokens redacted. The refusal test used fake token strings, in scratch only. Nothing was written to any repository; scratch is in `…/scratchpad/r3b.V2Jgvs/`. There is an untracked file in the frozen worktree, `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py`, which I did not create.

---
