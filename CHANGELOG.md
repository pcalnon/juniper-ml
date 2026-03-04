# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-03-03

### Security

- Enabled build attestations in publish workflow (`attestations: true`)

### Added

- `.github/workflows/security-scan.yml` — Weekly scheduled security scanning (Bandit, pip-audit)
- `notes/SECURITY_AUDIT_PLAN.md` — Cross-ecosystem security audit documentation (24 findings, 7 phases, 7 repos)

### Technical Notes

- **SemVer impact**: PATCH — CI/CD and documentation only; no package changes
- **Part of**: Cross-ecosystem security audit (7 repos, 24 findings)

## [0.2.0] - 2026-02-27

### Added

- CLAUDE.md for Claude Code onboarding
- PyPI publishing procedure documentation (`notes/pypi-publish-procedure.md`)

### Changed

- Renamed package from `juniper` to `juniper-ml`
- Raised minimum Python version to `>=3.12`
- Expanded keywords in package metadata

### Fixed

- Added `attestations: false` to publish.yml for both TestPyPI and PyPI steps

## [0.1.0] - 2026-02-22

### Added

- Initial `juniper` meta-package with `pyproject.toml`
- Optional dependency extras: `clients`, `worker`, `all`
- GitHub Actions CI/CD publish workflow (TestPyPI + PyPI with trusted publishing)
- README with installation instructions and ecosystem overview
- MIT License

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/pcalnon/juniper-ml/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
