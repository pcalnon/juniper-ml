"""Tests for :mod:`juniper_ci_tools.lint_agents_md_version` and the
:program:`juniper-lint-agents-md-version` CLI.

Mirrors the layout / style of ``test_lint_workflow_paths.py``: small
synthetic repos under ``tempfile.TemporaryDirectory()`` exercising the
library API, then CLI exit-code matrix tests that drive ``cli.main``
directly via ``argv=[...]`` (no subprocess overhead).
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from juniper_ci_tools.cli_lint_agents_md_version import main as cli_main
from juniper_ci_tools.lint_agents_md_version import (
    MultipleVersionHeadersError,
    RepoRootNotFoundError,
    find_agents_md_repo_root,
    lint_agents_md_version,
)


def _write_repo(root: Path, *, pyproject_version: str = "1.2.3", agents_md_version: str | None = "1.2.3", agents_md_extra: str = "") -> None:
    """Write a minimal pyproject.toml + AGENTS.md pair to ``root``."""
    (root / "pyproject.toml").write_text(f'[project]\nname = "demo"\nversion = "{pyproject_version}"\n', encoding="utf-8")
    parts = ["# Demo AGENTS.md", ""]
    if agents_md_version is not None:
        parts.append(f"**Version**: {agents_md_version}")
        parts.append("")
    parts.append(agents_md_extra)
    (root / "AGENTS.md").write_text("\n".join(parts), encoding="utf-8")


class FindAgentsMdRepoRootTest(unittest.TestCase):
    """``find_repo_root`` walk-up discovery."""

    def test_finds_root_from_subdirectory(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            sub = root / "src" / "deep" / "nested"
            sub.mkdir(parents=True)
            self.assertEqual(find_agents_md_repo_root(sub), root)

    def test_finds_root_from_file(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            file_path = root / "src" / "thing.py"
            file_path.parent.mkdir(parents=True)
            file_path.write_text("# stub\n", encoding="utf-8")
            self.assertEqual(find_agents_md_repo_root(file_path), root)

    def test_raises_when_no_repo_root(self) -> None:
        with TemporaryDirectory() as td:
            with self.assertRaises(RepoRootNotFoundError):
                find_agents_md_repo_root(Path(td))

    def test_requires_both_pyproject_and_agents_md(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n', encoding="utf-8")
            # No AGENTS.md.
            with self.assertRaises(RepoRootNotFoundError):
                find_agents_md_repo_root(root)


class LintAgentsMdVersionTest(unittest.TestCase):
    """Library-level :func:`lint_agents_md_version` behaviour."""

    def test_in_sync_versions(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="0.5.0", agents_md_version="0.5.0")
            result = lint_agents_md_version(repo_root=root)
            self.assertTrue(result.in_sync)
            self.assertFalse(result.is_drift)
            self.assertEqual(result.pyproject_version, "0.5.0")
            self.assertEqual(result.agents_md_version, "0.5.0")

    def test_drift_detected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="0.5.0", agents_md_version="0.4.0")
            result = lint_agents_md_version(repo_root=root)
            self.assertFalse(result.in_sync)
            self.assertTrue(result.is_drift)
            self.assertEqual(result.pyproject_version, "0.5.0")
            self.assertEqual(result.agents_md_version, "0.4.0")
            self.assertIn("DRIFT", result.render())

    def test_agents_md_without_header_is_opt_out(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="0.5.0", agents_md_version=None)
            result = lint_agents_md_version(repo_root=root)
            self.assertIsNone(result.in_sync)
            self.assertFalse(result.is_drift)
            self.assertIsNone(result.agents_md_version)
            self.assertIn("SKIP", result.render())

    def test_multiple_version_headers_raises(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(
                root,
                pyproject_version="0.5.0",
                agents_md_version="0.5.0",
                agents_md_extra="\n\n**Version**: 0.4.0\n",
            )
            with self.assertRaises(MultipleVersionHeadersError):
                lint_agents_md_version(repo_root=root)

    def test_missing_pyproject_raises(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("**Version**: 1.0.0\n", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                lint_agents_md_version(repo_root=root)

    def test_missing_agents_md_raises(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                lint_agents_md_version(repo_root=root)

    def test_missing_pyproject_version_raises(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
            (root / "AGENTS.md").write_text("**Version**: 1.0.0\n", encoding="utf-8")
            with self.assertRaises(KeyError):
                lint_agents_md_version(repo_root=root)

    def test_autodiscovery_from_start_path(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            sub = root / "deep" / "nested"
            sub.mkdir(parents=True)
            result = lint_agents_md_version(start=sub)
            self.assertEqual(result.repo_root, root.resolve())


class CliTest(unittest.TestCase):
    """End-to-end CLI exit codes via ``cli.main([...])``."""

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = cli_main(argv)
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_exit_zero_when_in_sync(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version="1.0.0")
            rc, out, _ = self._run(["--repo-root", str(root)])
            self.assertEqual(rc, 0)
            self.assertIn("OK", out)

    def test_exit_one_when_drift(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version="0.9.0")
            rc, out, _ = self._run(["--repo-root", str(root)])
            self.assertEqual(rc, 1)
            self.assertIn("DRIFT", out)

    def test_exit_zero_when_drift_and_exit_zero_flag(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version="0.9.0")
            rc, out, _ = self._run(["--repo-root", str(root), "--exit-zero"])
            self.assertEqual(rc, 0)
            self.assertIn("DRIFT", out)

    def test_exit_zero_when_agents_md_opted_out(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version=None)
            rc, out, _ = self._run(["--repo-root", str(root)])
            self.assertEqual(rc, 0)
            self.assertIn("SKIP", out)

    def test_exit_two_when_repo_root_missing(self) -> None:
        with TemporaryDirectory() as td:
            # Pass a directory with no pyproject + AGENTS.md (auto-discovery
            # would fail; explicit --repo-root surfaces FileNotFoundError).
            rc, _, err = self._run(["--repo-root", td])
            self.assertEqual(rc, 2)
            self.assertIn("does not exist", err)

    def test_exit_two_when_autodiscovery_fails(self) -> None:
        # Default repo-root discovery from a temp cwd with no marker files.
        with TemporaryDirectory() as td:
            cwd = Path(td)
            import os

            here = Path.cwd()
            try:
                os.chdir(cwd)
                rc, _, err = self._run([])
            finally:
                os.chdir(here)
            self.assertEqual(rc, 2)
            self.assertIn("Could not locate repo root", err)

    def test_exit_two_when_multiple_headers(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(
                root,
                pyproject_version="1.0.0",
                agents_md_version="1.0.0",
                agents_md_extra="\n\n**Version**: 0.9.0\n",
            )
            rc, _, err = self._run(["--repo-root", str(root)])
            self.assertEqual(rc, 2)
            self.assertIn("multiple", err)

    def test_json_output_in_sync(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version="1.0.0")
            rc, out, _ = self._run(["--repo-root", str(root), "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(out)
            self.assertEqual(payload["pyproject_version"], "1.0.0")
            self.assertEqual(payload["agents_md_version"], "1.0.0")
            self.assertTrue(payload["in_sync"])
            self.assertFalse(payload["is_drift"])

    def test_json_output_drift(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version="0.9.0")
            rc, out, _ = self._run(["--repo-root", str(root), "--json"])
            self.assertEqual(rc, 1)
            payload = json.loads(out)
            self.assertEqual(payload["pyproject_version"], "1.0.0")
            self.assertEqual(payload["agents_md_version"], "0.9.0")
            self.assertFalse(payload["in_sync"])
            self.assertTrue(payload["is_drift"])

    def test_json_output_opt_out(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, pyproject_version="1.0.0", agents_md_version=None)
            rc, out, _ = self._run(["--repo-root", str(root), "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(out)
            self.assertIsNone(payload["agents_md_version"])
            self.assertIsNone(payload["in_sync"])
            self.assertFalse(payload["is_drift"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
