# Handoff: flood-4 session 6 — four more landed, rulings 19–29 given; the weekly Fable limit killed five agents mid-task

**Date**: 2026-11-12 local (written 2026-11-13 01:47Z UTC)

**Arc**: the Cursor flood-4 disposition, session 6. It started as `resilient-tinkering-thimble` and ran in `humming-stargazing-papert` via EnterWorktree. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session5-seven-more-landed-queue-and-decisions-pending.md` (session 5's handoff; uncommitted in this worktree).

**Host**: the Linux host.

**Why the session stopped**: the account's **weekly Fable limit** was hit between 01:25Z and 01:44Z on 2026-11-13. The API's words: "You've hit your Fable limit · resets Nov 18, 9pm (America/Chicago)", which is 2026-11-19 03:00Z. Five background agents died mid-task (listed under Goal). Nothing is blocked by a decision except the D14 question below.

**The running log is the detail**: `tmp/flood4/session6/STATE_S6.txt` in the orchestrator worktree has one dated entry per event, including the owner's rulings verbatim. Read it before acting.

**If session 6 itself is still open when the limit lifts**, it can resume its five agents where they stopped with SendMessage (their work is saved), which a new session cannot: data carrier `a13021382be951da5`, ml-tests round 2 `abd21f5554a19c89f`, ml-docs `a1e6389f6c2d68753`, guard PR `a949c0b9e199389bf`, ml-propose quick check `a80ef4dd2caed2c10`. That is cheaper than relaunching, above all for ml-tests and ml-docs, which were nearly done. Closing session 6 gives that up.

---

## Git status

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert`. HEAD is `734aab58`, deliberately not fast-forwarded. `origin/main` was `f9582a74` at 01:44Z.
- **Uncommitted there** (nothing staged): this handoff and session 5's; session 5's and the agents' `util/ad-hoc/2026-11-1[12]_flood4r2_*` helpers; session 6's three helpers `util/ad-hoc/2026-11-12_flood4r2_s6_{seqsafety_probe,freeze_carrier,stage_texts}.py` and its agents' `2026-11-12_flood4r2_*` helpers. `tmp/` is ignored; session 6's evidence is `tmp/flood4/session6/` (`land/<item>/` per landing, `briefs/`, `prev_prompts/`, `prev_messages/`).
- **The primary checkout** is on the owner's branch. Do not touch it.

---

## Landed in session 6 (2026-11-13 UTC; each signed, frozen, probed for sequence safety, scanned with a planted-token control, merged by `util/safe_merge.py`)

| Item | PR | Squash | Merged | Drafts closed |
|---|---|---|---|---|
| ml-code (guard 1.3.0, launchers, fleet-triage) | juniper-ml#2554 | `b6b843b6` | 00:34:33Z | #2485 #2493 #2502 #2504 #2505 #2508 #2513 |
| Ruling 10 pilot: gitleaks PR-commit scan | juniper-data-client#260 | `b45aafbb` | 00:37:53Z | — |
| Ruling 17: cascor stop-then-start | juniper-cascor#756 | `44b60af2` | 00:40:45Z | — |
| N-2: service-core stop-then-start (409) | juniper-ml#2557 | `f9582a74` | 01:42:57Z | — |

Also: juniper-ml#2552 (ml-code's first cut) was **closed** and re-cut as #2554; issue **juniper-data#536** was opened (ruling 29). Ruling 11 is four of four done. Ruling 17 is four of four done. Ruling 10 is two of eight repos done.

---

## The owner's rulings of 2026-11-12 (AskUserQuestion, labels verbatim; provisional numbers 19–29, in `STATE_S6.txt`)

- Opening message: "merge approval granted for this work arc". It is per session and does not carry.
- 19 (D7) N-2's design: "Accept the 409 (Recommended)". 20 (D1) guard bypasses F3/F4: "In ruling 18's PR (Recommended)". 21 (D17) their exact spellings in public docs: "Keep them (Recommended)". 22 (D15) cascor's design: "Keep fence-and-queue (Recommended)".
- 23 service-core follow-ups, all three chosen: "WebSocket gaps beside N-4", "Lifecycle races beside N-2", "Match cascor's resume answers", with the note "we should verify that follow up 3 is the right apprach".
- 24 (D8): "In the ml-tests carrier (Recommended)". 25 (D2): "A follow-up PR now (Recommended)". 26 (D5+D9): "Port to all five + doc line (Recommended)". 27 (D6): "A follow-up PR (Recommended)". 28 (D12): "A follow-up PR (Recommended)". 29 (D3): "Open one juniper-data issue (Recommended)" (done).

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-12_flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead.md (in the
humming-stargazing-papert worktree, uncommitted). EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/
.claude/worktrees/humming-stargazing-papert). Run the Verification block, then read the tail of
tmp/flood4/session6/STATE_S6.txt.

FIRST:
(1) Ask the owner for THIS session's merge approval (a handoff cannot carry it).
(2) Confirm the weekly Fable limit has reset (2026-11-19 03:00Z) or that the owner changed model or bought credits.
    Six agents plus five other sessions exhausted it in about two hours: stage two or three agents, not six.
(3) Ask the owner the D14 question (below). Build nothing for it before the answer.
(4) Session 6's agents cannot be messaged from a new session. For each dead one: VERIFY ITS TREE FIRST (a killed
    mutation run once left a mutant in a carrier), read what it left, then relaunch a FRESH agent with its brief in
    tmp/flood4/session6/briefs/ plus tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt, pointing at the partial work as leads.
(5) Read this file's section "A side effect of juniper-cascor#756": since that merge a rare Pause / Stop / Start
    overlap leaves the NEW run frozen at its first checkpoint (STARTED, resume refused; pause then resume frees it).
    It is documented only in #756's description. Whether cascor's documents or pause_training change is not ruled.

1. juniper-data code carrier (Retry-After round-up). Tree: worktrees/juniper-data--land--flood4r2-stage3-data-code--
   20261111-1851--399eeffb; deliverables tmp/flood4/session5/data-landing/ (stage3/, stage3/s6/). Brief A. State: the
   test file holds 47 tests (sha256 222867d1...); security.py 7b6c3dec... and middleware.py 99db44a3... unchanged.
   A COMPLETE, recorded 39-test state is in stage3/s6/state39/. For the 47-test state the lanes, the full suite, the
   mutants (stage3/s6/mut-after-47), prescreen, shapes and pre-commit exist; NOT done: the count of the 47 that fail
   on main (c68e6b4c), and the final manifest, texts and REPORT. Check the control tree juniper-data--land--flood4r2-
   s6-control--20261112-1724--c68e6b4c is clean. Then land (steps in item 9). MESSAGE the R-OBS-SC-2 arc's session
   with the PR number at open and at merge: its next PR waits for this fix on main. That session asked (01:49Z) to
   be addressed as "foamy-squishing-floyd-3d" while ListAgents lists it (it also appears as
   "r-obs-sc-2-follow-ups-five-prs-validated-opening-next"; it knows the PR is late). If it is gone, the newest
   HANDOFF_*r-obs-sc-2-follow-ups* file under prompts/thread-handoff_automated-prompts/ on juniper-ml main names the
   live session. It will open NO juniper-data PR of its own for this fix.
2. ml-propose then ml-tests, in ONE sitting. ml-propose round 3b is BUILT: .claude/worktrees/agent-a211deee35ec85ad3,
   tmp/flood4r2/ml-propose/r3b/ (base 15b5d9bb; REPORT.txt gives the landing command). Its quick check died (brief K;
   partial output tmp/flood4r2-val/ml-propose-r3b-quick-s6/: it had verified the carrier 22/22 and made the landing
   worktree worktrees/juniper-ml--val--flood4r2-ml-propose-r3b--20261112-1920--26ea0ecb, nothing more). ml-tests
   round 2 (brief H; .claude/worktrees/agent-abd21f5554a19c89f, tmp/flood4r2/ml-tests/r2/; round 1 is
   agent-a67685d30bfa19727) died FAR ALONG, by its PROGRESS.txt of 01:19Z: rebuilt on 26ea0ecb, registrations
   re-derived (254 suites), F6 applied, the eight guard suites shown to run under CPython 3.9, 40 of 40 mutants
   killed, CI's list run on bytes of 01:10Z. NOT written: manifest, texts, REPORT. Both carriers now land on a main
   that holds N-2 (REFERENCE 0.6.69): re-derive. After round 2: two lenses, a fix-up, then both landings (fill
   <ML-PROPOSE-PR> in ml-tests' texts).
3. ml-docs. Its builder (brief I; .claude/worktrees/agent-a1e6389f6c2d68753, tmp/flood4r2/ml-docs/) died at its
   last screens: all six carrier files were edited (.claude/agents/fleet-supervisor.md, CHANGELOG.md, the cheatsheet,
   DOCUMENTATION_OVERVIEW, QUICK_START, REFERENCE), doc links and pre-commit passed. NOT written: manifest, texts,
   REPORT. Its stamps (REFERENCE 0.6.69, cheatsheet 1.0.68) COLLIDE with N-2's, which landed after: re-derive to
   main + 1. Finish, validate, land; then close #2494 and the docs drafts, and the triage's NONE group.
4. Ruling 18's guard PR, with F3/F4 and ruling 16's false refusals (brief J; .claude/worktrees/agent-a949c0b9e199389bf,
   tmp/flood4-fix/r18-guard/). Its builder had only finished READING (PROGRESS.txt 01:13Z): no DESIGN.md, no code.
   Relaunch from the brief. Then two lenses.
5. juniper-data's unrun tests (ruling 25) are BUILT and unvalidated: worktrees/juniper-data--test--run-the-unrun-
   tests--20261112-1815--c68e6b4c, tmp/flood4-fix/d2-unrun-tests/ (16 paths; 137 tests into lanes; tests/api/ moved to
   tests/unit/). One validator, then land AFTER item 1 (three-way REFERENCE and CHANGELOG; stamp 0.4.9).
6. Ruling 10's six other ports. tmp/flood4/session5/BRIEF_R10_PORT.txt has a session-6 section (lines 123-171): start
   from the pilot's merged test file, pin the blocking wiring, the live-run reading list.
7. New work from the rulings, none built: two service-core PRs (WebSocket gaps beside N-4; lifecycle races beside
   N-2) and the third after D14; five lockfile-print ports plus one canopy docs PR; canopy :8100; canopy's relay
   test. Then round 3's #2404 and #2406.
8. Ruling 7 cleanup, the record-update PR (rulings 15-29, sessions 4-6) and the provenance commit, as session 4's
   handoff describes. Session 6 added worktrees: juniper-ml--land--flood4r2-ml-code-s6check--*, juniper-cascor--val--
   flood4r2-d14-resume*, juniper-data--land--flood4r2-s6-control--*, juniper-data--test--run-the-unrun-tests--* (a
   carrier: keep), .claude/worktrees/agent-{a211deee35ec85ad3,a29e21f88df874394,abd21f5554a19c89f,a1e6389f6c2d68753,
   a949c0b9e199389bf,a80ef4dd2caed2c10}. Never use util/remove_stale_worktrees.bash. curious-plotting-hummingbird is
   DO NOT SWEEP.
9. Landing steps, with session 6's helpers in util/ad-hoc/ (each prints what to read):
   - 2026-11-12_flood4r2_s6_freeze_carrier.py --carrier <tree> --base <sha> --manifest <f> --out <land dir>
     (add --three-way / --prebuilt as needed; fetch first);
   - 2026-11-12_flood4r2_s6_stage_texts.py (title, body + footer, commit body + trailer block; --replace-body for
     a sentence a ruling or a merge made stale; --trailer for a waiver);
   - 2026-11-12_flood4r2_s6_seqsafety_probe.py with the repo's own scopes (STATE_S6.txt lists them);
   - 2026-11-09_flood4r2_land_gitleaks.py on the snapshot (--baseline <freeze>/main) and on the texts;
   - 2026-11-09_flood4r2_land_open_pr.py (--dry-run first), then util/safe_merge.py --execute --timeout 3300 in the
     background; read its MERGED line; close drafts with 2026-11-07_flood4_close_carried.py (READ the dry run).
10. Archive the next handoff.
```

---

## The open question for the owner (D14, the third service-core follow-up)

The owner asked to verify the approach before building. The check is done: `tmp/flood4r2-val/d14-resume-answers-s6/REPORT.txt`, section "FOR THE OWNER". It was presented in session 6's messages and is **unanswered**.

- Since juniper-cascor#754 the two services answer two malformed resume frames differently (a negative `last_seq`; a `data` that is not an object). No document or gate requires them to match, no in-tree client sends a resume frame, and they differ on 131 of 240 cases, not only those two.
- Options: (a) service-core follows cascor — on the two frames alone 88 cases still differ; with all four of cascor's cursor rules none do (8 lines); (b) cascor goes back; (c) leave both and document; (d) (a) plus a shared table both repositories test against.
- Recommended: (a) with all four rules, before service-core 0.8.0. To decide with it: refusing a `last_seq` above the newest message reverses a sentence `docs/REFERENCE.md` states on purpose; a negative could be refused instead of read as 0; is cascor still to move onto the shared copy.

Also for the owner: reinstall the guard (`bash util/install_claude_agent_guard.bash --dry-run`, then `--apply`, from a checkout at `b6b843b6` or later); the unrun-tests builder's benchmark-lane options A–E (`tmp/flood4-fix/d2-unrun-tests/` in its worktree); a proposed, unruled back-port of the pilot's blocking-wiring pins to juniper-data's own test.

## A side effect of juniper-cascor#756 that is on `main` now (carried at the owner's request, 2026-11-13)

juniper-cascor#756 (merged as `44b60af2`) makes a stopped training run really stop and queues the next run behind it; the owner ruled to keep that design. Its builder measured one side effect of it (probe g of `util/ad-hoc/2026-11-12_flood4r2_r17-cascor_adjacent_probes.py`):

- **When**: a `pause` passes its state check just before a `stop` and a `start` land. `pause_training` takes no lock, so the pause closes the pause gate after the start reopened it. It takes three overlapping requests.
- **What it does since #756**: the stopped fit stops, and the closed gate holds the **new** run at its first checkpoint. `state_machine.status` reads `STARTED`, the run never moves, and `resume` is refused.
- **The way out**: send `pause`, then `resume` (measured). By reading the pause loop, a `stop` ends it too (not measured).
- **Before #756** the same overlap held the OLD fit instead, which the start had released from its stop, with the new run queued behind it, until a stop. The cause, the unlocked check-then-act in `pause_training`, is older than #756 and was not changed by it; only the run that gets held differs.
- **Where it is written**: only in #756's description, section "What this does not close", and in the builder's records at `worktrees/juniper-cascor--fix--stop-then-start-race--20261109-0944--96cf891b/tmp/flood4-fix/r17-cascor-stop-start/` (`manifest.json` open question 4; `dispositions.json`, code-lens finding F7, declined as "none in this PR"). It is **not** in juniper-cascor's documents: the "Known, not fixed" list in `docs/api/API_SCHEMAS.md` covers a stopped fit that is still running, not this.
- **Not decided**: whether juniper-cascor's documents get a line for it, and whether `pause_training`'s check-then-act gets a fix. Neither is ruled, and no text promises either: ask the owner before building one.
- **Remember it** if a run looks started but never moves after a quick Pause, Stop and Start, in juniper-canopy or in an E2E run against a cascor that holds #756.

**Orchestrator decisions taken in session 6** (the owner may overrule):
- ml-code landed before N-2. Three sentences that rulings made false were corrected as text before landing (ml-code's "not decided" twice; cascor's "no ruling names the design" five times; the pilot's "No issue tracks that gap").
- The four test symbols ml-code changes on purpose were waived with an `Allow-Symbol-Loss` trailer.
- The pilot's mutation check grew from 48 to 61 mutations; cascor's PR has eight paths, not six; N-2 has twenty files, not eighteen.

## Traps (new this session)

- **Closing a session kills its agents, and a killed mutation run can leave a MUTANT in a carrier.** Session 5's close left `reset_in = 1` in the data carrier's `security.py`. Compare every carrier file with its recorded sha256 before building on it.
- **CI's Sequence Safety screen reads waivers from the commit message, and no builder had run it on ml-code.** #2552 failed on four intended test changes; a signed commit cannot be amended, so it was closed and re-cut. Run the probe before every push.
- **A ruling or a merge makes validated text false.** After each one, grep the pending carriers' texts for "no ruling", "not decided", "No issue", "not merged".
- **AGENTS.md's date check**: a PR that changes AGENTS.md needs the `Last Updated` line changed, or equal to today's UTC date, and never in the future.
- **The shell guard refuses a command that combines a pipe, `$(...)` or a heredoc with any word containing "git"**, and "gitleaks" in a path counts. Use the session-6 helpers or a script file.
- **An agent can sit inside one Bash call for an hour with no process alive.** Compare its PROGRESS.txt time with the clock; a SendMessage moves the call to the background.
- **`main` moved five times in two hours** (#2549, #2551, #2550, #2553, #2555). The push helper refuses a stale freeze; re-freeze and diff the snapshot against the previous freeze.
- **GitHub's API serves no step summary**; `find -newermt '<date> UTC'` returns nothing on this host; STATE stamps typed from memory ran up to five minutes ahead (use `date -u`).

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert
git fetch -q origin
git log -1 --format=%h origin/main
gh pr view 2554 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'          # MERGED b6b843b6
gh pr view 2557 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'          # MERGED f9582a74
gh pr view 2552 --repo pcalnon/juniper-ml --json state --jq .state                                                      # CLOSED
gh pr view 260 --repo pcalnon/juniper-data-client --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'  # MERGED b45aafbb
gh pr view 756 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'       # MERGED 44b60af2
gh issue view 536 --repo pcalnon/juniper-data --json state --jq .state                                                  # OPEN
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json isDraft --jq '[.[]|select(.isDraft)]|length'       # 33
sha256sum /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--land--flood4r2-stage3-data-code--20261111-1851--399eeffb/juniper_data/api/security.py   # 7b6c3dec...
tail -60 tmp/flood4/session6/STATE_S6.txt
```

## Documents created or modified in session 6

- **Merged on GitHub** (each PR's own files; see its body): the four PRs in the table. juniper-ml#2554 changes `AGENTS.md`, `CHANGELOG.md`, `docs/REFERENCE.md` (0.6.68), `.github/workflows/ci.yml` and `main-verify.yml`; juniper-ml#2557 changes `docs/REFERENCE.md` (0.6.69), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.68), `CHANGELOG.md` and `juniper-service-core/CHANGELOG.md`; juniper-cascor#756 changes `CHANGELOG.md`, `docs/DEVELOPER_CHEATSHEET.md` (1.0.11), `docs/api/API_SCHEMAS.md` (0.3.23) and `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`; juniper-data-client#260 changes `CHANGELOG.md` and `docs/REFERENCE.md` (0.5.2). Comments were posted when closing juniper-ml #2552 and the seven drafts. Issue juniper-data#536 was created.
- **Uncommitted, in the orchestrator worktree:**
  - this handoff;
  - `tmp/flood4/session6/STATE_S6.txt`, `BRIEF_S6_ADDENDUM.txt`, `briefs/A_…` to `K_…` (eleven task briefs), `prev_prompts/`, `prev_messages/`, `land/{ml-code,r17-cascor,r10-data-client,n2}/`, `issue/issue_body.md`;
  - `tmp/flood4/session5/BRIEF_R10_PORT.txt` (a session-6 section appended);
  - `tmp/flood4r2-val/d14-resume-answers-s6/` and the partial `tmp/flood4r2-val/ml-propose-r3b-quick-s6/`;
  - the three session-6 helpers named under Git status, and the agents' `util/ad-hoc/2026-11-12_flood4r2_*` helpers.
- **Uncommitted, elsewhere:** the carrier and agent worktrees named under Goal.
- **Outside any repo (auto-memory):** nothing was written this session. The sequence-safety probe, the mutant-left-by-a-kill trap and the weekly-limit staging rule are not in auto-memory yet.
