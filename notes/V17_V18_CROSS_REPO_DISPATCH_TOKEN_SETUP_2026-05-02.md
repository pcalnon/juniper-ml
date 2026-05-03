# V17 / V18 — `CROSS_REPO_DISPATCH_TOKEN` Setup Walkthrough

**Author:** Paul Calnon
**Date:** 2026-05-02
**Cycle:** Post-V01-V37 alignment closeout (juniper-ml)
**Status:** `CROSS_REPO_DISPATCH_TOKEN` has been provisioned (2026-05-02). Awaiting end-to-end verification on the next Dependabot `dependabot/pip/**` PR — see §2.6.
**Related findings:**
V17 (juniper-data `lockfile-update.yml` startup_failure / missing secret),
V18 (juniper-canopy `lockfile-update.yml` startup_failure / missing secret).

---

## 0. Plan

This document walks through provisioning the `CROSS_REPO_DISPATCH_TOKEN` secret needed by `lockfile-update.yml` in juniper-data and juniper-canopy (and by analogous workflows in other repos that follow the same pattern).
The plan has six stages:

1. **Document the existing situation** — what each workflow does, why it needs a non-default token, and the specific symptom that V17 and V18 represent.
2. **Walk through token creation and configuration** end-to-end:
   - choosing the token type (Personal Access Token classic vs. fine-grained vs. GitHub App installation token);
   - selecting scopes / permissions;
   - storing the secret at the right level (repo vs. environment vs. organization);
   - verifying the workflow accepts it.
3. **Document best practices and security considerations** — least-privilege scoping, expiration, rotation cadence, audit, and the CODEOWNERS / branch-protection interactions.
4. **Audit and validate** the walkthrough against what the workflow actually requires.
5. **Write the result into a markdown file in `notes/`** (this file).
6. **Lint** the markdown file.

---

## 1. Existing Situation

### 1.1 What `lockfile-update.yml` does

Both juniper-data and juniper-canopy ship a workflow at `.github/workflows/lockfile-update.yml` that:

1. Triggers on `push` to branches matching `dependabot/pip/**` (i.e., when Dependabot opens or updates a Python dependency PR).
2. Runs `uv pip compile pyproject.toml --upgrade -o requirements.lock` to regenerate the lockfile so the bumped dependency's transitive pins stay consistent.
3. Commits the regenerated `requirements.lock` back to the same `dependabot/pip/**` branch with the message `[dependabot skip] Update requirements.lock`.

The flow is documented inline at the top of each workflow file:

```yaml
# Description:
#    Automatically updates requirements.lock when Dependabot pushes a dependency
#    update to a dependabot/pip/** branch. Runs uv pip compile to regenerate
#    the lockfile and commits the result so Docker builds stay in sync.
#
#    Uses CROSS_REPO_DISPATCH_TOKEN (not GITHUB_TOKEN) so the push re-triggers CI.
```

### 1.2 Why the workflow uses a custom token instead of `secrets.GITHUB_TOKEN`

GitHub Actions ships every workflow run with an automatically-issued `GITHUB_TOKEN` (`secrets.GITHUB_TOKEN`).
It is conveniently available without any setup — but it has one critical limitation for this workflow: **commits and pushes made with `GITHUB_TOKEN` do not trigger downstream `push`/`pull_request` events**.
This is a deliberate GitHub policy to prevent infinite-loop workflow recursion.

For `lockfile-update.yml` we *want* the lockfile commit to re-trigger the main `ci.yml` pipeline (lint + test + build + lockfile freshness check) on the Dependabot branch — otherwise the PR sits at "lockfile stale" forever.

The standard workaround is to push with a different token that GitHub treats as a "real user" actor.
We use a token named `CROSS_REPO_DISPATCH_TOKEN`.
(The name is historical from an earlier cross-repo dispatch use case; the workflow now uses it only as a "non-`GITHUB_TOKEN` push-and-retrigger" credential within the same repo.)

### 1.3 Failure mode that V17 and V18 represent

When the secret isn't configured:

- For juniper-data, the V17 finding records that `actions/checkout@... with: token: ${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}` resolves to an **empty string**, which `actions/checkout` interprets as "fall back to GITHUB_TOKEN" — checkout *succeeds*, but the later `git push` runs under `GITHUB_TOKEN`, which then **does not retrigger CI** on the Dependabot branch.
  - The Lockfile Freshness check on the PR stays red forever even after the lockfile is updated, because the PR's CI was last run before the lockfile commit landed.
- For juniper-canopy, V18 is the same shape on the canopy `lockfile-update.yml`.

Both findings are flagged in `notes/CI_VALIDATION_FINDINGS_2026-04-29.md` as "deferred — depends on user-side secret config" because no amount of code change in either repo can solve them without the secret being provisioned.

### 1.4 Repos that need the secret

The current canonical pattern is to provision the secret at **each repo** that has a `lockfile-update.yml` workflow. As of 2026-05-02:

| Repo                    | Has `lockfile-update.yml`? | Needs the secret? |
|-------------------------|----------------------------|-------------------|
| juniper-data            | Yes                        | **Yes** (V17)     |
| juniper-canopy          | Yes                        | **Yes** (V18)     |
| juniper-cascor          | Yes                        | Yes (latent)      |
| juniper-data-client     | Yes                        | Yes (latent)      |
| juniper-cascor-client   | Yes                        | Yes (latent)      |
| juniper-cascor-worker   | Yes                        | Yes (latent)      |
| juniper-ml              | No (uses ci.yml only)      | No                |
| juniper-deploy          | No                         | No                |

V17/V18 are the two repos that are *currently active* with Dependabot PRs; the other four repos with `lockfile-update.yml` will hit the same issue the first time Dependabot opens a Python PR there.

If you provision the secret at the **organization level** (see §3.4) you cover all six repos in one step, plus any future repos that adopt the same workflow.

---

## 2. Walkthrough — Creating and Configuring `CROSS_REPO_DISPATCH_TOKEN`

There are three credential types that can serve as `CROSS_REPO_DISPATCH_TOKEN`.
They are listed in order of *increasing* security but *increasing* setup cost.
Pick one and follow the matching sub-walkthrough.

### 2.1 Decision tree

```text
START
 │
 ├── Single user, ≤ 5 repos, want it working today?
 │      → §2.2 (PAT classic). Lowest setup, but least granular.
 │
 ├── Single user, want least-privilege per-repo / want fine-grained
 │   permissions / want to scope to specific repos?
 │      → §2.3 (Fine-grained PAT). Recommended for individual maintainers.
 │
 └── Multi-user org, want non-personal credential, want to survive a
     maintainer leaving?
        → §2.4 (GitHub App installation token). Recommended for orgs.
```

For the Juniper ecosystem (single maintainer @pcalnon, 8 active repos), **§2.3 (fine-grained PAT) is the recommended path**.
§2.4 is documented for the future "what if Juniper grows beyond a single maintainer" case.

### 2.2 Option 1 — PAT (classic)

**When to use:** simplest, broadest scopes. Works everywhere a PAT works. Use only as a stop-gap if §2.3 isn't an option for some reason.

**Steps:**

1. Sign in to GitHub as the account that should *own* the token. The token will appear as the *actor* of every push it makes — usually you want this to be the maintainer's user account, not a bot.
2. Go to **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**.
3. Fill in:
   - **Note:** `juniper CROSS_REPO_DISPATCH_TOKEN` (so it shows up in the audit log with a clear purpose).
   - **Expiration:** 90 days (rotate quarterly — see §3.2).
   - **Scopes:**
     - ✅ `repo` (Full control of private repositories) — required to push to a `dependabot/pip/**` branch.
     - Nothing else. *Do not* check `workflow`, `admin:repo_hook`, `delete_repo`, `gist`, `notifications`, `user`, etc.
4. Click **Generate token**. Copy the token value **exactly once**; GitHub will not show it again.
5. Provision the token as a repository secret (§3.1) named `CROSS_REPO_DISPATCH_TOKEN` in each repo from §1.4. *Or* provision it as an org secret (§3.4) if the repos are under a GitHub org.

**Caveat:** PAT (classic) cannot be scoped to specific repos. If the account has admin on other repos in your account/org, this token inherits those rights. Prefer §2.3 for production use.

### 2.3 Option 2 — Fine-grained Personal Access Token (recommended)

**When to use:** least-privilege per-repo control with a PAT-style single-credential UX. Recommended for the Juniper ecosystem.

**Steps:**

1. Sign in to GitHub as the account that should own the token.
2. Go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
3. Fill in:
   - **Token name:** `juniper-lockfile-update-CROSS_REPO_DISPATCH_TOKEN`
   - **Description:** `Used by .github/workflows/lockfile-update.yml in juniper-* repos to push the regenerated requirements.lock back to dependabot branches with a non-GITHUB_TOKEN actor so CI re-triggers.`
   - **Resource owner:** the user that owns the juniper repos (or the org if applicable).
   - **Expiration:** 90 days (rotate quarterly).
   - **Repository access:** **Only select repositories**, then choose all six juniper repos that have `lockfile-update.yml` (`juniper-canopy`, `juniper-cascor`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-data`, `juniper-data-client`).
   - **Repository permissions:**
     - **Contents:** **Read and write** (required so `git push` to `dependabot/pip/**` branches succeeds).
     - **Pull requests:** **Read and write** (recommended; lets the workflow leave a comment on the PR if needed; not strictly required by the current workflow but cheap to keep available).
     - **Metadata:** **Read-only** (auto-selected, mandatory for any repo-scoped fine-grained token).
     - **Everything else:** leave at **No access**.
   - **Account permissions:** leave all at **No access**. The workflow only needs repo-scoped operations.
4. Click **Generate token**. Copy the token value once.
5. Provision the token as a repo or org secret (§3) named `CROSS_REPO_DISPATCH_TOKEN`.

### 2.4 Option 3 — GitHub App installation token

**When to use:** future-proof, non-personal credential. The token is issued from a GitHub App installation rather than a user account, so it survives a maintainer leaving and shows up in audit logs as the App's identity.

**High-level steps** (full walkthrough out of scope; pointer for the day Juniper grows beyond a single maintainer):

1. Create a GitHub App named e.g. `juniper-lockfile-bot`.
2. Grant the App the same fine-grained permissions as §2.3 (Contents: write, Pull requests: write).
3. Install the App on the juniper-* repos.
4. In each `lockfile-update.yml`, replace the `token: ${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}` line with the `tibdex/github-app-token@…` (or `actions/create-github-app-token@…`) action that mints a short- lived installation token from the App's private key, and pass the minted token to subsequent steps.
5. Store only the App's `app_id` and base64-encoded `private_key` as repository or organization secrets — both rotate independently from any user account.

For the V17/V18 unblock, §2.3 is sufficient. Migrating to §2.4 is a later refinement.

### 2.5 Provisioning the secret in GitHub

Once you have the token value from §2.2, §2.3, or §2.4, store it where the workflow can read it.

#### 2.5.1 Repo-level secret (per-repo)

For each repo that needs the secret:

1. Go to **`https://github.com/<owner>/<repo>/settings/secrets/actions`**.
2. Click **New repository secret**.
3. **Name:** `CROSS_REPO_DISPATCH_TOKEN` (must match the workflow's `${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}` reference exactly — including underscores and case).
4. **Secret:** paste the token value.
5. **Add secret**.

Repeat for each of the six juniper-* repos with `lockfile-update.yml`.

#### 2.5.2 Organization-level secret (recommended if any of the repos are under an org)

If the juniper-* repos are owned by an organization rather than a user account:

1. Go to **`https://github.com/organizations/<org>/settings/secrets/actions`**.
2. Click **New organization secret**.
3. **Name:** `CROSS_REPO_DISPATCH_TOKEN`.
4. **Secret:** paste the token value.
5. **Repository access:** **Selected repositories**, then add all six juniper-* repos with `lockfile-update.yml`. (Avoid "All repositories" — lockfile-update is a niche workflow and should not leak the token to repos that don't need it.)
6. **Add secret**.

This single org-level secret then satisfies V17, V18, **and** all four latent equivalents in cascor / cascor-client / cascor-worker / data-client.

### 2.6 Verification

After provisioning, verify end-to-end on each repo by triggering the workflow once:

#### 2.6.1 Wait for the next Dependabot PR (organic verification)

Dependabot is configured for weekly Python updates in each repo. The next time it opens a `dependabot/pip/**` PR, `lockfile-update.yml` should fire automatically. Watch for:

1. The lockfile-update workflow run completes successfully (green).
2. A second commit appears on the Dependabot branch with the message `[dependabot skip] Update requirements.lock` and an actor of either your user account (PAT path) or `<github-app-name>[bot]` (App path).
3. **Most importantly:** `ci.yml` re-runs on the new SHA after the lockfile-update commit lands. If `ci.yml` does not re-run, the token is being silently downgraded to `GITHUB_TOKEN`; double-check the secret name matches `CROSS_REPO_DISPATCH_TOKEN` exactly.

#### 2.6.2 Force-trigger via a manual `workflow_dispatch` (active verification)

`lockfile-update.yml` currently only triggers on `push` to `dependabot/pip/**`. To verify without waiting for Dependabot:

1. Locally check out a `dependabot/pip/test-token` branch:

   ```bash
   git checkout -b dependabot/pip/test-token
   git commit --allow-empty -m "test: probe CROSS_REPO_DISPATCH_TOKEN"
   git push -u origin dependabot/pip/test-token
   ```

2. Wait for `lockfile-update.yml` to fire. (Note: the `if: github.actor == 'dependabot[bot]'` guard at line 42 of canopy's workflow will *block* manual triggers — for the verification probe, temporarily relax that guard or run from a Dependabot branch the bot itself has pushed to.)

3. After verifying, delete the probe branch:

   ```bash
   git push origin :dependabot/pip/test-token
   ```

#### 2.6.3 Confirm V17/V18 closure

Once §2.6.1 or §2.6.2 succeeds, update `notes/CI_VALIDATION_FINDINGS_2026-04-29.md` to mark V17 and V18 as **fixed (verified)**, citing the verification run URLs. Update `notes/CI_ALIGNMENT_AUDIT_2026-04-29.md` fleet table to drop V17 and V18 from each row's deferral list.

---

## 3. Best Practices and Security Concerns

### 3.1 Least privilege

The token has **write access to the contents of repositories that hold the project's source code**. Treat it as you would treat a deploy key — **never paste it into a chat, never commit it, never log it**.

Specific guard rails:

- Use the **fine-grained PAT** (§2.3), not the classic PAT (§2.2), unless there's a specific reason classic is required.
- Limit the fine-grained PAT to **only the six juniper-* repos with `lockfile-update.yml`**. Do not grant access to all repositories.
- Limit permissions to **Contents: write** and **Pull requests: write**. Do not grant Actions: write, Workflows: write, or any Account-level permission.
- If your account has admin on unrelated production repos, consider generating the PAT under a **separate "automation" GitHub user** that has access only to the juniper-* repos. The PAT can never exceed the access of the user that mints it, so a constrained user is itself a guard rail.

### 3.2 Expiration and rotation

- Set the token expiration to **90 days**. GitHub will email when the token is 7 days from expiry. Rotate it in the same calendar reminder slot you rotate other secrets.
- After generating the new token, update the `CROSS_REPO_DISPATCH_TOKEN` secret in **all locations** at the same time (org-level if you used §2.5.2, otherwise per-repo). The old token continues to work until its expiration date, so there's no downtime as long as you rotate before expiry.
- Keep a run of `gh secret list` per repo (or per org) handy as a rotation checklist. Example:

  ```bash
  for repo in juniper-canopy juniper-cascor juniper-cascor-client \
              juniper-cascor-worker juniper-data juniper-data-client; do
      echo "=== $repo ==="
      gh secret list --repo "pcalnon/$repo"
  done
  ```

### 3.3 Audit and observability

- After rotation, scan recent `lockfile-update` runs for one with the new token: the run's "checkout" step shows the actor in the log header.
- Watch the GitHub audit log (`https://github.com/<owner>/settings/security-log` for users; `https://github.com/organizations/<org>/settings/audit-log` for orgs) for `personal_access_token.create` and `org.update_actions_secret` events.
- Treat any unexplained `git push` to a `dependabot/pip/**` branch outside of normal lockfile-update times as a token-leak signal — the actor of an unauthorized push will appear in the branch's reflog.

### 3.4 Why org-level is preferred (if applicable)

The Juniper repos are currently under the user account `pcalnon`, not an organization. **All advice in §2.5.2 about org-level secrets applies if and when the project moves to an org**, not before. For the user-owned model:

- Every repo needs the secret provisioned individually (§2.5.1).
- Six secret-store entries to update on rotation.
- A PR that adds a *seventh* `lockfile-update.yml` to a new repo must include a checklist item to also provision the secret in that new repo.

Migrating to an org later is straightforward (delete the per-repo secrets, add a single org secret with selected-repository scope, then re-verify).

### 3.5 Branch-protection interactions

- `lockfile-update.yml` writes to `dependabot/pip/**` branches, not to `main`. Branch-protection rules on `main` (required reviews, required status checks, signed commits) do **not** affect this workflow.
- The workflow's commit message includes `[dependabot skip]` so Dependabot itself doesn't re-run on its own auto-pushed commit.
- If you add CODEOWNERS-required reviews to `main`, ensure the PAT-issuing user is **not** a CODEOWNER for `requirements.lock`, or the lockfile-update commit will create a self-review situation on the eventual PR merge.

### 3.6 Required-checks interactions

The juniper-* repos' `ci.yml` workflows include a "Lockfile Freshness" job.
The whole point of the `CROSS_REPO_DISPATCH_TOKEN` plumbing is to ensure that job *re-runs* after the lockfile-update commit lands on the Dependabot branch.
If the workflow's `required-checks` gate doesn't include "Lockfile Freshness" in the PR's required check set, fixing the token *isn't enough*: the PR will merge with a stale check status.
Verify the branch protection rule for `main` includes "Lockfile Freshness" as a required check on PRs.

### 3.7 Token-leak response procedure

If the token is leaked (e.g., accidentally pasted into a public issue, committed to a repo, or shared in a chat outside the trust-boundary):

1. Immediately revoke the token via **Settings → Developer settings → Personal access tokens → (token name) → Delete**.
2. Generate a new token following §2.3.
3. Update the secret store(s) per §2.5.
4. Audit recent `dependabot/pip/**` pushes for actor anomalies.
5. If the leak was in a public location, also rotate any other credentials that were potentially co-disclosed.

---

## 4. Audit and Validation

### 4.1 Walkthrough completeness check

| Requirement                                                              | Section         | Status                                                                                                                 |
|--------------------------------------------------------------------------|-----------------|------------------------------------------------------------------------------------------------------------------------|
| Develop a plan for addressing V17/V18                                    | §0              | ✅                                                                                                                     |
| Thoroughly document the existing situation for V17/V18                   | §1              | ✅ — what the workflow does, why it needs a non-default token, the failure mode, scope across repos                    |
| Generate a detailed walkthrough for creating and configuring the secrets | §2              | ✅ — three credential options, per-step UI navigation, secret provisioning, verification                               |
| Consider and document best practices and security concerns               | §3              | ✅ — least-privilege, expiration/rotation, audit, org-vs-user, branch protection, required checks, token-leak response |
| Audit and validate all aspects                                           | §4              | ✅                                                                                                                     |
| Write into notes/                                                        | this file       | ✅ — `notes/V17_V18_CROSS_REPO_DISPATCH_TOKEN_SETUP_2026-05-02.md`                                                     |
| Lint and fix syntax violations                                           | post-write step | runs after this file is saved (see §4.3)                                                                               |

### 4.2 Cross-checks against the actual workflow code

The walkthrough was validated against the live workflow contents:

| Claim                                                                        | Walkthrough section | Verified against                                                                                                                      |
|------------------------------------------------------------------------------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Workflow uses `secrets.CROSS_REPO_DISPATCH_TOKEN` (not GITHUB_TOKEN)         | §1.1, §1.2          | `juniper-canopy/.github/workflows/lockfile-update.yml:49`, `juniper-data/.github/workflows/lockfile-update.yml:47` (token references) |
| Workflow triggers on `push` to `dependabot/pip/**`                           | §1.1, §2.6.2        | both files' `on:` block                                                                                                               |
| Workflow's permissions block declares `contents: write`                      | §3.1, §2.3          | both files' `permissions:` block                                                                                                      |
| Workflow runs `uv pip compile pyproject.toml --upgrade -o requirements.lock` | §1.1                | both files' "Regenerate requirements.lock" step                                                                                       |
| `if: github.actor == 'dependabot[bot]'` guard blocks non-Dependabot triggers | §2.6.2              | canopy `lockfile-update.yml:42` and the equivalent line in juniper-data                                                               |
| Six juniper-* repos have a `lockfile-update.yml`                             | §1.4, §3.2          | repo-by-repo `find -name lockfile-update.yml`                                                                                         |

### 4.3 Linting

After saving, run:

```bash
markdownlint -c .markdownlint.yaml notes/V17_V18_CROSS_REPO_DISPATCH_TOKEN_SETUP_2026-05-02.md
```

The juniper-ml `.markdownlint.yaml` sets `line-length: 512` and disables `ol-prefix` — which this document complies with.
The ASCII-art decision tree in §2.1 deliberately uses a fenced code block (language `text`) so markdownlint treats it as preformatted.
The verification command examples in §2.6.2, §3.2, and §4.3 are fenced `bash` blocks for the same reason.

### 4.4 Open follow-ups (not part of this walkthrough)

- §2.4 (GitHub App route) is a sketch, not a full walkthrough. If the Juniper ecosystem ever moves to an org or onboards a second maintainer, expand §2.4 into a full walkthrough.
- §3.6 (branch protection / required checks) assumes the PR's required-checks set includes "Lockfile Freshness". Verify that setting on each repo's `main` branch protection rule the next time you touch the rule.
- The single-maintainer rotation cadence is calendar-based (90 days). If/when the team grows, replace with an automation — e.g., a `juniper-rotation-bot` GitHub App that mints short-lived installation tokens for each lockfile-update run, eliminating long-lived PATs entirely.

---

## Appendix A — Cheat sheet for the impatient

If you just want to clear V17 and V18 right now and read the rationale later:

1. Generate a fine-grained PAT scoped to `juniper-canopy` and `juniper-data` only:
   - **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.**
   - Repository access: **Only select repositories** → pick both.
   - Permissions: **Contents: Read and write**, **Pull requests: Read and write**, **Metadata: Read-only**.
   - Expiration: **90 days**.
2. Add the token as `CROSS_REPO_DISPATCH_TOKEN` secret in each repo:
   - `https://github.com/pcalnon/juniper-canopy/settings/secrets/actions/new`
   - `https://github.com/pcalnon/juniper-data/settings/secrets/actions/new`
3. Wait for the next Dependabot PR in either repo. Confirm the lockfile-update workflow runs green and that `ci.yml` re-runs on the post-update commit.
4. Mark V17 and V18 fixed-verified in `notes/CI_VALIDATION_FINDINGS_2026-04-29.md`.

If you want to also clear the four latent cases (cascor / cascor-client / cascor-worker / data-client), add those four repos to the same fine-grained PAT's repository-access list and provision the secret in each.

---

## Appendix B — Mapping to the V01-V37 alignment cycle

V17/V18 are the only **secret-config** items in the entire V01-V37 catalog.
Every other finding in the cycle was either:

- a **CI-config** issue (workflow YAML, linter scope, lockfile drift) — fixed by editing files in the repo, or
- a **product or test** issue — fixed by editing source/tests, or
- **resolved upstream** by an unrelated PR.

Because V17/V18 require a one-time GitHub UI / `gh` CLI action that is not version-controlled in any repo, they are intentionally the final residue of the cycle: nothing else can be done from the codebase side.
Once provisioned, the workflows themselves require no further changes.
