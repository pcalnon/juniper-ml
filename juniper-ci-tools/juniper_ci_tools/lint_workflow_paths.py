"""Lint workflow-script-path references in ``.github/workflows/*.yml``.

This module is the library implementation behind the
``juniper-lint-workflow-paths`` console script. It is the consolidated
home for what was previously copy-pasted as
``util/test_workflow_script_paths.py`` (or ``tests/...``) into every
Juniper ecosystem repo -- 6 byte-identical copies before this
consolidation.

What it catches
---------------

Every ``python|bash <path/to/script>`` invocation in a
``.github/workflows/*.yml`` file must reference a path that exists in
the repo. Catches the failure class that broke 3 juniper-X CIs on
2026-05-18, where a script was renamed (or its symlink target moved
into a non-checked-out sibling repo) but the workflow continued to
invoke the old path. The CI would fail with
``python: can't open file '.../scripts/check_doc_links.py'`` on every
run until somebody noticed.

What it does NOT catch
----------------------

- Module form (``python -m foo.bar``) -- cannot resolve a module to a
  path without importing the package.
- Cross-repo paths (``juniper-X/...``) -- these are runtime-resolved
  from sibling clones in scheduled workflows.
- Absolute paths (``/usr/local/bin/foo``).
- Shell-variable-expanded paths (``${{ env.SCRIPT }}/foo.py``).

Library API
-----------

::

    from juniper_ci_tools.lint_workflow_paths import (
        lint_workflow_paths,
        LintFinding,
        LintResult,
        find_repo_root,
        extract_script_paths,
    )

    result = lint_workflow_paths(repo_root)  # auto-discovers via .github/workflows
    if not result.ok:
        for finding in result.missing:
            print(f"{finding.workflow}: {finding.path}")

Console script
--------------

::

    juniper-lint-workflow-paths [--repo-root PATH] [--workflows-dir PATH]
                                [--exit-zero] [--json] [--version]

Exit codes: ``0`` (no missing paths), ``1`` (missing paths found, default;
suppress with ``--exit-zero``), ``2`` (repo root or workflows dir not
discoverable).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Optional

import yaml

# Path-like script references: a token containing at least one ``/`` and
# ending in .py/.sh/.bash, not preceded by another path char. Catches all
# the common invocation forms:
#
#   python scripts/check_doc_links.py
#   python3 -m unittest -v tests/test_foo.py
#   bash util/generate_dep_docs.sh
#   $PYTHON scripts/foo.py            (shell var prefix)
#
# Module form ``python -m foo.bar`` is intentionally not validated because
# we cannot resolve a module to a path without importing the package.
_SCRIPT_PATH = re.compile(r"(?<![A-Za-z0-9_./-])([A-Za-z0-9_-]+(?:/[A-Za-z0-9_./-]+)+\.(?:py|sh|bash))\b")

# Sibling ecosystem repos that scheduled workflows clone into the runner
# workspace before invoking. Any path under one of these is runtime-
# resolved from a clone, not a path checked into this repo, so the lint
# must skip it.
DEFAULT_ECOSYSTEM_SIBLING_PREFIXES: tuple[str, ...] = (
    "juniper-canopy/",
    "juniper-cascor/",
    "juniper-cascor-client/",
    "juniper-cascor-worker/",
    "juniper-data/",
    "juniper-data-client/",
    "juniper-deploy/",
    "juniper-ml/",
)


@dataclass(frozen=True)
class LintFinding:
    """A single workflow-script-path lint finding."""

    workflow: Path
    """The workflow file that references the missing path."""

    path: str
    """The (relative) path that does not exist in the repo."""


@dataclass(frozen=True)
class LintResult:
    """Aggregate lint result over all workflow files."""

    repo_root: Path
    workflows_dir: Path
    workflow_files: tuple[Path, ...]
    missing: tuple[LintFinding, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0

    def report(self) -> str:
        """Human-readable summary suitable for CLI output or
        ``unittest.TestCase.fail`` argument."""
        if self.ok:
            return f"OK: {len(self.workflow_files)} workflow file(s) checked under {self.workflows_dir}, no missing script paths."
        lines = [
            "CI workflow(s) reference script paths that do not exist:",
            *(f"  {f.workflow.relative_to(self.repo_root)}: references missing path '{f.path}'" for f in self.missing),
            "",
            "This is the failure class that broke 3 juniper-X CIs on 2026-05-18 (script rename without workflow update).",
            "Either restore the missing path or update the workflow.",
        ]
        return "\n".join(lines)


def _iter_yaml_strings(node: object) -> Iterator[str]:
    """Yield every string value reachable in a parsed YAML tree."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _iter_yaml_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_yaml_strings(value)


def extract_script_paths(yaml_text: str) -> set[str]:
    """Extract ``python <path.py>`` and ``bash <path.{bash,sh}>`` paths
    from a workflow YAML file's parsed content. Returns the set of
    raw path strings (before any validatability filtering).

    Workflows that fail to parse are silently treated as having no
    extractable paths -- the YAML error is its own concern and would
    surface from yamllint / actionlint / GitHub.
    """
    paths: set[str] = set()
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return paths

    for value in _iter_yaml_strings(parsed):
        for match in _SCRIPT_PATH.finditer(value):
            paths.add(match.group(1))
    return paths


def is_validatable(
    path: str,
    *,
    sibling_prefixes: tuple[str, ...] = DEFAULT_ECOSYSTEM_SIBLING_PREFIXES,
) -> bool:
    """Filter out paths the lint cannot resolve to an on-disk file."""
    if "${" in path or "$(" in path:  # shell-expanded variables
        return False
    if path.startswith("/"):  # absolute paths (e.g., toolcache python)
        return False
    if path.startswith("-"):  # caught a flag like ``-m``
        return False
    if path.startswith(sibling_prefixes):
        return False  # cross-repo path resolved at runtime, not at lint time
    # Skip standalone short filenames (likely a shell variable or a
    # runtime-extracted name) -- we only validate paths that include a
    # directory.
    return "/" in path


def find_repo_root(start: Path) -> Path:
    """Walk up from ``start`` looking for the first ancestor that
    contains a ``.github/workflows/`` directory. That's the repo root
    relative to which every workflow path resolves.

    Raises :class:`RuntimeError` if no such ancestor exists.
    """
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ directory found in any ancestor of {start}")


def lint_workflow_paths(
    repo_root: Path,
    *,
    workflows_dir: Optional[Path] = None,
    sibling_prefixes: tuple[str, ...] = DEFAULT_ECOSYSTEM_SIBLING_PREFIXES,
) -> LintResult:
    """Walk every ``*.yml`` / ``*.yaml`` file under
    ``repo_root/.github/workflows/`` (or ``workflows_dir`` if given) and
    return a :class:`LintResult` listing every script path that is
    referenced but does not exist on disk.

    ``sibling_prefixes`` lets consumers tune the cross-repo skip list
    (e.g., for repos outside the Juniper ecosystem). Defaults match the
    8-repo Juniper layout that motivated this module.
    """
    wf_dir = workflows_dir if workflows_dir is not None else repo_root / ".github" / "workflows"
    workflow_files = tuple(sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")))

    missing: list[LintFinding] = []
    for wf_file in workflow_files:
        text = wf_file.read_text(encoding="utf-8")
        for script_path in extract_script_paths(text):
            if not is_validatable(script_path, sibling_prefixes=sibling_prefixes):
                continue
            resolved = repo_root / script_path
            if not resolved.exists():
                missing.append(LintFinding(workflow=wf_file, path=script_path))

    return LintResult(
        repo_root=repo_root,
        workflows_dir=wf_dir,
        workflow_files=workflow_files,
        missing=tuple(missing),
    )


__all__ = [
    "DEFAULT_ECOSYSTEM_SIBLING_PREFIXES",
    "LintFinding",
    "LintResult",
    "extract_script_paths",
    "find_repo_root",
    "is_validatable",
    "lint_workflow_paths",
]
