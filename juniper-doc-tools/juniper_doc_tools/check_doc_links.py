"""Documentation link validator -- core library.

Scans markdown files for relative links and anchor references, verifying
that target files exist and heading anchors are valid. Cross-repo links to
Juniper ecosystem siblings (``../juniper-X/...``) and ecosystem-root links
(``../CLAUDE.md``, ``../../notes/...``, etc.) are classified and handled
via the configurable ``cross_repo_mode`` policy (``skip``, ``warn``, or
``check``).

This module is the library form; the CLI lives in :mod:`juniper_doc_tools.cli`.
The public API exposed at package level is :class:`ValidationResult`,
:func:`validate_directory`, and :func:`validate_file`.
"""

from __future__ import annotations

import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from juniper_doc_tools._ecosystem import (
    CROSS_REPO_MODES,
    CROSS_REPO_PATTERN,
    ECOSYSTEM_REPOS,
    ECOSYSTEM_ROOT_PATTERN,
    MAX_TRAVERSAL_DEPTH,
)

# Regex to find markdown links: [text](target)
_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Prefixes that indicate external URLs (skip these)
_EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp://")

# File extensions to treat as documentation
_DOC_EXTENSIONS = {".md", ".markdown", ".rst", ".txt"}

# Directories to skip during scanning
_SKIP_DIRS = {
    ".git",
    ".claude",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".egg-info",
    "htmlcov",
    ".trunk",
    ".vscode",
    ".idea",
}


@dataclass
class ValidationResult:
    """Outcome of a documentation-link validation run.

    Attributes:
        ok: True if no broken links were found.
        errors: One human-readable line per broken link.
        cross_repo_skipped: Number of cross-repo and ecosystem-root links
            that were classified and either skipped (``skip`` mode) or
            warned (``warn`` mode). Always 0 in ``check`` mode (those
            links are either resolved as OK or appended to ``errors``).
        scanned_files: Number of markdown files actually validated.
        files_with_errors: Number of distinct markdown files that
            contributed at least one error. Counted at iteration time
            in :func:`validate_directory` -- do not try to derive it by
            parsing the error strings, because some error messages
            prefix with the absolute path (broken anchors use the full
            ``Path`` object) while others prefix with the path relative
            to ``repo_root``, so a string-deduplication heuristic
            double-counts.
    """

    ok: bool
    errors: list[str] = field(default_factory=list)
    cross_repo_skipped: int = 0
    scanned_files: int = 0
    files_with_errors: int = 0


def _is_ecosystem_root(candidate: Path) -> bool:
    """Check if a directory looks like the Juniper ecosystem parent.

    A directory is treated as the ecosystem root if it contains at least 3
    known sibling repos from :data:`ECOSYSTEM_REPOS`.
    """
    found = sum(1 for repo in ECOSYSTEM_REPOS if (candidate / repo).is_dir())
    return found >= 3


def discover_ecosystem_root(repo_root: Path) -> Path | None:
    """Find the Juniper ecosystem parent directory, if present.

    Uses two methods:

    1. Git's ``rev-parse --git-common-dir`` -- returns the main repo's
       ``.git`` directory even from worktrees (including ``.claude/worktrees/``
       and centralized worktrees). The ecosystem root is its grandparent.
    2. Walking up from ``repo_root`` (limited to 2 levels) as a fallback
       when git is not available.

    Args:
        repo_root: The repository root directory.

    Returns:
        Path to the ecosystem root directory, or None if not found.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=False,
        )
        if result.returncode == 0:
            git_common_dir = Path(result.stdout.strip())
            if not git_common_dir.is_absolute():
                git_common_dir = (repo_root / git_common_dir).resolve()
            main_repo_root = git_common_dir.parent
            candidate = main_repo_root.parent
            if _is_ecosystem_root(candidate):
                return candidate
    except FileNotFoundError:
        # Git is not installed/available; fall back to parent-directory probing below.
        # This keeps link validation usable in non-git environments.
        pass

    for parent in [repo_root.parent, repo_root.parent.parent]:
        if _is_ecosystem_root(parent):
            return parent

    return None


def _heading_to_anchor(heading_text: str) -> str:
    """Convert a markdown heading to its GitHub-style anchor id."""
    text = heading_text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s", "-", text)
    text = text.strip("-")
    return text


def _extract_headings(content: str) -> set[str]:
    """Extract all heading anchors from markdown content."""
    anchors: set[str] = set()
    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            heading_text = match.group(2).strip()
            anchors.add(_heading_to_anchor(heading_text))
    return anchors


def _find_markdown_files(
    search_paths: list[Path],
    repo_root: Path,
    exclude_dirs: set[str] | None = None,
) -> list[Path]:
    """Find all markdown files in the given paths.

    Dedupes by resolved (real) path so a file reachable both directly and
    via a symlink is only validated once.
    """
    skip = _SKIP_DIRS | (exclude_dirs or set())
    md_files: dict[Path, Path] = {}

    def _add(display_path: Path) -> None:
        real = display_path.resolve()
        if real not in md_files:
            md_files[real] = display_path

    for path in search_paths:
        if path.is_file() and path.suffix in _DOC_EXTENSIONS:
            if path.is_symlink() and not path.exists():
                continue
            try:
                rel = path.relative_to(repo_root)
                if not any(part in skip for part in rel.parts):
                    _add(path)
            except ValueError:
                _add(path)
        elif path.is_dir():
            for ext in _DOC_EXTENSIONS:
                for f in path.rglob(f"*{ext}"):
                    if f.is_symlink() and not f.exists():
                        continue
                    try:
                        rel = f.relative_to(repo_root)
                        if not any(part in skip for part in rel.parts):
                            _add(f)
                    except ValueError:
                        if not any(part in skip for part in f.parts):
                            _add(f)

    return sorted(md_files.values())


def _validate_cross_repo_structure(file_part: str) -> str | None:
    """Check that a cross-repo link doesn't traverse back out of its target.

    Even in skip mode, structurally malformed cross-repo links are rejected.
    This prevents patterns like ``../juniper-data/../../etc/passwd`` from
    being silently skipped.
    """
    parts = Path(file_part).parts
    for i, part in enumerate(parts):
        if part in ECOSYSTEM_REPOS:
            remainder = Path(*parts[i + 1 :]) if i + 1 < len(parts) else Path(".")
            if ".." in remainder.parts:
                return f"cross-repo link escapes target repository: {file_part}"
            break
    return None


def validate_file(
    md_file: Path,
    repo_root: Path,
    *,
    verbose: bool = False,
    cross_repo_mode: str = "check",
    ecosystem_root: Path | None = None,
    strict_repo_boundary: bool = False,
) -> tuple[list[str], int]:
    """Validate all internal links in a single markdown file.

    Args:
        md_file: Path to the markdown file.
        repo_root: Repository root for resolving relative paths.
        verbose: If True, print each link checked.
        cross_repo_mode: How to handle cross-repo links ("skip", "warn",
            or "check").
        ecosystem_root: Path to the Juniper ecosystem parent directory.
            Required for cross-repo link validation in "check" mode.
        strict_repo_boundary: If True, disable ecosystem-root link
            classification. Links like ``../../CLAUDE.md`` fall through
            to the "outside repository boundary" error path. Default is
            False (ecosystem-root links subject to ``cross_repo_mode``
            policy). See plan §3.4.1 / §8.4.

    Returns:
        Tuple of (error message list, cross-repo links skipped/warned count).
    """
    errors: list[str] = []
    cross_repo_skipped = 0
    content = md_file.read_text(encoding="utf-8", errors="replace")
    headings = _extract_headings(content)
    file_dir = md_file.parent
    repo_boundary = repo_root.resolve()

    code_fence: str | None = None
    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped_line = line.strip()

        if code_fence is None:
            fence_match = re.match(r"^(`{3,}|~{3,})", stripped_line)
            if fence_match:
                code_fence = fence_match.group(1)
                continue
        else:
            close_match = re.match(r"^(`{3,}|~{3,})\s*$", stripped_line)
            if close_match and close_match.group(1)[0] == code_fence[0] and len(close_match.group(1)) >= len(code_fence):
                code_fence = None
            continue

        check_line = re.sub(r"`[^`]+`", "", line)

        for match in _LINK_PATTERN.finditer(check_line):
            link_text = match.group(1)
            target = match.group(2).strip()

            if any(target.startswith(prefix) for prefix in _EXTERNAL_PREFIXES):
                if verbose:
                    print(f"  SKIP (external): {md_file}:{line_num} -> {target}")
                continue

            if target.startswith("data:") or target.startswith("//"):
                continue

            if "#" in target:
                file_part, anchor = target.split("#", 1)
            else:
                file_part = target
                anchor = None

            if not file_part:
                if anchor and anchor not in headings:
                    errors.append(f"  {md_file}:{line_num}: broken anchor #{anchor} (heading not found)")
                elif verbose:
                    print(f"  OK (anchor): {md_file}:{line_num} -> #{anchor}")
                continue

            rel_source = md_file.relative_to(repo_root)

            if "\x00" in file_part:
                errors.append(f"  {rel_source}:{line_num}: null byte in link target")
                continue

            if Path(file_part).is_absolute():
                errors.append(f"  {rel_source}:{line_num}: absolute path in documentation link (must be relative)")
                continue

            if file_part.count("..") > MAX_TRAVERSAL_DEPTH:
                errors.append(f"  {rel_source}:{line_num}: excessive directory traversal in link")
                continue

            # --- Cross-repo link classification ---

            cross_repo_match = CROSS_REPO_PATTERN.match(file_part)
            if cross_repo_match:
                structural_error = _validate_cross_repo_structure(file_part)
                if structural_error:
                    errors.append(f"  {rel_source}:{line_num}: {structural_error}")
                    continue

                if cross_repo_mode == "skip":
                    cross_repo_skipped += 1
                    if verbose:
                        print(f"  SKIP (cross-repo): {md_file}:{line_num} -> {file_part}")
                    continue
                elif cross_repo_mode == "warn":
                    cross_repo_skipped += 1
                    print(f"  WARN (cross-repo): {rel_source}:{line_num} -> {file_part}")
                    continue
                elif ecosystem_root is not None:
                    repo_name = cross_repo_match.group(1)
                    intra_repo_path = file_part[cross_repo_match.end() :]
                    target_path_xrepo = (ecosystem_root / repo_name / intra_repo_path).resolve()
                    target_repo_boundary = (ecosystem_root / repo_name).resolve()

                    if not target_path_xrepo.is_relative_to(target_repo_boundary):
                        errors.append(f"  {rel_source}:{line_num}: cross-repo link escapes target repository boundary")
                        continue

                    if target_path_xrepo.exists():
                        if verbose:
                            print(f"  OK (cross-repo): {md_file}:{line_num} -> {file_part}")
                    else:
                        errors.append(f"  {rel_source}:{line_num}: broken link [{link_text}]({target}) -> file not found in {repo_name}")
                    continue
                # "check" mode without ecosystem root falls through to normal validation

            # --- Resolve and validate file path ---

            target_path = (file_dir / file_part).resolve()
            target_path_from_root = (repo_root / file_part).resolve()

            file_relative_in_bounds = target_path.is_relative_to(repo_boundary)
            root_relative_in_bounds = target_path_from_root.is_relative_to(repo_boundary)

            if not file_relative_in_bounds and not root_relative_in_bounds:
                # Path escapes the repo. If it lands on a known ecosystem-root
                # item and strict-repo-boundary mode is OFF, classify as
                # cross-repo and apply --cross-repo policy.
                if not strict_repo_boundary:
                    eco_match = ECOSYSTEM_ROOT_PATTERN.match(file_part)
                    if eco_match:
                        if cross_repo_mode == "skip":
                            cross_repo_skipped += 1
                            if verbose:
                                print(f"  SKIP (ecosystem-root): {md_file}:{line_num} -> {file_part}")
                            continue
                        elif cross_repo_mode == "warn":
                            cross_repo_skipped += 1
                            print(f"  WARN (ecosystem-root): {rel_source}:{line_num} -> {file_part}")
                            continue
                        if target_path.exists() or target_path_from_root.exists():
                            if verbose:
                                print(f"  OK (ecosystem-root): {md_file}:{line_num} -> {file_part}")
                        else:
                            errors.append(f"  {rel_source}:{line_num}: broken ecosystem-root link [{link_text}]({target}) -> file not found")
                        continue

                errors.append(f"  {rel_source}:{line_num}: link resolves outside repository boundary")
                continue

            file_exists = file_relative_in_bounds and target_path.exists()
            root_exists = root_relative_in_bounds and target_path_from_root.exists()

            if file_exists or root_exists:
                if verbose:
                    print(f"  OK (file): {md_file}:{line_num} -> {file_part}")
            else:
                errors.append(f"  {rel_source}:{line_num}: broken link [{link_text}]({target}) -> file not found")

    return errors, cross_repo_skipped


def validate_directory(
    repo_root: Path,
    *,
    search_paths: list[Path] | None = None,
    exclude_dirs: set[str] | None = None,
    cross_repo_mode: str = "check",
    ecosystem_root: Path | None = None,
    strict_repo_boundary: bool = False,
    verbose: bool = False,
) -> ValidationResult:
    """Validate every markdown file under ``repo_root``.

    The ergonomic library entry point. The CLI in :mod:`juniper_doc_tools.cli`
    wraps this with argparse and printed progress output.

    Args:
        repo_root: Repository root for resolving relative paths.
        search_paths: Specific directories or files to scan. If None,
            scans ``repo_root`` recursively.
        exclude_dirs: Additional directory names to exclude from the scan.
        cross_repo_mode: How to handle cross-repo links ("skip", "warn",
            or "check").
        ecosystem_root: Path to the Juniper ecosystem parent directory.
            Required for cross-repo link validation in "check" mode; if
            ``cross_repo_mode == "check"`` and this is None, the function
            attempts :func:`discover_ecosystem_root` and falls back to
            "skip" mode if no ecosystem root is found.
        strict_repo_boundary: If True, disable ecosystem-root link
            classification (see :func:`validate_file`).
        verbose: If True, print every link checked.

    Returns:
        A :class:`ValidationResult` summarizing the outcome.
    """
    if cross_repo_mode not in CROSS_REPO_MODES:
        raise ValueError(f"cross_repo_mode must be one of {sorted(CROSS_REPO_MODES)!r}, got {cross_repo_mode!r}")

    if cross_repo_mode == "check" and ecosystem_root is None:
        ecosystem_root = discover_ecosystem_root(repo_root)
        if ecosystem_root is None:
            cross_repo_mode = "skip"

    if search_paths is None:
        search_paths = [repo_root]

    md_files = _find_markdown_files(search_paths, repo_root, exclude_dirs)

    all_errors: list[str] = []
    total_skipped = 0
    files_with_errors_count = 0
    for md_file in md_files:
        errors, skipped = validate_file(
            md_file,
            repo_root,
            verbose=verbose,
            cross_repo_mode=cross_repo_mode,
            ecosystem_root=ecosystem_root,
            strict_repo_boundary=strict_repo_boundary,
        )
        if errors:
            files_with_errors_count += 1
        all_errors.extend(errors)
        total_skipped += skipped

    return ValidationResult(
        ok=not all_errors,
        errors=all_errors,
        cross_repo_skipped=total_skipped,
        scanned_files=len(md_files),
        files_with_errors=files_with_errors_count,
    )
