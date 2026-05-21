"""Command-line entry point for :program:`juniper-lint-agents-md-version`.

Wraps :func:`juniper_ci_tools.lint_agents_md_version.lint_agents_md_version`
with argparse and a small text / JSON reporter so the lint can run
directly from CI without going through the unittest runner.

Usage::

    juniper-lint-agents-md-version              # auto-discover repo root
    juniper-lint-agents-md-version --repo-root /path/to/repo
    juniper-lint-agents-md-version --exit-zero  # report drift, exit 0
    juniper-lint-agents-md-version --json       # machine-readable output

Exit codes:
    0 -- versions match (or AGENTS.md is opted out, or ``--exit-zero``)
    1 -- versions drift
    2 -- structural problem (missing files, multiple headers, missing
         pyproject ``[project].version`` key)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from juniper_ci_tools._version import __version__
from juniper_ci_tools.lint_agents_md_version import (
    MultipleVersionHeadersError,
    RepoRootNotFoundError,
    lint_agents_md_version,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-lint-agents-md-version",
        description=("Lint that AGENTS.md `**Version**:` header matches pyproject.toml [project].version. Fails when they drift."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=("Explicit repo-root directory. When omitted, the repo root is auto-discovered by walking up from the current working directory looking for the first ancestor that contains both pyproject.toml and AGENTS.md."),
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Report drift but always exit 0 (still exits 2 on structural errors).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the default text report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"juniper-lint-agents-md-version {__version__}",
    )
    return parser


def _emit_json(result_dict: dict, stream) -> None:
    json.dump(result_dict, stream, indent=2, default=str)
    stream.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns the exit code (no SystemExit raised)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = lint_agents_md_version(repo_root=args.repo_root)
    except RepoRootNotFoundError as exc:
        msg = f"ERROR: {exc}"
        if args.json:
            _emit_json({"error": "repo_root_not_found", "message": str(exc)}, sys.stderr)
        else:
            print(msg, file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        msg = f"ERROR: {exc}"
        if args.json:
            _emit_json({"error": "file_not_found", "message": str(exc)}, sys.stderr)
        else:
            print(msg, file=sys.stderr)
        return 2
    except MultipleVersionHeadersError as exc:
        msg = f"ERROR: {exc}"
        if args.json:
            _emit_json({"error": "multiple_version_headers", "message": str(exc)}, sys.stderr)
        else:
            print(msg, file=sys.stderr)
        return 2
    except KeyError as exc:
        msg = f"ERROR: {exc}"
        if args.json:
            _emit_json({"error": "missing_pyproject_version", "message": str(exc)}, sys.stderr)
        else:
            print(msg, file=sys.stderr)
        return 2

    if args.json:
        _emit_json(
            {
                "repo_root": str(result.repo_root),
                "pyproject_path": str(result.pyproject_path),
                "agents_md_path": str(result.agents_md_path),
                "pyproject_version": result.pyproject_version,
                "agents_md_version": result.agents_md_version,
                "in_sync": result.in_sync,
                "is_drift": result.is_drift,
            },
            sys.stdout,
        )
    else:
        print(result.render())

    if result.is_drift and not args.exit_zero:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
