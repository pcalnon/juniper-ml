# CI-budget re-evaluation -- consensus round 3, Lane B -- find what the round-2 fixes broke

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `f0b3cc73`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

**Round 3, Lane B: ml#2017 frozen at `f0b3cc73` (round-2 fix `e4cd051b..f0b3cc73`)**

The round-2 fix broke one probe and left a blind spot in the C2 rule, a wrong soak count and a stale PR description. Nothing was clobbered, and the code tests still pass.

**Baseline.** 139 tests pass (`tests/test_safe_merge.py`, `tests/test_wait_for_checks.py`, `tests/test_md_structure_check.py`). `util/ad-hoc/2026-09-22_wait_budget_mutation_check.py` kills every mutation, including the probe mutant (control exits 0, mutant exits 2). CI on `f0b3cc73` is green, and the advisory soak ran clean on it.

### MAJOR

**M1 (code): the new soak guard refuses whenever a soak job is still running.**
- In `util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py`, `probe_soak` has `lost = [c for c in unread if c["conclusion"] != "cancelled"]`. A queued or in-progress soak job has no conclusion yet and its log returns HTTP 404, so it lands in `lost`.
- I ran `soak --since 2026-09-23T01:15:00Z`. It exited 2 with "soak: 2 completed run(s) whose log could not be read after retries: [107006935320, 107006932739]". I confirmed 107006935320 had `status=queued`.
- Four ci.yml runs were queued at that moment. So the PREFLIGHT `all` will often exit 2 on this repo, and the message implies lost evidence when nothing is lost.
- **Fix:** skip check-runs whose status is not `completed` and print them as "in flight, not scored". Count as lost only runs that are completed, not cancelled, and unreadable.

**M2 (action): NON-OWNER 1's C2 rule cannot see the damage it exists for when a fence sits directly under a prose line.** My simulation is in `r3b_c2_rule_sim.py`.
- These pass: the multiplicity test still counts 2, #1969's true finding still counts 1 (the line above it is a `# …` comment, which markdown reads as a heading), and the false findings on #1980 and #2007 clear.
- This fails: a prose lead-in (`Run these:`) followed by three commands counts 2, not 3. That breaks the rule's own "N contiguous commands must still count N".
- Census (`r3b_c2_blind_census.py`): tracked markdown has 955 fenced blocks containing commands. 22 open directly under a prose line, and if 10 of them lost their fence pair, C2 would not report it at all. Example: `notes/JUNIPER_2026-03-02_JUNIPER-ECOSYSTEM_SOPS-USAGE-GUIDE.md:115`, where "When a repo starts needing secrets:" is followed by `git add .env.enc`.
- **Fix:** add the negative control "a fence pair removed directly under a lead-in still fires". Narrow the skip, for example never skip the first of two or more contiguous commands, and never skip a line after prose that ends in `:`.

**M3 (action): CI screens the test-merge commit against a base that can be stale.**
- The soak job for #1980 at `1814a269` logged `HEAD is now at b1df7c7c Merge 1814a269… into 05c5f794…`, but its base was `739a233c`. It examined 8 files for a PR that changed 1.
- 3 of the 14 soak runs I read had this stale base (also #1999 at `25c001bd` and `276db114`).
- All 10 census findings are on files their own PR changed (`r3b_soak_attribution.py`). So no census number moves, and replaying at the PR head is faithful for these 10.
- The risk is after promotion: a required check would block a PR for another PR's markdown. A future finding on a file only main changed would also "clear" at the head without testing anything.
- **Fix:** in the PROMOTION PATH comment in `.github/workflows/ci.yml` and OWNER DECISION 3 in `HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`, diff against `HEAD^1`. The replay text there should say it is faithful only for files the PR changed.

**M4 (number): the soak census is stamped "2026-09-23 00:50 UTC" but was taken at 00:33.**
- The stamp appears in the `ci.yml` soak comment, in `HANDOFF_2026-09-09_…slack-deficit.md` (banner, DECISION 3, What moved 4), and in `JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §7.
- The only re-read output (scratchpad `main/r2/soak4.json`) records `measured_at` 00:33:18Z and covers PRs up to #2026.
- Between 00:33 and 00:50 the soak also examined #2027, #2028 (two heads) and #2029, all clean (`r3b_soak_window_edge.py`). Another round-3 lane's later run agrees: 65 PRs, 10 findings.
- **Fix:** either restamp to 00:33 with 62 PRs, or keep 00:50 and say 65 PRs. The findings (10 distinct, 2 true, 8 false) stand either way.

**M5 (docs): the live PR #2017 description is still the original.**
- Its figures come from the withdrawn rule (cascor p90 1615, per-row head counts of 26–29).
- It cites a `rerun-split` subcommand the reprobe no longer has, so that command would exit 2.
- It still says "5/5 mutations" and "124 OK", the consensus box is unchecked, and its file table lists 10 of the PR's 20 files.
- The drafted replacement (`main/pr2017_body_new.md`) was never applied.
- **Fix:** update the body with `gh api -X PATCH repos/pcalnon/juniper-ml/pulls/2017 -F body=@…` before asking for merge approval.

**M6 (action): the PR head moved after the freeze.**
- The owner pushed `6f17aea5` at 01:07Z, a CodeQL "Unused import" fix that removes `rest_pages` from the import in `round2-laneA/r2a_spans.py`.
- This worktree's untracked copy still has the old import, so pushing whole files from here would undo that fix. Build the round-3 fixes on `6f17aea5`.
- The handoff's GIT STATE note ("identical to the PR head") is no longer true for that file. I did not review `6f17aea5`.

### MINOR

**m1: several OWNER DECISION 2 premises are wrong.** This covers the first §1 block of `HANDOFF_2026-09-09_…slack-deficit.md` and the dissent comment above `REPO_TIMEOUTS` in `util/safe_merge.py`. The structure is balanced, and everywhere I checked the owner's ruling is stated as covering the three raises only.
- (a) "Every re-measure of an already-pinned budget has raised it" is false. Re-measures raised 6 of 24 pinned readings (09-08: 1 of 6; 09-09: 2 of 9; 09-22: 3 of 9) and lowered none (`r3b_budget_history.py`). The accurate wording is "no re-measure has lowered one".
- (b) "The one lowering" is wrong: there were two. `c3cf3951` (2026-08-19, ml#1183) cut the fleet-wide default from 1800 to 900 s "sized from measurement", and `27d3fc15` raised it to 2400 the next day.
- (c) The pre-start reading of the "do NOT raise a budget to absorb a queue" paragraph was written in `3cab4783` (2026-09-09, ml#1851), the same commit that wrote the paragraph. The 2026-09-10 WITHDRAWN (1) note (`db627616`) retracted only its reasoning. The paragraph itself is unedited since, as the text says.
- (d) Neither side mentions that the paragraph's own example was a within-span queue. That example is run 34293438446 on ml#1828: its first job started 66 s after the run was created, then jobs sat queued for 8.4–12 minutes. `3cab4783` raised ml from 1500 to 2800 to cover that same PR's span while calling its refusal "the design working". This is HOLD's strongest fact and the weak point of SHIP's precedent.

**m2: the watcher's error line splits in two (`util/ad-hoc/watch_prs_until_terminal.bash`).**
- With `PER_PR_TIMEOUT` unset, the waiter's stderr always starts with its `wait budget:` line. A PROBE-ERROR therefore prints on two lines, breaking the "one line per PR" contract. The 200-character cap then cuts off the real cause ("…failed after 3 attemp").
- **Fix:** `err="$(grep -v '^wait budget:' "$errf" | tr '\n' ' ')"`.
- Pre-existing: a PROBE-ERROR followed by a TIMEOUT exits 1, not the documented 2 (reproduced).
- Everything else behaved correctly:
  - shellcheck 0.11.0 reports nothing.
  - Under bash 5.3, the empty `--timeout` array is safe under `set -u`.
  - A merged PR prints `DONE juniper-ml#2010 state=MERGED`.
  - `PER_PR_TIMEOUT=1` on #2020 prints `TIMEOUT juniper-ml#2020 after 1s — NOT a verdict. running=[Regression Tests (Python 3.12), (3.13), (3.14)] absent=[Quality Gate]` and exits 1.
  - A `mktemp` failure prints PROBE-ERROR and exits 2.
  - `PER_PR_TIMEOUT=abc` prints PROBE-ERROR with the usage text and exits 2.

**m3: the replay procedure works as written, with one missing step.**
- The sandbox allowed both `git -C <this worktree> worktree add --detach …/worktrees/juniper-ml--round3-replay--<pr> <head>` and `cd <replay worktree> && python3 <screen by absolute path>`.
- Both findings reproduced exactly as the CI logs show them: #2024 C4 lost "### F. Dropped by THIS document and restored 2026-09-22 by a peer re-probe" (heading count 16 → 17), and #1980 C2 flagged "git). A table…".
- The missing step: `1814a269` was not in the local object store. #1980's branch is deleted, so the PREFLIGHT `git fetch origin` cannot bring it. Add `git fetch origin <head sha>`.
- I also tested a route that needs no worktree: write `git show <head>:<path>` into a temp directory and run the unmodified screen there with `GIT_DIR` set. It reproduced all four findings I replayed (#1969, #1980, #2007, #2024; exit 1 each).

**m4:** "Set S in the same command" invites `S=<dir> python3 … "${S:?…}"`. That form aborts, because the expansion happens before the assignment (exit 127 here). It fails safe. Write `S=<dir>; python3 …` instead.

**m5:** The PREFLIGHT says the merge request "must put OWNER DECISION 2 to the owner", but DECISION 2 already records the raises as ruled. It should say to cite the 2026-09-22 SHIP ruling instead.

### Other hunt items
- **Owner's commits (item 6):** nothing clobbered.
  - The `9c7f5618` `raise` survives at line 116 of the reprobe.
  - Main changed none of the PR's files between the fork point `d0582a21` and `d594a9d3`.
  - `f0b3cc73` touches only its 14 files, and `AGENTS.md` (dated by `e4cd051b`) is untouched.
- **Stale strings (item 5):** none of the nine strings appears on the branch or on main except in the dated census text and the corrections list.
- **Round-2 findings (item 7):**
  - All three raw reports are fixed or recorded, with two exceptions.
  - Lane B #2 is partial: the 733 figure is still uncited, and 733 and 680 rest on uncommitted scratchpad output.
  - Lane B #10 (no mutation covers the `sys.modules` registration) is not addressed; Lane B itself judged it safe.
  - Leftover problems in otherwise-fixed items are M2, M3 and m3 above.

### Verdicts
- **Code: FIX-FIRST.** Fix M1 and m2. `util/safe_merge.py` and `util/wait_for_checks.py` can ship.
- **CI: SHIP.** The only change needed is the stamp in the `ci.yml` comment, which goes with M4.
- **Docs: FIX-FIRST.** M2, M3, M4, M5, m1, m3, m4 and m5.

Round 3 changes a NUMBER / DISPOSITION / ACTION: yes -- NUMBER (the soak's PR count at the stated stamp is 65, not 62) and ACTION (M1, M2, M3, M5, M6, m3); no disposition changes.

**Created** (untracked, under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit/util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round3-laneB/`): `r3b_soak_attribution.py`, `r3b_budget_history.py`, `r3b_c2_rule_sim.py`, `r3b_c2_blind_census.py`, `r3b_rubric_findings.py`, `r3b_soak_window_edge.py`. Scratch outputs are `r3b_*` files in the session scratchpad.

**Worktrees:** created `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--round3-replay--2024` (at `3e7a860b`) and `…--1980` (at `1814a269`). Both were removed with `git worktree remove`, then `git worktree prune`, and `git worktree list` no longer shows them. I fetched three commits by SHA (`1814a269`, `5908be23`, `f042bfec`), which added objects and wrote `FETCH_HEAD` only. This worktree's HEAD (`18d3d5e3`), index and files are unchanged. I used about 170 REST calls.
