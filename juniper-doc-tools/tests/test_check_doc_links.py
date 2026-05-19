"""Regression tests for ``juniper_doc_tools.check_doc_links``.

Ports the 17 unittest-style tests that lived in
``juniper-ml/tests/test_check_doc_links.py`` v0.7.0 to pytest style
(plan §8.1), plus adds new coverage for the ``strict_repo_boundary``
parameter and the public ``validate_directory`` entry point.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable
from unittest import mock

import pytest

from juniper_doc_tools import (
    ValidationResult,
    discover_ecosystem_root,
    validate_directory,
    validate_file,
)
from juniper_doc_tools import check_doc_links as cdl

# ---------------------------------------------------------------------------
# validate_file (the per-file workhorse)
# ---------------------------------------------------------------------------


def test_ignores_links_in_code_blocks_and_inline_code(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    (repo_root / "docs").mkdir()
    (repo_root / "docs" / "existing.md").write_text("# Existing\n", encoding="utf-8")

    md_file = repo_root / "README.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "Inline code: `[inline](missing-inline.md)`",
                "```markdown",
                "[code-block-link](missing-code-block.md)",
                "```",
                "[valid](docs/existing.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="check",
        ecosystem_root=repo_root.parent,
    )

    assert errors == []
    assert cross_repo_count == 0


def test_rejects_absolute_paths_and_excessive_traversal(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    md_file = repo_root / "README.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[absolute](/etc/passwd)",
                "[too-deep](../../../../../../outside.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, _ = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="check",
        ecosystem_root=repo_root.parent,
    )

    assert len(errors) == 2
    assert any("absolute path in documentation link" in e for e in errors)
    assert any("excessive directory traversal" in e for e in errors)


def test_cross_repo_skip_counts_links(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo("juniper-ml")
    md_file = repo_root / "README.md"
    md_file.write_text(
        "# Title\n[cross](../juniper-data/README.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
    )

    assert errors == []
    assert cross_repo_count == 1


def test_cross_repo_escape_is_error_even_when_skipping(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo("juniper-ml")
    md_file = repo_root / "README.md"
    md_file.write_text(
        "# Title\n[escape](../juniper-data/../../etc/passwd)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "cross-repo link escapes target repository" in errors[0]


def test_cross_repo_check_validates_target_in_sibling_repo(tmp_path: Path) -> None:
    ecosystem_root = tmp_path / "ecosystem"
    repo_root = ecosystem_root / "juniper-ml"
    sibling_repo = ecosystem_root / "juniper-data"
    repo_root.mkdir(parents=True)
    sibling_repo.mkdir()
    (sibling_repo / "docs").mkdir()
    (sibling_repo / "docs" / "exists.md").write_text("# Exists\n", encoding="utf-8")

    md_file = repo_root / "README.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[ok](../juniper-data/docs/exists.md)",
                "[missing](../juniper-data/docs/missing.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="check",
        ecosystem_root=ecosystem_root,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "file not found in juniper-data" in errors[0]


def test_cross_repo_warn_prints_warning_and_counts_links(
    make_repo: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = make_repo("juniper-ml")
    md_file = repo_root / "README.md"
    md_file.write_text(
        "# Title\n[cross](../juniper-data/README.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="warn",
        ecosystem_root=None,
    )

    captured = capsys.readouterr()
    assert errors == []
    assert cross_repo_count == 1
    assert "WARN (cross-repo): README.md:2 -> ../juniper-data/README.md" in captured.out


def test_rejects_null_byte_and_out_of_bounds_paths(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    md_file = repo_root / "README.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[null-byte](bad\x00target.md)",
                "[outside](../../outside_unknown.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, _ = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="check",
        ecosystem_root=repo_root.parent,
    )

    assert len(errors) == 2
    assert any("null byte in link target" in e for e in errors)
    assert any("link resolves outside repository boundary" in e for e in errors)


def test_find_markdown_files_dedupes_symlinks_to_same_realpath(make_repo: Callable[..., Path]) -> None:
    """A file reachable both directly and via a symlinked directory must
    only be scanned once. Without dedupe, the two scans use different
    relative-path resolution roots, producing spurious "broken link"
    reports for any link that resolves correctly from one location but
    not the other.
    """
    repo_root = make_repo()
    notes = repo_root / "notes"
    notes.mkdir()
    (notes / "ROADMAP.md").write_text("# roadmap", encoding="utf-8")
    (notes / "PHASE_DESIGN.md").write_text("# design", encoding="utf-8")
    dev = notes / "development"
    dev.mkdir()
    (dev / "ROADMAP.md").symlink_to(Path("..") / "ROADMAP.md")

    files = cdl._find_markdown_files([repo_root], repo_root)

    real_paths = {f.resolve() for f in files}
    assert len(files) == len(real_paths), files


# ---------------------------------------------------------------------------
# Ecosystem-root link classification (v0.7.0 / plan §3.4.1)
# ---------------------------------------------------------------------------


def test_ecosystem_root_skip_counts_links(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo("juniper-data")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()

    md_file = docs_dir / "CHEATSHEET.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[Juniper CLAUDE.md](../../CLAUDE.md)",
                "[Template](../../notes/DOCUMENTATION_TEMPLATE_STANDARD.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
    )

    assert errors == []
    assert cross_repo_count == 2


def test_ecosystem_root_warn_prints_warning_and_counts_links(
    make_repo: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = make_repo("juniper-cascor")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()

    md_file = docs_dir / "GUIDE.md"
    md_file.write_text(
        "# Title\n[Notes](../../notes/PLAN.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="warn",
        ecosystem_root=None,
    )

    captured = capsys.readouterr()
    assert errors == []
    assert cross_repo_count == 1
    assert "WARN (ecosystem-root): docs/GUIDE.md:2 -> ../../notes/PLAN.md" in captured.out


def test_ecosystem_root_check_validates_file_exists(tmp_path: Path) -> None:
    ecosystem_root = tmp_path / "Juniper"
    repo_root = ecosystem_root / "juniper-data"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)
    (ecosystem_root / "CLAUDE.md").write_text("# eco\n", encoding="utf-8")
    (ecosystem_root / "notes").mkdir()

    md_file = docs_dir / "OVERVIEW.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[ok](../../CLAUDE.md)",
                "[missing](../../notes/DOES_NOT_EXIST.md)",
            ]
        ),
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="check",
        ecosystem_root=ecosystem_root,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "broken ecosystem-root link" in errors[0]
    assert "DOES_NOT_EXIST.md" in errors[0]


def test_intra_repo_link_through_eco_named_dir_is_not_misclassified(
    make_repo: Callable[..., Path],
) -> None:
    """``../notes/PLAN.md`` from ``juniper-data/docs/X.md`` resolves to
    ``juniper-data/notes/PLAN.md`` -- inside the repo. It must be
    validated as a normal intra-repo link, NOT silently skipped as
    ecosystem-root just because the path segment "notes" happens to
    match an eco-root item.
    """
    repo_root = make_repo("juniper-data")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()
    notes_dir = repo_root / "notes"
    notes_dir.mkdir()

    md_file = docs_dir / "X.md"
    md_file.write_text(
        "\n".join(
            [
                "# Title",
                "[ok](../notes/PRESENT.md)",
                "[broken](../notes/ABSENT.md)",
            ]
        ),
        encoding="utf-8",
    )
    (notes_dir / "PRESENT.md").write_text("# present\n", encoding="utf-8")

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "ABSENT.md" in errors[0]
    assert "file not found" in errors[0]


def test_outside_repo_non_ecosystem_root_is_still_an_error(
    make_repo: Callable[..., Path],
) -> None:
    """``../../random.md`` is NOT in ECOSYSTEM_ROOT_ITEMS, so it must
    still be flagged as "outside repository boundary" even with
    ``--cross-repo skip``. Guard against reverting to the permissive
    0.6.0-juniper-data behavior that silently swallowed any outside-repo
    link.
    """
    repo_root = make_repo("juniper-data")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()

    md_file = docs_dir / "Y.md"
    md_file.write_text(
        "# Title\n[escape](../../random_unknown.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "outside repository boundary" in errors[0]


# ---------------------------------------------------------------------------
# New: --strict-repo-boundary flag (plan §3.4.1 / §8.4)
# ---------------------------------------------------------------------------


def test_strict_repo_boundary_disables_ecosystem_root_classification(
    make_repo: Callable[..., Path],
) -> None:
    """With ``strict_repo_boundary=True``, an ``../../CLAUDE.md`` link
    falls through to the "outside repository boundary" error path
    instead of being treated as a skip-able cross-repo link.
    """
    repo_root = make_repo("juniper-data")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()

    md_file = docs_dir / "X.md"
    md_file.write_text(
        "# Title\n[Juniper CLAUDE.md](../../CLAUDE.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
        strict_repo_boundary=True,
    )

    assert cross_repo_count == 0
    assert len(errors) == 1
    assert "outside repository boundary" in errors[0]


def test_strict_repo_boundary_does_not_affect_intra_repo_links(
    make_repo: Callable[..., Path],
) -> None:
    """The flag should only impact links that escape the repo; valid
    intra-repo links are still accepted.
    """
    repo_root = make_repo("juniper-data")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "other.md").write_text("# other\n", encoding="utf-8")

    md_file = docs_dir / "X.md"
    md_file.write_text(
        "# Title\n[ok](other.md)\n",
        encoding="utf-8",
    )

    errors, _ = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
        strict_repo_boundary=True,
    )

    assert errors == []


def test_strict_repo_boundary_does_not_affect_cross_repo_classification(
    make_repo: Callable[..., Path],
) -> None:
    """``../juniper-X/...`` cross-repo links are independent of the
    ecosystem-root path; the strict flag must not change their
    handling.
    """
    repo_root = make_repo("juniper-ml")
    md_file = repo_root / "README.md"
    md_file.write_text(
        "# Title\n[cross](../juniper-data/README.md)\n",
        encoding="utf-8",
    )

    errors, cross_repo_count = validate_file(
        md_file,
        repo_root,
        cross_repo_mode="skip",
        ecosystem_root=None,
        strict_repo_boundary=True,
    )

    assert errors == []
    assert cross_repo_count == 1


# ---------------------------------------------------------------------------
# Ecosystem-root discovery + library entry point
# ---------------------------------------------------------------------------


def test_discover_ecosystem_root_uses_git_common_dir_result(tmp_path: Path) -> None:
    ecosystem_root = tmp_path / "Juniper"
    repo_root = ecosystem_root / "juniper-ml"
    repo_root.mkdir(parents=True)
    (ecosystem_root / "juniper-data").mkdir()
    (ecosystem_root / "juniper-cascor").mkdir()

    git_result = mock.Mock(returncode=0, stdout=".git\n")
    with mock.patch.object(subprocess, "run", return_value=git_result):
        discovered = discover_ecosystem_root(repo_root)

    assert discovered == ecosystem_root


def test_discover_ecosystem_root_falls_back_when_git_unavailable(tmp_path: Path) -> None:
    ecosystem_root = tmp_path / "Juniper"
    repo_root = ecosystem_root / "juniper-ml"
    repo_root.mkdir(parents=True)
    (ecosystem_root / "juniper-data").mkdir()
    (ecosystem_root / "juniper-cascor").mkdir()

    with mock.patch.object(subprocess, "run", side_effect=FileNotFoundError):
        discovered = discover_ecosystem_root(repo_root)

    assert discovered == ecosystem_root


def test_validate_directory_returns_validation_result(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    (repo_root / "docs").mkdir()
    (repo_root / "docs" / "ok.md").write_text("# ok\n", encoding="utf-8")
    (repo_root / "docs" / "links.md").write_text(
        "# links\n[ok](ok.md)\n[missing](does_not_exist.md)\n",
        encoding="utf-8",
    )

    result = validate_directory(
        repo_root,
        cross_repo_mode="skip",
    )

    assert isinstance(result, ValidationResult)
    assert result.ok is False
    assert result.scanned_files == 2
    assert any("does_not_exist.md" in e for e in result.errors)
    # 0.1.1: files_with_errors is a first-class field, counted at
    # iteration time. Only one file (links.md) has any error.
    assert result.files_with_errors == 1


def test_validate_directory_files_with_errors_counts_each_file_once(
    make_repo: Callable[..., Path],
) -> None:
    """Regression test for the 0.1.1 fix: a single markdown file that
    has both a broken-anchor error (prefixed with the absolute Path) and
    a broken-link error (prefixed with the path relative to repo_root)
    must still be counted as one file, not two. The 0.1.0 CLI heuristic
    string-deduped error prefixes and double-counted in this case.
    """
    repo_root = make_repo()
    md_file = repo_root / "page.md"
    md_file.write_text(
        "\n".join(
            [
                "# Heading One",
                "",
                "[missing-file](does_not_exist.md)",  # broken link -> rel_source prefix
                "[bad-anchor](#nope)",  # broken anchor -> absolute Path prefix
            ]
        ),
        encoding="utf-8",
    )

    result = validate_directory(repo_root, cross_repo_mode="skip")

    assert result.ok is False
    # Two errors, but they come from the same single file:
    assert len(result.errors) == 2
    assert result.files_with_errors == 1


def test_validate_directory_passes_clean_repo(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    (repo_root / "README.md").write_text("# Hello\n", encoding="utf-8")

    result = validate_directory(repo_root, cross_repo_mode="skip")

    assert result.ok is True
    assert result.errors == []
    assert result.scanned_files == 1


def test_validate_directory_rejects_invalid_cross_repo_mode(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    with pytest.raises(ValueError, match="cross_repo_mode must be one of"):
        validate_directory(repo_root, cross_repo_mode="bogus")


def test_validate_directory_falls_back_to_skip_when_ecosystem_root_not_found(
    make_repo: Callable[..., Path],
) -> None:
    repo_root = make_repo()
    (repo_root / "README.md").write_text(
        "# Title\n[cross](../juniper-data/README.md)\n",
        encoding="utf-8",
    )

    # ecosystem_root=None, cross_repo_mode="check" -> discovery returns None
    # (we're in tmp_path, not a real ecosystem) -> falls back to skip
    with mock.patch.object(cdl, "discover_ecosystem_root", return_value=None):
        result = validate_directory(repo_root, cross_repo_mode="check")

    assert result.ok is True
    assert result.cross_repo_skipped == 1
