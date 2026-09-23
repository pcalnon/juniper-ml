# CI-budget re-evaluation -- consensus round 1, Lane A2 -- the CI spans, re-measured by an independent instrument

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

**Lane A2 report: required-check spans re-measured from every execution on each head (not `filter=latest`)**

Most of the claims hold, and no budget at 53d05121 breaks the sizing rule under my numbers. The claims' re-run rule does have one real defect, though it changes no verdict in this sample.

**Instrument.** I wrote my own scripts and did not reuse the v2 tool or the reprobe tool. They read three sources:
- `check-runs?filter=all` for every execution of each required context.
- `actions/runs?head_sha=` to tie each check run to its workflow run, trigger event and run attempt.
- `actions/runs/&lt;id&gt;/jobs?filter=all` to get the attempt number of each job, and to split each job's wait into queue time and run time.

Other details:
- **Required contexts:** in all 9 repos, the union of ruleset contexts equals what `rules/branches/main` reports. No repo has classic branch protection.
- **Coverage:** every required context was found as a check run, so no legacy commit statuses were needed. All 270 heads were fully measurable.
- **`filter=latest`:** I called it directly only on the 21 heads with duplicate names, where it is the literal v2 input.
- **Cost:** about 700 REST calls.

**My re-run rule.** A context counts as repeated when a later execution starts at or after an earlier one on the same head has finished. Two exclusions:
- **Copies:** "re-run failed jobs" copies the jobs that passed into the next attempt with identical timestamps. Those copies are not new executions.
- **No heads are dropped for a repeat.** Instead each head gets a **first-pass span** (the first execution of every required context). A head counts as healthy if every first-pass execution passed (success, skipped or neutral).

Why: the budget is spent on one pass. A repeat after a healthy pass does not change what `safe_merge` waited for. A failed or cancelled first pass is not a healthy pass at all.

### Per-repo numbers (p90 / max / n; p90 = sorted[int(0.9·(n−1))])

| repo | budget | raw (literal `filter=latest`) | claims' rule (drop any head with a repeat) | first pass, healthy heads | claimed |
|---|---|---|---|---|---|
| ml | 2800 | 857/1061/30 | 857/1061/30 | 857/1061/30 | 910/2005/30 |
| canopy | 3300 | 1850/**33299**/30 | 1798/2174/26 | 1798/2174/27 | same as mine |
| cascor | 2800 | 1717/2221/30 | 1615/2221/27 | **1717**/2221/29 | same as mine |
| cascor-client | 3300 | 1264/1626/30 | 1264/1626/28 | 1264/1626/30 | same as mine |
| cascor-worker | 2400 | 1576/2059/30 | 1576/2059/29 | 1576/2059/30 | same as mine |
| data | 3300 | 1651/2589/30 | 1651/2589/28 | 1651/2589/30 | same as mine |
| data-client | 3300 | 1545/2565/30 | 1545/2565/28 | 1545/2565/30 | same as mine |
| deploy | 1400 | 450/965/30 | 450/965/29 | 450/965/30 | same as mine |
| recurrence | 2000 | 1119/**9886**/30 | 1114/1666/27 | 1114/1666/29 | same as mine |

When I apply the claims' rule, I match their clean figures exactly on 8 of 9 repos.

The juniper-ml difference is sample drift, not a measurement error:
- My sample is #1982–#2016. That is also the sample at 20:30:02Z, when 53d05121 was committed.
- The claimed 910/2005 comes out exactly when #1981 is in the sample instead of #2016. #1981 is a clean single pass of 2005 s. #2016 merged at 20:18:20Z.
- So one PR at the edge of the sample doubles ml's max. The verdict holds either way: 2800 fits both (2005, 3640] and (1061, 3428].

### Verdicts

**(a) Both are re-run tails. canopy#653: CONFIRMED. recurrence#175: CONFIRMED, but the description is inaccurate.**
- **canopy#653:** a literal `filter=latest` call reads 33,299 s.
  - Attempt 1 of ci.yml run 35712920481: `UI Sub-suite (Playwright)` failed at 09:58:37Z and `Quality Gate` failed at 10:08:23Z.
  - Attempt 2 (pcalnon) started at 19:01:37Z. It re-ran those two contexts, which finished at 19:08:22Z.
  - The other 16 ci.yml contexts were copied into attempt 2 with their original timestamps. That is why the span still starts at 09:53:23Z. The first-pass span is 900 s.
- **recurrence#175:** a literal `filter=latest` call reads 9,886 s. It is a dependabot PR.
  - The "~743 s pass" (19:15:43→19:28:06Z) was not a clean pass. Two sets of workflow runs fired on the same commit 1 s apart. Concurrency cancellation cancelled 5 required contexts, and all 4 `* required checks` aggregator jobs failed.
  - The tail 2.5 h later is attempt 2 of ci-pre-commit run 35643700110, whose attempt 1 had been **cancelled**. pcalnon re-ran it at 21:59:28Z, and the PR merged 4 s after it passed.
  - So this is the same kind of event as #653: a manual re-run to clear a required check that had not passed, not a routine extra run.

**(b) CONFIRMED, with one wording error.**
- data#405, data-client#206 and deploy#211 are single passes. Every workflow run on each head is attempt 1, and each required context has exactly one check run. The raw figure equals the clean figure on all three.
- The wording error: data#405's required `Slow Tests` was **skipped**, so "every required context ran once" is false for 1 of its 22 contexts.
- "Stretched by within-span queueing" is correct and, if anything, understated. I walked the longest dependency chain for each head from the jobs API (queue = job start minus job creation):

| PR | span | time waiting in queue | time running |
|---|---|---|---|
| data#405 | 2589 s | 2355 s (91%) | 231 s |
| data-client#206 | 2565 s | 2383 s (93%) | 180 s |
| deploy#211 | 965 s | 955 s (99%) | 9 s |

- On deploy#211, `Gitleaks` waited 888 s in the queue for a 5 s job.
- data#405 and data-client#206 ran in the same window (2026-09-21 13:10–13:56Z). One contention episode produced two of the three raises.

**(c) No budget fails the rule under my numbers.**
- All nine budgets are above the healthy max and at or below 4×p90 under both clean columns. That also holds under three sample definitions: by creation now, by creation at the 20:30Z cutoff, and by merge time (where ml reads 910/1450 and data's p90 is 1541).
- The pre-raise values on origin/main (data 2400, data-client 2400, deploy 700) do fail. So the three raises were needed.
- **Thinnest margin:** recurrence has 2000 − 1666 = **334 s**, not cascor-worker's 341 s as the comment in `util/safe_merge.py` says.

**(d) CONFIRMED that the claims' rule misclassifies heads; no verdict flips.**
- Of the 18 heads the claims set aside, only 5 had a real re-run or cancellation: canopy#653, #651, #636, cascor#647 and recurrence#175.
- The other **13** had a first pass that fully passed. Their only "repeat" is `Guard PR base branch` being triggered again by a later PR event: a new workflow run, attempt 1, both runs successful, finishing inside the pass. Raw span equals first-pass span on all 13.
  - The 13: canopy#646; cascor#663, #656; cascor-client#150, #143; cascor-worker#188; data#420, #414; data-client#184, #182; deploy#202; recurrence#174, #150.
  - The timelines of data#420 and cascor#656 show no label or rename. That is consistent with an `edited` event from a PR body update (my inference).
- The aggregator jobs (`* required checks`, `Quality Gate`) repeated only on the 5 genuine heads.
- None of the 13 is a repo max; the largest is cascor#656 at 1735 s against a max of 2221. So no max moves. What does change: cascor's p90 is 1717 rather than 1615, and every clean n is understated.

### Could my instrument have produced a different answer?
Yes, and in three places it did:
- the juniper-ml max;
- how `filter=latest` removes duplicates (see defect 2);
- the n values and cascor's p90.

My exact agreement on 8 repos under the claims' rule is an independent re-coding of the same rule on the same sample. It shows their code does what it says, not that the rule is right.

Limits:
- Both instruments read the same GitHub records. Where I compared them, the jobs API and the check-runs API gave identical start times.
- Timestamps have 1-second resolution.
- Each max is a single observation.

### Defects, most severe first
1. **Medium:** the claims' rule drops healthy heads (13 of 18). That is the unsafe direction, since dropping heads can only hide a healthy max. It is not biting in this sample. A rule keyed on attempt &gt; 1 or on "first pass did not pass" would avoid it.
2. **Medium-low:** the claimed mechanism is only half right. `filter=latest` keeps the latest check run per name **within each workflow run** (verified on 21 of 21 heads). So a re-run attempt does replace the earlier attempt, but a workflow run triggered again by a new event is not replaced and still enters the v2 span.
   - Example: recurrence#175's 9,886 s includes 50 s from the cancelled set of runs; keeping only the latest per name would give 9,836.
   - Consequence: a fix that deduplicates by name, or drops attempt &gt; 1, would not remove tails caused by a new trigger.
3. **Low:** the ml figure depends on one PR at the edge of the sample. The sample is also ordered by creation, not merge time.
4. **Low:** the "thinnest margin in the table" comment in `util/safe_merge.py` at 53d05121 is wrong (334 s &lt; 341 s).
5. **Low:** "every required context ran once and passed" is false for data#405.
6. **Low:** the recurrence#175 description hides the cancelled and restarted runs.

**For Lane B:** the three raised budgets now cover spans that were 91–99% runner queue. That sits uneasily with the comment's "do NOT raise a budget to absorb a queue", even though its note on juniper-ml puts queueing inside the span in scope.

### Files
- **Documents referenced:** `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (§2 Lane A); `util/safe_merge.py` and `tests/test_safe_merge.py` (`MEASURED_SPANS`) at 53d05121; and the docstring of `util/ad-hoc/2026-09-08_measure_required_check_span_v2.py` (docstring only).
- **Changed:** no existing file. I ran `git fetch origin` as instructed.
- **Created** (all new and uncommitted, in `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneA2/`):
  - `span_all_attempts.py` (main measurement)
  - `latest_semantics.py`
  - `queue_share.py`
  - `sample_drift.py`
  - `sample_order_sensitivity.py`
  - `show_at_commit.py`
  - `lane_a2_evidence.json`
  - `lane_a2_cutoff_samples.json`
- **Raw API cache:** `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad/laneA2-cache/` (49 MB).
