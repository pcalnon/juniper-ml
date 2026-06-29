"""Command-line entry point for :program:`juniper-env-drift-check`.

Wraps :func:`juniper_ci_tools.env_drift_check.check_env_drift` with argparse and
a text/JSON reporter so the dependency-satisfaction check can run directly from
CI or a local preflight without going through a test runner.

Usage::

    juniper-env-drift-check                                  # scan the active interpreter against ./pyproject.toml
    juniper-env-drift-check --repo-root /path/to/repo
    juniper-env-drift-check --check-lock                     # also assert requirements.lock pins satisfy the floors
    juniper-env-drift-check --site-packages /env/lib/pythonX.Y/site-packages
    juniper-env-drift-check --strict                         # MISSING / lock-ABSENT also fail
    juniper-env-drift-check --json                           # machine-readable output

Exit codes:
    0 -- no BELOW_FLOOR (and, under --strict, no MISSING / ABSENT)
    1 -- at least one BELOW_FLOOR (or a --strict MISSING / ABSENT)
    2 -- usage error (no pyproject.toml, no juniper-* floors, or --check-lock with no lockfile)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from juniper_ci_tools._version import __version__
from juniper_ci_tools.env_drift_check import DriftCheckError, check_env_drift


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-env-drift-check",
        description=("Assert that the juniper-* distributions installed in the active environment (plain wheels included) satisfy the floors a target repo's pyproject.toml declares; with --check-lock, also assert its requirements.lock pins do."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Target repo whose pyproject.toml floors are the requirement (default: current directory).",
    )
    parser.add_argument(
        "--site-packages",
        action="append",
        metavar="DIR",
        type=Path,
        help="Scan this site-packages directory instead of the active interpreter (repeatable). Reads *.dist-info METADATA -- plain wheels and editable installs alike.",
    )
    parser.add_argument(
        "--check-lock",
        action="store_true",
        help="Also assert the repo's requirements.lock pins satisfy the floors.",
    )
    parser.add_argument(
        "--lock-file",
        type=Path,
        default=None,
        help="Override the lockfile path checked by --check-lock (default: <repo-root>/requirements.lock).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail (exit 1) on MISSING packages (and, with --check-lock, lockfile-ABSENT floors).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="juniper-env-drift-check {}".format(__version__),
    )
    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        print(f"error: --repo-root {repo_root} is not a directory", file=sys.stderr)
        return 2

    site_packages: "list[Path] | None" = None
    if args.site_packages:
        existing = [p for p in args.site_packages if p.is_dir()]
        if not existing:
            print("error: none of the --site-packages directories exist: " + ", ".join(str(p) for p in args.site_packages), file=sys.stderr)
            return 2
        site_packages = existing

    try:
        result = check_env_drift(
            repo_root,
            site_packages=site_packages,
            check_lock=args.check_lock,
            lock_path=args.lock_file,
            strict=args.strict,
        )
    except DriftCheckError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code

    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        print(result.report())

    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
