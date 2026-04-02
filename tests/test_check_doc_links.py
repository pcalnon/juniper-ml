"""Targeted regression tests for util/check_doc_links.py."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


def _load_check_doc_links_module():
    module_path = Path(__file__).resolve().parent.parent / "util" / "check_doc_links.py"
    spec = importlib.util.spec_from_file_location("check_doc_links", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load check_doc_links module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_doc_links = _load_check_doc_links_module()


class ValidateFileBehaviorTests(unittest.TestCase):
    def test_ignores_links_in_code_blocks_and_inline_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()
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

            errors, cross_repo_count = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="check",
                ecosystem_root=repo_root.parent,
            )

            self.assertEqual(errors, [])
            self.assertEqual(cross_repo_count, 0)

    def test_rejects_absolute_paths_and_excessive_traversal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()

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

            errors, _ = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="check",
                ecosystem_root=repo_root.parent,
            )

            self.assertEqual(len(errors), 2)
            self.assertTrue(any("absolute path in documentation link" in error for error in errors))
            self.assertTrue(any("excessive directory traversal" in error for error in errors))

    def test_cross_repo_skip_counts_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "juniper-ml"
            repo_root.mkdir()

            md_file = repo_root / "README.md"
            md_file.write_text(
                "# Title\n[cross](../juniper-data/README.md)\n",
                encoding="utf-8",
            )

            errors, cross_repo_count = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="skip",
                ecosystem_root=None,
            )

            self.assertEqual(errors, [])
            self.assertEqual(cross_repo_count, 1)

    def test_cross_repo_escape_is_error_even_when_skipping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "juniper-ml"
            repo_root.mkdir()

            md_file = repo_root / "README.md"
            md_file.write_text(
                "# Title\n[escape](../juniper-data/../../etc/passwd)\n",
                encoding="utf-8",
            )

            errors, cross_repo_count = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="skip",
                ecosystem_root=None,
            )

            self.assertEqual(cross_repo_count, 0)
            self.assertEqual(len(errors), 1)
            self.assertIn("cross-repo link escapes target repository", errors[0])

    def test_cross_repo_check_validates_target_in_sibling_repo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ecosystem_root = Path(temp_dir) / "ecosystem"
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

            errors, cross_repo_count = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="check",
                ecosystem_root=ecosystem_root,
            )

            self.assertEqual(cross_repo_count, 0)
            self.assertEqual(len(errors), 1)
            self.assertIn("file not found in juniper-data", errors[0])

    def test_cross_repo_warn_prints_warning_and_counts_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "juniper-ml"
            repo_root.mkdir()

            md_file = repo_root / "README.md"
            md_file.write_text(
                "# Title\n[cross](../juniper-data/README.md)\n",
                encoding="utf-8",
            )

            buffer = StringIO()
            with redirect_stdout(buffer):
                errors, cross_repo_count = check_doc_links._validate_file(
                    md_file=md_file,
                    repo_root=repo_root,
                    cross_repo_mode="warn",
                    ecosystem_root=None,
                )

            self.assertEqual(errors, [])
            self.assertEqual(cross_repo_count, 1)
            self.assertIn("WARN (cross-repo): README.md:2 -> ../juniper-data/README.md", buffer.getvalue())

    def test_rejects_null_byte_and_out_of_bounds_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()

            md_file = repo_root / "README.md"
            md_file.write_text(
                "\n".join(
                    [
                        "# Title",
                        "[null-byte](bad\x00target.md)",
                        "[outside](../../outside.md)",
                    ]
                ),
                encoding="utf-8",
            )

            errors, _ = check_doc_links._validate_file(
                md_file=md_file,
                repo_root=repo_root,
                cross_repo_mode="check",
                ecosystem_root=repo_root.parent,
            )

            self.assertEqual(len(errors), 2)
            self.assertTrue(any("null byte in link target" in error for error in errors))
            self.assertTrue(any("link resolves outside repository boundary" in error for error in errors))


class EcosystemDiscoveryAndCliTests(unittest.TestCase):
    def test_discover_ecosystem_root_uses_git_common_dir_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ecosystem_root = Path(temp_dir) / "Juniper"
            repo_root = ecosystem_root / "juniper-ml"
            repo_root.mkdir(parents=True)
            (ecosystem_root / "juniper-data").mkdir()
            (ecosystem_root / "juniper-cascor").mkdir()

            git_result = mock.Mock(returncode=0, stdout=".git\n")
            with mock.patch.object(check_doc_links.subprocess, "run", return_value=git_result):
                discovered = check_doc_links._discover_ecosystem_root(repo_root)

            self.assertEqual(discovered, ecosystem_root)

    def test_discover_ecosystem_root_falls_back_when_git_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ecosystem_root = Path(temp_dir) / "Juniper"
            repo_root = ecosystem_root / "juniper-ml"
            repo_root.mkdir(parents=True)
            (ecosystem_root / "juniper-data").mkdir()
            (ecosystem_root / "juniper-cascor").mkdir()

            with mock.patch.object(check_doc_links.subprocess, "run", side_effect=FileNotFoundError):
                discovered = check_doc_links._discover_ecosystem_root(repo_root)

            self.assertEqual(discovered, ecosystem_root)

    def test_main_returns_error_on_invalid_cross_repo_mode(self):
        buffer = StringIO()
        with mock.patch.object(check_doc_links.sys, "argv", ["check_doc_links.py", "--cross-repo", "invalid"]):
            with redirect_stdout(buffer):
                result = check_doc_links.main()

        self.assertEqual(result, 1)
        self.assertIn("--cross-repo must be one of", buffer.getvalue())

    def test_main_falls_back_to_skip_when_ecosystem_root_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "juniper-ml"
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True)
            (repo_root / "README.md").write_text(
                "# Title\n[cross](../juniper-data/README.md)\n",
                encoding="utf-8",
            )
            fake_script = scripts_dir / "check_doc_links.py"
            fake_script.write_text("# placeholder\n", encoding="utf-8")

            buffer = StringIO()
            with mock.patch.object(check_doc_links, "__file__", str(fake_script)):
                with mock.patch.object(check_doc_links, "_discover_ecosystem_root", return_value=None):
                    with mock.patch.object(check_doc_links.sys, "argv", ["check_doc_links.py"]):
                        with redirect_stdout(buffer):
                            result = check_doc_links.main()

            output = buffer.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("WARNING: Ecosystem root not found. Cross-repo links will be skipped.", output)
            self.assertIn("Cross-repo links: skip", output)
            self.assertIn("Cross-repo links skipped: 1", output)


if __name__ == "__main__":
    unittest.main()
