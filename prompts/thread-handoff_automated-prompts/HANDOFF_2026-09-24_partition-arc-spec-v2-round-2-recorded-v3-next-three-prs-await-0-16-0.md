# Thread handoff: partition-arc residue, part 2. The Decision 12 spec v2 failed review round 2 and is recorded; v3 is next, and three PRs wait on juniper-data v0.16.0

**Date**: 2026-09-24. This supersedes an unpublished 2026-09-23 draft of this handoff.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md`
**Why now**: the harness compacted this thread once already. CLAUDE.md treats that as a handoff that should already have happened. A logical phase also closed: review round 2 of the spec is recorded, and the v3 fold is a context-heavy phase of its own.

## 1. Goal for the next thread

```text
Continue the partition-arc residue in the Juniper ecosystem. Read, in order: juniper-ml
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md
(the predecessor, whose five agent-doable items this thread worked), then this file,
HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-recorded-v3-next-three-prs-await-0-16-0.md.

Completed (2026-09-23, this thread):
- juniper-data#430 MERGED (90ad035e): arc_agi's task_ids are stored as <U, arc_agi VERSION is 4.0.0,
  and a fleet test loads every generator's artifact with np.load(allow_pickle=False). #429 and #427
  closed with it. Predecessor item 2.
- juniper-recurrence#185 MERGED (ca9609f0): the bench lane's concurrency group now ends with the
  dispatch payload version (the first residual gap on recurrence#178). Predecessor item 3, half 1.
  #185's body said "Neither closes #178", and GitHub closed #178 on merge anyway. #178 is REOPENED,
  with a status comment.
- Spec v2 (notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md, 0.2.0) in
  juniper-ml#2060, MERGED as 0f269c2b. It folds round 1's 14 findings, and comes with a reference gate
  (util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py: 52 PASS / 0 FAIL / 0 SKIP at
  juniper-data 90ad035e), a dtype inventory, and a citation checker (139 rows, 0 failures).
  REVIEW ROUND 2, four lanes frozen at 8c9d65f: v2 is NOT ratifiable. Ten MAJOR clusters, R2-1 to
  R2-10, are recorded in the spec's §15, and the four reports are archived verbatim under
  reports/partition-provenance-spec-v2-review-2026-09-23/. Predecessor item 1, first round.
- juniper-ml#2034 (decision 4): the step-1 inventory is posted on the issue, and step 2 (markers) is
  juniper-ml#2066. There is also a marker comment on juniper-cascor#578. Filed juniper-ml#2064: a run's
  stats.json, stats.md and eval_metrics.png report the IN-LOOP val scores, not eval_metrics.final.
- juniper-cascor#677 (V-3): the plan is posted on the issue. It uses three arms, derives arm A from
  arm B's network, and is not run yet. Predecessor item 5.
- juniper-data-client#213: posted a per-receiver correction of that issue's own framing.
- juniper-data#423 (Decision 12): posted round 2's outcome.
- Review round 3 (lane D) of the three PRs' correction commits:
  - #434: MERGE. Two of its three NITs are fixed, UNCOMMITTED (see §3). The third, the unlocked
    warned-id set, is benign and was not fixed.
  - #431: MERGE-WITH-FIXES. Its MINOR: a partial outage was still blamed on the consumer. Fixed in
    4b0d0a97 and tested on 7 cases.
  - #212: MERGE.
  #431 and #434 are now DRAFT, so no unseen actor can auto-merge them before the cut.

Remaining, agent-doable (merge approval is per-session: ask the owner for it again):
1. Spec v3. Fold §15 of the spec (R2-1..R2-10, then the MINORs and NITs, each traceable to a lane id
   in the archived reports) into §1-§13. Add a round-2 disposition table in the style of §14.
   Decisions v3 has to carry:
   - The block ships in juniper-data 0.17.0, because 0.16.0 is taken by #433.
   - W10 has a precondition: a juniper-recurrence release that carries W4's widened cap, plus an
     `[all]` dry-run resolve.
   - W11 and FIRST_EMITTING_VERSION are conditional on OQ-1 = yes, and the "no" branch is written out.
   - The "0.6.1 is a PATCH" argument is dropped. Release 0.7.0 instead, or put it to the owner in §16.
   - The status, override and caveat surfaces are named for each consumer.
   Update the reference gate so it has a vector for every R2 cluster, notably R2-1 (an unknown scheme
   with a changed core must be `unverifiable`, not refused). Move the citation checker's pins:
   juniper-data main is at 7125e16 (0.16.0's proposal), and cascor main moved at 0e016a7c, which
   shifted the manager.py lines. Then run ROUND 3 with fresh lanes on frozen text, and only then
   ask the owner to rule on anything in §16.
2. juniper-data#431, then juniper-data#434: merge ONLY after the owner cuts juniper-data v0.16.0.
   Both are DRAFT; run `gh pr ready` after the cut. Commit and push #434's uncommitted round-3
   fixes first (see §3).
   Neither is in 0.16.0's approved scope, which ends at 90ad035e; check with
   `gh release list -R pcalnon/juniper-data`. #434's CHANGELOG will conflict with #431's under
   [Unreleased]: keep main's entries verbatim first. After each merge, check that main's tree
   matches the PR head for the PR's files.
3. juniper-data-client#212: mergeable now. It does not depend on the release, and its workflow
   comment no longer depends on the merge order. Round 3 rated it MERGE. Two optional NITs:
   - 4 of cascor's 7 cancelled dispatch runs were cancelled by other dispatch runs, not pushes, so
     the comment should say "a later run in the receiver's concurrency group";
   - the three POSTs have no --max-time.
4. Merge juniper-ml#2066 (the markers). #2060 is merged: check its Post-Merge Main Verification run
   with `gh run list -R pcalnon/juniper-ml --commit 0f269c2b`.
   Round 2's outcome is already posted on juniper-data#423; post again there when v3 is reviewed.
5. #2064: surface eval_metrics.final (with its split and n_samples) in
   util/experiments/stats_summary.py:225 and plots_cascor.py:195, and label the in-loop scores.
   Add tests. That unblocks #2034 step 3, the re-measurement, which must pin sizing_mode: carve.
6. V-3 compute, only once the perf lane is quiet. Follow the plan on juniper-cascor#677.

Owner-only (never do these, and never approve deploy gates):
- Release cuts. juniper-data v0.16.0 (proposal #433 merged; ships #420, #421, #426, #422 and #430;
  BREAKING for store callers), juniper-cascor (ships #672), juniper-canopy (ships #663).
  juniper-ml 0.10.0 is cut.
- Widen CROSS_REPO_DISPATCH_TOKEN (the PAT in juniper-data) to pcalnon/juniper-recurrence with
  Contents: Read and write, and Actions: Read. Then run
  `gh workflow run notify-consumers.yml -R pcalnon/juniper-data -f version=0.15.0`.
  recurrence#178 closes only when that run and the bench run it starts are both green.
- juniper-data#424: does §6.2's generate-shortfall survive decision 9?
- Whether to close juniper-cascor#582, with #677 as its residue.

Key context:
- A closing keyword before #N closes the issue even inside a negation, and a bare #N means the PR's
  OWN repo. Scan every PR body before merge (the recipe is in memory,
  reference_negated_closing_keyword_still_closes.md).
- util/safe_merge.py can exit 0 having REFUSED ("went BEHIND 3 times"). Read its log for MERGED.
  In a contended lane: arm native auto-merge with no body flags, then run update-branch once.
- A release proposal that merges under an open PR moves that PR's [Unreleased] bullet under the
  release heading, and the merge reports no conflict. Move your bullet to a new [Unreleased].
- Freeze an artifact while a lane reviews it. This thread broke that once, on #434 at 4e38930.
```

## 2. Verify the starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch -q origin && git log --oneline -1 origin/main
# one plain command per PR (a worktree-isolated session refuses loops that run gh with computed arguments)
gh pr view 2060 -R pcalnon/juniper-ml          --json state,mergedAt,headRefOid
gh pr view 2066 -R pcalnon/juniper-ml          --json state,mergedAt,headRefOid
gh pr view 431  -R pcalnon/juniper-data        --json state,mergedAt,headRefOid   # head 4b0d0a97, DRAFT
gh pr view 434  -R pcalnon/juniper-data        --json state,mergedAt,headRefOid   # head ac6bdc8, DRAFT; fixes uncommitted (see §3)
gh pr view 212  -R pcalnon/juniper-data-client --json state,mergedAt,headRefOid
gh release list -R pcalnon/juniper-data --limit 1        # v0.15.0 until the owner cuts v0.16.0
gh issue view 178 -R pcalnon/juniper-recurrence --json state --jq .state   # OPEN
git show origin/main:notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md | grep -c '^| \*\*R2-'   # 10
/opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py --data-checkout /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--verify--spec-v2-pin--20260923-1545--90ad035e | tail -1   # 52 PASS, 0 FAIL, 0 SKIP
python3 util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py | tail -1   # 0 failures at the v2 pins
curl -s https://pypi.org/pypi/juniper-data/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"   # repeat per package
# expected at handoff: juniper-ml 0.10.0, juniper-data 0.15.0, juniper-cascor 0.11.0, juniper-canopy 0.8.1, juniper-data-client 0.5.0
```

## 3. Git status at handoff

- **juniper-ml.** Worktree `.claude/worktrees/warm-prancing-yeti`, on `docs/decision-4-pre-switch-markers` (#2066, pushed at `42cef7cd`). The unpublished 09-23 draft of this handoff is untracked there.
- **juniper-data#431.** Worktree `worktrees/juniper-data--ci--notify-consumers-confirm-run-started-178--20260923-1500--ce436819`, pushed at `4b0d0a97`, clean.
- **juniper-data#434.** Worktree `worktrees/juniper-data--fix--arc-agi-task-ids-unicode-429--20260923-1422--ce436819`, pushed at `ac6bdc8`. **Two files are UNCOMMITTED**:
  - `CHANGELOG.md`: `/versions?name=` returns every version; `/latest` returns only the newest.
  - `juniper_data/tests/unit/test_cached_store.py`: both traceback assertions now require `record.exc_info and record.exc_info[0] is not None`.
  The test file passes (30 tests), and all four exc_info mutants are killed. Commit and push both before `gh pr ready`.
- **juniper-data-client#212.** Worktree `worktrees/juniper-data-client--ci--notify-downstream-fail-loudly-211--20260923-1500--9bc8870f`, pushed at `80ae41d`, clean.
- **The pin worktree** `worktrees/juniper-data--verify--spec-v2-pin--20260923-1545--90ad035e` is detached and read-only. Keep it for v3.
- **Lane D's report was not archived.** Its findings are the ones summarised in §1.

## 4. Traps this session hit

- **A negated closing keyword still closes.** #185's "Neither closes #178" shut recurrence#178 when #185 merged at 20:22:55Z. The first rewording of #431's body then said "closed #178", which is also a keyword. The keyword list is close, closes, closed, fix, fixes, fixed, resolve, resolves and resolved.
- **A release proposal merged under two open PRs.** juniper-data 0.16.0's #433 moved #430's and #426's entries under `[0.16.0]`. #434 and #431 had edited those entries in place, and git merged the edits into the released section **without a conflict**. Both PRs now restore `[0.16.0]` to main's bytes and carry their own `[Unreleased]` bullets.
- **Sequence Safety counts a same-file test rename as a LOST test.** #434's round-1 commit renamed `test_a_non_string_task_id_is_stored_as_its_text`, and the required check failed. The fix restored the name; it did not waive the loss.
- **`safe_merge.py` exit 0 was a refusal**: "#2060 went BEHIND 3 times without a stable green head". The recovery was native auto-merge, SQUASH, with `commitBody` null and `--match-head-commit`.
- **A runner transient looks like a PR failure.** #431's unit job failed on `git clone … server certificate verification failed`. `gh run rerun --failed` cleared it.
- **The freeze slip.** This thread merged main into #434 and committed while lane C was reviewing 4e38930. Lane C noticed and reviewed both heads, but a lane that did not notice would have reported on the wrong code.
- **`exc_info=False` passes `record.exc_info is not None`.** Lane D's M09 mutant survived that check. Assert `exc_info and exc_info[0] is not None` instead.
- **jq exits 0 on an empty body.** Without `jq -e` and an explicit shape test, an empty 200 reads as a clean listing.
- **The memory index is at its load limit**: 24,966 of about 25,000 characters. A new pointer needs an equal trim, following `feedback_memory_index_target_is_20kb.md`: retire entries, never strip hazard hooks, and gate on the link-set tool.

## 5. What this evidence cannot support

- **The reference gate is an implementation of v2's text, not of a shipped gate.** Its 52 passes show the text is implementable and survives the vectors. Round 2 then found defects that the vectors did not cover, such as R2-1, the unknown-scheme path.
- **#431's confirmation step has never run in Actions.** The dispatch 403s until the owner widens the token, so the step is tested only locally, on four cases.
- **V-3's "arm A = arm B's network" rests on reading the code.** The plan's identity check (B against B′ at 0.8/0.05/0.15) is what would confirm it, and it has not been run.
- **The #2034 inventory is one agent's sweep.** Two of its load-bearing claims were re-checked against run directories: T6's `split: "validation"` with no `final` block, and #2064's figures, 0.9187 in-loop against 0.8997 held-out. The rest are as the agent reported them.

## 6. Documents referenced and changed

**Referenced**: the predecessor handoff named above; `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` (§7, §8, §9.1); `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md` (§2, V-2); `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.

**Changed in juniper-ml**:
- `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` (v2, plus §15), and `reports/partition-provenance-spec-v2-review-2026-09-23/` (`README.md`, `S1-grounding.md`, `S2-soundness.md`, `S3-executability.md`, `S4-fold-completeness.md`), all in #2060.
- `util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py`, `…_dtype_inventory.py`, `…_v2_citation_check.py` and `2026-09-23_extract_agent_final_reports.py`, in #2060.
- In #2066: `docs/REFERENCE.md`, `util/snapshot_attribute.py`, `util/ad-hoc/2026-09-23_decision4_pre_switch_markers.py`, and six notes:
  - `JUNIPER_2026-08-09_…P4-STUDIES-EVIDENCE.md`
  - `JUNIPER_2026-08-14_…R3-EA-RERUN-EVIDENCE.md`
  - `JUNIPER_2026-08-14_…E-I-CAP-CEILING-EVIDENCE.md`
  - `JUNIPER_2026-07-29_…EXPERIMENTATION-PLAN.md`
  - `JUNIPER_2026-08-08_…P3-ACCEPTANCE-ROLLUP.md`
  - `JUNIPER_2026-08-24_JUNIPER-CASCOR_ATTRIBUTION-NULL-MODEL-FINDINGS.md`
- This handoff.

**Changed in juniper-data**: `juniper_data/generators/arc_agi/generator.py`, `juniper_data/storage/cached.py`, `juniper_data/tests/unit/{test_artifacts_load_without_pickle,test_arc_agi_generator,test_cached_store,test_val_emission_guards}.py`, `.github/workflows/notify-consumers.yml`, `CHANGELOG.md`. These are in #430 (merged), #434 and #431.

**Changed in juniper-data-client**: `.github/workflows/ci.yml` and `CHANGELOG.md` (#212). **In juniper-recurrence**: `.github/workflows/ci-recurrence-bench.yml` (#185, merged).

**Memory**: `reference_negated_closing_keyword_still_closes.md` is new, and `MEMORY.md` was trimmed with no pointer dropped (222 before, 222 after).
