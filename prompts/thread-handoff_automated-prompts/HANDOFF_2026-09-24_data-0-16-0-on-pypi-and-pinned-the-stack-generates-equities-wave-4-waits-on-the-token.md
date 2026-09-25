# HANDOFF 2026-09-24 — data 0.16.0 is on PyPI and pinned, the stack generates equities, and Wave 4 waits on the token

**Session**: container-registry rollout, session `containers [2703c8]`. It worked every startable
item of the predecessor named below, plus the gaps it found on the way (see *What this session
did*).
**This file**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`.
Read it from `main`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-cut-at-one-commit-item-5-closed-in-five-repos-wave-4-waits-on-the-token.md`
(`…cut-at-one-commit-….md` below), **SUPERSEDED** by this file. It is history only; do not act on
its items. Its live items are carried below, not by reference.
**Times are UTC.** Live state was last probed at 2026-09-25 01:40Z. **Updated without a validation round, at the
owner's request** (the arc was paused for this handoff); round 4 was not run.

## Handoff goal — paste from the next line down to the line `— END OF GOAL —`

Continue the **container-registry rollout**. These documents govern it, and every section reference
below names its document:

- `…PUBLISHING-PLAN.md` is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`, the design of record.
- `…REGISTRATION-PROCEDURE.md` is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`, Wave 4's credential steps.
- `…PYPI-PUBLISH-PROCEDURE.md` is `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`, the release ceremony. Its §11.7 covers the Latest badge and `--target-sha`.

**Ecosystem root**: `/home/pcalnon/Development/python/Juniper/`. Paths beginning `notes/`,
`prompts/`, `util/` or `tests/` are inside `juniper-ml/` unless a repo is named.

### Rules that bind you

- **Every merge YOU perform needs the owner's explicit approval, naming that PR or group, in YOUR
  session.** An earlier session's approval does not carry over. `gh pr merge --auto` on a MERGEABLE
  PR merges it on the spot, and an `update-branch` on an armed PR completes its merge.
- **Merge with** `python3 util/safe_merge.py --repo <repo> --pr <n> --merge-method squash --execute`,
  and read its `MERGED` line, never its exit status: it exits 0 when it refuses. Under a `strict`
  ruleset, and only once the merge is approved, a `BEHIND` PR needs
  `gh api -X PUT repos/pcalnon/<repo>/pulls/<n>/update-branch`, one PR at a time.
- **The PR sweeper is the owner's.** It readies and arms open PRs as `pcalnon`, and the ruling was
  "Mine: fix forward". **Do not draft or disarm a PR to hold it.** To validate before a merge,
  validate before the PR exists:
  1. Create the branch with `gh api -X POST repos/pcalnon/<repo>/git/refs -f ref=refs/heads/<branch> -f sha=<main sha>`.
  2. Commit with `python3 util/push_signed_commit.py --repo <repo> --branch <branch> --expected-head <main sha> …`.
  3. Validate the pushed branch.
  4. Only then run `gh pr create --repo pcalnon/<repo> --head <branch> --base main`.
- **Commit only through the GitHub API** (`util/open_signed_pr.py`, `util/push_signed_commit.py`).
  Never `git push`, never sign locally, never `PUT /contents` (it makes an unsigned commit). Before
  every upload, re-probe the target's `commits/main` and diff each file: the helpers send whole files.
- **Before opening a fix PR, search open and just-merged PRs for the same fix.** After ANY head move
  on your PR, whoever made it, re-read its diff content against what you intended:
  `gh pr diff <n> --repo pcalnon/<repo>`.
  - On juniper-data#439, a merge commit resolved a real conflict in the PR's favour. It turned
    `CHANGELOG.md +26 −23` into `+0 −71`, which would have deleted 71 of `main`'s lines, with every
    check green.
  - Per-file counts (`gh api --paginate …/pulls/<n>/files`) are only a screen. A same-lines conflict
    resolved that way keeps the counts and still reverts `main`.
  - If `main` already carries your fix, close your PR.
- **Never handle a token.** Run no `gh secret set` or `gh variable set` for Docker Hub or
  `CROSS_REPO_DISPATCH_TOKEN`. If a token appears in chat, do not repeat or use it. Tell the owner
  it is exposed and must be deleted at its issuer first; for Docker Hub that is
  `…REGISTRATION-PROCEDURE.md` §8.
- **Never approve a `pypi` environment gate.** Run `util/release_train/ceremony.py --execute` only
  after the owner approves, in your session, both the cut and the auto-merge of the archive PR it
  opens. The tool arms that merge before it cuts.
- **If a later ruling from another session rests on a premise your session is changing, ask the
  owner. Do not pick one.** This happened with 0.16.0's notes (`…PUBLISHING-PLAN.md` §5.2).
- Re-probe every claim, this file's included. Scripts go in `util/ad-hoc/`, never `/tmp`.
- **The memory index is full.**
  `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md` sits
  near its ~25,000-**character** load limit (`wc -m`, not `wc -c`), and later lines silently drop.
  **Add no index line;** link a new memory from an indexed one with `[[name]]`. No live memory is
  retired to make room (owner, 2026-09-21).

### Owner gates — tell the owner; you run none of them

1. **Wave 4's credential.** The owner runs `…REGISTRATION-PROCEDURE.md` §2, §5.2B step 3a, §4, §5.2B
   step 3 and §6, in that order. The document's header lists the steps, and those sections hold the
   commands. The owner then tells you four things:
   - that the `…REGISTRATION-PROCEDURE.md` §4 login succeeded;
   - which form `…REGISTRATION-PROCEDURE.md` §5.2B step 3a used;
   - the Docker ID;
   - the token's expiry date.
2. **`CROSS_REPO_DISPATCH_TOKEN` cannot dispatch to juniper-recurrence.** 0.16.0's
   `Notify consumer repos` job got `403 Resource not accessible by personal access token`, and
   every data release fails the same way until the owner fixes the token.
   - A replay needs the owner's approval each time. It is one
     `gh api -X POST repos/pcalnon/juniper-recurrence/dispatches --input <file>`, with
     `{"event_type":"juniper-data-published","client_payload":{"source":"juniper-data","version":"<X.Y.Z>","sha":"<tag sha>"}}`.
   - Then confirm that a `juniper-data-published` run started (`…PUBLISHING-PLAN.md` §5.2).
3. **Still open**:
   - OQ-2, OQ-3 and OQ-4 (`…PUBLISHING-PLAN.md` §6);
   - the Pi pull (`…PUBLISHING-PLAN.md` §5.1);
   - whether `juniper-deploy-test` goes to Docker Hub (`…REGISTRATION-PROCEDURE.md` §10);
   - not yet put to the owner: should juniper-data answer a fetch failure with `502`/`503` instead
     of `400 Invalid request parameters` (`…PUBLISHING-PLAN.md` §5.2)?

### Remaining — yours once its condition holds

1. **When the owner reports the four Wave 4 facts**: record the token's expiry in
   `…REGISTRATION-PROCEDURE.md` §10, by PR.
2. **The Wave 4 workflow change, only when BOTH hold.**
   - **(a) The credential checks out.** Run plain `gh api` calls on each of the five repositories
     (`…REGISTRATION-PROCEDURE.md` §5.1: juniper-cascor, juniper-cascor-worker, juniper-canopy,
     juniper-data, juniper-recurrence).
     - **Names only.** Every listing call carries `--jq '[.secrets[].name]'` or
       `--jq '[.variables[].name]'`, because a bare GET of a variables endpoint prints values.
     - `environments/dockerhub/secrets` lists `DOCKERHUB_TOKEN`, plus `DOCKERHUB_USERNAME` if the
       owner chose a secret, and nothing else.
     - `environments/dockerhub/variables` lists `DOCKERHUB_USERNAME` if the owner chose a variable,
       and nothing else.
     - `actions/secrets` and `actions/variables` list no `DOCKERHUB_*`.
     - `environments/dockerhub/deployment-branch-policies`, with
       `--jq '[.branch_policies[] | .type + ":" + .name]'`, still shows `tag:juniper-*-v*` and
       `tag:v*`.
     - **A variable's value is checked only as a boolean:**
       `--jq '.variables[] | select(.name=="DOCKERHUB_USERNAME") | (.value=="<Docker ID>")'`. Never
       print it. `false` means only a mismatch; the owner looks with `…REGISTRATION-PROCEDURE.md` §6.
   - **(b)** The owner has told you, in your session, that the `…REGISTRATION-PROCEDURE.md` §4 login
     succeeded.
   - **Then:**
     - **Never name `dockerhub` unconditionally on the existing `build` or `merge` job.** A tags-only
       environment rejects their PR and dispatch runs.
     - Pick a shape from `…REGISTRATION-PROCEDURE.md` §3 and §7, and read the username from the
       context the owner chose (`vars.` or `secrets.`).
     - Give each new job its release-tag guard as a job-level `if:`: `'v'`, or
       `'juniper-recurrence-v'` in recurrence.
     - **Never pass the credential as a `--build-arg`.** Build-arg values are published in public
       SLSA provenance.
     - Ask the owner before editing the five `publish-image.yml` files.
3. **Known gaps**, below the goal, each with a *fix* or *track* verdict. None is time-bound.
4. **Finish this arc's records (no condition).** The archiving PR, from juniper-ml branch
   `docs/handoff-data-0-16-0-egress-guards-fail-closed`, is open and **unmerged**. Before it merges,
   add these to that branch with `util/push_signed_commit.py --expected-head <sha>`:
   - `…PUBLISHING-PLAN.md`: its status block (about L31-32) and about L725-726 still say the guards
     "evaluate the union". Rewrite both as the static fail-closed model in *Key context*, and record
     juniper-deploy#236.
   - Optionally, one scope-bounded reconciliation lane that judges #236 against its stated scope.

   Merging it needs the owner's approval naming it, in your session. Also append #236 to memory
   `project_container_registry_rollout_2026-09-08.md`; that is outside the repository.

### Key context

- **juniper-data 0.16.0 is complete**: on PyPI since 18:35:40Z, on GHCR, and pinned by
  juniper-deploy#230. The replayed notification's bench passed against it (run 36046705575), though
  recurrence still caps `<0.16.0`.
- **X8 (juniper-data#437) is NOT in 0.16.0.** It ships in the next data release. The parent
  `Juniper/AGENTS.md` Data Contract was corrected with the owner's approval; it is unversioned and
  has no PR.
- **The stack generates equities, mnist and arc_agi now**; each answered `201` in the stack. The
  owner ruled for a dedicated egress network.
  - juniper-deploy#231 adds compose `data-egress`.
  - juniper-deploy#232 adds the Helm TCP 443 rule, verified as rendered only.
  - juniper-deploy#233–#236 fix forward what validation refuted. The data pod mounts no
    service-account token. The guards are a **static model** of the rendered chart and
    `docker-compose.yml`, and they **fail closed**. A construct they do not model fails a test
    instead of passing: a List, `hostNetwork`, another policy kind, a compose `include`, or an
    external network alias. Mutation checks at deploy `main` `b2f8a428`: compose 25/25, Helm 34/34.
- **Read *Traps* below the goal before running commands.**

— END OF GOAL —

---

## Traps

- **A worktree-isolated shell refuses compound commands that also run `git` or `gh`** when it cannot
  prove where they point. Refused this session:
  - `for` loops over `gh`;
  - `$(cat …)` inside a `gh` argument;
  - `gh … --jq` combined with another command through `&&`/`;`;
  - `docker run --entrypoint sh -c`;
  - a `python3 - <<EOF` heredoc chained with `&&`.

  A refused command also drops its heredoc, so the file it would have written does not exist. Use
  plain single commands, `--body-file`, `--entrypoint python`, and the Write tool for files.
- **Sequence Safety fails a renamed or removed function** in its scope (`tests/**/*.py`,
  `scripts/**/*.bash` in juniper-deploy).
  - Waive it with `Allow-Symbol-Loss: func:<name> func:<name>` in the **last trailer paragraph** of
    a commit in the PR: space-separated symbols, never prose.
  - Check the paragraph with `git interpret-trailers --parse < body.txt`.
  - deploy squashes with `COMMIT_MESSAGES`, so the trailer reaches `main` (juniper-deploy#233,
    #234).
- **`docker compose down` skips profile-only services** (juniper-data is one) unless `--profile` is
  given; `down -v` then removes nothing and prints nothing. Count leftovers afterwards. **Always
  pass a unique `-p <project>`**: the owner's `juniper-deploy_*` volumes exist on this host, and the
  default project name would make `down -v` remove them.
- **Verify the published artifact, not the merge.** Pull an image before measuring it, because
  `2>&1 | wc -l` counts pull progress. `find … | wc -l` cannot tell an absent path from an
  unreadable one.
- **A render test can pass vacuously.** The chart's fullname helper collapses a release name that
  contains `juniper`, so select policies by label. A "none rendered" test must first prove its
  selector finds something.

## Verification commands

```bash
# 0.16.0: PyPI, the run, the 403, the replayed bench
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-data/0.16.0/json    # 200
gh run view 35977786108 --repo pcalnon/juniper-data --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'   # PyPI success; notify failure
gh api repos/pcalnon/juniper-data/actions/jobs/107777269559/logs | grep -n 'Resource not accessible'  # the 403
gh run view 36046705575 --repo pcalnon/juniper-recurrence --json conclusion --jq .conclusion  # success

# The deploy pins, the egress network, the Helm rule and the token (deploy main 8ec98277 or later)
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" | grep -n 'juniper-data:0\|data-egress'
gh api repos/pcalnon/juniper-deploy/contents/k8s/helm/juniper/templates/networkpolicy-data.yaml -H "Accept: application/vnd.github.raw" | grep -n 'port: 443\|0.0.0.0/0'
gh api repos/pcalnon/juniper-deploy/contents/k8s/helm/juniper/templates/data-deployment.yaml -H "Accept: application/vnd.github.raw" | grep -n 'automountServiceAccountToken'

# X8 is not in the tag, and main's [0.16.0] equals the tag's
gh api repos/pcalnon/juniper-data/compare/v0.16.0...1afc3484 --jq .status                   # ahead
python3 util/ad-hoc/2026-09-24_changelog_section_identity.py section --repo pcalnon/juniper-data --section 0.16.0 --ref v0.16.0 --against main   # IDENTICAL

# Wave 4 is still empty (names only)
gh api repos/pcalnon/juniper-data/environments/dockerhub/secrets --jq '[.secrets[].name]'      # []
```

## What this session did

| PR / item | merged | what |
| --- | --- | --- |
| juniper-deploy#230 | 18:58:50Z `b972ae8c` | the data pin `0.15.0` → `0.16.0`: compose `:164` and `:517` (`:523` since #231), helm `values.yaml:40` |
| juniper-data#439 | **closed unmerged** 19:03:54Z | moved X8 to `[Unreleased]`, which #438 had just done; a conflict resolved in its favour made its head destructive. A correction comment records the mechanism |
| juniper-cascor-worker#198 | 19:07:04Z `419bac36` | `.env.example` no longer ships `CASCOR_AUTHKEY=juniper` |
| juniper-deploy#231 | 19:26:18Z `2bde07b2` | compose `data-egress` |
| juniper-deploy#232 | 19:56:16Z `7ff6ff32` | the Helm TCP 443 rule |
| juniper-deploy#233 | 23:43:02Z `713e8a93` | fix-forward: the data pod's `automountServiceAccountToken: false`, and the guards moved toward the effect (15/15 Helm and 12/12 compose mutants). Rounds 2 and 3 showed they still passed defects, fixed in #235 and #236 |
| juniper-cascor-worker#199 | 23:48:00Z `a21e8dce` | #198's CHANGELOG key claim holds for a fresh network only |
| juniper-deploy#234 | 23:51:02Z `0408534d` | compose booleans must be literal, and juniper-data's network set is exact (14/14) |
| juniper-cascor-worker#200 | 09-25 00:40:08Z `b5780754` | #199's sentence was itself wrong; the entry defers cascor's key handling to #691 |
| juniper-deploy#235 | 09-25 00:43:57Z `8ec98277` | the guards evaluate the UNION of every policy selecting a pod (26/26), and pin `data-egress`'s whole definition (21/21). Body corrected 09-25 01:33Z: it named round 2 as "a third" |
| juniper-deploy#236 | 09-25 01:31:51Z `b2f8a428` | the guards fail closed. **Helm:** policyTypes defaulting, namespace-aware selection (`matchExpressions` refused), `hostNetwork` and Lists refused, no other policy kinds, projected tokens, and a policies-off check that covers every policy type (#235 had weakened it). **Compose:** no `include`, no external alias, no `dns` / `extra_hosts` on juniper-data. 25/25 compose and 34/34 Helm mutants; the four files on `main` are byte-identical to the intended tree |
| juniper-cascor#691 | issue, open; edited | snapshots persist the manager authkey twice and restore it, and pre-2026-03-18 ones carry the former public default. **Latent**: no manager has been started since `aa46ad55` (2026-03-17) |
| the PR archiving this file | — | the files listed below |

**Files in the archiving PR**:

- this file;
- `…cut-at-one-commit-….md`, marked SUPERSEDED;
- `…PUBLISHING-PLAN.md`: the status block and §5.2;
- seven new scripts in `util/ad-hoc/`:
  - `2026-09-24_changelog_section_identity.py`;
  - `2026-09-24_data_egress_mutation_check.py`;
  - `2026-09-24_helm_data_egress_mutation_check.py`;
  - `2026-09-24_laneB_helm_test_mutations.py`;
  - `2026-09-24_laneB_compose_test_mutations.py`;
  - `2026-09-24_laneB_helm_selector_match.py`;
  - `2026-09-24_laneB_section_identity_check.py`.

**Outside git**:

- **The parent `Juniper/AGENTS.md` Data Contract**, edited twice with the owner's approval:
  - X8 is not in 0.16.0;
  - `arc_agi` is at `4.0.0` from 0.16.0;
  - the guard's allow-list names `arc_agi`;
  - 0.16.0 is on PyPI.
- **One replayed `repository_dispatch`**, to juniper-recurrence.
- **One remote branch deleted**: juniper-data `docs/changelog-x8-to-unreleased`. `322135bd` stays
  reachable through #439.
- **Harness memory:**
  - new: `reference_a_conflict_resolved_for_your_pr_can_drop_mains_lines.md`. It is not indexed,
    because of the load limit; `reference_changelog_conflict_signed_update_branch.md` links it.
  - deleted: `reference_update_branch_merge_can_drop_mains_changelog_lines.md`. It had the
    mechanism wrong.
  - appended: `project_container_registry_rollout_2026-09-08.md` (twice) and
    `reference_changelog_conflict_signed_update_branch.md`;
  - edited: `MEMORY.md`, whose net change is nil.
- **Comments**: a correction on juniper-data#439, and one on juniper-cascor#691 recording its edit.

## Known gaps (verdict per gap)

- **Fix, when someone next edits the worker image.** Its `HEALTHCHECK` is `kill -0 1`
  (juniper-cascor-worker `Dockerfile:119-120`). The chart falls back to the same probe (juniper-deploy
  `k8s/helm/juniper/values.yaml:336-337`). Compose already overrides it with `/v1/health/ready`.
- **Track; latent.** juniper-cascor#691 covers cascor's side of #198:
  - snapshots store the manager key twice and restore it;
  - pre-2026-03-18 ones carry the former public default;
  - post-fix keys do not round-trip.

  No manager has been started since `aa46ad55`, so nothing reads the key today.
- **Track; stated in juniper-deploy's `docs/REFERENCE.md`.** The compose egress is unrestricted: any
  port, any destination. On Docker older than 28 with a FORWARD policy of ACCEPT, a LAN host that
  routes `172.27.0.0/16` via the Docker host can reach juniper-data. Both Docker protections assume
  Docker manages iptables.
- **Track.** The egress guards (juniper-deploy#236) are **static**. They judge the rendered chart and
  `docker-compose.yml`, never a live CNI or Docker daemon. They fail closed on what they do not
  model, which is why they refuse `hostNetwork` rather than model it.
- **Track.** The Helm rule is verified as rendered, not as enforced by a CNI.
  - It is IPv4 only, and a dual-stack pod's SEC fetch can wait out a 30 s timeout.
  - The accepted limits of `tests/test_helm_networkpolicy_data_egress.py`: the peerless DNS rule
    leaves ports 53 open to any address, the Redis subchart's own policy allows its pods all egress,
    and only the default values are rendered.
- **Track; it ends at cascor's next release.** The published cascor 0.11.0 reports `0.6.0`, and the
  published 0.11.0 image fails item 5's check for good. juniper-cascor#672 fixes both from the
  next release.
- **Track; cosmetic.** juniper-cascor's `CHANGELOG.md` repeats category headings. `ceremony.py`'s
  `changelog_version_section` merges repeated categories; only a repeated **version** heading is
  harmful.
- **Track.** The worker's source-checkout fallback literal reads `"0.6.0"` at 0.6.1
  (`juniper_cascor_worker/__init__.py:35`).
- **Track.** The stale-pin check (juniper-deploy#226) is advisory: no schedule, no
  `--fail-on-stale`.
- **Track.** The release train does not count image-only or packaging changes as ship changes
  (`…PUBLISHING-PLAN.md` §5.2).
- **Track.** worker#194's lock refresh was never functionally tested.
- **Track; binds Wave 4.** Build-arg values are published in public SLSA provenance.
- **Track; a local gate only.** The `dockerhub` drift gate's live half skips in CI. Run it with
  `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_publish_env_policy_drift.py`.
- **Track.** juniper-deploy's network tables omit `juniper-data` from the `backend` row, though
  compose attaches it there. They are `docs/REFERENCE.md` § Docker Networks and § Network
  Isolation, and `docs/DEVELOPER_CHEATSHEET.md`.
- **Track.** juniper-recurrence caps `juniper-data<0.16.0`
  (`juniper-recurrence/juniper-recurrence/pyproject.toml:97` and `:106`). The replayed bench is the
  evidence that raising the cap is safe.

**The Pi pull** (`…PUBLISHING-PLAN.md` §5.1) is still owed before any Pi runs a Juniper image. It is
an anonymous GHCR pull of worker 0.6.1, and it needs a 64-bit Pi OS. `turing` was reported down on
09-22. After Wave 4, pulls from docker.io follow `…REGISTRATION-PROCEDURE.md` §9: the nodes log in
with their own read-only token, and nodes that share an account share its 200 pulls per 6 h. None
of that applies to the GHCR pull.

**Mechanisms worth keeping** (detail in `…PUBLISHING-PLAN.md` §5.2 and harness memory
`reference_juniper_deploy_image_publish_traps.md`):

- only committed files reach a CI-published image;
- a bare `.dockerignore` pattern matches the context root only;
- the check unit is the context root;
- a `/app`-only scan passes vacuously;
- never blanket-add `**/logs/`, because canopy's is a symlink.

## Validation record

**Round 1: three independent read-only lanes on the frozen v1 draft (frozen about 20:00Z).**

| lane | lens | verdict |
| --- | --- | --- |
| A | re-probe every fact against GitHub, PyPI and GHCR, and run every verification command | PASS: 0 critical, 0 major, 6 minor |
| B | adversarial: grant the premises, attack the conclusions of #230–#232, #198 and #439 | FAIL: 4 major, 8 minor |
| C | residue loss against `…cut-at-one-commit-….md`, item by item, plus a cold read | FAIL: 2 major (plus 2 rubric-major residue drops), 11 minor |

**Lane B's four majors were each re-derived before acting, and all four held.**

- **M1.** The Helm rule "cannot reach cluster-internal services" is false where the API server or
  the pod/service ranges are public, and the data pod carried a service-account token. The owner
  ruled: correct the claim and set `automountServiceAccountToken: false` (juniper-deploy#233).
- **M2.** #232's tests pinned the rule's wording, and eight broader rules passed them. They now pin
  the effect: 15/15 mutants caught, including all eight (#233).
- **M3.** #198's "a random key per run" is true only for a fresh cascor network, because snapshots
  restore their saved key. Pre-March snapshots carry the old public default. Filed as
  juniper-cascor#691 on the owner's approval; the worker CHANGELOG is corrected (worker#199).
- **M4.** #439's "no conflict raised" was wrong. `git merge-tree` conflicts, so `322135bd` resolved
  a conflict in the PR's favour. A correction comment is on #439, and the memory is rewritten.

**Lane B's minors** were fixed in #233 and #234 or recorded as known gaps. Among them: the compose
egress is unrestricted, and "no way in" fails on Docker < 28. It also found that mnist and arc_agi
failed the same way (confirmed: `500` after about 23 s). Its compose probe then still passed two
cases against #233, and #234 closed both.

**Lane C's majors**: the "conflicting rulings → ask the owner" rule, the safe_merge mechanics, the
Pi pull's `…REGISTRATION-PROCEDURE.md` §9 note and the predecessor's cleanup were restored, and the
re-validation rule now names its command.

**Lane A's and lane C's minors** were all applied:

- bare section references now name their document;
- the predecessor's shorthand no longer collides with this file's name;
- each changed file is named;
- the 403 has a verification command;
- the gaps carry locations;
- the five repos are named;
- the branch state, the #438 and #439 times and the pre-#231 line numbers are corrected;
- "four gaps" is gone.

**Round 2: two lanes on v2 (frozen about 00:05Z) and on the merged fix-forwards.**

| lane | lens | verdict |
| --- | --- | --- |
| R1 | reconcile every round-1 finding against source; hunt for errors the fixes introduced | PASS: every round-1 major closed; 13 new minors or nits |
| R2 | adversarial on the fixes themselves | FAIL: 8 major, 8 minor |

**R2's majors, each re-derived before acting:**

- **F1–F3.** #233's Helm tests judged one labelled policy at a time, but Kubernetes unions every
  policy that selects a pod. So a widened deny-all, a second or unlabelled policy, a widened
  selector, or a data policy that no longer applied all passed. **juniper-deploy#235** evaluates
  the union. 26/26 planted defects are caught, all eleven of R2's shapes among them.
- **F6–F7.** #234 checked two compose keys, and others undid the route (`gateway_mode_ipv4`,
  `inhibit_ipv4`, interpolations); `extends` could hide an attachment. #235 pins the definition and
  forbids `extends`, and 21/21 are caught.
- **F8.** juniper-cascor#691's consequence was false. Nothing has started the manager since
  `aa46ad55`: `_start_manager`'s only call is commented out at `cascade_correlation.py:2676`. The
  issue was edited to call the defect latent, and a comment records the change.
- **F9, a minor folded in with F8.** The key is also in `config_json`, and post-fix keys do not
  round-trip. Both are now in the issue.
- **F10.** Per-file counts can miss a same-lines conflict resolved in the PR's favour. The rule now
  says to re-read the diff content, with counts only as a screen.
- **F13.** worker#199's corrected sentence repeated F8's premise. worker#200 defers to #691.

**R1's minors and R2's other minors** are applied. They cover:

- the branch count and #2079's time;
- the mnist and arc_agi claim, now **measured in the stack** (both `201`);
- the undeclared-network gap (#235);
- `--paginate`;
- undefined references;
- the stale PyPI line in deploy's CHANGELOG;
- the restored residue (the update-branch arm, the sweeper, the `find` trap, "tell the owner");
- the memory-file list;
- script-comment nits;
- the Docker firewall caveat;
- the `source: local` qualifier.

**Round 3: lanes on v3 and on #235's merged guards.** The shapes #235's tests still passed are the
ones #236 lists in *What this session did*, among them #235's own weakened policies-off check.
**juniper-deploy#236** makes the guards fail closed on every one. Document minors applied:
- #235's body round number;
- memory `reference_a_conflict_resolved_for_your_pr_can_drop_mains_lines.md`'s link to
  `safe-merge-exits-zero-without-merging`;
- cascor#691's restore paths (`config_json`, and the sanitizer that does not drop the key);
- the #233 row;
- the `down -v` trap and the git-state caution.

Still open: *Remaining* item 4's edits to `…PUBLISHING-PLAN.md`.

**Round 4: not run.** The owner paused the arc and asked for this update without validation.

## Git state

- **Worktree.** This session's worktree is `juniper-ml/.claude/worktrees/serene-swinging-beacon`, on
  local branch `worktree-serene-swinging-beacon`, fast-forwarded to `df21367d`. Its edits reach
  `main` only through the archiving PR; it holds no commits of its own. That PR's branch
  (`docs/handoff-data-0-16-0-egress-guards-fail-closed`) carries this file, the predecessor's
  banner, `…PUBLISHING-PLAN.md` and the seven `util/ad-hoc/2026-09-24_*` scripts this session wrote.
- **Remote branches.** Apart from the archiving PR's branch, none of this session's remain. Ten were
  deleted on merge, #236's `test/egress-guards-fail-closed` among them (the three
  repositories delete a branch on merge), and juniper-data `docs/changelog-x8-to-unreleased` was
  deleted by hand.
- **Carried from `…cut-at-one-commit-….md`:** six local `wip/*` branches were marked deletable once
  #2079 merged. It merged 10:08:31Z, and they still exist.
  - `wip/records-0924` is checked out in `juniper-ml/.claude/worktrees/fluffy-sniffing-mochi`, the
    predecessor session's worktree by its own handoff. Which live session, if any, still uses it
    is not established. **Ask the owner before removing `fluffy-sniffing-mochi` or
    `wip/records-0924`.**
  - Before any cleanup, check that worktree for uncommitted and ignored files, and follow
    `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`.
  - Never run `util/remove_stale_worktrees.bash`.
- **Leftovers.** The session created no sibling worktrees, and left no containers, networks or
  volumes.
