"""Tests for :mod:`juniper_doc_tools.cli` -- argparse + main()."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from juniper_doc_tools import __version__
from juniper_doc_tools.cli import main


def test_main_passes_clean_repo(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    (repo_root / "README.md").write_text("# Hello\n", encoding="utf-8")

    exit_code = main(["--repo-root", str(repo_root), "--cross-repo", "skip"])
    assert exit_code == 0


def test_main_returns_one_on_broken_link(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    (repo_root / "README.md").write_text(
        "# Title\n[bad](does_not_exist.md)\n",
        encoding="utf-8",
    )

    exit_code = main(["--repo-root", str(repo_root), "--cross-repo", "skip"])
    assert exit_code == 1


def test_main_rejects_invalid_cross_repo_mode(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    with pytest.raises(SystemExit) as exc_info:
        main(["--repo-root", str(repo_root), "--cross-repo", "bogus"])
    # argparse raises SystemExit(2) on invalid choices
    assert exc_info.value.code == 2


def test_main_exclude_flag_filters_directories(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    docs = repo_root / "docs"
    templates = repo_root / "templates"
    docs.mkdir()
    templates.mkdir()
    (docs / "ok.md").write_text("# ok\n", encoding="utf-8")
    # templates/ contains a broken link; if we don't exclude it the run fails.
    (templates / "bad.md").write_text(
        "# Title\n[bad](nope.md)\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--exclude",
            "templates",
            "--cross-repo",
            "skip",
        ]
    )
    assert exit_code == 0


def test_main_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_main_strict_repo_boundary_surfaces_eco_root_link_as_error(
    make_repo: Callable[..., Path],
) -> None:
    """End-to-end: when ``--strict-repo-boundary`` is passed, the CLI
    must fail on an ``../../CLAUDE.md`` link instead of silently
    skipping it under ``--cross-repo skip``.
    """
    repo_root = make_repo("juniper-data")
    docs = repo_root / "docs"
    docs.mkdir()
    (docs / "X.md").write_text(
        "# Title\n[Juniper](../../CLAUDE.md)\n",
        encoding="utf-8",
    )

    # Without --strict-repo-boundary: skip mode classifies the link.
    assert (
        main(
            [
                "--repo-root",
                str(repo_root),
                "--cross-repo",
                "skip",
            ]
        )
        == 0
    )

    # With --strict-repo-boundary: link surfaces as an error.
    assert (
        main(
            [
                "--repo-root",
                str(repo_root),
                "--cross-repo",
                "skip",
                "--strict-repo-boundary",
            ]
        )
        == 1
    )


def test_module_form_invocation_runs_cli(
    tmp_path: Path,
    make_repo: Callable[..., Path],
) -> None:
    """``python -m juniper_doc_tools`` must route through cli.main and
    return the same exit code as the console script. Confirms the
    decision from plan §8.3 holds end-to-end.
    """
    import subprocess
    import sys

    repo_root = make_repo()
    (repo_root / "README.md").write_text("# Hello\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "juniper_doc_tools",
            "--repo-root",
            str(repo_root),
            "--cross-repo",
            "skip",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "PASSED" in result.stdout


def test_main_positional_paths_limit_scan_scope(make_repo: Callable[..., Path]) -> None:
    repo_root = make_repo()
    docs = repo_root / "docs"
    notes = repo_root / "notes"
    docs.mkdir()
    notes.mkdir()
    (docs / "ok.md").write_text("# ok\n", encoding="utf-8")
    # notes/ has a broken link, but we'll only scan docs/
    (notes / "bad.md").write_text(
        "# Title\n[bad](does_not_exist.md)\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--cross-repo",
            "skip",
            "docs",
        ]
    )
    assert exit_code == 0
