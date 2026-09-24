#!/usr/bin/env python
"""Apply the Phase 9 ledger's round-4 validation corrections (Lanes R4-A and R4-B, plus canopy Lane C6's lead).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-4 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phases 9 and (one pointer) 1;
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round4.md;
         util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py (the pass this corrects)

Exact substitutions, each matching exactly once, or the script refuses and writes nothing. Nothing in this
pass is applied to the LEDGER by hand; the tools' code was edited directly. Labels: A = R4-A, B = R4-B,
C6 = the canopy follow-up's round-6 lane.

A lesson this pass applies: every round so far widened the "Who" narrative, and every widening invited a
new count to be wrong. The morning arms are therefore stated as bounded facts with pointers to the round
reports, not as a growing list.

Usage:
    python3 util/ad-hoc/2026-09-24_phase9_ledger_round4_corrections.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"

PROC = "`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`"
R4 = "`reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round4.md`"

SUBS = [
    # --- Summary and header ----------------------------------------------------------------------------------
    (
        "B13: the way out, in the summary",
        """    page also leaves cascor refusing training, while canopy shows Stopped, until someone presses Reset
    Training.""",
        """    page also leaves cascor refusing training until a Reset Training on the page, or a stop through cascor's
    API.""",
    ),
    (
        "B13: the way out, in F-059's header",
        "while cascor stays in REPLAYING and refuses training until someone presses Reset Training (P0,",
        "while cascor stays in REPLAYING and refuses training until a Reset Training or an API stop (P0,",
    ),
    # --- #676's round 2 ---------------------------------------------------------------------------------------
    (
        "B11: GitHub has it once this phase lands",
        """    unpushed branch; this phase's `5a0e4ea9` is its rebased copy), so GitHub never had it.""",
        """    unpushed branch; this phase's `5a0e4ea9` is its rebased copy), so GitHub did not have it before #676
    merged.""",
    ),
    # --- "Who" -----------------------------------------------------------------------------------------------
    (
        "B5, A8: what the pattern cannot see",
        """        re-run a PR (outputs in `reports/e2e-canopy-2026-09-02/phase9-scratch/ledger_r2_orchestrator/`). It is a
        pattern, not a proof: a script run by a path the pattern does not name is outside it. The only""",
        """        re-run a PR (outputs, regenerated in rounds 3 and 4 under the round-2 directory name, in
        `reports/e2e-canopy-2026-09-02/phase9-scratch/ledger_r2_orchestrator/`). It is a pattern, not a proof: a
        push, a script it does not name, or a command form it does not match is outside it. Rounds 3 and 4 each
        added forms it had missed, and no launch of those forms was found (Lanes R4-A and R4-B). The only""",
    ),
    (
        "A1-A4, A7, B1, B12: the owner evidence, bounded",
        """    - **Commits signed locally with the owner's key landed in that window** (Lanes R2-B and R3-A; re-derived
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
        f"""    - **Commits signed with the owner's key landed in that window** (Lanes R2-B, R3-A and R4-A; re-derived
      from the commits API). `4c496443` on ml#2058 (committed 21:45:22Z, two minutes before the pass's first
      ready) and `c666403b` on ml#2045 (23:47:30Z, a minute before that PR's disarm and re-arm) are committed
      by "Paul Calnon", not by GitHub's web-flow, with valid PGP signatures, while no Claude Code session made a
      tool call. On this host signing needs the owner's hardware key (`util/push_signed_commit.py`'s docstring
      says a touch; R4-A found five signatures stamped within one second, so one touch can cover a burst).
      ml#2045 also took a fast-forward push at 00:00:38Z of 29 more commits signed with that key between
      23:57:24Z and 00:00:07Z (R4-A, from the activity and compare APIs; R3-A had read it as a force-push).
    - **Arms like the pass's happened twice earlier that day** (Lanes R3-B, R4-A and R4-B; the arm events of
      ten of the PRs re-derived from their timelines). At least nine PRs across four repos were armed as
      `pcalnon` between 13:17:53Z and 13:32:10Z, and ml#2020, canopy#655 and cascor#673 between 00:52:07Z and
      01:08:14Z, and R4-A's scan of every tool call found no command arming any of them. R4-A's sweep covered
      each repo's 60 most recently updated PRs, so nine is a lower bound; each lane's list is in {R4}.
      Session `bc31e993` was working on ml#2032 and data#428 at 13:18–13:19Z (a retitle and a signed fix-up),
      without arming them, and its handoff that evening is titled "…four-prs-armed-by-an-unseen-actor…" (R4-A
      read it). Two background launches the pattern matches name morning PRs, and both came after those PRs'
      arms: `safe_merge --pr 670` at 15:29Z and 15:55Z, and a shepherd for ml#2041 at 13:35Z, which cannot arm.
    - **ml#2045 again, the next morning:** drafted at 03:04:45Z, which disarmed it (03:04:46Z), and readied at
      03:05:02Z, with no tool call on this host between 01:40Z and 03:26:44Z (Lanes R4-A and R4-B). It was not
      re-armed.""",
    ),
    # --- F-CANOPY-059 ------------------------------------------------------------------------------------------
    (
        "B4, A5, A6, B13: what the page shows, and Apply",
        """- **cascor stays in REPLAYING** (Lanes R3-A and R3-B; re-derived in source). It refuses a new network
  (`manager.py:1731-1732`), starting or stopping training (`:2452-2453`, `:2842-2843`), and restore, retrain
  and resume (`routes/snapshots.py:278`, `:329`, `:378`). It reports its training state as Stopped / Idle
  meanwhile (`manager.py:6001-6003`), so canopy shows Stopped while Start fails. The player's Stop is canopy's
  only caller of cascor's `/replay/control` (`replay_player_panel.py:371`), and it is never on screen. The one
  way out on the page is the sidebar's Reset Training: its button is disabled only while its own command is in
  flight (`dashboard_manager.py:8548-8549`), the adapter's `reset_training` (`cascor_service_adapter.py:1137-1139`)
  calls cascor's `/v1/training/reset` (`routes/training.py:169-173`), and cascor documents `reset()` as
  REPLAYING's escape hatch. Nothing on the page points a user to it.""",
        """- **cascor stays in REPLAYING** (Lanes R3-A, R3-B, R4-A and R4-B; re-derived in source). It refuses a new
  network (`manager.py:1731-1732`), starting or stopping training (`:2452-2453`, `:2842-2843`), the parameter
  updates Apply sends (`:4742-4743`), and restore, retrain and resume (`routes/snapshots.py:278`, `:329`,
  `:378`). It reports its training state as Stopped / Idle meanwhile (`manager.py:6001-6003`), and canopy maps
  the REPLAYING status it does not know to Stopped (`state_sync.py:177`), so the status bar shows Stopped; the
  Network Editor's badge alone reads "FSM: Replaying". A Start fails with cascor's refusal, whose text says to
  invoke `/replay/control` with `stop`. The player's controls are canopy's only callers of that route
  (`replay_player_panel.py:371`), its Stop the only one that ends a replay, and none is on screen. The one way
  out on the page is the sidebar's Reset Training: its button is disabled only while its own command is in
  flight (`dashboard_manager.py:8548-8549`), the adapter's `reset_training` (`cascor_service_adapter.py:1137-1139`)
  calls cascor's `/v1/training/reset` (`routes/training.py:169-173`), and cascor documents `reset()` as
  REPLAYING's escape hatch; a reset also discards the run's metrics and counters, not its data. Nothing on
  the page points a user to it.""",
    ),
    (
        "B2: F-CANOPY-014's controls were on screen and failing, and it also stranded cascor",
        """  F-CANOPY-056, whose controls it keeps off screen, and it leaves cascor refusing training. F-CANOPY-014, which
  disabled the same controls through a different fault (an empty base URL), was rated P1 and is fixed. This one
  is worse, since no session view appears at all, and §6.3's words give P0; which rating replay findings take
  is an owner question (Still owed, item 15).""",
        """  F-CANOPY-056, whose controls it keeps off screen, and it leaves cascor refusing training. F-CANOPY-014 broke
  the same workflow through a different fault: its controls were on screen but every one failed on an empty
  base URL, Stop included, so it too left cascor replaying (Phase 1 ended that session with a direct API stop).
  It was rated P1 and is fixed. What this one adds is that no session view appears at all. §6.3's words give
  P0 to a finding that blocks the workflow, which would cover F-CANOPY-014 too; which rating replay findings
  take is an owner question (Still owed, item 15).""",
    ),
    # --- Instruments -------------------------------------------------------------------------------------------
    (
        "B6, B7, A8: what the tools do now",
        """    each call's background flag. Widened after round 3 found forms it missed ("Who", above).
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py`: the rest of this phase's tmpfs evidence, round 2's
    included, from two sessions' scratchpads. It refuses secret shapes (widened after round 3 to every
    `gh*_` token prefix and JWTs) and any file holding an e-mail address other than a `noreply` one or the
    Codecov uploader's public key address, which CI logs print.""",
        """    each call's background flag. Widened in rounds 3 and 4, after each found forms it missed ("Who", above).
  - `2026-09-24_archive_phase9_tmpfs_evidence_round2.py`: the rest of this phase's tmpfs evidence, round 2's
    included, from two sessions' scratchpads. It refuses secret shapes and any file holding an e-mail address
    other than one containing `noreply` or one at `codecov.io` (the uploader's public key, which CI logs
    print). Since round 4 it re-checks the files it already archived; all 36 pass.
  - `2026-09-24_push_phase9_signed_groups.py`: lands this branch as signed commits in groups of at most
    250 KB, each pinned to the one before, re-reading the ref before any retry, since a 499 can still land. It
    refuses a dirty tree, or a base that is not an ancestor of HEAD (round 4, Lane R4-B).""",
    ),
    # --- Consensus record: round 3's bullets, then round 4 ---------------------------------------------------------
    (
        "B9: R3-A's mismatches",
        """    replay of round 2's script is exact, and every number and date R3-A re-derived holds.""",
        """    replay of round 2's script is exact; R3-A's MISMATCH rows were corrected in this pass.""",
    ),
    (
        "B1: the re-derived list held a false claim",
        """    lines; `4c496443`'s and `c666403b`'s committers and signatures; the morning's arms and that no logged
    command names those PRs then; ml#2045's 03:04–03:05Z draft and ready; `800c20bb`'s content; #189's""",
        """    lines; `4c496443`'s and `c666403b`'s committers and signatures; the morning's arms (but not the claim,
    false as worded, that no logged command named those PRs then); ml#2045's 03:04–03:05Z draft and ready;
    `800c20bb`'s content; #189's""",
    ),
    (
        "B10, B14: the tools were hand-edited; Phase 4's row",
        """    - all in `util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py`, with no hand edit to the ledger.""",
        """    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round3_corrections.py`, with no hand
      edit to the ledger (the tools' code was edited directly), including a pointer in Phase 4's F-CANOPY-015
      row.""",
    ),
    (
        "B10 and the round-4 record",
        """  - **Round 3 changed numbers and actions**, so §4 of the consensus procedure calls for a round 4 on these
    corrections.
""",
        f"""  - **Round 3 changed numbers and actions**, so §4 of {PROC} called for a round 4 on these corrections.
  - **Round 4**: two lanes on the frozen `86e82c0c`. Lane R4-A re-derived round 3's new claims from their
    artifacts; Lane R4-B attacked round 3's corrections. Both returned SOUND-WITH-FIXES. The replay of round 3's
    script is exact, and the REPLAYING lock-in, the Reset escape, #184, the dates, the line numbers and
    `800c20bb` held.
  - **What round 4 changed:**
    - the owner question's evidence, stated with bounds: arms like the pass's ran twice earlier that day, on at
      least twelve PRs; ml#2045's 00:00Z push was a fast-forward of 29 signed commits, not a force-push; and one
      touch of the key can sign a burst;
    - F-CANOPY-014's precedent: it too left cascor replaying, so only the missing session view separates the
      two ratings;
    - the REPLAYING bullet: Apply is refused too, and the status bar shows Stopped because canopy maps an
      unknown status to Stopped;
    - a new lead, Still owed item 17, from the canopy follow-up's round 6;
    - the tools: the scan's pattern, the e-mail rule and re-checking of archived files, and the push tool's
      clean-tree and ancestry checks;
    - pointers: F-CANOPY-015's own entry now points to F-CANOPY-059;
    - the ledger's changes all in `util/ad-hoc/2026-09-24_phase9_ledger_round4_corrections.py`, with no hand edit
      to the ledger.
  - **Re-derived before applying (round 4):** the arm events of ten PRs; the Network Editor's badge, the Apply
    refusal and `state_sync.py:177`; the network swap (`manager.py:1472`, `:5734`, `:5977`) and canopy's two
    "read-only" texts; the C4 paused-start claim (`manager.py:1076`, and `_run`'s `_emit_frame(0)`). Not
    re-derived: the arms of canopy#670 and ml#2038, the 29-commit push, the five signatures in one second, and
    `bc31e993`'s handoff title.
  - **Round 4 changed a number and actions**, so §4 of {PROC} calls for a round 5. An archived handoff,
    `HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md`, repeats the
    204 claim; archived handoffs are not edited.
""",
    ),
    # --- Still owed ------------------------------------------------------------------------------------------------
    (
        "B10, B3: item 13's procedure reference, and the C5 brief's old text",
        """      PR after this phase lands, the order #676 broke, and only once its own review terminates under §4 of
      the consensus procedure. Its review rounds are archived in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. It
      covers:""",
        f"""      PR after this phase lands, the order #676 broke, and only once its own review terminates under §4 of
      {PROC}. Its review rounds are archived in
      `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_canopy_followup.md`. Its FAQ
      note once named the wrong way out of a stuck replay (an API stop or a restart); round 5 corrected it to
      Reset Training, and the archived round-5 brief quotes the old text. It covers:""",
    ),
    (
        "A1, B1, B2: item 15's evidence and the precedent",
        """      process on this host did any of them ("Who", above), while commits signed locally with the owner's key
      landed at 21:45:22Z and 23:47:30Z, and the same arming pattern ran that morning at 13:23–13:29Z.""",
        """      process on this host did any of them ("Who", above), while commits signed with the owner's key landed at
      21:45:22Z, 23:47:30Z and 23:57–00:00Z, and arms like the pass's ran twice earlier that day (00:52–01:08Z
      and 13:17–13:32Z).""",
    ),
    (
        "B2: the rating question",
        """      F-CANOPY-057 P1, F-CANOPY-059 P0, against F-CANOPY-014's P1 for the same controls (F-CANOPY-059's
      severity bullet).""",
        """      F-CANOPY-057 P1, F-CANOPY-059 P0, against F-CANOPY-014's P1 for a fault that also blocked replaying and
      also left cascor replaying (F-CANOPY-059's severity bullet).""",
    ),
    (
        "items 13 to 17",
        "- Items 13, 14, 15 and 16 are new.\n",
        "- Items 13 to 17 are new.\n",
    ),
    (
        "B4 and C6: item 16 checks Apply; item 17 is the network-swap lead",
        """      should check that Start works after a Replay.
""",
        """      should check that Start and Apply work after one, and what the status bar says meanwhile.
17. **New lead, not yet a finding: a replay replaces cascor's live network** (Lane C6 of the canopy
    follow-up's review; re-derived in source). `start_replay` calls `_load_snapshot_to_network`
    (`manager.py:5977`), which sets `self.model` to the snapshot's network (`:5734`); neither `reset()` nor
    `stop_replay()` restores the earlier one, and `_auto_snap_best` is off by default (`:1472`). So a Replay
    discards an unsaved trained network, while canopy's Replay modal promises "a read-only playback session"
    (`hdf5_snapshots_panel.py:533`), as does the proxy route's docstring (`main.py:2985`). The canopy
    follow-up's FAQ note warns of it. Triage it: canopy's wording, cascor's design, or both (the owner).
""",
    ),
    (
        "the round-4 reports and briefs are archived",
        """  the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3}.md`; and the canopy""",
        """  the ledger's own validation, `…/2026-09-24_validator_reports_phase9_ledger_round{1,2,3,4}.md`; and the canopy""",
    ),
    # --- F-CANOPY-015's own entry, pointed at F-059 in place -------------------------------------------------------
    (
        "B14: F-015's entry points to F-059",
        """coincidence (P2, OPEN; root-caused, empirically confirmed).**
cascor's replay-start payload nests""",
        """coincidence (P2, OPEN; root-caused, empirically confirmed).**

> **Pointer added in Phase 9 (2026-09-24):** this finding's fix, canopy#532, reads `range` at the right level
> but indexes cascor's dict as a list, so every session cascor serves now crashes the player: F-CANOPY-059
> (P0).

cascor's replay-start payload nests""",
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
