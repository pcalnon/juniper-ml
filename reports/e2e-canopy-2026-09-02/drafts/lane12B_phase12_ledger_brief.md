# Lane 12-B brief — Phase 12 of the canopy E2E ledger, round 1: adversarial on the dispositions

You are Lane 12-B, an independent adversarial validator under §2 (Lane B) of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. You have not seen any other
lane's brief or verdict. Your entry point is the **ledger first**: read Phase 12 and the three changed entries, then
go to the evidence to attack them.

## What is under review

The ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` as frozen at local commit `c626e847`
(worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/squishy-growing-breeze`, branch
`docs/canopy-e2e-phase12`). The diff against `main` (`0e144c3c`) is `git diff 0e144c3c c626e847 -- notes/` run from
that worktree. It adds **Phase 12** at the end (`grep -n '^## Phase 12'`) and changes the headers and first Status
bullets of **F-CANOPY-055**, **F-CANOPY-058** and **F-CANOPY-068** (`grep -n '^\*\*F-CANOPY-0\(55\|58\|68\) '`).
Read those three entries in full, and Phase 11 (`grep -n '^## Phase 11'`), whose items 0, 24, 25 and 26 Phase 12
closes or carries. Phase 9's item 5 and Phase 10's item 18 are also touched.

Phase 12 marks the three findings **FIXED** by canopy#731 and says each is "verified live on the branch at
`2689a207`", on evidence made on 2026-10-08 by the session that wrote the fix
(`reports/e2e-canopy-2026-09-02/pacer-live/`, `…/pacer-renderer-check/`, and the review record
`…/consensus/2026-10-08_validator_reports_canopy731_pacer_rounds1-3.md`). The phase itself ran nothing live.

## Your job

Argue against the ledger. In particular:

1. **Should FIXED stand for each of the three?** The triage counts FIXED from the header. Phase 12 lists the limits
   of "VERIFIED LIVE" (no mid-request Apply release, no injected failure, no training run, nothing on the merged
   tree or the 0.9.0 wheel, one host, dash 4.2.0 only, the allow arm not driven, the minutes not reachable). Is that
   list complete? Does any limit undercut a FIXED, by the ledger's own precedents (how Phases 2, 5, 6 and 10 marked
   fixes FIXED, HEALED or "verified live"; F-CANOPY-059's FIXED on a throwaway stack; F-CANOPY-035's
   FIXED-FOR-ONE-VICTIM)? Would any precedent require "FIXED IN CODE" without "verified live", or an owner sign-off?
2. **Is anything in Phase 12 stated as observed that was inferred, synthetic, or copied from the PR body?** The PR
   body and the CHANGELOG are the fix author's claims; the ledger must not launder them as the ledger's own
   observations. Find each place where Phase 12 relies on the PR body or the handoff
   (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_canopy-pacer-731-landed-phase12-owed.md`) rather
   than on an artifact, and say whether it is labelled as such.
3. **The counts and ratings logic** (§ "Matrix effect and counts"): 79 / 56 / 1 / 2 / 20; 4 P1; 16 P2; the owner's
   two-limbed question; "the second limb moves no count now"; O17. Check with `python3 -B util/ad-hoc/e2e_finding_triage.py`.
4. **The dropped reader change** (item 24's push-order comparison, § Instruments): is the reason to drop it sound?
5. **Items 27, 28 and 29**, and the closures of items 0, 24, Phase 9's item 5 and the correction to item 18: is
   each closure earned by the evidence, and is each new item specified so that it can be done and can fail?
6. **The cost** (§ Summary and "The design, as merged"): is "at least 30 s, at most 120 s" right, by the code at
   `25c5c887`? What else did the pacer change that a user could notice, which Phase 12 does not say?
7. **The "two paths still re-request a feeder"** and the modulus change: are they findings in waiting, and should
   the ledger file them, decline them with a reason, or leave them as recorded?
8. **The Status bullets' wording** in the three entries, against the entries' own earlier text (F-055's "Fix
   direction", F-058's "In production", "The clamp defeat" and "NOT yet observed", F-068's "Fix direction").

Read canopy source only through `gh api repos/pcalnon/juniper-canopy/contents/<path>?ref=<sha> -H "Accept: application/vnd.github.raw"`
and `gh pr diff 731 --repo pcalnon/juniper-canopy`; use `gh pr view`, `gh release view` and
`curl -s https://pypi.org/pypi/juniper-canopy/json` for the rest.

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/D227803E-A1C2-4957-9A7C-824C3F8B44BD/scratchpad/lane12B/`
  (create it). Run Python with `-B`. Do not run any git command that changes state. Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- A finding against the ledger must quote the ledger and cite the artifact or code that contradicts it. "The
  evidence is thin" is a finding only where the ledger claims more than the evidence; if the ledger already states the
  limit, say so and move on.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 12-B** (adversarial on the dispositions, round 1)` and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`.
Then **FINDINGS**, numbered, most severe first, each with severity (BLOCKER / MAJOR / MINOR / NIT), the ledger text
quoted, your evidence, the fix, and the line "Changes a number, disposition or action? yes/no". Then **TRIED AND COULD
NOT REFUTE** (a list). Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line. Keep it under 14,000 characters.
