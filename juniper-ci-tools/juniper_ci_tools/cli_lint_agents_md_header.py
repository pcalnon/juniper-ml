"""Command-line entry point for :program:`juniper-lint-agents-md-header`.

Wraps :func:`juniper_ci_tools.lint_agents_md_header.lint_agents_md_header`
with argparse and a small text / JSON reporter so the lint can run
directly from CI without going through the unittest runner.

Usage::

    juniper-lint-agents-md-header              # auto-discover repo root
    juniper-lint-agents-md-header --repo-root /path/to/repo
    juniper-lint-agents-md-header --exit-zero  # report drift, exit 0
    juniper-lint-agents-md-header --json       # machine-readable output

Exit codes:
    0 -- schema is conformant (or ``--exit-zero``)
    1 -- schema drift detected
    2 -- structural problem (missing AGENTS.md, repo root not found)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from juniper_ci_tools._version import __version__
from juniper_ci_tools.lint_agents_md_header import (
    RepoRootNotFoundError,
    lint_agents_md_header,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-lint-agents-md-header",
        description=("Lint that AGENTS.md's header bullet block conforms to the canonical schema: Project, Repository, Author, License, Version, Last Updated (in that relative order), each non-empty, with Last Updated formatted as YYYY-MM-DD. Extra fields are permitted and may be interleaved freely."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=("Explicit repo-root directory. When omitted, the repo root is auto-discovered by walking up from the current working directory looking for the first ancestor that contains AGENTS.md next to .github/."),
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
        version=f"juniper-lint-agents-md-header {__version__}",
    )
    return parser


def _emit_json(payload: dict, stream) -> None:
    json.dump(payload, stream, indent=2, default=str)
    stream.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns the exit code (no SystemExit raised)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = lint_agents_md_header(repo_root=args.repo_root)
    except RepoRootNotFoundError as exc:
        if args.json:
            _emit_json({"error": "repo_root_not_found", "message": str(exc)}, sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        if args.json:
            _emit_json({"error": "file_not_found", "message": str(exc)}, sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        _emit_json(
            {
                "repo_root": str(result.repo_root),
                "agents_md_path": str(result.agents_md_path),
                "bullets": [list(b) for b in result.bullets],
                "missing_fields": list(result.missing_fields),
                "order_violations": list(result.order_violations),
                "empty_value_fields": list(result.empty_value_fields),
                "bad_last_updated_value": result.bad_last_updated_value,
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
