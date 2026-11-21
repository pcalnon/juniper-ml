# Handoff: one-artifact publish. All 8 port PRs are merged, and all 15 ported workflows pass the identity check on each repo's `main`. On 2026-11-16 the Overtoad ruled the sweep's two design questions. The sweep brief, cascor's template PR, the ports and plan v1.15.17 remain

**Written**: 2026-11-16 ~22:15Z by session `85756bf1`. Its ListAgents name is
`one-artifact-ports-8-prs-open-reviews-then-merge-plan-v1-15-17-next`, ref `bdd9d4`. Worktree
`.claude/worktrees/sparkling-percolating-meadow`. Paused because the weekly token limit is near.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_one-artifact-ports-8-prs-open-reviews-then-merge-plan-v1-15-17-next.md`
(juniper-ml#2594).

**Merge approval**: the Overtoad wrote "merge approval granted" at this session's start. It is per-session: ask again.

## Done this session

- **All 8 PRs are MERGED** (read from `gh` at 15:2xZ):
  - recurrence#236 at 11-15 23:07Z and ml#2592 at 23:36Z;
  - canopy#823 at 11-16 08:27Z (`1e8a8ece`) and data#543 at 08:30Z (`6fc7d53f`);
  - cascor-client#199 at 08:31Z (`fe962b7b`) and data-client#264 at 08:36Z (`61d6b44b`);
  - ml#2593 at 08:47Z (`67e9aab1`) and cascor-worker#232 at 08:49Z (`a0b5e363`).

  The Overtoad's armed auto-merge merged the last six, each at the head that carried its review fixes. For ml#2593 and
  #232 that head is an update-branch merge on top of the reviewed `acc5c262` and `41933886`. The fix-up agents'
  reports are in the predecessor session's transcript (`d67643b8…jsonl`, after 23:38Z).
- **Identity check, 15:29Z: 15 of 15 PASS.** Every ported workflow on each repo's `main` matches cascor `main`'s
  `publish.yml`, which is unchanged since #767 (`675884888f5a`). Rerun with `bash tmp/ports/verify_all_mains.bash`;
  the log is `tmp/ports/verify_all_mains.log`.
- **The 26 uncommitted scripts were copied** from `.claude/worktrees/giggly-foraging-sunbeam/util/ad-hoc/` into this
  worktree's `util/ad-hoc/`, untracked: 14 carried, 5 tools and 7 writers. The 14 carried files match
  `carried_scripts.sha256` (copy in `tmp/arc/`), and the other 12 are byte-identical to the source. Both copies exist.
- **The Overtoad's rulings of 2026-11-16** (this session's AskUserQuestion, asked 15:32:57Z, answered 22:08:20Z). No
  earlier ruling exists: 32 transcripts since 11-15 23:30Z were searched.
  1. **"Gate it in the job (Recommended)"**, for SWEEP items 11, 21 and 26. "The republish job reads the newest
     release run for the tag and refuses unless its TestPyPI job(s) concluded success in the latest attempt, and
     refuses if no release run exists. The docs say an index-lag failure goes to 'Re-run failed jobs' and a failed
     install check to a new patch version."
  2. **"Yes, in this sweep (Recommended)"**, for SWEEP item 6, which also covers item 10. "Add a job 'Verify the
     TestPyPI install' (needs the TestPyPI job, contents: read only, imports from outside any checkout) and make
     PyPI's job need it. The ceremony already reads any job with 'TestPyPI' in its name, so a failure there reads
     HALT_TESTPYPI with no ceremony change."

## Remaining work

1. **Write the sweep brief** `tmp/ports/SWEEP_BRIEF.md` in this worktree. Sources:
   - `tmp/ports/SWEEP_ITEMS.md`, items 1 to 27, copied from giggly's. Items 11, 21 and 26 are now ruled; items 24 and 27
     are status.
   - The two rulings above.
   - The mechanics in `tmp/ports/BRIEF.md`: writer scripts, `run_open_signed_pr.py`, the gate and the read-back.
   - The proposals below.
2. **cascor first: one PR over all three publishers** (`publish.yml`, `publish-protocol.yml`,
   `publish-cascor-model.yml`). It also changes `src/tests/unit/test_publish_one_artifact.py`, `docs/ci_cd/MANUAL.md`
   (§ One Artifact, Checked Against TestPyPI; § Recovering a Release That Did Not Reach PyPI; fetched to
   `tmp/ports/cascor_MANUAL.md`) and REFERENCE's One-Artifact Contract. Use a task-executor, then an independent review,
   then merge.
3. **Then the ports.** Update `util/ad-hoc/2026-11-15_publish_port_template_identity.py` for the new job (and any new
   parameter) first. The ports are canopy, data, the trio (cascor-client, data-client, worker), recurrence (3
   publishers) and ml (7), one PR per repo. Each gets reviews, then a merge. The ports that pin the template blocks'
   sha256 (data, cascor-client, data-client, worker, ml) move those pins.
4. **Plan v1.15.17** (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, now v1.15.16). Its
   v1.15.16 header still says the fix "is a session's work in progress". Record:
   - dialog 2;
   - #763/#767 and their reviews;
   - the audit, in the predecessor's words: "4 rebuild per job, 12 `skip-existing`, none checked sha256 before #763";
   - the 8 PRs, their reviews and merges;
   - the findings below and the sweep list;
   - the 2026-11-16 rulings;
   - ml `docs/REFERENCE.md`'s version line (item 18).

   Land the 26 scripts with it. This step is independent of 2 and 3, so it can run in parallel.

## Proposals for the brief (engineering calls; not yet ruled or done)

- **Ruling 1's mechanics.** "Find the release run's artifact" reads the newest release run for the tag, whether or not
  its artifact has expired, then `GET actions/runs/{id}/jobs?filter=latest`. It refuses unless every job whose name
  contains "TestPyPI" concluded `success`. Before relying on it, check that `filter=latest` returns the jobs carried
  over after "Re-run failed jobs".
- **Ruling 2's mechanics.**
  - The new job holds `contents: read` and no `id-token`. The install commands stay per-repo. The import runs from
    `$RUNNER_TEMP`, as canopy's `cd "${RUNNER_TEMP}"` does.
  - `ceremony.py:660-683` classifies by the substring "testpypi", so no ceremony change is needed. Prove it with
    `tests/test_release_train_ceremony.py` plus a simulated run.
- **Item 3/22**: a third env parameter, `PUBLISH_TAG_PREFIX` (`v` or `<package>-v`), so that a sub-package publisher
  refuses the meta `v` tag.
- **Item 23**: pin a normalized block with each `uses:` ref dropped (the action name kept), so a Dependabot bump needs
  no re-port.
- **Item 12**: keep the `v` guard, with a comment that an `rc`/`hf` convention must widen it.
- **Item 20**: docs only.
- **Item 25**: narrow the checker's push exemption to the gate step's name.

## Findings (carried, for v1.15.17)

- **TestPyPI and PyPI files differ:**
  - juniper-data, every release from 0.4.2 to 0.17.1;
  - data-client and cascor-client, every release (21 versions, 42 files);
  - canopy 0.3.0 only (0.5.0 to 0.10.0 match);
  - all 26 recurrence releases match.
- **The monitor could read the wrong run.** Before #2592 it could read `Publish Container Image`: 5 repos, and the image
  run had the larger id in 11 of 20 Releases sampled.
- **TestPyPI provenance.** Canopy 0.10.0's shows `environment: null`, where PyPI's shows `pypi`. Cascor 0.14.0 is null
  on both.
- **Old tags.** Tags cut before a repo's port have no republish job.
- **Re-runs are safe; re-cuts are not.** Warehouse answers a byte-identical re-upload with 200, so "Re-run failed jobs"
  is harmless. It refuses a re-cut, which brings new bytes (SWEEP item 11's correction).

## Key context

- **The Bash guard trips on "git" inside words**, `.github` included, on a `cd` into another worktree, and on complex
  git lines. Put such commands in a script file, as `tmp/ports/verify_all_mains.bash` does.
- **The predecessor's `tmp/ports/`** (in giggly-foraging-sunbeam) holds the clones and each repo's evidence, hundreds of
  MB, under the retention rule. Cleaning up the agent worktrees waits for the Overtoad's word.
- **task-executor agents get their own worktree** and mirror their files here through Bash.
- **The Overtoad's answer took 6.5 h.** Launch independent agents before you ask.

## Git status (this worktree, 22:15Z)

- Branch `worktree-sparkling-percolating-meadow` is at `445ebf4e`, behind `origin/main`. Nothing is staged.
- Untracked: the 26 scripts under `util/ad-hoc/` (`git status --short --untracked-files=all util/ad-hoc/` prints 26
  lines).
- Gitignored: `tmp/ports/` and `tmp/arc/`.

## Verification commands (one per call)

```bash
gh pr view 232 --repo pcalnon/juniper-cascor-worker --json state,mergedAt
bash tmp/ports/verify_all_mains.bash
git status --short --untracked-files=all util/ad-hoc/
```

`verify_all_mains.bash` must print "15 of 15 pass" and `identity-exit=0`.

## Documents referenced / changed

- **Referenced:**
  - the predecessor handoff;
  - `tmp/ports/SWEEP_ITEMS.md` and `tmp/ports/BRIEF.md` (copies in this worktree);
  - cascor `docs/ci_cd/MANUAL.md`;
  - `util/release_train/ceremony.py`;
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`.
- **Changed:** only this file, which lands through its own one-file PR. The copied scripts are untracked.
