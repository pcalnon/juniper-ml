"""Lint: ``AGENTS.md`` canonical header schema (Project / Repository /
Author / License / Version / Last Updated).

This module is the canonical home of the AGENTS.md *header-schema*
lint. The complementary *version-equality* lint -- which pins the
``**Version**:`` value to ``pyproject.toml`` ``[project].version`` --
lives in :mod:`juniper_ci_tools.lint_agents_md_version`.

Failure class caught
--------------------
Audit on 2026-05-22 across all 8 Juniper repos revealed that the
``**Last Updated**:`` header drifts silently. Six repos held a uniform
``2026-04-02`` from a bulk update ~50 days earlier; two repos
(juniper-ml, juniper-canopy) omitted the field entirely. The shape of
the header bullet block also varied (different bullets present,
different orderings). Manual maintenance has lost.

This lint locks the header schema. Pair it with the
``.github/workflows/agents-md-touch-up.yml`` workflow (auto-bumps
``**Last Updated**:`` on every PR push that touches AGENTS.md) for
full coverage: the lint guards the *shape*, the workflow guards
*currency*.

Canonical schema
----------------
Six required fields, in this *relative* order. Extra fields
(e.g. ``**Python**:``) may be interleaved freely:

* ``**Project**`` -- non-empty descriptive name
* ``**Repository**`` -- e.g. ``pcalnon/juniper-ml``
* ``**Author**`` -- non-empty
* ``**License**`` -- non-empty
* ``**Version**`` -- e.g. ``0.4.0``
* ``**Last Updated**`` -- ``YYYY-MM-DD``

Header termination
------------------
The header is everything before the first ``---`` horizontal rule
*or* the first ``## `` H2 section heading, whichever comes first.

Scope and portability
---------------------
The lint is intentionally repo-agnostic.
:func:`find_agents_md_header_repo_root` walks up from a starting path
looking for the first ancestor containing ``AGENTS.md`` *as a sibling
to* ``.github/`` -- which uniquely identifies a Juniper repo root.
Unlike the version-drift sibling lint, this lint does *not* require a
``pyproject.toml``: it applies equally to ``juniper-deploy``.

CLI entry point
---------------
:mod:`juniper_ci_tools.cli_lint_agents_md_header` exposes
:program:`juniper-lint-agents-md-header` for direct CI / pre-commit
invocation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REQUIRED_FIELDS: tuple[str, ...] = (
    "Project",
    "Repository",
    "Author",
    "License",
    "Version",
    "Last Updated",
)
"""Required AGENTS.md header bullets, in canonical relative order."""

# Whitespace-on-either-side is limited to [ \t] (no newlines) so the
# lazy ``.*?`` value cannot span to the next line when the bullet has
# only whitespace after the colon.
_BULLET_RE = re.compile(r"^\*\*(?P<field>[^*]+)\*\*:[ \t]*(?P<value>.*?)[ \t]*$", re.MULTILINE)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RepoRootNotFoundError(RuntimeError):
    """Raised when no ancestor directory contains ``AGENTS.md`` as a sibling to ``.github/``."""


@dataclass(frozen=True)
class AgentsMdHeaderLintResult:
    """Outcome of a single :func:`lint_agents_md_header` invocation.

    Attributes:
        repo_root: The directory that contains both ``AGENTS.md`` and
            ``.github/`` (auto-discovered or explicitly passed).
        agents_md_path: Resolved path to ``AGENTS.md``.
        bullets: All ``(field, value)`` bullets found in the header,
            in the order they appear in the file.
        missing_fields: Required fields that did not appear in the
            header at all. Empty tuple when all six are present.
        order_violations: When the required fields appear in the wrong
            *relative* order (filtering out extras), this is the
            observed order. Empty tuple when the order is correct.
        empty_value_fields: Required fields that appear but have an
            empty value (whitespace-only). Empty tuple when all
            required values are non-empty.
        bad_last_updated_value: The raw value of ``**Last Updated**``
            when it is present but does not match ``YYYY-MM-DD``.
            ``None`` when the value is well-formed or the field is
            absent (the latter is already covered by
            ``missing_fields``).
    """

    repo_root: Path
    agents_md_path: Path
    bullets: tuple[tuple[str, str], ...]
    missing_fields: tuple[str, ...]
    order_violations: tuple[str, ...]
    empty_value_fields: tuple[str, ...]
    bad_last_updated_value: Optional[str]

    @property
    def is_drift(self) -> bool:
        """``True`` when any schema violation is present."""
        return bool(self.missing_fields) or bool(self.order_violations) or bool(self.empty_value_fields) or self.bad_last_updated_value is not None

    def render(self) -> str:
        """Human-readable multi-line summary suitable for CLI output."""
        if not self.is_drift:
            return f"OK: {self.agents_md_path} header conforms to the canonical schema ({len(REQUIRED_FIELDS)} required fields, ISO date)."
        lines = [f"DRIFT: {self.agents_md_path} header does not match the canonical schema."]
        if self.missing_fields:
            lines.append(f"  Missing required field(s): {list(self.missing_fields)}")
        if self.order_violations:
            lines.append(f"  Required fields are in the wrong relative order. Observed (required-only): {list(self.order_violations)}. Expected: {list(REQUIRED_FIELDS)}.")
        if self.empty_value_fields:
            lines.append(f"  Required field(s) with empty value: {list(self.empty_value_fields)}")
        if self.bad_last_updated_value is not None:
            lines.append(f"  `**Last Updated**: {self.bad_last_updated_value!r}` is not in YYYY-MM-DD format.")
        return "\n".join(lines)


def find_agents_md_header_repo_root(start: Path) -> Path:
    """Walk up from ``start`` looking for an ancestor that contains
    ``AGENTS.md`` as a sibling to ``.github/``.

    Args:
        start: Starting path. May be a file or a directory. The search
            includes ``start`` itself (resolved to its parent if it is
            a file) and every ancestor up to the filesystem root.

    Returns:
        The first ancestor directory whose immediate children include
        both ``AGENTS.md`` and ``.github/``.

    Raises:
        RepoRootNotFoundError: When the search reaches the filesystem
            root without finding a match.
    """
    start = start.resolve()
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parents]
    for parent in candidates:
        if (parent / "AGENTS.md").is_file() and (parent / ".github").is_dir():
            return parent
    raise RepoRootNotFoundError(f"Could not locate repo root (AGENTS.md + .github/) from {start}")


def extract_header_bullets(text: str) -> list[tuple[str, str]]:
    """Extract the ordered list of ``(field, value)`` bullets from an
    AGENTS.md header.

    The header is everything before the first ``---`` horizontal rule
    or the first ``## `` H2 heading, whichever comes first.

    Args:
        text: Full AGENTS.md content.

    Returns:
        A list of ``(field, value)`` tuples in source order. Empty
        when no canonical bullets are present.
    """
    lines = text.splitlines()
    header_end = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "---" or line.startswith("## "):
            header_end = i
            break
    header = "\n".join(lines[:header_end])
    return [(m.group("field"), m.group("value")) for m in _BULLET_RE.finditer(header)]


def lint_agents_md_header(repo_root: Optional[Path] = None, *, start: Optional[Path] = None) -> AgentsMdHeaderLintResult:
    """Lint an AGENTS.md against the canonical six-field header schema.

    Args:
        repo_root: Explicit repo-root directory. When ``None``, the
            repo root is auto-discovered by walking up from ``start``.
        start: Starting path for auto-discovery. Defaults to the
            current working directory. Ignored when ``repo_root`` is
            given.

    Returns:
        :class:`AgentsMdHeaderLintResult` describing the schema check.
        The caller is responsible for inspecting
        :attr:`AgentsMdHeaderLintResult.is_drift` and acting on it.
        This function does not raise on schema violations -- only on
        structural problems (missing AGENTS.md, repo root not found).

    Raises:
        RepoRootNotFoundError: When ``repo_root`` is ``None`` and no
            ancestor of ``start`` contains ``AGENTS.md`` next to
            ``.github/``.
        FileNotFoundError: When ``repo_root`` is given explicitly but
            does not contain ``AGENTS.md``.
    """
    if repo_root is None:
        repo_root = find_agents_md_header_repo_root(start if start is not None else Path.cwd())
    repo_root = repo_root.resolve()
    agents_md_path = repo_root / "AGENTS.md"
    if not agents_md_path.is_file():
        raise FileNotFoundError(f"{agents_md_path} does not exist")

    text = agents_md_path.read_text(encoding="utf-8")
    bullets = extract_header_bullets(text)

    present = {field for field, _ in bullets}
    missing = tuple(f for f in REQUIRED_FIELDS if f not in present)

    present_required = [field for field, _ in bullets if field in REQUIRED_FIELDS]
    order_violations: tuple[str, ...] = ()
    if present_required != list(REQUIRED_FIELDS):
        order_violations = tuple(present_required)

    empty = tuple(field for field, value in bullets if field in REQUIRED_FIELDS and not value.strip())

    last_updated = next((value for field, value in bullets if field == "Last Updated"), None)
    bad_last_updated: Optional[str] = None
    if last_updated is not None and not _ISO_DATE_RE.match(last_updated.strip()):
        bad_last_updated = last_updated

    return AgentsMdHeaderLintResult(
        repo_root=repo_root,
        agents_md_path=agents_md_path,
        bullets=tuple(bullets),
        missing_fields=missing,
        order_violations=order_violations,
        empty_value_fields=empty,
        bad_last_updated_value=bad_last_updated,
    )


__all__ = [
    "REQUIRED_FIELDS",
    "RepoRootNotFoundError",
    "AgentsMdHeaderLintResult",
    "extract_header_bullets",
    "find_agents_md_header_repo_root",
    "lint_agents_md_header",
]
