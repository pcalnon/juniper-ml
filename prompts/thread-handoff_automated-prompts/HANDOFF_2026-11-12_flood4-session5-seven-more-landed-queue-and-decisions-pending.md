# Handoff: flood-4 session 5 — seven more landed; four carriers in flight, six ports and seventeen Overtoad decisions pending

**Date**: 2026-11-12 (written 09:15Z UTC)

**Arc**: the Cursor flood-4 disposition, session 5. It started as `agile-wondering-lollipop` and ran in `humming-stargazing-papert` via EnterWorktree. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md` (session 4's handoff, on `main` since juniper-ml#2545).

**Host**: the Linux host.

**Why the session stopped**: context length. The session ran about nine hours of wall-clock, with a six-hour gap when the account ran out of usage credits, and the harness began signalling context summarisation. Nothing is blocked.

**The running log is newer than this file.** `tmp/flood4/session5/STATE_S5.txt` in the orchestrator worktree has one dated entry per event. Read its tail before anything else: entries after 09:15Z describe what this handoff calls "in flight".

---

## Git status

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert`. HEAD is `734aab58` and was deliberately not fast-forwarded; `origin/main` was `15b5d9bb` at 09:13Z. Its landing tools equal `main`'s.
- **Uncommitted there: 224 paths at 09:15Z**, nothing staged. The count grows while agents write helpers.
  - This handoff.
  - Session 3's and session 4's handoffs and 80 helpers that juniper-ml#2545 put on `main`; the untracked copies here match `main`'s.
  - Owed to the provenance commit: the 39 helpers dated 11-08, session 3's 8, and (at 09:13Z) 64 `util/ad-hoc/2026-11-11_flood4r2_*.py` and 29 `util/ad-hoc/2026-11-12_flood4r2_*.py`. Eight are session 5's own (`…_s5_*`).
  - `tmp/` is ignored. Session 5's evidence is in `tmp/flood4/session5/` (`land/<item>/` per landing).
- **The primary checkout** is on the Overtoad's branch. Do not touch it.

---

## Landed in session 5 (2026-11-12 UTC; each signed, frozen, scanned with a planted-token control, merged by `util/safe_merge.py`)

| Item | PR | Squash | Merged | Drafts closed |
|---|---|---|---|---|
| Session-4 handoff and helpers (three CodeQL threads fixed) | juniper-ml#2545 | `9063ebf3` | 01:19:18Z | — |
| data-tests carrier | juniper-data#534 | `afeb4403` | 01:52:21Z | #520, #522, #523, #524 |
| data-docs carrier | juniper-data#535 | `c68e6b4c` | 02:02:56Z | #521 |
| Ruling 17: canopy lockfile print | juniper-canopy#814 | `51426d9c` | 02:06:58Z | — |
| Ruling 17: canopy unit-lane network guard | juniper-canopy#815 | `ee265fde` | 08:24:27Z | — |
| N-3 cascor WebSocket resume losses | juniper-cascor#754 | `b9167bdc` | 08:38:46Z | — |
| N-4 service-core dropped-socket close | juniper-ml#2547 | `15b5d9bb` | 08:59:58Z | — |

Ruling 11 is three of four done (N-2 remains). Ruling 17 is three of four done (cascor remains). juniper-data and juniper-canopy have no open PR.

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-12_flood4-session5-seven-more-landed-queue-and-decisions-pending.md (in the humming-stargazing-papert
worktree, uncommitted). EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/
humming-stargazing-papert). Run the Verification block, then read the tail of tmp/flood4/session5/STATE_S5.txt.

FIRST:
(1) Ask the Overtoad for THIS session's merge approval (a handoff cannot carry it).
(2) Decisions D1-D17 are unanswered. Present them (this file's "Open decisions"); only D7 gates a landing.
(3) Session 5's agents cannot be messaged from a new session. Read what each left on disk (below); relaunch only what
    has no REPORT.txt. Brief every agent with tmp/flood4/BRIEF_COMMON_R2.txt or BRIEF_VALIDATE_R2.txt, then
    tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt, then tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (checkpoint as you go;
    seven CodeQL shapes; helper names carry the local date).

1. Finish what was in flight at 09:15Z (four agents; each writes PROGRESS.txt and REPORT.txt):
   a. juniper-data code carrier (Retry-After round-up; stage 3). Tree: worktrees/juniper-data--land--flood4r2-stage3-
      data-code--20261111-1851--399eeffb. Deliverables: tmp/flood4/session5/data-landing/stage3/. Its agent was adding
      a helper-floor test and the rounding and wire points the R-OBS-SC-2 session's review supplied. Land it when the
      manifest says final: freeze with --base origin/main, run the stage-parent check, then the usual steps. MESSAGE
      the peer session "r-obs-sc-2-follow-ups-four-ruled-four-open" when the PR opens and when it merges. Keep
      security.py's method name and its `max(1, math.ceil(` expressions; never name that arc's register row.
   b. Ruling 17, cascor stop-then-start, round 2. Carrier: worktrees/juniper-cascor--fix--stop-then-start-race--
      20261109-0944--96cf891b, deliverables its tmp/flood4-fix/r17-cascor-stop-start/. Both lenses are done
      (tmp/flood4r2-val/r17-cascor-{code,claims}-lens-s5/); the builder was applying them and rebuilding on cascor
      main b9167bdc with cheatsheet 1.0.11 and API_SCHEMAS 0.3.23 set by hand. Check those two stamps, then land.
   c. ml-code final check -> tmp/flood4r2-val/ml-code-final-s5/. Carrier: .claude/worktrees/agent-abc4673d5f7701209,
      its tmp/flood4r2/ml-code/r3/ (base 187e3258, 42 files). Round 3 REWROTE the guard's scan (one pass, a
      fail-closed 2,000,000-character budget), so it does not land before that check. Then a fix-up, a three-way on
      the current main, REFERENCE = main + 0.0.1, AGENTS.md's date and suite count re-derived. After the merge tell
      the Overtoad to reinstall guard 1.3.0.
   d. ml-propose round 3 -> .claude/worktrees/agent-a316b11a248b6f8fe, its tmp/flood4r2/ml-propose/r3/. It must be
      right on main with and without the peer session's floor PR.

2. Land, per repo (a strict ruleset each). The steps, with session 5's helpers in util/ad-hoc/:
   - apply a validator's text_fixes.json with 2026-11-11_flood4r2_s5_text_fixes_to_edits.py, then
     2026-11-08_flood4r2_fix_apply_edits.py (--dry-run first); `git apply` its proposed/ diffs; re-run what they touch;
   - freeze with 2026-11-09_flood4r2_land_snapshot.py, from a checkout of the carrier's repository;
   - read 2026-11-11_flood4r2_s5_freeze_review.py's summary and run 2026-11-12_flood4r2_s5_snapshot_gate.py;
   - stage title.txt, pr_body.md, commit_body.txt with the footer and trailers; scan snapshot and texts with
     2026-11-09_flood4r2_land_gitleaks.py; push with 2026-11-09_flood4r2_land_open_pr.py (--dry-run first);
   - run util/safe_merge.py --execute --timeout 3300 in the background and read its MERGED line;
   - close drafts with 2026-11-07_flood4_close_carried.py: READ the dry run (see Traps).
   juniper-ml, in this order: N-2 (built: .claude/worktrees/agent-a9ff96b8a7d3346e7, tmp/flood4-fix/n2-r2/; waits
     for D7); ml-code; ml-propose and then ml-tests in ONE sitting; ml-docs (build it after ml-code); ruling 18's
     PR (scope per D1); round 3's #2404 and #2406; the ml port of ruling 10.
     ml-tests (.claude/worktrees/agent-a67685d30bfa19727, tmp/flood4r2/ml-tests/) still needs: the two findings the
     ml-propose rounds routed to it (final check F6), D8, a rebuild on the main that holds the peer's floor PR, two
     lenses on the post-ml-code state, then landing.
   juniper-data-client: the ruling-10 pilot is built and validated (tmp/flood4r2-val/r10-data-client-s5/: 0/1/9).
     Apply proposed/0001-test-pin-the-blocking-wiring.diff and text_fixes.json to worktrees/juniper-data-client--ci--
     gitleaks-pr-commit-scan--20261111-1914--3cd855d1, re-run its 25 tests and its mutation check, then land. Read the
     live run's log lines the manifest and the validator list BEFORE merging: wait with util/wait_for_checks.py
     first, and run safe_merge only after reading them.

3. Ruling 10's six other ports (juniper-ml, -canopy, -cascor, -cascor-client, -cascor-worker, -deploy): one builder
   and one validator each, staged two or three at a time. Brief: tmp/flood4/session5/BRIEF_R10_PORT.txt (it carries
   the pilot's lessons and session 5's rulings). ADD the pilot validator's F1 to it first: pin the blocking wiring.
   Also test whether juniper-data's own merged test lets the same twelve mutants live; if so that is a follow-up.

4. Ruling 7 cleanup, the record-update PR and the provenance commit, as session 4's handoff describes them. Session
   5 added worktrees matching: juniper-*--val--*, juniper-canopy--probe--r17-guard-r2-*, juniper-data--land--flood4r2-*,
   juniper-cascor--build--*n3-r3-scratch*, juniper-data-client--detached--*, juniper-ml--val--flood4r2-ml-propose-
   final-sims*, and .claude/worktrees/agent-* carriers and lenses named in STATE_S5.txt. The peer session's
   juniper-*--fix--rate-limit-retry-after-round-up--* and --fix--fastapi-telemetry-opt-out--* worktrees are NOT this
   arc's. Never use util/remove_stale_worktrees.bash. curious-plotting-hummingbird is DO NOT SWEEP.

5. Archive the next handoff.
```

---

## Open decisions (the Overtoad's; none answered)

D1–D9 are session 4's; its handoff has their full context. Evidence added in session 5 is noted. Option (a) is recommended unless marked.

| # | Decision | Session-5 evidence | Options |
|---|---|---|---|
| D1 | Where guard bypasses F3/F4 are fixed | ml-code round 3 lists both as open | (a) ruling 18's PR; (b) own PRs; (c) in ml-code |
| D2 | juniper-data: 137 tests no lane runs (75 security), plus 41 benchmarks | — | (a) follow-up PR; (b) record |
| D3 | An issue for M-1's force-push gap | — | (a) open one; (b) record |
| D4 | N-4's two adjacent gaps | N-4's code lens confirmed both and recommends (a) | (a) one follow-up PR; (c) record |
| D5 | The unreachable lockfile print in five sibling repos | #814's validator confirmed all five | (a) port; (b) record |
| D6 | canopy's :8100 unit-lane connects | #815 says "deferred" | (a) follow-up PR; (b) record |
| D7 | **Accept N-2's 409** | Both lenses say accept. Cost: a `fit` that hangs blocks every start until restart | (a) accept; (b) bounded wait; (c) fencing |
| D8 | Guard suites missing from host-tooling-macos | — | (a) in ml-tests; (b) follow-up |
| D9 | canopy `CICD_MANUAL.md:796` | Confirmed false; exact text in `tmp/flood4r2-val/r17-canopy-lockfile-print-s5/text_fixes.json` | (a) ride the canopy port; (b) own PR; (c) record |
| D10 | service-core's stop-then-LOAD race (pre-existing; a six-line fix passed on a copy) | N-2's code lens F2 | (a) own PR; (b) fold into N-2; (c) record |
| D11 | N-4's per-IP slot is released at the drop, so the cap is exceeded while a socket closes | Landed with honest text | (a) decide in D4's follow-up; (c) record |
| D12 | canopy's `test_relay_cascade_add_does_not_block_the_loop` failed #807 and #814 on load | Logs in `land/r17-canopy-lockfile/` | (a) follow-up PR; (b) keep re-running |
| D13 | With #2507's row test on `main` the compatibility row tracks pyproject, not the last release | Confirmed by the ml-propose final check | For information |
| D14 | N-3 answers a negative `last_seq` and a non-object `data` differently from service-core | N-3's quick check: keep, and have service-core follow | (a) juniper-ml follow-up PR; (b) record |
| D15 | cascor fences and queues where service-core refuses | cascor's code lens: keep; a 409 would break canopy's Restart | (a) keep; (b) refuse, with a canopy change |
| D16 | service-core: a leftover replay session's `stop` resets a running run | N-2 round 2, documented as unfixed | (a) own PR, with D10's; (b) record |
| D17 | Do F3/F4's exact spellings stay in public docs? | ml-code round 3 prints them | (a) keep; (b) describe the classes only |

**Orchestrator decisions taken in session 5** (the Overtoad may overrule):
- N-2's blocker, a refused start that "changes nothing", was fixed as text.
- N-4's three-line `disconnect()` cancel was accepted on a self-review.
- #814 kept `lockfile NOT committed` and gained a "Known limit" section; D9 was not folded in.
- The ports follow #530 on the SARIF artifact name, keep the two shell blocks byte-identical, and ship only the mutation check after the pilot.
- The peer session's test points were folded into the data code carrier.

## Coordination with the R-OBS-SC-2 session

Its peer name is `r-obs-sc-2-follow-ups-four-ruled-four-open`. It yielded juniper-data's Retry-After fix to this arc and keeps cascor's and canopy's.
- **Owed to it**: the data code PR's number on open and on merge; a message when ml-propose and ml-tests are both on `main` (its 0.11.5 cut waits on that).
- **Owed by it**: a message when its `[tools]` floor PR opens and merges. That PR lands before ml-propose; re-freeze after it.

## Traps (new this session)

- **Usage credits ran out at about 02:05Z and killed all eight agents.** The same session resumed each with SendMessage; a new session cannot. Checkpoints made it lossless.
- **`close_carried.py` prints "nothing -- carried as drafted" for a draft whose fix-up manifest holds `fixes: null`.** Build its input with `2026-11-11_flood4r2_s5_merge_close_manifest.py`.
- **`util/home_path_literal_check.py` passes vacuously on a path outside the repository** ("0 files").
- **A cumulative stage freezes with `--base origin/main`**, then `2026-11-11_flood4r2_s5_stage_parent_check.py` must report every path `main == parent`.
- **Three more CodeQL shapes block merges**; all seven are in `BRIEF_S5_ADDENDUM.txt`.
- **A three-way merge keeps a stale stamp silently** when both sides bumped to the same value. Read every stamp.
- **juniper-ml `main` moves under you**: #2360 landed mid-session, and the backup arc's #2548 (ci.yml, AGENTS.md, REFERENCE, CHANGELOG) is open.
- **A Bash call that mixes a loop, a pipe or `$(...)` with a word containing "git"** (`.github`, the scanner's name) is refused. A `cd` persists into the next call.
- **Stamp STATE entries from `date -u`**; estimates ran up to 25 minutes ahead.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert
git fetch -q origin
git log -1 --format=%h origin/main
gh pr view 2545 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'      # MERGED 9063ebf3
gh pr view 2547 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'      # MERGED 15b5d9bb
gh pr view 534 --repo pcalnon/juniper-data --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'     # MERGED afeb4403
gh pr view 535 --repo pcalnon/juniper-data --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'     # MERGED c68e6b4c
gh pr view 814 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED 51426d9c
gh pr view 815 --repo pcalnon/juniper-canopy --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED ee265fde
gh pr view 754 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'   # MERGED b9167bdc
gh pr list --repo pcalnon/juniper-data --state open --json number --jq length      # 0
gh pr list --repo pcalnon/juniper-canopy --state open --json number --jq length    # 0
python3 util/ad-hoc/2026-11-11_flood4r2_s5_checkpoints.py tmp/flood4/session5/checkpoints.txt
tail -60 tmp/flood4/session5/STATE_S5.txt
```

At 09:13Z juniper-ml had 41 open PRs: 40 Cursor drafts (38 of round 2, plus #2404 and #2406) and #2548, the backup arc's.

## Documents created or modified in session 5

- **Merged on GitHub** (each PR's own files; see its body): the seven PRs in the table above. juniper-ml#2547 changes `docs/REFERENCE.md` (now 0.6.67), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.67), `CHANGELOG.md` and `juniper-service-core/CHANGELOG.md`. Comments were posted when closing juniper-data #520–#524.
- **Uncommitted, in the orchestrator worktree:**
  - this handoff;
  - `tmp/flood4/session5/STATE_S5.txt`, `BRIEF_S5_ADDENDUM.txt`, `BRIEF_R10_PORT.txt`, `checkpoints.txt`, `prev_prompts/` (session 4's 42 agent briefs), `land/*`, `data-landing/*`, `ruling10/`, `memnotes/`;
  - `tmp/flood4r2-val/*-s5/` (each lens's findings);
  - session 5's helpers: `util/ad-hoc/2026-11-11_flood4r2_s5_{checkpoints,extract_agent_prompts,extract_bash_commands,freeze_review,merge_close_manifest,stage_parent_check,text_fixes_to_edits}.py` and `util/ad-hoc/2026-11-12_flood4r2_s5_snapshot_gate.py`;
  - the agents' `2026-11-11_flood4r2_*` and `2026-11-12_flood4r2_*` helpers.
- **Uncommitted, elsewhere:** the carrier and validator worktrees named under Goal.
- **Outside any repo (auto-memory):** `reference_codeql_unused_global_cascor.md`, `reference_ci_merge_mechanics_hub.md`, `reference_ci_parity_gitleaks_local_scan.md` and `project_dynamic_workflow_harness_design_2026-09-23.md` each gained a dated entry. The close-tool, vacuous-gate and stage-freeze traps above are not in auto-memory yet.
