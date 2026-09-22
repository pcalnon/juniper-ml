# Docker Hub Secret Registration — Owner Procedure (Wave 4 unblock)

**Project:** Juniper (ecosystem-wide)
**Author:** Paul Calnon
**Date:** 2026-09-22
**Status:** READY TO EXECUTE — owner action. **§3 RULED 2026-09-22: Option B**, a dedicated
`dockerhub` environment, so §5.2B is the path and §5.2A is not used.
**Unblocks:** Wave 4 of
[`JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`](JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md)
§6 OQ-1, ruled 2026-09-11.

---

## 1. What this is, and what it is not

Wave 4 adds `docker.io` as a **second** push target beside GHCR (plan D-2 phase 2). The plan's
own words on sequencing:

> **Owner action before any Wave 4 workflow change**: register a `DOCKERHUB_TOKEN` (and
> `DOCKERHUB_USERNAME`) repository secret in each of the five image repos […] **Until those
> exist the second login+push cannot be added, and adding it early would fail every release.**

The quote's *"repository secret"* is **superseded**. §3 ruled on 2026-09-22 that the credential is
an **environment** secret, and the plan was amended to match. The sequencing point stands.

**This document covers the credential registration only.** It does **not** change any workflow.
That ordering is not fussiness: the publish workflows are `release`-triggered, so a login step
referencing a secret that does not exist fails **at release time**, on the path that ships, after
the Release has already been cut.

**Nothing here is reversible-by-accident**, but everything here is reversible-on-purpose — see
§8.

---

## 2. Preconditions the owner must supply

These are **not** discoverable from the repos. A sweep for `docker.io/`, `dockerhub` and
`DOCKERHUB_` across all six image-bearing repos (2026-09-22) found **no existing Docker Hub
integration at all** — the only `docker.io` hit is buildx error text quoted in a comment at
`juniper-cascor-worker/.github/workflows/publish-image.yml:179`.

| precondition | why it matters | status |
| --- | --- | --- |
| A Docker Hub account exists | the namespace `docker.io/<user>/<image>` is derived from it | **UNKNOWN — owner must confirm** |
| Its **username**, exactly as Docker Hub spells it | becomes `DOCKERHUB_USERNAME`; Docker Hub usernames are lowercase and this is the push namespace, not a display name | **UNKNOWN** |
| The account tier | Personal (free) is sufficient — see §6 | assumed Personal |
| Five repositories exist or can be auto-created on first push | Personal allows **unlimited public** repos | assumed |

> **`pcalnon` is a GitHub User, not an Organization** (`gh api orgs/pcalnon` → 404, verified
> 2026-09-22). There is therefore **no organization-secret scope** available. Every secret below
> is per-repository or per-environment. Do not go looking for an org-level place to put it once.

---

## 3. RULED 2026-09-22 — Option B: environment secrets in a dedicated `dockerhub` environment

> **Owner ruling, 2026-09-22: Option B.** The credential lives in a `dockerhub` environment in
> each of the five repositories, restricted to release tags, with no reviewer and no wait timer.
> Register it with §5.2B; §5.2A is not used. This supersedes the plan's *"repository secret"*
> (plan §6 OQ-1, amended the same day).
>
> **One statement below was wrong when the ruling was made**, and is corrected in place: Option B's
> cost was given as two extra lines per repository. Taken literally, those two lines would reject
> every pull-request and dispatch run of `publish-image.yml` in all five repositories. The ruling
> still holds, because the correction changes **where** Wave 4 names the environment, not what
> the environment protects. See *Cost — corrected 2026-09-22* under Option B.

The plan said *"repository secret"*. This procedure recommended against that, and the owner
agreed. Both options stay written out below as the record of what was weighed.

### The problem with a repository secret

A repository secret is readable by **any workflow run in that repo, on any branch or tag**, not
only by `publish-image.yml` on a release. Any workflow a future PR adds — or any edit to an
existing one — can echo it. The blast radius is the whole repo's CI surface, forever.

### What this ecosystem already does for its other credential

`publish.yml` in these repos already gates PyPI publishing behind a **protected environment**, and
that environment is genuinely protected (verified on `juniper-cascor`, 2026-09-22):

| `pypi` environment | value |
| --- | --- |
| `required_reviewers` | `pcalnon` |
| `wait_timer` | 5 minutes |
| `branch_policy` | custom, **tags only**: `v*`, `rc*`, `hf*`, `juniper-*-v*`, `juniper-*-rc*`, `juniper-*-hf*` |

An environment secret is readable **only** by a job that declares `environment: <name>`, and only
when the ref satisfies that environment's branch policy.

> **This corrects a stale memory.** `memory/project_publish_path_authorization_2026-08-17.md`
> records that all 18 Juniper deployment environments had `deployment_branch_policy: null`. That
> was true on 2026-08-17 and is **false now** for `pypi` / `testpypi`, which carry custom tag
> policies. Re-probe before relying on either statement.

### Option A — repository secret (the plan's wording) — NOT CHOSEN

**Do this if** you want the least moving parts and accept the blast radius.
No workflow change beyond the eventual login step. Registration: §5.2A.

### Option B — a dedicated `dockerhub` environment — CHOSEN 2026-09-22

**Do this if** you want the credential scoped to the path that uses it.

Create an environment named `dockerhub` with a **branch policy of tags only** (`v*` plus the
`juniper-*-v*` family, mirroring `pypi`), and **no required reviewer and no wait timer** — the
Release is already an owner action, so a second manual gate on every image publish buys nothing
and delays every publish by 5 minutes.

**Cost — corrected 2026-09-22.** This paragraph first said the Wave 4 change would add
`environment: dockerhub` to **both** jobs in `publish-image.yml`: "two extra lines per repo and
… the whole of the extra work". **Taken literally, that breaks CI in all five repositories.**
GitHub matches an environment's branch and tag rules "against the `GITHUB_REF` of the workflow
run". The same page says it is adding a `refs/pull/*/merge` rule that "would also allow workflows
triggered by `pull_request` events" to use the environment. So without such a rule, a
pull-request run cannot use it. The branch policy is itself a protection rule: the API lists
`branch_policy` among the protection rules of juniper-cascor's `pypi` environment, next to
`required_reviewers` and `wait_timer`. And "the job won't start until all of the environment's
protection rules pass". (GitHub Docs, *Deployments and environments* and *Control deployments*,
read 2026-09-22.) Neither job runs only on release tags. In
`juniper-cascor/.github/workflows/publish-image.yml`:

| job | triggers | refs it runs on | a tags-only `dockerhub` environment |
| --- | --- | --- | --- |
| `build` | `release` (`:45`), `pull_request` (`:50`), `workflow_dispatch` (`:59`) | `refs/tags/v*`, `refs/pull/N/merge`, the dispatched branch | admits the release run only; **rejects every image-touching PR and every dispatch** |
| `merge` | `release`, or a dispatch with `push=true` (`:269`) | `refs/tags/v*`, the dispatched branch | **rejects every `push=true` dispatch**, the path that published the `dispatch-*` images |

So Wave 4 must name the environment **only on release runs**. There are two ways to do that, and
choosing between them belongs to the Wave 4 change (§7), not to this procedure:

1. **A separate release-only job that names `environment: dockerhub` unconditionally.** For
   example, a third job with `needs: [merge]`, gated to release runs, that copies the GHCR manifest
   list the in-image checks already passed to Docker Hub by digest
   (`docker buildx imagetools create`). The environment is then only ever checked against a
   release tag. The credential sits in one job that runs no build step. Docker Hub receives the
   same digest that was verified on GHCR, and §7's "two credential points" become one. **This is
   an outline, not a tested design.** Two things are unproven here: whether provenance
   attestations are copied across, and how to re-run a Docker Hub failure after GHCR has already
   published.
2. **A conditional environment name on the existing jobs**, for example
   `environment: ${{ github.event_name == 'release' && 'dockerhub' || '' }}`. **Unverified:**
   GitHub's documentation does not say what an empty environment name does. Test it in a
   throwaway repository first. If GitHub rejects it, or treats `''` as a real name, every PR run
   breaks as the table shows.

**The reason for the ruling survives the correction.** Option A exposes the credential to every
workflow on every ref. Option B exposes it only to a job that names the environment, and only on
a release tag. Both shapes keep that; they differ only in where the environment is named.

**Do NOT simply reuse `pypi`.** Its `required_reviewers` + 5-minute `wait_timer` would gate every
container publish behind manual approval — a behaviour change to a path that currently runs
unattended.

---

## 4. Create the access token (Docker Hub side)

Do this **once**. The same token value is registered into all five repos.

1. Sign in to <https://hub.docker.com/> as the account from §2.
2. **Account Settings → Personal access tokens → Generate new token.**
3. Set:
   - **Description**: `juniper-ci-image-publish-2026-09-22` — dated and purpose-named, so a later
     audit can tell what it is without guessing.
   - **Expiration**: set one. A never-expiring CI credential is a credential nobody ever reviews.
     12 months is reasonable; **write the expiry date into §10 of this document when you set it**,
     because nothing else will remind you.
   - **Access permissions**: **Read & Write**. *Not* Read/Write/Delete, and not Admin.
     The workflow pushes tags and manifests; it never deletes. The plan is explicit:
     *"Scope the token to Read & Write, not Admin."*
4. **Copy the token immediately.**

> **The token is displayed EXACTLY ONCE.** There is no "show again". If you navigate away before
> copying it, the only recovery is to delete it and generate another — and a half-registered
> token (in two repos of five) is worse than none, because the failure then appears only on the
> third repo's next release. This ecosystem has been bitten by a show-once credential before:
> `memory/project_grafana_admin_password_init_only_2026-05-10.md`.

---

## 5. Register the secrets (GitHub side)

### 5.1 The five repositories

Exactly these, from the plan's OQ-1:

```
juniper-cascor
juniper-cascor-worker
juniper-canopy
juniper-data
juniper-recurrence
```

> **juniper-deploy is deliberately NOT in this list.** It publishes
> `ghcr.io/pcalnon/juniper-deploy-test`, a containerised **test runner**, not a shipped service
> image. Whether that belongs on Docker Hub is an open question, not an oversight — recorded in
> §10.

### 5.2A Repository secrets (Option A) — NOT CHOSEN; do not run

> Kept as the record of what Option A would have needed. Running it would create the repo-wide
> exposure that §3 ruled against. Go to §5.2B. The warning below about `--body` applies there
> too.

`gh secret set` reads the value from stdin, so the token never appears in your shell history or
in `ps` output. Run one command per repo, pasting the token at the prompt:

```bash
gh secret set DOCKERHUB_TOKEN    --repo pcalnon/juniper-cascor
gh secret set DOCKERHUB_USERNAME --repo pcalnon/juniper-cascor
```

…and the same pair for `juniper-cascor-worker`, `juniper-canopy`, `juniper-data`,
`juniper-recurrence`. **Ten commands in total.**

> Do **not** use `--body "<token>"`. That puts the credential in your shell history and, briefly,
> in the process table where any local user can read it —
> `memory/reference_ps_cmdline_leaks_aescrypt_passphrase.md` records that exact leak in this
> ecosystem.

### 5.2B Environment secrets (Option B) — THE PATH, ruled 2026-09-22

Create the environment first, then set the secrets against it:

```bash
# 1. create the environment with no reviewer and no wait timer
gh api -X PUT repos/pcalnon/juniper-cascor/environments/dockerhub \
  -F wait_timer=0 -F 'deployment_branch_policy[protected_branches]=false' \
  -F 'deployment_branch_policy[custom_branch_policies]=true'

# 2. restrict it to release tags (mirrors the pypi environment)
gh api -X POST repos/pcalnon/juniper-cascor/environments/dockerhub/deployment-branch-policies \
  -f name='v*' -f type=tag
gh api -X POST repos/pcalnon/juniper-cascor/environments/dockerhub/deployment-branch-policies \
  -f name='juniper-*-v*' -f type=tag

# 3. the secrets, scoped to that environment
gh secret set DOCKERHUB_TOKEN    --repo pcalnon/juniper-cascor --env dockerhub
gh secret set DOCKERHUB_USERNAME --repo pcalnon/juniper-cascor --env dockerhub
```

Repeat all four steps for the other four repos.

> **Step 2 is not optional.** An environment created with `custom_branch_policies=true` and *no*
> policies added permits **nothing** — a job declaring it will never run. An environment created
> without step 1's `custom_branch_policies` flag permits **everything**, which throws away the
> entire reason for choosing Option B. Verify with §6 before assuming either.

---

## 6. Verify the registration — without printing the secret

GitHub's API **never returns a secret's value**. It returns names and timestamps only, which is
exactly what you want to check: that the name is spelled correctly and that it exists in all five
repos.

```bash
# Repository scope. Option B was ruled (§3), so this must show NO DOCKERHUB_* name. A
# `gh secret set` that dropped `--env dockerhub` puts the secret here, readable by the whole
# repo -- the exposure §3 ruled out. If one appears, delete it (§8) before going on.
for r in juniper-cascor juniper-cascor-worker juniper-canopy juniper-data juniper-recurrence; do
  printf '%-24s ' "$r"
  gh api "repos/pcalnon/$r/actions/secrets" --jq '[.secrets[].name] | join(",")'
done

# Environment scope (Option B, the ruled path). Expect DOCKERHUB_TOKEN and DOCKERHUB_USERNAME in each.
for r in juniper-cascor juniper-cascor-worker juniper-canopy juniper-data juniper-recurrence; do
  printf '%-24s ' "$r"
  gh api "repos/pcalnon/$r/environments/dockerhub/secrets" --jq '[.secrets[].name] | join(",")' 2>/dev/null \
    || echo "NO dockerhub ENVIRONMENT"
done

# Prove the environment is tag-restricted and its policy list NON-EMPTY -- in each repo.
# Expect, per repo: {"custom_branch_policies":true,"protected_branches":false}  tag:juniper-*-v*,tag:v*
# A null policy admits EVERY ref; custom=true with an empty list admits NONE (§5.2B's note).
for r in juniper-cascor juniper-cascor-worker juniper-canopy juniper-data juniper-recurrence; do
  printf '%-24s ' "$r"
  printf '%s  ' "$(gh api "repos/pcalnon/$r/environments/dockerhub" --jq '.deployment_branch_policy' 2>/dev/null || echo 'NO dockerhub ENVIRONMENT')"
  gh api "repos/pcalnon/$r/environments/dockerhub/deployment-branch-policies" \
    --jq '[.branch_policies[] | .type + ":" + .name] | join(",")' 2>/dev/null || echo "-"
done
```

**Baseline before you start** (verified 2026-09-22): all five repos hold exactly
`CROSS_REPO_DISPATCH_TOKEN,SOPS_AGE_KEY`, except `juniper-recurrence`, which holds **none**. If a
`DOCKERHUB_*` name appears before you have done anything, stop — someone else registered it and
you need to know who and with what scope.

**The name must match the workflow exactly.** A secret registered as `DOCKER_HUB_TOKEN` or
`DOCKERHUB_PAT` is not a typo that CI will catch for you: `secrets.DOCKERHUB_TOKEN` simply
evaluates to the empty string, `docker/login-action` fails with an unhelpful auth error, and it
fails **at release time**.

**Then prove the credential actually works**, before any workflow depends on it — a registered
secret is not a *valid* secret:

```bash
# from a machine with docker; reads the token from stdin, never from argv
docker login docker.io --username '<DOCKERHUB_USERNAME>' --password-stdin
docker logout docker.io
```

---

## 7. What happens next (NOT part of this procedure)

This section is recorded so the registration is not mistaken for completion. **Option B was
ruled, so the Wave 4 change starts by deciding where to name the environment**, using one of the
two shapes in §3. **Never name it unconditionally on the existing `build` or `merge` job.** That
rejects every PR and dispatch run of `publish-image.yml` (§3, *Cost — corrected*).

**Shape 1: a release-only Docker Hub job.** The `build` and `merge` jobs stay as they are. Add
one job to **each** of the five `publish-image.yml` files. The job:

1. names `environment: dockerhub`, runs after `merge`, and runs on release runs only;
2. logs in to Docker Hub, which is the **only** credential point (GHCR is read from, and its
   packages are public);
3. copies the manifest list that the `merge` job verified, by digest, applying the Docker Hub refs
   in the same `X.Y.Z` / `X.Y` / `latest` scheme (plan D-3).

**Shape 2: Docker Hub added to the existing jobs**, with the environment named conditionally,
once the empty-name behaviour is proven. Add to **each** file:

1. A second login in the **build** job (currently `Log in to GHCR`, `:131` in juniper-cascor).
2. A second login in the **merge** job (`:287`) — **this is the one that gets forgotten.**
   There are **two** credential points per workflow, because the build job pushes per-arch **by
   digest** and only the merge job applies tags and creates the manifest list. A change that adds
   Docker Hub to the build job alone produces arch blobs on Docker Hub with **no manifest tying
   them together** — an image that appears to exist and cannot be pulled by tag.
3. The conditional `environment:` on both jobs. **Never use the bare name** (§3).
4. The Docker Hub refs in the `metadata-action` tag computation, so both registries receive the
   same `X.Y.Z` / `X.Y` / `latest` scheme (plan D-3).

None of this should be written before §6 passes.

---

## 8. Revocation and rollback

**To roll back before any workflow uses the secret** — nothing depends on it, so simply delete it:

```bash
gh secret delete DOCKERHUB_TOKEN    --repo pcalnon/<repo> --env dockerhub   # Option B (ruled)
gh secret delete DOCKERHUB_USERNAME --repo pcalnon/<repo> --env dockerhub
gh api -X DELETE repos/pcalnon/<repo>/environments/dockerhub   # the whole environment, secrets included
gh secret delete DOCKERHUB_TOKEN    --repo pcalnon/<repo>            # Option A -- only to remove a mis-scoped copy (§6)
```

**If the token is ever exposed** — in a log, a screenshot, a paste — revoke it at the Docker Hub
end **first** (Account Settings → Personal access tokens → Delete), because that invalidates it
everywhere at once. Deleting the GitHub secret only stops *this* repo from using it; it does not
make the credential stop working. Then re-run §4 and §5 with a fresh token.

**A rotation is five repos, not one.** Whatever you do to the token, do it in all five, and
re-run §6 afterwards — a partially rotated credential fails on whichever repo releases next,
which may be weeks later.

---

## 9. Rate-limit posture — re-verified 2026-09-22

The plan's OQ-1 table was read on 2026-09-11. Re-checked today against
<https://docs.docker.com/docker-hub/usage/>:

| posture | value | status |
| --- | --- | --- |
| unauthenticated | **100 per 6 h**, per **IPv4 address or IPv6 /64 subnet** | **confirmed 2026-09-22** |
| authenticated, Personal | **200 per 6 h** | **confirmed 2026-09-22** |
| Pro / Team | unlimited | confirmed 2026-09-22 |
| public repositories, Personal | unlimited | not re-checked today |
| *a pull is counted once per **architecture*** | plan asserts this | **NOT confirmed** — the usage page does not state it. Treat as unverified. |

**The deployment consequence is unchanged and is the reason this matters**: every Pi node behind
one household connection shares a single **anonymous** bucket of 100/6 h, because the limit is
scoped to the IPv4 address or IPv6 /64, not to the machine. Wave 4's Pi nodes should therefore
`docker login` and draw on the authenticated 200/6 h. That is a **deployment** step, not a
workflow change, and it is easy to lose because it lives in neither the workflow nor this
procedure's five repos. It also bears on **OQ-3**.

---

## 10. Open items this procedure deliberately does not decide

| item | needs |
| --- | --- |
| ~~Option A vs Option B (§3)~~ | **RULED 2026-09-22: Option B** |
| Where Wave 4 names the environment (§3, §7) | Wave 4 design: a release-only job (shape 1), or a conditional name once proven (shape 2) |
| The Docker Hub account and username (§2) | owner — not discoverable from the repos |
| Token expiry date, once set (§4) | **write it here when you create the token** |
| Whether `juniper-deploy-test` should also publish to Docker Hub (§5.1) | owner — it is a test runner, not a service image |
| Pi-node `docker login` (§9) | deployment work, tracked against OQ-3 |

---

## 11. Verification summary

```bash
# 1. names only, never values: the secrets are in the ENVIRONMENT, and NOT at repo scope
gh api repos/pcalnon/juniper-cascor/environments/dockerhub/secrets --jq '[.secrets[].name]'
gh api repos/pcalnon/juniper-cascor/actions/secrets --jq '[.secrets[].name]'   # no DOCKERHUB_*

# 2. the environment is tag-scoped and its policy list NON-EMPTY (§6 loops all five repos)
gh api repos/pcalnon/juniper-cascor/environments/dockerhub/deployment-branch-policies \
  --jq '[.branch_policies[] | .type + ":" + .name]'

# 3. the credential is valid, not merely present
docker login docker.io --username '<user>' --password-stdin   # then: docker logout docker.io

# 4. nothing was published by accident — Wave 4 has not shipped
gh api repos/pcalnon/juniper-cascor/actions/workflows --jq '[.workflows[].name]'
```

**Related:** plan §6 OQ-1 and D-2 (`JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md`);
`memory/project_publish_path_authorization_2026-08-17.md` (stale on branch policies — see §3);
`memory/project_grafana_admin_password_init_only_2026-05-10.md` (show-once credentials);
`memory/reference_ps_cmdline_leaks_aescrypt_passphrase.md` (why `--password-stdin`).
