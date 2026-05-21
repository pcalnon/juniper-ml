<!-- markdownlint-disable -->

# Changelog

All notable changes to `juniper-ci-tools` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
