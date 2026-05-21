"""Command-line entry point for :program:`juniper-lint-workflow-paths`.

Wraps :func:`juniper_ci_tools.lint_workflow_paths.lint_workflow_paths`
with argparse and a small text/JSON reporter so the lint can run
directly from CI or pre-commit without going through the unittest
runner.

Usage::

    juniper-lint-workflow-paths              # auto-discover repo root
    juniper-lint-workflow-paths --repo-root /path/to/repo
    juniper-lint-workflow-paths --workflows-dir /custom/wf/dir
    juniper-lint-workflow-paths --exit-zero  # report findings, exit 0
    juniper-lint-workflow-paths --json       # machine-readable output

Exit codes:
    0 -- no missing paths (or ``--exit-zero`` was passed)
    1 -- missing paths detected
    2 -- repo root or workflows directory could not be located
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from juniper_ci_tools._version import __version__
from juniper_ci_tools.lint_workflow_paths import (
    find_repo_root,
    lint_workflow_paths,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="juniper-lint-workflow-paths",
        description=("Lint every python/bash script path referenced from a repo's .github/workflows/*.yml files. Fails if any reference points at a file that does not exist on disk."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root containing .github/workflows/ (default: walk up from cwd looking for a .github/workflows/ directory).",
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=None,
        help="Override the workflows directory (default: <repo-root>/.github/workflows/).",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 even when missing paths are found (useful for soft-mode adoption).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human report.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="juniper-lint-workflow-paths {}".format(__version__),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Resolve repo root.
    try:
        repo_root = args.repo_root.resolve() if args.repo_root is not None else find_repo_root(Path.cwd())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not repo_root.is_dir():
        print(f"error: --repo-root {repo_root} is not a directory", file=sys.stderr)
        return 2

    workflows_dir = args.workflows_dir.resolve() if args.workflows_dir is not None else repo_root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        print(f"error: workflows directory not found: {workflows_dir}", file=sys.stderr)
        return 2

    result = lint_workflow_paths(repo_root, workflows_dir=workflows_dir)

    if args.json:
        payload = {
            "repo_root": str(result.repo_root),
            "workflows_dir": str(result.workflows_dir),
            "workflow_files": [str(p.relative_to(result.repo_root)) for p in result.workflow_files],
            "ok": result.ok,
            "missing": [
                {
                    "workflow": str(f.workflow.relative_to(result.repo_root)),
                    "path": f.path,
                }
                for f in result.missing
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.report())

    if result.ok or args.exit_zero:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
