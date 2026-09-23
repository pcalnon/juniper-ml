# CI-budget re-evaluation -- consensus round 5, one reviewer -- re-derive the round-4 claims and find what the corrections broke

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2035 at `bdd60b20`
- **Archived**: the lane's final message, copied verbatim from its own session transcript
  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule
  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.

---

## Round 5 findings: ml#2035 at `bdd60b20`

Round 5 found two MAJOR problems. The C2 candidate rule offered in `HANDOFF_2026-09-09_…md` is not the rule round 4 actually simulated, so the claimed simulation results don't hold for the rule as written. And OWNER DECISION 2 says deploy's 700 s budget "held 14" days, when a healthy pass exceeded it after about 2 days. Nothing tracked was changed: all 24 round-4 files were still byte-identical to `bdd60b20` after the mutation run.

Shorthand below: `HANDOFF_2026-09-09_…md` is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`, cited by line at `bdd60b20`.

### MAJOR

**1. The C2 candidate as written is not the rule round 4 simulated.**
- **Where:** `HANDOFF_2026-09-09_…md` lines 170-178, "Simulated, it missed none of the 22 …, kept #1969 and every fixture".
- **What round 4 ran:** `round4-laneB/r4b_c2_rule_sim.py`'s `is_prose_alt` has three clauses the handoff leaves out: the previous line is not command-looking, and not a heading or fence; and the next line is not command-looking. It also ran with `python3?` and `(?=\s)`, not the regex the handoff names.
- **What I found** (`r5_c2_census.py` and `r5_c2_fixtures.py`, on origin/main `ba035cc9`), testing each gap separately:
  - **No "previous line is not command-looking" clause:** the multiplicity test `test_C2_counts_multiplicity_so_duplicated_commands_are_seen`, which the ACCEPTANCE says must pass UNEDITED, reads 0 new lines instead of 2. `pip install x` ends in a letter and has no shell token, so each copy reads as prose.
  - **A heading counted as "the same paragraph":** the rule misses 4 of the 22 fences. These are SOPS guide lines 74 and 86, and `notes/legacy/SECURITY_AUDIT_PLAN.md` lines 227 and 439. When the fence goes, a `# comment` inside it becomes a heading that ends in a letter.
  - **No next-line clause:** three commands glued under mid-sentence prose count 2, not 3.
  - **`python3(\.\d+)?` read as a replacement for `python3?`:** bare `python` stops matching, and the rule misses 6 of the 22. That is all five `**Interface.**` blocks the ACCEPTANCE names, plus `SECURITY_AUDIT_PLAN.md:439`.
  - **With every clause and `python3?(\.\d+)?(?=\s|$)`:** 0 of 22 missed, every fixture passes, #1969 still fires, #1980 clears through the whitespace rule, #2007 clears through the skip, and three glued commands count 3.
- **Fix:** write the candidate as it was simulated: all three clauses, plus the corrected regex.

**2. OWNER DECISION 2: "deploy's 700 s held 14" is wrong.**
- **Where:** `HANDOFF_2026-09-09_…md` line 110, `util/safe_merge.py` line 256, and the round-4 correction at `HANDOFF_2026-09-09_…md` lines 978-979.
- **Evidence:**
  - The max that forced the 09-22 raise was deploy#211, a healthy 965 s pass. It merged on 2026-09-11 at 09:11 UTC.
  - The pin (`b26acd62`) landed 2026-09-09 at 01:00 UTC, so a healthy pass exceeded the budget about 2.3 days later.
  - "14" is the time until the next re-measure. By the handoff's own definition of stale ("below its repo's healthy max"), the budget was stale from day 2.
  - ml's "16 days" is fine: it runs to the first refusal, ml#1754 on 09-05.
  - So three of the four budgets set below the default went stale within about 2 days, and "mixed record" understates the case against HOLD.
- **Fix:** "deploy's 700 s was exceeded by a healthy pass within ~2 days (#211, 965 s, 09-11), unnoticed until 09-22; only ml's 900 s held (16 days, until ml#1754)."

### MINOR

3. **The ACCEPTANCE in `HANDOFF_2026-09-09_…md` is weaker than the GOAL it serves.**
   - Even the rule round 4 simulated misses a duplicated "prose plus one glued command" paragraph: today's screen counts 1, the candidate 0. That is the ml#1799 shape the GOAL names. It also misses a one-command fence removed under mid-sentence prose. The handoff states only the false-positive cost.
   - The `make the` control can only pass in #2007's glued, mid-sentence context. Under every reading it fires after a full stop or at the start of a paragraph.
   - One fence opens directly under a heading and holds commands, so it sits outside the corpus control: `notes/observability/JUNIPER_2026-05-03_JUNIPER-ECOSYSTEM_A9-AND-3-2-STATE-ANALYSIS.md:621`.
   - The exemption list has no bound, and "22" has no stated definition or commit.
   - **Fix:** add a duplicated-paragraph control, name the control contexts, pin the definition and commit, and bound the exemption list.
4. **The archive is not a verbatim copy of what the lanes wrote.**
   - All 15 files do match their task-notification `<result>` exactly, and all 15 rows of `reports/2026-09-22_ci-budget-reeval-consensus/README.md` match each lane's spawning prompt (frozen commit) and description.
   - But the notification escapes `<`, `>` and `&`. So 13 of the 15 files match the lane's own last message (`subagents/agent-<id>.jsonl`) only after `html.unescape`.
   - Inside code spans the escapes show up literally. For example, `round4-laneB.md` line 32 lists the shell tokens as `&gt;` and `&amp;&amp;`.
   - That makes `README.md`'s "only change is presentational" inaccurate.
   - Nothing in the archive is credential-shaped.
   - **Fix:** unescape the text in `archive_round_reports.py` and re-archive, or disclose the escaping in `README.md`.
5. **The Round 5 line contradicts itself.** `HANDOFF_2026-09-09_…md` lines 1128-1129 say the result is recorded "in the same PR, whether or not that PR has merged". A merged PR takes no more commits. **Fix:** "in ml#2035 while it is open, otherwise in a follow-up PR".
6. **The Round 4 record in `HANDOFF_2026-09-09_…md` (lines 1119-1122) leaves out two things:**
   - Lane B reported round 3's M2 as "FIXED in the text, but it does not work".
   - Lane A disclosed that it took the "22" definition from round 3's lane-B census script. My own definition reproduces 22, so no number moves.
7. **The juniper-ml window naming still drifts.**
   - **Where:** `util/safe_merge.py` lines 318-319, `HANDOFF_2026-09-09_…md` lines 226-227 and 708-711, and `tests/test_safe_merge.py` lines 56-57.
   - "#1981–#2014 less #2004 and #2013" covers 32 numbers. It comes out to 30 merged PRs only because #1994 is an issue and #2012 is still open.
   - **Fix:** add "and #2012 (unmerged)".
8. **A check's comment overclaims.** In `check_first_pass_window.py`, `sample == sorted(sample)` can never fail, because the probe sorts the sample itself. A stale window that agrees with its own sample also passes. **Fix:** say it catches a window that doesn't match its sample.

### Verdict per item
1. **Partly holds.** The facts check out.
   - **The 22:** with my definition (the line above the fence is non-blank and is not a fence, heading, table row or command line; the block holds a command line), the count is 22 at `ab434c9b`, `bdd60b20` and `ba035cc9`.
   - **Round 3's rule:** it misses exactly the SOPS fence at line 115 and the five `**Interface.**` blocks.
   - **The SOPS fence at line 115:** its only command line is `git add .env.enc`, sitting under `sops -e`.
   - **The ACCEPTANCE** can be met, since the rule round 4 simulated passes all of it. But see MAJOR 1 and MINOR 3.
2. **Partly holds.**
   - Every commit and date is right: `c3cf3951`, `27d3fc15`, `37123036`, `b26acd62`, `3cab4783` and `7b226ca0`.
   - `3cab4783` introduced the "do NOT raise" paragraph, and it is unchanged since.
   - Pinned budgets were raised 7 times and never lowered.
   - Each side now has one "against it", and every statement of the owner's ruling limits it to the three raises. MAJOR 2 is the exception.
3. **Holds.** The sample was the same throughout 20:08:43–20:18:20 UTC. See MINOR 7.
4. **Holds.** The test's WITHDRAWN note matches both rows' notes in `util/safe_merge.py`, and all 78 tests pass.
5. **Holds**, re-derived by a different route than round 4:
   - GraphQL found exactly 33 annotated soak check-runs, all on the ten PRs.
   - In none of them did main touch any of the PR's markdown files between the merge-base and main at run start. That range covers the head-to-test-merge range.
   - All 33 annotations carry the cut-off title from before ml#2017, so exit 1 and exit 2 can't be told apart from them.
6. **Holds.** All four runs exit 0 and report ALL MUTATIONS KILLED, PASS, and WINDOW RECORDED (#223–#228). `probe_started_at` is written to the JSON, and the all-in-flight refusal message checked out in a stubbed test.
7. **Partly holds.** See MINOR 4.
8. **Partly holds.** "Five held, three held in part, none was refuted, four disagreements" is accurate. See MINOR 5, MINOR 6 and MAJOR 2.

Round 5 changes a NUMBER / DISPOSITION / ACTION: yes -- NUMBER (deploy's 700 s held about 2 days, not 14, in OWNER DECISION 2) and ACTION (NON-OWNER 1's candidate must carry the clauses and regex round 4 simulated); no disposition changes.

**Changed:** nothing tracked. About 45 REST and 13 GraphQL calls.

**Created** (untracked), in `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round5/`:
- `r5_identity.py`
- `r5_c2_census.py`
- `r5_c2_fixtures.py`
- `r5_c2_heading_fence.py`
- `r5_owner2_history.py`
- `r5_ml_window.py`
- `r5_replay_fidelity.py`
- `r5_soak_all_in_flight.py`
- `r5_archive_check.py`
- `r5_archive_rubric_diff.py`

Also `__pycache__/` there (gitignored), and in the session scratchpad: `para_3cab.txt`, `para_bdd6.txt`, `r5_mutation.txt` and `r5_waiter.json`.
