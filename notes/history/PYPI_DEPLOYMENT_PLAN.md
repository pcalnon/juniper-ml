# Juniper Ecosystem PyPI Deployment Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Created**: 2026-02-25
**Status**: PLAN (not yet executed)

---

## Table of Contents

1. [Objective](#1-objective)
2. [Current State](#2-current-state)
3. [Target State](#3-target-state)
4. [Dependency Graph and Release Order](#4-dependency-graph-and-release-order)
5. [Pre-Deployment Checklist](#5-pre-deployment-checklist)
6. [Phase 1: Publish juniper-data-client v0.3.1](#phase-1-publish-juniper-data-client-v031)
7. [Phase 2: Publish juniper-data v0.5.0](#phase-2-publish-juniper-data-v050)
8. [Phase 3: Publish juniper-cascor v1.0.0](#phase-3-publish-juniper-cascor-v100)
9. [Phase 4: Update juniper-ml Meta-Package v0.2.0](#phase-4-update-juniper-ml-meta-package-v020)
10. [Phase 5: Overtoad Research Organization Transfer](#phase-5-overtoad-research-organization-transfer)
11. [Automation Strategy](#6-automation-strategy)
12. [CI Integration](#7-ci-integration)
13. [Risk Mitigation](#8-risk-mitigation)
14. [Appendix A: Version Matrix](#appendix-a-version-matrix)
15. [Appendix B: Publish Workflow Template](#appendix-b-publish-workflow-template)

---

## 1. Objective

Deploy all Juniper polyrepo packages to TestPyPI and PyPI, establishing a complete, installable ecosystem where:

```bash
pip install juniper-ml[all]          # Installs all client libraries + worker
pip install juniper-data[api]        # Installs the dataset generation service
pip install juniper-cascor[all]      # Installs the CasCor backend with all extras
```

Additionally, transfer all packages to the **Overtoad Research** GitHub organization for long-term ownership and branding.

---

## 2. Current State

### Packages Already on PyPI

| Package | PyPI Version | Repo Version | Publish Workflow | Trusted Publishing |
|---------|:------------:|:------------:|:----------------:|:------------------:|
| `juniper-ml` | 0.1.0 | 0.1.0 | `publish.yml` | OIDC configured |
| `juniper-cascor-client` | 0.1.0 | 0.1.0 | `publish.yml` | OIDC configured |
| `juniper-cascor-worker` | 0.1.0 | 0.1.0 | `publish.yml` | OIDC configured |
| `juniper-data-client` | 0.3.0 | 0.3.1 | `publish.yml` | OIDC configured |

### Packages NOT on PyPI

| Package | Repo Version | Publish Workflow | Notes |
|---------|:------------:|:----------------:|-------|
| `juniper-data` | 0.4.2 | None | Service package; needs publish.yml |
| `juniper-cascor` | 0.3.17 | None | Backend package; needs publish.yml |

### Repository Locations

| Package | Repository | Owner |
|---------|-----------|-------|
| `juniper-ml` | `pcalnon/juniper` | pcalnon |
| `juniper-data` | `pcalnon/juniper-data` | pcalnon |
| `juniper-data-client` | `pcalnon/juniper-data-client` | pcalnon |
| `juniper-cascor` | `pcalnon/juniper-cascor` | pcalnon |
| `juniper-cascor-client` | `pcalnon/juniper-cascor-client` | pcalnon |
| `juniper-cascor-worker` | `pcalnon/juniper-cascor-worker` | pcalnon |

---

## 3. Target State

All 6 packages published to PyPI under the **Overtoad Research** organization:

| Package | Target Version | PyPI URL |
|---------|:--------------:|----------|
| `juniper-ml` | 0.2.0 | `pypi.org/project/juniper-ml/` |
| `juniper-data` | 0.5.0 | `pypi.org/project/juniper-data/` |
| `juniper-data-client` | 0.3.1 | `pypi.org/project/juniper-data-client/` |
| `juniper-cascor` | 1.0.0 | `pypi.org/project/juniper-cascor/` |
| `juniper-cascor-client` | 0.1.1 | `pypi.org/project/juniper-cascor-client/` |
| `juniper-cascor-worker` | 0.1.1 | `pypi.org/project/juniper-cascor-worker/` |

---

## 4. Dependency Graph and Release Order

Packages must be released bottom-up (leaves first, dependents last) to ensure dependencies resolve on PyPI.

```
Layer 0 (no inter-project deps — publish first):
  ├── juniper-data-client      (deps: numpy, requests, urllib3)
  ├── juniper-cascor-client    (deps: requests, urllib3, websockets)
  └── juniper-cascor-worker    (deps: numpy, torch)

Layer 1 (depends on Layer 0):
  ├── juniper-data             (optional dep: juniper-data-client)
  └── juniper-cascor           (optional dep: juniper-data-client)

Layer 2 (meta-package — depends on Layer 0):
  └── juniper-ml               (optional deps: data-client, cascor-client, cascor-worker)
```

### Required Release Order

```
1. juniper-data-client     ─┐
2. juniper-cascor-client   ─┤── Layer 0 (can be parallel)
3. juniper-cascor-worker   ─┘
4. juniper-data            ─┐── Layer 1 (can be parallel, after Layer 0)
5. juniper-cascor          ─┘
6. juniper-ml              ─── Layer 2 (after all others)
```

Layer 0 packages have no inter-Juniper dependencies and can be published in any order or in parallel. Layer 1 packages have optional dependencies on Layer 0 packages. The meta-package (`juniper-ml`) must be published last so its dependency constraints can reference published versions.

---

## 5. Pre-Deployment Checklist

### Global Prerequisites

- [ ] Verify PyPI account `pcalnon` has 2FA enabled
- [ ] Verify TestPyPI account `pcalnon` has 2FA enabled
- [ ] Create Overtoad Research organization on GitHub (if not already created)
- [ ] Create Overtoad Research organization on PyPI (if not already created)
- [ ] Verify `build` and `twine` are installed: `pip install build twine`

### Per-Package Prerequisites

For each package:

- [ ] `pyproject.toml` version is correct (not already published)
- [ ] `__version__` in `__init__.py` matches `pyproject.toml` version
- [ ] All tests pass: `pytest`
- [ ] CI pipeline is green on `main`
- [ ] `README.md` renders correctly: `twine check dist/*`
- [ ] No secrets in source tree (`.env`, API keys, etc.)
- [ ] `LICENSE` file exists
- [ ] Package builds cleanly: `python -m build`

### Known Issues to Fix Before Publishing

| Issue | Package | Action |
|-------|---------|--------|
| Version mismatch: `__init__.py` says `0.3.0`, pyproject says `0.3.1` | juniper-data-client | Sync `__version__` to `0.3.1` |
| No `publish.yml` workflow | juniper-data | Create from template (see Appendix B) |
| No `publish.yml` workflow | juniper-cascor | Create from template (see Appendix B) |
| Python version inconsistency | All | Decide on `>=3.11` vs `>=3.12` floor across ecosystem |
| `juniper-ml` extras don't include `juniper-data` or `juniper-cascor` | juniper-ml | Add `services` extra in Phase 4 |

---

## Phase 1: Publish juniper-data-client v0.3.1

**Why first**: Leaf dependency — `juniper-data` and `juniper-cascor` optionally depend on this.

### Steps

1. **Fix version mismatch**
   ```bash
   # In juniper-data-client/juniper_data_client/__init__.py
   # Change __version__ = "0.3.0" to __version__ = "0.3.1"
   ```

2. **Verify tests pass**
   ```bash
   cd juniper-data-client
   pytest tests/ -v --cov=juniper_data_client
   ```

3. **Build and validate**
   ```bash
   rm -rf dist/ build/
   python -m build
   twine check dist/*
   ```

4. **Cut a release**
   ```bash
   git add -A && git commit -m "Bump version to 0.3.1"
   git tag v0.3.1
   git push origin main v0.3.1
   gh release create v0.3.1 --title "v0.3.1" --notes "Patch release: version sync, doc link validation CI."
   ```

5. **Monitor workflow**: `gh run watch` — `publish.yml` triggers on release.

6. **Verify**
   ```bash
   pip install juniper-data-client==0.3.1
   python -c "import juniper_data_client; print(juniper_data_client.__version__)"
   ```

---

## Phase 2: Publish juniper-data v0.5.0

**Why**: Service package — not yet on PyPI. Needs a new `publish.yml` workflow.

### Steps

1. **Determine version**: Current repo is `0.4.2`. The next planned release is v0.5.0 (Quality + Tooling). Publish as `0.5.0` once all v0.5.0 roadmap items are complete, or publish as `0.4.3` for an early PyPI presence.

2. **Create `publish.yml`** (see [Appendix B](#appendix-b-publish-workflow-template))
   - Package name: `juniper-data`
   - Import verification: `python -c "import juniper_data; print(juniper_data.__version__)"`

3. **Configure trusted publishing on PyPI and TestPyPI**
   - Go to PyPI > Account Settings > Publishing > Add a new pending publisher
   - Owner: `pcalnon` (or `OvertoadResearch` if org transfer is done first)
   - Repository: `juniper-data`
   - Workflow: `publish.yml`
   - Environment: `pypi` (repeat for `testpypi`)

4. **Create GitHub environments**
   - In `pcalnon/juniper-data` > Settings > Environments
   - Create `testpypi` (no protection)
   - Create `pypi` (add required reviewer for production gate)

5. **Verify `__version__` exists**
   ```bash
   grep __version__ juniper_data/__init__.py
   ```

6. **Bump version in `pyproject.toml`**, commit, tag, release
   ```bash
   git tag v0.5.0
   git push origin main v0.5.0
   gh release create v0.5.0 --title "v0.5.0" --notes "First PyPI release. Quality + Tooling improvements."
   ```

7. **Verify**
   ```bash
   pip install juniper-data==0.5.0
   pip install "juniper-data[api]==0.5.0"
   ```

---

## Phase 3: Publish juniper-cascor v1.0.0

**Why**: Backend service — not yet on PyPI. Heavy dependency (PyTorch). Needs a `publish.yml` workflow.

### Steps

1. **Determine version**: Current repo is `0.3.17`. Given the maturity of the project and the polyrepo migration completion, `1.0.0` is appropriate for the first standalone PyPI release. Alternatively, continue the existing versioning with `0.4.0`.

2. **Create `publish.yml`** (see [Appendix B](#appendix-b-publish-workflow-template))
   - Package name: `juniper-cascor`
   - Import verification: `python -c "import juniper_cascor; print('OK')"`
   - **Note**: TestPyPI verification needs `--extra-index-url` for PyTorch CPU wheels:
     ```bash
     pip install torch --index-url https://download.pytorch.org/whl/cpu
     ```

3. **Configure trusted publishing** (same pattern as Phase 2)

4. **Create GitHub environments** (same pattern as Phase 2)

5. **Special consideration — PyTorch dependency**
   - PyTorch wheels are large (~200MB). The package will install cleanly from PyPI since `torch>=2.0.0` is available there.
   - TestPyPI verification step needs the `--extra-index-url` for both PyPI (regular deps) and the PyTorch CPU index.
   - Consider documenting CPU vs GPU install instructions in `README.md`.

6. **Bump version, tag, release**

7. **Verify**
   ```bash
   pip install juniper-cascor==1.0.0
   pip install "juniper-cascor[all]==1.0.0"
   ```

---

## Phase 4: Update juniper-ml Meta-Package v0.2.0

**Why**: The meta-package must be updated to reference the newly-published service packages.

### Steps

1. **Update `pyproject.toml` optional dependencies**
   ```toml
   [project.optional-dependencies]
   clients = [
       "juniper-data-client>=0.3.0",
       "juniper-cascor-client>=0.1.0",
   ]
   worker = [
       "juniper-cascor-worker>=0.1.0",
   ]
   services = [
       "juniper-data>=0.5.0",
       "juniper-cascor>=1.0.0",
   ]
   all = [
       "juniper-ml[clients,worker,services]",
   ]
   ```

2. **Bump version to `0.2.0`**

3. **Update README.md** with new installation options:
   ```bash
   pip install juniper-ml                 # Meta-package only (no deps)
   pip install juniper-ml[clients]        # Client libraries
   pip install juniper-ml[worker]         # Distributed worker
   pip install juniper-ml[services]       # Full service packages (data + cascor)
   pip install juniper-ml[all]            # Everything
   ```

4. **Tag and release**
   ```bash
   git tag v0.2.0
   git push origin main v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Add services extra with juniper-data and juniper-cascor."
   ```

5. **Verify end-to-end**
   ```bash
   pip install "juniper-ml[all]==0.2.0"
   python -c "
   import juniper_data_client
   import juniper_cascor_client
   import juniper_cascor_worker
   print('All client packages imported successfully')
   "
   ```

---

## Phase 5: Overtoad Research Organization Transfer

Transfer all Juniper repositories and PyPI packages from `pcalnon` to the `OvertoadResearch` GitHub organization.

### 5.1 Prerequisites

- [ ] Create the `OvertoadResearch` organization on GitHub
  - Settings > Organizations > New organization
  - Choose a plan (Free tier is sufficient for public repos)
  - Add `pcalnon` as owner

- [ ] Create the `OvertoadResearch` organization on PyPI
  - PyPI > Account Settings > Organizations > Create organization
  - Request organization account (PyPI org accounts may require approval)
  - Alternatively, manage under `pcalnon` account with collaborator access

- [ ] Create the `OvertoadResearch` organization on TestPyPI (same process)

### 5.2 GitHub Repository Transfer

For each repository:

1. **Transfer repository ownership**
   - GitHub > Repository > Settings > Danger Zone > Transfer ownership
   - New owner: `OvertoadResearch`
   - GitHub automatically creates a redirect from `pcalnon/<repo>` to `OvertoadResearch/<repo>`
   - **Warning**: This changes the repository URL. All git remotes, CI references, and trusted publisher configs must be updated.

2. **Update git remotes locally**
   ```bash
   git remote set-url origin git@github.com:OvertoadResearch/<repo>.git
   ```

3. **Update SSH config** (if using per-repo deploy keys)
   - Update `~/.ssh/config` Host entries from `github.com-<repo>` to use new org paths

4. **Repository transfer order** (to minimize breakage):
   - Transfer leaf repos first (clients, worker)
   - Transfer service repos second (juniper-data, juniper-cascor)
   - Transfer meta-package last (juniper)

### 5.3 PyPI Package Transfer

PyPI does not support transferring ownership between accounts the same way GitHub does. Options:

#### Option A: Add Organization as Maintainer (Recommended)

1. On PyPI, go to each project > Settings > Collaborators
2. Add the `OvertoadResearch` organization (or its members) as **Owner**
3. Optionally remove `pcalnon` as sole owner (keep as collaborator)
4. Repeat for TestPyPI

#### Option B: Re-publish Under Organization

If PyPI organization accounts become available:
1. Create the organization on PyPI
2. Configure trusted publishing from the new `OvertoadResearch/<repo>` GitHub repos
3. Publish new versions — the package name stays the same; ownership transfers via collaborator settings

### 5.4 Update Trusted Publishing Configuration

After repository transfer, trusted publishing OIDC configs must be updated on both PyPI and TestPyPI:

For each package on PyPI and TestPyPI:
1. Go to project Settings > Publishing
2. **Remove** old trusted publisher: `pcalnon/<repo>` / `publish.yml` / `pypi`
3. **Add** new trusted publisher: `OvertoadResearch/<repo>` / `publish.yml` / `pypi`
4. Repeat for `testpypi` environment

### 5.5 Update Package Metadata

After transfer, update `pyproject.toml` in each repo:

```toml
[project]
authors = [
    { name = "Paul Calnon" },
    { name = "Overtoad Research" },
]

[project.urls]
Homepage = "https://github.com/OvertoadResearch/<repo>"
Repository = "https://github.com/OvertoadResearch/<repo>"
Issues = "https://github.com/OvertoadResearch/<repo>/issues"
```

### 5.6 Update Cross-References

Files that reference `pcalnon/<repo>` URLs:
- `README.md` in each repo (badges, links)
- `CLAUDE.md` / `AGENTS.md` (repository references)
- `notes/` documentation files (GitHub links)
- Redirect notes (`notes/MONOREPO_ANALYSIS.md`, `notes/POLYREPO_MIGRATION_PLAN.md`)
- `dependabot.yml` (no change needed — uses relative paths)
- `pypi-publish-procedure.md` (example URLs)

### 5.7 Transfer Checklist

| Step | juniper-ml | data | data-client | cascor | cascor-client | cascor-worker |
|------|:----------:|:----:|:-----------:|:------:|:-------------:|:-------------:|
| GitHub transfer | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update git remote | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update SSH config | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| PyPI collaborator | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| TestPyPI collaborator | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update trusted pub (PyPI) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update trusted pub (TestPyPI) | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update pyproject.toml URLs | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Update README badges | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Verify CI passes | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Verify publish workflow | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 6. Automation Strategy

### 6.1 Current Automation (Already in Place)

All 4 published packages use the same proven pattern:

- **Trigger**: GitHub Release creation (`on: release: types: [published]`)
- **Authentication**: OIDC trusted publishing (no API tokens)
- **Flow**: TestPyPI → verify install → PyPI
- **Environments**: Separate `testpypi` and `pypi` GitHub environments

This pattern works well and should be extended to `juniper-data` and `juniper-cascor`.

### 6.2 Recommended Automation Enhancements

#### Enhancement 1: Release Coordination Workflow (juniper-ml repo)

A GitHub Actions workflow in the `juniper-ml` meta-package repo that orchestrates ecosystem-wide releases:

```yaml
# .github/workflows/ecosystem-release.yml
name: Ecosystem Release

on:
  workflow_dispatch:
    inputs:
      packages:
        description: 'Comma-separated list of packages to release'
        required: true
        type: string
      dry_run:
        description: 'Dry run (validate only, do not publish)'
        required: false
        type: boolean
        default: true
```

This workflow would:
1. Check dependency order automatically
2. Validate all packages build cleanly
3. Verify version consistency across the ecosystem
4. Optionally trigger releases in dependency order

**Complexity**: Medium. Requires cross-repo `workflow_dispatch` triggers via GitHub API or `gh workflow run`.

#### Enhancement 2: Version Consistency Checker

A CI job (in each repo or centralized in `juniper-ml`) that validates:
- `pyproject.toml` version matches `__init__.py.__version__`
- Inter-package version constraints are satisfiable
- No circular dependency issues

```python
# scripts/check_ecosystem_versions.py
# Reads all pyproject.toml files and validates the dependency graph
```

**Complexity**: Low. Pure Python script, no external dependencies.

#### Enhancement 3: Automated Changelog Generation

Use `git-cliff` or `auto-changelog` to generate changelogs from conventional commits:

```yaml
# In publish.yml, before building:
- name: Generate changelog
  run: |
    pip install git-cliff
    git-cliff --output CHANGELOG.md
```

**Complexity**: Low. One-time setup per repo.

#### Enhancement 4: Pre-Release Validation Gate

Add a `pre-release` CI job that runs on tag push (before the release is created):

```yaml
on:
  push:
    tags: ['v*']

jobs:
  validate:
    steps:
      - run: python -m build && twine check dist/*
      - run: pytest
      - run: pip install dist/*.whl && python -c "import <package>"
```

This catches packaging errors before the irreversible PyPI upload.

**Complexity**: Low. Standard CI pattern.

### 6.3 Automation NOT Recommended

| Idea | Why Not |
|------|---------|
| Fully automatic version bumping | Risk of unintended releases; versions should be deliberate |
| Auto-publish on merge to main | Too aggressive for a research platform; releases should be intentional |
| Monorepo-style unified versioning | Packages evolve at different rates; independent versioning is correct |
| PyPI publish without TestPyPI gate | TestPyPI catches packaging errors before the irreversible PyPI upload |

---

## 7. CI Integration

### 7.1 Current CI Architecture

Each repo has a CI pipeline (`ci.yml`) that runs on push/PR:

| Repo | CI Jobs |
|------|---------|
| juniper-data | pre-commit, docs, unit-tests, build, dependency-docs, integration-tests, security, quality gate, slow-tests, notify |
| juniper-cascor | pre-commit, docs, unit-tests, quick-integration, integration-tests, build, dependency-docs, security, quality gate, notify |
| juniper-data-client | docs, test, dependency-docs |
| juniper-cascor-client | docs, test, dependency-docs |
| juniper-cascor-worker | docs, test, dependency-docs |
| juniper-ml | docs, dependency-docs |

Publishing is handled by a separate `publish.yml` workflow triggered by GitHub Release events.

### 7.2 Integration Points for Publishing

The publish workflow is intentionally separate from CI:

```
CI (ci.yml)                          Publish (publish.yml)
─────────────                        ────────────────────
on: push, pull_request               on: release published
├── pre-commit                       ├── testpypi
├── unit-tests                       │   ├── build
├── integration-tests                │   ├── twine check
├── security                         │   ├── publish to TestPyPI
├── docs                             │   └── verify install
├── build                            └── pypi (needs: testpypi)
├── dependency-docs                      ├── build
└── quality-gate                         ├── twine check
                                         └── publish to PyPI
```

**Design rationale**: Publish is release-gated, not merge-gated. CI ensures code quality on every push; publishing is an explicit, versioned act.

### 7.3 Recommended CI Additions

#### Add Package Build Validation to CI

Currently, the `build` job in CI builds the package but doesn't validate it as installable. Add:

```yaml
# In ci.yml build job:
- name: Validate package installability
  run: |
    pip install dist/*.whl
    python -c "import <package_name>; print('Install OK')"
```

This catches packaging issues (missing files, broken imports) on every PR, not just at release time.

#### Add Cross-Package Version Constraint Check

In the `juniper-ml` CI, add a job that validates the ecosystem dependency graph:

```yaml
version-check:
  name: Ecosystem Version Check
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Validate ecosystem dependencies
      run: |
        pip install juniper-ml[all]
        pip check  # Verify no dependency conflicts
```

---

## 8. Risk Mitigation

### Version Conflicts

**Risk**: Publishing a package with a dependency constraint that can't be satisfied.
**Mitigation**: Publish leaves first (Layer 0), verify install, then publish dependents (Layer 1), then meta-package (Layer 2). The TestPyPI gate catches unresolvable constraints.

### Irreversible PyPI Uploads

**Risk**: Publishing a broken version that can't be re-uploaded.
**Mitigation**: TestPyPI verification step in every publish workflow. Add `pypi` environment with required reviewer protection in GitHub.

### Organization Transfer Breakage

**Risk**: Changing repository URLs breaks CI, trusted publishing, and local git remotes.
**Mitigation**: Transfer repos one at a time, starting with leaf packages. Verify CI and publish workflows after each transfer before proceeding. GitHub's URL redirects provide a grace period.

### PyTorch Dependency Size

**Risk**: `juniper-cascor` pulls in PyTorch (~200MB+), making installs slow.
**Mitigation**: PyTorch is an optional dependency under `[ml]` extra. Document CPU-only install:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install juniper-cascor[ml]
```

### TestPyPI Index Propagation Delay

**Risk**: Verification step fails because TestPyPI hasn't indexed the upload yet.
**Mitigation**: 30-second sleep is already in all publish workflows. If flaky, increase to 60 seconds or add retry logic.

---

## Appendix A: Version Matrix

### Current Versions (pre-deployment)

| Package | pyproject.toml | `__init__.py` | PyPI | TestPyPI | Status |
|---------|:-:|:-:|:-:|:-:|--------|
| juniper-ml | 0.1.0 | N/A (meta) | 0.1.0 | 0.1.0 | Published |
| juniper-data | 0.4.2 | 0.4.2 | — | — | Not published |
| juniper-data-client | 0.3.1 | **0.3.0** | 0.3.0 | 0.3.0 | Version mismatch |
| juniper-cascor | 0.3.17 | — | — | — | Not published |
| juniper-cascor-client | 0.1.0 | 0.1.0 | 0.1.0 | 0.1.0 | Published |
| juniper-cascor-worker | 0.1.0 | 0.1.0 | 0.1.0 | 0.1.0 | Published |

### Target Versions (post-deployment)

| Package | Version | Change Type |
|---------|:-------:|-------------|
| juniper-ml | 0.2.0 | MINOR — add `services` extra |
| juniper-data | 0.5.0 | MINOR — first PyPI release |
| juniper-data-client | 0.3.1 | PATCH — version sync fix |
| juniper-cascor | 1.0.0 | MAJOR — first standalone PyPI release |
| juniper-cascor-client | 0.1.1 | PATCH — doc validation CI |
| juniper-cascor-worker | 0.1.1 | PATCH — doc validation CI |

---

## Appendix B: Publish Workflow Template

Template for packages that don't yet have a `publish.yml`. Adapted from the existing pattern used by `juniper-ml`, `juniper-data-client`, `juniper-cascor-client`, and `juniper-cascor-worker`.

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write

jobs:
  testpypi:
    name: Publish to TestPyPI
    runs-on: ubuntu-latest
    environment: testpypi
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

      - name: Verify TestPyPI install
        run: |
          VERSION="${{ github.event.release.tag_name }}"
          VERSION="${VERSION#v}"
          sleep 30
          pip install \
              --index-url https://test.pypi.org/simple/ \
              --extra-index-url https://pypi.org/simple/ \
              PACKAGE_NAME==${VERSION}
          python -c "import IMPORT_NAME; print(f'TestPyPI OK: v{IMPORT_NAME.__version__}')"

  pypi:
    name: Publish to PyPI
    needs: testpypi
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### Template Substitutions

| Placeholder | juniper-data | juniper-cascor |
|-------------|:------------:|:--------------:|
| `PACKAGE_NAME` | `juniper-data` | `juniper-cascor` |
| `IMPORT_NAME` | `juniper_data` | (see note) |

**Note for juniper-cascor**: The TestPyPI verification step needs special handling for PyTorch:
```yaml
- name: Verify TestPyPI install
  run: |
    VERSION="${{ github.event.release.tag_name }}"
    VERSION="${VERSION#v}"
    sleep 30
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        juniper-cascor==${VERSION}
```

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-25 | Paul Calnon / AI Agent | Initial creation |
