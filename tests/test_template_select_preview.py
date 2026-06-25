"""Tests for util/template_select_preview.py (offline template-selection preview).

Drives the REAL manifest (so it also guards selection drift): a task containing a template's
own keyword selects that template; a no-keyword task falls back to ``generic``; the CLI exits
0 and emits the documented JSON shape.

util/ is not a package; the helper is importlib-loaded. Location-agnostic.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE = _REPO_ROOT / "util" / "template_select_preview.py"


def _load():
    spec = importlib.util.spec_from_file_location("template_select_preview", _MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SelectPreviewUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.manifest = cls.mod._load_manifest(_REPO_ROOT)

    def setUp(self):
        if self.manifest is None:
            self.skipTest("manifest.yaml not loadable (PyYAML absent?)")

    def test_failing_tests_keyword_selects_failing_tests(self):
        selected, _ = self.mod.select("the test suite is failing after the refactor", self.manifest)
        self.assertEqual(selected["id"], "failing-tests")
        self.assertTrue(selected["matched"])

    def test_no_keyword_falls_back_to_generic(self):
        selected, ranked = self.mod.select("frobnicate the wizzle component thoroughly", self.manifest)
        self.assertEqual(selected["id"], "generic")
        self.assertEqual(selected["matched"], [])

    def test_rank_never_crashes_and_excludes_generic(self):
        ranked = self.mod.rank("any task text", self.manifest["templates"])
        ids = {r["id"] for r in ranked}
        self.assertNotIn("generic", ids, "the always-match fallback must not appear in the ranked candidates")
        self.assertTrue(all("score" in r and "matched" in r for r in ranked))


class SelectPreviewCliTest(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_MODULE), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_cli_exit_0(self):
        proc = self._run("the test suite is failing", "--repo-root", str(_REPO_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_cli_json_shape(self):
        proc = self._run("the test suite is failing", "--repo-root", str(_REPO_ROOT), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"task", "selected", "candidates"})
        self.assertEqual(data["selected"]["id"], "failing-tests")
        self.assertIsInstance(data["candidates"], list)


if __name__ == "__main__":
    unittest.main()
