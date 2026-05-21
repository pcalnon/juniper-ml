"""Lint: ``AGENTS.md`` ``**Version**:`` header matches ``pyproject.toml``
``[project].version``.

This module is the canonical home of the AGENTS.md version-drift lint
that previously lived as a byte-identical inline copy of
``util/test_agents_md_version_drift.py`` in 6+ Juniper repos. Shipping
it as a library (+ console script) inside :mod:`juniper_ci_tools`
eliminates the drift class that motivated the lint in the first place.

Failure class caught
--------------------
``juniper-ml#295`` bumped ``pyproject.toml`` from 0.4.1 to 0.5.0 but
left the ``AGENTS.md`` ``**Version**`` header at 0.4.0. That drift
shipped for 6 days before an ad-hoc grep caught it
(``juniper-ml#304``). This lint makes the same drift impossible in
either direction (header ahead, pyproject ahead, or simply out of
sync) on every PR.

Scope and portability
---------------------
The lint is intentionally repo-agnostic. :func:`find_agents_md_repo_root` walks
up from a starting path looking for the first directory that contains
*both* ``pyproject.toml`` and ``AGENTS.md`` -- the same heuristic the
inline copies used. Repos without a ``pyproject.toml`` (e.g.,
``juniper-deploy``) have nothing to compare the header against and
should not adopt this lint; in those cases :func:`lint_agents_md_version`
raises :class:`RepoRootNotFoundError`.

CLI entry point
---------------
The companion :mod:`juniper_ci_tools.cli_lint_agents_md_version` module
exposes :program:`juniper-lint-agents-md-version` for direct CI / pre-
commit invocation. The legacy unittest form (``python -m unittest
util/test_agents_md_version_drift.py``) is no longer needed.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:  # pragma: no cover - exercised only on Python < 3.11
    import tomli as _tomllib  # type: ignore[no-redef]


# Matches the canonical header line ``**Version**: X.Y.Z``. We
# intentionally only accept the bold-then-colon-then-version shape that
# every Juniper AGENTS.md uses today -- a stricter pattern fails fast
# on accidental reformatting (e.g., dropping the bold markers).
_HEADER_RE = re.compile(r"^\*\*Version\*\*:\s*(?P<version>\S+)\s*$", re.MULTILINE)


class RepoRootNotFoundError(RuntimeError):
    """Raised when no ancestor directory contains both ``pyproject.toml`` and ``AGENTS.md``.

    The lint requires both files to exist before it can compare them.
    Repos with neither file (or with only one) cannot adopt this lint.
    """


class MultipleVersionHeadersError(AssertionError):
    """Raised when ``AGENTS.md`` contains more than one ``**Version**:`` header.

    The canonical convention is exactly one bold version header near the
    top of the file. Multiple headers create ambiguity about which one
    should track ``pyproject.toml``.
    """


@dataclass(frozen=True)
class AgentsMdLintResult:
    """Outcome of a single :func:`lint_agents_md_version` invocation.

    Attributes:
        repo_root: The directory that contains both ``pyproject.toml`` and
            ``AGENTS.md`` (auto-discovered or explicitly passed).
        pyproject_path: Resolved path to ``pyproject.toml``.
        agents_md_path: Resolved path to ``AGENTS.md``.
        pyproject_version: The ``[project].version`` value from
            ``pyproject.toml``.
        agents_md_version: The ``**Version**:`` header value from
            ``AGENTS.md``, or ``None`` when the file has no canonical
            header (an opt-in skip rather than a failure).
        in_sync: ``True`` when both versions exist and match. ``None``
            when the AGENTS.md file has no canonical header (no
            comparison possible, treated as opt-out, not a failure).
    """

    repo_root: Path
    pyproject_path: Path
    agents_md_path: Path
    pyproject_version: str
    agents_md_version: Optional[str]
    in_sync: Optional[bool]

    @property
    def is_drift(self) -> bool:
        """``True`` only when both versions are present and differ.

        A missing AGENTS.md header is *not* drift -- it is an opt-out.
        """
        return self.in_sync is False

    def render(self) -> str:
        """Human-readable one-line summary suitable for the CLI."""
        if self.agents_md_version is None:
            return f"SKIP: {self.agents_md_path} has no `**Version**:` header (opt-out)."
        if self.in_sync:
            return f"OK: AGENTS.md `**Version**: {self.agents_md_version}` matches " f'pyproject.toml `[project].version = "{self.pyproject_version}"`.'
        return (
            f"DRIFT: AGENTS.md `**Version**: {self.agents_md_version}` does not match "
            f'pyproject.toml `[project].version = "{self.pyproject_version}"`. '
            "Bump AGENTS.md in the same PR as the pyproject version bump so the "
            "agent-facing contract stays in sync with the package."
        )


def find_agents_md_repo_root(start: Path) -> Path:
    """Walk up from ``start`` looking for an ancestor that holds both
    ``pyproject.toml`` and ``AGENTS.md``.

    Args:
        start: Starting path. May be a file or a directory. The search
            includes ``start`` itself (resolved to its parent if it is
            a file) and every ancestor up to the filesystem root.

    Returns:
        The first ancestor directory that contains both required files.

    Raises:
        RepoRootNotFoundError: When the search reaches the filesystem
            root without finding a match.
    """
    start = start.resolve()
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parents]
    for parent in candidates:
        if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise RepoRootNotFoundError(f"Could not locate repo root (pyproject.toml + AGENTS.md) from {start}")


def _read_pyproject_version(pyproject_path: Path) -> str:
    """Read ``[project].version`` from a ``pyproject.toml`` file."""
    with pyproject_path.open("rb") as handle:
        data = _tomllib.load(handle)
    try:
        return str(data["project"]["version"])
    except KeyError as exc:
        raise KeyError(f"{pyproject_path} does not contain [project].version: missing key {exc!r}") from exc


def _extract_agents_md_version(agents_md_path: Path) -> Optional[str]:
    """Extract the canonical ``**Version**:`` header from an AGENTS.md file.

    Returns ``None`` when the file has no header (opt-out). Raises
    :class:`MultipleVersionHeadersError` when more than one header is
    present (ambiguous).
    """
    text = agents_md_path.read_text(encoding="utf-8")
    matches = _HEADER_RE.findall(text)
    if not matches:
        return None
    if len(matches) > 1:
        raise MultipleVersionHeadersError(f"{agents_md_path} has multiple `**Version**:` headers: {matches!r}. " "Expected exactly one canonical header at the top of the file.")
    return matches[0]


def lint_agents_md_version(repo_root: Optional[Path] = None, *, start: Optional[Path] = None) -> AgentsMdLintResult:
    """Compare ``AGENTS.md`` ``**Version**:`` header against
    ``pyproject.toml`` ``[project].version``.

    Args:
        repo_root: Explicit repo-root directory. When ``None``, the
            repo root is auto-discovered by walking up from ``start``.
        start: Starting path for auto-discovery. Defaults to the current
            working directory. Ignored when ``repo_root`` is given.

    Returns:
        :class:`AgentsMdLintResult` describing the comparison. The caller is
        responsible for inspecting :attr:`AgentsMdLintResult.is_drift` (or
        :attr:`AgentsMdLintResult.in_sync`) and acting on it. This function
        does not raise on drift -- only on structural problems
        (missing files, multiple headers, missing version key).

    Raises:
        RepoRootNotFoundError: When ``repo_root`` is ``None`` and no
            ancestor of ``start`` contains both required files.
        MultipleVersionHeadersError: When the AGENTS.md file has more
            than one ``**Version**:`` header.
        KeyError: When ``pyproject.toml`` exists but lacks
            ``[project].version``.
        FileNotFoundError: When ``repo_root`` is given explicitly but
            does not actually contain both required files.
    """
    if repo_root is None:
        repo_root = find_agents_md_repo_root(start if start is not None else Path.cwd())
    repo_root = repo_root.resolve()
    pyproject_path = repo_root / "pyproject.toml"
    agents_md_path = repo_root / "AGENTS.md"
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"{pyproject_path} does not exist")
    if not agents_md_path.is_file():
        raise FileNotFoundError(f"{agents_md_path} does not exist")

    pyproject_version = _read_pyproject_version(pyproject_path)
    agents_md_version = _extract_agents_md_version(agents_md_path)

    if agents_md_version is None:
        in_sync: Optional[bool] = None
    else:
        in_sync = agents_md_version == pyproject_version

    return AgentsMdLintResult(
        repo_root=repo_root,
        pyproject_path=pyproject_path,
        agents_md_path=agents_md_path,
        pyproject_version=pyproject_version,
        agents_md_version=agents_md_version,
        in_sync=in_sync,
    )


__all__ = [
    "RepoRootNotFoundError",
    "MultipleVersionHeadersError",
    "AgentsMdLintResult",
    "find_agents_md_repo_root",
    "lint_agents_md_version",
]
