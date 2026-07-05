<!-- markdownlint-disable -->

# Changelog

All notable changes to `juniper-config-tools` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] -- 2026-05-22

Initial release — Wave 0 of the
[juniper-config-tools PyPI migration plan](https://github.com/pcalnon/juniper-ml/blob/main/notes/JUNIPER_2026-05-22_JUNIPER-ML_CONFIG-TOOLS-PYPI-MIGRATION-PLAN.md).

### Added

- `juniper_config_tools.env_with_legacy_alias(new_name, legacy_name=None, default=None) -> str | None` —
  stdlib-only helper that reads an env var's canonical name first and
  falls back to a legacy alias while emitting one `DeprecationWarning`
  whose message names both env vars. Single public function in 0.1.0;
  multi-hop / variadic legacy aliases are deferred to a future minor.
- `python -m juniper_config_tools --version` module-form invocation
  (parity with sibling `juniper-ci-tools` / `juniper-doc-tools`
  packages). No other CLI in 0.1.0.
- 14 regression tests covering the four env-state branches × empty-
  string edge cases × `legacy_name=None` mode × public-import sanity
  × `stacklevel=2` filename attribution.
- MIT license, PyPI metadata, OIDC trusted-publishing release pipeline.

### Design notes

- **Stdlib-only by policy.** Runtime deps: none. Test deps: `pytest`,
  `pytest-cov`. This is a hard constraint: the package exists because
  `juniper-cascor-worker` cannot adopt `juniper-observability`
  (which requires pydantic) without breaking its
  `tests/test_no_pydantic_at_runtime.py` invariant.
- **Once-per-location warnings.** Uses Python's default warning filter
  (once per file:line) — callers in loops don't spam.
- **`stacklevel=2`** so warnings report the caller's filename, not
  the helper's internal location.
- **Narrow API on purpose.** Resist over-design on a single helper;
  add functions only when a real second consumer needs them.
