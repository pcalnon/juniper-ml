<!-- markdownlint-disable -->

# Changelog

All notable changes to `juniper-ci-tools` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] -- 2026-06-28

Adds the advisory per-file coverage-gap mapper as a fifth console script
(non-breaking; existing `juniper-generate-dep-docs`,
`juniper-lint-workflow-paths`, `juniper-lint-agents-md-version`, and
`juniper-lint-agents-md-header` callers are unaffected).

### Added

- `juniper_ci_tools.coverage_gap_mapper` — Python library that parses a
  `coverage json` (coverage.py / pytest-cov `--cov-report=json`) and emits
  three views: (a) the per-file coverage distribution (a histogram of file
  percentages), (b) the list of files below a threshold (default 90 %), and
  (c) each sub-module's average coverage vs a bar (default 95 %). A
  *sub-module* is the directory a file lives in. Public API:
  `FileCoverage`, `SubmoduleCoverage`, `CoverageReport`,
  `parse_coverage_json`, `load_coverage_json`, `run_coverage`,
  `package_cov_pytest_args`, `write_include_coverage_config`.
- `juniper-coverage-gap-map` console script (plus the
  `python -m juniper_ci_tools.cli_coverage_gap_mapper` module form). Supports
  **both** inputs: `--coverage-json PATH` parses a pre-generated report (the
  primary, deterministic path), and `--repo-root . --package PKG
  --test-command "..."` runs the repo's real test command under coverage
  first. Flags: `--include` (report-scoping glob, repeatable),
  `--file-threshold`, `--submodule-bar`, `--json`, `--version`.
- **Advisory-first posture (exit-code contract):** the CLI exits `0` whenever
  it produces a report — **always**, regardless of how many files are below
  the threshold or sub-modules are under the bar. It reports; it never fails a
  build on coverage findings. Exit `2` is reserved for structural / usage
  errors (no input, an unreadable or malformed `coverage.json`, a dotted
  `--package`). Promotion to a blocking per-file gate is a separate, per-repo,
  owner-signed decision.
- **numpy-2.x dotted-`--cov` shim (documented):** `package_cov_pytest_args`
  builds coverage invocations with the **package-form** `--cov=<package>` and
  scopes any narrowing through a `[report] include=` config written by
  `write_include_coverage_config` — never the dotted `--cov=pkg.submodule`
  form, which trips numpy 2.x's "cannot load module more than once per
  process" guard at pytest-cov startup (hit 2026-06-25, juniper-recurrence
  #70). The helper refuses a dotted package argument outright.
- 28 new tests under `tests/test_coverage_gap_mapper.py` driving synthetic
  `coverage.json` fixtures (no real coverage run): the per-file distribution,
  the strict `<90` list, the sub-module mean-vs-bar classification,
  exit-0-always, the full CLI exit-code matrix, JSON output shape, the
  package-form shim (including dotted-rejection), and the run-coverage path
  via a monkeypatched subprocess.

### Migration context

Hosts enhancement **E-4** of the juniper-ml custom-agent-suite enhancement
plan (`notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md`
§6.7, Phase-2 PR-6). Addresses the systemic gap surfaced by the 2026-06-26
ecosystem test-suite audit: no per-file coverage gate exists anywhere across
the Juniper repos. juniper-ml's own workflow pins (`ci.yml`,
`lockfile-update.yml`, `docs-full-check.yml`) are widened to admit 0.5.0 in
the same PR; the dogfood gate is `juniper-ml tests/test_coverage_gap_mapper_drift.py`.

## [0.4.0] -- 2026-05-22

Adds the AGENTS.md header-schema lint as a fourth console script
(non-breaking; existing `juniper-generate-dep-docs`,
`juniper-lint-workflow-paths`, and `juniper-lint-agents-md-version`
callers are unaffected).

### Added

- `juniper_ci_tools.lint_agents_md_header` — Python library that
  validates a repo's `AGENTS.md` header bullet block against the
  canonical six-field schema (`**Project**`, `**Repository**`,
  `**Author**`, `**License**`, `**Version**`, `**Last Updated**` in
  that relative order; each non-empty; `**Last Updated**` formatted
  as `YYYY-MM-DD`). Extra fields (e.g. `**Python**:`) are permitted
  and may be interleaved freely.
- `juniper-lint-agents-md-header` console script. Auto-discovers the
  repo root by walking up looking for `AGENTS.md` next to `.github/`
  (unlike the version-drift sibling, no `pyproject.toml` is
  required, so the lint applies to `juniper-deploy` as well).
  Supports `--repo-root`, `--exit-zero`, `--json`, `--version`. Exit
  codes: 0 (conformant), 1 (schema drift), 2 (structural error:
  missing AGENTS.md, repo root not found).
- Public API additions: `REQUIRED_FIELDS`,
  `AgentsMdHeaderLintResult`, `RepoRootNotFoundError`,
  `extract_header_bullets`, `find_agents_md_header_repo_root`,
  `lint_agents_md_header`.
- 24 new tests under `tests/test_lint_agents_md_header.py` covering
  walk-up discovery, header termination at `---` / `## `, missing /
  empty / mis-ordered required fields, freely-interleaved extras,
  bad `Last Updated` format, missing `AGENTS.md`, walk-up
  auto-discovery, and the full CLI exit-code matrix (including JSON
  output on success and drift).

### Migration context

This release is Phase 4 (per
`juniper-ml notes/AGENTS_MD_HEADER_STANDARDIZATION_PLAN_2026-05-22.md`)
of the AGENTS.md header standardization initiative kicked off in
juniper-ml#316. The canonical inline lint at
`juniper-ml tests/test_agents_md_header_schema.py` and the auto-bump
workflow at `juniper-ml .github/workflows/agents-md-touch-up.yml`
shipped first; this release packages the lint logic for ecosystem
fanout. Subsequent PRs in each sibling repo will bump the
`juniper-ci-tools>=...,<X.Y.Z` pin range to admit 0.4.0, adopt the
`juniper-lint-agents-md-header` invocation in `ci.yml`, copy the
`agents-md-touch-up.yml` workflow file, and bump `**Last Updated**`
to today.

## [0.3.0] -- 2026-05-21

Adds the AGENTS.md version-drift lint as a third console script
(non-breaking; existing `juniper-generate-dep-docs` and
`juniper-lint-workflow-paths` callers are unaffected).

### Added

- `juniper_ci_tools.lint_agents_md_version` — Python library that
  reads a repo's `AGENTS.md` `**Version**:` header and compares it to
  `pyproject.toml`'s `[project].version`. Catches the same drift class
  that motivated `juniper-ml#304` (pyproject 0.4.1 → 0.5.0 shipped
  while AGENTS.md stayed at 0.4.0 for 6 days).
- `juniper-lint-agents-md-version` console script. Auto-discovers the
  repo root by walking up looking for both `pyproject.toml` and
  `AGENTS.md`; supports `--repo-root`, `--exit-zero`, `--json`,
  `--version`. Exit codes: 0 (in sync OR opted out by omitting the
  header), 1 (drift), 2 (structural error: missing file, multiple
  headers, missing `[project].version` key).
- Public API additions: `AgentsMdLintResult`,
  `MultipleVersionHeadersError`, `RepoRootNotFoundError`,
  `find_agents_md_repo_root`, `lint_agents_md_version`.
- 18 new tests under `tests/test_lint_agents_md_version.py` covering
  in-sync detection, drift detection, opt-out (no header), multiple
  headers, missing files, missing pyproject `[project].version`,
  walk-up auto-discovery, full CLI exit-code matrix, and JSON output.

### Migration context

Replaces the byte-identical inline copies of
`util/test_agents_md_version_drift.py` that exist across 6 consumer
repos (juniper-canopy, juniper-cascor, juniper-cascor-client,
juniper-cascor-worker, juniper-data, juniper-data-client) plus
juniper-ml's `tests/test_agents_md_version_drift.py`. A follow-up
consumer-adoption PR series will swap the inline copies for
`pip install "juniper-ci-tools>=0.3.0,<0.4.0"` +
`juniper-lint-agents-md-version`.

## [0.2.0] -- 2026-05-21

Adds the workflow-script-path lint as a second console script
(non-breaking; existing `juniper-generate-dep-docs` callers are
unaffected).

### Added

- `juniper_ci_tools.lint_workflow_paths` — Python library that walks
  every `*.yml` / `*.yaml` file under a repo's `.github/workflows/`
  and validates that every `python <path.py>` / `bash <path.{sh,bash}>`
  invocation references a file that exists on disk. Catches the
  failure class that broke 3 juniper-X CIs on 2026-05-18 (script
  rename without workflow update).
- `juniper-lint-workflow-paths` console script. Auto-discovers the
  repo root via `.github/workflows/`; supports `--repo-root`,
  `--workflows-dir`, `--exit-zero`, `--json`, `--version`. Exit
  codes: 0 (clean), 1 (missing paths), 2 (repo root or workflows
  dir not discoverable).
- Public API additions: `LintResult`, `LintFinding`,
  `lint_workflow_paths`, `extract_script_paths`, `is_validatable`,
  `find_repo_root`, `DEFAULT_ECOSYSTEM_SIBLING_PREFIXES`.
- 23 new tests under `tests/test_lint_workflow_paths.py` covering
  extraction edge cases (YAML parse failure, multi-version python,
  bash invocations, unittest positional args), cross-repo prefix
  skipping with configurable sibling list, repo-root walk-up
  discovery, end-to-end lint runs against synthetic repos, and full
  CLI exit-code matrix including JSON output.

### Migration context

Replaces the 6 byte-identical copies of
`util/test_workflow_script_paths.py` that existed across consumer
repos. A future consumer-adoption PR series will swap the inline
copies for `pip install "juniper-ci-tools>=0.2.0,<0.3.0"` +
`juniper-lint-workflow-paths` (or `python3 -m unittest` of the
in-package test, depending on each repo's preferred runner).

## [0.1.0] -- 2026-05-20

Initial PyPI scaffold (Wave 0 of the `juniper-ci-tools` migration; plan doc
`notes/JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md` in the juniper-ml repo).

### Added

- `juniper_ci_tools.generate_dep_docs` -- Python port of the legacy
  `scripts/generate_dep_docs.sh` that drifted across 8 Juniper repos. The
  cascor 2026-05-20 awk-extraction fix is the canonical implementation;
  the pre-fix sed pipeline has been deliberately abandoned.
- `juniper-generate-dep-docs` console script and `python -m juniper_ci_tools`
  module form.
- `juniper_ci_tools.render_header` helper exposed for tests and ad-hoc
  callers; substitutes the historical `<X.Y.Z ...>`, `<YYYY-MM-dd ...>`,
  `<Python Version>`, `<Pip Version>` placeholders.
- 40+ pytest-based regression tests under `juniper-ci-tools/tests/` covering
  the awk-extraction fix (trailing `prefix:` / `variables:` exclusion,
  uppercase-key termination, nested pip indent preservation, empty inputs),
  end-to-end happy path, backup behavior, no-conda / no-validation paths,
  error cases (missing or malformed pyproject), and CLI exit codes.
- `ci-ci-tools.yml` and `publish-ci-tools.yml` GitHub Actions workflows in
  the juniper-ml repo (the package's home), mirroring the doc-tools
  precedent.
