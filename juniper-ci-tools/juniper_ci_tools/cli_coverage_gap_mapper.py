"""Command-line entry point for :program:`juniper-coverage-gap-map`.

Wraps :mod:`juniper_ci_tools.coverage_gap_mapper` with argparse and a small
text / JSON reporter so the per-file coverage-gap mapper can run directly from
CI, a Juniper agent, or a shell. **Advisory by default; enforcing is opt-in.**

Two inputs (the JSON path is primary)::

    # Parse a pre-generated coverage.json (primary, deterministic):
    juniper-coverage-gap-map --coverage-json coverage.json

    # Run a repo's real test command under coverage first (secondary):
    juniper-coverage-gap-map --repo-root . --package my_pkg \\
        --test-command "python -m pytest"

    juniper-coverage-gap-map --coverage-json coverage.json --json   # machine output
    python -m juniper_ci_tools.cli_coverage_gap_mapper --coverage-json coverage.json

Enforcing mode (opt-in; work-unit C-0 of the per-file coverage rollout,
``notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md``)::

    # Exit 1 if any source file's STATEMENT coverage < 90 OR any sub-module's
    # POOLED coverage < 95; exit 0 when clean. Thresholds are tunable and
    # --omit excludes thin shims (e.g. __main__.py) before gating.
    juniper-coverage-gap-map --coverage-json coverage.json --enforce \\
        --fail-under-file 90 --fail-under-submodule 95 --omit '*/__main__.py'

The enforcing gate deliberately uses different bases than the advisory display:
per-file gates on **statement** coverage (not the branch-inclusive
``percent_covered`` shown in the report) and per-sub-module gates on the
**pooled** statement-weighted figure (not the mean-of-files average shown in
the report). See :mod:`juniper_ci_tools.coverage_gap_mapper` for the rationale.

Exit codes:
    0 -- ADVISORY (default): a report was produced. **Always**, regardless of
         how many files are below the threshold or sub-modules under the bar --
         the default mode never fails a build on coverage findings.
         ENFORCING (``--enforce``): the gate is clean (every retained file's
         statement coverage >= ``--fail-under-file`` and every sub-module's
         pooled coverage >= ``--fail-under-submodule``).
    1 -- ENFORCING only: at least one retained file or sub-module is under its
         floor. Never returned without ``--enforce``.
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
    FileCoverage,
    SubmoduleCoverage,
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
        "--enforce",
        action="store_true",
        help="Enforcing mode (opt-in): exit 1 if any source file's STATEMENT coverage is below --fail-under-file OR any sub-module's POOLED (statement-weighted) coverage is below --fail-under-submodule; exit 0 when clean. Default (without this flag) is advisory -- exit 0 always.",
    )
    parser.add_argument(
        "--fail-under-file",
        type=float,
        default=DEFAULT_FILE_THRESHOLD,
        help="Enforcing per-file STATEMENT-coverage floor (default: %(default)s). Only used with --enforce; independent of the advisory --file-threshold display cut.",
    )
    parser.add_argument(
        "--fail-under-submodule",
        type=float,
        default=DEFAULT_SUBMODULE_BAR,
        help="Enforcing per-sub-module POOLED-coverage bar (default: %(default)s). Only used with --enforce; independent of the advisory --submodule-bar display bar.",
    )
    parser.add_argument(
        "--omit",
        action="append",
        default=None,
        metavar="GLOB",
        help="Exclude files matching this fnmatch glob from the report AND the gate, applied to the parsed coverage.json before aggregation/gating (repeatable). E.g. --omit '*/__main__.py' to drop thin CLI shims per the excluded-files policy.",
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
        return load_coverage_json(args.coverage_json, file_threshold=args.file_threshold, submodule_bar=args.submodule_bar, omit=args.omit)
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
            omit=args.omit,
        )
    raise ValueError('no input: pass --coverage-json PATH or --test-command "..." (with --package)')


def _enforcement_payload(fail_under_file: float, fail_under_submodule: float, files_below: Sequence[FileCoverage], submodules_below: Sequence[SubmoduleCoverage]) -> dict:
    """Machine-readable enforcement result merged into the ``--json`` output.

    Keeps the base report's JSON shape stable: this sub-object is only added
    under the ``"enforcement"`` key when ``--enforce`` is set.
    """
    return {
        "enforced": True,
        "fail_under_file": fail_under_file,
        "fail_under_submodule": fail_under_submodule,
        "basis": {"file": "statement", "submodule": "pooled"},
        "files_below": [
            {
                "path": f.path,
                "statement_percent": f.statement_percent,
                "covered_statements": f.covered_statements,
                "num_statements": f.num_statements,
            }
            for f in files_below
        ],
        "submodules_below": [
            {
                "name": s.name,
                "pooled_percent": s.pooled_percent,
                "covered_statements": s.covered_statements,
                "total_statements": s.total_statements,
            }
            for s in submodules_below
        ],
        "passed": not (files_below or submodules_below),
    }


def _render_enforcement(fail_under_file: float, fail_under_submodule: float, files_below: Sequence[FileCoverage], submodules_below: Sequence[SubmoduleCoverage]) -> str:
    """Human-readable enforcement verdict block (appended after the report).

    Names every offending file (statement %) and sub-module (pooled %) -- no
    silent truncation -- so the CI log shows exactly what must be lifted.
    """
    passed = not (files_below or submodules_below)
    verdict = "PASS" if passed else "FAIL"
    lines: list[str] = [f"Enforcing gate: {verdict}  (per-file statement >= {fail_under_file:.1f}%, sub-module pooled >= {fail_under_submodule:.1f}%)"]
    if files_below:
        lines.append(f"  Files below {fail_under_file:.1f}% statement ({len(files_below)}):")
        for f in files_below:
            lines.append(f"    {f.statement_percent:6.2f}%  {f.path}  ({f.covered_statements}/{f.num_statements})")
    if submodules_below:
        lines.append(f"  Sub-modules below {fail_under_submodule:.1f}% pooled ({len(submodules_below)}):")
        for s in submodules_below:
            lines.append(f"    {s.pooled_percent:6.2f}%  {s.name}  ({s.covered_statements}/{s.total_statements})")
    if passed:
        lines.append("  No files or sub-modules below the enforced thresholds.")
    return "\n".join(lines)


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

    # Enforcing gate (opt-in): STATEMENT basis per file, POOLED basis per
    # sub-module -- both distinct from the advisory display (see the mapper
    # module docstring). Computed once, reused by the reporter and the exit code.
    files_below: list[FileCoverage] = []
    submodules_below: list[SubmoduleCoverage] = []
    if args.enforce:
        files_below = report.files_below_statement_threshold(args.fail_under_file)
        submodules_below = report.submodules_below_pooled_bar(args.fail_under_submodule)

    if args.json:
        payload = report.to_dict()
        if args.enforce:
            payload["enforcement"] = _enforcement_payload(args.fail_under_file, args.fail_under_submodule, files_below, submodules_below)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(report.render())
        if args.enforce:
            print("")
            print(_render_enforcement(args.fail_under_file, args.fail_under_submodule, files_below, submodules_below))

    if args.enforce:
        # ENFORCING CONTRACT: exit 1 when any retained file's statement coverage
        # is under --fail-under-file OR any sub-module's pooled coverage is under
        # --fail-under-submodule; exit 0 when clean.
        return 1 if (files_below or submodules_below) else 0

    # ADVISORY CONTRACT (default): a report was produced, so exit 0 -- ALWAYS,
    # no matter how many files are below the threshold or sub-modules under the bar.
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
