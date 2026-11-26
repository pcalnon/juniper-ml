# Round-4 review brief: the cascor sweep's second fix pass (round 3)

Written 2026-11-23 by session `e71d3e`. Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Stopping rule.**
- A BLOCKER or MAJOR finding is fixed in the writer or checker, the final tree is regenerated as round 5, and round 5's
  interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- The landing step goes ahead only after a round with no BLOCKER and no MAJOR.

## The prompt

Round-4 adversarial review of a FIX PASS on juniper-cascor's publish workflows, tests and docs, and on the cross-repo
checker that gates the ports. Treat the fix pass as the least trustworthy part.

**Frozen trees (READ-ONLY).** Copy anything you want to change into the `tmp/` of the worktree you run in; never
write under `/tmp`.
- Round 3, under review: `$W/tmp/sweep/cascor-r3/juniper-cascor`. It is cascor `main` `802399ab` plus a working-tree
  diff. `$W/tmp/sweep/cascor-r3/sweep.diff` must hash to sha256
  `e02b4da8bfbe1a99c2b46e0c23e66f91cbaf884c7d5bf7a79f957cb63e3cb525`. If it does not, STOP and report.
- Round 2, already reviewed: `$W/tmp/sweep/cascor-r2/juniper-cascor`, diff sha256 `0056f312…`.
- The interdiff: `$W/tmp/sweep/cascor-r3/r2_to_r3.diff` (250 lines).

**Checker.**
- Under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256 `2feceecf…`.
- As round 2 reviewed it: `$W/tmp/sweep/cascor-r3/checker_r2_as_reviewed.py`.
- Usage: `python3 -I <checker> --template <cascor publish.yml> WORKFLOW...`.

**What the fix pass was meant to do.** See `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: the "Round-2 review" table (F1-F8)
and the "Round 3" section. Round 3 also ADDED rules the review did not ask for (listed in the Round 3 section and the
checker's docstring); scrutinise those hardest.

**Expected, by design:**
- the test-lens harness's C4, D1 and D2 fail;
- the suite's H2d, H2e, H4 and H10 edits fail;
- cascor's 11-15 non-vacuity script catches 41 of 43, because 2 of its anchors were rewritten.

Do these, in order:

1. **The delta.** Read every hunk of `r2_to_r3.diff`. Then diff the two checkers. Hunt new bugs:
   - does any F-fix change behaviour beyond its finding?
   - is any added checker rule wrong, over-strict (it rejects a legitimate port) or bypassable?

   Run `actionlint` (`/opt/miniforge3/envs/JuniperCascor1/bin/actionlint`) on the three round-3 workflows.
2. **Tests.** From a copy, run:
   `env -u JUNIPER_CASCOR_LOG_DIR /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest src/tests/unit/test_publish_one_artifact.py src/tests/unit/test_publish_docs_bounds.py -p no:cacheprovider`
   161 should pass. Then retry the round-2 harmless edits and confirm they now pass:
   - a docs rewrap;
   - `timeout-minutes`, `run-name`, and a non-cancelling `concurrency`.
3. **Checker against real ports.**
   - Re-run `python3 -I $W/util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py port-sim` (read its `--help`
     first). Confirm all 15 simulations pass (`$W/tmp/sweep/cascor-r3/port-sim/`), and that the 7 mutants in
     `$W/tmp/r2review/neg/` fail.
   - Then build at least 6 NEW bypass mutants of a passing port, aimed at the rules round 3 added and at F1-F4. Each
     must fail; any that passes is a finding.
   - Then check that the "small faithful changes" each port needs are truly small and keep the repo's own policy
     (juniper-ml #384 two-phase verify; recurrence-model's `tests/test_publish_smoke_pins.py:47`; canopy's smoke step).
4. **Docs.** Check every sentence round 3 changed in `docs/ci_cd/MANUAL.md`, `docs/ci_cd/REFERENCE.md` and
   `CHANGELOG.md` against the round-3 YAML.

**Rules.** Use read-only `gh` GETs only. Never comment on, edit, approve, merge or push anything. Put no secrets,
tokens, e-mail addresses or personal data in the report.

**Report**, most severe first, each finding with: severity, file:line, the failure scenario, evidence (code, or a
command plus its output), and the fix. Then give the bypass-mutant table, and the checks you found sound.
