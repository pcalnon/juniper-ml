# Cross-Repo CI Pipeline Alignment Plan

**Date**: 2026-04-29
**Author**: Paul Calnon (with Claude Opus 4.7)
**Scope**: All 8 active Juniper Project repositories.
**Goal**: Bring every repository's CI / pre-commit / quality-gate setup to a common baseline by **adding missing checks**, never by removing existing ones.

---

## 0. Table of contents

- [1. Goals and non-goals](#1-goals-and-non-goals)
- [2. Methodology](#2-methodology)
- [3. Authoritative inventory snapshot](#3-authoritative-inventory-snapshot)
- [4. Target baseline](#4-target-baseline)
- [5. Gap matrix](#5-gap-matrix)
- [6. Per-repo remediation plans](#6-per-repo-remediation-plans)
- [7. Cross-cutting templates](#7-cross-cutting-templates)
- [8. Validation criteria](#8-validation-criteria)
- [9. Sequencing and risk](#9-sequencing-and-risk)
- [10. Tracking checklist](#10-tracking-checklist)
- [Appendix A — by-design exclusions](#appendix-a--by-design-exclusions)
- [Appendix B — validation pass log](#appendix-b--validation-pass-log)
- [Appendix C — verbatim discovery commands](#appendix-c--verbatim-discovery-commands)

---

## 1. Goals and non-goals

### Goals

- Every repository has the same **set of applicable** quality gates wired into CI.
- Every repository's pre-commit suite enforces the same union of file-type
  checks (subject to the language / domain of the repository).
- Every repository's set of GitHub Actions workflows includes the same
  union of cross-cutting workflows (CodeQL, Claude assistant, scheduled
  security scan, scheduled doc check, scheduled tests, lockfile update),
  unless an exclusion is explicitly justified in
  [Appendix A](#appendix-a--by-design-exclusions).
- The plan is **additive only**. No existing job, hook, or workflow is
  removed.

### Non-goals

- Refactoring black/isort/flake8 → ruff. juniper-data is the only repo
  on ruff today; the plan does **not** propose migrating others to ruff
  or migrating juniper-data back. Tool-choice convergence is a separate
  initiative.
- Lowering / loosening any existing threshold (e.g. coverage % gates) to
  match a less-strict laggard. Where coverage gates differ, the strict
  one stays.
- Touching publishing pipelines (`publish*.yml`) — those are tag-gated
  release flows, already audited in
  `notes/releases/RELEASE_WALKTHROUGH_juniper-ml-v0.4.1_juniper-observability-v0.1.1a_2026-04-28.md`.
- Adding a new package manager, lockfile format, or container scanner
  beyond what the fleet uses today.

---

## 2. Methodology

1. **Inventory** — for each of the 8 repos, enumerate everything in
   `.github/workflows/`, `.github/dependabot.yml`,
   `.github/CODEOWNERS`, `.pre-commit-config.yaml`,
   pytest configuration, and any `[tool.*]` sections in
   `pyproject.toml`.
2. **Define the baseline** — the union of all checks that any repo
   in the fleet runs today, scoped to "what would it mean for *this*
   repo to fully meet that baseline."
3. **Compute the gap** per repo, separated into:
   - **Must-add** — applicable to the repo and present in at least one
     peer; the repo currently lacks it.
   - **By-design skip** — the repo legitimately doesn't need it (e.g.
     a Python type-checker on a Docker-only orchestration repo).
4. **Author per-repo remediation plans** — one PR per repo, scoped to
   *additions only*. Each PR description references this plan.
5. **Validate** the plan — direct file reads to confirm every gap
   claim is real, every "by-design skip" justification holds, and
   every additive-only constraint is preserved.
6. **Track completion** — the checklist in §10 is the single source
   of truth for plan execution status.

---

## 3. Authoritative inventory snapshot

Direct filesystem inventory as of **2026-04-29**:

### 3.1 Workflow files present (`.github/workflows/`)

| Workflow                                                        |    ml     | canopy |  cascor   | data | data-client | cascor-client | cascor-worker | deploy |
|-----------------------------------------------------------------|:---------:|:------:|:---------:|:----:|:-----------:|:-------------:|:-------------:|:------:|
| `ci.yml`                                                        |     ✓     |   ✓    |     ✓     |  ✓   |      ✓      |       ✓       |       ✓       |   ✓    |
| `claude.yml`                                                    |     ✓     |   ✗    |     ✗     |  ✗   |      ✗      |       ✗       |       ✗       |   ✗    |
| `codeql.yml`                                                    |     ✗     |   ✗    |     ✗     |  ✓   |      ✗      |       ✗       |       ✗       |   ✗    |
| `security-scan.yml` (weekly pip-audit)                          |     ✓     |   ✓    |     ✓     |  ✓   |      ✓      |       ✓       |       ✓       |   ✗    |
| `scheduled-tests.yml`                                           |     ✗     |   ✗    |     ✓     |  ✗   |      ✗      |       ✗       |       ✗       |   ✗    |
| `lockfile-update.yml`                                           |     ✗     |   ✓    |     ✓     |  ✓   |      ✗      |       ✓       |       ✗       |   ✗    |
| `docs-full-check.yml`                                           |     ✓     |   ✗    |     ✗     |  ✗   |      ✗      |       ✗       |       ✗       |   ✗    |
| `publish*.yml`                                                  |     ✓     |   ✓    |     ✓     |  ✓   |      ✓      |       ✓       |       ✓       |   ✗    |
| repo-specific (`ci-observability.yml`, `ci-protocol.yml`, etc.) | ml,cascor |   —    | ml,cascor |  —   |      —      |       —       |       —       |   —    |

### 3.2 Top-level config files

| File                      | ml | canopy | cascor | data | data-client | cascor-client | cascor-worker | deploy |
|---------------------------|:--:|:------:|:------:|:----:|:-----------:|:-------------:|:-------------:|:------:|
| `.pre-commit-config.yaml` | ✓  |   ✓    |   ✓    |  ✓   |      ✓      |       ✓       |       ✓       |   ✓    |
| `.github/dependabot.yml`  | ✓  |   ✓    |   ✓    |  ✓   |      ✓      |       ✓       |       ✓       |   ✓    |
| `.github/CODEOWNERS`      | ✓  |   ✓    |   ✓    |  ✓   |      ✓      |       ✓       |       ✓       |   ✓    |

### 3.3 Pre-commit hook coverage

(From the structured inventory. "•" = present, blank = absent.)

| Hook family                                                                           | ml |               canopy               | cascor |           data            | data-client | cascor-client | cascor-worker |               deploy                |
|---------------------------------------------------------------------------------------|:--:|:----------------------------------:|:------:|:-------------------------:|:-----------:|:-------------:|:-------------:|:-----------------------------------:|
| pre-commit/pre-commit-hooks (yaml/json/toml/eof/trailing/large-files/private-key/...) | •  |                 •                  |   •    |             •             |      •      |       •       |       •       |                  •                  |
| black                                                                                 |    |                 •                  |   •    |          (ruff)           |      •      |       •       |       •       |                                     |
| isort                                                                                 |    |                 •                  |   •    |          (ruff)           |      •      |       •       |       •       |                                     |
| flake8 source                                                                         |    |                 •                  |   •    |          (ruff)           |      •      |       •       |       •       |                                     |
| flake8 tests (relaxed)                                                                |    |                 •                  |   •    |          (ruff)           |      •      |       •       |       •       |                                     |
| ruff (lint + format)                                                                  |    |                                    |        |             •             |             |               |               |                                     |
| mypy                                                                                  |    |                 •                  |   •    |             •             |      •      |       •       |       •       |                                     |
| bandit source                                                                         | •  |                 •                  |   •    |             •             |      •      |       •       |       •       |                                     |
| bandit tests (relaxed)                                                                |    |                 •                  |   •    |         (note 1)          |      •      |       •       |       •       |                                     |
| shellcheck                                                                            | •  |                 •                  |   •    |             •             |      •      |       •       |       •       |                  •                  |
| markdownlint                                                                          | •  |                 •                  |   •    |                           |      •      |       •       |       •       |                                     |
| yamllint                                                                              | •  |                 •                  |   •    |             •             |      •      |       •       |       •       |             • (strict)              |
| no-unencrypted-env                                                                    | •  |                 •                  |   •    |             •             |      •      |       •       |       •       |                  •                  |
| repo-specific local hooks                                                             |    | C-22 normalize_metric_format_guard |        | coverage-check (pre-push) |             |               |               | helm-lint, validate-sops-encryption |

Note 1: juniper-data uses ruff for lint/format, has bandit on source only,
and relies on the test markers + ruff per-file-ignores to keep tests sane.

### 3.4 Test-infrastructure shape

| Repo                  | Coverage gate            | Markers (declared / inferred)             | Multi-Python matrix       |
|-----------------------|--------------------------|-------------------------------------------|---------------------------|
| juniper-ml            | none                     | n/a (regression scripts)                  | 3.12 only                 |
| juniper-canopy        | 80%                      | unit, integration, performance            | 3.12 / 3.13 / 3.14        |
| juniper-cascor        | 80%                      | unit, integration, performance, slow, gpu | 3.12 / 3.13 / 3.14        |
| juniper-data          | 95% agg / 85% per-module | unit, integration                         | 3.12 / 3.13 / 3.14        |
| juniper-data-client   | 80%                      | unit, integration                         | 3.12 / 3.13 / 3.14        |
| juniper-cascor-client | 80%                      | unit, integration                         | 3.11 / 3.12 / 3.13 / 3.14 |
| juniper-cascor-worker | 80%                      | unit, integration                         | 3.12 / 3.13 / 3.14        |
| juniper-deploy        | n/a                      | n/a                                       | n/a (infra)               |

---

## 4. Target baseline

For an **applicable** repo (i.e. excluding by-design skips in
[Appendix A](#appendix-a--by-design-exclusions)), the baseline is:

### 4.1 Workflows

| Workflow              | Purpose                                                                                            | Trigger                                   |
|-----------------------|----------------------------------------------------------------------------------------------------|-------------------------------------------|
| `ci.yml`              | Pre-commit + unit + integration + build + docs + security + dependency-docs + required-checks gate | push / PR / manual                        |
| `codeql.yml`          | Semantic SAST for Python                                                                           | push to main, weekly schedule, PR to main |
| `claude.yml`          | `@claude` PR/issue assistant                                                                       | issue / PR comment / review               |
| `security-scan.yml`   | Weekly pip-audit (or equivalent) standalone                                                        | schedule (Mon 06:00 UTC) + manual         |
| `docs-full-check.yml` | Full doc-link validation including cross-repo                                                      | weekly + manual                           |
| `scheduled-tests.yml` | Slow / integration / nightly suites                                                                | schedule (daily) + manual                 |
| `lockfile-update.yml` | Refresh pinned dependency lockfiles                                                                | schedule + manual                         |
| `publish*.yml`        | OIDC trusted publishing                                                                            | release / tag                             |

### 4.2 Pre-commit hook union

For each Python repo, all of:

- pre-commit/pre-commit-hooks suite (already universal)
- formatting + linting (either black + isort + flake8, **or** ruff —
  pick one stack per repo, do **not** add the other on top)
- mypy (gradually-typed, project-specific exclude list permitted)
- bandit on source (skip B101/B311 typical) + bandit on tests (relaxed)
- shellcheck for `*.sh` / `*.bash`
- markdownlint
- yamllint
- `no-unencrypted-env` local hook for `.env` / `.env.secrets`

### 4.3 Repo-level config

- `.github/dependabot.yml` covering `pip` (where applicable),
  `github-actions`, and `docker` (where applicable).
- `.github/CODEOWNERS` in place.
- `pyproject.toml` `[tool.*]` sections matching the active formatter /
  type checker / coverage tool.

### 4.4 CI job shape

Every repo's `ci.yml` should include (job names normalized):

1. `pre-commit` — run pre-commit on the supported Python matrix.
2. `unit-tests` — pytest unit suite on the supported Python matrix.
3. `integration-tests` — pytest integration suite (with whatever
   service fixtures the repo needs).
4. `docs` — `python util/check_doc_links.py --cross-repo skip` (or
   the project-local equivalent).
5. `security` — pip-audit + bandit SARIF + gitleaks (or, for
   non-Python repos, an equivalent set: SOPS validation + helm lint
   + container scan).
6. `build` — `python -m build`, `twine check dist/*`.
7. `dependency-docs` — `util/generate_dep_docs.sh` or equivalent.
8. `required-checks` — single aggregator that **all** of the above
   feed into; this is the only check protected branches require.

---

## 5. Gap matrix

For each repo, **only** the items that should be added.
Items intentionally skipped are listed in
[Appendix A](#appendix-a--by-design-exclusions).

### 5.1 Workflow gaps (additions only)

| Workflow              |     ml      |       canopy        |       cascor        |        data         |     data-client     |    cascor-client    |    cascor-worker    |                    deploy                     |
|-----------------------|:-----------:|:-------------------:|:-------------------:|:-------------------:|:-------------------:|:-------------------:|:-------------------:|:---------------------------------------------:|
| `claude.yml`          |      —      |       **add**       |       **add**       |       **add**       |       **add**       |       **add**       |       **add**       |                    **add**                    |
| `codeql.yml`          |   **add**   |       **add**       |       **add**       |          —          |       **add**       |       **add**       |       **add**       |                 skip (Appx A)                 |
| `security-scan.yml`   |      —      |          —          |          —          |          —          |          —          |          —          |          —          | **add (compose-scan / SOPS / trivy variant)** |
| `scheduled-tests.yml` | skip (meta) |       **add**       |          —          |       **add**       |       **add**       |       **add**       |       **add**       |                skip (no tests)                |
| `lockfile-update.yml` |   **add**   |          —          |          —          |          —          |       **add**       |          —          |       **add**       |           skip (no Python lockfile)           |
| `docs-full-check.yml` |      —      | **add (or import)** | **add (or import)** | **add (or import)** | **add (or import)** | **add (or import)** | **add (or import)** |              **add (or import)**              |

"add (or import)" — `docs-full-check.yml` lives in juniper-ml today
and clones every other repo. The cleanest plan is to keep it
juniper-ml-owned but add a thin per-repo `docs.yml` that re-uses
`util/check_doc_links.py` against the local repo only, so a missing
link in (say) canopy fails canopy's own CI rather than only juniper-ml's
weekly cross-repo run. Both are additive.

### 5.2 Pre-commit gaps

| Gap                                                                                 | Repos affected               | Fix                                                                                                                                      |
|-------------------------------------------------------------------------------------|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Missing `black` / `isort` / `flake8` / `mypy` on `scripts/` + `tests/` Python files | juniper-ml                   | Add hooks scoped to `^(scripts\|tests)/.*\.py$`. juniper-ml does have Python in those dirs and currently relies on flake8 + bandit only. |
| Missing `markdownlint`                                                              | juniper-data, juniper-deploy | Add it with the project-local `.markdownlint.yaml` and the standard exclude list.                                                        |
| Missing `bandit on tests (relaxed)` profile                                         | juniper-data                 | Already partially covered by ruff but a tests-only bandit profile aligns the fleet. Optional.                                            |

### 5.3 CI job gaps

| Gap                                         | Repos affected                              | Fix                                                                                                                                          |
|---------------------------------------------|---------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Every job is single-Python (3.12);          | juniper-ml                                  | Promote `pre-commit` and `tests` to a 3-version Python matrix to match the fleet.                                                            |
| -- rest of fleet runs matrix 3.12/3.13/3.14 |                                             | -- juniper-ml already has a dedicated `tests` job — no split needed.                                                                         |
| No `integration-tests` job                  | juniper-data-client, juniper-cascor-client, | Add an `integration-tests` job — even if the body is `pytest -m integration` matching whatever's currently in `tests/`.                      |
|                                             | -- juniper-cascor-worker                    | -- Where the suite is empty, the job is a no-op stub today and a real check tomorrow. juniper-ml is excluded (meta-package; see Appendix A). |
| No `dependency-docs` job                    | juniper-deploy                              | Skipped per Appendix A (infra repo — no pip surface to render). No applicable additions in this row for any other repo:                      |
|                                             |                                             | -- canopy / cascor / data / data-client / cascor-client / cascor-worker / ml all already have a `dependency-docs` job.                       |

### 5.4 Repo-config gaps

| Gap                                                                                               | Repos affected | Fix                                                                                                                                                                       |
|---------------------------------------------------------------------------------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `[tool.*]` sections in `pyproject.toml` not declared (formatter / type checker / coverage / ruff) | juniper-ml     | Even a meta-package benefits from `[tool.coverage.run]` for the regression suite + `[tool.black]` / `[tool.isort]` / `[tool.mypy]` aligned with the new pre-commit hooks. |

---

## 6. Per-repo remediation plans

Each entry below proposes a single PR per repo. PRs are independent
and can land in any order **except** the cross-cutting template work
in §7, which should land first so that subsequent PRs reference the
canonical templates.

### 6.1 juniper-ml

- Add `black`, `isort`, `mypy` pre-commit hooks scoped to
  `^(scripts|tests)/.*\.py$`. Configure `[tool.black]` /
  `[tool.isort]` / `[tool.mypy]` in `pyproject.toml`.
- Promote `ci.yml::pre-commit` to a Python matrix (`3.12, 3.13, 3.14`).
- Split a dedicated `unit-tests` job out of `pre-commit`.
- Add `codeql.yml` (template in §7.2).
- Add `lockfile-update.yml` (template in §7.4).

### 6.2 juniper-canopy

- Add `claude.yml` (template in §7.1).
- Add `codeql.yml` (template in §7.2).
- Add `scheduled-tests.yml` (template in §7.3).
- (Already has a `dependency-docs` job; no change needed.)

### 6.3 juniper-cascor

- Add `claude.yml`.
- Add `codeql.yml`.
- (Already has `scheduled-tests.yml`.)

### 6.4 juniper-data

- Add `claude.yml`.
- Add `markdownlint` pre-commit hook (project-local `.markdownlint.yaml`
  with the standard exclude list).
- Add `scheduled-tests.yml`.

### 6.5 juniper-data-client

- Add `claude.yml`.
- Add `codeql.yml`.
- Add `scheduled-tests.yml`.
- Add `lockfile-update.yml`.
- Add an `integration-tests` job to `ci.yml` (paired with whatever
  `juniper-data` test container the data-client integration suite
  needs).

### 6.6 juniper-cascor-client

- Add `claude.yml`.
- Add `codeql.yml`.
- Add `scheduled-tests.yml`.

### 6.7 juniper-cascor-worker

- Add `claude.yml`.
- Add `codeql.yml`.
- Add `scheduled-tests.yml`.
- Add `lockfile-update.yml`.

### 6.8 juniper-deploy

- Add `claude.yml`.
- Add `security-scan.yml` — but **not** pip-audit. Use a
  compose-side scan (e.g. `docker compose config` plus
  [trivy](https://github.com/aquasecurity/trivy) on referenced images
  and a SOPS encryption integrity check). Treat this as the
  infra-flavored equivalent of the Python `security-scan.yml`.
- Add a `markdownlint` pre-commit hook scoped to the repo's `*.md`
  files (currently absent — only shellcheck + yamllint cover non-YAML
  text). Use the standard exclude list.

---

## 7. Cross-cutting templates

These land first as PRs in juniper-ml, then are copied verbatim to
each consumer. The minimum viable form of each is sketched below; the
canonical, lint-clean form is committed with the template PR.

### 7.1 `claude.yml`

```yaml
---
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]
  pull_request_review:
    types: [submitted]

permissions:
  contents: read
  pull-requests: write
  issues: write
  id-token: write

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || contains(github.event.issue.title, '@claude')))
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: anthropics/claude-code-action@v1.0.107
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Pin the action version to whatever juniper-ml currently uses
(verified: `1.0.107`). Dependabot will keep it current.

### 7.2 `codeql.yml`

```yaml
---
name: CodeQL Analysis
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'
permissions:
  actions: read
  contents: read
  security-events: write
jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: [python]
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: github/codeql-action/init@v4
        with:
          languages: ${{ matrix.language }}
          queries: security-and-quality
      - uses: github/codeql-action/analyze@v4
```

For juniper-deploy: language `javascript` and `python` would both be
empty; replace with [`hadolint`](https://github.com/hadolint/hadolint-action)
+ [`trivy`](https://github.com/aquasecurity/trivy-action) instead, or
omit per [Appendix A](#appendix-a--by-design-exclusions).

### 7.3 `scheduled-tests.yml`

Daily nightly run of slow / integration suites that we don't run on
every push. Baseline shape:

```yaml
---
name: Scheduled Tests
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
jobs:
  slow:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: actions/setup-python@v6.2.0
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[test]"
      - run: pytest -m "slow or integration" --tb=short
```

### 7.4 `lockfile-update.yml`

For repos that maintain pinned lockfiles (`requirements_ci.txt`,
`conda_environment_ci.yaml`, `requirements.lock`):

```yaml
---
name: Update Lockfiles
on:
  schedule:
    - cron: '0 8 * * 1'
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: actions/setup-python@v6.2.0
        with:
          python-version: "3.12"
      - run: bash util/generate_dep_docs.sh
      - uses: peter-evans/create-pull-request@v7
        with:
          branch: chore/lockfile-update
          title: 'chore(deps): refresh CI lockfiles'
          body: 'Automated lockfile refresh.'
          commit-message: 'chore(deps): refresh CI lockfiles'
```

### 7.5 `security-scan.yml` (deploy variant)

```yaml
---
name: Scheduled Security Scan
on:
  schedule:
    - cron: '0 6 * * 1'
  workflow_dispatch:
jobs:
  trivy-fs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: aquasecurity/trivy-action@v0
        with:
          scan-type: fs
          severity: HIGH,CRITICAL
          exit-code: '1'
  sops-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - run: bash util/sops-pre-commit-hook.sh
```

### 7.6 `dependency-docs` job (snippet)

Append to `ci.yml`:

```yaml
  dependency-docs:
    runs-on: ubuntu-latest
    needs: [pre-commit]
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: actions/setup-python@v6.2.0
        with:
          python-version: ${{ env.PYTHON_TEST_VERSION }}
      - run: bash util/generate_dep_docs.sh
      - run: |
          if ! git diff --quiet -- requirements_ci.txt conda_environment_ci.yaml; then
            echo "Dependency docs are stale; regenerate with util/generate_dep_docs.sh"
            exit 1
          fi
```

---

## 8. Validation criteria

After the plan executes, the following holds for **every** repo
(unless an [Appendix A](#appendix-a--by-design-exclusions) exclusion
applies):

1. `ls .github/workflows/` includes `ci.yml`, `claude.yml`, `codeql.yml`, `security-scan.yml`, `scheduled-tests.yml`, `lockfile-update.yml`, and a `publish*.yml`.
2. `.pre-commit-config.yaml` includes formatting + linting + type-checking + bandit (with relaxed test profile) + shellcheck + markdownlint + yamllint + `no-unencrypted-env`.
3. `ci.yml` has a `required-checks` aggregator job that depends on every other job.
4. The CI matrix includes Python 3.12, 3.13, 3.14 (3.11 only where that repo already supports it, e.g. juniper-cascor-client).
5. Coverage gate is preserved (≥ 80% per pre-existing thresholds; no downward changes).
6. Every workflow file passes [`actionlint`](https://github.com/rhysd/actionlint).
7. Every pre-commit config passes `pre-commit run --all-files` on a freshly-cloned checkout.
8. `gh run list --limit 1` for each repo's `ci.yml` returns `success` on the first push that lands the alignment PR.

---

## 9. Sequencing and risk

1. **Phase 0 — Templates (juniper-ml).** Land §7.1 / 7.2 / 7.3 / 7.4 / 7.5 / 7.6 templates as a single PR, with shellcheck / actionlint / yamllint clean. Subsequent PRs reference these templates.
2. **Phase 1 — Cross-cutting workflow rollout.** One PR per repo adding `claude.yml`, `codeql.yml`, `scheduled-tests.yml`, and `lockfile-update.yml` (where applicable). These are pure additions — they cannot break any existing CI job because they live in their own files.
3. **Phase 2 — `ci.yml` job augmentation.** One PR per repo for the missing `unit-tests` / `integration-tests` / `dependency-docs` jobs. These edit the existing `ci.yml` and so are riskier; sanity check by running the workflow on the PR branch *before* merging.
4. **Phase 3 — Pre-commit hook additions.** One PR per repo. Run `pre-commit run --all-files` on the affected repo after the addition; any new violations get a separate fix-up commit on the same PR rather than deferred.
5. **Phase 4 — Coverage / `[tool.*]` config (juniper-ml only).** The most invasive — defer to last so the prior phases haven't churned the file.

### Risk register

| Risk                                                            | Likelihood     | Mitigation                                                                                                                                           |
|-----------------------------------------------------------------|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| New job exposes pre-existing latent failure                     | M              | Run the new job on the PR branch first; if it fails, fix the underlying issue rather than disabling the job.                                         |
| New pre-commit hook produces a flood of formatting changes      | H (juniper-ml) | Run the hook with `--all-files` on a separate branch; commit the auto-format pass separately so reviewers can isolate "config" from "auto-fix".      |
| `claude.yml` rollout reveals missing `ANTHROPIC_API_KEY` secret | M              | Verify the secret exists at the org or repo level before merging the PR; document the secret name in the per-repo PR description.                    |
| Required-checks aggregator references a job that doesn't exist  | L              | actionlint catches this.                                                                                                                             |
| CodeQL produces actionable findings on day one                  | M              | Treat the first CodeQL run as a soft-fail for one cycle (tag the PR `codeql-shakedown`) and triage findings before promoting it to a required check. |
| Trivy on juniper-deploy fails on transitive base-image CVEs     | H              | Pin `severity: HIGH,CRITICAL`; allow weekly re-tune via the same `--ignore-vuln`-style flag pip-audit uses.                                          |

---

## 10. Tracking checklist

Single source of truth for plan execution. All execution rolled out
**direct to `main` on each repo** (no PRs were used per session
direction); the SHAs below are the merged commits on each repo's
`origin/main`.

### Phase 0 — Templates

- [x] juniper-ml: commit canonical `claude.yml`, `codeql.yml`,
      `scheduled-tests.yml`, `lockfile-update.yml`, `security-scan.yml`
      (deploy variant) under `notes/templates/ci/` plus a README and
      this plan doc — **`f9ddc06`**. The `dependency-docs` snippet
      was dropped during validation: every applicable repo already
      ships a `dependency-docs` job, so a stand-alone snippet would
      have been dead weight.

### Phase 1 — Workflow file additions

- [x] juniper-canopy: add `claude.yml`, `codeql.yml`,
      `scheduled-tests.yml` — **`6bc6150`**.
- [x] juniper-cascor: add `claude.yml`, `codeql.yml` — **`4e409d3`**.
- [x] juniper-data: add `claude.yml`, `scheduled-tests.yml` —
      **`6586816`**.
- [x] juniper-data-client: add `claude.yml`, `codeql.yml`,
      `scheduled-tests.yml`, `lockfile-update.yml` — **`e71fdd9`**.
- [x] juniper-cascor-client: add `claude.yml`, `codeql.yml`,
      `scheduled-tests.yml` — **`642fce5`**.
- [x] juniper-cascor-worker: add `claude.yml`, `codeql.yml`,
      `scheduled-tests.yml`, `lockfile-update.yml` — **`b405f6a`**.
- [x] juniper-deploy: add `claude.yml`, `security-scan.yml` (deploy
      variant with `continue-on-error: true` on the `trivy-fs` job
      for the shakedown cycle) — **`407f1bd`**.
- [x] juniper-ml: add `codeql.yml`, `lockfile-update.yml` —
      **`a0f14a7`**.

### Phase 2 — `ci.yml` augmentation

- [x] juniper-data-client: add `integration-tests` job (matrix
      3.12/3.13/3.14, `pytest -m integration`, exit-code-5
      treated-as-skip, soft-fail in `required-checks`) — **`ada9b30`**.
- [x] juniper-cascor-client: add `integration-tests` job (matrix
      3.11/3.12/3.13/3.14 — preserves the cascor-client 3.11 floor;
      same shape as data-client) — **`f7b4cfd`**.
- [x] juniper-cascor-worker: add `integration-tests` job —
      **`a1ae19b`**.
- [x] juniper-ml: promote `pre-commit` and `tests` jobs to a Python
      `3.12 / 3.13 / 3.14` matrix — **`2eabb34`**.

### Phase 3 — Pre-commit additions

- [x] juniper-ml: add `black` 26.3.1 + `isort` 5.13.2 + `mypy`
      v1.13.0 (mirrors-mypy) hooks scoped to
      `^(scripts|tests)/.*\.py$`, plus the auto-format pass on
      `scripts/cleanup_session_worktrees.py` and
      `tests/test_worktree_cleanup.py` — **`ad2f5bb`**.
- [x] juniper-data: add `markdownlint` v0.42.0 + project-local
      `.markdownlint.yaml` (with `MD040` initially disabled so
      pre-existing bare-fence markdown didn't churn) — **`64e6d13`**.
- [x] juniper-deploy: add `markdownlint` v0.42.0; folded in real
      `MD056/table-column-count` fix on `AGENTS.md` —
      **`d8d0dc1`**.

### Phase 4 — `pyproject.toml` `[tool.*]`

- [x] juniper-ml: declare `[tool.black]` (line-length=512,
      target-version=py312), `[tool.isort]` (profile=black,
      known_first_party=["scripts","tests"]), `[tool.mypy]`
      (python_version=3.12, ignore-missing-imports,
      no-strict-optional, files=["scripts","tests"]),
      `[tool.coverage.run]` (branch=true, source=["scripts","tests"]),
      `[tool.coverage.report]` (no fail-under, intentional per
      Phase 4 framing) — **`036f747`**.

---

### Roll-out summary

**17 commits across 8 repositories. Zero PRs.** Every commit went
direct-to-`main` on its respective repo and is reachable from
`origin/main` (verified by
`git rev-list --left-right --count origin/main...HEAD` returning
`0 0` in every repo on 2026-04-29).

---

## Appendix A — by-design exclusions

| Repo                  | Excluded from baseline                            | Reason                                                                                                                      |
|-----------------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| juniper-ml            | `scheduled-tests.yml`                             | Meta-package owns no application code; the regression suite is exhaustive enough that a daily slow run adds no signal.      |
| juniper-deploy        | `codeql.yml`                                      | No Python or JS source — only shell, YAML, and helm. SAST is not meaningful; trivy / hadolint cover the actual surface.     |
| juniper-deploy        | `unit-tests`, `integration-tests`, coverage gate, | Infrastructure-only repo. Validation is via `docker compose config`, `helm lint`, SOPS integrity, and shellcheck.           |
|                       | -- `mypy`, `bandit`, `flake8` / `ruff`            |                                                                                                                             |
| juniper-deploy        | `dependency-docs` job,                            | No `pyproject.toml` and no pinned Python lockfile to render or refresh.                                                     |
|                       | -- `lockfile-update.yml`                          | -- The Docker images consumed by `compose` are the actual dependency surface;                                               |
|                       |                                                   | -- those are tracked by Dependabot's `docker` ecosystem and the `trivy` step proposed in §7.5.                              |
| juniper-cascor-client | Python 3.11 in the matrix (and only here)         | The client is held to `>=3.11` so older deployments can integrate;                                                          |
|                       |                                                   | -- the rest of the fleet is `>=3.12`. Do not lower other repos' minimum to match; do not raise this one's minimum to match. |

---

## Appendix B — validation pass log

The plan was validated on **2026-04-29** by directly re-running the
discovery commands in [Appendix C](#appendix-c--verbatim-discovery-commands)
against every repo and cross-checking the gap matrix.

### Findings (all corrections folded into the body of the plan above)

1. **Pre-commit hook gaps re-verified by `grep -E '^\s*-\s*id:\s'`** — confirmed that:
   - juniper-ml lacks `black`, `isort`, `mypy`. Plan §5.2 was correct.
   - juniper-data lacks `markdownlint`. Plan §5.2 was correct.
   - juniper-deploy lacks `markdownlint`. Plan §5.2 was correct.
2. **CI job presence re-verified by `python3 -c 'yaml.safe_load(...)'`** — parsed each `ci.yml` and listed the keys under `jobs:`. Findings:
   - **Correction 1.** Plan §5.3 originally listed juniper-canopy as missing the `dependency-docs` job. juniper-canopy *does* have a `dependency-docs` job. The row in §5.3 and the bullet in §6.2 were corrected.
   - **Correction 2.** Plan §5.3 originally claimed juniper-ml's tests "piggy-back on the pre-commit job." juniper-ml has a dedicated `tests` job; the real gap is that both `pre-commit` and `tests` run on a single Python (3.12) instead of the fleet matrix. Row and Phase-2 checklist were corrected.
   - **Correction 3.** juniper-ml *does* have a `dependency-docs` job — the plan never claimed otherwise, but the validation pass made that explicit in §5.3 to prevent future misinterpretation.
3. **Workflow file presence re-verified by direct `test -f` enumeration** — confirmed that:
   - Only juniper-ml ships `claude.yml`. The other 7 repos lack it.
   - Only juniper-data ships `codeql.yml`.
   - Only juniper-cascor ships `scheduled-tests.yml`.
   - juniper-deploy is the only repo without any `security-scan.yml`.
   - No corrections needed for §5.1.
4. **By-design exclusions sanity-checked** — Findings:
   - juniper-deploy has no `pyproject.toml`; confirmed no Python surface to type-check or lint with `ruff`/`flake8`/`mypy`.  Appendix A was extended with an explicit `dependency-docs` / `lockfile-update.yml` exclusion to match.
   - juniper-cascor-client's Python 3.11 floor was confirmed by reading its `requires-python` in `pyproject.toml`.

### Open follow-ups

- The plan does not yet specify per-repo `ANTHROPIC_API_KEY` secret ownership. Confirm at the org level (`pcalnon`) before the Phase 1 rollout so that `claude.yml` runs do not 401 on first dispatch.
- §7.5 proposes `trivy` for juniper-deploy. Verify that the trivy GitHub action's `severity: HIGH,CRITICAL` policy lines up with juniper-deploy's tolerance for base-image CVEs **before** treating the new job as a required check; a soft-fail shakedown cycle (§9 risk register) is recommended.

---

## Appendix C — verbatim discovery commands

These are the commands used to build §3. Re-run before starting any phase to refresh the snapshot.

```bash
# 1. Workflow inventory across all 8 repos
for repo in juniper-ml juniper-canopy juniper-cascor juniper-data \
            juniper-data-client juniper-cascor-client \
            juniper-cascor-worker juniper-deploy; do
    echo "=== $repo ==="
    ls /home/pcalnon/Development/python/Juniper/$repo/.github/workflows/ \
        2>/dev/null | sort
done

# 2. Per-file presence audit
for repo in <list>; do
    for f in claude.yml codeql.yml security-scan.yml scheduled-tests.yml \
             lockfile-update.yml; do
        echo -n "$repo/$f: "
        test -f /home/pcalnon/Development/python/Juniper/$repo/.github/workflows/$f \
            && echo YES || echo NO
    done
done

# 3. Pre-commit hooks per repo
for repo in <list>; do
    grep -E '^\s*-?\s*id:\s' \
        /home/pcalnon/Development/python/Juniper/$repo/.pre-commit-config.yaml
done

# 4. Coverage gates per repo
grep -RnE 'fail[-_]under|--cov-fail-under' \
    /home/pcalnon/Development/python/Juniper/*/pyproject.toml \
    /home/pcalnon/Development/python/Juniper/*/.github/workflows/ \
    2>/dev/null

# 5. Validate every workflow file with actionlint
find /home/pcalnon/Development/python/Juniper/*/.github/workflows -name '*.yml' \
    | xargs actionlint
```
