# Lane 13-A brief — Phase 13 of the canopy E2E ledger, round 1: manual-first re-derivation

You are Lane 13-A, an independent validator under §2 (Lane A) of
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. You have not seen any other
lane's brief or verdict. Your entry point is **canopy's manual and the sources first**, the ledger second: form your
own answer for every open finding before you read what the ledger decided.

## What is under review

The ledger `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` as frozen at local commit `566cb72a`
(worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/federated-stargazing-blanket`, branch
`docs/canopy-e2e-phase13`; the working tree equals the freeze). The diff against `main` (`ad6013f4`) is
`git diff ad6013f4 566cb72a` run from that worktree. In the ledger it adds **Phase 13** at the end
(`grep -n '^## Phase 13'`), changes the headers of **F-CANOPY-012, -013, -018, -028 and -032** from P2 to P1
(`grep -n 'P1 since 2026-10-19'`) and adds a RE-RATED blockquote under each, and adds a dated Status bullet to
**F-CANOPY-057** and **F-CANOPY-065**. The same commit corrects
`notes/JUNIPER_2026-05-04_JUNIPER-ECOSYSTEM_PHASE-6E-DEFERRED-CAN-015GH-DESIGN.md` (g-3), adds a new handoff
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`,
edits two other handoffs and the INDEX, and adds the apply script `util/ad-hoc/2026-10-19_phase13_manual_sweep_apply.py`.

Phase 13 is item 26's first step (Phase 11's "Still owed"): every open finding checked against canopy's manual under
plan §6.3's rule ("P1 (breaks a documented behaviour)", `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:357-360`).
It was written on a host with no live service: every claim in it is a reading of files, source and the GitHub API.

## Your job

**Step 1, before reading Phase 13.** Fetch canopy's manual at the commit the phase used:
`gh api -H "Accept: application/vnd.github.raw" "repos/pcalnon/juniper-canopy/contents/docs/USER_MANUAL.md?ref=571743db"`.
Get the 20 open findings with `python3 -B util/ad-hoc/e2e_finding_triage.py --open-only` on the frozen ledger (their
ids are the same before and after the phase), read each entry's header and the measurement it records
(`grep -n '^\*\*F-CANOPY-0NN '`), and decide for each, from the manual alone, whether the manual states as the
product's behaviour the thing the finding measured to be otherwise. Write your 20 answers down with the manual's line
numbers before step 2.

**Step 2.** Read Phase 13 (its table "The sweep, finding by finding", "The five re-ratings", "Matrix effect and
counts", "Still owed", and the five RE-RATED blockquotes) and compare with your answers. Report every disagreement.

**Step 3.** Re-derive every source and GitHub fact the phase rests on, each with your own command:

1. The manual's quoted sentences and line numbers at `571743db`: `:493-501` (Patch Weights), `:510` (workflow step 6),
   `:266-268` (Apply enables only when a value differs), `:754-755` (pin set survives a reload), `:732` (Degradation
   alert), `:311`, `:316`, `:338` (Training Metrics), `:820-822` and `:714-715` (no weight sample reaches the page),
   `:266-269`, `:155-171`, `:173-176`, `:1144`, `:225-244`, `:121`, `:777`. The term scan the phase describes under
   "The instrument" (run it yourself, case-insensitively, and say whether any hit the phase does not account for).
2. canopy PRs 532, 533 and 535: merge times, merge shas, titles (`gh pr view N --repo pcalnon/juniper-canopy --json
   number,state,mergedAt,mergeCommit,title`); whether each merge sha is an ancestor of the v0.7.0 tag
   (`gh api repos/pcalnon/juniper-canopy/compare/v0.7.0...<sha> --jq '{status,ahead_by,behind_by}'`: the phase says
   `behind`, 0 ahead); the v0.7.0 Release's publish time.
3. canopy's CHANGELOG at `571743db`: that no line names `#533` or `#535` and the only `#532` is in the 0.9.0 entry for
   F-CANOPY-059; that none of F-CANOPY-001/-012/-013/-018/-028/-034 is named; the 0.6.0 toast entry at `:2360-2365`
   ("declined with the reason"); the release headings' lines (`[0.9.0]` `:12`, `[0.7.0]` `:1700`, `[0.6.0]` `:2171`).
4. canopy source at `571743db` (`gh api … contents/<path>?ref=571743db` with the raw Accept header):
   `src/frontend/components/network_editor_panel.py`: `_resolve_patch_values` at `:457`, its rows / flat idioms,
   `_envelope_payload` at `:563` and its two call sites `:731` and `:828`; `src/backend/cascor_service_adapter.py`:
   `_to_dashboard_metric` at `:1960-1991` with no `weights` and no `kind` key.
5. cascor at `main` `4c26919f` (`gh api repos/pcalnon/juniper-cascor/commits/main`): `src/api/lifecycle/manager.py`
   `_emit_frame` at `:1260-1297` (the keys it emits; no `weights`), `weights_at` at `:1244` with no caller in the
   file; cascor PRs 187, 189, 190 (bases, merge times, shas); `gh api repos/pcalnon/juniper-cascor/compare/main...dbc25277`
   (the phase says diverged, 3 ahead, 537 behind).
6. The triage on the frozen ledger: 79 / 56 / 1 / 2 / 20; 9 open P1 (which nine); 11 open P2. And the triage's own
   rules on the five new headers (`util/ad-hoc/e2e_finding_triage.py:39`, `:58-76`): the first severity token in
   each header body is `P1`, and no FIXED / HEALED / ACCEPTED / WITHDRAWN word sits in the last 170 characters.
7. The matrix rows Phase 13 names (`notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`):
   C2.9-05, M-WORKERS-02, M-NETWORK-EDITOR-09/-13/-17, M-PARAMETERS-04/-05/-06, C2.1-01/02, M-METRICS-03, their
   status columns and which finding each names.
8. The ledger's own earlier text the phase relies on: Phase 4's "Still owed (unchanged, plus)" (the rows named),
   Phase 4's disposition table (which PR fixed which finding; F-CANOPY-032 "NOT fixed"), the F-CANOPY-032 entry's
   correction about its two arms, Phase 11's "Matrix effect and counts" (the four findings within the first limb's
   reach), Phase 12's item 26 wording, and that no numbered Still-owed item since Phase 9 carries the Phase 4 rows
   (grep the row ids).

## Rules

- Do not modify any tracked file in the worktree. Write your own scripts and outputs under
  `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/438B5B69-ACCF-4C62-BE45-EEFFF048856D/scratchpad/lane13A/`
  (create it). Run Python with `-B`. Do not run any git command that changes state, and run git only inside that
  worktree (the session's guard refuses `git -C` on other repos, `awk` programs, `sed` with shell variables and
  `$(…)` inside commands; use literal paths and plain commands). Do not start or touch any service.
- Never print secrets, environment values, tokens or any e-mail address. Use `git log --format='%h %s'`, never a
  format that prints authors. Do not read `.env*` files.
- The ledger's style: a claim is wrong only if the artifact says otherwise. A rounding or wording difference that
  changes no number, disposition or action is a NIT.

## Report format (your final message, which is archived verbatim)

Start with `**Lane 13-A** (manual-first re-derivation, round 1)` and `**VERDICT: SOUND | SOUND-WITH-FIXES | REFUTED**`.
Then **YOUR 20 ANSWERS** (finding | manual line(s) | reached? | your rating | the ledger's | agree?). Then a **TABLE**
of the facts re-derived (claim | re-derived | result MATCH/MISMATCH/holds | evidence). Then **FINDINGS**, numbered,
each with severity (BLOCKER / MAJOR / MINOR / NIT), the ledger text quoted, your evidence, the fix, and the line
"Changes a number, disposition or action? yes/no". Then **WHAT YOU COULD NOT CHECK**. Then **SECRETS/PII:** one line.
Keep it under 14,000 characters.
