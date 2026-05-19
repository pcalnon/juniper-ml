# `juniper-doc-tools` PyPI Migration Plan

**Date:** 2026-05-18
**Author:** Paul Calnon (drafted by Claude)
**Status:** Proposed
**Estimated effort:** 5–7 working days, single owner

---

## 1. Motivation

The Juniper ecosystem has three coexisting layouts for the doc-link validator
across eight repos, and each has its own failure mode:

| Pattern | Repos | Failure mode |
|---|---|---|
| Standalone copy | `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-data-client` | Drifts from the canonical source over time |
| Symlink to a sibling | `juniper-canopy`, `juniper-ml` (own scripts/ → util/) | Broken in CI — siblings aren't checked out |
| Renamed-without-replacement | `juniper-cascor`, `juniper-data` | File missing entirely |

The events of **2026-05-18** demonstrated this concretely: three repos
(`juniper-canopy`, `juniper-cascor`, `juniper-data`) hit the *same*
`python: can't open file '.../scripts/check_doc_links.py'` CI failure within
~30 minutes of each other, all stemming from one engineer's attempt to
centralize the validator without a working substrate.

The immediate fix (PRs #267, #286, #265, #112) is the **standalone-copy**
pattern across all four affected places. This restores parity but reinstates
the drift problem.

The **`juniper-doc-tools` PyPI package** proposed here is the long-term answer:
a single source of truth, no symlinks, no copies, no drift. Each repo's CI
becomes a one-line `pip install` and a console-script invocation.

## 2. Goals & non-goals

### Goals

1. **Single source of truth** for the doc-link validator (and any related
   doc-quality tooling: ecosystem-root classification, cross-repo policy,
   future markdown lint extensions).
2. **Reproducible installs in CI** without checking out sibling repos.
3. **Backward-compatible CLI surface** — same `--exclude`, `--cross-repo`
   flags as today's `python scripts/check_doc_links.py`.
4. **Versioned releases on PyPI** so each repo can pin a specific behavior
   if a future major bump needs gradual rollout.
5. **Drift detection** as a CI guard rail — if a repo pins an out-of-date
   minor version for too long, surface a warning (no hard fail).

### Non-goals

1. **Not** rewriting the validator's link-classification logic. v0.7.0 ships
   *as-is* in the first PyPI release.
2. **Not** consolidating other shared Python utilities (worktree management,
   reap-pytest-orphans, etc.) into the same package. Those have repo-shell
   dependencies that complicate a Python-package surface; out of scope.
3. **Not** removing the inline scripts immediately. The new console-script
   coexists with the standalone copies for one minor-version cycle, then
   the copies are deleted in a second wave.

## 3. Package design

### 3.1 Name and location

- **Distribution name (PyPI):** `juniper-doc-tools`
- **Import name (Python):** `juniper_doc_tools`
- **Source location:** new sibling directory in the `juniper-ml` repo:
  `juniper-doc-tools/`, mirroring the existing `juniper-observability/`
  precedent (separate `pyproject.toml`, separate CI workflow, separate
  release workflow, separate `CHANGELOG.md`).

This piggy-backs on the established polyrepo-companion pattern and keeps
`juniper-ml` as the canonical home for cross-cutting tooling.

### 3.2 Layout

```
juniper-ml/
  juniper-doc-tools/
    pyproject.toml
    README.md
    CHANGELOG.md
    LICENSE                       # MIT, matches the rest of the ecosystem
    src/
      juniper_doc_tools/
        __init__.py               # exposes __version__
        check_doc_links.py        # the validator, imported from current util/
        _ecosystem.py             # _ECOSYSTEM_REPOS, _ECOSYSTEM_ROOT_ITEMS
        cli.py                    # argparse + main() console-script entry point
    tests/
      test_check_doc_links.py     # ported from juniper-ml/tests/
      test_workflow_script_paths.py  # adapted to package layout
```

### 3.3 `pyproject.toml` essentials

```toml
[project]
name = "juniper-doc-tools"
version = "0.1.0"          # see §6 for versioning policy
requires-python = ">=3.12"
dependencies = []          # stdlib only; the validator already is
license = { text = "MIT" }

[project.scripts]
juniper-check-doc-links = "juniper_doc_tools.cli:main"

[project.urls]
Homepage = "https://github.com/pcalnon/juniper-ml"
Issues = "https://github.com/pcalnon/juniper-ml/issues"
```

`requires-python = ">=3.12"` matches the floor of every consumer repo. No
runtime dependencies are required — the validator is stdlib-only.

### 3.4 CLI compatibility

The console script `juniper-check-doc-links` accepts **all** the flags the
current `scripts/check_doc_links.py` accepts:

```
juniper-check-doc-links \
  --exclude templates --exclude history --exclude legacy \
  --exclude pull_requests --exclude releases --exclude analysis \
  --exclude fixes --exclude development --exclude CHANGELOG.md \
  --cross-repo skip
```

This is the only change CI workflows need: replace
`python scripts/check_doc_links.py` with `juniper-check-doc-links`.

### 3.5 Library API

```python
from juniper_doc_tools import validate_directory, validate_file, ValidationResult

result: ValidationResult = validate_directory(
    Path("."),
    exclude={"templates", "history"},
    cross_repo_mode="skip",
)
if not result.ok:
    for error in result.errors:
        print(error)
```

`ValidationResult` is a small dataclass with `ok`, `errors`,
`cross_repo_skipped`, `scanned_files`. This lets dashboards (e.g.,
juniper-canopy's docs panel — if we ever add one) consume validation
output programmatically.

## 4. Migration sequence

The sequence below assumes the **immediate fix** (PRs #267, #286, #265, #112)
has already landed and CI is green across all 4 affected repos.

### Wave 0 — Package scaffold (1 day)

1. Branch `feat/juniper-doc-tools-scaffold` in `juniper-ml`.
2. Create `juniper-doc-tools/` with the layout in §3.2.
3. Lift `juniper-ml/util/check_doc_links.py` v0.7.0 verbatim into
   `juniper_doc_tools/check_doc_links.py`. Extract `_ECOSYSTEM_REPOS` and
   `_ECOSYSTEM_ROOT_ITEMS` into `_ecosystem.py` (so they can be reused by
   future tools).
4. Add `tests/test_check_doc_links.py` (ported from existing test suite).
5. Add `juniper-doc-tools-ci.yml` workflow: pre-commit + pytest matrix
   (3.12/3.13/3.14). This is `juniper-ml`'s `ci.yml` style, scoped to
   the subdir.
6. Add `publish-juniper-doc-tools.yml` workflow: trigger on tag matching
   `juniper-doc-tools-v*`, OIDC trusted publish to TestPyPI → PyPI.
   Mirrors the existing `publish-observability.yml` exactly.
7. PR review + merge.

**Exit criterion:** `juniper-doc-tools-ci.yml` green; package builds with
`python -m build` from inside `juniper-doc-tools/`.

### Wave 1 — First release (1 day)

1. Cut tag `juniper-doc-tools-v0.1.0` from `main`.
2. Verify TestPyPI install + smoke test:
   ```
   pip install --index-url https://test.pypi.org/simple/ juniper-doc-tools==0.1.0
   juniper-check-doc-links --help
   ```
3. Promote to PyPI (automatic via publish workflow).
4. Pin a `juniper-ml` requirement: `juniper-doc-tools>=0.1.0,<0.2.0` in
   `juniper-ml/pyproject.toml` under a new `[project.optional-dependencies]`
   group `doc-tools`.

**Exit criterion:** `pip install juniper-doc-tools` works from a fresh
GitHub Actions runner.

### Wave 2 — Per-repo CI swap (2–3 days, one PR per repo)

For **each** consuming repo (in the order: `juniper-ml`, `juniper-canopy`,
`juniper-cascor`, `juniper-data`, then the three with standalone copies):

1. Update the repo's `.github/workflows/ci.yml` doc-links job:
   ```yaml
   - name: Install juniper-doc-tools
     run: pip install "juniper-doc-tools>=0.1.0,<0.2.0"
   - name: Validate Documentation Links
     run: |
       juniper-check-doc-links \
         --exclude templates --exclude history --exclude legacy \
         --exclude pull_requests --exclude releases --exclude analysis \
         --exclude fixes --exclude development --exclude CHANGELOG.md \
         --cross-repo skip
   ```
2. **Do NOT** delete `scripts/check_doc_links.py` yet. The standalone copy
   stays in place as the local-development fallback (for engineers running
   pre-commit hooks without the PyPI package installed).
3. Open PR, observe CI green, merge.

**Exit criterion:** all 8 repos' Documentation Links jobs use the PyPI
package; no repo invokes `python scripts/check_doc_links.py` from CI.

### Wave 3 — Pre-commit migration (1 day, optional)

If we add the doc-link validator as a pre-commit hook anywhere (not done
today, but proposed for `juniper-ml`), the hook config invokes the same
console script.

```yaml
- repo: local
  hooks:
    - id: juniper-check-doc-links
      name: Validate documentation links
      entry: juniper-check-doc-links
      language: system
      args: ["--cross-repo", "skip"]
      pass_filenames: false
      files: \.md$
```

**Exit criterion:** developers can run the hook locally after
`pip install juniper-doc-tools` in their venv.

### Wave 4 — Delete inline copies (1 day)

Once Wave 2 has been on `main` for **two weeks** across all repos and no
CI regressions have surfaced:

1. Delete `scripts/check_doc_links.py` from every repo.
2. Delete `scripts/check_doc_links-ORIG.py` from `juniper-cascor` and
   `juniper-data` (the orphaned backups from the 2026-05-18 incident).
3. Delete `util/check_doc_links_cascor-OLD.bash` from `juniper-cascor`.
4. Keep `util/check_doc_links.py` in `juniper-ml` *as a symlink* to
   `juniper-doc-tools/src/juniper_doc_tools/check_doc_links.py`, so the
   AGENTS.md-documented entry point still resolves.

**Exit criterion:** `grep -r check_doc_links scripts/` returns nothing
in 7 of 8 repos; `juniper-ml` keeps only the symlinked entry point.

## 5. Drift-detection guard rail

Add a new lint check (in `juniper-ml/tests/test_workflow_script_paths.py`,
the lint test that shipped with PR #267) — or a new test alongside it —
that asserts each consumer repo's CI pins a `juniper-doc-tools` version
in the supported window:

```python
def test_consumer_repos_pin_supported_doc_tools_version(self):
    """Cross-repo drift check: read each consumer's ci.yml and confirm
    the pinned ``juniper-doc-tools>=X,<Y`` range is still supported.

    A range that falls outside the supported window (more than 2 minor
    versions behind current) gets surfaced as a soft warning, not a
    hard fail. Hard fail only if the pin is for a version that has been
    yanked or pre-1.0."""
```

This test runs in the weekly `docs-full-check.yml` workflow (already
clones all sibling repos), so it gets cross-repo visibility without
needing each repo to opt in individually.

## 6. Versioning policy

- **MAJOR (1.x → 2.x):** breaking CLI flag changes, breaking output
  format changes. Coordinated across all 8 repos in a single sweep.
- **MINOR (0.x → 0.x+1):** new flags, new validation rules, new
  cross-repo classifications. Consumers pin `>=X.Y,<X.Y+1` initially,
  then widen the upper bound when ready.
- **PATCH (0.x.0 → 0.x.1):** bug fixes, no behavior changes. Consumers
  can pin `>=X.Y.0` and pick up patches automatically.

First public release is **`0.1.0`** to signal that the surface is stable
but breaking changes are still on the table; we aim for **`1.0.0`** once
all 8 repos have been on `>=0.x` for 3 months without a regression.

## 7. Rollback plan

If any wave goes wrong:

- **Wave 1 (initial release):** yank the version on PyPI, revert the
  `juniper-ml` pin, no consumers are affected yet.
- **Wave 2 (CI swap):** revert the consumer's `ci.yml` change. The
  standalone copy of `scripts/check_doc_links.py` is still in place
  (we haven't done Wave 4 yet), so the old invocation works.
- **Wave 4 (delete copies):** the deletion PR is per-repo; only roll
  back the affected repo. The PyPI package keeps working for the rest.

This is the value of keeping the standalone copies for one cycle:
**every wave is reversible without coordinating across 8 repos.**

## 8. Open questions / decisions still needed

1. **Test framework**: stay on `unittest` (matches current juniper-ml
   tests) or switch to `pytest` (matches juniper-observability)?
   Recommendation: `unittest`, no new test dependency.
2. **Console script name**: `juniper-check-doc-links` (verbose) vs.
   `jdoc-check` (terse)? Recommendation: verbose — discoverable from
   `pip show juniper-doc-tools` output, avoids name collisions.
3. **Module form support**: should `python -m juniper_doc_tools` also
   work alongside the console script? Cheap to add; recommend yes.
4. **Should the v0.7.0 ecosystem-root classification be a default-on
   feature, or behind a flag (`--allow-ecosystem-root`)?** This PR's
   immediate fix makes it default-on. The PyPI release could keep it
   default-on for parity, or expose the flag for repos that want
   stricter behavior. Recommendation: default-on, no flag — same
   behavior as today's v0.7.0.
5. **CI matrix**: should `juniper-doc-tools` itself be tested against
   each Juniper repo's docs in CI (downstream-consumer integration)?
   Recommendation: yes, but only in the weekly cross-repo workflow
   (`docs-full-check.yml`), not per-PR.

## 9. Effort estimate

| Wave | Owner-days |
|---|---|
| Wave 0 — Scaffold | 1.0 |
| Wave 1 — First release | 0.5 |
| Wave 2 — Per-repo CI swap (8 repos × 0.25d) | 2.0 |
| Wave 3 — Pre-commit migration | 0.5 (optional) |
| Wave 4 — Delete inline copies | 0.5 |
| Drift-detection test (§5) | 0.5 |
| Buffer / review cycles | 1.0 |
| **Total** | **5.5 working days** |

## 10. Related references

- **Immediate fix PRs** (must land before this plan starts):
  - juniper-ml#267 (validator v0.7.0 + workflow-path lint test)
  - juniper-canopy#286 (standalone copy)
  - juniper-cascor#265 (standalone copy)
  - juniper-data#112 (standalone copy)
- **Precedent for the package-in-subdir pattern:** existing
  `juniper-ml/juniper-observability/` subpackage, published via
  `.github/workflows/publish-observability.yml`.
- **Original incident root cause:** see commit `8729e78` in
  juniper-cascor and `3d2c15d` in juniper-data — both renamed
  `scripts/check_doc_links.py` → `scripts/check_doc_links-ORIG.py`
  without restoring the entry point.
