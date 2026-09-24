#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-1 validation corrections (Lanes A1, A2, B1, B2) as exact substitutions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-1 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round1.md

WHY A SCRIPT. The ledger is ~720 KB and shared with concurrent sessions. A scripted pass can be replayed on a
fresh copy of ``main``'s ledger if ``main`` moves before the upload, instead of hand-merging. Every
substitution must match exactly once, or the script refuses and writes nothing.

Each entry names the lane(s) whose finding it applies. The orchestrator re-derived every load-bearing
single-lane finding before applying it (consensus procedure §5.2); where it could not, the text says so.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round1_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

SUBS = [
    # --- Summary ------------------------------------------------------------------------------------------
    (
        "B2 #6, #9; the rate-limit exclusion",
        """  and without round 3's wording fixes.** It was held as a draft for exactly that order. An actor that no session
  on this host recorded readied it and armed auto-merge (see "The merge, out of order" below). What landed is
  byte-identical to the reviewed `4b4cfb16`. The cuts were rebuilt on `main` from local `668380ec`.
  - The live check against the PR's own parent scored STRUCTURE and SESSION PASS and LATENCY INCONSISTENT.""",
        """  and without round 3's wording fixes.** It was held as a draft: for round 1 (its PR comment), then for this
  phase to land first (its PR body only). No Claude Code session on this host readied it or armed auto-merge,
  because every one was rate-limited or idle then (see "The merge, out of order" below). The change that landed
  is byte-identical to the reviewed `4b4cfb16`. The cuts were rebuilt on `main` from local `668380ec`.
  - The live check of the rebuilt cuts (`ce78e0de`) against `3a6dea95`, the PR's parent at the time, scored
    STRUCTURE and SESSION PASS and LATENCY INCONSISTENT.""",
    ),
    (
        "A2 #4; A2 R5.b; B1 #1, #13",
        """  - The census, with its rule unchanged, scored the parent NEVER-APPLIES and the fix APPLIES. F-CANOPY-025's
    allow arm landed on the fix, on demo legs.
  - Round-1 Lane B then returned **DO-NOT-MERGE**. Three ordinary events re-enable the guarded lane mid-request:
    - a tab switch, through the fused gate's write;
    - the end of an Apply;
    - the strand watchdog's false fires.
  - Every completion releases the guard, an evicted request's included, so the eviction then sustains itself.
  - The census window contained none of those triggers. The class also reaches #613's metrics-store lane in
    production. That is F-CANOPY-058 below.""",
        """  - The census, with its rule unchanged, scored the parent NEVER-APPLIES and the fix APPLIES. F-CANOPY-025's
    allow arm landed on the fix and on the parent alike, on demo legs, so that drive does not discriminate.
  - Round-1 Lane B then returned **DO-NOT-MERGE**. Ordinary events re-request or re-enable the guarded lane
    mid-request:
    - a tab switch, through the fused gate's write;
    - the end of an Apply, the same gate write;
    - the strand watchdog's false fires;
    - on #613's lane, a change of the feeder's second Input (added by the ledger's validation, Lane B1).
  - Each completion that reaches `completeJob()` releases the guard, an evicted request's included, so the
    eviction then sustains itself.
  - The census windows held no tab switch and no Apply. The watchdog was armed and the gate's mount write
    fired, and neither produced a cascade on canopy. The class also reaches #613's metrics-store lane in
    production. That is F-CANOPY-058 below.""",
    ),
    (
        "B1 #4",
        """    - F-CANOPY-056: Stop keeps the replay session against cascor.""",
        """    - F-CANOPY-056: against cascor, the replay player drops every control's result, and a Stop keeps the
      session. The ledger's validation widened it from Stop alone and re-rated it P1.""",
    ),
    (
        "B1 #1, #13",
        """  - F-CANOPY-058, from F-055's round-1 adversarial lane: a `running=` guard is released by every completion,
    so one mid-request re-enable starts an eviction cascade.""",
        """  - F-CANOPY-058, from F-055's round-1 adversarial lane: a `running=` guard is released by an evicted
    request's completion too, so one mid-request re-request or re-enable starts an eviction cascade.""",
    ),
    # --- The idle cuts --------------------------------------------------------------------------------------
    (
        "A1 #2",
        """- **The rebuild.** Local `668380ec` (built on `723ee812`, canopy#670's branch, never pushed) was""",
        """- **The rebuild.** Local `668380ec` (built on `723ee812`, a local merge commit on canopy#670's branch; neither was
  pushed) was""",
    ),
    (
        "A2 R4.g",
        """  - Lane A re-derived the count from the progress characters, and the collection count at `ce78e0de` (6810)
    agrees.""",
        """  - Lane A re-derived the count from the progress characters, and the collection count at `ce78e0de` (6810)
    agrees. The log carries no SHA, so "at `ce78e0de`" is corroborated only indirectly (Lane A). It is archived
    as `reports/e2e-canopy-2026-09-02/phase9-scratch/orchestrator/cuts_full_suite.log`.""",
    ),
    (
        "A2 R5.f",
        """  - **STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT** (X/C 0.79). Console errors were 0 in every window.""",
        """  - **STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT** (X/C 0.79). Console errors were 0 in every window
    after page load. The listener attaches after load, so load-time errors are invisible to it.""",
    ),
    (
        "A2 #8 (the band re-read at idle_cuts_live_check.py:42)",
        """  - **The latency prediction was wrong.** X2 was 1.48% slower than C2 and 2.66% slower than C3. The rule was
    not changed and the run was not repeated.""",
        """  - **The latency prediction was half wrong.** X/C 0.79 fell inside its predicted band (0.60–0.85), but the
    predicted CONSISTENT verdict failed: X2 was 1.48% slower than C2 and 2.66% slower than C3. The rule was not
    changed and the run was not repeated.""",
    ),
    (
        "A2 #9",
        """  - **C1 is an outlier** (Lane A). It started 40 s after the full suite finished on the same host, in the
    worktree the cuts leg served from. Without C1, X/C is 0.88; the verdict does not depend on it.""",
        """  - **C1 is an outlier** (Lane A). It started 32–40 s after the full suite finished on the same host: the run
    command was issued ~32 s after the suite's last write, and its first read came at 40 s. The suite ran
    19:22:18Z–19:30:05Z, in the worktree the cuts leg served from, and overlapped both legs' launches. Without
    C1, X/C is 0.88; the verdict does not depend on it.""",
    ),
    (
        "A1 #4; A2 R4.i",
        """  - **Host load.** These are my `uptime` readings; the script records none, so Lane A scored the figure NO
    ARTIFACT.
    - 7.89 at the run's start (19:30:31Z) and 13.10 ten minutes in.
    - Two `clamscan` processes were at ~80% CPU each, plus other sessions' test runs.""",
        """  - **Host load.** These are the authoring session's `uptime` readings. The script records none, so Lane A
    scored the figure NO ARTIFACT; the readings survive only in that session's transcript (`259b4d16`).
    - 7.89 at the run's start (19:30:31Z) and 13.10 ten minutes in.
    - Two `clamscan` processes read 84.2% and 80.8% CPU. Those are `ps` lifetime averages, not the load at the
      time. Other sessions' test runs were also active.""",
    ),
    (
        "A1 G6; A2 R4.e",
        """  - **Rule provenance** (Lane A).
    - Run 1's "rule fixed before the first run" is UNTRACEABLE: the script and its JSON entered git together
      in `51993b37`, 3.5 h after the run.
    - Run 2's rule is traceable: the script was on `main` from 17:07Z, and run 2 began at 19:30Z.""",
        """  - **Rule provenance.**
    - Run 1's "rule fixed before the first run" is UNTRACEABLE (Lane A). The script and its JSON first entered
      git together in local `ada8e50c` at 16:26:49Z, about 2 h 52 min after the run, and reached `main` in
      `51993b37` at 17:07:01Z, about 3.5 h after it.
    - Run 2's rule is traceable (the orchestrator's check, re-derived by the ledger's validation): the script was
      on `main` from 17:07Z, and run 2 began at 19:30Z.""",
    ),
    (
        "A2 R4.a",
        """    - M1–M6 all MATCH, including the served SHAs, which it traced through `/proc/<pid>/cwd` without touching
      the ports.""",
        """    - Every number in M1–M6 matched, including the served SHAs, which it traced through `/proc/<pid>/cwd`
      without touching the ports. Its report still carried qualifiers: M1c ("one sentence") was a wording
      MISMATCH, and M6's "at `ce78e0de`" was corroborated only indirectly.""",
    ),
    (
        "A2 R4.d",
        """    - None changed this run's verdicts. The raw records rule each gap out, or the rule does not use the
      field.""",
        """    - None changed this run's verdicts. The raw records rule out three of the gaps. The fourth,
      `ticks_10s_cleared`, is a field the SESSION rule does use. Lane A could only argue it improbable, since the
      `disabled_after_s` read just before found the node present.""",
    ),
    (
        "B2 #2; A2 R4.c",
        """- **Review, round 2** (Lane B2, briefed only on the corrections, §4): **MERGE-WITH-FIXES, text only.** B2
  reproduced every number.
  - **MAJOR:** the corrections cited ledger records that did not exist yet. So this phase lands before
    #676 merges, and the canopy text cites the finding IDs.""",
        """- **Review, round 2** (Lane B2, briefed only on the corrections, §4): **MERGE-WITH-FIXES**, text plus one
  test-code change (the dict-id refusal). B2 reproduced every number it could check. It could not check the
  load readings or C1's start time.
  - **MAJOR:** the corrections cited ledger records that did not exist yet. The remedy was for this phase to
    land before #676 merged, with the canopy text citing only the finding IDs. The merge overtook it, so canopy
    `main` cited the IDs before they existed (see "The dangling citation" below).""",
    ),
    (
        "Lane C of the canopy follow-up (re-derived in dashboard_manager.py)",
        """    - "runs only while a replay session exists" survived in five places. Against cascor the drain runs until
      reload.""",
        """    - "runs only while a replay session exists" survived in five places. Against cascor the drain runs until
      the page reloads, or until a successful model select rebuilds the tab bar (see F-CANOPY-056).""",
    ),
    (
        "A2 R4.l, R5.g",
        """  - All were applied: 168 affected tests pass, and pre-commit is clean.""",
        """  - All were applied. The authoring session's run of eight named files passed 168 tests (archived log, no
    SHA). Its pre-commit run on four files, with the output filtered, showed no failure. B3's later pinned run on
    all 8 PR files was clean.""",
    ),
    (
        "B2 #2",
        """- **Review, round 3** (Lane B3, briefed only on the round-2 corrections): **MERGE-WITH-FIXES, text only.**""",
        """- **Review, round 3** (Lane B3, briefed only on the round-2 corrections): **MERGE-WITH-FIXES**. Its verdict
  named the squash message and the PR body, and it marked its code-file NITs no-action.""",
    ),
    (
        "A1 #1",
        """  - **MINOR:** the PR description still carried text rounds 1 and 2 corrected, plus stale counts: 7 files, not
    8; the old parent SHA; and two commits.""",
        """  - **MINOR:** the PR description still carried text rounds 1 and 2 corrected, plus stale counts: 7 files, not
    8; the old parent SHA; and two commits. The "two commits" text had been corrected 15 s after B3 read it.""",
    ),
    (
        "B2 #1",
        """    - F-CANOPY-056/057 exist only in this unpushed phase (it confirms the ledger-first order);""",
        """    - F-CANOPY-056/057 existed only in this then-unpushed phase, which confirmed the ledger-first order the
      merge later broke;""",
    ),
    (
        "B2 #2",
        """  - **§4:** the round changed no disposition. Its fixes are wording in the squash message and the PR body.
    They were to be applied before the merge, with an explicit decision on a round 4. The merge overtook both
    (next bullet), so no round 4 ran: nothing was left on #676 to review.""",
        """  - **§4:** the round changed no disposition. Its verdict's fixes were wording in the squash message and the PR
    body, to be applied before the merge with an explicit decision on a round 4. The merge overtook both (next
    bullet), so no round 4 ran: nothing was left on #676 to review. Its no-action NITs are carried in Still owed
    item 13.""",
    ),
    (
        "A1 G1 actor; B1 #13; the app check",
        """  and its commit dates. Every event reads `pcalnon`:""",
        """  and its commit dates. Every event's actor is `pcalnon`, none was performed by a GitHub App
  (`performed_via_github_app` is null), and two retitles are omitted:""",
    ),
    (
        "A1 G1 row 5; B1 #13",
        """  | 22:28:12 | **auto-merge armed** (squash), storing `4b4cfb16`'s own message as the squash body |""",
        """  | 22:28:12 | **auto-merge armed** (squash), storing `4b4cfb16`'s message as the squash body; GitHub adds "(#676)" to the title and rewrites the co-author trailer |""",
    ),
    (
        "B2 #4",
        """  | 22:29:31 | `5e52debb`, a second "Merge branch 'main'" |""",
        """  | 22:29:31 | `5e52debb`, a second "Merge branch 'main'", ten seconds after canopy#678's direct merge moved `main` |""",
    ),
    (
        "B2 #4, #5, #6, #11; A1 G4 instrument notes; re-derived with 2026-09-24_host_session_activity_window.py and gh",
        """  - **Who.**
    - The authoring session's transcript (`259b4d16`) holds `gh pr ready 676 --undo` and no ready or arm command.
      Its last entry is at 21:01:29Z, 87 minutes before the ready. The phase's WIP handoff was committed at
      21:00:59Z and records #676 as a draft with no auto-merge.
    - No transcript under `~/.claude/projects/` on this host holds a ready or an arm of canopy#676. The only other
      match was juniper-cascor#676.
    - The ready-then-arm pair, 8 s apart, fits the same night's sweep of drafted PRs: ml#2059 at 21:47:22Z, ml#2032
      at 22:27:20Z and data#428 at 22:29:55Z, each readied and armed 4–7 s apart.
    - The actor is unidentified. It acts as `pcalnon`, so GitHub cannot tell it from the owner or any session.""",
        """  - **Who.**
    - **No Claude Code session on this host could have done it.** Every session active before 21:41Z hit the
      weekly rate limit between 21:30:11Z and 21:41:01Z. From 21:41:02Z to 01:40Z no session on this host made a
      single tool call; the only entry is a new prompt the limit refused at 00:07:23Z
      (`util/ad-hoc/2026-09-24_host_session_activity_window.py`, which prints ids, counts and timestamps only).
    - The authoring session's transcript (`259b4d16`) executed `gh pr ready 676 --undo` and no ready or arm. Its
      handoff's prose mentions `gh pr ready 676`, but that is text, not a command. Its last timestamped entry is
      at 21:01:29Z, 87 minutes before the ready; the session stayed open, idle, until about 03:27Z. Its WIP
      handoff (`b54e3b3f`, committed 21:00:59Z) records #676 as a draft with no auto-merge.
    - A grep of every transcript under `~/.claude/projects/` finds no executed ready or arm of canopy#676; the
      only other match is juniper-cascor#676. A transcript scan sees only Claude Code on this host: not the
      GitHub UI, other hosts, cloud sessions or automations.
    - **It was one pass over nine PRs**, 21:47Z to 22:51Z, from their timelines:
      - readied, then armed 4–8 s later, drafts from three sessions: ml#2059 21:47:22Z, ml#2032 22:27:20Z,
        canopy#676 22:28:04Z, data#428 22:29:55Z, data#431 22:50:54Z and data#434 22:51:07Z;
      - armed, not a draft: ml#2066 22:27:08Z;
      - merged directly, with no arm event: canopy#678 22:29:21Z and data-client#212 22:30:44Z.
      #676 is the only one with an update-branch between its ready and its arm, which is where its 8 s comes
      from.
    - **What the hold said.** The draft comment's condition was round 1 plus green checks: "It will be marked
      ready and merged with util/safe_merge.py once that round reports and required checks are green." Both
      held before the ready: every successful or skipped check on `4b4cfb16` had finished by 20:59:25Z. The
      ledger-first order and round 3 appeared only in the PR body. So the ready met the comment's literal
      condition; the arm, which the comment asked no one to do, did not.
    - The actor is unidentified. It acts as `pcalnon`, the owner's account. **Owner question**: was that pass
      his? (Still owed, item 15.)""",
    ),
    (
        "B2 #9",
        """    `index` and hunk-offset lines (445 lines each, `cmp` exit 0). The head round 3 reviewed is what is on
    `main`.""",
        """    `index` and hunk-offset lines (445 lines each, `cmp` exit 0). The change round 3 reviewed is the change on
    `main`. `main`'s tree also carries #677 and #678, which overlap it only in `CHANGELOG.md`.""",
    ),
    (
        "B2 #3; A1 G3c and #3",
        """  - **What landed that round 3 said to fix.** `e9053227`'s message is `4b4cfb16`'s, so canopy's history now
    carries three statements this ledger corrects:
    - "(two rounds; prose corrections only)": there were three rounds, and rounds 1 and 2 each changed test code;
    - "A live check of this build against its parent": the pair checked was `ce78e0de` against `3a6dea95`;
    - "Two timers were half of the page's steady-state ticks": the census gives 3.0 of 6.6, which is 45%.
  - **Still unfixed on `main`:** round 3's wording survivors in the PR's files, and the stale PR description. Both
    are owed as a canopy follow-up (Still owed, item 13).""",
        """  - **What landed that round 3 said to fix.** `e9053227`'s message is `4b4cfb16`'s (plus "(#676)" and GitHub's
    trailer rewrite), so canopy's history now carries four statements this ledger corrects:
    - "(two rounds; prose corrections only)": there were three rounds, and rounds 1 and 2 each changed test code;
    - "A live check of this build against its parent": the pair checked was `ce78e0de` against `3a6dea95`;
    - "Two timers were half of the page's steady-state ticks": the static census of `c0530279` (canopy#670's head,
      whose Interval layout matches #676's parent) gives 3.0 of the 6.6 ticks per second the layout's enabled
      Intervals nominally fire, which is 45%. These are nominal rates, not measured ticks;
    - "Comments that claimed cascor emits weights … are corrected": `ws_dash_bridge.js:113-115` still said "(see
      g-3 emitter)".
  - **Still unfixed:** on canopy `main`, round 3's wording survivors in the PR's files and the class test's
    fragility; on GitHub, #676's stale PR description. The first two are owed as a canopy follow-up PR, the third
    as an edit of #676's description (Still owed, item 13).""",
    ),
    # --- F-CANOPY-055 ------------------------------------------------------------------------------------------
    (
        "A2 #1; B1 #10",
        """  - The lane is `(lane, None)` in `_GATED_POLL_INTERVALS`. The CAN-000 clamp reaches it and the tab gate never
    writes it, so F-CANOPY-053's hazard (a guard's fixed `runningOff` re-enabling a tab-gated lane) cannot
    arise.""",
        """  - The lane is `(lane, None)` in `_GATED_POLL_INTERVALS`. The commit claimed that the CAN-000 clamp reaches it
    and the tab gate never writes it, so F-CANOPY-053's hazard (a guard's fixed `runningOff` re-enabling a
    tab-gated lane) cannot arise. **Lane A refuted that below:** the fused gate writes the lane on every fire.""",
    ),
    (
        "A2 durability",
        """    metrics-store watchdog's node test passes on both sides; that is the evidence the per-lane refactor kept
    its behaviour.""",
        """    metrics-store watchdog's node test passes on both sides; that is the evidence the per-lane refactor kept
    its behaviour. Lane A's per-test junit files are archived in
    `reports/e2e-canopy-2026-09-02/phase9-scratch/f055_r1_laneA/`.""",
    ),
    (
        "A2 R4.o",
        """  - **Suite.** 6823 passed, 4 skipped, 0 failed: the parent's 6806 plus exactly the 17 new tests.""",
        """  - **Suite.** 6823 passed, 4 skipped, 0 failed: the parent's 6806 plus exactly the 17 new tests. No lane ran
    it. The log (no SHA) is archived as `phase9-scratch/orchestrator/f055_full_suite.log`, and the +17
    re-derives from an AST count (+7, +10, +0).""",
    ),
    (
        "A2 instrument #1, #5",
        """- **Census, rule unchanged** (`2026-09-23_status_bar_apply_census.py`; predictions added to its docstring
  before each run; idle trio, Training Metrics, GPU, one browser at a time):""",
        """- **Census, rule unchanged** (`2026-09-23_status_bar_apply_census.py`; idle trio, Training Metrics, GPU, one
  browser at a time). Its predictions were added to its docstring before each run; only the session transcript
  shows that, because the script entered git after the runs. `delivered` counts HTTP responses, while
  `watched` and `executed` count the renderer's callback objects, which run one or two ahead at a window's
  edges:""",
    ),
    (
        "A2 R2.g, R2.h, #6; B1 #13",
        """  - **The first fix run's prediction was wrong.** It predicted at least 10 responses in 60 s ("round trip plus
    up to 1 s"). The lane clocked itself at ~8 s instead, because `running=` releases the lane from
    `completeJob()`, after the saturated page has processed the response, not when the wire answers. That
    matches F-CANOPY-035's measured 5.5–7.3 s.""",
        """  - **The first fix run's prediction was wrong.** It predicted at least 10 responses in 60 s ("round trip plus
    up to 1 s"). The lane clocked itself at about 7.5 s per applied response instead: 7.4–8.7 s by every
    estimator. The census docstring's ~8.6 s is the mean gap between latency changes, and that skips repeated
    values. `running=` releases the lane from `completeJob()`, which runs when the page's main thread takes the
    fetch's response, before the result is applied; a saturated page takes it late. That is slower than
    F-CANOPY-035's measured 5.5–7.3 s, though the same order.""",
    ),
    (
        "A2 R2.g",
        """  - **The cost, stated:** the bar updates about every 8 s on a page this busy. Before the fix it updated never.""",
        """  - **The cost, stated:** the bar updates about every 7.5–8 s on a page this busy. Before the fix, on this
    page, it never updated.""",
    ),
    (
        "A2 #3, R5.d; B1 #10",
        """  - **The drive does not discriminate, as its docstring said it might before it ran.** A demo page is light
    enough that the old 1 Hz feeder gets responses through.
  - **What it shows:** the allow arm and the deny arm both work on the fix.
  - **What it adds to F-CANOPY-055:** the bar froze where the page's delivery latency exceeds the tick, as on
    the trio legs, not on every page. Phase 8's "F-CANOPY-025 inferred regressed" held only for such pages.""",
        """  - **The drive does not discriminate, as its docstring said it might before it ran:** the old 1 Hz feeder
    also got responses through on the demo parent page. Why is unmeasured, since the drive records no latency.
  - **What it shows:** the allow arm and the deny arm both work on the fix.
  - **What it suggests for F-CANOPY-055, unmeasured:** the bar freezes where the page's delivery latency exceeds
    the tick, as on the trio legs, and not on every page. The drive cannot show that, since it records no
    latency. The parent's bar did sit at its defaults for its first 18.5 s.""",
    ),
    (
        "A2 R4.b",
        """  - **Lane A** (measurement re-creation, entry point: git extracts, the transcripts, `/proc`): M1–M5 all
    MATCH.""",
        """  - **Lane A** (measurement re-creation, entry point: git extracts, the transcripts, `/proc`): no MISMATCH in
    M1–M5, with qualifiers. Two mutations were caught only incidentally or only with node present (below), the
    drive (M4b) does not discriminate, the parent leg was `78c057e2` (code-identical to `ce78e0de` in `src/`),
    and M5a found one false-positive path.""",
    ),
    (
        "A2 R4.f, #2",
        """      Apply that begins mid-request leaves the lane polling for the rest of that Apply. A tab change
      mid-request re-opens the eviction window for one cycle. Both limits are shared with #613's
      metrics-store lane and unmeasured.""",
        """      Apply that begins mid-request leaves the lane polling for the rest of that Apply. Shared with #613's
      metrics-store lane, and unmeasured.
    - The same commit also said "a tab change mid-request re-opens the eviction window for one cycle". That was
      the orchestrator's addition, not Lane A's, and Lane B refuted it: one tab click gave 0 of 28 over ~120 s,
      the cascade of F-CANOPY-058.""",
    ),
    (
        "A2 #2; B1 #13",
        """      requests can add up to 30 s and release one request early. Not observed: 20 of 20 applied in 150 s.""",
        """      requests can add up to 30 s and fire. Lane A read that as one request released early; Lane B showed that
      a fire starts the cascade (F-CANOPY-058). Not observed in the census: 20 of 20 applied in 150 s.""",
    ),
    (
        "B1 #13 (units)",
        """        - at a 7–8 s cycle: 4 of 4 applied, then one tab click 3 s into a request, then **0 of 28 over ~120 s**.
      - **Model:** at a 6.9–7.6 s cycle, the median time to the next applied response after a trigger is 352 s.""",
        """        - at a per-request time of 7–8 s: 4 of 4 applied, then one tab click 3 s into a request, then **0 of 28
          over ~120 s**.
      - **Model:** at a per-request time of 6.9–7.6 s, the median time to the next applied response after a
        trigger is 352 s.""",
    ),
    (
        "B1 #13 (units)",
        """      - Model: 37–44 false fires an hour at a 7 s cycle. The metrics-store watchdog has the same predicate.""",
        """      - Model: 37–44 false fires an hour at a 7 s per-request time. The metrics-store watchdog has the same
        predicate.""",
    ),
    (
        "B1 (round-1 report :324); the CI node check on e9053227",
        """      - the mount call cannot evict by itself;""",
        """      - the feeder's own mount call cannot evict by itself (the gate's mount write can, per the repro above);""",
    ),
    (
        "A2 #7 (settled from canopy CI's unit job on e9053227)",
        """      - CI runs the node test.""",
        """      - CI runs the node test. Settled 2026-09-24: none of the six skips in CI's Python 3.13 unit job on
        `e9053227` is the node test. GitHub's ubuntu image ships node, although `ci.yml` has no setup-node step.""",
    ),
    (
        "A2 R2.e, R5.b; B1 #13",
        """    - **Why the census still passed:** its window had no tab switch (Training Metrics is the default tab, so
      `open_tab` wrote nothing), no Apply, and, by chance, no watchdog false fire. 28 of 29 responses applied
      across the two fix runs' 210 s.""",
        """    - **Why the census still passed** (the orchestrator's reading, not Lane B's): its windows had no tab switch
      (Training Metrics is the default tab, so `open_tab` wrote nothing) and no Apply. Two trigger sources were
      live: the watchdog was armed throughout, and the gate's mount write fired on each page before its window.
      Neither produced a cascade on canopy. That is weak evidence against Lane B's modelled false-fire rate (at
      that rate, no fire in 210 s has a probability of about 0.15–0.18) and against a mount-time strand. The
      census does not record fires, so "no fire" is inferred from the applies. 28 of 29 watched callbacks
      executed across the two fix runs' 210 s, and 27 responses were delivered on the wire.""",
    ),
    # --- F-CANOPY-056 ----------------------------------------------------------------------------------------
    (
        "B1 #4, #13; Lane C (the model-select path)",
        """**F-CANOPY-056 — a Stop against cascor keeps the replay session, so the CAN-015 player stays in its session view and the weight drain keeps running until the page reloads (P2, canopy repo; found 2026-09-23 by the cuts' round-1 adversarial lane; OPEN).**""",
        """**F-CANOPY-056 — against cascor, the CAN-015 replay player drops every control's result: `_merge_session` overlays cascor's `{status, data, meta}` envelope, so play, pause, seek, speed and range never reach the session and a Stop never clears it; the player stays in its session view and the weight drain keeps running until the page reloads or a successful model select rebuilds the tab bar (P1, canopy repo; found 2026-09-23 by the cuts' round-1 adversarial lane, widened 2026-09-24 by the ledger's validation; OPEN).**""",
    ),
    (
        "B1 #4, #13; Lane C",
        """- **The result.** Lane B drove the registered `dispatch_control` with that envelope. The session kept its id,
  and `render_session` kept the active view with a `REPLAYING` badge.
- **Test coverage.** The only stop test passes an empty response, a shape the live route never produces.
- **Status.** This predates canopy#676. #676's gate inherits it: once a page has started a replay, the drain
  runs until the page reloads, as it always did.
- **Fix direction, not implemented:** clear the session on a successful stop (handle `stop` before `if
  data:`), plus a test with the real envelope. It was not done in #676, because it could not be verified live
  without starting a replay on the shared trio's cascor.""",
        """- **The result.** Lane B drove the registered `dispatch_control` with that envelope. The session kept its id,
  and `render_session` kept the active view with a `REPLAYING` badge.
- **Widened 2026-09-24** (Lane B1 of the ledger's validation; the overlay re-derived in source by the
  orchestrator). `_merge_session` does `new.update(data)` for ANY non-empty response. The proxied envelope's
  top level is `{status, data, meta}`, and none of the session's display keys sits there. So the results of
  play, pause, seek, speed and range never reach the session either, and `render_session` writes the stale
  values back into the sliders. B1's probe of `e9053227`'s `_merge_session` with cascor-shaped envelopes:
  speed(−5) left `speed` at 1.0; seek(40) left `time_index.current` at 0; play left `playing` at None; stop
  kept `snapshot_id` and REPLAYING. This is F-CANOPY-013's envelope-nesting class on a third site, which
  canopy#532's sweep missed. It rests on source and a probe; it has not been driven live.
- **Re-rated P1**, on plan §6.3's rule ("breaks a documented behaviour"). `docs/USER_MANUAL.md` documents the
  controls' readouts, and against cascor none of them reflects a control. The finding was P2 while it was
  scoped to Stop.
- **How a session does end** (Lane C of the canopy follow-up, re-derived in source): a successful model select
  writes `model-class-store` unconditionally, `suppress_cascade_tabs` rebuilds the whole tab bar, and the Replay
  tab re-mounts with an empty session and a disabled drain. A reload does the same.
- **Test coverage.** The only test of `_merge_session`'s stop branch passes an empty response, a shape the live
  route never produces. The tests that pass a non-empty response (`test_success_merges_session`,
  `test_backend_response_overrides`) use flat dicts the route never returns.
- **Status.** This predates canopy#676. #676's gate inherits it: once a page has started a replay, the drain
  runs until the page reloads or a model select rebuilds the tab bar.
- **Fix direction, not implemented:** unwrap the envelope's `data`, map `result`, and handle `stop` explicitly;
  test all six actions with the real envelope. Handling `stop` first alone fixes one action of six, and
  unwrapping `data` alone would put the echoed `snapshot_id` back on a Stop. It was not done in #676, because it
  could not be verified live without starting a replay on the shared trio's cascor.""",
    ),
    # --- F-CANOPY-057 ----------------------------------------------------------------------------------------
    (
        "B1 #5 (re-derived with gh pr view 187/189/190 and compare), #9",
        """- **History.** Lane B found that the g-3 commits the design record cites are not in the local cascor object
  store. So either the emitter was never merged, or it lives on an unfetched branch.""",
        """- **History** (Lane B1 of the ledger's validation, re-derived with `gh`). The g-3 emitter was merged twice,
  both times into a stacked feature branch that never reached `main`:
  - cascor#187, into `feature/can-015g-2-replay-weight-cache`, at 2026-05-03T07:31:04Z (`d85c9ddd`);
  - its retarget cascor#190, into `feature/can-015g-2-replay-weight-cache-v2`, at 20:05:12Z (`dbc25277`). That was
    13 minutes after the branch's own PR, cascor#189, had landed on `main`.
  - `dbc25277` has diverged from `main`: 3 ahead, 512 behind. Round-1 Lane B's "not in the local cascor object
    store" was an artifact of a local fetch.
  - The orphaned diff adds `metrics["weights"]` in `_emit_frame`, exactly the key `_to_dashboard_metric` strips,
    so both halves of this finding stand.
- **Fix direction:** re-land #190's diff on cascor and add `weights` to canopy's relay key set. Also sweep cascor
  for other stacked PRs merged into a base that had already landed.
- **Severity.** P2, because the canopy follow-up corrects the docs that promised the stream
  (`docs/USER_MANUAL.md` and `notes/development/REPLAY_V2_FAQ.md`). Until that merges, the manual documents a
  behaviour that does not exist, which on plan §6.3's rule argues P1.""",
    ),
    # --- F-CANOPY-058 ----------------------------------------------------------------------------------------
    (
        "B1 #1, #13",
        """**F-CANOPY-058 — a `running=` guard is released by every completion, an evicted request's included, so any mid-request re-enable of the guarded lane starts an eviction cascade, and the lane's responses can stop applying for minutes (P1, canopy repo; found 2026-09-23 by F-CANOPY-055's round-1 adversarial lane; OPEN).**""",
        """**F-CANOPY-058 — a `running=` guard is released by an evicted request's completion too, so any mid-request re-request or re-enable of the guarded lane starts an eviction cascade, and the lane's responses can stop applying for minutes (P1, canopy repo; found 2026-09-23 by F-CANOPY-055's round-1 adversarial lane; OPEN).**""",
    ),
    (
        "B1 #1, #6b, #8, #13, #14",
        """- **The class.** canopy#613's guard on `metrics-store-interval` (F-CANOPY-035) holds a lane's `disabled`
  true while its request is in flight. dash-renderer 4.2.0 releases the guard from `completeJob()`
  (`dash_renderer.dev.js:925-937`) on every HTTP outcome (`:966-986`), with no check that the request is
  still the current one.
- **The trigger.** Anything that re-enables the lane mid-request makes the restarted timer tick one period
  later, which evicts the in-flight request. Its late completion then re-enables the lane under the successor,
  and the two chains keep evicting each other. Mid-request re-enables come from:
  - the fused CAN-000/tab gate, which writes every registered lane on every tab switch, Apply change and
    mount;
  - the Apply release;
  - the strand watchdog's false fires. It samples a ~1 s enabled window every 5 s, so on a slow page it
    reads a healthy lane as stranded.
- **Evidence so far.** Source-derived (lines above, re-derived by the orchestrator), plus Lane B's
  synthetic-app repro with the real renderer (see F-CANOPY-055's review above).
- **In production:** #613's metrics-store poll carries the same guard, gate and watchdog. After a tab switch
  or an Apply mid-request, the metrics store's REST backstop can stop applying for minutes on a slow page.
- **NOT yet observed on canopy itself.** Live confirmation is owed: a census of the metrics store on a leg
  serving `main`, with a tab switch timed mid-request, an Apply spanning a request, and ≥ 10 idle minutes.
- **Fix direction** (Lane B): pace a poll with a request/ack handshake instead of the Interval's `disabled`.
  A progress-based watchdog predicate (reset on `n_intervals` change) addresses the false fires alone. The
  gate returning `no_update` for global lanes on a tab-only change addresses the tab trigger alone.""",
        """- **The class.** canopy#613's guard on `metrics-store-interval` (F-CANOPY-035) holds a lane's `disabled`
  true while its request is in flight. dash-renderer releases the guard from `completeJob()` on every HTTP
  outcome that reaches it (OK, PREVENT_UPDATE and non-OK), with no check that the request is still the
  current one. In 4.2.0, the JuniperCanopy1 env, that is `dash_renderer.dev.js:925-937` and `:966-986`.
  canopy's `requirements.lock` ships 4.4.1, where the same code is at `:979-991`. A 200 whose body fails to
  parse never reaches `completeJob()`.
- **The trigger.** Anything that re-requests or re-enables the lane mid-request. A re-enable restarts the
  Interval's timer, so it ticks one period later and evicts the in-flight request; a re-request evicts it
  directly. The evicted request's late completion then re-enables the lane under its successor, and the two
  chains keep evicting each other. The sources:
  - the fused CAN-000/tab gate. It writes this global lane `Boolean(apply-in-flight)` on every tab switch, at
    the end of an Apply, and at mount. An Apply's start writes `true`, which is not a re-enable. The mount
    write is qualified: Lane B could not check canopy's own mount order, and the gate's mount write was present
    during #613's live verification and this phase's 150 s census (20 of 20 applied);
  - the strand watchdog's false fires. It samples every 5 s and resets only on a sample that sees the lane
    enabled, about 1 s per cycle, so on a slow page it reads a healthy lane as stranded;
  - **on #613's lane, a change of the feeder's second Input**, `metrics-panel-display-mode-store.data` (Lane B1
    of the ledger's validation). `getUniqueIdentifier` ignores which Input fired, so a mid-flight change
    creates a same-identity request and evicts the in-flight one; canopy's own comment says so
    (`update_metrics_store`, qualification 3). B1's synthetic app with this wiring (3 s server latency): one
    mid-request change of the second Input gave 0 applied of 45 responses over 90 s, twice, against 23 of 23 in
    the no-trigger control, twice.
- **The clamp defeat** (Phase 8 item 6; Lane A above): `runningOff` is unconditional, so a completion under the
  CAN-000 clamp re-enables the lane, which then polls through the rest of an Apply.
- **Evidence so far.** Source-derived (lines above, re-derived by the orchestrator), plus Lane B's
  synthetic-app repro with the real renderer (see F-CANOPY-055's review above) and Lane B1's second-Input
  repro. Lane B's scripts and three of its raw outputs are archived (`util/ad-hoc/2026-09-23_f055_r1_laneB_*`,
  `reports/e2e-canopy-2026-09-02/phase9-scratch/f055_r1_laneB/`). Six of its figures (7 of 7, 0 of 51, 4 of 4
  then 0 of 28, 352 s, 0 of 21, 37–44 an hour) have no surviving raw output; its scripts can re-create them.
- **Provenance.** The mechanism was already in this ledger as "source-derived and unobserved" (Phase 7 item 7,
  Phase 8 item 6). Lane B made it a finding, with a repro.
- **In production:** #613's metrics-store poll carries the same guard, gate and watchdog, plus the second
  Input. After a tab switch, the end of an Apply, a display-mode change or a watchdog false fire mid-request,
  the lane can stop applying for minutes on a slow page. What a user would see is narrower. The feeder answers
  `no_update` while the WS is live in window mode, on non-modulus ticks in the full modes, and whenever the
  fetch equals the store. So a stall is visible only while the history is changing and the WS is stale or the
  view is a full mode. The P1 rests as much on blocking F-CANOPY-055's P1 repair, whose feeder always returns
  data, as on the production lane.
- **NOT yet observed on canopy itself.** Live confirmation is owed (Still owed, item 0). It must count
  evictions, not applies: on the idle trio every response after the first is a 204, so an applies count
  cannot tell a healthy lane from a stalled one.
- **Fix direction** (Lane B): pace a poll with a request/ack handshake instead of the Interval's `disabled`.
  A progress-based watchdog predicate (reset on `n_intervals` change) addresses the false fires alone. The
  gate returning `no_update` for global lanes on a tab-only change addresses the tab trigger alone. Neither
  addresses the second Input, and the design must.""",
    ),
    # --- Instruments -----------------------------------------------------------------------------------------
    (
        "the archive, activity and census tools added 2026-09-24",
        """- Consensus reports, archived verbatim: `reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round{1,2,3}.md`.""",
        """- Consensus reports, archived verbatim: `reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round{1,2,3}.md`,
  and the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2}.md`.
- Added 2026-09-24, while validating this phase:
  - `2026-09-24_archive_phase9_tmpfs_evidence.py` copied the files this phase rests on out of the authoring
    session's tmpfs scratchpad, which a reboot deletes. Raw outputs are in
    `reports/e2e-canopy-2026-09-02/phase9-scratch/` (indexed by its README). Round-1 Lane B's F-055 scripts
    are `2026-09-23_f055_r1_laneB_*` and the cuts' single-writer probe is `2026-09-23_cuts_r1_laneB_probe_deps.py`,
    each with a provenance header prepended.
  - `2026-09-24_host_session_activity_window.py`: which Claude Code sessions on this host made a tool call in a
    time window, and which hit a rate limit.
  - `2026-09-24_f058_trigger_census.py`: F-CANOPY-058's live confirmation, per-request evictions keyed by
    `executionPromise`, and five triggers. Its rule and predictions are fixed; it has not yet run.
  - `2026-09-24_phase9_ledger_round1_corrections.py`: this pass, as replayable substitutions.""",
    ),
    # --- Consensus record ------------------------------------------------------------------------------------
    (
        "A2 R4.b",
        """  - Lane A: every measurement MATCH. Lane B: DO-NOT-MERGE, whose central mechanism the orchestrator
    re-derived in the renderer source.""",
        """  - Lane A: no MISMATCH, with qualifiers (above). Lane B: DO-NOT-MERGE, whose central mechanism the
    orchestrator re-derived in the renderer source.""",
    ),
    (
        "A2 R2.f, R5.b; B1 #3",
        """  - The census that passed (n = 3 windows, 29 responses on the fix) could not have produced the failure,
    because its window held none of the triggers. That is the instrument-adequacy lesson of this phase.""",
        """  - The census that passed (two fix windows with 27 responses delivered, against one parent window) held no
    tab switch and no Apply, so it could not produce the failure those triggers cause. It could have seen a
    watchdog false fire or a mount-time strand, and saw neither. That is the instrument-adequacy lesson of this
    phase (Still owed, item 14).""",
    ),
    (
        "B1 #11; B2 #5",
        """  - that F-CANOPY-058 occurs on canopy itself (source plus a synthetic repro only);
  - any rate for F-CANOPY-058's false-fire trigger on a real page (modelled, not measured);
  - any browser other than headless GPU Chromium on one Linux host.""",
        """  - that F-CANOPY-058 occurs on canopy itself (source plus synthetic repros only);
  - any rate for F-CANOPY-058's false-fire trigger on a real page (modelled, not measured);
  - F-CANOPY-056's widened scope on a live page (a probe with constructed envelopes; never driven);
  - that F-CANOPY-055's bar freezes only on pages slower than the tick (the drive recorded no latency);
  - the live check's SESSION PASS beyond one run at its floor, whose disable leg is a synthetic clear that no
    production writer performs;
  - "no watchdog false fire" in the census, which it does not record;
  - who readied and armed canopy#676, beyond "no Claude Code session on this host";
  - any browser other than headless GPU Chromium on one Linux host.""",
    ),
    # --- Matrix effect and counts ------------------------------------------------------------------------------
    (
        "B1 #7",
        """- **F-CANOPY-025**: its allow arm lands on F-055's first fix and on a demo parent page. Phase 8's "inferred
  regressed" is narrowed to pages slower than the tick, and stays open with F-CANOPY-055.
- **New**: F-CANOPY-056 (P2), F-CANOPY-057 (P2) and F-CANOPY-058 (P1).
- **Counts**, from `e2e_finding_triage.py` (run it to confirm):
  - **69 findings**: 48 fixed, 1 accepted, 2 withdrawn, **18 open**.
  - **4 of the open are P1**: F-CANOPY-055, F-CANOPY-058, F-CASCOR-001 and F-CASCOR-002.""",
        """- **F-CANOPY-025**: stays counted **FIXED**. Its allow arm lands on F-055's first fix and on a demo parent
  page, so Phase 8's "inferred regressed" is not established. Whether a slow page regresses it is tracked under
  F-CANOPY-055, whose second fix must re-drive it (Still owed, item 0).
- **New**: F-CANOPY-056 (re-rated P1 on 2026-09-24, above), F-CANOPY-057 (P2) and F-CANOPY-058 (P1).
- **Counts**, from `e2e_finding_triage.py` (run it to confirm):
  - **69 findings**: 48 fixed, 1 accepted, 2 withdrawn, **18 open**.
  - **5 of the open are P1**: F-CANOPY-055, F-CANOPY-056, F-CANOPY-058, F-CASCOR-001 and F-CASCOR-002.""",
    ),
    # --- Still owed ---------------------------------------------------------------------------------------------
    (
        "B1 #6a; A1 #5; B2 #7",
        """- Item 0 is new, and takes over Phase 8's item 2.
- Items 13 and 14 are new.
- Phase 8's items 13 and 14 are merged into item 12.

0. **F-CANOPY-055's second fix, and F-CANOPY-058.**
   - They are the same class, so decide one design for both lanes. Lane B's handshake pacer is the
     candidate: request/ack tokens, with no `disabled`-prop guard.
   - First, confirm F-CANOPY-058 live on a leg serving `main`: a metrics-store census with a tab switch
     timed mid-request, an Apply spanning a request, and ≥ 10 idle minutes.
   - The fix needs real-renderer tests of all three triggers.""",
        """- Item 0 is new, and takes over both halves of Phase 8's item 2.
- Items 13, 14 and 15 are new.
- Phase 8's items 13 and 14 are merged into item 12.

0. **F-CANOPY-055's second fix, and F-CANOPY-058.**
   - They are the same class, so decide one design for both lanes. Lane B's handshake pacer is the
     candidate: request/ack tokens, with no `disabled`-prop guard. It must also cover a non-Interval Input,
     since #613's feeder has one.
   - First, confirm F-CANOPY-058 live on a leg serving `main`, counting EVICTIONS, not applies: on the idle
     trio every response after the first is a 204. `util/ad-hoc/2026-09-24_f058_trigger_census.py` is ready for
     it. It drives five triggers (a gate write, a tab switch, an Apply clamp and release, a display-mode change,
     and 10 idle minutes), with its rule and predictions fixed, and has not yet run. It simulates the Apply
     through the clamp Store, because a real Apply PATCHes the trio's cascor.
   - The fix needs real-renderer tests of every trigger: a tab switch mid-request, the end of an Apply spanning a
     request, a second-Input change mid-request, and 10 idle minutes with the watchdog.
   - Then the fix's own live verification, before its consensus rounds, PR and merge: the census and its
     triggers on the fix's leg, and F-CANOPY-025's allow arm re-driven on a leg where the old code fails (Phase 8
     item 2's second half).
   - Correct the canopy text F-CANOPY-058 contradicts: `dashboard_manager.py:467-472` ("the harmless window"),
     `:4698-4701` ("Self-healing, bounded to one cycle"), and `test_poll_gating.py:312-313` ("the apply clamp
     alone").""",
    ),
    (
        "B1 #6b",
        """5. **canopy#613's guard, source-derived and unobserved.** Superseded by F-CANOPY-058 (item 0). An evicted
   request's `completeJob` is now source-confirmed to release the guard.""",
        """5. **canopy#613's guard, source-derived and unobserved.** Superseded by F-CANOPY-058 (item 0). An evicted
   request's `completeJob` is now source-confirmed to release the guard. The item's other half, the clamp
   defeat, is now part of F-CANOPY-058's text.""",
    ),
    (
        "B1 #4",
        """7. **CAN-015's replay-player loop.** Now joined by F-CANOPY-056 and F-CANOPY-057.""",
        """7. **CAN-015's replay-player loop.** Now joined by F-CANOPY-056, now P1, and F-CANOPY-057.""",
    ),
    (
        "A2 #11; B1 #12; Lane C",
        """    - The live-check instrument's gaps (Lane A): a missing node reads as 0 ticks; there is no store read-back
      after `setProps`; `ticks_10s_cleared` keeps no raw counts; and the script records no host load.
    - **Round 3's fixes, which the merge left unapplied.** One canopy follow-up PR:
      - the wording survivors: `replay_player_panel.py:75`; `test_idle_dispatch_cuts.py:138` (the assertion
        message) and `:193` (the test name); `ws_dash_bridge.js:113-115` ("see g-3 emitter") and `:28` (an
        "Each carries…" with no antecedent). Line numbers are at `4b4cfb16`;
      - the CLASS test's fragility: a dict id crashes the sibling test at `:127`, and an Interval with no id
        raises `KeyError` at `:120`;
      - the PR description, refreshed on the merged PR.""",
        """    - The live-check instrument's gaps (Lane A): a missing node reads as 0 ticks; an empty `paths.strs` reads
      as "dead timer absent"; PROBE never checks the node's id; there is no store read-back after `setProps`;
      `ticks_10s_cleared` keeps no raw counts; and the script records no host load.
    - **Round 3's fixes, which the merge left unapplied.** Owed as one canopy follow-up PR:
      - the wording survivors: `replay_player_panel.py:75`; `test_idle_dispatch_cuts.py:138` (the assertion
        message) and `:193` (the test name); `ws_dash_bridge.js:113-115` ("see g-3 emitter") and `:28` (an
        "Each carries…" with no antecedent). Line numbers are at `4b4cfb16`;
      - the CLASS test's fragility: a dict id crashes the sibling test at `:127`, and an Interval with no id
        raises `KeyError` at `:120`;
      - the same false claims outside #676's files: `replay_forward.py`'s module docstring,
        `docs/USER_MANUAL.md`, and `notes/development/REPLAY_V2_FAQ.md`;
      - #676's own "until the page reloads", which missed the model-select path.
    - #676's PR description, refreshed on the merged PR. That is an edit of the PR, not part of the follow-up.""",
    ),
    (
        "B1 #3",
        """14. **New: a verdict floor calibrated for one cadence VOIDs a fix that changes the cadence.** The census's
    "≥ 10 responses" assumed a 1 Hz lane. Any future census of a self-clocked lane needs a window sized to its
    cadence, fixed before the run.""",
        """14. **New: a verification census must be able to fail.** Three rules this phase earned:
    - Put every known trigger inside the window, or name the ones it cannot see.
    - Count an observable that differs between pass and fail on that leg. On the idle trio an applies count
      cannot, since every response after the first is a 204; count evictions.
    - Size the window, and any verdict floor, to the lane's cadence, fixed before the run. The census's "≥ 10
      responses" assumed a 1 Hz lane and VOIDed a fix that self-clocks at ~7.5 s.
15. **New: owner questions and loose ends from #676's merge.**
    - Was the 21:47–22:51Z pass over nine PRs his? If not, nothing held a PR that night: not a disarm, a draft
      or a comment. Only a PR that does not yet exist is held.
    - F-CANOPY-056's re-rating to P1, on plan §6.3's rule.
    - Served canopy commits that exist only in the local clone: `ce78e0de`, `78c057e2`, `668380ec`,
      `723ee812`, `884d22fb`, `cf6fb1dc` and `7a4a2e33`. Push them to a provenance ref on canopy's remote, or
      accept that a lost clone loses them.""",
    ),
]


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
    if bad:
        for n, why, head in bad:
            print(f"REFUSED: {n} matches for [{why}]: {head!r}", file=sys.stderr)
        return 1
    if not args.dry_run:
        LEDGER.write_text(text, encoding="utf-8")
    print(f"{'would apply' if args.dry_run else 'applied'} {len(SUBS)} substitutions to {LEDGER.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
