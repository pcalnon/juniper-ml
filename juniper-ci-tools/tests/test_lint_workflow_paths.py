"""Tests for the workflow-script-path lint module.

Mirrors the behavior previously covered by the byte-identical copies
of ``util/test_workflow_script_paths.py`` that lived in 6 consumer
repos pre-consolidation. Adds CLI tests for the new
``juniper-lint-workflow-paths`` console script.
"""

from __future__ import annotations

import io
import json
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from juniper_ci_tools.cli_lint_workflow_paths import main as cli_main
from juniper_ci_tools.lint_workflow_paths import (
    DEFAULT_ECOSYSTEM_SIBLING_PREFIXES,
    extract_script_paths,
    find_repo_root,
    is_validatable,
    lint_workflow_paths,
)


def _make_repo(tmp: Path, workflows: dict[str, str], files: list[str]) -> Path:
    """Build a synthetic repo with the given workflow files (filename ->
    YAML text) and on-disk files (relative paths)."""
    (tmp / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    for name, content in workflows.items():
        (tmp / ".github" / "workflows" / name).write_text(content, encoding="utf-8")
    for rel in files:
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# placeholder\n", encoding="utf-8")
    return tmp


class ScriptPathExtractionTest(unittest.TestCase):
    """Direct unit tests for the parsing helpers."""

    def test_extracts_python_script_invocation(self):
        yaml_text = textwrap.dedent(
            """\
            jobs:
              docs:
                steps:
                  - run: python scripts/check_doc_links.py --exclude templates
            """
        )
        self.assertEqual(extract_script_paths(yaml_text), {"scripts/check_doc_links.py"})

    def test_extracts_python3_with_minor_version(self):
        yaml_text = "jobs:\n  t:\n    steps:\n      - run: python3.14 util/foo.py --bar\n"
        self.assertEqual(extract_script_paths(yaml_text), {"util/foo.py"})

    def test_extracts_bash_script_invocation(self):
        yaml_text = "jobs:\n  t:\n    steps:\n      - run: bash util/generate_dep_docs.bash\n"
        self.assertEqual(extract_script_paths(yaml_text), {"util/generate_dep_docs.bash"})

    def test_extracts_unittest_positional_test_files(self):
        yaml_text = "jobs:\n  t:\n    steps:\n      - run: python3 -m unittest -v tests/test_foo.py\n"
        self.assertEqual(extract_script_paths(yaml_text), {"tests/test_foo.py"})

    def test_ignores_invalid_yaml(self):
        # Garbage YAML returns an empty set rather than raising.
        self.assertEqual(extract_script_paths("not: [valid: yaml"), set())


class IsValidatableTest(unittest.TestCase):
    def test_skips_cross_repo_prefix_paths(self):
        self.assertFalse(is_validatable("juniper-ml/util/foo.bash"))
        self.assertFalse(is_validatable("juniper-data/scripts/bar.py"))

    def test_validates_intra_repo_paths(self):
        self.assertTrue(is_validatable("scripts/check_doc_links.py"))
        self.assertTrue(is_validatable("util/generate_dep_docs.sh"))
        self.assertTrue(is_validatable("tests/test_foo.py"))

    def test_skips_absolute_and_variable_paths(self):
        self.assertFalse(is_validatable("/usr/local/bin/foo.py"))
        self.assertFalse(is_validatable("${{ env.SCRIPT }}/foo.py"))
        self.assertFalse(is_validatable("$(get_path)/foo.sh"))
        # standalone filename without a directory -- ambiguous, skip
        self.assertFalse(is_validatable("foo.py"))

    def test_default_sibling_prefixes_cover_juniper_ecosystem(self):
        self.assertIn("juniper-canopy/", DEFAULT_ECOSYSTEM_SIBLING_PREFIXES)
        self.assertIn("juniper-deploy/", DEFAULT_ECOSYSTEM_SIBLING_PREFIXES)
        self.assertEqual(len(DEFAULT_ECOSYSTEM_SIBLING_PREFIXES), 8)

    def test_custom_sibling_prefixes_override(self):
        custom = ("vendor/", "external/")
        self.assertFalse(is_validatable("vendor/lib/foo.py", sibling_prefixes=custom))
        self.assertTrue(is_validatable("juniper-ml/foo.py", sibling_prefixes=custom))


class FindRepoRootTest(unittest.TestCase):
    def test_finds_root_via_dot_github_workflows(self):
        with TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-repo"
            (fake / ".github" / "workflows").mkdir(parents=True)
            nested = fake / "deep" / "nested" / "tests"
            nested.mkdir(parents=True)
            self.assertEqual(find_repo_root(nested), fake)
            self.assertEqual(find_repo_root(nested / "more"), fake)

    def test_raises_when_no_dot_github_workflows_in_ancestors(self):
        with TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "isolated"
            isolated.mkdir()
            with self.assertRaises(RuntimeError):
                find_repo_root(isolated)


class LintWorkflowPathsTest(unittest.TestCase):
    def test_no_findings_when_all_paths_exist(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": ("jobs:\n  t:\n    steps:\n      - run: bash scripts/foo.sh\n      - run: python tests/test_bar.py\n")},
                files=["scripts/foo.sh", "tests/test_bar.py"],
            )
            result = lint_workflow_paths(repo)
            self.assertTrue(result.ok)
            self.assertEqual(result.missing, ())
            self.assertEqual(len(result.workflow_files), 1)

    def test_finds_missing_path(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={
                    "ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash scripts/missing.sh\n",
                },
                files=[],
            )
            result = lint_workflow_paths(repo)
            self.assertFalse(result.ok)
            self.assertEqual(len(result.missing), 1)
            self.assertEqual(result.missing[0].path, "scripts/missing.sh")

    def test_skips_cross_repo_paths(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": ("jobs:\n  t:\n    steps:\n      - run: bash juniper-ml/util/sibling.bash\n      - run: python juniper-data/scripts/sib.py\n")},
                files=[],
            )
            result = lint_workflow_paths(repo)
            self.assertTrue(result.ok)  # cross-repo paths are skipped, not failed
            self.assertEqual(result.missing, ())

    def test_report_summarizes_findings(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash scripts/gone.sh\n"},
                files=[],
            )
            result = lint_workflow_paths(repo)
            report = result.report()
            self.assertIn("missing path 'scripts/gone.sh'", report)
            self.assertIn("ci.yml", report)
            self.assertIn("2026-05-18", report)  # incident reference preserved

    def test_yaml_and_yml_files_both_discovered(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={
                    "ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash a/foo.sh\n",
                    "alt.yaml": "jobs:\n  u:\n    steps:\n      - run: bash a/bar.sh\n",
                },
                files=["a/foo.sh", "a/bar.sh"],
            )
            result = lint_workflow_paths(repo)
            self.assertEqual(len(result.workflow_files), 2)
            self.assertTrue(result.ok)


class CliTest(unittest.TestCase):
    def _run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = cli_main(args)
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_cli_exit_zero_when_clean(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash a/foo.sh\n"},
                files=["a/foo.sh"],
            )
            rc, out, _ = self._run_cli(["--repo-root", str(repo)])
            self.assertEqual(rc, 0)
            self.assertIn("OK:", out)

    def test_cli_exit_one_on_missing(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash a/gone.sh\n"},
                files=[],
            )
            rc, out, _ = self._run_cli(["--repo-root", str(repo)])
            self.assertEqual(rc, 1)
            self.assertIn("missing path 'a/gone.sh'", out)

    def test_cli_exit_zero_with_flag(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash a/gone.sh\n"},
                files=[],
            )
            rc, _, _ = self._run_cli(["--repo-root", str(repo), "--exit-zero"])
            self.assertEqual(rc, 0)

    def test_cli_json_output(self):
        with TemporaryDirectory() as tmp:
            repo = _make_repo(
                Path(tmp),
                workflows={"ci.yml": "jobs:\n  t:\n    steps:\n      - run: bash a/gone.sh\n"},
                files=[],
            )
            rc, out, _ = self._run_cli(["--repo-root", str(repo), "--json"])
            payload = json.loads(out)
            self.assertEqual(rc, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["missing"][0]["path"], "a/gone.sh")
            self.assertEqual(payload["missing"][0]["workflow"], ".github/workflows/ci.yml")

    def test_cli_exit_two_when_repo_root_missing(self):
        rc, _, err = self._run_cli(["--repo-root", "/nonexistent/path/asdf"])
        self.assertEqual(rc, 2)
        self.assertIn("not a directory", err)

    def test_cli_exit_two_when_workflows_dir_missing(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".github" / "workflows").mkdir(parents=True)
            rc, _, err = self._run_cli(
                [
                    "--repo-root",
                    tmp,
                    "--workflows-dir",
                    str(Path(tmp) / "not-there"),
                ]
            )
            self.assertEqual(rc, 2)
            self.assertIn("workflows directory not found", err)


if __name__ == "__main__":
    unittest.main()
