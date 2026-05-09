# Release Walkthrough — juniper-ml v0.4.1 & juniper-observability v0.1.1a

**Date**: 2026-04-28
**Author**: Paul Calnon (with Claude Opus 4.7)
**Scope**: First coordinated release of the new `juniper-observability`
sibling package alongside a juniper-ml meta-package companion bump.

This document captures the **complete, reproducible** procedure that
was carried out — including the commands run, why each step exists,
the verification points, and the gotchas encountered. Treat it as the
canonical runbook for future independent-package releases under the
`juniper-ml` repository.

---

## 0. Table of contents

- [1. Preconditions](#1-preconditions)
- [2. Version-bump strategy](#2-version-bump-strategy)
- [3. Bump versions in source](#3-bump-versions-in-source)
- [4. Update changelogs](#4-update-changelogs)
- [5. Commit and push to main](#5-commit-and-push-to-main)
- [6. Create the GitHub releases](#6-create-the-github-releases)
- [7. Workflow trigger fan-out and the duplicate-publish gotcha](#7-workflow-trigger-fan-out-and-the-duplicate-publish-gotcha)
- [8. TestPyPI verification](#8-testpypi-verification)
- [9. PyPI approval gate](#9-pypi-approval-gate)
- [10. Post-publish verification](#10-post-publish-verification)
- [11. Trusted-publisher prerequisite (one-time)](#11-trusted-publisher-prerequisite-one-time)
- [12. Gotchas and lessons learned](#12-gotchas-and-lessons-learned)
- [13. Future improvements](#13-future-improvements)

---

## 1. Preconditions

Before starting, the following must be true. If any are not, **stop and
fix them first** — the workflow will fail in unhelpful ways.

| Precondition | Why it matters | Verification |
|---|---|---|
| Working tree clean on `main` | Mixed local edits will get caught up in the release commit. | `git -C juniper-ml status --short` returns no output. |
| `gh` CLI authenticated | Needed for `gh release create` and run inspection. | `gh auth status` reports the GitHub.com token. |
| TestPyPI **pending publisher** registered for `juniper-observability` (project did not previously exist) | Trusted publishing requires the publisher to claim the project on the **first successful upload**. | <https://test.pypi.org/manage/account/publishing/> shows a Pending Publisher matching `pcalnon` / `juniper-ml` / `publish-observability.yml` / env `testpypi` and project name `juniper-observability`. |
| PyPI pending publisher registered for `juniper-observability` | Same reason on production PyPI. | <https://pypi.org/manage/account/publishing/> equivalent. |
| TestPyPI / PyPI trusted publishers for `juniper-ml` already exist | The meta-package has been published before, so the trusted publishers should already be registered against the existing project. | Existence of past releases on PyPI confirms it. |
| GitHub Actions environments `testpypi` and `pypi` exist on the repo | Both publish workflows reference `environment: testpypi|pypi`. | <https://github.com/pcalnon/juniper-ml/settings/environments>. |
| `pypi` environment has the desired approval gate | If a manual approval is required to promote to PyPI, configure it here. | Same settings page → `pypi` → "Required reviewers". |

> **Critical gotcha (root cause of the failed publish that motivated
> this release):** if the trusted publisher was registered on the
> *wrong* project (e.g. under `juniper-ml` instead of
> `juniper-observability`), uploads of the new project will fail with
> `400 Bad Request` from `https://test.pypi.org/legacy/`. The
> server-side message is opaque unless `verbose: true` is set on
> `pypa/gh-action-pypi-publish`. See §11 for the configuration steps.

---

## 2. Version-bump strategy

| Package | Old version | New version | Type of bump |
|---|---|---|---|
| `juniper-ml` | `0.4.0` | `0.4.1` | Patch (point release) |
| `juniper-observability` | `0.1.0a2` | `0.1.1a` | Patch + strip the trailing digit after the alpha designator |

### Why a patch bump for the meta-package

`juniper-ml` source itself did not change in this release. It is being
re-cut to *advertise* the new sibling package and the new workflows
that publish it. There is no breaking change and no new functional
surface in `juniper-ml`, so a patch bump is sufficient and accurate.

### Why `0.1.1a` (not `0.1.1a0`) on disk

Per the user's spec: "remove the trailing digit after the alpha
designator." This produces a literal `0.1.1a` in `pyproject.toml` and
in `juniper_observability/_version.py`. Note the **PEP 440
normalization** gotcha:

```python
>>> from packaging.version import Version
>>> str(Version("0.1.1a"))
'0.1.1a0'
```

So the upload to PyPI / TestPyPI will be normalized to `0.1.1a0`. The
**built artifact filenames** will read `juniper_observability-0.1.1a0-*`
and the project page will display `0.1.1a0`. The source-of-truth in
`pyproject.toml` stays `0.1.1a`. `pip install
juniper-observability==0.1.1a` resolves correctly because pip
normalizes specifiers the same way.

### Why two different versions

Each package has its own version namespace on PyPI. The two versions
**must differ** because they are independent distributions; the two
GitHub release tags also live in different namespaces (`v*` for
`juniper-ml`, `juniper-observability-v*` for the sibling).

---

## 3. Bump versions in source

Three files were modified.

### 3.1 `juniper-ml/pyproject.toml`

```diff
 [project]
 name = "juniper-ml"
-version = "0.4.0"
+version = "0.4.1"
```

### 3.2 `juniper-ml/juniper-observability/pyproject.toml`

```diff
 [project]
 name = "juniper-observability"
-version = "0.1.0a2"
+version = "0.1.1a"
```

### 3.3 `juniper-ml/juniper-observability/juniper_observability/_version.py`

```diff
-__version__ = "0.1.0a0"
+__version__ = "0.1.1a"
```

### 3.4 Verification

```bash
grep -n "^version" juniper-ml/pyproject.toml
grep -n "^version" juniper-ml/juniper-observability/pyproject.toml
grep -n "__version__" juniper-ml/juniper-observability/juniper_observability/_version.py

# Sanity-check PEP 440 acceptance + normalization
python3 -c "from packaging.version import Version; print(Version('0.4.1'), Version('0.1.1a'))"
# → 0.4.1 0.1.1a0
```

> **Gotcha — single source of truth for `juniper-observability`.**
> The package has *two* version strings (pyproject + `_version.py`).
> Forgetting to bump `_version.py` will leave `juniper_observability.__version__`
> out of sync with the wheel filename. The TestPyPI install verification
> in `publish-observability.yml` does a `python -c "import juniper_observability;
> print(juniper_observability.__version__)"` which will display the stale value
> and not actually fail (the import succeeds either way), so this gotcha is silent.

---

## 4. Update changelogs

### 4.1 `juniper-ml/CHANGELOG.md`

The existing `## [Unreleased]` section already documented the additions
for this release (the `juniper-observability` package, the two new
workflows, the hardcoded-values refactor, etc.). The change is a pure
section rename:

```diff
-## [Unreleased]
+## [Unreleased]
+
+## [0.4.1] - 2026-04-28
```

…and a refresh of the link references at the bottom:

```diff
-[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.3.0...HEAD
+[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.4.1...HEAD
+[0.4.1]: https://github.com/pcalnon/juniper-ml/compare/v0.4.0...v0.4.1
+[0.4.0]: https://github.com/pcalnon/juniper-ml/compare/v0.3.0...v0.4.0
```

### 4.2 `juniper-ml/juniper-observability/CHANGELOG.md` (new file)

`juniper-observability` did not have its own CHANGELOG before. A new
file was created documenting:

- `0.1.0a0` — the initial source drop (never released to PyPI / TestPyPI).
- `0.1.1a` — first publishable alpha; *why* the version jumped past `0.1.0a*`.

This file follows Keep a Changelog format and lives next to the
package's `pyproject.toml`. The sibling package is published from a
sub-directory build, so its changelog is intentionally local to that
directory rather than embedded in the meta-package's changelog.

---

## 5. Commit and push to main

The user explicitly requested a direct push to `main` (no PR), so the
commit was made on the main checkout (not the worktree this Claude
session was running in).

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-ml add \
  CHANGELOG.md \
  pyproject.toml \
  juniper-observability/CHANGELOG.md \
  juniper-observability/pyproject.toml \
  juniper-observability/juniper_observability/_version.py

git -C /home/pcalnon/Development/python/Juniper/juniper-ml commit -m "release: juniper-ml v0.4.1 + juniper-observability v0.1.1a

- Bump juniper-ml meta-package 0.4.0 → 0.4.1.
- Bump juniper-observability 0.1.0a2 → 0.1.1a (pyproject + _version.py)
  to obtain a fresh, never-uploaded alpha after the earlier publish
  attempts under 0.1.0a0 / 0.1.0a2 failed at the trusted-publisher
  handshake. PEP 440 normalizes 0.1.1a to 0.1.1a0 on upload.
- Promote juniper-ml CHANGELOG Unreleased → 0.4.1; refresh compare links.
- New juniper-observability/CHANGELOG.md documenting the 0.1.0a0 source
  drop and the 0.1.1a republish.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

git -C /home/pcalnon/Development/python/Juniper/juniper-ml push origin main
```

> **Gotcha — branch-protection bypass notice.** `main` is protected
> (PR required, status checks required, CodeQL pending). Direct pushes
> succeed only when the pusher has the bypass permission, and they
> emit a noisy `remote: Bypassed rule violations for refs/heads/main`
> banner. If you do **not** have bypass, this push will be rejected
> and you must use a PR.

> **Gotcha — staging by name.** `git status` showed an unrelated
> deleted file (`bla`) in the working tree. The `git add` command
> above lists files explicitly so the deletion is **not** swept into
> the release commit. Avoid `git add -A` / `git add .` for release
> commits for exactly this reason.

---

## 6. Create the GitHub releases

Two releases, two tag namespaces, two workflows.

### 6.1 juniper-ml v0.4.1

```bash
gh release create v0.4.1 \
  --repo pcalnon/juniper-ml \
  --target main \
  --title "v0.4.1 — juniper-observability companion + publish workflow" \
  --notes "<full release-notes body>"
```

This:

- Creates the lightweight tag `v0.4.1` pointing at the current `main` HEAD.
- Creates a GitHub Release of the same name.
- Fires `.github/workflows/publish.yml` (triggered by `release: published`).

### 6.2 juniper-observability v0.1.1a

```bash
gh release create juniper-observability-v0.1.1a \
  --repo pcalnon/juniper-ml \
  --target main \
  --prerelease \
  --title "juniper-observability v0.1.1a — first publishable alpha" \
  --notes "<full release-notes body>"
```

`--prerelease` is important: an alpha release should be flagged so it
does not get listed as the project's "latest" on the GitHub releases
page.

This:

- Creates the tag `juniper-observability-v0.1.1a` on `main` HEAD.
- Creates a prerelease GitHub Release.
- Fires `.github/workflows/publish-observability.yml` (triggered by
  `push: tags: [juniper-observability-v*]`).

### 6.3 Tag and release naming conventions

| Package | Tag pattern | Why |
|---|---|---|
| juniper-ml | `v<MAJOR>.<MINOR>.<PATCH>` | Matches the original meta-package convention used since v0.1.0. |
| juniper-observability | `juniper-observability-v<PEP440>` | Namespaced because both packages live in the same repo and both publish workflows are wired off tags. The prefix ensures `publish.yml` (which would also fire on `release: published`) does not collide with `publish-observability.yml`. |

---

## 7. Workflow trigger fan-out and the duplicate-publish gotcha

### 7.1 What actually fired

Three publish runs were triggered, not two:

| Run ID | Workflow | Trigger | Tag | Notes |
|---|---|---|---|---|
| 25089943338 | `publish.yml` | `release: published` (v0.4.1) | `v0.4.1` | The intended juniper-ml publish. |
| 25089949911 | `publish-observability.yml` | `push: tags` (juniper-observability-v0.1.1a) | `juniper-observability-v0.1.1a` | The intended juniper-observability publish. |
| 25089949852 | `publish.yml` | `release: published` (juniper-observability-v0.1.1a) | `juniper-observability-v0.1.1a` | **Duplicate** juniper-ml publish. |

### 7.2 Why the duplicate fires

`publish.yml` triggers on **any** `release: published` event. Because
the juniper-observability release is also a GitHub Release, it fires
`publish.yml` too. That run checks out the tag (which points at the
same commit as `v0.4.1`), builds `juniper-ml==0.4.1` from the
sub-directory above, and tries to upload it. TestPyPI rejects the
duplicate `0.4.1` upload with `400 File already exists`.

### 7.3 Why this is benign (today)

- The first run (25089943338) wins and successfully uploads `juniper-ml==0.4.1`.
- The duplicate run (25089949852) fails on the second upload attempt with
  "file already exists" — a non-destructive failure.
- No bad artifact reaches the index.

### 7.4 How to fix it permanently

Add a tag-pattern filter to `publish.yml`:

```yaml
on:
  release:
    types: [published]
  push:
    tags:
      - "v*"  # restrict to juniper-ml tags only
  workflow_dispatch:
```

…or filter inside the job with an `if:` guard:

```yaml
jobs:
  build:
    if: startsWith(github.ref, 'refs/tags/v') && !startsWith(github.ref, 'refs/tags/juniper-')
```

Future releases of additional sibling packages (e.g. juniper-deploy,
juniper-foo) will compound this problem — each new release will fire
N redundant `publish.yml` runs. Worth fixing before the next sibling
package is added.

---

## 8. TestPyPI verification

After both publish runs reached the `Publish to TestPyPI` step and
returned `success`:

```bash
# Inspect job-level status without scrolling through logs
gh api repos/pcalnon/juniper-ml/actions/runs/25089943338/jobs \
  --jq '.jobs[] | {name, status, conclusion}'
gh api repos/pcalnon/juniper-ml/actions/runs/25089949911/jobs \
  --jq '.jobs[] | {name, status, conclusion}'
```

Both reports should show:

```text
{"name":"Build and Validate","status":"completed","conclusion":"success"}
{"name":"Publish to TestPyPI","status":"completed","conclusion":"success"}
{"name":"Publish to PyPI","status":"waiting","conclusion":null}
```

`status=waiting` on `Publish to PyPI` confirms the GitHub Actions
`pypi` environment has a **required reviewer** approval gate (this
was configured upstream of this release).

### 8.1 What to verify on TestPyPI

Open these URLs in a browser:

- <https://test.pypi.org/project/juniper-ml/0.4.1/>
- <https://test.pypi.org/project/juniper-observability/0.1.1a0/>
  (note: PEP 440 normalizes `0.1.1a` to `0.1.1a0`)

Check:

- The version listed.
- The list of files (sdist + wheel).
- The "Project description" — pulled from the package's `README.md`.
- For `juniper-observability`: the project page should now exist (it
  did not exist before; the pending publisher claims it on first upload).

### 8.2 Optional install-from-TestPyPI smoke test

```bash
# In a throwaway venv:
python -m venv /tmp/jo_test && source /tmp/jo_test/bin/activate
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  --pre \
  "juniper-observability==0.1.1a"
python -c "import juniper_observability; print(juniper_observability.__version__)"
```

- `--extra-index-url https://pypi.org/simple/` is required because
  TestPyPI does **not** host every transitive dependency; pip needs a
  real index for `pydantic`, `starlette`, etc.
- `--pre` is required because `0.1.1a0` is a pre-release.
- For juniper-ml, do the equivalent install on a fresh venv (no
  `--pre`, since `0.4.1` is a final).

The publish-observability workflow performs an automated version of
this install verification with a 5-attempt retry loop to absorb
TestPyPI index lag.

---

## 9. PyPI approval gate

When the run reaches `Publish to PyPI`, GitHub pauses the job until
an authorized reviewer approves the deployment.

### 9.1 How to approve

1. Open the run on GitHub:
   - juniper-ml v0.4.1: <https://github.com/pcalnon/juniper-ml/actions/runs/25089943338>
   - juniper-observability v0.1.1a: <https://github.com/pcalnon/juniper-ml/actions/runs/25089949911>
2. Click **Review deployments**.
3. Tick the `pypi` environment checkbox.
4. (Optional) Add an approval comment.
5. Click **Approve and deploy**.

Each run requires its own approval — they are independent jobs in
independent runs.

### 9.2 What to do *before* approving

- Verify TestPyPI (§8.1).
- Optionally do the install smoke test (§8.2).
- Read the diff one more time: `git -C juniper-ml show v0.4.1` and
  `git -C juniper-ml show juniper-observability-v0.1.1a` (the latter
  shows the same commit; the diff is the same release commit).

### 9.3 What happens after approval

The `Publish to PyPI` job:

- Downloads the build artifacts from the `Build and Validate` job.
- Runs `pypa/gh-action-pypi-publish` with `verbose: true` (for the
  observability workflow) targeting `https://upload.pypi.org/legacy/`.
- Uses the OIDC token minted from the `pypi` environment.

Assuming the trusted publisher is correctly registered on PyPI (§11),
the upload will succeed and the artifacts will appear at:

- <https://pypi.org/project/juniper-ml/0.4.1/>
- <https://pypi.org/project/juniper-observability/0.1.1a0/>

> **Gotcha — `gh` CLI does not expose deployment approval.** The
> approval action is **only** available through the web UI or the
> REST `POST /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments`
> endpoint. There is no `gh deployment review` subcommand at the time
> of writing. Plan for that in any automation.

---

## 10. Post-publish verification

After both PyPI promotions complete:

```bash
# Final state of both runs
gh run view 25089943338 --repo pcalnon/juniper-ml
gh run view 25089949911 --repo pcalnon/juniper-ml
# Expect: ✓ on every job for both runs.

# PyPI metadata
curl -sS https://pypi.org/pypi/juniper-ml/0.4.1/json | jq -r '.info.version, .info.name'
curl -sS https://pypi.org/pypi/juniper-observability/0.1.1a0/json | jq -r '.info.version, .info.name'

# Install in a throwaway venv
python -m venv /tmp/jm_v041 && source /tmp/jm_v041/bin/activate
pip install --upgrade juniper-ml==0.4.1
python -c "import importlib.metadata as m; print(m.version('juniper-ml'))───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
❯"

deactivate && python -m venv /tmp/jo_v011a && source /tmp/jo_v011a/bin/activate
pip install --pre juniper-observability==0.1.1a
python -c "import juniper_observability; print(juniper_observability.__version__)"
```

Cross-check that:

- The pyproject version in the tag commit matches the version on PyPI.
  (juniper-observability: `0.1.1a` on disk → `0.1.1a0` on PyPI; this
  is **expected normalization**, not a bug.)
- The GitHub release page reflects the published assets and looks
  correct externally.
- Dependabot (`.github/dependabot.yml` runs weekly on `pip`) will pick
  up future bumps automatically.

---

## 11. Trusted-publisher prerequisite (one-time)

This is the configuration that, when wrong, caused the original
`400 Bad Request` failures on `0.1.0a0` / `0.1.0a2`.

### 11.1 What "trusted publisher" means

PyPI / TestPyPI accept uploads authenticated via OIDC tokens minted
by GitHub Actions. The mapping is configured **per project on the
PyPI side**, binding:

- `Owner` (`pcalnon`)
- `Repository name` (`juniper-ml`)
- `Workflow filename` (`publish-observability.yml`)
- `Environment name` (`testpypi` or `pypi`)

…to a specific PyPI project name. **The project name is the field
people get wrong**: if you register the publisher on the existing
`juniper-ml` project, the OIDC token authorizes uploads of *that*
project — which is not what `publish-observability.yml` is doing.

### 11.2 For a *new* project that doesn't yet exist on PyPI

You must register a **Pending Publisher**, not a regular publisher.
The "Add a pending publisher" form lets you specify a project name
that does not exist yet; the publisher is bound to the project on
the **first successful upload** and the project is auto-created.

Steps for `juniper-observability` (do this **once on each index**):

1. TestPyPI: go to <https://test.pypi.org/manage/account/publishing/>.
2. Scroll to **Add a pending publisher**.
3. Fill in:
   - PyPI Project Name: `juniper-observability`
   - Owner: `pcalnon`
   - Repository name: `juniper-ml`
   - Workflow filename: `publish-observability.yml`
   - Environment name: `testpypi`
4. Submit.
5. Repeat the same on PyPI at <https://pypi.org/manage/account/publishing/>
   with environment name `pypi`.

### 11.3 Verifying the publisher is correctly bound

After the first successful upload, the pending publisher graduates
to a regular publisher attached to the project. To verify:

1. Go to <https://test.pypi.org/manage/project/juniper-observability/settings/publishing/>.
2. The publisher should appear under "GitHub" with the four fields above.

If the upload fails with `400 Bad Request`:

- Check `verbose: true` is set on the `pypa/gh-action-pypi-publish`
  step — without it, the response body (which contains the actual
  reason: project name mismatch, file already exists, invalid
  metadata, etc.) is hidden.
- The most common causes are:
  - Pending publisher registered against a **different project name**
    than the package's `[project] name`.
  - Pending publisher registered against a **different environment**
    than the workflow uses.
  - Project name typo (e.g. trailing whitespace, case mismatch).

### 11.4 Why `verbose: true` matters

The default `pypa/gh-action-pypi-publish` step swallows the upstream
response body. With `verbose: true`, the action prints the full HTTP
response, which is the only signal that distinguishes "wrong
publisher" from "version already exists" from "metadata invalid".
This release added `verbose: true` to both upload steps in
`publish-observability.yml`. Replicate this in any future publish
workflow.

---

## 12. Gotchas and lessons learned

| # | Gotcha | Mitigation |
|---|---|---|
| G1 | `0.1.1a` normalizes to `0.1.1a0` on upload. | Document the normalization in the changelog and release notes; never use the unnormalized form in user-facing comparisons. Prefer `0.1.1a0` going forward to avoid the cognitive friction. |
| G2 | `juniper-ml`'s `publish.yml` fires on **any** release, including the sibling package's release, causing a duplicate (and failing) upload. | Add a tag-pattern filter or job-level `if:` guard. See §7.4. |
| G3 | TestPyPI lacks transitive dependencies, so install verification needs `--extra-index-url https://pypi.org/simple/`. | Already present in `publish-observability.yml`. Worth keeping. |
| G4 | `juniper-observability` has **two** version strings (`pyproject.toml` and `_version.py`). | Until they are unified (e.g. via `setuptools-scm` or `importlib.metadata`), the bump procedure must touch both. A future task: consolidate. |
| G5 | The `pypi` environment approval gate is invisible from `gh run list` — the run shows as `in_progress` but the relevant job shows `status=waiting`. | Inspect with `gh api repos/.../actions/runs/<id>/jobs --jq '.jobs[] | {name,status}'`. |
| G6 | Branch protection on `main` requires bypass permission for direct pushes. | Use a PR if you do not have bypass. |
| G7 | A stale uncommitted file in the working tree (`bla`) almost got swept into the release commit if `git add -A` had been used. | Always stage release files by name; never use `git add -A`/`git add .` on release commits. |
| G8 | `gh` CLI cannot approve a deployment — only the web UI or REST API can. | Plan for that; do not assume `gh deployment review` exists. |
| G9 | Trusted publisher errors return only `400 Bad Request` without `verbose: true`. | Always set `verbose: true` on `pypa/gh-action-pypi-publish` steps. |
| G10 | `Pending Publisher` is required for *new* projects; a regular publisher under a *different existing* project does not work. | See §11. |

---

## 13. Future improvements

In rough priority order:

1. **Filter `publish.yml`** to only fire for `v*` tags (juniper-ml's
   own namespace) — eliminates the duplicate failing run described
   in §7.
2. **Unify the `juniper-observability` version source** so that
   `pyproject.toml` and `_version.py` cannot drift. The simplest
   approach is to read it from package metadata at runtime:

   ```python
   # juniper_observability/_version.py
   from importlib.metadata import version, PackageNotFoundError
   try:
       __version__ = version("juniper-observability")
   except PackageNotFoundError:
       __version__ = "0.0.0+local"
   ```

3. **Wire `juniper-observability` into `juniper-ml[all]`** once the
   alpha graduates. Until then, document explicitly that the meta-package
   does **not** install it.
4. **Capture this walkthrough as a template** under
   `notes/templates/` so the next sibling-package release follows the
   same shape.
5. **Consider `attestations: true`** on the `pypa/gh-action-pypi-publish`
   step. PEP 740 / attestations are now standard on PyPI; opting in
   adds signed provenance to the index.

---

## Appendix A — Verbatim command transcript

The exact commands run (in order) for this release. These are the
commands a future operator can re-run with new versions to repeat
the process.

```bash
# 1. Bump versions
sed -i 's/^version = "0.4.0"/version = "0.4.1"/' \
  juniper-ml/pyproject.toml
sed -i 's/^version = "0.1.0a2"/version = "0.1.1a"/' \
  juniper-ml/juniper-observability/pyproject.toml
sed -i 's/^__version__ = "0.1.0a0"/__version__ = "0.1.1a"/' \
  juniper-ml/juniper-observability/juniper_observability/_version.py

# 2. Update changelogs (manual edit — see §4)

# 3. Commit + push
git -C juniper-ml add CHANGELOG.md pyproject.toml \
  juniper-observability/CHANGELOG.md \
  juniper-observability/pyproject.toml \
  juniper-observability/juniper_observability/_version.py
git -C juniper-ml commit -m "release: juniper-ml v0.4.1 + juniper-observability v0.1.1a"
git -C juniper-ml push origin main

# 4. Create releases
gh release create v0.4.1 \
  --repo pcalnon/juniper-ml \
  --target main \
  --title "v0.4.1 — juniper-observability companion + publish workflow" \
  --notes-file release-notes-juniper-ml-v0.4.1.md

gh release create juniper-observability-v0.1.1a \
  --repo pcalnon/juniper-ml \
  --target main \
  --prerelease \
  --title "juniper-observability v0.1.1a — first publishable alpha" \
  --notes-file release-notes-juniper-observability-v0.1.1a.md

# 5. Monitor
gh run list --repo pcalnon/juniper-ml --limit 5
gh api repos/pcalnon/juniper-ml/actions/runs/<RUN_ID>/jobs \
  --jq '.jobs[] | {name, status, conclusion}'

# 6. Approve PyPI promotion (web UI only)
open "https://github.com/pcalnon/juniper-ml/actions/runs/<RUN_ID>"

# 7. Verify
curl -sS https://pypi.org/pypi/juniper-ml/0.4.1/json | jq .info.version
curl -sS https://pypi.org/pypi/juniper-observability/0.1.1a0/json | jq .info.version
```
