# CI-budget re-evaluation -- consensus round 4, Lane A -- re-derive the round-3 claims

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2035 at `0ffe15dc`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

Round 4, Lane A is finished. Two findings change an action, and no number or disposition changes: every re-derived figure holds or is only partly true, and the soak is still not ready to promote.

`HANDOFF` = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`; `WALKTHROUGH` = `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`. Line numbers are at 0ffe15dc. I used about 117 REST calls.

**Disclosure:** besides round 3's lane-A cache, I read round 3's archived lane-A report and lane B's census script. I used the script only to find which definition gives "22". Every figure below comes from my own code.

## Verdicts
1. **PARTIAL.** I walked every commit touching `util/safe_merge.py` and read the constants with Python's parser.
   - The history is as stated. One addition: 27d3fc15 raised the default to 2400 but also pinned juniper-ml at 900, which lasted until 37123036 on 09-05.
   - "No re-measure lowered an already-pinned budget" holds, and so does "3 raised, 6 stood".
   - "Both lowerings reversed within a day" does not hold: juniper-ml kept 900 for 16 days and deploy kept 700 for 14.
   - In UTC, b26acd62 lands on 09-09, the same day as the 2000 raise.
2. **CONFIRMED.** Run 34293438446 ran on fe02d251, an earlier head of ml#1828.
   - All 17 of today's required contexts ran on that head, and the span starts at 00:05:45Z.
   - `Build and Validate Package` waited 718 s (00:12:54 to 00:24:52), all of it inside the span.
3. **CONFIRMED.** Searching history for the "do NOT raise" sentence, and for every line of its paragraph, finds only 3cab4783 (ml#1851).
   - That commit also wrote the pre-start reading and raised juniper-ml 1500 to 2800.
   - db627616 replaced the reasoning with "measurement SCOPE" and kept the reading.
4. **CONFIRMED.** `ci.yml:1670` diffs against `github.event.pull_request.base.sha`; HEAD^1 is used only when that is empty.
   - Job 106513520869's log reads "examining 8 … against 739a233c" and "HEAD is now at b1df7c7c Merge 1814a269 into 05c5f794". The cached and live logs agree.
   - 739a233c is an ancestor of 05c5f794, two commits and seven markdown files behind it. #1980 changed one markdown file.
5. **CONFIRMED.** Each of the ten flagged files is in its own PR's changed-file list.
6. **PARTIAL.** See MAJOR 1.
7. **PARTIAL.** See MINOR 4. The pinned (910, 2005) and the 00:33 window #1991–#2026 at (680, 1061), max #2003, reproduce exactly.
8. **CONFIRMED.**
   - Provenance: the live run list matches the cache (the two extra runs have zero jobs), five job records match live, and the probe's own soak4.json is stamped 00:33:18Z.
   - Before 00:33:18Z: 210 soak check-runs, 13 unreadable (all cancelled), 19 with no markdown, 178 examined 429 files on 62 PRs (56 merged, 1 closed, 5 open), 10 findings.
   - By 00:50: 214 check-runs, 182 examined, 434 files, 65 PRs, still 10 findings. The four new runs are four distinct heads (#2027; #2028 twice, 8e8391bc and 5f6f735b; #2029), all clean.
   - A cutoff of "at or before 00:33:18" instead of "before" would admit #2027's run, created at exactly that second.
9. See the table.

## Findings

**MAJOR 1 (action) — NON-OWNER 1's lead-in example is not covered by its own rule.** `HANDOFF:167-171`, control at `:177-178`.
- **"22" needs its definition:** blocks directly under a prose line whose body contains a line the screen treats as a command (at both 0ffe15dc and f0b3cc73).
  - Read literally ("fences that open directly under a prose line"), the count is 232 under the rule's own definition of prose, or 162 counting only plain prose lines.
- **The cited example stays invisible:** of the 22, 10 were invisible to the old rule and 6 stay invisible under round 3's rule, including the example (SOPS guide line 115).
  - Its first line is `cp`, which the screen does not treat as a command.
  - Its only command line, `git add .env.enc`, sits under `sops -e …`, which the rule counts as prose.
- **The other 5** are the `**Interface.**` blocks in `notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md` (lines 96, 136, 169, 196, 226). So "one command glued to mid-sentence prose" understates the remaining cost.
- **The control fails:** a control built from the cited example would not fire.
- **Fix:** cite a block under a lead-in ending in `:` whose first line is a command, such as `notes/JUNIPER_2026-05-21_JUNIPER-ML_CI-TOOLS-EXTRACTION-PLAYBOOK.md:111`. State the 22 / 10 / 6 split, and either accept the 6 or close them.

**MAJOR 2 (action) — the walkthrough's promotion recipe leaves out the HEAD^1 base.** `WALKTHROUGH:283-290` lacks it, while `ci.yml:1641-1646` and `HANDOFF:131-135` carry it. Round 3 edited that very note. Fix: add the base change there.

**MINOR 3.** "Both past lowerings went stale within a day" (`util/safe_merge.py:260-262`, `HANDOFF:113-115`). Fix: two went stale within a day (the default, and recurrence); juniper-ml's 900 lasted until it refused ml#1754 (re-tiered 09-05), and deploy's 700 lasted until 09-22.

**MINOR 4.** The "#2004 … the pair is the same with it" note leaves out #2013.
- #2013 is also in #1981–#2014. It merged at 01:29:41Z, before 0ffe15dc, and is 0ffe15dc's grandparent. Reading the whole range now gives (857, 2005).
- Under the probe's "30 newest merged" rule, a merged #2004 would push #1981 out and the max would fall to 1061.
- The pinned 30-PR sample existed only from 20:08:43 to 20:18:20Z.
- Sites: `util/safe_merge.py:317-318`, `tests/test_safe_merge.py:56-57`, `HANDOFF:688-689` and `:932-933`. Fix: name #2013 and describe the window as the sample, not a number range.

**MINOR 5.** `tests/test_safe_merge.py:588-601` still states, as fact, both reasons withdrawn on 2026-09-10 ("which `safe_merge` waits through", "This is contention", "Its CI got heavier"). That contradicts `util/safe_merge.py:299-311` and `:373-379`. The text came from 3cab4783; round 3 edited this file and left it.

**MINOR 6.** `HANDOFF:191-192` says the replay is faithful "because each is on a file its own PR changed". That reason alone does not establish it. The conclusion holds on a direct check: main changed the flagged file between the PR head and the test merge in 0 of 33 flagged runs, and within the lagging base in 0 of 6. State that check instead.

## Cross-file table (0ffe15dc)
| Figure | Disagreement |
|---|---|
| Promotion diffs against HEAD^1 | `WALKTHROUGH:283-290` vs `ci.yml:1641-1646`, `HANDOFF:131-135` |
| Pre-start reading and its withdrawn reasons | `tests/test_safe_merge.py:588-601` vs `util/safe_merge.py:299-311`, `:373-379` |
| Lowerings "within a day" | `util/safe_merge.py:260-262` and `HANDOFF:113-115` agree with each other; both contradict the history |
| #2004 note | four sites agree; all omit #2013 |
| Soak stamped 00:33; 62 / 210 / 178 / 429; 10 findings (2 true, 8 false); 65 PRs at 00:50 | consistent: `ci.yml:1627-1630`, `WALKTHROUGH:285-286`, `HANDOFF:29, 121-123, 714-722` |
| Round 1 matched "7 of 8" pinned rows = "8 of 9" repos | consistent: `tests/test_safe_merge.py:38-39`, `HANDOFF:687, 932, 999` |
| Budgets; 4 of 9 at the ceiling | consistent: `util/safe_merge.py`, `HANDOFF:96`, `docs/REFERENCE.md:3292` |
| `.github/workflows/lockfile-update.yml`, `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` | state none of the round-3 figures |

Round 4 changes a NUMBER / DISPOSITION / ACTION: yes -- ACTION (NON-OWNER 1's example, control and stated remaining cost; the walkthrough's promotion recipe); no number or disposition changes.

**Changed:** nothing tracked.

**Created** (untracked), in `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round4-laneA/`:
- `r4a_budget_history.py`
- `r4a_run_34293438446.py`
- `r4a_ml_window.py`
- `r4a_soak.py`
- `r4a_soak_lag.py`
- `r4a_replay_fidelity.py`
- `r4a_fence_census.py`
- `r4a_fence_census2.py`
- `cache/` (56 files)
- `__pycache__/`
