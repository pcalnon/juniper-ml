"""Command-line entry point for :program:`juniper-generate-dep-docs`.

Wraps :func:`juniper_ci_tools.generate_dep_docs.generate_dep_docs` with
argparse and printed progress output that mirrors the legacy bash script's
banner. Supports two invocation forms:

- ``juniper-generate-dep-docs [args]`` (console script, see :file:`pyproject.toml`)
- ``python -m juniper_ci_tools [args]`` (module form, see :mod:`__main__`)

Both route through :func:`main`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from juniper_ci_tools._version import __version__
from juniper_ci_tools.generate_dep_docs import (
    GenerateDepDocsError,
    YamlValidationError,
    generate_dep_docs,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-generate-dep-docs",
        description=("Generate conf/requirements_ci.txt and conf/conda_environment_ci.yaml for a Juniper repo. Replaces the legacy scripts/generate_dep_docs.sh that drifted across 8 repos."),
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Repo root containing pyproject.toml (default: cwd).")
    parser.add_argument("--conf-dir", default="conf", help="Output directory for generated files (default: conf).")
    parser.add_argument("--notes-dir", default="notes", help="Directory containing header templates (default: notes).")
    parser.add_argument("--pip-header", default="PIP_DEPENDENCY_FILE_HEADER.md", help="Pip-requirements header template filename (in --notes-dir).")
    parser.add_argument("--conda-header", default="CONDA_DEPENDENCY_FILE_HEADER.md", help="Conda-environment header template filename (in --notes-dir).")
    parser.add_argument("--pip-filename", default="requirements_ci.txt", help="Output filename for pip requirements (in --conf-dir).")
    parser.add_argument("--conda-filename", default="conda_environment_ci.yaml", help="Output filename for conda environment (in --conf-dir).")
    parser.add_argument("--no-conda", action="store_true", help="Skip conda_environment_ci.yaml generation even if conda is available.")
    parser.add_argument("--no-yaml-validation", action="store_true", help="Skip the post-write YAML validation of the conda environment file.")
    parser.add_argument("--version", action="version", version="juniper-generate-dep-docs {}".format(__version__))
    return parser


def _print_banner(args: argparse.Namespace, *, repo_version: str, python_version: str, pip_version: str, timestamp: str) -> None:
    bar = "═" * 60
    print("╔{}╗".format(bar))
    print("║       Juniper - Generate Dependency Documentation          ║")
    print("╚{}╝".format(bar))
    print()
    print("  Repo Version:   {}".format(repo_version))
    print("  Python Version: {}".format(python_version))
    print("  Pip Version:    {}".format(pip_version))
    print("  Timestamp:      {}".format(timestamp))
    print()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        # Detect versions early so we can print the banner even if the
        # generation step fails on something later. We re-detect inside
        # generate_dep_docs() so the result remains the source of truth.
        from juniper_ci_tools.generate_dep_docs import (
            _detect_pip_version,
            _detect_python_version,
            _now,
            _read_pyproject_version,
        )

        root = Path(args.repo_root) if args.repo_root is not None else Path.cwd()
        repo_version = _read_pyproject_version(root)
        python_version = _detect_python_version()
        pip_version = _detect_pip_version()
        ts = _now().strftime("%Y-%m-%d_%H-%M-%S")
        _print_banner(args, repo_version=repo_version, python_version=python_version, pip_version=pip_version, timestamp=ts)

        result = generate_dep_docs(
            repo_root=args.repo_root,
            conf_dir=args.conf_dir,
            notes_dir=args.notes_dir,
            pip_header_name=args.pip_header,
            conda_header_name=args.conda_header,
            pip_filename=args.pip_filename,
            conda_filename=args.conda_filename,
            include_conda=not args.no_conda,
            validate_yaml=not args.no_yaml_validation,
        )

        if result.pip_backup is not None:
            print("  Backing up existing pip requirements to: {}".format(result.pip_backup))
        print("  Generated: {}".format(result.pip_file))

        if result.conda_file is not None:
            if result.conda_backup is not None:
                print("  Backing up existing conda environment to: {}".format(result.conda_backup))
            if result.yaml_validated:
                print("  Validated: {} YAML syntax OK".format(result.conda_file))
            print("  Generated: {}".format(result.conda_file))
        elif result.conda_skipped_reason:
            print("  WARNING: {}".format(result.conda_skipped_reason))
            print("           Install miniforge/miniconda to generate conda_environment_ci.yaml")

        print()
        print("  Dependency documentation generation complete.")
        return 0
    except YamlValidationError as exc:
        print("  ERROR: {}".format(exc), file=sys.stderr)
        return 1
    except GenerateDepDocsError as exc:
        print("  ERROR: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
