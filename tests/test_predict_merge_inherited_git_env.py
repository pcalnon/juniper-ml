"""Inherited git location variables must not reach predict_merge's scratch.

juniper-ml#2474 drops ``GIT_DIR`` and ``GIT_INDEX_FILE`` so a hook cannot re-initialise
the source or rewrite its index. Two variables from ``git rev-parse --local-env-vars``
were still forwarded:

* ``GIT_SHALLOW_FILE`` naming the branch tip makes ``git merge`` exit 128
  (``refusing to merge unrelated histories``) on a branch that is merely behind main.
* ``GIT_GRAFT_FILE`` that names main as that tip's parent reports ``MERGE-CLEAN`` and
  puts main's file in ``true_delta``.

``GIT_INDEX_FILE`` is already dropped. This suite pins that the source index bytes
stay put when a hook exports it.

Hermetic git fixtures. No network, no ``gh``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=60)
    if cp.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
    return cp


def _fingerprint(repo: Path) -> tuple[bytes, bytes, str]:
    """Index bytes, HEAD bytes, and every ref. ``git status`` is not used: it rewrites the index."""
    return (
        (repo / ".git" / "index").read_bytes(),
        (repo / ".git" / "HEAD").read_bytes(),
        _git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout,
    )


class InheritedGitEnvTest(unittest.TestCase):
    """A behind branch stays NEEDS-UPDATE-BRANCH when a hook exports a location variable."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="predict-merge-git-env-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "config", "user.email", "tests@example.invalid")
        _git(self.repo, "config", "user.name", "Fleet Tests")
        _git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "a.txt").write_text("A0\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "c0")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
        _git(self.repo, "checkout", "-q", "-b", "pr")
        (self.repo / "d.txt").write_text("D\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "add D")
        _git(self.repo, "checkout", "-q", "main")
        (self.repo / "b.txt").write_text("B\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "main moves")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
        self.pr_sha = _git(self.repo, "rev-parse", "pr").stdout.strip()
        self.main_sha = _git(self.repo, "rev-parse", "main").stdout.strip()
        self.before = _fingerprint(self.repo)

    def _simulate(self, env: dict[str, str]) -> dict:
        with mock.patch.dict(os.environ, env):
            return pm.simulate_merge(self.repo, "pr", run_gates=False, scratch_parent=self.tmp)

    def _assert_behind_and_untouched(self, verdict: dict) -> None:
        self.assertEqual(verdict["verdict"], "NEEDS-UPDATE-BRANCH")
        self.assertIs(verdict["behind_main"], True)
        self.assertEqual(verdict["true_delta"], ["d.txt"])
        self.assertEqual(_fingerprint(self.repo), self.before)
        self.assertEqual(list(self.tmp.glob("fleet-triage-*")), [])

    def test_an_inherited_shallow_file_does_not_refuse_the_merge(self) -> None:
        """A shallow boundary at the branch tip must not turn a behind branch into an error."""
        shallow = self.tmp / "cut.shallow"
        shallow.write_text(self.pr_sha + "\n", encoding="utf-8")
        verdict = self._simulate({"GIT_SHALLOW_FILE": str(shallow)})
        self._assert_behind_and_untouched(verdict)

    def test_an_inherited_graft_does_not_pretend_the_branch_contains_main(self) -> None:
        """A graft that reparents the branch tip onto main must not report MERGE-CLEAN."""
        graft = self.tmp / "grafts"
        graft.write_text(f"{self.pr_sha} {self.main_sha}\n", encoding="utf-8")
        verdict = self._simulate({"GIT_GRAFT_FILE": str(graft)})
        self._assert_behind_and_untouched(verdict)

    def test_an_inherited_index_file_does_not_rewrite_the_source_index(self) -> None:
        """``GIT_INDEX_FILE`` pointing at the source index must leave those bytes unchanged."""
        verdict = self._simulate({"GIT_INDEX_FILE": str(self.repo / ".git" / "index")})
        self._assert_behind_and_untouched(verdict)


if __name__ == "__main__":
    unittest.main()
