# Round 2 of the Phase 14 review — the corrections, and what they broke

Round 2 of the Phase 14 review (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
§4: "brief round 2 explicitly on the corrections, not on the whole artifact"). Review the worktree HEAD named in
your message, read-only; scratch under your lane's directory. Do not start any service.

## What changed since the commit you reviewed (`a77c1c54`)

The pass `util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py` (read its docstring: it lists every change and
the lane that raised it) was applied on top of `a77c1c54`. The three round-1 reports are archived verbatim in
`reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round1.md`. The round-1 consensus
record was written into Phase 14's "Consensus record" section. The 20 screenshots were taken out of the commit (LFS
pointers the API landing cannot push; they stay on turing) and `transcripts/` was force-added.

`git diff a77c1c54 HEAD --stat` and `git diff a77c1c54 HEAD -- <file>` (from inside the worktree) show every line.

## Find what the corrections broke

1. **Each substitution against its reason.** For every change the docstring lists: does the new text say what the
   evidence says (the records under `reports/e2e-canopy-2026-09-02/item30-turing/`, the transcripts, the source at
   canopy `571743db` in the E2 tree, the dash wheels), and only that? Did the fix over-correct (for instance, is
   "1 of 8 on the record" now stated consistently in the header, the blockquote, the Summary, "cannot support", the
   matrix cell, the handoff title, Completed and Traps, the parent's pointer and the INDEX row — count the places;
   any "2 of 8" left anywhere is a defect)?
2. **The consensus record.** Does it meet §7 of the procedure (instrument, sample size, lanes and entry points,
   iterations and what the last changed, unresolved dissent, what the evidence cannot support)? Does it describe
   each lane's finding as the archived report states it, and credit it to the right lane?
3. **The handoff's verification command** now reads
   `python3 -B util/ad-hoc/e2e_finding_triage.py | grep -c -E '^FIXED +P[012] +F-CANOPY-0(01|12|13|18|32) '` — run it;
   it must print 5. Run every other verification command in the handoff again.
4. **Replay.** `python3 -I util/ad-hoc/2026-10-20_phase14_item30_apply.py --root <copy of origin/main>` followed by
   `python3 -I util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py --root <the same copy>` must reproduce the
   worktree's six files byte for byte (the Lane 14-C recipe: `git show origin/main:<path> > <copy>/<path>`).
5. **Anything a round-1 defect asked for that the pass did not do**, or did differently; name it.
6. **New errors.** The fix pass is the least trustworthy part of any document: read the new sentences for claims
   the records do not carry (Lane 14-A's figures are in its archived report; the early#2 timings are in
   `demo_leg_8062_dash441.json` `f028.arms.early#2`).

## Report (your final message, verbatim is what gets archived)

Verdict first: SOUND / SOUND-WITH-FIXES / UNSOUND for the corrected draft. Then each defect, numbered, MAJOR (changes
a number, a disposition, a rating, an action, or a mechanism claim) or MINOR, with the exact text and the evidence.
Then what you re-checked and found right. Say explicitly whether anything in this round changes a number, a
disposition or an action: that is the termination test.
