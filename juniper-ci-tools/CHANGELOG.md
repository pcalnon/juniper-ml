<!-- markdownlint-disable -->

# Changelog

All notable changes to `juniper-ci-tools` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
