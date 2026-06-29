"""Command-line entry point for :program:`juniper-coverage-gap-map`.

Wraps :mod:`juniper_ci_tools.coverage_gap_mapper` with argparse and a small
text / JSON reporter so the advisory per-file coverage-gap mapper can run
directly from CI, a Juniper agent, or a shell.

Two inputs (the JSON path is primary)::

    # Parse a pre-generated coverage.json (primary, deterministic):
    juniper-coverage-gap-map --coverage-json coverage.json

    # Run a repo's real test command under coverage first (secondary):
    juniper-coverage-gap-map --repo-root . --package my_pkg \\
        --test-command "python -m pytest"

    juniper-coverage-gap-map --coverage-json coverage.json --json   # machine output
    python -m juniper_ci_tools.cli_coverage_gap_mapper --coverage-json coverage.json

Exit codes (advisory contract):
    0 -- a report was produced. **Always**, regardless of how many files are
         below the threshold or how many sub-modules are under the bar. The
         mapper is advisory: it never fails a build on coverage findings.
    2 -- a structural / usage error: no input given, an unreadable or
         malformed ``coverage.json``, or a dotted ``--package`` (the numpy-2.x
         dotted-``--cov`` shape the shim forbids).
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Optional, Sequence

from juniper_ci_tools._version import __version__
from juniper_ci_tools.coverage_gap_mapper import (
    DEFAULT_FILE_THRESHOLD,
    DEFAULT_SUBMODULE_BAR,
    CoverageReport,
    load_coverage_json,
    run_coverage,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-coverage-gap-map",
        description=("Advisory per-file coverage-gap mapper: emit the per-file coverage distribution, the files below a threshold (default 90%%), and each sub-module's average vs a bar (default 95%%). Exit 0 always (advisory) -- it reports, it never fails a build."),
    )
    parser.add_argument(
        "--coverage-json",
        type=Path,
        default=None,
        help="Parse a pre-generated coverage.json directly (the primary path).",
    )
    parser.add_argument(
        "--test-command",
        type=str,
        default=None,
        help="Run this pytest command under coverage first, then parse the JSON it writes (secondary path). Requires --package.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Working directory for --test-command (default: current directory).",
    )
    parser.add_argument(
        "--package",
        type=str,
        default=None,
        help="Top-level package to measure with the package-form --cov shim (required with --test-command; must not be dotted).",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=None,
        metavar="GLOB",
        help="Report-scoping [report] include= glob for --test-command (repeatable); the numpy-2.x-safe way to narrow to a submodule.",
    )
    parser.add_argument(
        "--file-threshold",
        type=float,
        default=DEFAULT_FILE_THRESHOLD,
        help="Percent below which a file is listed as a gap (default: %(default)s).",
    )
    parser.add_argument(
        "--submodule-bar",
        type=float,
        default=DEFAULT_SUBMODULE_BAR,
        help="Percent a sub-module average must reach (default: %(default)s).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the default text report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"juniper-coverage-gap-map {__version__}",
    )
    return parser


def _resolve_report(args: argparse.Namespace) -> CoverageReport:
    """Build the report from whichever input was supplied.

    Raises:
        ValueError: usage errors (no input, --test-command without --package,
            dotted package) and are mapped to exit 2 by :func:`main`.
        FileNotFoundError / json.JSONDecodeError: structural input errors,
            also mapped to exit 2.
    """
    if args.coverage_json is not None:
        return load_coverage_json(args.coverage_json, file_threshold=args.file_threshold, submodule_bar=args.submodule_bar)
    if args.test_command is not None:
        if not args.package:
            raise ValueError("--package is required when using --test-command")
        return run_coverage(
            shlex.split(args.test_command),
            repo_root=args.repo_root if args.repo_root is not None else Path.cwd(),
            package=args.package,
            include=args.include,
            file_threshold=args.file_threshold,
            submodule_bar=args.submodule_bar,
        )
    raise ValueError('no input: pass --coverage-json PATH or --test-command "..." (with --package)')


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns the exit code (no SystemExit raised)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        report = _resolve_report(args)
    except FileNotFoundError as exc:
        print(f"error: coverage.json not found: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: malformed coverage.json: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.render())

    # ADVISORY CONTRACT: a report was produced, so exit 0 -- ALWAYS, no matter
    # how many files are below the threshold or sub-modules are under the bar.
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
