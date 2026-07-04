# `juniper-ci-tools` PyPI Migration Plan

**Date:** 2026-05-20
**Author:** Paul Calnon (drafted by Amp)
**Status:** **Complete (2026-05-21)** — Waves 0, 1, 2, 4 merged across all 7 consumer repos; §5.1 + §5.2 drift detection live in `juniper-ml/.github/workflows/docs-full-check.yml`. Wave 3 was skipped per plan (no pre-commit surface). Wave 4 PRs: juniper-ml#298, juniper-cascor-client#56, juniper-cascor-worker#79, juniper-data-client#72, juniper-canopy#306, juniper-data#136, juniper-cascor#290. **Extension series (v0.2.0 + v0.3.0) also shipped 2026-05-21** — same package, same fan-out pattern, two additional lints (`juniper-lint-workflow-paths`, `juniper-lint-agents-md-version`); see §7 below for the PR roll-up. Pattern lessons captured in [`JUNIPER_2026-05-21_JUNIPER-ML_CI-TOOLS-EXTRACTION-PLAYBOOK.md`](JUNIPER_2026-05-21_JUNIPER-ML_CI-TOOLS-EXTRACTION-PLAYBOOK.md).
**Estimated effort:** 3–5 working days, single owner

---

## 1. Motivation

The Juniper ecosystem currently runs **three coexisting variants** of
`scripts/generate_dep_docs.sh` (or `util/generate_dep_docs.sh`) across eight
repos, invoked from each repo's `ci.yml` as the "Generate Dependency
Documentation" CI step:

| Variant | Repos | Conda extraction | YAML validation | Notes |
|---|---|---|---|---|
| **Newest** | `juniper-cascor` | `conda env export` + **awk** | yes | Fixed 2026-05-20 in [cascor#276](https://github.com/pcalnon/juniper-cascor/pull/276) |
| Middle | `juniper-canopy`, `juniper-data`, `juniper-cascor-client`, `juniper-cascor-worker` | `conda env export` + **sed** | yes | Buggy sed range terminator can emit `prefix:` / `variables:` as a YAML key, breaking validation |
| Oldest | `juniper-ml`, `juniper-data-client` | `conda list --explicit` | **no** | Pre-2026-05-20 upgrade entirely |

The cascor 2026-05-20 commit message captures the bug exactly:

> 2026-05-20 fix: switched from the previous `sed -n '/^dependencies:$/,/^[a-z]/{...}'`
> pipeline to awk because the sed range terminator was being emitted as a
> trailing top-level key (`prefix:`, `variables:`) in some setup-miniconda
> configurations, breaking YAML validation.

This is the **same incident class** as the 2026-05-18 doc-link validator
incident (`scripts/check_doc_links.py`): a script copied to N repos, a bug fix
landed in 1, the other N-1 are exposed. The `juniper-doc-tools` PyPI package
solved that class for the doc-link validator; this plan solves it for the
dependency-documentation generator.

## 2. Goals & non-goals

### Goals

1. **Single source of truth** for the dependency-documentation generator,
   with the cascor 2026-05-20 awk fix as the canonical implementation.
2. **Reproducible installs in CI** -- one `pip install` line, no shell-script
   maintenance burden in consumer repos.
3. **Backward-compatible CLI surface** -- the consumer-repo `ci.yml` step
   continues to read `pyproject.toml`, write `conf/requirements_ci.txt` and
   `conf/conda_environment_ci.yaml`, with the same backup-with-timestamp
   semantics.
4. **Versioned releases on PyPI** so each repo can pin a specific behavior
   if a future major bump needs gradual rollout.
5. **Drift detection** as a CI guard rail (plan §5) so future divergence
   between published-version and consumer-pin is surfaced rather than
   silently rotted.

### Non-goals

1. **Not** changing the file layout the script produces. The output paths
   (`conf/requirements_ci.txt`, `conf/conda_environment_ci.yaml`), the
   header-template paths (`notes/JUNIPER_2026-03-11_JUNIPER-ML_PIP-DEPENDENCY-FILE-HEADER.md`,
   `notes/JUNIPER_2026-03-15_JUNIPER-ML_CONDA-DEPENDENCY-FILE-HEADER.md`), and the backup-naming scheme
   are preserved verbatim from the cascor variant.
2. **Not** consolidating other shared CI scripts (e.g. `worktree_*`,
   `requirements_drift_check.py`) into the same package in Wave 0. Those
   are local-dev convenience tools without an incident on file; they can be
   considered for a future release if the playbook continues to pay off.
3. **Not** rewriting the conda extraction logic. The Python implementation
   reproduces the awk pipeline's behavior exactly:
   *"start collecting after `^dependencies:$`, stop before the next line
   that begins with an ASCII letter at column 0, exclusive."*

## 3. Package design

### 3.1 Name and location

- **Distribution name (PyPI):** `juniper-ci-tools`
- **Import name (Python):** `juniper_ci_tools`
- **Source location:** new sibling directory in the `juniper-ml` repo:
  `juniper-ci-tools/`, mirroring `juniper-doc-tools/` and
  `juniper-observability/` (separate `pyproject.toml`, separate CI workflow,
  separate release workflow, separate `CHANGELOG.md`).

### 3.2 Layout

```
juniper-ml/
  juniper-ci-tools/
    pyproject.toml
    README.md
    CHANGELOG.md
    LICENSE
    juniper_ci_tools/
      __init__.py
      __main__.py
      _version.py
      generate_dep_docs.py
      cli.py
    tests/
      __init__.py
      conftest.py
      test_generate_dep_docs.py
      test_cli.py
```

### 3.3 CLI surface

```
juniper-generate-dep-docs [--repo-root PATH] [--conf-dir DIR] [--notes-dir DIR]
                          [--pip-header NAME] [--conda-header NAME]
                          [--pip-filename NAME] [--conda-filename NAME]
                          [--no-conda] [--no-yaml-validation] [--version]
```

All defaults match the legacy bash script's behavior, so the migration in
Wave 2 is a one-line swap in each consumer's `ci.yml`:

```yaml
# before
- name: Generate Dependency Documentation
  run: bash scripts/generate_dep_docs.sh

# after
- name: Install juniper-ci-tools
  run: pip install "juniper-ci-tools>=0.1.0,<0.2.0"
- name: Generate Dependency Documentation
  run: juniper-generate-dep-docs
```

### 3.4 Library API

```python
from juniper_ci_tools import generate_dep_docs, GenerateResult, render_header
```

Exposed for the `juniper-ml` repo's own use and for tests; not advertised
externally in Wave 0.

## 4. Wave plan

Mirroring the doc-tools waves:

### Wave 0 -- Scaffold (this PR)

- Add `juniper-ci-tools/` subdirectory with full package + tests.
- Add `.github/workflows/ci-ci-tools.yml` to run pytest on every PR
  touching the package.
- Add `.github/workflows/publish-ci-tools.yml` triggered by
  `juniper-ci-tools-v*` tags.
- Add this plan doc.
- Update `juniper-ml/AGENTS.md` to mention the new package.

**Exit criteria:** PR merges to `main` with CI green.

### Wave 1 -- First publish

- Tag `juniper-ci-tools-v0.1.0`.
- Publish workflow runs TestPyPI -> PyPI via OIDC trusted publishing
  (re-uses the doc-tools / observability environments).
- Add `[ci-tools]` optional dependency group to `juniper-ml/pyproject.toml`
  pinning `juniper-ci-tools>=0.1.0,<0.2.0`.

**Exit criteria:** `pip install juniper-ci-tools==0.1.0` works from a clean
venv; `juniper-generate-dep-docs --version` prints `0.1.0`.

### Wave 2 -- Per-repo CI swap

Eight PRs (one per repo) replacing the inline `bash scripts/generate_dep_docs.sh`
step with the pip-install + console-script invocation shown in §3.3.

Order (least risky first):
1. `juniper-ml` (use `util/generate_dep_docs.sh` invocation as the proof PR)
2. `juniper-cascor-client`
3. `juniper-cascor-worker`
4. `juniper-data-client`
5. `juniper-canopy`
6. `juniper-data`
7. `juniper-cascor`
8. (`juniper-deploy` does not have this step; skip)

**Exit criteria:** each repo's CI green with the new step; generated
`conf/requirements_ci.txt` and `conf/conda_environment_ci.yaml` diff-clean
versus the previous run (modulo expected timestamp/version changes).

### Wave 3 -- (none planned)

The legacy bash script has no pre-commit-hook surface (unlike doc-tools); no
Wave 3 equivalent. Skip.

### Wave 4 -- Delete inline copies

Eight PRs deleting `scripts/generate_dep_docs.sh` / `util/generate_dep_docs.sh`
from each consumer repo after Wave 2 has soaked for at least one cycle
(or sooner if the proof PRs all pass on the first try, mirroring the
doc-tools Wave 4 early-cutover decision).

### §5 -- Drift detection guard rails

Two lints, analogous to those added for doc-tools after the migration:

#### §5.1 Consumer pin lint (in `juniper-ml/tests/`)

`tests/test_ci_tools_drift.py`: for each consumer repo cloned into the
`docs-full-check` workflow, extract the `juniper-ci-tools>=X,<Y` pin from
its `ci.yml`, compare against the current version in
`juniper-ml/juniper-ci-tools/pyproject.toml`, soft-warn on > 2 minors of
lag, hard-fail when the upper bound excludes the current version. Mirrors
`tests/test_doc_tools_drift.py`.

#### §5.2 Weekly downstream-consumer integration step (in `docs-full-check.yml`)

After cloning each consumer repo, run their `ci.yml`'s "Generate Dependency
Documentation" step locally against `pip install juniper-ci-tools` from the
juniper-ml `dist/`. Asserts that the package wired into the consumer's
CI behavior remains identical to what the consumer would get from PyPI.

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Python-port behavior diverges from the bash script for some setup-miniconda configuration we didn't test | Wave 2 first PR (`juniper-ml` itself) runs the *new* CLI side-by-side with the *old* bash script on the same conda env and asserts byte-identical output (modulo timestamps); only after that gate passes do consumer PRs roll out |
| Subprocess calls to `pip` and `conda` differ across CI runners | Tests stub both via `_pip_list_freeze` / `_conda_env_export` indirection so unit tests are deterministic; CI integration via the cascor consumer PR exercises the real subprocess path |
| Adding PyYAML as a runtime dep slows down CI install | Negligible (PyYAML is pre-installed in setup-python's wheel cache); already a transitive dep across multiple Juniper packages |
| Pre-fix consumers (canopy/data/cascor-client/cascor-worker) currently still emit invalid YAML | Wave 2 migration *is* the fix -- no separate hotfix needed; this is the same approach taken with doc-tools v0.7.0 |

## 6. Open questions

None at scaffold time. Wave 2 will produce a side-by-side diff in the
proof PR; if the diff is non-empty in unexpected ways we'll iterate on
the Python port before rolling out to consumers.

## 7. Extension series (post-2026-05-21)

The same package + fan-out pattern proven by Waves 0–4 has been re-used
twice more on the same day to absorb two unrelated lint scripts that had
drifted into byte-identical copies across the 6 consumer repos. Both
extensions reuse the established workflow verbatim: canonical
implementation lives in juniper-ml's `tests/`; the package extraction
lives under `juniper-ci-tools/`; consumer `util/` copies are deleted in
the fan-out PRs; juniper-ml's own `tests/` files stay as dogfooded
in-process unittests (mirroring how Wave 4 left
`juniper-ml/tests/test_workflow_script_paths.py` untouched).

### v0.2.0 — `juniper-lint-workflow-paths` (2026-05-21)

**Trigger:** a workflow-paths drift broke 3 juniper-X CIs on 2026-05-18
when a file referenced by `python|bash <path>` in `ci.yml` was renamed
without updating the workflow. The lint asserts every
`python|bash <path>` invocation in `.github/workflows/*.yml` resolves to
a file that exists in the repo, with cross-repo paths (`juniper-X/...`)
skipped as runtime-resolved.

| Repo | PR |
|---|---|
| juniper-ml (package release) | #307 (v0.2.0), #308 (CodeQL ReDoS fix) |
| juniper-data-client | #75 |
| juniper-canopy | #310 |
| juniper-cascor | #295 |
| juniper-cascor-client | #60 |
| juniper-cascor-worker | #82 |
| juniper-data | #139 |

### v0.3.0 — `juniper-lint-agents-md-version` (2026-05-21)

**Trigger:** juniper-ml#295 bumped pyproject 0.4.1 → 0.5.0 but left
AGENTS.md's `**Version**:` header at 0.4.0 for ~6 days (fixed in
juniper-ml#304). The lint asserts the AGENTS.md version header matches
`pyproject.toml [project].version` exactly.

| Repo | PR |
|---|---|
| juniper-ml (package release) | #310 (v0.3.0) |
| juniper-data-client | #76 |
| juniper-canopy | #311 |
| juniper-cascor | #298 |
| juniper-cascor-client | #61 |
| juniper-cascor-worker | #83 |
| juniper-data | #140 |

### Drift detection extension

The §5.1 consumer-pin lint at `juniper-ml/tests/test_ci_tools_drift.py`
already covers both new console scripts because the pin it inspects
(`juniper-ci-tools>=X,<Y` in each consumer's `ci.yml`) is shared. No
separate test_*_drift.py was added; widening the upper bound from
`<0.3.0` → `<0.4.0` in each consumer (done as part of each fan-out PR)
was the only consumer-side change to the drift contract.
