#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-3 validation corrections (Lanes R3-A and R3-B, plus canopy Lane C4's two ledger notes).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-3 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round3.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py (the pass this corrects)

As in rounds 1 and 2: exact substitutions, each matching exactly once (or, for the two REPLACE_ALL entries,
exactly the stated count), or the script refuses and writes nothing. Nothing in this pass is applied to the
ledger by hand. Entry labels: A = R3-A, B = R3-B, C4 = the canopy follow-up's round-4 lane.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

# (label, old, new, expected count)
REPLACE_ALL = [
    ("A6, B1: the jitter is one-sided (7 + uniform(0, 1) s)", "R = 7 ± 1 s", "R = 7–8 s", 2),
    ("A6, B1: the jitter is one-sided (3 + uniform(0, 2) s)", "R = 3 ± 2 s", "R = 3–5 s", 2),
]

SUBS = [
    # --- Summary ---------------------------------------------------------------------------------------------
    (
        "A3, B3: F-059's reach, in the summary",
        """    measured the payload (segment 7: "The obvious one-line fix crashes the panel").""",
        """    measured the payload (segment 7: "The obvious one-line fix crashes the panel"). A Replay started from the
    page also leaves cascor refusing training, while canopy shows Stopped, until someone presses Reset
    Training.""",
    ),
    # --- #676's review: round 2 and round 3 ------------------------------------------------------------------
    (
        "B7: the run-2 transcript entered git before the merge, locally",
        """    citation" below), and the transcript first entered git after the merge, in this phase's `5a0e4ea9`.""",
        """    citation" below). The transcript first entered git locally at 20:41:35Z, before the merge (`800c20bb`, on an
    unpushed branch; this phase's `5a0e4ea9` is its rebased copy), so GitHub never had it.""",
    ),
    (
        "B16, B17: the procedure's filename; what was left on #676",
        """    terminated. B3 marked both MINORs as changing a number and an action, so §4 called for a round 4 on their
    fixes, which were wording in the squash message and the PR body. The merge overtook both (next bullet), so
    no round 4 ran: nothing was left on #676 to review. Its no-action NITs are carried in Still owed item 13.""",
        f"""    terminated. B3 marked both MINORs as changing a number and an action, so §4 of {PROC}
    called for a round 4 on their fixes, which were wording in the squash message and the PR body. The merge
    overtook both (next bullet), so no round 4 ran: nothing was left on #676's code to review (its description
    is edited separately, Still owed item 13). Its no-action NITs are carried in item 13 too.""",
    ),
    # --- The merge, out of order: "Who" -----------------------------------------------------------------------
    (
        "A1, B2: the scan is a pattern, and its counts after widening",
        """      - **Launches, not tool calls.** `util/ad-hoc/2026-09-24_merge_command_launch_scan.py` lists every Bash
        call whose command line could ready, arm, merge, update-branch or re-run a PR (outputs in
        `reports/e2e-canopy-2026-09-02/phase9-scratch/ledger_r2_orchestrator/`). The only draft-readying
        command any session ran on 09-23 was `gh pr ready 2020`, at 06:09Z. None of that day's 38 matching
        background launches names a PR of the pass below or of the later actions: 34 name one PR each, and the
        other four name none within the 220 characters the scan keeps. None that could ready a draft was
        launched from 09-20 on, and the last matching call of any kind was at 21:27:05Z. The one repo script
        that readies drafts, `util/ad-hoc/2026-09-05_fleet_merge_train.py`, was not run that day.""",
        """      - **Launches, not tool calls.** `util/ad-hoc/2026-09-24_merge_command_launch_scan.py` lists the tool
        calls whose command line matches a pattern of commands that can ready, arm, merge, update-branch or
        re-run a PR (outputs in `reports/e2e-canopy-2026-09-02/phase9-scratch/ledger_r2_orchestrator/`). It is a
        pattern, not a proof: a script run by a path the pattern does not name is outside it. The only
        draft-readying command any session ran on 09-23 was `gh pr ready 2020`, at 06:09Z. None of that day's 44
        matching background launches names a PR of the pass below or of the later actions: 40 name one PR each,
        and the other four (a release-train detect, the release ceremony and two experiment runs) name none.
        None that could ready a draft was launched from 09-20 on, and the last matching call of any kind was at
        21:27:05Z. The one repo script that readies drafts, `util/ad-hoc/2026-09-05_fleet_merge_train.py`, was
        not run that day.
      - **What the first pattern missed** (Lanes R3-A and R3-B). Round 2's pattern counted 38 background
        launches, 34 naming a PR. It missed `util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py`, an
        update-branch loop that session `23e65d0b` launched in the background six times on 09-23 (13:50Z to
        15:19Z, for ml#2040 and ml#2049 to ml#2053; R3-B reads their 5,400–7,200 s timeouts as ending them by
        about 17:20Z), and the forms `gh pr -R <repo> <verb>`, a `$PR` merge path, GraphQL
        `updatePullRequestBranch`, check-suite re-requests and GraphQL read from a file. The widened pattern
        catches them, and the conclusion held: none of the six names a PR of the pass.""",
    ),
    (
        "A10: the pass's other update-branches",
        """      - #676 is the only one with an update-branch between its ready and its arm.""",
        """      - #676 is the only one with an update-branch between its ready and its arm. The pass also updated the
        branches of ml#2032 (22:27:32Z), data#428 (22:30:06Z), ml#2059 (22:50:08Z), ml#2066 (22:50:21Z,
        `41379ff9`) and data#431 (22:51:03Z) (Lane R3-A).""",
    ),
    (
        "A2, B8: the account's locally signed commits, and the morning's arms",
        """      background shepherd can update a branch, but none of the day's launches names ml#2066 or data#434.""",
        """      background shepherd can update a branch, but none of the day's launches names ml#2066 or data#434.
    - **Commits signed locally with the owner's key landed in that window** (Lanes R2-B and R3-A; re-derived
      from the commits API). `4c496443` on ml#2058 (committed 21:45:22Z, two minutes before the pass's first
      ready) and `c666403b` on ml#2045 (23:47:30Z, a minute before that PR's disarm and re-arm) are committed
      by "Paul Calnon", not by GitHub's web-flow, with valid PGP signatures. On this host a locally signed
      commit needs a touch of the owner's hardware key (`util/push_signed_commit.py`'s docstring), and no Claude
      Code session made a tool call then. R3-A also reads a rebase force-push to ml#2045 at 00:00:39Z from the
      push events. ml#2045 was drafted and readied again at 03:04:45Z and 03:05:02Z (its timeline).
    - **The same arming pattern that morning** (Lane R3-B; re-derived from the timelines). `pcalnon` armed
      ml#2032, ml#2045 and data#428 at 13:23:19Z, 13:26:23Z and 13:29:27Z, and no logged command names any of
      them between 13:15Z and 13:35Z. R3-B reads session `bc31e993`'s handoff that evening, titled
      "…four-prs-armed-by-an-unseen-actor…", as why it drafted two of them at 20:24Z.""",
    ),
    (
        "B6: the follow-up's review had not terminated; no SHA to go stale",
        """    fragility; on GitHub, #676's stale PR description. The first two are fixed on canopy branch
    `fix/idle-cuts-round3-wording` (local `9935b857`, not yet pushed), which opens as a PR after this phase
    lands; the third is an edit of #676's description (Still owed, item 13).""",
        """    fragility; on GitHub, #676's stale PR description. The first two are fixed on canopy branch
    `fix/idle-cuts-round3-wording` (local, not yet pushed), which opens as a PR after this phase lands and its
    own review terminates; the third is an edit of #676's description (Still owed, item 13).""",
    ),
    # --- F-CANOPY-055's first fix ------------------------------------------------------------------------------
    (
        "B7: the census docstring's first commit",
        """  `51993b37` (17:07:01Z), but those docstring edits entered git only after the runs (`5a0e4ea9`), so only the""",
        """  `51993b37` (17:07:01Z), but those docstring edits entered git only after the runs (locally at 20:41:35Z,
  `800c20bb`; rebased here as `5a0e4ea9`), so only the""",
    ),
    (
        "A7: the model is a Poisson approximation",
        """    - **What that says about Lane B's model** (corrected in round 2 of the ledger's validation). At the 37–44
      fires an hour stated above, no fire in 210 s has a probability of 0.08–0.12.""",
        """    - **What that says about Lane B's model** (corrected in round 2 of the ledger's validation). Under a Poisson
      approximation, at the 37–44 fires an hour stated above, no fire in 210 s has a probability of 0.08–0.12.
      Lane B's own alias simulation gives fires more regular than Poisson, which lowers every figure here (Lane
      R3-A), so the conclusion below only strengthens.""",
    ),
    # --- F-CANOPY-057 --------------------------------------------------------------------------------------------
    (
        "A4, B5, C4: cascor#184's diff reached main through #189",
        """  - The same pattern a third time (Lane R2-B; re-derived with `gh`): cascor#184 merged into
    `feature/can-015g-1-snapshot-weight-history` at 06:03:30Z, 3 h 57 min after that branch's own PR, cascor#180,
    had landed on `main` (02:06:37Z).""",
        """  - The same merge pattern a third time (Lane R2-B; re-derived with `gh`): cascor#184 merged into
    `feature/can-015g-1-snapshot-weight-history` at 06:03:30Z, 3 h 57 min after that branch's own PR, cascor#180,
    had landed on `main` (02:06:37Z). Unlike #187's, its diff did reach `main`: cascor#189 is its retarget
    ("[retarget #184]", the same +524/−3 over two files), merged as `b1d19948` (Lanes C4, R3-A and R3-B;
    re-derived from #189's title).""",
    ),
    (
        "A4, B5: #184 leaves the sweep",
        """  for other stacked PRs merged into a base that had already landed. cascor#184 is one; whether its diff reached
  `main` by another route is unchecked.""",
        """  for other stacked PRs merged into a base that had already landed. cascor#184 was one, and its retarget,
  cascor#189, landed it.""",
    ),
    # --- F-CANOPY-059 --------------------------------------------------------------------------------------------
    (
        "A3, B3: the header names the REPLAYING lock-in",
        """and the Replay tab stays at "▶ No active replay session" with no control reachable (P0,""",
        """and the Replay tab stays at "▶ No active replay session" with no control reachable, while cascor stays in REPLAYING and refuses training until someone presses Reset Training (P0,""",
    ),
    (
        "A9, B14: UTC merge dates",
        """  as it has since cascor#178 (`e01f57f`, 2026-05-02).""",
        """  as it has since cascor#178 (`e01f57f`, merged 2026-05-03T00:55:26Z).""",
    ),
    (
        "A5, B12: the layout lines at e9053227",
        """  (`replay_player_panel.py:114`), the controls hidden (`:115`).""",
        """  (`replay_player_panel.py:112`), the controls hidden (`:113`).""",
    ),
    (
        "C4, A3, B3: nothing replays; cascor stays in REPLAYING; the Reset escape",
        """- **What a user sees.** A successful Replay switches to the Replay tab, which says "▶ No active replay session"
  while cascor replays. Play, pause, seek, speed, range and Stop are never on screen. Every later write of the
  session Store re-raises.""",
        """- **What a user sees.** A successful Replay switches to the Replay tab, which says "▶ No active replay session".
  Play, pause, seek, speed, range and Stop are never on screen, and every later write of the session Store
  re-raises. Nothing replays either: cascor's session starts paused (`manager.py:1076`) and emits only its
  first frame until a Play arrives (`_run`'s initial `_emit_frame(0)`), and no Play is on screen (Lane C4).
- **cascor stays in REPLAYING** (Lanes R3-A and R3-B; re-derived in source). It refuses a new network
  (`manager.py:1731-1732`), starting or stopping training (`:2452-2453`, `:2842-2843`), and restore, retrain
  and resume (`routes/snapshots.py:278`, `:329`, `:378`). It reports its training state as Stopped / Idle
  meanwhile (`manager.py:6001-6003`), so canopy shows Stopped while Start fails. The player's Stop is canopy's
  only caller of cascor's `/replay/control` (`replay_player_panel.py:371`), and it is never on screen. The one
  way out on the page is the sidebar's Reset Training: its button is disabled only while its own command is in
  flight (`dashboard_manager.py:8548-8549`), the adapter's `reset_training` (`cascor_service_adapter.py:1137-1139`)
  calls cascor's `/v1/training/reset` (`routes/training.py:169-173`), and cascor documents `reset()` as
  REPLAYING's escape hatch. Nothing on the page points a user to it.""",
    ),
    (
        "A8, B13, A9, A11: Phase 4 kept F-015 open; UTC date; the fixture's other fields",
        """  crashes the panel." canopy#532 (`359e1bf7`, 2026-08-27) made that fix, and its test passes because its fixture,
  labelled "The exact shape measured off the running service", types the range as `[3, 37]`
  (`src/tests/unit/frontend/test_p2_wave_batch_a.py:179-190`). Phase 4 closed F-CANOPY-015 by test, pending a
  live re-drive that never ran.""",
        """  crashes the panel." canopy#532 (`359e1bf7`, merged 2026-08-28T04:16:14Z) made that fix, and its test passes
  because its fixture, labelled "The exact shape measured off the running service", types the range as
  `[3, 37]` (`src/tests/unit/frontend/test_p2_wave_batch_a.py:179-190`); it also differs from the measured
  payload in five other fields (Lane R3-A). Phase 4 listed F-CANOPY-015 as fixed by #532 but kept it OPEN
  pending a live re-drive (its status correction), which never ran.""",
    ),
    (
        "B4: the P0 against F-CANOPY-014's P1",
        """  it blocks a workflow the mandate names, "snapshots saving/loading/replaying" (§1.1(d)). It also masks
  F-CANOPY-056, whose controls it keeps off screen.""",
        """  it blocks a workflow the mandate names, "snapshots saving/loading/replaying" (§1.1(d)). It also masks
  F-CANOPY-056, whose controls it keeps off screen, and it leaves cascor refusing training. F-CANOPY-014, which
  disabled the same controls through a different fault (an empty base URL), was rated P1 and is fixed. This one
  is worse, since no session view appears at all, and §6.3's words give P0; which rating replay findings take
  is an owner question (Still owed, item 15).""",
    ),
    # --- Instruments -----------------------------------------------------------------------------------------------
    (
        "B20: R2-B's census figures are report-only",
        """      scores it EVICTED: 13 of 13 `no_update` answers, against 13 of 13 data answers APPLIED.
    - Its fire detector reads the lane after the fire's own `false` write, so it counted 0 of 2 real fires.""",
        """      scores it EVICTED: 13 of 13 `no_update` answers, against 13 of 13 data answers APPLIED.
    - Its fire detector reads the lane after the fire's own `false` write, so it counted 0 of 2 real fires.
    - Those figures are R2-B's report. Its synthetic apps, drivers and server logs are archived, not the
      census's scored output. One archived app still labels its no-props mode "HTTP 204" in a comment, while
      its own log shows 200s.""",
    ),
    (
        "B9, A1: what the new tools see and refuse",
        """  - `2026-09-24_merge_command_launch_scan.py`: every Claude Code Bash call on this host that could ready, arm,
    merge, update-branch or re-run a PR, in a window, with its background flag.
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py`: the rest of this phase's tmpfs evidence, round 2's
    included, from two sessions' scratchpads. It refuses any file holding an e-mail address other than a
    `noreply` one.""",
        """  - `2026-09-24_merge_command_launch_scan.py`: the Claude Code tool calls on this host, in a window, whose
    command line matches a pattern of commands that can ready, arm, merge, update-branch or re-run a PR, with
    each call's background flag. Widened after round 3 found forms it missed ("Who", above).
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py`: the rest of this phase's tmpfs evidence, round 2's
    included, from two sessions' scratchpads. It refuses secret shapes (widened after round 3 to every
    `gh*_` token prefix and JWTs) and any file holding an e-mail address other than a `noreply` one or the
    Codecov uploader's public key address, which CI logs print.""",
    ),
    # --- Consensus record ---------------------------------------------------------------------------------------------
    (
        "B16: the procedure's filename",
        """    The review had not terminated under §4, since B3's two MINORs each changed a number and an action. The""",
        f"""    The review had not terminated under §4 of {PROC}, since B3's two MINORs each
    changed a number and an action. The""",
    ),
    (
        "B16: the procedure's filename, round 2",
        """    SOUND-WITH-FIXES, and both said §4 required a round 3.""",
        f"""    SOUND-WITH-FIXES, and both said §4 of {PROC} required a round 3.""",
    ),
    (
        "B18: the 204 claim, in the ledger",
        """    - the F-058 census, refuted before its first run, and the 204 claim, corrected wherever it stood (Phase 7's
      line included);""",
        """    - the F-058 census, refuted before its first run, and the 204 claim, corrected wherever it stood in the
      ledger (Phase 7's line included; an archived lane script's comment still says it);""",
    ),
    (
        "B15: no hand edit to the LEDGER",
        """      are in `util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py`, with no hand edit.""",
        """      are in `util/ad-hoc/2026-09-24_phase9_ledger_round2_corrections.py`, with no hand edit to the ledger;
      the scripts' docstrings, the README and the handoff's note were edited directly.""",
    ),
    (
        "the round-3 record",
        """    ones sessions had drafted to hold.
""",
        """    ones sessions had drafted to hold.
  - **Round 3**: two lanes on the frozen `3f83b9c6`, briefed separately. Lane R3-A re-derived round 2's new
    claims from their artifacts; Lane R3-B attacked round 2's corrections. Both returned SOUND-WITH-FIXES. The
    replay of round 2's script is exact, and every number and date R3-A re-derived holds.
  - **What round 3 changed:**
    - F-CANOPY-059's reach: cascor stays in REPLAYING, refusing training, a new network, and restore, retrain
      and resume, while canopy shows Stopped, until a Reset; and its P0 now states F-CANOPY-014's P1
      precedent;
    - the launch scan's pattern and counts (44 background launches on 09-23 and 40 naming one PR, where 38
      and 34 stood), after it missed the converge driver; the conclusion held;
    - the owner question's evidence: commits signed locally with the owner's key inside the quiet window, and
      the same arming pattern that morning;
    - F-CANOPY-057's history: cascor#184 reached `main` through its retarget, #189;
    - the per-request ranges (3–5 s and 7–8 s, not "±"), two merge dates now in UTC, two line numbers, the
      run-2 transcript's first commit (`800c20bb`, before the merge), and the canopy follow-up's review state;
    - what the new tools see and refuse, and their secret shapes;
    - all in `util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py`, with no hand edit to the ledger.
  - **Re-derived before applying (round 3):** cascor's REPLAYING refusals, its Stopped/Idle report and its
    reset escape hatch; canopy's Reset button, its enabling and its path to cascor; the placeholder's layout
    lines; `4c496443`'s and `c666403b`'s committers and signatures; the morning's arms and that no logged
    command names those PRs then; ml#2045's 03:04–03:05Z draft and ready; `800c20bb`'s content; #189's
    retarget title; the two merge dates; the widened scan's counts. Not re-derived: R3-A's reading of the
    00:00:39Z force-push, R3-B's reading of `bc31e993`'s handoff title and of the converge runs' timeouts, and
    the fixture's five other differing fields.
  - **Round 3 changed numbers and actions**, so §4 of the consensus procedure calls for a round 4 on these
    corrections.
""",
    ),
    (
        "A1: who, by pattern",
        """    (foreground calls and background launches, checked by their command lines);""",
        """    (foreground calls and background launches whose command lines match a pattern, which a script run by an
    unnamed path escapes);""",
    ),
    # --- Still owed ------------------------------------------------------------------------------------------------------
    (
        "B11: the verify script takes the src directory",
        """   - A leg serving `main`: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy worktree on main>
     <port>`, with `JUNIPER_E2E_CANOPY_URL` exported for the drivers.""",
        """   - A leg serving `main`: `util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <canopy worktree on
     main>/src <port>` (it wants the directory holding `main.py`), with `JUNIPER_E2E_CANOPY_URL` exported for
     the drivers.""",
    ),
    (
        "B6: item 13, the follow-up's review is still running",
        """      follow-up, branch `fix/idle-cuts-round3-wording` (local commit `9935b857` on `e9053227`, not yet pushed),
      which opens as a PR after this phase lands, the order #676 broke. Its review, Lanes C, C2 and C3, is in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. It
      covers:""",
        """      follow-up, branch `fix/idle-cuts-round3-wording` (local, on `e9053227`, not yet pushed), which opens as a
      PR after this phase lands, the order #676 broke, and only once its own review terminates under §4 of
      the consensus procedure. Its review rounds are archived in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. It
      covers:""",
    ),
    (
        "B19: no lane passed the census's logic",
        """      F-058 census passed review of its logic and failed its first synthetic run (item 0).""",
        """      F-058 census was written with its rule and predictions fixed, and failed its first synthetic run
      (item 0).""",
    ),
    (
        "A2, B8, B4, B17: item 15's evidence, the precedent, the follow-up's commits",
        """      (01:21:37Z) and #676's CI re-run (01:22:32Z), without which its armed merge could not fire. No Claude Code
      process on this host did any of them ("Who", above).""",
        """      (01:21:37Z) and #676's CI re-run (01:22:32Z), without which its armed merge could not fire. No Claude Code
      process on this host did any of them ("Who", above), while commits signed locally with the owner's key
      landed at 21:45:22Z and 23:47:30Z, and the same arming pattern ran that morning at 13:23–13:29Z.""",
    ),
    (
        "B4: the rating question names the precedent",
        """      F-CANOPY-057 P1, F-CANOPY-059 P0.""",
        """      F-CANOPY-057 P1, F-CANOPY-059 P0, against F-CANOPY-014's P1 for the same controls (F-CANOPY-059's
      severity bullet).""",
    ),
    (
        "B17: the follow-up's local commits",
        """      them to a provenance ref on each remote (for example `refs/provenance/canopy-e2e-phase9`), or accept that
      a lost clone loses them.""",
        """      them to a provenance ref on each remote (for example `refs/provenance/canopy-e2e-phase9`), or accept that
      a lost clone loses them. The canopy follow-up's local commits join the list until its PR opens.""",
    ),
    (
        "A3, B3: item 16's drives must end their replay and check Start",
        """      Each of these drives starts a replay, so each needs a cascor that may be written, not the shared trio's.""",
        """      Each of these drives starts a replay, so each needs a cascor that may be written, not the shared trio's.
      Each must end its replay (the sidebar's Reset Training, or a stop through cascor's `/replay/control`), and
      should check that Start works after a Replay.""",
    ),
    (
        "the round-3 reports and briefs are archived",
        """  the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2}.md`; and the canopy""",
        """  the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3}.md`; and the canopy""",
    ),
    # --- Phase 4's row, pointed at F-CANOPY-059 in place ------------------------------------------------------------------
    (
        "B13: Phase 4's F-015 row points at F-059",
        """| F-CANOPY-015 replay session nesting | canopy#532 | fixed — `_session_summary`, legacy shape tolerated |""",
        """| F-CANOPY-015 replay session nesting | canopy#532 | fixed — `_session_summary`, legacy shape tolerated; its `range` read crashes every real session (F-CANOPY-059, Phase 9) |""",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    text = LEDGER.read_text(encoding="utf-8")
    bad = []
    for why, old, new, want in REPLACE_ALL:
        n = text.count(old)
        if n != want:
            bad.append((n, why, old))
            continue
        text = text.replace(old, new)
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
    print(f"{'would apply' if args.dry_run else 'applied'} {len(REPLACE_ALL)} replace-alls and {len(SUBS)} substitutions to {LEDGER.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
