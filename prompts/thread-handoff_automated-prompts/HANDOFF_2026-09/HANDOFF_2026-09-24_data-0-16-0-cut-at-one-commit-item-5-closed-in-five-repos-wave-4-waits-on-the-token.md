# HANDOFF 2026-09-24 — data 0.16.0 cut at one commit, item 5 closed in all five repos, and Wave 4 still waits on the token

**Session**: container-registry rollout. It worked all five items of the predecessor named below,
cut juniper-data v0.16.0 after resolving two conflicting owner rulings, and put the serve-and-version
check on the publish path of all five image repos.
**This file**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-cut-at-one-commit-item-5-closed-in-five-repos-wave-4-waits-on-the-token.md`.
Read it from `main`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_worker-0-6-1-shipped-equities-joins-the-data-image-lock-and-wave-4-waits-on-the-owner-token.md`
(`…waits-on-the-owner-token.md` below), **SUPERSEDED** by this file. It is history only; do not act
on its items. Its Wave 4 section is carried below, not by reference.
**Times are UTC.** Live state was last probed at 2026-09-24 09:24Z.
**Status: SUPERSEDED** (2026-09-24, about 20:00Z). It is history only; do not act on its items.
**Successor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`.
That file carries this one's live items. Its Remaining items 1 and 2 are done: the PyPI deploy was
approved and recorded, and the deploy repin is juniper-deploy#230.

## Handoff goal — paste from the next line down to the line `— END OF GOAL —`

Continue the **container-registry rollout**. Three documents govern it, and every section
reference below names its document:

- `…PUBLISHING-PLAN.md` is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, the design of record.
- `…REGISTRATION-PROCEDURE.md` is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`, Wave 4's credential steps.
- `…PYPI-PUBLISH-PROCEDURE.md` is `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`. `…PYPI-PUBLISH-PROCEDURE.md` §11.7 covers how the ceremony sets GitHub's Latest badge (from the registry's `latest:` flag, not a CLI flag) and its `--target-sha` option.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`,
`prompts/`, `util/` or `tests/` are inside `juniper-ml/` unless a repo is named.

### Rules that bind you

- **Every merge YOU perform needs the owner's explicit approval, naming that PR or group, in YOUR
  session.** An approval given to an earlier session does not carry over. `gh pr merge --auto` on a
  MERGEABLE PR merges it on the spot, and an `update-branch` on an armed PR completes its merge.
- **The PR sweeper is the owner's** (ruled 2026-09-24: "Mine: fix forward"). It readies and arms
  open PRs as `pcalnon`, and its merges are the owner's own and intended. **Do not draft or disarm
  a PR to hold it.** If a change must be validated before it can merge, validate it before the PR
  exists. Create the branch with
  `gh api -X POST repos/pcalnon/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<main sha>`, and
  commit with `python3 util/push_signed_commit.py --repo <repo> --branch <branch> --expected-head <main sha> …`.
  Validate that branch, and only then open the PR with
  `gh pr create --repo pcalnon/<repo> --head <branch> --base main`. Otherwise fix forward.
- **Commit only through the GitHub API**: `python3 util/open_signed_pr.py`, or
  `python3 util/push_signed_commit.py --expected-head <full 40-char sha>`. Never `git push` and
  never sign locally, because the YubiKey hangs. Never use `PUT /contents`: its commit is unsigned,
  which blocks the merge with every check green. **Before every upload, re-probe the target repo's
  `commits/main` and diff each file**, because the helpers send whole files.
- **Never handle the Docker Hub token.** Run no `gh secret set` or `gh variable set` for it. If the
  token appears in chat, do not repeat it or use it. Tell the owner it is exposed and must be
  deleted at Docker Hub first (`…REGISTRATION-PROCEDURE.md` §8), then replaced.
- **Never approve a `pypi` environment gate.** The owner approves every deploy. Run
  `util/release_train/ceremony.py --execute` only after the owner approves, in your session, both
  the cut and the auto-merge of the juniper-ml archive PR it opens. There is no cut-only mode: the
  tool arms that auto-merge before it cuts.
- Re-probe every claim before acting on it, this file's included. Scripts go in `util/ad-hoc/`,
  never `/tmp`. The owner ruled on 2026-09-21 that no live memory is retired to meet the MEMORY.md
  target.

### Owner gates — tell the owner; you run none of them

1. **PyPI for juniper-data 0.16.0.** Run 35977786108's `Publish to PyPI` job waits at the `pypi`
   environment. After the owner approves, see Remaining item 1.
2. **Wave 4's credential.** The owner runs `…REGISTRATION-PROCEDURE.md` §2, §5.2B step 3a, §4,
   §5.2B step 3 and §6, in that order. `…REGISTRATION-PROCEDURE.md`'s header lists the steps and
   holds every command. Point the owner there; do not restate them. The owner then tells you four
   things: that the `…REGISTRATION-PROCEDURE.md` §4 login succeeded; which form
   `…REGISTRATION-PROCEDURE.md` §5.2B step 3a used; the Docker ID; and the token's expiry date.
3. **Who repins juniper-deploy from data 0.15.0 to 0.16.0.** Other sessions made the last two
   repins (juniper-deploy#227, #229). Ask the owner who takes this one.
4. **Still open from earlier handoffs**: OQ-2, OQ-3 and OQ-4 (`…PUBLISHING-PLAN.md` §6); the Pi
   pull (`…PUBLISHING-PLAN.md` §5.1; below the goal); and whether `juniper-deploy-test` goes to
   Docker Hub (`…REGISTRATION-PROCEDURE.md` §10).

### Remaining — yours once its condition holds

1. **After the owner approves PyPI.**
   - In run 35977786108, confirm the jobs `Publish to PyPI` and `Notify consumer repos` succeeded.
     The `pypi` job is the publish verdict (juniper-data#426). `Notify consumer repos` appears in
     the run only after `pypi` finishes. Since juniper-data#431 it waits up to about two minutes
     for juniper-recurrence to start a `juniper-data-published` run. If only it failed, the release is
     fine, but the consumer was not notified: tell the owner.
   - Confirm `https://pypi.org/pypi/juniper-data/0.16.0/json` answers. Use the version-specific
     URL, because the aggregate one lags.
   - By PR, update `…PUBLISHING-PLAN.md` in two places: its status block (*State at 2026-09-24*:
     *"Its PyPI deploy waits on the owner"*) and §5.2's 0.16.0 paragraph (*"PyPI waits on the
     owner's approval"*).
   - Ask the owner before editing the parent `Juniper/AGENTS.md` Data Contract, which is
     unversioned and has no PR. It should say that arc_agi's `generator_version` is `4.0.0` from
     juniper-data 0.16.0 (juniper-data#430), and list 0.16.0 among the versions that moved.
2. **The juniper-deploy repin, once the owner assigns it to you** (Owner gate 3). It covers
   juniper-deploy's `docker-compose.yml:164` and `:517` (the demo seed),
   `k8s/helm/juniper/values.yaml:40`, and juniper-deploy's `CHANGELOG.md`.
   `scripts/verify_published_images.py` already reports the pin as STALE. Check for an open deploy
   PR first.
3. **When the owner reports the four Wave 4 facts**: record the token's expiry date in
   `…REGISTRATION-PROCEDURE.md` §10 by PR.
4. **The Wave 4 workflow change, only when BOTH hold.**
   - **(a)** Plain `gh api` calls, per repo, check the credential. **Names only**: every listing
     call carries `--jq '[.secrets[].name]'` or `--jq '[.variables[].name]'`, because a bare GET
     of a variables endpoint prints values.
     - `environments/dockerhub/secrets` lists `DOCKERHUB_TOKEN`, plus `DOCKERHUB_USERNAME` if the
       owner chose a secret, and nothing else.
     - `environments/dockerhub/variables` lists `DOCKERHUB_USERNAME` if the owner chose a
       variable, and nothing else.
     - `actions/secrets` and `actions/variables` list no `DOCKERHUB_*`.
     - `environments/dockerhub/deployment-branch-policies`, with
       `--jq '[.branch_policies[] | .type + ":" + .name]'`, still shows `tag:juniper-*-v*` and
       `tag:v*`.
     - For a variable, check the value only as a boolean:
       `--jq '.variables[] | select(.name=="DOCKERHUB_USERNAME") | (.value=="<Docker ID>")'`.
       Never print it. A `false` means only that the value is not the Docker ID the owner reported.
       Ask the owner to look with `…REGISTRATION-PROCEDURE.md` §6, which shows it to them.
   - **(b)** The owner has told you, in your session, that the `…REGISTRATION-PROCEDURE.md` §4
     login succeeded.
   - Then: **never name `dockerhub` unconditionally on the existing `build` or `merge` job**,
     because both also run on pull requests or dispatches, and a tags-only environment rejects
     those runs. Pick a shape from `…REGISTRATION-PROCEDURE.md` §3 and §7. Read the username from
     the context the owner chose (`vars.` or `secrets.`). Give each new job its repo's release-tag
     guard as a job-level `if:` (`'v'`, or `'juniper-recurrence-v'` in recurrence). **Never pass
     the credential as a `--build-arg`**: build-arg values are published in public SLSA provenance.
     Ask the owner before editing the five `publish-image.yml` files.
5. **Known gaps**, listed below the goal with a *fix* or *track* verdict each. None is time-bound.

### Key context

- **Two owner rulings on 0.16.0 conflicted across sessions.** At 07:45Z this session was told to
  pin the cut to `7125e161` and move #428, #431 and #434 to `[Unreleased]`. At 08:03Z, on
  juniper-data#435, another session recorded "0.16.0 carries #428" and folded them in, reasoning
  that the ceremony could not pin a commit, which juniper-ml#2071 was about to change. Put back to
  the owner, the fold governed, with the cut pinned. **If a later ruling in another session rests
  on a premise your session is changing, ask the owner. Do not pick one.**
- **An armed, CLEAN PR may still not merge.** juniper-ml#2071 sat that way;
  `python3 util/safe_merge.py --repo <repo> --pr <n> --merge-method squash --execute` merged it.
  Read its `MERGED` line, never its exit status. juniper-ml's ruleset is `strict`: once the owner
  approves that merge in your session, a `BEHIND` PR needs
  `gh api -X PUT repos/pcalnon/<repo>/pulls/<n>/update-branch`, one PR at a time.
- **Read *Traps* below the goal before running commands.**

— END OF GOAL —

---

## Traps

- **A worktree-isolated shell refuses compound commands that also run `git` or `gh`** when it
  cannot prove where they point. This session saw refusals for loops over runtime values, `awk`
  programs, function definitions, variable-built command paths and `python -c` chains. Split them
  into plain commands with literal paths.
- **Verify the published artifact, not the merge.** Pull an image before measuring it, because
  `2>&1 | wc -l` counts pull progress. `find … | wc -l` cannot tell an absent path from an
  unreadable one.

## Verification commands

```bash
# The cut: the tag, the badge, and the two release runs
gh api repos/pcalnon/juniper-data/git/ref/tags/v0.16.0 --jq .object.sha   # 39d1cab27a2067b8b00a5d44a8a37a739bd1d1ed
gh api repos/pcalnon/juniper-data/releases/latest --jq .tag_name          # v0.16.0
gh run view 35977786108 --repo pcalnon/juniper-data --json jobs --jq '.jobs[] | "\(.name): \(.status) \(.conclusion)"'
gh run view 35977785708 --repo pcalnon/juniper-data --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-data/0.16.0/json   # 404 until the owner approves

# The 0.16.0 notes archive (merged 2026-09-24 09:16Z)
gh pr view 2076 --repo pcalnon/juniper-ml --json state,mergedAt

# The published image: equities, then item 5's check with juniper-data's own script
docker pull ghcr.io/pcalnon/juniper-data:0.16.0
docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-data:0.16.0 -c "import importlib.util as u; from juniper_data.generators.equities import generator as g; print(g.EQUITIES_DEPS_AVAILABLE, u.find_spec('yfinance') is not None)"   # True True
gh api repos/pcalnon/juniper-data/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" > <scratchpad>/check_image_serves.py
python3 <scratchpad>/check_image_serves.py --image ghcr.io/pcalnon/juniper-data:0.16.0 --dist juniper-data --module juniper_data --port 8100 --expect-version 0.16.0   # exit 0

# Item 5 on every main (expect 41225ac2 five times)
gh api repos/pcalnon/juniper-cascor-worker/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" | sha256sum | cut -c1-8
gh api repos/pcalnon/juniper-cascor/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" | sha256sum | cut -c1-8
gh api repos/pcalnon/juniper-canopy/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" | sha256sum | cut -c1-8
gh api repos/pcalnon/juniper-data/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" | sha256sum | cut -c1-8
gh api repos/pcalnon/juniper-recurrence/contents/util/check_image_serves.py -H "Accept: application/vnd.github.raw" | sha256sum | cut -c1-8

# The stale data pin
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" | grep -n 'juniper-data:0'
```

## What this session did

| item | PR | merged | what |
| --- | --- | --- | --- |
| 1 | juniper-data#430 | 2026-09-23 20:02Z `90ad035e` | another session's; merged on the owner's approval. arc_agi `VERSION` 4.0.0, closing #427 and #429 |
| 1 | juniper-data#433 | 2026-09-23 20:24Z `7125e161` | the 0.16.0 bump, on `release/juniper-data-v0.16.0` |
| 1 | juniper-ml#2071 | 2026-09-24 08:51Z `b8165386` | `ceremony.py --target-sha`, and `commit_ci_verdict` |
| 1 | Release v0.16.0 | cut 2026-09-24 08:52Z | tag at `39d1cab2` (juniper-data#435's merge), Latest |
| 1 | juniper-ml#2076 | 2026-09-24 09:16Z `602094e3` | the ceremony's archive, `notes/releases/RELEASE_NOTES_juniper-data_v0.16.0.md` |
| 2 | juniper-cascor-worker#195 | 2026-09-23 19:50Z `73c6e76b` | `lockfile-update.yml` skips `release/` branches; juniper-cascor-worker's `CHANGELOG.md` records 0.6.1's unannounced lock refresh |
| 3 | juniper-ml#2056 | 2026-09-23 20:39Z `8d187b5f` | the `dockerhub` drift gate |
| 4 | juniper-ml#2055 | 2026-09-23 19:50Z `7fb40892` | the Latest badge per the registry's `latest:` flag; six stale badges moved by hand |
| 5 | juniper-cascor-worker#196, juniper-recurrence#186, juniper-cascor#684, juniper-canopy#679, juniper-data#436 | 2026-09-24 01:21Z to 08:57Z | `util/check_image_serves.py` on the publish path; table in `…PUBLISHING-PLAN.md` §5.3 |
| — | the PR archiving this file | — | this file; `…waits-on-the-owner-token.md` marked SUPERSEDED; `…PUBLISHING-PLAN.md` (status, §5 table, §5.2, new §5.3); `util/ad-hoc/2026-09-21_image_does_its_job_sweep.py` v2.0.0; new `util/ad-hoc/2026-09-23_arc_agi_dataset_id_probe.py` |

**GitHub settings**: the Latest badge moved on six repos under item 4, and v0.16.0 is Latest in
juniper-data.

**A rule broken, and no harm done.** This session drafted juniper-data#436 at about 08:47Z to hold
it until the cut, and un-drafted it after the cut. That went against the owner's 2026-09-24 sweeper
ruling, which this session had not read. The draft held, and the PR merged green after the cut.

**Outside git (harness memory)**: `project_container_registry_rollout_2026-09-08.md` and
`reference_release_train_ceremony_traps_2026-09-09.md` gained 2026-09-23/24 sections.

## How the 0.16.0 cut was decided

1. juniper-data#433's bump merged at 20:24Z on 09-23, and the owner approved cutting `7125e161`
   with a five-entry notes preview.
2. Before the cut, #428, #431 and #434 merged. #428's entries in juniper-data's `CHANGELOG.md`
   straddled the bump and left a second `## [0.16.0]` heading above the real one. The ceremony
   renders the **first** match, so a cut from `main` would have published only #428's bullets.
3. At 07:45Z the owner ruled: pin the cut to `7125e161` through a new `--target-sha`, and move the
   three to `[Unreleased]`. juniper-ml#2071 added the option. Its second commit fixed the gate for
   a commit whose green push run was followed by a superseded, `cancelled` `repository_dispatch`
   run.
4. At 08:03Z another session, on juniper-data#435, recorded "0.16.0 carries #428" and folded all
   three into `[0.16.0]`. #435 was armed at 08:04Z.
5. Asked which ruling governed, the owner chose the fold, with the cut pinned to #435's merge
   commit. The folded notes were the approved five entries byte-for-byte, plus #428's `ETag`
   feature (including a **Breaking** change: the access counters leave every metadata
   representation), #434's review round and #431's consumer-notification fix.
6. #435 merged at 08:14Z as `39d1cab2`. The ceremony ran with
   `--target-sha 39d1cab27a2067b8b00a5d44a8a37a739bd1d1ed --release-date 2026-09-23`. The Release
   body and `notes/releases/RELEASE_NOTES_juniper-data_v0.16.0.md` are byte-identical to the
   approved preview. The date matches the heading in juniper-data's `CHANGELOG.md`.

## Known gaps no gate catches (verdict per gap)

- **Track; cosmetic only.** juniper-cascor's `CHANGELOG.md` `[Unreleased]` carries `### Added`
  twice and `### Fixed` twice (lines 35 and 264, and 115 and 312, at `main` `d9220103`; the numbers
  move with every merge). No bullet is lost: `util/release_train/ceremony.py`'s
  `changelog_version_section` merges repeated category headings (its docstring records why). The
  harmful shape is a duplicated **version** heading, which the ceremony reads first-match only; that
  is what #428 left in juniper-data. juniper-cascor's released `[0.11.0]` section repeats
  `### Fixed` too.
- **Fix, when someone next edits the worker image.** Its `HEALTHCHECK` is `kill -0 1`
  (`Dockerfile:119-120`), which proves only that PID 1 has not died. The Helm chart's default falls
  back to the same probe (`k8s/helm/juniper/values.yaml:336-337`). juniper-deploy's compose already
  overrides it with an HTTP `/v1/health/ready` probe.
- **Fix, low priority.** `juniper-cascor-worker/.env.example:9` ships `CASCOR_AUTHKEY=juniper`.
- **Track.** The worker's source-checkout fallback literal reads `"0.6.0"` at 0.6.1
  (`juniper_cascor_worker/__init__.py:35`). juniper-data#433 bumped data's. The release train edits
  neither; installed artifacts read metadata.
- **Track; it ends at cascor's next release.** The published cascor 0.11.0 reports `0.6.0`:
  `__version__` in the wheel, and `meta.version` in the image's envelopes. juniper-cascor#672 fixes
  both from the next release, whose publish run is the first to run item 5's publish-arm check in
  cascor. The published 0.11.0 fails that check for good.
- **Track.** The stale-pin check (juniper-deploy#226) is advisory: no schedule, no
  `--fail-on-stale`. It flags the data pin today.
- **Track.** The release train does not count image-only or packaging-config changes as ship
  changes (`…PUBLISHING-PLAN.md` §5.2).
- **Track.** worker#194's lock refresh (`bca33c99`) was never functionally tested. filelock moved to
  4.0.1, with fsspec and networkx. An import check on the published 0.6.1 image passed.
- **Track; binds Wave 4.** Build-arg values are published in public SLSA provenance (goal,
  Remaining item 4).
- **Track; a local gate only.** The `dockerhub` drift gate's live half skips in per-PR CI. Run it with
  `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_publish_env_policy_drift.py`.

**The Pi pull** (`…PUBLISHING-PLAN.md` §5.1) is still owed before any Pi runs a Juniper image. It is
an anonymous GHCR pull of the newest worker release, 0.6.1, and it needs a 64-bit Pi OS. `turing`
was reported down on 09-22. After Wave 4, pulls from docker.io follow `…REGISTRATION-PROCEDURE.md`
§9: the nodes log in with their own read-only token, and nodes that share one account share its
200 pulls per 6 h. None of that applies to the GHCR pull.

**Mechanisms worth keeping** (the detail is in `…PUBLISHING-PLAN.md` §5.2): only committed files
reach a CI-published image; a bare `.dockerignore` pattern matches the context root only; the
check unit is the context root; a `/app`-only scan passes vacuously; never blanket-add `**/logs/`, because canopy's is a symlink.

## Validation record

**Round 1: two independent read-only lanes on the frozen v1 draft (frozen 09:02Z). Both returned
FAIL.**

| lane | lens | verdict |
| --- | --- | --- |
| A | re-probe every fact against GitHub, GHCR and PyPI, and run every verification command | FAIL: 1 critical, 3 major, 7 minor, plus moved-since items |
| B | residue loss against `…waits-on-the-owner-token.md`, item by item; cold read as the next session and as the owner | FAIL: 2 major, 10 minor; no major residue loss |

**Both lanes converged on the top finding.** v1 told the next session to draft a PR to hold it. That
contradicts the owner's 2026-09-24 sweeper ruling, recorded in harness memory
`reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`. v2 fixes the following:

- The sweeper rule now sits in *Rules*.
- juniper-ml#2076 had merged, so its Remaining item is gone.
- The probe time and the git state were wrong; both are re-stamped.
- cascor's duplicate **category** headings were called harmful. `ceremony.py`'s
  `changelog_version_section` merges them, so they are cosmetic.
- `ceremony.py` has no `--latest` flag; the badge comes from the registry.
- recurrence's tag guard compares against `_version.py`, and the drift gate is local-only and checks
  four things. `…PUBLISHING-PLAN.md` §5.3 and its status block now say so. `…PUBLISHING-PLAN.md`
  §5.2 no longer calls #428 "still open".
- Owner-gate items that were the session's own actions moved to *Remaining*. Every known gap now
  carries a *fix* or *track* verdict.
- Dropped residue is restored:
  - the boolean-`false` recovery;
  - `turing`, and the post-Wave-4 docker.io note;
  - the mechanisms worth keeping;
  - the shell refusals;
  - the `--auto` and `update-branch` traps;
  - the ceremony approval rule.
- Every document reference carries its filename.

The writing session re-probed each change: cascor's heading lines at `main` `d9220103`,
recurrence's `publish-image.yml:282-284`, `ceremony.py`'s `changelog_version_section`, and the
job display name at juniper-data `publish.yml:77-78`.

**Round 2: one reconciliation lane on v2 (frozen 09:24:40Z). PASS.** Every round-1 finding was
closed except one residue item, which was partly closed. No critical or major finding was
introduced. The final version fixes its six minor findings and nits:

- the pre-PR validation path is now executable with the allowed tools (create the ref, push a
  signed commit, then `gh pr create`);
- the `update-branch` trap is conditioned on the owner's approval in the session;
- juniper-cascor's `[0.11.0]` reference names its file;
- both wordings of the plan's PyPI sentence are quoted;
- restored residue: the ecosystem root, "no cut-only mode", why to pull before measuring, the
  context-root check unit, and §9's shared-account allowance;
- the shell-refusal note is scoped to compound commands that run `git` or `gh`;
- the branch count, the lane-A tally, the notify wait ("up to") and the two missing gap verdicts
  are corrected.

No round 3 was run on these fixes. That matches the predecessor, whose final version also folded
its PASS round's minor findings without another round.

**Not fixed:** the goal is 1,261 words, about 5% over the ~1,200 target. The excess is the
executable pre-PR validation path, which is safety text that a pointer would weaken; two traps
moved below the line to keep it near the target.

## Git state

- This session's worktree is `juniper-ml/.claude/worktrees/fluffy-sniffing-mochi`, on local branch
  `wip/records-0924`. That branch's unsigned scratch commits exist only to run the screens; the
  PR's commit is GitHub-signed through the API.
- Six local `wip/*` branches exist, none ever pushed; five hold unsigned scratch commits:
  - `wip/ceremony-latest-flag`, `wip/dockerhub-drift-gate` and `wip/ceremony-target-sha` reached
    `main` as juniper-ml#2055, #2056 and #2071;
  - `wip/adhoc-scripts` and `wip/records-0924` reach it through the PR archiving this file;
  - `wip/ceremony-run-data-0160` has no commits of its own.

  All six can be deleted once that PR merges.
- The session created no sibling worktrees.
