# Handoff: one-artifact sweep. Plan v1.15.17 is merged; the cascor sweep is built and reviewed in rounds 1, 2 and 4; round 4's two MAJORs (checker; ml port) need fix pass 3 (tree cascor-r4) and a round-5 review; it lands after juniper-cascor#772, then the ports and plan v1.15.18

**Written**: 2026-11-23 at 18:35Z (`date -u`) by session `11a98f94`. Its ListAgents name is
`one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next`, ref `e71d3e`.
**Worktree**: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-16_one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next.md`
(juniper-ml#2603).

**Merge approval**: the owner wrote "merge approval granted" at this session's start. It is per-session: ask again.
No step below merges anything until the owner grants it in YOUR session.

**Start the next session IN `$W`.** The arc's untracked scripts and evidence exist only there. A worktree-isolated
session elsewhere can neither Write/Edit into `$W` nor `cd` into it to run git.

## Goal

Continue the one-artifact publish sweep:
1. apply round 4's fixes as fix pass 3 (tree `cascor-r4`; numbering as in `REVIEW_DISPOSITIONS.md`: fix pass 1 made `cascor-r2`, fix pass 2 made `cascor-r3`), then run the round-5 review;
2. land the cascor PR after juniper-cascor#772 merges;
3. port the new template to the 15 publishers in 7 repos, one PR per repo;
4. record it all in plan v1.15.18, and land the sweep's scripts.

## Done this session (receipts)

- **Starting state.** `bash $W/tmp/ports/verify_all_mains.bash` printed `15 of 15 pass` at 11:47:45Z (the 2026-11-15
  checker).
- **Plan v1.15.17 MERGED** as juniper-ml#2610 at 14:14:46Z, merge `f00859f0`. All 32 files equal the PR head `2bb15956`
  (`$W/tmp/arc/verify_2610_landed.bash`).
  - It moves `docs/REFERENCE.md` to 0.6.78, and lands the 26 carried scripts, the plan writer and three 2026-11-23 tools.
  - The first independent fact-check's fixes are in its first commit, the second's in its second commit.
  - CodeQL alerts 1117-1120 (`py/incomplete-url-substring-sanitization`) on the carried audit script were dismissed
    as false positives. The script must stay byte-identical to its 11-15 manifest.
- **The owner's rulings of 2026-11-23** (11:46:13Z). They were given in the dialog of the session in worktree
  `crispy-forging-falcon`, ListAgents name `repos failing checks` [5da5c3], transcript `0f9a729e`; verified there:
  - "Propagate via cascor re-pin": cascor#772 merges first, then each client's pins move;
  - "Revert edits to records (Recommended)";
  - "Fix #2606 only";
  - "Merge the literals (Recommended)" (B914).

  The order agreed with that session is cascor#772, then the cascor sweep PR, then the ports. Message it before arming
  or merging anything that touches a file a rename PR touches. A sent message is enough; no reply is needed.
- **The cascor sweep is built and NOT pushed.**
  - Writer: `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py --tree <clone> [--date …] [--changelog-cases 159] [--changelog-mutations 45]`,
    sha256 `a287376f…`. It reads the person-word at run time, so it is valid before and after #772.
  - Final tree `$W/tmp/sweep/cascor-r3/juniper-cascor` (FROZEN). Its `sweep.diff` has sha256
    `e02b4da8bfbe1a99c2b46e0c23e66f91cbaf884c7d5bf7a79f957cb63e3cb525`, +1151/-190, over these 11 files:
    - `.github/workflows/publish.yml`, `publish-cascor-model.yml`, `publish-protocol.yml`;
    - `src/tests/unit/test_publish_one_artifact.py`, `src/tests/unit/test_publish_docs_bounds.py` (new);
    - `docs/ci_cd/MANUAL.md`, `docs/ci_cd/REFERENCE.md`, `docs/ci_cd/QUICK_START.md`;
    - `docs/DEVELOPER_CHEATSHEET.md`, `AGENTS.md`, `CHANGELOG.md`.
  - Reviews and fix passes, all recorded in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`:
    - round 1, a review through two lenses: 15 surviving mutations were closed;
    - round 2: a review of fix pass 1 (tree `cascor-r2`): the checker was too strict and too weak for the ports;
    - round 3: fix pass 2 (tree `cascor-r3`), reviewed by round 4 (0 BLOCKER, 2 MAJOR; item 1). Its results, on cascor `main` `802399ab` and on #772's head `1e6e877a`:
      - tests: 161 passed;
      - the 45-mutation proof: 45 of 45 caught;
      - the test-lens harness: 68 of 68 caught, 10 harmless edits pass, 3 fail by design;
      - actionlint, pre-commit, B914 (0 sites) and the sequence-safety screens: clean;
      - the evidence is in `$W/tmp/sweep/cascor-r3/evidence/`.
    - Round 3's residual risk: in an F3-style port, a later dependency install can pull a different version of the
      target.
- **The new checker** is `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256 `2feceecf…`. The 2026-11-15
  checker stays as provenance.
  - Port simulations (`$W/tmp/sweep/cascor-r3/port-sim/`): 15 of 15 PASS (12 faithful, 2 reordered, 1 faithful plus
    the ml F2 edits).
  - The 7 bypass mutants (`$W/tmp/r2review/neg/`) all FAIL.
  - The 43 earlier cases keep their verdicts, and the 74-case proof passes.
- **`jobs?filter=latest` is VERIFIED** (juniper-canopy run 43135960676): "Re-run failed jobs" COPIES carried jobs into
  the new attempt. Plan v1.15.17 records it.

## Remaining work (numbers match the Goal)

1. **Round 4 is DONE**: 0 BLOCKER and 2 MAJOR, neither a defect in cascor's frozen tree. The dispositions are in
   `REVIEW_DISPOSITIONS.md` § "Round-4 review"; the probes are
   `$W/util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py`, with output in `$W/tmp/r4review/`. Per its stopping
   rule:
   - **Fix pass 3** (the dispositions file's numbering).
     - In the CHECKER: R4-2 (MAJOR: a `| tee`/`&` after the import hides its failure), plus R4-3, R4-4's checker part,
       R4-6 and the checker NITs.
     - In the WRITER: R4-4 (admit `concurrency` at workflow level only; fix the test comments, `CHANGELOG.md:292` and
       `checker_proof_r3.py`'s C5) and the CHANGELOG/test-comment NITs. That includes correcting #767's unreleased
       `CHANGELOG` entry in place.
     - Regenerate the tree as `$W/tmp/sweep/cascor-r4/`. Re-run the tests, both mutation proofs, the checker proof,
       the 15 port simulations and the r2/r4 mutants: every R4 mutant must FAIL.
   - **Round 5**: a fresh reviewer reviews only the checker's interdiff (`2feceecf…` to the new one) and the cascor
     interdiff. It gets `ROUND4_BRIEF.md`'s prompt, re-aimed at round 4's fixes. A clean round 5 clears item 2.
   - R4-1 (MAJOR) and R4-5 are PORT items; see item 3.
2. **Land the cascor sweep PR**, only when round 5 is clean AND cascor#772 has MERGED.
   - Fix pass 3 changes only the WRITER, the CHECKER and the tree (`cascor-r4`).
   - Keep `cascor-r3/work-after772` as the comparison base.
   - Keep using the tools in `cascor-r3/` (`workflow_reader_tests.txt`, `mutation_proof.py`, the test-lens files,
     `venv-b914`, `predict_symbol_loss.py`).
   - Copy `pr_body.md` and `commit_message.txt` into `cascor-r4/`, and update every count and base in them.
   - **#772's state** (re-read 18:03Z): OPEN, BLOCKED, head `1e6e877a`, auto-merge armed since 2026-11-20 22:32Z.
     - Two checks fail: `Verify AGENTS.md Last Updated` and `Sequence Safety`.
     - The repair belongs to `repos failing checks`, which waits on the owner's "Symlinks" answer (asked 12:26:19Z).
     - #772 may merge by itself once green; a rebuilt head may be re-armed instead.
     - Check it with `gh pr view 772 --repo pcalnon/juniper-cascor --json state,mergedAt,headRefOid`.
     - If #772 closes unmerged, ask the owner whether the sweep lands on `main` as it is.
     - This session's watcher (`tmp/arc/watch_cascor_772.bash`) reports only to this session.
   - **Regenerate.** Make two fresh clones:
     - `python3 -I $W/util/ad-hoc/2026-11-15_publish_port_clone.py --dest-root $W/tmp/sweep/land/head juniper-cascor`;
     - the same with `--dest-root $W/tmp/sweep/land/base` for the gate's untouched base tree. The tool refuses an
       existing destination.

     Run the writer on `land/head`. Diff the result against `$W/tmp/sweep/cascor-r3/work-after772` (round 3's output
     on #772's head) and review every difference.
   - **Verify** with `/opt/miniforge3/envs/JuniperCascor1/bin/python` and `env -u JUNIPER_CASCOR_LOG_DIR`:
     - both test modules, and the 14 files in `$W/tmp/sweep/cascor-r3/workflow_reader_tests.txt`;
     - the mutation proof:
       `python3 -I $W/tmp/sweep/cascor-r3/mutation_proof.py --tree <land/head clone> --scratch <empty dir> --python /opt/miniforge3/envs/JuniperCascor1/bin/python`;
     - the test-lens harness: `make_r3_harness.py`, `test_lens_mutations_r3.py` and `run_test_lens.bash` in the same
       directory (read each header first);
     - actionlint: `/opt/miniforge3/envs/JuniperCascor1/bin/actionlint`;
     - pre-commit, through `$W/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py SRC DEST /opt/miniforge3/bin/pre-commit FILE…`.
       The guard blocks pre-commit inside a clone.
     - B914: `$W/tmp/sweep/cascor-r3/venv-b914/bin/flake8 --isolated --select=B914 <changed .py>`;
     - the sequence-safety screens. Symbol loss, once per changed test module:
       `/opt/miniforge3/envs/JuniperCascor1/bin/python -I $W/tmp/sweep/cascor-r3/predict_symbol_loss.py BASE_TREE HEAD_TREE <rel .py> --trailers <commit body>`.
       Then the docs screen and the markdown-structure delta, as `$W/tmp/sweep/cascor-r3/final_lint_and_screens.bash`
       runs them. That driver and the other `final_*.bash` are hard-wired to `work-main`/`work-after772`: adapt them.
   - **Texts.**
     - The PR body is `pr_body.md`, copied to `cascor-r4/`. Update its bases (`802399ab`, `1e6e877a`) and its counts
       to the landing run's. Replace its closing attribution lines (the robot line and the session link) with YOUR
       session's.
     - In `commit_message.txt`, line 1 is the headline and line 2 is blank; the body is line 3 onward. In the body
       file, replace the last two lines (the old trailers) with YOUR session's attribution lines, and keep the
       `Allow-Symbol-Loss:` line.
   - **Gate.**
     `python3 -I $W/util/ad-hoc/2026-11-15_build_gate_payload.py --out <gate> --tree <land/head clone> --base-tree <land/base clone> --text <pr body> --text <commit body> <the 11 paths>`,
     then `bash $W/util/ad-hoc/2026-11-15_pre_push_gate_run.bash <gate>`. Only exit 0 passes.
   - **Open the PR.**
     - Immediately before the upload, the clone's HEAD must equal
       `gh api repos/pcalnon/juniper-cascor/commits/main --jq .sha`. If not, re-clone and re-run.
     - `ARGS.json`: `repo` = `juniper-cascor`, `base` = `main`, `branch` = `fix/publish-one-artifact-sweep`,
       `tree` = the land/head clone, `paths` = the 11 files, and `message`, `commit_body_file`, `title`, `body_file`.
     - From `$W`'s root, run
       `python3 -I util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/run_open_signed_pr.py ARGS.json --dry-run`,
       then the same without `--dry-run`.
     - Read it back with `…/readback_branch.py ARGS.json`.
   - **Merge (only with YOUR session's approval).**
     - Confirm the PR has one commit carrying the `Allow-Symbol-Loss:` line, and that `autoMergeRequest` is null or has
       a null `commitBody`.
     - Message `repos failing checks`.
     - Run `python3 util/safe_merge.py --pr N --repo juniper-cascor --execute` in the background, and read its
       `MERGED` line.
     - Afterwards, `gh api repos/pcalnon/juniper-cascor/commits/<merge> --jq .commit.message` must show the waiver line.
3. **The ports**: 15 workflows in 7 repos, one PR per repo:
   - canopy, data, data-client, cascor-client, cascor-worker: `publish.yml`;
   - recurrence: its 3 publishers;
   - juniper-ml: its 7 publishers.

   Each port carries the SWEPT template: the `Verify the TestPyPI install` job, the republish gate,
   `PUBLISH_TAG_PREFIX`, the hardening, the docs, and the template's post-rename wording. The template is
   `$W/tmp/ports/SWEEP_BRIEF.md` together with cascor `main`'s merged `publish.yml`.
   - `$W/tmp/ports/BRIEF.md` is the 2026-11-15 brief. It is superseded for the template, and its paths (into
     `giggly-foraging-sunbeam`) are stale.
   - Clone fresh with `2026-11-15_publish_port_clone.py`. Use your own session's attribution lines, and take dates from
     `date -u`.
   - **Writers.** Model them on `util/ad-hoc/2026-11-15_<repo>_one_artifact_publish_port.py`, which is on `main`. The
     extractors `template_blocks` and `republish_job` in `2026-11-15_cascor_one_artifact_publish_edits.py` accept the
     swept template. Worked examples: `$W/tmp/sweep/cascor-r3/port-sim/`.
   - **Per-port changes the checker needs** (round 2's simulation):
     - canopy: one `cd`, with `pyproject.toml` read through a sparse checkout under `$GITHUB_WORKSPACE`;
     - data, cascor-client, cascor-worker: the tag passed through `env: RELEASE_TAG`;
     - data-client, the 3 recurrence publishers, ml `publish.yml` and the 6 ml sub-packages: the version file read
       under `$GITHUB_WORKSPACE`;
     - ml config-tools and doc-tools: `python -c` last;
     - ml `publish.yml`: the F2 edits too (drop `|| true` after `ls -la`, and replace the `set +e` block with
       `pip download … && { FETCHED=1; break; }`).
     - **juniper-ml's tests (R4-1, MAJOR).** `tests/test_publish_testpypi_verify.py:86-90` and
       `tests/test_publish_subpackage_workflows.py:92-98` look for the install step in the TestPyPI job and SKIP when
       it is not found, so after the move every #384 pin goes dark while CI stays green. The fix:
       - retarget both lookups to the `Verify the TestPyPI install` job;
       - make "not found" a FAILURE;
       - set the expected TestPyPI permissions (`:237`) to `{id-token: write}`.

       Acceptance for EVERY port: no new skip in that repo's publish tests.
     - **R4-5.** The six ports whose install checks end on metadata alone (cascor-client, cascor-worker, data,
       data-client, ml ci-tools, ml observability) add a failing `find_spec(<module>)`, as cascor's protocol publisher
       does.
   - **Every port's commit body** carries
     `Allow-Symbol-Loss: TestFindReleaseRun.test_the_newest_release_run_that_still_holds_the_artifact_is_found`. All 7
     port repos' tests contain that test. Check the squash as in item 2.
   - **Tests that pin publish text, and their environments:**
     - juniper-ml: `tests/test_publish_one_artifact.py`, `test_publish_subpackage_workflows.py`,
       `test_publish_testpypi_verify.py`, `test_publish_release_only_trigger.py` and `test_publish_env_policy_drift.py`.
       Run them with `python3 -m unittest`, following `ci.yml`'s list.
     - canopy: `src/tests/unit/test_publish_one_artifact.py:494`, in env `JuniperCanopy1`.
     - recurrence-model: `juniper-recurrence-model/tests/test_publish_smoke_pins.py:47`.
     - data: env `JuniperData`. data-client, cascor-client, cascor-worker and recurrence: the active env.
   - **The five repos that pin digests** (data, data-client, cascor-client, cascor-worker, ml) pin NORMALIZED blocks
     (SWEEP item 23).
   - **Per PR:**
     - compare the clone's HEAD with `main` before every upload;
     - run the gate;
     - open the PR;
     - fetch its head with `2026-11-15_fetch_pr_files.py --repo <repo> --ref <branch> --pr N --out <dir>`;
     - run the 2026-11-23 checker;
     - get an independent review and apply its fixes;
     - wait for green CI;
     - with YOUR session's approval, `safe_merge.py`.
   - **B914.** Do not edit `.pre-commit-config.yaml`. If a CI pre-commit cache miss trips B914, wait for that repo's
     literal-merge PR (below).
   - **Done when** the 2026-11-23 checker passes all 15 ports plus cascor's 3 on each repo's `main`. Make a copy of
     `verify_all_mains.bash` that calls the new checker; the old checker will fail every port once the sweep lands.
4. **Plan v1.15.18.** It records the sweep PR, reviews 1, 2, 4 and 5 with fix passes 1, 2 and 3, the ports, and two items
   that exist so far only in `REVIEW_DISPOSITIONS.md` (rows M5 and N6), to be added as SWEEP items:
   - 28 (M5): the install check tests the tag's version, and cascor's build has no tag==version assert; juniper-ml's
     assert step is the model;
   - 29 (N6): the republish gate runs after the `pypi` approval.

   **Build it ONLY on a fresh clone of juniper-ml `main`.** `$W`'s tracked plan is still v1.15.16, so an upload from
   `$W` would revert #2610.

   It lands the 6 scripts (`$W/tmp/arc/sweep_scripts.sha256`). It also promotes, or archives, round 3's proof tools
   from `$W/tmp/sweep/cascor-r3/`:
   - `mutation_proof.py`, `checker_proof_r3.py`, `port_sim_table.py`;
   - `make_r3_harness.py`, `test_lens_mutations_r3.py`, `predict_symbol_loss.py`;
   - the `final_*.bash` drivers.

   First run the CodeQL prescreen (`util/ad-hoc/2026-10-05_codeql_python_prescreen.py`; #2610 drew 4 alerts) and
   pre-commit on every new script. Regenerate the manifest if anything changed.

## Open PRs and peers (re-read 18:03Z)

- **Rename PRs:**
  - ml#2606 (publish.yml, the plan, ceremony.py): open, CONFLICTING, and the one to fix;
  - ml#2605 (all 7 ml publishers): armed and CONFLICTING. The owner ruled "Fix #2606 only": do not merge or close it;
  - canopy#830 (armed) and data#547: publish.yml and the one-artifact test;
  - cascor#772: above;
  - recurrence#237 and deploy#281 merged on 11-20; #237 renamed comments in recurrence's publishers.

  A rename PR still open when a port lands drops its publish edits; that is the rename session's side.
- **B914 literal-merge PRs**: canopy#832, cascor#774, data-client#268, cascor-client#202, cascor-worker#236, ml#2609.
  - ml#2609 edits `test_publish_subpackage_workflows.py` and `test_publish_testpypi_verify.py`, which the ml port edits
    too.
  - B9 is selected in ml, cascor, data-client, cascor-client, cascor-worker and canopy.
- **Peers:**
  - `repos failing checks` [5da5c3], worktree `crispy-forging-falcon`, repairs the rename PRs. It waits on "Symlinks".
  - `r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next` [9660dc] holds two things:
    - the worktree housekeeping;
    - the owner's open items from its source handoff: deploy restart, trio upgrade and probe, the recurrence pin, A1's
      open items, O13, the cascor fix-forward, the v2-draft pointer, the 0.4.3 launch.

    It waits on "Cleanup" and "Recur. pin" (since 12:18:32Z). It knows #2610 merged and that `$W` must stay.
  - The PyPI trusted-publisher check stays with the owner (plan §6).

## Traps

- The rename's blind substitution rewrote files ON DISK in sibling worktrees: giggly, sparkling, agent-a54a0a and
  humble-humming-flask. Use only `$W`'s pristine copies; the transcripts are the record (memory
  `reference_blind_substitution_rewrites_untracked_files_in_sibling_worktrees.md`).
- The Bash guard refuses complex git forms: `git -C`, `cd` into another worktree with git, `git/trees` in a URL, and
  some heredocs. Use script files.
- Agent worktrees are auto-removed when they hold no tracked changes. Have agents mirror their outputs into `$W/tmp/`.
- Never estimate a time. Four of this session's estimates were 10-40 min off.
- A squash did keep a fix-up commit (canopy#823, ml#2610). Still, pin every merge to a head whose CI ran.

## Git state of `$W` and the retention rule (18:35Z)

- Branch `worktree-ethereal-munching-peacock` at `81b8eaf7`, one commit behind `origin/main` `f00859f0` (fetched
  17:36Z). Nothing is staged.
- **34 untracked files.**
  - 28 are byte-identical copies of files on `main` via #2610. They block a fast-forward; before deleting any, verify
    each against main's blob (`$W/tmp/audit-handoff-r2/cmp28.py`).
  - 6 exist only here (`tmp/arc/sweep_scripts.sha256`). NEVER delete these:
    - `util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`
    - `util/ad-hoc/2026-11-23_publish_port_template_identity.py`
    - `util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py`
    - `util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_proposed_fixes.py`
    - `util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py`
    - `util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py`
- **Gitignored `tmp/`:**
  - `ports/`, `arc/`, `sweep/` (three frozen trees, `REVIEW_DISPOSITIONS.md`, `ROUND4_BRIEF.md`);
  - `r2review/`, `r4review/`, `review-test-lens/`, `review-workflow-lens/`;
  - `factcheck-2610/`, `audit-handoff-r1/`, `audit-handoff-r2/`.
- **Retention.** Do not remove `$W` until three things hold: the 6 scripts have landed; round 3's proof tools are
  promoted or archived; and `tmp/` is archived under the 2026-10-26 rule. `git worktree remove` deletes ignored files.
  Under the same rule, do not delete any single `tmp/` file that a work arc still uses or still needs for reference.

## Verification commands (from `$W`, one per call)

```bash
gh pr view 772 --repo pcalnon/juniper-cascor --json state,mergedAt,headRefOid   # OPEN until it merges
gh pr view 2610 --repo pcalnon/juniper-ml --json state,mergeCommit               # MERGED, f00859f0
sha256sum -c tmp/arc/sweep_scripts.sha256                                         # 6 x OK
echo "e02b4da8bfbe1a99c2b46e0c23e66f91cbaf884c7d5bf7a79f957cb63e3cb525  tmp/sweep/cascor-r3/sweep.diff" | sha256sum -c
bash tmp/ports/verify_all_mains.bash                                              # "15 of 15 pass" (OLD checker)
```

## Documents referenced / changed

- **Referenced:**
  - the predecessor handoff;
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.17);
  - `$W/tmp/ports/SWEEP_BRIEF.md`, `SWEEP_ITEMS.md`, `BRIEF.md`;
  - `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, `ROUND4_BRIEF.md`.
- **Changed on `main`:** the plan, `docs/REFERENCE.md` (0.6.78) and 30 scripts, through juniper-ml#2610.
- **New in `$W`, git-untracked:** the 6 scripts above.
- **New or restored in `$W`, gitignored `tmp/`:**
  - `tmp/ports/SWEEP_BRIEF.md`;
  - `tmp/sweep/REVIEW_DISPOSITIONS.md`, `tmp/sweep/ROUND4_BRIEF.md`;
  - the restored `tmp/ports/BRIEF.md` and `SWEEP_ITEMS.md`.
- This handoff lands through its own one-file PR.
