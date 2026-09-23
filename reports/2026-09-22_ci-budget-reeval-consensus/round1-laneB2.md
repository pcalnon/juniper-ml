# CI-budget re-evaluation -- consensus round 1, Lane B2 -- argue HOLD on the budget re-pin

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

I recommend HOLD on the three budget raises. The PR names runner queueing as their cause, and the same `util/safe_merge.py` comment block says not to raise a budget to absorb a queue. I measured that queue: the three maxima that forced the raises are 64-82% runner-queue time.

Documents referenced: the frozen re-evaluation `HANDOFF_frozen_round1.md` (scratchpad `round1/`), `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`, `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2. Code is cited at PR head `53d05121`.

## F1 (critical): the three raises absorb a runner queue

My probe splits each second of a head's required-context span into "some job executing" or "nothing executing, a job waiting for a runner" (queue).

| head | pass start (UTC) | span | executing | queue only | longest single-job queue |
|---|---|---:|---:|---:|---:|
| data#405 | 09-21 13:10 | 2589 | 934 | 1654 (64%) | 786 s |
| data-client#206 | 09-21 13:13 | 2565 | 503 | 2061 (80%) | 1077 s |
| deploy#211 | 09-11 08:54 | 965 | 174 | 790 (82%) | 888 s (Gitleaks: queued 888 s, ran 5 s) |

The same split over each repo's full 30-head window (raw → with queue-only seconds removed):

| repo | p90 | max |
|---|---|---|
| data | 1651 → 795 | 2589 → 1085 |
| data-client | 1545 → 410 | 2565 → 504 |
| deploy | 450 → 175 | 965 → 225 |

- My raw figures match the author's exactly, so this is the same quantity.
- **The 4×p90 bound is inflated too.** The four heads that set the p90 are 38-84% queue in all three repos.
- **Queue removed, the old budgets pass and the new ones fail.** data's window is (1085, 3180]: 2400 is inside it, 3300 is above 4×p90. deploy's queue-free 4×p90 is 700, exactly the old budget; 1400 is double it. data-client's old 2400 was already 4.8× its queue-free max.
- **The file's own rules argue against the raise:**
  - `safe_merge.py:191-194` says a budget must clear the typical worst case and "FIRE on a pathological tail". "Clear the max" was adopted because the old tail "was an instrument artifact". These tails are real runner starvation, so that premise is gone.
  - `:266-268` says "do NOT raise a budget to absorb a queue … let the net carry the tail".
  - `:261-264` calls a refusal under contention "the design working".
  - The new text at `:240-241` names queueing as the cause and raises anyway.
- **One burst, counted repeatedly.** data#405 started 13:10:36, data-client#206 13:13:15, and cascor's own max (#660) 13:10:20 on 09-21. data #406/#407, data-client #207 and deploy #222/#224 share 09-21 19:22-19:51.
- **Every re-measure so far has raised a budget.** ml 1500→2800, cascor 2400→2800, recurrence 700→2000, now three more; none has been lowered. Four of nine repos now sit at `TIMEOUT_CEILING`.
- **Steelman for SHIP:** during bursts, holding means `safe_merge` exits 2 on healthy PRs and relies on the net. But a larger budget does not fix the BEHIND state (`allow_update_branch` is false) either.

**Action:** revert the three `REPO_TIMEOUTS` raises. The conflict between the enforced "&gt; observed max" test and "do NOT absorb a queue" is an owner ruling. The options are sizing on span minus queue, or on uncontended heads.

## F2 (major for the record, minor for verdicts): `rerun-split` misclassifies 13 of 18 set-aside heads

- **13 are `Guard PR base branch` success→success, 7-142 s apart.** The guard fires on six event types, including `edited`/`labeled`/`unlabeled`, and has no concurrency group by design. `pr-base-branch-guard.yml:64-72` calls the duplicates "BENIGN".
- **Only 4 are failure-driven re-runs:** canopy #653/#651/#636 and cascor #647.
- **recurrence #175 involves no failure:** a cancelled run, a success 56 s later, then a later trigger on an already-green head.
- So the stated justification ("safe_merge reports a failure when it happens") covers 4 of 18.
- **The recorded `n` values are wrong.** data, data-client, deploy, cascor-worker and cascor-client are all 30/30 clean.
- **cascor's recorded p90 is wrong.** Its window reads 2221, 1743, 1735 (#656, a guard head), 1717. The author's p90 is 1615; setting aside only #647 gives 1717.
- **No verdict flips in this sample.** The largest guard head (1735) is below every max.
- **The bias carries forward.** `docs/REFERENCE.md` and the v2 docstring now say "size budgets from rerun-split", which will drop every PR edited or labelled mid-pass.

**Action:** only set a head aside when the earlier run ended non-success; fix the `n` values and cascor's p90; stop calling these heads "re-runs".

## F3 (major): the cause is asserted, not measured

"Stretched by within-span queueing on the contended … windows" has no measurement behind it: the reprobe script never reads job `created_at`. The file withdrew this kind of causal claim on 09-10 ("the span cannot separate them", `safe_merge.py:285-288`, `:343-348`). It happens to be true (F1), but measuring it undercuts the raise. **Action:** add the evidence and resolve F1, or delete the clause.

## F4 (minor): the waiter default

- **Mechanically benign.**
  - `safe_merge.py` has no import-time side effects, no dataclass, and no circular import (it calls the waiter by subprocess).
  - Nothing is registered in `sys.modules`.
  - All three in-repo callers pass `--timeout`, so none sees the new stderr line: `safe_merge` (≈`:795`), `util/ad-hoc/2026-08-24_bot_pr_merge_sweep.py:122` (150 s), and `util/ad-hoc/watch_prs_until_terminal.bash`.
- **It inherits F1.** The direct waiter would now default to 3300 s on data and data-client. It has no signal handling and no net. Under the ~3600 s lease, a background waiter on a spare worker that is already partly used gets killed silently instead of exiting 2 honestly.
- **Near miss.** `watch_prs_until_terminal.bash` pipes stderr into `jq` (`2&gt;&amp;1`) and survives only because it passes `--timeout`. Its hard-coded 2400 s still undercuts six budgets, the same defect class, and the PR leaves it alone.
- **"DROPPED by the 09-17 arc" is unfair.**
  - The walkthrough's scope is "the five owner decisions executed".
  - Item 10 was a non-owner "Minor, verified … merge path is unaffected" note.
  - The original handoff's §5 round-2 correction 3 (line 240 at head) confirmed "does not affect the merge path at all".
  - "Not carried forward" is the accurate phrase.

## F5 (minor): other overclaims

- **"0 breaches since 2026-09-17" on all nine repos.** The probe counts `::warning::` annotations, but juniper-ml's copy emits none on a breach (`pr-budget-alarm.yml:136-166`; walkthrough §4.1). The claim is true: juniper-ml's job logs for 09-16..09-22 show 7 runs, all `level=OK`, at most 9 open PRs against a warn threshold of 15. The author's instrument just could not have shown a breach there.
- **"The exact risk ml#1955's ci.yml comment named".** `ci.yml:1620-1621` names prose opening with `make` or `cd`. That covers #2007, not #1980's `git).`.
- **"KillResilienceTest stayed green".** True by construction, not observed. Better phrased as "could not go red".

**Claims that survived:**
- "Every required context ran once and passed": no context had more than one check-run on #405, #206 or #211.
- "Would have failed 7 PRs": all seven false findings were present at each PR's merge head.
- The lockfile "created, not suppressed" correction: #1932's runs were created at 08:26:10Z, 4 s after the PR opened, under `github-actions[bot]`.

## Recommendations

- **(a) The three budget raises: HOLD.**
- **(b) The `MEASURED_SPANS` refresh: HOLD as written.** Its three rows force the raises through the "&gt; max" test, and the `n` values and cascor's p90 are wrong. Re-measure with a failure-only classifier and a queue-aware statistic after the owner rules.
- **(c) The waiter default: HOLD while it is bundled with (a).** If (a) is settled, it can SHIP separately, with "DROPPED" re-worded and the lease exposure documented.
- **(d) Doc/comment corrections: SHIP** the lockfile mechanism fix, the stale `docs/REFERENCE.md` budgets row, and the v2 "KNOWN DEFECT" note once F2's wording is fixed. **HOLD or re-word** the unmeasured queueing clause, the "re-run heads set aside" wording, and "DROPPED".

**Changed** (new, uncommitted, read-only GitHub probes):
- `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB2/span_decompose.py`
- `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB2/window_queue_share.py`

Scratch data in the scratchpad: `laneB2_pr2017.diff`, `laneB2_safe_merge_head.py`, `laneB2_ml_prs.json`.
