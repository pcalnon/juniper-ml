"""Tests for util/install_agents.bash (custom-agent suite PR 6a).

The mirror symlinks `.claude/{agents,skills}/*` into `~/.claude` so the suite is available
cross-repo (design D-6). These tests drive the script against a SYNTHETIC source repo and a
throwaway target dir (via the `JUNIPER_ML_REPO_ROOT` / `JUNIPER_CLAUDE_HOME` overrides) and
assert it is idempotent, reversible, `--dry-run`-safe, and never clobbers or removes a file
it does not own.

Location-agnostic: discovers the repo root by walking up for `.github/workflows/`.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_SCRIPT = _REPO_ROOT / "util" / "install_agents.bash"


def _make_source(root: Path) -> None:
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "skills" / "sample-skill").mkdir(parents=True)
    (root / ".claude" / "agents" / "sample-agent.md").write_text("---\nname: sample-agent\n---\nbody\n", encoding="utf-8")
    (root / ".claude" / "skills" / "sample-skill" / "SKILL.md").write_text("---\nname: sample-skill\n---\nbody\n", encoding="utf-8")


class InstallAgentsTest(unittest.TestCase):
    def setUp(self):
        self._src_tmp = tempfile.TemporaryDirectory()
        self._tgt_tmp = tempfile.TemporaryDirectory()
        self.src = Path(self._src_tmp.name)
        self.tgt = Path(self._tgt_tmp.name)
        _make_source(self.src)

    def tearDown(self):
        self._src_tmp.cleanup()
        self._tgt_tmp.cleanup()

    def _run(self, *args):
        env = RedactedEnv(os.environ, JUNIPER_ML_REPO_ROOT=str(self.src), JUNIPER_CLAUDE_HOME=str(self.tgt))
        return subprocess.run(["bash", str(_SCRIPT), *args], capture_output=True, text=True, check=False, timeout=60, env=env)

    def test_script_exists_and_parses(self):
        self.assertTrue(_SCRIPT.exists(), f"missing {_SCRIPT}")
        proc = subprocess.run(["bash", "-n", str(_SCRIPT)], capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_install_creates_symlinks(self):
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        agent_link = self.tgt / "agents" / "sample-agent.md"
        skill_link = self.tgt / "skills" / "sample-skill"
        self.assertTrue(agent_link.is_symlink())
        self.assertTrue(skill_link.is_symlink())
        self.assertEqual(os.readlink(agent_link), str(self.src / ".claude" / "agents" / "sample-agent.md"))
        self.assertEqual(os.readlink(skill_link), str(self.src / ".claude" / "skills" / "sample-skill"))

    def test_idempotent(self):
        self.assertEqual(self._run().returncode, 0)
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("already linked", proc.stdout)
        self.assertTrue((self.tgt / "agents" / "sample-agent.md").is_symlink())

    def test_dry_run_touches_nothing(self):
        proc = self._run("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.tgt / "agents").exists(), "dry-run must not create anything")

    def test_reverse_removes_owned_links(self):
        self._run()
        self.assertTrue((self.tgt / "agents" / "sample-agent.md").is_symlink())
        proc = self._run("--reverse")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.tgt / "agents" / "sample-agent.md").exists())
        self.assertFalse((self.tgt / "skills" / "sample-skill").exists())

    def test_reverse_leaves_foreign_files(self):
        (self.tgt / "agents").mkdir(parents=True)
        foreign = self.tgt / "agents" / "user-own.md"
        foreign.write_text("mine\n", encoding="utf-8")
        self._run()
        self._run("--reverse")
        self.assertTrue(foreign.exists(), "reverse must not remove a file it does not own")

    def test_install_refuses_to_clobber_nonsymlink(self):
        (self.tgt / "agents").mkdir(parents=True)
        clash = self.tgt / "agents" / "sample-agent.md"
        clash.write_text("preexisting\n", encoding="utf-8")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(clash.is_symlink())
        self.assertEqual(clash.read_text(encoding="utf-8"), "preexisting\n")
        self.assertIn("refusing to clobber", proc.stdout)


if __name__ == "__main__":
    unittest.main()
