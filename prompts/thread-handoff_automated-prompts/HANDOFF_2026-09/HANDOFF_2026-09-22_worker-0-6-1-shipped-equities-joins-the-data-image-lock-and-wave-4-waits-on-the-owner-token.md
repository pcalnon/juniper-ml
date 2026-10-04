# HANDOFF 2026-09-22 — Worker 0.6.1 shipped, equities joins the data image lock, and Wave 4 waits on the owner's token

**Session**: container-registry rollout. It worked the startable items of the predecessor named
below, recorded three owner rulings, released the worker, and prepared Wave 4 up to the credential.
**This file**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_worker-0-6-1-shipped-equities-joins-the-data-image-lock-and-wave-4-waits-on-the-owner-token.md`.
Read it from `main`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`
(`…still-reports-0-4-0.md` below), **SUPERSEDED** by this file. It is history only; do not act
on its items.
**Times are UTC.** The host is CDT (UTC−5), so this file is dated 09-22 local while its last
events are 09-23 UTC. Live state was last probed at 2026-09-23 13:09Z.
**Successor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-cut-at-one-commit-item-5-closed-in-five-repos-wave-4-waits-on-the-token.md`
**Status**: **SUPERSEDED 2026-09-24 by the successor above**, which carries what is still open.
All five items were worked:

- item 1: juniper-data v0.16.0 was cut on 2026-09-24, pinned to `39d1cab2`, with PyPI waiting on
  the owner;
- items 2 to 4: juniper-cascor-worker#195, juniper-ml#2056 and juniper-ml#2055;
- item 5: the serve-and-version check, merged in all five image repos.

**This file is history only. Do not paste its goal and do not act on its items.** Among the
statements overtaken:

- *Data release recipe* step 5 says `ceremony.py` passes no `--target`. Since juniper-ml#2071 it
  can, through `--target-sha`.
- The 0.16.0 cut folded in data#428, #431 and #434, which merged after the bump. The owner ruled on
  2026-09-24 which way to go; the successor records how.

## Handoff goal — paste from the next line down to the line `— END OF GOAL —`

Continue the **container-registry rollout**. Two documents govern it, and every section
reference below names its document:

- `…PUBLISHING-PLAN.md` is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, the design of record.
- `…REGISTRATION-PROCEDURE.md` is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`, Wave 4's credential steps.

This handoff is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_worker-0-6-1-shipped-equities-joins-the-data-image-lock-and-wave-4-waits-on-the-owner-token.md`.
Read it from `main`, through `gh api repos/pcalnon/juniper-ml/contents/<that path>` or a checkout
made after it merged. Its sections below the goal are part of it: item 1 needs its *Data release
recipe*, and item 5 its *Item 5 detail*.
**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`,
`prompts/`, `util/` or `tests/` are inside `juniper-ml/`.

### Rules — read before acting

- **Every merge needs the owner's explicit approval, naming that PR or group, in YOUR session.**
  That includes the archive PR that `ceremony.py --execute` opens and arms for auto-merge by
  itself. A handoff, an earlier message or green CI is not approval. `gh pr merge --auto` on a
  mergeable PR merges at once.
- **Commit only through the GitHub API.** The helpers are mode 644, so run them with `python3`.
  - Open a PR with `python3 util/open_signed_pr.py --repo <bare repo name> --branch <b> --add LOCAL:REPOPATH --message <headline> --title <t> --body-file <f>`.
    Trailers go in `--commit-body-file`.
  - Add follow-up commits with `python3 util/push_signed_commit.py`, which juniper-ml#2036
    promoted at 06:21Z. It needs `--expected-head <full 40-char sha of the branch head>`. It
    supersedes `util/ad-hoc/2026-09-08_append_signed_commit.py`.
  - Never `git push` and never sign locally; the YubiKey hangs. Never use `PUT /contents`: its
    commit is unsigned, which blocks the merge with every check green.
  - **Before every upload, re-probe the target repo's `commits/main` and diff each file.** The
    helpers send whole files.
- **The shell is worktree-isolated.** It refuses loops, `$(…)` around `gh`, heredocs piped into
  `python3 -`, and git against sibling repos. Run one plain command per call. Read sibling files
  with `gh api repos/pcalnon/<repo>/contents/<path>`.
- **Never handle the Docker Hub token.** Run no `gh secret set` or `gh variable set` for it.
  If the token appears in chat, do not repeat it or use it. Tell the owner it is exposed and must
  be deleted at Docker Hub first (`…REGISTRATION-PROCEDURE.md` §8), then replaced by a new one.
- **Re-probe every claim here before acting on it.** Seven or more sessions run concurrently.

### Verify first

```bash
gh api repos/pcalnon/juniper-ml/contents/notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md --jq .content | base64 -d | grep -c 'Step 3a: the username'
#   prints 1. If gh itself errored, the count means nothing: fix the call first. A clean 0 means
#   this handoff's PR (branch docs/handoff-2026-09-22-worker-061-wave4-owner-token) has not
#   merged, and main's procedure still carries defects: stop, and ask the owner to merge it.
gh api repos/pcalnon/juniper-cascor-worker/releases/latest --jq .tag_name                       # v0.6.1
gh pr view 428 --repo pcalnon/juniper-data --json state --jq .state                              # OPEN at 13:09Z; item 1 either way
gh release list --repo pcalnon/juniper-data --limit 1                                             # v0.15.0 at 13:09Z: no 0.16.0 yet
gh api repos/pcalnon/juniper-data/environments/dockerhub/secrets --jq '[.secrets[].name]'       # [] until the owner registers
gh api repos/pcalnon/juniper-data/environments/dockerhub/variables --jq '[.variables[].name]'   # [] until the owner registers
```

In `juniper-ml`, `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_publish_env_policy_drift.py`
should report 17 OK.

### Owner rulings, 2026-09-22 — do not re-litigate

1. **The Docker Hub credential lives in a `dockerhub` environment** (Option B,
   `…REGISTRATION-PROCEDURE.md` §3; juniper-ml#2009). All five environments exist
   (juniper-ml#2011). Each admits tags `v*` and `juniper-*-v*` only, with no reviewer, no wait
   timer and nothing registered. Whether the username is a secret or a variable is still open
   (owner task 2).
2. **Worker v0.6.1 is released**: on PyPI since 00:37Z on 09-23, and its image prints
   `0.6.1 0.6.1`. The Latest badge was moved to it on the owner's instruction.
3. **The juniper-data image includes equities.** juniper-data#421 merged at 00:56Z on 09-23
   (`68c3cd7c`), with the owner's approval in the writing session. It adds `--extra equities` to
   the image lock. No published image has it until the next data release (item 1).

### Owner tasks — the owner runs these, you run none

The commands and their hazards live only in `…REGISTRATION-PROCEDURE.md`, whose header lists
these steps in the same order. Point the owner there; do not restate them.

1. `…REGISTRATION-PROCEDURE.md` §2: confirm the account, its exact Docker ID, and that new Docker
   Hub repositories default to public.
2. `…REGISTRATION-PROCEDURE.md` §5.2B step 3a: choose the username as a variable (recommended,
   because it can be read back) or a secret.
3. `…REGISTRATION-PROCEDURE.md` §4: create the Read & Write token, keep it in a password manager,
   and test it in a throwaway Docker config **before** registering it.
4. `…REGISTRATION-PROCEDURE.md` §5.2B step 3: five username commands, typed, then five token
   commands, pasted at the hidden prompt.
5. `…REGISTRATION-PROCEDURE.md` §6: verify. Then tell you four things: that the
   `…REGISTRATION-PROCEDURE.md` §4 login succeeded, which form its §5.2B step 3a used, the Docker
   ID, and the token's expiry date.

When the owner reports, record the expiry date in `…REGISTRATION-PROCEDURE.md` §10 by PR.

### Wave 4 workflow change — only when BOTH hold

**(a)** Plain `gh api` calls, per repo, check the credential. **Names only**: every listing call
carries `--jq '[.secrets[].name]'` or `--jq '[.variables[].name]'`, because a bare GET of a
variables endpoint prints values, and a token pasted into a variable would land in your transcript.

- `environments/dockerhub/secrets` lists `DOCKERHUB_TOKEN`, plus `DOCKERHUB_USERNAME` if the owner
  chose a secret, and nothing else.
- `environments/dockerhub/variables` lists `DOCKERHUB_USERNAME` if the owner chose a variable, and
  nothing else.
- `actions/secrets` and `actions/variables` list no `DOCKERHUB_*`.
- `environments/dockerhub/deployment-branch-policies`, with
  `--jq '[.branch_policies[] | .type + ":" + .name]'`, still shows `tag:juniper-*-v*` and `tag:v*`.
- For a variable, the value is checked as a boolean:
  `--jq '.variables[] | select(.name=="DOCKERHUB_USERNAME") | (.value=="<Docker ID>")'`. Never
  print it. A `false` means only that the value is not the Docker ID the owner reported. Ask the
  owner to look with `…REGISTRATION-PROCEDURE.md` §6, which shows it to them.

**(b)** The owner has told you, in your session, that the `…REGISTRATION-PROCEDURE.md` §4 login
succeeded.

- **Never name `dockerhub` unconditionally on the existing `build` or `merge` job.** Both also
  run on pull requests or dispatches, and a tags-only environment rejects those runs.
  juniper-ml#1151 saw a `--ref main` dispatch fail against `testpypi` with zero steps.
- Pick a shape from `…REGISTRATION-PROCEDURE.md` §3 and §7. This session prefers its shape 1, a
  release-only third job that copies the verified GHCR index by digest. A dry run carried both
  arch manifests and both attestations. A real push is untested.
- Read the username from the context the owner chose: `vars.DOCKERHUB_USERNAME` or
  `secrets.DOCKERHUB_USERNAME`. The other one evaluates to empty and fails at release time.
- Each new job carries its repo's release-tag guard as a job-level `if:`. The guard is `'v'` in
  four repos and `'juniper-recurrence-v'` in recurrence.
- **Ask the owner before editing the five `publish-image.yml` files.** Item 5 edits the same
  files, and another session said it was evaluating item 5.

### Startable now — open PRs; merges and cuts need the owner

1. **juniper-data 0.16.0, carrying #420, #421, #422 and #426.** Nothing will open it for you.
   - Since data#422 merged at 06:22Z, `detect.py` says `UNRELEASED_CHANGES` (minor). Before
     that, it said `UP_TO_DATE`: #421 touched no ship path, and #420's `pyproject.toml` edit is
     discounted as tooling.
   - The daily release train only reports, so no PR opens by itself. Open a hand-made bump PR.
     data#428, still open, edits ship paths too.
   - First check that no open juniper-data PR is on a `release/juniper-data-v*` branch.
   - Follow the *Data release recipe* below the goal.
   - **Run `ceremony.py --execute` only after the owner approves, in your session, both the cut
     and the auto-merge of the juniper-ml archive PR it opens.** There is no cut-only mode. The
     tool arms that auto-merge before it cuts, and prints the PR only when it finishes, so there
     is no race-free way to disarm it. If the owner approves only the cut, do not run it.
2. **The worker's `lockfile-update.yml` lacks the `release/` skip** that data, cascor and canopy
   have. That is how worker#194, a version-only PR, picked up a lock refresh that shipped in
   0.6.1.
3. **A drift gate for `dockerhub`.** `tests/test_publish_env_policy_drift.py` needs tag sets
   **and** repo sets per environment. For `dockerhub` the repo set is the five image repos; three
   of the registry's eight repos have no image.

### Needs an owner ruling first

4. **`ceremony.py:836` always passes `--latest=false`.** That is a sub-package rule from §11.4 of
   `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`, and here it lands on the
   sibling repos' own packages. Four repos' Latest badges are stale; the list is below the goal.
   Get the ruling before item 1's cut.
5. **Publish-path checks.** Add a liveness serve check on `/v1/health`, since all five images
   serve HTTP and `/ready` needs backing services. Add a version-vs-metadata check too. **cascor's
   image has no `juniper_cascor` package**, so an import-based check can never pass there. Read
   *Item 5 detail* below the goal before designing either check.

### Also owner-gated

- OQ-2, OQ-3 and OQ-4 (`…PUBLISHING-PLAN.md` §6).
- The Pi pull (`…PUBLISHING-PLAN.md` §5.1).
- Whether `juniper-deploy-test` goes to Docker Hub (`…REGISTRATION-PROCEDURE.md` §10).

### Traps

- juniper-ml's ruleset is `strict`. Once the owner approves, arm auto-merge. If the PR is
  `BEHIND`, run `gh api -X PUT repos/pcalnon/juniper-ml/pulls/<n>/update-branch`, one PR at a
  time. `safe_merge.py` timed out and disarmed twice this session.
- Pull an image before measuring it, because `2>&1 | wc -l` counts pull progress. And
  `find … | wc -l` cannot tell an absent path from an unreadable one.
- Verify the published artifact, not the merge. Re-probe agent verdicts.
- **Two items below the goal bind you:**
  - Build-arg values are published in public SLSA provenance, so Wave 4 must never pass the
    credential as a `--build-arg`.
  - The owner ruled on 2026-09-21 that no live memory is retired to meet the MEMORY.md target.

— END OF GOAL —

---

## Data release recipe (item 1)

**Before the bump PR**, ask the owner whether the fix for juniper-data#427 should ride 0.16.0.
Another session filed that issue at 01:46Z. It proposes bumping arc_agi's generator `VERSION`,
because #402 changed its `task_type` without one, so a cached pre-0.15.0 artifact keeps fabricated
class metadata. It is a data-contract change. Its fix PR, of which none existed at 13:09Z, must
merge before the bump PR, or it waits for the next release.

**The bump PR**, on branch `release/juniper-data-v0.16.0`. The `release/` prefix skips data's
lockfile automation, and `propose.py`'s dup-guard treats the branch as the release PR. It:

- sets the version in `pyproject.toml`;
- renames CHANGELOG `[Unreleased]` to `[0.16.0] - <date>`, leaving a fresh empty `## [Unreleased]`;
- bumps `AGENTS.md`'s **Version** and **Last Updated**;
- bumps the fallback literal in `juniper_data/__init__.py` (`"0.14.0"`; its comment says to bump it
  with the version).

**After the bump PR merges, warn the owner about CHANGELOG bullets.** An open data PR that adds
CHANGELOG bullets, such as #428 at 13:09Z, would merge them under `[0.16.0]` without a conflict.
- If it merges **before** the cut's step 1, it ships in 0.16.0, and that is where its bullet
  belongs.
- If it merges **after** the cut, its bullet belongs under the new `[Unreleased]`.

Those PRs belong to other sessions, so tell the owner rather than editing them. This is `reference_release_cut_under_an_open_pr_changelog_automerges_silently.md`.

**The cut** needs, in order: the bump PR merged; the owner's ruling on item 4; and, after step 4's
preview, the owner's approval in your session of both the cut and the archive PR's auto-merge
(goal, item 1). Work in the session scratchpad, not the worktree. Use one `<date>` throughout.

1. **Pin the source.** Run `gh api repos/pcalnon/juniper-data/commits/main --jq .sha` and keep
   the result as `<sha>`. Then run `gh api repos/pcalnon/juniper-data/tarball/<sha> > <scratch>/data.tgz`
   and extract it into `<scratch>/eco/juniper-data/` with `--strip-components=1`.
2. **Detect.** Run `python3 util/release_train/detect.py --package juniper-data --ecosystem-root <scratch>/eco --json > <scratch>/m.json`.
   Exit 1 is expected, with `BUMPED_NOT_RELEASED`. Omit `--local-git`, which needs a real clone.
   **Keep `--package juniper-data` on this and every later command.** Since juniper-ml#2033,
   juniper-ml itself is `BUMPED_NOT_RELEASED` (0.10.0 against PyPI's 0.9.0), and an unfiltered
   ceremony would cut its Release too.
3. **Dry run.** Run `python3 util/release_train/ceremony.py --manifest <scratch>/m.json --package juniper-data --ecosystem-root <scratch>/eco --cross-repo --release-date <date>`.
   Without `--cross-repo` it reports "skipped" and exits 0.
4. **Preview the Release body, then get the approval.** A Release cannot be re-cut. Run
   `python3 util/ad-hoc/2026-09-12_ceremony_notes_preview.py --package juniper-data --version 0.16.0 --release-date <date> --ecosystem-root <scratch>/eco`.
   Show the owner the output, and only now ask for the approval of the cut and the archive PR's
   auto-merge.
5. **Re-probe juniper-data's `commits/main`.** If it is no longer `<sha>`, start again from step 1,
   and get the approval again on the new preview. `gh release create` tags data's `main` as it is
   at cut time (`ceremony.py:836` passes no `--target`), but the notes come from your extract.
6. **Execute.** Add `--execute --monitor-timeout 540` to step 3's command, keeping its
   `--release-date`. Raise the Bash tool's timeout to 600000 ms, or run it in the background.
7. **Read the result.**
   - On a HALT it files an issue and stops.
   - Otherwise PyPI waits for the owner at the `pypi` gate.
   - Since juniper-data#426, a failed consumer notification turns the publish run red *after*
     PyPI has accepted the release. The `pypi` job, not the run, is the verdict. The ceremony's
     monitor stops at the `pypi` gate, so it never sees the `notify-consumers` job. Check both
     jobs yourself after the owner approves.
8. **Probe the published image.** This should print `True True`; 0.15.0 prints `False False`:
   `docker run --rm --entrypoint python ghcr.io/pcalnon/juniper-data:0.16.0 -c "import importlib.util as u; from juniper_data.generators.equities import generator as g; print(g.EQUITIES_DEPS_AVAILABLE, u.find_spec('yfinance') is not None)"`
9. **Move the deploy pin.** juniper-deploy's data pin then needs 0.16.0. It touches
   `CHANGELOG.md`, `docker-compose.yml` and `k8s/helm/juniper/values.yaml`. Another session made
   the last two pin moves (juniper-deploy#227, #229), so coordinate through the owner.

## Item 5 detail

- **cascor's version surface in the image is the response envelope.** Compare an enveloped
  response's `meta.version`, from `GET /v1/workers` for example, with
  `importlib.metadata.version("juniper-cascor")`. The published 0.11.0 reports `0.6.0` there.
  cascor#672 (merged 01:12Z) fixes it from the next release (`…PUBLISHING-PLAN.md` §5.2).
- **Fix `util/ad-hoc/2026-09-21_image_does_its_job_sweep.py` before reusing it.**
  - Its hard-coded tags are stale.
  - An absent `__version__` scores as a pass.
  - Its worker row skips the serve check, although the worker serves `/v1/health` on
    127.0.0.1:8210 inside the container.

## Known gaps no gate catches (re-verified 2026-09-22/23)

- **Build-arg values are published in public SLSA provenance.** `APP_VERSION`, `BUILD_DATE` and
  `GIT_SHA` appear in the 0.6.1 worker attestation. "Never pass a secret as `--build-arg`" is
  unenforced, and Wave 4 is about to add a credential to these workflows.
- **`juniper-cascor-worker/.env.example:9` ships `CASCOR_AUTHKEY=juniper`.**
- **The worker's `HEALTHCHECK` is `kill -0 1`** (`Dockerfile:119-120`). It proves only that PID 1
  has not died.
  - It affects the bare image.
  - It affects the Helm chart by default. `worker.healthcheck.enabled: false`
    (`k8s/helm/juniper/values.yaml:336-337`) falls back to the same `exec: kill -0 1` probe. The
    chart's own comment says worker images from 0.4.0 onward serve `/v1/health/*` on 8210, so
    the pinned 0.6.0 could already take the `httpGet` probe. 0.6.1 changed nothing here.
  - juniper-deploy's compose already replaces it with an HTTP `/v1/health/ready` probe.
- **Source-checkout fallback literals drift.** The worker's reads `"0.6.0"` at 0.6.1, and its own
  comment says to bump it. Data's reads `"0.14.0"` at 0.15.0; item 1 fixes that one. The release
  train never edits them. Installed artifacts read metadata and are correct.
- **cascor's published 0.11.0 reports `0.6.0`**, on a different surface in each artifact. The
  wheel's `__version__` is `"0.6.0"`. The image, which does not ship `juniper_cascor` at all,
  reports it as `meta.version` in every enveloped response; `/v1/health` is correct.
  cascor#668 is fixed on `main` by #672, so this lasts until cascor's next release. The class-2
  sweep scored it as a pass.
- **The stale-pin check (deploy#226) is advisory.** It runs only in juniper-deploy CI, with no
  schedule and no `--fail-on-stale`. At 13:09Z every pin matched its image's newest release, since
  deploy#229 (merged 06:23Z) repinned the worker to 0.6.1. The next drift is the data pin, at
  0.16.0.
- **The release train does not count image-only or packaging-config changes as ship changes.** It
  only flags a non-empty `[Unreleased]` for review.
- **worker#194's lock refresh (`bca33c99`) was not functionally tested.**
  - It moved filelock 3.32.6 → **4.0.1**, and also fsspec and networkx, in the CPU image. The
    smoke test imports none of them.
  - An import check on the published 0.6.1 amd64 image passed. It covered `filelock`, `fsspec`,
    `networkx`, `torch.utils._filelock` and `juniper_cascor_worker.worker`.
  - Neither the Release body nor the archived notes mention the change. Both say "None known".

**Stale Latest badges (item 4), probed 02:00Z:**

| repo | Latest badge | newest release |
| --- | --- | --- |
| data | `v0.13.0` | v0.15.0 |
| cascor | `v0.10.0` | v0.11.0 |
| canopy | `v0.5.0` | v0.8.1 |
| recurrence | `juniper-recurrence-model-v0.1.4` | app v0.5.0 |

The worker's badge is correct.

**The Pi pull** (`…PUBLISHING-PLAN.md` §5.1):

- It is owed before any Pi runs a Juniper image.
- It is an anonymous **GHCR** pull. Its target is the newest worker release, now 0.6.1, and it
  needs a 64-bit Pi OS.
- `turing` was reported down on 09-22.
- **After Wave 4**, pulls from **docker.io** follow `…REGISTRATION-PROCEDURE.md` §9. The nodes log
  in with their own read-only token, and nodes that share one account share its 200 pulls per
  6 h. None of that applies to the GHCR pull.

**Mechanisms worth keeping** (detail in `…PUBLISHING-PLAN.md` §5.2 and `…still-reports-0-4-0.md`):

- only committed files reach a CI-published image;
- a bare `.dockerignore` pattern matches the context root only;
- the check unit is the context root;
- a `/app`-only scan passes vacuously;
- never blanket-add `**/logs/`, because canopy's is a symlink.

**Owner ruling, 2026-09-21:** do not retire live memories to meet the 20 KB MEMORY.md target.

## Checkpoint — what this session changed

| repo | PR | merged | what |
| --- | --- | --- | --- |
| juniper-data | #420 | 19:05Z `6c81cc4c` | the wheel excludes `juniper_data.tests`, and `ci.yml` asserts it. The automation added `c2a50d89` (multidict 6.9.1, sentry-sdk 2.70.0) |
| juniper-cascor-worker | #193 | 18:59Z `48a523e6` | 8 stale `juniper-ci-tools` ranges; `[Unreleased]` gains #191/#192 |
| juniper-ml | #2009 | 19:20Z `c4a67481` | `…REGISTRATION-PROCEDURE.md` §3 ruled Option B and its cost corrected; `…PUBLISHING-PLAN.md` OQ-1 amended; new `util/ad-hoc/2026-09-22_wheel_test_members.py` |
| juniper-ml | #2011 | 19:58Z `099a5645` | the five `dockerhub` environments recorded |
| juniper-ml | #2019 | 20:53Z `5ea8e273` | the stale-pin check exists; the data-image equities finding; `…still-reports-0-4-0.md`'s banner |
| juniper-cascor-worker | #194 | 22:56Z `38f39cb8` | the v0.6.1 proposal, plus the automation's `bca33c99` lock refresh |
| juniper-ml | #2022 | 23:11Z `f1c2c23a` | `notes/releases/RELEASE_NOTES_juniper-cascor-worker_v0.6.1.md` (the ceremony) |
| juniper-ml | #2025 | 23:40Z `a7568f78` | `…PUBLISHING-PLAN.md` §5.2 and `…still-reports-0-4-0.md`'s banner: v0.6.1 shipped |
| juniper-data | #421 | 00:56Z `68c3cd7c` | the image lock gains `--extra equities`; the owner approved the merge |
| juniper-ml | the PR archiving this file | — | this handoff; `…still-reports-0-4-0.md` marked SUPERSEDED; `…PUBLISHING-PLAN.md` (status, §3 D-1, §5, §5.1, §5.2, §6 OQ-1); `…REGISTRATION-PROCEDURE.md` (header, §1–§11) |

**GitHub settings**: five `dockerhub` environments; Release `v0.6.1` marked Latest.
**Outside git (harness memory)**:

- `project_container_registry_rollout_2026-09-08.md`
- `project_publish_path_authorization_2026-08-17.md`
- `reference_release_cut_under_an_open_pr_changelog_automerges_silently.md`
- `reference_worktree_isolated_session_command_refusals.md`
- `reference_release_train_ceremony_traps_2026-09-09.md`
- `reference_docker_logout_registry_name_leaves_credentials.md` (new)

## Git state

- This session's worktree is `juniper-ml/.claude/worktrees/async-hatching-scroll`, on branch
  `worktree-async-hatching-scroll`, based on `ab434c9b`, which was `origin/main` at 01:44Z.
- The only changes are this file and the three documents in the last Checkpoint row. They sit in
  unsigned local scratch commits that exist only to run the screens, and ship as one PR through the
  API.
- No local branch was ever pushed. Every remote commit is GitHub-signed through the API.
- The session created no sibling worktrees.

## Validation record

Every finding below was re-probed by the writing session before it was folded in.

**Round 1: four independent lanes on the frozen v1 draft. All returned FAIL.**

| lane | lens | verdict |
| --- | --- | --- |
| A1 | re-probe every fact against GitHub, PyPI and GHCR | FAIL: 1 major, 8 minor |
| A2 | run every command and procedure step | FAIL: 2 major, 7 minor |
| B1 | residue loss and over-claim against `…still-reports-0-4-0.md`, `…PUBLISHING-PLAN.md` and `…REGISTRATION-PROCEDURE.md` | FAIL: 4 major, 12 minor |
| B2 | cold read, as a fresh session and as the owner | FAIL: 2 critical, 9 major, 9 minor |

Round 1 found that `docker logout docker.io` leaves the token stored. It was reproduced on docker
29.7.2. It also found that the merge-approval rule covered only #421, that five items of
`…still-reports-0-4-0.md` had been dropped, and that the token could have been handed to an agent.

**Round 2: three lanes on v2. All returned FAIL.**

| lane | lens | verdict |
| --- | --- | --- |
| 1 | re-probe v2's facts | FAIL: 2 major, 8 minor |
| 2 | cold read for actionability | FAIL: 1 critical, 7 major, grouped minor |
| 3 | consistency across all four documents | FAIL: 5 major, 10 minor |

What round 2 caught, and v3 fixed:

- **The critical finding.** `ceremony.py --execute` opens a juniper-ml archive PR and arms
  auto-merge on it, so approval must name that PR too.
- **The recommended username variable broke every later check.** The checks and the Wave 4
  context are now path-aware in this handoff, `…REGISTRATION-PROCEDURE.md` and
  `…PUBLISHING-PLAN.md`.
- **The owner's normal Docker config holds a Docker Hub web login.** The token test now runs in a
  throwaway config, and runs before registration.
- **`…REGISTRATION-PROCEDURE.md` contradicted itself.** It sent a mis-scoped entry to a
  destructive rollback block, and it alternated its ten prompts against its own warning. It would
  also have produced a second Read & Write token for the Pi nodes.
- **Stale by the time v2 was written.** deploy#227 and #228 had merged, and cascor#672 with them.
- **Docker's documentation.** Its pulls page confirms the per-arch count. Its usage page's table
  gives the per-account allowance.
- **Smaller fixes.**
  - The class-2 sweep's vacuous cascor probe.
  - The `__init__.py` fallback was missing from the bump.
  - `ml#1151` was misread.

**Round 3: three lanes on v3, frozen as commit `6d3987ba`.**

| lane | lens | verdict |
| --- | --- | --- |
| 1 | closure of every round-2 finding | FAIL: 1 major, 13 minor; every other round-2 critical and major resolved |
| 2 | live facts and cross-document consistency | FAIL: 1 major, 16 minor; 5 stale-since |
| 3 | cold read as the next session, and a literal walk as the owner | FAIL: 2 major, 22 minor |

What round 3 caught, and v4 fixes:

- **The token test was unsafe to retry.** Lanes 1 and 3 both found it. Its last line removed the
  throwaway config, so re-running the login line alone wrote the token into the owner's real
  config, over the web login. Each docker line now names the throwaway directory through
  `${d:?}`, which refuses to run when it is unset. A fake-credential run confirmed that a stray
  line cannot reach the real config.
- **Approval for the ceremony's archive PR** was stated only as a rule. It is now the
  precondition of the `--execute` step. v4 also added a cut-only fallback; round 4 found it
  unsafe, and v5 removed it.
- **The owner was never asked to report what Wave 4 waits for.**
  `…REGISTRATION-PROCEDURE.md`'s header now asks for all four things.
- **The cut recipe.**
  - The source is pinned by SHA.
  - The Release body is previewed.
  - The scripts run with `python3`.
  - The publish is judged by the `pypi` job, per juniper-data#426.
- **The release train.** It only reports, so data#422 and #428 change nothing about item 1. An
  unfiltered ceremony would also cut juniper-ml's own Release, which has been
  `BUMPED_NOT_RELEASED` since juniper-ml#2033.
- **cascor's version defect was misattributed.** Lane 2 found that the cascor image ships no
  `juniper_cascor` package. Its stale surface is the envelope's `meta.version`, which cascor#672
  also fixed. The fix to the sweep, and item 5's check, now target that surface.
- **The agent could have printed an exposed token** while checking the username variable. It now
  checks the value as a boolean.
- **A credential helper defeats a throwaway config.** `…REGISTRATION-PROCEDURE.md` §4 now checks
  for one first.
- **Smaller fixes.**
  - The clipboard rationale.
  - Exposure comes first in `…REGISTRATION-PROCEDURE.md` §8.
  - `…REGISTRATION-PROCEDURE.md` §11 no longer handles the token again.
  - Repo-scope variable values are printed for the owner.
  - Docker's abuse limit is given with its documented size.
  - The default-privacy setting is located.

**Round 4: two lanes on v4, frozen as commit `90c5180d`.**

| lane | lens | verdict |
| --- | --- | --- |
| A | closure of every round-3 finding, and regressions in v4's diff | FAIL: 1 major, 9 minor, 12 nits; 44 of 49 round-3 findings resolved |
| B | fresh cold read, owner walk, and a re-probe of every new fact | FAIL: 1 critical, 13 minor; every new fact held |

What round 4 caught, and the final version fixes:

- **The cut-only fallback** was both lanes' top finding. v4 let a session run `--execute` with
  only the cut approved and disarm the archive PR "as soon as the PR URL prints". The ceremony
  prints that URL only when it finishes, and juniper-ml#2022 merged 8m21s after arming. The
  fallback is gone: `--execute` needs both approvals.
- **The token test's guard caught only an unset variable.** A leftover `d` from any earlier command
  could have been `rm -rf`'d. The block in `…REGISTRATION-PROCEDURE.md` §4 step 5 now uses a
  distinctive name, a named `mktemp` template, and an `rm` that checks the path.
- **The owner could revoke a good token over a typo.** `…REGISTRATION-PROCEDURE.md` §6 now calls
  it exposure only when the value begins `dckr_pat_`.
- **The recipe's order.** The owner now approves the cut after the preview, and again after a
  restart. Item 4's ruling is a precondition. The session warns the owner about the CHANGELOG
  bullets of open data PRs.
- **Smaller fixes.**
  - The agent's Wave 4 checks carry names-only filters and a tag-rule check.
  - The first verify command names this PR's branch.
  - Section references in the goal now name their document.
  - In `…REGISTRATION-PROCEDURE.md`:
    - The clipboard is cleared after the last token paste.
    - "Paste only after `Password:`".
    - The token's scope is checked on Docker's list.

**Round 5: one reconciliation lane on v5, frozen as commit `fc88fd0c`: PASS.** No critical or
major finding was open. It re-ran the token test verbatim in four cases, including a real failed
login and a stale variable value. The fake web login survived all four. The final version also
fixes round 5's minor findings:

- A local `propose.py` run proposes only with `--execute`.
- juniper-data#427 is an issue, so it is the fix PR that must merge.
- The CHANGELOG warning covers only PRs that merge after the cut.
- `…REGISTRATION-PROCEDURE.md` §4 now says how to clean up when the shell is lost before line 4.
- Its §6 and §8 treat a `dckr_pat_` value in a variable of any name as exposure.

Before this PR opened, the documents were refreshed to 13:09Z. juniper-deploy#229, juniper-data#422
and juniper-ml#2036 had merged between 06:21Z and 06:23Z.

**Not fixed:**

- The goal is about 1,590 words, over the ~1,200 target. Two sections moved below the line
  (*Data release recipe*, *Item 5 detail*); the rest is safety text that a pointer would weaken.
- When an environment is missing, `…REGISTRATION-PROCEDURE.md` §6 prints GitHub's 404 JSON before
  its marker. That is cosmetic, and every environment exists.
- `…REGISTRATION-PROCEDURE.md` §6 and §11 print a variable's value. Both are for the owner's own
  terminal, never a Claude session.
- Some role references in this record, such as "the token test", name no file.
