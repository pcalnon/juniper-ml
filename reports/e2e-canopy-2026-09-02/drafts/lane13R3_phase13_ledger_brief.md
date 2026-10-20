# Lanes 13-R3A and 13-R3B brief — Phase 13 of the canopy E2E ledger, round 3: round 2's corrections only

You are one of two independent validators in round 3, under §4 of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`: "Brief round 2 explicitly on
the corrections, not on the whole artifact: these N changes were made in response to round 1; find what they
broke." The same rule governs this round against round 2's corrections. You have not seen the other lane's verdict.
**Lane 13-R3A** re-derives: replay the pass and re-create every claim it introduced. **Lane 13-R3B** is adversarial on
the pass: what did round 2's corrections break, overstate, or leave inconsistent across the files?

## What is under review

Round 2 reviewed local commit `c741351c` with two lanes; their reports are verbatim in
`reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round2.md`. The correction pass
`util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py` (19 substitutions in the ledger plus the round-2 record;
9 in the new handoff; 2 in the parent handoff, 1 in the INDEX, 1 in the V7 roadmap and 2 in the 2026-05-05 roadmap
audit) was applied to produce local commit **`10194b8c`**, now checked out in worktree
`/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/federated-stargazing-blanket` (branch
`docs/canopy-e2e-phase13`; the working tree equals the freeze). The diff under review is
`git diff c741351c 10194b8c` run from that worktree: the ledger, the new handoff, the parent handoff, the INDEX, the
V7 roadmap, the audit (`notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md`, new to the change set in this
round), the round-2 brief, the round-2 report file and the pass itself. The ledger's Phase 13 is at
`grep -n '^## Phase 13'`; its "Consensus record" now holds the round-1 record (amended by round 2 where it misdescribed
itself) and the round-2 record.

Round 2's substance: the audit's §5.2 says "both are **shipped end-to-end** on `main`" over the same per-PR table
the roadmap's §28.1 carried, while its own §11.4 confirmed only g-1 and g-6 of CAN-015g on cascor `main`; round 1 had
read the audit at its `:112` line alone. Round 2 gave §5.2 the same dated correction as the design note and §28.1,
annotated the roadmap's CAN-015 row, withdrew "10 and 10 by the broadest reading" (10 and 10 now remains only by
the F-CANOPY-067 dissent), fixed the handoff's stale item 8, moved the F-CANOPY-051 lead from `[0.5.0]` to `[0.6.0]`,
and amended round 1's record where it misdescribed its own change set.

## Your job

1. **Replay the pass.** From the worktree, `git show c741351c:<path>` each of the six files the pass edits into your
   scratch directory under the same relative paths (the ledger, the new handoff, the parent handoff, the INDEX, the
   V7 roadmap, the audit), run `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round2_corrections.py --root <your copy>`,
   and compare each result byte for byte with `git show 10194b8c:<same path>`. Report whether it replays with no hand
   edit. Then run it with `--check` against the worktree and report that it refuses.
2. **Re-derive every claim the pass introduced** (the round-2 record's "What round 2 changed" and "Re-derived by the
   orchestrator" lists), each with your own command:
   - the audit at `c741351c`: §5.2's sentence and its g-3 row (`:122-134`), §11.4's list (`:318-323`), the §5.1 line
     (`:112`); the audit's last change before this round (`git log --format='%h %ad %s' --date=short -3 -- <audit>`);
     that the correction at `10194b8c` states the same shas, times, bases and counts as the design note's, §28.1's and
     F-CANOPY-057's History; that it adds no markdown link; that the g-3 row is annotated;
   - the roadmap's CAN-015 row at `10194b8c` (`grep -n 'g-3 did not ship'`), and that nothing else in the roadmap changed
     between `c741351c` and `10194b8c`;
   - canopy's CHANGELOG at `571743db` (`gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/CHANGELOG.md?ref=571743db"`):
     `## [0.6.0]` at `:2171`, `## [0.5.0]` at `:2919`, so `:2909` is `[0.6.0]`'s;
   - the manual at `571743db`: the Candidate Epoch Progress condition spans `:687-688`, so the cite `:686-688`;
   - `_resolve_patch_values` at `571743db` (`src/frontend/components/network_editor_panel.py:457-507`): with one output,
     one-value rows are the right shape (the `len(rows) > 1` branch returns them unchanged and cascor wants
     `(I+H, 1)`), so "rejected wherever the network has more than one output" is the right scope;
   - the handoff's verification commands at `10194b8c`, run (all read-only; the two `Correction 2026-10-19` greps should
     print 1 each, `grep -c '^OPEN   P1 '` 9);
   - the triage on `10194b8c`: 79 / 56 / 1 / 2 / 20; 9 open P1; 11 open P2, unchanged; the five headers unchanged by
     the pass (`git diff c741351c 10194b8c -- <ledger> | grep '^[-+]\*\*F-'` should print nothing).
3. **Cross-file consistency after the pass** (Lane 13-R3B especially): the reach statement, "the first limb decides
   F-CANOPY-065 alone among the findings Phase 11 named", and the alternatives "9/11 or 8/12, the two dissents moving
   it one either way" stated the same way in the ledger's Summary, Matrix effect, F-CANOPY-057's and F-CANOPY-065's
   Status bullets, "The design note's correction", "Still owed", the handoff (Completed, Counts, item 4, item 8), the
   parent's O17 and item 4, and the INDEX; no file still says "only through the audit's line", "10/10 by the broadest
   reading", "dated snapshot of commit themes" outside a quotation of round 1, or "decides F-CANOPY-065 alone" on
   round 1's ground; the round-1 record's amended sentences against what round 1's pass did (its 24 substitutions,
   `util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py`); the round-2 record against the diff hunk by hunk
   (every change listed, nothing listed that the diff does not make); the lane credits against the round-2 report
   file; the dissents unchanged and stated as the lanes stated them.
4. **Gates**: `python3 -B -m unittest tests.test_thread_handoff_archive tests.test_e2e_finding_triage
   tests.test_e2e_finding_triage_nested_bold tests.test_e2e_finding_triage_priority`; the secret and e-mail grep over
   `git diff c741351c 10194b8c` (no `@` outside hunk headers and backticked rule text; no token prefixes).

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13R3A/`
  or `…/lane13R3B/` (create yours). Run Python with `-B`. Do not run any git command that changes state, and run git
  only inside that worktree (the session's guard refuses `git -C` on other repos, `awk` programs, `sed` with shell
  variables and `$(…)` inside commands; use literal paths and plain commands). Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- A claim is wrong only if the artifact says otherwise. A rounding or wording difference that changes no number,
  disposition or action is a NIT.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 13-R3A** (replay and re-derivation, round 3)` or `**Lane 13-R3B** (adversarial on the pass, round 3)`
and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`. Then **REPLAY** (one line per file: byte-identical or not).
Then a **TABLE** (claim | re-derived | result | evidence). Then **FINDINGS**, numbered, each with severity
(BLOCKER / MAJOR / MINOR / NIT), the text quoted, your evidence, the fix, and the line "Changes a number,
disposition or action? yes/no". Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line. Keep it under
14,000 characters.
