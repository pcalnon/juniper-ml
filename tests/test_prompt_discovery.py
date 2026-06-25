"""Behavioural tests for util/prompt_discovery/ (custom-agent suite PR 4).

Covers the design's CI-objective acceptance for the discovery helpers (S5.6, S8): the
grounding-bundle schema, the provenance envelope, the per-probe graceful degradation, and
-- the dominant grounding hazard -- the ``test_status`` ``cold_cache``/empty distinction
(so "no failures" can never masquerade as fact when the truth is "not measured").

``util/`` is not a package, so the probes are imported via the house ``sys.path.insert``
idiom (matching tests/test_editable_install_drift_check.py). Location-agnostic: the repo
root is discovered by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_PD_DIR = _REPO_ROOT / "util" / "prompt_discovery"
sys.path.insert(0, str(_PD_DIR))

import conventions  # noqa: E402
import dependency_facts  # noqa: E402
import file_probe  # noqa: E402
import repo_context  # noqa: E402
import symbol_probe  # noqa: E402
import test_status  # noqa: E402

_SHA40 = r"^[0-9a-f]{40}$"
_PROBE_KEYS = {"repo_context", "test_status", "file_probe", "symbol_probe", "dependency_facts", "conventions", "concurrency"}


class RepoContextProbeTest(unittest.TestCase):
    def test_real_repo_resolves_head(self):
        ctx = repo_context.probe(str(_REPO_ROOT))
        self.assertEqual(ctx["status"], "ok")
        self.assertRegex(ctx["head_sha"], _SHA40)
        self.assertTrue(ctx["repo"])

    def test_non_git_dir_is_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = repo_context.probe(d)
            self.assertEqual(ctx["status"], "unavailable")
            self.assertIsNone(ctx["head_sha"])


class TestStatusProbeTest(unittest.TestCase):
    """The cold_cache/empty distinction is the headline grounding-hazard guard."""

    def test_cold_cache_when_never_run(self):
        with tempfile.TemporaryDirectory() as d:
            res = test_status.probe(d)
            self.assertEqual(res["status"], "cold_cache")
            self.assertIsNone(res["failing_count"])

    def test_empty_cache_means_zero_failures(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".pytest_cache" / "v" / "cache").mkdir(parents=True)
            res = test_status.probe(d)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["failing_count"], 0)

    def test_failing_names_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / ".pytest_cache" / "v" / "cache"
            cache.mkdir(parents=True)
            (cache / "lastfailed").write_text('{"tests/test_x.py::test_a": true}', encoding="utf-8")
            res = test_status.probe(d)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["failing_count"], 1)
            self.assertIn("tests/test_x.py::test_a", res["failing"])


class DependencyFactsProbeTest(unittest.TestCase):
    def test_real_pyproject_surface(self):
        dep = dependency_facts.probe(str(_REPO_ROOT))
        self.assertEqual(dep["status"], "ok")
        self.assertIsNotNone(dep["version"])
        self.assertIn("clients", dep["extras"])
        self.assertIn("worker", dep["extras"])


class ConventionsProbeTest(unittest.TestCase):
    def test_real_agents_md_header(self):
        conv = conventions.probe(str(_REPO_ROOT))
        self.assertEqual(conv["line_length"], 512)
        self.assertIn("Project", conv["agents_md_header"])
        self.assertIn("Version", conv["agents_md_header"])


class SymbolProbeTest(unittest.TestCase):
    def test_resolved_and_unresolved(self):
        sp = symbol_probe.probe(str(_REPO_ROOT), ["register_or_reuse", "this_symbol_does_not_exist_zzz"])
        self.assertEqual(sp["symbols"]["register_or_reuse"]["status"], "resolved")
        self.assertIsNotNone(sp["symbols"]["register_or_reuse"]["definition"])
        self.assertEqual(sp["symbols"]["this_symbol_does_not_exist_zzz"]["status"], "unresolved")


class FileProbeTest(unittest.TestCase):
    def test_subject_yields_anchors(self):
        fp = file_probe.probe(str(_REPO_ROOT), "register_or_reuse")
        self.assertEqual(fp["status"], "ok")
        self.assertTrue(fp["anchors"], "expected at least one anchor for a known symbol")
        self.assertIsInstance(fp["anchors"][0]["line"], int)

    def test_no_subject_yields_no_anchors(self):
        fp = file_probe.probe(str(_REPO_ROOT), None)
        self.assertEqual(fp["anchors"], [])


class CliBundleTest(unittest.TestCase):
    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(_PD_DIR / "cli.py"), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

    def test_bundle_schema_and_provenance(self):
        proc = self._run_cli("--repo-root", str(_REPO_ROOT), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        bundle = json.loads(proc.stdout)
        self.assertEqual(bundle["schema_version"], 1)
        for key in _PROBE_KEYS | {"provenance"}:
            self.assertIn(key, bundle)
        prov = bundle["provenance"]
        for key in ("captured_at", "head_sha", "dirty", "ttl_seconds", "per_probe_status"):
            self.assertIn(key, prov)
        self.assertRegex(prov["head_sha"], _SHA40)
        self.assertIsInstance(prov["ttl_seconds"], int)
        self.assertEqual(set(prov["per_probe_status"]), _PROBE_KEYS)

    def test_head_sha_matches_git(self):
        proc = self._run_cli("--repo-root", str(_REPO_ROOT))
        bundle = json.loads(proc.stdout)
        git = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(bundle["provenance"]["head_sha"], git.stdout.strip())

    def test_hard_stop_on_non_git_root(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self._run_cli("--repo-root", d)
            self.assertEqual(proc.returncode, 2, "discovery failure must be a hard stop (exit 2)")
            envelope = json.loads(proc.stdout)
            self.assertEqual(envelope["status"], "discovery_failed")


if __name__ == "__main__":
    unittest.main()
