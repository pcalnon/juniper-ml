"""Command-line entry point for :program:`juniper-check-doc-links`.

Wraps :func:`juniper_doc_tools.check_doc_links.validate_directory` with
argparse and printed progress output. Supports two invocation forms:

- ``juniper-check-doc-links [args]`` (console script, see :file:`pyproject.toml`)
- ``python -m juniper_doc_tools [args]`` (module form, see :mod:`__main__`)

Both route through :func:`main`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from juniper_doc_tools._ecosystem import CROSS_REPO_MODES
from juniper_doc_tools._version import __version__
from juniper_doc_tools.check_doc_links import (
    discover_ecosystem_root,
    validate_directory,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-check-doc-links",
        description=("Validate internal links in Juniper repo markdown documentation. Returns 0 if all links are valid, 1 if any are broken or arguments are invalid."),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Directories or files to scan (default: repository root)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help=("Directory name to exclude from scanning. May be passed multiple times. Examples: templates, history, legacy."),
    )
    parser.add_argument(
        "--cross-repo",
        choices=sorted(CROSS_REPO_MODES),
        default="check",
        help=("How to handle cross-repo links and ecosystem-root links: 'skip' (silent, default for CI), 'warn' (print but do not fail), 'check' (validate via filesystem; requires sibling repos on disk)."),
    )
    parser.add_argument(
        "--strict-repo-boundary",
        action="store_true",
        help=(
            "Disable ecosystem-root link classification. With this flag set, links like ../../CLAUDE.md or ../../notes/X.md are flagged as 'outside repository boundary' instead of being subject to the --cross-repo policy. Use this when a repo wants stricter validation than the ecosystem-wide default. Off by default."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        metavar="PATH",
        help=("Repository root for resolving paths. Defaults to the current working directory."),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every link checked (debug output).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run documentation link validation.

    Args:
        argv: Optional list of arguments (for testing). When None, reads
            from ``sys.argv[1:]``.

    Returns:
        0 if all links are valid, 1 if broken links are found or arguments
        are invalid.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or Path.cwd()).resolve()
    exclude_dirs = set(args.exclude)
    cross_repo_mode = args.cross_repo

    search_paths = [repo_root / a for a in args.paths] if args.paths else [repo_root]

    ecosystem_root = None
    if cross_repo_mode == "check":
        ecosystem_root = discover_ecosystem_root(repo_root)
        if ecosystem_root is None:
            print("WARNING: Ecosystem root not found. Cross-repo links will be skipped.")
            print("  (Ensure sibling repos are checked out as siblings, or use --cross-repo skip)")
            cross_repo_mode = "skip"

    print("=" * 60)
    print("Documentation Link Validation")
    print("=" * 60)
    if exclude_dirs:
        print(f"Excluding directories: {', '.join(sorted(exclude_dirs))}")
    if cross_repo_mode != "check":
        print(f"Cross-repo links: {cross_repo_mode}")
    elif ecosystem_root is not None:
        print(f"Cross-repo links: check (ecosystem root: {ecosystem_root})")
    if args.strict_repo_boundary:
        print("Strict-repo-boundary mode: ecosystem-root links treated as errors")

    result = validate_directory(
        repo_root,
        search_paths=search_paths,
        exclude_dirs=exclude_dirs,
        cross_repo_mode=cross_repo_mode,
        ecosystem_root=ecosystem_root,
        strict_repo_boundary=args.strict_repo_boundary,
        verbose=args.verbose,
    )

    print(f"\nScanning {result.scanned_files} markdown files...\n")
    print("-" * 60)
    if result.cross_repo_skipped > 0:
        action = "skipped" if cross_repo_mode == "skip" else "warned"
        print(f"\nCross-repo links {action}: {result.cross_repo_skipped}")
    if not result.ok:
        print(f"\nFOUND {len(result.errors)} broken link(s) in {result.files_with_errors} file(s):\n")
        for error in result.errors:
            print(error)
        print(f"\n{'=' * 60}")
        print("FAILED: Documentation link validation")
        print(f"{'=' * 60}")
        return 1
    print(f"\nAll links valid across {result.scanned_files} files.")
    print(f"\n{'=' * 60}")
    print("PASSED: Documentation link validation")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
