"""Tests for :mod:`juniper_ci_tools.lint_agents_md_header` and the
:program:`juniper-lint-agents-md-header` CLI.

Mirrors ``test_lint_agents_md_version.py``: synthetic repos under
``TemporaryDirectory()`` exercising the library API, then CLI
exit-code matrix tests that drive ``cli_main`` directly via
``argv=[...]`` (no subprocess overhead).
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from juniper_ci_tools.cli_lint_agents_md_header import main as cli_main
from juniper_ci_tools.lint_agents_md_header import (
    REQUIRED_FIELDS,
    RepoRootNotFoundError,
    extract_header_bullets,
    find_agents_md_header_repo_root,
    lint_agents_md_header,
)


def _write_repo(
    root: Path,
    *,
    project: str | None = "demo — Example Project",
    repository: str | None = "pcalnon/demo",
    author: str | None = "Paul Calnon",
    license_: str | None = "MIT License",
    version: str | None = "1.2.3",
    last_updated: str | None = "2026-05-22",
    extras: tuple[tuple[str, str], ...] = (),
    custom_body: str | None = None,
) -> None:
    """Write a synthetic AGENTS.md + .github/ structure under ``root``.

    Any field passed as ``None`` is omitted from the header. ``extras``
    is a tuple of additional ``(field, value)`` bullets appended after
    the required block. ``custom_body`` overrides the whole bullet
    block when present (caller supplies raw markdown).
    """
    (root / ".github").mkdir(exist_ok=True)
    if custom_body is not None:
        text = custom_body
    else:
        bullets = []
        spec = (
            ("Project", project),
            ("Repository", repository),
            ("Author", author),
            ("License", license_),
            ("Version", version),
            ("Last Updated", last_updated),
        )
        for field, value in spec:
            if value is not None:
                bullets.append(f"**{field}**: {value}")
        for field, value in extras:
            bullets.append(f"**{field}**: {value}")
        text = "# Demo AGENTS.md\n\n" + "\n".join(bullets) + "\n\n---\n\nBody.\n"
    (root / "AGENTS.md").write_text(text, encoding="utf-8")


class FindAgentsMdHeaderRepoRootTest(unittest.TestCase):
    """Walk-up discovery requires AGENTS.md + .github/ co-located."""

    def test_finds_root_from_subdirectory(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            sub = root / "src" / "deep" / "nested"
            sub.mkdir(parents=True)
            self.assertEqual(find_agents_md_header_repo_root(sub), root)

    def test_finds_root_from_file(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            file_path = root / "src" / "thing.py"
            file_path.parent.mkdir(parents=True)
            file_path.write_text("# stub\n", encoding="utf-8")
            self.assertEqual(find_agents_md_header_repo_root(file_path), root)

    def test_raises_when_no_repo_root(self) -> None:
        with TemporaryDirectory() as td:
            with self.assertRaises(RepoRootNotFoundError):
                find_agents_md_header_repo_root(Path(td))

    def test_requires_dot_github_directory(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("# stub\n", encoding="utf-8")
            # No .github/ directory.
            with self.assertRaises(RepoRootNotFoundError):
                find_agents_md_header_repo_root(root)


class ExtractHeaderBulletsTest(unittest.TestCase):
    """The header is everything before the first ``---`` or ``## ``."""

    def test_stops_at_horizontal_rule(self) -> None:
        text = "**Project**: A\n**Version**: 1.0\n\n---\n\n**Other**: should-not-appear\n"
        self.assertEqual(extract_header_bullets(text), [("Project", "A"), ("Version", "1.0")])

    def test_stops_at_h2_heading(self) -> None:
        text = "**Project**: A\n\n## Section\n\n**Other**: should-not-appear\n"
        self.assertEqual(extract_header_bullets(text), [("Project", "A")])

    def test_empty_when_no_bullets(self) -> None:
        self.assertEqual(extract_header_bullets("# Title\n\nBody.\n"), [])


class LintAgentsMdHeaderTest(unittest.TestCase):
    """Library-level :func:`lint_agents_md_header` behaviour."""

    def test_conformant_header_is_not_drift(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            result = lint_agents_md_header(repo_root=root)
            self.assertFalse(result.is_drift)
            self.assertEqual(result.missing_fields, ())
            self.assertEqual(result.order_violations, ())
            self.assertEqual(result.empty_value_fields, ())
            self.assertIsNone(result.bad_last_updated_value)
            self.assertIn("OK", result.render())

    def test_missing_field_detected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, repository=None)
            result = lint_agents_md_header(repo_root=root)
            self.assertTrue(result.is_drift)
            self.assertEqual(result.missing_fields, ("Repository",))

    def test_multiple_missing_fields(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, repository=None, author=None, last_updated=None)
            result = lint_agents_md_header(repo_root=root)
            self.assertTrue(result.is_drift)
            self.assertEqual(set(result.missing_fields), {"Repository", "Author", "Last Updated"})

    def test_wrong_relative_order_detected(self) -> None:
        # Author before Repository.
        body = (
            "# Demo\n\n"
            + "\n".join(
                [
                    "**Project**: A",
                    "**Author**: Paul",
                    "**Repository**: pcalnon/x",
                    "**License**: MIT",
                    "**Version**: 1.0",
                    "**Last Updated**: 2026-05-22",
                ]
            )
            + "\n\n---\n"
        )
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, custom_body=body)
            result = lint_agents_md_header(repo_root=root)
            self.assertTrue(result.is_drift)
            self.assertEqual(
                result.order_violations,
                ("Project", "Author", "Repository", "License", "Version", "Last Updated"),
            )

    def test_extras_between_required_fields_allowed(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, extras=(("Python", ">=3.11"),))
            result = lint_agents_md_header(repo_root=root)
            self.assertFalse(result.is_drift)

    def test_extras_interleaved_with_required_are_allowed(self) -> None:
        # Python interleaved between Author and License.
        body = (
            "# Demo\n\n"
            + "\n".join(
                [
                    "**Project**: A",
                    "**Repository**: pcalnon/x",
                    "**Author**: Paul",
                    "**Python**: >=3.11",
                    "**License**: MIT",
                    "**Version**: 1.0",
                    "**Last Updated**: 2026-05-22",
                ]
            )
            + "\n\n---\n"
        )
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, custom_body=body)
            result = lint_agents_md_header(repo_root=root)
            self.assertFalse(result.is_drift)

    def test_empty_value_detected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, repository="   ")
            result = lint_agents_md_header(repo_root=root)
            self.assertTrue(result.is_drift)
            self.assertIn("Repository", result.empty_value_fields)
            # Field is present but with empty value -- distinct from
            # missing-field. ``Repository`` should still appear in the
            # bullets list (with empty value), not in ``missing_fields``.
            self.assertNotIn("Repository", result.missing_fields)

    def test_bad_last_updated_format_detected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, last_updated="May 22, 2026")
            result = lint_agents_md_header(repo_root=root)
            self.assertTrue(result.is_drift)
            self.assertEqual(result.bad_last_updated_value, "May 22, 2026")

    def test_missing_agents_md_raises(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".github").mkdir()
            with self.assertRaises(FileNotFoundError):
                lint_agents_md_header(repo_root=root)

    def test_autodiscovery_from_start_path(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            sub = root / "deep" / "nested"
            sub.mkdir(parents=True)
            result = lint_agents_md_header(start=sub)
            self.assertEqual(result.repo_root, root.resolve())

    def test_required_fields_constant_matches_spec(self) -> None:
        self.assertEqual(
            REQUIRED_FIELDS,
            ("Project", "Repository", "Author", "License", "Version", "Last Updated"),
        )


class CliExitCodeMatrixTest(unittest.TestCase):
    """Drive ``cli_main`` directly via argv; assert exit codes."""

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli_main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_conformant_exits_zero(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            code, out, _ = self._run(["--repo-root", str(root)])
            self.assertEqual(code, 0)
            self.assertIn("OK", out)

    def test_drift_exits_one(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, last_updated="not-a-date")
            code, out, _ = self._run(["--repo-root", str(root)])
            self.assertEqual(code, 1)
            self.assertIn("DRIFT", out)

    def test_drift_with_exit_zero_exits_zero(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, last_updated="not-a-date")
            code, out, _ = self._run(["--repo-root", str(root), "--exit-zero"])
            self.assertEqual(code, 0)
            self.assertIn("DRIFT", out)

    def test_repo_root_not_found_exits_two(self) -> None:
        with TemporaryDirectory() as td:
            code, _, err = self._run(["--repo-root", td])
            self.assertEqual(code, 2)
            self.assertIn("does not exist", err)

    def test_json_output_is_machine_readable(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root)
            code, out, _ = self._run(["--repo-root", str(root), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertFalse(payload["is_drift"])
            self.assertEqual(payload["missing_fields"], [])

    def test_json_output_on_drift(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _write_repo(root, last_updated="not-a-date")
            code, out, _ = self._run(["--repo-root", str(root), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(out)
            self.assertTrue(payload["is_drift"])
            self.assertEqual(payload["bad_last_updated_value"], "not-a-date")


if __name__ == "__main__":
    unittest.main()
