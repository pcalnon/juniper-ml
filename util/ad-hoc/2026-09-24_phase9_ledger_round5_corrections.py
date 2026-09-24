#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-5 validation corrections (Lanes R5-A and R5-B, plus the canopy follow-up's round 8).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-5 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round5.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round4_corrections.py (the pass this corrects);
         util/ad-hoc/2026-09-24_owner_answer_extract.py (prints the owner's answer, redacted)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the launch scan's docstring was edited directly. Labels: A = R5-A,
B = R5-B, C8 = the canopy follow-up's round-8 lane.

The pass's centre is R5-B's finding 1: four minutes after round 5's artifact was frozen, the owner answered
the owner question in another session ("Mine: fix forward"), so the "Who" narrative now records an answer
and its scope instead of an open question. Every re-derivation this pass rests on is listed in the round-5
consensus bullet it adds.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round5_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"
R4 = "`reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round4.md`"

SUBS = [
    # --- "Who": the scan's forms -------------------------------------------------------------------------------
    (
        "B6: round 3's forms did match launches",
        "added forms it had missed, and no launch of those forms was found (Lanes R4-A and R4-B).",
        """added forms it had missed: round 3's matched the converge driver's six background launches (below),
        and round 4's matched no launch (Lanes R4-A and R4-B).""",
    ),
    # --- "Who": the earlier arms ------------------------------------------------------------------------------
    (
        "B2, A3e: at least three occasions, at least 20 PRs",
        f"""    - **Arms like the pass's happened twice earlier that day** (Lanes R3-B, R4-A and R4-B; the arm events of
      ten of the PRs re-derived from their timelines). At least nine PRs across four repos were armed as
      `pcalnon` between 13:17:53Z and 13:32:10Z, and ml#2020, canopy#655 and cascor#673 between 00:52:07Z and
      01:08:14Z, and R4-A's scan of every tool call found no command arming any of them. R4-A's sweep covered
      each repo's 60 most recently updated PRs, so nine is a lower bound; each lane's list is in {R4}.""",
        f"""    - **Arms like the pass's happened at least three times earlier that day** (Lanes R3-B, R4-A, R4-B, R5-A
      and R5-B; round 5's two lanes each read the arm events of every PR updated since 09-22 in the nine
      Juniper repos). Ten PRs across ml, canopy, cascor and deploy were armed as `pcalnon` between 00:47:31Z
      and 01:08:14Z (ml#2020 twice), nine across four repos between 13:17:53Z and 13:32:10Z, and ml#2057 at
      20:23:01Z. The lanes found no command on this host, before any of those arms, that could have made it
      (each lane's windows are in its report). The lists are in {R4} and `…_round5.md`.""",
    ),
    (
        "A1, B5: three later background launches, and a no-op foreground arm",
        """Two background launches the pattern matches name morning PRs, and both came after those PRs'
      arms: `safe_merge --pr 670` at 15:29Z and 15:55Z, and a shepherd for ml#2041 at 13:35Z, which cannot arm.""",
        """Three background launches the pattern matches name morning PRs, and all came after those PRs'
      morning arms: a shepherd for ml#2041 at 13:35Z, which cannot arm, and `safe_merge --pr 670` at 15:29Z
      and 15:55Z, each followed within 6 s by a re-arm of canopy#670, which had been disarmed at 14:27:46Z and
      15:52:22Z. A foreground `gh pr merge 2041 --squash --auto` (session `1f771cb0`, 13:35:20Z) came after
      that PR's 13:25:23Z arm, and GitHub recorded no arm event for it (Lanes R5-A and R5-B).""",
    ),
    (
        "A3c, B: ml#2045's 03:02:06Z push, before its draft and ready",
        """      03:05:02Z, with no tool call on this host between 01:40Z and 03:26:44Z (Lanes R4-A and R4-B). It was not
      re-armed.""",
        """      03:05:02Z, with no tool call on this host between 01:40Z and 03:26:44Z (Lanes R4-A and R4-B). It was not
      re-armed. Two to three minutes before the draft, at 03:02:06Z, the account fast-forwarded its branch by
      three commits by "Paul Calnon", committed 03:00:20Z to 03:01:48Z with valid signatures (Lanes R5-A and
      R5-B read the same key as the night's; re-derived from the activity and compare APIs). ml#2045 was
      closed unmerged at 07:29:52Z.""",
    ),
    (
        "B1: the owner has answered",
        """    - The actor is unidentified. It acts as `pcalnon`, the owner's account, and it is not Claude Code on this
      host. **Owner question**: were that pass and the later actions his? (Still owed, item 15.)""",
        """    - **The owner has answered: the sweeper is the owner's.** It acts as `pcalnon` and is not Claude Code on
      this host. On 2026-09-24 at 07:32:48Z, four minutes after round 5's artifact was frozen, session
      `bc31e993` asked whether the sweeper that took four PRs out of draft and armed them 4–7 s later as
      `pcalnon` was the owner's. It named data#428, ml#2032, ml#2059 and canopy#678, all four in the pass above
      (canopy#678 merged there with no arm event), and cascor#678's morning arm. The owner chose "Mine: fix
      forward", an option whose text says the sweeper is the owner's and its merges intended, with validation
      continuing after the merge and fixes going forward in follow-up PRs. The question did not name #676, the
      account's later actions or ml#2045's next morning, so those remain the owner's to confirm (Still owed,
      item 15). Lane R5-B found the exchange; `util/ad-hoc/2026-09-24_owner_answer_extract.py` prints it,
      redacted, from lines 4227 and 4260 of that session's transcript.""",
    ),
    # --- F-CANOPY-059: the status bar's cause -----------------------------------------------------------------
    (
        "A2, B3: the status bar's own else, and F-055's frozen default",
        """and canopy maps
  the REPLAYING status it does not know to Stopped (`state_sync.py:177`), so the status bar shows Stopped; the
  Network Editor's badge alone reads "FSM: Replaying".""",
        """and the status
  bar shows Stopped: for a REPLAYING status every flag it reads is false, so it falls to its `else`
  (`dashboard_manager.py:7508-7518`), and while F-CANOPY-055 is open it holds its layout default, also Stopped
  (`:887`), whatever cascor reports. `/api/state` maps the unknown status to Stopped too (`state_sync.py:177`).
  The Network Editor's badge alone reads "FSM: Replaying".""",
    ),
    # --- Instruments -----------------------------------------------------------------------------------------
    (
        "Round list: the round-5 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5}.md`",
    ),
    (
        "Tools: rounds 3 to 5's passes, and the answer extractor",
        """  - `2026-09-24_phase9_ledger_round2_corrections.py`: round 2's pass, entirely scripted.
""",
        """  - `2026-09-24_phase9_ledger_round2_corrections.py`: round 2's pass, entirely scripted; rounds 3 to 5's passes
    are `…_round{3,4,5}_corrections.py`, likewise.
  - `2026-09-24_owner_answer_extract.py`: prints chosen records of a session transcript, redacted; round 5
    used it for the owner's answer ("Who", above).
""",
    ),
    (
        "B4: the ledger's upload is not within 250 KB",
        """  - `2026-09-24_push_phase9_signed_groups.py`: lands this branch as signed commits in groups of at most
    250 KB, each pinned to the one before, re-reading the ref before any retry, since a 499 can still land. It
    refuses a dirty tree, or a base that is not an ancestor of HEAD (round 4, Lane R4-B).""",
        """  - `2026-09-24_push_phase9_signed_groups.py`: lands this branch as signed commits, each pinned to the one
    before, re-reading the ref before any retry, since a 499 can still land. Its groups are at most 250 KB,
    except the ledger, which goes alone and last at about 780 KB, about 1 MB encoded. The tool's docstring
    cites failures from about 330 KB; Phase 8's ledger landed as one such commit at 683 KB (`fb9b382a`). It
    refuses a dirty tree, or a base that is not an ancestor of HEAD (round 4, Lane R4-B).""",
    ),
    # --- Consensus record --------------------------------------------------------------------------------------
    (
        "B2: round 4's record, bounded again",
        """    - the owner question's evidence, stated with bounds: arms like the pass's ran twice earlier that day, on at
      least twelve PRs; ml#2045's 00:00Z push was a fast-forward of 29 signed commits, not a force-push; and one
      touch of the key can sign a burst;""",
        """    - the owner question's evidence, stated with bounds: arms like the pass's ran twice earlier that day, on at
      least twelve PRs (round 5 found a third occasion and at least 20 PRs); ml#2045's 00:00Z push was a
      fast-forward of 29 signed commits, not a force-push; and one touch of the key can sign a burst;""",
    ),
    (
        "B3: round 4's record of the status bar",
        """    - the REPLAYING bullet: Apply is refused too, and the status bar shows Stopped because canopy maps an
      unknown status to Stopped;""",
        """    - the REPLAYING bullet: Apply is refused too, and the status bar shows Stopped because canopy maps an
      unknown status to Stopped (round 5 corrected the mapping it cited: the bar's own `else`, not
      `state_sync.py:177`);""",
    ),
    (
        "Round 5's record",
        f"""  - **Round 4 changed a number and actions**, so §4 of {PROC} calls for a round 5. An archived handoff,
    `HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md`, repeats the
    204 claim; archived handoffs are not edited.
""",
        f"""  - **Round 4 changed a number and actions**, so §4 of {PROC} called for a round 5. An archived handoff,
    `HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md`, repeats the
    204 claim; archived handoffs are not edited.
  - **Round 5**: two lanes on the frozen `07aef715`. Lane R5-A re-derived round 4's claims from their
    artifacts; Lane R5-B attacked round 4's corrections. Both returned SOUND-WITH-FIXES. The replay of round 4's
    script is exact, both launch-scan outputs regenerate byte-identical, and the counts, F-CANOPY-014's
    precedent, item 17, the F-CANOPY-015 pointer, the REPLAYING refusals and the signed-commit facts held.
  - **What round 5 changed:**
    - the owner question, answered for the pass's sweeper four minutes after the freeze (R5-B): "Who", item 15
      and "What the evidence cannot support" record the answer and its scope;
    - the arm census: at least three earlier occasions and at least 20 PRs, where two and twelve stood; three
      later background launches, not two, the two `safe_merge` runs re-arming canopy#670 after its disarms;
      and ml#2045's 03:02:06Z push of three commits signed with the owner's key;
    - the status bar's cause: its own `else` and, while F-CANOPY-055 is open, its layout default, not
      `state_sync.py:177`; item 16's check now reads `fsm_status` and the badge;
    - the push tool's group sizes, the scan's round-3 forms and its docstring (the forms it still misses), and
      item 13's account of the FAQ's old error and of the follow-up's review, which terminated at round 8;
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round5_corrections.py`, with no hand
      edit to the ledger.
  - **Re-derived before applying (round 5):** the owner's question and answer (lines 4227 and 4260 of
    `bc31e993`'s transcript); the events of ml#2059, canopy#676 and canopy#678; canopy#670's arms and
    disarms, ml#2041's single arm, the 13:35:20Z foreground command and the three background rows; the arms
    of ml#2013, deploy#228 and ml#2057; the status bar's `else` and layout default; ml#2045's 03:02:06Z push
    (activity and compare APIs) and its closing; the FAQ's text at `b07943d6`; and Phase 8's 683 KB ledger
    upload (`fb9b382a`). Not re-derived: the rest of the lanes' arm census, the signing key of the 03:00Z
    commits, and that no transcript names ml#2057 between 19:50Z and 21:00Z.
  - **Round 5 changed a disposition, numbers and actions**, so §4 of {PROC} calls for a round 6 on these
    corrections.
""",
    ),
    (
        "B1: what the evidence cannot support, after the answer",
        """  - who readied and armed canopy#676, or re-ran its CI, beyond "no Claude Code process on this host"
    (foreground calls and background launches whose command lines match a pattern, which a script run by an
    unnamed path escapes);""",
        """  - who re-ran #676's CI, or took the account's other later actions, beyond "no Claude Code process on this
    host" (foreground calls and background launches whose command lines match a pattern, which a script run
    by an unnamed path escapes): the owner's answer covers the sweeper that readied and armed the pass's PRs
    and names neither, and it covers #676's own ready and arm by the pass's pattern, not by name;""",
    ),
    # --- Still owed ----------------------------------------------------------------------------------------------
    (
        "C8, B7: item 13, the follow-up's review ended, and the FAQ's old error",
        f"""      follow-up, branch `fix/idle-cuts-round3-wording` (local, on `e9053227`, not yet pushed), which opens as a
      PR after this phase lands, the order #676 broke, and only once its own review terminates under §4 of
      {PROC}. Its review rounds are archived in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. Its FAQ
      note once named the wrong way out of a stuck replay (an API stop or a restart); round 5 corrected it to
      Reset Training, and the archived round-5 brief quotes the old text. It covers:""",
        f"""      follow-up, branch `fix/idle-cuts-round3-wording` (local commit `26bf27b3` on `e9053227`, not yet
      pushed), which opens as a PR after this phase lands, the order #676 broke. Its review terminated at round
      8 under §4 of {PROC}: Lane C8 found nothing false and returned MERGE. Its rounds are archived in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. Its FAQ
      note once called the player's Stop canopy's only way to stop a cascor replay, which left only an API stop
      or a restart; the follow-up's round 5 (Lane C5, whose report quotes the old text) found the sidebar's
      Reset Training, and the note now names it. It covers:""",
    ),
    (
        "B1, B2: item 15, answered for the sweeper",
        """    - Were the 21:47–22:51Z pass over nine PRs, and the account's later actions, his? Those are the update-branches
      on ml#2066 and data#434 (23:16–23:17Z), ml#2045's disarm and re-arm (23:48Z), cascor-worker#196's merge
      (01:21:37Z) and #676's CI re-run (01:22:32Z), without which its armed merge could not fire. No Claude Code
      process on this host did any of them ("Who", above), while commits signed with the owner's key landed at
      21:45:22Z, 23:47:30Z and 23:57–00:00Z, and arms like the pass's ran twice earlier that day (00:52–01:08Z
      and 13:17–13:32Z). Lane R2-F reports interactive git activity in host
      reflogs from about 21:39Z to 00:07Z (not re-derived). If they were not his, nothing held a PR that night:
      not a disarm, a draft or a comment. Only a PR that does not yet exist is held.""",
        """    - **Answered for the sweeper (2026-09-24):** the pass over nine PRs, 21:47–22:51Z, was the owner's sweeper
      ("Who", above), whose merges the owner calls intended. Still the owner's to confirm, because the question
      did not name them: the account's later actions, which are the update-branches on ml#2066 and data#434
      (23:16–23:17Z), ml#2045's disarm and re-arm (23:48Z), cascor-worker#196's merge (01:21:37Z) and #676's CI
      re-run (01:22:32Z), without which its armed merge could not fire; and ml#2045's draft and ready the next
      morning (03:04–03:05Z). No Claude Code process on this host did any of them, while commits signed with the
      owner's key landed at 21:45:22Z, 23:47:30Z, 23:57–00:00Z and 03:00–03:02Z. Lane R2-F reports interactive
      git activity in host reflogs from about 21:39Z to 00:07Z (not re-derived). What follows for this arc: a
      disarm, a draft or a comment does not hold a PR, so a PR that must be validated before it merges is
      validated before it is opened.""",
    ),
    (
        "A2, B3: item 16's check must be able to fail",
        "      should check that Start and Apply work after one, and what the status bar says meanwhile.",
        """      should check that Start and Apply work after one, and what `/api/status`'s `fsm_status` and the Network
      Editor's badge say meanwhile: while F-CANOPY-055 is open the status bar reads Stopped whatever happens.""",
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
