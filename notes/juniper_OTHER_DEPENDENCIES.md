# Juniper - Other Dependencies

**Project**: Juniper
**Application**: juniper (meta-package)
**Last Updated**: 2026-02-25

---

## Overview

This document tracks dependencies that are **not** managed by pip or conda/mamba.
For pip-managed dependencies, see `conf/requirements_ci.txt`.
For conda/mamba-managed dependencies, see `conf/conda_environment_ci.yaml`.

---

## Build & Packaging Tools

| Dependency | Version | Management Method | Purpose |
|------------|---------|-------------------|---------|
| build | >=1.0.0 | pip | Python package builder (`python -m build`) |
| twine | >=4.0.0 | pip | Package upload/validation for PyPI |
| setuptools | >=61.0 | pip | Build backend (declared in pyproject.toml) |
| wheel | latest | pip | Wheel format support |

## CI/CD Dependencies

| Dependency | Version | Management Method | Purpose |
|------------|---------|-------------------|---------|
| GitHub Actions | N/A | github | CI/CD platform |
| actions/checkout | v4 | github-action | Repository checkout |
| actions/setup-python | v5 | github-action | Python environment setup |
| actions/upload-artifact | v4 | github-action | CI artifact storage |
| conda-incubator/setup-miniconda | v3 | github-action | Conda/Miniforge setup in CI |
| pypa/gh-action-pypi-publish | release/v1 | github-action | PyPI trusted publishing |

## Development Tools

| Dependency | Version | Management Method | Purpose |
|------------|---------|-------------------|---------|
| git | >=2.30 | apt / system | Version control |
| conda / mamba | latest | miniforge3 | Environment management |

## Notes

- This is a meta-package with no source code; dependencies are minimal.
- The shared `JuniperPython` conda environment is managed at the ecosystem level.
- See the parent `CLAUDE.md` at `/home/pcalnon/Development/python/Juniper/CLAUDE.md` for the full ecosystem dependency graph.
