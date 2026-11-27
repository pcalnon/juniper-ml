# Round-5 review brief: the cascor sweep's third fix pass (tree `cascor-r4`)

Written 2026-11-23 by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`). Give this file, unedited, to
ONE fresh reviewer (a `general-purpose` agent). Paths:
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Stopping rule.**
- A BLOCKER or MAJOR finding is fixed in the writer or checker, the final tree is regenerated as `cascor-r5`, and that
  interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- The landing step goes ahead only after a round with no BLOCKER and no MAJOR.

## The prompt

Round-5 adversarial review of a FIX PASS (the third) on juniper-cascor's publish sweep and on the cross-repo checker that
gates the ports into seven other repos. Review ONLY what the fix pass changed, plus anything it could have broken. Treat
the fix pass as the least trustworthy part.

**Frozen trees (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r5review/`;
never write under `/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- Fix pass 3, under review: `$W/tmp/sweep/cascor-r4/juniper-cascor` (cascor `802399ab` plus a working-tree diff).
  `$W/tmp/sweep/cascor-r4/sweep.diff` must hash to sha256
  `f056c538f8600d007ab721793eedb2f6a5ad59215f2b7d57fe49629ebe5abaa4`. If it does not, STOP and report.
- The same writer on cascor `main` at `e9c86f83` (which includes the merged rename cascor#772), "base B":
  `$W/tmp/sweep/cascor-r4/main/juniper-cascor`, diff `$W/tmp/sweep/cascor-r4/main/sweep.diff`, sha256
  `a63991221c1f66a57aa59bd95ea7c7b4d5c1d0630e3b43788b18352f4f1fb42e`. What lands is this writer's output on the
  `main` of the landing day.

**cascor `main` has moved since base B** (read 2026-11-23 22:28Z): #774 (`829af03d`, 27 files, none of the sweep's
eleven; fix pass 3 reports the writer's output identical there) and #776 (`36dd6f2d`, which DOES touch `CHANGELOG.md`,
one of the eleven). Step 3 below therefore runs the writer on a newer `main`: every difference must be explained by
those merges, and the sweep's CHANGELOG entry must still sit correctly under `[Unreleased]`.
- Fix pass 2, already reviewed by round 4: `$W/tmp/sweep/cascor-r3/juniper-cascor`, diff sha256
  `e02b4da8bfbe1a99c2b46e0c23e66f91cbaf884c7d5bf7a79f957cb63e3cb525`.
- The interdiffs: `$W/tmp/sweep/cascor-r4/r3_to_r4.diff` (cascor), `$W/tmp/sweep/cascor-r4/checker_r3_to_r4.diff`,
  `$W/tmp/sweep/cascor-r4/writer_r3_to_r4.diff`.

**Checker.**
- Under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `c826ab875ecb5d6ad95891e341fb3b27020cfddf25d0161a4a44e04c74f88236`.
- As round 4 reviewed it: `$W/tmp/sweep/cascor-r4/checker_r3_as_reviewed.py` (sha256 `2feceecf…`).
- Usage: run it with `--help` first; fix pass 3 may have added a required argument.

**Writer.** `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`, sha256
`3f1d3ead6fbd29537ae20388f99c77ad63cd0a1cb9429e1f65f1fc5488a3e952`; as round 4 reviewed it:
`$W/tmp/sweep/cascor-r4/writer_r3_as_reviewed.py`.

**Also open to you:** the executor's tools and evidence in `$W/tmp/sweep/cascor-r4/` (`rerun_all.bash`, `evidence/`,
`checker_proof_r4.py`, `port-sim/`, `mutants-new/`), the draft `pr_body.md` and `commit_message.txt` there, and its
account of base B against round 3's `work-after772` (`evidence/account_base_b.log`). Re-run rather than trust them.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: the "Round-4 review" table (R4-2, R4-3,
R4-4, R4-6 and the NIT rows; R4-1 and R4-5 are port items, out of scope here) and the "Fix pass 3" section (what was
applied, rules added beyond the review, relaxations). Scrutinise the added rules and EVERY relaxation hardest: a
relaxation that reopens a bypass is a MAJOR.

**Expected, by design:**
- the test-lens harness's C4, D1 and D2 fail;
- the suite's H2d, H2e, H4 and H10 edits fail;
- a JOB-level `concurrency` now fails (R4-4); a workflow-level non-cancelling `concurrency` passes;
- the person-word differs between the two bases ("owner" at `802399ab`, the renamed wording on `e9c86f83`).

Do these, in order:

1. **The delta.** Read every hunk of the three interdiffs. Hunt new bugs:
   - does any fix change behaviour beyond its finding?
   - is any added rule wrong, over-strict (it rejects a legitimate port) or bypassable?
   - does the base-B tree differ from base A in anything except the person-word and what #772 changed?

   Run `actionlint` (`/opt/miniforge3/envs/JuniperCascor1/bin/actionlint`) on the three workflows of both trees.
2. **Tests.** From a copy of each tree, run
   `env -u JUNIPER_CASCOR_LOG_DIR /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest src/tests/unit/test_publish_one_artifact.py src/tests/unit/test_publish_docs_bounds.py -p no:cacheprovider`
   and compare with the count the Fix pass 3 section states. Retry the harmless edits (a docs rewrap; `timeout-minutes`
   on a job other than the republish job; a workflow-level non-cancelling `concurrency`): they must pass. A job-level
   `concurrency` must fail.
3. **Writer reproducibility.** Make a fresh clone of cascor `main` with
   `python3 -I $W/util/ad-hoc/2026-11-15_publish_port_clone.py --dest-root $W/tmp/r5review/clone juniper-cascor` (read
   its header), run the writer on it, and diff the result against the base-B tree. Report the clone's HEAD; any
   difference other than one explained by `main` having moved is a finding.
4. **Checker against real ports.**
   - Re-run the port simulations (`python3 -I $W/util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py port-sim
     --help` first; the simulations are in `$W/tmp/sweep/cascor-r3/port-sim/`, with any fix-pass-3 corrections in
     `$W/tmp/sweep/cascor-r4/port-sim/`). All 15 must pass.
   - Every mutant in `$W/tmp/r2review/neg/` and every bypass mutant in `$W/tmp/r4review/mutants/` must FAIL
     (`$W/util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py mutants --help`).
   - Then build at least 6 NEW bypass mutants of a passing port, aimed at fix pass 3's new rules and relaxations (the
     pipe/background rule, the first-word and `-m pip` rules, the builtin and function rules, quoting, `--repo`
     identity, `TAG_ASSERT`/`CANOPY_SMOKE` scoping, the lag-error text). Execute each mutant's install script the way
     round 4 did (a stub `pip` and `python`; `bash -e`) so a "bypass" is shown to change the outcome, not just to pass
     the checker. Each must fail the checker; any that passes is a finding.
   - Check that every per-port change the Fix pass 3 section adds is small and keeps the repo's own policy
     (juniper-ml #384's two-phase verify; recurrence-model's `tests/test_publish_smoke_pins.py:47`; canopy's smoke step;
     juniper-ml's tag assert).
5. **Docs and comments.** Check every sentence fix pass 3 changed (the CHANGELOG entries, #767's corrected entry, the
   test comments, the checker's docstring and reason texts) against the YAML and the code. Then read the draft
   `$W/tmp/sweep/cascor-r4/pr_body.md` and `commit_message.txt` (they become the PR's public text): flag every claim
   that is false or overstated for the tree that lands, and every count that does not match a run you made.

**Rules.** Use read-only `gh` GETs only. Never comment on, edit, approve, merge or push anything. Put no secrets,
tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one.

**Report** (your last message), most severe first, each finding with: severity, file:line, the failure scenario,
evidence (code, or a command plus its output), and the fix. Then the bypass-mutant table, and the checks you found
sound. Mirror the report and your probe outputs into `$W/tmp/r5review/`.
