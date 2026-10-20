# Lanes 13-R4A and 13-R4B brief — Phase 13 of the canopy E2E ledger, round 4: round 3's corrections only

You are one of two independent validators in round 4, under §4 of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`: brief the round explicitly on
the corrections, not on the whole artifact; find what they broke. You have not seen the other lane's verdict.
**Lane 13-R4A** re-derives: replay the pass and re-create every claim it introduced. **Lane 13-R4B** is adversarial
on the pass: what did round 3's corrections break, overstate, or leave inconsistent across the files?

## What is under review

Round 3 reviewed local commit `10194b8c` with two lanes; their reports are verbatim in
`reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round3.md`. The correction pass
`util/ad-hoc/2026-10-19_phase13_ledger_round3_corrections.py` (9 substitutions in the ledger plus the round-3 record;
4 in the new handoff; 1 in the Phase 12 handoff's banner; 3 in the 2026-05-05 roadmap audit) was applied to produce
local commit **`369863cf`**, now checked out in worktree
`/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/federated-stargazing-blanket` (branch
`docs/canopy-e2e-phase13`; the working tree equals the freeze). The diff under review is
`git diff 10194b8c 369863cf` run from that worktree: the ledger, the new handoff, the Phase 12 handoff, the audit
(`notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`), the round-3 brief, the round-3 report file and the
pass itself. The ledger's Phase 13 is at `grep -n '^## Phase 13'`; its "Consensus record" holds rounds 1 to 3, the
first two amended where they misdescribed themselves.

Round 3's substance: the audit restated its §5.2 shipping claim in three rows round 2 had not touched (the Status
delta under §5.2, the §8.1 row, the §11.7 row); each now carries a pointer to §5.2's dated correction. The ledger's
absolute "no document … still records the stream as shipped" is narrowed accordingly; "four sites in three
documents"; the roadmap's CAN-015 row is described as a pointer, not the note; the audit's line cites are pinned to
`c741351c`; the F-CANOPY-012 qualifier ("more than one output") reaches item 30 and the handoff's item 2; the
handoff's landing trap names the apply script and the three correction passes; the records say "eight" places, add
the F-CANOPY-049 counter-reading beside the F-CANOPY-067 dissent for 10 and 10, and list the hunks round 2 omitted.

## Your job

1. **Replay the pass.** From the worktree, `git show 10194b8c:<path>` each of the four files the pass edits into your
   scratch directory under the same relative paths (the ledger, the new handoff, the Phase 12 handoff, the audit),
   run `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round3_corrections.py --root <your copy>`, and compare each
   result byte for byte with `git show 369863cf:<same path>`. Report whether it replays with no hand edit. Then run it
   with `--check` against the worktree and report that it refuses.
2. **Re-derive every claim the pass introduced** (the round-3 record's "What round 3 changed" and "Re-derived by the
   orchestrator" lists), each with your own command:
   - the audit at `10194b8c`: `:168` ("Status delta"), `:225` (the §8.1 row), `:360` (the §11.7 row); that these three
     and no other lines changed between `10194b8c` and `369863cf` (`git diff --numstat`; `git diff` hunks); that the
     pointers add no markdown link; that §5.2's sentence, g-3 row and §11.4 sit at `:134`, `:142` and `:328-333` at
     `369863cf`; whether any further line of the audit still asserts CAN-015g or g-3 as shipped without a pointer
     (grep the file for `shipped`, `CAN-015g`, `g-3`, `#190`; report every hit and whether it is covered);
   - the ledger's Summary, F-CANOPY-057's Status bullet, "The design note's correction" and the Matrix effect at
     `369863cf`: the reach statement says every site carries the correction or a pointer; the audit cites say "at
     `c741351c`"; "four sites in three documents"; the CAN-015 row is "pointed at" the note (check the roadmap row at
     `:5196`: it is a pointer clause, not the note);
   - the handoff at `369863cf`: item 4 ("four sites in three documents"), item 2's qualifier, the landing trap naming
     the apply script and `round{1,2,3}_corrections.py` in that order, the "Changed by this session" audit line; run
     the verification commands (all read-only; the two `Correction 2026-10-19` greps 1 each; `grep -c '^OPEN   P1 '` 9);
     and the Phase 12 handoff's banner at `:4-7`;
   - the records: round 1's amended sentence now reads "all eight … the parent's O17" and names the INDEX and the
     parent's item 4 as carrying the corrected-document list and counts only (check: the INDEX's P2 row and the
     parent's item 4 contain no "first limb"); round 2's record says "10 and 10 remains by the F-CANOPY-067 dissent
     and by the F-CANOPY-049 counter-reading" and lists the hunks round 3 added; round 3's record against the diff
     hunk by hunk (every change listed, nothing listed the diff does not make); the lane credits against the round-3
     report file;
   - the triage on `369863cf`: 79 / 56 / 1 / 2 / 20; 9 open P1; 11 open P2, unchanged; the five headers unchanged by
     the pass (`git diff 10194b8c 369863cf -- <ledger> | grep '^[-+]\*\*F-'` should print nothing).
3. **Cross-file consistency after the pass** (Lane 13-R4B especially): nothing in the nine files still says "no
   document … still records the stream as shipped" without the "correction or a pointer" qualifier, "only by the
   F-CANOPY-067 dissent", "all nine", "four documents" (outside the records' quotations of earlier rounds), or
   describes the CAN-015 row as carrying the note; the dissents unchanged and stated as the lanes stated them; the
   parent's O17 and item 4 and the INDEX (unchanged by this pass) still consistent with the ledger's statements.
4. **Gates**: `python3 -B -m unittest tests.test_thread_handoff_archive tests.test_e2e_finding_triage
   tests.test_e2e_finding_triage_nested_bold tests.test_e2e_finding_triage_priority`; the secret and e-mail grep over
   `git diff 10194b8c 369863cf` (no `@` outside hunk headers and backticked rule text; no token prefixes).

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13R4A/`
  or `…/lane13R4B/` (create yours). Run Python with `-B`. Do not run any git command that changes state, and run git
  only inside that worktree (the session's guard refuses `git -C` on other repos, `awk` programs, `sed` with shell
  variables and `$(…)` inside commands; use literal paths and plain commands). Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- A claim is wrong only if the artifact says otherwise. A rounding or wording difference that changes no number,
  disposition or action is a NIT.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 13-R4A** (replay and re-derivation, round 4)` or `**Lane 13-R4B** (adversarial on the pass, round 4)`
and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`. Then **REPLAY** (one line per file: byte-identical or not).
Then a **TABLE** (claim | re-derived | result | evidence). Then **FINDINGS**, numbered, each with severity
(BLOCKER / MAJOR / MINOR / NIT), the text quoted, your evidence, the fix, and the line "Changes a number,
disposition or action? yes/no". Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line. Keep it under
14,000 characters.
