#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-6 validation corrections (Lanes R6-A and R6-B).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-6 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round6.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round5_corrections.py (the pass this corrects)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the answer extractor's and the launch scan's secret shapes and the
ad-hoc README were edited directly. Labels: A = R6-A, B = R6-B.

The pass's centre is the scope of the owner's answer, which round 5 stated three different ways: it names
four PRs, three of which were drafts, and reaches the pass's other drafts, #676 included, only through their
shared pattern. It is now stated once, in "Who", and the other two places defer to it.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round6_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"

SUBS = [
    # --- "Who" ---------------------------------------------------------------------------------------------------
    (
        "A1, B1, B2: the answer's time, its three drafts, and its scope, stated once",
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
        """    - **The owner has answered: the sweeper is the owner's.** It acts as `pcalnon` and is not Claude Code on
      this host. Session `bc31e993` asked at 03:34:45Z on 2026-09-24, and the owner answered at 07:32:48Z, four
      minutes after round 5's artifact was frozen. The question named four PRs of the pass above (data#428,
      ml#2032, ml#2059 and canopy#678) as taken out of draft and armed 4–7 s later as `pcalnon`, which three
      were; canopy#678 was never a draft and merged directly, with no arm event. It added that cascor#678 was
      armed the same way that morning, and asked whether that sweeper was the owner's. The owner chose "Mine:
      fix forward", an option whose text says the sweeper is the owner's and "the merges", those PRs', are
      intended, with validation continuing after the merge and fixes going forward in follow-up PRs.
      - **Its scope.** It names none of the pass's other five PRs. It reaches three of them, #676, data#431 and
        data#434, only through the shared pattern (a draft readied, then armed 4–8 s later), and ml#2066's arm
        and data-client#212's direct merge not even that way. It does not cover #676's CI re-run, the account's
        other later actions or ml#2045's next morning, which remain the owner's to confirm (Still owed, item
        15).
      - Lane R5-B found the exchange; `util/ad-hoc/2026-09-24_owner_answer_extract.py` prints it, redacted,
        from lines 4227 and 4260 of that session's transcript.""",
    ),
    (
        "Wording: the 03:00Z commits' committer",
        'three commits by "Paul Calnon", committed 03:00:20Z to 03:01:48Z with valid signatures',
        'three commits committed by "Paul Calnon" between 03:00:20Z and 03:01:48Z, with valid signatures',
    ),
    # --- F-CANOPY-059: F-055's freeze is page-dependent ---------------------------------------------------------
    (
        "B4: the bar freezes only on a page slower than its tick",
        """(`dashboard_manager.py:7508-7518`), and while F-CANOPY-055 is open it holds its layout default, also Stopped
  (`:887`), whatever cascor reports.""",
        """(`dashboard_manager.py:7508-7518`). On a page slower than its 1 s tick, F-CANOPY-055 (open) also holds it at
  its layout default, which is Stopped too (`:887`).""",
    ),
    # --- Instruments ---------------------------------------------------------------------------------------------
    (
        "Round list: the round-6 report",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5}.md`",
        "the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4,5,6}.md`",
    ),
    (
        "B3: the widened secret shapes, and their check",
        """  - `2026-09-24_owner_answer_extract.py`: prints chosen records of a session transcript, redacted; round 5
    used it for the owner's answer ("Who", above).
""",
        """  - `2026-09-24_owner_answer_extract.py`: prints chosen records of a session transcript, redacted; round 5
    used it for the owner's answer ("Who", above). Round 6 widened its secret shapes, and the launch scan's and
    the archive tool's, after Lane R6-B found `sk-ant-…` keys passing it; `2026-09-24_secret_shape_check.py`
    tests all three against constructed fake values, both ways.
""",
    ),
    (
        "Tools: round 6's pass",
        """rounds 3 to 5's passes
    are `…_round{3,4,5}_corrections.py`, likewise.""",
        """rounds 3 to 6's passes
    are `…_round{3,4,5,6}_corrections.py`, likewise.""",
    ),
    # --- Consensus record ----------------------------------------------------------------------------------------
    (
        "B1: round 5's record of the answer",
        """    - the owner question, answered for the pass's sweeper four minutes after the freeze (R5-B): "Who", item 15
      and "What the evidence cannot support" record the answer and its scope;""",
        """    - the owner question, answered four minutes after the freeze for the sweeper that readied and armed the
      drafts it named (R5-B): "Who", item 15 and "What the evidence cannot support" record the answer and its
      scope;""",
    ),
    (
        "B4: round 5's record of the bar",
        """    - the status bar's cause: its own `else` and, while F-CANOPY-055 is open, its layout default, not
      `state_sync.py:177`; item 16's check now reads `fsm_status` and the badge;""",
        """    - the status bar's cause: its own `else` (and, on a page slower than its tick, F-CANOPY-055's frozen
      layout default), not `state_sync.py:177`; item 16's check now reads `fsm_status` and the badge;""",
    ),
    (
        "A2: round 5's not-re-derived item, false as worded",
        "    commits, and that no transcript names ml#2057 between 19:50Z and 21:00Z.",
        """    commits, and that no transcript runs an arming-capable command naming ml#2057 or its branch between 19:50Z
    and 21:00Z (session `1f771cb0` opened it at 20:09:28Z and ran only the read-only `watch_pr_runs.bash`).""",
    ),
    (
        "Round 6's record",
        f"""  - **Round 5 changed a disposition, numbers and actions**, so §4 of {PROC} calls for a round 6 on these
    corrections.
""",
        f"""  - **Round 5 changed a disposition, numbers and actions**, so §4 of {PROC} called for a round 6 on these
    corrections.
  - **Round 6**: two lanes on the frozen `b0b17cad`. Lane R6-A re-derived round 5's claims from their
    artifacts; Lane R6-B attacked round 5's corrections. A session limit killed both mid-review; both were
    resumed with their context and returned SOUND-WITH-FIXES. The replay of round 5's script is exact, and every
    count, time and source line round 5 added held, including the signing key of the 03:00Z commits.
  - **What round 6 changed:**
    - the owner's answer: the question's time (03:34:45Z; 07:32:48Z is the answer), the three of its four PRs
      that were drafts, and one statement of its scope, in "Who", which item 15 and "What the evidence cannot
      support" now follow;
    - "whatever cascor reports": F-CANOPY-055 freezes the bar only on a page slower than its tick, and the bar
      reads Stopped during a replay through its own `else` either way;
    - round 5's "not re-derived" item on ml#2057, false as worded, which R6-A re-derived;
    - the secret shapes of the answer extractor, the launch scan and the archive tool, which missed seven,
      seven and three of the shapes `2026-09-24_secret_shape_check.py` tests (`sk-ant-…` keys among them).
      None occurs in the archived evidence: both scan windows regenerate byte-identical, and all 36 archived
      files pass. Also the README's push-tool sizes, and the follow-up's rebase onto canopy#679 (item 13);
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round6_corrections.py`, with no hand
      edit to the ledger.
  - **Re-derived before applying (round 6):** the question's and the answer's records (lines 4227 and 4260),
    canopy#678's events, the widened secret shapes (`2026-09-24_secret_shape_check.py` fails 17 times on round
    5's tools and passes on these), and the follow-up's rebase (`git range-diff` gives an identical patch, and
    its test file gives 13 passed). Both lanes' other findings
    concern wording this pass's predecessor wrote.
  - **Round 6 changed a disposition, numbers and an action**, so §4 of {PROC} calls for a round 7 on these
    corrections.
""",
    ),
    (
        "B1: what the evidence cannot support, one scope",
        """by an unnamed path escapes): the owner's answer covers the sweeper that readied and armed the pass's PRs
    and names neither, and it covers #676's own ready and arm by the pass's pattern, not by name;""",
        """by an unnamed path escapes): the owner's answer covers the sweeper that readied and armed the drafts it
    named, and names neither; #676's own ready and arm are tied to that sweeper by the pass's pattern, not by
    the answer;""",
    ),
    # --- Still owed ----------------------------------------------------------------------------------------------
    (
        "Item 13: the follow-up rebased onto canopy#679",
        """follow-up, branch `fix/idle-cuts-round3-wording` (local commit `26bf27b3` on `e9053227`, not yet
      pushed), which opens as a PR after this phase lands, the order #676 broke.""",
        """follow-up, branch `fix/idle-cuts-round3-wording` (local commit `26bf27b3` on `e9053227`, rebased with an
      identical patch as `96e7b105` onto canopy `main` `6c4ad9a9` after canopy#679 changed `CHANGELOG.md`; not
      yet pushed), which opens as a PR after this phase lands, the order #676 broke.""",
    ),
    (
        "B1: item 15, one scope",
        """    - **Answered for the sweeper (2026-09-24):** the pass over nine PRs, 21:47–22:51Z, was the owner's sweeper
      ("Who", above), whose merges the owner calls intended. Still the owner's to confirm, because the question
      did not name them:""",
        """    - **Answered for the sweeper (2026-09-24):** the sweeper that readied and armed the drafts the question
      named is the owner's, and the owner called their merges intended; the pass's other drafts, #676 included,
      share its pattern but were not named ("Who", above, gives the answer's scope). Still the owner's to
      confirm, because the question did not name them:""",
    ),
    (
        "B4: item 16's check, without the overreach",
        """      Editor's badge say meanwhile: while F-CANOPY-055 is open the status bar reads Stopped whatever happens.""",
        """      Editor's badge say meanwhile: the status bar reads Stopped both during a replay (its own `else`) and after
      one, so it cannot tell them apart.""",
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
