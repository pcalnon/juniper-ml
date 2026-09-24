#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-2 validation corrections (Lanes R2-F and R2-B) as exact substitutions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-2 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round1_corrections.py (round 1's pass)

WHY A SCRIPT. As in round 1: the ledger is ~720 KB and shared, so a scripted pass can be replayed on a fresh
copy of ``main``'s ledger if ``main`` moves before the upload. Every substitution must match exactly once, or
the script refuses and writes nothing. Unlike round 1, nothing in this pass is applied to the LEDGER by hand
(round 2 found that round 1's replay silently dropped the one bullet round 1 had hand-edited). The same commit
edited the scripts' docstrings, the README and the handoff's note directly (round 3, Lane R3-B).

Each entry names the lane finding it applies (F = R2-F, B = R2-B; N = a NIT). The orchestrator re-derived
every load-bearing single-lane finding before applying it (consensus procedure §5.2); the ledger's round-2
consensus bullet lists what was and was not re-derived.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"
PLAN = "`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`"

SUBS = [
    # --- Title and summary ----------------------------------------------------------------------------------
    (
        "F2: a fourth finding, P0",
        "F-CANOPY-055's first fix refuted in review, and three new findings\n",
        "F-CANOPY-055's first fix refuted in review, and four new findings, one of them P0\n",
    ),
    (
        "F1, F11, B3: the merge waited on a CI re-run; 'did not', not 'could not'",
        """  phase to land first (its PR body only). No Claude Code session on this host readied it or armed auto-merge,
  because every one was rate-limited or idle then (see "The merge, out of order" below). The change that landed
  is byte-identical to the reviewed `4b4cfb16`. The cuts were rebuilt on `main` from local `668380ec`.""",
        """  phase to land first (its PR body only). No Claude Code process on this host readied it or armed auto-merge,
  in the foreground or the background (see "The merge, out of order" below). The armed merge then waited on
  CI: the first run on its head, `5e52debb`, failed, and the `pcalnon` account re-ran it at 01:22:32Z. The
  change that landed is byte-identical to the reviewed `4b4cfb16`. The cuts were rebuilt on `main` from local
  `668380ec`.""",
    ),
    (
        "N55: name the two test-only changes",
        "  - The review corrected prose, plus two test-only changes:\n",
        "  - The review corrected prose, plus two test-only changes (`key=str`; the dict-id refusal):\n",
    ),
    (
        "F2, F8, F18: four findings; F-057 P1; F-058's scope; F-059",
        """- **Three new findings:**
  - F-CANOPY-056 and F-CANOPY-057, from the cuts' round-1 adversarial lane:
    - F-CANOPY-056: against cascor, the replay player drops every control's result, and a Stop keeps the
      session. The ledger's validation widened it from Stop alone and re-rated it P1.
    - F-CANOPY-057: the CAN-015g replay-weight stream is not wired end to end.
  - F-CANOPY-058, from F-055's round-1 adversarial lane: a `running=` guard is released by an evicted
    request's completion too, so one mid-request re-request or re-enable starts an eviction cascade.
  - All three were re-derived in source.""",
        """- **Four new findings:**
  - F-CANOPY-056 and F-CANOPY-057, from the cuts' round-1 adversarial lane:
    - F-CANOPY-056: against cascor, the replay player drops every control's result, and a Stop keeps the
      session. The ledger's validation widened it from Stop alone and re-rated it P1. Against cascor today it
      is masked: F-CANOPY-059 keeps the controls from rendering at all.
    - F-CANOPY-057: the CAN-015g replay-weight stream is not wired end to end. Round 2 of the ledger's
      validation re-rated it P1, because canopy's manual still promises the stream.
  - F-CANOPY-058, from F-055's round-1 adversarial lane: a `running=` guard is released by an evicted
    request's completion too, so a mid-request re-request, or a re-enable more than one period before the
    in-flight response lands, starts an eviction cascade.
  - **F-CANOPY-059 (P0)**, from round 2 of the ledger's validation: against cascor, the replay player never
    shows a session. canopy#532's fix for F-CANOPY-015 reads `range` where cascor serves a dict, and the
    readout indexes it as a list, so every render raises `KeyError: 0`. Phase 1 predicted this crash when it
    measured the payload (segment 7: "The obvious one-line fix crashes the panel").
  - All four were re-derived in source, and F-CANOPY-059 also by executing the callback.""",
    ),
    # --- The rebuild and the live check ---------------------------------------------------------------------
    (
        "N24: the driver's listener attaches before navigation",
        """  - **STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT** (X/C 0.79). Console errors were 0 in every window
    after page load. The listener attaches after load, so load-time errors are invisible to it.""",
        """  - **STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT** (X/C 0.79). Console errors were 0 in every window
    after page load. The check's own counter attaches after load, but the driver's listener attaches before
    navigation (`e2e_w3_params_driver.py:209`, `goto` at `:215`) and prints every console error or warning into
    the run's log, which holds none, load included (Lane R2-F; `phase9-scratch/orchestrator/idle_cuts_live_check_rebuilt.log`).""",
    ),
    (
        "N23, N26: C1's reads, and whose figure 32 s is",
        """    command was issued ~32 s after the suite's last write, and its first read came at 40 s. The suite ran""",
        """    command was issued ~32 s after the suite's last write (the ledger validation's Lane A2), and its first
    window read came at 40 s, after a health read at 34 s. The suite ran""",
    ),
    (
        "N22: 7.89 preceded the run's command",
        "    - 7.89 at the run's start (19:30:31Z) and 13.10 ten minutes in.",
        "    - 7.89 at 19:30:31Z, just before the run's command (19:30:37.9Z), and 13.10 ten minutes in.",
    ),
    # --- #676's review rounds ----------------------------------------------------------------------------------
    (
        "N34: round 1 listed more gaps than four",
        "    - It also listed instrument gaps in the live check:\n",
        "    - It also listed instrument gaps in the live check, among them:\n",
    ),
    (
        "N27: the reason given is the orchestrator's",
        """      `ticks_10s_cleared`, is a field the SESSION rule does use. Lane A could only argue it improbable, since the
      `disabled_after_s` read just before found the node present.""",
        """      `ticks_10s_cleared`, is a field the SESSION rule does use. Lane A could only argue it improbable. The
      reason, that the `disabled_after_s` read just before found the node present, is the orchestrator's.""",
    ),
    (
        "N28: Lane A refuted the stop claim too",
        """    - MAJOR: "stop clears it" was false. That became F-CANOPY-056 below.""",
        """    - MAJOR: "stop clears it" was false (Lane A found it too). That became F-CANOPY-056 below.""",
    ),
    (
        "N36: the renderer version",
        "    - the `@hash` readiness argument (`splitIdAndProp`, `getReadyCallbacks`; renderer lines cited);",
        "    - the `@hash` readiness argument (`splitIdAndProp`, `getReadyCallbacks`; dash 4.2.0 renderer lines cited);",
    ),
    (
        "F19, N31, N32: the procedure's filename; B2's limit and remedy",
        """- **Review, round 2** (Lane B2, briefed only on the corrections, §4): **MERGE-WITH-FIXES**, text plus one
  test-code change (the dict-id refusal). B2 reproduced every number it could check. It could not check the
  load readings or C1's start time.
  - **MAJOR:** the corrections cited ledger records that did not exist yet. The remedy was for this phase to
    land before #676 merged, with the canopy text citing only the finding IDs. The merge overtook it, so canopy
    `main` cited the IDs before they existed (see "The dangling citation" below).""",
        f"""- **Review, round 2** (Lane B2, briefed only on the corrections, per §4 of
  {PROC}): **MERGE-WITH-FIXES**, text
  plus one test-code change (the dict-id refusal). B2 reproduced every number it could check. It could not
  check the load readings, or that C1 started 40 s after the suite.
  - **MAJOR:** the corrections cited ledger records that did not exist yet. The remedy was for this phase to
    land before #676 merged, with the canopy text citing only the finding IDs and the run-2 transcript
    committed. The merge overtook it: canopy `main` cited the IDs before they existed (see "The dangling
    citation" below), and the transcript first entered git after the merge, in this phase's `5a0e4ea9`.""",
    ),
    (
        "N30: quote the g-3 comment exactly",
        """    - Four older comments contradicted the corrections, `ws_dash_bridge.js`'s "set by g-3's `_emit_frame`"
      among them.""",
        """    - Four older comments contradicted the corrections, `ws_dash_bridge.js`'s "g-3's
      `_ReplaySession._emit_frame`" among them.""",
    ),
    (
        "F10: applied to the tree and the message, not the PR body",
        """  - All were applied. The authoring session's run of eight named files passed 168 tests (archived log, no
    SHA).""",
        """  - All were applied to the tree and the commit message. The PR description kept text rounds 1 and 2 had
    corrected, which round 3 then flagged (below). The authoring session's run of eight named files passed 168
    tests (archived log, no SHA).""",
    ),
    (
        "N35: 14 s, and the edit fixed more",
        """    8; the old parent SHA; and two commits. The "two commits" text had been corrected 15 s after B3 read it.""",
        """    8; the old parent SHA; and two commits. The "two commits" text had been corrected 14 s after B3 read it, in
    an edit that fixed more than that.""",
    ),
    (
        "F9, F19: the round had not terminated under §4",
        """  - **§4:** the round changed no disposition. Its verdict's fixes were wording in the squash message and the PR
    body, to be applied before the merge with an explicit decision on a round 4. The merge overtook both (next
    bullet), so no round 4 ran: nothing was left on #676 to review. Its no-action NITs are carried in Still owed
    item 13.""",
        f"""  - **Termination** (§4 of {PROC}): the review had NOT
    terminated. B3 marked both MINORs as changing a number and an action, so §4 called for a round 4 on their
    fixes, which were wording in the squash message and the PR body. The merge overtook both (next bullet), so
    no round 4 ran: nothing was left on #676 to review. Its no-action NITs are carried in Still owed item 13.""",
    ),
    # --- The merge, out of order -------------------------------------------------------------------------------
    (
        "N47, F1: committed events carry no actor; the CI rows' source",
        """  and its commit dates. Every event's actor is `pcalnon`, none was performed by a GitHub App
  (`performed_via_github_app` is null), and two retitles are omitted:""",
        """  and its commit dates. Every event that records an actor names `pcalnon` (committed events record none),
  none was performed by a GitHub App (`performed_via_github_app` is null), and two retitles are omitted. The CI
  rows are from the Actions API (`gh api repos/pcalnon/juniper-canopy/actions/runs/35928632707/attempts/{1,2}/jobs`,
  added in round 2 of the ledger's validation):""",
    ),
    (
        "F1: the failed CI and the re-run that released the merge",
        """  | 2026-09-24 01:38:02 | **merged** as `e9053227` |""",
        """  | 22:40:57 | CI on `5e52debb` (run 35928632707, attempt 1) fails its "Unit Tests + Coverage (Python 3.12 on macos-latest)" job, then its Quality Gate at 22:42:30, so the armed merge cannot fire |
  | 2026-09-24 01:22:32 | **CI re-run** (attempt 2), triggered by `pcalnon`; its Quality Gate passes at 01:37:55 |
  | 01:38:02 | **merged** as `e9053227`, seven seconds after the re-run's Quality Gate |""",
    ),
    (
        "B3, F11: 'Who' re-based on launches, not tool calls",
        """    - **No Claude Code session on this host could have done it.** Every session active before 21:41Z hit the
      weekly rate limit between 21:30:11Z and 21:41:01Z. From 21:41:02Z to 01:40Z no session on this host made a
      single tool call; the only entry is a new prompt the limit refused at 00:07:23Z
      (`util/ad-hoc/2026-09-24_host_session_activity_window.py`, which prints ids, counts and timestamps only).""",
        """    - **No Claude Code process on this host readied or armed it, in the foreground or the background.** This
      basis replaced a first one that Lane R2-B refuted in round 2 of the ledger's validation.
      - **Launches, not tool calls.** `util/ad-hoc/2026-09-24_merge_command_launch_scan.py` lists every Bash
        call whose command line could ready, arm, merge, update-branch or re-run a PR (outputs in
        `reports/e2e-canopy-2026-09-02/phase9-scratch/ledger_r2_orchestrator/`). The only draft-readying
        command any session ran on 09-23 was `gh pr ready 2020`, at 06:09Z. None of that day's 38 matching
        background launches names a PR of the pass below or of the later actions: 34 name one PR each, and the
        other four name none within the 220 characters the scan keeps. None that could ready a draft was
        launched from 09-20 on, and the last matching call of any kind was at 21:27:05Z. The one repo script
        that readies drafts, `util/ad-hoc/2026-09-05_fleet_merge_train.py`, was not run that day.
      - **Why launches.** A count of tool calls, the first basis, cannot see a process launched before its
        window. Session `317c1df2`'s background shepherd (`2026-09-22_shepherd_automerge.bash 2058 60 180`,
        launched 20:39:42Z; its only write is `update-branch`) updated ml#2058's branch at 21:43:55Z
        (`cdb0a18b`), inside the window below, and reported completion at 21:53:09Z.
      - **The window.** The sessions working at 21:30Z hit the weekly rate limit between 21:30:11Z and
        21:41:01Z; the authoring session (`259b4d16`) and four subagents, idle since 21:25:49Z or earlier, hit
        none. From 21:41:02Z to 01:40Z no session made a tool call. Among the window's five transcript entries
        (Lane R2-B's count) are the shepherd's completion notice and a new prompt the limit refused at 00:07:23Z
        (`util/ad-hoc/2026-09-24_host_session_activity_window.py`, which prints ids, counts and timestamps only).""",
    ),
    (
        "F16: b54e3b3f's rebased copy",
        "      handoff (`b54e3b3f`, committed 21:00:59Z) records #676 as a draft with no auto-merge.",
        """      handoff (`b54e3b3f`, committed 21:00:59Z; rebased onto this branch as `f6861234`) records #676 as a draft
      with no auto-merge.""",
    ),
    (
        "N46, N54, F1: no causal clause; which drafts; the account's later actions",
        """      #676 is the only one with an update-branch between its ready and its arm, which is where its 8 s comes
      from.""",
        """      - #676 is the only one with an update-branch between its ready and its arm.
      - The drafts it readied were the ones sessions had drafted to hold them: `259b4d16` drafted #676 at
        19:44Z, `bc31e993` drafted data#428, ml#2032 and ml#2059 at 20:24Z, and `e6c1cb6d` drafted data#431 and
        data#434 at 21:26Z (the launch scan above).
    - **The account kept acting after the pass** (Lane R2-F; re-derived from the timelines and commit dates):
      update-branches on ml#2066 (`4392ab5a`, 23:16:06Z) and data#434 (`ae5a3b18`, 23:17:08Z), which merged at
      23:24:21Z and 23:22:46Z; ml#2045 disarmed and re-armed at 23:48:47–52Z; cascor-worker#196 merged at
      01:21:37Z; and #676's CI re-run at 01:22:32Z, without which its armed merge could not have fired. A
      background shepherd can update a branch, but none of the day's launches names ml#2066 or data#434.""",
    ),
    (
        "B NIT: the Cursor checks at the ready",
        """      held before the ready: every successful or skipped check on `4b4cfb16` had finished by 20:59:25Z. The""",
        """      held before the ready: every successful or skipped check on `4b4cfb16` had finished by 20:59:25Z (five
      Cursor checks then went neutral at 22:28:07–12Z, the seconds of the ready and the arm; Lane R2-B). The""",
    ),
    (
        "F1: the owner question covers the later actions",
        """    - The actor is unidentified. It acts as `pcalnon`, the owner's account. **Owner question**: was that pass
      his? (Still owed, item 15.)""",
        """    - The actor is unidentified. It acts as `pcalnon`, the owner's account, and it is not Claude Code on this
      host. **Owner question**: were that pass and the later actions his? (Still owed, item 15.)""",
    ),
    (
        "N45: #677 overlaps nothing",
        "    `main`. `main`'s tree also carries #677 and #678, which overlap it only in `CHANGELOG.md`.",
        """    `main`. `main`'s tree also carries #677, which overlaps it nowhere, and #678, which overlaps it only in
    `CHANGELOG.md`.""",
    ),
    (
        "C2/C3: five statements, not four",
        "    trailer rewrite), so canopy's history now carries four statements this ledger corrects:",
        "    trailer rewrite), so canopy's history now carries five statements this ledger corrects:",
    ),
    (
        "N44: c0530279 is #670's first commit",
        """    - "Two timers were half of the page's steady-state ticks": the static census of `c0530279` (canopy#670's head,
      whose Interval layout matches #676's parent) gives 3.0 of the 6.6 ticks per second the layout's enabled""",
        """    - "Two timers were half of the page's steady-state ticks": the static census of `c0530279` (canopy#670's first
      commit; its final head is `bc357d09`), whose Interval layout matches #676's parent, gives 3.0 of the 6.6
      ticks per second the layout's enabled""",
    ),
    (
        "C2/C3: the fifth statement",
        """    - "Comments that claimed cascor emits weights … are corrected": `ws_dash_bridge.js:113-115` still said "(see
      g-3 emitter)".""",
        """    - "Comments that claimed cascor emits weights … are corrected": `ws_dash_bridge.js:113-115` still said "(see
      g-3 emitter)";
    - "the drain runs until the page reloads, as it always ran before": a successful model select also ends it,
      by rebuilding the tab bar (F-CANOPY-056's "How a session does end").""",
    ),
    (
        "F7: the follow-up exists",
        """    fragility; on GitHub, #676's stale PR description. The first two are owed as a canopy follow-up PR, the third
    as an edit of #676's description (Still owed, item 13).""",
        """    fragility; on GitHub, #676's stale PR description. The first two are fixed on canopy branch
    `fix/idle-cuts-round3-wording` (local `9935b857`, not yet pushed), which opens as a PR after this phase
    lands; the third is an edit of #676's description (Still owed, item 13).""",
    ),
    (
        "N48: only the CHANGELOG carries the ledger phrase",
        """  - **The dangling citation.** From 01:38:02Z until this phase merged, canopy `main`'s CHANGELOG and comments cited
    F-CANOPY-056 and F-CANOPY-057 "in the juniper-ml E2E evidence ledger", which did not yet contain them.""",
        """  - **The dangling citation.** From 01:38:02Z until this phase merged, canopy `main`'s CHANGELOG cited F-CANOPY-056
    and F-CANOPY-057 "in the juniper-ml E2E evidence ledger", and its comments cited the IDs, before the ledger
    contained them.""",
    ),
    # --- F-CANOPY-055's first fix ------------------------------------------------------------------------------
    (
        "N43: the commit said 'silences'",
        "  - The lane is `(lane, None)` in `_GATED_POLL_INTERVALS`. The commit claimed that the CAN-000 clamp reaches it",
        "  - The lane is `(lane, None)` in `_GATED_POLL_INTERVALS`. The commit claimed that the CAN-000 clamp silences it",
    ),
    (
        "N42: the AST count includes inherited tests",
        "    re-derives from an AST count (+7, +10, +0).",
        "    re-derives from an AST count that includes inherited tests (+7, +10, +0; a plain count gives +7, +2, +0).",
    ),
    (
        "F12, N38: the script was in git; only its predictions entered later",
        """  browser at a time). Its predictions were added to its docstring before each run; only the session transcript
  shows that, because the script entered git after the runs. `delivered` counts HTTP responses, while
  `watched` and `executed` count the renderer's callback objects, which run one or two ahead at a window's
  edges:""",
        """  browser at a time). Its predictions were added to its docstring before each run. The script was in git from
  `51993b37` (17:07:01Z), but those docstring edits entered git only after the runs (`5a0e4ea9`), so only the
  session transcript shows the order. `delivered` counts HTTP responses, while `watched` and `executed` count
  the renderer's callback objects, which run one or two ahead at a window's edges or after a network failure:""",
    ),
    (
        "N37: the two readings of ~8.6 s",
        """    estimator. The census docstring's ~8.6 s is the mean gap between latency changes, and that skips repeated
    values. `running=` releases the lane from `completeJob()`, which runs when the page's main thread takes the""",
        """    estimator. The census docstring's ~8.6 s is either the mean gap between latency changes (8.69 s), which skips
    repeated values, or 60 s over 7 responses (8.57 s). `running=` releases the lane from `completeJob()`, which
    runs when the page's main thread takes the""",
    ),
    (
        "N43: 13.0 s is a lower bound",
        "| **LANDS**, 13.0 s after page load |",
        "| **LANDS**, 13.0 s after page load (a lower bound) |",
    ),
    (
        "N41: the line numbers are 884d22fb's",
        "    - **MAJOR, the tests pass on code that fails in a browser.** `test_poll_gating.py:406-408` exempts global",
        """    - **MAJOR, the tests pass on code that fails in a browser.** `test_poll_gating.py:406-408` (at `884d22fb`;
      `:311-313` at `e9053227`) exempts global""",
    ),
    (
        "B NIT: main carries no F-055 node test",
        """      - CI runs the node test. Settled 2026-09-24: none of the six skips in CI's Python 3.13 unit job on
        `e9053227` is the node test. GitHub's ubuntu image ships node, although `ci.yml` has no setup-node step.""",
        """      - CI runs the node test. Settled 2026-09-24 for `main`'s node-gated test, #614's metrics-store watchdog
        (the F-055 fix's own node tests were never on `main`): none of the six skips in CI's Python 3.13 unit job
        on `e9053227` is node-gated. GitHub's ubuntu image ships node, although `ci.yml` has no setup-node step.""",
    ),
    (
        "F3, F4, B5: the probability's basis, and Lane B's archived no-fire run",
        """      Neither produced a cascade on canopy. That is weak evidence against Lane B's modelled false-fire rate (at
      that rate, no fire in 210 s has a probability of about 0.15–0.18) and against a mount-time strand. The
      census does not record fires, so "no fire" is inferred from the applies. 28 of 29 watched callbacks
      executed across the two fix runs' 210 s, and 27 responses were delivered on the wire.""",
        """      Neither produced a cascade on canopy. The census does not record fires, so "no fire" is inferred from the
      applies, and only an evicting fire would show: 28 of 29 watched callbacks executed across the two fix
      runs' 210 s, and 27 responses were delivered on the wire.
    - **What that says about Lane B's model** (corrected in round 2 of the ledger's validation). At the 37–44
      fires an hour stated above, no fire in 210 s has a probability of 0.08–0.12. The census could see only
      EVICTING fires, which Lane B modelled at 29–33 an hour; no evicting fire in 210 s then has a probability
      of about 0.15–0.18 (the ledger validation's Lane A2). Lane B's own archived run at a similar per-request
      time, which records fires directly, saw none either: `phase9-scratch/f055_r1_laneB/run_watchdog.json`,
      R = 7 ± 1 s with the gate's mount write and the watchdog on, 23 of 23 applied and no fire in about 200 s
      (0.086–0.127 under the model; Lane R2-F). Together the two have a probability of about 0.013–0.023 under
      the model, so its rate is probably too high at this per-request time. The mechanism rests on source and
      on Lane B's run at R = 3 ± 2 s (F-CANOPY-058 below); the rate on a real page is unmeasured.""",
    ),
    # --- F-CANOPY-056 --------------------------------------------------------------------------------------------
    (
        "F2: the session view claims are masked by F-059",
        "and a Stop never clears it; the player stays in its session view and the weight drain keeps running until the page reloads or a successful model select rebuilds the tab bar (P1,",
        "and a Stop never clears it, and the weight drain keeps running until the page reloads or a successful model select rebuilds the tab bar; masked today by F-CANOPY-059, which keeps the player's controls from rendering at all (P1,",
    ),
    (
        "N49: the attribution was the round-1 corrections'",
        "  - Round 2 corrected round 1's attribution: cascor's own echo of the id is nested under `data`/`result`, and\n",
        "  - Round 2 corrected an attribution the round-1 corrections (`2fa134f8`) had made: cascor's own echo of the id\n    is nested under `data`/`result`, and\n",
    ),
    (
        "F2: Lane B's session was built by hand",
        """  and `render_session` kept the active view with a `REPLAYING` badge.""",
        """  and `render_session` kept the active view with a `REPLAYING` badge. That session was built by hand. One that
  `confirm_snapshot_op` stores from cascor's real `/replay` response makes `render_session` raise before it
  renders anything (F-CANOPY-059), so against cascor today the active view never appears and no control is
  reachable (Lane R2-F, round 2 of the ledger's validation).""",
    ),
    (
        "F2, N52: the probe's sessions; `playing`",
        """  speed(−5) left `speed` at 1.0; seek(40) left `time_index.current` at 0; play left `playing` at None; stop
  kept `snapshot_id` and REPLAYING. This is F-CANOPY-013's envelope-nesting class on a third site, which
  canopy#532's sweep missed. It rests on source and a probe; it has not been driven live.""",
        """  speed(−5) left `speed` at 1.0; seek(40) left `time_index.current` at 0; play left `playing` unset (a session
  `confirm_snapshot_op` stores starts it False, and it stays False); stop kept `snapshot_id` and REPLAYING.
  This is F-CANOPY-013's envelope-nesting class on a third site, which canopy#532's sweep missed. It rests on
  source and a probe whose sessions were built by hand. It has not been driven live, and against cascor it
  cannot be until F-CANOPY-059 is fixed.""",
    ),
    (
        "F19, F2: the plan's filename; P1 while masked",
        """- **Re-rated P1**, on plan §6.3's rule ("breaks a documented behaviour"). `docs/USER_MANUAL.md` documents the
  controls' readouts, and against cascor none of them reflects a control. The finding was P2 while it was
  scoped to Stop.""",
        f"""- **Re-rated P1**, on plan §6.3's rule ("breaks a documented behaviour";
  {PLAN}). `docs/USER_MANUAL.md` documents
  the controls' readouts, and against cascor none of them reflects a control. The finding was P2 while it was
  scoped to Stop. It stays P1 while F-CANOPY-059 masks it, because fixing F-059 exposes it at once.""",
    ),
    (
        "F7: cite Lane C's report",
        "- **How a session does end** (Lane C of the canopy follow-up, re-derived in source): a successful model select",
        """- **How a session does end** (Lane C of the canopy follow-up, in
  `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`; re-derived in
  source): a successful model select""",
    ),
    (
        "F2: F-059 first",
        "  could not be verified live without starting a replay on the shared trio's cascor.\n",
        "  could not be verified live without starting a replay on the shared trio's cascor. F-CANOPY-059's fix comes\n  first, since until then no control renders.\n",
    ),
    # --- F-CANOPY-057 --------------------------------------------------------------------------------------------
    (
        "F8, B10: F-057 re-rated P1",
        "(P2, canopy + cascor; found 2026-09-23 by the cuts' round-1 adversarial lane; OPEN).**",
        "(P1 while canopy's manual and FAQ promise the stream, re-rated 2026-09-24; canopy + cascor; found 2026-09-23 by the cuts' round-1 adversarial lane; OPEN).**",
    ),
    (
        "B9, N51, C2/C3: the history's self-contradiction; the base; cascor#184",
        """- **History** (Lane B1 of the ledger's validation, re-derived with `gh`). The g-3 emitter was merged twice,
  both times into a stacked feature branch that never reached `main`:
  - cascor#187, into `feature/can-015g-2-replay-weight-cache`, at 2026-05-03T07:31:04Z (`d85c9ddd`);
  - its retarget cascor#190, into `feature/can-015g-2-replay-weight-cache-v2`, at 20:05:12Z (`dbc25277`). That was
    13 minutes after the branch's own PR, cascor#189, had landed on `main`.
  - `dbc25277` has diverged from `main`: 3 ahead, 512 behind. Round-1 Lane B's "not in the local cascor object
    store" was an artifact of a local fetch.""",
        """- **History** (Lane B1 of the ledger's validation, re-derived with `gh`; corrected in round 2). The g-3 emitter
  was merged twice, both times into a stacked base branch after that branch had itself landed, so neither merge
  reached `main`:
  - cascor#187, into `feature/can-015g-2-replay-weight-cache`, at 2026-05-03T07:31:04Z (`d85c9ddd`);
  - its retarget cascor#190, into `feature/can-015g-2-replay-weight-cache-v2`, at 20:05:12Z (`dbc25277`), 13
    minutes after that branch's own PR, cascor#189, had landed on `main` as `b1d19948` (19:52:10Z).
  - `dbc25277` has diverged from cascor `main` `0e016a7c`: 3 ahead, 512 behind. Round-1 Lane B found neither
    commit in the local cascor clone, which is still true, since no local branch carries them; its inference
    that they were never merged was the error.
  - The same pattern a third time (Lane R2-B; re-derived with `gh`): cascor#184 merged into
    `feature/can-015g-1-snapshot-weight-history` at 06:03:30Z, 3 h 57 min after that branch's own PR, cascor#180,
    had landed on `main` (02:06:37Z).""",
    ),
    (
        "B9: #184 joins the sweep",
        """- **Fix direction:** re-land #190's diff on cascor and add `weights` to canopy's relay key set. Also sweep cascor
  for other stacked PRs merged into a base that had already landed.""",
        """- **Fix direction:** re-land #190's diff on cascor and add `weights` to canopy's relay key set. Also sweep cascor
  for other stacked PRs merged into a base that had already landed. cascor#184 is one; whether its diff reached
  `main` by another route is unchecked.""",
    ),
    (
        "F8, B10, F19: the severity paragraph",
        """- **Severity.** P2, because the canopy follow-up corrects the docs that promised the stream
  (`docs/USER_MANUAL.md` and `notes/development/REPLAY_V2_FAQ.md`). Until that merges, the manual documents a
  behaviour that does not exist, which on plan §6.3's rule argues P1.""",
        f"""- **Severity: P1**, re-rated in round 2 of the ledger's validation (Lanes R2-F and R2-B). canopy `main` still
  promises the stream (`docs/USER_MANUAL.md:764`, `notes/development/REPLAY_V2_FAQ.md:253`), and plan §6.3's rule
  ({PLAN}) makes a documented behaviour that does
  not exist P1, the rule that made F-CANOPY-056 P1. It returns to P2 when the canopy follow-up that corrects both
  files merges (branch `fix/idle-cuts-round3-wording`, Still owed item 13); that re-rating is owed with the
  merge.""",
    ),
    # --- F-CANOPY-058 --------------------------------------------------------------------------------------------
    (
        "F18: the class statement's scope",
        "so any mid-request re-request or re-enable of the guarded lane starts an eviction cascade, and the lane's responses can stop applying for minutes",
        "so a mid-request re-request, or a re-enable more than one period before the in-flight response lands, starts an eviction cascade, and the lane's responses can stop applying for minutes",
    ),
    (
        "N50: 4.4.1's definition and calls",
        """  canopy's `requirements.lock` ships 4.4.1, where the same code is at `:979-991`. A 200 whose body fails to
  parse never reaches `completeJob()`.""",
        """  canopy's `requirements.lock` ships 4.4.1, where `completeJob` is defined at `:979-991` and called at `:1020`,
  `:1024`, `:1033` and `:1037`. A 200 whose body fails to parse never reaches `completeJob()`.""",
    ),
    (
        "F18: not every trigger cascades, and not every cascade lasts",
        """- **The trigger.** Anything that re-requests or re-enables the lane mid-request. A re-enable restarts the
  Interval's timer, so it ticks one period later and evicts the in-flight request; a re-request evicts it
  directly. The evicted request's late completion then re-enables the lane under its successor, and the two
  chains keep evicting each other. The sources:""",
        """- **The trigger.** Anything that re-requests or re-enables the lane mid-request. A re-enable restarts the
  Interval's timer, so it ticks one period later and evicts the in-flight request if its response has not
  landed by then; a re-request evicts it directly. The evicted request's late completion then re-enables the
  lane under its successor, and the two chains can keep evicting each other. Not every trigger cascades, and
  not every cascade lasts (Lane R2-F; re-derived from the archived run): in Lane B's run at R = 3 ± 2 s
  (`phase9-scratch/f055_r1_laneB/run_watchdog_r3.json`), the fires at 57.8 s and 152.8 s evicted nothing. Of
  the three that did, two cascades ended by themselves, after 10 and 3 lost responses, and the third was still
  running when the run ended; 17 of 56 responses were lost in all. The sources:""",
    ),
    (
        "F4: Lane B's archived mount-write run",
        """    during #613's live verification and this phase's 150 s census (20 of 20 applied);""",
        """    during #613's live verification, this phase's 150 s census (20 of 20 applied) and Lane B's own archived
    watchdog run at R = 7 ± 1 s (`run_watchdog.json`: 23 of 23 applied, no fire);""",
    ),
    (
        "F17, B6: B1's figures are report-only; its repro is archived",
        """    mid-request change of the second Input gave 0 applied of 45 responses over 90 s, twice, against 23 of 23 in
    the no-trigger control, twice.""",
        """    mid-request change of the second Input gave 0 applied of 45 responses over 90 s, twice, against 23 of 23 in
    the no-trigger control, twice. Those figures are B1's report. Its app, driver and server log are archived
    (`util/ad-hoc/2026-09-24_ledger_r1_laneB1_second_input_{app,drive}.py`, `phase9-scratch/ledger_r1_laneB1/`),
    and the log fits the request counts only.""",
    ),
    (
        "B6: fix_callbacks.json; which figures R2-F re-created",
        """  `reports/e2e-canopy-2026-09-02/phase9-scratch/f055_r1_laneB/`). Six of its figures (7 of 7, 0 of 51, 4 of 4
  then 0 of 28, 352 s, 0 of 21, 37–44 an hour) have no surviving raw output; its scripts can re-create them.""",
        """  `reports/e2e-canopy-2026-09-02/phase9-scratch/f055_r1_laneB/`), with the `fix_callbacks.json` its repro reads
  (added in round 2, in `f055_r1_laneB/fix/`; the repro opens it at `util/ad-hoc/fix/`). Six of its figures (7 of
  7, 0 of 51, 4 of 4 then 0 of 28, 352 s, 0 of 21, 37–44 an hour) have no surviving raw output. Its scripts can
  re-create them, and round 2's Lane R2-F re-created two: the 352 s, and the 37–44 an hour.""",
    ),
    (
        "B2: a no_update answer is a 200 with an empty response, not a 204",
        """- **NOT yet observed on canopy itself.** Live confirmation is owed (Still owed, item 0). It must count
  evictions, not applies: on the idle trio every response after the first is a 204, so an applies count
  cannot tell a healthy lane from a stalled one.""",
        """- **NOT yet observed on canopy itself.** Live confirmation is owed (Still owed, item 0). It must count
  evictions, not applies. On the idle trio the feeder answers `no_update`, which applies nothing, so an applies
  count cannot tell a healthy lane from a stalled one. Such an answer is HTTP 200 with an empty `response`, not
  a 204 as this entry first said: in dash 4.2.0 a callback with outputs sets `has_update = … or has_output`
  (`_callback.py:602`), so it never raises `PreventUpdate` (Lane R2-B, round 2; 4.4.1 has the same code at
  `:695-699`, by R2-B's reading of the wheel).""",
    ),
    # --- Instruments -----------------------------------------------------------------------------------------------
    (
        "F13: the status-bar census docstring now holds the 150 s result",
        """- `2026-09-23_status_bar_apply_census.py`: the fix verification's predictions and results, recorded in its
  docstring before and after each run. The rule is untouched.""",
        """- `2026-09-23_status_bar_apply_census.py`: the fix verification's predictions and results, recorded in its
  docstring before and after each run. The 150 s run's result, and corrections to its "~8.6 s" and "F-035's …
  cadence again", were added on 2026-09-24 (round 2, Lane R2-F). The rule is untouched.""",
    ),
    (
        "F14, F7: the reports, and every brief",
        """  and the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2}.md`.""",
        """  the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2}.md`; and the canopy
  follow-up's review, `…/2026-09-24_validator_reports_phase9_canopy_followup.md`. Every lane's brief is in
  `reports/e2e-canopy-2026-09-02/drafts/`.""",
    ),
    (
        "B1, B7, F15: the census refuted; round 1's script is not a full replay; the new tools",
        """  - `2026-09-24_f058_trigger_census.py`: F-CANOPY-058's live confirmation, per-request evictions keyed by
    `executionPromise`, and five triggers. Its rule and predictions are fixed; it has not yet run.
  - `2026-09-24_phase9_ledger_round1_corrections.py`: this pass, as replayable substitutions.""",
        """  - `2026-09-24_f058_trigger_census.py`: F-CANOPY-058's live confirmation, per-request evictions keyed by
    `executionPromise`, and five triggers. **Refuted before its first run** (Lane R2-B, on a synthetic dash 4.2.0
    app running the census's own JavaScript; the mechanism re-derived by the orchestrator in the renderer
    source):
    - An answer that carries no props leaves `executed` inside the same synchronous dispatch that put it there
      (`removeExecutedCallbacks`, `dash_renderer.dev.js:2627`). A store subscriber never sees it there and
      scores it EVICTED: 13 of 13 `no_update` answers, against 13 of 13 data answers APPLIED.
    - Its fire detector reads the lane after the fire's own `false` write, so it counted 0 of 2 real fires.
    - T-apply is scored even with nothing in flight, `took()` skips its "still in flight" check, and T-tab's
      second click lands ~4.5 s after the first, not 1 s.
    - Its docstring now says so. Do not run it as written (Still owed, item 0). The synthetic apps are
      `2026-09-24_ledger_r2_laneB_{census,watchdog}_synth_{app,drive}.py`.
  - `2026-09-24_phase9_ledger_round1_corrections.py`: round 1's pass, as 56 replayable substitutions. It is
    not the whole pass: the consensus bullet "This phase's own text" was edited by hand, so a replay onto a
    moved `main` must re-apply it (Lanes R2-F and R2-B).
  - `2026-09-24_phase9_ledger_round2_corrections.py`: round 2's pass, entirely scripted.
  - `2026-09-24_merge_command_launch_scan.py`: every Claude Code Bash call on this host that could ready, arm,
    merge, update-branch or re-run a PR, in a window, with its background flag.
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py`: the rest of this phase's tmpfs evidence, round 2's
    included, from two sessions' scratchpads. It refuses any file holding an e-mail address other than a
    `noreply` one.""",
    ),
    # --- Consensus record --------------------------------------------------------------------------------------------
    (
        "F19: the procedure's filename in the heading",
        "### Consensus record (procedure §7)\n\n- **canopy#676 (the cuts).**\n",
        f"### Consensus record (§7 of {PROC})\n\n- **canopy#676 (the cuts).**\n",
    ),
    (
        "F9: #676's round 3 had not terminated",
        """    The merge overtook it: #676 landed with those fixes unapplied (see "The merge, out of order").""",
        """    The review had not terminated under §4, since B3's two MINORs each changed a number and an action. The
    merge overtook it: #676 landed with those fixes unapplied (see "The merge, out of order").""",
    ),
    (
        "N39: one window VOID; fires not recorded",
        """  - The census that passed (two fix windows with 27 responses delivered, against one parent window) held no
    tab switch and no Apply, so it could not produce the failure those triggers cause. It could have seen a
    watchdog false fire or a mount-time strand, and saw neither.""",
        """  - The census that passed (a 150 s fix window scored APPLIES after a 60 s one VOIDed, 27 responses delivered
    across the two, against one parent window) held no tab switch and no Apply, so it could not produce the
    failure those triggers cause. It could have seen an evicting watchdog false fire or a mount-time strand, as a
    drop in applies, and saw neither; it records no fires directly.""",
    ),
    (
        "F5: A1 and A2's mismatches were corrected",
        """  - **Verdicts.** A1 and A2 matched every number they could re-derive, and found wording, attribution and
    unit defects. B1 and B2 returned SOUND-WITH-FIXES.""",
        """  - **Verdicts.** A1 and A2 re-derived most numbers exactly. Their MISMATCH rows (A1's G6; A2's R2.e, R2.f,
    R2.h, R4.a–d and R5.b) were all corrected, alongside wording, attribution and unit defects. B1 and B2
    returned SOUND-WITH-FIXES.""",
    ),
    (
        "F15, B4, B2, and the round-2 record",
        """    - about forty wording, unit and attribution fixes. All are in
      `util/ad-hoc/2026-09-24_phase9_ledger_round1_corrections.py`.
  - **Re-derived before applying.** The orchestrator re-derived every load-bearing single-lane finding: the
    rate-limit window, the nine-PR pass, the checks' completion times, the stacked cascor PRs,
    `_merge_session`'s overlay, CI's node skips and the X/C band.""",
        """    - wording, unit and attribution fixes: 56 substitutions in
      `util/ad-hoc/2026-09-24_phase9_ledger_round1_corrections.py`, plus this bullet, which was edited by hand, so
      a replay of the script alone drops it.
  - **Re-derived before applying.** The orchestrator re-derived the rate-limit window, the nine-PR pass, the
    checks' completion times, the stacked cascor PRs, `_merge_session`'s overlay, CI's node skips and the X/C
    band. It did NOT re-derive Lane B1's claim that every answer after the first is a 204, which round 2
    refuted.
  - **Round 2**: two lanes on the frozen `acf1a93a`, briefed separately. Lane R2-F re-derived the whole phase
    from its primary artifacts; Lane R2-B attacked round 1's corrections, the new census included. Both returned
    SOUND-WITH-FIXES, and both said §4 required a round 3.
  - **What round 2 changed:**
    - a new finding, F-CANOPY-059 (P0), which qualifies F-CANOPY-056's claims about the session view;
    - one disposition: F-CANOPY-057 re-rated P1;
    - the counts: 70 findings, 19 open, 1 open P0 and 6 open P1;
    - the F-058 census, refuted before its first run, and the 204 claim, corrected wherever it stood (Phase 7's
      line included);
    - the merge record: CI's failure and the 01:22:32Z re-run, the account's later actions, and the "Who"
      basis, now a scan of launches rather than a count of tool calls;
    - F-CANOPY-058's scope, and the census probability's basis;
    - F-CANOPY-057's history, and cascor#184;
    - Still owed items 0, 3 to 9 (back-references), 13, 14 and 15, and a new item 16;
    - the rest: wording, attribution and pointer fixes, and the tmpfs evidence both lanes found unarchived. All
      are in `util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py`, with no hand edit.
  - **Re-derived before applying (round 2):** CI's two attempts and their jobs (Actions API); the `KeyError`, by
    executing the registered callback on the payload Phase 1 measured (segment 7) and, as a control, on the
    F-CANOPY-015 fixture's list shape, which renders; cascor's dict `range` since cascor#178 (`e01f57f`); dash
    4.2.0's `has_output`; the renderer's synchronous `removeExecutedCallbacks`; ml#2058's `cdb0a18b` at
    21:43:55Z and the shepherd's single write; the later actions on ml#2066, data#434, ml#2045 and
    cascor-worker#196; cascor#180 and #184, and both #674s; the fifth squash-message statement; and Lane B's two
    archived watchdog runs. Not re-derived: R2-F's reading of the host reflogs, R2-B's count of five window
    entries, and R2-B's synthetic census runs, whose mechanism was re-derived in the renderer source instead.
    New, beyond both lanes: the launch scan, and the finding that the drafts the pass readied were exactly the
    ones sessions had drafted to hold.""",
    ),
    (
        "F2: F-056's scope on a live page",
        "  - F-CANOPY-056's widened scope on a live page (a probe with constructed envelopes; never driven);",
        """  - F-CANOPY-056's widened scope on a live page (a probe with constructed envelopes on sessions built by hand;
    never driven, and masked against cascor by F-CANOPY-059);
  - F-CANOPY-059 on a live page: it rests on executing the callback with the payload shape Phase 1 measured
    live, not on a drive;
  - that the F-058 census works: round 2 refuted it before any run;""",
    ),
    (
        "F1, B3: who, beyond Claude Code on this host",
        """  - who readied and armed canopy#676, beyond "no Claude Code session on this host";""",
        """  - who readied and armed canopy#676, or re-ran its CI, beyond "no Claude Code process on this host"
    (foreground calls and background launches, checked by their command lines);""",
    ),
    # --- Matrix effect and counts --------------------------------------------------------------------------------------
    (
        "F2, F8: new finding, re-rating, counts",
        """- **New**: F-CANOPY-056 (re-rated P1 on 2026-09-24, above), F-CANOPY-057 (P2) and F-CANOPY-058 (P1).
- **Counts**, from `e2e_finding_triage.py` (run it to confirm):
  - **69 findings**: 48 fixed, 1 accepted, 2 withdrawn, **18 open**.
  - **5 of the open are P1**: F-CANOPY-055, F-CANOPY-056, F-CANOPY-058, F-CASCOR-001 and F-CASCOR-002.""",
        """- **New**: F-CANOPY-056 and F-CANOPY-057 (both re-rated P1 on 2026-09-24, above), F-CANOPY-058 (P1) and
  F-CANOPY-059 (P0).
- **F-CANOPY-015**: stays **OPEN** (P2), awaiting its live re-drive (Phase 4's status correction). That re-drive
  cannot pass until F-CANOPY-059, which F-015's own fix introduced, is fixed.
- **Counts**, from `e2e_finding_triage.py` (run it to confirm):
  - **70 findings**: 48 fixed, 1 accepted, 2 withdrawn, **19 open**.
  - **1 of the open is P0**: F-CANOPY-059.
  - **6 of the open are P1**: F-CANOPY-055, F-CANOPY-056, F-CANOPY-057, F-CANOPY-058, F-CASCOR-001 and
    F-CASCOR-002.""",
    ),
    # --- Still owed ------------------------------------------------------------------------------------------------------
    (
        "new item 16",
        "- Items 13, 14 and 15 are new.\n",
        "- Items 13, 14, 15 and 16 are new.\n",
    ),
    (
        "B1, B2, F-actionability: item 0's census, and how to stand up the leg",
        """   - First, confirm F-CANOPY-058 live on a leg serving `main`, counting EVICTIONS, not applies: on the idle
     trio every response after the first is a 204. `util/ad-hoc/2026-09-24_f058_trigger_census.py` is ready for
     it. It drives five triggers (a gate write, a tab switch, an Apply clamp and release, a display-mode change,
     and 10 idle minutes), with its rule and predictions fixed, and has not yet run. It simulates the Apply
     through the clamp Store, because a real Apply PATCHes the trio's cascor.""",
        """   - First, confirm F-CANOPY-058 live on a leg serving `main`, counting EVICTIONS, not applies: on the idle
     trio the feeder answers `no_update`, an HTTP 200 that applies nothing. The census written for this,
     `util/ad-hoc/2026-09-24_f058_trigger_census.py`, was **refuted before its first run** (Instruments, above):
     it scores every answer without props EVICTED and cannot count a watchdog fire. Fix it first:
     - record the executed transition itself: wrap `window.store.dispatch` and log `addExecutedCallbacks` by
       `executionPromise`, or install a shim with `add_init_script` before the renderer builds its store;
     - detect a fire from the lane's state before the reset;
     - score T-apply only with a request in flight, and check "still in flight" in `took()`;
     - then pass a synthetic check on a scratch dash app, with and without `no_update` answers, before any live
       run.
     It drives five triggers (a gate write, a tab switch, an Apply clamp and release, a display-mode change, and
     10 idle minutes), and simulates the Apply through the clamp Store, because a real Apply PATCHes the trio's
     cascor.
   - A leg serving `main`: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy worktree on main>
     <port>`, with `JUNIPER_E2E_CANOPY_URL` exported for the drivers. It reads the trio's `:8101` data and
     `:8202` cascor and must not write them; never use `:8051`.""",
    ),
    (
        "B NIT: Phase 8's condition on the allow-arm leg",
        """     triggers on the fix's leg, and F-CANOPY-025's allow arm re-driven on a leg where the old code fails (Phase 8
     item 2's second half).""",
        """     triggers on the fix's leg, and F-CANOPY-025's allow arm re-driven on a leg where the old code fails and
     whose training may be started (Phase 8 item 2's second half).""",
    ),
    (
        "F-actionability: item 3's pointer",
        "3. **Owner: F-CANOPY-004's contract.**\n",
        "3. **Owner: F-CANOPY-004's contract** (Phase 8 item 4; the question itself is Phase 7 item 5).\n",
    ),
    (
        "F-actionability: item 4's pointer",
        "4. **`FULL_HISTORY_POLL_TICK_MODULUS` → 1.**\n",
        "4. **`FULL_HISTORY_POLL_TICK_MODULUS` → 1** (Phase 8 item 5; the decision and its measurement are Phase 7\n   item 6).\n",
    ),
    (
        "F-actionability: item 5's pointer",
        "5. **canopy#613's guard, source-derived and unobserved.** Superseded by F-CANOPY-058 (item 0).",
        "5. **canopy#613's guard, source-derived and unobserved** (Phase 8 item 6). Superseded by F-CANOPY-058 (item 0).",
    ),
    (
        "F6: the right #674",
        "6. **F-CANOPY-049** and #674's follow-ups. #674 merged on 2026-09-23 as `894a2cc7`.\n",
        """6. **F-CANOPY-049** and cascor#674's follow-ups (Phase 8 item 7; the follow-ups are Phase 7 item 8).
   cascor#674 merged on 2026-09-23T00:45:02Z as `f9818b01` ("an unserializable broadcast is the message's
   fault"). This item first cited `894a2cc7`, which is canopy#674.
""",
    ),
    (
        "F-actionability, F2: item 7",
        "7. **CAN-015's replay-player loop.** Now joined by F-CANOPY-056, now P1, and F-CANOPY-057.\n",
        "7. **CAN-015's replay-player loop** (Phase 8 item 8; the trigger shape is Phase 7 item 9). Now joined by\n   F-CANOPY-056 and F-CANOPY-057, both P1, behind F-CANOPY-059 (item 16).\n",
    ),
    (
        "F-actionability: item 8's pointer",
        "8. **M-CANDIDATES-10/-11.**\n",
        "8. **M-CANDIDATES-10/-11** (Phase 8 item 9), now re-drivable (Phase 7 item 10).\n",
    ),
    (
        "F-actionability: item 9's pointer",
        """9. Unchanged: M-DATASET-17..26 (the owner's question), the M-TOPOLOGY-16 fade half, and F-038's browser-level
   test gap.""",
        """9. Unchanged (Phase 8 item 10; Phase 7 item 11): M-DATASET-17..26 (the owner's question), the M-TOPOLOGY-16
   fade half, and F-038's browser-level test gap.""",
    ),
    (
        "F-actionability: an owner for the instrument gaps",
        "      `ticks_10s_cleared` keeps no raw counts; and the script records no host load.\n",
        "      `ticks_10s_cleared` keeps no raw counts; and the script records no host load. Fix them before\n      `2026-09-23_idle_cuts_live_check.py` runs again.\n",
    ),
    (
        "F7, F20: item 13's heading and the existing follow-up",
        "    - **Round 3's fixes, which the merge left unapplied.** Owed as one canopy follow-up PR:\n",
        """    - **Round 3's findings and no-action NITs, now scheduled, with Lane C's additions.** Done as one canopy
      follow-up, branch `fix/idle-cuts-round3-wording` (local commit `9935b857` on `e9053227`, not yet pushed),
      which opens as a PR after this phase lands, the order #676 broke. Its review, Lanes C, C2 and C3, is in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. It
      covers:
""",
    ),
    (
        "F10, F-actionability: the PR body's stale phrases and the edit method",
        "    - #676's PR description, refreshed on the merged PR. That is an edit of the PR, not part of the follow-up.\n",
        """    - #676's PR description, refreshed on the merged PR with `gh api -X PATCH repos/pcalnon/juniper-canopy/pulls/676`
      (`gh pr edit` fails on gh 2.46.0). It still says "answered a third slower", "all seven files", "`main`
      `3a6dea95`", "Round 3 … running" and "lands before this PR merges". That is an edit of the PR, not part of
      the follow-up.
""",
    ),
    (
        "F21, B2: item 14's rule, and a fourth",
        """    - Count an observable that differs between pass and fail on that leg. On the idle trio an applies count
      cannot, since every response after the first is a 204; count evictions.""",
        """    - Count an observable that differs between pass and fail on that leg. An applies count does only where the
      feeder returns data: the F-055 census's status-bar feeder always does, and applies separated its legs (0
      against 19 latency changes). #613's feeder answers `no_update` on the idle trio, an HTTP 200 that applies
      nothing, so there count evictions, with an instrument shown to count them.
    - Run the instrument on a synthetic case whose answer is known, both ways, before trusting it live. The
      F-058 census passed review of its logic and failed its first synthetic run (item 0).""",
    ),
    (
        "F1, F16, F8: item 15 widened; the commit list; ratings; and item 16",
        """    - Was the 21:47–22:51Z pass over nine PRs his? If not, nothing held a PR that night: not a disarm, a draft
      or a comment. Only a PR that does not yet exist is held.
    - F-CANOPY-056's re-rating to P1, on plan §6.3's rule.
    - Served canopy commits that exist only in the local clone: `ce78e0de`, `78c057e2`, `668380ec`,
      `723ee812`, `884d22fb`, `cf6fb1dc` and `7a4a2e33`. Push them to a provenance ref on canopy's remote, or
      accept that a lost clone loses them.""",
        f"""    - Were the 21:47–22:51Z pass over nine PRs, and the account's later actions, his? Those are the update-branches
      on ml#2066 and data#434 (23:16–23:17Z), ml#2045's disarm and re-arm (23:48Z), cascor-worker#196's merge
      (01:21:37Z) and #676's CI re-run (01:22:32Z), without which its armed merge could not fire. No Claude Code
      process on this host did any of them ("Who", above). Lane R2-F reports interactive git activity in host
      reflogs from about 21:39Z to 00:07Z (not re-derived). If they were not his, nothing held a PR that night:
      not a disarm, a draft or a comment. Only a PR that does not yet exist is held.
    - The ratings on plan §6.3's rule ({PLAN}): F-CANOPY-056 and
      F-CANOPY-057 P1, F-CANOPY-059 P0.
    - Local-only commits this ledger cites. Canopy, served: `ce78e0de`, `78c057e2`, `668380ec`, `723ee812` and
      `884d22fb`; canopy, cited but never served: `cf6fb1dc`, `7a4a2e33`, `8990f65c`, `5310b81a`, `c360fb53` and
      `040dc5c1`; juniper-ml: `ada8e50c`, and `b54e3b3f`, whose rebased copy on this branch is `f6861234`. Push
      them to a provenance ref on each remote (for example `refs/provenance/canopy-e2e-phase9`), or accept that
      a lost clone loses them.
16. **New: F-CANOPY-059's fix, first in the replay loop** (item 7).
    - Convert cascor's `range` dict to `[start, end]` wherever canopy reads it: `render_session`'s readout
      (`replay_player_panel.py:532`) and the range slider's value, keeping a list, or no range, working.
    - Its regression test must use the payload Phase 1 measured (segment 7), not a typed list. Correct
      `test_p2_wave_batch_a.py:179-190`, whose fixture says it is "the exact shape measured off the running
      service" and is not, and sweep the other fixtures that make the same claim.
    - Then F-CANOPY-015's live re-drive, then F-CANOPY-056's fix, which needs a reachable control to verify.
      Each of these drives starts a replay, so each needs a cascor that may be written, not the shared trio's.""",
    ),
    # --- Phase 7's 204 claim, corrected in place ----------------------------------------------------------------------
    (
        "B2: Phase 7's 204",
        "    204 `no_update` runs at page load and on every tab change.\n",
        "    `no_update` runs at page load and on every tab change (HTTP 200 with an empty `response`, not the 204\n    first written here; corrected in Phase 9, round 2 of its validation).\n",
    ),
]

NEW_FINDING = """
**F-CANOPY-059 — against cascor, the CAN-015 replay player never shows a session: canopy#532's fix for F-CANOPY-015 reads `range` from `data.session`, where cascor serves a dict, and the readout indexes it as a list, so `render_session` raises `KeyError: 0` on every session cascor serves and the Replay tab stays at "▶ No active replay session" with no control reachable (P0, canopy repo; a regression from canopy#532; found 2026-09-24 by round 2 of this phase's validation, Lane R2-F; OPEN).**

- **The mechanism.** cascor's `/replay` route nests `state_summary()` at `data.session`
  (`src/api/routes/snapshots.py:449`), and `state_summary()` returns `"range": {"start": …, "end": …}`, a dict,
  as it has since cascor#178 (`e01f57f`, 2026-05-02). `confirm_snapshot_op` stores that `data` block as the
  session (`hdf5_snapshots_panel.py:1313-1323`). `render_session` then takes
  `range_value = summary.get("range") or [start, end]` (`replay_player_panel.py:505-506`) and formats
  `f"[{range_value[0]}, {range_value[1]}]"` (`:532`): `KeyError: 0`. Nothing in canopy converts the dict.
- **Executed, not only read** (the orchestrator, re-deriving Lane R2-F's finding): the registered callback,
  called on a session built from the payload Phase 1 measured live, raises `KeyError(0)`; the same session with
  the range as the list `[0, 12]` renders the active view and the `V2 ✓ weights` badge. Dash applies none of a
  callback's outputs when it raises, so the layout defaults stand: the idle placeholder shown
  (`replay_player_panel.py:114`), the controls hidden (`:115`).
- **What a user sees.** A successful Replay switches to the Replay tab, which says "▶ No active replay session"
  while cascor replays. Play, pause, seek, speed, range and Stop are never on screen. Every later write of the
  session Store re-raises.
- **How it shipped.** Phase 1 predicted it when it measured this payload (segment 7): "Reading one level deeper
  without converting dict → list turns a silently-wrong readout into a `KeyError`. The obvious one-line fix
  crashes the panel." canopy#532 (`359e1bf7`, 2026-08-27) made that fix, and its test passes because its fixture,
  labelled "The exact shape measured off the running service", types the range as `[3, 37]`
  (`src/tests/unit/frontend/test_p2_wave_batch_a.py:179-190`). Phase 4 closed F-CANOPY-015 by test, pending a
  live re-drive that never ran.
- **Severity: P0**, on plan §6.3's rule (`JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`):
  it blocks a workflow the mandate names, "snapshots saving/loading/replaying" (§1.1(d)). It also masks
  F-CANOPY-056, whose controls it keeps off screen.
- **Not yet driven live.** A drive starts a replay, which writes the cascor it runs against; the shared trio's
  must not be written. The fix and its live check are Still owed item 16.
"""

ANCHOR = "\n### Instruments\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    text = LEDGER.read_text(encoding="utf-8")
    bad = []
    for why, old, new in SUBS:
        n = text.count(old)
        if n != 1:
            bad.append((n, why, old[:90]))
            continue
        text = text.replace(old, new)
    # The new finding goes after F-CANOPY-058, at the end of "New findings", before "Instruments".
    if text.count(ANCHOR) != 1:
        bad.append((text.count(ANCHOR), "the F-CANOPY-059 anchor", ANCHOR))
    else:
        text = text.replace(ANCHOR, NEW_FINDING + ANCHOR)
    if bad:
        for n, why, head in bad:
            print(f"REFUSED: {n} matches for [{why}]: {head!r}", file=sys.stderr)
        return 1
    if not args.dry_run:
        LEDGER.write_text(text, encoding="utf-8")
    print(f"{'would apply' if args.dry_run else 'applied'} {len(SUBS)} substitutions and 1 insertion to {LEDGER.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
