# Lane 13-B brief — Phase 13 of the canopy E2E ledger, round 1: adversarial on the re-ratings

You are Lane 13-B, an independent adversarial validator under §2 (Lane B) of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. You have not seen any other
lane's brief or verdict. Your entry point is the **ledger first**: read Phase 13 and the seven changed entries, then
go to the manual, the sources and the ledger's own precedents to attack them.

## What is under review

The ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` as frozen at local commit `566cb72a`
(worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/federated-stargazing-blanket`, branch
`docs/canopy-e2e-phase13`; the working tree equals the freeze). The diff against `main` (`ad6013f4`) is
`git diff ad6013f4 566cb72a` run from that worktree. In the ledger it adds **Phase 13** at the end
(`grep -n '^## Phase 13'`), re-rates **F-CANOPY-012, -013, -018, -028 and -032** from P2 to P1 in their headers
(`grep -n 'P1 since 2026-10-19'`) with a RE-RATED blockquote under each, and adds a dated Status bullet to
**F-CANOPY-057** and **F-CANOPY-065**. Read those seven entries in full, Phase 11's "Matrix effect and counts" and
its item 26 (`grep -n '^## Phase 11'`), Phase 12's "Still owed" (`grep -n '^## Phase 12'`), Phase 4
(`grep -n '^## Phase 4'`), and the precedents the phase invokes: F-CANOPY-056's and F-CANOPY-057's Severity bullets,
F-CANOPY-064's Severity bullet, and plan §6.3 (`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`).
The same commit corrects the CAN-015g/h design note
(`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md`) and adds a new handoff
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`).

Phase 13 moves the open P1 count from 4 to 9 on a reading of canopy's `docs/USER_MANUAL.md` at canopy `main`
`571743db` (fetch it: `gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/docs/USER_MANUAL.md?ref=571743db"`).
It ran nothing live. It is a convenient result for an arc whose exit criterion counts P1s only if you believe the
opposite, so treat it as the top-right cell of §3 of the procedure and attack it.

## Your job

Argue against the ledger. In particular:

1. **Each re-rating on its own.** For F-CANOPY-012, -013, -018, -028 and -032: does the quoted manual sentence
   state the behaviour the finding measured to be otherwise, or only name a surface? Is the measurement the entry
   records the one the blockquote sets against the sentence? Is the F-CANOPY-056 / F-CANOPY-057 precedent applied
   the way those entries applied it (read their Severity bullets)? Which of the five would you rate P2, and why?
   F-CANOPY-028's counter-reading is written into the phase; is the phase's resolution of it defensible, and is it
   the only re-rating with a counter-reading? For F-CANOPY-032, is it sound to re-rate P1 a finding whose mechanism
   does not reproduce from source and whose one sound arm has not been re-driven since segment 16, or should the
   re-drive come first? For the four fixed in code, is rating "on the behaviour it measured" the ledger's practice
   (find a precedent either way), and does the header wording ("code change canopy#NNN … its live re-drive owed")
   keep the triage honest?
2. **"Reached" and "not reached".** Is the definition under "The instrument" applied evenly? Take the ten
   not-reached findings and try to reach each from the manual: F-CANOPY-049 against § Status Indicators,
   § Update Intervals, Troubleshooting 1 and 5 and § WebSocket Real-Time Updates; F-CANOPY-066 against the
   Network Information Panel and the recurrence text in § Visualization Tabs and § Training Metrics; F-CANOPY-060
   against § Dataset View and § "A wider dataset needs Start fresh"; F-CANOPY-051, -001, -033, -034, -063; and
   F-CANOPY-067 (is "unchanged" right when the manual documents the plots, given the entry's own condition?).
3. **The owner's question** (O17). The phase says the first limb now decides F-CANOPY-065 alone. Check: does the
   ruling still reach F-CANOPY-057 through `notes/development/REPLAY_V2_FAQ.md` or another plan the phase did not
   read? Is correcting the design note, and then saying the note no longer promises the stream, legitimate, or
   does it settle a rating by editing the evidence? (Item 26 required the correction whatever the ruling; say
   whether that answers the objection.) Could the ruling reach any other open finding through the CHANGELOG, which
   the phase explicitly did not sweep?
4. **The counts and the exit criterion**: 79 / 56 / 1 / 2 / 20; 9 open P1; 11 open P2; "9/11 or 8/12"; "8/12 or
   7/13" under F-CANOPY-028's other reading. Check with `python3 -B util/ad-hoc/e2e_finding_triage.py` and by
   hand. Does "every release from 0.7.0 carries the fixes" hold (compare v0.7.0 with the three merge shas)?
5. **Item 30**: is it specified so that it can be done and can fail? Are the legs right (a writable cascor for the
   Network Editor rows; a demo leg for C2.9-05 and M-PARAMETERS; a stoppable cascor for M-WORKERS-02)? Is the
   demo-leg expectation for F-CANOPY-018 and F-CANOPY-028 justified by the manual or by source, or assumed? Is
   M-METRICS-03 F-CANOPY-026's row (check the matrix) and is F-CANOPY-026 FIXED in the triage? Did any numbered
   Still-owed item since Phase 9 carry the Phase 4 rows after all (grep the row ids)?
6. **Facts stated that were inferred or copied.** Find each place Phase 13 states as fact something it did not
   derive from a file or an API answer, including the CHANGELOG's silence on canopy#532/#533/#535 and "the
   lines have moved, not changed" for F-CANOPY-064 (compare the sentences at `571743db` with what F-CANOPY-064
   quotes).
7. **"What this phase cannot support"**: is the list complete? What else can a reader not conclude from this phase
   that the phase's wording invites?
8. **The handoff**: do its "Remaining" items follow from the ledger; are the verification commands right (run
   them, except anything that touches a service); does the SUPERSEDED banner on the Phase 12 handoff state that
   file's items correctly; do the parent's item 4 and O17 edits and the INDEX's P2 row say the same thing the
   ledger says?

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13B/`
  (create it). Run Python with `-B`. Do not run any git command that changes state, and run git only inside that
  worktree (the session's guard refuses `git -C` on other repos, `awk` programs, `sed` with shell variables and
  `$(…)` inside commands; use literal paths and plain commands). Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- The ledger's style: a claim is wrong only if the artifact says otherwise. A rounding or wording difference that
  changes no number, disposition or action is a NIT. A rating you would set differently is a finding only if you
  can say which sentence of the manual or which measurement the phase misread; otherwise record it as dissent.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 13-B** (adversarial on the re-ratings, round 1)` and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`.
Then a **TABLE** of the claims attacked (claim | attack | result STANDS/FALLS/DISSENT | evidence). Then
**FINDINGS**, numbered, each with severity (BLOCKER / MAJOR / MINOR / NIT), the ledger text quoted, your evidence,
the fix, and the line "Changes a number, disposition or action? yes/no". Then **DISSENT** you could not resolve.
Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line. Keep it under 14,000 characters.
