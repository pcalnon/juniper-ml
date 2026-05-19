# Changelog

All notable changes to the `juniper-doc-tools` package are documented in this
file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-05-19

### Fixed

- CLI summary line "FOUND N broken link(s) in M file(s)" -- the M count
  now matches the inline-script behavior it replaced. The 0.1.0 CLI
  estimated M by string-deduping error prefixes, which double-counted
  any markdown file that had *both* a broken-anchor error (prefixed
  with the absolute ``Path``) and a broken-link error (prefixed with
  the path relative to ``repo_root``). The count is now tracked at
  iteration time in :func:`validate_directory` and exposed on
  :class:`ValidationResult` as the new ``files_with_errors`` attribute.
- Programmatic consumers gain access to the file count via
  ``ValidationResult.files_with_errors`` (additive; existing fields
  unchanged).

No behavioral change beyond the summary line: the per-error output and
the exit code are unchanged.

## [0.1.0] - 2026-05-18

### Added

- **First public release.** Packages the Juniper documentation link
  validator (previously a per-repo `scripts/check_doc_links.py` script) as
  a single PyPI distribution with a stable CLI surface and a small Python
  library API.
- `juniper-check-doc-links` console script (plan §8.2).
- `python -m juniper_doc_tools` module-form invocation (plan §8.3).
- `--strict-repo-boundary` flag for opt-out of ecosystem-root link
  classification (plan §3.4.1 / §8.4). Default is off; ecosystem-root
  links like `../../CLAUDE.md` are subject to the `--cross-repo` policy.
- `--repo-root` flag for explicit repository-root resolution (helpful in
  CI matrix runners that may not run from the repo root).
- `--version` flag for printing the package version.
- Public library API: `ValidationResult` dataclass, `validate_directory`,
  `validate_file`, `discover_ecosystem_root`.
- Constants and regex helpers extracted into a separate
  `juniper_doc_tools._ecosystem` module (`ECOSYSTEM_REPOS`,
  `ECOSYSTEM_ROOT_ITEMS`, `CROSS_REPO_PATTERN`, `ECOSYSTEM_ROOT_PATTERN`,
  `CROSS_REPO_MODES`, `MAX_TRAVERSAL_DEPTH`) so future ecosystem-wide
  tools can reuse them.

### Behavior parity with `juniper-ml/util/check_doc_links.py` v0.7.0

This first release is **functionally equivalent** to the v0.7.0 standalone
script that shipped on 2026-05-18 to fix the immediate CI failure. The
only intentional behavior addition is the `--strict-repo-boundary` flag;
default-on ecosystem-root classification is unchanged.

### Notes

- Pure stdlib; no runtime dependencies.
- Tests use pytest (plan §8.1) for parity with the rest of the Juniper
  ecosystem.
