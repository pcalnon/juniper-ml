# Lanes 13-R2A and 13-R2B brief — Phase 13 of the canopy E2E ledger, round 2: the corrections only

You are one of two independent validators in round 2, under §4 of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`: "Brief round 2 explicitly
on the corrections, not on the whole artifact: these N changes were made in response to round 1; find what they
broke." You have not seen the other lane's verdict. **Lane 13-R2A** re-derives: replay the pass and re-create every
claim it introduced from the artifacts, the code and the GitHub API. **Lane 13-R2B** is adversarial on the pass: what
did the corrections break, overstate, or leave inconsistent across the files?

## What is under review

Round 1 reviewed local commit `566cb72a` (the Phase 13 draft) with three lanes; their reports are verbatim in
`reports/e2e-canopy-2026-09-02/consensus/2026-10-19_validator_reports_phase13_round1.md`. The correction pass
`util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py` (24 substitutions in the ledger plus the round-1
record; 13 in the new handoff; 2 in the parent handoff, 1 in the INDEX, 1 in the Phase 12 handoff's banner, 1 in the
apply script's header and 2 in the V7 roadmap) was applied to produce local commit **`c741351c`**, now checked out in
worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/federated-stargazing-blanket`
(branch `docs/canopy-e2e-phase13`; the working tree equals the freeze). The diff under review is
`git diff 566cb72a c741351c` run from that worktree: the ledger, the new handoff, the parent handoff, the INDEX, the
Phase 12 handoff, the apply script, the V7 roadmap
(`notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`, new to the
change set in this round), the three round-1 briefs, the round-1 report file and the pass itself. The ledger's
Phase 13 is at `grep -n '^## Phase 13'`; its "Consensus record" now holds the round-1 record, which lists what the pass
changed, what the orchestrator re-derived, what it did not apply, and two items of unresolved dissent.

## Your job

1. **Replay the pass.** From the worktree, `git show 566cb72a:<path>` each of the seven files the pass edits into your
   scratch directory under the same relative paths (the ledger, the new handoff, the parent handoff, the INDEX, the
   Phase 12 handoff, `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`, the V7 roadmap), run
   `python3 -B util/ad-hoc/2026-10-19_phase13_ledger_round1_corrections.py --root <your copy>`, and compare each
   result byte for byte with `git show c741351c:<same path>`. Report whether it replays with no hand edit. Then run it
   with `--check` against the worktree and report that it refuses (the record is already in place).
2. **Re-derive every claim the pass introduced** (the round-1 record's "What round 1 changed" and "Re-derived by the
   orchestrator" lists), each with your own command:
   - the V7 roadmap's §28.1 heading, its g-3 row and its CAN-015 row at `566cb72a` (`git show 566cb72a:<roadmap>`,
     lines 15146-15160 and 5196), and the 2026-05-05 audit's line
     (`notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_ROADMAP-AUDIT.md:112`); that the roadmap's correction at `c741351c`
     states the same shas, times, bases and counts as the design note's and as F-CANOPY-057's History; that it adds
     no markdown link; and the roadmap's last change before this round (`git log --format='%h %ad %s' --date=short -3 -- <roadmap>`);
   - `_parse_float_rows` and `_resolve_patch_values` in canopy `src/frontend/components/network_editor_panel.py` at
     `571743db` (`gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/<path>?ref=571743db"`):
     that newlines and semicolons are row separators (`:437-456`) and that the `len(rows) > 1` branch returns the rows
     unchanged (`:487-494`), so a semicolon- or newline-separated flat list for `output_weights` is sent as one row per
     value; execute the two functions on `"1;2;3;4"` and on `"1,2,3,4"` with a `(1, 1, 2)` topology if you can import
     or copy them, and say what each returns;
   - the manual at `571743db`: `:266` (the env-var line), `:267-269`, `:285`, `:328`, `:686-687`;
   - the matrix: `:807` (M-WORKERS-02, FAIL, no finding id), `:822-824` (M-PARAMETERS-04/-05/-06); the ledger: Phase 5's
     "Still owed" (`grep -n '^### Still owed'`, the one after `## Phase 5 — the post-fix topology re-drive`) names
     F-039, F-037, F-038, F-036 and F-026 only; Phase 11's "three open P2s are already known to be within reach" and
     "F-CANOPY-013 … unsettled"; F-CASCOR-004's header (FIXED by cascor#674); F-CANOPY-056's Severity ("re-rated P1, on
     plan §6.3's rule"; "has not been driven live");
   - the handoff's verification commands at `c741351c`, run (all read-only; `grep -c '^OPEN   P1 '` should print 9 and
     the roadmap grep 1); canopy's CHANGELOG at `571743db`: `#532` at `:534`, `:535` and `:541` only, and the two lead
     entries at `:1436-1437` and `:2909`;
   - the triage on `c741351c`: 79 / 56 / 1 / 2 / 20; 9 open P1; 11 open P2, unchanged by the pass; the five headers
     unchanged by the pass (`git diff 566cb72a c741351c -- <ledger> | grep '^[-+]\*\*F-'` should print nothing).
3. **Cross-file consistency after the pass** (Lane 13-R2B especially): the ruling's alternatives ("9/11, 8/12, or
   10/10 by the broadest reading") stated the same way in the ledger's Summary, Matrix effect, F-CANOPY-057's and
   F-CANOPY-065's Status bullets, "Still owed", the handoff, the parent's O17 and the INDEX; the dissent on
   F-CANOPY-028 and F-CANOPY-067 stated the same way in the record, "The five re-ratings", the Summary and the
   handoff; the F-CANOPY-012 residue stated the same way in the entry's blockquote, "The five re-ratings", item 30,
   "What this phase cannot support" and the handoff; the banner's "item 3's first half" against the Phase 12
   handoff's own item 3; the handoff's "Changed by this session" against the diff (the roadmap added); the apply
   script's new header lines against `util/ad-hoc/README.md:17-31`; nothing the pass changed contradicts an unchanged
   sentence elsewhere in Phase 13 or in the seven entries.
4. **The record itself**: does "What round 1 changed" list every change the diff makes, and nothing the diff does not
   make (compare the diff hunk by hunk); are the lane credits right against the round-1 report file; is "Not applied"
   accurate; is each item of dissent stated as the dissenting lane stated it?
5. **Gates**: `python3 -B -m unittest tests.test_thread_handoff_archive tests.test_e2e_finding_triage
   tests.test_e2e_finding_triage_nested_bold tests.test_e2e_finding_triage_priority`; the secret and e-mail grep over
   `git diff 566cb72a c741351c` (no `@` outside hunk headers; no token prefixes).

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13R2A/`
  or `…/lane13R2B/` (create yours). Run Python with `-B`. Do not run any git command that changes state, and run git
  only inside that worktree (the session's guard refuses `git -C` on other repos, `awk` programs, `sed` with shell
  variables and `$(…)` inside commands; use literal paths and plain commands). Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- A claim is wrong only if the artifact says otherwise. A rounding or wording difference that changes no number,
  disposition or action is a NIT.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 13-R2A** (replay and re-derivation, round 2)` or `**Lane 13-R2B** (adversarial on the pass, round 2)`
and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`. Then **REPLAY** (one line per file: byte-identical or not).
Then a **TABLE** (claim | re-derived | result | evidence). Then **FINDINGS**, numbered, each with severity
(BLOCKER / MAJOR / MINOR / NIT), the text quoted, your evidence, the fix, and the line "Changes a number,
disposition or action? yes/no". Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line. Keep it under
14,000 characters.
