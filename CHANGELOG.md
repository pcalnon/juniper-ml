# Changelog

All notable changes to the `juniper-ml` meta-package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CLAUDE.md for Claude Code onboarding
- PyPI publishing procedure documentation (`notes/pypi-publish-procedure.md`)

### Changed

- Renamed package from `juniper` to `juniper-ml`
- Raised minimum Python version to `>=3.12`
- Expanded keywords in package metadata

## [0.1.0] - 2026-02-22

### Added

- Initial `juniper` meta-package with `pyproject.toml`
- Optional dependency extras: `clients`, `worker`, `all`
- GitHub Actions CI/CD publish workflow (TestPyPI + PyPI with trusted publishing)
- README with installation instructions and ecosystem overview
- MIT License

[Unreleased]: https://github.com/pcalnon/juniper-ml/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pcalnon/juniper-ml/releases/tag/v0.1.0
