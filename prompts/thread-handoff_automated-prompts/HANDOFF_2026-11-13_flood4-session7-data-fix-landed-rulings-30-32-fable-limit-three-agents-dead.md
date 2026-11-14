# Handoff: flood-4 session 7 — the juniper-data fix landed, rulings 30–32 given; the weekly Fable limit killed three more agents

**Date**: 2026-11-13 local (written 2026-11-13 10:26Z UTC)

**Arc**: the Cursor flood-4 disposition, session 7. It started as `curious-seeking-locket` and ran in `humming-stargazing-papert` via EnterWorktree. It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead.md` (session 6's handoff; uncommitted in that worktree). Session 6's sections "A side effect of juniper-cascor#756" and "Traps" still describe today's state and are not repeated here.

**Host**: the Linux host.

**Why the session stopped**: the account's **weekly Fable limit** was hit again at about 03:42Z on 2026-11-13, about 85 minutes after the first agents started. The API's words: "You've hit your Fable limit · resets Nov 18, 9pm (America/Chicago)", which is 2026-11-19 03:00Z. Three agents died mid-task (listed under Goal). The owner then logged in again (the harness reported an account change) and asked for this handoff; what that account's limit allows was not measured.

**The running log is the detail**: `tmp/flood4/session7/STATE_S7.txt` in the orchestrator worktree has one clock-stamped entry per event, with the owner's rulings verbatim. Read it before acting.

**If session 7 itself is still open when requests are accepted again**, it can resume its three dead agents with SendMessage, which a new session cannot: the guard builder `a5303a15bb4329057`, the unrun-tests validator `ab098e2e0ce5c1cfc`, the ml-tests tests lens `afa2d849b67f0bfb0`. The unrun-tests validator was near its report; the tests lens had finished its mutation run.

---

## Git status

- **The orchestrator worktree** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert`, on branch `worktree-humming-stargazing-papert`. HEAD is `734aab58`, deliberately not fast-forwarded.
- **juniper-ml's main**: `origin/main` was `48b66130` at 10:26Z. juniper-ml#2558, the 0.11.5 release proposal, merged at 10:08:14Z as `48b66130`, and the v0.11.5 Release was cut on that commit at 10:24:18Z. juniper-ml#2561 (that cut's release-notes archive: one new file, auto-merge armed, not ours) was still open.
- **This file** is on the branch `docs/handoff-2026-11-13-flood4-session7`, opened as a pull request by session 7 at the owner's request; **the owner merges it**. A working copy is in the orchestrator worktree.
- **Uncommitted there** (nothing staged): session 5's and session 6's handoffs; the helpers `util/ad-hoc/2026-11-1[12]_flood4r2_*`, to which session 7 added `2026-11-12_flood4r2_s7_log.py`, `2026-11-13_flood4r2_s7_handoff_check.py` and its agents' `2026-11-12_flood4r2_val_ml-propose-r3b_*` (13), `2026-11-12_flood4r2_val_d2-data_*` (9) and `2026-11-12_flood4r2_val_ml-tests-r2-tests_*` (11).
- **Ignored there**: `tmp/`. Session 7's evidence is `tmp/flood4/session7/` (`briefs/`, `land/data-code/`, `BRIEF_S7_ADDENDUM.txt`).
- **Other arcs on juniper-ml**: #2548 (the backup arc) is open. The R-OBS-SC-2 arc's session said on 2026-11-13, in its two messages around the cut, that its guard + register pull request follows the 0.11.5 cut (by session 6's log it changes `tests/test_service_fork_drift.py` and `docs/REFERENCE.md`), that it is ending, and that its next handoff will be the newest `HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-*` file.
- **The primary checkout** is on the owner's branch. Do not touch it.

---

## Landed in session 7

| Item | PR | Squash | Merged | Drafts closed |
|---|---|---|---|---|
| The Retry-After round-up fix (47 tests) | juniper-data#537 | `3cf8867c` | 2026-11-13T02:54:07Z | — |

Signed, frozen on `c68e6b4c`, probed for sequence safety, scanned with a planted-token control, merged by `util/safe_merge.py`; the three post-merge runs on `3cf8867c` succeeded. The R-OBS-SC-2 arc's session was sent the number at open and at merge. Evidence: `tmp/flood4/session7/land/data-code/`.

---

## The owner's rulings of 2026-11-13 (AskUserQuestion, labels verbatim; provisional numbers 30–32, in `STATE_S7.txt`)

- Opening message: "merge approval granted". It is per session and does not carry.
- Agent load: "2-3 Fable agents (Recommended)".
- 30 (D14, which way): "Four rules + shared table". 31 (D14, a negative `last_seq`): "Read as 0 (Recommended)". 32 (the side effect of juniper-cascor#756): "Fix it + document".
- At the end: "commit and PR the handoff. i'll take care of the merge."

---

## Goal

```text
Continue the Cursor flood-4 disposition from juniper-ml/prompts/thread-handoff_automated-prompts/
HANDOFF_2026-11-13_flood4-session7-data-fix-landed-rulings-30-32-fable-limit-three-agents-dead.md.
EnterWorktree(path=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert).
Run the Verification block, then read tmp/flood4/session7/STATE_S7.txt and tmp/flood4/session7/BRIEF_S7_ADDENDUM.txt
(binding on every agent; it names the four older briefs to read first).

FIRST:
(1) Ask the owner for THIS session's merge approval (a handoff cannot carry it).
(2) Ask the owner which model subagents run on and how many at once. Session 7 ran at most three Fable agents at a
    time and the limit still returned after about 85 minutes; the three that finished used 477,640, 664,263 and
    642,144 tokens.
(3) juniper-ml LANDINGS WERE HELD for the 0.11.5 cut from 03:10Z, and THE HOLD IS OVER: juniper-ml#2558, the release
    proposal of the R-OBS-SC-2 arc, merged at 10:08:14Z as 48b66130, and that arc's session cut the v0.11.5 Release
    on that commit at 10:24:18Z (the PyPI gate is the owner's). #2558 moved every unreleased CHANGELOG entry under
    "## [0.11.5] - 2026-11-13". Nothing of this arc is in 0.11.5: every CHANGELOG entry of ours goes under the
    now-empty "## [Unreleased]", never inside "## [0.11.5]". Read the headings above each entry after every rebuild.
(4) Session 7's agents cannot be messaged from a new session. For each dead one: VERIFY ITS TREES FIRST, read what
    it left, then relaunch a FRESH agent with its brief plus the addendum, pointing at the partial work as leads.
(5) Any run of juniper-ml's regression list from a tree that does not hold ae801a70 sets
    DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent/no-session-bus, or the owner gets a real "Backup FAILED" alert.

1. juniper-data's unrun tests (ruling 25): NOT held. Carrier worktrees/juniper-data--test--run-the-unrun-tests--
   20261112-1815--c68e6b4c (14 of 14 files at their recorded sha256 at 10:26Z). Its validator (brief
   tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt) died near its end; partial work in
   tmp/flood4r2-val/d2-unrun-tests-s7/: PROGRESS.txt, an in-progress findings.json with one MAJOR (a plain three-way
   of docs/REFERENCE.md onto main 3cf8867c merges cleanly and keeps the stale stamp 0.4.8: set 0.4.9 by rule),
   proposed/landing_on_main/ (rebuilt CHANGELOG.md and docs/REFERENCE.md), fixes_input.json (23 drafted text fixes).
   NOT written: text_fixes.json, the final findings, REPORT.txt. Its two worktrees (juniper-data--val--flood4r2-d2-
   unrun-tests--20261112-2110--3cf8867c and ...-base--20261112-2110--c68e6b4c) had mutant and lane runs in flight:
   its PROGRESS.txt says how to check them. Finish the validation, apply the fixes, then land on juniper-data's main.
2. ml-propose is VALIDATED (SHIP-WITH-FIXES): carrier .claude/worktrees/agent-a211deee35ec85ad3; the check is
   tmp/flood4r2-val/ml-propose-r3b-quick-s7/. #2558 has merged, so its REPORT.txt section 6, F.5, IS the landing
   procedure: the carrier's own landing command now files the entry inside "## [0.11.5]" and exits 1.
   text_fixes.json holds six fixes for pr_body.txt; #2558 merged from a head other than the d4dcefbc the check read,
   so re-run util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_compare_2558.py before using fix 5. It lands
   immediately before ml-tests.
3. ml-tests round 2 is BUILT: carrier .claude/worktrees/agent-a4cd1de89c2b57ea3 (59 of 59 files match its manifest
   at 10:26Z), deliverables its tmp/flood4r2/ml-tests/r2/ (REPORT.txt gives THE LANDING COMMAND; it takes
   --landing-date and --ml-propose-pr). It needs TWO LENSES, a fix-up, then the landing. The tests lens (brief
   tmp/flood4/session7/briefs/L1_ml_tests_r2_tests_lens.txt) died after its mutation run and before writing any
   findings: partial work in tmp/flood4r2-val/ml-tests-r2-tests-lens-s7/ (PROGRESS.txt; mutants/results.json: 56 mutants, 44 killed,
   7 "test fails (sound)", 3 "PASSES", 2 "SURVIVED" -- the last five are NOT analysed). The claims lens (brief
   L2_ml_tests_r2_claims_lens.txt) was never launched. Before merging, read the macOS job's log lines the carrier's
   REPORT.txt lists in its section 5. Then close its 18 drafts from manifest.json's "carried" table.
4. ml-docs: brief tmp/flood4/session7/briefs/I2_ml_docs_finish.txt, never launched; the dead builder's tree is
   .claude/worktrees/agent-a1e6389f6c2d68753. After it lands: close #2494, the docs drafts and the triage's NONE group.
5. Ruling 18's guard PR (brief tmp/flood4/session6/briefs/J_ruling18_guard_word_structure.txt): its builder wrote
   DESIGN.md and died WHILE EDITING THE GUARD. .claude/worktrees/agent-a5303a15bb4329057 holds a HALF-WRITTEN
   util/claude_agent_guard.py (sha256 7b5ee677...; main's is 09c5db22...) and no new test: never install it or land
   from it without reading all of it. Scratch: its tmp/flood4-fix/r18-guard/ (DESIGN.md, PROGRESS.txt, probes/,
   logs/). PROGRESS.txt lists SEVEN further open spellings its probes report on main (N1-N7; nobody has reviewed
   them). They are not ruled public: keep them out of every committed text until the owner says otherwise.
6. Ruling 10's six ports: tmp/flood4/session5/BRIEF_R10_PORT.txt; none started.
7. New rulings, briefs written, nothing launched: tmp/flood4/session7/briefs/M_d14_resume_four_rules_shared_table.txt
   (rulings 30 and 31; two carriers, juniper-ml and juniper-cascor) and N_cascor_pause_check_then_act.txt (ruling 32:
   a "Known, not fixed" document carrier first, then the fix).
8. From the rulings of 2026-11-12, none built and no brief: two service-core PRs (WebSocket gaps beside N-4;
   lifecycle races beside N-2); five lockfile-print ports plus one canopy docs PR; canopy :8100; canopy's relay
   test. Then round 3's #2404 and #2406.
9. Ruling 7 cleanup, the record-update PR (rulings 15-32, sessions 4-7) and the provenance commit, as
   HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md (on main) describes. Session 7's agents added,
   under Juniper/worktrees/: juniper-ml--val--flood4r2-ml-propose-r3b* (7, one of them session 6's),
   juniper-ml--flood4r2-ml-tests-r2s7-* (5), juniper-ml--val--flood4r2-ml-tests-r2-tests* (5) and
   juniper-data--val--flood4r2-d2-unrun-tests* (2); and .claude/worktrees/agent-{a4cd1de89c2b57ea3,a5303a15bb4329057}
   (a carrier and the guard's partial build: KEEP both) and agent-{a61564fc0ee03e2a2,afa2d849b67f0bfb0}. Never use
   util/remove_stale_worktrees.bash. curious-plotting-hummingbird is DO NOT SWEEP.
10. Landing steps: item 9 of session 6's handoff, unchanged; tmp/flood4/session7/land/data-code/ is a worked example
    for a sibling repository. Stamp the log with util/ad-hoc/2026-11-12_flood4r2_s7_log.py, never from memory.
11. Still owed: reading the first Dependabot pull request on juniper-data-client after #260 (none had opened by 10:26Z).
12. Archive the next handoff.
```

---

## For the owner

- Reinstall the guard: `bash util/install_claude_agent_guard.bash --dry-run`, then `--apply`, from a checkout at `b6b843b6` or later (carried from session 6).
- The guard builder's probes report seven more ways past the guard on main (item 5); nobody has reviewed them. Their spellings are only in that agent's scratch `PROGRESS.txt`.
- A lane for juniper-data's 41 benchmarks: options A–E are the first open question of `tmp/flood4-fix/d2-unrun-tests/manifest.json` in the unrun-tests carrier.
- Unruled: a back-port of the pilot's blocking-wiring pins to juniper-data's own test; whether `main-verify.yml` should hold all fifteen of ml-tests' new suites (it holds six).
- Up to two "Backup FAILED" desktop alerts on 2026-11-13 (02:38Z, 02:42Z) came from this arc's ml-tests builder, before juniper-ml#2559 was known to it.

## Orchestrator decisions taken in session 7 (the owner may overrule)

- juniper-data#537 kept the two 120 s end-to-end tests session 6 had added; the helper-floor test was not renamed to the sibling services' name (the other arc was told); one CHANGELOG sentence gained the qualifier "For every window a float holds exactly," because the carrier's own test reaches a remainder of 0.0. `juniper_data/api/security.py`'s docstring and comment say it without the qualifier.
- The hold on juniper-ml landings (Goal, FIRST 3), set at 03:10Z; the R-OBS-SC-2 arc's session confirmed it at 10:10Z, and it ended with the v0.11.5 Release at 10:24:18Z.

## Traps (new this session)

- **A release proposal empties `[Unreleased]`** (juniper-ml#2558 did). In either merge order a carrier's CHANGELOG entry ends under the released heading unless someone acts, with no conflict. Read the headings above the entry after every rebuild, and never merge main into a pushed carrier branch across a proposal's merge.
- **A limit-killed builder leaves a half-edited security control** (item 5). A killed validator leaves in-flight mutants in its own worktrees.
- **Three agents at a time still exhausted the weekly limit**: budget by tokens, not by agent count.
- **Log stamps typed from memory ran up to fourteen minutes ahead** in this session; the helper in item 10 reads the clock.
- **The other arc's mutation script allows its pre-fix failure only under the sibling services' test name**; against juniper-data it needs `--pre-fix-allowed-test test_the_helper_floors_a_zero_remainder_at_one` through `util/ad-hoc/2026-11-12_flood4r2_data-landing_second_opinion.py`.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert
git fetch -q origin
git log -1 --format=%h origin/main                                                                                     # 48b66130 at 10:26Z
gh pr view 537 --repo pcalnon/juniper-data --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'         # MERGED 3cf8867c
gh pr view 2558 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid[0:8]'          # MERGED 48b66130
gh release view v0.11.5 --repo pcalnon/juniper-ml --json targetCommitish,publishedAt --jq '.targetCommitish[0:8] + " " + .publishedAt'   # 48b66130 2026-11-13T10:24:18Z
gh pr list --repo pcalnon/juniper-ml --state open --limit 200 --json isDraft --jq '[.[]|select(.isDraft)]|length'       # 33
tail -40 tmp/flood4/session7/STATE_S7.txt
```

The two carrier checks need their own directories (a `cd` persists between Bash calls: use one call each):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-a4cd1de89c2b57ea3 && python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py --scratch tmp/flood4r2/ml-tests/r2 --verify   # "differing from the recorded sha256: none"
cd /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--test--run-the-unrun-tests--20261112-1815--c68e6b4c && sha256sum -c tmp/flood4-fix/d2-unrun-tests/sha256_final.txt   # 14 OK
sha256sum /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-a5303a15bb4329057/util/claude_agent_guard.py   # 7b5ee677... = the half-written guard
```

## How this handoff was checked

`util/ad-hoc/2026-11-13_flood4r2_s7_handoff_check.py` re-derived its checkable claims from their sources at 10:29Z: 69 of 69 passed (log: `tmp/flood4/session7/handoff_check.log`).

It reads GitHub for every pull request, issue, release and count named here; the disk for every path and sha256, running the two carriers' own verify commands; the agents' report files for each figure quoted from them; and session 7's transcript for the owner's answers, the agents' token counts and the other arc's statements. An earlier run caught the v0.11.5 Release appearing while this file still called the landings held.

**Not checked**: no second agent read this file (the owner asked to keep token use down). An agent's result is quoted from its report, not re-run. The three dead agents' partial work is unreviewed.

## Documents created or modified in session 7

- **Merged on GitHub**: juniper-data#537 changes `CHANGELOG.md`, `docs/REFERENCE.md` (0.4.8), `docs/DEVELOPER_CHEATSHEET.md` (0.4.7), `juniper_data/api/security.py` and adds `juniper_data/tests/unit/test_retry_after_rounds_up.py`.
- **On its own pull request**: this handoff.
- **Uncommitted, in the orchestrator worktree:**
  - `tmp/flood4/session7/STATE_S7.txt`, `BRIEF_S7_ADDENDUM.txt`, `bash_cmds.py`, `pr756_body.md`, `pr2558.diff`, `handoff_check.log`, `land/data-code/`, and nine briefs in `briefs/`: `A2_data_stage3_finish_47.txt`, `H2_ml_tests_round2_finish.txt`, `K2_ml_propose_r3b_quick_check.txt`, `I2_ml_docs_finish.txt`, `VF_validate_data_unrun_tests.txt`, `M_d14_resume_four_rules_shared_table.txt`, `N_cascor_pause_check_then_act.txt`, `L1_ml_tests_r2_tests_lens.txt`, `L2_ml_tests_r2_claims_lens.txt`;
  - `tmp/flood4/session5/data-landing/` (`REPORT.txt`, `PROGRESS.txt`, `stage3/manifest.json`, the texts, `stage3/s6/state47/`, `stage3/s7/`);
  - `tmp/flood4r2-val/ml-propose-r3b-quick-s7/`, and the partial `tmp/flood4r2-val/d2-unrun-tests-s7/` and `tmp/flood4r2-val/ml-tests-r2-tests-lens-s7/`;
  - the helpers named under Git status.
- **Uncommitted, elsewhere:** the carrier and agent worktrees named under Goal.
- **Outside any repo (auto-memory):** one line added to `reference_verification_discipline_hub.md` (stamps typed from memory); `MEMORY.md`'s count for that hub went 32 to 33.
