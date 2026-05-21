# Release Walkthrough — juniper-ml v0.5.0

**Date**: 2026-05-21
**Author**: Paul Calnon (with Claude Opus 4.7)
**Scope**: First release that ships the expanded extras surface
(`[servers]`, `[tools]`, the expanded `[all]`), the `juniper-ci-tools`
pin, and the back-compat `[doc-tools]` alias. Companion to the
`v0.4.1` walkthrough.

This document is the runbook for **cutting and publishing
`juniper-ml` v0.5.0**. The companion sibling packages
(`juniper-observability`, `juniper-doc-tools`, `juniper-ci-tools`) are
**not** re-cut by this walkthrough — they ship independently under
their own tag patterns and have already published the versions
`juniper-ml[tools]` pins against.

---

## 0. Table of contents

- [1. Preconditions](#1-preconditions)
- [2. Version-bump strategy](#2-version-bump-strategy)
- [3. Pre-tag PRs that should have already merged](#3-pre-tag-prs-that-should-have-already-merged)
- [4. CHANGELOG promotion](#4-changelog-promotion)
- [5. Cut the GitHub release](#5-cut-the-github-release)
- [6. TestPyPI + PyPI flow](#6-testpypi--pypi-flow)
- [7. The new extras-resolution verification step](#7-the-new-extras-resolution-verification-step)
- [8. Post-publish verification](#8-post-publish-verification)
- [9. Rollback options](#9-rollback-options)
- [10. Gotchas specific to a meta-package release](#10-gotchas-specific-to-a-meta-package-release)

---

## 1. Preconditions

| Precondition | Why it matters | Verification |
|---|---|---|
| Working tree clean on `main` | Mixed local edits will get caught up in the release commit if any is needed. | `git status --short` returns no output. |
| `gh` CLI authenticated | Needed for `gh release create` and run inspection. | `gh auth status` reports the GitHub.com token. |
| `juniper-ml/pyproject.toml` version is `0.5.0` | This is the version that will be tagged and published. | `grep '^version' pyproject.toml` |
| All `[tools]`-pinned packages are already on PyPI | The TestPyPI verification step installs `juniper-ml[clients]`, but the `[tools]` and `[servers]` resolutions are only validated post-publish. The pinned versions must exist or the resolver will fall back / fail. | `curl -sf https://pypi.org/pypi/juniper-ci-tools/json | jq .info.version` (and similarly for `-doc-tools`, `-observability`, `-canopy`, `-cascor`, `-data`, `-data-client`, `-cascor-client`, `-cascor-worker`). |
| TestPyPI / PyPI trusted publishers for `juniper-ml` already exist | Established in the v0.4.1 release. | Existence of past `juniper-ml` releases on PyPI. |
| GitHub Actions environments `testpypi` and `pypi` exist | `publish.yml` references both. | <https://github.com/pcalnon/juniper-ml/settings/environments>. |
| `tests/test_pyproject_extras.py` passes locally | The extras contract is what this release ships; if the lint fails locally, the workflow's TestPyPI install will also fail. | `python3 -m unittest tests/test_pyproject_extras.py`. |

> **Critical for v0.5.0 specifically**: the extras-resolution
> verification step added in this release (see §7) means the publish
> workflow will now refuse to promote a build with a broken extras
> declaration even on TestPyPI. This is the intended behavior — but it
> means a release that would have silently succeeded under the v0.4.1
> workflow can now fail at TestPyPI verify if the extras are broken.

---

## 2. Version-bump strategy

| Package | Old version | New version | Type of bump |
|---|---|---|---|
| `juniper-ml` | `0.4.1` | `0.5.0` | Minor (new optional dependency surface) |

### Why a minor bump

`juniper-ml` v0.5.0 introduces two new extras (`[servers]`, `[tools]`)
and expands `[all]` to be a strict superset of the v0.4.1 `[all]`. No
existing install command is broken. Per SemVer, that's a minor bump.

The version bump itself **already merged** in juniper-ml#295. This
walkthrough does not need to re-bump.

---

## 3. Pre-tag PRs that should have already merged

Before tagging `v0.5.0`, the following PRs should be on `main`:

| PR | Title | Purpose |
|---|---|---|
| #295 | feat(pyproject): add [servers] + [tools] extras; bump to 0.5.0 | Functional change being shipped. |
| #299 | chore: pre-0.5.0 docs polish + tests/test_pyproject_extras.py | Doc consistency + extras-contract lint. |
| #301 | docs: meta-package extras requirements source doc + install-size note | JR-ID groundwork + install-size advisory. |
| _this PR_ | chore: release v0.5.0 prep | `publish.yml` extras-resolution verify step + CHANGELOG promotion + this runbook. |

Verify:

```bash
git log --oneline main | grep -E "#295|#299|#301"
```

---

## 4. CHANGELOG promotion

Before tagging, promote `[Unreleased]` to `[0.5.0] - 2026-05-21` in
`CHANGELOG.md`. This is included in the release-prep PR that ships
this runbook; verify on `main` after merge:

```bash
grep -n "^## \[0.5.0\]" CHANGELOG.md
# Expected: line 8 (or wherever the [Unreleased] heading was)
```

The promotion preserves an empty `[Unreleased]` block above `[0.5.0]`
so subsequent PRs have a place to record changes against the next
release.

---

## 5. Cut the GitHub release

```bash
# From a clean main checkout, sanity-checked against pyproject:
VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
[ "$VERSION" = "0.5.0" ] || { echo "Version mismatch: pyproject says $VERSION"; exit 1; }

# Extract the [0.5.0] CHANGELOG section as the release body
awk '/^## \[0.5.0\]/{flag=1; next} /^## \[/{flag=0} flag' CHANGELOG.md > /tmp/release-notes-0.5.0.md

gh release create "v${VERSION}" \
  --title "juniper-ml v${VERSION} — servers + tools extras" \
  --notes-file /tmp/release-notes-0.5.0.md \
  --target main
```

The release event fires `.github/workflows/publish.yml`. Monitor:

```bash
gh run list --workflow publish.yml --limit 3
gh run watch <run-id>
```

---

## 6. TestPyPI + PyPI flow

The publish workflow runs in three stages:

1. **Build and Validate** — checks out the tag, runs `python -m build`,
   `twine check dist/*`, uploads the `dist/` artifact.
2. **TestPyPI: publish + verify** — uploads to TestPyPI via OIDC,
   then runs the new two-step verification described in §7.
3. **PyPI: publish** — gated by the `pypi` GitHub Actions environment
   approval (if configured) and the TestPyPI stage's success.

If stage 2 fails (the most likely failure mode for v0.5.0 — see §7),
the PyPI promotion does not happen. The release can be retried with
`gh workflow run publish.yml --ref v0.5.0` after fixing the underlying
issue.

---

## 7. The new extras-resolution verification step

`publish.yml` v0.5.0 prep PR added a second `pip install` in the
TestPyPI verify step:

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "juniper-ml[clients]==${VERSION}"
python -c "import juniper_data_client, juniper_cascor_client; ..."
```

**Why `[clients]` specifically:**

- It's the lightest non-empty extra (just `juniper-data-client` +
  `juniper-cascor-client`; no torch, no service distributions, no
  observability stack).
- Both dependencies are already on production PyPI, so the
  `--extra-index-url` is what actually serves them; TestPyPI only
  serves the `juniper-ml` wheel itself.
- It walks the full PEP 517 resolver path against the published
  TestPyPI metadata, so a broken `[clients]` (or, transitively, a
  broken `[all]` recursive reference) shows up here.

**What this catches vs. what it doesn't:**

- ✅ Misnamed extra (`[client]` vs `[clients]`).
- ✅ `[all]` missing a self-referenced subextra.
- ✅ Removed package from `[clients]` while a downstream caller still
  expects it.
- ❌ A broken `[servers]` or `[tools]` (those resolve large dependency
  trees that would slow the workflow too much; rely on the
  `tests/test_pyproject_extras.py` schema lint for those).

**If this step fails:**

1. Check the resolver error against `tests/test_pyproject_extras.py`'s
   `EXPECTED_EXTRAS` table.
2. The most likely cause is a typo in `pyproject.toml` that the schema
   lint missed (e.g. wrong PyPI name). Fix on a hotfix branch, bump
   the version to `0.5.1`, repeat the release flow.
3. **Do not** `gh release delete` and re-cut on the same tag; the
   TestPyPI version is immutable once uploaded.

---

## 8. Post-publish verification

After PyPI promotion succeeds:

```bash
# Confirm version is on PyPI
curl -sf https://pypi.org/pypi/juniper-ml/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'])"

# Confirm all six extras are advertised
curl -sf https://pypi.org/pypi/juniper-ml/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sorted([r for r in d['info']['requires_dist'] if 'extra ==' in r]))"

# Install verification on a fresh venv (no TestPyPI mixing)
python3 -m venv /tmp/v05-verify && source /tmp/v05-verify/bin/activate
pip install juniper-ml==0.5.0
pip install "juniper-ml[clients]==0.5.0"
pip install "juniper-ml[tools]==0.5.0"
pip install "juniper-ml[servers]==0.5.0"
pip install "juniper-ml[all]==0.5.0"      # ~2 GB, allow time
pip list | grep ^juniper
deactivate && rm -rf /tmp/v05-verify
```

Expected `pip list | grep ^juniper` after `[all]`:

```text
juniper-canopy           0.3.x
juniper-cascor           0.3.x
juniper-cascor-client    0.3.x
juniper-cascor-worker    0.3.x
juniper-ci-tools         0.1.x
juniper-data             0.6.x
juniper-data-client      0.4.x
juniper-doc-tools        0.1.x
juniper-ml               0.5.0
juniper-observability    0.2.x
```

---

## 9. Rollback options

A `juniper-ml` version on PyPI cannot be deleted. Options if v0.5.0
ships with a problem:

| Severity | Action |
|---|---|
| Build is unusable (import fails, install always errors) | `pip` admin yank: `pypi-admin yank juniper-ml 0.5.0` via the PyPI web UI under <https://pypi.org/manage/project/juniper-ml/release/0.5.0/>. Yanked versions are still resolvable by explicit `==0.5.0` but disappear from `pip install juniper-ml` (no version specifier). |
| Extras surface is broken but the package itself installs | Fix on a hotfix branch, ship `v0.5.1`. Do **not** yank; the broken extras are recoverable by upgrading. |
| Documentation drift discovered | Patch in `v0.5.1` or later. No yank needed. |
| Wrong package pinned (e.g. wrong child-package minimum version) | Patch in `v0.5.1`. Only yank if the wrong pin causes downstream resolver loops. |

---

## 10. Gotchas specific to a meta-package release

1. **Extras resolution is a publication contract.** Changing the set
   of extras or the packages in an extra is an observable change to
   every external caller. The v0.5.0 expansion of `[all]` is
   technically a strict superset (so non-breaking), but a caller who
   was relying on `[all]` to be small (e.g. in a constrained CI
   environment) will see the install size grow from ~30 MB to ~2 GB.
   The install-size advisory in `docs/QUICK_START.md` (#301) calls
   this out for new users; existing users discover it the first time
   they upgrade.

2. **The recursive `[all]` reference is checked at install time, not
   build time.** `twine check` does not validate that `juniper-ml[all]`
   resolves; that only happens when a real `pip install` walks the
   metadata. Hence §7 step.

3. **TestPyPI doesn't see the production PyPI graph by default.** The
   `--extra-index-url https://pypi.org/simple/` is what lets TestPyPI
   builds resolve their production-PyPI dependencies. Without it, the
   `[clients]` verify step would fail because `juniper-data-client`
   doesn't exist on TestPyPI.

4. **`gh release create` fires `publish.yml` once.** If the release
   was created with the wrong target / wrong tag, deleting the release
   does not unpublish from PyPI. Use `gh workflow run publish.yml
   --ref <tag>` to re-fire against the same tag; the `workflow_dispatch`
   trigger is the escape hatch.

5. **The TestPyPI extras-resolution check uses `[clients]`, not
   `[all]`.** A v0.5.0 release that broke `[servers]` would still
   pass TestPyPI verify and ship. The schema lint
   (`tests/test_pyproject_extras.py`) is the line of defense for that
   class of error and runs every PR.
