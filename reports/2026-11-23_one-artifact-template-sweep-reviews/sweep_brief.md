# Brief: the one-artifact template SWEEP (juniper-cascor first, then every port)

Written 2026-11-23 before 12:00:30Z (corrected 12:01:19Z and 13:06Z; times from `stat` and `date -u`, not estimated) by
the orchestrating session `e71d3e` (juniper-ml worktree `ethereal-munching-peacock`,
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`). Read it whole.
It supersedes nothing in `$W/tmp/ports/BRIEF.md` (the 2026-11-15 port brief: its template contract, mechanics and hard
rules still hold) except where this file says so. Sources: `$W/tmp/ports/SWEEP_ITEMS.md` (items 1-27; numbers below are
its numbers), the owner's rulings quoted below, and the handoff
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-16_one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next.md`.

## Starting state (read from `gh` and the disk, 2026-11-23 11:47Z)

- juniper-cascor `main` is `802399abc932`; its `publish.yml` is unchanged since #767 (`675884888f5a`).
- `bash $W/tmp/ports/verify_all_mains.bash` printed `15 of 15 pass` (log `$W/tmp/ports/verify_all_mains.log`): every
  ported workflow on each repo's `main` matches cascor's template.
- Open and touching the same files: the owner's "owner -> Overtoad" rename PRs. Its sequencing is below.

## The owner's rulings this sweep implements (verbatim)

2026-11-15, the directive and the ladder: see `$W/tmp/ports/BRIEF.md` § Why. The rulings of 2026-11-16, from session
`85756bf1`'s dialog (asked 15:32:57Z, answered 22:08:20Z):

1. **"Gate it in the job (Recommended)"** (SWEEP items 11, 21, 26): "The republish job reads the newest release run for
   the tag and refuses unless its TestPyPI job(s) concluded success in the latest attempt, and refuses if no release run
   exists. The docs say an index-lag failure goes to 'Re-run failed jobs' and a failed install check to a new patch
   version."
2. **"Yes, in this sweep (Recommended)"** (SWEEP item 6, which also covers item 10): "Add a job 'Verify the TestPyPI
   install' (needs the TestPyPI job, contents: read only, imports from outside any checkout) and make PyPI's job need
   it. The ceremony already reads any job with 'TestPyPI' in its name, so a failure there reads HALT_TESTPYPI with no
   ceremony change. It also fixes item 10, where an import from the checkout root passes without the wheel." (The
   11-16 handoff dropped that last sentence; this quote was checked against session `85756bf1`'s transcript on
   2026-11-23.)

2026-11-23, from session `crispy-forging-falcon`'s dialog (answered 11:46:13Z; read from its transcript):

- Template: **"Propagate via cascor re-pin"**: "Merge cascor#772 first, then update each client's pinned commit and SHA
  constants to the new template. Ordered merges are required."
- Records: **"Revert edits to records (Recommended)"**: "Records keep their original text; the rename applies only to
  living docs, code comments and config. This greens harcot's tests and the archive guard without waivers."

## Sequencing (agreed with session `crispy-forging-falcon` [5da5c3], which repairs the rename PRs)

1. juniper-cascor#772 (the rename) merges FIRST. The owner merges it; neither session does.
2. Then the cascor sweep PR, built on cascor `main` AFTER #772. Until #772 merges, build and review it locally, from a
   replayable writer script, and open NO PR (an open PR can be armed by the owner's sweeper and merge out of order).
3. Then the ports, one PR per repo. They carry the template's new text, the rename's wording included, to every repo,
   recurrence and juniper-ml too. A client rename PR still open by then drops its publish-file edits for the port.
4. Message `repos failing checks` before arming or merging anything that touches a file a rename PR touches.

**Wording.** In NEW text, avoid naming the person where you can ("ruling 1 of 2026-11-16", "the gate's approver").
Where you must, use the word the base file already uses: the writer detects it at run time (for cascor, "Overtoad"
once `publish.yml` reads "The Overtoad's recovery ladder", else "owner"), so one script is right on either base. Never
change "owner" where it is not the person (`/repos/{owner}/{repo}`, `repository_owner`, an owner of a lock).
Anchors that contain the word must be built from that detected value.

## What the sweep changes (by SWEEP item)

**A. Ruling 2, the install check's own job (items 6, 10).** In every publisher:

- New job, name exactly `Verify the TestPyPI install` (job id free; suggest `verify-testpypi-install`).
  - `needs:` the TestPyPI job; `runs-on: ubuntu-latest`.
  - `permissions:` exactly `contents: read`. No `environment`, no `id-token`, no upload, no `continue-on-error` on the
    job or any step.
  - Its steps are the repo's own install check, moved out of the TestPyPI job unchanged in substance.
  - Every `pip install` and the import run from `$RUNNER_TEMP` (`cd "${RUNNER_TEMP}"` first, as canopy's copy does since
    #823). The checkout root must never be on `sys.path`. A sparse checkout the check needs is allowed, but nothing
    runs from it.
- The PyPI job: `needs: [<TestPyPI job id>, <install job id>]`.
- The TestPyPI job ends at `Verify TestPyPI serves exactly these files`. With the install check gone, drop its checkout
  and `setup-python` when nothing else in it needs them. Its permissions then become exactly `id-token: write`,
  matching the PyPI job, so the job that can mint runs only the template steps and the publish action. That last step
  is an engineering proposal, not part of the ruling's text: say so in the PR body.
- Proven 2026-11-23 against juniper-ml `util/release_train/ceremony.py`'s `classify_publish_run` (`:657-667`; the
  simulation is `$W/tmp/arc/ceremony_new_job_sim.py`, 6/6 OK):
  - the install job failing (PyPI skipped) reads `HALT_TESTPYPI`;
  - running, it reads `IN_PROGRESS`;
  - both TestPyPI-named jobs green with PyPI parked reads `PENDING_PYPI_APPROVAL`.

  The monitor's 900 s budget (`DEFAULT_MONITOR_TIMEOUT_SECONDS`) gains one job start; note it, do not change it.

**B. Ruling 1, the republish gate (items 11, 21, 26).** Rewrite the template step `Find the release run's artifact`:

- Take the NEWEST run of this workflow with `event=release` and `head_branch == tag` (largest id), whether or not its
  artifact has expired. None: `::error::` naming the tag, exit 1.
- List that run's jobs with `GET actions/runs/{id}/jobs?filter=all` (paginate). Keep, per job NAME, the record with the
  highest `(run_attempt, id)`.
  - Why not `filter=latest`: GitHub documents it as "jobs from the most recent execution". Whether it lists jobs that a
    "Re-run failed jobs" attempt carried over is UNVERIFIED. Session e71d3e's probe
    (`$W/util/ad-hoc/2026-11-23_jobs_filter_latest_after_rerun_failed_probe.py`, logs `$W/tmp/arc/filter_latest_probe*.log`)
    found no such run among the 12 re-run runs it examined (2 in juniper-cascor's 300 most recent runs, 10 in
    juniper-ml's runs created 2026-11-07..16). The per-name latest from `filter=all` is right under either behaviour.
- The TestPyPI jobs are the names containing `testpypi` (case-insensitive), the same rule as the ceremony. Require at
  least one, and every one concluded `success`. Otherwise `::error::` listing each such job's name and conclusion, and
  exit 1. After A, both `Publish to TestPyPI` and `Verify the TestPyPI install` must be green.
- The artifact: that SAME run's unexpired `<package>-dist` gives `run-id`. Expired: the existing warning, and TestPyPI's
  JSON is the only record (unchanged).
- A consequence to document, not to engineer around: a version that a sub-package's PLAIN dispatch published has no
  release run whose TestPyPI jobs succeeded, so rung 1 refuses it. Rung 2 ("Re-run failed jobs") targets that dispatch
  run (item 7).

**C. `PUBLISH_TAG_PREFIX` (items 3, 22).** A third template env parameter: `v` in a single-package publisher,
`<package>-v` in a sub-package one (cascor: `juniper-cascor-model-v`, `juniper-cascor-protocol-v`).

- `Find the release run's artifact` accepts only `GITHUB_REF_TYPE == tag` with `tag.startswith(PUBLISH_TAG_PREFIX)`,
  and the version is the rest. A sub-package publisher dispatched from the meta `v` tag now refuses, before any API call.
- The env comment names all three parameters.
- Job-level `if:` cannot read `env`, so the build guards keep their literal prefixes. The checker cross-checks guard
  against parameter.

**D. Comment and doc corrections.**

- Item 1: the republish banner's "A dispatch run is not a release-event run, and the ceremony never reads one" is false
  since juniper-ml#2592: the monitor reads the publisher's dispatch runs and classifies a republish run by the run's own
  status. Say that. The name must still hold neither "testpypi" nor "pypi": `classify_publish_run` would otherwise
  count the job, skipped in every release run, as a PyPI job, and the job-level parked check would never fire.
- Item 2: the sub-package publishers' top comment "Each job adds what it needs to this": job-level `permissions`
  REPLACE the workflow block.
- Item 12: keep `startsWith(github.event.release.tag_name, 'v')`. Add a comment that an `rc*`/`hf*` convention
  (D2 of `notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`, juniper-ml) must widen it.
- Items 7, 11, 15, 20, 21, 26: the ladder (cascor `docs/ci_cd/MANUAL.md` § One Artifact, Checked Against TestPyPI and
  § Recovering a Release That Did Not Reach PyPI; `docs/ci_cd/REFERENCE.md` § One-Artifact Contract):
  - Rung 1 now refuses unless the release run's TestPyPI jobs succeeded in their latest attempt, and refuses when the
    tag has no release run.
  - A TestPyPI job that failed on index lag: "Re-run failed jobs" on the release run. It re-uploads the SAME bytes,
    which the index accepts (HTTP 200 for a byte-identical file), and repeats both checks.
  - A failed install check: a new patch version. "Fix; re-cut (idempotent)" is false for a same-version re-cut, because
    the index refuses new bytes under names it holds.
  - A failure of `Verify PyPI serves exactly these files` means the files are ALREADY on PyPI (the step runs after the
    upload).
  - The republish derives the version from the tag: a tag that is not `PUBLISH_TAG_PREFIX` + the exact version (e.g.
    data-client's `v0.3.1-beta`) cannot be republished, and fails safe.
  - The ladder holds only for tags cut after the publisher carries the job.
  - After a plain dispatch published, rung 2 targets that dispatch run.

**E. Test hardening (items 4, 5, 8, 9, 14, 17, 19), in cascor's `src/tests/unit/test_publish_one_artifact.py` now and
every port's copy later:**

- Retention pinned to exactly 90 (item 4).
- The reuse-condition exemption by the step's NAME (`Require a GitHub Release for this tag`), not by its `if:` text
  (item 5). That step is gated `github.event_name == 'push'` while no publisher has a push trigger, so it is dead. Keep
  it, and say so in the report.
- No template or check step carries an `if:` (except the reuse condition) or `continue-on-error`, and no job sets
  `continue-on-error` (item 9).
- Each job's EXACT step list, names and `uses` in order (item 14). This also refuses an extra step writing into `dist/`
  before `Record SHA256SUMS` (item 19).
- Workflow `name:` ends in "to PyPI" (item 17: juniper-ml#2592's monitor drops runs of any other workflow).
- The install check cannot be switched off: no `|| true` on its pip or python lines, no `continue-on-error`. Reject
  `skip_existing` (underscore) as well as `skip-existing`, and `attestations: false` (item 19).
- A's wiring, exactly: the new job's name, `needs`, permissions, no environment; PyPI `needs` both; the TestPyPI job's
  permissions and its lack of checkout.
- B's rehearsal against the existing stand-in GitHub API. Cases:
  - no release run: refuse;
  - the TestPyPI upload job failed in the latest attempt: refuse;
  - the install job failed: refuse;
  - a job green in attempt 1 and absent from attempt 2's records (carried): allowed;
  - attempt 1 failed, attempt 2 green: allowed;
  - "Re-run all jobs" whose attempt 2 failed after attempt 1 succeeded: refuse;
  - green with the artifact present: `run-id` set;
  - green with the artifact expired: the warning, `run-id` empty.
- C's rehearsal: a sub-package publisher refuses `v<version>`, and a single-package one refuses `<package>-v<version>`.
- Mutation proof: at least 8 mutations across A-C and the hardening, each failing the suite, each restored. Record
  them in the PR body.

**F. The cross-repo identity checker.** Do not edit the 2026-11-15 file: it is provenance of record for the 11-16 15/15
result and lands as-is with plan v1.15.17. Write `util/ad-hoc/2026-11-23_publish_port_template_identity.py`, a copy
plus:

- A's job checks, B's and C's template text, and `PUBLISH_TAG_PREFIX` in the env set. The prefix must equal `v` or
  `<PUBLISH_PACKAGE>-v` and agree with the build guard.
- The install check moves from the TestPyPI job to the new job.
- `uses:` compared by action name with the `@ref` dropped (item 23), so a Dependabot bump in one repo does not fail
  the check.
- The push exemption narrowed to the step named `Require a GitHub Release for this tag` (item 25).

It must PASS cascor's own three publishers (`publish.yml` against itself, and both sub-package publishers). Write it in
`$W/util/ad-hoc/` (mirror it there with `cp` if you work elsewhere).

**G. Item 23, for the ports only.** The ports that pin the template blocks' raw-text sha256 (data, cascor-client,
data-client, worker, ml) pin a NORMALIZED block instead: every `uses:` line reduced to the action name, its `@ref` and
trailing `# vX.Y.Z` dropped. A Dependabot bump then needs no re-port. cascor's own test pins no hash.

## The cascor PR (first executor)

- Files:
  - `.github/workflows/publish.yml`, `publish-protocol.yml`, `publish-cascor-model.yml`;
  - `src/tests/unit/test_publish_one_artifact.py`;
  - `docs/ci_cd/MANUAL.md` (the two sections), `docs/ci_cd/REFERENCE.md` (§ One-Artifact Contract), and wherever else
    cascor documents its publish pipeline (grep `AGENTS.md` and `docs/`; an `AGENTS.md` edit sets `**Last Updated**:`
    to `date -u`'s day);
  - `CHANGELOG.md`, one entry under `[Unreleased]`.
- Writer script: `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py --tree <fresh clone>`.
  - Exact-once anchored replacements (`replace_once`, as `util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py`
    does).
  - It refuses and writes nothing on any anchor miss.
  - It detects the wording as above.
  - Header as the 11-15 writer's (Project, Sub-Project, Author Paul Calnon, Created, Status, `Retire when: RETAINED`,
    Related, Why).
- Clone: a fresh `git clone` of `https://github.com/pcalnon/juniper-cascor` under YOUR worktree's `tmp/` (never a
  sibling primary checkout, never `/tmp`).
- Verification:
  - the full test file passes in conda env `JuniperCascor1`, plus every other test that pins publish text (grep
    `src/tests` for the three file names);
  - `actionlint` clean on all three workflows;
  - pre-commit on every changed file
    (`python3 -I $W/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py SRC DEST /opt/miniforge3/bin/pre-commit FILE...`
    or `/opt/miniforge3/bin/pre-commit run --files ...` in the clone);
  - the new checker PASS on all three;
  - the mutation proof.
- STOP before any push. Leave the clone, writer, evidence and a draft PR body (`tmp/sweep/cascor/pr_body.md`) and
  commit body in place, and report.
- Landing is the orchestrator's, after cascor#772 merges: re-run the writer on fresh `main`, re-test, the pre-push gate
  (`bash util/ad-hoc/2026-11-15_pre_push_gate_run.bash <gate dir>`), `run_open_signed_pr.py ARGS.json` (dry run
  first), `readback_branch.py`, CI, merge.

## Hard rules (in addition to `$W/tmp/ports/BRIEF.md` § Where to work, and hard rules)

- Never write under `/tmp` or `/var/tmp`. Never `git commit`, `git tag`, push, merge, arm auto-merge, update-branch,
  or open, close or edit a PR or issue.
- Never touch a rename PR's branch, any sibling primary checkout, or another session's worktree. Read-only `gh` GETs
  only.
- Quote only PR numbers, SHAs and run ids a tool printed. Do not put secrets, tokens, e-mail addresses or other personal
  data in any file or report.
- Commit trailers, when the orchestrator lands it (the LAST paragraph, nothing after):
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_016H76Ao6MysTB63dqf5Yr4W`. The PR body ends with
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`, a blank line, and
  `https://claude.ai/code/session_016H76Ao6MysTB63dqf5Yr4W`.

## Report back

- The writer's path.
- The clone's path and its `HEAD` (it must equal `origin/main` as fetched).
- `git diff --stat` and the full diff's path.
- Each verification's command and result: tests (counts), actionlint, pre-commit, the checker's lines, and the
  mutation table.
- Every judgement call, and anything in cascor that contradicts this brief.
